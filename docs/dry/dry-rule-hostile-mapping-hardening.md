# DRY review: `hostile-mapping-hardening`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is fail-closed consumption of untrusted mappings: a raw
mapping entering typed machinery is type-gated, defensively materialized, and
key-gated before anything hashes, sorts, splats, or compares its keys, with
unknown keys and hostile values rejected as typed errors rather than leaking
raw `TypeError` / `RuntimeError` past the boundary. The candidate was named by
File `utils/policies.py` as a materialize-once + key-guard + vocabulary triple
shared between `utils/policies.py::resolve_policy` and
`conf.py::upstream_patches_enabled`, with partial members in `conf.py` and
`types/base.py`, plus two adoptions (`rest_framework/resolvers.py::_hook_mapping`,
`rest_framework/sets.py` schema-map and nested-fields facets).

Traced at HEAD bytes (`5c3496e0`) through `git show HEAD:<path>` and
`git grep ... HEAD`. That instrument choice is load-bearing: all five indexed
files are dirty in the working tree with the concurrent bug-hunt truth/lazy
migration (549 insertions / 575 deletions across the five, none of it in the
plan's `## Owned changes` ledger), so working-tree reads do not show the bytes
this verdict is about. Every line cited below is a HEAD line; every
fingerprint is a HEAD blob except the worktree/ITEM_BASELINE pins recorded for
attribution. Prior file/family records were read as orientation and adjudicated
fresh; nothing below is inherited.

Sites found, by role. There is no shared definition; each site below is the
single owner of its own per-subject hardening (the verdict argued under
Findings). Groups:

- Deployment/settings mappings. `utils/policies.py::resolve_policy` (`:110`,
  mapping arm `:152`-`:190`: non-mapping rejection, `dict()` materialize-once,
  `isinstance`-str key guard, `fields()`-derived vocabulary rejection,
  constructor application); `conf.py::upstream_patches_enabled` (`:371`,
  bool-or-mapping toggle: hostile-`isinstance` armor, `dict()` materialize,
  armored `isinstance`-str key guard, frozenset vocabulary, exact-bool value
  loop, `.get` with default); `conf.py::_normalize_user_settings` (`:167`,
  shape gate plus materialize with a `dict` identity fast path, deliberately
  no key rule).
- Consumer `Meta`/class mappings (`types/`). `types/base.py::_validate_connection`
  (`:254`, `dict`-only gate, unknown sub-key list, bool value gate, copy
  last); `types/base.py::_validate_relation_shapes` (`:363`, `dict`-only
  gate, per-key `isinstance`-str guard, per-value shape vocabulary, live
  iteration then copy); `types/base.py::_meta_optimizer_hints` (`:1092`,
  `Mapping` gate plus live key guard plus copy last) with
  `types/base.py::_validate_optimizer_hints` (`:1510`, self-validating second
  key gate plus field-surface typo guards plus value-type check);
  `types/base.py::__init_subclass__` (`:709`, annotation `dict()` snapshot
  plus non-string-key collection); `types/finalizer.py::_annotation_names`
  (`:136`, guarded annotation read plus first-offender key gate plus
  render-normalize); `types/base.py::_validate_meta` (`:1429`, own-keys
  `Unknown Meta keys` set-difference guard).
- RF hook/`Meta` mappings. `rest_framework/resolvers.py::_hook_mapping`
  (`:690`, `Mapping` gate plus `BaseException`-contained `dict()` materialize
  plus exact-`str` offenders-list gate; 3 call sites, all in-file);
  `rest_framework/resolvers.py` context merge (`:1046`, `Mapping` gate plus
  contained `dict()` of the optional `context` sub-mapping, no key gate);
  `rest_framework/sets.py::_validate_schema_field_map` (`:146`, `Mapping`
  gate plus `tuple(items())` materialize plus per-entry unpack guard plus
  exact-`str` key gate plus DRF-field and bound-name guards, aggregate
  reporting); `rest_framework/sets.py::_validate_serializer_nested_fields`
  (`:308`, helper-fronted `Mapping` gate plus `tuple(items())` materialize
  plus unpack guard plus exact-`str` key gate plus config/membership/override
  checks, fail-fast reporting); `rest_framework/inputs.py` helpers
  (`require_nested_fields_mapping` `:326`,
  `require_nested_serializer_config`, `normalize_nested_serializer_configs`
  `:228` with its mapping-path cycle guard, `read_nested_serializer_fields`,
  `get_serializer_for_schema` `:345`).
- Forms hook mappings. `forms/inputs.py::get_form_fields` (`:191`, guarded
  `dict(base_fields)` discovery) and `forms/inputs.py::_form_field_basis`
  (`:217`, guarded `dict(source)` plus identifier-and-not-keyword key gate
  plus `forms.Field` value check, hostile-`__repr__`-contained reporting).
- Scalar/registry mappings. `scalars.py::strawberry_config` (`:139`,
  `dict()` materialize plus key-set intersection plus merge inside one
  `BaseException`-contained `ValueError` boundary, collision vocabulary over
  type keys).
- Input-traversal mappings. `utils/input_values.py::iter_input_items` (`:94`,
  base-slot `dict.items` read plus `str.__str__` key normalization) with
  `::_field_name` (`:77`, reject-and-normalize key rule);
  `utils/input_values.py::related_declaration_mapping` (`:307`, shared
  mapping front half with per-caller consumption explicitly separated in its
  docstring); `optimizer/extension.py::_freeze_variable_value` (`:439`,
  verdicts-once `Mapping` fork with fail-soft opaque fallback, never a
  rejection); `extensions/resource_policy.py` (`:585` container fork, `:642`
  `Mapping` gate with exact-`dict` fast path versus bounded-members read);
  `utils/inputs.py` (`:892` meta snapshot, `:1250` basis copy, `:1392`
  exact-`dict` base-slot versus general `dict()` kwargs materialize, `:1179`
  `str.__str__` key normalization).
- Canonical/permission reads. `utils/canonical.py::base_container_values`
  (`:51`, base-slot reads over exactly five builtins, typed refusal for
  anything else); `utils/permissions.py::_context_request` (`:168`, unbound
  `Mapping.get` single-slot read with readability reporting).
- `Meta`-namespace (not a mapping) typo guards. `mutations/sets.py::reject_unknown_meta_keys`
  (`:168`, shared `vars(meta)` scan with mixed-type-safe sort, called by
  mutations, both forms flavors, and the serializer flavor).
- Already-single-owned neighbors (boundaries, not members). Safe rendering
  (`exceptions.py::_safe_type_name` / `_safe_arg_repr` / `describe_value`,
  composed by name at every reporting site); `filters/base.py::_materialize_list_shaped_values`
  (list-shaped, not mapping-shaped); `utils/querysets.py` exact-`dict` /
  exact-`str` gates (SQL-identifier subject); `_strawberry_patches.py`
  multipart map handling (wire trust boundary, upstream-patch owned).

Consumers: schema construction (both policy flavors), app-load patch gates,
class-creation validators (types, mutations, forms, serializer flavors),
request-time hook pipelines (RF resolvers, forms resolvers), the input-build
and fingerprint/permission walks, and the scalar-config factory. Each consumes
only its own site's output.

Oracles: per-site hostile pins that spell expectations independently (bespoke
hostile doubles plus literal message matches, never reads of an owner):
`tests/utils/test_policies.py` (one-shot divergence, unhashable keys, raising
iterators, typed-passthrough, hashable non-string keys, both flavors);
`tests/base/test_conf.py` (toggle shapes, hostile mappings, key/value/unknown
rejections); `tests/types/test_base.py` (shape gates, key gates, unknown keys,
including a direct `_validate_optimizer_hints({123: ...})` call proving the
second gate is the tested contract); RF/forms/sets suites (non-mapping,
unmaterializable, malformed-entry, non-string-key, identifier, and hostile-
`__repr__` rows); canonical/inputs suites (subclass-iteration and ordering
rows). Projections: the precedent citations each site carries
(`resolve_policy` <-> `upstream_patches_enabled`, both RF sets validators ->
`_hook_mapping`, `_validate_connection` <-> `_validate_relation_shapes`,
forms basis -> identifier rationale), which name an idiom, not an owner.

## Verification

### Matrix

1. Cross-flavor policy mirroring. Searched, complete. Every flavor's
   mapping-entry validators were read at their owners: policies (ladder arm),
   conf (toggle plus top-level shape), types (connection, relation shapes,
   optimizer hints twice, annotations twice, `Meta` keys), RF (hook coercion,
   context merge, schema map, nested opt-in plus five inputs helpers), forms
   (discovery plus basis), mutations (shared `Meta` typo guard plus three
   composing flavors), scalars (config factory), filters (list-shaped only,
   excluded), orders (sequence gates, no mapping surface), optimizer
   (fail-soft freeze), extensions (bounded charging), utils (traversal,
   canonical, permission reads). No flavor resolves a mapping through another
   flavor's validator; the only cross-flavor sharing is the safe renderers
   (already single-owned in `exceptions.py`) and the shared `Meta` typo guard
   (already single-owned in `mutations/sets.py`, composed by name by all four
   write flavors). Both are boundaries of this family, not members.
2. Sync/async twins. Ruled inapplicable with reason. Every hardening site is
   synchronous validation at construction, class creation, or request entry
   with no await point; `_hook_mapping` is one sync body called from sync and
   async paths alike (3 call sites, single spelling). There is no colored
   twin of any gate to drift.
3. Derived rather than repeated knowledge. Searched. Vocabulary derivations
   (`fields()` in the ladder arm, frozensets for patches and shapes, live
   `field_map` membership for nested opt-ins, model `_meta` surfaces for
   hints, `vars(meta)` scans for `Meta` keys) each derive from the subject's
   own declaration; no vocabulary is spelled twice. Key-gate spellings come
   in three policies - reject-subclass (`type(x) is str`, RF trio plus a
   dozen unrelated subjects), accept-subclass (`isinstance(x, str)`, both
   deployment sites plus the types gates), normalize-subclass
   (`str.__str__`, input traversal twice) - each chosen by what the keys
   feed downstream (C2). Unknown-key renders (`sorted(unknown)` plus valid
   list) share a list shape but name per-subject vocabularies in per-subject
   messages (C3).
4. Inverse / round-trip pairs. Ruled inapplicable with reason. No validated
   mapping is ever serialized back: snapshots feed construction, comparison,
   or traversal only. The nearest pairs (schema-map snapshot versus the
   bind-time determinism fingerprint; canonical reads versus digest writes)
   are deliberately asymmetric checks over different inputs, not two halves
   of one grammar.
5. Contracts restated in another medium. Searched. Oracles (per-site hostile
   doubles plus literal wording pins, listed in System trace) check behavior
   without reading any owner; a wording change fails them rather than moving
   with them. Projections (precedent citations, module docstrings, the shared
   typo-guard docstring) describe; none owns. No medium carries a second
   hardening body.
6. Enforcement by omission. Enumerated the full mapping-entry surface (axis 1
   census). Asymmetries found and adjudicated, none a defect: the ladder arm
   lacks the toggle's `isinstance` armor (N1); relation shapes double-iterate
   a `dict`-subclass (N2); `_normalize_user_settings` has no key guard by
   documented design (keys never matched, cache typed `dict[object,
   object]`); the optimizer freeze fails soft to opaque tokens by documented
   design (cache keys, not validation); the context merge has no key gate
   (keys feed fixed-name `.get` reads, never hashing or splatting); the
   canonical reader refuses non-builtin mappings while deployment sites
   accept arbitrary `Mapping`s (opposite postures for fingerprint integrity
   versus deployment convenience). No contract source requires any missing
   guard, and the hostile-value lines are concurrent hunt work (see N1/N2);
   omission here is per-subject design, not a gap.

### Enumeration

Instrument: `git grep` censuses over HEAD blobs across all 117 package `.py`
files, plus full HEAD reads of the five indexed files and region reads of
every file a hit implicates. Populations censused, not sampled: `isinstance`
`Mapping` gates (22 sites), `dict(` materializations (60+ sites, each
classified by subject), `tuple(items())` consumptions (2: both RF sets
validators), `could not be materialized` producers (3: hook coercion, context
merge, schema map), `iteration failed` producers (2: ladder arm, toggle),
exact-`str` gates (30+ sites, of which exactly 3 guard mapping keys: the RF
trio), `Unknown`/`unknown` vocabulary rejections (8 mapping-shaped sites),
`_safe_*`/`describe_value` composers (40+ files, all by name from
`exceptions.py`). Internal `dict()` copies of package-owned structures
(queryset hints, plan keys, filter defaults, annotation snapshots, patch
params, resolver kwargs) never cross a trust boundary and are outside the
population by the rule's own subject test (untrusted mappings only).
Every member lands in F1, an R-exclusion, or a
verdict-neutral note; nothing is unassigned.

### Challenges

Each challenge posits a change on one of the candidate shared rule's
variation axes and counts authoritative definitions that must move.
Consumers, oracles, and projections that also move are listed, never counted.

- C1 (consumption axis): a hostile shape defeats `dict()`-consumption (a
  `Mapping` whose `keys()` and `__iter__` disagree). `dict(m)` sites (ladder
  arm, toggle, top-level shape, hook coercion, context merge, forms basis,
  scalar factory, RF discovery) each need a per-site fix shaped by what
  follows: the scalar intersection re-hashes keys after materialization, the
  forms basis feeds identifier interrogation, the hook coercion feeds
  `**kwargs`. `tuple(items())` sites (both RF sets validators) do not move
  (different consumption point, already immune). Base-slot sites (canonical
  reader, input traversal, exact-`dict` kwargs path) do not move (they never
  dispatch consumer iteration). No single fix shape: count is per
  consumption-point contract, 1 each, with different bodies.
- C2 (key-gate axis): `str` subclasses with verified-safe dunders are
  accepted. Exact-`str` sites (the RF trio) move; `isinstance`-`str` sites
  (ladder arm, toggle, relation shapes, both hints gates, both annotation
  gates) do not (already accept); normalize sites (input traversal,
  utils/inputs `:1179`) do not (already reduce); identifier site (forms
  basis) does not (different rule); gateless sites (top-level shape,
  connection, context merge, scalar type-map, canonical refusal, optimizer
  freeze) do not. Within the trio the shared part is the one-line predicate
  only: reporting is per-site and load-bearing (offenders list versus
  aggregate versus fail-fast, each pinned by oracles), and each gate's reason
  names a different downstream hazard (`**kwargs` plus DRF internals versus
  package dict-set plus bound-name comparison versus `.get` plus message
  render plus dict-set). Posit a change to any one site's reporting or
  downstream and the other two do not move (C5). Count: 3 per-site bodies
  sharing one predicate spelling, not 1 rule with 3 definitions.
- C3 (vocabulary axis): unknown-key rejections gain per-key reasons. Each
  vocabulary step moves alone with its own subject, source, and wording:
  ladder arm (`display_name`/`unit` over `fields()`), toggle (bespoke over
  its frozenset), relation shapes (per-value, no unknown-key step),
  connection (bool-gated sub-keys), hints (model `_meta` surfaces),
  nested opt-in (live `field_map` membership), `Meta` guards (`vars(meta)`
  scans), scalar factory (collision over type keys). Sites without a
  vocabulary step (hook coercion, context merge, schema map, top-level shape,
  canonical reader, freeze, chargers) do not move. Count per subject: 1.
  This confirms the f12 seam from this side: vocabulary rejection varies per
  subject, and the ladder's stays ladder-owned (R-seam).
- C4 (containment-breadth control): `BaseException` containment is narrowed
  to `Exception` (or vice versa). Request/hook sites (hook coercion,
  context merge, schema map, nested opt-in, forms basis, scalar factory)
  contain `BaseException`; construction/settings sites (ladder arm,
  toggle inner materialize, canonical reader callers) contain `Exception`
  with typed passthrough; the toggle additionally wraps the whole block.
  Each breadth matches its execution context (a hook return must never
  escape the typed boundary mid-request; construction lets process-control
  signals propagate). A change to one context's breadth is wrong for the
  other: count per context, 1 each.
- C5 (separation controls): a change to one site's downstream moves only
  that site. DRF changes `**kwargs` handling -> hook coercion alone;
  schema-map reporting goes fail-fast -> schema map alone; nested
  membership switches to effective-fields -> nested opt-in alone; policy
  vocabulary wording gains a unit plural -> ladder arm alone; the patch
  registry gains a dependency -> toggle alone (plus its constant); the
  input walk stops normalizing keys -> traversal alone. Each control moves
  exactly 1 body and none of the others, establishing that the bodies vary
  independently on every axis except shared predicate spellings.

All counts are 1 per subject. No posited change moves two definitions of one
contract.

## Findings

### F1: per-subject mapping hardening is intentionally separated (REJECT)

- Contract + variation: each mapping-entry site validates the mapping its
  own downstream consumes, on axes that vary per site: accepted container
  (`Mapping` versus `dict`-only versus exact-`dict` versus class namespace
  versus five builtins), consumption point (`dict()` versus `tuple(items())`
  versus base-slot versus single-slot versus live iteration), key policy
  (exact-`str` versus `isinstance`-`str` versus normalize versus identifier
  versus none), containment breadth (`BaseException` versus `Exception` plus
  typed passthrough versus opaque fallback), vocabulary source (dataclass
  fields, frozensets, live maps, model surfaces, `vars()` scans, none),
  value rule (constructor, exact-bool, DRF field, config record, identifier,
  none), error type (`ConfigurationError` versus `ValueError` versus opaque
  token versus `None`), and reporting (offenders list, aggregate, fail-fast,
  first-offender). Two sites in the same file choose differently on these
  axes (`_validate_connection` versus `_validate_relation_shapes`;
  `_validate_schema_field_map` versus
  `_validate_serializer_nested_fields`), which is the signature of
  per-subject rules, not one rule with many definitions.
- Sites + roles: every site in System trace is a definition of its own
  per-subject rule (count 1 each, established by C1-C5); precedent citations
  between them are projections of a shared idiom, not delegation. The two
  file-item adoptions resolve here: the resolvers `_hook_mapping` member and
  the sets schema-map / nested-fields facets stay with their file-local
  owners as facets of those per-site validations, not as members of a shared
  rule. No new index rows owed; Worker-0 flips the family row to rejected
  with the triggers below.
- Challenges: C1-C5 above, each count 1 per subject; C5's six separation
  controls each move exactly 1 body.
- Owner + lifetime: no single owner. Candidates refused by responsibility
  (principle 7): `utils/policies.py` owns deployment-policy normalization,
  not hook-return or `Meta` validation; `utils/canonical.py` owns
  refusal-posture canonical reads (five builtins only), the opposite of the
  permissive-consumption the deployment and hook sites need; `exceptions.py`
  already owns the genuinely shared part (safe rendering) and is composed by
  name everywhere; a new shared helper would need mode flags for container
  types, key policies, breadths, vocabularies, value rules, error types, and
  reporting shapes - machinery coupling independent domains, which DRY
  forbids. Each site keeps its hardening; the idiom stays shared vocabulary,
  deliberately unowned. No stored derivation, so no principle-4 fields owed.
- Migration: none. There is no former definition to re-point and no body to
  move; the verdict is zero-edit.
- Distinct behavior: everything stays where it is. The shared `Meta` typo
  guard and the safe renderers stay single-owned at their existing owners
  (boundaries, not members). The f12 vocabulary seam is confirmed from this
  side (R-seam): the ladder's unknown-key rejection is ladder-owned because
  vocabulary varies per subject everywhere.
- Behavioral proof: static-reviewed. A zero-edit rejection owes no
  equivalence proof because nothing moves; the evidence is the census (22
  `Mapping` gates, 60+ materializations, 3 key-policy families, 8
  vocabulary steps, each classified by subject) plus the five challenges
  with per-subject counts. The oracles that pin each site's behavior already
  exist in-tree (per-site hostile doubles plus literal wording pins) and are
  cited, not re-run: executing them can only confirm the suite is green,
  which proves nothing about definition count.
- Structural gate: none owed. The realistic bypass is a new mapping-entry
  site validating without hardening, and no mechanical gate can distinguish
  "unhardened" from "subject needs none" (the top-level shape, connection
  keys, context merge, and optimizer freeze are gateless by documented
  design). A bespoke existence test per helper is explicitly not the shape;
  the per-site hostile oracles are the gates that already exist.
- Coupling: none. Zero edits, zero dependencies.
- Freshness: HEAD `5c3496e0`. Blobs (HEAD short): `utils/policies.py`
  `4b180e2b`, `conf.py` `eccddc21`, `types/base.py` `e8416cc0`,
  `rest_framework/resolvers.py` `fc9d8ee5`, `rest_framework/sets.py`
  `b0894760`, `mutations/sets.py` `50f9d6a1`, `forms/inputs.py` `0ba0d9a5`,
  `scalars.py` `f203b79e`, `utils/canonical.py` `7f5bb5f7`,
  `utils/permissions.py` `0e13b869`, `utils/input_values.py` `929e81b5`,
  `utils/inputs.py` `0caa3416`, `optimizer/extension.py` `b7b6c434`,
  `extensions/resource_policy.py` `11e2a9ac`, `types/finalizer.py`
  `662826eb`, `rest_framework/inputs.py` `dfedd0e5`, `exceptions.py`
  `7a4fb661`, `filters/base.py` `6b952d4d`, `utils/sessions.py` `4135f507`,
  `utils/querysets.py` `69ac3ea3`, `error_policy.py` `7fc87d9f`,
  `resource_policy.py` `c554a679`, `tests/utils/test_policies.py`
  `57ab2170`, `tests/base/test_conf.py` `f35c7074`, `tests/types/test_base.py`
  `0d070aee`. Indexed-file worktree pins (hunt dirt, attributed by content,
  untouched): `utils/policies.py`
  `8d02c54bebd6b3e54bc4e1d07f470156a86d33aa`, `conf.py`
  `d239302afaa55213f42ca7d430fed52dcb42490c`, `types/base.py`
  `763a5acc92956bda84fc077892eec2c759ca7189`,
  `rest_framework/resolvers.py`
  `074d6e4bd0e1119e67ab8693b9dc8ce95d940786`,
  `rest_framework/sets.py`
  `f2e353b61de48a189fdd68cc8fc8f4e1005d1708`. ITEM_BASELINE
  `6181924ae85bc247da5fb7ce47884f7aab770496` pins the same five blobs as the
  worktree (dispatch-time stash capture; the item-scoped diff is empty).
  Searched population: all 117 package `.py` blobs at HEAD plus the oracle
  files named. Any fingerprint change reopens.

Verdict on F1: REJECT the consolidation; zero-edit.

### Rejections and exclusions (contract difference + trigger each)

R-depl. The deployment pair (ladder arm versus toggle). Difference: the
toggle carries hostile-`isinstance` armor, a whole-block wrap, a frozenset
vocabulary, and an exact-bool value loop for a bool-or-mapping setting read
at app load; the ladder arm has no armor, a `fields()` vocabulary, and
constructor application for an instance-or-mapping policy resolved at schema
construction. Same triple order, different threats, sources, values, and
messages (C1, C3, C4). Trigger: a hostile shape defeats one site's
consumption and the fix lands byte-identical at the other.

R-rf. The RF exact-`str` trio (hook coercion, schema map, nested opt-in).
Difference: one shared predicate spelling over three per-site contracts -
different mappings (hook returns versus hook field-maps versus `Meta`
opt-ins), phases (request/class-creation/class-creation), hazards
(`**kwargs` plus DRF internals versus dict-set plus comparison versus `.get`
plus render plus dict-set), and reporting (offenders list versus aggregate
versus fail-fast, each oracle-pinned). A predicate-only helper would relieve
no change obligation (C2, C5). Trigger: two trio sites adopt one reporting
shape, or a shared key-safety predicate gains logic (e.g. safe-subclass
detection) that two sites need.

R-types. The types `dict`-only validators (connection, relation shapes,
hints, annotations). Difference: each validates a different `Meta`/class
surface with its own value vocabulary (bool sub-keys, shape enum, model
fields, none) and its own copy discipline (copy-last after live iteration,
versus materialize-first at deployment and hook sites); the hints double
gate is self-validation across two phases, each function checking its own
input (the second gate is directly oracle-pinned). Trigger: two validators
start sharing a value vocabulary or a copy discipline for one reason.

R-forms. The forms identifier gate. Difference: the basis rejects keys that
are valid `str` but not identifiers or are keywords, because keys become
generated `__init__` attributes - a strictly stronger rule than any
string-gate in the family, with hostile-`__repr__`-contained aggregate
reporting. Trigger: generated inputs stop rendering names into source.

R-scalar. The scalar factory boundary. Difference: type keys (not strings),
one `BaseException`-contained `ValueError` (not `ConfigurationError`)
covering materialize plus intersection plus merge, collision vocabulary.
Trigger: consumer scalar keys become strings validated against a vocabulary.

R-trav. The traversal/canonical/permission readers. Difference:
refusal-posture base-slot reads (canonical five-builtin), single-slot
unbound reads with readability reporting (permission contexts),
normalize-posture walks (`str.__str__` reduction), fail-soft opaque
fallback (optimizer freeze), and bounded charging (extension walker) - each
posture answers a different consumer (fingerprints, request resolution, set
inputs, cache keys, width budgets), none of them validation. Trigger: two
readers need one posture for one consumer.

R-meta. The `Meta`-namespace typo guards. Difference: the shared guard scans
a class namespace (`vars(meta)`), not a mapping, with mixed-type-safe sort;
all four write flavors already compose it by name (single-owned, not a
member). The types `Meta` guard is the same shape over `meta.__dict__` with
its own deferred-keys axis. Trigger: the types guard starts importing the
shared guard instead of spelling the scan.

R-seam. The f12 vocabulary seam (boundary confirmation, not a verdict on
f12). This trace confirms from the family side what f12 R14 reserves: the
ladder's unknown-key rejection (valid names plus `display_name`/`unit`
wording) is ladder-owned because vocabulary steps vary per subject at all
eight mapping-shaped sites (C3). No trigger owed here; f12's row stands on
its own evidence and this item re-litigates none of it.

