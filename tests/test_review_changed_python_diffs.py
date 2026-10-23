"""Repo-tooling tests for the commit-vs-HEAD stripped diff helper.

Keeps the CLI, git-inventory and output-location contracts of
``scripts/review_changed_python_diffs_against_head.py``: which side is read
from where, how renames pair, what ``--list`` prints and what ``--prose``
captures. Every row builds a throwaway git repository under ``tmp_path`` and
runs the script from inside it, so the shared checkout's ``docs/shadow/`` is
never written. A live ``/graphql/`` request has no wire shape for git listings
or generated diff files, so none of these rows can move; there is no live
sibling in ``examples/fakeshop/test_query/``.
"""

import os
import subprocess
from pathlib import Path

import pytest

from scripts import review_changed_python_diffs_against_head as diffs
from tests._idioms import json_at, json_list, json_loads, json_object


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write(repo: Path, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    for key, value in {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }.items():
        monkeypatch.setenv(key, value)
    _git(root, "init", "-q", "-b", "main")
    monkeypatch.chdir(root)
    return root


BASE_MODULE = '''"""Module docstring."""


def load(queryset):
    """Load related rows."""
    # Follow the author relation.
    return queryset.select_related("author")
'''


def test_module_imports_as_scripts_package_member() -> None:
    assert callable(diffs.main)
    assert Path("docs/shadow/diff") == diffs.OUTPUT_DIFF


def test_output_dir_receives_all_three_folders_and_docs_shadow_is_untouched(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\n\nVALUE = 1\n")
    _commit(repo, "edit")
    out = tmp_path / "out"

    assert diffs.main([base, "--output-dir", str(out)]) == 0

    assert sorted(entry.name for entry in out.iterdir()) == ["diff", "new", "old"]
    diff_text = (out / "diff" / "pkg__mod.diff").read_text()
    assert "+VALUE = 1\n" in diff_text
    assert "--- old/pkg__mod.stripped.py" in diff_text
    assert (out / "old" / "pkg__mod.stripped.py").is_file()
    assert (out / "new" / "pkg__mod.overview.md").is_file()
    assert not (repo / "docs").exists()


def test_new_side_is_head_by_default_and_working_tree_only_when_asked(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\n\nCOMMITTED = 1\n")
    _commit(repo, "edit")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\n\nCOMMITTED = 1\nDIRTY = 2\n")
    _write(repo, "pkg/untracked.py", "UNTRACKED = 3\n")

    assert diffs.main([base, "--output-dir", str(tmp_path / "head")]) == 0
    assert (
        diffs.main(
            [
                base,
                "--against",
                "worktree",
                "--output-dir",
                str(tmp_path / "wt"),
            ],
        )
        == 0
    )

    head_diff = (tmp_path / "head" / "diff" / "pkg__mod.diff").read_text()
    assert "+COMMITTED = 1\n" in head_diff
    assert "DIRTY" not in head_diff
    assert not head_diff.startswith("#")
    assert not (tmp_path / "head" / "diff" / "pkg__untracked.diff").exists()

    worktree_diff = (tmp_path / "wt" / "diff" / "pkg__mod.diff").read_text()
    assert worktree_diff.startswith(diffs.WORKTREE_HEADER)
    assert "+DIRTY = 2\n" in worktree_diff
    assert "+UNTRACKED = 3\n" in (tmp_path / "wt" / "diff" / "pkg__untracked.diff").read_text()


def _snapshot(repo: Path, tmp_path: Path) -> str:
    """Return a commit of the whole working content, untracked files included, parent ``HEAD``."""
    env = {**os.environ, "GIT_INDEX_FILE": str(tmp_path / "snapshot-index")}
    for args in (("read-tree", "HEAD"), ("add", "-A")):
        _ = subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)
    tree = subprocess.run(
        ["git", "write-tree"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return _git(repo, "commit-tree", tree, "-p", "HEAD", "-m", "snapshot")


def _changes(base: str) -> list[tuple[str, str, str | None]]:
    return [
        (change.status, change.path, change.old_path)
        for change in diffs._changed_python_files(base, new_rev=None)
    ]


@pytest.mark.parametrize(
    ("step", "expected"),
    [
        pytest.param((), [("A", "pkg/new.py", None)], id="untracked"),
        pytest.param(("add", "pkg/new.py"), [("A", "pkg/new.py", None)], id="staged"),
        pytest.param(("add", "-N", "pkg/new.py"), [("A", "pkg/new.py", None)], id="intent-to-add"),
        pytest.param(
            (
                "rm",
                "-q",
                "--cached",
                "pkg/keep.py",
            ),
            [("A", "pkg/new.py", None)],
            id="rm-cached-unchanged",
        ),
    ],
)
def test_worktree_listing_is_independent_of_the_index(
    repo: Path,
    step: tuple[str, ...],
    expected: list[tuple[str, str, str | None]],
) -> None:
    _write(repo, "pkg/keep.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/new.py", "NEW = 1\n")
    if step:
        _git(repo, *step)

    assert _changes(base) == expected


def test_worktree_listing_pairs_an_unstaged_move_as_a_rename(repo: Path) -> None:
    _write(repo, "pkg/keep.py", BASE_MODULE)
    base = _commit(repo, "base")
    (repo / "pkg" / "keep.py").rename(repo / "pkg" / "moved.py")

    assert _changes(base) == [("R", "pkg/moved.py", "pkg/keep.py")]


@pytest.mark.parametrize(
    ("after_snapshot", "expected"),
    [
        pytest.param(None, [], id="unchanged"),
        pytest.param("edit", [("M", "pkg/u.py", None)], id="edited"),
        pytest.param("move", [("R", "pkg/v.py", "pkg/u.py")], id="moved"),
    ],
)
def test_worktree_listing_reads_a_baseline_holding_an_untracked_file(
    repo: Path,
    tmp_path: Path,
    after_snapshot: str | None,
    expected: list[tuple[str, str, str | None]],
) -> None:
    _write(repo, "pkg/keep.py", BASE_MODULE)
    _commit(repo, "base")
    _write(repo, "pkg/u.py", BASE_MODULE.replace('"author"', '"owner"'))
    base = _snapshot(repo, tmp_path)
    if after_snapshot == "edit":
        _write(repo, "pkg/u.py", BASE_MODULE.replace('"author"', '"editor"'))
    elif after_snapshot == "move":
        (repo / "pkg" / "u.py").rename(repo / "pkg" / "v.py")

    assert _changes(base) == expected


def test_worktree_run_on_a_baseline_holding_an_unchanged_untracked_file_finds_nothing(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write(repo, "pkg/keep.py", BASE_MODULE)
    _commit(repo, "base")
    _write(repo, "pkg/u.py", "UNTRACKED = 1\n")
    base = _snapshot(repo, tmp_path)

    assert (
        diffs.main(
            [
                base,
                "--against",
                "worktree",
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )
        == 0
    )
    assert "No eligible changed .py files" in capsys.readouterr().err


def test_worktree_listing_ignores_the_callers_global_ignore_file(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(repo, "pkg/keep.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/scratch.local.py", "LOCAL = 1\n")
    home = tmp_path / "home"
    _write(home, ".config/git/ignore", "*.local.py\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))

    assert _changes(base) == [("A", "pkg/scratch.local.py", None)]


def test_worktree_run_leaves_the_shared_index_untouched(repo: Path, tmp_path: Path) -> None:
    _write(repo, "pkg/keep.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/new.py", "NEW = 1\n")
    os.utime(repo / "pkg" / "keep.py", (1, 1))
    index = repo / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns)

    assert (
        diffs.main(
            [
                base,
                "--against",
                "worktree",
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )
        == 0
    )
    assert (index.read_bytes(), index.stat().st_mtime_ns) == before


def test_rename_reads_old_side_from_the_pre_rename_path(repo: Path, tmp_path: Path) -> None:
    _write(repo, "pkg/before.py", BASE_MODULE)
    base = _commit(repo, "base")
    _git(repo, "mv", "pkg/before.py", "pkg/after.py")
    _write(repo, "pkg/after.py", BASE_MODULE.replace('"author"', '"editor"'))
    _commit(repo, "rename")

    changes = diffs._changed_python_files(base)
    assert changes == [diffs._Change("R", "pkg/after.py", "pkg/before.py")]

    out = tmp_path / "out"
    assert (
        diffs.main(
            [
                base,
                "--output-dir",
                str(out),
                "--keep-literals",
            ],
        )
        == 0
    )
    diff_text = (out / "diff" / "pkg__after.diff").read_text()
    assert "--- old/pkg__before.stripped.py" in diff_text
    assert '-    return queryset.select_related("author")\n' in diff_text
    assert '+    return queryset.select_related("editor")\n' in diff_text
    assert "\n+def load" not in diff_text
    assert "\n def load(queryset):\n" in diff_text


def test_include_flags_admit_init_and_test_paths(repo: Path) -> None:
    _write(repo, "pkg/__init__.py", "")
    _write(repo, "pkg/testing/client.py", "")
    base = _commit(repo, "base")
    _write(repo, "pkg/__init__.py", "__all__ = ()\n")
    _write(repo, "pkg/testing/client.py", "CLIENT = 1\n")
    _commit(repo, "edit")

    assert diffs._changed_python_files(base) == []
    included = diffs._changed_python_files(base, include_tests=True, include_init=True)
    assert [change.path for change in included] == ["pkg/__init__.py", "pkg/testing/client.py"]


def test_list_json_reports_changes_head_blobs_and_dirty_group(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    _write(repo, "pkg/gone.py", "GONE = 1\n")
    _commit(repo, "base")
    _git(repo, "tag", "v1")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\nEDIT = 1\n")
    _write(repo, "pkg/added.py", "ADDED = 1\n")
    (repo / "pkg" / "gone.py").unlink()
    head = _commit(repo, "edit")
    _write(repo, "pkg/added.py", "ADDED = 2\n")
    _write(repo, "pkg/new.py", "NEW = 1\n")

    assert diffs.main(["--list", "--json"]) == 0
    payload = json_object(json_loads(capsys.readouterr().out))

    assert payload["base"] == "v1"
    assert payload["head"] == head
    assert payload["changed"] == [
        {
            "status": "A",
            "path": "pkg/added.py",
            "old_path": None,
            "head_blob": _git(repo, "rev-parse", "HEAD:pkg/added.py"),
        },
        {
            "status": "D",
            "path": "pkg/gone.py",
            "old_path": None,
            "head_blob": None,
        },
        {
            "status": "M",
            "path": "pkg/mod.py",
            "old_path": None,
            "head_blob": _git(repo, "rev-parse", "HEAD:pkg/mod.py"),
        },
    ]
    dirty = {json_at(row, "path"): row for row in json_list(payload, "dirty")}
    assert set(dirty) == {"pkg/added.py", "pkg/new.py"}
    assert json_at(dirty, "pkg/added.py", "status") == " M"
    assert json_at(dirty, "pkg/added.py", "worktree_blob") == _git(
        repo,
        "hash-object",
        "pkg/added.py",
    )
    assert json_at(dirty, "pkg/new.py", "status") == "??"
    assert json_at(dirty, "pkg/new.py", "head_blob") is None
    assert not (repo / "docs").exists()


def test_prose_captures_a_docstring_only_change_and_skips_code_changes(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    edited = BASE_MODULE.replace("Load related rows.", "Load the author row.").replace(
        '"author"',
        '"editor"',
    )
    _write(repo, "pkg/mod.py", edited)
    _commit(repo, "edit")
    out = tmp_path / "out"

    args = [
        base,
        "--output-dir",
        str(out),
        "--prose",
        "--collapse-blank",
        "--keep-literals",
    ]
    assert diffs.main(args) == 0

    prose = (out / "diff" / "pkg__mod.prose.diff").read_text()
    assert "@@ -5,1 +5,1 @@ pkg/mod.py::load\n" in prose
    assert diffs.MIXED_HUNK_NOTE not in prose
    assert '-    """Load related rows."""\n' in prose
    assert '+    """Load the author row."""\n' in prose
    assert "editor" not in prose
    code = (out / "diff" / "pkg__mod.diff").read_text()
    assert '+    return queryset.select_related("editor")\n' in code
    assert "Load" not in code
    assert "\n+\n" not in code


def test_prose_carries_every_prose_line_of_a_region_that_also_changes_code(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    edited = (
        BASE_MODULE.replace("Load related rows.", "Load the author row.")
        .replace("Follow the author relation.", "Prefetch the author relation.")
        .replace("select_related", "prefetch_related")
    )
    _write(repo, "pkg/mod.py", edited)
    _commit(repo, "edit")
    out = tmp_path / "out"

    assert (
        diffs.main(
            [
                base,
                "--output-dir",
                str(out),
                "--prose",
            ],
        )
        == 0
    )

    prose = (out / "diff" / "pkg__mod.prose.diff").read_text()
    assert f"@@ -5,3 +5,3 @@ pkg/mod.py::load {diffs.MIXED_HUNK_NOTE}\n" in prose
    assert '-    """Load related rows."""\n' in prose
    assert '+    """Load the author row."""\n' in prose
    assert "-    # Follow the author relation.\n" in prose
    assert "+    # Prefetch the author relation.\n" in prose
    code = (out / "diff" / "pkg__mod.diff").read_text()
    assert "+    return queryset.prefetch_related(...)\n" in code
    assert "Load" not in code
    assert "relation." not in code


def test_prose_is_empty_for_a_change_that_touches_code_alone(repo: Path, tmp_path: Path) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/mod.py", BASE_MODULE.replace("select_related", "prefetch_related"))
    _commit(repo, "edit")
    out = tmp_path / "out"

    assert (
        diffs.main(
            [
                base,
                "--output-dir",
                str(out),
                "--prose",
            ],
        )
        == 0
    )

    assert (out / "diff" / "pkg__mod.prose.diff").read_text() == ""
    code = (out / "diff" / "pkg__mod.diff").read_text()
    assert "+    return queryset.prefetch_related(...)\n" in code
