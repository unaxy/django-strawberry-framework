# DRY review: `prepared-view-handoff-shape`

Status: verified
Run: 0.0.15 2026-10-01-9

Family `prepared-view-handoff-shape`. Owner TBD by dispatch
(candidates: `_boundary_ordering.py` via pack/validate helpers,
or `views.py`) — decided here:
`django_strawberry_framework/_boundary_ordering.py` via a
pack helper plus a consume helper, re-derived, not inherited.
Indexed files (3):
`django_strawberry_framework/_boundary_ordering.py` (clean at
HEAD blob `197eea8e`), `django_strawberry_framework/views.py`,
`django_strawberry_framework/middleware/request_body.py`. Trace
at HEAD `5c3496e0` bytes;
`ITEM_BASELINE=73bec393832dbff22e94b4950146f9c8308e7a2c`.
Prior records (run-2 routing: target plus `views.py` plus
`middleware/request_body.py`, reshape count 2, owner
candidates) used only as population hints; every verdict below
re-derived fresh. Never read any `worker-memory/`.

Verdict in one line: F1 CONFIRMED (the handoff payload
grammar is spelled twice — the middleware pack plus the views
unpack, count 2) but BLOCKED on hunt-dirtied pack lines — zero
edits; nine rejections carry contract differences plus
triggers.

## System trace

The rule is the prepared-view handoff grammar between the
boundary middleware and the package view callback: after
`GraphQLRequestBodyBoundaryMiddleware.process_view` builds a
view instance through Django's `setup` lifecycle and runs its
boundary, it stamps the request with the `(mount token,
prepared view instance)` pair, and the `as_view` wrapper
dispatches on that instance instead of building a second one —
but only when the stamp is a well-formed pair whose token is
the wrapper's own mount, consuming it exactly once. The token
itself is created per mount in `as_view` (`mount = object()`,
`views.py:581`) and stamped on the callback (`:624`); the
middleware reads it back off the resolved callback (`:247`)
and re-stamps it into the request tuple (`:251`); the
`prepared_view` closure reads the tuple back, validates shape
plus token identity, deletes the stamp, and returns the
instance (`views.py:583`-`:588`). Both transport arms call
that one closure (`:605`, `:615`).

Whole-package sweep over all 117 HEAD `django_strawberry_framework/`
`.py` files (119 in the worktree, the extra two being the
untracked concurrent `utils/truth.py` plus `utils/lazy.py`)
for the mechanism vocabulary (`_BOUNDARY_PREPARED_VIEW`,
`_BOUNDARY_MOUNT`, `prepared_view`, `(mount`, `delattr(request`,
`setattr(request`, `getattr(request, _BOUNDARY`, `mount`):
every executable mechanism hit lands in the three indexed
files. One tuple construction exists (`middleware/request_body.py:251`),
one tuple validation (`views.py:585`), one request-targeted
`delattr` (`views.py:587`), one token creation (`views.py:581`).
The shadow candidates the sweep surfaced — the toolbar's
`_IS_GRAPHIQL` request tag, the `_BOUNDARY_ENFORCED` /
`_BOUNDARY_MARKER` / `_BOUNDARY_METHOD` marks, the sync/async
arm pairs, the recognition probe — are each discharged under
Findings with a contract difference. No module outside the
three indexed files packs, unpacks, validates, or consumes
the handoff, at HEAD bytes or at worktree bytes.

Attribution: every dirty hunk in the three indexed files was
diffed against `git show HEAD:<path>`, by content. The
`## Owned changes` ledger holds no production row on any of
them. `_boundary_ordering.py` is clean. `views.py` carries
three concurrent hunks, all at or above `:219` (the
truth-migration import plus `_resolved_max_request_body_bytes`
wording); the handoff region (`:578`-`:625`) is clean.
`middleware/request_body.py` carries seven concurrent
truth-migration hunks, one of which rewrites the pack's
mount-read lines directly above the pack the consolidation
must replace (recorded under F1 Coupling). The oracle file
`tests/test_views.py` is concurrently dirty too, including a
deletion of the O2 oracle in the worktree (recorded under
F1 Coupling as well). All of it is concurrent work, left
untouched. No `## Implementation (Worker-1)` section follows:
zero tracked files changed.

## Verification

### Matrix

1. Cross-flavor policy mirroring — discharged by the call
   census. The sync and async `as_view` arms do not mirror
   the handoff: both call the one `prepared_view` closure
   (`views.py:605` vs `:615`), defined once at `:583`. The
   middleware exposes one `process_view` hook for both
   chains (Django admits no async `process_view` twin), so
   the pack has no second color. The remaining transports
   carry no handoff surface: `consumers.py` (websocket, no
   middleware chain, zero mark hits), `testing/client.py`
   (drives views without a chain; an absent stamp takes the
   designed fresh path, zero hits), `middleware/debug_toolbar.py`
   (its only request write is the R7 boolean tag). No flavor
   re-spells the grammar.
