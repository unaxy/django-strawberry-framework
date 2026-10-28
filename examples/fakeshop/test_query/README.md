# Writing tests

The manual for writing tests in this repository: where a test goes, what it must prove, how a shortcut test becomes a real one, and what the fakeshop live tier owes every package line it can reach.

For agents. Binding. [AGENTS.md][agents] = law, one line each; this = long form w/ examples. [START.md][start] = cross-release hazards. [docs/TREE.md][tree-tests] = per-file layout. [CONTRIBUTING.md][contributing] = human mechanics. [Fakeshop tutorial][fakeshop-readme] = what the fixture demonstrates. This file vs a module docstring disagree → docstring describes one file, this describes the rule; fix the wrong one, same change.

## Contents

1. [The rule](#the-rule)
2. [Where a test goes](#where-a-test-goes)
3. [Anatomy of a live test](#anatomy-of-a-live-test)
4. [Promoting a shortcut test](#promoting-a-shortcut-test)
5. [Breaking a test up](#breaking-a-test-up)
6. [Shipped schema can't reach the subject](#shipped-schema-cant-reach-the-subject)
7. [Worked examples](#worked-examples)
8. [What legitimately stays package-side](#what-legitimately-stays-package-side)
9. [Isolation contract](#isolation-contract)
10. [Clients, transports, credentials](#clients-transports-credentials)
11. [Environment tiers](#environment-tiers)
12. [Prove the test can fail](#prove-the-test-can-fail)
13. [Test code style](#test-code-style)
14. [Checklist](#checklist)
15. [Suite map](#suite-map)

## The rule

**Real test > targeted test, even when slower to write and run.** Real = GraphQL doc over HTTP to fakeshop `/graphql/`, against the schema fakeshop composes, rows in DB, user on request. Targeted = throwaway type, private helper call, one branch via `SimpleNamespace`. Both turn a line green; only the first proves what a consumer sees.

Preference order, fixed:

1. Live request, fakeshop's shipped schema.
2. Live request, fakeshop surface added for the purpose. "Fixture can't reach it" = fixture gap, not unreachability → extend fixture.
3. Live request, test-local holder schema mounted beside fakeshop. Still HTTP.
4. In-process `schema.execute_sync` on the composed project schema.
5. Package tier, throwaway types.
6. Mock, only when real path impossible. Mock behaviour, never the class.

Speed never justifies skipping a rung. `pytest.ini` parallel default = the speed budget; a live row's extra ms is the price.

Two corollaries, enforced:

- **Live-first, both verdicts, and the must-not.** Any `django_strawberry_framework/` line a real fakeshop query reaches MUST be covered from this dir. Acceptance ≠ rejection: a plan can pin rejection live and leave acceptance package-only; rejection row covers nothing about acceptance. Check which VERDICT each live row proves. Claim = a behaviour is SCOPED (write-only exemption, an ordering, a one-surface opt-in) → row also owes the adjacent case that must NOT get it; positive alone proves the mechanism, not the boundary ([the `isPrivate` refetch](#the-must-not-only-a-real-session-can-phrase-isprivate-refetch)).
- **Promotion deletes the stand-in.** Package copy goes in the same change, after the live row is shown to fail w/ boundary removed ([Prove the test can fail](#prove-the-test-can-fail)). Two tests, one claim = debt, not safety.

Coverage = package only, `fail_under = 100`; live tests here are how it gets there. Example apps run every suite, never count. Don't add them to the gate.

## Where a test goes

Four trees, one `pytest.ini`. Locally, run targeted selections only; the full suite runs in GitHub Actions.

| Tree | SUT | Style | Package? |
|---|---|---|---|
| `examples/fakeshop/test_query/` | any package line a real query reaches | live `/graphql/` HTTP via [`graphql_client.py`][graphql-client] | no |
| `examples/fakeshop/apps/<app>/tests/` | one app's models/admin/services/commands | in-process: model methods, admin, services, `call_command`. NOT `execute_sync` on the composed schema; a query that reaches the claim → `test_query/` ([composition introspection](#wrong-tree-over-the-real-schema-composition-introspection)) | yes, `apps.<app>.tests` |
| `examples/fakeshop/tests/` | project/config only: urls, settings guard, schema export, project commands | in-process `Client`, `call_command` | no, never add `__init__.py` |
| `tests/` | package + repo tooling | in-process; throwaway `DjangoType`s; fakeshop models OK as fixtures | mirrors package layout |

Ask in order:

1. Real GraphQL doc against fakeshop can observe the claim? → here, in the suite owning the app/surface ([suite map](#suite-map)). No shipped field reaches it? Read [Shipped schema can't reach the subject](#shipped-schema-cant-reach-the-subject) BEFORE saying no.
2. Subject = one fakeshop app's own code (model method, admin action, service, command)? → `apps/<app>/tests/`. Each app owns its coverage; delete app = lose only its tests.
3. Subject = fakeshop as project (routing, `DEBUG` guard, schema export)? → `examples/fakeshop/tests/`.
4. Subject = package internal no request observes (registry lifecycle, construction-time validation, pure-function precedence, absence proof, repo tooling)? → `tests/`, file mirroring the module. `tests/base/` = exactly `test_init.py` + `test_conf.py`, may grow, no new files.

Landed in 2–4 while a real query could reach it = misplaced. Fix = move, not a live twin beside it.

## Anatomy of a live test

Seed → pick viewer → post doc → assert payload exactly → if claim is cost/shape, assert SQL.

```python
"""Live GraphQL HTTP tests for the library visibility hook: hidden rows never leave the row fetch."""

import pytest
from apps.library import models
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from graphql_client import assert_graphql_data, assert_graphql_success


def _seed_shelf_with_repair_book():
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="Fiction", branch=branch)
    models.Book.objects.create(title="Kindred", shelf=shelf)
    models.Book.objects.create(
        title="Dune",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.REPAIR,
    )


@pytest.mark.django_db
def test_anonymous_book_list_excludes_repair_rows_in_the_row_query():
    """``BookType.get_queryset`` drops ``repair`` rows for an anonymous viewer inside the one book query."""
    _seed_shelf_with_repair_book()

    with CaptureQueriesContext(connection) as captured:
        assert_graphql_data(
            "{ allLibraryBooks { title } }",
            {"allLibraryBooks": [{"title": "Kindred"}]},
        )

    book_queries = [q["sql"] for q in captured.captured_queries if "library_book" in q["sql"]]
    assert len(book_queries) == 1
    assert "repair" in book_queries[0]


@pytest.mark.django_db
def test_staff_book_list_keeps_repair_rows():
    """The same field returns every row once the viewer is staff."""
    create_users(1)
    _seed_shelf_with_repair_book()
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    data = assert_graphql_success("{ allLibraryBooks { title } }", client=client)

    assert sorted(book["title"] for book in data["allLibraryBooks"]) == ["Dune", "Kindred"]
```

- **Module docstring**: FIRST LINE = one period-terminated sentence naming the subject; later paragraphs free (`build_tree_md.py::assert_single_sentence` checks the extracted first line only). [TREE.md][tree-tests] renders that line; renderer fails on missing / multi-sentence first line; changing it → re-render, same change.
- **Capture helper per suite.** Every SQL-shape suite spells its own post-and-capture pair (`_capture` / `_capture_as_staff` in [`test_single_parent_fastpath_api.py`][test-single-parent-fastpath-api], `_library_sql` in [`test_library_api.py`][test-library-api]); [`graphql_client.py`][graphql-client] deliberately has none, only `statement_shapes` / `statement_shapes_after_last_delete` to read captured SQL as verbs and written tables, and `select_tables_after_last_delete` for the tables a write read after a stand-in concurrent delete. Read the target file's helpers before writing a capture.
- **Concurrent delete.** The [`conftest.py`][conftest] `delete_after_authorization` fixture arms a fakeshop mutation class (read off its schema module at test time) so its `check_permission` deletes the located row after the real authorization: the stand-in for a delete committed between the locate and the write, simulated on the request's own connection.
- **Async statement counts.** `CaptureQueriesContext` watches one connection object and an async request runs its ORM work on a `sync_to_async` executor thread holding another, so async rows count statements with the [`conftest.py`][conftest] `record_compiled_sql` fixture: each call returns a list of the plain SELECT compiler's statements from then on (only those naming its `table` argument when one is given), recorded where they are built, in any thread.
- **Seeding** per app. Products/auth: `seed_data(N)` / `create_users(N)` from [`apps/products/services.py`][products-services] first line; never hand-roll Category/Item/Property/Entry/User. Library: inline `Model.objects.create` (no services module). Seed the full non-null chain (Branch → Shelf → Book).
- **Viewer** = `django.test.Client`. Anonymous default. `force_login` a seeded user: `create_users` gives `staff_N` (`is_staff`), `regular_N`, `view_<model>_N` per products model, all `TEST_USER_PASSWORD`. Model-perm check → grant codename to a NON-superuser in-test; superuser short-circuits, proves nothing.
- **Request** via [`graphql_client.py`][graphql-client]. `assert_graphql_data` = 200 + no `errors` + exact `data`. `assert_graphql_success` → `data`. `graphql_payload` → whole envelope (rows about `errors`). `post_graphql` → raw `HttpResponse` (headers, status). JSON path routes through package [`TestClient`][glossary-testclient], so live rows exercise the consumer client too.
- **Payload** exact wherever data allows. Faker-seeded products → derive expected from the equivalent ORM query, never pin names.
- **SQL** = the instrument for optimizer / visibility / pagination claims. Filter `captured_queries` to the table under test, on `FROM "<table>"` when the selection touches a relation (M2M through-tables share the parent's prefix: `"library_book" in sql` also matches `library_book_genres`), assert count, then fragment (`LIMIT 2 OFFSET 1`, `EXISTS`, no `COUNT(`, no `DISTINCT`). Never assert bare total count; session / auth / content-type queries ride along the moment a viewer logs in. Plan-object attributes each translate to exactly one SQL fact (`select_related` → `JOIN`, `Prefetch` → second query on the target table, `only_fields` attname → column in root `SELECT`); an attribute w/ no translation was never a contract ([the hint pair](#sql-beats-the-plan-object-the-hint-pair)).
- **Identifiers minted, never pinned.** GlobalIDs via [`global_id_for`][testing-relay] over the real type; cursors from a prior `endCursor`. Package-owned encodings, may change.

## Promoting a shortcut test

A shortcut row, condensed from the throwaway-type idiom in [`tests/test_connection.py`][tests-connection]. Claim: "connection w/o `total_count` opt-in exposes no `totalCount`":

```python
def _make_node_type(name, *, total_count):
    meta = {"model": Genre, "fields": ("id", "name"), "interfaces": (relay.Node,)}
    if total_count is not None:
        meta["connection"] = {"total_count": total_count}
    return type(name, (DjangoType,), {"Meta": type("Meta", (), meta)})


def test_total_count_absent_unless_opted_in():
    node_type = _make_node_type("BareGenre", total_count=None)

    @strawberry.type
    class Query:
        genres: DjangoConnection[node_type] = DjangoConnectionField(node_type)

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config())

    result = schema.execute_sync("{ genres(first: 2) { edges { node { name } } } }")

    assert result.errors is None
    assert "totalCount" not in str(schema)
```

Passes. Proves ~nothing a consumer cares about: type not shipped, schema not fakeshop's, no view, no visibility hook, "not in SDL string" says nothing about whether a `COUNT` ran.

The same claim as a live row, condensed from [`test_library_api.py`][test-library-api]`::test_genre_connection_total_count_omitted_no_count` (read the row for its exact assertions):

```python
@pytest.mark.django_db
def test_genre_connection_total_count_omitted_no_count():
    """Omitting ``totalCount`` returns a correct count-less response and issues no count query."""
    _seed_genres("Alpha", "Beta", "Gamma")

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConnection(first: 2) {
                edges { node { id name } }
                pageInfo { hasNextPage }
              }
            }
            """,
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenresConnection"]
    names = [edge["node"]["name"] for edge in conn["edges"]]
    assert names == ["Alpha", "Beta"]
    assert "totalCount" not in conn
    assert not any("COUNT(" in query["sql"].upper() for query in captured.captured_queries)
```

What the live row proves that the shortcut can't:

1. **Type = shipped `GenreType`** ([`apps/library/schema.py`][lib-schema], `connection = {"total_count": True}`). Proves selection gating on a type that opted in = the consumer contract; a throwaway proves a weaker SDL fact about a type nobody ships.
2. **Schema = composed project schema**, reloaded by [`conftest.py`][conftest] autouse fixtures. Every app registered → a relation target that raises at finalize in prod raises here.
3. **Request crosses the view.** Middleware, optimizer extension, user on request. A resolver reading `info.context.request` is exercised, not skipped.
4. **Assertion = wire + DB**, not a schema string. `"totalCount" not in conn` = what client sees; no `COUNT(` = what DB saw.
5. **Rows real.** Three genres, page of two, actionable `hasNextPage`.

The package tier keeps what has no wire shape: `tests/test_connection.py::test_connection_type_for_returns_concrete_subclass_without_opt_in` pins that the generated connection is a concrete subclass, not the `DjangoConnection[T]` alias. Construction-time identity. Its docstring names this dir as home of the consumer round-trips. Package file says what it does NOT carry; live file says nothing about the package tier (consumer never sees it).

Promote → delete shortcut same change, then sweep what the shortcut alone kept alive: helpers, module constants, builder kwargs whose only caller was the deleted row (ruff sees unused imports, not an orphaned `def`; grep each name, count `1` = definition-only), the module docstring's bullets, and prose citations: `grep -rn -F '<name>' docs/ KANBAN.md` (bare name, not `::name`; prose rarely qualifies) plus `strings examples/fakeshop/db.sqlite3 | grep -F '<name>'` for a board row the next render would surface (a hit there may be freelist residue; confirm through the kanban app). The citation gate reads `.py`, `KANBAN.md` and the specs; other `docs/` prose is ungated. Run the live row w/ boundary removed first ([`prove_failability.py`][prove-failability]). Live row doesn't fail → one of two things, opposite fixes: the row isn't covering the claim yet (add assertions), OR the docstring you inherited names a boundary neither row pins (find the real one, rewrite the claim). Check the second first; a promoted docstring carries its author's belief, not a measurement ([corrupt image](#a-stand-ins-docstring-can-name-the-wrong-boundary-corrupt-image)). Also: a green run can mean the MUTATION was absorbed (unreachable guard, a root the optimizer never plans, fail-open `fields=[]`); the script's `WEAKLY PINNED` verdict points at the test, check the mutation first.

## Breaking a test up

Shortcut tests carry several claims under one name. Split along claims BEFORE moving.

One claim per row. `test_title_filters` looping three lookups = one node id: failure in #2 hides #3; failability counts the loop as ONE row however many boundaries it crosses.

Looped:

```python
@pytest.mark.django_db
def test_title_filters():
    _seed_books("Kindred", "Dune")
    for lookup, value, expected in [
        ("exact", '"Kindred"', ["Kindred"]),
        ("iContains", '"kin"', ["Kindred"]),
        ("in", '["Kindred", "Dune"]', ["Dune", "Kindred"]),
    ]:
        data = assert_graphql_success(
            "{ allLibraryBooks(filter: { title: { %s: %s } }, orderBy: [{ title: ASC }]) { title } }"
            % (lookup, value),
        )
        assert [b["title"] for b in data["allLibraryBooks"]] == expected
```

Split, one node id per claim:

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("lookup", "value", "expected"),
    [
        ("exact", '"Kindred"', ["Kindred"]),
        ("iContains", '"kin"', ["Kindred"]),
        ("in", '["Kindred", "Dune"]', ["Dune", "Kindred"]),
    ],
    ids=["exact", "icontains", "in"],
)
def test_book_title_lookup_returns_only_matching_rows(lookup, value, expected):
    """Each declared ``title`` lookup on ``BookFilter`` narrows ``allLibraryBooks`` to the matching rows."""
    _seed_books("Kindred", "Dune", "Neuromancer")
    query = (
        "{ allLibraryBooks(filter: { title: { %s: %s } }, orderBy: [{ title: ASC }]) { title } }"
        % (lookup, value)
    )

    data = assert_graphql_success(query)

    assert [b["title"] for b in data["allLibraryBooks"]] == expected
```

Rules applied:

- **Parametrize, don't loop.** Each case = own node id, readable `ids=`.
- **Seed a row that must NOT match.** `Neuromancer` → unfiltered result can't pass by accident. Assert the list, not `len == 2`; cardinality is satisfiable by wrong rows.
- **Split acceptance from rejection.** Declared lookup vs undeclared = two rows, two tests; rejection asserts the exact envelope error, never just "errors present".
- **Name = invariant**, not card / slice / bug number. Docstring may cite spec decision or glossary anchor; never how the test came to exist.
- **Explicit ordering.** Any list-order assertion carries `orderBy:`; no insertion-order flake.

Claims span two tiers → split by tier: consumer-visible live, construction-time package-side w/ docstring naming the live sibling.

## Shipped schema can't reach the subject

"No fakeshop field exposes this" = the most common misplacement. Three tools, in order, keep it live.

**1. Extend the fixture.** Fakeshop exists to be extended. `allLibraryBranchesViaListField` in [`apps/library/schema.py`][lib-schema] exists for ONE reason: give `DjangoListField` a live surface beside the connections. Feature w/o consumer surface in fakeshop → add one, in the app whose model fits, declared as a consumer would, field docstring naming it the acceptance surface.

**2. Settings flag read in the class body.** Permanent exposure would change fakeshop's public contract → gate it. `LoanType` reads `FAKESHOP_TEST_LOAN_CONNECTION` inside `Meta`, adds `relay.Node` + `connection = {"total_count": True}` under the flag only; `Query` reads the same flag for `allLibraryLoansConnection`. Test: `override_settings(FAKESHOP_TEST_LOAN_CONNECTION=True)` → `project_schema_override` fixture rebuilds → drive real `/graphql/` → autouse guard restores default on exit. Companion row asserts the field ABSENT by default; flag never leaks into shipped shape.

**3. Holder schema beside fakeshop.** Subject = consumer-declared class no fakeshop app would plausibly ship (hostile `OrderSet` override, counting converter, second view mount w/ different body cap) → build schema in the test module, mount on own URL:

```python
_CURRENT: dict[str, Any] = {"schema": None}


def _graphql_view(request: HttpRequest):
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _graphql_view)]


def _post(
    schema: DjangoSchema,
    query: str,
    *,
    client: Client | None = None,
    variables: Mapping[str, object] | None = None,
):
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return post_graphql(query, client=client, variables=variables, url="/graphql-test/")
    finally:
        _CURRENT["schema"] = None
```

Request still crosses the full HTTP pipeline. `override_settings(ROOT_URLCONF=...)` / `pytest.mark.urls` already clear resolver caches (Django's `setting_changed` receiver, both directions); call `clear_url_caches()` yourself only when the holder swaps its held schema WITHOUT changing `ROOT_URLCONF`. The reference impls below still call it inside their `override_settings` brackets; redundant, harmless, don't copy it into new mounts. What every holder mount DOES owe: resolve the schema at request time (`from config.schema import schema` INSIDE the view function, or the `_CURRENT` dict above). A schema captured at import is the pre-reload one and fails in a LATER module on the same worker, not yours. Holder types declared inside test body / fixture depending on the module reload, never at import; registry clear between modules would strand them (the autouse guard raises "Reloading the project schema shell mutated app registrations", naming the fixture, not your file). Mount path is the module's choice (`/graphql-test/`, `/graphql/` in own URLconf, `cap-misconfigured/`); function-level `@pytest.mark.urls("config.urls")` reaches the shipped endpoint from inside a holder module. Async mounts spelled longhand must carry `@_carrying_the_packages_csrf_mark(AsyncDjangoGraphQLView)` themselves. Reference impls: [`test_list_field_api.py`][test-list-field-api], [`test_products_visibility_api.py`][test-products-visibility-api], [`test_transport_api.py`][test-transport-api].

All three exhausted → `tests/`, and the docstring names the rung BY NUMBER, states the specific fakeshop change that would reach it, and why that change is unacceptable. "No shipped type declares this" disposes of rungs 1–2 and says nothing about rung 3; a package row resting on that sentence alone may be promotable through a holder mount.

## Worked examples

Real live rows, one lesson each, widest range first. Each names the live row that pins it; read the row for its exact assertions. Where the failability boundary is not obvious, the example names the mutation that fails the row.

### Wiring vs class: the plan cache

A package row w/ its own extension instance proves the CLASS caches. Fakeshop's `extensions=[lambda: _optimizer]` wiring in `config/schema.py` exists so the cache survives across REQUESTS; only a live row over two requests proves that: [`test_library_api.py`][test-library-api]`::test_library_optimizer_plan_cache_is_reused_across_http_requests`.

- **Read the served instance at call time.** The extension under test is the one `config.urls` serves, reached via `sys.modules["config.schema"]._optimizer` inside the test (the conftest rebuilds that module whenever a test leaves the registry stale; a module-level import can bind a discarded instance and read zeros forever, passing). Absolute `misses == 1` holds only because the conftest empties the plan cache before every test; the row's comment says so.
- **Hooks make a plan uncacheable.** A plan w/ any `get_queryset` hook in the selection is `cacheable=False`: `allLibraryBooks { shelf { code } }` measures `misses=2, size=0` because `BookType` / `ShelfType` declare `get_queryset`. Cache rows need hook-free types (`allLibraryMembershipCards`). Throwaway types have no hooks, so a package row never meets this.
- **SQL identity.** The second request's library SQL must equal the first's: a stale reused plan would change the emitted SQL.
- **Don't build the row on a plain `strawberry.Schema`.** It gives `lambda: ext` no per-operation isolation, so every operation shares one extension instance's per-operation state and execution context; `config/schema.py`'s `DjangoSchema` isolates both on the shared instance, which is what makes the singleton factory safe.

Failability: `extensions=[lambda: _optimizer]` → fresh instance per request → row fails.

### SQL beats the plan object: the hint pair

`LoanType.Meta.optimizer_hints = {"book": OptimizerHint.prefetch_related(), "patron": OptimizerHint(skip=True)}` ships in [`apps/library/schema.py`][lib-schema]. [`test_library_api.py`][test-library-api]`::test_library_optimizer_hints_are_observable_over_http` reads both hints from the SQL alone, never from `ctx.dst_optimizer_plan`:

- **Prefetch half.** `allLibraryLoans { book { title } }`: root query on `library_loan` w/o `JOIN`, `book_id` kept in its `SELECT` (the forced prefetch needs the FK column), then ONE batched query on `library_book`.
- **SKIP half.** `library_patron` absent from the root SQL AND one patron query per row: lazy load, not a batched prefetch. That is the live spelling of "not planned".

Every plan attribute translates to the SQL fact it implies:

| Plan attribute | Wire / SQL fact |
|---|---|
| `select_related` contains X | `JOIN` on X's table in the root query |
| `prefetch_related` contains X | second query against X's table, none in root |
| `only_fields` contains attname | that column in root `SELECT` |
| `cacheable is False` | `cache_info().misses == 2` over two identical requests |
| hint `SKIP` on X | no X table anywhere planned; one lazy query per row on access, X's link column kept in the root `SELECT` |

An attribute w/ no translation was never a contract; drop it, don't promote it.

Failability: delete the `optimizer_hints` line on `LoanType` → row fails. Deleting the walker's elision guard for a hooked target changes NOTHING: `django_strawberry_framework/optimizer/walker.py::plan_relation` downgrades to `Prefetch` first, so that guard is unreachable on this path. A row whose only failing mutation is that guard pins a dead guard.

### Optimizer-less is a configuration: one query per parent

Under the shipped optimizer a nested connection's query count is independent of N ([`test_library_api.py`][test-library-api]`::test_nested_books_connection_fixed_query_count`). An optimizer-less consumer is a real configuration in which the same nested connection costs one window query per parent. Both claims hold, each of its own configuration; a `1 + N` row on a bare `strawberry.Schema` that never names the missing extension reads as contradicting the fixed-count row. The optimizer-less claim lives on a holder mount WITHOUT the extension: [`test_products_visibility_api.py`][test-products-visibility-api]`::test_nested_connection_costs_one_query_per_parent_without_the_optimizer`.

- Shipped `CategoryType`, imported inside the helper (after the reload), real HTTP through the file's holder mount.
- Two cardinalities, so `N` is load-bearing: a fixed count can't satisfy both, and per-EDGE loading would overshoot N.
- SQL filtered to `products_item`, so session reads don't count.
- `seed_data(1)` seeds more categories than either cardinality; the helper slices exactly N parents by pk.

Failability: installing the optimizer on the holder changes nothing while the root returns a `list`, which the optimizer cannot plan; the mutation has to return a queryset too. Read a green run as "mutation absorbed" before "row weak".

### The must-not only a real session can phrase: `isPrivate` refetch

Shipped `ItemType.get_queryset` hides `is_private` rows from a non-staff viewer. A throwaway schema w/ a fabricated hook and an allow-all permission has no caller who can then read, so the must-not cannot be phrased. [`test_products_api.py`][test-products-api]`::test_create_item_private_row_is_refetched_for_its_author_but_stays_hidden_from_reads`: a non-staff caller granted `add_item` writes `isPrivate: true` and gets the row back in the payload `node` (the post-write re-fetch is by pk WITHOUT the visibility filter); the same caller's `allItems` read in the same session does NOT list it. The second half turns "re-fetch skips the filter" from a mechanism note into a security claim: the exemption is scoped to the actor's own write, never a hole in the read-side rule. `allItems` is a connection (`edges { node }`); `{ allItems { name } }` does not parse.

### Settings override reaches a misconfigured deployment: sessionless `login`

A sessionless refusal on fakeshop's `AllowAny` `login` is consumer-reachable, so the "one declaration per process" exemption (which covers only permission-gated variants) does not apply. Rung 2 via settings, real `/graphql/`: [`test_auth_api.py`][test-auth-api]`::test_sessionless_login_refuses_with_the_error_naming_both_middleware_stacks` and its logout twin `test_sessionless_logout_refuses_with_the_error_naming_both_middleware_stacks`.

- THREE middlewares dropped, not one: `AuthenticationMiddleware` and `MessageMiddleware` each `assert hasattr(request, "session")` and die inside Django before the view. Works because `require_session` runs before `authorize_or_raise`, so the missing `request.user` never matters.
- `Client()` constructed INSIDE the override: `ClientHandler` caches its middleware chain on first request.
- Pass-through needed to read the message.

Same file: `test_non_string_login_username_fails_validation_before_the_resolver` (`login(username: 123, ...)` rejected at validation, `{ me { username } }` still null on that client); `test_backend_raising_permission_denied_returns_the_same_envelope` (backend `PermissionDenied` envelope byte-identical to wrong-password), driven by the module-level `PermissionDeniedBackend` named via `AUTHENTICATION_BACKENDS=["test_auth_api.PermissionDeniedBackend", ...]`. `test_query/` is on `pythonpath`, so a live module's class is a valid settings string. Capture the CONTROL envelope (wrong password) before entering the backend override, else the comparison is vacuous.

### A synthetic model buys nothing: storage degradation

Shipped `MediaSpecimenWithPathType` declares the `filesystem_path_fields` opt-in a consumer would, so storage-degradation rows need no synthetic model, DDL bracket or `transaction=True`: [`test_uploads_api.py`][test-uploads-api]`::test_storage_without_absolute_paths_nulls_only_the_path_subfield_over_http`.

- ONE request selecting `name` / `path` / `url` together is stronger than one request per subfield: a guard sitting on the parent is then directly observable (`attachment: null` instead of a null `path`).
- Seed BEFORE monkeypatching storage (`_save` calls `self.path`).

Same shape: `test_vanished_file_resolves_size_to_null_over_http` (`Path(specimen.attachment.path).unlink()` → `size` null), `test_suspicious_file_operation_is_reported_not_nulled_over_http` (pass-through to see it), `test_empty_image_beside_populated_file_resolves_only_the_image_to_null_over_http` (the mixed row).

### A stand-in's docstring can name the wrong boundary: corrupt image

Django's `get_image_dimensions` returns `(None, None)` for unparseable bytes w/o raising, so `django_strawberry_framework/types/converters.py::_safe_file_attr` never fires for a corrupt image. The real boundary = the nullability `DjangoImageType` declares on `width` / `height`. A row whose docstring names `_safe_file_attr` survives removal of that guard; failability is what exposes it. Live rows: [`test_uploads_api.py`][test-uploads-api]`::test_corrupt_image_resolves_width_and_height_to_null_over_http`, plus `test_file_output_objects_publish_nullable_subfields_over_http` pinning the whole field-type map by introspection. Rule: verify a stand-in's claim against the code BEFORE copying it into the live row. Read which rows did NOT fail under each mutation; the silence is the finding.

### The error policy masks validation errors too: `BigInt` literals

Shipped `ScalarSpecimen.signed_big` / `unsigned_big` are filterable, so `BigInt` literal rejection is live: [`test_scalars_api.py`][test-scalars-api]`::test_filter_specimens_by_bigint_exact_rejects_non_integer_literal` (bool / float literals, both fields).

- Strawberry emits `data: null`, not absent.
- graphql-core's `ValuesOfCorrectTypeRule` calls `parse_value`, so the scalar's `ValueError` becomes the validation error's `original_error`, and the production policy masks it to `An unexpected error occurred.` w/ a `correlationId`. Asserting the reason needs the pass-through override.
- Must-not row: `test_filter_specimens_by_bigint_exact_accepts_decimal_string_literal` (`exact: "9007199254740993"` selects exactly the seeded row).
- Decorator order: `override_settings` outside `parametrize`, inside `django_db`.

### Wrong tree over the real schema: composition introspection

An `apps/<app>/tests/` module running queries against the REAL composed schema through `execute_sync`, w/ a conftest whose only job is rebuilding the schema w/o HTTP, is rung 4 while rung 1 is one import away. [`test_schema_composition_api.py`][test-schema-composition-api]`::test_the_composed_schema_publishes_each_apps_types` asks the schema `config.urls` serves, one type per contributing app. `assert published is not None` is the clause an in-process row never teaches: `__type` on a missing name returns `null`, so an unregistered app reads as a passing row unless presence is asserted. Moving a test module changes the tracked set ([Test code style](#test-code-style)).

### Exception as the observable: misconfigured cap on GET

"A bad cap cannot hide behind a bodyless request" is deployment-observable: [`test_transport_api.py`][test-transport-api]`::test_a_misconfigured_mount_fails_loud_on_every_request_including_get`, a `cap-misconfigured/` mount w/ `max_request_body_bytes=0` on the file's holder, `pytest.raises(ConfigurationError, match="positive int")` around both a GET and a POST. `ConfigurationError` is not an `HTTPException`, upstream `dispatch` does not translate it, `django.test.Client` re-raises it → the live observable is a raised exception, not a status. Works identically on `AsyncClient`. This is RESOLUTION-time validation (per request), so the "construction-time stays package-side" exemption does not apply.

### The claim is the contrast: `totalCount` opt-in

[Promoting a shortcut test](#promoting-a-shortcut-test) covers selection gating on an opted-in type. The ABSENT half on a bare type is [`test_connection_pagination_api.py`][test-connection-pagination-api]`::test_total_count_is_a_field_only_on_the_connection_that_opted_in`: `allItems(first: 1) { totalCount }` fails validation w/ `Cannot query field 'totalCount'` and `data is None`; `allLibraryGenresConnection(first: 1)` returns one edge and `totalCount == 2`, which proves the count is of the whole set, not the window (stronger than `== 0`). `graphql_payload` for the error half, `assert_graphql_success` for the other; one row, because the claim is the contrast. The SDL-description clause is its own row (`test_the_non_opted_connection_type_keeps_the_inherited_sdl_description`, `__type(name: "ItemTypeConnection") { description }`): generated connection names come from `graphql_type_name`, and only the NON-opted shape keeps the inherited description.

### Every term the name claims: two to-many `orderBy` terms

A row named for two to-many terms must exercise two; read the body against the name before promoting it. Shipped `BookOrder` declares `genres` and `loans`, so [`test_library_api.py`][test-library-api]`::test_library_books_order_by_two_to_many_terms_each_get_their_own_aggregate` drives both over the wire: exact title order, ONE `library_book` query, two `MIN(`, no `DISTINCT`. Seed makes both terms load-bearing (genre alone can't separate two titles; loan alone gives a different order). `"library_book" in sql` also matches the through-table `library_book_genres`; only safe here because the selection touches no relation. Selecting `genres` → filter on `FROM "library_book"`.

### Direct call to a patch vs a real GET

Fakeshop's `/graphql/` accepts GET, so the package's query-param parsing patch (`django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params`) is observable through a real GET, not a direct call on a bare `BaseView()`: [`test_products_api.py`][test-products-api]`::test_get_query_with_object_variables_executes_like_upstream`. Malformed twin: `test_get_query_with_malformed_variables_param_is_the_upstream_parse_400` (`variables='{not json'` → 400 w/ upstream's parse message). Patch-lifecycle rows (apply idempotence, signature drift) stay package-side; they have no wire shape.

### Shorter lessons, one line each

Same procedure; listed so the shapes are known. Rows in [`test_products_api.py`][test-products-api] unless named otherwise:

- **Form stale-field revalidation** → `test_update_item_via_form_revalidates_an_untouched_stale_name`: `updateItemViaForm` on a row named `REJECTED_ITEM_NAME`, partial update omitting `name`. Field key alone (`["name"]`) can't distinguish "reconstructed then revalidated" from "never bound"; assert the message `["This name is not allowed."]` too, else the boundary mutation leaves the row green.
- **Not-found before any auth signal** → `test_update_item_anonymous_on_hidden_private_row_is_not_found_before_any_auth_signal`: anonymous `updateItem` on a private Item: no top-level error, one `FieldError` on `id`. The anonymous arm beside the permitted-caller one; the claim is the ordering.
- **Auth before relation decode** → `test_create_item_via_form_authorize_before_decode_anonymous_gets_auth_denial`: anonymous `createItemViaForm` w/ a private Category's GlobalID: top-level "Not authorized", `data is None`, no in-band `categoryId` error. Serializer twin: `test_create_item_via_serializer_authorize_before_decode_unpermitted_gets_auth_denial`.
- **Explicit `null` FK on a form update** → `test_update_item_via_form_explicit_null_category_id_is_the_form_required_error`: the form's own `required` error, keyed `categoryId` (the input field the client sent, not the form field `category`); the message and the `required` code are what separate it from a decode "invalid id" on the same key. **Omitted required form field** → `test_create_item_via_form_omitted_required_name_is_a_coercion_error_no_write`: coercion error, `data is None`, no row.
- **Dangling non-null FK** → `test_all_items_dangling_forward_fk_is_the_non_null_completion_error_only`: `allItems` as staff after a raw-cursor delete under `connection.constraint_checks_disabled()`; message is graphql-core's `Cannot return null for non-nullable field ItemType.category.`, never a descriptor `AttributeError`. Pass-through required: completion errors are masked too. Keep children-before-parents cleanup in `finally`; teardown's `PRAGMA foreign_key_check` runs before rollback. `override_settings` INSIDE the constraint bracket so the PRAGMA is restored last.
- **Relation-seeded `pageInfo` / `last`+`before`** → [`test_library_api.py`][test-library-api]`::test_genre_books_connection_page_info_four_fields` and `::test_genre_books_connection_backward_pagination_last_before` on `allLibraryGenres { booksConnection(...) }`. The root-pipeline twins (`test_page_info_four_fields`, `test_backward_pagination_last_before`) don't make them redundant: the per-parent relation-manager pipeline is a different code path.
- **`nodes(ids:)` hidden arm** → [`test_library_api.py`][test-library-api]`::test_nodes_batch_mixed_types_order_and_null`: a `repair` Book in the mixed batch; same document anonymous → positional `null`, via `_post_graphql_as_staff` → resolves. Proves the null is visibility, not absence, in two lines.
- **Relay id-only projection** → [`test_products_visibility_api.py`][test-products-visibility-api]`::test_relay_id_only_connection_page_costs_one_query_and_emits_decodable_ids`: staff `allCategories(first: 5) { edges { node { id } } }`: one `products_category` query, each id equals `global_id_for(CategoryType, pk)`.
- **Cascading-hook target blocks elision** → [`test_products_visibility_api.py`][test-products-visibility-api]`::test_cascading_target_hook_blocks_fk_id_elision_over_http`. Failability boundary = `django_strawberry_framework/optimizer/walker.py::plan_relation`'s downgrade, not the elision guard ([the hint pair](#sql-beats-the-plan-object-the-hint-pair)).
- **Async multibyte body** → [`test_transport_api.py`][test-transport-api]`::test_the_async_package_view_parses_a_multibyte_utf8_body_unchanged` on `/async-graphql/`; the variable must be USED (`allItems(first: $value)`) or validation reports "never used" before coercion echoes the value. Spell the multibyte literal w/ `\u` escapes: ASCII-only `.py` is enforced by the `source-layout` hook, not ruff.
- **List-field introspection** → [`test_list_field_api.py`][test-list-field-api]`::test_shipped_branches_introspection_return_types` on the shipped `allLibraryBranchesViaListField`: every `ofType` level asserted needs its nesting level IN THE DOCUMENT, or the assert reads `None`.

### Deleting duplicates

Read the named live sibling, not its name. Every verdict the package row asserts must be there; missing clause → add it to the live row first (two-assert extension), then delete. Grep the asserted VALUE, not just the row name: a shared leaf (`FieldError` envelope, a codec) is usually re-asserted once per consuming flavour's package file. Sweep orphans the deletion strands: helpers, module constants, builder kwargs whose only caller was the deleted row. Ruff sees unused imports, not an orphaned `def`; grep each name, count `1` = definition-only. Make the module docstring truthful (drop bullets that named deleted rows; "X is pinned live" + a kept duplicate of X is a contradiction). Grep `docs/` for `::name`; the citation gate reads `.py`, `KANBAN.md` and the specs; other `docs/` prose is ungated.

### Trim, don't delete, when one clause survives

A multi-claim package row whose other clauses are live keeps only the surviving clause and is renamed to what it now asserts: `tests/extensions/test_debug.py::test_acknowledged_factory_restores_the_cursor_bracket_and_logs_no_warning` keeps no-warning + coordinator-restore; the payload half is live. Renaming a trimmed row is mandatory: a name asserting a payload the row no longer reads is a lie on the failure line.

### Gotchas

Grouped by where they bite.

**Optimizer / SQL**

- A plan w/ any `get_queryset` hook in the selection is `cacheable=False`; live cache rows need hook-free types (`allLibraryMembershipCards`), and the shipped instance via `sys.modules["config.schema"]._optimizer` at call time. Absolute `misses == 1` works only because the acceptance conftest empties the plan cache per test; say so in the docstring.
- Filter captured SQL on `FROM "<table>"` when the selection touches a relation; M2M through-tables share the parent's prefix. Never assert a bare total once a viewer is logged in; session + auth reads ride along.
- Failability mutations get absorbed: a `list`-returning root the optimizer can't plan either way; a guard unreachable behind an earlier downgrade; `model_to_dict(fields=[])` (empty = no filter, fail-open). Mutate at the level you mean to pin: deleting a `Meta` line proves the hint is load-bearing, not that the walker's dispatch is.

**Registry**

- A test that clears the registry and builds only its own types requests `private_registry` (`@pytest.mark.usefixtures("private_registry")`): it starts on an empty registry, and a registry an earlier test left stale is cleared for it instead of rebuilt. Such a test must not read the project schema.

**Settings**

- `monkeypatch.setattr` unwinds at teardown, `override_settings` at block exit; put every assertion depending on both inside the `with`.

**Shapes**

- Connections are `edges { node }`; `__type` on a missing name is `null` not an error; introspection depth is a property of the document; generated connection type names via `graphql_type_name`; filter lookups camel-case (`iContains`), and `"__all__"` expands to ~17 lookups on a text field and ~8 on any other (no text-pattern lookups) (dump `str(schema)` and grep the `...FilterInputType` block rather than guess).
- `TestClient().query()` asserts no errors by default; error rows pass `assert_no_errors=False` and read `res.errors` (list of dicts). `assert_graphql_success` asserts `"errors" not in payload`; `graphql_payload` for the envelope.
- A live module's one-sentence docstring feeds [TREE.md][tree-tests]; widening it → re-render, same change.

**Failability loop mechanics**

- Anchors must match exactly once; include leading indentation. Replacement replaces the WHOLE anchor (multi-line anchor → repeat unchanged lines w/ literal `\n`).
- Mutate to a different VALID statement (`raise`, `return int(value)`, `if False:`), never to nothing → `IndentationError` = collection error = invalid count.
- Non-zero exit ≠ proof; collection errors exit non-zero too. Assert exit 1 and expected node count collected.
- Read the per-boundary failing node-id LIST, diff against the rows you expected. The table's count can look healthy while the row you wanted is absent.
- Prove restore by hash (sha256 / `filecmp`), not by "tests pass again".
- Each entry runs the scope twice (baseline + mutated); six entries over two live files ≈ 90s. Don't narrow scope to one node id to save time; the recorded row set is the artifact.

## What legitimately stays package-side

Claims w/ no wire shape. Accepted categories + the file showing the docstring discipline:

- **Absence proofs.** Package view imports w/o `channels` = claim about what isn't there; request can't make it. [`tests/test_views.py`][tests-views]; its docstring lists every request-shaped sibling living in [`test_transport_api.py`][test-transport-api].
- **Internal state a response can't show.** Wire `413` identical whether body cap cost one `seek` or a full allocation. Bound only assertable from inside → measurement rows stay in [`tests/test_views.py`][tests-views]; every status code / reason string live. Same for the optimizer's runtime path tuple (`tests/types/test_resolvers.py::test_runtime_path_from_info_strips_list_indexes_and_keeps_aliases`).
- **Class-creation-time validation.** `Meta` raising `ConfigurationError` at class creation never reaches a schema. Registry lifecycle, finalizer ordering, duplicate-name rejection, concrete-subclass identity in [`tests/test_connection.py`][tests-connection]. NOT resolution-time configuration: a `ConfigurationError` raised per request (`max_request_body_bytes=0`) is live, as `pytest.raises` around `Client().get` ([misconfigured cap on GET](#exception-as-the-observable-misconfigured-cap-on-get)).
- **One-declaration-per-process.** `login` / `logout` / `register` declared once per process → permission-gated variant can't coexist w/ fakeshop's `AllowAny` default in one composed schema. [`tests/auth/test_mutations.py`][tests-auth-mutations] pins gated denial strings on isolated throwaway schemas; [`test_auth_api.py`][test-auth-api] owns every consumer-reachable behaviour.
- **Invisible-by-design matrices.** Nine rejected encodings share one status + message on purpose; per-encoding `__cause__` visible only package-side.
- **Soft-dep absence.** `cryptography`, `channels`, `django-debug-toolbar`, `djangorestframework` simulated absent via [`tests/_soft_dependency.py`][tests-soft-dep] (`sys.modules[name] = None`). Never patch `builtins.__import__`; guards use `importlib.import_module`, patched import silently passes.
- **Throwaway-schema internals.** Type-name `globalid_strategy`, multi-type-over-one-model `__typename` dispatch, `_stamp_node_type` isolation, custom `relay.NodeID` coercion/decode, construction- / finalize-time guards, consumer `resolve_nodes` override contracts, `SyncMisuseError.original_error` (not a wire field). [`tests/test_relay_node_field.py`][tests-relay-node-field]; live sibling [`test_library_api.py`][test-library-api].
- **No WebSocket mount.** Fakeshop has no `config/asgi.py`. [`tests/test_routers.py`][tests-routers] and [`tests/test_consumers.py`][tests-consumers] stay package-side (Channels scope, `WebsocketCommunicator`, actor-revalidation checkpoints). HTTP sibling [`test_transport_api.py`][test-transport-api].

Same discipline every case: package docstring says what it keeps, why no live request can express it, names the live sibling. Unsure whether a claim has a wire shape → try writing the live row. Don't argue.

## Isolation contract

`config/schema.py` composes every app's `Query`/`Mutation` into one `DjangoSchema`, `finalize_django_types()`, mounts a module-level `DjangoOptimizerExtension` singleton. `tests/` clears the global registry for its own isolation. Partial reload after a clear = classic order-dependent failure: reload one app → other apps' types gone → composed build raises `LazyType` `KeyError` or `DuplicatedTypeName` depending on what the previous worker left in `sys.modules`.

Single-sited in [`schema_reload.py`][schema-reload], applied by [`conftest.py`][conftest] in three ways:

- **Once per module per worker**: `_reload_project_schema_for_acceptance_tests` clears registry, reloads every `apps.<app>.schema` dependency-safe (`glossary` before `kanban`; `CardGlossaryTermType.term` FKs into glossary), then `config.schema` + `config.urls`.
- **Before every test**: `_isolate_project_schema_for_acceptance_test` empties the module-level optimizer's plan cache; schema, URLconf and finalized types are reused. Fingerprints every registry map + app module; test mutated registration → teardown marks the registry stale, incl. after assertion failure, and the next test that reads the project schema runs the full rebuild first (the module fixture runs it on the way out when the module's last test left it stale). `private_registry` tests skip that rebuild.
- **On request**: `project_schema_override` = the full-rebuild callable, for re-finalizing under `override_settings` when the setting is read at schema CONSTRUCTION (a `Meta` body, `FAKESHOP_TEST_LOAN_CONNECTION`); function guard restores default after. Settings read per request (`MEDIA_ROOT`, `DEBUG`, `MIDDLEWARE`, `AUTHENTICATION_BACKENDS`) need only `override_settings`.

`apps/<app>/tests/` never composes the project schema; a test needing it is a live row here. The project-level `examples/fakeshop/tests/` modules that build the aggregate (`config.urls`, `export_schema`, `inspect_django_type`) call the same `reload_all_project_schemas`: `test_urls.py` and `test_export_schema.py` through the module-scoped `reload_project_schemas` fixture in that tree's `conftest.py`, `test_inspect_django_type.py` through its own per-test fixture and cold-path teardown.

Adding an app → add to `_PROJECT_APP_SCHEMA_MODULES` in [`schema_reload.py`][schema-reload] + grep whole test tree for other private module lists. Order independence is a contract; invisible under `-n0` / single module; verify w/ full parallel sweep.

## Clients, transports, credentials

[`graphql_client.py`][graphql-client] helpers (sync) and [`AsyncTestClient`][testing-client] (async) = default for every ordinary row. A raw `.post(` / `.generic(` on a Django client is an exemption (spec-043 Decision 11), declared at the call, never inferred: a `# raw-envelope exemption: <what the envelope is>` comment in the comment block directly above the line the call starts on. [`tests/test_ci_governance.py`][tests-ci-governance]'s `test_no_live_tier_module_posts_raw_without_a_declared_exemption` fails any undeclared one, sync or async.

- **Raw envelope.** `post_graphql_raw` = bare `client.post` for malformed bodies / content-type negotiation, where the body IS the subject and the client's builder would replace it. [`test_transport_api.py`][test-transport-api] = raw-envelope resident: hostile `Host`, `secure=` / `enforce_csrf_checks=` clients, in-process `ASGIHandler` for fragmented bodies, real multipart control fields.
- **Async.** [`graphql_client.py`][graphql-client] stays sync-only; no shared async helper. Async rows drive the package's own [`AsyncTestClient`][testing-client] against a module-owned `AsyncDjangoGraphQLView` mount: [`test_relations_async_api.py`][test-relations-async-api] constructs it bare; the async mutation rows of [`test_products_api.py`][test-products-api] go through `AsyncTestClient(client=...)`, passing a `force_login`-ed `django.test.AsyncClient` where the row needs a user. [`test_list_field_async_api.py`][test-list-field-async-api], [`test_relation_deadline_api.py`][test-relation-deadline-api] and [`test_extension_isolation_api.py`][test-extension-isolation-api] do the same, the last carrying one `AsyncClient` across a row's requests. Async rows: `@pytest.mark.django_db(transaction=True)`, rely on [`tests/conftest.py`][tests-conftest] to close per-task SQLite connections (else `ResourceWarning` = error here).
- **Multipart.** `TestClient().query(..., files={"data.attachment": SimpleUploadedFile(...)})`, path-keyed variables; [`test_uploads_api.py`][test-uploads-api] w/ `tmp_path` `MEDIA_ROOT`. GraphiQL can't; live tier = only end-to-end proof of the upload path.
- **Credentials.** `Client().force_login(user)` on a `create_users` user; `TestClient.login(user)` = bracket that logs out even on raise; `Client(enforce_csrf_checks=True)` when CSRF is the claim (Django test client skips CSRF by default). `login` mutation is a SUBJECT only in [`test_auth_api.py`][test-auth-api]; everywhere else `force_login`.
- **DEBUG-gated detail.** pytest-django forces `DEBUG=False`. The production policy replaces any message whose `original_error` is a real exception: resolver exceptions, custom-scalar validation errors (`parse_value` runs inside validation), graphql-core's own non-null completion messages. Parse / syntax / structural-validation errors carry none and travel verbatim. Row asserting one of the masked messages → override `DEBUG=True` AND drop toolbar middleware from `MIDDLEWARE` in the same override: fakeshop wires debug-toolbar behind `DEBUG`, toolbar would inject a panel against `djdt` routes the URLconf never computed. Copy `_ERROR_POLICY_PASS_THROUGH` from [`test_products_api.py`][test-products-api]. Row asserting only THAT an error happened → no override; assert `data is None` (never absent) + `errors` present.
- **Credential helpers differ.** `_login_with_perm(...)` does NOT seed (needs `create_users(N)` first); `_staff_client()` seeds itself. `Client()` constructed INSIDE a `MIDDLEWARE` override (handler caches its chain on first request); control envelope captured BEFORE an `AUTHENTICATION_BACKENDS` override; a live module's class is a valid settings string (`"test_auth_api.PermissionDeniedBackend"`, `test_query/` is on `pythonpath`).
- **Test client family** covered both sides: [`test_client_api.py`][test-client-api] posts real ops through `TestClient` / `AsyncTestClient` / `GraphQLTestCase` / `GraphQLTransactionTestCase`; DB-free mechanics in [`tests/testing/test_client.py`][tests-testing-client]. Consumer usage: [docs/README.md][docs-readme-testing].

## Environment tiers

Two knobs, mutually exclusive, un-skip their tiers. Neither runs under bare `uv run pytest`.

**Sharded.** `FAKESHOP_SHARDED=1` adds `shard_b` on `db_shard_b.sqlite3` beside `default`. Sharded module gates at import: `pytest.skip(..., allow_module_level=True)` on the env var, NEVER `pytest.mark.skipif` (var changes `DATABASES` at settings import; mark evaluates too late). Each test `@pytest.mark.django_db(databases=["default", "shard_b"])` or pytest-django blocks the alias. Seed the full non-null chain on each alias read. Reference: [`test_multi_db.py`][test-multi-db]: `.using("shard_b")` keeps a deep relational leaf's hop subqueries on `shard_b`, no `library_loan` SQL on `default`, proven by capturing both aliases.

**Postgres.** `FAKESHOP_PG_DSN=postgres://...` → `default` = Postgres, un-skips `@pytest.mark.pg` (registered in `pytest.ini`, auto-skipped elsewhere by repo-root `conftest.py`). Launch `uv run --group pg pytest` (group pinned for the run). PG surfaces pk-magnitude bugs SQLite hides: per-test SQLite pks stay single-digit forever, PG sequences never rewind. PG row failing order-dependently but passing alone = pk-magnitude bug before pollution; repro `ALTER SEQUENCE ... RESTART WITH <big>` in one test.

## Prove the test can fail

Passing suite = evidence only if it could have failed. Every new boundary owes one loop: remove boundary → run the rows claiming to pin it → record failing node ids → restore → prove restore by byte compare. [`prove_failability.py`][prove-failability] mechanizes it from a manifest; refuses `-x` / `--maxfail` (cut run can't fail rows after the cut); collection error or odd exit code = invalid count, never zero. Method + recording rules: [BUILD.md][build-failability].

- **Uncovered line = claim nobody tested.** Read the claim first. Line may be uncovered because its reasoning is wrong; a blessing test locks the defect in.
- **Never paper over**: no `pragma: no cover`, no test-only fix, no follow-up card. Line a real fakeshop query can't reach = smell in prod code (too-clever branch, wrong abstraction). Fix the abstraction. `pragma: no cover` only for branches the runner structurally cannot execute.
- **Statement coverage can't see fail-open expressions.** `max(x, 0)`, `getattr(obj, name, default)`, `x or fallback`, broad `except` read covered once the happy path runs. Find by reading; BUILD.md "Fail-open shapes" lists them.
- **Two outcomes are not verdicts.** GREEN after the mutation = the mutation did not remove the boundary (reachable through another surface, absorbed by an earlier branch, itself fail-open) → re-aim; says nothing about the row. Collection ERROR = the mutation broke the build, not the claim → invalid count. Smallest mutation that changes one published fact: `Meta.name` rename to unpublish a type; one scalar dropped from `Meta.fields` that no `FilterSet` / `OrderSet` / `relation_shapes` entry names; one operand in package source; always a different VALID statement, never nothing.
- **Read the failing node-id list, not the count.** Diff it against the rows you expected to fail; a healthy count can hide the one row that survived. The survivor's docstring is naming a boundary it doesn't pin ([corrupt image](#a-stand-ins-docstring-can-name-the-wrong-boundary-corrupt-image)).
- **Guarded twice in series = no single-site mutation fails it.** A plan-time refusal plus a fetch-time fail-closed arm each hide the other's removal; `prove_failability.py` (one contiguous anchor per entry) can't express the conjunction. Record the pair by hand (both sites, one restore loop, hash-verified), name both sites in the live row's docstring, and KEEP the package unit row for the half w/ no independent wire shape; it is not a stand-in (`tests/optimizer/test_single_parent_fetch.py::test_spec_rejects_a_keyset_seek`).
- **Concurrently dirty tree.** The script snapshots a file at entry start and restores it at entry end; a concurrent edit to that file inside the window is silently reverted. `git status` the files you will mutate first; loop only over files nobody else is editing, or coordinate.

## Test code style

Production rules unchanged: ASCII-only `.py`, trailing-comma explosion at 4, `path::Symbol` never line numbers, line 99. Plus:

- **Docstring = invariant.** What must hold, and why when it helps. May cite spec decision (`spec-043 Decision 3`), glossary anchor, upstream ticket. Never process provenance: no severity labels, review-round / worker attribution, slice numbers, "previously", "as of 0.0.N". Removed provenance carried the WHY → restate as a clause about the code.
- **Name = observable claim.** `test_genre_connection_total_count_omitted_no_count` tells the reader from the failure line. `test_spec_030_case_4d` doesn't.
- **Failing assertion carries the payload.** `assert "errors" not in payload, payload`.
- **Seeding rules absolute.** `seed_data(N)` / `create_users(N)` first for products/auth; inline `Model.objects.create` for library; seed helpers' own tests = only exception.
- **Expected values derived, not memorized.** Faker → compute from ORM. Package-owned encodings (GlobalIDs, cursors) → mint w/ package helpers.
- **Format after every edit, stop.** `uv run ruff check --fix .` then `uv run ruff format .` (format last: `--fix` can add a magic trailing comma the formatter rejects). No `pytest` after edits unless asked; asked → `uv run pytest`; single test `uv run pytest -n0 path/to/test_file.py::test_name`.
- **New / deleted test file changes the tracked set.** After staging: `uv run python scripts/build_kanban_tracked_path_constants.py`, stage regenerated `examples/fakeshop/apps/kanban/constants.py` with it, else the hook rejects every later commit until a constants-only sync. Also re-render [TREE.md][tree-tests] (`uv run python scripts/build_tree_md.py`): one row per test module, a deleted module strands its row and the citation gate can't see it.
- **Removing code sweeps all four trees** for orphan imports / fixtures / helpers / builder kwargs, same change; ruff catches imports only. Then `grep -rn '::<name>' docs/` for stranded prose citations.
- **Trimmed row = renamed row.** Keep one clause of a multi-claim test → rename it to that clause; a name asserting a payload the row no longer reads lies on the failure line.

## Checklist

1. Claim covered from the highest reachable rung; any lower-rung test's docstring says why not higher + names live sibling.
2. Acceptance AND rejection each have a row.
3. No loop in a test body; every case own node id w/ `ids=`.
4. Seeding per app rule; a must-not-match row present; list assertions carry `orderBy:`.
5. Payload exact where data allows; SQL filtered to the table under test.
6. Identifiers / cursors minted, never pinned.
7. Promoted shortcut deleted; live row shown to fail w/ boundary removed; failing node ids read, not counted; orphans + `docs/` citations swept.
8. Scoped claim carries its must-not (same caller reads, adjacent surface, other verdict).
9. Async rows `django_db(transaction=True)`; sharded rows gate at module level + declare both aliases.
10. Module docstring one sentence (TREE.md re-rendered if changed); test docstrings no provenance; stand-in's claim verified against code before it was copied.
11. Message asserted → pass-through override present; error asserted → `data is None`, not absent.
12. `uv run ruff check --fix .`, `uv run ruff format .`, `uvx pre-commit run --files <paths>`; test file added / removed → kanban constants regenerated AND TREE.md re-rendered.

## Suite map

Module docstring = authoritative description; this = index. Read the docstring before adding a row: the suite owning the surface receives the case.

| Suite | Owns |
|---|---|
| [`test_library_api.py`][test-library-api] | Acceptance app end to end: FK / reverse FK / O2O / M2M traversal, choice enums, nullable scalars, optimizer SQL shape + hints (non-sentinel `skip=True`, reverse-O2O `card` JOIN in the root SQL, flag-gated `select_related()` book hint still prefetching past `BookType.get_queryset`), a consumer `select_related` the selection never reads (forward key, reverse one-to-one, second hop under a read first hop, a skip-hinted relation) compiling under the optimizer's `.only()` with the joined row selected whole, a root or child-hook `.only()` / `.defer()` loaded as the union with the selection (sync counts, async without errors), a child hook's `prefetch_related` meeting the planned `Prefetch` on the same lookup, link columns kept for a consumer `prefetch_related` (forward key and generic foreign key), a `SKIP` relation (list, nested connection, async non-pk link) and a consumer-assigned relation, a `__typename`-only reverse one-to-one JOIN, shipped plan cache reused across HTTP requests, consumer relation overrides, `filter:` / `orderBy:`, declared `conditionSpan` / `tierSpan` ranges over the text and integer choice columns comparing bounds off the choices and declared `conditionAmong` / `tierAmong` lists of enum members (flat and under `not`), django-filter's `MultipleChoiceFilter` (`conjoined` too) / `TypedMultipleChoiceFilter` / `AllValuesMultipleFilter` and a `Meta.filter_overrides` `MultipleChoiceFilter` on a holder over `Shelf`'s text and choice columns, each taking a list typed from its column (`BLANK` and `MEMBER_1` as their values, `[]` and `null` constraining nothing) and refusing a value off its own choices as `FILTER_INVALID` `invalid_choice`, declared `pkSpan` / `pkAmong` and `branchPkSpan` / `branchPkAmong` over Django's `pk` alias and `branch__pk` publishing `Int` / `[Int!]` as `idSpan` and the generated `id` `in` do, answering the rows the `id` spelling answers (flat, under `not`, and reached from `BookFilter` as `shelfPkSpan` / `shelfPkAmong` and the nested `shelf` branch) and refusing a malformed bound, a string element and a value past `Int` with the coercion error `id` gets, and `PatronProfileFilter`'s `pkSpan` / `pkAmong` over its one-to-one primary key comparing the `Patron.id` it stores (two bounds as `gte` + `lte`, one bound alone, under `not`), explicit `in: []` on a generated choice `in` as the empty set (flat, inside `not` / `or` / `and`, a nested branch, a nested `booksConnection(filter:)`) beside a declared `ModelMultipleChoiceFilter` skipping `[]`, a logical arm constraining nothing (`{}`, `null` lookups, the declared skip) as the identity, row-preserving deep relational predicates (no `DISTINCT`, no root `JOIN`, each declared hop a visibility-scoped subquery), flat relation leaves answering like their nested twins (target `get_queryset` + explicit `queryset=` at every declared hop, an owner-bound projected leaf, a logical arm, anonymous / staff / async), a child leaf whose absence acts (`IssueFilter.embargoed`, a checkbox) reaching a `PeriodicalFilter` request only when named flat or nested, `{}`, an own leaf, a flat sibling leaf and a logical arm answering without it while a nested sibling leaf runs the child's own form, where the unnamed checkbox still acts (anonymous / staff / async), filters a `get_filters()` override adds (`PatronFilter`'s `emailContains` on patrons and, flat and nested, on loans through the `LoanFilter` <-> `PatronFilter` cycle; `IssueFilter`'s `method=` `titleStarts` flat and nested on periodicals, sync and async), and a holder child filter whose absence would act (consumer field, `empty_value`, `__init__`-edited, `required`, own `filter`) applied by a parent or grandparent request only when named, walked leaves answering over the visible world (one- and two-hop `isNull: true` / `false` over parents with an absent, a hidden, a null-terminal and a set related row, the hidden row answering like the absent one; the nested twin staying existential; forward and to-many key membership naming a hidden target or one outside an explicit `queryset=`; the declared `exclude=True` `GenreFilter.withoutBookTitled` beside its `not:` twin and through its projections (`genresWithoutBookTitled` on books, `bookGenresWithoutBookTitled` on loans) negated at the outermost parent; `BookFilter.titleStarts`, a filter holding a `filter` of its own, flat, projected (`booksTitleStarts` on genres, `bookTitleStarts` on loans) and nested over a visible and a hidden book; a supplied empty value, walked (`bookShelfTopic`) or projected (`patronEmailMustHaveAtSign`), constraining nothing, so every loan matches, including those whose book or shelf the viewer cannot see; inside `and` / `or` / `not`; anonymous and staff, and through `apply_async` on a `/graphql-async-test/` holder connection), mixed direct/relational `OR` oracle over the seeded loan graph, flag-gated `allLibraryLoansConnection` proof, a lone surrogate or NUL in a filter text value refused as `FILTER_INVALID` on every filter shape a query binds it through (a plain-field text-pk relation key and a resolver's `SimpleLazyObject` included) while a GlobalID filter keeps `GLOBALID_INVALID` and a disabled field ignores it, each `FILTER_INVALID` key the field's path from the filter root (a nested branch keyed as its flat copy, a logical arm as `or_0` / `not`, sync and async) and `ShelfFilter`'s form-level refusal of a home branch named by pk and by name keyed `<path>____all__` through a branch and inside an arm, the whole-set filter sweep (`fields = "__all__"` and a set declaring only `Meta.exclude` publish one key set: forward single-column relations and the primary key unless `Meta.exclude` names it, never a many-to-many), GlobalID rejection codes, a `PublisherType` id read over `/graphql-async/` from the `house_code` its page or join loads (also published as `identity` by a `NameConverter`, on the async holder mount), GlobalID filters into `PublisherType`, whose id carries `house_code` (own id, own-id leaf through a hop flat and nested, forward / `to_field` / to-many keys and two hops, `not:` arms, a nested `printings2Connection(filter:)`), each returning the emitted id's row, the house whose code is another's primary-key digits rather than that key's row, nothing for a key-carrying or unknown id and `GLOBALID_INVALID` for a NUL-bearing code, the house whose stored code the column's validator refuses through every shape, at a primary-key filter's statement count, a primary-key target's GlobalID compiled on its key column, and `SeriesType`'s annotated `handle` id compared on its own rows and through the `inSeries` hop (flat and nested alike, the declared `handle` filter included) and refused `GLOBALID_UNVALIDATABLE` across the `Printing.series` key, shipped `node` / `nodes` / typed `genre(id:)` refetch (malformed / uncoercible / hidden / missing / mixed-batch holes, a publisher whose stored house code the column's validator refuses resolved, a `PatronProfileType` id past `Patron.id`'s range null with no error and no profile read, single-node missing row null with hidden-vs-missing query cost parity, per-table `nodes` query counts, a `LoanType.get_queryset` hook's `FETCH_PEERS` loading every `nodes` position's lazy `patron` in one statement (a repeated id and `/graphql-async/` included) and its `FETCH_RAISE` refusing each position, typed `DjangoNodesField` on `/graphql-test/`, async colour on `/graphql-async/`), genre-connection pagination + `totalCount` gating + filter/order/slice composition, post-`FilterSet` seal on the shipped genre connection (every defect class refused by name w/ SQL capture, `super()` pass-through admitted), relation-seeded `booksConnection` `pageInfo` + `last`/`before`, nested `booksConnection` argument guards (`first` overrun clamping, stale `after` cursor no-error, `first` + `last` mutual exclusivity rejection), two to-many `orderBy` terms each w/ own aggregate, descending to-many `MAX(` SQL on `allLibraryBooks` plus async to-many `orderBy` on `allLibraryGenresViaListField` over `/graphql-async/`; custom-input model writes (`genres` replace / clear vs omit / `null` / wrong-type / uncoercible member, choice-enum unwrap on create + update), raw-pk M2M attach + nonexistent member on `createShelf`; a `createEdition` `publisherId` whose house code the column's validator refuses relating that stored publisher; a lone surrogate in a raw-pk id into the text-keyed `Edition` (`editionId`, a `boundWith` element) refused at the relation type-check by every write flavor on create and update, before its lookup, beside a well-formed unknown ISBN's relation error, and in the raw `id` locating an `Edition` (`updateEdition` and its `ViaForm` / `ViaSerializer` siblings, `deleteEdition`) refused before the locate, beside a well-formed unknown ISBN's not-found; an `updatePatronProfile` / `updatePatronProfileViaForm` `id` past `Patron.id`'s range answered with the not-found `FieldError` and the row unchanged; model writes through the `to_field` key `PatronProfile.favorite_genre` on `updatePatronProfile` (a genre id stores the genre name, including beside a genre named like that id, `null` clears, omitted keeps, a missing genre is the relation error with the name kept); a `ModelForm` write through the same key on `updatePatronProfileViaForm`, whose declared field resolves a genre by id (an omitted genre keeps the stored name, including when that name is another genre's id; unset stays unset; a genre replaces it, `null` clears it; an omitted stored name no genre carries is the `favoriteGenreId`-keyed `invalid_choice` error with nothing written, including when that name is another genre's id); a single relation keyed `""` in the form field's lookup column refused as that field's `invalid_choice` error with nothing written, never a clear (`updatePatronProfileByGenreNameViaForm` over a stored name `""` with or without a genre carrying it, decided without a genre read, and a supplied genre named `""`, beside an omitted genre kept, an unset one left unset and a supplied genre or `null` replacing a stored `""`; `updateShelfViaForm` / `createShelfViaForm` over a branch named `""`, omitted or supplied, beside an omitted branch kept and a supplied one replacing it; `updatePrintingViaForm` over a stored edition ISBN `""`), while a `boundWith` member keyed `""` stays linked, omitted or supplied, and a `boundWith` element `""` naming no edition is decoded to the relation error, never a clear; serializer writes through the `to_field` key `PatronProfile.favorite_genre` (create and update with a genre, `null` and omitted, the column holding the genre name; create also through the renamed field `fav`) with a custom `create()` re-pointing the validated genre refused by the post-save attestation under both spellings and a field validator renaming it in place refused by the relation-intent walk; writes through the `to_field` key `InterlibraryLoan.lender` into the nullable `Branch.isil` in all three flavors (`createInterlibraryLoan` / `updateInterlibraryLoan` and their `ViaForm` / `ViaSerializer` siblings: a branch with an ISIL stores it, a branch with none is the `lenderId` relation error like a hidden or missing branch, with nothing written and the prior ISIL kept, and `null` clears); a serializer `PrimaryKeyRelatedField(many=True)` over the reverse foreign key `Branch.shelves` on `createBranchViaShelvesSerializer` / `updateBranchViaShelvesSerializer` (the input is `[Int!]`, the named shelves are re-pointed at the branch after one batched visibility read, an update attaches without detaching, and a hidden shelf is the `shelves` relation error with nothing written); a client-assigned primary key, a required create input on `createPatronProfile` / `createEdition` and the `ModelForm` `createPatronProfileViaForm` (a free key INSERTs the row with no `UPDATE`, a taken key is the `unique` error, a missing patron the relation's `invalid`, and a key a competing writer saves between validation and the save is the `"__all__"` `constraint` envelope with nothing written, never an overwrite); a `ModelForm` update whose located row is deleted after authorization (`updateBookViaForm` over a full input naming `genres`, with a loan and an archived genre; `updatePatronProfileViaForm` over the client-assigned `patron` key) answered with the `conflict` envelope, no `INSERT` run and the stored state rolled back and on no update input over `PatronProfile` in any flavor (sending `patronId` is a GraphQL validation error, an update keeps the key and writes only its row); a serializer `PrimaryKeyRelatedField` over the generic foreign key `CirculationDesk.content_object` on `updateCirculationDeskHoldViaSerializer` (its `Book` queryset names the target: a visible book stores its content type and pk, a book hidden by `BookType.get_queryset` is the `contentObjectId`-keyed error with nothing written, `null` clears the hold); serializer M2M `pk__in` batching (top-level `altBranches` and nested shelves) plus unauthorized `updateBookGenresViaSerializer` never querying `library_book_genres` while the granted path does snapshot it, after the permission read; consumer `Prefetch` children over the proxy-targeted relation `BranchNote.branch` -> `ProxyBranch` admitted for the proxy AND the concrete `Branch`, refused over an unrelated table, its unmasked seal wording readable under error-policy debug pass-through; flag-gated secondary `NullabilityOverrideBookType` Node emitting `library.book:<pk>` so `node(id:)` refetches as `BookType`; `ShelfType.books` binds to primary `BookType`, not that secondary; a target hook returning a sliced queryset refused with the typed `sliced` defect on a plain list relation before any child query runs, and its nested-connection control refused by the per-parent fallback's own read-surface seal after the parent query, which is what proves the walker still admits the shape the degrade path exists for; a source whose selected annotation's node already ran a row fetch (an evaluated `Prefetch` cache, or a hook result a sibling clone fetched) served at a fixed query count: a consumer `Prefetch` over `loans` through `Loan.objects.annotate(...)` (aggregate and non-aggregate, flag-gated `allLibraryAnnotatedLoanBooks`, absent by default) and a flag-gated `LoanType.get_queryset` returning an annotation a sibling clone already fetched (root connection, per-parent nested list and connection, node refetch, and the planned `loans` / `loansConnection` children under `allLibraryBooks`), each also over `/graphql-async/` at the sync view's statements, where `allLibraryBooks`' plain `def` root has its plan built off the event loop; a root that evaluates its own queryset (`allLibraryBranchesEagerEval`) answering the masked error on `/graphql-async/`. |
| [`test_library_inheritance_api.py`][test-library-inheritance-api] | The venue surface's model shapes: inherited `Venue` columns projected through the `venue_ptr` join in one statement (and through both joins for `SelfServeDesk`), unselected inherited columns kept out of the projection, `orderBy: openedOn` sorting by the parent table in both directions, desks hidden with their closed `Venue` through the parent-link cascade (transitively for the kiosk chain); `repairticket` / `venuebadge` / `venuesponsor` resolving through the default accessors of relations declared without `related_name`, one statement each; a withdrawn (`VOID-`) badge and a `Withdrawn` sponsor absent from the reverse accessors (`venuebadge: null`, dropped from `venuesponsor`) and from both roots, without errors; the nullable `lead_ticket` cycle cascading one way (unled venue kept by the `IS NULL` disjunct, venue with a withdrawn lead ticket hidden, `leadTicket { venue }` walking back); `allLibraryOpenVenues` served from the `OpenVenue` default manager against `allLibraryVenues` as control; a sign on a city-less branch hidden because the cascade composes the `VisibleBranch` target from its default manager while `sign.branch` still loads it; `CirculationDesk` publishing `children` / `profile` under a cascade scoped to `branch` / `shelf` (served despite its generic key, restricted-branch desk hidden from anonymous, shown to staff); the multi-column `ShelfLabel.shelf` `ForeignObject` published by the `"__all__"` `ShelfLabelOrder` after its carriers and ordered by `branch_id` then `shelf_code` in one statement (`ASC` / `DESC`), a label on the hidden `secret` shelf sorting as one with no shelf for anonymous (`ASC` / `ASC_NULLS_LAST` / `DESC`), a label naming no shelf at all kept and sorted as missing in a statement with no `JOIN` (`ASC` / `DESC`), and `allLibraryBranches` ordered by `shelfLabels: { shelf }` through one aggregate per carrier, each visibility test correlated to `library_shelflabel.branch_id` / `shelf_code`, every branch kept in one statement (`ASC` / `DESC`); `allLibraryShelfLabelsFiltered` filtering by `shelf`: `exact` / `in` take the shelf's raw primary key and match both carriers (a same-code shelf on another branch matches nothing, the hidden `secret` shelf matches nothing for anonymous), `isNull` publishes `Boolean` and answers over the visible shelves, a label on the `secret` shelf null for anonymous and not for staff, a label naming no shelf null for both, in one statement correlated on both carriers with no `JOIN`; `archiveGenres` absent from `BookInput` / `BookPartialInput` beside the editable `genres`; `MediaSpecimenInput` optional through `blank` (`optionalAttachment`) and through `null` (`spareImage`) separately, `attachment` still `Upload!`; `updateLendingDesk` and its `ViaForm` / `ViaSerializer` siblings writing the `Venue` table and the desk's own as two `UPDATE`s (the model and `ModelForm` flavors naming every loaded non-key column in `update_fields`, which a `pre_save` receiver sees; the serializer's plain save `None`), and a desk deleted after authorization, whole or only its own table, answered with the `conflict` envelope by every flavor and rolled back (no `INSERT` from the model or `ModelForm` flavor; the serializer's re-`INSERT` refused), and an `id` of `2**70` answered with the not-found `FieldError` by every flavor with the desk unchanged; `createKioskFault` and its `ViaForm` / `ViaSerializer` siblings typing `kioskId` `Int!` from `Venue.id`, two parent links below the non-Relay `SelfServeDesk` key, storing a visible kiosk, and answering a kiosk under a closed venue or a missing one with the relation error and nothing written. |
| [`test_library_shapes_api.py`][test-library-shapes-api] | The publishing surface's relation shapes, one planner rule each: a Relay id minted from a relation primary key (`PatronProfile.patron`, one statement, no patron read), a Relay id read from its `relay.NodeID` column beside a surrogate `id` (`PublisherType.house_code` at the root page, through forward keys and under a prefetched reverse key, in the statement loading the publisher row, also when a `NameConverter` publishes the `relay.Node` GlobalID field as `identity`) and from an annotation (`SeriesType.handle`, beside the primary key alone), `<word>_<digit>` names projecting their real columns (`Edition.isbn_10` on a scalar, `Edition.publisher_2` on a forward key), two `strawberry.field(name=...)` names whose normalized spellings collide each returning their own column, forward-key id elision when the target key is a text column not named `id` (`Printing.edition` answered from `edition_id`) against its non-key control that joins `library_edition`, elision refused through a `to_field` key (`PatronProfile.favorite_genre` stores the genre name) and refused into a custom `relay.NodeID` (`PublisherType.house_code`, the id decoding to the house code), a digit-boundary reverse accessor paging two parents off one `ROW_NUMBER() OVER (PARTITION BY publisher_2_id)` statement, and a child default manager returning `.distinct()` leaving `annotationsConnection` unplanned - no window anywhere, one `library_annotation` statement per parent, pages still correct; a random `Book` order (hook `"?"` / `Random()`, each direct and reversed, `Random()` under a composition, an annotation alias by name / descending / through a transform / under a name holding `__` / through an `F`, a `When` condition reading one; `Meta.ordering` `"?"` / `Random()` / `Random().desc()`; a `shelf` name under a random `Shelf.Meta.ordering`) leaving `booksConnection` unplanned under `first` / `last` / `after` / `before` windows - one non-window `library_book` statement per genre, each page structured exactly as the pk-ordered window serves it, while a condition's string literal spelled `"?"` or like a random annotation keeps the one windowed statement; an order naming a relation paged by the window exactly as with no optimizer (`Book` by `shelf` - hook ascending / descending / reversed and `Meta.ordering` - under five `Shelf.Meta.ordering` shapes, by `genres` and `loans` multiplying rows, `Printing` by `edition` reaching the nullable `publisher_2`, `ShelfLabel` by its multi-column `shelf` (its carrier columns, a declared `Shelf.Meta.ordering` ignored), `PatronProfile` by its one-to-one key with the key tiebreak in every statement; two statements, one `ROW_NUMBER`), and a related `"?"`, an ordering loop or a condition item raising Django's error with and without the optimizer; a hook `extra(order_by=...)` `Book` order (a descending field, its own `table.column`, its foreign key's raw column, a joined shelf column, a quoted table name, each as written and reversed) paged by the window exactly as with no optimizer and as Django orders the hook queryset itself, under `first` / `last` / `after` / `before` windows (two statements, one `ROW_NUMBER`); mixed-case Django names resolving by their published spelling (`Distributor.displayName` projecting its own column, the forward key `Consignment.distributorRef` one `JOIN`, its reverse `consignmentItems` one prefetch on `distributorRef_id`, both relation counts at one and three parents); `ReadingListEntry`'s `ordering = None` (clearing its abstract parent's title order) paging a no-`orderBy:` connection in pk order at the root and inside the nested `entriesConnection` window, the parent `ReadingList` keeping its inherited title order, and a resolver's bare `.order_by()` switching that inherited order off so `allLibraryReadingListsUnorderedConnection` pages in pk order. |
| [`test_products_api.py`][test-products-api] | Canonical consumer app: connection reads, all three mutation flavours, `DjangoModelPermission`, per-field filter permission gate, own-pk GlobalID filtering, `RelatedFilter` traversal, flat `EntryFilter.property` leaves answering like their nested twins inside its explicit `queryset=` (anonymous and staff), relation keys through a declared hop answering over the rows the viewer sees (`entriesId` `isNull` and GlobalID membership with an item's every entry hidden answering like one with none; `propertyId` `isNull` / `exact` over `EntryFilter.property`'s explicit `queryset=` against its existential nested twin), not-found-before-auth on hidden rows, private-row refetch after an authorized write, form stale-field revalidation, per-operation argument map by introspection, empty-`name` `full_clean` envelope, unresolvable relation id, form- / model- / serializer-mutation async colour on `/graphql-async/`, GET object / malformed `variables` params, dangling non-null FK (read live, and omitted from an `updateItemViaForm` as the form's own `categoryId` choice error), sync strict-UTF-8 rows, product-table statement total on cascade query count, `deleteItem` refused by an `ItemHold`'s `PROTECT` / `RESTRICT` reference, a save-time `ValidationError` from `Item.save()` / `delete()` returning the `name`-keyed envelope with nothing written on every `Item` write mutation (model, form, serializer; the model create / update / delete and the form and serializer creates also async) at an exact query count, explicit `itemId: null` on the `blank=True, null=False` hold FK keyed to `itemId`, a prefixed `ModelForm` (class-level `prefix`, `get_form_kwargs` `prefix=` over the package's data or `dict(data)` copies, re-keying `get_form`) binding every value sent and answering explicit `description` / `isPrivate` / required-`attachment` `null` as the unprefixed form does, an `Item` update whose located row is deleted after authorization answered with the `conflict` envelope by every flavor at exact statements and rolled back with the item's entries, a single-table update saving with `update_fields=None` in every flavor, the DEBUG pass-through idiom. |
| [`test_products_visibility_api.py`][test-products-visibility-api] | Generated relations enforce target visibility themselves; sync + async mounts, holder schema; optimizer-less nested connection and raw-list reverse-FK each cost `1 + N`; reverse-O2O custom-visibility holder over `QuerySet` and list roots, optimizer off and on (same data in every cell; only the planned `QuerySet`-root cell reads the card in one batched `Prefetch` carrying the hook's predicate, the other three re-check per patron; async colour); Relay id-only page in one query and `{ id name }` with decoded Relay ids clean under `strictness="raise"`; cascading-hook target blocks FK-id elision; a PLANNED relation is scoped by the plan alone (list and connection vocabularies, anonymous and staff), the resolver having stood down; and the converse, a relation the walker never planned on an execution whose `strictness="raise"` is armed anyway - the target loaded by a consumer `select_related`, re-checked per parent (non-null refusal for anonymous, served for staff, and a nullable holder key collapsing to `null` for the hidden row only); synchronous hooks that read the database on the async view - the shipped `has_perm` hooks over `allCategories` / `allItems` / `node` / `nodes` for each non-staff seeded user, and a planned child's `.exists()` hook run while a cold plan is built under a list root and a connection root - each answering the sync view's verdict. |
| [`test_joined_relation_visibility_api.py`][test-joined-relation-visibility-api] | A `select_related` JOIN on a path the optimizer plans as a visibility `Prefetch` never serves the row the target hook hides: consumer-resolver JOIN at depth one, depth two through a hooked intermediate and through a hookless one, the wildcard form, and a JOIN the root type's own hook adds (root and planned child); sync + async; staff controls served; a JOIN off every planned path kept; a hook JOIN the selection never reads kept under the `.only()` at the root, on a planned child (sync + async) and on a scalar-only (`pageInfo`-only) nested connection window. |
| [`test_combined_visibility_api.py`][test-combined-visibility-api] | A `union` / `intersection` / `difference` `get_queryset` result (one nested) served as its primary-key set on every read surface, each row equal to the uncombined equivalent hook with the optimizer on and off: root list (bare, `orderBy:`, `limit:`), root and keyset connections, reverse-FK / M2M list children, a to-one downgraded to a prefetch, nested `booksConnection` (one `ROW_NUMBER` window under the optimizer), `node` / `nodes` incl. an excluded id, related-filter derive, both cascade ends, mutation locate and payload, a hook's `Prefetch(<combined>)` and a holder `OptimizerHint.prefetch`, `strictness="raise"`, `reverse()` carried, an outer `F()` / `OrderBy` column ordering (incl. `nulls_last`) carried, a foreign-key name ordered by its key column as the combinator orders it; each shape the set cannot carry refused at the field with the `combined` defect (an outer `.values()` on a model-row surface as `projection`, a sliced one as `sliced`, or as `combined` under a nested connection), masked without `DEBUG`. |
| [`test_relation_deadline_api.py`][test-relation-deadline-api] | An already-passed `ResourcePolicy` deadline stops nested single-object relations (forward FK, reverse one-to-one, sync and async) before their lazy load, and at the resolver head when `select_related` already loaded them (async); an unarmed deadline leaves them alone. A deadline that ends after a generated mutation's write fails its forward FK and many-side payload hops and rolls the write back (sync and async), while a hop-free payload commits. |
| [`test_relations_async_api.py`][test-relations-async-api] | Generated relations lazy-load from async w/o `DJANGO_ALLOW_ASYNC_UNSAFE`; optimizer-planned prefetches of every many-side kind (incl. the no-`related_name` reverse many-to-many, cached under its query name) resolve from Django's prefetch cache in async with one statement per relation, consumer prefetches through the targets' visibility hooks, silent under `strictness="raise"`; a withdrawn badge or sponsor absent from the async wire, planned or lazy-loaded. |
| [`test_scalars_api.py`][test-scalars-api], [`test_scalars_filter_api.py`][test-scalars-filter-api], [`test_scalars_mutation_api.py`][test-scalars-mutation-api] | One specimen row per scalar wire format; `ScalarSpecimenType.id` as `Int` under `BigAutoField`; override-specimen SDL (`quantity: Float`, `note: String!`) plus resolved values; scalar filtering / ordering / related querysets, the declared `priceSpan` `RangeFilter` applied over the wire with its per-filterset scoped nested input names and one-sided / null bounds (a lone `start` as `gte`, a lone `end` as `lte`, no bound filters nothing; flat, under `not` and through the `partner` branch) and each bound cleaned as `price: { gte }` cleans it (a non-finite or past-the-cap decimal bound is `FILTER_INVALID`, flat, under `not` and through `partner` nested and flat), the declared `priceAmong` `ListFilter` (`in`) with each element cleaned the same way, the declared `signedBigSpan` / `unsignedBigSpan` `RangeFilter` and `signedBigAmong` / `unsignedBigAmong` `ListFilter` (`in`) answering a bound or element past the column's 64-bit range exactly as the generated `range` / `in` on the same column (flat and under `not`), a stored `signedBig` the column's validator refuses matched by the generated `in` exactly as by `exact`, `range`, `signedBigAmong` and `signedBigSpan` (flat and under `not`), a temporal value the database cannot bind (on SQLite an aware `occurredAt` whose UTC projection leaves years 1..9999, an aware `occurredTime`; `exact`, `gt`, an `in` member, a `range` bound, under `not` and through `partner` nested and flat) as `FILTER_INVALID` keyed to its form field, the same input filtering on PostgreSQL, a datetime through the declared `occurredDayOf` `date` transform whose date leaves years 1..9999 as the same `FILTER_INVALID` on every backend (flat, under `not` and through `partner` nested and flat), and on PostgreSQL a UTC offset the server refuses (16:00 or more either way, a fractional-second `occurredTime` offset; under `not`, an `or` arm and through `partner` too) as the same `FILTER_INVALID` where SQLite filters the datetime, django-filter's own `priceBetween` / `occurredBetween` / `occurredInBoxes` / `priceInUnderscoredBoxes` range filters and the consumer subclass `priceInFieldBoxes` (whose `field` property installs its widget) applying every bound under the keys each widget reads (`_min` / `_max`, `_after` / `_before`, a plain `MultiWidget`'s `_0` / `_1`, a consumer suffix's `__low` / `__high` or `_low` / `_high`; both / start / end / no bound, flat, inside `and` / `not` and through `partner` nested and flat), the package's `priceSpanInFieldBoxes` `RangeFilter`, whose widget a mixin's `field` override after it in the MRO installs, sent under that widget's `_low` / `_high` (flat and through the flat `partner` copy), the per-field `"__all__"` text-pattern leaves (`iExact` / `contains` / `startsWith` / `regex` / ...) only on the text column `label`, the `prefix` lookup registered on the `ScalarSpecimen.label` field instance alone published and filtering on that bag and absent from the same-class `ScalarSpecimenTag` label bag, an explicit pattern lookup on `occurredAt` / `unsignedBig` a `String` matched against the backend's text rendering on SQLite and PostgreSQL, out-of-range `__in` member drop, explicit `in: []` as the empty set on every column type (flat and inside `not` / `or` / `and`), `BigInt` bool / float / malformed decimal-string literal rejection, canonical `BigInt` input literals including int64 bounds; plain `def` roots (`allScalarSpecimens` bare / filtered / ordered, `allScalarSpecimensViaManager`) on a module-local `/graphql-async/` mount answering the sync view's rows in its statements; `ScalarSpecimen` create and update through the model, `ModelForm` and serializer flavors (sync, and async over a module-local `/graphql-async/` mount) refusing a datetime or time the database cannot store as the field's `invalid` `FieldError` (`"Enter a value the database can represent."`) with nothing written: on SQLite an aware datetime outside years 1..9999 once projected onto the connection's time zone (`TIME_ZONE`, `USE_TZ = False` and the connection's own `TIME_ZONE` cells included) and an aware time, on PostgreSQL a wall clock in the session time zone outside years 1..9999 and a UTC offset the server refuses (16:00 or more either way, a time's fractional-second offset), while DRF's own `overflow` answer stands and a value the flavor stores is written; a `SplitDateTimeField` over `occurredAt` (the `SplitForm` pairs: unprefixed, under the form's prefix `specimen` and beside a `get_form`'s own `specimen-<name>` copy) writing the datetime sent on create and update and keeping it when omitted. |
| [`test_uploads_api.py`][test-uploads-api] | `Upload` over multipart: file / image output objects, a file / image column dropped by `Meta.fields` or `Meta.exclude` absent from the type, filesystem-path opt-in, model + form write paths, `updateMediaSpecimen` omit / replace / explicit `null` on the required file and its optional partial-input `Upload`, its raw-pk `id:` (non-Relay primary; uncoercible / out-of-range / missing pk each the not-found `FieldError`), storage degradation (unpathable backend, vanished file, corrupt image, `SuspiciousFileOperation` not swallowed). |
| [`test_globalid_naming_api.py`][test-globalid-naming-api] | `type`-strategy GlobalIDs under a type-renaming `NameConverter`: fakeshop's composed `Query` / `Mutation` re-finalized under `RELAY_GLOBALID_STRATEGY = "type"` and served by an `Api`-prefixing converter on a holder mount - emitted ids carry the published name (root edge, nested relation), `node` / `nodes` / the typed `genre(id:)` refetch them (per-table query counts), every mutation flavor writes by them (lookup id, forward key, many-to-many), every GlobalID filter shape accepts them (own id, `RelatedFilter` hop, relation keys), the default spelling is refused on each surface, and a typed mismatch (single and batch) names published types; holder schemas for the `Meta.globalid_strategy = "type"` spelling with a converted name equal to another real type's name, an unpublished Relay type keeping its own spelling, a relation filter refusing a slot the schema publishes for another type, and a shadow-installed `type` child emitting its published name. |
| [`test_input_shapes_api.py`][test-input-shapes-api] | Relation-id and payload-slot shapes of generated write inputs: a forward key is `ID!` to a Relay primary (`ItemInput.categoryId`) and the raw `Int!` to a plain one (`BookInput.shelfId`, no `shelf` field), a many-to-many is an optional `[ID!]` to a Relay primary (`BookInput.genres`) and `[Int!]` to a plain one (`createShelf`'s `altBranches`), a Relay primary's payload (`CreateBookViaCustomInputPayload`) carries a nullable `node` with no `result` and a plain primary's (`createShelf`) a nullable `result` with no `node`, each beside `errors: [FieldError!]!`. |
| [`test_auth_api.py`][test-auth-api] | `login` / `logout` / `register` / `me` on the shipped `AllowAny` surface, plus a `/graphql-test/` holder arming optimizer `strictness="raise"` over the same mutations: session rotation branches, collapsed failure envelope incl. backend `PermissionDenied`, password validators, non-string `username` rejected at validation, sessionless middleware stack refused by name. |
| [`test_keyset_api.py`][test-keyset-api] | `Meta.cursor_field` keyset pagination: value cursors surviving inserts / deletes, nested uniform seeks, tamper rejection, permission-aware replay, cursor survives `SECRET_KEY` rotation via `SECRET_KEY_FALLBACKS`, nested window partitioned and counted over the viewer's rows, opaque deterministic cursors; a target `get_queryset` order paged nested (reverse FK / M2M, batched and single-parent, sync and async) under that order's own cursor vocabulary, byte-identical cursors across root / planned window / per-parent path, one relation name windowed under two root fields keeping each window's vocabulary, the unanchorable-order keyset error (an expression, `"?"`, `Random()`, a relation name under a related `Meta.ordering`) nested as at the root (`strictness="raise"` included), a random `Meta.ordering` on the target leaving the declared `cursor_field` window planned, a random hook order on an offset relation an unplanned per-parent access `strictness="raise"` reports, and a malformed cursor on a planner-refused relation under `strictness="raise"`; a target `get_queryset` `extra(order_by=...)` order (a field, a descending field, the child's own `table.column`, a foreign key's raw column, a joined table's column, a quoted table name, each as written and `.reverse()`'d) paging every row once forward and backward at the root on offset and keyset connections (one statement a page), the planned window serving the per-parent page (one batched statement against one per parent), a raw `table.column` term compiled into every statement as Django compiles it, a random `extra` order keeping the pk tiebreaker, the foreign-key and raw terms the keyset refusal root and nested, and the async root and window paging under it. |
| [`test_connection_pagination_api.py`][test-connection-pagination-api] | Pagination error containment on connections; `Meta.connection` `totalCount` opt-in gating + inherited connection SDL description; sidecar `filter:` / `orderBy:` argument presence on shipped connections; malformed post-`OrderSet` result matrix over both pipelines on the field shape each belongs to - `apply_sync` on the shipped `allLibraryGenresConnection` (sync public resolver) over `/graphql/`, each row = exact rejection + `library_genre` query cost, and `apply_async` on a test-local `GenreType` connection field whose `async def` consumer resolver is the only shape that selects the async pipeline, served over a module-owned `/graphql-async/` mount, each row = exact rejection + no raw exception text + a sentinel proving the override ran - each with a `super()` pass-through positive control; the async arm mirrors the sync shapes (evaluated, materialized-list, none, projection, wrong-model, sliced, a `union(all=True)` combination its primary-key set cannot represent, routing-rewritten-in-place, malformed-deferred-filter; a combined result it can represent is served) and answers the sync-only `awaitable-in-sync` row with two twins, `non-awaitable` and `residual-awaitable`, the second also reading the refused awaitable's disposal (closed coroutine, body never run); the whole async matrix is mirrored for the `FilterSet` arm (`GenreFilter.apply_async`) on a request carrying a real `filter:` argument, the same defect shapes, sentinel, disposal read and typed messages, with a pass-through control asserting the filtered page; offset cursor decoding under the default error policy over every source shape - list / tuple consumer resolvers sync and async under a three-row `max_page_size`, a generator resolver, an async `QuerySet` resolver (module-owned `/graphql-cursor/` and `/graphql-cursor-async/` mounts) and the shipped root `allLibraryGenresConnection` - where a negative, malformed, non-canonical or `sys.maxsize` `after` / `before` is one exact message (on the shipped root and on the planned nested `booksConnection` window under it, where the malformed shape plans no window, issues no `library_book` statement and is the nested field's own error at its `errors[].path`), and index 0, a minted cursor, `after: ""` and `sys.maxsize - 1` (past the end, root `QuerySet` and list resolver) still page; an `after` at `sys.maxsize - 1` or at the index whose page would end on `SliceMetadata`'s `sys.maxsize` sentinel serves the page an ordinary past-the-end cursor serves under `first: N`, `last: 0` or no page argument (`first: 0` / `2` / cap, `last: 0`, none; with or without `before: ""`) on the root `QuerySet`, list, tuple and generator resolvers, the async list and `QuerySet` resolvers and a nested per-parent `booksConnection` (one `library_book` statement per parent), an `after` + `before` interval there pages like any interval, and a page bounded only by a `sys.maxsize` cap (`/graphql-cursor-unbounded/`) serves every row; each `first` / `last` bound message is exact on both colours; and a row failing to hydrate (root, and nested under an offset root through the planned window and the per-parent pipeline, sync and async, each beside its unpatched control, the two nested paths told apart by `library_book` statement count), a consumer generator source raising `KeyError` / `ValueError`, or a source whose sliced-state read fails (a project `QuerySet` whose `query` raises a project `KeyError` subclass, or a related manager on an id its deferred relation filter cannot use; each exception's class name absent from the body and its original read back from the policy's server log) reaches the client masked (policy message + `correlationId`, no exception text), never as a pagination message; keyset negative / over-cap `first` are exact messages. |
| [`test_list_field_api.py`][test-list-field-api] | Sync `DjangoListField` argument surface: ordered offset pages, visibility before order, cap + error matrix, converter naming, the effective-ordering precedence behind the positive-offset guard (random model default rejected, superseded dormant random accepted, each with its control), the unreadable-leaf rejections (`RawSQL`, a bare `Func`, a `Subquery`, and a fragment boxed inside a predicate's `__in` sequence) against their conditional-order control, the spelling-independence tables (one ordering, one verdict, written directly or held by an annotation: transform chains after an alias or a column, lookups the registry picks for the operand and value, the `isnull` a `None` compiles to, the `isnull` a negation adds over a nullable or promoted join, date arithmetic, a comparison over a project field, an `F` naming a shadowing `extra` alias, approved nodes carrying their own template, operator or output field, and the seal answering first for a resolved project class), the evaluated-resolver re-query pins (root, zero-width, per parent, warm prefetch), malformed post-`OrderSet` result matrix (each row = exact rejection + query cost), hostile normalized-term rejection, legacy-reference byte-parity oracle under the same field name, consumer-context isolation for list field + ordered connection, the policy-authority boundary (a sibling field writing every policy object a resolver can reach, and the request after it). |
| [`test_list_field_async_api.py`][test-list-field-async-api] | Async colour of the same: safe queryset completion, optimizer preservation, iterable cleanup including a deadline the resolver ends across its own await, closing a source it never advanced, the offset guard's effective-ordering precedence witnessed at the compiler (an executor thread's connection is invisible to `CaptureQueriesContext`), the async twins of the spelling-independence tables and the evaluated-resolver re-query pins, async-only malformed shapes (non-awaitable result, residual awaitable), published-name reporting, post-`OrderSet` routing pin, consumer-context rows, the policy-authority boundary written across an await, and the nested synchronous operation an async request can start - the one shape where the ambient event loop and the GraphQL executor disagree, refused on the wire rather than answered with a generic completion failure. |
| [`test_optimizer_auto_api.py`][test-optimizer-auto-api], [`test_single_parent_fastpath_api.py`][test-single-parent-fastpath-api] | Nested-fetch strategy selection; single-parent windowed-prefetch fast path incl. the keyset-seek page keeping its window. |
| [`test_multi_db.py`][test-multi-db] | Behind `FAKESHOP_SHARDED=1`: resolver isolation on `shard_b`, deep relational leaf's hop subqueries pinned to `queryset.db`, post-`OrderSet` routing attestation (four list-field rejections + the accepted identity-preserving row, plus the connection-field alias rejection), multi-DB debug capture. |
| [`test_transport_api.py`][test-transport-api] | Transport boundary: middleware, security headers, hostile `Host`, CSRF directions, `Vary`, exact routing, per-mount IDE / GET controls, cumulative request-body cap across sync / async / multipart, misconfigured cap fails on GET too, async + multipart strict-UTF-8 rows, async view hands a plain sync resolver an evaluated session actor (anonymous / non-staff / staff). |
| [`test_error_policy_api.py`][test-error-policy-api] | Production error policy over the wire, including an entry that resolves to the masking authority refusing the request with the configuration code instead of masking it. |
| [`test_extension_isolation_api.py`][test-extension-isolation-api] | What one operation's extensions may be answered from: every write spelling aimed at the box an accepted slotted entry is held in plus a write to a stateful accepted factory (bound and masking both still enforced on the NEXT request, over the sync and async views), a consumer extension's own operation leaving the request its published optimizer plan, a factory resolving to an enforcement authority refusing every request - valid, aliased and malformed alike, and under an `operationName` that is absent, punctuated, empty or non-ASCII, over the sync and async views - with the stable configuration code in a JSON envelope that echoes nothing back, while its pre-parse token and depth ceiling still rejects an oversized or deeply nested document under any of those names, a factory resolving to anything but an ordinary extension instance (one that raises, returns a non-extension or a class, returns an object whose `__class__` claims an ordinary extension or an authority, or returns an authority subclass or hybrid) refusing every request with the configuration code and the reason in the package log only, and a worker that outlived its request bounded and publishing for itself over the async mount. |
| [`test_schema_composition_api.py`][test-schema-composition-api] | Composed project schema over HTTP: one type per contributing app by introspection, reverse relation resolved under the anonymous cascade. |
| [`test_resource_policy_api.py`][test-resource-policy-api] | Every `ResourcePolicy` bound, against mounts each narrowing one family of bounds; malformed document keeps the parser's own diagnostic / is rejected on size first; the pre-parse token bound charged over the whole request document with its named-operation control; an entry-declared `max_list_rows` as the bound the request is held to; a many-side relation whose manager returns a `QuerySet` subclass, bounded on both transports with Django's own manager as the control; sync/async parity row; streamed multipart rows. |
| [`test_debug_extension_api.py`][test-debug-extension-api], [`test_debug_toolbar_api.py`][test-debug-toolbar-api] | `DjangoDebugExtension` on a probe mount; `DebugToolbarMiddleware` across GraphQL / panel / pass-through routes under `DEBUG=True` override: bridge script + handle on the IDE page, named-operation panel payload (`TemplatesPanel` skip, `RedirectsPanel` `title: null`), `Content-Length` refresh after `CommonMiddleware`, introspection skip, `Content-Encoding` early-out via an inner stamp middleware, untagged JSON holder view left untouched. |
| [`test_mutation_atomicity.py`][test-mutation-atomicity] | Generated mutation's transaction spans response completion: unserializable payload → rollback, not commit behind `data: null`; async colour of the same on `/graphql-async/`. |
| [`test_client_api.py`][test-client-api] | Request-driving half of the `TestClient` family's coverage. |
| [`test_kanban_api.py`][test-kanban-api], [`test_kanban_mutations_api.py`][test-kanban-mutations-api], [`test_glossary_api.py`][test-glossary-api] | Docs-as-data apps' read + write surfaces (an illegal `setCardStatus` transition, a `pre_save` signal `ValidationError` under `perform_mutate`, is the exact `"__all__"` envelope, sync and async); the board is also the one example graph whose child model declares a single non-pk `Meta.ordering` column, so the nested `decisionsConnection` window is where the deterministic `ORDER BY <order column>, pk` is read off captured SQL for a two-parent batch, and, under the async `node` root over a module-local `/graphql-async/` mount, where its filter refuses a `decidedAt` bound the database cannot bind as `FILTER_INVALID` (year 0 on SQLite, a UTC offset of 16:00 on PostgreSQL); on the same mount the plain `def` root `allCards` (bare with a planned relation, related filter, order) answers the sync view's rows in its statements. |

Outside this dir: [`../tests/`][fakeshop-tests] = project-level rows (urls, settings guard, schema export, `inspect_django_type`); `../apps/<app>/tests/` = that app's in-process rows; [`../../../tests/`][tests-dir] = package tier, one file per module.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[contributing]: ../../../CONTRIBUTING.md
[start]: ../../../START.md

<!-- docs/ -->
[docs-readme-testing]: ../../../docs/README.md#testing-graphql-endpoints
[glossary-testclient]: ../../../docs/GLOSSARY.md#testclient
[tree-tests]: ../../../docs/TREE.md#test-layout

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-failability]: ../../../docs/builder/BUILD.md#failability-proofs-prove-the-test-can-fail

<!-- django_strawberry_framework/ -->
[testing-client]: ../../../django_strawberry_framework/testing/client.py
[testing-relay]: ../../../django_strawberry_framework/testing/relay.py

<!-- tests/ -->
[tests-auth-mutations]: ../../../tests/auth/test_mutations.py
[tests-ci-governance]: ../../../tests/test_ci_governance.py
[tests-conftest]: ../../../tests/conftest.py
[tests-connection]: ../../../tests/test_connection.py
[tests-consumers]: ../../../tests/test_consumers.py
[tests-dir]: ../../../tests/
[tests-relay-node-field]: ../../../tests/test_relay_node_field.py
[tests-routers]: ../../../tests/test_routers.py
[tests-soft-dep]: ../../../tests/_soft_dependency.py
[tests-testing-client]: ../../../tests/testing/test_client.py
[tests-views]: ../../../tests/test_views.py

<!-- examples/ -->
[conftest]: conftest.py
[fakeshop-readme]: ../README.md
[fakeshop-tests]: ../tests/
[graphql-client]: ../graphql_client.py
[lib-schema]: ../apps/library/schema.py
[products-services]: ../apps/products/services.py
[schema-reload]: ../schema_reload.py
[test-auth-api]: test_auth_api.py
[test-client-api]: test_client_api.py
[test-combined-visibility-api]: test_combined_visibility_api.py
[test-connection-pagination-api]: test_connection_pagination_api.py
[test-debug-extension-api]: test_debug_extension_api.py
[test-debug-toolbar-api]: test_debug_toolbar_api.py
[test-error-policy-api]: test_error_policy_api.py
[test-extension-isolation-api]: test_extension_isolation_api.py
[test-globalid-naming-api]: test_globalid_naming_api.py
[test-glossary-api]: test_glossary_api.py
[test-kanban-api]: test_kanban_api.py
[test-kanban-mutations-api]: test_kanban_mutations_api.py
[test-input-shapes-api]: test_input_shapes_api.py
[test-joined-relation-visibility-api]: test_joined_relation_visibility_api.py
[test-keyset-api]: test_keyset_api.py
[test-library-api]: test_library_api.py
[test-library-inheritance-api]: test_library_inheritance_api.py
[test-library-shapes-api]: test_library_shapes_api.py
[test-list-field-api]: test_list_field_api.py
[test-list-field-async-api]: test_list_field_async_api.py
[test-multi-db]: test_multi_db.py
[test-mutation-atomicity]: test_mutation_atomicity.py
[test-optimizer-auto-api]: test_optimizer_auto_api.py
[test-products-api]: test_products_api.py
[test-products-visibility-api]: test_products_visibility_api.py
[test-relation-deadline-api]: test_relation_deadline_api.py
[test-relations-async-api]: test_relations_async_api.py
[test-resource-policy-api]: test_resource_policy_api.py
[test-scalars-api]: test_scalars_api.py
[test-scalars-filter-api]: test_scalars_filter_api.py
[test-scalars-mutation-api]: test_scalars_mutation_api.py
[test-schema-composition-api]: test_schema_composition_api.py
[test-single-parent-fastpath-api]: test_single_parent_fastpath_api.py
[test-transport-api]: test_transport_api.py
[test-uploads-api]: test_uploads_api.py

<!-- scripts/ -->
[prove-failability]: ../../../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->
