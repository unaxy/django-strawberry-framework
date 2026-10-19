# DRY review: `types/finalizer.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target [types-finalizer][types-finalizer] at HEAD blob
`de34ae2a` (2050 lines; worktree `b9d8acb2`, 1974 lines, is
concurrent-external hunt dirt — the `truth.*` migration across 39
hunks, deleting the `_safe_*` trio among other rewrites — absent from
the ledger and the cycle baseline; traced at HEAD bytes throughout,
both fingerprints recorded, nothing tracked touched). The module owns
four things: the `finalize_django_types` build orchestrator (pending
drain → attach → 2.5 binds/audits/synthesis → `strawberry.type`
decoration); the relation-as-Connection synthesis cluster; the six
finalize-time audits (primary ambiguity, field surface, model-label
routing, unregistered related-filter targets, GlobalID filter
strategies, owner-axis agreement); and the two-family sidecar binding
driver (`_SidecarBindingSpec` + `_bind_sidecar_sets` +
`_bind_set_owner_common`) with its per-family adapters.

Sites found (HEAD bytes; `C` = consumer, `O` = oracle, `P` =
projection). Orchestration: the entry-guard no-op at :861 is one of
five finalized-flag verbs (C: the verified
`types-base-finalized-gates-stay-per-verb` row); the snapshot block
:873–899 computes once via [types-relay][types-relay]
`_validated_globalid_setting` (single caller), stamps the registry
slot, and refuses mixed-strategy retry (C: the UNAPPLIED
`globalid-setting-snapshot` row — role map re-verified); the pending
drain :903–960 is the single drain of the registry pending ledger
(C: verified `type-registry-pending-ledger`); `strawberry.type`
decoration :1146 is the only call site touching a consumer-facing
class (the [connection][connection] :1383 and
[mutations-inputs][mutations-inputs] :976 sites decorate generated
classes); `mark_finalized` :1149 is the single flag flip; the bind
slot order (auth → mutations → forms → filtersets → ordersets)
:1115–1131 is declared only here. Synthesis: the
`<field>_connection` name + `relation_connections` write :523–540 is
the single writer (readers: [walker][walker] :723,
[nested-planner][nested-planner] F4 by census); the teardown
registration :541–612 is the single `register_type_teardown` caller
(C: verified `type-teardown-lifecycle`); the marker value :505 is read
only at :730 (C: verified nested-planner R10 — no
`startswith("_dst")` predicate exists package-wide). Sidecars: the
owner write :1214 is the single `_owner_definition` writer; the
`filter`/`order` expand adapters :1706–1724 are the only Layer-4
expansion callers; subpass 4 :1827–1836 is the documented consumer of
the open `set-arguments-factory-bfs` family (touches `.arguments` +
`input_object_types`, spells no walk of its own). Audits: the
ambiguity walk :197–228, surface walk :230–331, routing walk
:378–504, unregistered walk :1726–1758, and GlobalID walk :1906–1952
are each single-sited; every strategy membership is composed by name
from [types-relay][types-relay] / [filters-base][filters-base] (no
inline typing — the `"connection"/"both"` subset :691 is the single
connection-requesting predicate over base's vocabulary). Oracles: the
three `test_finalizer.py` files (17 + 31 + 21 tests — message
wordings, subpass ordering, the `None`-hook asymmetry, orphan arms,
template sharing, idempotent rebind, both GlobalID arms) plus live
`/graphql` pins for synthesized connections across 7+ `test_query`
modules (independent — they drive declarations, never read owner
tables). Projections: the 47-line module docstring (phase contract —
three subpass-count sentences drifted, D2), the GLOSSARY
`finalize_django_types` entry, and spec-Decision cites
(spot-checked: spec-027 D6, spec-032 D6/D7 resolve).

Connected behavior examined: the base construction pipeline
(`__init_subclass__` ordering, `_build_annotations` pending skip,
`_format_unknown_fields_error`, `_validate_relation_shapes` +
`_validate_relation_shape_targets` Decisions 6/7, the annotation-key
creation gate), the definition record slots + `graphql_type_name`
normalization + `related_target_for`, the relay predicate/installer
bundle, the resolvers attach pair, the registry lookup/pending/teardown
quartet, the exceptions safe-renderers + `_safe_text`, the filters
GlobalID resolver + strategy sets + runtime error siblings, the
filters/orders helper ledgers + `materialize_input_class` seam, the
mutations/forms/auth binders, the walker surface matcher, the
mutations input-surface audit, the connection synthesis signature,
keyset cursor validation, `loaded_attr` / `instance_accessor`, the
root import graph (auth opt-in posture), and installed Strawberry
0.324.0 field discovery (`_check_field_annotations`,
`_get_fields`, `_wrap_dataclass`) for the audit-coverage question.
Also read with no rule interaction: [types-relations][types-relations]
(the `PendingRelation` record, composed by name) and
[types-init][types-init] (the leaf export — clean tree, no judgment).

## Verification

### Matrix

Six axes, each swept or ruled out in one line.

1. **Sync/async twins.** Ruled inapplicable: zero `async def` / `await`
   in the target (build-time only; the async surface lives in
   resolvers/execution, never imported here).
2. **Flavor mirrors (filter/order, input/output).** Swept: the two
   `_bind_*sets` declarations, the two `_expand_*` adapters, the two
   owner binders, the two `_owner_*_model_mismatch` wrappers, and the
   `partial`-worded target-mismatch / orphan formatters. The skeleton,
   driver, and three message templates are already single-owned
   (F-OWNER-SKELETON, F-SIDECAR-DRIVER, F-FORMAT-TARGET-SHARED,
   F-FORMAT-MODEL-SHARED, F-FORMAT-ORPHAN-SHARED); the expand split
   refuses unification (R7). The filter/order `materialize` +
   `helper-ledger` + `*_input_type` twins live outside this file and
   are consumed here through one seam each — the twin question belongs
   to those files' items, not this side (single call sites here).
3. **Build/runtime mirrors.** Swept: unregistered-target
   (`_format_unregistered_related_target_error` vs
   `FilterSet._iter_visibility_steps`) → R4; encode-only
   (`_format_globalid_encode_only_filter_error` vs
   `_decode_and_validate_global_id` `GLOBALID_UNVALIDATABLE`) → R5;
   surface audit vs plan-time matching (walker :258/313/322,
   mutations-inputs :189) → R2; surface audit vs input audit
   (mutations-inputs :150) → R3. Shared predicates stay shared
   (`_target_type_for_related_filter`, `resolve_globalid_target_definition`
   — one body, two callers each); messages stay per phase.
4. **Round trips (emit/parse, suppress/restore, bind/unbind).** Swept:
   `_suppress_relation_list_form` ↔ teardown restore halves (one
   lifecycle, F-SYNTHESIS); bind-owner set ↔ `clear_django_type`
   co-clear (the lifecycle owns the clear; this file only sets);
   snapshot stamp ↔ `registry.clear` reset (C1); parked input globals
   ↔ pre-bind ledger reset (the reset owns retry-idempotency; D1 shows
   the orphan comparison missed the same treatment). No second
   implementation of any half.
5. **Projections.** Swept: module docstring (47 lines — D2 drift),
   per-def docstrings (30+, each verified against its body),
   GLOSSARY entry (exists, accurate), spec cites (027 D6, 032 D6/D7
   resolve; the `"both"` vocabulary and `("connection", "both")`
   subset each single-sited). The `_dst_<field>_connection` mention
   :778 is prose projection of the open grammar family (C3); the
   marker value :505 is not a grammar spelling (C4).
6. **Enforcement by omission.** Swept per family: order side needs no
   unregistered-target audit (zero `get_queryset` reads in
   [orders-sets][orders-sets]; the apply path threads
   `target_type`/`model` only) and no GlobalID audit (no GlobalID
   machinery exists in `orders/`); the GlobalID `isinstance` pair
   covers both existing filter flavors (class census = 2); explicit
   shape keys on consumer-authored relations raise at creation
   (Decision 7 — the synthesis skip covers the implicit default
   only); the surface audit covers synthesized siblings (they are
   assigned `StrawberryField`s); rerun paths re-suppress, marker-skip
   without duplicate teardowns, and re-record idempotently. Two
   findings: D1 (orphan comparison omits finalized types' sets on
   rerun — P2-proven) and the cleared P3a near-miss (undecorated-parent
   annotations reach neither audit nor engine on any supported
   Python — F-AUDIT-SURFACE).

### Enumeration

Instrument: every name in `ast.Module.body` (66 top-level statements
binding 77 names: 32 import-bound + 1 `TYPE_CHECKING` + 41 functions
+ 1 class + 2 constants, plus the docstring). Count: 66/66 homed —
23 file-local rows, 0 new families (18 convergences/exclusions onto
existing rows, all transcribing nothing), 10 fresh rejections. The
class sub-map: `_SidecarBindingSpec` carries 10 annotation-only fields
and no methods (10/10 in F-SIDECAR-DRIVER).

| Member(s) | Home |
|---|---|
| #0 docstring, #1–20 imports (32 names), #21 `TYPE_CHECKING` block | F-MECH |
| #22 `_safe_qualified_class_name`, #23 `_safe_field_label`, #24 `_safe_str` | F-SAFE-RENDER |
| #25 `_annotation_names` | F-ANNOTATION-NAMES |
| #26 `_format_unresolved_targets_error`, #27 `_format_ambiguity_error`, #31 `_format_model_label_routing_error` | F-FORMAT-PHASE1 |
| #28 `_audit_primary_ambiguity` | F-AUDIT-AMBIGUITY |
| #29 `_field_surface_names`, #30 `_audit_field_surface` | F-AUDIT-SURFACE |
| #32 `_audit_model_label_routing`, #33 `_first_model_label_emitter`, #34 `_warn_model_label_secondary_collapse` | F-AUDIT-ROUTING |
| #35 marker, #36 `_MISSING_CLASS_MEMBER`, #37 `_suppress_relation_list_form`, #38 `_record_relation_connection`, #39 `_register_relation_connection_teardown`, #40 `_synthesize_relation_connections` | F-SYNTHESIS |
| #41 `finalize_django_types` (incl. entry guard, snapshot block, Phase 1–3 loops, bind slots, no-Node check) | F-FINALIZE |
| #42 `_bind_set_owner_common` | F-OWNER-SKELETON |
| #43 `_bind_filterset_owner`, #44 `_check_filterset_owner_axes`, #45 `_check_filterset_owner_get_queryset_safety`, #46 `_check_filterset_owner_pk_identity` | F-OWNER-FILTER |
| #47 `_format_owner_target_mismatch_error` | F-FORMAT-TARGET-SHARED |
| #48 `_format_owner_pk_mismatch_error`, #49 `_format_owner_get_queryset_mismatch_error` | F-FORMAT-OWNER |
| #50 `_format_owner_set_model_mismatch_error`, #51 `_format_owner_model_mismatch_error`, #55 `_format_owner_orderset_model_mismatch_error` | F-FORMAT-MODEL-SHARED |
| #52 `_format_orphan_sets_error` | F-FORMAT-ORPHAN-SHARED |
| #53 `_format_unregistered_related_target_error`, #63 `_format_globalid_encode_only_filter_error` | F-FORMAT-SIDECAR |
| #54 `_bind_orderset_owner` | F-OWNER-ORDER |
| #56 `_SidecarBindingSpec`, #60 `_bind_sidecar_sets` | F-SIDECAR-DRIVER |
| #57 `_expand_filterset`, #58 `_expand_orderset` | F-SIDECAR-EXPAND |
| #61 `_bind_ordersets`, #65 `_bind_filtersets` | F-SIDECAR-DECLS |
| #59 `_audit_unregistered_related_filter_targets` | F-AUDIT-UNREG |
| #62 `_audit_globalid_filter_strategies` | F-AUDIT-GLOBALID |
| #64 `_audit_filterset_subpass_2_5` | F-SUBPASS25-ORDER |

### Challenges

Each change posited against the rule's own variation axes; the count
is authoritative definitions only. Consumers, oracles, projections
listed, never counted ([dry][dry] Vocabulary). All bodies judged at
HEAD bytes. Static review plus five workspace probes: P1/P1c eliminate
two candidate mid-Phase-3 triggers (both defer to schema build), P2
proves D1 end to end, P3a (×3 Pythons) clears the parent-annotation
question. Nothing else judged is execution-sensitive beyond the cited
oracles.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| 1 | F-MECH | add/remove a module import (new consumer edge) | 1 (this block; the sibling leaf manifest is a different surface) | F-MECH |
| 2 | F-SAFE-RENDER | harden one helper's verdict (e.g. slot discipline) | 1 (that helper; `_safe_text` is a different contract) | F-SAFE-RENDER + R1 |
| 3 | F-ANNOTATION-NAMES | change the key rule (type, verdict, first-vs-all) | 1 (the read gate; the creation gate is a different boundary) | F-ANNOTATION-NAMES + R10 |
| 4 | F-FORMAT-PHASE1 | reword one Phase-1 message | 1 (that message; siblings vary independently) | F-FORMAT-PHASE1 |
| 5 | F-AUDIT-AMBIGUITY | change the ambiguity verdict (sort, quorum, wording) | 1 (the audit; registration guards see one type at a time) | F-AUDIT-AMBIGUITY + R9 |
| 6 | F-AUDIT-SURFACE | change the surface rule (source set, caser, verdict) | 1 (builder + audit; walker/mutations derive under their own converters) | F-AUDIT-SURFACE + R2 + R3 |
| 7 | F-AUDIT-ROUTING | change a routing verdict (raise, warn, emitter choice) | 1 (that arm; the decoder dispatches dynamically) | F-AUDIT-ROUTING |
| 8 | F-SYNTHESIS | change the synthesis rule (name, shape set, teardown) | 1 (the cluster; planner/walker consume the map) | F-SYNTHESIS |
| 9 | F-FINALIZE | reorder phases / change flag lifecycle | 1 (the orchestrator; per-verb gates stay per verb) | F-FINALIZE + C5 |
| 10 | F-OWNER-SKELETON | change the skeleton (order, idempotency, `None` arm) | 1 (the skeleton; adapters are hook params) | F-OWNER-SKELETON |
| 11 | F-OWNER-FILTER | add/change an owner axis | 1 (that axis; the order side stays `None`) | F-OWNER-FILTER |
| 12 | F-SIDECAR-DRIVER | reorder subpasses / change orphan-vs-materialize order | 1 (the driver; declarations are hook params) | F-SIDECAR-DRIVER |
| 13 | F-SIDECAR-EXPAND | change one family's expansion | 1 (that adapter; the other family's machinery differs) | F-SIDECAR-EXPAND + R7 |
| 14 | F-FORMAT-*-SHARED | reword a shared template | 1 (the template; wrappers/partials are word params) | F-FORMAT-TARGET/MODEL/ORPHAN-SHARED |
| 15 | F-AUDIT-UNREG | change the walk (depth, predicate, message) | 1 (the audit; the runtime sibling keeps its second reason arm) | F-AUDIT-UNREG + R4 |
| 16 | F-AUDIT-GLOBALID | change the strategy rule (pair, set, message) | 1 (the audit; the coded backstop keeps its lifecycle arm) | F-AUDIT-GLOBALID + R5 |
| 17 | snapshot | change snapshot lifecycle (timing, retry verdict) | 1 (the block; compute/store live elsewhere) | C1 |
| 18 | pending drain | change drain discipline (order, discard set) | 1 (the loop; the ledger is registry-owned) | C13 |
| 19 | offender sort | change the sort key | 2 lines, one idiom (helper refused as machinery) | F-AUDIT-AMBIGUITY note |
| 20 | bind imports | route all binds through one import posture | refused (three lifecycles, three postures) | R6 |

