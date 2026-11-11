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
