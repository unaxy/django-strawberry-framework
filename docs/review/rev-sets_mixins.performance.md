# Review · Performance: `django_strawberry_framework/sets_mixins.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=569603863d594f6296d1c27cd8d0a2e6f2f4b3a5

## Trace

Target read whole (779 lines, blob `088ddab0`; dirty with concurrent work
at read time: 45 insertions, 34 deletions vs HEAD, attributed to other
sessions, not graded). Skeleton `docs/review/rev-sets_mixins.md` read
(`Status: reviewing`, blank Path class); sibling axis records
`rev-sets_mixins.mechanics.md` / `rev-sets_mixins.comments.md` absent
(concurrent run, not yet written). Plan `docs/review/review-0_0_15.md` read
including `## Owned changes` (no row names this target) and run-3 `Drift:`
lines. Orientation: `review_inspect.py` overview + stripped source under
`<root>/performance/inspect/` (json `<root>/performance/sets_mixins.json`):
0 per-row leads, 2 hot entry points (+0 reachable), 0 import-time work
items, 0 Django/ORM markers.

Hot-path map (every caller traced by `rg` over the package, tests, examples):

- `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin._resolved_target`
  runs on every `.filterset` / `.orderset` read. Per-request readers:
  `django_strawberry_framework/utils/permissions.py::run_active_input_permission_checks`
  (`getattr(related_obj, target_attr)` per active related branch per level);
  `django_strawberry_framework/filters/sets.py::FilterSet._iter_visibility_steps`
  (two reads of the same object back to back per branch:
  `_target_type_for_related_filter` then the loop body);
  `django_strawberry_framework/orders/inputs.py::normalize_input_value`
  (one read per active related order branch per level);
  `django_strawberry_framework/filters/base.py::RelatedFilter.get_queryset`
  (no-explicit-queryset fallback, per apply). Cold readers: input emission,
  `_expand_related_filter`, finalizer audits (all cached / one-shot). (F1)
- `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin._run_permission_checks`
  runs once per filtered/ordered apply per request
  (`django_strawberry_framework/filters/sets.py` x2 call sites,
  `django_strawberry_framework/orders/sets.py` x2 incl. async), recursing per
  active related branch and (filter) per logic arm. Facade-owned work is
  three no-op-or-cheap hooks, two `_permission` reads, one `{}` and one
  `object.__new__`; the walks are `utils/permissions.py`-owned. (R2, R3)
- `django_strawberry_framework/sets_mixins.py::expanded_once` cache-hit check
  runs once per filter apply
  (`django_strawberry_framework/filters/sets.py::FilterSet._normalize_input`
  calls `get_filters()` per request); order `get_fields()` only at input
  build. (R1)
- `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin._input_traversal`
  runs per request per apply/normalize (both families). One class-attr read.
  (R3)
- Cold: `type_name_for` (input build, factory-cached),
  `collect_related_declarations` (two metaclass callers only),
  `should_cache_expansion` (inside expansion build only),
  `require_re_readable_field_declaration` (inside expansion build only),
  `SetLifecycleAttrs.binding_attrs` (`registry.clear()` only), `_bind_owner`
  (metaclass bind only), `resolve_lazy_class` first-resolution imports
  (once per string target), `_active_permission_field_paths` (no production
  caller: tests only).

`Path class: hot` - the related-target seam runs per request per active
related branch (permission recursion, visibility derivation, order
normalization); the permission facade runs per apply; declaration,
expansion-build, naming and lifecycle helpers are cold.

Measurements, copy `review/sets_mixins.py/performance`, package digest
`sha256:04570f7bec...780364` (tree as it stands; not the plan's bench-baseline
digest, so every figure is self-referenced and every before/after compares
within its own copy). No bench instrument applies (pure-CPU seams below bench
spread; the instrument is a timeit scratch probe, median of 7 x 20000).

