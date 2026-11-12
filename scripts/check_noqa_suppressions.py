"""Hold ruff suppressions, in comments and in config, to their ledgers.

ruff keeps no count of what it is told to skip: ``RUF100`` refuses a ``# noqa`` that
silences nothing, but a new one that silences a real diagnostic passes, and so does a rule
dropped from ``select``, a new per-file ignore, or an exclude. This gate closes all of them
over every git-tracked file ruff lints, as ``check_type_suppressions.py`` does for
basedpyright:

1. a file-level ``# ruff: noqa`` or ``# flake8: noqa``, with or without codes, is refused.
   ``[tool.ruff]`` and its per-file ignores own which rules a whole file skips;
2. a blanket or malformed ``# noqa`` (no code, or codes not written ``# noqa: E501, F401``)
   is refused;
3. the comment ledger. ``scripts/noqa_suppressions.toml`` records, per site, how many times
   each code is suppressed there, one count per ``# noqa`` line naming it and per
   ``# ruff: disable[...]`` fence opening it, plus ``bare``: the ``# noqa`` lines and fences
   whose comment gives no reason after the codes. A site is the innermost symbol enclosing
   the suppression, keyed as a citation names it (``path::QualifiedName``, ``path`` alone at
   module level). A count above its entry, or at a site the ledger does not list, is a new
   suppression: fix the diagnostic instead, and give a ``# noqa`` that must stay its reason
   on the same comment (``# noqa: A002 - the GraphQL argument is named id``). A count below
   it is a cleared one: ``--write`` lowers the entry so it cannot come back;
4. the config ledger. ``scripts/ruff_config_suppressions.toml`` records the effective
   config ruff itself reports (``ruff check --show-settings``), so every spelling of a
   setting counts the same: each stable rule no file runs (unselected or ignored) under
   ``pyproject.toml::lint.ignore``, and each rule a per-file ignore turns off under
   ``pyproject.toml::lint.per-file-ignores[GLOB]``, a prefix expanded to its codes. An
   entry the ledger does not list is refused as in 3;
5. a tracked file ruff never lints. Every tracked ``.py`` and ``.pyi`` file must be in
   ``ruff check --show-files`` (an ``exclude``, ``extend-exclude`` or ``.gitignore`` would
   drop it), ``lint.exclude`` must be empty, no tracked ``ruff.toml`` / ``.ruff.toml`` or
   nested ``pyproject.toml`` with a ``[tool.ruff`` table may override the root config, and
   no notebook is tracked (ruff lints its cells, which this gate cannot site).

Both ledgers are generated, never edited by hand: ``--write`` only lowers or drops an entry
and records a new or larger one only under ``--allow-new``. ``--since REV`` walks the
first-parent commits after ``REV`` and refuses each one that raises, without a
``Suppression-Growth-Approved: <reason>`` trailer (the consent ``check_type_suppressions.py``
reads), the comment ledger's total of any kind or any single entry of the config ledger: a
``# noqa`` moved between sites keeps its one-line reach, a per-file ignore moved to a wider
glob does not. The commit that creates a ledger sets its baseline.

Only comment tokens are read, so a string or docstring that quotes a ``# noqa`` is not a
suppression. Each ``#``-separated part of a comment is read on its own, so
``# pyright: ignore[...]  # noqa: X`` counts its ``X``. The reading errs toward counting: a
form ruff ignores (two ``# noqa`` parts on one line) may count, a form ruff honours may not
pass uncounted.

Usage::

    uv run python scripts/check_noqa_suppressions.py
    uv run python scripts/check_noqa_suppressions.py --write [--allow-new]
    uv run python scripts/check_noqa_suppressions.py --since REV [--until REV]

Exit code ``1`` (each violation listed) on any violation, ``2`` when a file cannot be read
or parsed, a ledger is invalid, ruff cannot report its config or prints it in a form this
script does not know, or git cannot read the ``--since`` range.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tokenize
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import tomli

try:
    import _git
    import check_citations
    import check_type_suppressions as type_suppressions
except ModuleNotFoundError:  # imported as a ``scripts`` submodule (repo root on path)
    from scripts import _git, check_citations
    from scripts import check_type_suppressions as type_suppressions

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence

    from typing_extensions import TypeIs

REPO_ROOT = _git.CHECKOUT_ROOT
#: The generated comment ledger, repo-relative.
LEDGER = "scripts/noqa_suppressions.toml"
#: The generated config ledger, repo-relative.
CONFIG_LEDGER = "scripts/ruff_config_suppressions.toml"
#: This script, as a ledger violation tells the reader to run it.
SCRIPT = "scripts/check_noqa_suppressions.py"
#: The ledger kind of a noqa line or fence that gives no reason after its codes.
BARE = "bare"
#: The one ruff config, repo-relative.
CONFIG = "pyproject.toml"
#: The config-ledger site of the stable rules no file runs.
OFF_SITE = f"{CONFIG}::lint.ignore"

_CODE = r"[A-Z]+[0-9]+"
#: A ``noqa`` part of a comment: its codes, then whatever the comment says after them.
_NOQA = re.compile(
    rf"\s*(?i:noqa)\b(?::\s*(?P<codes>{_CODE}(?:[\s,]+{_CODE})*))?(?P<rest>.*)",
    re.DOTALL,
)
#: A file-level exemption in either spelling, any case (ruff reads some spellings only).
_FILE_LEVEL = re.compile(r"\s*(?i:ruff|flake8)\s*:\s*(?i:noqa)\b")
#: The opening of a ruff ``disable`` fence, spaced as ruff allows; ``enable`` counts nothing.
_FENCE = re.compile(r"\s*ruff\s*:\s*disable\s*\[(?P<codes>[^\]]*)\](?P<rest>.*)", re.DOTALL)
#: Separators a reason may open with; what is left must say something.
_REASON_LEAD = " \t-:;,."
#: A tracked file that would override the root config for its tree.
_RUFF_TOML = re.compile(r"(?:^|/)\.?ruff\.toml$")
#: A rule in ``ruff check --show-settings``: ``\tname (CODE),``, or ``\tname,`` for a rule
#: ruff gives no code.
_SETTINGS_RULE = re.compile(rf"\s*(?P<name>[\w-]+)(?: \((?P<code>{_CODE})\))?,?")

_HEADER = (
    "# Generated by scripts/check_noqa_suppressions.py --write; never edited by hand.\n"
    "# Each site (`path::QualifiedName`, `path` at module level) lists how many times it\n"
    "# suppresses each ruff code (`# noqa` lines and `# ruff: disable[...]` fences) and\n"
    "# its `# noqa` lines and fences with no reason (`bare`); a count may only fall.\n"
)
_CONFIG_HEADER = (
    "# Generated by scripts/check_noqa_suppressions.py --write; never edited by hand.\n"
    "# The stable ruff rules the effective config turns off: for every file\n"
    "# (`pyproject.toml::lint.ignore`: unselected or ignored) and per per-file-ignore\n"
    "# glob (`pyproject.toml::lint.per-file-ignores[GLOB]`); an entry may only go.\n"
)


class _Args(argparse.Namespace):
    """The parsed command line: one field per ``parse_args`` argument."""

    write: bool
    allow_new: bool
    since: str | None
    until: str


# ``json.loads`` returns ``Any``; this alias hands callers an ``object`` to narrow.
_loads: Callable[[str], object] = json.loads


class UnreadableSourceError(ValueError):
    """A tracked file cannot be read, decoded, tokenized or parsed."""


class RuffConfigError(ValueError):
    """ruff printed its settings or rule catalog in a form this script does not read."""


class RuffConfig(NamedTuple):
    """What the effective ruff config skips, as ruff itself reports it."""

    #: The repo-relative files ``ruff check`` lints.
    linted: frozenset[str]
    #: ``lint.exclude``'s patterns.
    lint_exclude: tuple[str, ...]
    #: The stable rules no file runs.
    off: frozenset[str]
    #: ``(glob, code)`` per rule a per-file ignore turns off; a negated glob starts ``!``.
    per_file: tuple[tuple[str, str], ...]


def _is_object_list(value: object) -> TypeIs[list[object]]:
    """Return whether a decoded JSON value is an array."""
    return isinstance(value, list)


def _is_json_object(value: object) -> TypeIs[dict[str, object]]:
    """Return whether a decoded JSON value is an object (JSON keys are always strings)."""
    return isinstance(value, dict)


def _comment_parts(source: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line, part)`` for each ``#``-separated part of each comment in ``source``."""
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            for part in token.string.split("#")[1:]:
                yield token.start[0], part


