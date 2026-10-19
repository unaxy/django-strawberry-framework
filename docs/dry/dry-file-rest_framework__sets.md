# DRY review: `rest_framework/sets.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target `django_strawberry_framework/rest_framework/sets.py`: the
`SerializerMutation` base — `Meta` validation matrix, schema-hook
discovery + validation, the phase-2.5 input seams (`build_input` /
`input_type_name`), the three serializer construction hooks, and the
resolver-seam bindings. It rides the `DjangoMutation` base
([mutations-sets][mutations-sets]) exactly as the `038` form flavor does
(spec-039 Decision 6): same metaclass, same declaration registry, same
`bind_mutations()` drain; the serializer behavior is seam overrides.

Attribution (diff content vs `git show HEAD:<path>`, never filename):
HEAD blob `2c4c4930` (1013 lines), worktree `2b88fe58` (1000 lines).
The worktree dirt is concurrent-external — hunt `truth.*` migration
(`_safe_arg_repr` → `truth.render`, `getattr`/`issubclass`/`__dict__`
→ `truth.*` reads), the maintainer's `except BaseException` arm
deletion, and an identifier-gate addition in `_validate_schema_field_map`
— in neither the `## Owned changes` ledger (no `sets.py` rows) nor the
`## Cycle baseline` block (no `sets.py` paths). This item touches only
the new artifact (zero production edits), so the dirt is concurrent work
left alone, not a stop. Every claim below is traced at HEAD bytes;
connected dirty files are likewise read at HEAD with both fingerprints
recorded. HEAD `0c0537e2` throughout; `ITEM_BASELINE=467448e9fc52debd8d3f5f7ad519456372e7ba77`.

What the target owns: the serializer `Meta` matrix
(`serializer_class` / `operation` / narrowing / `optional_fields` /
`injected_fields` / `select_for_update` / `nested_fields` /
`permission_classes`); the schema-hook result validator
(`_validate_schema_field_map`) + the single guarded bind read
(`_checked_schema_field_map`) + the determinism fingerprint capture;
the nested opt-in validator (`_validate_serializer_nested_fields`) +
the operation→write-method map; the schema-time source-ownership walker;
the `get_serializer_for_schema` default; the build/name seams; the three
hook defaults; the `resolver_seams(...)` bindings. Everything else it
touches it composes by name (spine helpers in [mutations-sets][mutations-sets],
shaping machinery in [rf-inputs][rf-inputs], conversion in
[rf-converter][rf-converter]).

