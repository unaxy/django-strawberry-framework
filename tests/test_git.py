"""Repo-tooling tests for the scripts' one git runner and every site that reads through it.

Keeps the contracts of ``scripts/_git.py`` against throwaway git repositories
under ``tmp_path``: a script's answer about a checkout (a status baseline, an
untracked listing, a pathspec listing, a ``hash-object`` id) is the
repository's, equal for a caller whose global config, XDG ignore and
attributes files or stray ``GIT_*`` variables would change it and for a caller
with none; a ``status`` leaves ``.git/index`` untouched; ``GIT_INDEX_FILE``
reaches the generators that read a hook's or a private index; and the
caller's ``safe.directory`` trust is kept, never widened. The caller's setup
lives under a private ``HOME`` and XDG config directory with the system config
switched off, so neither the session nor the machine running the tests leaks
in. A live ``/graphql/`` request has no wire shape for git listings, so none
of these rows can move. There is no live sibling in
``examples/fakeshop/test_query/``.
"""

import ast
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import (
    _bench_common,
    _git,
    _plan_common,
    bug_hunt,
    build_kanban_tracked_path_constants,
    build_tree_md,
    check_trailing_commas,
    check_type_suppressions,
    list_package_python_changes_by_commit,
    review_inspect,
    review_plan,
    work,
    workspace,
)
from scripts import review_changed_python_diffs_against_head as diffs
from scripts import review_historical_package_snapshot_at_commit as snapshot

PACKAGE = review_plan.PACKAGE_DIR
# ``git`` 2.35 and later read this test variable as "the checkout belongs to another user".
ANOTHER_OWNER = {"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1"}


def _write(path: Path, content: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        _ = path.write_bytes(content)
    else:
        _ = path.write_text(content, encoding="utf-8")
    return path


def _fixture_env(**extra: str) -> dict[str, str]:
    """Return an environment for building fixtures that no caller setting reaches."""
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        XDG_CONFIG_HOME=os.devnull,
    )
    env.update(extra)
    return env


def _fixture_git(root: Path, *args: str, **extra: str) -> str:
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
        env=_fixture_env(**extra),
    )
    return result.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / PACKAGE / "__init__.py", "VALUE = 1\n")
    _write(root / PACKAGE / "core.py", "CORE = 2\n")
    _write(root / "tests" / "test_core.py", "TEST = 3\n")
    _write(root / ".gitignore", "ignored.txt\n")
    _ = _fixture_git(root, "init", "-q")
    _ = _fixture_git(root, "add", "-A")
    _ = _fixture_git(root, "commit", "-q", "-m", "initial")
    return root


def _head(repo: Path) -> str:
    return _fixture_git(repo, "rev-parse", "HEAD").strip()


def _callers_home(home: Path, files: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    for name, content in files.items():
        _write(home / name, content.format(home=home))
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))


