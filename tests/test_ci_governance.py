"""Governance tests for CI workflows, Dependabot, install floors and first-party source.

Repo tooling: these rows pin YAML under ``.github/workflows/``, Dependabot
ecosystems, the first-party ``DjangoOptimizerExtension`` ``extensions=`` form
sweep, the live tier's undeclared raw ``.post(`` / ``.generic(`` sweep,
install-floor constants against ``pyproject.toml``, ``[tool.ruff]``'s exclusions
binding a path named to ``ruff format``, every staged ``TODO(spec-NNN ...)``
anchor against the spec corpus and ``KANBAN.md``, and the ``docs/SPECS/``
archive layout (specs and ``NEXT.md``, their companions in ``appx/``). A live
``/graphql/`` request has no wire shape for a workflow permission block, an
action SHA pin, a digest-pinned container image, a Dependabot ecosystem list, an
AST classifier over every committable ``.py``, a TOML dependency row, a ruff
exclusion, a source comment or a file's place in the spec archive, so none of
these rows can move. There is no live sibling in
``examples/fakeshop/test_query/``. Plan-cache reuse across HTTP requests on
the shipped schema lives in
``examples/fakeshop/test_query/test_library_api.py``; that row cannot audit
a forbidden ``extensions=`` form in any other file.

Coverage note: the assertions target YAML under ``.github/`` and the text of
first-party ``.py`` files, not ``django_strawberry_framework``'s runtime
behavior, so this module adds no package coverage surface.
"""

import ast
import io
import re
import shutil
import subprocess
import sys
import tokenize
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TypeAlias

import pytest
import tomli
import yaml

import django_strawberry_framework
from django_strawberry_framework.utils.imports import (
    CHANNELS_FLOOR,
    CRYPTOGRAPHY_FLOOR,
    DEBUG_TOOLBAR_FLOOR,
    DRF_FLOOR,
    STRAWBERRY_FLOOR,
)
from django_strawberry_framework.utils.typing import object_result
from scripts import _git

# The repo-wide Python sweep below borrows this repo's existing definition of the
# first-party source trees rather than re-listing them, so the two cannot drift
# apart. Its exact scope is the four trees named by ``check_citations``'s
# ``SOURCE_TREES``, which is NOT literally every first-party .py: three tracked
# modules (``conftest.py``, ``line_count.py``, ``docs/dry/export_dry_review.py``)
# sit outside those trees, so ``EXTRA_SOURCE_FILES`` below adds them back and the
# corpus census pins the union against git. Walking the trees rather than the
# filesystem also excludes the gitignored ``docs/*/temp-tests/`` scratch by
# construction, so the gate cannot pass in a clean CI checkout and fail on a
# developer machine.
from scripts.check_citations import SOURCE_TREES, iter_python_sources, spec_files
from tests._idioms import (
    is_object_dict,
    is_object_list,
    json_at,
    json_list,
    json_loads,
    json_object,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

# A reviewed, immutable pin is a full 40-character commit SHA. A tag -- ``@v6``,
# ``@v6.1.0``, ``@main`` -- is mutable by definition, so the action's contents can
# change under a pin that still reads the same.
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
IMAGE_REFERENCE = re.compile(
    r"\b(postgres|ghcr\.io/[\w./-]+)(:[\w.-]+|@sha256:[0-9a-f]{64})",
)

# Local composite actions (``./.github/actions/...``) are part of this repository
# and therefore already covered by the commit under review.
LOCAL_ACTION_PREFIX = "./"

# A YAML mapping's keys are not all strings: the bare ``on:`` trigger key parses as ``True``.
_YAMLMapping: TypeAlias = "dict[object, object]"


def _workflow_paths() -> list[Path]:
    paths = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))
    assert paths, f"no workflow files found under {WORKFLOW_DIR}"
    return paths


def _load(path: Path) -> object:
    """Parse one YAML file into its untyped node tree."""
    return object_result(yaml.safe_load, path.read_text(encoding="utf-8"))


def _workflow(path: Path) -> _YAMLMapping:
    """Parse one workflow file, which is a mapping at its root."""
    workflow = _load(path)
    assert is_object_dict(workflow), f"{path.name}: workflow is not a mapping"
    return workflow


def _mapping(node: object) -> _YAMLMapping:
    """Read a YAML node as a mapping; an absent or empty node reads as an empty one."""
    if not node:
        return {}
    assert is_object_dict(node), f"expected a YAML mapping, got {node!r}"
    return node


WORKFLOW_PATHS = _workflow_paths()
WORKFLOW_IDS = [path.name for path in WORKFLOW_PATHS]


def _jobs(workflow: _YAMLMapping) -> _YAMLMapping:
    return _mapping(workflow.get("jobs"))


def _steps(job: _YAMLMapping) -> list[object]:
    steps = job.get("steps")
    if not steps:
        return []
    assert is_object_list(steps), f"expected a YAML sequence of steps, got {steps!r}"
    return steps


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_workflow_parses(path: Path) -> None:
    """Every workflow is loadable YAML with at least one job."""
    workflow = _workflow(path)
    assert _jobs(workflow), f"{path.name}: declares no jobs"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_workflow_declares_top_level_read_only_permissions(path: Path) -> None:
    """Each workflow pins a read-only default GITHUB_TOKEN scope.

    Without an explicit block the token inherits the repository default, which
    may be write-all. Declaring ``contents: read`` at the top level makes any
    wider grant an explicit, reviewable job-level override.
    """
    workflow = _workflow(path)
    permissions = workflow.get("permissions")
    assert permissions == {"contents": "read"}, (
        f"{path.name}: top-level permissions must be exactly "
        f"{{'contents': 'read'}}, got {permissions!r}"
    )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_no_job_grants_repository_write(path: Path) -> None:
    """No job may grant ``contents: write``.

    Nothing in this repository's CI pushes commits, tags, or releases. A
    ``contents: write`` grant would therefore be unused authority handed to every
    step in the job, including third-party actions and the dependency tree they
    install.
    """
    workflow = _workflow(path)
    for name, job in _jobs(workflow).items():
        permissions = _mapping(job).get("permissions")
        if not is_object_dict(permissions):
            continue
        assert permissions.get("contents") != "write", (
            f"{path.name}: job {name!r} grants contents: write; no CI job here "
            "pushes to the repository"
        )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_every_job_declares_a_timeout(path: Path) -> None:
    """Every job bounds its own wall-clock time.

    Each job here either installs dependencies from the network or runs the test
    suite. Without ``timeout-minutes`` a hung download or a deadlocked test holds
    a runner for GitHub's six-hour default.
    """
    workflow = _workflow(path)
    for name, node in _jobs(workflow).items():
        job = _mapping(node)
        if "uses" in job:
            # A reusable-workflow call cannot set timeout-minutes; the timeout
            # belongs to the jobs inside the called workflow.
            continue
        timeout = job.get("timeout-minutes")
        problem = f"{path.name}: job {name!r} has no positive timeout-minutes (got {timeout!r})"
        assert isinstance(timeout, int), problem
        assert timeout > 0, problem


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_every_job_declares_a_runner(path: Path) -> None:
    """Every job says what it runs on, so the whole file stays schedulable.

    ``runs-on`` is required. Omitting it does not fail the one job: GitHub
    refuses to parse the workflow, so a push that should have run reports an
    invalid-file error and nothing runs at all. The timeout pin on the same job
    cannot see this: a job that lost ``runs-on`` while keeping
    ``timeout-minutes`` still satisfies that row.
    """
    workflow = _workflow(path)
    for name, node in _jobs(workflow).items():
        job = _mapping(node)
        if "uses" in job:
            # A reusable-workflow call names no runner; the called workflow's own
            # jobs declare theirs, exactly as they declare their timeouts.
            continue
        runs_on = job.get("runs-on")
        assert runs_on, f"{path.name}: job {name!r} declares no runs-on (got {runs_on!r})"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_every_external_action_is_pinned_to_a_full_commit_sha(path: Path) -> None:
    """Third-party and first-party actions alike are pinned by commit SHA.

    ``actions/checkout@v6`` re-resolves on every run, so the code executing in
    CI is whatever the tag points at today. A full-SHA pin is the only immutable
    reference GitHub offers.
    """
    workflow = _workflow(path)
    for name, job in _jobs(workflow).items():
        for index, step in enumerate(_steps(_mapping(job))):
            uses = _mapping(step).get("uses")
            if not uses:
                continue
            assert isinstance(uses, str), (
                f"{path.name}: job {name!r} step {index} 'uses' is {uses!r}"
            )
            if uses.startswith(LOCAL_ACTION_PREFIX):
                continue
            _, separator, reference = uses.partition("@")
            assert separator, f"{path.name}: job {name!r} step {index} 'uses: {uses}' has no ref"
            assert FULL_SHA.match(reference), (
                f"{path.name}: job {name!r} step {index} pins {uses!r} to a "
                "mutable ref; use a full 40-character commit SHA with a "
                "trailing '# vX.Y.Z' comment"
            )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_pinned_actions_keep_a_readable_version_comment(path: Path) -> None:
    """A SHA pin carries a ``# vX.Y.Z`` comment so a reader can tell what it is.

    Asserted against the raw text, because YAML parsing discards comments.
    """
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- uses:") and not stripped.startswith("uses:"):
            continue
        _, _, value = stripped.partition("uses:")
        value = value.strip()
        if value.startswith(LOCAL_ACTION_PREFIX):
            continue
        _, separator, reference = value.partition("@")
        if not separator or not FULL_SHA.match(reference.split()[0].strip('"')):
            continue
        assert "#" in value, f"{path.name}: SHA-pinned {value!r} has no version comment"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_checkout_steps_do_not_persist_credentials(path: Path) -> None:
    """No checkout persists its credential into ``.git/config``.

    ``actions/checkout`` writes an extraheader credential by default, leaving a
    usable token in the workspace for every later step. No job here pushes, so
    the credential has no consumer and only widens the blast radius of a
    compromised dependency.
    """
    workflow = _workflow(path)
    for name, job in _jobs(workflow).items():
        for index, step in enumerate(_steps(_mapping(job))):
            uses = _mapping(step).get("uses") or ""
            assert isinstance(uses, str), (
                f"{path.name}: job {name!r} step {index} 'uses' is {uses!r}"
            )
            if not uses.startswith("actions/checkout@"):
                continue
            options = _mapping(_mapping(step).get("with"))
            assert options.get("persist-credentials") is False, (
                f"{path.name}: job {name!r} step {index} checks out without "
                "'persist-credentials: false'"
            )


def _workflow_image_references(path: Path) -> list[re.Match[str]]:
    executable = "\n".join(
        line.split("#", 1)[0] for line in path.read_text(encoding="utf-8").splitlines()
    )
    return list(IMAGE_REFERENCE.finditer(executable))


def test_workflow_container_images_are_present() -> None:
    """At least one workflow file contains a container image reference."""
    total_images = sum(len(_workflow_image_references(path)) for path in WORKFLOW_PATHS)
    assert total_images > 0


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_container_images_are_pinned_by_digest(path: Path) -> None:
    """Every container image started by a workflow is digest-pinned.

    A ``postgres:16`` tag is rebuilt upstream and silently becomes a different
    image; only a ``@sha256:`` digest names one reviewed image. Matched over the
    workflow text -- images appear in ``run:`` scripts and ``services:`` blocks
    alike -- with comments stripped first, so prose naming a tag is not mistaken
    for a reference that actually starts a container.
    """
    for match in _workflow_image_references(path):
        name, reference = match.group(1), match.group(2)
        assert reference.startswith("@sha256:"), (
            f"{path.name}: image {name}{reference} is tag-pinned; pin it by @sha256: digest"
        )


def test_dependabot_covers_python_and_github_actions() -> None:
    """Dependabot keeps both the Python resolution and the action SHAs current.

    The ``github-actions`` entry is what stops full-SHA pins from going stale:
    an immutable pin never picks up an upstream fix on its own.
    """
    config = _load(REPO_ROOT / ".github" / "dependabot.yml")
    ecosystems = {json_at(entry, "package-ecosystem") for entry in json_list(config, "updates")}
    assert {"uv", "github-actions"} <= ecosystems, (
        f"dependabot.yml must cover the 'uv' and 'github-actions' ecosystems, got {ecosystems}"
    )


def test_dependency_audit_workflow_runs_on_pull_request_and_a_schedule() -> None:
    """The audit is both diff-triggered and clock-triggered.

    A PR-only audit cannot see a vulnerability published against a dependency
    that is already locked; a schedule-only audit lets one merge first.
    """
    workflow = _workflow(WORKFLOW_DIR / "dependency-audit.yml")
    triggers = _mapping(workflow[True] if True in workflow else workflow["on"])
    assert "pull_request" in triggers, "dependency audit must run on pull requests"
    assert triggers.get("schedule"), "dependency audit must run on a schedule"


@pytest.mark.parametrize("name", ["django.yml", "postgres.yml"])
def test_vendor_and_full_matrix_tiers_run_on_a_schedule(name: str) -> None:
    """The full Django matrix and the Postgres tier also run weekly with no commit.

    Every run installs the newest Django patch release, so upstream drift can
    break either tier while the repository stays still.
    """
    workflow = _workflow(WORKFLOW_DIR / name)
    triggers = _mapping(workflow[True] if True in workflow else workflow["on"])
    assert triggers.get("schedule"), f"{name} must run on a schedule"


def test_the_scheduled_django_run_selects_the_full_matrix() -> None:
    """A scheduled Django CI run takes the dispatch matrix, not the two push cells."""
    workflow = _workflow(WORKFLOW_DIR / "django.yml")
    matrix = _mapping(_mapping(_mapping(_mapping(workflow["jobs"])["test"])["strategy"])["matrix"])
    assert "github.event_name == 'schedule'" in str(matrix["include"])


def _environment_name(job: _YAMLMapping) -> object:
    """Return a job's environment name, from the bare or the mapping spelling."""
    environment = job.get("environment")
    return _mapping(environment).get("name") if is_object_dict(environment) else environment


def test_publish_workflow_keeps_the_trusted_publisher_binding() -> None:
    """``publish.yml`` publishes on a version tag from the ``pypi`` environment.

    PyPI's trusted publisher names this file and this environment, so either
    rename silently breaks the next release. The upload stays the one job here
    holding ``id-token: write`` (the token PyPI exchanges for an upload
    credential), behind the build that checked the tag against ``__version__``.
    """
    workflow = _workflow(WORKFLOW_DIR / "publish.yml")
    triggers = _mapping(workflow[True] if True in workflow else workflow["on"])
    assert set(triggers) == {"push"}, f"publish.yml must run on tag pushes only, got {triggers}"
    assert _mapping(triggers["push"]).get("tags") == ["v*"], "publish.yml must run on v* tags"
    minting = {
        name: _mapping(job)
        for name, job in _jobs(workflow).items()
        if _mapping(_mapping(job).get("permissions")).get("id-token") == "write"
    }
    assert list(minting) == ["publish"], f"exactly one job mints the token, got {list(minting)}"
    publish = minting["publish"]
    assert _environment_name(publish) == "pypi"
    assert publish.get("needs") == "build"
    actions = [_mapping(step).get("uses") or "" for step in _steps(publish)]
    assert any(str(uses).startswith("pypa/gh-action-pypi-publish@") for uses in actions)


# ---------------------------------------------------------------------------
# Standing pin: no active .py may construct a schema with a forbidden
# DjangoOptimizerExtension ``extensions=`` form (spec-029 Decision 3).
# ---------------------------------------------------------------------------

OPTIMIZER_EXTENSION = "DjangoOptimizerExtension"

#: The corrective form, quoted in every failure message.
OPTIMIZER_FIX = f"optimizer = {OPTIMIZER_EXTENSION}(...) then extensions=[lambda: optimizer]"


def _forbidden_optimizer_entries(source: str, label: str) -> list[tuple[int, str, str]]:
    """Yield ``(lineno, form, snippet)`` per forbidden optimizer ``extensions=`` entry.

    Takes source TEXT plus a label rather than a path, so the control rows below
    can feed it literal snippets - the controls are what pin the classifier, and
    a path-only signature would make them impossible to write.

    Two rules, matched on FORM rather than on a literal spelling (a spelling
    match is blind to variants: a grep for ``lambda: DjangoOptimizerExtension()``
    misses every ``strictness=`` / ``nested_connection_strategy=`` variant):

    1. any ``lambda`` whose body constructs the optimizer;
    2. any bare optimizer class load that is an ELEMENT of a list or tuple
       literal and is not itself the callee of a call.

    Both rules share one test for "this expression is the optimizer class": the
    bare name, any attribute whose leaf is the class name (``dsf.DjangoOptimizerExtension``,
    ``pkg.sub.DjangoOptimizerExtension``), or a name the module binds with
    ``from ... import DjangoOptimizerExtension as <alias>``.
    """
    tree = ast.parse(source, filename=label)
    class_names = {OPTIMIZER_EXTENSION}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            class_names.update(
                alias.asname
                for alias in node.names
                if alias.name == OPTIMIZER_EXTENSION and alias.asname
            )

    def is_optimizer_class(node: ast.expr) -> bool:
        if isinstance(node, ast.Name):
            return node.id in class_names and isinstance(node.ctx, ast.Load)
        return (
            isinstance(node, ast.Attribute)
            and node.attr == OPTIMIZER_EXTENSION
            and isinstance(node.ctx, ast.Load)
        )

    call_funcs = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    # A subscript's tuple (``tuple[DjangoSchema, DjangoOptimizerExtension]``) is a type
    # expression, never an ``extensions=`` value.
    type_arguments = {id(node.slice) for node in ast.walk(tree) if isinstance(node, ast.Subscript)}
    sequence_elements: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)) and id(node) not in type_arguments:
            sequence_elements.update(id(element) for element in node.elts)
    found: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            body = node.body
            if isinstance(body, ast.Call) and (
                OPTIMIZER_EXTENSION in ast.unparse(body.func) or is_optimizer_class(body.func)
            ):
                found.append((node.lineno, "constructing lambda", ast.unparse(node)))
        if (
            isinstance(node, ast.expr)
            and is_optimizer_class(node)
            and id(node) not in call_funcs
            and id(node) in sequence_elements
        ):
            found.append((node.lineno, "bare class in a sequence", ast.unparse(node)))
    return sorted(found)


