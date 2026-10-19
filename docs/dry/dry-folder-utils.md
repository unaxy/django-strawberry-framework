# Folder integration `utils/` — trace + consolidate

Status: verified
Run: 0.0.15 2026-10-09-13
Item: Folder integration `utils/` (LAST folder)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `a630d234995261ccb9920dea1b9e569a82a2bfd7` (resolves as commit)
HEAD: `23b5f42106ffd14805936560f5155dd90d7568da`
Slot: slot-2 `dry/folder-utils/consolidate`
 (`~/dry/ws/c3af387fc1324a21/dry/slots/slot-2`)

## Scope

23 tracked files: the 22 ticked member Files plus
`utils/_queryset_private.py` (TRACKED, no File row — rebase split —
traced fresh IN FULL as folder remainder, optimizer precedent).
`utils/truth.py` + `utils/lazy.py` are UNTRACKED concurrent hunt work:
never traced as members, never touched; blocking references noted
only (see Findings FAM-1, FR-8, and the per-file verdicts). Member
artifacts (run-7/run-8 era inputs, every pin re-derived):
[file-init][file-init], [file-canonical][file-canonical],
[file-connections][file-connections], [file-context][file-context],
[file-converters][file-converters], [file-directives][file-directives],
[file-errors][file-errors], [file-execution-mode][file-execution-mode],
[file-imports][file-imports], [file-input-values][file-input-values],
[file-inputs][file-inputs],
[file-operation-lease][file-operation-lease],
[file-permissions][file-permissions], [file-policies][file-policies],
[file-private-state][file-private-state],
[file-querysets][file-querysets], [file-relations][file-relations],
[file-sessions][file-sessions], [file-strings][file-strings],
[file-typing][file-typing],
[file-write-transaction][file-write-transaction],
[file-write-values][file-write-values]. Traced against [plan][plan].

Item-scoped diff check: `git diff a630d234 --stat --
django_strawberry_framework/utils/` is EMPTY (BASE=WT over the folder;
the only BASE→WT move in the tree is the plan file's own dispatch
lines). Slot-2 verified byte-identical to the worktree on all 23
targets before any tracing (per-file `git hash-object` comparison).

| File | WT blob | HEAD blob | WT / HEAD lines | Dirt |
|---|---|---|---|---|
| `utils/__init__.py` | `53e75973` | =WT | 56 / 56 | clean |
| `utils/_queryset_private.py` | `a26a8d43` | `ff8b2b46` | 150 / 143 | 1 hunk, hunt |
| `utils/canonical.py` | `23a7c41a` | `a1209117` | 102 / 102 | 4 hunks, hunt |
| `utils/connections.py` | `2313fce5` | =WT | 985 / 985 | clean |
| `utils/context.py` | `127a2c15` | `d6937a21` | 248 / 259 | 2 hunks, hunt |
| `utils/converters.py` | `53ce2b2e` | `eb0f708d` | 207 / 220 | 4 hunks, hunt |
| `utils/directives.py` | `23421f6b` | `09e0de24` | 80 / 79 | 3 hunks, hunt |
| `utils/errors.py` | `e9572ea9` | `9cf4e952` | 452 / 564 | 7 hunks, hunt (FF-13) |
| `utils/execution_mode.py` | `b86a08cd` | =WT | 156 / 156 | clean |
| `utils/imports.py` | `3ea52b16` | =WT | 144 / 144 | clean |
| `utils/input_values.py` | `b0a2c66a` | `01c46036` | 372 / 443 | 11 hunks, 3 mixed f45-line |
| `utils/inputs.py` | `0b8d3daa` | `c199eaa4` | 1602 / 1582 | 20 hunks, 1 mixed f45-line |
| `utils/operation_lease.py` | `d1d272c5` | =WT | 78 / 78 | clean |
| `utils/permissions.py` | `f12edaf8` | `abf4239d` | 913 / 965 | 14 hunks, hunt |
| `utils/policies.py` | `ca9914b8` | `7fe7f8a6` | 188 / 192 | 7 hunks, hunt |
| `utils/private_state.py` | `78d6692f` | `ec4d8fc8` | 322 / 288 | 8 hunks, 7 f53 + 1 mixed |
| `utils/querysets.py` | `e6660894` | `4d8a3d39` | 5061 / 5139 | 75 hunks, hunt |
| `utils/relations.py` | `cc68c6ba` | `63f46750` | 903 / 1007 | 20 hunks, 1 ledger + 19 hunt |
| `utils/sessions.py` | `de3cf2c9` | `e3c7142b` | 399 / 415 | 7 hunks, hunt |
| `utils/strings.py` | `0b1774a7` | `1a49fe42` | 291 / 289 | 2 hunks, hunt |
| `utils/typing.py` | `b7e69600` | `3a5dae39` | 384 / 384 | 2 hunks, hunt |
| `utils/write_transaction.py` | `50909be8` | `2b9f861c` | 1268 / 1272 | 17 hunks, hunt |
| `utils/write_values.py` | `1dc426d4` | `a9d6fa32` | 542 / 507 | 8 hunks, hunt |

212 `@@` hunks total. Ledger rows naming folder paths (Owned changes
skimmed in full): exactly four — relations.py adopted-orphan prose,
inputs.py f45, input_values.py f45, private_state.py f53. Every other
hunk attributes to the hunt by diff content (truth-migration spelling,
`_safe_*` removal, guard deletion, id-dedup, exception narrowing),
never by filename. The f45/f53 ledger lines sit INSIDE hunt-rewritten
hunks (line-level mixed); attribution below is per line.

## Method

Five read-only deep-tracers covered disjoint file groups (A:
querysets pair; B: inputs trio; C: connections+relations; D:
write+errors+permissions; E: 12 small files), each re-deriving pins,
enumeration, dirt, drift, member verdicts, and in-group twins from WT
bytes. Packs A/B/C arrived intact; every load-bearing claim in them
was re-verified first-hand (spot censuses below). Packs D/E were
truncated in delivery and a shell outage blocked extraction, so the D
and E groups are traced FIRST-HAND in this artifact: full source
reads of all 16 files at WT bytes, member-artifact enumerations
re-read, every index row re-checked against bytes. Allfolder-level
attribution, composition censuses, FAM verdicts, and falsifications
are Worker-1's own bytes-derived work regardless of group.

Audited in full, first-hand: the 4414-line HEAD→WT folder diff (every
hunk), all 23 WT sources except connections.py/querysets.py/
relations.py/inputs.py (covered by intact packs A/B/C plus targeted
re-reads), the f45/f53/f47/f55/f46/e8 family records where cited,
and every census quoted (commands reproduced under Findings).

## Attribution (per file, `git diff HEAD -- <path>`)

- `_queryset_private.py` (1): docstring +7 stating the
  `truth.instance_state` read vs module-write split — hunt (names the
  untracked hunt module; no ledger row).
- `canonical.py` (4): docstring neutralization ×2, import swap (f45
  owner untouched), dispatch gates + refusal + sort key (5 arms
  otherwise byte-identical) — all hunt.
- `context.py` (2): read/write except-narrowings — hunt.
- `converters.py` (4): truth import, `_MroGetter` deletion,
  `truth.mro` substitution — hunt. (`_MroContinue`/`MRO_CONTINUE`
  intact at WT :49/:65.)
