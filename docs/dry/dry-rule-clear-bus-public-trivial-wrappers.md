# DRY review: `clear-bus-public-trivial-wrappers`

Status: verified
Run: 0.0.15 2026-10-11-20

Family `clear-bus-public-trivial-wrappers`. Item baseline `8b597495ce81d77d984f80b4141539bb836b2adf`; Worker-1 with edit rights at `dry/clear-bus-public-trivial-wrappers/consolidate` (slot-5). The item-1 F2/W2 trio nomination re-derived member by member, trying to disprove: walker + serializer CONFIRMED and landed in the copy; window CONFIRMED in shape but HELD on a foreign-hunk stop (per-member independence). Never read another worker's `worker-memory/`; never touched `rest_framework/sets.py`; live tree untouched.

## System trace

Rule: a subsystem-clear callback that is a public 1-statement `<ledger>.clear()` wrapper with a docstring, registration-only readers, and no test/example callers carries no P11 responsibility; the docstring rationale homes to the ledger comment and the registration takes the bound `.clear`.

Members, live pins re-derived: [walker][walker]`::clear_forward_names` (:312, owner `optimizer.forward_names`, ledger `_forward_names_memo` :309); [connection][connection]`::clear_window_edge_class_cache` (:1436, owner `connection.edge_class`, ledger `_window_edge_class_cache` :1431); [serializer-converter][serializer-converter]`::clear_serializer_choice_enums` (:305, owner `rest_framework.choice_enums`, ledger `_SERIALIZER_CHOICE_ENUMS` :302).

Zero-caller census per member, re-derived: def + own registration line only in the package; zero hits in tests/examples/scripts; no star-import of the three modules; no getattr-by-string; no `import ... clear_*` alias; no `TYPE_CHECKING` cite; the single test mention is docstring prose (`tests/test_registry.py:2153` names the window wrapper beside its twin). `--cited-by` over the gate corpus + standing docs: 0 citing sites for all three across 681 files — no gated `path::Symbol` citer holds any member.

Attribution vs HEAD: walker touch region :302-321 is HEAD-clean (item-2 port + truth/child-queryset hunks all outside); serializer :295-311 is HEAD-clean; connection :1431-1447 is a pure foreign ADD (absent at HEAD, unledgered) — per-member STOP, window held with trigger below.

Keeps re-derived, none lost: `clear_connection_type_cache` (3 direct test calls + gated `KANBAN.md:301` cite); `clear_document_key_cache` (test call + `scripts/_bench_common.py:382-385` call); all 5 namespace clears (filter/order/mutation/form/serializer — direct test calls each); the auth alias row is a factory-closure unpacking, not a def (no deletion shape). Bus contract re-confirmed: `register_subsystem_clear` stores `(clear, before_bind)` by owner, replays call bare, zero introspection; bound `.clear` is already the shape at 5 rows (2 item-1 twins + 3 declaration aliases). Both landed ledgers never rebound (one `AnnAssign` each; all other uses in-place `.get`/setitem/`.clear`).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** All 20 bus rows censused by body: the trio are the only public documented 1-stmt defs with registration-only readers; keeps dispositioned in the trace; window held on foreign dirt, not on shape.
2. **Sync/async twins.** Zero `AsyncFunctionDef` on the bus path; callbacks are `dict.clear()`. Trigger: a teardown callback awaiting or touching the DB.
3. **Derived rather than repeated knowledge.** Each owner string declared once at its registration; replay derives per call from the one dict. The deletion removes a name, never a derivation.
4. **Inverse / round-trip pairs.** register/replay unchanged (same owners, same flags, same ledgers). No second half exists to drift.
5. **Contracts restated in another medium.** Production (2 edited rows) + oracles (3 pinning tests green pre/post) + projections (zero trio cites in specs/board/glossary/builder; frozen history stays as written).
6. **Enforcement by omission.** Item-1's 118-file mutable census stands; the two landed touch regions add no new module-level state; the window ledger is foreign-new and its bus row rides the foreign hunk.

### Challenges

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Ledger renamed or re-containered | 1 before (wrapper body) → 1 after (registration line). Count equal; the P11 prong decides. |
| C2 | Clear gains a second effect | 1 → 1 (small callback at the registration). Same honesty: no count win claimed. |
| C3 | Generic clearable-record for the members | REJECTED, concurring with family C3: bound-method callbacks change no API/triples/owners, so the applied shape is disjoint from C3's rejection — no new type, driver, flag, or record. |

## Findings

### F1 — walker + serializer trivial wrappers (CONFIRMED, landed in the copy)

