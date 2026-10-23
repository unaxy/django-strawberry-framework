# Outstanding issues: to-do list

Every open issue found outside the bug-hunt and DRY trackers: the `docs/bug_hunt/pbugs.md` inspection (2026-10-21),
build-plan leftovers, and CI and test gaps. Each one is verified, fixed at the root, then deleted from this file in the
commit that lands it. The bug-hunt findings stay in `docs/bug_hunt/bug_hunt-0_0_15_2.md`; only their beta triage is
recorded here.

Progress: 20 to do.

Every item below was re-verified at HEAD on 2026-10-22 by one research agent per item; each "Research" sub-bullet is
that pass's finding and recommended landing.

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

- [ ] 10. `django_strawberry_framework/utils/write_values.py::raw_choice_value` unwraps choice enums one level only, so a
  nested `ArrayField(ArrayField(choices))` keeps enum members in the inner lists (Postgres only)
  - Research: narrower than stated. The generated input never produces it (a nested `ArrayField` is a schema-build
    `ConfigurationError`); only a consumer `list[list[Enum]]` override reaches it. The docstring and a test already pin
    "one level only". A recursive unwrap would walk every JSON value. Document in spec-001's element-wise paragraph.
    Size S
- [ ] 11. `django_strawberry_framework/utils/querysets.py::pks_all_present` compares `str()` forms, so a case-insensitive
  pk (MySQL collation, citext) or a `Decimal`-keyed target reads a valid related row as not found (fails closed)
  - Research: reproduced (`Decimal` `"1.5"` against a stored `1.50`; `NOCASE` `"ABC"` against `abc`). Wider than stated:
    `django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids` also indexes by `str(pk)`, and a
    single relation id works while the same id in an M2M list fails. `to_python` fixes `Decimal` only, not collation.
    Document in README "Writing data" ("Four behaviors are easy to trip over"). A real fix is M-L. Size S
- [ ] 12. `copy.copy` / `copy.deepcopy` of a `ChannelsRequestAdapter` raises `RecursionError`: `__getattr__` reads
  `self._request` before it exists (`django_strawberry_framework/utils/permissions.py`); reachable from consumer code only
  - Research: reproduced for copy, deepcopy and pickle. Fix instead of documenting: `if name == "_request": raise
    AttributeError(name)` at the top of `__getattr__`, plus a round-trip test in `tests/utils/test_permissions.py`.
    Optional: refuse dunder names too. Size S
- [ ] 13. `django_strawberry_framework/utils/sessions.py::scope_singleton` reads `scope.get(key)`, where
  `utils/permissions.py` deliberately avoids `Mapping.get`; a scope subclass overriding `get` could hand back a forged
  `ConnectionActorState` (hostile scope only)
  - Research: holds, but `scope.get` also appears in `consumers.py` (the revalidation `user` read and the window cache)
    and `auth/sessions.py`, so fixing this one site is partial. A hostile scope is in-process consumer code. Decide:
    document the trust boundary in the `scope_singleton` docstring (S) or sweep every site through one helper (M)
- [ ] 14. `django_strawberry_framework/auth/sessions.py::uses_signed_cookie_sessions` is a subclass check on
  `SignedCookieSessionStore`, so a custom client-side store is treated as server-side and WebSocket `logout` is allowed
  but cannot revoke the browser cookie; an unlisted import-time error from the engine module escapes raw from
  `logout_supported` (revalidation is unaffected)
  - Research: both halves reproduced. README already states the first half; the raw import error is undocumented (an
    engine that cannot import also breaks `SessionMiddleware`). Add it to the `uses_signed_cookie_sessions` docstring
    and one clause in README. Size S
