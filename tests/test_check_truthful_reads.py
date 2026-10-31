"""Script tests for the ``truthful-reads`` gate in ``scripts/check_truthful_reads.py``.

Pins every rule with a should-flag and a should-pass snippet, the ``# truth: ok``
marker (suppression, the reasonless TR900, the unused-marker note), the
``[tool.truthful_reads]`` configuration (default paths, exempt patterns, a
same-named key in another tool's table), the exit codes of the three modes and
the ``--report`` inventory. Every CLI case runs against a throwaway tree under
``tmp_path`` with ``REPO_ROOT`` pointed at it. The script inspects source files,
not a GraphQL request, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

import textwrap
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts import check_truthful_reads as ctr

PYPROJECT = textwrap.dedent(
    """\
    [tool.ruff]
    line-length = 99

    [tool.truthful_reads]
    # default scan and exemptions
    paths = ["pkg"]
    exempt = [
        "pkg/utils/truth.py",  # the one direct reader
        "pkg/vendored",
    ]

    [tool.other]
    paths = ["elsewhere"]
    """,
)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A throwaway repo root with its own pyproject, cwd inside it, config cache cleared."""
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    monkeypatch.setattr(ctr, "REPO_ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    ctr.config.cache_clear()
    yield tmp_path
    ctr.config.cache_clear()


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def _codes(source: str) -> list[tuple[int, str]]:
    findings, _markers = ctr.scan_source(textwrap.dedent(source), "mod.py")
    return [(finding.line, finding.code) for finding in findings]


def _summary(stdout: str) -> str:
    return stdout.strip().splitlines()[-1]


# --------------------------------------------------------------------------- TR001


@pytest.mark.parametrize("dunder", sorted(ctr.IDENTITY_DUNDERS))
def test_tr001_flags_every_identity_dunder_attribute(dunder: str) -> None:
    assert _codes(f"x = obj.{dunder}\n") == [(1, "TR001")]


@pytest.mark.parametrize(
    "source",
    ["obj.__class__ = Other\n", "del obj.__dict__\n", "value = call(\n    arg,\n).__name__\n"],
)
def test_tr001_flags_store_del_and_the_line_of_the_dunder(source: str) -> None:
    lines = source.count("\n")
    assert _codes(source) == [(lines, "TR001")]


@pytest.mark.parametrize(
    "source",
    [
        "logger = get_logger(__name__)\n",
        'if __name__ == "__main__":\n    pass\n',
        "x = obj.__init__\n",
        "x = obj.__slots__\n",
        "x = truth.name(obj)\n",
    ],
)
def test_tr001_ignores_bare_names_and_other_dunders(source: str) -> None:
    assert _codes(source) == []


# --------------------------------------------------------------------------- TR002


@pytest.mark.parametrize(
    "clause",
    [
        "except BaseException:",
        "except SystemExit:",
        "except KeyboardInterrupt:",
        "except GeneratorExit:",
        "except builtins.BaseException:",
        "except (ValueError, BaseException):",
        "except (ValueError, builtins.KeyboardInterrupt) as exc:",
        "except:",
    ],
)
def test_tr002_flags_a_swallowing_handler(clause: str) -> None:
    source = f"try:\n    work()\n{clause}\n    pass\n"
    assert _codes(source) == [(3, "TR002")]


@pytest.mark.parametrize(
    "body",
    [
        # Cleanup, then return: the exception is dropped.
        "    cleanup()\n    return None\n",
        # A different exception replaces the caught one.
        "    raise Other() from exc\n",
        "    raise Other()\n",
        # Re-raising the caught name with a new cause still rewrites it.
        "    raise exc from None\n",
        # The re-raise is not the last top-level statement.
        "    if cond:\n        raise\n",
        # An early return leaves before the trailing raise.
        "    if cond:\n        return None\n    raise\n",
        # A break aimed at the loop around the try leaves the handler.
        "    if cond:\n        break\n    raise\n",
    ],
)
def test_tr002_flags_a_handler_that_does_not_always_reraise(body: str) -> None:
    handler = "for item in items:\n    try:\n        work()\n    except BaseException as exc:\n"
    assert _codes(handler + textwrap.indent(body, "    ")) == [(4, "TR002")]


@pytest.mark.parametrize(
    "body",
    [
        "    raise\n",
        "    cleanup()\n    raise\n",
        "    raise exc\n",
        "    cleanup()\n    raise exc\n",
        # A break/continue aimed at a loop inside the handler stays inside it.
        "    for step in steps:\n        if step:\n            break\n    raise\n",
        # A return inside a nested function is not a return from the handler.
        "    def later():\n        return 1\n    register(later)\n    raise\n",
    ],
)
def test_tr002_passes_cleanup_then_reraise(body: str) -> None:
    source = f"try:\n    work()\nexcept BaseException as exc:\n{body}"
    assert _codes(source) == []


@pytest.mark.parametrize(
    "clause",
    [
        "except Exception:",
        "except (ValueError, TypeError):",
        "except asyncio.CancelledError:",
        "except mod.BaseException:",
    ],
)
def test_tr002_ignores_catchable_exceptions(clause: str) -> None:
    assert _codes(f"try:\n    work()\n{clause}\n    pass\n") == []


def test_tr002_raise_of_a_name_that_is_not_the_as_name_is_flagged() -> None:
    source = "try:\n    work()\nexcept BaseException:\n    raise primary\n"
    assert _codes(source) == [(3, "TR002")]


# --------------------------------------------------------------------------- TR003


@pytest.mark.parametrize(
    "source",
    [
        "from inspect import getattr_static\n",
        "from inspect import getattr_static as lookup\n",
        "value = inspect.getattr_static(obj, 'x')\n",
        "value = getattr_static(obj, 'x')\n",
    ],
)
def test_tr003_flags_every_getattr_static_use(source: str) -> None:
    assert _codes(source) == [(1, "TR003")]


def test_tr003_ignores_the_truthful_replacement() -> None:
    assert _codes("value = truth.static_attr(obj, 'x', None)\nimport inspect\n") == []


# --------------------------------------------------------------------------- TR002 aliases


def _handler_source(prelude: str, clause: str, body: str = "    pass\n") -> tuple[str, int]:
    """Return ``prelude`` + a try whose handler is ``clause``, and the ``except`` line."""
    return f"{prelude}try:\n    work()\n{clause}\n{body}", prelude.count("\n") + 3


@pytest.mark.parametrize(
    ("prelude", "clause"),
    [
        ("BE = BaseException\n", "except BE:"),
        ("CATCH = (BaseException,)\n", "except CATCH:"),
        ("CATCH = (ValueError, SystemExit)\n", "except CATCH as exc:"),
        ("BE: type = KeyboardInterrupt\n", "except (OSError, BE):"),
        ("A = GeneratorExit\nB = A\n", "except B:"),
        ("BASE = (BaseException,)\nCATCH = BASE + (OSError,)\n", "except CATCH:"),
        ("BASE = (SystemExit,)\nCATCH = (*BASE, OSError)\n", "except CATCH:"),
        ("from builtins import BaseException as BE\n", "except BE:"),
        ("import builtins as b\n", "except b.KeyboardInterrupt:"),
        ("import builtins\n", "except builtins.BaseException:"),
        ("if (BE := BaseException):\n    pass\n", "except BE:"),
        # A binding in any scope of the module counts.
        ("def setup():\n    catch = (BaseException,)\n", "except catch:"),
    ],
)
def test_tr002_flags_an_uncatchable_class_caught_through_a_module_name(
    prelude: str,
    clause: str,
) -> None:
    source, line = _handler_source(prelude, clause)
    assert _codes(source) == [(line, "TR002")]


def test_tr002_names_the_alias_and_what_it_catches() -> None:
    source, _line = _handler_source("CATCH = (ValueError, BaseException)\n", "except CATCH:")
    findings, _markers = ctr.scan_source(source, "mod.py")
    assert [finding.message for finding in findings] == [
        "`except CATCH` (catches BaseException) does not re-raise",
    ]


@pytest.mark.parametrize(
    ("prelude", "clause"),
    [
        ("CATCH = (ValueError, OSError)\n", "except CATCH:"),
        ("E = Exception\n", "except E:"),
        ("from builtins import Exception as E\n", "except E:"),
        # A class read through another module is out of reach by design.
        ("import errors\n", "except errors.BaseException:"),
        ("from errors import CATCH\n", "except CATCH:"),
        # Mutually recursive bindings resolve to nothing and terminate.
        ("A = B\nB = A\n", "except A:"),
    ],
)
def test_tr002_ignores_a_name_that_resolves_to_a_catchable_class(
    prelude: str,
    clause: str,
) -> None:
    source, _line = _handler_source(prelude, clause)
    assert _codes(source) == []


def test_tr002_passes_an_alias_handler_that_reraises() -> None:
    body = "    cleanup()\n    raise\n"
    source, _line = _handler_source("BE = BaseException\n", "except BE:", body)
    assert _codes(source) == []


# --------------------------------------------------------------------------- TR002 re-raise


@pytest.mark.parametrize(
    "body",
    [
        "    exc = Other()\n    raise exc\n",
        "    exc += 1\n    raise exc\n",
        "    del exc\n    raise exc\n",
        "    for exc in pending:\n        pass\n    raise exc\n",
        "    with guard() as exc:\n        pass\n    raise exc\n",
        "    try:\n        undo()\n    except OSError as exc:\n        pass\n    raise exc\n",
        "    from mod import thing as exc\n    raise exc\n",
        "    import exc\n    raise exc\n",
        "    if (exc := other()):\n        pass\n    raise exc\n",
        "    def exc():\n        pass\n    raise exc\n",
        "    class exc:\n        pass\n    raise exc\n",
        "    match value:\n        case [*exc]:\n            pass\n    raise exc\n",
        "    match value:\n        case {**exc}:\n            pass\n    raise exc\n",
        "    match value:\n        case str() as exc:\n            pass\n    raise exc\n",
    ],
)
def test_tr002_flags_a_reraise_of_a_rebound_as_name(body: str) -> None:
    source = f"try:\n    work()\nexcept BaseException as exc:\n{body}"
    assert _codes(source) == [(3, "TR002")]


@pytest.mark.parametrize(
    "body",
    [
        # Reading the caught name is not rebinding it.
        "    other = exc\n    log(exc.args)\n    raise exc\n",
        # A local of a nested function is another scope.
        "    def later():\n        exc = None\n    register(later)\n    raise exc\n",
        # A bare raise re-raises the caught exception whatever the name holds.
        "    exc = None\n    raise\n",
    ],
)
def test_tr002_passes_a_reraise_of_the_caught_exception(body: str) -> None:
    source = f"try:\n    work()\nexcept BaseException as exc:\n{body}"
    assert _codes(source) == []


# --------------------------------------------------------------------------- TR004


@pytest.mark.parametrize(
    ("source", "line"),
    [
        ("import contextlib\nwith contextlib.suppress(BaseException):\n    work()\n", 2),
        ("from contextlib import suppress\nwith suppress(KeyboardInterrupt):\n    work()\n", 2),
        ("from contextlib import suppress as quiet\nquiet(ValueError, SystemExit)\n", 2),
        ("import contextlib as cl\nwith cl.suppress(GeneratorExit):\n    work()\n", 2),
        ("import contextlib\nsilence = contextlib.suppress\nsilence(BaseException)\n", 3),
        ("import contextlib\nBE = BaseException\ncontextlib.suppress(BE)\n", 3),
        ("import contextlib\nCATCH = (OSError, BaseException)\ncontextlib.suppress(*CATCH)\n", 3),
        ("from contextlib import suppress\nsuppress(builtins.SystemExit)\n", 2),
    ],
)
def test_tr004_flags_suppress_of_an_uncatchable_class(source: str, line: int) -> None:
    assert _codes(source) == [(line, "TR004")]


def test_tr004_message_names_the_swallowed_classes() -> None:
    source = "import contextlib\ncontextlib.suppress(OSError, SystemExit, BaseException)\n"
    findings, _markers = ctr.scan_source(source, "mod.py")
    assert [finding.message for finding in findings] == [
        "`suppress(BaseException, SystemExit)` swallows cancellation",
    ]


@pytest.mark.parametrize(
    "source",
    [
        "import contextlib\nwith contextlib.suppress(FileNotFoundError):\n    work()\n",
        "from contextlib import suppress\nsuppress(KeyError, asyncio.CancelledError)\n",
        "import contextlib\nCATCH = (KeyError, OSError)\ncontextlib.suppress(*CATCH)\n",
        # A same-named function from another module is not contextlib's.
        "from mylib import suppress\nwith suppress(BaseException):\n    work()\n",
    ],
)
def test_tr004_ignores_suppress_of_catchable_classes(source: str) -> None:
    assert _codes(source) == []


# --------------------------------------------------------------------------- TR005


@pytest.mark.parametrize(
    ("source", "line", "keyword"),
    [
        ("def f():\n    try:\n        work()\n    finally:\n        return None\n", 5, "return"),
        (
            "def f():\n    try:\n        work()\n    finally:\n        if cond:\n            return 1\n",
            6,
            "return",
        ),
        (
            "for item in items:\n    try:\n        work()\n    finally:\n        break\n",
            5,
            "break",
        ),
        ("while cond:\n    try:\n        work()\n    finally:\n        continue\n", 5, "continue"),
        (
            (
                "def f():\n    try:\n        work()\n    except OSError:\n        log()\n"
                "    finally:\n        try:\n            return undo()\n        except OSError:\n"
                "            pass\n"
            ),
            8,
            "return",
        ),
        # A break in a loop's else clause leaves the enclosing loop, not the else.
        (
            (
                "for item in items:\n    try:\n        work()\n    finally:\n"
                "        for step in steps:\n            pass\n        else:\n            break\n"
            ),
            8,
            "break",
        ),
    ],
)
def test_tr005_flags_an_exit_from_a_finally_block(source: str, line: int, keyword: str) -> None:
    findings, _markers = ctr.scan_source(source, "mod.py")
    assert [(finding.line, finding.code, finding.message) for finding in findings] == [
        (line, "TR005", f"`{keyword}` in `finally` discards the in-flight exception"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        "try:\n    work()\nfinally:\n    cleanup()\n",
        "def f():\n    try:\n        return work()\n    finally:\n        cleanup()\n",
        "try:\n    work()\nfinally:\n    for step in steps:\n        if step:\n            break\n",
        "try:\n    work()\nfinally:\n    while step():\n        continue\n",
        "try:\n    work()\nfinally:\n    def later():\n        return 1\n    register(later)\n",
        "try:\n    work()\nfinally:\n    register(lambda: 1)\n",
    ],
)
def test_tr005_ignores_a_finally_block_that_runs_to_its_end(source: str) -> None:
    assert _codes(source) == []


# --------------------------------------------------------------------------- TR006


@pytest.mark.parametrize("dunder", sorted(ctr.IDENTITY_DUNDERS))
@pytest.mark.parametrize(
    "template",
    [
        'getattr(x, "{d}")\n',
        'getattr(x, "{d}", {{}})\n',
        'hasattr(x, "{d}")\n',
        'object.__getattribute__(x, "{d}")\n',
        'type.__getattribute__(cls, "{d}")\n',
        'super().__getattribute__("{d}")\n',
    ],
)
def test_tr006_flags_every_identity_dunder_read_by_name(template: str, dunder: str) -> None:
    assert _codes(template.format(d=dunder)) == [(1, "TR006")]


@pytest.mark.parametrize(
    ("source", "line"),
    [
        ('import operator\nread = operator.attrgetter("__qualname__")\n', 2),
        ('from operator import attrgetter\nread = attrgetter("__class__")\n', 2),
        ('from operator import attrgetter as ag\nread = ag("name", "__module__")\n', 2),
        ('import operator as op\nread = op.attrgetter("model.__name__")\n', 2),
        ('import builtins\nvalue = builtins.getattr(x, "__dict__")\n', 2),
        ('read = getattr\nvalue = read(x, "__mro__")\n', 2),
    ],
)
def test_tr006_flags_an_identity_dunder_named_through_an_alias(source: str, line: int) -> None:
    assert _codes(source) == [(line, "TR006")]


def test_tr006_message_spells_the_call_and_the_literal() -> None:
    findings, _markers = ctr.scan_source('state = object.__getattribute__(x, "__dict__")\n', "m")
    assert [finding.message for finding in findings] == [
        '`object.__getattribute__(..., "__dict__")` reads an identity dunder by name; use truth',
    ]


@pytest.mark.parametrize(
    "source",
    [
        'getattr(x, "name")\n',
        "getattr(x, name)\n",
        'getattr(x, "name", "__dict__")\n',
        'object.__getattribute__(x, "_state")\n',
        'import operator\noperator.attrgetter("name.value")\n',
        "import operator\noperator.attrgetter(name)\n",
        'from mylib import attrgetter\nattrgetter("__name__")\n',
        'x.getattribute("__dict__")\n',
    ],
)
def test_tr006_ignores_a_name_that_is_not_an_identity_dunder(source: str) -> None:
    assert _codes(source) == []


def test_tr006_replaces_tr104_for_an_identity_dunder() -> None:
    assert _codes('getattr(cls, "__name__")\ngetattr(cls, "__wrapped__")\n') == [
        (1, "TR006"),
        (2, "TR104"),
    ]


# --------------------------------------------------------------------------- TR007 / TR008


@pytest.mark.parametrize(
    "source",
    ["vars(obj)\n", "state = vars(self)\n", "import builtins\nstate = builtins.vars(obj)\n"],
)
def test_tr007_flags_vars_of_an_object(source: str) -> None:
    assert _codes(source) == [(source.count("\n"), "TR007")]


def test_tr007_ignores_vars_without_an_argument() -> None:
    assert _codes("names = vars()\n") == []


@pytest.mark.parametrize(
    "source",
    [
        "cls.mro()\n",
        "type.mro(cls)\n",
        "order = obj.mro\n",
        "order = type(obj).mro()\n",
    ],
)
def test_tr008_flags_an_mro_attribute(source: str) -> None:
    assert _codes(source) == [(1, "TR008")]


@pytest.mark.parametrize(
    "source",
    [
        "from ..utils import truth\norder = truth.mro(cls)\n",
        "from . import truth\norder = truth.mro(cls)\n",
        "from django_strawberry_framework.utils import truth as t\norder = t.mro(cls)\n",
        "from django_strawberry_framework.utils.truth import mro\norder = mro(cls)\n",
        "order = cls.__init_subclass__\n",
    ],
)
def test_tr008_ignores_the_truthful_replacement(source: str) -> None:
    assert _codes(source) == []


# --------------------------------------------------------------------------- TR009


@pytest.mark.parametrize(
    ("source", "line"),
    [
        ("found = type(value) in TYPES\n", 1),
        ("found = type(value) not in (list, tuple)\n", 1),
        ("import builtins\nfound = builtins.type(value) in TYPES\n", 2),
        ("from . import truth\nfound = truth.class_of(value) in TYPES\n", 2),
        ("def f(value):\n    kind = type(value)\n    return kind in TYPES\n", 3),
        ("def f(value):\n    if (kind := type(value)) in TYPES:\n        pass\n", 2),
        ("found = 0 < len(x) and type(value) in TYPES\n", 1),
    ],
)
def test_tr009_flags_membership_of_a_class_read(source: str, line: int) -> None:
    assert _codes(source) == [(line, "TR009")]


@pytest.mark.parametrize(
    "source",
    [
        "from . import truth\nfound = truth.is_exact_one_of(value, TYPES)\n",
        "found = type(value) is str\n",
        "found = type(None) == other\n",
        "found = type in TYPES\n",
        "found = type(name, bases, ns) in TYPES\n",
        "def f(kind):\n    return kind in TYPES\n",
        "def g(value):\n    kind = type(value)\n\ndef f(kind):\n    return kind in TYPES\n",
        "found = value in TYPES\n",
    ],
)
def test_tr009_ignores_identity_tests_and_names_bound_elsewhere(source: str) -> None:
    assert _codes(source) == []


# --------------------------------------------------------------------------- TR010


@pytest.mark.parametrize(
    ("source", "line"),
    [
        (
            "from . import truth\nsame = truth.static_attr(cls, name) is truth.static_attr(Base, name)\n",
            2,
        ),
        ("from . import truth\nsame = truth.mro_attr(cls, n) is not truth.mro_attr(Base, n)\n", 2),
        ("same = getattr(cls, seam) is not getattr(Base, seam)\n", 1),
        (
            (
                "from . import truth\n"
                "same = truth.stored_function(truth.static_attr(cls, n)) is truth.stored_function(\n"
                "    truth.mro_attr(Base, n)\n"
                ")\n"
            ),
            2,
        ),
        ("from . import truth\nsame = truth.static_attr(cls, n) is getattr(Base, n)\n", 2),
    ],
)
def test_tr010_flags_an_identity_test_between_two_attribute_reads(source: str, line: int) -> None:
    assert _codes(source) == [(line, "TR010")]


@pytest.mark.parametrize(
    "source",
    [
        "from . import truth\nsame = truth.overrides(cls, Base, name)\n",
        "from . import truth\nsame = truth.static_attr(cls, name) is DEFAULTS\n",
        "from . import truth\nsame = truth.static_attr(cls, name, ABSENT) is not ABSENT\n",
        "from . import truth\nsame = truth.static_attr(cls, name) == truth.static_attr(Base, name)\n",
        "from . import truth\nsame = truth.class_dict(cls).get(n) is truth.class_dict(Base).get(n)\n",
        "same = getattr(cls, name) is value\n",
        "from . import truth\nsame = truth.stored_function(value) is truth.stored_function(other)\n",
    ],
)
def test_tr010_ignores_a_compare_against_a_value_and_non_identity_tests(source: str) -> None:
    assert _codes(source) == []


# --------------------------------------------------------------------------- promoted rules


PROMOTED = [
    ("BE = BaseException\ntry:\n    work()\nexcept BE:{m}\n    pass\n", "TR002"),
    ("try:\n    work()\nexcept BaseException as exc:{m}\n    exc = 1\n    raise exc\n", "TR002"),
    ("import contextlib\nwith contextlib.suppress(BaseException):{m}\n    work()\n", "TR004"),
    ("def f():\n    try:\n        work()\n    finally:\n        return None{m}\n", "TR005"),
    ('state = object.__getattribute__(obj, "__dict__"){m}\n', "TR006"),
    ('reader = operator.attrgetter("__qualname__"){m}\nimport operator\n', "TR006"),
    ("state = vars(self){m}\n", "TR007"),
    ("order = cls.mro(){m}\n", "TR008"),
    ("found = type(value) in TYPES{m}\n", "TR009"),
    ("same = getattr(cls, n) is getattr(Base, n){m}\n", "TR010"),
]


@pytest.mark.parametrize(("template", "code"), PROMOTED)
def test_promoted_rule_fires_and_is_tier_one(template: str, code: str) -> None:
    findings, _markers = ctr.scan_source(template.format(m=""), "mod.py")
    assert [finding.code for finding in findings] == [code]
    assert findings[0].tier == 1


@pytest.mark.parametrize("template", [template for template, _code in PROMOTED])
def test_promoted_rule_is_suppressed_by_a_reasoned_marker(template: str) -> None:
    source = template.format(m="  # truth: ok own pickle state")
    findings, markers = ctr.scan_source(source, "mod.py")
    assert findings == []
    assert [marker.used for marker in markers] == [True]


@pytest.mark.parametrize(("template", "code"), PROMOTED)
def test_promoted_rule_is_not_suppressed_by_a_reasonless_marker(template: str, code: str) -> None:
    findings, _markers = ctr.scan_source(template.format(m="  # truth: ok"), "mod.py")
    assert sorted(finding.code for finding in findings) == sorted([code, "TR900"])


def test_a_promoted_finding_fails_the_gate(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(repo, "pkg/mod.py", "state = vars(obj)\n")
    assert ctr.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert "pkg/mod.py:1:9: TR007 `vars(x)` asks the object for its namespace; use truth" in out
    assert "TR007 1" in _summary(out)


# --------------------------------------------------------------------------- markers


def test_marker_with_reason_suppresses_its_line_only() -> None:
    source = "a = obj.__name__  # truth: ok framework-built class\nb = obj.__name__\n"
    findings, markers = ctr.scan_source(source, "mod.py")
    assert [(f.line, f.code) for f in findings] == [(2, "TR001")]
    assert markers == [ctr.Marker("mod.py", 1, "framework-built class", used=True)]


def test_marker_after_other_comment_text_suppresses() -> None:
    source = "a = obj.__name__  # noqa: B009  # truth: ok framework-built class\n"
    assert _codes(source) == []


def test_marker_on_the_except_line_suppresses_tr002() -> None:
    source = "try:\n    work()\nexcept BaseException:  # truth: ok thread boundary\n    pass\n"
    assert _codes(source) == []


def test_marker_on_the_handler_body_does_not_suppress_tr002() -> None:
    source = "try:\n    work()\nexcept BaseException:\n    pass  # truth: ok wrong line\n"
    assert _codes(source) == [(3, "TR002")]


@pytest.mark.parametrize(
    "comment",
    [
        "# truth: ok",
        "# truth: ok  ",
        "# truth: ok -",
        "#truth:ok:",
    ],
)
def test_marker_without_reason_is_tr900_and_suppresses_nothing(comment: str) -> None:
    assert _codes(f"a = obj.__name__  {comment}\n") == [(1, "TR001"), (1, "TR900")]


def test_marker_in_a_string_is_not_a_marker() -> None:
    assert _codes('a = obj.__name__, "# truth: ok not a comment"\n') == [(1, "TR001")]


def test_unused_marker_is_recorded_as_unused() -> None:
    _findings, markers = ctr.scan_source("a = 1  # truth: ok stale\n", "mod.py")
    assert markers == [ctr.Marker("mod.py", 1, "stale", used=False)]


# --------------------------------------------------------------------------- tier 2


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("isinstance(x, type)\n", "TR101"),
        ("isinstance(x, (type, str))\n", "TR101"),
        ("issubclass(x, Base)\n", "TR102"),
        ("hash(cls)\n", "TR103"),
        ('getattr(cls, "Meta", None)\n', "TR104"),
        ('hasattr(model, "_meta")\n', "TR104"),
        ('getattr(obj, "__wrapped__")\n', "TR104"),
    ],
)
def test_tier2_flags(source: str, code: str) -> None:
    assert _codes(source) == [(1, code)]


