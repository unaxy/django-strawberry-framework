# Review · Comments: `django_strawberry_framework/sets_mixins.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=569603863d594f6296d1c27cd8d0a2e6f2f4b3a5

## Trace

Read the whole live target (`django_strawberry_framework/sets_mixins.py`, 779
lines: 31 docstrings, comments census 39 entries per the
`review_inspect.py` overview) and the whole own test module
(`tests/test_sets_mixins.py`, 1036 lines: 36 docstrings) plus 22
other-test-module prose units about the target's symbols (extracted to
`other-prose.txt`; every genuine one graded in Findings/Rejected/Routed).
No sibling axis records existed at dispatch (only `rev-sets_mixins.md`,
`Status: reviewing`); required reading was AGENTS.md, START.md,
REVIEW.md, worker-1.md, the plan, and `rev-sets_mixins.md`. The target
and the own test module are byte-identical to ITEM_BASELINE (`git diff
ITEM_BASELINE -- <both paths>` is empty); the dirt versus HEAD is
pre-existing concurrent work captured in the baseline, and every grade
below is against the live text at the fingerprints in this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/sets_mixins/comments/inspect/` plus
`sets_mixins.json`. `build_tree_md.py --list-docstrings` passes on both
graded files (0 breaking each). `check_citations.py --paths <file>
--substrings --json` reports 9 citations, 0 violations in the target
and 1 citation, 0 violations in the own test module (saved as
`citations-target.json` / `citations-test.json`). Provenance sweep
(REVIEW.md pattern via the search tool, since `rg` is not installed) on
the two graded files hits the `spec-027 / spec-028 Decision 8` pointers
(kept per START.md), the `used to` / `grew` / `previous` / `pre-hook` /
`no longer` / `replaces` / `now` clauses graded below, and `round-trip`
free prose otherwise. No `we`/`you`/`I`, no `Tests that`/`Ensures`, no
`.py:NN` references, no TODO, no public symbol without a docstring in
either file. `__all__` carries 9 names; `require_re_readable_field_declaration`
(imported by both families' production modules),
`is_re_readable_field_declaration`, and `RE_READABLE_FIELDS_HELP` are
absent from it (M9 + C1).

Contract trace, each claim checked against its body and one real
caller: the module-docstring family censuses (both families inherit both
mixins, filters/sets.py:1156, orders/sets.py:334; the `two` count and
the `fourth` count falsified in M1/M2); the `type_name_for` consumer
census (`filters/inputs.py:975` per-field, `utils/inputs.py:80` root
delegate re-exported by both families, no order-side per-field call —
M7); the FilterSet `_field_type_suffix` override (filters/sets.py:1280)
and the OrderSet deliberate non-override (orders/sets.py:353); the
`_pascal_case` sharing (`filters/inputs.py:261` delegates to
`pascal_case_or_raise`; exactly two production consumers); the
`pascal_case` split-and-drop (`utils/strings.py:190`); the
`resolve_lazy_class` attempt/factory/passthrough ladder against the
cookbook body (same order, truthful reads) and the pinned passthroughs
(M5); the `_resolved_target` every-read gate (sets_mixins.py:224-234)
against the `plain read` / `first access` claims (M3/M4) and the
four-reader census (BFS `_ensure_built` via the `filterset`/`orderset`
property, utils/inputs.py:1785; `_expand_related_filter` via
`f.filterset`, filters/sets.py:1131; the finalizer audit via
`.filterset`/`.orderset`, finalizer.py:1679/1657; the permission
recursion via `target_attr`, permissions.py:594,693); the finalize-time
strict cross-owner catch (`_bind_filterset_owner` /
`_bind_orderset_owner`, both naming both owners); both metaclass call
sites (`declared_filters.items()` + `class_items` + `declared_filters`
map on the filter side, filters/sets.py:1052; `attrs.items()` +
`inherit_from_bases=True` on the plain-`type` order side,
orders/sets.py:323); both `expanded_once` call sites (filter passes
`on_reentry=get_base`, filters/sets.py:1424; order passes none,
orders/sets.py:446); both `require_*` call sites and their `accepted`
strings (filter lookup-bag + `__all__`, filters/sets.py:1493; order
`__all__`-only, orders/sets.py:514); the `binding_attrs` reset chain
(`_lifecycle` on both set classes incl. the filter `_expanded_snapshot`
extra, `clear_generated_input_namespace` consuming `binding_attrs`,
both namespace clears registered into `registry.clear()`); the
`SetInputTraversal` five-field census (input_values.py:159-163);
`target_attr` used only by the permission recursion (sets_mixins.py:756
-> permissions.py:594,693; the factories' `_related_target_attr` is a
separate attribute); `family_label` in both `request_from_info` errors;
both normalizers classifying through `cls._input_traversal()`
(filters/sets.py:2341, orders/inputs.py:317,356); the order-only
`_prepare_permission_input` override (orders/sets.py:620); the filter
fallback remap / depth cap / logic recursion overrides; the related
recursion cap inside `run_active_input_permission_checks`
(permissions.py:650-657,701-706); the cookbook ground truth
(`ClassBasedTypeNameMixin` inherited by cookbook filterset + orderset +
aggregateset; `stringcase.pascalcase`; per-segment split; nested
permission delegation, filterset.py:310; `fieldset.py` +
`AdvancedFieldSet`; idempotent-once cookbook bind; direct-slot cookbook
fget write; the three unported helper names exactly the module
docstring's list); the `6912ca92` introduction (both counts born: `two`
true then, `fourth` born-stale — only filters + orders ever used the
substrate); the `835445cf` guard single-siting (sibling guards merged
into the strings helper — M11); the born-structural gate (`a8f31a2d` —
L16); all five bare live-test names and all five live files named in
the test module docstring (verified verbatim); the live behavior mapping
(`iContains`, `and/or/not`, `orderBy`, both empty-input no-ops);
GLOSSARY (one RelatedOrder anchor, resolution account true) and
`docs/README.md` (no target prose).

Cells: no workspace run was needed — every instrument above is static
(source reads, AST census, citation resolution, cookbook comparison,
git history). Sharded and pg are inapplicable by construction to this
Comments pass (no database-reaching probe; all Proofs are static
`grep -c` / `sed` plus grade judgments; Worker-2's prose edits owe
`--code-digest` identity, not cell runs). Cells unverified: none.

Fingerprints (`git hash-object` 8-char; cookbook sha256 12-char):
target `088ddab0`; `tests/test_sets_mixins.py` `23946eb5`;
`filters/sets.py` `e47c6758`; `filters/base.py` `3b1dcbce`;
`filters/inputs.py` `a932dbf8`; `filters/__init__.py` `86b25818`;
`orders/sets.py` `60859f2d`; `orders/base.py` `7616b279`;
`orders/inputs.py` `2d258da7`; `utils/inputs.py` `b5af8255`;
`utils/permissions.py` `1c9cfd39`; `utils/input_values.py` `18992b79`;
`utils/strings.py` `5a4f4811`; `types/finalizer.py` `b9d8acb2`;
`registry.py` `27358cbc`; `forms/sets.py` `2642a647`;
`mutations/sets.py` `21c15c0b`; `rest_framework/sets.py` `2b88fe58`;
`tests/filters/test_inputs.py` `c5422da5`;
`tests/filters/test_sets.py` `ea6d0b04`;
`tests/filters/test_base.py` `3f04eeeb`;
`tests/filters/test_finalizer.py` `4bbcfaab`;
`tests/filters/fixtures/filtersets.py` `8ce45ef9`;
`tests/orders/test_inputs.py` `be8b48a3`;
`tests/orders/test_sets.py` `d66b482d`;
`tests/orders/test_base.py` `16ec8284`;
`tests/orders/test_composition.py` `9414d257`;
`tests/orders/test_finalizer.py` `5c011ef5`;
`tests/utils/test_inputs.py` `42bfb6a7`; `docs/GLOSSARY.md`
`3413edc3`; `docs/README.md` `30978c34`; cookbook `mixins.py`
`520d337e08a0`, `filterset.py` `a009caa423f5`, `filters.py`
`1feaa644e1a7`, `orders.py` `77f5a848371d`, `orderset.py`
`816ad0284e13`, `aggregateset.py` `ada1d45b999a`. A finding's
Freshness lists only files beyond these: none.

## Findings

### High

None.

### Medium

- Observation: the module docstring says "The two foundational
  mixins the shipped ``FilterSet`` / ``OrderSet`` use:" and then
  lists THREE bullets (`ClassBasedTypeNameMixin`,
  `LazyRelatedClassMixin`, `ActiveInputPermissionMixin`). The count
  was true at introduction (`6912ca92`, two bullets); the
  `ActiveInputPermissionMixin` bullet landed without updating it.
- Evidence: read verbatim (sets_mixins.py:9-20); `6912ca92` shows
  the two-bullet original.
- Impact: the module's own table of contents miscounts its entries;
  a reader stops after two.
- Severity: Medium (stale module prose).
- Recommendation: count three; see text-after.
- Must not change: n/a.
- Proof: `grep -c "The two foundational mixins"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the recounted opener earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py` module docstring.
- Grade: stale (count rotted by the third bullet).
- Text-before:
  `The two foundational mixins the shipped ``FilterSet`` / ``OrderSet`` use:`
- Text-after:
  `The three foundational mixins the shipped ``FilterSet`` / ``OrderSet`` use:`

- Observation: the module docstring says the substrate is
  single-sited here "so a future set family does not copy the
  related-declaration + metaclass + expansion lifecycle a fourth
  time". No natural count yields three prior copies: the package
  holds two lifecycles (filters, orders — the only
  `RelatedSetTargetMixin` / `collect_related_declarations` /
  `expanded_once` consumers; forms/mutations/rest_framework carry
  none), so a future family would be the third; counting the
  cookbook's three full lifecycles (filter, order, aggregate
  metaclasses + related collections + expansions) the total is five.
  The ordinal was born-stale in `6912ca92` (only two families used
  the substrate then too).
- Evidence: the consumer census above; the cookbook metaclass
  census; `git grep RelatedSetTargetMixin 6912ca92` (filters +
  orders only).
- Impact: wrong ordinal in the consolidation rationale; a reader
  hunting the third copy finds nothing.
- Severity: Medium (stale module prose).
- Recommendation: count the package lineage (third); see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "lifecycle a fourth time"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the recounted sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py` module docstring.
- Grade: stale (ordinal matches no lineage count).
- Text-before:
  `Plus the set-family DECLARATION-LIFECYCLE substrate single-sited here, so a future set family does not copy the related-declaration + metaclass + expansion lifecycle a fourth time:`