- **Contract + variation.** Each ledger drains when `registry.clear()` replays its owner row. Varies on nothing: same flag (full-only), same effect (`.clear()`), same lifetime reason (stated on the surviving ledger comments).
- **Sites + roles.** *Definitions removed (2):* the wrapper defs. *Consumers:* the bus replay (unchanged). *Oracles:* the memo co-clear test + the dedupe/collision pair (below). *Projections:* none — zero cites outside frozen history.
- **Challenges.** C1 → 1/1, C2 → 1/1, C3 → rejected-with-distinguisher. Bar basis is principle 11: registration-only readers, no introspection, docstring rationale homed (walker: 3-line drain sentence added to the ledger comment; serializer: ledger comment already stated it, recorded here per P11).
- **Owner + lifetime (principles 7, 4).** [registry][registry] bus stands (family verdict untouched — no owner/flag/ledger moved). Full-clear rows draining import-time memos.
- **Migration.** Defs deleted; each registration takes the ledger's bound `.clear` under the same owner/flag (slot-5 blobs below).
- **Shrinkage.** Package −16/+5, net −11 over live (walker −10/+4 net −6; serializer −6/+1 net −5). No new helper/wrapper/constant/flag.
- **Distinct behavior.** None — same owners/flags/effects; the [subsystem-clear][subsystem-clear] verdict stands.
- **Behavioral proof.** `execution-verified`: pre-edit 3/3 green (`65edae`); post-edit baselines green inside prove (1/1 + 2/2); failability 2/2 pinned — dropping either registration fails exactly its named test (stale memo vs `== {}`; stale `XColorEnum` erroring the collision test outside its `pytest.raises`); restores byte-proved (SHA-256 equal). Single-row pins, each rejecting a real wrong result (stale state surviving `clear()`).
- **Negative control.** None: test-isolation teardown, no auth/data-exposure surface.
- **Coupling.** None.
- **Freshness.** Live `git hash-object` (HEAD in parens): [walker][walker] `61d02873` (`ddb35b44`; touch :302-321 clean), [serializer-converter][serializer-converter] `89edbc6e` (`8e17f1ae`; touch :295-311 clean); slot-5 edited `5577636a` / `ec8feaad`; proving tests [test-walker][test-walker] `b1607a02` / [test-converter][test-converter] `f450459e` (both dirty, every hunk outside the cited lines :630-673 / :2100-2125). Searched population: package + tests + examples + scripts + specs + board + glossary + builder; contract sources: bus docstrings, item-1 F2 (re-derived, part-disproved on window). HEAD `c37a08a0`. Any fingerprint change reopens.

### F2 — window wrapper (CONFIRMED shape, HELD on foreign-hunk stop)

- Same rule, same zero-caller/zero-cite census (0/681). The one landing-time projection: `tests/test_registry.py:2153` docstring prose names the wrapper and needs the bound-form rewrite (item-1 `:2119` precedent); the board needs nothing (its `:301` clause never named this callback).
- STOP per edit rules: the whole member (ledger :1431-1433 + def :1436-1444 + registration :1447) is foreign concurrent-work `+` lines, absent at HEAD, unledgered. Nothing in [connection][connection] touched.
- Trigger: re-propose once HEAD contains the window lines — re-run the zero-caller census + `--cited-by`, seed the missing ledger comment from the docstring prose, rewrite the `:2153` docstring. No contract difference; a hold here never blocked the landed two.

## Defects

None meeting the bar.

## Pending execution

None. Every proof `execution-verified` in slot-5 (run ids under Implementation); sharded/PG cells inapplicable by construction (import-time registration + `dict.clear()` touch no DB, alias, or dialect — family precedent).

## Judgment

Two public trivial wrappers are P11 deletions with homed prose, landed and pinned by failing-if-dropped oracles. The window third is the same rule, held only on a foreign-hunk stop with an exact trigger. The bus family verdict stands; every keep re-derived with its callers intact.

## Implementation (Worker-1)

Slot-5 (`~/dry/ws/c3af387fc1324a21/dry/slots/slot-5`), 2 files, live tree untouched: `walker.py` (drain rationale homed to the ledger comment, def deleted, bound `.clear` registered) + `serializer_converter.py` (def deleted, bound `.clear` registered; ledger comment already carried the rationale). Runs: baseline 3/3 (`dry-20261011T222602-65edae`); prove 2/2 pinned (`dry-20261011T222714-ce841b`, JSON re-run same verdicts); gates `f6d488` basedpyright 0, `74ea08` floor 0, `677791` truthful-reads tier-1 0, `af5268` commas 0, `591bca` citations 3347 OK, `9658db` public-types OK (script forces `--reinstall-package`, so the green measures the edited copy). Post-edit `ruff check --fix` + `ruff format` clean on both copy paths. Port notes: both touch regions are HEAD-clean; `connection.py` NOT touched (held). Worker-0 rows: port 2 files; tick with 1 open coupling (window, trigger in F2); no defect homing.

