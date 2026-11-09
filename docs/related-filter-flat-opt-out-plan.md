# Item 216 plan v7: a per-declaration opt-out for flat RelatedFilter copies

Status: PLAN v7. HEAD `1462297f` (`main`). Process: `docs/bug_hunt/FIX.md`. **Blocked on tracker item 748,** whose fix
walks raw-form `RelatedFilter` heads through `FilterSet._flat_leaf_walk`, the walk D2's restored-own-key routing rows
describe; R1 re-derives those rows against it. 745 (ruling 6) is the GlobalID audit this plan builds on. 749 landed
without rewriting the walk: it hands the walk the path Django walks for a leaf
(`filters/base.py::_filterset_walked_lookup`).
- v1 was reviewed at `8d47f31f` (REVISE). The v1 review is in the repository's docs folder.
- v2 was reviewed at `a3c97aa4` (REVISE).
- v3 was reviewed at `703d538a` (REVISE, Sonnet High).
- v4 was reviewed at `703d538a` (REVISE, sol).
- v5 was reviewed at `45e6a15d` (REVISE, sol).
- v6 was traced at `1462297f` by two Haiku agents (holes) and one Sonnet High agent (reuse). v7 folds in their
  findings, marked "(v6 trace)" and "(v6 reuse)".
- Defaults marked "(vN review)", "(v6 trace)" or "(v6 reuse)" are reviewer recommendations, not maintainer rulings.
  Where AGENTS.md or GOAL.md settles a point, the plan cites it instead of asking.
- **Rebase.** Since `45e6a15d`, items 537, 538, 673, 680 and 681 landed in `filters/base.py`, `inputs.py`, `sets.py`,
  spec-027 and `test_raw_filter_forms_api.py`. The v6 trace found no cited expansion symbol changed. R1 re-pins every
  citation at the base it starts from (745 landed).

## Rulings so far (maintainer)

1. **The default stays on.** This item adds the opt-out tracker item 216 asks for; the bound landed in `47dd4daa`.
2. **Per-declaration only:** `RelatedFilter(flat=False)`. There is no global setting.
3. **`MAX_FLAT_FILTERS` keeps today's net key-growth accounting,** documented precisely.
4. **The empty-branch spec contradiction is tracker item 729,** under "To do: found along the way".
   - It was filed as 728 at first, but CHANGELOGTODO already uses 728.
   - FIX phase 8: a new item takes the next number unused in both files.
   - It closes with the separate relation-quantifier plan.
5. **Out of scope:** relation-existence operators (729 / the quantifier plan) and any nested-path cost work.
6. **(2026-11-03) The GlobalID audit correction is tracker item 745, and it lands before 216.** A correct audit must
   follow runtime routing (`_leaf_chain`, `_bound_terminal`, undeclared-hop re-entry) for wired sets too, and must skip
   consumer decoders (`_decodes_before_binding`). 216 may not ship a gap with a follow-up card (AGENTS root-cause
   rule), so it builds on 745's audit and changes no GlobalID code (D3).
7. **(2026-11-03) The copy-probe completion gap is tracker item 746.** It predates `flat=False`. D3's coverage claim is
   parity with HEAD.

Items 729, 745, 746 and 748 to 757 were filed in `26ab8295`. This plan is committed so the item's next agent starts
from v7; the landing commit deletes it.

## Fact finding (FIX phase 2, recorded)

- **Repro.** A dense `RelatedFilter` cycle is refused by `MAX_FLAT_FILTERS`. Below the cap, every declaration
  expands, and no lever exists between that and raising the cap.
- **History.**
  - `47dd4daa` added the cap, the per-build expansion memo and pipeline-only copying.
  - `7a86c0fe` added re-entrant surface reuse.
  - Item 61 set the path-relative stop; item 217 is the extra lap on subclass entry.
- **Upstream.**
  - django-filter has no recursive `RelatedFilter` expansion, only explicit `Meta.fields` relation paths.
  - django-graphene-filters builds expanded tables but leaves them out of connection arguments.
  - djangorestframework-filters resolves related parameters per request.
  - None of them offers a per-declaration flag. This package's surface is its own.
- **Split out (rulings 6 and 7).** The GlobalID and copy-probe probes are recorded in items 745 and 746. At HEAD the
  GlobalID shape fails only nonempty framework-decoded values; `exact: []` and `exact: null` succeed.
