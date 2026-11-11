"""Script tests for ``scripts/_sqlite_rows.py``, the row-level merge ``work.py land`` runs."""

from __future__ import annotations

import shutil
import sqlite3
from typing import TYPE_CHECKING

import pytest

from scripts import _sqlite_rows

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

#: ``sqlite3.Cursor.fetchall``, its rows typed for the caller.
_fetchall: Callable[[sqlite3.Cursor], list[tuple[object, ...]]] = sqlite3.Cursor.fetchall

SCHEMA = (
    "CREATE TABLE board (id integer PRIMARY KEY AUTOINCREMENT, title text NOT NULL UNIQUE)",
    (
        "CREATE TABLE term (id integer PRIMARY KEY AUTOINCREMENT, body text NOT NULL, "
        "board_id integer NOT NULL REFERENCES board (id))"
    ),
    "INSERT INTO board (id, title) VALUES (1, 'kanban'), (2, 'glossary')",
    "INSERT INTO term (id, body, board_id) VALUES (1, 'one', 1), (2, 'two', 1), (3, 'three', 2)",
)


def _run(path: Path, *statements: str) -> Path:
    connection = sqlite3.connect(path, isolation_level=None)
    for statement in statements:
        _ = connection.execute(statement)
    connection.close()
    return path


#: Each table's rows in ``rowid`` order.
READS = {
    "term": "SELECT * FROM term ORDER BY rowid",
    "sqlite_sequence": "SELECT * FROM sqlite_sequence ORDER BY rowid",
}


def _rows(path: Path, table: str) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(path)
    rows = _fetchall(connection.execute(READS[table]))
    connection.close()
    return rows


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return _run(tmp_path / "base.sqlite3", *SCHEMA)


def _fork(base: Path, name: str, *statements: str) -> Path:
    path = base.with_name(name)
    _ = shutil.copyfile(base, path)
    return _run(path, *statements)


def test_the_copys_inserts_updates_and_deletes_land_beside_mains_own_rows(base: Path) -> None:
    ours = _fork(
        base,
        "ours.sqlite3",
        "UPDATE term SET body = 'ONE' WHERE id = 1",
        "DELETE FROM term WHERE id = 3",
        "INSERT INTO term (body, board_id) VALUES ('four', 2)",
    )
    theirs = _fork(base, "theirs.sqlite3", "UPDATE term SET body = 'TWO' WHERE id = 2")
    out = base.with_name("out.sqlite3")
    changes = _sqlite_rows.merge(base, ours, theirs, out)
    assert _rows(out, "term") == [(1, "ONE", 1), (2, "TWO", 1), (4, "four", 2)]
    assert [(change.table, change.key, change.kind) for change in changes] == [
        ("sqlite_sequence", "term", "update"),
        ("term", 1, "update"),
        ("term", 3, "delete"),
        ("term", 4, "insert"),
    ]
    assert _rows(out, "sqlite_sequence") == [("board", 2), ("term", 4)]


def test_a_row_main_already_holds_as_the_copy_does_is_not_written(base: Path) -> None:
    edit = "UPDATE term SET body = 'ONE' WHERE id = 1"
    ours = _fork(base, "ours.sqlite3", edit)
    theirs = _fork(base, "theirs.sqlite3", edit)
    out = base.with_name("out.sqlite3")
    assert _sqlite_rows.merge(base, ours, theirs, out) == []
    assert out.read_bytes() == theirs.read_bytes()


def test_the_sequence_keeps_mains_larger_counter(base: Path) -> None:
    ours = _fork(base, "ours.sqlite3", "UPDATE sqlite_sequence SET seq = 5 WHERE name = 'term'")
    theirs = _fork(
        base,
        "theirs.sqlite3",
        "UPDATE sqlite_sequence SET seq = 9 WHERE name = 'term'",
    )
    out = base.with_name("out.sqlite3")
    assert _sqlite_rows.merge(base, ours, theirs, out) == []
    assert ("term", 9) in _rows(out, "sqlite_sequence")