@pytest.mark.parametrize(
    "source",
    [
        "isinstance(x, str)\n",
        'getattr(obj, "fields", None)\n',
        "getattr(obj, name)\n",
        "hashlib.sha256(data)\n",
        "type(obj) is Base\n",
    ],
)
def test_tier2_ignores(source: str) -> None:
    assert _codes(source) == []


@pytest.mark.parametrize(
    "probe",
    [
        "getattr(cls, name)",
        "hasattr(cls, name)",
        "isinstance(value, str)",
        "cls.__module__",
    ],
)
def test_tr105_flags_except_exception_around_an_identity_read(probe: str) -> None:
    source = f"try:\n    result = {probe}\nexcept (Exception, OSError):\n    result = None\n"
    assert (3, "TR105") in _codes(source)


@pytest.mark.parametrize(
    "source",
    [
        # The try body reads no identity.
        "try:\n    result = load()\nexcept Exception:\n    result = None\n",
        # The identity read is in the handler, not the try body.
        "try:\n    load()\nexcept Exception:\n    log(isinstance(x, str))\n",
        # A narrow handler is not containment of an identity read.
        "try:\n    result = int(raw)\nexcept ValueError:\n    result = isinstance(raw, str)\n",
    ],
)
def test_tr105_ignores(source: str) -> None:
    assert "TR105" not in {code for _line, code in _codes(source)}