- `review-20260929T131734-82a5b2`: `probe_steady_costs.py` (probe blob
  `7fc9a4fe`): `filter.filterset_steady` 1640.2 ns,
  `order.orderset_steady` 1604.6 ns (F1 before);
  `resolve_lazy_class_on_class` 621.3 ns, `filter.validate_target` 860.6 ns
  (`order` 819.2 ns), `family_base_deferred_import` 303.4 / 293.4 ns,
  `truth.is_instance/is_type/is_subclass` 276.5 / 269.5 / 552.4 ns,
  `getattr_pair_plus_setattr` 17.3 ns, `memo_identity_check_floor` 10.6 ns;
  `expanded_once_cache_hit` 364.2 ns (R1);
  `input_traversal` 44.3 / 44.6 ns,
  `run_permission_checks_inactive` 133.1 / 319.0 ns (R2, R3);
  `type_name_for_root/nested` 454.6 / 1306.0 ns (R5).
- `review-20260929T131928-3c0576`: `pytest tests/test_sets_mixins.py --no-cov
  -p no:randomly`, `33 passed` (before-state green; the Proof's 3 seam
  nodes are a subset).
- `review-20260929T131939-bbd7ba`: `importtime_report.py --rounds 5`
  (instrument `15f679c9`): 69 modules, `sets_mixins` absent from the
  bare-package import graph (lands on first filters/orders use, not on
  `import django_strawberry_framework`). JSON
  `<root>/performance/importtime.json` (import-time discharge).

Cells: default measured (the probe opens no database; the module reaches no
alias or dialect decision). Sharded and pg are `inapplicable by
construction` for F1 (pure-Python memoization: no query text, no alias read,
no dialect branch). The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/sets_mixins.py`
088ddab0c0f68c0605bc4a440dfa3daa544452dd;
`django_strawberry_framework/filters/sets.py`
e47c6758e540e0bd9caa8cb90103263b26e905e1;
`django_strawberry_framework/filters/base.py`
3b1dcbced1069e0faf1abeb33661e94a296f94ba;
`django_strawberry_framework/filters/inputs.py`
a932dbf85d89791280774b0600a40b5fb43b89e4;
`django_strawberry_framework/orders/sets.py`
60859f2d54525acfdb3dc997d3e931ff3d58d956;
`django_strawberry_framework/orders/inputs.py`
2d258da74ee36f5d851ffa6550462b0fd65bd460;
`django_strawberry_framework/orders/base.py`
7616b27986e7794500c2b0fac97b104325fe0f12;
`django_strawberry_framework/utils/permissions.py`
1c9cfd398e6096e03bda82ba93dfd66a6d2fb890;
`django_strawberry_framework/utils/inputs.py`
b5af8255dfa18a2ff423cdd2de211723c5a15590;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`tests/test_sets_mixins.py`
23946eb5c62ba1def9bf040f1c0df70c08959d3b;
`scripts/importtime_report.py`
15f679c9ad736b71215d8ead0733116f56083cef.

## Findings

### High

None.

### Medium

#### F1: `_resolved_target` re-resolves and re-validates on every read

- Observation:
  `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin._resolved_target`
  runs `resolve_lazy_class` plus a re-store plus the family
  `_validate_target` on EVERY `.filterset` / `.orderset` read, including
  the steady state where the slot already holds a resolved class. A repeat
  read can only change verdict by `_set_target` substitution (any other
  verdict change needs a module reload or a `__bases__` mutation, neither a
  real path), yet every read pays the full resolve (truth MRO walks) and the
  full gate (deferred family import + truth MRO walks).
- Evidence: `review-20260929T131734-82a5b2`: steady-state `.filterset`
  1640.2 ns, `.orderset` 1604.6 ns; breakdown 621.3 ns re-resolve + 860.6 ns
  re-validate (303.4 ns deferred `from .sets import FilterSet`, 552.4 ns
  `truth.is_subclass`) + 17.3 ns getattr/setattr. Frequency, by call-site
  trace: 3 reads per request per active filter branch per level (permission
  recursion via `getattr(related_obj, target_attr)` +
  `_iter_visibility_steps`' back-to-back pair at
  `django_strawberry_framework/filters/sets.py` `_target_type_for_related_filter`
  + loop body), 2 per active order branch per level (normalize recursion +
  permission recursion), plus the `RelatedFilter.get_queryset` fallback when
  no explicit queryset is set. The gate has no success-path side effects in
  either family (pure `is_subclass` + local import), so skipping a repeat
  validation of an identical value changes no verdict; the family base
  object is stable post-import (no reload path: `registry.clear()` resets
  binding state, never modules). The existing seam pin
  (`test_related_set_target_mixin_gates_resolved_targets_at_the_seam`) reads
  once per instance, so a memo still validates exactly once per instance
  there.
- Impact: ~1.5 us saved per read; e.g. a 3-branch x 2-level filter request
  pays ~18 reads (~27 us) today. Moves no bench row (no bench exercises
  related-target reads; plan cache, walk, nested fetch, importtime
  untouched).
- Path class: hot - per request per active related branch (permission
  recursion, visibility derivation, order normalization); expansion-build
  reads are cold and cached.
- Severity: Medium - measured hot-path CPU cost without N+1.
- Instrument: timeit scratch probe, median of 7 x 20000 per label. Before:
  1640.2 / 1604.6 ns per read. After (predicted): memo hit ~ property +
  getattr + identity, <= 120 ns (identity-check floor measured 10.6 ns).
  Delta (predicted): ~-1.5 us per read. Permanent test: no timing test
  (flaky by construction); behaviour pinned by the 3 seam nodes in the Proof
  plus a Worker-2 deterministic counting pin (two reads -> one validation;
  substitution -> re-validation; failed value -> retry), and the number
  reproduced by the probe rerun. The verifier judges the pin.
- Recommendation: memoize the last successfully resolved+validated slot
  value (identity) in `_resolved_target`; memoize ONLY on success so failed
  resolutions and failed validations retry exactly as today.
  `_set_target` needs no invalidation (a substituted value is never
  identical to the memo, so it re-resolves and re-validates). Keep
  `resolve_lazy_class` and both families' `_validate_target` byte-identical;
  no lock (a racing repeat validation is idempotent, as today's racing
  re-store is). Update the two stale sentences (see C1) and the family
  property docstrings at `django_strawberry_framework/filters/base.py` +
  `django_strawberry_framework/orders/base.py` (owner-adjacent prose, same
  change).
- Must not change: every DISTINCT slot value still resolves and validates;
  failed reads still raise with the slot left as today (resolved value
  stored, validation error on every retry); `None` still skips the gate;
  string/factory first-resolution semantics (import attempts, factory runs
  once via the re-store); validation verdicts for every input.
- Proof:
  - `uv run python scripts/workspace.py run review/sets_mixins.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/sets_mixins/performance/probe_steady_costs.py` prints `filter.filterset_steady: median_ns=` below `500.0` and `order.orderset_steady: median_ns=` below `500.0` (before `1640.2` / `1604.6`).
  - `uv run python scripts/workspace.py run review/sets_mixins.py/verify-performance-<n> -- pytest tests/test_sets_mixins.py::test_related_set_target_mixin tests/test_sets_mixins.py::test_related_set_target_mixin_gates_resolved_targets_at_the_seam tests/test_sets_mixins.py::test_related_set_target_mixin_hook_is_abstract_without_a_family_validator --no-cov -p no:randomly` reports `3 passed` (before-state green at `review-20260929T132404-36c31f`; also a subset of the `33 passed` module run at `review-20260929T131928-3c0576`).
- Freshness: all files in `## Trace`.