- Text-after:
  `Plus the set-family DECLARATION-LIFECYCLE substrate single-sited here, so a future set family does not copy the related-declaration + metaclass + expansion lifecycle a third time:`

- Observation: the `RelatedSetTargetMixin` docstring says the lazy
  property "re-stores the result so the next access is a plain
  read". No access is ever plain: the family getters call
  `_resolved_target()` unconditionally, which re-runs
  `resolve_lazy_class` AND re-fires `_validate_target` on every
  read — the same docstring's later paragraph says "every read of
  a resolved target is family-checked", and `_resolved_target`'s
  own docstring says a failed read "re-raises on every retry". The
  re-store skips re-import only, not re-validation.
- Evidence: `_resolved_target` body (sets_mixins.py:224-234, no
  early return); both family getters (`return
  self._resolved_target()`, filters/base.py:1157,
  orders/base.py:144).
- Impact: states a caching property the seam does not have, inside
  the docstring that elsewhere states the true every-read gate;
  the same false sentence is copied in both family property
  docstrings (routed).
- Severity: Medium (stale docstring clause, contradicted by its own
  paragraph).
- Recommendation: state what the re-store skips (re-import) and
  what still fires (the gate); see text-after.
- Must not change: n/a.
- Proof: `grep -c "the next access is a plain"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten clause earns grade true. (Source wraps `plain` /
  `read.` across lines 178-179.)
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`.
- Grade: stale (false caching claim).
- Text-before:
  `a lazy ``.<target>`` property that resolves a string / callable target through ``resolve_lazy_class`` and re-stores the result so the next access is a plain read.`
- Text-after:
  `a lazy ``.<target>`` property that resolves a string / callable target through ``resolve_lazy_class`` and re-stores the result so the next access skips re-import (the family gate still fires on every read).`

- Observation: `_resolved_target`'s first line says "Resolve the
  (possibly-lazy) target class on first access and re-store it."
  Resolution is not first-access-only: the body runs the full seam
  (resolve + re-store + gate) on every call, and the docstring's
  own second paragraph says a failed read "re-raises on every
  retry". Same root as the `plain read` clause, separate text.
- Evidence: the body has no resolved-check early return; the
  paragraph-2 retry sentence.
- Impact: the method summary promises once-ness its own paragraph
  retracts.
- Severity: Medium (stale first line).
- Recommendation: drop the once-ness; see text-after.
- Must not change: n/a.
- Proof: `grep -c "on first access and re-store it"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin._resolved_target`.
- Grade: stale (once-ness the body does not implement).
- Text-before:
  `Resolve the (possibly-lazy) target class on first access and re-store it.`
- Text-after:
  `Resolve the (possibly-lazy) target class and re-store it.`

- Observation: `resolve_lazy_class`'s first line says "Resolve
  `class_ref` to a class." The method does not always return a
  class: callables are invoked as zero-arg factories (their return
  value passes through whatever it is) and "everything else is
  returned as-is" — `None` passes to `None`, `12345` to `12345`
  (both pinned by tests), and the `None` passthrough is the
  load-bearing skip-silently placeholder contract. The docstring
  body documents all of this; only the headline overclaims.
  Graded Medium rather than High: the docstring as a whole states
  the true contract, with a wrong headline.
- Evidence: the body (sets_mixins.py:157-167); the passthrough
  tests (test_sets_mixins.py:544-545,984).
- Impact: the headline contract ("to a class") misleads about the
  `None` placeholder and factory shapes a consumer relies on.
- Severity: Medium (stale first line on a public method).
- Recommendation: headline the ladder; see text-after.
- Must not change: n/a.
- Proof: ``grep -c 'Resolve `class_ref` to a class\.'
  django_strawberry_framework/sets_mixins.py`` prints `0` (1 today);
  the rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`.
- Grade: stale (headline overclaims the documented ladder).
- Text-before:
  ``Resolve `class_ref` to a class.``
- Text-after:
  ``Resolve `class_ref`: strings via import, callables via zero-arg call, everything else as-is.``

- Observation: `expanded_once`'s first line says "Run ``build()``
  once under a class-level expansion cache + reentry guard."
  `build` does not run once: when it declines the cache write (a
  lazy related target keeps `should_cache_expansion` false), the
  next `get_filters` / `get_fields` call rebuilds — the re-run is
  documented in this file's own `require_*` docstring
  ("`OrderSet._expand_meta_fields` re-runs whenever ...") and is
  the behavior the cache-write gate exists to manage.
- Evidence: the skeleton returns cached-or-builds with no
  build-once enforcement (sets_mixins.py:388-398); the `require_*`
  re-run sentence; both families' conditional cache writes.
- Impact: the skeleton summary denies the lazy-window re-expansion
  the rest of the file describes.
- Severity: Medium (stale first line).
- Recommendation: state the cache-conditional once-ness; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "once under a class-level expansion cache"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::expanded_once`.
- Grade: stale (once-ness the lazy window breaks).
- Text-before:
  `Run ``build()`` once under a class-level expansion cache + reentry guard.`
- Text-after:
  `Run ``build()`` under a class-level expansion cache + reentry guard; ``build`` re-runs on every call while it declines the cache write (a lazy related target keeps ``should_cache_expansion`` false).`

