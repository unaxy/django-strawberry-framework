# Spec: Sealed `get_queryset` visibility-boundary policy artifacts — the governing security decisions, spec, and glossary for the framework-owned execution queryset

Built for `0.0.14` (card `DONE-045-0.0.14`). This is a **documentation-only**
card over the sealed [visibility boundary][glossary-visibility-boundary]: it
owns the governing set of numbered security decisions, this spec, a KANBAN card,
and the [glossary][glossary] fold-in, so the standing documentation states the
implemented security contract.

Decisions 1–6 and 8 below state the boundary's contract; Decision 7 records
release bookkeeping. Every rejected alternative lives in the deliberative
companion [`docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-rationale.md`][rationale].

Status: **COMPLETE — shipped in `0.0.14`.** The Slice checklist boxes below stay
unticked because the `Status:` line is the completion source of truth (the
shipped-spec convention).

No version bump and no `CHANGELOG.md` entry are owned here
([Decision 7](#decision-7--no-version-bump-the-0014-cut-already-landed)).

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [Sealed execution queryset][glossary-sealed-execution-queryset],
  [Visibility boundary][glossary-visibility-boundary],
  [Prefetch alias threading][glossary-prefetch-alias-threading] — the terms this
  card authors, naming the contract's moving parts.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — the
  consumer seam whose source and result the boundary seals.
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the cascade
  caller that composes over the same boundary and supplies the `render_error`
  seam.
- [`ConfigurationError`][glossary-configurationerror],
  [`SyncMisuseError`][glossary-syncmisuseerror] — the single typed fail-closed
  boundary error and its sync-context subclass.

## Slice checklist

A single documentation slice.

- [ ] **Slice 1 — Policy artifacts for the sealed boundary**
  - [ ] Numbered security decisions (below) covering the contract: the clone of
        the hook's source and result, the shape check, no identity fast path,
        alias threading, queryset-shape rejections, the typed error contract, and
        the threat model.
  - [ ] This spec `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` and its
        companions `*-terms.csv` and `*-rationale.md`.
  - [ ] The new glossary entries imported via the fakeshop glossary DB and
        `docs/GLOSSARY.md` regenerated (never hand-edited).
  - [ ] `KANBAN.md` / `KANBAN.html` regenerated from the kanban DB with this
        card in Done.

## Problem statement

Every surface that composes onto a [`get_queryset` visibility
hook][glossary-get_queryset-visibility-hook]'s return (Relay node defaults,
connections, list fields, relation resolvers, the cascade, the optimizer's
planned children) needs the same answer to two questions: is the return a shape
the surface can compose onto, and is the object it composes onto its own? A hook
that returns a list, another model's rows, a sliced or projected queryset, a
queryset routed to another database, or an object it already evaluated (or
shares across requests as a class attribute) is a mistake the surface must
refuse or neutralize in one place, not per surface.

## Current state

- [`django_strawberry_framework/utils/querysets.py`][querysets] owns the boundary
  and is covered under the repository's `fail_under = 100` gate.
- Both the source (before the hook) and the hook result (after) pass the seal
  ([`utils/querysets.py::_seal_or_defect`][querysets]), which checks the shape and
  returns `candidate.all()`: Django's own clone, of the candidate's own class, with
  no fetched rows, no related manager's parent instances (`_known_related_objects`, which
  would pre-empt a `Prefetch` the hook added on that relation), and a related manager's
  pending filter baked into its query.
- Every shape a surface cannot compose onto fails closed with a typed
  [`ConfigurationError`][glossary-configurationerror] (or
  [`SyncMisuseError`][glossary-syncmisuseerror] for an async hook in a sync
  context) — never a raw backend `OperationalError`, `TypeError`,
  `AttributeError`, or an unclosed coroutine.
- The sync and async runners share one preparation primitive
  (`_prepared_visibility_source`) and one normalization primitive
  (`_normalized_visibility_result`) so the two colored paths cannot drift.
