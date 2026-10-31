"""Tests for the Strawberry request-body and Relay patches.

System-under-test: :mod:`django_strawberry_framework._strawberry_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

Relay rows pin only installation, idempotence, signature/source drift and the
explicit upstream opt-out. Wire selection names and async row elision are owned
by ``examples/fakeshop/test_query/test_connection_names_api.py``.

The patch wraps :meth:`strawberry.http.base.BaseView.parse_json` to
close two upstream gaps that otherwise surface as unhandled ``500``s:

- **Decode failures.** ``json.loads`` on ``bytes`` raises
  ``UnicodeDecodeError`` when the bytes are not decodable under the encoding
  it detects, and that is a ``ValueError`` rather than a ``JSONDecodeError``,
  so it escapes upstream's ``except`` and becomes a ``500``; a pathologically
  nested document likewise escapes as ``RecursionError``. The wrapper
  translates both into the same ``HTTPException(400, ...)`` Strawberry already
  raises for malformed JSON.
- **Non-envelope bodies.** A body that is not a GraphQL-over-HTTP envelope is
  rejected with ``HTTPException(400, ...)``: a top-level JSON *scalar*, or a
  JSON *array* containing any non-object element. Upstream's
  ``parse_http_body`` handles a JSON object and a JSON array of objects
  (batch) but lets a scalar fall through to ``data.get("query")`` and a
  non-object batch element fall through to ``item.get("query")`` -> raw
  ``AttributeError`` -> ``500``. A well-typed batch ``list`` (every
  element a ``dict``) is passed through so upstream's batch validation
  keeps ownership of enablement / size limits.

The same module also wraps Strawberry's sync and async ``parse_multipart``
delegators. A multipart ``operations`` field may be a batched JSON array, but
the multipart ``map`` field must be an object with string paths. Upstream passes
an array map through the generic JSON helper and then calls ``.items()`` on it,
or lets malformed path values escape as low-level traversal errors. The delegates
turn those client-input failures into Strawberry's controlled ``400`` while
leaving accepted multipart behavior and non-structural consumer failures alone.

And it rebinds the ``strawberry.relay.types`` connection-page check
``ListConnection.resolve_connection`` calls, so a page whose ``edges`` /
``pageInfo`` a ``NameConverter`` respells still reads its rows. That outcome is
earned over real HTTP in ``examples/fakeshop/test_query/test_library_api.py``
(``test_snake_case_page_info_only_page_reports_has_next_page``); the rows here
pin its install lifecycle and the upstream call shape it refuses to run without.

Because the non-envelope scalar guard is a request-*body* contract enforced from
a generic JSON helper, ``apply()`` also installs
:func:`_patched_parse_query_params` - a delegate that runs upstream's own
``BaseView.parse_query_params`` with a context flag the wrapper reads to skip
the guard while keeping the decode-failure translation - so the guard never fires on
upstream's GET ``variables`` / ``extensions`` parses, where upstream has
its own precise per-param handling (``null`` -> ``None`` -> the request
executes; a scalar -> a per-param 400). Every wire-observable outcome of
both the envelope guard and the shield - rejected scalar and
non-object-batch bodies, object / null / malformed / scalar GET params,
and the RecursionError 400 on a nested body or GET param - is earned
over real HTTP in ``examples/fakeshop/test_query/test_products_api.py``.
The POST-body ``{not json`` row lives in
``examples/fakeshop/test_query/test_transport_api.py``.
The rows here pin the parse semantics that have no wire shape of their
own (the falsy skip, the well-typed batch handed on to upstream's own
validator), the ``__cause__`` values for UnicodeDecodeError and RecursionError
a live JSON 400 cannot isolate from the view's own decode, multipart structural vs
non-structural translation, and the full install lifecycle.

**What is deliberately absent here.** The strict UTF-8 wire contract
(spec-046 Decision 9) is not in this module: it is package *policy* with
no upstream lifecycle, so gating it on ``APPLY_UPSTREAM_PATCHES`` would
let a consumer disabling temporary bug workarounds silently lose a
security contract. It belongs to
``views.py::_RequestBodyBoundaryMixin.parse_json``, and its rows - the
nine-shape encoding matrix, the ``__cause__`` attribution, the
patch-opted-out proof - live in ``tests/test_views.py``. This module's
rows therefore assert the *opposite* property on purpose: that upstream's
own ``bytes`` semantics survive here untouched, because that is what a
consumer mounting Strawberry's own view is entitled to.
"""

import functools
import importlib
import inspect
import json
from collections.abc import Callable, Mapping
from types import FunctionType
from unittest import mock