# Positive controls. A sweep instrument dies silently on shape drift, and a
# control that did not run reads identically to a passing proof - so every form
# the classifier claims to catch is exhibited here as a row of its own.
MUST_FLAG_SNIPPETS = [
    ("bare-single", "schema = Schema(query=Q, extensions=[DjangoOptimizerExtension])"),
    ("bare-tuple", "schema = Schema(query=Q, extensions=(DjangoOptimizerExtension,))"),
    (
        "bare-multi-element",
        "schema = Schema(query=Q, extensions=[DjangoDebugExtension, DjangoOptimizerExtension])",
    ),
    (
        "bare-multiline",
        "schema = Schema(\n    query=Q,\n    extensions=[\n        DjangoOptimizerExtension,\n    ],\n)",
    ),
    ("bare-assigned-to-a-variable", "extensions = [DjangoOptimizerExtension]"),
    (
        "lambda-no-args",
        "schema = Schema(query=Q, extensions=[lambda: DjangoOptimizerExtension()])",
    ),
    (
        "lambda-with-kwargs",
        'schema = Schema(query=Q, extensions=[lambda: DjangoOptimizerExtension(strictness="raise")])',
    ),
    (
        "lambda-in-a-conditional-expression",
        "extensions = [lambda: DjangoOptimizerExtension()] if optimizer else []",
    ),
    ("lambda-dotted", "extensions = [lambda: optimizer.DjangoOptimizerExtension()]"),
    ("attribute-package-alias", "extensions = [dsf.DjangoOptimizerExtension]"),
    (
        "attribute-package-dotted",
        "extensions = [django_strawberry_framework.DjangoOptimizerExtension]",
    ),
    (
        "attribute-subpackage-dotted",
        "extensions = [django_strawberry_framework.optimizer.DjangoOptimizerExtension]",
    ),
    ("attribute-tuple", "extensions = (DjangoDebugExtension, dsf.DjangoOptimizerExtension)"),
    (
        "import-alias-bare",
        (
            "from django_strawberry_framework import DjangoOptimizerExtension as Opt\n"
            "extensions = [Opt]"
        ),
    ),
    (
        "import-alias-lambda",
        (
            "from django_strawberry_framework import DjangoOptimizerExtension as Opt\n"
            "extensions = [lambda: Opt()]"
        ),
    ),
    (
        "bare-tuple-beside-a-type-argument",
        (
            "def build() -> tuple[Schema, DjangoOptimizerExtension]:\n"
            "    return Schema(query=Q, extensions=(DjangoOptimizerExtension,)), None"
        ),
    ),
]

# Negative controls. Each is a form that LOOKS like the violation to a
# vocabulary-shaped sweep and is not one. Two are load-bearing: the debug
# extension's own docstring REQUIRES the bare class and forbids a pre-built
# instance, and the error-policy extension's says the two forms behave
# identically. A rule that flagged every bare-class entry would break the first.
MUST_NOT_FLAG_SNIPPETS = [
    ("factory-over-a-singleton", "extensions = [lambda: ext]"),
    ("factory-over-a-module-singleton", "extensions = [lambda: _optimizer]"),
    ("bare-debug-extension", "extensions = [DjangoDebugExtension]"),
    ("bare-error-policy-extension", "extensions = [DjangoErrorPolicyExtension]"),
    (
        "lambda-constructing-another-extension",
        "extensions = [lambda: DjangoDebugExtension(allow_unsafe_production=True)]",
    ),
    ("subclass-declaration", "class _CaptureExt(DjangoOptimizerExtension):\n    pass"),
    ("classmethod-call", "DjangoOptimizerExtension.check_schema(schema)"),
    ("identity-assertion", "assert DjangoOptimizerExtension is Other"),
    ("bare-instance-assignment", "ext = DjangoOptimizerExtension()\nextensions = [ext]"),
    ("attribute-classmethod-call", "dsf.DjangoOptimizerExtension.check_schema(schema)"),
    ("attribute-debug-extension", "extensions = [dsf.DjangoDebugExtension]"),
    ("attribute-instance-assignment", "ext = dsf.DjangoOptimizerExtension()\nextensions = [ext]"),
    ("attribute-identity-assertion", "assert dsf.DjangoOptimizerExtension is Other"),
    ("tuple-type-argument", "def build() -> tuple[Schema, DjangoOptimizerExtension]: ..."),
    (
        "attribute-tuple-type-argument",
        "optimizers: dict[str, tuple[dsf.DjangoOptimizerExtension, int]] = {}",
    ),
]


@pytest.mark.parametrize(
    "snippet",
    [snippet for _, snippet in MUST_FLAG_SNIPPETS],
    ids=[name for name, _ in MUST_FLAG_SNIPPETS],
)
def test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape(snippet: str) -> None:
    """Each forbidden shape the sweep claims to catch is exhibited as its own row.

    These rows are the sweep's positive control. Without them the sweep can go
    green because the corpus is clean OR because the classifier stopped matching
    anything at all, and those two readings are indistinguishable from a passing
    run.
    """
    assert _forbidden_optimizer_entries(snippet, "<must-flag>"), (
        f"the forbidden-form classifier no longer flags this shape:\n{snippet}"
    )


@pytest.mark.parametrize(
    "snippet",
    [snippet for _, snippet in MUST_NOT_FLAG_SNIPPETS],
    ids=[name for name, _ in MUST_NOT_FLAG_SNIPPETS],
)
def test_forbidden_optimizer_form_classifier_ignores_the_permitted_shapes(snippet: str) -> None:
    """The negative control: only the optimizer's own two forbidden forms match.

    ``DjangoDebugExtension``'s docstring REQUIRES the bare class and forbids a
    pre-built instance; ``DjangoErrorPolicyExtension``'s says a bare class and a
    factory behave identically. Only the optimizer carries the shared
    instance-bound plan cache, so only the optimizer is in scope, and widening
    this rule to every bare-class entry would break a documented contract.
    """
    assert _forbidden_optimizer_entries(snippet, "<must-not-flag>") == [], (
        f"the forbidden-form classifier now over-flags this permitted shape:\n{snippet}"
    )


#: Tracked first-party modules that live OUTSIDE ``check_citations``'s source
#: trees. Without them the sweep would stop at those four trees while claiming
#: every first-party module, and the repo-root ``conftest.py`` is a plausible
#: home for a shared schema fixture. The census below is what keeps this tuple
#: honest: a new ``.py`` outside the trees fails that row by name instead of
#: silently sitting outside the gate.
EXTRA_SOURCE_FILES = ("conftest.py", "docs/dry/export_dry_review.py", "line_count.py")

#: Files whose presence in the corpus the forbidden-form gate's answer rests on:
#: the optimizer's own module, the module that defines the corpus, one file per
#: source tree, the file added by ``EXTRA_SOURCE_FILES``, and the modules that
#: construct a schema with the optimizer. Named individually so a narrowed
#: corpus fails by saying WHICH files left, and so the failure survives a
#: machine without git.
CORPUS_REACH_FILES = (
    "conftest.py",
    "django_strawberry_framework/optimizer/extension.py",
    "examples/fakeshop/strategy_schemas.py",
    "examples/fakeshop/test_query/test_products_visibility_api.py",
    "scripts/check_citations.py",
    "tests/forms/test_resolvers.py",
    "tests/mutations/test_resolvers.py",
    "tests/mutations/test_write_transaction.py",
    "tests/optimizer/test_extension.py",
    "tests/test_relay_connection.py",
    "tests/types/test_resolvers.py",
)

#: This module's own repo-relative path, derived rather than written down so a
#: rename cannot strand it. The census's oracle is asked about the checkout that
#: is executing this file, so an answer omitting it is not an answer about this
#: repository at all.
CENSUS_MODULE = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

#: What any coherent ``git ls-files`` answer must report. The census subtracts the
#: sweep's corpus FROM this answer, so an answer enumerating nothing makes that
#: subtraction empty for EVERY corpus and the row can never fail again - and git
#: gives exactly that answer, at exit 0 and with no error to detect, whenever it
#: runs against a directory that is untracked-and-ignored inside an enclosing
#: repository (an export or vendored copy unpacked under another repo's ignored
#: path). Guard the ANSWER, not one spelling of the incoherent input: ``assert
#: answer`` refuses only the totally empty case while a partially enumerated one
#: walks straight through it, so the requirement is named files - this module,
#: plus every file the gate's answer already rests on.
ORACLE_REQUIRED_FILES = (CENSUS_MODULE, *CORPUS_REACH_FILES)

#: The one corpus region that is not a source tree: the tracked modules
#: ``EXTRA_SOURCE_FILES`` carries back in from outside them all. A label rather
#: than a path, so it can never be mistaken for one.
EXTRA_FILES_REGION = "outside-the-source-trees"

#: Every region the sweep's corpus is assembled from, in the vocabulary the
#: requirement above has to reach: this module, each source tree, and the files
#: outside them all. Derived from ``SOURCE_TREES`` and ``EXTRA_SOURCE_FILES``
#: instead of written down again - a fourth hardcoded list would need a fourth
#: thing to contradict it, which is the regress the rows below exist to end.
CORPUS_REGIONS = (CENSUS_MODULE, *SOURCE_TREES, EXTRA_FILES_REGION)


def _sweep_corpus() -> tuple[Path, ...]:
    """Return every first-party ``.py`` file the forbidden-form sweep reads."""
    extra = (REPO_ROOT / name for name in EXTRA_SOURCE_FILES)
    return tuple(sorted({*iter_python_sources(), *(path for path in extra if path.is_file())}))


def _committable_python_files() -> set[str]:
    """Return the ``.py`` paths a commit here could contain, repo-relative.

    ``--cached --others --exclude-standard`` is exactly "tracked, plus untracked
    but not ignored". It is an oracle for "first-party source" derived from git
    rather than from the sweep's own tree list, which is what makes the census
    below a measurement instead of a restatement of the corpus by itself. Read
    through ``scripts/_git.py``, so "ignored" is the repository's own rules and
    never the caller's global excludes or XDG ignore file.

    Three ways git can fail to answer, and none may reduce the census to nothing.
    A missing ``git`` raises here; a non-zero exit trips the assert below; and an
    exit-0 answer that enumerates nothing - what git returns when run against a
    directory that is untracked-and-ignored inside an enclosing repository - is
    refused by the caller through ``_unreported_required_files``. That third one
    reports no error of any kind: it is a coherent-LOOKING answer that happens to
    be wrong, which is the class no return code can catch.
    """
    completed = _git.run_git(
        REPO_ROOT,
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
        "--",
        "*.py",
    )
    assert completed.returncode == 0, (
        f"git ls-files failed ({completed.returncode}); the corpus census cannot "
        f"be taken without it: {completed.stderr.strip()}"
    )
    return {name for name in completed.stdout.split("\0") if name}


def _unreported_required_files(answer: Iterable[str]) -> list[str]:
    """Return the paths a coherent oracle answer must carry that ``answer`` lacks.

    A pure function over one git answer, so the control rows below can feed it
    answers the live tree cannot produce - an empty one, a truncated one. A guard
    whose whole job is to refuse an answer has no other exercise: while git
    answers correctly here, nothing would ever run the refusing branch, and a
    guard that never ran reads exactly like a guard that found nothing.
    """
    return sorted(set(ORACLE_REQUIRED_FILES) - set(answer))


def _unrepresented_corpus_regions(required: Iterable[str]) -> list[str]:
    """Return the corpus regions ``required`` names no file inside.

    ``ORACLE_REQUIRED_FILES`` is the only hardcoded tuple this gate reads that
    feeds assertions without also feeding an answer: the census subtracts it, the
    reach rows iterate it, and nothing measures it - so halving it deletes rows in
    silence rather than failing one. This is its contradictor, and it writes down
    no data of its own, deriving what the requirement must reach from the two
    definitions the census already disagrees with.

    A pure function over one requirement tuple, so the rows below can feed it the
    narrowed requirements the shipped module never holds. A region is reached when
    the requirement names this module, a file inside that tree, or one of the
    modules carried in from outside every tree.
    """
    named = set(required)
    unrepresented = [] if CENSUS_MODULE in named else [CENSUS_MODULE]
    unrepresented.extend(
        tree for tree in SOURCE_TREES if not any(name.startswith(f"{tree}/") for name in named)
    )
    if not named.intersection(EXTRA_SOURCE_FILES):
        unrepresented.append(EXTRA_FILES_REGION)
    return unrepresented


def _forbidden_entries_in(paths: Iterable[Path]) -> list[str]:
    """Return one formatted violation string per forbidden entry found in ``paths``.

    Split out of the sweep so the find-and-format path can be exercised against a
    synthetic corpus. Once the sweep is green the live tree contains no violation
    by construction, so nothing else here would run this formatting - and a
    reporter that had stopped formatting anything would read exactly like a clean
    tree.
    """
    violations: list[str] = []
    for path in paths:
        display = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        violations.extend(
            f"{display}:{lineno}: {form}: {snippet}"
            for lineno, form, snippet in _forbidden_optimizer_entries(
                path.read_text(encoding="utf-8"),
                str(path),
            )
        )
    return violations


def test_the_sweep_corpus_covers_every_committable_python_file() -> None:
    """The corpus the gate walks is the corpus it claims to walk.

    ``for path in <corpus>`` then ``assert not violations`` is green both when the
    corpus is CLEAN and when the corpus has silently NARROWED - the fail-open
    shape where "cannot enumerate" becomes "permit". No other row here can tell
    those two readings apart: the classifier's control rows are fed literal
    snippets and never touch the corpus, and the sweep itself passes hardest when
    it sees nothing at all.

    Measured, not argued: dropping ``"tests"`` from ``check_citations``'s
    ``SOURCE_TREES`` removes the test tree from the sweep while
    ``check_citations`` itself stays green, because no citation happens to
    point into the files that left.

    Only the missing direction is asserted. A path the corpus holds and git does
    not list (local scratch inside a source tree) makes the gate stricter, never
    blinder; asserting equality instead would fail on a developer machine while
    passing in CI.

    The same fail-open shape one level up is why the oracle is checked before it
    is believed: this row subtracts the corpus FROM git's answer, so an answer
    that enumerates nothing leaves nothing missing whatever the corpus holds, and
    the row stops being able to fail. Checking that the answer carries the files
    it must carry is what keeps ``not missing`` a measurement.
    """
    committable = _committable_python_files()
    unreported = _unreported_required_files(committable)
    assert not unreported, (
        f"git enumerated {len(committable)} .py file(s) but not "
        + ", ".join(unreported)
        + " - so it did not answer about this repository (it reports nothing, at "
        "exit 0, when run inside an enclosing repo's ignored path) and the census "
        "below could not tell a complete corpus from an empty one"
    )
    swept = {str(path.relative_to(REPO_ROOT)) for path in _sweep_corpus()}
    missing = sorted(committable - swept)
    assert not missing, (
        f"{len(missing)} committable .py file(s) are outside the forbidden-form "
        "sweep's corpus, so the gate cannot see them:\n"
        + "\n".join(missing)
        + "\nAdd the tree to check_citations.SOURCE_TREES, or the file to "
        "EXTRA_SOURCE_FILES."
    )


#: Answers no coherent oracle can give, each paired with a path it should have
#: reported. The last three are the load-bearing rows: a non-empty check accepts
#: all of them, which is why the guard requires named files rather than a size.
INCOHERENT_ORACLE_ANSWERS = [
    ("enumerates-nothing", (), CENSUS_MODULE),
    ("only-this-module", (CENSUS_MODULE,), "conftest.py"),
    ("only-one-load-bearing-file", ("conftest.py",), CENSUS_MODULE),
    ("every-load-bearing-file-but-this-module", CORPUS_REACH_FILES, CENSUS_MODULE),
]


@pytest.mark.parametrize(
    ("answer", "expected"),
    [(answer, expected) for _, answer, expected in INCOHERENT_ORACLE_ANSWERS],
    ids=[name for name, _, _ in INCOHERENT_ORACLE_ANSWERS],
)
def test_the_corpus_census_refuses_an_incoherent_oracle_answer(
    answer: Iterable[str],
    expected: str,
) -> None:
    """An under-enumerating oracle is refused by name, not by size.

    These are the answers the live tree cannot produce, so nothing else here runs
    the refusing branch. Both halves matter: an empty answer is what git returns
    at exit 0 from inside an enclosing repository's ignored path, and a truncated
    answer is what a bare ``assert answer`` would wave through while the census it
    feeds silently stops measuring.
    """
    assert expected in _unreported_required_files(answer), (
        f"an oracle answer of {sorted(answer)} was accepted as complete even "
        f"though it does not report {expected}"
    )


def test_the_corpus_census_accepts_a_complete_oracle_answer() -> None:
    """The guard's negative direction: a complete answer is not refused."""
    assert _unreported_required_files(ORACLE_REQUIRED_FILES) == []


@pytest.mark.parametrize("region", CORPUS_REGIONS, ids=CORPUS_REGIONS)
def test_the_oracle_requirement_reaches_every_corpus_region(region: str) -> None:
    """What the oracle must report stays as wide as the corpus it is asked about.

    Narrowing ``CORPUS_REACH_FILES`` deletes reach rows instead of failing one,
    and a side-effect of another row's literal is not a contract. These rows
    assert the structural property the requirement exists to hold - this module,
    every tree the corpus is walked from, and the modules carried in from
    outside them - so a narrowing fails by naming the region it cost. Not a
    count and not a copy of the tuple: a count gets "fixed" to the new number,
    and a copy is one more list needing a contradictor of its own.
    """
    assert region not in _unrepresented_corpus_regions(ORACLE_REQUIRED_FILES), (
        f"ORACLE_REQUIRED_FILES names nothing in {region}, so a corpus that lost "
        f"{region} entirely would still satisfy the census's oracle guard"
    )


#: Requirements too narrow to be a requirement, each paired with a region it
#: stops reaching. Built from the region vocabulary itself, so they keep narrowing
#: in a real direction if the corpus definitions later move.
NARROWED_REQUIREMENTS = [
    ("names-nothing", (), CENSUS_MODULE),
    ("only-this-module", (CENSUS_MODULE,), EXTRA_FILES_REGION),
    ("only-outside-the-trees", EXTRA_SOURCE_FILES, CENSUS_MODULE),
    (
        "every-tree-but-nothing-outside-them",
        (CENSUS_MODULE, *(f"{tree}/anything.py" for tree in SOURCE_TREES)),
        EXTRA_FILES_REGION,
    ),
    (
        "every-region-but-one-tree",
        (
            CENSUS_MODULE,
            *EXTRA_SOURCE_FILES,
            *(f"{tree}/anything.py" for tree in SOURCE_TREES[1:]),
        ),
        SOURCE_TREES[0],
    ),
]


@pytest.mark.parametrize(
    ("required", "expected"),
    [(required, expected) for _, required, expected in NARROWED_REQUIREMENTS],
    ids=[name for name, _, _ in NARROWED_REQUIREMENTS],
)
def test_a_narrowed_oracle_requirement_names_the_region_it_lost(
    required: Iterable[str],
    expected: str,
) -> None:
    """A requirement that stopped covering a region is refused, by region.

    The refusing direction of the guard above, which the shipped requirement can
    never exercise: while ``ORACLE_REQUIRED_FILES`` is wide enough, nothing runs
    the branch that reports a region as unreached, and a branch that never ran
    reads exactly like one that found nothing.
    """
    assert expected in _unrepresented_corpus_regions(required), (
        f"a requirement of {sorted(required)} was accepted as reaching the whole "
        f"corpus even though it names nothing in {expected}"
    )


@pytest.mark.parametrize("relative", CORPUS_REACH_FILES, ids=CORPUS_REACH_FILES)
def test_the_sweep_corpus_reaches_each_load_bearing_file(relative: str) -> None:
    """Each file the gate's answer depends on is inside the corpus, by name.

    The census above catches any narrowing; these rows say which files a
    narrowing cost, and they hold without git. Two instruments rather than one
    written twice: different oracle, different failure text, and a whole-tree
    drop fails several of these at once.
    """
    assert REPO_ROOT / relative in _sweep_corpus(), (
        f"{relative} is not in the forbidden-form sweep's corpus; the gate's "
        "answer does not cover it"
    )


