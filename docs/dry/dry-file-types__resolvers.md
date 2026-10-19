# DRY review: `types/resolvers.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target [types-resolvers][types-resolvers] at HEAD blob
`72d62dc4ebfe` (882 lines). Worktree `640905c63f46`
(906 lines, 15 `@@` regions, 45+/21-) mixes OWNED
hunks with concurrent-external dirt, and the dispatch
brief's "no owned ledger hunk names this file" is a
dispatch mislabel — content governs, no stop (file
item, zero edits): the `## Owned changes` ledger DOES
name this file (adopted orphan `one-sync-boundary`,
run 2) and the run-7 ledger re-prove confirms those
hunks INTACT. Attribution by diff content against
`git show HEAD:<path>`:

- Owned (ledger `types/resolvers.py — adopted orphan
  one-sync-boundary`, matched verbatim): the
  `sync_to_async` import drop (hunk 1), the
  `run_in_one_sync_boundary` import add (hunk 3), the
  docstring reword to the shared worker (hunk 11),
  and the `sync_to_async(getattr,
  thread_sensitive=True)` → `run_in_one_sync_boundary(
  getattr, ...)` conversions inside hunks 12/14/15
  (reverse-O2O, forward fast-path, forward planned-path
  arms — the ledger's "3 lazy-fetch arms", re-proved
  at worktree lines 637/713/786).
- Concurrent-external (absent from ledger and cycle
  baseline): the hunt's `truth.*` migration (hunks 2
  partial, 4, 5, 8, 9, 10: `_in_instance_namespace`,
  `truth.is_type`, `# truth: ok`, narrowed
  `except`), the elision-refusal docstring + `except
  BaseException` → `except Exception` narrowing
  (hunks 6, 7), and the maintainer's `check_deadline`
  dirt (hunk 2 partial + one line each inside hunks
  12/13/14/15 — adjacent to but non-overlapping with
  the owned arms, exactly as the run-7 re-prove
  records).

Target traced at HEAD bytes (`git show HEAD:` +
AST over HEAD bytes); dirty connected inputs read
at both bytes (table below); every `:NNN` pointer
HEAD-based (E5 re-pass). Nothing tracked touched;
target diff vs `ITEM_BASELINE=0490d39b45ff85dd6cd7a50325cb04ac96f7c5f6`
is empty (all dirt predates dispatch). Every hunk in
the touched path falls in those two homes: no stop
triggered.

The module is the generated-resolver layer: the
cardinality factory (`_make_relation_resolver` with
its many / reverse-O2O / forward closures), the
Phase-2 attach pair, the file parent-resolver pair,
the B3 N+1 probe (`_check_n1` + strictness/planned
ladders + lazy-load predicates), the FK-id elision
stub + deferral probe, the resolve-time visibility
recheck pair, and the per-relation
optimizer-scoped trust boundary. It owns no
queryset seed, no visibility boundary, no row bound,
no key grammar, no strictness vocabulary: seeds +
visibility + seal belong to [querysets][querysets],
bounds to [resource-policy][resource-policy], keys +
runtime paths to [plans][plans], the `to_attr`
grammar to [nested-planner][nested-planner], the
strictness vocabulary + validation to
[optimizer-extension][optimizer-extension], the
stash/channel mechanics to
[optimizer-context][optimizer-context], FieldMeta to
[field-meta][field-meta], the registry reads to
[registry][registry], the attach schedule + skip sets
to [types-finalizer][types-finalizer], the file map
walk to [types-converters][types-converters]
(`_field_output_type_for`), the executor fact to
[execution-mode][execution-mode].

Sites found (`D` = definition, `C` = consumer, `O` =
oracle, `P` = projection). `_check_n1`: 1 `D`
(:220) + 4 production `C` (in-file many :546,
reverse-O2O :614, forward :747; [connection][connection]
:2240 synthesized relation-connection, `kind=
"connection_to_attr"`) + docstring `P` cites in
[walker][walker] :649/:834, [optimizer-context][optimizer-context]
:397, [optimizer-extension][optimizer-extension] :1232.
`_optimizer_scoped_relation`: 1 `D` (:436) + 8
in-file `C` consults (+ 1 unscoped recheck call). `_visible_related_object`: 1 `D`
(:395) + 6 in-file `C` + 3 awaitable-flatten tails.
`_visible_many_rows`: 1 `D` (:415) + 2 in-file `C`.
`_build_fk_id_stub` / `_fk_attname_is_deferred`: 1
`D` each (:122/:93) + in-file `C` only.
`_will_lazy_load_single/many`: 1 `D` each (:156/:174)
+ `_check_n1` + 3 async-gate `C`. `_strictness_for`
/ `_relation_is_planned`: 1 `D` each (:189/:207) +
`_check_n1` `C`. `_name_resolver`: 1 `D` (:331) + 4
`C` (3 relation branches + file). `_custom_visibility_type`:
1 `D` (:371) + 1 `C` (factory head :541).
`_field_meta_for_resolver`: 1 `D` (:344) + 1 `C`
(:539) + docstring `P` in [walker][walker] :459 and
[field-meta][field-meta] :219/:334.
`_make_relation_resolver`: 1 `D` (:477) + 1 `C`
(in-file attach :822) + docstring `P` in
[types-init][types-init] :7 and
[types-base][types-base] :1767. `_attach_*`: 1 `D`
each (:803/:826/:853) + 1 `C` each
([types-finalizer][types-finalizer] :972/:986) +
docstring `P` in [types-converters][types-converters]
:29/:492/:543. Absence bindings: 2 `D` (reverse
:606–611, forward :660–665) + 6 `except C`.
`sync_to_async(getattr, thread_sensitive=True)`: 3
`D` arms (:619/:692/:763 — the open
`one-sync-boundary` members). `except` code arms:
exactly 10 (:114/:118/:140/:146 + 6
`related_does_not_exist`). `isinstance`: exactly 2
(:315/:384). Code `raise`: exactly 1 (:326).
`resolver.__name__` writes: exactly 1 (:340).
`_dst_` constructs: 0 (docstring `P` :258–259 only).
`sync_to_async` docstring mention: 1 (:520, `P` of
the 3 arms).

Oracles (all independent literals/shapes, never
owner reads): [test-resolvers][test-resolvers] (45
at worktree = 44 HEAD + the owned spy gate:
`__name__` stamps, B2 elision incl. attname/
null/deferral/unsafe-sentinel/router-db, `_check_n1`
warn/raise/silent/planned/many/accessor arms,
absence containment forward+reverse × sync/async ×
fast/planned + hostile-AttributeError propagation
both branches, the owned-orphan shared-boundary spy
gate over all 3 arms, scoped-vs-unscoped visibility
both colors, unsealable-prefetch refusal wording,
edge cases) + live payload/SQL in
[test-products-visibility-api][test-products-visibility-api]
(per the unit docstrings' own pointers).
Projections: module + 17 function docstrings (layer
map, spec-011 D7 / spec-033 D8 / spec-035 D5 /
spec-037 D3+D4 decision cites, B2/B3/B8/G2
milestone cites), [glossary][glossary]
`strictness-mode` / `fk-id-elision` /
`sealed-execution-queryset` entries.

Freshness (blob = `git hash-object` worktree /
`git rev-parse HEAD:`; HEAD `0c0537e2`):

| Input | Worktree | HEAD | Bytes traced |
|---|---|---|---|
| `types/resolvers.py` (target) | `640905c6…` | `72d62dc4…` | HEAD (882 lines) |
| `connection.py` | `1fca6266…` | `4894f90f…` | both (`_check_n1` call + grammar calls unchanged in shape) |
| `optimizer/_context.py` | clean `dbc30630…` | same | HEAD |
| `optimizer/walker.py` | `d5759ef8…` | `75f9c6b6…` | both (predicate + cites) |
| `optimizer/field_meta.py` | `bcddf517…` | `18ea719a…` | both (shape builder) |
| `optimizer/plans.py` | `33140a76…` | `cce98531…` | both (key builders) |
| `optimizer/nested_planner.py` | `d32d1b7b…` | `b4dfd4a6…` | both (grammar owner) |
| `optimizer/extension.py` | `39a8739c…` | `e0e53a8e…` | both (vocabulary + publish) |
| `registry.py` | `492654d2…` | `81bd561c…` | both (reads) |
| `resource_policy.py` | `cc3f9d80…` | `4b69e974…` | both (bound twins) |
| `utils/querysets.py` | `8fc556d5…` | `3616927d…` | both (visibility/recheck/seal/boundary) |
| `utils/relations.py` | `05ff55b0…` | `8dbc3fe6…` | both (accessor/kind) |
| `utils/execution_mode.py` | clean `9805cdaf…` | same | HEAD |
| `types/converters.py` | `f6cadb08…` | `058f1081…` | both (file map walk) |
| `types/finalizer.py` | `b9d8acb2…` | `de34ae2a…` | both (attach schedule) |
| `types/base.py` | `dc67f084…` | `dda91365…` | both (flag compute) |
| `types/definition.py` | `1c59a3fe…` | `fa6c4d33…` | both (flag slot) |
| `types/relay.py` | `4b2a9df5…` | `52439862…` | worktree (recourse census only) |
| `filters/sets.py` | `e47c6758…` | `993e887a…` | worktree (recourse census only) |
| `list_field.py` | `450e87cd…` | `21380eb7…` | worktree (recourse census only; re-fingerprinted at resubmission, ×2 calls re-confirmed) |
| `permissions.py` | `ef66f8b9…` | `72102cc0…` | worktree (recourse census only) |
| `mutations/resolvers.py` | `c9cff059…` | `043a2d0b…` | worktree (flavor-mirror read) |
| `forms/resolvers.py` | `a1000f21…` | `35c282cc…` | worktree (flavor-mirror read) |
| `rest_framework/resolvers.py` | `c49ce3c2…` | `0d302782…` | worktree (flavor-mirror read) |
| `utils/write_values.py` | `72f132f0…` | `d28587c7…` | worktree (consumer census) |
| `tests/types/test_resolvers.py` | `d78d605f…` | `346e945d…` | both (44 HEAD + 1 owned spy-gate oracle at worktree) |

Searched population: every `.py` under
`django_strawberry_framework/` for each target
symbol + `connection_to_attr` + `run_in_one_sync_boundary`
+ `apply_type_visibility_sync` + `has_custom_get_queryset`
+ `isawaitable` + `_ASYNC_RECOURSE` (per-symbol
hit lists in the trace above). `consumer=` /
`resolver=` upstream Django/Strawberry bodies read:
none (no upstream seam reached). No workspace runs
(read-only `git show` / search / AST-over-stdin).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Read the
   three write-flavor resolvers ([mutations-resolvers][mutations-resolvers],
   [forms-resolvers][forms-resolvers],
   [rest-framework-resolvers][rest-framework-resolvers])
   + [write-values][write-values] + root relay
   refetch + [list-field][list-field] /
   [connection][connection] surfaces before judging
   anything unique. Relation OUTPUT resolve (this
   file) vs relation INPUT decode (flavors) share a
   theme, not a rule: opposite directions, opposite
   error contracts (object-or-None vs FieldError
   envelope), opposite color posture (dual-color
   here, one-boundary pipelines there). The one
   genuine touch is the visibility recheck:
   write-side all compose
   `related_visibility_queryset_or_default` by name
   while `_visible_related_object` spells its own —
   assigned C-RECHECK (verified F5 names it the
   second definition; family item owes disproof, my
   deltas are its material). Recourse wording:
   R8. Custom-hook predicates: R7.
2. **Sync/async twins.** Compared by behavior, not
   shape. `_visible_related_object` /
   `_visible_many_rows` (dual-color bodies: sync
   tail vs returned coroutine), 3 resolver twin
   pairs (reverse, forward-fast, forward-slow: sync
   direct-read vs async one-hop read, identical
   gate/except/visibility composition), `bounded_rows`
   twins (owned [resource-policy][resource-policy]).
   Each pair shares every pure decision and differs
   only at the await boundary + hop — the
   principle-5 twin shape, kept as pairs
   (F-MANYVIS, R5). The `inspect.isawaitable`
   flatten triple is the mechanical dual-color
   tail, not a third body (R12, coupled to
   C-RECHECK).
3. **Derived rather than repeated knowledge.**
   Resolver keys (`resolver_key` + `runtime_path_from_info`),
   instance accessor (`instance_accessor`), kind
   (`FieldMeta.relation_kind` /
   `is_many_side_relation_kind`), seeds, bounds —
   all composed by name at every call site; zero
   inline key-building, zero re-derivation. The
   instance-attname reads (`getattr(root, attname)`)
   are column reads off the row, not members of the
   verified six-`pk.attname`-readers population
   (descriptor-column vs pk-descriptor split —
   trigger re-checked unfired). `prefetch_origin`
   is one origin composition (C-SEAL). The two
   absence bindings derive one catch-spec two ways
   (FAM-ABSENCE).
4. **Inverse / round-trip pairs.** `to_attr`
   PRODUCE ([nested-planner][nested-planner] grammar,
   single body + delegates) vs PROBE (here,
   `getattr(root, to_attr, None) is None`) — halves
   with one grammar owner (C-GRAMMAR). Stash
   PUBLISH ([optimizer-extension][optimizer-extension] /
   walker) vs READ (here) — halves, channel
   vocabulary owned by [optimizer-context][optimizer-context].
   Elision-stub BUILD vs normal RESOLVE — fallback
   halves of one dispatch (F-ELIDE). Bound sync/async
   twins — halves owned by [resource-policy][resource-policy].
   No half is re-owned here.
5. **Contracts restated in another medium.**
   Production (17 defs) / oracles (45 package tests
   at worktree = 44 HEAD + the owned spy gate)
   + live suites — all independent: literal
   messages, `__name__` strings, None-identity,
   spy-call tuples; the spy gate pins the owned
   worktree arms, HEAD arms pinned by containment
   parity tests) / prose (module + function
   docstrings, spec-decision cites, glossary
   entries — all projection). The `_check_n1`
   docstring's `_dst_` vocabulary is projection
   of the owned grammar (0 constructs here). No
   test reads an owner table (no `LOOKUP_NAME_MAP`
   class violation); no docstring restates a rule
   as a second definition.