@pytest.mark.parametrize(
    ("ours_edit", "theirs_edit", "named"),
    [
        (
            "UPDATE term SET body = 'mine' WHERE id = 1",
            "UPDATE term SET body = 'main' WHERE id = 1",
            "term rowid 1: changed here and on main",
        ),
        (
            "DELETE FROM term WHERE id = 1",
            "UPDATE term SET body = 'main' WHERE id = 1",
            "term rowid 1: deleted here and changed on main",
        ),
        (
            "INSERT INTO term (id, body, board_id) VALUES (9, 'mine', 1)",
            "INSERT INTO term (id, body, board_id) VALUES (9, 'main', 1)",
            "term rowid 9: inserted here and taken on main",
        ),
    ],
    ids=["update-update", "delete-update", "insert-insert"],
)
def test_a_row_both_sides_changed_is_a_conflict_and_nothing_is_written(
    base: Path,
    ours_edit: str,
    theirs_edit: str,
    named: str,
) -> None:
    ours = _fork(base, "ours.sqlite3", ours_edit)
    theirs = _fork(base, "theirs.sqlite3", theirs_edit)
    out = base.with_name("out.sqlite3")
    with pytest.raises(_sqlite_rows.MergeError, match=named):
        _ = _sqlite_rows.merge(base, ours, theirs, out)
    assert not out.exists()


def test_a_refusal_names_ten_conflicts_and_counts_the_rest(base: Path) -> None:
    insert = "INSERT INTO term (id, body, board_id) VALUES "
    keys = range(10, 22)
    ours = _fork(base, "ours.sqlite3", insert + ", ".join(f"({key}, 'mine', 1)" for key in keys))
    theirs = _fork(
        base,
        "theirs.sqlite3",
        insert + ", ".join(f"({key}, 'main', 1)" for key in keys),
    )
    with pytest.raises(_sqlite_rows.MergeError, match=r"; and 2 more$"):
        _ = _sqlite_rows.merge(base, ours, theirs, base.with_name("out.sqlite3"))


def test_a_deleted_parent_main_still_references_fails_the_foreign_key_check(base: Path) -> None:
    ours = _fork(
        base,
        "ours.sqlite3",
        "DELETE FROM term WHERE board_id = 2",
        "DELETE FROM board WHERE id = 2",
    )
    theirs = _fork(
        base,
        "theirs.sqlite3",
        "INSERT INTO term (id, body, board_id) VALUES (7, 'new', 2)",
    )
    out = base.with_name("out.sqlite3")
    with pytest.raises(_sqlite_rows.MergeError, match="dangling foreign keys"):
        _ = _sqlite_rows.merge(base, ours, theirs, out)
    assert not out.exists()


def test_a_row_breaking_a_unique_constraint_on_main_is_refused(base: Path) -> None:
    ours = _fork(base, "ours.sqlite3", "INSERT INTO board (id, title) VALUES (3, 'specs')")
    theirs = _fork(base, "theirs.sqlite3", "UPDATE board SET title = 'specs' WHERE id = 2")
    out = base.with_name("out.sqlite3")
    with pytest.raises(_sqlite_rows.MergeError, match="board rowid 3 breaks a constraint on main"):
        _ = _sqlite_rows.merge(base, ours, theirs, out)
    assert not out.exists()


def test_a_schema_change_is_not_merged_row_by_row(base: Path) -> None:
    ours = _fork(base, "ours.sqlite3", "ALTER TABLE term ADD COLUMN note text")
    with pytest.raises(_sqlite_rows.MergeError, match="schema differs"):
        _ = _sqlite_rows.merge(base, ours, base, base.with_name("out.sqlite3"))


def test_a_table_without_rowid_is_refused(tmp_path: Path) -> None:
    base = _run(tmp_path / "base.sqlite3", "CREATE TABLE pair (k text PRIMARY KEY) WITHOUT ROWID")
    ours = _fork(base, "ours.sqlite3", "INSERT INTO pair VALUES ('a')")
    with pytest.raises(_sqlite_rows.MergeError, match="cannot be read by rowid"):
        _ = _sqlite_rows.merge(base, ours, base, tmp_path / "out.sqlite3")


def test_a_generated_column_is_refused(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE sized (id integer PRIMARY KEY, body text, size integer AS (length(body)))",
    )
    ours = _fork(base, "ours.sqlite3", "INSERT INTO sized (id, body) VALUES (1, 'abc')")
    with pytest.raises(_sqlite_rows.MergeError, match="hidden or generated column"):
        _ = _sqlite_rows.merge(base, ours, base, tmp_path / "out.sqlite3")