### Verdict-neutral notes (observed, not defects)

N1. Armor asymmetry (ladder arm versus toggle). The ladder arm's `Mapping`
check and key-guard loop carry no `isinstance` armor while the toggle arms
both; a `str`-subclass key with hostile `__hash__`/`__lt__` reaches
uncontained set-membership/`sorted()` in the ladder arm but the toggle's
outer wrap. No contract source requires the armor at the ladder arm (its
docstring promises typed rejection for unhashable keys and iteration
failure, both of which hold), and the arm's lines are concurrent hunt work
(the worktree rewrite touches exactly this region). Observed-not-homed on
hunt-owned lines; left to that cycle.

N2. Relation-shapes double iteration. `_validate_relation_shapes` gates
`dict` (admitting subclasses) but validates over live iteration and copies
last, so a one-shot `dict` subclass could diverge between the two passes.
No contract source requires single-consumption there (its docstring claims
no one-shot containment), the accepted shape is in practice a class-body
literal, and the file is concurrent hunt work. Observed-not-homed; left to
that cycle.

N3. Hints double gate (intentional). `_validate_optimizer_hints` re-checks
key types on an already-gated dict because it validates its own input: it is
called directly by oracles with raw mappings
(`tests/types/test_base.py:2536`), so the second gate is the tested contract,
not redundancy. Same subject, same owner, two self-validating phases.