- Observation: the `type_name_for` docstring lists the consumers
  the raise serves as "`_build_input_fields` operator-bag naming,
  shipped `OrderSet` and future `AggregateSet` per-field naming".
  The shipped `OrderSet` does no per-field naming: the order side
  has no per-field operator bag (orders/sets.py:359-360), and the
  only per-field `type_name_for(path)` call in the tree is the
  filter side's (`filters/inputs.py:975`); orders mint root names
  only via `set_input_type_name`.
- Evidence: the `type_name_for` call census (Trace); the order
  no-operator-bag prose.
- Impact: credits the order family with a naming path it has
  never had; a reader hunts a nonexistent order-side bag.
- Severity: Medium (false consumer claim).
- Recommendation: scope per-field naming to filters (+ future
  aggregates); see text-after.
- Must not change: n/a.
- Proof: `grep -c "naming, shipped"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rescoped parenthetical earns grade true. (Source wraps
  `per-field` / `naming` across lines 110-111.)
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`.
- Grade: stale (phantom order-side consumer).
- Text-before:
  `(_build_input_fields operator-bag naming, shipped ``OrderSet`` and future ``AggregateSet`` per-field naming)`
- Text-after:
  `(_build_input_fields operator-bag naming; the order side mints root names only, and a future ``AggregateSet`` shares the per-field rule)`

- Observation: the `is_re_readable_field_declaration` docstring
  says the `Collection` check "admits every shipped declaration
  shape (list / tuple / set / frozenset / dict)". It does not
  admit `__all__`: the top-level string shorthand is a shipped
  shape on both families and the gate rejects it (text atom) —
  both families handle `__all__` BEFORE the gate (filter exempts
  `str`, filters/sets.py:1489; order branches on it,
  orders/sets.py:490) precisely because it cannot pass.
- Evidence: `is_re_readable_field_declaration("__all__")` is
  `False` (text-atom exclusion); both pre-gate branches.
- Impact: a reader believes `__all__` passes the gate; a third
  family routing it through `require_*` gets a surprising
  rejection.
- Severity: Medium (false universal with a real omitted member).
- Recommendation: scope the universal to collection shapes; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "admits every shipped declaration shape"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rescoped sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::is_re_readable_field_declaration`.
- Grade: stale (`__all__` ships and is not admitted).
- Text-before:
  `That admits every shipped declaration shape (list / tuple / set / frozenset / dict)`
- Text-after:
  `That admits every shipped collection declaration shape (list / tuple / set / frozenset / dict)`

- Observation: `test_sets_mixins_all_exports_are_complete`'s
  docstring says "``__all__`` names every public symbol."
  `__all__` omits `require_re_readable_field_declaration` — a
  non-underscore name both families' production modules import
  (filters/sets.py:62, orders/sets.py:45) — plus the non-underscore
  `is_re_readable_field_declaration` and
  `RE_READABLE_FIELDS_HELP`. The test itself pins only
  `should_cache_expansion` membership plus member existence, never
  completeness.
- Evidence: the `__all__` tuple (sets_mixins.py:769-779) versus the
  two family import blocks; the test body.
- Impact: the completeness claim is false on its face; either the
  export list or the sentence must move (C1 carries the Mechanics
  arm).
- Severity: Medium (false universal in test prose about the
  target's export surface).
- Recommendation: narrow the sentence to what the test pins, or
  complete `__all__` (then text-before stands true); see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "names every public symbol"
  tests/test_sets_mixins.py` prints `0` (1 today) with the narrowed
  sentence grading true; OR `require_re_readable_field_declaration`
  joins `__all__` via C1, in which case text-before stands true
  and this finding closes through the Mechanics fix. The verifier
  grades what landed.
- Freshness: none beyond Trace.
- Symbol: `tests/test_sets_mixins.py::test_sets_mixins_all_exports_are_complete`.
- Grade: stale (completeness the tuple does not have).
- Text-before:
  ```text
  ``__all__`` names every public symbol. A request cannot prove absence of extras.
  ```
- Text-after:
  ```text
  ``__all__`` names the mixin surface plus the expansion helpers. A request cannot prove absence of extras.
  ```

- Observation:
  `test_re_readable_gate_rejects_one_shot_and_text_atoms`'s
  docstring says "One-shot producers and text atoms are the two
  rejected shapes." Its own `rejected` tuple pins a third
  category: plain non-collections (`123`, `object()`, `None`),
  which are neither one-shot producers nor text atoms. The body
  explains the two named shapes and never mentions the third.
- Evidence: the tuple (test_sets_mixins.py:907-918) versus the
  docstring (lines 899-906).
- Impact: the docstring miscounts the partition its own test
  pins.
- Severity: Medium (stale test docstring).
- Recommendation: count three and name the third; see text-after.
- Must not change: n/a.
- Proof: `grep -c "are the two rejected shapes"
  tests/test_sets_mixins.py` prints `0` (1 today); the recounted
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_sets_mixins.py::test_re_readable_gate_rejects_one_shot_and_text_atoms`.
- Grade: stale (omits the tuple's third category).
- Text-before:
  ```text
  One-shot producers and text atoms are the two rejected shapes.
  ```
- Text-after:
  ```text
  One-shot producers, text atoms, and non-collections are the three rejected shapes.
  ```
  (plus, before the `Rejected at class creation` sentence:)
  ```text
  Plain non-collections (``123``, ``object()``, ``None``) fail the ``Collection`` check outright.
  ```

- Observation:
  `test_type_name_for_raises_for_no_word_character_field_path`'s
  docstring says "The guard is hoisted from ``_pascal_case`` (the
  direct ``_build_range_input_class`` consumer) into the shared
  ``ClassBasedTypeNameMixin``". Both halves are wrong: the guard
  lives in `utils.strings.pascal_case_or_raise`, which both
  consumers wrap — nothing moved from `_pascal_case` into the
  mixin. History (`835445cf`) merged two sibling guards (one in
  each consumer) into the strings helper; the guard never lived in
  the mixin, before or after.
- Evidence: both call sites (`type_name_for`,
  sets_mixins.py:116; `_pascal_case`, filters/inputs.py:261) wrap
  the helper; the `835445cf` diff (sibling-guard merge).
- Impact: wrong stated mechanism for the sharing the helper owns
  (DRY principle 10: worse than none), plus change narration.
- Severity: Medium (false mechanism in test prose about the
  target's symbol).
- Recommendation: state the shared-helper shape; see text-after.
- Must not change: n/a.
- Proof: `grep -c "hoisted from"
  tests/filters/test_inputs.py` prints `0` (1 today); the rewritten
  paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/filters/test_inputs.py::test_type_name_for_raises_for_no_word_character_field_path`.
- Grade: stale (guard moved neither from nor into the named sites).
- Text-before:
  ```text
  The guard is hoisted from ``_pascal_case`` (the direct ``_build_range_input_class`` consumer) into the shared ``ClassBasedTypeNameMixin`` so the bag-class naming path in
  ```
- Text-after:
  ```text
  The guard lives in the shared ``utils.strings.pascal_case_or_raise`` both ``_pascal_case`` and ``ClassBasedTypeNameMixin`` wrap, so the bag-class naming path in
  ```

- Observation:
  `test_related_order_orderset_setter_assigns_underscore_orderset`'s
  docstring says "the lazy-resolution cache write at
  ``RelatedOrder.orderset.fget`` re-stores the resolved class
  through this setter". It does not go through the setter:
  `_resolved_target` writes the slot directly (`setattr(self,
  self._target_attr, resolved)`, sets_mixins.py:228), and the
  cookbook fget it ports does the same (`self._orderset = ...`,
  cookbook orders.py:23). The setter and the cache write share an
  effect, not a path.
- Evidence: both bodies; the cookbook fget.
- Impact: states a call path that exists nowhere; a reader
  instrumenting the setter misses the cache write.
