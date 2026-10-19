# DRY review: `django_strawberry_framework/rest_framework/hook_context.py`

Status: verified
Run: 0.0.15 2026-09-22-6

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge or is a rejection
carrying its contract difference + trigger. Zero production edits; zero
tracked files changed. HEAD at dispatch `5ee86193` confirmed unmoved at
finish (see `## Implementation (Worker 1)`).

## System trace

Small target (56 lines): two frozen dataclasses with no behavior, no imports
beyond `dataclass` + `typing.Any`, no settings reads, no DRF import, no guard
call. It DEFINES the serializer-flavor hook-surface records and nothing else:

- [hook-context][rf-hook-context]`::SerializerHookContext` — the frozen
  `(operation, write_alias, instance_pk)` triple every serializer consumer
  hook receives INSTEAD of the live located instance.
- [hook-context][rf-hook-context]`::UploadMetadata` — the frozen
  `(name, size, content_type)` descriptor standing in for a file value in the
  hook data views.

What the target owns: the two record shapes (field sets + frozen + slotted +
equality/hash from the dataclass machinery) and the hardening rationale prose
(module + class docstrings). Everything else is composition by name elsewhere.

Sites found (roles per DRY.md vocabulary):

- Sole DEFINITION of both shapes: this module (one declaration each).
- Sole PRODUCER of `SerializerHookContext`: [resolvers][rf-resolvers]`::_serializer_write_step`
  constructs exactly one instance per write step from
  `mutation_cls._mutation_meta.operation` (validated upstream by
  [mutations-sets][mutations-sets]`::require_non_delete_operation` over
  `NON_DELETE_WRITE_OPERATIONS`, owned by
  [operations][mutations-operations]), `pipeline.alias`, and the
  `pipeline.authorized_pk` snapshot (with a documented direct-invocation
  fallback to `instance.pk` at step entry, still before any of the step's
  hooks run). HEAD-wide `git grep` census: exactly one package construction
  site; every other construction is in `tests/` oracles.
- Sole PRODUCER of `UploadMetadata`: [resolvers][rf-resolvers]`::_upload_metadata`
  (guarded `name` / `size` / `content_type` reads off the stateful upload;
  `None` on any read failure). HEAD-wide census: exactly one package
  construction site; the rest are `tests/` oracles.
- CONSUMERS (call sites, all in [resolvers][rf-resolvers]): the three hook
  invocations (`get_serializer_injected_data`, `get_serializer_kwargs`,
  `get_serializer_save_kwargs`) each take `hook_context` and forward it; the
  `instance`-rejection message names `hook_context.instance_pk`. No package
  code reads `.operation` / `.write_alias` / `.instance_pk` off the record —
  those reads belong to consumer overrides (one in-tree:
  [library-schema][library-schema]`::UpdateBookSubstitutingInstance.get_serializer_kwargs`
  reads `hook_context.write_alias` + `hook_context.instance_pk`).
- CONSUMERS (hook defaults, all in [sets][rf-sets]): the three default hook
  bodies accept `hook_context: Any`, ignore it (`del`), and document the
  frozen record in prose. The `Any` seam typing (no import of this module) is
  a [sets][rf-sets]-owned decision for the holding
  `File rest_framework/sets.py` item — noted, not judged here.
- CONSUMERS (import routing): the root `_DRF_SOFT_EXPORTS` table
  ([pkg-root][pkg-root]) resolves both names lazily through this module; the
  import fires the leaf `require_drf()` package guard first, so this
  stdlib-only module needs no guard of its own. Already homed by the verified
  root + `rest_framework/__init__.py` file items (see R8).
- ORACLES: `tests/rest_framework/test_resolvers.py::test_hook_context_and_upload_metadata_invariants`
  (frozen + slotted + equality pins), the hook-receipt tests, and
  `tests/base/test_init.py` (lazy-export resolution). All pins verified
  present at HEAD bytes (line numbers shifted under concurrent dirt only).
