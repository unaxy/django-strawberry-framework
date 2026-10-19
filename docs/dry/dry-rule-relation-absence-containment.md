# DRY review: `relation-absence-containment`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule: a single-valued relation descriptor read that resolves to no row
collapses to `None`; a consumer's own `AttributeError` keeps raising. The
catch is the target model's `DoesNotExist` ONLY, never a bare
`AttributeError`, because Django's per-relation `RelatedObjectDoesNotExist`
inherits from BOTH, so the `DoesNotExist` side already contains every ORM
absence signal while a consumer descriptor bug propagates.

Pre-change the rule had two authoritative definitions of its catch spec in
`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`,
both deriving "what to catch" from `field_meta.related_model`:

- reverse OneToOne: a single CLASS,
  `related_model.DoesNotExist if present else AttributeError`
  (pre-edit WT:721-726, no stated reason);
- forward FK / forward OneToOne: a TUPLE,
  `(related_model.DoesNotExist,) if present else ()`
  (pre-edit WT:778-783, with the recorded empty-tuple rationale).

Six `except` clauses compose the two bindings by name (reverse x2,
forward-fast x2, forward-slow x2). Real-model behavior was identical on both
branches; doubles without `DoesNotExist` diverged (reverse contained
`AttributeError` into `None`, forward propagated). No oracle pinned the
divergent fallback on either branch; every oracle pins the shared contract.

Verdict: CONFIRM. Consolidated at the re-derived owner
`django_strawberry_framework/types/resolvers.py::_absence_catch_spec` (new):
one spec derivation, both bindings compose by name, fallback unified toward
propagate (the forward spelling, the only one with a stated reason).
Count 2 -> 1 on all three variation axes. Net over ITEM_BASELINE:
+140/-24 (+29/-24 production: helper + 2 one-line compositions; +111/-0
tests: 3 new tests).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Sibling flavors read in full:
   `forms/resolvers.py` best-effort reconstruction catch (R1),
   `mutations/resolvers.py::locate_instance` pk-locate catch (R2),
   `types/relay.py` raisers (R3), `rest_framework/resolvers.py` upload
   sizing (R6), `types/relay.py` node locate (R3/R5). Each excluded with a
   contract difference; none shares the rule.
2. **Sync/async twins.** The 6 arms are 3 sync + 3 async twins with
   byte-identical except bodies (`return None`); both bindings feed both
   colors. The consolidation is factory-time and color-independent, so the
   twin split is untouched; twins were already enforcement sites composing
   by name, never definitions.
3. **Derived rather than repeated.** Swept `getattr` presence probes with a
   `None` default over relation roots (`connection.py` window-attr probes,
   relay id reads): all probe non-descriptor attrs or always-present
   columns, never the ORM absence signal (R5). The two bindings derived by
   the same means with different fallback values: the duplication itself.
4. **Inverse / round-trip pairs.** Derive (factory binding) vs compose (6
   excepts) halves already joined by name. Raise-side
   (`types/relay.py` raisers) vs contain-side: opposite directions (R3).
   Django's raise vocabulary (dual-parent `RelatedObjectDoesNotExist`) is
   the external oracle both halves agree on, verified in the installed
   Django 6.1 source.
5. **Contracts restated in another medium.** Production (1 definition +
   6 consumers) / oracles (14 package tests + 3 live suites, all
   independent: literal messages, `None`-identity, spy-call tuples; no
   test reads the owner) / prose (factory docstring, helper docstring,
   call-site pointer, test docstrings incl. the "same absent-row contract"
   pin). Counted separately; only definitions drive the verdict.
6. **Enforcement by omission.** Enumerated every cardinality x containment:
   reverse-O2O yes/yes (sync/async), forward-fast yes/yes, forward-slow
   yes/yes, many-side n/a (managers never raise `DoesNotExist`),
   file n/a (falsy check, no descriptor), elision-stub n/a (concrete
   column, verified R1 split). No member lacks a guard the contract
   extends to it.

### Enumeration

Instruments (all over post-edit WT bytes unless noted) + disposition of
every hit:

- `DoesNotExist` literal census: 61 lines in 19 files (mechanical
  `grep -rc`). Target file 11: helper docstring 5 + helper code 2 (the
  one definition) + factory docstring 3 + call-site pointer 1
  (projections). `forms/resolvers.py` 4 -> R1; `mutations/resolvers.py`
  3 -> R2; `types/relay.py` 5 -> R3; `types/definition.py`,
  `forms/inputs.py`, `keyset.py`, `optimizer/nested_planner.py`,
  `optimizer/plans.py`, `optimizer/join_taxonomy.py`,
  `mutations/inputs.py`, `utils/querysets.py`, `utils/relations.py`,
  `connection.py`, `rest_framework/resolvers.py`,
  `rest_framework/serializer_converter.py`, `relay.py`, `exceptions.py`,
  `list_field.py` (33 combined) -> R7 (`FieldDoesNotExist`: meta
  lookups, not row absence).