# --------------------------------------------------------------------------- config


@pytest.mark.usefixtures("repo")
def test_config_reads_paths_and_exempt_from_the_scoped_table() -> None:
    assert ctr.config() == (("pkg",), ("pkg/utils/truth.py", "pkg/vendored"))


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[tool.ruff]\nline-length = 99\n", "[tool.truthful_reads] missing"),
        ("[tool.truthful_reads]\npaths = []\nexempt = []\n", "paths is empty"),
        ('[tool.truthful_reads]\npaths = "pkg"\nexempt = []\n', "paths must be an array"),
        ('[tool.truthful_reads]\npaths = ["pkg"]\n', "exempt must be an array"),
    ],
)
def test_bad_config_is_an_error(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    text: str,
    message: str,
) -> None:
    (repo / "pyproject.toml").write_text(text, encoding="utf-8")
    assert ctr.main(["--check"]) == 1
    assert message in capsys.readouterr().err


def test_unparseable_pyproject_is_an_error(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "pyproject.toml").write_text("[tool.truthful_reads\n", encoding="utf-8")
    assert ctr.main(["--check"]) == 1
    assert "cannot parse" in capsys.readouterr().err


def test_missing_pyproject_is_an_error(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "pyproject.toml").unlink()
    assert ctr.main(["--check"]) == 1
    assert "cannot read" in capsys.readouterr().err