### Low

None.

## Rejected

- R1: `expanded_once` cache-hit check (364.2 ns per filter apply). The
  in-target cost is one mandated truthful namespace read
  (`truth.class_dict`); a direct `cls.__dict__` read trips the
  truthful-reads gate, and there is no other in-target term. Trigger: a
  gate-blessed fast path for own-dict reads, or the filters item caching
  `get_filters()` across apply phases (family judgment; ~1 us/request at
  stake).
- R2: `cls._permission` double-read in `_run_permission_checks` (traversal
  sentinel, then `cfg`). Hoisting saves one class-attr read (~44 ns class,
  per the `_input_traversal` median), below timeit discrimination on shared
  hardware. Trigger: the method is restructured for another finding and the
  hoist rides free.
- R3: thin-delegate overhead (`_request_from_info`, `_extract_branch_value`,
  `_invoke_permission_method`, `_input_traversal` at 44 ns, the inactive
  prologue at 133 / 319 ns). Inherent to the facade-vs-duplication trade
  this module exists for; inlining re-copies family code. Trigger: a bench
  row implicating facade dispatch.
- R4: `_filter_set_class()` / `_order_set_class()` deferred import (303.4 /
  293.4 ns per validation). Subsumed by F1 on repeats (a memoized seam runs
  the import once per distinct value); memoizing the family base itself is
  owned by `filters/base.py` + `orders/base.py` (Routed lead in the report).
  Trigger: F1 disputed, or the family passes judging the base memo on its
  own terms.
