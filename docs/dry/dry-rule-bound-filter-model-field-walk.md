# DRY review: `bound-filter-model-field-walk`

Status: verified
Run: 0.0.15 2026-10-09-13

Item kind: FAMILY (responsibility family). Verdict CONFIRM +
BLOCKED: the bound-filter model walk (parent -> `_meta.model`)
has two authoritative definitions at filter time (count 2 on
the walk and model-absent axes), but site 1's walk line
carries an uncommitted hunt hunk (the truth migration's
`truth.static_attr` rewrite, with the twin line named
outstanding in the hunt's own TR104 report), so the
consolidation is `blocked-on-hunt` with the migration
specified and zero edits. The `field_name` half of the pair
is an intentional strict-vs-lenient separation, and six
further candidates are excluded with contract difference +
trigger each. Zero defects.

## System trace

The target owns the derivation a live-`field_name` filter
resolves its model against: the owning filterset's model,
reached from the bound filter through its `parent` link
(`FilterSet._bound_terminal`'s docstring states the contract:
a terminal copy's `parent` "is" what it resolves its model
and owner against). The rule varies on binding state only
(bound with a model vs unbound / model-less); the read is
otherwise unconditional.

Two authoritative definitions spell the walk at filter time,
both in `django_strawberry_framework/filters/base.py`:

- Site 1, `IntegerInFilter.filter` (WT :705-712, HEAD
  :738-745): `parent = getattr(self, "parent", None)` ->
  `_meta` -> `model`, then `get_model_field(model,
  _bound_field_name(self))` when a model is present. The
  resolved field feeds `_coerce_int_in_members`.
- Site 2, `_relation_identity_column_for` (WT :1276-1284,
  HEAD :1314-1322): `parent = getattr(filter_instance,
  "parent", None)` -> `_meta` -> `model`, then
  `relation_identity_column(get_model_field(model,
  field_name))` with a lenient `None` / falsy guard. Its own
  docstring claims "the same walk `IntegerInFilter.filter`
  uses".

At HEAD the parent -> `_meta` -> model lines are
byte-identical modulo `self` vs `filter_instance`. In WT
they differ by exactly one hunt hunk: site 1's `_meta` line
was migrated to `truth.static_attr` (WT :708) while site 2's
twin (WT :1279) still spells plain `getattr` and is named
outstanding in the hunt's own `check_truthful_reads.py
--report` output (TR104, report-only). The WT split is
in-flight concurrent work, not a second rule.

Consumers of the two definitions: site 1's field feeds the
`__in` member coercion inside the same method (1 consumer);
site 2 feeds `_coerce_relation_identity` (1 caller), which
feeds both `RelationPkFilter.filter` and
`RelationPkMultipleFilter.filter` (2 callers). Both sites
also serve rebound terminals: `_bound_terminal` stamps a
synthetic `parent` (`_projection_child` or
`_UndeclaredHopSet`) on a shallow filter copy without
touching `.model`, and `_UndeclaredHopSet`'s docstring names
"a raw-key or integer terminal" as coercing through its
`_meta.model` - so the parent root (not the queryset-stamped
`filter_.model`) is load-bearing for exactly these two
consumers.

Oracles (all spell literal expectations, never computed from
the walk): `tests/filters/test_base.py` pins the unbound
passthrough of each site (`test_integer_in_filter_unbound_and_missing_model`
asserts `IN (1, 2)` SQL text;
`test_unbound_relation_pk_filters_apply_the_value_uncoerced`
asserts row lists) plus the bound coercion/drop behavior and
the `_bound_field_name` raise; live
`examples/fakeshop/test_query/test_scalars_api.py` pins the
bound `__in` coercion through real queries
(`test_filter_specimens_by_bigint_in_drops_past_64bit_members_no_overflow`
and siblings); live `test_scalars_filter_api.py` pins the
bound relation-key path
(`test_scalars_filter_by_non_relay_pk_in_list`,
`test_scalars_filter_by_forward_fk_primary_key_exact_and_in`).

Projections: site 2's "the same walk" docstring sentence;
`_model_field_for_filter`'s docstring cross-reference ("the
same `__`-separated relation traversal ... already use");
`_bound_field_name`'s "bound filter's `field_name` is a
string" invariant; spec-027's surface rows naming
`IntegerInFilter` as a reroute (never the walk). All
describe; none defines.

Excluded on the strength of their bodies (full records under
Findings): `filters/inputs.py::_model_field_for_filter`
(class root at build time),
`filters/sets.py::FilterSet.get_fields` per-field `"__all__"`
expansion (direct class-root read at class-definition time),
`filters/sets.py::FilterSet._leaf_chain` to-many key
derivation (hop-record root at plan time), the
`filter_.model` upstream read (wrong root for rebound
terminals), the parent -> `_owner_definition` slot (a
different rule), and the projected-child parent delegation
(parent used as the set instance, not a model source).

Upstream grounding (installed django-filter 26.1, Django
6.1.2 - each matching its `uv.lock` resolution for this
interpreter; the lock also pins Django 5.2.18 below the
`python_full_version >= '3.12'` marker):
`BaseFilterSet.__init__` stamps
`filter_.model = queryset.model` plus `filter_.parent =
self` on every per-request copy (`filterset.py`), where the
queryset defaults to the declared model's manager but may be
explicitly passed; `FilterSetMetaclass` defaults every
declared filter's `field_name` to its attribute name
(`filterset.py:94-97`); `Filter.__init__` defaults
`field_name` to `None` with no `model` / `parent` class
defaults, so the `getattr`-with-default reads are
load-bearing for unbound filters. This package passes
explicit same-model `queryset=constrained` at
`filters/sets.py:4711` / `:4835`.

## Verification

### Matrix

1. **Cross-flavor policy mirroring** - searched. No
   `get_model_field` call exists outside `filters/`
   (package-wide grep census under Enumeration: 5 calls, all
   inside the three indexed files). `forms/sets.py::_resolve_model`
   reads `Meta.form_class._meta.model` (a form-class root,
   different family, no bound filter, no parent). Orders,
   mutations, rest_framework, types hold no bound-filter
   walk. No second flavor of this rule.
2. **Sync/async twins** - inapplicable with reason. Both
   sites run inside django-filter's synchronous
   `Filter.filter` / form-validation path; binding
   (`BaseFilterSet.__init__`) is sync-only upstream, and
   no async twin of either consumer exists: the `.parent`
   census homes every parent-rooted read in `filters/`,
   and none falls inside the 5 `async def` bodies in
   `filters/sets.py` (`:3417`, `:3479`, `:3894`, `:4012`,
   `:4904`). No await boundary crosses the rule.
3. **Derived rather than repeated knowledge** - searched;
   the walk IS this axis's item. The `__`-path traversal is
   single-owned upstream (`get_model_field`; the 5 package
   calls are consumers). `_bound_field_name` is single-owned
   in base.py (5 callers: site 1 plus 4 in sets.py). Every
   other `_meta.model` read in `filters/` is a direct
   single-attribute read on a class, hop record, or target
   set - no second parent-rooted walk (census under
   Enumeration).
4. **Inverse / round-trip pairs** - searched, no shared
   rule. Generation runs the opposite direction
   (`filter_for_field(field, field_name, ...)` builds a
   filter FROM a field at class-definition time), but the
   halves meet only at the opaque `field_name` string and
   the single-owned `get_model_field` primitive - no shared
   grammar to own, no inverted walk to unify.
5. **Contracts restated in another medium** - searched.
   Production: the 2 definitions. Oracles: the named tests
   above, verified literal (SQL text, row lists, raised
   codes) - none computes an expectation from the walk or
   from either definition. Projections: the docstrings and
   spec-027 rows named above. Count every medium a walk
   change moves: 2 definitions + 0 oracles (all pass through
   unchanged: the consolidation is behavior-preserving) + 1
   projection sentence (site 2's "the same walk" claim moves
   to the helper).
6. **Enforcement by omission** - enumerated the runtime
   filter classes with a model-field need. Walk holders:
   `IntegerInFilter` (site 1), the `RelationPk` pair via
   site 2. Deliberate non-holders, each with a contract
   reason: the `GlobalID` pair resolves through
   `DjangoTypeDefinition` (`_target_definition_for` - type
   names, not model fields); `IntegerRangeFilter`
   decomposes to `gte` + `lte` (needs no field);
   `ListFilter` / `ArrayFilter` / choice / range siblings
   apply lookups without resolving a field. No contract
   source (spec, glossary anchor, owner prose, oracle)
   establishes a walk any member lacks: no defect, no
   omission.

### Enumeration

Instrument: `grep -rn "get_model_field"
django_strawberry_framework/ --include='*.py'` (source
only; `__pycache__` excluded) plus `grep -rn "\.parent\b"`
over `filters/*.py` and a `_meta.model` read census over
`filters/`. No third walk site exists outside the indexed
files - or inside them beyond the pair.

- `get_model_field`: 11 source hits = 3 imports (one per
  indexed file) + 5 calls + 3 prose mentions. Every call
  homed: site 1 + site 2 (F1, the counted pair),
  `inputs.py:1321` (R-inputs), `sets.py:2093` (R-getfields),
  `sets.py:4237` (R-leafchain).
- Parent-rooted model walks: exactly 2 (F1). Other `parent`
  reads cleared by body: parent -> `_owner_definition`
  (`base.py::_target_definition_for`, 1 + 1 prose cite at
  `sets.py:2998` - R-ownerdef); parent used as the set
  instance (`ProjectedChildFilter._child` / `filter`,
  `sets.py:1274-1275` / `:1295` - R-projected).
- Direct `_meta.model` single-attribute reads (no parent,
  no walk; cleared by shape): hop-record roots
  (`_hop_model` :1505, `_hop_source_model` :1521), the
  synthetic face assignment (`_UndeclaredHopSet` :1540),
  declaration-time class reads (`_require_relation_path`
  :1563, `_require_correlated_target` :1603-1604),
  metaclass / apply-pipeline class reads (`sets.py:1894`,
  `:1903`, `:2224`, `:2531`, `:3047`, `:3257`, `:3353`,
  `:3797`, `:3965`), and the target-class seed read
  (`RelatedFilter.get_queryset`, `base.py:1592`). Each
  reads the attribute off a subject already in hand; none
  derives a model from a bound filter.
- `_bound_field_name` callers: 5 (site 1 at `base.py:711`
  plus `sets.py:1057`, `:1454`, `:1513`, `:1561`) - the
  strict `field_name` rule is already single-owned;
  R-fieldname records why site 2 does not share it.

### Challenges

Authoritative definitions only; consumers, oracles,
projections listed, never counted. All static-reviewed
(HEAD-vs-WT body inspection, installed-upstream reads,
grep populations); no ordering, transactional, or async
behavior is decided here.

- **C-walk: parent-binding change** (django-filter stops
  stamping `.parent`, the package moves to an explicit
  binding record, `_meta` access changes shape) -> site 1 +
  site 2 = 2. The family count.
- **C-absent: model-absent policy change** (an unbound /
  model-less filter must raise instead of the lenient
  `None`) -> site 1's `if model is not None else None` +
  site 2's `if model is None ... return None` = 2. Same
  lenient contract, two spellings.
- **C-strict: strict `field_name` policy change** (the
  `_bound_field_name` raise moves) -> `_bound_field_name`
  = 1, carrying its 5 consumers including site 1
  (intended - one rule). Site 2's inline lenient arm does
  not move: different contract (R-fieldname).
- **C-lenient: lenient `field_name` policy change**
  (site 2's falsy-`field_name` -> `None` arm moves) ->
  site 2 alone = 1. No second lenient spelling exists.
- **C-classroot: class-root `_meta` access change** ->
  `inputs.py:1314-1315` = 1, `sets.py:2085` = 1,
  `base.py:1592` = 1, each alone. Three single-attribute
  reads on three different subjects - no shared walk
  beyond "the model lives at `_meta.model`", which is
  django-filter's contract, single-owned upstream.
- **C-primitive: `get_model_field` swap** -> 5 call sites
  move by construction = 0 definitions. Calls are
  consumers of the upstream definition, never counted
  (the `_bound_field_name` 5-caller precedent agrees).

Consumers following a C-walk consolidation by
construction: `_coerce_relation_identity`, both `RelationPk`
`filter` bodies, site 1's coercion arm. Oracles following
unchanged: the unbound/coercion/live pins named above.
Projection moving: site 2's "the same walk" sentence (to
the helper).

## Findings

### F1 - bound-filter model walk (CONFIRMED duplication, blocked-on-hunt)

- **Contract + variation.** From a bound filter, resolve
  the owning filterset's model: `filter.parent` ->
  `_meta.model`, lenient `None` when unbound or model-less.
  Varies on binding state only. The downstream `field_name`
  sourcing is NOT part of this contract: strict
  (`_bound_field_name`, raise) at site 1, lenient (falsy ->
  `None`) at site 2 - an intentional separation
  (R-fieldname).
- **Sites + roles.** Site 1 (`IntegerInFilter.filter`,
  WT :705-712, HEAD :738-745): definition (walk half) +
  consumer (of `_bound_field_name`, `get_model_field`).
  Site 2 (`_relation_identity_column_for`, WT :1276-1284,
  HEAD :1314-1322): definition (walk half) + consumer (of
  `get_model_field`, `relation_identity_column`). Upstream
  `get_model_field`: the authoritative path-traversal
  definition both consume. Tests: independent oracles (see
  trace). Docstrings / spec-027 rows: projections.
- **Challenges.** C-walk = 2, C-absent = 2 (above).
  C-strict / C-lenient / C-classroot / C-primitive each <=
  1, confirming the duplication is exactly the walk +
  model-absent halves.
- **Owner + lifetime.** `filters/base.py`: both consumers
  live here; `inputs.py` and `sets.py` already import from
  `base`, so hosting elsewhere would reverse a dependency
  (principle 7; dependency direction wins). No stored
  derivation - pure, "not cached" (principle 4).
- **Migration (specified, unlanded - blocked).** Add
  `_bound_filterset_model(filter_instance: Filter) ->
  type[models.Model] | None` in `filters/base.py`
  adjacent to `_bound_field_name`: the parent ->
  `_meta.model` walk with the lenient `None` contract.
  Site 1 replaces WT :705-709 with `model =
  _bound_filterset_model(self)`, keeping `_bound_field_name`
  + `get_model_field` + the coercion arm byte-identical.
  Site 2 replaces WT :1276-1280 the same way, keeping
  its lenient `field_name` read (:1281-1282) +
  `get_model_field` + `relation_identity_column`
  byte-identical. Site 2's "the
  same walk" sentence moves to the helper's docstring with
  the R-fieldname / R-modelattr / R-inputs / R-getfields /
  R-leafchain trigger clauses. Oracles unchanged (the
  consolidation is behavior-preserving on every input -
  proof below). The helper's `_meta`-read spelling adopts
  the LANDED hunt spelling (see Coupling): it must be one
  spelling, and the correct one is the hunt owner's call.
- **Distinct behavior.** The `field_name` None-policy
  split stays: site 1 refuses a consumer-rebound filter
  (`ConfigurationError`), site 2 passes it through
  (`None`); the split is reachable only when a bound
  filter carries `field_name = None`, which upstream's
  metaclass defaulting + the package's generation make a
  consumer programming error (R-fieldname). The helper
  never reads `filter_.model` (wrong for rebound
  terminals - R-modelattr).
- **Behavioral proof.** Static-reviewed: post-migration,
  each site computes the identical `model` value on every
  input (same parent, same `_meta` read, same `None`
  leniency) and every downstream line is untouched, so
  observable behavior - short-circuit order, exceptions,
  querysets - is identical by construction; no ordering /
  transactional / async behavior is decided here. The
  wrong result each oracle rejects: unbound passthrough
  turning into a crash or a constraint (both unbound
  tests), coercion silently widening (live `__in` / raw-pk
  suites). Execution of the suite green post-migration is
  `execution-deferred` (see Pending execution).
- **Structural gate (specified, unlanded).** Post-hunt
  landing owes an exact-match census test pinning exactly
  ONE parent -> `_meta.model` derivation in `filters/base.py`
  with both runtime consumers calling it by name.
  Negative control: revert one call site to an inline
  walk - the census fails (count 2) while every behavior
  oracle stays green (the copy is correct), proving the
  gate guards singularity, not behavior.
- **Coupling.** Blocked on the hunt landing the `_meta`
  read at site 1 (exact hunk below); the family stays open
  until then. If the hunt lands with the two `_meta`
  spellings still split (TR104 is report-only, so green
  does not preclude it), the helper's spelling choice is a
  maintainer decision owed before landing - the two
  spellings agree on every standard filterset and differ
  only under a hostile metaclass, which is the migration's
  own threat model. No other coupling.
- **Freshness.** `filters/base.py`: WT `77c2e7a6` (= full
  `77c2e7a64a4f580537ed96b0f2538d59b064cf2d`), HEAD
  `a43513a7`, ITEM_BASELINE `77c2e7a6` (== WT; baseline
  commit `a7f364af` taken at dispatch on `23b5f421`).
  `filters/inputs.py`: WT `a269a3fe`, HEAD `d77a113c`,
  ITEM_BASELINE `a269a3fe` (== WT). `filters/sets.py`: WT
  `9428aba9`, HEAD `b8740187`, ITEM_BASELINE `9428aba9`
  (== WT). Searched populations: package-wide
  `get_model_field` (11 hits, all read), `filters/` parent
  / `_meta.model` reads (all homed above),
  `tests/filters/test_base.py` (135 tests, all green),
  live `test_scalars_api.py` / `test_scalars_filter_api.py`
  (named nodes read), spec-027 (2 mentions, surface-only),
  installed django-filter 26.1 (`filterset.py` binding +
  metaclass, `filters.py` `Filter.__init__` +
  `LookupChoiceFilter.get_lookup_choices`) and Django 6.1.2
  (each matching its `uv.lock` resolution for this
  interpreter). Excluded modules read in full:
  none outside `filters/` - the mechanism census proves
  no site exists there.

Blocking hunk (hunt-owned truth migration; `git diff HEAD`
on `django_strawberry_framework/filters/base.py`):

```text
@@ -738,7 +705,7 @@ class IntegerInFilter(BaseInFilter, NumberFilter):
         # django-filter's ``BaseFilterSet.__init__`` stamps ``filter_.parent = self`` and its
         # metaclass stores ``_meta = FilterSetOptions(...)``.
         parent: BaseFilterSet | None = getattr(self, "parent", None)
-        meta: FilterSetOptions | None = getattr(parent, "_meta", None)
+        meta = cast("FilterSetOptions | None", truth.static_attr(parent, "_meta", None))
         model: type[models.Model] | None = getattr(meta, "model", None)
         model_field = (
             get_model_field(model, _bound_field_name(self)) if model is not None else None
```

Site 2's region (WT :1268-1284) is clean versus HEAD - no
hunk touches it - but the consolidation must rewrite site
1's walk to compose the helper, so the item touches
nothing. The hunt's own `--report` names site 2's twin
line outstanding (`base.py:1279:37: TR104
`getattr(x, "_meta")` asks the object; use
truth.static_attr`), confirming the split is in-flight
work with its home already assigned.

### R-inputs - `_model_field_for_filter` (REJECTED, class root at build time)

Contract difference: takes the `FilterSet` class and reads
`filterset_cls._meta.model` directly (WT :1288-1321, HEAD
:1243-1276), running once under `_build_input_fields`
during `finalize_django_types()`; the counted pair roots at
a bound filter's `parent` instance at filter time. Posit a
parent-binding change -> the pair moves, this helper does
not (0); posit a class-root change -> it alone moves
(C-classroot). Different roots, different lifetimes.
Trigger (the owed C2): a shared (model, field-path)
resolution seam spanning build and filter time. Durable
home: its docstring already carries the relationship note;
the trigger clause lands in the F1 helper docstring with
the migration.

### R-getfields - `get_fields` per-field `"__all__"` expansion (REJECTED, class-dict root)

Contract difference: reads `model = cls._meta.model`
directly (WT :2085, HEAD identical region) and walks
`field_name` values from the upstream fields dict at
class-definition time (call at WT :2093, HEAD :2066 - the
C1 site; the `:1548` number predates rebases and is
stale). No bound filter exists at this seam, so no parent
walk is possible. Trigger: the expansion walking from a
bound filter instance instead of the class fields dict.
Durable home: F1 helper docstring trigger clause, with the
migration.

### R-leafchain - `_leaf_chain` to-many key derivation (REJECTED, plan-record root)

Contract difference: recovers model and relation from plan
records (`_hop_source_model(hops, ...)` +
`_hop_relation(last)`, WT :4222-4237, HEAD :4200) at
query-plan time; no live filter's parent is consulted (the
method RECEIVES the filter but resolves the key from the
hops). Trigger: leaf-chain planning threading live bound
filters instead of hop records. Durable home: F1 helper
docstring trigger clause, with the migration.

### R-fieldname - strict vs lenient `field_name` sourcing (REJECTED, intentional separation)

Contract difference inside the pair: site 1 delegates to
the single-owned `_bound_field_name` (raises
`ConfigurationError` on `None` - a consumer-rebound
filter is refused, per its docstring and
`test_bound_field_name_refuses_a_filter_with_no_path`);
site 2 reads leniently (`getattr` + falsy -> `None`,
passed through uncoerced). Unifying either way changes
observable behavior on the bound-but-fieldless input
(raise vs passthrough) with no oracle covering it on
either side - not behavior-preserving, out of scope for a
consolidation. Trigger: a behavior decision unifying the
bound-filter `field_name`-None policy (raise-everywhere or
lenient-everywhere), owned by the maintainer with a contract source.
Durable home: F1 helper docstring separation clause, with
the migration.

### R-modelattr - upstream `filter_.model` (REJECTED, wrong root)

Contract difference: `filter_.model` is stamped from the
construction queryset (`BaseFilterSet.__init__`) and goes
stale for rebound terminals (`_bound_terminal` reassigns
`parent` and `field_name` on a shallow copy without
touching `.model`); `_UndeclaredHopSet` documents raw-key
and integer terminals - exactly these two consumers -
coercing through `parent._meta.model`. Reading `.model`
would resolve the walking set's model instead of the hop
target's. Upstream's own `get_model_field(self.model,
...)` consumer (`LookupChoiceFilter.get_lookup_choices`)
never runs on rebound copies. Trigger: a guarantee that
stamped `.model` always equals `parent._meta.model` for
every filter these sites serve (contradicted today by
`_bound_terminal`'s documented contract). Durable home:
F1 helper docstring "why not `filter_.model`" clause, with
the migration.

### R-ownerdef - parent -> `_owner_definition` (REJECTED, different slot)

Contract difference: `_target_definition_for`
(`base.py:770-806`) reads the finalizer-bound
`DjangoTypeDefinition` off the parent for GlobalID
type-name validation - a definition-resolution rule, not a
model-field walk. Same `parent` root, disjoint slot and
downstream. Trigger: the two parent-derived slots merging
into one record. Durable home: none owed beyond this
record (the slot owner already documents its contract).

### R-projected - projected-child parent delegation (REJECTED, parent as instance)

Contract difference: `ProjectedChildFilter._child` and
`filter` (`sets.py:1269-1275`, `:1294-1296`) use the parent
AS the filterset instance (delegating to
`_projection_child` / `_apply_relation_leaf`), never as a
model source. Trigger: projected leaves resolving model
fields through the parent. Durable home: none owed beyond
this record.

## Defects

None found while tracing. Checked and cleared: site 2's
"the same walk" docstring claim (true at HEAD; WT-divergent
only by the in-flight hunt hunk, whose home is assigned -
not a defect); the `get_model_field` `RuntimeError` on
unresolved lazy relations (unreachable at filter time -
apps are populated - and identical at both sites, so no
asymmetric guard is owed); axis-6 omission sweep (no
contract source establishes a missing walk).

## Pending execution

- `proof: uv run python scripts/workspace.py run
  dry/boundwalk-f60/consolidate -- pytest
  tests/filters/test_base.py -n0 --no-cov -q` (discharges
  F1's behavioral proof once the block clears: the unbound
  passthrough, coercion/drop, identity-column, and raise
  pins green post-migration; validated runnable at
  baseline - 135/135 green in the shared tree this run;
  runnable for verdict only after the unblocked
  consolidation lands).
- Sharded cell: `unverified` but `inapplicable by
  construction` (Worker-2 judges): the walk is a pure
  derivation (bound filter -> model -> field) touching no
  database, alias, or dialect decision; the owner body and
  both call sites hold no `using=`, no alias read, no
  backend branch.
- Postgres cell: `unverified` but `inapplicable by
  construction` (Worker-2 judges): same reason - no SQL,
  no parameter binding, no dialect branch in the rule.

## Judgment

CONFIRM-blocked. The bound-filter model walk is one rule
with two filter-time definitions (C-walk = 2, C-absent =
2); the `field_name` halves are an intentional
strict-vs-lenient separation, and the remaining
`get_model_field` / parent / `_meta.model` spellings are
each excluded on a re-derived contract difference with a
trigger. Owner re-derived as `filters/base.py` (dependency
direction; both consumers local). The migration -
`_bound_filterset_model` beside `_bound_field_name`, both
sites composing by name, field contracts untouched - is
specified byte-exactly but unlanded: site 1's walk line is
hunt dirt, recorded hunk-exact above. Zero edits, zero
defects, one validated proof entry, both cells claimed
inapplicable with reasons for Worker-2's judgment.

## Implementation (Worker-1)

No tracked changes (blocked-on-hunt, zero edits by rule -
see the blocking hunk under F1). No `## Owned changes`
rows, no new tests, no spec/doc updates owed (no behavior
changed; the "same walk" projection moves only with the
migration). No ruff runs owed (no `.py` touched);
`check_public_types.py` not run (no public symbol
touched).

Evidence runs (all through `heavy`, machine GREEN at
dispatch and before the run set, `pgrep` clean then,
`heavy` serializing the set):

- Focused proof validation (the entry's one authorized
  shared-tree run): `heavy uv run pytest
  tests/filters/test_base.py -n0 --no-cov -q` -> 135
  passed in 5.76s.
- Type gates as tree-state (zero edits, so these record
  the tree, not a change): `heavy uv run basedpyright` ->
  0 errors, 0 warnings, 0 notes; `heavy uv run
  basedpyright -p pyrightconfig.floor.json` -> 0 errors, 0
  warnings, 0 notes; `heavy uv run python
  scripts/check_truthful_reads.py --check` -> 120 files
  checked, errors 0 (`--report` additionally names site
  2's twin line outstanding TR104, cited under F1).
- No `workspace.py` copy created (no source-mutating proof
  exists for a zero-edit item); the `proof:` entry above
  runs at this address after the block clears.

Worker-0 transcriptions: index row `bound-filter-model-field-walk`
-> status `open, blocked-on-hunt (F1 CONFIRMED count-2,
migration + census gate specified, zero edits)`; no new
index rows (R-fieldname / R-modelattr separations live in
the F1 record and the specified helper docstring); Families
queue item stays open pending the unblock.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (own target reads +
package-wide sweeps only; header verdict + section titles
seen, finding bodies not).

Rule posited: BOUND-filter model-field walk -- a filter
instance bound to a `FilterSet` resolves its set's model via
`parent -> _meta.model`, then its field via
`get_model_field(model, field_name)`.

Sweep populations (own instruments, WT bytes):

- `get_model_field` call sites package-wide: 5 --
  `filters/base.py` x2 (`IntegerInFilter.filter`,
  `_relation_identity_column_for`),
  `filters/inputs.py::_model_field_for_filter`,
  `filters/sets.py` x2 (`get_fields` `"__all__"`
  expansion, `_leaf_chain`).
- `getattr(*, "parent", ...)` package-wide (`--include='*.py'`):
  10 hits -- 4 DRF serializer-converter (other family),
  3 `ProjectedChildFilter` (parent-as-instance delegation,
  no `_meta` walk), 3 `filters/base.py` (the two walk
  sites + `_target_definition_for`).

Definitions of the walk (count 2, both in `filters/base.py`,
both runtime/filter-time):

- D1 `filters/base.py::IntegerInFilter.filter` -- parent
  -> meta -> model -> `get_model_field(model,
  _bound_field_name(self))`; strict `field_name` (None
  raises `ConfigurationError`); model-None arm falls
  through to uncoerced `super().filter`.
- D2 `filters/base.py::_relation_identity_column_for` --
  parent -> meta -> model -> `get_model_field(model,
  field_name)` inside `relation_identity_column`; lenient
  `field_name` (falsy -> None); model-None arm returns
  None.

Change challenges (own):

- C-walk: change how a bound filter reaches its model
  (e.g. `getattr(parent, "_meta")` ->
  `truth.static_attr(parent, "_meta")`). D1 + D2 both move
  -> count 2. This change is literally in flight: the hunt
  migrated D1's line and left D2's twin on `getattr` --
  live drift, count-2 evidence.
- C-absent: change the unbound-filter verdict (parent None
  / model None). D1 and D2 each encode "no model" on their
  own arm -> count 2.
- C-terminal: change `get_model_field` None/error
  semantics. All five call sites compose django-filter's
  owner by name -> count 1, not duplication.

Owner I would choose: `filters/base.py` module scope (both
definitions already live there; narrowest cohesive owner;
no dependency reversal). Shape: one helper owning the
filter -> model walk (parent -> `_meta.model`, None when
unbound), D1/D2 composing by name; the strict-vs-lenient
`field_name` guards stay at the call sites (intentional
separation: raise vs None).

Excluded on my trace (contract difference in one clause
each; triggers owed by whoever records them):

- `inputs.py::_model_field_for_filter`: root is a
  filterset CLASS at build time, not a bound instance's
  parent; first hop differs.
- `sets.py::get_fields` + `sets.py::_leaf_chain` terminals:
  model already in hand; `get_model_field` only, no walk.
- `base.py::_target_definition_for`: parent ->
  `_owner_definition`, different slot, no model/field.
- `base.py::RelatedFilter.get_queryset`: class ->
  `_meta.model` -> `base_queryset`, different terminal.
- `sets.py::ProjectedChildFilter` parent reads: parent as
  instance delegation, no `_meta` walk.
- `rest_framework/serializer_converter.py`: DRF serializer
  parent, other family.
- Upstream `filter_.model`: not examined on my trace (no
  such attribute found on django-filter `Filter` in my
  sweep; reconcile against the artifact if claimed).

Block assessment (own): REAL. D1's `meta = ...` line is
`truth.static_attr` + `cast` dirt vs HEAD (hunk content =
the hunt's truth migration); `## Owned changes` carries no
row for `filters/base.py` (only `filters/sets.py` f51
depth-cap rows, which name no walk line), so the hunk is
external by the ledger rule. Any walk consolidation
rewrites D1's walk lines by construction (composition by
name); no re-route avoids it (a one-site migration leaves
count-2: owner + inline copy). Zero-edit outcome stands.

(Reconciliation with `## Findings`, gate re-runs, and
verdict follow below under `## Iterations` (pass 1).)

## Iterations

### Pass 1 (Worker-2) - reconciliation, gate re-runs, verdict

Reconciled every difference between my pre-findings trace
and `## Findings` explicitly:

- Definitions: AGREE, count 2 (D1 == site 1, D2 == site 2;
  both `filters/base.py`, both filter-time).
- Challenges: AGREE on C-walk = 2 and C-absent = 2. W1's
  C-strict / C-lenient / C-classroot subdivide ground my
  trace covered as exclusions + the call-site separation;
  each confirms the duplication is exactly the walk +
  model-absent halves. C-primitive: W1 counts 0
  in-population definitions (calls consume upstream); I
  counted 1 (upstream owns). Same verdict, no package
  duplication; I adopt W1's in-population convention.
- Owner: AGREE, `filters/base.py` module scope. W1's
  dependency-direction clause corroborated: both
  `filters/sets.py` and `filters/inputs.py` already
  `from .base import` (incl. `_bound_field_name`), so no
  reversal either way and both definitions are local.
- Shape: AGREE. One helper owning filter -> model
  (parent -> `_meta.model`, lenient None);
  strict-vs-lenient `field_name` guards stay at the call
  sites (R-fieldname). Verified the migration's
  preservation claims against the bodies: site 1 uses only
  `model` downstream (WT :710-720), site 2 only `model` +
  `field_name` (WT :1281-1284); the `parent` / `meta`
  locals have no other reader at either site, so deleting
  them is safe. Line ranges exact (site 1 WT :705-709,
  site 2 WT :1276-1280).
- Block: AGREE, REAL. Independently re-derived: D1's
  `meta = ...` line is `truth.static_attr` + `cast` dirt
  vs HEAD (hunt truth migration by content); `## Owned
  changes` carries no row for `filters/base.py` (only the
  f51 depth-cap rows on `filters/sets.py`, which name no
  walk line), so the hunk is external by the ledger rule.
  Composition by name must rewrite D1's walk lines; a
  one-site migration leaves count-2 (owner + inline
  copy), so no re-route exists. Zero-edit stands.
- Blocking hunk: byte-exact. Header
  `@@ -738,7 +705,7 @@` + all 8 lines match
  `git diff HEAD` output exactly (own capture). Site-2
  region clean: own hunk-header census (17 hunks, none
  spanning WT 1268-1284) confirms.
- TR104: corroborated in my copy
  (`check_truthful_reads.py --report` names
  `base.py:1279:37: TR104` outstanding) - the split is
  in-flight hunt work with its home assigned.
- Rejections (7): each carries contract difference +
  trigger (read all). R-inputs / R-getfields /
  R-leafchain / R-ownerdef / R-projected match my
  exclusions clause for clause. R-fieldname matches my
  call-site separation (raise vs None). R-modelattr I had
  not traced; verified all four sub-claims after reading:
  upstream stamps `filter_.model = queryset.model` +
  `filter_.parent` (`filterset.py:196-209`, installed
  django-filter 26.1); `_bound_terminal` reassigns
  `field_name` + `parent`, never `.model`
  (`sets.py:4149-4174`); `_UndeclaredHopSet` docstring
  names raw-key/integer terminals coercing through
  `parent._meta.model` (own pre-findings read);
  `LookupChoiceFilter.get_lookup_choices` consumes
  `get_model_field(self.model, ...)` (never runs on
  rebound copies). Adopted.
- Censuses re-derived, all match EXCEPT ONE:
  `get_model_field` 11 = 3 imports + 5 calls + 3 prose
  (own grep identical, all 5 calls homed); parent-read
  population consistent (2 walk + ownerdef + projected +
  DRF-other-family under Matrix axis 1); `async def` in
  `filters/sets.py` exactly 5 at :3417/:3479/:3894/:4012/
  :4904; `queryset=constrained` exactly :4711/:4835;
  upstream versions + `uv.lock` dual-Django marker match
  (`26.1` / `6.1.2` + `5.2.18 | python_full_version`);
  metaclass default + `Filter.__init__` + stamp lines
  confirmed in the installed wheel; all 6 cited oracle
  names exist at the cited tiers, 2 spot-checked literal
  (`IN (1, 2)` SQL text, `ConfigurationError` message);
  WT/HEAD/ITEM_BASELINE fingerprints all re-derived and
  matching (WT == baseline; item-scoped diff empty; no
  new files).
- CORRECTION (Worker-2; Worker-0 transcribes THIS figure,
  not W1's): `_bound_field_name` callers are 13, not 5.
  Instrument: `grep -rn --include='*.py'
  '_bound_field_name('` minus the 2 defs. Filters-family
  callers: `base.py:711` (site 1), `sets.py` x11 (:1057,
  :1454, :1513, :1561, :1601, :1633, :1655, :3747, :3863,
  :3958, :4274), `inputs.py:1146`. W1 listed only the
  first 4 sets.py hits. (DRF's same-named
  `serializer_converter.py::_bound_field_name` + its 4
  callers are a different function / different rule,
  correctly out of scope.) IMPACT: none on any decision -
  C-strict stays 1 definition (single-owned either way);
  F1, owner, rejections, migration, proof unaffected. The
  figure is illustrative for an already-single-owned
  rule, so this is a recorded correction, not
  revision-needed. It is also the ONLY W1 census I found
  wrong; every other figure matched exactly.
- Freshness depth: W1 fingerprints the 3 indexed files +
  upstream versions + search populations, but no per-file
  blob for `forms/sets.py::_resolve_model` or
  `rest_framework/serializer_converter.py` (Matrix axis 1
  body-strength claims). My independent sweep corroborates
  both claims (form-class root; serializer parent +
  separate `_bound_field_name`). Both files are
  hunt-dirty concurrent work (fingerprints would churn)
  and any post-hunt change reopens the item anyway;
  accepted with corroboration noted. Post-hunt
  re-verification re-fingerprints everything.
- Direct `_meta.model` reads (`RelatedFilter.get_queryset`,
  hop-record / declaration / metaclass reads): W1 homes
  them in Enumeration shape-clearance, not numbered Rs.
  Adequate: below family-membership threshold (no parent
  root, no walk); the mechanism census (parent +
  `get_model_field`) bounds membership, and every
  mechanism hit IS in F1 or a numbered R.
- Sharded/pg `inapplicable by construction`: ACCEPTED.
  The walk is a pure derivation (attribute reads +
  upstream path walk); no database, alias, `using=`,
  SQL, parameter binding, or dialect branch in the rule,
  the owner body, or either call site. Cell runs could
  add nothing.
- No scratch tests written: every claim was decided by
  body inspection + grep censuses + gate re-runs. The
  migration's behavior-preservation is by construction
  (identical `model` on every input, untouched
  downstream) with suite execution correctly deferred;
  a scratch simulation of an unlanded helper would test
  my simulation, not the migration. The one open semantic
  question (helper `_meta` spelling under a hostile
  metaclass) is correctly coupled to the hunt landing +
  maintainer decision, undecidable by execution now.
- Structural gate: specified-but-unlanded with an
  adequate negative control (inline-copy control: census
  fails count-2, behavior oracles stay green). Nothing
  executable now; validated when it lands at
  re-verification.
- Item-scoped diff vs AGENTS.md prose: touched production
  paths = {} (empty set, zero-edit confirmed) - no
  provenance surface, no citations owed, no tests owed,
  no ruff runs owed. Artifact is per-cycle scratch
  (raw `path:NN` permitted); scaffold untouched by my
  append (no links added, def block unmodified) - no
  layout-script run (outside the entry's authorization,
  and scratch is exempt from style cleanup).
- `## Defects` (Worker-2): none in product. The census
  correction above lives here, not under Defects (artifact
  figure, corrected in-record).

Gate re-runs (all through `heavy`, machine GREEN, `pgrep`
clean; first run synced copy
`~/dry/ws/c3af387fc1324a21/dry/slots/slot-2`,
reported fresh, shared tree unmoved since sync):

- Proof validation:
  `workspace.py run dry/boundwalk-f60/verify-1 --
  pytest tests/filters/test_base.py -n0 --no-cov -q` ->
  135 passed in 5.97s
  (run dry-20261009T201509-0d7084, exit 0). The `proof:`
  entry is validated runnable; runnable FOR VERDICT only
  after the unblocked consolidation lands (unchanged).
- `... -- basedpyright` -> 0 errors, 0 warnings, 0 notes
  (run dry-20261009T201521-34969a, 68.97s).
- `... -- basedpyright -p pyrightconfig.floor.json` -> 0
  errors, 0 warnings, 0 notes
  (run dry-20261009T201633-f756c5, 67.21s).
- `... -- python scripts/check_truthful_reads.py --check`
  -> 120 files, errors 0
  (run dry-20261009T201744-89ac81). `check_any.py` not
  run or cited (gone).

VERDICT: verified. The item keeps one `proof:` entry, so
Worker-0 marks the plan row `verified, pending execution`
(per DRY.md: `proof:` remains -> pending execution).
No ledger rows (zero edits). No new index rows (separations
live in the F1 record + specified helper docstring, per
W1's transcription note - endorsed). No defects. The
family stays open on the hunt block; re-verification after
the unblock re-fingerprints, lands the migration + census
gate, and runs the `proof:` command for verdict.

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



