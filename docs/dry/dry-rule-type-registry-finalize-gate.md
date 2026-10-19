# DRY review: `type-registry-finalize-gate`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `type-registry-finalize-gate`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry` (F5 aspects).
Member files: `django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/finalizer.py`,
`django_strawberry_framework/types/base.py`,
`django_strawberry_framework/mutations/sets.py` (all four read in full at
the gate-relevant sections; `HEAD` is `bfaee91d`; `ITEM_BASELINE` is
`039cb41e4b8ec9aeb7e1935650e57ff006415520`: item-scoped diff on all four
family paths vs the baseline is byte-empty, confirmed). The
`mutations/sets.py` worktree dirt vs `HEAD` (5 hunks, all
`__name__`-to-`_safe_class_name` message rendering, none on the gate
lines) is content-attributed external concurrent work — never edited,
so no attribution stop triggered. Registry core + `types/*` clean
(confirmed). Prior records used only as triggers, never verdicts: the
registry file item's F5 aspects (`docs/dry/dry-file-registry.md`,
verified) + the four verified siblings (`type-registry-enum-cache`,
`type-registry-definition-store`, `type-registry-pending-ledger`,
`type-registry-model-type-map` — their F1/F2/F3/F4/F5 boundary
statements checked, not inherited; the definition-store item's R-E
trigger names this family as its home and is adjudicated below as
R-B). Never read any `worker-memory/`.

## System trace

Rule: the finalize gate — the entry guard plus the per-type finalized
flags that together ensure every registered type resolves exactly once
and re-finalize is safe. `finalize_django_types()` runs four phases
(Phase 1 pending-drain, Phase 2 resolver attach, Phase 2.5 interface /
Relay / connection-synthesis / mutation-form-filter-order binds, Phase 3
`strawberry.type` decoration). The whole-registry `_finalized` flag
makes a second successful call a silent no-op; the per-definition
`finalized` flags let a retry after a partial failure skip
already-decorated types and resume from the failing entry; the
`mark_finalized()` tail flip runs only after every Phase-3 decoration
returns, so any raise leaves the gate open.

Boundary against the sibling families on the one class (re-derived,
agrees with all four siblings): F1 owns `_types` / `_primaries` /
`_models` plus `register` / `unregister` map arms / `get` and friends;
F2 owns `_definitions` plus the atomic pair and both accessors; F3 owns
`_pending` plus identity-matched add/iter/discard; F4 owns `_enums`
plus the pair; F5 owns `_finalized` plus `is_finalized` /
`mark_finalized` / `_check_mutable` plus the per-type `finalized`
semantics (storage lives on [definition][definition], the rule lives
here — the same split the definition-store item records as its R-E).
The `_finalized = False` reset inside `clear()` and the
`_check_mutable()` refusals inside `unregister` / `register` /
`register_definition` / `register_type_teardown` / `add_pending_relation`
/ `discard_pending` / `register_enum` are those lifecycles consuming F5
state, not second definitions.

Sites + roles. *Definitions* (one each, probe-pinned S1–S5): the
`_finalized` flag (1 construction, 1 tail flip, 1 reset, 1 guard read);
`is_finalized` / `mark_finalized` / `_check_mutable` (1 def each);
the `if registry.is_finalized(): return` entry line
([finalizer][finalizer] single line); the `registry.mark_finalized()`
tail line (single line); the `definition.finalized = True` flip line
(single line, Phase-3 loop); the six `if definition.finalized:
continue` skip lines (one per phase loop). *Producer*: the finalizer
(sole flip site; sole tail-flip caller). *Consumers*:
`DjangoType.__init_subclass__` (post-finalize refusal, [base][base]);
the mutation declaration `register` (post-finalize refusal,
[mutation-sets][mutation-sets]); the mutation / form / filter / order /
auth binds (Phase-2.5 drain riders, no done-flag of their own);
[testing-relay][testing-relay]`::global_id_for` (finalized-first read
order); the inspect command (unfinalized display branch);
[definition][definition]`::related_target_for` (cache validity key —
populates the memo only when the gate reads true, so pre-finalize
mutation can never lock in a transient `None`). Code-call census of
`is_finalized()`: exactly 4 ([base][base] refusal,
[definition][definition] validity key, [finalizer][finalizer] entry,
[mutation-sets][mutation-sets] refusal; all other hits are docstrings).
`mark_finalized()` code calls: exactly 1 (the tail line). *Step guards*
(intentionally separate, R-B/R-C): `effective_globalid_strategy`
non-`None` (Relay install re-entrancy); the synthesized-connection
field marker (synthesis re-entrancy). *Oracles*:
[test-registry][test-registry] (double-finalize decorates once,
pre-marked skip, post-finalize registration refusal, clear-then-fresh
pair ×2, Phase-3-failure recovery, Phase-1 retention + retry,
mutator-refusal pack, unregister-after-finalize refusal),
[test-orders-finalizer][test-orders-finalizer] (second call no-op),
[test-relay-interfaces][test-relay-interfaces] (audit-raise rerun
preserves strategy, resolver idempotence), [test-relay-connection][test-relay-connection]
(refinalize synthesis pair), [test-mutation-sets][test-mutation-sets] /
[test-form-sets][test-form-sets] /
[test-serializer-sets][test-serializer-sets] (bind retry-idempotence
trio), [test-filters-finalizer][test-filters-finalizer] /
[test-orders-finalizer][test-orders-finalizer] (owner rebind
idempotence), [test-testing-relay][test-testing-relay] (unfinalized
refusal), [test-definition-order][test-definition-order] (ambiguity
before unresolved; multi-cycle edges),
[test-finalizer][test-finalizer] (missing-definition typing). All spell
literals independently; none enumerates the owner. *Projections*: the
finalizer module docstring (gate contract: entry guard, per-entry
skips, tail flip, partial-recovery path), the `finalize_django_types`
docstring (same contract at the call site), the registry guard +
`clear` + `unregister` docstrings, the `DjangoTypeDefinition`
finalized-once clause, [spec-018][spec-018] (ambiguity audit),
[spec-031][spec-031] (setting snapshot + Decision-10 re-entrancy),
[spec-032][spec-032] (connection synthesis), [spec-036][spec-036]
(mutation bind), [spec-027][spec-027] / [spec-028][spec-028] (sidecar
subpasses + retry), [spec-040][spec-040] (auth bind slot). The live
compose sibling is
[test-schema-composition][test-schema-composition] (successful build;
package-side lifecycle rows stay here per the registry test-module
charter).

