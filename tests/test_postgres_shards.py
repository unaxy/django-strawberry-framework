"""Script tests for ``scripts/postgres_shards.py``, the Postgres tier's shard assignment.

Keeps the tier's partition exact: every module pytest collects runs in exactly
one ``postgres.yml`` shard, the module inventory follows pytest's own collection
rules, the workflow's matrix names exactly the script's shards and hands pytest
the paths unexpanded, the weighted split is deterministic and balanced, and the
log reader charges each module its workers' time and refuses an unfinished log.
A live ``/graphql/`` request has no wire shape for a CI shard assignment, so no
row can move to ``examples/fakeshop/test_query/``.
"""

from pathlib import Path

import pytest

from scripts import postgres_shards
from tests._idioms import json_at, json_list, json_object
from tests._workflows import WORKFLOW_DIR, job_steps, load_workflow, step_script, workflow_jobs


def _postgres_job() -> dict[object, object]:
    return workflow_jobs(load_workflow(WORKFLOW_DIR / "postgres.yml"))["test-postgres"]


def test_the_shards_partition_every_collected_test_module_exactly_once() -> None:
    """The checked-in tree and weights leave no collected module unassigned or doubled."""
    universe = postgres_shards.collected_modules(postgres_shards.REPO_ROOT)
    assignment = postgres_shards.shards(
        universe,
        postgres_shards.load_weights(postgres_shards.REPO_ROOT),
    )

    assert postgres_shards.partition_problems(universe, assignment) == []
    assert all(assignment[f"other-live-{index}"] for index in (1, 2, 3))


def test_the_postgres_matrix_names_exactly_the_scripts_shards() -> None:
    """A shard the script adds but the matrix omits would leave its modules unrun."""
    rows = [
        json_object(row)
        for row in json_list(json_at(_postgres_job(), "strategy", "matrix", "include"))
    ]
    universe = postgres_shards.collected_modules(postgres_shards.REPO_ROOT)
    assignment = postgres_shards.shards(
        universe,
        postgres_shards.load_weights(postgres_shards.REPO_ROOT),
    )

    assert [row.get("shard") for row in rows] == list(assignment)
    assert [row for row in rows if "pytest_targets" in row] == []


def test_the_postgres_run_step_passes_the_shard_paths_as_one_argument_each() -> None:
    """An unquoted expansion would glob a path such as ``test_case[12].py`` into other modules."""
    scripts = [
        step_script(step)
        for step in job_steps(_postgres_job())
        if step.get("name") == "Run Tests (Postgres)"
    ]

    assert len(scripts) == 1
    assert 'mapfile -t targets <<< "$listing"' in scripts[0]
    assert scripts[0].rstrip().endswith('"${targets[@]}"')


def _write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(text, encoding="utf-8")


def test_the_inventory_is_what_pytest_itself_collects(tmp_path: Path) -> None:
    """Path-bearing ``python_files``, ``norecursedirs`` and conftest ``collect_ignore`` all apply."""
    _write(
        tmp_path,
        {
            "pytest.ini": (
                "[pytest]\ntestpaths = suite\n"
                "python_files = test_*.py scenarios/*.py\nnorecursedirs = skipped\n"
            ),
            "suite/conftest.py": 'collect_ignore = ["test_ignored.py"]\n',
            "suite/test_a.py": "",
            "suite/scenarios/checkout.py": "",
            "suite/helper.py": "",
            "suite/test_ignored.py": "",
            "suite/skipped/test_skipped.py": "",
            "other/test_outside.py": "",
        },
    )

    assert postgres_shards.collected_modules(tmp_path) == {
        "suite/test_a.py",
        "suite/scenarios/checkout.py",
    }