2. Sync/async twins — no twin exists. The two view arms
   share the closure (axis 1); the `__call__` / `__acall__`
   twins (`middleware/request_body.py:164`-`:189`) publish
   only the `_boundary_middleware_request` ContextVar for
   the CSRF exemption and never touch the handoff (R5);
   the sync/async `parse_multipart` twins touch the
   lossy-field rejection, not the handoff. Compared by
   behavior: every colored path funnels through the same
   two grammar sites.
3. Derived rather than repeated knowledge — discharged by
   naming what each site derives. The tuple ORDER is known
   only at the pack (`(mount, view)`), the tuple INDEX
   roles only at the unpack (`[0]` token, `[1]` instance),
   and they agree by parallel spelling with no shared
   owner — that agreement is F1, not a derivation. The
   token VALUE is produced once (`views.py:581`) and
   threaded by identity through callback attribute, tuple,
   and closure scope, never re-materialized — which is why
   a token-representation change moves only the creation
   (C2). The `mount is not None` pack gate and the
   `delattr` consume are each single-sited policy (C4, C3).
4. Inverse / round-trip pairs — this axis IS the family.
   Pack (`middleware/request_body.py:246`-`:251`) and
   unpack-plus-validate-plus-consume (`views.py:583`-`:588`)
   are the two halves of one grammar with no shared
   executable owner: the only shared statement is prose in
   `_boundary_ordering.py` (a projection, not a body). A
   payload reshape must move both halves (C1, count 2).
   The neighboring stamp pairs belong elsewhere:
   `_BOUNDARY_ENFORCED` set/read is the verified-consolidated
   ordering family's completion record (R1), and the
   `_BOUNDARY_METHOD` probe/invoke pair is already
   single-owned through its constant (R2).
5. Contracts restated in another medium — oracles state
   expectations independently: O1
   (`tests/test_views.py:276`) stamps the literal 2-tuple
   `(mount, prepared)` and asserts dispatch-on-prepared
   plus single-consume, never reading any helper; O2
   (`:3238`, HEAD only — deleted in the worktree by the
   concurrent migration) pins the unreadable-mount skip;
   O3 (live,
   `examples/fakeshop/test_query/test_transport_api.py:3090`)
   proves the round trip end to end through a real chain
   (one `setup` per path). A reshape moves O1's literal
   but O1 stays an oracle: it must never be rewritten to
   read the helper (R8). Projections: the `_boundary_ordering.py`
   protocol prose (`:28`-`:34`) plus the `_BOUNDARY_MOUNT`
   / `_BOUNDARY_PREPARED_VIEW` comments (`:78`-`:85`), the
   `as_view` handoff paragraph (`views.py:556`-`:565`), and
   the O2 docstring. No `docs/` prose and no archived-spec
   prose states the tuple shape (zero `prepared view` hits
   outside the three modules plus the two oracle files).
6. Enforcement by omission — the callback population
   enumerated, every member checked: sync mount, async
   mount, consumer subclass overriding `dispatch`, and
   `wraps`-decorated callbacks all share the one closure
   (the decorator copies the same token object, so the
   identity match holds; live wrapped-mount rows cover
   it). Declined callbacks (non-package, unbuildable,
   unreadable-mount) take no stamp by design and keep the
   view-local arrangement — the contract source is the
   `_package_view_instance` docstring plus the
   `process_view` docstring's decline clause. Doubled chain
   entries keep the first pack through the `_BOUNDARY_ENFORCED`
   early return (pinned by
   `test_duplicate_boundary_entries_do_not_run_the_request_boundary_twice`).
   Websocket, test-client, and direct-`dispatch` paths
   carry no stamp; the closure's absent-input answer
   (`None`, fresh dispatch) is the designed fallback, and
   the handoff is documented as an optimization, not a
   dispatch invariant. No member lacks a guard its contract
   requires; F1 is a second spelling, not an omission.

### Enumeration

Family item: the sweep population stands in for a
file-member enumeration. Instruments plus counts (HEAD
bytes; prose mentions excluded from executable counts):

- `_BOUNDARY_PREPARED_VIEW` executable sites: 3 —
  write `middleware/request_body.py:251`, read
  `views.py:584`, delete `views.py:587`. Definition: 1
  (`_boundary_ordering.py:85`). Imports: 2 (`views.py:101`,
  `middleware/request_body.py:94`).
- `_BOUNDARY_MOUNT` executable sites: 2 — stamp
  `views.py:624`, read `middleware/request_body.py:247`.
  Definition: 1 (`_boundary_ordering.py:80`). Imports: 2.
  Token creation `mount = object()`: 1 (`views.py:581`).
- `(mount, view)` construction: 1
  (`middleware/request_body.py:251`). Validation triple
  (`type is tuple`, `len != 2`, `[0] is mount`): 1
  (`views.py:585`). `mount is not None` gate: 1
  (`middleware/request_body.py:250`). The worktree
  rewrites only the `:247` read line, not the shape.
- `prepared_view` closure: definition 1 (`views.py:583`),
  calls 2 (`:605` async arm, `:615` sync arm).
