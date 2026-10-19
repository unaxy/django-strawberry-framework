# DRY review: `django_strawberry_framework/permissions.py`

Status: verified
Run: 0.0.15 2026-09-30-8

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, re-derived
fresh on the cascade side, never inherited) or a file-local record with its
proving challenge, plus two recorded rejections. Zero production edits; zero
tracked files changed.

## System trace

Mid-size target (740 lines, 30 `ast.Module.body` members): the package's
call-time cascade visibility helper,
`django_strawberry_framework/permissions.py::apply_cascade_permissions` plus
its async twin
`django_strawberry_framework/permissions.py::aapply_cascade_permissions`.
A consumer calls it inside its `DjangoType.get_queryset` to make every
single-column concrete forward relation of its model respect its target
type's own visibility. The walk is depth-1; transitive cascade emerges
because each target's hook may itself call the helper.

It DEFINES the cascade walk (edge classification, scope validation,
traversal state, cycle policy, re-projection battery, per-edge composition)
and CONSUMES by name every hardened primitive it touches: the sealed
visibility boundary (`django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`,
`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`,
`django_strawberry_framework/utils/querysets.py::_CASCADE_SEAL_POLICY`,
`django_strawberry_framework/utils/querysets.py::_defect_message`), the
model/seed substrate
(`django_strawberry_framework/utils/querysets.py::model_for`,
`django_strawberry_framework/utils/querysets.py::base_queryset`), and the
single sync boundary
(`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`).
It ENFORCES the child-alias rule at its edge seed (`using=state.alias`) and
carries its own recourse sentence
(`django_strawberry_framework/permissions.py::_ASYNC_RECOURSE`) that stays
deliberately separate from the write/gate recourses.

Connected code read for judgment, outside the item:
`django_strawberry_framework/utils/querysets.py` (def lines + docstrings of
`model_for`, `base_queryset`, `_SealPolicy`, `_CASCADE_SEAL_POLICY`,
`_defect_message`, `_prepared_visibility_source`,
`_normalized_visibility_result`, `apply_type_visibility_sync`,
`run_in_one_sync_boundary`, `sync_pipeline_recourse`, `SyncMisuseError`;
full bodies of the seal-policy constants and the two visibility runners);
`django_strawberry_framework/utils/permissions.py`
(`_GATE_ASYNC_RECOURSE`, `invoke_permission_method`, `request_from_info`);
`django_strawberry_framework/mutations/permissions.py`
(`_PERMISSION_ASYNC_RECOURSE`, `has_permission`/`check_permission` contract);
`django_strawberry_framework/__init__.py` (root manifest entries for both
cascade names and `SyncMisuseError`);
`django_strawberry_framework/registry.py` (`registry.get` resolve);
`django_strawberry_framework/types/relay.py` (the redundant-alias re-export
convention); `tests/test_permissions.py` (full head + all 62 test titles +
the scope-classification bodies at the `_edge_plan` / `_is_cascadable_edge`
/ `_is_unsupported_forward_edge` pins); `docs/GLOSSARY.md`
(`apply_cascade_permissions`, `Visibility boundary`,
`Sealed execution queryset`, `Prefetch alias threading` entries, read as
projections); `docs/SPECS/spec-034-permissions-0_0_10.md` (pointer only,
body not relied upon).

