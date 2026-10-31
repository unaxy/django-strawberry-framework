"""Shared real primary-key column models for package metadata and native primitive acceptance."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models as db_models
from django.db.models.expressions import Combinable

__all__ = (
    "_BigKeyed",
    "_BigKeyedProfile",
    "_DecimalKeyed",
    "_DecimalKeyedHolder",
    "_UuidKeyed",
    "_UuidKeyedProfile",
)


class _UuidKeyed(db_models.Model):
    """A row keyed by a UUID column."""

    code: db_models.UUIDField[str | uuid.UUID, uuid.UUID] = db_models.UUIDField(
        primary_key=True,
    )

    class Meta:
        managed = False
        app_label = "test_pk_alias_columns"


class _UuidKeyedProfile(db_models.Model):
    """A row whose primary key is a one-to-one key into a ``_UuidKeyed``."""

    owner: db_models.OneToOneField[_UuidKeyed | Combinable, _UuidKeyed] = db_models.OneToOneField(
        _UuidKeyed,
        on_delete=db_models.CASCADE,
        primary_key=True,
        related_name="+",
    )
    # Key column Django adds beside ``owner``, declared for the type checker.
    owner_id: uuid.UUID

    class Meta:
        managed = False
        app_label = "test_pk_alias_columns"


class _BigKeyed(db_models.Model):
    """A row keyed by a signed 64-bit column."""

    code: db_models.BigIntegerField[float | int | str | Combinable, int] = (
        db_models.BigIntegerField(primary_key=True)
    )

    class Meta:
        managed = False
        app_label = "test_pk_alias_columns"


class _BigKeyedProfile(db_models.Model):
    """A row whose primary key is a one-to-one key into a ``_BigKeyed``."""

    owner: db_models.OneToOneField[_BigKeyed | Combinable, _BigKeyed] = db_models.OneToOneField(
        _BigKeyed,
        on_delete=db_models.CASCADE,
        primary_key=True,
        related_name="+",
    )
    label: db_models.TextField[str | Combinable, str] = db_models.TextField()

    class Meta:
        managed = False
        app_label = "test_pk_alias_columns"


class _DecimalKeyed(db_models.Model):
    """A row keyed by a decimal column."""

    code: db_models.DecimalField[str | float | Decimal | Combinable, Decimal] = (
        db_models.DecimalField(primary_key=True, max_digits=6, decimal_places=2)
    )

    class Meta:
        managed = False
        app_label = "test_pk_alias_columns"


class _DecimalKeyedHolder(db_models.Model):
    """A row keyed to a ``_DecimalKeyed``."""

    owner: db_models.ForeignKey[_DecimalKeyed | Combinable, _DecimalKeyed] = db_models.ForeignKey(
        _DecimalKeyed,
        on_delete=db_models.CASCADE,
        related_name="+",
    )

    class Meta:
        managed = False
        app_label = "test_pk_alias_columns"