import pytest
import pytest_django
import strawberry
from cross_web import (
    AsyncDjangoHTTPRequestAdapter,
    DjangoHTTPRequestAdapter,
    FormData,
    HTTPException,
)
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.test import RequestFactory
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.base import BaseView
from strawberry.http.sync_base_view import SyncBaseHTTPView
from strawberry.relay import types as relay_types
from strawberry.relay import utils as relay_utils
from typing_extensions import override

from django_strawberry_framework import _strawberry_patches as patches
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView


def test_apply_is_idempotent() -> None:
    """Repeated ``apply()`` calls leave the patch installed (self-healing no-op)."""
    patches.apply()
    patches.apply()
    assert patches._patch_is_installed() is True


def test_apply_reinstalls_when_method_reverted(monkeypatch: pytest.MonkeyPatch) -> None:
    """``apply()`` re-installs if a third party reverted ``BaseView.parse_json``."""
    patches.apply()
    assert patches._patch_is_installed() is True

    monkeypatch.setattr(BaseView, "parse_json", patches._original_parse_json)
    assert patches._patch_is_installed() is False

    patches.apply()
    assert patches._patch_is_installed() is True


def test_patch_is_installed_on_base_view() -> None:
    """By collection, ``AppConfig.ready()`` has installed every patch member."""
    assert BaseView.__dict__["parse_json"] is patches._patched_parse_json
    assert BaseView.__dict__["parse_query_params"] is patches._patched_parse_query_params
    assert SyncBaseHTTPView.__dict__["parse_multipart"] is patches._patched_sync_parse_multipart
    assert AsyncBaseHTTPView.__dict__["parse_multipart"] is patches._patched_async_parse_multipart
    assert (
        read_attr(relay_types, patches._EDGES_CHECK)
        is patches._patched_should_resolve_list_connection_edges
    )


def test_apply_reinstalls_the_connection_page_check_when_reverted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A third party restoring upstream's connection-page check makes ``apply()`` rebind it."""
    patches.apply()
    monkeypatch.setattr(
        relay_types,
        "should_resolve_list_connection_edges",
        patches._original_should_resolve_list_connection_edges,
    )
    assert patches._patch_is_installed() is False

    patches.apply()

    assert patches._patch_is_installed() is True


def test_apply_reinstalls_pair_when_parse_query_params_reverted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A partial revert (only ``parse_query_params``) makes ``apply()`` re-install the pair.

    ``_patch_is_installed()`` must report ``False`` when either method was
    reverted - the scalar guard must never run without its GET shield, so
    a half-installed state has to fall through to the install path.
    """
    patches.apply()
    assert patches._patch_is_installed() is True

    monkeypatch.setattr(BaseView, "parse_query_params", patches._original_parse_query_params)
    assert patches._patch_is_installed() is False

    patches.apply()
    assert patches._patch_is_installed() is True
    assert BaseView.__dict__["parse_query_params"] is patches._patched_parse_query_params


def test_apply_reinstalls_all_members_when_one_multipart_method_reverted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A partial multipart revert heals with the BaseView pair intact.

    The envelope guard's GET shield and the two multipart wrappers form one
    lifecycle: ``apply()`` must not report success while any member was replaced
    by a third party, and reinstallation must restore the complete state rather
    than merely the changed method.
    """
    patches.apply()
    monkeypatch.setattr(
        AsyncBaseHTTPView,
        "parse_multipart",
        patches._original_async_parse_multipart,
    )
    assert patches._patch_is_installed() is False

    patches.apply()

    assert patches._patch_is_installed() is True
    assert BaseView.__dict__["parse_json"] is patches._patched_parse_json
    assert BaseView.__dict__["parse_query_params"] is patches._patched_parse_query_params
    assert SyncBaseHTTPView.__dict__["parse_multipart"] is patches._patched_sync_parse_multipart
    assert AsyncBaseHTTPView.__dict__["parse_multipart"] is patches._patched_async_parse_multipart