Connected sources read for judgment, outside the members:
[definition][definition] (flag storage + finalized-once +
strategy-guard clauses), [trelay][trelay] (install step + step-0
guard), [relations][relations] (sentinel shape behind the B3 probe),
[testing-relay][testing-relay] + inspect bare-name resolver (flag
readers, consumer role), `filters/sets.py` single-threaded contract
(no-lock anchor), `orders/sets.py` normalization ledger (lock owner —
a per-resolution ledger, excluded on strength of body),
`schema.py` / `routers.py` locks (unrelated layers). Excluded on
strength of body: every other package module (zero `is_finalized` /
`mark_finalized` / `_finalized` / `definition.finalized` vocabulary
over the 117-file sweep; `optimizer/plans.py`
`finalized_*` hits are plan-cache vocabulary, not the gate).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The mutation / form /
serializer declaration ledgers (`make_declaration_registry` twins)
are pre-bind, per-flavor, disjoint declaration lists drained at
Phase 2.5 — a different subject (declared operations) from
build-done bookkeeping (R-E). Filter / Order sidecar binds ride the
same window through `_bind_sidecar_sets`; none keeps a done-flag of
its own (clear-and-rebuild is the retry mechanism). No flavor keeps
a second finalize gate (package sweep: `is_finalized` /
`mark_finalized` 1 def each; `_finalized` touched only in
[registry][registry]).
2. **Sync/async twins.** Zero `AsyncFunctionDef` in all four members
(AST-verified: registry 30/0, finalizer 42/0, base 32/0,
mutation-sets 48/0). Collection / finalize / drain are import-time
dict + class-attr work; no ORM I/O, no awaits. Trigger: a gate
method touching the DB or awaiting.
3. **Derived rather than repeated knowledge.** The step guards read
data, not duplicate done-facts: `effective_globalid_strategy`
records the classification string (R-B); the synthesis marker
records field-attach state (R-C). Collapsing either into
`definition.finalized` loses a state the retry path distinguishes
(proved B6 + N2-adjacent reasoning).
4. **Inverse / round-trip pairs.** mark/is/clear-reset;
finalize/retry/resume; decorate/skip; guard/refuse (entry no-op vs
mutator raise — R-D). All pinned by oracles below.
5. **Contracts restated in another medium.** Production (owner pair +
sole flip site + six skip consumers); oracles (independent
literals, plain classes + real models, no owner reads);
projections (docstrings verified against bodies; specs pin the
audit, snapshot, synthesis, and bind shapes). No consumer restates
"done": every site reads the owner.
6. **Enforcement by omission.** `_check_mutable` guards every direct
mutator (`register`, `register_definition`,
`register_type_teardown`, `add_pending_relation`,
`discard_pending`, `register_enum`, `unregister`); `clear()`
bypasses by its documented test-only contract;
`get_definition` / `iter_definitions` / `get` and friends are
deliberately unguarded pure reads — post-finalize request-time
resolution requires reads through the finalized snapshot. No
member lacks a guard its contract requires: no defect.

### Enumeration

Instrument: `ast.parse` def/call/assign/if census over the four
members + token sweeps over the 117-file package population
(`git ls-files django_strawberry_framework | grep -c` = 117,
re-counted). Every gate member assigned; every challenge ends in
the family row or a recorded rejection (no file-local row).

- `is_finalized` / `mark_finalized` / `_check_mutable`: exactly 1
  def each (S1). `_finalized`: 1 construction, 1 tail flip, 1
  reset, 1 guard read — all inside [registry][registry] (package
  sweep; no second gate def anywhere).
- Entry guard `if registry.is_finalized(): return`: exactly 1 line
  (S2). Tail `registry.mark_finalized()`: exactly 1 call (S3).
  `definition.finalized = True`: exactly 1 code site, Phase-3
  loop (S4; the module-docstring mention is prose).
- `if definition.finalized:` skips: exactly 6, one per phase loop
  (synthesis, Phase 2, Relay, field-surface audit, Phase 3,
  sidecar subpass 1) (S5).
- `threading` / lock vocabulary in `registry.py` +
  `finalizer.py`: zero (S6; single-threaded by design, R-F).
- Relay step guard: exactly 1 (S7). Synthesis marker check:
  exactly 1 (S8). `bind_mutations` def + finalizer call: 1 + 1
  (S9). Mutation declaration post-finalize guard: 1 (S10).
  `testing/relay.py` finalized-first read: 1 (S11).