@pytest.mark.parametrize(
    ("entry", "form"),
    [
        ("extensions=[DjangoOptimizerExtension]", "bare class in a sequence"),
        (
            'extensions=[lambda: DjangoOptimizerExtension(strictness="raise")]',
            "constructing lambda",
        ),
    ],
    ids=["bare-class", "constructing-lambda"],
)
def test_the_sweep_reports_a_planted_violation_with_its_file_and_line(
    tmp_path: Path,
    entry: str,
    form: str,
) -> None:
    """The find-and-format path is pinned independently of the live tree.

    The sweep's own row can only ever report success while the repository is
    clean, so the code that finds a violation and formats it into a readable
    location has no other exercise. A synthetic one-file corpus gives it one.
    """
    planted = tmp_path / "planted_schema.py"
    planted.write_text(f"# a planted corpus\n# line two\nschema = Schema(query=Q, {entry})\n")
    reported = _forbidden_entries_in([planted])
    assert len(reported) == 1, f"expected one violation from the planted file, got {reported}"
    assert reported[0].startswith(f"{planted}:3: {form}: "), reported[0]


def test_the_sweep_reports_nothing_for_a_planted_permitted_form(tmp_path: Path) -> None:
    """The reporter's negative direction: a clean file yields no violation."""
    planted = tmp_path / "planted_schema.py"
    planted.write_text(
        "optimizer = DjangoOptimizerExtension()\nextensions = [lambda: optimizer]\n",
    )
    assert _forbidden_entries_in([planted]) == []


def test_no_active_source_uses_a_forbidden_optimizer_extensions_form() -> None:
    """No first-party ``.py`` builds a schema with a cold-cached optimizer.

    Two forms are forbidden (spec-029 Decision 3): the bare class
    ``extensions=[DjangoOptimizerExtension]`` and any constructing lambda
    ``extensions=[lambda: DjangoOptimizerExtension(...)]``. Strawberry's
    ``Schema.get_extensions`` runs each non-instance entry ONCE PER OPERATION, in
    both sync and async modes, so both forms hand every request a brand-new
    extension - and the optimizer's plan cache lives on the instance
    (``self._plan_cache``), giving it a structurally zero hit rate. The fix is a
    factory over a singleton scoped to that construction site:
    ``ext = DjangoOptimizerExtension(...)`` then ``extensions=[lambda: ext]``.

    Deliberate limits, considered rather than missed. The pin does NOT match the
    deprecated instance form ``extensions=[DjangoOptimizerExtension()]`` (already
    fatal at runtime, since Strawberry's ``DeprecationWarning`` meets
    ``pytest.ini``'s ``filterwarnings = error``), a SUBCLASS entry spelled under
    another name, a rebinding (``Opt = DjangoOptimizerExtension``), a ``getattr``
    lookup, a set literal, or a named module-level function that constructs the
    optimizer; all but the set literal would need name resolution and none exists
    here. Qualified spellings (any attribute whose leaf is the class name) and
    ``from ... import DjangoOptimizerExtension as <alias>`` names ARE matched, by
    both rules.

    Its false-positive direction is deliberate too, and BOTH arms have one. The
    bare-class rule flags the class in ANY list or tuple literal, not only in an
    ``extensions=`` argument, so a future ``for cls in [DjangoOptimizerExtension,
    ...]:`` would trip it; only a subscript's tuple (a ``tuple[..., ...]``
    annotation) is exempt. The lambda rule matches the optimizer's name as a
    SUBSTRING of the unparsed callee, so a dotted spelling
    (``lambda: optimizer.DjangoOptimizerExtension()``) is caught on purpose and an
    affixed one (``lambda: MyDjangoOptimizerExtensionWrapper()``) is caught as a
    side effect. A false positive here is one loud, one-line-to-fix failure; a
    false negative is the rot this pin exists to stop. Repair the rule rather than
    deleting the test.

    What this row CANNOT see is its own corpus: it is green over an empty one.
    ``test_the_sweep_corpus_covers_every_committable_python_file`` and the
    per-file reach rows above are what make its silence mean something.
    """
    violations = _forbidden_entries_in(_sweep_corpus())
    assert not violations, (
        "forbidden DjangoOptimizerExtension extensions= form(s) in active source:\n"
        + "\n".join(violations)
        + f"\nUse a factory over a singleton scoped to that construction site: {OPTIMIZER_FIX}"
    )


#: A staged-slice anchor (``AGENTS.md #"staged-but-unbuilt slices get a source-site"``):
#: ``TODO(spec-NNN ...)``, bare or with a slice tail in either case. Group ``number`` is
#: the spec number, which is the KANBAN card number.
STAGED_ANCHOR = re.compile(r"TODO\(spec-(?P<number>\d{3})\b[^)]*\)", re.IGNORECASE)

KANBAN_PATH = REPO_ROOT / "KANBAN.md"

#: One ``## Card index`` row of the rendered board, which lists every scheduled card.
#: ``KANBAN.md`` is the board read without a database: CI's ``build_kanban_md.py
#: --check`` holds it byte-equal to the kanban app's rows.
CARD_INDEX_ROW = re.compile(
    r"^\| \[`(?P<card>[A-Z]+(?:-[A-Z]+)?-(?P<number>\d{3})-[0-9.]+)`\]",
    re.MULTILINE,
)

#: One card heading in the rendered board's column bodies.
CARD_HEADING = re.compile(r"^### \[(?P<card>[A-Z]+(?:-[A-Z]+)?-\d{3}-[0-9.]+) - ", re.MULTILINE)

#: The workflow-state prefix the card ID format gives a shipped card.
DONE_PREFIX = "DONE-"


def _board_cards(board: str) -> dict[str, str]:
    """Return ``{card number: card id}`` for every row of the board's card index."""
    return {match["number"]: match["card"] for match in CARD_INDEX_ROW.finditer(board)}


def _stale_staged_anchors(paths: Iterable[Path], cards: dict[str, str]) -> list[str]:
    """Return one formatted violation per staged anchor in ``paths`` that names no open spec.

    An anchor is stale when no spec carries its number, when the board has no card
    with that number, or when that card is done: a shipped spec's staged slice
    either shipped and kept its anchor, or never will under that spec. A pure
    function over a corpus and a board, so the rows below can feed it planted files
    the live tree never holds.
    """
    violations: list[str] = []
    for path in paths:
        display = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, start=1):
            for match in STAGED_ANCHOR.finditer(line):
                number = match["number"]
                card = cards.get(number)
                if not spec_files(number):
                    reason = f"no docs/spec-{number}-*.md or docs/SPECS/spec-{number}-*.md exists"
                elif card is None:
                    reason = f"no card {number} is on the board"
                elif card.startswith(DONE_PREFIX):
                    reason = f"card {card} is done"
                else:
                    continue
                violations.append(f"{display}:{lineno}: {match[0]}: {reason}")
    return violations


def _live_board_cards() -> dict[str, str]:
    """Return the live board's card index (see ``_board_cards``)."""
    return _board_cards(KANBAN_PATH.read_text(encoding="utf-8"))


def test_the_board_card_index_lists_every_card_heading() -> None:
    """The card-index parse reads every scheduled card the board renders.

    The anchor sweep looks a card up in ``_board_cards``, so a parse that narrowed
    (a reformatted index row the pattern stops matching) would report a live card
    as missing or, worse, miss the ``DONE-`` row that should have failed an anchor.
    The column bodies' headings are a second rendering of the same card set,
    matched by a different pattern.
    """
    board = KANBAN_PATH.read_text(encoding="utf-8")
    headings = {match["card"] for match in CARD_HEADING.finditer(board)}
    assert headings, "no card heading parsed from KANBAN.md"
    assert set(_board_cards(board).values()) == headings


def test_every_staged_todo_anchor_names_an_open_spec() -> None:
    """Every ``TODO(spec-NNN ...)`` in first-party source names a spec whose card is open.

    A staged slice's anchor is ``AGENTS.md #"removed in the change that ships the slice"``.
    Nothing else reads the anchors, so one left behind outlives its spec, or names a
    spec that was renumbered away, and reads as planned work forever. Documentation
    prose quoting the anchor form is outside the corpus: only ``.py`` sources are
    read, the corpus the census rows above pin against git.
    """
    violations = _stale_staged_anchors(_sweep_corpus(), _live_board_cards())
    assert not violations, (
        "staged TODO(spec-NNN ...) anchor(s) naming no open spec:\n"
        + "\n".join(violations)
        + "\nRemove the anchor with the slice that shipped it, or retarget it at the "
        "spec or BACKLOG entry that now owns the work."
    )


def _done_card_with_a_spec(cards: dict[str, str]) -> str:
    """Return the number of a done card that has a spec, read from the live board."""
    numbers = sorted(n for n, card in cards.items() if card.startswith(DONE_PREFIX))
    found = next((number for number in numbers if spec_files(number)), None)
    assert found is not None, "no done card on the board has a spec to plant against"
    return found


def _open_card_with_a_spec(cards: dict[str, str]) -> str:
    """Return the number of an open card that has a spec, read from the live board."""
    numbers = sorted(n for n, card in cards.items() if not card.startswith(DONE_PREFIX))
    found = next((number for number in numbers if spec_files(number)), None)
    assert found is not None, "no open card on the board has a spec to plant against"
    return found


def _number_without_a_spec() -> str:
    """Return the lowest three-digit number no spec carries."""
    return next(f"{n:03d}" for n in range(1, 1000) if not spec_files(f"{n:03d}"))


def _plant(tmp_path: Path, number: str, tail: str) -> Path:
    """Write a one-anchor corpus file; the anchor is assembled so this module holds none."""
    planted = tmp_path / "planted_anchor.py"
    anchor = "TODO(spec-" + number + tail + ")"
    planted.write_text(f"# a planted corpus\n# {anchor}: wire the slice\nVALUE = 1\n")
    return planted


@pytest.mark.parametrize("tail", ["", " slice 1", " Slice 2"], ids=["bare", "slice", "Slice"])
def test_the_anchor_sweep_reports_an_anchor_naming_a_done_card(tmp_path: Path, tail: str) -> None:
    """An anchor whose spec exists but whose card shipped is reported, in every spelling."""
    cards = _live_board_cards()
    number = _done_card_with_a_spec(cards)
    reported = _stale_staged_anchors([_plant(tmp_path, number, tail)], cards)
    assert len(reported) == 1, reported
    assert reported[0].endswith(f": card {cards[number]} is done"), reported[0]
    assert reported[0].startswith(f"{tmp_path / 'planted_anchor.py'}:2: "), reported[0]


def test_the_anchor_sweep_reports_an_anchor_naming_no_spec(tmp_path: Path) -> None:
    """An anchor whose number no spec carries is reported."""
    number = _number_without_a_spec()
    reported = _stale_staged_anchors([_plant(tmp_path, number, " slice 1")], _live_board_cards())
    assert len(reported) == 1, reported
    assert f"no docs/spec-{number}-*.md" in reported[0], reported[0]


def test_the_anchor_sweep_reports_a_spec_with_no_card(tmp_path: Path) -> None:
    """An anchor whose spec exists but whose number has no card on the board is reported."""
    cards = _live_board_cards()
    number = _done_card_with_a_spec(cards)
    without = {n: card for n, card in cards.items() if n != number}
    reported = _stale_staged_anchors([_plant(tmp_path, number, " slice 1")], without)
    location = f"{tmp_path / 'planted_anchor.py'}:2"
    assert reported == [
        f"{location}: TODO(spec-{number} slice 1): no card {number} is on the board",
    ]


def test_the_anchor_sweep_accepts_an_anchor_naming_an_open_spec(tmp_path: Path) -> None:
    """The sweep's negative direction: an anchor on an open card's spec is not reported."""
    cards = _live_board_cards()
    number = _open_card_with_a_spec(cards)
    assert _stale_staged_anchors([_plant(tmp_path, number, " Slice 1")], cards) == []


#: The package directory whose non-statement strings the provenance and release
#: sweeps also read.
PACKAGE_ROOT = REPO_ROOT / "django_strawberry_framework"

#: The process-provenance phrases START.md "Style the maintainer cares about" bans
#: from comments, docstrings, test names and error strings, each with the pattern
#: that finds it.
#: Every one reads as the history of a change in every hit the corpus has held, so
#: the set carries no exclusion: a sentence that needs the words is rephrased.
#: Words are joined by any whitespace, so a phrase a docstring wraps across lines,
#: or a block of full-line comments wraps, still matches; a def or class name is
#: read with its underscores as spaces.
#: ``scripts/review_inspect.py::PROVENANCE_PATTERNS`` is a separate, wider word
#: list: a lead flag in a report a reviewer reads by hand, where a false positive
#: costs a glance; here every hit fails CI, so the set holds no false positive.
PROVENANCE_PHRASES: tuple[tuple[str, str], ...] = (
    ("pre-fix", r"pre[-\s]+fix"),
    ("post-fix", r"post[-\s]+fix"),
    ("before the fix", r"before\s+the\s+fix"),
    ("after the fix", r"after\s+the\s+fix"),
    ("formerly", r"formerly"),
    ("exactly as before", r"exactly\s+as\s+before"),
    ("used to", r"used\s+to"),
    ("previously", r"previously"),
    ("as of 0.0.", r"as\s+of\s+0\.0\."),
    ("the hardening pass", r"the\s+hardening\s+pass"),
    ("(hardened)", r"\(hardened\)"),
    ("(hardening)", r"\(hardening\)"),
    ("pre-0.0.", r"pre-0\.0\."),
    ("the old implementation", r"the\s+old\s+implementation"),
    ("the previous implementation", r"the\s+previous\s+implementation"),
    ("task report", r"task\s+report"),
    ("finding-", r"finding-"),
    ("pre-033", r"pre-\d{3}"),
    ("pre-1.0", r"pre-1\.0"),
    ("back-compat", r"back(?:wards?)?[-\s]+compat\w*"),
    ("independently grew", r"independently\s+grew"),
    ("grew separately", r"grew\s+separately"),
    ("historically", r"historically"),
    ("byte-unchanged", r"byte[-\s]+unchanged"),
    ("moved verbatim", r"moved\s+verbatim"),
    ("net-new", r"net[-\s]+new"),
    ("now-fixed", r"now[-\s]+fixed"),
    ("the original implementation", r"the\s+original\s+implementation"),
)


def _phrase_alternative(index: int, phrase: str, pattern: str) -> str:
    """Return ``pattern`` as named group ``p<index>`` between word edges.

    No letter, digit, underscore or hyphen may precede the phrase, and no word
    character may follow it unless the phrase itself ends on punctuation (a
    version prefix such as ``0.0.`` runs straight into its digits).
    """
    tail = r"(?!\w)" if phrase[-1].isalnum() else ""
    return rf"(?P<p{index}>(?<![\w-]){pattern}{tail})"


#: One case-insensitive alternation over ``PROVENANCE_PHRASES``.
PROVENANCE_PATTERN = re.compile(
    "|".join(
        _phrase_alternative(index, phrase, pattern)
        for index, (phrase, pattern) in enumerate(PROVENANCE_PHRASES)
    ),
    re.IGNORECASE,
)


