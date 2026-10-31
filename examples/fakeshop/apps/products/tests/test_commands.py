"""Products command tests for catalog/user lifecycle and shard seeding."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from graphql_client import is_json_object, read_attr
from pytest_django import Settings

from apps.products.management.commands import seed_shards as seed_shards_module
from apps.products.models import Category, Item
from apps.products.services import create_users, seed_data


def _databases(settings: Settings) -> dict[str, object]:
    """The ``DATABASES`` setting, checked to be a dict keyed by alias."""
    databases = read_attr(settings, "DATABASES")
    assert is_json_object(databases), databases
    return databases


User = get_user_model()


# ---------------------------------------------------------------------------
# seed_data command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_seed_data_command_default_count() -> None:
    seed_data(0)
    out = StringIO()
    call_command("seed_data", stdout=out)
    output = out.getvalue()
    assert "Done!" in output
    assert Item.objects.count() == 5 * Category.objects.count()
    assert Item.objects.exists()


@pytest.mark.django_db
def test_seed_data_command_explicit_count() -> None:
    seed_data(0)
    out = StringIO()
    call_command("seed_data", "1", stdout=out)
    assert "Done!" in out.getvalue()
    assert Item.objects.count() == Category.objects.count()
    assert Item.objects.exists()


# ---------------------------------------------------------------------------
# delete_data command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_data_command_int_mode() -> None:
    seed_data(2)
    out = StringIO()
    before = set(Item.objects.values_list("pk", flat=True))
    removed = set(Item.objects.order_by("pk").values_list("pk", flat=True)[:3])
    call_command("delete_data", "3", stdout=out)
    output = out.getvalue()
    assert "Deleted" in output
    assert set(Item.objects.values_list("pk", flat=True)) == before - removed


@pytest.mark.django_db
def test_delete_data_command_all_mode() -> None:
    seed_data(1)
    out = StringIO()
    call_command("delete_data", "all", stdout=out)
    assert "Deleted" in out.getvalue()
    assert Item.objects.count() == 0


@pytest.mark.django_db
def test_delete_data_command_everything_mode() -> None:
    seed_data(1)
    out = StringIO()
    call_command("delete_data", "everything", stdout=out)
    assert "Deleted" in out.getvalue()
    assert Category.objects.count() == 0


@pytest.mark.django_db
def test_delete_data_command_nothing_to_delete_warns() -> None:
    seed_data(0)
    out = StringIO()
    call_command("delete_data", "5", stdout=out)
    assert "Nothing to delete" in out.getvalue()


@pytest.mark.django_db
def test_delete_data_command_invalid_negative() -> None:
    seed_data(0)
    err = StringIO()
    call_command("delete_data", "-1", stderr=err)
    assert "positive integer" in err.getvalue()


@pytest.mark.django_db
def test_delete_data_command_invalid_string() -> None:
    seed_data(0)
    err = StringIO()
    call_command("delete_data", "garbage", stderr=err)
    assert "Invalid target" in err.getvalue()


# ---------------------------------------------------------------------------
# create_users command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_users_command_default() -> None:
    create_users(0)
    out = StringIO()
    call_command("create_users", stdout=out)
    output = out.getvalue()
    assert "Done!" in output
    assert User.objects.count() == 6


@pytest.mark.django_db
def test_create_users_command_with_count() -> None:
    create_users(0)
    out = StringIO()
    call_command("create_users", "2", stdout=out)
    assert "Done!" in out.getvalue()
    assert User.objects.count() == 12


# ---------------------------------------------------------------------------
# delete_users command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_users_command_int_mode() -> None:
    create_users(1)
    out = StringIO()
    before = set(User.objects.values_list("pk", flat=True))
    removed = set(User.objects.order_by("pk").values_list("pk", flat=True)[:2])
    call_command("delete_users", "2", stdout=out)
    assert "Deleted" in out.getvalue()
    assert set(User.objects.values_list("pk", flat=True)) == before - removed


@pytest.mark.django_db
def test_delete_users_command_all_mode() -> None:
    create_users(1)
    out = StringIO()
    call_command("delete_users", "all", stdout=out)
    assert "Deleted" in out.getvalue()
    assert not User.objects.exists()


@pytest.mark.django_db
def test_delete_users_command_nothing_to_delete_warns() -> None:
    create_users(0)
    out = StringIO()
    call_command("delete_users", "5", stdout=out)
    assert "Nothing to delete" in out.getvalue()


@pytest.mark.django_db
def test_delete_users_command_invalid_negative() -> None:
    create_users(0)
    err = StringIO()
    call_command("delete_users", "-1", stderr=err)
    assert "positive integer" in err.getvalue()


@pytest.mark.django_db
def test_delete_users_command_invalid_string() -> None:
    create_users(0)
    err = StringIO()
    call_command("delete_users", "garbage", stderr=err)
    assert "Invalid target" in err.getvalue()


# ---------------------------------------------------------------------------
# seed_shards command
# ---------------------------------------------------------------------------


# Django emits an advisory UserWarning when a test overrides DATABASES; these two
# tests do so deliberately (shard-alias setup), so the otherwise-fatal warning is
# scoped-ignored here rather than globally (see pytest.ini filterwarnings).
@pytest.mark.filterwarnings("ignore:Overriding setting DATABASES:UserWarning")
def test_seed_shards_command_raises_when_shard_alias_missing(settings: Settings) -> None:
    """When ``shard_b`` isn't declared in DATABASES, the command must raise CommandError.

    Forces ``shard_b`` absence via the ``settings`` fixture so the test is
    environment-independent - it passes both under default and under
    ``FAKESHOP_SHARDED=1``. Under the env-var case ``shard_b`` would
    otherwise be present in ``DATABASES`` and the command would proceed
    past the alias-missing guard into real ``migrate`` / seeding (which
    pytest-django's database-access guard would then reject for an
    undeclared `@pytest.mark.django_db(databases=...)`).
    """
    settings.DATABASES = {"default": _databases(settings)["default"]}

    out = StringIO()
    with pytest.raises(CommandError, match="shard_b"):
        call_command("seed_shards", stdout=out)


@pytest.mark.django_db(databases=["default"])
@pytest.mark.filterwarnings("ignore:Overriding setting DATABASES:UserWarning")
def test_seed_shards_command_runs_when_shard_alias_present(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``shard_b`` is present in DATABASES, the command runs end-to-end against ``default`` only."""
    seed_data(0)
    databases = _databases(settings)
    settings.DATABASES = {
        **databases,
        "shard_b": databases["default"],  # alias both to the same test DB
    }

    # Patch SHARD_ALIASES so we only operate against ``default`` - pytest's transactional DB
    # only reaches ``default`` and we don't want to mutate production-style files.

    monkeypatch.setattr(seed_shards_module, "SHARD_ALIASES", ("default",))

    out = StringIO()
    call_command("seed_shards", "--count", "1", stdout=out)
    output = out.getvalue()
    assert "Secondary shard populated." in output
