# Review · Comments: `django_strawberry_framework/auth/queries.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=f26a7dff116cf2968524bab663453025006e185b

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run
0.0.15 2026-09-28-3, incl. its `## Owned changes`, which holds
no row for this target and no Routed lead on this item),
`docs/review/rev-auth__queries.md` (skeleton: `Status:
reviewing`, blank Path class). Sibling
`rev-auth__queries.mechanics.md` read whole incl. its Handoff
(no-findings; no `## Cross-axis (for Comments)`; its R1/Handoff
observations noted below, out of this axis's scope).
`rev-auth__queries.performance.md` did not exist at close
(siblings run concurrently); the verifier should confirm it
carries no `## Cross-axis (for Comments)`.

Target read whole, all 121 lines, as it stands: blob
`b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9`. `git diff
ITEM_BASELINE --` the target and its test module is empty:
the live tree equals the item baseline, so the fingerprints
below are the baseline's.

Orientation (leads only): `review_inspect.py` overview at
`docs/review/temp-tests/auth-queries/comments/inspect/`
(json `docs/review/temp-tests/auth-queries/comments/queries.json`):
3 docstrings, 4 comment blocks, 0 TODOs, 4 `spec-` flags
(all Decision pointers, kept per START.md).
`build_tree_md.py --list-docstrings` green on the target and
on `tests/auth/test_queries.py` (first-line rule holds; the
words are still graded here). `check_citations.py --paths
... --substrings` reports 0 citations in both files.
Provenance sweep over both files: `legacy` hits name
Django's pre-1.10 callable `is_authenticated()` only (R2);
no `Tests that` / `Ensures` / `we` / `you` / `I` /
line-number cites in either file.

Every docstring and comment graded against its body and one
real caller. Target blocks (7): module docstring, the three
module comments, the resolve-body docstring + inline
comment, the factory docstring — all true (R8 discharge).
Own test module `tests/auth/test_queries.py` graded whole:
module docstring (F1 first line stale; body paragraph L2),
5 helper + 3 class docstrings (L1 mood on one), 16 test
functions (15 docstrings: 14 true + F2 stale; 1 absent, R1),
8 inline/pragma comments (all true). Other test modules'
prose about the target's symbols: `tests/auth/conftest.py`
(the spy), `tests/auth/test_mutations.py` (5 sites),
`examples/fakeshop/test_query/test_auth_api.py` (10 `me`
sites) — all true. Package modules' prose about the
target's symbols (`auth/mutations.py` 8 sites,
`mutations/fields.py` 2 sites, `types/finalizer.py`,
`auth/__init__.py`) — all true; no Routed lead.

Callers/owners read for the grades:
`django_strawberry_framework/auth/mutations.py::bind_auth_mutations`,
`django_strawberry_framework/auth/mutations.py::_sync_bridged_async_body`,
`django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`,
`django_strawberry_framework/auth/mutations.py::_declare_fixed_auth_surface`,
`django_strawberry_framework/auth/mutations.py::_make_permission_holder`,
`django_strawberry_framework/mutations/resolvers.py::authorize_or_raise`,
`django_strawberry_framework/utils/inputs.py::make_input_namespace`,
`django_strawberry_framework/utils/inputs.py::materialize_generated_input_class`,
`django_strawberry_framework/utils/permissions.py::request_from_info`,
`django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter`,
`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`,
`django_strawberry_framework/utils/directives.py::validated_field_directives`,
`django_strawberry_framework/mutations/fields.py::_lazy_ref`,
`django_strawberry_framework/mutations/fields.py::build_lazy_field_signature`,
`django_strawberry_framework/registry.py::register_subsystem_clear`,
`django_strawberry_framework/registry.py::iter_subsystem_clears`,
the finalizer phase-2.5 slot, spec-040 Decisions 7/8/9/10 +
D13/D-N1/D17 bodies, and the installed Django
`AbstractBaseUser.is_authenticated` origin. History:
`git show fad17c20^:.` vs `fad17c20:.` for the F1 staleness
mechanism.