def test_patched_parse_json_translates_unicode_decode_error() -> None:
    """An undecodable ``bytes`` body -> controlled ``400``, not a raw ``UnicodeDecodeError``.

    This is the decode-failure gap in isolation, i.e. the state a consumer who mounts
    Strawberry's own view is in. The raise originates inside the delegated
    ``json.loads``: it detects UTF-8 for these bytes (they start with ``{``) and
    then fails to decode ``FF FE``, which upstream's ``except
    json.JSONDecodeError`` does not catch because ``UnicodeDecodeError`` is a
    ``ValueError`` instead. The reason is upstream's own, so the widened catch is
    indistinguishable from the catch it widens.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), b'{"a":"\xff\xfe"}')

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_JSON_PARSE_REASON
    assert type(excinfo.value.__cause__) is UnicodeDecodeError


def test_patched_parse_json_passes_through_valid_json() -> None:
    """The success path is untouched: valid JSON parses exactly as upstream.

    Both an ASCII body and a genuinely multi-byte one (the second carries an
    e-acute, ``C3 A9`` on the wire). ``bytes`` are handed to the delegate
    unchanged - this wrapper does not decode - so what is asserted here is
    upstream's parse, not a package narrowing.
    """
    assert patches._patched_parse_json(BaseView(), b'{"a": 1}') == {"a": 1}
    multibyte = json.dumps({"a": "caf\u00e9"}, ensure_ascii=False).encode("utf-8")
    assert max(multibyte) > 0x7F
    assert patches._patched_parse_json(BaseView(), multibyte) == {"a": "caf\u00e9"}


@pytest.mark.parametrize(
    "encoding",
    [
        pytest.param("utf-16", id="utf-16-with-bom"),
        pytest.param("utf-16-le", id="utf-16-le-no-bom"),
        pytest.param("utf-32", id="utf-32-with-bom"),
        pytest.param("utf-8-sig", id="utf-8-bom"),
    ],
)
def test_patched_parse_json_leaves_upstreams_bytes_semantics_alone(encoding: str) -> None:
    """The wrapper does **not** narrow the accepted encodings, and must not start.

    The inverse of the view boundary's contract, asserted here so the ownership
    split cannot silently collapse back into one site. ``json.loads`` on ``bytes``
    performs RFC 8259 encoding auto-detection, which is documented upstream
    behavior rather than a defect, so a body that reaches *this* wrapper as bytes
    still parses. That is what a consumer who deliberately mounts
    ``strawberry.django.views.GraphQLView`` is entitled to.

    The rejection of these same four shapes is the package view's job
    (``tests/test_views.py``), and this row is what would fail if a future change
    put the strict decode back on the ``APPLY_UPSTREAM_PATCHES`` switch.
    """
    body = '{"a": 1}'.encode(encoding)

    assert patches._patched_parse_json(BaseView(), body) == {"a": 1}


def test_patched_parse_json_passes_a_str_body_through_without_reencoding() -> None:
    """A ``str`` input reaches the delegate as the **same object**, not a round trip.

    The GET query-param and multipart form-field paths arrive already decoded,
    and spec-046 Decision 9 passes them through untouched. Asserting object
    identity rather than equality is what rules out an incidental
    encode-then-decode cycle being introduced on those paths.
    """
    body = '{"a": 1}'
    seen: list[str | bytes] = []

    def _recorder(_view: object, data: str | bytes) -> dict[str, bool]:
        seen.append(data)
        return {"recorded": True}

    with mock.patch.object(patches, "_original_parse_json", _recorder):
        patches._patched_parse_json(BaseView(), body)

    assert seen[0] is body


def test_patched_parse_json_passes_through_list_for_batch_handling() -> None:
    """A JSON array of objects passes through so upstream's batch validation owns it.

    The guard rejects scalars and lists with non-dict elements, but must NOT
    intercept a well-typed batch ``list`` - upstream's ``_validate_batch_request``
    is the path that accepts or rejects enablement / size limits.
    """
    assert patches._patched_parse_json(BaseView(), '[{"query": "{ x }"}]') == [
        {"query": "{ x }"},
    ]
    assert patches._patched_parse_json(BaseView(), "[]") == []


@strawberry.type
class _Query:
    ok: bool = True


_EMPTY_SCHEMA = strawberry.Schema(query=_Query)


def _multipart_request(operations: str, files_map: str, files: Mapping[str, str]) -> HttpRequest:
    """A real Django multipart POST: the ``operations`` / ``map`` fields plus one upload per name."""
    return RequestFactory().post(
        "/graphql/",
        data={
            "operations": operations,
            "map": files_map,
            **{
                name: SimpleUploadedFile(name, content.encode()) for name, content in files.items()
            },
        },
    )


def _sync_request(
    operations: str,
    files_map: str,
    files: Mapping[str, str] | None = None,
) -> DjangoHTTPRequestAdapter:
    """The real sync adapter over a multipart POST."""
    return DjangoHTTPRequestAdapter(_multipart_request(operations, files_map, files or {}))


def _async_request(
    operations: str,
    files_map: str,
    files: Mapping[str, str] | None = None,
) -> AsyncDjangoHTTPRequestAdapter:
    """The real async adapter over a multipart POST."""
    return AsyncDjangoHTTPRequestAdapter(_multipart_request(operations, files_map, files or {}))


class _MultipartView(DjangoGraphQLView):
    """The package's sync view: both upstream parsers read its ``parse_json`` hook."""

    def __init__(self) -> None:
        super().__init__(schema=_EMPTY_SCHEMA)


