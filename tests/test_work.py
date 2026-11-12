"""Repo-tooling tests for the private-working-copy manager's names, copies, pins, landing and cleanup.

Keeps the contracts of ``scripts/work.py`` against throwaway git repositories
under ``tmp_path``, never against this checkout's own ``.work/`` folder. The
rows that matter most are the ones whose failure would lose or misplace work:
the fail-closed sentinel, the pins that keep a copy's commits alive, the patch
landing that never touches a path another session has dirty or the shared
index, and every refusal ``rm`` and ``gc`` owe a copy someone may still be
using. A live ``/graphql/`` request has no wire shape for working copies, so
none of these rows can move there. There is no live sibling in
``examples/fakeshop/test_query/``.
"""

import contextlib
import dataclasses
import errno
import getpass
import json
import math
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Generator, Mapping
from pathlib import Path

import pytest

from docs.fleet.scripts import fleet
from scripts import _git, _locks, prove_failability, work, workspace
from tests._idioms import json_at, json_list, json_loads, json_object

#: ``sqlite3.Cursor.fetchall``, its rows typed for the caller.
_fetchall: Callable[[sqlite3.Cursor], list[tuple[object, ...]]] = sqlite3.Cursor.fetchall

PACKAGE = work.PACKAGE
ME = getpass.getuser()


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")
    return path


def _git_out(root: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=_git.repository_env(),
    )
    return result.stdout


def _age(path: Path, seconds: float = 3600) -> None:
    """Move every mtime under ``path`` (``.git`` and ``.venv`` aside) back by ``seconds``."""
    past = time.time() - seconds
    for directory, dirnames, filenames in os.walk(path):
        dirnames[:] = [name for name in dirnames if name not in work.UNWATCHED_DIRS]
        for name in filenames:
            os.utime(Path(directory) / name, (past, past), follow_symlinks=False)
    for directory, _dirnames, _filenames in os.walk(path, topdown=False):
        if not work.UNWATCHED_DIRS.intersection(Path(directory).relative_to(path).parts):
            os.utime(directory, (past, past))


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name in work.LOCATING_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv(workspace.ROOT_ENV, str(tmp_path / "ws"))
    root = tmp_path / "repo"
    _ = _write(root / PACKAGE / "__init__.py", "VALUE = 1\n")
    _ = _write(root / PACKAGE / "core.py", "CORE = 2\n")
    _ = _write(root / "examples" / "fakeshop" / "db.sqlite3", "tracked db\n")
    _ = _write(root / "gone.txt", "to delete\n")
    _ = _write(root / ".gitignore", ".work/\n.python-version\n.venv/\n")
    _ = _write(root / ".python-version", "3.14\n")
    _ = _git_out(root, "init", "-q", "-b", "main")
    _ = _git_out(root, "add", "-A")
    _ = _git_out(root, "commit", "-q", "-m", "initial")
    monkeypatch.setattr(work, "REPO_ROOT", root)

    def no_users(_path: Path) -> list[str]:
        return []

    def ample(_path: Path) -> int:
        return work.MIN_FREE_BYTES * 2

    monkeypatch.setattr(work, "process_census", no_users)
    monkeypatch.setattr(work, "free_bytes", ample)
    return root


def _new(name: str, *extra: str) -> Path:
    assert (
        work.main(
            [
                "new",
                name,
                "--no-setup",
                "--purpose",
                "a test",
                *extra,
            ],
        )
        == 0
    )
    copy = work.locate(work.REPO_ROOT, name)
    assert copy.path is not None
    return copy.path


def _pins(repo: Path) -> dict[str, dict[str, str]]:
    return work.pins(repo)


def _store(repo: Path) -> Path:
    return work.make_pin_store(repo)


def _plant(repo: Path, name: str, leaf: str) -> None:
    """Pin the shared ``HEAD`` as ``<name>/<leaf>``, as a copy that has since gone would leave."""
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    assert work.publish_pin(repo, repo, head, name, leaf)


# --------------------------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    (
        "text",
        "kind",
        "identifier",
        "slug",
        "stem",
    ),
    [
        (
            "build-work-manager",
            "build",
            None,
            "work-manager",
            "build-work-manager",
        ),
        (
            "fix-i681-unstorable",
            "fix",
            "i681",
            "unstorable",
            "fix-i681-unstorable",
        ),
        (
            "verify-c051-limits-r2",
            "verify",
            "c051",
            "limits",
            "verify-c051-limits",
        ),
        (
            "fix-i681-store-verify",
            "fix",
            "i681",
            "store",
            "fix-i681-store",
        ),
        (
            "head-v0-0-15-2-snap",
            "head",
            "v0-0-15-2",
            "snap",
            "head-v0-0-15-2-snap",
        ),
        (
            "bench-g1234abc-walk",
            "bench",
            "g1234abc",
            "walk",
            "bench-g1234abc-walk",
        ),
        (
            "spike-r2",
            "spike",
            None,
            "r2",
            "spike-r2",
        ),
    ],
)
def test_a_name_parses_into_kind_id_slug_and_the_stem_evidence_is_keyed_by(
    text: str,
    kind: str,
    identifier: str | None,
    slug: str,
    stem: str,
) -> None:
    name = work.parse_name(text)
    assert (
        name.kind,
        name.id,
        name.slug,
        name.stem,
    ) == (
        kind,
        identifier,
        slug,
        stem,
    )


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("review-x", "workspace.py"),
        ("hunt-x", "workspace.py"),
        ("dry-x", "workspace.py"),
        ("zap-thing", "must start with a kind"),
        ("build", "needs a slug"),
        ("fix-i681", "needs a slug"),
        ("Build-thing", "lowercase"),
        ("build--thing", "lowercase"),
        ("build-thing-", "lowercase"),
        ("build_thing", "lowercase"),
        ("build-" + "x" * 19, "1 to 24"),
        ("", "1 to 24"),
    ],
)
def test_a_name_that_breaks_the_grammar_is_refused_with_its_rule(text: str, reason: str) -> None:
    with pytest.raises(work.WorkError, match=reason):
        _ = work.parse_name(text)


def test_check_name_prints_the_parts_or_refuses(capsys: pytest.CaptureFixture[str]) -> None:
    assert work.main(["check-name", "fix-i681-unstorable-r2"]) == 0
    assert capsys.readouterr().out.strip() == (
        "kind=fix id=i681 slug=unstorable suffix=r2 stem=fix-i681-unstorable"
    )
    assert work.main(["check-name", "review-x"]) == 1
    assert "workspace.py" in capsys.readouterr().err


@pytest.mark.parametrize("variable", work.LOCATING_NAMES)
def test_every_command_refuses_while_git_is_pointed_at_another_repository_or_index(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    variable: str,
) -> None:
    monkeypatch.setenv(variable, str(repo / "elsewhere"))
    assert work.main(["list"]) == 1
    assert (
        work.main(
            [
                "run",
                "build-x",
                "--",
                "true",
            ],
        )
        == work.REFUSED
    )
    assert variable in capsys.readouterr().err
    assert not (repo / work.WORK_DIR).exists()


@pytest.mark.usefixtures("repo")
def test_run_and_others_take_nothing_after_the_separator_but_run() -> None:
    with pytest.raises(SystemExit):
        _ = work.main(["list", "--", "x"])
    assert work.main(["run", "build-x"]) == work.REFUSED


# --------------------------------------------------------------------------------------------
# new
# --------------------------------------------------------------------------------------------


def test_new_makes_a_detached_no_push_clone_with_its_note_pin_and_config(repo: Path) -> None:
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    path = _new("build-thing")
    assert path == repo / ".work" / "clones" / "build-thing"
    assert (repo / ".work" / ".git").read_text(encoding="utf-8") == work.SENTINEL_TEXT
    assert (repo / ".work" / "evidence" / "build-thing").is_dir()
    assert _git_out(path, "rev-parse", "HEAD").strip() == head
    assert _git_out(path, "rev-parse", "--abbrev-ref", "HEAD").strip() == "HEAD"
    assert _git_out(path, "remote", "get-url", "--push", "parent").strip() == work.NO_PUSH
    assert _git_out(path, "config", "--local", "core.longpaths").strip() == "true"
    assert _git_out(path, "config", "--local", "core.autocrlf").strip() == "false"
    assert (path / ".python-version").read_text(encoding="utf-8") == "3.14\n"
    note = work.locate(repo, "build-thing").note
    assert (
        note["name"],
        note["form"],
        note["purpose"],
        note["start"],
    ) == (
        "build-thing",
        "clone",
        "a test",
        head,
    )
    assert _pins(repo) == {"build-thing": {"start": head}}


def test_new_worktree_is_detached_locked_and_noted_in_its_own_worktree_config(repo: Path) -> None:
    path = _new("spike-tree", "--worktree")
    assert path == repo / ".work" / "worktrees" / "spike-tree"
    assert _git_out(repo, "config", "--bool", "extensions.worktreeConfig").strip() == "true"
    entry = next(entry for entry in work.worktree_entries(repo) if entry.path.name == "spike-tree")
    assert entry.branch is None
    assert entry.locked == "dsf-work spike-tree"
    assert _git_out(path, "config", "--worktree", "dsf-work.form").strip() == "worktree"
    assert _git_out(path, "config", "--worktree", "core.longpaths").strip() == "true"
    assert _git.run_git(repo, "config", "--get", "dsf-work.form").returncode != 0
    assert "start" in _pins(repo)["spike-tree"]


