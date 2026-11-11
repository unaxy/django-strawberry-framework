"""Script tests for the typing-change report in ``scripts/typing_delta.py``.

Pins each section's flag and no-flag case on small in-process source pairs: a narrowing
predicate whose claim names unproven type arguments (and one whose body walks the
elements, or whose arguments are all ``object``), the delegation rule (a delegate whose
claim differs, and one whose claim matches), the duplicate-body rule (and a stub body,
which is never a duplicate); a widened parameter, a new public function typed ``object``
(and ``object`` as a type argument, which is not one); a declared attribute read through
a defaulting reader; a ledger move into a function taking ``object`` (and one into a
precise signature), ledger growth; and the suppression-channel deltas. Also pins the
summary line, the JSON form, ``--fail-on-flags`` and that an empty range reports
nothing. The script inspects source files, not a GraphQL request, so there is no live
sibling in ``examples/fakeshop/test_query/``.
"""

import json

import pytest

from scripts import typing_delta as td

_PKG = "django_strawberry_framework"
_NARROWING = f"{_PKG}/utils/_narrowing.py"
_NARROWING_SOURCE = '''\
from typing import TYPE_CHECKING

from django.db.models import Model, QuerySet

if TYPE_CHECKING:
    from typing_extensions import TypeIs

    def is_queryset(_value: object, /) -> TypeIs[QuerySet[Model, object]]:
        """Stub."""
        ...

    def is_list(_value: object, /) -> TypeIs[list[object]]:
        """Stub."""
        ...
'''


def _report(
    before: dict[str, str],
    after: dict[str, str],
    ledgers: tuple[str | None, str | None] = (None, None),
    head_files: dict[str, str] | None = None,
) -> td.Report:
    files = {**after, **(head_files or {})}
    return td.build_report(("base", "head"), [_PKG], (before, after), ledgers, files.get)


def _rows(report: td.Report, number: int) -> list[td.Row]:
    return report.sections[number - 1].rows


def _flagged_titles(report: td.Report, number: int) -> list[str]:
    return [row.title for row in _rows(report, number) if row.flagged]


# --- section 1 -------------------------------------------------------------------------


_PREDICATES_BEFORE = '''\
from django.db import models
from typing_extensions import TypeIs

from django_strawberry_framework.utils import truth


def _is_queryset_class(value: object) -> TypeIs[type[models.QuerySet[models.Model, object]]]:
    """Old."""
    return truth.is_subclass(value, models.QuerySet)
'''


def test_a_new_predicate_claiming_unproven_type_arguments_is_flagged() -> None:
    """``QuerySet[Model]`` claims model rows; an ``isinstance`` proves only a ``QuerySet``."""
    after = _PREDICATES_BEFORE + (
        "\n\ndef _is_rows(value: object) -> TypeIs[models.QuerySet[models.Model]]:\n"
        "    return isinstance(value, models.QuerySet)\n"
    )
    report = _report({f"{_PKG}/a.py": _PREDICATES_BEFORE}, {f"{_PKG}/a.py": after})

    (row,) = _rows(report, 1)
    assert row.flagged
    assert row.title == f"new {_PKG}/a.py::_is_rows (line 12)"
    assert row.details[0] == (
        "- claim names type arguments a class check cannot prove: models.QuerySet[models.Model]"
    )
    assert "  return isinstance(value, models.QuerySet)" in row.details


