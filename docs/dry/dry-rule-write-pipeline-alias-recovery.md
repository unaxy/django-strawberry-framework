# DRY review: `write-pipeline-alias-recovery`

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

The rule: a `using: str | None = None` parameter left omitted recovers the
active mutation write pipeline's pinned alias (`current_write_pipeline()` →
`.alias`); with no pipeline active it stays `None` and the lookup keeps the
historical default-manager behavior. Lenient posture throughout: absence is a
fall-through, never an error.

### Site inventory (fresh trace at current bytes, WT + HEAD)

| Site | Lines | State | Role |
|---|---|---|---|
| `relay.py::_resolve_real_pk` recovery block | WT `:315`-`:323`, HEAD `:294`-`:304` | HEAD-committed shape (comment + `if` + 2 lines); WT moves only the import (hoisted to `:79`) | Definition D-a |
| `relay.py::_resolve_real_pks_batched` recovery block | WT `:404`-`:406` | Whole function WT-added (`:372`-`:422`), zero HEAD lines | Definition D-b |
| `relay.py::decode_model_global_id` | WT `:425`-`:469` | Composes D-a (`:466`); WT-reshaped around it | Consumer (single primitive) |
| `write_values.py::type_check_relation_id` | WT `:164` (HEAD `:161`, byte-identical call, no `using`) | Committed shape | Consumer (single relation decode → recovery) |
| `write_values.py::decode_visible_relation_ids` batched call | WT `:353` (no `using`) | WT-added review dirt | Consumer (set decode → D-b recovery) |
| `mutations/resolvers.py::coerce_lookup_id` | WT `:1405` (`using=using`, threaded) | Threads explicitly; see R6 | Adjacent (documents the split, `:1380`-`:1384`, committed) |
| `write_transaction.py::current_write_pipeline` | WT `:699`-`:701` | Pipeline-state owner | Mechanism owner |
| `write_transaction.py::open_write_pipeline` / setter | WT `:279` / `:271` | Sole `WriteAliasContext` construction site | Lifecycle entry (axis 4) |
| `write_transaction.py::pipeline_scoped_queryset` | WT `:1195` read | Pin + conditional lock | Excluded (R2) |
| `utils/querysets.py` seal pin + `required_alias` | WT `:4457`-`:4464` | Visibility-seal routing | Excluded (R3) |
| `require_write_pipeline` consumers (7) | mutations ×3, rest_framework ×2, write_transaction ×2 | Fail-loud posture | Excluded (R1) |
| `write_transaction.py` phase-guard closure | WT `:620` capture, `:629` test | SQL phase gating | Excluded (R4) |
| `filters/base.py` GlobalID decode | read surface | No alias touched | Excluded (R5) |

Oracles: `tests/mutations/test_resolvers.py:330`
`test_custom_node_id_real_pk_lookup_uses_pinned_alias` (HEAD `:322`, origin
`1842c6b6`; pins explicit-`using` forwarding — adjacent to recovery, not on
it; 1/1 green this run); live
`examples/fakeshop/test_query/test_multi_db.py:1212`
`test_custom_nodeid_mutation_resolves_real_pk_on_write_alias` (file clean, so
HEAD-identical; root-id path, explicit threading end to end); WT-only
`test_custom_node_id_relation_set_mapping_uses_pipeline_alias` in
`tests/utils/test_write_values.py` (batched-recovery pin, uncommitted review
dirt — cited as in-flight, not as evidence). Observation, not defect: no
committed test pins the recovery branch's alias choice (single-site,
`using=None` inside a pipeline); the branch is line-covered by every relation
decode inside a mutation but alias-unobservable on one database.

Projections: `1842c6b6` message (origin contract: wrong-database lookup
reported not-found for an existing row); `mutations/resolvers.py:1380`-`:1384`
prose (thread-vs-recover split rationale, committed); relay docstrings;
`docs/review/review-0_0_15.md` WT `:230` + `:815` (review relay-F1
implementation record — WT text, corroborated below).

### Attribution (by diff content vs `git show HEAD:<path>`)