Cells: default, sharded, and pg are all inapplicable by
construction — every Proof below is a static shared-tree
command over prose. No workspace runs were made; no run ids
exist for this record.

Fingerprints (`git hash-object`):

| File | Blob |
|---|---|
| `django_strawberry_framework/auth/queries.py` | `b036bdac` |
| `django_strawberry_framework/auth/mutations.py` | `98ae63f1` |
| `django_strawberry_framework/auth/sessions.py` | `865d6e70` |
| `django_strawberry_framework/auth/__init__.py` | `2e480818` |
| `django_strawberry_framework/types/finalizer.py` | `b9d8acb2` |
| `django_strawberry_framework/registry.py` | `27358cbc` |
| `django_strawberry_framework/utils/inputs.py` | `b5af8255` |
| `django_strawberry_framework/utils/permissions.py` | `1c9cfd39` |
| `django_strawberry_framework/utils/querysets.py` | `8fc556d5` |
| `django_strawberry_framework/utils/directives.py` | `84f770d4` |
| `django_strawberry_framework/mutations/fields.py` | `0e4d5ed1` |
| `django_strawberry_framework/mutations/resolvers.py` | `c9cff059` |
| `tests/auth/test_queries.py` | `86fa35e3` |
| `tests/auth/test_mutations.py` | `4cb49982` |
| `tests/auth/test_sessions.py` | `b71c84ec` |
| `tests/auth/conftest.py` | `a5c413ba` |
| `tests/auth/_helpers.py` | `996762b0` |
| `tests/utils/test_permissions.py` | `71e1ff4b` |
| `examples/fakeshop/test_query/test_auth_api.py` | `17fc9ddb` |
| `docs/TREE.md` | `769c2743` |
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | `4c9c585c` |
| `docs/review/review-0_0_15.md` | `6e025258` |
| `docs/review/rev-auth__queries.md` | `8d754393` |
| `docs/review/rev-auth__queries.mechanics.md` | `8fedec8d` |

## Findings

### High

None.

### Medium

#### F1 — test module first line claims `visibility` coverage the module does not hold

- Observation: the module docstring first line of
  `tests/auth/test_queries.py` enumerates `visibility` among
  the module's subjects, but the module contains no
  visibility test: the hide-everyone `get_queryset` row was
  promoted to the live tier and the module body itself says
  that behavior "is earned in
  `examples/fakeshop/test_query/test_auth_api.py`".