- Severity: Medium (false mechanism in test prose about the
  target's seam).
- Recommendation: contrast the two writes; see text-after.
- Must not change: n/a.
- Proof: `grep -c "re-stores the resolved class through"
  tests/orders/test_base.py` prints `0` (1 today); the rewritten
  parenthetical earns grade true. (Source wraps `through` / `this
  setter` across lines 201-202.)
- Freshness: none beyond Trace.
- Symbol: `tests/orders/test_base.py::test_related_order_orderset_setter_assigns_underscore_orderset`.
- Grade: stale (no setter on the cache-write path).
- Text-before:
  `(e.g., the lazy-resolution cache write at ``RelatedOrder.orderset.fget`` re-stores the resolved class through this setter).`
- Text-after:
  `(contrast the lazy-resolution cache write at ``RelatedOrder.orderset.fget``, which re-stores the resolved class by writing the ``_orderset`` slot directly, not through this setter).`

### Low

- Observation: the `ClassBasedTypeNameMixin` class docstring is
  imperative ("Contribute ..."). REVIEW.md requires a description
  for a class; ruff's Google convention leaves mood unchecked, so
  the reviewer is the gate. Content is true; only the mood is
  wrong. (Precedent: apps.py Comments F2, deferred there, stands.)
- Evidence: the first line; REVIEW.md "First lines, by kind".
- Impact: bounded clarity; class-first-line consistency.
- Severity: Low.
- Recommendation: recast as a description; see text-after.
- Must not change: n/a.
- Proof: `grep -c '"""Contribute a'
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten class docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin`.
- Grade: duplicates the code (mood defect; imperative class first
  line — graded here as the class-first-line rule violation, per
  the apps.py precedent).
- Text-before:
  `Contribute a ``type_name_for()`` classmethod for class-derived GraphQL naming.`
- Text-after:
  `Class-derived GraphQL naming through a ``type_name_for()`` classmethod.`

- Observation: the `LazyRelatedClassMixin` class docstring is
  imperative ("Resolve ..."). Same rule, same precedent as L1;
  content (aside from L5's clause) is true.
- Evidence: the first line; REVIEW.md "First lines, by kind".
- Impact: bounded clarity.
- Severity: Low.
- Recommendation: recast as a description; see text-after.
- Must not change: n/a.
- Proof: `grep -c '"""Resolve a class reference that may be'
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten class docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin`.
- Grade: duplicates the code (mood defect; see L1).
- Text-before:
  `Resolve a class reference that may be a string, callable, or class.`
- Text-after:
  `Lazy resolution for a class reference that may be a string, callable, or class.`

- Observation: the module docstring's `ActiveInputPermissionMixin`
  bullet ends "this mixin is the one wrapper layer both families
  used to copy." "Used to copy" narrates the pre-consolidation
  state instead of the live sharing the mixin owns.
- Evidence: both families inherit the mixin today (no copies).
- Impact: bounded; history where the ownership invariant belongs.
- Severity: Low.
- Recommendation: present-tense sharing; see text-after.
- Must not change: n/a.
- Proof: `grep -c "families used to copy"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten clause earns grade true. (Source wraps `both` /
  `families used to copy` across lines 19-20.)
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py` module docstring.
- Grade: process provenance (past-tense change narration).
- Text-before:
  `Mechanics live in ``utils/permissions.py``; this mixin is the one wrapper layer both families used to copy.`
- Text-after:
  `Mechanics live in ``utils/permissions.py``; this mixin is the one wrapper layer both families share.`

- Observation: the `type_name_for` docstring says a `LOOKUP_SEP`
  boundary "PascalCases each path segment exactly as the previous
  per-segment split did". The equivalence is true (whole-path
  `pascal_case` drops empty tokens; pinned by the digit-boundary
  tests), but "the previous ... did" narrates the replaced
  implementation.
- Evidence: `pascal_case` body (utils/strings.py:190); the
  digit-boundary pins.
- Impact: bounded; replaced-implementation comparison where the
  behavior rule belongs.
- Severity: Low.
- Recommendation: state the behavior without the predecessor; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "exactly as the previous"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten clause earns grade true. (Source wraps `previous`
  / `per-segment split did` across lines 107-108.)
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`.
- Grade: process provenance (predecessor narration on a true equivalence).
- Text-before:
  `boundary PascalCases each path segment exactly as the previous per-segment split did.`
- Text-after:
  `boundary PascalCases each path segment, matching the cookbook's per-segment split.`

- Observation: the `LazyRelatedClassMixin` docstring says "the
  `resolve_lazy_class` body follows upstream's resolution order
  with its identity reads made truthful, while the class docstring
  is rewritten to surface the consumer-side rationale." "Made
  truthful" narrates the change, and "the class docstring is
  rewritten" is the docstring describing its own writing. The
  next sentence already IS the consumer-side rationale.
- Evidence: read verbatim (sets_mixins.py:130-133).
- Impact: bounded; self-referential change narration.
- Severity: Low.
- Recommendation: state the present shape, drop the self-history;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c "docstring is rewritten"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin`.
- Grade: process provenance (self-referential rewrite narration).
- Text-before:
  ```text
  Port of `django_graphene_filters/mixins.py::LazyRelatedClassMixin`; the ``resolve_lazy_class`` body follows upstream's resolution order with its identity reads made truthful, while the class docstring is rewritten to surface the consumer-side rationale.
  ```
- Text-after:
  ```text
  Port of `django_graphene_filters/mixins.py::LazyRelatedClassMixin`, with upstream's resolution order and truthful identity reads.
  ```

- Observation: the `RelatedSetTargetMixin` docstring opens "The
  machinery ``RelatedFilter`` / ``RelatedOrder`` grew as
  byte-parallel copies". True history (both families carried
  inline bind + resolve before `6912ca92`), but origin narration
  rather than the present sharing.
- Evidence: `6912ca92^` (inline copies in both families).
- Impact: bounded; origin where the sharing invariant belongs.
- Severity: Low.
- Recommendation: present-tense sharing; see text-after.
- Must not change: n/a.
- Proof: `grep -c "grew as byte-parallel"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten opener earns grade true. (Source wraps
  `byte-parallel` / `copies` across lines 173-174.)
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`.
- Grade: process provenance (origin narration).
- Text-before:
  `The machinery ``RelatedFilter`` / ``RelatedOrder`` grew as byte-parallel copies:`
- Text-after:
  `The machinery shared by ``RelatedFilter`` / ``RelatedOrder``:`

- Observation: `_resolved_target`'s second paragraph says the gate
  fires "exactly where the pre-hook property getters sat relative
  to this call" and claims "the same observable behavior the
  inline family gates had". "Pre-hook" and "had" narrate the
  replaced getters; the behavioral sentence between them (failed
  read leaves the slot resolved, re-raises on retry — verified
  true) is what matters.
- Evidence: the body (setattr before the gate); read verbatim
  (sets_mixins.py:219-222).
- Impact: bounded; replaced-getter comparison on a true behavior
  sentence.
- Severity: Low.
- Recommendation: keep the behavior, drop the predecessor; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "the inline family gates had"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin._resolved_target`.
- Grade: process provenance (predecessor narration).
- Text-before:
  `The family gate (``_validate_target``) fires here, AFTER the re-store, exactly where the pre-hook property getters sat relative to this call: a failed read leaves the slot resolved and re-raises on every retry, the same observable behavior the inline family gates had.`
- Text-after:
  `The family gate (``_validate_target``) fires here, AFTER the re-store: a failed read leaves the slot resolved and re-raises on every retry.`

- Observation: the `expanded_once` docstring says "The
  control-flow skeleton ... grew separately". Past-tense origin
  narration for the sharing the skeleton owns.
- Evidence: read verbatim (sets_mixins.py:363-364).
- Impact: bounded; history where the sharing invariant belongs.
- Severity: Low.
- Recommendation: present-tense sharing; see text-after.
- Must not change: n/a.
- Proof: `grep -c "grew separately"
  django_strawberry_framework/sets_mixins.py` prints `0` (2 today;
  L9 removes the other instance); the rewritten opener earns grade
  true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::expanded_once`.
- Grade: process provenance (past-tense change narration).
- Text-before:
  `The control-flow skeleton ``FilterSet.get_filters`` / ``OrderSet.get_fields`` grew separately:`
- Text-after:
  `The control-flow skeleton shared by ``FilterSet.get_filters`` / ``OrderSet.get_fields``:`

- Observation: the `should_cache_expansion` docstring says "The
  two-condition cache-write gate ... grew separately,
  single-sited beside ``expanded_once``". Same past-tense origin
  narration as L8.
- Evidence: read verbatim (sets_mixins.py:404-407).
- Impact: bounded.
- Severity: Low.
- Recommendation: present-tense sharing; see text-after.
- Must not change: n/a.
- Proof: `grep -c "grew separately"
  django_strawberry_framework/sets_mixins.py` prints `0` (2 today;
  L8 removes the other instance); the rewritten sentence earns
  grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::should_cache_expansion`.
- Grade: process provenance (past-tense change narration).
- Text-before:
  `The two-condition cache-write gate ``FilterSet.get_filters`` and ``OrderSet.get_fields`` grew separately, single-sited beside ``expanded_once`` so the string-lazy-target rule`
- Text-after:
  `The two-condition cache-write gate ``FilterSet.get_filters`` and ``OrderSet.get_fields`` share, single-sited beside ``expanded_once`` so the string-lazy-target rule`

- Observation: the `ActiveInputPermissionAttrs` docstring says
  "What used to be re-spelled on ``FilterSet`` and ``OrderSet``
  as twin thin wrappers is the family shape." "Used to be"
  narrates the pre-consolidation state.
- Evidence: both families declare one `_permission` today (no
  twin wrappers).
- Impact: bounded; history where the shape invariant belongs.
- Severity: Low.
- Recommendation: present-tense shape; see text-after.
- Must not change: n/a.
- Proof: `grep -c "What used to be re-spelled"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionAttrs`.
- Grade: process provenance (past-tense change narration).
- Text-before:
  `What used to be re-spelled on ``FilterSet`` and ``OrderSet`` as twin thin wrappers is the family shape.`
- Text-after:
  `The family shape -- what ``FilterSet`` and ``OrderSet`` would otherwise re-spell as twin thin wrappers.`

- Observation: the same docstring says "this class used to
  re-declare them field-for-field and copy them across in a
  constructor that called itself "the ONE translation"." Past-tense
  self-history quoting dead code's self-description; the live
  content is the CONTAINS relationship the next sentence states.
- Evidence: read verbatim (sets_mixins.py:540-547); the class holds
  `traversal: SetInputTraversal` today.
- Impact: bounded; dead-constructor quotation where the
  containment rule belongs.
- Severity: Low.
- Recommendation: fold the containment into one present-tense
  sentence; see text-after.
- Must not change: n/a.
- Proof: `grep -c "the ONE translation"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionAttrs`.
- Grade: process provenance (dead-code history + quotation).
- Text-before:
  `Five of its axes are not permission axes at all - they are the neutral traversal shape ``utils/input_values.py::SetInputTraversal`` already declares, and this class used to re-declare them field-for-field and copy them across in a constructor that called itself "the ONE translation". It CONTAINS that shape instead, so a sixth traversal axis is one edit rather than three plus a declaration per family, and the gate-time and apply-time classifications are the same object rather than two objects a copy keeps in step.`
- Text-after:
  `Five of its axes are not permission axes at all - they are the neutral traversal shape ``utils/input_values.py::SetInputTraversal`` already declares, and this class CONTAINS that shape instead of re-declaring it field-for-field, so a sixth traversal axis is one edit rather than three plus a declaration per family, and the gate-time and apply-time classifications are the same object rather than two objects a copy keeps in step.`

- Observation: the `_input_traversal` docstring says "this is a
  read rather than the field-for-field copy it used to be" and
  "it flows by reference exactly as before". "Used to be" and "as
  before" narrate the replaced copy; the live content (read, not
  copy; flows by reference) is verified true.
