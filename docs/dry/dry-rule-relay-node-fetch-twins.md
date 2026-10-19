# DRY review: `relay-node-fetch-twins`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Pairs in [types/relay.py][types-relay] (WT/HEAD bodies byte-identical):
single `:1023-1066`/`:963-1006` vs `:1069-1091`/`:1009-1031`; bulk
`:1094-1139`/`:1034-1079` vs `:1142-1165`/`:1082-1105`.
`ITEM_BASELINE`↔WT target diff empty (`test_keyset.py` window dirt is
concurrent-external). 22 HEAD hunks attributed, none in the four bodies
or `_apply_node(s)_filter`; `_order_nodes`, `_raise_if_required`,
`_node_value(s)`, `_coerce_node_id` held (foreign truth hunks inside).
Per-pair table: deadline once in entry (async covered); `id_attr` once,
threaded; single coercion hoisted, bulk via shared `_node_values`;
visibility sync vs `await ..._async` (must differ: sync cannot await,
async must await consumer hooks); shared `_apply_node(s)_filter`;
terminals `get`/`first` vs `await aget`/`afirst`, `list(qs)` vs `async
for` + shared `_order_nodes`. Restated beyond color: 3-line None guard
(single), `if node_ids is None` shape with color-differing arms (bulk),
non-None strip + `coerced_keys` (bulk, each 2x). Errors symmetric except
sync-only `SyncMisuseError`; permission not decided here (visibility
hook scopes; permission layers elsewhere). Census over 121 files: no
third node-fetch spelling (R1 classifies each candidate).

## Verification

### Matrix

1: write-locate, relation re-check, write decode+map read — distinct
contracts, not mirrors. 2: this item — color-forced, table above.
3: `id_attr`/slot resolved once and threaded; keys derived 2x (H1).
4: emit (`resolve_id`) vs fetch, decode vs fetch — distinct halves;
`global_id_for` consumes `encode_typename`. 5: spec-015 Decision 9
(async shapes), spec-032 Decisions 4/5 (batch shape) agree with
bodies; oracles spell literals (listed, never counted); zero
spec sentences falsified (zero-edit). 6: deadline/coerce/visibility/
required enforced on every fetch arm incl. `None` paths (single has
no order by construction); `locate_instance` takes pre-decoded pks,
no gap.

### Challenges

- C1 key grammar (new normalization): 3 sites (2 twin comprehensions +
`_order_nodes` index) — confirmed, fix spans held code (H1); twin-only
hoist leaves count 2, fails the bar, not landed.
- C2 required-miss error: `_raise_if_required` + `_order_nodes` arm (both
held); `get`/`aget` misses Django-owned; bodies compose by name (H1).
- C3 deadline semantics: `check_deadline` owner, count 1 (trigger:
deadline must be observed inside async context — implausible, it reads
`info.context`).
- C4 fetch policy: `apply_type_visibility_*` pair (querysets family),
bodies unchanged; post-materialization variant = 4 enforcement sites
(terminals must differ), not definitions.
- C5 short-circuit semantics: 2 guard sites over shared
`_raise_if_required` — idiom, below bar (R2).
- C6 single-vs-bulk (bulk chunking): bulk only — 2 rules sharing
kernels, not 1 rule in 2x2.

## Findings

### R1 (rejection): sync/async node pairs are color-forced twins