## Findings

### F-MECH — module mechanics (file-local)

- **Contract + variation.** The 47-line phase-contract docstring; 20
  import statements binding 32 names, every one consumed (use census:
  `dataclass`/`TYPE_CHECKING`/`logger`/`FieldMeta`/
  `GLOBALID_SETTING_UNSET`/`instance_accessor`/
  `_accepts_model_label_decode`/`_check_composite_pk_for_relay_node`/
  `_validated_globalid_setting`/`install_relay_node_resolvers`/
  `_attach_file_resolvers` at exactly import + 1 use; the rest 3+);
  one `TYPE_CHECKING` import (`DjangoTypeDefinition`, annotation-only).
  `PendingRelation` / `FieldMeta` / `models` ride at runtime though
  used in annotations only — safe by leaf-ward direction (no cycle).
  Varies only as the module's consumer edges do.
- **Sites + roles.** Definition: this block (#0–21). Consumers: every
  symbol in the module. Oracles: none directly (mechanics).
- **Challenges.** #1 counts 1.
- **Owner + lifetime.** This module (mechanics have no lifetime).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Function-local imports (registry clearer,
  subsystem binders, helper ledgers) stay per call site with a stated
  cycle/weight reason each; the auth `loaded_attr` posture is R6.
- **Behavioral proof.** `static-reviewed` (use census; inspection
  decides).
- **Structural gate.** None owed (mechanics; RUF022 + CI already
  execute).
- **Coupling.** R6 (import postures), D2 (docstring drift).
- **Freshness.** Target `de34ae2aaed1` (worktree `b9d8acb2b942`,
  unjudged); [types-init][types-init] `1bf69028dbdc` (clean).

### F-SAFE-RENDER — hostile-metadata renderers (file-local)

- **Contract + variation.** Three per-shape non-raising renderers:
  `_safe_qualified_class_name` (module label + qualified class name,
  the only guarded module-qualname renderer package-wide),
  `_safe_field_label` (str passthrough else guarded repr, for
  field-name strings), `_safe_str` (message-text `str()` with
  repr-fallback for f-string assembly). Callers: 9 in-file lines,
  zero outside (census). Varies per helper (verdict, fallback).
- **Sites + roles.** Definition: #22–24. Consumers: the formatters +
  two audit sites in-file. The [exceptions][exceptions] primitives
  (`_safe_arg_repr`, `_safe_class_name`, `_safe_type_name`) are the
  composed owners, not twins.
- **Challenges.** #2 counts 1 per helper (R1, R8, C7 for the refused
  sharings).
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Each helper fixes one input domain (arbitrary
  value / name-string / message-text) and one fallback (type-name /
  repr / repr); no caller needs another helper's verdict.
