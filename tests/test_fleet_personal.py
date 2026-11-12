"""Script tests for ``docs/fleet/scripts/setup/ubuntu/personal.py``, a fleet box's personal layer."""

from __future__ import annotations

import io
import re
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from docs.fleet.scripts import fleet_setup
from docs.fleet.scripts.setup.ubuntu import personal

if TYPE_CHECKING:
    from collections.abc import Sequence

SETUP = Path(personal.__file__).resolve().parent.parent
FACTS = {
    "HOST": "box",
    "OS": "Ubuntu 26.04.1 LTS",
    "CPU": "Some CPU",
    "THREADS": "4",
    "RAM_GIB": "7",
    "DISK": "117G",
}


def _box(tmp_path: Path) -> personal.Box:
    return personal.Box(home=tmp_path, user="someone", facts=dict(FACTS), system="Linux")


def test_limits_reproduce_rio_ubus_hand_tuned_values() -> None:
    assert personal.limits(12, 45) == {
        "SLOTS": "3",
        "MIN_FREE_GIB": "4",
        "YELLOW_FREE_GIB": "8",
        "LOAD_YELLOW": "9",
        "LOAD_RED": "18",
    }


def test_limits_scale_down_to_a_small_box() -> None:
    assert personal.limits(4, 7) == {
        "SLOTS": "1",
        "MIN_FREE_GIB": "2",
        "YELLOW_FREE_GIB": "4",
        "LOAD_YELLOW": "3",
        "LOAD_RED": "6",
    }


def test_every_template_renders_with_no_placeholder_left(tmp_path: Path) -> None:
    box = _box(tmp_path)
    tools = personal.house_tools(box)
    assert set(tools) == {
        "agent-status",
        "git-autosync",
        "heavy",
        "pressure",
    }
    assert "SLOTS=1" in tools["heavy"]
    assert "at most 1 heavy job(s)" in personal.rules_text(box)


def test_render_refuses_an_unfilled_placeholder() -> None:
    with pytest.raises(ValueError, match="@MISSING@"):
        _ = personal.render("a @HOST@ b @MISSING@", {"HOST": "x"})


def test_the_path_block_step_is_fleet_setups_own_check_and_writer(tmp_path: Path) -> None:
    box = _box(tmp_path)
    step = next(step for step in personal.STEPS if step.key == "path-block")
    assert step.lines(box) == fleet_setup.path_block_lines()
    gap = "PATH block at the top of ~/.bashrc"
    assert step.check(box) == fleet_setup.check_path_block(tmp_path, "Linux") == gap
    _ = fleet_setup.write_path_block(tmp_path, "Linux", 1)
    assert step.check(box) is None


def test_the_interactive_block_goes_last_and_leaves_the_path_block_first(tmp_path: Path) -> None:
    box = _box(tmp_path)
    _ = fleet_setup.write_path_block(tmp_path, "Linux", 1)
    _ = (tmp_path / ".bashrc").write_text((tmp_path / ".bashrc").read_text() + "guard\n")
    wanted = personal._wanted_interactive(box)
    path_body = fleet_setup.PATH_BLOCK_FILE.read_text()
    interactive_body = (personal.FILES / "bashrc-interactive.sh").read_text()
    assert wanted.startswith(fleet_setup.block(fleet_setup.PATH_MARK, path_body) + "guard\n")
    assert wanted.endswith(
        "guard\n\n" + fleet_setup.block(personal.INTERACTIVE_MARK, interactive_body),
    )
    again = fleet_setup.with_block(wanted, personal.INTERACTIVE_MARK, "tmux2", top=False)
    assert again.count(f"# >>> {personal.INTERACTIVE_MARK} >>>") == 1
    assert again.endswith(fleet_setup.block(personal.INTERACTIVE_MARK, "tmux2"))


def test_select_refuses_an_unknown_step_or_kind() -> None:
    with pytest.raises(ValueError, match="nope, keys"):
        _ = personal.select(["nope"], ["keys"])