D-b, `_decode_and_coerce`, the `slot` threading (`_coerce_pk_or_none`,
`_resolve_real_pk`, batch loop), the `current_write_pipeline` import hoist
(L1), the `isawaitable` guard reshapes (F2), and the surrounding prose are
review-flow relay-F1 WT dirt: the review record names exactly these symbols;
`git log --all -S_decode_and_coerce` is empty (no commit anywhere holds them);
blobs `f5760b45` + `13548c76` cited by that record exist in the object store
but are reachable from no ref (dangling implementation snapshots on an older
base); the DRY `## Owned changes` ledger names `relay.py` once (adopted
`typed-globalid-decode` trigger, verified present WT `:454`-`:457`, absent at
HEAD — content-distinct, coexisting); the cycle baseline names no package
file. Same file, other hunks: `truth.*` reads, the `truth`/`lazy` imports,
and the `_stamp_node_type` rework are hunt truth-migration dirt. The F1
migration below must edit D-b's lines and lands in this file, so both dirt
layers block it independently; nothing is touched.

Connected behavior examined: the adjacent seed rule (Family
`queryset-seed-and-model-read` F1 — same block, see Coupling); single-vs-batch
mapping parity (both first-match-wins — the mapping rule, out of scope, left
to review F1's pins); the pipeline lifecycle (one sync skeleton
`run_write_pipeline_sync`, ridden at 5 call sites across 4 flavors —
mutations ×2, forms, rest_framework, auth — so every color recovers
sync-side).

## Verification

### Matrix

1. **Cross-flavor mirroring** — searched, no third site. Instruments:
`using is None` over the package = 2 hits, both `relay.py` (`:315`, `:404`);
`decode_model_global_id(` callers = 2 (`mutations/resolvers.py:1405`
explicit, `write_values.py:164` recovering); `current_write_pipeline` code
sites = 4 (2 recovery + 2 pinning); rider call sites of the one skeleton
= 5 across 4 flavors, all composing the shared decode primitives. Filters'
GlobalID decode is a read surface with no alias (R5).
2. **Sync/async twins** — searched, no twin. One `run_write_pipeline_sync`
definition; no `run_write_pipeline_async` exists; `relay.py`'s only async
bodies (`_gather`, `_await_and_stamp`) never touch recovery. Recovery always
executes sync-side inside the skeleton every color rides.
3. **Derived knowledge** — the recovery derivation (omitted `using` →
ambient alias) is the only duplicated one. `pipeline.alias` reads = 12
lines: relay ×2 (the finding), rest_framework ×4 (both inside
fail-loud `require_` bodies — R1), write_transaction ×4 (phase test + pin
read + pin + lock — R4 + R2), querysets ×2 (seal pin + `required_alias` —
R3).
4. **Round-trip pairs** — inapplicable with reason. The alias is *set* by
lifecycle entry (`WriteAliasContext(` constructed once, at
`write_transaction.py:271` inside `open_write_pipeline`), never spelled, so
no encode/decode grammar pair exists to unify; recovery reads ambient state,
it does not invert a spelling.
5. **Other media** — censused, no second definition. Origin message
(`1842c6b6`), 2 committed adjacent pins + 1 live row + line coverage (oracles
above), 2 committed prose sites + WT review record (projections above). The
`mutations/resolvers.py:1383` prose describes the split; it does not
re-implement recovery. Definitions counted separately: 2.
6. **Enforcement by omission** — caller census complete, no gap. Both
`decode_model_global_id` callers are covered (explicit-thread `:1405`,
recover `:164`); the batched caller (`:353`) recovers; the single primitive
(`:466`) recovers. No NodeID decoder runs inside a pipeline with neither
threading nor recovery.

### Challenges

| Id | Change posited | Definitions forced | Count |
|---|---|---|---|
| C1 | Recovery source change (pipeline exposes a read/write alias pair; recovery must take the write member) | D-a + D-b (each spells the read + fall-through inline) | 2 |
| C2 | Absence-posture change (omitted `using` with no pipeline fails loud instead of default-manager fall-through) | D-a + D-b | 2 |
| C3 | `using`-shape change (a third state, e.g. pin-or-fail sentinel) | D-a + D-b (both branch on `is None`) | 2 |
| C4 | Boundary discriminator: batched-only mapping-shape change (per-group query rewrite), recovery untouched | Neither (mapping bodies, not recovery definitions) | 0 |

C4 (count 0) proves the rule boundary: recovery vs NodeID→pk mapping are
adjacent but separate obligations; only C1–C3 move the recovery pair, and
always together.
A grep for the recovery population (`current_write_pipeline`) also returns
the pinning sites (R2/R3), while a grep for the seed population misses D-b
entirely — the drift vector in both directions.

