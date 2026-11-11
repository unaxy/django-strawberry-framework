"""Row-level three-way merge of a SQLite database, for ``scripts/work.py land``.

``examples/fakeshop/db.sqlite3`` is tracked source (the kanban and glossary apps keep
their prose in it), so a copy that edits a glossary row changes a binary file a text
patch cannot merge. :func:`merge` lands it the way START.md "MIXED sqlite carve"
describes by hand: start from an exact copy of the target database (``theirs``, the
shared ``HEAD``'s), and apply only the rows the copy changed between ``base`` (where its
patch starts) and ``ours`` (its content), so nothing else the copy's file holds rides
along, freelist residue included.

Rules
    Every table is keyed by its intrinsic ``rowid`` (read through whichever of
    ``rowid``, ``_rowid_`` or ``oid`` no column shadows). The three schemas
    (``sqlite_master``) must be equal: a migration is not merged row by row. A row the
    copy inserted, updated or deleted is applied where ``theirs`` still holds the
    ``base`` row, skipped where it already holds the copy's, and otherwise a conflict
    (main changed the same row, or inserted at the same ``rowid``); every conflict is
    named and nothing is written. ``sqlite_sequence`` is keyed by table name and takes
    the larger counter; a repeated name is refused.

Writing
    The planned rows are stored state, not operations to replay: in one transaction,
    with foreign keys off and every trigger dropped (and re-created unchanged before
    the commit), each changed row is deleted and the copy's row inserted at its
    ``rowid``, so no trigger or cascade fires and a unique-value swap lands;
    ``sqlite_sequence`` is then set to the planned counters (an insert at an explicit
    ``rowid`` raises one). The result must then hold exactly the planned rows in
    every table and pass ``PRAGMA integrity_check`` and ``PRAGMA foreign_key_check``.

A database with a live ``-wal`` or ``-journal`` file is refused: its file alone is not
its content.

Stdlib only.
"""

from __future__ import annotations

import dataclasses
import shutil
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

#: ``sqlite3.Cursor.fetchall``, its rows typed for the caller.
_fetchall: Callable[[sqlite3.Cursor], list[tuple[object, ...]]] = sqlite3.Cursor.fetchall

SEQUENCE_TABLE = "sqlite_sequence"
#: How many conflicts a refusal names before it summarises the rest.
NAMED_CONFLICTS = 10
#: The names SQLite reads as a table's intrinsic ``rowid`` unless a column takes them.
ROWID_ALIASES = ("rowid", "_rowid_", "oid")
#: The files SQLite keeps beside a database while a write is not yet in it.
JOURNAL_SUFFIXES = ("-wal", "-journal")

Row = tuple[object, ...]
Rows = dict[object, Row]


class MergeError(Exception):
    """The databases cannot be merged row by row; the message says why."""


@dataclasses.dataclass(frozen=True)
class RowChange:
    """One row the merge applied: ``kind`` is ``insert``, ``update`` or ``delete``."""

    table: str
    key: object
    kind: str


@dataclasses.dataclass(frozen=True)
class _Write:
    change: RowChange
    row: Row | None


@dataclasses.dataclass(frozen=True)
class _Plan:
    """The writes to make and every table's rows the result must then hold."""

    writes: list[_Write]
    expected: dict[str, Rows]


def live_journal(path: Path) -> Path | None:
    """Return ``path``'s non-empty ``-wal`` or ``-journal`` file, if it has one."""
    for suffix in JOURNAL_SUFFIXES:
        journal = path.with_name(path.name + suffix)
        if journal.is_file() and journal.stat().st_size > 0:
            return journal
    return None


def _open(path: Path) -> sqlite3.Connection:
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _sql(
    template: str,
    table: str,
    columns: Sequence[str] = (),
    key: str = "rowid",
) -> str:
    """Fill ``template``'s identifier slots; every value stays a bound ``?`` parameter.

    Slots: ``{table}``, ``{key}`` (the unshadowed rowid alias) and ``{columns}`` (quoted,
    comma-separated), and ``{marks}`` (one ``?`` per column plus the key).
    """
    return template.format(
        table=_quote(table),
        key=key,
        columns=", ".join(_quote(column) for column in columns),
        marks=", ".join("?" for _ in range(len(columns) + 1)),
    )


def _schema(connection: sqlite3.Connection) -> list[Row]:
    return _fetchall(
        connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name",
        ),
    )


def _tables(connection: sqlite3.Connection) -> list[str]:
    rows = _fetchall(
        connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"),
    )
    return [str(row[0]) for row in rows]


def _columns(connection: sqlite3.Connection, table: str) -> list[str]:
    """Return ``table``'s columns; a hidden or generated column is refused (it cannot be set)."""
    rows = _fetchall(connection.execute(_sql("PRAGMA table_xinfo({table})", table)))
    if any(row[6] != 0 for row in rows):
        msg = f"table {table} has a hidden or generated column; carve it by hand"
        raise MergeError(msg)
    return [str(row[1]) for row in rows]