- Evidence: `git show fad17c20^:tests/auth/test_queries.py`
  holds
  `test_me_composes_with_login_in_one_schema_without_visibility_rerun`
  ("`me` returns the actor even under a hide-everyone
  `get_queryset` (D-N1)"); `fad17c20` ("promote the
  consumer-reachable login, logout, register and me rows to
  the live tier") deleted it, leaving the first line
  untouched. Today `grep -n "get_queryset|visibility"`
  over the module hits only line 1 (`visibility`) and
  line 11 (the live-tier pointer). The live successor is
  `examples/fakeshop/test_query/test_auth_api.py::test_login_and_me_skip_user_type_visibility`.
  The stale first line renders into `docs/TREE.md` twice
  (lines 514, 765), so the fix rides a TREE.md render.
- Impact: a reader searching for the visibility pin looks
  in the wrong tier; the module contradicts itself (first
  line claims it, body disclaims it); the false census
  ships in TREE.md.
- Severity: Medium (stale docstring on internal code;
  test-module prose, not a public symbol).
- Recommendation: drop the spent word; re-render TREE.md
  in the same change (`uv run python
  scripts/build_tree_md.py`; attribute both hunks). See
  text-after.
- Must not change: n/a.
- Proof: `grep -c "visibility"
  tests/auth/test_queries.py` prints `0` (1 today);
  `grep -c "visibility, permission gates" docs/TREE.md`
  prints `0` (2 today); `uv run python
  scripts/build_tree_md.py --list-docstrings
  tests/auth/test_queries.py` exits 0; the rewritten first
  line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_queries.py` (module docstring).
- Grade: stale (promotion leftover; body disclaims what
  the first line claims).
- Text-before: `Current-user query tests for alias
  binding, visibility, permission gates, and sync/async
  resolution.`
- Text-after: `Current-user query tests for alias binding,
  permission gates, and sync/async resolution.`

#### F2 — async dispatch test calls the interim bridge a native async body

- Observation: the async dispatch test's name and
  docstring say `me` "awaits the native async body", but
  `current_user` has no native async body: its async seam
  is the interim
  `django_strawberry_framework/auth/mutations.py::_sync_bridged_async_body`
  bridge. The wording was copied from the
  `tests/auth/test_mutations.py` twins, where "native" is
  correct (login/logout ship native async bodies).
- Evidence: the owner docstring ("Build the interim async
  resolver body", "This is the SEAM only"); the
  `tests/auth/conftest.py::_sync_boundary_spy` docstring
  ("`current_user` through the `_sync_bridged_async_body`
  interim bridge, `login` / `logout` through their native
  async bodies", landed by the auth/mutations item);
  `django_strawberry_framework/auth/queries.py::current_user`
  wires `async_body=_sync_bridged_async_body(sync_body)`;
  the mechanics sibling record concurs ("`current_user`
  has no native async body"). Single-sited: the old name
  occurs only at `tests/auth/test_queries.py:179-180`
  (plus per-cycle DRY/review prose, which is frozen).
- Impact: states the wrong async shape for the field;
  contradicts the conftest prose every async test in both
  auth suites reads.
- Severity: Medium (stale test docstring + test name on
  internal code).
- Recommendation: rename the test and reword the
  docstring to the bridge vocabulary; see text-after (the
  new name is plain text here — it does not exist yet).
- Must not change: n/a.
- Proof: `grep -c "native async body"
  tests/auth/test_queries.py` prints `0` (1 today) and
  `grep -c "native_async_body"
  tests/auth/test_queries.py` prints `0` (1 today); the
  renamed test (test_async_me_dispatch_awaits_the_bridged_async_body_exactly_once
  in tests/auth/test_queries.py) plus its rewritten
  docstring earn grade true (the replacement word is
  bridge-true: "bridged" or "interim", matching the
  conftest's bridge-vs-native prose).
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_queries.py::test_async_me_dispatch_awaits_the_native_async_body_exactly_once`.
- Grade: stale (copied twin wording; false of this
  surface's seam).
- Text-before: def
  `test_async_me_dispatch_awaits_the_native_async_body_exactly_once`
  + docstring "`await schema.execute` `me` awaits the
  native async body exactly once."
- Text-after: def
  `test_async_me_dispatch_awaits_the_bridged_async_body_exactly_once`
  + docstring "`await schema.execute` `me` awaits the
  bridged async body exactly once."

### Low

#### L1 — `_channels_context` docstring is descriptive, not imperative

- Observation: the `_channels_context` helper docstring
  opens with a description ("A ... context ...") where the
  axis requires the imperative for a function. It is the
  lone descriptive helper in its file (every sibling
  helper opens `Register` / `Declare` / `Reset` / `Patch`
  / `Spy` / `Build` / `Yield`).
- Evidence: first-line census over `tests/auth/*.py`
  helper docstrings (AST scan this pass): all imperative
  except this one and the mutations-owned
  `tests/auth/test_mutations.py::_request_with_store`
  (observed, not graded — that file's item is closed;
  see Handoff).
- Impact: bounded style consistency; the reviewer is the
  mood gate (D401 unchecked).
- Severity: Low.
- Recommendation: reword to the imperative; see
  text-after. Rides the file F1/F2 already touch.
- Must not change: n/a.
- Proof: `grep -c "A Strawberry-Channels mapping context"
  tests/auth/test_queries.py` prints `0` (1 today); the
  rewritten first line earns grade true (imperative).
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_queries.py::_channels_context`.
- Grade: mood defect (descriptive opening on a function).
- Text-before: `A Strawberry-Channels mapping context
  (spec-041) that resolves to the adapter.`
- Text-after: `Build a Strawberry-Channels mapping context
  (spec-041) that resolves to the adapter.`

#### L2 — module body paragraph omits five pinned behaviors

- Observation: the module docstring's residue enumeration
  ("The `current_user` residue a live fakeshop request
  cannot drive: A, B, ..., and E") is maintained as the
  module's coverage statement (rewritten at each live
  promotion) but omits five behaviors the module pins:
  the one-declaration conflict error, the sync/async
  dispatch counting, the mapping-context request shape,
  the absent-user arms (Channels adapter, lazy `None`,
  custom actor), and the bare-string `directives`
  rejection.
- Evidence: enumeration shape + promotion history
  (`fad17c20`, `a01a2ab8` each rewrote it to track the
  module's tests); the five pins exist at
  `tests/auth/test_queries.py:161`,
  `tests/auth/test_queries.py:168`,
  `tests/auth/test_queries.py:179`,
  `tests/auth/test_queries.py:190`,
  `tests/auth/test_queries.py:202`,
  `tests/auth/test_queries.py:350`, none named in the
  paragraph. Everything the paragraph DOES say is true
  (each listed pin verified against its test).
- Impact: a reader relying on the paragraph misses a
  third of the module's pins.
- Severity: Low (bounded clarity improvement on internal
  prose).
- Recommendation: extend the enumeration; see text-after.
  Rides the file F1/F2 already touch.
- Must not change: n/a.
- Proof: `grep -c "conflict"
  tests/auth/test_queries.py` prints `2` or more (1
  today — the bare def name); the rewritten paragraph
  earns grade true (names the conflict, dispatch,
  mapping, absent-user, and directives pins).
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_queries.py` (module docstring
  body).
- Grade: incomplete census (true as far as it goes;
  maintained as exhaustive, missing five pins).
- Text-before: `The ``current_user`` residue a live
  fakeshop request cannot drive: the
  ``CurrentUserAlias`` namespace lifecycle (the
  ``make_input_namespace`` trio + its pre-bind
  ``register_subsystem_clear`` row), the surface-keyed
  current-user-only bind (its no-``UserType`` arm + no
  orphan payloads), the gated-anonymous ``GraphQLError``
  and its exact denial string, the legacy callable and
  awaitable ``is_authenticated`` forms plus a raising
  one's propagation, and the async lazy-user forcing
  inside the one ``sync_to_async`` boundary.`
- Text-after: `The ``current_user`` residue a live
  fakeshop request cannot drive: the
  ``CurrentUserAlias`` namespace lifecycle (the
  ``make_input_namespace`` trio + its pre-bind
  ``register_subsystem_clear`` row), the surface-keyed
  current-user-only bind (its no-``UserType`` arm + no
  orphan payloads), the one-declaration conflict error,
  the sync/async dispatch counting, the mapping-context
  request shape, the absent-user arms (the Channels
  adapter shape, a lazy ``None``, a custom actor), the
  bare-string ``directives`` rejection, the
  gated-anonymous ``GraphQLError`` and its exact denial
  string, the legacy callable and awaitable
  ``is_authenticated`` forms plus a raising one's
  propagation, and the async lazy-user forcing inside the
  one ``sync_to_async`` boundary.`

## Rejected

- R1: no docstring on
  `tests/auth/test_queries.py::test_conflicting_current_user_gates_raise_the_one_declaration_error`
  — accepted variance, not a finding. The axis flags
  absence only for public symbols, and docstring-less
  tests are established in this suite (3 in
  `tests/auth/test_mutations.py`, 17 in
  `tests/auth/test_sessions.py`, AST-counted this pass).
  Trigger: a gate requiring per-test docstrings.
- R2: `legacy` vocabulary (module line 7, the
  `test_legacy_*` names/docstrings) — names Django's
  pre-1.10 callable `is_authenticated()`, a historical
  upstream API fact, and matches the owner's own
  "legacy callable form (pre-1.10 ...)" vocabulary in
  `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`.
  Not process provenance. No trigger (owner-pinned
  vocabulary).
- R3: spec pointers (`spec-040` Decision 7/8/9/10,
  D13, D-N1, D17; `spec-041`) — all resolve in
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md`
  (Decision 10's body corroborates the "async-gate"
  claim line by line) and `spec-041-channels_router`
  exists. Kept per START.md. No trigger.
- R4: `django_strawberry_framework/utils/inputs.py::make_input_namespace`
  "the mutation + form + serializer input modules share"
  not naming `auth/queries.py` — not stale. The census
  names input modules; the alias namespace is not one,
  and the sentence claims no exhaustiveness ("only" /
  a count). Trigger: the helper docstring gains an
  exclusive census.
- R5: "The AllowAny default gates nothing"
  (`django_strawberry_framework/auth/queries.py::_current_user_resolve_body`)
  beside "no `AllowAny` class exists" — true shorthand,
  suite-consistent (live tier: "canonical AllowAny
  default surface"; `tests/auth/test_mutations.py`:
  "the documented AllowAny auth default"). No trigger.
- R6: "a me-only schema materializes the alias and
  nothing else"
  (`tests/auth/test_queries.py::test_current_user_only_bind_emits_no_login_logout_payloads`)
  — "materializes" scopes to emit (no Login/Logout
  payloads asserted); the holder `_primary_type`
  assignment is not a materialization. True. No trigger.
- R7: "pins the alias to the resolved user primary each
  finalize" (target module docstring) — surface-keyed
  in context (the bind pins when `current_user` was
  declared; a `current_user`-free ledger never reaches
  the arm). True. No trigger.
- R8: target prose discharge — every remaining block
  graded true against its body and one real caller:
  module docstring (Decision 7 / D-N1 / D13 / Decision
  9 pointers; actor-not-lookup; no re-fetch; parked
  global; pre-bind clear defeating the distinct-class
  collision — each verified at its owner);
  `CURRENT_USER_ALIAS_NAME` comment (`me: UserType` SDL
  pinned live); trio comment; pre-bind comment
  (finalizer drains pre-bind rows before the bind,
  full `clear()` replays all rows, the declaration
  ledger row carries no `before_bind` flag);
  `django_strawberry_framework/auth/queries.py::_current_user_resolve_body`
  docstring (gate-first, forced lazy load in-boundary,
  top-level `GraphQLError`, nullable-after-gate,
  `IsAuthenticated`-style denial — all pinned) +
  Channels inline comment (adapter `None`, missing
  `user` attribute, shared-with-logout ownership);
  `django_strawberry_framework/auth/queries.py::current_user`
  docstring (query-not-mutation, nullable-by-contract,
  no envelope, `CurrentUser` holder, lazy forward-ref).
  Likewise the other test modules' prose about the
  target's symbols: `tests/auth/conftest.py::_sync_boundary_spy`,
  five `tests/auth/test_mutations.py` sites
  (`tests/auth/test_mutations.py::_declare_group_type`,
  `tests/auth/test_mutations.py::_login_logout_schema`,
  `tests/auth/test_mutations.py::test_auth_permission_holder_snapshot_is_sealed`,
  `tests/auth/test_mutations.py::test_gate_introspecting_the_mutation_object_raises_on_the_model_less_fields`,
  `tests/auth/test_mutations.py::_auth_router_schema`),
  and ten live-tier `me` sites (happy path, relay id,
  anonymous `null`, reload, SDL shapes, missing
  middleware, visibility skip, holder schema + poster,
  seeder, strictness `OptimizerError` — each body-read).
  No trigger (verified true, not merely unrefuted).

Handoff: Beyond the record's trace I read spec-040
Decisions 7/10 whole (Decision 7's hostile-collapse
paragraph is stale against the shipped propagate-and-mask
behavior per the mechanics sibling's R1 — frozen spec
archive, no lead owed from this axis), the DRY
`dry-file-auth__queries.md` J2 ("native async body for
`me`", rejected — background only, consistent with F2),
and the GLOSSARY `request_from_info` parenthetical the
mechanics Handoff flags (omits `AuthMutation` — docs
prose, not a package module, so no Routed lead; the
folder/project passes own it). Conclusions not in the
findings: the target's own prose is exemplary (every
claim lands on a pinned oracle); the residue paragraph
is where this file rots, and L2's enumeration will rot
again the next time a test lands without a paragraph
edit — the verifier should grade the paragraph against
the final test list, not just the Proof anchors. Open
threads: (1) the Performance sibling record did not
exist at close — confirm at verify it carries no
`## Cross-axis (for Comments)`; (2) F1's TREE.md render
must attribute both hunks (render reads tracked files;
no concurrent TREE.md move was seen); (3) observed, not
graded: `tests/auth/test_mutations.py::_request_with_store`
opens descriptively like L1, but its file's item is
verified/closed and the helper is not prose about this
target's symbols — a folder/project mood sweep may take
it. No Cross-axis findings: nothing in this pass belongs
to Performance or Mechanics.

## Verify comments

Precondition: the live tree carries exactly the change under grade.
`git diff ITEM_BASELINE -- tests/auth/test_queries.py docs/TREE.md
django_strawberry_framework/auth/queries.py` (4921 bytes, sha256
f69a9862) is byte-identical to
`docs/review/temp-tests/auth-queries/diff/pass-1.diff` (`diff` exit 0;
copy at `docs/review/temp-tests/auth-queries/verify-comments-1/live-diff.txt`).
Fully static: no workspace copy bound, no run ids.

Target untouched: live blob `b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9`
== ITEM_BASELINE blob == record fingerprint; `git diff ITEM_BASELINE --`
the target is 0 bytes; `review_inspect.py --code-digest` prints
`sha256:27c0662b` on both sides (exit 0).

### F1 — pass

`grep -c "visibility" tests/auth/test_queries.py` prints `0` live (1 at
baseline); `grep -c "visibility, permission gates" docs/TREE.md` prints `0`
live (2 at baseline); `build_tree_md.py --list-docstrings
tests/auth/test_queries.py` exits 0 ("1 modules, 0 breaking the first-line
rule"). TREE.md carries exactly 2 rows of the new first line (live 514 +
765, the `test_queries.py` row both times; 4 +/- lines in the TREE section,
no foreign hunk), text equal to the live module first line. Grade true: the
module holds no visibility test (`get_queryset` hits live line 14 only, the
live-tier pointer), the body disclaims the behavior to
`examples/fakeshop/test_query/test_auth_api.py`, and the live successor
`test_login_and_me_skip_user_type_visibility` stands at
`test_auth_api.py:1020`. Text-after landed verbatim.

### F2 — pass

`grep -c "native async body"` prints `0` live (1 at baseline);
`grep -c "native_async_body"` prints `0` live (1 at baseline). The renamed
test + docstring stand at `tests/auth/test_queries.py:182-183`
(`test_async_me_dispatch_awaits_the_bridged_async_body_exactly_once`,
"awaits the bridged async body exactly once"), verbatim from the record's
text-after. Bridge-true: the owner docstring reads "Build the interim async
resolver body" (`auth/mutations.py:351`), the conftest prose reads "the
`_sync_bridged_async_body` interim bridge, `login` / `logout` through their
native async bodies" (`tests/auth/conftest.py:22-23`), and
`auth/queries.py:115` wires `async_body=_sync_bridged_async_body(sync_body)`.
Single-sited: the old name has zero live `.py` references; remaining hits
are frozen per-cycle prose (`dry-file-auth__queries.md:240`, this record's
Text-before/Symbol, `rev-auth__queries.performance.md:22` — the expected
frozen review-time cite) plus the mechanics verifier's baseline copy. The
`test_mutations.py` "native" twins (lines 774-775, 802-803) are login/logout
where "native" is correct. Grade true.

### L1 — pass

`grep -c "A Strawberry-Channels mapping context"` prints `0` live (1 at
baseline). Live `:118` reads "Build a Strawberry-Channels mapping context
(spec-041) that resolves to the adapter.", verbatim from the text-after.
Grade true (imperative): the file's helper census is now Reset / Register /
Declare / Build / Patch, all imperative. The `(spec-041)` pointer is kept per
START.md (verbatim from the record's text-after, not introduced here).

### L2 — pass

`grep -c "conflict"` prints `2` live (1 at baseline): the paragraph (`:7`)
plus the bare def name (`:164`). The residue paragraph (lines 1-18,
whitespace-normalized) equals the record's text-after verbatim. Graded
against the FINAL test list (15 tests), per the Handoff — every test maps:
namespace lifecycle -> `:125`; surface-keyed bind (no-`UserType` arm + no
orphan payloads) -> `:142` + `:150`; conflict -> `:164`; dispatch counting
-> `:171` + `:182`; mapping-context -> `:193`; absent-user arms (Channels
adapter + lazy `None` + custom actor, all three asserted in one test) ->
`:205`; raising propagation -> `:243`; legacy callable / awaitable forms ->
`:286` + `:301` + `:329`; directives rejection -> `:353`; gated-anonymous
denial string -> `:360`; async lazy-user forcing -> `:374`. No test unlisted,
no clause unpinned. Grade true (exhaustive as landed).

Whole-diff reading: the four test hunks are F1/L2/L1/F2 prose + the one test
rename only; TREE.md is the two F1 render rows. `check_citations.py --paths
tests/auth/test_queries.py --substrings` (with and without `--json`): OK, 0
citations, exit 0. Added-line sweeps: no `we`/`you`/`I`, no line-number
cites, no "Tests that"/"Ensures" (0 in file); the REVIEW provenance list hits
only the R2-kept "legacy callable" vocabulary (reflowed, not introduced) and
the kept `(spec-041)` pointer. Full-file `spec-`/`worker` hits outside the
diff (`:210`, `:377`, `:380`) are pre-existing prose in untouched symbols,
not graded. No touched symbol's surrounding prose was made false (the
`_channels_context` body still resolves to the adapter; the renamed test body
still awaits exactly once).

Handoffs obeyed: (1) no `## Cross-axis` header in the Performance or
Mechanics records (the Performance verify answers it likewise); (2) both
TREE.md hunks attributed (514/765, `test_queries.py` row, text == live first
line); (3) the `test_mutations.py::_request_with_store` mood observation
stands for a folder/project sweep, not graded. The Performance Handoff's
conditional probe re-run is not owed (no resolver body touched). Disputes:
none (all four landed verbatim). Attacks: old-name/new-name repo-wide sweeps,
TREE scope, citation + provenance sweeps, successor-pin check — all clean. No
`verify 1` finding; no gap on another axis.

Fingerprints live: `django_strawberry_framework/auth/queries.py` b036bdac,
`tests/auth/test_queries.py` a57722d4, `docs/TREE.md` 5c9d6066 (full blobs in
`docs/review/temp-tests/auth-queries/verify-comments-1/fingerprints.txt`).
Scratch: `docs/review/temp-tests/auth-queries/verify-comments-1/`
(`live-diff.txt`, `fingerprints.txt`, `proofs.txt`). New defects: none. Open
threads: none — except the record's standing note that L2's enumeration will
rot again when a test lands without a paragraph edit (maintenance watch, no
action).

Status: verified