- Each surface seals under one frozen option set,
  [`utils/querysets.py::_SealPolicy`][querysets] (`require_model_rows`,
  `reject_sliced`, `require_shared_alias`,
  `require_unevaluated`), declared once per surface and applied to both seals of
  one visibility call. The `get_queryset` surfaces run `_DEFAULT_SEAL_POLICY`,
  the cascade `_CASCADE_SEAL_POLICY`, and the optimizer's planned children
  `_PREFETCH_CHILD_POLICY` / `_LIST_RELATION_CHILD_POLICY`; the post-sidecar
  result seal (`_SIDECAR_RESULT_POLICY`) is spec-050's surface.

## Goals

- Record the governing numbered security decisions for the accepted queryset
  shapes, identity/cache behavior, aliases, errors, and query execution of the
  sealed boundary.
- Author the glossary terms naming the contract's moving parts, and relink the
  four existing terms the contract composes with.

## Non-goals

- **No behavior change.** This card is documentation only; the boundary's code
  is not owned by it.
- **No version bump.** ([Decision 7](#decision-7--no-version-bump-the-0014-cut-already-landed)).

## Borrowing posture

The clone is Django's own `QuerySet.all()`; the combined-queryset rewrite is
`QuerySet.filter(pk__in=<combined>.values("pk"))`. Neither `graphene-django` nor
`strawberry-graphql-django` checks a hook's return shape, so there is no
upstream peer to borrow the checks from.

## Architectural decisions

Decisions 1–6 and 8 below are the governing security decisions for the boundary
— 1–6 the shape of the seal, 8 the threat model that bounds it; Decision 7
records release bookkeeping. Each is pinned to the enforcing symbols in
[`django_strawberry_framework/utils/querysets.py`][querysets] and the tests that
hold it.

Decision numbers are load-bearing beyond this document: source and test
docstrings across the package cite them in the form `spec-045 Decision N`.
Renumbering a decision is a package-wide rename, not a documentation edit.

### Decision 1 — The hook's source and result are each sealed into a fresh clone

**Decision.** Every framework-owned invocation of a `get_queryset` hook runs
through the two colored runners, `apply_type_visibility_sync` and
`apply_type_visibility_async`. The source the surface seeded is sealed before
the hook runs and the hook's return is sealed after it; each seal hands on
`candidate.all()` (pinned with `.using(alias)` when the resolution requires an
alias and the candidate is unrouted). The clone keeps the candidate's own
`QuerySet` class, so a hook calls its project's queryset methods on its input and
a project method chains after the cascade; it is never the object the hook holds,
so the surface never composes onto, windows or evaluates the hook's own object.
A `Manager` return is coerced once through `.all()`, and a `Manager` whose
`all()` returns something other than a `QuerySet` fails closed rather than being
taken for the plain-iterable bypass. The cascade
([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) seals its root
through the same source seal and narrows the clone with its own class's `filter`.
This is the [sealed execution queryset][glossary-sealed-execution-queryset].

**Enforcing symbols.**
[`utils/querysets.py::_seal_or_defect`][querysets];
[`::_prepared_visibility_source`][querysets];
[`::_normalized_visibility_result`][querysets];
[`::_coerced_manager_queryset`][querysets];
[`::apply_type_visibility_sync`][querysets] and
[`::apply_type_visibility_async`][querysets];
[`django_strawberry_framework/permissions.py::apply_cascade_permissions`][permissions].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
`test_hook_receives_the_sources_own_queryset_class` (and its async twin),
`test_related_manager_queryset_seals_and_scopes_to_its_parent`;
[`tests/test_permissions.py`][permissions-tests]
`test_cascade_returns_the_sources_queryset_class`.

**Deliberation.** The rejected class-inventory, plain-rebuild and
return-the-candidate shapes are recorded in the [rationale companion][rationale].

### Decision 2 — The seal is a clone and a cheap shape check, not a proof

**Decision.** The seal reads what Django exposes about the candidate (its class,
`model`, `query`, `_db`, `_hints`, `_result_cache`, `_iterable_class`) and checks
it against the surface's [`_SealPolicy`][querysets]; it does not walk the query
graph, rebuild the query, or refuse a project's own query, expression, lookup or
iterable class. A hook, a project `QuerySet` class and a sidecar override are
application Python, trusted under GOAL.md "Trust boundary": the seal catches the
shapes a hook can return by mistake, and the clone is what the surface composes
onto. A combined (`union()` / `intersection()` / `difference()`) query is the one
shape the seal rewrites (Decision 5), and a `Prefetch` child the candidate carries
that is itself combined is rewritten the same way, since Django's prefetch filters
the child by its relation and refuses that after a combinator. Every such child, at
any depth, is also refused (the `prefetch` code) when its model is not its
relation's target or a subclass of it, since Django hands a child's rows to the
relation without checking them, or when it is routed off the candidate's
effective alias; an unrouted child follows its parent at fetch.

**Enforcing symbols.**
[`utils/querysets.py::_seal_or_defect`][querysets];
[`::_with_prefetch_children_served`][querysets].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
`test_seal_policy_presets_answer_slice_and_combinator_independently`,
`test_a_combined_prefetch_child_is_served_as_its_primary_key_set`;
[`examples/fakeshop/test_query/test_combined_visibility_api.py`][combined-visibility-tests]
`test_consumer_prefetch_of_a_combined_queryset_serves_its_rows`.

**Deliberation.** The rejected proof walk with canonical reconstruction is
recorded in the [rationale companion][rationale].

### Decision 3 — The identity fast path is removed; hook results are always re-sealed and result caches dropped

**Decision.** Neither runner skips result normalization when the hook returns
the exact source object it received: `apply_type_visibility_sync` and
`apply_type_visibility_async` ALWAYS re-seal the hook result through
`_normalized_visibility_result` (no `result is queryset` shortcut). The seal's
clone never copies `_result_cache`, so a hook that evaluated its return, or
returns a queryset shared across requests, hands the surface an unevaluated
clone that reads its rows again. Object identity is not immutability: a hook
holding the sealed source can evaluate or re-route it and return the same object,
so identity licenses no shortcut.

**Enforcing symbols.**
[`utils/querysets.py::apply_type_visibility_sync`][querysets] #"No identity fast path";
[`::apply_type_visibility_async`][querysets] #"No identity fast path";
[`::_seal_or_defect`][querysets] #"queryset = candidate.all()".

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
`test_identity_hook_result_is_resealed_dropping_injected_cache_sync` and
`test_identity_hook_result_is_resealed_dropping_injected_cache_async` (a hook
that injects a row into the received queryset's `_result_cache` and returns the
same object), `test_evaluated_hook_result_is_refreshed`.

**Deliberation.** The rejected identity shortcut and the rejected
unoverridden-default-hook narrowing are recorded in the
[rationale companion][rationale].

### Decision 4 — Alias threading with `require_shared_alias` for planned children

**Decision.** A queryset the optimizer walker installs as a parent's `Prefetch`
child is sealed under a policy that sets `require_shared_alias`: the child's
explicit `_db` must EQUAL the outer effective alias, including when that alias
is `None`, so an unrouted parent forces an unrouted child and one GraphQL
resolution never spans two database connections; an unrouted child inherits the
parent's connection at fetch time. This is
[Prefetch alias threading][glossary-prefetch-alias-threading]. On every other
surface an unrouted return is pinned onto the resolution's required alias, an
explicitly matching one is kept, and an explicitly divergent one fails closed
(`alias`).

The walker's children seal under `_PREFETCH_CHILD_POLICY` on the
nested-connection path (whose planner classifies a sliced child and degrades)
and under `_LIST_RELATION_CHILD_POLICY` on a plain list relation, which keeps the
slice rejection. A consumer `OptimizerHint.prefetch(Prefetch(...))` on a relation
whose target overrides `get_queryset` takes the plain-list path with the hinted
queryset as the seed the hook narrows
(`django_strawberry_framework/optimizer/walker.py::_scoped_hint_prefetch`); it
serves a combined seed as its primary-key set and refuses a sliced one. A hinted
seed on a `Prefetch` without `to_attr` whose model is neither the lookup's
target nor a proxy of it is refused at type build
(`django_strawberry_framework/types/base.py::_validate_optimizer_hints`), hooked
target or not, since Django builds the prefetched rows from the seed's model. A
consumer `Prefetch(queryset=...)` in a root or hook `prefetch_related` that wins
over such a planned `Prefetch` is sealed the same way, its queryset the seed
(`django_strawberry_framework/optimizer/plans.py::PrefetchSeal`, invoked by
`django_strawberry_framework/optimizer/plans.py::diff_plan_for_queryset`), and the
relation's own resolver key stays planned.

**Enforcing symbols.**
[`utils/querysets.py::_seal_or_defect`][querysets] #"require_shared_alias";
the policy threading in
[`django_strawberry_framework/optimizer/walker.py::_build_child_queryset`][walker].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
`test_divergent_explicit_result_alias_fails_closed`; the walker's two child
policies in
`tests/optimizer/test_walker.py::test_plan_refuses_sliced_hook_result_for_plain_list_relation`
and
`tests/optimizer/test_walker.py::test_connection_child_seam_still_admits_a_sliced_hook_result`.

**Deliberation.** The rejected unpinned child seal and the symmetric
unrouted-parent rule are recorded in the [rationale companion][rationale].

### Decision 5 — Queryset-shape rejections

**Decision.** The seal fails closed on: a value that is not a `QuerySet` (`type`
defect); a queryset whose model is not the registered type's concrete model or a
proxy of it (`table` defect); a sliced query on every surface whose policy sets
`reject_sliced` (`sliced` defect; off only for the walker's nested-connection
child under `_PREFETCH_CHILD_POLICY`); a row iterable that is not a
`ModelIterable` where the policy sets `require_model_rows` (`projection` defect;
every surface except the cascade). On every surface a combined query is rewritten as
`Model.filter(pk__in=<combined>.values("pk"))`, its outer column ordering (a
column name, or an exact `F()` over a column, bare or under `.asc()` / `.desc()`
with any nulls placement; a forward relation by its key column, as the
combinator orders it) and `reverse()` kept, so every surface narrows, projects
and prefetches the set of primary keys it selects. A branch over another model's
table is the `table` defect, since the rewrite would match this model's rows by
another table's primary keys; a shape the rewrite would serve different rows for
(`union(all=True)`; a branch's annotations, `extra(select=...)`, `.values()` or
`select_for_update`; an outer `.values()`, an ordering by a lookup, transform or
other expression, or a slice) fails closed (`combined` defect).

**Enforcing symbols.**
[`utils/querysets.py::_seal_or_defect`][querysets] #"is_sliced" (slice /
projection rejections);
[`::_foreign_combined_model`][querysets] (the branch-table check);
[`::_pk_membership_query_or_defect`][querysets] and
[`::_combined_lost_property`][querysets] (the combinator rewrite and its refusals);
[`::_is_carried_order_term`][querysets] and [`::_rewrite_order_term`][querysets]
(which outer ordering the rewrite carries, and its column spelling); the policy
threading in
[`django_strawberry_framework/optimizer/walker.py::_build_child_queryset`][walker]
and the nested-connection gate
[`django_strawberry_framework/optimizer/nested_fetch.py::unwindowable_child_queryset_reason`][nested-fetch].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
`test_wrong_model_hook_result_fails_closed`,
`test_mti_child_hook_result_fails_closed`,
`test_values_projection_result_fails_closed_on_read_surface`,
`test_combined_query_branch_over_another_model_fails_closed`;
[`examples/fakeshop/test_query/test_combined_visibility_api.py`][combined-visibility-tests]
for every combinator shape over HTTP.

**Deliberation.** The rejected copy-through of a combinator and the reason a
cross-model branch is refused rather than rewritten are recorded in the
[rationale companion][rationale].

### Decision 6 — Typed `ConfigurationError` fail-closed error contract

**Decision.** Every defect surfaces as a typed
[`ConfigurationError`][glossary-configurationerror] (never a raw backend
`OperationalError`, `TypeError`, `AttributeError`, or unclosed coroutine). The
seal's defect codes are `type`, `table`, `routing`, `evaluated`, `sliced`,
`projection`, `combined` and `alias`, checked in that order. `routing` and
`evaluated` are reached only by the post-sidecar result seal (spec-050's
surface); the `get_queryset` surfaces render the other six codes, each with
bespoke consumer-facing wording. Each message-building site dispatches
exhaustively through `_defect_message`, so a code with no arm at a site
self-names as a framework defect rather than borrowing another code's wording. A
caller-supplied `render_error` seam lets the cascade keep its path-rich per-edge
prose. The sync boundary reserves the [`SyncMisuseError`][glossary-syncmisuseerror]
subclass (`ConfigurationError` + `RuntimeError`) for an async hook met in a sync
context; the async runner awaits at most one returned awaitable and rejects a
nested awaitable after it.

**Enforcing symbols.**
[`utils/querysets.py::_visibility_result_error`][querysets] (defect-code ->
`ConfigurationError` mapping + `render_error` seam);
[`::_prepared_visibility_source`][querysets] (source-side typed errors);
[`::_defect_message`][querysets] (exhaustive per-site dispatch);
[`::SyncMisuseError`][querysets] and [`::reject_async_in_sync_context`][querysets];
[`django_strawberry_framework/exceptions.py::ConfigurationError`][exceptions].

**Tests that pin it.** [`tests/utils/test_querysets.py`][queryset-tests]
`test_visibility_defect_messages` and the per-code error-message assertions;
[`tests/test_permissions.py`][permissions-tests] for the cascade `render_error`
path.

**Deliberation.** The rejected propagate-backend-exceptions behavior, the rejected
per-code exception taxonomy, and the reason the cascade's prose lives behind a
`render_error` seam rather than inside the shared checker are recorded in the
[rationale companion][rationale].

### Decision 7 — No version bump: the `0.0.14` cut already landed

**Decision.** This card owns no version bump and no `CHANGELOG.md` entry: the
sealed boundary ships under the `0.0.14` release, so `__version__` in
`django_strawberry_framework/__init__.py` (the single version source) is
untouched here.

**Deliberation.** The rejected joint-cut-owner shape is recorded in the
[rationale companion][rationale].

### Decision 8 — Threat model: a mistaken hook, not an in-process adversary

**Decision.** The [visibility boundary][glossary-visibility-boundary] defends
against a [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook]
that is **wrong**: one that returns a shape its surface cannot compose onto, or an
object it evaluated or shares. It does not defend against application Python that
means harm: a hook, a project `QuerySet` class, a sidecar override and an
extension factory run inside the server process and are trusted (GOAL.md "Trust
boundary"), so the boundary checks what it can establish mechanically about
their results and states the contract each must keep. A report is a boundary
defect when a wire input reaches a wrong row set through code that could feasibly
exist in a project using supported public API.

**Deliberation.** The rejected in-process-adversary threat model and its proof
walk are recorded in the [rationale companion][rationale].

## Error shapes

The defect-code table the shared checker emits for a `get_queryset` result, in
the order [Decision 6](#decision-6--typed-configurationerror-fail-closed-error-contract)
states, each rendered by [`::_visibility_result_error`][querysets] (or the
caller's `render_error` seam). The seal's `routing` and `evaluated` codes sit
between `table` and `sliced` in that order and are rendered only by the
post-sidecar result seal.

| Code | Fails when | Consumer-facing wording (default) |
|---|---|---|
| `type` | hook returned a non-QuerySet/Manager (list, generator, `None`) | "must return a QuerySet or Manager of `<Model>` rows" |
| `table` | the queryset's model, or a combinator branch's, is not the registered concrete table | "composes over `<Model>`'s concrete table" |
| `sliced` | sliced query on a recomposing read surface | "Django forbids refiltering or reordering a sliced query" |
| `projection` | non-`ModelIterable` row iterable on a model-row surface | "composes over `<Model>` model rows, not a `.values()` / `.values_list()` (or custom-iterable) projection" |
| `combined` | a combinator whose primary-key set cannot represent its rows (duplicates, branch annotations / `extra(select=...)` / `.values()` / `select_for_update`, outer `.values()` / ordering by a lookup, transform or other expression / slice) | "serves a combined queryset as the set of `<Model>` primary keys it selects ... cannot be reduced to that set without changing its rows" |
| `prefetch` | a `Prefetch` child over a model its relation does not target, or routed off the effective alias | "prefetch `'<path>'` queryset is over `<Model>` rows, but the `'<path>'` relation targets `<Model>` rows" / "is routed to alias" |
| `alias` | a return routed off an alias that differs from the pinned resolution | "cannot re-route a pinned resolution. Remove the `.using(...)` call." |

## Test plan

The seal / row-survival matrix (maintainer-invoked gates only, per `AGENTS.md`):

- [`tests/utils/test_querysets.py`][queryset-tests] — the shared seal suite:
  shape defects, the clone's class and state, pending related-manager filters,
  combinator rewrites (a `Prefetch` child included), per-code error messages, and
  sync + async cache-removal cases.
- [`tests/test_relay_node_field.py`][relay-tests],
  [`tests/test_connection.py`][connection-tests],
  [`tests/test_list_field.py`][list-tests] — evaluation-level row-survival
  surfaces (the sealed boundary must not drop legitimate rows).
- [`tests/test_permissions.py`][permissions-tests] — the cascade `render_error`
  path and its class-preserving narrowing.
- `tests/optimizer/test_walker.py` — the walker's plain-list-relation and
  nested-connection child policies.
- `django_strawberry_framework/utils/querysets.py` sits inside the repository's
  `fail_under = 100` coverage gate, so every branch the decisions above add is
  covered or the gate fails.

## Doc updates

This card's Slice 1 doc set (the only surface it touches):

- `docs/GLOSSARY.md` via the glossary DB + re-render (never hand-edited): the
  new terms authored, the four existing terms relinked.
- `KANBAN.md` / `KANBAN.html` via the kanban DB + re-render: this card in Done
  with its glossary links.
- This spec and its two companions,
  `docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-terms.csv` (glossary terms) and
  [`docs/SPECS/appx/spec-045-visibility_boundary-0_0_14-rationale.md`][rationale] (the
  deliberative layer).

`README.md`, `docs/TREE.md`, `GOAL.md`, `TODAY.md`, and `CHANGELOG.md` are
untouched: the boundary's consumer-visible statement is the `docs/README.md`
paragraph on the hook's return.

## Constraints on the supported query surface

These are deliberate constraints of the contract above, not defects:

- **A combined return is served as its primary-key set.** A shape that set
  cannot represent fails closed (Decision 5); compose the branches with `Q`
  objects or `pk__in` subqueries instead.
- **A hook's return keeps nothing it fetched.** The clone reads its rows again,
  so a hook that evaluates its return pays for the discarded rows in one extra
  query (Decision 3).

## Out of scope (explicitly tracked elsewhere)

- Any behavior change to the boundary — this card is documentation only.

## Definition of done

- [ ] Numbered security decisions authored (above) covering the contract: the
      clone of the hook's source and result, the shape check, no identity fast
      path, alias threading, queryset-shape rejections, the typed error contract,
      and the threat model.
- [ ] Spec `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` authored with its
      companions `*-terms.csv` and `*-rationale.md`.
- [ ] The new glossary entries imported via the fakeshop glossary DB and
      `docs/GLOSSARY.md` regenerated.
- [ ] `KANBAN.md` / `KANBAN.html` regenerated from the kanban DB with this card
      in Done.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary]: ../GLOSSARY.md
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-prefetch-alias-threading]: ../GLOSSARY.md#prefetch-alias-threading
[glossary-sealed-execution-queryset]: ../GLOSSARY.md#sealed-execution-queryset
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-visibility-boundary]: ../GLOSSARY.md#visibility-boundary

<!-- docs/SPECS/ -->

[rationale]: appx/spec-045-visibility_boundary-0_0_14-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[exceptions]: ../../django_strawberry_framework/exceptions.py
[nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[permissions]: ../../django_strawberry_framework/permissions.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

[connection-tests]: ../../tests/test_connection.py
[list-tests]: ../../tests/test_list_field.py
[permissions-tests]: ../../tests/test_permissions.py
[queryset-tests]: ../../tests/utils/test_querysets.py
[relay-tests]: ../../tests/test_relay_node_field.py

<!-- examples/ -->

[combined-visibility-tests]: ../../examples/fakeshop/test_query/test_combined_visibility_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
