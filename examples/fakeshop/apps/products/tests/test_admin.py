"""Products admin tests for changelist query-param branches."""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.products.models import Category, Item
from apps.products.services import create_users, seed_data

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _admin_client() -> Client:
    """Authenticate a service-seeded staff user for the example's admin actions."""
    create_users(1)
    admin = User.objects.get(username="staff_1")
    admin.is_superuser = True
    admin.save(update_fields=["is_superuser"])
    client = Client()
    client.force_login(admin)
    return client


# ---------------------------------------------------------------------------
# UserAdmin: create_users / delete_users query params
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_user_admin_changelist_no_query_params() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/auth/user/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_admin_create_users_success() -> None:
    create_users(1)
    admin_client = _admin_client()
    before = {user.username for user in User.objects.all()}
    response = admin_client.get("/admin/auth/user/?create_users=2")
    assert response.status_code == 302
    expected_new = {username.rsplit("_", 1)[0] + "_2" for username in before}
    assert set(User.objects.values_list("username", flat=True)) == before | expected_new


@pytest.mark.django_db
def test_user_admin_create_users_zero_does_not_create() -> None:
    create_users(1)
    admin_client = _admin_client()
    before = set(User.objects.values_list("pk", flat=True))
    response = admin_client.get("/admin/auth/user/?create_users=0")
    assert response.status_code == 302
    assert set(User.objects.values_list("pk", flat=True)) == before


@pytest.mark.django_db
def test_user_admin_create_users_invalid() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/auth/user/?create_users=abc", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for create_users" in response.content


@pytest.mark.django_db
def test_user_admin_delete_users_int_mode_success() -> None:
    create_users(1)  # 6 non-superusers
    admin_client = _admin_client()
    before = set(User.objects.order_by("pk").values_list("pk", flat=True))
    removed = set(
        User.objects.filter(is_superuser=False).order_by("pk").values_list("pk", flat=True)[:3],
    )
    response = admin_client.get("/admin/auth/user/?delete_users=3")
    assert response.status_code == 302
    assert set(User.objects.values_list("pk", flat=True)) == before - removed


@pytest.mark.django_db
def test_user_admin_delete_users_no_data_warns() -> None:
    create_users(1)
    admin_client = _admin_client()
    User.objects.filter(is_superuser=False).delete()
    before = set(User.objects.values_list("pk", flat=True))
    response = admin_client.get("/admin/auth/user/?delete_users=5")
    assert response.status_code == 302
    # No non-superusers to delete; admin survives
    assert set(User.objects.values_list("pk", flat=True)) == before


@pytest.mark.django_db
def test_user_admin_delete_users_invalid() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/auth/user/?delete_users=garbage", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for delete_users" in response.content


# ---------------------------------------------------------------------------
# ItemAdmin: seed_data / delete_data query params
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_item_admin_changelist_no_query_params() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_item_admin_seed_data_success() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/?seed_data=1")
    assert response.status_code == 302
    assert Category.objects.count() > 0


@pytest.mark.django_db
def test_item_admin_seed_data_zero_does_not_create() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/?seed_data=0")
    assert response.status_code == 302
    assert Category.objects.count() == 0


@pytest.mark.django_db
def test_item_admin_seed_data_invalid() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/?seed_data=abc", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for seed_data" in response.content


@pytest.mark.django_db
def test_item_admin_delete_data_int_mode() -> None:
    seed_data(2)
    admin_client = _admin_client()
    before = set(Item.objects.values_list("pk", flat=True))
    removed = set(Item.objects.order_by("pk").values_list("pk", flat=True)[:3])
    response = admin_client.get("/admin/products/item/?delete_data=3")
    assert response.status_code == 302
    assert set(Item.objects.values_list("pk", flat=True)) == before - removed


@pytest.mark.django_db
def test_item_admin_delete_data_all_mode() -> None:
    seed_data(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/?delete_data=all")
    assert response.status_code == 302
    assert Item.objects.count() == 0


@pytest.mark.django_db
def test_item_admin_delete_data_everything_mode() -> None:
    seed_data(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/?delete_data=everything")
    assert response.status_code == 302
    assert Category.objects.count() == 0


@pytest.mark.django_db
def test_item_admin_delete_data_nothing_to_delete() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/?delete_data=5")
    assert response.status_code == 302
    assert Item.objects.count() == 0


@pytest.mark.django_db
def test_item_admin_delete_data_invalid() -> None:
    create_users(1)
    admin_client = _admin_client()
    response = admin_client.get("/admin/products/item/?delete_data=garbage", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for delete_data" in response.content