- **Raw-form heads skip visibility, tracker item 748 (v6 trace, verified 2026-11-03).** A raw-form `RelatedFilter`
  head, own or copied, is not walked, so it skips the target type's `get_queryset` and the declaration's `queryset=`
  scope that walked keys get. Probe on the shipped library schema, anonymous request:
  - `BookFilter` `shelf=<secret shelf pk>` returned the book on the hidden shelf; `shelf__code=<its code>` returned
    none.
  - `BranchFilter` `shelves__books__shelf=<secret shelf pk>` (a copied head) matched through a shelf outside
    `shelves`' `queryset=`; `shelves=<pk>` refused it as "Select a valid choice", and `shelves__code` excluded it.
  - GraphQL cannot name a head. 216 neither introduces nor widens this: a disabled declaration only withdraws copied
    heads. D9's raw-form head row uses visible rows only, so it pins nothing 748 changes.

## The defect

- `RelatedFilter` declarations are expanded at schema build into flat copies of each target's path-relative,
  reshaped contribution.
- A dense graph grows factorially. The cap refuses it; a consumer has no lever except raising the cap.
- `HIDE_FLAT_FILTERS` hides copies from the schema but still builds and counts them.

## D1: `RelatedFilter(filterset, *args, flat: bool = True, **kwargs)`

- **Signature (v6 trace, v6 reuse).** `flat` is keyword-only. A positional extra would fall into django-filter's
  `Filter.__init__(field_name, lookup_expr, ...)`, which `RelatedFilter` forwards. As a named parameter it never
  reaches `**kwargs`, so `Filter.__init__` cannot absorb it into `extra`. No `kwargs.pop` is needed.
- **Validation.** `truth.is_exact(flat, bool)`, else `ConfigurationError` with `truth.describe(flat)`, inline as
  `extensions/error_policy.py` validates `ErrorPolicy.enabled`. No shared bool validator exists, and none is added.
  Placeholders are validated too.
- **Read-only.** Stored as `self._flat` before `super().__init__` (the `_has_explicit_queryset` precedent) and exposed
  by a bare `@property` with no setter. A post-build flip would leave `_expanded_filters` stale.
  - The value survives deep copy, pickling and the metaclass's copy of a borrowed declaration. The v4 prototype and
    the v6 trace both confirmed it.
- **Not shared with `RelatedOrder` (v6 reuse).** `OrderSet.get_fields` copies no target table (D7), so the flag would
  mean nothing there. It does not go on `sets_mixins.py::RelatedSetTargetMixin` (AGENTS: add only what the feature
  needs).
- **Inheritance follows the declaration object** (`django_strawberry_framework/sets_mixins.py::collect_related_declarations`,
  unchanged).
  - A redeclared attribute is a new object with its own value.
  - In a diamond with mixed flags, the first base wins in `related_filters`, `declared_filters`, `base_filters` and
    the published head.
  - An attribute tombstone (`attr = None`) removes the edge.
  - `RelatedFilter(None)` is the placeholder (`.filterset is None`). It expands nothing. A subclass that binds a target
    does so by redeclaring the attribute, so the new object's `flat` applies. The rows pin that case.
- **Rows** (package construction, `tests/filters/`):
  - one parametrized invalid-`flat` row beside `tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg`:
    `1`, `"x"`, `None`, a `bool` subclass, and the placeholder `RelatedFilter(None, flat="x")`;
  - a positional third argument does not set `flat`;
  - assignment to `flat` refused;
  - redeclaration, mixed-flag diamond and borrowed declaration, reusing the `BaseFilter` / `RemovedFilter` /
    `KeptFilter` / `CombinedFilter` shape of
    `tests/filters/test_sets.py::test_filterset_metaclass_none_removal_survives_diamond_inheritance`.

## D2: the copy rule (operational)

- **An enabled declaration** copies its target's path-relative, reshaped contribution, as today.
- **A disabled declaration suppresses only that expansion operation.** The skip is `if not f.flat: continue` in
  `FilterSet._expand_along`, after `_require_relation_path` and `_require_correlated_target` and before
  `filters.update(...)`. `_require_correlated_target` still resolves lazy targets.
  - (v6 reuse) `_expand_along` is the only reader of `flat` in the package. Restored own keys, the HIDE direction and
    zero growth all follow from not calling `filters.update`; no restore helper is written.
- **The target's own filters stay eligible contributions,** explicit `Meta.fields` traversals included.
  - Example: over a disabled `B.books`, A's enabled `shelves` still yields `shelves__books__title` from B's own
    traversal.
  - The gate path still walks the declared hops.
- **Copied terminal heads survive.** The item 217 extra lap survives unless a disabled declaration sits on the lap,
  in which case the lap is cut.
- **Copied `RelatedFilter` heads stay as they are:** in the table and the direct form, and out of GraphQL.
  `_group_filters_by_head` skips `__` heads.
