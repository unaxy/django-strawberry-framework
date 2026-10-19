# Review · Mechanics: `django_strawberry_framework/sets_mixins.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=569603863d594f6296d1c27cd8d0a2e6f2f4b3a5

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for
this target and no Routed lead on this item),
`docs/review/rev-sets_mixins.md` (skeleton: `Status: reviewing`,
blank Path class). Sibling axis records:
`rev-sets_mixins.performance.md`, `rev-sets_mixins.mechanics.md`,
`rev-sets_mixins.comments.md` — none existed at close (siblings run
concurrently); no foreign Handoff or `## Cross-axis (for Mechanics)`
owed. `rev-sets_mixins.md` carries no Worker-2 sections yet.

Target read whole, all 779 lines, as it stands: blob
`088ddab0c0f68c0605bc4a440dfa3daa544452dd`. Dirty vs HEAD
(`+45/-34`, concurrent work) — reviewed as it stands per the
dispatch, no hunk attributed here.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/sets_mixins/mechanics/inspect/` (json
`docs/review/temp-tests/sets_mixins/mechanics/sets_mixins.json`):
30 symbols, 0 Django/ORM markers, 2 hot entry points
(`resolve_lazy_class` by name, `_request_from_info` by `info`
parameter), 0 import-time work. Leads only.

Contracts traced by hand: `docs/README.md` (error policy:
`ConfigurationError` for declaration/construction-time consumer
misconfiguration; mutation envelope — no mutations in target),
`docs/GLOSSARY.md` (no anchor names any target symbol),
`GOAL.md` "Trust boundary", spec-028 ship contract
(`docs/SPECS/spec-028-orders-0_0_8.md`, gate-surface enumeration),
both consumer families (`filters/sets.py`, `orders/sets.py`,
`filters/base.py`, `orders/base.py`, both `inputs.py`), the
mechanics owners (`utils/permissions.py`, `utils/input_values.py`,
`utils/inputs.py`, `utils/strings.py`), the finalize audit
(`types/finalizer.py::_bind_filterset_owner`), the package root
`__init__.py` (no `sets_mixins` re-export), and the test tiers
(`tests/test_sets_mixins.py`, `tests/filters/test_sets.py`,
`tests/orders/test_sets.py`, `tests/orders/test_base.py`,
`tests/orders/test_composition.py`, `tests/utils/test_permissions.py`).

Looks-for sweep, entries with no finding (reason each):

- Rule enforced at caller instead of owner: none. The target-type
  gate fires inside `RelatedSetTargetMixin._resolved_target`, the one
  seam every consumer routes through; the re-readability check is
  single-sited in `require_re_readable_field_declaration` with the
  call placed at each family's own consumption gate (filter
  `get_fields`, order `_expand_meta_fields`), whose timings
  legitimately differ; the logic-depth cap lives on `FilterSet`
  (owner of the logic grammar) and the related-branch cap in the
  shared core.
- Policy in adapter / mechanism in policy layer: none. The mixin
  delegates all permission mechanics to `utils/permissions.py`; its
  `_run_permission_checks` prologue only orchestrates the
  family hooks (`_prepare_permission_input`,
  `_check_permission_depth`, `_run_logic_permission_checks`) around
  the shared core — the split `utils/permissions.py` documents
  ("The family wrappers own the prologue").
- Contract sources deciding differently from the body: none. All
  declaration-error raises are `ConfigurationError`, matching the
  README error policy; no GLOSSARY anchor or README passage names a
  target symbol, so nothing contradicts.
- `django.conf.settings` read at import: none. The module imports
  only `django.utils.module_loading.import_string` (no settings
  read) plus stdlib, `.exceptions`, and `.utils.*`.
- Dependency pointing the wrong way: none. Package root imports
  downward into `utils/*` only; no `utils/` module imports
  `sets_mixins` at runtime (the `binding_attrs` read in
  `utils/inputs.py::clear_generated_input_namespace` is duck-typed
  via `getattr`); no `TYPE_CHECKING` block, no cycle. The neutral
  home is pinned by
  `tests/orders/test_base.py::test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base`.
- Sync/async twins drifted: none — no twin exists. Both families
  call the sync `_run_permission_checks`; the order async path wraps
  it in `run_in_one_sync_boundary` (`orders/sets.py`), so there is
  one implementation, not two.
- Duplication (DRY change challenge): none. `type_name_for` and
  `filters/inputs.py::_pascal_case` share one core
  (`utils/strings.pascal_case_or_raise`); posit a token-rule change
  and exactly one definition moves. The `_validate_target` twins
  are different rules (FilterSet-membership vs OrderSet-membership)
  behind one seam — one authoritative definition per family (R5).
  The `get_filters` / `get_fields` builds are family expansions
  over the shared `expanded_once` + `should_cache_expansion`
  skeleton. The depth-cap vocabularies are already unified via
  `utils/input_values.py::raise_set_traversal_depth_exceeded`.

Cells: default only; sharded and pg are inapplicable by
construction — the target reaches no database, alias, or dialect
decision (pure Python plus `import_string`).

Fingerprints (`git hash-object`) of everything inspected:

- `django_strawberry_framework/sets_mixins.py` 088ddab0c0f68c0605bc4a440dfa3daa544452dd
- `django_strawberry_framework/filters/sets.py` e47c6758e540e0bd9caa8cb90103263b26e905e1
- `django_strawberry_framework/orders/sets.py` 60859f2d54525acfdb3dc997d3e931ff3d58d956
- `django_strawberry_framework/filters/base.py` 3b1dcbced1069e0faf1abeb33661e94a296f94ba
- `django_strawberry_framework/orders/base.py` 7616b27986e7794500c2b0fac97b104325fe0f12
- `django_strawberry_framework/filters/inputs.py` a932dbf85d89791280774b0600a40b5fb43b89e4
- `django_strawberry_framework/orders/inputs.py` 2d258da74ee36f5d851ffa6550462b0fd65bd460
- `django_strawberry_framework/filters/__init__.py` 86b258186638c96995e31919346f44d7951c65ea
- `django_strawberry_framework/orders/__init__.py` ed546f9c70d56d73e0d84a029e9e04f27da3934b
- `django_strawberry_framework/utils/permissions.py` 1c9cfd398e6096e03bda82ba93dfd66a6d2fb890
- `django_strawberry_framework/utils/input_values.py` 18992b79cfd02ea778156800b88c924e8c50fa3b
- `django_strawberry_framework/utils/inputs.py` b5af8255dfa18a2ff423cdd2de211723c5a15590
- `django_strawberry_framework/utils/strings.py` 5a4f481132f87cc83abeb2a4a4a679990fa5b9bc
- `django_strawberry_framework/types/finalizer.py` b9d8acb2b9428cc8297550414ff86bdd98e0d1a7
- `django_strawberry_framework/__init__.py` 0ef72601ecac300ac87ff993af1b04a4f1bc335a
- `tests/test_sets_mixins.py` 23946eb5c62ba1def9bf040f1c0df70c08959d3b
- `tests/filters/test_sets.py` ea6d0b04d9a82214d6bbe45778bb93de1dc1121e
- `tests/orders/test_sets.py` d66b482dc65dec478e6941f9c59043698da7dfdd
- `tests/orders/test_base.py` 16ec82844441cbb68e789e8eba6dc2d4c0405645
- `tests/orders/test_composition.py` 9414d257f1d113188e78526a8681643dacc10da4
- `tests/utils/test_permissions.py` 71e1ff4bbe4707735c0a10ebfcda1de62f92c9a1
- `docs/README.md` 30978c34f63a833ffcc0fa11c80b773d241921be
- `docs/GLOSSARY.md` 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd
- `docs/SPECS/spec-028-orders-0_0_8.md` 94a3141c02b92265779d8f3f7a2eefc019f765d8

## Findings

### High

None.

### Medium

None.

### Low

#### F1: `__all__` omits three public names, two with production importers

- Observation: `django_strawberry_framework/sets_mixins.py::__all__`
  names 9 symbols but omits three module-defined public names:
  `require_re_readable_field_declaration` (imported by both
  production families, `filters/sets.py` and `orders/sets.py`),
  `is_re_readable_field_declaration`, and
  `RE_READABLE_FIELDS_HELP` (both imported by
  `tests/test_sets_mixins.py` for direct pins).
- Evidence: the module docstring presents
  `require_re_readable_field_declaration` as shipped set-family
  substrate; `filters/sets.py` and `orders/sets.py` import it at
  module top; `tests/test_sets_mixins.py` imports all three
  directly. The completeness test
  `tests/test_sets_mixins.py::test_sets_mixins_all_exports_are_complete`
  claims "`__all__` names every public symbol" in its docstring but
  only asserts one membership plus existence of listed entries, so
  the omission passes. Convention control: sibling
  `django_strawberry_framework/utils/permissions.py::__all__` names
  every public function it defines. Static only; no workspace run
  (nothing imported, measured, or opened a database).
- Impact: `from sets_mixins import *` silently drops the
  re-readability gate both families run, its predicate, and the
  shared message contract; anyone auditing the public surface via
  `__all__` misses them.
- Severity: Low (bounded clarity/maintainability).
- Recommendation: owner is
  `django_strawberry_framework/sets_mixins.py::__all__` (same
  file): add the three names in the existing ASCII-alphabetical
  order (`RE_READABLE_FIELDS_HELP` between `RelatedSetTargetMixin`
  and `SetLifecycleAttrs`; `is_re_readable_field_declaration` and
  `require_re_readable_field_declaration` between `expanded_once`
  and `should_cache_expansion`). Strengthen
  `tests/test_sets_mixins.py::test_sets_mixins_all_exports_are_complete`
  to pin completeness (every module-defined public symbol is in
  `__all__`), so the docstring claim holds. No symbol moves or
  renames; `check_citations.py --cited-by` on
  `require_re_readable_field_declaration` shows 2 gated citers
  (`filters/sets.py:1480`, `orders/sets.py:507`), both resolving,
  none needing edits for an `__all__` addition.
- Must not change: every import spelling in the two families and
  the tests keeps working; `import *` gains exactly the three
  names and nothing else.
- Proof:
  `uv run python scripts/workspace.py run review/sets_mixins.py/verify-mechanics-<n> -- python -c "from django_strawberry_framework import sets_mixins as sm; missing = [n for n in ('RE_READABLE_FIELDS_HELP', 'is_re_readable_field_declaration', 'require_re_readable_field_declaration') if n not in sm.__all__]; print('missing-from-__all__:', missing); assert not missing"`
  and
  `uv run python scripts/workspace.py run review/sets_mixins.py/verify-mechanics-<n> -- pytest tests/test_sets_mixins.py::test_sets_mixins_all_exports_are_complete --no-cov`
  (`1 passed`; the strengthened test must fail on the pre-fix tree).
- Freshness: no files beyond `## Trace`.

## Rejected

### R1: `_active_permission_field_paths` has no production callers — kept as documented facade surface, not dead code

The leaf-half accessor is called only by tests
(`tests/filters/test_sets.py`,
`tests/orders/test_sets.py:639-693`,
`tests/test_sets_mixins.py:714-719`); the production hot path uses
the single-pass `_active_permission_targets`. Removal was
considered and rejected: spec-028 enumerates the method as part of
"the whole gate surface" both families inherit
(`docs/SPECS/spec-028-orders-0_0_8.md`, Decision 8 step 6), the
single-sourcing pin lists it in `_SHARED_PERMISSION_METHODS`, and
the DRY consolidation deliberately kept the mixin method as the
survivor. Gated citer count is 1
(`utils/permissions.py:437`, docstring, resolving).
Trigger: a spec re-scoping the gate surface off this method — then
retire the method plus its direct pins.

### R2: order-side `_check_permission_depth` / `_run_logic_permission_checks` no-ops — unreachable by grammar, not a missing guard

The order traversal carries empty `logic_keys`
(`SetInputTraversal` default; order `_permission` passes none),
so no input classifies `LOGIC` and the hooks have no caller that
can supply logic input; the related-branch depth both families
share is capped inside `run_active_input_permission_checks` via
`assert_set_traversal_depth`. No contract source asks OrderSet to
cap logic nesting it cannot express.
Trigger: OrderSet gains logic keys — the no-ops become a gate hole
and must gain behavior.

### R3: filter-side `_prepare_permission_input` no-op while order overrides — family lifecycle difference, not a flavor gap

Order field specs build lazily at apply time
(`orders/inputs.py::normalize_input_value` calls
`_ensure_field_specs`), so a direct permission call needs the
hook; filter specs populate at finalize emission
(`filters/inputs.py::_build_input_fields`), and the whole filter
apply pipeline (normalizer included) already requires finalize, so
no contract asks the filter side to self-provision specs on a
direct call.
Trigger: FilterSet supports pre-finalize apply or lazy specs —
then it must override the hook.

### R4: `inherit_from_bases` bool in `collect_related_declarations` — upstream-structural policy selector, not a mode flag for a named adapter

The flag selects only the MRO-merge prelude (django-filter's
metaclass already merged vs plain `type` needing the reversed-base
copy); the tombstone reconciliation and owner bind — the rule —
are shared below it, and both call sites pass constants with the
reason stated. Splitting into named adapters would duplicate the
shared tail to no benefit.
Trigger: a third merge policy, or family-specific rules appearing
inside either branch.

### R5: `RelatedFilter._validate_target` / `RelatedOrder._validate_target` twins — different rules, one seam

Both spell an `issubclass` check plus `ConfigurationError`, but
FilterSet-membership and OrderSet-membership are different rules
with different reasons to change (posit "allow X as a filter
target" — exactly one definition moves). The firing seam is
already single (`_resolved_target`).
Trigger: a shared cross-family acceptance rule.

### R6: `_expanded_filters` / `base_filters` aliasing with asymmetric reset — upstream seam, self-healing

Filter `_build` publishes one dict object to both slots atomically;
`base_filters` is django-filter-owned state the package must keep
correct, `_expanded_filters` the package cache. `registry.clear()`
deletes only the package slot, but the next expansion (which
`finalize_django_types()` performs, per the `expanded_once`
contract) rebuilds and republishes both. No direct `base_filters`
reader between clear and rebuild was found.
Trigger: evidence of such a read — then the family (not this
module's descriptor) owns adding the slot to `extra`.

### R7: order-side expansion guard is write-only — shared-skeleton slot, documented

`OrderSet.get_fields` passes `guard_attr` to `expanded_once` with
`on_reentry=None`, so the guard is set and cleared but never read
on the order path (order expansion never resolves targets, hence
never re-enters). The slot is required by the shared skeleton and
its retention is documented on the family
(`orders/sets.py`, "stays in place for future defensive use").
Trigger: the skeleton splits per family, or a guard read is added.

### R8: filter re-readability gate exempts `str`, order does not — documented contract difference, not a missing guard

Filter `get_fields` skips `require_re_readable_field_declaration`
for string declarations because the top-level `"__all__"`
shorthand IS a string and any other string is upstream's to reject
(`filters/sets.py`); the order family, with no upstream owner,
routes every non-`"__all__"` declaration through the shared gate.
Both spellings are stated at their call sites.
Trigger: a string-shaped `Meta.fields` reaching either family
unvalidated.

Handoff: Beyond the record I read the plan's `## Owned changes`
(no row for this target), the skeleton main artifact, the full
live target, both consumer families' set/base/inputs modules at
the consumption seams, the three `utils/` mechanics owners plus
`utils/strings.py`, the finalizer's owner-bind audit, the package
root exports, and the six test modules listed in Trace. Sibling
axis records did not exist at close, so no cross-axis Proofs are
owed. Judgment calls: F1 is the only finding (Low, `__all__`
completeness plus test strengthening — no defect, no HUNT/DRY
fields owed); the `_active_permission_field_paths` zero-production-caller
observation is rejected per spec-028's gate-surface enumeration
(R1), and the guard/lifecycle asymmetries are rejected with
triggers (R2, R3, R7, R8). No workspace runs were needed — every claim
is static (grep populations plus cited-by checks). Open thread for
Worker-2/verifier: the target and `tests/test_sets_mixins.py` were
dirty with concurrent work at review time; re-fingerprint before
implementing.

## Verify mechanics

Pass 1, address `review/sets_mixins.py/verify-mechanics-1`
(copy slot-4; package digest
`sha256:b09615232d47c288dde033bdab0e9504332ddd3c0388761b776c2039bb811c87`
on every green run; python 3.14.2, django 6.1,
strawberry-graphql 0.324.0, default cell). Live
fingerprints: `sets_mixins.py` 1f8e078d,
`tests/test_sets_mixins.py` 8c1488d7,
`tests/filters/test_inputs.py` 4e280999,
`tests/orders/test_base.py` 00de6531 — each matches
the pass-1 diff's `+++` blob, and
`git diff ITEM_BASELINE -- <4 paths>` is
byte-identical to
`docs/review/temp-tests/sets_mixins/diff/pass-1.diff`,
so the live tree carries the implementation
unclobbered. `tests/filters/test_sets.py` ea6d0b04
matches the review fingerprint (L18 deferred file
untouched).

1. Proof (1) missing-from-`__all__` — pass.
   `review-20260929T140959-aa80fd` prints
   `missing-from-__all__: []`.
2. Proof (2) strengthened completeness node — pass.
   `review-20260929T141006-b5aea9`: `1 passed`.
3. Failability of the strengthened test — pass. The
   three names removed in the copy only (script under
   scratch; shared tree untouched):
   `review-20260929T141545-ef55e7` reports `1 failed`,
   naming exactly `['RE_READABLE_FIELDS_HELP',
   'is_re_readable_field_declaration',
   'require_re_readable_field_declaration']`.
   Copy restored afterwards (byte-identical to the
   shared tree) and the node re-passes at
   `review-20260929T141624-65f255`.
4. M9 closes with text-before true — pass. The
   sentence `names every public symbol` still occurs
   once in `tests/test_sets_mixins.py` with zero diff
   hunk lines touching it, and the tuple is completed
   (checks 1-2). The Comments C1 arm for Mechanics
   also holds: the `sed -n ... | grep -c
   "require_re_readable_field_declaration"` Proof
   prints `1` in the shared tree.
5. Memo introduces no Mechanics defect — pass.
   `review-20260929T141445-2c5155`
   (`probe_memo_mechanics.py`): `__all__` equals the
   exact 12-name tuple in RUF022 isort-style order
   (SCREAMING_SNAKE, then CamelCase, then the rest;
   `ruff check` green) and `import *` carries the
   three; the slot is fresh (0 hits at ITEM_BASELINE,
   2 hits live, both the new seam lines, no other
   package or test hit); neither family's
   `binding_attrs` contains the slot
   (`('_owner_definition', '_expanded_filters',
   '_is_expanding_filters', '_expanded_snapshot')` /
   `('_owner_definition', '_expanded_fields',
   '_is_expanding_fields')`), and the slot lives on
   the related declaration instance, not on any set
   class the reset chain clears; order-side two-reads
   validate once and substitution re-validates, a
   string forward reference resolves once, `None`
   never validates and never memoizes, a hostile
   target raises `ConfigurationError` on every retry
   with no memo set; `deepcopy` of a real
   `RelatedOrder` keeps a valid memo with no
   re-validation. No import hunk in the target diff
   (0 `^[+-](from|import)` lines), so no import or
   cycle change.
6. Pre-fix behavior was the worse one — pass. The
   baseline `_resolved_target` body restored in the
   copy only: `review-20260929T141608-64034c` fails
   the new counting pin with two validations for two
   reads (the F1 re-validation); copy restored after.
7. Own module green — pass.
   `review-20260929T141042-6dc55c`: `34 passed`
   (33 + the new counting pin).
8. Family attack — pass, nothing failing.
   `review-20260929T141812-10079a`:
   `tests/filters/test_sets.py` +
   `tests/orders/test_sets.py` +
   `tests/orders/test_base.py` +
   `tests/filters/test_inputs.py`, `524 passed` —
   the memo changes no verdict on any real-family
   path.
9. R1-R8 stand — pass. Zero added/removed pass-diff
   lines mention any R1-R4/R6/R7 site symbol, and
   `filters/base.py`, `orders/base.py`,
   `filters/sets.py`, `orders/sets.py`,
   `utils/permissions.py` are byte-identical to
   ITEM_BASELINE. R5: the only `_validate_target`
   diff lines are a docstring reword and the new
   pin's local test double; the family twins are
   untouched separate rules, no shared
   cross-family rule introduced. R8: only the three
   `__all__` additions; both families' exemption
   branches untouched. No trigger tripped.
10. `__all__` placement judgment — accepted. The
    record suggested the constant between
    `RelatedSetTargetMixin` and `SetLifecycleAttrs`;
    Worker-2 placed it first, which is the order
    RUF022 enforces (constants first; `ruff check`
    green, and the suggested slot would fail the
    gate). The Proof governs membership only and
    holds; placement is the gate-blessed shape.
11. Lint gates — pass (read-only): `ruff check` and
    `ruff format --check` over all 4 touched paths
    clean; `check_trailing_commas.py --check` 0
    violations; `check_citations.py --check` OK
    (1303 resolve).
12. Cells — default verified (every run above ran
    there); sharded + pg inapplicable by
    construction, judged: the target reaches no
    database, alias, or dialect decision (pure
    Python plus `import_string`), the Proof nodes
    carry no `django_db` marker, and the probe
    bootstraps no Django at all.

No disputed findings exist; none judged. No new
defects; no failing attack. Scratch:
`docs/review/temp-tests/sets_mixins/verify-mechanics-1/`
(`live-diff.diff`, `probe_memo_mechanics.py`,
`revert_failability.py`, `sets_mixins.backup.py`).
The verify copy is restored fresh; no run after
`review-20260929T141624-65f255` depends on a
reverted state.

Open threads: (1) the Perf Handoff's family
property-docstring reword was deliberately not
taken in this change — the Comments record routes
those twins to the `filters/base.py` +
`orders/base.py` items, and both files are
byte-identical to baseline, so the item fence
holds; (2) post-memo the routed "plain read"
twins describe the identical-value path more
closely than before — the owning family items
judge, not this item. Neither owes a re-pass.

Status: verified

Handoff: Beyond the record I read the Performance
and Comments records whole (incl. every Handoff
and the Comments C1/M9 disjunction), the plan's
`## Owned changes` rows for this item, the
pass-1 diff whole, and the live target + all four
touched test files. Judgment calls: the cells
verdict (12 above, concurring with the record);
accepting the RUF022 constant-first `__all__`
placement over the Recommendation's parenthetical
slot (10 above); R5 stands despite
`_validate_target` appearing in two diff lines
(prose + test double only, twins untouched).
Probe history worth one line: the first
`sorted(__all__)` oracle was my bug (RUF022 is
isort-style, not byte order), and the probe took
three iterations to bypass Django settings
(`object.__new__`) and count per family — all
green runs above are the final probe. Nothing
else is left for a later pass.