N4. Top-level shape gatelessness (documented design). `_normalize_user_settings`
validates no keys because non-string keys are never matched by attribute
lookup; the cache is typed `dict[object, object]` to say so. Not an omission.

## Defects

None found. The trace read for contract at every site above; no docstring
contradicts its body on mapping handling, no site lacks a guard its contract
requires (axis 6 enumerates the full entry surface and adjudicates every
asymmetry, with N1/N2 observed-not-homed on concurrent hunt lines), and no
layering claim is contradicted by the imports (precedent citations are prose
links, never imports; the only composed-by-name sharing in this space - safe
renderers, the shared `Meta` typo guard - is already single-owned).

## Pending execution

None. The verdict is static-decidable (definition counts from source census
plus challenges); no equivalence proof is owed because nothing moves, and no
gate is relied on beyond the per-site hostile oracles already in-tree. No
pytest ran: executing oracles can only confirm the suite is green, which
proves nothing about definition count. The type gates were read (not run as
proofs of the verdict): `uv run mypy` clean (119 files), `uv run
basedpyright` 0 errors / 0 warnings / 0 notes, `uv run python
scripts/check_any.py` 130 uses at 90 sites - all in the shared venv against
the untouched tree. The `--cell sharded` / `--cell pg` cells are inapplicable
by construction: the finding touches no database, alias, or dialect decision
(construction-time, class-creation-time, and in-memory request-entry
validation plus source census). No `proof:` or `gate:` entry is owed.

