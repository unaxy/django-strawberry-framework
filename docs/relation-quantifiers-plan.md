# Relation quantifiers plan: `some` / `none` / `every` on to-many branches, `{}` constrains nothing

Status: PLAN v1, **unreviewed**: the next step is an adversarial review. Written at `8d47f31f`; R1 re-pins every
citation at its own base. Closes tracker item 729 ("To do: found along the way"). Q1 and Q2 are maintainer rulings; the
rest is not yet approved. Process: `docs/bug_hunt/FIX.md` phases 3 to 9. Independent of item 216 (the `flat=False`
opt-out, landed; its plan is `git show 771c299f:docs/related-filter-flat-opt-out-plan.md`); R1 re-pins every
`filters/inputs.py::_build_input_fields` citation against it.

## The problem

- **An empty branch has two meanings.** A present nested branch is "active" regardless of its inner value
  (`utils/permissions.py::active_related_branches`). So `shelves: {}` means "has some visible shelf", and
  `not: {shelves: {}}` means "has none". A root `filter: {}` means "no constraint". The same value means different
  things by position.
- **spec-027 contradicts the code.** Its `apply_async` paragraph says a "present-but-empty nested branch ...
  constrains nothing". The first 216 review confirmed the existential behavior over HTTP: `{shelves: {}}` returned
  only the branch with a visible, in-scope shelf.
- **To-many existence has no clean spelling.**
  - "Has no visible shelf" is spelled `not: {shelves: {}}`.
  - "Every shelf matches" has no spelling at all.
  - A flat `isNull: true` across a to-many hop null-extends, unlike its nested twin. That works only on flat edges.

## Research done (2026-11-02, two survey agents)

