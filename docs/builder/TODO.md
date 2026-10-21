# Outstanding issues: to-do list

Every open issue found outside the bug-hunt and DRY trackers: the `docs/bug_hunt/pbugs.md` inspection (2026-10-21),
build-plan leftovers, and CI and test gaps. Each one is verified, fixed at the root, then deleted from this file in the
commit that lands it. The bug-hunt findings stay in `docs/bug_hunt/bug_hunt-0_0_15_2.md`; only their beta triage is
recorded here.

Progress: 28 to do.

## To do: fix before beta

- [ ] 2. Under ASGI, a default root `DjangoConnectionField` or a nested relation connection whose `get_queryset` hook
  touches the database (`user.has_perm(...)`, as fakeshop `CategoryType` does) fails with a masked "unexpected error":
  `django_strawberry_framework/connection.py::_pipeline_sync` always runs the sync pipeline on the loop, so
  `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` raises `SynchronousOnlyOperation`, and an
  `async def` hook raises `SyncMisuseError`. A root field can switch to an `async def resolver=`; a nested connection has
  no recourse except `relation_shapes = {"x": "list"}`. `DjangoListField` already picks
  `_execute_queryset_pipeline_async` per call, so lists work where connections fail. Confirmed live over
  `AsyncDjangoGraphQLView` (`allCategories`, `allItems`)