- `(mount` text hits: 2 in-family (the `:82` comment
  spelling the shape, the `:251` construction) plus 1
  false positive (`routers.py:153` prose, "mounted
  through its own `as_asgi`", excluded by reading).
- `setattr(request`: 3 package-wide — the handoff
  (`middleware/request_body.py:251`), the completion
  stamp (`:252`, R1), the toolbar tag
  (`middleware/debug_toolbar.py:246`, R7).
- `getattr(request, _BOUNDARY`: 4 — the handoff read
  (`views.py:584`) plus three completion reads
  (`_boundary_ordering.py:147`,
  `middleware/request_body.py:225`, `views.py:664`, R1).
- `mount`-token identity reads: `prepared[0] is not mount`
  1 (`views.py:585`).
- Oracles: O1 (`tests/test_views.py:276`), O2 (`:3238`,
  HEAD bytes; absent in the worktree), O3
  (`test_transport_api.py:3090`).
- Zero-hit exclusions on the full vocabulary over all
  117 HEAD files: `consumers.py`, `testing/client.py`,
  `_request_body.py`, `middleware/debug_toolbar.py`
  (except R7), and every other non-indexed module. The
  worktree sweep repeats the same three files (plus the
  two untracked concurrent files, which carry no
  mechanism hit).

### Challenges

Each change posited against the rule's variation axes;
only authoritative definitions counted.

- C1 (payload reshape): the pair gains a slot, drops
  one, reorders, or becomes a record type. Moves: the
  middleware construction (`:251`, order plus arity)
  plus the views validation and indexing (`:584`-`:588`,
  `type`/`len`/`[0]`/`[1]`). Count: 2. The prose in
  `_boundary_ordering.py` and O1's literal tuple move
  too, listed as projection plus oracle, not counted.
- C2 (token representation): `object()` becomes a uuid,
  a string, or any value type. Moves: the creation line
  (`views.py:581`) only. The `is not mount` check
  survives for ANY token type: the token is never
  re-materialized within a request (callback attribute
  to tuple to closure scope is the same object), so
  identity through the attribute chain is exact. Count: 1.
- C3 (consumption strictness): single-use `delattr`
  becomes multi-use, or exact-tuple validation becomes
  lenient-sequence. Moves: the closure (`views.py:584`-`:588`)
  only; the middleware never reads the stamp back.
  Count: 1.
- C4 (absent-mount policy): an unreadable or absent mount
  stamps anyway (a `None` token) instead of skipping.
  Moves: the pack gate (`middleware/request_body.py:247`-`:250`)
  only; the closure already answers `None` for a
  `None`-token pair (`None is not mount`), so its behavior
  is unchanged. Count: 1.

## Findings

### F1 — prepared-view handoff payload grammar (CONFIRMED, blocked-on-hunt)

- **Contract + variation.** The request-scoped pair the
  boundary middleware stamps and the `as_view` wrapper
  consumes: a 2-tuple `(mount token, prepared view
  instance)` under `_BOUNDARY_PREPARED_VIEW`, stamped
  only when the resolved callback carries a mount,
  consumed only when the stamp is an exact 2-tuple whose
  slot 0 is the consuming mount's own token, exactly
  once (`delattr`). Varies on payload shape (slots,
  order, container); the stamp-iff-mounted, match-iff-own,
  consume-once posture is the rule's fixed answer.
- **Sites + roles.** Definitions (2):
  `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`
  (`:246`-`:251`, guarded mount read plus conditional
  tuple stamp) and the `prepared_view` closure in
  `views.py::_RequestBodyBoundaryMixin.as_view`
  (`:583`-`:588`, read plus strict validate plus
  identity match plus `delattr` plus return). Neither
  invokes or derives from the other; they agree by
  parallel spelling. Consumers of the grammar (2, thin):
  the sync and async `as_view` arms (`:605`, `:615`),
  which call the closure rather than restating it.
  Oracles: O1 (match plus consume), O2 (pack skip,
  HEAD only), O3 (live round trip). Projections: the
  `_boundary_ordering.py` protocol prose plus mark
  comments, the `as_view` handoff paragraph.
- **Challenges.** C1 count 2 (the confirmation: order
  plus arity at the pack, `type`/`len`/index roles at
  the unpack, no shared owner). C2 count 1 (creation),
  C3 count 1 (closure), C4 count 1 (pack gate) — each a
  single-owned facet documented below, not a second
  definition of the grammar.
- **Owner + lifetime (principles 7, 4).**
  `django_strawberry_framework/_boundary_ordering.py`,
  via a pack helper plus a consume helper. It is the
  existing owner of exactly this protocol (the marks,
  the method name, the exemption, the prose); both
  grammar sites already import from it, so the migration
  adds no edge. `views.py` is excluded by dependency
  direction (principle 7: an owner its consumers cannot
  import is not one): the middleware must recognize and
  run the boundary without importing the view module,
  stated in both module docstrings. The middleware is
  excluded by responsibility: it owns *where* the
  boundary runs, not the protocol both ends share. The
  helpers are pure per-request functions. Stored-derivation
  lifetime for the stamp itself: owner, the
  boundary-ordering protocol; validity key, mount-token
  identity; publish point, `process_view` after the
  boundary passes; who may mutate, the two helpers only;
  invalidated, by the single-consume `delattr`.
- **Migration (deferred by the block).** The owner gains
  `stamp_prepared_view(request, view_func, view)` (the
  guarded mount read plus the conditional tuple stamp;
  the guard is re-derived against LANDED read bytes, see
  Coupling) and `consume_prepared_view(request, mount)`
  (read plus strict validate plus identity match plus
  `delattr` plus return), both standard-library-only
  with the request typed under `TYPE_CHECKING` exactly
  as the module's existing `ContextVar` annotation is.
  The pack block becomes one stamp call; the closure
  body becomes one consume call (the arms are untouched).
  Net about plus 30 helper lines with docstrings, minus
  10 call-site lines. Post-migration recount: C1 touches
  the two helper bodies — the two halves of one owned
  grammar in one module, one edit — and the two call
  sites become non-counted consumers; C2/C3/C4 each
  touch one body.
- **Distinct behavior.** Token creation (`mount =
  object()` plus the callback stamp, `views.py:581` /
  `:624`) stays in `as_view`: single site, single-owned
  on the representation axis (C2), and moving it would
  scatter the callback-stamping block. The `None`-gate
  skip and the single-consume travel with their halves
  into the helpers (they are the halves' stated policy,
  C3/C4). Boundary, `setup`, CSRF, and recognition
  behavior are untouched (R6, R9).
- **Behavioral proof.** `static-reviewed`: the pack
  output is exactly what the unpack accepts (slot order
  read against index roles, both bodies plus all three
  oracles read); the `None`-gate matches the
  absent-stamp fallback (O2 plus O1's fresh half); the
  `delattr` matches single dispatch (O1's `not hasattr`
  plus O3's one-`setup`-per-path); the `is` match is
  sound for any token type (never re-materialized, C2).
  `execution-deferred`: the post-block focused run (see
  `## Pending execution`).
- **Structural gate (deferred design, not landed).**
  Two spy gates: `stamp_prepared_view` called once by
  `process_view` on a recognized mount and never on a
  declined one; `consume_prepared_view` called by the
  dispatched callback, returning the prepared instance
  on a matching stamp and `None` otherwise. Negative
  control: a behavior-preserving hand copy of either
  helper body inline at its call site passes O1-O3 (the
  copy is correct) but fails the spy (the helper is
  bypassed). Landing any of it now would be born red —
  the helpers do not exist — so the gate travels with
  the deferred migration.
- **Coupling.** Blocked on concurrent non-ledger dirt:
  the pack's mount-read lines (HEAD
  `middleware/request_body.py:246`-`:249`, the
  `try:`/`getattr`/`except Exception` read inside hunk
  `@@ -243,10 +244,7 @@`) are rewritten in the
  worktree to `truth.static_attr`, contiguous with the
  clean `:250`-`:251` gate-plus-stamp lines the migration
  must replace — any edit merges into one hunk versus
  HEAD and is unattributable. The dirt matches no
  `## Owned changes` row and no cycle-baseline path; it
  is the concurrent truth-migration. Compounding it, the
  same migration deletes the O2 skip oracle in the
  worktree (`tests/test_views.py` hunk `@@ -3235,45
  +3102,6 @@`, HEAD `:3238`-`:3274`), so the unblocked
  migration must re-derive both the pack guard and its
  oracle against landed bytes. Nothing touched.
- **Freshness.** `_boundary_ordering.py` WT==HEAD
  `197eea8e` (clean); `views.py` WT `d1ff2aba` / HEAD
  `d627d5dd`; `middleware/request_body.py` WT `1febddbc`
  / HEAD `63a9a4a8`; oracles `tests/test_views.py` WT
  `a1de5141` / HEAD `715f3808`,
  `test_transport_api.py` WT `6d65274f` / HEAD `b1681e8c`.
  Full pins under `## Judgment`. Any fingerprint change
  reopens.
- **Reconsideration trigger.** The concurrent
  read-migration landing (committed) re-arms this
  consolidation: pack plus unpack route through the two
  owner helpers in one change, with the guard and the
  skip oracle re-derived against the landed read, or the
  family re-litigates against the landed shape. Durable
  home until then: this finding.

### R1 — completion stamp (rejected: consolidated family)

`_BOUNDARY_ENFORCED` (written `middleware/request_body.py:252`,
read `:225`, `views.py:664`,
`_boundary_ordering.py:147`) is a boolean completion
record owned by the verified-consolidated
`request-body-boundary-ordering` family. A handoff
reshape never moves a boolean stamp, and the closure
deliberately does not consult it: stamp presence, not
completion, licenses continuing on the prepared
instance. CONVERGE with that family's verified row.
Trigger: the stamp ever carrying payload — then it joins
F1's population.

### R2 — boundary method name (rejected: already single-owned)

`_BOUNDARY_METHOD` (defined `views.py:627`, probed
`middleware/request_body.py:345`, invoked `:239`) is
name-identity, not shape: all three sites read the one
constant, pinned by
`test_the_middleware_runs_the_boundary_it_probed_the_class_for`.
A tuple reshape never moves a name. Trigger: the name
ever varying per mount or per call site.

### R3 — marker presence bit (rejected: consolidated family)

`_BOUNDARY_MARKER` (stamped `views.py:623`, read
`middleware/request_body.py:339`) is a boolean
recognition bit from the same verified-consolidated
family as R1. Presence versus payload is the contract
difference. Trigger: the marker ever carrying more than
presence.

### R4 — transport arms (rejected: one closure, two callers)

The sync and async `as_view` arms (`views.py:601`-`:620`)
share the one closure by call; the `await` split is
transport, and O1 oracles the shared closure once. No
second grammar exists to count. Trigger: the arms ever
diverging in handoff handling.

### R5 — chain-presence publication (rejected: other family)

`__call__` / `__acall__` (`middleware/request_body.py:164`-`:189`)
publish the in-flight request into `_boundary_middleware_request`
for the CSRF exemption — the consolidated ordering
family's mark — and never read or write the handoff.
The verified File `_boundary_ordering.py` rejection of
boundary-versus-sibling-ContextVars stands,
trigger-checked (no handoff read added at HEAD).
Trigger: the exemption ever depending on the prepared
instance.

### R6 — callback recognition (rejected: producer, not grammar)

`_package_view_instance` (`middleware/request_body.py:256`-`:352`)
recognizes the callback and constructs the instance the
handoff then carries, but states no tuple grammar: it
never names `_BOUNDARY_PREPARED_VIEW` and never builds
or validates a pair. A reshape never moves recognition;
a recognition change (a new decline arm) never moves the
tuple. Trigger: recognition ever packing or validating
the handoff itself.

### R7 — toolbar request tag (rejected: memo, not handoff)

`_IS_GRAPHIQL` (`middleware/debug_toolbar.py`: written
`:246`, read `:283`) is the same mechanism — a request
attribute — carrying a different rule: a boolean,
persistent, same-module write-plus-read memo with no
token, no mount scoping, and no consumption. Cross-module,
token-scoped, single-use versus intra-module, unscoped,
persistent is the contract difference. Trigger: the tag
ever crossing modules, carrying a token, or needing
consumption.

### R8 — oracle tuple spelling (rejected: independence is the point)

O1 (`tests/test_views.py:301`-`:302`) spells the 2-tuple
literally and must keep doing so: an oracle that read
the helper it checks could not contradict a broken
owner (DRY.md Tests). Permanent separation on
principle, not conditional on any change; no trigger.

### R9 — carried policy (rejected: transport versus policy)

The handoff carries the instance; the cap, the encoding
refusals, and the boundary-run ordering on it are
`views.py` policy (spec-046 Decisions 7 and 9), and the
live O3 pins policy-through-handoff without pinning the
tuple. A handoff reshape never moves policy (the
boundary runs identically for callbacks that take no
stamp); a policy change never moves the tuple. The
handoff's own docstring states the split: it is an
optimization. Trigger: policy ever branching on handoff
shape — today `_enforce_request_boundary_once` branches
on the R1 completion stamp, never on the pair.

No sub-rule decomposed: token creation, consumption
strictness, and the absent-mount skip are single-owned
facets of F1 (C2/C3/C4), each without a second site
after the whole-package sweep — documented above, no
index row proposed. Worker-0 owns the index either way.

## Defects

None. Two examined-and-cleared notes, neither a defect:
the closure's defensive-ignore branches (a `len != 2`
stamp, a well-formed foreign-token stamp) have no direct
oracle — O1 exercises the matching pair plus the absent
(`None`) input, so those two `or` arms never evaluate
`True` under any oracle; statement-covered,
branch-unpinned, correct by reading, and the unblocked
migration owes branch-level oracles on the consume
helper. No already-ticked responsibility row was found
factually wrong; nothing reopened.

## Pending execution

- `proof: uv run python scripts/workspace.py run
  dry/viewhandoff-e9/consolidate -- pytest
  tests/test_views.py::test_async_as_view_dispatches_fresh_and_middleware_prepared_instances
  examples/fakeshop/test_query/test_transport_api.py::test_the_chain_applies_boundary_state_derived_during_view_setup
  -n0 --no-cov -q`
  (discharges F1's behavioral proof once the block
  clears; runnable only after the unblocked
  consolidation lands, joined by the landed successor
  of the O2 skip oracle if one exists then).
- Sharded cell: `inapplicable by construction`. PG cell:
  `inapplicable by construction`. Reason (Worker-2
  judges): the rule's executable surface is
  request/callback attribute reads plus writes plus
  tuple construction, validation, and identity
  comparison — no queryset, no database-alias read, no
  dialect branch exists in either half
  (`middleware/request_body.py:246`-`:251`,
  `views.py:581`-`:588` plus `:624`), so no cell can
  observe a different handoff.
- No `gate:` witness owed: a green unmutated suite would
  discharge nothing for a blocked finding.

## Judgment

The family is one real duplication with a specified but
unlandable migration. F1 CONFIRMED: the pack and the
unpack spell one payload grammar at two independent
sites (C1 count 2), with the same contract and the same
reasons to change; the owner is `_boundary_ordering.py`
(the middleware cannot import `views.py`, so dependency
direction decides between the dispatched candidates).
The migration — two helpers, two one-line call sites,
two spy gates — is fully specified above but BLOCKED on
the concurrent truth-migration's rewrite of the pack's
mount-read lines plus its deletion of the O2 oracle, so
zero files changed and nothing touched. Nine rejections
(R1-R9) each carry a concrete contract difference and a
trigger (R8's separation is principal, triggerless).
Single-owned facets (creation, consumption, skip) are
documented in F1, not rowed. No defect, no ticked row
disturbed.

Type gates (shared venv, tree-state — zero edits, so
these record the concurrently-dirty tree, not a
change): `uv run mypy` clean (119 files), `uv run
basedpyright` 0/0/0, `uv run python scripts/check_any.py`
130 uses at 90 sites (matches the run-9 baseline). Ruff:
VACUOUS — zero tracked paths touched (this artifact is
untracked `.md`, which ruff does not process); repo-wide
ruff correctly NOT run (it would surface concurrent
dirt). No workspace copy created (no source-mutating
proof ran); sweep probes were read-only greps plus
source reads in the shared tree, at HEAD bytes via
`git show` / `git grep HEAD` with a worktree-byte
confirmation sweep. The entry's one authorized focused
test was not spent.

Freshness (full input pins; `git hash-object` WT vs
`git rev-parse HEAD:<path>`; HEAD `5c3496e0`):

- Indexed 3: `_boundary_ordering.py` WT==HEAD `197eea8e`
  (clean); `views.py` WT `d1ff2aba` HEAD `d627d5dd`;
  `middleware/request_body.py` WT `1febddbc` HEAD
  `63a9a4a8`.
- Excluded on body strength: `middleware/debug_toolbar.py`
  WT `47b30dcd` HEAD `fb5f5549`; `consumers.py` WT
  `57d57b12` HEAD `06074640`; `testing/client.py` WT
  `594715cf` HEAD `690a4c70`; `_request_body.py` WT
  `b5484b64` HEAD `f6148ad5`.
- Contract sources: `tests/test_views.py` WT `a1de5141`
  HEAD `715f3808`;
  `examples/fakeshop/test_query/test_transport_api.py`
  WT `6d65274f` HEAD `b1681e8c`.
- Searched population: 117 HEAD package `.py` files
  (119 worktree files including the 2 untracked
  concurrent modules), whole
  `django_strawberry_framework/` tree, vocabulary
  `_BOUNDARY_PREPARED_VIEW`, `_BOUNDARY_MOUNT`,
  `prepared_view`, `(mount`, `delattr(request`,
  `setattr(request`, `getattr(request, _BOUNDARY`,
  `mount`, plus the `prepared view` prose sweep over
  `tests/`, `examples/`, `docs/`.

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

## Independent verification (Worker-2)

Run `0.0.15 2026-10-01-9`, item e9, address `dry/viewhandoff-e9/verify`.
`ITEM_BASELINE=73bec393832dbff22e94b4950146f9c8308e7a2c`, HEAD `5c3496e0` at
dispatch and at this pass. Part A below was recorded BEFORE opening
`## Findings` (the artifact's tail anchor was confirmed to be link scaffold
only); Part B reconciles after reading. Fingerprints: WT
`git hash-object` = `_boundary_ordering.py` `197eea8e`,
`views.py` `d1ff2aba`, `middleware/request_body.py` `1febddbc`;
HEAD blobs `197eea8e` / `d627d5dd` / `63a9a4a8`; ITEM_BASELINE blobs
`197eea8e` / `d1ff2aba` / `1febddbc` (WT == BASELINE on all three indexed
files; the views/middleware deltas vs HEAD are pre-baseline concurrent dirt).

### Part A — blind trace (expectation-first)

Population sweep (package-wide `grep` for `_BOUNDARY_MOUNT`,
`_BOUNDARY_PREPARED_VIEW`, `prepared_view`, `(mount,`, `delattr(request`,
`MOUNT`, `PREPARED` over `django_strawberry_framework/`): executable sites
exist ONLY in the three indexed files; no fourth site. Token-definition
site: `django_strawberry_framework/_boundary_ordering.py` L78-85
(`_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW` literals + protocol prose
L28-34) — role: name owner (already single). Pack site:
`django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`
WT L247-249 (`mount` read off `view_func`, `setattr(request,
_BOUNDARY_PREPARED_VIEW, (mount, view))`) — role: authoritative definition
of the pack half-grammar. Creation site:
`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.as_view`
WT L582 (`mount = object()`) + L625 (`setattr(view, _BOUNDARY_MOUNT,
mount)`) — role: single-owned token mint (one site only). Consume site:
`django_strawberry_framework/views.py::as_view.prepared_view` WT L584-589
(`getattr` + exact-`tuple` + len-2 + `[0] is mount` + `delattr` + `[1]`)
— role: authoritative definition of the unpack/validate/consume
half-grammar. Dispatch arms WT L604-621 call the one closure — role:
consumers, not definitions. Oracles (HEAD): O-async =
`tests/test_views.py::test_async_as_view_dispatches_fresh_and_middleware_prepared_instances`
(spells the `(token, instance)` tuple literally, asserts dispatch +
consume-once `delattr`) — PRESENT in WT (L276-306); O-guard =
`tests/test_views.py::test_middleware_ignores_an_unreadable_optional_mount_handoff`
(pins the pack's raising-mount-read guard: enforced-stamp set, no
`_BOUNDARY_PREPARED_VIEW` stamp, no raise) — PRESENT at HEAD (L3238) and
ABSENT in WT (deleted). Projections: `_boundary_ordering.py` module
docstring, both `as_view`/`process_view` docstrings.

Challenges (my counts): C1 payload-shape change (tuple order swap, arity
change, or container change, e.g. 3-tuple or dict): definitions forced =
2 (pack expression + unpack predicate: `prepared[0]`, `prepared[1]`,
len-2 arms); creation/compare facets do not move. C2 validation change
(exact-`type is tuple` -> `isinstance`, or dropping the len-2 arm): 1
(consume only; pack unaffected). C3 token-identity change (`is` ->
`==`): 1 (consume only). C4 mount-read failure semantics (guarded
read-with-`None`-fallback vs bare/static read): 1 (pack only). So the
family's grammar rule is count-2 on C1, count-1 on the three facet
changes: one CONFIRMED duplication (pack + unpack halves, same contract,
same reasons to change) with single-owned facets around it. Sync/async
arms: 1 definition (the closure), 2 consumer calls — not a twin.

Owner I choose: `django_strawberry_framework/_boundary_ordering.py` via a
pack helper + a consume helper, both views-side and middleware-side call
sites composing by name. Responsibility reasoning (principle 7): both
consumers already import it; it imports stdlib only; the middleware
MUST NOT import `views.py` (stated no-import rule in both module
docstrings: recognition without importing the view classes; views.py
pulls strawberry/django view machinery while the middleware is
instantiated from settings strings). Between the two dispatched
candidates, dependency direction is dispositive: an owner the
middleware cannot import is not one. `views.py` as owner would reverse
the documented dependency; `_boundary_ordering.py` exists exactly to
hold the two modules' shared protocol.

Matrix expectations: axis 1 cross-flavor — no second public surface
carries a prepared-view handoff (grep-clean). Axis 2 sync/async — one
closure, two callers; no twin bodies. Axis 3 derived knowledge — the
tuple is constructed once and validated once, not re-derived. Axis 4
round-trip — THIS family (pack/unpack). Axis 5 other media — oracles
O-async (survives) and O-guard (deleted in WT) + docstring prose. Axis
6 omission — the handoff is stamped only when `mount is not None`;
both transports consume through the same closure; no member lacks the
rule. Sharded/PG: inapplicable by construction — both halves touch
only request/callback attributes, closure state, and `object()`
tokens; no queryset, no alias, no dialect branch in either half.

Block pre-assessment (before reading W1's claim): the pack's WT mount-read
lines (`truth.static_attr` one-liner + docstring rewrite + the whole
`_package_view_instance` recognition rewrite + `truth.name` line) differ
from HEAD by truth-migration content and are byte-identical to
ITEM_BASELINE, i.e. pre-existing concurrent dirt. Any consolidation must
rewrite exactly those pack lines (pack call site) and re-pin O-guard
semantics; O-guard is deleted in WT so the guard-semantics proof has no
oracle. Landing only the `_boundary_ordering.py` helper half without the
pack call-site edit would add dead code, not relieve the C1 change
obligation (the pack would still spell the grammar); landing helpers +
the views-side consume edit alone (consume lines ARE byte-identical
HEAD==WT) would leave the grammar spelled in three places. Neither
partial landing is a consolidation. Zero-edit with a fully specified
migration is therefore the shape I expect; the `proof:` for the
unlanded consolidation must stay `execution-deferred` and the plan item
`verified, pending execution` iff the spec is complete.

### Part B — reconciliation and adjudication (after reading `## Findings`)

Reconciled EVERY Part A expectation against W1's record; differences: one,
immaterial. (1) Sites/roles: identical — pack
(`process_view`), unpack/validate/consume (`prepared_view` closure),
token mint (`mount = object()` + callback stamp), name owner
(`_boundary_ordering.py`), arms as consumers. (2) Counts: identical —
C1 reshape count 2, C2 token / C3 consume / C4 absent-mount count 1
each, same axes in the same order. (3) Owner: identical —
`_boundary_ordering.py` via pack + consume helpers, dependency direction
dispositive between the dispatched candidates; W1 additionally excludes
the middleware by responsibility (owns *where*, not the protocol) —
endorsed. (4) Oracles: W1's O1 = my O-async (survives WT L276), O2 = my
O-guard (HEAD L3238, deleted in WT by hunk `@@ -3235,45 +3102,6 @@`
— deletion claim HOLDS by content: the hunk removes exactly the
mount-guard test with the truth-migration's recognition-guard
deletions). The ONE delta: W1 enumerates a third oracle O3 (live
`test_transport_api.py::test_the_chain_applies_boundary_state_derived_during_view_setup`,
HEAD `:3090`, WT `:3092` — both verified present); my census had two.
O3 strengthens the proof set and moves no definition count (oracles are
never counted) — no verdict impact, W1's census is the fuller one.
(5) Block: AGREE fully. Pack dirt attributed BY CONTENT vs
`git show HEAD:<path>`: the mount-read rewrite (`try/getattr/except` ->
`truth.static_attr`), the `_package_view_instance` recognition rewrite,
the `truth.name` line, and the docstring rewrites are truth-migration
content; WT == ITEM_BASELINE on all three indexed files, so the dirt is
pre-baseline concurrent work, matching no `## Owned changes` row and no
cycle-baseline path. The migration must replace the read+gate+stamp
block spanning the dirty `:247` line — contiguous with clean lines, so
any edit merges into one hunk vs HEAD and is unattributable; the
helpers-only half would be dead code (pack still spells the grammar)
and the consume-side-only half would leave three spellings (consume
lines are byte-identical HEAD==WT, verified). Unlandable now, not
partially landable. (6) R1–R9: each carries a concrete contract
difference + trigger; all nine pins re-verified exact at HEAD bytes
(incl. R2's `:627`/`:345`/`:239`, R1's stamp sites, R6's range). R8
triggerless-principal: ENDORSED — DRY.md Tests already forbids
rewriting an oracle to read its owner, so no future change merges O1
into the helper; a trigger would be invented. R1/R3 CONVERGE claims
accepted (both name the verified ordering family; no ticked row
disturbed — nothing reopened). (7) Matrix: all six axes discharged
against the real surface; axis-6 contract sources named
(`_package_view_instance` + `process_view` docstrings, doubled-chain
row); my expectations match on every axis. (8) Enumeration: instrument
+ counts re-verified — 117 tracked + 2 untracked (`truth.py`,
`lazy.py`) = 119; `setattr(request)` 3, `getattr(request, _BOUNDARY` 4,
`(mount` 2 in-family + `routers.py` prose false positive excluded by
reading, `delattr(request` 1 — all match at WT bytes modulo the known
dirty-file shifts. (9) `proof:` typing: CORRECT — one `proof:` entry
(O1 + O3 node IDs both verified present in WT), `execution-deferred`,
runnable only post-migration; no `gate:` owed; plan item goes
`verified, pending execution`. (10) Cells: `inapplicable by
construction` ENDORSED — both halves verified alias- and dialect-free
(request/callback attributes, tuple, identity; creation + stamp lines
included). (11) Structural gates + negative control: specified (two
spies + hand-copy control that passes O1–O3 and fails the spy),
correctly deferred — landing now would be born red. (12) Zero-edit
gates RE-VERIFIED: no `## Implementation` header (one prose mention,
L80); 3/3 WT pins match dispatch pins (`197eea8e`/`d1ff2aba`/`1febddbc`);
`git diff ITEM_BASELINE --name-only` = `docs/dry/dry-0_0_15.md` alone
(43-insertion dispatch + submission record); `git status --short` = 457
with this artifact untracked; HEAD unmoved at `5c3496e0`. (13)
Freshness: every pin re-derived and comparable — indexed 3 (WT+HEAD),
excluded 4 (WT+HEAD), oracle files 2 (WT+HEAD), population + vocabulary
stated; all match. (14) AGENTS.md prose: tracked diff holds no
production edit; artifact is per-cycle scratch (raw `path:NN` allowed,
no cleanup owed). Ruff: VACUOUS — zero tracked paths touched (this
artifact is untracked `.md`); repo-wide ruff correctly not run.
(15) Defects: none found by W1 (2 examined-and-cleared notes endorsed:
the `or`-arm branch pins are owed to the unblocked migration, correct
by reading); none found by Worker-2 — no `(Worker-2)` `## Defects`
entry. Execution: shared venv (`uv run`) for all probes and gates;
read-only greps + `git show` reads; no workspace copy (no
source-mutating proof); slots 1–3 untouched. Type gates RE-RUN
whole-package just now: `uv run mypy` clean (119 files), `uv run
basedpyright` 0/0/0, `uv run python scripts/check_any.py` 130 uses at
90 sites — all three match the run-9 baseline exactly.

Verdict: `verified` (plan item: `verified, pending execution`, one
`proof:` remaining). No revision candidate exists: the only consolidation
is specified and correctly blocked; no standing disagreement.