## Findings

### F1 — write-pipeline alias recovery (CONFIRMED duplication, blocked)

- **Contract + variation.** A supplied `using` passes through; an omitted
  one recovers the ambient pipeline alias when a write pipeline is active,
  else stays `None` (standalone default-manager behavior). Varies on pipeline
  present/absent and supplied/omitted only. Fixed: lenient posture (absence
  never raises), read-at-decode-time (no caching across the decode).
- **Sites + roles.** Definitions (2): D-a (`relay.py::_resolve_real_pk` WT
  `:315`-`:323`) and D-b (`relay.py::_resolve_real_pks_batched` WT
  `:404`-`:406`) — same question, same shape; D-b's missing comment is prose
  absence, not a contract difference. Consumers: the single primitive, both
  relation decoders (single + batched), and transitively every flavor rider.
  Oracles / projections: as inventoried above.
- **Challenges.** C1 = 2, C2 = 2, C3 = 2, C4 = 0 (boundary discriminator).
- **Owner + lifetime (principle 7).** New private
  `relay.py::_recovered_write_alias`: both consumers are local, so it is the
  narrowest cohesive owner; no dependency changes (the `current_write_pipeline`
  import already sits at WT `:79`); dependency direction stays clean either
  way. A cross-module third recovery site re-homes it beside
  `current_write_pipeline` — that re-homing *is* the family trigger below.
  Pure derivation per call: no stored state, no lifetime owed.
- **Migration (deferred by the block; byte-exact).** Immediately preceding
  `_resolve_real_pk`, add:
  `def _recovered_write_alias(using: str | None) -> str | None:` returning
  `using` when not `None`, else `None if (pipeline :=
  current_write_pipeline()) is None else pipeline.alias`; its docstring
  carries D-a's six-line relation-rider comment once (that comment moves, not
  copies). D-a `:315`-`:323` and D-b `:404`-`:406` each become the one-liner
  `using = _recovered_write_alias(using)`. Net about −9 lines. Both move
  together or not at all: migrating D-a while D-b stays inline trades
  twin-consistency for a new divergence (same refusal as e8 F1). Tests in the
  same change at `tests/test_relay_node_field.py` (the relay module's test
  home, already importing relay privates): a 3-arm owner test (explicit
  passthrough / pipeline recovery / standalone `None`, the last two via
  `open_write_pipeline` + a `manager.using` spy in the `:330` style) plus one
  spy composition test per decoder. Package tier is justified by the `:330`
  precedent (alias unobservable on one database; the live sharded suite owns
  end-to-end).
- **Distinct behavior.** Untouched: the NodeID→pk mapping (first-match both
  colors), the seed shape (e8 F1 owns it), queryset pin/lock (R2), seal
  routing (R3), fail-loud entry (R1), explicit threading (R6).
- **Behavioral proof.** `static-reviewed`: branch-by-branch parity — omitted
  + no pipeline yields the default manager at both sites (D-a via
  `base_queryset(model, None)`, D-b by skipping `.using()`); omitted + active
  pipeline yields `using=alias` at both (modulo the seed-shape delta e8 F1
  owns); supplied passes through at both (the `if` guards recovery).
  `execution-deferred`: the `proof:` entry below, verdict-bearing only after
  the unblocked migration lands. Anchor (not discharge): the committed `:330`
  pin runs 1/1 green at current bytes (see Implementation).
- **Structural gate (specified, unlanded).** The spy composition pair: each
  decoder test patches `relay._recovered_write_alias` and asserts the call.
  Negative control: a behavior-preserving hand copy of the helper body at one
  decoder passes every oracle and fails that decoder's spy. No AST census: a
  raw `current_write_pipeline()` census counts 3 post-migration (helper + the
  two pinning sites) across two contracts it cannot tell apart; the spy can.