class _AsyncMultipartView(AsyncDjangoGraphQLView):
    """The package's async view, read the same way."""

    def __init__(self) -> None:
        super().__init__(schema=_EMPTY_SCHEMA)


_MULTIPART_OPERATIONS = '{"query": "{ __typename }", "variables": {"upload": null}}'
_MULTIPART_LIST_OPERATIONS = '{"query": "{ __typename }", "variables": []}'


@pytest.mark.parametrize(
    ("operations", "files_map"),
    [
        pytest.param(_MULTIPART_OPERATIONS, "[{}]", id="array-instead-of-object"),
        pytest.param(_MULTIPART_OPERATIONS, '{"0": [1]}', id="non-string-path"),
        pytest.param(
            _MULTIPART_LIST_OPERATIONS,
            '{"0": ["variables.not-an-index"]}',
            id="non-numeric-list-index",
        ),
        pytest.param(
            _MULTIPART_LIST_OPERATIONS,
            '{"0": ["variables.0"]}',
            id="missing-list-index",
        ),
    ],
)
def test_patched_sync_parse_multipart_rejects_structurally_invalid_maps(
    operations: str,
    files_map: str,
) -> None:
    """Every malformed map that upstream leaks as a Python error becomes its 400."""
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_sync_parse_multipart(
            _MultipartView(),
            _sync_request(operations, files_map, {"0": "x"}),
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_MULTIPART_PARSE_REASON


async def test_patched_async_parse_multipart_rejects_structurally_invalid_maps() -> None:
    """The async parser has the same untrusted-map failure boundary as the sync one."""
    with pytest.raises(HTTPException) as excinfo:
        await patches._patched_async_parse_multipart(
            _AsyncMultipartView(),
            _async_request(_MULTIPART_OPERATIONS, "[{}]", {"0": "x"}),
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_MULTIPART_PARSE_REASON


class _UnformableRequest(AsyncDjangoHTTPRequestAdapter):
    """An adapter whose form-data read fails the way a broken multipart body does."""

    def __init__(self) -> None:
        super().__init__(_multipart_request("{}", "{}", {}))

    @override
    async def get_form_data(self) -> FormData:
        raise ValueError("malformed multipart body")


async def test_the_multipart_reason_is_upstreams_own_native_literal() -> None:
    """The delegates' 400 reason stays byte-identical to Strawberry's own.

    ``_UPSTREAM_MULTIPART_PARSE_REASON`` reproduces the one native multipart-400
    reason upstream raises - the async parser wraps a failing
    ``get_form_data()`` in exactly this ``HTTPException`` - so the structural
    failures the delegates translate are indistinguishable on the wire from
    upstream's own multipart rejections. The malformed-map rows above compare
    the wrapper's output to this very constant, so only a pin against the
    native raise - the JSON reason's ``tests/test_views.py`` precedent - catches
    an upstream rewording instead of letting the copy drift silently.
    """
    original_async_parse_multipart = patches._original_async_parse_multipart
    assert original_async_parse_multipart is not None
    with pytest.raises(HTTPException) as excinfo:
        await original_async_parse_multipart(_AsyncMultipartView(), _UnformableRequest())

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_MULTIPART_PARSE_REASON


def test_patched_sync_parse_multipart_preserves_a_non_structural_parser_exception() -> None:
    """The malformed-envelope wrapper cannot hide a consumer JSON hook failure."""

    class _ExplodingView(_MultipartView):
        @override
        def parse_json(self, data: str | bytes) -> object:
            raise RuntimeError("consumer decode hook failed")

    request = _sync_request(_MULTIPART_OPERATIONS, "{}", {})

    with pytest.raises(RuntimeError, match="consumer decode hook failed"):
        patches._patched_sync_parse_multipart(_ExplodingView(), request)


class _StructurallyBuggyView(_MultipartView):
    """A view whose JSON hook has a genuine server-side bug of a TRAVERSAL type."""

    @override
    def parse_json(self, data: str | bytes) -> object:
        raise TypeError("server-side bug before the upload traversal")


class _StructurallyBuggyAsyncView(_AsyncMultipartView):
    """The async twin of ``_StructurallyBuggyView``."""

    @override
    def parse_json(self, data: str | bytes) -> object:
        raise TypeError("server-side bug before the upload traversal")


def test_patched_sync_parse_multipart_does_not_downgrade_a_server_bug_to_400() -> None:
    """A traversal-typed failure raised OUTSIDE the upload utility keeps its 500 shape.

    The wrapper delegates the whole upstream parser, which also runs the request
    adapter's form handling and the view's own ``parse_json`` - work whose
    genuine bugs share the traversal's exception types. Translating one into the
    client-error ``400`` would hide a server fault, so the translation is scoped
    to failures whose traceback passes through the upload utility's frame.
    """
    request = _sync_request(_MULTIPART_OPERATIONS, "{}", {})

    with pytest.raises(TypeError, match="server-side bug before the upload traversal"):
        patches._patched_sync_parse_multipart(_StructurallyBuggyView(), request)


async def test_patched_async_parse_multipart_does_not_downgrade_a_server_bug_to_400() -> None:
    """The async twin scopes the translation to the upload utility identically."""
    request = _async_request(_MULTIPART_OPERATIONS, "{}", {})

    with pytest.raises(TypeError, match="server-side bug before the upload traversal"):
        await patches._patched_async_parse_multipart(_StructurallyBuggyAsyncView(), request)


def test_patched_sync_parse_multipart_preserves_valid_batched_operations() -> None:
    """The batch allowance belongs to ``operations`` and remains available to Strawberry."""
    operations = '[{"query": "{ __typename }", "variables": {"upload": null}}]'
    http_request = _multipart_request(operations, '{"0": ["0.variables.upload"]}', {"0": "upload"})

    parsed = patches._patched_sync_parse_multipart(
        _MultipartView(),
        DjangoHTTPRequestAdapter(http_request),
    )

    assert parsed == [
        {"query": "{ __typename }", "variables": {"upload": http_request.FILES["0"]}},
    ]


def test_patched_parse_query_params_skips_empty_string_param() -> None:
    """An empty-string param is left unparsed by upstream's own falsy skip."""
    result = patches._patched_parse_query_params(BaseView(), {"variables": ""})
    assert result["variables"] == ""


def test_patch_is_installed_false_when_base_view_symbol_missing() -> None:
    """``_patch_is_installed`` short-circuits to ``False`` when the symbol moved."""
    with mock.patch.object(patches, "BaseView", None):
        assert patches._patch_is_installed() is False


def test_apply_fails_loudly_when_symbols_missing() -> None:
    """A dependency-shape change cannot silently disable request hardening."""
    with (
        mock.patch.object(patches, "BaseView", None),
        pytest.raises(RuntimeError, match=r"BaseView\.parse_json"),
    ):
        patches.apply()


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("SyncBaseHTTPView", id="sync-multipart-view"),
        pytest.param("AsyncBaseHTTPView", id="async-multipart-view"),
    ],
)
def test_apply_fails_loudly_when_a_multipart_view_symbol_moves(name: str) -> None:
    """A moved multipart owner cannot turn the malformed-map fix into an AttributeError."""
    with (
        mock.patch.object(patches, name, None),
        pytest.raises(RuntimeError, match="parse_multipart"),
    ):
        patches.apply()