@pytest.fixture
def bare_caller(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A caller with no git setup of its own, no system config and no stray ``GIT_*`` variable.

    The machine's system config is the caller's protected scope too, so a runner image whose
    ``/etc/gitconfig`` trusts every checkout (``safe.directory = *``) would hand that trust on;
    ``GIT_CONFIG_NOSYSTEM`` switches it off for the trust read as it does for git itself.
    """
    for name in list(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    _callers_home(tmp_path / "bare-home", {}, monkeypatch)


def _hostile_caller(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
    variables: dict[str, str],
) -> None:
    _callers_home(tmp_path / "home", files, monkeypatch)
    for name, value in variables.items():
        monkeypatch.setenv(name, value.format(home=tmp_path / "home"))


# Each row is a caller setup that hides ``*.local.py`` from an untracked listing.
CALLERS_IGNORE_SETUPS = [
    pytest.param({".config/git/ignore": "*.local.py\n"}, {}, id="xdg-ignore"),
    pytest.param(
        {".gitconfig": "[core]\n\texcludesFile = {home}/excludes\n", "excludes": "*.local.py\n"},
        {},
        id="global-excludes-file",
    ),
    pytest.param(
        {"excludes": "*.local.py\n"},
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.excludesFile",
            "GIT_CONFIG_VALUE_0": "{home}/excludes",
        },
        id="config-count-excludes",
    ),
    pytest.param(
        {"excludes": "*.local.py\n"},
        {"GIT_CONFIG_PARAMETERS": "'core.excludesfile'='{home}/excludes'"},
        id="config-parameters-excludes",
    ),
]


def _untracked_python(repo: Path) -> object:
    return review_plan._untracked_python(repo)


def _status_short(repo: Path) -> object:
    return _plan_common.git_status_short(repo)


def _visible_scope(repo: Path, monkeypatch: pytest.MonkeyPatch) -> object:
    monkeypatch.setattr(check_trailing_commas, "REPO_ROOT", repo)
    check_trailing_commas.git_visible_scope.cache_clear()
    try:
        scope = check_trailing_commas.git_visible_scope()
    finally:
        check_trailing_commas.git_visible_scope.cache_clear()
    assert scope is not None
    return sorted(scope[0])


def _workspace_wanted_files(repo: Path) -> object:
    return sorted(workspace.wanted_files(repo))


UNTRACKED_SITES: list[Callable[[Path, pytest.MonkeyPatch], object]] = [
    lambda repo, _monkeypatch: _untracked_python(repo),
    lambda repo, _monkeypatch: _status_short(repo),
    _visible_scope,
    lambda repo, _monkeypatch: _workspace_wanted_files(repo),
]
UNTRACKED_SITE_IDS = [
    "review_plan-untracked",
    "plan_common-status",
    "check_trailing_commas-scope",
    "workspace-wanted-files",
]


@pytest.mark.parametrize("site", UNTRACKED_SITES, ids=UNTRACKED_SITE_IDS)
@pytest.mark.parametrize(("files", "variables"), CALLERS_IGNORE_SETUPS)
@pytest.mark.usefixtures("bare_caller")
def test_an_untracked_listing_ignores_the_callers_ignore_setup(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: Callable[[Path, pytest.MonkeyPatch], object],
    files: dict[str, str],
    variables: dict[str, str],
) -> None:
    _write(repo / PACKAGE / "scratch.local.py", "LOCAL = 1\n")
    expected = site(repo, monkeypatch)
    assert f"{PACKAGE}/scratch.local.py" in str(expected)

    _hostile_caller(tmp_path, monkeypatch, files, variables)

    assert site(repo, monkeypatch) == expected


# Each row is a caller setup that reshapes ``git status --short`` output.
CALLERS_STATUS_SETUPS = [
    pytest.param({".gitconfig": "[status]\n\tshowUntrackedFiles = no\n"}, {}, id="no-untracked"),
    pytest.param({".gitconfig": "[color]\n\tui = always\n"}, {}, id="color-always"),
    pytest.param({".gitconfig": "[status]\n\tbranch = true\n"}, {}, id="status-branch"),
    pytest.param(
        {},
        {"GIT_CONFIG_PARAMETERS": "'status.showuntrackedfiles'='no'"},
        id="config-parameters",
    ),
]


@pytest.mark.parametrize(("files", "variables"), CALLERS_STATUS_SETUPS)
@pytest.mark.usefixtures("bare_caller")
def test_the_status_baseline_ignores_the_callers_status_setup(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
    variables: dict[str, str],
) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")
    expected = _plan_common.git_status_short(repo)
    assert expected == f" M {PACKAGE}/core.py\n?? {PACKAGE}/new.py\n"
    scope = review_plan.build_scope(repo, "HEAD")

    _hostile_caller(tmp_path, monkeypatch, files, variables)

    assert _plan_common.git_status_short(repo) == expected
    assert review_plan.build_scope(repo, "HEAD") == scope


# Each row is a caller setup under which ``hash-object`` would normalize CRLF line endings.
CALLERS_ATTRIBUTE_SETUPS = [
    pytest.param({".gitconfig": "[core]\n\tautocrlf = true\n"}, {}, id="global-autocrlf"),
    pytest.param({".config/git/attributes": "*.py text\n"}, {}, id="xdg-attributes"),
    pytest.param({}, {"GIT_CONFIG_PARAMETERS": "'core.autocrlf'='true'"}, id="config-parameters"),
]


@pytest.mark.parametrize(("files", "variables"), CALLERS_ATTRIBUTE_SETUPS)
@pytest.mark.usefixtures("bare_caller")
def test_a_blob_id_ignores_the_callers_attribute_setup(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
    variables: dict[str, str],
) -> None:
    target = _write(repo / PACKAGE / "crlf.py", b"CRLF = 1\r\n")
    raw = review_inspect._sha1_blob_id(target.read_bytes())
    assert review_inspect._blob_id(target) == (raw, "git")
    assert review_plan._worktree_blobs(repo, [f"{PACKAGE}/crlf.py"]) == {f"{PACKAGE}/crlf.py": raw}

    _hostile_caller(tmp_path, monkeypatch, files, variables)

    assert review_inspect._blob_id(target) == (raw, "git")
    assert review_plan._worktree_blobs(repo, [f"{PACKAGE}/crlf.py"]) == {f"{PACKAGE}/crlf.py": raw}


@pytest.mark.usefixtures("bare_caller")
def test_a_blob_id_keeps_the_repositorys_own_attributes(repo: Path) -> None:
    _write(repo / ".gitattributes", "*.py text\n")
    target = _write(repo / PACKAGE / "crlf.py", b"CRLF = 1\r\n")

    normalized = review_inspect._sha1_blob_id(b"CRLF = 1\n")

    assert review_inspect._blob_id(target) == (normalized, "git")
    assert review_plan._worktree_blobs(repo, [f"{PACKAGE}/crlf.py"]) == {
        f"{PACKAGE}/crlf.py": normalized,
    }


def _tracked_python(repo: Path, _monkeypatch: pytest.MonkeyPatch) -> object:
    return review_plan._tracked_python(repo)


def _suppression_corpus(repo: Path, monkeypatch: pytest.MonkeyPatch) -> object:
    monkeypatch.setattr(check_type_suppressions, "REPO_ROOT", repo)
    return check_type_suppressions.tracked_python_files()


PATHSPEC_SITES: list[Callable[[Path, pytest.MonkeyPatch], object]] = [
    _tracked_python,
    _suppression_corpus,
]


@pytest.mark.parametrize("site", PATHSPEC_SITES, ids=["review_plan-tracked", "suppressions"])
@pytest.mark.parametrize(
    "variables",
    [
        pytest.param({"GIT_LITERAL_PATHSPECS": "1"}, id="literal-pathspecs"),
        pytest.param({"GIT_NOGLOB_PATHSPECS": "1"}, id="noglob-pathspecs"),
        pytest.param({"GIT_ICASE_PATHSPECS": "1"}, id="icase-pathspecs"),
    ],
)
@pytest.mark.usefixtures("bare_caller")
def test_a_pathspec_listing_ignores_the_callers_pathspec_variables(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: Callable[[Path, pytest.MonkeyPatch], object],
    variables: dict[str, str],
) -> None:
    _write(repo / PACKAGE / "CAPS.PY", "CAPS = 1\n")
    _ = _fixture_git(repo, "add", "-A")
    expected = site(repo, monkeypatch)
    assert f"{PACKAGE}/core.py" in str(expected)

    for name, value in variables.items():
        monkeypatch.setenv(name, value)

    assert site(repo, monkeypatch) == expected


@pytest.mark.usefixtures("bare_caller")
def test_the_suppression_corpus_keeps_a_non_ascii_or_spaced_name_whole(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(repo / PACKAGE / "caf\u00e9.py", "CAFE = 1\n")
    _write(repo / PACKAGE / "two words.py", "TWO = 1\n")
    _ = _fixture_git(repo, "add", "-A")
    monkeypatch.setattr(check_type_suppressions, "REPO_ROOT", repo)

    assert sorted(check_type_suppressions.tracked_python_files()) == [
        f"{PACKAGE}/__init__.py",
        f"{PACKAGE}/caf\u00e9.py",
        f"{PACKAGE}/core.py",
        f"{PACKAGE}/two words.py",
        "tests/test_core.py",
    ]


STATUS_SITES: list[Callable[[Path], object]] = [
    _plan_common.git_status_short,
    lambda repo: review_plan.build_scope(repo, "HEAD"),
]


@pytest.mark.parametrize("site", STATUS_SITES, ids=["plan_common-status", "review_plan-scope"])
@pytest.mark.usefixtures("bare_caller")
def test_a_status_leaves_the_index_and_its_stat_data_untouched(
    repo: Path,
    site: Callable[[Path], object],
) -> None:
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")
    os.utime(repo / PACKAGE / "core.py", (1, 1))
    index = repo / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns)

    _ = site(repo)

    assert (index.read_bytes(), index.stat().st_mtime_ns) == before


@pytest.fixture
def private_index(repo: Path, tmp_path: Path) -> Path:
    """Return an index holding ``HEAD`` plus one file only it stages, as a hook's index does."""
    index = tmp_path / "private-index"
    _write(repo / "tests" / "test_staged.py", "STAGED = 1\n")
    _ = _fixture_git(repo, "read-tree", "HEAD", GIT_INDEX_FILE=str(index))
    _ = _fixture_git(repo, "add", "tests/test_staged.py", GIT_INDEX_FILE=str(index))
    return index


def _constants_paths(repo: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, ...]:
    # The builder reaches ``_kanban_lib`` under whichever name its import idiom found.
    for name in ("_kanban_lib", "scripts._kanban_lib"):
        if name in sys.modules:
            monkeypatch.setattr(sys.modules[name], "REPO_ROOT", repo)
    return build_kanban_tracked_path_constants.tracked_file_paths()


@pytest.mark.usefixtures("bare_caller")
def test_the_generators_read_the_index_git_index_file_names(
    repo: Path,
    private_index: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert "tests/test_staged.py" not in _constants_paths(repo, monkeypatch)
    monkeypatch.setattr(check_type_suppressions, "REPO_ROOT", repo)
    assert "tests/test_staged.py" not in check_type_suppressions.tracked_python_files()

    monkeypatch.setenv("GIT_INDEX_FILE", str(private_index))

    assert "tests/test_staged.py" in _constants_paths(repo, monkeypatch)
    assert "tests/test_staged.py" in check_type_suppressions.tracked_python_files()
    listing = build_tree_md._run_git(repo, "ls-files", "-z", "--cached")
    assert listing is not None
    assert "tests/test_staged.py" in listing.split("\0")


@pytest.mark.usefixtures("bare_caller")
def test_the_constants_builder_lists_a_non_ascii_name_whole(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(repo / "tests" / "test_caf\u00e9.py", "CAFE = 1\n")
    _ = _fixture_git(repo, "add", "-A")

    assert _constants_paths(repo, monkeypatch) == (
        f"{PACKAGE}/__init__.py",
        f"{PACKAGE}/core.py",
        "tests/test_caf\u00e9.py",
        "tests/test_core.py",
    )


@pytest.mark.usefixtures("bare_caller")
def test_repository_env_keeps_only_the_repository_locating_variables() -> None:
    caller = {
        "PATH": "/bin",
        "HOME": "/home/caller",
        "XDG_CONFIG_HOME": "/home/caller/.config",
        "GIT_DIR": "/repo/.git",
        "GIT_WORK_TREE": "/repo",
        "GIT_INDEX_FILE": "/scratch/index",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "status.showUntrackedFiles",
        "GIT_CONFIG_VALUE_0": "no",
        "GIT_CONFIG_PARAMETERS": "'color.ui'='always'",
        "GIT_CONFIG_SYSTEM": "/etc/caller-gitconfig",
        "GIT_OPTIONAL_LOCKS": "1",
    }

    assert _git.repository_env(caller, GIT_AUTHOR_NAME="tool") == {
        "PATH": "/bin",
        "HOME": "/home/caller",
        "XDG_CONFIG_HOME": os.devnull,
        "GIT_DIR": "/repo/.git",
        "GIT_WORK_TREE": "/repo",
        "GIT_INDEX_FILE": "/scratch/index",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_AUTHOR_NAME": "tool",
    }


@pytest.mark.usefixtures("bare_caller")
def test_a_checkout_the_caller_marked_safe_stays_readable(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _callers_home(
        tmp_path / "home",
        {".gitconfig": f"[safe]\n\tdirectory = {repo}\n"},
        monkeypatch,
    )

    completed = _git.run_git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == _head(repo)
    assert workspace._git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER).strip() == _head(repo)


@pytest.mark.usefixtures("bare_caller")
def test_the_callers_command_scope_trust_is_kept(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "safe.directory")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(repo))

    completed = _git.run_git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER)

    assert completed.returncode == 0, completed.stderr
    assert _git.caller_safe_directories() == (str(repo),)


@pytest.mark.parametrize(
    "repository_config",
    [
        pytest.param("", id="no-trust-anywhere"),
        pytest.param("[safe]\n\tdirectory = *\n", id="trust-only-in-the-repository"),
    ],
)
@pytest.mark.usefixtures("bare_caller")
def test_a_checkout_the_caller_did_not_mark_safe_is_refused(
    repo: Path,
    repository_config: str,
) -> None:
    with (repo / ".git" / "config").open("a", encoding="utf-8") as stream:
        _ = stream.write(repository_config)

    completed = _git.run_git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER)

    assert completed.returncode == 128
    assert "dubious ownership" in completed.stderr
    assert _git.caller_safe_directories() == ()
    with pytest.raises(workspace.WorkspaceError, match="dubious ownership"):
        _ = workspace._git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER)