## What shrinks

Rule: a subsystem ledger's drain-on-`clear()` effect, previously named twice (a public 1-statement wrapper def carrying the only statement of rationale + the registration line referencing it) for the optimizer forward-name memo and the serializer-only choice-enum cache. Change: delete both wrapper defs (`clear_forward_names`, `clear_serializer_choice_enums`); each `register_subsystem_clear` row now takes the ledger's bound `.clear` method directly under the same owner (`optimizer.forward_names`, `rest_framework.choice_enums`) and flag. The docstring rationale homes to the surviving owner per P11 "Prose is movable": the walker's drain sentence joins its ledger comment, and the serializer's one-liner was already subsumed by its ledger comment. Owner: the [registry][registry] subsystem-clear bus — unchanged, verdict of family [subsystem-clear][subsystem-clear] re-confirmed (bound-method callbacks change no API, triples, or owners, so the C3 generic-record rejection does not apply; 5 of 20 callbacks were already bound methods, and item-1 [helper-ledger][helper-ledger] deleted this exact wrapper shape twice before). Net lines: package −16/+5 (−11) over live; zero spec/test/board lines touched (nothing cited the landed two). Machinery attestation: nothing added — no driver, record, flag, or helper; each registration line names the effect it always named. What disappears forever: two maintained public indirections that carried no caller, no introspection, and no lifetime reason of their own — every future reader of these two ledgers now sees the ledger and its drain in adjacent lines, and no projection can cite a name that behavior never needed. The window third is the same deletion with the same proof shape, held only because its lines are foreign-uncommitted; its trigger names the exact re-proposal.

Status: verified

## Independent verification (Worker-2)

Pass 1 at `dry/clear-bus-public-trivial-wrappers/verify-1` (slot-2; pool granted the address, no fallback used). My copy synced pre-edit (live == baseline on all three paths), so the item diff was taken as slot-5 vs live: walker.py + serializer_converter.py only, -16/+5 net -11; `connection.py` IDENTICAL; the `sets.py` slot-5/live delta is live-side drift (item-3 port, slot-5 == baseline there), not this item.

