# Review · Performance: `django_strawberry_framework/auth/` integration

Status: no-findings
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5676d4fc6310a5ff0d075771593a0f3068eb9406

Path class: hot — the four surface resolvers each run once per field per
request (`django_strawberry_framework/auth/mutations.py::_login_resolve_body`,
`::_logout_resolve_body`, the register pipeline entry, and
`django_strawberry_framework/auth/queries.py::_current_user_resolve_body`,
all through the shared
`django_strawberry_framework/auth/mutations.py::_make_auth_field._resolve`
dispatch); the folder lifecycle — factories, the declaration ledger, the
alias-namespace trio, `bind_auth_mutations`, and the `auth/__init__.py`
opt-in import — is declaration / finalize / import cold.

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes` — the auth rows are the
three verified file items, and the plan carries one Routed lead on
this item, judged below), `docs/review/rev-auth.md` (skeleton:
`Status: reviewing`, blank Path class). Sibling axis records
`rev-auth.mechanics.md` and `rev-auth.comments.md` did not exist at
close (siblings run concurrently); no foreign Handoff or
`## Cross-axis (for Performance)` owed. The main artifact carries no
Worker-2 sections yet.

Folder target read whole as it stands: the folder `__init__.py` (20
lines), `queries.py` (121 lines), `sessions.py` (284 lines), and
`mutations.py` (1346 lines) end to end, plus every cross-module seam
in both directions. `git diff ITEM_BASELINE --` over the folder is
empty (0 bytes), so the live tree equals the item baseline and the
fingerprints below are the baseline's. (`git status` shows
`auth/mutations.py` and `auth/sessions.py` modified vs HEAD: those
are the two verified file items' own uncommitted ledger rows —
blobs `98ae63f1` / `e50011e6`, matching the plan — not drift under
this item.)

Orientation: `review_inspect.py` per module under
`docs/review/temp-tests/auth-integration/performance/inspect-*/`
(JSON `init.json`, `mutations.json`, `queries.json`,
`sessions.json`): init 0 symbols / 0 hot entries / 0 import-time
work; the three modules' leads match what their verified file
passes already measured. Leads only.

Closed file records read for context and to avoid re-filing (all
three axes of all three files; Performance records closest):

- `rev-auth__mutations.performance.md` (verified, no-findings):
  7 live surfaces constant at 6 -> 12 users (login_ok 12 -> 12,
  login_bad 1 -> 1, logout_authed 4 -> 4, logout_anon 0 -> 0,
  me_authed 2 -> 2, me_anon 0 -> 0, register_ok 7 -> 7,
  `review-20260929T143117-4c3a90`); 14/14 hot-path bounds ok
  (`review-20260929T143133-018e39`); 0 of 69 importtime rows name
  `auth` (`review-20260929T143147-a9760b`); R1–R7.
- `rev-auth__queries.performance.md` (verified, no-findings): me
  authed 2 -> 2 / anon 0 -> 0 (`review-20260929T153812-6ef0fe`);
  8/8 bounds ok (`review-20260929T153828-92545a`); 69 modules /
  0 auth (`review-20260929T153844-7216b6`); R1–R5.
- `rev-auth__sessions.performance.md` (verified, no-findings):
  13/13 bounds ok (`review-20260929T160425-8b9320`, ~800 ns sync
  / ~1.6 us async / +~2 us WebSocket-logout boundary CPU); R1–R7.
- Mechanics: mutations F1 (holder metaclass consolidated into
  the owner, implemented and verified — declaration-cold, no
  hot-path number moves); queries and sessions no-findings.
- Comments: prose-only on all three files (mutations 12,
  queries 4, sessions 9), each verified by digest identity or
  byte-identical target. No file finding touches a resolver
  body, so the Performance probes above stand un-re-run at
  folder scope.

Folder seam map (every cross-module edge traced by hand; call
sites enumerated by grep, executable only):

- `auth/__init__.py` eagerly imports `.mutations` (3 factories)
  then `.queries` (`current_user`); `queries.py` imports 5
  private names from `.mutations` (family label, actor
  classifier, fixed-surface declaration path, field builder,
  bridged async body); `mutations.py` imports `.sessions` at
  top; `bind_auth_mutations` imports `.queries` function-local
  (cold, once per finalize, only when `current_user` declared).
  No cycle: the back edge is lazy and documented.