@pytest.mark.parametrize(
    "predicate",
    [
        (
            "def _is_rows(value: object) -> TypeIs[models.QuerySet[models.Model, object]]:\n"
            "    return isinstance(value, models.QuerySet)\n"
        ),
        (
            "def _is_names(value: list[object]) -> TypeIs[list[str]]:\n"
            "    return all(isinstance(item, str) for item in value)\n"
        ),
        (
            "def _is_model(value: object) -> TypeIs[type[models.Model] | None]:\n"
            "    return value is None or isinstance(value, type)\n"
        ),
        (
            'def _is_mode(value: object) -> TypeIs[Literal["a", "b"]]:\n'
            '    return value in {"a", "b"}\n'
        ),
    ],
)
def test_a_new_predicate_whose_claim_a_class_check_proves_is_not_flagged(predicate: str) -> None:
    """Wide arguments, an element walk, a bare class and ``Literal`` are not unproven claims."""
    source = "from typing import Literal\n" + _PREDICATES_BEFORE + "\n\n" + predicate

    report = _report({}, {f"{_PKG}/a.py": source})

    assert [row.title.split(" (")[0] for row in _rows(report, 1) if not row.flagged] == [
        f"new {_PKG}/a.py::_is_queryset_class",
        f"new {_PKG}/a.py::{predicate.split('(', maxsplit=1)[0].removeprefix('def ')}",
    ]
    assert _flagged_titles(report, 1) == []


def test_a_predicate_delegating_to_a_differently_claiming_predicate_is_flagged() -> None:
    """A sole ``return is_queryset(value)`` cannot prove more than ``is_queryset`` claims."""
    source = (
        "from django.db import models\n"
        "from typing_extensions import TypeIs\n"
        "from django_strawberry_framework.utils._narrowing import is_list, is_queryset\n\n\n"
        "def _is_rows(value: object) -> TypeIs[models.QuerySet[models.Model, int]]:\n"
        "    return is_queryset(value)\n\n\n"
        "def _is_items(value: object) -> TypeIs[list[object]]:\n"
        "    return is_list(value)\n"
    )
    report = _report(
        {_NARROWING: _NARROWING_SOURCE},
        {_NARROWING: _NARROWING_SOURCE, f"{_PKG}/b.py": source},
    )

    rows = {row.title.split(" (")[0]: row for row in _rows(report, 1)}
    delegation = (
        f"- delegates to {_NARROWING}::is_queryset, whose claim is QuerySet[Model, object], "
        "while claiming models.QuerySet[models.Model, int]"
    )
    assert delegation in rows[f"new {_PKG}/b.py::_is_rows"].details
    # ``list[object]`` resolves to the same claim ``is_list`` makes: not a flag.
    assert not rows[f"new {_PKG}/b.py::_is_items"].flagged


def test_a_predicate_with_another_predicates_body_is_flagged_resolved_through_imports() -> None:
    """Two spellings of one check (``lookups`` vs ``model_lookups``) are one body."""
    first = (
        "from django.db.models import lookups as model_lookups\n"
        "from typing_extensions import TypeIs\n\n\n"
        "def _is_lookup(value: object) -> TypeIs[model_lookups.Lookup]:\n"
        '    """First."""\n'
        "    return isinstance(value, model_lookups.Lookup)\n"
    )
    second = (
        "from django.db.models import lookups\n"
        "from typing_extensions import TypeIs\n\n\n"
        "def _is_lookup(node: object) -> TypeIs[lookups.Lookup]:\n"
        "    return isinstance(node, lookups.Lookup)\n"
    )
    report = _report(
        {f"{_PKG}/a.py": first},
        {f"{_PKG}/a.py": first, f"{_PKG}/b.py": second},
    )

    (row,) = _rows(report, 1)
    assert row.flagged
    assert f"- same body as {_PKG}/a.py::_is_lookup (claim model_lookups.Lookup)" in row.details


def test_stub_bodies_are_never_duplicates_and_an_unchanged_predicate_is_not_reported() -> None:
    """Every ``...`` stub shares one body; a docstring-only edit is not a change."""
    after = _NARROWING_SOURCE.replace('"""Stub."""', '"""Reworded."""')
    added = _NARROWING_SOURCE.replace(
        "\n    def is_list",
        "\n    def is_tuple(_value: object, /) -> TypeIs[tuple[object, ...]]:\n"
        "        ...\n\n    def is_list",
    )

    assert _rows(_report({_NARROWING: _NARROWING_SOURCE}, {_NARROWING: after}), 1) == []
    (row,) = _rows(_report({_NARROWING: _NARROWING_SOURCE}, {_NARROWING: added}), 1)
    assert row.title == f"new {_NARROWING}::is_tuple (line 12)"
    assert not row.flagged