- **Re-keyed copies keep their provenance** (`PatronFilter.borrowed_title`).
- **Disabling restores a replaced own key.** When an enabled copy replaces an own key, the copy holds that key.
  Disabling the declaration gives the key back to the own filter, with its complete behavior. This is django-filter
  running the consumer's own filter (AGENTS: upstream behavior is asked, not re-derived):
  - its value when the key is omitted (a checkbox's `False`, a disabled initial);
  - `required`;
  - its widget, its `lookup_expr` and `exclude`;
  - its routing. An ordinary restored filter keeps declared-hop scoping, because `_flat_leaf_walk` reads behavior and
    ORM path, not flatness.
  - (v6 trace) A restored filter holding its own `filter` (`method=`, or a callable its `__init__` stores) is never
    walked: `_flat_leaf_walk` returns `None`, so `_visibility_hops` and `_leaf_gates` are empty. Its callable runs on
    the parent queryset with no relation gate and no target visibility. GOAL's trust boundary settles this: a
    `method=` is trusted consumer code, and an own `method=` filter that no copy replaces behaves the same at HEAD.
    The docs state it.
- **The omission case.** An enabled copy is unnamed and deferred (`FilterSet.__init__` defers only
  `snapshot.deferred_copies`), so its omitted value does not act. A restored own checkbox's omitted `False` does act,
  so `filter: {}` can return different rows.
- **HIDE.** Under `HIDE_FLAT_FILTERS=True` the key changes from a hidden copy to a shown own lookup
  (`inputs.py::_visible_entries` reads `_is_flat_copy`).
- **Rows (v6 reuse: `flat in {True, False}` parameters of existing builders; expected values hand-written per
  cell).**
  - Package tier: `tests/filters/test_sets.py::_absence_periodical_filter` over `_issue_filter_whose_absence_filters`
    (its `_ABSENCE_SHAPES` cover checkbox, disabled initial, consumer filter, consumer widget and null choice), and
    `_required_child_branch_filter` gaining a `flat` argument.
  - Live tier: `examples/fakeshop/test_query/test_filter_absence_api.py::_absence_schema` gaining `flat` and `own`
    arguments, and `test_projected_owned_filters_api.py::_own_world` for the own-`filter` row. R1 checks each seed fits
    the three-parent shape (child true, child false, no child).
  - The cells:
    - an ordinary restored `CharFilter`: the same membership, multiplicity (one parent through two matching
      children) and one SQL statement under both flags;
    - a checkbox key omitted: `flat=True` returns all three parents, `flat=False` the child-false parent only;
    - (v6 trace) the checkbox key supplied `true`: the child-true parent only, under both flags;
    - a `required=True` own filter omitted: `flat=True` returns all three parents, `flat=False` returns
      `FILTER_INVALID` naming the key with "This field is required.";
    - an own `CharFilter(method=...)` selecting a different row than the child's ordinary filter: `flat=True` returns
      the child copy's row, `flat=False` the method's row;
    - (v6 trace) the same method row with a child row hidden by the target's `get_queryset` and a
      `check_<rel>_permission` gate: `flat=True` excludes the hidden row and fires the gate; `flat=False` matches the
      hidden row when the method selects it and fires no relation gate;
    - (v6 trace) an own walked key with `exclude=True` over a child filter without it: `flat=False` negates at the
      parent (`_apply_relation_leaf`), with the expected rows per flag;
    - (v6 trace) an own key with `lookup_expr="iexact"` over the copy's `exact`: a mixed-case value matches only
      under `flat=False`;
    - (v6 trace) an own multi-key widget (`RangeWidget`): only its suffixed keys bind under both flags; a bare key is
      ignored;
    - HIDE publication of the key under both flags.
- **Expected surfaces, written independently:** filter table keys, direct form fields and served SDL. Cases:
  - all enabled (today exactly);
  - one disabled;
  - disabled under enabled;
  - own traversal across a disabled declaration;
  - a two-set cycle with each edge disabled in turn;
  - subclass entry, with and without a disabled lap edge;
  - the Patron override.

## D3: validation that expansion supplies today (implementation constraint)

### Deep-copy probe

- **Where (v6 reuse).** Inside the existing loop in `FilterSet.get_filters::_build_in_scope` that already calls
  `target._filter_table()` for each retained target. The loop iterates `.items()` to keep the attribute name, keeps
  the returned table, and, for a disabled declaration, probes each entry with `not _is_flat_copy(target, f)`.
  - It is the third caller of `filters/base.py::copied_declared_filter`, which owns the refusal text, `__cause__` and
    `via` rendering. No message builder is added.
  - `via = f"{truth.qualname(path[-1])}.{filter_name}"` is hoisted from `_expand_related_filter` into one helper
    (`_declaration_via`), so "(reached through RelatedFilter Owner.attr)" has one spelling.
  - `_expansion_record(f) is None` is wrong as the predicate: a filter a `get_filters()` override borrows keeps its
    record but is the borrowing set's own (`_is_flat_copy` docstring).
- **Mid-build targets are probed (v6 trace).** v6 skipped a target mid-build at the loop. At HEAD that target's own
  entries are probed by its enabled copy; with the copy gone, the skip drops them. The trace's cycle matrix (a
  three-set ring, all eight disabled subsets, three roots; a two-set cycle, four subsets, two roots) missed own probes
  in 16 of 32 rows with the skip and in none without it. A direct build of an unwired cyclic set then raised a raw
  `TypeError: cannot pickle '_thread.lock' object` on first use where HEAD raised `ConfigurationError` at build.
  - The probe therefore runs for a disabled declaration whatever the target's build state. The publish loop's own
    mid-build skip stays.
  - R1 confirms reading a mid-build target's `_filter_table()` there starts no re-entrant build and returns its own
    entries.
