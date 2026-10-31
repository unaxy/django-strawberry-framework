"""Restore test-local Django model registrations across every test tree.

The repo-root conftest installs the autouse fixture so live HTTP tests and app
unit tests receive the same cleanup as package tests. Module-bound models stay
registered; a late import registering one fails its importing test instead of
silently damaging later relation reads.
"""

import sys
from collections.abc import Iterator

import pytest
from django.apps import apps
from django.db.models import Model


@pytest.fixture(autouse=True)
def _restore_app_registry(request: pytest.FixtureRequest) -> Iterator[None]:
    """Leave ``django.apps.apps`` holding exactly the models the test found.

    Django registers a model in ``django.apps.apps.all_models[app_label]`` at class
    creation and nothing ever unregisters it, so a model declared inside a test or a
    function-scope fixture would otherwise outlive that test for the rest of the worker
    process:

    * it stays visible to ``apps.get_models()`` and to any sweep that enumerates the
      registry, which is how an unrelated test's "every model" assertion acquires a
      neighbour's fixture;
    * it stays wired into the relation tree of whatever real model it points at, so
      ``Category._meta.related_objects`` keeps naming a class the declaring test
      already discarded;
    * re-running the declaring test in the same process re-registers the same
      ``(app_label, model_name)`` key, and Django answers that with
      ``RuntimeWarning: Model ... was already registered`` - an error under this
      suite's ``filterwarnings = error`` policy.

    The snapshot shallow-copies each app label's inner dict; the restore writes
    back IN PLACE (``clear`` then ``update``) because ``AppConfig.import_models``
    binds ``AppConfig.models`` to the very dict object stored in
    ``all_models[label]`` - rebinding ``all_models[label]`` to a fresh dict would
    leave every installed app's ``AppConfig`` still pointing at the polluted one.
    Labels the test invented (``all_models`` is a ``defaultdict``, so declaring a
    model under an uninstalled label such as ``tests`` creates the key) are
    dropped outright.

    ``apps.clear_cache()`` runs last: ``Apps.get_models`` is cached and every
    ``_meta`` relation tree (``_relation_tree``, ``related_objects``) computed
    while the synthetic models were registered still names them, so restoring
    the registry without expiring those caches restores nothing observable.

    Autouse suite-wide rather than per-package because the invariant is the same in
    every module and a module that forgets to opt in is exactly the leak this exists
    to stop. Only a ``django_db``-marked test requests the public ``db`` fixture
    before taking the snapshot. It honors the marker's transaction and alias
    options, so teardown restores the registry before the transactional flush's
    ``post_migrate`` recreates content types; a test that builds a model therefore
    needs no manual ``all_models`` pop of its own. What it does NOT cover:

    (a) Models declared at module import (``tests/_relation_fixtures.py``,
        ``tests/optimizer/_link_models.py``, the ``_Ct*`` family in
        ``tests/test_permissions.py``, ``tests/optimizer/test_nested_index_advisory.py``,
        ``tests/_filter_key_models.py::_UuidKeyed``) are registered before any test
        runs, so they sit inside every snapshot; import-time leakage is not fixed here.
        That holds only while every consumer imports such a module at module level. A
        module first imported inside a test body registers its models DURING the test
        and stays in ``sys.modules``, so unregistering them would leave every later test
        holding classes Django no longer knows, stripped of their reverse relations; the
        restore keeps those registrations and fails the importing test instead
        (``_restore_app_registry_to``).
    (b) ``apps.clear_cache()`` does not expire the package's own model-keyed caches
        (``django_strawberry_framework/permissions.py::_edge_plan``'s ``lru_cache``,
        ``django_strawberry_framework/utils/relations.py::_classify_path_cached`` and
        ``::_path_traverses_to_many_cached``) nor ``django_strawberry_framework.registry``;
        the opt-in ``isolate_global_registry`` fixture handles the registry.
    (c) ``tests/utils/test_querysets.py::_ProxyTargetCategory`` and
        ``tests/utils/test_querysets.py::_ProxyTargetHolder`` register in a private
        ``Meta.apps`` and are outside the snapshot by design.
    """
    if "django_db" in request.keywords:
        request.getfixturevalue("db")
    snapshot = {label: dict(models) for label, models in apps.all_models.items()}
    try:
        yield
    finally:
        kept = _restore_app_registry_to(snapshot)
    if kept:
        names = ", ".join(f"{model.__module__}.{model.__qualname__}" for model in kept)
        pytest.fail(
            f"{names} registered with django.apps during this test from a module that stays "
            "imported; import that module at module level so its models register before "
            "any test runs",
            pytrace=False,
        )


def _declared_at_module_scope(model: type[Model]) -> bool:
    """Return whether ``model`` stays reachable by its qualified name from its module.

    A class declared inside a function or fixture carries ``<locals>`` in its
    qualified name (or, built with ``type()``, is bound nowhere), so nothing
    outlives the test that holds it. A module-scope class stays bound for as long
    as ``sys.modules`` keeps its module: the rest of the worker process.
    """
    owner = sys.modules.get(model.__module__)
    for part in model.__qualname__.split("."):
        owner = getattr(owner, part, None)
    return owner is model


def _restore_app_registry_to(
    snapshot: dict[str, dict[str, type[Model]]],
) -> list[type[Model]]:
    """Restore ``apps.all_models`` to ``snapshot`` and return the module-scope models kept.

    Every model registered since ``snapshot`` is unregistered except one declared at
    module scope of a still-imported module: that module is never imported again, so
    the class it holds is the only one any later test can reach, and dropping it from
    the registry would strip its reverse relations for every later test. Those stay
    registered and are returned for the caller to report.
    """
    kept = {
        (label, name): model
        for label, registered in apps.all_models.items()
        for name, model in registered.items()
        if snapshot.get(label, {}).get(name) is not model and _declared_at_module_scope(model)
    }
    added_labels = [label for label in apps.all_models if label not in snapshot]
    changed = bool(added_labels) or any(
        apps.all_models[label] != models for label, models in snapshot.items()
    )
    if changed:
        for label, models in snapshot.items():
            live = apps.all_models[label]
            live.clear()
            live.update(models)
        for label in added_labels:
            del apps.all_models[label]
        for (label, name), model in kept.items():
            apps.all_models[label][name] = model
        apps.clear_cache()
    return list(kept.values())