## Judgment

Hostile-mapping hardening is a shared idiom, not a shared rule. Twenty-two
`Mapping` gates across nine subjects - deployment settings, consumer `Meta`,
hook returns, form bases, scalar registries, input walks, canonical reads,
permission contexts, cache keys - each validate the mapping their own
downstream consumes, and vary independently on containers, consumption
points, key policies, breadths, vocabularies, values, error types, and
reporting. The closest pairs (the deployment triple-order pair, the RF
exact-`str` trio) share spellings over per-site contracts that move alone
under every posited change. A consolidation would be mode-flagged machinery
coupling independent domains. REJECT the consolidation, zero edits, no new
index rows; the two file-item adoptions resolve to their file-local owners
as facets. The f12 vocabulary seam is confirmed from this side.

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

## Independent verification (Worker-2)

Pre-exposure disclosure: this section was written BEFORE opening `## Findings`
(only the `Status:`/`Run:` header lines and `grep`ped section headings were
seen). Trace is at HEAD bytes (`5c3496e0`); every WT hunk on the traced files
is concurrent hunt dirt (notably the `truth.*` migration — `utils/truth.py`
does not exist at HEAD — and the RF sets identifier gate) and was NOT relied
on. HEAD pins re-derived: `utils/policies.py 4b180e2b`, `conf.py eccddc21`,
`types/base.py e8416cc0`, `rest_framework/resolvers.py fc9d8ee5`,
`rest_framework/sets.py b0894760`, `rest_framework/inputs.py dfedd0e5`,
`forms/inputs.py 0ba0d9a5`, `scalars.py f203b79e`,
`utils/converters.py 9eae7cbb`, `utils/input_values.py 929e81b5`,
`utils/permissions.py 0e13b869`, `utils/context.py 36675564`,
`optimizer/extension.py b7b6c434`, `extensions/resource_policy.py 11e2a9ac`,
`utils/inputs.py 0caa3416`, `auth/sessions.py d4a4857c`,
`resource_policy.py c554a679`, `utils/connections.py 5bf8f5fa`,
`keyset.py 6af980b8`, `schema.py 0dad535d`, `filters/inputs.py d8febb10`.
Instrument: package-wide `git grep` for `isinstance(.*Mapping` at HEAD (20
hits, all read) plus `not isinstance.*dict` neighbor triage (all excluded
with reason below).