- **Behavioral proof.** `static-reviewed` (in-file-only census +
  hostile oracles in [test-finalizer][test-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** R1, R8, C7.
- **Freshness.** Target `de34ae2aaed1`; [exceptions][exceptions]
  `e06b0b7f776e`; [types-converters][types-converters] `058f10813927`;
  [inspect-cmd][inspect-cmd] `2807d0fc9d75`;
  [rf-inputs][rf-inputs] `2410f3804fe3`;
  [utils-inputs][utils-inputs] `ee31d360c1db`; [sets-mixins][sets-mixins]
  `ad8987ea2fb1`; [test-finalizer][test-finalizer] `ad82b908d77b`.

### F-ANNOTATION-NAMES — read-time annotation-key gate (file-local)

- **Contract + variation.** `_annotation_names` (:121–148): read
  `type_cls.__annotations__` under a hostile-read guard (detonation →
  typed `ConfigurationError`, the per-subject "could not be read"
  wording), validate every key is a `str` (first bad key →
  `ConfigurationError` rendering the key through the guarded repr),
  return the normalized tuple. Single caller (:264). Varies as the
  read contract (guard, key type, first-vs-all verdict).
- **Sites + roles.** Definition: #25. Consumer: `_field_surface_names`.
  The base creation gate ([types-base][types-base] :640–652) guards a
  different boundary (R10).
- **Challenges.** #3 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Fail-fast-first verdict (vs the creation
  gate's list-all); the read guard has no creation counterpart.
- **Behavioral proof.** `static-reviewed` (single-caller census +
  key oracles in [test-finalizer][test-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** R10.
- **Freshness.** Target `de34ae2aaed1`; [types-base][types-base]
  `dda91365a7e8`; [test-finalizer][test-finalizer] `ad82b908d77b`.

### F-FORMAT-PHASE1 — Phase-1 message wordings (file-local)

- **Contract + variation.** Three per-subject grep-stable wordings:
  unresolved-targets (:150–173, single-vs-multi arms, "declares" lead
  shared with the docstring convention), ambiguity (:174–196,
  offender list + dual fix), model-label routing (:332–377, primary
  attribution + two fix sentences). Each varies with its subject
  (C8); no two share a subject.
- **Sites + roles.** Definition: #26, #27, #31. Consumers: the three
  Phase-1/2.5 audits. Sibling convention: base
  `_format_unknown_fields_error` (shared typo-guard, different
  subjects).
- **Challenges.** #4 counts 1 per message.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The offender-sort line :226/:420 is spelled
  identically twice — one determinism idiom, not two rules (challenge
  #19: a helper would be machinery for one line; the orphans sort
  :1822 uses a different key, proving keys are per-subject).
- **Behavioral proof.** `static-reviewed` (message pins in
  [test-finalizer][test-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** C8; F-AUDIT-AMBIGUITY / F-AUDIT-ROUTING (consumers).
- **Freshness.** Target `de34ae2aaed1`; [types-base][types-base]
  `dda91365a7e8`; [test-finalizer][test-finalizer] `ad82b908d77b`.

### F-AUDIT-AMBIGUITY — primary-ambiguity audit (file-local)

- **Contract + variation.** `_audit_primary_ambiguity` (:197–228):
  over the shared multi-type tuple, raise for a multi-type model with
  no primary (offenders sorted by model name for determinism).
  Failure-atomic (pure read, runs before any mutation). Varies as the
  quorum/verdict (sort, message → F-FORMAT-PHASE1).
- **Sites + roles.** Definition: #28. Consumer: `finalize_django_types`
  :901. Registration-time guards see one type at a time (R9).
- **Challenges.** #5 counts 1; #19 (sort idiom) notes the :226/:420
  pair (no row — the pair is the idiom).
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Cleared near-miss: same-named models from
  different apps sort equal under the unqualified key (stable sort
  preserves registry order) — message-order only, no oracle pins
  multi-offender order, no behavioral divergence; below the defect
  bar, recorded here.
- **Behavioral proof.** `static-reviewed` (ambiguity oracles in
  [test-finalizer][test-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** R9.
- **Freshness.** Target `de34ae2aaed1`; [registry][registry]
  `81bd561c99cb`; [test-finalizer][test-finalizer] `ad82b908d77b`.

### F-AUDIT-SURFACE — field-surface audit (file-local)

- **Contract + variation.** `_field_surface_names` (:230–284: own
  annotations via F-ANNOTATION-NAMES + own assigned `StrawberryField`s
  + inherited decorated bases' fields, explicit `graphql_name` winning
  over default camel-casing — the fifth MRO question, C11) feeds
  `_audit_field_surface` (:285–331: reject empty surfaces and
  camel-case collisions with DjangoType attribution). Runs after
  synthesis settles the surface (:1138–1141), so synthesized siblings
  are covered. Varies as the surface rule (source set, caser,
  verdicts).
- **Sites + roles.** Definition: #29, #30. Consumers: the finalize
  loop (single caller) + the synthesis guard :748–756 (pre-checks the
  generated name through the same builder). Walker / mutations-inputs
  derive names under their own converters (R2); the mutations input
  audit reports fail-fast (R3); base owns collection-time membership
  (C6).
- **Challenges.** #6 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Cleared near-miss (P3a, executed):
  undecorated-parent annotations were feared invisible to the audit
  but visible to the engine; probes on 3.10/3.13/3.14 show
  `cls.__annotations__` is own-only and dataclass inherits only from
  dataclass parents on every supported Python — audit matches engine
  everywhere, no defect. The inherited-interface arm also saves the
  empty message's attribution (suppression can only empty a surface
  whose Node base contributes `id`).
- **Behavioral proof.** `static-reviewed` (surface oracles in
  [test-finalizer][test-finalizer]; P3a runs
  `dry-20260929T022445-5c327f`, `dry-20260929T022634-98aa0d`,
  `dry-20260929T022634-059b69` for the clearance).
- **Structural gate.** None owed.
- **Coupling.** R2, R3, C6, C11.
- **Freshness.** Target `de34ae2aaed1`; [walker][walker]
  `75f9c6b65ed1`; [mutations-inputs][mutations-inputs] `fc4420475f40`;
  [types-base][types-base] `dda91365a7e8`;
  [test-finalizer][test-finalizer] `ad82b908d77b`;
  [test-base][test-base] `0d070aee0513`; installed
  Strawberry 0.324.0 field discovery (external, version-cited).

### F-AUDIT-ROUTING — model-label routing audit (file-local)

- **Contract + variation.** `_audit_model_label_routing` (:378–423):
  raise when a multi-type model's primary cannot decode model labels;
  `_first_model_label_emitter` (:424–444): first registered emitter
  or `None` (missing-definition → typed raise); `_warn_..._collapse`
  (:445–504): warn (not raise) when secondaries collapse onto the
  primary's model label. Memberships composed by name from
  [types-relay][types-relay] (`_emits_model_label` ×2,
  `_accepts_model_label_decode` ×1 — the only non-decode callers).
  The raise/warn split is one verdict pair over the shared tuple, not
  two walks to unify (different verdicts, subjects, messages).
  Varies per arm.
- **Sites + roles.** Definition: #32–34. Consumers: finalize :1055
  (audit) + :1059 (warn, ordering-safe: the audit guarantees
  definitions exist before the warn's direct slot reads).
- **Challenges.** #7 counts 1 per arm.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Cleared near-miss: the relay comment
  "deliberately no `{"callable", "custom"}` literal" governs decode
  acceptance (absence from both memberships); the positive
  `ENCODE_ONLY_GLOBALID_STRATEGIES` set in [filters-base][filters-base]
  :77 serves the filter/audit question — read in context, no
  contradiction.
- **Behavioral proof.** `static-reviewed` (routing + warning oracles
  in [test-finalizer][test-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** C8 (message), F-FORMAT-PHASE1 (formatter).
- **Freshness.** Target `de34ae2aaed1`; [types-relay][types-relay]
  `524398622354`; [filters-base][filters-base] `ba52351c2844`;
  [test-finalizer][test-finalizer] `ad82b908d77b`.

### F-SYNTHESIS — relation-connection synthesis cluster (file-local)

- **Contract + variation.** `_synthesize_relation_connections`
  (:614–823): per non-finalized Node type, per many-side relation,
  resolve the explicit-or-default shape; skip consumer-authored under
  the implicit default (explicit keys already raised at creation —
  Decision 7); degrade implicit non-Node targets to list-only while
  explicit requests raise (Decision 6 split); marker-skip reruns;
  re-suppress-then-attach the sibling (the rerun comment's Phase-2
  re-attach hazard); record + teardown-register. Helpers: tolerant
  pre-decoration suppressor :509–522 (raw-`__dict__` writes, Snapshot
  3.14-safe), idempotent recorder :523–540 (single
  `relation_connections` writer), identity-checked teardown registrar
  :541–612 (single `register_type_teardown` caller; restores exactly
  what it removed — the axis-4 inverse pair). Constants: the
  re-entrancy marker :505 (C4) and the per-contract
  `_MISSING_CLASS_MEMBER` sentinel :506. Varies as the synthesis rule
  (name, shape verdicts, teardown discipline).
- **Sites + roles.** Definition: #35–40. Consumers: finalize :1048;
  the map's reader ([walker][walker] — the planner owns the grammar,
  reads no map output); the lifecycle's teardown runner.
  Single connection-requesting predicate :691 over base's vocabulary.
- **Challenges.** #8 counts 1.
- **Owner + lifetime.** This module; teardown callbacks live until
  `registry.clear()` (C14).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Sentinel discipline: `_MISSING_CLASS_MEMBER`
  is one of 13 per-contract `object()` sentinels package-wide; no
  second class-membership sentinel exists (unification would alias
  `is`-checks across owners).
- **Behavioral proof.** `static-reviewed` (live `/graphql` pins across
  7+ `test_query` modules + synthesis oracles in
  [test-finalizer][test-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** C3, C4, C14.
- **Freshness.** Target `de34ae2aaed1`; [types-base][types-base]
  `dda91365a7e8`; [types-relay][types-relay] `524398622354`;
  [connection][connection] `4894f90fb296`; [registry][registry]
  `81bd561c99cb`; [walker][walker] `75f9c6b65ed1`;
  [nested-planner][nested-planner] `b4dfd4a6f610`;
  [spec-032][spec-032] `1e96ad410466`.

### F-FINALIZE — finalize orchestration (file-local)

- **Contract + variation.** `finalize_django_types` (:824–1149): the
  entry-guard no-op :861–862 (C5); materialize-once
  `multi_type_models` :871 (single
  `models_with_multiple_types` caller; the tuple is shared by both
  audits); unconditional snapshot compute :884 + stamp-or-refuse
  :885–899 (C1); failure-atomic Phase 1 :903–960 (classify
  unresolved / consumer-authored / resolved; single pending drain,
  C13); per-type attach + interfaces + relay installs + cursor
  validation + no-Node check :962–1041 (single orchestration site for
  all six — caller censuses each exactly 1); synthesis :1048 (after the installs, before the
  surface audit + Phase 3 that read the settled surface); routing
  audit :1055 + warn :1059; the pre-bind `iter_subsystem_clears` sweep
  :1095–1096 (C15); the bind slot order :1115–1131 (auth
  loaded-only → mutations → forms → filtersets → ordersets; R6);
  the surface audit loop :1138–1141; the Phase-3 decoration loop
  :1143–1147 (single `strawberry.type` on consumer classes :1146,
  single `finalized` flip :1147); the flag flip :1149 (single
  `mark_finalized` caller). Varies as the build order (slot order,
  flag lifecycle, retry verdicts).
- **Sites + roles.** Definition: #41. Consumers: none in-package (the
  entry point; oracles + consumers call it). Every phase step it
  sequences is owned elsewhere and composed by name.
- **Challenges.** #9 counts 1; #17 (snapshot) and #18 (drain) route to
  their owners.
- **Owner + lifetime.** This module; the retry contract spans calls
  (D1 breaks one arm of it).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Phase-3 `strawberry.type` errors propagate
  raw by design (the docstring's partial-application contract); P1/P1c
  eliminate two feared triggers (unresolvable annotations, invalid
  field names, dataclass ordering all defer past decoration) while
  installed `_check_field_annotations` proves the real one
  (`MissingFieldAnnotationError` on unannotated resolvers — D1's leg
  1, P2-proven).
- **Behavioral proof.** `static-reviewed` (caller censuses + oracles;
  P1 `dry-20260929T021629-c6147a`, P1c `dry-20260929T021700-ed17a4`).
- **Structural gate.** None owed.
- **Coupling.** C1, C5, C13, C15, R6, D1.
- **Freshness.** Target `de34ae2aaed1`; [registry][registry]
  `81bd561c99cb`; [types-relay][types-relay] `524398622354`;
  [types-resolvers][types-resolvers] `72d62dc4ebfe`;
  [keyset][keyset] `df4b5e2f105c`; [root-relay][root-relay]
  `c3c5aea52768`; [mutations-sets][mutations-sets] `7800bd530f2d`;
  [forms-sets][forms-sets] `36ce80b4fef4`;
  [auth-mutations][auth-mutations] `d1a59c44e147`;
  [root-init][root-init] `0ef72601ecac`.

### F-OWNER-SKELETON — set-owner binding skeleton (file-local)

- **Contract + variation.** `_bind_set_owner_common` (:1152–1247):
  the shared idempotent owner binder — stamp `_owner_definition`
  (single writer :1214), rebind-same-definition no-op, second-owner
  refusal (target agreement via `related_target_for` + family hook),
  model agreement (raw `Meta.model` read — the lazy-ref-tolerant
  posture). Hook params (`check_owner_axes`, `format_target_mismatch`,
  `get_model`, family nouns) vary per family; the skeleton varies as
  one body.
- **Sites + roles.** Definition: #42. Consumers: the two owner
  adapters (F-OWNER-FILTER, F-OWNER-ORDER). `related_target_for` is
  composed by name ([types-definition][types-definition] :263).
- **Challenges.** #10 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The order side's `None` hook is a pinned
  absence (`test_bind_orderset_owner_does_not_check_axis_1_relay_identity`),
  not a gap: no owner-dependent axis exists there (zero
  `get_queryset` reads in [orders-sets][orders-sets]; the apply path
  threads `target_type`/`model` only — [utils-querysets][utils-querysets]
  :3181–3198).
- **Behavioral proof.** `static-reviewed` (owner-bind oracles in
  [test-filters-finalizer][test-filters-finalizer] +
  [test-orders-finalizer][test-orders-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** F-OWNER-FILTER, F-OWNER-ORDER, F-FORMAT-TARGET-SHARED.
- **Freshness.** Target `de34ae2aaed1`;
  [types-definition][types-definition] `fa6c4d330e72`;
  [orders-sets][orders-sets] `6044ab1a11c7`;
  [utils-querysets][utils-querysets] `3616927de2bc`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`;
  [test-orders-finalizer][test-orders-finalizer] `44a00e8f6a30`.

### F-OWNER-FILTER — filterset owner axes (file-local)

- **Contract + variation.** `_bind_filterset_owner` (:1248–1304: the
  hook-param adapter) + `_check_filterset_owner_axes` (:1305–1332:
  the two-axis fan-out) + `_check_..._get_queryset_safety`
  (:1333–1365: fail-closed `__func__` comparison — refuses identity
  for behavior, C12) + `_check_..._pk_identity` (:1366–1393: relay
  off-pk agreement via the shared id-column seam). Varies per axis.
- **Sites + roles.** Definition: #43–46. Consumers: the skeleton
  (hook) + subpass 1. `implements_relay_node` / `origin` /
  `field_map` composed by name.
- **Challenges.** #11 counts 1 per axis.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Observed (not a defect): :1455 renders one
  `graphql_type_name` through `_safe_arg_repr` while :1458 uses
  `{...!r}` — both safe (the property returns an inert exact str via
  the base-slot read, verified at both gates); uniformity would use
  one renderer.
- **Behavioral proof.** `static-reviewed` (axis oracles incl.
  fail-closed + identical-target-accept in
  [test-filters-finalizer][test-filters-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** C12, F-FORMAT-OWNER.
- **Freshness.** Target `de34ae2aaed1`; [types-relay][types-relay]
  `524398622354`; [filters-sets][filters-sets] `993e887a7001`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`.

### F-FORMAT-TARGET-SHARED — shared owner-target wording (file-local)

- **Contract + variation.** `_format_owner_target_mismatch_error`
  (:1394–1437): the one second-owner template, shared across families
  via `partial` with family-words params (filter :1301, order :1648 —
  the only `partial(` call sites package-wide outside the inspect
  scalar namer). Varies as one template; families vary the words.
- **Sites + roles.** Definition: #47. Consumers: the two owner
  adapters via the skeleton hook.
- **Challenges.** #14 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** `partial`-words is this file's idiom (the
  model-mismatch pair uses wrapper functions instead because the
  model read itself differs per family — R-adjacent, no row: the
  sharing already exists).
- **Behavioral proof.** `static-reviewed` (mismatch oracles in both
  sidecar suites).
- **Structural gate.** None owed.
- **Coupling.** C8, F-OWNER-SKELETON.
- **Freshness.** Target `de34ae2aaed1`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`;
  [test-orders-finalizer][test-orders-finalizer] `44a00e8f6a30`.

### F-FORMAT-OWNER — filter-only owner verdicts (file-local)

- **Contract + variation.** `_format_owner_pk_mismatch_error`
  (:1438–1464) + `_format_owner_get_queryset_mismatch_error`
  (:1465–1492): the two filter-only axis wordings (no order twins
  exist — the order side has no axes). Each varies with its axis
  (C8).
- **Sites + roles.** Definition: #48, #49. Consumers: the two filter
  axis checks.
- **Challenges.** #11 counts 1 per message.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** None beyond per-subject wording.
- **Behavioral proof.** `static-reviewed` (axis-message pins in
  [test-filters-finalizer][test-filters-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** C8, F-OWNER-FILTER.
- **Freshness.** Target `de34ae2aaed1`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`.

### F-FORMAT-MODEL-SHARED — shared owner-model wording (file-local)

- **Contract + variation.** `_format_owner_set_model_mismatch_error`
  (:1493–1536): the one owner-model template (spec-053 Decision 7 —
  byte-identical to the family originals, pinned by
  `test_owner_model_mismatch_formatters_ride_shared_template`);
  wrappers `_format_owner_model_mismatch_error` (:1537–1559, validated
  `_meta.model`) + `_format_owner_orderset_model_mismatch_error`
  (:1656–1683, raw `Meta.model` incl. the string lazy-ref idiom, whose
  non-class rendering the template body handles). Varies as one
  template.
- **Sites + roles.** Definition: #50, #51, #55. Consumers: the two
  owner adapters via the skeleton.
- **Challenges.** #14 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** D3: the template annotates
  `set_model: type | None` but documents + handles the `str` lazy-ref
  case — the annotation excludes a documented input shape.
- **Behavioral proof.** `static-reviewed` (template-identity oracle).
- **Structural gate.** None owed.
- **Coupling.** C8, D3.
- **Freshness.** Target `de34ae2aaed1`;
  [test-finalizer][test-finalizer] `ad82b908d77b`.

### F-FORMAT-ORPHAN-SHARED — shared orphan wording (file-local)

- **Contract + variation.** `_format_orphan_sets_error` (:1560–1593):
  the one orphan template (single-vs-multi arms), shared across
  families via `partial` with family-words params (:1894, :2041).
  Varies as one template.
- **Sites + roles.** Definition: #52. Consumer: subpass 3 (single
  caller). The check it wordings is D1-broken on rerun; the wording
  itself is single-owned.
- **Challenges.** #14 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The single-vs-multi branching mirrors the
  unresolved-targets shape editorially (lead-in only); only this
  formatter branches on cardinality.
- **Behavioral proof.** `static-reviewed` (orphan-arm oracles in both
  sidecar suites).
- **Structural gate.** None owed.
- **Coupling.** C8, D1 (the check, not the wording).
- **Freshness.** Target `de34ae2aaed1`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`;
  [test-orders-finalizer][test-orders-finalizer] `44a00e8f6a30`.

### F-FORMAT-SIDECAR — sidecar-audit wordings (file-local)

- **Contract + variation.** `_format_unregistered_related_target_error`
  (:1594–1624: declares-RelatedFilter-targeting lead, Decision-8
  rationale, register-or-remove tail) +
  `_format_globalid_encode_only_filter_error` (:1953–1970: names
  filterset + field + target + strategy, remove-or-redecode tail).
  Each varies with its audit (C8); each has a runtime mirror with a
  different contract (R4, R5).
- **Sites + roles.** Definition: #53, #63. Consumers: the two
  filter-side audits.
- **Challenges.** #15/#16 count 1 per message.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The unregistered message's child-model label
  reads `getattr(getattr(child, "_meta", None), "model", None)` — a
  lenient display read over a non-relation subject (C16).
- **Behavioral proof.** `static-reviewed` (audit-message pins in
  [test-filters-finalizer][test-filters-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** C8, R4, R5.
- **Freshness.** Target `de34ae2aaed1`; [filters-sets][filters-sets]
  `993e887a7001`; [filters-base][filters-base] `ba52351c2844`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`.

### F-OWNER-ORDER — orderset owner adapter (file-local)

- **Contract + variation.** `_bind_orderset_owner` (:1625–1655): the
  order hook-param adapter — same skeleton, `None` second axis, raw
  `Meta.model` read, order family words. Varies as the order hook
  params.
- **Sites + roles.** Definition: #54. Consumer: the skeleton (hook) +
  subpass 1.
- **Challenges.** #10 counts 1 (adapter params; the skeleton is
  F-OWNER-SKELETON).
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The `None`-axis absence is behavior-pinned
  (see F-OWNER-SKELETON); no order-side visibility scoping exists to
  audit.
- **Behavioral proof.** `static-reviewed` (order owner-bind oracles in
  [test-orders-finalizer][test-orders-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** F-OWNER-SKELETON.
- **Freshness.** Target `de34ae2aaed1`;
  [test-orders-finalizer][test-orders-finalizer] `44a00e8f6a30`.

### F-SIDECAR-DRIVER — sidecar binding driver (file-local)

- **Contract + variation.** `_SidecarBindingSpec` (:1684–1705: 10
  hook-param fields, no methods) + `_bind_sidecar_sets` (:1759–1838:
  the five-step skeleton — bind owners, expand, optional post-expand
  audit, orphan validation BEFORE materialization, materialize;
  ImportError rewrap naming the set; fail-fast orphans over
  `helper_ledger - wired_set`). Varies as the skeleton (order, rewrap
  verdicts, orphan comparison — D1).
- **Sites + roles.** Definition: #56, #60. Consumers: the two
  declarations (F-SIDECAR-DECLS). Helper ledgers, factories, and
  `materialize` are composed by name ([filters-init][filters-init],
  [orders-init][orders-init], [utils-inputs][utils-inputs]).
- **Challenges.** #12 counts 1.
- **Owner + lifetime.** This module; the `wired` list is per-call
  (D1: it must also cover finalized types' sets on rerun).
- **Migration.** None — zero-edit.
- **Distinct behavior.** The ImportError arm renders `str(exc)` while
  the generic arm renders `repr(exc)` — deliberate verdicts (message
  text vs class+args, per the docstring), not an inconsistency.
- **Behavioral proof.** `static-reviewed` (subpass-ordering,
  orphan-arm, rewrap, and materialization oracles in both sidecar
  suites).
- **Structural gate.** None owed.
- **Coupling.** D1, D2 (prose counts), C2 (subpass-4 consumer).
- **Freshness.** Target `de34ae2aaed1`;
  [filters-init][filters-init] `86b258186638`;
  [orders-init][orders-init] `ed546f9c70d5`;
  [utils-inputs][utils-inputs] `ee31d360c1db`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`;
  [test-orders-finalizer][test-orders-finalizer] `44a00e8f6a30`;
  [spec-027][spec-027] `ca463bdda742`.

### F-SIDECAR-EXPAND — Layer-4 expansion adapters (file-local)

- **Contract + variation.** `_expand_filterset` (:1706–1710:
  `get_filters()` resolves related refs eagerly) +
  `_expand_orderset` (:1711–1724: `get_fields()` stores unresolved +
  the explicit `.orderset` touch forces Layer-2 resolution). One call
  site each (subpass 2). Genuinely different work per family's
  machinery — the unification is refused (R7), not missing.
- **Sites + roles.** Definition: #57, #58. Consumer: subpass 2 via
  the spec seam.
- **Challenges.** #13 counts 1 per adapter.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** None beyond the family-machinery split.
- **Behavioral proof.** `static-reviewed` (expansion-error oracles in
  both sidecar suites).
- **Structural gate.** None owed.
- **Coupling.** R7.
- **Freshness.** Target `de34ae2aaed1`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`;
  [test-orders-finalizer][test-orders-finalizer] `44a00e8f6a30`.

### F-SIDECAR-DECLS — binding declarations (file-local)

- **Contract + variation.** `_bind_ordersets` (:1839–1905) +
  `_bind_filtersets` (:1988–2050): the two per-family spec records
  (hook params + family words + filter-only post audit). Declarations
  of one driver (principle 1), not methods to unify. Vary as the
  family hook params.
- **Sites + roles.** Definition: #61, #65. Consumers: finalize
  :1130–1131. Local imports keep the subsystem pulls lazy (R6).
- **Challenges.** #12 counts 1 per declaration (params only; the
  skeleton is F-SIDECAR-DRIVER).
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** D2: both docstrings say "four ordered
  subpasses" and number orphan/materialize 3/4 — the driver executes
  five steps (the post-expand audit between expand and orphan).
- **Behavioral proof.** `static-reviewed` (declaration-pinned
  behaviors in both sidecar suites).
- **Structural gate.** None owed.
- **Coupling.** R6, D2, F-SIDECAR-DRIVER.
- **Freshness.** Target `de34ae2aaed1`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`;
  [test-orders-finalizer][test-orders-finalizer] `44a00e8f6a30`.

### F-AUDIT-UNREG — unregistered-target audit (file-local)

- **Contract + variation.** `_audit_unregistered_related_filter_targets`
  (:1726–1758): depth-first transitive walk over wired filtersets'
  `related_filters` (cycle-safe `seen` set), raising on the first
  `RelatedFilter` whose `_target_type_for_related_filter` is `None`
  (the shared predicate — one body, this + the runtime caller).
  Ordering-safe: runs post-expansion (refs resolved), post-bind
  (`_owner_definition` stamped).
- **Sites + roles.** Definition: #59. Consumer: `_audit_filterset_subpass_2_5`
  (first). The runtime sibling keeps its second reason arm (R4).
- **Challenges.** #15 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** None beyond the walk discipline.
- **Behavioral proof.** `static-reviewed` (unregistered oracles in
  [test-filters-finalizer][test-filters-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** R4, F-SUBPASS25-ORDER.
- **Freshness.** Target `de34ae2aaed1`; [filters-sets][filters-sets]
  `993e887a7001`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`.

### F-AUDIT-GLOBALID — GlobalID strategy audit (file-local)

- **Contract + variation.** `_audit_globalid_filter_strategies`
  (:1906–1952): over wired filtersets' `get_filters()`, resolve each
  `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` (the `isinstance`
  pair is single-sited; the class census is exactly 2 — no third
  flavor unenforced) through the shared
  `resolve_globalid_target_definition` (one body, this + the runtime
  caller) and raise when the target's effective strategy is in
  `ENCODE_ONLY_GLOBALID_STRATEGIES` (composed by name from
  [filters-base][filters-base] :77). Ordering-safe: runs after the
  unregistered walk (validated graph) and after installs (stamps
  recorded).
- **Sites + roles.** Definition: #62. Consumer: `_audit_filterset_subpass_2_5`
  (second). The coded runtime backstop keeps its lifecycle arm (R5).
- **Challenges.** #16 counts 1.
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** None beyond the membership composition.
- **Behavioral proof.** `static-reviewed` (both GlobalID arms in
  [test-filters-finalizer][test-filters-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** R5, F-SUBPASS25-ORDER.
- **Freshness.** Target `de34ae2aaed1`; [filters-base][filters-base]
  `ba52351c2844`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`.

### F-SUBPASS25-ORDER — subpass-2.5 audit ordering (file-local)

- **Contract + variation.** `_audit_filterset_subpass_2_5`
  (:1971–1987): run the unregistered-target walk before the GlobalID
  walk so GlobalID operates on a validated graph (an unregistered
  target would otherwise surface as a confusing strategy error).
  Varies as the ordering (swap = different first error).
- **Sites + roles.** Definition: #64. Consumer: `_bind_filtersets`
  (the `post_expand_audit` hook; orders pass `None`).
- **Challenges.** #12 counts 1 (ordering is the rule).
- **Owner + lifetime.** This module.
- **Migration.** None — zero-edit.
- **Distinct behavior.** None beyond the ordering.
- **Behavioral proof.** `static-reviewed` (subpass-order oracles in
  [test-filters-finalizer][test-filters-finalizer]).
- **Structural gate.** None owed.
- **Coupling.** F-AUDIT-UNREG, F-AUDIT-GLOBALID.
- **Freshness.** Target `de34ae2aaed1`;
  [test-filters-finalizer][test-filters-finalizer] `8365a1323b4b`.

### C1 — `globalid-setting-snapshot` (CONVERGE, transcribes nothing)

The UNAPPLIED record-only family's ([rule-snapshot][rule-snapshot])
role map re-verified at HEAD: thin
reader [conf][conf] (single caller: `_validated_globalid_setting`),
compute [types-relay][types-relay] `_validated_globalid_setting`
(single caller: :884), orchestration this file :873–899, store
[registry][registry] (slot + sentinel + reset), stamp writer the relay
install, pure readers (decode, filter, testing mint, both audits).
Fresh trigger check: no second compute/store/orchestration exists
(census). The family's missing T-comment stays missing (row already
records UNAPPLIED). Transcribes nothing — row exists.
Freshness: target `de34ae2aaed1`; [types-relay][types-relay]
`524398622354`; [registry][registry] `81bd561c99cb`;
[conf][conf] `c6ad46aa3f0c`.

### C2 — `set-arguments-factory-bfs` (CONVERGE, transcribes nothing)

Subpass 4 :1827–1836 is the family's documented consumer: touches
`factory.arguments`, loops `input_object_types`, calls
`spec.materialize` — spells no walk/collision/cache of its own
(verified at HEAD bytes). Transcribes nothing — row already covers
this file.
Freshness: target `de34ae2aaed1`.

### C3 — `relation-connection-to-attr-grammar` (CONVERGE, transcribes nothing)

This file spells the grammar nowhere: the :505 marker value and the
:778 comment are a re-entrancy token and prose projection, not window
attrs. The `relation_connections` map is synthesis bookkeeping the
walker reads during planning (F-SYNTHESIS), not a grammar definition.
Transcribes nothing — row already covers this file.
Freshness: target `de34ae2aaed1`;
[nested-planner][nested-planner] `b4dfd4a6f610`;
[types-resolvers][types-resolvers] `72d62dc4ebfe`.

### C4 — synthesized marker vs window grammar (CONVERGE with verified nested-planner R10)

Fresh trigger re-check: "a reader matching both namespaces with one
predicate" — no `startswith("_dst")`-style predicate exists
package-wide (sweep); all `_dst_` reads are exact-name
`getattr`/`__dict__` probes or the grammar delegates, and the marker
is read only via the named constant at :730. Unfired. Transcribes
nothing.
Freshness: target `de34ae2aaed1`;
[nested-planner][nested-planner] `b4dfd4a6f610`;
[connection][connection] `4894f90fb296`.

### C5 — finalized gates stay per verb (CONVERGE with verified `types-base-finalized-gates-stay-per-verb`)

The :861–862 no-op is the fifth verb (refuse-register / no-op /
refuse-declare / cache-read / refuse-mint — caller census re-verified:
[types-base][types-base] :628, this file :861,
[mutations-sets][mutations-sets] :543, [types-definition][types-definition]
:304, [testing-relay][testing-relay]). Single flip :1149. Transcribes
nothing.
Freshness: target `de34ae2aaed1`; [types-base][types-base]
`dda91365a7e8`; [types-definition][types-definition] `fa6c4d330e72`;
[mutations-sets][mutations-sets] `7800bd530f2d`;
[testing-relay][testing-relay] `df0dc72a1788`.

### C6 — surface audit vs collection gate (CONVERGE with verified `types-base-strawberryfield-gate-vs-surface-audit`)

Fresh check: base still owns collection-time membership detection,
this file still owns the settled-surface audit — the audit side is
unchanged (F-AUDIT-SURFACE). Transcribes nothing.
Freshness: target `de34ae2aaed1`; [types-base][types-base]
`dda91365a7e8`.

### C7 — label compositions (CONVERGE with verified `types-converters-label-vs-raw-compositions`)

Fresh check at HEAD-vs-HEAD: converters `_field_label`
([types-converters][types-converters] :305–319, guarded object-label over field
objects) vs this file's `_safe_field_label` (string renderer over
name strings) — different inputs, outputs, verdicts; bodies unchanged
in the judged regions. Transcribes nothing.
Freshness: target `de34ae2aaed1`; [types-converters][types-converters]
`058f10813927`.

### C8 — rejection wordings (CONVERGE with verified `per-subject-rejection-grammars`)

All 12 formatters are per-subject (no two share a subject; the three
sharings are already single-owned templates with family-words
params). The "could not be read" census finds only per-subject
variants package-wide. Transcribes nothing.
Freshness: target `de34ae2aaed1`; [schema][schema] `e6b52335b1d1`.

### C9 — except arms (CONVERGE with verified `shared-except-guard` J1)

9 `except BaseException` arms (:90, :95, :108, :117, :126, :141, :483,
:932, :953) with 4 verdict families (degrade-to-None / type-name /
repr / raise-with-context). Per-site, per J1. Transcribes nothing.
Freshness: target `de34ae2aaed1`.

### C10 — isinstance gates (CONVERGE with verified `shared-exact-type-gate` J2)

7 `isinstance` gates, all subclass-tolerant with per-site verdicts —
the opposite mechanism of an exact-type gate, per J2. Transcribes
nothing.
Freshness: target `de34ae2aaed1`.

### C11 — MRO walk (CONVERGE with verified R14 direction)

`_field_surface_names` :240–282 is the fifth MRO question (inherited
decorated-base fields for the settled surface) alongside the four
verified ones (converters dispatch, definition scan, base walk,
sets-mixins scan) — and not a map-key lookup (exclusion for the open
`mro-map-key-lookup` family: no map is keyed here). Transcribes
nothing.
Freshness: target `de34ae2aaed1`; [types-base][types-base]
`dda91365a7e8`; [types-converters][types-converters] `058f10813927`;
[types-definition][types-definition] `fa6c4d330e72`.

### C12 — `__func__` refusal (CONVERGE with verified `types-definition-func-recognition-vs-override-detection`)

The :1351–1352 identity comparison refuses `__func__` identity for
behavioral agreement (fail-closed) — the refusal side the standing
row cites. Bodies unchanged. Transcribes nothing.
Freshness: target `de34ae2aaed1`;
[types-definition][types-definition] `fa6c4d330e72`;
[filters-sets][filters-sets] `993e887a7001`.

### C13 — pending ledger (CONVERGE with verified `type-registry-pending-ledger`)

The :903–960 loop is the single drain (single `discard_pending`
caller; single producer [types-base][types-base] :822; the
register-before-record ordering the loop relies on re-verified).
Transcribes nothing.
Freshness: target `de34ae2aaed1`; [registry][registry]
`81bd561c99cb`; [types-base][types-base] `dda91365a7e8`;
[types-relations][types-relations] `5e9b5cdbc7fb`.

### C14 — teardown lifecycle (CONVERGE with verified `type-teardown-lifecycle`)

`_register_relation_connection_teardown` is the single
`register_type_teardown` caller; teardown callbacks restore exactly
what suppression removed (the lifecycle owns the runner). Transcribes
nothing.
Freshness: target `de34ae2aaed1`; [registry][registry]
`81bd561c99cb`.

### C15 — subsystem clears (CONVERGE with verified `subsystem-clear-lifecycle`)

The :1095–1096 `iter_subsystem_clears(before_bind=True)` loop is the
single pre-bind consumer (full-clear consumer is `registry.clear`).
Transcribes nothing.
Freshness: target `de34ae2aaed1`; [registry][registry]
`81bd561c99cb`.

### C16 — `lenient-relation-metadata-read` (EXCLUDED: non-relation subjects, transcribes nothing)

All 14 lenient `getattr`/`__dict__.get` sites (:249 decorated-base
probe, :569/:729/:766 class-member reads, :580 annotations-dict read,
:730 marker flag, :1212 owner slot, :1220/:1722/:1743 related
maps, :1607/:1644/:1676 display/model reads, :1785 strict wired read)
take non-relation subjects (framework class attrs, class members,
annotation dicts, marker flags, labels, slots) — the open family's
contract covers relation-metadata
reads (`is_relation` / `related_model` / accessor) only, and "strict
callers, bare callers, and non-relation subjects stay out" per
FAM-LENIENT. The family's census gate (over relation attributes) is
unaffected. Transcribes nothing.
Freshness: target `de34ae2aaed1`;
[utils-relations][utils-relations] `8dbc3fe668dd`;
[types-definition][types-definition] `fa6c4d330e72`.

### C17 — `hostile-mapping-hardening` (EXCLUDED: validated mappings, transcribes nothing)

Every mapping read here (`definition.relation_shapes or {}`,
`shapes.get(name, ...)`, `getattr(set_cls, related_attr, {}) or {}`)
runs over framework-owned, creation-validated
mappings — never deployment-supplied hostile input. No member of the
open family. Transcribes nothing.
Freshness: target `de34ae2aaed1`; [types-base][types-base]
`dda91365a7e8`.

### C18 — `graphql-name-gate` (consumer, transcribes nothing)

This file defines no name gate: 7 read sites consume the
`graphql_type_name` property (validated, base-slot-normalized — the
subclass question checked and cleared at both gates). The open
family's pair is untouched. Transcribes nothing.
Freshness: target `de34ae2aaed1`;
[types-definition][types-definition] `fa6c4d330e72`;
[types-base][types-base] `dda91365a7e8`.

### R1 — `_safe_str` vs `_safe_text` (rejected)

Same try-render/except-placeholder shape, different contracts:
`_safe_str` renders message text for f-string assembly (empty renders
empty, repr fallback preserves the message); `_safe_text`
([exceptions][exceptions]) coerces envelope values (inert base-slot
str, empty-collapse to a named fallback, unprintable placeholder).
Different verdicts (empty handling, placeholder choice), different
callers (message assembly vs envelope/field labels). A shared body
needs a verdict flag. Contract difference: interpolation render vs
envelope coercion. Reconsideration trigger: a `_safe_str` caller
needing the envelope verdicts, or a second `_safe_str`-shaped body.
(The worktree hunt deletes `_safe_str`; any future sharing routes
through the hunt's `truth.*` by lineage.)

### R2 — surface names vs plan-time matching (rejected)

`_field_surface_names` (pre-decoration class surface, default
camel-casing — no schema exists yet), [walker][walker] :258/313/322
(post-decoration schema fields, active converter), and
[mutations-inputs][mutations-inputs] :189 (input shaping, package
caser at :542 by deliberate disagreement) share only the
`explicit or to_camel_case(name)` expression — the inputs (class vs
schema vs input), postures (audit vs match vs emit), and caser
contracts differ per site. Sharing the expression is machinery; the
expression itself is the sharing (cf. the testing/client `&`
precedent). Contract difference: finalize-time default-casing
prediction vs plan-time active-converter match vs materialize-time
input naming. Reconsideration trigger: finalization gains access to
the schema converter (collapsing the posture split).

### R3 — surface audit vs input audit (rejected)

`_audit_field_surface` (exhaustive multi-collision report with
DjangoType attribution over a pre-decoration class surface, plus the
empty-surface arm) vs `_audit_mutation_input_surface`
([mutations-inputs][mutations-inputs] :175: fail-fast first-pair
report with input attribution over a post-decoration definition).
Same `_audit_` prefix and collision shape; different reporting
verdicts (exhaustive vs fail-fast), inputs (class vs definition),
arms (empty vs none), and subjects (output vs input). Contract
difference: settled-surface audit vs materialize-time input check.
Reconsideration trigger: either side adopts the other's
reporting/input contract.

### R4 — unregistered-target build vs runtime wording (rejected)

`_format_unregistered_related_target_error` (build-time: declares
lead, one reason arm — refs resolved in subpass 2) vs
`FilterSet._iter_visibility_steps` ([filters-sets][filters-sets]
:2562–2581: runtime, branch-present lead, TWO reason arms). The pair
shares one rationale clause but differs in lead, reason domain, and
tail — a template takes a parameter per clause and pins one sentence
(CONVERGE with the recourse-wording rejection direction on fresh
evidence). The shared predicate (`_target_type_for_related_filter`)
already is the sharing. Contract difference: schema-wiring
declaration error vs request-input branch error. Reconsideration
trigger: the runtime message drops its second reason arm AND both
wordings converge to phase-noun-only divergence.

### R5 — encode-only build vs runtime error (rejected)

`_format_globalid_encode_only_filter_error` (build-time
`ConfigurationError` naming filterset + field + target + strategy,
actionable tail) vs `_decode_and_validate_global_id`
([filters-base][filters-base]: request-time coded `GraphQLError`
`GLOBALID_UNVALIDATABLE`, covering hand-built filtersets plus the
`None`-lifecycle arm the build audit never sees). Different exception
classes (load-bearing: fail-the-build vs fail-the-request), audiences,
and arm domains; even identical wording could not share a body.
Contract difference: wiring error vs coded request backstop.
Reconsideration trigger: the backstop drops its `None`-lifecycle arm
AND both messages converge to phase-noun-only divergence.

### R6 — bind import postures (rejected)

Three postures for five binds: root-loaded plain local import
(mutations/forms — [root-init][root-init] already loads them),
hard-lazy plain local import (filters/orders — finalize pulls them;
no-op on empty ledgers), loaded-only `loaded_attr` (auth — zero
package importers, genuinely opt-in). Unifying to plain import breaks
auth opt-in; unifying to `loaded_attr` hides the unconditional-bind
contract and adds a skip path no caller needs. (The lazy-subpackage
oracles pin `registry.clear()`, not finalize — no contract source
forbids the filters/orders pull.) Contract difference: per-subsystem
lifecycle posture. Reconsideration trigger: auth becomes root-loaded
(→ plain import) or filters/orders become soft-optional (→
`loaded_attr`).

### R7 — expand-adapter unification (rejected)

`_expand_filterset` (eager ref resolution inside `get_filters()`) vs
`_expand_orderset` (`get_fields()` stores unresolved + explicit
`.orderset` touch) — same `_expand_*` shape, same call site, same
spec role, genuinely different work per family's machinery. A shared
body needs a mode flag (principle 5). Contract difference: eager
vs two-touch expansion. Reconsideration trigger: either family's
machinery adopts the other's resolution timing.

### R8 — qualified label vs raw interpolation (rejected)

`_safe_qualified_class_name` (guarded: arbitrary consumer values incl.
non-classes, hostile `__module__`/`__qualname__` degraded) vs raw
`__module__` interpolations ([inspect-cmd][inspect-cmd] ×3,
[rf-inputs][rf-inputs] ×3, [utils-inputs][utils-inputs] ×2, [sets-mixins][sets-mixins] ×1 — trusted
display/collision labels over framework-reached classes). The only other guarded `__module__`
read ([utils-querysets][utils-querysets] :587, via `type.__getattribute__`) is a spoof-resistant
identity check, not a label renderer. No second guarded renderer exists. Contract difference: hostile-metadata
diagnostic vs trusted display label. Reconsideration trigger: a raw
site starts receiving hostile values (it then adopts the guarded
renderer — strengthening F-SAFE-RENDER).

### R9 — ambiguity audit vs registration guards (rejected)

`_audit_primary_ambiguity` (finalize-time, whole-model-group,
missing-primary verdict) vs `registry.register` (incremental,
duplicate-primary refusal) and `definition_for_graphql_name`
(lookup-time ambiguity). Registration sees one type at a time; the
audit needs the full group — unavailable at register time. A shared
body is structurally impossible without group visibility at
registration. Contract difference: deferred group audit vs
incremental refusal. Reconsideration trigger: registration gains
whole-group visibility (e.g. a register-close step).

### R10 — annotation keys vs the creation gate (rejected)

`_annotation_names` (read-time: guarded read after a replacement
window, fail-fast-first verdict, type-label attribution) vs the base
creation gate ([types-base][types-base] :640–652: unguarded read of
the just-built namespace, list-all verdict, class attribution).
Different mappings (live read vs creation namespace), verdicts
(first-fail vs list-all), and guards (guarded vs unguarded read) —
layered defense at two boundaries, not one rule twice. (Distinct from
the open `graphql-name-gate` pair, which validates the same value
with the same verdict at two times.) Contract difference:
creation-boundary vs read-boundary validation. Reconsideration
trigger: either gate adopts the other's full shape, or a third
key-validation site appears.

## Defects

### D1 Orphan check false-positives on recover-in-place rerun after a mid-Phase-3 raise (HEAD, unfixed)

- **Contract row.** The recovery contract (the quoted sentences live
  in the `finalize_django_types` docstring :842–851; the module
  docstring states the sibling "fine-grained partial recovery"
  sentence):
  "Calling `finalize_django_types()` again is safe and resumes from
  the failing entry", and "`registry.clear()` remains the recommended
  escape hatch only when the offending type cannot be fixed in
  place."
- **Shape.** Two DjangoTypes: A wired to a helper-referenced
  filterset (universal — the framework itself calls
  `filter_input_type(definition.filterset_class)` at
  [connection][connection] :1969 / :1980 when building connection and
  list signatures), B carrying a consumer resolver without a return
  annotation. Pass 1: 2.5 green, Phase 3 decorates A, then
  `strawberry.type(BType)` raises `MissingFieldAnnotationError`
  (installed `_check_field_annotations` — decoration-time, proven).
  Consumer fixes B in place (adds the annotation) and re-calls.
- **Wire/config input.** Consumer schema configuration (type
  declarations + the documented rerun call). Pass 2 raises
  `ConfigurationError: FilterSet 'AFilter' is referenced via
  filter_input_type(...) but never assigned...` — spurious (AFilter
  IS assigned via `AType.Meta.filterset_class`), masking recovery.
- **Mechanism.** Subpass 1 skips finalized types (:1783 `continue`),
  so `wired` omits A's set on rerun; subpass 3 compares the
  persistent helper ledger (not a pre-bind-clear row —
  [filters-init][filters-init] registers without `before_bind`) against
  the reduced `wired_set` (:1819–1825) and flags A's set orphan. The
  same-driver orders twin shares the defect (one filing, both
  families). The judged lines are dirt-free (only the sort key and
  message-wording cosmetics differ in the worktree), so the verdict
  transfers to HEAD.
- **Behavioral proof.** `workspace-executed`: P2
  (`/tmp/finalizer-probe/p2.py`, run `dry-20260929T022023-5ac57c`)
  shows pass 1 `MissingFieldAnnotationError` with A finalized / B
  not / flag False, then pass 2 spurious orphan `ConfigurationError`
  after the in-place fix. (First attempt `dry-20260929T022004-c3600b`
  failed on probe construction — unannotated lambda params rejected
  at `strawberry.field` time — superseded.)
- **Owner + fix direction.** `_bind_sidecar_sets`
  ([types-finalizer][types-finalizer] :1780–1825): subpass 3's
  comparison set must include finalized definitions' sets (bind-owner
  only for non-finalized; compare against all-wired). Worker-0: home
  on a named card at closeout.
- **Freshness.** Target `de34ae2aaed1`;
  [filters-init][filters-init] `86b258186638`;
  [connection][connection] `4894f90fb296`;
  [registry][registry] `81bd561c99cb`.

### D2 Subpass-count prose disagrees across six sites (minor doc-only, HEAD, unfixed)

- **What.** The driver executes five steps (bind → expand →
  post-expand audit → orphan → materialize), but the prose takes
  three positions: "four ordered subpasses" at the module docstring
  :26–33 (which also orders materialize-before-orphan, against
  execution), `_SidecarBindingSpec` :1687 ("four-subpass skeleton"),
  `_bind_ordersets` :1840, and `_bind_filtersets` :1989 (both with
  orphan/materialize numbered 3/4); five steps numbered 1–5 in the
  `_bind_sidecar_sets` docstring :1759–1778; fractional 1/2/2.5/3/4
  in the body comments :1780–1827 and the
  `_audit_filterset_subpass_2_5` name. No single coherent reading
  covers all sites (the "2.5 is a hook, not a subpass" reading fails
  at the driver docstring's own step 3).
- **Bar.** Docstring/body contradiction in owner prose (cf. base D1,
  converters D1/D2 precedent class). No behavioral impact — oracles
  pin behavior, not prose.
- **Owner + fix direction.** This file: pick one numbering
  (recommend the fractional 1/2/2.5/3/4 matching the function name +
  body comments; fix the four "four"s + the driver docstring's 3/4/5).
  Worker-0: home at closeout.
- **Freshness.** Target `de34ae2aaed1`.

### D3 `set_model` annotation excludes the documented `str` case (minor, HEAD, unfixed)

- **What.** `_format_owner_set_model_mismatch_error` annotates
  `set_model: type | None` (:1499), but its docstring documents the
  string lazy-ref idiom reaching the template via the order wrapper,
  and the body handles non-class values through the guarded repr.
  The annotation excludes a documented input shape.
- **Bar.** Annotation/body-doc contradiction (same precedent class as
  D2). No runtime impact (ruff does not typecheck; callers pass
  untyped values).
- **Owner + fix direction.** This file: widen to `type | str | None`
  (or `object`). Worker-0: home at closeout.
- **Freshness.** Target `de34ae2aaed1`.

## Pending execution

None. No `proof:` entry: every verdict is `static-reviewed` except
D1 (`workspace-executed` P2) and the executed clearance probes (P1,
P1c, P3a ×3 — all run, all cited). No `gate:` entry: zero-edit, no
regression witness needed; D1's P2 stands as the defect's behavioral
record. Sharded and PG cells are inapplicable by construction: the
target reaches no database, alias, or dialect decision (registry dict
probes + pure string/class reads only). Seven workspace runs made,
all cited (`dry-20260929T021629-c6147a`, `dry-20260929T021700-ed17a4`,
`dry-20260929T022004-c3600b` superseded, `dry-20260929T022023-5ac57c`,
`dry-20260929T022445-5c327f`, `dry-20260929T022634-98aa0d`,
`dry-20260929T022634-059b69`). Probe scripts live at
`/tmp/finalizer-probe/{p1,p1c,p2,p3a}.py` (scratch custody, cited by
content); HEAD-byte extracts at `/tmp/finalizer-head/` (hash-verified
against HEAD). No `docs/dry/temp-tests/` scratch created.

## Judgment

File item with no genuine cross-file candidate: 66/66 statements
homed (77 bound names; 10/10 spec fields in the sub-map). Twenty-three
rules stand file-local with proving challenges; 18 convergences and
exclusions land on existing open/verified rows with fresh trigger
checks (all transcribing nothing — no new family needed); 10
rejections carry contract differences + triggers (R4 converging with
the recourse-wording direction, 9 fresh pairs/triples/splits). Three
HEAD defects filed unfixed (D1 P2-proven orphan-rerun
false positive, D2 stale subpass counts, D3 annotation lie). No
pending execution, no production edits.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs
`ITEM_BASELINE=95ff4a277e9310453d06ad3cb81966deffd27301`: `git diff
<baseline> -- django_strawberry_framework/types/finalizer.py
docs/dry/dry-file-types__finalizer.md` is empty for the baseline
window — the HEAD-vs-worktree dirt on the target (39 truth-migration
hunks) is concurrent-external, absent from both the ledger and the
baseline, traced at HEAD bytes and never touched; the artifact itself
is a new untracked file, the item's only output. The [plan][plan]
`## Owned changes` ledger gains no row from this item (no row names
the target; verified by reading). No `uv run ruff` run (no `.py`
touched; `.md` is outside ruff format scope; `/tmp` probes are
scratch, not tracked). No shared-tree pytest run (static review +
pinned oracles + workspace probes suffice — see `### Challenges`
note). Seven workspace runs, all cited. No commit.

Worker-0 instructions: (a) tick the plan item `File
types/finalizer.py` as verified under Run `0.0.15 2026-09-28-7` once
Worker 2 agrees; (b) add the 33 `## Responsibility index` rows under
`## Index rows for Worker-0` verbatim (23 file-local + 10 rejected);
(c) add nothing under `## Families` (none — see below); (d) home D1
(behavioral, P2-proven), D2, and D3 at closeout.

## Index rows for Worker-0

| `types-finalizer-module-mechanics` | `django_strawberry_framework/types/finalizer.py` (docstring + 20 import statements binding 32 names + 1 `TYPE_CHECKING` block) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-safe-renderers` | `django_strawberry_framework/types/finalizer.py::_safe_qualified_class_name` (+ `_safe_field_label`, `_safe_str`; in-file-only, 9 use-lines) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-annotation-names` | `django_strawberry_framework/types/finalizer.py::_annotation_names` (read-time key gate; creation gate is R10) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-phase1-formatters` | `django_strawberry_framework/types/finalizer.py::_format_unresolved_targets_error` (+ `_format_ambiguity_error`, `_format_model_label_routing_error`; per-subject) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-primary-ambiguity-audit` | `django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity` (group quorum over the shared tuple; registration guards are R9) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-field-surface-audit` | `django_strawberry_framework/types/finalizer.py::_field_surface_names` (+ `_audit_field_surface`; settled-surface builder + exhaustive audit) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-model-label-routing-audit` | `django_strawberry_framework/types/finalizer.py::_audit_model_label_routing` (+ `_first_model_label_emitter`, `_warn_model_label_secondary_collapse`) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-relation-connection-synthesis` | `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections` (+ suppress/record/teardown helpers, marker, sentinel) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-finalize-orchestration` | `django_strawberry_framework/types/finalizer.py::finalize_django_types` (entry guard, snapshot block, Phase 1–3 loops, bind slots) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-set-owner-skeleton` | `django_strawberry_framework/types/finalizer.py::_bind_set_owner_common` (shared idempotent binder + hook params) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-filterset-owner-axes` | `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` (+ `_check_filterset_owner_axes`, get_queryset-safety, pk-identity) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-owner-target-mismatch-shared` | `django_strawberry_framework/types/finalizer.py::_format_owner_target_mismatch_error` (one template, `partial` family-words) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-owner-verdict-formatters` | `django_strawberry_framework/types/finalizer.py::_format_owner_pk_mismatch_error` (+ `_format_owner_get_queryset_mismatch_error`; filter-only) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-owner-model-mismatch-shared` | `django_strawberry_framework/types/finalizer.py::_format_owner_set_model_mismatch_error` (+ filter/order wrappers; spec-053 Decision 7) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-orphan-sets-shared` | `django_strawberry_framework/types/finalizer.py::_format_orphan_sets_error` (one template, `partial` family-words; check is D1) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-sidecar-audit-formatters` | `django_strawberry_framework/types/finalizer.py::_format_unregistered_related_target_error` (+ `_format_globalid_encode_only_filter_error`) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-orderset-owner-adapter` | `django_strawberry_framework/types/finalizer.py::_bind_orderset_owner` (`None`-axis hook params; pinned absence) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-sidecar-binding-driver` | `django_strawberry_framework/types/finalizer.py::_SidecarBindingSpec` (+ `_bind_sidecar_sets`; five-step skeleton) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-sidecar-expand-adapters` | `django_strawberry_framework/types/finalizer.py::_expand_filterset` (+ `_expand_orderset`; per-family machinery, R7) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-sidecar-binding-declarations` | `django_strawberry_framework/types/finalizer.py::_bind_ordersets` (+ `_bind_filtersets`; spec records) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-unregistered-target-audit` | `django_strawberry_framework/types/finalizer.py::_audit_unregistered_related_filter_targets` (transitive walk; runtime sibling is R4) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-globalid-strategy-audit` | `django_strawberry_framework/types/finalizer.py::_audit_globalid_filter_strategies` (encode-only membership; backstop is R5) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-subpass-25-ordering` | `django_strawberry_framework/types/finalizer.py::_audit_filterset_subpass_2_5` (unregistered-before-globalid ordering) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | file-local |
| `types-finalizer-safe-str-vs-safe-text` | `django_strawberry_framework/types/finalizer.py::_safe_str` (rejection recorded here; fresh pair — interpolation render vs envelope coercion) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/exceptions.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-surface-names-vs-plan-time-matching` | `django_strawberry_framework/types/finalizer.py::_field_surface_names` (rejection recorded here; fresh triple — finalize prediction vs plan match vs input naming) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/mutations/inputs.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-surface-audit-vs-input-audit` | `django_strawberry_framework/types/finalizer.py::_audit_field_surface` (rejection recorded here; fresh pair — exhaustive vs fail-fast) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/mutations/inputs.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-unregistered-build-vs-runtime` | `django_strawberry_framework/types/finalizer.py::_format_unregistered_related_target_error` (rejection recorded here; fresh pair — wiring error vs branch error; CONVERGE with the recourse-wording direction) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/filters/sets.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-encode-only-build-vs-runtime` | `django_strawberry_framework/types/finalizer.py::_format_globalid_encode_only_filter_error` (rejection recorded here; fresh pair — ConfigurationError vs coded GraphQLError) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/filters/base.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-bind-import-postures` | `django_strawberry_framework/types/finalizer.py::finalize_django_types` (rejection recorded here; fresh triple — root-loaded vs hard-lazy vs opt-in) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-expand-adapter-split` | `django_strawberry_framework/types/finalizer.py::_expand_filterset` (rejection recorded here; same-file split — eager vs two-touch expansion) | `django_strawberry_framework/types/finalizer.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-qualified-label-vs-raw` | `django_strawberry_framework/types/finalizer.py::_safe_qualified_class_name` (rejection recorded here; fresh — guarded diagnostic vs trusted display) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/management/commands/inspect_django_type.py`, `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/sets_mixins.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-ambiguity-vs-registration-guards` | `django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity` (rejection recorded here; fresh pair — deferred group audit vs incremental refusal) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/registry.py` | File `types/finalizer.py` | rejected |
| `types-finalizer-annotation-keys-vs-creation-gate` | `django_strawberry_framework/types/finalizer.py::_annotation_names` (rejection recorded here; fresh pair — read-boundary vs creation-boundary validation) | `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/base.py` | File `types/finalizer.py` | rejected |

## Families

None — no new holding family. All cross-file candidates converge onto
existing open/verified rows (C1–C18, transcribing nothing) or reject
with triggers (R1–R10). Worker-0 adds no `## Families` item for this
file.

## Independent verification (Worker-2)

Address `dry/dry-file-types__finalizer/verify-1`. Traced HEAD bytes
throughout (`git show HEAD:...` + `/tmp/head-tree` archive of HEAD);
worktree `b9d8acb2` is concurrent-external hunt dirt (39
truth-migration hunks per W1's count, consistent with the `git diff
HEAD` hunk headers I re-read). This section was written before opening
`## Findings` below; reconciliation follows it.

### Own trace (pre-Findings)

Target [types-finalizer][types-finalizer] HEAD blob
`de34ae2a` (2050 lines, digest re-derived:
`de34ae2aaed10fd664197cc2205c29e7d1927c2d`). The module owns four
things: the `finalize_django_types` once-only build orchestrator
(entry guard, GlobalID snapshot block, Phase-1 pending drain,
Phase-2 resolver attach, Phase-2.5 interface/relay/cursor/Node-check/
synthesis/routing/bind/audit steps, Phase-3 `strawberry.type`
decoration, flag flip); the relation-as-Connection synthesis cluster
(marker + sentinel + suppress/record/teardown/synthesize); six
finalize-time audits (primary ambiguity, field surface, model-label
routing + collapse warning, unregistered related-filter targets,
GlobalID filter strategies, owner-axis agreement inside the owner
binders); and the two-family sidecar binding driver
(`_SidecarBindingSpec` + `_bind_sidecar_sets` +
`_bind_set_owner_common`) with per-family owner binders, `_expand_*`
adapters, `_bind_*sets` declarations, and shared `partial`-worded
message templates.

Enumeration (own instrument: `ast.Module.body`): 66 top-level
statements — 1 docstring + 20 imports + 1 `TYPE_CHECKING` block + 41
functions + 1 class + 2 constants. Names bound: 32 import-bound
(re-derived list incl. `annotations` and `TYPE_CHECKING`) + 41
functions + 1 class + 2 constants + 1 `TYPE_CHECKING`-block import
(`DjangoTypeDefinition`) = 77. I would home every statement in a
file-local row except the cross-file consumers/convergences below
(snapshot block, pending drain, entry guard, marker read, label
renderers, `except`/`isinstance` idioms, MRO walk, `__func__`
refusal, subsystem-clear consumption, name reads) and the ten fresh
pairs/triples I would reject. Class sub-map (own count):
`_SidecarBindingSpec` carries **10** annotation-only fields
(`definition_attr`, `expand_label_noun`, `related_noun`,
`bind_owner`, `helper_ledger`, `factory_cls`, `materialize`,
`format_orphans`, `expand`, `post_expand_audit`), zero methods — all
ten belong in the driver row. Module docstring spans file lines 1–47
(47 lines).

Matrix (own discharge): (1) sync/async — inapplicable, zero
`async def` / `await` re-derived by regex over HEAD bytes; (2) flavor
mirrors — the skeleton (`_bind_set_owner_common`, single
`_owner_definition` writer :1214 re-derived by package sweep),
driver, and three `partial`-worded templates are already single-owned;
the `_expand_*` split reflects genuinely different machinery (filter
`get_filters` expands eagerly, order needs the extra
`related.orderset` Layer-2 force-read :1722–1723); the
filter/order `materialize` + helper-ledger twins live outside this
file and are consumed through one seam each; (3) build/runtime
mirrors — four pairs each with one shared predicate body + two
callers (`_target_type_for_related_filter`: sets :2573 + finalizer
:1749; `resolve_globalid_target_definition`: base :635 + finalizer
:1938) and per-phase messages (unregistered-target build :1594 vs
runtime sets :2588; encode-only build :1953 vs coded backstop
filters/base :738/:814; surface builder vs walker converter-aware
match :258/:313/:322; surface audit vs `_audit_mutation_input_surface`
mutations/inputs :~184); (4) round trips — suppress (:509) /
teardown-restore (:568) halves one lifecycle; owner-set (:1214) /
registry co-clear halves split by responsibility; snapshot stamp
(:886) / `registry.clear` reset; parked input globals overwrite /
pre-bind ledger reset; (5) projections — per-def docstrings read
against bodies, GLOSSARY `finalize_django_types` entry exists,
spec-027 D6 / spec-032 D6/D7 cites resolve; the `_dst_<field>_connection`
:778 mention is prose, the :505 marker a re-entrancy token (exactly
two `_dst` hits in the target; zero `startswith("_dst` readers
package-wide); (6) omission — order side needs neither the
unregistered-target audit (the one `get_queryset` hit in orders/sets.py
:349 is prose documenting the ABSENCE of the path) nor the GlobalID
audit (the one `GlobalIDFilter` hit in orders/inputs.py :290 is
absence prose); the GlobalID `isinstance` pair covers both existing
filter flavors (class census = 2: base :852/:963); rerun paths
re-suppress (:738–739), marker-skip (:730), and re-record (:746);
the orphan comparison omits finalized types' sets on rerun (D1,
reproduced below).

Challenges (own posits; counts are authoritative definitions only):
reword one message → 1 (that formatter); change the skeleton order /
idempotency → 1 (the skeleton); change one owner axis → 1 (that axis;
order side stays `None` by contract); reorder subpasses → 1 (the
driver); change one audit verdict → 1 (that audit); change the
synthesis name/shape/teardown rule → 1 (the cluster; walker consumes
the map); change the surface rule → 1 (builder + audit); reorder
phases / change flag lifecycle → 1 (the orchestrator); change the
sort key (`_safe_class_name` offender sorts :226/:420) → 2 lines, one
idiom, helper refused as machinery; route all binds through one
import posture → refused (root-loaded vs hard-lazy vs opt-in are
three lifecycles). Consumers/oracles/projections move alongside,
never counted.

Single-site claims I closed by own sweep (HEAD tree): `_validated_globalid_setting`
single caller :884; `register_type_teardown` single caller :611;
`discard_pending` single caller :960; `iter_pending_relations` single
consumer :906; `mark_finalized` single flip :1149; `strawberry.type(`
consumer-class site :1146 vs generated-class sites connection :1383
+ mutations-inputs :976; `_GRAPHQL_NAME_RE.fullmatch` exactly 2
(base :1295, definition :257) plus 1 unrelated (scalars :84) —
finalizer adds no gate; oracle files 17 + 31 + 21 tests at HEAD
(`git show HEAD:` counts); bind-slot order auth → mutations → forms →
filtersets → ordersets (:1113–1131) read at HEAD.

Prior-verdict triggers I re-checked UNFIRED on fresh evidence (all at
HEAD bytes): base R10 (one shared gate verb — :861 stays the no-op
verb); base R15 (the audit needs membership only — :267–272 collects
`graphql_name` per field); converters R2 (one owned label helper
every site composes — none exists); policies R3 (one owned
rejection-message grammar — none exists); planner R10 (a reader
matching both namespaces — none exists); definition R15 (a consumer
`resolve_id` sharing identity with a default — impossible by
construction); R14 (one owned MRO-walk helper — none exists;
`_field_surface_names` :248 asks a fourth question on a fourth MRO);
J1 (a new guard needing position-state classification — finalizer's
`except BaseException` arms are hostile-metadata guards); J2 (a new
foreign-object protocol needing boundary exclusion — finalizer's
`isinstance` gates are not); `subsystem-clear-lifecycle` (finalizer
consumes `iter_subsystem_clears(before_bind=True)`, declares no row);
`type-registry-pending-ledger` / `type-teardown-lifecycle`
(finalizer is the single drain / single teardown registrant);
UNAPPLIED `globalid-setting-snapshot` (role map re-derived: compute
once :884, stamp :886, refuse mixed retry :887–899);
open `set-arguments-factory-bfs` (subpass 4 touches `.arguments` +
`input_object_types`, spells no walk :1828–1836);
open `relation-connection-to-attr-grammar` (finalizer never calls the
owner, prose-cites once :778);
open `graphql-name-gate` (finalizer reads `graphql_type_name`,
gates nothing);
open `lenient-relation-metadata-read` — EXCLUDED on body strength
(finalizer's relation-field reads are strict direct access
(`field.is_relation`, `field.related_model`,
`field_map[name].is_many_side`, `field_map[pending.field_name]`
raising :930–937); its lenient `getattr(..., default)` reads are on
non-relation subjects: `__strawberry_definition__`, marker, class
members, set declarations, `Meta.model`);
open `hostile-mapping-hardening` — EXCLUDED on body strength
(`relation_shapes` validated at creation by base :314/:1687,
`field_map` framework-built, helper ledgers framework-owned —
no hostile-mapping reads).

D1 reproduced end to end (fresh probe `/tmp/w2-d1-probe.py`, run
`dry-20260929T025845-1ade21`, exit 0, copy fresh): scenario 1 —
`oops = strawberry.field()` with no annotation/resolver on the
second-registered type → first finalize raises
`MissingFieldAnnotationError` with `BookType finalized: True`,
`GenreType finalized: False`, registry flag `False` → in-place fix
(`__annotations__` wholesale, PEP 649) → rerun raises spurious
orphan `ConfigurationError` naming the still-wired `BookFilter`;
scenario 2 (control, no filterset) recovers cleanly. My first probe
shape (bare unannotated `def`) finalized cleanly (strawberry ignores
it) and was discarded — run `dry-20260929T025754-f4982d`. This breaks
the documented recovery contract (module docstring + `finalize_django_types`
"Partial-failure recovery": rerun "is safe and resumes from the
failing entry"). D1's lines: the subpass-1 skip (:1783) and the
`helper_ledger - wired_set` comparison (:1819–1821) are byte-clean at
the worktree; only the adjacent sort key (:1822
`truth.label`) and the subpass-2 `except` arms are hunt-dirtied —
neither moves the membership verdict. HEAD defect on clean lines →
normal closeout homing (fix will neighbor one render-only dirt line,
exact hunk cited above).

Record notes (pre-Findings, immaterial unless Findings depend on
them): (a) `_SidecarBindingSpec` has 10 fields, not 8 — every home
claim must cover all ten; (b) `### Matrix` axis 5 says "67 lines" for
the module docstring whose span is 1–47 (System trace says 47 —
internally inconsistent); (c) `### Enumeration`'s "1 `TYPE_CHECKING`"
binds one name (`DjangoTypeDefinition` in the block) — the 77 total
holds; (d) nested-planner reads `relation_connections` zero times at
HEAD (my sweep) — only walker (+ the definition slot declaration)
reads the map, so any "nested-planner reads the map" phrasing would
be wrong (the grammar-family census is a different claim).

### Reconciliation (every difference explicit)

Verdict per area: enumeration AGREE (66/66 + 77 names; sub-map
corrected 8→10, all ten in F-SIDECAR-DRIVER); matrix AGREE (all six
axes discharged against the real surface — axis-1 inapplicability
re-derived zero `async`/`await`; axis-6 omission claims re-derived:
orders absence-prose ×2, GlobalID class census 2, rerun
re-suppress/marker-skip/re-record); challenges AGREE (all 20 counts
re-derived: #1–#18 each 1, #19 two-lines-one-idiom,
#20 refused-three-postures); convergences AGREE all 18 (every prior
trigger re-checked UNFIRED on fresh HEAD evidence, both body-strength
exclusions re-derived including the four sites C16 undercounted);
rejections AGREE all 10 (contract difference + trigger each, pairs
re-read at HEAD); D1 ENDORSED (my own end-to-end repro +
universality cites verified); D2 ENDORSED (scope +1, see E-W2-12);
D3 ENDORSED (annotation/docstring/body triple verified); index rows
33/33 match (mechanical + content check, one transcription direction
E-W2-13); freshness 40/40 pins digit-for-digit MATCH (both batches
above); Pending-None correct (W1's 7 runs all executed+cited; my 2
runs are verification evidence; sharded/PG inapplicable — the target
reaches no DB, my probe used none).

Errata corrected in place (run-7 E1 precedent; all verdict-neutral,
homes/counts/gates unmoved) — E-W2-1: spec-fields 8→10 in three
spots (`### Enumeration`, F-SIDECAR-DRIVER,
`## Judgment`); E-W2-2: matrix axis 5 "67 lines"→47;
E-W2-3: C11 "inspect walk"→sets-mixins scan (the inspect artifact's
RJkeywalk is a converters-overlap rejection, not an R14-family
member); E-W2-4: C16 census 10→14 (+ :569/:580/:729/:766, all
non-relation); E-W2-5: C17 phantom ``filter_spec.maps`` removed
(zero hits package-wide); E-W2-6: C18 6→7 read sites;
E-W2-7: R3 `:150`→`:175` (def line; :150 is FieldError-docstring
prose); E-W2-8: F-SYNTHESIS map readers → walker only + C3 "plan
side reads"→"walker reads during planning" (nested-planner owns the
grammar, zero map reads — sweep); E-W2-9: F-FINALIZE synthesis
parenthetical ("before the installs"→"after the installs, before
the surface audit + Phase 3"); E-W2-10: D1 contract-row location
(module→`finalize_django_types` docstring :842–851; quotes verbatim);
E-W2-11: Judgment rejection arithmetic (7+3+4=14 → R4
converge-direction + 9 fresh).

Section-documented (no artifact edit): E-W2-12 — D2's scope is seven
sites, not six: [filters-init][filters-init] :45 calls the orphan
check "subpass 4" (contradicts the driver's "Subpass 3: orphan");
home D2 with this seventh site (the orders twin carries no such
prose — verified absent). E-W2-13 — transcription direction: append
`, django_strawberry_framework/utils/querysets.py` to the R8 index
row's files list (R8 judges :587; the row omits it); other 32 rows
verbatim. E-W2-14 — loose paraphrases, no change:
F-OWNER-SKELETON hook nicknames, F-OWNER-FILTER "off-pk"/"comparison"
glosses, F-FORMAT-TARGET-SHARED bare-`partial(` census (auth's five
`functools.partial` sites are a different idiom — verified).

Considered and NOT routed (file-item duty): the six
`if definition.finalized: continue` loop heads (one line each, loop
furniture — refused on the challenge-#19 ground: a registry helper
would hide the skip from phase readers); the two missing-definition
raises (:410–414, :434–438 — per-subject wordings, C8 class). No
production edit owed, no holding family named — zero-edit stands.

P3a clearance independently verified: strawberry 0.324.0 `_get_fields`
collects parent fields only from `has_object_definition` bases and
own fields via dataclasses (own annotations + dataclass bases) —
the audit's three sources mirror the engine exactly, and every
DjangoType carries own `__annotations__` (base :823), so no
undecorated-parent asymmetry exists on any supported Python. The
F-OWNER-FILTER :1455/:1458 renderer asymmetry stays observed-not-defect
(`graphql_type_name` is exact-`str` at both `fullmatch` gates —
re-derived base :1295 + definition :257); the same-name-model sort
stays below the bar (message order only). No `(Worker-2)` defects.

Window re-attribution (hunk-by-hunk vs
`ITEM_BASELINE=95ff4a27…`, HEAD unmoved at `0c0537e2`, target
worktree hash unchanged at `b9d8acb2` — fingerprints fresh):
the plan (Worker-0 dispatch/record — mine to leave alone);
`connection.py` (one hunk, `untrimmed = conn` — the review's V1 fix,
review owned-changes row "V1 untrimmed bind"); `consumers.py` +
`tests/test_routers.py` (prose-only hunks that landed
mid-verification — the review's consumers Comments pass, review
owned-changes rows cite both); `review-0_0_15.md` (bench numbers,
connection verified record, consumers/error_policy/routers status,
owned-changes rows, drift lines — all review-flow); the artifact
(new untracked, the item's only output). All concurrent/out-of-scope
except the artifact. Zero-edit confirmed (`git diff` names no
W1-tracked path); zero `.py` touched by the item so no ruff owed
(the window `.py` files are review-owned; their record says lint
green). AGENTS.md prose rules on the artifact: `path::Symbol` rows
(33/33) + `:line` cites (allowed in `dry-file-*` scratch artifacts),
10/10 canonical link groups present, run-id citations as DRY.md
requires, no tests owed by a zero-edit file item.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[plan]: dry-0_0_15.md
[rule-snapshot]: dry-rule-globalid-setting-snapshot.md

<!-- docs/SPECS/ -->
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[keyset]: ../../django_strawberry_framework/keyset.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[root-init]: ../../django_strawberry_framework/__init__.py
[root-relay]: ../../django_strawberry_framework/relay.py
[schema]: ../../django_strawberry_framework/schema.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base]: ../../tests/types/test_base.py
[test-finalizer]: ../../tests/types/test_finalizer.py
[test-filters-finalizer]: ../../tests/filters/test_finalizer.py
[test-orders-finalizer]: ../../tests/orders/test_finalizer.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