- `except AttributeError` census: 4 lines. Target `:174` (stub column
  read) -> R4; `utils/inputs.py:1662`, `list_field.py:363,393` -> R6.
- `ObjectDoesNotExist|RelatedObjectDoesNotExist` census: 3 lines.
  Target comment (dual-parentage prose) -> projection;
  `forms/resolvers.py:428,438` -> R1.
- `except <name>` composing clauses: 6, all in the target
  (`:760,:775,:827,:844,:900,:920` post-edit) -> consumers.
- `except (` census over the six relation-touched files: 5 sites
  (`rest_framework/resolvers.py:678`, `mutations/resolvers.py:1224`,
  `connection.py:735,866,1126`) -> R6, each read, none a descriptor
  absence catch.
- `getattr((root|instance|related|obj|parent)` census: 39 lines -> R5
  (presence probes / column reads / many-side `.all()`), except the
  family consumers and the R4 column arm.

Every census hit lands in F1, a consumer slot, or R1-R8. No second
definition of the catch-spec rule exists package-wide.

### Challenges

Authoritative definitions only; consumers, oracles, projections listed,
never counted. Pre-change counts re-derived fresh at pre-edit WT bytes
(== ITEM_BASELINE bytes for the target); post-change at current WT.

| # | Change posited | Pre | Post |
|---|---|---|---|
| C1 | Known-model catch changes (narrow/widen the caught signal, e.g. a new Django absence class outside `target.DoesNotExist`) | **2** (reverse binding + forward binding) | **1** (helper) |
| C2 | Unknown-model fallback verdict changes (any reconsideration of the double contract) | **2** (disagreeing: `AttributeError` vs `()`) | **1** (helper) |
| C3 | Derivation guards change (`None` check / `hasattr` shape, e.g. string `related_model` must resolve-or-raise) | **2** (guard pair per binding) | **1** (helper) |

Consumers moving with every challenge: the 6 except clauses (by-name
composition, zero edits owed). Oracles moving: none (all pin the shared
contract, which is unchanged for every pinned shape). Projections moving:
none (helper docstring owns the rationale; factory docstring already
stated the unified contract).

The pre-change C2 count deserves one explicit note: the two bindings
disagree, so "the fallback" is not one rule pre-change - the count 2 is
the cost of the divergence itself (any fallback decision must be made
twice, unguided). Unification direction is forced: propagate is the only
spelling with a stated reason (forward comment + factory docstring +
two propagate oracles + the "same absent-row contract" oracle pin);
unifying toward contain would rewrite the contract and weaken oracles.

## Findings

### F1 - `relation-absence-containment` (CONFIRMED + CONSOLIDATED, 2 -> 1)

- **Contract + variation.** "A single-valued relation read that resolves
  to no row collapses to `None`; a consumer's own `AttributeError` keeps
  raising." Varies on: the caught signal when the model is known (C1),
  the fallback when it is unknown (C2), the derivation guards (C3).
- **Sites + roles.** 1 `D` post-change:
  `django_strawberry_framework/types/resolvers.py::_absence_catch_spec`
  (`:552-573`; pure derivation, "not cached" per principle 4 - bound per
  factory call into immutable closure locals, no cross-call state). 2
  composing bindings (`:745` reverse, `:788` forward). 6 `C` (the except
  clauses, unchanged). 14 `O` (11 pre-existing absence oracles + 3 new;
  listed under Tests). `P`: factory docstring contract paragraphs,
  helper docstring (rationale owner), one-line call-site pointer,
  `test_relations_async_api.py:91` docstring (names
  `related_does_not_exist`, still accurate - both binding names kept).
- **Challenges.** C1/C2/C3 all count 2 pre, 1 post.
- **Owner + lifetime.** `types/resolvers.py` via `_absence_catch_spec`,
  by principle 7: both consumers live in the same factory function; the
  rule's vocabulary (descriptor absence, consumer-bug propagation) is
  resolver-domain; no dependency moves (same module). FieldMeta rejected
  as owner (R8: metadata carrier, not resolver control flow; widens a
  walker/planner-shared surface for one consumer module). `utils/`
  rejected (single-consumer-module rule, not cross-cutting).
- **Migration.** Reverse binding: 6-line conditional -> one call (the
  `AttributeError` fallback deleted). Forward comment + binding: 18
  lines -> 3-line pointer + one call (rationale moved to the helper,
  not copied). Except clauses, binding names, and all 6 consumers:
  byte-identical apart from line shifts.
- **Distinct behavior.** Real models: byte-identical behavior
  (`except (X,)` == `except X`; fallback unreachable - every Django
  model carries `DoesNotExist`). Doubles WITH `DoesNotExist`:
  identical. Doubles WITHOUT: reverse now propagates `AttributeError`
  (was: contain into `None`) - the unified verdict, previously
  unpinned on both branches, now pinned both branches. Reachable only
  via direct private-API calls with fabricated fields (test-only
  shape); no wire input reaches it.