def _prose_segments(source: str) -> list[tuple[int, str, str]]:
    """Return ``(first line, kind, text)`` for every comment, docstring and def/class name.

    Every string statement is read as a docstring wherever it sits: the first
    statement of a module, class or function body, an attribute docstring after
    an assignment, a later string statement, one inside an ``if`` / ``try`` /
    ``with`` / loop body. An f-string statement is read as its literal parts
    joined. A run of full-line comments on consecutive lines is one segment,
    joined by newlines, so a phrase the block wraps is still one match; a
    trailing comment is a segment of its own and never joins the full-line
    comment below it. A string that is not a statement (an error message, an
    assigned constant, fixture data) is not read.
    """
    segments: list[tuple[int, str, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segments.append((node.lineno, "name", node.name.replace("_", " ")))
        if not isinstance(node, ast.Expr):
            continue
        value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            segments.append((node.lineno, "docstring", value.value))
        elif isinstance(value, ast.JoinedStr):
            # A replacement field separates the parts, so no phrase matches across it.
            text = "\x00".join(
                part.value
                for part in value.values
                if isinstance(part, ast.Constant) and isinstance(part.value, str)
            )
            segments.append((node.lineno, "docstring", text))
    block: list[str] = []
    start = last = 0
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        full = not token.line[: token.start[1]].strip()
        text = token.string.lstrip("#").lstrip(":").strip()
        if full and block and last and line == last + 1:
            block.append(text)
            last = line
            continue
        if block:
            segments.append((start, "comment", "\n".join(block)))
        block, start, last = [text], line, line if full else 0
    if block:
        segments.append((start, "comment", "\n".join(block)))
    return segments


def _swept_texts(path: Path, source: str, package_root: Path) -> list[tuple[int, str, str]]:
    """Return ``(first line, kind, text)`` for every text the sweeps read in ``source``.

    Every file contributes its comments, string statements and def/class names
    (``_prose_segments``); a file under ``package_root`` also contributes its
    runtime strings (``_runtime_strings``, kind ``string``), the value assigned to
    ``__version__`` in the package's ``__init__.py`` excepted.
    """
    texts = _prose_segments(source)
    if path.is_relative_to(package_root):
        version_file = path == package_root / "__init__.py"
        texts.extend(
            (line, "string", text)
            for line, text in _runtime_strings(source, version_file=version_file)
        )
    return texts


def _provenance_entries_in(
    paths: Iterable[Path],
    package_root: Path = PACKAGE_ROOT,
) -> tuple[list[str], int]:
    """Return one formatted violation per gated phrase in ``paths``, and the texts read.

    Each violation names the file, the line the phrase starts on, the kind of text
    it sits in and the phrase. The text count is what lets the sweep tell a clean
    corpus from one it could not read.
    """
    violations: list[str] = []
    read = 0
    for path in paths:
        display = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        source = path.read_text(encoding="utf-8")
        for first_line, kind, text in _swept_texts(path, source, package_root):
            read += 1
            for match in PROVENANCE_PATTERN.finditer(text):
                phrase = PROVENANCE_PHRASES[int((match.lastgroup or "p0")[1:])][0]
                line = first_line + text.count("\n", 0, match.start())
                violations.append(f"{display}:{line}: {kind}: {phrase!r}: {match[0]!r}")
    return violations, read


def test_no_comment_docstring_name_or_package_string_carries_a_provenance_phrase() -> None:
    """No first-party comment, docstring, def/class name or package string narrates history.

    START.md "Style the maintainer cares about": comments, docstrings, test names
    and error strings state the invariant, never how the change came to be. This
    row is that rule's gate for the phrase set ``PROVENANCE_PHRASES`` names, over the corpus
    the census rows above pin against git, plus every other ``str`` constant in
    ``django_strawberry_framework/`` (runtime messages, as the release sweep below
    reads them). A sentence a phrase lands in is restated as behaviour: a
    counterfactual becomes a present-tense or conditional statement the enclosing
    test asserts.

    Deliberate limits. Only those phrases are read; the wider history vocabulary
    ("now", "no longer", "the fix", version banners) needs judgment site by site and
    is not gated here; the optimizer plan labels have their own row below. Outside
    the package only string statements are read: an error message, an assigned
    constant or a fixture string in a test or script may quote a phrase. A statement
    built with ``+`` is not read (ruff B018 and basedpyright
    ``reportUnusedExpression`` refuse it), nor is a bytes statement, which is not
    prose, nor is a t-string statement. A trailing comment is never joined to the
    full-line comment below it: each is its own segment, so a phrase split across
    that pair is no match.
    """
    corpus = _sweep_corpus()
    violations, read = _provenance_entries_in(corpus)
    assert REPO_ROOT / CENSUS_MODULE in corpus, "the sweep corpus does not hold this module"
    assert PACKAGE_ROOT / "__init__.py" in corpus, "the sweep corpus does not hold the package"
    assert read, "no comment, docstring, name or string was read; the sweep read nothing"
    assert not violations, (
        "process-provenance phrase(s) in first-party prose:\n"
        + "\n".join(violations)
        + "\nRestate each sentence as the behaviour it guards, or rephrase a non-historical "
        "use (START.md, 'Style the maintainer cares about')."
    )


def _plant_prose(tmp_path: Path, body: str) -> Path:
    """Write a planted corpus file; the phrase arrives as data so this module holds none."""
    planted = tmp_path / "planted_prose.py"
    planted.write_text(body, encoding="utf-8")
    return planted


@pytest.mark.parametrize(
    "phrase",
    [phrase for phrase, _ in PROVENANCE_PHRASES],
    ids=[phrase for phrase, _ in PROVENANCE_PHRASES],
)
def test_the_provenance_sweep_reports_each_planted_phrase(tmp_path: Path, phrase: str) -> None:
    """Each gated phrase in a comment is reported with its file, line and phrase."""
    planted = _plant_prose(
        tmp_path,
        f"# a planted corpus\n# the value {phrase} 15 here\nVALUE = 1\n",
    )
    violations, read = _provenance_entries_in([planted])
    assert read == 1, read
    assert violations == [f"{planted}:2: comment: {phrase!r}: {phrase!r}"], violations


#: Planted shapes beyond a one-line comment, each with the line and kind the
#: report must name: a phrase a docstring wraps, a phrase a full-line comment
#: block wraps, a def name, a class docstring, an attribute docstring after a
#: class assignment and after a module annotated assignment, a later string
#: statement in a function body, a string statement in an ``if`` body, an
#: f-string first statement, a trailing comment, and a phrase in another case.
PLANTED_PROSE_SHAPES = [
    (
        "docstring-wrap",
        'def run():\n    """Summary.\n\n    The result is exactly as\n    before.\n    """\n',
        "4: docstring: 'exactly as before'",
    ),
    (
        "comment-block-wrap",
        "VALUE = 1\n# the result is exactly\n# as before here\nOTHER = 2\n",
        "2: comment: 'exactly as before'",
    ),
    ("def-name", "def test_used_to_raise():\n    pass\n", "1: name: 'used to'"),
    (
        "class-docstring",
        'class Probe:\n    """Probe.\n\n    It formerly ran.\n    """\n',
        "4: docstring: 'formerly'",
    ),
    (
        "class-attribute-docstring",
        'class Probe:\n    VALUE = 1\n    """It formerly ran."""\n',
        "3: docstring: 'formerly'",
    ),
    (
        "module-attribute-docstring",
        'VALUE: int = 1\n"""Set by the old implementation."""\n',
        "2: docstring: 'the old implementation'",
    ),
    (
        "later-string-statement",
        'def run():\n    """Run."""\n    VALUE = 1\n    """It used to run."""\n',
        "4: docstring: 'used to'",
    ),
    (
        "nested-string-statement",
        'if VALUE:\n    """The value is set as of 0.0.15."""\n',
        "2: docstring: 'as of 0.0.'",
    ),
    (
        "f-string-statement",
        'def run(value):\n    f"""Run {value} as previously set."""\n',
        "2: docstring: 'previously'",
    ),
    ("trailing-comment", "VALUE = 1  # pre-fix value\n", "1: comment: 'pre-fix'"),
    ("upper-case", "# PREVIOUSLY SET\nVALUE = 1\n", "1: comment: 'previously'"),
    (
        "back-compat-spelling",
        'def run():\n    """Run.\n\n    Kept for backwards compatibility.\n    """\n',
        "4: docstring: 'back-compat'",
    ),
]


@pytest.mark.parametrize(
    ("body", "expected"),
    [(body, expected) for _, body, expected in PLANTED_PROSE_SHAPES],
    ids=[name for name, _, _ in PLANTED_PROSE_SHAPES],
)
def test_the_provenance_sweep_reports_a_planted_shape(
    tmp_path: Path,
    body: str,
    expected: str,
) -> None:
    """A wrapped phrase, a name and every prose kind are reported at the phrase's line."""
    planted = _plant_prose(tmp_path, body)
    violations, _ = _provenance_entries_in([planted])
    assert len(violations) == 1, violations
    assert violations[0].startswith(f"{planted}:{expected}: "), violations[0]


#: Planted package modules: a runtime message and an f-string message part, each
#: with the line, kind and phrase the report must name.
PLANTED_PACKAGE_PROSE_SHAPES = [
    ("package-message", "MESSAGE = 'the value is previously set'\n", "1: string: 'previously'"),
    (
        "package-f-string",
        "def run(value):\n    raise ValueError(f'{value} formerly ran')\n",
        "2: string: 'formerly'",
    ),
]


@pytest.mark.parametrize(
    ("body", "expected"),
    [(body, expected) for _, body, expected in PLANTED_PACKAGE_PROSE_SHAPES],
    ids=[name for name, _, _ in PLANTED_PACKAGE_PROSE_SHAPES],
)
def test_the_provenance_sweep_reports_a_planted_package_string(
    tmp_path: Path,
    body: str,
    expected: str,
) -> None:
    """A phrase in a package runtime string is reported at its line, with kind ``string``."""
    planted, root = _plant_package(tmp_path, "planted.py", body)
    violations, _ = _provenance_entries_in([planted], root)
    assert len(violations) == 1, violations
    assert violations[0].startswith(f"{planted}:{expected}: "), violations[0]


def test_the_provenance_sweep_reports_nothing_for_a_planted_permitted_form(
    tmp_path: Path,
) -> None:
    """The negative direction: a phrase in a plain string, or inside another word, is not read.

    An error message outside the package may quote a phrase; ``reused`` and
    ``unused`` contain the letters but not the words, an upstream ``pre-1.10`` or
    a ``pre-2024`` date is neither the 1.0 release nor a three-digit spec number; a
    blank line between two comments ends the block, a trailing comment never
    joins the full-line comment below it, and an f-string's replacement field
    separates its parts, so a phrase split across any of those breaks is two
    halves and no match.
    """
    planted = _plant_prose(
        tmp_path,
        "MESSAGE = 'the value used to be set'\n"
        "# the reused token; unused tokens; pre-1.10 and pre-2024\n"
        "# are fine and exactly as\n"
        "\n"
        "# before is a new block\n"
        "VALUE = 1  # the value is exactly as\n"
        "# before here\n"
        "f'it used {VALUE} to be'\n",
    )
    violations, read = _provenance_entries_in([planted])
    assert read == 5, read
    assert violations == [], violations


#: The release the package tracks; the sweep refuses it and every earlier one.
PACKAGE_VERSION = django_strawberry_framework.__version__


def _release_pattern(version: str, separator: str) -> re.Pattern[str]:
    """Return the pattern for every release of this package up to ``version``'s series.

    ``version`` is ``major.minor.patch``. A release is any earlier major with any
    minor, or ``major`` with a minor up to ``minor``, and any patch, written with
    ``separator`` between the parts. No digit, and no separator after a digit,
    may sit on either side, so an IP address, a four-part version or a longer
    number is no match, and a sentence-final dot still ends one.
    """
    major, minor = (int(part) for part in version.split(".")[:2])
    sep = re.escape(separator)
    series = [rf"{major}{sep}(?:{'|'.join(str(n) for n in range(minor + 1))})"]
    if major:
        series.insert(0, rf"(?:{'|'.join(str(n) for n in range(major))}){sep}\d+")
    return re.compile(
        rf"(?<!\d)(?<!\d{sep})(?:{'|'.join(series)}){sep}\d+(?!{sep}?\d)",
    )


#: A release of this package in prose or in a string, derived from ``__version__``.
RELEASE_PATTERN = _release_pattern(PACKAGE_VERSION, ".")

#: A release of this package in a def or class name, spelled with underscores.
RELEASE_NAME_PATTERN = _release_pattern(PACKAGE_VERSION, "_")

#: A board card id carrying a release, past or planned (``<STATE>-<PHASE>-<NNN>-<release>``).
CARD_ID_PATTERN = re.compile(r"\b(?:DONE|WIP|TODO)-(?:[A-Z]+-)?\d+-\d+\.\d+\.\d+\b")

#: What prose and strings are read for: a card id, which carries its release, is
#: reported once as the card id.
PROSE_RELEASE_PATTERN = re.compile(f"{CARD_ID_PATTERN.pattern}|{RELEASE_PATTERN.pattern}")


def _runtime_strings(source: str, *, version_file: bool) -> list[tuple[int, str]]:
    """Return ``(line, text)`` for every ``str`` constant that is not a string statement.

    These are a module's runtime messages, assigned constants and arguments; an
    f-string contributes each literal part. A string statement is skipped (the
    prose sweep reads it), and in ``version_file`` so is the value assigned to
    ``__version__``, the one place the release is tracked.
    """
    tree = ast.parse(source)
    skipped: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, (ast.Constant, ast.JoinedStr)):
            skipped.update(id(part) for part in ast.walk(node.value))
        if (
            version_file
            and isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__version__"
                for target in node.targets
            )
        ):
            skipped.add(id(node.value))
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in skipped
    ]


def _release_entries_in(
    paths: Iterable[Path],
    package_root: Path = PACKAGE_ROOT,
) -> tuple[list[str], int]:
    """Return one formatted violation per release or release-carrying card id, and the texts read.

    The texts are ``_swept_texts``: every file's prose, plus a package file's
    runtime strings. Each violation names the file, the line, the kind of text and
    the match.
    """
    violations: list[str] = []
    read = 0
    for path in paths:
        display = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        source = path.read_text(encoding="utf-8")
        texts = [
            (first_line, kind, text.replace(" ", "_") if kind == "name" else text)
            for first_line, kind, text in _swept_texts(path, source, package_root)
        ]
        for first_line, kind, text in texts:
            read += 1
            pattern = RELEASE_NAME_PATTERN if kind == "name" else PROSE_RELEASE_PATTERN
            for match in pattern.finditer(text):
                line = first_line + text.count("\n", 0, match.start())
                violations.append(f"{display}:{line}: {kind}: {match[0]!r}")
    return violations, read


def test_no_comment_docstring_name_or_package_string_carries_a_release_of_this_package() -> None:
    """No first-party prose, and no package string, names a release of this package.

    START.md "Style the maintainer cares about": code states the behaviour, never
    the release that brought it; the release is tracked in ``__version__``, the
    changelog and the board. This row reads every comment, string statement and
    def/class name of the sweep corpus, plus every other ``str`` constant in
    ``django_strawberry_framework/`` (runtime messages), and refuses:

    - a release of this package: any earlier major, or the current major up to
      the current minor, with any patch (``RELEASE_PATTERN``, derived from
      ``__version__`` so each new series widens it without an edit);
    - a board card id carrying a release, past or planned (``CARD_ID_PATTERN``);
    - a release spelled with underscores in a def or class name.

    The one exclusion is the value assigned to ``__version__`` in
    ``django_strawberry_framework/__init__.py``. A site is restated as the
    behaviour it describes; a card id becomes its spec (``spec-NNN``) or its
    topic in words.

    Deliberate limits. A non-statement string outside the package (test data,
    fixtures, a script's argument example) is not read, so release-handling
    tests keep their inputs. A planned release of a later series than the current
    one is not a match unless it sits in a card id. The underscore spelling is
    read only in def/class names, so a cited ``spec-NNN-<topic>-<release>.md``
    path in prose stays. A release split by a line wrap is no match.
    """
    corpus = _sweep_corpus()
    violations, read = _release_entries_in(corpus)
    assert REPO_ROOT / CENSUS_MODULE in corpus, "the sweep corpus does not hold this module"
    assert PACKAGE_ROOT / "__init__.py" in corpus, "the sweep corpus does not hold the package"
    assert read, "no comment, docstring, name or string was read; the sweep read nothing"
    assert not violations, (
        "release(s) of this package in first-party code:\n"
        + "\n".join(violations)
        + "\nRestate each site as the behaviour it describes; name a card by its spec or "
        "its topic (START.md, 'Style the maintainer cares about')."
    )


def _plant_package(tmp_path: Path, name: str, body: str) -> tuple[Path, Path]:
    """Write a planted package module under ``tmp_path``; return it and the package root."""
    root = tmp_path / "django_strawberry_framework"
    root.mkdir(exist_ok=True)
    planted = root / name
    planted.write_text(body, encoding="utf-8")
    return planted, root


#: One planted shape per refused form: the file it sits in (``package`` or
#: ``other``), its body, and the line, kind and match the report must name.
PLANTED_RELEASE_SHAPES = [
    (
        "comment",
        "other",
        "VALUE = 1\n# the default since 0.0.9\n",
        "2: comment: '0.0.9'",
    ),
    (
        "docstring",
        "other",
        'def run():\n    """Run.\n\n    Shipped in 0.0.9.\n    """\n',
        "4: docstring: '0.0.9'",
    ),
    (
        "sentence-final",
        "other",
        "# The default is 0.0.9.\n",
        "1: comment: '0.0.9'",
    ),
    (
        "package-message",
        "package",
        "MESSAGE = 'refused since 0.0.9'\n",
        "1: string: '0.0.9'",
    ),
    (
        "package-f-string",
        "package",
        "def run(value):\n    raise ValueError(f'{value} refused since 0.0.9')\n",
        "2: string: '0.0.9'",
    ),
    (
        "card-id",
        "other",
        "# the scope of DONE-033-0.0.9\n",
        "1: comment: 'DONE-033-0.0.9'",
    ),
    (
        "planned-card-id",
        "package",
        "MESSAGE = 'see TODO-BETA-059-9.0.1'\n",
        "1: string: 'TODO-BETA-059-9.0.1'",
    ),
    (
        "name",
        "other",
        "def test_the_0_0_9_default():\n    pass\n",
        "1: name: '0_0_9'",
    ),
]


@pytest.mark.parametrize(
    ("where", "body", "expected"),
    [(where, body, expected) for _, where, body, expected in PLANTED_RELEASE_SHAPES],
    ids=[name for name, _, _, _ in PLANTED_RELEASE_SHAPES],
)
def test_the_release_sweep_reports_a_planted_shape(
    tmp_path: Path,
    where: str,
    body: str,
    expected: str,
) -> None:
    """Each refused form is reported at its line, with its kind and match."""
    if where == "package":
        planted, root = _plant_package(tmp_path, "planted.py", body)
    else:
        planted, root = _plant_prose(tmp_path, body), tmp_path / "django_strawberry_framework"
    violations, _ = _release_entries_in([planted], root)
    assert violations == [f"{planted}:{expected}"], violations


def test_the_release_sweep_reports_nothing_for_a_planted_permitted_form(tmp_path: Path) -> None:
    """The negative direction: the forms the gate leaves alone are not reported.

    An upstream release range, an IP address, a spec file path spelled with
    underscores in prose, a later series, a four-part version, a test-data string
    outside the package, and the ``__version__`` value in the package's
    ``__init__.py``.
    """
    other = _plant_prose(
        tmp_path,
        "# strawberry-graphql 0.322.2 - 0.327.7 and cross-web 0.7.0 are audited\n"
        "# the server listens on 127.0.0.1 and 10.0.0.1\n"
        "# see docs/SPECS/spec-032-full_relay-0_0_9.md\n"
        "# a later series 9.0.1; a four-part version 0.0.8.4\n"
        "FIXTURE = '0.0.8'\n",
    )
    version_file, root = _plant_package(
        tmp_path,
        "__init__.py",
        f'"""The package."""\n\n__version__ = {PACKAGE_VERSION!r}\n',
    )
    violations, read = _release_entries_in([other, version_file], root)
    assert read == 2, read
    assert violations == [], violations


def test_the_release_pattern_widens_with_the_version() -> None:
    """Each later series widens the pattern: every earlier major and minor stays refused."""
    pattern = _release_pattern("2.1.0", ".")
    assert [
        text
        for text in (
            "0.9.3",
            "1.4.0",
            "2.0.7",
            "2.1.12",
        )
        if pattern.search(text)
    ] == [
        "0.9.3",
        "1.4.0",
        "2.0.7",
        "2.1.12",
    ]
    assert [text for text in ("2.2.0", "3.0.0", "12.1.0") if pattern.search(text)] == []


#: The optimizer plan labels: ``O[1-6]`` title spec-002's headings (the
#: optimizer foundation), ``B[1-8]`` spec-004's (the optimizer beyond it) and
#: ``G[1-3]`` spec-035's decisions (the robustness guards). Case-sensitive: a
#: lowercase ``b1`` in prose is a seed value or a local, never a label.
PLAN_LABEL_PATTERN = re.compile(r"(?<!\w)(?:B[1-8]|O[1-6]|G[1-3])(?!\w)")

#: The same labels in a def or class name, read with its underscores as spaces.
PLAN_LABEL_NAME_PATTERN = re.compile(r"(?<!\w)(?:B[1-8]|O[1-6]|G[1-3])(?!\w)", re.IGNORECASE)

#: An inline code span closed on its line. It quotes a value (a seed row, a
#: branch code, a computed genre key), so a token inside it is not a label,
#: unless the span holds nothing but a label (``PLAN_LABEL_SPAN_PATTERN``):
#: that is the label set in code type, and a value of that spelling is quoted
#: as the literal it is (``"B1"``).
CODE_SPAN_PATTERN = re.compile(r"(``?)([^`\n]+?)\1")

#: A code span's content that is a bare label.
PLAN_LABEL_SPAN_PATTERN = re.compile(r"(?:B[1-8]|O[1-6]|G[1-3])")

#: A camel-case word boundary in a def or class name: a lowercase letter
#: followed by an uppercase one (``TestB8``), or an uppercase letter followed by
#: a lowercase one (``O2OField``, split before ``Field`` only, so ``O2O`` stays
#: one word).
CAMEL_BOUNDARY_PATTERN = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=\w)(?=[A-Z][a-z])")


def _blank_value_span(span: re.Match[str]) -> str:
    """Blank a code span quoting a value; keep one holding a bare plan label."""
    if PLAN_LABEL_SPAN_PATTERN.fullmatch(span[2]):
        return span[0]
    return " " * len(span[0])


def _plan_label_entries_in(
    paths: Iterable[Path],
    package_root: Path = PACKAGE_ROOT,
) -> tuple[list[str], int]:
    """Return one formatted violation per optimizer plan label, and the texts read.

    The texts are ``_swept_texts``: every file's prose, plus a package file's
    runtime strings. Prose and strings are read with their value code spans
    blanked (``_blank_value_span``); a def or class name is read whole, split at
    its camel-case boundaries (``CAMEL_BOUNDARY_PATTERN``). Each violation names
    the file, the line, the kind of text and the label.
    """
    violations: list[str] = []
    read = 0
    for path in paths:
        display = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        source = path.read_text(encoding="utf-8")
        for first_line, kind, text in _swept_texts(path, source, package_root):
            read += 1
            if kind == "name":
                words = CAMEL_BOUNDARY_PATTERN.sub(" ", text)
                matches = PLAN_LABEL_NAME_PATTERN.finditer(words)
            else:
                blanked = CODE_SPAN_PATTERN.sub(_blank_value_span, text)
                matches = PLAN_LABEL_PATTERN.finditer(blanked)
            for match in matches:
                line = first_line + text.count("\n", 0, match.start())
                violations.append(f"{display}:{line}: {kind}: {match[0]!r}")
    return violations, read