def _codes(text: str) -> list[str]:
    """Return the ruff codes a comma- or space-separated list names."""
    return re.findall(_CODE, text)


def _unreasoned(rest: str) -> bool:
    """Return whether the text after a suppression's codes gives no reason."""
    return not rest.strip(_REASON_LEAD)


def scan(
    path: str,
    source: str,
) -> tuple[list[type_suppressions.Violation], list[tuple[int, str]]]:
    """Return ``source``'s refused comments and its ``(line, kind)`` suppressions.

    A kind is a ruff code or :data:`BARE`. A ``# noqa`` line naming two codes counts once
    for each; a ``# ruff: enable[...]`` closes a fence and counts nothing.
    """
    violations: list[type_suppressions.Violation] = []
    found: list[tuple[int, str]] = []
    for line, part in _comment_parts(source):
        if _FILE_LEVEL.match(part):
            violations.append(
                type_suppressions.Violation(
                    path,
                    line,
                    f"file-level `#{part.rstrip()}` (pyproject.toml owns which rules a file skips)",
                ),
            )
        elif (fence := _FENCE.match(part)) is not None:
            found.extend((line, code) for code in _codes(fence.group("codes")))
            if _unreasoned(fence.group("rest")):
                found.append((line, BARE))
        elif (noqa := _NOQA.match(part)) is not None:
            if noqa.group("codes") is None:
                violations.append(
                    type_suppressions.Violation(
                        path,
                        line,
                        "blanket or malformed `# noqa`: name its codes as `# noqa: E501, F401`",
                    ),
                )
                continue
            found.extend((line, code) for code in _codes(noqa.group("codes")))
            if _unreasoned(noqa.group("rest")):
                found.append((line, BARE))
    return violations, found


