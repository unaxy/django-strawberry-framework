"""Script tests for ``scripts/postgres_shards.py``, the Postgres tier's shard assignment.

Keeps the tier's partition exact: every collected test module runs in exactly
one ``postgres.yml`` shard, the workflow's matrix names exactly the script's
shards, the weighted split is deterministic and balanced, and the log reader
charges each module its workers' time. A live ``/graphql/`` request has no wire
shape for a CI shard assignment, so no row can move to
``examples/fakeshop/test_query/``.
"""

from pathlib import Path

import pytest

from scripts import postgres_shards
from tests._idioms import json_at, json_list, json_object
from tests._workflows import WORKFLOW_DIR, load_workflow, workflow_jobs


def test_the_shards_partition_every_collected_test_module_exactly_once() -> None:
    """The checked-in tree, weights and shard table leave no module unassigned or doubled."""
    assignment = postgres_shards.shards()

    assert postgres_shards.partition_problems(postgres_shards.REPO_ROOT, assignment) == []


def test_the_postgres_matrix_names_exactly_the_scripts_shards() -> None:
    """A shard the script adds but the matrix omits would leave its modules unrun."""
    job = workflow_jobs(load_workflow(WORKFLOW_DIR / "postgres.yml"))["test-postgres"]
    rows = [json_object(row) for row in json_list(json_at(job, "strategy", "matrix", "include"))]

    assert [row.get("shard") for row in rows] == list(postgres_shards.shards())
    assert [row for row in rows if "pytest_targets" in row] == []


def _tree(root: Path, files: list[str]) -> None:
    (root / "pytest.ini").write_text(
        "[pytest]\ntestpaths = suite\npython_files = test_*.py\n",
        encoding="utf-8",
    )
    for name in files:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")


def test_the_partition_check_names_an_unassigned_a_doubled_and_an_outside_module(
    tmp_path: Path,
) -> None:
    """Each way an assignment can miss the suite is reported by module."""
    _tree(
        tmp_path,
        [
            "suite/test_a.py",
            "suite/test_b.py",
            "suite/test_c.py",
            "suite/helper.py",
            "suite/__pycache__/test_cached.py",
            "suite/.hidden/test_hidden.py",
            "other/test_d.py",
        ],
    )
    assignment = {
        "one": ("suite/test_a.py", "suite/test_b.py"),
        "two": ("suite/test_b.py", "other/test_d.py"),
        "three": (),
    }

    assert postgres_shards.partition_problems(tmp_path, assignment) == [
        "shard three runs nothing",
        "suite/test_c.py is in no shard",
        "suite/test_b.py is in shards one, two",
        "other/test_d.py (shard two) is outside pytest.ini's testpaths",
    ]


def test_a_missing_shard_target_is_an_error(tmp_path: Path) -> None:
    """A renamed dedicated module fails the check instead of silently dropping its shard."""
    _tree(tmp_path, ["suite/test_a.py"])

    with pytest.raises(postgres_shards.ShardError, match=r"suite/test_gone\.py does not exist"):
        postgres_shards.partition_problems(tmp_path, {"one": ("suite/test_gone.py",)})


def test_the_split_puts_the_heaviest_module_on_the_lightest_bin_deterministically() -> None:
    """Longest-processing-time-first; an unweighed module takes the median weight."""
    weights = {
        "a": 9.0,
        "b": 5.0,
        "c": 4.0,
        "d": 3.0,
        "e": 1.0,
    }

    bins = postgres_shards.split(
        [
            "e",
            "new",
            "d",
            "c",
            "b",
            "a",
        ],
        weights,
        2,
    )

    # a=9 -> bin 0; b=5 -> 1; c=4 -> 1 (9); new=median 4 -> 0 (13); d=3 -> 1 (12); e=1 -> 1 (13).
    assert bins == [
        ["a", "new"],
        [
            "b",
            "c",
            "d",
            "e",
        ],
    ]
    assert (
        postgres_shards.split(
            reversed(
                [
                    "a",
                    "b",
                    "c",
                    "d",
                    "e",
                    "new",
                ],
            ),
            weights,
            2,
        )
        == bins
    )


def test_the_log_reader_charges_each_module_its_workers_time() -> None:
    """Each result is charged the time since that worker's previous result, or since start."""
    log = (
        "job\tRun Tests\t2026-01-01T00:00:00.0000000Z collecting ...\n"
        "job\tRun Tests\t2026-01-01T00:00:10.0000000Z 2 workers [3 items]\n"
        "job\tRun Tests\t2026-01-01T00:00:40.0000000Z [gw0] [ 33%] PASSED x/test_a.py\n"
        "job\tRun Tests\t2026-01-01T00:00:15.5000000Z [gw1] [ 66%] SKIPPED x/test_b.py\n"
        "job\tRun Tests\t2026-01-01T00:00:50.0000000Z [gw0] [100%] FAILED x/test_b.py\n"
    )

    assert postgres_shards.log_weights([log]) == {"x/test_a.py": 30.0, "x/test_b.py": 15.5}


def test_the_log_reader_refuses_a_log_without_its_workers_line() -> None:
    """A truncated log would charge nothing, so it is refused."""
    with pytest.raises(postgres_shards.ShardError, match="workers"):
        postgres_shards.log_weights(["2026-01-01T00:00:40Z [gw0] [ 33%] PASSED x/test_a.py"])


def test_paths_refuses_an_unknown_shard(capsys: pytest.CaptureFixture[str]) -> None:
    """A matrix row the script does not know fails its job instead of running nothing."""
    assert postgres_shards.main(["paths", "other-live-99"]) == 2
    assert "unknown shard 'other-live-99'" in capsys.readouterr().err


def test_paths_prints_one_path_per_line(capsys: pytest.CaptureFixture[str]) -> None:
    """The workflow word-splits the output into pytest arguments."""
    assert postgres_shards.main(["paths", "example-non-live"]) == 0
    assert capsys.readouterr().out == "examples/fakeshop/apps\nexamples/fakeshop/tests\n"