- PROJECTIONS: [spec-039][spec-039] (Decision 7 step 4 / Decision 8: the
  `(info, *, data, hook_context)` signatures, the frozen surface, and this
  module's dependency-free posture — the contract source), the module + class
  + hook-default docstrings, the `serializermutation` anchor ([glossary][glossary]), the
  CHANGELOG breaking-change bullet.

Connected behavior examined and EXCLUDED on body evidence (all HEAD-pinned;
dirty-file claims re-verified via `git show HEAD:` — see fingerprints):

- The internal pipeline record
  [write-transaction][write-transaction]`::WriteAliasContext`
  (`alias`/`lock`/`authorized_pk`/`target_state`/phase flags/auth scope) —
  R1.
- The operation vocabulary ([operations][mutations-operations] descriptors +
  `NON_DELETE_WRITE_OPERATIONS` + `require_non_delete_operation`) — R2
  (converge).
- The sibling-flavor hook seams: model
  [mutations-sets][mutations-sets]`::DjangoMutation.check_permission(info, operation, data, instance)`
  (live instance + bare operation string) and form
  [forms-sets][forms-sets]`::_default_get_form_kwargs(info, *, data, files, instance)`
  (live instance) — R5. The one genuine cross-flavor sharing at this seam,
  [mutations-sets][mutations-sets]`::construction_kwargs` (used by both the
  form default and the serializer default), is already single-sited — no
  action.
- The request-context helpers ([utils-context][utils-context]), the
  permissions walk state ([permissions][permissions]`::_TraversalState`),
  and the sibling frozen metadata records
  (`filters/sets.py::CandidateFilterMetadata`,
  `rest_framework/inputs.py::NestedSerializerConfig` /
  `::SerializerInputShape`) — R4, R6, R7.
- Negative censuses at HEAD: zero `HookContext`/`UploadMetadata`/
  `hook_context` references in `rest_framework/inputs.py`,
  `rest_framework/serializer_converter.py`, and every other package module
  outside the sites above; zero `.operation` reads off a hook context in
  package code.

Lifetime (principle 4): one `SerializerHookContext` per serializer write
step, built after the locate/authorization snapshot and handed to the three
hooks; `UploadMetadata` instances are built per file value during
`_frozen_hook_view`. Nothing is cached, stored, or mutated afterwards — pure
per-call projections, so no owner/validity/invalidation fields are owed.

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — SEARCHED. Sibling write flavors
   (model / ModelForm / plain-form hooks) pass the live instance and/or a
   bare `operation: str`, never a frozen context record (signatures verified
   at HEAD in [mutations-sets][mutations-sets] and [forms-sets][forms-sets];
   call sites in [mutations-resolvers][mutations-resolvers] and
   [forms-resolvers][forms-resolvers]). The frozen posture is serializer-only
   by contract ([spec-039][spec-039] Decision 8; the glossary's "all three
   hooks" names exactly the serializer triple). No second frozen hook-context
   record exists; the candidate consolidation is R5 (rejected: per-spec hook
   contracts, breaking-change boundary). The internal
   `WriteAliasContext` triple-overlap (`alias`/`authorized_pk`) is R1
   (rejected: mutable pipeline interior vs frozen trust-boundary snapshot).
   The operation-vocabulary overlap is R2 (converge: this module is a
   convention consumer, verified before).
2. **Sync/async twins** — INAPPLICABLE, reason: the module defines two data
   records with no functions, no await points, no I/O, and no execution of
   any color. The serializer pipeline runs the one sync body
   (`shared-write-skeleton` family, verified); the hooks themselves are sync
   seams. There is no behavior here that could fork across a sync/async
   boundary.
3. **Derived rather than repeated knowledge** — SEARCHED. The module derives
   nothing: no name concatenation, no `_meta` reads, no settings reads
   (imports are `dataclass` + `Any` only). The three `SerializerHookContext`
   values are PROJECTED once each at the single producer from their owners
   (operation ← validated `Meta.operation`; alias ← pinned pipeline alias;
   pk ← authorization snapshot) — R1/R2. The `"create"`/`"update"` literals
   appear only in docstring prose (projection), never in a branch, gate, or
   default — verified by HEAD grep. No second derivation site for any of the
   three values or the upload triple.
4. **Inverse / round-trip pairs** — SEARCHED, none. Both records are terminal
   projections: built once, read by consumers, never parsed back into
   anything. `UploadMetadata` deliberately has no inverse — a descriptor must
   never reconstruct the stateful upload (that would hand the stream to a
   hook, the exact hazard the record exists to prevent). No build/parse,
   encode/decode, or pack/unpack half exists to pair.
5. **Contracts restated in another medium** — SEARCHED and classified. One
   definition (this module); consumers (producer + 3 call sites + 3 hook
   defaults + root lazy table, listed above); oracles (the frozen/slotted/
   equality pins + hook-receipt tests + lazy-export test, all HEAD-present);
   projections (spec-039 contract prose, module/class/hook docstrings,
   glossary anchor, CHANGELOG bullet). A field-set change moves 1 definition
   plus its consumers/oracles/projections — the expected single-owner shape,
   not duplication.
6. **Enforcement by omission** — SEARCHED, no defect. Family = the four write
   flavors' consumer hooks. Frozen-context hardening holds on the serializer
   flavor only; model/form hooks receive the live instance. No contract
   source (spec-036/038/039, glossary, oracles) establishes that the frozen
   posture applies beyond the serializer triple — specs 036/038 define their
   own hook signatures passing the live row. Per the axis rule, sibling
   behavior justifies the investigation, never the verdict: recorded as R5,
   not filed.

### Enumeration

Instrument: `ast.Module.body` over the worktree file (= HEAD bytes,
`f4910159`). 6 top-level statements: the module docstring, `from
__future__ import annotations`, `from dataclasses import dataclass`, `from
typing import Any`, `class SerializerHookContext`, `class UploadMetadata`.
Rule-bearing members: 2 classes + 6 fields. Homing (8/8):

| Member | Home |
|---|---|
| `SerializerHookContext` (+ `operation`, `write_alias`, `instance_pk`) | file-local F1 `serializer-hook-context-record` |
| `UploadMetadata` (+ `name`, `size`, `content_type`) | file-local F2 `hook-upload-metadata-record` |
| module docstring (hardening rationale) | projection, split across F1/F2 (paras 1 / 2) |
| class docstrings (field contracts) | projections on F1/F2 respectively |
| 3 imports (`annotations`, `dataclass`, `Any`) | non-rules: stdlib machinery, no package contract |

No member unassigned; no consolidation inside this file item.

### Challenges

- **C1 — add a fourth hook-context field** (e.g. a request-scoped key the
  documented use cases grow to need): definitions to move = **1** (the
  record's field set, here). The single producer gains one keyword (a
  consumer update, not a second definition — it fills the set, never defines
  it), plus oracles (invariant test) and projections (docstrings). Proves
  F1.
- **C2 — change the upload descriptor triple** (add `charset`, drop `size`):
  definitions = **1** (the record, here). The single producer
  (`_upload_metadata`) gains/loses one guarded read (consumer), plus oracles
  and projections. Proves F2.
- **C3 — tighten `operation: str` to a literal/enum**: definitions = **1**
  today BECAUSE the field is an unvalidated carrier — the domain lives once
  in [operations][mutations-operations] (`NON_DELETE_WRITE_OPERATIONS` +
  `require_non_delete_operation`). Typing the domain here would CREATE a
  second spelling to keep in sync (a new coupling needing its own
  justification, e.g. a gate). The challenge confirms the current shape is
  the minimal one; any future typing owes a family item. Supports F1 + R2.
- **C4 — relax frozen (let hooks annotate the context)**: definitions =
  **1** (the two decorators, one module, one edit — two applications of one
  stdlib idiom, not two rules). Oracles (frozen pins) + projections move.
  Confirms the frozen-ness has a single owner. Supports F1 + F2.
- **C5 — second consumer-facing hook surface needs the same triple** (the R1
  trigger, posited, not present): today there is exactly one consumer of the
  projection (the serializer write step) — no second site exists, so no
  family is named. If a flavor ever needs it, the PROJECTION (this record +
  its fill line), not the mutable pipeline interior, is the shared form.

All challenges `static-reviewed`: the claims are structural (single
declaration, single producer, no branches) and the behavior pins already
exist as permanent oracles (`test_hook_context_and_upload_metadata_invariants`,
`test_default_serializer_mutation_instance_hook_methods`, the root
lazy-export test). No executable experiment was needed; nothing uncertain
remains.

## Findings

### F1 `serializer-hook-context-record` (file-local)

- **Contract + variation.** The frozen consumer-facing identity triple for
  serializer hooks: `operation` (the validated `Meta.operation` value),
  `write_alias` (the pinned pipeline alias, so hook queries join the one
  transaction), `instance_pk` (the authorized target's pk snapshot, `None`
  on create). Varies only by the operation's own values; the SHAPE is fixed.
- **Sites + roles.** Definition: this module (1 declaration). Sole producer:
  [resolvers][rf-resolvers]`::_serializer_write_step` (fills from the three
  owners). Consumers: the 3 hook call sites + 3 hook defaults + root lazy
  table + in-tree example override. Oracles + projections as traced above.
- **Challenges.** C1 (count 1), C3 (count 1; typing would create a second
  spelling), C4 (count 1).
- **Owner + lifetime.** This module — the narrowest cohesive owner every
  legitimate consumer (resolvers, sets prose, root export, consumer
  overrides) can depend on without importing a sibling flavor's machinery.
  Per-call lifetime, never cached (see trace).
- **Distinct behavior.** The `Any`-typed pk and unvalidated `str` operation
  are deliberate carrier choices (validation lives at
  `require_non_delete_operation` + the pipeline snapshot); C3 records why.
- **Behavioral proof.** `static-reviewed`: oracles pin frozen/slotted/
  equality and hook receipt; no ordering/transactional/async content to
  execute.
- **Freshness.** Target `f4910159` (both); producer/call-site bodies
  verified identical at HEAD `8024703e` vs work `c0b54039` (dirt touches no
  hook-context line — all 39 `@@` hunks enumerated, none naming
  `hook_context`/`HookContext`/`UploadMetadata` outside unchanged context);
  hook defaults identical at HEAD `2c7117d6` vs work `70a1e1b16` (all 9
  hunks end at HEAD line 608, region untouched); vocabulary chain
  `16223c6b` (clean), `cffa29e5`/`936f5ae7` (gate body HEAD-verified),
  skeleton `3fd1e571`/`a322d17a` (capture lines HEAD-verified).

### F2 `hook-upload-metadata-record` (file-local)

- **Contract + variation.** The frozen `(name, size, content_type)` file
  descriptor for hook data views; the stateful upload never reaches a hook.
  Fixed shape; values vary per file.
- **Sites + roles.** Definition: this module (1 declaration). Sole producer:
  [resolvers][rf-resolvers]`::_upload_metadata`. Consumers: `_frozen_hook_view`
  (embeds descriptors) + hook overrides branching on them. Oracles +
  projections as traced.
- **Challenges.** C2 (count 1), C4 (count 1).
- **Owner + lifetime.** This module (same reasoning as F1; co-located with
  its only sibling consumer-surface record, dependency-free per spec-039).
  Per-file-value lifetime, never cached.
- **Distinct behavior.** No inverse constructor exists by design (axis 4);
  unvalidated field types are deliberate (values originate from
  framework-decoded uploads, never consumer code — near-miss N2 ruled out).
- **Behavioral proof.** `static-reviewed` (same oracles).
- **Freshness.** Target `f4910159` (both); producer verified identical at
  HEAD `8024703e` vs work `c0b54039` (the `_frozen_hook_view` wording hunk
  touches neither `_upload_metadata` nor any descriptor line).

### Rejections (contract difference + trigger)

- **R1 — `SerializerHookContext` vs internal `WriteAliasContext`.**
  Difference: the pipeline record is MUTABLE interior lifecycle state
  (`alias`, `lock`, `authorized_pk`, `target_state`, `write_phase`,
  `auth_phase`/`auth_aliases`) that the guard, skeleton, and flavors mutate
  through the operation; the hook record is a FROZEN snapshot of three
  values crossing a TRUST BOUNDARY into indefinitely-held consumer code.
  Handing hooks the interior object would expose phase flags and the loaded
  target state to mutation. One projection line (not a second definition)
  copies the two overlapping values. Trigger: a second consumer-facing hook
  surface needing the same triple (C5) — then share THIS projection, never
  the interior. Fresh pair, no prior verdict. Durable home: this artifact
  (both owners' docstrings already state their own contract; no doc edit in
  a file item).
- **R2 — `operation` vocabulary vs `mutations/operations.py`.** Difference:
  none to resolve — this module DEFINES no vocabulary (unvalidated `str`,
  zero literal branches; literals live only in docstring prose). It is a
  convention consumer of the owned domain. CONVERGE with verified
  `mutations/operations.py` F(g) ("convention consumers; no definition
  lives here") on FRESH evidence: HEAD grep shows no `== "create"` /
  `== "update"` in this module, and the value chain
  (`require_non_delete_operation` → `_ValidatedMutationMeta.operation` →
  construction kwarg) re-verified at HEAD bytes. Trigger: typing the field
  (C3) would create a real second spelling.
- **R3 — frozen-record shape vs the ~50 `@dataclass(frozen=True)` records.**
  Difference: `frozen=True[, slots=True]` is a stdlib idiom, not a package
  rule — each record (descriptors, policies, plans, shapes, this pair) has a
  disjoint field set, contract, and lifetime, and no shared driver exists.
  A shared frozen-record base/factory would couple independent domains for
  zero change-obligation relief (C4 moves one module either way). Trigger: a
  package-wide frozen-record MECHANISM need (e.g. a shared validation or
  fingerprint protocol), not mere decorator repetition. Fresh; no standing
  verdict found in `docs/dry/` (searched).
- **R4 — `UploadMetadata` vs sibling metadata records.**
  Difference: `CandidateFilterMetadata` (filter-leaf routing row),
  `NestedSerializerConfig` (nested-input opt-in), `SerializerInputShape`
  (generated-shape identity) each answer a different question for a
  different consumer; the shared token is the English word "metadata".
  Posit a change to any one (a routing bit, an opt-in flag, a shape
  component) — no other moves. Trigger: a second FILE-descriptor need
  (a second producer of `(name, size, content_type)`). Fresh.
- **R5 — one hook-context record for all write flavors.** Difference: each
  flavor's hook signature is its own spec'd public contract — model
  `check_permission(info, operation, data, instance)` (spec-036), form
  `get_form_kwargs(info, *, data, files, instance)` (spec-038), serializer
  `(info, *, data, hook_context)` (spec-039 Decision 8). Unifying them is a
  breaking public-API change owned by those specs, not a DRY consolidation;
  no shared consumer needs one record (each flavor's producer + hooks form a
  closed triple). The axis-6 omission probe (frozen posture only on
  serializer hooks) found no contract source extending it — investigated,
  not a defect. Trigger: a spec unifying the write-flavor hook signatures.
  Fresh.
- **R6 — `utils/context.py` request-context helpers.** Difference: different
  population entirely — shape-agnostic read/write/delete over STRAWBERRY
  `info.context` (None/object/dict/frozen), no record shape, no hook
  surface. Shared token is the English word "context". Trigger: none
  foreseeable (disjoint domains). Fresh.
- **R7 — `permissions.py::_TraversalState`.** Difference: private,
  ContextVar-carried per-walk traversal state (`alias`/`active`/`path`) for
  the permission cascade — internal frame bookkeeping, never handed to
  consumer code, disjoint fields and lifetime. Trigger: none (a second
  cascade-walk state, not a hook record, would reopen it). Fresh.
- **R8 — root lazy-export table rows.** Difference: none to resolve — the
  `_DRF_SOFT_EXPORTS` entries are import ROUTING (consumers), already homed
  by the verified root + `rest_framework/__init__.py` file items (guard
  posture, lazy-export hook). CONVERGE on fresh evidence: this module is
  listed there by name only, and its guard-free body is correct because the
  parent-package import fires `require_drf()` first (leaf posture,
  verified). No trigger (routing follows the definition by construction).

## Defects

None filed. Three near-misses investigated and ruled out (not defects):

- **N1 — `instance_pk` docstring vs the direct-invocation fallback.**
  The record documents the snapshot as "captured immediately after the
  locate, before any consumer code ran"; the producer falls back to
  `instance.pk` at step entry when invoked without the skeleton. Ruled out:
  the fallback still runs before any of the step's hooks, the permission
  hook does not run in a direct invocation, and the producer comment states
  the fallback explicitly. No contradiction.
- **N2 — unvalidated `UploadMetadata` field types.** Ruled out: carrier
  record; values originate from framework-decoded uploads, never consumer
  code; no contract requires validation. A hostile client file object is
  contained by the producer's guarded reads (`None` on failure), and the
  framework-decoded stream objects carry real types.
- **N3 — no `__all__` in the module.** Ruled out: two-public-class leaf
  imported by name; the root table routes by name; matches the verified
  guard-leaf precedent (no manifest where none is needed).

Out of scope, noted for the holding item (not a defect): the `hook_context:
Any` seam typing in the [sets][rf-sets] hook defaults (a
`File rest_framework/sets.py` decision — that item judges whether to import
the record or keep the seam untyped).

## Pending execution

None. No `proof:` entries (all findings `static-reviewed` against permanent
oracles); no `gate:` entries. Sharded/Postgres cells are inapplicable by
construction: the module defines two frozen data records with no database
access, no alias or dialect decision, and no queryset involvement.

## Judgment

Zero-edit file item. The target is two single-owned frozen records with one
producer each, consumed by name, pinned by permanent oracles, and projected
in spec prose. Every cross-flavor and cross-module lookalike was discharged
on body evidence (2 convergences with verified prior verdicts on fresh
evidence, 6 fresh rejections); the axis-6 omission probe found no contract
source and yields no defect. No families to name, no defects to home.

## Implementation (Worker 1)

No tracked files changed; no ledger rows (file items land none). Worker-0
instructions: (a) tick the plan item
`File rest_framework/hook_context.py — dry-file-rest_framework__hook_context.md`
as verified under Run `0.0.15 2026-09-22-6` once Worker 2 concurs; (b) add
the ten `## Responsibility index` rows below verbatim (2 file-local, 8
rejected); (c) add NO `## Families` item (no multi-definition rule found);
(d) nothing to remove (no `docs/dry/temp-tests/` scratch was created; all
probes were read-only greps / `git show` / `git hash-object` / `git grep` /
one `ast` one-liner). No commit. HEAD at finish `5ee86193` (unmoved from
dispatch; `git rev-parse HEAD`).

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `serializer-hook-context-record` | `django_strawberry_framework/rest_framework/hook_context.py::SerializerHookContext` | `django_strawberry_framework/rest_framework/hook_context.py` | File `rest_framework/hook_context.py` | file-local |
| `hook-upload-metadata-record` | `django_strawberry_framework/rest_framework/hook_context.py::UploadMetadata` | `django_strawberry_framework/rest_framework/hook_context.py` | File `rest_framework/hook_context.py` | file-local |
| `hook-context-vs-pipeline-interior` | `django_strawberry_framework/rest_framework/hook_context.py::SerializerHookContext` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/utils/write_transaction.py` | File `rest_framework/hook_context.py` | rejected |
| `hook-context-operation-vs-vocabulary` | `django_strawberry_framework/mutations/operations.py` (rejection recorded here; CONVERGE with verified mutations/operations F(g) on fresh evidence) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/mutations/operations.py`, `django_strawberry_framework/mutations/sets.py` | File `rest_framework/hook_context.py` | rejected |
| `hook-context-frozen-record-idiom` | `django_strawberry_framework/rest_framework/hook_context.py` (rejection recorded here; fresh, no standing verdict) | `django_strawberry_framework/rest_framework/hook_context.py` | File `rest_framework/hook_context.py` | rejected |
| `hook-upload-metadata-vs-sibling-records` | `django_strawberry_framework/rest_framework/hook_context.py::UploadMetadata` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/hook_context.py` | rejected |
| `hook-context-cross-flavor-record` | `django_strawberry_framework/rest_framework/hook_context.py::SerializerHookContext` (rejection recorded here; fresh, axis-6 probe, no defect) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/hook_context.py` | rejected |
| `hook-context-vs-request-context-helpers` | `django_strawberry_framework/rest_framework/hook_context.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/utils/context.py` | File `rest_framework/hook_context.py` | rejected |
| `hook-context-vs-traversal-state` | `django_strawberry_framework/rest_framework/hook_context.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/permissions.py` | File `rest_framework/hook_context.py` | rejected |
| `hook-context-lazy-export-routing` | `django_strawberry_framework/__init__.py::__getattr__` (rejection recorded here; CONVERGE with verified root + rest_framework/__init__ on fresh evidence) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/__init__.py`, `django_strawberry_framework/rest_framework/__init__.py` | File `rest_framework/hook_context.py` | rejected |

Freshness fingerprints (`git hash-object` = worktree, `git rev-parse
HEAD:` = HEAD; dirty-file claims additionally verified against HEAD bytes):

| Input | Worktree | HEAD | State |
|---|---|---|---|
| `rest_framework/hook_context.py` (target) | `f4910159` | `f4910159` | CLEAN |
| `rest_framework/resolvers.py` | `c0b54039` | `8024703e` | DIRTY, hook-context lines HEAD-identical (39 hunks enumerated) |
| `rest_framework/sets.py` | `70a1e1b16` | `2c7117d6` | DIRTY, hook-default region HEAD-identical (9 hunks, all ≤ HEAD 608) |
| `rest_framework/inputs.py` | `9b17d952` | `9b17d952` | CLEAN (negative census) |
| `rest_framework/serializer_converter.py` | `95568390` | `32904418` | DIRTY, negative census holds at both |
| `rest_framework/__init__.py` | `45cf7b63` | `45cf7b63` | CLEAN |
| `__init__.py` (root) | `0ef72601` | `0ef72601` | CLEAN |
| `mutations/operations.py` | `16223c6b` | `16223c6b` | CLEAN |
| `mutations/sets.py` | `936f5ae7` | `cffa29e5` | DIRTY, gate + seam bodies HEAD-verified |
| `mutations/resolvers.py` | `a322d17a` | `3fd1e571` | DIRTY, snapshot lines HEAD-verified |
| `forms/sets.py` | `98ef150d` | `36ce80b4` | DIRTY, hook-default signature HEAD-verified |
| `forms/resolvers.py` | `4edb984b` | `4edb984b` | CLEAN |
| `utils/write_transaction.py` | `9ad493b6` | `eca9ad4d` | DIRTY, record body HEAD-verified |
| `utils/context.py` | `cd0adcc5` | `cd0adcc5` | CLEAN (excluded on body) |
| `permissions.py` | `757dce34` | `757dce34` | CLEAN (excluded on body) |
| `filters/sets.py` | `c1a0f1b2` | `722e0c77` | DIRTY, metadata record read at HEAD |
| `tests/rest_framework/test_resolvers.py` | `b8ce1dfd` | `8dc889fd` | DIRTY, oracle pins HEAD-present |
| `tests/rest_framework/test_sets.py` | `85c4c3a0` | `7e7d1819` | DIRTY, oracle pins HEAD-present |
| `tests/base/test_init.py` | `239648ed` | `4cc12105` | DIRTY, oracle pins HEAD-present |
| `examples/.../library/schema.py` | `bed9d071` | `bed9d071` | CLEAN (consumer override) |

## Independent verification (Worker 2)

Recorded expectation-first: the trace, counts, and owner calls below are my
own, derived from HEAD bytes (`git show HEAD:` for every hunt-dirty file)
before reconciling with `## Findings`. HEAD `5ee86193` confirmed unmoved at
my finish; window diff vs `ITEM_BASELINE=ce3ed947…` names only the plan's
Worker-0 accounting hunk plus this new untracked artifact — no third-party
hunk in any path the item touches.

### W2 trace: sites, roles, counts, owner calls

- Definitions (2, both in the target): `hook_context.py::SerializerHookContext`
  `(operation, write_alias, instance_pk)` and `hook_context.py::UploadMetadata`
  `(name, size, content_type)`. No second declaration of either shape exists
  package-wide (census below).
- Sole producers: `rest_framework/resolvers.py::_serializer_write_step`
  constructs the single `SerializerHookContext` per write step (HEAD line
  2190; exactly one package construction site; all others are `tests/`
  oracles); `rest_framework/resolvers.py::_upload_metadata` constructs every
  `UploadMetadata` (HEAD line 633; exactly one package site). Both fill from
  owners by name (`_mutation_meta.operation`, `pipeline.alias`,
  `pipeline.authorized_pk`; guarded `File` attr reads).
- Consumers: the three hook call sites (all take and forward `hook_context`),
  the three `rest_framework/sets.py` hook defaults (`hook_context: Any`,
  `del`-ignored, prose-documented), the root `_DRF_SOFT_EXPORTS` routing rows,
  one in-tree example override reading `.write_alias`/`.instance_pk`. No
  package code reads a record field off either shape (only prose mentions).
- Oracles (all HEAD-present, all spelling expectations literally, never
  reading the owner): the frozen/slotted/equality pins, the three-defaults
  hook-receipt test (W2-C3: it lives in `tests/rest_framework/test_sets.py`,
  not `test_resolvers.py`), the lazy-export resolution test.
- Projections: spec-039 Decision 8 + signature prose, the glossary "all three
  hooks" anchor, the CHANGELOG breaking bullet, module/class/hook docstrings.
- Per-change definition counts (my own challenges): add a context field → 1;
  change the upload triple → 1; type `operation` → 1 today (typing would
  CREATE a second spelling — the domain lives once in
  `mutations/operations.py`); relax frozen → 1 module; a second
  consumer-facing surface needing the triple → 0 present (trigger only).
- Owner calls: the target module for both records (narrowest
  dependency-free owner every consumer can import); ZERO families — no
  second producer, no parallel context record, no shadow triple found.
  `WriteAliasContext` is mutable pipeline interior with phase flags,
  `target_state`, and no `operation` member (disjoint lifecycle, not a twin);
  every sibling `*Metadata`/`*Context*`/`*Snapshot` record answers a
  different question (`CandidateFilterMetadata` routes filter leaves;
  `_FileNameSnapshot` is drift-check behavior, never handed to hooks);
  cross-flavor hooks pass the live instance / bare `str` under their own
  specs. My calls match W1's F1/F2/R1–R8 one for one.

### W2 enumeration (instrument: `ast.Module.body`, my count: 6 / 8)

My statement count matches W1's exactly: module docstring, three imports,
two classes. Member-by-member homing check: `SerializerHookContext` + its
three fields → F1; `UploadMetadata` + its three fields → F2 (8/8
rule-bearing members homed, agreed); module docstring paras 1/2 →
projections on F1/F2 (verified: para 1 is hook-context rationale, para 2 is
upload-descriptor rationale); class docstrings → projections on their
record; three imports → stdlib machinery, no package contract. The two
`@dataclass(frozen=True, slots=True)` applications ride with their classes
and are independently discharged by R3 + C4. Nothing unassigned.

### W2 matrix (against the target's real surface)

Axis 1 searched (sibling seams, pipeline interior, vocabulary all re-read at
HEAD — real surface, not sampled). Axis 2 inapplicable, reason sound (pure
data, no function, no await, no color). Axis 3 searched (`"create"` /
`"update"` literals confirmed docstring-only by HEAD grep; the three values
projected once each from their owners). Axis 4 searched, none — the
no-inverse argument verified as a design entailment (an inverse would hand
the stream to a hook). Axis 5 classified, roles confirmed (no oracle reads
the owner). Axis 6 searched, no defect: family = the four write flavors'
hooks; no contract source extends the frozen posture past the serializer
triple (specs 036/038 spec the live-instance seams; the glossary names
exactly the serializer triple). Sharded/Postgres inapplicability endorsed:
no database, alias, or dialect surface exists in the module.

### W2 convergence + rejection judgments (fresh evidence)

- R2 CONVERGE endorsed, and the prior verdict is stronger than cited: the
  operations artifact's re-review row (g) literally names
  `SerializerHookContext.operation` as a "convention consumer … no
  definition lives here" (quote verified verbatim), and R6's Home is this
  rest_framework file item with verdict SURVIVES. The value chain
  (`require_non_delete_operation` at HEAD rf-sets:601 →
  `_ValidatedMutationMeta.operation` slot → construction kwarg) re-verified
  at HEAD bytes. See W2-C1 for the citation-precision note.
- R8 CONVERGE endorsed: my independent census is exactly 2 module-level
  `__getattr__` (root:98, routers:556 — line shifted under hunt dirt, count
  stands); the leaf is correctly hookless and manifestless; the guard-free
  body is correct because the parent-package import fires `require_drf()`
  first (leaf body re-read). Root R2 + leaf J5 converge holds.
- R1/R3/R4/R5/R6/R7 endorsed as fresh rejections with load-bearing contract
  differences and triggers: mutable-interior vs frozen-trust-boundary (R1);
  stdlib idiom over 47 `@dataclass(frozen=True` sites, disjoint contracts
  (R3 — count re-derived); English-word collisions, one-change-moves-one
  (R4, R6); per-spec public hook signatures, breaking-change boundary, with
  the axis-6 probe correctly yielding no defect (R5); private
  ContextVar-carried walk frame, never consumer-handed (R7).

### W2 rule-out judgments (N1/N2/N3 + seam note)

- N1 endorsed. Strengthening evidence beyond W1's reasoning: the fallback is
  production-dead — the step's sole production caller runs inside
  `run_write_pipeline_sync`, which always snapshots `authorized_pk` before
  the permission hook (HEAD mutations-resolvers:246-250), so the fallback
  condition can only fire on direct (test-only, private-function)
  invocation. The docstring describes the production contract exactly; the
  producer comment documents the fallback explicitly. No wire input under
  supported public API reaches the fallback path — not a defect.
- N2 endorsed with correction W2-C2. The wire path carries real Django
  `File` types through an `isinstance` gate with guarded reads (no crash,
  no framework read of any field), and no contract source requires field
  validation — but W1's "never consumer code" overstates: injected values
  merge into the kwargs/save-kwargs frozen views, so a consumer CAN inject a
  `File`. That breakage would be first-party only (the injector's own
  downstream reads; framework code never reads the fields), so no contract
  row breaks. Verdict stands.
- N3 endorsed. Absence is the folder norm (no `rest_framework/` module
  carries `__all__`; 45/117 package files do), the root table routes by
  name, and no star-import of this module exists anywhere. Matches the
  verified guard-leaf precedent.
- The `hook_context: Any` seam note is correctly routed-not-filed: the
  annotations live in `rest_framework/sets.py` (pending item), they break no
  runtime contract (consumers receive the record regardless), and judging
  them here would exceed this file item's fence.

### W2 corrections (evidence-precision, none structural, none verdict-affecting)

- W2-C1: R2's "F(g)" shorthand is cryptic — the converged row is the
  operations artifact's bounded-re-review `### 2.` row (g) (the `## Findings`
  section proper uses F1 + R1–R8). Companion cite: R6, whose Home is this
  item. Quotes and verdict verified verbatim; convergence stands.
- W2-C2: N2 supporting sentence "values originate from framework-decoded
  uploads, never consumer code" — see rule-out judgment above for the
  injected-data path (`final_data = {**provided_data, **injected}`, HEAD
  resolvers:2252). Rule-out stands on the corrected ground.
- W2-C3: `test_default_serializer_mutation_instance_hook_methods` lives in
  `tests/rest_framework/test_sets.py:2127` (HEAD), not alongside the
  `test_resolvers.py` oracle named next to it. All pins HEAD-present as
  claimed; independent-oracle status confirmed (spells literals).
- W2-C4 (supporting, not corrective): N1's rule-out can cite
  production-deadness (sole production caller via the skeleton) in addition
  to W1's three reasons.

### W2 freshness, window, and checks

- All 19 W1 fingerprints independently re-hashed (worktree + HEAD): match
  every row. Relied-upon dirty-file claims re-verified against HEAD bytes:
  producer/call-site bodies, hook defaults + `Any` seams, vocabulary chain,
  skeleton snapshot lines, sibling records, oracle pins.
- Diff-shape claims verified mechanically: 39 resolvers hunks / 9 sets
  hunks, zero added/removed hook-token lines across both, all sets hunks at
  or below HEAD line 608 (hook region at 908+ untouched).
- Item-scoped diff: only the plan's Worker-0 accounting hunk plus this new
  artifact; no production edit by W1 (zero-edit confirmed), none by me. No
  scratch created by either worker (scope dir absent). No `.py` touched, so
  no ruff target exists (nothing to `--check`); the trailing-comma script
  excludes this `.md` path (verified via `--check` run).
- Prose rules: `path::Symbol` citations throughout, no process provenance
  (only the sanctioned role headings + a Worker-0 handoff line), link
  scaffold 10/10 canonical headers in order with alphabetical defs, every
  inline label defined, every def used.

### W2 verdict

`verified` (zero-edit). Enumeration 6/6 statements and 8/8 members homed;
matrix discharged against the real surface; zero-family claim holds under
an independent whole-package census (single producer per record, no second
shape, no shadow triple); both convergences verified on fresh evidence
(R2 against the row that literally names this field; R8 against a
re-derived exactly-2 hook census); all three rule-outs endorsed (N2 on
corrected ground per W2-C2); the seam note correctly routed to the pending
`rest_framework/sets.py` item; no defects found by W1 or W2; no pending
execution. Findings reconciliation: no differences of substance — four
evidence-precision corrections (W2-C1–C4) only.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[permissions]: ../../django_strawberry_framework/permissions.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[rf-hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[utils-context]: ../../django_strawberry_framework/utils/context.py
[write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py

<!-- tests/ -->

<!-- examples/ -->
[library-schema]: ../../examples/fakeshop/apps/library/schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
