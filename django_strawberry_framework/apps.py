"""Django ``AppConfig`` - registers the package and applies its Strawberry patches at app load."""

from typing import TYPE_CHECKING

from django.apps import AppConfig
from typing_extensions import override

if TYPE_CHECKING:
    from django_stubs_ext import StrOrPromise


class DjangoStrawberryFrameworkConfig(AppConfig):
    """Register django-strawberry-framework with Django's app loader."""

    name: str = "django_strawberry_framework"
    # Declared at the base type: ``AppConfig.verbose_name`` is a mutable attribute that
    # accepts a lazy translation, so a plain ``str`` here would narrow it covariantly.
    verbose_name: "StrOrPromise" = "Django Strawberry Framework"

    @override
    def ready(self) -> None:
        """Apply the package's defensive Strawberry patches at app-load time.

        :mod:`django_strawberry_framework._strawberry_patches` is the one
        patch module; its own docstring is the single source of truth for
        exactly which upstream bugs it hardens, and this dispatcher
        deliberately repeats none of that inventory.

        It is gated by the ``APPLY_UPSTREAM_PATCHES`` setting (default
        on); ``apply()`` self-gates, so a consumer who sets
        ``DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}``
        gets none of the patches.

        ``ready()`` is the canonical place to perform one-time setup
        that depends on Django being fully configured. Consumers get
        the patches automatically by having
        ``"django_strawberry_framework"`` in ``INSTALLED_APPS`` - no
        opt-in boilerplate is required. ``apply()`` is idempotent and
        self-healing, so a repeated ``ready()`` (some Django test
        runners fire it more than once) is safe.
        """
        from django_strawberry_framework._strawberry_patches import apply as apply_strawberry  # noqa: PLC0415 - patches load once Django is configured

        apply_strawberry()