def test_no_comment_docstring_name_or_package_string_carries_an_optimizer_plan_label() -> None:
    """No first-party prose, and no package string, names an optimizer plan label.

    START.md "Style the maintainer cares about": plan and slice numbering is
    process provenance, and a contract is cited by content, never by ordinal.
    The optimizer specs title their headings with labels (``PLAN_LABEL_PATTERN``);
    code names the behaviour instead (the plan cache, FK-id elision, the
    evaluated-queryset guard), and a spec-035 guard is cited as
    ``spec-035 Decision N``, the gated pointer. This row reads every comment,
    string statement and def/class name of the sweep corpus, plus every other
    ``str`` constant in ``django_strawberry_framework/``, and refuses a label.

    Deliberate limits. A label inside an inline code span that quotes more than
    the label is not read: seed rows, branch codes and computed values share the
    spelling, so a value is quoted as its literal (``"B1"``), and a value written
    bare in prose is quoted, not exempted. A span holding a bare label is read.
    A def or class name is read at its underscores and camel-case boundaries
    (``TestB8Diffing``), never inside one word (``O2OField``). Only these three
    families are read; another plan's labels (requirement ids, a lateral
    strategy's arms) are judged by hand. A non-statement string outside the
    package (test data, fixtures) is not read.
    """
    corpus = _sweep_corpus()
    violations, read = _plan_label_entries_in(corpus)
    assert REPO_ROOT / CENSUS_MODULE in corpus, "the sweep corpus does not hold this module"
    assert PACKAGE_ROOT / "__init__.py" in corpus, "the sweep corpus does not hold the package"
    assert read, "no comment, docstring, name or string was read; the sweep read nothing"
    assert not violations, (
        "optimizer plan label(s) in first-party code:\n"
        + "\n".join(violations)
        + "\nName the behaviour the label stood for, cite a spec-035 guard as "
        "'spec-035 Decision N', or quote a data value as its literal in a code span "
        "(START.md, "
        "'Style the maintainer cares about')."
    )


#: One planted shape per refused form: the file it sits in (``package`` or
#: ``other``), its body, and every violation the report must name (line, kind,
#: label).
PLANTED_PLAN_LABEL_SHAPES = [
    (
        "comment",
        "other",
        "VALUE = 1\n# the B3 contract fires\n",
        ["2: comment: 'B3'"],
    ),
    (
        "docstring-prefixed",
        "other",
        'def run():\n    """Run.\n\n    The clone, pre-G1, re-ran the SQL.\n    """\n',
        ["4: docstring: 'G1'"],
    ),
    (
        "range",
        "other",
        "# the B1-B8 suite\n",
        ["1: comment: 'B1'", "1: comment: 'B8'"],
    ),
    (
        "beside-a-spec",
        "other",
        "# spec-035 G2 gates the projection\n",
        ["1: comment: 'G2'"],
    ),
    (
        "test-name",
        "other",
        "def test_o6_downgrade():\n    pass\n",
        ["1: name: 'o6'"],
    ),
    (
        "class-name",
        "other",
        "class Probe_B4:\n    pass\n",
        ["1: name: 'B4'"],
    ),
    (
        "bare-label-code-span",
        "other",
        "# Pins the ``B2`` elision\n",
        ["1: comment: 'B2'"],
    ),
    (
        "camel-case-class-name",
        "other",
        "class TestB8Diffing:\n    pass\n",
        ["1: name: 'B8'"],
    ),
    (
        "package-message",
        "package",
        "MESSAGE = 'the B5 stash is empty'\n",
        ["1: string: 'B5'"],
    ),
]


@pytest.mark.parametrize(
    ("where", "body", "expected"),
    [(where, body, expected) for _, where, body, expected in PLANTED_PLAN_LABEL_SHAPES],
    ids=[name for name, _, _, _ in PLANTED_PLAN_LABEL_SHAPES],
)
def test_the_plan_label_sweep_reports_a_planted_shape(
    tmp_path: Path,
    where: str,
    body: str,
    expected: list[str],
) -> None:
    """Each refused form is reported at its line, with its kind and label."""
    if where == "package":
        planted, root = _plant_package(tmp_path, "planted.py", body)
    else:
        planted, root = _plant_prose(tmp_path, body), tmp_path / "django_strawberry_framework"
    violations, _ = _plan_label_entries_in([planted], root)
    assert violations == [f"{planted}:{entry}" for entry in expected], violations


def test_the_plan_label_sweep_reports_nothing_for_a_planted_permitted_form(
    tmp_path: Path,
) -> None:
    """The negative direction: the forms the gate leaves alone are not reported.

    A value quoted as its literal in a double or single code span, a code span
    holding more than a label, a token outside the three families or glued to a
    word (``B9``, ``O7``, ``G4``, ``AB1``, ``B1a``), a lowercase seed value in
    prose, the gated ``spec-035 Decision N`` pointer, a label-shaped run inside
    one camel-case word of a class name, and a test-data string outside the
    package.
    """
    planted = _plant_prose(
        tmp_path,
        '# rows ``A1`` and ``"B1"``; the key `"G1"`, ``"G2"`` and ``B3 rows``\n'
        "# B9, O7, G4, AB1 and B1a are not labels; nor is the seed b2\n"
        "# spec-035 Decision 3 is the pointer\n"
        "class O2OField:\n"
        "    pass\n"
        "FIXTURE = 'B1'\n",
    )
    violations, read = _plan_label_entries_in([planted])
    assert read == 2, read
    assert violations == [], violations


def test_channels_floor_constant_matches_the_pyproject_dependency_row() -> None:
    """The one Channels floor the install hints name is the one the project pins.

    ``CHANNELS_FLOOR`` is interpolated into every ``pip install
    'channels>=...'`` hint, so the hints cannot drift from each other. This
    row compares it to the ``channels[daphne]`` dev-group row in
    ``pyproject.toml``. Nothing imports a TOML dependency row, so a bump on
    either side is otherwise silent.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    rows = re.findall(r'"channels\[daphne\]>=([0-9][^"]*)"', text)
    assert rows == [CHANNELS_FLOOR], (rows, CHANNELS_FLOOR)


def test_strawberry_floor_constant_matches_the_pyproject_dependency_row() -> None:
    """The Strawberry floor the router's hint recommends is the one the project requires.

    The mirror of the Channels row above: the router's broken-``strawberry.channels``
    hint interpolates ``STRAWBERRY_FLOOR``, and nothing else compares that
    constant to the ``strawberry-graphql`` row in ``pyproject.toml``. A floor
    raise on either side would otherwise be silent, and the hint could advise
    installing a version the install itself rejects. Parsed exactly like the
    Channels row so the two pins cannot diverge in method.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    rows = re.findall(r'"strawberry-graphql>=([0-9][^"]*)"', text)
    assert rows == [STRAWBERRY_FLOOR], (rows, STRAWBERRY_FLOOR)


def test_debug_toolbar_floor_constant_matches_the_pyproject_dependency_row() -> None:
    """The debug-toolbar floor the middleware's hint names is the one the project pins.

    The toolbar middleware's install hint interpolates ``DEBUG_TOOLBAR_FLOOR``,
    and nothing else compares that constant to the ``django-debug-toolbar``
    dev-group row in ``pyproject.toml``. A floor bump on either side would
    otherwise be silent. Parsed exactly like the Channels row.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    rows = re.findall(r'"django-debug-toolbar>=([0-9][^"]*)"', text)
    assert rows == [DEBUG_TOOLBAR_FLOOR], (rows, DEBUG_TOOLBAR_FLOOR)


def test_drf_floor_constant_matches_the_pyproject_dependency_row() -> None:
    """The DRF floor the serializer-mutation hint names is the one the project pins.

    ``require_drf()``'s install hint interpolates ``DRF_FLOOR``, and nothing
    else compares that constant to the ``djangorestframework`` dev-group row in
    ``pyproject.toml``. A floor bump on either side would otherwise be silent.
    Parsed exactly like the Channels row; the quote before ``>=`` keeps the
    ``djangorestframework-stubs`` row out of the match.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    rows = re.findall(r'"djangorestframework>=([0-9][^"]*)"', text)
    assert rows == [DRF_FLOOR], (rows, DRF_FLOOR)


def test_cryptography_floor_constant_matches_the_pyproject_dependency_row() -> None:
    """The cryptography floor the keyset cursor's hint names is the one the project pins.

    The keyset cursor's install hint interpolates ``CRYPTOGRAPHY_FLOOR``, and
    nothing else compares that constant to the ``cryptography`` dev-group row in
    ``pyproject.toml``. A floor bump on either side would otherwise be silent.
    Parsed exactly like the Channels row.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    rows = re.findall(r'"cryptography>=([0-9][^"]*)"', text)
    assert rows == [CRYPTOGRAPHY_FLOOR], (rows, CRYPTOGRAPHY_FLOOR)


#: The soft dependencies (START.md "Support matrix"), spelled as their dev-group rows are.
SOFT_DEPENDENCIES = (
    "channels[daphne]",
    "cryptography",
    "django-debug-toolbar",
    "djangorestframework",
)
_REQUIREMENT = re.compile(r"\s*([A-Za-z0-9][\w.-]*(?:\[[^\]]*\])?)\s*(.*)")
_LOWER_BOUND = re.compile(r">=\s*([^,;\s]+)")


#: The pyproject rows the floor cell pins, so each must state exactly one floor.
_FLOOR_ROWS = ("Django", "strawberry-graphql", *SOFT_DEPENDENCIES)


def _lower_bounds_of(pyproject_text: str) -> dict[str, str]:
    """Each ``>=`` bound ``pyproject_text`` states, keyed by requirement name with its extras.

    ``python`` is ``requires-python``'s; every other key is a ``[project].dependencies``
    or ``[dependency-groups].dev`` row's. A floor row (``_FLOOR_ROWS``) two bounded
    rows state (rows split by environment marker) fails, since the floor cell pins
    one version per package.
    """
    document = object_result(tomli.loads, pyproject_text)
    rows = [
        *json_list(document, "project", "dependencies"),
        *json_list(document, "dependency-groups", "dev"),
    ]
    requires_python = _LOWER_BOUND.search(str(json_at(document, "project", "requires-python")))
    assert requires_python is not None
    bounds = {"python": requires_python.group(1)}
    for row in map(str, rows):
        requirement = _REQUIREMENT.match(row)
        bound = _LOWER_BOUND.search(requirement.group(2)) if requirement else None
        if requirement and bound:
            name = requirement.group(1)
            assert name not in _FLOOR_ROWS or name not in bounds, (
                f"{name} states more than one floor: {bounds[name]} and {bound.group(1)}"
            )
            bounds[name] = bound.group(1)
    return bounds


def _pyproject_lower_bounds() -> dict[str, str]:
    """``_lower_bounds_of`` this repository's ``pyproject.toml``."""
    return _lower_bounds_of((REPO_ROOT / "pyproject.toml").read_text("utf-8"))


def test_the_floor_bounds_refuse_a_marker_split_floor_row() -> None:
    """A floor row split by environment marker fails; a repeated non-floor row does not."""
    text = (
        "[project]\n"
        'requires-python = ">=3.10"\n'
        'dependencies = ["Django>=5.2.16", "strawberry-graphql>=0.322.2"]\n'
        "[dependency-groups]\n"
        "dev = [\"pytest>=9.0.2; python_version<'3.12'\", \"pytest>=9.1.0; python_version>='3.12'\", "
        "\"cryptography>=44.0.0; python_version<'3.12'\", "
        "\"cryptography>=45.0.0; python_version>='3.12'\"]\n"
    )

    with pytest.raises(
        AssertionError,
        match=r"^cryptography states more than one floor: 44\.0\.0 and 45\.0\.0",
    ):
        _lower_bounds_of(text)
    assert _lower_bounds_of(text.replace("cryptography>=45.0.0", "cffi>=1.0"))["pytest"] == "9.1.0"


#: The ``if`` of the ``test`` job's strawberry-graphql floor step and of its soft-dependency one.
STRAWBERRY_FLOOR_IF = "matrix.strawberry"
SOFT_FLOOR_IF = "matrix.compatibility_only == '1'"
#: ``(later, earlier)``: each step that must run after the other in the ``test`` job.
_STEP_ORDER = (
    ("Django install", "uv sync"),
    ("strawberry floor", "uv sync"),
    ("strawberry floor", "Django install"),
    ("soft floor", "uv sync"),
    ("soft floor", "Django install"),
    ("pytest run", "strawberry floor"),
    ("pytest run", "soft floor"),
)


def _step_script(step: dict[object, object]) -> str:
    """A workflow step's ``run`` script with its backslash-newline continuations joined."""
    return str(step.get("run", "")).replace("\\\n", " ")


#: The control operators that end a simple command, each before any operator it begins.
_SHELL_OPERATORS = (
    "&&",
    "||",
    ";",
    "|",
    "&",
)
#: A simple command of a shell line, or the operator that ends it; a quoted string and a
#: redirection's ``&`` (``2>&1``, ``>&2``, ``&>file``) stay inside the command.
_SHELL_PART = re.compile(
    r"""(?:"[^"]*"|'[^']*'|\d*[<>]&\d*-?|&>|[^"';&|])+|"""
    + "|".join(map(re.escape, _SHELL_OPERATORS)),
)
#: A quoted string (group 1, kept whole) or a ``#`` comment, which opens at a word start.
_SHELL_COMMENT = re.compile(r"""("[^"]*"|'[^']*')|(?:^|(?<=\s))#.*""")
#: A word ahead of a command's own name: a ``VAR=val`` assignment, ``env`` or ``time``.
_COMMAND_PREFIX = re.compile(r"env|time|[A-Za-z_]\w*=\S*")
#: The ``shell:`` names GitHub runs with errexit (``bash --noprofile --norc -eo pipefail {0}``,
#: ``sh -e {0}``).
_ERREXIT_SHELL_NAMES = frozenset({"bash", "sh"})
#: A custom ``bash`` / ``sh`` option cluster turning errexit on (``-e``, ``-eo pipefail``).
_ERREXIT_SHELL_OPTION = re.compile(r"-[a-z]*e[a-z]*")
#: The ``bash`` / ``sh`` options whose value is the next word (``-o pipefail``).
_SHELL_VALUED_OPTIONS = frozenset({"-o", "+o"})
#: A ``uv`` word and a later ``sync`` word (never the ``sync`` of ``--no-sync``).
_UV_SYNC_WORDS = re.compile(r"\buv\b.*(?<![\w-])sync\b")
#: uv's global options that take the next word as their value at runtime, hidden and alias
#: names included (``--python-fetch``, ``--python-preference``, ``--preview-features``,
#: ``--trusted-host``); the subcommand follows.
_UV_VALUED_GLOBALS = frozenset(
    {
        "--allow-insecure-host",
        "--cache-dir",
        "--color",
        "--config-file",
        "--directory",
        "--preview-features",
        "--project",
        "--python-fetch",
        "--python-preference",
        "--trusted-host",
    },
)
#: The options ``uv run`` takes the next word as the value of at runtime, its own and the
#: globals, hidden names included (``--max-recursion-depth``); the child command follows.
_UV_RUN_VALUED = _UV_VALUED_GLOBALS | frozenset(
    {
        "--config-setting",
        "--config-settings-package",
        "--default-index",
        "--env-file",
        "--exclude-newer",
        "--exclude-newer-package",
        "--extra",
        "--extra-index-url",
        "--find-links",
        "--fork-strategy",
        "--group",
        "--index",
        "--index-strategy",
        "--index-url",
        "--keyring-provider",
        "--link-mode",
        "--max-recursion-depth",
        "--no-binary-package",
        "--no-build-isolation-package",
        "--no-build-package",
        "--no-editable-package",
        "--no-extra",
        "--no-group",
        "--no-sources-package",
        "--only-group",
        "--package",
        "--prerelease",
        "--prerelease-package",
        "--python",
        "--python-platform",
        "--refresh-package",
        "--reinstall-package",
        "--resolution",
        "--upgrade-group",
        "--upgrade-package",
        "--with",
        "--with-editable",
        "--with-requirements",
        "-C",
        "-P",
        "-f",
        "-i",
        "-p",
        "-w",
    },
)
#: The uv subcommands a workflow runs besides ``sync``; a ``sync`` word after one is an argument.
_UV_OTHER_SUBCOMMANDS = frozenset(
    {
        "build",
        "lock",
        "pip",
        "python",
        "run",
        "tool",
        "venv",
    },
)
#: The uv subcommands that edit ``pyproject.toml`` and ``uv.lock``; CI runs neither.
_UV_PROJECT_EDITS = frozenset({"add", "remove"})
#: The uv subcommands that lock the project first unless told ``--locked`` / ``--frozen``.
_UV_RELOCKING = frozenset({"export", "tree"})
#: The uv subcommand that re-locks only when it writes a version (a value or ``--bump``) without
#: ``--locked`` / ``--frozen``; a bare ``uv version`` reads the version and leaves ``uv.lock``.
_UV_VERSION = "version"
#: A superset of the options ``uv version`` takes the next word as the value of at runtime:
#: ``uv run``'s plus ``--bump`` and ``--output-format``.
_UV_VERSION_VALUED = _UV_RUN_VALUED | frozenset({"--bump", "--output-format"})
#: A word deciding whether a uv command may move off ``uv.lock``; group 1 spells a one-package
#: upgrade (``--upgrade-package X``, ``--upgrade-package=X``, ``-P X``, ``-PX``), group 2 a
#: whole upgrade.
_UV_LOCK_FLAG = re.compile(
    r"--frozen|--locked|--no-sync|(--upgrade-package(?:=\S+)?|-P\S*)|(--upgrade|-U)",
)
#: ``UV_FROZEN`` / ``UV_NO_SYNC`` / ``UV_LOCKED``: the environment spellings of the flags above.
_UV_LOCK_ENV = re.compile(r"UV_(?:FROZEN|NO_SYNC|LOCKED)")
_UV_LOCK_ENV_SET = re.compile(rf"\b({_UV_LOCK_ENV.pattern})=")
#: A step ``if:`` that runs the step after an earlier step failed.
_RUNS_PAST_A_FAILURE = re.compile(r"\b(?:always|failure|cancelled)\s*\(")


def _command_word(command: str) -> str:
    """A simple command's own first word, past ``VAR=val`` assignments, ``env`` and ``time``."""
    return next((word for word in command.split() if not _COMMAND_PREFIX.fullmatch(word)), "")