def suppressions(
    path: str,
    found: list[tuple[int, str]],
) -> Iterator[tuple[int, type_suppressions.Entry]]:
    """Yield ``(line, (site, kind))`` for each of ``path``'s ``found`` suppressions, keyed to its site."""
    for line, kind in sorted(found):
        symbol = check_citations.enclosing_symbol(REPO_ROOT / path, line)
        yield line, (path if symbol is None else f"{path}::{symbol}", kind)


def _setting(settings: str, name: str) -> list[str]:
    """Return the value lines of setting ``name`` in ``ruff check --show-settings`` output.

    A bracketed value spans the lines up to its closing bracket at the start of a line; a
    one-line value (``[]``) is returned as its only line.

    Raises:
        RuffConfigError: ``settings`` prints no ``name``.

    """
    lines = settings.splitlines()
    prefix = f"{name} = "
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            value = line.removeprefix(prefix)
            if value not in {"[", "{"}:
                return [value]
            close = "]" if value == "[" else "}"
            try:
                end = lines.index(close, index + 1)
            except ValueError:
                raise RuffConfigError(f"`{name}` in ruff's settings is never closed") from None
            return lines[index + 1 : end]
    raise RuffConfigError(f"ruff's settings print no `{name}`")


def _rule_key(rule: re.Match[str]) -> str:
    """Return a settings rule's ledger kind: its code, or its name when ruff gives it none."""
    return rule.group("code") or rule.group("name")