def _key(table: str, columns: Sequence[str]) -> str:
    """Return the first rowid alias no column of ``table`` shadows."""
    taken = {column.lower() for column in columns}
    for alias in ROWID_ALIASES:
        if alias not in taken:
            return alias
    msg = f"table {table} has columns named rowid, _rowid_ and oid; carve it by hand"
    raise MergeError(msg)


def _keyed_rows(connection: sqlite3.Connection, table: str) -> Rows:
    """Return ``table``'s rows by ``rowid`` (``sqlite_sequence`` by table name)."""
    if table == SEQUENCE_TABLE:
        rows = _fetchall(connection.execute("SELECT name, seq FROM sqlite_sequence"))
        named = {row[0]: row for row in rows}
        if len(named) != len(rows):
            msg = "sqlite_sequence repeats a table name; carve it by hand"
            raise MergeError(msg)
        return named
    names = _fetchall(connection.execute(_sql("PRAGMA table_xinfo({table})", table)))
    key = _key(table, [str(row[1]) for row in names])
    try:
        rows = _fetchall(connection.execute(_sql("SELECT {key}, * FROM {table}", table, key=key)))
    except sqlite3.OperationalError as error:
        msg = f"table {table} cannot be read by rowid ({error}); carve it by hand"
        raise MergeError(msg) from None
    keyed = {row[0]: row[1:] for row in rows}
    if len(keyed) != len(rows):
        msg = f"table {table} repeats a rowid; carve it by hand"
        raise MergeError(msg)
    return keyed


def _order(key: object) -> tuple[int, int, str]:
    return (0, key, "") if isinstance(key, int) else (1, 0, str(key))


def _seq(row: Row) -> int:
    value = row[1]
    return value if isinstance(value, int) else 0


def _conflict(
    table: str,
    key: object,
    was: Row | None,
    now: Row | None,
) -> str:
    if was is None:
        return f"{table} rowid {key!r}: inserted here and taken on main"
    if now is None:
        return f"{table} rowid {key!r}: deleted here and changed on main"
    return f"{table} rowid {key!r}: changed here and on main"


def _plan_table(
    table: str,
    rows: tuple[Mapping[object, Row], Mapping[object, Row], Rows],
    writes: list[_Write],
    conflicts: list[str],
) -> None:
    """Add ``table``'s writes and conflicts, given its ``(base, ours, theirs)`` rows.

    ``theirs`` is updated in place to the rows the result must hold.
    """
    base, ours, theirs = rows
    for key in sorted({*base, *ours}, key=_order):
        was, now = base.get(key), ours.get(key)
        if was == now:
            continue
        held = theirs.get(key)
        if table == SEQUENCE_TABLE:
            if now is None or (held is not None and _seq(held) >= _seq(now)):
                continue
        elif held == now:
            continue
        elif held != was:
            conflicts.append(_conflict(table, key, was, now))
            continue
        kind = "delete" if now is None else "insert" if held is None else "update"
        writes.append(_Write(RowChange(table, key, kind), now))
        if now is None:
            del theirs[key]
        else:
            theirs[key] = now


def _same_schema(connections: Sequence[sqlite3.Connection]) -> None:
    """Raise :class:`MergeError` unless every database has one schema (no migration between)."""
    schemas = [_schema(connection) for connection in connections]
    if any(schema != schemas[0] for schema in schemas[1:]):
        msg = "the database schema differs (a migration); carve it by hand"
        raise MergeError(msg)


def _plan(base: Path, ours: Path, theirs: Path) -> _Plan:
    """Return the writes that put ``base`` -> ``ours`` onto ``theirs``, and the result's rows.

    Raises:
        MergeError: an input has a live journal, the schemas differ, a table cannot be
            keyed, or a row conflicts.

    """
    for path in (base, ours, theirs):
        journal = live_journal(path)
        if journal is not None:
            msg = (
                f"{journal.name} holds writes not yet in the database (a connection is open "
                "or was not checkpointed); close it and run `PRAGMA wal_checkpoint(TRUNCATE)`"
            )
            raise MergeError(msg)
    writes: list[_Write] = []
    expected: dict[str, Rows] = {}
    conflicts: list[str] = []
    connections: list[sqlite3.Connection] = []
    try:
        connections.extend(_open(path) for path in (base, ours, theirs))
        _same_schema(connections)
        for table in _tables(connections[0]):
            keyed = [_keyed_rows(connection, table) for connection in connections]
            _plan_table(table, (keyed[0], keyed[1], keyed[2]), writes, conflicts)
            expected[table] = keyed[2]
    except sqlite3.DatabaseError as error:
        msg = f"cannot be read as a SQLite database ({error}); carve it by hand"
        raise MergeError(msg) from None
    finally:
        for connection in connections:
            connection.close()
    if conflicts:
        named = conflicts[:NAMED_CONFLICTS]
        more = len(conflicts) - len(named)
        tail = f"; and {more} more" if more else ""
        msg = f"rows conflict with main: {'; '.join(named)}{tail}"
        raise MergeError(msg)
    return _Plan(writes, expected)