- Hot seam, sync login/logout: `_transport_prologue` =
  `request_from_info` (1x) + `sessions.classify_transport` (1x)
  + capability predicate (1x) + `sessions.require_session`
  (1x, a `getattr`, ~50 ns). Hot seam, async login/logout:
  the same plus one loop-branch `request_from_info` +
  `classify_transport` pair (~1.6 us total boundary CPU).
  `me` never touches `sessions.py`; register never touches it
  either (shared write skeleton only).
- The ONLY `for` loop in executable folder code is the cold
  ≤4-entry ledger scan in
  `django_strawberry_framework/auth/mutations.py::_declared_auth_surface`,
  called only from `_declare_auth_surface` (factories,
  declaration time). Zero `await` inside any loop. The only
  other comprehensions sit on raise paths or at bind.
- Zero static package importers of the folder outside itself
  (grep over the package: the two hits are prose); the sole
  runtime reach is `types/finalizer.py` via
  `loaded_attr("django_strawberry_framework.auth.mutations",
  "bind_auth_mutations")` — finalize cold. The structural
  opt-in holds: the package root never imports auth.
- `get_user_model()` runs at first factory call and at bind
  only (2 executable sites), never per request — and is
  Django-cached regardless.

Routed lead, judged: the plan's Routed lead from
auth/queries.py Comments
(`tests/auth/test_mutations.py::_request_with_store` opening
descriptively — "A Django request wired to an explicit session
store, anonymous actor") is a test-docstring mood question,
pure Comments axis. It carries no query, timing, or hot-path
content: the helper builds one `RequestFactory` request per
test. Out of Performance scope; routed onward to the Comments
sibling, not graded here.

Cells: default, sharded, and pg are all `inapplicable by
construction` for every entry below. The folder passes no
`using`, reads no alias, holds no raw SQL and no dialect
branch (single-row pk / unique-key statements plus Django
session CRUD through the default router — settings carry no
`DATABASE_ROUTERS`, so `shard_b` changes nothing for auth);
the file passes' live query shapes were measured on in-memory
SQLite by construction and are constant across table sizes;
every CPU entry is pure Python with no database reach. No
workspace run was needed: the folder is byte-identical to
what the three verified file probes measured, and every
folder-level candidate below resolves against owner bodies
plus those pinned figures. The verifier judges. Cells
unverified: none. Run ids: none (no `workspace.py` runs).

Fingerprints (`git hash-object` of every file whose body was
read):

- `django_strawberry_framework/auth/__init__.py` 2e480818424d4b130e613e3e2da027aaad7144ad
- `django_strawberry_framework/auth/mutations.py` 98ae63f1965a08d28332ae6e24aa24ea39d9d511
- `django_strawberry_framework/auth/queries.py` b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9
- `django_strawberry_framework/auth/sessions.py` e50011e6cae837a7b1322d704a7f8adbb69bcec3
- `django_strawberry_framework/types/finalizer.py` (phase-2.5 slot region) b9d8acb2b9428cc8297550414ff86bdd98e0d1a7
- `django_strawberry_framework/utils/permissions.py` (request owner) 1c9cfd398e6096e03bda82ba93dfd66a6d2fb890
- `django_strawberry_framework/utils/sessions.py` (engine/lease owner) 21041723250de58876d95eaec14e1078a6f16a4f
- `tests/auth/test_mutations.py` (Routed-lead helper region) 4cb499820cbed5163777099e9c9804cf7a523b50
- `docs/review/rev-auth__mutations.performance.md` b9070df1d9696cb29a586400070af86526d1e169
- `docs/review/rev-auth__queries.performance.md` (whole) — read live; blob not pinned (record may still grow a verify section under a concurrent pass)
- `docs/review/rev-auth__sessions.performance.md` (whole) — read live; same
- `docs/review/rev-auth__mutations.mechanics.md` 5fc46e232314eb80f83703bfa06f1d4d766ce5
- `docs/review/rev-auth__mutations.comments.md` (whole, findings + R1/R2 routes) — read live
- `docs/review/rev-auth.md` 8d7543933322eabb34c40fe7e26a20a396ac8a85

## Findings

### High

None.

### Medium

None.

### Low

None.

## Looks-for discharge

Every entry is `none` with the reason, measured where a file
probe backs it. Folder-crossing candidates that clear the
"worth naming" bar are rejections RF1–RF2 below; seam costs
already rejected inside the closed file items are cited, not
re-filed.

- N+1 and per-row queries: none, measured. All seven folder
  surfaces are constant across user-table sizes (12/1/4/0/2/0/7
  at 6 -> 12 users), including two zero-query anonymous paths;
  the folder's only loop is declaration-cold, no `await` sits
  in any loop, and no `.filter(` / `.get(` / `objects.` queryset
  exists anywhere in the folder — the resolver bodies issue
  zero SQL themselves (actor-not-lookup; session work is
  Django/Channels natives). A multi-auth-field operation runs
  each root field once; fields share no per-row multiplier.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none.
  Zero hits for every spelling across the folder; no queryset
  exists to count.
- `only()` / `defer()`: none. Zero hits; the only rows read
  are the middleware's own fully-loaded session/user rows.
- Unbatched writes where `bulk_create` / `bulk_update` fit:
  none. The only row write is the single-user register INSERT
  (plus Django's own session / `last_login` writes); no batch
  shape exists at folder scope.
- `blog.id` vs `blog_id`: none. Zero model-attribute or FK
  reads on any folder path (the one `_id` hit is a docstring
  mention of `<field>_id` inputs).
- Repeated `_meta` walks: none. Zero `_meta` hits in the
  folder. `derive_register_fields` reads `USERNAME_FIELD` /
  `REQUIRED_FIELDS` (plain attributes, not `_meta` walks) at
  declaration only.
- Repeated settings reads: none rising above the one
  documented call-time read. Zero `settings` hits in
  executable folder code; the single reachable read
  (`logout_supported` -> `uses_signed_cookie_sessions` ->
  `session_store_class`) fires only on WebSocket logout and
  must read at call time for `override_settings` (file
  rejections sessions R3 / mutations R7, not re-filed).
- Repeated regex compilation: none. Zero `re` hits in the
  folder.
- Repeated schema or type lookups per request: none rising to
  a finding. Per-request folder work is one dispatch read
  (~160–180 ns), one `request_from_info` (~0.8–1.9 us), one
  classify (~0.7–0.8 us), one gate, and one payload build —
  each once per field (twice per async login/logout for the
  resolve+classify pair: file rejections mutations R4 /
  sessions R1, not re-filed). The payload class/slot
  recompute is mutations R1, the wire-name map is mutations
  R2 (routed to `mutations/resolvers.py`), the lazy
  `resolvers` import is queries R1 — all cited, none
  re-filed. A cross-field per-operation memo is RF2.
- `lru_cache` on methods: none. Zero hits; the folder's only
  memos are the cold declaration ledger and the cold alias
  trio.
- Locks: none removable. One `scope_session_lock`
  acquisition per Channels login/logout plus the documented
  scope-OUTER / actor-lease-INNER pair at the single logout
  site; the Django path is lock-free. Mutations execute
  serially, so the non-reentrant lock never re-enters (file
  rejections mutations R6 / sessions R5, not re-filed).
- Cache reads: none. Zero cache hits outside ledger-cache
  prose.
- Re-parses: none. No document parsing, no plan-cache touch
  anywhere in the folder.
- Extra round trips on the per-request path: none beyond the
  one justified duplicate (login's durability + cookie-emission
  UPDATE pair: mutations R5, not re-filed). `require_session`
  is a `getattr`, not I/O; the anonymous logout / `me` paths
  measure 0 queries.
- Import-time cost: none, measured. The package root never
  imports auth (structural opt-in; zero static package
  importers, sole runtime reach via finalize-cold
  `loaded_attr`): 0 of 69 `importtime_report.py` rows name
  `auth`, measured twice (`review-20260929T143147-a9760b`,
  `review-20260929T153844-7216b6`). The opt-in folder import
  itself runs only ledger construction + the alias trio + two
  `register_subsystem_clear` rows, reads no settings, and
  pulls no channels/asgiref (both function-local; pinned by
  `tests/auth/test_sessions.py::test_auth_submodule_import_stays_channels_free`).
  Eager `.queries` import from `__init__` is RF1.
- Allocation in the walk: none. The folder is not the
  optimizer walk and holds no hot loop; per-request
  allocations are one small gate-data dict, tuples, and the
  payload object itself — all inherent. Every f-string, join,
  and comprehension sits on a cold, bind-time, or raising
  path.

## Rejected

- RF1: lazy-load `.queries` in `auth/__init__.py` (import it
  on first `current_user` use) instead of the eager
  `from .queries import current_user`, so a login-only
  consumer skips the queries module. Rejected: cold-path
  plainness wins — the module is 121 lines whose import runs
  only the alias trio plus one clear row on top of the
  already-imported `.mutations`, and laziness would trade a
  plain re-export surface for import machinery with no
  per-request effect (factories run at declaration, never per
  request). Trigger: the opt-in `import auth` cost appears in
  a measured consumer profile with `django.contrib.auth`
  factored out.
- RF2: memoize `request_from_info` per operation across auth
  fields, so a multi-auth-field operation pays the ~1–2 us
  shape sniff once instead of once per field. Rejected: a
  single auth field per operation is the norm (login XOR
  logout XOR register XOR me; a login+logout operation is
  pathological), so there is normally no second call to
  amortize against; even doubled, ~2–4 us beside 10–200 ms
  of hashing plus session DB work; and the helper is owned
  by the `utils/permissions.py` item (shared by the filter /
  order / mutation seams), not this fence — a folder-local
  cache keyed off shared `info.context` would split its one
  rule. The single-field form of this candidate is already
  rejected as queries R3. Trigger: a profile of a real
  multi-auth-field operation attributes more than 1% of
  operation CPU to request resolution, and the owner memoizes
  the seam for all callers.

## Cross-axis

None. No finding on another axis; the plan's Routed lead is a
Comments-lead pass-through (see Trace), not a finding.

Handoff: Performance closes no-findings at folder scope. The
folder's hot story is fully contained in its three verified
file passes: every surface batched and constant, every
per-request seam measured in the low single-digit
microseconds against millisecond-scale hashing and session
DB work, zero package-import cost by a structural opt-in I
re-verified (no static importers; finalize reaches bind only
through `loaded_attr`). The two folder-level candidates I
could name (eager `.queries` import, cross-field request
memo) are cold-path plainness and owner-outside-fence
rejections with triggers, and every seam micro-cost (async
double resolution, payload recompute, wire-name map, lazy
imports, lock/lease, double UPDATE, settings read) is a
cited file-level rejection, deliberately not re-filed. The
`## Bench baseline` rows stand — no figure moves: the benches
measure plan cache, the optimizer walk, nested fetch, and
the package import, none of which this folder reaches. A
verifier reproduces this pass statically (`git diff
ITEM_BASELINE -- django_strawberry_framework/auth/` empty;
the grep censuses in Trace; `check_citations.py --paths` on
this record) — no workspace run is owed, and none was taken.
Open threads: none. Sibling notes: sibling axis records were
absent at review time; if the Mechanics or Comments passes
land findings touching a resolver body, prologue, classifier,
or import edge, their verifiers should re-run the file
`probe_query_counts.py` scripts to confirm the counts still
hold.

## Verify performance

Pass 1, fully static (no copy bound, no workspace run — none
owed on a zero-path implement pass).

Zero-change check: `git diff ITEM_BASELINE --`
over `django_strawberry_framework/auth/` + `tests/auth/` is
empty (0 bytes), ITEM_BASELINE
5676d4fc6310a5ff0d075771593a0f3068eb9406. Live
fingerprints equal the review's: init
2e480818424d4b130e613e3e2da027aaad7144ad (matches the
plan's baseline), mutations
98ae63f1965a08d28332ae6e24aa24ea39d9d511, queries
b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9, sessions
e50011e6cae837a7b1322d704a7f8adbb69bcec3,
tests/auth/__init__.py
09e0f06d9c93719e6e75dbcd54e8c03255c655b0 (F1 deferred,
untouched). Nothing attributable to this item; the
`auth/mutations.py` + `auth/sessions.py` dirty-vs-HEAD hunks
are the two verified file items' own ledger rows, as the
review already states.

No-findings stands: the Implement pass took zero paths
(Performance + Mechanics recorded no-findings; Comments F1
Low deferred per the ride rule), so every measured figure
the review cites (7 constant live surfaces, 14/14 + 8/8 +
13/13 hot-path bounds, 0-of-69 importtime rows) still
describes byte-identical code. RF1/RF2 triggers unmet (no
new consumer profile exists; static). No bench row moves:
the benches measure plan cache, optimizer walk, nested
fetch, and package import — none reachable from this
folder, and no code moved. Sibling check per the review
Handoff: Mechanics carries only `## Cross-axis (for
Comments)` (no Performance finding to re-probe), Comments
carries no Cross-axis section and its F1 is a test-docstring
census with no resolver/prologue/classifier/import content —
no re-run owed. Record citations resolve
(`check_citations.py --paths` on this record: 6/6 OK).
Cells: inapplicable-by-construction stands (nothing to
prove); none unverified. No new defects.

Status: verified. Open threads: none.
