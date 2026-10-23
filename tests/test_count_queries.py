"""Script tests for the N+1 detector's verdict and comparison logic.

Keeps the database-free half of ``scripts/count_queries.py``: the verdict a
list of per-cardinality query counts earns, the root-row growth gate that
decides whether a verdict is evidence, ``--cardinalities`` parsing, the
``--compare`` delta and refusal, the operation Strawberry would run, and the
usage errors (exit 2, before Django bootstraps) for a document or file that
cannot be measured. The counts are synthetic; the seeding and
execution half needs the fakeshop database and is exercised by running the
script in a workspace copy. There is no live sibling in
``examples/fakeshop/test_query/``: the script measures the package, it is not
reached by a query.
"""

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import pytest

from scripts import _bench_common

if TYPE_CHECKING:
    from graphql import OperationDefinitionNode

    from scripts.count_queries import Operation


@runtime_checkable
class _CountQueries(Protocol):
    """The part of ``scripts/count_queries.py`` these tests read.

    ``compare_reports`` takes the decoded JSON reports, which these tests build as plain
    report dicts.
    """

    BUILTIN_OPERATIONS: "dict[str, Operation]"

    def classify_counts(self, counts: list[int], /) -> str: ...

    def rows_grew(self, root_rows: list[int | None], /) -> bool: ...

    def parse_cardinalities(self, raw: str, /) -> list[int]: ...

    def compare_reports(
        self,
        baseline: Mapping[str, object],
        current: Mapping[str, object],
        /,
    ) -> list[str]: ...

    def select_operation(
        self,
        document: str,
        operation_name: str | None,
        /,
    ) -> "OperationDefinitionNode": ...

    def main(self) -> int: ...


@pytest.fixture
def count_queries(scripts_module: Callable[[str], ModuleType]) -> _CountQueries:
    """Import ``scripts/count_queries.py`` the way it runs: scripts dir on ``sys.path``."""
    module = scripts_module("count_queries")
    assert isinstance(module, _CountQueries)
    return module


@pytest.mark.parametrize(
    ("counts", "verdict"),
    [
        ([4, 4, 4], "batched"),
        ([4, 4], "batched"),
        ([37, 73, 148], "scales with cardinality"),
        ([4, 5], "scales with cardinality"),
        ([4, 4, 5], "mixed"),
        ([5, 4, 6], "mixed"),
        ([6, 5, 4], "mixed"),
    ],
)
def test_counts_classify_by_shape_across_cardinalities(
    count_queries: _CountQueries,
    counts: list[int],
    verdict: str,
) -> None:
    """Equal counts are batched, a rise at every step scales, anything else is mixed."""
    assert count_queries.classify_counts(counts) == verdict


def test_one_count_has_no_verdict(count_queries: _CountQueries) -> None:
    """A single cardinality cannot show a shape, so classification refuses."""
    with pytest.raises(ValueError, match="two or more"):
        count_queries.classify_counts([4])


@pytest.mark.parametrize(
    ("root_rows", "grew"),
    [
        ([6, 12, 27], True),
        ([6, 12, 12], False),
        ([100, 100], False),
        ([6, None], False),
    ],
)
def test_verdict_is_evidence_only_when_root_rows_grew(
    count_queries: _CountQueries,
    root_rows: list[int | None],
    *,
    grew: bool,
) -> None:
    """Flat or unknown root rows mean the added parents never reached a resolver."""
    assert count_queries.rows_grew(root_rows) is grew


def test_cardinalities_parse_sorted_and_refuse_zero_or_repeats(
    count_queries: _CountQueries,
) -> None:
    """Cells run ascending; 0 fakes a slope and a repeat measures nothing new."""
    assert count_queries.parse_cardinalities("30,2,10") == [2, 10, 30]
    with pytest.raises(ValueError, match="positive"):
        count_queries.parse_cardinalities("0,2")
    with pytest.raises(ValueError, match="distinct"):
        count_queries.parse_cardinalities("2,2,10")


def _report(
    counts: list[int],
    *,
    sha1: str = "abc",
    name: str | None = None,
    verdict: str | None = "batched",
) -> dict[str, object]:
    report = _bench_common.build_report(
        tool="count_queries",
        provenance={"package_file": "/tree/pkg/__init__.py"},
        params={
            "graphql_operation_name": name,
            "operation_sha1": sha1,
            "optimizer": True,
            "seeder": "products",
        },
        rows=[
            {"cardinality": n, "queries": q, "root_rows": n * 6}
            for n, q in zip((2, 10, 30), counts, strict=False)
        ],
        failures=[],
    )
    report["verdict"] = verdict
    return report