- `directives.py` (3): manifesto prose, truth import +
  `any(truth.is_instance …)` gate, `except Exception`→`TypeError`
  (the member artifact's predicted C3 probe, discharged) — hunt.
- `errors.py` (7): import reshape, 3× `truth.text` substitutions,
  `_str_list` rewrite + `_is_text_atom` + `_leaf_codes` (5 helpers
  deleted), `_error_dict_entry` deletion, mapper rewrite, path-join
  substitution — ALL hunt. The dispatch note claiming MIXED
  ledger+hunt is not borne out by content: no ledger row names this
  path and no hunk matches ledger content (f47's owner
  `coded_error_extensions` is untouched committed content; its two
  composition sites live in schema.py/list_field.py). See FF-13.
- `input_values.py` (11): 3 MIXED hunks carrying the f45 ledger lines
  (`from .canonical import base_container_values` :42;
  `pairs = base_container_values(input_value)` :110;
  `elements = base_container_values(input_value)` :340) inside
  hunt-rewritten gates; 8 hunt-only (gate migration, guard deletion,
  `"unreadable"`-kind deletion, BaseException-guard deletion).
- `inputs.py` (20): 1 MIXED hunk carrying the f45 ledger line
  (`for key, value in base_container_values(fields)` :587) beside
  hunt gates; 19 hunt-only (incl. WT-added `_UNORDERED_TYPES` :526 +
  `_is_one_of` :529 + `_META_ABSENT` :536). f45's site-A one-liner is
  absent: committed `899cb35b` deleted `_hashable_meta_value` while
  its arm still read `dict.items(v)` (FF-1).
- `permissions.py` (14): truth+lazy imports, `_context_request`
  tuple→single rewrite (closes D2 — the false `__getitem__` half is
  a `-` line), WT-added `_is_request` (`+def`, hunt-authored FL1
  extension), `_safe_get_model` narrowing, `"unreadable"`-arm
  deletion — all hunt.
- `policies.py` (7): truth+lazy imports, `display_name` param
  orphaned by the read-failure-message deletion (hunt-caused dead
  parameter; no DRY action), ladder rewrite, `truth.describe` — hunt.
- `private_state.py` (8): 7 f53 ledger hunks (`PayloadT` + `_Entry` +
  `_IdFiledEntries` driver :72-139, both stores composing by name,
  `_settled`/`_accepted`/`_Accepted` deleted with zero residue) + 1
  mixed hunk whose `object.__setattr__` lines are the
  concurrent-external hunk the f53 record attributes by content (the
  adjacent `self._filed.file(…)` line is ledger).
- `querysets.py` (75): all hunt truth-migration (~59 mechanical
  swaps: 131 added `truth.*` lines, HEAD has 0; `_safe_class_name`
  + `_is_class` deleted; `_safe_routing_repr`→`_routing_repr` +
  `_ROUTING_SCALAR_TYPES`; coerce except-narrowing; guard removals
  incl. the seal unreadable-state arm :3779-81; `_readable_queryset_state`
  `origin` param dropped). Zero ledger rows name this path.
- `relations.py` (20): hunk 7 (`@@ -366,6 +305,20`) is THE
  ledger hunk — `classify_path` docstring +14, pure additive prose,
  verbatim the adopted orphan (WT :309-321). Other 19 hunt
  (`safe_truthy`+`relation_attr`+`lenient` axis deleted — f43
  extinction; Col-cursor rewrite; guard deletions).
- `sessions.py` (7): truth/lazy import growth (2 function-local
  cycle dodges :184/:214), 3 message-field deletions + guard
  deletions (4-arm→1.5-arm containment), engine-tail narrowing —
  hunt.
- `strings.py` (2): truth import + gate substitution — hunt.
- `typing.py` (2): truth import + `is_async_callable`
  class/instance `__call__` unification — hunt.
- `write_transaction.py` (17): `_is_one_of` + `_FINGERPRINT_CONTAINER_TYPES`
  additions, gate migration, `bool`-literal + mapping-config
  substitutions, probe/comment rewrites — hunt (no ledger row).
- `write_values.py` (8): docstring touch, truth import, NodeID-batched
  decode rewrite (function-local relay-private imports) — hunt (no
  ledger row; f63 stays blocked).
- Clean (0 hunks each): `__init__.py`, `connections.py`,
  `execution_mode.py`, `imports.py`, `operation_lease.py`. All five
  differ from their run-7 blobs by COMMITTED drift only (homed per
  file below: S0c growth + `PayloadT` variance + formatting/prose).

## Matrix

1. **Cross-flavor policy mirroring — SEARCHED.** The write flavors
   (model/form/serializer) consume the folder's decode spine
   (`decode_visible_relation`, `decode_visible_relation_ids`,
   `decode_provided_fields`, `decode_field_handlers`), the scalar
   leaf order, and the preflight by name (FC-WRITE); flavor-kept
   colorings (model null-reject, form `empty_values`/`to_field_name`,
   serializer None-passthrough + nested recursion) verified
   intentional at their bodies. No mirrored rule; the one genuine
   cross-file mirror found is FAM-1 (hunt-authored, held).
2. **Sync/async twins — SEARCHED.** AST census: 8 module-level
   `async def` (`querysets.py` ×7 incl. 3 overloads of
   `apply_type_visibility_async` + `run_in_one_sync_boundary`,
   `sessions.py::actor_transition` ×1), 0 nested. The applier
   sync/async pairs converge on rowed families (e7 twins, boundary
   s20); `actor_transition` has no sync twin (lease is an
   `asyncio.Lock` — twin impossible); `permissions.py`/`typing.py`
   "async def" hits are docstring prose. No new twin.
3. **Derived rather than repeated — SEARCHED.** Gate names derive
   once (`_check_method_name` over composed `flatten_lookup_path`);
   camel names derive once (12 calls, 5 files, FC-STRINGS);
   fingerprints derive once (FC-CANONICAL). The `_is_one_of` triple
   is the single re-derivation found (FAM-1).
4. **Inverse / round-trip pairs — SEARCHED.** `graphql_camel_name`
   / `snake_case` exact-inverse pair (member-verified, oracle-pinned);
   snapshot capture/compare closed via `matches()` methods (member
   L9). No unowned inverse.
5. **Contracts in another medium — SEARCHED.** 1176 + 107 witness
   rows green in slot-2 (see Verification); census gates (f45 7-hit,
   f53 store census, f47 single-site, f55 supplied rows) all green.
   Docstring-vs-body re-read on all 23 files: riding defects listed
   under Defects, 2 closures + 1 narrowing recorded, no new defect.
6. **Enforcement by omission — SEARCHED.** Leaf withholding holds
   (root re-exports nothing from utils/ — 0 hits); `__all__`-less
   substrate modules (7) are imported by name everywhere with zero
   executable star imports package-wide (only prose mentions). No
   omission gap.
7. **Boundary ContextVars — SEARCHED.** `_MANAGED_WRITE_ALIAS`,
   `_WRITE_PIPELINE`, `_OPERATION_MODES` each single-owned with
   disjoint scopes (write-alias flag vs pipeline record vs executor
   mode); the lease-vs-ContextVar separations converge on standing
   rows. No shared driver.
8. **Exception-shape twins — SEARCHED.** Zero `except BaseException`
   folder-wide at WT (AST census, all 23 files); 12 `except` arms in
   write_transaction.py, 1 in private_state.py, all per-site
   verdicts converging on J1. `SyncMisuseError`/`ConfigurationError`
   discipline holds. No twin.

## Member verdicts

Verdict vocabulary: CONVERGE (row's family/standing verdict
re-confirmed at WT bytes), STAND (file-local row intact),
REVISE (verdict stands with refreshed evidence/counts/pins), SPENT
(subject extinct), FALSIFIED (verdict contradicted — always with the
superseding record). Fresh pins re-derived; artifact pins cited only
to confirm or correct.

### `utils/querysets.py` (pack A, load-bearing claims re-verified)

WT 172 top-level nodes (123 sync + 7 async + 8 class + 34 const),
unique 166; s16→WT +18/−5, each homed: 8 seal-body predicates +
2 order-rewrite parts + `VisibleRowExists` + relation-hop trio
adopted into file-local/seal-body homes (committed); `_ROUTING_`
rename rides the F12 row (hunt); −5 spent (2 hunt-deleted,
`is_async_queryset_adapter` + post_process pair deleted by committed
`899cb35b` — F9 spent, e6 row stale per FF-8).
F1(e1)→converged in WT via owned dirt out-of-group (HEAD still
carries `_close_unawaited`; converges pending commit); F2/F4/F5/F6/
F7 CONVERGE; F3 REVISE (rule holds, cause-text oracle narrowed —
FF-15); F8 CONVERGE (still 2 mechanisms — pack A's `_scoped_seed_rows`
site misattributed: the run-13 filters FAM-2 body composes mechanism 1
at filters/sets.py:1546 and is counted in FF-4's 14, not a new
mechanism); F11
REVISE (consumers 5→7 files incl. NEW committed `views.py:1145`,
direct `sync_to_async` 7→3 — FF-5); I-R6 RETIRED/spent at WT (both
sides hunt-deleted; HEAD holds the pair — FF-10); I-R1/R2/R4/R5,
F10, F12 rows STAND/REVISE-pins. D1 persists fixed (re-verified);
D2–D5 persist; O1 persists strengthened; O2 closed-concurrent.
New in-group: T2 `_is_exact` order pair → FR-3 (reject);
T1/C3 charter-gap slots → FAM-2/FAM-3.

### `utils/_queryset_private.py` (fresh trace, no artifact)

19 nodes: 14 defs + `PrefetchLookup`/`DeferredFilter` +
`_QuerySetT` + docstring. Exclusivity re-proved for the 10 covered
slots (zero executable `._db/._hints/._fields/
._prefetch_related_lookups/._deferred_filter/._defer_next_filter/
._sticky_filter/._for_write/._query/._chain` spellings in
production outside this module). Every member homed: 9 in the
module family (incl. f61/f65 owners), `DeferredFilter`/`_QuerySetT`
typing shells, 6 test-only members → O-NEW-1 (verdict KEEP: tests
are callers under the exclusivity charter; deleting re-scatters
spellings — counts 6, correcting pack A's "five"). Read/write
pairs STAND as paired directional bodies (principle 5: no mode
flag). The 2 uncovered slots (`_result_cache`, `_iterable_class`)
→ FAM-2/FAM-3; seal snapshot string-keys correctly separate (FR-7).

### `utils/inputs.py` (pack B, load-bearing claims re-verified)

WT 64 nodes (29 def + 4 class + mechanics). Drift 60→64: 10 names
removed by committed `899cb35b` (all homed: 4 rejections SPENT —
incl. R-depth-caps, whose index row now dangles per FF-7 — plus
family rides); 7 TypeVars + TYPE_CHECKING (committed typing);
`_is_one_of`/`_UNORDERED_TYPES`/`_META_ABSENT` (hunt). A-factory-bfs
(A-factory-bfs/STAND), A-provisional-name (STAND), A-clear-bus
(STAND), A-imports (STAND) CONVERGE; A-dynamic-getter REVISE/spent
(names grep-0 package-wide — converges with deferred f32
retire-or-revise, FF-3); A-baseslot REVISE (site A spent FF-1, site
B :587 composed); A-membership REVISE (3→2, FF-2). 25 FL STAND
(modulo FL-mechanics counts); 11 rejections STAND (R-alias-arm
byte-stable; R-graph-walks STANDS despite hunt `id()` convergence
— DFS-vs-BFS + visit contracts still differ; R-model-guard callers
still forms + rest_framework only); R-guards REVISED (zero
`except BaseException` left). D1 NARROWED to limb (c) — WT:575
still claims "`repr`-sorted lists" while the body sorts by
`canonical_sort_key` (:522) — rides (hunt-adjacent hunk, no edit).
In-group T1–T12 all NOT TWINS (T1's membership question homed in
f46/f64 — compatible with FAM-1, which names the defs, not the
dispatch; expected fusion noted at FAM-1).

### `utils/input_values.py` (pack B)

WT 26 nodes; zero added/removed/renamed def/class/assign names
run-7→WT (17/17 identical) — drift is imports + bodies only.
F-FA CONVERGE (:110/:340 composed, :134 resolved as f45 R-E);
F-NEW CONVERGE (f51 binder + 5 compositions re-pinned);
FL1/FL2/FL3/FL5/FL6 STAND (FL2 exactly 19 calls / 6 files
re-derived: 10+3+3+1+1+1; FL5 exactly 2 callers :355 +
permissions.py:793); FL4/FL7/FL8 REVISED evidence (label read →
`truth.qualname`; 11 BaseException guards → 1
`RelatedDeclarationError` guard, zero `BaseException`; imports
5→7, still no family package / no `__all__`); R1–R5 STAND, R6
REVISED (J1 spent, J2 unfired). Zero defects STAND. O3 persists
(= permissions D1 — recorded once there).

### `utils/canonical.py` (pack B)

WT 13 nodes (2 def names + overloads + TypeVars + truth import).
FA CONVERGE (5 arms intact :73-82; 3/4 inlines composed, 1 spent
FF-1); FB REVISE (count 3→2, FF-2); L1 STAND (consumers
re-derived: inputs.py:522 + write_transaction.py:1053/:1073 —
1 call + 2 key-references); L2 REVISED (production importers
2→3: inputs/input_values/write_transaction); R1 SPENT; R2/R4/R5/R6
STAND; R3 REVISED (exclusions 3→1, two migrated to `truth.render`
— FF-16); R7 REVISED (sorted-list vs digest-string separation
prose intact). D1 = inputs D1 (routed; narrowed per above).

### `utils/connections.py` (pack C, clean — WT=HEAD)

WT 50 nodes. Drift s15→WT: +4 cursor-validation defs (+2 imports),
one family ride (offset entries compose `validate_offset_pagination`)
— committed. C1 REVISE (+4 homed; `page_arguments` 3 readers
re-pinned); C2/C3 STAND; F-new (f20) CONVERGE (9/9 defs);
L-sidecar STANDS; L-supplied CONVERGE (f55: binding :166-179 +
list_field ×3 :452-454 + 0 raw spellings); L0 REVISE (counts);
R1–R9 STAND (R5/R7/R8 local halves; remote halves converge on
standing rows); O1 SPENT/STAND; O2 LANDED/STAND; s10-R14 hold
CONFIRMED (single `last == 0` site :208, package census).
Zero defects persists. In-group (a)–(d),(k)–(m) homed;
CND-1→FR-5, CND-2→FR-6, CND-3/CND-4 converge (dedup, no new family).

### `utils/relations.py` (pack C)

WT 50 nodes. Drift orig→WT: +9 committed (link cluster → new FL
rule; `leading_relation_hops` → F-ORM facet; `is_single_column_
foreign_key` → FL gate; contract split) + cache-alias committed
removal; HEAD→WT: `safe_truthy`+`relation_attr` hunt-deleted
(f43 extinction). F-TAX CONVERGE/STAND (R-C narrowing owed:
zero lenient consumers); F-ORM CONVERGE/REVISE (ladder minus the
BaseException arm; H7 prose :309-321; 4 walkers re-pinned);
F-ACC CONVERGE/STAND (strict-only; renderers now untracked
`truth.kind`); F-LENIENT FALSIFIED (owner absent, count 2→0 —
superseded by f43, FF-9). FL rows STAND/REVISE-mechanics
(`__all__` 17→20: +5 link, −2 lenient); R1–R6/R8–R33 STAND or
REVISE (R7 FALSIFIED as WT statement — FF-9; R14 trigger moot;
R21 FALSIFIED as WT consumption — picker side resolved: zero
residue package-wide, no broken import); R23 population
hunt-narrowed, direction stands. D1 persists (byte-identical :150);
D2 persists (4th consumer forms/inputs.py:460 + import :72
re-confirmed).

### `utils/write_transaction.py` (first-hand: full WT read)

WT 53+ nodes. Net run-7→WT: +`_ModelT`/`_QuerySetT` (committed
typing) + `_is_one_of` :848 (hunt → FAM-1) +
`_FINGERPRINT_CONTAINER_TYPES` :839 (hunt → f46 Spelling B ride) +
import growth; minus none. All 13 FL (L1–L13) STAND as single
definitions (re-read in full): managed-alias, pipeline substrate,
phase flag, read-only barrier, SQL phase gate, alias guards,
alias pinning, canonical-pk trio, snapshot capture (compare side
still closed via `matches()`), fingerprint walk (gate dual-homed
to open f46 — Spelling B survives at :839-845/:1026), drift
compare (serializer-only), row locks, conflict trio.
Converge/consume: `conflict_error` composes `field_error` (:1213);
`base_container_values` ×3 (:1052/:1066/:1073) + `canonical_sort_key`
×1 call + 1 key-reference (:1053/:1073); `queryset_db` composed
at :740. All 10 R STAND: hook-context (remote R1), pk-vs-coercion
(e4 R1; `canonical_pk` to_python-direct), leaf-tail/atom
(canonical R2/R4), fingerprint-vs-meta-encoding (canonical R7),
wording (policies R3), except-guard J1 (12 arms, 0 BaseException),
drift-vs-intent-ledger (remote), pipeline-vs-op-lease
(owner-recorded), snapshot-vs-fingerprint-set (in-file: sets
differ by `bytearray` + order — intentional). Zero defects
persists (full re-read, nothing found).

### `utils/write_values.py` (first-hand: full WT read)

WT 28 nodes, names IDENTICAL to run-7 (17 defs + 1 const; import
spelling evolved: +truth hunt, +relay committed, TYPE_CHECKING
extended). All 12 FL STAND: mechanics (REVISE counts: 8 imports,
all consumed — verified each), preflight (consumers: in-file
:191 + auth login :642-643 + register :1227 ✓), choice-unwrap
(sole consumer the leaf :190 ✓), scalar-leaf order ✓, raw-pk
pick (consumers :168 + model locate arm mutations/resolvers.py:1401
✓ exact), id-check (two-branch + function-local relay import ✓),
single spine (skip/type-check/visible/project + no-attach-unseen
✓), atom set (Mapping-bearing, bilateral separation recorded at
errors.py:85-86 ✓), materialize (consumers :324 + form multi
forms/resolvers.py:279 ✓ exact), batched decode (L10; body
hunt-dirtied — NodeID batching; f63 stays blocked), store
vocabulary (three riders re-derived: form factory
forms/resolvers.py:330 + serializer factory
rest_framework/resolvers.py:398 + model primitives
mutations/resolvers.py:528/:539/:555/:557 ✓), provided walk
(single map + UNSET strip + scalar default + first-error ✓). All
8 R STAND except storage-read-vs-render-read → REVISE (remote
`_safe_text` extinct in exceptions.py — FF-12; separation holds
on the truth-render basis). O1 CLOSED (docstring :148-150 now
states the batched non-pk query). Zero defects persists.

### `utils/errors.py` (first-hand: full WT read)

WT 34→~30 nodes. Net run-7→WT: −5 validation helpers −
`_error_dict_entry` (hunt) + `_is_text_atom` :197 (hunt → FAM-1
specialized site) + `_leaf_codes` :216 (hunt, 2 in-file callers)
+ `build_error_key_map` :283 + `model_field_error_names` :330 +
`ErrorKeyMap` (COMMITTED post-run-7 feature — single definitions,
5 + 2 cross-flavor callers by name: rest_framework ×3+1,
mutations ×1+1, forms ×1 — homed NEW file-local); `__all__`
18→19, all defined. FL1 mechanics REVISE (counts + seam intact
:173). 8 envelope converges hold (sole ctor, code table 7/7
re-counted :111-117, flat mapper with reworked private readers,
integrity/relation/null/empty leaves, dotted grammar :185 +
testing/client.py:335 + filters/sets.py:505 — three contracts
intact); f47 coded-shape holds (owner byte-untouched + 10
composers incl. schema.py:710 + list_field.py:326). 8 R:
text-atoms (CONVERGE — tables differ by 5th member, bilateral
prose intact), path-split (STAND), coded-vs-correlation (STAND),
django-vs-drf-readers (REVISE — owner re-pinned to `_leaf_codes`,
`.code` read intact), envelope-vs-extension (STAND),
per-condition-wrappers (STAND), three-save-mappers (STAND),
safe-renderer-composition (BASIS EXTINCT — `_safe_text`/
`_unprintable` gone from exceptions.py — FF-11; separation holds
on the truth-text basis, row needs re-homing). D1 CLOSED (auth
imports the leaf directly at both sites :547/:1210;
`resolvers.field_error` 0 hits in auth/mutations.py; fixer era
undetermined — closeout attributes via pickaxe). D2 persists
("DIRECTLY" :267 verbatim).

### `utils/permissions.py` (first-hand: full WT read)

WT 32→40 nodes. Net run-7→WT: +`_is_request` (`+def` — hunt-authored
FL1 extension, single definition) + `RelationHop` +
`walk_declared_relation_path` + `_walk_undeclared_hops` +
`_set_model` + `set_bound_type` + `relation_path_gates` +
`_key_gate_path` (committed flat-path-gates feature — FL5
extension, each single-owned) + truth/lazy/relations/strings
imports; minus none. FL1–FL6 STAND (ladder + adapter + helpers;
auth-alias derivation; gate dispatch incl. `_GATE_ASYNC_RECOURSE`;
walk orchestration; flat-path parity incl. the new walk;
mechanics with 11-name `__all__`). 2 convergences hold (F-AWAIT
consumer :409-415; F-FA dict arm :806). All 8 R STAND: R1 twin
wording distinct + composed at mutations/permissions.py:110
(trigger unfired); R2 half-strength shape intact; R3 (declarations
still any-`Mapping` — trigger unfired); R4 (context R2); R5
(fail-soft posture kept — `LookupError`-only narrowing); R6 (J1/J2
unfired — no exact-type gates added); R7 (no vocabulary-validated
read); R8 (tolerant `partition` intact :310). D1 persists (all
three sites: input_values:294-296 + :786-788 + conditional body
:805-808 — recorded once, = input_values O3). D2 CLOSED by hunt
reword (false `__getitem__` half is a `-` line in the HEAD→WT
diff; surviving `get`-only claim verified true). O1 persists
(filters/sets.py:87 imports from input_values directly; comment's
consumer name stale — observation, no defect).

### `utils/__init__.py` (first-hand: full WT read; clean)

5 statements, enumeration-identical to run-7 (S0a/S0b/S0c + 3
imports + 7-name `__all__`; blob delta non-structural except S0c
growth). FL1 manifest STANDS (7 names, identity oracle
tests/utils/test_init.py:35-40 green); FL2 prose STANDS. R1
(leaf-vs-root) CONVERGE — root re-exports nothing from utils/ (0
hits); R2 (leaf-vs-sibling) CONVERGE — manifest intact. D1
persists REVISED: (a) persists — zero short-spelling consumers
of the seven (only the oracle reads `utils.<name>`; every
production consumer uses dotted-submodule paths — package-wide
census); (b) NARROWED by committed evolution — S0c now names
20/23 submodules (only `connections` unnamed; was 9/21);
(c) persists, strengthened — 7 submodules without `__all__` (was
5; +`inputs` posture + new `_queryset_private`).

### `utils/context.py` (first-hand: full WT read)

12 statements, names IDENTICAL to run-7 (5 public names +
mechanics). 5 FL + 8 R all STAND (hunt narrowed excepts,
body-only; the F1(b) concurrent-external narrowing the artifact
already predicted). Zero defects persists.

### `utils/converters.py` (first-hand: full WT read)

Net run-7→WT: zero name-delta (`_MroContinue`/`MRO_CONTINUE`
intact :49/:65; `_MroGetter` lived only at HEAD, deleted by
hunt; truth import was already WT dirt at run-7). F-DISPATCH
(4 call sites re-derived: serializer_converter.py:567,
forms/converter.py:267, filters/inputs.py:632/:748 ✓),
F-SENTINEL (2 consumers: forms :218 + filters :738 ✓),
F-VALUE (both factories), F-FINISH, F-MECH all STAND. 6 R
STAND (singledispatch refusal home intact at
forms/converter.py:243 + serializer_converter.py:23; R14
J1/J2 unfired). Zero defects persists.

### `utils/directives.py` (first-hand: full WT read)

Net run-7→WT: zero name-delta (truth import already dirt at
run-7; `_safe_type_name` import dropped for `truth.kind`).
F-VALIDATE STANDS (1 def + 6 field-factory calls re-derived:
auth/mutations.py:479, relay.py:644/:753, mutations/fields.py:336,
connection.py:2444, list_field.py:1598); F-MECH STANDS. 5 R
STAND (J1 per-site verdict kept under the `except TypeError`
narrowing; C3 probe discharged — the narrowing counted 1 in
both states as predicted). D1 persists (every-factory sentence
:3-5 still omits the connection-factory consumer :2444).

### `utils/execution_mode.py` (first-hand: full WT read; clean)

15 nodes, enumeration-identical to run-7 (docstring + 7 imports +
5-name `__all__` + `OperationMode` + `_OPERATION_MODES` + 4
functions). f48/f49/f50 CONVERGE (compositions hold:
`OperationLease` :52 + `SyncMisuseError` :53; 11 referencing
files); FL1/FL2 STAND; 7 R STAND (4 lease readers re-derived:
operation_state ×2, resource_policy, execution_mode,
optimizer/_context — the row's "4 readers" counts modules:
4 modules, 5 constructions). Zero defects persists.

### `utils/imports.py` (first-hand: full WT read; clean)

13 members, enumeration-identical to run-7 (floors still
"4.3.2"/"0.316.0", 6-name `__all__`, stdlib-only layering
intact — the fact R1 relies on). 6 FL STAND; F1 ADOPT holds
(f34 consolidated: 4 wrappers + keyset ×2 direct re-derived:
auth/sessions.py:127, routers.py:248, debug_toolbar.py:118,
rest_framework/__init__.py:58, keyset.py:447/:451); 6 R STAND
(R1 twin: pass-through vs fail-closed + stdlib-only — the
difference is SHARPER at WT since strings now depends on
package `truth`; trigger unfired). O1 stands observed-not-homed
(glossary staleness, owned elsewhere). Zero defects persists.

### `utils/operation_lease.py` (first-hand: full WT read; clean)

6 statements. Net run-7→WT: exactly one token of committed
drift — `PayloadT` gained `covariant=True` (77→78 lines).
FL2 mechanics REVISE (variance noted); FL1 + 6 R STAND (4
consumer modules re-derived — same 4 as execution_mode's
readers; ledger/actor/authority/boundary separations intact;
O1 `__weakref__` slot persists observed). Zero defects persists.

### `utils/policies.py` (first-hand: full WT read)

Net run-5→WT: zero name-delta (6 members); imports evolved
(+truth/+lazy hunt, −`describe_value` hunt — `truth.describe`
replaces). f12/f13 CONVERGE (owners intact; `canonical_policy`:
3 external + 3 in-ladder calls; `copy_policy`: 6 calls in 3
files — FF-14: error_policy + conf no longer call, census was
4 files; `resolve_policy`: error_policy:168 + resource_policy:523
✓). f14 rejection scope intact. Article + mechanics FL STAND.
6 R STAND (R3 per-subject grammars intact — the CONVERGE hub
for the inputs/input_values/write_transaction/canonical wording
rows holds). Hunt-orphaned `display_name` noted, no action.

### `utils/private_state.py` (first-hand: full WT read)

f53 CONSOLIDATED holds with zero residue: driver + `PayloadT` +
`_Entry` present, both stores compose by name (`self._filed`
inits + `.has`/`.file`/`.verified`), `_settled`/`_accepted`/
`_Accepted` extinct (only `_accepted_member` helper +
unrelated `extensions_settled`/`is_accepted` spellings remain).
3 FL STAND (mechanics REVISE: +f53 members); f53 R1–R6 STAND
(R2's `truth.py::IdentityMap` still untracked — trigger
uncheckable, row stands as rowed). 6 file R STAND. Zero defects
persists.

### `utils/sessions.py` (first-hand: full WT read)

Net run-7→WT: zero name-delta (12 members + 10-name `__all__`).
FL0/FL1/FL4/FL5/FL6/FL7/FL8/FL9 STAND (3 scope-key declarations
+ 2 engine callers + 4 lease holders + sole transition holder
auth/mutations.py:969 + lease-order projection all re-derived).
FL2 REVISE (record 4 fields → 1 `corrupted`; single data site
auth/sessions.py:96 migrated to 1 kwarg); FL3 REVISE (4-arm →
1.5-arm containment; C4's posited change HAPPENED — coupled
triple moved together as predicted). 12 R: 10 STAND (R-J1
trigger moot at 1 arm — REVISE note; safe-render basis extinct
— FF-11, separation holds on the `truth.describe` basis).
Zero defects persists (narrowings are hunt-owned body changes,
not docstring contradictions — the surviving prose matches).

### `utils/strings.py` (first-hand: full WT read)

Net run-7→WT: zero def-name-delta (7 defs + 3 assigns +
exact-5 `__all__`); imports grew (+truth hunt, −`_safe_type_name`
hunt, +typing machinery committed). FL0 REVISE (counts; zero
star-importers re-verified); FL1 STAND (4 direct + 1 transitive
consumers); FL2 STAND (memo + controls + off-clear-bus); FL3
STAND; FL4 STAND (2 consumers re-derived: sets_mixins.py:125 +
filters/inputs.py:286 ✓ exact); FL5 STAND (12 calls / 5 files
re-derived EXACT: 1+4+3+2+2 ✓); FL6 REVISE (3→4 mangle sites —
FF-6; docstring leg (a) covers the new site). 8 R STAND
(R7 trigger unfired — exactly the 4 known lines package-wide;
R8 encodings still differ; J2 still 1 message).

### `utils/typing.py` (first-hand: full WT read)

Net run-7→WT: zero def-name-delta (9 defs + ceiling 64 +
exact-9 `__all__`); +truth import (hunt). FL0 REVISE
("stdlib-only imports" now FALSE — truth import added; row
claim needs update); FL1 (1 consumer via alias ✓), FL2 (2: 1
alias + 1 in-file ✓), FL3 (4 calls / 3 files ✓), FL4 (64 +
4 peels + loud RuntimeError ✓), FL5 (sole consumer
is_async_callable :232 ✓), FL7–FL10 (2/3/1/1 calls re-derived
EXACT ✓) STAND; FL6 REVISE evidence (unified `__call__` read;
asyncgen-False + partial-aware postures hold). 8 R STAND (R7:
2 code spellings, trigger unfired; R6 four peels four stop
rules). Zero defects persists.

## Findings — compositions (FC)

Every composition below was re-derived at WT bytes (import +
call censuses quoted). All hold; zero landings (single ownership
everywhere except the three FAMs).

- FC-LEAF: the 7-name `utils/__init__.py` manifest (identity oracle
  tests/utils/test_init.py:35-40 green); root re-exports nothing
  (0 hits); family `_camel_case` aliases compose by binding
  (orders/inputs.py:60, filters/inputs.py:84 — production-reader-less,
  test-pinned: tests/orders/test_inputs.py:861-863,
  tests/filters/test_inputs.py:1274, identity
  tests/utils/test_inputs.py:199-200); the `graphql_camel_name`
  as-re-export in utils/inputs.py:53 is an UNREAD compat path
  (retained for external import stability — observation, no row).
- FC-CANONICAL: `base_container_values` owner + 7 call sites
  (input_values.py:110/:340 f45, inputs.py:522/:587,
  write_transaction.py:1052/:1066/:1073); `canonical_sort_key`
  1 call (:1053) + 2 key-references (inputs.py:522, :1073).
- FC-SUPPLIED: `is_supplied` owner + 18 non-def lines in 3 files
  (f55's list_field ×3 :452-454 compose); `is_inactive_value`
  owner + 19 calls / 6 files; connections.py:179 composes the
  input-values rule (unset-bindings layering holds); CC7's
  filters/sets.py:2895 mixed form is a consistent consumer (the
  explicit `is None` is redundant but composing — no finding).
- FC-CONVERTERS: `convert_with_mro` 4 calls (serializer/forms/
  filters pair); `MRO_CONTINUE` 2 consumers; SCALAR/
  FieldConversionBase imported from `.inputs`.
- FC-MODE: `OperationLease` 4 consumer modules (5 constructions);
  mode readers compose; `bind_operation_mode` 11 referencing files.
- FC-SCOPE: `scope_key` exactly 3 declarations; `session_store_class`
  exactly 2 production callers (capability + instantiate).
- FC-DIRECTIVES: `validated_field_directives` 1 def + 6 calls.
- FC-REQUIRE: `require_optional_module` 4 wrappers + keyset ×2
  direct; `CHANNELS_FLOOR` 4 interpolations + `STRAWBERRY_FLOOR` 1.
- FC-CODED: `coded_error_extensions` owner + 10 composers (f47's
  schema.py:710 + list_field.py:326 compose; single construction
  site pinned by the errors gate — green).
- FC-ENVELOPE: 8 leaf/mapper defs, each single-owned with
  cross-flavor mention lines (33/4/5/8/3/4/6/2 — the 33 includes
  prose/import lines); error-key-map feature (build :283 + names
  :330) single-owned with 5 + 2 callers.
- FC-BOUNDARY: `run_in_one_sync_boundary` 14 awaits / 7 files
  (census revised per FF-5); owner intact :544.
- FC-QPRIVATE: 10-slot exclusivity re-proved; f61 composer
  plans.py:615 (+ gate) + walker.py:1544; f65 3-file TYPE_CHECKING
  imports; seal composes 4 setters :3974-81; nested_fetch composes
  `chain_queryset` :208.
- FC-DEPTH: f51 binder filters/sets.py:3483 + 5 compositions
  (:3553/:3633/:4619/:4907/:4978).
- FC-POLICY: `canonical_policy` 3 external + 3 in-ladder;
  `copy_policy` 6 calls / 3 files (FF-14); `resolve_policy` 2.
- FC-TRIO: `relation_target_type` 3 consumers by name
  (orders/sets.py:823, permissions.py:701, + import :59);
  `relation_path_visibility_types` filters/sets.py:3991 (+ import
  :101); chained hop-resolution intact.
- FC-STRINGS: camel 12/5, flatten 4 (FF-6), or_raise 2, `_plain_text`
  gate 4+1 — all exact.
- FC-PEELS: typing consumers 1/2/4/3/2/3/1/1 (incl. 2 alias imports).
- FC-WRITE: handler-map riders (form + serializer factory, model
  primitives); decode loop over `iter_provided_input_fields`;
  spine (form multi per-element) vs batched (model vs serializer)
  separation holds.
- FC-PERMISSION: `iter_input_items` re-export intact
  (permissions.py:55/:107); walkers compose `iter_active_fields`
  + `related_declaration_mapping` + `assert_set_traversal_depth`.
- FC-RELATIONS: taxonomy trio + classifier + caches + accessor
  3-tier — compositions hold (hunt-narrowed bodies, same graph).
- FC-CONNECTIONS: window rules + sidecar + supplied binding — all
  compositions hold (clean file).
- FC-LAZY: `unwrap_lazy_object` single def (untracked hunt module)
  + 7 consumers (auth/sessions, relay, types/relay ×2, permissions,
  policies ×2) — consumers, not duplication.
- FC-TRUTH: 272 `truth.*` mentions (271 code + 1 docstring prose
  in _queryset_private.py) / 17 functions / 16 files (`kind` 85,
  `is_instance` 46, `name` 37, …), single external owner, 0
  in-folder definitions — the folder composes; semantics blocked
  on the untracked module (FR-8).

## Findings — rejections (FR)

Fresh folder-level verdicts (member-row converges live in the
per-file sections above; standing triggers re-checked unfired
unless noted).

- FR-1 `_plain_text` triple — CONVERGE (no merge).
  imports.py:57 (pass-through generic `_T → _T | str`, stdlib-only
  file) vs strings.py:54 (fail-closed `ConfigurationError`) vs
  input_values.py:79 (`_field_name`, fail-closed per-subject
  grammar). Contracts differ on the non-str posture (pass-through
  vs two fail-closed grammars) and the layering gap WIDENED at WT
  (strings now depends on package `truth`; imports still
  stdlib-only). Triggers (own-boundary non-str rejection need;
  generalized message / third normalizer; posture change) all
  unfired — verified bodies + censuses.
- FR-2 per-module TypeVar declarations — REJECT (no shared TypeVar
  module). `PayloadT` ×2 (operation_lease.py:49 covariant vs
  private_state.py:72 invariant — different variance, different
  generic roles), `PolicyT`, `StateT`/`MemberT`, `_T`×N,
  `_ModelT`/`_QuerySetT` pairs: each generic owner declares its
  own; no cross-module TypeVar is ever imported. Trigger: a
  TypeVar imported across modules.
- FR-3 `_is_exact_sequence` vs `_is_exact_tuple_or_list` — REJECT
  (pack A proposal adopted after body re-read). Same membership,
  different ORDER, with the load-bearing documented reason
  (querysets.py:1141-1146: `in` compares by equality, so order
  decides which class a metaclass `__eq__` is asked about first;
  "each site keeps its own"). Merging forces one order on all
  sites. Trigger: order stops mattering (equality-proof
  membership) → merge.
- FR-4 snapshot-vs-fingerprint container sets — CONVERGE (standing
  in-file separation). `_MUTABLE_SNAPSHOT_TYPES` (6 members incl.
  `bytearray`) vs `_FINGERPRINT_CONTAINER_TYPES` (5 members):
  different memberships AND different orders for different
  questions (snapshot-vs-fingerprint). Trigger unfired (no third
  set).
- FR-5 Col-cursor start vs order-path anchoring (pack C CND-1) —
  REJECT. relations.py:426-444 derives "the column Django compiles
  from" (compilation cursor for filter lookups);
  connection.py:878 derives "the field this order path names" with
  orderability guards (nullable/reverse/multi refusal). Different
  contracts, different answers (column vs field); the adopted
  orphan `orm-lookup-path-resolution` explicitly homes the four
  walkers separate. Trigger: a caller needing field+column jointly
  from one walk.
- FR-6 connection zero-arm vs list zero normalization (pack C
  CND-2) — REJECT. connections.py:208 (`last == 0` without int
  `first` → the `first: 0` page — the Strawberry `edges[-0:]`
  slice quirk) vs list_field.py:452-474 (`is_supplied(0)` is True;
  0 is a valid offset under integer/non-negative validation).
  Slice-quirk vs offset-validation across disjoint vocabularies
  (first/last vs offset/limit). Trigger: a shared zero-page rule
  across vocabularies.
- FR-7 seal snapshot string-keys vs module attribute-access —
  CONVERGE (pack A note adopted). The seal MUST use string keys
  (it snapshots sealed/unknown objects); `_queryset_private`
  owns typed attribute access. Distinct rules (seal discipline vs
  typed access), correctly not merged — this scopes FAM-2/FAM-3
  to attribute spellings only.
- FR-8 `truth.*` vocabulary — CONVERGE (folder composes an external
  owner). 271 code compositions (+1 prose mention), 0 in-folder
  definitions; semantic
  verdicts on gate behavior (J2 subclass-inclusive claims,
  totality, exception-safety where guards were removed) are
  BLOCKED on the untracked `truth.py` landing. Per-file blocking
  refs recorded in packs A/B/C and the D/E re-derivations (e.g.
  canonical.py:73-81 J2 claim; querysets.py:3781 unreadable-state
  successor; permissions.py `_is_request` posture).
- FR-9 FAM-1 exclusions — types/base.py:533 (`any(truth.is_instance
  (arg, NodeIDPrivate) for arg in args)`) is a DIFFERENT rule (one
  class over many values — the "which value" question) vs FAM-1's
  many-classes-over-one-value (the "which class" question).
  Excluded with trigger: an n-ary class-membership need at that
  site → join FAM-1's landing.
- FR-10 alias bindings are declarations — CONVERGE (no row). The
  `_camel_case` ×2 bindings and the unread `graphql_camel_name`
  re-export compose the one strings.py owner by binding; no rule
  is defined twice. Test-pinned (FC-LEAF); deleting relieves no
  change obligation.

Converging standing rejections spot re-verified with fresh
triggers/censuses (all unfired): R7 edge-split (exactly 4 lines
package-wide); token-encoder-vs-pascal-case (owner-recorded both
sides intact); strings digit-twin (encodings still differ);
peels-vs-each-other (four peels, four stop rules); schema-literal
pair (2 code spellings); alias-arm (byte-stable); collision-quartet;
graph-walks (DFS-vs-BFS + visit contracts); record-shape;
sequence-gate; name-vs-orphan-wording; provided-vs-set-walk;
shared-guard-directions (J1/J2); per-subject-wordings (policies R3
intact); opaque-vs-sort-key; model-guard-applicability
(routed-to-the maintainer — stands); all D/E file rejections in the per-file
sections.

## Findings — families (FAM-N)

- FAM-1 real-class membership test — CONFIRMED count-5,
  BLOCKED-ON-HUNT (Family-hold for Worker-0, unticked+blocked).
  One rule ("value's real class subclasses one of a type tuple",
  no `__class__` read — `any(truth.is_instance(v, cls) for cls
  in classes)`): utils/inputs.py:529 + utils/write_transaction.py:848
  + rest_framework/resolvers.py:755 (byte-identical defs; the
  rest_framework docstring drifts by two words — "is (a subclass
  of)" vs "subclasses" — two wordings, one rule) +
  utils/errors.py:197 `_is_text_atom` (same rule, fixed
  `_TEXT_ATOM_TYPES` table) + utils/directives.py:68 (same rule,
  inline). 10 use sites (3+2+3+1+1). Change challenge: "membership
  must consult X beyond real-class" → all 5 move. Package-wide
  `any(truth.is_instance` census is COMPLETE at 6 hits (5 family +
  FR-9 exclusion). Owner candidates: (1) open f46's eventual
  canonical-membership predicate — PRIMARY, expected fusion at
  landing (same membership question; pack B's T1 trigger agrees);
  (2) a `truth.py` n-ary helper — secondary (module untracked).
  Blocked-on-hunt: every rule spelling is WT-added hunt dirt —
  inputs hunk `@@ -515,19` (+ callers in `@@ -565,14`/`@@ -806,37`),
  write_transaction fingerprint/snapshot hunks, rest_framework
  `+def` + callers (file `M`, zero ledger rows), errors `_str_list`
  rewrite hunk, directives `@@ -50,7` (`+` line) — plus untracked
  `truth.py` semantics. Tables are mixed-era (committed:
  `_TEXT_ATOM_TYPES`, `_CHAR_WISE_TYPES`, `_MUTABLE_SNAPSHOT_TYPES`,
  `_FROZEN_VIEW_CONTAINERS`, `_IMMUTABLE_LEAF_TYPES`; WT-added:
  `_UNORDERED_TYPES`; literal `(set, frozenset)` at
  rest_framework/resolvers.py:831) — the landing keeps tables and
  composes gates; it cannot proceed until the hunt lands.
- FAM-2 `_result_cache` slot spelling — CONFIRMED count-2,
  ROUTE TO WORKER-0 as an open family row (NOT folder-landed:
  cross-folder; landing touches verified optimizer files).
  Attribute spellings of Django's slot outside `_queryset_private`:
  utils/querysets.py:3991 (seal write) + optimizer/extension.py:1203
  (read) — both COMMITTED lines (0 hunt-diff hits). Excluded with
  reason: f-string wording (:3918), snapshot string-keys
  (:3909/:4095 — FR-7), nested_fetch's `self._result_cache`
  (own attribute, different rule). Owner: `_queryset_private`
  (new getter+setter pair); the module's own charter ("spelled
  here once … every caller goes through these functions") makes
  this a charter gap, same shape as consolidated f61/f65.
  Challenge: "Django renames `_result_cache`" → 2 defs move.
  Unblocked-by-hunt; blocked-by-scope (family item spans folders).
- FAM-3 `_iterable_class` slot spelling — CONFIRMED count-2,
  same routing as FAM-2. Sites: utils/querysets.py:3973 (seal
  write) + optimizer/nested_fetch.py:151 (read) — both COMMITTED
  (0 hunt-diff hits). Excluded: f-string wording (:3894),
  snapshot key (:3787 — FR-7). Owner: `_queryset_private` (new
  pair). Shared landing note with FAM-2 (one module extension,
  two slot-rules — raised separately for precision).

## Defects

Riding (persist as rowed, route to closeout — zero edits, several
sit in hunt-adjacent hunks): `__init__` D1 (REVISED: (a) persists,
(b) narrowed 12→1 unnamed, (c) persists 5→7); inputs D1 limb (c)
(WT:575); relations D1 (:150 byte-identical) + D2 (4th consumer
re-confirmed); errors D2 (:267 verbatim); permissions D1 (3/3
sites — = input_values O3, recorded once); directives D1 (:3-5 vs
:2444); querysets D1 (fixed, holding re-verified) + D2–D5 + O1
(strengthened). Closed: permissions D2 (hunt reword removed the
false half — `-` lines in the HEAD→WT diff; surviving claim
verified true); errors D1 (auth imports the leaf directly at both
sites; `resolvers.field_error` 0 hits; fixer era undetermined —
closeout attributes via `git log -S 'resolvers.field_error' --
auth/mutations.py`); input_values/write_values observations O3/O1
resolved as noted (O3 = D1 persists; write_values O1 docstring
now states the query). Narrowed: inputs D1 (limbs a/b/d spent
with `899cb35b`). New: none — full docstring-vs-body re-read on
all 23 files; the `_is_request` docstring, `_UNORDERED_TYPES`
comment, and seal-guard deletions match their bodies; hunt prose
(exception-policy manifesto in directives.py, seal paragraph in
_queryset_private.py) is concurrent-owned, not verdicts.

## Falsifications (record-only for closeout)

- FF-1 f45 site-A spent: committed `899cb35b` deleted
  `_hashable_meta_value` while its arm still read `dict.items(v)`.
  f45 holds consolidated as 3 surviving compositions + 1 spent
  site (gate green, zero residue — 121-file AST census reproduced
  independently).
- FF-2 f46 Spelling-A spent (same commit); live population is
  Spelling B (write_transaction.py:839-845/:1026) + Spelling C
  (canonical.py:73-82) + the WT-added `_UNORDERED_TYPES` gates +
  FAM-1's triple. Family still open+blocked (truth.py untracked).
- FF-3 f32 owner + helpers absent at WT and HEAD (names grep-0) —
  converges with the already-deferred retire-or-revise; no new row.
- FF-4 e8 F1 half-landed by committed evolution: relay.py:325 now
  composes `base_queryset(model_for(resolved_type), using=using)`
  (present at HEAD :306 — exactly the specified migration);
  remainder is the WT-only batched instance relay.py:410 (still
  blocked). Owner consumers 8→14 calls (new: orders ×2, filters +3
  incl. the run-13 filters-FAM-2 `_scoped_seed_rows` body :1546,
  relay +1).
- FF-5 one-sync-boundary consumer census stale: NEW committed
  views.py:1145; schema.py prose-only (:388); auth/queries.py +
  testing/client.py 0 mentions (committed removals);
  types/resolvers.py ×3 migrated (adopted orphan); direct
  `sync_to_async` 7→3. Family open — needs census refresh.
- FF-6 flatten census 3→4 mangle sites: committed `754ed263`
  (2026-10-03) added filters/inputs.py:1150 (`input_attr`); row
  files += filters/inputs.py. Docstring leg (a) covers the site;
  verdict intact.
- FF-7 `depth-cap-split` index row dangles: `_MAX_META_VALUE_DEPTH`
  deleted by `899cb35b` (R-depth-caps SPENT); row needs retirement.
- FF-8 e6 row stale: `is_async_queryset_adapter` deleted by
  `899cb35b` ("delete test-only package code"); F9 spent.
- FF-9 F-LENIENT adoption + relations R7 falsified as WT statements
  (owner body + entire `lenient` axis extinct); superseded by the
  f43 extinction rejection. R21 spent both sides (zero residue).
- FF-10 I-R6 retired/spent at WT (both sides hunt-deleted);
  HEAD still holds the pair — WT-only retirement.
- FF-11 `errors-safe-renderer-composition` + `utils-sessions-safe-
  render-composition` bases extinct (`_safe_text`, `_unprintable`,
  `describe_scope` all absent from exceptions.py at WT);
  separations hold on the truth-render basis — rows need re-homing.
- FF-12 `write-values-storage-read-vs-render-read` remote basis
  extinct (same cause) → REVISE.
- FF-13 dispatch "MIXED ledger+hunt" on errors.py not borne out:
  7/7 hunks are hunt by content; no ledger hunk exists.
- FF-14 f13 consumer census stale: error_policy + conf no longer
  call `copy_policy` (0 hits); live population is 6 calls / 3
  files (extensions/resource_policy, resource_policy, schema).
  Consolidation holds; census refresh only.
- FF-15 seal-wording oracle narrowed by committed evolution:
  cause-text literal pins 0 at HEAD+WT (was 6–7); rule holds,
  oracle half needs re-pinning (family open).
- FF-16 canonical R3 exclusions 3→1 (two migrated to `truth.render`
  / `key=truth.render` by the hunt); trigger unfired.
- FF-17 canonical member artifact's WT stamp `ce7f40f4` does not
  resolve in the object store (all other cited stamps resolve).

## Family-holds + transcription (for Worker-0)

New unticked+blocked row: FH-1 FAM-1 real-class membership
(count-5: inputs.py:529, write_transaction.py:848,
rest_framework/resolvers.py:755, errors.py:197, directives.py:68;
owner candidates f46-predicate (primary, fusion expected) /
truth.py n-ary (secondary); blocked-on-hunt per-site as listed
at FAM-1 + untracked truth.py).

New open family rows (unblocked, cross-folder — family items, not
folder-landed): FAM-2 `_result_cache` (querysets.py:3991 +
extension.py:1203; owner `_queryset_private`); FAM-3
`_iterable_class` (querysets.py:3973 + nested_fetch.py:151;
owner `_queryset_private`).

Existing holds persist with census refreshes: f46 (FF-2), f64
(halves intact), f36 (owner + restatement intact, hunt-dirtied),
f63 (zero edits, host function hunt-rewritten), e8 F1 (narrowed
per FF-4, still pending execution). No new hold for f32 (FF-3
converges with the deferred retire-or-revise).

Transcription: this artifact proposes NO new file-local index
rows except two — (1) the committed error-key-map feature
(`build_error_key_map` + `model_field_error_names`, single-owned,
5 + 2 callers) as NEW file-local (post-run-7 drift, folder-homed);
(2) the `_queryset_private` remainder homes (module family +
O-NEW-1 KEEP + FR-7 separation). All other verdicts converge on
standing rows; FF-1–FF-17 are closeout refreshes to existing rows
as noted. CC-N: none. Copy edits: NONE — zero-edit submission
(slot-2 untouched; no diff).

## Verification

Witnesses (all in slot-2 via `workspace.py run`, serialized,
GREEN pressure, no competing suite): tests/utils/test_canonical.py
14 passed (`dry-20261010T062517-49dce2`); tests/utils 1176 passed
(`dry-20261010T063408-267d1b`); tests/test_list_field.py 107 passed
(`dry-20261010T063452-cca032`). f45's 7-hit gate, f53's store
census + tests, f47's single-site gate, f55's supplied rows, and
f12/f13's policy pins are all inside the witnessed files. Copy
reported fresh on all runs; shared-tree move is the plan file only.

Static gates: NOT RUN — the shell tool failed for the entire
closing window (`CallerInvalid: nested spawn session/run is not
durably attested`), blocking `heavy`, `uv`, and every gate
command. Worker-0: run before dispatching Worker-2 —
`heavy uv run basedpyright -p pyproject.toml` (both configured
passes), `heavy uv run python scripts/check_truthful_reads.py
--check`, and (no public symbol touched — zero `.py` edits, so
expected-skipped) `check_public_types.py`. Ruff: nothing to
fix/format (zero `.py` edits; this artifact is `.md`-only and
follows the verified folder-types shape including the link
scaffold below).

Cells: sharded/pg inapplicable by construction — no database,
alias, or dialect surface is touched (zero-edit submission; the
only `.using(` in the folder's orbit is pre-existing pipeline
plumbing outside this item's files).

## Observations (verdict-neutral, no action)

- O-NEW-1 six test-only `_queryset_private` members → KEEP with
  the charter reason (recorded under the remainder trace).
- O-NEW-5 (pack A): the seal's unreadable-state typed-defect arm
  was deleted by the hunt (querysets.py:3779-81); what replaces it
  is blocked on `truth.instance_state` semantics (untracked).
- O-NEW-3 (pack A) = FF-15; O-NEW-4 (pack A) = FF-8.
- The `display_name` parameter orphaned in `canonical_policy` and
  the `RelatedDeclarationError.kind` single-value parameter are
  hunt-owned shape notes, not DRY findings.
- Pack B CC1/CC2/CC5/CC6/CC8 are pointers into verified rows of
  other items (graph-walks third leg, f36 rest leg, Range leg,
  collision-quartet legs, orders D2) — all converge, no folder
  action. CC4 was already queued at File `list_field.py`.

## Independent verification (Worker-2)

Verdict: verified. Zero-edit stands; all three family routings
stand with corrected enumeration (CC-1..CC-3); both proposed
file-local rows confirmed with transcribable text (CC-4/CC-5);
no fourth family; no new defect; no D-N.

Sequencing disclosure: the dispatch brief ordered the
submission artifact read before any other work and itself
summarized W1's claims, so blind expectation-first tracing was
impossible — deviation from `worker-2.md` step 1 recorded here.
Mitigation: every load-bearing pin, count, and census below was
re-derived with Worker-2's own commands at current bytes before
reconciling against W1's numbers, and the rule-level n-ary
sweep that found the sixth FAM-1 site ran beyond W1's
spelling-scoped census. Where my first grep disagreed with W1
(FL5 13-vs-12, O-NEW-1 5-vs-6), the cause was my instrument
(prose line, substring match), corrected by the precise census
quoted — W1's numbers held in both cases.

Copy: slot-3 `dry/folder-utils/verify-1`
(`~/dry/ws/c3af387fc1324a21/dry/slots/slot-3`),
synced 2026-10-10T07:31:03Z, reported fresh with shared tree
unmoved on every run. Byte-identity proven first-hand: per-file
`git hash-object` over all 23 targets identical across WT,
slot-2, and slot-3 — no drift under W1's pins.

### Own re-derivation

- Zero-edit: `git diff a630d234 --stat --
  django_strawberry_framework/ tests/ examples/` EMPTY. No new
  tracked files; exactly two untracked folder files
  (`utils/truth.py`, `utils/lazy.py` — concurrent hunt work, out
  of scope). 23 tracked `utils/*.py` confirmed.
- Hunk census: 212 `@@` hunks folder-wide; all 21 per-file
  counts re-derived EXACT (1/4/0/2/4/3/7/0/0/11/20/0/14/7/8/
  75/20/7/2/2/17/8). Ledger skim: exactly 4 rows naming folder
  paths (relations adopted-orphan, inputs f45, input_values
  f45, private_state f53); none names `errors.py` (FF-13) or
  `rest_framework/resolvers.py`.
- FAM-1 (rule-level sweep, own instrument): `any(truth.
  is_instance` complete at 6 hits — 5 family (inputs.py:531,
  write_transaction.py:850, rest_framework/resolvers.py:757,
  errors.py:199, directives.py:68; defs at :529/:848/:755/:197)
  + FR-9 exclusion (types/base.py:533). All 5 defs absent at
  HEAD (0 hits per file); every gate spelling a `+` line in
  the HEAD→WT diff; use sites 3+2+3+1+1 = 10 re-counted.
  Extended sweep over `any(is_subclass`, `any(truth.
  is_subclass`, tuple-second-arg, and `not any(` forms found
  ONE further rule member (CC-1) and three further
  wrong-direction exclusions (CC-1); `any(issubclass` 0 hits,
  native `isinstance(x, _TYPES)` 0 hits.
- FAM-2/FAM-3: sites confirmed at querysets.py:3991 +
  extension.py:1203 and querysets.py:3973 +
  nested_fetch.py:151. Site lines committed (0 `+`/`-` hits on
  those lines; extension.py's hunks never touch :1203,
  nested_fetch's :151 is diff context). Exclusions confirmed:
  `self._result_cache` own-attribute (:222/:225), f-string
  wordings (:3918/:3894), snapshot string-keys (:3909/:4095,
  :3787 — FR-7). Read halves use defensive
  getattr-with-default (CC-2/CC-3 note).
- Compositions spot re-derived EXACT: FC-CANONICAL 7 calls at
  the cited pins; FL5 12 calls / 5 files as 1+4+3+2+2 (13th
  grep hit is the forms/inputs.py:518 docstring line —
  correctly excluded by W1); `is_inactive_value` 19 calls / 6
  files; FC-TRUTH 272 occurrences / 16 tracked files / 0
  in-folder defs (my 275 raw count included untracked
  lazy.py's 3); FC-QPRIVATE seal composes 4 setters
  (:3974/:3976/:3980/:3981); f61 composers plans.py:615 +
  walker.py:1544; 8 module-level `async def` (7 + 1);
  zero `except BaseException` folder-wide (grep).
- `_queryset_private` remainder: 19 top-level AST nodes;
  exclusivity re-proved with an AST-precise sweep (ZERO
  executable attribute spellings of the 10 covered slots
  outside the module — stronger than grep); O-NEW-1 count-6
  EXACT (test-only: `queryset_fields`, `set_queryset_db`,
  `set_queryset_hints`, `set_queryset_deferred_filter`,
  `set_queryset_defer_next_filter`, `set_queryset_query`;
  family 8 defs + `PrefetchLookup` = 9; shells
  `DeferredFilter` + `_QuerySetT` = 2; 9+2+6 = 17).
- Defects: permissions D2 closure confirmed (false
  `__getitem__` half is a `-` line); errors D1 closure
  confirmed (direct leaf imports auth/mutations.py:547/:1210,
  `resolvers.field_error` 0 hits); inputs D1 limb (c) still
  riding (`repr`-sorted prose vs `canonical_sort_key` body).
  No new defect found in the regions re-read and the sweeps;
  the full 23-file prose re-read is trusted from W1 (a miss
  there lands as a minor riding defect at closeout, never a
  verdict-changer — defects don't block the item).
- Falsifications exactly confirmed: FF-1 (name grep-0), FF-3
  (`make_dynamic_set_getter` 0 at WT and HEAD), FF-4
  (relay.py:325 exact migration + 14 `base_queryset(`
  consumers), FF-5 (views.py:1145 exact), FF-6
  (filters/inputs.py:1150 exact), FF-7/FF-8 (names grep-0),
  FF-11/FF-12 (0 hits in exceptions.py), FF-13 (ledger),
  FF-14 (`copy_policy` 6 calls / 3 files as 1+3+2).
  FF-2/FF-9/FF-10/FF-15/FF-16 accepted as record-only with
  direction consistent (Spelling-B ride, lenient-axis
  deletion, oracle narrowing). FF-17 WITHDRAWN confirmed:
  stamp `ce7f40f4` RESOLVES (`ce7f40f43e…`, 4613 bytes), so
  the non-resolution sentence is not borne out — no closeout
  action; the `_scoped_seed_rows` folding into FF-4 is
  already in the artifact text.
- FR spotchecks: FR-2 variance verdict holds (covariant vs
  invariant) with pin fixes below; FR-4 sets exact (6 incl.
  `bytearray` :830-837 vs 5 :839-845, orders differ); FR-7
  applied in the FAM exclusions above; FR-8 counts confirmed.

### Corrections (transcribable)

- CC-1 FAM-1 count-5 → count-6. SIXTH SITE:
  `sets_mixins.py:620-627` (`is_re_readable_field_declaration`,
  inline `not any(truth.is_subclass(value_type, atom) for atom
  in _TEXT_ATOM_TYPES)` over the local 4-member table;
  `value_type = truth.class_of(value)`; gate line is hunt `+`
  dirt replacing committed `isinstance`). Same rule (real
  class over a type tuple — Textual difference ≠
  independence; table and polarity stay per-site by W1's own
  landing note), moves under W1's change challenge. Use sites
  10 → 11. Spelling census stays complete at 6 hits; RULE
  census is 6. FR-9 exclusion population extends to 4 (same
  one-class-over-many-values direction + trigger):
  types/base.py:533 (named), types/base.py:590 (is_subclass
  over interfaces), rest_framework/resolvers.py:598
  (committed isinstance-tuple over errors),
  types/converters.py:856 (is_instance over pairs). ROW TEXT —
  owner: Family `real-class-membership-test`, owner
  candidates f46 canonical-membership predicate (primary,
  fusion expected) / `truth.py` n-ary helper (secondary);
  files: `utils/inputs.py:529`,
  `utils/write_transaction.py:848`,
  `rest_framework/resolvers.py:755`, `utils/errors.py:197`,
  `utils/directives.py:68`, `sets_mixins.py:626`; outcome:
  unticked+blocked (blocked-on-hunt: all 6 gate spellings
  WT-added dirt + untracked `truth.py` semantics; landing
  keeps per-site tables).
- CC-2 FAM-2 ROW TEXT — owner:
  `utils/_queryset_private.py` (new getter+setter pair; the
  read half needs default-preserving semantics — the family
  item adjudicates defensive-probe vs typed-access: a getter
  with default preserves extension.py:1203 exactly, or the
  family narrows to the seal-write half); files:
  `utils/querysets.py:3991` (seal write) +
  `optimizer/extension.py:1203` (defensive getattr read on
  possibly-non-queryset input — see its comment); outcome:
  open family (committed lines, unblocked-by-hunt,
  cross-folder → family item, not folder-landed).
- CC-3 FAM-3 ROW TEXT — owner: same module (new pair; same
  getattr adjudication at the read half); files:
  `utils/querysets.py:3973` + `optimizer/nested_fetch.py:151`;
  outcome: open family, shared landing note with FAM-2 (one
  module extension, two slot-rules).
- CC-4 file-local error-key-map ROW TEXT — owner:
  `utils/errors.py::build_error_key_map` + `::model_field_
  error_names` (+ `ErrorKeyMap` record); files:
  `utils/errors.py:283` + `:330` (manifest `:68`/`:74`);
  callers build 5 (`rest_framework/resolvers.py:2435/:2501/
  :2556`, `mutations/resolvers.py:1322`,
  `forms/resolvers.py:475`) + names 2 (`rest_framework/
  resolvers.py:2552`, `mutations/resolvers.py:1324`);
  outcome: file-local (committed post-run-7 feature,
  single-owned; in-file recursion `:317` is the owner
  calling itself).
- CC-5 file-local `_queryset_private` remainder ROW TEXT —
  owner: `utils/_queryset_private.py` module family; files:
  the module (10-slot exclusivity incl. f61/f65 owners;
  O-NEW-1 KEEP on the 6 test-only members named above —
  tests are callers under the exclusivity charter; FR-7
  seal-string-key separation); outcome: file-local.
- Pin fixes (verdicts stand): FR-2 `PayloadT` pins are
  operation_lease.py:43 (not :49) and private_state.py:88
  (not :72); variance claims hold. No other pin drift found.

### Judgments

- Method disclosure: ACCEPTED. First-hand tracing of the D/E
  groups satisfies verification depth — every D/E-group
  census re-derived here matched exactly, including two
  where W1's discipline exceeded my first instrument. The
  CC-1 miss sits outside the folder (cross-folder family
  sweep scope), not in D/E depth, and is remediated by
  transcription; the family item re-sweeps the mechanism
  package-wide regardless.
- Static gates: W0's shared-tree runs SUFFICE (basedpyright
  0/0/0 both passes, truthful-reads 120 files tier-1 0,
  public-types skipped per expectation — zero `.py` edits).
  They ran post-submission at HEAD `23b5f421`, still current;
  for a zero-edit submission they are tree-health
  confirmation, and slot-3's byte-identity proof extends
  them to the verified bytes. Ruff vacuous (no `.py`
  touched); artifact prose rules checked first-hand (run-id
  citations are DRY-mandated record, not provenance).
- Cells: sharded/pg inapplicable by construction — AGREED
  (zero-edit; no database, alias, or dialect surface
  touched; the one `.using(` nearby is pre-existing plumbing
  outside the item).
- No fourth family: CONFIRMED. Duplicate-def sweep over the
  folder yields only the FAM-1 triple plus an overload
  false alarm (`_prepared_visibility_source` ×3, one file);
  the n-ary sweep's only new member joins FAM-1; `_safe_*`
  residue is two single-owned helpers, not twins.
- Defects: riding/closed/narrowed lists endorsed as
  re-derived above; zero new; no `(Worker-2)` entries owed.

### Gates run (slot-3, serialized via heavy, GREEN)

- `pytest tests/utils/test_canonical.py -n0 --no-cov -q` →
  14 passed (`dry-20261010T073443-ad2433`). (An earlier
  invocation without the `pytest` word exited 0 without
  executing tests — discarded, re-run correctly.)
- `pytest tests/utils -n0 --no-cov -q` → 1176 passed
  (`dry-20261010T073450-92dd42`).
- `pytest tests/test_list_field.py -n0 --no-cov -q` → 107
  passed (`dry-20261010T073527-716f94`).
- Copy fresh + shared unmoved on all runs; package digest
  `sha256:e91e8021…` inside the copy.

Re-derived vs trusted: everything under "Own re-derivation"
and the CC pins is Worker-2's own bytes-derived work; trusted
from W1 are the member-verdict vocabulary rows whose pins were
not individually rechecked, the per-file drift homings, the
unlisted FC censuses, and the full 23-file prose re-read
breadth — all direction-consistent with the green witnesses
and immaterial to the verdicts above.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[plan]: dry-0_0_15.md
[file-init]: dry-file-utils____init__.md
[file-canonical]: dry-file-utils__canonical.md
[file-connections]: dry-file-utils__connections.md
[file-context]: dry-file-utils__context.md
[file-converters]: dry-file-utils__converters.md
[file-directives]: dry-file-utils__directives.md
[file-errors]: dry-file-utils__errors.md
[file-execution-mode]: dry-file-utils__execution_mode.md
[file-imports]: dry-file-utils__imports.md
[file-input-values]: dry-file-utils__input_values.md
[file-inputs]: dry-file-utils__inputs.md
[file-operation-lease]: dry-file-utils__operation_lease.md
[file-permissions]: dry-file-utils__permissions.md
[file-policies]: dry-file-utils__policies.md
[file-private-state]: dry-file-utils__private_state.md
[file-querysets]: dry-file-utils__querysets.md
[file-relations]: dry-file-utils__relations.md
[file-sessions]: dry-file-utils__sessions.md
[file-strings]: dry-file-utils__strings.md
[file-typing]: dry-file-utils__typing.md
[file-write-transaction]: dry-file-utils__write_transaction.md
[file-write-values]: dry-file-utils__write_values.md
[self]: dry-folder-utils.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