def test_a_file_that_is_not_a_database_is_refused(tmp_path: Path) -> None:
    text = tmp_path / "text.sqlite3"
    _ = text.write_text("rows\n", encoding="utf-8")
    with pytest.raises(_sqlite_rows.MergeError, match="cannot be read as a SQLite database"):
        _ = _sqlite_rows.merge(text, text, text, tmp_path / "out.sqlite3")


def _read(path: Path, statement: str) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(path)
    rows = _fetchall(connection.execute(statement))
    connection.close()
    return rows


def test_no_trigger_fires_again_on_the_rows_it_already_wrote(tmp_path: Path) -> None:
    count = "BEGIN UPDATE audit SET n = n + 1 WHERE id = 1; END"
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE audit (id integer PRIMARY KEY, n integer)",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "INSERT INTO audit VALUES (1, 0)",
        "INSERT INTO source VALUES (1, 'base'), (2, 'gone')",
        f"CREATE TRIGGER on_insert AFTER INSERT ON source {count}",
        f"CREATE TRIGGER on_update AFTER UPDATE ON source {count}",
        f"CREATE TRIGGER on_delete AFTER DELETE ON source {count}",
    )
    ours = _fork(
        base,
        "ours.sqlite3",
        "UPDATE source SET body = 'ours' WHERE id = 1",
        "DELETE FROM source WHERE id = 2",
        "INSERT INTO source VALUES (3, 'new')",
    )
    out = tmp_path / "out.sqlite3"
    _ = _sqlite_rows.merge(base, ours, base, out)
    assert _read(out, "SELECT * FROM audit") == [(1, 3)]
    assert _read(out, "SELECT * FROM source ORDER BY id") == [(1, "ours"), (3, "new")]
    assert _read(out, "SELECT name FROM sqlite_master WHERE type = 'trigger' ORDER BY name") == [
        ("on_delete",),
        ("on_insert",),
        ("on_update",),
    ]


def test_a_column_named_rowid_does_not_hide_a_changed_row(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, rowid text, body text)",
        "INSERT INTO source VALUES (1, 'same', 'one'), (2, 'same', 'two')",
    )
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET body = 'ONE' WHERE _rowid_ = 1")
    out = tmp_path / "out.sqlite3"
    changes = _sqlite_rows.merge(base, ours, base, out)
    assert changes == [_sqlite_rows.RowChange("source", 1, "update")]
    assert _read(out, "SELECT _rowid_, * FROM source") == [
        (
            1,
            1,
            "same",
            "ONE",
        ),
        (
            2,
            2,
            "same",
            "two",
        ),
    ]


def test_a_table_shadowing_every_rowid_alias_is_refused(tmp_path: Path) -> None:
    base = _run(tmp_path / "base.sqlite3", "CREATE TABLE odd (rowid text, _rowid_ text, oid text)")
    with pytest.raises(_sqlite_rows.MergeError, match="columns named rowid, _rowid_ and oid"):
        _ = _sqlite_rows.merge(base, base, base, tmp_path / "out.sqlite3")


def test_a_database_with_a_live_wal_is_refused(base: Path) -> None:
    ours = _fork(base, "ours.sqlite3", "UPDATE term SET body = 'ONE' WHERE id = 1")
    theirs = _fork(base, "theirs.sqlite3")
    writer = sqlite3.connect(theirs)
    try:
        _ = writer.execute("PRAGMA journal_mode = WAL")
        _ = writer.execute("PRAGMA wal_autocheckpoint = 0")
        _ = writer.execute("UPDATE term SET body = 'TWO' WHERE id = 2")
        writer.commit()
        out = base.with_name("out.sqlite3")
        with pytest.raises(_sqlite_rows.MergeError, match=r"theirs\.sqlite3-wal holds writes"):
            _ = _sqlite_rows.merge(base, ours, theirs, out)
        assert not out.exists()
    finally:
        writer.close()


def test_a_unique_value_swap_lands(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text UNIQUE)",
        "INSERT INTO source VALUES (1, 'one'), (2, 'two')",
    )
    ours = _fork(
        base,
        "ours.sqlite3",
        "UPDATE source SET body = 'temporary' WHERE id = 1",
        "UPDATE source SET body = 'one' WHERE id = 2",
        "UPDATE source SET body = 'two' WHERE id = 1",
    )
    out = tmp_path / "out.sqlite3"
    _ = _sqlite_rows.merge(base, ours, base, out)
    assert _read(out, "SELECT * FROM source ORDER BY id") == [(1, "two"), (2, "one")]


