"""Tests for ``scripts/shared_checkout_guard.py``: the Claude edit hook and the pytest guard."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import shared_checkout_guard as guard
from tests._idioms import json_at

_AGENTLESS: dict[str, str] = {}


def _git_init(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "init",
            "-q",
            str(folder),
        ],
        check=True,
    )
    return folder


@pytest.fixture
def shared(tmp_path: Path) -> Path:
    """A shared checkout: a git repo holding a real ``.work`` directory and a copy in it."""
    root = _git_init(tmp_path / "shared")
    (root / ".work" / "clones").mkdir(parents=True)
    (root / ".gitignore").write_text(".work/\n*.local.json\n")
    _git_init(root / ".work" / "clones" / "fix-copy")
    return root


def _edit(path: Path | str, *, tool: str = "Edit", cwd: Path | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"tool_name": tool, "tool_input": {"file_path": str(path)}}
    if cwd is not None:
        payload["cwd"] = str(cwd)
    return payload


def test_shared_root_is_the_checkout_holding_a_real_work_folder(
    shared: Path,
    tmp_path: Path,
) -> None:
    assert guard.shared_root(shared / "pkg" / "module.py") == shared
    assert guard.shared_root(shared) == shared
    assert (
        guard.shared_root(shared / ".work" / "clones" / "fix-copy" / "pkg" / "module.py") is None
    )
    assert guard.shared_root(_git_init(tmp_path / "plain") / "module.py") is None
    assert guard.shared_root(tmp_path / "nowhere" / "module.py") is None


def test_a_symlinked_work_folder_does_not_make_a_shared_checkout(tmp_path: Path) -> None:
    root = _git_init(tmp_path / "linked")
    (tmp_path / "elsewhere").mkdir()
    (root / ".work").symlink_to(tmp_path / "elsewhere")
    assert guard.shared_root(root / "module.py") is None


@pytest.mark.parametrize("tool", ["Edit", "MultiEdit", "Write"])
def test_a_write_to_a_shared_file_is_refused_with_the_copy_command(
    shared: Path,
    tool: str,
) -> None:
    reason = guard.edit_refusal(_edit(shared / "pkg" / "module.py", tool=tool), _AGENTLESS)
    assert reason is not None
    assert "pkg/module.py is in the shared checkout" in reason
    assert "scripts/work.py new" in reason
    assert "work.py land" in reason


def test_a_notebook_edit_names_its_target_by_notebook_path(shared: Path) -> None:
    payload = {
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": str(shared / "nb.ipynb")},
    }
    assert guard.edit_refusal(payload, _AGENTLESS) is not None


def test_a_relative_target_resolves_against_the_payload_cwd(shared: Path) -> None:
    assert guard.edit_refusal(_edit("pkg/module.py", cwd=shared), _AGENTLESS) is not None
    copy = shared / ".work" / "clones" / "fix-copy"
    assert guard.edit_refusal(_edit("pkg/module.py", cwd=copy), _AGENTLESS) is None


@pytest.mark.parametrize(
    "relative",
    [
        ".work/clones/fix-copy/pkg/module.py",
        ".work/evidence/fix-copy/notes.md",
        "docs/bug_hunt/bug_hunt-0_0_15_2.md",
        "CHANGELOGTODO.md",
        "settings.local.json",
    ],
)
def test_copies_evidence_in_place_files_and_ignored_files_are_allowed(
    shared: Path,
    relative: str,
) -> None:
    assert guard.edit_refusal(_edit(shared / relative), _AGENTLESS) is None


def test_a_tracked_file_matching_an_ignore_pattern_is_still_refused(shared: Path) -> None:
    tracked = shared / "kept.local.json"
    tracked.write_text("{}\n")
    subprocess.run(
        [
            "git",
            "-C",
            str(shared),
            "add",
            "-f",
            "kept.local.json",
        ],
        check=True,
    )
    assert guard.edit_refusal(_edit(tracked), _AGENTLESS) is not None


def test_writes_outside_any_shared_checkout_are_allowed(tmp_path: Path) -> None:
    assert guard.edit_refusal(_edit(tmp_path / "scratch" / "probe.py"), _AGENTLESS) is None


def test_the_override_and_unguarded_tools_and_malformed_inputs_allow(shared: Path) -> None:
    target = shared / "pkg" / "module.py"
    assert guard.edit_refusal(_edit(target), {guard.EDIT_OVERRIDE_ENV: "1"}) is None
    assert guard.edit_refusal(_edit(target, tool="Read"), _AGENTLESS) is None
    assert guard.edit_refusal({"tool_name": "Edit", "tool_input": "nope"}, _AGENTLESS) is None
    assert (
        guard.edit_refusal({"tool_name": "Edit", "tool_input": {"file_path": ""}}, _AGENTLESS)
        is None
    )


def test_main_prints_a_deny_decision_for_a_refused_write(
    shared: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(guard.EDIT_OVERRIDE_ENV, raising=False)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_edit(shared / "pkg" / "module.py"))))
    assert guard.main() == 0
    output = guard._loads(capsys.readouterr().out)
    assert guard.is_json_object(output)
    decision = output["hookSpecificOutput"]
    assert guard.is_json_object(decision)
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    reason = decision["permissionDecisionReason"]
    assert isinstance(reason, str)
    assert "work.py new" in reason


def test_main_prints_nothing_for_an_allowed_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_edit(tmp_path / "probe.py"))))
    assert guard.main() == 0
    assert capsys.readouterr().out == ""


def _decision(output: str) -> dict[str, object]:
    parsed = guard._loads(output)
    assert guard.is_json_object(parsed)
    decision = parsed["hookSpecificOutput"]
    assert guard.is_json_object(decision)
    return decision


def test_main_fails_closed_on_an_unreadable_payload(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(guard.EDIT_OVERRIDE_ENV, raising=False)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert guard.main() == 0
    decision = _decision(capsys.readouterr().out)
    assert decision["permissionDecision"] == "deny"
    reason = decision["permissionDecisionReason"]
    assert isinstance(reason, str)
    assert "could not classify this write" in reason
    assert guard.EDIT_OVERRIDE_ENV in reason


def test_the_hook_denies_a_shared_write_when_git_cannot_run(shared: Path) -> None:
    environ = {key: value for key, value in os.environ.items() if key != guard.EDIT_OVERRIDE_ENV}
    environ["PATH"] = ""
    completed = subprocess.run(
        [sys.executable, guard.__file__],
        input=json.dumps(_edit(shared / "settings.local.json")),
        env=environ,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    decision = _decision(completed.stdout)
    assert decision["permissionDecision"] == "deny"
    assert "FileNotFoundError" in str(decision["permissionDecisionReason"])


def test_a_case_alias_of_a_tracked_ignored_file_is_refused(shared: Path) -> None:
    tracked = shared / "kept.local.json"
    tracked.write_text("{}\n")
    subprocess.run(
        [
            "git",
            "-C",
            str(shared),
            "add",
            "-f",
            "kept.local.json",
        ],
        check=True,
    )
    alias = shared / "KEPT.LOCAL.JSON"
    if not alias.exists():
        pytest.skip("needs a case-insensitive filesystem")
    assert guard.edit_refusal(_edit(alias), _AGENTLESS) is not None
    assert guard.edit_refusal(_edit(shared / "OTHER.LOCAL.JSON"), _AGENTLESS) is None


@pytest.mark.parametrize(
    "relative",
    [
        "docs/bug_hunt/helper.py",
        "docs/bug_hunt/sub/notes.md",
        "docs/bug_hunt.md",
        "CHANGELOGTODO.txt",
    ],
)
def test_only_the_bug_hunt_folders_own_markdown_is_edited_in_place(
    shared: Path,
    relative: str,
) -> None:
    assert guard.edit_refusal(_edit(shared / relative, tool="Write"), _AGENTLESS) is not None


def test_pytest_in_the_shared_checkout_is_refused_without_the_override(shared: Path) -> None:
    reason = guard.pytest_refusal(shared, _AGENTLESS)
    assert reason is not None
    assert "pytest in the shared checkout" in reason
    assert "work.py run" in reason
    assert "--worktree --from <sha>" in reason
    assert f"{guard.PYTEST_OVERRIDE_ENV}=1" in reason


def test_pytest_in_a_copy_or_with_the_override_runs(shared: Path) -> None:
    assert guard.pytest_refusal(shared, {guard.PYTEST_OVERRIDE_ENV: "1"}) is None
    assert guard.pytest_refusal(shared / ".work" / "clones" / "fix-copy", _AGENTLESS) is None


def test_a_moved_rootdir_does_not_hide_the_shared_conftest(shared: Path, tmp_path: Path) -> None:
    elsewhere = tmp_path / "private"
    elsewhere.mkdir()
    (elsewhere / "pytest.ini").write_text("[pytest]\n")
    (shared / "conftest.py").write_text(
        "import os\nfrom pathlib import Path\n\nimport pytest\n\n"
        "from scripts import shared_checkout_guard\n\n\n"
        "def pytest_configure(config):\n"
        "    reason = shared_checkout_guard.pytest_refusal(Path(__file__).parent, os.environ)\n"
        "    if reason is not None:\n"
        "        pytest.exit(reason, returncode=4)\n",
    )
    (shared / "test_probe.py").write_text("def test_probe():\n    pass\n")
    environ = {key: value for key, value in os.environ.items() if key != guard.PYTEST_OVERRIDE_ENV}
    environ.update(
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTHONPATH=str(Path(guard.__file__).parents[1]),
    )
    environ.pop("PYTEST_ADDOPTS", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-c",
            str(elsewhere / "pytest.ini"),
            "--rootdir",
            str(elsewhere),
            str(shared / "test_probe.py"),
        ],
        cwd=elsewhere,
        env=environ,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 4, completed.stdout + completed.stderr
    assert "pytest in the shared checkout" in completed.stdout + completed.stderr


def _track(root: Path, name: str, text: str = "{}\n") -> Path:
    path = root / name
    path.write_text(text)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "add",
            "-f",
            "--",
            name,
        ],
        check=True,
    )
    return path


@pytest.mark.parametrize(
    ("tracked", "alias"),
    [
        ("kept.local.json", "KEPT.LOCAL.JSON"),
        ("caf\u00e9.local.json", "CAF\u00c9.local.json"),
        ("na\u00efve.local.json", "NA\u00cfVE.local.json"),
    ],
)
def test_a_case_or_unicode_alias_of_a_tracked_ignored_file_is_refused(
    shared: Path,
    tracked: str,
    alias: str,
) -> None:
    kept = _track(shared, tracked)
    target = shared / alias
    if not target.exists() or not target.samefile(kept):
        pytest.skip("needs a case-insensitive filesystem")
    assert guard.edit_refusal(_edit(target), _AGENTLESS) is not None


def test_an_inherited_private_index_does_not_hide_a_tracked_file(
    shared: Path,
    tmp_path: Path,
) -> None:
    _ = _track(shared, "kept.local.json")
    environ = {key: value for key, value in os.environ.items() if key != guard.EDIT_OVERRIDE_ENV}
    environ["GIT_INDEX_FILE"] = str(tmp_path / "private.index")
    subprocess.run(
        [
            "git",
            "-C",
            str(shared),
            "read-tree",
            "--empty",
        ],
        env=environ,
        check=True,
    )
    completed = subprocess.run(
        [sys.executable, guard.__file__],
        input=json.dumps(_edit(shared / "kept.local.json")),
        env=environ,
        capture_output=True,
        text=True,
        check=False,
    )
    assert _decision(completed.stdout)["permissionDecision"] == "deny"


def test_a_distinct_ignored_file_beside_a_tracked_case_sibling_is_allowed(tmp_path: Path) -> None:
    """Needs case-sensitive storage: ``DSF_CASE_SENSITIVE_ROOT`` names a folder on one."""
    parent = Path(os.environ.get("DSF_CASE_SENSITIVE_ROOT", str(tmp_path)))
    root = _git_init(parent / f"case-{os.getpid()}")
    (root / ".work").mkdir()
    (root / ".gitignore").write_text(".work/\n*.local.json\n")
    kept = _track(root, "kept.local.json", "tracked\n")
    target = root / "KEPT.local.json"
    if target.exists():
        pytest.skip("needs case-sensitive storage; set DSF_CASE_SENSITIVE_ROOT")
    target.write_text("untracked\n")
    assert not target.samefile(kept)
    assert guard.edit_refusal(_edit(target), _AGENTLESS) is None


@pytest.mark.parametrize("name", ["[kept].local.json", "*.local.json"])
def test_a_literal_wildcard_name_is_a_file_name_not_a_pattern(shared: Path, name: str) -> None:
    _ = _track(shared, "kept.local.json")
    target = shared / name
    target.write_text("{}\n")
    assert guard.edit_refusal(_edit(target), _AGENTLESS) is None


def test_a_case_alias_of_a_bug_hunt_markdown_file_keeps_the_exception(shared: Path) -> None:
    target = shared / "docs" / "bug_hunt" / "FIX.md"
    target.parent.mkdir(parents=True)
    target.write_text("fixture\n")
    alias = shared / "DOCS" / "BUG_HUNT" / "FIX.MD"
    if not alias.exists() or not alias.samefile(target):
        pytest.skip("needs a case-insensitive filesystem")
    assert guard.edit_refusal(_edit(alias), _AGENTLESS) is None


def test_canonical_keeps_a_missing_tail_as_given(shared: Path) -> None:
    (shared / "docs").mkdir()
    assert (
        guard.canonical(shared, shared / "docs" / "New" / "File.md")
        == shared / "docs" / "New" / "File.md"
    )


def test_a_tracked_file_renamed_on_disk_by_case_alone_is_still_refused(shared: Path) -> None:
    kept = _track(shared, "kept.local.json")
    renamed = shared / "Kept.local.json"
    kept.rename(renamed)
    if not kept.exists():
        pytest.skip("needs a case-insensitive filesystem")
    assert guard.edit_refusal(_edit(renamed), _AGENTLESS) is not None


@pytest.fixture
def tracked_shared(tmp_path: Path) -> Path:
    root = tmp_path / "shared"
    root.mkdir()
    _ = subprocess.run(
        [
            "git",
            "init",
            "-q",
            str(root),
        ],
        check=True,
    )
    (root / ".work").mkdir()
    _ = (root / ".gitignore").write_text(".work/\n*.local.json\n")
    _ = (root / "kept.local.json").write_text("{}\n")
    _ = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "add",
            "-f",
            "kept.local.json",
        ],
        check=True,
    )
    return root


def _payload(path: Path | str, cwd: Path | None = None, tool: str = "Edit") -> dict[str, object]:
    result: dict[str, object] = {"tool_name": tool, "tool_input": {"file_path": str(path)}}
    if cwd is not None:
        result["cwd"] = str(cwd)
    return result


def test_dot_segments_symlinks_missing_parents_and_a_missing_cwd_are_refused(
    tracked_shared: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tracked_shared
    (root / "pkg").mkdir()
    _ = (root / "pkg" / "module.py").write_text("VALUE = 1\n")
    (root / "alias").symlink_to(root / "pkg", target_is_directory=True)
    (root / ".work" / "escape").symlink_to(root / "pkg", target_is_directory=True)
    for name in (
        "pkg/../pkg/module.py",
        "alias/module.py",
        ".work/escape/module.py",
        "new/parent/new.py",
    ):
        assert guard.edit_refusal(_payload(root / name), {}) is not None, name
    monkeypatch.chdir(root)
    assert guard.edit_refusal(_payload("pkg/module.py"), {}) is not None


def test_copies_harness_worktrees_and_nested_repos_are_allowed(
    tracked_shared: Path,
) -> None:
    for name, git_entry in (
        (".work/clones/fix-copy", "directory"),
        (".work/worktrees/fix-copy", "file"),
        (".claude/worktrees/harness", "file"),
        ("vendor/nested", "directory"),
    ):
        root = tracked_shared / name
        root.mkdir(parents=True)
        if git_entry == "file":
            _ = (root / ".git").write_text("gitdir: unused\n")
        else:
            (root / ".git").mkdir()
        assert guard.edit_refusal(_payload(root / "module.py"), {}) is None


def _system_hook(cwd: Path, raw: str) -> subprocess.CompletedProcess[str]:
    project = Path(guard.__file__).resolve().parents[1]
    command = json_at(
        guard._loads((project / ".claude" / "settings.json").read_text()),
        "hooks",
        "PreToolUse",
        0,
        "hooks",
        0,
        "command",
    )
    assert isinstance(command, str)
    environment = dict(os.environ, PATH="/usr/bin:/bin", CLAUDE_PROJECT_DIR=str(project))
    environment.pop(guard.EDIT_OVERRIDE_ENV, None)
    return subprocess.run(
        ["/bin/sh", "-c", command],
        cwd=cwd,
        input=raw,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("where", "name", "refused"),
    [
        ("shared", "module.py", True),
        ("private", "module.py", False),
        ("shared", "/nonexistent/codex-guard-probe/module.py", False),
        ("shared", "kept.local.json", True),
        ("shared", "untracked.local.json", False),
    ],
)
def test_the_system_python_hook_without_a_payload_cwd(
    tracked_shared: Path,
    tmp_path: Path,
    where: str,
    name: str,
    *,
    refused: bool,
) -> None:
    private = _git_init(tmp_path / "private")
    cwd = tracked_shared if where == "shared" else private
    result = _system_hook(cwd, json.dumps(_payload(name)))
    assert result.returncode == 0, result.stderr
    assert ('"permissionDecision": "deny"' in result.stdout) == refused, (
        result.stdout,
        result.stderr,
    )


@pytest.mark.parametrize("raw", ["not json", "[]", "null"])
def test_the_system_python_hook_denies_an_unreadable_payload(
    tracked_shared: Path,
    raw: str,
) -> None:
    result = _system_hook(tracked_shared, raw)
    assert result.returncode == 0, result.stderr
    assert '"permissionDecision": "deny"' in result.stdout


def test_a_hardlink_cannot_supply_the_canonical_name(shared: Path) -> None:
    allowed = shared / "CHANGELOGTODO.md"
    allowed.write_text("before\n")
    tracked = shared / "zz_source.py"
    tracked.hardlink_to(allowed)
    subprocess.run(
        [
            "git",
            "-C",
            str(shared),
            "add",
            "-f",
            "--",
            tracked.name,
        ],
        check=True,
    )
    target = shared / "ZZ_SOURCE.PY"
    if not target.exists():
        pytest.skip("requires case-insensitive storage")
    assert target.samefile(tracked)
    assert guard.canonical(shared, target) == tracked
    result = _system_hook(shared, json.dumps(_edit(target, tool="Write")))
    assert result.returncode == 0, result.stderr
    assert '"permissionDecision": "deny"' in result.stdout, (
        guard.canonical(shared, target),
        result.stdout,
        result.stderr,
    )


def test_a_tracked_inode_is_not_an_untracked_ignored_file(shared: Path) -> None:
    tracked = _track(shared, "source.py")
    target = shared / "cache.local.json"
    target.hardlink_to(tracked)
    assert target.samefile(tracked)
    result = _system_hook(shared, json.dumps(_edit(target, tool="Write")))
    assert result.returncode == 0, result.stderr
    assert '"permissionDecision": "deny"' in result.stdout


def test_a_missing_index_is_not_an_empty_tracking_answer(shared: Path) -> None:
    tracked = _track(shared, "kept.local.json")
    subprocess.run(
        [
            "git",
            "-C",
            str(shared),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "isolated guard fixture",
        ],
        check=True,
    )
    (shared / ".git" / "index").unlink()
    result = _system_hook(shared, json.dumps(_edit(tracked)))
    assert result.returncode == 0, result.stderr
    assert '"permissionDecision": "deny"' in result.stdout


def test_a_raw_index_name_is_checked_by_identity(tmp_path: Path) -> None:
    parent = Path(os.environ.get("DSF_CASE_SENSITIVE_ROOT", str(tmp_path)))
    root = _git_init(parent / f"raw-{os.getpid()}-{tmp_path.name}")
    (root / ".work").mkdir()
    (root / ".gitignore").write_text(".work/\n*.local.json\n")
    raw_name = b"bad-\xff.local.json"
    raw_path = os.fsencode(root) + b"/" + raw_name
    try:
        descriptor = os.open(raw_path, os.O_CREAT | os.O_WRONLY, 0o600)
    except OSError as error:
        pytest.skip(f"filesystem refuses raw-byte names: {error}")
    _ = os.write(descriptor, b"raw")
    os.close(descriptor)
    target = root / os.fsdecode(raw_name)
    blob = (
        subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "hash-object",
                "-w",
                "--stdin",
            ],
            input=b"raw",
        )
        .decode()
        .strip()
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{blob},{target.name}",
        ],
        check=True,
    )
    listed = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "-z",
        ],
    )
    assert raw_name in listed.split(b"\0")
    canonical = guard.canonical(root, target)
    assert canonical.samefile(target)
    result = _system_hook(root, json.dumps(_edit(target)))
    assert result.returncode == 0, result.stderr
    assert '"permissionDecision": "deny"' in result.stdout, (listed, canonical, result.stdout)


@pytest.mark.parametrize(
    ("name", "alias"),
    [("kept.local.json", "KEPT.local.json"), ("stra\u00dfe.local.json", "STRASSE.local.json")],
)
def test_a_deleted_case_sibling_does_not_reserve_a_distinct_new_name(
    tmp_path: Path,
    name: str,
    alias: str,
) -> None:
    parent = Path(os.environ.get("DSF_CASE_SENSITIVE_ROOT", str(tmp_path)))
    root = _git_init(parent / f"deleted-{os.getpid()}-{tmp_path.name}")
    (root / ".work").mkdir()
    (root / ".gitignore").write_text(".work/\n*.local.json\n")
    tracked = _track(root, name)
    target = root / alias
    if target.exists():
        pytest.skip("requires filesystem-distinct names")
    target.write_text("different file\n")
    assert not target.samefile(tracked)
    target.unlink()
    tracked.unlink()
    assert guard.edit_refusal(_edit(target), {}) is None


@pytest.mark.parametrize(
    ("relative", "allowed"),
    [
        ("new/deep/cache.local.json", True),
        ("new/deep/module.py", False),
        (".work/new/deep/module.py", True),
    ],
)
def test_new_files_keep_their_intended_boundary(
    shared: Path,
    relative: str,
    *,
    allowed: bool,
) -> None:
    assert (guard.edit_refusal(_edit(shared / relative), {}) is None) == allowed


def test_a_work_directory_case_alias_stays_allowed(shared: Path) -> None:
    alias = shared / ".WORK"
    if not alias.exists():
        pytest.skip("requires case-insensitive storage")
    assert alias.samefile(shared / ".work")
    assert guard.edit_refusal(_edit(alias / "evidence" / "New" / "module.py"), {}) is None


@pytest.mark.parametrize(
    ("relative", "allowed"),
    [("kept.local.json", False), (".work/evidence/New/module.py", True)],
)
def test_a_symlinked_parent_keeps_the_real_boundary(
    tracked_shared: Path,
    tmp_path: Path,
    relative: str,
    *,
    allowed: bool,
) -> None:
    alias = tmp_path / "parent-link"
    alias.symlink_to(tracked_shared, target_is_directory=True)
    assert (guard.edit_refusal(_edit(alias / relative), {}) is None) == allowed


def test_untracked_ignored_hardlinks_remain_allowed(shared: Path) -> None:
    first = shared / "first.local.json"
    first.write_text("cached\n")
    second = shared / "second.local.json"
    second.hardlink_to(first)
    assert first.samefile(second)
    assert guard.edit_refusal(_edit(first), {}) is None
    assert guard.edit_refusal(_edit(second), {}) is None


def test_system_python_fails_closed_until_permissions_return(shared: Path) -> None:
    closed = shared / "closed"
    closed.mkdir()
    target = closed / "cache.local.json"
    target.write_text("{}\n")
    closed.chmod(0)
    try:
        result = _system_hook(shared, json.dumps(_edit(target)))
    finally:
        closed.chmod(0o700)
    assert result.returncode == 0, result.stderr
    assert '"permissionDecision": "deny"' in result.stdout
    assert "PermissionError" in result.stdout
    assert not result.stderr
    restored = _system_hook(shared, json.dumps(_edit(target)))
    assert restored.returncode == 0, restored.stderr
    assert not restored.stdout


def test_system_python_handles_a_listing_lstat_race(shared: Path) -> None:
    target = shared / "CACHE.LOCAL.JSON"
    (shared / "cache.local.json").write_text("{}\n")
    (shared / "ephemeral").write_text("temporary\n")
    if not target.exists():
        pytest.skip("requires case-insensitive storage")
    raw = json.dumps(_edit(target))
    program = f"""