@pytest.mark.usefixtures("bare_caller")
def test_trust_held_only_in_git_config_is_refused(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trust = _write(tmp_path / "git-config", "[safe]\n\tdirectory = *\n")
    monkeypatch.setenv("GIT_CONFIG", str(trust))

    completed = _git.run_git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER)

    assert completed.returncode == 128
    assert "dubious ownership" in completed.stderr


@pytest.mark.usefixtures("bare_caller")
def test_global_trust_survives_an_unrelated_git_config(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _callers_home(
        tmp_path / "home",
        {".gitconfig": f"[safe]\n\tdirectory = {repo}\n"},
        monkeypatch,
    )
    unrelated = _write(tmp_path / "git-config", "[color]\n\tui = always\n")
    monkeypatch.setenv("GIT_CONFIG", str(unrelated))

    completed = _git.run_git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == _head(repo)


@pytest.mark.parametrize("trust", ["repo-trusted", "repo-untrusted"])
@pytest.mark.usefixtures("bare_caller")
def test_a_non_utf8_trust_value_leaves_the_runners_working(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    trust: str,
) -> None:
    trusted = trust == "repo-trusted"
    home = tmp_path / "home"
    repo_line = f"\tdirectory = {repo}\n".encode() if trusted else b""
    _write(home / ".gitconfig", b"[safe]\n\tdirectory = /caf\xe9\n" + repo_line)
    _callers_home(home, {}, monkeypatch)
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")

    assert _plan_common.git_status_short(repo) == f"?? {PACKAGE}/new.py\n"
    completed = _git.run_git(repo, "rev-parse", "HEAD", env=ANOTHER_OWNER)

    assert (completed.returncode == 0) is trusted, completed.stderr


@pytest.mark.usefixtures("bare_caller")
def test_the_trust_read_keeps_order_and_list_resets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _callers_home(
        tmp_path / "home",
        {".gitconfig": "[safe]\n\tdirectory = /first\n\tdirectory =\n\tdirectory = /second\n"},
        monkeypatch,
    )

    assert _git.caller_safe_directories() == ("/first", "", "/second")
    assert _git.caller_safe_directory_env() == {
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": "/first",
        "GIT_CONFIG_KEY_1": "safe.directory",
        "GIT_CONFIG_VALUE_1": "",
        "GIT_CONFIG_KEY_2": "safe.directory",
        "GIT_CONFIG_VALUE_2": "/second",
    }


@pytest.mark.usefixtures("bare_caller")
@pytest.mark.parametrize(
    "operation",
    [
        "root",
        "shallow",
        "log",
        "missing-revision",
    ],
)
def test_the_history_lister_reads_a_real_checkout(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """Each history-runner seam reads the same real checkout from its package subdirectory."""
    monkeypatch.chdir(repo / PACKAGE)
    monkeypatch.setenv("GIT_CONFIG_PARAMETERS", "'log.showsignature'='true'")
    if operation == "root":
        monkeypatch.setattr(_git, "CHECKOUT_ROOT", repo.resolve())
        assert list_package_python_changes_by_commit.repo_root() == repo.resolve()
    elif operation == "shallow":
        assert not list_package_python_changes_by_commit.is_shallow_repository(repo)
    elif operation == "log":
        assert (
            list_package_python_changes_by_commit.run_git(["log", "--format=%H"], cwd=repo)
            == f"{_head(repo)}\n"
        )
    else:
        with pytest.raises(list_package_python_changes_by_commit.GitHistoryError):
            list_package_python_changes_by_commit.run_git(["rev-parse", "--verify", "nope"])


@pytest.mark.usefixtures("bare_caller")
@pytest.mark.parametrize("checkout", [True, False], ids=["checkout", "outside-git"])
def test_the_bench_head_reads_a_real_checkout(
    repo: Path,
    tmp_path: Path,
    *,
    checkout: bool,
) -> None:
    """A real checkout yields its HEAD; a directory outside Git yields the unavailable sentinel."""
    root = repo if checkout else tmp_path
    assert _bench_common.git_head(root) == (_head(repo) if checkout else "unavailable")


@pytest.mark.usefixtures("bare_caller")
def test_the_checkout_guard_answers_only_for_the_checkout_holding_the_scripts(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``repo_root`` returns the toplevel git finds only when it is the scripts' own checkout."""
    monkeypatch.chdir(repo / PACKAGE)
    with pytest.raises(_git.CheckoutError, match="this script belongs to") as refused:
        _ = _git.repo_root()
    assert str(repo.resolve()) in str(refused.value)
    assert str(_git.CHECKOUT_ROOT) in str(refused.value)
    monkeypatch.setattr(_git, "CHECKOUT_ROOT", repo.resolve())
    assert _git.repo_root() == repo.resolve()
    assert _git.repo_root(repo) == repo.resolve()


@pytest.mark.skipif(
    not (_git.CHECKOUT_ROOT / ".git").exists(),
    reason="the scripts do not sit in a git checkout (an sdist)",
)
@pytest.mark.usefixtures("bare_caller")
@pytest.mark.parametrize("where", [".", "scripts"], ids=["root", "subdirectory"])
def test_the_checkout_guard_answers_for_the_real_checkout_unpatched(
    monkeypatch: pytest.MonkeyPatch,
    where: str,
) -> None:
    """Run inside the checkout holding the scripts, ``repo_root`` is that checkout."""
    monkeypatch.chdir(_git.CHECKOUT_ROOT / where)
    assert _git.repo_root() == _git.CHECKOUT_ROOT


def _case_changed(path: Path) -> Path:
    """Return ``path`` with its last component upper-cased; skip on a case-sensitive disk."""
    changed = path.with_name(path.name.upper())
    if changed.name == path.name or not changed.exists():
        pytest.skip("the filesystem is case-sensitive")
    return changed


@pytest.mark.usefixtures("bare_caller")
def test_a_checkout_spelled_in_another_case_is_still_the_same_checkout(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On a case-insensitive disk, one checkout named in two cases passes every toplevel check.

    ``CHECKOUT_ROOT`` takes the spelling the script was started with, git answers with the
    spelling on disk: compared as paths they differ, compared as directories they match.
    """
    changed = _case_changed(repo.resolve())
    monkeypatch.setattr(_git, "CHECKOUT_ROOT", changed)
    assert _git.same_directory(_git.repo_root(repo / PACKAGE), changed)
    assert _git.same_directory(_git.repo_root(changed), changed)
    build_tree_md.git_tracked_paths.cache_clear()
    try:
        tracked = build_tree_md.git_tracked_paths(changed)
    finally:
        build_tree_md.git_tracked_paths.cache_clear()
    assert tracked is not None
    assert f"{PACKAGE}/core.py" in tracked.files
    assert work._is_own_checkout(changed)


def test_same_directory_answers_false_for_a_missing_path(tmp_path: Path) -> None:
    """A path that cannot be looked up is no directory, not a traceback."""
    assert not _git.same_directory(tmp_path / "missing", tmp_path)
    assert _git.same_directory(tmp_path / "." / "", tmp_path)


@pytest.mark.usefixtures("bare_caller")
def test_the_checkout_guard_refuses_a_folder_outside_every_checkout(tmp_path: Path) -> None:
    """A current directory git finds no checkout from is a refusal, not a traceback."""
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(_git.CheckoutError, match="finds no checkout"):
        _ = _git.repo_root(outside)


@pytest.mark.usefixtures("bare_caller")
def test_a_copy_whose_git_is_missing_is_refused_not_resolved_to_the_parent(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A copy under the checkout without its ``.git`` resolves to the parent; the guard says no.

    With the ``.work/.git`` sentinel in place git finds no checkout at all, which is the
    same refusal reached one step earlier.
    """
    copy = repo / ".work" / "clones" / "fix-broken"
    _ = _write(copy / PACKAGE / "__init__.py", "VALUE = 1\n")
    monkeypatch.setattr(_git, "CHECKOUT_ROOT", copy.resolve())
    with pytest.raises(_git.CheckoutError, match="this script belongs to"):
        _ = _git.repo_root(copy)
    _ = _write(repo / ".work" / ".git", "gitdir: /nonexistent/dsf-work-sentinel\n")
    with pytest.raises(_git.CheckoutError, match="finds no checkout"):
        _ = _git.repo_root(copy)


@pytest.mark.usefixtures("bare_caller")
@pytest.mark.parametrize("script", ["snapshot", "diffs"])
def test_a_commit_taking_script_in_a_copy_without_git_reports_the_checkout_not_the_commit(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    script: str,
) -> None:
    """The checkout guard answers before the commit check, so a valid hash is never blamed.

    Under the ``.work/.git`` sentinel every git call fails; a commit check run first would
    report the valid hash as invalid instead of naming the missing checkout.
    """
    sha = _head(repo)
    copy = repo / ".work" / "clones" / "fix-broken"
    _ = _write(copy / PACKAGE / "__init__.py", "VALUE = 1\n")
    _ = _write(repo / ".work" / ".git", "gitdir: /nonexistent/dsf-work-sentinel\n")
    monkeypatch.setattr(_git, "CHECKOUT_ROOT", copy.resolve())
    monkeypatch.chdir(copy)
    main = snapshot.main if script == "snapshot" else diffs.main
    assert main([sha]) == 2
    stderr = capsys.readouterr().err
    assert "finds no checkout" in stderr
    assert "Not a valid commit hash" not in stderr


@pytest.mark.usefixtures("bare_caller")
@pytest.mark.parametrize(
    "script",
    [
        "bug_hunt",
        "snapshot",
        "diffs",
        "history",
    ],
)
def test_every_cwd_rooted_script_refuses_a_checkout_other_than_its_own(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    script: str,
) -> None:
    """Started from another checkout, each script writes nothing there and exits non-zero."""
    monkeypatch.chdir(repo)
    before = sorted(
        path.relative_to(repo).as_posix() for path in repo.rglob("*") if ".git" not in path.parts
    )
    if script == "bug_hunt":
        assert bug_hunt.main([]) == 2
    elif script == "snapshot":
        assert snapshot.main(["HEAD"]) == 2
    elif script == "diffs":
        assert diffs.main(["HEAD"]) == 2
    else:
        with pytest.raises(
            list_package_python_changes_by_commit.GitHistoryError,
            match="belongs to",
        ):
            _ = list_package_python_changes_by_commit.main([])
    after = sorted(
        path.relative_to(repo).as_posix() for path in repo.rglob("*") if ".git" not in path.parts
    )
    assert after == before


#: Scripts that read ``rev-parse --show-toplevel`` themselves, each for its own reason.
TOPLEVEL_READERS = {
    # The guard itself.
    "_git.py",
    # Compares the toplevel with the root it was handed and falls back to the filesystem.
    "build_tree_md.py",
    # Asks whether a private copy's own ``.git`` is intact (its toplevel is the copy itself).
    "work.py",
}


def _reads_the_toplevel(source: str) -> bool:
    """Return whether any string in ``source`` carries the ``--show-toplevel`` token.

    The token, not an exact argument constant: ``"git rev-parse --show-toplevel".split()``
    and an f-string reach git the same way a separate ``"--show-toplevel"`` argument does.
    """
    return any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and "--show-toplevel" in node.value
        for node in ast.walk(ast.parse(source))
    )


@pytest.mark.parametrize(
    "source",
    [
        'run(["git", "rev-parse", "--show-toplevel"])',
        'run("git rev-parse --show-toplevel".split())',
        'run(f"git rev-parse --show-toplevel {where}")',
    ],
)
def test_the_toplevel_census_sees_every_spelling_of_the_token(source: str) -> None:
    assert _reads_the_toplevel(source)
    assert not _reads_the_toplevel('run(["git", "rev-parse", "HEAD"])')


def test_no_script_resolves_its_checkout_from_the_current_directory_but_through_the_guard() -> (
    None
):
    """Every other script reaches the checkout root through ``scripts/_git.py::repo_root``."""
    scripts_dir = Path(_git.__file__).resolve().parent
    sources = sorted(scripts_dir.glob("*.py"))
    assert len(sources) > 10
    readers = {
        path.name for path in sources if _reads_the_toplevel(path.read_text(encoding="utf-8"))
    }
    assert readers == TOPLEVEL_READERS


def test_git_dirs_is_gits_own_answer_for_a_checkout_and_a_linked_worktree(
    repo: Path,
    tmp_path: Path,
) -> None:
    """The one common-dir rule ``work.py``, ``workspace.py`` and ``_locks.py`` read."""
    common = (repo / ".git").resolve()
    assert _git.git_dirs(repo) == (common, common)
    linked = tmp_path / "linked"
    _ = _fixture_git(repo, "worktree", "add", "-q", "--detach", str(linked))
    assert _git.git_dirs(linked) == (common / "worktrees" / "linked", common)
    plain = tmp_path / "plain"
    plain.mkdir()
    _ = (plain / ".git").write_text("gitdir: /nonexistent/repo.git\n", encoding="utf-8")
    assert _git.git_dirs(plain) is None


def test_a_gate_copy_of_no_repository_is_refused_by_workspaces_own_error(tmp_path: Path) -> None:
    gate = tmp_path / "gate"
    gate.mkdir()
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    _ = (nowhere / ".git").write_text("gitdir: /nonexistent/repo.git\n", encoding="utf-8")
    with pytest.raises(workspace.WorkspaceError, match="git reads no repository at"):
        _ = workspace.build_gate_git(nowhere, gate)