def enabled_rules(settings: str) -> frozenset[str]:
    """Return the codes ``linter.rules.enabled`` lists in ``settings``.

    Raises:
        RuffConfigError: The list is missing, empty, or holds a line that is not a rule.

    """
    codes: set[str] = set()
    for line in _setting(settings, "linter.rules.enabled"):
        if (rule := _SETTINGS_RULE.fullmatch(line)) is None:
            raise RuffConfigError(f"unreadable enabled rule {line!r}")
        codes.add(_rule_key(rule))
    if not codes:
        raise RuffConfigError("ruff's settings enable no rule")
    return frozenset(codes)


def per_file_ignores(settings: str) -> tuple[tuple[str, str], ...]:
    """Return ``(glob, code)`` per rule ``linter.per_file_ignores`` turns off in ``settings``.

    Raises:
        RuffConfigError: An entry has no ``basename_matcher`` or ``negated``, or a rule line
            is unreadable.

    """
    found: list[tuple[str, str]] = []
    glob: str | None = None
    negated: bool | None = None
    in_data = False
    for raw in _setting(settings, "linter.per_file_ignores"):
        line = raw.strip()
        if line.startswith("basename_matcher = "):
            glob, negated = str(_loads(line.removeprefix("basename_matcher = "))), None
        elif line.startswith("negated = "):
            negated = line.removeprefix("negated = ") == "true"
        elif line == "data = [":
            if glob is None or negated is None:
                raise RuffConfigError(
                    "a per-file ignore prints no `basename_matcher` or `negated`",
                )
            in_data = True
        elif line == "]":
            in_data, glob, negated = False, None, None
        elif in_data:
            if (rule := _SETTINGS_RULE.fullmatch(line)) is None:
                raise RuffConfigError(f"unreadable per-file-ignored rule {line!r}")
            found.append((f"!{glob}" if negated else str(glob), _rule_key(rule)))
    return tuple(sorted(set(found)))


def stable_rules(catalog: str) -> frozenset[str]:
    """Return the stable rules in ``ruff rule --all --output-format json`` output, by code.

    A rule ruff gives no code is keyed by its name, as ``--show-settings`` prints it.

    Raises:
        RuffConfigError: The catalog is not a list of rules or lists no stable one.

    """
    rules = _loads(catalog)
    if not _is_object_list(rules):
        raise RuffConfigError("ruff's rule catalog is not a list")
    codes: set[str] = set()
    for rule in rules:
        if not _is_json_object(rule):
            raise RuffConfigError(f"ruff's rule catalog lists {rule!r}")
        status, code, name = rule.get("status"), rule.get("code"), rule.get("name")
        key = code if isinstance(code, str) else name
        if not isinstance(key, str):
            raise RuffConfigError(
                f"ruff's rule catalog lists a rule with no code or name: {name!r}",
            )
        if status == "Stable" or (_is_json_object(status) and "Stable" in status):
            codes.add(key)
    if not codes:
        raise RuffConfigError("ruff's rule catalog lists no stable rule")
    return frozenset(codes)