- R5: `type_name_for` (root 454.6 ns, nested 1306.0 ns). Cold: input-build
  only, factory-cached. Trigger: a per-request caller appears.
- R6: `collect_related_declarations` namespace re-reads in the diamond
  reconciliation. Metaclass-time only (exactly two callers, both
  metaclasses). Trigger: a runtime caller appears.
- R7: `is_re_readable_field_declaration` (~2 us: `issubclass` + 4x
  `truth.is_subclass`). Runs per expansion build, cached after warm; on the
  unfinalized-direct-apply path the gate is noise beside the expansion's
  own deepcopy-per-related-filter. Trigger: a per-request caller outside
  expansion build.
- R8: `_run_permission_checks` per-level `{}` + `object.__new__(cls)`.
  Inherent: the dedup map scopes one run, and the bare instance must match
  the child class for gate lookup (the parent's bare cannot serve a child
  branch; same-`cls` logic recursion already reuses `_bare`). Trigger: a
  redesign of the dedup/bare contract.
- R9: `_active_permission_field_paths` runs the full single-pass traversal
  and discards the branches half. No production caller (tests only); cold
  by construction. Trigger: a production caller appears.
- R10: three active-branch walks per filter apply (permission single-pass +
  `_iter_visibility_steps` + `_apply_related_constraints`). The walks are
  `utils/permissions.py`-owned mechanics and the composition is
  `filters/sets.py`-owned; in-target there is nothing to change (facade
  delegates). Routed to the filters item (see report). Trigger: that pass
  measures walk cost worth sharing across phases.
- Looks-for entries with no candidate at all: N+1 / per-row queries,
  `len(qs)` / `bool(qs)`, `only()` / `defer()`, unbatched writes,
  `blog.id` vs `blog_id` (the module issues zero ORM calls:
  review_inspect reports 0 Django/ORM markers); repeated `_meta` walks,
  settings reads, regex compilation (none in the module; `truth.mro` runs
  at metaclass time only); `lru_cache` on methods (no caches, `B019`
  clean); locks, cache reads, re-parses, round trips on a per-request path
  (none: no locks, no I/O); import-time cost (module absent from the
  69-module bare-package import graph; review_inspect reports 0
  import-time work items; imports are stdlib +
  `django.utils.module_loading` + 4 light local modules).

## Cross-axis (for Comments)

### C1: target docstrings promise a plain repeat read the seam never gives

- Observation:
  `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`'s
  class docstring says the lazy property "re-stores the result so the next
  access is a plain read", and
  `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin._resolved_target`'s
  docstring says "on first access". Both are false against the body: every
  access re-runs `resolve_lazy_class`, re-stores, and re-fires
  `_validate_target` (measured 1640.2 ns steady-state, F1). The same
  class docstring contradicts itself two paragraphs down ("every read of a
  resolved target is family-checked").
- Evidence: body read of `_resolved_target` (no early return on a stored
  class) + `review-20260929T131734-82a5b2` steady-state medians proving
  repeat reads do full resolve+validate work.
- Impact: a reader sizing the hot path (or copying the seam for a future
  set family) budgets a plain dict read and gets 1.6 us of re-validation.
- Severity: Medium - stale docstring on a `__all__`-exported mixin, but
  the normative half of the same docstring (every read is family-checked)
  is true, so no behavioral contract misleads.
- Text after (F1-landed world; the Comments verifier grades what landed,
  the whole docstring each line sits in): class docstring: "resolves a
  string / callable target through ``resolve_lazy_class``, validates it
  through the family gate, and memoizes the validated result so a repeat
  access re-resolves only a substituted value." `._resolved_target`
  docstring first line: "Resolve the (possibly-lazy) target class and
  re-store it, validating each distinct value once." If F1 is disputed,
  the fallback text is: "re-stores the result, then re-validates it
  through the family gate on every access" (and the method line drops
  "on first access").