- `effective_globalid_strategy` writes: exactly 2 lines, both
  inside `install_globalid_typename_resolver` (one function,
  step-local).

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace probes S1–S11/B1–B7
map one-to-one onto C1–C8 (40/40 `execution-verified`); negative
controls N1/N2 proved by mutation.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Finalize twice | **1** (entry guard; per-type flags 0 moved — the second call returns before any loop). Oracles: `test_finalize_is_idempotent`, the orders second-call row. Probe B1. |
| C2 | New phase (a fifth loop over definitions) | **1** (the same flag composed by name; the flip stays 1; the new loop owes the skip as a consumer — S5 grows by one enforcement site, not one definition). |
| C3 | Concurrent finalize from two threads | **1 decision** (documented no-lock single-threaded design at [registry][registry] + the filters/sets contract; zero lock vocabulary on the path — S6). No lock owed: the production path is import-time single-threaded, so a lock guards no reachable contention (GIL vs explicit never arises). Trigger: a request-path finalize (R-F). |
| C4 | `clear()` then re-finalize | **1** (`clear()`'s `_finalized = False` reset; the vacuous re-finalize then flips the tail). Oracles: the clear-then-fresh pair ×2. Probes B4/B5. |
| C5 | Collapse entry guard + per-type flags into one "done" fact | **2 intentionally separate** (THE consolidation question — rejected F1: whole-build no-op vs per-entry skip-and-continue; different granularity, different observable behavior). |
| C6 | Replace the entry guard with `_check_mutable` | Rejected (R-D: silent no-op vs loud refusal; N1 shows the backstop fires exactly there). |
| C7 | Collapse the Relay step guard into `definition.finalized` | Rejected (R-B: fires the definition-store R-E trigger and is adjudicated here — a retry with strategy recorded but `finalized = False` would reinstall and misclassify `custom`). Probe B6. |
| C8 | Give the mutation bind its own done-flag | **0** (no flag exists; clear-and-rebuild is the mechanism — R-E). |

**Experiment (executed, disposable workspace).** Copy per [dry][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/finalize-gate-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_finalize_gate.py
```

Proof (`CHECKS_PASSED=40/40`): gate/accessor/skip/step-guard/
bind-consumer singularity censuses, double-finalize decorates once
+ returns `None`, pre-marked skip with build flip, Phase-1 raise
(retained pending + untouched sentinel annotation + retry rewrite +
drain), Phase-3 failure (gate + flag false, partial class marks,
clear + fresh recovery), clear-then-refinalize, Relay step-guard
rerun no-op without misclassification, post-finalize refusal at
both layers. Status: `execution-verified`. Rejects "a second gate
exists", "double finalize re-decorates", "Phase-1 failure records
progress", "the step guard re-installs", "the bind keeps a flag".
Copy `__file__`:
`.../dry-ws/finalize-gate-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/finalize-gate-w1/examples/fakeshop/db.sqlite3` (copy's
own tree and database; never the shared tree; the probes open no DB
at all). No source mutation in the proof; searched population
inside the copy: 117 `.py` (matches the shared tree).
`grep -c truncated` == 0.

**Negative control N1 (executed, disposable workspace).** Backed up
the copy's `finalizer.py`, replaced the entry guard with
`if False:`, re-ran: fails exactly at `S2-entry-guard-once` +
`B1` — the second finalize raises `ConfigurationError` from the
`discard_pending` `_check_mutable` backstop instead of returning a
silent no-op (exit 1). Restored the backup (md5 identical),
re-ran: 40/40. The standing idempotence oracle
(`test_finalize_is_idempotent`) pins the same contract in the
suite. Status: `execution-verified`.

**Negative control N2 (executed, disposable workspace).** Removed
only the Phase-3 `if definition.finalized: continue` skip,
re-ran: fails exactly at `S5-pertype-skip-count` (6→5) +
`B2-no-decorate` (pre-marked type re-decorated; attach-skip and
build-flip unaffected) (exit 1). Restored (md5 identical),
re-ran: 40/40. Status: `execution-verified`.

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "finalize or
mark_finalized or mutators_reject or unregister_raises_after_finalize
or clear_allows_fresh or pending_set_is_cleaned or
registering_concrete or finalize_discards"` → 10 passed (the gate
oracle pack: idempotence, pre-marked skip, Phase-3 recovery,
clear-then-fresh ×2, mutator refusal, unregister refusal, pending
retention + retry, post-finalize registration refusal,
consumer-authored discard).

## Findings

### F1 — finalize gate (REJECTED consolidation: single-owned, overlaps intentionally separate)

- **Contract + variation.** Whole-build done (entry guard: second
  successful call is a silent no-op) plus per-entry done (flags:
  retry skips decorated types and resumes). Varies on: all-decorated
  (no-op) vs partially-decorated (skip-and-continue) vs never-run
  (full build); drop-all (`clear()`) vs drop-one (`unregister`,
  pre-finalize only). Never varies on hierarchy or reader: every
  site reads the owner.
- **Sites + roles.** *Definitions*: the flag + guard + flip +
  six skips (one each, S1–S5). *Producer*: the finalizer (sole
  flip + tail-flip site). *Consumers / oracles / projections*: as
  listed in System trace.
- **Challenges.** C1 → 1; C2 → 1; C3 → 1 decision; C4 → 1;
  C5 → 2 separate; C6/C7/C8 → rejected/0. Count > 1 nowhere in
  one rule: no duplication.
- **Owner + lifetime (principles 7, 4).**
  `django_strawberry_framework/registry.py::TypeRegistry` (F5
  aspects) stands: narrowest cohesive owner every consumer can
  import without reversing a dependency ([base][base] and
  [finalizer][finalizer] already import the registry at module
  top; [definition][definition] reaches it only in-function for
  exactly this reason). Stored-derivation lifetime, both flags:
  `_finalized` validity = tail flip → `clear()` (publish point =
  last line of `finalize_django_types`; who may mutate =
  `mark_finalized` (finalizer tail only) + `clear()` (test-only
  reset); reads = entry guard + declaration refusals);
  `definition.finalized` validity = Phase-3 decoration →
  `clear()`-discard of the definition (publish point = the single
  Phase-3 line; who may mutate = the finalizer only; reads = the
  six skips + `global_id_for` + inspect); terminal state =
  all-flags-true plus gate-true, or gate-false with Phase-3
  progress recorded per entry and Phase-2/2.5 progress recovered
  by step idempotence.
- **Migration.** None (zero-edit rejection: no behavior hunk, no
  test hunk; every durable home below already exists).
- **Distinct behavior (stays separate).** Entry no-op vs per-entry
  skip (C5); silent no-op vs loud refusal (C6/R-D); recorded
  classification vs done-flag (C7/R-B); field-attach state vs
  type-done (R-C); operation binding vs build-done (C8/R-E);
  documented no-lock vs guarded mutation (C3/R-F).
- **Behavioral proof.** `execution-verified` for singularity
  censuses, decorate-once + silent no-op, pre-marked skip +
  build flip, Phase-1 atomicity + retry, Phase-3 recovery,
  clear-then-refinalize, step-guard rerun, dual-layer refusal
  (workspace 40/40 + N1 + N2 + the authorized 10-passed focused
  run). `static-reviewed` for the zero-`async` census, the zero
  second-gate sweep, docstring-vs-body prose, and oracle-body
  independence (plain test classes + real models; none reads the
  owner). Observable behavior pinned: second finalize decorates
  nothing and raises nothing; retry resumes from the failing
  entry; any raise leaves the gate open; `clear()` re-arms the
  whole gate. Rejects every duplication direction in C1–C8.
- **Structural gate.** Deferred with reason: a behavior-preserving
  hand copy of the owner pair passes every standing oracle by
  construction (the copy is correct — identical keys, identical
  no-op/skip semantics), so no behavioral gate can pin unity;
  only a source census could, and that is a bespoke existence
  test per helper, which [dry][dry] forbids for gate-only
  findings (same bar as the verified enum-cache,
  definition-store, pending-ledger, taxonomy, and accessor
  items). Unity rests on the one-way import edges (base →
  registry, finalizer → registry, sets → registry; never the
  reverse at module top) plus the recorded triggers below. What
  N1/N2 prove instead: the two load-bearing lines each fail
  exactly their contract row when removed (entry guard →
  idempotence; Phase-3 skip → pre-marked skip), so the standing
  rows that fail real breaks stay as behavior coverage: the
  idempotence row, the pre-marked-skip row, the Phase-3-failure
  row, the clear-then-fresh pair, the mutator-refusal pack, the
  three bind retry-idempotence rows.
- **Coupling.** None. Adjacent verified items untouched: the
  F1/F2/F3/F4 stores and every oracle file keep their blobs
  (fingerprints below); no edit here can stale them.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `registry.py` `9cc8bb55…`, `types/finalizer.py`
  `77fd9a2d…`, `types/base.py` `91c58747…`,
  `types/definition.py` `fa6c4d330…`, `types/relay.py`
  `52439862…`, `mutations/sets.py` worktree `936f5ae7…`
  (`HEAD` `cffa29e5…`; the delta is the 5-hunk concurrent
  `__name__`-to-`_safe_class_name` wording-only drift outside
  every cited gate line — read, never edited),
  `tests/test_registry.py` `e330cfb8…`,
  `tests/types/test_finalizer.py` `462275e5…`,
  `tests/types/test_definition_order.py` `7dd04d67…`,
  `tests/types/test_relay_interfaces.py` `26fb2ccf…`,
  `tests/test_relay_connection.py` `b6bd90d9…`,
  `tests/mutations/test_sets.py` `8574a349…`,
  `tests/forms/test_sets.py` `159b55ec…`,
  `tests/rest_framework/test_sets.py` `7e7d1819…`,
  `tests/orders/test_finalizer.py` `44a00e8f6…`,
  `tests/filters/test_finalizer.py` `8365a132…`,
  `tests/testing/test_relay.py` `55e43ed2…`. Searched
  population: whole package (117 `.py`, both trees). Any
  fingerprint change reopens the finding.
- **Reconsideration triggers (recorded at the owners).** The gate
  stays single-owned until one fires: T-guard fires if a second
  no-op-on-done path appears beside the entry line; T-skip fires
  if a definition loop lands without the skip; T-flag fires if a
  third finalized-state needs its own flag (FIRED once by the
  Relay step guard — adjudicated R-B, separation stands);
  T-lock fires if a request-path finalize appears (R-F). Durable
  homes: the finalizer module docstring (gate contract), the
  `mark_finalized` / `is_finalized` docstrings, this finding. The
  plan's `## Responsibility index` row for
  `type-registry-finalize-gate` already covers all four member
  files; no new row owed.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A entry guard vs per-type flags (the core split; discharges
  the definition-store R-E home). Difference: whole-build
  no-op (`if registry.is_finalized(): return` — second success
  does nothing, B1) vs per-entry skip-and-continue (six
  `if definition.finalized: continue` lines — retry resumes,
  B2/B4). Collapsing to one fact breaks one direction or the
  other: guard-only loses partial recovery (a Phase-3 raise
  would force `clear()` + fresh classes for a fixable entry);
  flags-only loses the silent no-op (every second call would
  re-walk all phases). Trigger: a consumer needing build-done
  and entry-done to agree (T-guard/T-skip). Home: the finalizer
  module docstring + this finding.
- R-B Relay step guard vs done-flag (definition-store R-E
  trigger fired, adjudicated). Difference: `effective_globalid_strategy`
  records classification data (a string the decode path reads)
  that doubles as one step's re-entrancy guard; `finalized`
  records `strawberry.type` applied. A retry after a Phase-2.5
  audit raise holds strategy-recorded-but-unfinalized types —
  collapsing the guard into the flag reinstalls the closure and
  misclassifies the type `custom` (the install docstring names
  exactly this). Trigger: a step whose guard can ride the type
  flag without misclassification (T-flag re-fire). Home:
  [trelay][trelay]`::install_globalid_typename_resolver`
  (step-0 clause) + this finding.
- R-C synthesis field marker vs type-done. Difference:
  per-field attach state (recognize our own prior attachment;
  re-suppress the list form on rerun) vs per-type done. The
  marker fires inside one Phase-2.5 step for one field; the flag
  fires at Phase 3 for the type. Trigger: synthesis needing
  type-level state (T-flag re-fire). Home: the marker comment +
  [test-relay-connection][test-relay-connection] refinalize pair.
- R-D `_check_mutable` vs entry guard. Difference: loud refusal
  (mutators raise post-finalize so a late import corrupts
  nothing) vs silent no-op (second finalize returns `None`).
  N1 proves the layering: without the guard the no-op contract
  breaks exactly at the backstop. Trigger: a mutator needing
  silent acceptance post-finalize (none exists). Home: the
  `_check_mutable` docstring + this finding.
- R-E mutation / form / serializer binds vs the gate (the
  `mutations/sets.py` membership answer). Difference: deferred
  operation binding (drain declaration ledgers, materialize
  inputs/payloads as module globals, resolve primaries — the
  write-flavor subject owned by the sealed-authorization and
  payload families) vs build-done bookkeeping. The bind reads
  the gate (`register` refuses post-finalize, mirroring
  `_check_mutable`) and rides its recovery (pre-bind reset +
  per-pass cache clear make re-finalize retry-idempotent with no
  flag of its own — C8). Trigger: a bind path needing its own
  done-flag instead of clear-and-rebuild. Home:
  [mutation-sets][mutation-sets]`::bind_write_declarations` +
  `::make_declaration_registry` + this finding.
- R-F no-lock vs guarded mutation. Difference: the gate documents
  single-threaded import-time finalization ([registry][registry]
  class docstring + the filters/sets expansion contract), so
  phases compose without a lock; the `threading.Lock`s in
  `orders/sets.py` (per-resolution attestation ledger),
  `schema.py`, `routers.py` guard unrelated runtime layers
  (excluded on strength of body). Trigger: a request-path
  finalize (T-lock). Home: the registry class docstring + this
  finding.

## Defects

None meeting the [agents][agents] bar (contract row + feasible
shape + wire/config input). Adjudicated while tracing, kept out
for cause: no mid-build re-entrancy guard (nested finalize
during finalize has no test and no lock — but no contract
requires one; the production path is import-time
single-threaded and no wire input reaches a nested call, so this
is a robustness note, not a defect); N1's loud
second-finalize-without-guard (the `_check_mutable` backstop
working as designed, R-D); Phase-2/2.5 progress unrecorded
(by-design step idempotence, pinned per step by the relay,
synthesis, and bind retry oracles).

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace (40/40 + N1 + N2, copy `__file__` + copy DB `NAME`
recorded, no source mutation, byte-identical restores,
`grep -c truncated` == 0); the one authorized shared-tree focused
test ran green post-trace (10 passed) with zero edits in flight,
so no run is invalidated. No `execution-deferred` items.
`FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by
construction`: every executed claim is in-memory dict work plus
pure class construction/decoration; the probes open no DB
(recorded `NAME` is the copy's own file, never touched).
Full-suite gate business is deferred to the final-gate item with
reason: the entry command authorizes workspace runs plus one
focused `--no-cov` test, and a green unmutated suite would
discharge no failability proof for a rejection that proposes no
gate.

## Judgment

Single-owned gate, single flip site, single tail line, six skip
enforcement sites composing one flag by name. What "finalized"
MEANS per phase: Phase 1 records nothing (failure-atomic; the
pending ledger item pins retention); Phase 2/2.5 record nothing
per type (idempotent re-execution per step); Phase 3 records per
entry (the one flip line); the entry guard records the build.
The six resemblance candidates (per-type flags, step guard,
field marker, mutator guard, bind ledgers, lock absence) are
intentional separations with recorded differences, triggers, and
existing homes. Consolidation rejected; zero edits; no new tests
owed (standing oracles at the mandated tiers pin every
challenged axis; the two load-bearing lines additionally carry
N1/N2's proved shape).

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`039cb41e4b8ec9aeb7e1935650e57ff006415520`) is empty for
`django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/finalizer.py`,
`django_strawberry_framework/types/base.py`, and
`django_strawberry_framework/mutations/sets.py` (and vs `HEAD`
`bfaee91d` likewise, except the five known concurrent-work
wording-only hunks in `mutations/sets.py`, sampled above —
message rendering only, outside every cited gate line; never
edited, so no attribution stop triggered). The plan's
`## Owned changes` ledger holds no row on any family path (only
`optimizer/walker.py`, two fakeshop live files,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`) — confirmed by full read; nothing
to attribute. A stale `index.lock` (concurrent git process)
refused `git stash create` for an independent item baseline, so
the brief's `ITEM_BASELINE` plus `git diff <baseline> -- <paths>`
carries the scoping instead. No commit per standing rule.

After the (zero) edits: nothing to fix or format (no tracked
path touched; `.md` artifacts are excluded from format). No
`CHANGELOG.md` touch.

Scratch paths (removal is Worker 0's, after `verified`, by
explicit path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/finalize-gate-w1`
(includes its own `.venv`, created by the authorized runs, plus
`probe_finalize_gate.py` holding the 40 executed checks + N1/N2).
No manifest (no `prove_failability.py` run — no gate added, none
owed).

Worker 0 rows: tick Family `type-registry-finalize-gate` (this
artifact); no `## Responsibility index` change (provisional owner
+ all four member files already covered, status stays `open`
until Worker 2); no `## Owned changes` append (zero tracked
edits); no defect homing (none found).

Worker 0 rows: tick Family `type-registry-finalize-gate` (this
artifact); no `## Responsibility index` change (provisional owner
+ all four member files already covered, status stays `open`
until Worker 2); no `## Owned changes` append (zero tracked
edits); no defect homing (none found).

## Independent verification (Worker 2)

Own trace (derived from the four members + consumers before
reconciling with `## Findings` above; every count re-pinned
against the tree at `HEAD bfaee91d`).

**Mechanism sweep.** Storage: `_finalized: bool = False`
single construction (`registry.py` init line), single tail flip
(`mark_finalized` body), single reset (`clear()` body), guard
read (`_check_mutable` body) — all inside `registry.py`; no
second gate def anywhere in the 117-file sweep. Accessors:
`is_finalized` / `mark_finalized` / `_check_mutable` 1 def
each. Entry guard `if registry.is_finalized(): return` exactly
1 code line (`finalizer.py` top of `finalize_django_types`);
tail `registry.mark_finalized()` exactly 1 code call (last
statement); `definition.finalized = True` exactly 1 code site
(Phase-3 loop; the two other mentions are docstrings).
`if definition.finalized:` skips exactly 6 code sites
(synthesis loop, Phase-2 loop, Phase-2.5 interface/Relay loop,
field-surface audit loop, Phase-3 loop, sidecar subpass-1
loop; two further mentions are docstring prose). Storage for
the per-type flag: `finalized: bool = False` single field on
`DjangoTypeDefinition` (`definition.py`), with a
finalized-once clause — storage lives there, the rule here.
Producer: the finalizer (sole flip site + sole tail-flip
caller). `is_finalized()` code calls exactly 4 (`base.py`
refusal, `definition.py` validity key, `finalizer.py` entry,
`mutation-sets.py` refusal; all other hits are docstrings).
`mark_finalized()` code calls exactly 1.

**Consumers (each confirmed by body read).**
`DjangoType.__init_subclass__` post-finalize refusal
(`base.py`); mutation declaration `register`
post-finalize refusal (`mutations/sets.py` lines on the
`make_declaration_registry` closure, mirroring
`_check_mutable` wording); mutation / form / filter / order /
auth Phase-2.5 bind riders with no done-flag of their own
(clear-and-rebuild via the pre-bind
`iter_subsystem_clears(before_bind=True)` sweep);
`definition.py::related_target_for` cache validity key
(populates the memo only when the gate reads true, so a
transient pre-finalize `None` can never lock in);
`testing/relay.py::global_id_for` finalized-first read order
(strategy stamp is Phase-2.5, `finalized` flips Phase 3 —
the gate-first ordering is load-bearing and documented at
the read); inspect command unfinalized display branch
(`definition.finalized is False` → `CommandError`).
Step guards intentionally separate: Relay
`effective_globalid_strategy` non-`None` re-entrancy guard
(`relay.py`, step-0 clause naming the exact
reinstall-misclassifies-`custom` rationale) and the
synthesis field marker (recognize-own-prior-attachment;
re-entrant `continue` still re-records the walker slot and
re-suppresses the list form).

**Definition counts per posited change (agree).**
C1 finalize-twice → 1 (entry guard; flags 0 moved).
C2 new phase → 1 (flag composed by name; the new loop owes
the skip as a consumer, not a definition). C3 concurrent →
1 decision (see lock judgment below). C4 clear + re-finalize
→ 1 (the `clear()` reset). C5 → 2 intentionally separate
(see hard re-judgment below). C6 → rejected (silent no-op
vs loud refusal; N1 pins the layering). C7 → rejected
(recorded classification vs done-flag; a
strategy-recorded-but-unfinalized retry would reinstall and
misclassify `custom`). C8 → 0 (no bind done-flag exists;
clear-and-rebuild is the mechanism).

**Owner.** `registry.py::TypeRegistry` (F5 aspects) — agree.
Narrowest cohesive owner every consumer can import without
reversing a dependency (`base.py` and `finalizer.py`
already import the registry at module top;
`definition.py` reaches it only in-function for exactly
this reason). F1/F2/F3/F4 boundary statements re-derived
and agree; the definition-store R-E trigger is adjudicated
here as R-B and the separation stands.

**C5 hard re-judgment: guard + flags BOTH LIVE, no
consolidation candidate.** Failed-then-retried trace:
a Phase-3 raise leaves the tail flip unrun (guard stays
open) with a MIXED per-entry flag vector (decorated types
`True`, the failing entry onward `False`). The retry enters
through the open guard and the six per-loop skips resume
from the failing entry — the flags carry per-entry progress
state the whole-build guard does not encode. Guard-only
loses partial recovery (forces `clear()` + fresh classes
for a fixable entry); flags-only loses the silent no-op
(every second call re-walks all phases) and, per N2,
re-decorates already-built types. The flags are NOT dead on
the second finalize: that path (guard true → early return)
is one of three states (all-done no-op vs partially-done
resume vs never-run full build), and the flags are
reachable on every retry where the guard reads false with
mixed flags. R-A / R-B separation stands; nothing routes
to the family.

**C3 lock judgment: documented no-lock, sound, no gap.**
The no-lock statement is written AT the owner
(`registry.py::TypeRegistry` class docstring: mutators not
guard-locked; safe because every production-path mutation
runs at import time from `__init_subclass__`
(single-threaded module loading); `clear` is test-only; do
not mutate from a request handler or async resolver),
anchored by the `filters/sets.py` single-threaded expansion
contract. Finalize runs at import/collect time,
single-threaded — the assumption is written where owned,
so there is no projection gap and no defect or trigger owed
beyond the recorded T-lock/R-F (a request-path finalize).
Zero lock vocabulary on the gate path confirmed
(`registry.py` + `finalizer.py` carry no threading/lock
imports; the package locks live in `schema.py`,
`routers.py`, `orders/sets.py`, `write_transaction.py` —
unrelated runtime layers, excluded on strength of body).
Zero `AsyncFunctionDef` in the four members is consistent
with the read (collection / finalize / drain are dict +
class-attr work, no ORM I/O, no awaits).

**`mutations/sets.py` declaration refusal + dirt.**
Consumer confirmed (the `register` closure refuses
post-finalize, mirroring `_check_mutable`). Item-baseline
diff on all four family paths is byte-empty (confirmed).
`HEAD` diff carries exactly the 5 known hunks, all
`__name__`-to-`_safe_class_name` message rendering, none
touching the gate line (`is_finalized` refusal) or any
cited gate line — verified outside gate lines, left alone,
never edited. No attribution stop triggered (ledger holds
no row on any family path; dirt is external concurrent
work).

**No-gate reasoning: same standard as siblings, accept.**
A behavior-preserving hand copy of the owner pair passes
every standing oracle by construction, so no behavioral
gate can pin unity and a source census would be a bespoke
existence test per helper, which the method forbids for
gate-only findings — the same bar as the verified
enum-cache, definition-store, pending-ledger, taxonomy,
and accessor items. N1/N2 instead prove the two
load-bearing lines each fail exactly their contract row
when removed (entry guard → idempotence; Phase-3 skip →
pre-marked skip), and the standing rows that fail real
breaks stay as behavior coverage. Justified population +
existing triggers recorded; no gate owed.

**Freshness re-hashed (Worker 2, `git hash-object`,
working tree).** `registry.py` `9cc8bb55…`,
`types/finalizer.py` `77fd9a2d…`, `types/base.py`
`91c58747…`, `types/definition.py` `fa6c4d330…`,
`types/relay.py` `52439862…`, `mutations/sets.py`
worktree `936f5ae7…` (`HEAD` `cffa29e5…`, delta = the
5-hunk concurrent drift above), `tests/test_registry.py`
`e330cfb8…`, `tests/types/test_finalizer.py`
`462275e5…`, `tests/types/test_definition_order.py`
`7dd04d67…`, `tests/types/test_relay_interfaces.py`
`26fb2ccf…`, `tests/test_relay_connection.py`
`b6bd90d9…`, `tests/mutations/test_sets.py`
`8574a349…`, `tests/forms/test_sets.py` `159b55ec…`,
`tests/rest_framework/test_sets.py` `7e7d1819…`,
`tests/orders/test_finalizer.py` `44a00e8f6…`,
`tests/filters/test_finalizer.py` `8365a132…`,
`tests/testing/test_relay.py` `55e43ed2…` — every prefix
matches the recorded fingerprint; no finding went stale.
`HEAD` is `bfaee91d`. All other dirty paths in
`git status --short` are outside the family scope and were
left untouched.

**`## Pending execution` empty: judged adequate.**
Finalize lifecycle + retry are covered by named gate-run
oracles that stay in the suite: the idempotence row, the
pre-marked-skip row, the Phase-3-failure recovery row, the
clear-then-fresh pair ×2, the mutator-refusal pack, the
unregister-after-finalize refusal, the three bind
retry-idempotence rows, the refinalize synthesis pair, and
the audit-raise rerun rows. The 40/40 workspace proof + N1
+ N2 were executed in a disposable copy (copy `__file__` +
copy DB `NAME` recorded, no source mutation,
byte-identical restores); the one authorized shared-tree
focused run (10 passed) ran green with zero edits in
flight, so no run is invalidated. Sharded/PG cells
inapplicable by construction (in-memory dict work plus
pure class construction/decoration; the probes open no DB)
— sound. Full-suite business stays deferred to the
final-gate item with reason (a green unmutated suite
discharges no failability proof for a rejection proposing
no gate).

**AGENTS.md prose on the (empty) diff.** The
`## Implementation (Worker 1)` section is factual scoping
prose only (baseline + ledger check + the `index.lock`
attribution note explaining why the brief baseline
carries scoping) — no process storytelling, no
unattributed-hunk stop (empty item diff; ledger holds no
family-path row). Citations are reference-style
`path::Symbol` links with the bottom `LINK DEFINITIONS`
block; oracles sit at the mandated tiers (`tests/` +
live composition sibling noted). No tracked `.py` touched
→ `ruff check` / `ruff format --check` have no touched
paths to run against (vacuously satisfied; `.md`
artifacts are excluded from format). No `CHANGELOG.md`
touch. No commit.

**Per-claim agreement/difference.** Agree on every
numbered claim in the brief (definitions 1-each,
producer/consumer census, 4 code calls of `is_finalized`,
1 of `mark_finalized`, C1–C8 counts, F5 owner, REJECT
with R-B..R-F separations, no defects, no pending
execution, zero production edits). No material difference:
the Phase-2/2.5 loop skips, which a thin reading could
call redundant given step idempotence, are reachable on
every mixed-flag retry and keep already-decorated classes
from re-mutation — consumers, not definitions (C2
adjudicates). Population completeness confirmed:
whole-package 117-file sweep; the only out-of-member
`finalized*` hits are different vocabulary
(`optimizer/plans.py` plan-cache) or listed consumers
(`testing/relay.py`, inspect command).

## Defects

None meeting the `AGENTS.md` bar. Concur on the three
adjudicated non-defects (no mid-build re-entrancy guard —
no contract requires one, no wire input reaches a nested
call; N1's loud second-finalize-without-guard — the
`_check_mutable` backstop working as designed; Phase-2/2.5
progress unrecorded — by-design step idempotence pinned by
the relay, synthesis, and bind retry oracles). No
`(Worker 2)` entries.

## Judgment (Worker 2)

`Status: verified`. Single-owned gate, single flip site,
single tail line, six skip enforcement sites composing one
flag by name. C5 re-judged hard: both guard and flags
live, no consolidation candidate, nothing routed. C3
re-judged: documented at the owner, sound, no gap. Dirt
verified outside gate lines and preserved. Freshness
re-hashed clean. Pending execution empty and adequate.

Worker 0 rows: tick Family `type-registry-finalize-gate`
(this artifact) as `verified` (no pending execution);
`## Responsibility index` row `type-registry-finalize-gate`
`open` → `rejected` (single-owned, R-A..R-F separations
with triggers at the owners); no `## Owned changes` append
(zero tracked edits); no defect homing (none found);
remove scratch by explicit path only after ticking:
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/finalize-gate-w1`
(includes its own `.venv` plus `probe_finalize_gate.py`
holding the 40 executed checks + N1/N2). Do not commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[dry]: DRY.md
[spec-018]: ../SPECS/spec-018-meta_primary-0_0_6.md
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[definition]: ../../django_strawberry_framework/types/definition.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[mutation-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[relations]: ../../django_strawberry_framework/types/relations.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[trelay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-definition-order]: ../../tests/types/test_definition_order.py
[test-filters-finalizer]: ../../tests/filters/test_finalizer.py
[test-finalizer]: ../../tests/types/test_finalizer.py
[test-form-sets]: ../../tests/forms/test_sets.py
[test-mutation-sets]: ../../tests/mutations/test_sets.py
[test-orders-finalizer]: ../../tests/orders/test_finalizer.py
[test-registry]: ../../tests/test_registry.py
[test-relay-connection]: ../../tests/test_relay_connection.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py
[test-serializer-sets]: ../../tests/rest_framework/test_sets.py
[test-testing-relay]: ../../tests/testing/test_relay.py

<!-- examples/ -->
[test-schema-composition]: ../../examples/fakeshop/test_query/test_schema_composition_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Bounded re-review (Worker 2, Q14)

Phase-1 trace, Worker 2, reconciliation queue Q14. Zero edits. HEAD bytes primary;
worktree diffs read for attribution only. Prior findings NOT read in this phase; no status
set; no verdict on prior findings proposed.

Method: `registry.py` finalize aspects + `types/finalizer.py` traced from HEAD bytes;
`types/definition.py` + `types/base.py` worktree-vs-HEAD hunks read for overlap only.
Tests read as oracles, never run.

### 1. Gate mechanism (re-derived from HEAD bytes)

Entry guard: `django_strawberry_framework/types/finalizer.py::finalize_django_types` opens
with `if registry.is_finalized(): return` — a second successful call is a no-op before any
work. Phase order: Phase 1 (primary-ambiguity audit + pending-relation
classify/resolve, failure-atomic — no class object mutated before the unresolved-target
raise) → Phase 2 (relation + file resolvers) → Phase 2.5 (interface injection, Relay
composite-pk gate + resolver install, globalid strategy stamp, cursor-field validation,
node-field check, relation-connection synthesis, model-label routing audit + collapse
warning, mutation/form/auth binds, filterset/orderset binds, field-surface audit) →
Phase 3 (`strawberry.type` per type, then `definition.finalized = True`) → tail
`registry.mark_finalized()` as the last statement, so any Phase 2/2.5/3 raise leaves the
flag False and a rerun resumes per entry.

Per-type skips: six `if definition.finalized: continue` consumers over the one
`django_strawberry_framework/types/definition.py::DjangoTypeDefinition.finalized` flag —
the Phase-2 loop, the Phase-2.5 interface loop,
`django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`,
`django_strawberry_framework/types/finalizer.py::_bind_sidecar_sets` subpass 1, the
field-surface audit loop, and the Phase-3 loop. Sole writer is Phase 3.

Mutator refusals, two layers: (a) declaration refusal in
`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` — explicit
`if registry.is_finalized(): raise ConfigurationError` with class-name attribution
(Meta-less abstract bases return before it); the later
`django_strawberry_framework/registry.py::TypeRegistry.register_with_definition` call
would independently trip layer (b). (b) boundary refusal
`django_strawberry_framework/registry.py::TypeRegistry._check_mutable`, consumed by all
seven public mutators (`register`, `register_definition`, `register_type_teardown`,
`unregister`, `add_pending_relation`, `discard_pending`, `register_enum`); `clear()` is
the one public mutator that intentionally bypasses the guard and resets `_finalized`.

### 2. Dirt overlap verdict per gate element

(a) `types/definition.py` dirt (HEAD `fa6c4d33` → worktree `01f78d93`): guarded
`isinstance` / `str.__str__` hardening in 4 method bodies. `finalized` and every other
field declaration untouched.

- `DjangoTypeDefinition.graphql_type_name` — gate EXECUTES it on three paths:
`_audit_field_surface` error text, `_check_filterset_owner_pk_identity` comparison, and
`_format_globalid_encode_only_filter_error` text (plus the registry
`definition_for_graphql_name` scan). Honest inputs (validated `Meta.name` or exact-str
origin `__name__`) render byte-identically; hostile inputs convert a raw escape into a
typed `ConfigurationError`. Verdict: OVERLAP but benign-transparent.
- `DjangoTypeDefinition.related_target_for` — gate EXECUTES it in the
`_bind_set_owner_common` second-owner agreement walk. Honest keys identical; hostile
keys now return `None` (typed divergence error downstream) instead of escaping raw.
Verdict: OVERLAP but benign-transparent.
- `_normalize_pk_name` + `_resolves_id_off_pk` — zero gate call sites; sole consumer is
`django_strawberry_framework/optimizer/walker.py::_has_custom_id_resolver` (request-time
FK-id elision). Verdict: NO OVERLAP; gate never executes these bodies.

(b) `types/base.py` dirt (HEAD `91c58747` → worktree `377d00eb` at my verification;
moving-concurrent, see fingerprints): validator `isinstance` hardening,
`_is_suppressed_relay_pk` extraction, `_format_name_list`, `_is_optimizer_hint_value`,
plus the NEW class-name gate at the head of `__init_subclass__` (typed
`ConfigurationError` on unreadable / non-exact-`str` / empty `__name__`).

- The class-name gate sits AFTER `super().__init_subclass__` but BEFORE sentinel
stamping, the Meta-None early return, and the `is_finalized()` refusal: it is
PRE-refusal. For honest classes (CPython always sets an exact `str` `__name__`) it
passes transparently, so a post-finalize honest subclass still raises the pinned
refusal message. A hostile-`__name__` class gets the class-name error instead of the
finalize-refusal error — same exception type, typed either way, and reachable only via
a hostile metaclass, which is outside the supported-API trust boundary. Verdict:
pre-refusal, benign-transparent.
- The refusal body itself is byte-unchanged; `_check_mutable`, all 7 call sites, and
the `clear()` bypass are unchanged (`registry.py` + `types/finalizer.py` worktree diffs
are comment-only). All remaining base.py churn runs at class-creation/collection time;
no gate element executes any of it at finalize time (the `_synthesize_relation_connections`
`DEFAULT_RELATION_SHAPE` import is a constant, not a dirtied body). Verdict: NO
finalize-time OVERLAP.

### 3. Definition counts (my own)

- Second finalize: 1 entry-guard definition (finalizer head); 1 flag definition
(`DjangoTypeDefinition.finalized`) with 6 skip consumers + 1 Phase-3 flip site; 1
tail-flip statement (`mark_finalized`). The no-op holds via the guard alone.
- New phase needing rerun-skip: 0 new definitions — one more consumer line on the
existing flag (6 → 7).
- Concurrent finalize: 0 definitions — explicitly unsupported (registry docstring: no
lock, single-threaded import-time mutation); outside the trust boundary.
- Mutator-refusal layers: 2 singly-owned layers (declaration refusal in
`DjangoType.__init_subclass__`; boundary refusal `TypeRegistry._check_mutable` with 7
consumers). A "new public mutator" change adds 1 `_check_mutable()` consumer line and 0
new definitions.

### 4. Owners I would choose

- Entry guard + tail flip + phase sequencing:
`django_strawberry_framework/types/finalizer.py::finalize_django_types`; inert slot +
accessors: `django_strawberry_framework/registry.py::TypeRegistry`.
- Per-type flag state: `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.finalized`;
sole writer Phase 3; the six skips are consumers.
- Declaration refusal: `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`
(the new class-name gate joins the same function head — no new owner).
- Boundary refusal: `django_strawberry_framework/registry.py::TypeRegistry._check_mutable`.
- `graphql_type_name` derivation + `related_target_for` lookup:
`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`; gate paths are
consumers. Applicable contracts: DRY principles 4 (stated lifetime: flag flips once in
Phase 3, slot resets in `clear()`) and 7 (responsibility: lifecycle owner per layer).

### 5. Breakage verdict

The dirt breaks nothing derived. No contract row (DRY 4/7; GOAL finalize-must-be-safe +
re-finalize-silent-no-op) is broken, so no defect is recorded: every divergence I found
needs a hostile metaclass / `__class__` / `__str__` input with no feasible project shape
under the supported public API, and each converts a raw escape into a typed
`ConfigurationError` (or `None`-as-absent) — the same direction as the pinned oracles.

Oracles read (not run): `tests/test_registry.py::test_finalize_is_idempotent` (one
`strawberry.type` call across two finalizes),
`tests/test_registry.py::test_finalize_skips_definitions_marked_finalized_when_registry_is_unfinalized`,
`tests/test_registry.py::test_registering_concrete_type_after_finalization_raises`,
`tests/test_registry.py::test_mutators_reject_calls_after_mark_finalized`,
`tests/test_registry.py::test_phase_3_failure_leaves_registry_unfinalized_and_requires_fresh_classes`,
`tests/test_registry.py::test_registry_clear_allows_fresh_type_classes_to_finalize_again`,
`tests/types/test_base.py::test_post_finalization_registration_raises` (pins the refusal
message with the honest class name — flows through the unmodified refusal lines).

### 6. Freshness fingerprints

- HEAD commit `bfaee91d` (verified `git rev-parse HEAD` at trace time): `registry.py`
`9cc8bb55`, `types/finalizer.py` `77fd9a2d`, `types/definition.py` `fa6c4d33`,
`types/base.py` `91c58747` (each via `git show HEAD:<path> | git hash-object --stdin`).
- Worktree at 2026-09-21T01:04:49Z (verified `git hash-object` at trace time):
`registry.py` `612bea87` (mtime 2026-09-19T09:57:12Z, comment-only drift),
`types/finalizer.py` `f4266a15` (mtime 2026-09-19T08:26:27Z, comment-only drift),
`types/definition.py` `01f78d93` (mtime 2026-09-21T00:28:13Z),
`types/base.py` `377d00eb` (mtime 2026-09-21T01:01:18Z) — matches the third observed
worktree hash, so the churn had settled on `377d00eb` at my verification time; still
treated as moving-concurrent for phase 2.

PHASE-1-TRACE-RECORDED — `docs/dry/dry-rule-type-registry-finalize-gate.md`