def test_the_partition_check_names_an_unassigned_a_doubled_and_an_empty_path() -> None:
    """Each way an assignment can miss the collected modules is reported."""
    universe = {
        "suite/test_a.py",
        "suite/test_b.py",
        "suite/test_c.py",
        "suite/deep/test_d.py",
    }
    assignment = {
        "one": ("suite/test_a.py", "suite/deep"),
        "two": ("suite/test_a.py", "suite/test_gone.py"),
        "three": ("suite/test_b.py\nsuite/test_x.py",),
    }

    assert postgres_shards.partition_problems(universe, assignment) == [
        "shard two path suite/test_gone.py holds no collected module",
        "shard three path 'suite/test_b.py\\nsuite/test_x.py' holds a line break",
        "shard three path suite/test_b.py\nsuite/test_x.py holds no collected module",
        "suite/test_b.py is in no shard",
        "suite/test_c.py is in no shard",
        "suite/test_a.py is in shards one, two",
    ]


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


_HEADER = "job\tRun Tests\t2026-01-01T00:00:10.0000000Z 2 workers [3 items]\n"
_RESULTS = (
    "job\tRun Tests\t2026-01-01T00:00:40.0000000Z [gw0] [ 33%] PASSED x/test_a.py\n"
    "job\tRun Tests\t2026-01-01T00:00:15.5000000Z [gw1] [ 66%] SKIPPED x/test_b.py\n"
    "job\tRun Tests\t2026-01-01T00:00:50.0000000Z [gw0] [100%] FAILED x/test_b.py\n"
)
_SUMMARY = "job\tRun Tests\t2026-01-01T00:00:51.0000000Z ==== 1 failed, 2 passed in 41.00s ====\n"


def test_the_log_reader_charges_each_module_its_workers_time() -> None:
    """Each result is charged the time since that worker's previous result, or since start."""
    log = (
        "job\tRun Tests\t2026-01-01T00:00:00.0000000Z collecting ...\n"
        + _HEADER
        + _RESULTS
        + _SUMMARY
    )

    assert postgres_shards.log_weights([log]) == {"x/test_a.py": 30.0, "x/test_b.py": 15.5}


@pytest.mark.parametrize(
    ("log", "refusal"),
    [
        pytest.param(_RESULTS + _SUMMARY, "no xdist 'N workers \\[' line", id="no-workers-line"),
        pytest.param(_HEADER, "no test result line", id="header-only"),
        pytest.param(_HEADER + _SUMMARY, "no test result line", id="no-results"),
        pytest.param(_HEADER + _RESULTS, "ends before pytest's summary line", id="interrupted"),
    ],
)
def test_the_log_reader_refuses_an_unfinished_log(log: str, refusal: str) -> None:
    """A log that cannot have measured every module is refused, not read as light modules."""
    with pytest.raises(postgres_shards.ShardError, match=refusal):
        _ = postgres_shards.log_weights([_HEADER + _RESULTS + _SUMMARY, log])


def test_refresh_refuses_logs_that_measure_no_split_module(tmp_path: Path) -> None:
    """Logs of another shard would empty the weights; the file is left as it was."""
    weights = tmp_path / postgres_shards.WEIGHTS_FILE
    _write(
        tmp_path,
        {
            "pytest.ini": f"[pytest]\ntestpaths = {postgres_shards.LIVE_ROOT}\n",
            f"{postgres_shards.LIVE_ROOT}/test_other_api.py": "",
            postgres_shards.WEIGHTS_FILE: '{\n  "kept": 1\n}\n',
            "job.log": _HEADER + _RESULTS + _SUMMARY,
        },
    )

    with pytest.raises(postgres_shards.ShardError, match="measure no other-live module"):
        _ = postgres_shards.refresh(tmp_path, [tmp_path / "job.log"])
    assert weights.read_text(encoding="utf-8") == '{\n  "kept": 1\n}\n'


def test_paths_prints_one_path_per_line_and_refuses_an_unknown_shard(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The workflow reads one argument per line; a matrix row the script does not know fails its job."""
    assert postgres_shards.main(["paths", "example-non-live"]) == 0
    assert capsys.readouterr().out == "examples/fakeshop/apps\nexamples/fakeshop/tests\n"
    assert postgres_shards.main(["paths", "other-live-99"]) == 2
    assert "unknown shard 'other-live-99'" in capsys.readouterr().err