- **Work unit.** One disabled declaration per declaring-set build. Two disabled declarations into one set probe its
  own entries twice, which is accepted.
- **Coverage claim: parity with HEAD (ruling 7).** Every own entry HEAD probes, through subpass 1.5 or an enabled
  declaration's expansion copy, is still probed under any flag combination. Entries HEAD never probes (item 746) stay
  unprobed; 216 neither fixes nor widens that gap. The trace confirmed parity for nested (enabled then disabled), lazy
  string targets, and override-added entries under an incoming edge.
- **Enabled declarations keep the expansion probe unchanged.**
- **One target reached through both a disabled and an enabled declaration** names `via` by build order. Rows assert
  the set and attribute, not `via`.
- **Rows (v6 reuse: parameters of existing tests).**
  - `tests/filters/test_finalizer.py::test_finalize_refuses_a_related_child_filter_a_deep_copy_refuses` is
    parametrized over `flat`, keeping its "(reached through RelatedFilter BookFilter.shelf)" pin, and gains the
    borrowed-head parameter (a `get_filters()` override borrowing a donor filter under `shelf__branch`). It reuses
    `_InstanceLockHolder` and `_shelf_filter`.
  - (v6 trace) Cycle rows, direct builds of an unwired cyclic set: the two-set cycle with the lock on the root and the
    back-edge disabled, refused naming the disabled edge's `via`; the same with the lock on an override-added root
    entry.
  - (v6 trace) The nested row: wired W, enabled into A, A disabled into B, lock on B, refused naming `A.<attr>`.
  - (v6 trace) A disabled declaration with an invalid target (no `Meta.model`, or an uncorrelated model) still
    raises its `ConfigurationError` at build.

### GlobalID encode-only audit: built on 745 (ruling 6)