def test_new_starts_from_the_named_commit(repo: Path) -> None:
    first = _git_out(repo, "rev-parse", "HEAD").strip()
    _ = _write(repo / "later.txt", "later\n")
    _ = _git_out(repo, "add", "later.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "later")
    path = _new("head-g0000000-old", "--from", first)
    assert _git_out(path, "rev-parse", "HEAD").strip() == first
    assert not (path / "later.txt").exists()


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_new_refuses_a_name_in_use_or_holding_pins(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    form: list[str],
) -> None:
    _ = _new("build-thing", *form)
    assert work.main(["new", "build-thing", "--no-setup"]) == 1
    assert "is claimed" in capsys.readouterr().err
    _plant(repo, "fix-old", "save-1")
    assert work.main(["new", "fix-old", "--no-setup"]) == 1
    assert "pins left" in capsys.readouterr().err


def test_new_claims_its_folder_exclusively(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    claimed = repo / ".work" / "clones" / "build-race"
    claimed.mkdir(parents=True)
    _ = _write(claimed / "theirs.txt", "another new got here first\n")
    assert work.main(["new", "build-race", "--no-setup"]) == 1
    assert "already" in capsys.readouterr().err
    assert (claimed / "theirs.txt").is_file()


def test_new_refuses_below_the_disk_floor(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def scarce(_path: Path) -> int:
        return work.MIN_FREE_BYTES - 1

    monkeypatch.setattr(work, "free_bytes", scarce)
    assert work.main(["new", "build-thing", "--no-setup"]) == 1
    assert "GB free" in capsys.readouterr().err
    assert not (repo / ".work" / "clones" / "build-thing").exists()


@pytest.mark.usefixtures("repo")
def test_new_refuses_a_start_that_is_no_commit() -> None:
    assert (
        work.main(
            [
                "new",
                "build-thing",
                "--no-setup",
                "--from",
                "nope",
            ],
        )
        == 1
    )


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_a_new_that_fails_part_way_leaves_nothing_behind(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    form: list[str],
) -> None:
    def failing_setup(_path: Path, _form: str) -> None:
        msg = "uv sync --frozen failed"
        raise work.WorkError(msg)

    monkeypatch.setattr(work, "_setup", failing_setup)
    assert work.main(["new", "build-thing", *form]) == 1
    assert not (repo / ".work" / "clones" / "build-thing").exists()
    assert not (repo / ".work" / "worktrees" / "build-thing").exists()
    assert work.worktree_entries(repo) == []
    assert _pins(repo) == {}


def test_the_sentinel_makes_git_fail_closed_in_a_folder_without_its_own_git(repo: Path) -> None:
    _ = _new("build-thing")
    evidence = repo / ".work" / "evidence" / "build-thing"
    completed = _git.run_git(evidence, "rev-parse", "--show-toplevel")
    # git's wording for a gitfile naming no repository differs between releases; its die() exit
    # and an empty answer do not, and an empty answer means no walk up to the shared checkout.
    assert completed.returncode == 128
    assert completed.stdout == ""
    assert completed.stderr.startswith("fatal:")
    broken = repo / ".work" / "clones" / "build-thing"
    work.delete_tree(broken / ".git")
    assert _git.run_git(broken, "status").returncode != 0
    assert (
        "!! .work/" in _git.run_git(repo, "status", "--porcelain", "--ignored").stdout.splitlines()
    )


# --------------------------------------------------------------------------------------------
# adopt
# --------------------------------------------------------------------------------------------


def test_adopt_registers_a_harness_worktree_in_place_and_rm_leaves_it_to_the_harness(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    harness = tmp_path / "harness" / "bold-name"
    _ = _git_out(repo, "worktree", "add", "-q", "-b", "claude/bold-name", str(harness))
    assert (
        work.main(
            [
                "adopt",
                str(harness),
                "fix-i681-harness",
                "--purpose",
                "t3",
            ],
        )
        == 0
    )
    copy = work.locate(repo, "fix-i681-harness")
    assert copy.adopted
    assert copy.path == harness
    assert copy.locked is None
    assert _git_out(harness, "rev-parse", "--abbrev-ref", "HEAD").strip() == "claude/bold-name"
    assert "start" in _pins(repo)["fix-i681-harness"]
    _ = capsys.readouterr()
    assert work.main(["rm", "fix-i681-harness"]) == 1
    assert "harness" in capsys.readouterr().err
    assert harness.is_dir()
    assert work.main(["adopt", str(harness), "fix-i681-again"]) == 1
    assert "already registered" in capsys.readouterr().err


def test_adopt_registers_a_clone_already_under_work_clones(repo: Path) -> None:
    path = repo / ".work" / "clones" / "build-lead"
    path.parent.mkdir(parents=True)
    _ = _git_out(repo, "clone", "-q", "-o", "parent", str(repo), str(path))
    assert work.main(["adopt", str(path), "build-lead"]) == 0
    assert _git_out(path, "remote", "get-url", "--push", "parent").strip() == work.NO_PUSH
    assert _git_out(path, "config", "--local", "core.autocrlf").strip() == "false"
    assert work.locate(repo, "build-lead").adopted


def test_adopt_refuses_what_it_cannot_register(repo: Path, tmp_path: Path) -> None:
    stray = tmp_path / "stray"
    _ = _git_out(repo, "clone", "-q", str(repo), str(stray))
    assert work.main(["adopt", str(stray), "build-stray"]) == 1
    plain = tmp_path / "plain"
    plain.mkdir()
    assert work.main(["adopt", str(plain), "build-plain"]) == 1
    assert work.main(["adopt", str(tmp_path / "missing"), "build-missing"]) == 1
    foreign = repo / ".work" / "clones" / "build-foreign"
    foreign.parent.mkdir(parents=True)
    other = tmp_path / "other"
    _ = _git_out(tmp_path, "init", "-q", str(other))
    _ = _git_out(other, "commit", "-q", "--allow-empty", "-m", "x")
    _ = _git_out(tmp_path, "clone", "-q", str(other), str(foreign))
    assert work.main(["adopt", str(foreign), "build-foreign"]) == 1
    inside = repo / ".work" / "worktrees" / "spike-folder"
    _ = _git_out(repo, "worktree", "add", "-q", "--detach", str(inside))
    assert work.main(["adopt", str(inside), "spike-other"]) == 1


# --------------------------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------------------------


def test_list_derives_every_state_from_folders_worktrees_and_pins(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _ = _new("build-live")
    landed = _new("fix-landed")
    _ = _write(landed / "gone.txt", "edited\n")
    assert work.main(["land", "fix-landed"]) == 0
    gone = _new("spike-gone", "--worktree")
    work.delete_tree(gone)
    broken = _new("ci-broken")
    work.delete_tree(broken / ".git")
    _plant(repo, "bench-old", "save-1")
    _ = capsys.readouterr()
    assert work.main(["list", "--json"]) == 0
    listing = json_list(json_loads(capsys.readouterr().out))
    rows = {str(json_at(row, "name")): json_object(row) for row in listing}
    assert {name: row["state"] for name, row in rows.items()} == {
        "bench-old": "pins-only",
        "build-live": "live",
        "ci-broken": "broken",
        "fix-landed": "landed",
        "spike-gone": "folder-gone",
    }
    assert rows["build-live"]["purpose"] == "a test"
    assert work.main(["list"]) == 0
    text = capsys.readouterr().out
    assert "build-live" in text
    assert "# a test" in text


def test_list_shows_the_owner_and_the_pins_the_note_and_pins_git_agree_on(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``pins=`` is what the note attributes and ``pins.git`` holds; the rest is named apart."""
    path = _new("fix-owned", "--owner", "bug hunt session")
    head = _git_out(path, "rev-parse", "HEAD").strip()
    note = work._config_values(path, "--local")
    assert work.recorded_pins(note) == {"start": head}
    _ = capsys.readouterr()
    assert work.main(["list"]) == 0
    line = capsys.readouterr().out
    assert "pins=start adopted=no owner='bug hunt session' " in line
    assert "foreign-pins" not in line
    assert "missing-pins" not in line
    _plant(repo, "fix-owned", "save-9")
    _ = _git_out(_store(repo), "update-ref", "-d", "refs/work/fix-owned/start")
    assert work.main(["list", "--json"]) == 0
    [row] = json_list(json_loads(capsys.readouterr().out))
    assert json_object(row)["pins"] == "-"
    assert json_object(row)["foreign"] == "save-9"
    assert json_object(row)["missing"] == "start"
    assert json_object(row)["owner"] == "bug hunt session"
    assert work.main(["list"]) == 0
    assert "pins=- foreign-pins=save-9 missing-pins=start " in capsys.readouterr().out


@pytest.mark.usefixtures("repo")
def test_a_new_clone_keeps_no_branch_tracking_config() -> None:
    """Its ``HEAD`` is detached: nothing in it tracks the branch ``git clone`` made."""
    path = _new("fix-detached")
    assert _git.run_git(path, "config", "--local", "--get-regexp", r"^branch\.").stdout == ""
    assert _git.run_git(path, "symbolic-ref", "--quiet", "HEAD").returncode != 0
    assert _git_out(path, "remote", "get-url", "parent").strip() == str(work.REPO_ROOT)


# --------------------------------------------------------------------------------------------
# save
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_save_pins_uncommitted_content_without_touching_either_index(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    form: list[str],
) -> None:
    path = _new("spike-save", *form)
    assert work.main(["save", "spike-save"]) == 0
    assert "nothing to save" in capsys.readouterr().err
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "new.txt", "untracked\n")
    (path / "gone.txt").unlink()
    parent_index = (repo / ".git" / "index").read_bytes()
    copy_index = Path(
        _git_out(path, "rev-parse", "--path-format=absolute", "--git-path", "index").strip(),
    )
    copy_index_bytes = copy_index.read_bytes()
    assert work.main(["save", "spike-save"]) == 0
    assert capsys.readouterr().out.strip() == "refs/work/spike-save/save-1"
    saved = _pins(repo)["spike-save"]["save-1"]
    assert _git_out(_store(repo), "show", f"{saved}:new.txt") == "untracked\n"
    assert _git_out(_store(repo), "show", f"{saved}:{PACKAGE}/core.py") == "CORE = 3\n"
    assert "gone.txt" not in _git_out(_store(repo), "ls-tree", "--name-only", saved)
    assert (repo / ".git" / "index").read_bytes() == parent_index
    assert copy_index.read_bytes() == copy_index_bytes
    assert work.main(["save", "spike-save"]) == 0
    assert capsys.readouterr().out.strip() == "refs/work/spike-save/save-2"


def test_save_of_a_commit_the_copy_made_pins_that_commit(repo: Path) -> None:
    path = _new("spike-commit")
    _ = _write(path / "made.txt", "committed\n")
    _ = _git_out(path, "add", "made.txt")
    _ = _git_out(path, "commit", "-q", "-m", "copy commit")
    assert work.main(["save", "spike-commit"]) == 0
    head = _git_out(path, "rev-parse", "HEAD").strip()
    assert _pins(repo)["spike-commit"]["save-1"] == head
    work.delete_tree(path)
    assert _git_out(_store(repo), "cat-file", "-t", head).strip() == "commit"


def test_save_and_run_refuse_a_copy_without_a_folder(repo: Path) -> None:
    _plant(repo, "bench-old", "save-1")
    assert work.main(["save", "bench-old"]) == 1
    assert work.main(["save", "bench-unknown"]) == 1


# --------------------------------------------------------------------------------------------
# land
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_land_applies_the_copy_to_the_shared_working_tree_and_never_its_index(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    form: list[str],
) -> None:
    path = _new("fix-i681-land", *form)
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "docs" / "new.md", "new\n")
    (path / "gone.txt").unlink()
    index = (repo / ".git" / "index").read_bytes()
    _ = capsys.readouterr()
    assert work.main(["land", "fix-i681-land"]) == 0
    out = capsys.readouterr().out
    assert sorted(out.split()) == sorted(
        [
            "landed:",
            "landed:",
            "landed:",
            f"{PACKAGE}/core.py",
            "docs/new.md",
            "gone.txt",
        ],
    )
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"
    assert (repo / "docs" / "new.md").read_text(encoding="utf-8") == "new\n"
    assert not (repo / "gone.txt").exists()
    assert (repo / ".git" / "index").read_bytes() == index
    assert _git_out(repo, "diff", "--cached", "--name-only") == ""
    note = work.locate(repo, "fix-i681-land").note
    assert note["landed"] == _git_out(repo, "rev-parse", "HEAD").strip()
    assert note["landedtree"] == work.content_tree(path)


def test_land_skips_a_path_the_shared_tree_already_holds_and_refuses_one_dirty_otherwise(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-dirty")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "gone.txt", "copy edit\n")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(repo / "gone.txt", "their edit\n")
    assert work.main(["land", "fix-dirty"]) == 1
    assert "gone.txt" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "their edit\n"
    _ = _write(repo / "gone.txt", "copy edit\n")
    assert work.main(["land", "fix-dirty"]) == 0
    captured = capsys.readouterr()
    assert "already there: gone.txt" in captured.err
    assert f"already there: {PACKAGE}/core.py" in captured.err
    assert "nothing to land" in captured.err


def test_land_never_writes_through_a_symlinked_shared_folder(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "pkg").symlink_to(outside, target_is_directory=True)
    path = _new("fix-through")
    _ = _write(path / "pkg" / "payload.txt", "payload\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-through"]) == 1
    assert "pkg in the shared checkout is a symlink" in capsys.readouterr().err
    assert list(outside.iterdir()) == []
    assert (repo / "pkg").is_symlink()


def test_land_writes_a_symlink_blob_as_a_link(repo: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    path = _new("fix-link-blob")
    (path / "link").symlink_to(outside, target_is_directory=True)
    assert work.main(["land", "fix-link-blob"]) == 0
    assert (repo / "link").readlink() == outside
    assert list(outside.iterdir()) == []


def test_land_refuses_a_staged_or_untracked_change_at_a_path_it_touches(repo: Path) -> None:
    path = _new("fix-staged")
    _ = _write(path / "docs" / "new.md", "copy\n")
    _ = _write(repo / "docs" / "new.md", "theirs, untracked\n")
    assert work.main(["land", "fix-staged"]) == 1
    (repo / "docs" / "new.md").unlink()
    _ = _write(path / "gone.txt", "copy\n")
    _ = _write(repo / "gone.txt", "staged\n")
    _ = _git_out(repo, "add", "gone.txt")
    _ = _write(repo / "gone.txt", "to delete\n")
    assert work.main(["land", "fix-staged"]) == 1


def test_land_dry_run_and_patch_apply_nothing(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-dry")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    patch = tmp_path / "fix.patch"
    _ = capsys.readouterr()
    assert (
        work.main(
            [
                "land",
                "fix-dry",
                "--dry-run",
                "--patch",
                str(patch),
            ],
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == f"would land: {PACKAGE}/core.py"
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert b"+CORE = 3" in patch.read_bytes()
    assert "landed" not in work.locate(repo, "fix-dry").note


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 folder")
@pytest.mark.parametrize("mode", [0o000, 0o444], ids=["unlistable", "listable-not-enterable"])
def test_an_unreadable_folder_refuses_land_and_save_instead_of_reading_deleted(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    mode: int,
) -> None:
    path = _new("fix-unreadable")
    fresh = path / "fresh"
    _ = _write(fresh / "new.txt", "untracked work\n")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    for folder, shown in ((path / PACKAGE, PACKAGE), (fresh, "fresh")):
        folder.chmod(mode)
        try:
            _ = capsys.readouterr()
            assert work.main(["land", "fix-unreadable", "--dry-run"]) == 1
            assert work.main(["save", "fix-unreadable"]) == 1
            captured = capsys.readouterr()
        finally:
            folder.chmod(0o755)
        assert f"cannot read {shown} in {path}: Permission denied" in captured.err
        assert "would land" not in captured.out
        assert _pins(repo).get("fix-unreadable", {}).keys() <= {"start"}


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 folder")
@pytest.mark.parametrize("mode", [0o000, 0o644], ids=["unlistable", "listable-not-enterable"])
def test_land_refuses_a_deletion_whose_shared_folder_cannot_be_read(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    mode: int,
) -> None:
    path = _new("fix-gone-shared")
    (path / PACKAGE / "core.py").unlink()
    (repo / PACKAGE).chmod(mode)
    try:
        _ = capsys.readouterr()
        assert work.main(["land", "fix-gone-shared", "--dry-run"]) == 1
        captured = capsys.readouterr()
    finally:
        (repo / PACKAGE).chmod(0o755)
    assert f"cannot read {PACKAGE} in {repo}: Permission denied" in captured.err
    assert "nothing to land" not in captured.out
    assert "already there" not in captured.err


DB = Path("examples") / "fakeshop" / "db.sqlite3"


def _sql(path: Path, *statements: str) -> None:
    connection = sqlite3.connect(path, isolation_level=None)
    for statement in statements:
        _ = connection.execute(statement)
    connection.close()


def _terms(path: Path) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(path)
    rows = _fetchall(connection.execute("SELECT id, body FROM term ORDER BY id"))
    connection.close()
    return rows


def _commit_db(repo: Path, *statements: str) -> None:
    """Commit the shared database after ``statements`` (a fresh one first if it is no SQLite)."""
    path = repo / DB
    if not path.read_bytes().startswith(b"SQLite format 3"):
        path.unlink()
        _sql(path, "CREATE TABLE term (id integer PRIMARY KEY, body text NOT NULL)")
    _sql(path, *statements)
    _ = _git_out(repo, "commit", "-qam", "database")


def test_land_merges_the_copys_database_rows_onto_a_moved_main(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _commit_db(repo, "INSERT INTO term VALUES (1, 'one'), (2, 'two')")
    path = _new("fix-db")
    _sql(path / DB, "UPDATE term SET body = 'ONE' WHERE id = 1")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _commit_db(repo, "UPDATE term SET body = 'TWO' WHERE id = 2")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-db"]) == 0
    out = capsys.readouterr().out
    assert f"landed: {DB.as_posix()}\n  rows: term: update 1\n" in out
    assert _terms(repo / DB) == [(1, "ONE"), (2, "TWO")]
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"


def test_land_refuses_a_database_row_main_changed_too_and_applies_nothing(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _commit_db(repo, "INSERT INTO term VALUES (1, 'one')")
    path = _new("fix-db")
    _sql(path / DB, "UPDATE term SET body = 'mine' WHERE id = 1")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _commit_db(repo, "UPDATE term SET body = 'main' WHERE id = 1")
    held = (repo / DB).read_bytes()
    assert work.main(["land", "fix-db"]) == 1
    err = capsys.readouterr().err
    assert "term rowid 1: changed here and on main; nothing applied" in err
    assert (repo / DB).read_bytes() == held
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"


def test_land_skips_a_database_whose_bytes_moved_but_no_row(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _commit_db(repo, "INSERT INTO term VALUES (1, 'one')")
    path = _new("fix-db")
    _sql(
        path / DB,
        "INSERT INTO term VALUES (2, 'two')",
        "DELETE FROM term WHERE id = 2",
        "VACUUM",
    )
    assert work.main(["land", "fix-db"]) == 0
    captured = capsys.readouterr()
    assert f"already there: {DB.as_posix()}" in captured.err
    assert "nothing to land" in captured.err
    assert not _git_out(repo, "status", "--porcelain", "--", DB.as_posix())


def test_land_refuses_a_database_file_that_is_not_sqlite(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-db")
    _ = _write(path / DB, "rows\n")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-db"]) == 1
    assert "cannot be read as a SQLite database" in capsys.readouterr().err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"


def test_land_refuses_a_copy_database_with_a_live_wal(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _commit_db(repo, "INSERT INTO term VALUES (1, 'one'), (2, 'two')")
    path = _new("fix-db")
    writer = sqlite3.connect(path / DB)
    try:
        _ = writer.execute("PRAGMA journal_mode = WAL")
        _ = writer.execute("PRAGMA wal_autocheckpoint = 0")
        _ = writer.execute("UPDATE term SET body = 'WAL' WHERE id = 1")
        writer.commit()
        _commit_db(repo, "UPDATE term SET body = 'MAIN' WHERE id = 2")
        held = (repo / DB).read_bytes()
        assert work.main(["land", "fix-db"]) == 1
        assert "db.sqlite3-wal holds database writes its file does not" in capsys.readouterr().err
        assert (repo / DB).read_bytes() == held
    finally:
        writer.close()


def test_land_patch_carries_the_merged_database(repo: Path, tmp_path: Path) -> None:
    _commit_db(repo, "INSERT INTO term VALUES (1, 'one')")
    path = _new("fix-db")
    _sql(path / DB, "UPDATE term SET body = 'ONE' WHERE id = 1")
    patch = tmp_path / "landing.patch"
    assert (
        work.main(
            [
                "land",
                "fix-db",
                "--dry-run",
                "--patch",
                str(patch),
            ],
        )
        == 0
    )
    assert f"diff --git a/{DB.as_posix()} b/{DB.as_posix()}".encode() in patch.read_bytes()
    assert not _git_out(repo, "status", "--porcelain", "--", DB.as_posix())
    _ = _git_out(repo, "apply", str(patch))
    assert _terms(repo / DB) == [(1, "ONE")]


def test_land_again_takes_only_the_rows_changed_since_the_last_landing(repo: Path) -> None:
    _commit_db(repo, "INSERT INTO term VALUES (1, 'one'), (2, 'two')")
    path = _new("fix-db")
    _sql(path / DB, "UPDATE term SET body = 'ONE' WHERE id = 1")
    assert work.main(["land", "fix-db"]) == 0
    _ = _git_out(repo, "commit", "-qam", "first database landing")
    _commit_db(repo, "UPDATE term SET body = 'TWO' WHERE id = 2")
    _sql(path / DB, "UPDATE term SET body = 'ONE AGAIN' WHERE id = 1")
    assert work.main(["land", "fix-db"]) == 0
    assert _terms(repo / DB) == [(1, "ONE AGAIN"), (2, "TWO")]


def test_land_refuses_a_copy_whose_commits_are_not_on_main(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-commit")
    _ = _write(path / "made.txt", "committed\n")
    _ = _git_out(path, "add", "made.txt")
    _ = _git_out(path, "commit", "-q", "-m", "copy commit")
    assert work.main(["land", "fix-commit"]) == 1
    assert "copies do not commit" in capsys.readouterr().err
    assert not (repo / "made.txt").exists()


def test_land_lands_onto_a_main_that_moved_since_the_copy_started(repo: Path) -> None:
    path = _new("fix-moved")
    _ = _write(repo / "other.txt", "landed meanwhile\n")
    _ = _git_out(repo, "add", "other.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "meanwhile")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-moved"]) == 0
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"
    assert (repo / "other.txt").is_file()


def test_land_refuses_a_shared_checkout_off_main(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-detached")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _git_out(repo, "checkout", "-q", "--detach")
    assert work.main(["land", "fix-detached"]) == 1
    assert "not refs/heads/main" in capsys.readouterr().err


def test_land_refuses_a_patch_that_does_not_apply(
    repo: Path,
) -> None:
    path = _new("fix-conflict")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 9\n")
    _ = _git_out(repo, "commit", "-q", "-am", "moved the same line")
    assert work.main(["land", "fix-conflict"]) == 1
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 9\n"


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_a_copy_lands_again_once_main_commits_its_landing(repo: Path, form: list[str]) -> None:
    path = _new("fix-again", *form)
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-again"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits the landing")
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    assert work.main(["land", "fix-again"]) == 0
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 4\n"
    assert _git_out(repo, "status", "--porcelain") == f" M {PACKAGE}/core.py\n"
    assert _git_out(repo, "diff", "--cached", "--name-only") == ""


OWN = "the shared tree holds this copy's own uncommitted landing in "


def test_a_second_landing_before_main_commits_the_first_is_refused(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-uncommitted")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-uncommitted"]) == 0
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-uncommitted"]) == 1
    err = capsys.readouterr().err
    assert OWN + f"{PACKAGE}/core.py (the maintainer commits it first)" in err
    assert "other changes" not in err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"


def test_a_landing_onto_another_writers_change_to_a_landed_path_names_that_writer(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-overwritten")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-overwritten"]) == 0
    _ = _write(repo / PACKAGE / "core.py", "CORE = MAIN\n")
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-overwritten"]) == 1
    err = capsys.readouterr().err
    assert f"the shared tree holds other changes in {PACKAGE}/core.py (land after" in err
    assert OWN not in err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = MAIN\n"


def test_a_path_main_held_before_the_landing_reads_as_other_changes(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-held-before")
    _ = _write(repo / "gone.txt", "same\n")
    _ = _write(path / "gone.txt", "same\n")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-held-before"]) == 0
    _ = _write(path / "gone.txt", "later\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-held-before"]) == 1
    err = capsys.readouterr().err
    assert "the shared tree holds other changes in gone.txt (land after" in err
    assert OWN not in err


def test_landed_bytes_written_back_after_main_moved_read_as_other_changes(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-written-back")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-written-back"]) == 0
    _ = _write(repo / PACKAGE / "core.py", "CORE = 5\n")
    _ = _git_out(repo, "commit", "-q", "-am", "main moves on")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _ = _git_out(repo, "add", f"{PACKAGE}/core.py")
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-written-back"]) == 1
    err = capsys.readouterr().err
    assert f"the shared tree holds other changes in {PACKAGE}/core.py (land after" in err
    assert OWN not in err


def test_a_landed_path_another_writer_staged_reads_as_other_changes(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-staged-over")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-staged-over"]) == 0
    _ = _write(repo / PACKAGE / "core.py", "CORE = OTHER\n")
    _ = _git_out(repo, "add", f"{PACKAGE}/core.py")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-staged-over"]) == 1
    err = capsys.readouterr().err
    assert f"the shared tree holds other changes in {PACKAGE}/core.py (land after" in err
    assert OWN not in err


def test_a_landing_onto_its_own_and_another_writers_changes_names_each(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-mixed")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "gone.txt", "copy\n")
    assert work.main(["land", "fix-mixed"]) == 0
    _ = _write(repo / "gone.txt", "main\n")
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = _write(path / "gone.txt", "copy again\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-mixed"]) == 1
    err = capsys.readouterr().err
    assert OWN + f"{PACKAGE}/core.py (the maintainer commits it first)" in err
    assert "the shared tree holds other changes in gone.txt (land after" in err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "main\n"


NOTE = "not re-applied: main does not hold the copy's earlier landing of"


def test_a_partly_committed_landing_lands_the_copys_later_work_onto_either_part(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-partly")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "gone.txt", "copy\n")
    assert work.main(["land", "fix-partly"]) == 0
    _ = _git_out(repo, "commit", "-q", "-m", "the maintainer commits part", f"{PACKAGE}/core.py")
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-partly"]) == 0
    assert NOTE not in capsys.readouterr().err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 4\n"
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "copy\n"
    _ = _write(path / "gone.txt", "copy again\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-partly"]) == 1
    assert "the shared tree holds other changes in gone.txt" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "copy\n"


def _land_and_commit(
    repo: Path,
    name: str,
    path: Path,
    rel: str,
    content: str,
) -> None:
    """Write ``rel`` in the copy, land it and commit it on main, as the maintainer would."""
    _ = _write(path / rel, content)
    assert work.main(["land", name]) == 0
    _ = _git_out(repo, "add", "-A")
    _ = _git_out(repo, "commit", "-q", "-m", f"the maintainer commits {rel}")


def test_a_path_the_copy_changed_again_after_main_changed_it_is_refused_and_named(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-diverged")
    _land_and_commit(repo, "fix-diverged", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 9\n")
    _ = _git_out(repo, "commit", "-q", "-am", "and changes it")
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = _write(path / "gone.txt", "copy\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-diverged"]) == 1
    err = capsys.readouterr().err
    assert f"does not apply onto the shared HEAD {_git_out(repo, 'rev-parse', 'HEAD')[:12]}" in err
    assert f" in {PACKAGE}/core.py;" in err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 9\n"
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"


def test_a_landed_path_main_changed_since_stays_mains_when_the_copy_lands_another(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-main-changed")
    _land_and_commit(repo, "fix-main-changed", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 9\n")
    _ = _git_out(repo, "commit", "-q", "-am", "main changes the landed path")
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-main-changed"]) == 0
    assert f"{NOTE} {PACKAGE}/core.py" in capsys.readouterr().err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 9\n"
    assert (repo / "other.txt").read_text(encoding="utf-8") == "other\n"


def test_a_discarded_uncommitted_landing_is_named_and_from_start_lands_it_again(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-discarded")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-discarded"]) == 0
    _ = _git_out(repo, "checkout", "-q", "--", f"{PACKAGE}/core.py")
    _ = _write(path / "gone.txt", "copy\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-discarded"]) == 0
    captured = capsys.readouterr()
    assert f"{NOTE} {PACKAGE}/core.py" in captured.err
    assert "land --from-start" in captured.err
    assert captured.out.split() == ["landed:", "gone.txt"]
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert work.main(["land", "fix-discarded", "--from-start"]) == 0
    captured = capsys.readouterr()
    assert NOTE not in captured.err
    assert captured.out.split() == ["landed:", f"{PACKAGE}/core.py"]
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"


def _undo(repo: Path, how: str) -> None:
    if how == "revert":
        _ = _git_out(repo, "revert", "--no-edit", "HEAD")
    else:
        _ = _git_out(repo, "reset", "-q", "--hard", "HEAD~1")


@pytest.mark.parametrize("undo", ["revert", "reset"])
def test_a_landing_main_undid_is_named_and_never_reapplied_while_the_rest_lands(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    undo: str,
) -> None:
    path = _new("fix-undone")
    _land_and_commit(repo, "fix-undone", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    _undo(repo, undo)
    _ = _write(path / "gone.txt", "copy\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-undone"]) == 0
    assert f"{NOTE} {PACKAGE}/core.py" in capsys.readouterr().err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "copy\n"


@pytest.mark.parametrize("undo", ["revert", "reset"])
def test_a_landing_main_undid_and_the_copy_changed_again_is_refused_and_named(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    undo: str,
) -> None:
    path = _new("fix-undone-edit")
    _land_and_commit(repo, "fix-undone-edit", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    _undo(repo, undo)
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-undone-edit"]) == 1
    assert f" in {PACKAGE}/core.py;" in capsys.readouterr().err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"


def test_a_landed_new_file_main_reverted_is_named_and_never_recreated(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-unadded")
    _land_and_commit(repo, "fix-unadded", path, "docs/new.md", "new\n")
    _undo(repo, "revert")
    _ = _write(path / "gone.txt", "copy\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-unadded"]) == 0
    assert f"{NOTE} docs/new.md" in capsys.readouterr().err
    assert not (repo / "docs" / "new.md").exists()
    _ = _write(path / "docs" / "new.md", "new again\n")
    assert work.main(["land", "fix-unadded"]) == 1
    assert " in docs/new.md;" in capsys.readouterr().err
    assert not (repo / "docs" / "new.md").exists()


def test_an_older_landing_main_reverted_is_never_reapplied_by_a_later_one(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-older")
    _land_and_commit(repo, "fix-older", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    first = _git_out(repo, "rev-parse", "HEAD").strip()
    _land_and_commit(repo, "fix-older", path, "q.txt", "q\n")
    _ = _git_out(repo, "revert", "--no-edit", first)
    _ = _write(path / "r.txt", "r\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-older"]) == 0
    assert f"{NOTE} {PACKAGE}/core.py" in capsys.readouterr().err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert (repo / "r.txt").read_text(encoding="utf-8") == "r\n"


def test_a_path_skipped_as_already_there_that_main_reverted_is_never_reapplied(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-skip-undone")
    _ = _write(path / "gone.txt", "copy\n")
    _ = _write(repo / "gone.txt", "copy\n")
    _ = _git_out(repo, "commit", "-q", "-am", "another session commits the same edit")
    theirs = _git_out(repo, "rev-parse", "HEAD").strip()
    _ = capsys.readouterr()
    _land_and_commit(repo, "fix-skip-undone", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    assert "already there: gone.txt" in capsys.readouterr().err
    _ = _git_out(repo, "revert", "--no-edit", theirs)
    _ = _write(path / "r.txt", "r\n")
    assert work.main(["land", "fix-skip-undone"]) == 0
    assert f"{NOTE} gone.txt" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
    assert (repo / "r.txt").read_text(encoding="utf-8") == "r\n"


@pytest.mark.parametrize("leaf", [work.LANDED_PIN, work.LANDED_COPY_PIN])
def test_a_recorded_landing_whose_pin_is_gone_refuses_until_from_start(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    leaf: str,
) -> None:
    path = _new("fix-pin-gone")
    _land_and_commit(repo, "fix-pin-gone", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    _undo(repo, "revert")
    work.drop_pin(repo, "fix-pin-gone", leaf)
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-pin-gone"]) == 1
    err = capsys.readouterr().err
    assert f"fix-pin-gone records a landing, but refs/work/fix-pin-gone/{leaf} is missing" in err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert not (repo / "other.txt").exists()
    assert work.main(["land", "fix-pin-gone", "--from-start"]) == 0
    assert (repo / "other.txt").read_text(encoding="utf-8") == "other\n"


def test_a_recorded_landing_whose_pin_another_copy_replaced_refuses(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-pin-foreign")
    _land_and_commit(repo, "fix-pin-foreign", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    work.drop_pin(repo, "fix-pin-foreign", work.LANDED_COPY_PIN)
    _plant(repo, "fix-pin-foreign", work.LANDED_COPY_PIN)
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-pin-foreign"]) == 1
    assert "refs/work/fix-pin-foreign/landed-copy is missing, not this copy's" in (
        capsys.readouterr().err
    )
    assert not (repo / "other.txt").exists()


def test_a_recorded_landing_whose_pin_lost_its_commit_refuses(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-pin-hollow")
    _land_and_commit(repo, "fix-pin-hollow", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    commit = _pins(repo)["fix-pin-hollow"][work.LANDED_COPY_PIN]
    loose = _store(repo) / "objects" / commit[:2] / commit[2:]
    assert loose.is_file()
    loose.unlink()
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-pin-hollow"]) == 1
    assert "or incomplete in pins.git" in capsys.readouterr().err
    assert not (repo / "other.txt").exists()


@pytest.mark.parametrize("undo", ["reset", "checkout"])
def test_a_copy_put_back_at_its_start_never_undoes_mains_committed_landing(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    undo: str,
) -> None:
    path = _new("fix-copy-reset")
    _land_and_commit(repo, "fix-copy-reset", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    if undo == "reset":
        _ = _git_out(path, "reset", "-q", "--hard")
    else:
        _ = _git_out(path, "checkout", "-q", "--", f"{PACKAGE}/core.py")
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-copy-reset"]) == 1
    err = capsys.readouterr().err
    assert (
        f"the copy is back at its start in {PACKAGE}/core.py, where its last landing held" in err
    )
    assert "land --from-start" in err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"
    assert not (repo / "other.txt").exists()
    assert work.main(["land", "fix-copy-reset", "--from-start"]) == 0
    assert capsys.readouterr().out.split() == ["landed:", "other.txt"]
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"
    assert (repo / "other.txt").read_text(encoding="utf-8") == "other\n"


@pytest.mark.parametrize("undo", ["reset", "checkout"])
def test_a_copy_put_back_at_its_start_never_undoes_its_hunk_beside_mains_own(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    undo: str,
) -> None:
    _ = _write(repo / "multi.txt", MULTILINE)
    _ = _git_out(repo, "add", "multi.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "multiline")
    path = _new("fix-copy-reset-hunk")
    copied = MULTILINE.replace("line 0\n", "COPY\n")
    _land_and_commit(repo, "fix-copy-reset-hunk", path, "multi.txt", copied)
    _ = _write(repo / "multi.txt", copied.replace("line 29\n", "MAIN\n"))
    _ = _git_out(repo, "commit", "-q", "-am", "main edits another hunk")
    if undo == "reset":
        _ = _git_out(path, "reset", "-q", "--hard")
    else:
        _ = _git_out(path, "checkout", "-q", "--", ".")
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-copy-reset-hunk"]) == 1
    assert "the copy is back at its start in multi.txt" in capsys.readouterr().err
    assert (repo / "multi.txt").read_text(encoding="utf-8") == copied.replace(
        "line 29\n",
        "MAIN\n",
    )
    assert not (repo / "other.txt").exists()


def test_a_copy_and_main_both_back_at_the_start_land_the_rest(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-both-start")
    _land_and_commit(repo, "fix-both-start", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    _undo(repo, "revert")
    _ = _git_out(path, "reset", "-q", "--hard")
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-both-start"]) == 0
    captured = capsys.readouterr()
    assert NOTE not in captured.err
    assert captured.out.split() == ["landed:", "other.txt"]
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"


def test_each_landing_moves_both_landing_pins_to_itself(repo: Path) -> None:
    path = _new("fix-pins-move")
    _land_and_commit(repo, "fix-pins-move", path, "a.txt", "a\n")
    _land_and_commit(repo, "fix-pins-move", path, "b.txt", "b\n")
    _ = _write(path / "b.txt", "b2\n")
    assert work.main(["land", "fix-pins-move"]) == 0
    assert (repo / "b.txt").read_text(encoding="utf-8") == "b2\n"
    leaves = _pins(repo)["fix-pins-move"]
    store = _store(repo)
    own = leaves[work.LANDED_COPY_PIN]
    assert _git_out(store, "rev-parse", f"{own}^{{tree}}").strip() == work.content_tree(path)
    merged = leaves[work.LANDED_PIN]
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    assert _git_out(store, "rev-parse", f"{merged}^").strip() == head
    assert _git_out(store, "show", f"{merged}:b.txt") == "b2\n"
    note = work.locate(repo, "fix-pins-move").note
    assert work.pin_belongs(note, work.LANDED_PIN, merged)
    assert work.pin_belongs(note, work.LANDED_COPY_PIN, own)


def test_a_copy_put_back_at_its_start_where_main_moved_off_its_landing_lands_from_start(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-reset-none")
    _land_and_commit(repo, "fix-reset-none", path, f"{PACKAGE}/core.py", "CORE = 3\n")
    _undo(repo, "revert")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 9\n")
    _ = _git_out(repo, "commit", "-q", "-am", "main edits the file again")
    _ = _git_out(path, "reset", "-q", "--hard")
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-reset-none"]) == 1
    err = capsys.readouterr().err
    assert f"the copy is back at its start in {PACKAGE}/core.py, where its last landing" in err
    assert "`land --from-start` lands the rest and leaves those paths as main holds them" in err
    assert not (repo / "other.txt").exists()
    assert work.main(["land", "fix-reset-none", "--from-start"]) == 0
    assert capsys.readouterr().out.split() == ["landed:", "other.txt"]
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 9\n"


def test_a_copy_put_back_at_its_start_where_main_holds_one_landed_hunk_is_refused(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _ = _write(repo / "multi.txt", MULTILINE)
    _ = _git_out(repo, "add", "multi.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "multiline")
    path = _new("fix-reset-part")
    landed = MULTILINE.replace("line 0\n", "COPY\n").replace("line 29\n", "COPY 29\n")
    _land_and_commit(repo, "fix-reset-part", path, "multi.txt", landed)
    kept = landed.replace("COPY\n", "line 0\n")
    _ = _write(repo / "multi.txt", kept)
    _ = _git_out(repo, "commit", "-q", "-am", "main takes back one hunk")
    _ = _git_out(path, "reset", "-q", "--hard")
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-reset-part"]) == 1
    assert "back at its start in multi.txt, where its last landing held other" in (
        capsys.readouterr().err
    )
    assert (repo / "multi.txt").read_text(encoding="utf-8") == kept
    assert not (repo / "other.txt").exists()


def test_a_landing_pin_another_copy_left_under_the_name_is_never_a_patch_base(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-foreign")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 7\n")
    _ = _git_out(repo, "commit", "-q", "-am", "main moves the line")
    _plant(repo, "fix-foreign", work.LANDED_PIN)
    _plant(repo, "fix-foreign", work.LANDED_COPY_PIN)
    _ = _write(path / PACKAGE / "core.py", "CORE = 4\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-foreign"]) == 1
    assert "does not apply" in capsys.readouterr().err
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 7\n"


def test_a_path_skipped_as_already_there_lands_again_once_main_commits_it(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-skipped")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "gone.txt", "copy\n")
    _ = _write(repo / "gone.txt", "copy\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-skipped"]) == 0
    assert "already there: gone.txt" in capsys.readouterr().err
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits both")
    _ = _write(path / "gone.txt", "copy again\n")
    assert work.main(["land", "fix-skipped"]) == 0
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "copy again\n"


def test_a_landing_merged_onto_a_moved_main_lands_again_keeping_mains_change(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _ = _write(repo / "multi.txt", MULTILINE)
    _ = _git_out(repo, "add", "multi.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "multiline")
    path = _new("fix-merged-again")
    _ = _write(path / "multi.txt", MULTILINE.replace("line 0\n", "COPY\n"))
    _ = _write(repo / "multi.txt", MULTILINE.replace("line 29\n", "MAIN\n"))
    _ = _git_out(repo, "commit", "-q", "-am", "another session")
    assert work.main(["land", "fix-merged-again"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits the landing")
    _ = _write(path / "other.txt", "other\n")
    _ = capsys.readouterr()
    assert work.main(["land", "fix-merged-again"]) == 0
    assert NOTE not in capsys.readouterr().err
    _ = _git_out(repo, "add", "other.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "the maintainer commits it")
    _ = _write(path / "multi.txt", MULTILINE.replace("line 0\n", "COPY 2\n"))
    assert work.main(["land", "fix-merged-again"]) == 0
    landed = (repo / "multi.txt").read_text(encoding="utf-8")
    assert landed == MULTILINE.replace("line 0\n", "COPY 2\n").replace("line 29\n", "MAIN\n")


def test_a_file_added_after_a_committed_landing_lands_alone(repo: Path) -> None:
    path = _new("fix-added")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-added"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits the landing")
    _ = _write(path / "docs" / "new.md", "new\n")
    assert work.main(["land", "fix-added"]) == 0
    assert (repo / "docs" / "new.md").read_text(encoding="utf-8") == "new\n"
    assert _git_out(repo, "status", "--porcelain") == "?? docs/\n"


def test_a_file_deleted_after_a_committed_landing_is_deleted(repo: Path) -> None:
    path = _new("fix-deleted")
    _ = _write(path / "docs" / "new.md", "new\n")
    assert work.main(["land", "fix-deleted"]) == 0
    _ = _git_out(repo, "add", "docs/new.md")
    _ = _git_out(repo, "commit", "-q", "-m", "the maintainer commits the landing")
    (path / "docs" / "new.md").unlink()
    assert work.main(["land", "fix-deleted"]) == 0
    assert not (repo / "docs" / "new.md").exists()
    assert _git_out(repo, "status", "--porcelain") == " D docs/new.md\n"


# --------------------------------------------------------------------------------------------
# rm
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_rm_moves_the_copy_to_trash_deletes_it_and_keeps_saves_and_evidence(
    repo: Path,
    form: list[str],
) -> None:
    path = _new("spike-rm", *form)
    _ = _write(path / "new.txt", "spike\n")
    assert work.main(["save", "spike-rm"]) == 0
    (path / "readonly").mkdir()
    _ = _write(path / "readonly" / "locked.txt", "x\n")
    (path / "readonly" / "locked.txt").chmod(0o444)
    (path / "readonly").chmod(0o555)
    sealed = path / "sealed"
    _ = _write(sealed / "inner" / "x.txt", "x\n")
    _age(path)
    (sealed / "inner").chmod(0o000)
    sealed.chmod(0o000)
    try:
        assert work.main(["rm", "spike-rm"]) == 1
        assert work.main(["rm", "spike-rm", "--discard"]) == 0
    finally:
        if path.is_dir():
            sealed.chmod(0o755)
            (sealed / "inner").chmod(0o755)
    assert not path.exists()
    assert list((repo / ".work" / "trash").iterdir()) == []
    assert work.worktree_entries(repo) == []
    assert set(_pins(repo)["spike-rm"]) == {"save-1"}
    assert (repo / ".work" / "evidence" / "spike-rm").is_dir()
    assert (
        work.main(
            [
                "rm",
                "spike-rm",
                "--drop-saves",
                "--evidence",
            ],
        )
        == 0
    )
    assert _pins(repo) == {}
    assert not (repo / ".work" / "evidence" / "spike-rm").exists()


@pytest.mark.usefixtures("repo")
def test_rm_right_after_landing_or_saving_needs_no_wait() -> None:
    landed = _new("fix-quick")
    _ = _write(landed / "gone.txt", "edited\n")
    assert work.main(["land", "fix-quick"]) == 0
    assert work.main(["rm", "fix-quick"]) == 0
    saved = _new("spike-quick")
    _ = _write(saved / "new.txt", "kept in the pin\n")
    assert work.main(["save", "spike-quick"]) == 0
    assert work.main(["rm", "spike-quick"]) == 0


@pytest.mark.usefixtures("repo")
def test_rm_of_an_untouched_new_copy_needs_no_wait() -> None:
    """Its own checkout moved the mtimes; its content is still the start tree."""
    for form in ((), ("--worktree",)):
        path = _new("spike-untouched", *form)
        assert work.main(["rm", "spike-untouched"]) == 0
        assert not path.exists()


@pytest.mark.usefixtures("repo")
def test_rm_refuses_a_copy_modified_recently_and_after_its_last_save_or_landing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-recent")
    _ = _write(path / "new.txt", "x\n")
    assert work.main(["rm", "spike-recent"]) == 1
    assert "modified" in capsys.readouterr().err
    assert work.main(["save", "spike-recent"]) == 0
    time.sleep(0.01)
    _ = _write(path / "new.txt", "edited after the save\n")
    assert work.main(["rm", "spike-recent", "--discard"]) == 1
    assert "after its last save" in capsys.readouterr().err
    _age(path)
    assert work.main(["rm", "spike-recent", "--discard"]) == 0


def test_rm_evidence_stays_while_a_sibling_of_the_stem_remains(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = _new("fix-i681-pair")
    _ = _new("fix-i681-pair-verify")
    _age(first)
    assert work.main(["rm", "fix-i681-pair", "--evidence"]) == 0
    assert "fix-i681-pair-verify still use it" in capsys.readouterr().err
    assert (repo / ".work" / "evidence" / "fix-i681-pair").is_dir()
    assert work.evidence_tombstones(repo) == []


@pytest.mark.usefixtures("repo")
def test_rm_refuses_a_copy_a_process_works_in(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-busy")
    _age(path)

    def busy(_path: Path) -> list[str]:
        return ["4242"]

    monkeypatch.setattr(work, "process_census", busy)
    assert work.main(["rm", "spike-busy"]) == 1
    assert "process 4242" in capsys.readouterr().err

    def unknown(_path: Path) -> work.CensusGap:
        return work.CensusGap("cannot read the working folder of pid 1234 (foo)")

    monkeypatch.setattr(work, "process_census", unknown)
    assert work.main(["rm", "spike-busy"]) == 1
    assert (
        "the process census is incomplete: cannot read the working folder of pid 1234 (foo), "
        "so it cannot tell"
    ) in capsys.readouterr().err
    assert path.is_dir()


def test_cwd_users_finds_a_real_process_whose_current_directory_is_inside(
    tmp_path: Path,
) -> None:
    inside = tmp_path / "copy" / "nested"
    inside.mkdir(parents=True)
    with subprocess.Popen(["sleep", "30"], cwd=inside) as process:
        try:
            users = work.cwd_users(tmp_path / "copy")
            if users is None:
                pytest.skip("neither /proc nor lsof on this machine")
            assert str(process.pid) in users
            assert str(process.pid) not in (work.cwd_users(tmp_path / "elsewhere") or [])
        finally:
            process.kill()


@pytest.mark.usefixtures("repo")
def test_rm_refuses_a_copy_holding_workspace_or_prover_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-state")
    _age(path)
    pool = workspace.workspace_base(path.resolve())
    pool.mkdir(parents=True)
    assert work.main(["rm", "spike-state"]) == 1
    assert "workspace.py holds" in capsys.readouterr().err
    work.delete_tree(pool)
    proof = prove_failability.tree_state_directory(path.resolve())
    proof.mkdir(parents=True)
    assert work.main(["rm", "spike-state"]) == 1
    assert "prove_failability.py state" in capsys.readouterr().err
    work.delete_tree(proof)
    assert work.main(["rm", "spike-state"]) == 0


@pytest.mark.usefixtures("repo")
def test_rm_under_an_interpreter_without_tomli_names_tomli_and_uv_run_in_one_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A bare ``python3`` lacks ``tomli``, which ``rm`` reads through workspace.py."""
    path = _new("spike-no-tomli")
    _age(path)
    monkeypatch.setattr(sys, "path", [str(Path(work.__file__).parent), *sys.path])
    monkeypatch.delitem(sys.modules, "workspace", raising=False)
    monkeypatch.setitem(sys.modules, "tomli", None)
    monkeypatch.setitem(sys.modules, "scripts", None)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-no-tomli"]) == 1
    error = capsys.readouterr().err
    assert error.splitlines() == [f"work: {sys.executable} lacks the module tomli; {work.RUN_AS}"]
    assert path.is_dir()


@pytest.mark.parametrize(
    ("noted", "shown"),
    [("spike-locked", "locked by someone else"), ("spike-renamed", "unsafe, never touched")],
    ids=["note-names-folder", "note-names-another"],
)
def test_rm_refuses_a_worktree_someone_else_locked(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    noted: str,
    shown: str,
) -> None:
    path = _new("spike-locked", "--worktree")
    _age(path)
    _ = _git_out(repo, "worktree", "unlock", str(path))
    _ = _git_out(repo, "worktree", "lock", "--reason", "harness keeps this", str(path))
    _ = _git_out(path, "config", "--worktree", "dsf-work.name", noted)
    assert work.main(["rm", "spike-locked", "--discard"]) == 1
    assert shown in capsys.readouterr().err
    assert "locked harness keeps this" in _git_out(repo, "worktree", "list", "--porcelain")
    assert path.is_dir()


@pytest.mark.usefixtures("repo")
def test_a_worktree_note_naming_a_live_clone_makes_both_unsafe(
    capsys: pytest.CaptureFixture[str],
) -> None:
    clone = _new("fix-a-clone")
    tree = _new("fix-a-tree", "--worktree")
    for path in (clone, tree):
        _ = _write(path / "unsaved.txt", f"{path.name} edit\n")
        _age(path)
    _ = _git_out(tree, "config", "--worktree", "dsf-work.name", "fix-a-clone")
    copies = work.discover(work.REPO_ROOT)
    assert [copies[name].path for name in ("fix-a-clone", "fix-a-tree")] == [clone, tree]
    assert all(copies[name].hazard for name in ("fix-a-clone", "fix-a-tree"))
    _ = capsys.readouterr()
    assert work.main(["rm", "fix-a-clone", "--discard"]) == 1
    assert work.main(["rm", "fix-a-tree", "--discard"]) == 1
    assert "fix the note or the folder by hand" in capsys.readouterr().err
    assert work.main(["gc"]) == 0
    for path in (clone, tree):
        assert (path / "unsaved.txt").read_text(encoding="utf-8") == f"{path.name} edit\n"
        assert (work.REPO_ROOT / ".work" / "names" / path.name).is_dir()
        assert _pins(work.REPO_ROOT)[path.name].keys() == {"start"}


@pytest.mark.parametrize("command", ["rm", "gc"])
def test_a_gone_worktree_someone_else_locked_keeps_its_metadata(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    path = _new("spike-gone-lock", "--worktree")
    _ = _git_out(repo, "worktree", "unlock", str(path))
    _ = _git_out(repo, "worktree", "lock", "--reason", "harness keeps this", str(path))
    work.delete_tree(path)
    argv = ["rm", "spike-gone-lock", "--discard"] if command == "rm" else ["gc"]
    assert work.main(argv) == 1
    assert "locked by someone else" in capsys.readouterr().err
    assert "locked harness keeps this" in _git_out(repo, "worktree", "list", "--porcelain")


def test_rm_refuses_a_copy_outside_the_work_folder(repo: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    _ = _git_out(repo, "worktree", "add", "-q", "--detach", str(outside))
    _ = _git_out(repo, "config", "extensions.worktreeConfig", "true")
    _ = _git_out(outside, "config", "--worktree", "dsf-work.name", "spike-outside")
    copy = work.locate(repo, "spike-outside")
    reasons = work.removal_refusals(repo, copy, discard=True)
    assert len(reasons) == 1
    assert "not a folder directly under" in reasons[0]
    assert work.main(["rm", "spike-outside"]) == 1
    assert outside.is_dir()


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 file")
def test_rm_refuses_a_copy_whose_note_cannot_be_read(repo: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    _ = _git_out(repo, "worktree", "add", "-q", "--detach", str(outside))
    _ = _git_out(repo, "config", "extensions.worktreeConfig", "true")
    _ = _git_out(outside, "config", "--worktree", "dsf-work.name", "spike-outside")
    _ = _git_out(outside, "config", "--worktree", "dsf-work.adopted", "true")
    _plant(repo, "spike-outside", "start")
    note = repo / ".git" / "worktrees" / "outside" / "config.worktree"
    note.chmod(0o000)
    try:
        assert work.main(["rm", "spike-outside"]) == 1
    finally:
        note.chmod(0o644)
    assert _pins(repo)["spike-outside"].keys() == {"start"}
    assert work.locate(repo, "spike-outside").adopted


@pytest.mark.skipif(os.geteuid() == 0, reason="root looks into a mode-600 folder")
@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_an_unenterable_copy_container_keeps_its_live_copy(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    form: list[str],
) -> None:
    path = _new("spike-shut", *form)
    _ = _write(path / "gone.txt", "unsaved edit\n")
    admin = work.locate(repo, "spike-shut").admin
    path.parent.chmod(0o600)
    try:
        _ = capsys.readouterr()
        assert work.main(["rm", "spike-shut"]) == 1
        assert work.main(["gc"]) == 0
        captured = capsys.readouterr()
        hazard = work.discover(repo)["spike-shut"].hazard
    finally:
        path.parent.chmod(0o755)
    assert hazard is not None
    assert "Permission denied" in hazard
    assert "unsafe, never touched" in captured.err
    assert "spike-shut" not in captured.out
    assert (path / "gone.txt").read_text(encoding="utf-8") == "unsaved edit\n"
    assert admin is None or admin.is_dir()
    assert (repo / ".work" / "names" / "spike-shut").is_dir()
    assert _pins(repo)["spike-shut"].keys() == {"start"}


@pytest.mark.usefixtures("repo")
def test_a_note_name_outside_the_grammar_is_never_a_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    victim = _write(tmp_path / "victim" / "keep.txt", "outside\n")
    path = _new("spike-named", "--worktree")
    _ = _write(path / "unsaved.txt", "unsaved\n")
    _age(path)
    traversal = "../../../victim"
    _ = _git_out(path, "config", "--worktree", "dsf-work.name", traversal)
    _ = capsys.readouterr()
    assert work.main(["list"]) == 0
    assert f"{traversal:<24} worktree unsafe" in capsys.readouterr().out
    assert work.main(["rm", traversal]) == 1
    assert work.main(["rm", traversal, "--discard"]) == 1
    assert work.main(["rm", "spike-named", "--discard"]) == 1
    assert "not a valid copy name" in capsys.readouterr().err
    assert (path / "unsaved.txt").read_text(encoding="utf-8") == "unsaved\n"
    assert victim.read_text(encoding="utf-8") == "outside\n"
    assert [entry.name for entry in tmp_path.iterdir() if "victim" in entry.name] == ["victim"]
    assert path.is_dir()


def test_rm_refuses_a_symlinked_copy(repo: Path, tmp_path: Path) -> None:
    target = tmp_path / "real"
    target.mkdir()
    clones = repo / ".work" / "clones"
    clones.mkdir(parents=True)
    (clones / "spike-link").symlink_to(target)
    assert work.main(["rm", "spike-link"]) == 1
    assert target.is_dir()


# --------------------------------------------------------------------------------------------
# Evidence tombstones: an explicit deletion, recorded before anything moves
# --------------------------------------------------------------------------------------------


def _evidence(repo: Path, stem: str) -> Path:
    return repo / ".work" / "evidence" / stem


def _evidence_entries(repo: Path, stem: str) -> list[Path]:
    trash = repo / ".work" / "trash"
    entries = trash.iterdir() if trash.is_dir() else iter(())
    return sorted(entry for entry in entries if entry.name.startswith(f"evidence-{stem}-"))


def test_rm_evidence_of_a_saved_copy_deletes_it_though_its_saves_stay(repo: Path) -> None:
    """The removed copy's own name, left holding its saves, is no sibling of its stem."""
    path = _new("spike-saved")
    note = work.locate(repo, "spike-saved").note
    _ = _write(path / "new.txt", "kept in a save\n")
    assert work.main(["save", "spike-saved"]) == 0
    _ = _write(_evidence(repo, "spike-saved") / "proof.txt", "proof\n")
    assert work.main(["rm", "spike-saved", "--evidence"]) == 0
    assert set(_pins(repo)["spike-saved"]) == {"save-1"}
    assert not _evidence(repo, "spike-saved").exists()
    (grave,) = work.evidence_tombstones(repo)
    assert (grave.stem, grave.copy, list(grave.states)) == (
        "spike-saved",
        "spike-saved",
        ["proof.txt"],
    )
    assert grave.identity == note["incarnation"]
    assert dict(grave.pins) == {"start": note["start"], **_pins(repo)["spike-saved"]}


def test_rm_evidence_writes_a_tombstone_of_exactly_the_deleted_files_before_trashing(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _new("spike-graves")
    evidence = _evidence(repo, "spike-graves")
    _ = _write(evidence / "top.txt", "top\n")
    _ = _write(evidence / "proofs" / "deep" / "out.txt", "nested output\n")
    _ = _write(evidence / "__pycache__" / "x.cpython-314.pyc", "cache")
    os.utime(evidence / "top.txt", (1_700_000_000.75, 1_700_000_000.75))
    _age(path)
    real_rename = Path.rename

    def refusing(self: Path, target: Path) -> Path:
        if self == evidence:
            raise OSError(errno.EBUSY, "Resource busy", str(self))
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", refusing)
    assert work.main(["rm", "spike-graves", "--evidence"]) == 1
    (grave,) = work.evidence_tombstones(repo)
    out = (evidence / "proofs" / "deep" / "out.txt").lstat()
    assert grave.as_json()["files"] == {
        "proofs/deep/out.txt": [out.st_size, int(out.st_mtime)],
        "top.txt": [4, 1_700_000_000],
    }
    assert (grave.stem, grave.whole, grave.copy) == ("spike-graves", True, "spike-graves")
    assert evidence.is_dir()
    assert _evidence_entries(repo, "spike-graves") == []
    monkeypatch.setattr(Path, "rename", real_rename)
    assert work.main(["evidence-rm", "spike-graves"]) == 0
    (entry,) = _evidence_entries(repo, "spike-graves")
    assert (entry / "proofs" / "deep" / "out.txt").read_text(encoding="utf-8") == "nested output\n"
    assert not evidence.exists()


def test_rm_evidence_moves_the_stem_to_a_kept_trash_entry_gc_removes_after_retention(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-trashed")
    _ = _write(_evidence(repo, "spike-trashed") / "proof.txt", "proof\n")
    _age(path)
    assert work.main(["rm", "spike-trashed", "--evidence"]) == 0
    (entry,) = _evidence_entries(repo, "spike-trashed")
    prefix, stamp, kept = entry.name.rsplit("-", 2)
    assert (prefix, kept) == ("evidence-spike-trashed", work.KEPT_TRASH)
    assert (entry / "proof.txt").read_text(encoding="utf-8") == "proof\n"
    _ = capsys.readouterr()
    assert work.main(["gc"]) == 0
    assert (
        f"keep trash {entry.name}: evidence an explicit deletion moved" in capsys.readouterr().out
    )
    assert entry.is_dir()
    old = entry.with_name(f"{prefix}-{int(stamp) - work.TRASH_RETENTION_SECONDS - 60}-{kept}")
    _ = entry.rename(old)
    assert work.main(["gc"]) == 0
    assert not old.exists()


def test_evidence_tombstone_round_trips_and_is_create_only(repo: Path) -> None:
    grave = work.EvidenceTombstone(
        "lead-merge",
        "a",
        1_731_300_000.5,
        "a",
        (("a/b.txt", 3, 17), ("c", 0, 1)),
        whole=False,
    )
    assert work.EvidenceTombstone.parse(json_loads(json.dumps(grave.as_json()))) == grave
    assert work.write_evidence_tombstone(repo, grave)
    assert not work.write_evidence_tombstone(repo, grave)
    other = dataclasses.replace(grave, removed_by="b", copy="fix-i1-x")
    assert other.file_name == grave.file_name
    assert not work.write_evidence_tombstone(repo, other)
    assert work.evidence_tombstones(repo) == [grave]
    folder = repo / ".work" / work.EVIDENCE_GRAVES
    assert [path.name for path in folder.iterdir()] == [grave.file_name]
    later = dataclasses.replace(grave, removed_at=grave.removed_at + 1)
    assert later.file_name != grave.file_name


@pytest.mark.parametrize("stem", ["lead-merge", "load-balancer.patch", "fix-i681-pair"])
def test_an_evidence_tombstone_accepts_stems_that_are_no_copy_names(stem: str) -> None:
    grave = work.EvidenceTombstone(stem, "a", 1.0, "a", (("x.txt", 1, 2),), whole=True)
    assert work.EvidenceTombstone.parse(grave.as_json()) == grave


@pytest.mark.parametrize(
    ("stem", "rel"),
    [
        ("../x", "x.txt"),
        ("a/b", "x.txt"),
        ("", "x.txt"),
        (".", "x.txt"),
        ("..", "x.txt"),
        ("ok", "../../x"),
        ("ok", "/etc/passwd"),
        ("ok", "a/./b"),
        ("ok", "a//b"),
    ],
)
def test_an_evidence_tombstone_refuses_a_stem_or_path_that_leaves_its_folder(
    stem: str,
    rel: str,
) -> None:
    document = {
        "kind": "evidence",
        "stem": stem,
        "home": "a",
        "removedat": 1.0,
        "removedby": "a",
        "whole": True,
        "copy": "",
        "files": {rel: [1, 2]},
    }
    assert work.EvidenceTombstone.parse(document) is None


@pytest.mark.parametrize(
    "moment",
    [
        math.nan,
        math.inf,
        -math.inf,
        -1.0,
        2.0**32,
        1e300,
    ],
    ids=[
        "nan",
        "positive-infinity",
        "negative-infinity",
        "negative",
        "past-2106",
        "huge",
    ],
)
def test_a_record_whose_removal_moment_is_no_finite_sane_time_is_refused(moment: float) -> None:
    """Retention reads the moment: one that is no real time would keep or reap a record at once."""
    evidence = work.EvidenceTombstone("lead-merge", "a", 1.0, "a", (("f", 1, 1),), whole=True)
    copy = work.Tombstone("fix-i1-x", "a", "abc@1", 1.0, "a")
    assert work.EvidenceTombstone.parse({**evidence.as_json(), "removedat": moment}) is None
    assert work.Tombstone.parse({**copy.as_json(), "removedat": moment}) is None
    assert work.EvidenceTombstone.parse(evidence.as_json()) == evidence
    assert work.Tombstone.parse(copy.as_json()) == copy


def test_the_removed_copy_fields_round_trip_and_leave_the_record_name_alone() -> None:
    """``identity`` and ``pins`` stay out of the name; a record without them exempts nothing."""
    grave = work.EvidenceTombstone(
        "fix-i1-x",
        "a",
        1_731_300_000.5,
        "a",
        (("f.txt", 3, 17),),
        whole=True,
        copy="fix-i1-x",
        identity="0123456789abcdef",
        pins=(("save-1", "c" * 40), ("start", "d" * 40)),
    )
    assert work.EvidenceTombstone.parse(json_loads(json.dumps(grave.as_json()))) == grave
    older = {
        key: value for key, value in grave.as_json().items() if key not in {"identity", "pins"}
    }
    stripped = work.EvidenceTombstone.parse(older)
    assert stripped is not None
    assert stripped == dataclasses.replace(grave, identity="", pins=())
    assert stripped.file_name == grave.file_name
    held = {"save-1": "c" * 40}
    assert grave.removed is not None
    assert grave.removed.left_alone("fix-i1-x", held)
    assert stripped.removed is not None
    assert not stripped.removed.left_alone("fix-i1-x", held)
    assert work.EvidenceTombstone.parse({**grave.as_json(), "pins": {"save-1": 7}}) is None


def test_the_copy_tombstone_reader_never_sees_evidence_tombstones(repo: Path) -> None:
    grave = work.EvidenceTombstone("spike-x", "a", time.time() - 40 * 86400, "a", (), whole=True)
    assert work.write_evidence_tombstone(repo, grave)
    assert not (repo / ".work" / work.TOMBSTONES).exists()
    assert work.tombstones(repo) == []
    assert work.main(["gc"]) == 0
    assert work.evidence_tombstones(repo) == [grave]


def test_gc_reaps_evidence_tombstones_only_past_their_own_retention(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    now = time.time()
    fresh, month, stale = (
        work.EvidenceTombstone("spike-x", "a", at, "a", (("f", 1, 1),), whole=True)
        for at in (
            now,
            now - work.TOMBSTONE_RETENTION_SECONDS - 86400,
            now - work.EVIDENCE_TOMBSTONE_RETENTION_SECONDS - 60,
        )
    )
    for grave in (fresh, month, stale):
        assert work.write_evidence_tombstone(repo, grave)
    _ = capsys.readouterr()
    assert work.main(["gc", "--dry-run"]) == 0
    assert f"would delete evidence tombstone {stale.file_name}" in capsys.readouterr().out
    assert len(work.evidence_tombstones(repo)) == 3
    assert work.main(["gc"]) == 0
    assert f"deleted evidence tombstone {stale.file_name}" in capsys.readouterr().out
    assert sorted(work.evidence_tombstones(repo), key=lambda grave: grave.removed_at) == [
        month,
        fresh,
    ]


def test_a_symlinked_evidence_tombstone_folder_is_refused_by_the_layout_check(
    repo: Path,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    _ = _write(_evidence(repo, "spike-x") / "proof.txt", "proof\n")
    (repo / ".work" / work.EVIDENCE_GRAVES).symlink_to(outside, target_is_directory=True)
    assert work.main(["list"]) == 1
    assert work.main(["evidence-rm", "spike-x"]) == 1
    assert list(outside.iterdir()) == []
    assert (_evidence(repo, "spike-x") / "proof.txt").is_file()


def test_evidence_rm_by_file_records_only_those_files_and_refuses_an_escaping_path(
    repo: Path,
    tmp_path: Path,
) -> None:
    evidence = _evidence(repo, "lead-merge")
    _ = _write(evidence / "keep.txt", "keep\n")
    _ = _write(evidence / "sub" / "drop.txt", "drop\n")
    outside = _write(tmp_path / "outside" / "x.txt", "outside\n")
    (evidence / "link").symlink_to(outside.parent, target_is_directory=True)
    assert (
        work.main(
            [
                "evidence-rm",
                "lead-merge",
                "--file",
                "sub/drop.txt",
            ],
        )
        == 0
    )
    (grave,) = work.evidence_tombstones(repo)
    assert (grave.whole, list(grave.states)) == (False, ["sub/drop.txt"])
    (entry,) = _evidence_entries(repo, "lead-merge")
    assert (entry / "sub" / "drop.txt").read_text(encoding="utf-8") == "drop\n"
    assert (evidence / "keep.txt").is_file()
    assert not (evidence / "sub").exists()
    for rel in (
        "../../x.txt",
        str(outside),
        "link/x.txt",
        "./keep.txt",
        "sub",
    ):
        assert (
            work.main(
                [
                    "evidence-rm",
                    "lead-merge",
                    "--file",
                    rel,
                ],
            )
            == 1
        )
    assert outside.read_text(encoding="utf-8") == "outside\n"
    assert len(work.evidence_tombstones(repo)) == 1


def test_evidence_rm_refuses_a_stem_a_name_still_uses_and_waits_for_the_fleet_lock(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-i9-held")
    _age(path)
    _ = _write(_evidence(repo, "fix-i9-held") / "proof.txt", "proof\n")
    assert work.main(["evidence-rm", "fix-i9-held"]) == 1
    assert "fix-i9-held still use it" in capsys.readouterr().err
    monkeypatch.setattr(work, "EVIDENCE_LOCK_WAIT_SECONDS", 0.3)
    with work.fleet_lock(repo):
        assert work.main(["rm", "fix-i9-held", "--evidence"]) == 1
        assert "a fleet sync holds" in capsys.readouterr().err
    assert path.is_dir()
    assert work.evidence_tombstones(repo) == []
    assert (_evidence(repo, "fix-i9-held") / "proof.txt").is_file()


def test_a_held_stem_lock_refuses_new_and_evidence_deletions_with_nothing_changed(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A fleet sync applying a stem's deletion holds its lock: ``new`` and the deletions wait, then refuse."""
    path = _new("fix-i9-locked")
    _age(path)
    proof = _write(_evidence(repo, "fix-i9-locked") / "proof.txt", "proof\n")
    _ = _write(_evidence(repo, "lead-merge") / "proof.txt", "proof\n")
    monkeypatch.setattr(work, "STEM_LOCK_WAIT_SECONDS", 0.3)
    with work.stem_lock(repo, "fix-i9-locked", 0):
        _ = capsys.readouterr()
        assert work.main(["new", "fix-i9-locked-verify", "--no-setup"]) == 1
        assert "holds" in capsys.readouterr().err
        assert work.main(["rm", "fix-i9-locked", "--evidence"]) == 1
        assert work.main(["new", "fix-i9-other", "--no-setup"]) == 0
        with work.stem_lock(repo, "lead-merge", 0):
            assert work.main(["evidence-rm", "lead-merge"]) == 1
    assert "fix-i9-locked-verify" not in work.discover(repo)
    assert not (repo / ".work" / "names" / "fix-i9-locked-verify").exists()
    assert path.is_dir()
    assert proof.is_file()
    assert work.evidence_tombstones(repo) == []
    with (
        pytest.raises(work.StemBusyError),
        work.stem_lock(repo, "fix-i9-locked", 0),
        work.stem_lock(repo, "fix-i9-locked", 0),
    ):
        pass
    assert work.main(["rm", "fix-i9-locked", "--evidence"]) == 0
    assert not proof.exists()


def test_evidence_rm_adopt_missing_builds_the_record_from_peer_manifests_and_refuses_a_wiped_root(
    repo: Path,
    tmp_path: Path,
) -> None:
    evidence = _evidence(repo, "lead-merge")
    here = _write(evidence / "here.txt", "here\n")
    state = list(work.file_state(here.lstat()))
    manifests = repo / ".work" / work.FLEET
    _ = _write(
        manifests / "evidence-b.json",
        json.dumps({"lead-merge": {"here.txt": state, "gone.txt": [5, 100]}, "other": {}}),
    )
    _ = _write(manifests / "evidence-c.json", json.dumps({"lead-merge": {"gone.txt": [6, 200]}}))
    assert (
        work.main(
            [
                "evidence-rm",
                "lead-merge",
                "--adopt-missing",
                "--dry-run",
            ],
        )
        == 0
    )
    assert work.evidence_tombstones(repo) == []
    assert work.main(["evidence-rm", "lead-merge", "--adopt-missing"]) == 0
    graves = work.evidence_tombstones(repo)
    assert sorted((grave.whole, grave.files) for grave in graves) == [
        (False, (("gone.txt", 5, 100),)),
        (False, (("gone.txt", 6, 200),)),
    ]
    assert here.is_file()
    shutil.rmtree(evidence)
    assert work.main(["evidence-rm", "lead-merge", "--adopt-missing"]) == 0
    whole = [grave for grave in work.evidence_tombstones(repo) if grave.whole]
    assert sorted(grave.states.get("here.txt", (0, 0)) for grave in whole) == [
        (0, 0),
        (state[0], state[1]),
    ]
    count = len(work.evidence_tombstones(repo))
    shutil.rmtree(repo / ".work" / "evidence")
    assert work.main(["evidence-rm", "lead-merge", "--adopt-missing"]) == 1
    (repo / ".work" / "evidence").mkdir()
    (repo / ".work" / "evidence" / "lead-merge").symlink_to(tmp_path, target_is_directory=True)
    assert work.main(["evidence-rm", "lead-merge", "--adopt-missing"]) == 1
    assert len(work.evidence_tombstones(repo)) == count


def test_an_evidence_deletion_on_a_replica_is_refused_and_removes_nothing(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Evidence goes from the copy's home: a replica's record would trash what the home writes."""
    path = _new("spike-mirror")
    _make_replica(path)
    _age(path)
    proof = _write(_evidence(repo, "spike-mirror") / "proof.txt", "proof\n")
    _ = capsys.readouterr()
    for argv in (
        [
            "rm",
            "spike-mirror",
            "--discard",
            "--evidence",
        ],
        ["rm", "spike-mirror", "--evidence"],
        ["evidence-rm", "spike-mirror"],
    ):
        assert work.main(argv) == 1
        error = capsys.readouterr().err
        assert "spike-mirror here is a replica of rio-mac's copy" in error, argv
        assert "evidence is deleted from the copy's home: run it there" in error, argv
    assert path.is_dir()
    assert proof.is_file()
    assert work.evidence_tombstones(repo) == []
    assert _evidence_entries(repo, "spike-mirror") == []
    assert work.main(["rm", "spike-mirror", "--discard"]) == 0
    assert proof.is_file()


def test_an_evidence_deletion_refuses_the_pins_a_discarded_replica_left(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pins left under a replica's name are its home's: this machine cannot vouch for them."""
    path = _new("spike-left")
    _ = _write(path / "new.txt", "the home's save\n")
    assert work.main(["save", "spike-left"]) == 0
    _make_replica(path)
    _age(path)
    proof = _write(_evidence(repo, "spike-left") / "proof.txt", "proof\n")
    assert work.main(["rm", "spike-left", "--discard"]) == 0
    assert set(_pins(repo)["spike-left"]) == {"save-1"}
    _ = capsys.readouterr()
    for argv in (["rm", "spike-left", "--evidence"], ["evidence-rm", "spike-left"]):
        assert work.main(argv) == 1
        error = capsys.readouterr().err
        assert "spike-left here is a replica of another machine's copy" in error, argv
        assert "evidence is deleted from the copy's home: run it there" in error, argv
    assert proof.is_file()
    assert set(_pins(repo)["spike-left"]) == {"save-1"}
    assert work.evidence_tombstones(repo) == []


def test_evidence_restore_moves_the_files_back_with_a_fresh_mtime_no_record_holds(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A restored file holds no recorded state, even one deleted in the second it comes back."""
    now = int(time.time())
    monkeypatch.setattr(time, "time", lambda: now + 0.5)
    evidence = _evidence(repo, "lead-merge")
    proof = _write(evidence / "proofs" / "out.txt", "proof\n")
    top = _write(evidence / "top.txt", "top\n")
    os.utime(proof, (1_700_000_000, 1_700_000_000))
    os.utime(top, (now, now))
    assert work.main(["evidence-rm", "lead-merge"]) == 0
    (grave,) = work.evidence_tombstones(repo)
    (entry,) = _evidence_entries(repo, "lead-merge")
    _ = _write(evidence / "top.txt", "made since\n")
    _ = capsys.readouterr()
    assert work.main(["evidence-restore", "lead-merge"]) == 1
    assert "evidence lead-merge already holds top.txt; nothing restored" in capsys.readouterr().err
    assert sorted(work.evidence_files(entry)) == ["proofs/out.txt", "top.txt"]
    (evidence / "top.txt").unlink()
    assert work.main(["evidence-restore", entry.name, "--dry-run"]) == 0
    assert sorted(work.evidence_files(entry)) == ["proofs/out.txt", "top.txt"]
    assert work.main(["evidence-restore", entry.name]) == 0
    assert not entry.exists()
    restored = work.evidence_files(evidence)
    assert restored == {"proofs/out.txt": (6, now), "top.txt": (4, now + 1)}
    assert not [rel for rel, state in restored.items() if grave.matches(rel, *state)]
    assert (evidence / "proofs" / "out.txt").read_text(encoding="utf-8") == "proof\n"
    assert work.evidence_tombstones(repo) == [grave]
    assert work.main(["evidence-restore", "lead-merge"]) == 1


# --------------------------------------------------------------------------------------------
# gc
# --------------------------------------------------------------------------------------------


def test_gc_removes_only_what_is_finished(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    live = _new("build-live")
    landed = _new("fix-landed")
    _ = _write(landed / "gone.txt", "edited\n")
    assert work.main(["land", "fix-landed"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits the landing")
    gone = _new("spike-gone", "--worktree")
    work.delete_tree(gone)
    _plant(repo, "bench-old", "start")
    _plant(repo, "bench-saved", "save-1")
    trash = repo / ".work" / "trash"
    trash.mkdir(parents=True)
    (trash / "spike-dead-1-999999").mkdir()
    running = trash / f"spike-alive-1-{os.getppid()}"
    running.mkdir()
    _ = capsys.readouterr()
    assert work.main(["gc", "--dry-run"]) == 0
    assert landed.is_dir()
    assert (trash / "spike-dead-1-999999").is_dir()
    assert work.main(["gc"]) == 0
    out = capsys.readouterr().out
    assert "removed fix-landed (landed)" in out
    assert "pruned spike-gone" in out
    assert not landed.exists()
    assert live.is_dir()
    assert running.is_dir()
    assert not (trash / "spike-dead-1-999999").exists()
    assert set(_pins(repo)) == {"build-live", "bench-saved", "spike-gone"}
    assert work.worktree_entries(repo) == []


def test_rm_on_the_home_leaves_a_tombstone_of_this_copy_and_off_the_home_none(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(fleet.MACHINE_ENV, "a")
    first = _new("spike-grave")
    _age(first)
    identity = work.copy_identity(work._config_values(first, "--local"))
    assert len(identity) == 16
    assert work.main(["rm", "spike-grave"]) == 0
    graves = work.tombstones(repo)
    assert [
        (
            t.name,
            t.home,
            t.identity,
            t.removed_by,
        )
        for t in graves
    ] == [
        (
            "spike-grave",
            "a",
            identity,
            "a",
        ),
    ]
    second = _new("spike-grave")
    _age(second)
    assert work.copy_identity(work._config_values(second, "--local")) != identity
    monkeypatch.setenv(fleet.MACHINE_ENV, "z")
    assert work.main(["rm", "spike-grave"]) == 0
    assert work.tombstones(repo) == graves


def test_gc_deletes_kept_trash_and_tombstones_only_past_their_ages(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-kept")
    _age(path)
    _ = work.remove(
        repo,
        work.locate(repo, "spike-kept"),
        discard=False,
        drop_saves=False,
        keep_in_trash=True,
    )
    trash = repo / ".work" / "trash"
    (young,) = trash.iterdir()
    assert young.name.endswith(f"-{work.KEPT_TRASH}")
    assert (young / "gone.txt").is_file()
    old = trash / f"spike-old-{int(time.time() - work.TRASH_RETENTION_SECONDS) - 60}-kept"
    old.mkdir()
    (fresh,) = work.tombstones(repo)
    stale = work.Tombstone(
        "spike-stale",
        "a",
        "abc",
        time.time() - work.TOMBSTONE_RETENTION_SECONDS - 60,
        "a",
    )
    assert work.write_tombstone(repo, stale)
    assert not work.write_tombstone(repo, stale)
    assert not work.write_tombstone(repo, dataclasses.replace(stale, removed_by="b"))
    assert stale in work.tombstones(repo)
    assert not [path for path in (repo / ".work" / "tombstones").iterdir() if path.name[0] == "."]
    _ = capsys.readouterr()
    assert work.main(["gc"]) == 0
    out = capsys.readouterr().out
    assert f"deleted tombstone {stale.file_name}" in out
    assert f"keep trash {young.name}" in out
    assert sorted(trash.iterdir()) == [young]
    assert work.tombstones(repo) == [fresh]


def test_gc_deletes_a_sealed_trash_folder_and_reports_one_it_cannot(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trash = repo / ".work" / "trash"
    sealed = trash / "spike-b-sealed-1-999999" / "inner"
    stuck = trash / "spike-a-stuck-1-999998"
    sealed.mkdir(parents=True)
    stuck.mkdir()
    real = work.delete_tree

    def refusing(path: Path) -> None:
        if path == stuck:
            raise PermissionError(1, "Operation not permitted", str(path))
        real(path)

    monkeypatch.setattr(work, "delete_tree", refusing)
    sealed.chmod(0o000)
    try:
        assert work.main(["gc"]) == 1
    finally:
        if sealed.is_dir():
            sealed.chmod(0o755)
    assert list(trash.iterdir()) == [stuck]
    assert "cannot delete trash spike-a-stuck-1-999998" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["rm", "gc"])
def test_a_copy_the_trash_cannot_delete_is_reported_and_the_rest_still_runs(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    stuck = _new("fix-a-stuck")
    _ = _write(stuck / "gone.txt", "edited\n")
    assert work.main(["land", "fix-a-stuck"]) == 0
    freed = _new("fix-b-freed")
    _ = _write(freed / PACKAGE / "core.py", "CORE = 3\n")
    assert work.main(["land", "fix-b-freed"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits both landings")
    real = work.delete_tree

    def refusing(path: Path) -> None:
        if path.parent.name == "trash" and path.name.startswith("fix-a-stuck-"):
            raise PermissionError(1, "Operation not permitted", str(path))
        real(path)

    monkeypatch.setattr(work, "delete_tree", refusing)
    _ = capsys.readouterr()
    assert work.main([command] if command == "gc" else [command, "fix-a-stuck"]) == 1
    captured = capsys.readouterr()
    assert "fix-a-stuck: removed, but cannot delete" in captured.err
    assert "Operation not permitted; it stays in .work/trash" in captured.err
    assert not stuck.exists()
    assert [entry.name[:12] for entry in (repo / ".work" / "trash").iterdir()] == ["fix-a-stuck-"]
    assert freed.is_dir() == (command == "rm")
    if command == "gc":
        assert "removed fix-b-freed (landed)" in captured.out


def test_delete_tree_unlinks_a_symlink_at_its_top_and_never_touches_the_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "outside"
    _ = _write(target / "kept.txt", "outside\n")
    target.chmod(0o555)
    link = tmp_path / "link"
    link.symlink_to(target)
    try:
        work.delete_tree(link)
        assert not link.is_symlink()
        assert (target / "kept.txt").read_text(encoding="utf-8") == "outside\n"
        assert target.stat().st_mode & 0o777 == 0o555
    finally:
        target.chmod(0o755)


@pytest.mark.parametrize("system", ["posix", "nt"])
def test_delete_tree_never_changes_a_hard_linked_files_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    system: str,
) -> None:
    monkeypatch.setattr(work, "READ_ONLY_FILES_BLOCK_DELETE", system == "nt")
    outside = _write(tmp_path / "outside.txt", "outside\n")
    outside.chmod(0o444)
    tree = tmp_path / "tree"
    tree.mkdir()
    os.link(outside, tree / "linked.txt")
    try:
        work.delete_tree(tree)
        assert not tree.exists()
        assert outside.stat().st_mode & 0o777 == 0o444
    finally:
        outside.chmod(0o644)


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 folder")
@pytest.mark.parametrize(
    (
        "folder",
        "command",
        "status",
        "shown",
    ),
    [
        (
            ".work/clones",
            "list",
            1,
            "work: cannot read",
        ),
        (
            ".work/clones/spike-sealed",
            "list",
            0,
            "broken",
        ),
        (
            ".work/trash",
            "gc",
            1,
            "work: cannot read",
        ),
    ],
    ids=["clones", "copy-root", "trash"],
)
def test_an_unreadable_work_folder_is_reported_never_a_traceback(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    folder: str,
    command: str,
    status: int,
    shown: str,
) -> None:
    _ = _new("spike-sealed")
    sealed = repo / folder
    sealed.mkdir(parents=True, exist_ok=True)
    sealed.chmod(0o000)
    _ = capsys.readouterr()
    try:
        assert work.main([command]) == status
    finally:
        sealed.chmod(0o755)
    captured = capsys.readouterr()
    assert shown in captured.out + captured.err


@pytest.mark.usefixtures("repo")
def test_gc_reports_a_landed_copy_it_must_keep(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    landed = _new("fix-landed")
    _ = _write(landed / "gone.txt", "edited\n")
    assert work.main(["land", "fix-landed"]) == 0
    _ = _git_out(work.REPO_ROOT, "commit", "-q", "-am", "the maintainer commits the landing")

    def busy(_path: Path) -> list[str]:
        return ["4242"]

    monkeypatch.setattr(work, "process_census", busy)
    assert work.main(["gc", "--dry-run"]) == 0
    assert "keep fix-landed" in capsys.readouterr().out
    assert work.main(["gc"]) == 1
    assert landed.is_dir()


def _commit_in(path: Path) -> str:
    """Commit the copy's whole content plus a new file (detached ``HEAD``); return the commit."""
    _ = _write(path / "made.txt", "committed in the copy\n")
    _ = _git_out(path, "add", "-A")
    _ = _git_out(path, "commit", "-q", "-m", "copy commit")
    return _git_out(path, "rev-parse", "HEAD").strip()


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_rm_refuses_a_commit_the_copy_made_until_it_is_saved(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    form: list[str],
) -> None:
    path = _new("spike-own", *form)
    head = _commit_in(path)
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-own"]) == 1
    assert f"its HEAD {head[:12]}" in capsys.readouterr().err
    assert path.is_dir()
    assert work.main(["save", "spike-own"]) == 0
    _age(path)
    assert work.main(["rm", "spike-own"]) == 0
    assert not path.exists()
    assert _git_out(_store(repo), "cat-file", "-t", head).strip() == "commit"


def test_gc_keeps_a_landed_copy_holding_a_later_commit_until_it_is_saved(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-later")
    _ = _write(path / "gone.txt", "edited\n")
    assert work.main(["land", "fix-later"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits the landing")
    head = _commit_in(path)
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["gc"]) == 1
    assert f"its HEAD {head[:12]}" in capsys.readouterr().err
    assert path.is_dir()
    assert work.main(["save", "fix-later"]) == 0
    _age(path)
    assert work.main(["gc"]) == 0
    assert "removed fix-later (landed)" in capsys.readouterr().out
    assert not path.exists()
    assert _pins(repo)["fix-later"]["save-1"] == head


def test_rm_removes_a_copy_at_its_unchanged_start_off_main(repo: Path) -> None:
    tree = _git_out(repo, "rev-parse", "HEAD^{tree}").strip()
    side = _git_out(repo, "commit-tree", "-m", "side", "-p", "HEAD", tree).strip()
    _ = _git_out(repo, "tag", "side", side)
    path = _new("spike-side", "--from", "side")
    _age(path)
    assert work.main(["rm", "spike-side"]) == 0
    assert not path.exists()


def test_rm_does_not_count_another_copys_start_pin_as_keeping_the_head(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-a", "--worktree")
    head = _commit_in(path)
    _ = _new("spike-b", "--worktree", "--from", head)
    assert _pins(repo)["spike-b"]["start"] == head
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-a"]) == 1
    assert "neither main nor a pin reaches" in capsys.readouterr().err
    assert path.is_dir()
    assert work.main(["save", "spike-a"]) == 0
    _age(path)
    assert work.main(["rm", "--drop-saves", "spike-a"]) == 0
    assert not path.exists()
    other = work.locate(repo, "spike-b").path
    assert other is not None
    _age(other)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-b"]) == 1
    assert "neither main nor a pin reaches" in capsys.readouterr().err
    assert work.main(["save", "spike-b"]) == 0
    _age(other)
    assert work.main(["rm", "spike-b"]) == 0


def test_rm_drop_saves_keeps_and_names_a_pin_another_copy_left_under_the_name(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-own")
    _plant(repo, "spike-own", "save-1")
    foreign = _pins(repo)["spike-own"]["save-1"]
    _ = _write(path / "mine.txt", "my work\n")
    assert work.main(["save", "spike-own"]) == 0
    assert set(work.recorded_pins(work._config_values(path, "--local"))) == {"start", "save-2"}
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "--drop-saves", "spike-own"]) == 0
    out = capsys.readouterr().out
    assert f"save-1 {foreign[:12]}" in out
    assert "`work.py rm spike-own --drop-saves` drops them" in out
    assert _pins(repo)["spike-own"] == {"save-1": foreign}
    (grave,) = work.tombstones(repo)
    assert {leaf for leaf, _sha in grave.dropped_pins} == {"start", "save-2"}


def test_a_note_older_than_its_pin_record_owns_only_the_saves_it_made(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-old")
    _plant(repo, "spike-old", "save-1")
    foreign = _pins(repo)["spike-old"]["save-1"]
    _ = _write(path / "mine.txt", "my work\n")
    assert work.main(["save", "spike-old"]) == 0
    _ = _git_out(path, "config", "--local", "--unset", f"{work.NOTE_SECTION}.{work.PINS_NOTE}")
    note = work._config_values(path, "--local")
    own = _pins(repo)["spike-old"]["save-2"]
    assert work.legacy_pins(repo, note) == {"save-2": own}
    _ = _write(path / "more.txt", "more work\n")
    assert work.main(["save", "spike-old"]) == 0
    assert set(work.recorded_pins(work._config_values(path, "--local"))) == {"save-2", "save-3"}
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "--drop-saves", "spike-old"]) == 0
    out = capsys.readouterr().out
    assert f"kept pins this copy cannot prove are its own: save-1 {foreign[:12]}" in out
    assert _pins(repo)["spike-old"] == {"save-1": foreign}


def test_rm_refuses_an_adopted_clone_whose_start_it_committed_until_it_is_saved(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = repo / ".work" / "clones" / "spike-own"
    path.parent.mkdir(parents=True)
    _ = _git_out(repo, "clone", "-q", "-o", "parent", str(repo), str(path))
    head = _commit_in(path)
    assert work.main(["adopt", str(path), "spike-own"]) == 0
    assert _pins(repo)["spike-own"]["start"] == head
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-own"]) == 1
    assert "neither main nor a pin reaches" in capsys.readouterr().err
    assert work.main(["save", "spike-own"]) == 0
    _age(path)
    assert work.main(["rm", "spike-own"]) == 0
    assert not path.exists()


@pytest.mark.usefixtures("repo")
@pytest.mark.parametrize(
    ("form", "ref", "hold"),
    [
        ([], "refs/heads/side", ["branch", "side"]),
        (
            [],
            "refs/tags/side",
            [
                "tag",
                "-a",
                "-m",
                "side",
                "side",
            ],
        ),
        ([], "refs/stash", ["stash", "-q"]),
        ([], "refs/remotes/parent/x", ["update-ref", "refs/remotes/parent/x", "HEAD"]),
        (["--worktree"], "refs/bisect/bad", ["update-ref", "refs/bisect/bad", "HEAD"]),
    ],
    ids=[
        "branch",
        "annotated-tag",
        "stash",
        "remote-tracking",
        "worktree-bisect",
    ],
)
def test_rm_refuses_a_copy_whose_dying_ref_holds_a_commit_nothing_keeps(
    capsys: pytest.CaptureFixture[str],
    form: list[str],
    ref: str,
    hold: list[str],
) -> None:
    path = _new("spike-ref", *form)
    start = _git_out(path, "rev-parse", "HEAD").strip()
    _ = _write(path / "gone.txt", "held\n")
    if ref != "refs/stash":
        _ = _git_out(path, "commit", "-q", "-am", "copy commit")
    _ = _git_out(path, *hold)
    _ = _git_out(path, "checkout", "-q", "--detach", start)
    held = _git_out(path, "rev-parse", f"{ref}^{{commit}}").strip()
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-ref"]) == 1
    assert f"its ref {ref} {held[:12]} holds commits" in capsys.readouterr().err
    assert path.is_dir()
    assert work.main(["rm", "--discard", "spike-ref"]) == 0
    assert not path.exists()


def test_rm_removes_a_worktree_whose_head_a_shared_side_branch_holds(repo: Path) -> None:
    path = _new("spike-shared", "--worktree")
    head = _commit_in(path)
    _ = _git_out(repo, "branch", "side", head)
    _age(path)
    assert work.main(["rm", "spike-shared"]) == 0
    assert not path.exists()
    assert _git_out(repo, "rev-parse", "refs/heads/side").strip() == head


@pytest.mark.parametrize("held_by", ["HEAD", "refs/bisect/bad"])
def test_rm_and_gc_refuse_a_gone_worktree_folder_whose_head_or_ref_nothing_keeps(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    held_by: str,
) -> None:
    path = _new("spike-gone", "--worktree")
    start = _git_out(path, "rev-parse", "HEAD").strip()
    head = _commit_in(path)
    if held_by != "HEAD":
        _ = _git_out(path, "update-ref", held_by, head)
        _ = _git_out(path, "checkout", "-q", "--detach", start)
    admin = work.locate(repo, "spike-gone").admin
    assert admin is not None
    work.delete_tree(path)
    _ = capsys.readouterr()
    assert work.main(["gc", "--dry-run"]) == 0
    assert "keep spike-gone" in capsys.readouterr().out
    assert work.main(["gc"]) == 1
    assert work.main(["rm", "spike-gone"]) == 1
    shown = "its HEAD" if held_by == "HEAD" else f"its ref {held_by}"
    assert f"{shown} {head[:12]}" in capsys.readouterr().err
    assert admin.is_dir()
    assert work.main(["rm", "--discard", "spike-gone"]) == 0
    assert not admin.exists()


@pytest.mark.usefixtures("repo")
@pytest.mark.parametrize("fault", ["incomplete", "listing"])
def test_rm_refuses_a_saved_head_when_its_pin_cannot_be_trusted(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    path = _new("spike-fault")
    head = _commit_in(path)
    assert work.main(["save", "spike-fault"]) == 0
    real_run_git = _git.run_git

    def failing_listing(
        root: Path | str,
        *args: str,
        stdin: str | None = None,
        check: bool = False,
        env: Mapping[str, str] | None = None,
        base: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """``_git.run_git``'s signature, every keyword passed on."""
        if args[:2] == ("for-each-ref", f"--contains={head}"):
            return subprocess.CompletedProcess(args, 1, "", "listing failed")
        return real_run_git(root, *args, stdin=stdin, check=check, env=env, base=base)

    def incomplete(_store: Path, _commit: str) -> bool:
        return False

    if fault == "incomplete":
        monkeypatch.setattr(work, "_complete", incomplete)
    else:
        monkeypatch.setattr("scripts.work._git_runner.run_git", failing_listing)
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-fault"]) == 1
    assert f"its HEAD {head[:12]}" in capsys.readouterr().err
    assert path.is_dir()


# --------------------------------------------------------------------------------------------
# repair
# --------------------------------------------------------------------------------------------


def test_repair_fixes_what_is_safe_and_reports_the_rest(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    clone = _new("build-fixme")
    _ = _new("spike-tree", "--worktree")
    broken = _new("ci-broken")
    (repo / ".work" / ".git").unlink()
    _ = _git_out(clone, "remote", "set-url", "--push", "parent", str(repo))
    _ = _git_out(clone, "config", "--local", "core.autocrlf", "true")
    work.drop_pin(repo, "build-fixme", "start")
    work.delete_tree(broken / ".git")
    _ = _write(clone / ".git" / "index.lock", "")
    _ = _write(repo / ".coverage.host.1.x", "")
    _ = capsys.readouterr()
    assert work.main(["repair"]) == 1
    out = capsys.readouterr().out
    assert (repo / ".work" / ".git").read_text(encoding="utf-8") == work.SENTINEL_TEXT
    assert _git_out(clone, "remote", "get-url", "--push", "parent").strip() == work.NO_PUSH
    assert _git_out(clone, "config", "--local", "core.autocrlf").strip() == "false"
    assert "start" in _pins(repo)["build-fixme"]
    assert "ci-broken" in out
    assert "index.lock" in out
    assert (clone / ".git" / "index.lock").exists()
    assert ".coverage.host.1.x" in out
    (clone / ".git" / "index.lock").unlink()
    (repo / ".coverage.host.1.x").unlink()
    work.delete_tree(broken)
    assert work.main(["repair"]) == 1
    assert "claim ci-broken has no copy" in capsys.readouterr().out
    work.release_name(repo, "ci-broken")
    assert work.main(["repair"]) == 0


def test_ensure_sentinel_refuses_a_directory_in_its_place(repo: Path) -> None:
    (repo / ".work" / ".git").mkdir(parents=True)
    with pytest.raises(work.WorkError, match="must be one"):
        _ = work.ensure_sentinel(repo)


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------


def _fake_venv(copy: Path) -> None:
    """Give the copy a ``.venv`` whose ``python`` is this interpreter, so ``run`` can probe it."""
    bin_dir = copy / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").symlink_to(sys.executable)


@pytest.mark.usefixtures("repo")
def test_run_uses_the_copy_its_venv_and_a_scrubbed_environment(
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    path = _new("bench-run")
    _fake_venv(path)
    monkeypatch.setenv("PYTHONPATH", "/parent/examples/fakeshop")
    monkeypatch.setenv("DIRENV_DIR", "-/parent")
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings")
    monkeypatch.setenv("VIRTUAL_ENV", "/parent/.venv")
    monkeypatch.setenv("PATH", os.pathsep.join(["/parent/.venv/bin", os.environ["PATH"]]))
    monkeypatch.setenv("FAKESHOP_PG_DSN", "postgres://u:p@localhost:5432/fakeshop")
    monkeypatch.setenv("KEPT", "yes")
    probe = "import json, os; print(json.dumps({'cwd': os.getcwd(), 'env': dict(os.environ)}))"
    assert (
        work.main(
            [
                "run",
                "bench-run",
                "--",
                "python",
                "-c",
                probe,
            ],
        )
        == 0
    )
    captured = capfd.readouterr()
    seen = json_loads(captured.out.strip().splitlines()[-1])
    env = {str(key): str(value) for key, value in json_object(seen, "env").items()}
    assert Path(str(json_at(seen, "cwd"))).resolve() == path.resolve()
    assert env["VIRTUAL_ENV"] == str(path.resolve() / ".venv")
    assert env["PATH"].split(os.pathsep)[0] == str(path.resolve() / ".venv" / "bin")
    assert "/parent/.venv/bin" not in env["PATH"].split(os.pathsep)
    assert env["PROJECT_ROOT"] == str(path.resolve())
    assert env["FAKESHOP_PG_DSN"] == "postgres://u:p@localhost:5432/dsfw_bench_run"
    assert env["KEPT"] == "yes"
    for scrubbed in ("PYTHONPATH", "DIRENV_DIR", "DJANGO_SETTINGS_MODULE"):
        assert scrubbed not in env
    root = path.resolve()
    assert f"work: run bench-run in {root} (.venv {root / '.venv'})\n" in captured.err
    assert "work: run" not in captured.out


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_a_copys_own_work_py_runs_on_the_shared_checkout_and_refuses_what_writes_it(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    form: list[str],
) -> None:
    """``uv run python scripts/work.py`` from inside a copy: its root is the copy's, not the registry's."""
    path = _new("bench-inside", *form)
    _fake_venv(path)
    _age(path)
    monkeypatch.setattr(work, "REPO_ROOT", path)
    assert (
        work.main(
            [
                "run",
                "bench-inside",
                "--",
                "python",
                "-c",
                "print('ran here')",
            ],
        )
        == 0
    )
    assert "ran here" in capfd.readouterr().out
    assert work.main(["list"]) == 0
    assert "bench-inside" in capfd.readouterr().out
    assert work.main(["rm", "bench-inside"]) == 1
    assert f"run work.py from the shared checkout {repo}" in capfd.readouterr().err
    assert path.is_dir()
    assert not (path / ".work").exists()


def test_work_py_below_python_3_10_is_one_line_naming_uv_run() -> None:
    """The module needs 3.10 to load: macOS's ``/usr/bin/python3`` (3.9) stops before it.

    ``sys.path[0]`` is the script's folder, as ``python3 scripts/work.py`` sets it.
    """
    script = Path(work.__file__).resolve()
    old = (
        f"import runpy, sys; sys.path[0] = {str(script.parent)!r}; sys.hexversion = 0x030906F0; "
        "sys.argv = ['work.py', 'check-name', 'spike-x']; "
        f"runpy.run_path({str(script)!r}, run_name='__main__')"
    )
    completed = subprocess.run(
        [sys.executable, "-c", old],
        cwd=script.parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stderr.splitlines() == [
        f"work: {sys.executable} is Python {sys.version.split()[0]}; {work.RUN_AS}",
    ]


@pytest.mark.parametrize(
    ("argv", "pytest_run"),
    [
        (["pytest", "-x"], True),
        (["/x/.venv/bin/pytest"], True),
        (["C:\\x\\Scripts\\pytest.exe", "-q"], True),
        (["py.test"], True),
        (
            [
                "python",
                "-m",
                "pytest",
                "tests",
            ],
            True,
        ),
        (["python3", "-mpytest"], True),
        (
            [
                "uv",
                "run",
                "pytest",
                "-k",
                "x",
            ],
            True,
        ),
        (
            [
                "uv",
                "run",
                "--group",
                "pg",
                "pytest",
            ],
            True,
        ),
        (
            [
                "uv",
                "run",
                "--frozen",
                "--group",
                "pg",
                "pytest",
            ],
            True,
        ),
        (
            [
                "uv",
                "run",
                "--with",
                "pytest-cov",
                "pytest",
            ],
            True,
        ),
        (
            [
                "uv",
                "run",
                "--python",
                "3.13",
                "pytest",
            ],
            True,
        ),
        (
            [
                "uv",
                "tool",
                "run",
                "pytest",
            ],
            True,
        ),
        (["uvx", "pytest"], True),
        (
            [
                "python",
                "-m",
                "pip",
                "pytest",
            ],
            True,
        ),
        (["python", "-c", "print('pytest')"], False),
        (
            [
                "uv",
                "run",
                "--with",
                "pytest-cov",
                "python",
                "-c",
                "x",
            ],
            False,
        ),
        (
            [
                "python",
                "scripts/prove_failability.py",
                "--only",
                "x",
            ],
            False,
        ),
        (["grep", "pytest_plugins"], False),
        ([], False),
    ],
)
def test_is_pytest_reads_every_word_for_pytest(argv: list[str], *, pytest_run: bool) -> None:
    """Any word that is pytest, however a wrapper hands it on; a false positive only waits."""
    assert work.is_pytest(argv) is pytest_run


def _pytest_venv(copy: Path) -> None:
    """Give the copy a ``.venv`` whose ``pytest`` only says it ran."""
    _fake_venv(copy)
    script = _write(copy / ".venv" / "bin" / "pytest", "#!/bin/sh\necho pytest-ran\n")
    script.chmod(0o755)


_PYTEST_LOCK_HOLDER = (
    "import os, sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import _locks\n"
    "descriptor = os.open(sys.argv[2], os.O_RDWR | os.O_CREAT)\n"
    "assert _locks.try_lock(descriptor)\n"
    "os.write(descriptor, (sys.argv[3] + '\\n').encode())\n"
    "print('held', flush=True)\n"
    "sys.stdin.read()\n"
)


@contextlib.contextmanager
def _pytest_lock_holder(repo: Path, holder: str) -> Generator[subprocess.Popen[bytes], None, None]:
    """Hold ``repo``'s pytest lock from another process, as another pytest run would.

    Closing the holder's stdin (or leaving the block) ends it, which lets the lock go.
    """
    _ = work.ensure_sentinel(repo)
    lock = repo / ".work" / work.PYTEST_LOCK
    with subprocess.Popen(
        [
            sys.executable,
            "-c",
            _PYTEST_LOCK_HOLDER,
            str(Path(_locks.__file__).parent),
            str(lock),
            holder,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as process:
        assert process.stdout is not None
        assert os.read(process.stdout.fileno(), 64).strip() == b"held"
        assert _locks.pytest_lock_path(repo) == lock.resolve()
        probe = os.open(lock, os.O_RDWR)
        try:
            assert not _locks.try_lock(probe)
        finally:
            os.close(probe)
        try:
            yield process
        finally:
            process.kill()


def _let_go(process: subprocess.Popen[bytes]) -> None:
    """End the holder process and wait for it, so its lock is gone."""
    assert process.stdin is not None
    process.stdin.close()
    _ = process.wait()  # no timeout: a timed wait polls with ``time.sleep``, which tests patch


def test_run_waits_for_another_pytest_in_this_checkout(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """One line names the holder; the run starts once the holder lets go, and records itself."""
    path = _new("bench-pytest", "--owner", "agent-7")
    _pytest_venv(path)
    waits: list[float] = []
    with _pytest_lock_holder(repo, "fix-other agent-3 rio-mac pid 42") as other:

        def release(seconds: float) -> None:
            waits.append(seconds)
            _let_go(other)

        with monkeypatch.context() as patch:
            patch.setattr(time, "sleep", release)
            code = work.main(
                [
                    "run",
                    "bench-pytest",
                    "--",
                    "pytest",
                    "-q",
                ],
            )
    assert code == 0
    captured = capfd.readouterr()
    assert waits == [_locks.POLL_SECONDS]
    assert captured.err.count("work: waiting for another pytest") == 1
    assert (
        "work: waiting for another pytest in this checkout (fix-other agent-3 rio-mac pid 42)"
        in captured.err
    )
    assert "pytest-ran" in captured.out
    holder = (work.work_dir(repo) / work.PYTEST_LOCK).read_text(encoding="utf-8")
    assert holder == f"bench-pytest agent-7 {work.machine_id()} pid {os.getpid()}\n"


def test_run_never_serialises_a_command_that_is_not_pytest(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _new("bench-free")
    _fake_venv(path)

    def no_wait(_seconds: float) -> None:
        pytest.fail("a command that is not pytest waited on the pytest lock")

    with _pytest_lock_holder(repo, "fix-other"), monkeypatch.context() as patch:
        patch.setattr(time, "sleep", no_wait)
        code = work.main(
            [
                "run",
                "bench-free",
                "--",
                "python",
                "-c",
                "pass",
            ],
        )
    assert code == 0


def test_a_checkout_under_an_unrelated_work_folder_takes_its_own_pytest_lock(
    tmp_path: Path,
) -> None:
    """A scratch repository in a copy's evidence (or a test's temp under ``.work``) is no copy."""
    shared = tmp_path / "shared"
    scratch = shared / ".work" / "evidence" / "fix-x" / "repo"
    scratch.mkdir(parents=True)
    assert _locks.pytest_lock_path(scratch) == scratch.resolve() / ".work" / work.PYTEST_LOCK


def test_a_clone_and_a_worktree_work_py_makes_take_the_shared_pytest_lock(repo: Path) -> None:
    expected = repo.resolve() / ".work" / work.PYTEST_LOCK
    assert _locks.pytest_lock_path(_new("fix-lockclone")) == expected
    assert _locks.pytest_lock_path(_new("fix-lockwt", "--worktree")) == expected


@pytest.mark.usefixtures("repo")
def test_run_returns_the_commands_exit_code_and_its_signal() -> None:
    path = _new("bench-code")
    _fake_venv(path)
    assert (
        work.main(
            [
                "run",
                "bench-code",
                "--",
                "python",
                "-c",
                "raise SystemExit(3)",
            ],
        )
        == 3
    )
    kill = "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"
    assert (
        work.main(
            [
                "run",
                "bench-code",
                "--",
                "python",
                "-c",
                kill,
            ],
        )
        == 128 + signal.SIGTERM
    )


@pytest.mark.usefixtures("repo")
def test_run_refuses_a_copy_whose_package_does_not_import_from_inside_it(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("bench-refuse")
    assert (
        work.main(
            [
                "run",
                "bench-refuse",
                "--",
                "true",
            ],
        )
        == work.REFUSED
    )
    assert "no .venv" in capsys.readouterr().err
    _fake_venv(path)
    work.delete_tree(path / PACKAGE)
    assert (
        work.main(
            [
                "run",
                "bench-refuse",
                "--",
                "true",
            ],
        )
        == work.REFUSED
    )
    assert "cannot import" in capsys.readouterr().err

    def elsewhere(_root: Path, _env: object) -> Path:
        return Path("/parent") / PACKAGE / "__init__.py"

    monkeypatch.setattr(work, "package_location", elsewhere)
    assert (
        work.main(
            [
                "run",
                "bench-refuse",
                "--",
                "true",
            ],
        )
        == work.REFUSED
    )
    assert "outside the copy" in capsys.readouterr().err


# --------------------------------------------------------------------------------------------
# The shared checkout
# --------------------------------------------------------------------------------------------


def test_this_checkout_ignores_the_work_folder_and_tracks_nothing_under_it() -> None:
    root = work.REPO_ROOT
    lines = (root / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "/.work/" in lines or ".work/" in lines
    tracked = _git.run_git(root, "ls-files", "-z", "--", work.WORK_DIR)
    assert tracked.returncode == 0
    assert tracked.stdout == ""
    gitlinks = _git.run_git(root, "ls-files", "-s", "-z")
    assert gitlinks.stdout
    assert not [entry for entry in gitlinks.stdout.split("\0") if entry.startswith("160000 ")]


def test_setup_refuses_without_uv_on_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    with pytest.raises(work.WorkError, match="uv is not on PATH"):
        work._setup(tmp_path, "clone")


# --------------------------------------------------------------------------------------------
# Content that cannot be verified, flags that hide edits, landings main undid
# --------------------------------------------------------------------------------------------


def test_rm_refuses_a_copy_whose_git_is_gone_unless_discarded(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-headless")
    _ = _write(path / "precious.txt", "only unsaved copy\n")
    work.delete_tree(path / ".git")
    _age(path)
    assert work.main(["rm", "spike-headless"]) == 1
    assert "cannot be read" in capsys.readouterr().err
    assert (path / "precious.txt").is_file()
    assert work.main(["rm", "spike-headless", "--discard"]) == 0
    assert not path.exists()
    assert "kept pins this copy cannot prove are its own" in capsys.readouterr().out
    assert set(_pins(repo)["spike-headless"]) == {"start"}
    assert work.main(["rm", "spike-headless", "--drop-saves"]) == 0
    assert "spike-headless" not in _pins(repo)


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_an_assume_unchanged_edit_is_saved_and_blocks_rm(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    form: list[str],
) -> None:
    path = _new("spike-hidden", *form)
    _ = _git_out(path, "update-index", "--assume-unchanged", "gone.txt")
    _ = _write(path / "gone.txt", "only precious content\n")
    assert work.main(["save", "spike-hidden"]) == 0
    saved = _pins(repo)["spike-hidden"]["save-1"]
    assert _git_out(_store(repo), "show", f"{saved}:gone.txt") == "only precious content\n"
    _ = _write(path / "gone.txt", "edited again, unsaved\n")
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-hidden"]) == 1
    assert "neither HEAD, a save" in capsys.readouterr().err
    assert path.is_dir()


def test_a_skip_worktree_copy_is_refused_by_save_and_by_rm(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-sparse")
    _ = _git_out(path, "update-index", "--skip-worktree", "gone.txt")
    _ = _write(path / "gone.txt", "hidden edit\n")
    assert work.main(["save", "spike-sparse"]) == 1
    assert "skip-worktree" in capsys.readouterr().err
    _age(path)
    assert work.main(["rm", "spike-sparse"]) == 1
    assert "cannot be read" in capsys.readouterr().err
    assert path.is_dir()
    _ = repo


def test_gc_reports_keeping_a_landed_copy_whose_landed_path_main_later_changed(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-moved")
    _ = _write(path / "gone.txt", "landed\n")
    assert work.main(["land", "fix-moved"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits the landing")
    _ = _write(repo / "gone.txt", "changed later\n")
    _ = _git_out(repo, "commit", "-q", "-am", "a later commit")
    _age(path)
    _ = capsys.readouterr()
    for mode in (["--dry-run"], []):
        assert work.main(["gc", *mode]) == 0
        assert "keep fix-moved: the shared HEAD does not hold its landing" in (
            capsys.readouterr().out
        )
    assert path.is_dir()


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_rm_removes_a_pristine_copy_whose_start_main_amended_away(
    repo: Path,
    form: list[str],
) -> None:
    path = _new("spike-amended", *form)
    _ = _git_out(repo, "commit", "-q", "--amend", "-m", "initial, amended")
    _age(path)
    assert work.main(["rm", "spike-amended"]) == 0
    assert not path.exists()


def test_gc_keeps_a_landed_copy_until_main_holds_the_landing(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-undone")
    _ = _write(path / "gone.txt", "precious\n")
    assert work.main(["land", "fix-undone"]) == 0
    _ = _write(repo / "gone.txt", "to delete\n")
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["gc"]) == 0
    assert "removed" not in capsys.readouterr().out
    assert path.is_dir()
    landed = _pins(repo)["fix-undone"]["landed"]
    assert _git_out(_store(repo), "show", f"{landed}:gone.txt") == "precious\n"
    assert work.main(["rm", "fix-undone"]) == 0
    assert "landed" in _pins(repo)["fix-undone"]


# --------------------------------------------------------------------------------------------
# Symlinks never lead a command outside .work
# --------------------------------------------------------------------------------------------


def test_a_symlinked_work_folder_is_refused_before_anything_is_written(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    outside = tmp_path / "outside"
    _ = _write(outside / ".git", "gitdir: preserve-me\n")
    (repo / ".work").symlink_to(outside, target_is_directory=True)
    assert work.main(["new", "fix-probe", "--no-setup"]) == 1
    assert "symlink" in capsys.readouterr().err
    assert work.main(["repair"]) == 1
    assert (outside / ".git").read_text(encoding="utf-8") == "gitdir: preserve-me\n"
    assert sorted(path.name for path in outside.iterdir()) == [".git"]


def test_a_symlinked_container_is_refused(repo: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / ".work").mkdir()
    (repo / ".work" / "clones").symlink_to(outside, target_is_directory=True)
    assert work.main(["new", "fix-probe", "--no-setup"]) == 1
    assert work.main(["list"]) == 1
    assert list(outside.iterdir()) == []


def test_a_symlinked_clone_is_listed_unsafe_and_never_touched(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    other = tmp_path / "other"
    _ = _git_out(tmp_path, "init", "-q", "-b", "main", str(other))
    _ = _git_out(other, "commit", "-q", "--allow-empty", "-m", "outside")
    _ = _git_out(other, "remote", "add", "parent", "https://example.invalid/repo")
    clones = repo / ".work" / "clones"
    clones.mkdir(parents=True)
    (clones / "fix-link").symlink_to(other, target_is_directory=True)
    assert work.main(["repair"]) == 1
    assert "unsafe" in capsys.readouterr().out
    assert (
        _git_out(other, "remote", "get-url", "--push", "parent").strip()
        == "https://example.invalid/repo"
    )
    assert _git.run_git(other, "config", "core.autocrlf").stdout == ""
    assert work.main(["list", "--json"]) == 0
    rows = json_list(json_loads(capsys.readouterr().out))
    assert [json_at(row, "state") for row in rows] == ["unsafe"]
    for command in (["save", "fix-link"], ["land", "fix-link"], ["rm", "fix-link", "--discard"]):
        assert work.main(command) == 1
    assert other.is_dir()


# --------------------------------------------------------------------------------------------
# Pins: create-only, outside the shared repository, restorable
# --------------------------------------------------------------------------------------------


def test_racing_saves_get_two_numbers_and_neither_replaces_the_other(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _new("spike-race")
    _ = _write(path / "gone.txt", "first\n")
    publish = work.publish_pin
    raced: list[str | None] = []

    def racing(
        root: Path,
        source: Path,
        commit: str,
        name: str,
        leaf: str,
        *,
        replacing: str = "",
    ) -> bool:
        if not raced:
            raced.append(None)
            _ = _write(path / "gone.txt", "second\n")
            raced[0] = work.save(repo, work.locate(repo, "spike-race"))
        return publish(root, source, commit, name, leaf, replacing=replacing)

    monkeypatch.setattr(work, "publish_pin", racing)
    first = work.save(repo, work.locate(repo, "spike-race"))
    assert raced == ["refs/work/spike-race/save-1"]
    assert first == "refs/work/spike-race/save-2"
    leaves = _pins(repo)["spike-race"]
    assert _git_out(_store(repo), "show", f"{leaves['save-1']}:gone.txt") == "second\n"
    assert _git_out(_store(repo), "show", f"{leaves['save-2']}:gone.txt") == "first\n"


def test_a_pin_is_created_only_where_none_exists(repo: Path) -> None:
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    _ = _write(repo / "later.txt", "later\n")
    _ = _git_out(repo, "add", "later.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "later")
    later = _git_out(repo, "rev-parse", "HEAD").strip()
    assert work.publish_pin(repo, repo, head, "spike-x", "save-1")
    assert not work.publish_pin(repo, repo, later, "spike-x", "save-1")
    assert _pins(repo)["spike-x"]["save-1"] == head
    assert work.publish_pin(repo, repo, later, "spike-x", "landed")
    assert not work.publish_pin(repo, repo, head, "spike-x", "landed", replacing=head)
    assert work.publish_pin(repo, repo, head, "spike-x", "landed", replacing=later)


def test_a_mirror_push_of_the_shared_repository_carries_no_pin(repo: Path, tmp_path: Path) -> None:
    path = _new("spike-secret")
    _ = _write(path / "gone.txt", "uncommitted secret\n")
    assert work.main(["save", "spike-secret"]) == 0
    remote = tmp_path / "remote.git"
    _ = _git_out(tmp_path, "init", "--bare", "-q", str(remote))
    _ = _git_out(repo, "push", "-q", "--mirror", str(remote))
    assert _git_out(remote, "for-each-ref", "--format=%(refname)") == "refs/heads/main\n"
    assert _git_out(repo, "for-each-ref", "--format=%(refname)", "refs/work/") == ""
    assert set(_pins(repo)["spike-secret"]) == {"start", "save-1"}


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_a_restored_save_holds_the_work_uncommitted_and_lands(repo: Path, form: list[str]) -> None:
    path = _new("spike-keep")
    _ = _write(path / "gone.txt", "saved work\n")
    _ = _write(path / "new.txt", "new file\n")
    assert work.main(["save", "spike-keep"]) == 0
    assert work.main(["rm", "spike-keep"]) == 0
    restored = _new("spike-back", "--from", "refs/work/spike-keep/save-1", *form)
    assert _git_out(restored, "rev-parse", "HEAD") == _git_out(repo, "rev-parse", "HEAD")
    assert (restored / "gone.txt").read_text(encoding="utf-8") == "saved work\n"
    assert _git_out(restored, "diff", "--cached", "--name-only") == ""
    assert work.main(["land", "spike-back"]) == 0
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "saved work\n"
    assert (repo / "new.txt").read_text(encoding="utf-8") == "new file\n"


@pytest.mark.parametrize("form", [[], ["--worktree"]], ids=["clone", "worktree"])
def test_a_restored_save_registers_its_new_source_paths(repo: Path, form: list[str]) -> None:
    path = _new("fix-new-file")
    _ = _write(path / "tests" / "test_added.py", "VALUE = 1\n")
    assert work.main(["save", "fix-new-file"]) == 0
    restored = _new("verify-new-file", "--from", "refs/work/fix-new-file/save-1", *form)
    assert (restored / "tests" / "test_added.py").read_text() == "VALUE = 1\n"
    assert (
        "tests/test_added.py"
        in _git_out(
            restored,
            "ls-files",
            "--",
            "tests/test_added.py",
        ).splitlines()
    )
    assert _git_out(restored, "diff", "--cached", "--name-only") == ""
    assert _git_out(restored, "rev-parse", "HEAD") == _git_out(repo, "rev-parse", "HEAD")


@pytest.mark.parametrize("leaf", ["landed", "landed-copy"])
def test_a_restored_landing_holds_the_work_uncommitted_on_main(repo: Path, leaf: str) -> None:
    """A landing pin is content on a main commit, restored as a save is."""
    path = _new("fix-landed")
    _ = _write(path / "gone.txt", "landed work\n")
    assert work.main(["land", "fix-landed"]) == 0
    restored = _new("verify-landed", "--from", f"refs/work/fix-landed/{leaf}")
    assert _git_out(restored, "rev-parse", "HEAD") == _git_out(repo, "rev-parse", "HEAD")
    assert (restored / "gone.txt").read_text(encoding="utf-8") == "landed work\n"
    assert _git_out(restored, "status", "--porcelain").strip() == "M gone.txt"
    assert work.main(["land", "verify-landed", "--dry-run"]) == 0


def test_new_refuses_a_pin_whose_parent_is_not_on_main(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A save on a commit the copy made could never land from a new copy either."""
    path = _new("spike-off-main")
    _ = _write(path / "gone.txt", "committed in the copy\n")
    _ = _git_out(path, "commit", "-q", "-am", "a copy commit")
    _ = _write(path / "new.txt", "saved on it\n")
    assert work.main(["save", "spike-off-main"]) == 0
    _ = capsys.readouterr()
    argv = [
        "new",
        "spike-from-off",
        "--no-setup",
        "--from",
        "refs/work/spike-off-main/save-1",
    ]
    assert work.main(argv) == 1
    assert "which is not on the shared main" in capsys.readouterr().err
    assert not (repo / ".work" / "clones" / "spike-from-off").exists()
    assert not (repo / ".work" / "names" / "spike-from-off").exists()


@pytest.mark.parametrize("store", [False, True], ids=["no-store", "store-without-that-pin"])
def test_new_refuses_a_pin_that_does_not_exist(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    store: bool,
) -> None:
    if store:
        _plant(repo, "spike-other", "save-1")
    assert (
        work.main(
            [
                "new",
                "spike-none",
                "--no-setup",
                "--from",
                "refs/work/x/save-1",
            ],
        )
        == 1
    )
    assert "names no pin" in capsys.readouterr().err
    assert not (repo / ".work" / "clones" / "spike-none").exists()
    assert not (repo / ".work" / "names" / "spike-none").exists()


# --------------------------------------------------------------------------------------------
# Process census
# --------------------------------------------------------------------------------------------


def _fake_lsof(tmp_path: Path, body: str) -> str:
    script = _write(tmp_path / "bin" / "lsof", f"#!/bin/sh\n{body}\n")
    script.chmod(0o755)
    return str(script)


def test_an_lsof_census_that_fails_misses_its_own_process_or_cannot_cover_cannot_tell(
    tmp_path: Path,
) -> None:
    target = tmp_path / "copy"
    target.mkdir()

    def census(body: str, *, shut: bool = True) -> list[str] | work.CensusGap:
        return work._lsof_users(_fake_lsof(tmp_path, body), target, others_shut_out=shut)

    assert census("exit 1") == work.CensusGap("lsof exited 1")
    assert census(f"printf 'p{os.getpid()}\\nn/\\n'; exit 1") == work.CensusGap("lsof exited 1")
    assert census("printf 'p1\\nn/\\n'") == work.CensusGap("lsof does not list this process")
    whole = f"printf 'p{os.getpid()}\\nn/\\np77\\nn{target}\\n'"
    assert census(whole) == ["77"]
    assert isinstance(census(whole, shut=False), work.CensusGap)


def _fake_process(
    proc: Path,
    pid: int,
    cwd: Path,
    comm: str = "bash",
    cmdline: bytes = b"",
) -> None:
    """Add ``/proc/<pid>`` with its ``cwd`` link and the ``comm`` and ``cmdline`` the kernel shows."""
    entry = proc / str(pid)
    entry.mkdir(parents=True)
    (entry / "cwd").symlink_to(cwd)
    _ = (entry / "comm").write_text(f"{comm}\n", encoding="utf-8")
    _ = (entry / "cmdline").write_bytes(cmdline or f"{comm}\0".encode())


def _fake_proc(tmp_path: Path, target: Path, *, with_self: bool) -> Path:
    proc = tmp_path / "proc"
    _fake_process(proc, 77, target)
    if with_self:
        _fake_process(proc, os.getpid(), tmp_path, "python3")
    return proc


def test_a_proc_census_without_its_own_process_cannot_tell(tmp_path: Path) -> None:
    target = tmp_path / "copy"
    target.mkdir()
    without = _fake_proc(tmp_path, target, with_self=False)
    assert work._proc_users(without, target, others_shut_out=True) == work.CensusGap(
        "/proc does not list this process",
    )
    work.delete_tree(without)
    whole = _fake_proc(tmp_path, target, with_self=True)
    assert work._proc_users(whole, target, others_shut_out=True) == ["77"]


def _hide_cwd(monkeypatch: pytest.MonkeyPatch, entry: Path, owner: int) -> None:
    """Make ``entry``'s cwd unreadable, as the kernel does, and its folder owned by ``owner``."""
    readlink, stat_of = Path.readlink, Path.stat

    def denied(path: Path) -> Path:
        if path == entry / "cwd":
            raise PermissionError(path)
        return readlink(path)

    def owned(path: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        info = stat_of(path, follow_symlinks=follow_symlinks)
        if path == entry:
            fields = list(info)
            fields[4] = owner
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(Path, "readlink", denied)
    monkeypatch.setattr(Path, "stat", owned)


#: One own process per entry of ``work.CENSUS_SKIPPED_DAEMONS``, as Linux logins show them.
LOGIN_DAEMONS = {
    "systemd": b"/usr/lib/systemd/systemd\0--user\0",
    "(sd-pam)": b"(sd-pam)\0",
    "sshd-session": b"sshd-session: rio@notty" + b"\0" * 17,
    "sshd": b"sshd: rio@pts/0\0",
    "ssh-agent": b"/usr/bin/ssh-agent\0-D\0-a\0/run/user/1000/gcr/.ssh\0",
    "gpg-agent": b"/usr/bin/gpg-agent\0--supervised\0",
    "gnome-keyring-d": b"/usr/bin/gnome-keyring-daemon\0--foreground\0--components=secrets\0",
}


def test_every_skipped_daemon_has_a_census_row() -> None:
    assert set(LOGIN_DAEMONS) == set(work.CENSUS_SKIPPED_DAEMONS)


@pytest.mark.parametrize("comm", sorted(LOGIN_DAEMONS))
def test_a_proc_census_skips_an_own_login_daemon_it_cannot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    comm: str,
) -> None:
    target = tmp_path / "copy"
    target.mkdir()
    proc = _fake_proc(tmp_path, target, with_self=True)
    _fake_process(proc, 78, target, comm, LOGIN_DAEMONS[comm])
    _hide_cwd(monkeypatch, proc / "78", os.getuid())
    assert work._proc_users(proc, target, others_shut_out=True) == ["77"]


@pytest.mark.parametrize(
    ("comm", "cmdline", "shown"),
    [
        ("bash", b"-bash\0", "-bash"),
        ("claude", b"node\0/usr/bin/claude\0", "node /usr/bin/claude"),
        ("systemd", b"/usr/lib/systemd/systemd\0", "/usr/lib/systemd/systemd"),
        ("sshd", b"/usr/sbin/sshd\0-D\0-f\0sshd_config\0", "/usr/sbin/sshd -D -f sshd_config"),
        ("ssh-agent", b"python3\0agent.py\0", "python3 agent.py"),
        ("bash", b"\0", "bash"),
    ],
    ids=[
        "shell",
        "agent-cli",
        "systemd-not-user",
        "sshd-server",
        "comm-argv-mismatch",
        "empty-cmdline",
    ],
)
def test_a_proc_census_with_an_unknown_own_unreadable_process_names_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    comm: str,
    cmdline: bytes,
    shown: str,
) -> None:
    target = tmp_path / "copy"
    target.mkdir()
    proc = _fake_proc(tmp_path, target, with_self=True)
    _fake_process(proc, 78, tmp_path, comm, cmdline)
    _hide_cwd(monkeypatch, proc / "78", os.getuid())
    for shut in (True, False):
        found = work._proc_users(proc, target, others_shut_out=shut)
        assert isinstance(found, work.CensusGap)
        assert found.reason.startswith(f"cannot read the working folder of pid 78 ({shown}), ")


@pytest.mark.parametrize(
    ("shut", "expected"),
    [
        (
            False,
            work.CensusGap(
                "cannot read the working folder of pid 78 (bash), another user's, while no "
                "folder above the copy shuts others out",
            ),
        ),
        (True, ["77"]),
    ],
    ids=["other-user-while-others-may-enter", "other-user-shut-out"],
)
def test_a_proc_census_with_another_users_unreadable_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    shut: bool,
    expected: list[str] | work.CensusGap,
) -> None:
    target = tmp_path / "copy"
    target.mkdir()
    proc = _fake_proc(tmp_path, target, with_self=True)
    _fake_process(proc, 78, target)
    _hide_cwd(monkeypatch, proc / "78", os.getuid() + 1)
    assert work._proc_users(proc, target, others_shut_out=shut) == expected


def test_others_are_shut_out_only_by_a_folder_of_ours_closed_to_everyone(tmp_path: Path) -> None:
    closed = tmp_path / "closed"
    (closed / "copy").mkdir(parents=True)
    closed.chmod(0o700)
    assert work.others_shut_out(closed / "copy")
    assert not work.others_shut_out(Path("/usr/bin"))
    assert not work.others_shut_out(Path("/"))


def test_rm_refuses_when_the_real_census_fails(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if Path("/proc/self/cwd").exists():
        pytest.skip("this machine censuses /proc, not lsof")
    path = _new("spike-census")
    _age(path)
    monkeypatch.setattr(work, "process_census", _real_process_census)
    _ = _fake_lsof(tmp_path, "exit 1")
    monkeypatch.setenv("PATH", os.pathsep.join([str(tmp_path / "bin"), os.environ["PATH"]]))
    assert work.main(["rm", "spike-census"]) == 1
    assert "census is incomplete" in capsys.readouterr().err
    assert path.is_dir()
    _ = repo


_real_process_census = work.process_census


# --------------------------------------------------------------------------------------------
# land: merged with main, all or nothing, one at a time
# --------------------------------------------------------------------------------------------


MULTILINE = "".join(f"line {number}\n" for number in range(30))


def test_land_merges_onto_a_main_that_changed_the_same_file_elsewhere(repo: Path) -> None:
    _ = _write(repo / "multi.txt", MULTILINE)
    _ = _git_out(repo, "add", "multi.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "multiline")
    path = _new("fix-merge")
    _ = _write(path / "multi.txt", MULTILINE.replace("line 0\n", "COPY\n"))
    _ = _write(path / "gone.txt", "COPY B\n")
    _ = _write(repo / "multi.txt", MULTILINE.replace("line 29\n", "MAIN\n"))
    _ = _git_out(repo, "commit", "-q", "-am", "another session")
    assert work.main(["land", "fix-merge"]) == 0
    landed = (repo / "multi.txt").read_text(encoding="utf-8")
    assert landed == MULTILINE.replace("line 0\n", "COPY\n").replace("line 29\n", "MAIN\n")
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "COPY B\n"


def test_a_patch_that_does_not_apply_writes_no_path_at_all(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-conflict")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "gone.txt", "copy\n")
    _ = _write(repo / PACKAGE / "core.py", "CORE = 9\n")
    _ = _git_out(repo, "commit", "-q", "-am", "moved the same line")
    assert work.main(["land", "fix-conflict"]) == 1
    assert "does not apply" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
    assert "landed" not in work.locate(repo, "fix-conflict").note


@pytest.mark.parametrize("moment", ["detach", "commit", "edit"])
def test_land_rolls_back_when_the_shared_checkout_moves_while_it_writes(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    moment: str,
) -> None:
    path = _new("fix-moving")
    _ = _write(path / "gone.txt", "from copy\n")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    put = work.put_path
    calls: list[str] = []

    def moving(
        root: Path,
        rel: str,
        state: work.State,
        preimage: work.State,
    ) -> bool:
        if not calls:
            if moment == "detach":
                _ = _git_out(repo, "checkout", "-q", "--detach")
            elif moment == "commit":
                _ = _git_out(repo, "commit", "-q", "--allow-empty", "-m", "meanwhile")
        calls.append(rel)
        done = put(root, rel, state, preimage)
        if moment == "edit" and rel == f"{PACKAGE}/core.py":
            _ = _write(repo / PACKAGE / "core.py", "CORE = theirs\n")
        return done

    monkeypatch.setattr(work, "put_path", moving)
    assert work.main(["land", "fix-moving"]) == 1
    assert "rolled back" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
    expected_core = "CORE = theirs\n" if moment == "edit" else "CORE = 2\n"
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == expected_core
    assert "landed" not in work.locate(repo, "fix-moving").note
    assert not (repo / ".work" / "land-journal.json").exists()


def test_land_writes_nothing_when_a_path_changes_after_planning(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-late")
    _ = _write(path / "gone.txt", "from copy\n")
    plan = work.plan_landing

    def late(
        root: Path,
        copy: work.Copy,
        index: Path,
        *,
        from_start: bool,
    ) -> work.LandPlan:
        result = plan(root, copy, index, from_start=from_start)
        _ = _write(repo / "gone.txt", "another session\n")
        return result

    monkeypatch.setattr(work, "plan_landing", late)
    assert work.main(["land", "fix-late"]) == 1
    assert "nothing written" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "another session\n"


def test_one_land_at_a_time(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _new("fix-locked")
    _ = _write(path / "gone.txt", "from copy\n")
    with work.land_lock(repo):
        assert work.main(["land", "fix-locked"]) == 1
        assert "another land holds" in capsys.readouterr().err
        assert work.main(["repair"]) == 1
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
    assert work.main(["land", "fix-locked"]) == 0
    assert (repo / ".work" / "land.lock").is_file()


HOLD_LOCK = (
    "import fcntl, os, sys\n"
    "descriptor = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT)\n"
    "fcntl.flock(descriptor, fcntl.LOCK_EX)\n"
    "print('held', flush=True)\n"
    "sys.stdin.read()\n"
)


def test_a_dead_holders_lock_frees_itself(repo: Path) -> None:
    path = _new("fix-dead-lock")
    _ = _write(path / "gone.txt", "from copy\n")
    with subprocess.Popen(
        [
            sys.executable,
            "-c",
            HOLD_LOCK,
            str(repo / ".work" / "land.lock"),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as holder:
        assert holder.stdout is not None
        assert os.read(holder.stdout.fileno(), 64).strip() == b"held"
        assert work.main(["land", "fix-dead-lock"]) == 1
        holder.kill()
    assert work.main(["land", "fix-dead-lock"]) == 0


# --------------------------------------------------------------------------------------------
# new: worktree config, its own checkout, setup failures, one namespace
# --------------------------------------------------------------------------------------------


def test_new_worktree_moves_a_repository_level_core_worktree_first(repo: Path) -> None:
    _ = (
        _git_out(repo, "config", "--unset", "extensions.worktreeConfig")
        if _git.run_git(
            repo,
            "config",
            "extensions.worktreeConfig",
        ).stdout
        else ""
    )
    _ = _git_out(repo, "config", "core.worktree", str(repo))
    path = _new("spike-moved", "--worktree")
    assert work.locate(repo, "spike-moved").healthy
    assert Path(_git_out(path, "rev-parse", "--show-toplevel").strip()).resolve() == path.resolve()
    assert Path(_git_out(repo, "rev-parse", "--show-toplevel").strip()).resolve() == repo.resolve()
    assert _git.run_git(repo, "config", "--local", "core.worktree").returncode != 0
    assert _git_out(repo, "config", "--worktree", "core.worktree").strip() == str(repo)


def test_new_fails_and_leaves_nothing_when_git_does_not_read_the_copy_as_its_own(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def never(_path: Path) -> bool:
        return False

    monkeypatch.setattr(work, "_is_own_checkout", never)
    assert (
        work.main(
            [
                "new",
                "spike-lost",
                "--no-setup",
                "--worktree",
            ],
        )
        == 1
    )
    assert "own checkout" in capsys.readouterr().err
    assert work.worktree_entries(repo) == []
    assert not (repo / ".work" / "names" / "spike-lost").exists()


def _fake_tool(tmp_path: Path, name: str, body: str) -> None:
    script = _write(tmp_path / "bin" / name, f"#!/bin/sh\n{body}\n")
    script.chmod(0o755)


@pytest.mark.parametrize(
    ("uv", "pre_commit", "message"),
    [
        ("echo lock out of date >&2; exit 2", "exit 0", "lock out of date"),
        ("exit 0", "echo hook-install-failed >&2; exit 37", "hook-install-failed"),
    ],
    ids=["uv", "pre-commit"],
)
def test_a_failed_setup_step_fails_the_new_and_says_why(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uv: str,
    pre_commit: str,
    message: str,
) -> None:
    _fake_tool(tmp_path, "uv", uv)
    _fake_tool(tmp_path, "pre-commit", pre_commit)
    monkeypatch.setenv("PATH", os.pathsep.join([str(tmp_path / "bin"), os.environ["PATH"]]))
    assert work.main(["new", "build-setup"]) == 1
    assert message in capsys.readouterr().err
    assert not (repo / ".work" / "clones" / "build-setup").exists()


def test_a_clone_and_a_worktree_racing_for_one_name_cannot_both_win(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discover = work.discover
    inner: list[int] = []

    def racing(root: Path) -> dict[str, work.Copy]:
        if not inner:
            inner.append(-1)
            inner[0] = work.main(
                [
                    "new",
                    "fix-same",
                    "--no-setup",
                    "--worktree",
                ],
            )
        return discover(root)

    monkeypatch.setattr(work, "discover", racing)
    assert work.main(["new", "fix-same", "--no-setup"]) == 0
    assert inner == [1]
    assert (repo / ".work" / "clones" / "fix-same").is_dir()
    assert not (repo / ".work" / "worktrees" / "fix-same").exists()


# --------------------------------------------------------------------------------------------
# adopt: a clone whose parent is a fleet checkout over SSH
# --------------------------------------------------------------------------------------------


FLEET = json.dumps(
    {
        "machines": [
            {
                "name": name,
                "ssh": name,
                "os": os_name,
                "repo": "~/projects/django-strawberry-framework",
                "weight": {"light": 1, "heavy": 1},
                "floors": {},
                "aliases": aliases,
            }
            for name, os_name, aliases in (
                ("rio-mac", "macos", []),
                ("rio-desktop", "linux", ["old-desktop"]),
            )
        ],
    },
)
#: The login the fake ``ssh -G`` answers for the desktop: another account than this one's.
DESK = f"desk-{ME}"


def _fake_ssh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str | None = None) -> None:
    """Put an ``ssh`` on ``PATH`` whose ``-G`` answers ``DESK`` for the desktop, else ``ME``."""
    _fake_tool(
        tmp_path,
        "ssh",
        body
        or (
            'test "$1" = -G || exit 255\n'
            'echo "hostname $2"\n'
            f'case "$2" in *[Dd]esktop*) echo "user {DESK}" ;; *) echo "user {ME}" ;; esac\n'
            'echo "port 22"'
        ),
    )
    monkeypatch.setenv("PATH", os.pathsep.join([str(tmp_path / "bin"), os.environ["PATH"]]))


@pytest.mark.parametrize(
    ("url", "parent"),
    [
        (f"rio-mac:/Users/{ME}/projects/django-strawberry-framework", True),
        ("rio-mac:~/projects/django-strawberry-framework", True),
        (f"{ME}@rio-mac:/home/{ME}/projects/django-strawberry-framework", True),
        (f"ssh://{DESK}@rio-desktop:22/home/{DESK}/projects/django-strawberry-framework", True),
        (f"rio-desktop:/home/{DESK}/projects/django-strawberry-framework", True),
        (f"Rio-Desktop.tail.ts.net:/home/{DESK}/projects/django-strawberry-framework", True),
        (f"old-desktop:/home/{DESK}/projects/django-strawberry-framework", True),
        ("ssh://rio-desktop/~/projects/django-strawberry-framework", True),
        ("rio-mac:~/projects/django-strawberry-framework/", True),
        (f"rio-desktop:/home/{ME}/projects/django-strawberry-framework", False),
        (f"{ME}@rio-desktop:~/projects/django-strawberry-framework", False),
        ("otheruser@rio-mac:~/projects/django-strawberry-framework", False),
        (f"rio-mac:/Users/not-{ME}/projects/django-strawberry-framework", False),
        (f"ssh://{DESK}@rio-desktop:2222/home/{DESK}/projects/django-strawberry-framework", False),
        (f"rio-mac:/Users/{ME}/projects/../projects/django-strawberry-framework", False),
        (f"rio-mac:/Users/{ME}/projects/Django-strawberry-framework", False),
        ("rio-elsewhere:/Users/someone/projects/django-strawberry-framework", False),
        (f"rio-mac:/Users/{ME}/projects/other", False),
        ("rio-mac:/srv/a/b/projects/django-strawberry-framework", False),
        ("https://github.com/x/django-strawberry-framework", False),
    ],
)
def test_a_fleet_checkout_over_ssh_is_this_checkouts_parent(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
    *,
    parent: bool,
) -> None:
    """The host reaches a row by any of its names; the account is the one ``ssh -G`` names."""
    _ = _write(repo / "docs" / "fleet" / "machines.json", FLEET)
    _fake_ssh(tmp_path, monkeypatch)
    assert work.is_parent_url(repo, url) is parent


def test_a_local_parent_needs_no_machine_list(repo: Path) -> None:
    assert not (repo / "docs" / "fleet" / "machines.json").exists()
    assert work.is_parent_url(repo, str(repo))
    assert work.is_parent_url(repo, f"file://{repo}")


@pytest.mark.parametrize(
    ("machines", "ssh", "message"),
    [
        ('{"machines": []}', None, "'machines' must be a non-empty list"),
        (None, None, "machines.json"),
        (FLEET, "exit 255", "cannot tell which account ssh logs in to rio-desktop as"),
        (FLEET, 'echo "hostname $2"', "cannot tell which account ssh logs in to rio-desktop as"),
    ],
    ids=[
        "broken-list",
        "no-list",
        "ssh-fails",
        "no-user-line",
    ],
)
def test_adopt_refuses_an_ssh_parent_it_cannot_check_and_says_why(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    machines: str | None,
    ssh: str | None,
    message: str,
) -> None:
    """A broken list is fleet's refusal, never every SSH parent silently refused."""
    if machines is not None:
        _ = _write(repo / "docs" / "fleet" / "machines.json", machines)
    _fake_ssh(tmp_path, monkeypatch, ssh)
    path = repo / ".work" / "clones" / "fix-remote"
    path.parent.mkdir(parents=True)
    _ = _git_out(repo, "clone", "-q", "--no-hardlinks", "-o", "parent", str(repo), str(path))
    url = f"rio-desktop:/home/{DESK}/projects/django-strawberry-framework"
    _ = _git_out(path, "remote", "set-url", "parent", url)
    assert work.main(["adopt", str(path), "fix-remote"]) == 1
    assert message in capsys.readouterr().err
    assert not work.locate(repo, "fix-remote").adopted


def test_adopt_registers_a_clone_whose_parent_is_a_fleet_checkout_over_ssh(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = _write(repo / "docs" / "fleet" / "machines.json", FLEET)
    _fake_ssh(tmp_path, monkeypatch)
    path = repo / ".work" / "clones" / "fix-remote"
    path.parent.mkdir(parents=True)
    _ = _git_out(repo, "clone", "-q", "--no-hardlinks", "-o", "parent", str(repo), str(path))
    _ = _git_out(
        path,
        "remote",
        "set-url",
        "parent",
        f"rio-desktop:/home/{DESK}/projects/django-strawberry-framework",
    )
    _ = _git_out(path, "remote", "set-url", "--push", "parent", work.NO_PUSH)
    assert work.main(["adopt", str(path), "fix-remote"]) == 0
    assert work.locate(repo, "fix-remote").adopted
    assert "start" in _pins(repo)["fix-remote"]


# --------------------------------------------------------------------------------------------
# Landing against hidden edits, racing editors, crashes and odd shapes
# --------------------------------------------------------------------------------------------


def test_land_refuses_a_shared_edit_an_assume_unchanged_bit_hides(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-hidden-main")
    _ = _write(path / "gone.txt", "COPY\n")
    _ = _git_out(repo, "update-index", "--assume-unchanged", "gone.txt")
    _ = _write(repo / "gone.txt", "MAIN UNSAVED ONLY COPY\n")
    assert _git_out(repo, "status", "--porcelain") == ""
    assert work.main(["land", "fix-hidden-main"]) == 1
    assert "other changes in gone.txt" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "MAIN UNSAVED ONLY COPY\n"


def test_an_edit_racing_the_write_is_kept_and_the_landing_rolled_back(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-race-edit")
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    _ = _write(path / "gone.txt", "from copy\n")
    blob_bytes = work._blob_bytes

    def racing(root: Path, rel: str, state: tuple[str, str]) -> bytes:
        if rel == "gone.txt":
            _ = _write(repo / "gone.txt", "OTHER SESSION ONLY COPY\n")
        return blob_bytes(root, rel, state)

    monkeypatch.setattr(work, "_blob_bytes", racing)
    assert work.main(["land", "fix-race-edit"]) == 1
    err = capsys.readouterr().err
    assert "gone.txt changed under the landing" in err
    assert "kept untouched in gone.txt" in err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "OTHER SESSION ONLY COPY\n"
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert not (repo / ".work" / "land-journal.json").exists()


def test_a_failed_write_rolls_every_path_back(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("fix-full-disk")
    (path / "gone.txt").unlink()
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    put = work.put_path
    failed: list[str] = []

    def full(
        root: Path,
        rel: str,
        state: work.State,
        preimage: work.State,
    ) -> bool:
        if state is not None and not failed:
            failed.append(rel)
            raise OSError(28, "No space left on device")
        return put(root, rel, state, preimage)

    monkeypatch.setattr(work, "put_path", full)
    assert work.main(["land", "fix-full-disk"]) == 1
    assert "No space left" in capsys.readouterr().err
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
    assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert not (repo / ".work" / "land-journal.json").exists()


CRASH_LAND = """
import os, sys
from pathlib import Path
from scripts import work
work.REPO_ROOT = Path(sys.argv[1])
put = work.put_path
def crash(root, rel, state, preimage):
    done = put(root, rel, state, preimage)
    os._exit(91)
work.put_path = crash
work.main(["land", "fix-crash"])
"""


@pytest.mark.parametrize("recoverer", ["repair", "land"])
def test_a_land_killed_mid_write_is_undone_by_the_next_repair_or_land(
    repo: Path,
    recoverer: str,
) -> None:
    path = _new("fix-crash")
    (path / "gone.txt").unlink()
    _ = _write(path / PACKAGE / "core.py", "CORE = 3\n")
    crashed = subprocess.run(
        [
            sys.executable,
            "-c",
            CRASH_LAND,
            str(repo),
        ],
        cwd=Path(work.__file__).resolve().parents[1],
        env=_git.repository_env(),
        check=False,
    )
    assert crashed.returncode == 91
    assert not (repo / "gone.txt").exists()
    assert (repo / ".work" / "land-journal.json").is_file()
    if recoverer == "repair":
        assert work.main(["repair"]) == 0
        assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
        assert not (repo / ".work" / "land-journal.json").exists()
    else:
        _ = _write(path / "gone.txt", "to delete\n")
        assert work.main(["land", "fix-crash"]) == 0
        assert not (repo / ".work" / "land-journal.json").exists()
        assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
        assert (repo / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 3\n"


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 folder")
@pytest.mark.parametrize(
    "mode",
    [0o000, 0o644, 0o555],
    ids=["unreadable", "listable-not-enterable", "unwritable"],
)
def test_a_journaled_path_that_cannot_be_undone_keeps_the_journal_until_it_can(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    mode: int,
) -> None:
    path = _new("fix-after-lock")
    _ = _write(path / "gone.txt", "from copy\n")
    landed = _write(repo / "locked" / "b.txt", "landed bytes\n")
    after = work.working_state(repo, "locked/b.txt")
    assert after is not None
    work._store_journal(repo, "HEAD", {"locked/b.txt": {"before": None, "after": list(after)}})
    journal = repo / ".work" / "land-journal.json"
    landed.parent.chmod(mode)
    try:
        assert work.main(["land", "fix-after-lock"]) == 1
    finally:
        landed.parent.chmod(0o755)
    err = capsys.readouterr().err
    assert "locked/b.txt" in err
    assert "journal is kept" in err
    assert "another writer" not in err
    assert journal.is_file()
    assert landed.read_text(encoding="utf-8") == "landed bytes\n"
    assert work.main(["land", "fix-after-lock"]) == 0
    assert not journal.exists()
    assert not (repo / "locked").exists()
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "from copy\n"


@pytest.mark.parametrize(
    "hostile",
    [
        "../escaped.txt",
        "/outside/escaped.txt",
        "a/../../escaped.txt",
        "./a.txt",
        "a//b.txt",
    ],
)
def test_a_journal_naming_a_path_outside_the_checkout_is_refused_untouched(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    hostile: str,
) -> None:
    after = work.working_state(repo, "gone.txt")
    assert after is not None
    entries: dict[str, object] = {
        "gone.txt": {"before": None, "after": list(after)},
        hostile: {"before": None, "after": list(after)},
    }
    _ = work.ensure_sentinel(repo)
    work._store_journal(repo, "HEAD", entries)
    journal = repo / ".work" / "land-journal.json"
    assert work.main(["repair"]) == 1
    err = capsys.readouterr().err
    assert f"the land journal names a path outside the checkout: {hostile}" in err
    assert journal.is_file()
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
    assert not (repo.parent / "escaped.txt").exists()


def test_land_turns_a_folder_into_a_file_and_back(repo: Path) -> None:
    _ = _write(repo / "dir" / "x", "old\n")
    _ = _git_out(repo, "add", "dir")
    _ = _git_out(repo, "commit", "-q", "-m", "a folder")
    path = _new("fix-shape")
    work.delete_tree(path / "dir")
    _ = _write(path / "dir", "now a file\n")
    assert work.main(["land", "fix-shape"]) == 0
    assert (repo / "dir").read_text(encoding="utf-8") == "now a file\n"


def test_a_case_only_rename_lands_with_its_new_spelling(repo: Path) -> None:
    _ = _write(repo / "Case.txt", "old\n")
    _ = _git_out(repo, "add", "Case.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "case")
    path = _new("fix-case")
    (path / "Case.txt").rename(path / "case-tmp")
    (path / "case-tmp").rename(path / "case.txt")
    _ = _write(path / "case.txt", "new\n")
    assert work.main(["land", "fix-case"]) == 0
    spellings = [entry.name for entry in repo.iterdir() if entry.name.lower() == "case.txt"]
    assert spellings == ["case.txt"]
    assert (repo / "case.txt").read_text(encoding="utf-8") == "new\n"


def test_gc_keeps_a_copy_whose_mode_only_landing_main_undid(repo: Path) -> None:
    path = _new("fix-mode")
    (path / "gone.txt").chmod(0o755)
    assert work.main(["land", "fix-mode"]) == 0
    (repo / "gone.txt").chmod(0o644)
    assert not work.landing_on_main(repo, _pins(repo)["fix-mode"]["landed"])
    _age(path)
    assert work.main(["gc"]) == 0
    assert path.is_dir()


def test_gc_frees_a_copy_that_landed_onto_a_moved_main_once_main_commits_it(repo: Path) -> None:
    _ = _write(repo / "multi.txt", MULTILINE)
    _ = _git_out(repo, "add", "multi.txt")
    _ = _git_out(repo, "commit", "-q", "-m", "multiline")
    path = _new("fix-stale-gc")
    _ = _write(path / "multi.txt", MULTILINE.replace("line 0\n", "COPY\n"))
    _ = _write(repo / "multi.txt", MULTILINE.replace("line 29\n", "MAIN\n"))
    _ = _git_out(repo, "commit", "-q", "-am", "another session")
    assert work.main(["land", "fix-stale-gc"]) == 0
    _ = _git_out(repo, "commit", "-q", "-am", "the maintainer commits the landing")
    assert work.landing_on_main(repo, _pins(repo)["fix-stale-gc"]["landed"])
    _age(path)
    assert work.main(["gc"]) == 0
    assert not path.exists()


def test_rm_refuses_when_a_pinned_snapshot_lost_an_object(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-corrupt")
    _ = _write(path / "gone.txt", "precious\n")
    assert work.main(["save", "spike-corrupt"]) == 0
    store = _store(repo)
    blob = _git_out(
        store,
        "rev-parse",
        f"{_pins(repo)['spike-corrupt']['save-1']}:gone.txt",
    ).strip()
    loose = store / "objects" / blob[:2] / blob[2:]
    assert loose.is_file()
    loose.unlink()
    _age(path)
    _ = capsys.readouterr()
    assert work.main(["rm", "spike-corrupt"]) == 1
    assert "neither HEAD, a save" in capsys.readouterr().err
    assert path.is_dir()


@pytest.mark.parametrize("shape", ["nested", "submodule"])
def test_a_copy_holding_a_nested_repository_is_refused_by_save_land_and_rm(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    shape: str,
) -> None:
    path = _new("spike-nested")
    nested = path / "nested"
    _ = _git_out(path, "init", "-q", str(nested))
    _ = _write(nested / "data", "ONLY PRECIOUS UNSAVED DATA\n")
    if shape == "submodule":
        _ = _git_out(nested, "add", "data")
        _ = _git_out(nested, "commit", "-q", "-m", "inner")
        _ = _git_out(path, "add", "nested")
        _ = _write(nested / "data", "edited after the inner commit\n")
    for command in (["save", "spike-nested"], ["land", "spike-nested"]):
        assert work.main(command) == 1
        assert "nested repository" in capsys.readouterr().err
    _age(path)
    assert work.main(["rm", "spike-nested"]) == 1
    assert nested.is_dir()
    _ = repo


# --------------------------------------------------------------------------------------------
# Guards each pinned on its own
# --------------------------------------------------------------------------------------------


def test_a_sparse_checkout_setting_alone_is_refused(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-sparse-set")
    _ = _git_out(path, "config", "core.sparseCheckout", "true")
    _ = _write(path / "gone.txt", "edit\n")
    assert work.main(["save", "spike-sparse-set"]) == 1
    assert "is a sparse checkout" in capsys.readouterr().err
    _ = repo


@pytest.mark.parametrize(("entry", "make_folder"), [("clones", False), ("land.lock", True)])
def test_a_work_entry_of_the_wrong_kind_is_refused(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    entry: str,
    *,
    make_folder: bool,
) -> None:
    target = repo / ".work" / entry
    if make_folder:
        target.mkdir(parents=True)
    else:
        _ = _write(target, "not a folder\n")
    assert work.main(["list"]) == 1
    assert "is not a" in capsys.readouterr().err


def test_a_symlink_alias_inside_the_same_container_is_unsafe(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real = _new("fix-real")
    (real.parent / "fix-alias").symlink_to("fix-real", target_is_directory=True)
    _ = capsys.readouterr()
    assert work.main(["list", "--json"]) == 0
    rows = {
        str(json_at(row, "name")): str(json_at(row, "state"))
        for row in json_list(json_loads(capsys.readouterr().out))
    }
    assert rows["fix-alias"] == "unsafe"
    assert work.main(["rm", "fix-alias", "--discard"]) == 1
    assert real.is_dir()
    _ = repo


def test_claims_a_dead_command_left_are_released_and_unknown_ones_reported(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _ = work.ensure_sentinel(repo)
    claims = repo / ".work" / "names"
    ownerless = claims / "fix-ownerless"
    ownerless.mkdir(parents=True)
    past = time.time() - 2 * work.CLAIM_GRACE_SECONDS
    os.utime(ownerless, (past, past))
    foreign = claims / "fix-foreign"
    _ = _write(foreign / "owner", "another-machine 999999\n")
    _ = capsys.readouterr()
    assert work.main(["repair"]) == 1
    out = capsys.readouterr().out
    assert "released dead claim fix-ownerless" in out
    assert "claim fix-foreign has no copy" in out
    assert foreign.is_dir()
    assert work.main(["new", "fix-ownerless", "--no-setup"]) == 0
    fresh = claims / "fix-fresh"
    fresh.mkdir()
    assert not work._claim_is_stale(fresh)


def test_repair_reclaims_a_live_copy_that_lost_its_claim(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _ = _new("fix-unclaimed")
    work.release_name(repo, "fix-unclaimed")
    _ = capsys.readouterr()
    assert work.main(["repair"]) == 0
    assert "re-claimed fix-unclaimed" in capsys.readouterr().out
    assert (repo / ".work" / "names" / "fix-unclaimed" / "owner").is_file()


def test_a_claim_is_published_whole_or_not_at_all(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rename = Path.rename

    def interrupted(self: Path, target: str | os.PathLike[str]) -> Path:
        assert (self / "owner").is_file()
        return rename(self, target)

    monkeypatch.setattr(Path, "rename", interrupted)
    claim = work.claim_name(repo, "fix-whole")
    assert (claim / "owner").is_file()
    assert [entry.name for entry in (repo / ".work" / "names").iterdir()] == ["fix-whole"]


def test_a_damaged_pin_store_is_refused_until_repair_reinitializes_it(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-headless-store")
    _ = _write(path / "gone.txt", "precious\n")
    assert work.main(["save", "spike-headless-store"]) == 0
    (_store(repo) / "HEAD").unlink()
    assert work.main(["list"]) == 1
    assert "damaged" in capsys.readouterr().err
    assert work.main(["repair"]) == 0
    assert "re-initialized" in capsys.readouterr().out
    assert set(_pins(repo)["spike-headless-store"]) == {"start", "save-1"}


def test_an_empty_folder_at_a_names_place_still_holds_the_name(repo: Path) -> None:
    _ = work.ensure_sentinel(repo)
    (repo / ".work" / "names" / "fix-legacy").mkdir(parents=True)
    with pytest.raises(work.WorkError, match="is claimed"):
        _ = work.claim_name(repo, "fix-legacy")
    assert list((repo / ".work" / "names" / "fix-legacy").iterdir()) == []


# --------------------------------------------------------------------------------------------
# Homes and replicas (docs/fleet/scripts/fleet_sync.py keeps the replicas)
# --------------------------------------------------------------------------------------------


ALIASED_FLEET = json.dumps(
    {
        "machines": [
            {
                "name": name,
                "ssh": name,
                "os": os_name,
                "repo": "~/projects/django-strawberry-framework",
                "weight": {"light": 1, "heavy": 1},
                "floors": {},
                "aliases": aliases,
            }
            for name, os_name, aliases in (
                ("rio-ubu", "linux", []),
                ("rio-air", "macos", ["Riordens-MacBook-Air"]),
            )
        ],
    },
)


def _on_rio_air(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """List ``rio-air`` (alias ``Riordens-MacBook-Air``) in ``repo`` and make this host it."""
    _ = _write(repo / "docs" / "fleet" / "machines.json", ALIASED_FLEET)
    monkeypatch.delenv(fleet.MACHINE_ENV, raising=False)
    monkeypatch.setattr(fleet, "this_hostname", lambda: "rio-air")


def test_a_machine_is_named_by_its_row_else_its_short_hostname(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The override first, then the hostname; a former name records its row's, never itself."""
    _on_rio_air(repo, monkeypatch)
    assert work.machine_id() == "rio-air"
    monkeypatch.setattr(fleet, "this_hostname", lambda: "Riordens-MacBook-Air.local")
    assert work.machine_id() == "rio-air"
    monkeypatch.setenv(fleet.MACHINE_ENV, "Rio-Ubu")
    assert work.machine_id() == "rio-ubu"
    monkeypatch.setenv(fleet.MACHINE_ENV, "Stranger.lan")
    assert work.machine_id() == "stranger"


def test_a_note_naming_a_former_hostname_reads_as_that_machine(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Old records are never rewritten: ``home``, ``host`` and ``formerhomes`` read through the list."""
    _on_rio_air(repo, monkeypatch)
    assert work.home_of({"home": "riordens-macbook-air"}) == "rio-air"
    assert work.home_of({"host": "Riordens-MacBook-Air.local"}) == "rio-air"
    assert work.home_of({"host": "Rio-Ubu.lan"}) == "rio-ubu"
    assert work.home_of({"host": "rio-ubu", "home": "Rio-Mac"}) == "rio-mac"
    assert work.former_homes({"formerhomes": "riordens-macbook-air,rio-ubu"}) == (
        "rio-air",
        "rio-ubu",
    )
    assert work.later_home(
        {"home": "rio-ubu", "generation": "1", "formerhomes": "riordens-macbook-air"},
        {"home": "rio-air"},
    )


def test_a_copy_whose_note_names_a_former_hostname_is_this_machines_home_copy(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Its ``rm`` buries it under the row's name; ``list`` names the row."""
    _on_rio_air(repo, monkeypatch)
    old = _new("spike-old-home")
    work.write_note(old, "clone", {"home": "riordens-macbook-air"})
    hostless = _new("spike-old-host")
    _ = work._git(hostless, "config", "--local", "--unset", f"{work.NOTE_SECTION}.home")
    work.write_note(hostless, "clone", {"host": "Riordens-MacBook-Air.local"})
    for path in (old, hostless):
        assert work.home_of(work._config_values(path, "--local")) == "rio-air"
    _age(old)
    assert work.main(["rm", "spike-old-home"]) == 0
    [grave] = work.tombstones(repo)
    assert (grave.name, grave.home, grave.removed_by) == ("spike-old-home", "rio-air", "rio-air")


def test_a_tombstone_naming_a_former_hostname_is_that_machines_and_stays_as_written(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create-only and carried between machines: read through the list, never rewritten."""
    _on_rio_air(repo, monkeypatch)
    old = work.Tombstone(
        "spike-old-grave",
        "riordens-macbook-air",
        "abc123",
        1.0,
        "riordens-macbook-air",
    )
    replica = {"replica": "true", "home": "rio-air", "incarnation": "abc123"}
    assert old.buries("spike-old-grave", replica)
    other = dataclasses.replace(old, home="rio-ubu", removed_by="rio-ubu")
    assert not other.buries("spike-old-grave", replica)
    assert work.write_tombstone(repo, old)
    assert work.tombstones(repo) == [old]


def test_a_claim_owned_under_a_former_hostname_is_this_machines(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A new claim's owner is the row's name; an old one under the alias is known dead here."""
    _on_rio_air(repo, monkeypatch)
    claim = work.claim_name(repo, "fix-claimed-here")
    owner = (claim / "owner").read_text(encoding="utf-8").split()
    assert owner == ["rio-air", str(os.getpid())]
    old = repo / ".work" / "names" / "fix-claimed-before"
    _ = _write(old / "owner", "Riordens-MacBook-Air.local 999999\n")
    assert work._claim_is_stale(old)
    _ = _write(old / "owner", "rio-ubu 999999\n")
    assert not work._claim_is_stale(old)


def test_a_machine_with_no_name_takes_no_claim_and_owns_none(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty name (``$DSF_MACHINE_ID=.``) refuses the claim; a ``.`` owner is never its own."""
    _on_rio_air(repo, monkeypatch)
    monkeypatch.setenv(fleet.MACHINE_ENV, ".")
    with pytest.raises(work.WorkError, match="this machine has no name"):
        _ = work.claim_name(repo, "fix-nameless")
    assert not (repo / ".work" / "names" / "fix-nameless").exists()
    dotted = repo / ".work" / "names" / "fix-dotted"
    _ = _write(dotted / "owner", ". 999999\n")
    assert not work._claim_is_stale(dotted)


def test_new_and_adopt_record_this_machine_as_the_copys_home(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(fleet.MACHINE_ENV, "rio-desktop")
    _ = _new("build-homed")
    assert work.locate(repo, "build-homed").note["home"] == "rio-desktop"
    clone = repo / ".work" / "clones" / "spike-adopted-home"
    _ = _git_out(repo, "clone", "-q", "-o", "parent", str(repo), str(clone))
    assert work.main(["adopt", str(clone), "spike-adopted-home"]) == 0
    assert work.locate(repo, "spike-adopted-home").note["home"] == "rio-desktop"


def _make_replica(path: Path, home: str = "rio-mac") -> None:
    work.write_note(path, "clone", {"replica": "true", "home": home})


def test_save_land_and_rm_refuse_a_replica_and_name_its_home(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-replica")
    _ = _write(path / "gone.txt", "edited on the replica\n")
    _make_replica(path)
    for command in ("save", "land", "rm"):
        assert work.main([command, "spike-replica"]) == 1
        error = capsys.readouterr().err
        assert "spike-replica is a replica of rio-mac's copy" in error
        assert "fleet_sync.py handoff spike-replica" in error
    assert (repo / "gone.txt").read_text(encoding="utf-8") == "to delete\n"
    assert "save-1" not in _pins(repo).get("spike-replica", {})
    _age(path)
    assert work.main(["rm", "spike-replica", "--discard"]) == 0
    assert not path.exists()


@pytest.mark.usefixtures("repo")
def test_list_marks_a_replica_with_its_home(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _make_replica(_new("spike-listed"))
    _ = capsys.readouterr()
    assert work.main(["list", "--json"]) == 0
    [row] = json_list(json_loads(capsys.readouterr().out))
    assert json_object(row)["replica"] == "yes"
    assert json_object(row)["home"] == "rio-mac"
    assert work.main(["list"]) == 0
    assert "replica-of=rio-mac" in capsys.readouterr().out


@pytest.mark.usefixtures("repo")
def test_rm_right_after_a_sync_needs_no_wait() -> None:
    path = _new("spike-synced")
    _ = _write(path / "new.txt", "as the sync wrote it\n")
    work.write_note(path, "clone", {"syncedat": str(time.time())})
    assert work.main(["rm", "spike-synced", "--discard"]) == 0


@pytest.mark.usefixtures("repo")
def test_run_rebuilds_a_venv_marked_stale_before_the_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    path = _new("spike-stale-venv")
    _fake_venv(path)
    stale = path / ".git" / work.VENV_STALE
    _ = stale.write_text("", encoding="utf-8")
    _fake_tool(tmp_path, "uv", f'echo "$@" > "{tmp_path / "uv-args"}"')
    monkeypatch.setenv("PATH", os.pathsep.join([str(tmp_path / "bin"), os.environ["PATH"]]))
    assert (
        work.main(
            [
                "run",
                "spike-stale-venv",
                "--",
                "python",
                "-c",
                "print('ran')",
            ],
        )
        == 0
    )
    assert (tmp_path / "uv-args").read_text(encoding="utf-8").split() == [
        "sync",
        "--frozen",
        "--quiet",
    ]
    assert not stale.exists()
    captured = capfd.readouterr()
    assert "rebuilding it" in captured.err
    assert "ran" in captured.out
    (tmp_path / "uv-args").unlink()
    assert (
        work.main(
            [
                "run",
                "spike-stale-venv",
                "--",
                "python",
                "-c",
                "print('again')",
            ],
        )
        == 0
    )
    assert not (tmp_path / "uv-args").exists()


def test_a_pytest_a_run_starts_again_never_waits_on_the_runs_own_lock(repo: Path) -> None:
    """``run`` hands the hold down: a child taking the same lock (a proof run in a pytest run)."""
    path = _new("bench-nested")
    _fake_venv(path)
    child = (
        "import sys; from pathlib import Path; "
        f"sys.path.insert(0, {str(Path(_locks.__file__).parent)!r}); "
        "import _locks\n"
        "def stuck(line): raise SystemExit('deadlock: ' + line)\n"
        "with _locks.hold_pytest(Path.cwd(), 'child', say=stuck):\n"
        "    print('child ran')"
    )
    assert (
        work.main(
            [
                "run",
                "bench-nested",
                "--",
                "python",
                "-c",
                child,
                "pytest",
            ],
        )
        == 0
    )
    lock = (repo / ".work" / work.PYTEST_LOCK).read_text(encoding="utf-8")
    assert lock.startswith("bench-nested - ")


def test_a_lock_failure_that_is_not_contention_refuses_the_run(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _new("bench-locked")
    _pytest_venv(path)

    def broken(_descriptor: int) -> bool:
        raise OSError(errno.ENOLCK, "no locks available")

    monkeypatch.setattr(_locks, "try_lock", broken)
    assert (
        work.main(
            [
                "run",
                "bench-locked",
                "--",
                "pytest",
            ],
        )
        == work.REFUSED
    )
    assert "cannot take the pytest lock" in capsys.readouterr().err
    assert work.main(["land", "bench-locked"]) == 1
    assert "cannot lock" in capsys.readouterr().err
    _ = repo


def test_a_pytest_command_that_cannot_start_is_its_own_error_not_the_locks(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Only taking the lock is the lock's error: a missing pytest stays a missing program."""
    path = _new("bench-nopytest")
    _fake_venv(path)
    command = [
        "run",
        "bench-nopytest",
        "--",
        "pytest-not-installed-here",
        "pytest",
    ]
    assert work.main(command) == work.REFUSED
    err = capsys.readouterr().err
    assert "No such file or directory" in err
    assert "pytest-not-installed-here" in err
    assert "pytest lock" not in err
    assert (
        (repo / ".work" / work.PYTEST_LOCK)
        .read_text(encoding="utf-8")
        .startswith(
            "bench-nopytest - ",
        )
    )


@pytest.mark.parametrize("option", ["--purpose", "--owner"])
@pytest.mark.parametrize(
    "value",
    [
        "two\nlines",
        "tab\there",
        "bell\a",
        "esc\x1b[2J",
        "line\u2028separator",
        "paragraph\u2029separator",
    ],
)
def test_new_and_adopt_refuse_a_purpose_or_owner_holding_a_control_character(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    option: str,
    value: str,
) -> None:
    assert (
        work.main(
            [
                "new",
                "fix-ctl",
                "--no-setup",
                option,
                value,
            ],
        )
        == 1
    )
    assert "control character" in capsys.readouterr().err
    assert "fix-ctl" not in work.discover(repo)
    harness = repo / ".work" / "clones" / "fix-ctl"
    harness.parent.mkdir(parents=True, exist_ok=True)
    _ = _git_out(repo, "clone", "-q", "--no-hardlinks", "-o", "parent", str(repo), str(harness))
    assert (
        work.main(
            [
                "adopt",
                str(harness),
                "fix-ctl",
                option,
                value,
            ],
        )
        == 1
    )
    assert "control character" in capsys.readouterr().err
    assert not work.locate(repo, "fix-ctl").adopted


def test_land_merges_a_primary_key_update(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _commit_db(
        repo,
        "DROP TABLE term",
        "CREATE TABLE term (id integer PRIMARY KEY AUTOINCREMENT, body text NOT NULL)",
        "INSERT INTO term VALUES (1, 'one')",
    )
    path = _new("fix-db-key")
    _sql(path / DB, "UPDATE term SET id = 100 WHERE id = 1")
    code = work.main(["land", "fix-db-key"])
    assert code == 0, capsys.readouterr()
    assert _terms(repo / DB) == [(100, "one")]


def test_land_without_a_tracked_database_lands_the_rest(repo: Path) -> None:
    _ = _git_out(repo, "rm", "--", DB.as_posix())
    _ = _git_out(repo, "commit", "-qm", "remove fixture database")
    path = _new("fix-no-db")
    _ = _write(path / "gone.txt", "ours\n")
    assert work.main(["land", "fix-no-db"]) == 0
    assert not (repo / DB).exists()
    assert (repo / "gone.txt").read_text() == "ours\n"


def test_land_refuses_a_wal_commit_made_after_the_first_check(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _commit_db(repo, "INSERT INTO term VALUES (1, 'one'), (2, 'two')")
    path = _new("fix-db-late-wal")
    writer = sqlite3.connect(path / DB)
    try:
        _ = writer.execute("PRAGMA journal_mode = WAL")
        _ = writer.execute("PRAGMA wal_autocheckpoint = 0")
        _commit_db(repo, "UPDATE term SET body = 'MAIN-OWNED' WHERE id = 2")
        preflight = work.refuse_live_journals

        def commit_after_check(root: Path, copy_root: Path) -> None:
            preflight(root, copy_root)
            _ = writer.execute("UPDATE term SET body = 'WAL-OWNED' WHERE id = 1")
            writer.commit()

        monkeypatch.setattr(work, "refuse_live_journals", commit_after_check)
        code = work.main(["land", "fix-db-late-wal"])
        output = capsys.readouterr()
        assert code == 1, output
        assert "db.sqlite3-wal holds database writes" in output.err
        assert _terms(repo / DB) == [(1, "one"), (2, "MAIN-OWNED")]
    finally:
        writer.close()