### W2 census (29 mechanism sites, 10 subjects)

Deployment settings (accepted shapes disjoint: mapping-or-None / bool-or-mapping
/ instance-or-mapping-or-None):

- W2-D1 `conf.py:167` `_normalize_user_settings`: None→`{}`; guarded
  Mapping gate; exact-`dict` passthrough (identity!); `dict()` copy with
  iteration-failure CE. NO key policy (non-string keys never match
  `__getattr__`). One definition; 3+ write-site consumers compose it.
- W2-D2 `conf.py:371` `upstream_patches_enabled`: exact-`bool` fast path;
  Mapping gate; guarded materialize (single consumption point); isinstance-str
  key guard FIRST; unknown-name rejection vs the `UPSTREAM_PATCH_DEPENDENCIES`
  frozenset; per-value exact-`bool`; whole-map validated on every read.
- W2-D3 `utils/policies.py:110` `resolve_policy`: two-slot ladder
  (explicit > setting > default), instance-or-mapping-or-None per slot;
  Mapping gate; guarded materialize; isinstance-str key guard FIRST;
  unknown-key rejection vs the policy dataclass fields; values to the
  constructor (domain downstream in `__post_init__`).

Consumer Meta (exact-`dict` vs Mapping; None→None vs None→`{}`):

- W2-M1 `types/base.py:254` `_validate_connection`: None→None; exact-`dict`
  gate; unknown-subkey rejection vs `{"total_count"}`; bool value gate;
  Relay-Node gate; `dict()` copy.
- W2-M2 `types/base.py:363` `_validate_relation_shapes`: None→None;
  exact-`dict` gate; per-entry str-key + str-in-`RELATION_SHAPE_VALUES`
  value gate (isinstance-first so unhashables stay typed); Relay-Node gate
  with its own "or remove the key" tail; `dict()` copy.
- W2-M3 `types/base.py:1092` `_meta_optimizer_hints`: None→`{}`; Mapping
  gate; str-key guard; then `dict(value)` — TWO consumptions of the raw
  mapping (guard loop + copy), both unguarded (see W2-N1).
- W2-M4 `rest_framework/sets.py:308` `_validate_serializer_nested_fields`:
  None→None; container gate via the shared H5; guarded materialize +
  guarded unpack; exact-`str` keys (immediate per-entry raise); value gate
  via shared `require_nested_serializer_config`; field-map membership;
  nested-kind gate; empty-means-absent; write-method-override requirement;
  normalize exit.

Hook returns (the RF trio + context + normalize + shared helper):

- W2-H1 `rest_framework/resolvers.py:691` `_hook_mapping`: Mapping gate;
  guarded materialize; exact-`str` keys with SORTED-AGGREGATE offenders
  report. One definition; 3 hook call-site consumers (injected-data,
  kwargs, save-kwargs).
- W2-H2 `rest_framework/resolvers.py:1046` context arm: None→`{}`; Mapping
  gate; guarded materialize; NO key gate (passthrough bag; reserved keys
  checked downstream by identity/value).
- W2-H3 `rest_framework/sets.py:146` `_validate_schema_field_map`: Mapping
  gate; guarded materialize; guarded per-entry unpack; exact-`str` keys;
  `serializers.Field` values; guarded bound-name read AND guarded
  comparison; key==bound-name match; ALL-errors aggregate CE. NO
  identifier gate at HEAD (run-7 R-ident still open; the WT identifier
  gate is concurrent dirt).
- W2-H4 `rest_framework/inputs.py:228`
  `normalize_nested_serializer_configs`: None→None; Mapping gate; cycle
  guard via `_mapping_path`; recursive rebuild with tuple selectors.
- W2-H5 `rest_framework/inputs.py:326` `require_nested_fields_mapping`:
  shared container rejection, already single-owned; 2 callers (W2-M4,
  `validate_nested_config_keys`). Counts as 1 definition, 0 opportunity.

Form bases (BaseException-guarded `dict()`; identifier gate lives ONLY here):

- W2-F1 `forms/inputs.py:191` `get_form_fields`: `dict(base_fields)` with
  BaseException→CE; no key/value policy (Django-built basis trusted).
- W2-F2 `forms/inputs.py:217` `_form_field_basis`: hook-or-base;
  `dict()` guard; per-name gate (isinstance-str + `isidentifier` +
  non-keyword, each interrogation guarded); `forms.Field` value gate;
  aggregate CE with safe renders.
- W2-F3 `forms/inputs.py:276` `normalize_form_field_basis`: None→RAISE
  (the None-posture outlier — a hook MUST return a map); delegates to F2.

Scalar registries (ValueError vs total-read; permissive vs identity):

- W2-S1 `scalars.py:146` `strawberry_config`: None→`{}`; `dict()` +
  key-set intersection + merge under ONE BaseException→`ValueError`
  guard; collision rejection vs the package map; `ValueError` (public
  factory contract), NOT CE; otherwise Strawberry-permissive keys/values.
- W2-S2 `utils/converters.py:80` `convert_with_mro` registry arm:
  `dict()` snapshot; identity (`is`) MRO scan so no consumer
  `__hash__`/`__eq__` ever runs; NO rejection — a total read.

Input walks (reject vs shared-front-half vs silent-skip):

- W2-W1 `utils/input_values.py:96` `iter_input_items` dataclass arm:
  non-walkable→None; non-Mapping `__dataclass_fields__`→CE; guarded
  enumerate; unbound `dict.items` for the dict arm.
- W2-W2 `utils/input_values.py:307` `related_declaration_mapping`:
  unreadable→`RelatedDeclarationError`; None→`{}`; non-Mapping→
  `RelatedDeclarationError(kind, value)` for CALLER translation; returns
  the mapping UN-materialized (tails differ per caller: permission
  walker takes unbound `dict.items`; traversal reads lazily).
  Already-consolidated front half; 2 consumers.
- W2-W3 `utils/inputs.py:1861` factory related-map fork: `getattr(...) or
  {}` then `if isinstance(related_map, Mapping)` — non-mapping SILENTLY
  yields zero branches (no rejection; see W2-N2).

Permission contexts (probes and forks, never rejections):

- W2-P1 `utils/permissions.py:149` `_channels_scope`: two Mapping probes
  over BaseException-guarded getattr chains; scope-or-None.
- W2-P2 `utils/permissions.py:171` `_context_request`: Mapping-vs-attribute
  fork; unbound `Mapping.get`, guarded; returns `(request, readable)`.