def test_a_failed_write_removes_the_output_and_names_the_error(
    base: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ours = _fork(base, "ours.sqlite3", "UPDATE term SET body = 'ONE' WHERE id = 1")

    def fail(connection: sqlite3.Connection, writes: object) -> None:
        del connection, writes
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(_sqlite_rows, "_store", fail)
    out = base.with_name("out.sqlite3")
    with pytest.raises(
        _sqlite_rows.MergeError,
        match=r"writing the merged database failed \(disk I/O",
    ):
        _ = _sqlite_rows.merge(base, ours, base, out)
    assert not out.exists()


def test_a_path_with_uri_characters_is_read_as_that_file(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base#source?.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "INSERT INTO source VALUES (1, 'one')",
    )
    ours = _fork(base, "ours#source?.sqlite3", "UPDATE source SET body = 'ONE' WHERE id = 1")
    out = tmp_path / "out.sqlite3"
    _ = _sqlite_rows.merge(base, ours, base, out)
    assert _read(out, "SELECT * FROM source") == [(1, "ONE")]


def test_a_vacuum_without_an_integer_key_is_no_change(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (k text PRIMARY KEY, body text)",
        "INSERT INTO source (rowid, k, body) VALUES (3, 'a', 'one'), (8, 'b', 'two')",
    )
    ours = _fork(base, "ours.sqlite3", "VACUUM")
    assert _sqlite_rows.merge(base, ours, base, tmp_path / "out.sqlite3") == []


def test_a_deleted_and_reinserted_key_lands_beside_mains_row(base: Path) -> None:
    ours = _fork(
        base,
        "ours.sqlite3",
        "DELETE FROM term WHERE id = 2",
        "INSERT INTO term (id, body, board_id) VALUES (2, 'replacement', 1)",
    )
    theirs = _fork(base, "theirs.sqlite3", "UPDATE term SET body = 'ONE' WHERE id = 1")
    out = base.with_name("out.sqlite3")
    _ = _sqlite_rows.merge(base, ours, theirs, out)
    assert _rows(out, "term") == [(1, "ONE", 1), (2, "replacement", 1), (3, "three", 2)]


@pytest.fixture
def cascading(tmp_path: Path) -> Path:
    return _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE parent (id integer PRIMARY KEY, body text)",
        (
            "CREATE TABLE child (id integer PRIMARY KEY, "
            "parent_id integer REFERENCES parent (id) ON DELETE CASCADE)"
        ),
        "CREATE VIEW current_parents AS SELECT id, body FROM parent",
        "INSERT INTO parent VALUES (1, 'one'), (2, 'two')",
        "INSERT INTO child VALUES (1, 1), (2, 2)",
    )


def test_a_cascaded_delete_lands_as_its_rows_beside_mains(cascading: Path) -> None:
    ours = _fork(
        cascading,
        "ours.sqlite3",
        "PRAGMA foreign_keys = ON",
        "DELETE FROM parent WHERE id = 1",
    )
    theirs = _fork(cascading, "theirs.sqlite3", "UPDATE parent SET body = 'TWO' WHERE id = 2")
    out = cascading.with_name("out.sqlite3")
    _ = _sqlite_rows.merge(cascading, ours, theirs, out)
    assert _read(out, "SELECT * FROM current_parents") == [(2, "TWO")]
    assert _read(out, "SELECT * FROM child") == [(2, 2)]


def test_a_cascaded_delete_cannot_orphan_a_child_main_added(cascading: Path) -> None:
    ours = _fork(
        cascading,
        "ours.sqlite3",
        "PRAGMA foreign_keys = ON",
        "DELETE FROM parent WHERE id = 1",
    )
    theirs = _fork(cascading, "theirs.sqlite3", "INSERT INTO child VALUES (3, 1)")
    out = cascading.with_name("out.sqlite3")
    with pytest.raises(_sqlite_rows.MergeError, match="dangling foreign keys"):
        _ = _sqlite_rows.merge(cascading, ours, theirs, out)
    assert not out.exists()


def test_a_primary_key_update_keeps_the_planned_sequence(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY AUTOINCREMENT, body text)",
        "INSERT INTO source VALUES (1, 'one')",
    )
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET id = 100 WHERE id = 1")
    out = tmp_path / "out.sqlite3"
    _ = _sqlite_rows.merge(base, ours, base, out)
    assert _read(out, "SELECT * FROM source") == [(100, "one")]
    assert _read(out, "SELECT * FROM sqlite_sequence") == [("source", 1)]