def _restore_sequence(connection: sqlite3.Connection, planned: Rows) -> None:
    """Put ``sqlite_sequence`` back to ``planned``: an insert at an explicit rowid moves it."""
    held = _keyed_rows(connection, SEQUENCE_TABLE)
    for name in held.keys() - planned.keys():
        _ = connection.execute("DELETE FROM sqlite_sequence WHERE name = ?", (name,))
    for name, row in planned.items():
        if held.get(name) == row:
            continue
        if name in held:
            _ = connection.execute(
                "UPDATE sqlite_sequence SET seq = ? WHERE name = ?",
                (row[1], name),
            )
        else:
            _ = connection.execute("INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)", row)


def _store(connection: sqlite3.Connection, writes: Sequence[_Write]) -> None:
    """Delete every changed row, then insert the copy's rows at their ``rowid``.

    ``sqlite_sequence`` is not written here: :func:`_restore_sequence` sets it after.
    """
    rows = [write for write in writes if write.change.table != SEQUENCE_TABLE]
    keys: dict[str, tuple[str, list[str]]] = {}
    for write in rows:
        table = write.change.table
        if table not in keys:
            columns = _columns(connection, table)
            keys[table] = (_key(table, columns), columns)
    for write in rows:
        if write.change.kind != "insert":
            table = write.change.table
            statement = _sql("DELETE FROM {table} WHERE {key} = ?", table, key=keys[table][0])
            _ = connection.execute(statement, (write.change.key,))
    for write in rows:
        if write.row is None:
            continue
        table = write.change.table
        key, columns = keys[table]
        statement = _sql(
            "INSERT INTO {table} ({key}, {columns}) VALUES ({marks})",
            table,
            columns,
            key,
        )
        try:
            _ = connection.execute(statement, (write.change.key, *write.row))
        except sqlite3.IntegrityError as error:
            msg = f"{table} rowid {write.change.key!r} breaks a constraint on main ({error})"
            raise MergeError(msg) from None


def _verify(connection: sqlite3.Connection, expected: Mapping[str, Rows]) -> None:
    """Raise :class:`MergeError` unless the result holds ``expected`` and passes the checks."""
    for table, rows in expected.items():
        if _keyed_rows(connection, table) != rows:
            msg = f"the merged database's {table} rows are not the planned ones; carve it by hand"
            raise MergeError(msg)
    integrity = _fetchall(connection.execute("PRAGMA integrity_check"))
    if integrity != [("ok",)]:
        msg = f"the merged database fails its integrity check: {integrity[:3]!r}"
        raise MergeError(msg)
    dangling = _fetchall(connection.execute("PRAGMA foreign_key_check"))
    if dangling:
        msg = f"the merged database has dangling foreign keys: {dangling[:3]!r}"
        raise MergeError(msg)


def _write_all(connection: sqlite3.Connection, plan: _Plan) -> None:
    """Store the plan's rows in one transaction with no trigger or foreign key acting."""
    _ = connection.execute("PRAGMA foreign_keys = OFF")
    _ = connection.execute("BEGIN")
    try:
        triggers = _fetchall(
            connection.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger'"),
        )
        for name, _definition in triggers:
            _ = connection.execute(f"DROP TRIGGER {_quote(str(name))}")
        _store(connection, plan.writes)
        if SEQUENCE_TABLE in plan.expected:
            _restore_sequence(connection, plan.expected[SEQUENCE_TABLE])
        for _name, definition in triggers:
            _ = connection.execute(str(definition))
    except BaseException:
        _ = connection.execute("ROLLBACK")
        raise
    _ = connection.execute("COMMIT")
    _verify(connection, plan.expected)


def merge(
    base: Path,
    ours: Path,
    theirs: Path,
    out: Path,
) -> list[RowChange]:
    """Write ``theirs`` plus the rows ``base`` -> ``ours`` changed to ``out``; return them.

    ``out`` starts as a byte copy of ``theirs``, so only the changed rows' pages move.
    An empty list means ``out`` holds exactly ``theirs``' rows.

    Raises:
        MergeError: ``out`` already exists (it is never touched then), as
            :func:`_plan`, or the result breaks a constraint, does not hold the
            planned rows, or fails the integrity or foreign-key check. An ``out``
            the merge made is removed on any failure.

    """
    if out.exists() or out.is_symlink():
        msg = f"{out} already exists; the merge writes only a new file"
        raise MergeError(msg)
    plan = _plan(base, ours, theirs)
    try:
        _ = shutil.copyfile(theirs, out)
        connection = sqlite3.connect(out, isolation_level=None)
        try:
            _write_all(connection, plan)
        finally:
            connection.close()
    except BaseException as error:
        out.unlink(missing_ok=True)
        if isinstance(error, sqlite3.Error):
            msg = f"writing the merged database failed ({error}); carve it by hand"
            raise MergeError(msg) from None
        raise
    return [write.change for write in plan.writes]
