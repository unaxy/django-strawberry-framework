"""Script tests for the ``truthful-reads`` gate in ``scripts/check_truthful_reads.py``.

Pins every rule with a should-flag and a should-pass snippet, the exit codes of
both modes and the ``--report`` counts. Every CLI case runs against a throwaway
tree under ``tmp_path`` with ``REPO_ROOT`` pointed at it and ``PACKAGE`` set to
``pkg``. The script inspects source files, not a GraphQL request, so there is no
live sibling in ``examples/fakeshop/test_query/``.
"""

import textwrap
from pathlib import Path

import pytest

from scripts import check_truthful_reads as ctr


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway repo root scanning ``pkg``, cwd inside it."""
    monkeypatch.setattr(ctr, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ctr, "PACKAGE", "pkg")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def _codes(source: str) -> list[tuple[int, str]]:
    findings = ctr.scan_source(textwrap.dedent(source), "mod.py")
    return [(finding.line, finding.code) for finding in findings]


def _summary(stdout: str) -> str:
    return stdout.strip().splitlines()[-1]


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
    findings = ctr.scan_source(source, "mod.py")
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
    findings = ctr.scan_source(source, "mod.py")
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
    findings = ctr.scan_source(source, "mod.py")
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


# --------------------------------------------------------------------------- CLI


def _tree(repo: Path) -> None:
    _write(repo, "pkg/clean.py", "VALUE = 1\n")
    _write(repo, "pkg/types/base.py", "try:\n    work()\nexcept BaseException:\n    pass\n")
    _write(repo, "pkg/types/__pycache__/stale.py", "try:\n    work()\nexcept:\n    pass\n")


def test_default_scan_reads_the_package(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _tree(repo)
    assert ctr.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert out.splitlines()[0] == (
        "pkg/types/base.py:3:1: TR002 `except BaseException` does not re-raise"
    )
    assert _summary(out) == (
        "truthful-reads: checked 2 file(s); findings 1 (TR002 1, TR004 0, TR005 0); errors 0"
    )


def test_no_flag_gates_like_check(repo: Path) -> None:
    _tree(repo)
    assert ctr.main([]) == 1


def test_clean_tree_exits_zero_in_every_mode(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write(repo, "pkg/clean.py", "VALUE = isinstance(1, int)\n")
    assert ctr.main(["--check"]) == 0
    assert ctr.main([]) == 0
    assert ctr.main(["--report"]) == 0
    assert _summary(capsys.readouterr().out).startswith("truthful-reads: checked 1 file(s)")


def test_report_lists_findings_and_counts_and_exits_zero(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(repo)
    _write(repo, "pkg/quiet.py", "import contextlib\ncontextlib.suppress(SystemExit)\n")
    assert ctr.main(["--report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "pkg/types/base.py:3:1: TR002 `except BaseException` does not re-raise" in lines
    assert "pkg/quiet.py:2:1: TR004 `suppress(SystemExit)` swallows cancellation" in lines
    assert "  TR002 1" in lines
    assert "  TR004 1" in lines
    assert "  TR005 0" in lines


def test_findings_are_sorted(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    handler = "try:\n    work()\nexcept SystemExit:\n    pass\n"
    _write(repo, "pkg/b.py", handler)
    _write(repo, "pkg/a.py", handler + handler)
    ctr.main(["--check"])
    lines = [line for line in capsys.readouterr().out.splitlines() if ": TR" in line]
    assert [line.split(": ")[0] for line in lines] == [
        "pkg/a.py:3:1",
        "pkg/a.py:7:1",
        "pkg/b.py:3:1",
    ]


def test_named_file_is_checked(repo: Path) -> None:
    _tree(repo)
    assert ctr.main(["--check", "pkg/clean.py"]) == 0
    assert ctr.main(["--check", "pkg/types/base.py"]) == 1


@pytest.mark.parametrize(
    ("argument", "reason"),
    [
        ("missing.py", "matches nothing"),
        ("notes.txt", "not a .py file"),
        ("pkg/empty", "directory yielded no checkable file"),
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
    _write(repo, "notes.txt", "text\n")
    (repo / "pkg/empty").mkdir()
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