def test_a_changed_claim_and_a_removed_predicate_are_reported() -> None:
    """A claim edit is ``changed`` (and judged); a deleted predicate is listed, not flagged."""
    narrowed = _PREDICATES_BEFORE.replace("models.Model, object]", "models.Model]")

    changed = _rows(_report({f"{_PKG}/a.py": _PREDICATES_BEFORE}, {f"{_PKG}/a.py": narrowed}), 1)
    removed = _rows(_report({f"{_PKG}/a.py": _PREDICATES_BEFORE}, {f"{_PKG}/a.py": "x = 1\n"}), 1)

    assert [(row.flagged, row.title) for row in changed] == [
        (True, f"changed {_PKG}/a.py::_is_queryset_class (line 7)"),
    ]
    assert [(row.flagged, row.title) for row in removed] == [
        (
            False,
            (
                f"removed {_PKG}/a.py::_is_queryset_class "
                "(claim type[models.QuerySet[models.Model, object]])"
            ),
        ),
    ]


def test_a_string_return_annotation_is_read() -> None:
    """A quoted ``"TypeIs[...]"`` is a predicate like an unquoted one."""
    source = (
        "from django.db import models\n\n\n"
        'def _is_rows(value: object) -> "TypeIs[models.QuerySet[models.Model]]":\n'
        "    return isinstance(value, models.QuerySet)\n"
    )

    assert _flagged_titles(_report({}, {f"{_PKG}/a.py": source}), 1) == [
        f"new {_PKG}/a.py::_is_rows (line 4)",
    ]


# --- section 2 -------------------------------------------------------------------------


def test_a_parameter_widened_to_object_is_flagged() -> None:
    """``int`` to ``object``, ``dict[str, int]`` to ``dict[str, Any]`` and a lost annotation."""
    before = "def _f(a: int, b: dict[str, int], c: str) -> int:\n    return 1\n"
    after = (
        "from typing import Any\n\n\n"
        "def _f(a: object, b: dict[str, Any], c) -> int:\n    return 1\n"
    )

    (row,) = _rows(_report({f"{_PKG}/a.py": before}, {f"{_PKG}/a.py": after}), 2)

    assert row.flagged
    assert row.details == [
        "a: int -> object",
        "b: dict[str, int] -> dict[str, Any]",
        "c: str -> (unannotated)",
    ]


def test_an_unwidened_signature_change_is_not_reported() -> None:
    """A narrowed parameter, or a new one typed precisely or with ``object`` as an argument."""
    before = "def _f(a: object) -> int:\n    return 1\n"
    after = "def _f(a: int, b: list[object], c: str | None = None) -> int:\n    return 1\n"

    assert _rows(_report({f"{_PKG}/a.py": before}, {f"{_PKG}/a.py": after}), 2) == []


def test_a_new_public_function_taking_object_is_flagged_and_a_private_one_is_not() -> None:
    """START.md forbids widening a public package parameter; private helpers and tests may take ``object``."""
    source = (
        "class Public:\n"
        "    def run(self, value: object | None) -> None: ...\n"
        "    def _hidden(self, value: object) -> None: ...\n\n\n"
        "class _Private:\n"
        "    def run(self, value: object) -> None: ...\n\n\n"
        "def outer(rows: list[object]) -> None:\n"
        "    def inner(value: object) -> None: ...\n"
    )

    report = _report(
        {},
        {
            f"{_PKG}/a.py": source,
            f"{_PKG}/_b.py": "def f(x: object) -> None: ...\n",
            "tests/test_c.py": "def test_c(value: object) -> None: ...\n",
        },
    )

    assert [(row.title, row.details) for row in _rows(report, 2)] == [
        (f"new public {_PKG}/a.py::Public.run", ["value: object | None"]),
    ]