def test_root_steps_come_first_so_one_prompt_covers_them() -> None:
    kinds = [step.kind for step in personal.STEPS]
    assert kinds[: kinds.count("sudo")] == ["sudo"] * kinds.count("sudo")


def test_install_runs_root_steps_first_and_skips_done_ones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake(lines: Sequence[str], _box: personal.Box, *, sudo: bool = False) -> int:
        calls.append((list(lines), sudo))
        return 0

    answers = {"done": [None, None], "tool": ["tool", None, None], "pkg": ["pkg", None]}

    def step(key: str, kind: str) -> personal.Step:
        return personal.Step(
            key,
            kind,
            lambda _box: answers[key].pop(0) if answers[key] else None,
            lambda _box: [f"make {key}"],
        )

    monkeypatch.setattr(personal, "run_lines", fake)
    steps = [step("done", "user"), step("tool", "user"), step("pkg", "sudo")]
    assert personal.install(_box(tmp_path), steps) == 0
    assert calls == [(["make pkg"], True), (["make tool"], False)]


def test_the_bundle_carries_the_script_its_files_and_the_shared_path_step_only() -> None:
    with tarfile.open(fileobj=io.BytesIO(personal.bundle())) as archive:
        names = archive.getnames()
        shared = {
            name: archive.extractfile(name) for name in ("fleet_setup.py", "setup/files/path.sh")
        }
        bodies = {name: member.read() for name, member in shared.items() if member is not None}
    assert "setup/ubuntu/personal.py" in names
    assert "setup/ubuntu/files/bin/heavy.in" in names
    assert sorted(name for name in names if not name.startswith("setup/ubuntu/")) == [
        "fleet_setup.py",
        "setup/files/path.sh",
    ]
    assert bodies == {
        "fleet_setup.py": Path(fleet_setup.__file__).read_bytes(),
        "setup/files/path.sh": fleet_setup.PATH_BLOCK_FILE.read_bytes(),
    }
    assert not any("__pycache__" in name for name in names)


PRIVATE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}"  # an email address
    r"|\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d+\.\d+\b"  # a Tailscale address
    r"|\b(?:192\.168|10)\.\d+\.\d+(?:\.\d+)?\b"  # a LAN address
    r"|/(?:home|Users)/[a-z]",  # an account's home folder
)


def test_the_setup_folder_holds_no_private_value() -> None:
    files = [
        path for path in SETUP.rglob("*") if path.is_file() and "__pycache__" not in path.parts
    ]
    assert len(files) >= 10
    hits = [
        f"{path.relative_to(SETUP)}: {match.group(0)}"
        for path in files
        for match in PRIVATE.finditer(_without_extension_lists(path.read_text(encoding="utf-8")))
        if not _is_pinned_extension(match.group(0))
    ]
    assert hits == []


#: GNOME Shell extension UUIDs are public ids shaped like emails (``ding@rastersoft.com``).
EXTENSION_LIST = re.compile(r"^(?:enabled|disabled)-extensions=\[(.*)\]$", re.MULTILINE)
EXTENSION_UUID = re.compile(r"'[A-Za-z0-9_.-]+@[A-Za-z0-9.-]+'")


def _is_pinned_extension(found: str) -> bool:
    """Return whether ``found`` is (the start of) a UUID ``personal.EXTENSIONS`` pins."""
    return any(uuid.startswith(found) for uuid in personal.EXTENSIONS)


def _without_extension_lists(text: str) -> str:
    """Return ``text`` with the extension-list keys removed, each checked to hold UUIDs only."""
    for match in EXTENSION_LIST.finditer(text):
        items = [item.strip() for item in match.group(1).split(",") if item.strip()]
        assert all(EXTENSION_UUID.fullmatch(item) for item in items), match.group(0)
    return EXTENSION_LIST.sub("", text)


@pytest.mark.parametrize(
    "sample",
    [
        "someone@example.com",
        "100.64.0.1",
        "192.168.0.10",
        "/home/someone/x",
        "/Users/someone",
    ],
)
def test_the_private_value_pattern_catches_each_kind(sample: str) -> None:
    assert PRIVATE.search(f"text {sample} text") is not None