My census (derived before reading `## Findings`). Bus: 20 registration rows; trio are the only public documented 1-statement defs with registration-only readers. Readers per trio member: def + own registration line only; zero hits in tests/examples/scripts; no star-import of the three modules; no getattr-by-string; no alias; no `TYPE_CHECKING` cite (package `__init__` imports other names only); neither module defines `__all__`. Citers: `--cited-by` 0/681 for all three; manual grep over specs+board+glossary+builder names the trio nowhere (`KANBAN.md:301` + spec-030 cite the keep `clear_connection_type_cache` only). Non-gated prose mentions: `tests/test_registry.py:2153` docstring (window), review/dry scratch. Ledgers never rebound (one `AnnAssign` each; only `.get`/setitem/`.clear` elsewhere). Bus replays bare with zero introspection (no `__name__`/`inspect` in `registry.py`; only other consumer is the finalizer's `before_bind` pass, untouched — landed rows stay full-only). Keeps, each with its caller intact: `clear_connection_type_cache` (3 direct test calls), `clear_document_key_cache` (test call + membership assert + bench call), 5 input-namespace clears + `clear_current_user_alias_namespace` + 3 shape caches + mutation/form declaration aliases (test refs each), auth declaration alias (already bound-method shape = precedent, not target), `_clear_node_fields_declared` (private + test ref), off-bus `clear_index_advisory_dedup` (4 test calls). My decisions: walker LAND, serializer LAND, window HOLD (whole member absent at HEAD, unledgered concurrent work).

SPLIT adjudication. (a) P8 equivalence: bound `.clear` on the same never-rebound object, same owner/flag, same replay point, no exceptions/queries/transactions/cancellation surface, no introspection consumer; reload semantics preserved (owner-keyed replace). Homing complete by quoted comparison — walker docstring "Registered with ``registry.clear()`` so a registry-clearing test drops the entries of the types it discards; the next plan rebuilds each map once." survives nearly verbatim in the ledger comment ("Drained by ..." + same two clauses), the summary clause carried by "Drained" + the adjacent `.clear` row; serializer one-liner "Reset the serializer-only choice-enum cache for a fresh build (the registered clear)." is clause-subsumed by its ledger comment ("Reset by ``registry.clear()`` via the registered subsystem clear so a fresh finalize re-emits") — "already subsumed" TRUE. (b) HOLD: ledger :1431-1433 + def :1436-1444 + registration :1447 all absent at HEAD (0 occurrences of the name at HEAD); nothing in `connection.py` touched; trigger exact (HEAD-contains-lines + re-census + seed comment + rewrite the `:2153` docstring; board `:301` verified to name only the keep); disjoint owners/ledgers/files so the hold blocks nothing landed. (c) PUBLIC-name removal: zero readers re-derived on every axis (import/alias/star/getattr-string/`TYPE_CHECKING`/`__all__`); the public spelling is incidental on module-level test-only teardown helpers, not the Meta-class public surface, with no standing contract anywhere. Deletable under the bar's P11 prong ("helper w/ no readers — what breaks if removed? nothing").

C3 concurred (bound-method rows change no API/triples/owners; 5 of 20 rows already that shape). Matrix discharged against the real surface on all six axes (own 20-row body census; sync-only; single-declared owners; register/replay halves unchanged; zero standing cites; no missed same-shape member). `## Pending execution` typing compliant; sharded/PG inapplicable-by-construction reason sound. Negative control `None` with sound reason (test-isolation teardown, bypass not the threat). Freshness: all 8 blobs reproduce (`61d02873`/`ddb35b44`, `89edbc6e`/`8e17f1ae`, slot-5 `5577636a`/`ec8feaad`, tests `b1607a02`/`f450459e`; HEAD `c37a08a0`); both touch regions HEAD-clean (nearest hunks outside; item-2 port ledgered).

Proofs re-derived in slot-2, all through `workspace.py` at my address: baseline 4/4 green pre-edit (`7e19fb`, 3 pins + my edition-agnostic drain probe); my re-typed edit independently reproduces slot-5 byte-identical both files (`f4241f`+`f60508`; one patch-script blank-line bug of mine, fixed and disclosed); post-edit 4/4 green (`a1ab7b`); failability 2/2 PINNED with byte-identical restores — walker row dropped fails exactly the co-clear assert (`666b9d`, `AssertionError` at `:671`); serializer row dropped fails exactly the collision test (`2bc136`, stale `XColorEnum` `ConfigurationError` outside `pytest.raises`, "1 failed, 1 passed"). All 8 Worker-1 run ids bind exit 0 at consolidate/slot-5 with the 2 copy_edits; prove JSON verdicts match. Public-types `9658db` measures the EDITED copy (script roots `REPO_ROOT` at its own slot-5 location and reinstalls from there) — the "forces --reinstall-package" claim stands. `ruff check` + `ruff format --check` re-run by me on both slot-5 paths: pass ("2 files already formatted"); the >99-col lines in the file are pre-existing (<=110 grace, outside the touch region). Other gates not re-run: type-trivial edit, evidence binds, and my own `--cited-by` re-derivation covers the deletion-sensitive axis.

Reconciliation (read `## Findings` after recording the above): agree on every land/hold/keep/proof decision. Two immaterial prose corrections, no `## Defects` entry (per-cycle scratch, no production or standing-doc contract broken): (1) line 18's "auth alias row is a factory-closure unpacking" — it is a bound-method alias (`= _auth_declaration_registry.clear`), i.e. already the post-consolidation shape; conclusion unchanged. (2) "all 5 namespace clears" buckets out `clear_current_user_alias_namespace`, a 6th namespace-family row pinned by import + membership assert; no lost caller either way. Shape ruling: the dual `Status:` lines STAY (verdict-neutral) — the end marker re-anchors the verdict after the uncapped `## What shrinks` tail, Worker-0 already validated the dual-line form, and both lines now read `verified` identically. No AGENTS.md prose violation in the 5 added lines (mechanism only, no provenance; no new citations; no new permanent tests). Bar met on the P11 prong with honestly-counted C1/C2 (1→1, no count win claimed), no machinery, behavioral pins failing on real wrong results, zero spec sentences falsified.

Verdict: `verified`. Worker-0 rows: port 2 files byte-identical; 1 open coupling (window, trigger in F2); no defect homing; remove `docs/dry/temp-tests/clear-bus-verify-1/` by explicit path after port.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[helper-ledger]: dry-rule-helper-ledger-clear-wrappers.md
[subsystem-clear]: dry-rule-subsystem-clear-lifecycle.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[registry]: ../../django_strawberry_framework/registry.py
[serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-converter]: ../../tests/rest_framework/test_converter.py
[test-walker]: ../../tests/optimizer/test_walker.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
