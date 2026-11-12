"""Script tests for ``docs/fleet/scripts/fleet_setup.py``, the one-command setup of a new fleet machine."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from docs.fleet.scripts import fleet, fleet_setup, fleet_stop

if TYPE_CHECKING:
    from collections.abc import Sequence


def _box(tmp_path: Path) -> fleet_setup.Box:
    return fleet_setup.Box(home=tmp_path, user="someone", repo=tmp_path / "projects" / "dsf")


def _step(key: str, kind: str, gaps: list[str | None]) -> fleet_setup.Step:
    """Return a step whose check answers ``gaps`` in turn, its line naming ``key``."""
    return fleet_setup.Step(
        key,
        kind,
        key,
        lambda _box: gaps.pop(0) if gaps else None,
        lambda _box: [f"make {key}"],
    )


def test_the_ssh_options_match_the_fleets() -> None:
    assert fleet_setup.SSH_OPTIONS == fleet.SSH_OPTIONS


def test_the_checkout_path_is_the_one_fleet_sync_requires() -> None:
    assert {row["repo"] for row in fleet_stop.machine_rows()} == {fleet_setup.REPO}


def test_step_keys_are_unique_and_every_kind_is_known() -> None:
    keys = [step.key for step in fleet_setup.STEPS]
    assert len(keys) == len(set(keys))
    assert {step.kind for step in fleet_setup.STEPS} <= set(fleet_setup.KINDS)


def test_root_steps_come_first_so_one_prompt_covers_them() -> None:
    kinds = [step.kind for step in fleet_setup.STEPS]
    assert kinds[: kinds.count("sudo")] == ["sudo"] * kinds.count("sudo")


def test_select_keeps_order_and_drops_skipped_kinds() -> None:
    picked = fleet_setup.select(["checkout", "uv", "ssh-key"], ["keys"], fleet_setup.LINUX)
    assert [step.key for step in picked] == ["uv", "checkout"]


def test_select_refuses_an_unknown_step_or_kind() -> None:
    with pytest.raises(ValueError, match="nope, root"):
        _ = fleet_setup.select(["nope"], ["root"], fleet_setup.LINUX)


def test_report_marks_each_step(tmp_path: Path) -> None:
    steps = [_step("uv", "user", [None]), _step("packages", "sudo", ["git"])]
    lines = fleet_setup.report(fleet_setup.check(_box(tmp_path), steps))
    assert lines == ["ok      user uv", "missing sudo packages  git"]


def test_install_runs_root_steps_first_in_one_call_and_skips_done_ones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake(lines: Sequence[str], _box: fleet_setup.Box, *, sudo: bool = False) -> int:
        calls.append((list(lines), sudo))
        return 0

    monkeypatch.setattr(fleet_setup, "run_lines", fake)
    steps = [
        _step("done", "user", [None, None]),
        _step("tool", "user", ["tool", None, None]),
        _step("pkg", "sudo", ["pkg", None]),
        _step("login", "hand", ["login", "login"]),
    ]
    assert fleet_setup.install(_box(tmp_path), steps) == 0
    assert calls == [(["make pkg"], True), (["make tool"], False)]


def test_install_stops_at_a_step_whose_check_still_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ran: list[str] = []

    def fake(lines: Sequence[str], _box: fleet_setup.Box, *, sudo: bool = False) -> int:
        del sudo
        ran.extend(lines)
        return 0

    monkeypatch.setattr(fleet_setup, "run_lines", fake)
    steps = [_step("first", "user", ["x", "still x"]), _step("second", "user", ["y"])]
    assert fleet_setup.install(_box(tmp_path), steps) == 1
    assert ran == ["make first"]


def test_the_direnv_hook_check_reads_bashrc(tmp_path: Path) -> None:
    box = _box(tmp_path)
    hook = next(step for step in fleet_setup.STEPS if step.key == "direnv-hook")
    assert hook.check(box) is not None
    _ = (tmp_path / ".bashrc").write_text(f"# shell\n{fleet_setup.DIRENV_HOOK}\n")
    assert hook.check(box) is None


def test_a_github_ssh_remote_becomes_https() -> None:
    assert fleet_setup.https_url("git@github.com:o/r.git") == "https://github.com/o/r.git"
    assert fleet_setup.https_url("https://example.com/r.git") == "https://example.com/r.git"


def test_box_command_quotes_its_words() -> None:
    line = fleet_setup.box_command("check", ["--repo-url", "a b"])
    assert line == f"python3 {fleet_setup.REMOTE_COPY} box check --repo-url 'a b'"


def test_a_small_box_gets_low_weights_and_lowered_floors() -> None:
    assert fleet_setup.suggest_row("box", 4, 7 * 1024 * 1024) == {
        "name": "box",
        "ssh": "box",
        "os": "linux",
        "repo": fleet_setup.REPO,
        "weight": {"light": 0.4, "heavy": 0.2},
        "floors": {
            "light": {
                "min_mem_available_gib": 2,
                "min_disk_free_gib": 6,
                "max_psi_memory_full_avg10": 5,
            },
            "heavy": {
                "min_mem_available_gib": 3,
                "min_disk_free_gib": 12,
                "max_psi_memory_full_avg10": 5,
            },
        },
        "aliases": [],
    }


@pytest.mark.parametrize(
    (
        "cores",
        "gib",
        "light",
        "heavy",
    ),
    [
        (
            12,
            45,
            1.0,
            1.0,
        ),
        (
            1,
            1,
            0.1,
            0.1,
        ),
    ],
)
def test_a_suggested_weight_is_capped_at_one_and_floored_at_a_tenth(
    cores: int,
    gib: int,
    light: float,
    heavy: float,
) -> None:
    suggested = fleet_setup.suggest_row("box", cores, gib * 1024 * 1024)
    assert suggested["weight"] == {"light": light, "heavy": heavy}


def test_machine_names_reads_every_named_row(tmp_path: Path) -> None:
    listed = tmp_path / "machines.json"
    _ = listed.write_text(json.dumps({"machines": [{"name": "a"}, {"ssh": "b"}, "c"]}))
    assert fleet_setup.machine_names(listed) == ["a"]


SYSTEMS = (fleet_setup.LINUX, fleet_setup.MACOS)


def _block() -> str:
    return fleet_setup.block(fleet_setup.PATH_MARK, fleet_setup.PATH_BLOCK_FILE.read_text())


def _listing(home: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(home.iterdir())}


def test_one_block_file_serves_every_os_and_the_ubuntu_layer() -> None:
    setup = fleet_setup.PATH_BLOCK_FILE.parent.parent
    assert setup / "files" / "path.sh" == fleet_setup.PATH_BLOCK_FILE
    assert fleet_setup.PATH_BLOCK_FILE.is_file()
    assert not any(setup.rglob("bashrc-path.sh"))
    assert (fleet_setup.PATH_BLOCK_FILE, "setup/files/path.sh") in fleet_setup.PUSHED
    step = next(step for step in fleet_setup.STEPS if step.key == "path-block")
    assert step.systems == SYSTEMS


@pytest.mark.parametrize(
    ("system", "name"),
    [(fleet_setup.LINUX, ".bashrc"), (fleet_setup.MACOS, ".zshenv")],
)
def test_each_os_gets_the_file_its_shell_reads_for_an_ssh_command(
    tmp_path: Path,
    system: str,
    name: str,
) -> None:
    assert fleet_setup.startup_file(tmp_path, system) == tmp_path / name


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_writer_creates_an_absent_file_holding_the_block_alone(
    tmp_path: Path,
    system: str,
) -> None:
    assert fleet_setup.write_path_block(tmp_path, system, 7) is None
    target = fleet_setup.startup_file(tmp_path, system)
    assert _listing(tmp_path) == {target.name: _block().encode()}
    assert target.stat().st_mode & 0o777 == 0o644
    assert fleet_setup.check_path_block(tmp_path, system) is None


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_writer_replaces_a_stale_block_moves_it_first_and_keeps_a_backup(
    tmp_path: Path,
    system: str,
) -> None:
    target = fleet_setup.startup_file(tmp_path, system)
    stale = "export A=1\n" + fleet_setup.block(fleet_setup.PATH_MARK, "PATH=old") + "export B=2\n"
    _ = target.write_text(stale)
    target.chmod(0o600)
    backup = tmp_path / f"{target.name}.bak-7"
    assert fleet_setup.write_path_block(tmp_path, system, 7) == backup
    assert backup.read_text() == stale
    assert target.read_text() == _block() + "\nexport A=1\nexport B=2\n"
    assert target.stat().st_mode & 0o777 == 0o600
    assert sorted(_listing(tmp_path)) == sorted([target.name, backup.name])


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_writer_prepends_the_block_to_a_file_without_one(tmp_path: Path, system: str) -> None:
    target = fleet_setup.startup_file(tmp_path, system)
    _ = target.write_text("\n\nexport A=1\n")
    backup = fleet_setup.write_path_block(tmp_path, system, 7)
    assert backup is not None
    assert backup.read_text() == "\n\nexport A=1\n"
    assert target.read_text() == _block() + "\nexport A=1\n"


@pytest.mark.parametrize("system", SYSTEMS)
def test_a_second_write_changes_nothing_and_keeps_no_second_backup(
    tmp_path: Path,
    system: str,
) -> None:
    _ = fleet_setup.startup_file(tmp_path, system).write_text("export A=1\n")
    _ = fleet_setup.write_path_block(tmp_path, system, 7)
    before = _listing(tmp_path)
    assert fleet_setup.write_path_block(tmp_path, system, 8) is None
    assert _listing(tmp_path) == before


@pytest.mark.parametrize("system", SYSTEMS)
def test_a_file_holding_the_block_alone_is_current_and_left_as_it_is(
    tmp_path: Path,
    system: str,
) -> None:
    target = fleet_setup.startup_file(tmp_path, system)
    _ = target.write_text(_block())
    assert fleet_setup.check_path_block(tmp_path, system) is None
    assert fleet_setup.write_path_block(tmp_path, system, 7) is None
    assert _listing(tmp_path) == {target.name: _block().encode()}


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_check_writes_nothing_and_wants_the_block_first(tmp_path: Path, system: str) -> None:
    name = fleet_setup.startup_file(tmp_path, system).name
    gap = f"PATH block at the top of ~/{name}"
    assert fleet_setup.check_path_block(tmp_path, system) == gap
    assert _listing(tmp_path) == {}
    target = fleet_setup.startup_file(tmp_path, system)
    _ = target.write_text("guard\n" + _block())
    stamp = target.stat().st_mtime_ns
    assert fleet_setup.check_path_block(tmp_path, system) == gap
    assert _listing(tmp_path) == {name: ("guard\n" + _block()).encode()}
    assert target.stat().st_mtime_ns == stamp


def test_the_steps_writer_line_runs_this_file_with_this_python(tmp_path: Path) -> None:
    (line,) = fleet_setup.path_block_lines()
    assert line.endswith(" box write-path-block")
    env = {**os.environ, "HOME": str(tmp_path)}
    completed = subprocess.run(
        ["bash", "-c", line],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    assert fleet_setup.check_path_block(tmp_path, platform.system()) is None


def test_a_mac_box_runs_the_path_step_and_the_reference_sources_only() -> None:
    steps = fleet_setup.select([], [], fleet_setup.MACOS)
    assert [step.key for step in steps] == [
        "path-block",
        "strawberry-django",
        "django-graphene-filters",
        "graphene-django",
    ]
    assert "path-block" in [step.key for step in fleet_setup.select([], [], fleet_setup.LINUX)]
    with pytest.raises(ValueError, match="not a Darwin step: linger"):
        _ = fleet_setup.select(["linger"], [], fleet_setup.MACOS)


@pytest.mark.parametrize(
    ("answers", "system"),
    [
        ([(0, "Darwin")], "Darwin"),
        ([(0, "Linux"), (0, "ubuntu")], "Linux"),
        ([(0, "Linux"), (0, "debian")], "Linux debian"),
        ([(255, "unreached")], ""),
    ],
)
def test_add_tells_a_mac_from_ubuntu_and_anything_else(
    monkeypatch: pytest.MonkeyPatch,
    answers: list[tuple[int, str]],
    system: str,
) -> None:
    def fake(host: str | None, command: str, **_options: object) -> tuple[int, str]:
        del host, command
        return answers.pop(0)

    monkeypatch.setattr(fleet_setup, "on", fake)
    assert fleet_setup.system_of("box") == system
    assert answers == []


def test_add_copies_the_script_the_path_block_and_the_pins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pushed: list[tuple[str, str | None]] = []

    def fake(host: str | None, command: str, **options: str | None) -> tuple[int, str]:
        del host
        pushed.append((command, options.get("stdin")))
        return 0, ""

    monkeypatch.setattr(fleet_setup, "on", fake)
    assert fleet_setup.push_self("box") == 0
    root = fleet_setup.REMOTE_ROOT
    assert pushed == [
        (
            f"mkdir -p {root} && cat > {root}/fleet_setup.py",
            Path(fleet_setup.__file__).read_text(),
        ),
        (
            f"mkdir -p {root}/setup/files && cat > {root}/setup/files/path.sh",
            fleet_setup.PATH_BLOCK_FILE.read_text(),
        ),
        (
            f"mkdir -p {root}/setup && cat > {root}/setup/versions.json",
            fleet_setup.VERSIONS_FILE.read_text(),
        ),
    ]


def test_verify_asks_plain_ssh_for_every_tool() -> None:
    assert fleet_setup.tools_command() == "command -v uv git python3 node claude codex gh"


@pytest.mark.parametrize(
    ("output", "absent", "code"),
    [
        ("\n".join(f"/some/bin/{tool}" for tool in fleet_setup.SSH_TOOLS), [], 0),
        (
            "/l/bin/uv\n/usr/bin/git\n/usr/bin/python3",
            [
                "node",
                "claude",
                "codex",
                "gh",
            ],
            1,
        ),
    ],
)
def test_verify_names_each_tool_a_non_interactive_ssh_misses(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    output: str,
    absent: list[str],
    code: int,
) -> None:
    asked: list[tuple[str | None, str]] = []

    def fake(host: str | None, command: str, **_options: object) -> tuple[int, str]:
        asked.append((host, command))
        return (1 if absent else 0), output

    monkeypatch.setattr(fleet_setup, "on", fake)
    assert fleet_setup.missing_tools(output) == absent
    assert fleet_setup.check_tools("box") == code
    assert asked == [("box", fleet_setup.tools_command())]
    expected = f"missing {', '.join(absent)}" if absent else "ok      every tool on PATH"
    assert capsys.readouterr().out.splitlines()[-1] == expected


# -- reference sources ------------------------------------------------------------------------

#: The environment a test's own ``git`` and the lines run in: no ``GIT_*`` from the caller.
_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _env(home: Path, path: str | None = None) -> dict[str, str]:
    base = fleet_setup.git_env(os.environ)
    return {
        **base,
        "HOME": str(home),
        "PATH": path or base["PATH"],
        **_GIT_IDENTITY,
    }


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env=_env(cwd),
    )
    return completed.stdout.strip()


def _commit(repo: Path, name: str, text: str) -> str:
    _ = (repo / name).write_text(text)
    _ = _git(repo, "add", name)
    _ = _git(repo, "commit", "-q", "-m", name)
    return _git(repo, "rev-parse", "HEAD")


def _lines(
    lines: Sequence[str],
    home: Path,
    path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", " && ".join(f"( {line} )" for line in lines)],
        capture_output=True,
        text=True,
        check=False,
        cwd=home,
        env=_env(home, path),
    )


def _tree(folder: Path) -> dict[str, bytes]:
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def _box_git(home: Path) -> fleet_setup.Git:
    return fleet_setup.box_git(fleet_setup.Box(home=home, user="u", repo=home / "r"))


def test_the_versions_file_pins_both_reference_sources() -> None:
    pins = fleet_setup.load_versions()
    assert pins["strawberry-django"] == "0.82.1"
    assert pins["django-graphene-filters"] == "v1.0.0"
    assert pins["graphene-django"] == "3.2.3"
    assert {fleet_setup.STRAWBERRY_DJANGO_DIR, fleet_setup.FILTERS_DIR} <= (
        fleet_setup.PROJECT_ENTRIES
    )


def test_the_reference_paths_are_the_ones_agents_md_names() -> None:
    rules = (Path(fleet_setup.ROOT) / "AGENTS.md").read_text(encoding="utf-8")
    projects = f"~/{fleet_setup.PROJECTS}"
    assert f"`{projects}/{fleet_setup.STRAWBERRY_DJANGO_DIR}/strawberry_django`" in rules
    venv = f"{projects}/{fleet_setup.FILTERS_DIR}/.venv/lib/python*/site-packages/graphene_django"
    assert f"`{venv}`" in rules


def test_strawberry_djangos_version_is_its_project_tables_release(tmp_path: Path) -> None:
    tree = tmp_path / "projects" / fleet_setup.STRAWBERRY_DJANGO_DIR
    assert fleet_setup.strawberry_django_version(tmp_path) == ""
    tree.mkdir(parents=True)
    pyproject = tree / "pyproject.toml"
    _ = pyproject.write_text(
        '[tool.x]\nversion = "9.9.9"\n[project]\nname = "s"\nversion = "0.82.1"\n',
    )
    assert fleet_setup.strawberry_django_version(tmp_path) == "0.82.1"
    _ = pyproject.write_text('[project]\nversion = "0.82.1; rm -rf ~"\n')
    assert fleet_setup.strawberry_django_version(tmp_path) == ""


def test_graphene_djangos_version_is_the_clones_dist_info(tmp_path: Path) -> None:
    assert fleet_setup.graphene_django_version(tmp_path) == ""
    site = tmp_path / "projects" / fleet_setup.FILTERS_DIR / ".venv/lib/python3.14/site-packages"
    (site / "graphene_django-3.2.3.dist-info").mkdir(parents=True)
    (site / "graphene-3.4.3.dist-info").mkdir()
    assert fleet_setup.graphene_django_version(tmp_path) == "3.2.3"


def _archive(folder: Path, tag: str, files: dict[str, str]) -> None:
    """Write GitHub's tarball shape for ``tag``: every file under one top folder."""
    source = folder / f"src-{tag}"
    for name, text in files.items():
        (source / name).parent.mkdir(parents=True, exist_ok=True)
        _ = (source / name).write_text(text)
    with tarfile.open(folder / f"{tag}.tar.gz", "w:gz") as archive:
        archive.add(source, arcname=f"strawberry-django-{tag}")