- **Behavioral proof.** `execution-verified`:
  (a) `tests/types/test_resolvers.py` 53/53 green in the workspace copy
  (run `dry-20261001T183124-110020`; rejects "the consolidation broke a
  pinned verdict"); (b) live relation suites 109/109 green
  (`test_products_visibility_api` + `test_relations_async_api` +
  `test_scalars_api`, run `dry-20261001T183319-7fa510`; rejects "the
  factory change broke a real query"); (c) failability entry 1: fallback
  narrowed to `(AttributeError,)` fails exactly the 2 new fallback
  tests with `DID NOT RAISE AttributeError`, baseline 2 passed (run
  `dry-20261001T183239-3135d7`; rejects "the new tests cannot fail").
- **Structural gate.** `test_single_valued_absence_specs_compose_the_shared_owner`
  (spy on `_absence_catch_spec` across one reverse + one forward factory
  build, asserting 2 derivations + contained `None` through each):
  fails when either branch bypasses the owner. Negative control
  `execution-verified`: behavior-preserving hand copy inlined at the
  reverse binding fails exactly the gate while all 7 behavior oracles in
  scope pass (failability entry 2, same run; rejects "the gate pins
  behavior, not composition"). The 1-failing-row outcome is the correct
  grade for a negative control (DRY.md demands every behavior oracle
  pass it), not weak pinning.
- **Coupling.** None blocking. D1 (doc-only prose slip, see Defects)
  rides closeout homing; the consolidation stands without it.
- **Freshness.** Target pre-edit WT `b37b85d6` == ITEM_BASELINE
  `02719049` bytes; target post-edit WT `5abd9b93` (== workspace copy
  blob in the prove record); target HEAD `2c588030`; HEAD `dd0b6691`
  unmoved throughout. Oracle file post-edit WT `7c12883d`, HEAD
  `233bc37c`. Django external oracle: installed 6.1
  `related_descriptors.py` (`ForwardManyToOneDescriptor:132-300`,
  `ReverseOneToOneDescriptor:431-560`, dual-parent `type(...)` at
  `:149-165`/`:450-466`). Exclusion fingerprints (WT/HEAD, all read at
  WT): forms/resolvers `9f7ff436`/`61678b9e`, mutations/resolvers
  `2ff49673`/`d77a6c68`, types/relay `a9b90a17`/`a200f190`,
  utils/inputs `0826c9d4`/`0b7d353c`, list_field `b534ea32`/`3842542a`,
  rest_framework/resolvers `08310034`/`5e80bbf7`, connection
  `6c4b01f9`/`38491372`, optimizer/field_meta `99f7b1d3`/`7c9afe35`,
  relay `63bbba0b`/`037723cd`, utils/relations `a6692e4d`/`e64a7a8f`,
  utils/querysets `6d471bd7`/`adc74b64`, keyset `513b54e3`/`4fd54f28`,
  types/definition `e79d7129`/`ff80ef02`, forms/inputs
  `65ac558f`/`0ba0d9a5`, mutations/inputs `fe2218dd`/`fd0f17d8`,
  optimizer/nested_planner `b6ff0a0e`/`8c3a45f5`, optimizer/plans
  `2e4332cc`/`a584c63f`, rest_framework/serializer_converter
  `a22dcbe3`/`469a4959`, exceptions `34e2e6be`/`7a4fb661`. Live
  oracles: test_products_visibility_api `318bc95e` (clean),
  test_relations_async_api `349618d8` (clean), test_scalars_api
  `edc50088` (clean).
- **Tests.** Three, all in `tests/types/test_resolvers.py` (package
  tier: both fallback arms are unreachable via a real GraphQL query -
  real models always carry `DoesNotExist` - so AGENTS.md falls back to
  `tests/`; the helper's live-reachable arm stays covered by the
  existing live suites, re-run green above):
  `test_reverse_one_to_one_without_does_not_exist_propagates_attribute_error`
  (`:895`, unified verdict, fails pre-change),
  `test_forward_resolver_without_related_model_propagates_attribute_error`
  (`:923`, survivor pin incl. the `None`-model arm, passes pre-change),
  `test_single_valued_absence_specs_compose_the_shared_owner` (`:948`,
  composition gate). No live-tier test owed: no new live-reachable
  behavior (real-model verdicts unchanged and already live-pinned).
- **Type gates (workspace copy, tree state with this change).**
  `basedpyright`: 0 errors, 0 warnings, 0 notes (run
  `dry-20261001T183151-976dce`). `check_any.py`: 128 allowed uses at 89
  sites, exit 0, no new `Any`, no stale entry (run
  `dry-20261001T183213-029f1c`). `check_truthful_reads.py --check`:
  errors 0 (run `dry-20261001T183215-68232f`). No new cast, `Any`, or
  suppression: the helper reuses the forward binding's annotation shape
  verbatim. `ruff check --fix` + `ruff format`: clean on both touched
  paths. `check_trailing_commas.py --check`: 0 violations on both.
- **Cells.** Sharded/PG `inapplicable by construction` (for Worker-2 to
  judge): the consolidation renames which exception classes two
  factory-time bindings hold; it touches no queryset, alias, SQL, or
  executor decision, and the verdict change fires only for doubles,
  which never reach a database.

### R1 - forms reconstruction catch (excluded)

- **Shared form considered.** `forms/resolvers.py:428,438`
  (`except (AttributeError, ObjectDoesNotExist)` in
  `_reconstruct_unprovided_data`) as a third absence-containment
  definition.
- **Contract difference.** Best-effort update-pipeline reconstruction,
  not read nullability: unreadable relation -> omit the field (M2M) or
  fall through to `model_to_dict` (FK), never `return None` to a
  GraphQL field. Unconditional broad catch (base
  `ObjectDoesNotExist` + `AttributeError`, plus a `getattr(..., None)`
  default covering the dual-parent signal and the except covering a
  plain dangling-FK `DoesNotExist`) with no model-conditional
  derivation and no unknown-model axis. Different subject, verb,
  mechanism, and downstream.
- **Trigger.** The reconstruction starts deriving its catch from the
  target model (a conditional spec with a fallback question).
- **Home.** Its own docstring (reconstruction contract) + this row.

### R2 - mutations pk-locate catch (excluded)

- **Shared form considered.** `mutations/resolvers.py:737`
  (`except model.DoesNotExist: return None` in `locate_instance`) as a
  third definition.
- **Contract difference.** Write-pipeline row locate via
  `queryset.get(pk=...)`, not a descriptor read; the model is always
  known (`model_for(target_type)`), so there is no fallback-spec axis
  at all; `None` maps to a not-found `FieldError` on `id`
  (indistinguishable from a hidden row), never a GraphQL null.
- **Trigger.** A locate path with an unknown model needing a
  catch-what fallback.
- **Home.** Its own docstring (miss -> `FieldError` contract) + this row.

### R3 - relay raisers (excluded)

- **Shared form considered.** `types/relay.py:433,1014`
  (`raise model.DoesNotExist`) as the same rule.
- **Contract difference.** Opposite direction: signaling "required id
  identifies no row" so one consumer catch covers `qs.get()` /
  `_order_nodes()` / required misses - never containment into `None`.
- **Trigger.** A relay path containing (rather than raising) a
  `DoesNotExist`.
- **Home.** `_raise_if_required` docstring + this row.

### R4 - elision-stub column arm (excluded)

- **Shared form considered.** `types/resolvers.py:174-176`
  (`except AttributeError: return None` on the FK attname read in
  `_build_fk_id_stub`) as a third definition.
- **Contract difference.** Different subject (concrete column, never a
  relation descriptor) with no spec derivation (bare arm, no
  `related_model` question); confirms the verified
  `types-resolvers-except-arms-vs-shared-guard` scope x verdict split
  (attname-miss vs absence-containment). A double missing the column
  reads as a null FK - a column contract, not the descriptor contract.
- **Trigger.** The stub read deriving its catch from the target model.
- **Home.** The `_build_fk_id_stub` docstring + this row.

### R5 - getattr-default presence probes (excluded)

- **Shared form considered.** `connection.py:2330,2333`
  (`getattr(root, per_key_attr/to_attr, None)` window probes),
  `types/relay.py:365` id-column read, and the remaining 30+ `getattr`
  census hits as containment by another means.
- **Contract difference.** Presence probes on optimizer-published
  plain attributes (never descriptors raising `DoesNotExist`),
  always-present column reads, or many-side `.all()` (managers never
  raise). No absence signal exists at any of these sites to contain.
- **Trigger.** A probe site reading a descriptor that raises the
  ORM absence signal.
- **Home.** Each site's own prose + this row.

### R6 - unrelated `except` sites (excluded)

- **Shared form considered.** `utils/inputs.py:1662` (import-attr
  leniency), `list_field.py:363,393` (direct-call-stub wire-name
  leniency), `rest_framework/resolvers.py:678` (unsizable upload),
  `connection.py:735,866,1126` (windowed-connection error mapping),
  `forms/resolvers.py:178` (`serializable_value` leniency) as shared
  absence machinery.
- **Contract difference.** Each read in full; every one guards an
  unrelated subject (imports, stubs, files, pagination, form keys).
  None reads a relation descriptor; none derives a catch from a
  target model.
- **Trigger.** Any of these sites catching a relation absence signal.
- **Home.** Each site's own prose + this row.

### R7 - `FieldDoesNotExist` population (excluded)

- **Shared form considered.** The 33 meta-lookup hits across 15 files
  as the same rule.
- **Contract difference.** Different exception about a different
  subject: `Model._meta` field resolution (schema shape), never row
  absence. No hit catches, derives, or names a row-absence signal.
- **Trigger.** A `FieldDoesNotExist` site handling row absence.
- **Home.** This row (no shared owner exists across 15 files).

### R8 - FieldMeta as alternative owner (rejected)

- **Shared form considered.** Deriving the spec on
  `optimizer/field_meta.py::FieldMeta` (e.g. a `related_model`-based
  property) instead of in `types/resolvers.py`.
- **Contract difference.** The except-spec is resolver control flow,
  not relation metadata; FieldMeta is a walker/planner-shared carrier
  and gains a one-consumer control-flow helper under this shape.
  Dependency direction allows either home (types already imports
  optimizer.field_meta); narrowest-cohesive-owner wins per principle 7
  and both consumers sit in the one factory.
- **Trigger.** A second consumer module outside `types/resolvers.py`
  needing the spec.
- **Home.** The helper docstring ("The one spec both single-valued
  branches ... compose by name") + this row.

No sub-rules decomposed: single-rule family, no new index rows owed
beyond the Family `relation-absence-containment` row itself, which
Worker-0 marks consolidated.

## Defects

D1 (doc-only, for Worker-0 closeout homing; non-blocking, consolidation
stands without it): `examples/fakeshop/test_query/test_relations_async_api.py:91`
docstring says the absent-card row drives
`reverse_one_to_one_resolver`'s "`except related_does_not_exist:
return None` arm" - but the reverse closure catches
`reverse_does_not_exist`; `related_does_not_exist` is the FORWARD
binding's name. Pre-existing (file clean at HEAD `349618d8`),
zero behavioral impact, names kept by this change so the slip is
unchanged. Owner: that test module's docstring.

No other defects. In particular the `forms/resolvers.py:437` shape
(`getattr(instance, name, None)` inside
`except (AttributeError, ObjectDoesNotExist)`) was re-derived, not
assumed, dead: the default covers the dual-parent signal while the
except stays live for a plain dangling-FK `DoesNotExist` - coherent,
no finding.

## Judgment

CONFIRM-consolidated. The two catch-spec bindings encoded one contract
(stated identically in the factory docstring, the forward rationale,
two propagate oracles, and one "same absent-row contract" oracle pin)
with same reasons to change on all three variation axes and no
intentional separation behind the divergence. One helper, two
composing bindings, six untouched consumers, three permanent tests,
both failability entries pinned, all gates green. Counts: 1 finding
consolidated (2 -> 1), 8 exclusions with triggers, 1 doc-only defect
routed, 0 sub-rules, 0 pending executions.

## Implementation (Worker-1)

Tracked edits (4 hunks, all attributed to this item; every other hunk
on both paths predates ITEM_BASELINE and was left byte-identical):

- `django_strawberry_framework/types/resolvers.py` (+29/-24):
  new `_absence_catch_spec` (`:552-573`, docstring owns the contract +
  rationale); reverse binding -> one call (`:745`, `AttributeError`
  fallback deleted); forward comment + binding -> pointer + one call
  (`:786-788`). Except clauses and binding names unchanged.
- `tests/types/test_resolvers.py` (+111/-0): 3 tests (`:895`, `:923`,
  `:948`) in the clean absence block; concurrent hunks (module
  docstring line, elision-test rewrite) and the ledgered spy gate
  untouched.

Concurrency attribution performed by diff content vs
`git show HEAD:<path>` before the first edit: target hunks split into
ledgered one-sync-boundary content (import swap, 3 arm conversions,
docstring reword) and concurrent work (maintainer `check_deadline` +
except-`BaseException` rework, hunt truth migration); oracle hunks
split into the ledgered spy gate + concurrent wording/elision rework.
All four edit spans landed on lines identical between HEAD and WT
(context lines of adjacent hunks at most); no concurrent line edited,
reverted, or tidied. Proposed Worker-0 transcription: Family
`relation-absence-containment` -> consolidated; index row likewise;
`## Owned changes` rows for the 2 paths above.

## Independent verification (Worker-2)

### Own trace (recorded before opening ## Findings)

Rule re-derived from the target at ITEM_BASELINE bytes (`git show
02719049:django_strawberry_framework/types/resolvers.py`, reverse
conditional + forward comment/binding read in full): a single-valued
relation descriptor read that resolves to no row collapses to `None`;
anything else raised by the read propagates. The catch is the target
model's `DoesNotExist` ONLY, never a bare `AttributeError`, because
Django's per-relation `RelatedObjectDoesNotExist` inherits from BOTH.

Sites (pre-change) and the roles I assign:

- D1 (definition): reverse-OneToOne binding in
  `django_strawberry_framework/types/resolvers.py::_make_relation_resolver`
  - `related_model.DoesNotExist if guard else AttributeError`, a single
  CLASS, no stated reason for the fallback.
- D2 (definition): forward binding in the same factory -
  `(related_model.DoesNotExist,) if guard else ()`, a TUPLE, with a
  recorded empty-tuple rationale in the comment above it.
- Consumers (6): the `except` clauses composing the two bindings by
  name - reverse sync + async (2), forward fast-path sync + async (2),
  forward planned-path sync + async (2). Post-edit at `:760, :775,
  :827, :844, :900, :920`, bodies byte-identical (`return None`).
  Verified by regex search, not by reading W1's list.
- Oracles: the absence block in `tests/types/test_resolvers.py`
  (reverse swallow/propagate/real-model rows, forward
  unsaved/dangling/propagate rows, async parities) plus live suites
  (`test_relations_async_api.py` absent-card row,
  `test_products_visibility_api.py` reverse-O2O rows,
  `test_scalars_api.py` dangling-FK row). Every oracle I read pins the
  SHARED contract (known-model swallow into `None`, known-model
  `AttributeError` propagation); none I have found pins either
  unknown-target fallback verdict (full fallback-pin sweep still
  open at trace time - see step 4 below).
- Projections: factory docstring (states the unified contract on BOTH
  bullets - the reverse bullet says `try/except DoesNotExist`, which
  the reverse `AttributeError` fallback violated for unknown
  targets), the pre-change forward comment (rationale), the post-change
  helper docstring + call-site pointer.

Definition counts per posited change (my own challenges, pre AND post):

- X1 (known-model catch widens/narrows, e.g. a new Django absence
  class outside `target.DoesNotExist`): pre 2 (both bindings derive
  the catch independently), post 1 (helper).
- X2 (unknown-model fallback verdict reconsidered): pre 2 AND
  disagreeing (`AttributeError` vs `()` - any fallback decision is
  made twice, unguided), post 1 (helper).
- X3 (derivation guard changes - `None` check / `hasattr` shape):
  pre 2 (guard pair per binding), post 1 (helper).

Owner I would choose: a module-private helper in
`django_strawberry_framework/types/resolvers.py` next to the factory -
the narrowest cohesive owner both branches already live beside, so no
dependency reverses and no sibling flavor is imported for machinery.
(FieldMeta as an alternative owner: not chosen - it is a field-shape
record, while the catch spec is resolve-time containment policy; the
R8 rejection will be judged on its own reasons after I read it.)

Census re-derivations (mechanical, post-edit WT bytes, `.py` only):

- `DoesNotExist`: 61 lines in 19 files - REPRODUCED EXACTLY
  (independent file-by-file count). Target-file 11 = helper
  docstring 5 + helper code 2 + factory docstring 3 + call-site
  pointer 1 - REPRODUCED EXACTLY.
- `except AttributeError`: 4 lines (target `:175`,
  `utils/inputs.py:1662`, `list_field.py:363,393`) - REPRODUCED
  EXACTLY.
- `ObjectDoesNotExist|RelatedObjectDoesNotExist`: the stated
  instrument yields 4 `.py` lines (target `:558`,
  `forms/resolvers.py:103,428,438`), not 3 - the import at `:103`
  is undispositioned. It belongs to the same home as its two
  consumers; verdict-neutral, record-accuracy note.
- `except <name>` composing clauses: 6, at `:760,:775,:827,:844,
  :900,:920` - REPRODUCED EXACTLY.
- `except (` over the six relation-touched files
  (`types/resolvers.py`, `types/relay.py`, `forms/resolvers.py`,
  `mutations/resolvers.py`, `rest_framework/resolvers.py`,
  `connection.py`): 8 hits - `forms` 3 (R1 home),
  `mutations/resolvers.py:1224` + `rest_framework/resolvers.py:678`
  + `connection.py:735,866,1126` (R6 home). W1's "5 sites" matches
  the R6 subset; R1 must also name `forms:178`.
- `getattr((root|instance|related|obj|parent)`: the stated
  instrument yields 47 `.py` lines (53 with `__pycache__`), not 39 -
  a delta of 8 I could not close under any natural scoping (code-only
  37, six-files 34, delimiter-terminated 47). The disposition rule
  (R5 except family consumers + the R4 column arm) covers every hit
  by category, so I verify each of my 47 hits' roles directly in
  step 2 below instead of inheriting the count.

Unification-direction pre-judgment (evidence read, verdict owed to
step 4): propagate is the only spelling with a stated reason -
factory docstring (both bullets), forward rationale comment, the
reverse known-target propagate oracle
(`test_o1_reverse_one_to_one_propagates_plain_attribute_error`), the
forward known-target propagate oracle
(`test_forward_resolver_propagates_consumer_attribute_error`), and
the "same absent-row contract" pin in the unsaved-instance oracle
docstring. Unifying toward contain would contradict all five. The
reverse-unknown-target behavior change (contain -> propagate) is
within mandate ONLY IF the old verdict was truly unpinned - the
fallback-pin sweep + oracle re-runs below decide that.

### Reconciliation (after opening ## Findings)

Every difference between my trace and W1's findings, explicitly:

- Sites/roles: AGREE. 2 definitions pre -> 1 post, 6 by-name
  consumers, 11 pre-existing + 3 new oracles (the 11 re-enumerated
  by `def` lines `:573,:627,:644,:657,:677,:692,:758,:793,:810,
  :822,:872` - all below the insert point, all pin the shared
  contract), projections as listed. (File-item time said 10
  oracles; the +1 is drift since that trace, verified present.)
- Challenges: AGREE. My X1/X2/X3 are C1/C2/C3 under other names;
  2 pre / 1 post on all three, including the C2
  disagreeing-fallbacks note.
- Owner: AGREE. Same module-private helper; R8's FieldMeta
  rejection verified (walker + planner both import
  `optimizer/field_meta.py::FieldMeta`; narrowest-cohesive-owner
  wins per principle 7).
- Censuses: 4 reproduce EXACTLY (`DoesNotExist` 61/19 with the
  5+2+3+1 target split, `except AttributeError` 4, composing
  clauses 6 at the same six lines, `except (` R6 subset 5 with
  the other 3 homed R1/R6 - R6 names `forms:178`, closing my
  trace-time question). 2 do NOT reproduce - see record notes
  N1/N2 below. Neither hides a site: every hit of my wider
  counts is dispositioned by category and read.
- Unification direction: AGREE (propagate), for the same five
  reasons plus one more: the factory reverse bullet already
  stated `try/except DoesNotExist`, which the old reverse
  fallback violated for unknown targets - the divergence was
  against the documented contract, not an undocumented choice.

### Steps 2-8

Step 2 (enumeration + matrix). All 47 of my `getattr` hits read
and homed: 3 F1 sync consumers (`:774,:843,:919`; the async
three pass bare `getattr`, outside the census), 1 R4 (`:174`),
3 F1 docstring projections (`:589,:598,:600`), 40 R5 (probes,
column reads, `.all()`s, prose). None derives a catch spec;
no second definition exists. Matrix: all six axes discharged
against the real surface - axis 2 twins are 3 sync + 3 async
with byte-identical `return None` bodies (read at all six
sites); axis 4's Django oracle re-verified in the installed
6.1 `related_descriptors.py` (dual-parent `type(...)` at both
descriptors, both `DoesNotExist`-first); axis 6's many/file/
elision n/a verdicts each confirmed at the owning body
(`.all()` never raises, `_make_file_resolver` carries no
`try`, stub reads a concrete column).

Step 3 (counts, roles, oracles). Counts confirmed above. The
test-file item diff is +111/-0: purely additive, so no
pre-existing oracle was touched, let alone rewritten to read
the owner. The 3 new tests pin literals (`DID NOT RAISE`
messages, `None`-identity) and spy-call counts
(`assert len(seen) == 2`); the gate imports the owner module
only to count derivations, never to build an expectation.

Step 4 - point (a) (the load-bearing call). The fallback was
truly unpinned pre-change on BOTH branches: a whole-tree sweep
for unknown-target doubles (`related_model=SimpleNamespace()`
/ `related_model=None` / missing) found exactly one resolver
double without `DoesNotExist` outside the new tests (the
forward naming test, which resolves a present sentinel and
raises nothing), and every reverse test used a known double or
a real model. No live suite can pin it (doubles never reach
the wire). Every pinned shape re-ran green in my copy: 53/53
package (run `dry-20261001T184356-d557c7`) + 109/109 live
(5 relations-async + 22 visibility + 82 scalars, runs
`dry-20261001T184423-6a9011`,
`dry-20261001T184437-c52da4`,
`dry-20261001T184512-7145dd`). Judgment: the
contain->propagate change on reverse-unknown-target doubles
is WITHIN the behavior-preserving mandate - it moves an
unpinned, wire-unreachable, contract-contradicting verdict
toward the only reasoned spelling, and the direction is
forced by five convergent pins (factory docstring both
bullets, forward rationale, two propagate oracles, the
"same absent-row contract" pin). No pinned behavior moved.

Step 4 - point (b) (equivalence + annotation). `except (X,)`
== `except X` demonstrated by execution (exact, subclass,
and non-matching cases identical; `except ()` catches
nothing) and by language semantics (tuple form is an
element-wise `isinstance` check; neither form catches
`ExceptionGroup` - only `except*` does - so no interplay
delta). The dropped forward `: tuple[...]` annotation is
inference-equivalent: the helper's declared return IS that
spelling, and basedpyright reports 0/0/0. Every known-target
consumer is behavior-identical.

Step 6 (rejections, freshness, gates, pending, coupling,
concurrency). R1-R8 each carry contract difference + trigger
+ home; every cited site read in full and confirmed (R1
reconstruction omit/fall-through with unconditional broad
catch; R2 always-known-model locate mapping to `FieldError`;
R3 opposite-direction raisers; R4 bare column arm; R5 probes
with no absence signal; R6 seven unrelated subjects; R7
meta-lookup exception; R8 one-consumer control flow). R4's
converge-claim verified against the standing record
(`dry-file-types__resolvers.md` R1: "attname-miss `None`,
stub-refusal sentinel, absence-containment `None` - no two
share both"). Freshness re-hashed same-kind (blob vs blob):
`5abd9b93` + `7c12883d` match; 5 exclusion spot-checks match;
3 live pins match; HEAD `dd0b6691` unmoved. Failability
re-derived with WIDER scopes than W1 (full 53-file both
entries, my own manifest): entry 1 (fallback narrowed)
fails exactly the 2 new fallback tests (`2 failed, 51
passed`, both `DID NOT RAISE AttributeError`); entry 2
(bypass hand-copy at the reverse binding) fails ONLY the
gate (`1 failed, 52 passed`, `assert 1 == 2`) - all 52
behavior rows pass the bypass, so the gate pins composition,
not behavior. Both restores byte-proved (`5abd9b93` round
trip). Pending-None correct (every proof execution-verified,
all re-run here). Coupling none (D1 rides closeout; the
consolidation stands without it). Concurrency re-derived
from `git diff HEAD` content: 16 HEAD hunks on the target, 6
on the oracle file; W1's 4 hunks land on baseline lines with
concurrent (`check_deadline`, truth migration) and ledgered
(one-sync-boundary) content context-only and preserved
byte-for-byte (helper insert purely additive; reverse
`-` lines exactly the 6-line conditional; forward `-` lines
exactly the 18-line comment+binding above the `check_deadline`
line; test insert identical-hunk additive). Item diff
+140/-24 over exactly 2 paths, no new files - as claimed.

Step 7 (prose rules, points (c)/(d), lint, types, rows).
Item diff prose: no process provenance, no stale symbol refs
(`path:NN` allowed in `dry-*.md`). Point (c) D1: CONFIRMED
pre-existing (byte-identical at HEAD, file clean),
doc-only (seed-helper docstring), correctly routed (owner
named, closeout homing), non-blocking (binding names kept,
slip unchanged either way). Point (d) `tests/` tier:
CONFIRMED - both fallback arms are unreachable via a real
query (every real Django model carries `DoesNotExist`;
`related_model` is never `None` for a real field), the
helper's live-reachable arm stays covered by the re-run
live suites, and no new live-reachable behavior exists;
no live-tier test owed. `ruff format --check` (2 already
formatted) + `ruff check` (all passed) +
`check_trailing_commas.py --check` (0 violations) green on
both paths. Banned-word sweep of the new tests: zero hits.
Type gates re-run in my copy: basedpyright 0/0/0 (run
`dry-20261001T184730-fc108a`), check_any 128/89 exit 0 (run
`dry-20261001T184738-db95b2`), truthful-reads tier-1 0
errors 0 (run `dry-20261001T184739-93e03c) - all match the
run-11 baseline; no new cast/`Any`, no `ALLOWED_ANY` move
owed. Behavior rows: 53 package + 109 live re-run green
above, one heavy suite at a time. No new defect: nothing
found meeting the GOAL.md trust-boundary bar. Sharded/PG
`inapplicable by construction` JUDGED SOUND: factory-time
exception-class bindings touch no queryset, alias, SQL, or
executor decision, and the verdict delta fires only for
doubles, which never reach a database.

Record notes (Worker-2, non-blocking - corrected here in the
durable record, no revision round owed):

- N1: the `getattr` census states 39 lines; the stated
  instrument yields 47 `.py` lines (53 with `__pycache__`),
  unreproducible as 39 under code-only (37), six-file (34),
  or delimiter-terminated (41) scopings. All 47 homed above;
  decision-neutral.
- N2: the dual-parent census states 3 lines; the stated
  instrument yields 4 `.py` lines - the `forms:103` import is
  undispositioned and belongs to R1 with its consumers.
  Decision-neutral.
- N3: "no new suppression" overstates by one: the gate test
  adds `# noqa: N818`, identical to the 3 pre-existing
  instances in the same file (mechanical carve-out for
  Django's `DoesNotExist` naming, required for ruff-clean).
  Convention-conformant.

Verdict: verified. Counts 2 -> 1 on C1/C2/C3; point (a)
within mandate with zero pinned movement; point (b)
equivalent with clean inference; (c) correctly routed;
(d) tier correct; all gates green; no defects.
