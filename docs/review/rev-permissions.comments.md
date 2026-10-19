# Review · Comments: `django_strawberry_framework/permissions.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=623c43216c5c50961b3dc0f5448ae6d21926ece1

## Trace

Read in dispatch order: AGENTS.md, START.md, REVIEW.md, worker-1.md, the
plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3;
`## Owned changes` names no row for this item), `rev-permissions.md`
(skeleton, `Status: reviewing`). Sibling axis records were absent at
open; both landed mid-pass and were read whole:
`rev-permissions.performance.md` (`findings-recorded`: F1 per-edge
`.filter` clones, F2 eager renderer names; Handoff read) and
`rev-permissions.mechanics.md` (`no-findings`; R1/R15 and Handoff read —
R1 withdraws one candidate below, R15's glossary lead is theirs, noted
in Handoff). Then the WHOLE live target (740 lines: module docstring,
15 symbol docstrings, 6 inline comments) and the WHOLE own test module
`tests/test_permissions.py` (2119 lines: module docstring, every
test/helper/class docstring, every inline comment).

The target is dirty with concurrent work (`M
django_strawberry_framework/permissions.py`, on the plan's run-3 Drift
lines) but byte-identical to ITEM_BASELINE (empty `git diff
ITEM_BASELINE --` on both graded paths); every grade is against the
live text at the fingerprints below, which agree with both siblings'
(`ef66f8b9`, `c22af728`).

Instruments, all static in the shared tree (no workspace run: nothing
graded imports the package or opens a database): `review_inspect.py`
orientation + stripped source + JSON under
`docs/review/temp-tests/permissions/comments/inspect/`;
`build_tree_md.py --list-docstrings` passes on both files (1 module, 0
breaking, each); `check_citations.py --paths <file> --substrings`
reports 5 citations / 0 violations in the target and 23 / 0 in the own
tests; the REVIEW.md provenance pattern plus `we`/`you`/`I`,
`Tests that`/`Ensures`, and `.py:NN` sweeps (voice and line-refs clean
in both files; every provenance-pattern hit graded below).