- [ ] 15. The default `max_collection_cost` is `1_000_000_000`, so a depth-4 nest at `first: 100` passes admission; there
  is no aggregate scalar-bytes bound (65 KB per scalar times up to 5000 nodes; Django's body-size limit is the real cap);
  a released `memoryview` or hostile container raises raw from
  `django_strawberry_framework/extensions/resource_policy.py::_charge_leaf` (in-process only)
  - Research: correction: the real cap is the package's `MAX_REQUEST_BODY_BYTES` (default 1 MiB), not Django's
    limit. The docstring, spec-047 and the glossary already cover the cost bound; README's "Production security
    profile" mentions neither bound. Add a paragraph there and "per scalar, not aggregate" to the `max_scalar_bytes`
    entry of `django_strawberry_framework/resource_policy.py::ResourcePolicy`. Raw raise: reproduced; decide document
    or typed rejection. Size S
- [ ] 16. Under async, `size`, `width`, `height`, `url` and `path` on file and image fields do blocking storage I/O on the
  loop (`django_strawberry_framework/types/resolvers.py::file_resolver` itself touches no storage); remote storage
  blocks the event loop
  - Research: reproduced: the subfield resolvers in `types/converters.py` run on the loop thread; `width` / `height`
    open and decode the image even on local storage. Document in README "Uploads" and the `DjangoFileType` glossary
    body (S), or decide a loop-guarded thread hop in `_safe_file_attr` (M)
- [ ] 17. A configured `relay_max_results` above 100 is silently clamped to the policy's `max_page_size` (default 100)
  by `django_strawberry_framework/utils/connections.py::resolve_relay_max_results`; by design, but undocumented
  - Research: reproduced (500 resolves to 100 under the default policy, 500 with `max_page_size=1000`). The ceiling is
    documented on `ResourcePolicy`, but the `strawberry_config` glossary entry's own example (`relay_max_results=200`)
    has no effect under defaults. Add the `min(...)` sentence there, or change the example to 50. Size S
- [ ] 18. `contains` is case-insensitive for ASCII on SQLite and case-sensitive on Postgres, and non-ASCII `i`-lookup
  folding differs (Django semantics; the package emits no LIKE of its own)
  - Research: reproduced on SQLite (`contains` matches across ASCII case; an accented `icontains` misses the other
    case). Nothing documents it. Add a "Text matching is the database's" paragraph to README "Filtering with
    `FilterSet`" and the `FilterSet` glossary entry; confirm `EnumLookupFilter` also defers to Django first. Size S
- [ ] 19. `django_strawberry_framework/_strawberry_patches.py::_validate_upstream_shape` and
  `django_strawberry_framework/_django_patches.py::_validate_upstream_shape` pin exact `inspect.getsource` text,
  comments included, and abort startup on a mismatch: a comment-only upstream edit, or a source-less install, stops the
  app booting until `APPLY_UPSTREAM_PATCHES` changes. Every published release in range matches today
  - Research: reproduced (a comment-only edit and a `.pyc`-only install both raise). Fail-loud is the design: document
    in the "Upstream patches" glossary kill-switch paragraph. Also fix the stale "verbatim at strawberry-graphql 0.322.2
    and 0.324.0" comment in `_strawberry_patches.py` (0.327.7 matches). Size S
- [ ] 20. The `lru_cache`s keyed on model classes (`_classify_path_cached` and siblings) are not cleared by registry
  teardown; no stale answer was shown, but a test that monkeypatches `_meta.pk` could poison them
  - Research: reproduced (a cached classification survives `registry.clear()`). The model-keyed caches are
    `django_strawberry_framework/utils/relations.py::_classify_path_cached`, `_path_traverses_to_many_cached` and
    `django_strawberry_framework/permissions.py::_edge_plan`. Fix instead of documenting: `register_subsystem_clear`
    for `_edge_plan`; the relations clear must register lazily or from `filters` / `orders` (import cycle through
    `utils/__init__.py`). Update the `tests/conftest.py` caveat. Size S

## To do: CI and test gaps

- [ ] 21. No CI step or pre-commit hook runs `makemigrations --check`; no drift exists today under `config.settings`,
  `config.test_settings` or `FAKESHOP_SHARDED=1`
  - Research: `makemigrations --check --dry-run` passes under all three. Add a `lint`-job step in `django.yml` running
    all three, and a path-scoped pre-commit hook (default settings, `pass_filenames: false`); list both in START.md's
    gates. Size S
- [ ] 22. Nothing shuffles test order: pytest-randomly is not installed, so the order-independence rule has no enforcer.
  Two shuffled module orders over ten registry-heavy modules (2106 passed each) found no dependence
  - Research: decide. A: install it, shuffling everywhere (it reseeds Faker and `random`, so `seed_data` changes per
    seed; M). B (recommended): install it off by default (`-p no:randomly` in `pytest.ini`) with a scheduled shuffle
    job that prints the seed (S). C: keep as-is. Then name the enforcer in START.md's order-independence bullet
- [ ] 23. `postgres.yml` runs only on dispatch and weekly, on Python 3.14 and the latest Django; there is no Postgres row
  for the Django 5.2 floor, psycopg2, or more than one alias
  - Research: add matrix rows: a 3.10 / `Django==5.2.16` floor row (pins as in `django.yml`), a psycopg2 row (uninstall
    psycopg, install `psycopg2-binary`), and a sharded row (`settings.py` must define `shard_b` on Postgres when both
    env vars are set; "mutually exclusive" is not enforced today). About 3.4 times the runner minutes. Decide the rows
    and shards. Size M
- [ ] 25. The real-server `SET TRANSACTION READ ONLY` barrier arm of
  `django_strawberry_framework/utils/write_transaction.py::_enforce_read_only_barrier` runs only against a fake
  connection; the real-server test is skipped off SQLite
  - Research: correction: the real-server test runs on SQLite only, and no Postgres real-server test exists. Add a `pg`
    sibling in `tests/rest_framework/test_resolvers.py`: a second alias on the test database and a real (not TEMP)
    table; `INSERT` fails inside `authorization_phase` and succeeds after it. Size S
- [ ] 26. Local runs read `config.settings` (`.envrc`) while pytest reads `config.test_settings`; the only delta is the
  MD5 password hasher (372 auth and transport tests pass under both)
  - Research: close with two wording fixes and no test: the `.envrc` comment ("Match pytest.ini/example-project
    defaults" is false) and spec-042, which says `pytest.ini` sets `config.settings`. Size S
- [ ] 27. No live request exercises a composite primary key, and no SQLite fixture has a `db_column=` rename (one exists
  in the Postgres tier only)
  - Research: new finding: a `DjangoType` with `fields = "__all__"` over a `CompositePrimaryKey` model raises
    `ConfigurationError: Unsupported Django field type 'CompositePrimaryKey'`; `exclude = ("pk",)` works. Decide: skip
    the composite pk in `"__all__"` or document it. Coverage: a `CompositeStamp` library model (composite pk plus a
    `db_column=` text column), migration 0017, a list field and a live test in `test_library_shapes_api.py`. Size S
    (M with the `"__all__"` fix)
- [ ] 28. The sharded fakeshop test is unverified until a `FAKESHOP_SHARDED=1` row of `django.yml` runs on the current
  head
  - Research: the three sharded paths pass locally at `feb83d59` (113 passed). The last green dispatch with the multi-DB
    rows is `f0885b9e` (2026-10-19), 94 commits behind. Closes on the next green dispatch or weekly run
  - Same run as `bug_hunt-0_0_15_2.md` item 29 (the hunt's final gate, Postgres and sharded runs included); one green
    dispatch on the current head closes both

## To do: tooling

- [ ] 29. `scripts/check_citations.py` does not check a spec citation written in comma form ("spec-037, Decision 3"),
  only the forms it parses today
  - Research: allow `,?` before the separator in `DECISION_RE`, and add tests beside
    `test_a_spec_decision_citation_must_name_a_decision_heading`. Two live comma citations exist (in
    `tests/types/test_converters.py`), and both resolve. Bracketed link forms stay unparsed (separate). Size S

## Waiting on you

- [ ] 30. `AGENTS.md` mandates repo-wide write-mode `ruff`; `docs/builder/worker-2.md` step 5 tells workers to scope it to
  the files the pass touched ("never on `.`"). `START.md` "Session rules you will forget" also states the repo-wide
  form, and the role files defer to `AGENTS.md`, so the scoping instruction is inert. Recommended: `AGENTS.md` and
  `START.md` adopt touched-path `ruff`, matching the explicit-path rule for `check_trailing_commas.py` under concurrent
  sessions
  - Research: `docs/builder/ARTIFACT.md`, `docs/review/REVIEW.md` and `docs/review/worker-2.md` already scope it. The
    repo-wide write form also appears in `docs/dry/worker-1.md`, `docs/dry/DRY.md`, `docs/bug_hunt/worker-1.md`,
    `docs/bug_hunt/HUNT.md`, the `scripts/bug_hunt.py` template, `examples/fakeshop/test_query/README.md`,
    `CONTRIBUTING.md` and `MUSE.md`. Read-only `.` checks in CI stay. Decide how far the sweep goes
  - Overlaps the KANBAN "Before a release" checklist (BoardDoc 11), whose repo-wide `ruff check --fix .` and
    `ruff format .` lines a touched-path rule rewrites, and `bug_hunt-0_0_15_2.md` item 183 (`ruff format` on an
    explicit `.md` path rewrites its fenced blocks, so a touched-path rule must pass Python paths only)

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