- **Meta and the GraphQL Foundation:** no standard.
  - The spec defines no filter grammar and no relation-existence operator, and gives `{}` no meaning. Every
    filter-grammar issue in graphql/graphql-spec was closed without a spec change (#271, #341, #1001).
  - Coercion makes `{}` an input object with no fields, the same value at the root and in a branch. "Constrains
    nothing" is the reading most consistent with the spec.
  - `@oneOf` refuses `{}`, so it cannot be the filter type.
  - The working-group strawman `AbstractFilter` prefers "directive, not convention" for anything clients must rely
    on. It is a weak signal and covers abstract types only.
- **Industry:** strong consensus for an explicit to-many operator. Eight implementations have one:
  - Prisma, PostGraphile, Hot Chocolate, Neo4j and Directus spell it `some` / `none` / `every` (Hot Chocolate `all`;
    Directus `_some` / `_none`). Each operator takes the target's own filter as a nested predicate.
  - Gatsby (`elemMatch`), Dgraph (`has`) and Contentful (`_exists`) spell it differently.
  - Only Hasura v2 and strawberry-django use the bare nested object as an implicit "some".
- **What `{}` means elsewhere:**
  - No constraint: strawberry-django, pg_graphql.
  - Existence: Prisma under a quantifier (`some: {}`), Hasura v2 bare.
  - Error: PostGraphile by default.
- **To-one:** a yes/no null flag is the usual form (PostGraphile `<rel>Exists`, Contentful, Django `fk__isnull`).
  Prisma alone uses `is` / `isNot`.
- **Where the operators live.** Prisma puts them on a separate per-target wrapper type, so they never appear on the
  model's own filter input, the root included, and never collide with model field names.

## Decisions (recommendation first; maintainer rulings recorded)

### Q1 (RULED): the Prisma wrapper for to-many relations

- A to-many `RelatedFilter` field is typed as a per-target wrapper input:
  `ShelfListRelationFilterInputType { some, none, every }`. The name follows the package's `type_name_for` pattern
  (R2). Each field is typed as the target's existing shared input.
  - `some: P`: a visible, admitted child matches P.
  - `none: P`: no visible, admitted child matches P.
  - `every: P`: no visible, admitted child fails P. True when the parent has no child (vacuous), as in Prisma.
- "Visible, admitted" means the child type's `get_queryset` scope intersected with the declaration's `queryset=`,
  callable included. These are today's `_admitted_rows` rows. Hidden rows are never counted, so `none` and `every`
  cannot reveal a hidden row.
- Several operators in one wrapper AND together, as in Prisma.
- An empty wrapper `shelves: {}` constrains nothing. `some: {}` means "has a visible shelf"; `none: {}` means "has
  none".
- There is one wrapper per target FilterSet, not per edge. Edge scope lives in evaluation, not in the type. Types grow
  linearly.
- `and` / `or` / `not` stay on the shared input only, not on the wrapper. The wrapper's operators already express the
  negations.

### Q2 (RULED): `{}` constrains nothing, everywhere

- An inner `{}` under a quantifier contributes no child predicate. The quantifier alone decides.
- spec-027's contradictory sentence is rewritten in every home.

### D3: to-one relations, OPEN (my summary to the maintainer was imprecise here)

- The ruling said "to-one keeps the bare nested filter plus a yes/no null flag". A bare nested filter means the field
  is typed as the target's shared input, so a null flag placed on it would land on the shared type: the root and a
  name collision, the exact problem the wrapper avoids.
- Options:
  - **(a) A to-one wrapper** `ShelfRelationFilterInputType { is: P, isNot: P, isNull: Boolean }`. This is Prisma's
    shape plus Django's `isnull`. It is a consistent pair with the to-many wrapper, but every to-one nested query
    changes shape too.
  - **(b) Bare nested stays, and the existence flag is a parent-level sibling** `<rel>IsNull: Boolean`
    (`branchIsNull`). It reads like PostGraphile's `<rel>Exists` and Django's `branch__isnull`. It is a name on the
    parent, so it can collide with a flat copy or own filter of that name; that collision is refused at build. Small
    break: none for existing to-one queries.
  - **(c) Bare nested stays, and explicit `branch: null` means "has no branch".** Spec-legal (null is distinct from
    omitted), but clients and codegen often conflate the two. Not recommended.
- **Recommended: (b).** Bare to-one has no quantifier ambiguity, since there is at most one row. Its "has some" is
  `branch: {}`, which then constrains nothing, so "has some" must be spelled `branchIsNull: false`.
- What counts as to-one: a declaration whose relation path has only forward FK or O2O hops. Any to-many hop (reverse
  FK, M2M, reverse O2O through a multi-segment `field_name` that fans out) makes it to-many. R1 pins this against
  `_require_relation_path`.

### D4: flat copies, unaffected

- Flat leaves keep their own semantics: independent rows and null extension (spec-027 Decision 8).
- No flat key name changes.
- `HIDE_FLAT_FILTERS`, `MAX_FLAT_FILTERS` and 216's `flat=` are unaffected.

### D5: evaluation reuses the existing seams

- `some` is today's branch restriction: `_restrict_through_branch` over `_admitted_rows`.
- `none` is the same correlated predicate, negated at the parent.
- `every` is "none of the admitted children outside the rows matching P": admitted rows minus matched rows.
- No second relation evaluator is built. The sync and async twins
  (`_derive_related_visibility_querysets_sync/async`, `_collect_nested_visibility_querysets_*`) carry the operator
  through.
- Each operator in a wrapper is one child application, so `{some: A, none: B}` builds two child filter sets.

### D6: gates and visibility

- The parent's `check_<rel>_permission` fires for any present operator, `none` and `every` included, and for a
  present empty wrapper. Presence stays the gate trigger, as today; R2 checks that against the active-branch rule.
- The child's gates fire for the filters its predicate names.
- Item 601 is unchanged.
- **OPEN:** does an empty wrapper `shelves: {}` still fire the parent gate? Recommend yes. It is an attempted use of
  the relation, and that keeps "present means gated".

### D7: the child form contract, documented and not changed

- A child predicate is built by the child's own form, defaults included. A child checkbox's omitted `False` or a
  disabled initial value can constrain inside `some`, `none` and `every`. For example, under
  `issues: {every: {title: ...}}` the predicate also requires the checkbox's default.
- This is today's child-form contract (spec-027 Decision 3 Layer 4). The wrapper does not change it, and the docs
  state it per operator.

### D8: migration, a breaking schema change pre-1.0, made once

- Every nested to-many query changes shape: `shelves: {books: {title: ...}}` becomes
  `shelves: {some: {books: {some: {title: ...}}}}`.
- Old queries fail loudly at validation (unknown field `books` on the wrapper), never silently.
- No compatibility mode. A dual surface would publish two meanings for one field.
- Direct django-filter and DRF use is unaffected: nested branches are GraphQL-only, and the form-data surface is the
  flat keys.

### D9: ordering, unaffected

- `OrderSet` branches are a different input. spec-028 gets one sentence saying so.

## Must preserve

- Visibility and admitted-row scope at every hop, the explicit callable `queryset=` with the request, and the
  database alias.
- The order of branch, form and permission errors, and their error paths.
- The recursion budget, including logical arms and wrapper depth (R2: does a wrapper level count as depth?).
- Query counts. `some` costs no more than today's branch. Each added operator costs one correlated subquery.
- Connection pagination and the optimizer: exact row membership and multiplicity. A parent matching through two
  children appears once, as today.
- Async-only `get_queryset` awaited, never run inside the sync boundary.

## Research (R1 and R2, `opus-high`, private clone)

- **R1 (inputs):**
  - wrapper type naming and `NameConverter` interaction;
  - the to-one / to-many classification across multi-segment `field_name`;
  - collision rules for D3 (b);
  - what introspection shows, a before-and-after SDL diff for fakeshop;
  - a census of every live and package test and doc example sending a nested to-many branch: the migration count.
- **R2 (evaluation):**
  - whether `none` and `every` fit `_restrict_through_branch` / `_restrict_to_related` without a new evaluator;
  - gate firing per operator;
  - the sync/async twin path;
  - the SQL each operator emits, with query counts;
  - `every` over a multi-hop `field_name`;
  - cost per operator against today's nested branch, with a self-time profile and paired, warmed, alternated
    variants (the review's finding 7 recipe).

## Implementation, verification, docs

- Same FIX.md obligations as the 216 plan v2: failability manifest, expectation-first grid, type checks, suppression
  check, citation and doc checks, scoped mutations, four-tree sweep, CPU budget.
- **Mutations to kill:**
  - `none` behaves as `some`;
  - `every` is not vacuous on no children;
  - `every` counts hidden rows;
  - an empty wrapper constrains;
  - the parent gate is skipped for `none`;
  - an async-only hook runs inside the sync boundary.
- **Live acceptance rows** (`examples/fakeshop/test_query/`), each with anonymous/staff pairs:
  - each operator on reverse FK and M2M;
  - multi-hop;
  - a declaration `queryset=`;
  - hidden rows;
  - an empty wrapper;
  - `some: {}` and `none: {}`;
  - nested wrappers;
  - wrappers under `and` / `or` / `not`;
  - to-one per D3;
  - a connection with the optimizer.
- **Docs:**
  - spec-027 five homes: the Decision 8 pipeline, Layer 4 branch rendering, the async paragraph's contradictory
    sentence, Edge cases, Test plan, DoD;
  - spec-028's sentence;
  - GLOSSARY via the DB (the wrapper types, `some` / `none` / `every`), with TREE regenerated;
  - the test READMEs;
  - a migration section discoverable from the root README.
- **CHANGELOGTODO:** an item marking the breaking nested to-many shape.
- **Tracker:** tick 729 in the landing commit, and delete this plan file (`docs/relation-quantifiers-plan.md`).

## Risks

- This is the largest schema break the package has made. Every client nested query over to-many changes.
- `every` with child form defaults (D7) is easy to misread. The docs need a worked example.
- The D3 to-one shape is a one-way door, and so are the wrapper type names.

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