Contract trace, each load-bearing claim against its body plus one real
caller or contract source: the sealed boundary
(`utils/querysets.py::apply_type_visibility_sync` coroutine-close,
`_prepared_visibility_source` apply_type_visibility defaults,
`_normalized_visibility_result` Manager coercion + construction-time
alias pin, `_CASCADE_SEAL_POLICY` = model-rows-off / slice+combined
rejected, `run_in_one_sync_boundary` neutral
`sync_to_async(thread_sensitive=True)` owner); asgiref
`contextvars.copy_context()` into the worker; the `types/relay.py:44`
redundant-alias convention + package-root `__all__` via `types`;
spec-034 Decisions 5/7/8/9/10/11/12 (subjects match every pointer; D5
"step 1" is the spec's own vocabulary) and its `## Edge cases and
constraints`; shipped hooks (products four roots `fields=None`-shaped,
library five incl. the `CirculationDeskType` fixed subset,
`RepairTicketType` not cascading back, `GenreType` hook-free);
`Entry.item`/`Entry.property`/`Item.category` non-null,
`Venue.lead_ticket` nullable, `RepairTicket.venue` non-null,
`CirculationDesk` carrying exactly the asserted relation set,
`Edition.publisher`/`publisher_2`, `Printing`'s converging graph,
`ScalarSpecimen.parent`/`tag`, `PatronProfile` to_field + O2O shape,
`TaggedItem` GFK triple; every live test name the module docstring
cites (9/9 exist); products `check_name_permission` staff-only bodies
byte-matching the local mirrors; all six `services.seed_*` helpers;
`_make_info` mirrors + `_NoneDirectionSyncOrder` precedent +
`_field_specs`/factory caches + the `_permission_fallback_path`
python-attr fallback; `registry.clear()` replaying the
`orders.input_namespace` subsystem clear (M3); upstream
`django-graphene-filters` `_cascade_seen` (M2's vocabulary origin);
history spot-checks (`3131a2fe` direct `__in` composition + identity
skip, `c68aecab` own slice checks, `1dd9273a` Manager coercion) for the
R2 keeps.

Fingerprints (`git hash-object` of every file whose body was read):
target `ef66f8b9ce5c17813558d10150f945d0c9420bef`; own tests
`c22af72892e3430ea51d5e4bef0112871445c604`;
`utils/querysets.py` `8fc556d582b313e4aed7cddaa15f9a8480d88a46`;
`types/base.py` `dc67f084cbc969d64b7b1f1ef18c388095d394f7`;
`registry.py` `492654d219d1061fef33f186d962dc5369b71ebe`;
`sets_mixins.py` `088ddab0c0f68c0605bc4a440dfa3daa544452dd`;
`orders/sets.py` `60859f2d54525acfdb3dc997d3e931ff3d58d956`;
`orders/inputs.py` `2d258da74ee36f5d851ffa6550462b0fd65bd460`;
`orders/factories.py` `b9fd62bcbdb787c5aa168f4f48b9e74704e69876`;
`utils/permissions.py` `1c9cfd398e6096e03bda82ba93dfd66a6d2fb890`;
`mutations/permissions.py`
`55e5edf80c601f373c1802d34fc4e497919d17e7`;
`types/relay.py` `4b2a9df59d6dc99270e3aa8ffac397468f7eee1b`;
`__init__.py` `0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`apps/products/schema.py` `04a5afe3dddff9279660ae1370924e03857d57e7`;
`apps/products/models.py` `02d3ea18e94fc70461decd57c081706f326d9b1b`;
`apps/products/services.py`
`ece9da7a1d5a1ad88f09f42a980c4436972a68a0`;
`apps/products/filters.py`
`6a93b09dd6adf6fcd30ebe445e4598aa760363cd`;
`apps/products/orders.py`
`448f926ebe41e6e31de45dbb3efba2f365a7d870`;
`apps/library/schema.py` `9682db07a0054937c80900d20519265b87121606`;
`apps/library/models.py` `b980e82c5e5a73690a18befd1eb5c7db1cf05691`;
`apps/scalars/models.py` `6f65052e83c0aab1af268784e45bd50bf3a37905`;
`strategy_schemas.py` `a66200fb22f9441269bd4b44b9c3162408a73893`;
`tests/test_connection.py`
`8e08b23fbf7eee84a94ab406d8713855056087a1`;
`tests/optimizer/test_extension.py`
`8b3e2e1c5f940803cd283a7a0683eb318929446c`;
`tests/utils/test_querysets.py`
`77d45a48a8cfa84d25ab383d03b5ac8a60fc4311`;
`tests/filters/test_sets.py`
`ea6d0b04d9a82214d6bbe45778bb93de1dc1121e`;
`tests/orders/test_sets.py`
`d66b482dc65dec478e6941f9c59043698da7dfdd`;
`tests/base/test_init.py`
`239648ed635fa67baa10bf5bd428cd127098088b`;
`docs/SPECS/spec-034-permissions-0_0_10.md`
`788245cbf8ee394a661fb4c23ef8f818046a0bfc`;
`docs/SPECS/spec-045-visibility_boundary-0_0_14.md`
`97561f2dc5f6286c88b5a2b742211d01b950804c`;
`docs/GLOSSARY.md` `3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`;
`docs/README.md` `30978c34f63a833ffcc0fa11c80b773d241921be`;
`test_products_api.py` `fe78cf9d4862123442611444d44bf81b5187ec6d`;
`test_products_visibility_api.py`
`318bc95ebb66e9e0c76f04c4ce042ee2ef133aec`;
`test_library_inheritance_api.py`
`cafc97f81081ea19537ab5dd15dfd01cc235a575`;
`test_list_field_api.py`
`4c85f77971fcf352b7c8eb0c46cd2268184a0b4a`;
`test_keyset_api.py` `88a432b0858c54afc91a79cedbf8938983ab2c23`;
`rev-permissions.performance.md`
`677ba79454f6366df1d6e72b89b9771955b7d7ab`;
`rev-permissions.mechanics.md`
`03ef2500fc2d15e60a880f44855847c46a0465fc`.

## Findings

### High

None.

### Medium

#### M1: the "every products type declares a custom get_queryset" census is false — ItemHoldType is identity

- Observation: two docstrings state every (shipped) products type
  declares a custom `get_queryset`. `ItemHoldType`
  (`examples/fakeshop/apps/products/schema.py:221`, identity default,
  no hook) falsifies the census. The homing conclusions still hold
  (no cascading edge targets `ItemHold`, so no live request composes
  identity-hook subqueries), but the stated reason is wrong, and
  DRY principle 10 puts a wrong stated reason below none.
- Evidence: the five products type declarations (hooks on
  Category/Item/Property/Entry, none on `ItemHoldType`); `ItemHold`
  carries two forward FKs to `Item` yet no model holds an FK *to*
  `ItemHold` (grep clean), and holds are payload-only ("Not a root
  connection"); the Query docstring's own "four types" vocabulary
  for the roots.
- Impact: a maintainer checking the census finds the fifth type
  hook-free and cannot tell whether the package-only homing (module
  docstring) or the "no live two-identity-target root" claim (test
  docstring) survived it.
- Severity: Medium (stale census on internal prose; wrong stated
  reason for two homing claims).
- Recommendation: scope both sentences to the four root types and
  name the exception; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'declares a custom' tests/test_permissions.py`
  prints `0` (2 today); both rewritten sentences grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_permissions.py` module docstring +
  `tests/test_permissions.py::test_identity_hook_targets_compose_default_manager`.
- Grade: stale.
- Text-before:
  `identity-hook default-manager composition over products types`
  `(every products type declares a custom ``get_queryset``)`
  and
  `Every shipped products type declares a custom ``get_queryset``,`
  `so no live products request carries two identity-hook targets on`
  `one root;`
- Text-after:
  `identity-hook default-manager composition over products types`
  `(the four root products types declare custom ``get_queryset```
  `hooks; ``ItemHoldType`` is identity but no cascading edge targets`
  `it)`
  and
  `The four root products types declare custom ``get_queryset```
  `hooks, so no live products request carries two identity-hook`
  `targets on one root (``ItemHoldType`` is identity but no cascading`
  `edge targets it);`

#### M2: "seen-set" misnames the ContextVar mechanism — upstream vocabulary for a replaced design

- Observation: the `aapply` off-loop test calls the traversal state
  a "seen-set" (docstring + comment). No set exists anywhere on this
  path: the var holds an immutable `_TraversalState`
  (`alias`/`active`/`path`), never added to, only replaced. The word
  is upstream `django-graphene-filters` vocabulary
  (`_cascade_seen: ContextVar[set]`, "Cycle detection via context-var
  seen set"), left behind when the package replaced the mutable set
  with the frozen state object.
- Evidence: `grep -n 'seen'` over the target prints nothing (the two
  test lines are the only hits in either graded file);
  `_TraversalState` + every install site (`dataclasses.replace` +
  token `set`/`reset`); upstream `permissions.py:16,60-69`.
- Impact: a reader hunting the "seen-set" finds no symbol, no set,
  and no `seen` identifier; the leak property the test pins reads
  as attached to a mechanism that does not exist.
- Severity: Medium (stale mechanism name on internal prose).
- Recommendation: call it what the code holds — traversal state;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'seen-set' tests/test_permissions.py` prints `0`
  (2 today); both rewritten lines grade true.
- Freshness: none beyond Trace.
- Symbol:
  `tests/test_permissions.py::test_aapply_runs_walk_off_event_loop`.
- Grade: stale.
- Text-before:
  `Assert the walk executes and the ``ContextVar`` seen-set installed`
  `inside the worker ...`
  and
  `# ...and the worker-thread seen-set did NOT leak back into the`
  `awaiting task.`
- Text-after:
  `Assert the walk executes and the ``ContextVar`` traversal state`
  `installed inside the worker ...`
  and
  `# ...and the worker-thread traversal state did NOT leak back into`
  `the awaiting task.`

#### M3: the OrderSet-mirror docstring claims this file's fixtures do not clear caches they do clear

- Observation: `_StaffOnlyCategoryOrder` justifies its
  `_normalize_input` override as avoiding the input class "whose
  module-global `_field_specs` / factory caches this file's autouse
  fixtures do not clear". They do: this file's `_isolate_registry`
  calls `registry.clear()`, which replays every subsystem clear
  including `orders.input_namespace`, whose documented coverage is
  exactly the ledger, `_field_specs`, the `OrderArgumentsFactory`
  caches, and the binding attrs. The override stands; its stated
  reason contradicts the body (DRY principle 10).
- Evidence: `tests/test_permissions.py:111-116` (`registry.clear()`
  on entry and exit); `registry.py::TypeRegistry.clear` replaying
  `iter_subsystem_clears()` (default replays all rows);
  `orders/inputs.py::clear_order_input_namespace` docstring (ledger,
  `_field_specs`, factory caches) + its `register_subsystem_clear`
  row; `orders/__init__.py` importing `.inputs`/`.sets`, so the row
  is registered in any process importing `orders` (this file does,
  line 93).
- Impact: a reader takes the override for cache-hygiene load-bearing
  and will preserve or extend the workaround for a leak that cannot
  happen; the real reason (deterministic `order_by` without standing
  up the input class) is already in the sentence.
- Severity: Medium (false stated reason on internal prose).
- Recommendation: delete the false parenthetical, keep the rest;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c 'autouse fixtures do not clear'
  tests/test_permissions.py` prints `0` (1 today); the rewritten
  docstring grades true.
- Freshness: none beyond Trace.
- Symbol:
  `tests/test_permissions.py::_StaffOnlyCategoryOrder`.
- Grade: stale.
- Text-before:
  `so the apply pipeline produces a deterministic ``order_by```
  `without standing up the ``OrderArgumentsFactory`` input class`
  `(whose module-global ``_field_specs`` / factory caches this file's`
  `autouse fixtures do not clear). The gate's active-input walk ...`
- Text-after:
  `so the apply pipeline produces a deterministic ``order_by```
  `without standing up the ``OrderArgumentsFactory`` input class.`
  `The gate's active-input walk ...`

### Low

#### L1: eight bare Decision numerals in the target name no spec

- Observation: the target cites `(Decision 5 step 1)`, `(Decision
  5)`, `(Decision 7)`, `(Decision 9)` x2, `(Decision 10)` x3 and
  never names spec-034 anywhere in the file, so no anchor sits on
  the reader's path (the connection-R5 exemption fails on its own
  trigger). The numerals are all correct (subjects verified against
  spec-034), but a second same-numeral Decision governs this file's
  neighborhood — spec-045 Decision 5, the visibility boundary whose
  seals the file imports — which is exactly the list_field-M2
  ambiguity trigger.
- Evidence: `grep -c spec-034` over the target prints `0`;
  spec-034 Decision 5/7/9/10 titles match the cited subjects (D5
  "step 1" is the spec's own phrasing); spec-045 Decision 5
  ("Queryset-shape rejections") shares the numeral with the D5
  sites.
- Impact: bounded clarity; a maintainer cannot resolve which spec
  any numeral means without searching, and the D5 sites have a
  plausible wrong answer one import away.
- Severity: Low (ambiguous pointer, correct number).
- Recommendation: anchor all eight to `spec-034`; see text-after.
- Must not change: n/a.
- Proof: `grep -c '(Decision [0-9]'
  django_strawberry_framework/permissions.py` prints `0` (8 today);
  the rewritten parentheticals grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/permissions.py` (import
  comment + `_cascadable_edge_names`, `_validate_fields`,
  `apply_cascade_permissions` x3, `aapply_cascade_permissions`
  docstrings).
- Grade: ambiguous pointer (bare spec-Decision numeral).
- Text-before:
  `(Decision 10)` (import comment), `(Decision 5 step 1)`,
  `(Decision 9)`, `(Decision 5)`, `(Decision 7)`, `(Decision 9)`,
  `(Decision 10)`, `(Decision 10)`
- Text-after:
  `(spec-034 Decision 10)`, `(spec-034 Decision 5 step 1)`,
  `(spec-034 Decision 9)`, `(spec-034 Decision 5)`,
  `(spec-034 Decision 7)`, `(spec-034 Decision 9)`,
  `(spec-034 Decision 10)`, `(spec-034 Decision 10)` — same sites,
  same order.

#### L2: the async twin's first line describes instead of commanding

- Observation: `aapply_cascade_permissions` opens "Async twin of
  ..." — a description where the axis rule (reviewer is the gate;
  D401 unchecked) requires the imperative for a function. Every
  other function/method first line in the target is imperative.
- Evidence: first-line census over the target's 13
  function/method docstrings: 12 imperative, this one descriptive;
  the body paragraphs already carry the twin relationship, so
  nothing is lost.
- Impact: bounded; the one public docstring a consumer reads that
  breaks the file's own mood.
- Severity: Low.
- Recommendation: open with the imperative; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Async twin of'
  django_strawberry_framework/permissions.py` prints `0` (1 today);
  the rewritten first line is imperative and grades true.
- Freshness: none beyond Trace.
- Symbol:
  `django_strawberry_framework/permissions.py::aapply_cascade_permissions`.
- Grade: duplicates the convention it breaks (non-imperative
  function first line).
- Text-before:
  `"""Async twin of ``apply_cascade_permissions`` -- the same walk,`
  `off the event loop.`
- Text-after:
  `"""Run the ``apply_cascade_permissions`` walk off the event loop.`

#### L3: four test-helper first lines describe instead of commanding

- Observation: `_cascade_only`, `_exclude_private`, `_gate_info`,
  and the `_assert_contextvar_clean` fixture open with
  descriptions. The file's own helper convention is imperative
  (9 imperative vs these 4), so the connection-R1
  consistency exemption does not apply — rewriting moves with the
  majority, not against it.
- Evidence: helper-mood census over the own test module (each
  first line read): imperative `_isolate_registry`, `_tables`,
  `_make_type`, `_cascading_hook`, `_gfk_host_with_content_type_hook`,
  `_register_ct_pair`, `_profiles_by_genre`, `_specimen`,
  `_anonymous_narrowed_categories`; descriptive the four sites.
- Impact: bounded clarity; four first lines misstate the file's
  contract for helpers.
- Severity: Low.
- Recommendation: re-mood each to the imperative; see text-after.
- Must not change: n/a.
- Proof: `grep -c -e 'A hook that cascades and nothing else' -e
  'The recurring cascading hook' -e 'shaped stub carrying' -e 'must
  be reset to' tests/test_permissions.py` prints `0` (4 today, one
  per site); all four rewritten first lines grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_permissions.py::_cascade_only`,
  `::_exclude_private`, `::_gate_info`,
  `::_assert_contextvar_clean`.
- Grade: non-imperative function first line (x4).
- Text-before:
  `A hook that cascades and nothing else - the pure re-entrant`
  `shape.` /
  `The recurring cascading hook: row-narrow ``is_private=False```
  `then cascade.` /
  ```info``-shaped stub carrying ``info.context.request`` with a`
  ```user``.` /
  `The traversal-state var must be reset to ``None`` after every`
  `test.`
- Text-after:
  `Cascade and nothing else - the pure re-entrant hook shape.` /
  `Row-narrow ``is_private=False``, then cascade.` /
  `Build an ``info``-shaped stub carrying`
  ```info.context.request`` with a ``user``.` /
  `Assert the traversal-state var reset to ``None`` after every`
  `test.`

#### L4: `_cascade_only` carries its own dedup history

- Observation: "...each used to define a local copy of this exact
  body" narrates the test file's own editing (a dedup), not
  behavior. Pure process provenance: no invariant, leak shape, or
  design rationale a reader can use — the surviving sentence
  already states the sharing.
- Evidence: the sentence's subject is prior file content ("a local
  copy"), unverifiable from any contract source and load-bearing
  for nothing the helper does.
- Impact: bounded; history where the file's convention states
  sharing.
- Severity: Low.
- Recommendation: delete the sentence; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'used to define a local copy'
  tests/test_permissions.py` prints `0` (1 today); the trimmed
  docstring grades true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_permissions.py::_cascade_only`.
- Grade: process provenance.
- Text-before:
  `Shared by the cycle fixtures (ring / diamond / self) and the`
  `transitive-chain tests; each used to define a local copy of this`
  `exact body.`
- Text-after:
  `Shared by the cycle fixtures (ring / diamond / self) and the`
  `transitive-chain tests.`

## Rejected

- R1 — Temporal language serving a present fact (connection-R3
  precedent, no process artifact named): target "can no longer
  compare the wrong column" (the guarantee), "the boundary now
  returns a SEALED queryset" (why `.values` is genuine); tests
  "now contributes a subquery", "can no longer compare" / "no
  longer raises" / "no longer trips", "no longer in this battery"
  (battery scope + the coercion-test pointer), "survives the move"
  (why the seam prose stays path-rich). Trigger: a rewrite to pure
  present tense.
- R2 — History serving a present design fact (connection-R4
  precedent), every claim verified rather than trusted: the
  previous un-narrowed re-entry (spec-034 "raises instead of
  returning an un-narrowed queryset"); the identity-hook skip
  (`3131a2fe:21`); the parent-link exclusion (spec-034's
  `related_model`-pair tightening); the straight-into-`__in`
  `.values` passthrough (`3131a2fe:227`, no re-projection); the
  Manager rejection (coercion arrives in `1dd9273a`); the
  cascade's own slice checks at both entry points (`c68aecab:322`
  + per-edge prose, backing `test_querysets.py:5025`); the
  pre-string-check `set([1])` diff (mechanically derivable from
  the validator); the `require_model_rows=False` slice licence
  (`_SealPolicy` field split). Trigger: the design changing under
  any of them.
- R3 — Bare numerals WITH the anchor on the reader's path
  (connection-R5): own-tests `(Decision 10)` (spec-034 named in
  the two docstrings directly above); `test_connection.py`
  "Decision 12 / DoD item 9" (spec-034 section banner);
  `test_extension.py` "(Decision 7 / Goal 3)" (spec-034 banner;
  Goal 3 is the spec's N+1-safe goal, matching the section);
  own-tests "(Edge cases)" (spec-034 carries the section and is
  named throughout the file). Trigger: an anchor removed or a
  second same-named Decision.
- R4 — `(spec-036)` attributive in the own-tests module docstring
  (the mutation pin's home spec) with the exact live test-name
  locator beside it — attribution plus locator, not a bare tag.
  Trigger: none (pointer + locator both present).
- R5 — `(the get_queryset-visibility-boundary decision)` topic
  parenthetical (Manager-coercion test): no Decision number, so it
  cannot misdirect to a wrong one, and the behavior it attributes
  is verified true in `_normalized_visibility_result` plus the
  test's own assertion. Trigger: a rewrite naming the decision
  number.
- R6 — Other-module prose about the target's symbols, all read,
  all true, no `Routed:` lead: `test_connection.py` (module
  homing list; the 1153 live pin, exists; the 2130-2219 section —
  products declare no `Meta.connection` opt-in per the Query
  docstring's deferral, `allLibraryIssuesConnection` + totalCount
  live in `test_keyset_api.py`); `test_extension.py` 4989-5110
  (optimizer-mechanism claims belong to the walker/extension
  items; every cascade claim true); `test_querysets.py:1527`
  ("already rejects", pinned by the battery) and 5025-5027
  (verified via `c68aecab`); `filters/test_sets.py:5968`
  (`base_queryset` is exactly the spelled construction);
  `base/test_init.py` (export names, no prose);
  `mutations/permissions.py:5` (true contrast, no lead);
  `docs/README.md:393` (true on every clause); the GLOSSARY
  `apply_cascade_permissions` anchor (true; its `distinct(...)`
  omission is already routed by Mechanics R15, not duplicated
  here). Trigger: the named source changing.
- R7 — `_cascadable_edges` docstring duplicates its body
  ("Return ... (the cached plan's tuple)" vs `return
  _edge_plan(model).cascadable`) — WITHDRAWN as a finding. The
  helpers are production-dead and owned by TODO-ALPHA-053 with
  undecided paths including keep-as-documented-test-seams
  (Mechanics R1, re-read and concurred): deleting the docstring
  churns against the delete path, and the keep path owes seam
  rationale, not deletion. Trigger: the card decides keep (then
  the docstring owes the seam rationale) or delete (then it goes
  with the functions).
- R8 — One-line private factories without docstrings (the
  `_root_*` / `_hook_*` / `_values_*` shapers): no looks-for entry
  requires them (connection-R11 precedent). Trigger: none.
- R9 — "worker" hits are the `sync_to_async` worker thread
  (technical term, verified against asgiref), never review-worker
  attribution; "round-trips" matched the `round` pattern only.
  Trigger: none.
- R10 — Remaining looks-for discharges: module first lines pass
  `build_tree_md.py` on both files; class moods descriptive;
  test docstrings state behavior (no "Tests that"/"Ensures"); no
  `we`/`you`/`I`; no line-number citations; citations resolve
  (5/0 target, 23/0 tests); public symbols all documented; the one
  intentional duplication (`_exclude_private` re-declared locally)
  carries its reason at the site, and no unrecorded separation was
  found. Trigger: none.

Handoff: Read beyond the record's trace: the `orders/sets.py`
`_normalize_input` purity contract + `_prepare_permission_input`
(the M3 neighborhood), `filters/sets.py` python-attr plumbing,
`tests/orders/test_sets.py:360` (the orders-side clearing fixture
M3's prose claims this file lacks), `tests/test_list_field.py` /
`test_relay_node_field.py` / `test_relay_connection.py` (absence
of cascade pins, discharging the gate-banner's "own files"
parenthetical toward the live tier, where both pins exist), the
`ItemHold` model + `ItemHoldType` (M1), upstream
`django-graphene-filters` `_cascade_seen` (M2's origin), and
`git show 3131a2fe / c68aecab / 1dd9273a` for the R2 history
proofs. Conclusions the findings do not state: the target's
contract prose is otherwise in unusually good shape — every
verifiable behavioral claim in the module docstring, the seal
comments, and the error-renderer docstrings held against the
boundary bodies, and the history asides are all true (R2), so the
file's reputation for accuracy is earned; the three Mediums are
all test-prose staleness (a new fifth products type, upstream
vocabulary, a registry-clear row the prose predates), i.e. drift
from surrounding evolution, not authoring error. Open threads for
Worker-0/verifier: (1) no `Routed:` lead — every other package
module's cascade prose grades true, and the one glossary gap
(`distinct(...)`) is already routed by Mechanics R15; do not
re-route it. (2) L1-L2 sit in the target, which no higher finding
touches — disposition per the Low-riding rule is Worker-0's, but
the Proofs are written so a prose-only pass can land them with a
`--code-digest` identity. (3) Performance F1/F2 rewrite `_walk`'s
filter grouping and the renderer factories' construction timing;
neither shape is described by any graded docstring (verified:
`_walk` says "composes the per-edge subqueries", the renderers
describe arms, not evaluation timing), so no finding here is
disturbed — the Comments verifier re-grades the final text
regardless, last, per the flow. (4) If TODO-ALPHA-053 closes
keep-path on the dead edge helpers while this item is still open,
R7 reopens as the seam-rationale docstring it names.

## Verify comments

Pass 1 over Implement pass 1 (`docs/review/temp-tests/permissions/diff/pass-1.diff`,
read whole; live files match its post-images: target `6c97d887`,
tests `c113d05e`). Static verification in the shared tree — no
workspace run: nothing graded imports the package or opens a
database, same as the review. Prose diff re-read via
`review_changed_python_diffs_against_head.py ITEM_BASELINE
--against worktree --prose` under
`docs/review/temp-tests/permissions/verify-comments-1/diff/`.

Per-finding verdicts (Proof = the record's command, re-run live):

- M1: pass. `grep -c 'declares a custom'
  tests/test_permissions.py` prints `0` (was 2). Census
  re-derived, not trusted: five products types, hooks on the four
  roots (`apps/products/schema.py:90,130,168,205`), `ItemHoldType`
  (`schema.py:221`) hook-free; `ItemHold` carries two forward FKs
  to `Item` and no model anywhere in `examples/` or `tests/` holds
  an FK to `ItemHold` (grep clean), so "no cascading edge targets
  it" holds; the "four root" vocabulary matches the Query
  docstring ("The four types", `schema.py:254`) and
  `ItemHoldType`'s own "Not a root connection". Both rewritten
  sentences match Text-after word-for-word and grade true.
- M2: pass. `grep -c 'seen-set' tests/test_permissions.py`
  prints `0` (was 2); `grep -n 'seen'` over both graded files
  prints nothing. Both lines now read "traversal state" and grade
  true: the var holds an immutable `_TraversalState` installed
  inside the worker via asgiref `copy_context`, and the test
  asserts `_cascade_state.get() is None` after the await.
- M3: pass. `grep -c 'autouse fixtures do not clear'
  tests/test_permissions.py` prints `0` (was 1). The false
  parenthetical is deleted; the remainder ("deterministic
  `order_by` without standing up the `OrderArgumentsFactory`
  input class") reads coherently and grades true.
- L1: pass. `grep -c '(Decision [0-9]'
  django_strawberry_framework/permissions.py` prints `0` (was 8);
  `grep -c '(spec-034 Decision'` prints `8`, same sites in the
  same order as Text-after (import comment D10;
  `_cascadable_edge_names` D5-step-1; `_validate_fields` D9;
  `apply_cascade_permissions` D5/D7/D9/D10;
  `aapply_cascade_permissions` D10). All eight grade true.
- L2: pass. `grep -c 'Async twin of'
  django_strawberry_framework/permissions.py` prints `0` (was 1).
  First line is now `Run the ... walk off the event loop.`
  (target line 728): imperative, true, and the twin relationship
  survives in the body ("Wraps the single sync walk ...").
- L3: pass on the text; the record's Proof line is defective (see
  below). Per-pattern counts: `A hook that cascades and nothing
  else` 0, `The recurring cascading hook` 0, `shaped stub
  carrying` 1, `must be reset to` 0 — so the combined Proof prints
  `1`, not `0`. The `1` is `Build an ...-shaped stub carrying`
  (tests line 1990), which the record's own Text-after prescribes:
  the third disjunct matches Text-after verbatim, so the Proof as
  written cannot print `0` on the prescribed text. Corrected
  proof: the old single-line `...-shaped stub carrying
  ... with a ... .` form prints `0`, the new `Build an ...`
  line prints `1`, and each of the other three old/new pairs
  prints `0`/`1`. All four rewritten first lines (`Cascade ...`,
  `Row-narrow ...`, `Build an ...`, `Assert ...`) are imperative
  and grade true.
- L4: pass. `grep -c 'used to define a local copy'
  tests/test_permissions.py` prints `0` (was 1). The trimmed
  `_cascade_only` docstring states only the sharing and grades
  true; no provenance remains.

F1/F2 disturbance: none. `_walk`'s docstring ("composes the
per-edge subqueries") and `apply_cascade_permissions`' ("pure
`.filter(...)` composition") say nothing about call count and stay
true; both renderer docstrings describe arms, not evaluation
timing, and stay true; the moved `name`/`edge` lines are verbatim
except indent (pass-1.diff). New prose the diff wrote grades true
as well: the `_walk` "One `.filter` call" comment (matches the F1
shape); `_count_filter_calls` ("Yield ...", imperative, true);
`test_two_edge_cascade_issues_a_single_filter_call` (Entry = 2
edges, pins 1 call + 2 `IN (SELECT`; SQL-identity pointer to the
existing test is real); `test_zero_edge_root_issues_no_filter_call`
(`Category` verified FK-free: Text/Boolean/DateTime fields only);
`test_error_renderers_build_without_naming_calls` (both factories
built under a raising `truth.name`, by reading).

Inverse proof (both files carry F1/F2 code, so live is compared
against a reconstruction = live minus only the seven findings'
prose, under `docs/review/temp-tests/permissions/verify-comments-1/`):

- Control `review_inspect.py --code-digest
  ITEM_BASELINE:<path> <path>`: exit 1 on both files (target
  `28cde43e...` vs `b7a57675...`; tests `31e0f802...` vs
  `19980ef0...`) — the instrument sees the F1/F2 code movement.
- Inverse `--code-digest <recon> <live>`: exit 0 on both files,
  digests equal (`b7a57675...`, `19980ef0...`) — every remaining
  diff is prose-only. The stripped-source diffs show exactly the
  F1/F2 code (conditions accumulation + guarded single `.filter`;
  `name`/`edge` moved into `_render`; the four pin blocks +
  imports) plus whitespace alignment.

Citations: `check_citations.py --paths <file> --substrings --json`
prints `checked 5, violations 0` (target) and `checked 23,
violations 0` (tests) — identical to the review baseline; the
prose moved no citation. `build_tree_md.py --list-docstrings` on
both files: 2 modules, 0 breaking. Voice (`we`/`you`/`I`),
`Tests that`/`Ensures` openers, and `.py:NN` sweeps: clean.
Provenance-pattern hits are all the record's graded keeps
(R1/R2/R4/R9) plus the L1 anchors; zero hits inside the new-code
ranges.

Status: verified

Open threads: (1) L3's Proof line needs a record correction (the
`shaped stub carrying` disjunct contradicts Text-after); no code
or prose revision is owed — Worker-2 implemented Text-after
exactly. No other thread: no `Routed:` lead, no new prose defect,
no disturbed docstring.

Handoff: Read beyond the verdict's trace: the full pass-1.diff,
both live files' final docstrings, `apps/products/schema.py`
(types + hooks + Query vocabulary), `apps/products/models.py`
(`ItemHold`, `Category`), and the prose/stripped diffs. Method
note for the next reader: `rg` is not installed in this
environment; all sweeps above ran under `grep`. The L3 Proof
defect is a record wording bug, not an implementation gap — do not
re-open the item for it.