- Evidence: the body (`return cls._permission.traversal`); the
  `field_specs is` identity pins.
- Impact: bounded; replaced-copy comparison on true behavior
  sentences.
- Severity: Low.
- Recommendation: drop the predecessor comparisons; see
  text-after.
- Must not change: n/a.
- Proof: `grep -cE "it used to be|exactly as before"
  django_strawberry_framework/sets_mixins.py` prints `0` (2 today);
  the rewritten sentences earn grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin._input_traversal`.
- Grade: process provenance (predecessor narration, two clauses).
- Text-before:
  ```text
  ``utils.input_values.iter_active_fields`` consumes, so this is a read rather than the field-for-field copy it used to be.
  ```
  ```text
  ``inputs`` module mutates in place at bind time, so it flows by reference exactly as before.
  ```
- Text-after:
  ```text
  ``utils.input_values.iter_active_fields`` consumes, so this is a read, not a field-for-field copy.
  ```
  ```text
  ``inputs`` module mutates in place at bind time, so it flows by reference.
  ```

- Observation:
  `test_related_set_target_mixin_gates_resolved_targets_at_the_seam`'s
  docstring says "Regression pin for the BFS-enqueue lead: gate
  protection no longer depends on a family property getter
  re-declaring the check inline." "The BFS-enqueue lead" names a
  review artifact (process attribution), and "no longer depends"
  narrates the replaced shape. The behavioral claims (fires every
  read, hostile rejected, `None` passthrough) are verified true.
- Evidence: read verbatim (test_sets_mixins.py:320-321); the seam
  body.
- Impact: bounded; review residue + temporal on a true pin.
- Severity: Low.
- Recommendation: state the present independence; see text-after.
- Must not change: n/a.
- Proof: `grep -c "BFS-enqueue lead"
  tests/test_sets_mixins.py` prints `0` (1 today); the rewritten
  sentence (which also drops `no longer`) earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_sets_mixins.py::test_related_set_target_mixin_gates_resolved_targets_at_the_seam`.
- Grade: process provenance (review-artifact attribution + temporal).
- Text-before:
  `Regression pin for the BFS-enqueue lead: gate protection no longer depends on a family property getter re-declaring the check inline.`
- Text-after:
  `Gate protection does not depend on a family property getter re-declaring the check inline.`

- Observation:
  `test_filter_normalizer_consumes_the_family_permission_traversal`'s
  docstring ends "This replaces an assertion that a module-level
  singleton NAME was absent, which any differently-named singleton
  would also have satisfied." "Replaces an assertion" narrates the
  test's own edit history; the preceding sentences already state
  the pinned contract.
- Evidence: read verbatim (test_sets_mixins.py:799-800).
- Impact: bounded; test-history where the contract pin stands
  alone.
- Severity: Low.
- Recommendation: delete the sentence; see text-after.
- Must not change: n/a.
- Proof: `grep -c "replaces an assertion that a module-level"
  tests/test_sets_mixins.py` prints `0` (1 today); the docstring
  without the sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_sets_mixins.py::test_filter_normalizer_consumes_the_family_permission_traversal`.
- Grade: process provenance (test-edit narration).
- Text-before:
  `This replaces an assertion that a module-level singleton NAME was absent, which any differently-named singleton would also have satisfied.`
- Text-after:
  (sentence deleted; the preceding paragraph stands unchanged.)

- Observation:
  `test_filter_normalizer_honors_a_subclass_unset_sentinel_override`'s
  docstring says "The defect the derived config closes:
  ``_normalize_input`` used to read a module-level singleton
  pinned to ``UNSET`` ... Both sides now classify identically."
  "The defect ... closes", "used to read", and "now" narrate the
  fixed defect rather than the present single-grammar invariant
  (verified true: both sides classify through
  `cls._input_traversal()`).
- Evidence: both normalizer call sites; read verbatim
  (test_sets_mixins.py:819-822).
- Impact: bounded; defect-history where the invariant belongs.
- Severity: Low.
- Recommendation: state the invariant; see text-after.
- Must not change: n/a.
- Proof: `grep -cE "used to read a|now classify identically"
  tests/test_sets_mixins.py` prints `0` (2 today); the rewritten
  paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`.
