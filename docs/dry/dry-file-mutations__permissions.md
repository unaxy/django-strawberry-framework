# DRY review: `mutations/permissions.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

The target owns the write side's authorization vocabulary: the shared
sync-bool auth-result contract
[mutations-permissions][mutations-permissions]`::_require_sync_bool_auth_result`,
the single permission-class walk
[mutations-permissions][mutations-permissions]`::run_permission_classes`, the default
model-permission check
[mutations-permissions][mutations-permissions]`::DjangoModelPermission`, and the
model-less closed default [mutations-permissions][mutations-permissions]`::DenyAll`.

Connected behavior examined, upstream and downstream. The resolver gate
[mutations-resolvers][mutations-resolvers]`::authorize_or_raise` composes the result
contract by name and maps denial to the top-level `GraphQLError`; both
`check_permission` seams
([mutations-sets][mutations-sets]`::DjangoMutation.check_permission` and
[forms-sets][forms-sets]`::DjangoFormMutation.check_permission`, the latter not a
subclass of the former) delegate to the single walk body, and the serializer
flavor inherits the model's seam. Class-creation validation
[mutations-sets][mutations-sets]`::_validate_permission_classes` wires the
`DjangoModelPermission` / `DenyAll` defaults and the immutability the walk relies
on (`_ValidatedMutationMeta` seal). The operation-to-action map
[operations][operations]`::_OPERATION_PERMISSION_ACTION` is read, never respelled.
Request resolution rides [utils-permissions][utils-permissions]`::request_from_info`;
async discipline rides
[querysets][querysets]`::reject_async_in_sync_context`. The auth holder binds
`DjangoMutation.check_permission` directly rather than minting a fourth seam.
Oracles: [test-permissions][test-permissions] (class behavior, enforcement,
snapshot-immutability rows) plus live-tier DenyAll-denies and denial-surface
rows. Projections: the module docstring, the
[GLOSSARY `DjangoModelPermission` anchor][glossary], the
[consumer write-auth section][docs-readme], spec-036 Decision 15 / spec-038
Decision 11.

## Verification

### Matrix

Each axis searched or ruled inapplicable, against the target's real surface.

1. **Cross-flavor policy mirroring.** Compared by behavior and contract, not
   shape: write authorization returns a `bool` deny-by-default per operation;
   the cascade narrows a queryset per edge (composable); the filter / order
   gates fire per supplied input field with per-class dedup. Three contracts,
   three reasons to change; unification re-derived and rejected in F2. The
   serializer flavor inherits the model seam; the plain form carries its own
   seam delegating to the same walk body (F4).
2. **Sync/async twins.** The target is sync-only: zero `AsyncFunctionDef`,
   zero `await` (probe). No async twin exists here; the async write surface
   wraps the sync pipeline in the single boundary owned elsewhere. The four
   recourse sentences (write, gate, pipeline template, relay) are pairwise
   distinct literals; the write-vs-gate pair is re-derived clause by clause
   and rejected in F1.
3. **Derived rather than repeated knowledge.** The operation-to-action map is
   derived from [operations][operations]`::_OPERATION_PERMISSION_ACTION` by
   lookup (`_OPERATION_PERMISSION_ACTION[operation]`); no `add` / `change` /
   `delete` literal lives here (probe). The request comes from
   [utils-permissions][utils-permissions]`::request_from_info`; the model
   from the `mutation._resolve_model` seam. No second derivation of any of
   the three.
4. **Inverse / round-trip pairs.** No surface: no encode/decode, pack/unpack,
   or build/parse grammar here. The `DenyAll` default vs `[]` opt-out is a
   policy pair (closed default vs explicit open), not a codec with two
   halves.
5. **Contracts restated in another medium.** Oracles are
   [test-permissions][test-permissions] class-behavior rows (real users,
   real perms, `True` / `False` verdicts — independent), the
   snapshot-mutation bypass-attempt and non-bool / async rejection rows
   (behavioral), and live-tier DenyAll-denies plus denial-surface rows
   (independent). The snapshot-identity pins (`permission_classes ==
   (DjangoModelPermission,)`) honestly grade as owner-reading: they pin the
   default tuple, not the walk. Projections (module docstring,
   [GLOSSARY][glossary], [consumer docs][docs-readme], spec decisions)
   describe; none is read by an oracle. No oracle rewritten to read its
   expectation from the owner it checks.