- W2-P3 `utils/permissions.py:206` `_request_from_context` Mapping arm:
  unreadable-mapping→None-and-STOP (deliberate asymmetry vs keep-looking).

Canonical reads (dict-first coercion trio, per-direction swallowed sets):

- W2-C1/C2/C3 `utils/context.py:57/:123/:198` get/stash/clear: None
  posture; `dict`-first dispatch with attribute/item fallbacks; read
  swallows `Exception`→default (fail-closed lookup); stash/clear keep
  narrower per-direction contracts (write failures can signal caller bugs).

Cache keys / budget walks (total functions; hostile shapes degraded, never
rejected):

- W2-K1 `optimizer/extension.py:438` `_freeze_variable_value` mapping arm:
  3-way classification with Exception→opaque-token; `items()` on the
  mapping's own terms; cycle token; TOTAL (any value → key).
- W2-K2 `extensions/resource_policy.py:603` `_charge_container` mapping
  arm (entry fork `:585` folds in): exact-`dict` fast path (`len` +
  `items` trusted) vs `_bounded_members` (one past the bound) for exotic
  mappings; cycle close; width charged from QUEUED members; object-keyed
  lookups that just miss; charged-never-classified.

Mutability (the only write-need gate):

- W2-X0 `auth/sessions.py:273` `_require_mutable_scope`: `MutableMapping`
  gate → CE (needs to STORE the per-scope lock). Different container,
  different purpose; immediate separation.

Roles: every W2-* is the DEFINITION of its own per-site rule. Consumers
(not counted): H1's 3 hook sites; H5's 2 callers; W2's 2 tails;
`_related_declarations` (W2 consumer + its own unbound-items tail);
S2's 4 converter callers; D3's 2 policy resolvers; C-trio callers
(`policy_from_info` reads via C1); K2's `:585` dispatcher; `child_mappings`
(`resolvers.py:1162`, a filter, not a gate).

Excluded neighbors (read at HEAD, each with its reason):

- X-keyset `keyset.py:568` cursor-payload `dict` gate: UNIFORM opaque error
  (anti-oracle: tamper/stale/shape deliberately indistinguishable).
  Sharing any typed gate would break that contract. Different rule.
- X-schema `schema.py:229` `parent_fields` dict probe: reflective read off
  a graphql-core descriptor, miss→None. `conf.py` module docstring names
  this class explicitly separate ("Do not unify the two").
- X-range `filters/inputs.py:909/914` dict-vs-attribute sniff: opportunistic
  read (start/end), no validation, no key policy, no containment. Different
  mechanism (belongs, if anywhere, to the input-shape-traversal rule).
- X-payloads `middleware/request_body.py:343`, `middleware/debug_toolbar.py:183`,
  `optimizer/plans.py:505`, `filters/sets.py:3315`,
  `rest_framework/resolvers.py:1860` (pragma-pinned DRF shape),
  `utils/inputs.py:703/739/803`: per-feature payload/shape probes, each
  with its own miss contract. Mechanism sweep confirms no Mapping-key-policy
  content.
- X-upstream-reads `serializer_converter.py:937` + `rf/inputs.py:416`
  (`field.choices`), `types/resolvers.py:642` (`_prefetched_objects_cache`),
  `sets_mixins.py:322` + `types/finalizer.py:1229` (framework-maintained
  declaration maps): reads of upstream- or framework-owned maps with no
  hostile key policy. Consumers, not gates.
- X-sidecar `utils/connections.py:106` + `list_field.py:371/1216` +
  `optimizer/extension.py:1611` (`or {}` / `.get` chains): framework-internal
  readers of framework-produced kwargs/contexts. No validation content.

### W2 variation axes (8, re-derived)

- X1 containers: Mapping vs exact-`dict` vs bool|mapping vs
  instance|mapping|None vs MutableMapping vs dict-or-dataclass vs
  try-anything (F1/F2) vs classification-only (K1/K2).
- X2 None posture: →`{}` (D1, H2, S1, M3) vs →None (M1, M2, M4, H4, W1)
  vs →raise (F3) vs N/A (probes, total functions).
- X3 iteration/materialize failure: wrap→CE with per-site message (D1, D2,
  D3, H1, H2, H3, M4, F1, F2) vs BaseException→CE (F1, F2, H3-unpack) vs
  propagate (M3 second pass, K1 items) vs unbound-method (W1-dict, P2,
  W2-permission-tail) vs bounded (K2) vs ValueError-wrap (S1).
- X4 key policy: none (D1, H2, S1-permissive, K2-miss) vs isinstance-str
  (D2, D3, M2, M3, F2-part) vs exact-str reject (H1, H3, M4) vs
  identifier+keyword (F2) vs vocab-membership (M1-subkeys, M2-values).
- X5 value policy: none (D1, H1, H2, W-gates) vs exact-bool (D2, M1) vs
  closed-vocab (M2) vs type-gate (H3-Field, M4-config, F2-Field) vs
  downstream-domain (D3-ctor) vs collision-vs-package-map (S1).
- X6 vocabulary source: frozenset const (D2) vs dataclass fields (D3) vs
  literal singleton (M1) vs spec frozenset (M2) vs schema field_map (M4,
  H3-bound-names) vs package scalar map (S1) vs none.
- X7 error contract: per-site CE wording, immediate (most) vs aggregate
  (H1-offenders, H3-all, F2-names+fields) vs ValueError (S1) vs
  caller-translated `RelatedDeclarationError` (W2) vs uniform-opaque
  (X-keyset, excluded) vs silent-skip (W3) vs total-token (K1) vs
  charge-not-reject (K2).
- X8 breadth/consumption: whole-map-every-read (D2) vs single-copy-then-read
  (D3, H1, S1) vs lazy (W2-traversal-tail) vs unbound-reads (P2, W1-dict)
  vs bounded (K2) vs snapshot+identity-scan (S2) vs double-consume (M3).

### W2 challenges (definition counts; HEAD bytes)

- W2-C1 value-shape validation added to every gate (e.g. reject
  non-JSON values): each site's X5 moves alone — D2 bools, D3
  ctor-domain, M1 bool, M2 vocab, H3 Fields, M4 configs, F2 Fields,
  S1 permissive-by-contract. No shared value rule exists; count = N
  with NO landable owner (each value domain owned downstream).
- W2-C2 one shared hostile-key error type for all key rejections: every
  key-gated site's raise + its literal oracles move, but the TYPE is
  owned per boundary (CE→config envelope; S1 `ValueError` public-ctor
  contract; W2 caller-translated; K1/K2 never raise). Count > 1 with
  NO landable owner — unifying couples independent envelope contracts.