- Grade: process provenance (defect-history narration).
- Text-before:
  `The defect the derived config closes: ``_normalize_input`` used to read a module-level singleton pinned to ``UNSET`` while the permission walkers read ``_permission``, so a subclass narrowing the sentinel was GATED on one grammar and FILTERED on another. Both sides now classify identically.`
- Text-after:
  ` ``_normalize_input`` and the permission walkers classify through the same derived config, so a subclass narrowing the sentinel is GATED and FILTERED on one grammar.`
  (leading space dropped; the sentence joins the preceding first
  line's paragraph.)

- Observation:
  `test_re_readable_gate_accepts_every_sized_collection`'s
  docstring says "Pinning the accepted set to ``(dict, list,
  tuple, set, frozenset)`` rejected them for a property they
  have." No committed version ever pinned builtins — the gate was
  born structural (`a8f31a2d`: `isinstance(value, Collection)`).
  "Rejected" states as history an event that never happened; the
  design point (structural over allow-list) is true.
- Evidence: `git log -S "builtin allow-list"` (no real commit);
  the `a8f31a2d` gate body.
- Impact: bounded; false-history verb on a true rationale.
- Severity: Low.
- Recommendation: counterfactual mood; see text-after.
- Must not change: n/a.
- Proof: `grep -c "rejected them for a property"
  tests/test_sets_mixins.py` prints `0` (1 today); the reworded
  sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_sets_mixins.py::test_re_readable_gate_accepts_every_sized_collection`.
- Grade: process provenance (false-history verb; the rationale is true).
- Text-before:
  `Pinning the accepted set to ``(dict, list, tuple, set, frozenset)`` rejected them for a property they have.`
- Text-after:
  `Pinning the accepted set to ``(dict, list, tuple, set, frozenset)`` would reject them for a property they have.`

- Observation: the `expanded_once` docstring justifies the
  own-`__dict__` read "so an in-flight class (the metaclass runs
  ``super().__new__`` -> ``get_filters`` before stamping
  ``related_filters``) cannot serve a half-built result." The
  parenthetical mechanism is filter-side only: only django-filter's
  `super().__new__` triggers `get_filters()` mid-creation
  (filters/sets.py:1295-1299); the order metaclass extends plain
  `type`, whose `__new__` calls nothing. The guard's protection
  holds on both sides; the stated trigger exists on one.
- Evidence: `OrderSetMetaclass(type)` (orders/sets.py:290);
  absence of any order-side creation-time `get_fields` call.
- Impact: bounded; an order-side reader learns a trigger that
  never fires there (in filter spellings, in shared prose).
- Severity: Low.
- Recommendation: scope the trigger to the filter side; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "before stamping"
  django_strawberry_framework/sets_mixins.py` prints `0` (1 today);
  the rescoped bullet earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py::expanded_once`.
- Grade: stale (filter-only mechanism stated generically).
- Text-before:
  `Read from the class's OWN ``__dict__`` (NOT ``getattr``) so a subclass never inherits a parent's completed expansion cache via MRO, and so an in-flight class (the metaclass runs ``super().__new__`` -> ``get_filters`` before stamping ``related_filters``) cannot serve a half-built result.`
- Text-after:
  `Read from the class's OWN ``__dict__`` (NOT ``getattr``) so a subclass never inherits a parent's completed expansion cache via MRO, and so an in-flight class cannot serve a half-built result (on the filter side the upstream ``super().__new__`` triggers ``get_filters()`` before ``related_filters`` is stamped).`

- Observation:
  `test_collect_related_declarations_honors_base_tombstone`'s
  docstring says "A direct base's non-related declaration removes
  a later inherited candidate." The test sets up ONE base, so no
  later base exists; "later" describes the multi-base rule (an
  earlier base's map entry shadows a later base's candidate —
  pinned by the diamond test) rather than this single-base
  degenerate case.
- Evidence: the single-base setup
  (tests/filters/test_sets.py:5939-5954).
- Impact: bounded; one word misdescribing the setup.
- Severity: Low.
- Recommendation: drop the positional; see text-after.
- Must not change: n/a.
- Proof: `grep -c "removes a later inherited candidate"
  tests/filters/test_sets.py` prints `0` (1 today); the rewritten
  first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/filters/test_sets.py::test_collect_related_declarations_honors_base_tombstone`.
- Grade: stale (positional word with no referent in the setup).
- Text-before:
  `A direct base's non-related declaration removes a later inherited candidate.`
- Text-after:
  `A direct base's non-related declaration removes the inherited candidate.`

## Rejected

- R1 — Descriptive method mood. `_active_permission_targets`
  ("Single-pass ...") joins the file's descriptive-concept
  convention. Standing precedent (connection.py Comments R1,
  exceptions.py Comments R1, keyset Comments R1) accepts
  descriptive mood on functions and rewrites nothing until a
  package-wide mood gate lands; rewriting one site here would make
  this file inconsistent with that rejection. Trigger: a
  package-wide mood gate lands.
- R2 — "Ported from" / "Port of" / "refactored" origin pointers
  (module docstring, both ported-mixin docstrings). Cross-project
  origin facts that do not rot, in the package's documented
  cribbing direction (AGENTS.md: crib from django-graphene-filters);
  verified against the cookbook source. Trigger: none (origin
  facts, fixed).
- R3 — "Used by `RelatedFilter`" (existential, no universal).
  RelatedFilter does use the mixin; the sentence claims no
  exclusivity, and the module docstring names both families.
  Incomplete without falsity is not a finding. Trigger: reworded
  as a consumer census.
- R4 — Past/continuity verbs stating present facts ("did not
  re-copy", "did not collapse", "stay distinct", "stay
  family-owned", "still derive", "still flatten"). Each names a
  construction fact or standing invariant that holds today
  (identity pins, family-owned apply), not a change. Trigger:
  none.
- R5 — Future-family framings ("future aggregates / fieldsets",
  "future AggregateSet", "a future set family"). True design
  intent grounded in the cookbook's shipped families (verified:
  `aggregateset.py`, `fieldset.py` with `AdvancedFieldSet`).
  Trigger: a family lands or the cookbook drops one.
- R6 — "Silently" contrasts (collapse, accept, re-expand to
  nothing/EMPTY). Each is a true behavioral contrast (silent
  failure vs the loud gate), verified in its body. Trigger: none.
- R7 — spec-027 / spec-028 Decision pointers (module, mixin, and
  test-module docstrings). Kept per START.md "Style". Trigger:
  spec renumber.
- R8 — "Instead of / rather than / otherwise" design contrasts
  (re-spelled tuples, re-deriving inline, two vocabularies,
  three-plus-a-declaration arithmetic). Present-tense
  rejected-alternative rationale, not change history. Trigger:
  none.
- R9 — "Every consumer's resolved target flows through" universals
  (mixin docstring, hookless-test docstring). Verified: BFS
  enqueue, both expansions, the finalizer audit, and the
  permission traversal all read the property;
  `should_cache_expansion` reads the raw slot only to test
  laziness, never to consume a resolved target. Trigger: a new
  resolved-target reader bypassing the property.
- R10 — "The cookbook's nested-permission contract"
  (`_run_permission_checks`). Verified: the cookbook delegates
  related-path checks to the child filterset (filterset.py:310).
  True. Trigger: cookbook drops the delegation.

## Cross-axis (for Mechanics)

