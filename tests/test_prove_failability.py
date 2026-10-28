"""Script tests for the failability-proof runner's refusals and restore proof.

Repo tooling: these rows pin ``scripts/prove_failability.py`` (manifest
refusals, exactly-once anchors, mutate-run-restore with byte-compared restore,
acceptance verdicts, and the labelling that stops a narrowed ``--only`` run's
report from reading like a complete one). A live ``/graphql/`` request has no
wire shape for a CLI that mutates tracked source and writes a markdown proof
record. Rungs 1-3 (shipped field, fixture extension, holder schema) would only
wrap those refusals in a GraphQL type, which is not a consumer contract. There
is no live sibling in ``examples/fakeshop/test_query/``.

The runner writes to tracked production source, so the boundaries worth pinning
are the ones that stop it writing the wrong thing or leaving a mutation behind:
the exactly-once anchor, the inside-the-repo target check, the outside-the-repo
scratch check, the scope that may neither turn coverage on nor stop the run
early, the label that may not name a file other than the mutated one, the
restore proved by byte comparison, the acceptance rule that turns a row count
into a verdict, and the labelling that stops a narrowed (``--only``) run's
report from reading like a complete one.

One class of defect has recurred here more than any other: **the emitted record
reads more complete, or more true, than the run actually was** - a missing
baseline, an error-bearing run, a narrowed run, an unexplained zero, a pytest
exit code nothing read, manifest prose rendered instead of the bytes it claims
to describe, a record that never named the file the bytes went to while its
free-text label named a different one, and a scope whose own truncation made the
recorded count a count of other rows. The rows below pin each instance, and
``test_every_captured_field_of_a_run_outcome_is_load_bearing_in_the_record``
pins the shape rather than one instance of it.

The optional manifest fields have rows of their own: a declared
``expect_failing`` set replaces the row-count grading (``[]`` = nothing may
fail), a declared ``isolates`` row makes a one-row result the success verdict
of a row-isolation proof and any other failing set its failure, several sites
mutate and restore together, a ``pre_image`` or ``reverse_patch`` reverts a
file without git, the probe plugin reports the package ``__file__`` and
database ``NAME`` from inside pytest, ``--workspace`` refuses a root outside the
copy, and ``--json`` carries the whole record. Each
repository root keeps a live mutation's pristine copies and marker in one state
directory that no scratch root moves, so a crashed run's marker refuses every
later run against that tree, with or without a scratch root; the directory is
private to its owner, a failed restore leaves everything in it, and once every
restore is proved the copies move to the run's scratch directory, where the
record names them, and the directory is gone. Scratch is per tree under an
explicit root and under the system temporary directory alike, so two runs
against one tree share it and two trees never do. Every run, with or without a
scratch root and anchors-only included, holds an exclusive kernel lock on the
tree itself for its whole duration, which refuses a second concurrent run before
it writes anything, involves no file, and leaves nothing behind when its holder
dies. The original single-anchor shape reads and grades exactly as it did.

``REPO_ROOT`` is monkeypatched to a ``tmp_path`` fake repo (as
``tests/test_clean_up.py`` does), ``XDG_STATE_HOME`` and the system temporary
directory (``tempfile.tempdir`` and ``TMPDIR``) point into ``tmp_path``, and
``_run_scope`` is stubbed or given a stand-in command for pytest, so no test
here mutates a real file, writes under the home or temporary directory or spawns
a real pytest. In process, a scope starts as ``PYTEST_COMMAND`` in this
process's environment; a run in a child process resolves it through a stand-in
``uv`` on ``PATH`` that, like uv, stays the parent of what it runs and forwards
every stop signal it gets to it, ``SIGINT`` 0.2 s late.

A stop signal (SIGINT, SIGTERM, SIGHUP, SIGQUIT) is delivered for real, by the kernel, to
``main`` running in a child process against the fake repo: the stand-in scope
blocks with a grandchild of its own, as pytest and an xdist worker do, so a
row can see the restore, the exit code and every scope process ended. Sending
the signal to the test process instead would end the worker itself whenever the
handler under test was missing.
"""

import dataclasses
import difflib
import errno
import fcntl
import filecmp
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import types
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import pytest
from django.conf import settings

import django_strawberry_framework
from django_strawberry_framework.utils._narrowing import read_attr
from scripts import prove_failability
from tests._idioms import is_object_dict, json_at, json_list, json_loads

if TYPE_CHECKING:
    from typing_extensions import TypeIs


def _is_json_object(value: object) -> "TypeIs[dict[str, object]]":
    """Return whether a decoded JSON value is an object (JSON object keys are always strings)."""
    return isinstance(value, dict)


def _text(value: object, *path: str | int) -> str:
    """The string ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert isinstance(found, str), found
    return found


def _hook(probe: types.ModuleType, name: str) -> "Callable[[object], object]":
    """The probe module's hook ``name``, checked to be callable (``exec`` defines it untyped)."""
    hook = read_attr(probe, name)
    assert callable(hook), name
    return hook


def _json_object(text: str) -> dict[str, object]:
    """Decode ``text``, which every marker and report this script writes holds as one object."""
    document = json_loads(text)
    assert _is_json_object(document), f"expected a JSON object, got {document!r}"
    return document


SOURCE = """def gate(value):
    if value is None:
        raise ValueError("no")
    return value
"""
ANCHOR = '    if value is None:\n        raise ValueError("no")'


@pytest.fixture(autouse=True)
def state_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the state home into ``tmp_path``; the environment reaches child runs too."""
    home = tmp_path / "state-home"
    monkeypatch.setenv(prove_failability.STATE_HOME_ENV, str(home))
    return home


@pytest.fixture(autouse=True)
def system_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the system temporary directory into ``tmp_path``, in process and in child runs."""
    directory = tmp_path / "system-tmp"
    directory.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(directory))
    monkeypatch.setenv("TMPDIR", str(directory))
    return directory


_RESOLVE_SCOPE_LAUNCH = prove_failability._resolve_scope_launch


@pytest.fixture(autouse=True)
def scope_launch_in_this_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start an in-process scope as ``PYTEST_COMMAND`` in this process's environment.

    The real resolution runs ``uv run`` in the fake repo, which is no project; the rows that
    prove it run ``main`` in a child process with a stand-in ``uv`` on ``PATH``, or put
    ``_RESOLVE_SCOPE_LAUNCH`` back.
    """
    monkeypatch.setattr(
        prove_failability,
        "_resolve_scope_launch",
        lambda: (tuple(prove_failability.PYTEST_COMMAND), dict(os.environ)),
    )


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    (repo / "package").mkdir(parents=True)
    target = repo / "package" / "views.py"
    target.write_text(SOURCE, encoding="utf-8")
    monkeypatch.setattr(prove_failability, "REPO_ROOT", repo)
    return repo


@pytest.fixture
def scratch_root(tmp_path: Path) -> Path:
    root = tmp_path / "scratch"
    root.mkdir()
    return root


@pytest.fixture
def state_directory(fake_repo: Path) -> Path:
    """Return the fake repository root's state directory, which exists only while it is used."""
    assert fake_repo == prove_failability.REPO_ROOT
    return prove_failability._tree_state_directory()


def _never_identical(*_args: object, **_kwargs: object) -> bool:
    """A ``filecmp.cmp`` stand-in that reports every pair as different."""
    return False


def _stub_run(
    monkeypatch: pytest.MonkeyPatch,
    failed: Iterable[str] = (),
    errored: Iterable[str] = (),
    summary: str = "stubbed",
    code: int = 1,
    baseline_failed: Iterable[str] = (),
    baseline_errored: Iterable[str] = (),
    baseline_code: int | None = None,
    *,
    first_call_is_baseline: bool = True,
) -> list[prove_failability.ProofEntry]:
    """Stub ``_run_scope``: the first call is the baseline, every later one the mutant.

    The baseline run is the default, so a stub that returned the mutant's failure
    set for both calls would difference the count to zero and pin nothing. Pass
    ``first_call_is_baseline=False`` for the ``--no-baseline`` path, where the only
    run there is *is* the mutant's.

    ``code`` and ``baseline_code`` are the two runs' pytest exit codes, which are
    a validity channel and not a diagnostic: ``baseline_code`` defaults to the
    code a real pytest would return for the stubbed failure set.
    """
    outcomes: list[prove_failability.ProofEntry] = []

    def fake_run_scope(
        entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        outcomes.append(entry)
        if first_call_is_baseline and len(outcomes) == 1:
            return prove_failability.RunOutcome(
                failed_node_ids=tuple(baseline_failed),
                error_node_ids=tuple(baseline_errored),
                summary="baseline: stubbed",
                return_code=(
                    baseline_code
                    if baseline_code is not None
                    else (0 if not baseline_failed else 1)
                ),
            )
        return prove_failability.RunOutcome(
            failed_node_ids=tuple(baseline_failed) + tuple(failed),
            error_node_ids=tuple(errored),
            summary=summary,
            return_code=code,
        )

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    return outcomes


def _manifest(tmp_path: Path, **overrides: object) -> Path:
    entry: dict[str, object] = {
        "label": "package/views.py::gate",
        "target": "package/views.py",
        "anchor": ANCHOR,
        "replacement": "    pass",
        "scope": ["tests/test_x.py"],
    }
    entry.update(overrides)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"proofs": [entry]}), encoding="utf-8")
    return path


def _single_entry(tmp_path: Path, **overrides: object) -> prove_failability.ProofEntry:
    entries, _ = prove_failability.load_manifest(_manifest(tmp_path, **overrides))
    return entries[0]


def _multi_manifest(tmp_path: Path, count: int = 3) -> Path:
    """Write a ``count``-entry manifest, so ``--only`` can select a genuine subset."""
    proofs = [
        {
            "label": f"package/views.py::gate_{index}",
            "target": "package/views.py",
            "anchor": ANCHOR,
            "replacement": "    pass",
            "scope": [f"tests/test_{index}.py"],
        }
        for index in range(1, count + 1)
    ]
    path = tmp_path / "multi.json"
    path.write_text(json.dumps({"proofs": proofs}), encoding="utf-8")
    return path