# --- section 3 -------------------------------------------------------------------------


_FORM = """\
class Form:
    _active: bool
    plain: bool = False

    def first(self) -> bool:
        return getattr(self, "_active", False)

    def second(self) -> bool:
        return hasattr(self, "_active") or getattr(self, "plain", False)

    def third(self) -> bool:
        return read_attr(self, "_active", None) is None

    def fourth(self, other: object) -> bool:
        return getattr(other, "_active", False)
"""


def test_a_declared_attribute_read_with_a_default_is_flagged() -> None:
    """``getattr``/``hasattr``/``read_attr`` on ``self`` of a value-less declaration, once per reader."""
    report = _report({}, {f"{_PKG}/a.py": _FORM})

    assert _flagged_titles(report, 3) == [
        f"{_PKG}/a.py::Form declares `_active` and reads it through getattr(self, ...) (line 6)",
        f"{_PKG}/a.py::Form declares `_active` and reads it through hasattr(self, ...) (line 9)",
        f"{_PKG}/a.py::Form declares `_active` and reads it through read_attr(self, ...) (line 12)",
    ]


def test_an_existing_defaulted_read_and_a_defaulted_attribute_are_not_reported() -> None:
    """A site the base already had is not new; an attribute with a class default is not declared-only."""
    after = _FORM + "\n    x = 1\n"

    assert _rows(_report({f"{_PKG}/a.py": _FORM}, {f"{_PKG}/a.py": after}), 3) == []


# --- section 4 -------------------------------------------------------------------------


_HELPERS = """\
def _walked(owner: str, field_name: object) -> None: ...


def _precise(owner: str, field_name: str) -> None: ...
"""


def test_a_ledger_move_into_a_function_taking_object_is_flagged() -> None:
    """One ignore in a helper taking ``object`` covers every call; a precise signature does not."""
    base = (
        '"probe/t.py::test_a" = { reportArgumentType = 1 }\n"probe/t.py::test_b" = { cast = 1 }\n'
    )
    head = '"probe/t.py::_walked" = { reportArgumentType = 1 }\n"probe/t.py::_precise" = { cast = 1 }\n'

    report = _report({}, {}, (base, head), {"probe/t.py": _HELPERS})

    assert report.sections[3].summary == "total 2 -> 2"
    assert [(row.flagged, row.title, row.details) for row in _rows(report, 4)] == [
        (
            False,
            "move `cast` -> probe/t.py::_precise",
            ["from probe/t.py::test_b", "parameters: owner: str, field_name: str"],
        ),
        (
            True,
            "move `reportArgumentType` -> probe/t.py::_walked",
            [
                "- moved into a function taking object/Any: one ignore covers every call",
                "from probe/t.py::test_a",
                "parameters: owner: str, field_name: object",
            ],
        ),
    ]


def test_ledger_growth_is_flagged_and_a_clear_is_listed() -> None:
    """An appeared unit with no vanished partner is growth; a vanished one is a clear."""
    base = '"probe/t.py::test_a" = { cast = 2 }\n'
    head = (
        '"probe/t.py::test_a" = { cast = 1 }\n"probe/t.py::_precise" = { reportCallIssue = 1 }\n'
    )

    report = _report({}, {}, (base, head), {"probe/t.py": _HELPERS})

    assert report.sections[3].summary == "total 2 -> 2; cast 2 -> 1, reportCallIssue 0 -> 1"
    assert [(row.flagged, row.title) for row in _rows(report, 4)] == [
        (False, "cleared `cast` at probe/t.py::test_a"),
        (True, "new `reportCallIssue` at probe/t.py::_precise"),
    ]


# --- section 5 -------------------------------------------------------------------------