@pytest.mark.parametrize(
    "sample",
    [
        "3.10",
        "~/.local/bin",
        "$HOME/projects",
        "1.0.77",
    ],
)
def test_the_private_value_pattern_lets_ordinary_text_through(sample: str) -> None:
    assert PRIVATE.search(f"text {sample} text") is None


def test_the_dock_keeps_only_installed_favourites_in_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    apps = tmp_path / "apps"
    flatpak = tmp_path / "flatpak"
    for folder, name in (
        (apps, "org.gnome.Settings.desktop"),
        (flatpak, "org.gnome.Nautilus.desktop"),
    ):
        folder.mkdir()
        _ = (folder / name).write_text("[Desktop Entry]\n")
    monkeypatch.setattr(personal, "APPLICATION_DIRS", (str(apps), str(flatpak)))
    assert personal.favorites(_box(tmp_path)) == (
        "['org.gnome.Nautilus.desktop', 'org.gnome.Settings.desktop']"
    )


def test_flatpak_exports_are_searched_for_favourites() -> None:
    assert "/var/lib/flatpak/exports/share/applications" in personal.APPLICATION_DIRS
    assert "~/.local/share/flatpak/exports/share/applications" in personal.APPLICATION_DIRS


def test_no_installed_favourite_is_an_empty_typed_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(personal, "APPLICATION_DIRS", ("~/none",))
    assert personal.favorites(_box(tmp_path)) == "@as []"


def test_the_desktop_settings_render_and_read_back_as_dconf_paths(tmp_path: Path) -> None:
    keys = personal.dconf_keys(personal.dconf_text(_box(tmp_path)))
    assert keys["/org/gnome/shell/extensions/dash-to-dock/dock-position"] == "'LEFT'"
    assert keys["/org/gnome/settings-daemon/plugins/power/sleep-inactive-ac-type"] == "'nothing'"
    assert str(tmp_path) in keys["/org/gnome/shell/extensions/executor/right-commands-json"]
    assert not any("preferred-monitor" in path for path in keys)


def test_the_files_sidebar_puts_projects_first_once(tmp_path: Path) -> None:
    bookmarks = tmp_path / ".config" / "gtk-3.0" / "bookmarks"
    bookmarks.parent.mkdir(parents=True)
    mark = f"file://{tmp_path}/projects projects"
    _ = bookmarks.write_text(f"file://{tmp_path}/Documents\n{mark}\n")
    body, _mode = personal._desktop_files(_box(tmp_path))[bookmarks]
    assert body == f"{mark}\nfile://{tmp_path}/Documents\n"


def test_an_older_copy_path_shortcut_is_replaced_not_kept(tmp_path: Path) -> None:
    accels = tmp_path / ".config" / "nautilus" / "scripts-accels"
    accels.parent.mkdir(parents=True)
    _ = accels.write_text("F4 Copy Path\n<Control>o Other Script\n")
    body, _mode = personal._desktop_files(_box(tmp_path))[accels]
    assert body == f"{personal.ACCEL}\n<Control>o Other Script\n"


def test_a_copy_path_script_without_its_execute_bit_is_stale(tmp_path: Path) -> None:
    box = _box(tmp_path)
    for path, (body, mode) in personal._desktop_files(box).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(body)
        path.chmod(int(mode, 8))
    assert personal._check_desktop_files(box) is None
    script = tmp_path / ".local" / "share" / "nautilus" / "scripts" / "Copy Path"
    script.chmod(0o644)
    assert personal._check_desktop_files(box) == "Copy Path"


def test_desktop_settings_name_a_missing_dconf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_command(_name: str) -> None:
        return None

    monkeypatch.setattr(shutil, "which", no_command)
    gap = personal._check_desktop_settings(_box(tmp_path))
    assert gap is not None
    assert "dconf-cli" in gap