- Must not change: n/a (Comments finding).
- Proof: `grep -c "next access is a plain" django_strawberry_framework/sets_mixins.py` prints `0` (1 today, line 178), and the rewritten sentences grade true against `_resolved_target`'s body.
- Freshness: all files in `## Trace`.

Handoff: F1 is the only Performance finding: a per-read re-resolve +
re-validate worth ~1.5 us per `.filterset`/`.orderset` read, 2-3 reads per
request per active related branch per level, fixed by a success-only
identity memo that preserves every verdict on every real path (analysis in
Evidence). Everything else hot is either mandated truthful reads (R1),
inherent facade/alloc costs (R2/R3/R8), or owned elsewhere (R4/R10 routed
to the family passes). C1 rides F1's behaviour change and must be
implemented with the Comments axis against whatever lands. Open threads
for Worker-2: the memo slot name and its interplay with the expansion
deepcopy (class identities survive deepcopy atomically, so a copied memo
stays valid - the counting pin should cover a deepcopy round-trip); the
family property docstrings in `filters/base.py` + `orders/base.py` carry
the same "plain read" sentence and need the same rewording in this change.
No defect, no blocked item, no bench row moves.

## Verify performance

Precondition: the live tree carries exactly the change under grade.
`git diff ITEM_BASELINE -- <4 paths>` is byte-identical to
`docs/review/temp-tests/sets_mixins/diff/pass-1.diff` (DIFF-MATCH);
live blobs `sets_mixins.py` 1f8e078d, `tests/test_sets_mixins.py`
8c1488d7, `tests/filters/test_inputs.py` 4e280999,
`tests/orders/test_base.py` 00de6531. `tests/filters/test_sets.py`
is byte-identical to ITEM_BASELINE (ea6d0b04, L18 deferred per the
ride rule). The landed memo matches the F1 Recommendation verbatim
(identity check before resolve, store after a successful gate, no
lock); `resolve_lazy_class` and both family `_validate_target`s are
byte-identical (no body hunk touches them; `filters/base.py` and
`orders/base.py` are absent from the diff).

All runs at `review/sets_mixins.py/verify-performance-1` (slot-3,
package digest `sha256:b0961523...` after / `sha256:04570f7b...`
reverted, cell default, copy `fresh` except during the staged
revert). Scratch: `docs/review/temp-tests/sets_mixins/verify-performance-1/`
(`sets_mixins.after.py`, `attack_memo_edges.py`).

### F1: success-only identity memo - pass

- Probe `review-20260929T140934-ea5a25`: `filter.filterset_steady:
  median_ns=146.1`, `order.orderset_steady: median_ns=183.7`, both
  below the `500.0` gate (record before `1640.2` / `1604.6`;
  implement after `58.2` / `60.4` at
  `review-20260929T140147-e9d306` - cross-copy medians drift, the
  gate holds on every after-side reading).
- Seam nodes `review-20260929T140946-8f94c9`: `3 passed`.
- Counting pin + factory pin `review-20260929T141157-275b57`: `2
  passed`. Full pin-bearing modules
  `review-20260929T141214-e7de52`: `57 passed`
  (`tests/test_sets_mixins.py` 34 incl. the new pin,
  `tests/orders/test_base.py` 23).
- The pin covers all four legs the record asks for: two reads ->
  one validation; `_set_target` substitution -> re-validation;
  failed value -> retry (`[_MemoHostile, _MemoHostile]`);
  `deepcopy` round-trip -> memo hit with no new validation.
- Failability on memo revert `review-20260929T141233-3ae1d2`
  (ITEM_BASELINE production blob written into my copy, tests
  kept): exactly the counting pin fails, the 3 seam nodes still
  pass (`1 failed, 3 passed`) - the pin is the discriminating
  gate. Post-restore rerun `review-20260929T141330-6756e4`: `1
  passed`; copy restored byte-identical (`cmp` clean).
- Must-not-change holds: distinct values validate (pin legs 1-2);
  failures retry identical (pin leg 3: slot left resolved,
  error on every retry); `None` skips the gate (seam test
  passthrough + attack probe); factory runs once
  (`test_related_order_accepts_callable_factory`, invocations ==
  1 across two reads, in the 2-passed run); string
  first-resolution covered by the 57-passed modules; verdicts
  for every input preserved (gate is a pure `is_subclass` check
  against a post-import-stable family base, skipped only for an
  identical already-validated value).