def test_the_state_check_rejects_a_row_the_plan_did_not_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "INSERT INTO source VALUES (1, 'one'), (2, 'two')",
    )
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET body = 'ONE' WHERE id = 1")

    def extra_write(connection: sqlite3.Connection, writes: object) -> None:
        del writes
        _ = connection.execute("UPDATE source SET body = 'ONE' WHERE id = 1")
        _ = connection.execute("UPDATE source SET body = 'unplanned' WHERE id = 2")

    monkeypatch.setattr(_sqlite_rows, "_store", extra_write)
    out = tmp_path / "out.sqlite3"
    with pytest.raises(_sqlite_rows.MergeError, match="source rows are not"):
        _ = _sqlite_rows.merge(base, ours, base, out)
    assert not out.exists()


def test_a_repeated_sequence_name_is_refused(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY AUTOINCREMENT, body text)",
        "INSERT INTO source VALUES (1, 'one')",
        "INSERT INTO sqlite_sequence VALUES ('source', 99)",
    )
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET id = 100 WHERE id = 1")
    out = tmp_path / "out.sqlite3"
    with pytest.raises(_sqlite_rows.MergeError, match="sqlite_sequence repeats a table name"):
        _ = _sqlite_rows.merge(base, ours, base, out)
    assert not out.exists()


def test_an_existing_output_is_refused_and_left_as_it_was(tmp_path: Path) -> None:
    base = _run(tmp_path / "base.sqlite3", "CREATE TABLE source (id integer PRIMARY KEY)")
    out = _fork(base, "out.sqlite3")
    held = out.read_bytes()
    with pytest.raises(_sqlite_rows.MergeError, match="already exists"):
        _ = _sqlite_rows.merge(base, tmp_path / "missing.sqlite3", base, out)
    assert out.read_bytes() == held


def test_an_output_naming_an_input_never_touches_it(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "INSERT INTO source VALUES (1, 'one')",
    )
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET body = 'ONE'")
    before = base.read_bytes()
    with pytest.raises(_sqlite_rows.MergeError, match="already exists"):
        _ = _sqlite_rows.merge(base, ours, base, base)
    assert base.exists()
    assert base.read_bytes() == before


def test_recreated_triggers_fire_as_before_in_their_order(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "CREATE TABLE audit (id integer PRIMARY KEY, body text)",
        "INSERT INTO source VALUES (1, 'one')",
    )
    for statement in (
        (
            "CREATE TRIGGER z_first AFTER UPDATE ON source "
            "BEGIN INSERT INTO audit (body) VALUES ('z_first'); END"
        ),
        (
            "CREATE TRIGGER a_second AFTER UPDATE ON source "
            "BEGIN INSERT INTO audit (body) VALUES ('a_second'); END"
        ),
        (
            "CREATE TRIGGER m_third AFTER UPDATE ON source "
            "BEGIN INSERT INTO audit (body) VALUES ('m_third'); END"
        ),
    ):
        _ = _run(base, statement)
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET body = 'ours'")
    out = tmp_path / "out.sqlite3"
    _ = _sqlite_rows.merge(base, ours, base, out)
    triggers = "SELECT name FROM sqlite_master WHERE type = 'trigger'"
    assert _read(out, triggers) == _read(ours, triggers)
    _ = _run(ours, "UPDATE source SET body = 'next'")
    _ = _run(out, "UPDATE source SET body = 'next'")
    assert _read(out, "SELECT * FROM audit ORDER BY id") == _read(
        ours,
        "SELECT * FROM audit ORDER BY id",
    )


def test_an_explicit_insert_keeps_mains_higher_sequence(tmp_path: Path) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY AUTOINCREMENT, body text)",
        "INSERT INTO source VALUES (1, 'one')",
    )
    ours = _fork(base, "ours.sqlite3", "INSERT INTO source VALUES (500, 'ours')")
    theirs = _fork(
        base,
        "theirs.sqlite3",
        "INSERT INTO source VALUES (999, 'gone')",
        "DELETE FROM source WHERE id = 999",
    )
    out = tmp_path / "out.sqlite3"
    _ = _sqlite_rows.merge(base, ours, theirs, out)
    assert _read(out, "SELECT * FROM sqlite_sequence") == [("source", 999)]
    _ = _run(out, "INSERT INTO source (body) VALUES ('next')")
    assert _read(out, "SELECT id FROM source WHERE body = 'next'") == [(1000,)]