- **Coupling.** e8 F1 (seed) is blocked on the same dirt; both migrations
  re-arm together when review F1 lands, and landing re-keys every line number
  above. Blocking hunk (exact): `relay.py` WT `:332`-`:424` (the `+` run of
  hunk `@@ -310,6 +329,99 @@` — content `:332`-`:422` plus two blanks —
  holding D-b's `:404`-`:406`), plus the hunt truth-migration hunks in the
  same file — either layer stops the item alone.
- **Freshness.** `HEAD 23b5f421`; `ITEM_BASELINE
  d769fc25327dec20df789346ef9ba0a962d4105c` (stash-capture commit on
  `23b5f421`, `WIP on (no branch)`); `relay.py` WT `9257a51b` / HEAD
  `025f2a6a` / ITEM_BASELINE `9257a51b`; `write_transaction.py` WT
  `50909be8` / HEAD `2b9f861c`; `querysets.py` WT `e6660894` / HEAD
  `4d8a3d39`; `write_values.py` WT `1dc426d4` / HEAD `a9d6fa32`;
  `mutations/resolvers.py` WT `9171b93f` / HEAD `bb6c630d`;
  `rest_framework/resolvers.py` WT `4d05a330` / HEAD `14ffc9c8`;
  `tests/mutations/test_resolvers.py` WT `4d9a03cc` / HEAD `9dd13c73`;
  `tests/test_relay_node_field.py` WT `5764374e` / HEAD `70e59815`;
  `tests/utils/test_write_values.py` WT `f033e5ca` / HEAD `f812e5ad`.
  Drift since ITEM_BASELINE: `docs/dry/dry-0_0_15.md` +29 only (dispatch
  rows). Census instruments + hit counts above are the searched-population
  fingerprint (Python `3.14.8`, Django `6.1.2`, per the proof run header).
  Any fingerprint change reopens.
- **Reconsideration trigger.** Review F1 landing (committed) re-arms this
  consolidation whole; a third recovery site, or a recovery-semantics change
  (C1–C3 firing), re-opens the rule — and re-homes the helper beside
  `current_write_pipeline` when that site sits outside `relay.py`. Durable
  home until then: this finding.

### R1 — `require_write_pipeline` consumers (rejected)

Fail-loud vs lenient: every `require_` site (mutations ×3, rest_framework
×2, write_transaction internals ×2) raises `ConfigurationError` with no
pipeline, while recovery falls through to `None`. Merging the postures would
fail either the standalone decoders (raise where fall-through is the
contract) or the pipeline internals (tolerate a wiring bug). Trigger: a
lenient caller needing fail-loud or vice versa. Specified home: the new
helper's docstring contrast clause.

### R2 — `pipeline_scoped_queryset` pin + lock (rejected)

Queryset-in/queryset-out (fail-closed re-route pin + conditional `FOR UPDATE`
lock) vs `using`-string-out for a fresh lookup. Different inputs, outputs,
and failure modes; the pin site never produces an alias a lookup could take.
Trigger: a pin site needing a `using` string instead of a queryset.
Specified home: helper docstring.

### R3 — seal pin + `required_alias` (rejected)

Visibility-seal routing (`utils/querysets.py` WT `:4457`-`:4464`): pins an
existing sealed queryset and reports the alias downstream seal checks must
see. Recovery sources an alias for a *fresh* default-manager lookup outside
any seal. Trigger: the seal path sourcing an ambient alias for a fresh
lookup. Specified home: helper docstring.

### R4 — write-phase SQL guard (rejected)

Phase gating (`write_transaction.py` WT `:620` capture / `:629` test):
captures the pipeline once to reject write SQL outside the write phase on the
already-pinned connection. It consumes the pinned alias's *phase*, never
sources an alias. Trigger: the guard needing a recovered alias. Specified
home: helper docstring.

### R5 — filters GlobalID decode (rejected)

Read surface: `filters/base.py` decodes + validates a GlobalID for filtering
without touching any database alias — no pipeline exists on reads, so there
is nothing to recover. Trigger: filters needing a pipeline-aware lookup.
Specified home: helper docstring.

### R6 — `coerce_lookup_id` explicit threading (rejected)

Intentional two-shape split, committed prose at
`mutations/resolvers.py:1383`: the root-id caller already holds the alias
(`require_write_pipeline().alias` at `:1094`) and threads it explicitly, so a
second context-variable read there "could only ever return the same answer".
Threading (caller knows) vs recovery (rider cannot thread) differ by
contract, not by accident. Trigger: `coerce_lookup_id` losing its explicit
alias — it then becomes the third recovery site and fires F1's trigger.
Specified home: helper docstring, beside the moved rider comment.

## Defects

None. Examined and cleared (not defects): no committed test pins the
recovery branch's alias choice — a gap note living in F1's oracle record,
owed its pins by the post-block migration, not a code bug; single-vs-batch
first-match parity holds by construction (DB order both sides) under review
F1's pins — the mapping rule, out of scope.

## Pending execution

- `proof: uv run python scripts/workspace.py run dry/aliasrec-f63/consolidate
  -- pytest tests/mutations/test_resolvers.py::test_custom_node_id_real_pk_lookup_uses_pinned_alias
  -n0 --no-cov -q` (discharges F1's behavioral proof once the block clears
  and the migration + spy pair land: the committed pin stays green under the
  composed helper; validated runnable at baseline — 1/1 green in the shared
  tree this run; runnable for verdict only after the unblocked consolidation
  lands, when the new pin nodes join it).
- Sharded cell: `unverified` (cell unauthorized; the live `:1212` row and any
  future live recovery row need `FAKESHOP_SHARDED=1`). `inapplicable by
  construction` is NOT claimed: the rule is alias/database behavior.
- Postgres cell: `unverified` (cell unauthorized). Not inapplicable: same
  reason — alias routing, not a pure derivation.

## Judgment

CONFIRM-blocked. The write-pipeline alias recovery is one rule with two
`relay.py` definitions (C1–C3 = 2, C4 = 0 boundary discriminator); the
pin/lock, seal, fail-loud, phase-guard, read-surface, and explicit-threading
spellings are each excluded on a re-derived contract difference with a
trigger. Owner re-derived as a new `relay.py` private (both consumers local;
a cross-module third site re-homes it — the family trigger). The migration —
helper beside the decoders, two one-line compositions, moved rider comment,
3-arm owner test + spy pair — is specified byte-exactly but unlanded: D-b
lives entirely in review-F1 WT-added lines and the host file carries hunt
truth-migration hunks, recorded hunk-exact above. Zero edits, zero defects,
one validated proof entry, both cells `unverified` (cells unauthorized;
inapplicable correctly not claimed).

## Implementation (Worker-1)

No tracked changes (blocked, zero edits by rule — see the blocking hunk under
F1). No `## Owned changes` rows, no new tests, no spec/doc updates owed (no
behavior changed; every projection moves only with the migration). No ruff
runs owed (no `.py` touched); `check_public_types.py` not run (no public
symbol touched).

Evidence runs (all through `heavy`; machine GREEN and `pgrep` clean before
the set; `heavy` serializing it):

- Focused proof validation (the entry's one authorized shared-tree run):
  `heavy uv run pytest
  tests/mutations/test_resolvers.py::test_custom_node_id_real_pk_lookup_uses_pinned_alias
  -n0 --no-cov -q` → 1 passed in 5.62s.
- Type gates as tree-state (zero edits, so these record the tree, not a
  change): `heavy uv run basedpyright` → 0 errors, 0 warnings, 0 notes;
  `heavy uv run basedpyright -p pyrightconfig.floor.json` → 0 errors, 0
  warnings, 0 notes; `heavy uv run python
  scripts/check_truthful_reads.py --check` → 120 files checked, errors 0
  (tier-2 28, markers 17).
- No `workspace.py` copy created (no source-mutating proof exists for a
  zero-edit item; slot-2 path issued at this address, copy never synced);
  the `proof:` entry above runs there after the block clears.

Worker-0 transcriptions: index row `write-pipeline-alias-recovery` → status
`open, blocked (F1 CONFIRMED count-2, migration + spy gate specified, zero
edits; review-F1 WT dirt + hunt hunks in host file)`; no new index rows (R1–R6
separations live in the F1 record + specified helper docstring); Families
queue item f63 stays open pending the unblock.

## Independent verification (Worker-2)

Recorded before opening `## Findings` below (pass 1, fresh trace at current
bytes: HEAD `23b5f421` + WT; ITEM_BASELINE `d769fc25` consulted for the
three-state pin only).

### Own trace: the rule

A `using: str | None = None` parameter left omitted recovers the active
mutation write pipeline's pinned alias and stays `None` when no pipeline is
active (default-manager behavior). Lenient posture: absence falls through,
never raises.

### Own trace: sites + roles

- D-a — `django_strawberry_framework/relay.py::_resolve_real_pk`, the `if
  using is None:` recovery block: DEFINITION. Executable lines committed at
  HEAD (local import since hoisted to module top by WT dirt); the recovery
  spelling itself is byte-stable across HEAD → ITEM_BASELINE → WT.
- D-b — `django_strawberry_framework/relay.py::_resolve_real_pks_batched`,
  the `if using is None:` recovery block: DEFINITION. The whole function is
  WT-added (0 matches at HEAD, present at ITEM_BASELINE and WT); same three
  executable lines as D-a minus the comment.
- `django_strawberry_framework/utils/write_transaction.py::current_write_pipeline`:
  the contextvar-read primitive both spellings compose; a definition of the
  read, not of the recovery rule (consumer-side from this family's view).
- Consumers: `relay.py::decode_model_global_id` (calls D-a),
  `utils/write_values.py::decode_visible_relation_ids` (calls D-b),
  `utils/write_values.py::type_check_relation_id` (via the single primitive),
  `mutations/resolvers.py::coerce_lookup_id` (threads `using` explicitly, so
  D-a's recovery arm is not exercised there).
- Oracles: `tests/mutations/test_resolvers.py::test_custom_node_id_real_pk_lookup_uses_pinned_alias`
  (single, threaded-`using` path; committed at HEAD),
  `tests/utils/test_write_values.py::test_custom_node_id_relation_set_mapping_uses_pipeline_alias`
  (batched recovery under an active pipeline; WT-added, absent at HEAD),
  `tests/test_relay_node_field.py` decode-contract tests (mapping behavior).
- Projections: the recovery comments/docstrings in `relay.py`, and the
  `mutations/resolvers.py` docstring recording the deliberate explicit-thread
  separation at the root-`id` seam.
- Excluded on body strength (each read in full): `pipeline_scoped_queryset`
  (queryset pin + conditional row lock, no `str | None` alias resolution),
  `require_write_pipeline` (absence raises, never falls through),
  `utils/querysets.py` sealed-visibility pin site (queryset-level pin with
  owner string + `required_alias` bookkeeping),
  `rest_framework/resolvers.py` pipeline sites (pipeline already held via
  `require_write_pipeline`, direct `.alias` use, no recovery).

### Own trace: challenges + counts

- C1 (no-pipeline fallback changes: `None` → router default): 2.
- C2 (absent-pipeline posture changes: lenient → raise): 2.
- C3 (alias source changes: how the alias is read off the pipeline): 2.
- C4 boundary discriminator (pk-mapping query shape changes —
  `.first()`/single-row vs `__in` grouping semantics): 0. Moves the mapping
  rule both functions also carry, never the recovery rule.

### Own trace: owner choice

`django_strawberry_framework/utils/write_transaction.py`: it owns the
`_WRITE_PIPELINE` contextvar, the None-on-a-read-surface contract, and the
pipeline lifetime, and `relay.py` already imports from it, so no dependency
reverses. Shape: one `using: str | None` → `str | None` resolver beside
`current_write_pipeline`, both relay sites composing it by name. A
`relay.py`-internal helper is an acceptable narrower alternative (both
consumers in-module); the contextvar + None-contract ownership breaks the
tie toward `write_transaction.py`.

### Own trace: block assessment

The consolidation must rewrite D-b's recovery lines (entirely WT-added,
unattributed: absent from `## Cycle baseline`, and the ledger's sole
`relay.py` row covers only the adopted `typed-globalid-decode` trigger
docstring) and add the owner helper in a dirty-external file (`relay.py` or
`write_transaction.py`, both carrying unattributed hunt/feature hunks vs
HEAD). No re-route avoids touching D-b: a count-2 consolidation requires
both sites to compose. Provisional verdict: blocked, zero-edit stands.

### Reconciliation with `## Findings`

Read after the trace above. Agreement on every verdict-driving claim: the
rule contract + lenient posture; D-a/D-b identity, WT/HEAD states, and
definition roles; C1–C3 = 2 with C4 = 0 as the boundary discriminator;
consumers (single primitive, both relation decoders, transitive flavor
riders); oracles (committed `:330` pin, live `:1212` row, WT-only batched
pin cited as in-flight); projections; R1–R6 coverage with a contract
difference + trigger each; the block (D-b WT-added, hunt hunks in host
file); zero-edit; both cells `unverified` with inapplicability correctly
not claimed; the `proof:` typing; the specified spy gate + negative control;
coupling; and no defects.

Difference 1 — owner choice (resolved in Worker-1's favor). I chose
`utils/write_transaction.py` (contextvar ownership); Worker-1 specifies a
new `relay.py` private. Principle 7 prefers an existing owner with the
responsibility, else the narrowest cohesive owner: no existing symbol owns
the `using: str | None` resolution (the pipeline module owns the read, the
raise, and the queryset-pin applications — each rejected here with its own
trigger), and both consumers live in `relay.py` with the import already
present, so the module-internal helper is the narrowest owner with no
dependency change. My alternative paragraph already admitted this; the
third-site re-homing trigger covers future growth. The unblocked item
re-derives ownership anyway.

Difference 2 — supporting-census corrections (transcribed here, e8
precedent; verdict-neutral, not code defects, hence not under `## Defects`):

- M3 "`pipeline.alias` reads = 12 lines" is overstated: the literal
  instrument returns 10 (relay `:323` + `:406`; rest_framework ×4;
  write_transaction `:1198` + `:1200`; querysets ×2), and the
  write_transaction "×4 (phase test + pin read + pin + lock)" parenthetical
  names `:629` + `:1195`, which contain no `.alias`. Allied reads under
  other receivers (mutations `:1094`, `:1185`; write_transaction `:434`)
  sit inside `require_` bodies and belong to the R1 family. Coverage is
  intact: every pipeline read is censused in M1 (4 code sites) and each
  non-recovery shape carries its rejection; the `using is None` = 2 census
  independently closes the recovery population.
- R1 "(7)" undercounts: 8 `require_write_pipeline()` call sites exist
  (mutations `:342`, `:1094`, `:1168`; write_transaction `:306`, `:430`,
  `:1126`; rest_framework `:1515`, `:2317`). The eighth (`:1126`, the
  serializer target-state snapshot check) shares R1's fail-loud contract,
  so the rejection's reasoning covers all 8.
- The review-snapshot blobs are NOT "reachable from no ref": `git rev-list
  --all --objects` lists `f5760b45` (relay.py) and `13548c76`
  (write_values.py) from a `dry-backup` snapshot ref. The load-bearing
  half stands on my re-run (`git log --all -S_decode_and_coerce` empty; 0
  HEAD matches; ledger/cycle-baseline absent), and the review record's
  symbol inventory (`:230`, `:815`) matches the WT hunks verbatim — the
  "review-flow WT dirt" attribution holds.
- Freshness gap cured: `filters/base.py` (R5, excluded on body strength)
  carries no fingerprint in F1. Supplying: WT `77c2e7a6` / HEAD `a43513a7`
  / ITEM_BASELINE `77c2e7a6` (stable across the item window); body
  re-verified (no `pipeline`/`using`/alias reference outside one prose
  "six-layer pipeline" line).

Probes the brief ordered: (i) C4 holds — the recovery blocks (WT `:315`–
`:323`, `:404`–`:406`) are line-disjoint from the mapping bodies, so a
mapping-shape change moves 0 recovery definitions. (ii) No feasible
recovery-semantics change moves exactly one: the only asymmetric candidate
(batched goes fail-loud) is infeasible because D-b's leniency serves
standalone set-decode callers (the docstring-stated default-manager
fall-through, exercised without a pipeline). (iii) D-b's WT-added status
changes landing, not counting: the trace is at current bytes, D-b is
present at ITEM_BASELINE, and e8 F1 counted the same WT-only twin the same
way.

Gate re-runs in my copy (`dry/aliasrec-f63/verify-1`, slot-3, synced after
Worker-1's submission, shared tree unmoved): basedpyright all-mode 0/0/0;
floor 0/0/0; truthful-reads 120 files, errors 0 (tier-2 28, markers 17) —
all match Worker-1's tree-state record. Shared-tree anchor re-run:
`test_custom_node_id_real_pk_lookup_uses_pinned_alias` 1 passed. Ruff:
touched `.py` paths = {} (zero-edit), so no ruff run owed — stated
explicitly; the artifact itself is source-layout-exempt (0 violations).
Item-scoped diff re-verified empty at verdict time; status count 521.

Verdict: `verified`. The artifact keeps one `proof:` entry, so Worker-0
marks the plan row `verified, pending execution`.

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