def test_dconf_cli_is_installed_before_the_desktop_steps() -> None:
    keys = [step.key for step in personal.STEPS]
    assert "dconf-cli" in personal.APT_PACKAGES
    assert keys.index("apt-cli") < keys.index("desktop-settings")


TOSHY_CONFIG = """head
###  SLICE_MARK_START: kbtype_override  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE

keyboards_UserCustom_dct = {
    'My Keyboard Device Name': 'Apple',
}


###  SLICE_MARK_END: kbtype_override  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
tail
"""


def test_the_toshy_slice_replaces_only_its_own_marks_and_settles() -> None:
    once = personal.with_slice(TOSHY_CONFIG)
    assert "'Logitech USB Receiver': 'Apple'" in once
    assert once.startswith("head\n###  SLICE_MARK_START: kbtype_override")
    assert once.endswith(
        "###  SLICE_MARK_END: kbtype_override  ###" + TOSHY_CONFIG.rsplit("###", maxsplit=1)[-1],
    )
    assert personal.with_slice(once) == once
    assert personal.with_slice("no marks here\n") == "no marks here\n"


def test_toshy_sync_writes_the_slice_and_preferences(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path)
    config = tmp_path / personal.TOSHY_CONFIG
    config.parent.mkdir(parents=True)
    _ = config.write_text(TOSHY_CONFIG)
    assert personal._check_toshy_config(box) is not None

    def no_systemctl(*_args: object, **_kwargs: object) -> object:
        raise OSError

    monkeypatch.setattr(subprocess, "run", no_systemctl)
    assert personal.toshy_sync(box) == 0
    assert personal._check_toshy_config(box) is None


def test_every_pinned_extension_is_enabled_by_the_desktop_settings(tmp_path: Path) -> None:
    keys = personal.dconf_keys(personal.dconf_text(_box(tmp_path)))
    enabled = keys["/org/gnome/shell/enabled-extensions"]
    pinned_enabled = [uuid for uuid in personal.EXTENSIONS if f"'{uuid}'" in enabled]
    # rio-ubu installs Workspace Islands but leaves it off; every other pinned one is enabled.
    assert sorted(set(personal.EXTENSIONS) - set(pinned_enabled)) == [
        "workspace-islands@danielbernalo.github.io",
    ]


def test_an_extension_counts_only_at_its_pinned_version(tmp_path: Path) -> None:
    box = _box(tmp_path)
    folder = personal._extension_folder(box, "moveclock@kuvaus.org")
    folder.mkdir(parents=True)
    _ = (folder / "metadata.json").write_text('{"version": 10}')
    assert "moveclock@kuvaus.org" in personal._missing_extensions(box)
    _ = (folder / "metadata.json").write_text('{"version": 11}')
    assert "moveclock@kuvaus.org" not in personal._missing_extensions(box)


def test_toshy_runs_in_a_terminal_and_before_the_extensions_and_settings() -> None:
    keys = [step.key for step in personal.STEPS]
    assert next(step.kind for step in personal.STEPS if step.key == "toshy") == "tty"
    assert keys.index("toshy") < keys.index("toshy-config") < keys.index("shell-extensions")
    assert keys.index("shell-extensions") < keys.index("desktop-settings")


def test_a_step_an_earlier_step_undid_runs_again(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"settings": "set"}
    ran: list[str] = []

    def fake(lines: Sequence[str], _box: personal.Box, *, sudo: bool = False) -> int:
        del sudo
        ran.extend(lines)
        state["settings"] = "toshy" if lines == ["make toshy"] else "set"
        return 0

    toshy_done = iter(["missing", None, None])
    steps = [
        personal.Step("toshy", "tty", lambda _box: next(toshy_done), lambda _box: ["make toshy"]),
        personal.Step(
            "settings",
            "user",
            lambda _box: None if state["settings"] == "set" else "drifted",
            lambda _box: ["make settings"],
        ),
    ]
    monkeypatch.setattr(personal, "run_lines", fake)
    assert personal.install(_box(tmp_path), steps) == 0
    assert ran == ["make toshy", "make settings"]