def _shell_commands(script: str) -> list[tuple[str, str]]:
    """The simple commands of a joined ``run`` script in order, each with the operator after it.

    Each line loses a trailing ``#`` comment (a ``#`` inside quotes stays), then splits at
    ``&&``, ``||``, ``;``, ``|`` and ``&`` outside quotes and outside a redirection
    (``2>&1``, ``&>file``), whitespace runs collapsed. A command ending its line is
    followed by ``""``.
    """
    commands: list[tuple[str, str]] = []
    for line in script.splitlines():
        stripped = _SHELL_COMMENT.sub(lambda match: match.group(1) or "", line)
        parts = [
            match.group() for match in _SHELL_PART.finditer(stripped) if match.group().strip()
        ]
        commands.extend(
            (" ".join(part.split()), parts[index + 1] if index + 1 < len(parts) else "")
            for index, part in enumerate(parts)
            if part not in _SHELL_OPERATORS
        )
    return commands


def _shell_segments(script: str) -> list[str]:
    """The simple commands of a joined ``run`` script, in order (``_shell_commands`` sans operator)."""
    return [command for command, _after in _shell_commands(script)]


def _default_shell(node: _YAMLMapping, inherited: object) -> object:
    """The ``defaults.run.shell`` a workflow or job sets, else the one it inherits."""
    return _mapping(_mapping(node.get("defaults")).get("run")).get("shell", inherited)


def _runs_with_errexit(shell: object) -> bool:
    """Whether a step's ``shell:`` ends the step on its first failing command.

    True when no shell is set (on a Linux or macOS runner, where every job here runs, the
    default is ``bash -e``; a Windows runner's default is ``pwsh``), for ``bash`` and
    ``sh`` (GitHub adds ``-e``), and for a custom shell string whose program is ``bash``
    or ``sh`` with a lowercase option cluster carrying ``e`` (``-e``, ``-eo pipefail``)
    among its options. ``bash -l {0}``, ``bash -E {0}``, ``pwsh``, ``python -We {0}`` and
    ``xvfb-run -e /dev/stdout bash {0}`` run past a failing command.
    """
    if shell is None or str(shell) in _ERREXIT_SHELL_NAMES:
        return True
    words = str(shell).split()
    if not words or Path(words[0]).name not in _ERREXIT_SHELL_NAMES:
        return False
    options = words[1 : _skip_options(words, 1, _SHELL_VALUED_OPTIONS)]
    return any(_ERREXIT_SHELL_OPTION.fullmatch(word) for word in options)


def _skip_options(words: list[str], index: int, valued: frozenset[str]) -> int:
    """The index of the first word from ``index`` on that is no option and no option's value.

    A ``--`` ends the options: the index stops on it.
    """
    while index < len(words) and words[index].startswith("-") and words[index] != "--":
        index += 2 if words[index] in valued else 1
    return index


def _uv_command(segment: str) -> tuple[str, list[str]]:
    """A segment's uv subcommand and uv's own words after its first ``uv`` word.

    Whatever precedes ``uv`` (``VAR=val`` assignments, ``env``) and uv's global
    options are skipped. The subcommand reads ``"pip sync"`` / ``"pip install"`` for
    those (``pip``'s global options skipped too), ``"?"`` for a segment naming ``uv``
    and ``sync`` with no subcommand this check knows, and ``""`` for a segment running
    no uv command it judges. A ``uv run``'s words end at its child command, so the
    child's own ``--locked`` / ``--no-sync`` is never read as uv's.
    """
    words = segment.split()
    rest = words[words.index("uv") + 1 :] if "uv" in words else []
    index = _skip_options(rest, 0, _UV_VALUED_GLOBALS)
    subcommand = rest[index] if index < len(rest) else ""
    if subcommand == "pip":
        action = _skip_options(rest, index + 1, _UV_VALUED_GLOBALS)
        if rest[action : action + 1] in (["sync"], ["install"]):
            return f"pip {rest[action]}", rest
    if subcommand == "run":
        return subcommand, rest[: _skip_options(rest, index + 1, _UV_RUN_VALUED)]
    if subcommand in {
        "sync",
        *_UV_OTHER_SUBCOMMANDS,
        *_UV_PROJECT_EDITS,
        *_UV_RELOCKING,
        _UV_VERSION,
    }:
        return subcommand, rest
    return ("?" if _UV_SYNC_WORDS.search(segment) else ""), rest


def _uv_version_writes(words: list[str]) -> bool:
    """Whether a ``uv version``'s uv words set the version: a positional value or ``--bump``."""
    args = words[_skip_options(words, 0, _UV_VALUED_GLOBALS) + 1 :]
    return _skip_options(args, 0, _UV_VERSION_VALUED) < len(args) or any(
        word == "--bump" or word.startswith("--bump=") for word in args
    )


def _lock_flags(words: list[str]) -> list[str]:
    """The lock-deciding words of a uv command, each upgrade spelling read by its group."""
    return [
        "--upgrade-package" if match.group(1) else "--upgrade" if match.group(2) else word
        for word in words
        if (match := _UV_LOCK_FLAG.fullmatch(word))
    ]


def _floor_cell_problems(workflow_text: str, bounds: dict[str, str]) -> list[str]:
    """Each way the ``test`` job of ``workflow_text`` fails to run exactly the floors ``bounds`` states.

    A floor node is identified by its content, a ``(python, django)`` pair equal to
    the floor's, never by the ``compatibility_only`` marker the floor steps key on;
    the floor steps are identified by their ``if``, the sync and the Django install by
    their shell segments, the test run by its ``run`` script.
    """
    job = json_object(object_result(yaml.safe_load, workflow_text), "jobs", "test")
    include = str(json_at(job, "strategy", "matrix", "include"))
    node_lists: list[str] = re.findall(r"fromJSON\('(\[.*?\])'\)", include, re.DOTALL)
    problems: list[str] = []
    if len(node_lists) != 2:
        problems.append(f"{len(node_lists)} matrix node lists, not the full and push/PR pair")
    floor = (bounds["python"], bounds["Django"], bounds["strawberry-graphql"])
    for list_index, text in enumerate(node_lists):
        nodes = list(map(json_object, json_list(json_loads(text))))
        if not any((node.get("python"), node.get("django")) == floor[:2] for node in nodes):
            problems.append(f"node list {list_index} has no node at the floor")
        for index, node in enumerate(nodes):
            marked = node.get("compatibility_only") == "1"
            if (node.get("python"), node.get("django")) == floor[:2] and not marked:
                problems.append(
                    f"node list {list_index}, node {index}: at the floor without compatibility_only",
                )
            if (
                marked
                and (node.get("python"), node.get("django"), node.get("strawberry")) != floor
            ):
                problems.append(f"node list {list_index}, node {index}: marked but off the floor")

    steps = list(map(json_object, json_list(job, "steps")))
    segments = [_shell_segments(_step_script(step)) for step in steps]
    located = {
        "uv sync": [
            index
            for index, found in enumerate(segments)
            if any(_uv_command(segment)[0] == "sync" for segment in found)
        ],
        "Django install": [
            index
            for index, found in enumerate(segments)
            if any(
                subcommand == "pip install" and "--upgrade-package" in _lock_flags(words)
                for subcommand, words in map(_uv_command, found)
            )
        ],
        "strawberry floor": [
            index for index, step in enumerate(steps) if step.get("if") == STRAWBERRY_FLOOR_IF
        ],
        "soft floor": [
            index for index, step in enumerate(steps) if step.get("if") == SOFT_FLOOR_IF
        ],
        "pytest run": [
            index
            for index, step in enumerate(steps)
            if re.search(r"\bpytest\b", _step_script(step))
        ],
    }
    if any(len(found) != 1 for found in located.values()):
        return [*problems, f"steps located {located}, not one each"]
    at = {name: found[0] for name, found in located.items()}
    problems.extend(
        f"the {later} step runs before the {earlier} step"
        for later, earlier in _STEP_ORDER
        if at[later] < at[earlier]
    )
    installs = [
        segment
        for segment in segments[at["soft floor"]]
        if _uv_command(segment)[0] == "pip install"
    ]
    pinned = [
        (match.group(1), match.group(2))
        for match in re.finditer(r'"([^"=]+)==([^"]+)"', installs[0] if len(installs) == 1 else "")
    ]
    if [name for name, _version in pinned] != list(SOFT_DEPENDENCIES):
        problems.append(f"the soft floor step pins {installs}, not each of {SOFT_DEPENDENCIES}")
    problems.extend(
        f"the soft floor step pins {name} off its floor"
        for name, version in pinned
        if bounds.get(name) != version
    )
    return problems


def test_every_floor_literal_in_the_django_workflow_is_its_pyproject_lower_bound() -> None:
    """The CI floor cell installs exactly the floors ``pyproject.toml`` states, and keeps them.

    ``django.yml`` cannot read ``pyproject.toml``, so the floor cell carries
    each floor as a literal: the ``python`` / ``django`` / ``strawberry`` keys
    of the floor matrix nodes (the push/PR list and the full matrix alike) and
    each ``name==version`` pin of the soft-dependency install step those nodes
    run. Each must equal the ``>=`` bound of its pyproject row, extras
    included, and every soft dependency must be pinned, so a floor raised on
    either side alone fails here instead of the cell silently running a point
    the project no longer declares. Every node at the floor Python and Django
    carries ``compatibility_only`` (the floor steps' condition) and every node
    carrying it is at the floor. The Django install runs after the job's one
    ``uv sync``, both floor steps after the two of them, and the test run after
    the floor steps; ``_uv_lock_problems`` refuses a ``uv run`` that would sync
    the pins away.
    """
    text = (WORKFLOW_DIR / "django.yml").read_text(encoding="utf-8")

    assert _floor_cell_problems(text, _pyproject_lower_bounds()) == []


def _test_job_span(text: str) -> tuple[int, int]:
    """The character span of ``django.yml``'s ``test`` job."""
    start = text.index("\n  test:\n")
    following = re.compile(r"\n  \S").search(text, start + 1)
    return start, following.start() if following else len(text)


def _move_step(text: str, step: str, above: str) -> str:
    """Move the ``test`` job step named ``step...`` to just above the one named ``above...``."""
    start, end = _test_job_span(text)
    job = text[start:end]
    marker = "\n      - name: "
    assert job.count(marker + step) == job.count(marker + above) == 1, (step, above)
    begin = job.index(marker + step)
    finish = job.find(marker, begin + 1)
    block = job[begin : finish if finish != -1 else len(job)]
    rest = job.replace(block, "", 1)
    target = rest.index(marker + above)
    return text[:start] + rest[:target] + block + rest[target:] + text[end:]


def _replace_once(
    text: str,
    old: str,
    new: str,
    *,
    last: bool = False,
) -> str:
    """Replace the first (or ``last``) occurrence of ``old``, which must occur in ``text``."""
    assert old in text, old
    if last:
        head, _, tail = text.rpartition(old)
        return head + new + tail
    return text.replace(old, new, 1)


_MULTI_DB_FLOOR_NODE = '"database": "multi DB", "fakeshop_sharded": "1", "strawberry": "'
_FLOOR_MUTATIONS: dict[str, tuple[Callable[[str, dict[str, str]], str], list[str]]] = {
    "django-step-above-sync": (
        lambda text, _bounds: _move_step(text, "Install Django", "Install dependencies"),
        ["the Django install step runs before the uv sync step"],
    ),
    "strawberry-step-above-sync": (
        lambda text, _bounds: _move_step(text, "Install Strawberry", "Install dependencies"),
        [
            "the strawberry floor step runs before the uv sync step",
            "the strawberry floor step runs before the Django install step",
        ],
    ),
    "soft-step-above-sync": (
        lambda text, _bounds: _move_step(text, "Install the soft", "Install dependencies"),
        [
            "the soft floor step runs before the uv sync step",
            "the soft floor step runs before the Django install step",
        ],
    ),
    "soft-step-above-django": (
        lambda text, _bounds: _move_step(text, "Install the soft", "Install Django"),
        ["the soft floor step runs before the Django install step"],
    ),
    "test-run-above-strawberry-step": (
        lambda text, _bounds: _move_step(text, "Run Tests", "Install Strawberry"),
        [
            "the pytest run step runs before the strawberry floor step",
            "the pytest run step runs before the soft floor step",
        ],
    ),
    "test-run-above-soft-step": (
        lambda text, _bounds: _move_step(text, "Run Tests", "Install the soft"),
        ["the pytest run step runs before the soft floor step"],
    ),
    "full-list-node-unmarked": (
        lambda text, bounds: _replace_once(
            text,
            f'{_MULTI_DB_FLOOR_NODE}{bounds["strawberry-graphql"]}", "compatibility_only": "1"',
            f'{_MULTI_DB_FLOOR_NODE}{bounds["strawberry-graphql"]}"',
        ),
        ["node list 0, node 2: at the floor without compatibility_only"],
    ),
    "push-list-node-unmarked": (
        lambda text, _bounds: _replace_once(
            text,
            ', "compatibility_only": "1", "shard": "remainder"',
            ', "shard": "remainder"',
            last=True,
        ),
        ["node list 1, node 1: at the floor without compatibility_only"],
    ),
    "floor-node-strawberry-drifts": (
        lambda text, bounds: _replace_once(
            text,
            f'{_MULTI_DB_FLOOR_NODE}{bounds["strawberry-graphql"]}"',
            f'{_MULTI_DB_FLOOR_NODE}{bounds["strawberry-graphql"]}.1"',
        ),
        ["node list 0, node 2: marked but off the floor"],
    ),
    "soft-pin-drifts": (
        lambda text, bounds: _replace_once(
            text,
            f'"cryptography=={bounds["cryptography"]}"',
            f'"cryptography=={bounds["cryptography"]}.1"',
        ),
        ["the soft floor step pins cryptography off its floor"],
    ),
}


@pytest.mark.parametrize("mutation", list(_FLOOR_MUTATIONS))
def test_the_floor_cell_check_judges_a_mutated_django_workflow(mutation: str) -> None:
    """Each mutation of the floor cell yields exactly its own problems, a harmless one none."""
    mutate, expected = _FLOOR_MUTATIONS[mutation]
    bounds = _pyproject_lower_bounds()
    text = (WORKFLOW_DIR / "django.yml").read_text(encoding="utf-8")
    mutated = mutate(text, bounds)

    assert mutated != text
    assert _floor_cell_problems(mutated, bounds) == expected


#: The problem of a ``uv run`` that may re-lock with no sync before it.
_UNSYNCED_RUN = "may re-lock with no uv sync before it in its job"
#: The problem of a ``uv run`` that syncs away the pins of an earlier ``uv pip install``.
_PINS_REVERTED = "syncs away the job's uv pip install pins without --no-sync"
#: The problem of an upgrading ``uv sync`` no lock check it can rely on precedes.
_UNCHECKED_UPGRADE = "upgrades with no unconditional uv lock --check before it"
#: The workflow files that run a ``uv sync``; the check must read one in each.
_UV_SYNCING_WORKFLOWS = ("django.yml", "kanban-pages.yml", "postgres.yml")


def _local_actions_dir_problems(root: Path) -> list[str]:
    """The problem of a ``.github/actions`` directory under ``root``: no reader here reads it."""
    actions = root / ".github" / "actions"
    if not actions.exists():
        return []
    return [f"{actions} exists; the uv lock check does not read its actions"]


def _env_keys(env: object) -> list[str]:
    """The lock-deciding ``UV_*`` names a workflow, job or step ``env:`` block sets."""
    return [str(key) for key in _mapping(env) if _UV_LOCK_ENV.fullmatch(str(key))]


def _uv_lock_problems(workflow_text: str) -> list[str]:
    """Each way ``workflow_text`` installs or runs anything but exactly ``uv.lock``.

    The reader guards against honest drift (a well-meaning workflow edit), not
    deliberate evasion: quote-split spellings, ``uv tool run uv``, a ``--project``
    pointing elsewhere and a quoted ``"--locked"`` are out of its reach.

    - A ``uv sync`` carries ``--locked``, unless it upgrades one package
      (``--upgrade-package X``, ``--upgrade-package=X``, ``-P X``, ``-PX``): an
      upgrading sync carries no ``--locked``, sits in a step whose ``if:`` never runs it
      past a failure (``always()``, ``failure()``, ``cancelled()``), and follows a
      ``uv lock --check`` of its job that runs unconditionally. Such a check is its
      step's first simple command, followed by nothing but ``;`` or its line end, with
      ``uv`` its first word past ``VAR=val`` / ``env`` / ``time``; the step has no
      ``if:``, no ``continue-on-error`` and a shell that stops at a failing command
      (``_runs_with_errexit``, the step's ``shell:`` else the job's, else the
      workflow's ``defaults.run.shell``).
    - No sync carries ``--frozen`` or ``--upgrade``; nothing runs ``uv pip sync`` or a
      uv sync this check cannot read; the only ``uv lock`` is ``uv lock --check``.
    - Nothing runs ``uv add`` or ``uv remove``; ``uv export``, ``uv tree`` and a
      ``uv version`` that writes a version (a positional value or ``--bump``) carry
      ``--locked`` or ``--frozen``; a bare ``uv version`` only reads it.
    - A ``uv run`` with neither ``--no-sync`` nor ``--locked`` of its own (a child
      command's flags are not uv's) may re-lock, so it follows a sync in its job; no
      ``uv run`` upgrades a package.
    - A ``uv run`` after a ``uv pip install`` in its job carries ``--no-sync``.
    - No ``env:`` block and no command sets ``UV_FROZEN``, ``UV_NO_SYNC`` or
      ``UV_LOCKED``.
    - No step runs a local ``uses: ./...`` action, which this check does not read.
    """
    workflow = object_result(yaml.safe_load, workflow_text)
    assert is_object_dict(workflow), "workflow is not a mapping"
    problems = [f"workflow env sets {key}" for key in _env_keys(workflow.get("env"))]
    workflow_shell = _default_shell(workflow, None)
    for job_name, job_node in _jobs(workflow).items():
        job = _mapping(job_node)
        job_shell = _default_shell(job, workflow_shell)
        problems.extend(f"job {job_name!r} env sets {key}" for key in _env_keys(job.get("env")))
        synced = lock_checked = pinned = False
        for step in map(_mapping, _steps(job)):
            at = f"job {job_name!r}, step {str(step.get('name'))!r}"
            uses = str(step.get("uses", ""))
            if uses.startswith(LOCAL_ACTION_PREFIX):
                problems.append(f"{at} runs the local action {uses}")
            problems.extend(f"{at} env sets {key}" for key in _env_keys(step.get("env")))
            checkable = (
                "if" not in step
                and "continue-on-error" not in step
                and _runs_with_errexit(step.get("shell", job_shell))
            )
            forced = _RUNS_PAST_A_FAILURE.search(str(step.get("if", ""))) is not None
            for position, (segment, after) in enumerate(_shell_commands(_step_script(step))):
                subcommand, words = _uv_command(segment)
                flags = set(_lock_flags(words))
                where = f"{at}: {segment}"
                problems.extend(
                    f"{where} sets {match.group(1)}"
                    for match in _UV_LOCK_ENV_SET.finditer(segment)
                )
                upgrades = "--upgrade-package" in flags
                if subcommand == "sync":
                    synced = True
                    if "--frozen" in flags:
                        problems.append(f"{where} carries --frozen")
                    if "--upgrade" in flags:
                        problems.append(f"{where} carries --upgrade")
                    if upgrades and "--locked" in flags:
                        problems.append(f"{where} carries --locked beside --upgrade-package")
                    if upgrades and forced:
                        problems.append(f"{where} upgrades in a step that runs past a failure")
                    if upgrades and not lock_checked:
                        problems.append(f"{where} {_UNCHECKED_UPGRADE}")
                    if not upgrades and "--locked" not in flags:
                        problems.append(f"{where} does not carry --locked")
                elif subcommand == "pip sync":
                    synced = True
                    problems.append(f"{where} installs a requirements file past uv.lock")
                elif subcommand == "?":
                    synced = True
                    problems.append(f"{where} names a uv sync this check cannot read")
                elif subcommand == "pip install":
                    pinned = True
                elif subcommand in _UV_PROJECT_EDITS:
                    problems.append(f"{where} edits pyproject.toml and uv.lock")
                elif (
                    subcommand in _UV_RELOCKING
                    or (subcommand == _UV_VERSION and _uv_version_writes(words))
                ) and not {"--locked", "--frozen"} & flags:
                    problems.append(f"{where} may re-lock without --locked or --frozen")
                elif subcommand == "lock":
                    if "--check" not in words or {"--upgrade", "--upgrade-package"} & flags:
                        problems.append(f"{where} is not a plain uv lock --check")
                    elif (
                        checkable
                        and position == 0
                        and after in ("", ";")
                        and _command_word(segment) == "uv"
                    ):
                        lock_checked = True
                elif subcommand == "run":
                    if not synced and not {"--locked", "--no-sync"} & flags:
                        problems.append(f"{where} {_UNSYNCED_RUN}")
                    if pinned and "--no-sync" not in flags:
                        problems.append(f"{where} {_PINS_REVERTED}")
                    if upgrades or "--upgrade" in flags:
                        problems.append(f"{where} upgrades past uv.lock")
    return problems


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_every_ci_uv_sync_asserts_the_lock_unless_it_upgrades_a_package(path: Path) -> None:
    """Every CI install is exactly ``uv.lock``, by the rules ``_uv_lock_problems`` lists.

    A workflow that syncs must show the check a sync it read, so the row cannot
    pass over a file whose syncs it no longer finds.
    """
    text = path.read_text(encoding="utf-8")
    read = [
        segment
        for job in _jobs(_workflow(path)).values()
        for step in map(_mapping, _steps(_mapping(job)))
        for segment in _shell_segments(_step_script(step))
        if _uv_command(segment)[0] == "sync"
    ]

    assert set(_UV_SYNCING_WORKFLOWS) <= set(WORKFLOW_IDS)
    assert bool(read) is (path.name in _UV_SYNCING_WORKFLOWS)
    assert _uv_lock_problems(text) == []