def _ruff(*args: str) -> str:
    """Return the output of ``ruff *args`` run at the repository root."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def ruff_config() -> RuffConfig:
    """Return what the effective config skips, asking ruff at :data:`REPO_ROOT`.

    Raises:
        RuffConfigError: As :func:`enabled_rules`, :func:`per_file_ignores` and
            :func:`stable_rules`.
        subprocess.CalledProcessError: ruff cannot report.

    """
    settings = _ruff("check", "--show-settings", CONFIG)
    root = REPO_ROOT.resolve()
    linted: set[str] = set()
    for line in _ruff("check", "--show-files", ".").splitlines():
        try:
            linted.add(Path(line).resolve().relative_to(root).as_posix())
        except ValueError:
            continue
    exclude = _setting(settings, "linter.exclude")
    return RuffConfig(
        linted=frozenset(linted),
        lint_exclude=()
        if exclude == ["[]"]
        else tuple(line.strip().rstrip(",") for line in exclude),
        off=stable_rules(_ruff("rule", "--all", "--output-format", "json"))
        - enabled_rules(settings),
        per_file=per_file_ignores(settings),
    )


def tracked_files() -> list[str]:
    """Every git-tracked file ruff lints or that holds ruff config, repo-relative."""
    result = _git.run_git(
        REPO_ROOT,
        "ls-files",
        "-z",
        "--",
        "*.py",
        "*.pyi",
        "*.ipynb",
        "*ruff.toml",
        "*pyproject.toml",
        check=True,
    )
    return [path for path in result.stdout.split("\0") if path]


def _config_line(text: str, needle: str) -> int:
    """Return the first line of the config ``text`` that holds ``needle``; ``1`` if none."""
    for number, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return number
    return 1


def config_suppressions(
    config: RuffConfig,
    config_text: str,
) -> Iterator[tuple[str, int, type_suppressions.Entry]]:
    """Yield ``(path, line, (site, code))`` per rule ``config`` turns off."""
    off_line = _config_line(config_text, "[tool.ruff.lint]")
    for code in sorted(config.off):
        yield CONFIG, off_line, (OFF_SITE, code)
    for glob, code in config.per_file:
        line = _config_line(config_text, json.dumps(glob.removeprefix("!")))
        yield CONFIG, line, (f"{CONFIG}::lint.per-file-ignores[{glob}]", code)


def coverage_violations(
    tracked: Iterable[str],
    config: RuffConfig,
    root: Path,
) -> Iterator[type_suppressions.Violation]:
    """Yield each tracked file ruff never lints, each override config, and ``lint.exclude``."""
    for pattern in config.lint_exclude:
        yield type_suppressions.Violation(
            CONFIG,
            1,
            f"`lint.exclude` skips {pattern}: no file may skip every rule",
        )
    for path in tracked:
        if path.endswith(".ipynb"):
            yield type_suppressions.Violation(
                path,
                1,
                "a tracked notebook: ruff lints its cells, which no ledger can site; "
                "keep the code in a `.py` module",
            )
        elif _RUFF_TOML.search(path) or (
            path != CONFIG
            and path.endswith("/pyproject.toml")
            and "[tool.ruff" in (root / path).read_text(encoding="utf-8")
        ):
            yield type_suppressions.Violation(
                path,
                1,
                "a nested ruff config overrides pyproject.toml for its tree: fold it in",
            )
        elif path.endswith((".py", ".pyi")) and path not in config.linted:
            yield type_suppressions.Violation(
                path,
                1,
                "ruff never lints this file (an exclude or .gitignore skips it)",
            )


def _hint(kind: str) -> str:
    """Return what to do about a new suppression of ``kind`` in a comment."""
    if kind == BARE:
        return "give the `# noqa` or fence its reason after the codes"
    return "fix the new diagnostic instead of suppressing it"


def _config_hint(_kind: str) -> str:
    """Return what to do about a rule the config newly turns off."""
    return "keep the rule on and fix its diagnostics"


def _measure(
    paths: Iterable[str],
) -> tuple[list[type_suppressions.Violation], list[tuple[str, int, type_suppressions.Entry]]]:
    """Return the refused comments and the sited suppressions in ``paths``.

    Raises:
        UnreadableSourceError: A file cannot be read, decoded, tokenized or parsed.

    """
    violations: list[type_suppressions.Violation] = []
    measured: list[tuple[str, int, type_suppressions.Entry]] = []
    for path in paths:
        try:
            source = (REPO_ROOT / path).read_text(encoding="utf-8")
            refused, found = scan(path, source)
            violations.extend(refused)
            measured.extend((path, line, entry) for line, entry in suppressions(path, found))
        except (
            OSError,
            UnicodeDecodeError,
            SyntaxError,
            tokenize.TokenError,
        ) as error:
            raise UnreadableSourceError(f"{path}: {error}") from error
    return violations, measured


def _walk(since: str, until: str) -> Iterator[type_suppressions.Violation]:
    """Yield each commit after ``since`` that grows a ledger without consent.

    Raises:
        subprocess.CalledProcessError: git cannot list the range.

    """
    yield from type_suppressions.growth_violations(since, until, LEDGER)
    yield from type_suppressions.growth_violations(since, until, CONFIG_LEDGER, per_entry=True)


def _parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    _ = parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite both ledgers from the tree, lowering or dropping cleared entries",
    )
    _ = parser.add_argument(
        "--allow-new",
        action="store_true",
        help="with --write, also record new or larger entries",
    )
    _ = parser.add_argument(
        "--since",
        help=(
            "also refuse each commit after REV that raises a ledger without "
            f"`{type_suppressions.TRAILER}:`"
        ),
    )
    _ = parser.add_argument(
        "--until",
        default="HEAD",
        help="the last commit --since walks to (default HEAD)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Check (or ``--write``) every tracked file ruff lints, and the config, against the ledgers."""
    args = _parser().parse_args(argv, namespace=_Args())
    ledger_path, config_ledger_path = REPO_ROOT / LEDGER, REPO_ROOT / CONFIG_LEDGER
    try:
        ledger = type_suppressions.load_ledger(ledger_path, frozenset())
        config_ledger = type_suppressions.load_ledger(config_ledger_path, frozenset())
        tracked = tracked_files()
        config = ruff_config()
        violations = list(coverage_violations(tracked, config, REPO_ROOT))
        configured = list(config_suppressions(config, (REPO_ROOT / CONFIG).read_text("utf-8")))
        paths = [path for path in tracked if path.endswith((".py", ".pyi"))]
        refused, measured = _measure(paths)
    except (
        OSError,
        ValueError,
        tomli.TOMLDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"cannot check: {error}", file=sys.stderr)
        return 2
    violations.extend(refused)
    drift = [
        *type_suppressions.ledger_violations(
            measured,
            ledger,
            ledger_path=LEDGER,
            script=SCRIPT,
            over_hint=_hint,
        ),
        *type_suppressions.ledger_violations(
            configured,
            config_ledger,
            ledger_path=CONFIG_LEDGER,
            script=SCRIPT,
            over_hint=_config_hint,
        ),
    ]
    if args.write:
        growth = [v for v in drift if v.path not in {LEDGER, CONFIG_LEDGER}]
        if growth and not args.allow_new:
            violations.extend(growth)
        elif not violations:
            for target, rows, header in (
                (ledger_path, measured, _HEADER),
                (config_ledger_path, configured, _CONFIG_HEADER),
            ):
                _ = target.write_text(
                    type_suppressions.render_ledger(
                        Counter(entry for _, _, entry in rows),
                        header,
                    ),
                    encoding="utf-8",
                )
    else:
        violations.extend(drift)
        try:
            violations.extend(_walk(args.since or "", args.until))
        except (
            OSError,
            subprocess.CalledProcessError,
            ValueError,
            tomli.TOMLDecodeError,
        ) as error:
            print(f"cannot walk --since {args.since}: {error}", file=sys.stderr)
            return 2
    for violation in violations:
        print(f"{violation.path}:{violation.line}: {violation.message}")
    bare = sum(entry[1] == BARE for _, _, entry in measured)
    print(
        f"noqa-suppressions: checked {len(paths)} file(s); suppressed codes "
        f"{len(measured) - bare}, bare {bare}; config off {len(config.off)}, "
        f"per-file {len(config.per_file)}; violations {len(violations)}",
    )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