6. **Enforcement by omission.** Enumerated every
   branch × (N+1 check, visibility gate, async
   hop, row bound): many ✓/✓/✓(async-iter)/✓,
   reverse-O2O ✓/✓/✓/n/a(single),
   forward-fast ✓-via-cheap-gate/✓/✓/n/a,
   forward-slow ✓/✓/✓/n/a, elision-stub
   n/a(no access)/✓/n/a/n/a, file n/a/n/a/n/a/n/a
   (R13: relations-scoped per owner prose).
   Cheap-gate equivalence probed: it skips
   `_check_n1` exactly when `not elisions and
   planned is None and live in (None, "off")` —
   wire-safe (the extension co-publishes live +
   stash, so stash-armed-without-live is a
   hand-built-context-only shape, unpinned by any
   oracle), with the residual test-only
   divergence recorded in R13's trigger. Absence
   of a guard is never counted as a definition;
   no contract source extends any skipped guard.

### Enumeration

Instrument: `ast.parse` over HEAD bytes
(`ast.Module.body` = 42 top-level members, #0–#41)
plus full nested expansion (10 nested `def`s: 3
relation closures + 3 `_resolve_async` + 2
`_resolve` + `file_resolver` + `_resolve` (many
async); no classes). 42/42 homed; no member
unassigned. (`F-*` = file-local finding, `C-*` =
open-family convergence, `FAM-*` = new family,
`R-*` = rejection; all defined under
`## Findings`.)

| # | Member (HEAD line) | Home |
|---|---|---|
| 0 | Module docstring, layer map (:1–21) | F-MECH (claims verified: no base import; caller passes fields) |
| 1 | `import inspect` (:23) | F-MECH (R12 flatten ×3) |
| 2 | `Callable` (:24) | F-MECH (F-NAME annotation) |
| 3 | `Any` (:25) | F-MECH (annotations) |
| 4 | `import strawberry` (:27) | F-MECH (attach ×2) |
| 5 | `sync_to_async` (:28) | C-ONEBOUND (3 unconsolidated arms; owned dirt converts) |
| 6 | `router` (:29) | F-MECH (F-ELIDE db pin) |
| 7 | `Info` (:30) | F-MECH (annotations) |
| 8 | `OptimizerError` (:32) | F-MECH (F-N1 raise) |
| 9 | `_resolver_logger` (:40) | F-MECH (F-N1 warn; near-miss: finalizer plain import) |
| 10 | `DST_*` ×3 (:41–45) | F-MECH (F-N1/F-ELIDE/F-STRICT reads) |
| 11 | `_active_strictness` (:46–48) | F-MECH (F-STRICT + cheap gate) |
| 12 | `_optimizer_value` (:49–51) | F-MECH (sentinel reads) |
| 13 | `_relation_is_optimizer_scoped` (:52–54) | F-MECH (F-STRICT/F-SCOPED) |
| 14 | `FieldMeta` (:55) | F-MECH (annotations + F-FMETA fallback) |
| 15 | key builders (:56) | F-MECH (composed by name, zero inline builds) |
| 16 | `registry` (:57) | F-MECH (F-FMETA/F-GATE reads) |
| 17 | bound twins (:58) | F-MECH + C-SEAL (F-MANYVIS + many arms) |
| 18 | `async_execution` (:59) | F-MECH (8 color dispatches) |
| 19 | querysets 5-name (:60–66) | F-MECH + C-SEAL (normalize/materialize) + C-RECHECK (seed/apply) |
| 20 | relations 2-name (:67) | F-MECH (accessor + kind predicate) |
| 21 | `_field_output_type_for` (:68) | F-MECH (F-FILE; C-MRO consumer) |
| 22 | `_EMPTY_ELISIONS` (:72) | F-SENT |
| 23 | `_PLAN_UNREAD` (:78) | F-SENT (+ F-N1 threading) |
| 24 | `_FK_ELISION_UNSAFE` (:90) | F-SENT (+ F-ELIDE flow) |
| 25 | `_fk_attname_is_deferred` (:93) | F-ELIDE (+ R1 arms, O1) |
| 26 | `_build_fk_id_stub` (:122) | F-ELIDE (+ R1 arms, O1) |
| 27 | `_will_lazy_load_single` (:156) | F-PROBE |
| 28 | `_will_lazy_load_many` (:174) | F-PROBE (+ R4 split) |
| 29 | `_strictness_for` (:189) | F-STRICT |
| 30 | `_relation_is_planned` (:207) | F-STRICT |
| 31 | `_check_n1` (:220) | F-N1 (+ C-ORCH/C-GRAMMAR arm, R3/R10/R11) |
| 32 | `_name_resolver` (:331) | F-NAME |
| 33 | `_field_meta_for_resolver` (:344) | F-FMETA (+ F-DOUBLE fallback) |
| 34 | `_custom_visibility_type` (:371) | F-GATE (+ R7 walker pair, R2 gate) |
| 35 | `_visible_related_object` (:395) | C-RECHECK (+ R8 recourse, R5/R12 coupling) |
| 36 | `_visible_many_rows` (:415) | F-MANYVIS (+ C-SEAL cite, R8 recourse) |
| 37 | `_optimizer_scoped_relation` (:436) | F-SCOPED |
| 38 | `_make_relation_resolver` (:477) + 3 closures + 4 nested resolves | F-RESOLVER (+ FAM-ABSENCE, R5/R6, C-ONEBOUND) |
| 39 | `_attach_relation_resolvers` (:803) | F-RESOLVER (+ R9 twin) |
| 40 | `_make_file_resolver` (:826) + closure | F-FILE (+ R13, file-null converge) |
| 41 | `_attach_file_resolvers` (:853) | F-FILE (+ R9 twin, C-MRO) |

### Challenges

Counts are authoritative definitions only;
consumers, oracles, projections listed, never
counted. Every row ends in its home.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Layering needs a base import | **1** (import + docstring map move together) → F-MECH |
| C2 | An import goes dead | **0** (30/30 names consumed — census, not a rule) → F-MECH |
| C3 | Fourth dispatch sentinel | **1** (new token + its readers) → F-SENT |
| C4 | Stub must carry another column | **1** (`_build_fk_id_stub`; deferral follows only if deferrable — listed) → F-ELIDE |
| C5 | Deferral verdict change | **1** (`_fk_attname_is_deferred`) → F-ELIDE |
| C6 | Many-side gains double-compat | **1** (`_will_lazy_load_many` gains the arm; single untouched) → F-PROBE/R4 |
| C7 | Third strictness source | **1** (`_strictness_for` ladder) → F-STRICT |
| C8 | Third planned channel | **1** (`_relation_is_planned`) → F-STRICT |
| C9 | Fifth `_check_n1` kind | **1** (dispatch + probe selection) → F-N1 |
| C10 | N+1 message wording | **1** (raise + warn share `suffix`; oracles pin both — listed) → F-N1/R3 |
| C11 | Threaded-value set change | **1 convention** (accept-sites + pass-site move as API coupling — listed, not counted) → F-N1/F-SCOPED |
| C12 | Stamp-shape change | **1** (`_name_resolver`; oracles pin — listed) → F-NAME |
| C13 | FieldMeta source change | **1** (`_field_meta_for_resolver`) → F-FMETA |
| C14 | No-definition routing posture | **1** here (`_custom_visibility_type`; walker moves independently — R7) → F-GATE |
| C15 | No-primary fallback change | **0 here** (owner moves; this file cannot receive no-primary — C-RECHECK delta) |
| C16 | Recheck alias/pk/twin change | **1** (`_visible_related_object`; owner unaffected — C-RECHECK delta) |
| C17 | Many-pipeline order change | **1** (`_visible_many_rows`) → F-MANYVIS |
| C18 | Scoped-channel change | **1** (`_optimizer_scoped_relation` + rejected-channels rationale) → F-SCOPED |
| C19 | Fourth cardinality branch | **1** (new factory branch; attach loop follows — listed) → F-RESOLVER |
| C20 | Absence-fallback unification | **2** (reverse + forward bindings — FAM-ABSENCE) |
| C21 | Boundary-hop change | **0 here** (3 arms follow the C-ONEBOUND owner; worktree already converted) |
| C22 | File null-shape change | **1** (`_make_file_resolver`; column side unaffected — file-null converge) → F-FILE |
| C23 | Skip-set change | **2 by design** (relation vs file sets, Decision 3 — R9) |
| C24 | Visibility-gate condition | **1 pair** (`_custom_visibility_type` + `_optimizer_scoped_relation`; 8 scoped-consults + 1 unscoped recheck (:590) follow as enforcement sites — R6) |
| C25 | Arm-tail change | **0 new** (tails follow dual-color/bound contracts — R5/R12, coupled to C-RECHECK) |
| C26 | Fourth strictness mode | **0 here** (extension owns; comparisons follow — R11) |
| C27 | `to_attr` grammar change | **0 here** (nested_planner owns; docstring follows — C-GRAMMAR) |
| C28 | Recourse-subject change | **0 here** (default composed by omission; remedy shared — R8) |

## Findings

### F-MECH — module mechanics (file-local)

- **Contract + variation.** The module docstring's
  layer map (relation/file resolvers, cardinality
  rationale, sibling-of-base with the no-base-import
  rule + caller-passes-fields seam) + 21 import
  statements binding 30 names, all consumed (census:
  `inspect` R12 ×3, `Callable` F-NAME, `Any`
  annotations, `strawberry` attach ×2,
  `sync_to_async` C-ONEBOUND ×3, `router` F-ELIDE,
  `Info` annotations, `OptimizerError` F-N1,
  `_resolver_logger` F-N1, `DST_*` ×3 reads,
  `_active_strictness` F-STRICT + cheap gate,
  `_optimizer_value` sentinel reads,
  `_relation_is_optimizer_scoped` F-STRICT/F-SCOPED,
  `FieldMeta` annotations + F-FMETA, key builders
  composed by name, `registry` F-FMETA/F-GATE,
  bound twins F-MANYVIS + many arms,
  `async_execution` 6 code dispatches (+ import +
  docstring = 8 occurrences), querysets 5-name
  C-SEAL/C-RECHECK, relations 2-name, file-map
  reader C-MRO) + the `_resolver_logger` alias
  (explicit cross-subpackage surfacing) + the
  implicit surface (no `__all__`; Phase-2 private
  names reached by dotted path).
- **Sites + roles.** 1 `D` (this module, members
  #0–#21). `C`: [types-finalizer][types-finalizer]
  (attach calls), [connection][connection] (`_check_n1`
  call). `O`: none directly (mechanics covered via
  behavior oracles). `P`: the docstring map itself.
- **Challenges.** C1 (1), C2 (0 — census).
- **Owner + lifetime.** This module (leaf
  mechanics; no stored derivation).
- **Distinct behavior.** The logger alias vs
  [types-finalizer][types-finalizer]'s plain
  `from ..optimizer import logger`: both bind the
  one optimizer logger object — local naming, not
  two rules (near-miss, no row).
- **Behavioral proof.** `static-reviewed` (no
  edit; import census by byte read).
- **Structural gate.** None owed (mechanics; the
  `check_citations` gate covers the dotted
  consumers).
- **Freshness.** Target HEAD `72d62dc4…`; finalizer
  HEAD `de34ae2a…`; connection HEAD `4894f90f…`.

### F-SENT — dispatch sentinels (file-local)

- **Contract + variation.** Three opaque identity
  tokens, each with one job: `_EMPTY_ELISIONS`
  (frozen no-elisions branch, no per-call
  allocation), `_PLAN_UNREAD` (unread-plan vs
  `planned is None` distinction for the threading
  convention), `_FK_ELISION_UNSAFE` (elision
  refused: deferred column at HEAD; the worktree
  extends the refusal to stub-construction
  failure — hunt dirt, not judged).
- **Sites + roles.** 1 `D` per token (members
  #22–#24). `C`: forward dispatch + `_check_n1`
  threading + `_build_fk_id_stub` flow. `O`:
  elision/sentinel tests (unsafe-sentinel return,
  bare-key ignores, stub-scoping).
- **Challenges.** C3 (1).
- **Owner + lifetime.** This module (tokens are
  never re-read across executions; pure identity).
- **Distinct behavior.** Opaque `object()` dispatch
  tokens vs [types-relations][types-relations]' diagnostic
  `PendingRelationAnnotation` error shape:
  CONVERGE with verified
  `types-relations-sentinel-vs-runtime-tokens` on
  fresh evidence (still opaque, still no
  diagnostic shaping — trigger re-checked
  unfired; transcribes nothing).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** None owed (identity tokens;
  oracles pin the flows, not the tokens).
- **Freshness.** Target HEAD `72d62dc4…`; relations
  row (plan index, verified run 7).

### F-ELIDE — elision stub + deferral probe (file-local)

- **Contract + variation.** B2 id-only selections:
  `_build_fk_id_stub` builds a pk-only target
  instance from `root.<attname>` (None when no
  attname/model/id; `_FK_ELISION_UNSAFE` when the
  column is deferred per spec-035 Decision 5, never
  reading it; `state.adding = False` +
  `router.db_for_read(model, instance=...)` pin,
  instance None when the parent lacks `_state`);
  `_fk_attname_is_deferred` confirms deferral only
  via `__dict__` absence PLUS a real
  `get_deferred_fields()` listing (test doubles
  without the method read as loaded).
- **Sites + roles.** 1 `D` per helper (members
  #25–#26). `C`: forward elision dispatch only.
  `O`: stub/router/instance/deferral/unsafe/fallback
  tests (incl. real deferred-`.only()` instance).
  `P`: Decision-5 docstrings here + B2/B8/G2
  cites.
- **Challenges.** C4 (1), C5 (1).
- **Owner + lifetime.** This module (per-row pure
  derivation; "not cached").
- **Distinct behavior.** The HEAD `except
  BaseException` arms (deferral-probe ×2, stub
  ×1) are observed-not-homed (O1): no wire input
  reaches them (Django's method / model `__init__`
  under supported API), and worktree hunt dirt
  already reworks them.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles (deferred
  real-instance fallback + unsafe-sentinel
  identity).
- **Freshness.** Target HEAD `72d62dc4…`; oracle
  file HEAD `346e945d…` / worktree `d78d605f…`.

### F-PROBE — lazy-load predicates (file-local)

- **Contract + variation.** "Would this access
  query": single-valued (`__dict__` OR
  `fields_cache` = loaded, test-double-compat) vs
  many-side (`_prefetched_objects_cache` ONLY —
  the `__dict__` short-circuit deliberately
  withheld so consumer-assigned attributes cannot
  exempt the many-side strictness path).
- **Sites + roles.** 1 `D` per probe (members
  #27–#28). `C`: `_check_n1` dispatch + 3 async
  gates. `O`: loaded/double/prefetched/accessor
  tests both sides.
- **Challenges.** C6 (1 — R4 records the split).
- **Owner + lifetime.** This module (pure per-row
  reads).
- **Distinct behavior.** The single/many split is
  the stated separation (R4); the probes are one
  pair, not two definitions of one probe.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles
  (consumer-set-attribute stays lazy many-side).
- **Freshness.** Target HEAD `72d62dc4…`.

### F-STRICT — strictness + planned ladders (file-local)

- **Contract + variation.** `_strictness_for`:
  live ContextVar → `DST_OPTIMIZER_STRICTNESS`
  stash → `"off"` (the stash is the only channel
  for hand-built contexts). `_relation_is_planned`:
  stash membership OR per-execution scoped set
  (same resolver-key vocabulary; the stash alone
  leaves stash-less executions disarmed).
- **Sites + roles.** 1 `D` per ladder (members
  #29–#30). `C`: `_check_n1` (+ forward cheap
  gate reads live directly). `O`: stash-ladder
  tests (off/warn/raise, planned-hit/miss,
  connection-agnostic).
- **Challenges.** C7 (1), C8 (1).
- **Owner + lifetime.** This module (per-call
  reads; no stored derivation).
- **Distinct behavior.** Unknown strictness values
  are silent — unreachable via the validated
  extension ([optimizer-extension][optimizer-extension]
  `_STRICTNESS_MODES` + constructor refusal); a
  hand-poisoned stash disarms only its own
  diagnostic (R11).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles (literal
  stash maps).
- **Freshness.** Target HEAD `72d62dc4…`; extension
  HEAD `e0e53a8e…`; context clean `dbc30630…`.

### F-N1 — B3 unplanned-access probe (file-local)

- **Contract + variation.** `_check_n1`: strictness
  gates everything (read first — absent plan is
  the reportable case, never silence); threaded
  `planned`/`precomputed_key`/`strictness` reuse
  (forward path walks `info.path` once per row);
  planned short-circuit bypassable via
  `force_unplanned` (Decision-5 unsafe elision);
  kind dispatch (`many`/`reverse_many_to_one` →
  many probe; `"connection_to_attr"` → `to_attr`
  presence probe; else single probe; `kind=None`
  reserved for test-double direct callers);
  `accessor_name or field_name` cache vocabulary;
  `reason` suffix; raise (`OptimizerError`) vs
  warn (logger) vs silent.
- **Sites + roles.** 1 `D` (member #31). `C`: 3
  in-file branches + [connection][connection] :2240
  (whose docstring states SAME-machinery,
  never-a-second-checker). `O`: direct-caller
  matrix (silent/warn/raise/planned/many/accessor/
  alias) + connection strictness suites. `P`:
  walker/context/extension docstring cites.
- **Challenges.** C9 (1), C10 (1 — R3), C11 (1
  convention; API coupling listed).
- **Owner + lifetime.** This module (per-row
  derivation; threaded values live one resolve).
- **Distinct behavior.** The `"connection_to_attr"`
  arm is the C-ORCH consumer; the kind token is
  caller/callee coupling (R10); the message is
  per-subject (R3); the vocabulary is consumed
  (R11).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles (literal
  `"Unplanned N\\+1: shelf"` pin).
- **Freshness.** Target HEAD `72d62dc4…`;
  connection HEAD `4894f90f…`.

### F-NAME — resolver-name stamp (file-local)

- **Contract + variation.** `_name_resolver` stamps
  `resolve_<field_name>` onto generated closures
  (GraphiQL trace stability; centralizes the
  three branch renames; requires a writeable
  `__name__`).
- **Sites + roles.** 1 `D` (member #32) + the one
  package `resolver.__name__ =` write (:340). `C`:
  3 relation branches + file. `O`: stamp tests
  (many/forward/reverse).
- **Challenges.** C12 (1).
- **Owner + lifetime.** This module.
- **Distinct behavior.** None (sole stamper; the
  mutations `__name__` pins assert factory entry
  names — a different rule, noted not paired).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles (literal
  `resolve_<field>` pins).
- **Freshness.** Target HEAD `72d62dc4…`.

### F-FMETA — resolver FieldMeta source (file-local)

- **Contract + variation.** `_field_meta_for_resolver`:
  registered definition's `field_map` hit →
  canonical `FieldMeta.from_django_field` →
  test-double `_from_field_shape(is_relation=True)`
  fallback (doubles lack `is_relation`; the
  blessed private seam — [field-meta][field-meta]
  documents both call sites as non-drifting).
  `parent_type=None` is test-double-only;
  production must pass `cls` for branch-sensitive
  keys.
- **Sites + roles.** 1 `D` (member #33). `C`:
  factory head only. `O`: registered-attname /
  double-shape tests. `P`: walker/field-meta
  docstring cites.
- **Challenges.** C13 (1).
- **Owner + lifetime.** This module (per-build
  read; resolvers are built once at finalize).
- **Distinct behavior.** The fallback is the
  F-DOUBLE posture at one seam.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles.
- **Freshness.** Target HEAD `72d62dc4…`; field-meta
  HEAD `18ea719a…`; registry HEAD `81bd561c…`.

### F-GATE — custom-visibility routing token (file-local)

- **Contract + variation.** `_custom_visibility_type`:
  related-model None/non-`type` → None; registry
  miss → None; missing definition or identity hook
  → None; else the TARGET TYPE (the recheck calls
  need the type, not a bool). Default hooks stay
  on the fast path preserving prefetch behavior.
- **Sites + roles.** 1 `D` (member #34). `C`:
  factory head (:541) feeding all 9 gates. `O`:
  scoped/unscoped visibility suites both colors.
- **Challenges.** C14 (1 — R7), C24 (pair half).
- **Owner + lifetime.** This module (per-build
  token).
- **Distinct behavior.** Vs walker's bool verdict:
  rejected (R7 — routing token vs plan verdict,
  opposite no-definition postures, dependency
  direction forbids the composition).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles
  (unscoped recheck fires exactly once).
- **Freshness.** Target HEAD `72d62dc4…`; registry
  HEAD `81bd561c…`; walker HEAD `75f9c6b6…`;
  definition HEAD `fa6c4d33…`.

### F-SCOPED — optimizer-scoped trust boundary (file-local)

- **Contract + variation.** `_optimizer_scoped_relation`:
  per-relation (never per-request) verdict from
  the optimizer's scoped-relation set; the stash
  (strictness-gated publish), `DST_OPTIMIZER_PLAN`
  (last-wins introspection), and absent-context
  shapes are explicitly rejected as channels; an
  empty set re-checks (one query beats serving a
  hidden row). `precomputed_key` mirrors the
  `_check_n1` threading convention.
- **Sites + roles.** 1 `D` (member #37). `C`: 8
  in-file scoped-consults (the 9th recheck call,
  :590, rechecks without consulting the set).
  `O`: scoped/unscoped suites both
  colors + warn-frame tests.
- **Challenges.** C18 (1), C11 (convention),
  C24 (pair half).
- **Owner + lifetime.** This module (per-row set
  read).
- **Distinct behavior.** The trust boundary for
  SKIPPING a hook; `_relation_is_planned` is the
  strictness sibling answering a different question
  (report vs skip) — paired, not shared (F-STRICT).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles.
- **Freshness.** Target HEAD `72d62dc4…`; context
  clean `dbc30630…`; plans HEAD `cce98531…`.

### F-MANYVIS — many-side recheck pipeline (file-local)

- **Contract + variation.** `_visible_many_rows`:
  visibility → bound → materialize in both
  colors (sync `list(bounded_rows(...))`; async
  `bounded_rows_async` + unconditional `async
  for` — sound because the boundary normalizes to
  a plain `QuerySet`, slicing keeps it one, and
  every `QuerySet` is `AsyncIterable`, so no
  sync-iterable fallback exists by construction).
- **Sites + roles.** 1 `D` (member #36). `C`: 2
  many gates (prefetched-unscoped, unprefetched).
  `O`: many visibility suites + materialization
  pins. `P`: the `_normalized_visibility_result`
  cite (C-SEAL projection).
- **Challenges.** C17 (1).
- **Owner + lifetime.** This module (per-resolve
  pipeline).
- **Distinct behavior.** Twin-pair with itself
  across the await boundary (principle-5 shape;
  R5 records the cross-arm non-sharing).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles.
- **Freshness.** Target HEAD `72d62dc4…`; querysets
  HEAD `3616927d…`; resource-policy HEAD
  `4b69e974…`.

### F-RESOLVER — cardinality factory + Phase-2 install (file-local)

- **Contract + variation.** `_make_relation_resolver`
  builds the per-field closure: many (prefetch
  fast path with unscoped-recheck + seal-normalize
  + bound, else lazy queryset with bound-into-SQL
  + async-iter arm), reverse-O2O (DoesNotExist →
  None both colors), forward (cheap gate skipping
  the key walk when nothing is armed; elision
  dispatch with unsafe fallback; planned resolve).
  `_attach_relation_resolvers` installs one per
  relation over the caller-passed field list,
  honoring assigned-override skips.
- **Sites + roles.** 1 `D` + 3 closures + 4 nested
  resolves (members #38–#39). `C`:
  [types-finalizer][types-finalizer] :972. `O`: the 45-test
  worktree matrix (44 HEAD + spy gate) + live
  suites. `P`: base/init docstring
  cites.
- **Challenges.** C19 (1), C24 (enforcement — R6).
- **Owner + lifetime.** This module (built once at
  finalize; closures live with the type).
- **Distinct behavior.** Branches compose
  single-owned rules by name (R5/R6); absence
  bindings are FAM-ABSENCE; hops are C-ONEBOUND;
  the recheck call is C-RECHECK.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles.
- **Freshness.** Target HEAD `72d62dc4…`; finalizer
  HEAD `de34ae2a…`.

### F-FILE — file parent-resolver pair (file-local)

- **Contract + variation.** `_make_file_resolver`:
  object-nullability ONLY (falsy `FieldFile` →
  None, else the bound file; no subfield touch,
  no `try/except` — storage failures surface in
  Strawberry's per-subfield resolution via
  `_safe_file_attr`; stamped; `(root, info)`
  signature with unused `info`).
  `_attach_file_resolvers`: the structural twin
  over non-relations resolving via the file map,
  with the BROADER `consumer_authored_fields`
  skip set so annotation-only opt-outs
  (`attachment: str`) receive no resolver
  (spec-037 Decision 3, recorded at both sites +
  finalizer).
- **Sites + roles.** 1 `D` per helper + closure
  (members #40–#41). `C`: finalizer :986. `O`:
  file API suites (null-shape pins live
  read-side). `P`: converters docstring cites.
- **Challenges.** C22 (1), C23 (2 by design — R9).
- **Owner + lifetime.** This module.
- **Distinct behavior.** CONVERGE with verified
  `types-converters-file-null-vs-column-null`
  (resolver-shape vs column nullability still
  separated per Decision 4 — trigger re-checked
  unfired; transcribes nothing). Omission
  verdict: R13.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles.
- **Freshness.** Target HEAD `72d62dc4…`;
  converters HEAD `058f1081…`; finalizer HEAD
  `de34ae2a…`.

### F-DOUBLE — test-double-compat posture (file-local)

- **Contract + variation.** One posture across
  every lenient seam: `getattr` defaults for
  `__dict__` / `_state` / `fields_cache` /
  `_prefetched_objects_cache` / `get_deferred_fields`
  / `to_attr` / `context`; `kind=None` /
  `accessor_name=None` / `parent_type=None`
  fallbacks for direct callers; DoesNotExist
  fallbacks for doubles (FAM-ABSENCE halves);
  `_from_field_shape` fallback (F-FMETA). Doubles
  read as loaded; doubles can still simulate
  deferred/unloaded shapes explicitly.
- **Sites + roles.** 1 posture `D` (this module;
  25 `getattr(` reads). `C`: every probe/factory
  seam. `O`: the double-matrix tests.
- **Challenges.** C6 (1 — the posture varies per
  seam, never wholesale).
- **Owner + lifetime.** This module.
- **Distinct behavior.** CONVERGE with verified
  join-taxonomy-R13 (no lenient-readers module —
  per-site defaults stay; trigger re-checked
  unfired; transcribes nothing).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** Existing oracles.
- **Freshness.** Target HEAD `72d62dc4…`.

### C-SEAL — `sealed-execution-queryset` (converge; transcribes nothing)

Consumer convergence onto the OPEN family (owner
[querysets][querysets]`::_seal_or_defect`; standing
row already lists this file). Consumer sites: the
prefetched path composes `normalized_row_source`
(origin: the single `prefetch_origin` composition)
→ `materialized_rows` → `bounded_rows`, so a
subclass-built cache is normalized before the bound
reads it and Django's own slot answers the fetched
rows; `_visible_*` run hook returns through
`apply_type_visibility_*`'s shared sealed boundary
(the `_normalized_visibility_result` docstring cite
is projection). Zero seal logic re-owned here: no
second `_seal_or_defect`, no second exact-type
rule, no second cause list. Oracles: the
unsealable-prefetch refusal test (accessor-named
error) + visibility suites. Family item inherits
no new site from this file.

### C-RECHECK — `related-object-visibility-recheck` (converge; second definition stands)

Convergence onto the OPEN family (owner
[querysets][querysets]`::related_visibility_queryset_or_default`;
standing row already lists this file). Verified
F5 (querysets item, W2-endorsed) names
`_visible_related_object` the read-side second
definition — "same NAME, different contract" —
and assigns the disprove attempt to the family
item. Fresh-trace deltas for that attempt (not a
counter-verdict): type-keyed input (registry
already resolved by F-GATE) vs model-keyed;
already-fetched instance + `related._state.db`
alias pin vs unpinned base; pk-filter-then-hook
order vs hook-then-tail; dual-color return
(object or coroutine) vs sync-only queryset;
no-primary impossible-by-construction (callers
skip on `None`) vs default-manager fallback.
Coupled: the 3 awaitable-flatten tails (R12) +
`_visible_many_rows`' twin encode the same
dual-color contract — any redesign counts 5
sites, not 1. Oracles: scoped/unscoped suites
both colors. Transcribes nothing (row + F5
already cover this file).

### C-ONEBOUND — `one-sync-boundary` (converge; unconsolidated members)

Convergence onto the OPEN family (owner
[querysets][querysets]`::run_in_one_sync_boundary`; standing
row already lists this file). At HEAD bytes the 3
lazy-fetch arms (:619/:692/:763) + import (:28) +
docstring paragraph (:518–529) are 3 independent
definitions of the one-hop rule — the exact
members the family item consolidates. The owned
worktree orphan already performs that
consolidation (import swap + 3 arm conversions +
paragraph reword, re-proved INTACT run 7); the
family item reconciles HEAD membership against
the owned conversion rather than re-finding it.
Census of already-consolidated callers (by name):
filters/sets, auth/mutations, mutations/resolvers,
permissions, orders/sets; refused alternative
cited in consumers.py (projection). Oracles: the
owned spy gate (worktree; pins all 3 arms +
absence containment on the worker) + HEAD
containment-parity tests. Transcribes nothing.

### C-ORCH — `nested-connection-plan-orchestration` (converge; transcribes nothing)

Consumer convergence onto the OPEN family (owner
[nested-planner][nested-planner]`::plan_connection_relation`;
standing row already lists this file). Consumer
site: `_check_n1`'s `kind="connection_to_attr"`
arm — presence-probe of the caller-threaded
`to_attr` + `reason`-suffixed message — reached
only via [connection][connection]'s synthesized resolver
(which threads whichever attr its fast-path probe
found). This file plans nothing, publishes
nothing, recovers nothing. Transcribes nothing.

### C-GRAMMAR — `relation-connection-to-attr-grammar` (converge; transcribes nothing)

Consumer-by-value convergence onto the OPEN
family (owner [nested-planner][nested-planner]`::relation_connection_to_attr`;
standing row already lists this file). This file
NEVER constructs `_dst_` (0 constructs; docstring
:258–259 is pure projection of the grammar) —
it receives a finished `to_attr` and probes
presence. Producer census (unchanged in shape):
single grammar body + 2 delegates
(nested_planner) + walker re-export aliases +
connection produce/probe pair. Transcribes nothing.

### C-MRO — `mro-map-key-lookup` (adoption; transcribes nothing)

Pure-consumer adoption of the OPEN family
(candidate owner [types-converters][types-converters];
blocked-on-hunt for its same-file legs).
`_attach_file_resolvers` composes
`_field_output_type_for` by name — the walk
itself is written once in converters (its
docstring claims the single site, verified by
that item). No mechanism site here; the standing
row needs no new file. Transcribes nothing.

### FAM-ABSENCE — `relation-absence-containment` (NEW FAMILY for Worker-0)

- **Contract + variation.** "A single-valued
  relation read that resolves to no row collapses
  to None; a consumer's own AttributeError keeps
  raising." Two fallback definitions of the
  catch-spec: reverse-O2O binds a single CLASS
  (`DoesNotExist if present else AttributeError`,
  :606–611); forward binds a TUPLE
  (`(DoesNotExist,) if present else ()`, :660–665
  with the empty-tuple rationale recorded
  in-body). Real-model behavior is identical
  (contain `DoesNotExist` incl. the dual-parent
  `RelatedObjectDoesNotExist`; propagate plain
  `AttributeError` — both pinned); doubles
  without `DoesNotExist` diverge (reverse
  contains AttributeError → None; forward
  propagates). The reverse fallback carries no
  stated reason (contrast the forward comment) —
  the family item decides unify-toward-one-spelling
  (double-visible; oracle updates) vs recorded
  separation with trigger.
- **Sites + roles.** 2 `D` (the bindings). `C`:
  6 `except related_does_not_exist` clauses
  (reverse ×2, forward-fast ×2, forward-slow ×2 —
  all compose the binding by name). `O`: 10
  absence tests (O1 swallow; forward unsaved +
  async + planned + async-planned; reverse
  propagate; reverse real-model + async; forward
  dangling; forward propagate). `P`: the
  forward rationale comment.
- **Challenges.** C20 (2); C24-gate coupling
  (arms carry the visibility gate — R6).
- **Owner + lifetime.** TBD by family item
  (candidate: a shared `_absence_catch(field_meta)`
  helper in this module; both arms become calls).
- **Migration.** N/A (file item names only).
- **Distinct behavior.** Production behavior must
  not move (identical today); only the
  double-without-DoesNotExist verdict is at stake.
- **Behavioral proof.** `static-reviewed` (no
  edit; family item owes execution-verified
  containment parity if it unifies).
- **Structural gate.** Existing oracles (both
  propagate tests fail a bare-`AttributeError`
  regression; family item adds a fallback-shape
  gate if it unifies).
- **Coupling.** R5 (arm composition carries these
  bindings); R6 (gates sit inside the same arms).
- **Freshness.** Target HEAD `72d62dc4…`; oracle
  file HEAD `346e945d…` / worktree `d78d605f…`.

### R1 — `except` arms vs a shared guard (rejected)

- **Shared form considered.** One shared
  exception-guard driver for the 10 code arms
  (:114/:118/:140/:146 probe+stub, 6
  `related_does_not_exist`).
- **Contract difference.** Per-site scope ×
  verdict: deferral-probe fail-soft `False`,
  attname-miss `None`, stub-refusal sentinel,
  absence-containment `None` — no two share both.
  CONVERGE with the verified shared-except-guard
  J1 direction on fresh evidence.
- **Trigger.** A second arm sharing scope AND
  verdict with an existing one.
- **Freshness.** Target HEAD `72d62dc4…`.

### R2 — gates vs a shared exact gate (rejected)

- **Shared form considered.** One shared
  type-gate for `isinstance(to_attr, str)` (:315)
  and `isinstance(related_model, type)` (:384).
- **Contract difference.** Opposite mechanisms
  for opposite questions (narrowing-guard with
  `else True` vs routing-guard with early `None`);
  subclass-tolerant by contract, not exact-type.
  CONVERGE with the verified shared-exact-type-gate
  J2 direction on fresh evidence.
- **Trigger.** A third gate sharing mechanism
  with either.
- **Freshness.** Target HEAD `72d62dc4…`.

### R3 — wordings vs an owned grammar (rejected)

- **Shared form considered.** One owned wording
  grammar for the N+1 message + `reason` suffix +
  `prefetch_origin` + `resolve_<field>` stamp.
- **Contract difference.** Four per-subject
  compositions (strictness verdict, fallback
  cause, seal-refusal origin, trace stamp) with
  disjoint readers; still no owned grammar at
  HEAD. CONVERGE with verified
  per-subject-rejection-grammars on fresh
  evidence. Oracles pin each literally and
  independently (the `reason`-suffix pin lives in
  [test-relay-connection][test-relay-connection]).
- **Trigger.** A second subject needing any one
  of these wordings verbatim.
- **Freshness.** Target HEAD `72d62dc4…`.

### R4 — single/many probe unification (rejected)

- **Shared form considered.** One lazy-load
  predicate parameterized by cardinality.
- **Contract difference.** Same-file intentional
  separation with the reason in-body: the many
  side's only Django-supported cache is the
  prefetch cache, and a `__dict__` short-circuit
  there would exempt consumer-assigned attributes
  from the N+1 contract (C6 moves one side only;
  oracles pin the consumer-set-attribute
  asymmetry). Durable home: the `_will_lazy_load_many`
  docstring (already states it).
- **Trigger.** Django gaining a many-side
  `__dict__`-backed cache, or a spec row
  requiring double-compat on the many side.
- **Freshness.** Target HEAD `72d62dc4…`.

### R5 — fetch-arm unification (rejected)

- **Shared form considered.** One shared
  single-fetch arm body for the 6 member sites
  (reverse / forward-fast / forward-slow ×
  sync/async).
- **Contract difference.** Four branch-varying
  axes no one body absorbs without re-spelling
  the branches as parameters: accessor
  vocabulary (`accessor_name` vs `field_name`),
  absence binding (FAM-ABSENCE halves), key
  threading (precomputed or walked), gate
  spelling (positive vs inverted — spelling, not
  contract; unifying it relieves no change
  obligation). Each arm composes single-owned
  rules by name (probe, hop, binding, scoped
  verdict, recheck) — enforcement sites per the
  `pipeline_write_phase()` precedent, not
  copies. The hop itself converges (C-ONEBOUND);
  the tails couple (R12).
- **Trigger.** A branch-axis collapse (absence
  bindings unified by FAM-ABSENCE + accessor
  vocabulary unified) leaving parameter-only
  variation.
- **Freshness.** Target HEAD `72d62dc4…`.

### R6 — visibility-gate unification (rejected)

- **Shared form considered.** One shared gate
  body for the 9 recheck call sites (many ×2,
  reverse ×2, fast ×2, slow ×2, elision ×1).
- **Contract difference.** 8 compose the
  single-owned pair (`_custom_visibility_type` +
  `_optimizer_scoped_relation` → `_visible_*`) by
  name with branch-local short-circuits (None
  checks, stub checks, prefetched-shape checks);
  the 9th (unprefetched-many, :590) rechecks
  without consulting the set. C24 moves the pair;
  all 9 follow as enforcement sites. Unifying the
  call sites would hide the branch conditions a
  reader needs at each arm.
- **Trigger.** A gate condition that must hold at
  all 9 but cannot live in the pair.
- **Freshness.** Target HEAD `72d62dc4…`.

### R7 — routing token vs walker verdict (rejected)

- **Shared form considered.** One custom-hook
  predicate shared by `_custom_visibility_type`
  and [walker][walker]`::_target_has_custom_get_queryset`.
- **Contract difference (three legs).** (1) I/O:
  type-or-None routing token (the recheck calls
  need the TYPE) vs bool plan verdict
  (select-vs-Prefetch). (2) No-definition
  posture: None (resolve-time: nothing to call)
  vs class-fallback report (plan-time:
  captured-consistency) — already divergent
  inputs, divergent answers. (3) Dependency
  direction: [walker][walker] lazily imports
  `types.definition` (cycle avoidance), so the
  direction is optimizer→types; composing the
  walker's predicate from here reverses it —
  direction wins per principle 7. The WHAT-COUNTS
  rule itself is single-owned
  ([types-base][types-base]`::_detect_custom_get_queryset`
  → flag); both are its consumers.
- **Trigger.** Bare-registration retirement
  converging the postures, or a third consumer
  needing type-from-model routing.
- **Freshness.** Target HEAD `72d62dc4…`; walker
  HEAD `75f9c6b6…`; base HEAD `dda91365…`.

### R8 — recourse omission vs recourse wording (rejected)

- **Shared form considered.** A surface-specific
  `async_recourse` for the two `_visible_*`
  `apply_type_visibility_sync` calls (which take
  the Relay-subject default).
- **Contract difference.** The default's REMEDY
  shape is correct here (async IS possible —
  both helpers have async twins — the same
  property that keeps the Relay recourse
  separate per the verified finding); only the
  subject noun names Relay. Zero tokens owned
  here (composed by omission), and the omission
  is a 7-site cross-surface posture (filters/sets,
  list_field ×2, connection, walker, types/relay
  ×2 where the subject is correct) — not
  file-homable. CONVERGE with the verified
  `sync-boundary-recourse-wording` rejection
  (trigger re-checked unfired).
- **Trigger.** A spec row requiring per-surface
  async-possible recourse subjects (a
  cross-surface card, not this file's defect).
- **Freshness.** Target HEAD `72d62dc4…`;
  recourse census over worktree bytes (all
  DIRTY paths in the trace table).

### R9 — attach-twin unification (rejected)

- **Shared form considered.** One attach loop for
  relations + file columns.
- **Contract difference.** Same-file intentional
  separation, spec-037 Decision 3, recorded at
  BOTH attach docstrings + the finalizer call
  site: the file pass skips the broader
  `consumer_authored_fields` union so
  annotation-only opt-outs receive no resolver;
  the relation pass skips assigned overrides
  only. C23 moves both BY DESIGN. (Decision-3
  record at finalizer :980–983.)
- **Trigger.** Decision 3 reversed (skip sets
  converge).
- **Freshness.** Target HEAD `72d62dc4…`;
  finalizer HEAD `de34ae2a…`.

### R10 — kind token vs grammar ownership (rejected)

- **Shared form considered.** Folding the
  `"connection_to_attr"` token into the
  `to_attr` grammar owner.
- **Contract difference.** The token is
  caller/callee API coupling (dispatch :312 +
  call [connection][connection] :2245 + docstring cites) —
  renaming it moves def + caller as one API,
  never counted; the grammar owner produces the
  token's VALUES, not the dispatch vocabulary.
- **Trigger.** A second dispatch over the same
  token, or a third token-sharing call site.
- **Freshness.** Target HEAD `72d62dc4…`;
  connection HEAD `4894f90f…`; nested-planner
  HEAD `b4dfd4a6…`.

### R11 — strictness comparisons vs vocabulary ownership (rejected)

- **Shared form considered.** Routing the
  `"off"`/`"raise"`/`"warn"` comparisons through
  the extension's `_STRICTNESS_MODES`.
- **Contract difference.** Pure consumers of a
  validated vocabulary (constructor refusal at
  extension :958–960); C26 moves zero definitions
  here. Unknown values silent is unreachable via
  any validated path.
- **Trigger.** A readable vocabulary export from
  the extension, or a fourth mode.
- **Freshness.** Target HEAD `72d62dc4…`;
  extension HEAD `e0e53a8e…`.

### R12 — flatten-tail unification (rejected)

- **Shared form considered.** One
  await-if-awaitable helper for the 3
  `inspect.isawaitable(res)` tails (:629/:705/:778).
- **Contract difference.** Mechanical tails of
  ONE dual-color contract
  (`_visible_related_object`'s object-or-coroutine
  return); the other 12 sites flatten 6 distinct
  values (`value`, `candidate`,
  `candidate_awaitable`, `result`, `conn`,
  `is_authenticated` — per-value idiom, never one
  rule). A 2-line helper would
  be machinery obscuring the call it tails. The
  tails are COUPLED to C-RECHECK: a redesign of
  the dual-color return (twins vs flatten)
  counts all 3 + both `_visible_*` bodies = 5
  sites — recorded here so the family item
  inherits the full count.
- **Trigger.** The C-RECHECK family item
  redesigning the dual-color return.
- **Freshness.** Target HEAD `72d62dc4…`;
  `isawaitable` census (15 at both bytes: 3 here +
  querysets 6, relay 2, extension 1, connection 1,
  auth/mutations 2 at HEAD; worktree carries
  connection 2 / auth 1 with the same total).

### R13 — file-resolver guard omissions (rejected)

- **Shared form considered.** Extending the N+1
  check / visibility gate / row bound to the
  file parent resolver (axis-6 probe).
- **Contract difference.** Every guard in this
  module is relations-scoped per its owner prose
  (`_check_n1`: "if the relation is not planned
  and would lazy-load"; file columns are
  scalar-object reads off an already-fetched
  `FieldFile`, not relation traversals). No
  contract source extends strictness to deferred
  file columns. Absence ≠ gap. Companion probe:
  the forward cheap gate skips `_check_n1` when
  nothing is armed — wire-safe (the extension
  co-publishes live + stash, so a stash-armed
  hand-built context is the only divergent
  shape, and no oracle pins it); the in-body
  "nothing armed the guard" comment over-claims
  exactly that test-only shape.
- **Trigger.** A spec row extending strictness to
  file columns, or an arming channel that sets
  stash strictness without the extension.
- **Freshness.** Target HEAD `72d62dc4…`;
  extension HEAD `e0e53a8e…` (live frame :1078–1084 +
  guarded stash publish :1422, `if` :1416).

### Considered, no row (near-misses cleared with evidence)

- Resolver-key construction: every key via
  `resolver_key(...)` by name; membership reads
  only — zero inline builds, nothing to home.
- `_check_n1` default-arg sentinel: `planned`
  defaults to the module token evaluated once —
  correct by construction, single site.
- Forward `live_strictness` double-read (cheap
  gate + `_strictness_for` re-read on the None
  path): one redundant ContextVar read on one
  path — perf trivia, not a rule.
- `str` f-string copies (`suffix`, message,
  stamp, origin): per-subject compositions —
  owned by R3, no separate row.
- HEAD async docstrings naming `sync_to_async`:
  accurate at HEAD bytes (the owned dirt rewords
  them) — projection of C-ONEBOUND arms.
- `_order_nodes`-style order-key twins: no
  ordering vocabulary here (relation resolvers
  apply no `OrderSet`) — inapplicable, not
  omitted.

## Defects

Zero D-numbered defects. Every candidate found
while tracing either converged onto a verified
direction (R8 recourse, R11 silent-unknown) or
failed the defect bar (no wire input):

- **O1 (observed-not-homed, not a defect).**
  HEAD `except BaseException` arms in
  `_fk_attname_is_deferred` (×2, :114/:118) and
  `_build_fk_id_stub` (:146) swallow
  cancellation/interpreter-exit alongside
  ordinary failure. No feasible project shape
  under supported public API reaches them with
  such an exception (Django's
  `get_deferred_fields` / model `__init__`), so
  the AGENTS.md defect bar (contract row +
  feasible shape + wire input) is not met; the
  worktree hunt dirt already reworks all three
  arms. If closeout wants it homed anyway, home
  it on the hunt's truth-migration card, not a
  DRY card — no DRY change obligation exists.

## Pending execution

None. Read-only trace (no `workspace.py` runs,
no test runs); every proof is `static-reviewed`
and every oracle cited already exists. No
`proof:` / `gate:` entries owed.

## Judgment

The file is a well-factored resolve layer: 14
single-owned rules (all counts 1), 6 lawful
convergences onto open families (consumers ×4:
seal, orchestration, grammar, MRO; 1 named
second definition: recheck; 1 unconsolidated
member: one-boundary — all transcribing
nothing), 1 genuine new family
(`relation-absence-containment`, count 2 on the
fallback spelling), and 13 rejections with
contract differences + triggers (4 converging
with verified directions, 9 fresh). No
production edit owed or made; no defect filed.
The dispatch brief's "no owned ledger hunk"
line is corrected above by content (the
one-sync-boundary orphan matches verbatim) —
the family item for `one-sync-boundary`
reconciles against the owned conversion rather
than re-finding it.

## Implementation (Worker-1)

No tracked changes. Item-scoped diff vs
`ITEM_BASELINE`
(`0490d39b45ff85dd6cd7a50325cb04ac96f7c5f6`) is
empty for `django_strawberry_framework/types/resolvers.py`
(verified: `git diff <baseline> -- <target>`
prints nothing — all dirt predates dispatch).
Hunk attribution by content against
`git show HEAD:<path>` (15 `@@` regions,
45+/21-): hunks 1/3/11 + the boundary conversions
inside 12/14/15 are OWNED (adopted orphan
`one-sync-boundary`, ledger-matched verbatim +
run-7 re-prove INTACT; the brief's "no owned
ledger hunk" label is a dispatch mislabel —
content governs, no stop); the `truth.*`
migration + elision-refusal prose/except
narrowing + `check_deadline` lines are
concurrent-external hunt/maintainer dirt — all
fingerprinted, none judged, none touched. No hunk
in a path this item touches falls outside those
two homes: no stop triggered. The only new path is
this artifact (untracked, owned by this item) plus
`docs/dry/temp-tests/types-resolvers/head.py`
(untracked HEAD-bytes scratch for Worker-2's
line-number checks; Worker-0 removes by explicit
path after verification). No `.py` touched, so no
ruff run is owed. No commit per standing rule.
HEAD unmoved (`0c0537e2`) from dispatch to writing.

## Index rows for Worker-0

| `types-resolvers-module-mechanics` | `django_strawberry_framework/types/resolvers.py` (module docstring layer map + 21 import statements binding 30 names, all consumed + logger alias + implicit surface) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-dispatch-sentinels` | `django_strawberry_framework/types/resolvers.py::_EMPTY_ELISIONS` (+ `_PLAN_UNREAD` + `_FK_ELISION_UNSAFE` opaque identity tokens) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-elision-stub-and-deferral` | `django_strawberry_framework/types/resolvers.py::_build_fk_id_stub` (+ `_fk_attname_is_deferred` confirmed-deferral probe + router db pin) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-lazy-load-probes` | `django_strawberry_framework/types/resolvers.py::_will_lazy_load_single` (+ `_will_lazy_load_many` prefetch-only twin) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-strictness-and-planned-ladders` | `django_strawberry_framework/types/resolvers.py::_strictness_for` (+ `_relation_is_planned` stash-OR-scoped read) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-n1-probe` | `django_strawberry_framework/types/resolvers.py::_check_n1` (strictness-first gate + kind dispatch + threading convention + raise/warn) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-name-stamp` | `django_strawberry_framework/types/resolvers.py::_name_resolver` (sole `resolve_<field>` stamper) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-fieldmeta-source` | `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` (registry hit → canonical → double fallback) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-custom-visibility-token` | `django_strawberry_framework/types/resolvers.py::_custom_visibility_type` (type-or-None routing token, None on missing definition) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-scoped-trust-boundary` | `django_strawberry_framework/types/resolvers.py::_optimizer_scoped_relation` (per-relation scoped-set verdict, stash/PLAN rejected) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-many-recheck-pipeline` | `django_strawberry_framework/types/resolvers.py::_visible_many_rows` (visibility → bound → materialize, dual-color) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-cardinality-factory-and-install` | `django_strawberry_framework/types/resolvers.py::_make_relation_resolver` (+ `_attach_relation_resolvers` Phase-2 install) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-file-pair` | `django_strawberry_framework/types/resolvers.py::_make_file_resolver` (+ `_attach_file_resolvers` broad-skip twin) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `types-resolvers-double-compat-posture` | `django_strawberry_framework/types/resolvers.py` (lenient `getattr` defaults + None-fallbacks + double seams) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | file-local |
| `relation-absence-containment` | TBD by family item (candidate: `django_strawberry_framework/types/resolvers.py` via a shared catch-spec helper; reverse class-fallback vs forward tuple-fallback) | `django_strawberry_framework/types/resolvers.py` | Family `relation-absence-containment` | open |
| `types-resolvers-except-arms-vs-shared-guard` | `django_strawberry_framework/types/resolvers.py::_fk_attname_is_deferred` (rejection recorded here; CONVERGE with the verified shared-except-guard J1 direction on fresh evidence — 10 arms, per-site scope × verdict) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-gates-vs-shared-exact-gate` | `django_strawberry_framework/types/resolvers.py::_custom_visibility_type` (rejection recorded here; CONVERGE with the verified shared-exact-type-gate J2 direction on fresh evidence — opposite mechanisms, subclass-tolerant) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-wordings-vs-shared-grammar` | `django_strawberry_framework/types/resolvers.py::_check_n1` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence — 4 per-subject compositions, still no owned grammar at HEAD) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-probe-split` | `django_strawberry_framework/types/resolvers.py::_will_lazy_load_many` (rejection recorded here; same-file intentional separation — prefetch-only many cache vs double-compat single cache; durable home the in-body docstring) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-arm-unification` | `django_strawberry_framework/types/resolvers.py::_make_relation_resolver` (rejection recorded here; fresh 6-site split — 4 branch-varying axes; enforcement sites per the pipeline_write_phase precedent) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-gate-unification` | `django_strawberry_framework/types/resolvers.py::_optimizer_scoped_relation` (rejection recorded here; fresh 9-site split — all compose the single-owned pair by name) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-routing-vs-walker-verdict` | `django_strawberry_framework/types/resolvers.py::_custom_visibility_type` (rejection recorded here; fresh triple-leg split — token vs verdict, opposite no-definition postures, optimizer→types direction wins) | `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/base.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-recourse-omission` | `django_strawberry_framework/types/resolvers.py::_visible_related_object` (rejection recorded here; CONVERGE with the verified sync-boundary-recourse-wording rejection on fresh evidence — remedy-correct, 7-site cross-surface posture) | `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/relay.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-attach-twin-split` | `django_strawberry_framework/types/resolvers.py::_attach_file_resolvers` (rejection recorded here; same-file intentional separation — spec-037 Decision 3 skip sets, recorded at both sites + finalizer) | `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/types/finalizer.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-kind-token-vs-grammar` | `django_strawberry_framework/types/resolvers.py::_check_n1` (rejection recorded here; fresh pair — caller/callee API coupling vs value grammar at nested_planner) | `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/optimizer/nested_planner.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-strictness-consumers` | `django_strawberry_framework/types/resolvers.py::_check_n1` (rejection recorded here; fresh pair — pure consumers of the validated extension vocabulary) | `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/optimizer/extension.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-flatten-tails` | `django_strawberry_framework/types/resolvers.py::_visible_related_object` (rejection recorded here; fresh triple — mechanical dual-color tails coupled to the C-RECHECK redesign; trigger: that family's verdict) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |
| `types-resolvers-file-guard-omissions` | `django_strawberry_framework/types/resolvers.py::_make_file_resolver` (rejection recorded here; fresh axis-6 verdict — guards are relations-scoped per owner prose; cheap-gate wire-safe with test-only residual) | `django_strawberry_framework/types/resolvers.py` | File `types/resolvers.py` | rejected |

## Families

Worker-0 must add one `## Families` item:

- `Family relation-absence-containment — dry-rule-relation-absence-containment.md — no artifact on disk; undispatched (named by File types/resolvers.py FAM-ABSENCE; 2 same-file fallback definitions + 6 composing except clauses + 10 oracles; unify-vs-record decision owed)`

## Independent verification (Worker-2)

Recorded before opening `## Findings` (only the
artifact's headings, `## System trace`,
`## Verification`, and tail sections read).
Target HEAD bytes via `git show HEAD:` (882
lines, blob `72d62dc4…`); W1's scratch
`docs/dry/temp-tests/types-resolvers/head.py`
hashes `72d62dc4…` — byte-identical to HEAD,
used for line checks below. HEAD `0c0537e2`
unmoved at this writing.

### W2 independent trace

The module is the generated-resolver layer for
finalized `DjangoType`s: three cardinality
closures (many list, reverse O2O, forward
FK/O2O) built by `_make_relation_resolver`,
installed by `_attach_relation_resolvers`; a
file-column parent pair
(`_make_file_resolver` /
`_attach_file_resolvers`); the B3 N+1 probe
(`_check_n1` over strictness + planned
ladders + single/many lazy-load predicates);
the FK-id elision stub + deferral probe; the
resolve-time visibility recheck pair; and the
per-relation optimizer-scoped trust gate. It
owns no seed, no visibility boundary, no row
bound, no key/to_attr grammar, no strictness
vocabulary — all composed by name from
`utils/querysets.py`, `resource_policy.py`,
`optimizer/plans.py`,
`optimizer/nested_planner.py`,
`optimizer/extension.py` /
`optimizer/_context.py`, `utils/relations.py`,
`types/converters.py`, `utils/execution_mode.py`.

Independent enumeration (AST over HEAD bytes,
`ast.Module.body`): **42 members** — 1 module
docstring + 21 imports + 3 sentinels
(`_EMPTY_ELISIONS` :72, `_PLAN_UNREAD` :78,
`_FK_ELISION_UNSAFE` :90) + 17 defs
(`_fk_attname_is_deferred` :93 through
`_attach_file_resolvers` :853). Independent
census: `except` arms exactly 10
(:114/:118/:140/:146 + 6 absence arms
:623/:638/:696/:713/:767/:787);
`isinstance(` ×2; code `raise` ×1;
`__name__` write ×1; `_dst_` ×2, both
docstring prose, 0 constructed;
`sync_to_async` ×5 (import :28, docstring
:520, arms :619/:692/:763).

Independent hunk attribution (worktree
`640905c6` vs HEAD, 15 `@@` regions,
45+/21-), by content against the run-2
ledger row (`types/resolvers.py — adopted
orphan one-sync-boundary`: 3 lazy-fetch arms
through imported `run_in_one_sync_boundary`,
`sync_to_async` import dropped) and the run-7
ledger re-prove (arms at worktree
637/713/786; maintainer `check_deadline` 6
hits adjacent, non-overlapping):

- Owned: hunk 1 (`sync_to_async` import
  drop), hunk 3 (`run_in_one_sync_boundary`
  import add), hunk 11 (factory docstring
  reword to the shared worker), and the
  `sync_to_async(getattr,
  thread_sensitive=True)` →
  `run_in_one_sync_boundary(getattr, ...)`
  conversions inside hunks 12/14/15
  (reverse-O2O, forward fast-path,
  forward main-path — exactly the 3
  ledger arms).
- Concurrent-external: hunk 2
  (`check_deadline` + `truth` imports),
  hunks 4/5/8/9/10 (hunt `truth.*`
  migration: `_in_instance_namespace`,
  `truth.is_type`, `# truth: ok`,
  narrowed `except`), hunks 6/7
  (elision-refusal prose + `except
  BaseException` → `except Exception`),
  hunk 13 (forward-entry `check_deadline`),
  and the `check_deadline` lines inside
  12/14/15 (maintainer relation-deadline
  dirt). No hunk falls outside these two
  homes; the dispatch "no owned ledger
  hunk" line is a mislabel — content
  governs, no stop.

Matrix expectations (own discharge): (1)
cross-flavor — relation OUTPUT resolve vs
write-flavor INPUT decode share a theme,
not a rule (opposite directions + error
contracts); visibility recheck is the one
genuine touch, converging on the open
family; (2) sync/async twins — dual-color
bodies share every pure decision and differ
only at the await boundary (principle-5
pair shape, kept); the 3 HEAD
`sync_to_async` spellings are the already-
consolidated `one-sync-boundary` members
(worktree carries the owned conversion);
(3) derived knowledge — keys, accessor,
kind, seeds, bounds all composed by name,
zero inline builds; attname reads are
descriptor-column reads, not pk-reader
members; (4) round-trip — `to_attr`
produce (nested_planner) vs probe (here)
halves with one grammar owner; stash
publish vs read halves; stub-build vs
resolve fallback halves; (5) other media —
45 package oracles spell literals (no
owner-table reads), docstrings are
projection; (6) omission — every branch ×
(N+1, visibility, hop, bound) enumerated;
many-side absence arm absent by contract
(managers never raise); file guards absent
by spec-037 owner prose; forward vs
reverse-O2O fallback spellings differ and
are the one count-2 candidate.

Own change challenges (definitions only):
absence-fallback unification → 2 (reverse
class-fallback vs forward tuple-fallback);
boundary-hop change → 0 here at worktree
(3 HEAD arms follow the verified owner);
visibility-recheck change → compose-by-name
(converge); seal/normalize change →
compose-by-name (converge); `to_attr`
grammar change → 0 here (pure consumer,
zero grammar literals); resolver-key
change → 0 here (composed); map-key
lookup change → 0 here (`_field_output_type_for`
consumer → adopt into open
`mro-map-key-lookup`); single/many probe
split → distinct caches, intentional
(reject with contract difference);
strictness-mode addition → 0 here
(extension owns; comparisons follow);
attach skip-set change → 2 by design
(spec-037 Decision 3 split); stub-shape
change → 1 (`_build_fk_id_stub`);
name-stamp change → 1 (`_name_resolver`).

Owners I would choose: every convergence
owner already exists (querysets,
resource_policy, plans, nested_planner,
converters, extension/_context);
FAM-ABSENCE owner TBD by its family item
(candidate: this module via one catch-spec
helper; unify-vs-record owed there, with a
lean to unify — the reverse `AttributeError`
fallback reads as drift against the
forward tuple-fallback's stated reason);
O1 (HEAD `except BaseException` arms)
fails the AGENTS.md defect bar (no
contract row + feasible shape + wire
input reaches them; worktree already
reworks them) → observed-not-homed,
not a defect; zero D-numbered defects.

Reconciliation against `## Findings`
follows in the next section.

### Reconciliation (post-Findings)

Read `## Findings` (lines 376–1238) after
recording the trace above. Every routing
decision reconciles; every count below was
re-derived mechanically at both bytes
(`git show HEAD:` + worktree grep/AST).

1. **Enumeration 42/42: STANDS.** My AST
   count matches (1 docstring + 21 imports
   + 3 sentinels + 17 defs); every member
   #0–#41 lands in a home, and every
   target-internal `:NNN` in the table
   resolves at HEAD bytes (all 17 def
   lines, all 3 sentinel lines, all
   import lines re-checked). Nested-def
   census (10) re-derived exactly. Zero
   dead imports re-confirmed — but the
   bound-name literal is 30, not 33 (E1).
2. **Hunk attribution: STANDS.**
   Independent attribution matches W1
   line-for-line: hunks 1/3/11 fully
   owned, hunks 12/14/15 mixed (owned
   conversions + external `check_deadline`
   lines), hunks 2/4/5/6/7/8/9/10/13
   fully external. The 3 conversions are
   exactly the ledger's 3 arms; the
   run-7 re-prove lines (637/713/786 +
   6 deadline hits) re-verified. The
   dispatch-mislabel correction is
   correct, on record, and complete. No
   stop owed (file item, zero edits;
   item diff vs `ITEM_BASELINE` empty —
   re-verified: `git diff 0490d39b… --`
   target prints nothing).
3. **Adoption + 5 convergences: STAND.**
   C-SEAL (by-name compose; `_seal_or_defect`
   ×0 here; origin single-composed :538→:579);
   C-RECHECK (verified-F5 cross-checked at
   HEAD artifact bytes :859; deltas are
   legitimate family-item material, not a
   counter-verdict); C-ONEBOUND (HEAD arms
   :619/:692/:763 + import + docstring;
   5-file caller census re-derived, schema.py
   hit is docstring at both bytes,
   consumers.py:1290 projection
   confirmed); C-ORCH (connection HEAD
   :2240 threads `to_attr`+`reason`;
   SAME-machinery docstring :2166–2169);
   C-GRAMMAR (0 constructs here, :258–259
   projection; producer census re-derived:
   1 body + 2 delegates + walker aliases
   + connection pair); C-MRO (one by-name
   call; walk owned by converters).
   All transcribe nothing — correct.
4. **FAM-ABSENCE: ENDORSED (new family).**
   Bindings re-read at HEAD (:606–611
   class-fallback, no stated reason;
   :660–665 tuple-fallback with recorded
   rationale); 6 excepts compose by name;
   all 10 oracles located (:572/:626/:643/
   :656/:676/:690/:725/:742/:754/:804);
   real-model identical, doubles diverge
   — a genuine count-2 (C20) on one rule
   ("what the catch degrades to when the
   target model is unknown"). Unify-vs-record
   rightly left to the family item; lean
   to unify recorded pre-reading stands.
5. **R1–R13: ALL STAND** (contract
   differences re-probed at HEAD bytes +
   second sites): R1 (4 scope×verdict
   groups over 10 arms); R2 (:315 narrow
   vs :384 route); R3 (4 per-subject
   wordings; pins: N+1 :1030-form,
   `resolve_` ×7, origin :1636, reason in
   relay-connection suite ×2 — suite
   unstated, see E7); R4 (in-body reason
   + :473 asymmetry pin); R5 (4 axes
   re-verified: accessor vocabulary,
   threading, gate spelling, bindings);
   R6 (9 recheck CALL sites confirmed —
   but only 8 consult the scoped set,
   see E4); R7 (3 legs at walker HEAD
   :205–242 + base :864 + lazy import
   :1464); R8 (Relay default + 7-site
   census re-derived at current worktree
   bytes); R9 (Decision 3 at both attach
   docstrings + finalizer :980–983);
   R10 (token-vs-values split; pointers
   need re-basing, see E5); R11 (pure
   consumers; vocabulary at extension
   :150/:958); R12 (mechanical-tail
   reasoning stands; census is 15 not
   14, see E3); R13 (cheap-gate logic +
   co-publish :1078–1084 + :1422
   re-derived; pointers need re-basing,
   see E5). Triggers adequate throughout;
   couplings marked.
6. **O1 + zero-defect: STAND.** O1 arms
   re-read at HEAD (:114/:118/:146);
   no feasible wire input reaches them
   with a `BaseException` under supported
   API; worktree already reworks all
   three. The reverse-fallback concern
   routes to FAM-ABSENCE (real models
   always carry `DoesNotExist`), not a
   defect. No independent defect found.

Artifact checks: matrix discharged on the
real surface (no axis excused by a found
consolidation); C1–C28 counts sound
(C11 listed-not-counted, correctly);
freshness 25/26 re-hash identical (E6 is
the one drift); `## Pending execution`
correctly empty (static-reviewed file
item, no `proof:`/`gate:` owed); ruff
check + format `--check` pass on the
artifact; `check_trailing_commas.py
--check` excludes `dry-*.md` (0
violations); link scaffold carries all 10
groups; per-cycle `:NNN` + cycle-bookkeeping
vocabulary permitted in `dry-*.md`
scratch (no AGENTS.md violation); no
tests owed.

### Verdict: revision-needed (record accuracy only)

Nothing routes differently; no count-as-decision
moves. But mechanical evidence must
reproduce, and these literals do not (all
checked at HEAD blob `72d62dc4` unless
noted). Resubmission by the SAME Worker-1
context; re-verify is pointer-and-census
only.

- **E1 (propagates to plan index).**
  "33 bound import names" → **30** (21
  statements; zero dead re-confirmed).
  Fix 3 occurrences: F-MECH contract,
  C2 `(33/33…)`, index row
  `types-resolvers-module-mechanics`.
- **E2.** "`async_execution` 8 dispatches"
  → **6 code dispatches** (F-MECH census;
  8 = occurrences incl. import :59 +
  docstring :520).
- **E3.** R12 census "14 sites (3+11)" →
  **15 at both bytes** (3 here + 12:
  querysets 6, relay 2, connection 2,
  extension 1, auth/mutations 1);
  re-derive the "N different values"
  claim over 12.
- **E4.** F-SCOPED "9 in-file gates" →
  **8** call `_optimizer_scoped_relation`
  (9 = recheck CALL sites; :590 rechecks
  without consulting the set);
  disambiguate in F-SCOPED + C24.
- **E5 (pointer basis).** Non-target
  `:NNN` (and 4 target-internal ones)
  are worktree-relative under HEAD
  fingerprints. Re-base to HEAD bytes:
  connection :2271→**2240**, :2276→**2245**;
  walker :460→**459**, :650→**649**,
  :835→**834**; extension :949→**958**–960,
  :1222→**1232**,
  :1406–1412→frame **1078**–1084 + stash
  **1422**; field-meta :232→**219**,
  :354→**334**; finalizer :916→**972**,
  :930→**986** (Decision-3 record
  :980–983); base :1770→**1767**;
  converters :486→**492**, :535→**543**;
  R10 dispatch :326→**312**; R12 tails
  :648/:727/:802→**:629/:705/:778**.
  (context :397, types-init :7,
  converters :29 already resolve at HEAD.)
- **E6.** list_field worktree print
  `450e87c9…` vs current `450e87cd…`:
  re-fingerprint at resubmission (R8's ×2
  re-confirmed at current bytes —
  substance stands either way).
- **E7 (bytes-stating).** "45 tests" =
  worktree (44 HEAD + owned spy gate —
  disclose); qualify "HEAD bytes
  throughout" (target HEAD; dirty inputs
  both, pointers HEAD per E5); name the
  R3 reason-pin suite
  (`tests/test_relay_connection.py`).

Reproduce with: `git show HEAD:<path> | grep -n …`
per pointer; AST import census + `grep -c`
recounts per E1–E4. No production edits;
no plan edits; scratch `head.py` stays for
the re-pass (Worker-0 removes it after
verification).

HEAD `0c0537e2` unmoved at verdict.

### Re-pass (pass 2; same Worker-2 context)

Resubmission (`ready-for-verification/2`)
re-checked pointer-and-census only. Each
E-item re-derived mechanically, not
re-read:

- E1 ✓ — 30 bound names in F-MECH, C2,
  index row; no `33` literal remains
  outside line numbers, hashes, and
  prior-record quotes.
- E2 ✓ — 6 code dispatches at the exact
  HEAD lines (:405/:424/:591/:615/:688/
  :759) + import/docstring occurrence
  breakdown.
- E3 ✓ — 15 at both bytes; HEAD split
  (querysets 6, relay 2, extension 1,
  connection 1, auth 2) and worktree
  split (connection 2 / auth 1)
  independently reproduced; the 6
  distinct flattened values verified
  site-by-site over the other 12.
- E4 ✓ — 8 consults + :590 unscoped
  recheck in F-SCOPED, C24, System
  trace; R6 keeps the accurate "9
  recheck call sites".
- E5 ✓ — stale pointers gone from the
  findings range (the one `:326` hit is
  the HEAD raise line, correct); all
  re-based pointers resolve at HEAD
  bytes, including the newly supplied
  guard (`if` :1416) guarding the :1422
  stash publish.
- E6 ✓ — table `450e87cd…` matches
  current worktree hash; ×2 calls at
  :1378/:1382 current bytes.
- E7 ✓ — 4 disclosure spots; bytes
  basis stated (target HEAD, dirty
  inputs both, pointers HEAD); R3 names
  the pin suite with link definition.

Residual (confined, non-blocking): the
`## Iterations` log cites the reason-pin
lines as :2313/:2330 — worktree-relative.
HEAD lines are :2273/:2290
(`tests/test_relay_connection.py`,
verified). R3's finding itself names only
the suite and is correct; no finding,
index row, or family handoff depends on
the log's parenthetical. Recorded here so
no future cycle re-derives it.

Substance untouched (spot-checked
FAM-ABSENCE, challenges, index rows,
structure); target diff vs `ITEM_BASELINE`
still empty; ruff check + format
`--check` pass; HEAD `0c0537e2` unmoved.
Record reproduces. Verdict: **verified**.

## Iterations

### Resubmission pass 2 (Worker-1, same context)

Applied Worker-2's E1–E7 (record accuracy
only); every item re-derived at HEAD bytes
before applying, substance unchanged (42/42,
attribution, 6 convergences, FAM-ABSENCE, R1–R13,
O1 + zero-defect all stand):

- E1: import census 33 → **30** bound names
  (21 statements; AST recount; zero dead
  re-confirmed). Fixed F-MECH contract, C2,
  index row `types-resolvers-module-mechanics`.
- E2: `async_execution` 8 → **6 code dispatches**
  (:405/:424/:591/:615/:688/:759; + import :59
  + docstring :520 = 8 occurrences).
- E3: `isawaitable` census 14 → **15 at both
  bytes**. HEAD split re-derived (not the
  verdict's parenthetical, which matches
  worktree): 3 here + querysets 6, relay 2,
  extension 1, connection 1, auth/mutations 2;
  worktree carries connection 2 / auth 1 with
  the same total. "Different values" re-derived:
  6 distinct (`value`, `candidate`,
  `candidate_awaitable`, `result`, `conn`,
  `is_authenticated`) over the other 12.
- E4: 9 → **8** `_optimizer_scoped_relation`
  consults; the 9th recheck call (:590)
  rechecks without consulting the set.
  Disambiguated in F-SCOPED + C24, propagated
  to the System-trace census + R6 (which keeps
  "9 recheck call sites" as the accurate
  call-count).
- E5: all `:NNN` pointers re-based to HEAD
  bytes and re-verified line by line:
  connection :2271→:2240, :2276→:2245; walker
  :460→:459, :650→:649, :835→:834; extension
  :949→:958–960, :1222→:1232,
  :1406–1412→live frame :1078–1084 + guarded
  stash publish :1422 (`if` :1416, guard
  re-verified); field-meta :232→:219, :354→:334;
  finalizer :916→:972, :930→:986 (+ Decision-3
  record :980–983, verified); base :1770→:1767;
  converters :486→:492, :535→:543; R10 dispatch
  :326→:312; R12 tails :648/:727/:802→
  :629/:705/:778. (context :397, types-init :7,
  converters :29 re-confirmed resolving at HEAD.)
- E6: list_field worktree print re-fingerprinted
  `450e87c9…` → **`450e87cd…`** (concurrent
  drift; HEAD `21380eb7…` unchanged); R8 ×2
  re-confirmed at current bytes (:1378
  single-line + :1382).
- E7: "45 tests" disclosed as **44 HEAD + owned
  spy gate** (4 spots: System-trace oracles,
  matrix axis 5, F-RESOLVER, freshness table);
  "HEAD bytes throughout" qualified (target
  HEAD; dirty inputs both; pointers HEAD); R3
  names the reason-pin suite
  (`tests/test_relay_connection.py`
  :2313/:2330) with a new link definition.

No production edits; no plan edits; scratch
`head.py` stays for the re-pass. Status →
`ready-for-verification/2`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[connection]: ../../django_strawberry_framework/connection.py
[execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->

[test-relay-connection]: ../../tests/test_relay_connection.py
[test-resolvers]: ../../tests/types/test_resolvers.py

<!-- examples/ -->

[test-products-visibility-api]: ../../examples/fakeshop/test_query/test_products_visibility_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