def test_no_local_action_directory_runs_uv_commands_the_lock_check_cannot_see() -> None:
    """``.github/actions`` does not exist, so no composite action escapes ``_uv_lock_problems``.

    The check reads workflow steps only; a step's local ``uses: ./...`` is refused
    per step, and this row refuses the directory such an action would live in.
    """
    assert _local_actions_dir_problems(REPO_ROOT) == []


def test_the_local_action_directory_check_reports_a_planted_directory(tmp_path: Path) -> None:
    """A ``.github/actions`` directory is one problem; its absence is none."""
    actions = tmp_path / ".github" / "actions"
    before = _local_actions_dir_problems(tmp_path)
    (actions / "setup").mkdir(parents=True)

    assert before == []
    assert _local_actions_dir_problems(tmp_path) == [
        f"{actions} exists; the uv lock check does not read its actions",
    ]


#: A ``run`` script, then each of its segments' uv subcommand and lock flags.
_UV_SEGMENT_READINGS: dict[str, list[tuple[str, list[str]]]] = {
    "cd docs && uv sync": [("", []), ("sync", [])],
    "UV_PYTHON=3.12 uv sync --locked": [("sync", ["--locked"])],
    "uv --directory sub sync --locked": [("sync", ["--locked"])],
    "uv -q --no-cache sync --locked": [("sync", ["--locked"])],
    "uv sync && uv run --locked ruff --version": [("sync", []), ("run", ["--locked"])],
    "uv sync --locked & uv sync": [("sync", ["--locked"]), ("sync", [])],
    "uv sync  # --locked": [("sync", [])],
    "uv sync --upgrade-package=Django": [("sync", ["--upgrade-package"])],
    "uv sync -P Django --group pg": [("sync", ["--upgrade-package"])],
    "uv${UV_FLAGS} sync --locked": [("?", [])],
    'uv run --no-sync python -c "a; b" | uv sync': [("run", ["--no-sync"]), ("sync", [])],
    "uv run pytest -k sync": [("run", [])],
    "uv pip install x && uv pip sync requirements.txt": [("pip install", []), ("pip sync", [])],
    "uv run pytest --locked": [("run", [])],
    "uv run --python 3.12 --locked pytest": [("run", ["--locked"])],
    "uv sync --locked && uv run --max-recursion-depth 3 -PDjango pytest": [
        ("sync", ["--locked"]),
        ("run", ["--upgrade-package"]),
    ],
    "uv run -q --with x --no-sync pytest": [("run", ["--no-sync"])],
    "uv --directory d run --no-sync pytest --locked": [("run", ["--no-sync"])],
    "uv --python-preference only-managed sync --locked": [("sync", ["--locked"])],
    'printf "%s\\n" "a # b"; uv sync --frozen': [("", []), ("sync", ["--frozen"])],
    'uv sync --locked # "--frozen"': [("sync", ["--locked"])],
    "echo '#' ; uv sync": [("", []), ("sync", [])],
    "uv pip -q sync req.txt": [("pip sync", [])],
    "uv pip --cache-dir d install x": [("pip install", [])],
    "uv -q pip -q install x": [("pip install", [])],
    "uv pip show x": [("pip", [])],
    "uv sync -P=Django": [("sync", ["--upgrade-package"])],
    "uv sync --locked 2>&1": [("sync", ["--locked"])],
    "uv lock --check >/dev/null 2>&1": [("lock", [])],
    "uv sync --locked &>log": [("sync", ["--locked"])],
    "if x; then uv sync --locked; fi": [("", []), ("sync", ["--locked"]), ("", [])],
    "uv run -- --no-sync": [("run", [])],
    "uv export --frozen": [("export", ["--frozen"])],
}


@pytest.mark.parametrize("script", list(_UV_SEGMENT_READINGS))
def test_the_uv_lock_check_reads_each_shell_segment_on_its_own(script: str) -> None:
    """Each segment of a ``run`` script reads as its own uv subcommand and lock flags."""
    readings = [_uv_command(segment) for segment in _shell_segments(script)]

    assert [
        (subcommand, _lock_flags(words)) for subcommand, words in readings
    ] == _UV_SEGMENT_READINGS[script]


#: A ``run`` script, then each of its simple commands with the operator after it.
_SHELL_COMMAND_READINGS: dict[str, list[tuple[str, str]]] = {
    "a; b": [("a", ";"), ("b", "")],
    "a && b": [("a", "&&"), ("b", "")],
    "a || b": [("a", "||"), ("b", "")],
    "a | b": [("a", "|"), ("b", "")],
    "a & b": [("a", "&"), ("b", "")],
    "a 2>&1": [("a 2>&1", "")],
    "a &>log": [("a &>log", "")],
    "# x\n\na &&\nb": [("a", "&&"), ("b", "")],
}


@pytest.mark.parametrize("script", list(_SHELL_COMMAND_READINGS))
def test_the_shell_reader_reads_each_command_and_the_operator_after_it(script: str) -> None:
    """Commands read in order, each with the operator after it, ``""`` at its line end."""
    assert _shell_commands(script) == _SHELL_COMMAND_READINGS[script]


#: A ``shell:`` value, then whether a step under it ends on its first failing command.
_ERREXIT_READINGS: dict[str | None, bool] = {
    None: True,
    "bash": True,
    "sh": True,
    "bash --noprofile --norc -eo pipefail {0}": True,
    "sh -e {0}": True,
    "/bin/bash -o pipefail -e {0}": True,
    "bash {0}": False,
    "bash -l {0}": False,
    "bash --login -l {0}": False,
    "bash -x {0}": False,
    "bash -E {0}": False,
    "bash -c 'set +e; . {0}'": False,
    "pwsh -NoProfile -Command \". '{0}'\"": False,
    "pwsh -File {0}": False,
    "xvfb-run -e /dev/stdout bash {0}": False,
    "python -We {0}": False,
}


@pytest.mark.parametrize("shell", list(_ERREXIT_READINGS))
def test_the_errexit_reader_reads_only_a_bash_or_sh_e_option(shell: str | None) -> None:
    """Errexit is the unset default, ``bash`` / ``sh``, or their own ``-e`` option cluster."""
    assert _runs_with_errexit(shell) is _ERREXIT_READINGS[shell]


def _add_job(command: str) -> Callable[[str], str]:
    """A mutation adding to ``django.yml`` a job ``extra`` whose one step runs ``command``."""
    body = "\n".join(f"          {line}" for line in command.splitlines())
    return lambda text: _replace_once(
        text,
        "\n  test:\n",
        (
            "\n  extra:\n    runs-on: ubuntu-latest\n    steps:\n"
            f"      - name: Render\n        run: |\n{body}\n\n  test:\n"
        ),
    )


_LINT_SYNC = "        run: uv sync --locked\n"
_KANBAN_SYNC = "        run: uv sync --locked --python 3.12\n"
_POSTGRES_SYNC = "uv sync --python 3.14 --group pg --upgrade-package Django"
_POSTGRES_STEP = "job 'test-postgres', step 'Install dependencies with latest Django'"
_TEST_STEP = "job 'test', step 'Run Tests (${{ matrix.database }}, ${{ matrix.shard }})'"
_LINT_STEP = "job 'lint', step 'Install dependencies'"
_EXTRA_STEP = "job 'extra', step 'Render'"
_POSTGRES_CHECK = "          uv lock --check\n"
_POSTGRES_UNCHECKED = f"{_POSTGRES_STEP}: {_POSTGRES_SYNC} {_UNCHECKED_UPGRADE}"
_POSTGRES_GATED = f"{_POSTGRES_STEP}: {_POSTGRES_SYNC} upgrades in a step that runs past a failure"
_NO_ERREXIT_DEFAULT = "\ndefaults:\n  run:\n    shell: bash -l {0}\n\njobs:\n"
_PWSH_DEFAULT = "\ndefaults:\n  run:\n    shell: pwsh -NoProfile -Command \". '{0}'\"\n\njobs:\n"
_UV_LOCK_MUTATIONS: dict[str, tuple[str, Callable[[str], str], list[str]]] = {
    "lint-sync-drops-locked": (
        "django.yml",
        lambda text: _replace_once(text, _LINT_SYNC, "        run: uv sync\n"),
        ["job 'lint', step 'Install dependencies': uv sync does not carry --locked"],
    ),
    "lint-sync-frozen": (
        "django.yml",
        lambda text: _replace_once(text, _LINT_SYNC, "        run: uv sync --frozen\n"),
        [
            "job 'lint', step 'Install dependencies': uv sync --frozen carries --frozen",
            "job 'lint', step 'Install dependencies': uv sync --frozen does not carry --locked",
        ],
    ),
    "lint-sync-unreadable": (
        "django.yml",
        lambda text: _replace_once(text, _LINT_SYNC, "        run: uv${UV_FLAGS} sync --locked\n"),
        [
            (
                "job 'lint', step 'Install dependencies': uv${UV_FLAGS} sync --locked "
                "names a uv sync this check cannot read"
            ),
        ],
    ),
    "kanban-sync-becomes-pip-sync": (
        "kanban-pages.yml",
        lambda text: _replace_once(text, _KANBAN_SYNC, "        run: uv pip sync req.txt\n"),
        [
            (
                "job 'build', step 'Install dependencies': uv pip sync req.txt "
                "installs a requirements file past uv.lock"
            ),
        ],
    ),
    "job-runs-uv-run-frozen-without-a-sync": (
        "django.yml",
        _add_job("uv run --frozen python x.py"),
        [f"job 'extra', step 'Render': uv run --frozen python x.py {_UNSYNCED_RUN}"],
    ),
    "job-runs-uv-run-locked-without-a-sync": (
        "django.yml",
        _add_job("uv run --locked python x.py"),
        [],
    ),
    "test-run-locked-after-the-pins": (
        "django.yml",
        lambda text: _replace_once(text, "uv run --no-sync pytest", "uv run --locked pytest"),
        [f'{_TEST_STEP}: uv run --locked pytest -o addopts="$addopts" $targets {_PINS_REVERTED}'],
    ),
    "test-run-frozen-after-the-pins": (
        "django.yml",
        lambda text: _replace_once(text, "uv run --no-sync pytest", "uv run --frozen pytest"),
        [f'{_TEST_STEP}: uv run --frozen pytest -o addopts="$addopts" $targets {_PINS_REVERTED}'],
    ),
    "test-run-tolerates-flags-before-no-sync": (
        "django.yml",
        lambda text: _replace_once(
            text,
            "uv run --no-sync pytest",
            "uv run --frozen --no-sync pytest",
        ),
        [],
    ),
    "postgres-sync-locked": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_SYNC, f"{_POSTGRES_SYNC} --locked"),
        [f"{_POSTGRES_STEP}: {_POSTGRES_SYNC} --locked carries --locked beside --upgrade-package"],
    ),
    "postgres-drops-the-lock-check": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, ""),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-run-after-the-upgrade-sync": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            "uv run --no-sync django-admin --version",
            "uv run django-admin --version",
        ),
        [],
    ),
    "uv-run-child-no-sync-flag": (
        "django.yml",
        _add_job("uv run python x.py --no-sync"),
        [f"{_EXTRA_STEP}: uv run python x.py --no-sync {_UNSYNCED_RUN}"],
    ),
    "test-run-child-no-sync-after-the-pins": (
        "django.yml",
        lambda text: _replace_once(text, "uv run --no-sync pytest", "uv run pytest --no-sync"),
        [f'{_TEST_STEP}: uv run pytest --no-sync -o addopts="$addopts" $targets {_PINS_REVERTED}'],
    ),
    "uv-run-valued-option-then-locked-without-a-sync": (
        "django.yml",
        _add_job("uv run --python 3.12 --locked python x.py"),
        [],
    ),
    "uv-run-upgrades-a-package": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            "uv run --no-sync django-admin",
            "uv run --no-sync --upgrade-package Django django-admin",
        ),
        [
            (
                f"{_POSTGRES_STEP}: uv run --no-sync --upgrade-package Django django-admin "
                "--version upgrades past uv.lock"
            ),
        ],
    ),
    "uv-run-upgrades-everything": (
        "django.yml",
        _add_job("uv run --locked -U python x.py"),
        [f"{_EXTRA_STEP}: uv run --locked -U python x.py upgrades past uv.lock"],
    ),
    "quoted-hash-hides-a-frozen-sync": (
        "django.yml",
        _add_job('printf "%s\\n" "a # b"; uv sync --frozen'),
        [
            f"{_EXTRA_STEP}: uv sync --frozen carries --frozen",
            f"{_EXTRA_STEP}: uv sync --frozen does not carry --locked",
        ],
    ),
    "uv-pip-sync-after-a-global-option": (
        "django.yml",
        _add_job("uv pip -q sync req.txt"),
        [f"{_EXTRA_STEP}: uv pip -q sync req.txt installs a requirements file past uv.lock"],
    ),
    "uv-run-after-a-pip-install-after-a-global-option": (
        "django.yml",
        _add_job("uv pip -q install x && uv run python x.py"),
        [
            f"{_EXTRA_STEP}: uv run python x.py {_UNSYNCED_RUN}",
            f"{_EXTRA_STEP}: uv run python x.py {_PINS_REVERTED}",
        ],
    ),
    "postgres-lock-check-or-true": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          uv lock --check || true\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-after-and": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          true && uv lock --check\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-before-and": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          uv lock --check && echo ok\n",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-after-or": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          false || uv lock --check\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-in-the-background": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          uv lock --check &\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-piped": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          uv lock --check | cat\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-step-has-if": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            f"        run: |\n{_POSTGRES_CHECK}",
            f"        if: always()\n        run: |\n{_POSTGRES_CHECK}",
        ),
        [_POSTGRES_GATED, _POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-step-continues-on-error": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            f"        run: |\n{_POSTGRES_CHECK}",
            f"        continue-on-error: true\n        run: |\n{_POSTGRES_CHECK}",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-in-its-own-step": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            f"        run: |\n{_POSTGRES_CHECK}",
            (
                "        run: uv lock --check\n"
                "      - name: Install dependencies with latest Django\n        run: |\n"
            ),
        ),
        [],
    ),
    "postgres-upgrade-step-has-if": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            f"        run: |\n{_POSTGRES_CHECK}",
            (
                "        run: uv lock --check\n"
                "      - name: Install dependencies with latest Django\n"
                "        if: always()\n        run: |\n"
            ),
        ),
        [_POSTGRES_GATED],
    ),
    "postgres-upgrade-step-has-a-matrix-if": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            f"        run: |\n{_POSTGRES_CHECK}",
            (
                "        run: uv lock --check\n"
                "      - name: Install dependencies with latest Django\n"
                "        if: matrix.x == 'y'\n        run: |\n"
            ),
        ),
        [],
    ),
    "postgres-lock-check-after-the-sync": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            f"{_POSTGRES_CHECK}          {_POSTGRES_SYNC}\n",
            f"          {_POSTGRES_SYNC}\n{_POSTGRES_CHECK}",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-in-another-job": (
        "postgres.yml",
        lambda text: _replace_once(
            _replace_once(text, _POSTGRES_CHECK, ""),
            "\n  test-postgres:\n",
            (
                "\n  lockcheck:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - name: Check\n        run: uv lock --check\n\n  test-postgres:\n"
            ),
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-redirects-stderr": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          uv lock --check 2>&1\n"),
        [],
    ),
    "postgres-lock-check-redirects-both-streams": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          uv lock --check &>lock.log\n",
        ),
        [],
    ),
    "postgres-lock-check-in-a-one-line-if": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          if true; then uv lock --check; fi\n",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-in-an-if-block": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          if true; then\n            uv lock --check\n          fi\n",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-as-an-if-condition": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          if uv lock --check; then echo ok; fi\n",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-negated": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          ! uv lock --check\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-after-a-trailing-or": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          true ||\n          uv lock --check\n",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-after-set-plus-e": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          set +e\n          uv lock --check\n",
        ),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-after-another-command": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          echo x; uv lock --check\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-then-a-semicolon": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          uv lock --check; echo ok\n"),
        [],
    ),
    "postgres-lock-check-under-a-shell-without-errexit": (
        "postgres.yml",
        lambda text: _replace_once(text, "\njobs:\n", _NO_ERREXIT_DEFAULT),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-under-a-pwsh-default": (
        "postgres.yml",
        lambda text: _replace_once(text, "\njobs:\n", _PWSH_DEFAULT),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-job-shell-bash-overrides-the-default": (
        "postgres.yml",
        lambda text: _replace_once(
            _replace_once(text, "\njobs:\n", _NO_ERREXIT_DEFAULT),
            "\n  test-postgres:\n",
            "\n  test-postgres:\n    defaults:\n      run:\n        shell: bash\n",
        ),
        [],
    ),
    "postgres-step-shell-with-errexit-overrides-the-default": (
        "postgres.yml",
        lambda text: _replace_once(
            _replace_once(text, "\njobs:\n", _NO_ERREXIT_DEFAULT),
            f"        run: |\n{_POSTGRES_CHECK}",
            f"        shell: bash -eo pipefail {{0}}\n        run: |\n{_POSTGRES_CHECK}",
        ),
        [],
    ),
    "postgres-lock-check-as-an-echo-argument": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_CHECK, "          echo uv lock --check\n"),
        [_POSTGRES_UNCHECKED],
    ),
    "postgres-lock-check-after-prefixes": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_CHECK,
            "          X=1 env time uv lock --check\n",
        ),
        [],
    ),
    "job-runs-uv-add": (
        "django.yml",
        _add_job("uv add x"),
        [f"{_EXTRA_STEP}: uv add x edits pyproject.toml and uv.lock"],
    ),
    "job-runs-uv-remove": (
        "django.yml",
        _add_job("uv remove x"),
        [f"{_EXTRA_STEP}: uv remove x edits pyproject.toml and uv.lock"],
    ),
    "job-runs-uv-export": (
        "django.yml",
        _add_job("uv export -o r.txt"),
        [f"{_EXTRA_STEP}: uv export -o r.txt may re-lock without --locked or --frozen"],
    ),
    "job-runs-uv-tree": (
        "django.yml",
        _add_job("uv tree"),
        [f"{_EXTRA_STEP}: uv tree may re-lock without --locked or --frozen"],
    ),
    "job-runs-uv-version": ("django.yml", _add_job("uv version"), []),
    "job-runs-uv-version-bump": (
        "django.yml",
        _add_job("uv version --bump patch"),
        [f"{_EXTRA_STEP}: uv version --bump patch may re-lock without --locked or --frozen"],
    ),
    "job-runs-uv-version-value": (
        "django.yml",
        _add_job("uv version 0.2.0"),
        [f"{_EXTRA_STEP}: uv version 0.2.0 may re-lock without --locked or --frozen"],
    ),
    "job-runs-uv-export-frozen": ("django.yml", _add_job("uv export --frozen -o r.txt"), []),
    "job-runs-uv-tree-locked": ("django.yml", _add_job("uv tree --locked"), []),
    "workflow-env-sets-uv-frozen": (
        "django.yml",
        lambda text: _replace_once(
            text,
            "\npermissions:\n",
            "\nenv:\n  UV_FROZEN: 1\n\npermissions:\n",
        ),
        ["workflow env sets UV_FROZEN"],
    ),
    "job-env-sets-uv-no-sync": (
        "django.yml",
        lambda text: _replace_once(
            text,
            "\n  lint:\n",
            "\n  lint:\n    env:\n      UV_NO_SYNC: 1\n",
        ),
        ["job 'lint' env sets UV_NO_SYNC"],
    ),
    "step-env-sets-uv-locked": (
        "django.yml",
        lambda text: _replace_once(
            text,
            _LINT_SYNC,
            f"        env:\n          UV_LOCKED: 1\n{_LINT_SYNC}",
        ),
        [f"{_LINT_STEP} env sets UV_LOCKED"],
    ),
    "command-prefix-sets-uv-frozen": (
        "django.yml",
        lambda text: _replace_once(
            text,
            _LINT_SYNC,
            "        run: UV_FROZEN=1 uv sync --locked\n",
        ),
        [f"{_LINT_STEP}: UV_FROZEN=1 uv sync --locked sets UV_FROZEN"],
    ),
    "export-sets-uv-no-sync": (
        "django.yml",
        _add_job("export UV_NO_SYNC=1"),
        [f"{_EXTRA_STEP}: export UV_NO_SYNC=1 sets UV_NO_SYNC"],
    ),
    "job-runs-a-bare-uv-lock": (
        "django.yml",
        _add_job("uv lock"),
        [f"{_EXTRA_STEP}: uv lock is not a plain uv lock --check"],
    ),
    "job-runs-uv-lock-upgrade-package": (
        "django.yml",
        _add_job("uv lock --check -P Django"),
        [
            f"{_EXTRA_STEP}: uv lock --check -P Django is not a plain uv lock --check",
        ],
    ),
    "lint-sync-upgrades-everything": (
        "django.yml",
        lambda text: _replace_once(text, _LINT_SYNC, "        run: uv sync --locked -U\n"),
        [f"{_LINT_STEP}: uv sync --locked -U carries --upgrade"],
    ),
    "postgres-sync-upgrades-everything": (
        "postgres.yml",
        lambda text: _replace_once(text, _POSTGRES_SYNC, f"{_POSTGRES_SYNC} --upgrade"),
        [f"{_POSTGRES_STEP}: {_POSTGRES_SYNC} --upgrade carries --upgrade"],
    ),
    "step-runs-a-local-action": (
        "django.yml",
        lambda text: _replace_once(
            text,
            "      - name: Set up Python 3.12\n",
            (
                "      - name: Local\n        uses: ./.github/actions/setup\n"
                "      - name: Set up Python 3.12\n"
            ),
        ),
        ["job 'lint', step 'Local' runs the local action ./.github/actions/setup"],
    ),
    "postgres-sync-attached-short-upgrade": (
        "postgres.yml",
        lambda text: _replace_once(
            text,
            _POSTGRES_SYNC,
            "uv sync --python 3.14 --group pg -PDjango",
        ),
        [],
    ),
}