- **Contract + variation.** Two fetch rules (single: `get`/`first`;
bulk: queryset-or-ordered-list) × two colors. Shared pure decisions:
deadline, `id_attr`, coerce kernel, required-raise, id filter,
reorder — each one definition, several hoisted above the branch.
Varies only by color dispatch + materialization (await points, ORM
terminals), which must differ: sync cannot await consumer `async
def get_queryset` (refuses `SyncMisuseError`), async must await it.
- **Sites + roles.** Definitions: 4 bodies + 7 shared helpers
(deadline/coerce×2/raise/filter×2/order; slot/coerce owned in
[root-relay][root-relay]). Consumers: root `DjangoNode(s)Field`
resolvers (by-name classmethod calls; own decode-gate +
batch-assembly — run-18 `relay-gather-vs-sync-loop` rejection),
Strawberry `relay.node()`/`nodes()` (`required=not is_optional`,
await-if-awaitable), `GlobalID.resolve_node`. Distinct rules: write
decode+map (outcome codes, no rows), upstream row-mapper (3
connection sites, row→object), `testing/relay` (no fetch),
`locate_instance` (alias pin, lock, miss→None — documents the
parallel), `_visible_related_object` (object-in, no
decode/coerce/deadline). Oracles listed, both colors.
- **Challenges.** C3/C4/C6 count 1; C1/C2 held (H1); C5 idiom (R2).
- **Owner + lifetime.** Here, beside the coerce/order halves
(principle 7; same home as file-local `types-relay-node-fetch-
defaults`). Per-request; sync inline, async returns an awaitable.
- **Migration.** None — zero-edit. One body + adapters refused: the
branch cannot vanish (some line must `await`-or-not) and a
maybe-await adapter is barred by standing contract
(`normalize_query_source` docstring); two colored bodies sharing
pure decisions is the DRY.md-5 sanctioned shape (connection
precedent). R9 trigger (Strawberry separate slots) unfired —
installed Strawberry still one-slot + await-if-awaitable. R16
trigger (shared sets coincide) unfired — window/page/seal disjoint.
- **Distinct behavior.** Color dispatch + materialization stay per
body; single vs bulk stay 2 rules; key/required grammars stay
twinned pending H1; pair-A guard stays per body (R2).
- **Behavioral proof.** execution-verified: both node oracle files,
172 passed, both colors (found/required/order/holes/uncoercible/
async-hook-awaited — each rejects a real wrong result). Negative
control: sync-color `SyncMisuseError` refusal oracles, both arities,
green in the same run.
- **Coupling.** None. **Freshness.** Target WT `3b4447ae`;
`test_relay_interfaces.py` `5c5ed7fe`; `test_relay_node_field.py`
`122d5398`; HEAD `c37a08a0`; baseline `5288401b`; population 121
package files via `rg`; contracts spec-015 Decision 9, spec-032
Decisions 4/5, installed Strawberry `relay/fields.py` + `types.py`.

### H1 (held): key + required-miss grammars span held helpers

Key grammar (`None`-hole + `str`) lives at 3 sites: the 2 twin
`coerced_keys` comprehensions (HEAD-clean) + the `_order_nodes`
index (held). Required-miss message at 2: `_raise_if_required` +
the `_order_nodes` arm (both held). Specified migration (record-
only): `_order_nodes` takes raw `values` and computes keys beside
its index (2 call sites pass `values`, comprehensions deleted);
required-miss arms keep homogeneous construction with the message
owned once. Trigger: truth-migration hunks in `_order_nodes`/
`_raise_if_required` land (lines HEAD-clean) → fresh item lands the
migration with both-color order/hole/required oracles + key-grammar
failability. No edits now: `_order_nodes` carries a foreign hunk.

### R2 (rejection): pair-A None guard stays twinned (below bar)

The 3-line `if value is None: _raise_if_required; return None`
shape is identical in both single bodies, but the logic (raise vs
`None`) is already single-owned by `_raise_if_required`; the sites
carry control-flow idiom, not definitions. The available hoist
(moving the guard above the branch) narrows `_resolve_node_async`
to non-`None` values — a latent filter-by-`None` fail-open for any
future caller — and shifts async+required+uncoercible from
await-time to call-time raise (outcome-identical for Strawberry's
call-then-await shape and every in-repo caller, still a timing
refinement). Cost exceeds a 3-line idiom. Trigger: a second
operation accretes in either guard, or the guards drift — then hoist
with a both-color uncoercible oracle pinning the raise point.

## Defects

None. Key/index agreement is by parallel construction, pinned by
both-color order/hole oracles; fragility rides H1, not a defect.

## Judgment

Run-18 hunt-note verified with an own table: twins share every pure
decision and differ only where color forces. No third spelling in
121 files. One bar-passing unification specified but held on foreign
dirt (H1); all else rejected with triggers. Zero-edit, 172/172 green.

## What shrinks