def test_apply_fails_loudly_when_the_upload_utility_moves() -> None:
    """A moved upload utility cannot silently widen the multipart translation.

    The multipart delegates scope their ``400`` by the utility's own frame, so a
    renamed or relocated ``replace_placeholders_with_files`` would leave them
    unable to tell a client-input traversal failure from a server bug. That is a
    dependency-shape change, and it fails at ``apply()`` like every other.
    """
    with (
        mock.patch.object(patches, "replace_placeholders_with_files", None),
        pytest.raises(RuntimeError, match="replace_placeholders_with_files"),
    ):
        patches.apply()


def test_apply_fails_loudly_when_the_upload_utility_is_not_a_plain_function() -> None:
    """The frame-scoped ``400`` reads the utility's code object, so callability is not enough.

    A release that wrapped the utility in a callable with no ``__code__`` (a
    ``functools.partial``, a C function) would otherwise pass capture and then
    raise ``AttributeError`` from inside the traversal handler, replacing the
    request's own error.
    """
    utility = patches.replace_placeholders_with_files
    assert utility is not None
    wrapped = functools.partial(utility)
    with (
        mock.patch.object(patches, "replace_placeholders_with_files", wrapped),
        pytest.raises(RuntimeError, match="replace_placeholders_with_files"),
    ):
        patches.apply()


def _self_only_method(_self: object) -> None:
    """A delegate whose signature lost every parameter but ``self``."""
    return


def test_apply_fails_loudly_when_parse_json_signature_changes() -> None:
    """The patch pins the method arity it delegates to."""
    with (
        mock.patch.object(patches, "_original_parse_json", _self_only_method),
        pytest.raises(RuntimeError, match=r"expected \(self, data\) signature"),
    ):
        patches.apply()


def test_apply_fails_loudly_when_parse_query_params_missing() -> None:
    """A missing ``parse_query_params`` cannot silently strand the guard unshielded."""
    with (
        mock.patch.object(patches, "_original_parse_query_params", None),
        pytest.raises(RuntimeError, match="parse_query_params"),
    ):
        patches.apply()