# --------------------------------------------------------------------------- CLI


def _tree(repo: Path) -> None:
    _write(repo, "pkg/clean.py", "VALUE = 1\n")
    _write(repo, "pkg/utils/truth.py", "def name(cls):\n    return type.__dict__['__name__']\n")
    _write(repo, "pkg/vendored/lib.py", "x = obj.__class__\n")
    _write(repo, "pkg/types/base.py", "a = cls.__name__\nb = issubclass(a, B)\n")
    _write(repo, "pkg/types/__pycache__/stale.py", "x = obj.__class__\n")


def test_default_scan_uses_configured_paths_and_skips_exempt(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(repo)
    assert ctr.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert (
        out.splitlines()[0]
        == "pkg/types/base.py:1:9: TR001 identity dunder `.__name__` read by lookup"
    )
    assert _summary(out) == (
        "truthful-reads: checked 2 file(s); exempt 2; "
        "tier-1 1 (TR001 1, TR002 0, TR003 0, TR004 0, TR005 0, TR006 0, TR007 0, TR008 0, "
        "TR009 0, TR010 0, TR900 0); tier-2 1; markers 0; errors 0"
    )


def test_check_prints_no_tier2_detail_or_counts(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(repo)
    ctr.main(["--check"])
    out = capsys.readouterr().out
    assert "TR102" not in out.replace("tier-2 1", "")
    assert "report-only" not in out


def test_no_flag_gates_and_prints_tier2_counts(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(repo)
    assert ctr.main([]) == 1
    out = capsys.readouterr().out
    assert (
        "truthful-reads tier 2 (report-only): TR101 0, TR102 1, TR103 0, TR104 0, TR105 0" in out
    )
    assert "pkg/types/base.py:2" not in out


def test_clean_tree_exits_zero_in_every_mode(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write(repo, "pkg/clean.py", "VALUE = isinstance(1, int)\n")
    assert ctr.main(["--check"]) == 0
    assert ctr.main([]) == 0
    assert ctr.main(["--report"]) == 0
    assert _summary(capsys.readouterr().out).startswith("truthful-reads: checked 1 file(s)")


def test_tier2_only_never_fails(repo: Path) -> None:
    _write(repo, "pkg/mod.py", "x = issubclass(a, B)\ny = hash(a)\n")
    assert ctr.main(["--check"]) == 0
    assert ctr.main([]) == 0


def test_report_lists_findings_markers_and_counts_and_exits_zero(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(repo)
    _write(
        repo,
        "pkg/marked.py",
        "a = obj.__name__  # truth: ok framework-built class\nb = 1  # truth: ok\n",
    )
    assert ctr.main(["--report"]) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert "pkg/types/base.py:1:9: TR001 identity dunder `.__name__` read by lookup" in lines
    assert "pkg/types/base.py:2:5: TR102 `issubclass(...)`; use truth.is_subclass" in lines
    assert "pkg/marked.py:2:8: TR900 `# truth: ok` marker without a reason" in lines
    assert "pkg/marked.py:1: truth: ok framework-built class" in lines
    assert "pkg/marked.py:2: truth: ok <no reason>  [suppresses nothing]" in lines
    assert "  TR001 1" in lines
    assert "  TR102 1" in lines
    assert "  TR900 1" in lines
    assert "     1 /    1  pkg/types/base.py" in lines
    assert "     1 /    0  pkg/marked.py" in lines


def test_findings_are_sorted(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(repo, "pkg/b.py", "x = o.__name__\n")
    _write(repo, "pkg/a.py", "y = o.__class__\nx = o.__module__\n")
    ctr.main(["--check"])
    lines = [line for line in capsys.readouterr().out.splitlines() if ": TR" in line]
    assert [line.split(": ")[0] for line in lines] == [
        "pkg/a.py:1:7",
        "pkg/a.py:2:7",
        "pkg/b.py:1:7",
    ]


def test_named_exempt_file_is_reported_not_checked(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(repo)
    assert ctr.main(["--check", "pkg/utils/truth.py", "pkg/clean.py"]) == 0
    captured = capsys.readouterr()
    assert (
        "pkg/utils/truth.py: exempt from the truthful-reads rules -- not checked" in captured.err
    )
    assert "checked 1 file(s); exempt 1;" in _summary(captured.out)


def test_named_file_is_checked(repo: Path) -> None:
    _tree(repo)
    assert ctr.main(["--check", "pkg/types/base.py"]) == 1


@pytest.mark.parametrize(
    ("argument", "reason"),
    [
        ("missing.py", "matches nothing"),
        ("pyproject.toml", "not a .py file"),
        ("pkg/vendored", "directory yielded no checkable file (1 exempt)"),
    ],
)
@pytest.mark.parametrize("mode", ["", "--check", "--report"], ids=["default", "check", "report"])
def test_path_contributing_nothing_is_an_error_in_every_mode(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    mode: str,
    argument: str,
    reason: str,
) -> None:
    _tree(repo)
    assert ctr.main([*([mode] if mode else []), argument]) == 1
    captured = capsys.readouterr()
    assert f"{argument}: {reason} -- NOT checked" in captured.err
    assert _summary(captured.out).endswith("errors 1")


def test_unparseable_file_is_an_error(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(repo, "pkg/broken.py", "def f(:\n")
    assert ctr.main(["--report"]) == 1
    captured = capsys.readouterr()
    assert "pkg/broken.py: cannot scan:" in captured.err


@pytest.mark.usefixtures("repo")
def test_check_and_report_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        ctr.main(["--check", "--report"])
