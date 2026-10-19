# DRY review: `django_strawberry_framework/types/base.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every
rule below is recorded file-local with its proving challenge, routed to
a holding family for Worker-0 to add, converged onto an existing family
with fresh trigger checks, or is a rejection carrying its contract
difference + trigger. Zero production edits; zero tracked files changed.
HEAD-bytes trace throughout (see Dirt note).

Target: `django_strawberry_framework/types/base.py`, HEAD blob
`dda91365a7e8cb146d718b6f61b95e4821d6a555` (2015 lines) versus worktree
`dc67f084cbc969d64b7b1f1ef18c388095d394f7` (2018 lines).
`ITEM_BASELINE=8c043fc1ff78f1ef45552da2206be46bda6088d5` (stash-commit
object; resolves). Address
`dry/dry-file-types__base/consolidate`; no workspace runs — the item is
static-decidable (one read-only interpreter probe, inline, cited at R1).

## System trace

The target is the package's type-collection root: `DjangoType`, the
`Meta`-class-driven Django-model-to-Strawberry-type adapter every
consumer type subclasses. It DEFINES the `Meta` declaration contract
(`ALLOWED_META_KEYS` / `DEFERRED_META_KEYS`, per-key validators, the
`_ValidatedMeta` snapshot), the consumer-override contract (four-corner
annotation/assignment collection + `consumer_authored_fields` union +
`auto` marker), the Relay-shape predicate (`_is_relay_shaped`) and its
gate wording, the GlobalID strategy vocabulary + single validator, the
relation-shape vocabulary, field selection, annotation synthesis with
Relay-pk suppression, the `get_queryset` hook contract, and the Relay-id
collision guard. It COMPOSES by name everything downstream: the
`DjangoTypeDefinition` record ([types-definition][types-definition]),
scalar/file conversion ([types-converters][types-converters]), the
pending-relation record ([types-relations][types-relations]),
`install_is_type_of` ([types-relay][types-relay]), the registry
([registry][registry]), the `OptimizerHint` shape
([hints][hints]) + `FieldMeta` ([field-meta][field-meta]), the async
predicate ([utils-typing][utils-typing]), the setting key
([conf][conf]), safe renders ([exceptions][exceptions]), and the
`FilterSet` / `OrderSet` / keyset validators through documented
cycle-dodging in-function imports. No queryset, no transport, no
`await`, no bus row: all effects are class-creation-time validation +
registration.

Connected code read for judgment, outside the item (all at HEAD bytes;
see Freshness): the six types siblings in full
([types-init][types-init] clean,
[types-converters][types-converters] entry + enum core,
[types-definition][types-definition] record + `graphql_type_name` +
`_resolves_id_off_pk` + `related_target_for`,
[types-finalizer][types-finalizer] Phase 2.5 + audits + sidecar bind,
[types-relations][types-relations] clean,
[types-relay][types-relay] strategy path + payload sets + guards,
[types-resolvers][types-resolvers] attach seam);
[registry][registry] (`register_with_definition`,
`add_pending_relation`, `is_finalized`, `primary_for`);
[keyset][keyset] (both cursor validators);
[exceptions][exceptions] (the four safe helpers);
[conf][conf] (setting reader + key);
[list-field][list-field] (both target guards);
[inspect][inspect] (predictor + row dispatch + finalized check);
[testing-relay][testing-relay] (gate composition + mint tail);
[root-relay][root-relay] (fifth-guard variant + decode routing);
[connection][connection] (field guard + `_connection_type_for`
provenance); [filters-sets][filters-sets] + [filters-base][filters-base]
+ [filters-inputs][filters-inputs] (expansion contract, strategy
acceptance, decode); [orders-sets][orders-sets] (expansion twin);
[forms-sets][forms-sets] + [forms-inputs][forms-inputs] (Meta matrix +
GFK posture); [mutations-sets][mutations-sets] +
[mutations-inputs][mutations-inputs] (shared key helper, model chain,
GFK posture); [sets-mixins][sets-mixins] (MRO declaration scan);
[routers][routers] (factory arity bind); [hints][hints] (shape +
skip predicate); [field-meta][field-meta] (construction + flags);
[walker][walker] + [nested-planner][nested-planner] (override-set +
hook consumers, census-level); [querysets][querysets] (stamp read,
census-level); [scalars][scalars] (unrelated `fullmatch`,
census-level); oracles under `tests/types/` (486 tests across 10
modules: counts + pin bodies below) plus the Meta-class-gate pins in
[test-forms-sets][test-forms-sets] / [test-mutations-sets][test-mutations-sets]
and the worktree-only mirror gate in [test-inspect][test-inspect];
contract sources [spec-015][spec-015] (Decision 4 + slices, read) and
[spec-015-rationale][spec-015-rationale] (`:100` renumber record, read)
plus the [spec-011-stub][spec-011-stub] header (read; other code-cited
spec decisions were NOT re-read — bodies + oracles carry those
verdicts); projections [glossary][glossary] (Meta-key catalog, clean)
and [docs-readme][docs-readme] (consumer `Meta` examples).