def _release(version: str) -> dict[str, str]:
    return {
        "pyproject.toml": f'[project]\nversion = "{version}"\n',
        "strawberry_django/__init__.py": f"# {version}\n",
    }


@pytest.fixture
def archives(tmp_path: Path) -> str:
    folder = tmp_path / "archives"
    folder.mkdir()
    _archive(folder, "0.81.0", _release("0.81.0"))
    _archive(folder, "0.82.1", _release("0.82.1"))
    return f"file://{folder}/{{tag}}.tar.gz"


def _strawberry(home: Path) -> Path:
    return home / "projects" / fleet_setup.STRAWBERRY_DJANGO_DIR


def test_strawberry_django_is_unpacked_from_its_tags_tarball(
    tmp_path: Path,
    archives: str,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    lines = fleet_setup.strawberry_django_lines("0.82.1", "", archives)
    assert _lines(lines, home).returncode == 0
    assert _tree(_strawberry(home)) == {k: v.encode() for k, v in _release("0.82.1").items()}
    assert fleet_setup.strawberry_django_version(home) == "0.82.1"
    assert list((home / ".cache" / "dsf-fleet-setup").iterdir()) == []


def test_a_tree_equal_to_its_own_release_is_replaced_by_the_pin(
    tmp_path: Path,
    archives: str,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    assert (
        _lines(fleet_setup.strawberry_django_lines("0.81.0", "", archives), home).returncode == 0
    )
    (_strawberry(home) / "strawberry_django" / "__pycache__").mkdir()
    lines = fleet_setup.strawberry_django_lines("0.82.1", "0.81.0", archives)
    completed = _lines(lines, home)
    assert completed.returncode == 0, completed.stderr
    assert _tree(_strawberry(home)) == {k: v.encode() for k, v in _release("0.82.1").items()}


@pytest.mark.parametrize("installed", ["0.81.0", ""])
def test_a_tree_that_differs_from_its_release_is_never_overwritten(
    tmp_path: Path,
    archives: str,
    installed: str,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    assert (
        _lines(fleet_setup.strawberry_django_lines("0.81.0", "", archives), home).returncode == 0
    )
    _ = (_strawberry(home) / "strawberry_django" / "__init__.py").write_text("# edited\n")
    before = _tree(_strawberry(home))
    completed = _lines(fleet_setup.strawberry_django_lines("0.82.1", installed, archives), home)
    assert completed.returncode != 0
    assert "left as it is" in completed.stderr
    assert _tree(_strawberry(home)) == before


def test_the_strawberry_django_step_is_done_at_the_pin_and_names_another_version(
    tmp_path: Path,
) -> None:
    box = _box(tmp_path)
    step = next(step for step in fleet_setup.STEPS if step.key == "strawberry-django")
    folder = f"~/projects/{fleet_setup.STRAWBERRY_DJANGO_DIR}"
    assert step.check(box) == folder
    tree = _strawberry(tmp_path)
    tree.mkdir(parents=True)
    _ = (tree / "pyproject.toml").write_text('[project]\nversion = "0.81.0"\n')
    assert step.check(box) == f"{folder} at 0.81.0, not 0.82.1"
    assert step.lines(box) == fleet_setup.strawberry_django_lines("0.82.1", "0.81.0")
    _ = (tree / "pyproject.toml").write_text('[project]\nversion = "0.82.1"\n')
    assert step.check(box) is None


@pytest.fixture
def origin(tmp_path: Path) -> Path:
    """A django-graphene-filters origin with tags v1.0.0 and v1.1.0 (one commit apart)."""
    work = tmp_path / "upstream"
    work.mkdir()
    _ = _git(work, "init", "-q", "-b", "master")
    _ = _commit(work, "a.txt", "1\n")
    _ = _git(work, "tag", "-a", "v1.0.0", "-m", "v1.0.0")
    _ = _commit(work, "b.txt", "2\n")
    _ = _git(work, "tag", "-a", "v1.1.0", "-m", "v1.1.0")
    bare = tmp_path / "riodw" / "django-graphene-filters.git"
    _ = _git(tmp_path, "clone", "-q", "--bare", str(work), str(bare))
    return bare


def _clone(home: Path) -> Path:
    return home / "projects" / fleet_setup.FILTERS_DIR


def _head(home: Path) -> str:
    return _git(_clone(home), "rev-parse", "HEAD")


def test_an_absent_clone_is_made_detached_at_the_pinned_tag(tmp_path: Path, origin: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    completed = _lines(fleet_setup.filters_lines("v1.0.0", str(origin)), home)
    assert completed.returncode == 0, completed.stderr
    assert _head(home) == _git(origin, "rev-parse", "v1.0.0^{commit}")
    assert _git(_clone(home), "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"
    assert fleet_setup.filters_status(home, "v1.0.0", _box_git(home)) == ("ok", "")
    assert fleet_setup.filters_described(home, _box_git(home)) == "v1.0.0"


def test_a_clean_detached_clone_behind_the_pin_is_moved_to_it(
    tmp_path: Path,
    origin: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _ = _git(home, "clone", "-q", "--branch", "v1.0.0", str(origin), str(_clone(home)))
    _ = _git(_clone(home), "tag", "-d", "v1.1.0")
    git = _box_git(home)
    assert fleet_setup.filters_status(home, "v1.1.0", git) == (
        "behind",
        "tag v1.1.0 is not fetched",
    )
    completed = _lines(fleet_setup.filters_lines("v1.1.0", str(origin)), home)
    assert completed.returncode == 0, completed.stderr
    assert _head(home) == _git(origin, "rev-parse", "v1.1.0^{commit}")
    assert fleet_setup.filters_status(home, "v1.1.0", git) == ("ok", "")


@pytest.mark.parametrize(
    "shape",
    [
        "branch",
        "changes",
        "origin",
        "not-a-checkout",
    ],
)
def test_a_clone_someone_works_in_is_never_changed(
    tmp_path: Path,
    origin: Path,
    shape: str,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    clone = _clone(home)
    if shape == "not-a-checkout":
        clone.mkdir(parents=True)
        _ = (clone / "notes.txt").write_text("mine\n")
    else:
        _ = _git(home, "clone", "-q", str(origin), str(clone))
        _ = _git(clone, "reset", "-q", "--hard", "v1.0.0")
        if shape != "branch":
            _ = _git(clone, "checkout", "-q", "--detach")
        if shape == "changes":
            _ = (clone / "a.txt").write_text("edited\n")
        if shape == "origin":
            _ = _git(clone, "remote", "set-url", "origin", "https://example.com/other/repo.git")
    before = {**_tree(clone)}
    head = _head(home) if shape != "not-a-checkout" else ""
    completed = _lines(fleet_setup.filters_lines("v1.1.0", str(origin)), home)
    assert completed.returncode != 0
    assert "left as it is" in completed.stderr
    assert _tree(clone) == before
    if head:
        assert _head(home) == head
    status, _detail = fleet_setup.filters_status(home, "v1.1.0", _box_git(home))
    assert status == ("behind" if shape in {"branch", "changes"} else "differs")


def test_a_working_clone_past_the_pin_is_present_and_names_its_changes(
    tmp_path: Path,
    origin: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _ = _git(home, "clone", "-q", str(origin), str(_clone(home)))
    _ = (_clone(home) / "a.txt").write_text("edited\n")
    git = _box_git(home)
    assert fleet_setup.filters_status(home, "v1.0.0", git) == ("ahead", "local changes")
    index = _clone(home) / ".git" / "index"
    stamp = index.stat().st_mtime_ns
    box = fleet_setup.Box(home=home, user="u", repo=home / "r")
    step = next(step for step in fleet_setup.STEPS if step.key == fleet_setup.FILTERS_DIR)
    assert step.check(box) is None
    assert index.stat().st_mtime_ns == stamp


def test_a_diverged_clone_differs(tmp_path: Path, origin: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _ = _git(home, "clone", "-q", "--branch", "v1.0.0", str(origin), str(_clone(home)))
    _ = _commit(_clone(home), "c.txt", "mine\n")
    status = fleet_setup.filters_status(home, "v1.1.0", _box_git(home))
    assert status == ("differs", "diverged from v1.1.0")


def _fake_uv(tmp_path: Path) -> tuple[str, Path]:
    tools = tmp_path / "tools"
    tools.mkdir()
    record = tmp_path / "uv-calls"
    uv = tools / "uv"
    _ = uv.write_text(f'#!/bin/sh\necho "$PWD $*" >> {record}\n')
    uv.chmod(0o755)
    return f"{tools}{os.pathsep}{os.environ['PATH']}", record


def test_graphene_django_is_a_frozen_uv_sync_in_a_clean_clone(
    tmp_path: Path,
    origin: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    path, record = _fake_uv(tmp_path)
    _ = _git(home, "clone", "-q", "--branch", "v1.0.0", str(origin), str(_clone(home)))
    completed = _lines(fleet_setup.graphene_django_lines(), home, path)
    assert completed.returncode == 0, completed.stderr
    python = fleet_setup.PYTHONS[-1]
    real = _clone(home).resolve()
    assert record.read_text() == f"{real} sync --frozen --quiet --python {python}\n"


@pytest.mark.parametrize("shape", ["changes", "missing"])
def test_graphene_django_never_syncs_a_clone_with_changes_or_none(
    tmp_path: Path,
    origin: Path,
    shape: str,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    path, record = _fake_uv(tmp_path)
    if shape == "changes":
        _ = _git(home, "clone", "-q", "--branch", "v1.0.0", str(origin), str(_clone(home)))
        _ = (_clone(home) / "a.txt").write_text("edited\n")
    completed = _lines(fleet_setup.graphene_django_lines(), home, path)
    assert completed.returncode != 0
    assert not record.exists()


def test_git_reads_drop_the_callers_git_variables_and_take_no_lock() -> None:
    assert fleet_setup.git_argv(Path("/r"), ["status"]) == [
        "git",
        "--no-optional-locks",
        "-C",
        "/r",
        "status",
    ]
    assert fleet_setup.git_env({"GIT_DIR": "/x", "GIT_INDEX_FILE": "/i", "HOME": "/h"}) == {
        "HOME": "/h",
    }


# -- strays -----------------------------------------------------------------------------------


@pytest.fixture
def fleet_home(tmp_path: Path) -> Path:
    """A home holding the checkout (one root commit), its ``.work`` copies and the references."""
    home = tmp_path / "home"
    checkout = home / "projects" / "django-strawberry-framework"
    checkout.mkdir(parents=True)
    _ = _git(checkout, "init", "-q", "-b", "main")
    _ = _commit(checkout, "README.md", "dsf\n")
    _ = _git(checkout, "worktree", "add", "-q", "--detach", str(checkout / ".work/worktrees/w"))
    _ = _git(home, "clone", "-q", str(checkout), str(checkout / ".work/clones/c"))
    for name in (fleet_setup.STRAWBERRY_DJANGO_DIR, fleet_setup.FILTERS_DIR):
        (home / "projects" / name).mkdir()
    for name in fleet_setup.RULES_FILES:
        _ = (home / "projects" / name).write_text("rules\n")
    return home


def _strays(home: Path, *, other_projects: bool = False) -> list[tuple[str, str]]:
    checkout = home / "projects" / "django-strawberry-framework"
    found = fleet_setup.strays(home, checkout, _box_git(home), other_projects=other_projects)
    return [(fleet_setup.home_relative(stray.path, home), stray.why) for stray in found]


def test_a_clean_fleet_home_has_no_strays(fleet_home: Path) -> None:
    assert _strays(fleet_home) == []


def test_every_repo_of_this_repo_outside_the_checkout_and_its_copies_is_a_stray(
    fleet_home: Path,
) -> None:
    checkout = fleet_home / "projects" / "django-strawberry-framework"
    _ = _git(fleet_home, "clone", "-q", str(checkout), str(fleet_home / "old" / "dsf-copy"))
    renamed = fleet_home / "old" / "renamed"
    _ = _git(fleet_home, "clone", "-q", str(checkout), str(renamed))
    _ = _git(renamed, "remote", "remove", "origin")
    _ = _git(checkout, "worktree", "add", "-q", "--detach", str(fleet_home / "wt"))
    _ = _git(fleet_home, "clone", "-q", "--bare", str(checkout), str(fleet_home / "dsf.git"))
    gone = fleet_home / "gone-wt"
    _ = _git(checkout, "worktree", "add", "-q", "--detach", str(gone))
    shutil.rmtree(checkout / ".git" / "worktrees" / "gone-wt")
    other = fleet_home / "other"
    other.mkdir()
    _ = _git(other, "init", "-q")
    _ = _commit(other, "x.txt", "x\n")
    fresh = fleet_home / "fresh"
    fresh.mkdir()
    _ = _git(fresh, "init", "-q")
    _ = _commit(fresh, "y.txt", "y\n")
    url = "git@github.com:unaxy/django-strawberry-framework.git"
    _ = _git(fresh, "remote", "add", "origin", url)
    assert _strays(fleet_home) == [
        ("~/dsf.git", "a bare clone of this repo"),
        ("~/fresh", "a clone of this repo"),
        ("~/gone-wt", "a worktree of this repo"),
        ("~/old/dsf-copy", "a clone of this repo"),
        ("~/old/renamed", "a clone of this repo"),
        ("~/wt", "a worktree of this repo"),
    ]


@pytest.mark.parametrize(
    "where",
    [
        "Library/Caches/dsf",
        "node_modules/dsf",
        ".nvm/dsf",
        ".Trash/dsf",
        ".local/share/Trash/files/dsf",
        "snap/dsf",
        ".npm/dsf",
        ".cache/uv/git-v0/dsf",
        "work/app/.cache/uv/dsf",
    ],
)
def test_the_walk_leaves_out_caches_trash_and_system_folders(fleet_home: Path, where: str) -> None:
    checkout = fleet_home / "projects" / "django-strawberry-framework"
    _ = _git(fleet_home, "clone", "-q", str(checkout), str(fleet_home / where))
    assert _strays(fleet_home) == []


def test_a_git_file_that_is_no_gitdir_pointer_is_no_repo(fleet_home: Path) -> None:
    sdists = fleet_home / "work" / "sdists-v9"
    sdists.mkdir(parents=True)
    _ = (sdists / ".git").write_text("")
    assert _strays(fleet_home) == []


def test_an_extra_projects_entry_is_a_stray_unless_the_machine_allows_others(
    fleet_home: Path,
) -> None:
    projects = fleet_home / "projects"
    (projects / "mine").mkdir()
    _ = (projects / "notes.zip").write_text("z")
    _ = (projects / fleet_setup.FINDER_FILE).write_text("")
    checkout = projects / "django-strawberry-framework"
    _ = _git(fleet_home, "clone", "-q", str(checkout), str(projects / "dsf-2"))
    why = "no entry ~/projects holds"
    assert _strays(fleet_home) == [
        ("~/projects/dsf-2", f"a clone of this repo; {why}"),
        ("~/projects/mine", why),
        ("~/projects/notes.zip", why),
    ]
    assert _strays(fleet_home, other_projects=True) == [
        ("~/projects/dsf-2", "a clone of this repo"),
    ]


@pytest.mark.parametrize(
    ("system", "entered"),
    [("Darwin", False), ("Linux", True)],
)
def test_a_mac_never_walks_the_folders_macos_guards_with_a_privacy_prompt(
    system: str,
    *,
    entered: bool,
) -> None:
    home = Path("/home/someone")
    fixed = fleet_setup.pruned_folders(home, system)
    for name in fleet_setup.MACOS_PRIVATE_FOLDERS:
        assert (home / name in fixed) is not entered
    assert home / "Library" in fixed


def test_the_stray_check_reads_only(fleet_home: Path) -> None:
    def listing() -> list[tuple[str, int]]:
        return [
            (str(path), path.stat().st_mtime_ns)
            for path in sorted(fleet_home.rglob("*"))
            if not path.is_symlink()
        ]

    checkout = fleet_home / "projects" / "django-strawberry-framework"
    _ = _git(fleet_home, "clone", "-q", str(checkout), str(fleet_home / "dsf-copy"))
    before = listing()
    assert _strays(fleet_home) != []
    assert listing() == before


def test_only_rio_air_holds_other_projects() -> None:
    names = fleet_setup.machine_names()
    allowed = [name for name in names if fleet_setup.other_projects_allowed(name)]
    assert allowed == ["rio-air"]
    assert [machine.name for machine in fleet.machines() if machine.other_projects] == allowed


def test_box_strays_prints_each_and_exits_1(
    fleet_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    listed = tmp_path / "machines.json"
    _ = listed.write_text(json.dumps({"machines": [{"name": "box", "other_projects": False}]}))
    monkeypatch.setenv("DSF_MACHINE_ID", "box")
    checkout = fleet_home / "projects" / "django-strawberry-framework"
    box = fleet_setup.Box(home=fleet_home, user="u", repo=checkout)
    assert fleet_setup.print_strays(box, listed) == 0
    assert capsys.readouterr().out == "ok      no strays\n"
    (fleet_home / "projects" / "mine").mkdir()
    assert fleet_setup.print_strays(box, listed) == 1
    assert capsys.readouterr().out == "stray   ~/projects/mine  no entry ~/projects holds\n"
    _ = listed.write_text(json.dumps({"machines": [{"name": "box", "other_projects": True}]}))
    assert fleet_setup.print_strays(box, listed) == 0


def test_verify_runs_the_boxs_stray_check(monkeypatch: pytest.MonkeyPatch) -> None:
    asked: list[tuple[str | None, str]] = []

    def on(host: str | None, command: str, **_options: object) -> tuple[int, str]:
        asked.append((host, command))
        return (1, "stray") if "box strays" in command else (0, "")

    def check_tools(_host: str) -> int:
        return 0

    monkeypatch.setattr(fleet_setup, "on", on)
    monkeypatch.setattr(fleet_setup, "check_tools", check_tools)
    assert fleet_setup.verify("rio-bee") == 1
    line = f"cd {fleet_setup.REPO} && python3 {fleet_setup.SETUP_SCRIPT} box strays"
    assert ("rio-bee", line) in asked