- W2-C3 subclass-key posture unified (admit-normalize vs reject vs
  interrogate): D2/D3 ADMIT subclasses (downstream set-membership /
  ctor splat tolerate them); H1/H3/M4 REJECT (`type(k) is not str` —
  downstream hashing/compare must run `str`'s own); F2 INTERROGATES
  (methods under guard). Each downstream need differs; any unification
  breaks one downstream. Count 1 per site, no shared rule.
- W2-C4 shared materialize-once helper: the call `dict(m)` IS the shared
  primitive (a builtin); the per-site content is the FAILURE policy
  (X3: wrap/propagate/unbound/bounded + per-site message). A helper
  takes message + breadth flags → mode-flagged machinery. No new owner.
- W2-C5 shared unknown-key helper `reject_unknown(map, vocab, msg)`:
  vocabularies (X6), message shapes (X7: whole-list vs per-entry vs
  aggregate-with-others), and breadths (X8) all differ per site. The
  helper owns ~2 lines and every call site keeps its wording —
  relieves no change obligation. No landable owner.
- W2-C6 closest pair 1, D2 vs D3 (deployment pair): posit D2's bool
  fast path ported to D3 (`RESOURCE_POLICY=False` disables). D3's
  contract forbids it ("no spelling of this key disables a bound",
  `conf.py` RESOURCE_POLICY comment). Conversely an instance slot for
  APPLY_UPSTREAM_PATCHES is meaningless (no class). Shared SPELLING
  (gate→materialize→key-guard→unknown-reject) over disjoint accepted
  shapes + disjoint vocabs + disjoint value rules. Shape change moves
  exactly one. Count 1 each way.
- W2-C7 closest pair 2, RF exact-`str` trio H1/H3/M4: posit
  "admit behaving subclasses" (F2-style). H1 downstream splats
  `**kwargs` + exact-match injection compare; H3 downstream dict-sets
  + bound-name compare (pinned by the hostile-hash oracle); M4
  downstream `field_map.get` + dict-set. The reject-decision is
  per-downstream; the shared predicate `type(k) is not str` is one
  expression needing no owner; REPORTING differs (H1 sorted-offenders
  vs H3 all-errors-aggregate vs M4 immediate). Count 1 per site.
- W2-C8 entry-shape sub-pair H3 vs M4: posit "accept any 2-sequence".
  At HEAD both unpack under guard; reasons differ (H3 hook ergonomics
  vs M4 declaration strictness); reporting differs (aggregate vs
  immediate). Any wording-visible change stays count 2; the silent
  predicate is one line. The "SAME containment" comments record
  PRECEDENT (principle 10), not shared code. No owner.
- W2-C9 R-ident asymmetry F2 vs H3: at HEAD F2 HAS the identifier gate,
  H3 does NOT (run-7 R-ident routed to the maintainer, still accurately describes
  HEAD; the WT identifier gate is concurrent dirt). Posit "identifier
  keys required where hook keys become input attrs": moves H3 alone —
  and the DECISION is the maintainer's (no contract source), not a consolidation.
  Persistence across runs 7→9 proves the sites move alone.
- W2-C10 total-function pair K1 vs K2: posit "raise on hostile mapping".
  K1 MUST be total (any custom-scalar value → cache key; opaque token
  on hostility) or plan-cache lookup breaks; K2 MUST charge-and-queue
  (raise would turn budget accounting into mid-walk config errors).
  Count 0 — forbidden by both contracts.
- W2-C11 breadth ported (D2's whole-map-every-read → H2/K2/W2): breadth
  follows consumption (D2 app-load-cheap; K2 budget-bounded; W2
  caller-tailed). Each breadth moves alone. Count 1 per site.
- W2-C12 None→raise everywhere (F3's rule): D1's None→`{}` is the
  documented package-wide None stance (`conf.py` module docstring);
  W1/H2/M4/S1 None arms are each seam-contracted; F3 is the deliberate
  outlier (a hook MUST return a map). Unifying breaks documented
  contracts. Count N, no owner.

### W2 owner decision: NONE (reject as one rule)

Decomposition (each row stays owned where its contract lives):

- D1/D2: `conf.py` settings-shape rules (D2's vocab = patch-module
  registry; ladder-adjacent but shape-owned).
- D3: the f12 `resolve_policy` ladder (vocabulary rejection ladder-owned
  per f12-R14; consumption steps per-site here).
- M1/M2/M3: `types/base.py` per-key Meta validators (relay-gated pair +
  hints shape guard; downstream validators own values).
- M4/H3: `rest_framework/sets.py` file-local rows F-NESTVAL / F-SCHEMAMAP
  (adopted facets stay facets — see reconciliation).
- H1/H2: `rest_framework/resolvers.py` hook-boundary rule (C11 member).
- H4/H5: `rest_framework/inputs.py` nested-config rules (H5 already
  single-owned across its 2 callers).
- F1/F2/F3: `forms/inputs.py` basis rule (identifier gate file-local).
- S1/S2: scalar factory contract / converter read hardening.
- W1/W2: `utils/input_values.py` traversal primitives (W2 already
  single-owned front half; tails per caller by contract).
- W3: factory walk guard (silent-skip by contract; see W2-N2).
- P1/P2/P3: permission context-resolution rules (probe/fork/asymmetry).
- C1/C2/C3: `utils/context.py` accessor trio (per-direction contracts).
- K1/K2: plan-cache-key / budget-walk rules (total functions).
- X0: auth session boundary (sole mutability need).

Already-consolidated sub-clusters (a shared rule, where one existed,
already has exactly one owner — no remainder): H1 across its 3 hook
sites; H5 across its 2 callers; W2's front half across its 2 tails;
D1 across the Settings write sites. Each was verified single at HEAD.

### W2 matrix discharge

1. Cross-flavor: RF trio vs forms basis read both; R-ident asymmetry
   persists at HEAD (F2 gate, H3 none) — closest cross-flavor pair
   tested in W2-C9, rejected (domains/reporting/downstream differ).
2. Sync/async twins: inapplicable — every gate is pure sync validation;
   no await boundary, no twin.
3. Derived knowledge: each vocab derived once from its owner (dataclass
   fields, frozensets, live field_map); no re-derivation found; D3's
   per-call `known` set is a pure uncached derivation.
4. Inverse/round-trip: inapplicable — gates are one-way validators; K1
   keys are hash-consumed only (no inverse).
5. Other media: oracles pin each gate literally (H3's 6, M4's 15,
   hook-mapping non-mapping/unmaterializable/non-string-key rows,
   context pins); `conf.py` None-stance + f12/f13 prose are
   projections. No restatement found; each message names its own site.
6. Enforcement by omission: family enumerated (29); missing arms checked
   per member — H2/D1/S2 absences match stated contracts; M3 (W2-N1)
   and W3 (W2-N2) have NO contract source for the missing arm →
   verdict-neutral notes, not defects (axis-6 rule); R-ident already
   with the maintainer and still accurate at HEAD. No new defect.

### W2 verdict-neutral notes (observed, not defects)

- W2-N1 (M3 double-consumption): `_meta_optimizer_hints` iterates the
  RAW mapping for the key guard, then `dict(value)` re-iterates — a
  one-shot mapping passes the guard over one key set and copies
  another (silently dropped hints). No contract source (spec, owner
  prose, oracle) requires single-consumption of Meta mappings → per
  the axis-6 rule this routes to the maintainer-or-nothing, never `## Defects`.
  Recorded so a later trigger-check has the observation.
- W2-N2 (W3 silent-skip vs loud walker): the factory walk (W2-W3)
  silently yields zero branches for a non-mapping `related_map` while
  the permission walker fails loud on the same declaration via W2-W2.
  No contract source requires factory loudness (the factory never
  indexes, only iterates under guard) → note, not defect.

W2 F1 verdict (pre-findings): REJECT as one rule — 29 mechanism sites
across 10 subjects, varying independently on X1–X8; every posited
change forces count 1 per owning site or N with no landable owner;
the two closest pairs share spellings over per-site contracts that
move alone under every challenge. Owner: NONE.

### Reconciliation (post-findings — every difference explicit)

Census (W1 22/9 vs W2 29/10): the raw `isinstance`-`Mapping` line
count reproduces at exactly 22, but line 22 is the `:301` comment
restating the `:289` verdict (W2-D1, verdict-neutral count slip:
code sites = 21). Of the 21, `:1162` is a filter not a gate
(consumer, correctly unhomed). W1's prose homes 13 code sites fully
(D1–D3, M1–M4, H1–H5, F1–F2) plus 4 I missed
(`__init_subclass__` annotation gate, finalizer `_annotation_names`,
`_validate_meta` Meta-keys guard, `_validate_optimizer_hints`
second gate — all 4 verified at HEAD in reconciliation, all
per-subject rules separating on phase/reporting/inputs; W2-D4) and
boundaries I had not traced (canonical.py refusal posture,
`reject_unknown_meta_keys` already-single-owned, RF discovery
helpers, utils/inputs `:892`/`:1179`/`:1250`/`:1392`, querysets
SQL-identifier gates spot-verified, `_strawberry_patches`
multipart) — every one verified, every one separating. 8 of my
sites get no W1 prose home (C-trio, P1, P3, X0, S2, W3 — W2-D2):
each is independently challenged in W2-C1..C12 (C-trio: per-direction
contracts + file-local ownership; P1/P3: probe/fork/asymmetry vs
P2's readability tuple; X0: sole mutability need; S2: total
identity-scan read vs S1's admission collision check; W3:
silent-skip vs W2's loud front half) and each separates. No
consolidation hides in either direction; the UNION population is
fully homed across the two sections. F3 (None→raise) folds into
F2's home by delegation (W2-D6). Taxonomy: my 10th subject
(mutability) is W1's uncounted X0 (W2-D5). Census verdict: AGREE
in substance; F1 holds on the union.

F1 separation: CONFIRM. My X1–X8 map 1:1 onto W1's 8 axes and all
8 are genuine (X1 8 postures, X2 3+NA, X3 6 breadths, X4 5 key
policies, X5 6 value rules, X6 6+none vocab sources, X7 8 error
contracts, X8 7 breadths — each posture per-site owned). Closest
pairs: deployment (W2-C6 ≡ R-depl — bool-port forbidden at D3 by
its no-disable contract, instance-slot meaningless at D2; count 1
each way) and RF trio (W2-C7/C8 ≡ R-rf — one-expression predicate,
per-site reporting/downstream; predicate-only helper relieves no
change obligation). Dispatch stress changes all tested: value-shape
validation (W2-C1: N, no owner), shared hostile-key error type
(W2-C2: N, no owner — envelope contracts per boundary), subclass
posture unification as the serious form of case-folding (W2-C3:
admit/reject/interrogate per downstream; literal case-folding moves
≤1 — every vocab is case-sensitive by contract), materialize
helper (W2-C4: builtin already shared; failure policy per site),
vocab helper (W2-C5: wording/vocab/breadth per site). W1's C1–C5
re-derived independently and agreed. No change forces count > 1
with a landable owner. Owner: NONE (agreed).

R-depl/R-rf/R-types/R-forms/R-scalar/R-trav/R-meta: ALL CONFIRM —
each contract difference re-verified at HEAD bytes
(armor/whole-wrap/frozenset/exact-bool/app-load vs
no-armor/fields-vocab/ctor/schema-construction;
hook-returns-vs-field-maps-vs-Meta + request-vs-creation +
offenders-vs-aggregate-vs-fail-fast;
per-surface vocabs + live-then-copy disciplines;
identifier-strictly-stronger; type-keys + ValueError + collision;
5 postures / 5 consumers; namespace-scan vs mapping +
deferred-keys axis), each trigger concrete and landable-detectable.

R-seam/f12 boundary: CONFIRM EXACT. f12 R14 reserves "the vocabulary
rejection itself (valid names + display_name/unit wording),
ladder-specific" and offers "shared consumption hardening" as this
item's subject; W1 claims nothing ladder-owned and confirms
vocabulary varies per subject at every mapping-shaped site (C3).
"No trigger owed here" matches f12's "that item sets its own";
this item's triggers live in R-depl etc. Consistent both ways;
nothing re-litigated.

Adoptions-to-file-local: CONFIRM. C11 stays the file's hook-boundary
rule (J4's difference record undisturbed); F-SCHEMAMAP/F-NESTVAL
facets return to their file-local owners with challenges counting 1
there. No remainder on any facet's change. R-ident still
accurately describes HEAD (F2 gate present, H3 absent — verified;
WT identifier gate is concurrent dirt) and stays with the maintainer.

N1/N2: both correctly observed-not-homed, CONFIRM. N1: D3's
docstring promises hold (unhashable keys typed via the materialize
wrap since `dict()` hashes during construction; iteration failure
typed); the residual needs a stateful hostile `__hash__`
surviving materialize then detonating membership/`sorted` —
pathological, loud at construction, no contract source, hunt
lines. N2: live-iteration-then-copy verified at HEAD; no
single-consumption contract source; class-body literal in
practice; hunt file. N3 CONFIRMED via
`test_validate_optimizer_hints_non_string_keys` (direct call at
HEAD `tests/types/test_base.py:2529`). N4 CONFIRMED via docstring
+ `dict[object, object]` typing. My W2-N1 (M3, sibling pattern to
N2) and W2-N2 (W3) stand as same-class notes. 0 defects; no
`## Defects` entry owed by either worker.

Index rows: "no new index rows owed" ENDORSED (exact text for
Worker-0: flip the family row to rejected with the F1+R triggers;
transcription of adoptions already sits in the row's Files
covered). No new family named by either census; R-ident already
routed; notes are not rows.

Pending-"None": CORRECT → plain `verified`. Static-decidable;
zero-edit (no equivalence proof); oracles cited not re-run as
verdict evidence (correct: green proves nothing about count). No
`proof:`/`gate:` owed.

Cells: CORRECT — construction/class-creation/in-memory-entry
validation + source census; no database, alias, or dialect
decision.

Structural gate: ADEQUATE for zero-edit REJECT (gateless-by-design
sites make a mechanical gate unsound; per-site hostile oracles are
the operative gates; no new gate → no negative control owed).
Matrix: all 6 CONFIRMED (axis 1 extended by 8 W2 sites, all
separating; axes 2/4 inapplicability reasons sound; 3/5 searched;
6 enumerated with N1/N2 + documented gatelessness).
Enumeration: instruments reproduced — 117 files ✓; 22 lines incl.
1 comment (W2-D1); `could not be materialized` 3 line-hits, 4th
producer (M4) hidden by a split string but correctly classified
in C4 (W2-D3); `iteration failed` 2 functions ✓ (D2's double wrap
as described); exact-`str` 30+ with exactly 3 mapping-key gates ✓
(querysets boundary spot-verified as compiler-state sealing).
Freshness: 25/25 re-hash clean; 5/5 WT pins match dispatch; 5/5
WT pins match W1's full hashes (no drift since submission);
ITEM_BASELINE pins match WT; excluded modules fingerprinted.
Comparable; any change reopens.

Zero-edit: CONFIRMED — no `## Implementation`; item diff vs
ITEM_BASELINE is the plan edit alone; status count 462 reproduced
(`git status --porcelain | wc -l` = 268 untracked + 194 modified);
HEAD unmoved at `5c3496e0`. AGENTS.md diff check: tracked diff is
Worker-0's plan edit alone; ruff on touched tracked paths VACUOUS
(none — neither worker touched a tracked `.py`); artifact is
per-cycle scratch (raw `path:NN` allowed, no style cleanup owed).
Type gates re-run whole-package in the shared venv (slots 1–3
damaged per dispatch; shared venv stated): mypy clean (119
source files), basedpyright 0 errors / 0 warnings / 0 notes,
check_any 130 uses at 90 sites — all three match W1's
informational numbers exactly.

W2-D1..D6 are all verdict-neutral record slips in the f12/f13-D
precedent class (counts, prose homes, taxonomy); none names a
consolidation, so none spends the verdict. No `revision-needed`
candidate exists (every gap site separates under challenge); no
standing disagreement (W1/W2 agree on F1, owner NONE, and every
R-row). Verdict: verified, plain.