- [ ] 4. A model whose `delete()` returns `None` (soft-delete mixins such as model_utils' `SoftDeletableModel`) can
  never be deleted through `DjangoMutation`: `django_strawberry_framework/mutations/resolvers.py::_delete_or_field_errors`
  unpacks `_total, per_model = instance.delete()` and raises `TypeError` as a top-level error (the write rolls back).
  Fix: tolerate a non-tuple return
- [ ] 5. The ModelForm flavor stores an explicit `null` on a non-null `BooleanField` as `false` and reports success
  (`isPrivate: null` on a `True` row stored `False`, `errors: []`), where the model flavor returns a field-keyed error:
  `django_strawberry_framework/utils/write_values.py::decode_provided_fields` hands `None` to the bound form, which
  cleans it to the empty value. Fix, or decide that form-flavor `null` keeps form semantics and document it
- [ ] 6. On Postgres an embedded NUL (`\u0000`) in a text value escapes as a top-level error with `data: null`:
  `django_strawberry_framework/utils/write_values.py::unencodable_text_error` states that NUL passes, a model
  `TextField` has no validator, and nothing in the package maps psycopg's `DataError` ("PostgreSQL text fields cannot
  contain NUL (0x00) bytes"). Reached by model-flavor create / update, auth login / register, text-pk `node(id:)` and
  NUL inside `JSON` values (jsonb); ModelForm, serializer and `FilterSet` text are shielded by their validators. The
  write rolls back. The psycopg half is confirmed; the end-to-end shape needs a Postgres run, and no Postgres test sends
  NUL through a model write

## Beta triage of `bug_hunt-0_0_15_2.md`

From the full entries, 2026-10-21. Item numbers are that file's.

- Fix before beta: 158 (a consumer `.only()` is never widened under a mutation: 77 statements against 2, and the
  re-fetch fails on async), 160 (confirmed live: `range: {start: "10.0000"}` and `range: {end: "100.0000"}` on
  `priceSpan` each return no rows; both bounds return the right row), 161 (django-filter 26.1's `RangeWidget` reads
  `_min` / `_max` while the package writes `_0` / `_1`, so a declared upstream `django_filters.RangeFilter` applies no
  bounds; the package's own `RangeFilter` works; not run end to end), 197 (decide the narrowing contract), 200, 241,
  249, 290, 291, 292, and the 204 disclosure decision
- Decide (either answer is fine for beta): 68, 85, 135
- Document for beta: 26, 77, 84, 94, 108, 162, 163 (docs only), 165 (test gap), 190, 198, 199, 216, 217, 220, 229, 234,
  236, 269, 271, 272, 276, 278, 279, 281, 294, 295, the Postgres `ArrayField` rows 45-47, and upstream 205 and 219
- Release paperwork: the "CHANGELOG entry for item N" rows (maintainer edits) and the decisions 114, 201, 242, 262
- Not beta-relevant: the `workspace.py` / script tooling rows and internal-doc prose rows

## To do: document for beta

- [ ] 7. The ModelForm flavor ignores an explicit `null` on an optional `FileField` (Django form `None` means "no
  change"), so `attachment: null` returns success with the file unchanged; a client likely means "clear"
- [ ] 8. A primary / replica router: on a vendor other than PostgreSQL or SQLite every mutation with
  `permission_classes` fails with `ConfigurationError`, because
  `django_strawberry_framework/utils/permissions.py::resolve_auth_aliases` returns the read alias and
  `django_strawberry_framework/utils/write_transaction.py::_enforce_read_only_barrier` fails closed; on PostgreSQL each
  such mutation opens a read-only transaction on the replica per call; a permission class reading an alias outside the
  auth set (a Session or custom auth model on its own alias) is refused. All loud; the message names the fix
- [ ] 9. `django_strawberry_framework/utils/write_transaction.py::assert_no_target_drift` compares mutable custom values
  by reference (`current is not value and current != value`), so an in-place mutation of a GeoDjango geometry,
  `memoryview` or custom `to_python` object by a hostile hook is not detected (serializer flavor only)
- [ ] 10. `django_strawberry_framework/utils/write_values.py::raw_choice_value` unwraps choice enums one level only, so a
  nested `ArrayField(ArrayField(choices))` keeps enum members in the inner lists (Postgres only)
- [ ] 11. `django_strawberry_framework/utils/querysets.py::pks_all_present` compares `str()` forms, so a case-insensitive
  pk (MySQL collation, citext) or a `Decimal`-keyed target reads a valid related row as not found (fails closed)
- [ ] 12. `copy.copy` / `copy.deepcopy` of a `ChannelsRequestAdapter` raises `RecursionError`: `__getattr__` reads
  `self._request` before it exists (`django_strawberry_framework/utils/permissions.py`); reachable from consumer code only
- [ ] 13. `django_strawberry_framework/utils/sessions.py::scope_singleton` reads `scope.get(key)`, where
  `utils/permissions.py` deliberately avoids `Mapping.get`; a scope subclass overriding `get` could hand back a forged
  `ConnectionActorState` (hostile scope only)
- [ ] 14. `django_strawberry_framework/auth/sessions.py::uses_signed_cookie_sessions` is a subclass check on
  `SignedCookieSessionStore`, so a custom client-side store is treated as server-side and WebSocket `logout` is allowed
  but cannot revoke the browser cookie; an unlisted import-time error from the engine module escapes raw from
  `logout_supported` (revalidation is unaffected)
- [ ] 15. The default `max_collection_cost` is `1_000_000_000`, so a depth-4 nest at `first: 100` passes admission; there
  is no aggregate scalar-bytes bound (65 KB per scalar times up to 5000 nodes; Django's body-size limit is the real cap);
  a released `memoryview` or hostile container raises raw from
  `django_strawberry_framework/extensions/resource_policy.py::_charge_leaf` (in-process only)
- [ ] 16. Under async, `size`, `width`, `height`, `url` and `path` on file and image fields do blocking storage I/O on the
  loop (`django_strawberry_framework/types/resolvers.py::file_resolver` itself touches no storage); remote storage
  blocks the event loop
- [ ] 17. A configured `relay_max_results` above 100 is silently clamped to the policy's `max_page_size` (default 100)
  by `django_strawberry_framework/utils/connections.py::resolve_relay_max_results`; by design, but undocumented
- [ ] 18. `contains` is case-insensitive for ASCII on SQLite and case-sensitive on Postgres, and non-ASCII `i`-lookup
  folding differs (Django semantics; the package emits no LIKE of its own)
- [ ] 19. `django_strawberry_framework/_strawberry_patches.py::_validate_upstream_shape` and
  `django_strawberry_framework/_django_patches.py::_validate_upstream_shape` pin exact `inspect.getsource` text,
  comments included, and abort startup on a mismatch: a comment-only upstream edit, or a source-less install, stops the
  app booting until `APPLY_UPSTREAM_PATCHES` changes. Every published release in range matches today
- [ ] 20. The `lru_cache`s keyed on model classes (`_classify_path_cached` and siblings) are not cleared by registry
  teardown; no stale answer was shown, but a test that monkeypatches `_meta.pk` could poison them

## To do: CI and test gaps

- [ ] 21. No CI step or pre-commit hook runs `makemigrations --check`; no drift exists today under `config.settings`,
  `config.test_settings` or `FAKESHOP_SHARDED=1`
- [ ] 22. Nothing shuffles test order: pytest-randomly is not installed, so the order-independence rule has no enforcer.
  Two shuffled module orders over ten registry-heavy modules (2106 passed each) found no dependence
- [ ] 23. `postgres.yml` runs only on dispatch and weekly, on Python 3.14 and the latest Django; there is no Postgres row
  for the Django 5.2 floor, psycopg2, or more than one alias
- [ ] 24. No test uses two Postgres connections to prove the `FOR UPDATE` lock blocks a concurrent writer (the
  `conflict` tests delete on the same connection); under READ COMMITTED the visibility subquery is not re-evaluated
  after a lock wait, so a row hidden by a concurrent commit may still be located and written
- [ ] 25. The real-server `SET TRANSACTION READ ONLY` barrier arm of
  `django_strawberry_framework/utils/write_transaction.py::_enforce_read_only_barrier` runs only against a fake
  connection; the real-server test is skipped off SQLite
- [ ] 26. Local runs read `config.settings` (`.envrc`) while pytest reads `config.test_settings`; the only delta is the
  MD5 password hasher (372 auth and transport tests pass under both)
- [ ] 27. No live request exercises a composite primary key, and no SQLite fixture has a `db_column=` rename (one exists
  in the Postgres tier only)
- [ ] 28. The sharded fakeshop test is unverified until a `FAKESHOP_SHARDED=1` row of `django.yml` runs on the current
  head

## To do: tooling

- [ ] 29. `scripts/check_citations.py` does not check a spec citation written in comma form ("spec-037, Decision 3"),
  only the forms it parses today

## Waiting on you

- [ ] 30. `AGENTS.md` mandates repo-wide write-mode `ruff`; `docs/builder/worker-2.md` step 5 tells workers to scope it to
  the files the pass touched ("never on `.`"). `START.md` "Session rules you will forget" also states the repo-wide
  form, and the role files defer to `AGENTS.md`, so the scoping instruction is inert. Recommended: `AGENTS.md` and
  `START.md` adopt touched-path `ruff`, matching the explicit-path rule for `check_trailing_commas.py` under concurrent
  sessions

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