import importlib.util, io, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("guard_under_test", {guard.__file__!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
native = module._stored_name
def race(folder, names, part, held):
    if folder == Path({str(shared)!r}):
        (folder / "ephemeral").unlink()
        names = ["ephemeral"] + [name for name in names if name != "ephemeral"]
    return native(folder, names, part, held)
module._stored_name = race
sys.stdin = io.StringIO({raw!r})
raise SystemExit(module.main())
"""
    environment = {
        key: value for key, value in os.environ.items() if key != guard.EDIT_OVERRIDE_ENV
    }
    result = subprocess.run(
        ["/usr/bin/python3", "-c", program],
        input="",
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"permissionDecision": "deny"' in result.stdout
    assert "FileNotFoundError" in result.stdout
    assert not result.stderr


def test_an_in_place_file_hard_linked_to_tracked_source_is_refused(shared: Path) -> None:
    tracked = _track(shared, "source.py", "VALUE = 1\n")
    in_place = shared / "CHANGELOGTODO.md"
    in_place.hardlink_to(tracked)
    assert guard.edit_refusal(_edit(in_place), _AGENTLESS) is not None
    _ = _track(shared, "CHANGELOGTODO.md")
    assert guard.edit_refusal(_edit(shared / "docs" / "bug_hunt" / "notes.md"), _AGENTLESS) is None