Before confirmation (the `before` copy's venv is broken - see
open threads, same failure the scalars item hit): the staged
revert above doubles as the before leg -
`review-20260929T141252-1611ac` prints `2567.3` / `2544.8` ns
with package digest `sha256:04570f7b...`, exactly the `before`
copy's header digest, so the reverted tree IS the before tree.
Same-session delta: `-94%` / `-93%` per read. Every before
reading (`1640.2` / `1604.6` review-time, `2567.3` / `2544.8`
same-session) sits far above the gate; every after reading
sits far below it.

Cells: default run performed for every leg. Sharded and pg stand
`inapplicable by construction`, judged independently: the target
imports only stdlib + `django.utils.module_loading.import_string`
+ `.exceptions` + `.utils.*` (no `django.db`, no `connections` /
`using` / `alias` / dialect token in the module), the memo is
pure-Python instance state, and no probe opens a database.

No bench row moves: none of the three bench scripts nor
`_bench_common.py` references `sets_mixins` / `_resolved_target` /
`filterset` / `orderset` (grep exit 1); the diff adds no import,
so the bare-package import graph (which `sets_mixins` is absent
from) is unchanged. Rejections R1-R10 stand: R1/R2/R3/R5/R6/R7/
R8/R9 code untouched (docstring-only hunks on R1/R5/R7); R4
subsumed by F1 on repeats exactly as predicted (the deferred
family import now runs once per distinct value; the family-base
memo stays owned by the untouched family files); R10 the
walk composition is untouched out-of-target code. The looks-for
discharges hold: no new imports, ORM calls, locks, or settings
reads in the diff.

Prose edits disturb no Performance claim: the converged C1/M3/M4
memo-world text is true against the landed body (memoizes the
validated result; identical repeat skips re-validation;
substituted re-resolves and re-validates; failures never
memoized - each clause pinned by the pin or the attack probe);
the three "every read" -> "every distinct value" rewords state
the memo semantics; M1/M2/M5-M8/M10-M12 + L1-L17 touch counts,
mood, provenance, and consumer censuses only, none of them a
measured quantity. Whole-diff reading: every production hunk is
the memo (check + store + `current` hoist, which reuses the one
`getattr` the old body already paid), the `__all__` +3 (static
tuple, zero per-request cost), or prose - no other hot-path code
is touched. C1 itself is graded by the Comments verifier; the
behavior it describes is confirmed here.

Attacks, all passing, no new finding (`attack_memo_edges.py`,
`review-20260929T141402-18c575`, ATTACK-PROBE-GREEN): (1)
A->B->A substitution re-validates the restored value (the safe
direction - a repeat validation, never a skipped one); (2)
`None` interleaving leaves a live memo intact and skips the
gate; (3) a failed value is never memoized
(`getattr(bad, "_validated_target_memo", None) is None`) and a
failure does not clobber a live memo. Static: no `__slots__` on
either family or the mixin (the memo `setattr` rides the same
instance dict the re-store already writes); the memo slot name
appears only in the seam + the pin; the memo check uses `is`
throughout, immune to hostile `__eq__`; a racing repeat
validation stays idempotent, as the Recommendation states.
Disputes: none (the main artifact carries no Worker-2 section,
as on every other item this run; `implement/pass-1.md` disputes
nothing).

Open threads: (1) the item's `before` copy venv is broken
(`review-20260929T140955-9c2928` exits 1:
`ModuleNotFoundError: No module named 'typing_extensions'`) -
Worker-0 note for sibling verifiers, not a gap (before
confirmed via the digest-matched staged revert above); never
`--fresh`-ed nor edited.

Handoff: Performance verification is closed: F1 passes with both
probe medians below threshold on two after-side runs plus a
same-session digest-matched before leg; 3 seam + pin + factory +
57 module nodes green; the pin fails exactly on memo revert
while the seam nodes stay green; edge attacks (round-trip
substitution, None interleaving, failure non-clobbering) green;
cells judged (sharded/pg inapplicable by construction); no bench
row moves; R1-R10 stand; prose edits Performance-clean. The only
follow-up is Worker-0's: the broken `before` venv, which the
Mechanics and Comments verifiers will also hit if they address
that copy.

Status: verified