Connected behavior examined (all at HEAD bytes): [mutations-sets][mutations-sets]
(base seams, all 16+ composed helpers, drain, field-factory protocol in
[mutations-fields][mutations-fields], vocabulary in [operations][operations]);
[forms-sets][forms-sets] in full (the mandatory mirror — matrices, discovery
default, invocation boundary, waiver, tails, seams); [rf-inputs][rf-inputs]
(every composed shaping helper's contract);
[rf-resolvers][rf-resolvers] (`_hook_mapping`, merged kwargs, runtime
ownership twin, agreement guards, the 3 hook call sites);
[rf-converter][rf-converter] (nested detection/child);
[hook-context][hook-context] (the carried `hook_context: Any` seam note —
adjudicated in F-HOOKS); [forms-inputs][forms-inputs] (`_form_field_basis`
identifier gate); [utils-inputs][utils-inputs] (spine: normalize,
`guard_dropped_required`, `resolve_effective_fields`, `generated_input_type_name`,
`build_strawberry_input_class`); the 87 oracles in [test-sets][test-sets];
[spec-039][spec-039] Decisions 6/7/8/10/11/12; the `serializermutation`
anchor in [glossary][glossary]; 23 in-tree example subclasses in
[library-schema][library-schema]. Prior file artifacts read as
rejected-candidate triggers only (never evidence):
`dry-file-forms__sets.md`, `dry-file-mutations__sets.md`,
`dry-file-rest_framework__inputs.md`,
`dry-file-rest_framework__resolvers.md`,
`dry-file-rest_framework__serializer_converter.md`,
`dry-file-rest_framework__hook_context.md`,
`dry-file-rest_framework____init__.md`.

Freshness fingerprints (every input inspected; `HEAD`/`WT` = first 8 of
`git rev-parse HEAD:<path>` / `git hash-object <path>`):

| Input | HEAD | WT | State |
|---|---|---|---|
| `rest_framework/sets.py` (target) | `2c4c4930` | `2b88fe58` | DIRTY (concurrent, untraced) |
| `mutations/sets.py` | `7800bd53` | `21c15c0b` | DIRTY (traced at HEAD) |
| `forms/sets.py` | `36ce80b4` | `2642a647` | DIRTY (traced at HEAD) |
| `rest_framework/inputs.py` | `2410f380` | `eab5cf34` | DIRTY (traced at HEAD) |
| `rest_framework/resolvers.py` | `0d302782` | `c49ce3c2` | DIRTY (traced at HEAD) |
| `rest_framework/serializer_converter.py` | `6652d092` | `96d2b56a` | DIRTY (traced at HEAD) |
| `rest_framework/hook_context.py` | `646377d9` | `646377d9` | CLEAN |
| `rest_framework/__init__.py` | `45cf7b63` | `45cf7b63` | CLEAN |
| `mutations/inputs.py` | `fc442047` | `840da733` | DIRTY (traced at HEAD) |
| `mutations/operations.py` | `9fecef04` | `dda68775` | DIRTY (traced at HEAD) |
| `mutations/fields.py` | `d4edcbb7` | `0e4d5ed1` | DIRTY (traced at HEAD) |
| `mutations/permissions.py` | `54f770ae` | `55e5edf8` | DIRTY (traced at HEAD) |
| `forms/inputs.py` | `6418753d` | `259afbb2` | DIRTY (traced at HEAD) |
| `utils/inputs.py` | `ee31d360` | `b5af8255` | DIRTY (traced at HEAD) |
| `exceptions.py` | `e06b0b7f` | `206e9f8d` | DIRTY (import only) |
| `__init__.py` (root) | `0ef72601` | `0ef72601` | CLEAN |
| `tests/rest_framework/test_sets.py` | `ff621ce8` | `078e8486` | DIRTY (traced at HEAD) |
| `docs/GLOSSARY.md` | `3413edc3` | `3413edc3` | CLEAN |
| `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | `cf78af93` | `cf78af93` | CLEAN |
| `examples/fakeshop/apps/library/schema.py` | — | — | consumer census only (23 subclasses) |

Main drift since the sibling verifications (`5ee86193..0c0537e2`) on
every connected file is the one-line `e6a33c46` docstring-first-line
prose (target `2c7117d6→2c4c4930` is that line only) — no finding the
siblings recorded moves, and every CONVERGE below re-derives fresh at
HEAD bytes rather than inheriting.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** [forms-sets][forms-sets] read in
   full (1035 lines) + [mutations-sets][mutations-sets] seams/kit/drain
   (all composed helpers re-read at HEAD). Pairs adjudicated:
   `Meta` matrices (R-merged), allowed-key unions (F-KEYS),
   discovery defaults (FAM-OWN), invocation boundary vs result
   validation (R-formdisc, R-invoke), waiver vs `injected_fields`
   (recorded separation, F-BUILD), build/name tails (F-BUILD/F-NAME,
   R-cached, R-formname), `construction_kwargs` (shared, consumed),
   `build_and_stash_input` (shared, consumed), `resolver_seams`
   bindings (shared factory, F-SEAMS), `input_module_path` bindings
   (F-NS), `_input_field_specs` declarations (F-SLOTS, R-slotredecl),
   hook defaults (F-HOOKS), ownership walkers (R-runtime),
   identifier gate (R-ident). No mirror left unread.
2. **Sync/async twins.** Inapplicable: the file defines no `async def`
   and no await boundary — `resolve_async` is factory-generated by
   `resolver_seams` (single body in [mutations-sets][mutations-sets],
   verified FL10 direction). Nothing here can drift across a twin.
3. **Derived rather than repeated knowledge.** Checked, holds:
   the bind discovers the field map ONCE (`_checked_schema_field_map`)
   and threads it into every helper (`resolve_effective_serializer_fields`,
   `resolve_injected_field_specs`, `_serializer_input_shape_for`) —
   no helper re-discovers; the input name is single-sourced
   (descriptor `type_name` pre-bind, stashed `__name__` post-bind —
   F-NAME); the effective set is computed per window from the same
   threaded map, never cached across windows (each window re-resolves,
   so no stale-set derivation exists). The `operation→kind` read
   composes the operations-owned map (F4 direction, F-BUILD/F-NAME).
4. **Inverse / round-trip pairs.** Fingerprint capture (`_validate_meta`)
   vs check (`_checked_schema_field_map`) — one contract, two call
   sites of the inputs-owned computation (F-DET). Build-vs-name
   agreement (`build_input` materialize name vs `input_type_name` —
   F-NAME). Schema-vs-runtime agreement halves live in
   [rf-resolvers][rf-resolvers] (consumers of the bind stash —
   F-SLOTS/F-BUILD note the reliance). Encode (inputs walk) vs decode
   (resolvers) halves are inputs-/resolvers-owned; this file only
   stashes the reverse map between them (F-SLOTS).
5. **Contracts restated in another medium.** [spec-039][spec-039]
   (Decisions 6/7/8/10/11/12 — projections, never owners); 87 oracles
   in [test-sets][test-sets] (all spelling expectations literally —
   independent oracles, listed per finding, never counted); the
   `serializermutation` glossary anchor + README consumer example
   (projections). Roles tagged per finding; no test reads from this
   file's definitions (the direct `_validate_serializer_nested_fields`
   unit calls pin raised messages literally).
6. **Enforcement by omission.** Family enumerated per rule:
   identifier gate (forms gates, serializer does not at HEAD —
   R-ident, ROUTED TO MAINTAINER); hook-invocation wrap (forms wraps,
   serializer does not — R-invoke, ROUTED TO MAINTAINER); deeper nested-map
   dunder hardening (top map hardened here, deeper maps raw in
   inputs — sweep note for the open `hostile-mapping-hardening`
   family, not a defect); coarse `get_serializer` hook (absent by
   recorded design — R-coarse); `check_permission` (inherited from
   base, correctly not overridden); `delete` (rejected per Decision
   10, oracle-pinned); `subsystem-clear-lifecycle` bus rows (none
   here — inputs owns the namespace rows, correctly); model-flavor
   discovery hook (no such hook — model inputs derive from the model,
   correctly absent from FAM-OWN).

### Enumeration

Instrument: every statement in `ast.Module.body` (21) plus every
statement in the `SerializerMutation` class body (14) = **35 members**.
The 12 import statements house 47 imported names; all 47 verified
referenced (AST `Name` census — only the `__future__`
`annotations` token is unreferenced, by construction). No `__all__`
(the folder norm per verified hook_context N3).

| # | Member | Home |
|---|---|---|
| 0 | module docstring | F-MECH (projection prose) |
| 1 | `from __future__ import annotations` | F-MECH |
| 2 | `from collections.abc import Mapping` | F-MECH |
| 3 | `from typing import Any` | F-MECH |
| 4 | `from rest_framework import serializers` | F-MECH (DRF posture) |
| 5 | `exceptions` (`ConfigurationError`, `_safe_arg_repr`) | F-MECH |
| 6 | `mutations.inputs.CREATE` | F-MECH |
| 7 | `mutations.sets` (16 names) | F-MECH |
| 8 | `_validate_permission_classes as _validate_mutation_permission_classes` | F-MECH |
| 9 | `utils.inputs.normalize_field_name_sequence` | F-MECH |
| 10 | `.inputs` (19 names) | F-MECH |
| 11 | `get_serializer_for_schema as _default_serializer_schema_fields` | F-MECH |
| 12 | `.serializer_converter` (2 names) | F-MECH |
| 13 | `_ALLOWED_SERIALIZER_META_KEYS` | F-KEYS |
| 14 | `_validate_schema_field_map` | F-SCHEMAMAP (+ hostile adoption facet) |
| 15 | `_checked_schema_field_map` | F-DET |
| 16 | `_serializer_input_shape_for` | F-SHAPETAIL |
| 17 | `_SERIALIZER_OPERATION_NESTED_WRITE_METHOD` | F-WRITEMAP |
| 18 | `_validate_serializer_nested_fields` | F-NESTVAL (+ hostile adoption facet) |
| 19 | `_assert_schema_source_ownership` | F-OWNWALK |
| 20 | `class SerializerMutation` | members below |
| 20.0 | class docstring | F-MECH (projection prose) |
| 20.1 | `input_module_path` | F-NS |
| 20.2 | `_input_field_specs` | F-SLOTS |
| 20.3 | `_injected_field_specs` | F-SLOTS |
| 20.4 | `_input_type_name` | F-SLOTS |
| 20.5 | `_resolve_model` | F-RESOLVEMODEL |
| 20.6 | `_validate_meta` | F-MATRIX |
| 20.7 | `get_serializer_for_schema` | F-HOOK (+ FAM-OWN facet) |
| 20.8 | `build_input` | F-BUILD |
| 20.9 | `input_type_name` | F-NAME |
| 20.10 | `get_serializer_kwargs` | F-HOOKS |
| 20.11 | `get_serializer_injected_data` | F-HOOKS |
| 20.12 | `get_serializer_save_kwargs` | F-HOOKS |
| 20.13 | `resolve_sync, resolve_async = resolver_seams(...)` | F-SEAMS |

35/35 homed; zero unassigned. Rejections R-* record the considered
unifications per finding (16 rows).

### Challenges

Each change posited against AUTHORITATIVE definitions only (consumers /
oracles / projections listed, never counted). All counts re-derived at
HEAD bytes.

| # | Rule | Change posited | Count |
|---|---|---|---|
| F-KEYS | serializer allowed-key arm | add a 5th serializer key | 1 (here; foundation 0) |
| F-KEYS | same | add a shared model-backed key | 0 here (1 at `MODEL_BACKED_WRITE_META_KEYS`) |
| F-SCHEMAMAP | schema-map validation | add a 7th value check | 1 (here) |
| F-SCHEMAMAP | same | change the aggregate message shape | 1 (here) |
| F-SCHEMAMAP | hardening facet | change the key-gate policy | joins open `hostile-mapping-hardening` (member) |
| F-DET | bind-read determinism | change the drift wording / window | 1 (here; computation 0, inputs-owned) |
| F-SHAPETAIL | shape build tail | change build-then-dedupe order | 1 (here) |
| F-WRITEMAP | nested write-method map | add a method axis value | 1 (here) |
| F-NESTVAL | nested opt-in validation | add a top-level gate | 1 (here) |
| F-NESTVAL | same | change empty-means-absent | 1 here for the top return (per-level rule inputs-owned; R-perlevel) |
| F-NESTVAL | hardening facet | change the entry/key-gate policy | joins open `hostile-mapping-hardening` (member) |
| F-OWNWALK | schema ownership walk | change the walk (phase/basis) | 1 (here; raise path 0, inputs-owned) |
| F-MATRIX | meta matrix arms | add/reword a serializer arm | 1 (here; spine bodies 0) |
| F-MATRIX | same | change a spine helper body | 0 here (1 upstream each) |
| F-RESOLVEMODEL | model resolution | change the attr chain | 0 here (1 at `resolve_meta_model`; this is the arg declaration) |
| F-HOOK | schema-hook default | change discovery fallback | 1 (here; discovery body 0, inputs-owned) |
| F-HOOK | own-snapshot read | change the stamp-timing fallback | 2 (here + forms default → FAM-OWN) |
| F-NS | input namespace binding | repoint the serializer namespace | 1 here (path value 0, inputs-owned) |
| F-SLOTS | bind slots | change a slot default | 1 per slot here (R-slotredecl: no plausible joint variation) |
| F-BUILD | build seam | change guard-before-dedupe order | 1 (here; tail/guard bodies 0) |
| F-NAME | name seam | change bound-or-derive | 1 (here; name computation 0) |
| F-HOOKS | hook defaults | change a default body / signature | 1 per hook here (each signature its own spec contract) |
| F-HOOKS | `Any` seam | annotate `hook_context` with the record | 1 here (3 annotations, one decision — R-importrecord) |
| F-SEAMS | seam bindings | change the delegate targets | 1 here (the arg declaration; bodies 0 at the factory) |
| F-MECH | module mechanics | change the DRF posture | 0 here (posture owned by leaf+root; this module covered by execution order) |

## Findings

Proof status key: every behavioral proof below is `static-reviewed`
(HEAD-byte body reads + permanent-oracle citations — sufficient for a
zero-edit file item; no ordering/transactional/async claim needs
execution). No `execution-deferred` proof is owed.

### F-KEYS — `serializer-allowed-meta-keys` (file-local)

- **Contract + variation.** Member 13: the serializer `Meta` allows
  exactly the shared `MODEL_BACKED_WRITE_META_KEYS` plus
  `serializer_class` / `optional_fields` / `injected_fields` /
  `nested_fields` (spec-039 Decision 6 — adds 4, drops `model` /
  `input_class` / `partial_input_class`). Varies only as the
  serializer arm (foundation changes count 0 here).
- **Sites + roles.** Definition: the union here (the 4-key arm).
  Foundation owner: [mutations-sets][mutations-sets]
  `::MODEL_BACKED_WRITE_META_KEYS` (converge, no row — consumer
  facet). Consumers: `_validate_meta`'s `reject_unknown_meta_keys`
  call; every `SerializerMutation` declaration. Oracles:
  `test_serializer_class_accepted_as_known_key`,
  `test_permission_classes_accepted_as_known_key`,
  `test_unknown_meta_key_raises`, `test_model_key_is_unknown`.
  Projection: module + `_validate_meta` docstrings, spec-039.
- **Challenges.** 5th serializer key → 1 (here); shared key → 0
  here (1 at the foundation).
- **Owner + lifetime.** Here (the serializer-`Meta` home; frozenset
  read per validation, nothing stored).
- **Behavioral proof.** `static-reviewed` (union body + oracle pins).
- **Structural gate.** The known-key oracles fail an arm drop (every
  declaration would typo-reject); the unknown-key oracles fail an
  arm widening. No bespoke gate owed (single owner + literal pins).
- **Freshness.** Target `2c4c4930`; foundation as fingerprinted.
- **R-keys** (rejection, fresh; CONVERGE with the verified forms-J2
  disjoint-matrix direction): one shared allowed-set for all write
  flavors. Difference: each flavor's matrix validates a different key
  vocabulary (Decision 6 disjoint matrices — the serializer matrix
  rejects `model`, the model matrix rejects `serializer_class`); a
  shared set would bless keys the matrix then mishandles. Trigger: the
  matrices merging onto one vocabulary.

### F-SCHEMAMAP — `serializer-schema-map-validation` (file-local)

- **Contract + variation.** Member 14: the hook-result validator —
  Mapping gate, guarded `items()` materialize, guarded per-entry
  unpack, exact-`str` key gate, `serializers.Field` value gate,
  guarded `field_name` read, guarded bound-name comparison,
  key==bound-name match, aggregate `ConfigurationError`. Varies per
  check (each check's wording/shape lives here).
- **Sites + roles.** Definition here (the check sequence + the aggregate).
  Precondition provider for the open
  `serializer-source-axis-normalization` family (both FAM records
  cite the key==bound-name arm — reliance noted, no transcription:
  a precondition, not a member). Consumers: `_validate_meta`,
  `_checked_schema_field_map`. Oracles: the 6 schema-hook reject
  tests (`..._at_class_creation`, `..._cannot_be_materialized`,
  `..._malformed_entries_and_unreadable_bound_names`,
  `..._hostile_bound_name_comparison_is_typed`,
  `..._str_subclass_key_with_hostile_hash`,
  `..._invalid_value_with_hostile_repr_is_typed`). Projection:
  member docstring (the `_hook_mapping` precedent citation).
- **Challenges.** 7th check / message reshape → 1 (here). The
  key-gate + materialize + unpack facet joins open
  `hostile-mapping-hardening` (adoption, below — same mechanism as
  resolvers member 50: Mapping gate + defensive materialize +
  exact-`str` key gate where downstream hashing consumes keys).
- **Owner + lifetime.** Here (pure per-call validation; returns a
  snapshot dict, nothing stored).
- **Behavioral proof.** `static-reviewed` (body + 6 literal oracles).
- **Structural gate.** The hostile-key/comparison oracles fail a
  gate removal (raw consumer exceptions would escape); the
  materialize oracle fails an unguarded `items()`. No bespoke gate
  owed. CONVERGE with verified J1 (shared-except-guard rejection):
  each `except` guard is locally owned — trigger-checked fresh (no
  shared guard primitive has appeared).
- **Freshness.** Target `2c4c4930`; resolvers `_hook_mapping`
  re-read at `0d302782`; oracles at `ff621ce8`.
- **R-ident** (axis-6 asymmetry; ROUTED TO MAINTAINER — no contract source):
  the forms basis (`_form_field_basis`) rejects non-identifier /
  keyword hook keys, this validator does not at HEAD. The hazard is
  shared (both flavors' keys become dataclass attrs rendered into an
  exec'd `__init__` via `build_strawberry_input_class` — a
  `"with space"` key detonates raw `SyntaxError` at finalization),
  and a hand-crafted hook map passes every check here. But no HEAD
  source (spec-039, glossary, owner prose, oracle) requires
  identifier keys on the serializer side — the stated contract is
  "keys are the bound field names". Not a defect, not a quiet close:
  Worker 0 surfaces it to the maintainer. Trigger: a spec row requiring
  identifier hook keys, or the maintainer ruling the form-side posture extends
  here (a concurrent worktree gate is in flight — judged at HEAD
  bytes only, neither relied on nor preempted).
- **R-invoke** (axis-6 asymmetry; ROUTED TO MAINTAINER — no contract source):
  the form flavor wraps the hook INVOCATION in a typed boundary
  (`_mutation_form_fields`); this file calls
  `cls.get_serializer_for_schema()` raw in `_validate_meta` and
  `_checked_schema_field_map`, so a raising override (forgotten
  `@classmethod`, body bug) escapes raw at class creation / bind.
  Both postures fail loud in the same phase — the difference is
  error-type diagnosis only — and no HEAD source picks one for the
  serializer hook. Not a defect, not a quiet close: Worker 0
  surfaces it to the maintainer. Trigger: a spec row extending the
  typed-invocation rule to serializer hooks, or the maintainer's ruling.

### F-DET — `serializer-bind-read-determinism` (file-local)

- **Contract + variation.** Member 15: the ONE guarded schema-hook
  read for the bind window — validate the map, and when
  `meta.schema_fingerprint` is present recompute it over the
  EFFECTIVE set with the SAME `meta.nested_fields` opt-in tree and
  raise on drift (nondeterministic-hook `ConfigurationError`).
  Varies as the window rule (which set, which tree, what raises).
- **Sites + roles.** Definition here (the read + the comparison).
  Computation owner: [rf-inputs][rf-inputs]
  `::serializer_schema_fingerprint` + `::resolve_effective_serializer_fields`
  (converge, no rows). Consumers: `build_input`, `input_type_name`
  (exactly 2 — closed census). Oracles:
  `test_nondeterministic_schema_hook_raises_at_bind`,
  `test_deterministic_schema_hook_binds_without_drift_error`,
  `test_input_type_name_runs_the_determinism_guard`.
  Projection: member docstring, spec-039 fingerprint rows.
- **Challenges.** Drift-wording / window change → 1 (here);
  fingerprint-axis change → 0 (inputs-owned).
- **Owner + lifetime.** Here (per-call read; the captured print
  lives on the sealed snapshot).
- **Behavioral proof.** `static-reviewed` (both consumers route
  through here — no unguarded second read exists package-wide).
- **Structural gate.** The nondeterminism oracle fails a check
  removal (a drifting hook would bind silently); the guard oracle
  fails an `input_type_name` bypass. No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; fingerprint bodies at `2410f380`.

### F-SHAPETAIL — `serializer-shape-build-tail` (file-local)

- **Contract + variation.** Member 16: build the input class via
  `build_serializer_input_class` (threading the validated `field_map`
  + `meta.nested_fields`), then dedupe through the inputs-owned
  cache protocol (`dedupe_serializer_input_shape` — sets must not
  poke the cache directly). Varies as the build-then-dedupe order.
- **Sites + roles.** Definition here (the two-call tail). Owners
  upstream ([rf-inputs][rf-inputs] build + dedupe — converge, no
  rows). Consumers: `build_input._build`, `input_type_name`
  (exactly 2 — closed census). Oracles: bind-materialize rows +
  `test_input_type_name_reads_bound_name_after_finalize`.
  Explicitly excluded: verified `generated-mutation-input-identity`
  (the MODEL descriptor scheme — this tail composes the serializer
  `SerializerInputShape` scheme, a different identity; no second
  site of either).
- **Challenges.** Order change → 1 (here); build/dedupe body
  changes → 0.
- **Owner + lifetime.** Here (per-call tail; cache lifetime owned
  by the inputs namespace rows).
- **Behavioral proof.** `static-reviewed` (tail body + both call
  sites + dedupe oracles).
- **Structural gate.** The per-declaration-guard oracle
  (`test_build_input_runs_required_guard_per_declaration`) fails a
  tail reorder that dedupes before guarding. No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; build/dedupe at `2410f380`.

### F-WRITEMAP — `serializer-nested-write-method-map` (file-local)

- **Contract + variation.** Member 17: `operation → DRF write
  method` (`create→create`, `update→update`) — the method whose
  override `Meta.nested_fields` requires (DRF's default asserts
  against nested writable data). Varies as the method contract.
- **Sites + roles.** Definition here (the dict). Sole consumer:
  `_validate_serializer_nested_fields`. Oracles:
  `test_validate_nested_fields_requires_create_override` (+ update
  twin) and the empty-mapping no-override test. Projection: member
  comment (the `raise_errors_on_nested_writes` rationale).
- **Challenges.** Third operation / method rename → 1 (here).
- **Owner + lifetime.** Here (module constant; read per validation).
- **Behavioral proof.** `static-reviewed` (dict + override oracles).
- **Structural gate.** The override-required oracles fail a map
  change that names a non-overridden method (DRF's raw
  `AssertionError` would escape the envelope). No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; [operations][operations] at
  `9fecef04` (excluded below).
- **R-ops** (rejection, fresh): fold the map into
  [operations][operations] descriptors as a third axis. Difference:
  the vocabulary module is DRF-free by layering (descriptors know
  input kinds, override attrs, id/data args, permission actions —
  no DRF method names); a `write_method` axis would drag DRF
  semantics into the soft-dependency-free core, reversing the
  dependency direction. Trigger: operations gaining flavor axes, or
  a second DRF-method consumer.

### F-NESTVAL — `serializer-nested-opt-in-validation` (file-local)

- **Contract + variation.** Member 18: `None→None`; mapping +
  value gates via the shared `require_*` pair; guarded materialize
  + unpack; exact-`str` key gate; schema-map membership; nested-field
  kind gate; empty-means-absent return; write-method-override
  requirement; `normalize_nested_serializer_configs` exit. Varies
  per gate.
- **Sites + roles.** Definition here (the gate sequence).
  Owners upstream for the shared pair + normalize + converter
  predicates (converge, no rows). Sole production consumer:
  `_validate_meta` (plus direct unit oracles — literal pins).
  Oracles: the 15 `test_validate_nested_fields_*` rows + cycle /
  deeper / stored-snapshot rows. Projection: member docstring.
- **Challenges.** New top gate → 1 (here); shared-pair wording →
  0. The entry/key hardening facet joins open
  `hostile-mapping-hardening` (adoption — same mechanism as
  F-SCHEMAMAP's facet: guarded materialize + unpack + exact-`str`
  gate before key-hashing consumers). Sweep note for the family
  item (not a defect — no oracle pins depth, and the top-level
  rationale's extension to depth is the family's scope call):
  deeper `nested_fields` maps inside configs iterate raw in
  `normalize_nested_serializer_configs` / `validate_nested_config_keys`
  (no guarded materialize/unpack/key gate) — candidate members for
  the family's package-wide mechanism sweep.
- **Owner + lifetime.** Here (per-call validation; returns the
  normalized tree stored on the snapshot).
- **Behavioral proof.** `static-reviewed` (sequence + 15 literal
  oracles). CONVERGE with verified J1 (except-guard locality),
  trigger-checked fresh.
- **Structural gate.** The midway-raising-iteration + malformed-entry
  + non-plain-key oracles fail a hardening removal. No bespoke gate
  owed.
- **Freshness.** Target `2c4c4930`; shared pair + normalize +
  `validate_nested_config_keys` at `2410f380`; predicates at `6652d092`.
- **R-perlevel** (rejection, fresh): unify with
  [rf-inputs][rf-inputs] `::validate_nested_config_keys`. Difference:
  this validates the TOP map against the SCHEMA basis + enforces the
  write-method override + normalizes; that rechecks EVERY level
  against the EFFECTIVE (narrowed) basis with no override concern.
  Different bases, different depths, different jobs — and this
  file's walker already composes that checker by name per level.
  Trigger: the bases collapsing to one, or the override gate moving
  per-level.

### F-OWNWALK — `serializer-schema-source-ownership-walk` (file-local)

- **Contract + variation.** Member 19: the recursive class-creation
  ownership check — `runtime_validated_data_fields` →
  `raise_writable_source_ownership_errors` at the root (supplied =
  effective + injected, defaults iff create) and every opted-in
  nested level (per-level key check, cycle/depth guard, child-map
  read, effective re-resolve, recurse). Root + nested share the one
  walker so wording cannot drift. Varies as the walk (phase, basis,
  supplied set).
- **Sites + roles.** Definition here (the walker). Raise-path +
  detection owners in [rf-inputs][rf-inputs] (converge — the F-WRITE
  row; no rows). Sole production caller: `_validate_meta` (+
  self-recursion). Oracles: the 6 class-creation collision/star
  tests + nested collision/star + read-only/narrowed no-break rows.
- **Challenges.** Walk/basis change → 1 (here); raise-wording →
  0 (inputs-owned).
- **Owner + lifetime.** Here (per-validation walk; nothing stored).
- **Behavioral proof.** `static-reviewed` (walker + collision
  oracles at both depths).
- **Structural gate.** The hidden-field/defaulted-collision oracles
  fail a supplied-set narrowing (silent last-write-wins would
  return). No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; raise path at `2410f380`;
  runtime twin at `0d302782` (excluded below).
- **R-runtime** (rejection, fresh): unify with resolvers
  `_assert_runtime_write_source_ownership`. Difference: this walks
  DECLARATIONS at class creation (schema map + config tree,
  supplied = effective + injected, no request data); that walks the
  LIVE serializer at request time (runtime `.fields` + spec tree,
  supplied = provided-data keys) to catch context-dependent fields
  schema discovery cannot see. Same raise path (already shared),
  irreconcilably different trees. Trigger: one walker parameterized
  over declaration-vs-live trees.

### F-MATRIX — `serializer-meta-matrix` (file-local)

- **Contract + variation.** Member 20.6: the class-creation matrix —
  unknown-key guard; presence → `Serializer` gate → `ModelSerializer`
  gate → no-model raise → model-class gate (all BEFORE resolution,
  so wrong-type/model-less is a clean error); non-delete operation;
  one-shot selector materialize; schema-hook discovery; narrowing
  fail-loud; `optional_fields` shape + name checks; `injected_fields`
  shape + writable-membership + narrowed-away checks;
  `select_for_update`; nested opt-in; ownership walk; permission
  classes; sealed snapshot incl. the effective-set fingerprint.
  Varies per arm (spine-body changes count 0 here).
- **Sites + roles.** Definition here (arm order + the 4 local
  raises: ModelSerializer gate, unknown/exposed injected, plus the
  threaded calls). Spine owners: 16+ composed helpers (converge, no
  rows — each verified/standing direction holds: FL1/FL3/FL4/FL9
  kit, F-NARROW/F-INJ/F-FP/F-WRITE/F-NEST machinery). Snapshot
  shape owner: `_ValidatedMutationMeta` (converge — sealed record;
  this matrix PRODUCES it). Consumers: the metaclass validation
  call, the bind, the resolver (via the snapshot). Oracles: ~40
  matrix rows (presence/type/model/operation/narrowing/optional/
  injected/lock/permission/fingerprint). Projection: member +
  module docstrings, spec-039 Decision 6/10/11.
- **Challenges.** New/reworded serializer arm → 1 (here); any
  spine-body change → 0 here (1 upstream each — verified by the
  direct-call composition, no wrapper re-spelling).
- **Owner + lifetime.** Here (per-class-creation validation; the
  snapshot is sealed at construction).
- **Behavioral proof.** `static-reviewed` (arm order + literal
  oracles per arm). The `operation == CREATE` defaults flag is a
  local policy read, not a second definition of any vocabulary rule.
- **Structural gate.** The per-arm reject oracles (delete, plain
  serializer, model-less, exposed-injected, non-bool lock) each fail
  their arm's removal. No bespoke gate owed.
- **Distinct behavior.** The split permission/lock calls (vs the
  `model_backed_permission_and_lock` pair — R-pair); the
  validate-then-store-raw precedent shared with the form flavor
  (snapshot stores normalized tuples, bind re-resolves).
- **Freshness.** Target `2c4c4930`; spine at `7800bd53`/`2410f380`.
- **R-merged** (rejection; CONVERGE with the verified forms-J2
  merged-`_validate_meta` direction on fresh evidence): one merged
  matrix for model/form/serializer. Difference re-derived: backing
  classes (`model` vs `form_class` vs `serializer_class`), operation
  vocabularies (delete vs never), narrowing bases (columns vs
  base_fields vs writable serializer fields), and serializer-only
  keys (`optional_fields`/`injected_fields`/`nested_fields`) — a
  merge needs a mode flag per arm, the exact shape principle 5
  forbids. Trigger: the backing/operation/narrowing axes collapsing.
- **R-pair** (rejection; CONVERGE with the owner-recorded
  separation): route the permission+lock calls through
  `model_backed_permission_and_lock`. Difference: this matrix
  interleaves five other key validations between the lock and the
  permission walk (nested/ownership must precede permissions in
  diagnostic order) — recorded at the owner's docstring ("the
  serializer flavor interleaves ... so it keeps calling the two
  primitives"). Trigger: the interleaving going away.

### F-RESOLVEMODEL — `serializer-model-resolution` (file-local)

- **Contract + variation.** Member 20.5: resolve the model from
  `Meta.serializer_class.Meta.model`, returning `None` for any
  missing link (the base raises the clean no-model error). One-line
  arg declaration over the shared chain.
- **Sites + roles.** Declaration here (`key="serializer_class"`,
  `meta_attr="Meta"`); chain owner `resolve_meta_model` (converge,
  no row). Consumers: `resolve_backed_model_or_raise` (via
  `_validate_meta`). Oracles: `test_modelserializer_with_no_meta_model_rejected`,
  `test_modelserializer_non_model_meta_model_raises_at_class_creation`.
- **Challenges.** Chain change → 0 here (1 upstream); arg change →
  1 (the declaration).
- **Owner + lifetime.** Declaration here; chain upstream. Per-call.
- **Behavioral proof.** `static-reviewed` (one line + no-model
  oracles). The form twin (`form_class`/`_meta`) is the same
  declaration shape, not a second definition (R-keys-class
  reasoning: declarations compose the owner; no plausible change
  moves the two arg pairs without moving the owner first).
- **Structural gate.** The no-model oracles fail an arg drift
  (wrong key/attr would resolve `None` for valid declarations).
- **Freshness.** Target `2c4c4930`; chain at `7800bd53`.

### F-HOOK — `serializer-schema-hook` (file-local)

- **Contract + variation.** Member 20.7: the Decision-7 default —
  read the OWN snapshot from `cls.__dict__` when stamped (bind
  window), else `cls.Meta.serializer_class` (class creation,
  before the stamp); delegate discovery to the module default.
  Varies as the fallback (which slot, which window, strictness).
- **Sites + roles.** Definition here (the fallback + delegation).
  Discovery-body owner: [rf-inputs][rf-inputs]
  `::get_serializer_for_schema` (converge, no row). Consumers:
  `_validate_meta`, `_checked_schema_field_map` (both windows);
  consumer overrides replace the default. Oracles:
  `test_get_serializer_for_schema_classmethod_override_drives_bind`,
  `test_subclass_redefining_serializer_validates_against_child_serializer`,
  the override-driven bind rows. Projection: member docstring (the
  MRO-hazard rationale), spec-039 Decision 7.
- **Challenges.** Fallback change → 1 (here); discovery-body
  change → 0. The own-snapshot-read facet counts 2 with the forms
  default (FAM-OWN, below).
- **Owner + lifetime.** Here (the Decision-7 hook home; per-call
  read + delegation, nothing stored).
- **Behavioral proof.** `static-reviewed` (fallback body + the
  subclass-override oracle proving the own-read).
- **Structural gate.** The subclass-redefining oracle fails an
  MRO-visible read (`cls._mutation_meta` would discover the
  parent's serializer). No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; discovery at `2410f380`;
  forms twin at `36ce80b4` (FAM-OWN).
- **R-formdisc** (rejection, fresh): unify discovery beyond the
  own-read (one shared discovery helper for form + serializer).
  Difference: the form path wraps the hook INVOCATION
  (`_mutation_form_fields`) + normalizes a basis; this path
  validates the hook RESULT (`_validate_schema_field_map`) +
  fingerprints for determinism. Invocation-vs-result are opposite
  typed boundaries with opposite helpers; only the 3-line
  own-snapshot fallback is shared (FAM-OWN). Trigger: the two
  boundaries converging on one helper shape.

### F-NS — `serializer-input-namespace` (file-local)

- **Contract + variation.** Member 20.1: this flavor's lazy `data:`
  ref resolves in `rest_framework.inputs` (overriding the `036`
  model default `mutations.inputs`). Varies as the binding (which
  namespace this flavor pins).
- **Sites + roles.** Declaration here (= the imported path
  constant). Path-value owner: [rf-inputs][rf-inputs]
  `::SERIALIZER_INPUTS_MODULE_PATH` (converge, no row). Consumers:
  the field factory's `_lazy_ref` + the bind materializer. Oracles:
  `test_bind_materializes_serializer_input_into_rest_framework_namespace`,
  `test_nested_input_materialized_in_ledger_after_finalize`.
- **Challenges.** Repoint this flavor → 1 (here); path-value
  change → 0 (inputs-owned).
- **Owner + lifetime.** Binding here; value upstream. Class
  attribute (no per-`Meta` dependence).
- **Behavioral proof.** `static-reviewed` (binding + namespace
  materialize oracles).
- **Structural gate.** The namespace-materialize oracle fails a
  binding drift (the lazy ref would resolve a model-column input).
  No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; path at `2410f380`.
- **R-path** (rejection; CONVERGE with verified inputs R-path on
  fresh evidence): unify the five `*_INPUTS_MODULE_PATH` names/
  values. Difference re-derived: each namespace needs a DISJOINT
  materialize ledger (the `SERIALIZER_` prefix keeps the serializer
  ledger apart from the model/form ledgers); the NAME variance
  (`SERIALIZER_INPUTS_MODULE_PATH` vs `INPUTS_MODULE_PATH` × 4) is
  incidental with no contract behind it. Trigger: ledgers merging.

### F-SLOTS — `serializer-bind-slots` (file-local)

- **Contract + variation.** Members 20.2–20.4: pre-bind slot
  declarations — `_input_field_specs` (reverse map, `None` until
  bind), `_injected_field_specs` (injected specs, `None` until
  bind), `_input_type_name` (bound name, `None` until bind). Each
  varies as its own stash contract.
- **Sites + roles.** Declarations here. Writers: `build_input`
  (all three, via the shared tail + direct stash). Readers: the
  resolvers decode/agreement guards (`mutation_cls._input_field_specs`,
  `_injected_field_specs`), `input_type_name` (own `_input_type_name`
  read) — all plain attribute access, verified: no `__dict__`
  reader of any slot package-wide. Oracles: bind-stash rows
  (decode + agreement suites exercise the stashes).
  Explicitly excluded: verified `mutation-input-reverse-map` (the
  MODEL remap scheme — these stash `InputFieldSpec` lists, a
  different scheme; resolvers J6 direction holds).
- **Challenges.** One slot's default/shape → 1 here per slot; no
  plausible change moves slots jointly (R-slotredecl).
- **Owner + lifetime.** Declared here; values stashed at bind on
  the concrete class; cleared per finalize lifecycle upstream.
- **Behavioral proof.** `static-reviewed` (declarations + writer/
  reader census + bind oracles).
- **Structural gate.** The decode/agreement oracles fail a stash
  drop (unbound `None` would crash the decode). No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; readers at `0d302782`;
  sibling declarations at `7800bd53`/`36ce80b4` (excluded below).
- **R-slotredecl** (rejection, fresh): delete the `_input_field_specs`
  redeclarations (base + 2 form + this = 4 identical lines) as one
  rule. Difference: (a) no plausible variation moves them jointly —
  the pre-bind default has no variation axis (rename moves 10+
  readers regardless; the 2-line saving is not a change obligation);
  (b) the sites are not uniformly redundant — the plain-form twin
  is LOAD-BEARING (no `DjangoMutation` inheritance) while the two
  model-backed twins document per-flavor keying; (c) the base
  comment blesses the pattern ("subclasses overwrite ... with their
  own flavor map"). Trigger: a slot-shape change that must move all
  four declarations, or the base blessing retiring.

### F-BUILD — `serializer-build-input` (file-local)

- **Contract + variation.** Member 20.8: the seam override —
  guarded hook read; injected-specs stash; effective-names resolve;
  per-declaration create-required guard (BEFORE dedupe, injected
  the only subtraction); build via F-SHAPETAIL; materialize +
  reverse-map stash via the shared tail; `_input_type_name` stash.
  Varies as the seam order (guard-before-dedupe is load-bearing).
- **Sites + roles.** Definition here (the order + the `_build`
  closure). Owners upstream: `build_and_stash_input` (tail),
  `guard_create_required_serializer_fields` (guard),
  `materialize_serializer_input_class` (materialize) — converge, no
  rows. Consumer: the phase-2.5 drain (`bind_write_declarations`
  calls `mutation_cls.build_input(meta, object_type)`). Oracles:
  the create-guard trio (`..._fires_through_build_input`,
  `..._override_no_longer_waives...`, `..._per_declaration`) +
  materialize/bind/idempotency rows. Projection: member docstring
  (the `cached_build_input` non-routing rationale — recorded at
  BOTH owners).
- **Challenges.** Order change → 1 (here); tail/guard/materialize
  body changes → 0.
- **Owner + lifetime.** Here (per-bind build; stashes land on the
  concrete class).
- **Behavioral proof.** `static-reviewed` (order + guard-trio
  oracles, incl. the waiving-first poisoning shape).
- **Structural gate.** The per-declaration oracle fails a
  guard-after-dedupe reorder (a cached shape would suppress a later
  guard). No bespoke gate owed.
- **Distinct behavior.** The `Meta.injected_fields`-only waiver
  (vs the form coarse hook-override waiver — recorded separations
  at `_hook_overridden`, `_form_kwargs_overridden`, and here).
- **Freshness.** Target `2c4c4930`; tail at `7800bd53`; guard +
  materialize at `2410f380`; drain at `7800bd53`.
- **R-cached** (rejection; CONVERGE with the both-sides-recorded
  separation): route through `cached_build_input`. Difference: that
  helper keys pre-build (form: class+op+names known upfront) while
  the serializer key is the POST-build `SerializerInputShape`
  descriptor — forcing this path through it builds the shape twice.
  Recorded at the helper's docstring AND here. Trigger: a pre-build
  serializer cache key.

### F-NAME — `serializer-input-name` (file-local)

- **Contract + variation.** Member 20.9: the name seam — the SAME
  guarded hook read as `build_input` (determinism enforced even
  when the bound name is stashed); bound name if present, else the
  descriptor `type_name` via F-SHAPETAIL. No second name deriver.
  Varies as the bound-or-derive rule.
- **Sites + roles.** Definition here (the read + the branch).
  Name-computation owners upstream (descriptor / stashed `__name__`
  — converge, no rows). Consumers: the field factory's lazy `data:`
  ref; direct seam callers. Oracles:
  `test_input_type_name_runs_the_determinism_guard`,
  `test_input_type_name_reads_bound_name_after_finalize`.
- **Challenges.** Bound-or-derive change → 1 (here); name-template
  change → 0 (generator-owned). The direct
  `NON_DELETE_OPERATION_INPUT_KIND[meta.operation]` index is safe:
  `meta` is the sealed snapshot (create/update-only by
  construction) — the base's `.get()`+typed-reject exists for the
  model flavor's delete, which never reaches this seam.
- **Owner + lifetime.** Here (per-call derivation; the stash is
  bind-written).
- **Behavioral proof.** `static-reviewed` (branch + both oracles).
- **Structural gate.** The determinism-guard oracle fails a read
  bypass (an unguarded name could disagree with the bound class).
  No bespoke gate owed.
- **Freshness.** Target `2c4c4930`.
- **R-formname** (rejection, fresh): unify with the form
  pre-build name derivation (`form_input_type_name` over effective
  + full sets). Difference: the form name is computable pre-build
  from (class, op, names); the serializer name needs the POST-build
  descriptor (hook-varying specs + `optional_fields` fold into the
  identity). Different phases, different keys. Trigger: a
  pre-build serializer name key.

### F-HOOKS — `serializer-construction-hooks` (file-local)

- **Contract + variation.** Members 20.10–20.12: the three
  Decision-7/8 hook defaults — `(self, info, *, data, hook_context)`
  each (spec-pinned shape); kwargs default returns
  `construction_kwargs(data=data)` (constructor-only, no
  `instance`); injected-data and save-kwargs defaults return `{}`.
  Each signature is its own spec contract; each body varies alone.
- **Sites + roles.** Definitions here (3 signatures + 3 bodies).
  Framework-rule owners in [rf-resolvers][rf-resolvers] (reserved
  merge, exact-match injection, save-kwarg guards — converge, no
  rows). Shared clause owner: `construction_kwargs` (converge, no
  row). Consumers: the 3 production call sites (resolvers
  865/926/2320 — closed census) + consumer overrides (2 test
  overrides + 1 in-tree: `UpdateBookSubstitutingInstance`).
  Oracles: `test_default_serializer_mutation_instance_hook_methods`
  (all three defaults, literal pins) + the override-driven guard
  rows. Projection: member docstrings (framework-owned invariants),
  spec-039 Decision 7/8, glossary.
- **Challenges.** One default body / one signature → 1 here each
  (adding a parameter to one hook moves only that hook — separate
  contracts). The `hook_context: Any` seam (carried note from File
  `rest_framework/hook_context.py`, adjudicated fresh): ONE decision
  here — all 3 annotations stay `Any` (file-local, below).
- **Owner + lifetime.** Here (the hook-default home; per-call
  bodies, nothing stored).
- **Behavioral proof.** `static-reviewed` (bodies + literal default
  pins + call-site census). Annotations are behavior-free (the
  resolver passes the record regardless).
- **Structural gate.** The defaults oracle fails a body change
  (a `data`-rewriting or `instance`-injecting default would break
  the constructor-only contract). No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; call sites at `0d302782`;
  record defs at `646377d9` (CLEAN).
- **Carried-note adjudication (`hook_context: Any`).** FILE-LOCAL:
  keep the seam untyped. (a) The defaults never touch the record
  (`del`-ignored) — an import would serve annotation only. (b)
  Consistent with the other opaque hook params (`info: Any`,
  `data: Any` in all 3 signatures + the form hooks +
  `check_permission`). (c) No import edge to a module whose values
  this module never reads (hook_context stays a resolver-side leaf
  import). (d) No second site defines this — each hook signature is
  its own spec contract (form hooks have no `hook_context` param at
  all). Runtime receives the record regardless, so no contract row
  breaks either way.
- **R-importrecord** (rejection, fresh — the considered alternative):
  import `SerializerHookContext` and annotate the 3 params.
  Difference: annotation-only precision vs the seam's deliberate
  opacity (no cycle would result — the leaf imports nothing — but
  no reader needs it either). Trigger: the defaults starting to
  read the record, or a type-checker-driven consumer need.
- **R-coarse** (rejection; CONVERGE with the module-docstring
  recorded separation): add a coarse `get_serializer` constructor
  hook mirroring the form `get_form`. Difference: the serializer's
  framework-owned invariants (`partial`, authorized-actor
  `context["request"]`) cannot be entrusted to a consumer
  constructor — recorded in the module docstring. Trigger: those
  invariants becoming consumer-delegable.

### F-SEAMS — `serializer-resolver-seam-bindings` (file-local)

- **Contract + variation.** Member 20.13: bind
  (`resolve_serializer_sync`, `resolve_serializer_async`) from
  `django_strawberry_framework.rest_framework.resolvers` as this
  class's `resolve_sync`/`resolve_async`. Varies as the arg
  declaration (which module, which entries).
- **Sites + roles.** Declaration here. Body/factory owner:
  `resolver_seams` (converge, no row — verified FL10 direction;
  the function-local import keeps this module free of a load-time
  resolver edge, the forms precedent). Consumers: the field
  factory's `_resolve` dispatch (via `_has_mutation_protocol`).
  Oracles: routing-identity tests + the live serializer-mutation
  suites (transitive ride of `shared-write-skeleton` — converge,
  no row).
- **Challenges.** Retarget this flavor → 1 (the declaration);
  seam-body change → 0 (factory-owned, 8 bodies single-sited).
- **Owner + lifetime.** Declaration here; bodies at the factory.
  Class-body assignment (both land in the class `__dict__`).
- **Behavioral proof.** `static-reviewed` (one call + routing
  oracles).
- **Structural gate.** The routing-identity oracles fail a
  declaration drop (inheritance vs distinct-call identities).
  No bespoke gate owed.
- **Freshness.** Target `2c4c4930`; factory at `7800bd53`.

### F-MECH — `serializer-module-mechanics` (file-local)

- **Contract + variation.** Members 0–12 + 20.0: the module
  docstring (Decision-6 riding statement, matrix summary, guard
  posture, seam/hook statements — projection prose, verified
  against the bodies claim by claim); the 12-statement import block
  (47 names, all referenced — totality census above); the class
  docstring (Decision-6 riding projection). The DRF posture: this
  module top-imports `rest_framework.serializers` with NO
  `require_drf()` call — covered by parent-`__init__` execution
  order (verified J1 direction).
- **Sites + roles.** Mechanics here. Guard owners: leaf
  `require_drf()` + root `__getattr__` routing (converge — covered
  module, no row). Every import is a consumer facet of its finding
  (F-KEYS…F-SEAMS); totality owned here. Oracles:
  `test_serializer_mutation_resolves_through_root_getattr`,
  `test_serializer_mutation_not_in_all` (posture pins).
- **Challenges.** Posture change → 0 here (leaf+root owned);
  prose/body drift → 1 (the docstring is corrected to the body,
  never vice versa — all riding/matrix/seam claims re-verified
  against HEAD bodies in this pass).
- **Owner + lifetime.** Prose + imports here; guard behavior
  upstream. Import-time execution.
- **Behavioral proof.** `static-reviewed` (import census 47/47 +
  posture pins + prose-vs-body re-read).
- **Structural gate.** The root-resolution oracles fail a posture
  break (a DRF-absent import crash outside the guard). No bespoke
  gate owed.
- **Freshness.** Target `2c4c4930`; leaf `45cf7b63` + root
  `0ef72601` (both CLEAN).
- **R-guardcalls** (rejection; CONVERGE with verified
  `rest-framework-per-module-guard-calls` on fresh evidence):
  per-module `require_drf()` calls. Trigger re-checked fresh: no
  submodule is reachable without executing the parent `__init__`
  (no such import shape exists in Python) and the production
  `require_drf(` census is still exactly 2 (root + leaf line 62).
  Difference stands: enforcement is execution order, not calls.

### FAM-OWN — `mutation-discovery-own-snapshot-read` (NEW FAMILY for Worker 0)

- **Contract + variation.** Discovery defaults read the class's OWN
  `_mutation_meta` snapshot from `cls.__dict__` when stamped, else
  fall back to the live `Meta` declaration — because class
  validation runs BEFORE the metaclass stamps the snapshot (one
  window reads live, every later call reads frozen-own). Varies as
  the stamp-timing fallback (slot, key, missing strictness).
- **Sites + roles.** *Definitions (2)*, verified at HEAD bytes:
  [forms-sets][forms-sets] `::_default_mutation_get_form_fields`
  (`cls.__dict__.get("_mutation_meta")` → snapshot `form_class`
  via getattr-defaults, else live-`Meta` chain, else typed raise)
  and member 20.7 here (`cls.__dict__.get("_mutation_meta")` →
  `meta.serializer_class`, else `cls.Meta.serializer_class`).
  Shared core: the 3-line own-or-live fallback over the same
  stamp-timing fact (both docstrings state it). *Fair differences
  for the family item:* fallback strictness (form: getattr chain +
  typed raise on unresolvable; serializer: direct access, safe by
  validation order — `_validate_meta` gates presence before any
  hook read) and hazard emphasis (form: post-declaration `Meta`
  mutation; serializer: subclass-MRO inheritance). *Excluded on
  body strength:* `mutations/fields.py:114` (presence-only boolean,
  no value read, no fallback); member 20.9's `_input_type_name`
  own-read (bind-stash job, no `Meta` fallback, no timing hazard);
  `types/base.py:625` (reads `Meta` itself, not the snapshot);
  patch-module `__dict__` descriptor reads (different domain).
  Population closed: `__dict__.get("_mutation_meta")` value reads
  with fallback = exactly these 2 package-wide. *Consumers:* both
  flavors' class-creation validation + bind reads. *Oracles:*
  `test_subclass_redefining_serializer_validates_against_child_serializer`
  (this side) + the forms frozen-snapshot rows (form side) — pin
  VALUES, never the fallback spelling.
- **Challenges.** Metaclass stamp-timing change (stamp before
  validation, slot rename) → **2** (both fallbacks move; presence
  checks and post-stamp plain reads follow as consumers).
- **Owner + lifetime.** Candidate: [mutations-sets][mutations-sets]
  (owns the metaclass factory + the snapshot record; both flavors
  already import from it — no dependency reversal). No stored
  derivation (per-call read). The family item decides.
- **Migration (sketch for the family item, not this file item).**
  A `snapshot_or_meta_backing(cls, slot, key)`-shaped helper at the
  owner returning the backing class or `None`; form keeps its typed
  raise on `None`, serializer keeps direct-index-equivalent
  behavior under its validation order. Oracles stay.
- **Distinct behavior.** Missing-value strictness stays per-flavor
  (typed-raise vs validation-ordered direct) unless the family item
  finds one posture serves both windows.
- **Behavioral proof.** `static-reviewed` for the COUNT (both
  bodies + the closed population census at HEAD bytes).
  Consolidation proof owed by the family item.
- **Structural gate.** Owed by the family item (a two-site fallback
  gate with its negative control: a hand copy passing the
  subclass-override oracles).
- **Coupling.** F-HOOK (this side's host) + the forms R7 host.
- **Freshness.** This side `2c4c4930`; forms side `36ce80b4`;
  fields.py presence-check `d4edcbb7` (excluded).

### ADOPT — `hostile-mapping-hardening` (adoption into the OPEN family)

Following the verified resolvers-C11 precedent (member + coverage
append, family item decides the owner with this member in its sweep):

- **Contract.** Mappings crossing a trust boundary are type-gated,
  materialized defensively, and key-gated where downstream code
  hashes them — never a raw consumer exception past the boundary.
- **Sites + roles.** Owner: TBD by the family item (currently
  `utils/policies.py`, `conf.py`, `types/base.py`,
  `rest_framework/resolvers.py`). This target's role: MEMBER —
  F-SCHEMAMAP's facet (Mapping gate + guarded `items()` materialize
  + guarded unpack + exact-`str` key gate before the snapshot
  dict-set and bound-name comparisons) plus F-NESTVAL's facet
  (guarded materialize + unpack + exact-`str` key gate before
  `field_map.get()` and the normalized dict-set). Same mechanism
  as the resolvers member, fresh evidence: both facets exist
  precisely because the gated maps feed key-hashing consumers.
  Family sweep note (rides with the adoption, not a defect): deeper
  `nested_fields` maps iterate raw in inputs — candidate members
  for the sweep (F-NESTVAL).
- **Worker 0 transcription:** append
  `django_strawberry_framework/rest_framework/sets.py` to the
  `hostile-mapping-hardening` index row's Files covered. No new
  family. Proof `static-reviewed` (both facet bodies + 21 oracle
  pins for non-mapping / unmaterializable / malformed-entry /
  non-string-key returns).
- **Challenges.** Gate-policy change → moves with the family owner
  once chosen.
- **Freshness.** Target `2c4c4930`; resolvers member at `0d302782`.

## Defects

None filed. Candidates examined and cleared on-record (not defects):

- **N1 — deeper nested-map dunder hardening.** Deeper
  `nested_fields` maps iterate raw (see F-NESTVAL sweep note). Not
  filed: no HEAD oracle pins depth behavior, and whether the
  top-level rationale extends to depth is the open family's scope
  call — the family sweep adjudicates with the full mechanism
  census. No contract row breaks today.
- **N2 — direct dict indexing on operation maps**
  (`NON_DELETE_OPERATION_INPUT_KIND[...]`,
  `_SERIALIZER_OPERATION_NESTED_WRITE_METHOD[...]`). Not filed: the
  indexed values come from the sealed snapshot / validated locals
  (create/update-only by construction) — the base's `.get()`+typed
  reject exists for the model flavor's delete, which never reaches
  these seams. Safe by verified seal.
- **N3 — raw `getattr` reads on consumer `Meta`.** Not filed:
  package-wide posture (every flavor's `Meta` reads are raw
  getattr); changing it is a package-wide decision, and concurrent
  hunt work owns that migration. Out of scope, left alone.
- **N4 — `del (primary_type)` paren form.** Cosmetic idiom, not a
  rule; no home owed, no defect.

## Pending execution

None. No `proof:` entries (all findings `static-reviewed` against
HEAD bytes + permanent oracles); no `gate:` entries. Sharded/Postgres
cells are inapplicable by construction: the target defines
class-creation validation + finalize-time input seams with no database,
alias, or dialect decision (no queryset, no `using`, no backend probe
— verified by body read).

## Judgment

Zero-edit file item: 35/35 members homed (17 file-local rows),
1 new holding family (`mutation-discovery-own-snapshot-read`,
count 2, population closed), 1 adoption into open
`hostile-mapping-hardening` (coverage append), 16 rejections (2
CONVERGE-routed to the maintainer with no contract source, 7 fresh, 7 CONVERGE
with standing directions on fresh evidence), 0 defects. The file is a
clean Decision-6 rider: every shared spine is composed by name with
zero re-spelling (verified call by call), and every serializer-only
rule has exactly one definition. The two maintainer routes (identifier gate,
invocation wrap) are the only open contract questions; both fail loud
today and differ only in error-type diagnosis, so neither blocks.

## Index rows for Worker-0

Worker 0 transcribes verbatim; Worker 0 authors nothing. 34 rows
(17 file-local + 1 open family + 16 rejected) plus 1 coverage append.

| `serializer-allowed-meta-keys` | `django_strawberry_framework/rest_framework/sets.py::_ALLOWED_SERIALIZER_META_KEYS` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-schema-map-validation` | `django_strawberry_framework/rest_framework/sets.py::_validate_schema_field_map` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-bind-read-determinism` | `django_strawberry_framework/rest_framework/sets.py::_checked_schema_field_map` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-shape-build-tail` | `django_strawberry_framework/rest_framework/sets.py::_serializer_input_shape_for` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-nested-write-method-map` | `django_strawberry_framework/rest_framework/sets.py::_SERIALIZER_OPERATION_NESTED_WRITE_METHOD` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-nested-opt-in-validation` | `django_strawberry_framework/rest_framework/sets.py::_validate_serializer_nested_fields` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-schema-source-ownership-walk` | `django_strawberry_framework/rest_framework/sets.py::_assert_schema_source_ownership` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-meta-matrix` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._validate_meta` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-model-resolution` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._resolve_model` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-schema-hook` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_for_schema` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-input-namespace` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.input_module_path` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-bind-slots` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._input_field_specs` + `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._injected_field_specs` + `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._input_type_name` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-build-input` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.build_input` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-input-name` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.input_type_name` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-construction-hooks` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_kwargs` + `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_injected_data` + `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_save_kwargs` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-resolver-seam-bindings` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.resolve_sync` + `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.resolve_async` | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `serializer-module-mechanics` | `django_strawberry_framework/rest_framework/sets.py` (module + class docstrings, import block) | `django_strawberry_framework/rest_framework/sets.py` | File `rest_framework/sets.py` | file-local |
| `mutation-discovery-own-snapshot-read` | TBD by family item (candidates: `django_strawberry_framework/mutations/sets.py` via a snapshot-or-meta helper, or the forms default) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/forms/sets.py` | Family `mutation-discovery-own-snapshot-read` | open |
| `serializer-allowed-keys-vs-shared-set` | `django_strawberry_framework/rest_framework/sets.py::_ALLOWED_SERIALIZER_META_KEYS` (rejection recorded here; CONVERGE with verified forms-J2 disjoint-matrix direction on fresh evidence) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-hook-key-identifier-gate` | `django_strawberry_framework/forms/inputs.py::_form_field_basis` (asymmetry recorded here; ROUTED TO MAINTAINER — no contract source; trigger: a spec row requiring identifier hook keys, or the maintainer ruling the form-side posture extends here) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/sets.py` | rejected |
| `serializer-hook-invocation-typed-wrap` | `django_strawberry_framework/forms/sets.py::_mutation_form_fields` (asymmetry recorded here; ROUTED TO MAINTAINER — no contract source; trigger: a spec row extending the typed-invocation rule to serializer hooks, or the maintainer's ruling) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-write-method-vs-operations-vocabulary` | `django_strawberry_framework/rest_framework/sets.py::_SERIALIZER_OPERATION_NESTED_WRITE_METHOD` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/mutations/operations.py` | File `rest_framework/sets.py` | rejected |
| `serializer-nested-validation-vs-per-level-keys` | `django_strawberry_framework/rest_framework/sets.py::_validate_serializer_nested_fields` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/sets.py` | rejected |
| `serializer-ownership-schema-vs-runtime-walk` | `django_strawberry_framework/rest_framework/sets.py::_assert_schema_source_ownership` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/sets.py` | rejected |
| `serializer-matrix-vs-merged-matrix` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._validate_meta` (rejection recorded here; CONVERGE with verified forms-J2 on fresh evidence) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-permission-lock-split-vs-pair` | `django_strawberry_framework/mutations/sets.py::model_backed_permission_and_lock` (rejection recorded here; CONVERGE with the owner-recorded separation on fresh evidence) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/mutations/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-discovery-vs-form-discovery` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_for_schema` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-namespace-vs-shared-path` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.input_module_path` (rejection recorded here; CONVERGE with verified inputs R-path on fresh evidence) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/orders/inputs.py` | File `rest_framework/sets.py` | rejected |
| `serializer-slot-redeclaration-vs-single` | `django_strawberry_framework/mutations/sets.py::DjangoMutation._input_field_specs` (rejection recorded here; fresh, no-variation + load-bearing-twin + base-blessing) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-build-vs-cached-build-input` | `django_strawberry_framework/mutations/sets.py::cached_build_input` (rejection recorded here; CONVERGE with the both-sides-recorded separation on fresh evidence) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/mutations/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-name-vs-form-name-derivation` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.input_type_name` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-hook-context-record-annotation` | `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_kwargs` (rejection recorded here; fresh adjudication of the carried hook_context: Any seam note — keep untyped) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/hook_context.py` | File `rest_framework/sets.py` | rejected |
| `serializer-no-coarse-constructor-hook` | `django_strawberry_framework/rest_framework/sets.py` (rejection recorded here; CONVERGE with the module-docstring recorded separation on fresh evidence) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/forms/sets.py` | File `rest_framework/sets.py` | rejected |
| `serializer-per-module-guard-calls` | `django_strawberry_framework/rest_framework/__init__.py::require_drf` (rejection recorded here; CONVERGE with verified rest-framework-per-module-guard-calls on fresh evidence — trigger re-checked, still unfired) | `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/__init__.py` | File `rest_framework/sets.py` | rejected |

Coverage append (no new row — Worker 0 appends to the existing open
row): add `django_strawberry_framework/rest_framework/sets.py` to the
`hostile-mapping-hardening` index row's Files covered (F-SCHEMAMAP +
F-NESTVAL hardening facets adopted; family item decides the owner with
this member in its sweep).

## Families

Worker 0 must add one `## Families` item:

- [ ] Family `mutation-discovery-own-snapshot-read` — [dry-rule-mutation-discovery-own-snapshot-read.md](dry-rule-mutation-discovery-own-snapshot-read.md) — no artifact on disk; undispatched

No family item for the `hostile-mapping-hardening` adoption (row
exists, open — coverage append only).

## Independent verification (Worker-2)

Run `0.0.15 2026-09-28-7`, HEAD `0c0537e2`. Target traced at HEAD
bytes (`git show HEAD:django_strawberry_framework/rest_framework/sets.py`,
blob `2c4c4930`, 1013 lines; worktree `2b88fe58`, 1000 lines, concurrent
hunt/maintainer dirt left alone). This section's part A was written
before opening `## Findings`; part B reconciles after reading them.

### Part A — own trace (pre-findings)

Instrument: `ast.Module.body` statements (21: docstring + 12 imports +
2 module constants + 5 module functions + 1 class) plus
`SerializerMutation` class-body statements (14: docstring + 4 slots +
8 methods + 1 seam assignment) = 35 members. Import census: 47 names,
all referenced except the `__future__` `annotations` token (verified by
`ast.Name` walk). No `__all__` anywhere in `rest_framework/` (verified
per module at HEAD; the `inputs.py` hits are `"__all__"` selector prose).

Sites, roles, counts per posited change, homes I would choose (all
re-derived at HEAD bytes; consumers/oracles/projections listed, never
counted):

- Module + class docstrings, 12-import block: projection prose +
  wiring. DRF posture (leaf `import serializers`, no `require_drf()`
  call): 0 here — posture owned by the root `__getattr__` + the leaf
  `require_drf`; the execution-order coverage is the known prior
  `rest-framework-per-module-guard-calls` rejection. Home: one
  file-local mechanics row.
- `_ALLOWED_SERIALIZER_META_KEYS`: declaration of the 4 serializer
  arms over the upstream-owned `MODEL_BACKED_WRITE_META_KEYS`
  (`mutations/sets.py:91`). Add a 5th serializer key: 1, here. Add a
  shared key: 0 here, 1 upstream. Parallel unions are per-flavor
  declarations (model, modelform, plainform, serializer). Home:
  file-local + reject the merged-set unification.
- `_validate_schema_field_map`: the schema-hook result validator (6
  value checks + aggregate message). Add a 7th check / reshape the
  message: 1, here. Its entry-materialize + plain-`str` key gates cite
  the resolver-tier `_hook_mapping` precedent
  (`rest_framework/resolvers.py:: _hook_mapping`, Mapping check +
  materialize guard + `type(key) is not str` gate, 3 call sites) —
  same rule, second member. Home: file-local for the validator, adopt
  the hardening facets into open `hostile-mapping-hardening`.
- `_checked_schema_field_map`: the one guarded bind read + drift check.
  Change wording/window: 1, here; the fingerprint computation is
  inputs-owned (0 here). Home: file-local.
- `_serializer_input_shape_for`: build-then-dedupe tail over
  inputs-owned bodies. Change the order: 1, here. Home: file-local.
- `_SERIALIZER_OPERATION_NESTED_WRITE_METHOD`: operation→DRF-method
  table. Add an axis value: 1, here. Distinct axis from the
  operations-owned `NON_DELETE_OPERATION_INPUT_KIND`
  (`mutations/operations.py:109`, input-kind vocabulary). Home:
  file-local + reject the operations-vocabulary merge.
- `_validate_serializer_nested_fields`: top-level opt-in validation
  (container + entry + key + config + membership + nested-ness +
  override requirement + empty-means-absent). Add a top gate: 1, here.
  Empty-means-absent: 1 here for the top return; the per-level rule is
  inputs-owned (`validate_nested_config_keys`). Entry/key gates join
  the hostile family as above. Home: file-local + adopt + reject the
  per-level merge.
- `_assert_schema_source_ownership`: schema-phase recursive walk over
  the schema field map + opt-in configs. Change phase/basis: 1, here;
  the raise path (`runtime_validated_data_fields` →
  `raise_writable_source_ownership_errors`) is inputs-owned (0 here).
  The runtime twin (`resolvers.py::_assert_runtime_write_source_ownership`)
  walks different inputs (live `serializer.fields` + `data` + specs) in
  a different phase over the same shared raise path. Home: file-local +
  reject the schema/runtime merge.
- `SerializerMutation._resolve_model`: one-arg declaration over shared
  `resolve_meta_model`. Change the attr chain: 0 here, 1 upstream.
  Home: file-local (declaration, not a definition of the chain).
- `SerializerMutation._validate_meta`: the serializer matrix. Add or
  reword a serializer arm: 1, here; every spine body 0 here (1
  upstream each). The permission/lock split (primitives called
  separately with nested-fields + ownership interleaved) is the
  owner-recorded separation in
  `mutations/sets.py::model_backed_permission_and_lock`'s own
  docstring. Home: file-local + reject the merged-matrix and
  permission-lock-pair unifications.
- `SerializerMutation.get_serializer_for_schema`: hook default. Change
  the discovery fallback: 1, here; the discovery body 0 here
  (inputs-owned `get_serializer_for_schema`). Its
  `cls.__dict__.get("_mutation_meta")` own-snapshot read twins
  `forms/sets.py::_default_mutation_get_form_fields:172` exactly (same
  stamp-timing fallback: own snapshot else live `Meta`). Change the
  fallback: 2. Population sweep for `__dict__.get("_mutation_meta")`:
  only those two plus `mutations/fields.py:114`, which is a different
  contract (field-factory concreteness guard: own snapshot AND ledger
  entry) and correctly excluded; `sets.py:898`
  (`__dict__.get("_input_type_name")`) is a bound-name cache read, also
  a different contract. Model flavor has no discovery hook (inputs
  derive from the model) — correctly absent. Home: file-local for the
  default, NEW FAMILY for the own-snapshot read (count 2, population
  closed), reject the discovery-vs-discovery merge (different bodies).
- `SerializerMutation.input_module_path`: namespace binding. Repoint:
  1 here for the binding, 0 for the path value (inputs-owned). Four
  parallel bindings (model, 2 form, serializer) each name their own
  namespace — no shared declaration to consolidate. Home: file-local +
  reject.
- The three bind slots: 1 default each, here. `_injected_field_specs`
  / `_input_type_name` are serializer-only. `_input_field_specs` is
  re-declared `= None` on 4 classes (model base + 2 form + serializer);
  readers are MRO-tolerant (`mutation_cls._input_field_specs`,
  `getattr(..., None)`), writers always land on the concrete class, and
  the base comment blesses the overwrite — each declaration initializes
  its own class's binding state with no plausible joint variation.
  Home: file-local + reject the single-declaration unification (my one
  soft spot — see part B).
- `SerializerMutation.build_input`: guard-before-dedupe ordering +
  shared-tail composition. Change the order: 1, here; tail/guard bodies
  0 here. The `cached_build_input` bypass is recorded on BOTH sides
  (the helper's docstring names this module's descriptor-keyed reason;
  this seam's docstring preserves the discipline inline). The
  waiver-vs-`injected_fields` split is likewise recorded at both
  owners (forms waives on construction-hook override; here overrides
  never suppress — only `Meta.injected_fields` subtracts). Home:
  file-local + reject both merges.
- `SerializerMutation.input_type_name`: bound-or-derive seam. Change
  it: 1, here; the name computation 0 here (descriptor-owned
  pre-bind, stashed `__name__` post-bind). Forms derives pre-build via
  a pure function; here the descriptor exists only post-build — no
  shared derivation. Home: file-local + reject the form-name merge.
- The three construction-hook defaults: 1 body/signature each, here —
  each its own spec-039 contract (`get_serializer_kwargs` constructor
  shape, injected-data exact-match, save-kwarg rejections). The
  carried `hook_context: Any` seam note: keep untyped — the `Any`
  seam is the cross-flavor posture (forms defaults are all-`Any`
  too), the defaults are consumer-override templates, and the
  docstrings already name `SerializerHookContext` (projection). No
  import cycle either way (`hook_context.py` imports nothing local),
  so this is a posture decision, not a dependency one. Home:
  file-local + reject the record annotation.
- `resolve_sync, resolve_async = resolver_seams(...)`: arg declaration
  over the single factory body in `mutations/sets.py:410`. Change
  targets: 1 here; bodies 0. The function-local import keeps the
  load-time edge out (forms precedent). Home: file-local.
- `check_permission`: inherited from the base, correctly not
  overridden (the forms override is the model-less plain flavor's own
  required seam over the shared `run_permission_classes` body). No
  finding. `delete`: rejected per Decision 10, oracle-pinned both
  sides (serializer rejects, model accepts). No finding. Coarse
  `get_serializer`: absent by module-docstring-recorded design
  (framework-owned `partial`/`context["request"]` cannot be entrusted
  to a consumer constructor) — reject. Subsystem-clear rows: none
  here, correctly (inputs owns both namespace rows). No finding.

Matrix (judged against the real surface): (1) cross-flavor — forms +
mutations read in full, every pair above adjudicated; (2) sync/async —
inapplicable, no `async def` / await boundary, `resolve_async` is
factory-generated from the single body; (3) derived knowledge — holds
(one guarded read threaded everywhere, single-sourced name, per-window
effective sets); (4) round-trips — fingerprint capture/check are two
call sites of the inputs-owned computation, build/name agree via the
shared tail + stash, encode/decode halves owned elsewhere; (5) other
media — spec-039 Decisions 6/7/8/10/11/12 are projections, the 87
oracles in `tests/rest_framework/test_sets.py` spell expectations
literally (direct validator calls pin messages via `match=`, never
read from the owner), glossary + README are projections; (6) omission —
two genuine asymmetries, both without a contract source (see below).

Axis-6 contract-source sweeps (my own, for the two maintainer routes):
identifier gate — spec-039 has no identifier/keyword row for serializer
hook keys (only the generic `.fields`-materialization wrap, which is
inputs-owned and present); the glossary `serializermutation` anchor
says nothing about key shape; owner prose at HEAD promises only the
plain-`str` gate; all 87 oracles negative (no non-identifier probe).
Invocation wrap — same four negatives: no spec row extends the
forms-side typed-invocation rule (`forms/sets.py::_mutation_form_fields`)
to serializer hooks; owner prose promises result validation, not
invocation containment. Both fail loud today (raw `SyntaxError` /
hook-raised exception at finalize, never silent corruption), so both
are contract questions for the maintainer, not defects. I would route both.

Deeper nested maps (`inputs.py::read_nested_serializer_fields` does
`dict(serializer.fields)` under an `except Exception` wrap with no
per-key gate): a sweep note for the open hostile family, not a defect
— the family item adjudicates with the full population.

### Part B — reconciliation (post-findings)

Read `## Findings` (F-KEYS…F-MECH, FAM-OWN, ADOPT) + `## Defects`
end to end after Part A. Verdict per area (AGREE = re-derived at HEAD
bytes, never inherited):

- Enumeration: AGREE. 21 module + 14 class statements re-derived by
  AST; every row's member verified against the dump (docstring, 12
  imports, 2 constants, 5 functions, class + its 14). Import census
  47/47 with only `annotations` unreferenced re-derived. All 35
  homes match mine member by member, including the three faceted
  members (14 → F-SCHEMAMAP + hostile adoption, 18 → F-NESTVAL +
  hostile adoption, 20.7 → F-HOOK + FAM-OWN).
- Challenges: AGREE on all 25 rows. Each count re-derived: the 1/0
  splits (foundation, spine bodies, chain, discovery body, path
  value, name computation, tail/guard bodies, posture) all verified
  against the upstream owners; the count-2 own-snapshot read verified
  against both bodies.
- Matrix: AGREE on all 6 axes. Axis 2 inapplicability holds (zero
  `async def`/`await` in the target; `resolve_async` is
  factory-generated). Axis 6 enumeration verified item by item
  (identifier, invocation, deeper maps, coarse hook, inherited
  `check_permission`, delete, subsystem rows, model-hook absence).
- New family (FAM-OWN): AGREE. Count 2 re-derived from both bodies;
  both directions pinned by value-oracles on both sides (serializer
  subclass oracle + forms frozen-snapshot rows, 7 hits); population
  closed by my own `__dict__.get("_mutation_meta")` sweep (only the
  two value-reads-with-fallback; `fields.py:114` presence-only and
  `types/base.py:625` Meta-read exclusions verified on body
  strength; patch-module descriptor reads a different domain).
  Owner candidacy sound (metaclass + snapshot home, no reversal);
  migration sketch, distinct-behavior split, family-owed gate, and
  coupling (F-HOOK + forms R7 — the R7 host verified in the forms
  artifact, which never considered this unification, so no prior
  rejection is contradicted) all present.
- Adoption (ADOPT): AGREE. Family open with no artifact (plan row +
  disk check); resolvers-C11 precedent verified in the resolvers
  artifact (member 50); both facets re-read at HEAD; the 21-oracle
  figure reconciles (6 schema-hook + 15 nested, each name verified);
  coverage-append transcription exact.
- Convergences: AGREE on all 7 CONVERGE rejections, each re-derived
  fresh: R-keys/R-merged (disjoint vocabularies verified —
  serializer rejects `model`, model rejects `serializer_class`),
  R-pair (owner docstring records the serializer split at HEAD),
  R-path (5 disjoint ledgers verified), R-cached (both-sides
  recording verified at both docstrings), R-coarse (module
  docstring), R-guardcalls (production `require_drf(` census
  re-derived: exactly 2, root + leaf line 62). J1 trigger re-check
  holds at HEAD bytes (no shared guard primitive; the worktree
  `truth.*` migration is concurrent dirt, correctly untraced).
- Fresh rejections (R-ops, R-perlevel, R-runtime, R-formdisc,
  R-slotredecl, R-formname, R-importrecord): AGREE, each carries a
  contract difference + trigger. R-slotredecl resolves my Part-A
  soft spot: W1's load-bearing-twin point is correct (the
  plain-form twin cannot inherit — `DjangoFormMutation` is not a
  `DjangoMutation` subclass, verified in its own docstring), and a
  rename moves 10+ readers regardless, so the declarations are not
  the lever. I adopt the rejection.
- maintainer routes (R-ident, R-invoke): AGREE, both endorsed. My own
  four-source sweeps (spec-039, glossary anchor, owner prose, all 87
  oracles) are negative on both; the shared hazards verified (same
  `build_strawberry_input_class` exec path; raw hook call at both
  serializer sites); both fail loud in-phase today. Correctly
  routed, not defects, not quietly closed.
- Seam note (`hook_context: Any`): AGREE, file-local keep-untyped.
  All four grounds verified (del-ignored defaults, all-`Any` form
  hooks, leaf with no local imports, no second site — form hooks
  lack the param entirely). R-importrecord carries difference +
  trigger.
- Near-misses N1–N4: AGREE, all four correctly cleared (no depth
  oracle — the one `hostile` hit is the top map; base `.get` at
  `mutations/sets.py:1279` exists for model delete; raw-getattr is
  package posture with the hunt migration in flight; paren-`del`
  cosmetic).
- Index rows: AGREE, 34/34 (17 file-local + 1 open + 16 rejected)
  match their findings in name, owner, files, and fresh/CONVERGE/
  ROUTED posture; coverage append + Families item exact.
- Freshness: AGREE, all 19 table pins re-derived digit-for-digit;
  per-finding pins consistent.
- Pending execution: AGREE, correctly empty; the sharded/pg
  inapplicability reason verified by full body read (no
  queryset/`using`/backend probe in the target).
- Prose rules: AGREE. No `feedback*` mention; `path::Symbol`
  citations in the established artifact idiom; the 10-header link
  block intact; zero `.py` touched so no ruff owed. `## Defects`
  holds no production defect from either worker — correct.

Differences reconciled (2, both immaterial, neither moves a home,
count, or gate):

1. F-SLOTS "no `__dict__` reader of any slot package-wide"
   overstates: `input_type_name` reads its own `_input_type_name`
   slot via `cls.__dict__.get` (member 20.9, line 898). True
   census (in my Part A and W1's own FAM-OWN exclusion): exactly
   one `__dict__` slot read, by the owning seam itself, correctly
   excluded from the family on contract grounds (bind-stash job,
   no `Meta` fallback, no stamp-timing hazard). Record note only.
2. `## Judgment` "2 CONVERGE-routed to the maintainer" is loose phrasing —
   the two routes are fresh asymmetries, not CONVERGE rows; the
   index rows carry the correct ROUTED posture. Record note only.

No `(Worker-2)` defect: nothing I found breaks a contract row.
No oracle touched (zero-edit; target dirt is pre-existing
concurrent work, absent from the item window).

Window attribution (vs `ITEM_BASELINE=467448e9…`): the tracked diff
names exactly the plan (Worker-0's dispatch/submission record —
concurrent, out of scope) + 5 review-flow paths
(`review-0_0_15.md`, 4× `rev-utils__strings.*`: header touches +
gate/drift/checklist appends; the 3 serializer mentions are a
checklist line + a drift census line, no item content). The item's
own deliverable is the untracked artifact (this file, plus this
verification section). Nothing to re-attribute to the item; no
`.py` in the window.

Status: verified (zero-edit file item; no pending execution).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[operations]: ../../django_strawberry_framework/mutations/operations.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->

[test-sets]: ../../tests/rest_framework/test_sets.py

<!-- examples/ -->

[library-schema]: ../../examples/fakeshop/apps/library/schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->