@pytest.mark.parametrize("mutation", list(_UV_LOCK_MUTATIONS))
def test_the_uv_lock_check_judges_a_mutated_workflow(mutation: str) -> None:
    """Each mutation of a workflow's uv commands yields exactly its own problems, a harmless one none."""
    name, mutate, expected = _UV_LOCK_MUTATIONS[mutation]
    text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
    mutated = mutate(text)

    assert mutated != text
    assert _uv_lock_problems(mutated) == expected


#: Files the project's ruff config excludes, each holding source ``ruff format`` would change.
RUFF_EXCLUDED_FILES = (
    ("docs/example.md", "# Example\n\n```python\nx = [1,2 ,3]\n```\n"),
    ("hunt-ws/copy/example.py", "x = [1,2 ,3]\n"),
)


def _ruff_format(
    root: Path,
    *args: str,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``ruff format`` with ``args`` in ``root``, which holds a copy of this pyproject."""
    shutil.copy(REPO_ROOT / "pyproject.toml", root / "pyproject.toml")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            *args,
        ],
        cwd=root,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("mode", ["check", "write", "stdin"])
@pytest.mark.parametrize(
    ("relative", "text"),
    RUFF_EXCLUDED_FILES,
    ids=[relative for relative, _ in RUFF_EXCLUDED_FILES],
)
def test_ruff_format_skips_an_excluded_file_named_explicitly(
    tmp_path: Path,
    relative: str,
    text: str,
    mode: str,
) -> None:
    """A path ruff's config excludes stays unformatted when it is named, not only when walked.

    Fenced Python in a ``.md`` is verbatim example content and a ``hunt-ws/`` tree is
    evidence kept as found. A directory run skips both through ``exclude`` /
    ``extend-exclude``; ``force-exclude`` makes a named path (a touched-paths format
    run) and ``--stdin-filename`` skip them too.
    """
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    if mode == "stdin":
        result = _ruff_format(tmp_path, "--stdin-filename", relative, "-", stdin=text)
        assert (result.returncode, result.stdout) == (0, text), result.stderr
        return
    result = _ruff_format(tmp_path, *(["--check"] if mode == "check" else []), relative)
    assert result.returncode == 0, result.stdout + result.stderr
    assert path.read_text(encoding="utf-8") == text


def test_ruff_format_still_checks_a_named_python_file(tmp_path: Path) -> None:
    """Control: the same config and invocation report a named, non-excluded ``.py``."""
    (tmp_path / "example.py").write_text("x = [1,2 ,3]\n", encoding="utf-8")
    result = _ruff_format(tmp_path, "--check", "example.py")
    assert result.returncode == 1, result.stdout + result.stderr


#: The live tier the raw-post sweep reads: every ``.py`` directly under it.
LIVE_TIER = REPO_ROOT / "examples" / "fakeshop" / "test_query"

#: The Django test-client methods that put a hand-built request on the wire.
RAW_POST_METHODS = frozenset({"generic", "post"})

#: The declaration a raw post carries (spec-043 Decision 11): a full-line comment
#: naming what the raw envelope is, with a reason after the colon.
RAW_POST_EXEMPTION = re.compile(r"^#\s*raw-envelope exemption:\s*\S")


def _full_line_comments(source: str) -> dict[int, str]:
    """Every comment that is alone on its line, keyed by its 1-based line number."""
    comments: dict[int, str] = {}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and not token.line[: token.start[1]].strip():
            comments[token.start[0]] = token.string
    return comments


def _raw_posts(path: Path) -> tuple[list[str], list[str]]:
    """``(undeclared, declared)`` ``file:line: callee`` entries for each raw post in ``path``.

    A call is declared when the contiguous block of full-line comments directly
    above the line it starts on carries ``RAW_POST_EXEMPTION``; a blank or code
    line ends the block.
    """
    source = path.read_text(encoding="utf-8")
    comments = _full_line_comments(source)
    undeclared: list[tuple[int, str]] = []
    declared: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source, filename=str(path))):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in RAW_POST_METHODS
        ):
            continue
        line = node.lineno - 1
        block: list[str] = []
        while line in comments:
            block.append(comments[line])
            line -= 1
        entry = (node.lineno, f"{path}:{node.lineno}: {ast.unparse(node.func)}(")
        if any(RAW_POST_EXEMPTION.match(comment) for comment in block):
            declared.append(entry)
        else:
            undeclared.append(entry)
    return [text for _, text in sorted(undeclared)], [text for _, text in sorted(declared)]


def _live_tier_modules() -> list[Path]:
    paths = sorted(LIVE_TIER.glob("*.py"))
    assert LIVE_TIER / "test_transport_api.py" in paths, f"live tier not found at {LIVE_TIER}"
    return paths


def test_no_live_tier_module_posts_raw_without_a_declared_exemption() -> None:
    """Every raw ``.post(`` / ``.generic(`` in the live tier declares its exemption.

    spec-043 Decision 11: a live row posts through ``TestClient`` /
    ``AsyncTestClient`` (directly or through ``graphql_client.py``) unless the
    raw envelope is its subject - a hand-built multipart envelope, a malformed or
    byte-exact body, a content-type or charset probe, a header or CSRF shape the
    client cannot carry. Such a call carries a ``# raw-envelope exemption:
    <what the envelope is>`` comment in the comment block directly above the line
    it starts on, sync or async alike.

    Deliberate limits. Any ``.post(`` / ``.generic(`` attribute call counts,
    whatever its receiver, so a non-client ``.post`` would have to declare too;
    that false positive is loud and one line to fix. A ``getattr(client,
    "post")`` lookup is not seen. The sanctioned paths sit outside the corpus by
    construction: ``graphql_client.py::post_graphql_raw`` (the shared
    raw-envelope helper) and the package client's own ``request``. The declared
    count must be non-zero, so a corpus the sweep cannot read fails rather than
    passes.
    """
    undeclared: list[str] = []
    declared: list[str] = []
    for path in _live_tier_modules():
        found, ok = _raw_posts(path)
        undeclared += found
        declared += ok
    assert declared, f"no declared raw post found under {LIVE_TIER}; the sweep read nothing"
    assert not undeclared, (
        "raw .post( / .generic( without a declared exemption in the live tier:\n"
        + "\n".join(undeclared)
        + "\nRoute it through TestClient / AsyncTestClient, or declare the raw envelope"
        " with a '# raw-envelope exemption: <reason>' comment directly above the call."
    )


@pytest.mark.parametrize(
    ("body", "callee"),
    [
        ("response = Client().post('/graphql/', data=raw)\n", "Client().post"),
        ("response = await AsyncClient().post('/graphql/', data=raw)\n", "AsyncClient().post"),
        ("response = client.generic('POST', '/graphql/', data=raw)\n", "client.generic"),
        (
            "# raw-envelope exemption: a byte-exact body\n\nresponse = client.post('/g/')\n",
            "client.post",
        ),
        (
            (
                "# raw-envelope exemption: a byte-exact body\nclient = Client()\n"
                "response = client.post('/g/')\n"
            ),
            "client.post",
        ),
        ("# raw-envelope exemption:\nresponse = client.post('/g/')\n", "client.post"),
        ("response = client.post('/g/')  # raw-envelope exemption: inline\n", "client.post"),
    ],
    ids=[
        "sync-post",
        "async-post",
        "generic",
        "blank-line-breaks-the-block",
        "code-line-breaks-the-block",
        "no-reason",
        "trailing-comment",
    ],
)
def test_the_raw_post_sweep_reports_an_undeclared_call(
    tmp_path: Path,
    body: str,
    callee: str,
) -> None:
    """Each undeclared shape is reported with its file, its line and its callee."""
    planted = tmp_path / "test_planted_api.py"
    planted.write_text(f"# a planted live module\n{body}")
    undeclared, declared = _raw_posts(planted)
    assert declared == [], declared
    assert len(undeclared) == 1, undeclared
    assert undeclared[0].startswith(f"{planted}:"), undeclared[0]
    assert undeclared[0].endswith(f": {callee}("), undeclared[0]


def test_the_raw_post_sweep_accepts_a_declared_call(tmp_path: Path) -> None:
    """The negative direction: a marker anywhere in the block directly above declares it."""
    planted = tmp_path / "test_planted_api.py"
    planted.write_text(
        "async def row(client):\n"
        "    # raw-envelope exemption: a hand-built multipart envelope\n"
        "    # with an arbitrary file label.\n"
        "    response = await client.post(\n"
        "        '/g/',\n"
        "    )\n"
        "    return client.query('{ x }')\n",
    )
    assert _raw_posts(planted) == ([], [f"{planted}:4: client.post("])


#: The archive the spec-authoring flow moves every completed spec into. It holds
#: the archived specs and the process doc ``NEXT.md``; their ``-terms.csv`` and
#: ``-rationale.md`` companions go one level down in ``appx/``.
SPEC_ARCHIVE = "docs/SPECS"
SPEC_APPENDIX = f"{SPEC_ARCHIVE}/appx"

#: A spec's file name, and a companion's: the stem plus its companion suffix.
SPEC_NAME = re.compile(r"spec-\d{3}-.+\.md")
SPEC_COMPANION_NAME = re.compile(r"spec-\d{3}-.+-(?:terms\.csv|rationale\.md)")


def _misplaced_archive_files(paths: Iterable[str]) -> list[str]:
    """Return one formatted violation per archive path outside the archive layout.

    ``docs/SPECS/`` holds archived specs and ``NEXT.md`` and ``docs/SPECS/appx/``
    holds their companions, nothing else at either level and no other
    subdirectory. Both glossary lookups (the terms importer and
    ``check_spec_glossary.py``) accept a CSV beside its spec as well as under
    ``appx/``, so a companion left beside an archived spec changes no gate result
    and nothing else would notice it. Whether a companion still has its spec is
    ``scripts/check_all_spec_glossaries.py``'s check, not this one. A pure function
    over repo-relative paths, so the rows below can feed it layouts the live tree
    never holds.
    """
    violations: list[str] = []
    for path in sorted(paths):
        parent, _, name = path.rpartition("/")
        if parent == SPEC_ARCHIVE:
            if SPEC_COMPANION_NAME.fullmatch(name):
                violations.append(f"{path}: an archived spec's companion goes to {SPEC_APPENDIX}/")
            elif name != "NEXT.md" and not SPEC_NAME.fullmatch(name):
                violations.append(f"{path}: {SPEC_ARCHIVE}/ holds only specs and NEXT.md")
        elif parent == SPEC_APPENDIX:
            if not SPEC_COMPANION_NAME.fullmatch(name):
                violations.append(
                    f"{path}: {SPEC_APPENDIX}/ holds only -terms.csv and -rationale.md companions",
                )
        else:
            violations.append(f"{path}: {SPEC_ARCHIVE}/ has no subdirectory but appx/")
    return violations


def _committable_archive_files() -> list[str]:
    """Return every committable path under ``docs/SPECS/``, repo-relative.

    The same git oracle as ``_committable_python_files`` (tracked, plus untracked
    but not ignored), so an ignored scratch file never fails the row and a
    misplaced file fails it before it is staged.
    """
    completed = _git.run_git(
        REPO_ROOT,
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
        "--",
        SPEC_ARCHIVE,
    )
    assert completed.returncode == 0, (
        f"git ls-files failed ({completed.returncode}): {completed.stderr.strip()}"
    )
    return [name for name in completed.stdout.split("\0") if name]


def test_the_spec_archive_holds_only_specs_and_their_appx_companions() -> None:
    """Every file under ``docs/SPECS/`` sits where the archive layout puts it."""
    paths = _committable_archive_files()
    # An answer missing either level would pass the layout row on nothing.
    assert any(path.startswith(f"{SPEC_APPENDIX}/") for path in paths), paths
    assert f"{SPEC_ARCHIVE}/NEXT.md" in paths, paths
    assert _misplaced_archive_files(paths) == []


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        pytest.param(
            "docs/SPECS/spec-001-x-0_0_1-terms.csv",
            "an archived spec's companion goes to docs/SPECS/appx/",
            id="terms-csv-beside-an-archived-spec",
        ),
        pytest.param(
            "docs/SPECS/spec-001-x-0_0_1-rationale.md",
            "an archived spec's companion goes to docs/SPECS/appx/",
            id="rationale-beside-an-archived-spec",
        ),
        pytest.param(
            "docs/SPECS/notes.md",
            "docs/SPECS/ holds only specs and NEXT.md",
            id="foreign-file-in-the-archive",
        ),
        pytest.param(
            "docs/SPECS/appx/spec-001-x-0_0_1.md",
            "docs/SPECS/appx/ holds only -terms.csv and -rationale.md companions",
            id="spec-in-appx",
        ),
        pytest.param(
            "docs/SPECS/appx/spec-001-x-0_0_1-notes.md",
            "docs/SPECS/appx/ holds only -terms.csv and -rationale.md companions",
            id="foreign-file-in-appx",
        ),
        pytest.param(
            "docs/SPECS/appx/old/spec-001-x-0_0_1-terms.csv",
            "docs/SPECS/ has no subdirectory but appx/",
            id="nested-directory",
        ),
    ],
)
def test_the_archive_layout_sweep_reports_a_misplaced_file(path: str, reason: str) -> None:
    """Each misplaced file is reported once, with its path and the rule it breaks."""
    layout = [
        "docs/SPECS/NEXT.md",
        "docs/SPECS/spec-001-x-0_0_1.md",
        "docs/SPECS/appx/spec-001-x-0_0_1-terms.csv",
        path,
    ]
    assert _misplaced_archive_files(layout) == [f"{path}: {reason}"]


def test_the_archive_layout_sweep_accepts_the_archive_layout() -> None:
    """The negative direction: an archived spec with both companions under ``appx/``."""
    layout = [
        "docs/SPECS/NEXT.md",
        "docs/SPECS/spec-001-x-0_0_1.md",
        "docs/SPECS/appx/spec-001-x-0_0_1-terms.csv",
        "docs/SPECS/appx/spec-001-x-0_0_1-rationale.md",
    ]
    assert _misplaced_archive_files(layout) == []