def test_compare_prints_per_cardinality_deltas_and_both_verdicts(
    count_queries: _CountQueries,
) -> None:
    """Each cardinality shows before, after and signed delta, then the verdict change."""
    before = _report([4, 4, 4])
    after = _report([4, 13, 33], verdict="scales with cardinality")

    lines = count_queries.compare_reports(before, after)

    assert lines == [
        "    N  before   after   delta",
        "    2       4       4      +0",
        "   10       4      13      +9",
        "   30       4      33     +29",
        "verdict: batched -> scales with cardinality",
    ]


@pytest.mark.parametrize(
    ("before", "after", "key"),
    [
        (("abc", None), ("def", None), "operation_sha1"),
        (("abc", "One"), ("abc", "Two"), "graphql_operation_name"),
        (("abc", None), ("abc", "Two"), "graphql_operation_name"),
    ],
)
def test_compare_refuses_a_different_operation(
    count_queries: _CountQueries,
    before: tuple[str, str | None],
    after: tuple[str, str | None],
    key: str,
) -> None:
    """Deltas between two operations mean nothing, so the comparison refuses.

    One document can hold several operations, so the same fingerprint run
    under another operation name is a different measurement.
    """
    baseline = _report([4, 4, 4], sha1=before[0], name=before[1])
    current = _report([4, 4, 4], sha1=after[0], name=after[1])

    with pytest.raises(ValueError, match=key):
        count_queries.compare_reports(baseline, current)


@pytest.mark.parametrize(
    ("document", "operation_name", "selected"),
    [
        ("{ allItems { name } }", None, None),
        ("query One { allItems { name } }", None, "One"),
        ("query One { allItems { name } }", "One", "One"),
        ("query One { a } query Two { b }", None, "One"),
        ("query One { a } query Two { b }", "Two", "Two"),
        ("fragment F on Item { name } query Two { b }", None, "Two"),
        ("fragment F on Item { name } query Two { b }", "Two", "Two"),
    ],
)
def test_select_operation_follows_strawberrys_rule(
    count_queries: _CountQueries,
    document: str,
    operation_name: str | None,
    selected: str | None,
) -> None:
    """A given name must match; none runs the first operation, so a nameless run compares alike."""
    operation = count_queries.select_operation(document, operation_name)
    assert (operation.name.value if operation.name else None) == selected


@pytest.mark.parametrize(
    ("document", "operation_name", "reason"),
    [
        ("", None, "Unexpected <EOF>"),
        ("  \n", None, "Unexpected <EOF>"),
        ("query {", None, "Expected Name"),
        ("fragment F on Item { name }", None, "no operation definition"),
        ("fragment F on Item { name }", "F", "no operation named 'F'"),
        ("{ allItems { name } }", "Foo", "no operation named 'Foo'"),
        ("query One { a }", "Nope", "no operation named 'Nope'"),
    ],
)
def test_select_operation_refuses_an_unparseable_document_or_a_missing_operation(
    count_queries: _CountQueries,
    document: str,
    operation_name: str | None,
    reason: str,
) -> None:
    """A document that does not parse, or holds no operation under the name, is refused."""
    with pytest.raises(ValueError, match=reason):
        count_queries.select_operation(document, operation_name)


class _BootstrapReachedError(Exception):
    """Raised by the stand-in bootstrap: the run got past every up-front refusal."""


def _refuse_bootstrap(mode: str) -> None:
    raise _BootstrapReachedError(mode)