def test_apply_fails_loudly_when_parse_query_params_signature_changes() -> None:
    """The shield pins the delegated method's arity."""
    with (
        mock.patch.object(patches, "_original_parse_query_params", _self_only_method),
        pytest.raises(RuntimeError, match=r"expected \(self, params\) signature"),
    ):
        patches.apply()


@pytest.mark.parametrize(
    ("name", "method"),
    [
        pytest.param("_original_sync_parse_multipart", _self_only_method, id="sync-multipart"),
        pytest.param("_original_async_parse_multipart", _self_only_method, id="async-multipart"),
    ],
)
def test_apply_fails_loudly_when_parse_multipart_signature_changes(
    name: str,
    method: Callable[..., object],
) -> None:
    """Each delegating multipart wrapper pins the upstream call shape it invokes."""
    with (
        mock.patch.object(patches, name, method),
        pytest.raises(RuntimeError, match=r"expected \(self, request\) signature"),
    ):
        patches.apply()


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("relay_types", id="relay-module"),
        pytest.param("_original_should_resolve_list_connection_edges", id="check"),
    ],
)
def test_apply_fails_loudly_when_the_connection_page_check_moves(name: str) -> None:
    """A moved or renamed check cannot leave the rebind silently uninstalled."""
    with (
        mock.patch.object(patches, name, None),
        pytest.raises(RuntimeError, match="should_resolve_list_connection_edges"),
    ):
        patches.apply()


def _info_and_more(_info: object, _more: object) -> bool:
    """A check whose signature grew a second parameter."""
    return False


def test_apply_fails_loudly_when_the_connection_page_check_signature_changes() -> None:
    """The rebind delegates ``(info)``, so a reshaped upstream check refuses to install."""
    with (
        mock.patch.object(
            patches,
            "_original_should_resolve_list_connection_edges",
            _info_and_more,
        ),
        pytest.raises(RuntimeError, match=r"expected \(info\) signature"),
    ):
        patches.apply()


class _InlinedCheckConnection:
    """A ``ListConnection`` whose ``resolve_connection`` no longer calls the module global."""

    @classmethod
    def resolve_connection(cls) -> bool:
        return False


def test_apply_fails_loudly_when_resolve_connection_stops_calling_the_check() -> None:
    """A release that inlines the check would leave the rebind installed and inert."""
    inlined = truth.stored_function(
        truth.class_dict(_InlinedCheckConnection).get("resolve_connection"),
    )
    with (
        mock.patch.object(patches, "_original_relay_list_connection", inlined),
        pytest.raises(RuntimeError, match="no longer calls"),
    ):
        patches.apply()


def test_apply_no_ops_when_toggle_disabled(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``APPLY_UPSTREAM_PATCHES = False`` makes ``apply()`` decline to install."""
    monkeypatch.setattr(BaseView, "parse_json", patches._original_parse_json)
    assert patches._patch_is_installed() is False

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
    patches.apply()
    assert patches._patch_is_installed() is False
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": True}
    patches.apply()
    assert patches._patch_is_installed() is True


def test_apply_no_ops_when_strawberry_dependency_opted_out(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``{"strawberry": False}`` disables only this module; ``{"django": False}`` does not.

    The production half of the per-dependency opt-out contract: opting out of
    the test-only Django patch alone leaves this request hardening
    installing normally (each gate reads its own dependency name).
    """
    monkeypatch.setattr(BaseView, "parse_json", patches._original_parse_json)
    monkeypatch.setattr(BaseView, "parse_query_params", patches._original_parse_query_params)
    assert patches._patch_is_installed() is False

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}
    patches.apply()
    assert patches._patch_is_installed() is False

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
    patches.apply()
    assert patches._patch_is_installed() is True


def test_the_gated_workarounds_really_stop_hardening_when_opted_out(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The opt-out is behavioral, not just an install flag - and stays that way.

    The companion to ``tests/test_views.py``'s patch-opted-out rows, and the
    reason both are needed: the wire contract must survive the switch, and the
    upstream-bug workarounds must not. If a future change moved the envelope
    guard or the ``UnicodeDecodeError`` translation somewhere ungated to make an
    opt-out row easier, this row fails - which is the point, because those two are
    workarounds for defects in a specific upstream version and a consumer pinning
    a fixed or reshaped Strawberry has to be able to turn them off.

    With the pair un-installed, upstream's own ``parse_json`` is what runs: a
    JSON scalar body parses straight through (it is the caller downstream, not
    this method, that then raises ``AttributeError``), and an undecodable body
    raises the raw ``UnicodeDecodeError`` upstream never catches.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}
    monkeypatch.setattr(BaseView, "parse_json", patches._original_parse_json)
    monkeypatch.setattr(BaseView, "parse_query_params", patches._original_parse_query_params)
    patches.apply()
    assert patches._patch_is_installed() is False

    view: BaseView[object] = BaseView()
    assert view.parse_json("42") == 42
    assert view.parse_json("[1, 2, 3]") == [1, 2, 3]
    with pytest.raises(UnicodeDecodeError):
        view.parse_json(b'{"a":"\xff\xfe"}')


