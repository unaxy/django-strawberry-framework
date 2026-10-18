"""Library schema test for the declaration-order invariant the app deliberately carries.

The intentionally cross-referenced declaration order is pinned against the
library schema module directly (self-contained, and invisible to any request).
That the composed project schema publishes the library types is read over real
HTTP in ``examples/fakeshop/test_query/test_schema_composition_api.py``.
"""

from collections.abc import Callable
from types import ModuleType

from apps.library import schema as library_schema
from django_strawberry_framework import DjangoType

#: ``vars`` typed as the ``object`` members a module namespace holds.
_module_vars: Callable[[ModuleType], dict[str, object]] = vars


def test_library_djangotype_declaration_order_stays_awkward() -> None:
    """Pin the real app's intentionally cross-referenced declaration order."""
    declaration_order = [
        name
        for name, value in _module_vars(library_schema).items()
        if isinstance(value, type) and issubclass(value, DjangoType) and value is not DjangoType
    ]

    assert declaration_order.index("LoanType") < declaration_order.index("BookType")
    assert declaration_order.index("LoanType") < declaration_order.index("PatronType")
    assert declaration_order.index("ShelfType") < declaration_order.index("BranchType")
    assert declaration_order.index("MembershipCardType") < declaration_order.index("PatronType")