@pytest.mark.parametrize(
    "module",
    [
        "fts3",
        "fts4",
        "fts5",
        "rtree",
    ],
)
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged-virtual", "changed-virtual"])
def test_virtual_tables_merge_unchanged_or_refuse_with_no_output(
    tmp_path: Path,
    module: str,
    *,
    changed: bool,
) -> None:
    connection = sqlite3.connect(":memory:")
    try:
        modules = {row[0] for row in _fetchall(connection.execute("PRAGMA module_list"))}
    finally:
        connection.close()
    if module not in modules:
        pytest.skip(f"SQLite has no {module} module")
    spec = "id, lo, hi" if module == "rtree" else "body"
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "INSERT INTO source VALUES (1, 'one')",
        f"CREATE VIRTUAL TABLE search USING {module} ({spec})",
        (
            "INSERT INTO search VALUES (1, 0, 10)"
            if module == "rtree"
            else "INSERT INTO search (rowid, body) VALUES (1, 'alpha')"
        ),
    )
    edit = (
        "UPDATE search SET lo = 2 WHERE id = 1"
        if module == "rtree"
        else "UPDATE search SET body = 'beta' WHERE rowid = 1"
    )
    ours = _fork(
        base,
        "ours.sqlite3",
        edit if changed else "UPDATE source SET body = 'ONE'",
    )
    out = tmp_path / "out.sqlite3"
    if changed or module == "fts5":
        with pytest.raises(_sqlite_rows.MergeError):
            _ = _sqlite_rows.merge(base, ours, base, out)
        assert not out.exists()
    else:
        _ = _sqlite_rows.merge(base, ours, base, out)
        assert _read(out, "SELECT * FROM source") == [(1, "ONE")]
        assert _read(out, "SELECT * FROM search") == _read(base, "SELECT * FROM search")
        if module != "rtree":
            assert _read(out, "SELECT rowid FROM search WHERE search MATCH 'alpha'") == [(1,)]


@pytest.mark.parametrize("role", ["base", "ours", "theirs"])
@pytest.mark.parametrize("mode", ["WAL", "DELETE"])
def test_a_live_journal_is_refused_on_every_input(tmp_path: Path, role: str, mode: str) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "INSERT INTO source VALUES (1, 'one')",
    )
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET body = 'ONE'")
    theirs = _fork(base, "theirs.sqlite3")
    selected = {"base": base, "ours": ours, "theirs": theirs}[role]
    writer = sqlite3.connect(selected)
    try:
        _ = writer.execute(f"PRAGMA journal_mode = {mode}")
        _ = writer.execute("PRAGMA wal_autocheckpoint = 0")
        _ = writer.execute("UPDATE source SET body = 'live'")
        if mode == "WAL":
            writer.commit()
        out = tmp_path / "out.sqlite3"
        with pytest.raises(_sqlite_rows.MergeError, match="holds writes"):
            _ = _sqlite_rows.merge(base, ours, theirs, out)
        assert not out.exists()
    finally:
        writer.close()


@pytest.mark.parametrize("kind", ["symlink", "dangling", "hardlink"])
def test_an_output_link_is_refused_without_touching_it(tmp_path: Path, kind: str) -> None:
    base = _run(
        tmp_path / "base.sqlite3",
        "CREATE TABLE source (id integer PRIMARY KEY, body text)",
        "INSERT INTO source VALUES (1, 'one')",
    )
    ours = _fork(base, "ours.sqlite3", "UPDATE source SET body = 'ONE'")
    before = {path: path.read_bytes() for path in (base, ours)}
    out = tmp_path / "out.sqlite3"
    missing = tmp_path / "missing.sqlite3"
    if kind == "hardlink":
        out.hardlink_to(base)
    else:
        out.symlink_to(missing if kind == "dangling" else base)
    inode = out.lstat().st_ino
    with pytest.raises(_sqlite_rows.MergeError, match="already exists"):
        _ = _sqlite_rows.merge(base, ours, base, out)
    assert out.lstat().st_ino == inode
    assert out.is_symlink() == (kind != "hardlink")
    assert not missing.exists()
    assert {path: path.read_bytes() for path in before} == before