Excluded with reason: the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) — never touched, not in this finding's sites;
concurrent dirt (`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) — read where needed as oracles, never edited;
`optimizer/walker.py` / `filters/sets.py` bodies beyond the cited
`base_queryset(using=)` enforcement lines (the family items own the full
sweep; this item verifies the cascade-side consumer role only);
`auth/mutations.py` + `routers.py` disposal bodies (the
`awaitable-refusal-and-disposal` owner-side count is plan-indexed; this item
verifies the cascade has no such body); upstream Django/Strawberry sources
in `.venv` (no upstream seam is re-decided here).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Every public surface's permission
vocabulary was compared by behavior, not name. The cascade answers "may this
caller *see* this row" through `get_queryset` narrowing (queryset in,
narrowed queryset out). The write side answers "may this caller *write* it"
through `has_permission` / `check_permission` returning a `bool`
(`mutations/permissions.py::_require_sync_bool_auth_result`, deny-by-default,
`user.has_perm` mapping). The filter/order side judges *input* through
`check_<field>_permission` gates fired per active field
(`utils/permissions.py::invoke_permission_method`, deduped per class,
async-rejected). Three vocabularies, three contracts, three reasons to
change: a new row-visibility shape moves the cascade; a new model perm moves
the write default; a new input gate moves the traversal. The separation is
stated at the write owner ("first-class, separate contract from row
visibility ... can view is never can write") and composed in the right order
(cascade narrows first, gates judge survivors, denials leak nothing — pinned
by `test_cascade_then_filter_*` / `test_cascade_then_order_*`). No flavor
restates another's rule. The unified-vocabulary form is considered and
rejected in F8.

**2. Sync/async twins.** One colored pair touches this file:
`apply_cascade_permissions` / `aapply_cascade_permissions`. Compared by
behavior, not shape: the async twin wraps the single sync walk in
`run_in_one_sync_boundary` (probe: source names both, exactly one `_walk`
definition, exactly one `await` node in the module AST). There is no second
walk implementation; pure decisions (classification, validation, cycle
policy, re-projection, composition) are shared by construction, and an
`async def` target hook raises `SyncMisuseError` identically from both
variants (the worker thread has no awaiting context either). This is
principle 5's write-pipeline shape (one sync body in one boundary), already
recorded at the boundary owner — not the connection's two-colored-bodies
shape. No divergence found. Family `one-sync-boundary`, F3.

**3. Derived rather than repeated knowledge.** Four facts are derived once
and read by name: the cascadable set is classified once per model by
`_edge_plan` (bounded `lru_cache`, shared by the validator, the preflight,
and the walk — probe: `Category is Category` identity holds); the target
column is read off `field.target_field.attname` at composition time, never
restated per edge (probe: `Item.category` re-projects to `id`, the
`to_field`-correct column); the root alias is read once off the sealed
queryset (`alias=queryset.db`) and threaded as state, never re-derived per
edge; the seal option set is the single `_CASCADE_SEAL_POLICY` constant
passed at both ends (probe: exactly two `policy=_CASCADE_SEAL_POLICY`
passes). The one near-miss — `_validate_fields` spelling
`frozenset(field.name for field in plan.cascadable)` instead of calling
`_cascadable_edge_names` — reads the same plan object the helper reads, so
it composes the owner (`_edge_plan`), not `_meta`; not a second definition.

**4. Inverse / round-trip pairs.** Two pairs, both with both halves here:
`_root_error_renderer` / `_edge_error_renderer` (the two ends of one helper,
each rendering exactly the defect subset its end can reach — probe: root 5
arms, edge 6 arms, both exactly the reachable set; the D5 positive controls,
re-derived in F5); `fields=None` (walk every cascadable edge) /
`fields=[]` (walk nothing, compose nothing — the defined no-op and the
documented cycle-breaking recourse). No encode/decode, pack/unpack, or
build/parse grammar lives here. The seal/unseal direction is owned by the
boundary; this file only supplies prose through its seam.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target + the six boundary symbols it composes);
oracles that pin behavior — `tests/test_permissions.py` (62 test titles
covering cycles, GFK preflight, `fields=` validation, hook-return / root /
alias defects, MTI, identity-hook default-manager composition, nullable
disjuncts, `ContextVar` isolation across threads/tasks, the `aapply`
off-loop contract; the classification pins at the `_edge_plan` bodies read
the helpers from the owner and are therefore *not* independent oracles for
the predicates, while every narrowing/error/alias/SQL-shape row asserts
rows, errors, or query strings and is independent); the live tier
(`test_products_api.py` cascade rows, `test_products_visibility_api.py`
optimizer-plan rows — projections of the same contracts onto shipped
fixtures); projections (the module docstring's eight-bullet traversal
contract, the GLOSSARY `apply_cascade_permissions` entry, spec-034). No
oracle was rewritten to read its expectation from the owner it checks,
except the predicate pins noted above, which are honestly recorded as
owner-reading rather than graded as independent.

**6. Enforcement by omission.** Two families enumerated member-by-member.
(a) *Forward-edge coverage*: the walk composes every cascadable edge whose
target model has a registered primary type; it skips unregistered targets
(no policy to apply), reverse relations, M2M, `GenericRelation`, scalars,
and fails closed on GFK/composite (preflight + `fields=` rejection).
Probe on real fakeshop `_meta`: `Category` walks nothing, `Item` walks
`category`, `Entry` walks `property` + `item`. Contract sources (module
docstring's edge bullets, `_is_cascadable_edge` / `_is_unsupported_forward_edge`
docstrings, the scope test's per-kind pins) establish each skip or failure
as the rule — no member lacks a guard its contract requires. (b)
*Child-alias inheritance*: the three seeding surfaces named by the owner
are `permissions.py` (`using=state.alias`), `filters/sets.py`
(`using=parent_db`), and `optimizer/walker.py` (unguarded at cycle entry,
since fixed under the ledgered D1 to seal under `_PREFETCH_CHILD_POLICY`).
This target is the guarded member; the gap lives elsewhere and is already
ledgered, not re-decided here. Family `child-queryset-alias-inheritance`,
F2.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **30 top-level statements** — plus, better than the minimum, every
`func`/`class` name. Every member lands below; every challenge in
`### Challenges` ends in a family row or a file-local record.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (eight-bullet traversal contract) | (none) | projection, F1–F8 |
| 1–12 | twelve imports (`annotations`, `dataclasses`, `ContextVar`, `lru_cache`, `Any`/`NamedTuple`, `models`, `Q`, `ForeignObjectRel`, `ConfigurationError`, `registry`, seven boundary names, `SyncMisuseError as SyncMisuseError`) | machinery | F1–F5, R9 |
| 13 | `_ASYNC_RECOURSE` | recourse sentence | F6 (rejected) |
| 14 | `class _TraversalState` (`alias`, `active`, `path`, frozen) | traversal record | R4, file-local |
| 15 | `_cascade_state: ContextVar[...]` | walk slot | R4, file-local |
| 16 | `class _EdgePlan` (`cascadable`, `unsupported`) | plan record | R1, file-local |
| 17 | `def _is_cascadable_edge` | forward-concrete test | R1, file-local |
| 18 | `def _is_unsupported_forward_edge` | fail-closed test | R2, file-local |
| 19 | `def _edge_plan` (`lru_cache`, shared slice) | plan owner | R1, file-local |
| 20 | `def _cascadable_edges` | plan-tuple accessor | R8, file-local (KANBAN-homed) |
| 21 | `def _cascadable_edge_names` | name-set accessor | R8, file-local (KANBAN-homed) |
| 22 | `def _validate_fields` | scope validator | R3, file-local |
| 23 | `def _root_error_renderer` | source-defect prose | F5 (consumer) |
| 24 | `def _edge_error_renderer` | per-edge defect prose | F5 (consumer) |
| 25 | `def _validated_target_subquery` | re-projection battery | R6, file-local |
| 26 | `def _cycle_error` | cycle message | R5, file-local |
| 27 | `def apply_cascade_permissions` | root orchestration | F1/F2/F4 consumers + R2/R3/R5 |
| 28 | `def _walk` | per-edge composition | F1/F2/F4 consumers + R7 |
| 29 | `async def aapply_cascade_permissions` | async twin | F3 (consumer) |

Rules: F1 sealed-execution-queryset (consumer), F2
child-queryset-alias-inheritance (enforcement), F3 one-sync-boundary
(consumer), F4 queryset-seed-and-model-read (consumer), F5
seal-defect-code-wording (consumer, positive controls), F6
sync-boundary-recourse-wording (rejected), F7
awaitable-refusal-and-disposal (checked, not a member), F8 unified
permission-hook vocabulary (rejected); R1 cascadable-edge classification
(+ MTI inclusion, + plan cache), R2 unsupported-edge preflight, R3 `fields=`
scope validation, R4 immutable `ContextVar` traversal state, R5 cycle
fail-closed + `fields=[]` escape, R6 re-projection battery, R7 per-edge
composition (registry skip, `using=` seed, nullable disjunct, depth-1 walk),
R8 vestigial accessors (principle 11, KANBAN-homed), R9 re-export posture.
No new family is named: the cascade walk as a whole is sole-owned here and
stays file-local; every cross-file rule reuses an indexed family.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | sealed execution at both cascade ends | a new untrusted shape (project queryset class) must fail closed | **1** (`_seal_or_defect`, via `_prepared_visibility_source` + `apply_type_visibility_sync` composed by name) | independent; F1 |
| C2 | child-alias seed | seeds must spell `db_manager(alias)` instead of `.using(alias)` | **1** (`base_queryset` owns the spelling; this file's `using=state.alias` follows as consumer) | independent; F2 |
| C3 | one sync boundary | the boundary must also bind a `ContextVar` | **1** (`run_in_one_sync_boundary`; this file's twin follows) | independent; F3 |
| C4 | model read + seed read | a registered type overrides its seed manager | **2** (`model_for` + `base_queryset`, composed by `initial_queryset`) — neither moves here | independent; F4 |
| C5 | defect-code wording | a new seal code ships | **1** definition + arms at reachable sites; this file's two sites stay correct (probe) | independent; F5 |
| C6 | recourse sentence | the sentence must name the settings key that relaxes it | **1** here (`_ASYNC_RECOURSE`); write/gate sentences do NOT move | rejected; F6 |
| C7 | awaitable disposal | async generators gain a disposal protocol | **0** here (no body; refusal rides the runner) | not a member; F7 |
| C8 | cascadable-edge test | a future single-column `ForeignKey` shape must be excluded | **1** (`_is_cascadable_edge`) | file-local; R1 |
| C9 | unsupported-edge test | a new composite forward relation must fail closed | **1** (`_is_unsupported_forward_edge` + the preflight it feeds) | file-local; R2 |
| C10 | `fields=` grammar | a new scope spelling (`fields="__all__"`) must validate | **1** (`_validate_fields`) | file-local; R3 |
| C11 | traversal isolation | state must survive a hook exception without leaking | **1** (`_cascade_state` token install/reset) | file-local; R4 |
| C12 | cycle policy | the escape must also cover a non-empty subset | **1** (`apply_cascade_permissions` active-tuple branch; staying fail-closed is the point) | file-local; R5 |
| C13 | re-projection | a new semantic-changing shape must be rejected, not repaired | **1** (`_validated_target_subquery`) | file-local; R6 |
| C14 | per-edge composition | the nullable disjunct must ride a different predicate | **1** (`_walk` `field.null` arm) | file-local; R7 |
| C15 | hook vocabulary | visibility and authorization collapse into one hook | **0** moves — refused (three contracts, three reasons to change) | rejected; F8 |
| C16 | vestigial accessors | both helpers are deleted | **0** production readers break (tests read the plan directly) | KANBAN-homed; R8 |

**Experiments.** Two read-only probes (no source mutation, no SQL
evaluation, no shared-tree pytest):

```shell
uv run python docs/dry/temp-tests/dry-file-permissions/probe_w1.py
```

Output (`ALL OK`): 30-member AST with kinds
(`Expr` 1, `ImportFrom` 11, `Import` 1, `Assign` 1, `ClassDef` 2,
`AnnAssign` 1, `FunctionDef` 12, `AsyncFunctionDef` 1); single `_walk`,
`aapply` wraps `apply` in `run_in_one_sync_boundary`, exactly one `await`
node; `_CASCADE_SEAL_POLICY` fields
(`require_model_rows=False`, `reject_combined=True`, rest defaults);
exactly two `policy=_CASCADE_SEAL_POLICY` passes, one
`_prepared_visibility_source(` call, one `apply_type_visibility_sync(`
call; root arms exactly `{type, table, untrusted, sliced, combined}`, edge
arms exactly those plus `alias`; `using=state.alias`, `alias=queryset.db`,
`queryset.db != state.alias` all present; the three recourse sentences
pairwise distinct; `SyncMisuseError` one definition with alias re-export;
both `_cascadable_*` helpers used only inside this file; cascade vocabulary
`get_queryset`-only; edge plans `Category=[]`, `Item=[category]`,
`Entry=[property, item]` with `lru_cache` identity. Status:
`execution-verified` for every identity/count/shape/absence claim above.
Rejects "a second walk exists", "the twin awaits hooks", "a reachable code
lacks an arm", "the seed floats off-alias", "the recourses are one rule".

```shell
uv run python docs/dry/temp-tests/dry-file-permissions/probe_w2.py
```

Output (`ALL OK`): `fields=None` walks all, `[]` walks none,
`["category"]` scopes, bare-string / non-iterable / non-string /
unhashable / unknown each raise `ConfigurationError`; `Item.category`
cascadable and not unsupported; plain hook return re-projects to the
edge's `target_field.attname`; field-specific `distinct(...)`, grouped
(aggregate) shapes, and the `values("name").annotate(id=Value(1))`
column-shadowing vector (ungrouped, the security-critical one) each raise.
Status: `execution-verified` for the validator branches and the
re-projection battery. Rejects "a malformed scope escapes as `TypeError`",
"a grouped return is repaired", "a shadowing alias composes".

## Findings

No production edit is owed by a file item; each finding names the family
that will own it.

### F1 — sealed-execution-queryset (existing family, consumer)

- **Contract + variation.** A consumer-supplied root and every hook return
  are untrusted query STATE: read without dispatch, validate, rebuild a
  framework-owned plain `QuerySet`, never return the consumer object.
  Variation rides the five `_SealPolicy` fields; this surface passes
  `_CASCADE_SEAL_POLICY` at both ends.
- **Sites + roles.** *Definition*:
  `utils/querysets.py::_seal_or_defect` + helpers (owner).
  *Consumers (this target)*:
  `permissions.py::apply_cascade_permissions` (root via
  `_prepared_visibility_source` with `_root_error_renderer` and the cascade
  policy), `permissions.py::_walk` (per-edge via
  `apply_type_visibility_sync` with `_edge_error_renderer` and the same
  policy). *Oracles*: `tests/test_permissions.py` root-shape rows,
  hook-return rows, hostile-clone/override rows, unsealable-`Query` rows.
  *Projections*: module docstring's hook-validation bullets, GLOSSARY
  `Visibility boundary` / `Sealed execution queryset`.
- **Challenges.** C1 → 1 (elsewhere). No surface outside the owner rebuilds
  `sql.Query` (the querysets artifact's package-wide search, re-checked at
  the two call sites here).
- **Owner + lifetime.** Existing owner by responsibility:
  `utils/querysets.py::_seal_or_defect`. No stored derivation here (the
  sealed objects are threaded, never cached); principle-4 fields live at
  the owner.
- **Migration.** None (zero-edit item; consumer already composes by name).
- **Distinct behavior.** The `.values()` acceptance (`require_model_rows`
  off) is the cascade's declared variation, not a relaxation elsewhere.
- **Behavioral proof.** `execution-verified` (probe_w1 seal sites +
  policy fields; probe_w2 hostile-shape rejections are pinned by named
  oracles, bodies `static-reviewed` per no-pytest rule). Rejects "a second
  sealing body lives here".
- **Structural gate.** Owned by the family item; this target's contribution
  is the hostile-clone/override rows (a hand copy of the owner's body
  passes every behavior oracle, so the gate must be the seal's own
  type-identity checks, not a name assertion).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/permissions.py`
  `757dce34cecd7a249b2634947a771d4608808bfe`,
  `django_strawberry_framework/utils/querysets.py`
  `1539b66c9ce9a659e1dc5f6bf1029b15d6868587`,
  `tests/test_permissions.py`
  `4a1d7775b32a38c06a15745d1c581daea917c71e`. Searched population: all 117
  package files for a second `sql.Query`-rebuilding body (none).

### F2 — child-queryset-alias-inheritance (existing family, enforcement site)

- **Contract + variation.** A queryset seeded for a relation's target model
  must read on the same connection as the parent that seeded it. Two
  mechanisms encode it: `base_queryset(model, using=)` pins the seed, and
  the seal's `require_shared_alias` rejects a re-routed hook result.
- **Sites + roles.** *Definitions*: `base_queryset`'s `using` arm +
  `_seal_or_defect`'s `require_shared_alias` arm (owner file).
  *Enforcement site (this target)*: `permissions.py::_walk`
  `base_queryset(field.related_model, using=state.alias)`, with the root
  pin `alias=queryset.db` and the nested-application guard
  `queryset.db != state.alias`. *Siblings*: `filters/sets.py` (pinned),
  `optimizer/walker.py` (the ledgered D1 member, since fixed).
  *Oracles*: `test_multi_db_subquery_pinned_to_caller_alias`,
  `test_nested_application_off_root_alias_fails_closed`,
  `test_unpinned_hook_return_is_repinned_to_root_alias`.
- **Challenges.** C2 → 1 (elsewhere). This file holds no second seed
  spelling.
- **Behavioral proof.** `execution-verified` for the seed-site
  enumeration (probe_w1 source pins); the cross-connection *consequence*
  stays `execution-deferred` (see `## Pending execution` — sharded mode
  needs the maintainer's word).
- **Family.** `child-queryset-alias-inheritance`.
- **Freshness.** Target + querysets blobs as in F1,
  `django_strawberry_framework/filters/sets.py`
  `4ab65a26b0ccf56f7f40f4938282bba9690673d1`,
  `django_strawberry_framework/optimizer/walker.py`
  `9b111ed938951a073a9226ccbcfacabc3af981e8`.

### F3 — one-sync-boundary (existing family, consumer)

- **Contract + variation.** A consumer-overridable sync hook runs in
  exactly one `sync_to_async(thread_sensitive=True)` worker per
  resolution, never per-step hops.
- **Sites + roles.** *Definition*:
  `utils/querysets.py::run_in_one_sync_boundary`. *Consumer (this
  target)*: `permissions.py::aapply_cascade_permissions` wrapping the
  single sync walk. *Oracles*: `test_aapply_runs_walk_off_event_loop`,
  `test_aapply_async_target_hook_still_raises`,
  `test_aapply_gather_restores_task_contexts`.
- **Challenges.** C3 → 1 (elsewhere). The five direct `sync_to_async`
  sites named in the querysets artifact wrap relation reads / test-client
  logins, not consumer hooks — neither definitions nor enforcement sites
  of this rule.
- **Behavioral proof.** `execution-verified` for the shape (one wrapper,
  one walk, one `await` node); oracle bodies `static-reviewed`.
- **Family.** `one-sync-boundary`.
- **Freshness.** Target + querysets blobs as in F1.

### F4 — queryset-seed-and-model-read (existing family, consumer)

- **Contract + variation.** Read the model registered to a `DjangoType`
  from the one definition attribute; seed a fresh base queryset for a
  model (optionally alias-pinned) from its default manager.
- **Sites + roles.** *Definitions*: `utils/querysets.py::model_for`,
  `utils/querysets.py::base_queryset`. *Consumers (this target)*:
  `model_for(cls)` at the walk root, `base_queryset(field.related_model,
  using=state.alias)` at each edge. `relay.py`'s raw-manager read is the
  recorded deliberate exception, not a copy.
- **Challenges.** C4 → 2 (both elsewhere, composed by `initial_queryset`).
- **Behavioral proof.** `static-reviewed` (import moves composed by name;
  no ordering/transactional/async content).
- **Family.** `queryset-seed-and-model-read`.
- **Freshness.** Target + querysets blobs as in F1.

### F5 — seal-defect-code-wording (existing family, consumer; D5 positive controls re-derived)

- **Contract + variation.** The seal's defect codes are closed and ordered;
  each message site renders only the subset IT can reach, in its own prose.
- **Sites + roles.** *Definition*:
  `utils/querysets.py::_defect_message` (dispatch + exhaustiveness).
  *Consumers (this target)*: `permissions.py::_root_error_renderer`
  (5 arms) and `permissions.py::_edge_error_renderer` (6 arms).
  *Projection*: the per-renderer "reachable codes" paragraphs.
- **Challenges.** C5 → 1 definition + per-site arms. Re-derived fresh at
  this HEAD (not inherited): reachable under `_CASCADE_SEAL_POLICY` with
  no `expected_routing` is `{type, table, untrusted, sliced, combined}`
  at the root, plus `alias` at the edge (required alias present); the
  `projection` code cannot arrive (`require_model_rows=False`), nor can
  `routing` / `evaluated`. Probe reads both ladders out of the AST and
  diffs against that set: both sites `OK` — the comparison can tell a
  right site from a wrong one (the three dead-arm sites live in the owner
  file as D5, untouched here).
- **Behavioral proof.** `execution-verified` (probe_w1 arm diff + negative
  shape: the model that fell open would print every code).
- **Family.** `seal-defect-code-wording`.
- **Freshness.** Target + querysets blobs as in F1.

### F6 — REJECTED: the cascade recourse stays its own sentence

- **Shared form considered.** Generating
  `permissions.py::_ASYNC_RECOURSE` from
  `utils/querysets.py::sync_pipeline_recourse`.
- **Contract difference.** The write template names `get_queryset` and
  offers "redefine the target hook sync" for a pipeline that *could* run
  async elsewhere; the Relay twin offers an async resolver because async
  IS possible there; the cascade sentence must additionally name the
  twin (`aapply_cascade_permissions` wraps the same sync walk, so neither
  variant can await) and the escape (`fields=` to skip the async-hooked
  edge). Four clauses differ, so a template takes a parameter per clause
  and pins nothing. Re-read at this HEAD: the three literals remain
  pairwise distinct (probe).
- **Reconsideration trigger.** If the cascade ever grows an async-native
  walk, or the sentence is reworded to differ from the write template
  only in the subject noun, the two collapse into one rule.
- **Durable home.** `utils/querysets.py::sync_pipeline_recourse`
  (declines it) + `permissions.py::_ASYNC_RECOURSE` (states its own
  recourse). Not written by this item.
- **Family.** `sync-boundary-recourse-wording` (stays `rejected`).
- **Freshness.** Target blob as in F1, querysets blob as in F1,
  `django_strawberry_framework/mutations/permissions.py`
  `54f770ae5aa1238327246cd2dcb141e8aac14965`,
  `django_strawberry_framework/utils/permissions.py`
  `9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`.

### F7 — checked, not a member: awaitable-refusal-and-disposal

- **Checked, not inherited.** Searched for a second disposal body:
  module AST holds exactly one `await` node (the `aapply` wrapper) and no
  `reject_async*` / `_dispose*` definition or call (probe). Async-hook
  refusal here rides `apply_type_visibility_sync`'s
  `reject_async_in_sync_context` (coroutine closed, `SyncMisuseError`
  with `_ASYNC_RECOURSE`) — a consumer of the family, not a definition.
  No family row is claimed for this target; the family item owes no
  re-derivation on its account beyond the consumer role recorded here.
- **Freshness.** Target + querysets blobs as in F1.

### F8 — REJECTED: one permission-hook vocabulary for visibility, writes, and input gates

- **Shared form considered.** A single `has_permission`-shaped hook (or a
  single `get_queryset`-shaped hook) spanning row visibility, write
  authorization, and filter/order input gating.
- **Contract difference.** `get_queryset` narrows *which rows exist* for
  the caller (queryset in/out, composes with subqueries, must stay
  sync-composable); `has_permission` / `check_permission` decides *whether
  the write may proceed* (bool, deny-by-default, `user.has_perm`
  mapping); `check_<field>_permission` judges *whether supplied input may
  constrain* a field (per-field fire, per-class dedup, flat-path chain so
  a flat spelling cannot bypass a nested gate). Merging any two either
  adds validator rejection to an equality test or drops the fail-closed
  raise from an authorization check — the same shape as the sustained
  `field-value-coercion` rejection. Composition order (cascade first,
  gates on survivors) is itself load-bearing against existence leaks.
- **Reconsideration trigger.** If a surface ever needs to judge input
  *and* narrow rows in one hook (a single call returning both a queryset
  and an allow/deny verdict), that hook is the shared rule's new member.
- **Durable home.** `mutations/permissions.py` module docstring
  ("first-class, separate contract from row visibility ... can view is
  never can write") + `utils/permissions.py` module docstring (mechanics
  vs family shape). Not written by this item.
- **Freshness.** Target blob as in F1, mutations-permissions +
  utils-permissions blobs as in F6.

### File-local records (no second site after the matrix)

| Rule | Owner | Challenge posited | Definitions |
|---|---|---|---|
| R1 — "cascadable edge" (single-column concrete forward FK/O2O incl. MTI parent links; cached plan shared by validator, preflight, walk) | `permissions.py::_is_cascadable_edge` + `_edge_plan` (`_EdgePlan` record) | C8 — a future single-column `ForeignKey` shape must be excluded | 1 (probe: `Item.category` true; M2M/reverse/GFK/GenericRelation false per scope pins; `lru_cache` identity holds) |
| R2 — unsupported-forward-edge preflight (GFK/composite fail closed before any hook; naming one in `fields=` fails at validation) | `permissions.py::_is_unsupported_forward_edge` + preflight in `apply_cascade_permissions` | C9 — a new composite forward relation must fail closed, not skip | 1 (the `getattr(field, "is_relation", False)` hardening note is KANBAN-homed, unreachable today — not a new defect) |
| R3 — `fields=` scope grammar (`None` = walk all, `[]` = defined no-op, bare-string / non-iterable / non-string entries rejected loudly, unknown vs unsupported distinguished) | `permissions.py::_validate_fields` | C10 — a new scope spelling must validate | 1 (probe_w2: all five malformed shapes raise `ConfigurationError`, never raw `TypeError`) |
| R4 — immutable `ContextVar` traversal state (root alias + active tuple + path frames; token install/reset in `finally`; WSGI/ASGI + `sync_to_async`-copy isolation) | `permissions.py::_TraversalState` + `_cascade_state` | C11 — state must not leak across a hook exception | 1 (oracles: hook-exception-reset + thread/gather isolation rows; bodies `static-reviewed`) |
| R5 — cycle fail-closed with the explicit zero-edge escape (re-entry raises path-rich `ConfigurationError`; `fields=[]` re-entry returns the direct narrowing) | `permissions.py::_cycle_error` + `apply_cascade_permissions` active-tuple branch | C12 — a non-empty re-entrant subset must stay closed | 1 (oracles: mutual/longer/diamond/self-referential cycle rows + the `fields=[]` recourse rows) |
| R6 — re-projection battery (distinct/grouped/column-shadowing rejected; accepted return re-projected to `.values(target_field.attname)`) | `permissions.py::_validated_target_subquery` | C13 — a new semantic-changing shape must be rejected, not repaired | 1 (probe_w2: all three vectors raise; `to_field` binds its own column by construction) |
| R7 — per-edge composition (registry miss skipped; base pinned; hook probed; `Q(__in)` + nullable-only `__isnull` disjunct; depth-1 walk, transitive via nested hooks) | `permissions.py::_walk` | C14 — the null disjunct must ride nullability, not edge kind | 1 (oracles: nullable-chain + `isnull`-only-on-nullable rows; unregistered-target + secondary-type-skip rows) |
| R8 — the two plan accessors (one reader / zero production readers) | `permissions.py::_cascadable_edges` + `_cascadable_edge_names` | C16 — delete both | 0 production readers break; KANBAN-homed (delete-vs-keep paths recorded there, low value, gates nothing) — principle-11 note, not a family |
| R9 — redundant-alias re-export posture | `permissions.py::SyncMisuseError` (`as`-form, the `types/relay.py` convention) | "a new public name arrives through this module" | 0 new names (already in the root `__all__` via `types`; probe: identity with the owner's class) |

## Defects

None. Every claim checked while tracing held: the twin wraps the one
walk; both seal ends pass the cascade policy; both renderers declare
exactly their reachable arms; the edge seed pins the root alias and the
nested guard compares it; the three recourse sentences are pairwise
distinct; the re-export adds no public name; the `fields=` ladder never
escapes as a raw `TypeError`; the grouped/distinct/shadowing vectors all
fail closed; the classification pins match the bodies. The two
KANBAN-homed notes encountered while tracing (the `is_relation`
`getattr`-default hardening choice; the vestigial-accessor delete-vs-keep
choice) are already owned on their card with paths recorded — not new
defects, not re-homed here. Nothing routed to any owner.

## Pending execution

One command this run is not authorized to issue. It blocks no finding;
it is listed so the gate carries it.

1. `FAKESHOP_SHARDED=1 uv run pytest tests/test_permissions.py -k "multi_db or alias or pinned" --no-cov`
   — discharges F2's observable half: that a cascade edge whose target
   hook returns `.using(other)` actually fails closed (or repins) against
   a live second connection rather than only against composed lazy state.
   Needs the maintainer's separate authorization for the sharded mode; until then the
   cross-connection *consequence* stays `unverified` (the seed-site
   enumeration and the lazy-state policy pins above are already
   `execution-verified` by the read-only probes). Postgres cells stay
   `unverified` (need the maintainer's word); the target's code path reaches no
   pk-magnitude or dialect decision, but that judgment is Worker 2's to
   make, not this artifact's.

No shared-tree pytest was run, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` proof beyond the sharded row.

## Judgment

Backstop discharged: 30/30 `ast.Module.body` members enumerated (13
functions incl. 1 async, 2 classes, 2 module-level values, 12 imports, 1
docstring), 16 challenges run, every rule terminating in a reused indexed
family (F1–F5 consumers/enforcement, F6 + F8 rejections re-derived fresh,
F7 checked-not-member) or a file-local record (R1–R9, with R8's
keep-or-delete owned on its KANBAN card). The six-axis matrix was
discharged against the real surface — twin sameness by behavior,
vocabulary separation by contract, derivation by owner-read, round-trip
halves both present, media counted with oracle independence graded, and
both omission families enumerated member-by-member rather than asserted.
No consolidation owed, no defect found, no new family named. Zero-edit
result is legitimate.

No consolidation family is proposed for Worker 0: the cascade walk itself
is sole-owned here and stays file-local. One proposed rejected index row is
offered for Worker 0's judgment — F8 (unified permission-hook vocabulary,
rejected, homes at the write + gate module docstrings) — since no indexed
family currently spans visibility vs write vs input-gate vocabulary; if
Worker 0 prefers to hold it as matrix evidence for the three owning file
items instead, this artifact loses nothing.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
5cecc2e4068f7f789ced97459a277efa4ebe3a2f --
django_strawberry_framework/permissions.py` is empty (0 bytes, re-measured
after both probe runs); the working blob
`757dce34cecd7a249b2634947a771d4608808bfe` equals the item baseline, the
cycle member, and `HEAD:` — the target is clean, so no hunk attribution
was owed. Before touching any path, the item-scoped paths were verified
clean; the `## Owned changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never
touched; concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied. Dirt elsewhere left alone, not a stop. No
commit. Untracked scratch created (not tracked changes): this artifact
`docs/dry/dry-file-permissions.md` and the two read-only probes
`docs/dry/temp-tests/dry-file-permissions/probe_w1.py` (`ALL OK`) and
`docs/dry/temp-tests/dry-file-permissions/probe_w2.py` (`ALL OK`) — no
source mutation, no DB writes, no shared-tree pytest, zero SQL evaluated.
Scoped `ruff format` + `ruff check --fix` were run on the two untracked
probe files only (8 autofixes; remaining N812/D101/D103/PERF203 notes are
exempt per-cycle scratch, no style cleanup owed); repo-wide ruff was not
run, and no tracked `.py` was edited (artifact is `.md` only).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Own trace derived BEFORE reconciling with `## Findings` (fresh `ast.parse` +
source-text + lazy `_meta` reads; W1 probes re-ran only as execution checks
after the trace). Scratch:
`docs/dry/temp-tests/dry-file-permissions-w2/w2_trace.py` (`ALL OK`) and
`w2_behavior.py` (`ALL OK`) — read-only, zero SQL evaluated, no source
mutation, no shared-tree pytest.

### Own trace (counts; owner I would choose)

- Seal consumer + cascade policy passes: root via
  `django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`
  x1, per-edge via
  `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`
  x1, both `policy=_CASCADE_SEAL_POLICY` (exactly 2 passes). Policy fields
  `require_model_rows=False, reject_sliced=True, reject_combined=True`
  (rest defaults). Count 1 definition
  (`django_strawberry_framework/utils/querysets.py::_seal_or_defect`).
  Owner: seal owner. No second `sql.Query`-rebuilding body here.
- Alias enforcement: root pin `alias=queryset.db`, edge seed
  `base_queryset(field.related_model, using=state.alias)`, nested guard
  `queryset.db != state.alias`. Count 1 (`base_queryset` owning the
  spelling + seal `require_shared_alias` arm). Owner: existing
  `child-queryset-alias-inheritance` owners. This target is the guarded
  enforcement site.
- Sync/async twin: single `_walk` def, single `await` node, `aapply`
  body wraps `apply` in `run_in_one_sync_boundary` (4 textual mentions:
  import + def + call + docstring). Count 1
  (`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`).
  Owner: boundary owner. Write-pipeline shape, not connection two-body shape.
- Seed/model reads: `model_for(cls)` x1 at root,
  `base_queryset(..., using=state.alias)` x1 at edge. Count 2 (both in
  owner file, composed by `initial_queryset`). Owner: existing
  `queryset-seed-and-model-read` owners. Neither moves here.
- Defect ladders as D5 controls: `_root_error_renderer` 5 arms
  `{type, table, untrusted, sliced, combined}`, `_edge_error_renderer`
  6 arms (those + `alias`). Reachable under `_CASCADE_SEAL_POLICY`
  with no `expected_routing` is exactly those sets (`projection`
  excluded by `require_model_rows=False`; `routing`/`evaluated` excluded
  by no routing/evaluation contract; `alias` only at edge where a
  required alias exists). Count 1 definition
  (`django_strawberry_framework/utils/querysets.py::_defect_message`).
  Owner: defect-code owner. Both sites re-derived from AST, not inherited.
- Recourse separation: three literals pairwise distinct —
  cascade `permissions.py::_ASYNC_RECOURSE` (names `aapply`, `fields=`
  escape), write `mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE`
  (names `has_permission`/`check_permission`, bool), gate
  `utils/permissions.py::_GATE_ASYNC_RECOURSE` (names
  `check_<field>_permission`). Count 1 here. Owner: each surface keeps
  its own sentence. Rejected consolidation.
- Awaitable absence: zero `reject_async*`/`_dispose*` defs or calls,
  zero `awaitable` mentions, exactly one `await`. Refusal rides the
  runner (`reject_async_in_sync_context`, coroutine closed,
  `SyncMisuseError` + cascade recourse). Count 0 here. Not a member;
  consumer role only.
- Hook vocabularies: cascade `get_queryset`-only (no `has_permission` /
  `check_permission` token in target); write `has_permission` /
  `check_permission` bool deny-by-default; gates
  `check_<field>_permission` per-field fire + per-class dedup. Three
  contracts, three reasons to change; order cascade-first-then-gates is
  load-bearing (`test_cascade_then_filter_*` /
  `test_cascade_then_order_*`). Rejected unification.
- Edge taxonomy: `_is_cascadable_edge` (`isinstance ForeignKey` +
  `column is not None`; O2O incl. MTI `_ptr` in, reverse/M2M/GFK/
  GenericRelation/multi-column out) + `_edge_plan` (`lru_cache`,
  shared slice) + `_EdgePlan` record. Count 1. Owner stays here,
  file-local.
- GFK preflight: `_is_unsupported_forward_edge`
  (`is_relation and not ForeignObjectRel and not many_to_many and not
  one_to_many and not cascadable`) + full-walk preflight raising before
  any hook + `fields=` naming-unsupported raising dedicated error.
  Count 1. Owner here, file-local.
- Fields grammar: `None`→`None`, `[]`→`set()`, scoped set validated;
  bare-string / non-iterable / non-string / unhashable / unknown /
  unsupported each raise `ConfigurationError` (never raw `TypeError`).
  Count 1 (`_validate_fields`). Owner here, file-local.
- ContextVar state: frozen `_TraversalState(alias, active, path)` +
  `_cascade_state: ContextVar[...|None]` token `set`/`reset` in
  `finally` at root and per-edge frame. Count 1. Owner here,
  file-local. WSGI/ASGI + `sync_to_async`-copy isolation by construction.
- Cycle escape: `cls in state.active` raises path-rich
  `_cycle_error`; only `names_to_walk == set()` (`fields=[]`) returns
  the direct narrowing. Count 1 (branch + renderer). Owner here,
  file-local.
- Re-projection: `_validated_target_subquery` rejects field-specific
  `distinct(...)`, grouped (`group_by is not None`), annotation/`extra`
  alias shadowing `target_field.attname`, then `.values(attname)`.
  `to_field` binds its own column by construction. Count 1. Owner here,
  file-local.
- Vestigial pair: `_cascadable_edges` + `_cascadable_edge_names`
  production readers only this file (package-wide grep: both lists ==
  `["django_strawberry_framework/permissions.py"]`; tests read the plan
  directly). Count 0 production readers break on delete. Principle-11
  KANBAN-homed, not a family.
- Alias re-export: `SyncMisuseError as SyncMisuseError` redundant-alias
  form (the `types/relay.py` convention); `P.SyncMisuseError is
  Q.SyncMisuseError`; zero `class SyncMisuseError` here, one in owner;
  already in root `__all__` via `types`, so zero new public names.
  Count 0 new names. Posture holds.

### Enumeration (member-by-member vs own count)

W1: 30 = 1 doc + 12 imports + 1 Assign + 2 ClassDef + 1 AnnAssign +
12 FunctionDef + 1 AsyncFunctionDef. W2 `ast.parse`: identical —
`Expr` 1, `ImportFrom` 11, `Import` 1, `Assign` 1 (`_ASYNC_RECOURSE`),
`ClassDef` 2 (`_TraversalState`, `_EdgePlan`), `AnnAssign` 1
(`_cascade_state`), `FunctionDef` 12 + `AsyncFunctionDef` 1 in the exact
order W1 tables (verified name-by-name in `w2_trace.py`). 30/30 land as
W1 homes: 0 docstring→projection F1–F8; 1–12 imports→F1–F5,R9; 13
`_ASYNC_RECOURSE`→F6 rejected; 14–15 traversal record+slot→R4; 16–19
plan record + two predicates + plan owner→R1/R2; 20–21 accessors→R8;
22 scope validator→R3; 23–24 renderers→F5 consumers; 25 re-projection→R6;
26 cycle message→R5; 27–28 root+walk→F1/F2/F4 + R2/R3/R5/R7; 29 async
twin→F3. AGREE. No member unassigned; every challenge C1–C16 ends in a
family row or file-local record.

### Matrix vs real surface

1. Cross-flavor mirroring: AGREE — compared by behavior (queryset
   narrow vs bool write vs per-field input gate), separation stated at
   write owner, order pinned by cascade-then-gate oracles. Unified form
   considered and rejected in F8.
2. Sync/async twins: AGREE — one `_walk`, one `await`, wrapper shape;
   `async def` hook raises identically from both (no awaiting context in
   worker thread). Principle-5 write-pipeline shape recorded at owner.
3. Derived knowledge: AGREE — `_edge_plan` shared slice (`lru_cache`
   identity re-verified), `target_field.attname` at composition time,
   `alias=queryset.db` threaded, one policy const x2 passes. The
   `_validate_fields` inline `frozenset(... plan.cascadable)` composes
   `_edge_plan`, not `_meta`; with R8 KANBAN-homed for deletion there is
   no second owned derivation. Not a missed consolidation.
4. Round-trip pairs: AGREE — root/edge renderers (5 vs 6 arms, exactly
   reachable), `None`/`[]` scope pair. No other grammar here.
5. Contracts in other media: AGREE with one erratum (below) — oracles
   are `tests/test_permissions.py` narrowing/error/alias/SQL-shape rows
   (independent) plus classification pins honestly graded as
   owner-reading, live-tier `test_products_api.py` cascade rows +
   `test_products_visibility_api.py` optimizer rows (projections),
   module docstring eight bullets + GLOSSARY + spec-034 pointer
   (projections). No oracle rewritten to read its expectation from the
   owner it checks.
6. Enforcement by omission: AGREE — (a) forward-edge coverage
   re-verified on real `_meta` (`Category=[]`, `Item=[category]`,
   `Entry=[item, property]`); skips/failures each have a contract source;
   (b) child-alias three seeding surfaces correctly routed
   (`permissions.py` guarded here, `filters/sets.py` pinned, walker D1
   ledgered elsewhere).

Erratum (non-blocking): W1 `### Matrix` axis 5 says “60 test titles”;
fresh `ast.parse` of `tests/test_permissions.py` counts 62
`test_*` defs (list in verification scratch output). Coverage claim is
unaffected (the two extra titles are within the same narrowing/error/
alias families); Worker 0 should correct “60” → “62” in place. Not a
product defect, not a revision trigger.

### Counts + roles; no oracle rewritten

C1→1, C2→1, C3→1, C4→2, C5→1+arms, C6→1-here, C7→0-here, C8→1, C9→1,
C10→1, C11→1, C12→1, C13→1, C14→1, C15→0-refused, C16→0-break all
re-derived and AGREE. Roles hold: seal/seed/boundary owners elsewhere,
this target consumer/enforcement only; oracles independent except the
two predicate-pin groups W1 already grades as owner-reading
(`ScopeModel` per-kind pins, MTI `ptr` pins); live-tier rows are
projections. `git log` shows no test rewrite in this item (zero tracked
changes); nothing reads its expectation from the owner.

### Equivalence (principle 8)

Inspection suffices for import moves composed by name (F4 seed/model
reads — no ordering/transactional/async content; `static-reviewed`).
Execution evidence re-ran green for everything ordering/transactional/
async-adjacent: `w2_trace.py` (identity/count/shape/absence: twin wrap,
policy fields, arm diffs, alias pins, recourse distinctness, re-export
identity, plan identity) + `w2_behavior.py` (validator six malformed
shapes raise; plain re-projects to `id`; distinct/grouped/shadowing
vectors raise) + W1 `probe_w1.py`/`probe_w2.py` (`ALL OK` re-observed).
Each rejects its wrong result (“second walk”, “twin awaits hooks”,
“missing arm”, “floating seed”, “one recourse”, “malformed scope
escapes”, “grouped repaired”, “shadow composes”). Observable behavior
preserved vacuously — zero production edits, so no new behavior to
prove equivalent; the probes prove the claimed sameness holds.

### Zero-edit; coverage + assignment; routing

`git diff 5cecc2e4068f7f789ced97459a277efa4ebe3a2f --
django_strawberry_framework/permissions.py` empty (re-measured after both
W2 probes); working blob `757dce34…` == `HEAD:` == item baseline.
`git status --short` shows only concurrent dirt plus untracked DRY
artifacts/probes — untouched. Backstop discharged 30/30; every rule in
an indexed family (F1–F5 consumers/enforcement, F6+F8 rejected, F7
checked-not-member) or a file-local record (R1–R9, R8 KANBAN-homed).
No consolidation inside a file item by construction; any candidate
(e.g. the `_validate_fields` inline vs `_cascadable_edge_names`) routes
to its holding family — here correctly held file-local with the
delete-vs-keep owned on its KANBAN card. Zero-edit legitimate.

### Rejections; fingerprints; gates; pending

- F6 recourse: AGREE — four clauses differ (twin naming + `fields=`
  escape vs write-subject vs relay-async-possible); trigger (async-native
  walk or collapse to subject-noun-only difference) and durable homes
  (`utils/querysets.py::sync_pipeline_recourse` declining +
  `permissions.py::_ASYNC_RECOURSE` stating its own) correct. Family
  `sync-boundary-recourse-wording` stays `rejected`.
- F8 vocabulary: AGREE — contract difference (row-narrowing composable
  queryset vs bool deny-by-default vs per-field input gate; merging adds
  validator rejection to an equality test or drops the fail-closed raise;
  cascade-first order load-bearing against existence leaks) and trigger
  (one hook returning queryset+verdict) correct. Endorse the proposed
  rejected index row (exact text for Worker 0 below). Durable homes
  (write + gate module docstrings) correct; not written here.
- No other rejection owed (F7 correctly checked-not-member, not a
  rejection).
- Freshness (fresh `git hash-object`, all match W1): target `757dce34…`,
  querysets `1539b66c…`, `tests/test_permissions.py` `4a1d7775…`,
  `filters/sets.py` `4ab65a26…`, `optimizer/walker.py` `9b111ed9…`,
  `mutations/permissions.py` `54f770ae…`, `utils/permissions.py`
  `9889d6fe…`. Searched population (117 package files for a second
  seal body; package-wide grep for vestigial readers) as stated.
- Structural gates: owned by the family items (correct for a file
  item). This target contributes hostile-clone/override rows
  (`test_hostile_hook_clone_override_*`,
  `test_hostile_values_override_*`, unsealable-`Query` rows) — present
  and green by inspection (`static-reviewed`); a hand copy of the
  owner's body passes every behavior oracle, so the gate must be the
  seal's type-identity checks. Failability proof deferred to the family
  items (no red gate born here; red would be a defect, none found).
- Pending: W1 entry 1 belongs under `## Pending execution` with its
  exact command (target reaches alias decisions, so sharded mode is NOT
  `inapplicable by construction`): `FAKESHOP_SHARDED=1 uv run pytest
  tests/test_permissions.py -k "multi_db or alias or pinned" --no-cov`
  (needs the maintainer auth; discharges F2’s live-second-connection consequence;
  lazy-state pins already `execution-verified`). Postgres cells:
  `inapplicable by construction` (target reaches no dialect or
  pk-magnitude decision — pure ORM `Q`/`.values`/alias composition;
  no raw SQL, no dialect branch). Plan tick therefore `verified,
  pending execution`.

### AGENTS.md prose check

`path::Symbol` citations throughout, no raw `path:NN`; LINK
DEFINITIONS block intact; no process provenance; no tests owed or added
(zero-edit file item, strongest-tier oracles already exist at
`tests/` + live `test_query/`); no `ruff` owed (no tracked `.py`
edited; W2 probes are exempt per-cycle scratch under
`docs/dry/temp-tests/dry-file-permissions-w2/`); line-length/markdown
scaffold unaffected. PASS.

### Verdict

`Status: verified` — per-row agreement on every finding (one non-blocking
count erratum noted above), 30/30 enumeration verified member-by-member,
7/7 fingerprints re-hashed and matching, negative-control routing
correct, pending-execution row confirmed, no defects, zero edits.

## Defects (Worker 2)

None. Every claim checked while tracing held (twin wrap, both seal ends
on the cascade policy, both renderers exactly their reachable arms,
alias pin/seed/guard, three recourses pairwise distinct, re-export adds
no public name, `fields=` ladder never escapes as `TypeError`,
grouped/distinct/shadowing vectors fail closed, classification pins
match the bodies). The two KANBAN-homed notes W1 cites (`is_relation`
`getattr` hardening; vestigial-accessor delete-vs-keep) are already
owned and are not re-homed here. The “60 vs 62” title count is an
artifact erratum for Worker 0 to correct in place, not a routed product
defect.

## Iterations

### Scoped re-trace (run 7, `0.0.15 2026-09-28-7`, pass stale7-1)

Scope: the drift `git diff 5ee86193..0c0537e2 --
django_strawberry_framework/permissions.py` (6+/7-) carries exactly four
hunks, traced at HEAD bytes (blob `72102cc0`; worktree `ef66f8b9` is HUNT
`truth.*` dirt, 25+/24-, attributed by diff content against `git show
HEAD:`, untouched — it rewrites `__name__`/`isinstance`/`{!r}` lines only
and no hunk lands inside the four drift sites). Prior sections stay as
verified evidence about `5cecc2e4`/`5ee86193` bytes; nothing above is
rewritten. Findings no drift hunk touches STAND without re-review, per
the dispatch. Zero tracked edits; no production edit is owed by a file
item.

Hunk map (all four read off `git show HEAD:`, never the worktree file):

- H1: the `from .utils.querysets import (...)` statement gains the name
  `_UNSEALABLE_STATE_CAUSES` (8th name in the existing statement; no new
  statement).
- H2: `_root_error_renderer` `untrusted` arm — the two-line 3-cause
  literal plus `Pass plain query state` recourse becomes `f"and
  {_UNSEALABLE_STATE_CAUSES}"`; the subject/detail/middle framing
  (`apply_cascade_permissions for {name} got a root queryset ... cannot
  be sealed ... ({detail}); the cascade narrows a rebuilt queryset
  rather than the caller's object, and ...`) is kept word for word.
- H3: `_edge_error_renderer` docstring — the inline cause enumeration
  (`a foreign Query class, a foreign row iterable, or malformed
  deferred-filter state`) becomes the pointer
  ``utils/querysets.py #"_UNSEALABLE_STATE_CAUSES = ("``.
- H4: `_edge_error_renderer` `untrusted` arm — the three-line 3-cause
  literal plus `Return plain rows` recourse becomes the same composed
  tail; the subject/detail/middle framing (`{name}.get_queryset returned
  a queryset ... cannot be sealed ... ({detail}) for the cascade
  subquery on {edge}; the cascade re-projects the sealed queryset to the
  edge's target column, and ...`) is kept word for word.

The constant's own comment at HEAD (`querysets.py` above
`_UNSEALABLE_STATE_CAUSES`) states the authorship contract this
recomposition implements: each surface prefixes its own subject and the
defect detail while the cause list and advice stay one text. The two
cascade arms are now surfaces under that contract.

REVISE (drift touches the recorded reasoning; fingerprints refreshed to
HEAD blobs in the table below):

- F5 (seal-defect-code-wording consumer). Arm sets CONFIRM: root arms
  re-derived at HEAD as exactly `{type, table, untrusted, sliced,
  combined}` (5) and edge arms as those plus `alias` (6), keys
  byte-identical to the recorded ladders, still no
  `projection`/`routing`/`evaluated` — H2/H4 recompose arm bodies, never
  arm keys, and H1/H3 move no arm. Reachable-set challenge C5 (1
  definition + arms at reachable sites) CONFIRMS. REVISED clause: "each
  message site renders only the subset IT can reach, in its own prose"
  now reads — the reachable-subset rule stands; the cascade keeps its
  subject/detail/middle framing prose per end, while the
  cause-list-plus-advice clause is composed by name from
  `utils/querysets.py::_UNSEALABLE_STATE_CAUSES` (both ends are
  consumers of it). The new-cause challenge ("an eighth unsealable cause
  must be named" forces 1 definition) lives at the constant and is
  already indexed there; nothing about it is decided here.
- Matrix axis 4 (round-trip pairs). The arm-count core CONFIRMS (root 5,
  edge 6, both exactly the reachable set — re-derived above; H1/H3
  examined and move no arm). REVISED clause: "this file only supplies
  prose through its seam" now reads — the seam supplies cascade framing
  prose and composes the shared cause-plus-advice clause; seal/unseal
  direction stays owned by the boundary.
- Enumeration members 1–12 (imports). 30/30 CONFIRMED at HEAD by fresh
  `ast.parse` of `git show HEAD:` bytes: kinds identical (`Expr` 1,
  `ImportFrom` 11, `Import` 1, `Assign` 1, `ClassDef` 2, `AnnAssign` 1,
  `FunctionDef` 12, `AsyncFunctionDef` 1), def/class order identical
  (15 names), 1 `await` node, 1 `_walk` def, exactly 2
  `policy=_CASCADE_SEAL_POLICY` passes, 4 `_UNSEALABLE_STATE_CAUSES`
  references (1 import + 2 arms + 1 docstring = exactly H1–H4). Zero
  additions, zero removals, zero renames — every home in the table
  stands. REVISED text: the import row's "seven boundary names" is now
  eight (H1 adds a name to the existing statement, not a statement).

CONFIRM (drift touches the sites; every recorded claim re-derived true
at HEAD):

- F1 (sealed-execution-queryset consumer). H1–H4 examined: the renderer
  identities and roles are unchanged (still the cascade's two error
  seams), policy passes still exactly 2, runner composition (one
  `_prepared_visibility_source` call, one `apply_type_visibility_sync`
  call) byte-identical outside the drift. C1 still forces 1 definition
  elsewhere.
- C5 challenge row. Count (1 definition + arms) and "this file's two
  sites stay correct" both re-derived true via the arm-key derivation
  above.
- W2 defect-ladder trace, W2 enumeration, W2 matrix-4. All counts
  re-derived identical at HEAD (5/6 arms, 30/30 with the same kind
  split, `None`/`[]` scope pair untouched). W2's text stands; the
  cause-list authorship move is recorded once in the F5 revision above.
- Defects-none. "Both renderers declare exactly their reachable arms"
  re-derived true. The recomposition fails loud, never silent (a missing
  constant is an import-time `ImportError`, not a weakened message).
  Oracles moved with the wording on main — the legitimate
  production-plus-oracles shape: HEAD `tests/test_permissions.py` carries
  `test_a_hook_carrying_a_consumer_expression_names_what_the_cascade_can_rebuild`
  and `test_a_root_carrying_a_consumer_expression_names_what_the_cascade_can_rebuild`,
  which pin the new cause-plus-advice substrings (`a consumer-defined
  expression, lookup`, `Build the queryset with Django's own`) and assert
  both retired recourses absent (`Return plain rows` / `Pass plain query
  state` `not in message`); the two cascade-prose `match=` rows still
  match the kept framing; `faithfully rebuilt` still occurs exactly
  twice (both test docstrings, unchanged since `5ee86193`). No new
  defect; nothing routed.

STAND (no drift hunk touches the reasoning; not re-reviewed): F2, F3,
F4, F6, F7, F8; R1–R9; matrix axes 1, 2, 3, 5, 6; challenges C1–C4,
C6–C16; `## Pending execution` (the sharded F2 row); `## Judgment`
(F1–F5 still terminate in their indexed families as
consumers/enforcement — F5's consumer posture deepened, which the
revision above records); the remainder of the W2 sections.

Definition-count judgment: this file's recomposition CONFIRMS the
constant's authorship and moves no definition count of its own. The two
cascade arms are 2 of the 5 verified composers (3 in-file querysets arms
+ these 2), H1 is the verified import, H3 is 1 of the 2 verified prose
cites — the verified run-7 querysets re-trace cites `permissions.py:400`
and blob `72102cc0`, both matching digit-for-digit. Per that verified
verdict the per-site wordings were never counted as definitions, so the
authorship move (2 per-site spellings become 2 consumer compositions)
changes no count; no new `def`/`class`/assign lands here (30/30, zero
additions).

Holding-family consequences: `seal-defect-code-wording` — the adoption
row (`Unsealable-state cause-list wording single-source`, covering
`utils/querysets.py` + `permissions.py`) is already indexed as open;
this pass confirms the permissions-side consumer evidence for it. No new
row, no status change (O1 homing still rides closeout; not this item's).
Every other family covering `permissions.py`
(`sealed-execution-queryset`, `child-queryset-alias-inheritance`,
`one-sync-boundary`, `queryset-seed-and-model-read`,
`sync-boundary-recourse-wording` (rejected),
`awaitable-refusal-and-disposal`, the `Boundary ContextVar` and
`hook-context-vs-traversal-state` rejections): the drift touches none of
their rules — no consequence. (Worker-0 routes; the plan is untouched by
this pass.)

Observation for Worker-0 (not a revision trigger, no verdict moves on
it): no `## Responsibility index` row is homed at File `permissions.py`
— the R1–R9 file-local records and F8's proposed rejected row were never
transcribed. Gap dates from the original pass, not from this drift.

Fingerprint table (recorded pins are `5cecc2e4` bytes; re-hashed at
HEAD; `5ee86193` shown for the cause window — `5cecc2e4` is not an
ancestor of `5ee86193`, so pre-window and window ranges are cited
separately; worktree hashes record HUNT dirt, never relied upon):

| Input | Recorded | HEAD | Worktree | Verdict + cause |
|---|---|---|---|---|
| `django_strawberry_framework/permissions.py` | `757dce34…` | `72102cc0` | `ef66f8b9` | STALE — window drift is exactly H1–H4 (`5ee86193` matched recorded at `757dce34`); worktree adds the content-attributed `truth.*` dirt |
| `django_strawberry_framework/utils/querysets.py` | `1539b66c…` | `3616927d` | `8fc556d5` | STALE — pre-window `1539b66c`→`b68be0e3` plus window `b68be0e3`→`3616927d` (the constant; verified querysets re-trace) |
| `tests/test_permissions.py` | `4a1d7775…` | `384f451b` | `c22af728` | STALE — pre-window `4a1d7775`→`943dcb49` plus window `943dcb49`→`384f451b` (includes the 2 recomposed-wording oracle rows examined above) |
| `django_strawberry_framework/filters/sets.py` | `4ab65a26…` | `993e887a` | `e47c6758` | STALE — pre-window `4ab65a26`→`722e0c77` plus window `722e0c77`→`993e887a` (F2 sibling pin; F2 STANDS per scope) |
| `django_strawberry_framework/optimizer/walker.py` | `9b111ed9…` | `75f9c6b6` | `d5759ef8` | STALE — pre-window `9b111ed9`→`e8d80005` plus window `e8d80005`→`75f9c6b6` (F2 sibling pin; F2 STANDS per scope) |
| `django_strawberry_framework/mutations/permissions.py` | `54f770ae…` | `54f770ae` | `55e5edf8` | MATCH at HEAD (full `54f770ae5aa1238327246cd2dcb141e8aac14965`; worktree is hunt dirt) |
| `django_strawberry_framework/utils/permissions.py` | `9889d6fe…` | `9889d6fe` | `1c9cfd39` | MATCH at HEAD (full `9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`; worktree is hunt dirt) |
| Searched population (F1/R8: package `.py` files) | 117 files | 117 files, membership-identical (`diff` of `git ls-files` listings empty) | — (untracked hunt files excluded from a HEAD comparison) | MATCH |

Result: 3 MATCH / 5 STALE, every STALE with its cause window. STALE
inputs whose findings STAND (filters/sets, walker, and the
non-wording remainder of the tests pin) are reported, not
adjudicated, per the scoped dispatch.

Literal index-row texts for new enumeration members: none — H1 adds an
imported name inside the existing `from .utils.querysets import (...)`
statement (member 11 of the 1–12 import run), not a member; the
enumeration re-derives 30/30 with zero additions, zero removals, zero
renames, so Worker-0 owes no transcription.

Provenance: read-only inspection in the shared tree only (`git show
HEAD:`, `git rev-parse`, `git hash-object`, `ast.parse` over piped HEAD
bytes, `grep` over `git show` output) — no `workspace.py` runs, no run
ids; no `.py` path touched, so no ruff owed; no `docs/dry/temp-tests/`
scratch (the two `/tmp/dry-perm-pop-*.txt` population listings ride with
the scratch-custody closeout decision). Item window vs
`cae309e937bc2324365792a2e7b64a98116cfdf7` holds this untracked artifact
only; `git status` shows no tracked edit by this pass. Pre-edit artifact
53605 B / `92d6f5ec`; post-edit size/hash in the report-back.

## Independent verification (Worker-2) — stale7 re-trace

Run: 0.0.15 2026-09-28-7. Address: `dry/dry-file-permissions-stale7/verify-1`.
Traced at HEAD bytes (HEAD `0c0537e2`, target HEAD blob `72102cc0`;
worktree `ef66f8b9` is hunt dirt — the `truth.*` migration plus its import —
traced only for fingerprinting, never for judgment). This section was composed
before opening W1's `## Iterations`; all counts below are re-derived.

### Own drift re-derivation

`git diff 5ee86193..0c0537e2 -- django_strawberry_framework/permissions.py`:
6+/7-, four hunks, all inside the defect-prose seam:

1. Import: `_UNSEALABLE_STATE_CAUSES` joins the existing
   `utils/querysets.py` ImportFrom (seven→eight names, same statement).
2. Root `untrusted` arm recomposed: the inline "a foreign Query class, a
   foreign row iterable, or malformed deferred-filter state ..." spelling is
   replaced by `{_UNSEALABLE_STATE_CAUSES}`; subject/detail/framing prose kept.
3. `_edge_error_renderer` docstring: the inline cause gloss is replaced by a
   `utils/querysets.py #"_UNSEALABLE_STATE_CAUSES = ("` citation.
4. Edge `untrusted` arm recomposed likewise (its "Return plain rows" advice
   now lives inside the constant).

No seal call-site, policy, arm-count, twin-shape, validator, or alias change.
`git grep _UNSEALABLE_STATE_CAUSES 5ee86193` finds nothing (the constant is
window-new); at HEAD there is 1 definition (`utils/querysets.py` line 3733) +
5 code composers (3 owner-file at lines 3769/3894/4015 + these 2 arms) + 2
docstring citations (1 here, 1 owner-file). The run-7 querysets re-trace (queue
item b1, verified) already established the constant moves authorship only.

### Own per-finding expectations

- REVISE F5 (seal-defect-code-wording consumer): cause-list authorship moves
  to the constant; both arms stay consumer composition by name (the
  subject/detail/framing prose remains cascade-local and load-bearing — the
  path-rich edge seam). Arm counts unchanged.
- REVISE axis 4: the renderer-pair description must note the composed
  untrusted arms plus the docstring citation; the pair structure is unchanged.
- REVISE the enumeration import row: seven→eight boundary names; the
  statement count stays 30/30 (verified on HEAD bytes: `ast.Module.body` is
  30 members with kind counts identical to recorded — 12 FunctionDef, 1
  AsyncFunctionDef, 2 ClassDef, 1 Assign, 1 AnnAssign, 11 ImportFrom, 1
  Import, 1 Expr — and 12 imports).
- CONFIRM F1 (seal shape byte-identical: 1 `_walk` def, 2
  `policy=_CASCADE_SEAL_POLICY` passes), C5 (reachable-code sets unchanged
  under the unchanged `_CASCADE_SEAL_POLICY`), the W2 ladders (root 5 arms
  `{type, table, untrusted, sliced, combined}`, edge 6 — those plus `alias`
  — re-derived from the HEAD AST), and defects-none.
- STAND everything else (F2/F3/F4/F6/F7/F8, R1–R9, axes 1/2/3/5/6): no drift
  hunk touches them, so re-review is not owed.

### Own definition-count and owner judgments

- The recomposed arms confirm the constant's authorship as consumer
  composition by name: both arms interpolate the imported constant and restate
  no cause text. The cascade framing prose is not part of the constant's
  contract (each surface keeps its own subject/detail — exactly what the
  constant's own comment prescribes).
- Nothing moves a definition count in this file: wording definitions owned
  here before = 0 (the arms were always consumer arms — C5 "1 definition +
  per-site arms"), after = 0. The 2 arms are 2 of the 5 verified code
  composers; no new definition, no new family member.
- The import-name addition is correctly a non-member: the enumeration counts
  `ast.Module.body` statements, and the 8th name rides the existing ImportFrom
  → 30/30 zero delta, zero removals.

### Own fingerprint expectations (7 recorded pins)

Method: `git rev-parse <commit>:<path>` per commit for tracked blobs,
`git hash-object <path>` for worktree bytes; HEAD-vs-recorded compared as
commit blobs, worktree fingerprinted separately, never one against the other.

- The recorded pins are the `5cecc2e4` stash-tree bytes: all 7 match
  digit-for-digit at 8 hex (target `757dce34`, querysets `1539b66c`, tests
  `4a1d7775`, filters/sets `4ab65a26`, walker `9b111ed9`, mut-perm
  `54f770ae`, utils-perm `9889d6fe`). NOTE: the correct short is `5cecc2e4`
  (`WIP on t3code/1cc21548`); `5cecc2e2` does not resolve as an object —
  flagged for reconciliation against W1's spelling.
- `5cecc2e4` is NOT an ancestor of `5ee86193` nor of HEAD (dangling stash
  commit; its base `9031cb3d` IS an ancestor of `5ee86193`).
- Over the 7 recorded pins I derive 2 MATCH (mut-perm `54f770ae`, utils-perm
  `9889d6fe` — byte-identical through HEAD) / 5 STALE (target: window-only,
  `757dce34`→`72102cc0` with recorded==`5ee86193`; querysets / tests /
  filters-sets / walker: pre-window + window, recorded≠`5ee86193`≠HEAD;
  window churn lines: querysets 98, tests 1079, walker 181, filters-sets
  2-line prose-only). The briefed 3 MATCH / 5 STALE = 8 rows implies one
  added MATCH row W1 must name; judged on read below.

### Own family-consequence expectation

The adoption row is already indexed (`Unsealable-state cause-list wording
single-source`, owner the constant, files querysets.py + permissions.py,
holding Family seal-defect-code-wording, open) → no new row, no status
change, no literal index rows owed (the import name is not a member).
Confirmed zero index rows hold at File permissions.py (the original-pass
bookkeeping gap under the 2026-09-22 ruling) — noted without demanding
back-transcription.

### Reconciliation (read after recording the above)

Per-finding, W1 disposition → W2 judgment (all re-derived at HEAD bytes):

- Hunk map H1–H4 → AGREE. Identical four-hunk derivation (import + root arm
  + docstring cite + edge arm). Dirt extent re-measured at exactly 25+/24-,
  content-attributed as `truth.*` `__name__`/`isinstance`/`{!r}` rewrites;
  the three dirt hunks adjacent to drift sites (`-348,20`, `-405,8`,
  `-420,7`) change neighboring lines only — none lands inside H1–H4.
- REVISE F5 → AGREE. Arm keys re-derived byte-identical (root 5, edge 6, no
  `projection`/`routing`/`evaluated`); revised clause (framing-prose-local +
  cause-plus-advice composed by name) matches; new-cause challenge correctly
  left at the constant where it is already indexed.
- REVISE axis 4 → AGREE. Pair structure unchanged; seam clause correctly
  reworded to framing-plus-composed-clause.
- REVISE enumeration import row → AGREE. 30/30 re-derived on HEAD bytes with
  identical kind split, 12 imports, 1 `await`, 1 `_walk`, 2 policy passes, 4
  constant references (import + 2 arms + docstring); seven→eight names, zero
  additions/removals/renames; every home stands.
- CONFIRM F1 → AGREE. Renderer identities/roles, 2 policy passes, and both
  runner compositions unchanged outside the drift; C1 still forces 1
  definition elsewhere.
- CONFIRM C5 → AGREE. Count (1 definition + arms) and both-sites-correct
  re-derived via the HEAD arm keys.
- CONFIRM W2 ladders / enumeration / matrix-4 → AGREE. 5/6 arms, 30/30 with
  the same kind split, `None`/`[]` pair untouched — all re-derived identical.
- CONFIRM defects-none → AGREE. Fail-loud argument is sound (missing
  constant = import-time `ImportError`); both new oracle tests verified
  present at HEAD (`test_a_hook_...` line 1216, `test_a_root_...` line 1411),
  pinning the new substrings and asserting each retired recourse absent;
  `faithfully rebuilt` occurs exactly twice at HEAD and twice at `5ee86193`
  (test docstrings); framing prose is word-for-word kept per the drift diff,
  so framing `match=` rows still match.
- STAND rest → AGREE. F2/F3/F4/F6/F7/F8, R1–R9, axes 1/2/3/5/6, C1–C4/C6–C16,
  Pending execution, Judgment, and the W2 remainder are all untouched by H1–H4
  on the stated reasons; re-review correctly not owed.
- Definition counts (2 of 5 composers, no count moves) → AGREE. Composer
  census independently re-derived: 1 definition + 5 code composers (3
  owner-file + 2 here) + 2 docstring cites; per-site wordings were never
  counted as definitions, so 0→0 here; the querysets-artifact cross-cites
  (`permissions.py:400`, blob `72102cc0`) match digit-for-digit.
- Import-name non-member → AGREE. The 8th name rides member 11 of the import
  run (statement-count instrument) — correctly not a member, no index text owed.
- Fingerprints 3 MATCH / 5 STALE → AGREE. All 7 pin rows match my hashes
  digit-for-digit (recorded, `5ee86193`-window, HEAD, worktree); every STALE
  carries its pre-window + window cause; the 8th MATCH row (searched
  population, 117 files membership-identical) is a legitimate added input,
  re-derived via `git ls-files` diff (empty). This resolves my pre-read
  2-vs-3 question: my 7-pin derivation was complete, and the 8th row is named.
- Pin-note substance (exact-bytes + not-an-ancestor) → AGREE, with one
  non-blocking erratum below. All 7 pins are the stash-tree bytes and the
  stash commit is dangling (base `9031cb3d` on main history).
- Holding-family consequence → AGREE. Adoption row already indexed and open;
  permissions-side consumer evidence confirmed; no new row, no status change;
  the no-row-homed-at-this-file observation is correct (original-pass gap)
  and correctly not a revision trigger — back-transcription not demanded per
  the 2026-09-22 ruling.
- No literal index rows owed → AGREE. Import name is not a member; 30/30
  zero delta.
- Provenance → AGREE. Read-only inspection only; zero `.py` touched (target
  worktree hash still `ef66f8b9`, identical to the dispatch record); no ruff
  owed; `/tmp` listings ride with scratch custody like the sibling passes.

Erratum E1 (non-blocking, Worker-0 corrects in place — not a revision
trigger): the fingerprint-table intro spells the stash short as `5cecc2e2`
(twice); the object is `5cecc2e4` (`WIP on t3code/1cc21548`; `5cecc2e2` does
not resolve). Substance is unaffected — the full SHA is present in-artifact
(`## Implementation (Worker 1)` line) and every byte claim verifies true —
but a freshness note should name a resolvable object. Same in-place class as
the original pass's "60→62" erratum. (Worker-0's plan record repeats the
short; the plan is Worker-0's to fix.)

### Nothing-else-changed + prose checks

- Prior sections untouched by this pass: my append starts after W1's stated
  post-edit end; Status line swap below is the verdict edit. W1's own
  append-only shape (Status swap + EOF `## Iterations`, pre-edit 53605 B
  matching the plan) is structurally consistent.
- No production edit, no plan edit, no tracked file touched by either
  run-7 worker on this item: item window vs
  `cae309e937bc2324365792a2e7b64a98116cfdf7` holds the plan (Worker-0's)
  plus this untracked artifact only.
- AGENTS.md prose: `path::Symbol` citations throughout both appended
  sections; the two `path:NN` cites sit in a `docs/dry/dry-*.md` per-cycle
  artifact where the form is allowed; no new reference-style links (LINK
  DEFINITIONS block still sufficient); no process provenance beyond the
  standard read-only method note.
- Ruff: none owed — zero `.py` paths touched (confirmed via the unchanged
  `ef66f8b9` worktree hash, not merely asserted).

### Verdict

`Status: verified` — every W1 disposition AGREE-re-derived at HEAD bytes,
8/8 fingerprints digit-for-digit, family consequence endorsed, no defects, no
pending execution, one non-blocking erratum (E1) for Worker-0's in-place
correction.

## Scoped re-trace (run 8) — Worker 1

Scoped run: `0.0.15 2026-09-30-8`. HEAD `83998e08` at start,
verified unmoved at finish (`git rev-parse HEAD` both times).
Prior text above is prior evidence only and stands untouched;
this section appends. Zero production edits; a file item owes
none. Every claim below is traced at HEAD bytes unless marked
worktree or pre-merge; the worktree is read only for hunk
attribution. Three read-only probes, `/tmp`-only, no Django
import, no pytest: `/tmp/perm_r8_enum.py` (36 checks),
`/tmp/perm_r8_delta.py` (7 checks), `/tmp/perm_r8_oracles.py`
(35 checks) — 78/78 `ALL OK`.

### Scope of the delta (drift base → HEAD → worktree → pre-merge)

Drift base `0c0537e2` → HEAD `83998e08` on the target is 4
commits, 77+/64-. One is behavior-bearing, re-read in full:

- `5c5e32c5` (12 `-U0` hunks, 39+/36-): the cascade ends
  rewritten for pk-set serving. Module bullet (hook returns
  "unsliced (a `union()` etc. arrives as its primary-key
  set)"); the boundary import gains `_COMBINED_WHAT` (9th
  name, same statement); `_root_error_renderer` docstring
  (`reject_combined` → `rewrite_combined`, reachable codes
  still `type` `table` `untrusted` `sliced` `combined`) and
  its `combined` arm (inline refusal → cascade subject +
  `_COMBINED_WHAT.format(...)`); `_edge_error_renderer`
  docstring (same axis swap) and its `combined` arm (same
  recomposition); `_validated_target_subquery` docstring
  (combinator "answered one layer up" as a pk set, refused
  when the set would change rows); `apply_cascade_permissions`
  docstring + seal comment (same). Package-wide at HEAD
  `reject_combined` is 0 hits in package + tests + examples
  (`git grep | wc -l`), and the old inline combined wordings
  survive nowhere: both cascade arms compose the shared text
  by name.

The other 3 commits are proved non-behavioral on this target
by full-diff read (every hunk): `999a1aab` (3+/3-),
`b20277fe` (33+/24-), `dfbea72b` (2+/1-) are annotations
(`Any` → narrow types, `Callable`, `TypeGuard`), the
`collections.abc` import, the `TYPE_CHECKING` guard, one
local rename (`requested` → `entries` in `_validate_fields`,
same statements), and one `# type: ignore[redundant-expr]`
with its mypy comment. The delta probe confirms mechanically
(base → HEAD per-symbol, annotations stripped, docstrings
split out): 15/15 symbols present both sides, 0 added, 0
removed; code-differing exactly `_root_error_renderer`,
`_edge_error_renderer` (the two arm recompositions) and
`_validate_fields` (the rename); doc-differing exactly the
two renderers, `_validated_target_subquery`, and
`apply_cascade_permissions`; module docstring differs in
exactly the combined-serving bullet.

HEAD → worktree is 38 `-U0` hunks, 42+/36-, worktree blob
`42c3c19c`. NO owned ledger hunk names this file: all dirt
is concurrent, attributed by content against `git show
HEAD:` (full diff read). Categories: the `utils/truth.py`
migration (1 import + 20 `truth.name` for the 20 `__name__`
renders + 4 `truth.render` for the 4 `{!r}` renders + 2
`truth.is_instance` for the 2 validator `isinstance` tests +
the `name`/`edge` binds hoisted from closure-outer into
`_render`, 4 hunk fragments); 8 `(Decision N)` → `(spec-034
Decision N)` prose cites; the `_walk` single-filter
accumulation (`conditions` list + one `.filter(*conditions)`
with its comment); the `aapply` docstring first-line
rewrite. Mechanical screen: 37/38 hunks match the category
patterns, the 38th is the truth import itself, 0 unmatched.
Render-normalized AST proof (renders + annotations + strings
blanked): HEAD-vs-worktree delta is exactly the two
renderer hoists (remainder-identity proved: worktree
`_render` minus its leading binds equals HEAD `_render`)
and `_walk` (loop bodies equal modulo the tail swap);
module level is exactly +1 truth import. Nothing judged
from worktree bytes; nothing edited, reverted, or tidied.

Pre-merge bytes `9aaaad5d` (read-only evidence via `git
show`, never applied): target blob
`6c97d887744e2bb389e2fd957346540dacf85533` — pre-`5c5e32c5`
bytes (`reject_combined` prose, `requested` spelling, 0
`_COMBINED_WHAT`) carrying the tree's dirt (`truth.*` 24
hits, `conditions` accumulation, 8 spec-034 cites). The
merge took main's combined rewrite + typing under the
tree's render/composition shapes; no owned byte is at stake
on this target.

### Enumeration (fresh instrument at HEAD bytes)

Instrument: `ast.parse` over `git show HEAD:` bytes: **32
top-level statements** — 1 module docstring, 13 imports (12
`ImportFrom` + 1 `Import`), 1 `TYPE_CHECKING` guard, 1
`Assign` (`_ASYNC_RECOURSE`), 2 `ClassDef`, 1 `AnnAssign`
(`_cascade_state`), 12 `FunctionDef`, 1 `AsyncFunctionDef`.
Delta vs run-7's 30 is exactly +2, both typing-drift: the
`collections.abc` import and the `TYPE_CHECKING` guard. The
15 def/class names and their order are unchanged; 0 added,
0 removed, 0 renamed. The boundary import carries 9 names
(`_COMBINED_WHAT` joins the run-7 8, same statement).

Every member lands in a home; every challenge below ends in
one:

| Members | Home |
|---|---|
| 0 docstring | projection, F1–F8 (combined bullet re-derived) |
| 1–13 imports, 14 guard | machinery / consumers (F1–F5, R9) |
| 15 `_ASYNC_RECOURSE` | F6 (rejected, literals re-derived) |
| 16–17 traversal record + slot | R4, file-local |
| 18–21 plan record + two predicates + plan owner | R1/R2, file-local |
| 22–23 accessors | R8, file-local (KANBAN-homed) |
| 24 scope validator | R3, file-local |
| 25–26 renderers | F5 consumers (arms re-derived) |
| 27 re-projection battery | R6, file-local |
| 28 cycle message | R5, file-local |
| 29–30 root + walk | F1/F2/F4 consumers + R2/R3/R5/R7 |
| 31 async twin | F3 (consumer) |

No new family is named: the cascade walk stays sole-owned
here and file-local; the two composer memberships (pk-set
serving, shared combined text) converge onto the holding
families `sealed-execution-queryset` (s17) and
`seal-defect-code-wording` (s18), which own their rows.

### Matrix re-discharge (at HEAD bytes)

**1. Cross-flavor policy mirroring — CONFIRM.** The three
vocabularies are behaviorally where run-1 left them:
cascade narrows rows through `get_queryset` (target carries
0 `has_permission` / `check_permission` tokens, probe);
write decides bools through `has_permission` /
`check_permission` (owner
`django_strawberry_framework/mutations/permissions.py`,
typing-only drift, recourse literal byte-identical since
the drift base, probe); input gates judge supplied fields
through `check_<field>_permission` (owner
`django_strawberry_framework/utils/permissions.py`,
typing-only drift, recourse literal byte-identical, probe).
The three literals re-derive pairwise distinct at HEAD
(lengths 249/236/165). Separation prose intact at both
homes ("first-class, separate contract from row
visibility"; "owns mechanics only"). F8 stands.

**2. Sync/async twins — CONFIRM.** One `_walk` def, one
`await` node, `aapply` body is exactly `return await
run_in_one_sync_boundary(apply_cascade_permissions, ...)`
(probe). No second walk; the `async def` hook raises
identically from both variants (runner-owned refusal,
unchanged). Principle-5 write-pipeline shape, recorded at
the boundary owner. F3 stands.

**3. Derived rather than repeated knowledge — CONFIRM.**
`_edge_plan` still classifies once per model (bounded
`lru_cache`, shared by validator, preflight, walk);
`field.target_field.attname` still read at composition
time; `alias=queryset.db` threaded as state (1 pin, 1 edge
seed, 1 nested guard, probe); the seal option set still one
constant passed at both ends (exactly 2
`policy=_CASCADE_SEAL_POLICY` passes, probe). The
`_validate_fields` inline `frozenset(... plan.cascadable)`
still composes `_edge_plan`, never `_meta` (probe: no
`model._meta` in the validator). The policy constant's own
shape changed (axis swap, F1) but the single-owner read
here did not.

**4. Inverse / round-trip pairs — REVISE.** Arm-count core
CONFIRMS: root arms re-derived at HEAD as exactly `type`
`table` `untrusted` `sliced` `combined` (5) and edge arms as
those plus `alias` (6), keys byte-identical to the recorded
ladders, still no `projection` / `routing` / `evaluated`
(probe reads both dict literals out of the AST). The
`fields=None` / `fields=[]` scope pair is untouched.
REVISED clause: each end's `combined` arm now prefixes its
own subject and composes the shared combined-queryset text
(`_COMBINED_WHAT`) by name — the same composer shape run-7
recorded for the `untrusted` arms (`_UNSEALABLE_STATE_CAUSES`,
still 4 refs here, intact). The seal/unseal direction stays
owned by the boundary.

**5. Contracts restated in another medium — REVISE.**
Production (target + composed owners) and projections move
together legitimately. Oracle census at HEAD, fresh
instrument (AST `test_*` defs, the run-1/W2 instrument):
59, vs 57 at the drift base — exactly +2, the two new
served-rows tests
(`test_combined_hook_return_narrows_by_its_primary_key_set`,
parametrized union/intersection/difference;
`test_combined_root_is_narrowed_as_its_primary_key_set`).
(The prior "62" counted a pre-window tree; superseded, not
contradicted.) The old refusal rows are rewritten, not
dropped: `_hook_union` → `_hook_union_all` (`all=True`),
`_hook_intersection` → `_hook_intersection_values`
(`.values("id")`), `_root_combined` → `_root_combined_all`,
pinning the verbose lost-property wordings
(`union: union\(all=True\) keeps duplicate…`, probe). Live
tier gains `test_combined_visibility_api.py` with 3 cascade
rows (combined target, combined root, outer-values
refusal). Projections move with the behavior: the GLOSSARY
`apply_cascade_permissions` bullet (combined serving +
refusal list) and the `Sealed execution queryset` term.
Oracle independence grading stands: narrowing / error /
alias / SQL-shape rows assert rows, errors, or query
strings; the classification pins still read the helpers
from the owner (honestly owner-reading, not independent).

**6. Enforcement by omission — CONFIRM.** (a) Forward-edge
coverage: both predicate bodies are code-identical
base → HEAD (delta probe; annotation-only delta) and the
fixture models are identical (`products/models.py`: 0 drift
commits, clean in the worktree; `library/models.py` gains
only additive models whose new FK is a plain single-column
edge — no new edge kind). Same pure predicates + same
inputs ⇒ the recorded plans (`Category=[]`,
`Item=[category]`, `Entry=[property, item]`) and every
skip/fail-closed contract hold without re-execution. (b)
Child-alias inheritance: this target still the guarded
member (pin/seed/guard re-derived); siblings re-pinned at
HEAD — `filters/sets.py` still
`child_base = base_queryset(child_model, using=parent_db)`;
`optimizer/walker.py::_build_child_queryset` still seals
under `_LIST_RELATION_CHILD_POLICY` by default with
`_PREFETCH_CHILD_POLICY` for the nested-connection planner
(the ledgered D1 fix intact under the drift).

### Challenges (definition counts, authoritative only)

C1→1 (elsewhere: `_seal_or_defect`, via the same two runner
calls + policy const — composition unchanged). C2→1
(`base_queryset` spelling + seal alias arm). C3→1 (the
boundary). C4→2 (both elsewhere; `relay.py`'s raw-manager
read at `relay.py:297` survives at HEAD — the recorded
deliberate exception holds, s4 owns any deeper word).
C5→1 definition + per-site arms, REVISED: reachable sets
re-derived unchanged (root 5 / edge 6, keys identical); the
`combined` arms are now `_COMBINED_WHAT` composers (2 of 6
code composers: 3 owner-file — `_validate_post_orderset_result`,
`_visibility_result_error`, `_prepared_visibility_source`
— plus `optimizer/walker.py::_hint_prefetch_over_pk_set`
plus these 2; 1 definition + 2 docstring cites); a new
combined lost-property forces 1 definition at
`utils/querysets.py::_combined_lost_property`; the canon
order moved (`sliced` → `projection` → `combined` →
`alias`) with no cascade impact (`projection` unreachable
under `require_model_rows=False`). C6→1 here (literals
byte-identical; still rejected). C7→0 here (no body; e1
owner `_dispose_sync_awaitable` intact in querysets).
C8→1, C9→1 (predicate bodies identical, fixtures
identical). C10→1 (validator logic identical modulo the
read-verified local rename; all six malformed shapes still
raise `ConfigurationError`). C11→1 (state record/slot +
install sites untouched — `apply_cascade_permissions`
code-identical per the delta probe). C12→1 (cycle branch
untouched). C13→1 per layer, REVISED note: a new
re-projection-specific shape still forces exactly
`_validated_target_subquery` (battery body identical); a
new *combined* shape forces `_combined_lost_property`
(elsewhere) — the split is the documented layering (seal
answers combinators because they also block root
`.filter(...)`), not a second battery. C14→1 (null arm
untouched at HEAD; the worktree single-filter accumulation
is concurrent dirt composing the same conditions — read,
not judged). C15→0 refused. C16→0 production readers break
(package-only readers still this file alone; tests +
binary-DB hits as recorded).

### Findings: CONFIRM / REVISE ledger (18 + 6)

- **F1 sealed-execution-queryset (consumer) — REVISE.**
  Composition CONFIRMS (same two runners, same policy
  const, 2 passes). Re-derived under the new seal: the
  `reject_combined` axis is gone; `_CASCADE_SEAL_POLICY` is
  `_SealPolicy(require_model_rows=False)` with
  `reject_sliced=True`, `rewrite_combined=True` (defaults);
  a combinator at either cascade end is served as
  `Model.filter(pk__in=<combined>.order_by().values("pk"))`
  with outer column ordering + `reverse()` carried
  (`utils/querysets.py::_pk_membership_query_or_defect`),
  and only an unrepresentable shape fails closed with the
  `combined` defect (`utils/querysets.py::_combined_lost_property`
  names the lost property; audited slots pinned beside it).
  (Also corrects the recorded "five `_SealPolicy` fields":
  six, both before and after — the axis was swapped, not
  added.) Convergence onto Family
  `sealed-execution-queryset` (s17 owns the row).
- **F2 child-queryset-alias-inheritance — CONFIRM.** Seed,
  pin, guard, and both sibling pins re-derived at HEAD
  (matrix axis 6). The sharded consequence stays
  `unverified` (pending row carried).
- **F3 one-sync-boundary — CONFIRM.** Twin shape re-derived
  (matrix axis 2).
- **F4 queryset-seed-and-model-read — CONFIRM.**
  `model_for(cls)` ×1, `base_queryset(..., using=...)` ×1
  (probe); relay exception survives (C4).
- **F5 seal-defect-code-wording (consumer) — REVISE.** Arm
  sets CONFIRM (root 5 / edge 6, keys byte-identical).
  Revised clause: the cascade keeps its per-end framing
  prose and reachable-subset discipline, while the
  cause-list-plus-advice clause (`untrusted` arms, run-7)
  AND the combined-queryset clause (`combined` arms, this
  pass) are composed by name from
  `utils/querysets.py::_UNSEALABLE_STATE_CAUSES` (2 of 5
  code composers) and `utils/querysets.py::_COMBINED_WHAT`
  (2 of 6) respectively. Run-7's F5 revision stands and is
  extended, not superseded. Convergence onto Family
  `seal-defect-code-wording` (s18 owns the row; literal
  text proposed below).
- **F6 recourse rejection — CONFIRM.** All three literals
  byte-identical since the drift base and pairwise distinct
  at HEAD (probe); the four differing clauses and the
  trigger stand. Family stays `rejected`.
- **F7 checked-not-member — CONFIRM.** Zero
  `reject_async*` / `_dispose*` / `awaitable` tokens at
  HEAD (probe); refusal still rides the runner.
- **F8 vocabulary rejection — CONFIRM.** Three contracts,
  three reasons to change; cascade-first order still
  load-bearing; durable homes' prose intact at HEAD.
  Proposed rejected index row stands as offered.
- **R1 cascadable-edge classification — CONFIRM.**
  Predicate body code-identical (annotations only);
  fixtures identical; plan cache untouched.
- **R2 unsupported-edge preflight — CONFIRM.** Predicate +
  preflight + `fields=` dedicated error untouched
  (validator logic identical; the `getattr(is_relation)`
  note stays KANBAN-homed).
- **R3 `fields=` grammar — CONFIRM.** All branches
  identical modulo the read-verified `requested` →
  `entries` rename; malformed shapes still raise
  `ConfigurationError`, never raw `TypeError`.
- **R4 traversal state — CONFIRM.** Record, slot, and both
  install/reset sites untouched.
- **R5 cycle policy + `fields=[]` escape — CONFIRM.**
  Branch, renderer, and recourse rows untouched.
- **R6 re-projection battery — REVISE (prose context
  only).** The three checks + `.values(attname)` tail are
  code-identical (delta probe); the `to_field` binding and
  the shadowing fail-closed stand. Revised: the docstring's
  combined paragraph now reads pk-set-serving (seal hands
  the cascade a one-table query whose re-projection binds
  one column) with refusal for unrepresentable shapes —
  citing `_pk_membership_query_or_defect`, not the removed
  axis.
- **R7 per-edge composition — CONFIRM at HEAD bytes.**
  Registry skip, `using=` seed, `Q(__in)` + nullable-only
  `__isnull`, depth-1 walk, per-edge `.filter(condition)`
  all re-derived; the single-filter accumulation exists
  only in the worktree (concurrent, read-not-judged).
- **R8 vestigial accessors — CONFIRM.** Helpers untouched;
  package-only readers still this file alone; delete-vs-keep
  stays KANBAN-homed (principle-11 note, not a family).
- **R9 re-export posture — CONFIRM.** `as`-form intact, 0
  local definitions, root `__all__` still carries both
  cascade names + `SyncMisuseError` via `types` — 0 new
  public names.
- **Enumeration — REVISE.** 30 → 32, exactly the +2 typed
  above; import row now reads 9 boundary names. Every home
  stands; 0 additions, 0 removals, 0 renames among the 15
  def/class names.
- **Matrix axes 1/2/3/6 — CONFIRM; 4/5 — REVISE** as
  discharged above (composer shape; oracle census 59 + new
  live tier + moved projections).
- **Run-7 dispositions carried:** run-7 F5/axis-4/import
  REVISEs stand (causes composition intact) and are
  extended by this pass's combined-text revision; every
  run-7 CONFIRM/STAND is re-derived above at current HEAD
  bytes (no finding rests on run-7 bytes); errata E1
  (`5cecc2e4`) and "60→62" stay Worker-0's in-place
  corrections.

Definition-count judgment: this file gains no definition
(0 new `def`/`class`/assign among members; the import gains
a composed name, not a member). The two `combined` arms go
from 2 per-site spellings to 2 consumer compositions —
per-site wordings were never counted as definitions, so the
move is 0→0 here, mirroring run-7's authorship verdict. The
new-behavior definitions (`_combined_lost_property`,
`_pk_membership_query_or_defect`, `_COMBINED_WHAT`) live in
`utils/querysets.py`, each single-sited (probe + owner
reads).

### Defects

None. Every claim checked while tracing held at HEAD bytes:
twin wrap, both seal ends on the cascade policy, both
renderers exactly their reachable arms (keys byte-identical,
new composer clauses verified), alias pin/seed/guard,
three recourses pairwise distinct and stable, re-export
adds no public name, `fields=` ladder intact, battery
identical, classification predicates + fixtures identical,
accessor readers unchanged, oracles moved legitimately with
the behavior (2 new served-rows tests, 3 rewritten refusal
pins, 3 new live rows). The run-1 "five fields" and "62
titles" counts are artifact errata corrected in the
revisions above, not product defects. The two KANBAN-homed
notes stay homed. Nothing routed to any owner.

### Pending execution

1. `FAKESHOP_SHARDED=1 uv run pytest tests/test_permissions.py -k "multi_db or alias or pinned" --no-cov`
   — carried unchanged from the prior pass: discharges
   F2's live-second-connection consequence. Still needs
   the maintainer's separate sharded authorization; until then
   `unverified` (seed-site enumeration + lazy-state pins
   are `execution-verified` by the read-only probes).
   Postgres cells: `inapplicable by construction` (the
   run-1 W2 judgment stands — the pk-set rewrite is
   ORM-level `.filter(pk__in=...)` composition with no raw
   SQL, dialect branch, or pk-magnitude decision).

No shared-tree pytest was run (the one authorized focused
run is unused — a zero-edit file item owes no behavior
proof beyond the read-only probes, and all relied-upon
oracles already exist at HEAD). No `workspace.py` runs (no
source-mutating proof exists to route through one). No
`execution-deferred` proof beyond the sharded row.

### Item-scoped diff state and fingerprints

`git diff f3a10d3af066d9fa0f67b0bd833cb5c4ba20ae09` holds
this untracked artifact only: the item baseline's target
blob equals the worktree hash (`42c3c19c…` both), so every
hunk of target dirt predates the item; `git status --short`
count holds at 448 (no file created outside `/tmp`).
`ITEM_BASELINE=f3a10d3a…` (stash commit on `83998e08`)
resolves; HEAD unmoved throughout.

| Input | Drift base `0c0537e2` | HEAD `83998e08` | Worktree | Pre-merge `9aaaad5d` | Verdict + cause |
|---|---|---|---|---|---|
| `django_strawberry_framework/permissions.py` | `72102cc0` | `d77c5050` | `42c3c19c` | `6c97d887` | STALE, re-traced — `5c5e32c5` (12 hunks, combined rewrite) + 3 typing commits; worktree adds the content-attributed truth/cite/accumulation dirt |
| `django_strawberry_framework/utils/querysets.py` | (run-7 `3616927d`) | `392e50d0` | `cfc773ba` | `8fc556d5` | STALE — `5c5e32c5` (seal rewrite, new combined owners) + `10d2b9cd` (order owners) + typing; owner's bytes re-read for F1/F5 |
| `tests/test_permissions.py` | (run-7 `384f451b`) | `14961acd` | `7cf7b3af` | `c113d05e` | STALE — `5c5e32c5` only (2 new + 3 rewritten rows); oracle census re-derived (57→59) |
| `django_strawberry_framework/filters/sets.py` | (run-7 `993e887a`) | `3d307402` | `ec278851` | `e47c6758` | STALE — `bbe54687` + typing; F2 sibling pin re-derived intact |
| `django_strawberry_framework/optimizer/walker.py` | (run-7 `75f9c6b6`) | `bdd9c2f1` | `9130aceb` | `d5759ef8` | STALE — `5c5e32c5` (hint pk-set path) + typing; F2 sibling + WHAT-composer pins re-derived |
| `django_strawberry_framework/mutations/permissions.py` | (run-7 `54f770ae`) | `f23eb540` | `35a48499` | `55e5edf8` | STALE by hash, typing-only drift — recourse literal byte-identical (probe) |
| `django_strawberry_framework/utils/permissions.py` | (run-7 `9889d6fe`) | `e2b46fd7` | `a23d32f0` | `1c9cfd39` | STALE by hash, typing-only drift — recourse literal byte-identical (probe) |
| Searched population (package `.py` files) | 117 files | 117 files (`reject_combined` 0 hits; `_COMBINED_WHAT` 1 def + 6 code composers + 2 prose cites; accessors package-only here) | — (untracked hunt files excluded) | — | MATCH on membership; censuses re-derived |

Full SHAs: target HEAD
`d77c50503ac49a7b9dd689d2d1e4b722b5ead694`, worktree
`42c3c19cff8571a0cc4f1a511f3e41df0999ea1c`, pre-merge
`6c97d887744e2bb389e2fd957346540dacf85533`; querysets
`392e50d085c5b5a15c850a9a69b0f1b50e8529a` /
`cfc773ba8d4fa2d5f79b70d4cd0539f33b7166bd` /
`8fc556d582b313e4aed7cddaa15f9a8480d88a46`; tests
`14961acd35707e3c87628badcaea3fdd49e27562` /
`7cf7b3af6342dabb8ebf2da1dbec87abe7e5cad8` /
`c113d05eef6172f9837ed6b2d70676ff8957a4f8`;
filters/sets `3d307402a8c29860957a23bd99a821e094c606a6` /
`ec278851996aff2835677b4ca77197da2a1c2728` /
`e47c6758e540e0bd9caa8cb90103263b26e905e1`; walker
`bdd9c2f1d9518f12a4af8056e2804ee7bdc19661` /
`9130acebe13146fd35186b20e4b769f90265c08a` /
`d5759ef8533a6218942a0a2a33e64f59599a93a7`;
mutations-permissions
`f23eb540323dfad5c683ad8aa9040e0eee47676d` /
`35a484998095e2f87699f3f0df265a6e3bfa52ad` /
`55e5edf80c601f373c1802d34fc4e497919d17e7`; utils-permissions
`e2b46fd7d9712de1293c867708b1299f0e85e521` /
`a23d32f035bce1e140cd9a4600cd9355b75fdf95` /
`1c9cfd398e6096e03bda82ba93dfd66a6d2fb890`.

### Judgment

Backstop discharged at current HEAD bytes: 32/32 members
enumerated (15 def/class, all homes standing), 16
challenges re-run with counts (14 CONFIRM, C5 + C13-note
REVISED), six-axis matrix re-discharged (4 CONFIRM, 2
REVISE), every prior finding CONFIRMed or REVISEd with
fresh evidence (18 + 6). The drift touches exactly the two
cascade ends' combined handling plus typing: the seal
answers combinators by pk-set serving under the new owners,
and this file consumes both answers by name. No
consolidation owed, no defect found, no new family named.
Zero-edit result is legitimate.

Family impact: none beyond recorded convergences — F1's
pk-set consumer evidence belongs to s17
(`sealed-execution-queryset`), F5's `_COMBINED_WHAT`
consumer evidence to s18 (`seal-defect-code-wording`);
both re-traces own their rows. No other family covering
this target is touched by the drift.

### Index rows for Worker-0 (run-8)

Literal texts (Worker-0 alone edits the plan; no
back-transcription of the standing R1–R9/F8 gap is
demanded — run-7 precedent):

- Proposed member row under Family
  `seal-defect-code-wording` (open): `Combined-refusal
  shared text (_COMBINED_WHAT)` | owner
  `utils/querysets.py::_COMBINED_WHAT` | files
  `utils/querysets.py`, `permissions.py`,
  `optimizer/walker.py` | holding Family
  `seal-defect-code-wording` | 1 definition + 6 code
  composers (3 owner-file: `_validate_post_orderset_result`,
  `_visibility_result_error`, `_prepared_visibility_source`;
  2 cascade arms; `optimizer/walker.py::_hint_prefetch_over_pk_set`)
  + 2 prose cites; cascade-side consumer evidence in this
  artifact (F5).
- Convergence note for s17 (`sealed-execution-queryset`):
  cascade ends consume the pk-set rewrite
  (`_pk_membership_query_or_defect` /
  `_combined_lost_property`) through the unchanged
  two-runner + `_CASCADE_SEAL_POLICY` composition; no new
  row, F1 evidence stands for the family census.
- The `Unsealable-state cause-list wording single-source`
  adoption row keeps its permissions-side consumer
  evidence (2 arms, intact — causes census re-derived: 1
  definition + 5 code composers + 2 prose cites); no
  status change.

## Independent verification (Worker-2) — run-8 re-trace

Run: 0.0.15 2026-09-30-8. Address:
`dry/permissions-retrace-s3/verify`. HEAD `83998e08`,
verified unmoved at finish. Target HEAD blob `d77c5050`,
worktree `42c3c19c` (758 lines), drift base `0c0537e2`
(`72102cc0`), pre-merge `9aaaad5d` (`6c97d887`, read-only
via `git show`, never applied). Method: four independent
read-only probes over `git show` bytes only
(`/tmp/perm_w2_p1.py` 27 checks, `/tmp/perm_w2_p2.py` 29,
`/tmp/perm_w2_p3.py` 31, `/tmp/perm_w2_p4.py` 6 — 93/93
green), no Django import, no shared-tree pytest, no
`workspace.py` runs (no source-mutating proof exists to
route through one). W1's run-8 section was read first per
the dispatch order; every count below is re-derived with
own instruments, then reconciled row by row. Nothing
tracked edited except this section plus the `Status:`
line; no `.py` touched, so no ruff/mypy owed.

### Own drift derivation

`0c0537e2..83998e08` on the target is 4 commits,
77+/64-. `5c5e32c5`: 12 `-U0` hunks, 40+/37- (numstat +
manual `^[+-]` count agree; see erratum E-R8-1). It rewrites the cascade ends
for pk-set serving: module bullet, `_COMBINED_WHAT` as 9th
boundary-import name (same statement), both renderer
docstrings (`reject_combined` → `rewrite_combined`), both
`combined` arms recomposed to `.format(...)` composition,
`_validated_target_subquery` / `apply_cascade_permissions`
docstrings + seal comment. Typing trio: `999a1aab` 3+/3-,
`b20277fe` 33+/24- (16 hunks, all signature/import/
annotation sites), `dfbea72b` 2+/1- (mypy comment +
`redundant-expr` ignore). Typing-neutrality is proved
mechanically, not by reading: per-symbol normalized
annotation-stripped AST, `5c5e32c5` bytes → HEAD bytes,
differs in exactly `_validate_fields`, and that one only
by the list/set local split (E-R8-2) plus the ignore
comment. `reject_combined`: 0 hits in package + tests +
examples at HEAD; `_LIST_ARGUMENT_VISIBILITY_POLICY`: 0
hits. Pre-merge bytes carry the old axis
(`reject_combined` prose, `requested` spelling, 0
`_COMBINED_WHAT`) under the tree's dirt — consistent with
the merge taking main's combined rewrite.

HEAD → worktree is 38 `-U0` hunks, 42+/36-. No
`## Owned changes` row names this file, so all dirt is
external by the ledger rule; attribution by content
against `git show HEAD:` closes arithmetically: +42 = 26
`truth.` + 8 spec-034 cites + 6 `_walk` accumulation +
1 truth import + 1 `aapply` docstring line; -36 = 26
render originals + 8 `(Decision N)` originals + 1
per-edge `.filter` + 1 docstring line. Counts re-derived:
20 `truth.name`, 4 `truth.render`, 2 `truth.is_instance`,
1 import, 0 `truth.` at HEAD. Zero diff lines touch a
seal/alias/runner token (`policy=`, both runner calls,
pin/seed/guard). The `_walk` tail rewrite is worktree-only
(HEAD keeps per-edge `.filter(condition)` at line 725);
judgment stays at HEAD bytes, where R7 is re-derived.

### Own per-row judgments (24 rows)

W1 disposition → W2 judgment, each with own evidence.
AGREE = re-derived true at HEAD bytes.

- F1 sealed-execution-queryset consumer, REVISE → AGREE.
  Composition re-derived: same two runner calls (1 + 1),
  exactly 2 `policy=_CASCADE_SEAL_POLICY` passes.
  `_CASCADE_SEAL_POLICY` is
  `_SealPolicy(require_model_rows=False)` with
  `reject_sliced=True`, `rewrite_combined=True` as class
  defaults; `_SealPolicy` has 6 fields at HEAD and 6 at
  the drift base (axis swapped, not added).
  `_combined_lost_property` + `_pk_membership_query_or_defect`
  each single-sited in `utils/querysets.py`, absent from
  the target; the pk-set body carries `pk__in` +
  `.values("pk")` + `order_by()`; canon order
  `sliced → projection → combined → alias` re-derived
  from the owner doc line. C1 → 1 elsewhere.
- F2 child-queryset-alias-inheritance, CONFIRM → AGREE.
  Pin/seed/guard re-derived (1/1/present); siblings
  re-pinned (`child_base = base_queryset(child_model,
  using=parent_db)`; walker seals under
  `_LIST_RELATION_CHILD_POLICY` with `_PREFETCH_CHILD_POLICY`
  for the nested-connection path). C2 → 1.
- F3 one-sync-boundary, CONFIRM → AGREE. One `_walk`,
  one `await`, `aapply` wraps `apply` in
  `run_in_one_sync_boundary`. C3 → 1.
- F4 queryset-seed-and-model-read, CONFIRM → AGREE.
  `model_for(cls)` ×1, `base_queryset(..., using=...)`
  ×1; the relay raw-manager read survives at HEAD. C4 → 2
  elsewhere.
- F5 seal-defect-code-wording consumer, REVISE → AGREE.
  Arm keys re-derived byte-identical from the AST: root 5
  `{type, table, untrusted, sliced, combined}`, edge 6
  (those + `alias`), no `projection`/`routing`/`evaluated`.
  `_COMBINED_WHAT` census re-derived: 1 definition
  (querysets line 3973) + 6 code composers (3 owner-file
  inside `_validate_post_orderset_result`,
  `_visibility_result_error`, `_prepared_visibility_source`
  — enclosing defs verified — plus the 2 cascade arms
  plus `optimizer/walker.py::_hint_prefetch_over_pk_set`,
  enclosing def verified) + 2 prose cites (owner comment +
  cascade docstring). `_UNSEALABLE_STATE_CAUSES` census
  re-derived intact: 1 + 5 code + 2 prose; 4 refs here
  (import + 2 arms + docstring), same shape as the 4
  `_COMBINED_WHAT` refs here. C5 → 1 definition + arms.
- F6 recourse rejection, CONFIRM → AGREE. All three
  literals byte-identical base → HEAD, pairwise distinct
  (lengths 249/236/165, matching W1's triple); four
  differing clauses + trigger stand. C6 → 1 here.
- F7 checked-not-member, CONFIRM → AGREE. Zero
  `reject_async*` / `_dispose*` / `awaitable` tokens at
  HEAD; refusal rides the runner. C7 → 0 here.
- F8 vocabulary rejection, CONFIRM → AGREE. Target
  carries 0 `has_permission` / `check_permission` tokens;
  both durable-home sentences present at HEAD (1 hit
  each). C15 → 0 refused.
- R1 cascadable-edge classification, CONFIRM → AGREE.
  Predicate normalized-identical base → HEAD; fixtures
  identical (`products/models.py`: 0 drift commits;
  `library/models.py`: +35/0 additive, one plain
  single-column FK, no new edge kind). C8 → 1.
- R2 unsupported-edge preflight, CONFIRM → AGREE.
  Predicate + preflight + dedicated `fields=` error
  normalized-identical. C9 → 1.
- R3 `fields=` grammar, CONFIRM → AGREE. All branches
  identical modulo the list/set split + ignore comment;
  no `model._meta` in the validator. C10 → 1.
- R4 traversal state, CONFIRM → AGREE. Both records
  normalized-identical; both install/reset sites inside
  code-identical functions. C11 → 1.
- R5 cycle policy + `fields=[]` escape, CONFIRM → AGREE.
  `_cycle_error` identical; branch inside code-identical
  `apply_cascade_permissions`. C12 → 1.
- R6 re-projection battery, REVISE (prose only) → AGREE
  on the verdict, with erratum E-R8-3 on one clause. Body
  normalized-identical (three checks + `.values(attname)`
  tail); docstring combined paragraph reworded to pk-set
  serving with refusal for unrepresentable shapes. E-R8-3:
  the paragraph cites the seal/policy/axis by contract —
  the target never names `_pk_membership_query_or_defect`
  (0 hits target-wide) — so "citing
  `_pk_membership_query_or_defect`" overstates; the
  verdict itself (prose-only revision) is unaffected.
  C13 → 1 per layer as recorded.
- R7 per-edge composition, CONFIRM at HEAD → AGREE.
  `_walk` normalized-identical base → HEAD (registry
  skip, `using=` seed, `Q(__in)` + nullable-only
  `__isnull`, depth-1, per-edge `.filter(condition)`);
  the single-filter accumulation exists only in worktree
  bytes. C14 → 1.
- R8 vestigial accessors, CONFIRM → AGREE. Helpers
  identical; package-wide readers still this file alone;
  non-package hits are `tests/test_permissions.py` + the
  binary DB, as recorded. C16 → 0 break.
- R9 re-export posture, CONFIRM → AGREE. `as`-form
  intact, 0 local definitions, root `__all__` carries
  both cascade names + `SyncMisuseError`. 0 new names.
- Enumeration, REVISE → AGREE. 32 members re-derived
  (`Expr` 1, `ImportFrom` 12, `Import` 1, `If` 1 guard,
  `Assign` 1, `ClassDef` 2, `AnnAssign` 1, `FunctionDef`
  12, `AsyncFunctionDef` 1); 15 def/class names in the
  identical order, 0 added/removed/renamed; delta vs
  run-7's 30 is exactly the `collections.abc` import +
  the `TYPE_CHECKING` guard; boundary import carries 9
  names. Every home stands.
- Matrix axis 1, CONFIRM → AGREE (three vocabularies
  behaviorally separated; literals + homes re-derived).
- Matrix axis 2, CONFIRM → AGREE (twin shape re-derived).
- Matrix axis 3, CONFIRM → AGREE (classification
  cache, attname read, alias threading, single policy
  const ×2 passes all re-derived; validator composes
  `_edge_plan`).
- Matrix axis 4, REVISE → AGREE (arm sets re-derived
  identical; `combined` arms compose the shared text by
  name; `None`/`[]` pair untouched; causes composition
  intact at 4 refs).
- Matrix axis 5, REVISE → AGREE. Oracle census
  re-derived with the run-1 instrument: 59 at HEAD vs 57
  at the drift base, exactly +2 (both served-rows tests
  named by W1), 0 dropped; the three rewritten refusal
  pins verified (`_hook_union_all`,
  `_hook_intersection_values`, `_root_combined_all`,
  verbose lost-property wording); live
  `test_combined_visibility_api.py` carries exactly 3
  cascade rows (target, root, outer-values refusal) of
  28; GLOSSARY `apply_cascade_permissions` bullet +
  `Sealed execution queryset` term both carry the
  serving/refusal prose (base carries the refusal-only
  prose); oracle independence holds — 0 owner-name reads
  in `tests/test_permissions.py` and in the live file at
  HEAD (the `_COMBINED_WHAT` imports in
  `tests/utils/test_querysets.py` +
  `tests/optimizer/test_walker.py` belong to the owner's
  own suites, for s17/s18, not this item).
- Matrix axis 6, CONFIRM → AGREE (predicates identical +
  fixtures identical ⇒ recorded edge sets hold; alias
  member + siblings re-derived).
- Run-7 carried dispositions → AGREE. The F5/axis-4/
  import REVISEs stand (causes composition intact) and
  are extended, not superseded; no finding rests on
  run-7 bytes; errata E1 + "60→62" stay Worker-0's
  in-place corrections.

Definition-count judgment: AGREE. This file gains no
definition (0 new `def`/`class`/assign; the import gains
a composed name, not a member). The two `combined` arms
go from 2 per-site spellings to 2 consumer compositions
— per-site wordings were never counted as definitions,
so 0→0 here. The new-behavior definitions live singly
in `utils/querysets.py`.

### Proposed member row: ENDORSED

The `Combined-refusal shared text (_COMBINED_WHAT)` row
under Family `seal-defect-code-wording` is endorsed as
written: owner, three-file membership, holding family,
and the 1 + 6 + 2 census all re-derived independently
above (composer enclosing functions verified by def
line). The s17 convergence note is likewise endorsed
(two-runner + policy composition unchanged). This
verification edits no index; s18 owns the row.

### Fingerprints (all re-hashed, digit-for-digit)

Target `72102cc0` → `d77c5050` → worktree `42c3c19c` →
pre-merge `6c97d887`; querysets HEAD `392e50d0`,
worktree `cfc773ba`, pre-merge `8fc556d5`; tests HEAD
`14961acd`, worktree `7cf7b3af`, pre-merge `c113d05e`
(drift is `5c5e32c5` only, re-derived); filters/sets
`3d307402` / `ec278851` / `e47c6758`; walker `bdd9c2f1`
/ `9130aceb` / `d5759ef8`; mutations-permissions
`f23eb540` / `35a48499` / `55e5edf8` (typing-only drift,
literal byte-identical); utils-permissions `e2b46fd7` /
`a23d32f0` / `1c9cfd39` (same). Population: 117 package
files, membership re-derived; `reject_combined` 0 hits.
Every W1 pin matches to 8 hex; full SHAs verified for
the target row.

### Pending execution + prose checks

Item-scoped diff re-measured empty: `git diff
f3a10d3af066d9fa0f67b0bd833cb5c4ba20ae09 --
django_strawberry_framework/permissions.py` is 0 bytes;
`git status --short` count holds at 448. The sharded F2
row is carried unchanged (still needs the maintainer's separate
authorization; `unverified` until then). Postgres cells:
`inapplicable by construction`, concurred on own reading
— the pk-set rewrite is ORM-level `.filter(pk__in=...)`
composition with no raw SQL, dialect branch, or
pk-magnitude decision. The run-8 record therefore reads
`verified, pending execution` on the sharded row only.
AGENTS.md prose: `path::Symbol` citations throughout, no
new reference-style links (LINK DEFINITIONS block still
sufficient), no process provenance, no tests owed or
added, zero `.py` paths touched.

### Defects (this pass)

None. Every claim checked while tracing held at HEAD
bytes. The two KANBAN-homed notes stay homed.

### Errata for in-place correction (no resubmission)

Record precision only — no verdict, index, or decision
moves (run-8 s1 precedent). E-R8-1: `5c5e32c5` on the
target is 40+/37- (numstat + manual count agree), not
39+/36-. E-R8-2: the validator change is a list/set
local split (`entries` list + `requested` set both
present at HEAD), not a full rename — `requested`
survives. E-R8-3: the R6 docstring cites the seal,
policy, and axis by contract; it never names
`_pk_membership_query_or_defect` (0 target-wide hits).

### Verdict

`Status: verified` — all 24 rows survive on independent
evidence (18 CONFIRM + 6 REVISE re-derived with own
counts), enumeration 32/32 member-by-member, censuses
re-derived (WHAT 1+6+2, causes 1+5+2), 8/8 fingerprints
digit-for-digit, proposed member row endorsed, no
defects, zero edits.
