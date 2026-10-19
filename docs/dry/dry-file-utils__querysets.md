# DRY review: `django_strawberry_framework/utils/querysets.py`

Status: verified
Run: 0.0.15 2026-09-30-8

Revision pass 1 (Worker 1, after Worker 2's `revision-needed`): see `## Iterations` at the
bottom. Two figures in `## System trace` were corrected in place; nothing else above was
rewritten, and two `## Findings` rows are superseded rather than edited.

Item kind: FILE (inventory backstop). No consolidation performed; every rule below is either
assigned to a named responsibility family for a later family item, or recorded file-local with
the challenge that proved it. Zero production edits; zero tracked files changed.

## System trace

4294 lines, read end to end. Inventory instrument: `ast.parse` over the pinned blob, counting
`ast.Module.body` members only — **102 top-level functions, 7 classes, 25 module-level
constants (134 names; 109 excluding constants), plus 6 nested methods**. (Revision 1 corrected
this line: it previously read "99 module-level symbols", a figure no instrument reproduces.
Revision 1 then re-derived the assignment name-by-name against the full 134-name enumeration
rather than trusting that the original pass had been complete; that re-derivation found two
unassigned rules, recorded as I-R3 and I-R5 in `## Iterations`.) The module is the package's neutral
query-source substrate and its hardened `get_queryset` security boundary. 22 package modules
import from it (`permissions.py`, `schema.py`, `relay.py`, `orders/sets.py`,
`forms/resolvers.py`, `list_field.py`, `auth/mutations.py`, `utils/execution_mode.py`,
`utils/permissions.py`, `utils/write_values.py`, `connection.py`, `filters/base.py`,
`filters/sets.py`, `mutations/permissions.py`, `mutations/resolvers.py`,
`optimizer/extension.py`, `optimizer/walker.py`, `resource_policy.py`,
`rest_framework/resolvers.py`, `types/relay.py`, `types/resolvers.py`, `utils/__init__.py`).
`SyncMisuseError` is re-exported from the package root and from `types/relay.py`.

Five responsibility clusters live here:

1. **Query-source seeding and coercion** — `model_for`, `base_queryset`, `initial_queryset`,
   `normalize_query_source`, `_coerced_manager_queryset`, `_captured_model`.
2. **Colored-boundary refusals** — `reject_async_in_sync_context`, `_disposed_awaitable`,
   `_dispose_sync_awaitable`, `reject_awaitable_sync_source`, `reject_residual_async_source`,
   `is_async_only_iterable`, `reject_async_iterable_in_sync_context`, the `_AsyncQuerySetRows`
   adapter trio, `run_in_one_sync_boundary`, `sync_pipeline_recourse`.
3. **The sealed-execution-queryset boundary** — lines 486-3330, roughly 65 symbols: state
   extraction without dispatch, genuineness-by-object-identity, exact-type inventories, the
   three-state graph walk, canonical reconstruction, prefetch sealing, deferred-filter baking,
   `_SealPolicy` and its seven policy constants, routing intent, defect codes.
4. **Visibility runners and their relation helpers** — `_prepared_visibility_source`,
   `_normalized_visibility_result`, `apply_type_visibility_sync` / `_async`,
   `visibility_scoped_related_queryset`, `related_visibility_queryset(_or_default)`,
   `visible_related_object(s)`, `_stringified`, `stringified_pks_present`, `pks_all_present`.
5. **Raw-list row-source ownership and the resolver-source head** — `normalized_row_source`,
   `materialized_rows`, `_readable_queryset_state`, `_row_source_model`,
   `_raw_list_source_message`, `prepared_resolver_source`,
   `post_process_queryset_result_sync` / `_async`.

Connected code read for judgment, outside the item: `connection.py`, `list_field.py`,
`relay.py`, `permissions.py`, `optimizer/walker.py`, `optimizer/nested_fetch.py`,
`types/resolvers.py`, `rest_framework/resolvers.py`, `utils/write_values.py`,
`utils/write_transaction.py`, `utils/permissions.py`, `mutations/permissions.py`,
`filters/base.py`, `filters/sets.py`, `auth/mutations.py`, `routers.py`, `exceptions.py`,
`resource_policy.py`, `tests/utils/test_querysets.py`, `docs/GLOSSARY.md`,
`docs/spec-050-list_field_arguments-0_0_15.md`, `docs/SPECS/spec-045-visibility_boundary-0_0_14.md`.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Searched every public surface for its own spelling of
this module's rules. `models.Manager` appears in exactly three places, all inside this file
(querysets.py:307, 3479, 3818) — no flavor coerces a Manager itself. `__django_strawberry_definition__.model`
is read at exactly one site (`model_for`, querysets.py:243); the only other mention package-wide
is a `types/relay.py` docstring. `reject_async_in_sync_context` is reached by all three sync
hook seams Decision 9/15 name (`relay.py` ×2, `utils/permissions.py`, `mutations/permissions.py`)
plus this module's own runner. `sync_pipeline_recourse` is composed by all three write flavors
(`mutations/resolvers.py:139`, `forms/resolvers.py:125`, `rest_framework/resolvers.py:201`).
`prepared_resolver_source` and `reject_async_iterable_in_sync_context` are each reached by both
collection flavors (list field and connection). Positive results: the **pre-sliced source**
rule has a second flavor-local definition in `connection.py::_guard_source_not_pre_sliced`
(F4), and the **related-object visibility re-check** has a second one in
`types/resolvers.py::_visible_related_object` (F5).

**2. Sync/async twins.** Four colored pairs touch this module: `apply_type_visibility_sync` /
`_async`, `post_process_queryset_result_sync` / `_async`, `reject_awaitable_sync_source` /
`reject_residual_async_source`, and the post-`OrderSet` seal pair, which now lives in this
module as `utils/querysets.py::apply_orderset_sync` / `::apply_orderset_async` and is called
from both `list_field.py` and `connection.py`. Compared by behavior, not shape, and by
signature parity:

```text
apply_type_visibility_sync (type_cls, queryset, info, async_recourse='...', *, model=None, render_error=None, policy=_SealPolicy(...))
apply_type_visibility_async(type_cls, queryset, info,                       *, model=None, render_error=None, policy=_SealPolicy(...))
```

Every seam a surface can vary (`model`, `render_error`, `policy`) is present on both colorings;
`async_recourse` is sync-only and correctly so (the async twin awaits rather than refuses). The
two bodies share `_prepared_visibility_source` and `_normalized_visibility_result` verbatim and
differ only at the await point and its nested-awaitable refusal — principle 5's "one body, named
adapters" shape, already recorded at the async runner (querysets.py:4120-4131). The
`_SealPolicy` docstring records the historical drift this closed ("which is how the async runner
came to reach none of them"), so the twin axis is a solved problem here, not an open one.
`post_process_queryset_result_*` differ only in the `async_guard` they pass and the `await`.
No behavioral divergence found.

**3. Derived rather than repeated knowledge.** Four facts in this file are reconstructed by a
second means rather than restated: `_RETAINED_LEAF_TYPES` is *derived* from `_INERT_VALUE_TYPES`
(querysets.py:1481); `_DIRECT_RHS_DATA_BASES` and `_DIRECT_RHS_TRUSTED_MRO` are derived from it
too (1079, 1083); `_BOUND_VALUE_NORMALIZERS` is a deliberately **hand-ordered mirror** of it
(1670-1692, order is semantic so it cannot be derived) whose agreement is pinned mechanically by
`tests/utils/test_querysets.py::test_bound_value_normalizers_mirror_the_inert_inventory`; and
`_PLAIN_CONTAINER_TYPES` is the prove-side inventory whose rebuild-side answer is pinned by
`::test_every_admitted_plain_container_has_a_rebuild_branch`. Both mirrors carry principle-9
gates, so neither is a second definition. The one *ungated* derived fact is the seal's defect-code
set (F3). Outside the file: `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
re-derives "is this queryset sliced / combined / values-shaped" from `query` attributes; contract
difference recorded in F4.

**4. Inverse / round-trip pairs.** Three pairs, all with both halves in this file:
`wrap_async_queryset_adapter` / `unwrap_async_queryset_adapter` (consumed across `list_field.py`
and `optimizer/extension.py`); `_rebuilt_prefetch_or_defect` (rebuild) against
`_sealed_prefetch_related_lookups` (validate); and the load-bearing one — the whole prove side
(`_expr_graph_defect`, `_container_defect`, `_direct_rhs_defect`, `_is_inert_value`) against the
whole rebuild side (`_reconstructed_value`, `_normalized_bound_value`, `_is_reconstructable_node`).
The dangerous direction (prover-accepted / rebuilder-unhandled) is named at
`_PLAIN_CONTAINER_TYPES` and gated for containers and for bound-value leaves; for AST nodes the
two halves compose the SAME predicate by name (`_type_is_genuinely_django`), so they cannot
disagree by construction. The adapter trio yielded F9 (a third member with no production reader).

**5. Contracts restated in another medium.** Five media carry this module's contracts: production
code; `tests/utils/test_querysets.py` (5760 lines, 309 tests — oracles, several of them
independent by DRY.md's definition, e.g. the two inventory-agreement tests above); the live tier;
`docs/GLOSSARY.md` anchors *Sealed execution queryset* (1891), *Visibility boundary* (2127),
*Prefetch alias threading* (1556), *Prove-then-clone AST trust*, *Callable shadow defect*; and
`docs/SPECS/spec-045-visibility_boundary-0_0_14.md` plus the in-flight
`docs/spec-050-list_field_arguments-0_0_15.md`. Counting the media a change must move surfaced
**D2**: the glossary projection still describes a keyword (`allow_sliced=True`) that
`_SealPolicy` replaced, and `docs/SPECS/spec-034-permissions-0_0_10.md:353` still pins the
retired call shape as a "verified dependency to protect".

**6. Enforcement by omission.** Three families enumerated member-by-member.
(a) *Child-alias inheritance*: `base_queryset`'s own docstring names three surfaces that seed
from a relation's target model — the cascade edge, a `RelatedFilter` child, and the optimizer
walker's prefetch child. Two pass `using=` (`permissions.py:692` `using=state.alias`;
`filters/sets.py:2592` `using=parent_db`); `optimizer/walker.py:443` does not, and seals under a
policy that does not set `require_shared_alias`. Contract sources establish the rule for that
member, so this is **D1**, a behavior defect, not a consolidation.
(b) *Post-`OrderSet` result validation*: `list_field.py` freezes routing intent and re-seals the
override's return; `connection.py:1828/1865` invokes the same public `OrderSet.apply_sync` /
`apply_async` with neither. The contract sources found (spec-050's Edge cases, the
`_SealPolicy.require_unevaluated` prose) both scope the rule to the list field, so the axis says
*ambiguous* — routed to the maintainer through Worker 0 (**D3**), not decided here.
(c) *Awaitable disposal*: enumerated every site that refuses an awaitable. The shared
`_dispose_sync_awaitable` covers this module, `list_field.py` and the two exported refusers;
`auth/mutations.py:505-511` (twice) and `routers.py:279-285` each spell detect-then-dispose
inline. That is duplication, not a gap — F1.

### Challenges

Each change posited against the rule's own variation axes; the count is authoritative
definitions only. Consumers, oracles and projections that also move are listed, never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | read the model registered to a `DjangoType` | definition attribute is renamed / becomes a method | **1** (`model_for`) | independent |
| C2 | seed a fresh base queryset for a model, optionally alias-pinned | seeds must pass `db_manager(alias)` instead of `.using(alias)` | **1** (`base_queryset`) | independent |
| C3 | coerce a `Manager` to a `QuerySet` | a Manager that returns an async iterable must fail closed | **1** (`_coerced_manager_queryset`) | independent |
| C4 | coerce a raw literal through a Django field, or nothing | add a per-field normalization step before validation | **1** (`coerce_field_value_or_none`); `canonical_pk` does NOT move | independent; F6 records why |
| C5 | dispose a refused awaitable so no "never awaited" warning escapes | async generators gain a disposal protocol | **3** (`_dispose_sync_awaitable`, `auth/mutations.py` inline, `routers.py` inline) | duplication — F1 |
| C6 | the "runs synchronously, cannot await" recourse sentence | the sentence must name the settings key that relaxes it | **4** (`sync_pipeline_recourse`, `_RELAY_ASYNC_RECOURSE`, `_PERMISSION_ASYNC_RECOURSE`, `_GATE_ASYNC_RECOURSE`) | 3 rejections already recorded at owners — F7 |
| C7 | run one consumer sync hook in exactly one off-loop worker | the boundary must also bind a ContextVar | **1** (`run_in_one_sync_boundary`) + 5 direct `sync_to_async(...)` sites with different subjects | F11 |
| C8 | "async-only iterable" | a new async-only shape must be recognized | **1** (`is_async_only_iterable`); `connection.py`'s `(AsyncIterator, AsyncIterable)` tests do NOT move | independent — F10 |
| C9 | prove an embedded node is genuine Django | provenance moves from `sys.modules` identity to an interpreter-level check | **1** (`_type_is_genuinely_django`), composed by name by `_is_reconstructable_node` | independent |
| C10 | admit a new inert query-parameter leaf type | one entry in `_INERT_VALUE_TYPES` + one normalizer | **2 declared inventories, mechanically pinned to agree** | independent by principle 9 |
| C11 | admit a new plain container type | prove side + rebuild side | **2, mechanically pinned** | independent by principle 9 |
| C12 | add a seal defect code | the seal's return + an arm at every message site that can reach it | **1 definition**, 6 message sites, **no gate** | gate-only — F3 |
| C13 | add a seal policy axis | one `_SealPolicy` field + one check in `_seal_or_defect` | **1** | independent (the worked-example shape) |
| C14 | relax "a pre-sliced source is rejected" for a new surface | `_SealPolicy.reject_sliced` + `connection.py::_guard_source_not_pre_sliced` | **2** | duplication — F4 |
| C15 | resolve one visible related object through the target's hook | the hook must also receive the relation descriptor | **2** (`visible_related_object`, `types/resolvers.py::_visible_related_object`) | duplication — F5 |
| C16 | the relation-membership pk comparison basis | a pk type whose `str()` is ambiguous | **2** (`_stringified`, `write_transaction.py::canonical_pk`) | rejected — F6 |
| C17 | a child queryset must stay on its parent's connection | a fourth child-seeding surface appears | **2** (`base_queryset(using=)`, `_SealPolicy.require_shared_alias`) + 1 member not enforced | F8 / D1 |
| C18 | re-seal a public `OrderSet.apply_*` return against frozen routing | the connection field must do it too | **1** (`_validate_post_orderset_result`) | independent; enforcement question is D3 |

**Experiments.**

```shell
uv run python docs/dry/temp-tests/dry-file-utils__querysets/probe_alias_policy.py
```

Read-only, zero SQL (the seal composes lazy query state only). Output:

```text
_DEFAULT_SEAL_POLICY: defect=None sealed_db='shard_b'
_UNRECOMPOSED_CHILD_POLICY: defect=None sealed_db='shard_b'
_PREFETCH_CHILD_POLICY: defect=('alias', 'shard_b') sealed_db=None
```

Proves the policy asymmetry D1 rests on: a queryset explicitly routed off the outer alias is
**accepted** under the policy `optimizer/walker.py::_build_child_queryset` seals with, and
**rejected** under the policy a `Prefetch` child gets. Status: `execution-verified`. Rejects the
wrong result "both child policies pin the alias".

```shell
uv run python docs/dry/temp-tests/dry-file-utils__querysets/probe_using_order.py
```

Read-only, zero SQL. Output: `default manager: shard_b shard_b True True` — for a default
manager, `manager.using(a).all()` and `manager.all().using(a)` produce the same `_db`, the same
SQL and the same type, i.e. the orders are indistinguishable at the seam `base_queryset` occupies.
Status: `execution-verified`. Rejects the wrong result "the two spellings differ for the seed this
function performs", which is what `base_queryset`'s docstring asserts (**D4**).

## Findings

No production edit is owed by a file item; each finding names the family that will own it.

### F1 — awaitable refusal and disposal has three definitions

- **Contract + variation.** A refused awaitable must be detected without awaiting it and then
  released (native coroutine closed, future cancelled) so no "coroutine was never awaited"
  RuntimeWarning escapes. Legitimate variation: what follows the disposal (raise
  `SyncMisuseError`, raise `ConfigurationError`, return a not-authenticated sentinel, append an
  error addendum) and whether disposal failures are suppressed.
- **Sites + roles.** *Definitions*: `utils/querysets.py::_dispose_sync_awaitable` (querysets.py:217,
  coroutine + future); `auth/mutations.py` #"is_authenticated.close()" (two inline copies at 505-511,
  coroutine only, wrapped in `contextlib.suppress(BaseException)`); `routers.py` #"application.close()"
  (279-285, coroutine only). *Consumers*: `reject_async_in_sync_context`, `_disposed_awaitable`,
  `apply_type_visibility_async`, `reject_awaitable_sync_source`, `reject_residual_async_source`,
  `utils/querysets.py::apply_orderset_sync` / `::apply_orderset_async`, `utils/permissions.py`,
  `mutations/permissions.py`, `relay.py` ×2. *Projection*: the `_disposed_awaitable` docstring,
  which already records "Four sites spelled this pair inline".
- **Challenges.** C5 → 3 definitions. Second axis: "futures must be awaited-with-timeout rather
  than cancelled" → the same 3.
- **Owner + lifetime.** Existing owner by responsibility: `utils/querysets.py::_dispose_sync_awaitable`.
  It is already the neutral cycle-safe substrate both `auth/` and the root import from
  (`auth/mutations.py` already imports `run_in_one_sync_boundary` from it), so no dependency is
  reversed. No stored derivation; no lifetime fields owed.
- **Distinct behavior to preserve.** `auth/mutations.py` suppresses `BaseException` from `.close()`
  because a hostile `is_authenticated` must classify as anonymous rather than raise; `routers.py`
  needs to know *whether* it disposed so it can append `_ASYNC_FACTORY_HINT`. `_disposed_awaitable`
  already returns that boolean. The suppression is the one genuine variation and would be an
  adapter, not a mode flag.
- **Behavioral proof.** `static-reviewed` — import moves and body composed by name; the refusal
  each site raises stays at the site. Rejects the wrong result "consolidating changes which
  exception a seam raises". An `execution-deferred` proof is NOT owed by this file item; the
  family item owes one for the `auth/` suppression arm.
- **Structural gate.** Owed by the family item, not here. Negative control it must survive: a
  behavior-preserving hand copy of `_dispose_sync_awaitable`'s two-branch body pasted back into
  `routers.py`. A name/existence assertion would pass that control, so the gate must be
  behavioral (assert no `RuntimeWarning` escapes with `filterwarnings = error` already armed).
- **Family.** `awaitable-refusal-and-disposal`.
- **Freshness.** `utils/querysets.py` `5907a1f72de42c71402886e7480ab559eb06a3af`,
  `auth/mutations.py` `dbe64995b87240b87a1d5119f46cc42c7cab646f`,
  `routers.py` `a18c5001471d4a937bb81d2ff41a2e442e7d2dad`.

### F2 — the sealed-execution-queryset boundary is one rule with one owner

- **Contract + variation.** A consumer-supplied or hook-returned queryset is untrusted query
  STATE: read it without dispatching consumer code, validate it, rebuild a framework-owned plain
  `QuerySet` from the validated state, never return the consumer object. Variation axes are
  declared, not branched: the five `_SealPolicy` fields and the seven policy constants.
- **Sites + roles.** *Definition*: `_seal_or_defect` and the ~60 helpers it composes — all in
  this file. *Consumers*: `_prepared_visibility_source`, `_normalized_visibility_result`,
  `_validate_post_orderset_result`, `normalized_row_source`, `_sealed_prefetch_related_lookups`
  (recursive), plus `permissions.py`, `list_field.py`, `optimizer/walker.py`, `connection.py`,
  `types/resolvers.py`, `resource_policy.py` through the runners. *Oracles*:
  `tests/utils/test_querysets.py`. *Projections*: the glossary anchors and spec-045.
- **Challenges.** C9, C10, C11, C13 — each forces exactly one definition (two mechanically-pinned
  inventories for C10/C11). No surface outside this file constructs a `models.QuerySet(...)` or
  touches `sql.Query` (searched package-wide: zero hits). `object.__getattribute__` /
  `type.__getattribute__` / `inspect.getattr_static` appear nowhere else in the package.
- **Distinct behavior.** The raw-list row-source rule (`normalized_row_source`,
  `_RAW_LIST_SOURCE_POLICY`) is deliberately a *different question* from visibility — it asks who
  owns the slice, not who may see the rows — and is recorded as its own policy constant rather
  than a branch. Kept.
- **Behavioral proof.** `static-reviewed` for the ownership claim (a package-wide search for the
  mechanism returned one definition). No edit, so no equivalence proof is owed.
- **Family.** `sealed-execution-queryset`. Named so a family item sweeps the whole package for the
  mechanism (`_meta.concrete_model` reads, `_iterable_class` / `_result_cache` / `is_sliced`
  reads, `Prefetch(` construction) rather than this file's neighbours; the four such readers
  found (`connection.py:1603`, `optimizer/nested_fetch.py:123,131,197`,
  `optimizer/predicates.py:165`, `optimizer/extension.py:1161`) all run on already-sealed
  framework-owned querysets and ask planning questions, which the family item should confirm
  independently.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `tests/utils/test_querysets.py`
  `c9a84d53f3e74e3f5274a6b5096ce1a17ceef292`.

### F3 — the seal's defect-code set is a rule with no gate (gate-only)

> **Revision 1 — the "Justified population for a gate" paragraph below is SUPERSEDED by I-R4.**
> This finding assumed the rule it proposes to gate currently holds. Measured, it does not: three
> sites in this file declare arms for codes their own call shape cannot produce. I-R4 restates the
> gate population against the tree as it is and routes the false-invariant docstring to `## Defects`
> as D5.

- **Contract + variation.** The seal's defect codes are a closed, canonically ordered set
  (`type` → `table` → `untrusted` → `routing` → `evaluated` → `sliced` → `combined` →
  `projection` → `alias`, stated at querysets.py:3039-3041). Every message-building site renders
  only the subset IT can reach, and "a new code takes a FIXED position in it, and owes an arm at
  every message-building site that can reach it".
- **Sites + roles.** *Definition*: the seal's own `return None, (code, detail)` statements — one
  definition, enacted by control flow. *Consumers*: six `_defect_message` call sites
  (`_validate_post_orderset_result`, `_raw_list_source_message`, `_visibility_result_error`,
  `_prepared_visibility_source`, `permissions.py:353`, `permissions.py:412`). *Projection*: the
  prose ordering in the `_seal_or_defect` docstring, and the per-site "which codes can reach me"
  paragraphs at querysets.py:2988-3005 and 3442-3446.
- **Challenges.** C12 → 1 definition, 6 sites that must be revisited by hand. `_defect_message`
  makes a missing arm *legible at runtime* (`tests/utils/test_querysets.py::test_unrendered_defect_code_says_so_instead_of_mislabelling`
  pins that) but nothing fails at build or test time. Per DRY.md this is a `gate-only` finding:
  owner already single, no gate.
- **Justified population for a gate.** The six `_defect_message` call sites, and the codes each
  reachable `_SealPolicy` can actually emit. Plausible bypass: a seventh site, or a new code whose
  author updates four of the six ladders. A bespoke existence test per helper is explicitly not
  what is wanted; the gate must enumerate the population independently.
- **Behavioral proof.** `static-reviewed`. No edit owed here.
- **Family.** `seal-defect-code-wording`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `permissions.py`
  `9e0236b3bbcfa9320a5d4e18e34b35c27adf233e`.

### F4 — "a pre-sliced source is rejected" has two definitions

- **Contract + variation.** A source a surface will recompose onto (reorder, refilter, window)
  may not arrive already sliced, because Django forbids reordering a sliced query and the next
  transform would raise a raw `TypeError` outside the typed contract. Legitimate variation:
  surfaces that do NOT recompose (a `Prefetch` child, the optimizer's nested-connection child)
  switch it off.
- **Sites + roles.** *Definitions*: `_SealPolicy.reject_sliced` + the `sliced` arm of
  `_seal_or_defect` (querysets.py:3291); `connection.py::_guard_source_not_pre_sliced`
  (connection.py:1602-1625), which reads `source.query.is_sliced` through ordinary attribute
  access on an untrusted consumer queryset and raises a `GraphQLError`. *Not a definition*:
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`, which classifies five shapes
  (`sliced`, `select_for_update`, `combined`, `distinct`, `values`) to **degrade a plan**, never
  to reject — a different contract with different reasons to change.
- **Challenges.** C14 → 2 definitions. Both give the same stated reason (recomposition is
  illegal on a sliced query); they differ in error class (`GraphQLError` vs
  `ConfigurationError`), in timing (before visibility vs during the seal) and in whether the read
  dispatches consumer code.
- **Owner + lifetime.** Candidate owner `utils/querysets.py::_SealPolicy` / `_seal_or_defect`.
  The family item must decide whether the connection's earlier, wire-flavored rejection is a
  legitimate adapter (it names the `resolver=` contract at the wire, which the seal's
  `ConfigurationError` does not) or a second definition to delete. Note the seal already rejects
  the same source one step later, so the guard is not load-bearing for fail-closed behaviour.
- **Coupling.** None. F4 and D3 both touch `connection.py`'s sidecar pipeline; they are
  independent decisions.
- **Behavioral proof.** `static-reviewed` (no edit). Any consolidation would owe an
  `execution-verified` proof that the error CLASS a client sees does not change, since
  `GraphQLError` and `ConfigurationError` surface differently at the boundary.
- **Family.** `recomposition-illegal-source-rejection`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `connection.py`
  `93e998f2c7ea1d7f18607a6e37e394466ac75ad4`, `optimizer/nested_fetch.py`
  `4d8d37a7f52cf94d2916f17db3a8a21393e28d57`.

### F5 — "resolve one visible related object" has two definitions

- **Contract + variation.** Given a related row and its target type, re-confirm the row is
  visible through the target's `get_queryset` hook before it crosses the boundary. Legitimate
  variation: the key (model vs registered type), the coloring (sync-only vs colored), and the
  tail (write-pipeline pin + lock vs `_state.db` pin).
- **Sites + roles.** *Definitions*: `utils/querysets.py::visible_related_object` (model-keyed,
  registry resolve, default-manager fallback, `pipeline_scoped_queryset`, sync-only);
  `types/resolvers.py::_visible_related_object` (type-keyed, `_state.db` pin, colored
  sync/async, no registry resolve, no pipeline scope). *Consumers*: `utils/write_values.py:226`,
  `types/resolvers.py` ×7. *Related, composed by name*: `visibility_scoped_related_queryset`,
  `related_visibility_queryset`, `related_visibility_queryset_or_default`,
  `rest_framework/resolvers.py:1447`.
- **Challenges.** C15 → 2 definitions. Second axis: "the visibility query must also be pinned to
  the write alias on the read path" → 2 again. Third axis: "the write decoder needs an async
  coloring" → 2.
- **Owner + lifetime.** Candidate owner `utils/querysets.py`. The shared kernel is
  `apply_type_visibility_*(target_type, initial_queryset(target_type).filter(pk=pk), info)`
  followed by `.first()` / `.afirst()`; what genuinely differs is the *seed pin* and the
  *coloring*, both of which are adapter-shaped. The family item must first try to disprove shared
  responsibility: the read-side re-check exists to confirm an already-prefetched row, the
  write-side decoder exists to admit a client-named row, and those may be two rules that agree
  today.
- **Behavioral proof.** `static-reviewed` (no edit). Any consolidation owes an
  `execution-verified` proof of query count and of the async coloring, since the read path
  returns a coroutine from a sync function.
- **Family.** `related-object-visibility-recheck`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `types/resolvers.py`
  `fc077f38a1f10db2a447c11b11bea1e82bcbb362`, `utils/write_values.py`
  `d28587c7c8d9f0d25e0a01bf289a63d9c3291728`, `rest_framework/resolvers.py`
  `8024703ec0fb09758daeec0585e0065de1c61fc3`.

### F6 — REJECTED: the two pk comparison bases are two rules

- **Shared form considered.** One canonical pk comparison primitive for the whole package,
  replacing both `utils/querysets.py::_stringified` (the `{str(pk) for pk in ...}` membership
  basis behind `stringified_pks_present` / `pks_all_present`) and
  `utils/write_transaction.py::canonical_pk` / `pks_match` (the `to_python`-both-sides equality
  behind `reject_substituted_row`).
- **Contract difference.** `_stringified` builds a *set membership basis* for a batched
  `pk__in` result, where both sides have ALREADY been canonicalized: the declared side passes
  through `type_check_relation_id` → `coerce_relation_pk_or_none` →
  `coerce_field_value_or_none` (`utils/write_values.py:302-309`) before
  `visible_related_objects` is called, and the present side comes back from the DB as the field's
  own Python type. Stringifying two already-canonical values is a *hashability* convenience, not
  a comparison rule. `canonical_pk` compares a consumer-supplied `save()` return against an
  authorization snapshot where NEITHER side is pre-coerced, which is exactly the case its comment
  warns about ("a UUID pk stringifies in more than one spelling of the SAME row"). It also raises
  rather than returning `None`, and deliberately skips `run_validators` (it is answering "same
  row?", not "may this literal enter a query?"). Merging them would either add validator
  rejection to an equality test or drop the fail-closed raise from an authorization check.
- **Reconsideration trigger.** If `stringified_pks_present` ever receives pks that have not
  passed `coerce_field_value_or_none` first — i.e. a caller reaches it without
  `type_check_relation_id` — the stringified basis stops being safe and the two collapse into one
  rule. Grep the callers of `stringified_pks_present` / `pks_all_present` for that.
- **Durable home for the rejection.** `utils/querysets.py::_stringified` (one plain clause noting
  the basis is valid only because both sides are pre-canonicalized). Not written by this item —
  a file item lands no edit; recorded here for the family item.
- **Related, also single-owned.** `coerce_field_value_or_none` has exactly one definition and
  three named consumers (`relay.py::_coerce_pk_or_none`, `utils/write_values.py::coerce_relation_pk_or_none`,
  `filters/base.py::_coerce_int_in_members`), each composing it by name against a different
  field — the "WHICH field stays at the caller" split is principle 2's "one owned translation",
  correctly applied. `keyset.py:384` uses `field.to_python` without validators for cursor decode:
  a third contract (round-trip re-serialization), not a copy.
- **Family.** `field-value-coercion`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `utils/write_transaction.py`
  `eca9ad4d3f765964df05884e080eb3ea63190ca8`, `utils/write_values.py` `d28587c7…`,
  `rest_framework/resolvers.py` `8024703e…`.

### F7 — REJECTED (re-verified): the two permission recourse sentences stay separate

- **Shared form considered.** Extending `sync_pipeline_recourse` to also generate
  `mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE` and
  `utils/permissions.py::_GATE_ASYNC_RECOURSE`.
- **Prior rejection re-derived, not inherited.** Both owners already record the rejection
  (`sync_pipeline_recourse` docstring declines them; `mutations/permissions.py:44-49` states
  "four of their clauses differ, so a template would take a parameter per clause and pin
  nothing"). Re-read both literals at this HEAD: the write recourse names
  `has_permission / check_permission`, requires a `bool` return, and names `user.has_perm` /
  auth backends; the gate recourse names `check_<field>_permission` and the FilterSet / OrderSet
  subject. They share one clause ("runs synchronously, so it cannot await"). Rejection stands.
- **Reconsideration trigger.** If either sentence is reworded so the two differ only in the
  subject noun — the exact shape `sync_pipeline_recourse` already solved for the three write
  flavors — they become one rule.
- **Also verified.** `_RELAY_ASYNC_RECOURSE` (querysets.py:349) stays separate for a stated
  reason that holds: async IS possible on the Relay branch, so its recourse offers a different
  remedy. `permissions.py::_ASYNC_RECOURSE` likewise (no async-native cascade walk exists).
- **Family.** `sync-boundary-recourse-wording`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `mutations/permissions.py`
  `54f770ae5aa1238327246cd2dcb141e8aac14965`, `utils/permissions.py`
  `9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`, `permissions.py` `9e0236b3…`.

### F8 — child-queryset alias inheritance: one rule, two enforcement mechanisms, one unguarded member

- **Contract + variation.** A queryset seeded for a relation's target model must read on the same
  database connection as the parent that seeded it, so one GraphQL resolution never spans two
  connections. Two mechanisms encode it: `base_queryset(model, using=...)` pins the *seed*, and
  `_SealPolicy.require_shared_alias` rejects a *hook result* routed elsewhere.
- **Sites + roles.** *Definitions*: `base_queryset`'s `using` arm (querysets.py:265);
  `_seal_or_defect`'s `require_shared_alias` arm (querysets.py:3299-3304). *Enforcement sites*:
  `permissions.py:692` (`using=state.alias`), `filters/sets.py:2592` (`using=parent_db`),
  `_sealed_prefetch_related_lookups` (threads the outer effective alias into the child seal).
  *Unguarded member*: `optimizer/walker.py:443` seeds without `using=` and seals under
  `_UNRECOMPOSED_CHILD_POLICY`, which does not set `require_shared_alias` — see D1.
  *Projection*: `docs/GLOSSARY.md` *Prefetch alias threading*.
- **Challenges.** C17 → 2 definitions, which is the correct count: they answer different
  questions (what the seed routes to; what the hook may change it to) and would not move
  together for a seed-spelling change. Not a consolidation candidate.
- **Coupling.** D1 must be resolved before any consolidation here; an alias rule with an
  unguarded member is not a rule whose owner can be moved.
- **Behavioral proof.** `execution-verified` via `probe_alias_policy.py` above, for the policy
  asymmetry. `static-reviewed` for the seed-site enumeration.
- **Family.** `child-queryset-alias-inheritance`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `optimizer/walker.py`
  `054207017c3435ed1f6b7891683fed112c807d11`, `permissions.py` `9e0236b3…`,
  `filters/sets.py` `4ab65a26b0ccf56f7f40f4938282bba9690673d1`, `docs/GLOSSARY.md`
  `37a61802fbb2c257d12e33b34bc3ea1a08c4b3fa`.

### F9 — `is_async_queryset_adapter` has no production reader (principle 11)

- **Contract.** `_AsyncQuerySetRows` is the async-only completion adapter; three module-level
  functions surround it: `wrap_async_queryset_adapter`, `unwrap_async_queryset_adapter`,
  `is_async_queryset_adapter`.
- **Sites + roles.** *Definition*: querysets.py:414-416. *Production readers*: **none**, searched
  package-wide. `list_field.py` uses only `wrap_`; `optimizer/extension.py:1142-1145` uses
  `unwrap_` (which returns `(value, was_adapted)`) and `wrap_`. *Test readers only*:
  `tests/test_list_field.py` ×7, `tests/optimizer/test_extension.py` ×9. Not in any `__all__`,
  not re-exported from the package root.
- **Challenge.** "What breaks if it is removed and inlined?" Nothing in production. The 16 test
  assertions would spell `isinstance(x, _AsyncQuerySetRows)` or read the second element of
  `unwrap_async_queryset_adapter`. Note the current tests are NOT independent oracles for the
  adapter — they check the owner's own predicate against itself — so the deletion question is
  entangled with whether those assertions should name the class instead.
- **Owner + lifetime.** Decision (keep as a boundary name callers depend on, or delete and
  inline) belongs to the family item, which must also decide the oracle shape. DRY.md requires
  the keep-or-move outcome to be recorded at the owner so the question is not re-raised.
- **Behavioral proof.** `static-reviewed` (search for readers, whole repo minus `.git` and
  `docs/shadow`). Rejects the wrong result "it is used by the optimizer".
- **Family.** `async-only-queryset-row-adapter`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `list_field.py`
  `f357eded3d96fcffe17e6fd84bceb8cd12af98d5`, `resource_policy.py`
  `9205124f41814dbda5a7df0a4882e10b5f951b2f`.

### F10 — REJECTED: `connection.py`'s async-shape tests are not a second `is_async_only_iterable`

- **Shared form considered.** Routing `connection.py:1050`, `:1095` and `:1575` through
  `is_async_only_iterable`.
- **Contract difference.** `is_async_only_iterable` is `AsyncIterable and not Iterable`; the
  `not Iterable` half exists precisely so a `QuerySet` (both sync- and async-iterable) never
  classifies as async-only. `connection.py:1050` / `:1095` ask the OPPOSITE question — "may the
  async executor stream this?" — and must answer **yes** for a QuerySet, which is the branch they
  take. `connection.py:1575` is an admission test (`Iterable` OR `AsyncIterable` OR
  `__getitem__`), a union rather than a difference. Substituting the shared predicate would send
  every queryset down the sync branch under async execution.
- **Reconsideration trigger.** If the connection field ever needs to tell an async-only consumer
  source apart from a queryset — e.g. to apply the same sync-execution refusal the list field
  applies — that new site is the shared rule's, not a fourth spelling.
- **Confirmed consumers of the real predicate.** `reject_async_iterable_in_sync_context`
  (this file), `list_field.py:891/895`, `resource_policy.py`. All three composed by name.
- **Family.** `sealed-execution-queryset` is not the right home; recorded under
  `async-only-queryset-row-adapter`, which owns the async-shape vocabulary.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `connection.py` `93e998f2…`,
  `resource_policy.py` `9205124f…`, `list_field.py` `f357eded…`.

### F11 — the one-sync-boundary rule has one definition and five direct-call sites to classify

- **Contract + variation.** A consumer-overridable sync hook must run in exactly ONE
  `sync_to_async(thread_sensitive=True)` worker per resolution, never per-step hops.
- **Sites + roles.** *Definition*: `run_in_one_sync_boundary` (querysets.py:483). *Consumers
  composing it by name*: `schema.py:73`, `permissions.py:125`, `orders/sets.py:50`,
  `filters/sets.py`, `mutations/resolvers.py:104`, `auth/mutations.py:73`. *Direct
  `sync_to_async(...)` calls not routed through it*: `types/resolvers.py:616/689/760`
  (`sync_to_async(getattr, thread_sensitive=True)` — a relation attribute read, not a consumer
  hook) and `testing/client.py:471/475` (`force_login` / `logout`, no `thread_sensitive` argument
  at all, and the test client is not a resolver surface).
- **Challenge.** C7 → 1 definition. The five direct sites do not encode the rule (they are not
  wrapping a consumer-overridable hook), so they are neither definitions nor enforcement sites of
  it. Recorded so a family item does not re-derive the classification, and so the
  `testing/client.py` omission of `thread_sensitive=True` is looked at deliberately rather than
  swept in.
- **Behavioral proof.** `static-reviewed`. No edit owed.
- **Family.** `one-sync-boundary`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `types/resolvers.py` `fc077f38…`.

### F12 — file-local rules (no second site after the matrix)

Each carries the challenge that proved it. None is assigned to a family; each stays owned here.

> **Revision 1 — two rows in this table are SUPERSEDED, and the table is incomplete.** The
> `_safe_class_name` row and the `_prefetch_relation_target_or_none` row both claim "no second
> site" for rules that have one; they are replaced by I-R1 and I-R2 in `## Iterations`, which
> record them as REJECTIONS with a contract difference and a reconsideration trigger. Two rules
> the original table omitted entirely are added as I-R3 and I-R5. The remaining rows stand as
> written and were re-checked in revision 1. Prior text is left intact per DRY.md.

| Rule | Owner | Challenge posited | Definitions |
|---|---|---|---|
| Render a class name without letting hostile metaclass metadata escape, STRICTER than the shared renderer (a non-`str` `__name__` degrades to the metaclass label rather than `repr(name)`) | `utils/querysets.py::_safe_class_name` | "the fallback must also strip control characters" | 1 here; `exceptions.py::_safe_class_name` is a separate, deliberately weaker rule for non-boundary messages, documented at querysets.py:142-150 |
| Format database routing intent without invoking consumer `__repr__` | `_safe_routing_repr` | "hint values must render their id in decimal" | 1 (readers: `_seal_or_defect`'s routing arm, `tests/utils/test_querysets.py`, `tests/test_list_field.py`) |
| Three-state identity bookkeeping distinguishing a shared diamond from a cycle | `_GraphWalk` / `_WalkState` / `_walk_short_circuit` | "a fourth state is needed for a partially-validated node" | 1 (7 in-module callers; no other recursive proof in the package) |
| Freeze a source's routing intent before consumer code receives it | `_snapshot_routing_intent` | "the snapshot must also capture `_for_write`" (it does) | 1 (sole external consumer `list_field.py`) |
| Compare routing hints by identity, never by equality | `_routing_hints_equal` | "absent vs empty hints must stop being distinguished" | 1 |
| The `(negate, args, kwargs)` deferred-filter bake onto a detached clone | `_bake_deferred_filter_or_defect` + `_deferred_value_defect` | "a fourth prohibited kwarg ships in Django" (the `PROHIBITED_FILTER_KWARGS` import + floor mirror at querysets.py:100-108 is the single site) | 1 |
| Resolve a prefetch path to its relation target, including the default `<model>_set` accessor spelling | `_prefetch_relation_target_or_none` + `_reverse_relation_by_accessor_or_none` | "a `GenericForeignKey` alias must resolve rather than fail open" | 1 |
| The list-field consumer-resolver head order: refuse the wrong async shape, THEN normalize, THEN per-branch guard | `prepared_resolver_source` | "a third per-branch guard is needed" | 1 (both collection flavors compose it) |

## Defects

Non-duplication defects found while tracing. None fixed here.

### D1 — the optimizer walker's prefetch child can be re-routed to another database by its own visibility hook

`optimizer/walker.py::_build_child_queryset` seeds `base_queryset(field.related_model)` with no
`using=`, so `_prepared_visibility_source` resolves `required_alias = queryset._db` = `None`, and
seals under `_UNRECOMPOSED_CHILD_POLICY`, which does not set `require_shared_alias`. A target type
whose `get_queryset` returns `qs.using("other")` therefore passes, and the result is installed as
`Prefetch(lookup_path, queryset=child_queryset)` at `optimizer/walker.py:916` — a prefetch child
on a different connection from its parent. The plan applies that prefetch after visibility, so it
never passes back through `_sealed_prefetch_related_lookups`, which is where
`require_shared_alias` would have caught it.

Proven by `docs/dry/temp-tests/dry-file-utils__querysets/probe_alias_policy.py` (output above):
the same explicitly-routed queryset is accepted under `_UNRECOMPOSED_CHILD_POLICY` and rejected
with `('alias', 'shard_b')` under `_PREFETCH_CHILD_POLICY`.

Contract sources establishing the rule for this member: `_SealPolicy.require_shared_alias`
("Set solely for a `Prefetch` child, so one GraphQL resolution never spans two database
connections", querysets.py:2750-2753); `base_queryset`'s `using` paragraph ("a sharded parent must
seed its children on the SAME connection", querysets.py:256-262), which names the optimizer
walker's prefetch child as one of the three surfaces that seed from a relation's target model; and
`docs/GLOSSARY.md` *Prefetch alias threading*. The two sibling members named alongside it
(`permissions.py:692`, `filters/sets.py:2592`) both thread the alias.

Adding the guard changes what is accepted, so it is never behavior-preserving and must not ride a
consolidation. **Routes to:** the sealed-execution-queryset / visibility-boundary owner —
`optimizer/walker.py::_build_child_queryset` and `_UNRECOMPOSED_CHILD_POLICY`. Needs a named
owning card. Behavior is only observable under `FAKESHOP_SHARDED=1` or a multi-database settings
fixture, which this run is not authorized to execute (see `## Pending execution`).

### D2 — the glossary describes a keyword that no longer exists

`docs/GLOSSARY.md:1556` (*Prefetch alias threading*) states "The child seal allows a sliced
top-N-per-parent prefetch queryset (`allow_sliced=True`)". `allow_sliced` occurs **zero** times
under `django_strawberry_framework/`; the `_SealPolicy` record replaced the threaded keyword, and
the current spelling is `_PREFETCH_CHILD_POLICY = _SealPolicy(reject_sliced=False,
require_shared_alias=True)`. The glossary is rendered from the fakeshop `glossary` app DB, so the
repair is a `GlossaryTerm` body edit plus a re-render, not a file edit.

`docs/SPECS/spec-034-permissions-0_0_10.md:353` carries the same retired call shape inside a
"**Verified dependency to protect**" clause —
`apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)` — which no longer
matches the code it pins. (The four occurrences in
`docs/SPECS/spec-045-visibility_boundary-0_0_14.md` and the rationale appendices are historical
records of the shipped design and read correctly as such.)

**Routes to:** whoever introduced `_SealPolicy` — the in-flight spec-050 card. Needs a named
owning card.

### D3 — ambiguous: the connection field runs `OrderSet.apply_*` with no post-apply result seal

As raised, the list field froze routing intent before the public override ran and re-sealed its
return through `_validate_post_orderset_result` (`_ORDERSET_RESULT_POLICY`: model rows,
unevaluated, unsliced, uncombined, same route), while `connection.py:1828` / `:1865` invoked the
same public `OrderSet.apply_sync` / `apply_async` on a sealed queryset and passed the return
straight to `_finalize_queryset` with neither the snapshot nor the re-seal. That seal no longer
belongs to the list field: it lives in this module as
`utils/querysets.py::apply_orderset_sync` / `::apply_orderset_async` and is called from
`list_field.py` and from `connection.py::_pipeline_sync` / `::_pipeline_async`, so both fields
run one snapshot-plus-re-seal on the same result axes. The `FilterSet.apply_*` return is the
half still unsealed at both.

Per the axis-6 rule, sibling behaviour justifies the investigation but not the verdict. The two
contract sources found both scope the rule to the list field:
`docs/spec-050-list_field_arguments-0_0_15.md` Edge cases ("A custom `OrderSet.apply_*` result
must SEAL to a lazy, unsliced, model-row-shaped, non-combined, same-model, same-route plain
queryset") is a list-field spec, and `_SealPolicy.require_unevaluated`'s prose reasons from "the
list field invoked that ordering method one step earlier and takes its window on what comes back".
The connection field also windows what comes back (Relay cursor slicing via
`ListConnection`), which is why this is not simply out of scope. **Ambiguous or newly proposed →
routed to the maintainer** through Worker 0. No fix, and no consolidation depends on it.

### D4 — `base_queryset`'s docstring states a distinction its body's reason does not support

querysets.py:257-260 asserts the seed is spelled "`manager.using(alias).all()` (never
`.all().using(alias)`): a sharded parent must seed its children on the SAME connection". The
stated reason justifies passing `using` at all, not the ORDER. Measured
(`docs/dry/temp-tests/dry-file-utils__querysets/probe_using_order.py`): for a default manager the
two spellings produce the same `_db`, the same SQL and the same queryset type — they are
indistinguishable at the seam this function occupies. Two package sites already write the
"never" spelling (`rest_framework/resolvers.py:1849` and `:1955`,
`getattr(instance, source).all().using(alias)`), so the prohibition is also unenforced and
unenforceable as stated.

Per AGENTS.md style ("Removed attribution carried the WHY → restate as one plain clause from the
code"; a wrong stated reason is worse than none, because the next author honors it), the clause
should either be dropped or replaced with the real reason if one exists for a non-default manager.
**Routes to:** `utils/querysets.py::base_queryset`. Needs a named owning card, or folding into the
`child-queryset-alias-inheritance` family item alongside D1.

### D5 (revision 1) — three message sites declare arms for defect codes they cannot produce, and one asserts the opposite as fact

Raised by Worker 2 (its C1/R2), independently re-derived here from source rather than taken on
trust; full derivation and the one place I qualify Worker 2's instrument are in `## Iterations`
I-R4.

The rule is stated at its owner: `_defect_message`'s docstring ("each message-building site
renders only the subset IT can reach") and, more sharply, `_validate_post_orderset_result`'s
inline comment ("an arm for a code that cannot arrive would be wording no rejection can ever
quote"). Three sites in this file break it:

| site | dead arm(s) | why the code cannot arrive |
|---|---|---|
| `utils/querysets.py::_raw_list_source_message` | `combined` | its only caller passes `_RAW_LIST_SOURCE_POLICY`, which leaves `reject_combined` at its `False` default |
| `utils/querysets.py::_prepared_visibility_source` | `routing`, `evaluated` | it calls `_seal_or_defect(queryset, model, None, policy)` with no `expected_routing`; none of the four policies that can reach it sets `require_unevaluated` |
| `utils/querysets.py::_visibility_result_error` | `routing`, `evaluated` | reached only from `_normalized_visibility_result`, same two facts |

Both `permissions.py` sites are correct, which is what shows the comparison can tell a right site
from a wrong one.

The defect proper — the D4-class half — is `_raw_list_source_message`'s docstring, which asserts
the false state as fact: *"Only the defects `_RAW_LIST_SOURCE_POLICY` can actually reach have
arms: `evaluated`, `sliced` and `projection` are switched off by that policy, and `routing` /
`alias` need an expectation this surface never states."* Its own enumeration omits `combined`,
which that policy also switches off, and the `combined` arm sits four lines below the sentence.
Same class as D4: a wrong stated reason is worse than none, because the next author honors it.

`fail_under = 100` cannot see any of this — every arm is a value in one dict literal, so a dead
arm is "covered" by the statement that builds the mapping.

**Routes to:** `utils/querysets.py::_raw_list_source_message` (the docstring), with
`_prepared_visibility_source` and `_visibility_result_error` named as the two sibling sites
carrying dead arms. Family `seal-defect-code-wording`. Needs a named owning card. Deleting a dead
arm changes no observable behavior (no rejection can quote it), but it is still not a file-item
edit.

## Pending execution

Three commands this run is not authorized to issue. None blocks the item; all are listed so the
gate carries them.

1. `proof:` `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query -k prefetch --no-cov`
   — discharges D1's observable half: that a nested-connection prefetch child whose target
   `get_queryset` returns `.using("shard_b")` actually reads the other shard at fetch time.
   Needs the maintainer's separate authorization for the sharded mode; until then D1's cross-connection
   *consequence* stays `unverified` (the policy asymmetry itself is already
   `execution-verified` by the read-only probe).

2. `gate:` `uv run pytest tests/utils/test_querysets.py tests/test_list_field.py tests/optimizer/test_extension.py --no-cov`
   — the one focused shared-tree run this item is authorized for was not spent, because the item
   landed no edit and every finding's proof is either a package-wide search or the two read-only
   probes already run. Listed so the gate can confirm the three suites that own this file's
   oracles are green at the cycle's end, and so F9's claim (that only tests read
   `is_async_queryset_adapter`) is exercised rather than only searched.

3. *(revision 1)* `gate:` `uv run python docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py`
   — re-runs D5's reachability measurement at gate time. It is read-only and I already ran it
   against the shared tree during this revision (output reproduced in `## Iterations` I-R4), so
   it is listed not as a deferred proof but as a **regression witness**: if a family item deletes
   the three dead arms, this probe is what shows the state changed, and if one is added back the
   probe is what catches it. The gate should expect `sites with a mismatch: 4/6` today and should
   read I-R4 before treating a change in that number as a pass or a fail — one of the four rows
   (`_validate_post_orderset_result`, `missing: ['alias']`) is a modelling artifact, not a defect.

## Judgment

`utils/querysets.py` is, by a wide margin, the most DRY-disciplined file in the package: the
mechanisms it owns (`object.__getattribute__` state extraction, genuineness-by-identity, the
seal, Manager coercion, the definition-model read) each have exactly one definition package-wide,
several of its type inventories carry real principle-9 agreement gates, and its two colored
runners share every pure decision. The `_SealPolicy` record is a textbook instance of the worked
example's shape — declare the variation, share the meaning — and it already closed a documented
sync/async drift.

What the matrix did surface is mostly *outside* the file, which is the point of tracing a rule
rather than a module: three inline copies of the awaitable-disposal pair, two definitions of the
pre-sliced refusal, two of the related-object visibility re-check, and one member of the
child-alias family with no guard at all. Twelve families are named for Worker 0; four of them
(`awaitable-refusal-and-disposal`, `recomposition-illegal-source-rejection`,
`related-object-visibility-recheck`, `child-queryset-alias-inheritance`) carry live consolidation
or defect work and should be dispatched before the `utils/` folder item. The remaining eight are
expected to close as zero-edit or gate-only, but each needs the package-wide mechanism sweep a
file item is not allowed to substitute for.

Four defects routed, none fixed. No file-local rule was left unassigned, and no production edit
was owed or made.

## Implementation (Worker 1)

No tracked changes. Zero production edits, zero test edits, zero new tracked files — a file item
never owes a production edit, and every candidate found is named for its holding family instead.

Untracked scratch created (outside the tracked tree's concern, to be removed by Worker 0 after
verification, by explicit path):

- `docs/dry/temp-tests/dry-file-utils__querysets/probe_alias_policy.py`
- `docs/dry/temp-tests/dry-file-utils__querysets/probe_using_order.py`

Both are read-only against the live package and execute zero SQL. No disposable workspace was
needed: nothing in this item mutates source, so `scripts/prove_failability.py` was never run and
`<scratch>/dry-ws/` was never created. `uv run ruff format .` / `uv run ruff check --fix .` were
not run, because no tracked file was edited.

Item-scoped diff versus `ITEM_BASELINE=b2ec17eea042873767e2e30ebcdffa9e7e1ecaca` for the paths
this item touches: empty. `django_strawberry_framework/utils/querysets.py` is clean at HEAD, blob
`5907a1f72de42c71402886e7480ab559eb06a3af`, unchanged from dispatch.

Concurrent work observed and left alone. These paths are dirty but absent from the plan's
`## Cycle baseline` block, and they grew during the item (the last three appeared between the
first and last `git status` of this pass):

```text
 M examples/fakeshop/test_query/README.md
 M examples/fakeshop/test_query/test_library_api.py
 M examples/fakeshop/test_query/test_products_api.py
 M tests/forms/test_converter.py
 M tests/forms/test_inputs.py
 M tests/forms/test_resolvers.py
 M tests/forms/test_sets.py
```

None is a path this item touches, so per DRY.md "dirt elsewhere is concurrent work to leave
alone, not a stop" — reported to Worker 0 for reconciliation rather than acted on.

## Independent verification (Worker 2)

Written BEFORE reading `## Findings` / `## Defects` / `## Pending execution` / `## Judgment` /
`## Implementation (Worker 1)`. Everything under "My own trace" below was derived from the target,
the package, the tests and the installed Django/asgiref sources alone.

### Workspace and freshness, recorded before any verdict

Fresh copy taken after Worker 1's pass:
`<scratch>/dry-ws/w2-file-utils__querysets`.

- `uv run --project "$WS" --directory "$WS" python -c "import django_strawberry_framework as p;
  print(p.__file__)"` -> `$WS/django_strawberry_framework/__init__.py` (the workspace copy, not the
  shared checkout). `__version__` = `0.0.15`.
- Database `NAME` resolved from inside `$WS` with `config.settings` ->
  `$WS/examples/fakeshop/db.sqlite3`. No shared-tree database is opened by anything below.
- `git hash-object $WS/django_strawberry_framework/utils/querysets.py` =
  `5907a1f72de42c71402886e7480ab559eb06a3af`, byte-identical to the shared tree AND to
  `git ls-tree HEAD` at `e9e4d45c`. The target is unmodified at HEAD.

Item-scoped diff verified empty for myself:

```shell
git diff b2ec17eea042873767e2e30ebcdffa9e7e1ecaca -- django_strawberry_framework/   # no output
git ls-files --others --exclude-standard django_strawberry_framework/               # no output
```

The whole package is clean against HEAD; `## Owned changes` is empty and needs no row. Two paths
went dirty during my pass that are in neither the plan's `## Cycle baseline` list nor the
dispatch's addendum — `docs/spec-050-list_field_arguments-0_0_15.md` and
`docs/spec-050-list_field_arguments-0_0_15-rationale.md`. Neither is a path this item touches and
neither is package source; reported to Worker 0, not acted on.

### My own trace

**Inventory, counted not estimated.** `ast` over the target at the fingerprint above: 102
module-level functions, 7 classes (`SyncMisuseError`, `_AsyncQuerySetRows`, `_WalkState`,
`_GraphWalk`, `_UntrustedBoundValueError`, `_SealPolicy`, `_RoutingIntent`), 25 module-level
constants. The plan's `## Responsibility index` assigns 20 rows to this file (12 families + 8
file-local). Every symbol above maps onto one of those 20 rows except the ones I name under
"Where I differ".

**Rules I traced, with the change I posited and the authoritative-definition count.**

1. *Awaitable refusal and disposal.* Posited change: "a rejected awaitable must also be reported to
   the operation-state extension before it is disposed." Definitions that must move: 1 —
   `_dispose_sync_awaitable`. `_disposed_awaitable`, `reject_async_in_sync_context`,
   `reject_awaitable_sync_source`, `reject_residual_async_source` and the async runner's nested
   rejection all call it. Consumers outside the file (`auth/mutations.py`, `routers.py`,
   `list_field.py`, `relay.py`, `utils/permissions.py`, `mutations/permissions.py`,
   `connection.py`) are enforcement sites, not definitions. Second posited change: "the refusal
   message gains a common prefix" — count 4 (the four raise sites keep their own prose by a stated
   hot-path reason). Owner I would choose: unchanged, `_dispose_sync_awaitable`. Family
   `awaitable-refusal-and-disposal` is the right holder.

2. *Sealed-execution queryset.* Posited change: "a new untrusted shape (a consumer `__class_getitem__`
   on an expression) must fail closed." Definitions forced: 1 — `_seal_or_defect`, reached from
   exactly 5 call sites, all inside this file (`_sealed_prefetch_related_lookups`,
   `_validate_post_orderset_result`, `normalized_row_source`, `_prepared_visibility_source`,
   `_normalized_visibility_result`). Grepped the package: no second `sql.Query`-rebuilding body
   exists. Second posited change: "every framework invocation of the `get_queryset` hook must log."
   `rg "\.get_queryset\(" django_strawberry_framework/` returns 4 hits: two in this file (the two
   colored runners) and two that are not the hook (`optimizer/plans.py` prose,
   `filters/base.py::super().get_queryset(request)`, a django-filter API). Count 2 — the sync/async
   twin, which principle 5 keeps as two colored bodies sharing `_prepared_visibility_source` +
   `_normalized_visibility_result`. Owner: unchanged. Family `sealed-execution-queryset`.

3. *Seal defect-code wording.* Posited change: "add a `locked` defect code to the seal." Definitions
   forced: 1 (`_seal_or_defect`) plus an arm at every message site that can reach it. `_defect_message`
   has ONE definition and 6 call sites (4 here, 2 in `permissions.py`), each owning its own prose —
   which is the correct shape. **But the invariant those sites state is false at three of them**; see
   "Candidates I raise" C1. Family `seal-defect-code-wording`.

4. *Recomposition-illegal source rejection.* Posited change: "a new axis — reject a queryset carrying
   `select_for_update`." Definitions forced: 1 — a field on `_SealPolicy` plus its check in
   `_seal_or_defect`. All 7 policy constants are declared in this file and each is consumed at exactly
   one boundary (`_DEFAULT`, `_CASCADE` -> `permissions.py`, `_UNRECOMPOSED_CHILD` ->
   `optimizer/walker.py`, `_PREFETCH_CHILD` -> the inner seal here, `_LIST_ARGUMENT_VISIBILITY` ->
   `list_field.py`, `_ORDERSET_RESULT` and `_RAW_LIST_SOURCE` -> here). This is principle 1 executed
   exactly: declaration, not method. Owner: unchanged. Family
   `recomposition-illegal-source-rejection`.

5. *Related-object visibility recheck.* Posited change: "a hidden relation target must raise instead
   of returning `None`." Definitions forced: 2 —
   `utils/querysets.py::related_visibility_queryset_or_default` (model-keyed, sync-only, registry
   resolve, default-manager fallback, write-pipeline pinned) and
   `types/resolvers.py::_visible_related_object` (type-keyed, already-fetched instance, reads
   `related._state.db`, colored async branch, `afirst()`, no fallback). Same NAME, different
   contract. The read-side one is the second definition a seed naming only `utils/` would miss.
   Family `related-object-visibility-recheck` already lists `types/resolvers.py` among its files, so
   the assignment is right; the family item owes the disprove attempt.

6. *Field-value coercion.* Posited change: "a coercion failure must carry the offending literal."
   Definitions forced: 1 — `coerce_field_value_or_none`. `relay.py`, `filters/base.py`,
   `utils/write_values.py` call it; WHICH field is a per-caller decision, recorded in the docstring.
   I independently reach the same rejection.

7. *Sync-boundary recourse wording.* Posited change: "the write-flavor recourse must name the
   settings key that relaxes it." Definitions forced: 1 — `sync_pipeline_recourse`. The Relay
   recourse (`_RELAY_ASYNC_RECOURSE`, async IS possible) and the permission recourse (about
   `has_permission`/`check_permission`, not `get_queryset`) do not move. Rejection stands; the
   contract difference is stated at the owner.

8. *Child-queryset alias inheritance.* Posited change: "a sharded parent must seed every child on the
   parent's connection." Definitions forced: 1 — `base_queryset(..., using=)`. Enforcement sites:
   `permissions.py` (`using=state.alias`), `filters/sets.py` (`using=parent_db`),
   `optimizer/walker.py` — which calls `base_queryset(field.related_model)` with **no** `using=`.
   That is axis 6 (enforcement by omission) with a contract source: `_PREFETCH_CHILD_POLICY`'s
   `require_shared_alias` states the one-resolution-one-connection rule in this file's own prose.
   I reach `defect-routed` independently.

9. *Async-only queryset row adapter.* Posited change: "the adapter must also expose `__len__`."
   Definitions forced: 1 — `_AsyncQuerySetRows`. `is_async_only_iterable` is the one spelling of the
   async-only predicate (3 consumers: `list_field.py`, `resource_policy.py`, and the local
   `reject_async_iterable_in_sync_context`). **`is_async_queryset_adapter` has no production reader
   at all** — `rg` across the tree outside `docs/` finds it only at its definition and in
   `tests/test_list_field.py` (5 asserts) / `tests/optimizer/test_extension.py` (6 asserts). It is a
   test-only accessor, i.e. principle 11. I reached this independently; see C3.

10. *Post-set-apply result validation.* Posited change: "the post-OrderSet seal must also pin the
    schema's read-replica choice." Definitions forced: 1 — `_snapshot_routing_intent` /
    `_RoutingIntent` / `_validate_post_orderset_result`, a round-trip pair (freeze -> compare) both
    halves of which live here. Consumers: `list_field.py`, `connection.py`.

11. *One sync boundary.* Posited change: "the boundary must carry an operation lease across the
    worker." Definitions forced: 1 — `run_in_one_sync_boundary`. Enforcement sites named by the
    index: `schema.py`, `permissions.py`, `orders/sets.py`, `filters/sets.py`,
    `mutations/resolvers.py`, `auth/mutations.py`. I swept `rg "sync_to_async\("` over the package
    and found the raw call still spelled inline at `types/resolvers.py` (three
    `sync_to_async(getattr, thread_sensitive=True)` sites) and `testing/client.py` (two bare
    `sync_to_async(...)` calls; asgiref's default for `thread_sensitive` is `True`, verified in
    `.venv/.../asgiref/sync.py`, so they are behaviorally the same boundary). Both files ARE in the
    family's "files covered" list, so the assignment is right and the family item owes the verdict
    on whether these five compose or restate.

12. *Queryset seed and model read.* Posited change: "a registered type may override its seed
    manager." Definitions forced: 2 — `model_for` (the definition read) and `base_queryset` (the
    manager read), which `initial_queryset` composes. `relay.py` deliberately takes the raw manager
    instead, and that separation is recorded at `base_queryset`. Nine consumer files.

**Matrix, discharged against the real surface.**

1. *Cross-flavor policy mirroring.* Searched. The file's rules cross into `types/`, `forms/`,
   `rest_framework/`, `mutations/`, `filters/`, `orders/`, `optimizer/`. Every relation-visibility
   flavor composes by name (`write_values.py` -> `visible_related_object` / `visible_related_objects`
   / `pks_all_present`; `rest_framework/resolvers.py` -> `related_visibility_queryset`;
   `forms/resolvers.py` -> `visibility_scoped_related_queryset`). The one flavor that does NOT is
   `types/resolvers.py::_visible_related_object` (rule 5 above).
2. *Sync/async twins.* Searched. Three pairs: `apply_type_visibility_sync`/`_async`,
   `post_process_queryset_result_sync`/`_async`, `reject_awaitable_sync_source`/
   `reject_residual_async_source`. All three share their pure decisions
   (`_prepared_visibility_source` + `_normalized_visibility_result`; `prepared_resolver_source`;
   `_disposed_awaitable`) and keep only the await point and the exception class apart. I checked the
   async runner reaches every `_SealPolicy` axis the sync one does (both take `policy=` and thread it
   to both seals) — the drift the policy record was introduced to close is in fact closed.
3. *Derived rather than repeated knowledge.* Searched. `__django_strawberry_definition__.model` is
   spelled once, inside `model_for`; the only other textual hit is prose in `types/relay.py`.
   `_default_manager` reaches an executable site only in `base_queryset` and the one recorded
   exception in `relay.py`. `_meta.concrete_model` is read through `_concrete_or_none`.
4. *Inverse / round-trip pairs.* Searched, four found, all with both halves in this file:
   `_INERT_VALUE_TYPES` <-> `_BOUND_VALUE_NORMALIZERS`; `_PLAIN_CONTAINER_TYPES` <->
   `_reconstructed_value`'s container branches; `wrap_async_queryset_adapter` <->
   `unwrap_async_queryset_adapter`; `_snapshot_routing_intent` <-> `_validate_post_orderset_result`.
   The first two are the dangerous direction (prover-accepted / rebuilder-unhandled) and both carry a
   real agreement test in `tests/utils/test_querysets.py` (`assert set(samples) ==
   set(_PLAIN_CONTAINER_TYPES)`; `assert set(_INERT_VALUE_TYPES) - {bool} == {base for base, _ in
   _BOUND_VALUE_NORMALIZERS}`). I confirmed both assertions exist in the test body rather than
   trusting the docstrings that claim them.
5. *Contracts restated in another medium.* Searched. Media: `tests/utils/test_querysets.py` (5760
   lines, oracle), `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` (projection, cited 38 times
   from this file — by Decision number, which `START.md` warns is an ordinal citation, but the spec
   is archived and its decisions are numbered contract items, so the ordinal is the contract's own
   identifier, not a heading position), `docs/TREE.md` (projection), the module docstring
   (projection). No test was found reading its expectation FROM the owner it checks.
6. *Enforcement by omission.* Searched, three members enumerated and checked. (a) Every `get_queryset`
   invocation routes through the two runners — proven by the 4-hit grep above, not assumed.
   (b) Every seal call site passes a `_SealPolicy` — all 5 do. (c) Every `base_queryset` child seed
   pins its alias — `optimizer/walker.py` does not (rule 8). This axis is the one that produced a
   real gap, so it was not discharged by assertion.

### Candidates I raise

**C1 — three message sites in this file declare arms for defect codes their own call shape cannot
produce, while the rule says they must not.** Owner of the rule: `_defect_message`'s docstring
("each message-building site renders only the subset IT can reach") and
`_validate_post_orderset_result`'s inline statement ("Each site renders the subset it can reach; an
arm for a code that cannot arrive would be wording no rejection can ever quote").
`_raw_list_source_message`'s docstring goes further and asserts the fact: "Only the defects
`_RAW_LIST_SOURCE_POLICY` can actually reach have arms". That sentence is false.

I proved it rather than argued it. Probe (read-only, run in `$WS`, saved at
`docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py`): for each site, derive the
reachable code set from the `_SealPolicy` values that actually reach it plus whether the site passes
`expected_routing` / a non-`None` `required_alias`, then diff against the arms the site declares
(read out of the AST, so the probe cannot be fooled by prose). Result:

| site | reachable | dead arms |
|---|---|---|
| `querysets.py::_raw_list_source_message` | `type`, `table`, `untrusted` | `combined` |
| `querysets.py::_prepared_visibility_source` | + `sliced`, `combined`, `projection` | `routing`, `evaluated` |
| `querysets.py::_visibility_result_error` | + `sliced`, `combined`, `projection`, `alias` | `routing`, `evaluated` |
| `permissions.py::_root_error_renderer` | `type`, `table`, `untrusted`, `sliced`, `combined` | none |
| `permissions.py::_edge_error_renderer` | + `alias` | none |

`_RAW_LIST_SOURCE_POLICY` leaves `reject_combined` at its `False` default, so the `combined` arm
cannot fire; `_prepared_visibility_source` never passes `expected_routing` and no policy reaching it
sets `require_unevaluated`, so `routing` and `evaluated` cannot fire there or at
`_visibility_result_error`. `_validate_post_orderset_result`'s one absent arm (`alias`) is the
opposite case and is argued correctly in its own comment — the seal reaches the alias check only
after `routing` admitted `candidate_db == intent.db`, and `_snapshot_routing_intent` pins
`effective_alias` to that same value.

Negative control inside the probe: it asserts `_RAW_LIST_SOURCE_POLICY` does NOT reach `sliced` /
`projection` / `combined`, so a reachability model that fell open (returning every code) fails the
control instead of printing a clean table. Both `permissions.py` sites coming back `OK` is the
positive control: the comparison can distinguish a correct site from an incorrect one.

Why this matters beyond tidiness: the invariant is stated at the owner and enforced by nobody, and
`fail_under = 100` cannot see it — every arm is a value in one dict literal, so the dead arms are
"covered" by the statement that builds the mapping. This is the shape `DRY.md` principle 9 exists
for. **Routing: family `seal-defect-code-wording`** (which already lists `utils/querysets.py` and
`permissions.py`, the two files involved). It is not a file-item edit and I do not ask for one.

**C2 — `_prefetch_relation_target_or_none` is recorded file-local, but a second definition of the
`LOOKUP_SEP` path walk exists.** `utils/relations.py::classify_path` (with
`_resolve_segment_field` / `_lenient_traverses_to_many`) is the package's authoritative
segment-by-segment walk through `Model._meta.get_field`; `connection.py`, `optimizer/plans.py` and
`utils/permissions.py` each run one too. `_prefetch_relation_target_or_none` is a fourth. The
contract difference is real and I would expect the rejection to survive — `classify_path` resolves
DECLARED field-map names and RAISES `PathResolutionError`, while the prefetch resolver must also
accept the `<model>_set` reverse-accessor spelling Django's prefetch traversal reaches (verified
against `_reverse_relation_by_accessor_or_none`, which scans `get_accessor_name()` over
`_meta.get_fields()`) and must fail OPEN with `None` so it never fail-closes a path Django supports.
But "file-local with no second site" is not the right record for it. It is a REJECTED candidate and
owes a contract difference plus a reconsideration trigger (my proposal for the trigger: *if
`classify_path` ever grows an accessor-name fallback or a non-raising mode, the two become one
rule*). **Routing: either a new family `orm-lookup-path-resolution` owned by
`utils/relations.py::classify_path`, or a rejection recorded at
`_prefetch_relation_target_or_none`.**

**C3 — `is_async_queryset_adapter` has no production reader.** Definition here; 11 assertions across
`tests/test_list_field.py` and `tests/optimizer/test_extension.py`; zero package callers. Under
principle 11 this is an indirection whose only job is being checked. Note the counter-argument
before deleting: it is the only spelling of "is this the async-only adapter" that a test can use
WITHOUT importing the private `_AsyncQuerySetRows`, so removing it pushes 11 oracles onto a private
name. Principle 11's own carve-out ("keep a one-caller wrapper only for a concrete responsibility it
carries: a boundary name callers depend on") arguably covers that. Either outcome is defensible; what
is not defensible is leaving it unrecorded. **Routing: family `async-only-queryset-row-adapter`,
which owns `_AsyncQuerySetRows`.**

**C4 — `_safe_class_name` is recorded file-local, but the package has two definitions of it.**
`exceptions.py::_safe_class_name` and `utils/querysets.py::_safe_class_name` are two independently
maintained bodies under one name. The contract difference is recorded at BOTH owners (exceptions'
docstring names the querysets variant as "a stricter local variant whose non-string fallback never
dispatches the name object at all"; the querysets docstring names exceptions' as the shared one),
which is exactly what `DRY.md` "Rejected candidates" asks for as a durable home — so the reasoning
is already right and already written. The index row is what is wrong: `file-local` claims "no second
site", and the row's "files covered" names only `utils/querysets.py`. It should read as a rejection
covering `utils/querysets.py` and `exceptions.py`. Missing from both docstrings: a reconsideration
trigger (proposal: *if `exceptions._safe_class_name` ever stops calling `_safe_arg_repr` on a
non-string name, the two collapse to one*). **Routing: a rejection row, files covered
`utils/querysets.py` + `exceptions.py`.**

C2 and C4 are the same defect of bookkeeping, not of reasoning: "file-local" is defined by `DRY.md`
as "no second site after the matrix", and both rows have one. Neither changes what the cycle should
DO with the rule; both change what a later run reading `## Outcomes` would believe about it.

### Things I checked and found sound

- The item-scoped diff is empty and I verified it myself at the ITEM_BASELINE, not from the
  dispatch's word.
- `_seal_or_defect` really is the single sealing primitive: 1 definition, 5 call sites, no second
  `sql.Query`-rebuilding body anywhere in the package.
- The two round-trip inventory gates (`_PLAIN_CONTAINER_TYPES`, `_INERT_VALUE_TYPES` /
  `_BOUND_VALUE_NORMALIZERS`) are real executable assertions, not docstring claims. Their negative
  control is structural: each asserts SET EQUALITY, so a member added to one inventory and not the
  other fails the assertion in both directions. A one-sided `<=` would have passed a
  prover-accepted / rebuilder-unhandled gap, which is the direction that fails the seal closed with
  no indication the inventories disagree; the test does not have that hole.
- No oracle in `tests/utils/test_querysets.py` was rewritten to read its expectation from the owner
  it checks.
- AGENTS.md prose rules over the (empty) diff: nothing to check in production source. The two
  untracked probe scripts Worker 1 left and the one I added are per-cycle scratch under
  `docs/dry/temp-tests/`, which the standing docs exempt.

### Commands I ran

```shell
uv run --project "$WS" --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --project "$WS" --directory "$WS" python -c "<django.setup(); print settings.DATABASES['default']['NAME']>"
uv run --project "$WS" --directory "$WS" python probe_defect_arms.py
git diff b2ec17eea042873767e2e30ebcdffa9e7e1ecaca -- django_strawberry_framework/
git hash-object django_strawberry_framework/utils/querysets.py
```

No source was mutated anywhere. No permanent test was run in the shared tree (nothing in this file
item needed one; the one claim I wanted execution for is answered by the read-only probe above).
`FAKESHOP_SHARDED=1` and the Postgres cells stay `unverified`.

### Reconciliation against Worker 1's findings (read after the trace above was on disk)

Worker 1's pass is strong and, on most axes, reaches further than mine: it found the inline
disposal copies in `auth/mutations.py` and `routers.py` (F1), the second pre-sliced refusal in
`connection.py::_guard_source_not_pre_sliced` (F4), `write_transaction.py::canonical_pk` as the
rejected second pk basis (F6), the retired `allow_sliced` keyword still live in the glossary and
in `spec-034` (D2), and the `base_queryset` `using`-order clause whose stated reason its own body
does not support (D4) — all of which my trace missed. Where we overlap we agree: F9 is my C3, F11
is my rule 11, F5 is my rule 5, F8/D1 is my rule 8, and the definition counts match on every
family I counted independently (1 for `_seal_or_defect`, 1 for `_dispose_sync_awaitable`, 1 for
`run_in_one_sync_boundary`, 1 for `model_for`, 2 for the related-object re-check, 2 for the
pre-sliced refusal). Owner choices and family granularity: no disagreement.

Three things do not survive the reconciliation.

**R1 — F12 records `_prefetch_relation_target_or_none` as file-local "no second site"; a mechanism
sweep falsifies that.** This is my C2, and reading F12 makes it sharper rather than softer, because
the challenge F12 posits for that row ("a `GenericForeignKey` alias must resolve rather than fail
open") exercises only this function's own fail-open tail — the "one convenient change" DRY.md's
change-challenge section warns against. Posit instead the change that exercises the rule's real
variation axis, *"a `pk` segment must resolve to the model's pk field at every hop"*, and count:

| body | separator | `pk` resolution | failure mode |
|---|---|---|---|
| `utils/relations.py::classify_path` (+ `_resolve_segment_field`) | `LOOKUP_SEP` | yes | raises `PathResolutionError` |
| `utils/relations.py::_lenient_traverses_to_many` | `LOOKUP_SEP` | no | `False` |
| `connection.py` (keyset terminal-column resolver) | literal `"__"` | yes, via `_meta.pk.name` | `None` |
| `optimizer/plans.py` (loaded-column probe) | literal `"__"` | no | `False` |
| `utils/querysets.py::_prefetch_relation_target_or_none` | `LOOKUP_SEP` | no | `None` |

Five independently maintained bodies of "walk a `__`-separated ORM path through
`Model._meta.get_field`, following `related_model` at each hop"; two of them do not even spell the
separator through `LOOKUP_SEP`. DRY.md's family rule is explicit that the sweep is for the rule's
MECHANISM, not the target's neighbours, and that the second definition is routinely in a module no
seed named — `utils/relations.py` is exactly that module here. The contract difference is real
(raise-vs-fail-open, and only the prefetch resolver accepts the `<model>_set` accessor spelling
Django's prefetch traversal reaches), so I expect this to end as a REJECTION rather than a
consolidation. But `DRY.md` gives a rejection a durable home, a contract difference and a
reconsideration trigger; it does not permit recording it as "file-local, no second site", which is
the one label that guarantees no later item looks again. A file item that ticks with this row as
written leaves the rule unhomed, and `utils/relations.py`'s own file item will see only its side
and reach the same local verdict.

**Owed:** either a new family row `orm-lookup-path-resolution`, owner
`utils/relations.py::classify_path`, files covered `utils/relations.py`, `connection.py`,
`optimizer/plans.py`, `utils/querysets.py` — or an F12 row rewritten as a rejection carrying the
contract difference above and a trigger (proposed: *if `classify_path` grows an accessor-name
fallback or a non-raising mode, the two collapse into one rule*).

**R2 — F3 designs a gate on a premise that is already false, and the docstring asserting it is a
D4-class defect nobody recorded.** F3 quotes the rule ("Every message-building site renders only
the subset IT can reach") and concludes `gate-only`: owner single, no gate. It never checks whether
the rule currently HOLDS. It does not, at three sites inside this very file. The probe under
"Candidates I raise" C1 above measures it: `_raw_list_source_message` declares a `combined` arm its
policy cannot produce (`_RAW_LIST_SOURCE_POLICY` leaves `reject_combined` at its `False` default),
and `_prepared_visibility_source` / `_visibility_result_error` each declare `routing` and
`evaluated` arms their call shape cannot produce (neither passes `expected_routing`; no policy
reaching them sets `require_unevaluated`). Both `permissions.py` sites are correct, which is the
positive control that the comparison can tell a right site from a wrong one.

Worse than the dead arms: `_raw_list_source_message`'s docstring states the false half as a fact —
"Only the defects `_RAW_LIST_SOURCE_POLICY` can actually reach have arms: `evaluated`, `sliced` and
`projection` are switched off by that policy, and `routing` / `alias` need an expectation this
surface never states." Its own enumeration omits `combined`, which is also switched off, and the
arm for it sits four lines below. That is precisely the class Worker 1 recorded as D4 for
`base_queryset` ("a wrong stated reason is worse than none, because the next author honors it") and
it belongs under `## Defects` with the same treatment, not only inside a finding that reads as if
the invariant held.

This is not cosmetic for the family item. F3's "justified population for a gate" is "the six
`_defect_message` call sites, and the codes each reachable `_SealPolicy` can actually emit". A gate
built from that population and run against today's tree goes red at three sites on its first run —
so whoever writes it will either discover R2 the hard way, or, the likelier failure, relax the gate
until the current state passes and thereby encode the opposite of the rule. `fail_under = 100`
cannot warn them: every arm is a value in one dict literal, so the dead arms are "covered" by the
statement that builds the mapping.

**Owed:** a `## Defects` row (owner `utils/querysets.py::_raw_list_source_message`, with the two
sibling sites named), and F3 restated so its gate population is described against the tree as it
is, not as the prose claims it is.

**R3 — challenge C3's rule lands in no family row and no file-local row.** Every other challenge in
the `### Challenges` table terminates somewhere: C1/C2 in `queryset-seed-and-model-read`, C4/C16 in
`field-value-coercion`, C5 in F1, C6 in F7, C7 in F11, C8 in F10, C9/C10/C11/C13 in F2, C12 in F3,
C14 in F4, C15 in F5, C17 in F8, C18 in `post-set-apply-result-validation`. C3 — "coerce a
`Manager` to a `QuerySet`", verdict "independent", 1 definition (`_coerced_manager_queryset`) — is
named in no `## Responsibility index` row and in no F12 row. The rule is not a minor one: it is a
visibility-bypass boundary whose own docstring says a degraded `Manager.all()` "must NEVER be
allowed to fall into the plain-iterable (`is_queryset=False`) bypass", it has a second entry point
(`normalize_query_source` for resolver returns, `_normalized_visibility_result` for hook returns),
and its consumers span `list_field.py`, `connection.py` and `optimizer/extension.py`. Under DRY.md
a file item discharges only when every rule is assigned OR recorded file-local; this one is
neither.

**Owed:** an F12 row for the Manager-coercion rule (with the challenge that proved it file-local),
or an index row naming the family that holds it.

Non-blocking, recorded so they are not re-derived:

- `## System trace` states "99 module-level symbols". Measured at the pinned blob: 102 top-level
  functions, 7 classes, 25 module-level constants (134); `funcs + classes` is 109 and
  `dir()` members whose `__module__` is this module is 116. No instrument yields 99. For an
  inventory backstop the inventory count is load-bearing — an undercount is exactly how a rule goes
  unassigned — so the figure should name its instrument or be corrected.
- F12's `_safe_class_name` row is sound on the substance (it names `exceptions.py` and gives the
  contract difference, and both docstrings already carry the separation at their own owners), but
  it carries no reconsideration trigger. DRY.md asks a rejection for one; "file-local" is the label
  that lets it skip the requirement. Proposed trigger: *if `exceptions._safe_class_name` stops
  routing a non-string name through `_safe_arg_repr`, the two collapse into one rule.*

### Verdict

`Status: revision-needed`. The plan item `- [ ] File \`utils/querysets.py\`` is NOT ticked.

The item-scoped diff is empty and correctly so — a file item owes no production edit and I demand
none. Nothing in R1/R2/R3 asks for one. What is owed is the file item's actual deliverable: an
assignment for every rule the file defines or enforces. Three rules are mis-assigned or
unassigned (R1, R3) or assigned on a false premise (R2), and each is the kind that dies unhomed
once the checkbox is ticked, because `DRY.md` reopens a verified item only when a freshness
fingerprint changes and nothing here will change one.

Everything else verified: matrix discharged against the real surface on all six axes with the one
gap-producing axis (6) enumerated member-by-member rather than asserted; definition counts
confirmed independently; site roles correct and no oracle rewritten to read from its owner; the
two round-trip inventory gates are real executable set-equality assertions; both `## Pending
execution` entries carry an exact command and what it discharges; F8's coupling to D1 is marked;
every finding carries blob-id freshness fingerprints and all of them still match the tree (I
re-hashed `utils/querysets.py`, `permissions.py`, `connection.py`, `types/resolvers.py`,
`optimizer/walker.py`, `list_field.py` and `tests/utils/test_querysets.py`). D1's negative control
is genuine: `probe_alias_policy.py` shows the same input ACCEPTED under one policy and REJECTED
under another, so the instrument can distinguish the two and did not merely print a pass.

Scratch left in place for Worker 0 to remove by explicit path after verification:
`docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py`.

### HEAD moved during this verification; no finding went stale

A concurrent session committed `5c62515a test(forms): move the form-mutation verdicts a request
can show to the live tier` between the start and the end of this pass, so HEAD advanced from
`e9e4d45c` (the plan's cycle-entry HEAD) to `5c62515a`. Re-hashed every file any finding
fingerprints, after the move:

```text
django_strawberry_framework/utils/querysets.py    5907a1f72de42c71402886e7480ab559eb06a3af
django_strawberry_framework/permissions.py        9e0236b3bbcfa9320a5d4e18e34b35c27adf233e
django_strawberry_framework/connection.py         93e998f2c7ea1d7f18607a6e37e394466ac75ad4
django_strawberry_framework/types/resolvers.py    fc077f38a1f10db2a447c11b11bea1e82bcbb362
django_strawberry_framework/optimizer/walker.py   054207017c3435ed1f6b7891683fed112c807d11
django_strawberry_framework/list_field.py         f357eded3d96fcffe17e6fd84bceb8cd12af98d5
django_strawberry_framework/auth/mutations.py     dbe64995b87240b87a1d5119f46cc42c7cab646f
django_strawberry_framework/routers.py            a18c5001471d4a937bb81d2ff41a2e442e7d2dad
tests/utils/test_querysets.py                     c9a84d53f3e74e3f5274a6b5096ce1a17ceef292
```

All nine match the values Worker 1 recorded, so every finding is still fresh and the revision
asked for above is the only thing owed. `django_strawberry_framework/` remains clean against the
new HEAD, and `ITEM_BASELINE=b2ec17ee` still produces an empty package diff. The plan's
`## Cycle baseline` dirty list has also drifted further (`AGENTS.md`, `GOAL.md`,
`docs/feedback.md`, `examples/fakeshop/tests/test_export_schema.py`,
`examples/fakeshop/tests/test_inspect_django_type.py` are now dirty; the `tests/forms/*` and
`examples/fakeshop/test_query/*` entries Worker 1 listed have landed in `5c62515a`). None is a
path this item touches; Worker 0 owns the reconciliation.

## Iterations

### Revision pass 1 — Worker 1, after Worker 2's `revision-needed`

Worker 2 raised three blocking candidates (R1, R2, R3) and two non-blocking points. I verified
each against source myself rather than accepting the report: DRY.md makes a round's self-reported
finding a claim to re-derive, and that cuts both ways. **All three blocking candidates are
upheld.** One of them (R3) turned out to be narrower than the real problem, which is recorded as
I-R5. I qualify one detail of Worker 2's instrument (I-R4) and correct one detail of its site
list (I-R2); neither changes its verdict.

Nothing above was rewritten. Two `## Findings` rows and one `## Findings` paragraph are marked
SUPERSEDED in place and replaced here; two figures in `## System trace` were corrected, with the
old figure quoted so the correction is legible. No production edit: a file item owes none, and
Worker 2 explicitly demanded none.

#### I-R1 (upholds R1, part 1) — `_prefetch_relation_target_or_none` is a REJECTION, not a file-local rule

Worker 2 is right and the mistake was mine in a way worth naming: the challenge I posited for that
F12 row — *"a `GenericForeignKey` alias must resolve rather than fail open"* — could only ever
return 1, because it exercises that function's own fail-open tail rather than the rule's shared
mechanism. DRY.md warns about exactly this ("Exercise the rule's variation axes, not one
convenient change"), and I wrote a convenient one.

Mechanism swept package-wide: *split an ORM lookup path and walk each segment through
`Model._meta.get_field`, following the relation at each hop*. Five independently maintained
bodies, each re-read at the current tree:

| body | separator | `pk` segment | failure mode | accessor-name fallback |
|---|---|---|---|---|
| `utils/relations.py::classify_path` (+ `_resolve_segment_field`) | `LOOKUP_SEP` | resolved to `_meta.pk` | raises `PathResolutionError` | no |
| `utils/relations.py::_lenient_traverses_to_many` | `LOOKUP_SEP` | not resolved | `False` | no |
| `connection.py::_resolve_order_path_field` | literal `"__"` | resolved via `current._meta.pk.name` | `None` | no |
| `optimizer/plans.py::_select_path_traversable` | literal `"__"` | not resolved | `False` | no |
| `utils/querysets.py::_prefetch_relation_target_or_none` | `LOOKUP_SEP` | not resolved | `None` | **yes** (`_reverse_relation_by_accessor_or_none`) |

Re-run challenges, on the rule's real variation axes:

- *"a `pk` segment must resolve to the pk field at every hop"* → **3 definitions move** (rows 2, 4,
  5 gain it), and rows 1 and 3 already implement it two different ways (`_meta.pk` vs
  `_meta.pk.name`). Worker 2's count confirmed.
- *"the separator stops being two underscores"* → **2 definitions** break silently (rows 3 and 4
  hardcode `"__"` while `LOOKUP_SEP` exists and is imported four modules over).
- *"a forward `GenericForeignKey` segment must be refused rather than silently traversed"* → **5**,
  because all five currently answer it differently.

**Verdict: REJECTED, not consolidated** — and I expect that to survive a family item. The contract
difference is real and load-bearing in both directions: `classify_path` resolves DECLARED
field-map names and RAISES, because a filter/order path that does not resolve is a schema-author
error the package must name; `_prefetch_relation_target_or_none` must additionally accept the
default `<model>_set` reverse-accessor spelling that Django's own prefetch traversal reaches by
attribute access, and must fail OPEN with `None` so it never fail-closes a prefetch path Django
supports. Merging them would either make the prefetch guard reject legal Django paths or make the
filter/order classifier silently accept unresolvable ones.

**Reconsideration trigger** (adopting Worker 2's, which is the right one): *if
`utils/relations.py::classify_path` grows an accessor-name fallback or a non-raising mode, the
two collapse into one rule.* Second trigger of my own: *if either literal-`"__"` body is ever
changed to import `LOOKUP_SEP`, the separator axis stops distinguishing them and the population
should be re-counted.*

**Durable home for the rejection:** `utils/querysets.py::_prefetch_relation_target_or_none`, one
plain docstring clause naming `classify_path` as the strict sibling and why this one fails open.
Not written by this item — a file item lands no edit; the family item owes it.

#### I-R2 (upholds R1, part 2) — new family, with one correction to Worker 2's site list

I take Worker 2's first routing option rather than its second, because a rejection recorded only
at `utils/querysets.py` still leaves `utils/relations.py`'s own file item free to reach the same
local verdict from its side — which is precisely the failure Worker 2 names.

**Family: `orm-lookup-path-resolution`**, owner `utils/relations.py::classify_path`, files covered
`utils/relations.py`, `connection.py`, `optimizer/plans.py`, `utils/querysets.py`. Status `open`.

Correction to Worker 2's C2, which lists `utils/permissions.py` as a member: it is not one. Its
walk (`utils/permissions.py` #"hops = source_path.split(LOOKUP_SEP)") matches path segments against
DECLARED `RelatedFilter` / `RelatedOrder` attributes and never touches `Model._meta.get_field`, so
it shares the separator but not the mechanism. Worker 2's own R1 table drops it, so the two halves
of its write-up disagree; the R1 table is the accurate one. Recorded so the family item does not
sweep a fifth module in and then have to argue it back out.

Also excluded, with the reason, so it is not re-derived: `filters/base.py`
#"segments = field_name.split(\"__\")" walks the REGISTRY graph
(`DjangoTypeDefinition.related_target_for`), resolving `pk` against `_meta.pk.name` but never
calling `get_field`. Adjacent, not a member. If the family item decides the rule is "resolve a
lookup path" rather than "resolve it through `_meta`", that judgement pulls this site in and the
count rises to 6 — worth stating, because the boundary of the population is the one thing a
rejection of this shape can get wrong.

#### I-R3 (upholds R3) — the Manager-coercion rule now has a record

Worker 2 is right that challenge C3 terminated nowhere. Adding it to the file-local table, with
challenges that exercise the rule's own axes rather than a convenient one:

| Rule | Owner | Challenges posited | Definitions |
|---|---|---|---|
| A `Manager` entering the visibility boundary is coerced to a `QuerySet` exactly once, preserving its explicit routing, and may NEVER fall into the plain-iterable (`is_queryset=False`) bypass | `utils/querysets.py::_coerced_manager_queryset`, with `normalize_query_source` owning the is-it-a-queryset verdict | (a) "a Manager whose `.all()` returns an async iterable must fail closed"; (b) "the coercion must preserve `_hints`, not only `_db`"; (c) "a Manager that self-routes an unrouted `.all()` must fail closed" (already the rule) | **1** for each challenge |

Population evidence: `models.Manager` appears at exactly three lines package-wide, all in this
file (querysets.py:307 the `normalize_query_source` test, :3479 the coercer's signature, :3818 the
hook-result arm). No other module coerces a Manager or decides "this is a plain iterable"; both
collection flavors reach the verdict through `prepared_resolver_source`. Two entry points, one
body — the boundary shape, not a duplication. **File-local.**

Worth flagging for the folder item rather than hiding in a table: this is the rule whose failure
mode is a *visibility bypass* (a degraded `Manager.all()` mistaken for the deliberate
plain-iterable escape skips `get_queryset` entirely). It is file-local today; it is also the rule
in this file with the least margin, so `utils/` integration should confirm no future surface grows
its own Manager test.

#### I-R4 (upholds R2, with one qualification) — F3's gate population, restated against the tree

I re-derived Worker 2's result from source before accepting it, because its probe's reachability
model is **asserted in a hand-written `SITES` table, not measured** — the probe reads the declared
arms from the AST (which is sound) but hardcodes which policies and which `expected_routing` reach
each site. The two facts that table rests on are checkable, and I checked them:

- `expected_routing` is passed at exactly **one** `_seal_or_defect` call site in the package —
  `_validate_post_orderset_result` (querysets.py:2984). The other four calls
  (querysets.py:2537, :3396, :3703, :3820) pass none. So `routing` is unreachable everywhere else.
- The complete set of `policy=` values that can reach `_prepared_visibility_source` /
  `_normalized_visibility_result` is four: `_DEFAULT_SEAL_POLICY` (the default),
  `_CASCADE_SEAL_POLICY` (`permissions.py:623`, `:705`), `_UNRECOMPOSED_CHILD_POLICY`
  (`optimizer/walker.py:458`), `_LIST_ARGUMENT_VISIBILITY_POLICY` (`list_field.py:1080`, `:1133`).
  None sets `require_unevaluated`; the only policy that does, `_ORDERSET_RESULT_POLICY`, reaches
  `_seal_or_defect` solely through `_validate_post_orderset_result`. So `evaluated` is unreachable
  at both sites.

With those two facts verified the `SITES` table is sound, and I re-ran the probe against the
**shared tree** (read-only, no SQL, no mutation — it imports the module and parses two files):

```text
querysets._validate_post_orderset_result: MISMATCH   dead: []                  missing: ['alias']
querysets._raw_list_source_message:       MISMATCH   dead: ['combined']        missing: []
querysets._prepared_visibility_source:    MISMATCH   dead: ['routing','evaluated']
querysets._visibility_result_error:       MISMATCH   dead: ['routing','evaluated']
permissions._root_error_renderer:         OK
permissions._edge_error_renderer:         OK
sites with a mismatch: 4/6
negative control: raw-list policy reaches ['type', 'table', 'untrusted']
```

**Qualification.** The probe reports 4 mismatches, not 3. The fourth
(`_validate_post_orderset_result`, `missing: ['alias']`) is **not** a defect: that site's own
comment argues the omission at length, and correctly — the seal reaches the alias check only after
`routing` admitted `candidate_db == intent.db`, and `_snapshot_routing_intent` pins
`effective_alias` to that same value, so an `alias` defect cannot arrive there. The probe's model
sets `required_alias_possible=True` for that site and therefore disagrees with a documented
subsumption. Worker 2's prose gets this right and its table reports dead arms only, so its
conclusion stands — but the *instrument* has a known false positive, and anyone building the real
gate from it must encode the subsumption or the gate will demand a wrong arm. That is exactly the
"relax the gate until the current state passes" failure Worker 2 warns about, arriving from the
other direction.

**F3's gate population, restated.** Not "the six `_defect_message` call sites and the codes each
reachable `_SealPolicy` can emit" — that population, run today, goes red at four sites, three
legitimately (D5) and one spuriously. The correct population for a family item to gate is:

> for each `_defect_message` call site, the code set reachable at that site, computed from
> (i) the policies that reach it, (ii) whether it passes `expected_routing`, (iii) whether its
> `required_alias` can be non-`None`, **and (iv) the documented subsumptions a site declares** —
> of which exactly one exists today, `routing` subsuming `alias` at
> `_validate_post_orderset_result`. A subsumption must be declared at the site in a form the gate
> reads, not in prose, or it is indistinguishable from a missing arm.

That fourth term is the part F3 did not have, and it is what makes the gate buildable rather than
merely desirable. It also raises the gate's cost estimate: a declared-subsumption mechanism is a
small production change at the sites, so this is no longer a pure `gate-only` finding — it is
gate-plus-declaration. Family `seal-defect-code-wording` inherits that.

The false-invariant docstring is recorded separately as **D5** under `## Defects`.

#### I-R5 (new, found by the re-derivation R3 prompted) — `SyncMisuseError` was also unassigned

Worker 2's R3 found one unassigned rule by walking the challenge table. I did not want to fix one
gap and leave the class of gap intact, so I re-derived the assignment name-by-name over the full
134-name AST enumeration (the same enumeration that corrected the `## System trace` figure). That
found a **second** unassigned rule that neither pass had noticed: `SyncMisuseError` itself —
name 1 of 134, the first symbol in the file.

| Rule | Owner | Challenge posited | Definitions |
|---|---|---|---|
| A sync-boundary misuse raises a marker that multiply-inherits the package base AND the foreign base a consumer's existing `except` already names, so neither catch stops matching | `utils/querysets.py::SyncMisuseError` | "a fourth catch shape must keep matching" → its own bases; "every package error must also match a wire error" → `exceptions.py`'s bases, not this class | **1** |

Sibling declarations of the same PATTERN, swept and excluded with the reason:
`list_field.py::ListArgumentError` and `resource_policy.py::ResourceLimitExceeded` both pair a
package base with `GraphQLError` for the same structural reason. They are three declarations, not
three definitions: a change to the pattern ("every package error must also inherit X") moves the
base classes in `exceptions.py`, and a change to any one marker's identity moves only that marker.
**File-local**, with the population recorded so `exceptions.py`'s file item does not re-derive it.

Every other name of the 134 resolves to an existing finding or family. The two rows I-R3 and I-R5
add are the complete remainder; the re-derivation is what lets me say "complete" rather than
"none that I noticed", which is the difference DRY.md's inventory backstop is actually asking for.

#### I-R6 (upholds the non-blocking point) — `_safe_class_name` is a rejection with a trigger

Worker 2 is right that the substance was sound and the label was not: `file-local` is defined as
"no second site after the matrix", and `exceptions.py::_safe_class_name` is a second site. The
reasoning was already correct and already written at both owners, which is what DRY.md asks a
rejection for; what was missing is the label, the covered-files list, and a trigger.

**REJECTED.** Contract difference: `exceptions.py::_safe_class_name` renders a non-string
`__name__` through `_safe_arg_repr`, which is the right trade for an ordinary configuration
message; `utils/querysets.py::_safe_class_name` degrades to `_safe_type_name` instead, because a
`repr` of the name object would dispatch a hostile dunder on the very object the sealed boundary
is rejecting. Files covered: `utils/querysets.py`, `exceptions.py`. **Trigger** (adopting Worker
2's): *if `exceptions._safe_class_name` stops routing a non-string name through `_safe_arg_repr`,
the two collapse into one rule.*

#### Where I disagree with Worker 2

Only on two details, neither affecting its verdict, both recorded above: `utils/permissions.py` is
not a member of the lookup-path family (I-R2), and its defect-arm probe carries a known false
positive at `_validate_post_orderset_result` (I-R4). I also think R3 was under-scoped — the gap it
found was a symptom of an enumeration I never did, not of one challenge losing its footing — which
is why I-R5 exists.

On everything else its reading is correct, and on two points it is sharper than mine: F12's
`GenericForeignKey` challenge really was the "one convenient change" DRY.md warns about, and F3
really did design a gate without checking whether the invariant it gates currently holds. Both are
the same mistake in different clothes — asserting a property of the tree from prose at the owner
instead of measuring it — which is the failure mode this whole method exists to catch, so it is
fitting that it took a second reader.

#### Freshness, re-recorded at the current tree

HEAD moved `e9e4d45c` → `5c62515a` during Worker 2's pass. Re-hashed at the start of this
revision; every file any finding fingerprints is unchanged, so no finding went stale and none is
reopened on freshness grounds:

```text
django_strawberry_framework/utils/querysets.py    5907a1f72de42c71402886e7480ab559eb06a3af
django_strawberry_framework/permissions.py        9e0236b3bbcfa9320a5d4e18e34b35c27adf233e
django_strawberry_framework/connection.py         93e998f2c7ea1d7f18607a6e37e394466ac75ad4
django_strawberry_framework/optimizer/walker.py   054207017c3435ed1f6b7891683fed112c807d11
django_strawberry_framework/list_field.py         f357eded3d96fcffe17e6fd84bceb8cd12af98d5
django_strawberry_framework/types/resolvers.py    fc077f38a1f10db2a447c11b11bea1e82bcbb362
django_strawberry_framework/auth/mutations.py     dbe64995b87240b87a1d5119f46cc42c7cab646f
django_strawberry_framework/routers.py            a18c5001471d4a937bb81d2ff41a2e442e7d2dad
tests/utils/test_querysets.py                     c9a84d53f3e74e3f5274a6b5096ce1a17ceef292
```

Newly fingerprinted by this revision (I-R1, I-R2, I-R5), recorded against the current tree:

```text
django_strawberry_framework/utils/relations.py    7662b0bb669c4dfba4a437f3b8f309357f718dca
django_strawberry_framework/optimizer/plans.py    cce985319c8833f3660653327d3003f1f03655a5
django_strawberry_framework/utils/permissions.py  9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec
django_strawberry_framework/exceptions.py         e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b
django_strawberry_framework/filters/base.py       ba52351c284425336262ae6c2b82b262f6586fc0
django_strawberry_framework/resource_policy.py    9205124f41814dbda5a7df0a4882e10b5f951b2f
```

All six are clean at the current HEAD (`git status --short django_strawberry_framework/` prints
nothing). `utils/permissions.py` and `filters/base.py` are fingerprinted because I-R2 EXCLUDES
them from the lookup-path family on the strength of their current bodies; an exclusion needs a
fingerprint as much as an inclusion does, or a later edit silently changes the population without
reopening anything.

#### Revision 1 — item state

No production edit. Item-scoped diff against `ITEM_BASELINE=b2ec17eea042873767e2e30ebcdffa9e7e1ecaca`
still empty; `django_strawberry_framework/utils/querysets.py` still blob
`5907a1f72de42c71402886e7480ab559eb06a3af`. `uv run ruff format .` / `ruff check --fix .` not run,
because no tracked file was edited. No workspace was built this pass (nothing mutates source), so
the `--project`/`--directory` hazard the dispatch flagged did not arise; the one command I ran
against the shared tree is read-only and its package root is printed in its own output
(`~/projects/django-strawberry-framework/django_strawberry_framework`).

Concurrent dirt has grown again and is entirely another session's: `AGENTS.md`, `GOAL.md`,
`docs/TREE.md`, `docs/feedback.md`, `docs/spec-050-list_field_arguments-0_0_15.md` and its
`-rationale.md`, `examples/fakeshop/tests/test_export_schema.py`,
`examples/fakeshop/tests/test_inspect_django_type.py`, `tests/management/test_export_schema.py`,
`tests/management/test_imports.py`, `tests/management/test_inspect_django_type.py`, plus three
untracked repo-root files whose names are literal whitespace. None is a path this item touches;
untouched, and Worker 0 owns the `## Cycle baseline` reconciliation.

## Independent verification (Worker 2) — re-pass after revision 1

Re-verifying revision 1. My pass-1 section above is intact and nothing in it was erased; the two
SUPERSEDED markers are additive and point forward to `## Iterations`, which is the correct shape.

### Mechanical state, re-checked rather than taken from the dispatch

```text
HEAD                                              5c62515a  (unchanged since my pass-1 note)
git diff b2ec17ee -- django_strawberry_framework/ empty
git status --short django_strawberry_framework/   empty
git ls-files --others --exclude-standard <pkg>    empty
utils/querysets.py                                5907a1f72de42c71402886e7480ab559eb06a3af
$WS/.../utils/querysets.py                        5907a1f72de42c71402886e7480ab559eb06a3af
```

The workspace predates the revision but the revision landed zero source edits, so the copy is
still faithful — confirmed by the blob above rather than assumed, and I re-ran the probe inside it
rather than only in the shared tree. All nine pass-1 fingerprints and all six newly recorded ones
(`utils/relations.py` `7662b0bb…`, `optimizer/plans.py` `cce98531…`, `utils/permissions.py`
`9889d6fe…`, `exceptions.py` `e06b0b7f…`, `filters/base.py` `ba52351c…`, `resource_policy.py`
`9205124f…`) re-hash to exactly the values recorded. Fingerprinting the two EXCLUDED modules is
the right call and I would not have thought to ask for it: an exclusion rests on a body just as an
inclusion does.

### R1 — discharged

I re-derived the population with an instrument instead of re-reading the same five bodies: an AST
sweep over every function in the package, flagging bodies that split on `"__"`/`LOOKUP_SEP` and
bodies that call `_meta.get_field`. Result — 21 functions touch one of the two, and exactly **4**
do both in one body: `connection.py::_resolve_order_path_field`,
`optimizer/plans.py::_select_path_traversable`, `utils/querysets.py::_prefetch_relation_target_or_none`,
`utils/relations.py::_lenient_traverses_to_many`. `classify_path` splits and delegates the
`get_field` half to `_resolve_segment_field`, which is why it is one body with its helper and the
fifth member. That is I-R1's table, reproduced by a different method. Every symbol name I-R1 and
I-R2 cite resolves (`_resolve_order_path_field` connection.py:780,
`_select_path_traversable` plans.py:653, `classify_path` relations.py:323,
`_resolve_segment_field` :287, `_lenient_traverses_to_many` :487).

**Both corrections to my write-up are accepted, and the first one is a straight error of mine.**
`utils/permissions.py` contains **zero** occurrences of `_meta.` anywhere in the file, so
`_fire_flat_relation_path_gates` cannot be a member of a family defined by the `_meta` walk — it
matches segments against declared `RelatedFilter` / `RelatedOrder` attributes. My C2 prose listed
it and my R1 table did not; Worker 1 is right that the two halves disagreed and right about which
half was accurate. The `filters/base.py` exclusion is equally correct
(`resolve_globalid_target_definition` splits but resolves through
`DjangoTypeDefinition.related_target_for`, never `get_field`), and flagging that a "resolve a
lookup path" framing would pull it in and make the count 6 is exactly the boundary statement a
rejection of this shape needs.

One addition, non-blocking: my sweep finds a second split-only site in the same class,
`list_field.py::_is_deterministic_order_name`. It is excluded for the same reason as
`filters/base.py` and belongs in the same sentence, so the "count rises to 6" caveat is really
"rises to 7". Worth one clause when the family item opens; it changes nothing now.

Verdict REJECTED-not-consolidated is the right outcome and it is now recorded as a rejection with
a contract difference and two triggers, with a durable home named. That is what R1 asked for.

### R2 — discharged, and the qualification is correct

I verified I-R4's two load-bearing facts myself, mechanically, because they are what makes my own
probe's hand-written `SITES` table sound and Worker 1 is right to have challenged it:

- AST over every `_seal_or_defect` call: **5 sites, exactly 1 passes `expected_routing`**
  (querysets.py:2979, `_validate_post_orderset_result`); the other four (`:2537`, `:3396`,
  `:3703`, `:3820`) pass none.
- `require_unevaluated` read off the live policy objects: **`_ORDERSET_RESULT_POLICY` alone is
  `True`**, and the complete set of `policy=` arguments reaching the two runners package-wide is
  `_LIST_ARGUMENT_VISIBILITY_POLICY` (list_field.py:1080, :1133), `_CASCADE_SEAL_POLICY`
  (permissions.py:623, :705), `_UNRECOMPOSED_CHILD_POLICY` (optimizer/walker.py:458), plus the
  `_DEFAULT_SEAL_POLICY` default — four, none of them `require_unevaluated`.

So `routing` and `evaluated` are unreachable at both sites, and D5's table is right for reasons
now measured at both ends rather than asserted at one.

**The false-positive qualification is correct and I should have caught it myself.** My prose says
`_validate_post_orderset_result`'s absent `alias` arm "is the opposite case and is argued
correctly in its own comment", and my table reports dead arms only — but the probe I shipped
prints `MISMATCH … missing: ['alias']` for that site and a bare `4/6` summary line. Anyone reading
the instrument's output instead of my prose concludes four defects. That is a self-falsifying
instrument in the small: the probe measures declared-vs-reachable honestly and then reports a
documented subsumption in the same vocabulary as a real omission. I-R4's fourth population term —
*a declared subsumption must be machine-readable at the site or it is indistinguishable from a
missing arm* — is the right repair and is the part F3 did not have. Reclassifying the finding as
gate-plus-declaration follows from it, and the honesty about the added cost (a small production
change at the sites, inherited by the family item) is the correct way to record it rather than
quietly leaving it inside a "gate-only" label.

D5 is a proper defect record: rule quoted at its owner, the three sites tabulated with the reason
each code cannot arrive, the `permissions.py` pair named as the control that shows the comparison
discriminates, the D4-class docstring quoted verbatim, the coverage blind spot stated, an owner
and a family named, and the file-item boundary respected. Re-ran the probe in `$WS` at the current
tree: `4/6`, same rows, negative control intact, **exit status 0** — so it cannot fail a gate; its
only hazard is being misread, which entry 3 of `## Pending execution` now warns about explicitly.

### R3 — discharged, and I-R5 is a real find that my method would not have reached

I-R3 gives the Manager-coercion rule a row with three challenges on its own axes and population
evidence (`models.Manager` at exactly three lines, all in this file — I re-checked). Flagging it
to the folder item as the file-local rule with the least margin is a judgement I agree with: its
failure mode is a visibility bypass, not a drift.

Worker 1 is right that R3 was under-scoped. I found C3 by walking the `### Challenges` table for a
row that terminated nowhere — an instrument that can only find gaps in rules someone already
posed a challenge for. `SyncMisuseError` had no challenge row, so my method was blind to it by
construction. Re-deriving name-by-name over the full enumeration is the instrument that sees the
class of gap rather than one instance, and it is what an inventory backstop is actually for.

**I tested the completeness claim rather than accepting it**, with two instruments:

1. *Name-mention sweep.* For each of the 134 module-level names, count word-boundary occurrences
   in Worker 1's sections excluding `## System trace` (descriptive, not an assignment). 54 names
   are never mentioned. That number over-reports by design and I say so: F2 assigns the seal by
   composition — "`_seal_or_defect` and the ~60 helpers it composes" — so a helper is assigned
   without being named, and DRY.md's unit is the RULE, not the symbol.
2. *Call-graph closure.* Starting from the 38 owners Worker 1 names across the families, F-rows,
   F12 rows, I-R3 and I-R5, take the transitive closure over intra-module references. **113 of 134
   names are reachable; 21 are not.** Judging those 21 one at a time: the three exported
   `_SealPolicy` instances and the twelve `_normalized_*` primitives are reached only through
   module-level constants (`_BOUND_VALUE_NORMALIZERS`), which my closure does not traverse — an
   instrument blind spot, not a gap, and F2/F4 name "the seven policy constants" explicitly;
   `pks_all_present` is named in F6's text; `reject_awaitable_sync_source` /
   `reject_residual_async_source` are named in F1's consumer list;
   `post_process_queryset_result_sync` / `_async` are named in matrix axis 2 under the `_*` glob my
   regex could not match.

That leaves **one** marginal name, and it is not a blocker: `materialized_rows`, with its helpers
`_readable_queryset_state` and `_row_source_model`, is named only in `## System trace` cluster 5.
It is not an unassigned RULE — it shares `normalized_row_source`'s premise exactly (an exact
`models.QuerySet`'s slots are Django's; a subclass's are consumer code), the two shipped in one
commit and are called on adjacent lines at `types/resolvers.py:576-577`, and F2's "Distinct
behavior" paragraph assigns that rule. But `materialized_rows` is the one symbol in the cluster
with a package-external consumer AND its own oracle (`tests/test_resource_policy.py:2160`, `:2174`),
so naming it in F2's row would save the `utils/` folder item a re-derivation. **Recorded as a
precision note, not a revision condition.**

So: yes, `SyncMisuseError` plus Manager coercion closes the enumeration. I-R5's sibling sweep is
also sound — `list_field.py::ListArgumentError` and `resource_policy.py::ResourceLimitExceeded` are
both `(GraphQLError, DjangoStrawberryFrameworkError)` against this one's
`(ConfigurationError, RuntimeError)`, and the declarations-not-definitions reasoning holds: the
pattern's change moves `exceptions.py`'s bases, a marker's identity change moves only that marker.

### The `## System trace` figure

Corrected in place to 102 functions / 7 classes / 25 constants (134 names; 109 excluding
constants) plus 6 nested methods, instrument named (`ast.Module.body`), old figure quoted so the
correction is legible rather than silent. Every number matches my own measurement, including the 6
nested methods (`_AsyncQuerySetRows.__init__` / `.__aiter__`, `_GraphWalk.__init__` / `.enter` /
`.begin` / `.leave`). Discharged.

### Where I do not fully agree: `## Pending execution` entry 3

DRY.md defines that section narrowly — *"Each `execution-deferred` proof: exact command, what it
discharges. Absent when none."* Entry 3 is not a deferred proof; it already ran, twice, and
Worker 1 labels it honestly as a regression witness. Strictly it does not belong under that
heading. Two things stop me making it a revision condition:

- Entry 2 has the same character (a request that the gate confirm three suites are green) and I
  accepted it in pass 1. Rejecting entry 3 now would be inconsistent with my own prior verdict.
- The consequence of leaving it is bounded and Worker 1 already bounded it: the probe exits 0, so
  it cannot fail the gate, and the entry states the expected `4/6` and points at I-R4 before the
  number is read as pass or fail.

Accepted as written, with the taxonomy point recorded for Worker 0 and the gate: **entries 2 and 3
are gate requests, not `execution-deferred` proofs; only entry 1 is.** A gate worker should run all
three and treat only entry 1 as discharging a proof. The section being non-empty is what decides
the plan marking below, so the distinction costs nothing here — but DRY.md's `## Pending execution`
contract has no home for a regression witness, and that is a gap in the method, not in this
artifact.

### Verdict

`Status: verified`. `## Pending execution` is non-empty (three entries, one of them a genuine
`execution-deferred` proof gated on the maintainer's `FAKESHOP_SHARDED=1` authorization), so the plan item is
ticked as **`verified, pending execution`**.

R1, R2 and R3 are all discharged, each in a stronger form than I asked for: R1 as a rejection with
contract difference, two triggers and a named durable home plus a new family; R2 with the gate
population repaired by a term I had not identified and the defect split out as D5; R3 with the
gap's whole class closed by an enumeration rather than its one instance. Two corrections to my own
write-up are accepted — `utils/permissions.py` is not a family member, and my probe carries a
known false positive at `_validate_post_orderset_result`. The item-scoped diff is still empty,
which is correct: a file item owes no production edit, none was made, and nothing in this
verification asks for one.

Plan rows Worker 0 should now write, all of which I endorse as stated:

- New family `orm-lookup-path-resolution`, owner
  `django_strawberry_framework/utils/relations.py::classify_path`, files covered
  `utils/relations.py`, `connection.py`, `optimizer/plans.py`, `utils/querysets.py`, holding item
  `dry-rule-orm-lookup-path-resolution.md`, status `open`.
- Index row for `utils/querysets.py::_prefetch_relation_target_or_none` changed from `file-local`
  to `rejected` (currently plan line 310 still reads `file-local`), files covered
  `utils/querysets.py` + `utils/relations.py`.
- Index row for `utils/querysets.py::_safe_class_name` changed from `file-local` to `rejected`,
  files covered `utils/querysets.py` + `exceptions.py` (currently plan line 304).
- Two new `file-local` index rows: Manager coercion (owner
  `utils/querysets.py::_coerced_manager_queryset`) and the sync-misuse marker's catch-shape
  contract (owner `utils/querysets.py::SyncMisuseError`).
- `seal-defect-code-wording` now carries D5 as well as F3, and F3 is gate-plus-declaration rather
  than gate-only.
- The twelve pass-1 families otherwise unchanged.

Scratch for Worker 0 to remove by explicit path after this verification:
`docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py` and the two
`docs/dry/temp-tests/dry-file-utils__querysets/` probes.

Concurrent dirt grew again during this pass and none of it is this item's; left alone, Worker 0
owns the `## Cycle baseline` reconciliation.

## D1 fix (Worker 1)

Root-cause correction of `## Defects` D1 — the optimizer walker's prefetch child accepting its own
`.using(...)`. Scope: the walker's seal call only. `django_strawberry_framework/utils/querysets.py`
and `tests/utils/test_querysets.py` were dirty with another session's `carry_result_cache` work at
dispatch time and were NOT touched; the residue that leaves is listed under "Residue" below.

### Files changed

| Path | Symbol | Change |
|---|---|---|
| `django_strawberry_framework/optimizer/walker.py` | module imports | `_UNRECOMPOSED_CHILD_POLICY` → `_PREFETCH_CHILD_POLICY` (the module already imported the private policy constant from `utils/querysets.py`, so no new layering) |
| `django_strawberry_framework/optimizer/walker.py` | `_build_child_queryset` | seals the child under `_PREFETCH_CHILD_POLICY` (`reject_sliced=False, require_shared_alias=True`); docstring + comment state why the seed stays unrouted and what each policy field buys |
| `examples/fakeshop/test_query/test_products_visibility_api.py` | module docstring, `_child_routing_schema`, `_CHILD_ROUTING_QUERY`, 2 tests | non-sharded live rows |
| `examples/fakeshop/test_query/test_multi_db.py` | module docstring, `_prefetch_alias_schema`, `_PREFETCH_ALIAS_QUERY`, `_post_prefetch_alias_query`, 3 tests | sharded live rows |

No new files. Item-scoped diff = `git diff -- django_strawberry_framework/optimizer/walker.py
examples/fakeshop/test_query/test_products_visibility_api.py
examples/fakeshop/test_query/test_multi_db.py` → `3 files changed, 264 insertions(+), 5
deletions(-)`; no `git diff --no-index /dev/null <new>` row is owed. All three paths were CLEAN at
`git status --short` when the item opened and carry nothing but this item's hunks now.

### Why the alias threaded is `None`

D1's prescription was "thread the parent's effective alias". The walker never holds the parent
queryset: `_build_child_queryset` runs inside `_walk_selections`, and the plan it contributes to is
inserted into `DjangoOptimizerExtension._plan_cache` and REUSED across requests
(`optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`). A per-request alias baked
into a cached child queryset would be served to the next request on another connection, so the
child must be alias-agnostic — which is exactly what `require_shared_alias` against an unresolved
outer alias enforces. `_prepared_visibility_source` already derives `required_alias` from the seed
(`base_queryset(field.related_model)`, `_db is None`), so the one missing fact was the policy. This
matches the rule `utils/querysets.py::_sealed_prefetch_related_lookups` applies to a
consumer-supplied `Prefetch` child under an unrouted parent: an explicitly routed child fails
closed, an unrouted child inherits the parent's connection at fetch time.

### Tests added

Live tier (`examples/fakeshop/test_query/`), which AGENTS.md mandates for any line reachable from a
real query. Both modules already existed, so the live-tier README suite map needs no new row; each
module's docstring gained the new verdict. No new fakeshop model or relation shape was needed, so
DRY.md "Tests" fixture-gap clause does not fire.

| Node id | Tier | Gate |
|---|---|---|
| `examples/fakeshop/test_query/test_products_visibility_api.py::test_planned_prefetch_child_may_not_pin_its_own_connection` | live, single DB | child hook returns `qs.using("default")` → `data: null`, one error naming `RoutingItemType.get_queryset` and `routed to alias 'default'` |
| `examples/fakeshop/test_query/test_products_visibility_api.py::test_planned_prefetch_child_still_serves_rows_when_the_hook_only_narrows` | live, single DB | control: a hook that only narrows still scopes the planned child and serves its page |
| `examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_cannot_route_itself_to_the_other_shard` | live, `FAKESHOP_SHARDED=1` | child hook returns `qs.using("shard_b")` under a `default` parent → refused, and `library_book` SQL count is 0 on BOTH aliases |
| `examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_inherits_an_unrouted_parents_connection` | live, `FAKESHOP_SHARDED=1` | control: unrouted child under unrouted parent → `on-default` only, 1 `library_book` read on `default`, 0 on `shard_b` |
| `examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_follows_a_routed_parent_onto_its_shard` | live, `FAKESHOP_SHARDED=1` | control: same unrouted child under a `.using("shard_b")` parent → `on-shard-b` only, 1 `library_book` read on `shard_b`, 0 on `default` |

The sharded three sit under `test_multi_db.py`'s module-level
`pytest.skip(..., allow_module_level=True)` env gate, so they skip under the default `uv run
pytest` exactly like every other row in that module.

### Fail-without-fix proof

Workspace copy only (`$WS = <scratch>/dry-ws/d1-fix`, package `__file__` printed from inside it
before every verdict:
`.../scratchpad/dry-ws/d1-fix/django_strawberry_framework/__init__.py`). The production hunk was
reverted IN THE WORKSPACE (`policy=_PREFETCH_CHILD_POLICY` → `policy=_UNRECOMPOSED_CHILD_POLICY`
plus the import), never in the shared tree; the file was restored from a pre-revert copy afterwards
and `cmp` against the shared tree reported byte identity.

Reverted, single DB:

```
>       assert payload["data"] is None
E       AssertionError: assert {'categories': [{'name': 'address', 'items': [{'name': 'address_fcd07f08'}]}, ...]} is None
FAILED .../test_products_visibility_api.py::test_planned_prefetch_child_may_not_pin_its_own_connection
1 failed, 1 passed, 12 deselected
```

Reverted, `FAKESHOP_SHARDED=1` — the failure message IS the leak:

```
>       assert payload["data"] is None
E       AssertionError: assert {'shelves': [{'code': 'S-default-on-default', 'books': [{'title': 'on-shard-b'}]}]} is None
FAILED .../test_multi_db.py::test_planned_prefetch_child_cannot_route_itself_to_the_other_shard
1 failed, 2 passed, 15 deselected
```

A shelf read from `default` served a book row that exists only on `shard_b`. Each control passed
under the revert, which is what makes the two failures attributable to the seal policy and not to
the fixtures.

Restored, in the workspace:

```
examples/fakeshop/test_query/test_multi_db.py ...            [100%]
3 passed, 15 deselected in 5.99s          (FAKESHOP_SHARDED=1)

examples/fakeshop/test_query/test_products_visibility_api.py [100%]
14 passed in 8.44s
```

### Commands

Workspace (`uv run --directory "$WS"` throughout):

- `pytest tests/optimizer examples/fakeshop/test_query/test_products_visibility_api.py
  examples/fakeshop/test_query/test_optimizer_auto_api.py --no-cov -q` → `869 passed, 2 skipped`.
- `pytest --no-cov -q` → `8311 passed, 41 skipped`, plus 3 failures + 1 collection error that are
  artifacts of the workspace recipe's `--exclude docs/ --exclude .git`
  (`tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file`,
  `::test_the_git_oracle_enumerates_this_module`,
  `tests/test_pg_explain_artifact_footer.py::test_checked_in_artifact_passes_link_block_validation`,
  `tests/test_export_dry_review.py` import error). They reproduce on a pristine copy of the same
  recipe and touch nothing this item changed.
- `FAKESHOP_SHARDED=1 pytest --no-cov -q` → `8333 passed, 38 skipped` with the same four recipe
  artifacts.
- `python scripts/check_citations.py --check` → `OK: 1104 citations resolve`.

Shared tree (the authorized focused run, plus the AGENTS.md post-edit formatters):

- `uv run pytest examples/fakeshop/test_query/test_products_visibility_api.py -k prefetch_child
  --no-cov -n0 -q` → `2 passed, 12 deselected`.
- `uv run ruff format .` / `uv run ruff check --fix .` / `uv run python
  scripts/check_trailing_commas.py <the three edited .py files>` — run scoped to the edited paths
  so the repo-wide auto-fix default never rewrote another session's files.

### Residue (owner reads a path this item was not allowed to edit)

Both sit in `django_strawberry_framework/utils/querysets.py`, dirty with another session's work:

1. `_UNRECOMPOSED_CHILD_POLICY` now has NO production caller — the walker was its only one. Its
   remaining reader is `tests/utils/test_querysets.py` (also dirty). Either the constant is deleted
   and that assertion re-pointed at `_PREFETCH_CHILD_POLICY`, or it stays as a named alias with a
   reason; leaving it as-is publishes a policy nothing applies.
2. Two docstrings still name it as the walker's policy:
   `utils/querysets.py::apply_type_visibility_sync` (the `policy` paragraph) and
   `utils/querysets.py::apply_type_visibility_async` (its sibling paragraph).
   Neither is a `path::Symbol` citation, so no gate catches the drift.

Two more, outside this item's scope:

3. `docs/GLOSSARY.md` *Prefetch alias threading* describes the child seal; the walker-built child
   now meets the same rule as the consumer-supplied one. Glossary bodies are rendered from the
   fakeshop `glossary` app DB, so the repair is a `GlossaryTerm` edit plus a re-render — the same
   mechanism D2 already needs.
4. `examples/fakeshop/test_query/README.md`'s suite-map rows for `test_products_visibility_api.py`
   and `test_multi_db.py` do not mention the connection verdict. The README was dirty at dispatch
   and was left alone; the authoritative module docstrings were updated instead.

### Behavior change

Not behavior-preserving, as D1 stated. A consumer whose target type's `get_queryset` calls
`.using(...)` and whose relation the optimizer plans now gets a `ConfigurationError` naming the
alias, where before it silently got a prefetch on that connection. The recourse the existing error
text already gives ("Remove the `.using(...)` call") is the correct one: pinning the PARENT moves
the whole resolution, and the child follows.

## D1 independent verification (Worker 2)

Status: `revision-needed` — one AGENTS.md layout violation in the item's own diff. The substance
(fix, owner, proof, tests) is otherwise verified; the re-pass is a formatter run.

### Expectation, recorded before reading `## D1 fix (Worker 1)`

Read first: `utils/querysets.py::_SealPolicy` (`require_shared_alias` bullet),
`utils/querysets.py::base_queryset` (`using` paragraph),
`utils/querysets.py::_sealed_prefetch_related_lookups`,
`utils/querysets.py::_prepared_visibility_source` (required-alias priority: write-pipeline pin >
sealed source's `_db` > `None`), `utils/querysets.py::_seal_or_defect` #"policy.require_shared_alias",
`docs/GLOSSARY.md` *Prefetch alias threading*, then the production hunk of
`git diff -- django_strawberry_framework/optimizer/walker.py`.

`optimizer/walker.py::_build_child_queryset` seeds with `base_queryset(field.related_model)` and
passes no `using=`, so the source's `_db` is `None` and the resolved `required_alias` is `None`.
Under `require_shared_alias` the seal's rule is `db is not None and db != required_alias`:

| case | expected |
|---|---|
| routed child, unrouted parent | REFUSED — `("alias", <alias>)` → `ConfigurationError`; this is the fix |
| unrouted child, unrouted parent | ACCEPTED, stays unrouted (`using = None`) |
| unrouted child, ROUTED parent | ACCEPTED — the parent's alias never enters this call; the child leaves unrouted and Django resolves it against the parent rows' connection at fetch |
| child hook that only narrows | ACCEPTED unchanged; the filter survives onto the sealed rebuild |

Corollaries I expected and then tested: the `reject_sliced=False` licence survives; a routed child
under a parent routed to the SAME alias is ALSO refused, because the walker cannot know the
parent's alias at plan-build time; and the new docstring's unconditional claim "never pinned to a
database alias, so the child's effective alias entering the hook is `None`" is in tension with
`_prepared_visibility_source`'s priority-1 write-pipeline pin.

Reconciliation with `## D1 fix (Worker 1)`: all four rows agree, and W1's "Why the alias threaded
is `None`" gives the same reason I derived (the plan is cached and reused across requests, so a
baked-in alias would be served to the next request on another connection). Two differences.
(a) W1 records no case for a routed child under a parent routed to the SAME alias; that case is
refused, and probe E below is what shows the refusal is required rather than over-strict.
(b) the write-pipeline wrinkle is unaddressed; it is not reachable here (the optimizer plan is a
read path) so it is a docstring-precision note, not a defect.

### Workspace provenance

```
WS=<scratch>/dry-ws/d1-verify   (fresh rsync taken after Worker 1's edits)
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
-> <WS>/django_strawberry_framework/__init__.py
settings.DATABASES["default"]["NAME"] -> <WS>/examples/fakeshop/db.sqlite3
```

`md5` of `django_strawberry_framework/optimizer/walker.py` equal in `$WS` and the shared tree at
copy time. Every command below ran via `uv run --directory "$WS"`; nothing ran in the shared tree.

### Checks

**1. New tests, both modes, and the fail-without-fix control.**

| command (in `$WS`) | result |
|---|---|
| `pytest examples/fakeshop/test_query/test_products_visibility_api.py --no-cov -q -n0` | `14 passed` |
| `FAKESHOP_SHARDED=1 pytest examples/fakeshop/test_query/test_multi_db.py --no-cov -q -n0` | `18 passed` |
| `FAKESHOP_SHARDED=1 pytest examples/fakeshop/test_query/test_products_visibility_api.py --no-cov -q -n0` | `14 passed` |

Reverted in the workspace only
(`git show HEAD:django_strawberry_framework/optimizer/walker.py > $WS/.../walker.py`):

- `test_planned_prefetch_child_may_not_pin_its_own_connection` → `1 failed, 1 passed`, the failure
  being `assert {'categories': [...]} is None`; its control passed.
- `FAKESHOP_SHARDED=1 ... -k prefetch_child` → `1 failed, 2 passed`; the failure is the leak itself,
  `{'shelves': [{'code': 'S-default-on-default', 'books': [{'title': 'on-shard-b'}]}]}` — a shelf
  read on `default` serving a book row that exists only on `shard_b`. Both controls passed reverted,
  so the two failures are attributable to the policy and not to the fixtures.

Restored afterwards; `cmp` against the shared tree reports byte identity.

**2. Attacks.** Scratch module `$WS/examples/fakeshop/test_query/test_w2_d1_attack.py`, live
`/graphql/` HTTP, `library_book` SQL counted per alias.

| probe | shape | result |
|---|---|---|
| A | parent `.using("shard_b")` + child hook `.using("shard_b")` (SAME alias) | REFUSED, 0 reads on both aliases |
| B | child hook returns `Book.objects.db_manager("shard_b").all()` | REFUSED, 0 reads on both aliases |
| B2 | child hook returns a fresh UNROUTED `Book.objects.all()` | ACCEPTED, 1 read on `default`, `on-default` only |
| C | sliced child (`q.order_by("pk")[:1]`) on a plain list relation | raw Django `TypeError` "Cannot filter a query once a slice has been taken." — IDENTICAL at HEAD; see `## Defects` |
| C2 | sliced AND routed child | REFUSED on the alias, 0 reads — the slice licence opens no bypass |
| D | `branches { shelves { books } }`, routed grandchild hook | REFUSED, names `AliasBookType.get_queryset`, 0 reads |
| D2 | same query, routed MIDDLE hook | REFUSED, names `AliasShelfType.get_queryset`, 0 reads |
| D3 | control: no routing anywhere, parent `.using("shard_b")` | ACCEPTED two levels down, 1 read on `shard_b`, 0 on `default` |
| E | ONE schema object, two requests, parent unrouted then `.using("shard_b")` | req 1 → `on-default`, 1 read on `default`; req 2 → `on-shard-b`, 1 read on `shard_b` |

A is the case W1 did not record, and E is its justification: the SAME cached plan serves a
`default` parent and a `shard_b` parent in consecutive requests, so a child that carried any
explicit alias would be wrong for one of them. Refusing the same-alias pin is correct, not
over-strict. The error text carries the recourse ("Remove the `.using(...)` call"), though its
"pinned to alias None" wording reads oddly for this surface.

**3. Owner and the `utils/querysets.py` question.** Confirmed at the owner. `git show
HEAD:django_strawberry_framework/utils/querysets.py` already defines
`_PREFETCH_CHILD_POLICY = _SealPolicy(reject_sliced=False, require_shared_alias=True)` and
`_seal_or_defect` already implements the axis; the only production fact missing was which policy
the walker passes. The concurrent dirt in that file touches `_RAW_LIST_SOURCE_POLICY` alone
(`git diff -- django_strawberry_framework/utils/querysets.py | grep POLICY`), so the no-edit claim
is independent of the concurrent work.

Residue judgment: `_UNRECOMPOSED_CHILD_POLICY` now has no production caller
(`grep -rn "_UNRECOMPOSED_CHILD_POLICY"` → `utils/querysets.py` definition + two docstrings,
`tests/utils/test_querysets.py:4956`, nothing else), and the `apply_type_visibility_sync` /
`apply_type_visibility_async` `policy` paragraphs still name it as the walker's policy, which is
now false. ACCEPTABLE TO LEAVE for the maintainer; it does NOT block acceptance. It changes no
behavior, the only reader left is a test that still passes, and both sites sit in a file this item
was correctly forbidden to edit. It must be homed on a named card, not dropped — recorded under
`## Defects` below.

**4. AGENTS.md prose rules.** No process provenance in any added line (no spec-cycle, worker, pass
or review vocabulary; the one `spec-045-visibility_boundary-0_0_14` anchor is a pre-existing
context line). No `path:NN` refs; citations are `path::Symbol`
(`optimizer/walker.py::_build_child_queryset`, `nested_fetch.py::unwindowable_child_queryset_reason`,
`utils/querysets.py::_sealed_prefetch_related_lookups`) and
`python scripts/check_citations.py --check` → `OK: 1104 citations resolve`. Tier is correct: all
five rows are in `examples/fakeshop/test_query/`, all reach the changed line through a real
`/graphql/` POST (`post_graphql` / `graphql_payload` over `django.test.Client`), no mock, no
`execute_sync`. Each asserts the boundary it claims — the refusals assert `data is None`, exactly
one error, the hook's own type name and the alias, and (sharded) zero `library_book` SQL on BOTH
aliases; the controls assert the served rows and the per-alias read counts. The three sharded rows
inherit the module-level `FAKESHOP_SHARDED` skip. `ruff check` → `All checks passed!`;
`scripts/check_trailing_commas.py --check` on the three files → exit 0.

BLOCKING: `ruff format --check` fails on the item's own new code.

```
$ uv run --directory "$WS" ruff format --check <the three paths>
1458 |     shelf_type = make_django_type(
     -         "AliasShelfType", models.Shelf, ("id", "code", "books"), node=False,
1459 +         "AliasShelfType",
...
1 file would be reformatted, 2 files already formatted
```

`examples/fakeshop/test_query/test_multi_db.py::_prefetch_alias_schema` #"AliasShelfType" is a
four-argument call left on one line with a magic trailing comma, which AGENTS.md's
explode-at-threshold layout (threshold 4) and the mandatory post-edit `uv run ruff format .` both
forbid. The `### Commands` section states the formatters were run; on this file they were not.
Fix: `uv run ruff format examples/fakeshop/test_query/test_multi_db.py`, re-run
`FAKESHOP_SHARDED=1 pytest examples/fakeshop/test_query/test_multi_db.py`, resubmit. Nothing else
is owed.

**5. Coverage.**
`pytest tests/optimizer examples/fakeshop/test_query/test_products_visibility_api.py
--cov=django_strawberry_framework.optimizer.walker --cov-report=term-missing -q -n0` →
`django_strawberry_framework/optimizer/walker.py  374  0  100%`, `869 passed`. The changed code
stays fully covered by the non-sharded suite: the single-DB refusal row drives the defect arm and
its control drives the accept arm, so the `fail_under = 100` gate does not depend on
`FAKESHOP_SHARDED=1`.

### Defects (Worker 2)

- **D-W2-a `_UNRECOMPOSED_CHILD_POLICY` is a published policy nothing applies.** Owner
  `django_strawberry_framework/utils/querysets.py`. After this item the constant has no production
  caller; `utils/querysets.py::apply_type_visibility_sync` and
  `utils/querysets.py::apply_type_visibility_async` still tell the reader the optimizer walker
  passes it, which the walker no longer does. Docstring-contradicting-its-body, with a contract
  source. Not fixable inside this item (the file is dirty with another session's
  `carry_result_cache` work). Needs a named card: either delete the constant and re-point
  `tests/utils/test_querysets.py` #"_UNRECOMPOSED_CHILD_POLICY" at `_PREFETCH_CHILD_POLICY`, or keep
  it as a named alias with a stated reason. Non-blocking.
- **D-W2-b The `reject_sliced=False` licence's premise does not hold for a plain list relation.**
  Owner `django_strawberry_framework/utils/querysets.py::_SealPolicy` #"Off one edge down" plus
  `django_strawberry_framework/optimizer/walker.py::_build_child_queryset`. The bullet justifies the
  licence by "the optimizer walker's nested-connection child, whose own gate degrades a sliced
  child"; `unwindowable_child_queryset_reason` is consulted only on the nested-connection / lateral
  / single-parent paths, never for a plain planned list relation. A child `get_queryset` returning
  a sliced queryset on such a relation therefore reaches Django's own recomposition and surfaces a
  raw `TypeError` ("Cannot filter a query once a slice has been taken.") outside the typed defect
  contract. PRE-EXISTING: reproduced identically with the walker reverted to HEAD, and plain Django
  raises the same error for the same `Prefetch("books", queryset=Book.objects.order_by("pk")[:1])`
  without this framework, so it is a wording / guard-scope robustness row, not a leak and not a D1
  regression. Non-blocking.

### Scratch to remove by explicit path after this verification

`$WS` is left on disk as instructed. Inside it:
`examples/fakeshop/test_query/test_w2_d1_attack.py` and
`examples/fakeshop/test_query/test_w2_django_sliced.py` (workspace-only, never in the shared tree).

### Revision 1

Two corrections, both raised by Worker 2. No test was added, removed or reworded, and no production
behavior changed.

**1. `ruff format --check` failed on `examples/fakeshop/test_query/test_multi_db.py`.** The
`shelf_type = make_django_type(...)` call inside `_prefetch_alias_schema` sat on one line carrying a
magic trailing comma. Cause is the COM812-versus-formatter interaction ruff warns about on every
run: the first `ruff format` collapsed the call, the `ruff check --fix` that followed added the
trailing comma, and nothing re-formatted afterwards, so the file was left in a state the formatter
would change. Fixed by re-running the formatter, which explodes the call to one argument per line:

```
     shelf_type = make_django_type(
-        "AliasShelfType", models.Shelf, ("id", "code", "books"), node=False,
+        "AliasShelfType",
+        models.Shelf,
+        ("id", "code", "books"),
+        node=False,
     )
```

Ordering lesson for this cycle: when both run, `ruff format` must be LAST, or `--check` disagrees
with what `--fix` just wrote.

**2. The walker docstring overclaimed.** It said the seed "is never pinned to a database alias",
which reads as a property of `_prepared_visibility_source` in general; that function's
priority-1 write-pipeline pin can supply an alias ahead of any seed, it is just unreachable on a
plan walk. Narrowed to a claim about this path and nothing else:

```
-    - the prefetch child is keyed on ``field.related_model``).
+    - the prefetch child is keyed on ``field.related_model``) and carries no
+    explicit ``.using(...)``. A plan walk is a read with no write pipeline in
+    force, so nothing pins an alias ahead of that seed either: the child's
+    effective alias entering the hook is ``None`` on this path, and the hook
+    cannot pin one of its own.
```

**Commands.** Shared tree, scoped to the item's paths:

- `uv run ruff format examples/fakeshop/test_query/test_multi_db.py` → `1 file reformatted`.
- `uv run ruff check --fix examples/fakeshop/test_query/test_multi_db.py` → `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py examples/fakeshop/test_query/test_multi_db.py` →
  `Fixed 0 file(s).`
- Same three on `django_strawberry_framework/optimizer/walker.py` after the docstring edit →
  `1 file left unchanged` / `All checks passed!` / `Fixed 0 file(s).`
- `uv run ruff format --check` on all three item paths → `3 files already formatted`.

Fresh workspace (`<scratch>/dry-ws/d1-fix-2`, rsynced with the same recipe; package `__file__`
printed as `.../dry-ws/d1-fix-2/django_strawberry_framework/__init__.py`, and the resolved database
names read from inside it as `.../dry-ws/d1-fix-2/examples/fakeshop/db.sqlite3` and
`.../db_shard_b.sqlite3`):

- `FAKESHOP_SHARDED=1 uv run --directory "$WS" pytest examples/fakeshop/test_query/test_multi_db.py
  --no-cov -q` — the WHOLE module, no `-k`, under the default parallel `-n auto` — →
  **`18 passed in 11.09s`** (8 workers, 18 items collected). 15 pre-existing rows plus this item's
  3.

Item-scoped diff after revision 1: `3 files changed, 269 insertions(+), 5 deletions(-)` (was 264
insertions; +5 are the two corrections above). Still no new files, so no
`git diff --no-index /dev/null <new>` row is owed. Nothing outside the three item paths was
touched, and the residue list above stands unchanged.

### Re-pass 1

Status: `verified`. The sole blocker from pass 1 is cleared and nothing else moved.

**Delta is exactly the two declared hunks.** The pass-1 workspace still holds the bytes I verified,
so the delta is read directly off it rather than off Worker 1's account:
`diff -u <d1-verify>/<path> <shared>/<path>` for all three item paths →
`examples/fakeshop/test_query/test_products_visibility_api.py` identical; `test_multi_db.py`
differs only at `_prefetch_alias_schema` #"AliasShelfType" (the four arguments exploded one per
line); `optimizer/walker.py` differs only in the `_build_child_queryset` docstring sentence about
the seed's alias. No other hunk, no other file. Every pass-1 finding therefore stands unretested.

**Lint, in a fresh copy `<scratch>/dry-ws/d1-verify-2`** (package `__file__` printed from inside it
first: `<WS2>/django_strawberry_framework/__init__.py`):

| command (in `$WS2`, three item paths) | result |
|---|---|
| `ruff format --check` | `3 files already formatted`, exit 0 |
| `ruff check` | `All checks passed!` |
| `python scripts/check_trailing_commas.py --check` | exit 0 |

**Tests re-run in `$WS2`:** `pytest examples/fakeshop/test_query/test_products_visibility_api.py
--no-cov -q -n0` → `14 passed`; `FAKESHOP_SHARDED=1 ... test_multi_db.py` → `18 passed`;
`FAKESHOP_SHARDED=1 ... test_products_visibility_api.py` → `14 passed`.

**The new docstring sentence is precise.** It now claims two things: the seed carries no explicit
`.using(...)`, and a plan walk is a read with no write pipeline in force, so the effective alias
entering the hook is `None` on this path. Both hold against
`utils/querysets.py::_prepared_visibility_source`, whose only two ways to a non-`None`
`required_alias` are the source's own `_db` (the seed has none) and priority 1,
`current_write_pipeline()`. That contextvar is set only inside
`utils/write_transaction.py::open_write_pipeline`, which `mutations/resolvers.py` #"with
open_write_pipeline(mutation_cls) as using:" enters as a `with` block around the mutation's own
body; the block has exited by the time any payload sub-field resolves, which is the only place an
optimizer plan walk could run under a mutation. So the claim is true for a sharper reason than the
one the sentence gives — it is not merely that a plan walk "is a read", it is that the pipeline's
scope closes before the walk can happen. The sentence asserts the conclusion without that
mechanism, which is a legitimate docstring choice at this altitude; my pass-1 tension note is
discharged.

Both `## Defects` entries marked `(Worker 2)` stand as written: `D-W2-a` (the
`_UNRECOMPOSED_CHILD_POLICY` residue) and `D-W2-b` (the slice-licence premise) are unchanged by
this revision and remain non-blocking, each needing a named owning card.

Scratch: `<scratch>/dry-ws/d1-verify-2` joins `d1-verify` on disk; both are workspace copies and
neither holds anything the shared tree needs.

### Adjudication pass 1 (run 2) — Worker 1

Adjudication run: `0.0.15 2026-09-21-2`. Run 1 verified this item at `5c62515a`;
HEAD is now `bfaee91d`. Scoped freshness adjudication only: every finding
F1..F12, iteration I-R1..I-R6 and defect D1..D5 re-derived against the new
tree. No production edits, no test edits, no new tracked files. Prior text
above untouched; this section appends.

Method. All nine causing commits were read as full diffs, never as messages:
`f7192bfb` (seal admits a project queryset class + `carry_result_cache`),
`4d9f1c3d` (retires `_UNRECOMPOSED_CHILD_POLICY`), `5741eaa6` (drops dead
seal wording + a false docstring reason), `fd39cac6` (owned D1 fix, ledgered),
`ffce6f29` / `0b110b51` / `319a1ec0` / `737b971b` (list_field ordering
guards), `dfb95984` (glossary child-seal wording), `02e266df` (tests). Every
claim below was verified against HEAD bytes via `git show bfaee91d:<path>`
and `git grep -n <symbol> bfaee91d`, not against the working tree (which
carries 60 dirty concurrent paths) and not against any commit message. The
`django_strawberry_framework/utils/querysets.py` diff `5c62515a..bfaee91d`
holds 26 hunks, all inside `f7192bfb` / `4d9f1c3d` / `5741eaa6`; their
old-line ranges are 51, 254, 2410, 2639, 2671, 2764, 2771, 2782, 2802, 3083,
3102, 3234, 3244, 3286, 3327, 3385, 3410, 3440, 3465, 3593, 3626, 3664, 3724,
3751, 3867, 4121. A symbol cited below as "outside all hunks" was checked
against exactly that list.

Enumeration recount at HEAD (`ast.Module.body`): 99 sync functions + 3 async
(`run_in_one_sync_boundary`, `apply_type_visibility_async`,
`post_process_queryset_result_async`) = 102 functions, 7 classes (same names),
24 module-level constants. 133 names, was 134: the one retirement is
`_UNRECOMPOSED_CHILD_POLICY`, which was assigned (F8 / I-R4), and no name was
added — so I-R5's completeness claim survives with one fewer assigned name.

#### Adjudication pass 1 (run 2) — F1 (CONFIRM)

Count stays 3. `auth/mutations.py` and `routers.py` are byte-identical
(MATCH), and every querysets hunk lies outside `_dispose_sync_awaitable` /
`_disposed_awaitable` / the reject sites (lines 160-230): `f7192bfb` touches
the seal, the deferred-filter bake, the policy record and the message sites;
`4d9f1c3d` touches the policy constants and two `apply_type_visibility`
docstrings; `5741eaa6` touches the `base_queryset` docstring and three
message sites. The second-axis challenge (futures awaited-with-timeout)
forces the same 3. Family `awaitable-refusal-and-disposal` unchanged.

#### Adjudication pass 1 (run 2) — F2 (REVISE: counts only, conclusion stands)

Still one owner. Re-ran the three package-wide mechanism searches at HEAD:
`models.QuerySet(` outside `utils/querysets.py` = 0 hits;
`sql.Query` touches outside = 0; executable `object.__getattribute__` /
`type.__getattribute__` / `inspect.getattr_static` outside = 0 (the one
textual hit, `utils/converters.py:119`, is a comment explaining why that
module avoids the protocol; the file predates the range, verified via
`git log`). `_seal_or_defect` still has exactly 5 call sites, all in this
file (querysets.py:2535, :2996, :3444, :3743, :3851). The four planning
readers on already-sealed querysets are unchanged and untouched in range:
`connection.py:1603` (`source.query.is_sliced`), `optimizer/nested_fetch.py`
123/131/197, `optimizer/predicates.py:165` (`queryset.query.combinator`),
`optimizer/extension.py:1161`; the three cited inventory-oracle tests still
exist at HEAD (`tests/utils/test_querysets.py:5033, :5055, :5082`).
`f7192bfb` extends the single sealing body (bake for every class, exact-bool
`negate` gate, `carry_result_cache` axis); it adds no second body, so no
challenge count moves. What does move is the record's own census: "the five
`_SealPolicy` fields" is now six (`carry_result_cache` added), and "the
seven policy constants" is now six (`_UNRECOMPOSED_CHILD_POLICY` retired):
`_DEFAULT`, `_CASCADE`, `_PREFETCH_CHILD`, `_LIST_ARGUMENT_VISIBILITY`,
`_ORDERSET_RESULT`, `_RAW_LIST_SOURCE_POLICY` (querysets.py:2792-2826). C13
still forces 1 definition — the new axis arrived as one field plus its
checks, the worked-example shape. The glossary *Sealed execution queryset*
projection moved with the code (`f7192bfb` documents the raw-list carry
there); production + projection moving together is the legitimate shape, not
a second definition. Family `sealed-execution-queryset` unchanged.

#### Adjudication pass 1 (run 2) — F3 (REVISE: gate population, rule now holds)

`_defect_message` still has exactly 6 call sites (permissions.py:353, :412;
querysets.py:3040, :3500, :3625, :3751) and the dispatcher itself
(querysets.py:3576) is outside all hunks. `f7192bfb` rewords only the
`untrusted` arm prose (deferred-filter phrase) at three sites; it changes no
code set and no arm set. `5741eaa6` removed the three dead-arm sites'
unreachable arms (see D5), so the rule F3 gates — "each site renders only
the subset IT can reach" — now HOLDS at every site except the two documented
modelling artifacts carried in I-R4 (orderset-alias subsumption, unchanged;
source-alias source-shape, new — both argued there, neither a defect).
Finding stays gate-plus-declaration in family `seal-defect-code-wording`,
now with D5 fixed rather than open.

#### Adjudication pass 1 (run 2) — F4 (CONFIRM)

Count stays 2. The seal's `reject_sliced` check is context (not `+`/`-`) in
the `f7192bfb` result-cache hunk; `connection.py::_guard_source_not_pre_sliced`
and `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` are in
MATCH files, byte-identical including the contract difference (reject vs
degrade-a-plan). `4d9f1c3d` preserves the slice licence on the surviving
`_PREFETCH_CHILD_POLICY` (`reject_sliced=False`); the retired constant was a
consumer of the policy field, never a third definition. `5741eaa6` is
wording-only. The family item's open question (legitimate wire adapter vs
second definition to delete) is unchanged, as is the `GraphQLError` vs
`ConfigurationError` proof it owes.

#### Adjudication pass 1 (run 2) — F5 (CONFIRM)

Count stays 2, site lists unchanged. The entire `types/resolvers.py` diff in
range is one 6-line comment reword inside `_make_relation_resolver`
(`f7192bfb`, lines 570-577, prefetched-rows-carry note);
`types/resolvers.py::_visible_related_object` (:395) is untouched, as is
`utils/querysets.py::visible_related_object` (:4060, outside all hunks) and
`related_visibility_queryset_or_default` (:3991). `utils/write_values.py`
and `rest_framework/resolvers.py` are MATCH. The disprove-first question the
family item owes (confirm-a-prefetched-row vs admit-a-client-named-row) is
untouched by every causing commit.

#### Adjudication pass 1 (run 2) — F6 (CONFIRM)

Rejection stands. `_stringified` (:4012), `stringified_pks_present`,
`pks_all_present` and `coerce_field_value_or_none` (310-344) are all outside
all hunks; `utils/write_transaction.py`, `utils/write_values.py` and
`rest_framework/resolvers.py` are MATCH. The contract difference (hashability
convenience over pre-canonical values vs fail-closed authorization equality)
is byte-identical, and the reconsideration trigger is untriggered (the
callers still route through `type_check_relation_id` — that file is MATCH).
`keyset.py:384` was not touched in range (not among the causing commits'
paths).

#### Adjudication pass 1 (run 2) — F7 (CONFIRM)

Rejection stands. `sync_pipeline_recourse` and `_RELAY_ASYNC_RECOURSE`
(347-372) are outside all hunks and byte-identical to the recorded literals;
`mutations/permissions.py` and `utils/permissions.py` are MATCH
(`_PERMISSION_ASYNC_RECOURSE` :50, `_GATE_ASYNC_RECOURSE` :59, same lines).
`permissions.py` changed only in the cascade `untrusted` arm wording
(`f7192bfb` hunks at :366, :397, :429); `_ASYNC_RECOURSE` (:136) and the
four-clauses-differ reason are untouched. Reconsideration trigger (differ
only in the subject noun) untriggered.

#### Adjudication pass 1 (run 2) — F8 (REVISE: the unguarded member is now guarded)

The two enforcement mechanisms are still 2 definitions, correctly counted:
`base_queryset`'s `using` arm (body unchanged — `5741eaa6` trimmed only the
docstring's false order clause, see D4) and `_seal_or_defect`'s
`require_shared_alias` arm (untouched). Enforcement sites `permissions.py:692`
(`using=state.alias`) and `filters/sets.py:2592` (`using=parent_db`) are
present at the same lines, and `_sealed_prefetch_related_lookups` still
threads the outer effective alias into the child seal (the `f7192bfb` hunk in
that function is comment-only). What changed is the row's "Unguarded member"
line: `optimizer/walker.py::_build_child_queryset` now seals under
`_PREFETCH_CHILD_POLICY` (owned fix `fd39cac6`, in the ledger; walker file
changed by no other commit in range) while still seeding unrouted by design
(the plan cache cannot hold a per-request alias — the D1-fix reasoning,
unchanged). `_UNRECOMPOSED_CHILD_POLICY`, the policy that line named, no
longer exists anywhere in `.py` at HEAD (`4d9f1c3d` deleted it; remaining
hits are this artifact's own history plus builder records). The glossary
projection now names `reject_sliced=False` in `_PREFETCH_CHILD_POLICY`
(`dfb95984`). The run-1 probe asymmetry (accepted under the walker's policy,
rejected under the prefetch child's) is therefore gone: both child seals are
now the same policy. Re-derived execution-verified — see "Probes re-run".
Coupling to D1 is discharged (D1 fixed, owned). Family
`child-queryset-alias-inheritance` still owes its family item (verify the
two-mechanism split at the new tree); Worker 0 note below proposes retiring
the `defect-routed` status.

#### Adjudication pass 1 (run 2) — F9 (CONFIRM)

Still no production reader. HEAD census (`git grep`): the definition
(querysets.py:412) is the only package hit; test readers are 5 asserts in
`tests/test_list_field.py` (689, 1450, 1456, 1466, 1475) plus 5 in
`tests/optimizer/test_extension.py` (5874, 5888, 5890, 5911, 5944) — 10
total, drifted from run-1's 16/11 by concurrent test edits, and the
conclusion never depended on the count. `wrap_` consumers are still
`list_field.py` only (4 call sites + import) and `unwrap_` still
`optimizer/extension.py:1142-1145` (returning `(value, was_adapted)`); the
list_field guard commits touch only the ordering classifier
(`_is_deterministic_order_name` / `_term` / `_value`, the order-value tables,
imports) plus nothing in the adapter path, and `list_field.py` is still
absent from every `__all__`/re-export for this symbol. The `resource_policy.py`
diff (`f7192bfb`: `_windowed_rows` / `bounded_rows` carry tails) adds no
reader. The principle-11 keep-or-delete decision with its oracle-shape
entailment still belongs to family `async-only-queryset-row-adapter`.

#### Adjudication pass 1 (run 2) — F10 (CONFIRM verdict, corrected census)

Rejection stands; the contract difference is byte-identical
(`connection.py` MATCH — :1050/:1095 still answer yes for a QuerySet, :1575
still the union admission test; `is_async_only_iterable` :375 outside all
hunks; `resource_policy.py:1216` still composes it by name; `list_field.py`
holds no direct `AsyncIterable`/`AsyncIterator` reference at HEAD, so no new
predicate was introduced by the guard commits). Census correction, in my
favour to record precisely: `list_field.py` had THREE composed call sites
already at run 1 (891, 895, 1387 at `5c62515a` — F10 cited two); at HEAD the
same three sites sit at 1333, 1337, 1829 (shifted by classifier growth, none
added or removed in range). Reconsideration trigger untriggered.

#### Adjudication pass 1 (run 2) — F11 (CONFIRM)

Still 1 definition, same classification. `run_in_one_sync_boundary` (:465)
is outside all hunks; all six consumer files still compose it by name
(`schema.py` import shifted 73→79 inside `f7192bfb`'s schema hunk;
`permissions.py:125`, `orders/sets.py:50`, `filters/sets.py`,
`mutations/resolvers.py`, `auth/mutations.py` unchanged). The five direct
`sync_to_async(...)` sites are at byte-identical lines with byte-identical
shapes: `types/resolvers.py` 616/689/760 (`sync_to_async(getattr,
thread_sensitive=True)` — `f7192bfb`'s 6-line comment swap preserved the
line count) and `testing/client.py` 471/475 (bare calls). Neither encodes
the consumer-hook rule, as recorded. Family `one-sync-boundary` unchanged.

#### Adjudication pass 1 (run 2) — F12 (CONFIRM all live rows; two stay superseded)

Re-swept every row whose consumers live in a changed module; the two
superseded rows (`_safe_class_name`, `_prefetch_relation_target_or_none`)
are adjudicated under I-R6 / I-R1 and not here.

- `_safe_routing_repr`: production readers still only `_seal_or_defect`'s
  routing arm (:3225-3228). 1 definition. CONFIRM.
- `_GraphWalk` / `_WalkState` / `_walk_short_circuit`: lines 826-900,
  outside all hunks; no second recursive proof in range (the
  `converters.py:119` textual hit is a pre-existing comment). CONFIRM.
- `_snapshot_routing_intent` (:2881, outside hunks): sole external consumer
  still `list_field.py` (:1369, :1397); guard commits don't touch the call
  sites. CONFIRM.
- `_routing_hints_equal` (:2830, outside hunks): reader still the seal
  (:3219). CONFIRM.
- `_bake_deferred_filter_or_defect` + `_deferred_value_defect`: `f7192bfb`
  strengthened the single body (exact-`bool` `negate` gate; bake runs for
  every class instead of exact-`QuerySet` only) without adding a second one:
  sole caller still `_seal_or_defect` (:3274), `PROHIBITED_FILTER_KWARGS`
  still single-sited (import + floor mirror :101-108, one use :2660). The
  recorded challenge still returns 1. CONFIRM.
- `prepared_resolver_source` (:4241, outside hunks): still composed by both
  collection flavors (`connection.py:1762`, `list_field.py:1793, :1840`);
  guard hunks never touch the resolver head. CONFIRM.
- `_coerced_manager_queryset` and `SyncMisuseError`: see I-R3 / I-R5.

#### Adjudication pass 1 (run 2) — I-R1 (CONFIRM)

Rejection stands. `_prefetch_relation_target_or_none` (:2304) and
`_reverse_relation_by_accessor_or_none` (:2354) are outside all hunks (the
nearest hunk, 2410, is the NEXT function's docstring, per its `@@` header);
`utils/relations.py`, `connection.py` and `optimizer/plans.py` are MATCH, so
the five-body mechanism table is byte-identical. `list_field.py::
_is_deterministic_order_name` still exists (:824 def, :956 call), so the
"count rises to 7" caveat stands. `02e266df`'s `tests/utils/test_querysets.py`
edit retires a package-tier proxy-prefetch test in favour of its live-tier
promotion — a tier move, not a contract change; the fail-open-vs-raise
contract difference and both reconsideration triggers are untouched.

#### Adjudication pass 1 (run 2) — I-R2 (CONFIRM)

Family naming and both exclusions stand. `utils/permissions.py` and
`filters/base.py` are MATCH, so the exclusion reasoning rests on unchanged
bodies (the former never touches `Model._meta.get_field`, the latter
resolves through the registry graph). No causing commit touches either file.
Family `orm-lookup-path-resolution` unchanged.

#### Adjudication pass 1 (run 2) — I-R3 (CONFIRM)

Still file-local. `models.Manager` appears at exactly three lines
package-wide, all in this file (querysets.py:305, :3526, :3849 — numbers
shifted by the carry hunks, count and file identical). `_coerced_manager_queryset`
(:3526) sits below the last message-site hunk (ends :3522) and is untouched;
both entry points (`normalize_query_source`, `_normalized_visibility_result`)
are intact. The flag to the `utils/` folder item (least margin, visibility
bypass on failure) stands.

#### Adjudication pass 1 (run 2) — I-R4 (REVISE: policy set swapped, dead arms gone, one new artifact)

Both load-bearing facts re-derived against the new tree rather than
inherited. (1) `expected_routing` is still passed at exactly 1 of the 5
`_seal_or_defect` calls (`_validate_post_orderset_result`, :3001); the other
four (:2535, :3444, :3743, :3851) pass none — verified by `git grep`, not
from the probe's table. So `routing` is still unreachable at both
visibility sites. (2) The complete `policy=` set reaching the runners is
now `_DEFAULT_SEAL_POLICY` (default), `_CASCADE_SEAL_POLICY`
(permissions.py:623, :705), `_PREFETCH_CHILD_POLICY` (walker.py:476) and
`_LIST_ARGUMENT_VISIBILITY_POLICY` (list_field.py:1522, :1575) — four
policies, with `_PREFETCH_CHILD_POLICY` in place of the retired
`_UNRECOMPOSED_CHILD_POLICY`. None of the four sets `require_unevaluated`
(still only `_ORDERSET_RESULT_POLICY`, still reaching the seal solely
through `_validate_post_orderset_result`), so `evaluated` is still
unreachable at both sites. The `SITES` table with that one swap is sound.

`probe_defect_arms_r2.py` (adjudication scope, same instrument, swapped
policy) reports `sites with a mismatch: 2/6` with ZERO dead arms anywhere:
`_raw_list_source_message` OK, `_visibility_result_error` OK, both
`permissions.py` sites OK — the D5 fix holds. The two mismatch rows are both
`missing: ['alias']` modelling artifacts, and they need different reasons:
(a) `_validate_post_orderset_result` — the KNOWN I-R4 artifact (documented
`routing`-subsumes-`alias` subsumption, comment intact at :3013-3023);
(b) `_prepared_visibility_source` — NEW, and it arrives from the coarse
model, not from the tree: the model adds `alias` because
`_PREFETCH_CHILD_POLICY.require_shared_alias` is set, but the seal emits
`alias` there only for a (shared-alias policy, explicitly-routed source)
pair, and the sole caller passing that policy (the walker) always passes the
unrouted `base_queryset` seed — the write-pipeline pin resolves AFTER this
seal and cannot change what it emits, and on a plan walk there is no
pipeline at all (D1 re-pass). A pre-routed default manager is the only
shape that could produce the pair; none exists, and even it would fail
closed (unrendered-code wording), never open. So no arm is owed — adding
one would be wording no rejection can quote, exactly what D5 deleted.
Trigger: if a caller ever passes `_PREFETCH_CHILD_POLICY` with a routed
source to `_prepared_visibility_source`, the site owes an `alias` arm.
The gate population's fourth term (declared subsumptions must be
machine-readable) gains this fifth: source-shape pairings the coarse model
cannot see must be recorded with the site. Family
`seal-defect-code-wording` stays gate-plus-declaration.

#### Adjudication pass 1 (run 2) — I-R5 (CONFIRM)

Still file-local with the population recorded. `SyncMisuseError` (119-139)
is outside all hunks with unchanged bases
(`ConfigurationError`, `RuntimeError`); both siblings keep
(`GraphQLError`, `DjangoStrawberryFrameworkError`)
(`list_field.py::ListArgumentError` :248,
`resource_policy.py::ResourceLimitExceeded` :121) — the list_field guard
hunks touch only the ordering classifier and the resource_policy hunks only
the window/bound tails, neither near a marker. Declarations-not-definitions
reasoning stands.

#### Adjudication pass 1 (run 2) — I-R6 (CONFIRM)

Rejection stands. `utils/querysets.py::_safe_class_name` (142-157) is
outside all hunks; `exceptions.py` is MATCH, so the contract difference
(`_safe_arg_repr` routing vs metaclass-label degrade) and the trigger (stop
routing non-string names through `_safe_arg_repr`) rest on unchanged bodies
at both owners.

#### Adjudication pass 1 (run 2) — D1 (FIXED by owned fd39cac6; policy retired by 4d9f1c3d)

Disposition: fixed (owned fix, in the ledger — not a concurrent fix).
Verified at HEAD: the walker seeds `base_queryset(field.related_model)`
unrouted and seals `policy=_PREFETCH_CHILD_POLICY` (walker.py:447-476; the
file changed by no commit but `fd39cac6` in range); the policy D1 named no
longer exists (`4d9f1c3d`). `probe_alias_policy_r2.py` re-derives the
now-holding behavior execution-verified: the same explicitly-routed
queryset is rejected with `('alias', 'shard_b')` under `_PREFETCH_CHILD_POLICY`
and the walker's only `policy=` keyword is that policy — the run-1
accept/reject asymmetry is gone because both child seals are one policy.
The five permanent live rows `fd39cac6` added (2 single-DB, 3 sharded) pin
the observable half, including the cross-connection consequence that
`## Pending execution` entry 1 left `unverified` — see the Pending note
below. `## Defects` routing note stays accurate (owner pair named; the
seal-policy half is deleted, the walker half carries the fix).

#### Adjudication pass 1 (run 2) — D2 (CONCURRENTLY FIXED by dfb95984 + 4d9f1c3d)

Disposition: concurrently fixed. Glossary half fixed by `dfb95984`: *Prefetch
alias threading* now reads "`reject_sliced=False` in `_PREFETCH_CHILD_POLICY`"
(GLOSSARY.md:1558). spec-034 half fixed by `4d9f1c3d`: the "Verified
dependency to protect" clause now reads
`apply_type_visibility_sync(target_type, queryset, info,
policy=_PREFETCH_CHILD_POLICY)` (spec-034:353). `allow_sliced` has zero hits
at HEAD across the package, the glossary and spec-034; the remaining hits
(spec-045's four, rationale appendices, build records, this artifact's own
history) are the historical records D2 already exempted. `## Defects`
routing note stays accurate; the repair Worker 0 must home is record-keeping
(the fix has landed), not new work.

#### Adjudication pass 1 (run 2) — D3 (CONFIRM: still ambiguous, still routed to the maintainer)

`list_field.py::_apply_orderset_sync` / `_async` still freeze routing intent
(:1369/:1397) and re-seal through `_validate_post_orderset_result`
(:1377/:1411); `connection.py:1828/:1865` still invoke the same public
`OrderSet.apply_sync` / `apply_async` with neither (connection.py MATCH).
Both contract sources still scope the rule to the list field:
`_SealPolicy.require_unevaluated`'s prose still reasons from "the list field
invoked that ordering method one step earlier" (the new `carry_result_cache`
bullet names itself that axis's complement without rescoping it), and the
spec-050 Edge sentence still reads as quoted (spec-050:2123). No
consolidation depends on it. Unchanged: ambiguous → the maintainer, through Worker 0.

#### Adjudication pass 1 (run 2) — D4 (CONCURRENTLY FIXED by 5741eaa6)

Disposition: concurrently fixed. The "`manager.using(alias).all()` (never
`.all().using(alias)`)" clause is gone from `base_queryset`'s docstring;
what stays is the real reason (`using` pins the seed so a sharded parent
seeds children on the same connection). Body unchanged
(`manager.using(using).all() if using is not None else manager.all()`).
`probe_using_order.py` re-run read-only at the new tree: identical output
(`default manager: shard_b shard_b True True`) — replayable as
`uv run python docs/dry/temp-tests/dry-file-utils__querysets/probe_using_order.py`.
`## Defects` routing note stays accurate; like D2 the fix has landed, so
Worker 0 homes the record, not new work.

#### Adjudication pass 1 (run 2) — D5 (CONCURRENTLY FIXED by 5741eaa6)

Disposition: concurrently fixed, arm by arm re-derived against the new tree
(not the commit message). `_raw_list_source_message` declares only
type/table/untrusted: `combined` unreachable because
`_RAW_LIST_SOURCE_POLICY` still leaves `reject_combined` at its `False`
default (verified :2823-2826) — arm correctly removed, and the docstring now
enumerates `combined` among the switched-off codes, repairing the false
sentence. `_prepared_visibility_source` and `_visibility_result_error`:
`routing` unreachable (expected_routing still single-site, :3001) and
`evaluated` unreachable (no runner policy sets `require_unevaluated` — the
set is re-derived in I-R4, not inherited) — both arms correctly removed at
both sites. Now-holding behavior: each site renders exactly its reachable
set (type/table/untrusted at the raw-list site; + sliced/combined/projection
at the source site; + alias at the result site; the permissions pair
unchanged as the discriminating control), and any code the seal gains
without an arm renders as the framework defect `_defect_message` names
rather than as wording nothing can quote. `probe_defect_arms_r2.py`: zero
dead arms at all six sites. Family `seal-defect-code-wording`; routing note
stays accurate (fix landed; Worker 0 homes the record).

Worker-2 D1-verification defects, observed (outside the F/D scope, one line
each for Worker 0): D-W2-a is fixed — `4d9f1c3d` deleted the constant and
named the walker's actual policy in both `apply_type_visibility` docstrings.
D-W2-b is untouched — the slice-licence premise still reads as recorded
(nested-connection gate paths unchanged in range), still open as recorded.

#### Adjudication pass 1 (run 2) — probes re-run (replay info)

Retained probes: `probe_using_order.py` re-run read-only at the new tree,
same output as run 1 (command + output in D4 above); it needs no update.
`probe_alias_policy.py` and `probe_defect_arms.py` no longer import — both
name the retired `_UNRECOMPOSED_CHILD_POLICY` (verified: `ImportError` /
`AttributeError` on the live tree). Their successors live ONLY in the
adjudication scope `docs/dry/temp-tests/dry-adjud-querysets-w1-r2/` (earlier
scopes untouched); both read-only, zero SQL:

- `uv run python docs/dry/temp-tests/dry-adjud-querysets-w1-r2/probe_alias_policy_r2.py`
  → `_DEFAULT_SEAL_POLICY: defect=None sealed_db='shard_b'`,
  `_PREFETCH_CHILD_POLICY: defect=('alias', 'shard_b') sealed_db=None`,
  `walker passes _PREFETCH_CHILD_POLICY: True` (AST-asserted). Discharges
  F8/D1's now-holding behavior. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-adjud-querysets-w1-r2/probe_defect_arms_r2.py`
  → `sites with a mismatch: 2/6`, zero dead arms; the two rows are the
  documented artifacts argued in I-R4 (orderset-alias subsumption;
  source-alias source-shape). Negative control intact
  (`raw-list policy reaches ['type', 'table', 'untrusted']`), exit 0.
  Discharges D5/I-R4/F3. `execution-verified`.

No source-mutating proof was needed (nothing here mutates source), so no
disposable workspace was built. The one authorized focused shared-tree run
was not spent. `FAKESHOP_SHARDED=1` and Postgres cells stay `unverified`
except where `fd39cac6`'s own record already ran them in its workspaces.

#### Adjudication pass 1 (run 2) — freshness, refreshed to HEAD bfaee91d

`git rev-parse HEAD:<path>` for every input any finding fingerprints
(including the four I-R exclusions Worker 0's 18-row table did not list):

```text
django_strawberry_framework/utils/querysets.py    96618fba4eafb6a87e73414770014e3aee5b41ef
django_strawberry_framework/auth/mutations.py     dbe64995b87240b87a1d5119f46cc42c7cab646f
django_strawberry_framework/routers.py            a18c5001471d4a937bb81d2ff41a2e442e7d2dad
tests/utils/test_querysets.py                     977a81df44b5cede99b2be9b8dcc5be76db0f03a
django_strawberry_framework/permissions.py        757dce34cecd7a249b2634947a771d4608808bfe
django_strawberry_framework/connection.py         93e998f2c7ea1d7f18607a6e37e394466ac75ad4
django_strawberry_framework/optimizer/nested_fetch.py 4d8d37a7f52cf94d2916f17db3a8a21393e28d57
django_strawberry_framework/types/resolvers.py    f3341e6a9f52659925762bce097033bac67e3b51
django_strawberry_framework/utils/write_values.py d28587c7c8d9f0d25e0a01bf289a63d9c3291728
django_strawberry_framework/rest_framework/resolvers.py 8024703ec0fb09758daeec0585e0065de1c61fc3
django_strawberry_framework/utils/write_transaction.py eca9ad4d3f765964df05884e080eb3ea63190ca8
django_strawberry_framework/mutations/permissions.py 54f770ae5aa1238327246cd2dcb141e8aac14965
django_strawberry_framework/utils/permissions.py  9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec
django_strawberry_framework/optimizer/walker.py   9b111ed938951a073a9226ccbcfacabc3af981e8
django_strawberry_framework/filters/sets.py       4ab65a26b0ccf56f7f40f4938282bba9690673d1
docs/GLOSSARY.md                                  bc51debc54cf3ed142b45fa9feda1b99bce60c79
django_strawberry_framework/list_field.py         ce682d5f79518919ff3676f2fc8bbe2bd33995a4
django_strawberry_framework/resource_policy.py    647133d23785d325856b2d1d495d18c5741dd23c
django_strawberry_framework/utils/relations.py    7662b0bb669c4dfba4a437f3b8f309357f718dca
django_strawberry_framework/optimizer/plans.py    cce985319c8833f3660653327d3003f1f03655a5
django_strawberry_framework/exceptions.py         e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b
django_strawberry_framework/filters/base.py       ba52351c284425336262ae6c2b82b262f6586fc0
```

The last four match their run-1 values (I-R1/I-R2/I-R6 rest on unchanged
bodies). Every other row above supersedes the corresponding run-1 `Freshness`
line for the re-derived conclusion; no run-1 line was edited.

#### Adjudication pass 1 (run 2) — `## Pending execution` note (state changed, entries kept)

Entries 1-3 above stand as run-1 history; two state changes for the gate:

1. Entry 1 (`proof: FAKESHOP_SHARDED=1 ... -k prefetch`) is now pinned by
   permanent tests: owned `fd39cac6` added five live rows (2 single-DB in
   `test_products_visibility_api.py`, 3 sharded in `test_multi_db.py`) whose
   fail-without-fix runs are recorded in `## D1 fix` / `## D1 independent
   verification`. The gate should run those node ids (both modes) instead of
   treating D1's consequence as deferred — the `-k prefetch` sweep stays a
   valid superset command.
2. Entry 3's witness command names the retired probe path. The gate should
   run `uv run python docs/dry/temp-tests/dry-adjud-querysets-w1-r2/probe_defect_arms_r2.py`
   and expect `sites with a mismatch: 2/6` with zero dead arms (rows argued
   in I-R4 above); the original path now exits `AttributeError` by design
   (it names the deleted policy).

Entry 2 unchanged.

#### Adjudication pass 1 (run 2) — family-index changes Worker 0 must apply (I never edit the plan)

1. `child-queryset-alias-inheritance`: `defect-routed` → `open`. D1 is fixed
   by the owned `fd39cac6` (ledgered) and F8 is revised; the family item is
   still owed (verify the two-mechanism split at the new tree) but no defect
   blocks it.
2. `seal-defect-code-wording`: keep `open`, update the parenthetical. It
   reads "carries F3 as gate-plus-declaration, and D5"; D5 is now fixed by
   `5741eaa6` and F3/I-R4 are revised (rule holds modulo two documented
   artifacts). Suggested: "carries F3 as gate-plus-declaration (D5 fixed by
   5741eaa6; gate population revised run 2)".
3. No other index row changes: no new family, no further status move. The
   file-item line keeps `verified, pending execution` pending Worker 2's
   two-phase verification of this pass; only its verdict returns the item to
   `verified`.

#### Adjudication pass 1 (run 2) — item state

Zero production edits, zero test edits, zero new tracked files. Untracked
scratch created, all inside the adjudication scope (other scopes untouched):
`docs/dry/temp-tests/dry-adjud-querysets-w1-r2/probe_alias_policy_r2.py` and
`.../probe_defect_arms_r2.py`. Item-scoped diff vs
`ITEM_BASELINE=1eb4ae4fd24cf3297f43f97df4e6c8cfe72040de` covers only this
artifact's append (verified before finishing; package tree clean, zero
untracked package files). `uv run ruff check` / `ruff format` not run: no
`.py` file was edited; the layout script's `.md` scaffold needs nothing
(the append carries no cross-file links). Concurrent dirt (60 paths,
docs/examples/tests, none under the package) left alone.

## Independent verification (Worker 2) — adjudication expectations (Phase A)

Recorded BEFORE reading `### Adjudication pass 1 (run 2) — Worker 1` or opening
Worker 1's run-2 scratch. Every claim below is re-derived from HEAD bytes
(`git show HEAD:<path>` / `git grep -n <symbol> HEAD`) and the causing-commit
diffs, never from the dirty working copy and never from run-1 prose. HEAD is
`bfaee91d`; `git status --short -- django_strawberry_framework/` is empty;
`git diff 1eb4ae4fd24cf3297f43f97df4e6c8cfe72040de -- django_strawberry_framework/`
is empty when checked mid-phase (a concurrent session dirtied package files before phase end — see the Phase-B ruling; all evidence here is HEAD-pinned, unaffected).

### Provenance and scope

Re-hashed all 18 plan inputs at HEAD: all match the plan's `HEAD now` column
exactly (10 MATCH byte-for-byte, 8 STALE as recorded). The four extra
fingerprints revision 1 added (`utils/relations.py` `7662b0bb…`,
`optimizer/plans.py` `cce98531…`, `exceptions.py` `e06b0b7f…`,
`filters/base.py` `ba52351c…`) are unchanged `5c62515a..bfaee91d`.
Commit-to-file scope in range (`git log --oneline 5c62515a..bfaee91d -- <path>`):
querysets.py ← exactly f7192bfb + 4d9f1c3d + 5741eaa6; permissions.py,
types/resolvers.py, resource_policy.py ← f7192bfb only; walker.py ← fd39cac6
only; list_field.py ← exactly ffce6f29 + 0b110b51 + 319a1ec0 + 737b971b;
schema.py ← f7192bfb + ffce6f29; GLOSSARY.md ← dfb95984 + f7192bfb + 737b971b;
tests/utils/test_querysets.py ← f7192bfb + 4d9f1c3d + 5741eaa6 + 02e266df.
Unchanged in range (verified, each bears on a finding below): connection.py,
nested_fetch.py, write_values.py, write_transaction.py, rest_framework/resolvers.py,
mutations/permissions.py, utils/permissions.py, filters/sets.py, auth/mutations.py,
routers.py, optimizer/extension.py, optimizer/predicates.py, optimizer/plans.py,
optimizer/lateral_fetch.py, optimizer/nested_planner.py, optimizer/single_parent_fetch.py,
mutations/resolvers.py, forms/resolvers.py, relay.py, filters/base.py, keyset.py,
orders/sets.py, testing/client.py, utils/converters.py, exceptions.py,
utils/relations.py.

Full querysets.py hunk map `5c62515a..bfaee91d` (26 hunks; `grep -c` over the
diff): module docstring + `_sealed_prefetch_related_lookups` docstring +
`_visibility_result_error`/`_prepared_visibility_source` `untrusted` strings +
permissions.py strings (f7192bfb wording "unresolved deferred filter" →
"malformed deferred-filter state", prose only); `base_queryset` docstring
(5741eaa6, D4 clause dropped, body identical); `_bake_deferred_filter_or_defect`
+1 exact-`bool` `negate` gate + docstring; `_SealPolicy` +1 field
(`carry_result_cache`) + bullet; policy constants −1 (`_UNRECOMPOSED_CHILD_POLICY`
retired, 4d9f1c3d) with `_PREFETCH_CHILD_POLICY` comment rewritten and
`_RAW_LIST_SOURCE_POLICY` gaining `carry_result_cache=True`; `_seal_or_defect`
docstring (deferred-bake-for-all + carry prose), bake call for EVERY candidate
(the exact-`QuerySet`-only refusal deleted), +1 exact-`list` carry gate
(emits existing code `untrusted`), +1 carry tail (`sealed._result_cache =
result_cache`); `normalized_row_source`/`materialized_rows` docstrings;
−5 message arms (`combined` at raw-list; `evaluated` + `routing` at each
visibility site) + raw-list docstring fix (5741eaa6, D5); both runner docstrings
(walker policy name). Untouched bodies (no hunk in their spans): every
disposal/refusal symbol, `model_for`, `initial_queryset`, `_coerced_manager_queryset`,
`normalize_query_source`, `is_async_only_iterable`, the adapter trio,
`run_in_one_sync_boundary`, `sync_pipeline_recourse`, `coerce_field_value_or_none`,
`_stringified` + both pk-set helpers, all visibility runners/relation helpers,
`_safe_class_name`, `_safe_routing_repr`, `_GraphWalk` family,
`_snapshot_routing_intent`, `_routing_hints_equal`, `_prefetch_relation_target_or_none`,
`prepared_resolver_source`, `SyncMisuseError`, both post-process twins,
`_validate_post_orderset_result`, `_defect_message`, `_RoutingIntent`.

### Findings

**F1 — HOLDS.** `_dispose_sync_awaitable` body byte-identical (region has no
hunk); auth/mutations.py + routers.py MATCH so both inline copies
(auth/mutations.py #"is_authenticated.close()" ×2, routers.py
#"application.close()") are byte-identical. Count stays 3 definitions;
consumer list unchanged (all consumer files MATCH or untouched: list_field.py
still reaches `_apply_orderset_sync`/`_async` at HEAD lines 1356/1386 with the
same freeze/re-seal shape; relay.py, utils/permissions.py, mutations/permissions.py
unchanged). f7192bfb/4d9f1c3d/5741eaa6 hunks never mention the disposal symbols
in a `+`/`-` line (verified by grep over the diff).

**F2 — NEEDS REVISION (counts only).** Owner, exclusivity, and mechanism census
all re-verified at HEAD: `_seal_or_defect` is still the single sealing
primitive with exactly 5 call sites, all in-file (HEAD
utils/querysets.py:2535 inner-prefetch, :2996 post-orderset, :3444 raw-list,
:3743 prepared-source, :3851 normalized-result); `models.QuerySet(` is
constructed at exactly 1 package site (HEAD :3352, the seal's own rebuild);
`sql.Query` outside querysets.py is only the pre-existing
optimizer/lateral_fetch.py:82 `sql.where` import (file unchanged in range — no
new site); `object.__getattribute__`/`type.__getattribute__`/
`inspect.getattr_static` outside querysets.py is only the pre-existing prose
mention at utils/converters.py:119 (file unchanged — no new site); the four
planning readers are byte-identical files (connection.py, nested_fetch.py,
predicates.py, extension.py all unchanged); the defect-code set is still the
same closed 9 with the same canonical order (HEAD :3056-3058; f7192bfb's carry
gate emits existing code `untrusted`, no new code). What is stale: "the five
`_SealPolicy` fields" is now SIX (`carry_result_cache`, HEAD :2782-2787) and
"the seven policy constants" is now SIX (HEAD :2792-2826; `_UNRECOMPOSED_CHILD_POLICY`
retired, zero `.py` hits at HEAD). C13's shorthand "one field + one check"
needs one clause: f7192bfb — a live C13 exercise — landed as one field + one
check + one rebuild-tail write (`sealed._result_cache`), all inside the one
definition plus the one constant that sets the flag; definition count 1 held
in practice.

**F3 — NEEDS REVISION (gate population, not the verdict).** Core holds: 1
definition (control flow in `_seal_or_defect`), 6 `_defect_message` call sites
(permissions.py:353/:412 unchanged lines; querysets.py:3040 post-orderset,
:3500 raw-list, :3625 result-error, :3751 prepared-source), canonical order
intact, still no gate. What is stale: the population must be restated for the
D5-fixed tree (all dead arms gone — measured zero, see D5) AND for the walker
policy swap: `SOURCE_POLICIES` now contains a `require_shared_alias` setter
(`_PREFETCH_CHILD_POLICY`), so the run-1 union model newly flags `missing:
['alias']` at `_prepared_visibility_source` (measured with my successor probe;
see I-R4). The finding stays gate-plus-declaration per I-R4 with one more
population term owed.

**F4 — HOLDS.** `connection.py::_guard_source_not_pre_sliced` byte-identical
(file MATCH); the seal's `sliced` arm (`if policy.reject_sliced and
rebuilt_query.is_sliced`, HEAD :~3329) untouched; `nested_fetch.py`
(byte-identical) still degrades rather than rejects. f7192bfb's bake/carry
hunks do not touch `reject_sliced` or any of the three sites. Count stays 2
definitions; the error-class/timing/dispatch differences are unchanged text.

**F5 — HOLDS.** types/resolvers.py's only range hunk is the f7192bfb comment
reword at :~570 (no executable line); `_visible_related_object` (def HEAD :395)
with its 7 call sites (:625/:640/:701/:718/:737/:774/:794) and
`visible_related_object` (def HEAD :4060) are byte-identical; consumers
(write_values.py:226, rest_framework/resolvers.py, types/resolvers.py ×7) all in
MATCH files. Count stays 2 definitions; seed-pin/coloring adapter shape
unchanged.

**F6 REJECTED — HOLDS.** `utils/write_transaction.py` + `utils/write_values.py`
MATCH; `_stringified`/pk-set helpers/coercion regions have no hunk. The
contract difference (pre-canonicalized set-membership basis vs uncoerced
same-row? raise) is unchanged text; the trigger (a caller reaching the
stringified basis without `type_check_relation_id`) has no new caller — no
file in the family changed except querysets.py prose/bake regions that do not
call these helpers (verified: no `+`/`-` line mentions them).

**F7 REJECTED — HOLDS.** All four recourse definitions byte-identical
(querysets.py region untouched; mutations/permissions.py, utils/permissions.py
MATCH; permissions.py:136 `_ASYNC_RECOURSE` outside the three string hunks at
:366/:397/:429). The three `sync_pipeline_recourse` compositions intact
(mutations/resolvers.py:139, forms/resolvers.py:125,
rest_framework/resolvers.py:201 — all files unchanged). Shared-one-clause /
differing-remedy differences re-read and unchanged; trigger unmet.

**F8 — NEEDS REVISION (the member is now guarded).** Mechanisms intact: seed pin
(`base_queryset(using=)`, body identical) + `require_shared_alias` arm
(HEAD :3336-3342, identical semantics); enforcement sites intact
(permissions.py:692 `using=state.alias` re-read; filters/sets.py:2592 in a MATCH
file; `_sealed_prefetch_related_lookups` threading comment + code re-read, only
its docstring retouched). What is stale: the "one unguarded member" —
walker.py:476 now seals under `_PREFETCH_CHILD_POLICY` (fd39cac6, the owned
fix); the accepting policy `_UNRECOMPOSED_CHILD_POLICY` no longer exists (zero
`.py` hits); the glossary projection now names the current policy (dfb95984).
F8's run-1 probe quotation is history; my successor probe re-proves the current
asymmetry (default accepts, prefetch-child rejects `('alias', 'shard_b')`,
unrouted inherits — exit 0). The family is no longer blocked by an unguarded
member; the defect-routed status wants the fixed state recorded.

**F9 — HOLDS.** `is_async_queryset_adapter` (def HEAD :412) still has zero
production readers package-wide (only test files read it:
tests/test_list_field.py 7 lines, tests/optimizer/test_extension.py 9 lines —
same files, and neither gained a production use); `wrap_` readers still
list_field.py (HEAD :1515/:1551/:1568/:1604) + extension.py:1145, `unwrap_`
still extension.py:1142 (same lines — file unchanged). The four list_field
guard commits added no reader (their hunks are classifier/offset-guard code;
verified the reader census, not the commit messages). Principle-11 question
stands as written for the family item.

**F10 REJECTED — HOLDS.** connection.py MATCH, so the three async-shape tests
(:1050/:1095/:1575) and the contract difference (difference vs union vs
admission question; queryset-must-stream-yes) are byte-identical. The real
predicate's consumers are the same three sites, only shifted by guard
insertions (list_field.py 891/895/1387 → 1333/1337/1829 — verified the 1829
site pre-existed at 1387 in 5c62515a bytes; resource_policy.py:1216; local
:458). No new consumer, no new spelling. Trigger unmet.

**F11 — HOLDS.** 1 definition (`run_in_one_sync_boundary`, HEAD :465, body
identical); all six composing consumers intact (schema.py import shifted 73→79
by the ffce6f29 import expansion, call sites :346/:360/:373 same shape;
permissions.py:734, orders/sets.py:831, filters/sets.py:3497,
mutations/resolvers.py:1288, auth/mutations.py ×6 — all re-censused); the five
direct `sync_to_async(` sites unchanged (types/resolvers.py:616/:689/:760,
testing/client.py:471/:475 — both files' diffs, where any, do not touch these
lines; full-package `sync_to_async(` census shows no other executable call).
The schema.py/error-policy/consumers hunks add no boundary call. The
testing/client.py `thread_sensitive` omission note stands (lines identical).

**F12 rows — HOLD (all ten, with the two I-R1/I-R2/I-R6 supersessions standing
as revisions, not reversions).** Every row's owner region has no hunk except
the deferred-bake row, whose helper gained the exact-`bool` `negate` gate
inside the same single body (f7192bfb :2637-2650) — the row's challenge (single
`PROHIBITED_FILTER_KWARGS` site) still counts 1, and the new gate is a second
axis landing in the same one definition, corroborating rather than disturbing
it. Spot re-censuses: `models.Manager` still exactly 3 lines, all in-file
(HEAD :305/:3526/:3849); `prepared_resolver_source` still composed by both
flavors (connection.py:1762 in a MATCH file; list_field.py:1793/:1840);
`_safe_routing_repr` production readers still only the routing arm (HEAD
:3225-3228); `_snapshot_routing_intent` sole external consumer still list_field
(:1369/:1397); `_GraphWalk` family byte-identical (region has no body hunk, so
the "7 in-module callers" count is unchanged by construction);
`_routing_hints_equal`, `_coerced_manager_queryset`, `SyncMisuseError` regions
untouched. The `_safe_class_name` and `_prefetch_relation_target_or_none`
rows stay superseded-by-rejection per I-R6/I-R1 (see below).

### Iterations

**I-R1/I-R2 (lookup-path rejection + family) — HOLD.** All five member bodies
byte-identical (relations.py, plans.py, querysets.py resolver region, and
connection.py MATCH/unchanged); both exclusions rest on unchanged bodies
(utils/permissions.py MATCH, filters/base.py unchanged); neither trigger met
(no accessor fallback/non-raising mode in `classify_path`, both literal-`"__"`
sites identical). The family row, owner, and contract difference stand.

**I-R3 (Manager-coercion file-local row) — HOLDS.** Population evidence
re-derived: `models.Manager` at exactly the 3 in-file lines above; both entry
points (`normalize_query_source` :305 arm, `_normalized_visibility_result`
:3849 arm) and the one body (`_coerced_manager_queryset` :3526) untouched. The
folder-item flag (least-margin file-local rule) is unaffected by the range.

**I-R4 (F3 population restatement) — NEEDS REVISION (one more term).** Its two
load-bearing facts re-verified mechanically at HEAD: `expected_routing` passed
at exactly 1 of 5 seal calls (:2996 post-orderset; :2535/:3444/:3743/:3851 pass
none) and `require_unevaluated=True` set only by `_ORDERSET_RESULT_POLICY`
(HEAD :2813), which reaches the seal solely through :2996; the `policy=`
calling census is complete (list_field.py:1522/:1575, walker.py:476,
permissions.py:623/:705, plus `_DEFAULT` default). The (iv) declared-subsumption
term is intact (post-orderset comment + shape map byte-identical; successor
probe still reports that site `missing: ['alias']` with `dead: []`). What is new:
with `_PREFETCH_CHILD_POLICY` in the source-policy set, the union model newly
reports `_prepared_visibility_source` as `missing: ['alias']` too (successor
probe: 2/6, both `dead: []`). That row is a pairing artifact, not a D5-class
defect: the alias arm fires iff `require_shared_alias` AND `db is not None`
(HEAD :3336-3340), the site always seals with `required_alias=None` (:3743),
and the flag-setting policy's only production pairing is the walker's unrouted
seed (`base_queryset(field.related_model)`, no `using=`) — under which alias
cannot fire. Owed: term (v) — reachability per production (policy ×
source-shape) pairing, not per-site union. The flip trigger is explicit: a
production caller pairing a `require_shared_alias` policy with a routed source
would owe that site a real `alias` arm.

**I-R5 (`SyncMisuseError` file-local row) — HOLDS.** Marker still
`(ConfigurationError, RuntimeError)` (:119, region untouched); siblings still
`(GraphQLError, DjangoStrawberryFrameworkError)` (list_field.py:248,
resource_policy.py:121 — both files' range hunks verified not to touch these
declarations). Declarations-not-definitions reasoning unchanged.

**I-R6 (`_safe_class_name` rejection) — HOLDS.** exceptions.py MATCH;
querysets.py variant region untouched; the contracted difference (repr-dispatch
vs degrade-to-metaclass-label at the sealed boundary) re-read and identical;
trigger unmet (no such change in the MATCH file).

**Enumeration completeness (I-R5's instrument) — NEEDS ONE-LINE REVISION.**
HEAD recount by the same `ast.Module.body` instrument: 102 functions / 7
classes / 24 constants = 133 names (was 134; the −1 is the retired
`_UNRECOMPOSED_CHILD_POLICY`, which carried no unique rule — same licence as
`_PREFETCH_CHILD_POLICY` minus the alias requirement — so no rule is orphaned
and the "every other name resolves" closure stands with the count updated).

### Defects

**D1 — FIXED by fd39cac6 (owned). Judged against the record, fresh:** the
defect was acceptance of a hook-routed prefetch child onto a divergent
connection. The fix seals the walker child under `_PREFETCH_CHILD_POLICY`
(walker.py:476, import :17), so any explicit `.using()` fails closed with
`('alias', <alias>)` — measured live by my successor probe — while an unrouted
child seals with `_db None` and inherits the parent's connection at fetch.
This matches the sibling rule the record cites (consumer `Prefetch` under an
unrouted parent meets the same policy with the same `None` outer alias in
`_sealed_prefetch_related_lookups`, re-read). Threading `None` rather than the
parent's alias, contra D1's prescription sentence, is correct against unchanged
architecture: `optimizer/extension.py::_get_or_build_plan` serves cached plans
from the cross-request instance `_plan_cache` (HEAD :1254-1336, file unchanged
in range), so a baked-in per-parent alias would be served to the next request
on another connection — the same-alias pin MUST refuse, and probe row A/E of
the run-1 D1 verification (read as history) showed exactly that. The fix's 5
live tests are present at HEAD (2 in test_products_visibility_api.py + 3 in
test_multi_db.py, counted from `git show HEAD:`); walker.py is touched by
fd39cac6 alone in range, so the verified bytes are the HEAD bytes. D-W2-b is
untouched by the fix (same `reject_sliced=False` licence as before).

**D2 — FIXED.** Glossary *Prefetch alias threading* (HEAD :1558) now reads
`` `reject_sliced=False` in `_PREFETCH_CHILD_POLICY` `` (dfb95984); spec-034's
live pin now reads `policy=_PREFETCH_CHILD_POLICY` (4d9f1c3d hunk verified).
`allow_sliced` occurs zero times in the package + glossary at HEAD; remaining
tree hits are archived-cycle prose (spec-003/spec-009/spec-045 + rationales,
build records, this artifact's own history) covered by D2's historical carve-out,
plus Django's unrelated `allow_sliced_subqueries_with_in` setting name (2 hits).

**D3 — HOLDS OPEN, still routed to the maintainer.** Connection side byte-identical
(:1828/:1865 still invoke `OrderSet.apply_*` with no snapshot/re-seal —
inferred from MATCH, not re-read); list-field side same shape (freeze
:1369/:1397, re-seal :1377/:1411, both colorings); the `require_unevaluated`
prose still scopes itself to the list field (HEAD :2760-2771, carry bullet
appended after it, original sentences identical). The f7192bfb carry axis does
not touch the ambiguity (raw-list policy only; connection path identical).

**D4 — FIXED by 5741eaa6.** The `(never `.all().using(alias)`)` clause is gone
(HEAD :256-260); the body is identical (`manager.using(using).all() if using is
not None else manager.all()`); the real reason (pass `using` at all) stays.
probe_using_order.py re-ran with byte-identical output (`default manager:
shard_b shard_b True True`), so the measurement that falsified the clause
reproduces against the tree that dropped it.

**D5 — FIXED by 5741eaa6 (all three rows + docstring).** Measured against the
new tree, not the commit message: raw-list map now exactly
type/table/untrusted (HEAD :3500-3522, `combined` arm deleted);
prepared-source map now exactly type/table/untrusted/sliced/combined/projection
(HEAD :3751+, `evaluated` + `routing` deleted); result-error map now exactly
those six + `alias` (HEAD :3625-3675); raw-list docstring now enumerates all
four switched-off codes including `combined` (HEAD :3494-3498). Successor probe
confirms `dead: []` at all six sites with both permissions sites still OK
(positive control intact) and the negative control intact (raw-list reaches
exactly type/table/untrusted). The `fail_under = 100` blind-spot note stands as
the reason the arms died silently.

**D-W2-a — FIXED by 4d9f1c3d.** Constant deleted (zero `.py` hits HEAD-wide);
both runner docstrings name `_PREFETCH_CHILD_POLICY` (HEAD :3901-3904,
:4154-4156, re-read); the seal-policy test's dead row deleted and the import
dropped (hunk verified). The delete-option the defect offered is what landed.

**D-W2-b — HOLDS OPEN (non-blocking, as written).** The `reject_sliced` bullet
premise ("the optimizer walker's nested-connection child, whose own gate
degrades…", HEAD :2740-2748) is identical; gate consultation still exactly the
three nested-connection paths (lateral_fetch.py:599, nested_planner.py:1239,
single_parent_fetch.py:232 — all files unchanged) and never the plain planned
list relation; the walker comment carries the same justification (:450-460).
Pre-existing wording/guard-scope row, not a D1 regression — unchanged.

### Probes

- `dry-file-utils__querysets/probe_alias_policy.py`: NO LONGER RUNS
  (`ImportError: _UNRECOMPOSED_CHILD_POLICY`, exit 1) — itself adjudication
  evidence for F8/D1: the accepting policy it measured no longer exists.
  Successor `dry-adjud-querysets-w2-r2/probe_alias_policy_r2.py` (read-only,
  zero SQL): exit 0 — `_DEFAULT_SEAL_POLICY: defect=None sealed_db='shard_b'`,
  `_PREFETCH_CHILD_POLICY: defect=('alias', 'shard_b')`, unrouted-under-prefetch
  `defect=None sealed_db=None`. Rejects "the walker child still accepts a
  routed hook result" and "an unrouted child is pinned by the seal".
- `dry-file-utils__querysets/probe_using_order.py`: RUNS, output identical to
  run-1 (`default manager: shard_b shard_b True True`, exit 0). D4's
  measurement reproduces; the clause it falsified is gone.
- `dry-file-utils__querysets-w2/probe_defect_arms.py`: NO LONGER RUNS
  (`AttributeError: _UNRECOMPOSED_CHILD_POLICY`, exit 1) — evidence for F3/I-R4:
  its hand-written `SOURCE_POLICIES` names the retired policy. Successor
  `dry-adjud-querysets-w2-r2/probe_defect_arms_r2.py` (same model + AST reader,
  `_PREFETCH_CHILD_POLICY` substituted; read-only): exit 0 — 2/6 mismatch, both
  `dead: []`: post-orderset `missing: ['alias']` (the known I-R4 subsumption
  artifact, unchanged) and prepared-source `missing: ['alias']` (new pairing
  artifact, see I-R4). Negative control intact.

### Pending execution (expectation, no verdict)

- Entry 1 (`FAKESHOP_SHARDED=1 … -k prefetch`, D1's observable half): moot as
  written — the leak it would demonstrate is fixed, and the owned fix carries
  its own sharded refusal/inheritance/routed-parent rows plus a fail-without-fix
  run that showed the leak on the reverted tree. The entry wants superseding by
  those node ids, not re-running.
- Entry 2 (focused gate run): still a valid gate request, unchanged.
- Entry 3 (arms regression witness, expects `4/6`): instrument dead (see above);
  successor shows `2/6` with both rows explained. The entry wants re-pointing at
  the successor plus the I-R4 term-(v) note before anyone reads the number.

### Census summary (all at HEAD)

Enumeration 102/7/24 = 133 names · `_SealPolicy` 6 fields / 6 constants ·
`_seal_or_defect` 5 call sites, 1 with `expected_routing` · `_defect_message` 6
sites · `policy=` pass sites list_field ×2 + walker + permissions ×2 + default ·
defect codes 9, order unchanged · message arms 8/3/6/7/5/6 across the six sites ·
F1 3 defs · F4 2 · F5 2 (+7 internal calls) · F11 1 + 5 direct · F9 0 production
readers · `models.Manager` 3 in-file sites · `is_async_only_iterable` 5
consumers (list_field ×3, resource_policy, local) · `sync_pipeline_recourse` 3
compositions · `run_in_one_sync_boundary` 6 consumer files · `allow_sliced` 0 in
package+glossary · `_UNRECOMPOSED_CHILD_POLICY` 0 in `.py` · D1 live tests 2+3
at HEAD. `FAKESHOP_SHARDED=1`/Postgres cells untouched (unauthorized), as in
run-1.

## Independent verification (Worker 2) — adjudication reconciliation (Phase B)

Read AFTER Phase A was on disk: `### Adjudication pass 1 (run 2) — Worker 1`
(artifact lines 2161–2674) and both probes in
`docs/dry/temp-tests/dry-adjud-querysets-w1-r2/`. HEAD unmoved at `bfaee91d`;
item diff vs `ITEM_BASELINE=1eb4ae4f` confirmed exactly two hunks (Status line
+ EOF append). Every difference below is reconciled explicitly; then the
verdict.

### Agreement (independently derived on both sides)

- Hunk map: identical 26 old-line ranges (51 … 4121), all inside the same three
  commits. Enumeration: 102/7/24 = 133 both sides (W1's 99+3 async split
  verified: exactly the three named `^async def` at HEAD).
- Per-item verdicts agree on all 12 findings, all 6 iterations and all 7
  defect records: F1/F4/F5/F6/F7/F9/F10/F11/F12 CONFIRM (F10 with the corrected
  3-site census both sides derived: 891/895/1387 → 1333/1337/1829); F2/F3/F8
  REVISE (6 fields, 6 constants; gate population for the D5-fixed tree; member
  now guarded); I-R1/R2/R3/R5/R6 CONFIRM; I-R4 REVISE with the same fifth
  pairing-scope term and the same flip trigger (a production caller pairing a
  `require_shared_alias` policy with a routed source owes the site an `alias`
  arm); D1 fixed-owned, D2/D4/D5/D-W2-a fixed-concurrent, D3/D-W2-b open.
- All 22 freshness hashes byte-identical to my independent hashes (18 plan rows
  + 4 I-R exclusions).
- Probes: both W1 successors re-run read-only by me with outputs identical to
  W1's record AND to my own successors' (alias: default accepts / prefetch
  rejects `('alias', 'shard_b')` / walker `policy=` keywords == exactly
  `{_PREFETCH_CHILD_POLICY}`; arms: 2/6, zero dead, same two missing-alias rows,
  negative control intact, exit 0). The AST `policy=` sweep additionally proves
  no second walker policy pass exists.
- Pending/plan notes: substance identical (entry 1 superseded by the 5 D1 node
  ids owing a both-modes gate run; entry 3 re-pointed to a successor expecting
  2/6; entry 2 unchanged). I endorse W1's two family-index rows
  (`child-queryset-alias-inheritance` → `open`; `seal-defect-code-wording`
  parenthetical refresh) for Worker 0.

### Deltas reconciled (all immaterial to the verdict)

1. F9 census wording: W1 "drifted from 16/11 by concurrent test edits" is
   wrong as drift. Measured at `5c62515a` bytes: 10 asserts / 16 lines then
   AND now (test_list_field 5 asserts, test_extension 5 asserts; only line
   numbers shifted). The files changed around the readers; the reader census
   did not drift — run-1's "16" counted lines, "11" miscounted asserts.
   Correction recorded; both sides agree the conclusion never depended on the
   count. Precise figure: 10 asserts / 16 lines, stable across the range.
2. F2 `sql.Query` sweep: W1 "0 touches outside" vs my `lateral_fetch.py:82`
   `sql.where` import note — a pattern difference, not a conflict: the import
   is pre-existing (file unchanged in range) and not a Query touch under W1's
   pattern. Agreed: no new site; my note stands as the conservative superset.
3. C13 shape: W1 "one field plus its checks" vs my "one field + one check +
   one rebuild-tail write" — agree count = 1; adopt mine as the more precise
   shape for the family record.
4. I-R4 site line: W1 :3001 (kwarg line) vs my :2996 (call line) — same call.
   No conflict.
5. D2: my `allow_sliced_subqueries_with_in` note (Django's own setting name,
   rationale prose only) supplements W1's zero-hits claim, which is scoped to
   package+glossary+spec-034 and holds. No conflict.
6. Two successor-probe pairs exist (`dry-adjud-querysets-w1-r2/` +
   `dry-adjud-querysets-w2-r2/`) with identical results. Worker 0 custody note:
   keep one pair at closeout; either discharges F8/D1 and D5/I-R4/F3.

### Verdict

`Status: verified`. No `revision-needed` item: every W1 claim I re-derived
agrees, the six deltas above are wording/precision with agreed resolutions,
both W1 instruments re-run green under my hand, and the item diff is the two
ledgered hunks. Worker 0 plan marking: keep `verified, pending execution` —
entry 1's proof is pinned to the five D1 live node ids but still owes the
gate run in both modes (sharded mode needs the maintainer's authorization); entries 2–3
are gate requests. `FAKESHOP_SHARDED=1`/Postgres cells stay `unverified` as in
run 1. No ruff/format run: `.md`-only edits; repo-wide auto-fix would rewrite
110 dirty concurrent paths (same reason W1 recorded).

### Adjudication pass 2 (run 2) — Worker 1

Adjudication run: `0.0.15 2026-09-21-2`. Adjudication-1 verified this item
at `bfaee91d`; HEAD is now `69a25369`, verified at dispatch
(`69a253690002fdd413704a7879528c3ded363020`) and again unmoved at finish.
Scoped freshness adjudication only: `bfaee91d..69a25369` holds three
test/docs commits and zero package files (`git diff --name-only ...
-- django_strawberry_framework/` prints nothing), so production bytes are
identical and only fingerprinted TEST inputs can be stale. No production
edits, no test edits, no new tracked files. Prior text above untouched;
this section appends. Pre-existing dirt attribution: vs HEAD the artifact
carries one 956-insertion / 0-deletion hunk, running from `### Adjudication
pass 1 (run 2) — Worker 1` to the Phase-B verdict tail — exactly the
adjudication-1 append the plan records (artifact lines 2161–3115). No
foreign hunk; the item was not stopped.

Method. Every claim below was verified against HEAD bytes via `git show
HEAD:<path>`, `git rev-parse HEAD:<path>` and `git grep`, never against
the working tree (which carries concurrent dirt) and never against a
commit message. The target was not re-read end to end: the worktree file
hashes to `96618fba…`, identical to the HEAD blob adjudication-1 verified,
and MATCH inputs need no re-review under the same rule reconciliation 1
applied. Target regions the probe model rests on (the `_SealPolicy`
record, the seal's emit guards, the six arm shapes) were re-read at HEAD
bytes to encode the successor instrument.

#### Adjudication pass 2 (run 2) — fingerprints: 21 MATCH, 1 STALE

All 22 adjudication-1 fingerprints re-hashed via `git rev-parse
HEAD:<path>`. Twenty-one are byte-identical to the recorded values
(querysets `96618fba…`, auth/mutations `dbe64995…`, routers `a18c5001…`,
permissions `757dce34…`, connection `93e998f2…`, nested_fetch `4d8d37a7…`,
types/resolvers `f3341e6a…`, write_values `d28587c7…`,
rest_framework/resolvers `8024703e…`, write_transaction `eca9ad4d…`,
mutations/permissions `54f770ae…`, utils/permissions `9889d6fe…`, walker
`9b111ed9…`, filters/sets `4ab65a26…`, GLOSSARY `bc51debc…`, list_field
`ce682d5f…`, resource_policy `647133d2…`, relations `7662b0bb…`, plans
`cce98531…`, exceptions `e06b0b7f…`, filters/base `ba52351c…`). Exactly
one is stale:

`tests/utils/test_querysets.py`: `977a81df44b5cede99b2be9b8dcc5be76db0f03a`
→ `6ce0bbc128f0febcbfb8a4837a2c169125d4d997` (landed clean; the worktree
file hashes to the same blob). The stale set is exactly that one file —
no other mismatch, so no finding reopens beyond the claims that cite it.

#### Adjudication pass 2 (run 2) — the causing range (4 hunks, one commit)

`git log bfaee91d..69a25369 -- tests/utils/test_querysets.py` names exactly
one commit: `a01a2ab8 test: move the request-observable rows live and pin
the cost each one claims`. Its diff on this file is 48 insertions / 18
deletions in 4 hunks: (H1) module-docstring reword — the contract paragraph
and the `coerce_field_value_or_none` paragraph replaced by live-tier
pointers; (H2) four added imports (`seed_data`, `Apps`, `connection`,
`CaptureQueriesContext`); (H3) `_proxy_target_apps = Apps([])` plus
`apps = _proxy_target_apps` on the two proxy-target fixture models;
(H4) two new tests (`test_proxy_target_fixtures_leave_category_relations_unchanged`,
`test_proxy_target_fixtures_allow_category_deletion`) asserting only
`Category._meta` registry facts and deletion-SQL facts. Net effect on
later line numbers is +30 (5882 → 5912 lines; `def test_` count 313 → 315).

#### Adjudication pass 2 (run 2) — F2 (CONFIRM; fingerprint refreshed)

Oracle role intact. The three named inventory-oracle tests adjudication-1
cited (`:5033, :5055, :5082`) exist at HEAD with byte-identical bodies at
`:5063, :5085, :5112` (`test_unrendered_defect_code_says_so_instead_of_mislabelling`,
`test_every_admitted_plain_container_has_a_rebuild_branch`,
`test_bound_value_normalizers_mirror_the_inert_inventory` — the +30 shift
is exactly the hunk net, verified by name). Both principle-9
set-equality assertions are verbatim (`assert set(samples) ==
set(_PLAIN_CONTAINER_TYPES)` at :5103; `assert set(_INERT_VALUE_TYPES) -
{bool} == …` at :5123). No oracle was rewritten to read from its owner:
H1/H2 add no oracle, H3 touches fixture registration only, and H4's two
tests assert `Category` registry/deletion facts without importing any
seal, coercion or policy symbol. Hunk-by-hunk unrelatedness: H1 is
projection prose (cites live tiers, removes no contract); H2 supports H4
only; H3/H4 are fixture hygiene whose assertions never name the module
under review. Run-1's scene-setting "5760 lines, 309 tests" is history,
not a live claim (the `def test_` count reproduces at neither endpoint —
313 before, 315 after — so no verdict ever depended on 309); refreshed
figures are 5912 lines / 315 def-tests. Conclusion (one owner) and
definition counts unchanged. Fingerprint refreshed to `6ce0bbc1…` (full
row under "freshness" below).

#### Adjudication pass 2 (run 2) — every other claim citing the file (CONFIRM)

- F3's legibility pin (`test_unrendered_defect_code_…`, run-1 line 301):
  byte-identical at HEAD :5063, outside all hunks. The file is not in F3's
  fingerprint set, so the landing reopens nothing; the citation stands.
- Matrix axis 3 (the two inventory-agreement gates): both tests and both
  quoted assertions verbatim at HEAD (:5085/:5112, :5103/:5123). CONFIRM.
- F12 `_safe_routing_repr` readers: the test file still reads it (2 hits
  at HEAD); the hunks add tests, never remove a reader. CONFIRM.
- Matrix axis 5 / W2-trace media counts: history (see F2 for refreshed
  figures); the file's oracle-medium role is unchanged. CONFIRM.
- D1-fix history cites (the dirty-at-dispatch notes, the `:4956`
  `_UNRECOMPOSED_CHILD_POLICY` reader): history. D-W2-a's holding
  re-verified: zero hits for the retired constant in the file at HEAD.
  No live claim affected. CONFIRM.
- I-R1 (the `02e266df` tier-move note): about a prior commit, untouched
  by this range. H3 isolates the same proxy-target fixtures with
  `apps=` — fixture REGISTRATION, not resolver behavior; the production
  fail-open-vs-raise contract (byte-identical file) and both
  reconsideration triggers are untriggered. CONFIRM.
- All remaining findings and iterations (F1/F4/F5/F6/F7/F8/F9/F10/F11,
  F12's other rows, I-R2/R3/R4/R5/R6, D1–D5, D-W2-a/b): every input they
  fingerprint is MATCH, and none cites the stale file outside already-
  covered history. No re-review owed — the reconciliation-1 rule
  (MATCH-only needs no re-review), applied again.

#### Adjudication pass 2 (run 2) — freshness, refreshed to HEAD 69a25369

F2 is the only finding fingerprinting the stale file. Its refreshed row:

```text
tests/utils/test_querysets.py                     6ce0bbc128f0febcbfb8a4837a2c169125d4d997
```

The other 21 rows stand as adjudication-1 recorded them (values listed
under "fingerprints" above). No run-1 line was edited.

#### Adjudication pass 2 (run 2) — `## Pending execution` (entries 1–2 CONFIRM, 3 REVISED)

Entries 1–3 above stand as run-1/adjudication-1 history; state now:

1. Entry 1 (superseded by the five D1 live node ids): CONFIRM. All five
   resolve at HEAD (visibility :890/:914, multi_db :1514/:1539/:1556)
   with byte-identical bodies — the landed visibility diff is +262/−1
   with the lone deletion a module-docstring line, and `test_multi_db.py`
   is untouched in range. The both-modes gate run is still owed, and the
   sharded mode still needs the maintainer's word.
2. Entry 2 (focused gate run over the three oracle suites): CONFIRM
   unchanged. All three paths resolve at HEAD. The F9-exercise
   expectation is intact: `is_async_queryset_adapter` still reads 7 + 9
   = 16 lines across the two suites, exactly adjudication-1's
   reconciled census (those files are not fingerprinted, so their
   landing is gate-watch, never a trigger).
3. Entry 3 (arms witness, re-pointed at a successor expecting 2/6):
   REVISE the pointer, CONFIRM the expectation by re-derivation. Both
   adjudication-1 successor scopes are gone (relocation), and the run-1
   originals are gone with them — the `dry-file-utils__querysets[-w2]`
   scopes now hold differently-named September-18 files, which were
   left untouched and unopened. Nothing was trusted from the record
   alone: the successor below re-derives the census from HEAD bytes.

Successor probe (fresh scope, adjudication-2):
`docs/dry/temp-tests/dry-adjud2-querysets-w1/probe_defect_arms_adjud2.py`
— `uv run python` it. Pure AST over `git show HEAD:` bytes (no Django
import, zero SQL, read-only); it asserts the four input blobs
(querysets `96618fba…`, permissions `757dce34…`, walker `9b111ed9…`,
list_field `ce682d5f…`), re-verifies both I-R4 load-bearing facts
(expected_routing at exactly 1 of 5 seal calls; the walker /
permissions / list_field `policy=` edges plus runner defaults
flag-equal to `_DEFAULT_SEAL_POLICY`), reads all six arm sets from the
AST (dict-literal plus the orderset `dict.fromkeys` shape), and keeps
the negative control (raw-list reaches exactly type/table/untrusted).
Output at HEAD: `sites with a mismatch: 2/6`, zero dead arms anywhere,
arms 8/3/6/7/5/6 — the orderset-alias subsumption and the
source-alias pairing artifact, negative control intact, exit 0. That
reproduces adjudication-1's record digit for digit from independent
bytes. `execution-verified` (re-derived-by-adjudication-2-W1). The
gate should run this path and expect `2/6`; the two dead r2 paths stay
dead. `uv run ruff check` + `ruff format --check` both pass scoped to
the fresh scope dir.

#### Adjudication pass 2 (run 2) — family index and ledger (nothing owed)

Test-only change; every production input MATCH; every oracle intact and
no definition count moved. All thirteen querysets family rows stand as
adjudication-1 left them (W2-endorsed). No index-row change and no
`## Owned changes` row is owed to Worker 0 — this pass lands no
production edit, no test edit, and no tracked file besides this
artifact's own append.

#### Adjudication pass 2 (run 2) — item state

Zero production edits, zero test edits, zero new tracked files. Untracked
scratch created, all inside the fresh scope (other scopes untouched):
`docs/dry/temp-tests/dry-adjud2-querysets-w1/probe_defect_arms_adjud2.py`.
Item-scoped diff vs `ITEM_BASELINE=ebaa77237e42da28d5395bcb73292dd9a56d3ff5`
covers only this artifact's append plus the `Status:` line (verified
before finishing; the pre-existing dirt is the attributed adjudication-1
append, and the probe scope is the authorized fresh scope).
`uv run ruff check` / `ruff format --check` pass on the scope dir; no
ruff on the `.md` artifact. The one authorized focused shared-tree pytest
was not spent — every claim here is decided by HEAD-byte inspection plus
the read-only AST probe. `FAKESHOP_SHARDED=1` and Postgres cells stay
`unverified`. Concurrent dirt (package, tests, docs) left alone.

## Independent verification (Worker 2) — adjudication-2

Two-phase per the dispatch. Phase A (below, as recorded pre-read in
`docs/dry/temp-tests/dry-adjud2-querysets-w2/phase_a_expectations.md`) was
written BEFORE opening `### Adjudication pass 2 (run 2) — Worker 1`
(artifact lines 3117–3303) and before opening
`docs/dry/temp-tests/dry-adjud2-querysets-w1/`. Reconciliation + verdict
follow it.

### Phase A — expectations (recorded blind)

Start HEAD: `69a253690002fdd413704a7879528c3ded363020` (recorded before any
read). `ITEM_BASELINE=ebaa77237e42da28d5395bcb73292dd9a56d3ff5` resolves
(`commit`). Scope `docs/dry/temp-tests/dry-adjud2-querysets-w2/` verified
absent, then created by me. Method: HEAD-pinned bytes only — `git rev-parse
HEAD:<path>`, `git show <commit>:<path>`, `git grep -n <symbol> <commit>`,
`git diff <commit>..<commit>`. No execution: every Phase-A claim is static
(hashes, diffs, greps), so no probe and no workspace was needed, and no
execution-backed claim from the (relocated, unreplayable) run-2 scopes is
relied on. Never imported `management/commands/inspect_django_type`.
Working tree at Phase-A time: target and `tests/utils/test_querysets.py`
both clean; only the artifact is dirty (W1's append, unread).

22-hash re-verification at HEAD: 21 MATCH
(`utils/querysets.py 96618fba…`, `auth/mutations.py dbe64995…`, `routers.py
a18c5001…`, `permissions.py 757dce34…`, `connection.py 93e998f2…`,
`optimizer/nested_fetch.py 4d8d37a7…`, `types/resolvers.py f3341e6a…`,
`utils/write_values.py d28587c7…`, `rest_framework/resolvers.py 8024703e…`,
`utils/write_transaction.py eca9ad4d…`, `mutations/permissions.py 54f770ae…`,
`utils/permissions.py 9889d6fe…`, `optimizer/walker.py 9b111ed9…`,
`filters/sets.py 4ab65a26…`, `docs/GLOSSARY.md bc51debc…`, `list_field.py
ce682d5f…`, `resource_policy.py 647133d2…`, `utils/relations.py 7662b0bb…`,
`optimizer/plans.py cce98531…`, `exceptions.py e06b0b7f…`, `filters/base.py
ba52351c…` — each re-hashed by me to the full recorded blob), 1 STALE:
`tests/utils/test_querysets.py`
`977a81df44b5cede99b2be9b8dcc5be76db0f03a` →
`6ce0bbc128f0febcbfb8a4837a2c169125d4d997`. Exactly the plan's
Freshness-reconciliation-2 row. Expected hash action: refresh exactly that
row; re-affirm the other 21.

Causing range: exactly one commit (`git log
bfaee91d..69a25369 -- tests/utils/test_querysets.py`), `a01a2ab8 test: move
the request-observable rows live and pin the cost each one claims` (44
files, all docs/examples/tests, zero package files). In
`tests/utils/test_querysets.py` exactly 4 hunks, 48+/18- = net +30 (5882 →
5912 lines). Added/removed `def test_` scan: 2 added, 0 removed, 0 renamed;
no class added or removed.

- Hunk 1 (`@@ -1,25 +1,16 @@`, docstring reword, net −9): replaces the
  contract paragraph + the `coerce_field_value_or_none` paragraph with
  live-tier pointers. Could touch F2's oracle role and the Matrix axis-5 /
  W2-trace media description — but the docstring is test-file prose, not an
  artifact claim, and the oracle role rests on test BODIES (the set-equality
  assertions), untouched. Expected: **CONFIRM**. Note (not a demand): the
  artifact's "5760 lines, 309 tests" is now 5912 lines / 315 `^def test_`
  defs by my count — but it was ALREADY stale at `bfaee91d` (5882/313) and
  adjudication-1 set precedent by leaving run-1 history untouched while
  re-pinning only the oracle-test lines. Expected W1 to follow that
  precedent; a revision of run-1 prose would contradict DRY.md.
- Hunk 2 (`@@ -32,11 +23,14 @@`, imports, net +3): adds `seed_data`,
  `Apps`, `connection`, `CaptureQueriesContext`. Pure support for hunk 4;
  touches nothing recorded. Expected: **CONFIRM**.
- Hunk 3 (`@@ -4688,12 +4682,16 @@`, `_proxy_target_apps` + proxy Meta,
  net +4): fixture-registration isolation for the proxy-prefetch tests.
  Neighboring test bodies are context-only. Could touch I-R1 (fail-open
  tail) and F8/F2 (child-seal assertions) — but the production contract
  (MATCH bytes) and both I-R1 triggers (`classify_path`, `relations.py`
  MATCH) are untouched. Expected: **CONFIRM**.
- Hunk 4 (`@@ -4716,6 +4714,38 @@`, holder Meta + 2 new tests, net +32):
  `test_proxy_target_fixtures_leave_category_relations_unchanged` and
  `test_proxy_target_fixtures_allow_category_deletion` assert
  Django-registry/fixture facts, not expectations about any package rule —
  not oracles of a finding; no definition count moves; oracle independence
  unaffected. Expected: **CONFIRM**.

Cross-cutting expectations. F2: owner/exclusivity/5-call-sites/9-codes rest
on MATCH bytes → **CONFIRM**; the three oracle tests exist by name at HEAD
with byte-identical bodies (all hunks end ~4751), shifted exactly +30 to
`:5063` / `:5085` / `:5112` (verified via `git grep` at both commits);
expected W1 to CONFIRM F2, refresh the hash to `6ce0bbc1…`, and re-pin the
three oracle lines. F3: cited by `::name`, stable → **CONFIRM**, no
revision. F1/F4/F5/F6/F7/F8/F9/F10/F11/F12, I-R1..I-R6, D1..D5, D-W2-a/b:
all inputs MATCH, no hunk names their symbols → expected W1 CONFIRMs each;
my spot re-derivations: F9 still 0 production readers with test-reader
lines 9 + 7 = 16 IDENTICAL at both commits (the `test_extension.py` churn
never touched them — out of scope regardless per the plan's basename
sweep); F12 `_safe_routing_repr` production reader still only the seal's
routing arm (`:3225-3228`), test readers still the same two files; I-R1
triggers untriggered. Pending entries: 1 still owes the both-modes gate on
the five D1 node ids (D1 live-file landing is gate-watch, not this
adjudication); 2 still valid (file exists, +2 tests); 3 still `gate:`-typed
(the successor path dangles post-relocation — Worker-0 custody, not a
typing change). Expected all three statuses unchanged, no re-typing.
Family rows / ledger: no production edit possible → expected W1 names no
index change, no ledger row, no new family. Verdict expectation: `verified`
(keeping `verified, pending execution`) with the one hash refreshed; any
`revision-needed` would have to name a concrete moved claim, and I found
none.

### Phase B — reconciliation (every difference, explicitly)

Read AFTER Phase A was on disk: `### Adjudication pass 2 (run 2) —
Worker 1` (lines 3117–3303) and
`docs/dry/temp-tests/dry-adjud2-querysets-w1/probe_defect_arms_adjud2.py`
(read-only; then re-run read-only).

Agreement (independently derived on both sides): 22-hash table identical
(21 MATCH full blobs + the one stale row with the same before/after blobs);
causing range identical (one commit `a01a2ab8`, 4 hunks, 48+/18-, H1–H4
characters, net +30, 5882→5912 lines, 313→315 def-tests); F2 CONFIRM with
the hash refreshed to `6ce0bbc1…` and the three oracle lines re-pinned to
`:5063/:5085/:5112` with byte-identical bodies; "5760/309 is run-1 history"
with the same precedent reasoning AND the same refreshed figures (5912/315,
313 before); F3 + Matrix axis 3 + F12 readers + axis-5 media role + D1-fix
history + I-R1 all CONFIRM with matching reasons (fixture REGISTRATION vs
resolver behavior; `::name` citations stable); all remaining findings and
iterations CONFIRM via the MATCH-only rule; family index + ledger: nothing
owed. W1's extra pins (set-equality assertions verbatim at `:5103/:5123`,
`_safe_routing_repr` 2 hits in the file, zero retired-constant hits) all
re-verified by me via `git grep` at `69a25369` — each matches.

Deltas reconciled (three, none verdict-affecting):

1. Entry 3: I expected "status unchanged"; W1 REVISED the pointer while
   CONFIRMing the type (`gate:`) and expectation (`2/6`). The revision was
   owed, not scope creep: both adjudication-1 successor paths are dead
   (relocation — confirmed: neither `dry-adjud-querysets-*-r2` scope exists,
   and the `dry-file-utils__querysets[-w2]` scopes now hold
   differently-named September-18 files, verified by names only, unopened),
   so the entry-3 command pointed at nothing. W1 re-derived rather than
   trusted: `probe_defect_arms_adjud2.py` is pure AST over `git show HEAD:`
   bytes (no Django import, zero SQL), asserts the four input blobs
   (`96618fba…`/`757dce34…`/`9b111ed9…`/`ce682d5f…` — all matching my hash
   table), re-verifies both I-R4 load-bearing facts (routing at exactly 1
   of 5 seal calls; walker/permissions/list_field `policy=` edges plus
   runner defaults flag-equal to default), reads all six arm sets from the
   AST (dict-literal plus the orderset `dict.fromkeys` shape), and keeps
   the negative control. I re-ran it read-only: output identical to W1's
   record (`sites with a mismatch: 2/6`, zero dead arms, arms 8/3/6/7/5/6,
   same two missing-alias rows, negative control intact, exit 0), and
   `uv run ruff check` + `ruff format --check` both pass scoped to W1's
   scope dir. The `_django_patches` precedent (superseded replay command,
   re-derived endorsement) covers exactly this shape. Endorsed:
   entry 3 is `gate:` + live path + `2/6`, `execution-verified
   (re-derived-by-adjudication-2-W1)`, doubly derived (W1 + my re-run).
2. Entry 1: I expected "status unchanged / gate-watch"; W1 additionally
   re-verified the five D1 node ids resolve at HEAD
   (`:890/:914/:1514/:1539/:1556`) with byte-identical bodies, the
   visibility diff at +262/−1 with the lone deletion a module-docstring
   line, and `test_multi_db.py` untouched in range. Stronger evidence,
   same verdict (both-modes gate still owed, sharded needs the maintainer's word). I
   verified each sub-claim: the five `def` lines resolve as cited, the two
   visibility hunks sit at docstring + old-line 326 (neither touches the
   D1 bodies), the deletion extends a docstring sentence, and multi_db has
   no numstat row. No gap — W1's confirmation subsumes my expectation.
3. Entry 2: identical verdict (CONFIRM unchanged); W1's F9-exercise census
   (7 + 9 = 16 lines) matches my independent re-census line for line, and
   W1's "not fingerprinted → gate-watch" matches my out-of-scope reading.
   No difference at all; recorded for completeness.

Verification job. Item-diff scope: `git diff
ebaa77237e42da28d5395bcb73292dd9a56d3ff5 -- <artifact>` is exactly two
hunks — the `Status:` swap (the diff's sole deletion line) plus a purely
additive 188-line EOF append (W1's record, read in full); prior text
untouched, no foreign hunk. Corroboration vs HEAD: 1145+/1- = 956
(attributed adjudication-1 append) + 188 (W1) + Status — exact. HEAD
tripwire: `69a25369` at my start, mid-phase, and finish (recorded below) —
unmoved throughout. AGENTS.md prose rules on the diff: no process
provenance beyond the DRY.md-mandated role label in W1's own section
header; citations in the adjudication-1-precedent form (raw `path:NN`
allowed in `docs/dry/dry-*.md`, bare in-target symbol names with the
artifact's subject file implicit); no tests added (the probe is untracked
scratch at the DRY.md-mandated location); no cross-file links, so no link
block owed; no CHANGELOG, no commit. Pending-execution typing: entry 1
still the pinned `proof:` (five node ids, both-modes gate owed), entries
2–3 `gate:` — types unchanged, commands live. Test authorization: one
read-only W1-probe re-run (above); no pytest spent; no workspace built
(nothing mutates source); `inspect_django_type` never imported.
Sharded/Postgres cells stay `unverified` as typed. No ruff on the `.md`
artifact (precedent: `.md`-only edits; my scope holds no `.py`).

### Verdict

`Status: verified`. Every W1 claim re-derived by me agrees; the three
deltas are a re-pointing endorsement (entry 3), a subsuming confirmation
(entry 1), and a non-difference (entry 2). Worker 0 plan marking: keep
`verified, pending execution` — entry 1's proof still owes the gate run in
both modes (sharded mode needs the maintainer's authorization); entries 2–3 are gate
requests (entry 3 at the new live path expecting `2/6`). No family-row,
ledger, or pending-entry change is owed to Worker 0 beyond that marking.
Finish HEAD: `69a253690002fdd413704a7879528c3ded363020`, unmoved.

### Adjudication pass 3 (run 3) — Worker 1

Adjudication run: `0.0.15 2026-09-21-3`. Adjudication-2 verified this item
at `69a25369`; HEAD is now `24e6b4d3` (`24e6b4d3e74b104779225cd6bbff713880bc48e3`,
verified at dispatch and again unmoved at finish). Scoped freshness
adjudication only, over the plan's 7 stale inputs of 22. No production
edits, no test edits, no new tracked files. Prior text above untouched;
this section appends. Pre-existing dirt attribution: vs HEAD the artifact
carries one 1336-insertion / 0-deletion hunk — exactly the plan-recorded
adjudication-1+2 appends. No foreign hunk; the item was not stopped.
`ITEM_BASELINE=101a8d752b5a324021ffe0b923cf49270a7588c6` resolves.

Method. All eleven causing commits were read as diffs, never as messages;
only five touch a fingerprinted input (`fee87ac4` target/list_field/connection,
`44712901` target/walker/glossary/tests, `c87f4f98` target/connection,
`9350eb8d` resource_policy/glossary, `24e6b4d3` tests — each verified via
`git log --oneline 69a25369..24e6b4d3 -- <path>`). The other six touch no
fingerprinted input (`9fb725c8` tests/test_connection.py only, `3c53842f`
live async rows + docs, `1f68871a` + fee87ac4's 8 lines on
tests/test_list_field.py covered as a mention-check, `fa6d48f8` spec-034
:444 + rationale :193 covered as a mention-check, `357e5487` KANBAN only,
`ec0d21de` records + the artifact citation fix itself, which HEAD bytes
carry as the record). Every claim below was verified against HEAD bytes
via `git show HEAD:<path>`, `git rev-parse HEAD:<path>` and `git grep`,
never against the working tree and never against a commit message.

Target hunk map `69a25369..24e6b4d3` (10 hunks; old-line starts 2404, 2525,
2742, 2796, 2979, 2997, 3041, 3136, 3898, 4152). Seven hunks are prose-only
(docstring/comment; the identity probe proves executable-identity, see
below). The executable inventory of the whole range is exactly: 7 new
functions (`require_orderset_class`, `_apply_sidecar_sync/_async`,
`apply_orderset_sync/_async`, `apply_filterset_sync/_async`), 1 new
constant (`_LIST_RELATION_CHILD_POLICY`), 1 rename
(`_ORDERSET_RESULT_POLICY` → `_SIDECAR_RESULT_POLICY`, def + its one use).
Everything above old :2404 is byte-identical, so every cite below it keeps
its line.

Enumeration recount at HEAD (`ast.Module.body`, identity probe): 103 sync +
6 async = 109 functions, 7 classes, 25 constants = 141 names (was 133; +7
functions — 4 sync, 3 async — and +1 constant; the rename is count-neutral).
New-name homes for the I-R5 closure (no rule orphaned): the seven sidecar
functions → family `post-set-apply-result-validation` (the one seal body
plus its thin entries; `fee87ac4`/`c87f4f98` landed the family's
centralization concurrently — the family item verifies, it does not redo);
`_LIST_RELATION_CHILD_POLICY` → `sealed-execution-queryset` (F2 census) and
`child-queryset-alias-inheritance` (F8); `_SIDECAR_RESULT_POLICY` inherits
every home `_ORDERSET_RESULT_POLICY` had (F2/F3/I-R4/D3).

#### Adjudication pass 3 (run 3) — F1 (CONFIRM)

Count stays 3. `auth/mutations.py` and `routers.py` are byte-identical
(MATCH), and the disposal region (:160-230) sits above the first target
hunk. The new `_apply_sidecar_sync/_async` consume `_dispose_sync_awaitable`
by name — two more in-file consumers, not definitions — and the
`ec0d21de`-fixed consumer citation (`apply_orderset_sync/_async`) reads
correctly at HEAD. The second-axis challenge forces the same 3. Family
`awaitable-refusal-and-disposal` unchanged.

#### Adjudication pass 3 (run 3) — F2 (REVISE: counts and pins only)

Still one owner. Exclusivity re-derived at HEAD: `models.QuerySet(`
outside the target = 0 hits; `sql.Query` touches outside = only the
pre-existing `lateral_fetch.py:82` import (file unchanged in range — the
adjudication-1 delta-2 note stands); executable `object.__getattribute__` /
`type.__getattribute__` / `inspect.getattr_static` outside = 0 (the one
textual hit stays the pre-existing `converters.py:119` comment, file
unchanged). `_seal_or_defect` still has exactly 5 call sites, all in-file
(:2548, :3033, :3662, :3961, :4069; def :3260), with zero callers
package-wide outside. The four planning readers are intact:
`connection.py:1610` (was :1603, +7 import shift, same
`source.query.is_sliced` read), `nested_fetch.py` 123/131/197,
`predicates.py:165`, `extension.py:1161` (all three files unchanged in
range). The defect-code set is still the same closed 9 in the same order
(:3272-3274). What moves is the record's own census, as in adjudication-1:
"the six policy constants" is now SEVEN (`_LIST_RELATION_CHILD_POLICY`
added at :2835, `_SIDECAR_RESULT_POLICY` renamed at :2846 with identical
flags — proven by the identity probe); `_SealPolicy` stays 6 fields. C13
still forces 1 — the new child policy arrived as one constant differing on
one axis, the worked-example shape. The three inventory-oracle tests exist
with byte-identical bodies at :5076/:5098/:5125 (identity probe
compares source segments at both commits; both principle-9 assertions
verbatim at :5116/:5136). The *Sealed execution queryset* glossary
projection (:1889) is untouched in range. Family `sealed-execution-queryset`
unchanged.

#### Adjudication pass 3 (run 3) — F3 (CONFIRM, re-pinned; population in I-R4)

`_defect_message` still has exactly 6 call sites (`permissions.py:353`,
`:412`, unchanged lines; target :3077, :3718, :3843, :3969) and the
dispatcher itself (:3794) is executable-identical modulo nothing (outside
all code hunks). `c87f4f98` rewords only the validator docstring
(FilterSet-or-OrderSet wording) and the policy identifier; it changes no
code set and no arm set — the arms probe re-derives 8/3/6/7/5/6 with zero
dead arms. The rule F3 gates still holds at every site modulo the same two
documented modelling artifacts (see I-R4). Finding stays
gate-plus-declaration in family `seal-defect-code-wording`.

#### Adjudication pass 3 (run 3) — F4 (CONFIRM)

Count stays 2. The guard `connection.py::_guard_source_not_pre_sliced` is
byte-identical at :1609-1632 (was :1602-1625; endpoint bytes verified
equal), the seal's `sliced` arm is untouched code (:3547; the :3136 hunk is
docstring-only, proven by the identity probe), and `nested_fetch.py` is
MATCH including the contract difference. `_LIST_RELATION_CHILD_POLICY`
keeps `reject_sliced` at its default — a consumer of the policy field,
never a third definition (the same licence adjudication-1 applied to the
retired constant). `44712901`'s licence narrowing is what D-W2-b becomes
(see there). The family item's open question and the `GraphQLError` vs
`ConfigurationError` proof it owes are unchanged.

#### Adjudication pass 3 (run 3) — F5 (CONFIRM)

Count stays 2, site lists unchanged. `types/resolvers.py`,
`utils/write_values.py`, `rest_framework/resolvers.py` are all MATCH, so
`_visible_related_object` (:395), its 7 call sites, and the
`write_values.py:226` consumer are byte-identical. Target re-pins:
`related_visibility_queryset_or_default` :4211, `visible_related_object`
:4280 (both +220, bodies untouched — the range adds no hunk in their
spans). The disprove-first question the family item owes is untouched by
every causing commit.

#### Adjudication pass 3 (run 3) — F6 (CONFIRM)

Rejection stands. `coerce_field_value_or_none` (310-344) is above the first
hunk, byte-identical; `_stringified` re-pins to :4232 with
`stringified_pks_present` :4242 / `pks_all_present` :4266 (bodies
untouched). `utils/write_transaction.py`, `utils/write_values.py`,
`rest_framework/resolvers.py` are MATCH. The reconsideration trigger is
untriggered: production callers are still only `visible_related_objects`
(in-file :4346) and `write_values.py:313` (MATCH file, same
`type_check_relation_id` routing). `keyset.py:384` is untouched in range
(file absent from the range log). Contract difference byte-identical.

#### Adjudication pass 3 (run 3) — F7 (CONFIRM)

Rejection stands. `sync_pipeline_recourse` and `_RELAY_ASYNC_RECOURSE`
(347-372) are above the first hunk; `mutations/permissions.py`,
`utils/permissions.py`, `permissions.py` are MATCH (`_PERMISSION_ASYNC_RECOURSE`
:50, `_GATE_ASYNC_RECOURSE` :59, `_ASYNC_RECOURSE` :136, same lines). The
three `sync_pipeline_recourse` compositions sit in unchanged files
(`mutations/resolvers.py:139`, `forms/resolvers.py:125`,
`rest_framework/resolvers.py:201` — all absent from the range log).
Reconsideration trigger untriggered.

#### Adjudication pass 3 (run 3) — F8 (REVISE: guarded under two child seals)

The two enforcement mechanisms are still 2 definitions, correctly counted:
`base_queryset`'s `using` arm (body AST-identical, see the identity probe)
and the seal's `require_shared_alias` arm (AST-identical at :3555-3560).
Enforcement sites `permissions.py:692` and `filters/sets.py:2592` are in
MATCH files, and `_sealed_prefetch_related_lookups` still threads the outer
effective alias into the child seal (call at :2548 with `required_alias`
and `_PREFETCH_CHILD_POLICY`; both hunks in that function are prose-only).
What changed is the "one policy" line adjudication-1 recorded: the walker
now seals under TWO child policies — `_LIST_RELATION_CHILD_POLICY` (the
builder default, :420) and `_PREFETCH_CHILD_POLICY` (the
`_build_connection_child_queryset` seam, :525, wired at :1619) — which the
arms probe proves differ on `reject_sliced` and on nothing else, with
`require_shared_alias=True` in both. The alias verdict therefore carries:
an explicitly-routed child is still rejected under either seal by the
identical arm, the seed is still unrouted (`base_queryset(field.related_model)`
:457), and the plain-list call (:1035-1041) passes no policy, taking the
default. The glossary projection cite re-pins to the re-rendered :1558
sentence, which still names `reject_sliced=False` in
`_PREFETCH_CHILD_POLICY` and now states the `_LIST_RELATION_CHILD_POLICY`
split. Coupling to D1 stays discharged. Family
`child-queryset-alias-inheritance` still owes its family item.

#### Adjudication pass 3 (run 3) — F9 (CONFIRM)

Still no production reader. HEAD census: the definition (:412, unchanged
line) is the only package hit — zero across `django_strawberry_framework/`,
`tests/` beyond the two suites, and `examples/`; not in any `__all__`, not
re-exported. Test readers are 7 + 9 = 16 lines at BOTH commits
(`test_list_field.py` 5 asserts + 2 imports, `test_extension.py` 9 lines):
the `fee87ac4` 8-line hunk (import swap `_require_orderset_class` →
`require_orderset_class` + message re-point) and the `1f68871a` hunk
(`django_db(transaction=True)` + docstring) touch neither reader line nor
any assert. `wrap_` consumers are still `list_field.py` (import :105 + 4
call sites :1437/:1473/:1490/:1526, same shapes) and `extension.py:1145`
(MATCH file); `unwrap_` still `extension.py:1142` (MATCH). The
`resource_policy.py` diff (template/`_PACKAGE` split) adds no reader. The
principle-11 decision with its oracle-shape entailment still belongs to
family `async-only-queryset-row-adapter`.

#### Adjudication pass 3 (run 3) — F10 (CONFIRM)

Rejection stands; the contract difference is byte-identical. Connection
sites re-pin to :1057/:1102 (still answer yes for a QuerySet) and :1582
(still the union admission test) — same shapes, +7 import shift.
`is_async_only_iterable` (:375) and its local consumer (:458) are above the
first hunk. Composed consumers re-pin with identical shapes:
`list_field.py` :1332/:1336/:1751 (the same three sites, −1/−1/−78),
`resource_policy.py:1240` (was :1216, +24 from the template hunk plus the
copy hunk). `list_field.py` holds no direct `AsyncIterable`/`AsyncIterator`
reference at HEAD, and its `_safe_type_name` / `SyncMisuseError` /
`_snapshot_routing_intent` / `_validate_post_orderset_result` /
`_dispose_sync_awaitable` counts are all zero — the seal move left nothing
behind. Reconsideration trigger untriggered.

#### Adjudication pass 3 (run 3) — F11 (CONFIRM)

Still 1 definition, same classification. `run_in_one_sync_boundary` (:465)
is above the first hunk; all six consumer files still compose it by name,
and the `schema.py` cites need no re-pin (import :79, calls :346/:360/:373 —
the `9350eb8d` schema hunks are all 1-for-1 identifier swaps preserving
every line number). The five direct `sync_to_async(...)` sites are in
MATCH/unchanged files at identical lines, and the package-wide
`sync_to_async(` census is identical at both commits (10 files, same
counts), so no boundary call was added. Family `one-sync-boundary`
unchanged.

#### Adjudication pass 3 (run 3) — F12 (one row REVISED, rest CONFIRM + re-pins)

- `_safe_routing_repr`: production readers still only the seal's routing arm
  (:3443-3446, inside `_seal_or_defect`). 1 definition. CONFIRM.
- `_GraphWalk` / `_WalkState` / `_walk_short_circuit` (826-900, above the
  first hunk): byte-identical, "7 in-module callers" unchanged by
  construction; the `converters.py:119` hit is still the pre-existing
  comment. CONFIRM.
- `_snapshot_routing_intent`: REVISED — it now has ZERO external consumers.
  The two `list_field.py` call sites adjudication-1 cited were inside the
  moved `_apply_orderset_*` bodies; the calls now live in-file at :3120 and
  :3153 (the two `_apply_sidecar_*` seals), and the symbol has zero hits
  outside the target module package-wide. Still 1 definition; the row's
  consumer census is what changed.
- `_routing_hints_equal`: reader still the seal (:3437). CONFIRM.
- `_bake_deferred_filter_or_defect` + `_deferred_value_defect`: sole caller
  still the seal (:3492); `PROHIBITED_FILTER_KWARGS` still single-sited
  (import + floor mirror :101-108, one use :2673). CONFIRM.
- `prepared_resolver_source` (:4462): still composed by both collection
  flavors (`connection.py:1769`, `list_field.py:1715/:1762`, same shapes)
  plus the two pre-existing in-file callers in the post-process twins
  (:4517/:4539, below the last hunk, uncited until now). CONFIRM.
- `_coerced_manager_queryset` and `SyncMisuseError`: see I-R3 / I-R5.

#### Adjudication pass 3 (run 3) — I-R1 (CONFIRM)

Rejection stands. `_prefetch_relation_target_or_none` (:2304) and
`_reverse_relation_by_accessor_or_none` (:2354) are above the first hunk;
`utils/relations.py`, `connection.py` (for this finding's mechanism table —
the guard hunks touch no lookup-path line), `optimizer/plans.py` carry no
relevant change, and the "count rises to 7" caveat stands with
`_is_deterministic_order_name` re-pinned (def :823, call :955). The
`02e266df` tier-move note is history. Both reconsideration triggers
untriggered.

#### Adjudication pass 3 (run 3) — I-R2 (CONFIRM)

Family naming and both exclusions stand. `utils/permissions.py` and
`filters/base.py` are MATCH, so the exclusion reasoning rests on unchanged
bodies. No causing commit touches either file. Family
`orm-lookup-path-resolution` unchanged.

#### Adjudication pass 3 (run 3) — I-R3 (CONFIRM)

Still file-local. `models.Manager` appears at exactly three lines
package-wide, all in this file (:305, :3744, :4067 — count and file
identical). `_coerced_manager_queryset` (:3744) and both entry points (the
:305 `normalize_query_source` arm, the :4067
`_normalized_visibility_result` arm) are intact. The flag to the `utils/`
folder item stands.

#### Adjudication pass 3 (run 3) — I-R4 (REVISE: five-policy set, same rows)

Both load-bearing facts re-derived against the new tree by the successor
arms probe, not inherited. (1) `expected_routing` is still passed at
exactly 1 of the 5 seal calls (`_validate_post_orderset_result`, :3033);
the other four (:2548, :3662, :3961, :4069) pass none — the new sidecar
entries reach the seal through the validator, never directly. So `routing`
is still unreachable at both visibility sites. (2) The complete `policy=`
set reaching the runners is now FIVE: `_DEFAULT_SEAL_POLICY` (default),
`_CASCADE_SEAL_POLICY` (`permissions.py:623`, `:705`),
`_PREFETCH_CHILD_POLICY` (walker seam :525),
`_LIST_RELATION_CHILD_POLICY` (walker default :420), and
`_LIST_ARGUMENT_VISIBILITY_POLICY` (`list_field.py:1444`, `:1497`, plus the
connection's `_sidecar_visibility_policy` at :1872/:1920, which the probe
proves returns one of `_LIST_ARGUMENT_VISIBILITY_POLICY` /
`_DEFAULT_SEAL_POLICY` — no new policy). None of the five sets
`require_unevaluated` (still only `_SIDECAR_RESULT_POLICY`, still reaching
the seal solely through :3033), so `evaluated` is still unreachable at
both sites. The `SITES` table with that one addition is sound.

`probe_defect_arms_adjud3.py` (fresh scope, same instrument, five-policy
set) reports `sites with a mismatch: 2/6` with ZERO dead arms anywhere and
arms 8/3/6/7/5/6 — digit-for-digit the adjudication-2 record. The two rows
are the same two artifacts with the same reasons: (a)
`_validate_post_orderset_result` — the KNOWN subsumption (comment intact at
:3049-3059); (b) `_prepared_visibility_source` — the source-shape pairing
artifact, now generalized: TWO flag-setting policies reach via the walker,
and the sole production pairing for both is the unrouted
`base_queryset` seed, under which `alias` cannot fire. The gate
population's fifth term generalizes with it: source-shape pairings the
coarse model cannot see must be recorded with the site, PER POLICY. The
flip trigger generalizes likewise: a production caller pairing EITHER
`require_shared_alias` policy with a routed source owes the site a real
`alias` arm. Family `seal-defect-code-wording` stays gate-plus-declaration.

#### Adjudication pass 3 (run 3) — I-R5 (CONFIRM)

Still file-local with the population recorded. `SyncMisuseError` (119-139)
is above the first hunk with unchanged bases; siblings keep
(`list_field.py::ListArgumentError` :245, same bases;
`resource_policy.py::ResourceLimitExceeded` :121, identical line — the
template hunks sit below it). Declarations-not-definitions reasoning
stands.

#### Adjudication pass 3 (run 3) — I-R6 (CONFIRM)

Rejection stands. `utils/querysets.py::_safe_class_name` (142-157) is above
the first hunk; `exceptions.py` is MATCH, so the contract difference and
the trigger rest on unchanged bodies at both owners.

#### Adjudication pass 3 (run 3) — D1 (FIXED-owned; holding re-verified)

Disposition: fixed (owned fix `fd39cac6`, in the ledger — not a concurrent
fix). Verified at HEAD: the walker still seeds
`base_queryset(field.related_model)` unrouted (:457) and now seals under
`policy=policy` (:497) with `_LIST_RELATION_CHILD_POLICY` the default
(:420) and `_PREFETCH_CHILD_POLICY` at the nested-connection seam (:525) —
both carrying `require_shared_alias=True` (arms-probe-asserted), so the
owned fix's verdict holds on BOTH paths. The seal arm deciding it is
AST-identical to the execution-verified tree (identity probe). The five
permanent live rows resolve at HEAD (visibility :890/:914, identical;
multi_db :1594/:1619/:1636, +80 from `fee87ac4`) — see the Pending note;
the both-modes gate run is still owed. `## Defects` routing note stays
accurate.

#### Adjudication pass 3 (run 3) — D2 (fixed-concurrent; holding re-verified)

Disposition: concurrently fixed (unchanged). `allow_sliced` still has zero
hits across the package, the glossary and spec-034 at HEAD. The glossary
half still reads fixed: the re-rendered :1558 sentence keeps
"`reject_sliced=False` in `_PREFETCH_CHILD_POLICY`" and adds the
`_LIST_RELATION_CHILD_POLICY` split. The spec-034 half is intact: the
"Verified dependency to protect" clause at :353 still reads
`policy=_PREFETCH_CHILD_POLICY` with the nested-connection-concession
sentence `44712901` left true, and `fa6d48f8` touched only :444 and the
rationale's :193. Worker 0 homes the record, not new work.

#### Adjudication pass 3 (run 3) — D3 (RESOLVED-fixed by fee87ac4 + c87f4f98)

Disposition change: was ambiguous→the maintainer, now resolved by the maintainer's
decision-in-code. `fee87ac4` moved the snapshot-plus-re-seal into
`utils/querysets.py::apply_orderset_sync/_async` and routed the connection
field's order arm through it; `c87f4f98` added `apply_filterset_sync/_async`
over the shared `_apply_sidecar_sync/_async` and routed BOTH sidecar arms
through the seal in BOTH pipelines (`connection.py:1876` / `:1924`), with
the visibility seal under `_LIST_ARGUMENT_VISIBILITY_POLICY` exactly as the
list field's argument path. The card-053 row records both halves
discharged, noting the list field publishes no `filter:` — so no field
runs an unsealed sidecar return. Dated correction to the HEAD record: the
`ec0d21de` sentence in `### D3` ("the `FilterSet.apply_*` return is the
half still unsealed at both") was true at its commit and is superseded by
the later `c87f4f98`. Both contract sources the ambiguity cited are
byte-identical (spec-050 Edge sentence at :2123; the
`require_unevaluated` bullet still reasons from "the list field invoked
that ordering method one step earlier" — a true instance, now an
incomplete one; noted for the family item, not a defect). No consolidation
ever depended on D3. Worker 0 homes the record.

#### Adjudication pass 3 (run 3) — D4 (fixed-concurrent; measurement carries)

Disposition: concurrently fixed (unchanged). The `base_queryset` docstring
keeps the repaired wording and the body is AST-identical to the measured
tree (identity probe) — the region sits above the first hunk. The run-1
`probe_using_order.py` file did not survive the relocation (the run-1
scopes hold September-18 files, left unopened per precedent), and this
pass's fences forbid settings-backed execution, so the carry rests on
byte-identity rather than a re-run: the exact bytes the
adjudication-1 re-run measured are the HEAD bytes. Replayable via
`uv run python docs/dry/temp-tests/dry-adjud3-querysets-w1/probe_byte_identity_adjud3.py`.
Worker 0 homes the record.

#### Adjudication pass 3 (run 3) — D5 (fixed-concurrent; zero dead re-derived)

Disposition: concurrently fixed (unchanged), re-derived against the new
tree. The arms probe reads all six arm sets from the AST at HEAD bytes:
8/3/6/7/5/6 with zero dead arms anywhere — the D5 fix holds through the
rename (the renamed policy keeps its flags; no arm dict was touched).
Family `seal-defect-code-wording`; routing note stays accurate. Worker 0
homes the record.

Worker-2 D1-verification defects, observed (outside the F/D scope, one line
each for Worker 0): D-W2-a is fixed and its holding re-verified — both
runner docstrings name the walker's actual policies, now the pair
(`_PREFETCH_CHILD_POLICY` / `_LIST_RELATION_CHILD_POLICY` at :4122 and
:4375). D-W2-b is CONCURRENTLY FIXED by `44712901`: the exact premise it
challenged ("Off one edge down", slice licence for a plain list relation
with no gate) is restated at every site it named (`_SealPolicy` bullet,
walker comment, both prefetch docstrings, both runner docstrings, glossary
:1558), the plain-list child now seals under `_LIST_RELATION_CHILD_POLICY`
and gets the typed `sliced` defect, and the nested-connection seam is the
one place spending the licence. Worker 0 homes the record.

#### Adjudication pass 3 (run 3) — probes re-run (replay info)

The retained adjudication-2 arms probe was re-run read-only: it refuses
this tree with its designed blob-tripwire (`AssertionError:
('querysets', 'b68be0e3…')`, exit 1) — the pins work, and nothing below is
trusted from the record alone. Both successors live ONLY in the fresh
scope `docs/dry/temp-tests/dry-adjud3-querysets-w1/` (verified absent
before creation; earlier scopes untouched); both read-only, zero SQL, no
Django import (pure AST over `git show` bytes):

- `uv run python docs/dry/temp-tests/dry-adjud3-querysets-w1/probe_defect_arms_adjud3.py`
  → asserts the five input blobs, re-verifies both I-R4 load-bearing facts
  (routing at exactly 1 of 5 seal calls; walker default + seam + permissions
  + list_field + connection `policy=` edges; runner defaults flag-equal to
  default), proves the child policies differ on `reject_sliced` alone and
  the rename complete, reads all six arm sets, keeps the negative control.
  Output: `sites with a mismatch: 2/6`, zero dead arms, arms 8/3/6/7/5/6,
  exit 0. Discharges F3/I-R4/D5/F8. `execution-verified`
  (re-derived-by-adjudication-3-W1).
- `uv run python docs/dry/temp-tests/dry-adjud3-querysets-w1/probe_byte_identity_adjud3.py`
  → AST-identity of `base_queryset`, the seal alias arm, and the five
  prose-touched veteran functions (modulo the rename) across 69a25369..HEAD;
  veteran policy flags identical +1/rename; the three oracle bodies
  source-identical with re-pins :5076/:5098/:5125 and both assertions
  verbatim at :5116/:5136; enumeration 103+6/7/25 = 141 with the seven
  added functions named. Exit 0. Carries D4/F8/D1/F2 without re-execution,
  each replayably.

No source-mutating proof was needed (nothing here mutates source), so no
disposable workspace was built. The one authorized focused shared-tree run
was not spent (no pytest per this pass's fences). `FAKESHOP_SHARDED=1` and
Postgres cells stay `unverified` except where `fd39cac6`'s own record
already ran them in its workspaces.

#### Adjudication pass 3 (run 3) — freshness, refreshed to HEAD 24e6b4d3

`git rev-parse HEAD:<path>` for every input any finding fingerprints —
all 22 re-hashed blind (containment: no extra mismatch beyond the plan's 7):

```text
django_strawberry_framework/utils/querysets.py    b68be0e337d178fc703ca1ac2ff4144c1fd766a5
django_strawberry_framework/auth/mutations.py     dbe64995b87240b87a1d5119f46cc42c7cab646f
django_strawberry_framework/routers.py            a18c5001471d4a937bb81d2ff41a2e442e7d2dad
tests/utils/test_querysets.py                     183d52ba71b8324a4975e7e08515862af689dc98
django_strawberry_framework/permissions.py        757dce34cecd7a249b2634947a771d4608808bfe
django_strawberry_framework/connection.py         4894f90fb2963a44d25b0eabc649c67d04afa587
django_strawberry_framework/optimizer/nested_fetch.py 4d8d37a7f52cf94d2916f17db3a8a21393e28d57
django_strawberry_framework/types/resolvers.py    f3341e6a9f52659925762bce097033bac67e3b51
django_strawberry_framework/utils/write_values.py d28587c7c8d9f0d25e0a01bf289a63d9c3291728
django_strawberry_framework/rest_framework/resolvers.py 8024703ec0fb09758daeec0585e0065de1c61fc3
django_strawberry_framework/utils/write_transaction.py eca9ad4d3f765964df05884e080eb3ea63190ca8
django_strawberry_framework/mutations/permissions.py 54f770ae5aa1238327246cd2dcb141e8aac14965
django_strawberry_framework/utils/permissions.py  9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec
django_strawberry_framework/optimizer/walker.py   e8d800052cc87ca77070290c4c2f396061259b81
django_strawberry_framework/filters/sets.py       4ab65a26b0ccf56f7f40f4938282bba9690673d1
docs/GLOSSARY.md                                  d3ef357c26ede6a5bd21d4290b394ade4eb987b4
django_strawberry_framework/list_field.py         21380eb72364caef0da05ca3ee3f26c0134e3904
django_strawberry_framework/resource_policy.py    4b69e974decbd45916bd55f444f4b5f86724a07a
django_strawberry_framework/utils/relations.py    7662b0bb669c4dfba4a437f3b8f309357f718dca
django_strawberry_framework/optimizer/plans.py    cce985319c8833f3660653327d3003f1f03655a5
django_strawberry_framework/exceptions.py         e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b
django_strawberry_framework/filters/base.py       ba52351c284425336262ae6c2b82b262f6586fc0
```

Fifteen rows match their adjudication-2 values; exactly the seven plan-tabled
rows are refreshed (target, connection, walker, list_field, resource_policy,
GLOSSARY, tests). Every other row above re-affirms the corresponding
adjudication-1/2 `Freshness` line for the re-derived conclusion; no run-1
line was edited.

#### Adjudication pass 3 (run 3) — `## Pending execution` (entries 1–3 re-stated)

Entries 1–3 above stand as run-1/adjudication-1/2 history; state now:

1. Entry 1 (superseded by the five D1 live node ids): CONFIRM. All five
   resolve at HEAD — `test_products_visibility_api.py`
   `test_planned_prefetch_child_may_not_pin_its_own_connection` :890 and
   `test_planned_prefetch_child_still_serves_rows_when_the_hook_only_narrows`
   :914 (file untouched in range, lines identical), `test_multi_db.py`
   `test_planned_prefetch_child_cannot_route_itself_to_the_other_shard`
   :1594, `test_planned_prefetch_child_inherits_an_unrouted_parents_connection`
   :1619, `test_planned_prefetch_child_follows_a_routed_parent_onto_its_shard`
   :1636 (+80 from `fee87ac4`'s connection-seal rows; the D1 bodies
   themselves are outside those hunks). The both-modes gate run is still
   owed, and the sharded mode still needs the maintainer's word. Recorded for the
   gate; never triggered here.
2. Entry 2 (focused gate run over the three oracle suites): CONFIRM
   unchanged. All three paths resolve at HEAD. The F9-exercise expectation
   is intact: `is_async_queryset_adapter` still reads 7 + 9 = 16 lines
   across the two suites at both commits (those files are not fingerprinted,
   so their landing is gate-watch, never a trigger).
3. Entry 3 (arms witness, re-pointed at a successor expecting 2/6):
   REVISE the pointer, CONFIRM the expectation by re-derivation. The
   adjudication-2 successor path dangles by design (its blob pins refuse
   this tree — tripwire verified above), so the entry-3 command pointed at
   a probe that exits 1. The gate should run
   `uv run python docs/dry/temp-tests/dry-adjud3-querysets-w1/probe_defect_arms_adjud3.py`
   and expect `sites with a mismatch: 2/6` with zero dead arms and arms
   8/3/6/7/5/6 (rows argued in I-R4 above). Still `gate:`-typed.

#### Adjudication pass 3 (run 3) — mention-checks and gate-watch (verify, no widening)

- `tests/test_list_field.py` oracle counts: `fee87ac4`'s hunk is an import
  swap + docstring rename + the announced "Field target" message re-point
  (8 lines); `1f68871a` adds `transaction=True` + docstring. Neither touches
  a reader line or an assert — F9's 7 lines reproduce at both commits.
- spec-034 `:353` call-shape cite: `fa6d48f8` re-pointed the spec's test
  plan at :444 (and the rationale at :193) only; the :353 "Verified
  dependency to protect" clause is byte-identical.
- Gate-watch: `test_multi_db.py` changed in range (`fee87ac4` only, +82/−1
  per its stat); the five D1 node ids resolve as recorded under entry 1.
  `test_products_visibility_api.py` is untouched in range. No trigger —
  the final gate re-runs them as already planned.
- No other mismatch: the blind 22-table re-hash reproduced exactly the
  plan's stale set, and the six non-touching commits were each verified to
  touch no fingerprinted input.

#### Adjudication pass 3 (run 3) — family index and ledger (nothing owed)

No new family, no index-row change, no `## Owned changes` row. The
`fee87ac4`/`c87f4f98` centralization landed inside the existing
`post-set-apply-result-validation` owner (`_validate_post_orderset_result`
and its module), so every family row keeps its owner; the family item
verifies the concurrent move rather than redoing it. D3 and D-W2-b join
D2/D4/D5/D-W2-a as closeout-homed records (fixes landed; Worker 0 homes
the record-keeping, not new work). This pass lands no production edit, no
test edit, and no tracked file besides this artifact's own append.

#### Adjudication pass 3 (run 3) — item state

Zero production edits, zero test edits, zero new tracked files. Untracked
scratch created, all inside the fresh scope (other scopes untouched):
`docs/dry/temp-tests/dry-adjud3-querysets-w1/probe_defect_arms_adjud3.py`
and `.../probe_byte_identity_adjud3.py`. Item-scoped diff vs
`ITEM_BASELINE=101a8d752b5a324021ffe0b923cf49270a7588c6` covers only this
artifact's append plus the `Status:` line (verified before finishing; the
pre-existing dirt is the attributed adjudication-1+2 append, and the probe
scope is the authorized fresh scope). `uv run ruff check` /
`ruff format --check` pass on the scope dir (format last; the COM812
hand-comma is inside my own scope, no concurrent file touched); no ruff on
the `.md` artifact. The one authorized focused shared-tree pytest was not
spent — every claim here is decided by HEAD-byte inspection plus the two
read-only AST probes. `FAKESHOP_SHARDED=1` and Postgres cells stay
`unverified`. Concurrent dirt (package, tests, docs) left alone. HEAD
`24e6b4d3` at start, mid-pass, and finish — unmoved throughout.

## Independent verification (Worker 2) — adjudication-3

Two-phase per the dispatch. Phase A (below, as recorded pre-read in
`docs/dry/temp-tests/dry-adjud3-querysets-w2/phase_a_expectations.md`) was
written BEFORE opening `### Adjudication pass 3 (run 3) — Worker 1`
(artifact lines 3503–4042) and before opening
`docs/dry/temp-tests/dry-adjud3-querysets-w1/`. Reconciliation + verdict
follow it.

### Phase A — expectations (recorded blind)

Start HEAD: `24e6b4d3e74b104779225cd6bbff713880bc48e3` (recorded before any
read). `ITEM_BASELINE=101a8d752b5a324021ffe0b923cf49270a7588c6` resolves.
Scope `docs/dry/temp-tests/dry-adjud3-querysets-w2/` verified absent, then
created by me. Method: HEAD-pinned bytes only — `git rev-parse
<rev>:<path>`, `git show <rev>:<path>`, `git grep -n <pattern> <rev>`
with both top-level and `**/` patterns (the latter alone misses top-level
files — an instrument lesson, not a verdict change), `git diff
69a25369..24e6b4d3`. Two read-only probes of my own (pure AST over `git
show` bytes; no Django import, zero SQL, no pytest, no settings, no
database). Never imported `management/commands/inspect_django_type`.

22-hash re-verification at HEAD: 15 MATCH, 7 STALE —
`utils/querysets.py b68be0e3…`, `tests/utils/test_querysets.py 183d52ba…`,
`connection.py 4894f90f…`, `optimizer/walker.py e8d80005…`,
`docs/GLOSSARY.md d3ef357c…`, `list_field.py 21380eb7…`,
`resource_policy.py 4b69e974…` (full blobs in the probe; old pins exact in
all 22 rows). Exactly the plan's reconciliation row. Causing range: the
plan's 11 commits; per-file cause re-derived (querysets ← fee87ac4 /
44712901 / c87f4f98, +251/−30 in 10 hunks at old 2404 … 4152; tests ←
44712901 / 24e6b4d3; connection ← fee87ac4 / c87f4f98; walker ← 44712901;
GLOSSARY ← 9350eb8d / 44712901; list_field ← fee87ac4; resource_policy ←
9350eb8d). The `ec0d21de` artifact edit (3 hunks) read as the record per
the plan; its citations re-verified against code.

Per-finding expectations: F1 CONFIRM (3 defs; sidecars new consumers);
F2 REVISE counts (7 constants, 6 fields; oracles :5076/:5098/:5125
identical; enumeration 141 = 109/7/25); F3 CONFIRM (6 sites, zero dead);
F4 CONFIRM (guard :1593 identical, count 2); F5/F6/F7 CONFIRM (symbols
identical, triggers untriggered); F8 REVISE member line (two child
policies, both alias-guarded); F9 CONFIRM (0 production, 16 test lines /
10 asserts); F10 CONFIRM (bodies identical at :1057/:1102/:1582, :1240,
:1332/:1336/:1751); F11 CONFIRM (6 consumers, schema.py cites untouched);
F12 CONFIRM with `_snapshot_routing_intent` REVISED to zero external
consumers (:3120/:3153 in-module) + `prepared_resolver_source` re-pinned
(:1769, :1715/:1762, :4517/:4539); I-R1/R2/R3/R5/R6 CONFIRM; I-R4 REVISE
(1-of-5 routing, FIVE runner policies, 2/6 zero dead); D1 FIXED holds
(per-path pins; multi_db :1594/:1619/:1636 identical); D2 FIXED holds
(`allow_sliced` 0; :1558; :353); D3 REVISE (HEAD-record FilterSet sentence
false at HEAD — sealed at connection, list_field publishes no `filter:`;
expected resolved-by-landing); D4/D5/D-W2-a FIXED holds; D-W2-b
CONCURRENTLY FIXED by 44712901 (flip open→fixed). Mention-checks:
test_list_field 8 lines touch import/docstring/match only; spec-034 :353
intact (:444-only touch). Gate-watch: D1 node ids resolve with identical
bodies; both-modes run still owed. Pending: entry 1 CONFIRM + re-pin
(still `proof:`), entry 2 CONFIRM (still `gate:`), entry 3 REVISE pointer
(old command red at HEAD, exit 1; successor must re-derive 2/6).
Families: no new family expected (8 new names to `sealed-execution-queryset`);
`seal-defect-code-wording` + `child-queryset-alias-inheritance`
parenthetical refreshes; no ledger row. Verdict expectation: `verified`
(keeping `verified, pending execution`).

Probe outputs (own execution): `probe_spans_adjud3.py` → `enumeration:
109 funcs + 7 classes + 25 consts = 141`, `ALL OK (23 checks)`, exit 0;
`probe_arms_adjud3.py` → 5 seal calls with routing at `_validate` only, 6
fields / 7 constants, all five policy edges re-verified, runner defaults
flag-equal, `sites with a mismatch: 2/6` with zero dead arms (8/3/6/7/5/6)
and the negative control intact, exit 0; adjudication-2 entry-3 probe
re-run read-only → `AssertionError: ('querysets', 'b68be0e3…')`, exit 1.

### Phase B — reconciliation (every difference, explicitly)

Read AFTER Phase A was on disk: W1's record (lines 3503–4042) and both
W1 probes (read in full, then re-run read-only — outputs identical to
W1's record and, for the arms table, digit-for-digit identical to my own
probe's: same 2/6, same counts, same two artifacts).

Agreement (independently derived on both sides): the full 22-table
identical (all full blobs match); the causing range identical (11 commits,
same 5 touching with the same per-file attribution, same 6 non-touching
with matching reasons); the target hunk map identical (10 hunks, same
old-line starts, 7 prose-only, executable inventory 7+1+rename);
enumeration identical (141 = 109/7/25, 6 async, same 7 added functions);
F1/F3/F4/F5/F6/F7/F9/F10/F11 CONFIRM with matching counts, pins and
reasons; F2 REVISE with the same 7-constant census and oracle re-pins;
F8 REVISE with the same two-policy member line; F12 with the same
snapshot revision and re-pins; I-R1/R2/R3/R5/R6 CONFIRM; I-R4 REVISE with
the same 5-policy set and generalized source-shape reason; D1/D2/D4/D5 /
D-W2-a FIXED holdings with matching pins; D3 resolved-by-landing with the
`ec0d21de` sentence dated and superseded by `c87f4f98`; D-W2-b
concurrently fixed by 44712901; entries 1–3 in the expected states
(re-pin / CONFIRM / REVISED pointer to a re-derived 2/6 successor, types
unchanged); mention-checks and gate-watch outcomes identical; no ledger
row; fences respected.

Deltas reconciled (ten, none verdict-affecting):

1. New-name homes: I expected all 8 names under
   `sealed-execution-queryset`; W1 assigns the 7 sidecar functions to the
   pre-existing `post-set-apply-result-validation` (verified: the name
   stands in run-1's record at line 1154) and the constant to F2/F8. Finer
   and valid; "no new family" is consistent. Accepted.
2. Index parentheticals: I expected Worker-0 refreshes for
   `seal-defect-code-wording` (runner set 5) and
   `child-queryset-alias-inheritance` (D-W2-b fixed); W1 records "no
   index-row change". Ownership/files/holding/status genuinely unchanged,
   so W1's mechanics are correct; the two parentheticals remain available
   to Worker 0 from W1's record. Advisory below, not a W1 gap.
3. W1's multi_db "+82/−1 per its stat" vs actual +81/−1 (82 is the stat's
   total-changed column; fee87ac4-only confirmed). One-digit erratum in a
   gate-watch note; node ids and bodies verified independently. Noted.
4. W1's "(MATCH file)" for `extension.py`, which is fingerprinted by no
   row — precisely "unchanged in range" (absent from the range log).
   Wording imprecision, substance true. Noted.
5. F1 direct callers: my probe pins 4 call lines
   (`reject_async_in_sync_context` 1, `_disposed_awaitable` 1,
   `_apply_sidecar_*` 1+1); W1's "citation reads correctly" is
   transitively true. Precise set recorded here; no W1 change needed.
6. `sql.Query` sweep: mine (capital-Q, adjudication-1's pattern) finds 0
   outside; W1 additionally names the pre-existing lowercase
   `lateral_fetch.py:82` import (verified real, file unchanged in range).
   Complementary; same one-owner verdict.
7. F4 anchors: W1 re-pins run-1's body sub-span (:1609–1632, endpoints
   re-verified equal by me); I pinned the def (:1593) plus whole-body
   identity. Same bytes, different anchors. Agreement.
8. Matrix twin census 4→6 (new `_apply_sidecar` + `apply_filterset`
   pairs): W1 does not state the census sentence, but its evidence
   confirms the axis conclusion for the new pairs (executable-identity
   modulo the rename; the async twins' extra arms are the same legitimate
   coloring the moved bodies already carried), and run-1 census prose
   stays history by precedent. Recorded here with evidence; accepted.
9. Orderset message ("Field target …"): W1 covers the re-point in the
   mention-checks; my probe additionally asserts prod + literal oracle
   moved together with zero old-wording hits. Agreement.
10. Card-053 row (KANBAN.md:334): verified — it records both halves
    discharged and notes the list field publishes no `filter:`, exactly
    as W1's D3 cites. Agreement.

Verification job. Item-diff scope: `git diff
101a8d752b5a324021ffe0b923cf49270a7588c6 -- <artifact>` is exactly two
hunks — the `Status:` swap (the diff's sole deletion line) plus a purely
additive 541-line EOF append (W1's record, read in full); prior text
untouched, no foreign hunk. The window's other paths (target 4-line
`__name__`→`_safe_class_name` hardening, bug_hunt ledger, plan,
tests) are concurrent Worker-0/hunt bytes, out of item scope and left
alone; the target hunk touches wording only and moves no verdict. HEAD
tripwire: `24e6b4d3` at my start, mid-phase, and finish — unmoved
throughout. AGENTS.md prose rules on the diff: no process provenance
beyond DRY.md-mandated role/plan labels (`Worker 1`, `Worker 0 homes the
record`, `the plan's 7`); zero hits for audit/sweep/restored/hardening/
previously/grader/feedback; citations in the precedent form (raw `path:NN`
allowed in `docs/dry/dry-*.md`, `path::Symbol` elsewhere); no tests added
(the probes are untracked scratch at the DRY.md-mandated location); no
cross-file links, so no link block owed; no CHANGELOG, no commit. Pending
typing: entry 1 still the pinned `proof:`, entries 2–3 `gate:` — types
unchanged, all three commands live. Test authorization: two own probes +
two W1-probe re-runs + one retired-probe red confirmation, all read-only;
no pytest spent; no workspace built (nothing mutates source);
`inspect_django_type` never imported. Sharded/Postgres cells stay
`unverified` as typed. `uv run ruff check` + `uv run ruff format --check`
pass scoped to both adjudication-3 probe dirs (4 files); the layout
script reports `Fixed 0 file(s)` on my scope. No `## Defects` entries:
nothing found outside the adjudicated scope.

### Verdict

`Status: verified`. Every W1 claim re-derived by me agrees; the ten
deltas are finer-or-equal evidence (1, 5–7, 9–10), Worker-0-closeout
prose (2), noted errata (3–4), and a recorded-here observation (8). Worker
0 plan marking: keep `verified, pending execution` — entry 1's proof
still owes the gate run in both modes (sharded mode needs the maintainer's
authorization); entries 2–3 are gate requests (entry 3 at W1's new live
path expecting `2/6` with arms 8/3/6/7/5/6, doubly derived — W1 + my
re-run — and triply witnessed counting my independent probe). No
family-row, ledger, or pending-entry change is owed to Worker 0 beyond
that marking; two parenthetical refreshes are available from W1's record
should closeout want them (`seal-defect-code-wording`: runner set 4→5 +
rename; `child-queryset-alias-inheritance`: D-W2-b fixed). No defects,
no `## Defects` entries. Finish HEAD:
`24e6b4d3e74b104779225cd6bbff713880bc48e3`, unmoved.

### Scoped re-trace (run 7) — Worker 1

Scoped run: `0.0.15 2026-09-28-7`. Adjudication-3 verified this item at
`24e6b4d3`; HEAD is now `0c0537e2`
(`0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`, verified at start and again
unmoved at finish). Prior text above untouched; this section appends. No
production edits, no test edits, no new tracked files: a file-item re-trace
owes none. `ITEM_BASELINE=8f8ca0fc05bba066755221150fe33d3b4d99a9bb` resolves;
the item-scoped diff holds this append plus the `Status:` swap and nothing
else. The target's worktree dirt (`8fc556d5`, hunt `truth.*` migration, ~540
lines vs HEAD) is concurrent work outside the ledger and the cycle baseline;
every claim below is traced at HEAD bytes (`3616927d`), never the worktree.

Method. The artifact's recorded pins equal `5ee86193` bytes on 21 of 22
inputs (verified blob by blob; the one exception is `filters/sets.py`, whose
pin predates the range by one docstring commit — see the table), so the
re-trace adjudicates `5ee86193..0c0537e2` per input, read as full diffs never
as messages. The target drift is one commit (`982537c3`), 13 hunks, 63+/35-:
(1) the `origin` thread through `_row_source_model` / `normalized_row_source`
/ `_readable_queryset_state` / `_raw_list_source_message`; (2) new
`_sentence_start` + single-sourced `_UNSEALABLE_STATE_CAUSES` with the three
in-file untrusted arms recomposed onto it; (3) the `_SealPolicy`
docstring widened from post-OrderSet to every post-sidecar result (both the
`require_unevaluated` and the `reject_combined` bullets); (4) module-docstring
+ prefetch-docstring rewords and two provenance-word comment deletions. Every
claim below was verified against HEAD bytes via `git show HEAD:<path>`,
`git rev-parse HEAD:<path>` and `git grep`, plus four read-only pure-AST
probes over `git show` bytes in `/tmp/stale7-probes/` (no Django import, zero
SQL, nothing mutates source, so no workspace was built and no workspace run
id exists). Regions outside the drift hunks are byte-identical to the bytes
the artifact adjudicated; dispositions cite HEAD re-pins for every moved line.

Enumeration recount at HEAD (`ast.Module.body`, probe): 104 sync + 6 async =
110 functions, 7 classes, 25 + 1 = 26 constants = 143 names (was 141). Exactly
two additions, zero removals, zero renames: `_sentence_start` (function) and
`_UNSEALABLE_STATE_CAUSES` (constant). Homes proposed below; the I-R5 closure
holds with two new rows.

#### Scoped re-trace (run 7) — fingerprints: 11 MATCH, 1 STALE-plus-note, 10 STALE

`git rev-parse HEAD:<path>` for all 22 inputs (recorded pin → HEAD):

```text
django_strawberry_framework/utils/querysets.py    b68be0e3… → 3616927d… STALE (982537c3: origin + causes + policy prose)
django_strawberry_framework/auth/mutations.py     dbe64995… → d1a59c44… STALE (e6a33c46 module-docstring first line only)
django_strawberry_framework/routers.py            a18c5001… → 7d5e4814… STALE (same, first line only)
tests/utils/test_querysets.py                     183d52ba… → 73e7a6c2… STALE (982537c3 wording oracles + 4667db4f real-model fixtures)
django_strawberry_framework/permissions.py        757dce34… → 72102cc0… STALE (982537c3: both untrusted arms onto the constant)
django_strawberry_framework/connection.py         4894f90f… MATCH
django_strawberry_framework/optimizer/nested_fetch.py 4d8d37a7… MATCH
django_strawberry_framework/types/resolvers.py    f3341e6a… → 72d62dc4… STALE (982537c3: the one origin= caller, +3 lines)
django_strawberry_framework/utils/write_values.py d28587c7… MATCH
django_strawberry_framework/rest_framework/resolvers.py 8024703e… → 0d302782… STALE (e6a33c46 first line only)
django_strawberry_framework/utils/write_transaction.py eca9ad4d… MATCH
django_strawberry_framework/mutations/permissions.py 54f770ae… MATCH
django_strawberry_framework/utils/permissions.py  9889d6fe… MATCH
django_strawberry_framework/optimizer/walker.py   e8d80005… → 75f9c6b6… STALE (53a50bf7 name-memo + e1ba094e/e6a33c46 prose; child-seal region untouched)
django_strawberry_framework/filters/sets.py       4ab65a26… → 993e887a… STALE-PLUS-NOTE (see below)
docs/GLOSSARY.md                                  d3ef357c… → 3413edc3… STALE (4 hunks; sealed-queryset reword + dup-Status delete)
django_strawberry_framework/list_field.py         21380eb7… MATCH
django_strawberry_framework/resource_policy.py    4b69e974… MATCH
django_strawberry_framework/utils/relations.py    7662b0bb… → 8dbc3fe6… STALE (instance_accessor docstring-only reword)
django_strawberry_framework/optimizer/plans.py    cce98531… MATCH
django_strawberry_framework/exceptions.py         e06b0b7f… MATCH
django_strawberry_framework/filters/base.py       ba52351c… MATCH
```

`filters/sets.py` note: the recorded pin `4ab65a26` is the `24e6b4d3` blob,
not the `5ee86193` blob (`722e0c77`). `29ddc0a8` (inside
`24e6b4d3..5ee86193`, after adjudication-3) retouched two docstring lines in
`FilterSet.apply_sync`'s trailer (`materialized` → `lazy`, :3357/:3396); the
in-range hunk retouches one comment line (:1705). All three hunks are
prose-only and touch neither F8's `:2592` edge (same line, same bytes) nor
F11's consumer. Pin refreshed to `993e887a` with this correction; no finding
moves on it.

#### Scoped re-trace (run 7) — F1 (CONFIRM)

Count stays 3. `auth/mutations.py:505-511` and `routers.py:279-285` are
byte-identical at the same lines (each file's whole drift is its line-1
docstring, 1+/1-, line count preserved); the disposal region
(`_disposed_awaitable` :197, `_dispose_sync_awaitable` :219) sits below the
target's :51 docstring hunk (+2 shift) and above every code hunk, bodies
untouched. The new `_apply_sidecar_*` consumers F1 already counts are intact.
The second-axis challenge forces the same 3. Family
`awaitable-refusal-and-disposal` unchanged.

#### Scoped re-trace (run 7) — F2 (CONFIRM, re-pinned; one new family-sweep candidate)

Still one owner. Exclusivity re-derived at HEAD: `models.QuerySet(` outside
the target = 0 hits; `sql.Query` touches outside = 0 (the only `models.sql`
import stays the pre-existing `lateral_fetch.py:82` where-clause import, file
unchanged in range); executable `object.__getattribute__` /
`type.__getattribute__` / `inspect.getattr_static` outside = 0 (the one
textual hit stays the pre-existing `converters.py:119` comment).
`_seal_or_defect` still has exactly 5 call sites, all in-file (:3038 with
`expected_routing`, :3672, :3992, :4097, :2550; def :3265), zero callers
package-wide outside. `_SealPolicy` stays 6 fields with identical defaults;
all 7 policy constants keep byte-identical flags (probe-read). The defect-code
set is still the same closed 9 in the same order (prose :3277-3281). The
`origin` thread adds a consumer parameter, not a definition (analysis in its
own section below): the seal body, the policy record and every call shape keep
their counts. The three inventory-oracle tests exist with AST-identical bodies
at :5150/:5172/:5199 (+74 test-file shift, below every test hunk).
`_GraphWalk` callers hold by byte-identity (no code hunk in :826-2700; the
:2420 hunk is docstring-only, net 0).

Re-pins: the four planning readers are `connection.py:1610` (MATCH file),
`nested_fetch.py` 123/131/197 (MATCH), `predicates.py:165` (file absent from
the range log, same statement), `extension.py:1188` (was :1161, +27, same
`_result_cache` getattr). NEW for the family sweep: `extension.py:1237`
(`if queryset.query.combinator: return queryset`, the 982537c3 combined
passthrough) is a fifth `.query`-attribute read the run-1 sweep could not
have seen; whether its input is already-sealed is the family item's question
(F2 already routes that classification to the family — this names the new
member, it does not answer it). The glossary projection moved with the code:
*Sealed execution queryset* (:1893) now states the post-sidecar `evaluated`
refusal, and the module + prefetch docstrings reword their cause lists onto
the constant's vocabulary — production + projection moving together, the
legitimate shape. Family `sealed-execution-queryset` unchanged.

#### Scoped re-trace (run 7) — F3 (REVISE: arm sets identical, prose ownership moved)

`_defect_message` still has exactly 6 call sites (probe-read with arm sets):
target :3082 (8 arms: 7 shape codes via `dict.fromkeys` + `routing`),
:3753 (3), :4000 (6), :3877 (7); `permissions.py:354` (5), `:412` (6) — counts
8/3/6/7/5/6, digit-for-digit the adjudication-3 record, zero dead arms. The
dispatcher itself (:3828) sits between drift hunks, body untouched. No code
added, no arm added or removed, no site added: the F3 RULE (each site renders
only the subset it can reach) holds exactly as recorded, and C12 still forces
1 definition with 6 hand-revisited sites.

What the drift moves is a wording sub-rule F3 never counted: the five
`untrusted` arms (3 in-file + 2 permissions) each spelled their own cause
list ("a foreign Query class, a foreign row iterable, or malformed
deferred-filter state") plus per-site advice. Those five spellings are now one
constant, `_UNSEALABLE_STATE_CAUSES` (:3733), with per-site subject + detail
prefixes retained. The commit's own message states the consolidation ("The
five untrusted seal messages listed three causes ... they now share
_UNSEALABLE_STATE_CAUSES"). So: the seal-defect-code FAMILY gains a
concurrently-consolidated member — the cause-list + advice text is now
authored once in `utils/querysets.py` and composed by name (permissions.py
imports it at :120). The family item verifies this move, it does not redo it;
the gate it owes still gates arm SETS, now with the prose half already
single-sourced. `seal-defect-code-wording` stays gate-plus-declaration, with
the declaration half narrower than recorded.

The consolidation arrived with independent oracles: six literal-substring
assertions pin the constant's text without reading it — source arm
(test_querysets.py:461), result arm (:753), raw-list arm
(test_resource_policy.py:2153, plus its file-local tail "a result cache that
is not an exact list"), root + edge arms (test_permissions.py:1228/:1419),
and over the wire (test_list_field_api.py:2353). A seventh
(tests/types/test_resolvers.py:1636) pins the origin lead. Finding stays in
family `seal-defect-code-wording`.

Refreshed fingerprints for this finding: `utils/querysets.py`
`3616927de2bc8a7bead38f255ece8695064d5de0`, `permissions.py`
`72102cc08e19689b61bbf8bb8697b7d86e4ec1a5`.

#### Scoped re-trace (run 7) — F4 (CONFIRM)

Count stays 2. `connection.py::_guard_source_not_pre_sliced` is in a MATCH
file (byte-identical, same lines); the seal's `sliced` arm code is untouched
(the only seal-body hunks are the two provenance-word comment deletions at
:3494/:3504, which no finding cites); `nested_fetch.py` is MATCH including the
reject-vs-degrade contract difference. All 7 policy constants keep their
flags, so no third definition arrives via the licence axis. The family item's
open question and the `GraphQLError` vs `ConfigurationError` proof it owes
are unchanged.

#### Scoped re-trace (run 7) — F5 (CONFIRM)

Count stays 2, site lists unchanged. `types/resolvers.py::_visible_related_object`
(:395) sits above that file's :533 hunk, body untouched; its 7 call sites are
in unchanged regions; `utils/write_values.py` is MATCH (`:226` consumer
intact); `rest_framework/resolvers.py:1447` is in the file's 1+/1- line-1-only
drift, same line, same call shape. The `types/resolvers.py` drift (the
`prefetch_origin` + `origin=` call at :538/:579, inside `_make_relation_resolver`)
touches neither definition nor the seed-pin/coloring variation axes. Target
re-pins: `related_visibility_queryset_or_default` :4239,
`visible_related_object` :4308 (both +28, bodies below every code hunk). The
disprove-first question the family item owes is untouched by every causing
commit. Family `related-object-visibility-recheck` unchanged.

#### Scoped re-trace (run 7) — F6 (CONFIRM)

Rejection stands. `coerce_field_value_or_none` (def :312, +2) and `_stringified`
(:4260, +28) with `stringified_pks_present` (:4270) / `pks_all_present` (:4294)
are outside all code hunks; `utils/write_transaction.py`,
`utils/write_values.py`, `rest_framework/resolvers.py` (line-1-only drift)
carry no relevant change. The reconsideration trigger is untriggered:
production callers are still only `visible_related_objects` (in-file :4374,
+28) and `write_values.py:313` (MATCH file, same `type_check_relation_id`
routing). `keyset.py:384` is intact (file absent from the range log, same
`field.to_python` statement). Contract difference byte-identical. Family
`field-value-coercion` unchanged.

#### Scoped re-trace (run 7) — F7 (CONFIRM)

Rejection stands. `sync_pipeline_recourse` (:356, +2) and `_RELAY_ASYNC_RECOURSE`
(:349, +2) are outside all code hunks with byte-identical literals;
`mutations/permissions.py` and `utils/permissions.py` are MATCH;
`permissions.py`'s `_ASYNC_RECOURSE` re-pins to :137 (+1 import line) with the
same literal, and the drift hunks in that file (import + two untrusted arms +
one docstring) never touch the recourse sentence or the four-clauses-differ
reason. The three compositions keep identical shapes at
`mutations/resolvers.py:142` (was :139, +3 from that file's own drift),
`forms/resolvers.py:125`, `rest_framework/resolvers.py:201`. Reconsideration
trigger (differ only in the subject noun) untriggered. Family
`sync-boundary-recourse-wording` unchanged.

#### Scoped re-trace (run 7) — F8 (CONFIRM, re-pinned)

The two enforcement mechanisms are still 2 definitions, correctly counted:
`base_queryset`'s `using` arm (body `manager.using(using).all() if using is
not None else manager.all()` intact, :248) and the seal's
`require_shared_alias` arm (untouched code). Enforcement sites:
`permissions.py:691` (`using=state.alias`, -1), `filters/sets.py:2592`
(`using=parent_db`, same line), `_sealed_prefetch_related_lookups` (seal call
at :2550 with `required_alias` + `_PREFETCH_CHILD_POLICY` positional, +2; the
:2420 hunk in that function is docstring-only). The walker still seals under
the two child policies with `require_shared_alias=True` in both
(probe-read flags): default `_LIST_RELATION_CHILD_POLICY` (:525), unrouted
seed (:562), `policy=policy` (:602), nested-connection seam (:607 def, :630
policy edge, wired at :1726), plain-list call taking the default (:1141).
The glossary projection cite is intact (`Prefetch alias threading`, same
sentence, same :1558). Coupling to D1 stays discharged. Family
`child-queryset-alias-inheritance` still owes its family item.

#### Scoped re-trace (run 7) — F9 (CONFIRM)

Still no production reader. HEAD census (`git grep` over package + tests +
examples): the definition (:414, +2) is the only package hit; test readers
are 7 lines in `tests/test_list_field.py` + 9 in
`tests/optimizer/test_extension.py` = 16 lines, the same count at both commits.
`wrap_` consumers are still `list_field.py` only (MATCH file: import :105 + 4
call sites :1437/:1473/:1490/:1526, same shapes) and `unwrap_` still
`optimizer/extension.py` (re-pinned :1169/:1172, +27, same
`(value, was_adapted)` shapes; that file's drift is the combined passthrough
+ cache lifecycle + first line, none of it in the adapter path). Not in any
`__all__`, not re-exported (no `__all__` drift in range). The principle-11
keep-or-delete decision with its oracle-shape entailment still belongs to
family `async-only-queryset-row-adapter`.

#### Scoped re-trace (run 7) — F10 (CONFIRM)

Rejection stands; the contract difference is byte-identical (`connection.py`
MATCH — both QuerySet-yes sites and the union admission test unchanged;
`is_async_only_iterable` :377, +2, outside all code hunks). Composed consumers
re-pin with identical shapes: `list_field.py` :1332/:1336/:1751 (MATCH file),
`resource_policy.py:1240` (MATCH file, and its `:1051`
`normalized_row_source(result)` default-origin call is the same pre-existing
consumer). `list_field.py` holds no direct `AsyncIterable`/`AsyncIterator`
reference at HEAD. Reconsideration trigger untriggered. Recorded under
`async-only-queryset-row-adapter`, unchanged.

#### Scoped re-trace (run 7) — F11 (REVISE: consumer files 6 → 5, conclusion stands)

Still 1 definition, same direct-site classification — but the consumer census
moves on a non-target hunk this re-derivation must report truthfully.
`run_in_one_sync_boundary` (:467, +2) is outside all code hunks. The five
direct `sync_to_async(...)` sites keep byte-identical shapes at
`types/resolvers.py` :619/:692/:763 (+3 from that file's origin hunk) and
`testing/client.py` :471/:475 (same lines; that file's whole drift is its
line-1 docstring). Neither encodes the consumer-hook rule, as recorded. The
package-wide `sync_to_async(` census is 10 files with identical per-file
counts except `schema.py` 2 → 1, and that delta is prose-only (a docstring
reword dropped one ``sync_to_async(`` mention; schema.py never held an
executable direct call).

What moves: `1b6a09b1` removed schema.py's `run_in_one_sync_boundary` import
(:79) and all three calls (:346/:360/:373), replacing them with per-window
private-thread machinery (`ThreadPoolExecutor`, `SyncToAsync`,
`ThreadSensitiveContext`). At HEAD schema.py carries only a prose mention
(:430). The remaining five consumer files still compose by name
(`permissions.py:126` + call :733, `orders/sets.py:50` + call :831,
`filters/sets.py:83` + call :3497, `mutations/resolvers.py:105` + call :1308,
`auth/mutations.py:73` + calls). The new schema machinery is neither a second
definition nor a new enforcement site of this rule: F11's contract is "a
consumer-overridable sync hook runs in exactly one off-loop worker", while
the window machinery answers per-window thread/connection isolation for
completion-spanning transactions (different contract, different reasons to
change — the same classification F11 already gives the pre-existing direct
sites). C7 still forces 1 definition. Holding-family consequence for verified
`one-sync-boundary` named below (consumer census record moved; verdict stands
subject to Worker-0's routing).

Refreshed fingerprints for this finding: `utils/querysets.py`
`3616927de2bc8a7bead38f255ece8695064d5de0`, `types/resolvers.py`
`72d62dc4ebfe90aa1ed13e6786c63f9d76873e59`.

#### Scoped re-trace (run 7) — F12 (CONFIRM all live rows + re-pins)

Superseded rows stay superseded (adjudicated under I-R1/I-R6, confirmed
there). Every live row re-derived:

- `_safe_routing_repr`: production readers still only the seal's routing arm
  (:3448-3451, +5). 1 definition. CONFIRM.
- `_GraphWalk` / `_WalkState` / `_walk_short_circuit` (defs :828/:843/:892,
  +2): region byte-identical (no code hunk in :826-2700), caller count holds
  by construction; the `converters.py:119` hit is still the pre-existing
  comment. CONFIRM.
- `_snapshot_routing_intent`: still ZERO external consumers — executable
  callers only in-file at :3125/:3158 (was :3120/:3153, +5); package-wide
  sweep finds nothing else. Still 1 definition. CONFIRM.
- `_routing_hints_equal`: reader still the seal (:3442, +5). CONFIRM.
- `_bake_deferred_filter_or_defect` + `_deferred_value_defect`: sole caller
  still the seal (:3497, +5); `PROHIBITED_FILTER_KWARGS` still single-sited
  (import + floor mirror :102-110, one use :2675, +2). The recorded challenge
  still returns 1. CONFIRM.
- `prepared_resolver_source` (def :4490, +28): still composed by both
  collection flavors (`connection.py:1769`, `list_field.py:1715/:1762` — both
  MATCH files) plus the two in-file post-process callers (:4545/:4567, +28).
  CONFIRM.
- `_coerced_manager_queryset` and `SyncMisuseError`: see I-R3 / I-R5.

#### Scoped re-trace (run 7) — I-R1 (CONFIRM)

Rejection stands. `_prefetch_relation_target_or_none` (:2306, +2) and
`_reverse_relation_by_accessor_or_none` (:2356, +2) are above the first code
hunk; the :2420 hunk is the NEXT function's docstring, as its `@@` header
shows. `utils/relations.py`'s drift is an `instance_accessor` docstring-only
reword (:700) — none of the mechanism bodies (`classify_path`,
`_resolve_segment_field`, `_lenient_traverses_to_many`) is touched;
`connection.py`, `optimizer/plans.py`, `list_field.py` are MATCH, so the
five-body mechanism table, the contract difference and both reconsideration
triggers rest on unchanged bodies, including the "count rises to 7" caveat
(`_is_deterministic_order_name`, same lines).

#### Scoped re-trace (run 7) — I-R2 (CONFIRM)

Family naming and both exclusions stand. `utils/permissions.py` and
`filters/base.py` are MATCH, so the exclusion reasoning rests on unchanged
bodies. No causing commit touches either file. Family
`orm-lookup-path-resolution` unchanged.

#### Scoped re-trace (run 7) — I-R3 (CONFIRM)

Still file-local. `models.Manager` appears at exactly three lines
package-wide, all in this file (:307 `normalize_query_source` arm,
:3778 `_coerced_manager_queryset` def, :4095 `_normalized_visibility_result`
arm — count and file identical, re-pinned). Both entry points and the coercion
body are intact; the flag to the `utils/` folder item stands.

#### Scoped re-trace (run 7) — I-R4 (REVISE: same rows, wording half single-sourced)

Both load-bearing facts re-derived against the new tree by AST probe, not
inherited. (1) `expected_routing` is still passed at exactly 1 of the 5 seal
calls (`_validate_post_orderset_result`, :3038); the other four (:2550, :3672,
:3992, :4097) pass none — the origin thread adds parameters to the row-source
call chain, never a seal call, and the sidecar entries still reach the seal
through the validator. So `routing` is still unreachable at both visibility
sites. (2) The complete `policy=` set reaching the runners is still FIVE:
`_DEFAULT_SEAL_POLICY` (default), `_CASCADE_SEAL_POLICY`
(`permissions.py:622`, `:704`), `_PREFETCH_CHILD_POLICY` (walker seam :630),
`_LIST_RELATION_CHILD_POLICY` (walker default :525), and
`_LIST_ARGUMENT_VISIBILITY_POLICY` (`list_field.py:1444`, `:1497`, plus the
connection's `_sidecar_visibility_policy` — both MATCH files). None of the
five sets `require_unevaluated` (still only `_SIDECAR_RESULT_POLICY`, still
reaching the seal solely through :3038), so `evaluated` is still unreachable
at both sites.

Arm sets probe-read at all six sites: 8/3/6/7/5/6 with ZERO dead arms — the
D5 fix holds through the recompose (only `untrusted` prose changed, no arm
added or removed). The two mismatch artifacts keep their reasons: (a)
`_validate_post_orderset_result` — the KNOWN subsumption (comment intact at
:3054-3064, alias arm correctly absent); (b) `_prepared_visibility_source` —
the source-shape pairing artifact, unchanged: the sole production pairing for
both flag-setting policies is still the unrouted `base_queryset` seed (walker
:562), under which `alias` cannot fire, and the flip trigger (a production
caller pairing EITHER policy with a routed source) is untriggered. What the
drift revises is the gate population's COST side: the family item no longer
owes a prose-consolidation design — the cause-list text is already one
constant — it gates arm sets against the five-policy + routing + alias-shape
+ declared-subsumption model and verifies the constant's composition. Family
`seal-defect-code-wording` stays gate-plus-declaration.

Refreshed fingerprints for this finding: `utils/querysets.py`
`3616927de2bc8a7bead38f255ece8695064d5de0`, `permissions.py`
`72102cc08e19689b61bbf8bb8697b7d86e4ec1a5`, `optimizer/walker.py`
`75f9c6b65ed131913b30db541a5b09b31cc4b96a`.

#### Scoped re-trace (run 7) — I-R5 (CONFIRM)

Still file-local with the population recorded. `SyncMisuseError` (:121, +2)
is outside all code hunks with unchanged bases (`ConfigurationError`,
`RuntimeError`); both siblings keep their bases (`list_field.py` and
`resource_policy.py` are MATCH files). Declarations-not-definitions reasoning
stands.

#### Scoped re-trace (run 7) — I-R6 (CONFIRM)

Rejection stands. `utils/querysets.py::_safe_class_name` (:144, +2) is
outside all code hunks; `exceptions.py` is MATCH, so the contract difference
and the trigger rest on unchanged bodies at both owners.

#### Scoped re-trace (run 7) — D1 (FIXED-owned; holding re-verified)

Disposition: fixed (owned fix `fd39cac6`, in the ledger). Verified at HEAD:
the walker still seeds `base_queryset(field.related_model)` unrouted (:562)
and seals under `policy=policy` (:602) with `_LIST_RELATION_CHILD_POLICY` the
default (:525) and `_PREFETCH_CHILD_POLICY` at the nested-connection seam
(:630) — both carrying `require_shared_alias=True` (probe-asserted flags),
so the owned fix's verdict holds on BOTH paths. The seal arm deciding it is
untouched code (the seal-body hunks are comment-only). The walker drift
(53a50bf7 name-memo region :261-450 plus prose) never enters the child-seal
region. The five permanent live rows resolve at HEAD (visibility :1076/:1100,
re-pinned; multi_db :1594/:1619/:1636, identical) — see the Pending note; the
both-modes gate run is still owed. `## Defects` routing note stays accurate.

#### Scoped re-trace (run 7) — D2 (fixed-concurrent; holding re-verified)

Disposition: concurrently fixed (unchanged). `allow_sliced` still has zero
hits across the package, the glossary and spec-034 at HEAD (re-swept). The
glossary half keeps its fixed sentence (`Prefetch alias threading`, :1558,
intact); the spec-034 half is untouched in range. Worker 0 homes the record,
not new work.

#### Scoped re-trace (run 7) — D3 (RESOLVED-fixed stands; prose note DISCHARGED by the drift)

Disposition: resolved-by-landing (unchanged) — and the drift discharges the
one open note adjudication-3 left. The `require_unevaluated` bullet
(:2781-2795) no longer reasons from "the list field invoked that ordering
method one step earlier": it now states the rule for every post-sidecar
result (`_SIDECAR_RESULT_POLICY`) — a public `FilterSet.apply_*` or
`OrderSet.apply_*` return, on the list field and the Relay connection alike.
The "true instance, now an incomplete one" qualification is therefore gone;
the prose matches the resolved state. The `reject_combined` bullet moved the
same way ("on the list field and the Relay connection alike, wherever a list
argument is active"). The glossary projection moved with the code (*Sealed
execution queryset*, :1893, now states the post-sidecar `evaluated` refusal).
No consolidation ever depended on D3. Worker 0 homes the record; the family
item inherits no stale note.

Refreshed fingerprints for this defect's record: `utils/querysets.py`
`3616927de2bc8a7bead38f255ece8695064d5de0`, `docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`.

#### Scoped re-trace (run 7) — D4 (fixed-concurrent; holding re-verified)

Disposition: concurrently fixed (unchanged). The `base_queryset` docstring
(:248-262, +2) keeps the repaired wording and the body is byte-identical to
the measured tree (region outside all code hunks). No re-run needed or owed:
the exact bytes adjudication-1 measured are the HEAD bytes. Worker 0 homes
the record.

#### Scoped re-trace (run 7) — D5 (fixed-concurrent; zero dead re-derived)

Disposition: concurrently fixed (unchanged), re-derived against the new tree.
The arms probe reads all six arm sets from the AST at HEAD bytes: 8/3/6/7/5/6
with zero dead arms anywhere — the D5 fix holds through the rename (kept) and
the recompose (prose-only). `_raw_list_source_message`'s docstring keeps the
repaired enumeration (now correctly including `combined` among the
switched-off codes). The fallback contract holds: any code the seal gains
without an arm still renders as the framework defect `_defect_message` names
— the raw-list site's `subject` argument changed wording (`f"The {name}
{origin}"`) but the fallback body is untouched, and its oracle
(`test_unrendered_defect_code_says_so_instead_of_mislabelling`, AST-identical
at :5150) renders through the dispatcher directly, never through the site.
Family `seal-defect-code-wording`; routing note stays accurate. Worker 0
homes the record.

Worker-2 D1-verification defects, observed (outside the F/D scope, one line
each for Worker 0): D-W2-a is fixed and its holding re-verified — both runner
docstrings name the walker's actual policy pair (`_PREFETCH_CHILD_POLICY` /
`_LIST_RELATION_CHILD_POLICY` at :4148/:4150 and :4403). D-W2-b is fixed and
its holding re-verified — the restated premises are intact (the `_SealPolicy`
`reject_sliced` bullet untouched; the walker licence comments at :567/:577
intact; the glossary sentence at :1558 intact). Worker 0 homes the records.

#### Scoped re-trace (run 7) — O1 (observed, new): `_defect_message` says "never the wording"

D4-class prose defect, minor, found while tracing the recompose. The
`_defect_message` docstring (:3829-3843) states: "Each site owns its own prose
... what is shared is the dispatch and the exhaustiveness, never the wording."
That sentence was true when written; the drift shares the untrusted cause-list
+ advice wording across all five arms via `_UNSEALABLE_STATE_CAUSES`, whose
own comment states the new rule ("the cause list and advice stay one text so
no surface names fewer causes than the seal refuses"). A next author honoring
"never the wording" would un-share the constant. Per the D4 rule (a wrong
stated reason is worse than none), the sentence owes a one-clause repair
(per-site subject + detail framing stays per-site; the cause list + advice is
constant-owned). No behavior is affected; no consolidation depends on it.
**Routes to:** `utils/querysets.py::_defect_message` docstring. Family
`seal-defect-code-wording`. Needs a named owning card at closeout (Worker-0
homes; I never edit the plan).

Not a defect, recorded so Worker-2 sees it was considered:
`_prepared_visibility_source`'s docstring still summarizes sealability as "(a
plain `sql.Query`, a Django row iterable, a pending deferred filter in the
exact shape Django writes)". That parenthetical is a positive summary, not the
cause enumeration the constant owns, and no drift hunk touches it — it stands
as written.

#### Scoped re-trace (run 7) — enumeration: two new names, homes proposed

- `_UNSEALABLE_STATE_CAUSES` (:3733) → adopt into family
  `seal-defect-code-wording` (new index row; it IS the wording single-source:
  5 executable arms + 1 import + 1 prose cite, zero test reads of the symbol
  itself). Challenge: "an eighth unsealable cause must be named" → 1
  definition (the constant) + 7 literal oracles move with it.
- `_sentence_start` (:3724) → file-local: "capitalize a refusal lead without
  touching the rest". Challenge: "a second refusal-lead shape must capitalize
  differently" → 1 definition; readers are exactly the 4 in-file refusal sites
  (:3620/:3718/:3752/:3769). No second site after the matrix (package-wide
  sweep: no other capitalization helper for refusal leads; `str.capitalize`
  would lowercase the rest and is the wrong primitive).
- Matrix twin census stays 6 pairs: the drift adds one sync function and zero
  async, so no new colored pair exists to compare.

#### Scoped re-trace (run 7) — the `origin` thread: a consumer parameter, not a definition

Judgment requested by the dispatch. The thread adds NO definition:
`_row_source_model(state, origin)` (required positional),
`normalized_row_source(value, *, origin=...)` (keyword, defaulted),
`_readable_queryset_state(value, origin=...)` (defaulted),
`_raw_list_source_message(defect, name, origin)` (required positional). The
change challenge "a new origin must be named" forces ZERO definitions to move
— a caller passes a string. There is exactly ONE non-default caller
package-wide: `types/resolvers.py:579`
(`normalized_row_source(cached, origin=prefetch_origin)`); every other
production call site (`resource_policy.py:1051`, the in-file chain,
`materialized_rows`' default read) and every test call site keeps the default.
(The unrelated `origin=` hits — `FilterGenerationProvenance`,
extension `_OriginAndModel`, `types/base.py` — are a different vocabulary with
a different owner, excluded with reason.) F2's "distinct behavior" note (the
raw-list rule asks who owns the slice, not who may see the rows) is confirmed
and sharpened: the new `origin` docstring paragraph states the same split for
refusal attribution (prefetch cache vs resolver return). No holding-family
consequence beyond the `sealed-execution-queryset` consumer census gaining one
member (named in the family section).

#### Scoped re-trace (run 7) — probes (read-only; no workspace, no pytest)

No source-mutating proof was needed (nothing here mutates source), so no
disposable workspace was built and no workspace run id exists. No pytest was
spent (not authorized; every claim is decided by HEAD-byte inspection). Four
read-only pure-AST probes over `git show` bytes in `/tmp/stale7-probes/`
(not in the repo; contents: `enumerate.py` → 141 = 103+6/7/25 at baseline,
143 = 104+6/7/26 at HEAD, additions exactly `_sentence_start` +
`_UNSEALABLE_STATE_CAUSES`; `arms.py` → 5 seal calls with routing at :3038
only, 6 fields, 7 policies with identical flags; `arms2.py` → arm sets
8/3/6/7/5/6; `oracles.py` → the three oracle bodies AST-identical across the
range). Re-runnable by Worker-2 from the descriptions; nothing below is
trusted from the record alone.

#### Scoped re-trace (run 7) — `## Pending execution` (entries 1-3 re-stated)

Entries 1-3 above stand as history; state now:

1. Entry 1 (the five D1 live node ids): CONFIRM + re-pin. All five resolve at
   HEAD — `test_products_visibility_api.py`
   `test_planned_prefetch_child_may_not_pin_its_own_connection` :1076 and
   `test_planned_prefetch_child_still_serves_rows_when_the_hook_only_narrows`
   :1100 (file drifted, bodies outside the D1 hunks), `test_multi_db.py`
   :1594/:1619/:1636 (identical lines). The both-modes gate run is still owed,
   and the sharded mode still needs the maintainer's word. Still `proof:`-typed.
2. Entry 2 (focused gate run over the three oracle suites): CONFIRM unchanged.
   All three paths resolve at HEAD. The F9-exercise expectation is intact
   (`is_async_queryset_adapter` still reads 7 + 9 = 16 lines across the two
   suites). Still `gate:`-typed.
3. Entry 3 (arms witness): the adjudication-3 successor path dangles by design
   (its blob pins tripwire-refuse this tree — the pins work). The expectation
   is re-derived HERE, not trusted: `sites with a mismatch: 2/6` with zero
   dead arms and arms 8/3/6/7/5/6 (rows argued in I-R4 above). Still
   `gate:`-typed. No successor probe was written: run-7 protocol retires new
   `docs/dry/temp-tests/` scratch (legacy scopes are read-only evidence), and
   a successor's home needs a Worker-0 decision — named below, not decided
   here.

#### Scoped re-trace (run 7) — family index and ledger consequences (Worker-0 routes; I never edit the plan)

No `## Owned changes` row (zero production edits). Consequences, explicitly:

1. `seal-defect-code-wording` (open): (a) the untrusted-arm PROSE consolidated
   concurrently (5 spellings → 1 constant) — the family item verifies, it does
   not redo; its gate still gates arm SETS; (b) adopt
   `_UNSEALABLE_STATE_CAUSES` as an owned member (new index row proposed
   above); (c) adopt the 7 new literal oracles (6 cause-list + 1 origin lead)
   as the wording pins; (d) home O1 (the "never the wording" sentence).
2. `sealed-execution-queryset` (open): (a) the family sweep gains a 5th
   candidate `.query` read to classify (`extension.py:1237`, combined
   passthrough); (b) the `normalized_row_source` consumer census gains the
   types/resolvers prefetch caller (consumer, not a definition).
3. `one-sync-boundary` (VERIFIED — flagging, not reopening): the consumer
   census moved 6 → 5 files (`1b6a09b1` removed schema.py's import + 3 calls;
   the replacement window machinery is classified above as neither definition
   nor enforcement site). Definition count unchanged; the verified verdict
   stands subject to Worker-0's call on whether the census move needs a
   family-record note at closeout.
4. `post-set-apply-result-validation` (open): D3's adjudication-3 prose note
   is discharged — the family item inherits no stale note.
5. `child-queryset-alias-inheritance`, `awaitable-refusal-and-disposal`,
   `recomposition-illegal-source-rejection`, `related-object-visibility-recheck`,
   `async-only-queryset-row-adapter`, `queryset-seed-and-model-read` (all
   open): nothing moves (re-pins only).
6. `field-value-coercion`, `sync-boundary-recourse-wording` (rejected):
   rejections re-verified, triggers untriggered; nothing moves.
7. New file-local row proposed: `_sentence_start` refusal-lead capitalization
   (challenge + 4-reader census above); alternatively the wording family
   adopts it — Worker-0's call.
8. Entry-3 successor probe: needs a Worker-0 decision on where a read-only
   successor lives under the retired-scratch rule (legacy scopes are
   read-only; my `/tmp` probes are cited by content, not by path).

#### Scoped re-trace (run 7) — item state

Zero production edits, zero test edits, zero new tracked files. The
item-scoped diff vs
`ITEM_BASELINE=8f8ca0fc05bba066755221150fe33d3b4d99a9bb` holds this append plus
the `Status:` swap (verified before finishing; the target's worktree dirt is
the pre-existing hunt migration, untouched by me — worktree blob still
`8fc556d5`). `uv run ruff check` / `ruff format` not run: no `.py` file was
edited (the layout script's `.md` scaffold needs nothing — the append carries
no cross-file links). No workspace built (nothing mutates source); the one
authorized focused shared-tree pytest was not spent — every claim here is
decided by HEAD-byte inspection plus the four read-only AST probes.
`FAKESHOP_SHARDED=1` and Postgres cells stay `unverified`. Concurrent dirt
left alone. HEAD `0c0537e2` at start and finish — unmoved throughout.

## Independent verification (Worker-2) — stale7 re-trace

Verdict: `verified`. Scoped run `0.0.15 2026-09-28-7`, HEAD
`0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62` at start and finish, unmoved.
Target HEAD blob `3616927d`, worktree `8fc556d5` (hunt dirt, concurrent work);
every claim below traced at HEAD bytes via `git show HEAD:<path>`,
`git rev-parse HEAD:<path>`, and `git grep`, plus read-only AST probes over
`git show` bytes in `/tmp/w2-verify/` (cited by content; OS temp, rides with
the scratch-custody closeout decision). No workspace built, no workspace run
id exists, no pytest spent: nothing here mutates source and every claim is
decided by HEAD-byte inspection. The dispatch brief already summarized W1's
dispositions, so true blindness was unavailable; every number below was
re-derived by my own commands, never trusted from W1's record.

### Own trace (re-derived before reconciling)

Drift hunks, own derivation. `git diff 5ee86193..0c0537e2 --
django_strawberry_framework/utils/querysets.py` is one commit (`982537c3`),
63+/35-: (1) the `origin` thread through `_row_source_model` (now `(state,
origin)`) / `normalized_row_source` (now `(*, origin=...)`) /
`_readable_queryset_state` (now `(value, origin=...)`) /
`_raw_list_source_message` (now `(defect, name, origin)`) with new
`_sentence_start`; (2) new `_UNSEALABLE_STATE_CAUSES` with the three in-file
untrusted arms recomposed onto it; (3) the `_SealPolicy` docstring widened
from post-OrderSet to every post-sidecar result (both the
`require_unevaluated` and the `reject_combined` bullets); (4)
module-docstring + prefetch-docstring rewords and two provenance-word comment
deletions (`:3494`/:3504). Consumer files re-derived from the same range:
`permissions.py` (import + two untrusted arms + one docstring),
`types/resolvers.py` (+3 `prefetch_origin` lines + one `origin=` call),
`schema.py` (`1b6a09b1` removed the `run_in_one_sync_boundary` import + 3
calls), `optimizer/extension.py` (combined passthrough `:1237`), plus
prose-only drifts. Regions outside these hunks are byte-identical to the
adjudicated bytes.

Per-finding expectations, own: CONFIRM F1 (3 definitions; both inline sites
whole-drift-is-line-1, disposal region untouched), F2 (1 owner; exclusivity
re-derived — `models.QuerySet(` outside 0, `sql.Query` touches outside 0,
executable truth-reads outside 0; `_seal_or_defect` 5 in-file calls, zero
outside; 6 policy fields, 7 constants with byte-identical flags; defect-code
set same closed 9 in same order), F4 (2; MATCH file; seal `sliced` arm
untouched), F5 (2; `types/resolvers.py` drift above the definition, seed/color
axes untouched), F6 (rejection stands; trigger untriggered — production
callers still the in-file `:4374` + `write_values.py:313`), F7 (rejection
stands; recourse literals byte-identical), F8 (2 mechanisms; enforcement
sites re-pinned, walker seals intact), F9 (no production reader; 9 + 7 = 16
test lines), F10 (rejection stands; MATCH file), F12 (all live rows;
superseded stay superseded), I-R1/R2/R3/R5/R6 (bodies unchanged, triggers
untriggered), D1/D2/D4/D5 holdings; REVISE F3 (arm sets identical, prose
authorship moved), I-R4 (rows stand, gate cost revised), F11 (consumer files
6→5, conclusion stands), D3 (prose note discharged). New O1 is a real
D4-class prose defect routing to
`utils/querysets.py::_defect_message`.

Three judgments the dispatch names, own answers. (1)
`_UNSEALABLE_STATE_CAUSES` moves authorship only, not any definition count:
C12 still forces 1 definition with 6 hand-revisited sites — the five
spellings were per-site prose inside the message sites, never counted as five
definitions, and are now 1 constant + 5 composers. (2) `origin` is a consumer
parameter, not a definition: "a new origin must be named" forces zero
definitions to move; exactly one non-default caller package-wide
(`types/resolvers.py:579`); the unrelated `origin=` vocabularies
(`FilterGenerationProvenance`, extension `_OriginAndModel`, `types/base.py`)
are excluded with reason. (3) F11's 6→5 census moves nothing the verified
`one-sync-boundary` verdict rests on: still 1 definition, still 5 direct
`sync_to_async` sites with byte-identical shapes and the same
different-contract classification, and the replacement window machinery
(`ThreadPoolExecutor`/`SyncToAsync`/`ThreadSensitiveContext`) answers
per-window thread/connection isolation, not the consumer-hook rule — neither
a second definition nor a new enforcement site.

Enumeration, own instrument (`ast.Module.body` assigns-only constants):
baseline sync 103 + async 6 + classes 7 + const-assigns 25 = 141; HEAD sync
104 + async 6 + classes 7 + const-assigns 26 = 143. Additions exactly
`_sentence_start` + `_UNSEALABLE_STATE_CAUSES`; zero removals, zero renames
— member-by-member delta AGREES. Homes: `_UNSEALABLE_STATE_CAUSES` into
family `seal-defect-code-wording` (it IS the wording single-source; challenge
"an eighth cause must be named" → 1 definition + 7 literal oracles);
`_sentence_start` file-local ("capitalize a refusal lead without touching the
rest"; readers exactly the 4 in-file sites `:3620`/`:3718`/`:3752`/`:3769`;
`str.capitalize` lowercases the rest and is the wrong primitive).
Matrix: no axis reopens beyond the drift scope — no new cross-flavor policy
(the constant IS the consolidation), no new colored pair (one sync function,
zero async added), no new ungated derived fact, no new round-trip half, no
new medium (glossary moved with code, the legitimate shape), no new omission.

### Reconciliation (every difference, explicitly)

AGREE on all 12 findings, all 6 I-R rows, all 5 D holdings, O1, both
enumeration homes, and the matrix. Zero differences of verdict or count. One
trivial census note, immaterial: W1 counts "1 prose cite" for the constant; I
find 2 (`querysets.py:2424` + `permissions.py:400` docstrings) alongside the
5 executable arms + 1 import and zero test symbol-reads. No home, count, or
verdict moves on it.

### Fingerprints (own method: `git rev-parse HEAD:<path>`, never mixed)

All 22 HEAD blobs re-derived and MATCH W1's table digit-for-digit:
`querysets.py` `3616927d`, `auth/mutations.py` `d1a59c44`, `routers.py`
`7d5e4814`, `tests/utils/test_querysets.py` `73e7a6c2`, `permissions.py`
`72102cc0`, `connection.py` `4894f90f` MATCH, `nested_fetch.py` `4d8d37a7`
MATCH, `types/resolvers.py` `72d62dc4`, `write_values.py` `d28587c7` MATCH,
`rest_framework/resolvers.py` `0d302782`, `write_transaction.py` `eca9ad4d`
MATCH, `mutations/permissions.py` `54f770ae` MATCH,
`utils/permissions.py` `9889d6fe` MATCH, `walker.py` `75f9c6b6`,
`filters/sets.py` `993e887a`, `GLOSSARY.md` `3413edc3`, `list_field.py`
`21380eb7` MATCH, `resource_policy.py` `4b69e974` MATCH,
`utils/relations.py` `8dbc3fe6`, `plans.py` `cce98531` MATCH,
`exceptions.py` `e06b0b7f` MATCH, `filters/base.py` `ba52351c` MATCH. All 11
MATCH files are byte-identical to `5ee86193` (own `git rev-parse
5ee86193:<path>` comparison). Every STALE cause judged correct:
`auth/mutations.py`/`routers.py`/`rest_framework/resolvers.py` each 1+/1-
line-1 docstring; `tests/utils/test_querysets.py` 151+/77- over `982537c3`
wording oracles + `4667db4f` fixtures; `permissions.py` import + 2 arms +
docstring; `types/resolvers.py` +3/+1 origin call; `walker.py` name-memo
(`53a50bf7`) + `e1ba094e`/`e6a33c46` prose with the child-seal statements
byte-identical at `:525`/`:562`/`:602`/`:630`; `GLOSSARY.md` 4 hunks
(sealed-queryset reword + dup-Status delete + 2 unrelated); `relations.py`
`instance_accessor` docstring-only. The `filters/sets.py` pin correction is
correct: recorded `4ab65a26` is the `24e6b4d3` blob, `5ee86193` holds
`722e0c77`, `29ddc0a8` sits between with a 2-line docstring retouch, the
in-range hunk is 1 comment line — all prose-only, F8's `:2592` edge and F11's
consumer byte-identical. The 7 wording oracles verified at HEAD
(`test_querysets.py:461`/`:753`, `test_permissions.py:1228`/`:1419`,
`test_resource_policy.py:2153`+`:2155` tail, `test_list_field_api.py:2353`,
origin lead `tests/types/test_resolvers.py:1636`); zero test reads of the
constant symbol itself — independent oracles, correctly claimed.

### Family-consequence judgments (Worker-0 routes on these)

Endorse all eight: (1) `seal-defect-code-wording` — concurrent
prose consolidation verified-not-redone, gate still gates arm SETS
(8/3/6/7/5/6 re-derived with zero dead arms), constant + 7 oracles adopted,
O1 homed here; (2) `sealed-execution-queryset` — `extension.py:1237` is a
genuine 5th `.query`-read candidate for the family to classify (named, not
answered), `types/resolvers.py:579` joins the consumer census; (3)
`one-sync-boundary` (verified) — flagged-not-reopened is correct, census
6→5 only, verdict stands subject to Worker-0's closeout-note call; (4)
`post-set-apply-result-validation` — D3 note discharged, family inherits no
stale prose; (5–6) all other open/rejected holdings stand with re-pins only;
(7) `_sentence_start` file-local, wording-family adoption left to Worker-0's
call; (8) entry-3 successor-probe home correctly deferred to Worker-0 (no new
scratch written; retired-scratch rule honored).

### Nothing-else-changed

Window vs `ITEM_BASELINE=8f8ca0fc05bba066755221150fe33d3b4d99a9bb` holds
exactly the plan (Worker-0's) plus this artifact — nothing to re-attribute.
Prior sections untouched (diff vs baseline is the `Status:` swap plus the one
621-line append; baseline artifact 4223 lines, now 4844 + this section). No
production edit, no test edit, no plan edit, no new tracked file, zero `.py`
touched (`--name-only -- '*.py'` empty) so no ruff run owed. Appended prose
checked against AGENTS.md: `path::Symbol` cites present, `path:NN` confined
to this per-cycle artifact (allowed), no process provenance, no cross-file
links (no scaffold owed). No `(Worker-2)` defect beyond O1's endorsement
(O1 stays W1's entry; no new `## Defects` row needed). `FAKESHOP_SHARDED=1`
and pg cells stay `unverified`. Concurrent dirt left alone; no commit.

### Index rows (narrow pass, run 7)

Literal plan-index row texts for the 2 new run-7 enumeration members, transcribed
from `#### Scoped re-trace (run 7) — enumeration: two new names, homes proposed`
and items 1 and 7 of
`#### Scoped re-trace (run 7) — family index and ledger consequences`
(W2-endorsed under `## Independent verification (Worker-2) — stale7 re-trace`).
Mechanical transcription only; Worker-0 owns the plan paste. Address
`dry/dry-file-utils__querysets-stale7/consolidate`. No workspace run, no pytest,
no `.py` touched, no ruff owed; no cross-file links, no scaffold owed.

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| Unsealable-state cause-list wording single-source | `utils/querysets.py::_UNSEALABLE_STATE_CAUSES` | `utils/querysets.py`, `permissions.py` | Family `seal-defect-code-wording` | open (it IS the wording single-source; challenge "an eighth unsealable cause must be named" → 1 definition + 7 literal oracles) |
| Refusal-lead capitalization ("capitalize a refusal lead without touching the rest") | `utils/querysets.py::_sentence_start` | `utils/querysets.py` | File `utils/querysets.py` | file-local (challenge "a second refusal-lead shape must capitalize differently" → 1 definition; readers exactly the 4 in-file refusal sites; alternatively the wording family adopts it) |

### Light confirmation (Worker-2) — index rows, run 7

2/2 rows match their endorsed findings with no correction: row 1 adopts `utils/querysets.py::_UNSEALABLE_STATE_CAUSES` into family `seal-defect-code-wording` with files covered `utils/querysets.py` + `permissions.py` (the importing consumer) and the enumeration challenge "an eighth unsealable cause must be named" → 1 definition + 7 literal oracles; row 2 records `utils/querysets.py::_sentence_start` file-local with the single file, the enumeration challenge + 4-reader census, and the adoption-alternative parenthetical verbatim from item 7; append-only confirmed (the pre-confirm artifact measured exactly the plan-recorded 5018 lines / 329870 B with the 16-line EOF append under `### Index rows (narrow pass, run 7)` as its tail, so the Status swap + EOF append is the whole narrow-pass delta and every prior section stands untouched), the appended text meets AGENTS.md prose rules (`path::Symbol` cites, no process provenance beyond the DRY.md-mandated role labels, no cross-file links so no scaffold owed), and no `.py` was touched so no ruff run is owed — address `dry/dry-file-utils__querysets-stale7/verify-2`, no workspace runs, no pytest, no plan edit, no commit.

## Run-8 scoped re-trace (Worker 1, REOPENED item s16)

Run: 0.0.15 2026-09-30-8. Prior sections above are prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh, CONFIRMs or
REVISEs every prior finding (run-7 CONFIRM set + REVISE F3/I-R4/F11/D3 +
O1), scopes the drift delta, confirms the carried s11 seal-side exclusion
and the `connection-order-ladder` composing tier from this file's side,
and assigns the drift's new shape. Zero production edits; zero tracked
files changed except this artifact.

Method: probes `/tmp/s16/*.py` (`exec_identity2/3.py` per-node
normalized-AST drift classifier, `target_census.py` enumeration,
`seal_census.py` seal/policy/arm census, `reachability.py` entry-3 model),
cited by content. All execution via `workspace.py run
dry/querysets-retrace-s16/consolidate` (copy slot-2, synced 19:05:52Z,
worktree bytes); git reads via `git -C <shared>` through the same runner
(the copy carries no `.git`). The target is never imported (pure AST over
`git show` bytes). No pytest.

### Scope and fingerprints

Drift base `0c0537e2`, HEAD `83998e08` (unmoved at close).

- `0c0537e2:utils/querysets.py` blob `3616927d` (4575 lines, 143
  members) -> `HEAD:utils/querysets.py` blob `392e50d0` (4866 lines,
  158 def/class/assign nodes, 154 unique names). Committed delta
  `0c0537e2..HEAD` on this target is exactly 6 commits: 2
  behavior-bearing + 4 typing-only.
- Behavior-bearing (each read end to end on this target): `5c5e32c5`
  (combined `get_queryset` served as its pk set: `reject_combined` ->
  `rewrite_combined`, `_LIST_ARGUMENT_VISIBILITY_POLICY` deleted,
  `_RAW_LIST_SOURCE_POLICY` gains `rewrite_combined=False`, new
  `_is_model_column` / `_combined_lost_property` /
  `_pk_membership_query_or_defect` / `_COMBINED_WHAT`, seal arm order
  `projection` before `combined`, 217+/68-), `10d2b9cd` (default-order
  read consolidated: new `default_order` / `applied_order`,
  `Combinable` import, 26+/1-).
- Typing-only (every hunk verified: annotations, casts, `@overload`
  stubs, `TYPE_CHECKING`, `@override`, `Generic` bases, one local
  rename, docstring/prose; moves no rule ownership): `999a1aab`
  (11 hunks + 1 docstring sentence documenting the existing
  `coerce_field_value_or_none` fallthrough), `b20277fe` (~100 hunks;
  the one local rename `queryset` -> `candidate`/`sealed` in
  `_prepared_visibility_source` preserves data flow; the 4
  `@overload` stubs and 6 `TypeVar`/`ParamSpec` shells are
  declaration-only; `_SealedPrefetch` sits inside the
  `TYPE_CHECKING` block so the `Prefetch[...]` subscription never
  executes), `dfbea72b` (1 annotation line), `fef11e64` (2 casts
  removed, 1 annotation, 1 reformat).
- Worktree blob `cfc773ba` (4805 lines, 158 nodes) vs HEAD `392e50d0`:
  222+/283-, 76 hunks (default context), every hunk the hunt's
  `truth.*` introspection migration or its companion hardening (see
  attribution below). No `## Owned changes` ledger row names this
  file (section lines 1427-1501 checked; the one `querysets` hit is
  the D1-fix row whose hunk is in `optimizer/walker.py`, landed as
  `fd39cac6`). The trace reads HEAD bytes, never the dirty tree.
- Pre-ff bytes `9aaaad5d` (`On (no branch): dry-0015 pre-ff snapshot`,
  stash): target blob `8fc556d5` (4523 lines, 143 nodes: 103+6/7/27).
  Its name-delta vs base is IDENTICAL to worktree-vs-HEAD
  (`+_ROUTING_SCALAR_TYPES`, `+_routing_repr`, `-_safe_class_name`,
  `-_safe_routing_repr`): the same hunt migration carried forward.
  Read-only evidence, never applied.
- `ITEM_BASELINE=85b01ebe470a0aeefcfd4a137be7046cc3259adf` (resolves;
  before-copy pinned).

Worktree dirt attribution (all 76 hunks grouped by content; all
hunt-migration family, zero owned, zero concurrent-maintainer):

- Mechanical `truth.*` migration (~62 hunks): introspection spellings
  replaced by `truth.kind` (x60), `truth.name` (x22),
  `truth.instance_state` (x15), `truth.is_subclass` (x8),
  `truth.instance_dict` (x7), `truth.render` (x5),
  `truth.static_attr` (x4), `truth.qualname`/`truth.mro`/
  `truth.module`/`truth.class_dict` (x2 each), `truth.text`/
  `truth.is_instance` (x1 each). Removed-line profile:
  `__getattribute__` x33, `__dict__` x22, `repr(` x12, `issubclass`
  x10, `type(` x10, `__name__` x5, `getattr` x4, `__module__`/
  `__qualname__` x2, `__mro__`/`__repr__`/`__class__`/`__str__`/
  `__getattr__` x1.
- Migration roots (3 hunks): `from . import truth` (+ exceptions-import
  narrowing dropping `_safe_arg_repr`/`_safe_type_name`); `from
  django.core.exceptions import FieldDoesNotExist, ValidationError`;
  `TYPE_CHECKING` `BaseIterable`.
- Safe-render rework (4 hunks): local `_safe_class_name` deleted;
  `_safe_routing_repr` -> `_routing_repr` + new
  `_ROUTING_SCALAR_TYPES` (+ the 4 call-site swaps).
- Exception narrowing (2 hunks): coerce `except Exception` ->
  `(ValidationError, TypeError, ValueError, OverflowError)` with the
  `DurationField`/`int(inf)` rationale reword; relation-target
  `except Exception` -> `FieldDoesNotExist`.
- Router-guard removal (1 hunk): `_snapshot_routing_intent`
  try/except-`BaseException` -> bare `resolve` call.
- Fallout (4 hunks): `_template_params_defect` signature reformat;
  `_DIRECT_RHS_TRUSTED_MRO` frozenset -> tuple; combined-child
  `cast` + comment; guard-history comment reworded timeless.

### Drift delta — per-input freshness (22 STALE, 0 MATCH)

Every fingerprinted input drifted (the typing wave touches the whole
package). Each STALE input was re-derived at HEAD bytes via the
per-node normalized-AST classifier (annotations, casts, overload
stubs, `TYPE_CHECKING` blocks stripped; residuals hand-classified)
plus targeted `git grep HEAD` censuses. HEAD blobs + causes +
judgment:

- `utils/querysets.py` `392e50d0` (`5c5e32c5 999a1aab b20277fe
  10d2b9cd dfbea72b fef11e64`): the 6-commit delta above; every
  finding re-derived below.
- `auth/mutations.py` `72595bb1` (`dc0ae008 849f67bc 2915250d
  b20277fe 999a1aab`): two inline `is_authenticated.close()` copies
  became `auth/mutations.py::_close_unawaited` + 2 calls
  (`2915250d`, outcome-identical: getattr-default-`None` + callable
  check under the same `suppress(BaseException)`); `field_error`
  import moved to `utils.errors`; register steps read
  `backing_model_of(meta)`; `derive_register_fields` gains a
  non-`str` `USERNAME_FIELD` guard (`dc0ae008`, register path, out of
  F-scope); F11 boundary import + 6 calls intact. F1 REVISEd (see
  below); the e1 consolidation is NOT in this tree (no commit, both
  greps empty) — its owned form lives in worktree+snapshot only per
  s6, so F1's 3-count persists at HEAD (flag for Worker-0).
- `routers.py` `ef1e2038` (`fef11e64 dfbea72b b20277fe 999a1aab`):
  EXEC-IDENTICAL (67-line drift is pure annotations/imports); the
  inline dispose copy intact. F1's third definition stands.
- `tests/utils/test_querysets.py` `3ff4094a` (`5c5e32c5` only): old
  refusal tests replaced by pk-set rewrite tests; the 3 inventory
  oracles byte-identical (`:5280` `:5302` `:5329`, set-equalities
  `:5320` `:5340`); wording oracles `:461` `:753` intact.
- `permissions.py` `d77c5050` (`dfbea72b b20277fe 999a1aab
  5c5e32c5`): cascade combined arms recomposed onto `_COMBINED_WHAT`
  (`:387` `:455`); `_validate_fields` pure local rename
  (`requested` -> `entries`); renderer docstrings reworded. Arm sets
  5/6 re-derived; 2 cascade `policy=_CASCADE_SEAL_POLICY` edges
  (`:635` `:717`) intact.
- `connection.py` `3d6dd424` (10 commits incl `5c5e32c5 10d2b9cd
  dbf0a870 193f9946`): `_sidecar_visibility_policy` deleted;
  `_finalize_queryset` recomposed onto `applied_order` (`:1730`);
  `_sync`/`_async_connection_resolver` closure split (`fef11e64`);
  `_guard_source_not_pre_sliced` byte-identical (def `:1648`, call
  `:1030`, passed `:1817`); F10 shapes `:1097` `:1143` + union
  admission `:1637` intact; prepared call `:1812` intact; order+filter
  arms still route through `apply_orderset/filterset` (`:1907`
  `:1954`). Last:0/page-arg drift is s1/s15 scope, untouched by
  querysets findings.
- `optimizer/nested_fetch.py` `304e2f3e` (typing only):
  `Generic` bases + `plan` gains an unobservable `raise
  NotImplementedError` (never instantiated); F4's
  `unwindowable_child_queryset_reason` byte-identical.
- `types/resolvers.py` `574e9768` (typing only): `_make_relation_resolver`
  local rename (neutral); `_FieldResolver` alias; `_visible_related_object`
  body byte-identical (def `:407`, 7 calls); direct sites `:642` `:715`
  `:786`; origin caller `:602`; runner calls `:424` `:428` `:447` `:452`
  (default policy).
- `utils/write_values.py` `01a3318c` (typing only): 2 import
  residuals; `type_check_relation_id` `:316` ->
  `visible_related_objects` `:326` chain intact.
- `rest_framework/resolvers.py` `420fc3ca` (typing only):
  `meta.model` -> `backing_model_of(meta)` and `spec.nested_specs` ->
  `_nested_specs_of(spec)` typing-driven restatements (new helper,
  cited regions untouched); consumer `:1519`, composition `:227`
  intact.
- `utils/write_transaction.py` `c0a12b34` (typing only):
  `canonical_pk` annotation-only; `_field_fingerprint` container
  branch inverted (outcome-identical per `dfbea72b`). F6 stands.
- `mutations/permissions.py` `f23eb540`, `utils/permissions.py`
  `e2b46fd7` (typing only): 1 import residual each. F7 stands.
- `optimizer/walker.py` `bdd9c2f1` (`fef11e64 b20277fe 999a1aab
  5c5e32c5`): new `_hint_prefetch_over_pk_set` composing
  `_pk_membership_query_or_defect` + `_COMBINED_WHAT` (`:1424`); new
  `models.QuerySet(` construction `:1426` (consumer, not a second
  sealing body — F2 REVISE note); `_apply_hint` routes through it;
  `_relay_max_results_from_info` import rebinding (same object);
  child-seal region re-pinned (default `:556`, seed `:594`
  unrouted+cast, call `:629`, `policy=policy` `:635`, seam `:663`,
  plain-list `:1188`, wiring `:1824`).
- `filters/sets.py` `3d307402` (typing + `bbe54687` + `e37448e5`):
  relation-identity profiles added (s9 scope); F8 edge byte-identical
  at `:2707`; F11 call `:3628` intact.
- `docs/GLOSSARY.md` `431ca7ba` (6 commits): cascade +
  Sealed-execution-queryset terms reworded with the code; Prefetch
  alias sentence intact at `:1560`. F8 projection holds.
- `list_field.py` `77ddb86c` (9 commits): ZERO `policy=` left (both
  runner calls `:1463` `:1509` take the default — I-R4 REVISE);
  `_selected_ordering` model tier via `default_order` (`:1163`);
  F10 sites `:1361` `:1365` `:1771`; wrap calls `:1466` `:1495`
  `:1512` `:1541`; prepared calls `:1732` `:1782`; order arm routes
  through `apply_orderset` (`:1474` `:1520`); visibility call hoisted
  above the branch (s2-verified, same default policy).
- `resource_policy.py` `47befb3f` (typing only): `@override` only on
  `ResourceLimitExceeded` (bases intact); `check_deadline` local
  rename. I-R5 stands.
- `utils/relations.py` `72e7ff08` (typing only):
  `validate_lookup_expr` unpack rewrite (outcome-identical, guards
  prove non-empty; not a mechanism body); `classify_path` family
  byte-identical. I-R1/I-R2 stand.
- `optimizer/plans.py` `fdc4b1b0` (typing + `10d2b9cd`):
  `effective_connection_order(cursor_field, query, model)` composes
  `applied_order` (`:939` inside `:911`); `_consumer_prefetch_lookups`
  and `_select_path_traversable` byte-identical;
  `order_entry_name_and_direction` recomposed (s11-verified file, out
  of F-scope).
- `exceptions.py` `f27e1f91` (typing only): `@override` only.
  `_safe_class_name` body byte-identical. I-R6 stands.
- `filters/base.py` `e2e683a8` (typing + `57131b99` + `bbe54687`):
  `_coerce_int_in_members` byte-identical (still composes
  `coerce_field_value_or_none`, `:541`); GlobalID node-id composer
  `:898` pre-existed at base (run-7's "three consumers" undercounted
  by one — F6 REVISE corrects the census); new `_coerce_relation_identity`
  composer `:1179`; new `meta.get_field(to_field_name)` `:1125` is a
  single resolution, not a `__`-segment walk (I-R1 population
  unaffected); `resolve_globalid_target_definition` byte-identical
  (I-R2 exclusion holds); `get_model_field` is
  `django_filters.utils` upstream, not a package mechanism body; F6
  trigger untriggered (no `stringified_pks_present` caller outside
  the file + `write_values.py:327`).

### Enumeration at HEAD bytes

`target_census.py` over HEAD bytes: 111 sync + 8 async + 7 classes +
32 const-assigns = 158 nodes, 154 unique names (143 -> 154 unique;
+12 -1). The 4 node-count extras over unique names are the
`@overload` stubs (`apply_type_visibility_sync` x3,
`apply_type_visibility_async` x3: 2 stubs + impl each), which share
their impl's name. Added unique names: `_COMBINED_WHAT`,
`_combined_lost_property`, `_is_model_column`,
`_pk_membership_query_or_defect`, `applied_order`, `default_order`
(rule-bearing, homed below) + 6 `TypeVar`/`ParamSpec` shells
(`_T _R _P _ModelT _RowT _RowT_co`, typing-only, no rules).
Removed: `_LIST_ARGUMENT_VISIBILITY_POLICY` (zero `.py` hits
package-wide at HEAD). `_SealedPrefetch` is `TYPE_CHECKING`-only
(`:134-135` inside the block) and correctly absent from the count.
Stash `8fc556d5`: 103+6/7/27 = 143. Worktree `cfc773ba`:
110+8/7/33 = 158.

Homes for the 6 rule-bearing names (no other new rule surface):

- `default_order` / `applied_order` -> family
  `connection-order-ladder`, composing tier (CONFIRMED from this
  side; see below). No new index row (s11's row already adjusted).
- `_is_model_column` / `_combined_lost_property` /
  `_pk_membership_query_or_defect` -> family
  `sealed-execution-queryset`: parts of the one seal body (the
  rewrite the combined arm dispatches). No new row.
- `_COMBINED_WHAT` -> adopt into family `seal-defect-code-wording`
  like `_UNSEALABLE_STATE_CAUSES` (new index row below).

### CONFIRM verdicts (18, each re-proved at HEAD bytes)

- F4: `_guard_source_not_pre_sliced` byte-identical (`:1648` `:1030`
  `:1817`); F2-adjacent contract difference (`nested_fetch.py`
  degradation vs analyzability verdict) intact on untouched bodies.
- F5: 2 named readers (`types/resolvers.py:407` body-identical, 7
  calls `:651`-`:820`; `utils/querysets.py:4576`) + the default
  (`:4504`) + the DRF consumer (`:1519`) all re-pinned; verbatim
  `get_queryset` origin caller at `types/resolvers.py:602`.
- F7: `sync_pipeline_recourse` untouched; compositions
  `mutations/resolvers.py:207`, `forms/resolvers.py:142`,
  `rest_framework/resolvers.py:227` intact; 4 recourse sentences
  re-pinned (`:71` `:65` `:143` `:398` `:405` across the four homes);
  trigger untriggered; "four clauses differ" regions untouched.
- F8: walker edges re-pinned (`:556` `:594` `:629` `:635` `:663`
  `:1188` `:1824`); licence comments `:596`-`:627` intact;
  `using=parent_db` byte-identical at `filters/sets.py:2707`;
  `using=state.alias` at `permissions.py:704`; glossary projection
  `:1560`; trigger untriggered.
- F9: 2 defs (`:432` `:463` re-pinned) + 2 wrap sites + 2 check sites
  intact; production-reader census still zero (16 test lines only);
  extension unwrap/wrap `:1214` `:1217` + `_result_cache` read
  `:1233` + combinator passthrough `:1282` `:1286` re-pinned; union
  admission `connection.py:1637` intact.
- F10: 3 definitions + 3 test-only readers + 1 union admission
  (`connection.py:1637`) re-pinned; shapes `connection.py:1097`
  `:1143`, `list_field.py:1361` `:1365` `:1771` intact (plus
  `# type: ignore[redundant-expr]` comments).
- F12: all 9 rows re-verified — `_snapshot_routing_intent` (`:2985`)
  callers exactly the 2 in-file (`:3201` `:3234`); `_safe_routing_repr`
  (`:3047`) production readers the seal routing arm only
  (`:3651`-`:3654`); `_routing_hints_equal` untouched (identity-only);
  `_bake_deferred_filter_or_defect` (`:2697`) sole caller the seal
  (`:3700`); `_prefetch_relation_target_or_none` bodies + twin-site
  outcomes untouched; `_GraphWalk` region byte-identical (no code
  hunk in range); `prepared_resolver_source` (`:4777`) callers
  `list_field.py:1732` `:1782` + `connection.py:1812`;
  `_coerced_manager_queryset` body + entry points untouched.
- I-R1: five-body table byte-identical (`classify_path`,
  `_lenient_traverses_to_many`, connection resolver, plans probe,
  prefetch resolver — none in any drift residual); the new
  `relation_identity_column` path resolves ONE field name
  (`:1125`) via upstream `get_model_field`, not a `__`-segment
  walk — outside the population.
- I-R2: `resolve_globalid_target_definition` byte-identical
  (registry graph, never `get_field`); the new `:1125` single
  resolution is adjacent, not a walk.
- I-R3: executable `models.Manager` reads still exactly the 3
  in-file (`:355` `:4018` `:4338`); one new TEXTUAL hit,
  `relay.py:296`, is a typing-wave annotation, not a
  coercion/verdict (precision note on the record).
- I-R5: twin impl signatures keep parity (`:4368` `:4664`: same
  shape, `async_recourse` sync-only; the 4 overloads mirror it);
  `SyncMisuseError` bases (`:144`) and `ListArgumentError` /
  `ResourceLimitExceeded` bases intact; no new sync/async closure;
  trigger untriggered.
- I-R6: contract difference + trigger rest on two untouched bodies
  (neither file's residuals touch them); trigger untriggered.
- D1: fixed-verdict holds — child policies + seed re-pinned, all 5
  live node ids resolve unmoved (`test_multi_db.py:1594` `:1619`
  `:1636`, `test_products_visibility_api.py:1076` `:1100`).
- D3: resolved-fixed holds — `require_unevaluated` post-sidecar
  bullet intact, both sidecar arms still route through
  `apply_orderset/filterset` (`connection.py:1907` `:1954`,
  `list_field.py:1474` `:1520`); the run-7 spec-050 citation now
  CONTRADICTS the behavior — recorded as O2 (new), the D3 verdict
  itself stands.
- D4: closed-empty stands (no second axle-reading spelling; the
  package-wide order census below is the re-proof).
- D5: arm sets re-derived executably (`reachability.py`):
  8/3/7/6 in-file + 5/6 permissions, digit-for-digit the run-7
  record; zero undeclared mismatches (the validator's
  alias-subsumed-by-routing remains the one declared exception).
- D-W2-a/D-W2-b: holdings intact — `_SealPolicy` bullets (incl.
  `reject_sliced` axis + post-sidecar `require_unevaluated`),
  walker licence comments `:596`-`:627`, glossary `:1560`.
- O1: `_defect_message`'s "never the wording" sentence (`:4084`)
  persists verbatim; the drift makes it doubly false (the
  `untrusted` cause list AND the combined text are now shared).
  Same owner, same one-clause repair (now covering both shared
  texts).

### REVISE verdicts (6)

- F1-REVISED (site record; count stays 3): auth's two inline
  `is_authenticated.close()` copies are now one named
  `auth/mutations.py::_close_unawaited` (3 hits: def + 2 calls in
  `_authenticated_actor_or_none`), outcome-identical under the same
  suppression. Definitions at HEAD: `_dispose_sync_awaitable`
  (owner) + `_close_unawaited` (auth suppression adapter) +
  `routers.py` inline (byte-identical). Both challenge axes
  re-discharged (async-generator/future shapes unchanged). FLAG for
  Worker-0: the plan's e1 "migrated to consumers" record is NOT in
  this tree (no such commit; `_disposed_awaitable` zero hits in
  `auth/mutations.py` at HEAD); per s6 the consolidation lives in
  worktree+snapshot only. F1's 3-count persists at HEAD.
- F2-REVISED (new construction site, verdict stands): one new
  `models.QuerySet(` site, `optimizer/walker.py:1426`, inside
  `_hint_prefetch_over_pk_set` — it constructs around a query the
  seal's own `_pk_membership_query_or_defect` rewrote (composed by
  name, `:1419`), over trusted schema configuration
  (documented in `_combined_lost_property`'s docstring). A consumer
  of the seal's machinery, not a second sealing body. One owner
  stands; the exclusivity record gains this classified site.
  (Truth-read trio + `sql.Query` + hook-invocation censuses
  unchanged: zero outside the file.)
- F3-REVISED (combined arm recomposed; oracles re-pinned): the gate
  (`combined` -> `rewrite_combined` flag + `_pk_membership` rewrite
  + `_combined_lost_property` audit) stays owned; the six
  declarations keep their shape with the `combined` arm now
  composing `_COMBINED_WHAT` at 6 code sites (definition `:3973` +
  `querysets.py:3149` `:4147` `:4268`, `permissions.py:387` `:455`,
  `walker.py:1424`) + 2 prose cites. All 7 cause-list oracles
  resolve (`test_querysets.py:461` `:753`,
  `test_permissions.py:1269` `:1487`, `test_resource_policy.py:2153`,
  `test_list_field_api.py:2357`); combined-wording oracles: 8
  independent literal pins (6 live + 2 `test_connection.py`) plus
  `_COMBINED_WHAT.format` compositions (which pin composition, not
  wording). `reject_combined` zero hits package-wide.
- F6-REVISED (composer census corrected + extended; rejection
  stands): `coerce_field_value_or_none` (body untouched but the
  `999a1aab` docstring sentence) now has FIVE call sites in four
  files — `relay.py:191`, `write_values.py:126`,
  `filters/base.py:541` (`_coerce_int_in_members`, byte-identical),
  `filters/base.py:898` (GlobalID node-id; pre-existed at base, the
  run-7 "three consumers" undercounted by one),
  `filters/base.py:1179` (new `_coerce_relation_identity` chain).
  "One owned translation, WHICH field stays at the caller" holds
  over the larger census. Third contract re-pinned
  (`keyset.py:402` `field.to_python`). Trigger untriggered
  (sole `stringified_pks_present` callers: in-file `:4642` after
  `:4620`'s model gate, `write_values.py:327` after `:316`'s
  `type_check_relation_id`).
- F11-REVISED (direct-site census 5 -> 7; verdict stands):
  consumers still exactly the 5 files (imports + calls re-pinned;
  `schema.py` has prose only, zero composition); direct
  `sync_to_async(` sites gain `schema.py:406`
  (`sync_to_async(window, ...)` + `:394` `async_to_sync(complete)`),
  the completion-window machinery (per-window thread/connection
  isolation for completion-spanning transactions — a different
  contract from the consumer-hook rule, which RUNS INSIDE it per
  `:355`). `async_to_sync` in `auth/mutations.py` (`:841` `:1049`)
  pre-existed at base (reverse direction, outside the census then
  and now). Neither a second definition nor a new enforcement
  site — same verdict, revised census (the s20 family item judges
  the window).
- I-R4-REVISED (runner policy set 5 -> 4; rows/expectation hold):
  `_LIST_ARGUMENT_VISIBILITY_POLICY` deleted;
  `list_field.py` (`:1463` `:1509`) and `connection.py` (`:1900`
  `:1947`) now take `_DEFAULT_SEAL_POLICY`. Complete runner set at
  HEAD: default (list_field x2, connection x2, types/resolvers x4)
  + `_CASCADE_SEAL_POLICY` (permissions x2) + walker child pair
  (default `:556`, seam `:663`). `require_unevaluated` still set
  solely by `_SIDECAR_RESULT_POLICY`, reaching the seal solely via
  the validator (`:3104`, the one `expected_routing` of 5 seal
  calls `:2608` `:3104` `:3897` `:4234` `:4340`); `evaluated`
  unreachable at visibility sites, `routing` unreachable without
  it. Canonical code order moved (`:3475`: `... -> projection ->
  combined -> alias`); arms-per-site expectation 2/6 re-derived
  executably with zero undeclared mismatches.

### Carried cross-file items (fresh evidence from this file's side)

- s11 seal-side exclusion CONFIRMED: `utils/querysets.py:3733` is
  `state.get("_prefetch_related_lookups")` (a snapshot-`__dict__`-key
  read feeding `_sealed_prefetch_related_lookups(lookups, ...)`,
  which takes the lookups as a parameter and contains no attribute
  spelling) and `:3806` is `sealed._prefetch_related_lookups =
  sealed_prefetch` (a clone-write) — both inside `_seal_or_defect`,
  both moving under seal contracts (snapshot discipline + clone
  reproduction), not the `attached-prefetch-lookups-read` read
  rule. Package-wide `_prefetch_related_lookups` census at HEAD is
  exactly the s11 population: live reads `optimizer/plans.py:572`
  (lenient) + `optimizer/walker.py:1432` (strict forward), the two
  seal touches above, rest prose/def-name/comment. Rename-count-2
  for the read rule re-proved.
- `connection-order-ladder` composing tier CONFIRMED:
  `default_order` (`:291`: model's ordering while default ordering
  stands and is truthy) / `applied_order` (`:306`: explicit order
  else that) own the explicit-else-default tier.
  `model._meta.ordering` is read at exactly ONE package site
  (`:304`, inside `default_order`); composers exactly three —
  `optimizer/plans.py:939` (inside `effective_connection_order`),
  `connection.py:1730`, `list_field.py:1163`; zero inline rebuilds
  (`10d2b9cd` removed the connection tail's and nested planner's
  hand rebuilds). Challenges from the owner side: "honor
  `extra(order_by=)`" -> `applied_order` (1) + the list field's
  deliberate non-consumer (documented in `_selected_ordering`);
  "`ordering=None`/cleared handling" -> `default_order` (1).

### Defects (run-8: O1 persisting, O2 new, zero target-behavior defects)

- O1 (persists, strengthened): `_defect_message` `:4084` "never the
  wording" now doubly false (see CONFIRM above). Same owner, same
  one-clause repair extended to both shared texts.
- O2 (new, observed): `docs/spec-050-list_field_arguments-0_0_15.md`
  Edge sentences (`:2121` `:2123`) still pin the pre-`5c5e32c5`
  refusal rule — "A combined queryset is rejected for any non-null
  argument" and "must SEAL to a lazy, unsliced, model-row-shaped,
  non-combined, same-model, same-route plain queryset" — but a
  combinator is now SERVED as its pk set unless the rewrite fails
  (`utils/querysets.py:3769` + `_COMBINED_WHAT`). `5c5e32c5`
  updated spec-045 but not spec-050. Routes to the spec-050 owning
  card (in-flight spec prose); note for family
  `post-set-apply-result-validation`. Neither s1's nor s2's
  artifact flags the spec itself (both quote the old rule text
  only), so this is first-recorded here; Worker-0 dedups.
- D-rows: D1 fixed-verdict holds, D3 resolved-fixed holds, D4
  closed-empty stands, D5 8/3/6/7/5/6 + zero dead re-derived,
  D-W2-a/D-W2-b holdings intact (see CONFIRM). No new
  target-behavior defect.

### Pending execution (3 entries, restated)

1. D1's contract-source set lives in prose + 5 live node ids (all
   resolve unmoved — see F8/D1) — no probe to re-run.
2. Unchanged: no database/alias/dialect surface in this file's own
   probes applies beyond entry 1 (read-only AST; `inapplicable by
   construction` for the rest, judged sound).
3. Arms-per-site expectation 2/6 re-derived executably at HEAD
   (`reachability.py`: 8/3/7/6 in-file + 5/6 permissions, zero
   undeclared mismatches under the declared-semantics model; the
   validator's alias-subsumed-by-routing remains the one declared
   exception).

### Judgment

Coverage complete: 143 -> 154 unique names, every member in a family
row, file-local record, rejection, or the external row; the drift's
6 rule-bearing names homed (2 + 3 into existing families, 1 new
index row); typing shells (`@overload` x4, `TypeVar` x6,
`TYPE_CHECKING` alias) carry no rules. 18 CONFIRM + 6 REVISE, each
re-proved at HEAD bytes with fresh censuses; O1 persisting, O2 new;
zero target-behavior defects. Zero-edit accepted: this artifact is
the whole delta.

### Item-scoped diff state

Own run: this artifact only (append below the run-7
light-confirmation; every prior section untouched). HEAD `83998e08`
unmoved at close. All 22 cited HEAD blobs re-hashed identical at
write time: `392e50d0 72595bb1 ef1e2038 3ff4094a d77c5050 3d6dd424
304e2f3e 574e9768 01a3318c 420fc3ca c0a12b34 f23eb540 e2b46fd7
bdd9c2f1 3d307402 431ca7ba 77ddb86c 47befb3f 72e7ff08 fdc4b1b0
f27e1f91 e2e683a8` (input order as listed). No ruff/mypy owed
(artifact `.md` only; probes `/tmp`-only). No cross-file links, no
scaffold owed.

## Index rows for Worker-0 (run-8)

Mechanical transcription only; Worker-0 owns the plan paste. Address
`dry/querysets-retrace-s16/consolidate`. No pytest, no `.py`
touched, no ruff owed; no cross-file links, no scaffold owed.

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| Combined-queryset what-phrase wording single-source | `utils/querysets.py::_COMBINED_WHAT` | `utils/querysets.py`, `permissions.py`, `optimizer/walker.py` | Family `seal-defect-code-wording` | open (it IS the combined-text single-source; 1 definition + 6 code composers + 2 prose cites; challenge "a seventh combined-error site must name the what-phrase" -> compose, don't respell; 8 independent literal oracles pin the rendered text) |

No other new rows: `default_order`/`applied_order` and the three
combined-rewrite helpers are members of already-indexed families
(`connection-order-ladder`, `sealed-execution-queryset`);
`walker.py:1426` is a consumer, not a definition; the e1-divergence
flag (F1-REVISED) proposes no row change.

Status: ready-for-verification/1

## Run-8 verification (Worker 2)

Verdict: `verified`. Every W1 verdict row (18 CONFIRM + 6 REVISE) survives on
my independent evidence; the 7 notes below are pin/citation precision, none
moves a verdict. Prior sections untouched; the header swap above plus this
append is the whole delta.

Method. All execution via `workspace.py run dry/querysets-retrace-s16/verify`
(copy slot-3, synced 19:50:02Z, fresh at every run; the copy carries no
`.git`, so all git reads are `git -C <shared>` through the same runner).
HEAD `83998e08` at start and finish, unmoved. Target never imported: pure AST
over `git show` bytes plus `git grep` with directory pathspecs. Own probes in
`/tmp/w2-run8/` (`probe_enum/drift/execid/execid2/residuals/seal/policy/f1/f2/
f3/arms/oracle_ident`), cited by content. No pytest; read-only probes only.
The dispatch brief summarized W1's dispositions, so true blindness was
unavailable; every number below was re-derived by my own commands, never
trusted from W1's record.

Scope, re-derived. `0c0537e2..HEAD` on the target is exactly 6 commits:
`5c5e32c5` (+217/-68, 23 `-U0` hunks, all at old :2813+ — policy record,
constants, validator, sidecars, seal, message sites, one runner-docstring
reword), `10d2b9cd` (+26/-1: `default_order`/`applied_order` +
`Combinable` import), and 4 typing-only. My executable-identity probe
(strips annotations, type params, `TYPE_CHECKING`, `@overload` stubs,
`cast()`, docstrings; keys assigns by target name) reports zero normalized
differences for `dfbea72b` and `fef11e64`, and exactly one residual each for
`999a1aab` (`_seal_or_defect`: `rebuilt_query` -> `rewritten` + cast-back,
outcome-identical) and `b20277fe` (`_prepared_visibility_source`:
`queryset` -> `candidate`/`sealed` + cast, data flow preserved). 2
behavior-bearing + 4 typing-only CONFIRMED by a different instrument.

Enumeration, own instrument (`ast.Module.body`, assigns-only constants).
Base: 104 sync + 6 async + 7 classes + 26 consts = 143 unique. HEAD: 111
sync + 8 async + 7 classes + 32 consts = 158 nodes, 154 unique (+12 -1).
Added: `_COMBINED_WHAT`, `_combined_lost_property`, `_is_model_column`,
`_pk_membership_query_or_defect`, `applied_order`, `default_order` +
6 `TypeVar`/`ParamSpec` shells. Removed: `_LIST_ARGUMENT_VISIBILITY_POLICY`
(zero `.py` hits package-wide). The 4 node extras are the `@overload` stubs
(3 defs each for the two visibility runners). `_SealedPrefetch` is
`TYPE_CHECKING`-only and correctly absent. 143 -> 154 CONFIRMED. (Line
counts 4574/4865 vs W1's 4575/4866: `splitlines` vs `wc -l`; immaterial.)

CONFIRM rows, each re-proved (own pins): F4 (guard def :1648, direct call
:1030, passed-as-guard :1817; body identical, def-line annotation only —
note 2; `nested_fetch.py` degradation body identical), F5 (`:407` + 7 calls
`:651`-`:820`, `:4504`, `:4576`, DRF `:1519`, origin caller `:602`), F7 (4
sentences `:71` `:65` `:143` `:398`, compositions `:207` `:142` `:227),
F8 (`:556` `:594` `:629` `:635` `:663` `:1188` `:1824`, licence comments,
`:2707`, `permissions.py:704`, glossary `:1560`), F9 (def `:463` the only
package hit; 7 + 9 = 16 test lines; wrap `:1466` `:1495` `:1512` `:1541`,
unwrap/wrap `:1214` `:1217`, `:1233`, `:1282` `:1286`; `:432` pin — note 3),
F10 (`:1097` `:1143` + union `:1637`, `list_field.py` zero direct refs,
composers `:1361` `:1365` `:1771` + `resource_policy.py:1258`), F12 (all 9:
snapshot `:2985` callers exactly `:3201` `:3234`; routing-repr readers only
`:3651`-`:3654`; bake `:2697` sole caller `:3700`; prepared `:4777` callers
`:1812` `:1732` `:1782` `:4832` `:4858`; `_GraphWalk` region has no behavior
hunk — all `5c5e32c5` hunks sit at old :2813+), I-R1 (five-body table
executable-identical — mechanism hunks are annotation/cast-only; `:1125` is
a single `get_field` resolution; `get_model_field` is `django_filters`
upstream), I-R2 (`resolve_globalid_target_definition` in no drift hunk),
I-R3 (executable `models.Manager` exactly `:355` `:4018` `:4338`;
`relay.py:296` is a variable annotation, not a verdict), I-R5 (twins `:4368`
`:4664` parity with `async_recourse` sync-only, 4 overloads mirror it;
bases intact; no new colored pair — the +2 async nodes are overload stubs),
I-R6 (both bodies executable-identical), D1 (5 node ids resolve unmoved),
D3 (post-sidecar bullet `:2845`-`:2847` intact; sidecar arms route through
the shared seal `:1907` `:1954` + list field), D4 (repaired docstring, body
`manager.using(using).all() if using is not None else manager.all()`
intact — confirmed on direct evidence, note 5), D5 (arm sets 8/3/7/6 +
5/6 re-derived by my own AST reader with zero dead arms; validator
`fromkeys` 6 + `combined` + `routing`, alias-subsumption comment intact),
D-W2-a/b (runner docstrings name the policy pair — the one `5c5e32c5`
runner hunk is the combined-service docstring reword; walker licence
comments, glossary `:1560`), O1 (`:4084` "never the wording" verbatim,
now doubly false — cause list AND combined text shared).

REVISE rows: F1 (auth `_close_unawaited` def `:528` + 2 calls `:599` `:602`,
`getattr`-default-`None` + callable under the same `suppress(BaseException)`;
`is_authenticated.close()` zero hits; routers inline `:324` intact; count
stays 3 — and the e1 flag below), F2 (outside-target `models.QuerySet(`
exactly 1: `walker.py:1426`, constructing around the seal's own
`_pk_membership_query_or_defect` rewrite composed by name at `:1419` —
a consumer, not a second sealing body; `sql.Query`/truth-read trio/`get_queryset`
censuses re-derived: zero outside), F3 (def `:3973` + 6 code composers
`:3149` `:4147` `:4268` `:387` `:455` `:1424` + 2 prose cites `:3117` `:409`;
all 7 wording oracles resolve — `:461` `:753` `:1269` `:1487` `:2153`
`:2357` + origin lead `:1636`; 8 combined literal pins re-derived: 6 live
+ 2 `test_connection.py`; test `.format` uses pin composition, not wording;
`reject_combined` zero hits), F6 (5 call sites `:191` `:126` `:541` `:898`
`:1179`; `:898` pre-existed at base `:840` — the run-7 undercount correction
verified; `keyset.py:402`; trigger untriggered), F11 (composing consumers
exactly 5 files — `consumers.py:1612` and `schema.py:355` are prose-only,
the latter explicitly stating the boundary work runs INSIDE the window;
direct sites 5 -> 7 per W1's per-call convention — note 4; `types` x3 +
`testing` x2 shapes intact; auth `async_to_sync` pre-existed at base),
I-R4 (runner set 5 -> 4: default (`list_field.py` zero `policy=`,
connection `_sidecar_visibility_policy` deleted with zero hits,
`types/resolvers.py` x4) + cascade x2 + walker pair; `require_unevaluated`
solely `_SIDECAR_RESULT_POLICY`; seal calls `:2608` `:3104` `:3897` `:4234`
`:4340` with `:3104` the one `expected_routing`; canonical order
`projection` before `combined` at `:3475`; the pairing artifact holds —
the flag-setting policies' sole production pairing into the source seal is
the walker's unrouted `:594` seed; flip trigger untriggered).

Entry-3 re-derivation. My own arm reader + policy census: 8/3/7/6 in-file +
5/6 permissions, zero dead arms anywhere; the 2/6 expectation re-derived
(validator alias = the one declared subsumption; prepared-source alias =
the pairing artifact). The gate should expect `2/6` with zero undeclared
mismatches.

Carried items, fresh evidence: s11 seal-side exclusion CONFIRMED (`:3733`
snapshot-key read into the parameterized seal helper, `:3806` clone-write,
both inside `_seal_or_defect`; package-wide census exactly the s11
population: `plans.py:572` lenient + `walker.py:1432` strict-forward live
reads, rest prose/def-name/comment — rename-count-2 re-proved).
`connection-order-ladder` composing tier CONFIRMED (`model._meta.ordering`
at exactly one package site `:304`, inside `default_order`; composers
exactly three — `plans.py:939` inside `effective_connection_order`,
`connection.py:1730`, `list_field.py:1163`; zero inline rebuilds — the only
residual match is a comparison, not a rebuild; both owner-side challenges
discharge at 1 definition each with the list field's documented
extra-ordering non-consumption).

F1 flag adjudication. Verified: no "migrated to consumers" commit exists
(`log --all --grep` empty); `_disposed_awaitable` has zero hits in
`auth/mutations.py` at HEAD (package-wide only the def + 3 in-file
callers); the worktree DOES carry the consolidation (`auth/mutations.py`
imports it at `:75` and composes at `:529`). Per s6 it lives in
worktree+snapshot only (snapshot `9aaaad5d`, target blob `8fc556d5`,
verified to exist). Moves no verdict: the HEAD trace is the committed
record and F1's 3-count persists there; e1 stands as the plan record for
uncommitted work. No row change proposed or owed.

O2, new: observation stands with corrected pins (note 1). Both stale Edge
sentences verified at HEAD (`:2123` combined-rejected, `:2125`-`:2126`
must-SEAL-non-combined); `5c5e32c5` touched spec-045 and no commit in range
touched spec-050; s1's run-8 never mentions spec-050 and s2 cites it only
as an unchanged fingerprint input — first-recorded here, Worker-0 dedups.
Routing endorsed: spec-050 owning card (in-flight prose contradicting
landed behavior at `utils/querysets.py:3769` + `_COMBINED_WHAT`), note for
family `post-set-apply-result-validation`.

Index row judgment. The 1 row is exact replacement text: family name
parallels the run-7 cause-list row; owner/files/holding correct and
complete (all 6 code composers across the 3 files covered); the parenthetical
counts verified (1 + 6 + 2; 8 oracles); the challenge/trigger well-formed
(a seventh site composes). "No other new rows" endorsed (ladder tier under
s11's row, rewrite helpers inside the one seal body, `:1426` a consumer,
e1 flag row-less).

Worktree attribution, all 76 hunks (222+/283-, default context):
mechanical `truth.*` migration with added/removed profiles digit-for-digit
W1's table (`truth.kind` x60 down to `truth.text`/`truth.is_instance` x1;
`__getattribute__` x33 down to the five x1 dunders), plus migration roots
(`from . import truth`, the `FieldDoesNotExist, ValidationError` import,
`BaseIterable`), safe-render rework (local `_safe_class_name` deleted,
`_safe_routing_repr` -> `_routing_repr` + `_ROUTING_SCALAR_TYPES` + 4
call-site swaps), exception narrowing (coerce 4-tuple exploded one-per-line
with the `DurationField`/`int(inf)` rationale; relation-target
`FieldDoesNotExist`), the `_snapshot_routing_intent` guard removal, and
fallout (`_template_params_defect`, `_DIRECT_RHS_TRUSTED_MRO`
frozenset->tuple, combined-child cast, timeless comment). Zero owned: the
drift's 6 commits are maintainer fix/typing, none a DRY-owned change, and
the dirt is uncommitted hunt migration. Name-delta vs HEAD identical in
snapshot `8fc556d5` (same migration carried forward). Read-only evidence;
nothing applied.

Fingerprints, three states plus closeout. Base `0c0537e2` target
`3616927d`; HEAD target `392e50d0`; worktree `cfc773ba`; snapshot
`8fc556d5`. All 22 HEAD blobs re-hashed identical at write time
(`392e50d0 72595bb1 ef1e2038 3ff4094a d77c5050 3d6dd424 304e2f3e 574e9768
01a3318c 420fc3ca c0a12b34 f23eb540 e2b46fd7 bdd9c2f1 3d307402 431ca7ba
77ddb86c 47befb3f 72e7ff08 fdc4b1b0 f27e1f91 e2e683a8`). Zero-edit vs
`ITEM_BASELINE=85b01ebe…`: diff touches only this artifact (header swap +
EOF append) and Worker-0's `dry-0_0_15.md`; `--name-only -- '*.py'`
empty. The 3 inventory oracles are source-text identical across the drift
(`:5150`->`:5280`, `:5172`->`:5302`, `:5199`->`:5329`).

Shape. The header lines 3-4 are W1's authored run-8 stamp (`Status:
ready-for-verification/1`, `Run: 0.0.15 2026-09-30-8`), transcribed by
Worker-0 after the followup successor was admitted without edit tools; the
vs-baseline diff is exactly that 2-line swap (the baseline's stale
`verified` / `2026-09-17-1` lines) plus the 511-line EOF append, with every
prior section untouched. The submission stands; this verification flips
line 3 to `verified` and appends here.

Precision notes (recorded, none verdict-affecting): (1) O2 pins read
`:2123` + `:2125`-`:2126`, not `:2121` `:2123` (`:2121` is the slice
bullet's continuation); the `:3041` test-plan checkbox
("non-projection, non-combined…") is a third stale pin in the same spec
the owning card should take with the two Edge sentences. (2)
"Byte-identical" for guard/def/signature lines touched by the typing wave
means body/executable-identical (annotations differ); every affected
verdict rests on logic or prose, which is unchanged. (3) F9's `:432` pin
resolves to docstring prose inside `is_async_only_iterable`, not a def;
the trio defs re-pin around it and the zero-reader census is as stated.
(4) F11's 7th direct site is the reverse-direction `async_to_sync` half of
the window machinery — a per-call convention; per-site it is 5 -> 6 with
the same verdict. (5) D4's cited "order census re-proof" is the ORDER BY
ladder census, which does not prove the `using`/`all` question; the holding
is confirmed on direct docstring+body evidence instead. (6) W1's s1/s2
"both quote the old rule text" overstates (s1 silent, s2 cites as input);
the material first-recorded claim holds. (7) The run-8 `## Pending
execution` entry 1's "no probe to re-run" retires the entry-1 `proof:`
type by prose rather than by gate run; Worker-0 should confirm the type
change is intended at closeout.

No new defects. `FAKESHOP_SHARDED=1`/Postgres cells stay `unverified`.
No ruff run owed (artifact `.md` only, no cross-file links, no scaffold
owed). No commit. Address `dry/querysets-retrace-s16/verify`.