- Rule: node-fetch color twins (single + bulk pairs).
- Change: none landed (rejection R1/R2 + held migration H1).
- Owner: `django_strawberry_framework/types/relay.py`, unchanged.
- Net package lines over `ITEM_BASELINE 5288401b`: 0 (target diff
empty; only this artifact added, untracked).
- Machinery attestation: no new helper, driver, registry, mode flag,
or contract reshape — none added, none needed; the refused shapes
(one-line `_coerced_keys` helper, maybe-await adapter, mode-flagged
unified filter) each obscure ownership per principles 5/7/11.
- Held projection: H1 deletes the 2 twin `coerced_keys` lines and
relocates key computation beside the index (net ~0, definitions 3→1).

## Independent verification (Worker-2)

Own pre-findings trace (WT): single entry runs deadline →
id_attr → coerce → dispatch → None-arm → visibility_sync →
node-filter → get/first; async sibling runs None-arm →
visibility_async → node-filter → aget/afirst. Bulk entry runs
deadline → id_attr → dispatch → None-arm → values →
visibility_sync → nodes-filter → keys → order; async mirrors
with awaited visibility + async-for. Shared (1 def each):
check_deadline, _node_value_or_none, _node_values,
_raise_if_required, _apply_node_filter, _apply_nodes_filter,
_order_nodes; id_attr once + threaded, deadline once above
branch. Restated beyond color: 3-line None guard (pair A),
None-queryset arm (pair B, arms differ by color), non-None
strip + coerced_keys (pair B, 2x each). Challenges:
fetch-policy → 2 bodies but color-forced (sync ORM vs await
points, no shared spelling sans thread/await change); deadline
→ 1; batching/key-norm → 2 one-liners + index, below bar;
error-message → 1 (+ H1-held order arm). Pre-read verdict:
reject, zero-edit.

Reconciliation: all 7 singles verified single + shared
(call-site census); color-necessity verified — sync core under
sync_to_async cannot await consumer async get_queryset and
moves ORM across the thread boundary (principle-8 observable
change); maybe-await barred by normalize_query_source
docstring; connection.py two-body precedent governs (must
await hooks) vs write-pipeline one-body (no txn interleave).
No material difference from R1/R2/H1; C1–C6 counts concur.

Consolidation hunt (own, 7 candidates, all fail):
coerced_keys/non-None hoists → twin-only leaves count 2
(index held), single-expression, below bar (trigger: H1
fires); pair-A guard → idiom over shared helper, hoist narrows
async contract + shifts raise timing (trigger:
accretion/drift); None-queryset arm → arms differ by color;
dispatch preamble → per-pair entry, sharing needs a driver
(barred); root holes vs order → interleave vs reorder,
distinct; required triple → distinct miss causes. None
above-bar.

Matrix: axis 2 is the question; axes 1/3/4/5/6 judged sound
(distinct contracts / threaded+H1 / halves distinct / specs
agree + literal oracles / every arm enforces). Third spelling:
relay.py entries (own decode-gate, by-name dispatch),
connection row→object mappers, testing helpers (no fetch),
locate/re-check/write-map — each classification verified.
Triggers firable (installed Strawberry one-slot +
await-if-awaitable confirmed; H1 via HEAD-clean; R2 via arm
diff). Byte-identity re-diffed: 4 bodies + 2 filters identical
(9e75e276/4cf70ddb/efb8def7/79d21e36, ed37902b/29a758c2); 5
helpers differ (foreign truth hunks, correctly held).
Pending-absent correct (zero-edit). Coupling: H1 outcome does
not affect this verdict (keys only, color split stands) —
non-blocking. Freshness pins match (3b4447ae, 5c5ed7fe,
122d5398, c37a08a0, 121 files). Prose/shape hold (150-line
body, :NN allowed in dry-*.md, Run line, 10 link groups). No
Python touched → no ruff. No pytest re-run (zero-edit:
byte-identity + census are the evidence; suite-green is the
gate's). Defects: none (agree).

Verdict: verified — zero-edit rejection stands; H1 carried.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[root-relay]: ../../django_strawberry_framework/relay.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