def _write_inputs(root: Path) -> None:
    """Write the files the ``main`` rows name, relative to ``root``."""
    for name, text in {
        "anonymous.graphql": "{ allItems { name } }",
        "named.graphql": "query One { allItems { name } }",
        "syntax.graphql": "query {",
        "empty.graphql": "",
        "whitespace.graphql": "  \n",
        "fragment.graphql": "fragment F on Item { name }",
        "not-json.json": "not json",
        "not-a-report.json": "[1]",
        "failed-run.json": json.dumps(_report([], verdict=None)),
        "unmeasured-run.json": json.dumps(_report([4], verdict=None)),
        "measured-run.json": json.dumps(_report([4, 4, 4])),
    }.items():
        _ = (root / name).write_text(text, encoding="utf-8")
    _ = (root / "latin1.graphql").write_bytes(b"\xff\xfe{ a }")
    (root / "inputs").mkdir()


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["--query", "syntax.graphql"], "Expected Name, found <EOF>. (line 1 column 8)"),
        (["--query", "empty.graphql"], "Unexpected <EOF>"),
        (["--query", "whitespace.graphql"], "Unexpected <EOF>"),
        (["--query", "fragment.graphql"], "no operation definition"),
        (
            [
                "--query",
                "fragment.graphql",
                "--operation-name",
                "F",
            ],
            "no operation named 'F'",
        ),
        (
            [
                "--query",
                "anonymous.graphql",
                "--operation-name",
                "Foo",
            ],
            "no operation named 'Foo'",
        ),
        (
            [
                "--query",
                "named.graphql",
                "--operation-name",
                "Nope",
            ],
            "no operation named 'Nope'",
        ),
        (["--query", "missing.graphql"], "--query: cannot read missing.graphql"),
        (["--query", "inputs"], "--query: cannot read inputs"),
        (["--query", "latin1.graphql"], "not UTF-8 text"),
        (
            [
                "--query",
                "named.graphql",
                "--compare",
                "missing.json",
            ],
            "--compare: cannot read missing.json",
        ),
        (
            [
                "--query",
                "named.graphql",
                "--compare",
                "inputs",
            ],
            "--compare: cannot read inputs",
        ),
        (
            [
                "--query",
                "named.graphql",
                "--compare",
                "not-json.json",
            ],
            "is not JSON text",
        ),
        (
            [
                "--query",
                "named.graphql",
                "--compare",
                "not-a-report.json",
            ],
            "is not a count_queries JSON report",
        ),
        (
            [
                "--query",
                "named.graphql",
                "--compare",
                "failed-run.json",
            ],
            "measured no cell",
        ),
        (
            [
                "--query",
                "named.graphql",
                "--json",
                "missing/report.json",
            ],
            "missing is not a directory",
        ),
        (
            [
                "--query",
                "named.graphql",
                "--json",
                "inputs",
            ],
            "argument --json: cannot write inputs: it is a directory",
        ),
    ],
)
def test_unmeasurable_input_exits_2_before_bootstrap(
    count_queries: _CountQueries,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    argv: list[str],
    message: str,
) -> None:
    """A document, file or path the run cannot use is a usage error: exit 2, no bootstrap, no report."""
    _write_inputs(tmp_path)
    monkeypatch.chdir(tmp_path)
    json_flag = [] if "--json" in argv else ["--json", "report.json"]
    monkeypatch.setattr("sys.argv", ["count_queries", *argv, *json_flag])
    monkeypatch.setattr(count_queries, "bootstrap_fakeshop_django", _refuse_bootstrap)

    with pytest.raises(SystemExit) as raised:
        count_queries.main()

    assert raised.value.code == 2
    assert message in capsys.readouterr().err
    assert not (tmp_path / "report.json").exists()


@pytest.mark.parametrize(
    "argv",
    [
        ["--query", "named.graphql"],
        ["--query", "anonymous.graphql"],
        [
            "--query",
            "named.graphql",
            "--operation-name",
            "One",
        ],
        [
            "--query",
            "named.graphql",
            "--compare",
            "measured-run.json",
            "--json",
            "report.json",
        ],
        [
            "--query",
            "named.graphql",
            "--compare",
            "unmeasured-run.json",
        ],
        [
            "--query",
            "named.graphql",
            "--json",
            "",
        ],
        ["--operation-name", "products-items"],
    ],
)
def test_measurable_input_reaches_bootstrap(
    count_queries: _CountQueries,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    argv: list[str],
) -> None:
    """The control for the refusals: usable inputs pass every up-front check.

    A baseline with cells but no verdict still compares cell by cell, and an empty ``--json``
    means no report.
    """
    _write_inputs(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["count_queries", *argv])
    monkeypatch.setattr(count_queries, "bootstrap_fakeshop_django", _refuse_bootstrap)

    with pytest.raises(_BootstrapReachedError):
        count_queries.main()


def test_builtin_operations_name_a_known_seeder(count_queries: _CountQueries) -> None:
    """Every built-in operation seeds rows its root field reads."""
    assert {op.seeder for op in count_queries.BUILTIN_OPERATIONS.values()} <= {
        "products",
        "library",
        "glossary",
    }