def test_capture_returns_none_when_upstream_owner_is_missing() -> None:
    """A missing upstream owner captures as ``None`` instead of failing at import.

    The four captures run at module scope, and the import guard above them sets
    every owner to ``None`` when Strawberry is absent or has moved the view
    classes. So the capture has to tolerate ``None``: raising here would make the
    patch module - and with it the whole package's app config - unimportable on
    exactly the installs ``apply()`` exists to refuse loudly and specifically.
    ``None`` is the shape ``_validate_upstream_shape`` reads as "no upstream to
    supersede".
    """
    assert patches._captured_upstream_method(None, "parse_json") is None


def test_patched_parse_json_translates_a_pathologically_nested_body(
    pathological_json_text: str,
) -> None:
    """A body nested past the parser's C stack -> controlled 400, not a raw escape.

    The second half of the decode-failure gap: ``json.loads`` answers a pathologically nested
    document with ``RecursionError`` - a ``RuntimeError``, so neither
    upstream's ``except json.JSONDecodeError`` nor a ``ValueError`` widening
    catches it, and it escaped as an unhandled ``500`` from every one of the
    nine call sites. The translation is the same ``HTTPException(400, ...)``
    upstream already gives unparseable JSON, indistinguishable but for
    ``__cause__``.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), pathological_json_text)

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_JSON_PARSE_REASON
    assert type(excinfo.value.__cause__) is RecursionError


@pytest.mark.parametrize("param", ["variables", "extensions"])
def test_patched_parse_query_params_translates_a_deep_param(
    param: str,
    pathological_json_text: str,
) -> None:
    """The GET shield keeps the decode-failure error channel, not the envelope guard.

    The shield turns the envelope guard off for the two query-param parses
    (upstream's per-param handling owns validity there), but a deep param
    still drives ``json.loads`` past the C stack - client input that must
    meet the same controlled ``400`` as malformed JSON, not an unhandled
    ``RecursionError`` -> ``500`` on a bodyless GET.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_query_params(
            BaseView(),
            {"query": "{ __typename }", param: pathological_json_text},
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_JSON_PARSE_REASON
    assert type(excinfo.value.__cause__) is RecursionError


def test_patched_sync_parse_multipart_translates_a_deep_operations_document(
    deepcopy_overflow_operations_text: str,
) -> None:
    """The upload utility's ``copy.deepcopy`` recursion becomes its own 400.

    A valid-JSON ``operations`` document whose value nesting exceeds Python's
    recursion limit parses cleanly (so the envelope guard passes it) and then
    overflows the utility's unconditional ``copy.deepcopy`` - inside the very
    frame the provenance check scopes by, hence a client-input translation to
    the multipart-parse ``400``, not a server-bug ``500``.
    """
    request = _sync_request(deepcopy_overflow_operations_text, "{}", {})

    with pytest.raises(HTTPException) as excinfo:
        patches._patched_sync_parse_multipart(_MultipartView(), request)

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_MULTIPART_PARSE_REASON


async def test_patched_async_parse_multipart_translates_a_deep_operations_document(
    deepcopy_overflow_operations_text: str,
) -> None:
    """The async delegate scopes the deepcopy recursion identically."""
    request = _async_request(deepcopy_overflow_operations_text, "{}", {})

    with pytest.raises(HTTPException) as excinfo:
        await patches._patched_async_parse_multipart(_AsyncMultipartView(), request)

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_MULTIPART_PARSE_REASON


def _relay_resolver_function() -> object:
    """The classmethod's stored function, without invoking its descriptor."""
    return truth.stored_function(
        truth.class_dict(relay_types.ListConnection).get("resolve_connection"),
    )


def test_relay_patch_occupies_the_types_global_and_the_list_resolver() -> None:
    """The ``strawberry.relay.types`` check and the list resolver are replaced; utils is not."""
    patches.apply()
    assert (
        read_attr(relay_types, "should_resolve_list_connection_edges")
        is patches._patched_should_resolve_list_connection_edges
    )
    assert (
        relay_utils.should_resolve_list_connection_edges
        is patches._original_should_resolve_list_connection_edges
    )
    assert _relay_resolver_function() is patches._patched_list_connection_resolve_connection
    assert patches._patch_is_installed()


def test_relay_apply_repairs_a_reverted_list_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reverting the adapted resolver alone makes the next apply reinstall it."""
    patches.apply()
    original_resolver = patches._original_relay_list_connection
    assert callable(original_resolver)
    monkeypatch.setattr(
        relay_types.ListConnection,
        "resolve_connection",
        classmethod(original_resolver),
    )
    assert not patches._relay_patch_is_installed()
    assert not patches._patch_is_installed()
    patches.apply()
    assert patches._relay_patch_is_installed()
    assert patches._patch_is_installed()


def test_relay_repeated_apply_keeps_the_same_replacements() -> None:
    """Repeated app-ready calls do not layer wrappers or change the installed functions."""
    patches.apply()
    first = (
        read_attr(relay_types, "should_resolve_list_connection_edges"),
        _relay_resolver_function(),
    )
    patches.apply()
    assert (
        read_attr(relay_types, "should_resolve_list_connection_edges"),
        _relay_resolver_function(),
    ) == first


def test_relay_reload_recovers_genuine_upstream_originals() -> None:
    """A reload unwraps this module's old replacements instead of pinning its own source as upstream."""
    originals = (
        patches._original_should_resolve_list_connection_edges,
        patches._original_relay_list_connection,
        patches._original_parse_json,
    )
    importlib.reload(patches)
    patches.apply()
    assert (
        patches._original_should_resolve_list_connection_edges,
        patches._original_relay_list_connection,
        patches._original_parse_json,
    ) == originals
    assert patches._patch_is_installed()


def test_relay_apply_refuses_a_missing_list_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A moved ``ListConnection.resolve_connection`` fails the Relay validation by name."""
    monkeypatch.setattr(patches, "_original_relay_list_connection", None)
    with pytest.raises(
        RuntimeError,
        match=r"expected ListConnection\.resolve_connection",
    ) as excinfo:
        patches.apply()
    assert 'APPLY_UPSTREAM_PATCHES = {"strawberry": False}' in str(excinfo.value)
    assert "Relay opt-out consequences" in str(excinfo.value)


def _drifted_resolve_connection(_cls: object, info: strawberry.Info[object, object]) -> bool:
    """A resolver that still asks the connection-page check but lost its pagination keywords."""
    return relay_utils.should_resolve_list_connection_edges(info)


def test_relay_apply_refuses_upstream_signature_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    """A changed call shape cannot pass merely because the resolver still asks the check."""
    monkeypatch.setattr(patches, "_original_relay_list_connection", _drifted_resolve_connection)
    with pytest.raises(
        RuntimeError,
        match="upstream pagination signature changed",
    ) as excinfo:
        patches.apply()
    assert 'APPLY_UPSTREAM_PATCHES = {"strawberry": False}' in str(excinfo.value)
    assert "Relay opt-out consequences" in str(excinfo.value)


@pytest.mark.parametrize("source_state", ["changed", "unreadable"])
def test_relay_apply_refuses_changed_or_unreadable_adapted_source(
    monkeypatch: pytest.MonkeyPatch,
    source_state: str,
) -> None:
    """The adapted body is pinned; unavailable source is not permission to supersede unknown code."""
    target = patches._original_relay_list_connection
    original_getsource = inspect.getsource

    def source(value: object) -> str:
        assert isinstance(value, FunctionType)
        if value is target:
            if source_state == "unreadable":
                raise OSError("dependency source unavailable")
            return original_getsource(value) + "\n# upstream algorithm changed\n"
        return original_getsource(value)

    monkeypatch.setattr(inspect, "getsource", source)
    with pytest.raises(RuntimeError, match="resolve_connection no longer matches") as excinfo:
        patches.apply()
    assert 'APPLY_UPSTREAM_PATCHES = {"strawberry": False}' in str(excinfo.value)
    assert "Relay opt-out consequences" in str(excinfo.value)


@pytest.mark.parametrize(
    "toggle",
    [False, {"strawberry": False}],
    ids=["global-off", "dependency-off"],
)
def test_relay_patch_respects_the_existing_upstream_opt_out(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
    toggle: object,
) -> None:
    """Opting out leaves the native connection-page check and the native resolver unchanged."""
    monkeypatch.setattr(
        relay_types,
        "should_resolve_list_connection_edges",
        patches._original_should_resolve_list_connection_edges,
    )
    original_resolver = patches._original_relay_list_connection
    assert callable(original_resolver)
    monkeypatch.setattr(
        relay_types.ListConnection,
        "resolve_connection",
        classmethod(original_resolver),
    )
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": toggle}
    patches.apply()
    assert (
        read_attr(relay_types, "should_resolve_list_connection_edges")
        is patches._original_should_resolve_list_connection_edges
    )
    assert _relay_resolver_function() is patches._original_relay_list_connection
    assert not patches._relay_patch_is_installed()