6. **Enforcement by omission.** Every write-auth seam enumerated: model
   `check_permission`, plain-form `check_permission`, serializer (inherits
   model's), auth holder (binds the base method), the single resolver gate.
   All ride the one walk; no flavor lacks it. `user is None` denies;
   anonymous denies via `has_perm` returning `False`. No omission gap, so
   no defect.

### Enumeration

Instrument: `ast.parse` over `ast.Module.body`. Count: **12**. Every member
lands below; no member unassigned.

| # | Member | Kind | Home |
|---|---|---|---|
| 1 | module docstring | `Expr` | projection (F1 + F2 durable homes) |
| 2 | `from __future__ import annotations` | `ImportFrom` | import (no rule) |
| 3 | `from typing import Any` | `ImportFrom` | import (no rule) |
| 4 | `from ..exceptions import ...` | `ImportFrom` | consumer (`ConfigurationError`, `_safe_arg_repr`) |
| 5 | `from ..utils.permissions import request_from_info` | `ImportFrom` | consumer (F5-adjacent; single-sited user resolution) |
| 6 | `from ..utils.querysets import reject_async_in_sync_context` | `ImportFrom` | consumer (F3; single async-guard site) |
| 7 | `from .operations import _OPERATION_PERMISSION_ACTION` | `ImportFrom` | consumer (F5; operation descriptors) |
| 8 | `_PERMISSION_ASYNC_RECOURSE` | `Assign` | F1 (rejected) |
| 9 | `_require_sync_bool_auth_result` | `FunctionDef` | F3 (file-local) |
| 10 | `run_permission_classes` | `FunctionDef` | F4 (file-local) |
| 11 | `DjangoModelPermission` | `ClassDef` | F5 (consumer) + file-local default check |
| 12 | `DenyAll` | `ClassDef` | F6 (file-local) |

Candidates checked, not inherited: `sync-boundary-recourse-wording`
(rejected — F1 re-derives the 4-clause difference fresh),
`unified-permission-hook-vocabulary` (rejected — F2 re-derives; the
owner-docstring home lives HERE),
`mutation-operation-descriptors` (consumer — member 11 reads the table),
`awaitable-refusal-and-disposal` (checked, not a member — refusal rides the
imported guard; no dispose body here),
`one-sync-boundary` (checked, no surface — no boundary call lives here; the
target runs inside the pipeline's boundary).

### Challenges

Counts are authoritative definitions only; consumers, oracles, projections
listed, never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | recourse sentence | the sentence must name the settings key that relaxes it | template refused — write sentence here + gate sentence in [utils-permissions][utils-permissions] stay separate (4 clauses differ) | rejected; F1 |
| C2 | hook vocabulary | visibility and authorization collapse into one hook | **0** move — refused (three contracts, three reasons to change) | rejected; F2 |
| C3 | auth-result contract | a fourth seam (new flavor override) must also reject truthy non-bools | **1** (`_require_sync_bool_auth_result`) | file-local; F3 |
| C4 | operation-to-action map | a new operation gains a model perm (or an action is renamed) | **0** here (table moves in [operations][operations]; this file follows by lookup) | consumer; F5 |
| C5 | permission-class walk | a new flavor needs the AND-over-snapshot walk | **1** (`run_permission_classes`; new seam delegates) | file-local; F4 |
| C6 | model-less default | the closed default gains an allow case | **1** (`DenyAll.has_permission`) | file-local; F6 |
| C7 | request resolution | a new context shape must resolve | **0** here (`request_from_info` moves; four call shapes follow) | consumer |
| C8 | bool strictness | truthy non-bools must be allowed | **1** (the `isinstance` arm in F3) | file-local; F3 |

**Experiments.** Two read-only probes (no source mutation, no SQL
evaluation, no shared-tree pytest):

```shell
uv run python docs/dry/temp-tests/dry-file-mutations__permissions/probe_w1.py
```

Output (`ALL OK`, 27 checks): 12-member AST with exact kinds, import
modules, function and class names; zero `AsyncFunctionDef`, zero `await`;
docstring carries the separation clause and the `request_from_info`
composition claim; the result contract calls the imported guard with the
shared recourse and raises `ConfigurationError` on non-bool; the walk
iterates `tuple(meta.permission_classes)` with first-denial short-circuit;
the model check reads the operations table with no inline action literal
and denies a `None` user; `DenyAll.has_permission` returns `False` and its
body reads no model and no request. Status: `execution-verified`.
Rejects "a second walk exists", "an async seam lives here", "the action
map is respelled", "the closed default inspects state".

```shell
uv run python docs/dry/temp-tests/dry-file-mutations__permissions/probe_w2.py
```

Output (`ALL OK`, 41 checks): write-vs-gate 4-clause difference proved
from runtime literals (write owns hook naming + bool clause +
`has_perm`/backend clause; gate owns gate naming + subject clause; one
shared clause; sentences unequal); `True` / `False` pass, six non-bool
shapes raise `ConfigurationError`, a coroutine is closed and raised as
`SyncMisuseError` carrying the recourse; `DenyAll` denies five operations;
stub-permission walk denies on first `False` with short-circuit calls
`["A", "B"]` and allows with calls `["X", "Y"]`; the operations table
equals exactly the three verb mappings; both flavor seams delegate to the
one walk body (exactly two identical delegating returns) while the
serializer flavor adds none. Status: `execution-verified`. Rejects "one
recourse covers both", "truthiness is coerced", "an async denial passes",
"the seams fork".

## Findings

No production edit is owed by a file item; each finding names the family
that will own it. No new family is named: the walk, the result contract,
the model check, and the closed default are each sole-owned here and stay
file-local; every cross-file rule reuses an indexed family or records a
rejection at its owner.

### F1 — sync-boundary recourse wording (existing family `sync-boundary-recourse-wording`, rejected)

- **Contract + variation.** The sentence appended to a `SyncMisuseError`
  when a permission hook returns an awaitable in the sync write pipeline.
  Re-derived fresh from the runtime literals (probe), not inherited: the
  write sentence names `has_permission / check_permission`, requires
  `returning a bool`, and names `user.has_perm / auth backends`; the gate
  sentence names `check_<field>_permission` and the `FilterSet / OrderSet`
  subject. Four clauses differ; the single shared clause is
  "synchronously, so it cannot await". A template would take a parameter
  per clause and pin nothing.
- **Sites + roles.** *Definitions staying separate:* this target's
  `_PERMISSION_ASYNC_RECOURSE` and
  [utils-permissions][utils-permissions]`::_GATE_ASYNC_RECOURSE`.
  *Declining owner:* [querysets][querysets]`::sync_pipeline_recourse`
  (docstring declines both, for the same reason). *Consumers:* the result
  contract passes this target's sentence at all three seams.
- **Challenges.** C1 → template refused. No second site defines either
  sentence.
- **Owner + lifetime.** Each surface keeps its own sentence; no stored
  derivation. Durable homes: the declining docstring at
  [querysets][querysets]`::sync_pipeline_recourse`, the four-clause comment
  above `_PERMISSION_ASYNC_RECOURSE`, the twin comment above
  `_GATE_ASYNC_RECOURSE`. Not written here (file item lands no edit).
- **Migration.** None (rejection).
- **Distinct behavior.** The `bool` and `has_perm` clauses have no gate
  analogue; the gate subject has no write analogue.
- **Behavioral proof.** `execution-verified` via `probe_w2.py` (clause
  presence/absence per literal + inequality). Rejects "one recourse covers
  both".
- **Structural gate.** Owned by the family item.
- **Freshness.** Target `54f770ae…`, [utils-permissions][utils-permissions]
  `9889d6fe…`, [querysets][querysets] `1539b66c…` (`git hash-object`,
  worktree at run time).
- **Reconsideration trigger.** Either sentence reworded so the two differ
  only in the subject noun — the shape the pipeline template already
  solves for the three write flavors.

### F2 — unified permission hook vocabulary (existing family `unified-permission-hook-vocabulary`, rejected)

- **Contract + variation.** Whether the cascade visibility hook
  (`get_queryset`), the write authorization hooks (`has_permission` /
  `check_permission`), and the per-field gates (`check_<field>_permission`)
  are one rule. Re-derived fresh from behavior + contract: the cascade
  composes a row-narrowing queryset; the write hooks return a
  deny-by-default `bool` per operation; the gates fire per supplied input
  field with per-class dedup. Three contracts, three reasons to change;
  merging adds validator rejection to an equality test or drops the
  fail-closed raise. Cascade-first-then-gates ordering is load-bearing
  against existence leaks.
- **Sites + roles.** *This target:* the write vocabulary (definition of
  the write half; the module docstring states the separation from row
  visibility). *Neighbors:* [permissions-cascade][permissions-cascade]
  (queryset-narrowing), [utils-permissions][utils-permissions] (per-field
  gates). *Oracles:* cascade-then-gate ordering rows.
- **Challenges.** C2 → 0 moves.
- **Owner + lifetime.** No owner (rejection). Durable homes: this target's
  module docstring (separation clause) and the
  [utils-permissions][utils-permissions] module docstring (mechanics-only
  clause). Not written here.
- **Behavioral proof.** `static-reviewed` (contract comparison against the
  three bodies) + `execution-verified` write-half behavior via `probe_w2.py`
  (bool strictness, short-circuit, closed default). Rejects "one hook
  covers all three".
- **Freshness.** Target `54f770ae…`, [permissions-cascade][permissions-cascade]
  `757dce34…`, [utils-permissions][utils-permissions] `9889d6fe…`.
- **Reconsideration trigger.** One hook returning a queryset plus a
  verdict — a site that is genuinely both rules at once.

### F3 — write-auth sync-bool result contract (file-local)

- **Contract + variation.** The ONE write-authorization result rule the
  three sync seams share (`has_permission` entries, `check_permission`
  overrides, `user.has_perm`): each must return an actual `bool`; a truthy
  coroutine is closed and raised as `SyncMisuseError`, any other non-bool
  raises `ConfigurationError`. Never coerced from truthiness (an
  authorization bypass otherwise).
- **Sites + roles.** *Definition:*
  [mutations-permissions][mutations-permissions]`::_require_sync_bool_auth_result`.
  *Consumers:* the walk body (per-entry), the model check (`has_perm`),
  [mutations-resolvers][mutations-resolvers]`::authorize_or_raise`
  (`check_permission`). No second definition anywhere in the package
  (package-wide grep: one `def`, three call sites across two files).
- **Challenges.** C3 + C8 → 1.
- **Behavioral proof.** `execution-verified` via `probe_w2.py` (bools pass,
  six non-bool shapes raise, coroutine closed + raised with recourse
  attached). Rejects "truthiness is coerced", "an async denial passes".
- **Structural gate.** Owned by the family item; contributing oracles are
  the non-bool / async rejection rows in [test-permissions][test-permissions].
- **Freshness.** Target `54f770ae…`,
  [mutations-resolvers][mutations-resolvers] `3fd1e571…`,
  [querysets][querysets] `1539b66c…`.

### F4 — single permission-class walk body (file-local)

- **Contract + variation.** The AND-over-snapshot walk: iterate
  `tuple(meta.permission_classes)` (snapshot captured before the walk, so a
  hook holding the mutation class cannot empty the live set into an
  allow-any posture), deny on first `False`, allow only when all allow.
  Each entry's result runs through F3.
- **Sites + roles.** *Definition:*
  [mutations-permissions][mutations-permissions]`::run_permission_classes`.
  *Seams composing it by name:* `DjangoMutation.check_permission`,
  `DjangoFormMutation.check_permission` (exactly two identical delegating
  returns, probe-verified); the serializer flavor inherits the model's;
  the auth holder binds the base method. *Storage guarantor:*
  [mutations-sets][mutations-sets]`::_ValidatedMutationMeta` (sealed tuple).
- **Challenges.** C5 → 1.
- **Behavioral proof.** `execution-verified` via `probe_w2.py`
  (short-circuit call list, all-allow call list). Rejects "the seams fork".
- **Structural gate.** Owned by the family item; contributing oracles are
  the short-circuit + snapshot-mutation bypass-attempt rows in
  [test-permissions][test-permissions].
- **Freshness.** Target `54f770ae…`, [mutations-sets][mutations-sets]
  `cffa29e5…`, [forms-sets][forms-sets] (read at run time; not fingerprinted
  — consumer text only).

### F5 — operation-to-permission-action mapping (existing family `mutation-operation-descriptors`, consumer)

- **Contract + variation.** `create -> add`, `update -> change`,
  `delete -> delete`. Owned by [operations][operations]; this target is a
  consumer: `DjangoModelPermission.has_permission` looks up
  `_OPERATION_PERMISSION_ACTION[operation]` and builds
  `<app_label>.<action>_<model_name>` for `user.has_perm`.
- **Challenges.** C4 → 0 here (the table moves; this file follows by
  lookup — probe asserts no inline action literal).
- **Behavioral proof.** `execution-verified` via `probe_w2.py` (table
  equals exactly the three mappings) + `static-reviewed` delegation.
  Rejects "the mapping is respelled here".
- **Freshness.** Target `54f770ae…`, [operations][operations] `16223c6b…`.

### F6 — model-less deny-by-default (file-local)

- **Contract + variation.** A plain `DjangoFormMutation` has no model, so
  the model-permission default cannot apply (it would raise at request
  time, not deny). An unset `Meta.permission_classes` on the plain form
  installs `DenyAll`, which denies every request while inspecting no model
  metadata; the explicit `[]` opt-in stays the public-write posture.
- **Sites + roles.** *Definition:*
  [mutations-permissions][mutations-permissions]`::DenyAll`
  (`has_permission` returns `False`; body reads no model, no request —
  probe-verified on the method body, whose docstring mention of the model
  seam is prose, not a read). *Wiring:*
  [mutations-sets][mutations-sets]`::_validate_permission_classes`
  (`unset_default=(DenyAll,)` for the plain form + the
  model-permission-on-model-less reject at class creation).
- **Challenges.** C6 → 1.
- **Behavioral proof.** `execution-verified` via `probe_w2.py` (denies five
  operations) + live-tier DenyAll-denies rows. Rejects "a model-less write
  ships open".
- **Freshness.** Target `54f770ae…`, [mutations-sets][mutations-sets]
  `cffa29e5…`.

## Defects

None. Every claim checked while tracing held (four recourse clauses differ
as the comment states; the separation clause matches the three bodies; the
snapshot iteration, short-circuit, `None`-user denial, and closed default
match their prose; no flavor lacks the walk).

No further defects (Worker 2) - see `## Independent verification (Worker 2)`.

## Judgment

Zero-edit result legitimate: the six-axis matrix discharged against the
target's real surface, challenges recorded with counts (C1 refused, C2
refused, C3/C5/C6/C8 → 1 here, C4/C7 → 0 here as consumer), both
rejections carry their contract differences + triggers with durable homes
at the owners, and the backstop assigns 12/12 members with no second site
left homeless. No consolidation inside a file item by construction; the
two candidate unifications stay rejected, the three shared mechanisms stay
composed by name.

## Implementation (Worker 1)

Zero production edits (target CLEAN: `git diff <ITEM_BASELINE> --
django_strawberry_framework/mutations/permissions.py` empty; worktree blob
`54f770ae…`). No tracked files added; no `ruff` owed (no tracked `.py`
touched). Item-scoped diff: empty. Two read-only probes created as
untracked scratch under
`docs/dry/temp-tests/dry-file-mutations__permissions/` (`probe_w1.py` 27
checks, `probe_w2.py` 41 checks; both `ALL OK` at run time) and left on
disk for Worker 2. Concurrent dirt (worktree `connection.py`,
`extensions/resource_policy.py`, `filters/sets.py`, `forms/inputs.py`,
`mutations/fields.py` hunks, `filters/inputs.py` hunk, `tests/`
companions, staged `tests/utils/test_querysets.py`, `docs/bug_hunt/`,
`docs/dry/dry-0_0_15.md`, the utils/querysets collision) untouched per the
brief; none is fingerprinted here except paths read at HEAD bytes, and no
finding depends on a concurrently-dirty hunk. No shared-tree pytest run
(not authorized). Sharded / Postgres cells: `inapplicable by construction`
(the target's exercised paths reach no database, alias, or dialect
decision — pure `bool` / tuple / string composition; stated, Worker 2 to
judge).

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. HEAD `9031cb3d`. Dispatch ITEM_BASELINE
`f84dc5c980b938a8fdcb8cf0b2903bf0acb0d752`. This section was recorded
own-trace-first: the target, the item-scoped diff, `git status --short`,
consumers and tests (cascade plus gate flavors first), and both probes were
read before `## Findings` was opened. No worker-memory was read.

### Own trace

Sites re-derived from the target plus its real surface:
`django_strawberry_framework/permissions.py::apply_cascade_permissions`
(queryset narrowing per edge), `django_strawberry_framework/utils/permissions.py`
(per-field gates plus `request_from_info` plus the gate recourse),
`django_strawberry_framework/mutations/resolvers.py::authorize_or_raise`
(denial-to-GraphQLError gate), `django_strawberry_framework/mutations/sets.py`
(`_validate_permission_classes`, `_ValidatedMutationMeta`,
`DjangoMutation.check_permission`), `django_strawberry_framework/forms/sets.py`
(plain-form `check_permission`), `django_strawberry_framework/rest_framework/sets.py`
(serializer flavor: validation wiring only, no auth seam),
`django_strawberry_framework/auth/mutations.py` (binds
`DjangoMutation.check_permission` directly), `django_strawberry_framework/mutations/operations.py`
(operation table), `tests/mutations/test_permissions.py` (oracles).

Rules, posited changes, definition counts, and the owners I would choose:

- R1 write recourse sentence. Change: the sentence must name a settings key
  that relaxes it. Count: template refused - the write sentence owns hook
  naming plus the bool clause plus the `has_perm`/backend clause, the gate
  sentence owns gate naming plus the FilterSet/OrderSet subject, one shared
  clause. Owner: each surface keeps its own sentence.
- R2 hook vocabulary. Change: visibility and authorization collapse into one
  hook. Count: 0 move - write returns a deny-by-default bool per operation,
  the cascade narrows a queryset per edge, the gates fire per supplied input
  field with per-class dedup. Owner: none (rejection).
- R3 sync-bool result contract. Change: a fourth seam must also reject truthy
  non-bools. Count: 1
  (`mutations/permissions.py::_require_sync_bool_auth_result`; three call
  sites across two files: the walk per entry, the model check on
  `user.has_perm`, the resolver on `check_permission`). Owner: here.
- R4 permission-class walk. Change: a new flavor needs the AND-over-snapshot
  walk. Count: 1 (`run_permission_classes`; a new seam delegates). Owner: here.
- R5 operation-to-action map. Change: a new operation gains a model perm.
  Count: 0 here (the table moves in `mutations/operations.py`; this file
  follows by lookup). Owner: `mutations/operations.py`; this file is a consumer.
- R6 model-less closed default. Change: the closed default gains an allow
  case. Count: 1 (`DenyAll.has_permission`; wiring in
  `mutations/sets.py::_validate_permission_classes` via
  `unset_default=(DenyAll,)`). Owner: here.
- R7 request resolution. Change: a new context shape must resolve. Count: 0
  here (`request_from_info` moves). Owner:
  `django_strawberry_framework/utils/permissions.py::request_from_info`;
  this file is a consumer.

Reconciliation vs W1: full agreement on all six findings (F1 = R1 rejected,
F2 = R2 rejected, F3 = R3 file-local, F4 = R4 file-local, F5 = R5 consumer,
F6 = R6 file-local). The remaining differences are record-level only and are
ruled below; none touches the verdict.

### Baseline-hash ruling

I re-ran `git diff f84dc5c980b938a8fdcb8cf0b2903bf0acb0d752 --
django_strawberry_framework/mutations/permissions.py` myself: empty, exit 0.
Worktree blob `54f770ae` equals the HEAD blob, the target is absent from
`git status --short`, and `git diff HEAD -- <target>` is empty. Ruling: the
dispatch baseline and W1's self-taken stash are equivalent snapshots of HEAD
`9031cb3d` for this path, as the dispatch note predicts. The pattern is
explained and immaterial here - the item-scoped diff is empty under either
baseline, so the zero-edit claim does not depend on which snapshot is used.

### Enumeration check (member by member; own count 12, 0 async)

Own instrument: `ast.parse` over `ast.Module.body` (re-ran independently).
Count 12, 0 `AsyncFunctionDef`, 0 `Await` - matches W1 exactly.

| # | Member | Kind | Agreement |
|---|---|---|---|
| 1 | module docstring | `Expr` | agree - projection (F1 + F2 homes) |
| 2 | `from __future__ import annotations` | `ImportFrom` | agree - no rule |
| 3 | `from typing import Any` | `ImportFrom` | agree - no rule |
| 4 | `from ..exceptions import ...` | `ImportFrom` | agree - consumer |
| 5 | `from ..utils.permissions import request_from_info` | `ImportFrom` | agree - consumer (R7) |
| 6 | `from ..utils.querysets import reject_async_in_sync_context` | `ImportFrom` | agree - consumer (R3 guard) |
| 7 | `from .operations import _OPERATION_PERMISSION_ACTION` | `ImportFrom` | agree - consumer (R5) |
| 8 | `_PERMISSION_ASYNC_RECOURSE` | `Assign` | agree - F1 rejected |
| 9 | `_require_sync_bool_auth_result` | `FunctionDef` | agree - F3 file-local |
| 10 | `run_permission_classes` | `FunctionDef` | agree - F4 file-local |
| 11 | `DjangoModelPermission` | `ClassDef` | agree - F5 consumer plus file-local default check |
| 12 | `DenyAll` | `ClassDef` | agree - F6 file-local |

Kind order and import-module order verified identical to W1's table. No
member unassigned; no thirteenth member.

### Fingerprint re-hashes (`git hash-object`, worktree)

- Target `54f770ae`: match (also equals `HEAD:<path>`).
- `utils/permissions.py` `9889d6fe`: match.
- `permissions.py` (cascade) `757dce34`: match.
- `utils/querysets.py` `1539b66c`: match.
- `mutations/operations.py` `16223c6b`: match.
- `mutations/resolvers.py` `3fd1e571`: match.
- `mutations/sets.py` cited `cffa29e5`: equals the HEAD blob (W1's
  worktree-at-run-time reading, correct when taken). The worktree now hashes
  `936f5ae7`. Cause verified via `git diff HEAD -- <path>`: a concurrent
  wording-only hunk renaming `cls.__name__` / `mutation_cls.__name__` to a
  safe class-name helper in seal messages and type-naming sites (seal
  rebinding/deletion messages, `_validate_meta`, input materialization, the
  delete-operation message, payload binding). It does not touch
  `_validate_permission_classes` defaults, `_ValidatedMutationMeta` seal
  semantics, or either `return run_permission_classes(...)` delegation, whose
  lines I confirmed unchanged. F4/F6 are robust to it; Worker 0 should rebind
  this fingerprint at closeout rather than treating W1's reading as stale
  evidence against the findings.
- `forms/sets.py`: W1 did not fingerprint it (disclosed as consumer text
  only). Supply: `36ce80b4` (clean tree - absent from `git status`). I
  verified both delegating seams in the current tree
  (`forms/sets.py::DjangoFormMutation.check_permission` and
  `mutations/sets.py::DjangoMutation.check_permission` each return the one
  walk body; the serializer flavor defines no seam). Worker 0 should bind
  this hash in `## Outcomes`.
- `rest_framework/sets.py` `2c7117d6` and `tests/mutations/test_permissions.py`
  `9cef2100` recorded as searched population (verified content, not
  freshness-bound by W1; no finding depends on their bytes).

### Challenges, roles, oracles

Counts agree: C1 refused, C2 zero moves, C3/C5/C6/C8 one definition here,
C4/C7 zero here as consumer. Roles agree: the operations table, the request
resolver, and the async guard are consumers; the test rows are oracles; the
module docstring, glossary anchor, consumer docs, and spec decisions are
projections. No oracle was rewritten to read from the owner it checks:
`tests/mutations/test_permissions.py` asserts literal expectations (real
users with real perms returning literal `True` / `False`; async, awaitable,
and non-bool rejections by behavior; snapshot-pollution walks by denial
outcome). The owner-reading pins (the default-tuple identity rows and the
action-map pin) assert literal right-hand sides and are honestly graded as
such in the artifact; they pin wiring, not the walk.

### Equivalence (principle 8)

Zero production edits, so no behavior delta to prove equivalent. Both
read-only probes were re-run in the shared tree (no source mutation, no SQL,
no pytest): `probe_w1.py` ALL OK (27 checks), `probe_w2.py` ALL OK (41
checks). Together they cover short-circuit order and call lists, exception
identity (`SyncMisuseError` vs `ConfigurationError`), recourse attachment,
coroutine closing, `DenyAll` denial across five operations, the exact
three-entry operation map, and the exactly-two delegating seams. One weak
probe line noted: `probe_w2.py`'s `serializer-inherits-model-seam` check is
tautological (`or True`). I verified the underlying claim myself instead
(`rest_framework/sets.py` carries no `check_permission` or
`run_permission_classes` body; the auth holder binds the base method), so the
claim holds and the weakness is scratch quality, not a finding defect.

### Rejections, gates, pending, coupling

- F1: the four-clause difference re-verified from the runtime literals via
  the re-run probe; the trigger (the two sentences converging to differ only
  in the subject noun) is concrete. Durable homes confirmed in place: the
  declining docstring at `utils/querysets.py::sync_pipeline_recourse`
  (verified: it declines both the Relay and the permission recourses), the
  four-clause comment above `_PERMISSION_ASYNC_RECOURSE`, the twin comment
  above `_GATE_ASYNC_RECOURSE`.
- F2: the three-contract difference verified against the three bodies
  (bool-per-operation vs queryset-per-edge vs gates-per-field-with-dedup);
  the trigger (one hook returning a queryset plus a verdict) is concrete.
  The owner-docstring home lives HERE as claimed: the target module
  docstring carries the separation clause ("first-class, separate contract
  from row visibility", verified present), and the
  `utils/permissions.py` module docstring carries the mechanics-only clause
  (verified present).
- Structural gates: none owed inside a file item; the family items own them.
  W1's withholding of the refusal family (`awaitable-refusal-and-disposal`)
  and the boundary family (`one-sync-boundary`) is judged correct: the
  target consumes `reject_async_in_sync_context` by name with no dispose
  body of its own, and it contains no boundary call (it runs inside the
  pipeline's boundary). There is no negative control to fail here.
- `## Pending execution`: the artifact carries no such section, which is
  compliant (absent when none). Sharded/Postgres
  inapplicable-by-construction is accepted: the target holds no
  database-alias or dialect branch (pure bool/tuple/string composition; the
  only database-touching call is Django's `user.has_perm`, owned outside
  this file and gated by the pipeline's auth-alias phase, not by logic here).
- Coupling: none introduced (zero edits). F4/F6 cite HEAD-pinned
  `mutations/sets.py` text whose worktree drift is wording-only (above) -
  no coupling to record.

### AGENTS.md prose check

- Item-scoped diff empty under both baselines; no production or test file
  touched; all concurrent dirt from `git status --short` (including
  `mutations/sets.py`, `mutations/fields.py`, `filters/*`, `forms/inputs.py`,
  `connection.py`, `extensions/resource_policy.py`, and the tests/docs
  companions) left untouched.
- Citations use `path::Symbol` reference-style links with the bottom
  `LINK DEFINITIONS` block carrying all ten canonical group headers.
- No process provenance beyond the required `Run:`, freshness blobs, and
  baseline rows. No changelog edit, no commit, no branch move.
- Tests: none added or rewritten, which is correct for a zero-edit file
  item (consolidation and gates live in the holding family items). No
  shared-tree pytest run (not authorized); the two read-only probes were
  re-run green.
- The em-dash/arrow glyphs in this artifact are markdown prose, outside the
  ASCII-only `.py` rule; the target file itself is fully ASCII, and the
  probe docstring dashes are untracked scratch, not shipped source. No
  violation. Ruff is a no-op on this markdown-only edit, and a full-tree
  run was withheld to avoid touching concurrent dirt.

### Verdict

`Status: verified`. Zero-edit file item: the six-axis matrix is discharged
against the target's real surface (three permission flavors first), 12/12
members are assigned with counts agreeing, both rejections carry contract
differences plus triggers with durable homes at the owners, and freshness
is bound except for the two record-level notes Worker 0 must carry into
`## Outcomes` (rebind `mutations/sets.py` at closeout bytes; bind
`forms/sets.py` `36ce80b4`).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[docs-readme]: ../README.md
[dry]: DRY.md
[glossary]: ../GLOSSARY.md
[plan]: dry-0_0_15.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[operations]: ../../django_strawberry_framework/mutations/operations.py
[permissions-cascade]: ../../django_strawberry_framework/permissions.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->
[test-permissions]: ../../tests/mutations/test_permissions.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