- Observation: `__all__` omits
  `require_re_readable_field_declaration` (imported by both
  families' production modules), `is_re_readable_field_declaration`,
  and `RE_READABLE_FIELDS_HELP`, while exporting the sibling
  helper `should_cache_expansion`. Either the export list is
  incomplete (Mechanics looks-for: "`__all__` that disagrees w/
  the public surface") or the omission is deliberate and M9's
  prose narrowing stands.
- Evidence: the `__all__` tuple (sets_mixins.py:769-779) versus
  the two family import blocks (filters/sets.py:55-64,
  orders/sets.py:38-47).
- Impact: a consumer star-importing the neutral module misses the
  families' `Meta.fields` gate while getting its sibling.
- Severity: Medium (proposed; owning Mechanics pass judges).
- Recommendation: complete `__all__` (retires M9's text-before to
  true) or rule the omission deliberate (M9's narrowing lands).
- Must not change: n/a.
- Proof: `sed -n '/^__all__ = (/,/^)/p'
  django_strawberry_framework/sets_mixins.py | grep -c
  "require_re_readable_field_declaration"` prints `1` (0 today)
  when Mechanics completes the export; if the omission is ruled
  deliberate, M9's Proof arm is the landing instead.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/sets_mixins.py` `__all__`.
- Grade: stale (export list disagrees with the import surface).
- Text-before:
  (the 9-name `__all__` tuple, sets_mixins.py:769-779.)
- Text-after:
  (Mechanics decides: the tuple plus the missing names, or M9's
  narrowed test sentence with the tuple unchanged.)

## Routed leads

- Routed: `django_strawberry_framework/filters/base.py::RelatedFilter.filterset`
  — "Re-stores the resolved class so the next access is a plain
  attribute read" (filters/base.py:1148). False for the same root
  as M3 (the getter calls `_resolved_target()`, which re-fires
  the gate every read). Owner: the `filters/base.py` item.
- Routed: `django_strawberry_framework/orders/base.py::RelatedOrder.orderset`
  — the same "plain attribute read" sentence (orders/base.py:135).
  Same root as M3. Owner: the `orders/base.py` item.
- Routed (observed): both families' `RelatedFilter` /
  `RelatedOrder` "Target acceptance shapes" lists omit the
  callable-factory shape, which `resolve_lazy_class` accepts and
  `test_related_order_accepts_callable_factory` pins. Owners: the
  `filters/base.py` / `orders/base.py` items.
- Routed (observed): `django_strawberry_framework/orders/base.py`
  module docstring "after the neutral module was extracted"
  (orders/base.py:10) — provenance. Owner: the `orders/base.py`
  item.
- Routed (observed; no owning open item — Worker-0 to carry into
  `## Decisions`): `docs/GLOSSARY.md` RelatedOrder anchor
  ("`sets_mixins.LazyRelatedClassMixin` ... not `filters.base` as
  named in earlier revisions"). The resolution account is true;
  "as named in earlier revisions" is temporal. Fix is a
  glossary-DB edit plus render, outside the item fence.

Handoff: I graded every docstring and comment in the target (31
docstrings) and the own test module whole (36 docstrings), plus 22
other-test-module prose units about the target's symbols
(`other-prose.txt`): 12 Mediums (M1/M2 module counts; M3/M4
resolution once-ness; M5 ladder headline; M6 expansion once-ness;
M7 phantom order per-field naming; M8 `__all__`-string admission
universal; M9 `__all__` completeness; M10 two-vs-three rejected
shapes; M11
guard-hoist mechanism; M12 setter-path mechanism) and 18 Lows (L1/L2
class mood; L3-L16 provenance/tense across target and tests; L17
filter-only trigger stated generically; L18 positional without
referent), 10 rejections with triggers, 1 Cross-axis lead for
Mechanics (C1 `__all__` completeness, disjunctive with M9), and 5
Routed leads (the `plain read` twins to their family items, two
observed family-doc notes, one glossary temporal to Decisions).
Everything else grades true, including all 10 `path::Symbol`
citations (0 violations), the cookbook port claims (verified
against the cookbook source at the Trace fingerprints), the
four-reader gate census, both metaclass/expansion/require call
sites, the `binding_attrs` reset chain, the five-axis traversal,
and the live-test mapping. No defect (no broken contract found
while reading). No workspace runs (all instruments static);
scratch under `docs/review/temp-tests/sets_mixins/comments/`
(`inspect/`, `sets_mixins.json`, `citations-target.json`,
`citations-test.json`, `other-prose.txt`); live text equals
ITEM_BASELINE on both graded files. On verify: each Proof is a
static `grep -c`/`sed` run in the shared tree printing the stated
count with the rewritten text grading true; every prose-only file
owes `--code-digest` identity. Open thread for Worker-2: M9/C1 is
one decision with two landings (complete `__all__` vs narrow the
sentence) — the Mechanics pass owns the call; if it completes the
tuple, M9 closes with text-before true.

## Verify comments

Pass 1, run 0.0.15 2026-09-28-3. Fully static: no workspace copy bound, no
pytest. Read in order: AGENTS.md, START.md, REVIEW.md, worker-2.md, the plan
incl. run-3 scope plus Owned changes (four new ledger rows for this item),
all four records whole with every Handoff, pass-1.diff whole
(docs/review/temp-tests/sets_mixins/diff/pass-1.diff), then the live touched
files whole (sets_mixins.py lines 1-786; the four test hunks plus the seam
test, the new pin, and the two residual-vocabulary sites live).

Identity: live blobs equal the pass diff post-images on all four files, so
live == pass-1 post-image: sets_mixins.py 1f8e078d, tests/test_sets_mixins.py
8c1488d7, tests/filters/test_inputs.py 4e280999, tests/orders/test_base.py
00de6531 (git hash-object). tests/filters/test_sets.py ea6d0b04 ==
ITEM_BASELINE (L18 deferred, untouched). filters/base.py 3b1dcbce and
orders/base.py 7616b279 byte-identical to ITEM_BASELINE (ruling (c):
family property docstrings deliberately not reworded, confirmed untouched,
not flagged). Proof Transcript: docs/review/temp-tests/sets_mixins/verify-comments-1/proofs.out
(runner: proofs.sh in the same dir); every count below is from that run.

Worker-0 rulings applied: (a) C1/M3/M4 graded as ONE converged memo-world
text against the memo body, all three Proofs at 0; (b) the seam test's
first-line change on every read -> for every distinct value graded as
F1-consequential prose beyond L13's text-after; (c) family docstrings above.

Per-finding verdicts (Proof = record's grep, all re-run live):

- Perf C1: PASS. Proof `grep -c "next access is a plain"
  django_strawberry_framework/sets_mixins.py` prints 0. Landed class-docstring
  clause (sets_mixins.py:171-177: "validates it through the family gate, and
  memoizes the validated result so a repeat access of an identical value
  skips re-validation (a substituted value re-resolves and re-validates)")
  grades true against the memo body (lines 223-236: identity early-return,
  memo store only after a passed gate, failures never memoized). Judgment
  call J1 below covers the back-substitution corner.
- M1: PASS. Proof prints 0. "The three foundational mixins" true: three
  bullets follow (lines 11-20).
- M2: PASS. Proof prints 0. "lifecycle a third time" true: two package
  lifecycles (filters, orders) are the only substrate consumers per the
  record census, so a future family is the third.
- M3: PASS. Proof `grep -c "the next access is a plain"` prints 0. Converged
  text (same clause as C1) true, see C1.
- M4: PASS. Proof prints 0. Landed first line (line 215: "Resolve the
  (possibly-lazy) target class and re-store it, validating each distinct
  value once.") true: the memo fires the gate exactly once per distinct
  successfully validated value.
- M5: PASS. Proof prints 0. Ladder headline (line 138) true against the body
  (lines 155-165: strings via import_string + module fallback, callable
  non-classes via zero-arg call, everything else as-is).
- M6: PASS. Proof prints 0. Worker-2 split the record's one-line text-after
  into a first line plus paragraph (lines 364-367); both true against the
  skeleton (lines 393-403, cached-or-builds, no build-once enforcement) and
  the families' conditional cache writes.
- M7: PASS. Proof prints 0. Rescoped parenthetical (lines 109-111: order side
  mints root names only) true per the record's call census (only per-field
  call is filters/inputs.py:975).
- M8: PASS. Proof prints 0. "every shipped collection declaration shape"
  true: the "collection" scoping carves out `__all__`, which both families
  handle pre-gate.
- M9: PASS via Mech F1, NO prose edit (line 107 of tests/test_sets_mixins.py
  is byte-identical to text-before). Tuple holds all three names (each sed
  Proof prints 1); module-level enumeration finds exactly 12 public names
  (6 classes + 5 functions + RE_READABLE_FIELDS_HELP) and the tuple names
  all 12, so "names every public symbol" stands true. Strengthened test
  prose: the sentence now matches a body that pins it (dir() sweep with the
  None-arm covering the constant; fails pre-fix on exactly the 3 missing
  names by reading).
- M10: PASS. Proof prints 0. Recounted first line plus the inserted
  third-category sentence (lines 978-984) true against the 10-member tuple
  (3 one-shot + 4 text atoms + 3 non-collections; the non-collections fail
  the Collection check outright).
- M11: PASS. Proof `grep -c "hoisted from" tests/filters/test_inputs.py`
  prints 0. Landed paragraph (lines 1031-1033: guard lives in
  pascal_case_or_raise, wrapped by both consumers) true against both call
  sites (sets_mixins.py:116, filters/inputs.py:261).
- M12: PASS. Proof prints 0. Contrast parenthetical (tests/orders/test_base.py
  lines 200-202: cache write stores the slot directly, not through the
  setter) true against the body (line 230 direct setattr; the memo is a
  separate `_validated_target_memo` attr, so F1 leaves the claim intact).
- L1: PASS. Proof prints 0. Description-mood class first line (line 71),
  content preserved and true.
- L2: PASS. Proof prints 0. Description-mood class first line (line 128),
  content (minus L5's clause) true.
- L3: PASS. Proof prints 0. "families share" true: both families inherit the
  mixin today.
- L4: PASS. Proof prints 0. "matching the cookbook's per-segment split" true
  per the record's verified equivalence.
- L5: PASS. Proof prints 0. Present-shape sentence (lines 130-131) true; the
  next sentence still carries the consumer rationale.
- L6: PASS. Proof prints 0. "shared by" opener (line 171) true.
- L7: PASS. Proof prints 0. Behavior-only paragraph (lines 217-218) true:
  setattr precedes the gate (lines 230-235), failures never memoize so every
  retry re-raises.
- L8/L9: PASS. Proof `grep -c "grew separately"` prints 0 (was 2; both sites
  reworded: lines 369, 409-410).
- L10: PASS. Proof prints 0. Counterfactual shape sentence (lines 542-543)
  true: one `_permission` per family today.
- L11: PASS. Proof prints 0. Folded containment sentence (lines 545-551)
  true: the class holds `traversal: SetInputTraversal`.
- L12: PASS. Proof prints 0 (was 2). Both reworded sentences (lines 593-594,
  604-605) true against the body (`return cls._permission.traversal`) and
  the identity pins.
- L13: PASS. Proof `grep -c "BFS-enqueue lead"` prints 0; `grep -c "no longer
  depends"` prints 0. Landed sentence matches text-after. Ruling (b):
  first-line "fires from ``_resolved_target`` for every distinct value"
  (line 329) true: each distinct non-None value fires the gate once (the
  test reads once per instance over distinct values) and the None carve-out
  is explicit in the same docstring's paragraph 2. The None corner is
  inherited from the pre-existing "on every read" line, not introduced.
- L14: PASS. Proof prints 0. Sentence deleted; the standing paragraph states
  the pinned contract alone.
- L15: PASS. Proof prints 0 (was 2). Landed invariant joins the first
  paragraph as the record directed (lines 897-900); true: both sides
  classify through `cls._input_traversal()`.
- L16: PASS. Proof prints 0. Counterfactual "would reject" true: no committed
  version pinned builtins (record's git evidence).
- L17: PASS. Proof prints 0. Filter-scoped trigger (lines 373-375) true:
  OrderSetMetaclass extends plain `type`, whose `__new__` calls nothing.
- L18: DEFERRED correctly. File byte-identical to baseline (ea6d0b04); Proof
  still prints 1; no higher finding touches the file, so the ride rule
  leaves it.

F1-consequential prose beyond the records (all graded): class docstring
"every distinct value is family-checked" (line 191) true -- fires at the one
seam for every distinct non-None value, None carved out by design
(Must-not-change) and stated at `_validate_target` ("every non-None RESOLVED
target", line 242) plus the body comment (lines 231-234); the
NotImplementedError message "validates every distinct value" (line 252)
updated consistently; the memo paragraph (lines 219-221) true item by item
(identity memo, repeat reads skip re-validation, failures never memoized,
None never memoized via the `current is not None` guard).

F1-disturbance sweep (no other graded claim falsified): `_validate_target`
docstring (values quantifier, hook still sees every distinct non-None
resolved value); `_set_target` docstring ("family-checked on the next read"
-- a substituted value reaching a consumer is always a checked value, either
freshly or by memo of a prior pass; corner J1); hookless-test docstring
("fails at first resolved read" -- failures never memoized, still raises);
retry sentence; `_bind_owner`; expanded_once/should_cache/require_*/binding
chain (untouched by F1); four-reader census prose (the property path is
unchanged, only redundant work skipped); family base modules and GLOSSARY
anchor (untouched, routed). Memo attr census: exactly the two sites in
`_resolved_target` (lines 224, 236); no other reader/writer in package or
tests (one stale `__pycache__` hit only).

New pin prose
(test_resolved_target_validates_each_distinct_value_once, lines 372-379):
PASS. First line states the four pinned behaviors; the paragraph matches the
body (success-only identity memo, substitution re-validates, failures retry)
and the test legs; the deepcopy sentence ("Classes survive ``deepcopy``
atomically, so a copied memo stays valid") is true and asserted by the pin
(validations unchanged after the clone read). States behavior, no Tests-that
/Ensures, no we/you/I.

Inverse proofs: `review_inspect.py --code-digest ITEM_BASELINE:path path`
exit 0 with equal digests on both prose-only files
(tests/filters/test_inputs.py sha256:7043d980 both sides;
tests/orders/test_base.py sha256:de2e0139 both sides); exit 1 on both
code-touched files (sets_mixins.py, tests/test_sets_mixins.py) as the
discriminating control (F1 memo + `__all__` + pin + strengthened test are
the Mechanics verifier's reconstruction comparison, not this axis's).

Citations: `check_citations.py --paths <all four touched files>
--substrings` prints "OK: 15 citations resolve (15 in 4 named file(s); 0 of
them substring pinpoints)." (Record baseline was 9 + 1 on two files; the two
added test files contribute resolving cites only.)

Provenance sweep over added lines (REVIEW.md pattern plus Tests-that/Ensures
and we/you/I over the item diff's `+` lines): PROVENANCE-CLEAN. Residual
vocabulary check: the only "plain read"-family hits in touched files are
pre-existing prose in untouched symbols (tests/test_sets_mixins.py:1098
"plain attribute" about SimpleLazyObject classification;
tests/orders/test_base.py:210 "resolves and caches on first access" -- still
true under the memo, which makes "caches" literal); both outside verify scope
and both still true, noted only.

Lint (read-only): `ruff check` "All checks passed!" and `ruff format --check`
"4 files already formatted" on the four touched files. Three added lines run
103-105 chars (M5 first line, L6 opener reflow, M4 first line), all within
the 110 E501 grace for lines the formatter cannot break; RUF022 (`__all__`
order) is in select and green. `__all__` placement note for the Mechanics
verifier (non-blocking, that axis's call): the constant landed first rather
than between RelatedSetTargetMixin and SetLifecycleAttrs as the Mechanics
record prescribed; the ordering gate is green either way.

Judgment calls: J1 -- re-substituting the memoized identity back through
`_set_target` hits the memo and skips a redundant re-validation of an
already-validated value (the Perf record's "never identical to the memo"
model treats it as outside the real-path population; verdict-inert either
way, since the memo holds only passed values). J2 -- "every distinct value"
is read with the file's own explicit None carve-outs (same shape as the
pre-existing "every read" lines it replaces).

Handoffs obeyed: Perf (deepcopy leg landed in the pin; family rewording
NOT applied per ruling (c)); Mech (re-fingerprinted before grading);
Comments (M9/C1 closed through the completed tuple with text-before true,
no prose edit; L18's file untouched).

Status: verified (open threads: none)
