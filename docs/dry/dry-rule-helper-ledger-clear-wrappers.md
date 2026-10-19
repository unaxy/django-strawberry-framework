# DRY review: `helper-ledger-clear-wrappers`

Status: verified
Run: 0.0.15 2026-10-11-20

Family `helper-ledger-clear-wrappers`. Item baseline `c039b790fe594cc70307a593ce069210ffdd6dd2`; Worker-1 with edit rights at `dry/helper-ledger-clear-wrappers/consolidate` (slot-5; pool grown to 6 slots via the documented `DSF_WS_SLOTS` knob — 3 before-copies + item-2's consolidate filled the default 4). Never read another worker's `worker-memory/`; never touched `optimizer/walker.py` or `rest_framework/sets.py`.

## System trace

Rule: a helper ledger's drain-on-`clear()` effect should be named once. Three private 1-statement wrappers, each body a bare `<ledger>.clear()`, no docstring, exactly one in-package reader (its own registration line), zero test/example callers: [filters-init][filters-init]`::_clear_helper_referenced_filtersets` (:56, owner `filters.helper_references`), [orders-init][orders-init]`::_clear_helper_referenced_ordersets` (:48, owner `orders.helper_references`), [relay][relay]`::_clear_node_fields_declared` (:115, owner `relay.node_fields`). Bus contract re-derived on live bytes: [registry][registry]`::register_subsystem_clear` stores `(clear, before_bind)` keyed by owner with no introspection (zero `__name__` reads on the bus path); `TypeRegistry.clear` and the finalizer pre-bind sweep call each callback bare; reload replaces by owner key. Whole-package census: 20 registration sites (17 family + 3 drift-new: `connection.edge_class`, `optimizer.document_key_cache`, `optimizer.forward_names`), 13 named defs + 7 factory closures — the bus already stores non-def callables, so a bound `.clear` is no new shape. Ledgers never rebound (in-place `.clear()`/`.discard()` only; tests import the ledger objects). Worker-0 premise part-disproved: specs DO cite the twins (spec-027 :655/:891, spec-028 :65/:620 — bare literals, ungated, rewritten in this change) and the board cites relay's wrapper as gated `path::Symbol` (KANBAN.md:301). Decision: twins CONFIRMED and landed; relay CONFIRMED with migration held on the board render cycle (Coupling, trigger stated — no contract difference).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** All 20 members censused by body (trace). Twins + relay are the only private undocumented 1-stmt defs; 5 public 1-stmt defs dispositioned (2 keep on direct test callers, 3 named as follow-up F2); 5 namespace wrappers + serializer wrapper keep on callers + stated family reasons; 7 factory closures are the precedent.
2. **Sync/async twins.** Zero `AsyncFunctionDef` on the bus path; callbacks are `set`/`list` `.clear()`. No color split exists. Trigger: a teardown callback awaiting or touching the DB.
3. **Derived rather than repeated knowledge.** Each owner string declared once at its registration; the replay population derives per call from the one dict. The deletion removes a name, never a derivation.
4. **Inverse / round-trip pairs.** register/replay pair unchanged (same owners, same flags, same ledgers). No second half exists to drift.
5. **Contracts restated in another medium.** Production (2 edited rows) + oracles (3 ledger tests + 8 bus rows, all green pre/post) + projections (4 spec sites + 1 test docstring rewritten; board row untouched by the duo — verified zero twin mentions). Closed history (`DONE/`, `dry-file-*`, `review-0_0_15`) stays as written.
6. **Enforcement by omission.** AST census of module-level mutables over all 118 package files + literal backstop: every mutable is bus-cleared, contract-persistent (lookup tables, `_ROUTER_CLASS_LOCK`, class-keyed memos `never recreated by clear()`), or `_index_advisory_seen` — a DEBUG-only warning dedup with an owner-stated per-test direct-call seam (`clear_index_advisory_dedup`), correctness-neutral by its own comment. No contract source extends the bus rule to it; consequence of staleness is a suppressed warning, never a wrong result. No defect (trigger: an oracle asserting re-warn after `registry.clear()`).

### Challenges

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Ledger renamed or re-containered | 1 before (wrapper body) → 1 after (registration line). Count equal; the P11 prong, not the count, decides. |
| C2 | Clear gains a second effect (ledger + metric) | 1 → 1 (small callback at the registration). Same honesty: no count win claimed. |
| C3 | Generic clearable-record for the trio (family-C3 shape) | REJECTED, concurring with family C3: a record type + driver + validation re-declares every owner/flag/object triple for 3 one-call members. The APPLIED shape is disjoint from C3's rejection: no new type/driver/flag/API, owners/flags/triples byte-identical, lifetime prose stays on the untouched ledger comments. |

## Findings

### F1 — helper-ledger clear wrappers (CONFIRMED; twins applied, relay held on projection mechanics)

- **Contract + variation.** Each helper ledger drains when `registry.clear()` replays its owner row. Varies on nothing: same flag (full-only), same effect (`.clear()`), same lifetime reason (orphan-audit/finalize-check ledgers, stated on the ledger comments which survive).
- **Sites + roles.** *Definitions removed (2):* the twin wrapper defs. *Definitions kept (1, held):* relay's wrapper. *Consumers:* the bus replay (unchanged). *Oracles:* 3 ledger tests + 8 bus rows (below). *Projections moved:* 4 spec sites + 1 test docstring; *projection holding relay:* 1 gated board citation.
- **Challenges.** C1 → 1/1, C2 → 1/1, C3 → rejected-with-distinguisher (above). Bar basis is principle 11: no callers, no docstring, no introspection, no flag, no stated reason, reload-safe by owner key either way. Precedent: spec-039 already deleted this exact shape (`clear_*` over `_materialized_names.clear()` → factory `clear_fn`).
- **Owner + lifetime (principles 7, 4).** [registry][registry] bus stands (family verdict untouched — no owner/flag/ledger moved). Callback-state lifetime unchanged: full-clear rows draining import-time ledgers.
- **Migration.** Twins: def deleted, registration takes the bound `<ledger>.clear` (applied, slot-5 blobs below). Relay: identical 4-line deletion PROVEN behavior-preserving (prove run `43644c`, 0 rows failed) but NOT landed — Coupling.
- **Shrinkage.** Net package −8 lines over the item baseline (2 defs × 4 lines); no new helper/wrapper/constant/flag (machinery attestation: none added).
- **Distinct behavior.** Relay wrapper text stays until its projection moves; all owners/flags/effects identical. Family `subsystem-clear-lifecycle` verdict stands (bus/owners/flags/ledgers unchanged; member drift 17→20 already flagged-not-reopened by the plan).
- **Behavioral proof.** `execution-verified`: post-edit ledger 3/3 (`1b0812`) + bus 8/8 (`126426`), identical to pre-edit baselines (`56fa3e`, `b51cf8`); failability 2/2 pinned (`3a156c`: dropping either registration fails exactly its named test, `assert {BookFilter} == set()` / `assert {HelperLedgerOrder} == set()`); relay preservation (`43644c`, expect-none-failed); docstring-edit inverse proof (docstring-stripped AST of `tests/test_registry.py` identical slot-1 vs slot-5). Each proof names its wrong result (stale ledger surviving `clear()`).
- **Negative control.** None: bypass is not the threat class (test-isolation teardown, no auth/data-exposure surface).
- **Coupling.** Relay third blocked on rewording the KANBAN.md:301 clause under card TODO-ALPHA-053-0.0.15 (gated citation `django_strawberry_framework/relay.py::_clear_node_fields_declared`) — a board-DB edit + `KANBAN.md`/`KANBAN.html` re-render outside this item's fence. Owning card named; relay migration + trigger exact.
- **Freshness.** Live `git hash-object` (HEAD in parens where dirty): [registry][registry] `c5aa2050` (`47b52c52`; concurrent truth hunks, all outside bus lines 63/81-115/clear tail — hunk `637` only appends below `clear()`); [filters-init][filters-init] `ecff967b` (clean); [orders-init][orders-init] `e835e9b3` (clean); [relay][relay] `edfa8d6d` (`337a2d96`; trio lines 102-119 byte-identical, every diff hunk outside); spec-027 `f104c22b` (clean); spec-028 `45f64a2c` (`2e312a6e`; one concurrent hunk at :57-63, disjoint from :65/:620); `tests/test_registry.py` `5f3b5812` (`cdd04c9f`; concurrent body/docstring hunks, all disjoint from :2119); proving tests `2c8c3afc`/`9de61ae1`/`122d5398` (all dirty, every hunk outside the cited test lines). Slot-5 verified bytes: filters `8df38dd7`, orders `d784c777`, spec-027 `a73f8674`, spec-028 `f2fa4c08`, test_registry `6388dac0`. Searched population: 118 package files, tests, examples, specs, board; `--cited-by` over 681 files (twins 0 citers, relay 1 gated). Contract sources: spec-027/028 Decisions 9+11, spec-032 Decision 8, bus docstrings. HEAD `c37a08a0`. Any fingerprint change reopens.

### F2 — follow-up sub-rule for Worker-0: `clear-bus-public-trivial-wrappers`

Public 1-statement `.clear()` defs with docstrings and registration-only readers (no test/example callers; test mentions docstring-only): `optimizer/walker.py::clear_forward_names` (:322), `connection.py::clear_window_edge_class_cache` (:1436), `rest_framework/serializer_converter.py::clear_serializer_choice_enums` (:305). Refines the run note's anticipated "duo" to this trio. Held: `walker.py` is sibling-owned this run, and each docstring states a reason that must home to its ledger comment before deletion. (Kept with reason, not follow-ups: `clear_connection_type_cache`, `clear_document_key_cache`, all 5 namespace clears — direct test callers; `clear_index_advisory_dedup` — off-bus direct-call seam, has callers.)

## Defects

None meeting the bar. Axis-6 advisory item investigated with its trigger under Matrix-6; no contract source, no wire input, no card owed.

## Pending execution

None. Every proof `execution-verified` in slot-5 (run ids under Implementation); sharded/PG cells inapplicable by construction (import-time registration + `set.clear()` touch no DB, alias, or dialect — family precedent).

## Judgment

The twins are principle-11 deletions with zero responsibility, landed with their projections and pinned by failing-if-dropped oracles. Relay is the same rule, proven behavior-preserving, held only on a gated board citation whose render cycle owns to another card. The bus family verdict stands; three same-shape public wrappers are named for Worker-0.

## Implementation (Worker-1)

Slot-5 (`~/dry/ws/c3af387fc1324a21/dry/slots/slot-5`), 5 files, live tree untouched: `filters/__init__.py` + `orders/__init__.py` (wrapper defs deleted, bound `.clear` registered; ledger comments already owner-accurate, unchanged); `spec-027` (:655 code block, :891 prose) + `spec-028` (:65 prose, :620 code block) rewritten to the bound form; `tests/test_registry.py:2119` docstring reworded (inverse-proved). Relay.py NOT edited (held per Coupling). Item-scoped diff: package −8/+2 lines, specs 4 lines, tests 1 line. Runs: baseline `56fa3e` 3/3 + `b51cf8` 8/8; post-edit `1b0812` 3/3 + `126426` 8/8; prove `3a156c` 2/2 pinned + `43644c` relay-preserved; gates `853560` basedpyright 0, `146cdd` floor 0, `a8489e` truthful 0, `5031ef` commas 0, `23444d` citations 3347 OK. Post-edit `ruff check --fix` + `ruff format` clean on the 3 touched `.py` paths. Port notes: spec-028 :57-63 and `test_registry.py` body hunks are concurrent, verified disjoint from touch lines; live gained only the sibling artifact since sync. Worker-0 rows: port 5 files; tick with 1 open coupling (relay); add F2 family row; no defect homing.

## What shrinks

Rule: a helper ledger's drain-on-clear effect, previously named twice (a private 1-statement wrapper def + the registration line referencing it) for the filter and order helper ledgers. Change: delete both wrapper defs (`_clear_helper_referenced_filtersets`, `_clear_helper_referenced_ordersets`); each `register_subsystem_clear` row now takes the ledger's bound `.clear` method directly under the same owner (`filters.helper_references`, `orders.helper_references`) and flag. Owner: the [registry][registry] subsystem-clear bus — unchanged, verdict of family `subsystem-clear-lifecycle` re-confirmed (bound-method callbacks change no API, triples, or owners, so the C3 generic-record rejection does not apply; 7 of 20 callbacks were already factory closures, and spec-039 deleted this exact wrapper shape before). Net lines: package −8/+2 (two 4-line defs removed, two registration lines re-pointed); specs 4 lines reworded; 1 test docstring line reworded; relay twin behavior-proven but held for its gated board citation (exact migration + trigger in F1 Coupling). Machinery attestation: nothing added — no driver, record, flag, or helper; the registration lines name the effect they always named. What disappears forever: two maintained indirections that carried no docstring, no caller, no introspection, and no lifetime reason — every future reader of these two ledgers now sees the ledger and its drain in adjacent lines, and no projection can cite a name that behavior never needed.

## Independent verification (Worker-2)

Recorded from my own trace before reading `## Findings` (run 20, pass 1).

**Bus census (mine, live bytes + slot-5 copy).** 20 `register_subsystem_clear` call sites: rest_framework/inputs.py x2, serializer_converter.py, auth/mutations.py, auth/queries.py, orders/__init__.py, orders/inputs.py, relay.py, mutations/sets.py x2, mutations/inputs.py, forms/sets.py x2, forms/inputs.py, connection.py x2, filters/__init__.py, filters/inputs.py, optimizer/extension.py, optimizer/walker.py. Shapes: 13 module-level named `def`s (10 public `clear_*` + the 3 private trio wrappers), 4 factory closures (`make_shape_build_cache` x3: mutations/form/serializer shape caches; `make_input_namespace` x1: auth alias namespace), 3 bound-`.clear` module aliases (auth/mutations/forms declaration registries). Bus contract re-derived: `registry.py::register_subsystem_clear` stores `(clear, before_bind)` keyed by owner (plain dict overwrite); replay sites (`TypeRegistry.clear`, finalizer pre-bind sweep) call each callback bare; zero `__name__`/`__qualname__` reads in registry.py/finalizer.py; tests use `in iter_subsystem_clears()` membership only.

**Ledger-never-rebound (mine).** Exactly 3 assignments package-wide (the AnnAssign declarations); every other production use is in-place (`.add` via `build_lazy_input_annotation`, `.clear`, `.discard`, `.append`, reads); tests import the ledger OBJECTS and mutate in place. Import-time binding of `.clear` therefore always drains the object every site mutates.

**Posited changes + counts (mine).** (a) Delete each trio wrapper and register the bound `.clear`: each wrapper is its own 1-definition P11 deletion (no shared logic across the three; three independent deletions, not a consolidation — count 1 each, landed/hold decided per member). (b) Generic clearable-record driver: rejected (couples independent lifecycles/phase flags; the C3 rejection in `dry-rule-subsystem-clear-lifecycle.md`). (c) Ledger rename: 1 declaration + followers by name. Owner I choose: the registry bus, unchanged; no new machinery (inline bound method beats alias-then-register: same behavior, shorter; the 3 declaration-site aliases are precedent for the shape, not a required spelling).

**Decision I would choose.** Twins: CONFIRM and land (P11: no docstring, exactly 1 in-package reader each — def + own registration line — zero test/example callers, no introspection, no lifetime reason). Relay: CONFIRM the deletion (identical shape/proof) but HOLD it: my `--cited-by` sweep shows exactly one `path::Symbol` citer, KANBAN.md:301 [gated], and `check_citations.py` fails KANBAN.md on real rot (cited file exists, symbol gone); the fix is a board-DB edit + KANBAN.md/KANBAN.html re-render, outside the item fence. Members are independent files/ledgers/owners, so the split breaks no coupling rule.

**Projection completeness (mine).** Twin-wrapper cites outside the package: exactly the 4 spec lines (spec-027 :655/:891, spec-028 :65/:620 — bare literals, ungated but falsified prose) + tests/test_registry.py:2119 docstring (mechanism prose, falsified); tests/test_registry.py:2181 cites relay (held, correctly untouched). Zero twin cites on the board (KANBAN.md + KANBAN.html carry only the relay wrapper + unaffected ledger names). docs/builder/DONE + docs/review + prior dry-* cites are frozen history, correctly untouched. GLOSSARY cites ledger names only.

**F2 follow-up (mine).** 5 same-shape public trivials (public `def`, body a bare `<ledger>.clear()`): `clear_serializer_choice_enums` (1 reader: registration), `clear_window_edge_class_cache` (registration + test docstring cite), `clear_connection_type_cache` (pinned: 3 direct test calls + KANBAN.md:301 gated cite), `clear_document_key_cache` (pinned: direct test + `scripts/_bench_common.py` calls), `clear_forward_names` (1 reader: registration).

**Axis 6 (mine).** `_index_advisory_seen` no-defect: advisory-dedup LRU with its own public `clear_index_advisory_dedup` seam and owner prose stating its lifecycle; no contract source puts it on the bus.

**Proofs I re-ran (slot-5 copy, post-edit bytes).** 6/6 green: both co-clear proofs + filter/order/relay/connection tolerance tests. Failability 2/2 re-derived at runtime (bus row popped in-process, no source mutation: each proof's logic fails with the ledger left populated). Reload verified: owner set unchanged, callback replaced, new bound method drains the current ledger. `ruff check` + `ruff format --check` green on both touched files; `check_citations.py` 3347/3347 OK in the copy.

**Reconciliation.** Read `## Findings` after recording the above. Agreements: 20-site total; bus contract (dict-by-owner, bare replay, zero introspection); ledger-never-rebound; C1/C2 counts (1/1 each, P11 decides); C3 rejected-with-distinguisher concurring with family C3; twin CONFIRM + relay CONFIRM-but-HOLD (KANBAN.md:301 gated cite, board render outside fence, members independent); projection completeness (4 spec lines + 1 test docstring; relay :2181 correctly untouched; frozen history correctly untouched); F2 trio + keeps + pins (exact match, incl. `walker.py` sibling-ownership); axis-6 advisory no-defect + trigger; `## Pending execution` typing (`None`, sharded/PG inapplicable-by-construction reason sound); negative-control `None` with sound reason; no machinery; all freshness blobs reproduce (live, HEAD, and all 5 slot-5 bytes; `122d5398` = `tests/test_relay_node_field.py`); all 11 cited run ids bind in `evidence/runs.jsonl` with exit 0 and slot-5 package resolution, and both prove JSONs confirm the verdicts (2/2 pinned; relay migration applied-in-sandbox with zero rows failed). Differences, all immaterial to every land/hold/proof decision: (1) census split is 13 named defs + 4 factory closures + 3 bound-`.clear` aliases (auth/mutations/forms declaration registries are bound methods, not closures) — the artifact's "7 factory closures" mislabels the 3 aliases; the precedent conclusion stands and is stronger than stated. (2) Matrix-1 bucket prose sums to 21 as written ("5 namespace wrappers + serializer wrapper" double-counts `clear_serializer_input_namespace`; the namespace bucket is 4+1=5). (3) Shrinkage is gross −12/+2, net −10 (−5/file: each hunk removes blank+def+body+2 blanks+old register line and adds the re-pointed line; measured `162→157` and `149→144`), not "net −8"/"−8/+2"/"two 4-line defs". (4) F2's `clear_forward_names` line drifted :322→:312 under a concurrent `walker.py` edit mid-verify (out-of-scope dirt, left alone; my scope diff vs baseline is empty). No `## Defects` entry: (1)-(3) are per-cycle scratch arithmetic, corrected here, breaking no production or standing-doc contract. Procedural note: the pool showed "5 of 4" at verify time and refused my `verify-1` address (line 6's 6-slot growth did not hold), so proofs were re-run via read-only inspection plus in-copy runs (`ruff`, `check_citations`, focused + full `tests/test_registry.py`, runtime failability/reload probes) — no source outside slot-5 written; live tree untouched by me. Basedpyright/floor/truthful-commas gates not re-run: the edit is type-trivial (`set.clear` matches `Callable[[], None]`) with no truth-usage or layout-sensitive construct, and Worker-1's green run ids bind. Verdict: `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/relay.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