Dirt note (HEAD-only judgment; nothing touched): the target is DIRTY —
214+/211- across ~40 hunks, all concurrent-external per dispatch (hunt
`truth`-migration: `_safe_*` → `truth.*`, `isinstance`/`getattr` →
`truth.*`, new `_model_name`, plus the maintainer's 4 `except
BaseException` arm deletions), absent from the ledger and the cycle
baseline; attributed by diff content against `git show HEAD:`, never by
filename. `utils/truth.py` is absent at HEAD (verified: `git show
HEAD:` fails), so no truth-reader consolidation is available to any
HEAD verdict. Every other package input inspected is likewise dirty
(concurrent hunt work); all verdicts read the pinned HEAD blobs in
Freshness. The worktree-only mirror-gate test
(`_mirror_check`/`test_inspect_suppressed_pk_mirror_matches_synthesis`,
owned `## Owned changes` dirt) is cited by content as the standing
guard for C3, not as HEAD evidence.

Excluded with reason (body strength; fingerprints in Freshness):
`one-sync-boundary` (token grep 0 for `sync_to_async`), `awaitable-refusal-and-disposal`
(no awaitable here), `sealed-execution-queryset` + the optimizer
execution families (no queryset: `Queryset`/`QuerySet` token grep 0
outside the `get_queryset` hook name), `subsystem-clear-lifecycle` (no
bus row: `register_subsystem_clear` grep 0),
`soft-dependency-require-guard` (all 33 imports hard),
`version-single-sourcing` / `logger-single-sourcing` (no surface),
`set-arguments-factory-bfs` / `dynamic-set-class-getter` (no factory
here), `active-terms-purity-agreement`,
`serializer-source-axis-normalization`,
`canonical-input-provisional-name`,
`mutation-discovery-own-snapshot-read`,
`multipart-control-field-names`,
`registered-djangotype-definition-validation` (no registration proof
here — reconciled in C3, not adopted), `relation-connection-to-attr-grammar`
(`relation_connection_to_attr` grep 0), every `nested-*` / `window-*` /
`lateral-*` / `prefetch-*` / `composite-index` / `scalar-only-window` /
`keyset-cursor-column` family (optimizer interior; this file feeds
`field_map`/declarations only), `upstream-patch-*` (no patch
mechanics), `prepared-view-handoff-shape` (no view handoff),
`mutation-input-reverse-map` / `mutation-error-envelope` /
`shared-write-skeleton` / `write-relation-id-typing` /
`generated-mutation-input-identity` (write-side; no surface),
`subscription-per-event-error-masking` (extension-side),
`already-registered-error-wording` (registry-side),
`relation-instance-accessor` / `relation-kind-taxonomy` (no classifier
here — cardinality read from `FieldMeta.is_many_side` by name),
`schema-construction-policy-ladder` / `policy-authority-isolation` (no
policy surface), `optimizer-hint-skip-predicate`
(`hint_is_skip` grep 0 — only the shape is enforced here),
`nested-connection-strategy-selection` (no strategy selection here),
`child-queryset-alias-inheritance` /
`async-only-queryset-row-adapter` /
`post-set-apply-result-validation` / `queryset-seed-and-model-read` /
`orm-lookup-path-resolution` / `recomposition-illegal-source-rejection` /
`related-object-visibility-recheck` / `field-value-coercion` /
`sync-boundary-recourse-wording` (queryset/execution-side; no surface).
The verified `relay-node-name-decode`, `typed-globalid-decode`,
`globalid-decode-input-hardening`, `globalid-relation-pk-marker`,
`relay-node-type-stamp`, `optimizer-execution-frame`, and
`type-registry-*` / `type-teardown-lifecycle` families sit downstream
of this file (they consume its outputs); no member facet lives here
except the convergences C2/C4/C5/C6 named below.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Sibling flavors read before any
uniqueness claim: the write-flavor `Meta` matrices
([mutations-sets][mutations-sets] shared `reject_unknown_meta_keys` +
model chain, [forms-sets][forms-sets] three key sets), the set-flavor
expansion contracts ([filters-sets][filters-sets],
[orders-sets][orders-sets]), the field-factory target guards
([list-field][list-field], [root-relay][root-relay],
[connection][connection]), and the GFK postures
([forms-inputs][forms-inputs], [mutations-inputs][mutations-inputs]).
Two genuine cross-module pairs found: the GraphQL-name gate (FAM-NEW,
count 2) and the suppression performer/predictor (C3 onto the standing
UNAPPLIED family, count 2). Everything else is per-flavor by contract
(R1/R2/R4/R5/R6/R8/R9/R10/R12/R14/R15/R16/R19/R20/R21, each with its
difference + trigger).

**2. Sync/async twins.** Inapplicable with reason: the target defines
no colored pair — token grep over HEAD bytes for `async def` /
`await` / `sync_to_async` / `asyncio` returns 0; the 10 `async` substring
lines all sit in the import (:59) plus the two strategy validators'
prose and code (:376–473) (the
`is_async_callable` composition + sync-encoder messages). Class
creation is sync by construction; the one async-*related* rule
(encoders must be sync) is enforced by composing the shared predicate
(F-STRAT1). Considered families `one-sync-boundary` and
`async-only-queryset-row-adapter`: checked, no surface (Exclusions).

**3. Derived rather than repeated knowledge.** Audited every
re-derivation: `relay_shaped` is recomputed by calling the one
`_is_relay_shaped` predicate twice with identical arguments
(`_validate_meta` :1342 for the gates, `__init_subclass__` :738 for
the guards) — one definition called twice, not two definitions
(change moves 1 site; threading the bool would save a call, not a
change obligation — noted, not a finding). `field_map`,
`selected_fields`, and the `consumer_authored_fields` union are each
derived once and threaded. The pk-NAME identity (`_meta.pk.name`
guarded by relay-shape) is spelled at three sites (F-NULL :1595,
F-SYNTH :1937, predictor) — count 2+, routed with the suppression
rule (C3). Gate wording, strategy vocabulary, shape vocabulary, and
the name regex are each declared once and composed by name (C7/C9/C11
analogues below). Nothing else is re-derived at runtime.

**4. Inverse / round-trip pairs.** Six pairs, each single-sited per
half: (a) cursor stage-1 here + `validate_cursor_field_references`
(shared by both stages, one body in [keyset][keyset]) + stage-2
columns (F-CURSOR); (b) relation-shapes stage-1 here + stage-2 here +
finalizer Decision-6 target check (F-RSHAPES1/F-RSHAPES2); (c)
strategy validate here (both sources) → resolve → stamp → encode →
decode ([types-relay][types-relay]) with the encode-only absence
contract (F-STRAT1/R8); (d) `PendingRelation` produce here / resolve
in [types-finalizer][types-finalizer] / discard in
[registry][registry] (F-SYNTH); (e) `Meta.name` declare here /
`graphql_type_name` derive in [types-definition][types-definition]
(FAM-NEW — the pair whose gate halves are one rule); (f) suppression
performer here / read mirror in [inspect][inspect] (C3). The
nullability tri-state is computed here and honored in
[types-converters][types-converters] (F-SYNTH facet, one computation).

**5. Contracts restated in another medium.** Four media: production
code (the validators + synthesis); independent oracles (486 tests
under `tests/types/`, spelling literals and driving behavior, never
reading owner tables; the Meta-class-gate pins in the write-flavor
suites; the worktree-only mirror gate); contract sources
([spec-015][spec-015] Decision 4 read + code-cited decisions
elsewhere, carried by bodies + oracles); projections (module +
validator docstrings, [glossary][glossary] Meta-key catalog,
[docs-readme][docs-readme] consumer examples, owner cross-reference
comments). A vocabulary change moves each owner once; consumers
follow by name (challenges C7/C9/C12/C15/C27).

**6. Enforcement by omission.** Six probed absences: (a) `description`
passes unvalidated — no flavor validates it either (grep 0), so no
asymmetry, cleared in F-META; (b) non-class `Meta` is accepted when
it quacks (write flavors gate `isinstance(meta, type)` with oracles;
no contract source establishes the rule here) — ROUTED TO MAINTAINER
(R-MAINT1); (c) hostile dict-subclass / Mapping iteration inside the
mapping gates — the open family's scope call, rides as C1 sweep
notes, not defects; (d) flavors read `Meta` raw where this file
contains (`_meta_attr`) — no contract source extends containment
(R17, sets-N3 prior evidence trigger-checked); (e) the finalizer
re-walks `vars(type_cls)` for its surface audit instead of reading
the stored override sets — different read (names, not membership),
rejected R15; (f) `connection`/`relation_shapes` defensive `dict()`
copies — two sites, independent change obligations (a change to one
copy moves 1 site), noted in F-CONN/F-RSHAPES1, not a rule. No member
lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned HEAD blob
`dda91365a7e8cb146d718b6f61b95e4821d6a555`, counting
`ast.Module.body` members — **67 top-level statements** (1 docstring
+ 21 import statements binding 33 names + 14 constant/assignment
statements + 31 function/class definitions). Every member lands
below; every challenge in `### Challenges` ends in a family row, a
file-local row, or a rejection. (HEAD line numbers throughout.)

| # | Statement (HEAD) | Binds / carries | Home |
|---|---|---|---|
| 0 | module docstring (consumer surface + pipeline list) | prose projection | F-MECH |
| 1 | `import inspect` | `inspect` (callable arity bind) | F-MECH |
| 2 | `import re` | `re` (NodeID string matcher) | F-MECH |
| 3 | `import typing` | `typing` (origin/args reads) | F-MECH |
| 4 | `from collections.abc import Callable, Mapping, Sequence` | annotation + gates | F-MECH |
| 5 | `from collections.abc import Set as AbstractSet` | set-accepting gate | F-MECH |
| 6 | `from typing import Annotated, Any, ClassVar, NamedTuple` | marker check + records | F-MECH |
| 7 | `from django.db import models` | `models` (model gate) | F-MECH |
| 8 | `from strawberry import relay` | `relay` (Node + helpers table) | F-MECH |
| 9 | `from strawberry.relay.types import NodeIDPrivate` | marker identity | F-MECH |
| 10 | `from strawberry.types.auto import StrawberryAuto` | `auto` instance arm | F-MECH |
| 11 | `from strawberry.types.field import StrawberryField` | override gates | F-MECH |
| 12 | `from ..conf import RELAY_GLOBALID_STRATEGY_KEY` | setting subject label | F-MECH |
| 13 | `from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_text, _safe_type_name` | raise + render vocabulary | F-MECH |
| 14 | `from ..optimizer.field_meta import FieldMeta` | `field_map` values | F-MECH |
| 15 | `from ..optimizer.hints import OptimizerHint` | hint value gate | F-MECH |
| 16 | `from ..registry import registry` | registration + finalized flag | F-MECH |
| 17 | `from ..utils.typing import is_async_callable` | encoder sync-ness | F-MECH |
| 18 | `from .converters import _field_output_type_for, convert_field_output` | scalar/file synthesis | F-MECH |
| 19 | `from .definition import _GRAPHQL_NAME_RE, DjangoTypeDefinition` | name regex + record | F-MECH |
| 20 | `from .relations import PendingRelation, PendingRelationAnnotation` | deferral record + sentinel | F-MECH |
| 21 | `from .relay import install_is_type_of` | collection-tail install | F-MECH |
| 22 | `DEFERRED_META_KEYS` (:65) | 3 reserved keys | F-METAKEYS |
| 23 | `ALLOWED_META_KEYS` (:69) + net-new-keys comment | 18-key vocabulary | F-METAKEYS |
| 24 | `RELATION_SHAPE_VALUES` (:104) | 3-shape vocabulary | F-SHAPES |
| 25 | `DEFAULT_RELATION_SHAPE` (:111) + secure-default comment | `"connection"` default | F-SHAPES |
| 26 | `_RELAY_NODE_GATE_LEAD` (:119) | shared lead-in | F-GATEWORDS |
| 27 | `_RELAY_NODE_GATE_INHERIT_TAIL` (:125) | shared tail | F-GATEWORDS |
| 28 | `STRING_GLOBALID_STRATEGIES` (:134) | 3-strategy vocabulary | F-STRATVOCAB |
| 29 | `DEFAULT_GLOBALID_STRATEGY` (:135) | `"model"` default | F-STRATVOCAB |
| 30 | `_validate_set_sidecar` (:138) | shared subclass gate | F-SIDECAR |
| 31 | `_validate_filterset_class` (:162, in-function import) | FilterSet arm | F-SIDECAR |
| 32 | `_validate_orderset_class` (:189, in-function import) | OrderSet arm | F-SIDECAR |
| 33 | `_validate_connection` (:218) | connection grammar + gate | F-CONN + C1 facet |
| 34 | `_validate_cursor_field` (:266, in-function import) | cursor stage-1 + gate | F-CURSOR |
| 35 | `_validate_relation_shapes` (:314) | shapes stage-1 + gate | F-RSHAPES1 + C1 facet |
| 36 | `_GLOBALID_CALLABLE_PARAMS` (:373) | encoder triple | F-STRATVOCAB |
| 37 | `_validate_globalid_strategy` (:376) | one validator, two sources | F-STRAT1 |
| 38 | `_validate_globalid_callable` (:436) | arity + sync-ness | F-STRAT1 |
| 39 | `_NODEID_STRING_RE` (:483) | token matcher | F-NODEID |
| 40 | `_has_node_id_marker` (:486) | resolved-form check | F-NODEID |
| 41 | `_id_annotation_is_relay_node_id` (:501) | two-form recognition | F-NODEID |
| 42 | `_is_relay_shaped` (:545) | relay-shape predicate | F-RELAYPRED |
| 43 | `_meta_attr` (:561) | contained Meta read | F-METAATTR |
| 44 | `_is_auto_annotation` (:580) | 3-spelling marker | F-AUTO |
| 45 | `class DjangoType` (:609: docstring, `_is_default_get_queryset`, `__init_subclass__`, `get_queryset`, `has_custom_get_queryset`) | collection pipeline + hook trio | F-COLLECT + F-QS |
| 46 | `_detect_custom_get_queryset` (:864) | MRO override scan | F-QS |
| 47 | `_normalize_fields_spec` (:876) | fields ladder | F-NORM |
| 48 | `_normalize_sequence_spec` (:904) | shared sequence ladder | F-NORM |
| 49 | `_consumer_assigned_fields` (:941) | assigned-override walk | F-ASSIGN |
| 50 | `_meta_optimizer_hints` (:1005) | hints mapping read | F-HINTREAD + C1 facet + C2 |
| 51 | `_format_unknown_fields_error` (:1031) | typo format | F-TYPOFMT |
| 52 | `_INTERFACES_SHAPE_ERROR_LEAD_IN` (:1052) | shared lead-in | F-IFACE |
| 53 | `_interfaces_shape_error` (:1058) | two-site formatter | F-IFACE |
| 54 | `_RELAY_NON_INTERFACE_REMEDIATION` (:1072) | shared tail | F-IFACE |
| 55 | `_RELAY_CONNECTION_HELPER_DESCRIPTION` (:1078) | shared description | F-IFACE |
| 56 | `_RELAY_NON_INTERFACE_HELPERS` (:1090) | 6-row table | F-IFACE |
| 57 | `_validate_interfaces` (:1113) | interfaces validation | F-IFACE |
| 58 | `class _ValidatedMeta` (:1206: docstring + 15 slots) | snapshot record | F-META |
| 59 | `_validate_meta` (:1233) | Meta orchestration | F-META |
| 60 | `_validate_optimizer_hints` (:1413) | hints validation | F-HINTVAL + C2 |
| 61 | `_selected_meta_targets` (:1482) | unknown/excluded skeleton | F-TARGETS |
| 62 | `_validate_nullability_override_targets` (:1526) | override stage-2 | F-NULL + C3 identity facet |
| 63 | `_validate_filesystem_path_targets` (:1620) | path-opt-in stage-2 | F-FSPATH |
| 64 | `_validate_relation_shape_targets` (:1687) | shapes stage-2 | F-RSHAPES2 |
| 65 | `_select_fields` (:1758) | field selection | F-SELECT |
| 66 | `_build_annotations` (:1827) | annotation synthesis | F-SYNTH + C3 suppression facet |

Rules: 29 file-local (F-MECH, F-METAKEYS, F-SHAPES, F-GATEWORDS,
F-STRATVOCAB, F-SIDECAR, F-CONN, F-CURSOR, F-RSHAPES1, F-STRAT1,
F-NODEID, F-RELAYPRED, F-METAATTR, F-AUTO, F-COLLECT, F-QS, F-NORM,
F-ASSIGN, F-HINTREAD, F-TYPOFMT, F-IFACE, F-META, F-HINTVAL, F-TARGETS,
F-NULL, F-FSPATH, F-RSHAPES2, F-SELECT, F-SYNTH); 1 adoption (C1 into
open `hostile-mapping-hardening`); 5 convergences (C2
`optimizer-hint-shape`, C3 `relay-pk-suppression-read-mirror`
UNAPPLIED, C4 `type-registry-finalize-gate`, C5
`relay-node-target-guard`, C6 `generated-choice-enum-name-template`);
1 new holding family (FAM-NEW `graphql-name-gate`); 22 rejections
(R1–R21 + R-MAINT1). Index rows named for Worker-0: 53 (29 file-local +
1 new family + 1 converge + 22 rejected).

### Challenges

Each change posited against the rule's own variation axes; the count
is authoritative definitions only. Consumers, oracles, projections
listed, never counted. All bodies judged at HEAD bytes.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F-SIDECAR skeleton | accept non-subclass sidecars | **1** (`_validate_set_sidecar` gate) | independent |
| C2 | F-SIDECAR wording | reword `must be {article} … subclass` | **1** (skeleton message) | independent |
| C3 | F-SIDECAR imports | hoist the FilterSet/OrderSet imports | **0** — refused: closes documented load cycles | independent |
| C4 | F-CONN grammar | admit a second sub-key beside `total_count` | **1** (unknown-list + reader) | independent |
| C5 | F-CONN copy | stop returning `dict(connection)` | **1** (this return) | independent |
| C6 | F-CURSOR ladder | accept `__`-traversal order strings | **1** here for shape (keyset references shared) | independent |
| C7 | F-STRAT1 framing | reword the Meta-side strategy message | **1** here (setting framing untouched) | independent |
| C8 | F-STRAT1 arity | encoders take `(type, obj)` | **1** (triple + bind move together) | independent |
| C9 | F-STRATVOCAB set | add a fourth string strategy | **1** for vocabulary (payload memberships are the R8 split) | independent |
| C10 | F-NODEID forms | accept `x.NodeID[int]` prefixed lookalikes | **1** (regex anchor) | independent |
| C11 | F-NODEID marker | Strawberry renames `NodeIDPrivate` | **1** (`_has_node_id_marker`) | independent |
| C12 | F-RELAYPRED arms | drop the direct-inheritance arm | **1** (predicate; 5 composed call sites follow) | independent |
| C13 | F-METAATTR scope | contain `Meta.__dict__` reads too | **1** (this helper) | independent |
| C14 | F-AUTO spellings | recognize `sb.auto` aliases | **1** (refused by design: PEP 563) | independent |
| C15 | F-GATEWORDS text | reword the gate lead/tail | **1** (constants; in-file + testing/relay follow by name) | independent |
| C16 | F-QS detection | detect overrides via `getattr` compare | **1** (detector + sentinel stamp) | independent |
| C17 | F-NORM shapes | `Meta.exclude` rejects sets | **1** (shared ladder gate) | independent |
| C18 | F-NORM fields | `Meta.fields` accepts a bare string name | **1** (fields ladder) | independent |
| C19 | F-ASSIGN gate | accept non-`StrawberryField` shadows | **1** (shadow rejection) | independent |
| C20 | F-TYPOFMT shape | drop the `Available:` tail | **1** (formatter; 5 call sites follow) | independent |
| C21 | F-IFACE table | reject a 7th relay helper | **1** (table row) | independent |
| C22 | F-IFACE singles | drop single-class acceptance | **1** (normalization branch) | independent |
| C23 | F-META keys | add an 18th allowed key | **1** (vocabulary + 1 validator) | independent |
| C24 | F-META order | run interfaces before the model gate | **1** (orchestration) | independent |
| C25 | F-HINTVAL scope | allow scalar-field hints | **1** (relation-membership gate) | independent |
| C26 | F-TARGETS guards | collapse unknown/excluded into one error | **1** (skeleton; 3 callers follow) | independent |
| C27 | F-SHAPES default | default flips to `"list"` | **1** (constant; finalizer follows by name) | independent |
| C28 | F-SELECT order | selection follows `fields` order, not `_meta` | **1** (return walk) | independent |
| C29 | F-SYNTH deferral | eager-bind relations again | **1** (refused: spec-018 trap) | independent |
| C30 | F-SYNTH tri-state | a fourth nullability state | **1** here + honoring consumers (converters listed) | independent |
| C31 | F-COLLECT merge | consumer annotations lose the merge | **1** (merge line) | independent |
| C32 | F-METAKEYS sets | promote a deferred key | **1** (vocabulary move) | independent |
| C33 | F-RSHAPES1 tails | unify the two remediation tails | **1** (this gate's tail) | independent |
| C34 | FAM-NEW grammar | allow the `__` prefix | **2** (base.py :1295 + definition.py :257) | candidate → holding family |
| C35 | FAM-NEW ladder | drop the empty-name arm | **2** (same pair) | candidate → holding family |
| C36 | FAM-NEW messages | reword the Meta.name message | **1** (per-subject; stays separate) | independent facet |
| C37 | C3 suppression | relation pks become suppressible | **2** (performer branch + predictor) | candidate → UNAPPLIED family |
| C38 | C3 identity | pk identity reads `attname` not `name` | **3** spellings (2 here + predictor) | candidate → UNAPPLIED family |
| C39 | C1 mapping gate | mappings must materialize before key checks | joins open `hostile-mapping-hardening` | adoption |
| C40 | R19 conventions | router factories take `(schema, request)` | **1** (routers; globalid bind untouched) | independent — rejected pair |
| C41 | R10 verbs | registration refusal rewords | **1** (this gate; sibling gates untouched) | independent — rejected pair |
| C42 | R-MAINT1 stance | DjangoType gates `isinstance(meta, type)` | **1** would be new (no second site today) | routed to the maintainer |

## Findings

Proof posture for every finding below: `static-reviewed` (HEAD-byte
body reads + permanent oracle pins cited; no behavior was executed
except the R1 interpreter micro-probe, read-only, cited inline). No
new structural gate is proposed by any finding — a file item owes
none; each file-local row names the existing oracles that fail on
divergence, and each candidate names the disjoint oracle sets that
prove count 2 today. Per-finding pins are 12-char prefixes of the
Freshness table.

### Freshness fingerprints

HEAD governs every verdict; worktree hashes prove the dirt was
fingerprinted, never judged. Read depth: `full` = whole file at HEAD
bytes, `regions` = cited regions, `census` = vocabulary sweep +
pin lines.

| Input | HEAD | Worktree | State | Depth |
|---|---|---|---|---|
| types/base.py (target) | `dda91365a7e8` | `dc67f084cbc9` | dirty (hunt + maintainer) | full (2015 lines) |
| types/__init__.py | `1bf69028dbdc` | same | clean | full |
| types/converters.py | `058f10813927` | `f6cadb0856c7` | dirty | regions |
| types/definition.py | `fa6c4d330e72` | `1c59a3feec53` | dirty | regions |
| types/finalizer.py | `de34ae2aaed1` | `b9d8acb2b942` | dirty | regions |
| types/relations.py | `5e9b5cdbc7fb` | same | clean | full |
| types/relay.py | `524398622354` | `4b2a9df59d6d` | dirty | regions |
| types/resolvers.py | `72d62dc4ebfe` | `640905c63f46` | dirty | regions |
| registry.py | `81bd561c99cb` | `492654d219d1` | dirty | regions |
| keyset.py | `df4b5e2f105c` | `279ad7b089de` | dirty | regions |
| exceptions.py | `e06b0b7f776e` | `206e9f8d914f` | dirty | regions |
| conf.py | `c6ad46aa3f0c` | `ae3de0a36e2f` | dirty | regions |
| connection.py | `4894f90fb296` | `68d1ea2c325e` | dirty | regions |
| list_field.py | `21380eb72364` | `450e87cde13e` | dirty | regions |
| relay.py | `c3c5aea52768` | `e75e2b66a9b4` | dirty | regions |
| optimizer/hints.py | `da46ef891ccd` | `8b545718c2f7` | dirty | regions |
| optimizer/field_meta.py | `18ea719a6141` | `bcddf517b014` | dirty | regions |
| optimizer/walker.py | `75f9c6b65ed1` | `d5759ef8533a` | dirty | census |
| optimizer/nested_planner.py | `b4dfd4a6f610` | `d32d1b7bd872` | dirty | census |
| utils/typing.py | `de6309f6cb59` | `a672cd6b4f5c` | dirty | regions |
| utils/querysets.py | `3616927de2bc` | `8fc556d582b3` | dirty | census |
| filters/sets.py | `993e887a7001` | `e47c6758e540` | dirty | regions |
| filters/base.py | `ba52351c2844` | `3b1dcbced106` | dirty | regions |
| filters/inputs.py | `82b52d97b8f8` | `a932dbf85d89` | dirty | census |
| orders/sets.py | `6044ab1a11c7` | `60859f2d5452` | dirty | regions |
| forms/sets.py | `36ce80b4fef4` | `2642a6470217` | dirty | regions |
| forms/inputs.py | `6418753d6db1` | `259afbb2d5c7` | dirty | census |
| mutations/sets.py | `7800bd530f2d` | `21c15c0b92c6` | dirty | regions |
| mutations/inputs.py | `fc4420475f40` | `840da733f956` | dirty | census |
| management/commands/inspect_django_type.py | `2807d0fc9d75` | `bb63204cca61` | dirty | regions |
| testing/relay.py | `df0dc72a1788` | `f807bf92fbc4` | dirty | regions |
| sets_mixins.py | `ad8987ea2fb1` | `088ddab0c0f6` | dirty | regions |
| routers.py | `7d5e48148702` | `e18772f76bee` | dirty | census |
| scalars.py | `5e354042d405` | `5da8c1405232` | dirty | census |
| tests/types/test_base.py | `0d070aee0513` | `bb56c89bbcad` | dirty | counts + pins |
| tests/types/test_relay_interfaces.py | `515ebce54705` | `3ffb75b82487` | dirty | counts + pins |
| tests/types/test_definition_order.py | `aff87c5211e9` | same | clean | counts + pins |
| tests/types/test_finalizer.py | `ad82b908d77b` | `3eeb6d4c8521` | dirty | counts |
| tests/types/test_converters.py | `c2ff9fca8c66` | `ddf24f5997a5` | dirty | counts |
| tests/types/test_relations.py | `2e18880ad7f4` | same | clean | counts |
| tests/types/test_resolvers.py | `346e945daf15` | `d78d605f1dc7` | dirty | counts |
| tests/types/test_generic_foreign_key.py | `5520ca02dd01` | same | clean | counts |
| tests/types/test_definition_relations.py | `196e783d1d87` | `fee20cf81674` | dirty | counts |
| tests/management/test_inspect_django_type.py | `9b1360d0b62d` | `a91b1e92ad74` | dirty (owned gate) | gate lines (worktree, by content) |
| tests/forms/test_sets.py | `7d4c0da6722f` | `dca57bfcd255` | dirty | pin lines |
| tests/mutations/test_sets.py | `1c5fcb0787e7` | `69668c00e65d` | dirty | pin lines |
| docs/GLOSSARY.md | `3413edc36ccf` | same | clean | anchor rows |
| docs/README.md | `1497164f903d` | `30978c34f63a` | dirty | example lines |
| docs/SPECS/spec-015-relay_interfaces-0_0_5.md | `317debd68536` | same | clean | Decision 4 + slices |
| docs/SPECS/appx/spec-015-rationale.md | `c11f901b7b56` | same | clean | `:100` renumber record |
| docs/SPECS/spec-011-stub.md | `fb30803a3375` | same | clean | header (D1) |
| docs/dry/dry-0_0_15.md (plan) | `ba411b27ce18` | `f2713d766e9e` | dirty (cycle) | index + ledger + runs |
| prior artifact [dry-rule-relay-pk-suppression-read-mirror.md][rule-relay-pk-mirror] | — (untracked) | `0f48ee970f52` | worktree-only | owner record + triggers |
| prior artifact [dry-file-utils__policies.md][file-policies] | — (untracked) | `0a41dec28bc2` | worktree-only | F3/L1/R3 (triggers) |
| prior artifact [dry-file-testing__relay.md][file-testing-relay] | — (untracked) | `5c08128ba491` | worktree-only | F3/R1/R4 (postures) |
| prior artifact [dry-file-orders__sets.md][file-orders-sets] | — (untracked) | `53a7a7fb0b2a` | worktree-only | single-file-family precedent |
| prior artifact [dry-file-rest_framework__sets.md][file-rf-sets] | — (untracked) | `75b817674c8e` | worktree-only | ADOPT precedent + N3 |
| prior artifact [dry-file-optimizer__join_taxonomy.md][file-join-taxonomy] | — (untracked) | `867a42924c61` | worktree-only | attname-rejection trigger |
| prior artifact [dry-file-optimizer__nested_fetch.md][file-nested-fetch] | — (untracked) | `4b330e42c0d4` | worktree-only | strategy-auto trigger |
| prior artifact [dry-file-filters__sets.md][file-filters-sets] | — (untracked) | `dd5d97390d2a` | worktree-only | R-m1..R-m4 scope check |

Any fingerprint change reopens the citing finding.

### F-MECH — module mechanics (file-local)

Members 0–21: the module docstring (consumer surface + 5-step
pipeline projection) and the 21 import statements binding 33 names.
Every import is a consumer edge to its owner (stdlib, Django,
Strawberry, or the sibling/parent modules named in System trace);
the three in-function imports (FilterSet, OrderSet, keyset
references) stay function-scoped by the documented do-not-hoist
cycle rationale (challenge C3 refuses hoisting: each hoist closes a
load cycle — `types -> filters -> types`, `types -> orders ->
types`, order-dependence on keyset). No `__all__` (regular module,
not a leaf). Challenge: posit a 34th import — each binding is used
at least once (verified by body read); posit moving any binding to
module top — C3. Oracles: collection behavior across
`tests/types/test_base.py` (148 tests) pins the pipeline the
mechanics serve. Freshness: target `dda91365a7e8`.

Note (future trigger, no row): `utils/truth.py` does not exist at
HEAD, so no shared-reader consolidation is available to the
`getattr`/`isinstance` sites here; reconsider when the hunt
truth-migration lands.

### F-METAKEYS — Meta-key vocabulary (file-local)

Members 22–23 + the `_validate_meta` guard facet: `DEFERRED_META_KEYS`
(3 reserved keys), `ALLOWED_META_KEYS` (17 keys), and the comment
recording that the six net-new keys were never deferred. One
vocabulary, one definition; the only production readers are the two
guards in `_validate_meta` (`declared & DEFERRED`,
`declared - ALLOWED - DEFERRED`); oracles pin membership from
outside (`tests/mutations/test_sets.py` :1253–1264 asserts disjoint
mutation keys, clean-read at HEAD `1c5fcb0787e7`). Challenges C23/C32
count 1. Distinct: the write-flavor key sets are intentionally
disjoint (R1). Freshness: target `dda91365a7e8`.

### F-SHAPES — relation-shape vocabulary (file-local)

Members 24–25: `RELATION_SHAPE_VALUES` (`list`/`connection`/`both`)
and `DEFAULT_RELATION_SHAPE` (`connection`, with the spec-047
secure-default rationale comment). Single source for the stage-1
typo guard, the finalizer Phase-2.5 default
([types-finalizer][types-finalizer] :709 follows by name), and the
error text. Challenge C27 counts 1. Oracles: shape + default rows in
[test-base][test-base]. Freshness: target `dda91365a7e8`,
finalizer `de34ae2aaed1`.

### F-GATEWORDS — Relay-gate wording (file-local)

Members 26–27: `_RELAY_NODE_GATE_LEAD` + `_RELAY_NODE_GATE_INHERIT_TAIL`.
One literal pair; compose sites: the connection gate, the
globalid gate, the cursor gate (lead+tail), the relation_shapes gate
(lead + own tail), and [testing-relay][testing-relay] :95–96 (lead +
tail, verified consumer). Challenge C15 counts 1 — a rewording moves
the constants; every site follows by name. The relay.py/connection.py
fifth-guard variants stay inline by recorded separation (R4).
Freshness: target `dda91365a7e8`, testing/relay `df0dc72a1788`.

### F-STRATVOCAB — strategy vocabulary + encoder triple (file-local)

Members 28–29 + 36: `STRING_GLOBALID_STRATEGIES`, the `"model"`
default, and `_GLOBALID_CALLABLE_PARAMS`. Single source for the
validator, the encoder default ([types-relay][types-relay] :413–420
follows by name), and the decode-shape enforcement. The triple is
shared by the validator message and the install closure so arity
text and check stay in lockstep. Challenge C9 counts 1 for
vocabulary; the payload-shape memberships are the R8 split.
Freshness: target `dda91365a7e8`, types/relay `524398622354`.

### F-SIDECAR — set-sidecar gate (file-local)

Members 30–32: the shared `_validate_set_sidecar` skeleton (subclass
check + `must be {article} … subclass` wording) with two wrapper
arms keeping their own cycle-safe imports and `None` short-circuits.
One body, two callers — the sharing already exists. Challenges C1–C3
count 1 (C3 refuses hoisting). The caller-spelled article is the R12
split from derivation. Oracles: sidecar rows in [test-base][test-base].
Freshness: target `dda91365a7e8`.

### F-CONN — connection-dict grammar (file-local + C1 facet)

Member 33: `None` short-circuit → dict gate → unknown-subkey reject
→ `total_count` bool gate → relay gate → defensive `dict()` copy.
One grammar, one definition; read by
[connection][connection]`::_connection_type_for`. Challenges C4/C5
count 1 (the copy idiom is independent per site — a change to this
copy moves 1). The dict-gate + unknown-key arm is a C1 adoption
facet (mapping hardening member). The bool gate is the R21
converge facet. Freshness: target `dda91365a7e8`,
connection `4894f90fb296`.

### F-CURSOR — cursor-field stage-1 (file-local)

Member 34: `None` short-circuit → non-string-sequence ladder →
`tuple()` materialize → non-empty all-`str` gate → shared
`validate_cursor_field_references` (one body in [keyset][keyset],
called by both stages) → relay gate → entries tuple. Stage-2
(columns) lives in [keyset][keyset]; the split is by timing
(unsettled model at class creation), not by copy. Challenge C6
counts 1. The ladder-vs-ladder split is R13. Freshness: target
`dda91365a7e8`, keyset `df4b5e2f105c`.

### F-RSHAPES1 — relation-shapes stage-1 (file-local + C1 facet)

Member 35: `None` short-circuit → dict gate → per-key `str` guard →
per-value vocabulary guard with the `isinstance`-first unhashable
rule → relay gate with the spec-pinned "or remove the key." tail →
defensive copy. Stage-2 ([F-RSHAPES2](#findings)) and the finalizer
Decision-6 check complete the flow. Challenge C33 counts 1. This is
the mapping arm the open `hostile-mapping-hardening` family already
names as a partial member — fresh evidence for the sweep in C1
(policies F3 cited this file at `91c58747`; re-verified at
`dda91365a7e8`). Freshness: target `dda91365a7e8`.

### F-STRAT1 — GlobalID strategy validation (file-local)

Members 37–38: the single validator for both sources (Meta path via
`_validate_meta`, setting path via
[types-relay][types-relay]`::_validated_globalid_setting`, which
passes `relay_shaped=True`/`meta=None` and is read once per
finalization into the registry snapshot) plus the callable arity +
sync-ness check composing `is_async_callable`
([utils-typing][utils-typing]) and `inspect.signature().bind()`.
One validator, two framings. Challenges C7/C8 count 1; the router
arity twin is R19. Oracles: strategy + callable rows in
[test-base][test-base] / [test-relay-interfaces][test-relay-interfaces].
Freshness: target `dda91365a7e8`, types/relay `524398622354`,
utils/typing `de6309f6cb59`.

### F-NODEID — NodeID annotation recognition (file-local)

Members 39–41: the `(?:^|\\.)NodeID\\[` token matcher (import-time
compile), the `Annotated[T, NodeIDPrivate()]` check (sole
`NodeIDPrivate` consumer package-wide — census 1 module), and the
two-form recognizer that never calls `get_type_hints` (sibling
annotations cannot mask `id`; pinned by
`test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`
at [test-definition-order][test-definition-order] :1212, clean
`aff87c5211e9`). Challenges C10/C11 count 1. Freshness: target
`dda91365a7e8`.

### F-RELAYPRED — relay-shaped predicate (file-local)

Member 42: `_is_relay_shaped(cls, interfaces)` — tuple arm (any
`relay.Node` subclass, so `CustomNode` counts) OR direct-inheritance
arm. One predicate; composed call sites: `_validate_meta` :1342,
`__init_subclass__` :738, `_build_annotations` :1928,
[list-field][list-field] :240 (shared by the connection + node
fields), [inspect][inspect] :295. Challenge C12 counts 1 — every
site follows by name. The post-injection MRO check (R5) and the
id-column probe (R6) are distinct contracts. Freshness: target
`dda91365a7e8`, list_field `21380eb72364`, inspect `2807d0fc9d75`.

### F-METAATTR — contained Meta read (file-local)

Member 43: every `Meta` attribute read routes through `_meta_attr`,
so a hostile metaclass `__getattr__` surfaces as `ConfigurationError`
instead of leaking raw. One reader, 21 call sites in-file.
Challenge C13 counts 1. The raw-read flavors are R17. Freshness:
target `dda91365a7e8`.

### F-AUTO — `auto` marker (file-local)

Member 44: instance + `"auto"` + `"strawberry.auto"` spellings, with
the `x.auto` refusal (foreign attribute keeps its meaning) and the
alias refusal (PEP 563). One recognizer; the fan-out (unselected /
assigned / drop) lives in F-COLLECT. Challenge C14 counts 1. The
strategy-`"auto"` twin is R11. Freshness: target `dda91365a7e8`.

### F-COLLECT — subclass collection pipeline (file-local)

Member 45 (`__init_subclass__`): sentinel stamp before the
`Meta`-absent early return (abstract bases flip the flag; pinned by
`test_has_custom_get_queryset_inherits_through_abstract_base_without_meta`
at [test-base][test-base] :1660) → finalized-registration gate →
`_validate_meta` → select → hints → `field_map` → annotation-keys
gate → `auto` fan-out → four-corner union → stage-2 validators →
Relay-id collision guard (H1 assigned / H2 non-NodeID annotation) →
synthesize → `DjangoTypeDefinition` build (single construction site
per [types-definition][types-definition]) → `register_with_definition`
→ pending registration → `{**synthesized, **consumer}` merge →
`__django_strawberry_definition__` stamp → `install_is_type_of`.
One pipeline; stage order is load-bearing (selection before
targets, union before synthesis). Challenge C31 counts 1. The
finalized-gate siblings are R10. Freshness: target `dda91365a7e8`,
registry `81bd561c99cb`, definition `fa6c4d330e72`.

### F-QS — queryset-hook contract (file-local)

Member 45 hook trio + 46: the identity `get_queryset`, the
`_is_default_get_queryset` stamp, `has_custom_get_queryset` (stamp
read pre-definition, definition read post-definition), and the MRO
override scan stopping at `DjangoType`. One detector; consumers are
the optimizer downgrade ([walker][walker], [nested-planner][nested-planner]),
[types-resolvers][types-resolvers], and
[types-finalizer][types-finalizer] (census: 6 files read
`has_custom_get_queryset`). Challenge C16 counts 1. The dispatch
MRO walks are R14. Freshness: target `dda91365a7e8`.

### F-NORM — spec normalization (file-local)

Members 47–48: `_normalize_fields_spec` (the `__all__`-string-or-
sequence ladder) and the shared `_normalize_sequence_spec`
(exclude + nullable + required + filesystem keys route through the
one body with the rejecting key named). The 4-key sharing already
exists; sets are accepted because all four keys are sets
semantically, strings refused. Challenges C17/C18 count 1 each.
The cursor ladder split is R13. Freshness: target `dda91365a7e8`.

### F-ASSIGN — assigned-override collection (file-local)

Member 49: walks every selected field against `cls.__dict__`,
sorting `StrawberryField` assignments into relation/scalar sets and
raising the uniform shadow rejection otherwise. One of the four
override-collection corners (the other two live in F-COLLECT; the
contract docstring enumerates all four). Challenge C19 counts 1.
Oracles: override rows in [test-base][test-base]. Freshness: target
`dda91365a7e8`.

### F-HINTREAD — optimizer-hints read (file-local + C1 facet + C2)

Member 50: `None` → `{}`; Mapping gate; per-key `str` guard with the
model-name prefix derivation; `dict()` copy. One read; validated by
F-HINTVAL. The mapping facets join C1; the `OptimizerHint` value
gate in F-HINTVAL converges on C2. Challenge: posit a second hints
reader — package census finds exactly one (`_validate_meta` :1340).
Freshness: target `dda91365a7e8`.

### F-TYPOFMT — unknown-fields format (file-local)

Member 51: `"{Model}.Meta.{attr} names unknown fields: {unknown}.
Available: {sorted(available)}."` Single formatter; call sites:
`_select_fields` ×2 (fields/exclude), `_validate_optimizer_hints`
×2, `_selected_meta_targets` (serving 3 validators). Challenge C20
counts 1. Package census: the only `"Available:"` producer
(1 site). Freshness: target `dda91365a7e8`.

### F-IFACE — interfaces validation (file-local)

Members 52–57: the shape lead-in + two-site formatter, the
Decision-8 remediation tail + shared connection description, the
6-row non-interface helper table (identity-matched: `NodeID` is an
`Annotated` alias), and `_validate_interfaces` (None/empty/single/
tuple-list normalization → string-entry → named-helper →
non-class → DjangoType → non-interface → duplicate-by-`id`).
Single normalization returning the tuple `F-META` threads onward.
Challenges C21/C22 count 1. Oracles: 126 tests in
[test-relay-interfaces][test-relay-interfaces]. Freshness: target
`dda91365a7e8`.

### F-META — Meta validation orchestration (file-local)

Members 58–59: the 15-slot `_ValidatedMeta` snapshot (shape gates
run once per class) and `_validate_meta` (model → name → own-keys
`declared` vs MRO `has_fields`/`has_exclude` — the intentional
counterpart, documented do-not-unify → exclusivity → primary →
deferred → unknown → specs → hints → interfaces → relay bool →
sidecars → overrides + collision → path set → snapshot). One
orchestration; `description` reads through unvalidated (probed
absence: no flavor validates it — grep 0 — so no asymmetry).
Challenges C23/C24/C32 count 1. The flavor-guard twin is R1, the
model twin R20, the class-gate asymmetry R-MAINT1. Freshness: target
`dda91365a7e8`.

### F-HINTVAL — optimizer-hints validation (file-local + C2)

Member 60: non-`str` key re-check → unknown-against-model (via
F-TYPOFMT) → excluded-or-scalar-against-selected-relations (via
F-TYPOFMT) → non-`OptimizerHint` value reject. One validation; the
value gate enforces the C2 shape. Challenge C25 counts 1.
Freshness: target `dda91365a7e8`, hints `da46ef891ccd`.

### F-TARGETS — Meta-target skeleton (file-local)

Member 61: `_selected_meta_targets` — unknown-against-model (via
F-TYPOFMT keyed on `attr`) → excluded-against-selected (via the
caller's family-specific `excluded_error`) → `(selected_by_name,
sorted)` return; domain checks stay in the three callers
(F-NULL/F-FSPATH/F-RSHAPES2). One skeleton, three callers — the
sharing already exists. Challenge C26 counts 1. Freshness: target
`dda91365a7e8`.

### F-NULL — nullability-override targets (file-local + C3 facet)

Member 62: union → skeleton → per-name order (consumer-authored →
relay-pk → relation; relay precedes relation so a relation pk
reports the Relay reason). One stage-2. Challenge: posit a sixth
path — 1 site. The `relay_pk_name = model._meta.pk.name if
relay_shaped else None` identity read is the C3 identity facet (one
of three spellings). Freshness: target `dda91365a7e8`.

### F-FSPATH — filesystem-path targets (file-local)

Member 63: skeleton → consumer-authored → non-file-column (via
`_field_output_type_for(...) is None`, composing
[types-converters][types-converters] by name). One stage-2; every
non-working target raises (no silent no-op is the contract).
Challenge: posit a fourth path — 1 site. Freshness: target
`dda91365a7e8`, converters `058f10813927`.

### F-RSHAPES2 — relation-shape targets (file-local)

Member 64: skeleton → non-relation → single-valued (via
`field_map[name].is_many_side` — the same classifier the resolvers
and Phase-2.5 key on, so validator and synthesis cannot disagree) →
consumer-authored. Sorted iteration for deterministic messages.
Challenge: posit a fifth path — 1 site. Freshness: target
`dda91365a7e8`, field_meta `18ea719a6141`.

### F-SELECT — field selection (file-local)

Member 65: `__all__`-or-`None` → every concrete + relation field;
sequence → subset with typo guard; `exclude_spec` → complement with
typo guard; Django `_meta.get_fields()` order preserved; the one
walk reused by synthesis and the resolver attach. Challenge C28
counts 1. The input-shaping twin is R9. Freshness: target
`dda91365a7e8`.

### F-SYNTH — annotation synthesis (file-local + C3 facet)

Member 66: per-field dispatch — relation branch (authored
short-circuit → `related_model`-None GFK refusal, the single GFK
refusal site → always-defer `PendingRelation` per spec-018, never
eager-bind) / scalar branch (authored short-circuit → pk-suppress
skip → tri-state → `convert_field_output` with the path flag). One
synthesizer. Challenges C29/C30 count 1. The suppression branch +
`pk_name` identity read are the C3 performer facet (challenge
C37/C38 count 2 with the predictor). The enum-name seed
(`cls.__name__` threading) is the C6 consumer facet. Freshness:
target `dda91365a7e8`, converters `058f10813927`, relations
`5e9b5cdbc7fb` (clean).

### C1 — `hostile-mapping-hardening` (ADOPT into the OPEN family)

Following the verified resolvers-C11 / sets-ADOPT precedent (member
+ coverage note; the family item decides the owner with this member
in its sweep):

- **Contract.** Mappings crossing a trust boundary are type-gated,
  materialized defensively, and key-gated before downstream hashing
  — never a raw consumer exception past the boundary.
- **Sites + roles.** Owner: TBD by the family item (currently
  `utils/policies.py`, `conf.py`, `types/base.py`,
  `rest_framework/resolvers.py`, `rest_framework/sets.py`). This
  target's role: MEMBER — three facets, fresh evidence at
  `dda91365a7e8`: (a) F-CONN's arm (`dict` gate + unknown-
  subkey reject + `bool` value rule); (b) F-RSHAPES1's arm
  (`dict` gate + per-key `str` guard + per-value vocabulary with
  the `isinstance`-first unhashable rule — the partial member
  policies F3 named at `91c58747`, re-verified here); (c)
  F-HINTREAD's arm (`Mapping` gate + `str`-key guard + `dict()`
  copy). Same mechanism as the resolvers/sets members: each gate
  exists precisely because the gated map feeds key-hashing
  consumers.
- **Worker 0 transcription:** none — the family row already covers
  `types/base.py`. The three facets above ride with the adoption
  for the family sweep. No new family.
- **Challenges.** Gate-policy change (C39) moves with the family
  owner once chosen. Proof `static-reviewed` (three bodies +
  hostile-shape oracle rows in [test-base][test-base]).
- **Sweep notes (ride with the adoption, not defects):** the
  `dict` gates admit hostile dict *subclasses* (overridden
  `items()`/`__iter__`), and F-HINTREAD iterates a possibly hostile
  `Mapping`; no HEAD oracle pins subclass/iterator behavior, so the
  open family's scope call adjudicates. No contract row breaks today.
- **Freshness.** Target `dda91365a7e8`; policies member at
  `8c881c0a` (prior artifact `0a41dec28bc2`); conf.py `c6ad46aa3f0c`
  still byte-identical to the F3-cited blob.

### C2 — `optimizer-hint-shape` (CONVERGE, transcribes nothing)

F-HINTREAD/F-HINTVAL enforce the open family's shape: the value
gate (`isinstance(v, OptimizerHint)`) and the relation-membership
gate are enforcement sites of `optimizer/hints.py::OptimizerHint`.
The family row already covers `types/base.py`; this convergence
adds the enforcement-site evidence (fresh: hints `da46ef891ccd`,
value-gate body re-read). No `hint_is_skip` surface here (grep 0),
so the skip-predicate family is untouched. Transcribes nothing.

### C3 — `relay-pk-suppression-read-mirror` (CONVERGE onto the UNAPPLIED family)

- **Contract + variation.** Which field the Relay-pk suppression
  removes: a non-relation pk on a relay-shaped type, identified by
  `_meta.pk.name` (not attname). Varies on relation-ness and shape
  only.
- **Sites + roles.** Performer: F-SYNTH's suppress branch
  (relation branch first, then `suppress_pk_annotation and
  field.name == pk_name` skip on the scalar branch). Read mirror:
  [inspect][inspect]`::Command._is_suppressed_relay_pk` (inline
  3-conjunct: relation-first, `_is_relay_shaped` composed by name,
  `field.name == model._meta.pk.name`). Identity facet: the two
  in-file `_meta.pk.name` reads (F-NULL :1595, F-SYNTH :1937) plus
  the predictor's read. Consumers/oracles/projections (listed, not
  counted): the GFK/relation rows, the suppression oracles in
  [test-base][test-base], the worktree-only mirror gate
  (`_mirror_check` + `test_inspect_suppressed_pk_mirror_matches_synthesis`
  at worktree `a91b1e92ad74`, owned dirt, cited by content).
- **Challenges.** C37 counts **2** (performer + predictor); C38
  counts **3** spellings of the pk-name identity. Consumers follow;
  oracles are disjoint per half (synthesis rows vs table rows),
  proving count 2 today.
- **Fresh trigger checks on the standing UNAPPLIED record:** owner
  `types/base.py::_is_suppressed_relay_pk` still 0 hits
  package-wide (only the command's same-named method + call site);
  predictor still inline composing `_is_relay_shaped` (body
  re-read at `2807d0fc9d75`); mirror gate still worktree-only owned
  dirt; maintainer decision (a/b/c) still owed. All unfired.
- **Owner + lifetime.** Per the rule artifact
  (`0f48ee970f52`): `types/base.py::_is_suppressed_relay_pk` pure
  per-field predicate; blocked-on-hunt (performer lines hunt-dirty).
  This file item assigns only; no consolidation, no edit.
- **Worker 0 transcription:** the family has a `## Families` entry
  but no responsibility-index row — one converge row is named in
  `## Index rows for Worker-0` (status open, UNAPPLIED noted).
- **Freshness.** Target `dda91365a7e8`; inspect `2807d0fc9d75`;
  rule artifact `0f48ee970f52`.

### C4 — `type-registry-finalize-gate` (CONVERGE, transcribes nothing)

F-COLLECT's registration gate composes `registry.is_finalized()`
by name; the verified family owns the flag. Consumer posture only
(the per-verb gates stay separate — R10). Transcribes nothing.
Freshness: registry `81bd561c99cb`.

### C5 — `relay-node-target-guard` (CONVERGE, transcribes nothing)

The verified guard ([list-field][list-field]
`::_validate_relay_djangotype_target`, shared by the connection +
node fields) composes F-RELAYPRED by name for its relay arm — our
predicate is the guard's composed primitive, read once and returned
onward. Transcribes nothing. Freshness: list_field `21380eb72364`.

### C6 — `generated-choice-enum-name-template` (CONVERGE, transcribes nothing)

F-SYNTH threads `cls.__name__` as the `type_name` seed into
`convert_field_output` — the caller side of the open family's enum-
name template (candidate owner [types-converters][types-converters]).
Consumer posture only. Transcribes nothing. Freshness: converters
`058f10813927`.

### FAM-NEW — `graphql-name-gate` (NEW FAMILY for Worker-0)

- **Contract + variation.** A GraphQL type name is valid iff it is a
  non-empty string matching `_GRAPHQL_NAME_RE` with no `__` prefix;
  `str` subclasses normalize through `str.__str__`. Varies on the
  grammar only; messages stay per-subject (C36 counts 1 — the
  standing per-subject direction, not part of this family).
- **Sites + roles.** Owner: TBD by the family item (candidates:
  [types-definition][types-definition] via a pure
  `is_valid_graphql_name(normalized) -> bool` predicate both gates
  compose, keeping messages + normalization per site; or the status
  quo with the separation recorded at both sites). Definitions (2):
  [types-base][types-base] :1295 (`Meta.name` declaration gate:
  non-`str` → empty → regex+`__` trio) and
  [types-definition][types-definition] :257 (`graphql_type_name`
  derivation gate: same trio over the derived surface name).
  Consumers (listed): the 9 `graphql_type_name` consumer files
  (connection, filters/base, filters/inputs, finalizer, inspect,
  registry, relay, testing/relay, types/relay). Oracles (listed, disjoint per half — proving count 2):
  `Meta.name` rows in [test-base][test-base] ([test-base][test-base]
  :292–323) vs derived-name rows in
  [test-definition-relations][test-definition-relations] (:192, :565). Population closed: the `_GRAPHQL_NAME_RE.fullmatch`
  census is exactly these 2 production sites (the third `fullmatch`
  token, scalars' `_BIGINT_STRING_PATTERN`, is a different regex); the other
  `startswith("__")` sites are the R18 split (sanitize / dunder
  short-circuit, different contracts).
- **Challenges.** C34 (grammar) and C35 (ladder) count **2**; C36
  (messages) counts **1** and stays out. Single-file-family
  precedent: verified `active-terms-purity-agreement` (prior
  artifact `53a7a7fb0b2a`).
- **Migration sketch (family item's call).** Both gates compose the
  one predicate for the `fullmatch`-plus-`__` conjunct; the trio
  order, `str.__str__` normalization, and messages stay per site.
- **Behavioral proof.** `static-reviewed` (both bodies + disjoint
  oracle sets read at HEAD bytes; no execution — a file item runs
  no failability probe).
- **Structural gate.** Owed by the family item, not this file item;
  shape: a gate failing a third spelling of the conjunct (negative
  control: a hand copy of one gate's trio with a diverged arm —
  behavior oracles stay green, the gate goes red).
- **Coupling.** None (pure predicate + two call sites).
- **Freshness.** Target `dda91365a7e8`; definition `fa6c4d330e72`.
- **Worker 0 transcription:** one family index row + one
  `## Families` item, both spelled in `## Index rows for Worker-0`
  / `## Families`.

### R1 — Meta-guard vs write-flavor guard (rejected)

Our unknown-key guard (`declared - ALLOWED - DEFERRED`, own-keys
`meta.__dict__`, `f"Unknown Meta keys: {unknown}"`) vs
[mutations-sets][mutations-sets]`::reject_unknown_meta_keys`
(one-set `declared - allowed`, `vars(meta)` scan, per-flavor
framing, shared by all four write flavors). Contract differences:
two-set vs one-set vocabulary (deferred keys exist only here);
per-subject message grammar (CONVERGE with verified
per-subject-rejection-grammars on fresh evidence — still no owned
grammar at HEAD); non-`str` tolerance (the helper sorts defensively,
ours calls `k.startswith` — and non-`str` class-dict keys ARE
constructible: read-only probe `uv run python -W ignore` over
`type("X", (), {1: 2})` + `types.new_class` prints accepted/accepted,
`execution-verified`). Reconsideration trigger: the package adopts
one owned Meta-key-guard helper taking allowed+deferred sets.
Freshness: target `dda91365a7e8`, mutations/sets `7800bd530f2d`,
policies artifact `0a41dec28bc2`.

### R2 — wordings vs shared grammar (rejected)

The 72 `ConfigurationError` raise sites in this file stay per-key:
each names its subject, vocabulary source, and remediation.
CONVERGE with verified per-subject-rejection-grammars on fresh
evidence (the row already names this file's `Unknown Meta keys`;
re-checked: no owned message grammar at HEAD). Reconsideration
trigger: the package adopts one owned rejection-message grammar
(the row's standing trigger, unfired). Freshness: target
`dda91365a7e8`.

### R3 — except arms vs shared guard (rejected)

The 6 `except BaseException` arms (cursor `tuple()`, callable
inspect ×2, `_meta_attr` getattr, both normalizers' `tuple()`)
stay per-site: each wraps a different probe with different framing
and chaining. CONVERGE with the verified shared-except-guard (J1)
direction on fresh evidence. Reconsideration trigger: the standing
J1 trigger (a driver preserving per-site framing + chaining),
unfired. Freshness: target `dda91365a7e8`.

### R4 — gate wording vs factory wording (rejected)

The F-GATEWORDS constants (Meta-key remediation: "add `relay.Node`
to `Meta.interfaces`…") vs the [root-relay][root-relay] :341 /
[connection][connection] :2304 fifth-guard inline variants
(field-factory remediation: each factory names itself, passed as
`relay_error_message` into the shared guard). Contract difference:
Meta-key vs field-factory remediation subject; already recorded at
the owner comment (:120–124). Reconsideration trigger: factories
stop self-naming (one remediation text). Freshness: target
`dda91365a7e8`, relay `c3c5aea52768`, connection `4894f90fb296`.

### R5 — relay predicate vs post-injection check (rejected)

`_is_relay_shaped` (pre-injection: declared-tuple OR inheritance,
for class-creation timing) vs
[types-relay][types-relay]`::implements_relay_node` (post-injection
MRO check, for Phase-2.5 timing). Contract difference: timing —
each runs where the other would misread (a plain MRO check at
class creation rejects declared-but-uninjected `relay.Node`);
both docstrings record the split. Reconsideration trigger:
collection moves post-injection (single timing). Freshness: target
`dda91365a7e8`, types/relay `524398622354`.

### R6 — relay predicate vs id-column probe (rejected)

`_is_relay_shaped` (shape gate returning the shape fact) vs the
inline `isinstance(origin, type) and issubclass(origin, relay.Node)`
inside [types-definition][types-definition]`::_resolves_id_off_pk`
(fail-closed safety probe: hostile reads answer `True`, non-Node
answers `False`, and the tuple arm is meaningless there — the
origin is post-finalization). Contract difference: gate vs probe;
no interfaces tuple exists at the probe's site. Reconsideration
trigger: probe callers need tuple-declared shapes. Freshness:
target `dda91365a7e8`, definition `fa6c4d330e72`.

### R7 — pk-name vs pk-attname reads (rejected)

The three `_meta.pk.name` identity reads (F-NULL, F-SYNTH,
predictor — NAME compare for display/identity) vs the
`pk.attname` column readers owned elsewhere (the connection pk-alias
segment read and the filters prose mention are different uses — alias
resolution and a comment, not identity). CONVERGE with the
verified join-taxonomy six-`pk.attname`-readers rejection on fresh
evidence (name-vs-column split stands; prior artifact
`867a42924c61`). Reconsideration trigger: the standing trigger (an
identity read needing name+attname together), unfired. Freshness:
target `dda91365a7e8`.

### R8 — strategy vocabulary vs payload memberships (rejected)

`STRING_GLOBALID_STRATEGIES` (declared vocabulary: what a consumer
may configure) vs `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES`
(payload-shape memberships: what each strategy emits/accepts) and
the [filters-base][filters-base] acceptance derivation.
Contract difference: vocabulary vs encode/decode acceptance —
`callable`/`custom` are deliberately in neither membership (their
absence IS the no-decode contract; recorded on the shared set).
Reconsideration trigger: vocabulary and payload shapes collapse
(every strategy both declared and decodable). Freshness: target
`dda91365a7e8`, types/relay `524398622354`, filters/base
`ba52351c2844`.

### R9 — selection vs input shaping (rejected)

`_select_fields` (model-level `__all__` sweep for the type surface)
vs `FilterSet.get_fields` / `OrderSet` per-field `__all__` lookup
expansion for input shaping. CONVERGE with the DRY.md worked-
example separation (recorded at the `FilterSet.get_fields` owner:
one token, two contracts) on fresh evidence — the sweep feeds
`field_map`/synthesis, the expansion feeds input triples; a change
to either moves 1. Reconsideration trigger: a single field-set
derivation serving surface + shaping. Freshness: target
`dda91365a7e8`, filters/sets `993e887a7001`, orders/sets
`6044ab1a11c7`.

### R10 — finalized gates stay per-verb (rejected)

Five gates, five verbs: refuse-registration here (:628),
no-op short-circuit ([types-finalizer][types-finalizer] :861),
refuse-declaration ([mutations-sets][mutations-sets] :543),
cache-validity read ([types-definition][types-definition] :304),
refuse-mint ([testing-relay][testing-relay] stamp gate) — plus the
inspect table-print check. Contract difference: each gate's verb +
remediation belongs to its boundary; the FLAG is single-owned by
the verified `type-registry-finalize-gate` family (C4). Challenge
C41 counts 1. Reconsideration trigger: one shared gate verb.
Freshness: target `dda91365a7e8`, finalizer `de34ae2aaed1`,
mutations/sets `7800bd530f2d`, definition `fa6c4d330e72`,
testing/relay `df0dc72a1788`.

### R11 — `auto` vs strategy-`auto` (rejected)

Field marker `auto` (declare-but-infer, F-AUTO) vs the
nested-fetch strategy `"auto"` (connection-strategy selection).
CONVERGE with the verified nested_fetch strategy-vs-field-`auto`
rejection on fresh evidence (prior artifact `4b330e42c0d4`;
trigger re-checked unfired — no shared marker rule at HEAD).
Reconsideration trigger: the standing trigger. Freshness: target
`dda91365a7e8`.

### R12 — article declaration vs derivation (rejected)

`_validate_set_sidecar`'s caller-spelled `article` param ("a"/"an"
literals, the same idiom as the 116 package-wide `must be a`
literals in 40 files) vs `utils/policies.py::_article` (derives a/an from the
class-name initial). Contract difference: declaration vs
derivation — this site is NOT a second consumer of the derivation
(policies-L1 trigger re-checked: UNFIRED at HEAD); sharing the
private deriver would couple Meta validation to policy prose for
two literals (dependency direction wins, principle 7).
Reconsideration trigger: a third article-needing message, or either
site changing stance. Freshness: target `dda91365a7e8`, policies
artifact `0a41dec28bc2`.

### R13 — sequence ladders stay split (rejected)

`_normalize_fields_spec` (`__all__`-string-or-sequence),
`_normalize_sequence_spec` (set-accepting, shared by 4 keys), and
the cursor-field inline ladder (order-string vocabulary + keyset
references). Same-file intentional separation: accepted-shape sets
differ per subject, so the one shared body covers exactly the
identical contracts. Reconsideration trigger: accepted shapes
unify. Freshness: target `dda91365a7e8`.

### R14 — MRO walk vs dispatch walks (rejected)

`_detect_custom_get_queryset` (override detection: "does any base
below `DjangoType` define `get_queryset`") vs the
[types-converters][types-converters] `SCALAR_MAP` dispatch walks
(type→scalar lookup) vs the [sets-mixins][sets-mixins] declaration
inheritance scan (attr collection). Contract difference: three
different questions asked of three different MROs. Reconsideration
trigger: one owned MRO-walk helper (no such rule at HEAD).
Freshness: target `dda91365a7e8`, converters `058f10813927`,
sets_mixins `ad8987ea2fb1`.

### R15 — override gates vs surface audit (rejected)

The `StrawberryField` override gates here (:761 id-assignment,
:990 assigned walk — membership detection at collection) vs
[types-finalizer][types-finalizer] :268 (surface-name collection
for the camelCase collision audit at finalization). Contract
difference: membership vs names — the audit needs `graphql_name`
per field, which the stored sets do not carry. Reconsideration
trigger: the audit needs membership only. Freshness: target
`dda91365a7e8`, finalizer `de34ae2aaed1`.

### R16 — GFK posture vs flavor posture (rejected)

Our GFK-shaped refusal (unresolvable relation → `ConfigurationError`
at synthesis, the single refusal site) vs
[forms-inputs][forms-inputs] (skip to `None`) and
[mutations-inputs][mutations-inputs] (input-shaping error) handling.
Contract difference: type-surface refusal vs input-shaping policy
per flavor. Reconsideration trigger: one package GFK policy.
Freshness: target `dda91365a7e8`, forms/inputs `6418753d6db1`,
mutations/inputs `fc4420475f40`.

### R17 — containment vs raw flavor reads (rejected)

`_meta_attr` contains hostile metaclass reads at the type boundary;
every write/set flavor reads `Meta` raw (`getattr(meta, …)` census:
mutations, forms, filters — same posture package-wide). No contract
source (spec, glossary, owner prose, oracle) establishes containment
for the flavor seams — sets-N3 prior evidence trigger-checked
fresh (prior artifact `75b817674c8e`; still no source at HEAD; the
hunt truth-migration owns that decision and is worktree-only).
Not a defect: sibling behavior justifies the investigation, never
the verdict. Reconsideration trigger: a spec row extending
containment to flavor `Meta` reads, or the truth-migration landing.
Freshness: target `dda91365a7e8`.

### R18 — name gate vs sanitize and dunder (rejected)

The `Meta.name` reject-gate (invalid → raise) vs
[types-converters][types-converters] enum-member sanitization
(invalid → `MEMBER_`-prefix, never raise) vs [conf][conf]
`__getattr__` dunder short-circuit (introspection safety, not name
validity). Contract differences: reject vs sanitize vs
introspect — three rules sharing only the `__` token.
Reconsideration trigger: one owned name-safety rule. Freshness:
target `dda91365a7e8`, converters `058f10813927`, conf
`c6ad46aa3f0c`.

### R19 — arity bind vs router bind (rejected)

GlobalID-encoder arity (`signature(value).bind(*triple)` +
sync-ness, at type creation) vs [routers][routers] factory arity
(`signature(factory)` + `bind(schema=schema)` at router build;
patch-module `signature(...).parameters` probes are a third,
upstream-shape contract). Contract difference: three calling
conventions with per-subject framing over the shared stdlib
mechanism (which is already the sharing). Challenge C40 counts 1.
Reconsideration trigger: a third consumer convention needing the
same framing. Freshness: target `dda91365a7e8`, routers
`7d5e48148702`.

### R20 — model gate vs resolution chain (rejected)

Our direct `Meta.model` gate (must be a Django model class) vs the
[mutations-sets][mutations-sets] three-getattr resolution chain
(`Meta` → backing → backing-`Meta`, an overridable hook the
serializer flavor replaces). Contract difference: direct
declaration vs indirect overridable source. Reconsideration
trigger: `DjangoType` gains an indirect model source. Freshness:
target `dda91365a7e8`, mutations/sets `7800bd530f2d`.

### R21 — bool gates vs shared exact gate (rejected)

The `isinstance(…, bool)` gates (`primary`, `total_count`) stay
per-site. CONVERGE with the verified shared-exact-type-gate (J2)
direction on fresh evidence (no shared driver at HEAD; each gate
names its own key). Reconsideration trigger: the standing J2
trigger, unfired. Freshness: target `dda91365a7e8`.

### R-MAINT1 — Meta-class gate asymmetry (ROUTED TO MAINTAINER)

Write flavors gate `isinstance(meta, type)` with oracles
([mutations-sets][mutations-sets] :144–156,
[test-mutations-sets][test-mutations-sets] :1903,
[test-forms-sets][test-forms-sets] :1246/:1264); this file accepts
any namespace carrying a valid `model` (traced: a quacking
non-class `Meta` passes every gate end to end — no class check
anywhere on the path). No contract source (spec, glossary, owner
prose, oracle) establishes class-only `Meta` for `DjangoType`,
so per axis 6 this is ambiguity, not a defect: ROUTED TO MAINTAINER.
Trigger: a spec row requiring class-only `Meta` for `DjangoType`,
or the maintainer ruling the write-flavor posture extends here. Challenge C42.
Freshness: target `dda91365a7e8`, mutations/sets `7800bd530f2d`.

## Defects

- **D1 (minor, doc-only, unfixed).** Five stale `spec-011`
  citations in the target (:1119, :1121, :1252, :1864, :1982) plus
  the twin in [types-resolvers][types-resolvers] :669: `spec-011`
  now names "stale placeholder cleanup" ([spec-011-stub][spec-011-stub],
  clean `fb30803a3375`), while the relay-interfaces content moved
  to [spec-015][spec-015] (verified: Decision 4 + slices read at
  clean `317debd68536`) in the 2026-06-01 renumber whose rationale
  records "The in-source citations were not swept"
  ([spec-015-rationale][spec-015-rationale] :100, clean
  `c11f901b7b56`). Owner: `types/base.py` (+ the resolvers cite).
  All other spec cites in the target re-verified current (018,
  029, 030, 031, 032, 037, 047, 048 — every stem exists with its
  topic). For normal closeout homing (one card; prose-only).

Cleared near-misses (not defects): **N1** — set-order message
variance (`_normalize_sequence_spec` accepts sets, so which bad
entry a message names can vary by hash order; every order names a
genuinely bad value — no contract row breaks). **N2** —
unqualified messages (`Meta.primary must be a bool`, `Unknown Meta
keys`) vs model-qualified siblings — per-subject framing variance
allowed by the standing direction; no row breaks. **N3** — hostile
dict-subclass / `Mapping`-iterator behavior inside the C1 facets —
no HEAD oracle pins it; rides as C1 sweep notes for the open
family, not a defect.

## Pending execution

None. No `proof:` entries (all findings `static-reviewed` against
HEAD bytes + permanent oracles; the single R1 micro-probe is
read-only and already executed inline). No `gate:` entries.
Sharded/Postgres cells are inapplicable by construction: the target
defines class-creation validation + annotation synthesis with no
database, alias, or dialect decision (no queryset, no `using`, no
backend probe — verified by full body read).

## Judgment

Zero-edit file item: 67/67 members homed (29 file-local rows), 1 new
holding family (`graphql-name-gate`, count 2, population closed),
1 adoption into open `hostile-mapping-hardening` (3 facets, no
transcription — row already covers this file), 5 convergences (1
verbatim converge row for the rowless UNAPPLIED
`relay-pk-suppression-read-mirror`, 4 transcribing nothing), 22
rejections (7 CONVERGE with standing directions on fresh evidence
+ 14 fresh + 1 routed to the maintainer), 1 minor doc defect. The file is a
disciplined single-owner root: every shared spine (gate wording,
vocabularies, predicate, typo format, target skeleton, sidecar
skeleton, sequence ladder, deferral record) is already one body
composed by name, and the two genuine pairs found each have a
standing or newly-named home.

## Independent verification (Worker-2)

Address `dry/dry-file-types__base/verify-1`. HEAD `0c0537e2`
unmoved throughout; target HEAD `dda91365a7e8` / worktree
`dc67f084cbc9` both re-derived. All verdicts below were reached by
fresh reads of HEAD bytes (`git show HEAD:` + `git grep`, one
read-only interpreter probe); no workspace runs — the item is
static-decidable. Zero `.py` touched, so no ruff owed. My own trace
first, then reconciliation.

### Own trace (before Findings)

Sites: the collection root (`DjangoType.__init_subclass__` pipeline,
`_validate_meta` orchestration, per-key validators, `_ValidatedMeta`
snapshot), the relay-shape predicate + gate wording, the GlobalID
strategy vocabulary + two-source validator, the relation-shape
vocabulary, field selection + annotation synthesis with Relay-pk
suppression, the `get_queryset` hook trio, the override collection
corners, the target skeleton + three stage-2 validators, the NodeID
recognizer, and module mechanics. Roles: all definitions live here
except the composed primitives (`DjangoTypeDefinition`, converters,
`PendingRelation`, `install_is_type_of`, registry, `OptimizerHint`,
`FieldMeta`, `is_async_callable`, setting key, safe renders), which
are consumer edges. Homes I would choose: file-local for every
single-owned spine; the `Meta.name`/`graphql_type_name` grammar pair
to a new holding family (count 2: base.py :1295 + definition.py :257,
same trio, per-subject messages); the suppression performer +
predictor + pk-name identity to the standing UNAPPLIED
`relay-pk-suppression-read-mirror` family (count 2 / 3 spellings);
the three mapping arms to open `hostile-mapping-hardening`;
enforcement postures onto `optimizer-hint-shape`,
`type-registry-finalize-gate`, `relay-node-target-guard`, and
`generated-choice-enum-name-template` as convergences; the
non-class-`Meta` asymmetry to the maintainer (write flavors gate, no source
here). Definition counts per posited change: every W1 challenge
count re-derived — all file-local challenges 1 (counted on the
authoritative site, consumers listed), C34/C35 2, C37 2, C38 3
spellings, C42 would-be-1 routed.

### Reconciliation — all areas AGREE

- **Enumeration: AGREE.** `ast.Module.body` over the pinned HEAD
  blob = 67 statements; member-by-member the table matches (1
  docstring + 21 imports + 14 assignments + 31 defs; every #0–66
  line number confirmed). All 67 homed; multi-homes (#33/#35/#50/
  #60/#62/#66) are C-facets riding with their adoption/converge,
  correctly not double-counted. Two immaterial count notes: bound
  import names are 32, not 33; `_meta_attr` has 20 call sites + the
  def line, not 21. Neither moves a home.
- **Matrix: AGREE on all six axes.** Axis 2 inapplicability holds:
  no `AsyncFunctionDef` in the AST, zero `await` /
  `sync_to_async` / `asyncio` tokens, and the 10 `async` substring
  lines are exactly the import + strategy-validator prose/code W1
  names. Axes 1/3/4/5/6 discharged against the real surface; the
  six axis-6 absences each judged on its reason (the `dict()` pair
  is two independent 1-site copies — verified at :263/:363).
- **New family `graphql-name-gate`: AGREE.** Count 2 re-derived:
  both gates spell the non-`str` → empty → regex+`__` trio with
  `str.__str__` normalization and per-subject messages. Tested
  hard both directions: Meta side rejects empty/hostile/invalid
  (test-base :292–323), derived side rejects empty (:192),
  hostile (:565), and invalid grammar (:583 — completion note:
  W1's cite lists :192/:565 only; :583 is the grammar-conjunct
  pin the family item should also cite). Population closed by my
  own sweep: `_GRAPHQL_NAME_RE.fullmatch` = exactly these 2
  production sites (scalars' is a different regex); remaining
  `startswith("__")` sites are the verified R18 splits (conf
  dunder short-circuit, converters sanitize-prefix-never-raise).
  C36 message facet correctly stays out.
- **C1 adoption: AGREE — "transcribes nothing" is correct.** The
  open `hostile-mapping-hardening` row already covers
  `types/base.py`; the three facets (F-CONN arm, F-RSHAPES1 arm
  incl. the `isinstance`-first unhashable rule, F-HINTREAD arm)
  ride as member evidence per the verified ADOPT precedent. Sweep
  notes correctly non-defects (N3: no HEAD oracle pins
  dict-subclass behavior — verified by sweep).
- **Convergences: AGREE, all 5 on fresh evidence.**
  C2: value + relation-membership gates enforce the shape; row
  already covers this file; `hint_is_skip` grep 0 re-verified.
  C3: owner 0 hits package-wide (only the command method + call
  site), predictor still inline composing `_is_relay_shaped`
  (body re-read), mirror gate 0 hits at HEAD / 8 worktree-only,
  Families entry exists with no index row (verified — the
  remaining mentions are ledger/run prose), maintainer decision
  still owed. All triggers unfired; the verbatim converge row is
  owed and correctly worded. C4: `registry.is_finalized()`
  composed at :628, flag owned by the verified family. C5:
  list_field composes `_is_relay_shaped(target_type,
  definition.interfaces)` (shared by both fields per its
  docstring). C6: `cls.__name__` seed threading is a pure
  consumer facet — transcribes nothing per the converge
  convention (endorsed; the family sweep starts at converters).
- **Rejections: AGREE, all 22.** Every pair body re-read at HEAD:
  R1 helper is one-set + defensive non-`str`-tolerant sort with
  per-flavor framing, and I re-ran the constructibility probe
  myself (accepted/accepted, execution-verified); R4 variants
  self-name with the parenthesized tail shape the owner comment
  records; R5/R6/R8 bodies exist as described; R10 all five verbs
  confirmed (incl. the refuse-mint `definition.finalized` gate,
  which also confirms the F-GATEWORDS testing/relay consumer);
  R7 three `.name` reads confirmed; R12 `_article` confirmed
  (census note below); R13/R14/R15/R16/R17/R19/R20 bodies
  confirmed (R17 raw-`getattr(meta,…)` posture 15/2/1 across the
  three flavor files). The 7 CONVERGE rejections each name a
  standing row whose trigger I re-checked unfired (no owned
  grammar, no shared except/exact driver, no shared marker rule,
  name-vs-column split stands, worked-example separation holds).
  Every rejection carries its contract difference + trigger.
- **R-MAINT1 route: ENDORSED on my own negative sweep.** Write
  flavors gate via the one shared helper (both forms
  `_validate_meta` overrides compose it — verified at :578/:832;
  the test-forms pins apply to the mutation classes); target has
  zero class checks (grep 0) and a quacking namespace passes
  every gate. Contract sources all negative: spec sweep finds
  only `issubclass`-arg wordings (spec-042, bug_hunt doc —
  unrelated rules); glossary has no class-only-`Meta` anchor;
  owner prose is descriptive, never normative; oracles pin
  non-class rejection only for other rules. Ambiguity, not a
  defect — correctly routed with a sound trigger.
- **D1: ENDORSED as filed.** All 5 cites at the exact lines plus
  the resolvers :669 twin; stub names stale-placeholder cleanup;
  rationale :100 records the unswept citations; spec-015 Decision
  4 verified as the content's home; all 8 other cited stems exist
  with matching topics. Minor doc-only: the cites point readers
  at a contract the stub no longer owns (wrong stated reason),
  for normal closeout homing. No trust-boundary behavior breaks;
  no re-home warranted.
- **Near-misses: AGREE, all 3 cleared by my own checks.** N1: the
  ladder raises only on genuinely non-`str` entries (body read) —
  order variance names no innocent value. N2: framing variance
  allowed by the standing per-subject direction. N3: sweep above.
- **Index rows + Families: AGREE, 53/53.** 29 file-local + 1 new
  family + 1 converge + 22 rejected; each row's owner/status/
  trigger matches its finding (spot-verified row texts against
  F-METAKEYS, C3, R-MAINT1). Families item is the one new family in
  plan format; C1/C3/C2/C4/C5/C6 transcription claims all hold.
- **Freshness + Pending: AGREE.** 50/51 HEAD pins digit-for-digit
  (the 51st is E1, corrected); 8/8 prior-artifact pins match;
  HEAD unmoved; target worktree pin matches. `Pending: None`
  correct; sharded/PG inapplicable by construction endorsed (no
  queryset/alias/dialect surface — only the identity-hook
  annotations; `sync_to_async` grep 0).
- **Window attribution: AGREE, all concurrent/out-of-scope.** The
  window holds exactly the plan (Worker-0's dispatch + submission
  record, mine to leave alone), `review-0_0_15.md` (review-flow
  status/routes), `conf.py` + `tests/base/test_conf.py`
  (review-flow conf.py work: `-> Any` reader annotations + the
  verbatim-value test). None is W1's: W1 is zero-edit (target
  worktree hash matches dispatch; artifact untracked). The
  mid-item conf.py drift (worktree `ae3de0a3` → `3820c575`)
  leaves W1's judged regions byte-intact (`:343` dunder line is
  hunk context, key import untouched) — no finding reopens.

### Erratum corrected in place (E1, verdicts stand)

W1 mistranscribed the `types/relay.py` HEAD pin as `524398623547`
(5 occurrences: freshness table + F-STRATVOCAB/F-STRAT1/R5/R8
freshness lines); the object is `524398622354`. Corrected in place
per the run-7 permissions-E1 precedent (0 old / 5 new confirmed).
W1 demonstrably read the right bytes (cited regions :413–420 and
the `relay_shaped=True` setting path match HEAD exactly), so this
is a literal typo, never a staleness signal.

### Immaterial record notes (no home/count/gate moves)

1. E1 above. 2. Import bound names 32, not 33. 3. `_meta_attr`
   call sites 20 + def, not 21. 4. `ALLOWED_META_KEYS` holds 17
   keys (AST-verified): F-METAKEYS "(17 keys)" is right while
   enumeration #23 "18-key vocabulary" and C23 "18th" are
   off-by-one — internal inconsistency, C23 still counts 1. 5.
   R12 "116 literals in 40 files" recounts as 125 in 44 files
   (106 with trailing space) — verdict rests on
   declaration-vs-derivation + principle 7, not the census. 6.
   FAM-NEW oracle cite should add :583 (derived-side grammar pin).

No defects found by Worker-2. No `## Defects` addition.
`Status: verified` (zero-edit file item; nothing pending).

## Index rows for Worker-0

Literal 5-column rows; Worker-0 transcribes verbatim.

| `types-base-module-mechanics` | `django_strawberry_framework/types/base.py` (docstring + 21 import statements binding 33 names, all consumer edges) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-meta-key-vocabulary` | `django_strawberry_framework/types/base.py::ALLOWED_META_KEYS` (+ `DEFERRED_META_KEYS`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-relation-shape-vocabulary` | `django_strawberry_framework/types/base.py::RELATION_SHAPE_VALUES` (+ `DEFAULT_RELATION_SHAPE`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-relay-gate-wording` | `django_strawberry_framework/types/base.py::_RELAY_NODE_GATE_LEAD` (+ `_RELAY_NODE_GATE_INHERIT_TAIL`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-globalid-strategy-vocabulary` | `django_strawberry_framework/types/base.py::STRING_GLOBALID_STRATEGIES` (+ `DEFAULT_GLOBALID_STRATEGY`, `_GLOBALID_CALLABLE_PARAMS`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-set-sidecar-gate` | `django_strawberry_framework/types/base.py::_validate_set_sidecar` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-connection-dict-grammar` | `django_strawberry_framework/types/base.py::_validate_connection` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-cursor-field-stage-1` | `django_strawberry_framework/types/base.py::_validate_cursor_field` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-relation-shapes-stage-1` | `django_strawberry_framework/types/base.py::_validate_relation_shapes` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-globalid-strategy-validation` | `django_strawberry_framework/types/base.py::_validate_globalid_strategy` (+ `_validate_globalid_callable`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-nodeid-annotation-recognition` | `django_strawberry_framework/types/base.py::_id_annotation_is_relay_node_id` (+ `_has_node_id_marker`, `_NODEID_STRING_RE`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-relay-shaped-predicate` | `django_strawberry_framework/types/base.py::_is_relay_shaped` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-meta-attribute-read` | `django_strawberry_framework/types/base.py::_meta_attr` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-auto-marker` | `django_strawberry_framework/types/base.py::_is_auto_annotation` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-subclass-collection` | `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-queryset-hook-contract` | `django_strawberry_framework/types/base.py::DjangoType.has_custom_get_queryset` (+ `get_queryset`, `_is_default_get_queryset`, `_detect_custom_get_queryset`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-spec-normalization` | `django_strawberry_framework/types/base.py::_normalize_sequence_spec` (+ `_normalize_fields_spec`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-assigned-override-collection` | `django_strawberry_framework/types/base.py::_consumer_assigned_fields` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-optimizer-hints-read` | `django_strawberry_framework/types/base.py::_meta_optimizer_hints` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-unknown-fields-format` | `django_strawberry_framework/types/base.py::_format_unknown_fields_error` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-interfaces-validation` | `django_strawberry_framework/types/base.py::_validate_interfaces` (+ `_RELAY_NON_INTERFACE_HELPERS`, shape lead-in + formatter, remediation tail) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-meta-validation` | `django_strawberry_framework/types/base.py::_validate_meta` (+ `_ValidatedMeta`) | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-optimizer-hints-validation` | `django_strawberry_framework/types/base.py::_validate_optimizer_hints` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-meta-target-skeleton` | `django_strawberry_framework/types/base.py::_selected_meta_targets` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-nullability-override-targets` | `django_strawberry_framework/types/base.py::_validate_nullability_override_targets` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-filesystem-path-targets` | `django_strawberry_framework/types/base.py::_validate_filesystem_path_targets` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-relation-shape-targets` | `django_strawberry_framework/types/base.py::_validate_relation_shape_targets` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-field-selection` | `django_strawberry_framework/types/base.py::_select_fields` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `types-base-annotation-synthesis` | `django_strawberry_framework/types/base.py::_build_annotations` | `django_strawberry_framework/types/base.py` | File `types/base.py` | file-local |
| `graphql-name-gate` | TBD by family item (candidates: `django_strawberry_framework/types/definition.py` via a pure name-validity predicate both gates compose, or the status quo with the separation recorded at both sites) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py` | Family `graphql-name-gate` | open |
| `relay-pk-suppression-read-mirror` | TBD by family item (per the rule artifact: `django_strawberry_framework/types/base.py::_is_suppressed_relay_pk` pure predicate; this file item CONVERGES the performer + predictor + pk-name identity facet onto the standing UNAPPLIED family with fresh trigger checks, all unfired) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/management/commands/inspect_django_type.py` | Family `relay-pk-suppression-read-mirror` | open (UNAPPLIED; blocked-on-hunt; maintainer decision a/b/c owed) |
| `types-base-meta-guard-vs-write-flavor-guard` | `django_strawberry_framework/types/base.py::_validate_meta` (rejection recorded here; two-set vs one-set vocabulary + per-subject message CONVERGE with verified per-subject-rejection-grammars on fresh evidence + non-`str` tolerance split, execution-verified constructible) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/mutations/sets.py` | File `types/base.py` | rejected |
| `types-base-wordings-vs-shared-grammar` | `django_strawberry_framework/types/base.py` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence — still no owned grammar at HEAD) | `django_strawberry_framework/types/base.py` | File `types/base.py` | rejected |
| `types-base-except-arms-vs-shared-guard` | `django_strawberry_framework/types/base.py` (rejection recorded here; CONVERGE with the verified shared-except-guard J1 direction on fresh evidence — 6 per-site arms) | `django_strawberry_framework/types/base.py` | File `types/base.py` | rejected |
| `types-base-gate-wording-vs-factory-wording` | `django_strawberry_framework/types/base.py::_RELAY_NODE_GATE_LEAD` (rejection recorded here; fresh pair — Meta-key vs field-factory remediation; durable home the owner comment) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/relay.py`, `django_strawberry_framework/connection.py` | File `types/base.py` | rejected |
| `types-base-relay-predicate-vs-post-injection-check` | `django_strawberry_framework/types/base.py::_is_relay_shaped` (rejection recorded here; fresh pair — pre-injection tuple-or-inheritance vs post-injection MRO timing) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/relay.py` | File `types/base.py` | rejected |
| `types-base-relay-predicate-vs-id-column-probe` | `django_strawberry_framework/types/base.py::_is_relay_shaped` (rejection recorded here; fresh pair — shape gate vs fail-closed id-column probe) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py` | File `types/base.py` | rejected |
| `types-base-pk-name-vs-pk-attname-reads` | `django_strawberry_framework/types/base.py::_build_annotations` (rejection recorded here; CONVERGE with the verified join_taxonomy six-`pk.attname`-readers rejection on fresh evidence — name-vs-column split stands) | `django_strawberry_framework/types/base.py` | File `types/base.py` | rejected |
| `types-base-strategy-vocabulary-vs-payload-memberships` | `django_strawberry_framework/types/base.py::STRING_GLOBALID_STRATEGIES` (rejection recorded here; fresh pair — declared vocabulary vs encode/decode payload-shape memberships) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/filters/base.py` | File `types/base.py` | rejected |
| `types-base-selection-vs-input-shaping` | `django_strawberry_framework/types/base.py::_select_fields` (rejection recorded here; CONVERGE with the DRY.md worked-example `FilterSet.get_fields` separation on fresh evidence — one token, two contracts) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/orders/sets.py` | File `types/base.py` | rejected |
| `types-base-finalized-gates-stay-per-verb` | `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` (rejection recorded here; fresh 5-gate split — refuse-register vs no-op vs refuse-declare vs cache-read vs refuse-mint; flag owned by verified `type-registry-finalize-gate`) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/testing/relay.py` | File `types/base.py` | rejected |
| `types-base-auto-vs-strategy-auto` | `django_strawberry_framework/types/base.py::_is_auto_annotation` (rejection recorded here; CONVERGE with the verified nested_fetch strategy-vs-field-`auto` rejection on fresh evidence) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/optimizer/nested_fetch.py` | File `types/base.py` | rejected |
| `types-base-article-declaration-vs-derivation` | `django_strawberry_framework/types/base.py::_validate_set_sidecar` (rejection recorded here; fresh pair — caller-spelled article vs policies derivation; policies-L1 trigger re-checked unfired) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/utils/policies.py` | File `types/base.py` | rejected |
| `types-base-sequence-ladders-split` | `django_strawberry_framework/types/base.py::_normalize_sequence_spec` (rejection recorded here; same-file intentional separation — accepted-shape sets differ per subject) | `django_strawberry_framework/types/base.py` | File `types/base.py` | rejected |
| `types-base-mro-walk-vs-dispatch-walks` | `django_strawberry_framework/types/base.py::_detect_custom_get_queryset` (rejection recorded here; fresh pair — override detection vs scalar dispatch vs declaration collection) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/sets_mixins.py` | File `types/base.py` | rejected |
| `types-base-strawberryfield-gate-vs-surface-audit` | `django_strawberry_framework/types/base.py::_consumer_assigned_fields` (rejection recorded here; fresh pair — membership detection at collection vs surface-name collection at audit) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/finalizer.py` | File `types/base.py` | rejected |
| `types-base-gfk-posture-vs-flavor-posture` | `django_strawberry_framework/types/base.py::_build_annotations` (rejection recorded here; fresh pair — type-surface refusal vs per-flavor input-shaping policy) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/mutations/inputs.py` | File `types/base.py` | rejected |
| `types-base-metaread-containment-vs-raw-flavor-reads` | `django_strawberry_framework/types/base.py::_meta_attr` (rejection recorded here; fresh axis-6 probe — no contract source extends containment to flavor seams; sets-N3 prior evidence trigger-checked) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/filters/base.py` | File `types/base.py` | rejected |
| `types-base-name-gate-vs-sanitize-and-dunder` | `django_strawberry_framework/types/base.py::_validate_meta` (rejection recorded here; fresh pair — reject vs sanitize vs introspection-safety) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/conf.py` | File `types/base.py` | rejected |
| `types-base-arity-bind-vs-router-bind` | `django_strawberry_framework/types/base.py::_validate_globalid_callable` (rejection recorded here; fresh pair — three calling conventions over the shared stdlib mechanism) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/routers.py` | File `types/base.py` | rejected |
| `types-base-model-gate-vs-resolution-chain` | `django_strawberry_framework/types/base.py::_validate_meta` (rejection recorded here; fresh pair — direct declaration vs indirect overridable hook) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/mutations/sets.py` | File `types/base.py` | rejected |
| `types-base-bool-gates-vs-shared-exact-gate` | `django_strawberry_framework/types/base.py::_validate_meta` (rejection recorded here; CONVERGE with the verified shared-exact-type-gate J2 direction on fresh evidence — per-site `isinstance(…, bool)` gates) | `django_strawberry_framework/types/base.py` | File `types/base.py` | rejected |
| `types-base-meta-class-gate` | `django_strawberry_framework/mutations/sets.py::reject_unknown_meta_keys` (asymmetry recorded here; ROUTED TO MAINTAINER — no contract source; trigger: a spec row requiring class-only `Meta` for `DjangoType`, or the maintainer ruling the write-flavor posture extends here) | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | File `types/base.py` | rejected |

## Families

Worker-0 must add:

- [ ] Family `graphql-name-gate` — [dry-rule-graphql-name-gate.md](dry-rule-graphql-name-gate.md) — no artifact on disk; undispatched

No other family: C1 adopts into the open `hostile-mapping-hardening`
(no transcription — row already covers this file); C3 converges onto
the standing UNAPPLIED `relay-pk-suppression-read-mirror` (converge
row above; `## Families` entry already exists); C2/C4/C5/C6
transcribe nothing.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[docs-readme]: ../README.md
[file-filters-sets]: dry-file-filters__sets.md
[file-join-taxonomy]: dry-file-optimizer__join_taxonomy.md
[file-nested-fetch]: dry-file-optimizer__nested_fetch.md
[file-orders-sets]: dry-file-orders__sets.md
[file-policies]: dry-file-utils__policies.md
[file-rf-sets]: dry-file-rest_framework__sets.md
[file-testing-relay]: dry-file-testing__relay.md
[glossary]: ../GLOSSARY.md
[rule-relay-pk-mirror]: dry-rule-relay-pk-suppression-read-mirror.md

<!-- docs/SPECS/ -->
[spec-011-stub]: ../SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md
[spec-015]: ../SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-015-rationale]: ../SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[hints]: ../../django_strawberry_framework/optimizer/hints.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[keyset]: ../../django_strawberry_framework/keyset.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[root-relay]: ../../django_strawberry_framework/relay.py
[routers]: ../../django_strawberry_framework/routers.py
[scalars]: ../../django_strawberry_framework/scalars.py
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
[utils-typing]: ../../django_strawberry_framework/utils/typing.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base]: ../../tests/types/test_base.py
[test-definition-order]: ../../tests/types/test_definition_order.py
[test-definition-relations]: ../../tests/types/test_definition_relations.py
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-inspect]: ../../tests/management/test_inspect_django_type.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