def _four_failing_rows(monkeypatch: pytest.MonkeyPatch) -> list[prove_failability.ProofEntry]:
    """Stub every entry as a pinned boundary: 4 attributable rows each, so the run exits 0.

    ``_stub_run`` treats only the very first call as a baseline, which is right for a
    one-entry manifest; a multi-entry run needs a baseline/mutant pair per entry, or
    entries after the first difference to zero and grade weakly pinned.
    """
    calls: list[prove_failability.ProofEntry] = []
    failed = tuple(f"tests/test_x.py::test_{index}" for index in range(4))

    def fake_run_scope(
        entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        calls.append(entry)
        if len(calls) % 2 == 1:
            return prove_failability.RunOutcome((), (), "baseline: stubbed", 0)
        return prove_failability.RunOutcome(failed, (), "stubbed", 1)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    return calls


def _provenance(
    package_file: str,
    databases: tuple[tuple[str, str], ...] = (("default", "/ws/examples/fakeshop/db.sqlite3"),),
) -> prove_failability.Provenance:
    """Return one pytest process's provenance as the probe would have recorded it."""
    return prove_failability.Provenance(
        role="controller",
        package_file=package_file,
        package_imported_by_run=True,
        databases=databases,
        executable="/ws/.venv/bin/python",
        cwd="/ws",
        rootpath="/ws",
    )


def test_a_proof_mutates_runs_restores_and_proves_the_restore_by_byte_comparison(
    fake_repo: Path,
    scratch_root: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _stub_run(monkeypatch, failed=("tests/test_x.py::test_a", "tests/test_x.py::test_b"))
    entry = _single_entry(tmp_path)

    result = prove_failability.execute_entry(entry, scratch_root)

    # The mutation was live while the scope ran, and is gone afterwards. The scope
    # ran twice: once unmutated for the baseline, once with the mutation live.
    assert seen == [entry, entry]
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert "filecmp.cmp(shallow=False) True" in result.restore_proof
    assert result.failed_count == 2
    assert result.failure is None
    # No marker survives a proved restore, so a leftover marker always means trouble.
    assert not (state_directory / prove_failability.ACTIVE_MARKER_NAME).exists()


def test_the_mutated_text_is_what_the_scope_actually_runs_against(
    fake_repo: Path,
    scratch_root: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = fake_repo / "package" / "views.py"
    observed: dict[str, str] = {}
    markers: list[dict[str, object]] = []
    calls: list[prove_failability.ProofEntry] = []

    def fake_run_scope(
        entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        calls.append(entry)
        observed[f"text{len(calls)}"] = target.read_text(encoding="utf-8")
        if len(calls) == 1:
            # The baseline runs before the marker is written: nothing is mutated yet.
            assert not (state_directory / prove_failability.ACTIVE_MARKER_NAME).exists()
        else:
            markers.append(
                _json_object(
                    (state_directory / prove_failability.ACTIVE_MARKER_NAME).read_text(
                        encoding="utf-8",
                    ),
                ),
            )
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)

    prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert observed["text1"] == SOURCE
    assert observed["text2"] == "def gate(value):\n    pass\n    return value\n"
    (marker,) = markers
    assert marker["mutated_file"] == str(target)
    restore_from = marker["restore_from"]
    assert isinstance(restore_from, str)
    assert restore_from.endswith("__package__views.py")
    assert Path(restore_from).parent == state_directory / prove_failability.PRISTINE_DIRECTORY_NAME


def test_a_delete_entry_removes_the_anchor_text(
    fake_repo: Path,
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = fake_repo / "package" / "views.py"
    observed: dict[str, str] = {}
    calls: list[prove_failability.ProofEntry] = []

    def fake_run_scope(
        entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        calls.append(entry)
        # The second call is the mutant; the first is the unmutated baseline.
        observed["text"] = target.read_text(encoding="utf-8")
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    # ``delete`` and ``replacement`` are mutually exclusive, so build without one.
    manifest = tmp_path / "delete.json"
    manifest.write_text(
        json.dumps(
            {
                "proofs": [
                    {
                        "label": "package/views.py::gate",
                        "target": "package/views.py",
                        "anchor": ANCHOR,
                        "delete": True,
                        "scope": ["tests/test_x.py"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    entries, _ = prove_failability.load_manifest(manifest)
    assert entries[0].replacement is None
    assert entries[0].mutation.startswith("deleted:")

    prove_failability.execute_entry(entries[0], scratch_root)

    assert observed["text"] == "def gate(value):\n\n    return value\n"
    assert target.read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize(
    ("anchor", "expected"),
    [("not in the file at all", 0), ("value", 3)],
)
def test_an_anchor_that_does_not_match_exactly_once_mutates_nothing(
    fake_repo: Path,
    scratch_root: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    anchor: str,
    expected: int,
) -> None:
    seen = _stub_run(monkeypatch)
    entry = _single_entry(tmp_path, anchor=anchor)

    result = prove_failability.execute_entry(entry, scratch_root)

    assert seen == []
    assert result.failure is not None
    assert f"anchor matched {expected} times" in result.failure
    assert result.outcome is None
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert not state_directory.exists()


@pytest.mark.usefixtures("fake_repo")
def test_check_anchors_only_validates_without_mutating_or_running(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _stub_run(monkeypatch)

    result = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
        anchors_only=True,
    )

    assert seen == []
    assert result.failure is None
    assert result.outcome is None
    # An unrun entry is not a zero-row entry: it must not read as weakly pinned.
    assert result.is_weakly_pinned is False
    assert result.is_inside_rerun_floor is False


def test_a_failed_restore_raises_writes_a_marker_and_stops_the_run(
    fake_repo: Path,
    scratch_root: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch)
    monkeypatch.setattr(filecmp, "cmp", _never_identical)

    with pytest.raises(prove_failability.RestoreProofError):
        prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    marker = _json_object(
        (state_directory / prove_failability.RESTORE_FAILED_MARKER_NAME).read_text(
            encoding="utf-8",
        ),
    )
    assert marker["mutated_file"] == str(fake_repo / "package" / "views.py")
    # The active marker deliberately survives: it is what identifies the live mutation,
    # and the pristine copy it names stays beside it rather than moving to scratch.
    active = _json_object(
        (state_directory / prove_failability.ACTIVE_MARKER_NAME).read_text(encoding="utf-8"),
    )
    restore_from = Path(_text(active, "restore_from"))
    assert restore_from.parent == state_directory / prove_failability.PRISTINE_DIRECTORY_NAME
    assert restore_from.read_text(encoding="utf-8") == SOURCE
    assert marker["restore_from"] == str(restore_from)
    assert not (scratch_root / prove_failability.PRISTINE_DIRECTORY_NAME).exists()


@pytest.mark.usefixtures("fake_repo")
def test_an_unwritable_target_is_a_restore_proof_error_not_a_bare_oserror(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> NoReturn:
        raise PermissionError("read-only file system")

    def fake_run_scope(
        _entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        # Break the restore only AFTER the pristine copy was taken, so the
        # failure lands where a real read-only tree would put it.
        monkeypatch.setattr(shutil, "copyfile", refuse)
        return prove_failability.RunOutcome((), (), "stubbed", 1)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)

    with pytest.raises(prove_failability.RestoreProofError, match="could not be restored"):
        prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)


def test_a_pristine_copy_that_cannot_be_taken_stops_before_mutating(
    fake_repo: Path,
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _stub_run(monkeypatch)

    def refuse(*_args: object, **_kwargs: object) -> NoReturn:
        raise PermissionError("no space left on device")

    monkeypatch.setattr(shutil, "copy2", refuse)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert seen == []
    assert result.failure is not None
    assert "nothing was mutated" in result.failure
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.usefixtures("fake_repo")
def test_a_target_outside_the_repository_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text(SOURCE, encoding="utf-8")

    with pytest.raises(prove_failability.ManifestError, match="outside the repository"):
        prove_failability.load_manifest(_manifest(tmp_path, target=str(outside)))


def test_a_scratch_root_inside_the_repository_is_refused(fake_repo: Path) -> None:
    with pytest.raises(prove_failability.ManifestError, match="inside the repository"):
        prove_failability._resolve_scratch_root(str(fake_repo / "docs"))


@pytest.mark.usefixtures("fake_repo")
def test_a_scratch_root_outside_the_repository_is_created(tmp_path: Path) -> None:
    resolved = prove_failability._resolve_scratch_root(str(tmp_path / "outside-scratch"))

    assert resolved.is_dir()
    assert resolved.parent == tmp_path / "outside-scratch"


def test_a_state_home_inside_the_repository_is_refused(
    fake_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(prove_failability.STATE_HOME_ENV, str(fake_repo / "state"))
    with pytest.raises(prove_failability.ManifestError, match="inside the repository"):
        prove_failability._tree_state_directory()


@pytest.mark.parametrize("value", ["", "relative/state"], ids=["empty", "relative"])
def test_a_state_home_that_is_not_an_absolute_path_falls_back_to_the_xdg_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    value: str,
) -> None:
    monkeypatch.setenv(prove_failability.STATE_HOME_ENV, value)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    assert prove_failability.state_home() == tmp_path / "home" / ".local" / "state"


def test_the_state_directory_named_for_a_root_is_the_one_a_run_against_it_uses(
    fake_repo: Path,
    state_home: Path,
    state_directory: Path,
    tmp_path: Path,
) -> None:
    # ``scripts/workspace.py`` removes a copy's state directory by this name, so it must be
    # the very directory a run against that root writes, and no other root's.
    assert prove_failability.tree_state_directory(fake_repo) == state_directory
    assert state_directory.parent == state_home.resolve() / prove_failability.STATE_DIRECTORY_NAME
    assert prove_failability.tree_state_directory(tmp_path / "repo-b") != state_directory


@pytest.mark.usefixtures("fake_repo")
@pytest.mark.parametrize(
    ("uv_source", "reason"),
    [
        (
            "import sys; sys.stderr.write('the lockfile needs to be updated\\n'); sys.exit(2)",
            "uv run found no environment (2): the lockfile needs to be updated",
        ),
        (
            "import sys; sys.stdout.write('PATH=' + sys.argv[0] + '-bin' + chr(0))",
            "pytest is not on the PATH uv run gives its command",
        ),
    ],
    ids=["no-environment", "no-pytest"],
)
def test_a_scope_launch_uv_run_cannot_resolve_is_refused_before_anything_is_mutated(
    uv_source: str,
    reason: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(prove_failability, "_resolve_scope_launch", _RESOLVE_SCOPE_LAUNCH)
    tools = tmp_path / "tools"
    tools.mkdir()
    uv = tools / "uv"
    _ = uv.write_text(f"#!{sys.executable}\n{uv_source}\n", encoding="utf-8")
    uv.chmod(0o755)
    monkeypatch.setenv("PATH", str(tools))
    target = prove_failability.REPO_ROOT / "package" / "views.py"

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "scratch")],
    )

    assert code == 1
    assert capsys.readouterr().err.endswith(
        f"scope refused: {reason}; nothing was mutated or run\n",
    )
    assert target.read_text(encoding="utf-8") == SOURCE
    # No mutation was ever live, so the tree's state directory is not there.
    assert not prove_failability._tree_state_directory().exists()


@pytest.mark.usefixtures("fake_repo")
def test_a_scope_executable_missing_from_path_is_refused_before_anything_is_written(
    state_home: Path,
    system_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The scope is ``uv run pytest``: with no ``uv`` on PATH the baseline's Popen would raise
    # a raw FileNotFoundError, so the run is refused first, before any directory is made.
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    target = prove_failability.REPO_ROOT / "package" / "views.py"
    scratch = tmp_path / "scratch"

    code = prove_failability.main([str(_manifest(tmp_path)), "--scratch-root", str(scratch)])

    assert code == 1
    assert capsys.readouterr().err == (
        "scope refused: uv is not on PATH, so no entry's scope can run; nothing was mutated, "
        "run or written\n"
    )
    assert target.read_text(encoding="utf-8") == SOURCE
    assert not state_home.exists()
    assert not scratch.exists()
    assert list(system_tmp.iterdir()) == []


@pytest.mark.usefixtures("fake_repo")
def test_an_anchors_only_run_needs_no_scope_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))

    assert prove_failability.main([str(_manifest(tmp_path)), "--check-anchors-only"]) == 0


def test_two_workspace_roots_under_one_scratch_root_never_share_pristine_marker_or_probe_paths(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two verifiers proving one manifest against their own workspace copies, sharing one
    # --scratch-root: B's whole proof runs while A's mutation is live, which is how two
    # parallel runs interleave. Each tree must be restored from its OWN pre-mutation bytes.
    given = tmp_path / "outside-scratch"
    other_repo = tmp_path / "repo-b"
    (other_repo / "package").mkdir(parents=True)
    other_source = SOURCE.replace("    return value", "    return value  # workspace b")
    (other_repo / "package" / "views.py").write_text(other_source, encoding="utf-8")
    entry_a = _single_entry(tmp_path)
    directory_a = prove_failability._resolve_scratch_root(str(given))
    state_a = prove_failability._tree_state_directory()
    monkeypatch.setattr(prove_failability, "REPO_ROOT", other_repo)
    entry_b = _single_entry(tmp_path)
    directory_b = prove_failability._resolve_scratch_root(str(given))
    state_b = prove_failability._tree_state_directory()
    monkeypatch.setattr(prove_failability, "REPO_ROOT", fake_repo)
    calls: list[prove_failability.ProofEntry] = []
    probes: dict[str, list[Path]] = {"a": [], "b": []}
    markers: dict[str, dict[str, object]] = {}
    nested: dict[str, prove_failability.ProofResult] = {}

    def fake_run_scope(
        entry: prove_failability.ProofEntry,
        capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        calls.append(entry)
        name = "a" if entry is entry_a else "b"
        assert capture is not None
        probes[name].append(capture.probe_output)
        state = state_a if name == "a" else state_b
        if calls.count(entry) == 2:
            marker = state / prove_failability.ACTIVE_MARKER_NAME
            markers[name] = _json_object(marker.read_text(encoding="utf-8"))
        if name == "a" and calls.count(entry) == 2:
            monkeypatch.setattr(prove_failability, "REPO_ROOT", other_repo)
            try:
                nested["b"] = prove_failability.execute_entry(entry_b, directory_b)
            finally:
                monkeypatch.setattr(prove_failability, "REPO_ROOT", fake_repo)
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)

    result_a = prove_failability.execute_entry(entry_a, directory_a)

    assert directory_a.parent == directory_b.parent == given
    assert directory_a != directory_b
    assert state_a.parent == state_b.parent
    assert state_a != state_b
    assert len(calls) == 4
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert (other_repo / "package" / "views.py").read_text(encoding="utf-8") == other_source
    assert nested["b"].failure is None
    restore_a = markers["a"]["restore_from"]
    restore_b = markers["b"]["restore_from"]
    assert isinstance(restore_a, str)
    assert isinstance(restore_b, str)
    assert restore_a != restore_b
    assert restore_a.startswith(str(state_a))
    assert restore_b.startswith(str(state_b))
    pristine_a = directory_a / prove_failability.PRISTINE_DIRECTORY_NAME
    pristine_b = directory_b / prove_failability.PRISTINE_DIRECTORY_NAME
    assert result_a.files[0].pristine == str(pristine_a / Path(restore_a).name)
    assert nested["b"].files[0].pristine == str(pristine_b / Path(restore_b).name)
    assert len(probes["a"]) == len(probes["b"]) == 2
    assert not set(probes["a"]) & set(probes["b"])
    assert all(directory_a in path.parents for path in probes["a"])
    assert all(directory_b in path.parents for path in probes["b"])
    assert not state_a.exists()
    assert not state_b.exists()


def _hold_tree_lock(repo: Path) -> int:
    """Take the lock a run takes on ``repo`` through a descriptor of this test's own.

    ``flock`` belongs to the open file description, so a second ``os.open`` in
    this process contends exactly as another process would.
    """
    descriptor = os.open(repo, os.O_RDONLY | os.O_DIRECTORY)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return descriptor


def _tree_lock_is_free(repo: Path) -> bool:
    """Return whether a run could take ``repo``'s lock now, releasing it at once."""
    try:
        os.close(_hold_tree_lock(repo))
    except BlockingIOError:
        return False
    return True


@pytest.mark.parametrize("rerun_scratch", ["same-root", "other-root", "default"])
@pytest.mark.parametrize("writer_pid", ["running", "gone"])
def test_a_crashed_runs_marker_refuses_every_later_run_against_the_tree_and_is_kept(
    fake_repo: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    system_tmp: Path,
    writer_pid: str,
    rerun_scratch: str,
) -> None:
    # A run that holds the tree's lock reads a marker only a crashed run can have left:
    # the writer held the same lock while its mutation was live. So the pid the marker
    # names is no evidence either way - a live one is a reused pid - and both read alike.
    # The marker sits in the tree's state directory, so a rerun given another scratch
    # root, or none, finds it as surely as one given the crashed run's own root.
    seen = _stub_run(monkeypatch)
    marker = state_directory / prove_failability.ACTIVE_MARKER_NAME
    pid = os.getppid() if writer_pid == "running" else None
    pristine = state_directory / prove_failability.PRISTINE_DIRECTORY_NAME / "x"
    restore = f"cp {pristine} {fake_repo}/package/views.py"
    pristine.parent.mkdir(parents=True)
    pristine.write_text(SOURCE, encoding="utf-8")
    marker.write_text(
        json.dumps({"pid": pid, "files": [{"restore_with": restore}]}),
        encoding="utf-8",
    )
    before = marker.read_bytes()
    arguments = [str(_manifest(tmp_path))]
    if rerun_scratch != "default":
        arguments += ["--scratch-root", str(tmp_path / rerun_scratch)]

    code = prove_failability.main(arguments)

    assert code == 1
    assert seen == []
    error = capsys.readouterr().err
    assert "scratch root refused" in error
    assert str(marker) in error
    assert restore in error
    assert "no longer running" in error
    assert marker.read_bytes() == before
    # The refusal comes before the sweep, so the copy the marker names survives intact.
    assert pristine.read_text(encoding="utf-8") == SOURCE
    assert sorted(path.name for path in state_directory.iterdir()) == [
        marker.name,
        prove_failability.PRISTINE_DIRECTORY_NAME,
    ]
    # The refusal comes before the scratch directory is resolved, so none is made.
    assert not (tmp_path / rerun_scratch).exists()
    assert list(system_tmp.iterdir()) == []
    assert _tree_lock_is_free(fake_repo)
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize("mode", ["run", "check-anchors-only"])
@pytest.mark.parametrize("scratch", ["given", "default"])
def test_a_run_against_a_tree_another_run_holds_is_refused_before_anything_is_written(
    fake_repo: Path,
    state_home: Path,
    system_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scratch: str,
    mode: str,
) -> None:
    # The lock names the tree, not the scratch directory, so it refuses a run given any
    # scratch root or none. An anchors-only run reads the tree the holder may be
    # mutating, so it is refused the same way.
    seen = _stub_run(monkeypatch)
    given = tmp_path / "outside-scratch"
    arguments = [str(_manifest(tmp_path))]
    if scratch == "given":
        arguments += ["--scratch-root", str(given)]
    if mode == "check-anchors-only":
        arguments.append("--check-anchors-only")
    holder = _hold_tree_lock(fake_repo)
    try:
        code = prove_failability.main(arguments)
    finally:
        os.close(holder)

    assert code == 1
    assert seen == []
    error = capsys.readouterr().err
    assert "another run holds the lock on the repository root" in error
    assert str(fake_repo) in error
    assert not given.exists()
    assert not state_home.exists()
    assert list(system_tmp.iterdir()) == []
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize("scratch", ["given", "default"])
def test_the_tree_lock_is_held_for_the_whole_run_and_released_when_it_ends(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scratch: str,
) -> None:
    _four_failing_rows(monkeypatch)
    stubbed = prove_failability._run_scope
    held_during: list[bool] = []
    nested: list[int] = []

    def observing_run_scope(
        entry: prove_failability.ProofEntry,
        capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        held_during.append(not _tree_lock_is_free(fake_repo))
        nested.append(prove_failability.main([str(_manifest(tmp_path)), "--check-anchors-only"]))
        return stubbed(entry, capture)

    monkeypatch.setattr(prove_failability, "_run_scope", observing_run_scope)
    arguments = [str(_manifest(tmp_path))]
    if scratch == "given":
        arguments += ["--scratch-root", str(tmp_path / "outside-scratch")]

    code = prove_failability.main(arguments)

    assert code == 0
    assert held_during == [True, True]
    assert nested == [1, 1]
    assert _tree_lock_is_free(fake_repo)


def test_a_holder_killed_mid_run_leaves_no_lock_to_clear(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A crashed holder's lock is never stale and never taken over: the kernel drops it
    # with the process, so there is no file whose contents a contender must judge.
    _four_failing_rows(monkeypatch)
    given = tmp_path / "outside-scratch"
    # Leaving the block closes the holder's stdin, so a failed assertion inside it still
    # ends the holder instead of leaking it into later rows.
    with subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import fcntl, os, sys\n"
                "descriptor = os.open(sys.argv[1], os.O_RDONLY | os.O_DIRECTORY)\n"
                "fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
                "print('held', flush=True)\n"
                "sys.stdin.read()\n"
            ),
            str(fake_repo),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    ) as holder:
        assert holder.stdout is not None
        assert holder.stdout.readline() == "held\n"
        refused = prove_failability.main(
            [str(_manifest(tmp_path)), "--scratch-root", str(given)],
        )
        holder.kill()

    code = prove_failability.main([str(_manifest(tmp_path)), "--scratch-root", str(given)])

    assert refused == 1
    assert code == 0
    assert _tree_lock_is_free(fake_repo)


@pytest.mark.parametrize("code", [errno.ENOLCK, errno.EINVAL], ids=["ENOLCK", "EINVAL"])
@pytest.mark.usefixtures("fake_repo")
def test_a_lock_failure_other_than_contention_propagates_and_closes_the_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    code: int,
) -> None:
    # Only a held lock is a refusal; any other flock error is not evidence that another
    # run holds the tree, so it surfaces as itself and the descriptor does not leak.
    seen = _stub_run(monkeypatch)
    locked: list[int] = []
    closed: list[int] = []
    real_close = os.close

    def failing_flock(descriptor: int, _operation: int) -> None:
        locked.append(descriptor)
        raise OSError(code, os.strerror(code))

    def recording_close(descriptor: int) -> None:
        closed.append(descriptor)
        real_close(descriptor)

    monkeypatch.setattr(fcntl, "flock", failing_flock)
    monkeypatch.setattr(os, "close", recording_close)
    given = tmp_path / "outside-scratch"

    with pytest.raises(OSError, match=os.strerror(code)) as raised:
        _ = prove_failability.main([str(_manifest(tmp_path)), "--scratch-root", str(given)])

    assert not isinstance(raised.value, BlockingIOError)
    assert raised.value.errno == code
    assert len(locked) == 1
    assert closed == locked
    assert seen == []
    assert not given.exists()


def test_without_a_scratch_root_every_run_against_one_tree_shares_its_temporary_namespace(
    state_directory: Path,
    system_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The default scratch is per tree, not per run: two runs against one tree reuse it
    # (the lock keeps them one at a time), and another tree gets its own beside it.
    namespace = (
        system_tmp.resolve()
        / f"{prove_failability.DEFAULT_SCRATCH_DIRECTORY_PREFIX}-{os.getuid()}"
        / prove_failability._tree_namespace()
    )
    documents: list[dict[str, object]] = []
    for run in range(2):
        _four_failing_rows(monkeypatch)
        output = tmp_path / f"run-{run}.json"

        assert prove_failability.main([str(_manifest(tmp_path)), "--json", str(output)]) == 0

        documents.append(_json_object(output.read_text(encoding="utf-8")))
        header = capsys.readouterr().err
        assert f"scratch root: {namespace}" in header
        assert "under the system temporary directory (no scratch root given)" in header
    for document in documents:
        assert document["scratch_root"] == str(namespace)
        assert document["scratch_root_given"] is None
        assert document["state_directory"] == str(state_directory)
        assert document["active_marker"] == str(
            state_directory / prove_failability.ACTIVE_MARKER_NAME,
        )
    assert sorted(path.name for path in namespace.iterdir()) == [
        prove_failability.PRISTINE_DIRECTORY_NAME,
        prove_failability.PROBE_DIRECTORY_NAME,
        prove_failability.RUNS_DIRECTORY_NAME,
    ]
    other_repo = tmp_path / "other-repo"
    other_repo.mkdir()
    monkeypatch.setattr(prove_failability, "REPO_ROOT", other_repo)
    other = prove_failability._resolve_scratch_root(None)
    assert other.parent == namespace.parent
    assert other != namespace
    assert prove_failability._tree_state_directory() != state_directory


@pytest.mark.parametrize("scratch", ["given", "default"])
def test_a_proved_run_leaves_no_state_directory_and_its_pristine_copy_in_scratch(
    state_home: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scratch: str,
) -> None:
    # The state directory exists only while a mutation is live, private to its owner
    # as the XDG specification asks; once the restore is proved the copy moves to the
    # scratch directory, where the record names it, and the state directory goes.
    _four_failing_rows(monkeypatch)
    stubbed = prove_failability._run_scope
    live: list[dict[str, int]] = []

    def observing_run_scope(
        entry: prove_failability.ProofEntry,
        capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        if (state_directory / prove_failability.ACTIVE_MARKER_NAME).exists():
            created = (
                state_home,
                state_home / prove_failability.STATE_DIRECTORY_NAME,
                state_directory,
                state_directory / prove_failability.PRISTINE_DIRECTORY_NAME,
            )
            live.append({path.name: path.stat().st_mode & 0o777 for path in created})
        return stubbed(entry, capture)

    monkeypatch.setattr(prove_failability, "_run_scope", observing_run_scope)
    output = tmp_path / "proof.json"
    arguments = [str(_manifest(tmp_path)), "--json", str(output)]
    if scratch == "given":
        arguments += ["--scratch-root", str(tmp_path / "outside-scratch")]

    assert prove_failability.main(arguments) == 0

    assert live == [dict.fromkeys(live[0], 0o700)]
    assert len(live[0]) == 4
    assert not state_directory.exists()
    assert (state_home / prove_failability.STATE_DIRECTORY_NAME).is_dir()
    document = _json_object(output.read_text(encoding="utf-8"))
    pristine = Path(_text(document, "entries", 0, "files", 0, "pristine"))
    assert pristine.parent == (
        Path(_text(document, "scratch_root")) / prove_failability.PRISTINE_DIRECTORY_NAME
    )
    assert pristine.name.endswith("__package__views.py")
    assert pristine.read_text(encoding="utf-8") == SOURCE
    assert list(pristine.parent.iterdir()) == [pristine]


@pytest.mark.parametrize("scratch", ["given", "default"])
def test_a_stray_pristine_copy_with_no_marker_is_swept_before_the_run(
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scratch: str,
) -> None:
    # A run killed before writing its marker, or after deleting it mid-move, leaves
    # copies and no marker. Under the lock nobody owns them, so the next run sweeps
    # them and the state directory is empty at rest again.
    _four_failing_rows(monkeypatch)
    stray = state_directory / prove_failability.PRISTINE_DIRECTORY_NAME / "stray__views.py"
    stray.parent.mkdir(parents=True)
    stray.write_text("mutated", encoding="utf-8")
    arguments = [str(_manifest(tmp_path))]
    if scratch == "given":
        arguments += ["--scratch-root", str(tmp_path / "outside-scratch")]

    assert prove_failability.main(arguments) == 0

    assert not state_directory.exists()


def test_a_resolved_restore_failed_marker_is_swept_before_the_run(
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # With no live-mutation marker under the lock, the failed restore it recorded was
    # resolved, so its record goes with the rest and the state directory is gone at rest.
    _four_failing_rows(monkeypatch)
    state_directory.mkdir(parents=True)
    (state_directory / prove_failability.RESTORE_FAILED_MARKER_NAME).write_text(
        "{}",
        encoding="utf-8",
    )

    assert prove_failability.main([str(_manifest(tmp_path))]) == 0

    assert not state_directory.exists()


def test_a_scratch_root_that_overlaps_the_state_directory_is_refused(
    fake_repo: Path,
    state_home: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A scratch directory that is the state directory would have its proved copies
    # deleted by the next run's sweep, so it is refused before it is created.
    seen = _stub_run(monkeypatch)
    given = state_home / prove_failability.STATE_DIRECTORY_NAME

    code = prove_failability.main([str(_manifest(tmp_path)), "--scratch-root", str(given)])

    assert code == 1
    assert seen == []
    error = capsys.readouterr().err
    assert "scratch root refused" in error
    assert "overlaps the tree's state directory" in error
    assert not state_directory.exists()
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize("kind", ["symlink", "dangling-symlink", "other-owner"])
@pytest.mark.parametrize("shared", ["failability", "prove_failability"])
def test_a_shared_directory_that_is_not_this_users_own_is_refused_before_anything_is_written(
    fake_repo: Path,
    state_home: Path,
    system_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    shared: str,
    kind: str,
) -> None:
    # The default scratch parent and the state home's directory are shared by every run;
    # in a temporary directory others can write to, someone else may have made them.
    seen = _stub_run(monkeypatch)
    directory = (
        system_tmp.resolve()
        / f"{prove_failability.DEFAULT_SCRATCH_DIRECTORY_PREFIX}-{os.getuid()}"
        if shared == "failability"
        else state_home.resolve() / prove_failability.STATE_DIRECTORY_NAME
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    nowhere = tmp_path / "nowhere"
    directory.parent.mkdir(parents=True, exist_ok=True)
    if kind == "symlink":
        directory.symlink_to(elsewhere, target_is_directory=True)
    elif kind == "dangling-symlink":
        directory.symlink_to(nowhere, target_is_directory=True)
    else:
        directory.mkdir()
        real_lstat = Path.lstat

        # The ownership check reads ``Path.lstat``; Python 3.10's pathlib binds ``os.lstat``
        # at import, so a stub on ``os.lstat`` would never reach it there.
        def foreign_lstat(path: Path) -> os.stat_result:
            status = real_lstat(path)
            if path != directory:
                return status
            fields = list(status)
            fields[4] = os.getuid() + 1
            return os.stat_result(fields)

        monkeypatch.setattr(Path, "lstat", foreign_lstat)

    code = prove_failability.main([str(_manifest(tmp_path))])

    assert code == 1
    assert seen == []
    error = capsys.readouterr().err
    assert "scratch root refused" in error
    assert f"{directory} is not a directory owned by this user" in error
    assert list(elsewhere.iterdir()) == []
    assert not nowhere.exists()
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.usefixtures("fake_repo", "state_home")
def test_users_sharing_one_temporary_directory_get_their_own_default_scratch_parent(
    system_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The default parent is named by the numeric uid: a second user's run is not refused
    # by the directory the first user's run claimed under the same temporary directory.
    real_lstat = Path.lstat
    first_uid = os.getuid()
    second_uid = first_uid + 1
    first = system_tmp.resolve() / f"failability-{first_uid}"
    second = system_tmp.resolve() / f"failability-{second_uid}"

    first_scratch = prove_failability._resolve_scratch_root(None)
    claimed = first_scratch.parent

    # Every directory reads as owned by the second user once it is the caller, except the
    # parent the first run claimed, which stays the first user's.
    def lstat_as_second_user(path: Path) -> os.stat_result:
        status = real_lstat(path)
        fields = list(status)
        fields[4] = first_uid if path == claimed else second_uid
        return os.stat_result(fields)

    monkeypatch.setattr(os, "getuid", lambda: second_uid)
    monkeypatch.setattr(Path, "lstat", lstat_as_second_user)

    second_scratch = prove_failability._resolve_scratch_root(None)

    assert first_scratch == first / prove_failability._tree_namespace()
    assert second_scratch == second / prove_failability._tree_namespace()
    assert first_scratch.is_dir()
    assert second_scratch.is_dir()


def test_a_pristine_copy_that_cannot_move_stays_in_the_state_directory_named_by_the_record(
    fake_repo: Path,
    scratch_root: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A copy is moved only once its restore is proved and the marker is gone, so a move
    # that fails costs nothing but tidiness: the copy stays where it was and the record
    # says so, and the state directory holding it stays too.
    _stub_run(monkeypatch, failed=("tests/test_x.py::test_a",))
    (scratch_root / prove_failability.PRISTINE_DIRECTORY_NAME).write_text("", encoding="utf-8")

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    (record,) = result.files
    pristine = Path(record.pristine)
    assert pristine.parent == state_directory / prove_failability.PRISTINE_DIRECTORY_NAME
    assert pristine.read_text(encoding="utf-8") == SOURCE
    assert sorted(path.name for path in state_directory.iterdir()) == [
        prove_failability.PRISTINE_DIRECTORY_NAME,
    ]
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"scope": ["tests/test_x.py", "--cov=package"]}, "forbidden"),
        ({"scope": []}, "non-empty list"),
        ({"anchor": ""}, "must not be empty"),
        ({"label": ""}, "non-empty string"),
        ({"target": ""}, "non-empty string"),
        ({"delete": True}, "not both"),
        ({"anchor": {"a": 1}}, "list of strings"),
        ({"mutation": 7}, "must be a string"),
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_manifest_refusals(tmp_path: Path, overrides: dict[str, object], expected: str) -> None:
    with pytest.raises(prove_failability.ManifestError, match=expected):
        prove_failability.load_manifest(_manifest(tmp_path, **overrides))


@pytest.mark.parametrize(
    "label",
    [
        "package/other.py::gate",
        "django_strawberry_framework/views.py::GraphQLView.dispatch",
        'package/other.py #"if value is None"',
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_a_label_whose_leading_path_disagrees_with_the_target_is_refused(
    tmp_path: Path,
    label: str,
) -> None:
    # The fail-open this closes: `label` is free manifest text and `target` is resolved
    # separately, so an entry could name a PRODUCTION boundary while the bytes landed in
    # a test file - and the label was the record's only file identity, so nothing
    # downstream could notice. `relative_target` already existed; it just falsified
    # nothing.
    with pytest.raises(prove_failability.ManifestError, match="is not the mutation target"):
        prove_failability.load_manifest(_manifest(tmp_path, label=label))


@pytest.mark.parametrize(
    "label",
    [
        "gate",
        "GraphQLView.dispatch",
        'GraphQLView.dispatch #"if value is None"',
        "package/views.py::gate",
        'package/views.py::gate #"raise ValueError"',
        'package/views.py #"raise ValueError"',
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_a_label_that_claims_no_path_or_the_right_one_is_accepted(
    tmp_path: Path,
    label: str,
) -> None:
    # Only DISAGREEMENT is refused, never absence: the AGENTS.md source-refs rule also
    # blesses `path #"unique substring"` and a bare symbol, so a label with no path prefix
    # is a legitimate shape and must not be rejected. A bare symbol carrying a substring
    # pointer is the trap - `GraphQLView.dispatch` has a dotted tail that reads like a
    # filename, and refusing it would be a false refusal.
    assert prove_failability.load_manifest(_manifest(tmp_path, label=label))[0][0].label == label


def test_an_absolute_leading_path_and_a_top_level_one_are_both_read_as_path_claims(
    fake_repo: Path,
    tmp_path: Path,
) -> None:
    # Two spellings a substring comparison would get wrong: the same file given
    # absolutely (agrees - accept), and a repo-root file named without any `/` at all
    # (disagrees - refuse), which is why the check resolves paths and asks the
    # filesystem rather than matching text.
    absolute = str((fake_repo / "package" / "views.py").resolve())
    entries, _ = prove_failability.load_manifest(_manifest(tmp_path, label=f"{absolute}::gate"))
    assert entries[0].relative_target == "package/views.py"

    (fake_repo / "conftest.py").write_text(SOURCE, encoding="utf-8")
    with pytest.raises(prove_failability.ManifestError, match="is not the mutation target"):
        prove_failability.load_manifest(_manifest(tmp_path, label="conftest.py::gate"))


@pytest.mark.parametrize(
    "fragment",
    [
        "-x",
        "-xvs",
        "-svx",
        "--exitfirst",
        "--maxfail=3",
        "--maxfail",
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_a_scope_that_stops_the_run_early_is_refused_like_cov(
    tmp_path: Path,
    fragment: str,
) -> None:
    # Verified against a real 9-row scope before this was written: `-n0 -x` grades a
    # 4-row boundary as 1 row (**WEAKLY PINNED**) and `-n0 --maxfail=3` grades it 3 rows
    # (inside the re-run acceptance floor), both at pytest exit 1 with every recorded field
    # present, and both reporting fewer pre-existing rows than were already failing. The
    # exit-code channel does not see it: it is only under this repo's default `-n auto`
    # that the same fragments interrupt the session (exit 2) and are already invalid.
    # What no channel can see is that the fragment travels in the RECORDED scope, so the
    # mandatory independent re-run reproduces the same wrong number.
    with pytest.raises(prove_failability.ManifestError, match="stops the run early"):
        prove_failability.load_manifest(
            _manifest(tmp_path, scope=["tests/test_x.py", fragment]),
        )


@pytest.mark.parametrize(
    "scope",
    [
        ["tests/test_x.py", "-k", "test_expiry"],
        ["tests/test_x.py", "-ktest_expiry"],
        ["tests/test_x.py", "-n0"],
        ["tests/test_exitfirst.py::test_maxfail"],
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_a_scope_that_merely_narrows_the_row_set_is_not_refused(
    tmp_path: Path,
    scope: list[str],
) -> None:
    # `-k`, `--deselect` and a node id narrow the row set IDENTICALLY in the unmutated
    # and the mutated run, so the set difference stays a difference of the same rows - a
    # focused scope is the whole point. What is refused is a cut whose position depends
    # on the failures of the run making it. `-ktest_expiry` and a path containing an `x`
    # are the shapes a substring search for `-x` would refuse by mistake.
    assert prove_failability.load_manifest(_manifest(tmp_path, scope=scope))[0][0].scope == tuple(
        scope,
    )


@pytest.mark.usefixtures("fake_repo")
def test_a_missing_replacement_and_a_missing_anchor_are_both_refused(
    tmp_path: Path,
) -> None:
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps({"proofs": [{"label": "x", "target": "package/views.py", "scope": ["a"]}]}),
        encoding="utf-8",
    )
    with pytest.raises(prove_failability.ManifestError, match="'anchor' is required"):
        prove_failability.load_manifest(path)

    path.write_text(
        json.dumps(
            {
                "proofs": [
                    {
                        "label": "x",
                        "target": "package/views.py",
                        "anchor": ANCHOR,
                        "scope": ["a"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    with pytest.raises(prove_failability.ManifestError, match="'replacement' or 'delete'"):
        prove_failability.load_manifest(path)


@pytest.mark.usefixtures("fake_repo")
def test_an_unknown_entry_key_is_refused_so_a_typo_is_not_silently_ignored(
    tmp_path: Path,
) -> None:
    with pytest.raises(prove_failability.ManifestError, match=r"unknown key\(s\) \['ancor'\]"):
        prove_failability.load_manifest(_manifest(tmp_path, ancor=ANCHOR))


@pytest.mark.usefixtures("fake_repo")
def test_a_multi_line_anchor_may_be_given_as_a_list_of_lines(tmp_path: Path) -> None:
    entry = _single_entry(
        tmp_path,
        anchor=["    if value is None:", '        raise ValueError("no")'],
        replacement=["    pass"],
    )

    assert entry.anchor == ANCHOR
    assert entry.replacement == "    pass"


@pytest.mark.usefixtures("fake_repo")
def test_duplicate_labels_are_refused(tmp_path: Path) -> None:
    entry = {
        "label": "same",
        "target": "package/views.py",
        "anchor": ANCHOR,
        "replacement": "    pass",
        "scope": ["tests/test_x.py"],
    }
    path = tmp_path / "dupes.json"
    path.write_text(json.dumps({"proofs": [entry, dict(entry)]}), encoding="utf-8")

    with pytest.raises(prove_failability.ManifestError, match="duplicate label"):
        prove_failability.load_manifest(path)


@pytest.mark.parametrize(
    ("selectors", "expected"),
    [
        ([], ["a", "b", "c"]),
        (["2"], ["b"]),
        (["c", "a"], ["c", "a"]),
        (["1", "1"], ["a"]),
    ],
)
def test_only_selects_by_index_or_label_substring(
    selectors: list[str],
    expected: list[str],
) -> None:
    entries = [
        prove_failability.ProofEntry(name, prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
        for name in ("a", "b", "c")
    ]

    selected = prove_failability.select_entries(entries, selectors)

    assert [entry.label for entry in selected] == expected


@pytest.mark.parametrize("selector", ["9", "nope"])
def test_only_refuses_a_selector_that_matches_nothing(selector: str) -> None:
    entries = [
        prove_failability.ProofEntry("a", prove_failability.REPO_ROOT, "x", "y", "m", ("s",)),
    ]

    with pytest.raises(prove_failability.ManifestError):
        prove_failability.select_entries(entries, [selector])


def test_xdist_progress_lines_are_not_mistaken_for_failing_node_ids() -> None:
    stdout = (
        "[gw3] [ 50%] FAILED tests/test_x.py::test_progress_line_only\n"
        "=========================== short test summary info ============================\n"
        "FAILED tests/test_x.py::test_real - AssertionError: boom\n"
        "FAILED tests/test_x.py::test_real - a duplicate summary line\n"
        "ERROR tests/test_y.py - collection blew up\n"
        "=== 1 failed, 1 error, 40 passed in 3.21s ===\n"
    )

    failed, errored, summary = prove_failability._parse_run_output(stdout)

    assert failed == ("tests/test_x.py::test_real",)
    assert errored == ("tests/test_y.py",)
    assert "1 failed, 1 error, 40 passed" in summary


def test_captured_log_records_above_the_short_summary_are_not_counted_as_errors() -> None:
    stdout = (
        "F.                                                                       [100%]\n"
        "=================================== FAILURES ===================================\n"
        "------------------------------ Captured log call -------------------------------\n"
        "ERROR    django.request:log.py:241 Internal Server Error: /graphql/\n"
        "FAILED    a logger named FAILED:x.py:1 a record, not a row\n"
        "=========================== short test summary info ============================\n"
        "FAILED tests/test_x.py::test_real - assert False\n"
        "1 failed, 1 passed in 0.04s\n"
    )

    failed, errored, summary = prove_failability._parse_run_output(stdout)

    assert failed == ("tests/test_x.py::test_real",)
    assert errored == ()
    assert summary == "1 failed, 1 passed in 0.04s"


@pytest.mark.parametrize(
    ("failed_rows", "weak", "floor"),
    [
        (0, True, True),
        (1, True, True),
        (2, False, True),
        (3, False, True),
        (4, False, False),
    ],
)
def test_the_acceptance_rule_flags_weak_pinning_and_the_rerun_floor(
    failed_rows: int,
    *,
    weak: bool,
    floor: bool,
) -> None:
    entry = prove_failability.ProofEntry(
        "label",
        prove_failability.REPO_ROOT,
        "a",
        "b",
        "m",
        ("s",),
    )
    outcome = prove_failability.RunOutcome(
        failed_node_ids=tuple(f"tests/test_x.py::test_{index}" for index in range(failed_rows)),
        error_node_ids=(),
        summary="stubbed",
        return_code=1,
    )
    result = prove_failability.ProofResult(entry, outcome, "proved", None)

    assert result.failed_count == failed_rows
    assert result.is_weakly_pinned is weak
    assert result.is_inside_rerun_floor is floor
    assert ("WEAKLY PINNED" in prove_failability._verdict(result)) is weak


@pytest.mark.usefixtures("fake_repo")
def test_the_baseline_runs_by_default_and_excludes_rows_that_were_already_failing(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No ``capture_baseline`` argument: the pre-mutation run is a mandatory field of
    # the record, so it is the default. One pre-existing failing row would otherwise
    # inflate the count and make this genuinely 1-row boundary read as 2-row pinned.
    calls = _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_boundary",),
        baseline_failed=("tests/test_x.py::test_flaky",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert len(calls) == 2
    assert result.baseline is not None
    assert result.outcome is not None
    assert result.outcome.failed_node_ids == (
        "tests/test_x.py::test_flaky",
        "tests/test_x.py::test_boundary",
    )
    assert result.attributable_node_ids == ("tests/test_x.py::test_boundary",)
    assert result.failed_count == 1
    assert result.is_weakly_pinned is True


@pytest.mark.usefixtures("fake_repo")
def test_opting_out_of_the_baseline_records_the_missing_mandatory_field(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_boundary",),
        baseline_failed=("tests/test_x.py::test_flaky",),
    )

    result = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
        capture_baseline=False,
    )

    # Only the mutant ran, so the count is the raw failure set - the pre-existing
    # row inflates it. The report must say the field is missing, not imply a green
    # pre-mutation state, because "2 rows" here is not attributable to the mutation.
    assert len(calls) == 1
    assert result.baseline is None
    assert result.failed_count == 1
    report = prove_failability.render_report([result])
    assert "**NOT CAPTURED** (`--no-baseline`)" in report
    assert "not a compliant proof" in report


@pytest.mark.usefixtures("fake_repo")
def test_collection_errors_make_the_count_invalid_rather_than_footnoted(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_a", "tests/test_x.py::test_b"),
        errored=("tests/test_y.py",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.error_count == 1
    assert result.invalid_count_reason is not None
    verdict = prove_failability._verdict(result)
    assert "INVALID COUNT" in verdict
    assert "1 collection/setup error(s)" in verdict
    assert "not a valid count" in verdict
    report = prove_failability.render_report([result])
    assert "NOT A VALID COUNT" in report
    assert "collection/setup errors: 1" in report
    assert "ERROR `tests/test_y.py`" in report


@pytest.mark.usefixtures("fake_repo")
def test_a_baseline_collection_error_also_invalidates_the_count(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The pre-mutation run is the reference the mutant is differenced against, so a
    # scope that cannot even collect unmutated is no reference at all.
    _stub_run(
        monkeypatch,
        failed=("tests/test_x.py::test_a", "tests/test_x.py::test_b"),
        baseline_errored=("tests/test_y.py",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.error_count == 1
    assert result.invalid_count_reason is not None
    assert "in the baseline run" in result.invalid_count_reason


@pytest.mark.parametrize(
    ("code", "reading"),
    [
        (5, "pytest collected no test at all"),
        (4, "pytest rejected the invocation as a usage error"),
        (2, "pytest was interrupted"),
        (3, "pytest hit an internal error"),
        (99, "pytest exited outside its documented code set"),
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_a_mutant_run_that_could_not_report_is_an_invalid_count_not_a_measured_zero(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    code: int,
    reading: str,
) -> None:
    # pytest emits no FAILED line for exit 5, 4, 2 or 3, which is textually identical
    # to a clean run of a boundary nothing pins. Recorded as a measured 0 the entry
    # earns the `why 0` slot, and a hand fill-in of "harness-impossible interleaving"
    # converts a mistyped scope path into an accepted boundary - fail-open, and the
    # same class as the collection-error case above.
    _stub_run(monkeypatch, failed=(), code=code)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.failed_count == 0
    assert result.invalid_count_reason is not None
    assert f"the mutant run exited {code}" in result.invalid_count_reason
    assert reading in result.invalid_count_reason
    assert "INVALID COUNT" in prove_failability._verdict(result)
    # An uncountable run is not a small count: claiming both would prescribe two
    # opposite remedies (more rows, versus fix the run) in one verdict.
    assert result.is_weakly_pinned is False
    assert result.is_inside_rerun_floor is False
    assert "WEAKLY PINNED" not in report
    # And the zero that was never measured is not offered the judgement slot.
    assert "why 0:" not in report
    assert "no `why 0` is asked for here" in report
    assert f"pytest exit code: {code}" in report


@pytest.mark.usefixtures("fake_repo")
def test_exit_five_reads_as_a_wrong_scope_and_every_other_code_as_a_broken_run(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # "Your scope matched no tests" is a different operator action from "your run blew
    # up" - correct the scope path or node id, versus fix the run - so the two must not
    # collapse into one generic sentence that leaves the reader guessing which happened.
    _stub_run(monkeypatch, failed=(), code=5)
    collected_nothing = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
    ).invalid_count_reason

    _stub_run(monkeypatch, failed=(), code=4)
    blew_up = prove_failability.execute_entry(
        _single_entry(tmp_path),
        scratch_root,
    ).invalid_count_reason

    assert collected_nothing is not None
    assert "the scope matched no test at all" in collected_nothing
    assert "a node id that no longer exists" in collected_nothing
    assert "correct the scope and re-run" in collected_nothing
    assert "the run did not complete" not in collected_nothing
    assert blew_up is not None
    assert "the run did not complete" in blew_up
    assert "the scope matched no test" not in blew_up


@pytest.mark.parametrize("code", [5, 4, 2])
@pytest.mark.usefixtures("fake_repo")
def test_a_baseline_run_that_could_not_report_also_invalidates_the_count(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    code: int,
) -> None:
    # The pre-mutation run is the reference the mutant's failure set is differenced
    # against, so a baseline that never collected is no reference at all - and its
    # empty failure set otherwise reads as "nothing was already failing". The mutant
    # here reports 4 rows, so without reading the baseline's code this grades pinned.
    _stub_run(
        monkeypatch,
        failed=tuple(f"tests/test_x.py::test_{index}" for index in range(4)),
        baseline_code=code,
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.failed_count == 4
    assert result.invalid_count_reason is not None
    assert f"the baseline run exited {code}" in result.invalid_count_reason
    assert "invalidates the difference as well" in result.invalid_count_reason
    assert "INVALID COUNT" in prove_failability._verdict(result)
    assert f"(pytest exit code {code})" in prove_failability.render_report([result])


@pytest.mark.usefixtures("fake_repo")
def test_every_invalidating_reason_is_named_rather_than_only_the_first(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Three independent invalidations at once. Reporting one and dropping the others
    # would send the reader to fix the collection error and re-run into the same two
    # broken invocations.
    _stub_run(monkeypatch, errored=("tests/test_y.py",), code=5, baseline_code=4)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert len(result.invalid_count_reasons) == 3
    assert result.invalid_count_reason is not None
    assert "1 collection/setup error(s)" in result.invalid_count_reason
    assert "the mutant run exited 5" in result.invalid_count_reason
    assert "the baseline run exited 4" in result.invalid_count_reason


@pytest.mark.usefixtures("fake_repo")
def test_two_runs_that_failed_the_same_way_are_named_once_not_twice(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A mistyped scope path collects nothing in either run, and repeating the same
    # paragraph under two headings is how a reader learns to skim the verdict.
    _stub_run(monkeypatch, failed=(), code=5, baseline_code=5)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.invalid_count_reasons == (
        prove_failability._uncountable_run_reason("both the mutant and the baseline run", 5),
    )
    assert result.invalid_count_reason is not None
    assert "both the mutant and the baseline run exited 5" in result.invalid_count_reason
    assert "invalidates the difference as well" in result.invalid_count_reason


@pytest.mark.usefixtures("fake_repo")
def test_a_genuinely_measured_zero_still_carries_the_why_zero_judgement_slot(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Exit 0 means the scope ran and every row passed: that IS a zero-row result, and
    # the judgement belongs there. The exit-code check must not swallow the real case.
    _stub_run(monkeypatch, failed=(), code=0)

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.invalid_count_reason is None
    assert result.is_weakly_pinned is True
    assert "why 0: <fill in" in report
    assert "no `why 0` is asked for here" not in report


@pytest.mark.usefixtures("fake_repo")
def test_main_fails_when_the_scope_collected_nothing_at_all(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A typo'd scope path or a retired node id exits 5 with no FAILED lines; the
    # record must not call that a measured 0 and hand it the why-0 slot.
    _stub_run(monkeypatch, failed=(), code=5)

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 1
    captured = capsys.readouterr()
    assert "NOT A VALID COUNT" in captured.out
    assert "the mutant run exited 5" in captured.out
    assert "why 0:" not in captured.out


@pytest.mark.usefixtures("fake_repo")
def test_a_clean_run_has_no_error_count_and_no_invalid_verdict(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.error_count == 0
    assert result.invalid_count_reason is None
    assert prove_failability._verdict(result) == "pinned"


@pytest.mark.usefixtures("fake_repo")
def test_the_report_carries_the_scope_the_node_ids_and_the_restore_proof(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=("tests/test_x.py::test_a",), summary="1 failed in 1.00s")

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert report.startswith("### Failability proofs")
    assert "package/views.py::gate" in report
    assert "tests/test_x.py::test_a" in report
    assert "1 failed in 1.00s" in report
    assert "filecmp.cmp(shallow=False) True" in report
    assert "WEAKLY PINNED" in report
    assert "git" in report
    assert "pre-mutation (unmutated) state of this scope: `baseline: stubbed`" in report


def test_the_record_names_the_file_that_was_actually_mutated(
    fake_repo: Path,
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `relative_target` was computed and rendered nowhere, so every file identity in the
    # emitted record came from the free-text label - the record could not name the file
    # the bytes went to even though the value that falsifies the label already existed.
    # Varying only the target must change the record: the same load-bearing requirement
    # `test_every_captured_field_of_a_run_outcome_is_load_bearing_in_the_record` puts on
    # the observation fields, applied to the one input that is not merely an identifier
    # a reader re-runs.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    entry = _single_entry(tmp_path)

    result = prove_failability.execute_entry(entry, scratch_root)
    report = prove_failability.render_report([result])

    assert "| File mutated |" in report
    assert "| `package/views.py` |" in report
    assert "   - file mutated: `package/views.py`" in report
    moved = dataclasses.replace(
        result,
        entry=dataclasses.replace(entry, target=fake_repo / "package" / "elsewhere.py"),
    )
    assert prove_failability.render_report([moved]) != report


@pytest.mark.usefixtures("fake_repo")
def test_manifest_prose_accompanies_the_derived_mutation_and_never_replaces_it(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The fail-open this closes: the manifest's optional free-text `mutation` was
    # rendered INSTEAD of the derived anchor -> replacement, so an entry claiming "the
    # Host-validation gate deleted" printed exactly that while its anchor may only have
    # perturbed an adjacent line - which `### What gets recorded` forbids outright ("a
    # mutation must remove the boundary, not merely perturb code near it"). The report
    # carried no rendering of the real bytes, so no reader downstream could audit the
    # claim against what was written.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    claimed = "the Host-validation gate deleted"
    entry = _single_entry(tmp_path, mutation=claimed)

    result = prove_failability.execute_entry(entry, scratch_root)
    report = prove_failability.render_report([result])

    derived = '`if value is None: raise ValueError("no")` -> `pass`'
    assert entry.prose == claimed
    assert entry.mutation == derived
    assert derived in report
    assert f"builder's description (unverified prose): {claimed}" in report


@pytest.mark.usefixtures("fake_repo")
def test_an_entry_without_prose_renders_the_derived_mutation_alone(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Absence of the "unverified prose" marker must mean something, so an entry that
    # made no claim does not get an empty one.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    entry = _single_entry(tmp_path)

    report = prove_failability.render_report(
        [prove_failability.execute_entry(entry, scratch_root)],
    )

    assert entry.prose == ""
    assert entry.mutation_applied == entry.mutation
    assert '`if value is None: raise ValueError("no")` -> `pass`' in report
    assert "builder's description" not in report


@pytest.mark.usefixtures("fake_repo")
def test_the_table_prints_the_scope_as_a_runnable_command_not_a_bare_path(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The independent re-run happens "at the scope the record names"; a bare path in
    # the column headed "Scope as run" forces the re-runner to reconstruct --no-cov and
    # the rest of the flag set out of a prose paragraph instead of copying a command.
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    entry = _single_entry(tmp_path)

    report = prove_failability.render_report(
        [prove_failability.execute_entry(entry, scratch_root)],
    )

    assert entry.scope_as_run.startswith("pytest --no-cov")
    assert entry.scope_as_run.endswith("tests/test_x.py")
    assert f"| `{entry.scope_as_run}` |" in report


def test_every_captured_field_of_a_run_outcome_is_load_bearing_in_the_record() -> None:
    """No field of the observation type may be captured and then read by nothing.

    This pins the recurring class rather than one instance of it. A
    ``return_code`` captured and consumed by nothing records a pytest exit 5 as a
    measured zero; the same shape would recur the next time a field is added to the captured observation and
    the record is not taught to read it. Varying one field at a time and
    requiring the rendered record to change is the cheapest mechanical statement
    of "every claim in the record is backed by an observation, and every
    observation reaches the record".

    Scoped deliberately to the observation type: ``ProofEntry`` holds *inputs*,
    and an input the record does not render is a different question (a reader
    re-runs an identifier rather than trusting it).
    """
    variants = {
        "failed_node_ids": ("tests/test_x.py::test_other",),
        "error_node_ids": ("tests/test_y.py",),
        "summary": "a different summary line",
        "return_code": 5,
        "crash_lines": (("tests/test_x.py::test_a", "tests/test_x.py:9: assert 6 == 1"),),
        "provenance": (_provenance("/elsewhere/django_strawberry_framework/__init__.py"),),
        "wall_seconds": 12.5,
        "log_path": "/scratch/runs/001-mutant.log",
    }
    captured = {field.name for field in dataclasses.fields(prove_failability.RunOutcome)}
    assert set(variants) == captured, "a new captured field needs a variant here"
    entry = prove_failability.ProofEntry("a", prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
    reference = prove_failability.RunOutcome(("tests/test_x.py::test_a",), (), "stubbed", 1)
    unaltered = prove_failability.render_report(
        [prove_failability.ProofResult(entry, reference, "proved", None)],
    )

    for name, value in variants.items():
        altered = dataclasses.replace(reference, **{name: value})
        report = prove_failability.render_report(
            [prove_failability.ProofResult(entry, altered, "proved", None)],
        )
        assert report != unaltered, f"RunOutcome.{name} never reaches the emitted record"


@pytest.mark.usefixtures("fake_repo")
def test_a_zero_row_entry_carries_a_why_zero_placeholder_the_tool_cannot_fill(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Weakly pinned and harness-impossible prescribe opposite responses, so the
    # emitted subsection must carry the slot rather than guess or omit it.
    _stub_run(monkeypatch, failed=())

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.failed_count == 0
    assert "why 0: <fill in - weakly pinned" in report
    assert "harness-impossible interleaving" in report
    assert "MUST be replaced by hand" in report


@pytest.mark.usefixtures("fake_repo")
def test_a_nonzero_row_entry_carries_no_why_zero_placeholder(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert "why 0:" not in prove_failability.render_report([result])


@pytest.mark.usefixtures("fake_repo")
def test_a_row_that_is_only_zero_after_the_baseline_difference_still_gets_the_placeholder(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The pre-existing row is the whole failure set, so nothing is attributable: the
    # fail-open this closes is exactly this entry reading as a pinned 1-row boundary.
    _stub_run(
        monkeypatch,
        failed=(),
        baseline_failed=("tests/test_x.py::test_flaky",),
    )

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)
    report = prove_failability.render_report([result])

    assert result.failed_count == 0
    assert "why 0: <fill in" in report
    assert "pre-existing failing rows excluded from the count: 1" in report


@pytest.mark.usefixtures("fake_repo")
def test_main_returns_zero_on_a_pinned_boundary_and_one_on_a_weakly_pinned_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _manifest(tmp_path)
    scratch = tmp_path / "outside-scratch"

    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    assert prove_failability.main([str(manifest), "--scratch-root", str(scratch)]) == 0

    _stub_run(monkeypatch, failed=("tests/test_x.py::test_only",))
    assert prove_failability.main([str(manifest), "--scratch-root", str(scratch)]) == 1
    assert "WEAKLY PINNED" in capsys.readouterr().out


@pytest.mark.usefixtures("fake_repo")
def test_main_fails_when_collection_errors_make_the_count_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # 4 attributable failures would be a pinned boundary; 8 rows that never ran mean
    # the run is not evidence of anything. This is the recorded csrf_exempt incident.
    _stub_run(
        monkeypatch,
        failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)),
        errored=tuple(f"tests/test_y{i}.py" for i in range(8)),
    )

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 1
    captured = capsys.readouterr()
    assert "NOT A VALID COUNT" in captured.out
    assert "8 collection/setup error(s)" in captured.out


@pytest.mark.usefixtures("fake_repo")
def test_main_refuses_output_without_a_baseline_and_runs_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
            "--output",
            str(output),
        ],
    )

    assert code == 1
    assert seen == []
    assert not output.exists()
    assert "--no-baseline cannot be combined with --output" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_repo")
def test_check_anchors_only_may_write_output_without_a_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Nothing ran, so there is no count for a missing baseline to inflate and the
    # emitted block says so in its own words rather than claiming a proof.
    seen = _stub_run(monkeypatch)
    output = tmp_path / "anchors.md"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
            "--check-anchors-only",
            "--output",
            str(output),
        ],
    )

    assert code == 0
    assert seen == []
    assert "no mutation was applied and no scope was run" in output.read_text(encoding="utf-8")


@pytest.mark.usefixtures("fake_repo")
def test_no_baseline_without_output_runs_the_scope_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _stub_run(
        monkeypatch,
        failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)),
        first_call_is_baseline=False,
    )

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
        ],
    )

    assert code == 0
    assert len(seen) == 1


@pytest.mark.usefixtures("fake_repo")
def test_the_legacy_baseline_flag_is_accepted_and_wins_over_no_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--no-baseline",
            "--baseline",
        ],
    )

    assert code == 0
    assert len(seen) == 2


def test_main_reports_a_manifest_error_without_running_anything(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = tmp_path / "broken.json"
    manifest.write_text("{not json", encoding="utf-8")

    assert prove_failability.main([str(manifest)]) == 1
    assert "invalid JSON" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_repo")
def test_main_aborts_with_a_dedicated_code_when_a_restore_cannot_be_proved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _stub_run(monkeypatch)
    monkeypatch.setattr(filecmp, "cmp", _never_identical)

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 3
    assert "RESTORE FAILED" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_repo")
def test_a_failed_restore_still_writes_the_partial_report_to_the_output_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A partial record of a run that stopped with a possibly-live mutation is exactly
    # what the next reader needs; stdout-only would lose it.
    _stub_run(monkeypatch)
    monkeypatch.setattr(filecmp, "cmp", _never_identical)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--output",
            str(output),
        ],
    )

    assert code == 3
    written = output.read_text(encoding="utf-8")
    assert written.startswith("### Failability proofs")
    assert "RUN ABORTED - A RESTORE COULD NOT BE PROVED" in written
    assert prove_failability.RESTORE_FAILED_MARKER_NAME in written
    assert "PARTIAL record" in written
    assert "_(no entry completed)_" in written
    assert "partial report written to" in capsys.readouterr().err


# --- stop signals ------------------------------------------------------------------------


# Spelled out rather than read from the script, so a signal dropped there fails its rows.
STOP_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM,
    signal.SIGHUP,
    signal.SIGQUIT,
)


# Stands in for pytest in a stop-signal run (``cwd`` is the fake repo): it appends its phase
# to ``<P_READY>.started``; in the phase ``P_BLOCK`` names it writes its parent's pid and its
# ``argv[0]`` to ``<P_READY>.launched``, starts a grandchild, says so in ``P_READY`` and blocks
# until ``<P_READY>.release`` exists, the shape of pytest -> xdist worker; in every other phase
# it passes at once. While it blocks, ``P_ON_STOP=teardown`` makes a stop signal append its
# name to ``<P_READY>.got``, take half a second, write the name to ``<P_READY>.teardown`` and
# exit, as pytest's teardown does; ``P_ON_STOP=ignore`` makes it and its grandchild ignore
# every stop signal.
_SCOPE_STANDIN = """
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

source = Path("package/views.py").read_text(encoding="utf-8")
phase = "baseline" if "raise ValueError" in source else "mutant"
with open(os.environ["P_READY"] + ".started", "a", encoding="utf-8") as started:
    started.write(phase + "\\n")
if phase == os.environ["P_BLOCK"]:
    stop_signals = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)

    def teardown(signum, _frame):
        with open(os.environ["P_READY"] + ".got", "a", encoding="utf-8") as got:
            got.write(signal.Signals(signum).name + "\\n")
        time.sleep(0.5)
        Path(os.environ["P_READY"] + ".teardown").write_text(signal.Signals(signum).name)
        sys.exit(1)

    for stop_signal in stop_signals:
        if os.environ["P_ON_STOP"] == "teardown":
            signal.signal(stop_signal, teardown)
        if os.environ["P_ON_STOP"] == "ignore":
            signal.signal(stop_signal, signal.SIG_IGN)
    Path(os.environ["P_READY"] + ".launched").write_text(f"{os.getppid()} {sys.argv[0]}")
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ready = Path(os.environ["P_READY"])
    ready.with_suffix(".tmp").write_text(f"{os.getpid()} {child.pid}", encoding="utf-8")
    os.replace(ready.with_suffix(".tmp"), ready)
    release = Path(os.environ["P_READY"] + ".release")
    deadline = time.monotonic() + 30
    while not release.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
print("1 passed in 0.01s")
"""

# Runs ``main`` in a process of its own, as the CLI does, against the fake repo and the
# stand-in scope (``P_SCOPE``; empty keeps ``PYTEST_COMMAND``, so the stand-in ``uv`` finds
# ``pytest`` in ``P_VENV``). ``restore`` signals the process itself twice inside every restore;
# ``starting`` signals it as each scope process starts, before the run has recorded it;
# ``cli`` runs it through ``_cli``, the script's entry point, instead of ``main``.
_SIGNALLED_RUN = """
import os
import subprocess
import sys
from pathlib import Path

from scripts import prove_failability

repo, manifest, scratch, mode = sys.argv[1:5]
signum = int(os.environ["P_SIGNUM"])
prove_failability.REPO_ROOT = Path(repo)
if os.environ["P_SCOPE"]:
    prove_failability.PYTEST_COMMAND = (sys.executable, "-c", os.environ["P_SCOPE"])
if mode == "restore":
    restore = prove_failability._restore_and_prove

    def signalled_restore(target, pristine):
        os.kill(os.getpid(), signum)
        proof = restore(target, pristine)
        os.kill(os.getpid(), signum)
        return proof

    prove_failability._restore_and_prove = signalled_restore
if mode == "starting":

    class SignalledPopen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if kwargs.get("start_new_session"):
                os.kill(os.getpid(), signum)

    subprocess.Popen = SignalledPopen
arguments = [manifest, "--scratch-root", scratch]
if mode == "cli":
    sys.argv = ["prove_failability.py", *arguments]
    prove_failability._cli()
raise SystemExit(prove_failability.main(arguments))
"""

# Stands in for ``uv`` on ``PATH``: ``uv run [options] [--] <command>`` runs ``<command>``,
# looked up on a ``PATH`` led by ``<P_VENV>/bin``, with ``VIRTUAL_ENV`` set to ``P_VENV``, as a
# child it waits for, and exits with its code. Like uv it forwards every stop signal it gets to
# that child, ``SIGINT`` after 0.2 s and the others at once.
_UV_STANDIN = """
import os
import shutil
import signal
import subprocess
import sys
import threading

arguments = sys.argv[2:]
command = arguments[arguments.index("--") + 1 :] if "--" in arguments else arguments
venv = os.environ["P_VENV"]
env = {
    **os.environ,
    "VIRTUAL_ENV": venv,
    "PATH": os.path.join(venv, "bin") + os.pathsep + os.environ["PATH"],
}
program = shutil.which(command[0], path=env["PATH"]) or command[0]
child = subprocess.Popen([program, *command[1:]], env=env)


def forward(signum, _frame):
    def send():
        if child.poll() is None:
            child.send_signal(signum)

    threading.Timer(0.2 if signum == signal.SIGINT else 0.0, send).start()


for stop_signal in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
    signal.signal(stop_signal, forward)
code = child.wait()
sys.exit(128 - code if code < 0 else code)
"""

# Sets ``P_SIGNUM`` to ``SIG_IGN`` and execs the rest of its argv under a fresh interpreter,
# which inherits the ignored disposition as a process started under ``nohup`` does.
_IGNORING_EXEC = """
import os
import signal
import sys

signal.signal(int(os.environ["P_SIGNUM"]), signal.SIG_IGN)
os.execv(sys.executable, [sys.executable, *sys.argv[1:]])
"""


def _signalled_run(
    fake_repo: Path,
    tmp_path: Path,
    manifest: Path,
    signum: int,
    *,
    mode: str = "external",
    block: str = "none",
    ignored: bool = False,
    on_stop: str = "",
    through_path: bool = False,
) -> "subprocess.Popen[str]":
    """Start ``main`` in a child process whose scope is ``_SCOPE_STANDIN``.

    ``_UV_STANDIN`` is the ``uv`` on its ``PATH``. ``ignored`` starts it the way ``nohup`` or
    a background job does: ``signum`` is already ``SIG_IGN`` when the run's interpreter
    starts, inherited across ``exec``. ``through_path`` keeps ``PYTEST_COMMAND``, so the
    scope is ``_SCOPE_STANDIN`` installed as ``<tmp_path>/venv/bin/pytest``.
    """
    tools = tmp_path / "tools"
    tools.mkdir(exist_ok=True)
    uv = tools / "uv"
    _ = uv.write_text(f"#!{sys.executable}\n{_UV_STANDIN}", encoding="utf-8")
    uv.chmod(0o755)
    venv_pytest = tmp_path / "venv" / "bin" / "pytest"
    venv_pytest.parent.mkdir(parents=True, exist_ok=True)
    _ = venv_pytest.write_text(f"#!{sys.executable}\n{_SCOPE_STANDIN}", encoding="utf-8")
    venv_pytest.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": str(tools) + os.pathsep + os.environ["PATH"],
        "PYTHONPATH": str(Path(prove_failability.__file__).resolve().parents[1]),
        # ``int`` first: on Python 3.10 ``str`` of a ``Signals`` member is ``Signals.SIGTERM``.
        "P_SIGNUM": str(int(signum)),
        "P_SCOPE": "" if through_path else _SCOPE_STANDIN,
        "P_VENV": str(venv_pytest.parents[1]),
        "P_BLOCK": block,
        "P_ON_STOP": on_stop,
        "P_READY": str(tmp_path / "ready"),
    }
    command = [
        sys.executable,
        "-c",
        _SIGNALLED_RUN,
        str(fake_repo),
        str(manifest),
        str(tmp_path / "outside-scratch"),
        mode,
    ]
    if ignored:
        command = [
            sys.executable,
            "-c",
            _IGNORING_EXEC,
            *command[1:],
        ]
    return subprocess.Popen(
        command,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _is_running(pid: int) -> bool:
    """Return whether ``pid`` is a process that has not exited (a zombie has exited)."""
    state = subprocess.run(
        [
            "ps",
            "-o",
            "stat=",
            "-p",
            str(pid),
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return bool(state) and not state.startswith("Z")


def _poll(predicate: "Callable[[], bool]", seconds: float = 20) -> bool:
    """Return whether ``predicate`` became true within ``seconds``."""
    deadline = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.05)
    return True


def _scope_pids(tmp_path: Path) -> list[int]:
    """Return the blocking stand-in's pid and its grandchild's, once it has said so."""
    ready = tmp_path / "ready"
    return (
        [int(pid) for pid in ready.read_text(encoding="utf-8").split()] if ready.exists() else []
    )


def _stop_run(driver: "subprocess.Popen[str]", tmp_path: Path) -> None:
    """Kill whatever a failed row left running, so it cannot outlive the row."""
    for pid in [driver.pid, *_scope_pids(tmp_path)]:
        if _is_running(pid):
            os.kill(pid, signal.SIGKILL)


def _scopes_started(tmp_path: Path) -> list[str]:
    """Return the phase of every scope the run started, in order."""
    started = tmp_path / "ready.started"
    return started.read_text(encoding="utf-8").split() if started.exists() else []


def _run_logs(tmp_path: Path) -> list[str]:
    """Return the run logs the run wrote, by ``<position>-<run name>``."""
    (namespace,) = (tmp_path / "outside-scratch").iterdir()
    # No mutation is left live, so the tree's state directory is gone, markers and all.
    assert not prove_failability._tree_state_directory().exists()
    runs = namespace / prove_failability.RUNS_DIRECTORY_NAME
    return sorted(f"{path.name[:3]}-{path.stem.rsplit('-', 1)[-1]}" for path in runs.glob("*.log"))


@pytest.mark.parametrize("phase", ["baseline", "mutant"])
@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_a_stop_signal_to_the_run_alone_restores_the_tree_and_ends_the_whole_scope(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
    phase: str,
) -> None:
    # The signal reaches the run's process and nothing else - ``kill``, ``timeout``, a
    # harness stopping a background shell - so the scope's processes get no signal of
    # their own and only the run can end them; left alone they outlive it.
    with _signalled_run(fake_repo, tmp_path, _manifest(tmp_path), signum, block=phase) as driver:
        try:
            assert _poll(lambda: bool(_scope_pids(tmp_path)))
            os.kill(driver.pid, signum)
            _, error = driver.communicate(timeout=10)
            # Read before the ``finally`` kills whatever the run left behind.
            scope_ended = _poll(
                lambda: not any(_is_running(pid) for pid in _scope_pids(tmp_path)),
                seconds=5,
            )
        finally:
            _stop_run(driver, tmp_path)

    assert driver.returncode == 128 + signum
    assert f"stopped by {signum.name}" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    # The cut-short run writes no log: it measured nothing. A baseline stop never mutates.
    assert _run_logs(tmp_path) == ([] if phase == "baseline" else ["001-baseline"])
    assert _scopes_started(tmp_path) == (
        ["baseline"] if phase == "baseline" else ["baseline", "mutant"]
    )
    assert scope_ended


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_stop_signals_during_a_restore_let_it_finish_and_stop_the_run_at_the_next_scope(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    # Two signals land inside the restore: one before the copy and one after it, before
    # the marker is removed. The restore and its proof still complete, and the run stops
    # before entry 2 starts a scope, so entry 2 mutates nothing.
    with _signalled_run(
        fake_repo,
        tmp_path,
        _multi_manifest(tmp_path, 2),
        signum,
        mode="restore",
    ) as driver:
        try:
            _, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert driver.returncode == 128 + signum
    assert f"stopped by {signum.name}" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert _run_logs(tmp_path) == ["001-baseline", "001-mutant"]
    assert _scopes_started(tmp_path) == ["baseline", "mutant"]


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_a_stop_signal_the_run_inherited_as_ignored_stays_ignored(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    # ``nohup`` (SIGHUP) or a background job (SIGINT) asked the run to survive the signal:
    # it reaches the run mid-mutant, kills nothing, and the run completes with its record.
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signum,
        block="mutant",
        ignored=True,
    ) as driver:
        try:
            assert _poll(lambda: bool(_scope_pids(tmp_path)))
            os.kill(driver.pid, signum)
            # Long enough for a handler that kills the scope to have done so.
            time.sleep(0.5)
            scope_alive = all(_is_running(pid) for pid in _scope_pids(tmp_path))
            (tmp_path / "ready.release").write_text("", encoding="utf-8")
            record, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert scope_alive
    # The stand-in passes under the mutation, so the one entry is weakly pinned.
    assert driver.returncode == 1
    assert "stopped by" not in error
    assert record.startswith("### Failability proofs")
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert _run_logs(tmp_path) == ["001-baseline", "001-mutant"]


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_the_first_stop_signal_is_forwarded_to_the_scope_so_pytest_can_tear_down(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signum,
        block="mutant",
        on_stop="teardown",
    ) as driver:
        try:
            assert _poll(lambda: bool(_scope_pids(tmp_path)))
            os.kill(driver.pid, signum)
            _, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert (tmp_path / "ready.teardown").read_text(encoding="utf-8") == signum.name
    assert driver.returncode == 128 + signum
    assert f"stopped by {signum.name}" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_the_scope_is_pytest_itself_so_its_teardown_gets_the_first_stop_once(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    # ``uv run`` stays the parent of what it runs and forwards every stop it gets, so a scope
    # started under it would get the group's stop and then uv's copy, SIGINT 0.2 s later,
    # inside a teardown that takes half a second. The scope is the ``pytest`` the stand-in
    # ``uv`` puts on ``PATH``, started by the run itself, so the teardown gets one stop and
    # finishes.
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signum,
        block="mutant",
        on_stop="teardown",
        through_path=True,
    ) as driver:
        try:
            assert _poll(lambda: bool(_scope_pids(tmp_path)))
            os.kill(driver.pid, signum)
            _, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert (tmp_path / "ready.got").read_text(encoding="utf-8").split() == [signum.name]
    assert (tmp_path / "ready.teardown").read_text(encoding="utf-8") == signum.name
    # The scope is the environment's ``pytest``, and the run itself is its parent.
    launched = (tmp_path / "ready.launched").read_text(encoding="utf-8")
    assert launched == f"{driver.pid} {tmp_path / 'venv' / 'bin' / 'pytest'}"
    assert driver.returncode == 128 + signum
    assert f"stopped by {signum.name}" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_a_repeat_stop_signal_inside_the_grace_window_lets_the_teardown_finish(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    # ``uv run`` forwards a Ctrl-C the terminal already sent the whole foreground group, so
    # one keypress reaches the run twice a fraction of a second apart. The repeat is the
    # same stop: the scope's teardown, which takes longer than the gap, must still finish.
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signum,
        block="mutant",
        on_stop="teardown",
    ) as driver:
        try:
            assert _poll(lambda: bool(_scope_pids(tmp_path)))
            os.kill(driver.pid, signum)
            time.sleep(prove_failability.STOP_REPEAT_GRACE / 5)
            os.kill(driver.pid, signum)
            _, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert (tmp_path / "ready.teardown").read_text(encoding="utf-8") == signum.name
    assert driver.returncode == 128 + signum
    assert f"stopped by {signum.name}" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_a_second_stop_signal_kills_a_scope_that_ignored_the_first(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signum,
        block="mutant",
        on_stop="ignore",
    ) as driver:
        try:
            assert _poll(lambda: bool(_scope_pids(tmp_path)))
            os.kill(driver.pid, signum)
            # Past the window in which a repeat counts as the same stop, and long enough
            # for a scope that honoured the first signal to have ended.
            time.sleep(prove_failability.STOP_REPEAT_GRACE + 0.5)
            waited = driver.poll() is None and all(
                _is_running(pid) for pid in _scope_pids(tmp_path)
            )
            os.kill(driver.pid, signum)
            _, error = driver.communicate(timeout=10)
            scope_ended = _poll(
                lambda: not any(_is_running(pid) for pid in _scope_pids(tmp_path)),
                seconds=5,
            )
        finally:
            _stop_run(driver, tmp_path)

    assert waited
    assert driver.returncode == 128 + signum
    assert f"stopped by {signum.name}" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert scope_ended


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM], ids=["SIGINT", "SIGTERM"])
def test_a_stopped_script_run_ends_by_the_signal_so_its_caller_stops_too(
    fake_repo: Path,
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    # A shell loop runs its next command after an exit of 130, but not after a death by
    # SIGINT; ``main`` still returns ``128 + N`` to an in-process caller.
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signum,
        mode="cli",
        block="mutant",
    ) as driver:
        try:
            assert _poll(lambda: bool(_scope_pids(tmp_path)))
            os.kill(driver.pid, signum)
            _, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert driver.returncode == -signum
    assert f"stopped by {signum.name}" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert _run_logs(tmp_path) == ["001-baseline"]


def test_a_stop_signal_after_the_last_scope_lets_the_run_finish_with_its_own_verdict(
    fake_repo: Path,
    tmp_path: Path,
) -> None:
    # Both signals land inside the only entry's restore, after its last scope: nothing is
    # left to stop, so the run completes and grades. The stand-in passes under the
    # mutation, so the one entry is weakly pinned.
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signal.SIGTERM,
        mode="restore",
    ) as driver:
        try:
            _, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert driver.returncode == 1
    assert "stopped by" not in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert _run_logs(tmp_path) == ["001-baseline", "001-mutant"]


def test_a_restore_that_fails_during_a_stop_is_still_exit_3_with_its_marker(
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The stop cuts the mutant run short and the restore it unwinds through cannot be
    # proved: the tree may hold a mutation, which outranks the stop.
    calls: list[str] = []

    def stopped_run_scope(
        _entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        calls.append("run")
        if len(calls) == 2:
            prove_failability._request_stop(signal.SIGTERM, None)
            prove_failability._raise_if_stopped()
        return prove_failability.RunOutcome((), (), "baseline: stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", stopped_run_scope)
    monkeypatch.setattr(filecmp, "cmp", _never_identical)

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 3
    error = capsys.readouterr().err
    assert "RESTORE FAILED" in error
    assert "stopped by" not in error
    assert (state_directory / prove_failability.RESTORE_FAILED_MARKER_NAME).exists()
    assert (state_directory / prove_failability.ACTIVE_MARKER_NAME).exists()
    assert prove_failability._STOP.signum is None


def test_a_stop_signal_that_lands_while_the_scope_starts_still_ends_the_scope(
    fake_repo: Path,
    tmp_path: Path,
) -> None:
    # The signal arrives after the run checked for one and before it recorded the scope
    # it is starting, so the handler finds no scope to signal; the run must forward the
    # signal to the scope itself rather than wait out a scope that would block for 30 seconds.
    with _signalled_run(
        fake_repo,
        tmp_path,
        _manifest(tmp_path),
        signal.SIGTERM,
        mode="starting",
        block="baseline",
    ) as driver:
        try:
            _, error = driver.communicate(timeout=10)
        finally:
            _stop_run(driver, tmp_path)

    assert driver.returncode == 128 + signal.SIGTERM
    assert "stopped by SIGTERM" in error
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE
    assert _run_logs(tmp_path) == []


@pytest.mark.usefixtures("fake_repo")
def test_main_routes_stop_signals_only_while_it_runs_and_puts_the_old_handlers_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _four_failing_rows(monkeypatch)
    stubbed = prove_failability._run_scope
    during: list[list[object]] = []

    def observing_run_scope(
        entry: prove_failability.ProofEntry,
        capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        during.append([signal.getsignal(signum) for signum in STOP_SIGNALS])
        return stubbed(entry, capture)

    monkeypatch.setattr(prove_failability, "_run_scope", observing_run_scope)
    before = [signal.getsignal(signum) for signum in STOP_SIGNALS]

    code = prove_failability.main(
        [str(_manifest(tmp_path)), "--scratch-root", str(tmp_path / "outside-scratch")],
    )

    assert code == 0
    # Importing the script installed nothing; only a run does, and only while it runs.
    assert prove_failability._request_stop not in before
    assert during == [[prove_failability._request_stop] * len(STOP_SIGNALS)] * 2
    assert [signal.getsignal(signum) for signum in STOP_SIGNALS] == before


@pytest.mark.usefixtures("fake_repo")
def test_a_stop_ends_with_its_run_so_the_next_run_in_the_process_is_not_stopped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The handler is called directly here: delivering a real signal to the test process
    # would end the worker if the handler were missing. The rows above deliver real ones.
    monkeypatch.setattr(
        prove_failability,
        "PYTEST_COMMAND",
        (sys.executable, "-c", "print('1 passed in 0.01s')"),
    )
    restore = prove_failability._restore_and_prove
    stops = [signal.SIGTERM]

    def stopping_restore(target: Path, pristine: Path) -> str:
        if stops:
            prove_failability._request_stop(stops.pop(), None)
        return restore(target, pristine)

    monkeypatch.setattr(prove_failability, "_restore_and_prove", stopping_restore)
    arguments = [str(_multi_manifest(tmp_path, 2)), "--scratch-root", str(tmp_path / "outside")]

    stopped = prove_failability.main(arguments)
    unstopped = prove_failability.main(arguments)

    assert stopped == 128 + signal.SIGTERM
    # Nothing failed under the mutation, so both entries complete and grade weakly pinned.
    assert unstopped == 1
    assert (tmp_path / "repo" / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize("state", ["exited", "reaped"])
def test_killing_a_scope_that_already_ended_raises_nothing(state: str) -> None:
    # A signal can land after the scope exited and before the run reaped it (every
    # member gone: macOS ``killpg`` says EPERM) or after an outside reap (ESRCH). The
    # handler runs between any two bytecodes, so raising there would abort a restore.
    with subprocess.Popen([sys.executable, "-c", ""], start_new_session=True, text=True) as scope:
        if state == "reaped":
            _ = os.waitpid(scope.pid, 0)
        else:
            assert _poll(lambda: not _is_running(scope.pid))
        prove_failability._STOP.scope = scope
        try:
            prove_failability._signal_scope(signal.SIGKILL)
        finally:
            prove_failability._STOP.scope = None


@pytest.mark.usefixtures("fake_repo")
def test_an_only_run_labels_its_report_a_partial_record_at_both_ends_and_in_the_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The fail-open this guards: a `--only 3 --output` block textually identical to a
    # complete run's would let a record covering one boundary of twenty be pasted into
    # a subsection that requires one entry per new boundary, and a reader of the
    # record - who never sees the command line - would have nothing to notice.
    _four_failing_rows(monkeypatch)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--only",
            "2",
            "--output",
            str(output),
        ],
    )

    assert code == 0
    written = output.read_text(encoding="utf-8")
    lines = written.rstrip().split("\n")
    # Directly under the heading, ahead of the procedure prose: the first thing read.
    assert lines[0] == "### Failability proofs"
    assert lines[2].startswith("**PARTIAL RECORD - `--only` NARROWED THIS RUN: 1 of 3 manifest")
    assert "`--only 2`" in lines[2]
    # And on the last line, because a top-only notice is lost when the block is pasted
    # from part-way down.
    assert lines[-1].startswith("**Reminder, PARTIAL RECORD: this block covers 1 of 3 manifest")
    # The entries that went unproved are named, not merely counted.
    assert "- `package/views.py::gate_1`" in written
    assert "- `package/views.py::gate_3`" in written
    # And the `#` column carries the manifest position, so the single row cannot read
    # as entry 1 of 1 even with every line of prose stripped out.
    assert "| 2 | `package/views.py::gate_2` |" in written
    assert "2. `package/views.py::gate_2` - pinned" in written
    assert "PARTIAL RUN: --only selected 1 of 3 manifest entries" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_repo")
def test_a_full_run_says_nothing_about_selection_so_the_partial_notice_stays_meaningful(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Absence of the notice is only evidence if the notice is never noise, so a run
    # that covered the whole manifest emits no selection prose at all.
    _four_failing_rows(monkeypatch)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--output",
            str(output),
        ],
    )

    assert code == 0
    written = output.read_text(encoding="utf-8")
    assert "PARTIAL RECORD" not in written
    assert "did NOT prove" not in written
    assert "manifest entries" not in written
    # Numbering is unchanged for a full run: manifest position and row number agree.
    assert "| 3 | `package/views.py::gate_3` |" in written


@pytest.mark.usefixtures("fake_repo")
def test_only_selectors_that_cover_the_whole_manifest_are_not_a_partial_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Partial is about coverage, not about the flag: a selector set that names every
    # entry leaves no boundary unproved, so labelling it partial would be false.
    _four_failing_rows(monkeypatch)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--only",
            "gate",
            "--output",
            str(output),
        ],
    )

    assert code == 0
    assert "PARTIAL RECORD" not in output.read_text(encoding="utf-8")


@pytest.mark.usefixtures("fake_repo")
def test_only_is_still_allowed_output_unlike_no_baseline_which_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The two flags are not the same fault. --no-baseline omits a field ARTIFACT.md
    # requires, so no annotation can make that report a compliant record. --only emits
    # a truthful record of fewer boundaries - and the mandatory independent
    # re-run of a *subset* is exactly what it is for, and that re-run gets recorded.
    # Refusing --output would push that re-run back to hand-copied stdout, which is
    # where a banner gets dropped. So: labelled, not refused.
    manifest = _multi_manifest(tmp_path)
    scratch = tmp_path / "outside-scratch"
    narrowed = tmp_path / "narrowed.md"
    baseline_less = tmp_path / "baseline-less.md"

    _four_failing_rows(monkeypatch)
    assert (
        prove_failability.main(
            [
                str(manifest),
                "--scratch-root",
                str(scratch),
                "--only",
                "1",
                "--output",
                str(narrowed),
            ],
        )
        == 0
    )

    seen = _four_failing_rows(monkeypatch)
    code = prove_failability.main(
        [
            str(manifest),
            "--scratch-root",
            str(scratch),
            "--only",
            "1",
            "--no-baseline",
            "--output",
            str(baseline_less),
        ],
    )

    written = narrowed.read_text(encoding="utf-8")
    assert written.startswith("### Failability proofs")
    assert "PARTIAL RECORD" in written
    assert code == 1
    assert seen == []
    assert not baseline_less.exists()
    assert "--no-baseline cannot be combined with --output" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_repo")
def test_an_aborted_narrowed_run_keeps_the_partial_record_notice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two independent reasons the record is partial: the restore that stopped the run
    # and the selection that shrank it. The reader needs both, so neither replaces
    # the other.
    _stub_run(monkeypatch)
    monkeypatch.setattr(filecmp, "cmp", _never_identical)
    output = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(_multi_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--only",
            "2",
            "--output",
            str(output),
        ],
    )

    assert code == 3
    written = output.read_text(encoding="utf-8")
    assert "PARTIAL RECORD - `--only` NARROWED THIS RUN: 1 of 3" in written
    assert "RUN ABORTED - A RESTORE COULD NOT BE PROVED" in written


def test_an_entry_with_no_manifest_position_falls_back_to_its_row_number() -> None:
    # ProofEntry can be built by hand (no manifest, so no position); the report must
    # still number the row rather than printing a 0.
    entry = prove_failability.ProofEntry("a", prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
    outcome = prove_failability.RunOutcome(("tests/test_x.py::test_a",), (), "stubbed", 1)

    report = prove_failability.render_report(
        [prove_failability.ProofResult(entry, outcome, "proved", None)],
    )

    assert entry.manifest_position == 0
    assert "| 1 | `a` |" in report


def test_describe_selection_counts_coverage_rather_than_trusting_the_selector_list() -> None:
    entries = [
        prove_failability.ProofEntry(name, prove_failability.REPO_ROOT, "x", "y", "m", ("s",))
        for name in ("a", "b", "c")
    ]

    partial = prove_failability.describe_selection(entries, entries[:1], ["1"])
    whole = prove_failability.describe_selection(entries, entries, [])

    assert partial.is_partial is True
    assert partial.selected_total == 1
    assert partial.omitted_labels == ("b", "c")
    assert partial.selector_text == "--only 1"
    assert whole.is_partial is False
    assert whole.selected_total == 3
    assert whole.selector_text == "no selector"


@pytest.mark.usefixtures("fake_repo")
def test_the_output_flag_writes_the_report_to_disk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    output = tmp_path / "proofs.md"

    prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--output",
            str(output),
        ],
    )

    assert output.read_text(encoding="utf-8").startswith("### Failability proofs")


# --- declared failing sets --------------------------------------------------------------


COUNT_ROW = "tests/test_x.py::test_query_count_is_flat_across_row_counts"


def _run_with_expectation(
    tmp_path: Path,
    scratch_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    expect_failing: list[str],
    *,
    failed: tuple[str, ...] = (),
    errored: tuple[str, ...] = (),
    code: int = 1,
    baseline_failed: tuple[str, ...] = (),
) -> prove_failability.ProofResult:
    _stub_run(
        monkeypatch,
        failed=failed,
        errored=errored,
        code=code,
        baseline_failed=baseline_failed,
    )
    entry = _single_entry(tmp_path, expect_failing=expect_failing)
    return prove_failability.execute_entry(entry, scratch_root)


@pytest.mark.usefixtures("fake_repo")
def test_a_declared_single_row_is_a_complete_proof_not_a_weak_pin(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # One query-count function asserting two cardinalities fails as one row; the row
    # count would grade it WEAKLY PINNED although it is exactly the row the proof names.
    result = _run_with_expectation(
        tmp_path,
        scratch_root,
        monkeypatch,
        [COUNT_ROW],
        failed=(COUNT_ROW,),
    )

    assert result.failed_count == 1
    assert result.is_weakly_pinned is False
    assert result.is_inside_rerun_floor is False
    assert result.expectation is not None
    assert result.expectation.is_met is True
    verdict = prove_failability._verdict(result)
    assert "WEAKLY PINNED" not in verdict
    assert "exactly the declared `expect_failing`" in verdict
    report = prove_failability.render_report([result])
    assert "why 0" not in report
    assert f"declared `expect_failing`: `{COUNT_ROW}`" in report
    assert prove_failability._exit_code([result]) == 0


@pytest.mark.usefixtures("fake_repo")
def test_the_same_single_row_without_a_declaration_keeps_the_row_count_grading(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=(COUNT_ROW,))

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.entry.expect_failing is None
    assert result.expectation is None
    assert result.is_weakly_pinned is True
    assert prove_failability._exit_code([result]) == 1


@pytest.mark.usefixtures("fake_repo")
def test_a_declared_set_names_missing_and_undeclared_rows(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_with_expectation(
        tmp_path,
        scratch_root,
        monkeypatch,
        [COUNT_ROW],
        failed=("tests/test_x.py::test_other",),
    )

    assert result.expectation is not None
    assert result.expectation.missing == (COUNT_ROW,)
    assert result.expectation.unexpected == ("tests/test_x.py::test_other",)
    assert result.is_expectation_unmet is True
    verdict = prove_failability._verdict(result)
    assert "EXPECTATION NOT MET" in verdict
    assert f"declared but not failing: `{COUNT_ROW}`" in verdict
    assert "failing but not declared: `tests/test_x.py::test_other`" in verdict
    assert prove_failability._exit_code([result]) == 1


@pytest.mark.usefixtures("fake_repo")
def test_an_empty_declaration_is_a_behaviour_preservation_proof(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preserved = _run_with_expectation(tmp_path, scratch_root, monkeypatch, [], code=0)

    assert preserved.failed_count == 0
    assert preserved.is_weakly_pinned is False
    assert "behaviour preserved" in prove_failability._verdict(preserved)
    assert "why 0" not in prove_failability.render_report([preserved])
    assert prove_failability._exit_code([preserved]) == 0

    broken = _run_with_expectation(
        tmp_path,
        scratch_root,
        monkeypatch,
        [],
        failed=("tests/test_x.py::test_a",),
    )

    assert broken.expectation is not None
    assert broken.expectation.unexpected == ("tests/test_x.py::test_a",)
    assert prove_failability._exit_code([broken]) == 1


@pytest.mark.usefixtures("fake_repo")
def test_patterns_match_globs_and_parametrized_ids_literally(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ``[a-b]`` is a character class to fnmatch, so equality is tried first.
    parametrized = "tests/test_x.py::test_count[a-b]"
    result = _run_with_expectation(
        tmp_path,
        scratch_root,
        monkeypatch,
        [parametrized, "tests/test_y.py::test_alias_*"],
        failed=(
            parametrized,
            "tests/test_y.py::test_alias_one",
            "tests/test_y.py::test_alias_two",
        ),
    )

    assert result.expectation is not None
    assert result.expectation.is_met is True


@pytest.mark.parametrize(
    ("pattern", "node_id", "expected"),
    [
        pytest.param(
            "tests/test_x.py::test_x[*]",
            "tests/test_x.py::test_x[a-b]",
            True,
            id="any-row-matches-a-dashed-id",
        ),
        pytest.param(
            "tests/test_x.py::test_x[*]",
            "tests/test_x.py::test_x[1]",
            True,
            id="any-row-matches-a-numeric-id",
        ),
        pytest.param(
            "tests/test_x.py::test_x[*]",
            "tests/test_x.py::test_xy[1]",
            False,
            id="any-row-skips-another-test",
        ),
        pytest.param(
            "tests/test_x.py::test_x[a-*]",
            "tests/test_x.py::test_x[a-b]",
            True,
            id="id-prefix-matches",
        ),
        pytest.param(
            "tests/test_x.py::test_x[a-*]",
            "tests/test_x.py::test_x[b-a]",
            False,
            id="id-prefix-skips-another-prefix",
        ),
        pytest.param(
            "tests/test_x.py::test_x[a[*]",
            "tests/test_x.py::test_x[a[b]]",
            True,
            id="every-bracket-is-literal",
        ),
        pytest.param(
            "tests/test_x.py::test_[ab]",
            "tests/test_x.py::test_a",
            True,
            id="character-class-still-matches",
        ),
    ],
)
def test_a_pattern_reads_brackets_literally_or_as_a_character_class(
    pattern: str,
    node_id: str,
    *,
    expected: bool,
) -> None:
    assert prove_failability._pattern_matches(pattern, node_id) is expected


@pytest.mark.usefixtures("fake_repo")
def test_a_glob_over_a_parametrized_id_names_every_row_of_the_test(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_with_expectation(
        tmp_path,
        scratch_root,
        monkeypatch,
        ["tests/test_x.py::test_count[*]"],
        failed=("tests/test_x.py::test_count[a-b]", "tests/test_x.py::test_count[1]"),
    )

    assert result.expectation is not None
    assert result.expectation.is_met is True


@pytest.mark.usefixtures("fake_repo")
def test_a_row_isolation_node_id_never_reads_a_parametrized_glob(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=("tests/test_x.py::test_count[a-b]",))
    entry = _single_entry(tmp_path, isolates="tests/test_x.py::test_count[*]")

    result = prove_failability.execute_entry(entry, scratch_root)

    assert result.is_expectation_unmet is True


@pytest.mark.usefixtures("fake_repo")
def test_a_declared_row_already_failing_before_the_mutation_is_named_as_such(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_with_expectation(
        tmp_path,
        scratch_root,
        monkeypatch,
        [COUNT_ROW],
        baseline_failed=(COUNT_ROW,),
    )

    assert result.expectation is not None
    assert result.expectation.missing_but_failing_at_baseline == (COUNT_ROW,)
    assert "already failing before the mutation" in prove_failability._verdict(result)


@pytest.mark.usefixtures("fake_repo")
def test_a_declaration_does_not_rescue_an_invalid_count(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_with_expectation(
        tmp_path,
        scratch_root,
        monkeypatch,
        [],
        errored=("tests/test_y.py",),
    )

    assert result.invalid_count_reason is not None
    assert result.is_expectation_unmet is False
    assert "behaviour preserved" not in prove_failability._verdict(result)
    assert prove_failability._exit_code([result]) == 1


@pytest.mark.parametrize(
    "value",
    [
        "tests/test_x.py::test_a",
        [""],
        [7],
        {"a": 1},
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_a_declaration_must_be_a_list_of_node_ids(tmp_path: Path, value: object) -> None:
    with pytest.raises(prove_failability.ManifestError, match="'expect_failing' must be a list"):
        prove_failability.load_manifest(_manifest(tmp_path, expect_failing=value))


# --- row-isolation proofs ---------------------------------------------------------------


OTHER_ROW = "tests/test_x.py::test_other"


def _run_isolating(
    tmp_path: Path,
    scratch_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    failed: tuple[str, ...],
    baseline_failed: tuple[str, ...] = (),
) -> prove_failability.ProofResult:
    _stub_run(monkeypatch, failed=failed, baseline_failed=baseline_failed)
    entry = _single_entry(tmp_path, isolates=COUNT_ROW)
    return prove_failability.execute_entry(entry, scratch_root)


@pytest.mark.usefixtures("fake_repo")
def test_a_row_isolation_proof_failing_only_its_declared_row_is_row_isolated(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_isolating(tmp_path, scratch_root, monkeypatch, failed=(COUNT_ROW,))

    assert result.entry.isolates == COUNT_ROW
    assert result.is_weakly_pinned is False
    assert result.is_inside_rerun_floor is False
    verdict = prove_failability._verdict(result)
    assert verdict == f"row isolated: exactly the declared row `{COUNT_ROW}` failed, and no other"
    report = prove_failability.render_report([result])
    assert "WEAKLY PINNED" not in report
    assert "why 0" not in report
    assert f"declared `isolates`: `{COUNT_ROW}`" in report
    assert prove_failability._exit_code([result]) == 0


@pytest.mark.usefixtures("fake_repo")
def test_a_row_isolation_proof_names_every_extra_failing_row(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_isolating(
        tmp_path,
        scratch_root,
        monkeypatch,
        failed=(COUNT_ROW, OTHER_ROW),
    )

    assert result.is_expectation_unmet is True
    verdict = prove_failability._verdict(result)
    assert verdict == (
        f"**ROW ISOLATION NOT MET - revision-needed** (extra failing rows: `{OTHER_ROW}`)"
    )
    assert prove_failability._exit_code([result]) == 1


@pytest.mark.usefixtures("fake_repo")
def test_a_row_isolation_proof_whose_declared_row_passes_is_not_met(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passing = _run_isolating(tmp_path, scratch_root, monkeypatch, failed=())

    assert prove_failability._verdict(passing) == (
        f"**ROW ISOLATION NOT MET - revision-needed** (declared row not failing: `{COUNT_ROW}`)"
    )
    assert "why 0" not in prove_failability.render_report([passing])
    assert prove_failability._exit_code([passing]) == 1

    elsewhere = _run_isolating(
        tmp_path,
        scratch_root,
        monkeypatch,
        failed=(OTHER_ROW,),
        baseline_failed=(COUNT_ROW,),
    )

    assert prove_failability._verdict(elsewhere) == (
        f"**ROW ISOLATION NOT MET - revision-needed** (declared row not failing: `{COUNT_ROW}`; "
        f"it was already failing before the mutation; extra failing rows: `{OTHER_ROW}`)"
    )


@pytest.mark.usefixtures("fake_repo")
def test_a_row_isolation_node_id_is_compared_by_equality_not_as_a_glob(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=("tests/test_x.py::test_alias_one",))
    entry = _single_entry(tmp_path, isolates="tests/test_x.py::test_alias_*")

    result = prove_failability.execute_entry(entry, scratch_root)

    assert result.is_expectation_unmet is True


@pytest.mark.usefixtures("fake_repo")
def test_a_boundary_proof_failing_one_row_is_still_weakly_pinned(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=(COUNT_ROW,))

    result = prove_failability.execute_entry(_single_entry(tmp_path), scratch_root)

    assert result.entry.isolates is None
    assert prove_failability._verdict(result) == (
        "**WEAKLY PINNED - revision-needed**; inside Worker-3's mandatory re-run floor (<= 3 rows)"
    )
    assert prove_failability._exit_code([result]) == 1


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"isolates": ["tests/test_x.py::test_a"]}, "'isolates' must be one non-empty node id"),
        ({"isolates": ""}, "'isolates' must be one non-empty node id"),
        ({"isolates": COUNT_ROW, "expect_failing": [COUNT_ROW]}, "give either 'isolates'"),
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_an_isolates_declaration_must_be_one_node_id_without_expect_failing(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(prove_failability.ManifestError, match=message):
        prove_failability.load_manifest(_manifest(tmp_path, **overrides))


# --- several sites mutated together ---------------------------------------------------


OTHER_SOURCE = "def other(value):\n    return value + 1\n"


def _sites_manifest(
    tmp_path: Path,
    sites: object,
    **overrides: object,
) -> prove_failability.ProofEntry:
    entry: dict[str, object] = {
        "label": "package/views.py::gate",
        "sites": sites,
        "scope": ["tests/test_x.py"],
    }
    entry.update(overrides)
    path = tmp_path / "sites.json"
    path.write_text(json.dumps({"proofs": [entry]}), encoding="utf-8")
    return prove_failability.load_manifest(path)[0][0]


@pytest.fixture
def two_files(fake_repo: Path) -> tuple[Path, Path]:
    other = fake_repo / "package" / "other.py"
    other.write_text(OTHER_SOURCE, encoding="utf-8")
    return fake_repo / "package" / "views.py", other


def _two_sites() -> list[dict[str, str]]:
    return [
        {"target": "package/views.py", "anchor": ANCHOR, "replacement": "    pass"},
        {"target": "package/other.py", "anchor": "value + 1", "replacement": "value"},
    ]


def test_every_site_is_live_during_the_mutant_run_and_every_file_is_restored(
    two_files: tuple[Path, Path],
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    views, other = two_files
    seen: list[tuple[str, str]] = []

    def fake_run_scope(
        _entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        seen.append((views.read_text(encoding="utf-8"), other.read_text(encoding="utf-8")))
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    entry = _sites_manifest(tmp_path, _two_sites())

    result = prove_failability.execute_entry(entry, scratch_root)

    assert seen[0] == (SOURCE, OTHER_SOURCE)
    assert seen[1] == ("def gate(value):\n    pass\n    return value\n", OTHER_SOURCE[:-5] + "\n")
    assert views.read_text(encoding="utf-8") == SOURCE
    assert other.read_text(encoding="utf-8") == OTHER_SOURCE
    assert [record.relative_target for record in result.files] == [
        "package/views.py",
        "package/other.py",
    ]
    for record, text in zip(result.files, (SOURCE, OTHER_SOURCE), strict=True):
        blob = prove_failability.git_blob_id(text.encode("utf-8"))
        assert record.blob_before == record.blob_after == blob
        assert record.blob_mutated != blob
        assert record.diff.startswith(f"--- a/{record.relative_target}")
    assert result.restore_proof.count("filecmp.cmp(shallow=False) True") == 2
    assert entry.relative_targets == ("package/views.py", "package/other.py")
    report = prove_failability.render_report([result])
    assert "| `package/views.py`, `package/other.py` |" in report
    assert "```diff" in report


def test_one_unprovable_restore_still_restores_every_other_site(
    two_files: tuple[Path, Path],
    scratch_root: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    views, other = two_files
    _stub_run(monkeypatch)
    real_restore = prove_failability._restore_and_prove

    def restore(target: Path, pristine: Path) -> str:
        if target == views:
            raise prove_failability.RestoreProofError(f"{target} could not be restored")
        return real_restore(target, pristine)

    monkeypatch.setattr(prove_failability, "_restore_and_prove", restore)

    with pytest.raises(prove_failability.RestoreProofError):
        prove_failability.execute_entry(_sites_manifest(tmp_path, _two_sites()), scratch_root)

    assert other.read_text(encoding="utf-8") == OTHER_SOURCE
    marker = _json_object(
        (state_directory / prove_failability.RESTORE_FAILED_MARKER_NAME).read_text(
            encoding="utf-8",
        ),
    )
    assert marker["mutated_file"] == str(views)
    assert [json_at(item, "mutated_file") for item in json_list(marker, "files")] == [str(views)]
    active = _json_object(
        (state_directory / prove_failability.ACTIVE_MARKER_NAME).read_text(encoding="utf-8"),
    )
    assert [json_at(item, "mutated_file") for item in json_list(active, "files")] == [
        str(views),
        str(other),
    ]


def test_a_site_that_does_not_match_names_itself_and_nothing_is_written(
    two_files: tuple[Path, Path],
    scratch_root: Path,
    state_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    views, _ = two_files
    seen = _stub_run(monkeypatch)
    sites = _two_sites()
    sites[1]["anchor"] = "not in the file"

    result = prove_failability.execute_entry(_sites_manifest(tmp_path, sites), scratch_root)

    assert seen == []
    assert result.failure is not None
    assert result.failure.startswith("site 2 (`package/other.py`): anchor matched 0 times")
    assert views.read_text(encoding="utf-8") == SOURCE
    assert not state_directory.exists()


def test_two_anchor_sites_on_one_file_apply_in_order(
    fake_repo: Path,
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    views = fake_repo / "package" / "views.py"
    seen: list[str] = []

    def fake_run_scope(
        _entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        seen.append(views.read_text(encoding="utf-8"))
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    sites = [
        {"target": "package/views.py", "anchor": ANCHOR, "replacement": "    pass"},
        {"target": "package/views.py", "anchor": "return value", "delete": True},
    ]

    result = prove_failability.execute_entry(_sites_manifest(tmp_path, sites), scratch_root)

    assert seen[1] == "def gate(value):\n    pass\n    \n"
    assert len(result.files) == 1
    assert views.read_text(encoding="utf-8") == SOURCE


@pytest.mark.parametrize(
    ("sites", "overrides", "expected"),
    [
        ([], {}, "'sites' must be a non-empty list"),
        (["x"], {}, "each site must be an object"),
        ([{"target": "package/views.py", "ancor": ANCHOR}], {}, r"unknown key\(s\) \['ancor'\]"),
        (
            [{"target": "package/views.py", "anchor": ANCHOR, "replacement": "x"}],
            {"target": "package/views.py"},
            "carries no top-level",
        ),
        (
            [
                {
                    "target": "package/views.py",
                    "anchor": ANCHOR,
                    "pre_image": "x",
                    "replacement": "",
                },
            ],
            {},
            "exactly one of",
        ),
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_malformed_sites_are_refused(
    tmp_path: Path,
    sites: object,
    overrides: dict[str, object],
    expected: str,
) -> None:
    with pytest.raises(prove_failability.ManifestError, match=expected):
        _sites_manifest(tmp_path, sites, **overrides)


@pytest.mark.usefixtures("fake_repo")
def test_a_pre_image_site_may_not_share_its_target(tmp_path: Path) -> None:
    image = tmp_path / "views.pre"
    image.write_text("x = 1\n", encoding="utf-8")
    sites = [
        {"target": "package/views.py", "pre_image": str(image)},
        {"target": "package/views.py", "anchor": ANCHOR, "replacement": "    pass"},
    ]

    with pytest.raises(prove_failability.ManifestError, match="give that file one site"):
        _sites_manifest(tmp_path, sites)


@pytest.mark.usefixtures("two_files")
def test_a_multi_site_label_may_name_any_site_and_no_other_file(
    tmp_path: Path,
) -> None:
    assert _sites_manifest(tmp_path, _two_sites(), label="package/other.py::other").label == (
        "package/other.py::other"
    )
    with pytest.raises(prove_failability.ManifestError, match="not the mutation target of any"):
        _sites_manifest(tmp_path, _two_sites(), label="package/third.py::gate")


# --- revert-style inputs ----------------------------------------------------------------


PRE_IMAGE = "def gate(value):\n    return value\n"


def test_a_pre_image_replaces_the_file_wholesale_and_is_restored(
    fake_repo: Path,
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    views = fake_repo / "package" / "views.py"
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "views.pre").write_text(PRE_IMAGE, encoding="utf-8")
    seen: list[str] = []

    def fake_run_scope(
        _entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        seen.append(views.read_text(encoding="utf-8"))
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    manifest = tmp_path / "inputs" / "m.json"
    # A relative pre-image path resolves against the manifest's directory.
    manifest.write_text(
        json.dumps(
            {
                "proofs": [
                    {
                        "label": "package/views.py::gate",
                        "target": "package/views.py",
                        "pre_image": "views.pre",
                        "expect_failing": [],
                        "scope": ["tests/test_x.py"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    entry = prove_failability.load_manifest(manifest)[0][0]

    result = prove_failability.execute_entry(entry, scratch_root)

    assert seen == [SOURCE, PRE_IMAGE]
    assert views.read_text(encoding="utf-8") == SOURCE
    assert result.files[0].blob_mutated == prove_failability.git_blob_id(PRE_IMAGE.encode())
    assert "replaced wholesale by the pre-image" in entry.mutation
    assert "behaviour preserved" in prove_failability._verdict(result)


@pytest.mark.usefixtures("fake_repo")
def test_a_pre_image_identical_to_the_file_is_refused_before_anything_is_written(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _stub_run(monkeypatch)
    image = tmp_path / "same.pre"
    image.write_text(SOURCE, encoding="utf-8")
    manifest = tmp_path / "m.json"
    manifest.write_text(
        json.dumps(
            {
                "proofs": [
                    {
                        "label": "gate",
                        "target": "package/views.py",
                        "pre_image": str(image),
                        "scope": ["tests/test_x.py"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    result = prove_failability.execute_entry(
        prove_failability.load_manifest(manifest)[0][0],
        scratch_root,
    )

    assert seen == []
    assert result.failure is not None
    assert "would mutate nothing" in result.failure


def _patch_file(
    tmp_path: Path,
    pre: str,
    post: str,
    relative: str = "package/views.py",
    name: str = "item.diff",
) -> Path:
    """Write the diff a caller saves from ``git diff <base> -- <path>`` (pre -> post)."""
    diff = "".join(
        difflib.unified_diff(
            pre.splitlines(keepends=True),
            post.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        ),
    )
    path = tmp_path / name
    path.write_text(f"diff --git a/{relative} b/{relative}\nindex 1111111..2222222 100644\n{diff}")
    return path


def _reverse_patch_entry(
    tmp_path: Path,
    patch: Path,
    **fields: object,
) -> prove_failability.ProofEntry:
    entry: dict[str, object] = {
        "label": "gate",
        "reverse_patch": str(patch),
        "scope": ["tests/test_x.py"],
    }
    entry.update(fields)
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"proofs": [entry]}), encoding="utf-8")
    return prove_failability.load_manifest(manifest)[0][0]


def test_a_reverse_patch_restores_the_pre_image_while_the_scope_runs(
    fake_repo: Path,
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    views = fake_repo / "package" / "views.py"
    patch = _patch_file(tmp_path, PRE_IMAGE, SOURCE)
    seen: list[str] = []

    def fake_run_scope(
        _entry: prove_failability.ProofEntry,
        _capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        seen.append(views.read_text(encoding="utf-8"))
        return prove_failability.RunOutcome((), (), "stubbed", 0)

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)

    for fields in ({}, {"target": "package/views.py"}):
        seen.clear()
        entry = _reverse_patch_entry(tmp_path, patch, **fields)
        result = prove_failability.execute_entry(entry, scratch_root)

        assert seen == [SOURCE, PRE_IMAGE]
        assert views.read_text(encoding="utf-8") == SOURCE
        assert result.files[0].blob_after == prove_failability.git_blob_id(SOURCE.encode())
        assert entry.mutation_sites[0].kind == prove_failability.REVERSE_PATCH_KIND


@pytest.mark.usefixtures("two_files")
def test_a_reverse_patch_spanning_two_files_becomes_two_sites(
    tmp_path: Path,
) -> None:
    views_patch = _patch_file(tmp_path, PRE_IMAGE, SOURCE).read_text()
    other_patch = _patch_file(tmp_path, "x\n", OTHER_SOURCE, relative="package/other.py")
    both = tmp_path / "both.diff"
    both.write_text(views_patch + other_patch.read_text())

    entry = _reverse_patch_entry(tmp_path, both)

    assert entry.relative_targets == ("package/views.py", "package/other.py")
    only_other = _reverse_patch_entry(tmp_path, both, target="package/other.py")
    assert only_other.relative_targets == ("package/other.py",)


def test_a_reverse_patch_whose_post_image_is_absent_mutates_nothing(
    fake_repo: Path,
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _stub_run(monkeypatch)
    patch = _patch_file(tmp_path, PRE_IMAGE, "def gate(value):\n    return value * 2\n")

    result = prove_failability.execute_entry(_reverse_patch_entry(tmp_path, patch), scratch_root)

    assert seen == []
    assert result.failure is not None
    assert "hunk 1 for package/views.py does not apply" in result.failure
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


def test_a_repeated_post_image_is_located_by_the_hunk_header_alone() -> None:
    text = "a\nx\nb\na\nx\nb\n"
    hunk = prove_failability.PatchHunk(
        new_start=4,
        old_lines=(("a", True), ("y", True), ("b", True)),
        new_lines=(("a", True), ("x", True), ("b", True)),
    )

    assert prove_failability._reverse_hunks(text, [hunk], "f.py") == "a\nx\nb\na\ny\nb\n"
    elsewhere = dataclasses.replace(hunk, new_start=1)
    assert prove_failability._reverse_hunks(text, [elsewhere], "f.py") == "a\ny\nb\na\nx\nb\n"
    nowhere = dataclasses.replace(hunk, new_start=3)
    with pytest.raises(prove_failability.SiteError, match="occurs 2 time"):
        prove_failability._reverse_hunks(text, [nowhere], "f.py")


def test_a_missing_final_newline_is_reverted_byte_for_byte() -> None:
    diff = (
        "--- a/f.py\n+++ b/f.py\n@@ -1,2 +1,2 @@\n a\n-b\n\\ No newline at end of file\n"
        "+c\n\\ No newline at end of file\n"
    )
    sections = prove_failability._parse_unified_diff(diff, "test")

    assert prove_failability._reverse_hunks("a\nc", sections["f.py"], "f.py") == "a\nb"


@pytest.mark.parametrize(
    ("diff", "expected"),
    [
        ("--- /dev/null\n+++ b/package/views.py\n@@ -0,0 +1 @@\n+x\n", "creates or deletes"),
        ("not a diff\n", "not a unified diff"),
        ("--- a/package/views.py\n+++ b/package/views.py\n@@ -1,2 +1,2 @@\n a\n", "truncated"),
        ("--- a/package/views.py\n+++ b/package/views.py\n@@ -1 +1 @@\n?x\n", "malformed"),
        ("--- a/package/views.py\n+++ b/package/views.py\nBinary files differ\n", "no hunk"),
    ],
)
@pytest.mark.usefixtures("fake_repo")
def test_a_patch_the_applier_cannot_revert_is_refused(
    tmp_path: Path,
    diff: str,
    expected: str,
) -> None:
    patch = tmp_path / "bad.diff"
    patch.write_text(diff)

    with pytest.raises(prove_failability.ManifestError, match=expected):
        _reverse_patch_entry(tmp_path, patch)


@pytest.mark.usefixtures("two_files")
def test_a_patch_without_a_section_for_the_target_is_refused(
    tmp_path: Path,
) -> None:
    patch = _patch_file(tmp_path, PRE_IMAGE, SOURCE)

    with pytest.raises(
        prove_failability.ManifestError,
        match=r"has no hunk for 'package/other\.py'",
    ):
        _reverse_patch_entry(tmp_path, patch, target="package/other.py")


# --- provenance observed inside pytest -------------------------------------------------


def _load_probe() -> types.ModuleType:
    probe = types.ModuleType(prove_failability.PROBE_MODULE_NAME)
    exec(compile(prove_failability.PROBE_SOURCE, "probe", "exec"), probe.__dict__)  # noqa: S102 - runs the script's own probe source under test
    return probe


def test_the_probe_records_package_file_database_names_and_crash_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "probe.jsonl"
    monkeypatch.setenv(prove_failability.PROBE_OUTPUT_ENV, str(output))
    monkeypatch.setenv(prove_failability.PROBE_PACKAGE_ENV, "django_strawberry_framework")
    probe = _load_probe()
    config = types.SimpleNamespace(rootpath=tmp_path)
    crash = types.SimpleNamespace(path="/ws/tests/test_x.py", lineno=9, message="assert 6 == 1")
    report = types.SimpleNamespace(
        failed=True,
        when="call",
        nodeid=COUNT_ROW,
        longrepr=types.SimpleNamespace(reprcrash=crash),
    )

    _hook(probe, "pytest_configure")(config)
    _hook(probe, "pytest_runtest_logreport")(report)
    _hook(probe, "pytest_collectreport")(
        types.SimpleNamespace(failed=True, nodeid="tests/test_y.py", longrepr="ImportError: x"),
    )
    _hook(probe, "pytest_sessionfinish")(types.SimpleNamespace(config=config))
    crash_lines, provenance = prove_failability._read_probe(output)

    assert dict(crash_lines) == {
        COUNT_ROW: "/ws/tests/test_x.py:9: assert 6 == 1",
        "tests/test_y.py": "ImportError: x",
    }

    (record,) = provenance
    assert record.role == "controller"
    assert record.package_file == django_strawberry_framework.__file__
    assert record.package_imported_by_run is True
    databases = read_attr(settings, "DATABASES")
    assert is_object_dict(databases)
    assert dict(record.databases) == {
        alias: str(json_at(options, "NAME")) for alias, options in databases.items()
    }


def _run_once_before_reading(
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
    action: Callable[[], object],
) -> None:
    """Run ``action`` once, right before the first ``read_text`` of ``target`` reads it."""
    real_read_text = Path.read_text
    pending = [action]

    def _read_text(path: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if path == target and pending:
            pending.pop()()
        return real_read_text(path, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", _read_text)


@pytest.mark.usefixtures("fake_repo")
def test_a_probe_plugin_the_purge_removes_as_it_is_read_is_written_again(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # ``workspace.py prove`` puts the scratch root in the temporary directory the OS cleans:
    # the read is the existence check, so a plugin gone by then is written, never a crash.
    entry = _single_entry(tmp_path)
    first = prove_failability._new_capture(scratch_root, entry, "baseline")
    plugin = first.probe_directory / f"{prove_failability.PROBE_MODULE_NAME}.py"
    _run_once_before_reading(monkeypatch, plugin, plugin.unlink)

    again = prove_failability._new_capture(scratch_root, entry, "mutant")

    assert again.probe_directory == first.probe_directory
    assert plugin.read_text(encoding="utf-8") == prove_failability.PROBE_SOURCE


def test_probe_output_the_purge_removes_as_it_is_read_reads_as_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "probe.jsonl"
    _ = output.write_text(
        json.dumps({"kind": "failed", "nodeid": COUNT_ROW, "crash": "t.py:9: boom"}) + "\n",
        encoding="utf-8",
    )
    _run_once_before_reading(monkeypatch, output, output.unlink)

    assert prove_failability._read_probe(output) == ((), ())


def test_an_xdist_worker_reports_provenance_but_leaves_rows_to_the_controller(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "probe.jsonl"
    monkeypatch.setenv(prove_failability.PROBE_OUTPUT_ENV, str(output))
    monkeypatch.setenv(prove_failability.PROBE_PACKAGE_ENV, "json")
    probe = _load_probe()
    config = types.SimpleNamespace(rootpath=tmp_path, workerinput={"workerid": "gw0"})
    report = types.SimpleNamespace(failed=True, when="call", nodeid=COUNT_ROW, longrepr="boom")

    _hook(probe, "pytest_configure")(config)
    _hook(probe, "pytest_runtest_logreport")(report)
    _hook(probe, "pytest_sessionfinish")(types.SimpleNamespace(config=config))
    crash_lines, provenance = prove_failability._read_probe(output)

    assert crash_lines == ()
    assert provenance[0].role == "worker"


# Stands in for ``uv run pytest`` in a real scope run: it reports one failing row on
# stdout, as ``-rfE`` does, writes the probe records the plugin would, and echoes the
# argv and ``PYTHONPATH`` it was given on stderr, which the run keeps in its log.
_REPORTING_SCOPE = f"""
import json
import os
import sys
from pathlib import Path

Path(os.environ["{prove_failability.PROBE_OUTPUT_ENV}"]).write_text(
    json.dumps({{"kind": "failed", "nodeid": "{COUNT_ROW}", "crash": "t.py:9: assert 6 == 1"}})
    + "\\n"
    + json.dumps({{"kind": "provenance", "role": "controller", "package_file": "/x.py"}})
    + "\\n",
    encoding="utf-8",
)
print("=========================== short test summary info ============================")
print("FAILED {COUNT_ROW} - assert 6 == 1")
print("1 failed in 0.1s")
print(json.dumps({{"argv": sys.argv[1:], "pythonpath": os.environ["PYTHONPATH"]}}), file=sys.stderr)
sys.exit(1)
"""


@pytest.mark.usefixtures("fake_repo")
def test_a_scope_run_loads_the_probe_and_keeps_its_raw_output(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = _single_entry(tmp_path)
    capture = prove_failability._new_capture(scratch_root, entry, "mutant")
    monkeypatch.setattr(
        prove_failability,
        "PYTEST_COMMAND",
        (sys.executable, "-c", _REPORTING_SCOPE),
    )

    outcome = prove_failability._run_scope(entry, capture)

    log = capture.log_path.read_text(encoding="utf-8")
    seen = _json_object(log.rsplit("--- stderr ---\n", 1)[1])
    assert json_at(seen, "argv") == ["-p", prove_failability.PROBE_MODULE_NAME, "tests/test_x.py"]
    assert _text(seen, "pythonpath").split(os.pathsep)[0] == str(capture.probe_directory)
    assert (capture.probe_directory / "prove_failability_probe.py").read_text(
        encoding="utf-8",
    ) == prove_failability.PROBE_SOURCE
    assert outcome.return_code == 1
    assert outcome.failed_node_ids == (COUNT_ROW,)
    assert outcome.crash_line(COUNT_ROW) == "t.py:9: assert 6 == 1"
    assert outcome.provenance[0].package_file == "/x.py"
    assert outcome.log_path == str(capture.log_path)
    assert log.startswith("argv: ")
    assert f"FAILED {COUNT_ROW}" in log


def test_a_run_that_imported_another_tree_is_an_invalid_count(fake_repo: Path) -> None:
    entry = prove_failability.ProofEntry("a", fake_repo, "x", "y", "m", ("s",))
    inside = _provenance(str(fake_repo / "django_strawberry_framework" / "__init__.py"))
    outside = _provenance("/shared/checkout/django_strawberry_framework/__init__.py")
    failing = (
        COUNT_ROW,
        "tests/test_x.py::b",
        "tests/test_x.py::c",
        "tests/test_x.py::d",
    )

    outcome = prove_failability.RunOutcome(failing, (), "4 failed", 1, provenance=(inside,))
    honest = prove_failability.ProofResult(entry, outcome, "proved", None)
    foreign = dataclasses.replace(
        honest,
        outcome=dataclasses.replace(outcome, provenance=(inside, outside)),
    )

    assert honest.invalid_count_reason is None
    assert foreign.invalid_count_reason is not None
    assert "outside the tree under proof" in foreign.invalid_count_reason
    assert "/shared/checkout/" in foreign.invalid_count_reason
    # ``--workspace`` additionally refuses a run the probe observed nothing about.
    unobserved = dataclasses.replace(
        honest,
        outcome=dataclasses.replace(outcome, provenance=()),
        provenance_required=True,
    )
    assert unobserved.invalid_count_reason is not None
    assert "reported no package `__file__`" in unobserved.invalid_count_reason
    assert dataclasses.replace(unobserved, provenance_required=False).invalid_count_reason is None


def test_the_git_blob_id_is_the_one_git_hash_object_prints() -> None:
    # ``printf 'hello\n' | git hash-object --stdin``
    assert prove_failability.git_blob_id(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


# --- the machine-readable record and the workspace guard -------------------------------


LONG_ANCHOR = ["    if value is None:", '        raise ValueError("no")']


def test_the_json_record_carries_the_whole_mutation_blob_ids_and_provenance(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    long_line = "    return value  # " + "x" * 150
    target = fake_repo / "package" / "views.py"
    target.write_text(SOURCE.replace("    return value", long_line), encoding="utf-8")
    calls: list[prove_failability.RunCapture | None] = []

    def fake_run_scope(
        _entry: prove_failability.ProofEntry,
        capture: prove_failability.RunCapture | None = None,
    ) -> prove_failability.RunOutcome:
        calls.append(capture)
        if len(calls) == 1:
            return prove_failability.RunOutcome((), (), "3 passed", 0, wall_seconds=1.0)
        return prove_failability.RunOutcome(
            (COUNT_ROW,),
            (),
            "1 failed, 2 passed",
            1,
            crash_lines=((COUNT_ROW, "t.py:9: assert 6 == 1\n +  where 6 = len(queries)"),),
            provenance=(_provenance(str(fake_repo / "django_strawberry_framework.py")),),
            wall_seconds=2.0,
            log_path="/scratch/runs/mutant.log",
        )

    monkeypatch.setattr(prove_failability, "_run_scope", fake_run_scope)
    manifest = _manifest(
        tmp_path,
        anchor=[*LONG_ANCHOR, long_line],
        replacement="    pass",
        expect_failing=[COUNT_ROW],
    )
    output = tmp_path / "proofs.json"
    markdown = tmp_path / "proofs.md"

    code = prove_failability.main(
        [
            str(manifest),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--json",
            str(output),
            "--output",
            str(markdown),
        ],
    )

    assert code == 0
    assert all(capture is not None for capture in calls)
    document = _json_object(output.read_text(encoding="utf-8"))
    assert document["exit_code"] == 0
    assert document["repo_root"] == str(fake_repo)
    assert document["workspace"] is None
    (entry,) = json_list(document, "entries")
    assert json_at(entry, "sites", 0, "anchor") == "\n".join([*LONG_ANCHOR, long_line])
    assert long_line in _text(entry, "files", 0, "diff")
    original = SOURCE.replace("    return value", long_line).encode("utf-8")
    assert json_at(entry, "files", 0, "blob_before") == prove_failability.git_blob_id(original)
    assert json_at(entry, "files", 0, "blob_after") == json_at(entry, "files", 0, "blob_before")
    assert _text(entry, "mutant", "crash_lines", COUNT_ROW).endswith("where 6 = len(queries)")
    assert json_at(entry, "mutant", "provenance", 0, "databases") == {
        "default": "/ws/examples/fakeshop/db.sqlite3",
    }
    assert json_at(entry, "baseline", "wall_seconds") == 1.0
    assert json_at(entry, "expectation") == {
        "met": True,
        "missing": [],
        "unexpected": [],
        "missing_but_failing_at_baseline": [],
    }
    assert json_at(entry, "weakly_pinned") is False
    rendered = markdown.read_text(encoding="utf-8")
    assert f"Workspace: repository root mutated `{fake_repo}`" in rendered
    assert "crash: `t.py:9: assert 6 == 1` (+1 more line(s) in --json)" in rendered
    assert "package `__file__`" in rendered


@pytest.mark.usefixtures("fake_repo")
def test_the_json_record_is_written_for_an_aborted_run_too(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch)
    monkeypatch.setattr(filecmp, "cmp", _never_identical)
    output = tmp_path / "proofs.json"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--json",
            str(output),
        ],
    )

    assert code == 3
    document = _json_object(output.read_text(encoding="utf-8"))
    assert document["exit_code"] == 3
    aborted = _text(document, "aborted")
    assert "could not be restored" in aborted or "does NOT match" in aborted


def test_workspace_refuses_a_repository_root_outside_the_given_path(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = _stub_run(monkeypatch)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--workspace",
            str(elsewhere),
        ],
    )

    assert code == 1
    assert seen == []
    assert "is not inside it" in capsys.readouterr().err
    assert (fake_repo / "package" / "views.py").read_text(encoding="utf-8") == SOURCE


def test_workspace_refuses_a_checkout_that_holds_a_git_directory(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen = _stub_run(monkeypatch)
    (fake_repo / ".git").mkdir()

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--workspace",
            str(fake_repo),
        ],
    )

    assert code == 1
    assert seen == []
    assert "holds a .git" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_repo")
def test_workspace_accepts_the_copy_and_requires_observed_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_run(monkeypatch, failed=tuple(f"tests/test_x.py::test_{i}" for i in range(4)))
    output = tmp_path / "proofs.json"

    code = prove_failability.main(
        [
            str(_manifest(tmp_path)),
            "--scratch-root",
            str(tmp_path / "outside-scratch"),
            "--workspace",
            str(tmp_path),
            "--json",
            str(output),
        ],
    )

    # The stub reports no provenance, which a workspace run may not accept.
    assert code == 1
    document = _json_object(output.read_text(encoding="utf-8"))
    assert document["workspace"] == str(tmp_path.resolve())
    assert any(
        "reported no package `__file__`" in _text(reason)
        for reason in json_list(document, "entries", 0, "invalid_count_reasons")
    )


# --- the original manifest shape ---------------------------------------------------------


@pytest.mark.usefixtures("fake_repo")
def test_an_original_shape_manifest_reads_and_grades_with_the_default_fields(
    scratch_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "historical.json"
    manifest.write_text(
        json.dumps(
            {
                "scratch_root": str(tmp_path / "outside-scratch"),
                "proofs": [
                    {
                        "label": "package/views.py::gate",
                        "target": "package/views.py",
                        "anchor": ["    if value is None:", '        raise ValueError("no")'],
                        "replacement": ["    pass"],
                        "mutation": "the gate removed",
                        "scope": ["-n0", "tests/test_x.py"],
                    },
                    {
                        "label": "gate delete",
                        "target": "package/views.py",
                        "anchor": "        return value",
                        "delete": True,
                        "scope": ["tests/test_x.py::test_a"],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    entries, root = prove_failability.load_manifest(manifest)

    assert root == str(tmp_path / "outside-scratch")
    first, second = entries
    assert first.sites == ()
    assert first.expect_failing is None
    assert first.mutation == prove_failability._describe_mutation(ANCHOR, "    pass")
    assert first.mutation_applied.endswith(
        "builder's description (unverified prose): the gate removed",
    )
    assert second.replacement is None
    assert second.mutation.startswith("deleted:")
    assert [site.kind for site in first.mutation_sites] == [prove_failability.ANCHOR_KIND]
    _stub_run(monkeypatch, failed=("tests/test_x.py::test_a",))

    result = prove_failability.execute_entry(first, scratch_root)

    assert result.is_weakly_pinned is True
    assert result.is_inside_rerun_floor is True
    assert "WEAKLY PINNED - revision-needed" in prove_failability._verdict(result)
    assert prove_failability.ZERO_ROW_PLACEHOLDER not in prove_failability.render_report([result])


def test_the_markdown_crash_line_prefers_the_assert_line_over_a_custom_message() -> None:
    # ``assert len(queries) == 1, queries`` puts the captured SQL first and the
    # comparison on a later line; the comparison is what shows direction and size.
    crash = "/ws/t.py:1166: AssertionError: ['SELECT ...']\nassert 6 == 1\n +  where 6 = len(q)"
    run = prove_failability.RunOutcome(
        (COUNT_ROW,),
        (),
        "1 failed",
        1,
        crash_lines=((COUNT_ROW, crash),),
    )

    assert prove_failability._crash_suffix(run, COUNT_ROW) == (
        " - crash: `/ws/t.py:1166: assert 6 == 1` (+2 more line(s) in --json)"
    )
    assert prove_failability._crash_suffix(run, "tests/test_x.py::unseen") == ""