def test_channel_counts_reads_markers_codes_and_orphan_reasons() -> None:
    """A reason line counts as orphan only when its next logical line has no ignore."""
    source = (
        "a = f()  # truth: ok identity read\n"
        "b = f()  # noqa: ANN401, PLC0415\n"
        "# basedpyright: covered on a later line of the statement\n"
        "c = f(\n"
        "    x,  # pyright: ignore[reportArgumentType]\n"
        ")\n"
        "# basedpyright: nothing below\n"
        "# continues\n"
        "d = f()\n"
        's = "# truth: ok in a string"\n'
    )

    assert td.channel_counts(source) == {
        "truth: ok": 1,
        "noqa ANN401": 1,
        "noqa PLC0415": 1,
        "basedpyright reason without ignore": 1,
    }


def test_channel_rises_flag_only_typing_channels() -> None:
    """A new ``truth: ok`` or ``ANN`` code is flagged; another ``noqa`` code is listed."""
    before = "a = 1  # noqa: PLC0415\n"
    after = "a = 1  # truth: ok why\nb = 2  # noqa: ANN401\nc = 3  # noqa: S608\n"

    report = _report({f"{_PKG}/a.py": before}, {f"{_PKG}/a.py": after})

    assert [(row.flagged, row.title) for row in _rows(report, 5)] == [
        (True, "noqa ANN401: 0 -> 1 (+1)"),
        (False, "noqa PLC0415: 1 -> 0 (-1)"),
        (False, "noqa S608: 0 -> 1 (+1)"),
        (True, "truth: ok: 0 -> 1 (+1)"),
    ]


# --- output and the command line -------------------------------------------------------


def test_text_lists_flagged_rows_first_and_ends_with_the_summary() -> None:
    """Each section prints flagged rows before the rest; the last line counts every flag."""
    before = "a = 1  # noqa: S608\n"
    after = "a = 1  # truth: ok why\n"

    report = _report({f"{_PKG}/a.py": before}, {f"{_PKG}/a.py": after})
    lines = report.text().splitlines()

    section = lines.index("== 5. Other suppression channels: 2 count(s) moved")
    assert lines[section + 1 : section + 3] == [
        "FLAG truth: ok: 0 -> 1 (+1)",
        "     noqa S608: 1 -> 0 (-1)",
    ]
    assert lines[-1] == "typing-delta base..head: 1 flagged"
    payload = report.as_json()
    assert payload["flagged"] == 1
    assert json.loads(json.dumps(payload)) == payload


def test_an_empty_range_reports_nothing_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """``HEAD..HEAD`` reads both trees through git and changes nothing, even with ``--fail-on-flags``."""
    assert td.main(["HEAD", "--fail-on-flags"]) == 0

    assert capsys.readouterr().out.splitlines()[-1] == "typing-delta HEAD..HEAD: 0 flagged"


def test_worktree_reads_the_head_side_without_touching_the_index_or_refs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--worktree`` reports ``base..worktree``; the index, refs and git dir stay as found."""
    git_dir = td.REPO_ROOT / ".git"
    index = (git_dir / "index").read_bytes()
    head = td._commit("HEAD")

    assert td.main(["HEAD", "--worktree"]) == 0

    assert capsys.readouterr().out.splitlines()[-1].startswith("typing-delta HEAD..worktree: ")
    assert (git_dir / "index").read_bytes() == index
    assert td._commit("HEAD") == head
    assert list(git_dir.glob("typing-delta-*.index")) == []


def test_fail_on_flags_exits_one_when_a_row_is_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--fail-on-flags`` turns a flagged report into exit ``1``; without it the exit is ``0``."""
    flagged = td.Report("a", "b", (_PKG,), [td.Section("s", "1", [td.Row("x", flagged=True)])])

    def build(*_args: object) -> td.Report:
        return flagged

    monkeypatch.setattr(td, "build_report", build)

    assert td.main(["HEAD", "--fail-on-flags", "--json"]) == 1
    assert td.main(["HEAD"]) == 0


def test_an_unknown_revision_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    """A revision git cannot resolve is a read failure, not an empty report."""
    assert td.main(["no-such-revision-for-typing-delta"]) == 2

    assert "git cannot read the range" in capsys.readouterr().err