- 216 changes no GlobalID code and no GlobalID docstring or spec text.
- **Precondition, stated for R1 to verify (v6 trace).** As 745 lands it, the audit
  (`types/finalizer.py::_audit_globalid_filter_strategies`) asks every set `filters/inputs.py::_served_reach` yields
  from a wired set: the wired set, then each set reached through a branch the table publishes (the declared
  `RelatedFilter` head, or a flat copy `HIDE_FLAT_FILTERS` does not hide), not every declaration
  `_reachable_filtersets` follows. Each GlobalID entry of a reached set's table is resolved where a request decodes it
  (`filters/sets.py::FilterSet._globalid_decode_sites`, the routing `_leaf_chain` runs: declared hops, an undeclared
  hop's face and re-entry included); a projected copy is asked in its child set, and entries that do not decode before
  binding (`_decodes_before_binding`) are skipped. It refuses naming the wired set and the request key, identically
  under both flags, with the landed template: `filterset <Wired> serves GlobalID filter '<request key>'
  (<DeclaringSet>.<name>, reached through RelatedFilter <Set>.<attribute>, then ...) targeting <Type>, whose globalid
  strategy is '<strategy>'.` for a reached leaf, `filterset <Wired> declares GlobalID filter '<key>' targeting <Type>,
  ...` for an own one. R1 re-derives the rows against this reach, including whether a `flat=False` declaration's
  target set is still reached. If a later change moves the identity rule or the reach, R1 stops and the plan is
  revised.
- **Rows (v6 reuse: a `flat` parameter on 745's rows, no new Book/Shelf/Branch world):**
  - the declared-hop callable-strategy shape: refused under both flags with the same message;
  - the undeclared-hop re-entry shape: refused under both flags with the same message;
  - a consumer `method=` decoder on the same key: admitted under both flags.

### Already correct, unchanged

- `_audit_unregistered_related_filter_targets` walks every declaration transitively.
- `reject_captured_branches` and `_target_reaches` recurse declarations, so a captured branch is refused whether the
  inner edge is enabled or disabled (the trace ran four cases). `_filter_paths` also yields `Meta.fields` leaves; the
  refusal holds because `_target_reaches` recurses declarations (v6 trace corrects v6's reason).

### Walker table (v6 trace corrections)

| Walker | Follows |
|---|---|
| `FilterSet._expand_along` | The only reader of `flat`. Validates every declaration, copies enabled ones. |
| `_expand_related_filter`, `_filters_along` | Unchanged callees. `_expand_related_filter` takes one declaration; `_filters_along`'s reach test reads all. |
| `_reachable_filtersets` | Unchanged: all declarations (v3 review). R1 measures build cost on the seven-set graph with reverse edges disabled (v6 reuse: disabled edges keep every set reachable, which can defeat `_filters_along`'s `target._filter_table()` shortcut). A visible cost restricts it through the same `flat` read, pinned by a structural row (`_expand_along` call count or `scope.surfaces` size). Its docstring's "as `FilterSet._expand_along` does" is corrected. |
| `FilterSet.get_filters` target-publication loop | All retained targets, plus the disabled-declaration probe, mid-build targets included. |
| `reject_captured_branches` / `_target_reaches` | All declarations. |
| `should_cache_expansion` | Every declaration, disabled included: a disabled lazy target still blocks caching. |
| Finalizer registered-target audit | All declarations, unchanged. |
| Finalizer GlobalID audit | As 745 lands it (precondition above). |
| `GeneratedInputArgumentsFactory._ensure_built` | Every non-`None` declaration. |
| `filters/inputs.py::_build_input_fields` (`_related_of`), input grouping and emission | Unchanged: all declarations; `__` heads skipped. |
| `_flat_leaf_walk`, `_leaf_chain`, `_bound_terminal`, `_leaf_declaration`, `ChildProjection.holds_in` | Unchanged: routing of supplied keys over declared hops, whatever the flag (D2's restored-own-key routing). |
| `walk_declared_relation_path`, gates, projected-leaf walks | All declarations on an active supplied path. |
| Active-input permission, nested visibility, related-constraint recursion | All active branches, including logical arms. |
| Lifecycle clearing | All classes. |

## D4: direct django-filter / DRF use

- On a disabled declaration, the automatically generated keys are withdrawn.
  - A key an own filter registers is unaffected, and D2's restored-own-key behavior applies.
  - An unregistered key is ignored, as django-filter does and `DjangoFilterBackend` inherits (AGENTS: upstream
    behavior is asked).
- **Documentation only.** spec-027's `HIDE_FLAT_FILTERS` paragraph and the `conf.py` HIDE comment both end "a
  form-data client can still send a flat key". Both get "on an enabled declaration".

## D5: `HIDE_FLAT_FILTERS`, unchanged

- It hides what is built. See D2 for the restored-own-key direction.

## D6: `MAX_FLAT_FILTERS`, today's accounting, documented

- **The budget is net key growth per expansion call** (one set along one path, or a set as root):
  `len(filters) - own > scope.limit`, checked in `_expand_along`, the only raise site, after each contribution is
  built.
- **What it counts and excludes:**
  - It excludes the call's initial own population.
  - A copy replacing an own key adds zero.
  - Copied heads count.
  - (v6 trace) A `get_filters()` override's additions on the set itself are outside the budget: the count is taken in
    `_expand_along` before the override runs. A parent counts them only when it copies them.
  - It is not a total allocation or whole-schema bound.
- **Each set is checked on its own.** A retained target behind a disabled declaration builds and is capped on its
  own.
- **Failure atomicity and retry are as today.** A child's snapshot can be published while the failed root has none.
- **Message (v6 trace: exact template; v6 reuse: only the tail changes).** The prefix stays byte-identical:
  `FilterSet {qualname(path[0])}: its RelatedFilter expansion publishes more than {limit} flat filters, crossed
  expanding {qualname(cls)}.{filter_name} along {trail}.` `trail` already ends with `cls`. The tail
  "Raise DJANGO_STRAWBERRY_FRAMEWORK['MAX_FLAT_FILTERS'], or declare fewer RelatedFilter edges in the cycle." becomes:
  `Mark {qualname(cls)}'s RelatedFilter declarations flat=False, or raise
  DJANGO_STRAWBERRY_FRAMEWORK['MAX_FLAT_FILTERS']; a target behind a flat=False declaration still builds on its own.`
  - The remedy names `cls`, the crossing set, which differs from the reported root on an inner path.
  - The source and `tests/filters/test_sets.py::_flat_limit_message` change together; the helper stays independently
    spelled.
- **Rows (v6 reuse: `tests/filters/test_sets.py::_desk_ring` gains `disabled: Collection[str] = ()`, with one
  independent expected table per disabled edge; cap rows are parameters of
  `test_a_set_whose_expansion_passes_max_flat_filters_fails_its_build`, which already carries both HIDE settings and
  the failure and retry assertions):**
  - zero, the exact boundary, one over (the trace measured cap 8 admits, cap 7 refuses);
  - a copy replacing an own key;
  - a copied head with no GraphQL field;
  - acyclic fan-out;
  - a retained disabled target over its own cap;
  - the three-set ring at cap five: disabling the reported root's only declaration still refuses, naming Desk as root
    and `Desk.shelf` (trace confirmed);
  - root failure after a child publishes, then a retry;
  - `flat=False` bringing a refused graph under the cap (trace: cap 5, `desk.shelf` disabled, admitted);
  - (v6 trace) an override adding keys past the cap on the root itself is admitted, pinning the documented exclusion.

## D7: ordering, unchanged

- `OrderSet.get_fields` copies no target table, and spec-028 Layer 4 gets one sentence.
- A shared-helper edit owes ordering preservation rows.

## D8: copy-once, out of scope

- BACKLOG card with the prototype numbers, labelled "unverified, recipe not retained".

## D9: fakeshop and live coverage

- **The shipped fixture.** AGENTS: test through real usage, prefer the example project. Every shipped library cycle
  edge feeds live flat-key tests, so no shipped edge can be disabled. Add a new cycle:
  - `ReadingListFilter.entries = RelatedFilter("ReadingListEntryFilter", field_name="entries")`, enabled. (v6 trace)
    The string spelling is required: `ReadingListFilter` is defined first, so a class reference raises `NameError`.
  - `ReadingListEntryFilter.reading_list = RelatedFilter(ReadingListFilter, ..., flat=False)`, disabled.
  - The own traversal: `ReadingListEntryFilter.Meta.fields` gains `"reading_list__title": ["exact"]`.
    - The entry set keeps `readingListTitle` as its own key across the disabled declaration.
    - The list set gains `entriesReadingListTitle` from it.
    - This is also the live replaced-own-key case.
  - The withdrawn key for the ignored-key row is `reading_list__id`, which only the disabled copy would register.
  - The trace found no collision and no full-SDL snapshot test. R1 measures the SDL diff at its base and lists the
    tests reading either input type.
- **Live rows in `examples/fakeshop/test_query/`, with HTTP requests:**
  - the disabled copies are absent from the served SDL;
  - the nested `readingList` branch executes;
  - the enabled `entriesTitle` flattens and executes;
  - `readingListTitle` (own) and `entriesReadingListTitle` execute;
  - `readingListTitle`'s operator bag has `exact` only; the disabled copy would have added the target's `iContains`.
    The row asserts the bag's exact field set;
  - the `flat`-into-`extra` mutant is request-reachable (a disabled branch finalizes, and the first request builds
    the form field), so a request across the ReadingList branch kills it.
- **Form-data rows** in `examples/fakeshop/test_query/test_raw_filter_forms_api.py`, through a generalized
  `_split_widget_schema(mode)` taking the parent filterset (v6 reuse). R1 names a non-Postgres host, since the
  current builder is `pg`-marked for `SplitArrayWidget`.
  - A raw `reading_list__id` is ignored and both candidate entries return.
  - The copied terminal head: a raw key under an enabled declaration's copied head filters the expected rows, over
    rows every viewer sees. Hidden-row behavior of heads is item 748's.
- **Patron:** both source edges stay enabled. A live `borrowedTitle` query with matching and non-matching rows proves
  the alias executes.
- **Visibility, gates and async-only hooks.** The ReadingList types provide none of these.
  - These rows run on `examples/fakeshop/test_query/test_filter_publication_api.py::_ring` / `_ring_schema`, which
    gain the same `disabled` knob (v6 reuse). Variants with `get_queryset`, a `check_<rel>_permission` gate and an
    async-only hook come from `strategy_schemas.make_django_type(meta_extra=, namespace_extra=)`, not hand-written
    types. Async needs an async resolver and `AsyncDjangoGraphQLView`.
  - The two rings (`_desk_ring` in `tests/`, `_ring` in `test_query/`) stay separate, one per tier.
- **Placement by reachability.**
  - Static refusals go in package construction tests under `tests/filters/`: the invalid `flat`, the deep-copy
    refusals, the GlobalID rows and the cap, all raised at declaration or build. No request reaches them.
  - Valid publication, execution and request-time behavior go in `test_query/`, the D2 live cells included.
  - A refusal that a real raw-form request reaches names that host and asserts its HTTP behavior.
  - Existing unrelated tests are not reorganized.
- **Named expectations:** sync/async, visibility, gates, exact query counts. The database-alias row runs on one node
  id under `FAKESHOP_SHARDED=1`.

## Must preserve (named rows in the expectation grid)

- **Item 61.** `tests/filters/test_sets.py::_path_walk` gains a disabled-declaration `continue`, placed before its
  `target is not None` assert so a disabled placeholder does not fail the walk (v6 trace). It reads
  `declaration.flat` itself and calls no package helper: it stays an independent oracle (v6 reuse). It gets bounded
  registration permutations, including subclass entry. The existing order tests stay. Custom `get_filters()` surfaces
  keep their own expected tables.
- **Item 217 (v6 trace).** No test pins the subclass extra lap today. A characterization row lands in the parent
  column of the grid first: for the parent and subclass shapes, the subclass's two extra names
  (`books__shelf__books__title`, `books__shelf__books__shelf` in the trace's probe). The disabled-lap rows follow.
- **Item 601:** unchanged.
- **The absence rule and pipeline-only laziness:** unchanged on enabled declarations.
- **All-enabled schemas:** every finalize refusal and message the base raises (HEAD plus 745), GlobalID and deep
  copy included.
- **Disabled declarations:** every GlobalID refusal the all-enabled schema raises, with the same message; every
  deep-copy refusal HEAD raises, with a `via` naming a real declaration.
- **Request-time rows:**
  - database alias (sharded node id), callable `queryset=` with the request;
  - async-only visibility outside the sync boundary;
  - error precedence and paths;
  - recursion limits;
  - membership and multiplicity;
  - optimizer cooperation;
  - exact query counts.

## Research (R1, `opus-high`, private clone, after 745 lands)

- **Rebase.** Every cited symbol, docstring, pin and test at the base; items 537, 538 and 681 against D2 and D3.
- **Deep copy.** The mid-build probe starts no re-entrant build; the probed-entry sets equal HEAD's on the trace's
  cycle matrix, the nested shape and the borrowed head. The probe's build-time cost.
- **`_reachable_filtersets` cost.** The seven-set graph with reverse edges disabled, paired, warmed, alternated
  against the all-enabled graph.
- **GlobalID precondition.** D3's statement against 745's landed audit, with all three rows.
- **Fixture.** The ReadingList SDL diff, and the existing tests that read either input type.
- **Hosts.** The D2 builders' seeds fit the three-parent shape; a non-Postgres raw-form host.
- **Stop rule.** R1 measures. A counterexample to any mechanism in D2, D3 or D6 stops R1, which reports it for a plan
  revision instead of designing around it.

## Implementation and verification (FIX.md, in full)

- **Implementer:** `opus-medium`, private clone.
- **Verifier:** `opus-high`, the same verifier every round, expectations written before reading the diff.
- The full FIX brief applies:
  - a failability manifest and an expectation-first parent/change grid;
  - basedpyright main and floor, and the public-type check;
  - the suppression check (no growth);
  - the citation, source-layout and generated-doc checks;
  - pre-commit on the changed paths;
  - an orphan sweep over all four test trees;
  - the Python 3.10 floor run last.
- **Shared expected strings.** Test helpers (`_flat_limit_message`, `_copy_refusal`) stay independently spelled and
  are shared only across `flat` parameter values, never with the source (v6 reuse).
- **Mutations to kill.** Each is classified as a valid-schema failure (killed by a live publication or execution
  row), a construction failure (killed by a construction row), or equivalent (documented, with no unpinned branch).
  - a disabled declaration still expands (valid schema);
  - an enabled one is skipped (valid schema);
  - the deep-copy probe is skipped for a disabled declaration (construction);
  - the probe uses record absence instead of `_is_flat_copy` (construction, by the borrowed row);
  - (v6 trace) the probe skips mid-build targets (construction, by the cycle rows);
  - (v6 trace) the probe runs only in the root build, not nested publishes (construction, by the nested row);
  - (v6 trace) the skip moves above `_require_relation_path` / `_require_correlated_target` (construction, by the
    invalid-target row);
  - the GlobalID audit reads only copies, so a disabled declaration escapes it (construction, by the D3 rows);
  - the cap is bypassed or its accounting changed (construction, plus a valid-schema row at the boundary);
  - an own traversal key is lost (valid schema);
  - a copied terminal head is dropped (valid schema, by the raw-form row);
  - a restored own key loses its omitted-value behavior (valid schema, the checkbox cell);
  - a restored own `method=` filter is walked as a hop (valid schema, the method cells);
  - `flat` leaks into `extra` (valid schema, by the live ReadingList request);
  - `flat` becomes assignable (construction);
  - if R1 restricts `_reachable_filtersets`: the restriction removed (structural row; output-equivalent).
- **CPU budget:** node ids only, one foreground run at a time, `-n 2` at most, no whole-file `test_library_api.py`,
  no coverage sweep. Full suite, coverage, matrix, shard and Postgres run in Actions.

## Docs and bookkeeping (one landing commit)

- **Canonical homes (v6 reuse).** Each fact is stated once; every other site gets one clause and a `path::Symbol`
  pointer.
  - The consumer contract of `flat=False`: the `RelatedFilter` docstring, mirrored once in the GLOSSARY
    `RelatedFilter` term and in `docs/README.md`.
  - The path rule and cap accounting: the `FilterSet.get_filters` docstring and spec-027 Decision 3 Layer 4. The raise
    site's accounting goes in the `_expand_along` docstring.
  - Who probes what for deep copy: the `copied_declared_filter` docstring, one clause naming its three callers.
- **Pointer sites:**
  - spec-027: the `HIDE_FLAT_FILTERS` paragraph's last sentence; the `MAX_FLAT_FILTERS` paragraph and remedy (the
    override exclusion included); Decision 6's deep-copy probe; the Subpass 1.5 checklist line ("probed by its
    expansion copy" becomes "probed where its declaration is built"); the "Circular RelatedFilter cycles" edge case
    (one clause, "except through a declaration marked `flat=False`, which copies nothing"); Test plan and DoD get
    test-file pointers only.
  - Checks: the spec-027 rationale companion; spec-051's flat-copy mention and its two test citations; spec-031
    Decision 13 and spec-027 Decision 6, as 745 left them, assume no copies exist.
  - spec-028: the Layer 4 sentence.
  - `types/finalizer.py::_audit_filter_copies` and `_bind_filtersets`: "probed by its expansion copy" becomes "probed
    where its declaration is built, see `filters/base.py::copied_declared_filter`".
  - `filters/sets.py::_reachable_filtersets`: it follows every declaration, `flat=False` included.
  - `filters/sets.py::_expand_related_filter`: only if `_declaration_via` is hoisted from it.
  - `conf.py`: the HIDE comment (D4) and the `MAX_FLAT_FILTERS` comment naming `flat=False` as a remedy.
- **Consumer docs:** `docs/README.md` gets the opt-out, reachable from the root README. It says:
  - flat and nested differ in meaning, so `flat=False` removes a capability;
  - direct-form keys are ignored on a disabled declaration;
  - own traversals stay;
  - a restored own key brings back its full behavior: omitted values, `required`, `lookup_expr`, `exclude`, the HIDE
    direction, and a `method=` running on the parent with no relation gate or target visibility (D2);
  - a `get_filters()` override reading a copied key silently loses its alias when a declaration it depends on is
    disabled;
  - clients must regenerate their schema.
- **Generated docs:** GLOSSARY through the kanban DB, TREE, both KANBAN renderers where DB rows change, and every
  generator check.
- **Test docs:** the `examples/fakeshop/test_query/` README map, and TODAY's capability line if it names the
  expansion.
- **CHANGELOGTODO.md:** one item, with the next number unused in both files. It covers `MAX_FLAT_FILTERS` (from
  `47dd4daa`) and `RelatedFilter(flat=)`. No CHANGELOG edit.
- **BACKLOG:** remove `related_filter_flat_opt_out`; add the copy-once card.
- **Tracker:**
  - move 216 from "Waiting on you" to Done with a one-line outcome;
  - recheck that items 729, 745, 746 and 748 to 757 still read accurately;
  - delete this plan file (`docs/related-filter-flat-opt-out-plan.md`);
  - update Progress counts;
  - recheck numbers and concurrent edits when landing.

## Risks

- **D2's exemptions** (own traversals, terminal heads, re-keyed copies, restored own keys). The independent expected
  surfaces are the only guard.
- **The 745 dependency.** 216 cannot start R1 until 745 lands. If 745's audit does not meet D3's precondition, the
  plan is revised, not shipped with a gap.
- **Mid-build probing** reads a table during a build. R1 proves it is not re-entrant before implementation.
- **`_reachable_filtersets` cost** on dense graphs with disabled reverse edges. R1 measures it.
- **Rebase drift.** 745 will touch the finalizer and the GlobalID resolvers. R1 rechecks every citation first.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
