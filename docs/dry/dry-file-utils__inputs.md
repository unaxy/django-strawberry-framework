# DRY review: `utils/inputs.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits, zero plan edits.

## System trace

Target `django_strawberry_framework/utils/inputs.py` is the generated-input
construction and lifecycle hub both the set families (filter / order) and the
three write flavors (model / form / serializer) build on. Set side: the
triple-emission scaffold (`emit_set_input_field_triples`), the BFS factory
substrate (`GeneratedInputArgumentsFactory`), the Layer-6 dynamic-set surface
(`make_dynamic_set_getter` + normalize / key / skeleton helpers), the heavy
namespace quartet, and the Decision-11 lazy helper. Write side: the
construction site (`build_strawberry_input_class`), the light namespace trio,
the sequence-shape gate + narrowing spine, the naming ladder
(`pascalize_token` / `generated_input_type_name` / `name_set_input_type_name`),
the collision walk, the shape-cache plumbing + spine, the decode-kind
vocabulary + conversion / reverse-map records, and the provided-fields walk.
Domain semantics stay at the call sites per the module docstring; what lives
here is mechanics both families import downward without a cycle.

Target identity and attribution. HEAD blob
`ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` (1823 lines); worktree blob
`b5af8255dfa18a2ff423cdd2de211723c5a15590` (1834 lines). `git diff HEAD`
shows 28 hunks, 120+/109-, every hunk attributed by content to
concurrent-external work, none to this item (zero edits made):

- Hunk 1 (imports): `..exceptions._safe_arg_repr/_safe_type_name` replaced
  by `from . import truth`.
- Hunks 2, 20, 28 (`emit_set_input_field_triples`, `duplicate_name_message`
  body, factory empty-message): `__qualname__` / `__module__.__qualname__`
  become `truth.qualname` / `truth.label`, plus reflow.
- Hunks 3-6 (`_sorted_meta_values`, `_hashable_meta_value`): the refusal
  translation wrapper drops to a bare return; new `_META_CONTAINER_TYPES` /
  `_UNORDERED_TYPES` / `_is_one_of` scaffolding; `isinstance` arms become
  `truth.is_instance` / `_is_one_of`; leaf `except BaseException` narrows to
  `TypeError`; docstring gains the real-class paragraph.
- Hunk 7 (`make_hashable_meta_value` docstring): "or raise from `__hash__`"
  becomes "(the unhashable `TypeError`)". The D1(a) `repr`-sorting paragraph
  is untouched diff context.
- Hunk 8 (`_set_meta_has` / `_set_meta_get`): new `_META_ABSENT` sentinel;
  `hasattr` / `getattr` become `truth.static_attr` reads; `isinstance`
  becomes `truth.is_instance`; docstring follows.
- Hunks 9-13 (`canonicalize_set_meta_fields`, `promote_set_meta_fields`,
  `make_set_meta_cache_key`, `normalize_set_meta_for_factory` x2):
  `isinstance` becomes `truth.is_instance` / `_is_one_of`;
  `_safe_type_name` becomes `truth.kind`; the normalize entry-dict wrapper
  drops its `try/except`; docstrings gain real-class sentences. The D1(c),
  D1(b), D1(d) `repr` claims are untouched diff context.
- Hunks 14-15 (`create_dynamic_set_class`): `isinstance`+`issubclass`
  becomes `truth.is_subclass`; `{model!r}` becomes `truth.render`;
  `__name__` becomes `truth.name`.
- Hunk 16 (getter stamp): two `# truth: ok` markers on the `__name__` /
  `__qualname__` writes.
- Hunk 17 (`normalize_field_name_sequence`): docstring +3 lines;
  `isinstance` becomes `truth.is_instance` / `_is_one_of`; `_safe_*`
  becomes `truth.render` / `truth.kind` / `truth.name`; `except
  BaseException` narrows to `TypeError`; `str.__str__` becomes
  `truth.text`.
- Hunks 18-19 (`build_strawberry_input_class`): the specs-tuple wrapper
  drops to a bare `tuple()`; triple/kwargs `except BaseException`
  narrows to `(TypeError, ValueError)`; `_safe_type_name` becomes
  `truth.kind`; `isinstance` becomes `truth.is_instance`.
- Hunks 21-22 (`build_lazy_input_annotation`, `iter_set_subclasses`):
  gate becomes `truth.is_subclass` + `truth.render`; subclass walk
  becomes the `type.__subclasses__` base slot with `id` dedup plus
  `# truth: ok` markers and docstring.
- Hunk 23 (`clear_generated_input_namespace`): `subclass.__dict__`
  becomes `truth.class_dict` plus comment.
- Hunks 24-27 (factory): `__bases__` becomes `truth.bases`;
  `__name__` becomes `truth.name` / `truth.render`; `seen: set[type]`
  becomes `set[int]` with `id` membership; `getattr` reads become
  `truth.static_attr`.

Every hunk is the shared-tree `truth.*` migration vocabulary
(`truth.is_instance/is_subclass/static_attr/qualname/name/label/kind/
render/text/bases/class_dict`, `# truth: ok` markers, `BaseException`
narrowing, `id` dedup) already attributed the same way by verified File
`utils/canonical.py`. `ITEM_BASELINE` blob for this path equals the
worktree blob (`b5af8255`; `git diff 722a927b -- <path>` empty), proving
zero worktree change since the item baseline: the dirt predates this item.
No `## Owned changes` ledger row names this file. This trace reads HEAD
bytes only; worktree bytes are fingerprinted, never reasoned from.

Consumers, classified (HEAD bytes; blobs are HEAD short ids). Production
importers of `..utils.inputs` (22 files, AST `ImportFrom` census over
`git show HEAD:` bytes of every package `.py`):

- Set families: `filters/inputs.py` (`82b52d97`: scaffold, both records,
  build site, heavy namespace, `optional_field_kwargs`, name delegate,
  subclass walk), `orders/inputs.py` (`6f6ec946`: same minus
  `optional_field_kwargs`), `filters/factories.py` (`ad5634c4`: BFS base,
  getter, alias), `orders/factories.py` (`b9fd62bc`: BFS base, getter),
  `filters/sets.py` (`993e887a`: alias + `promote_set_meta_fields`),
  `orders/sets.py` (`6044ab1a`: promote + `read_set_meta_fields`),
  `filters/__init__.py` + `orders/__init__.py` (Decision-11 bodies).
- Write flavors: `mutations/inputs.py` (`fc442047`: kinds, record, build
  site, collision walk, light namespace, name-set spine, token,
  `resolve_effective_fields`, `optional_input_field`),
  `mutations/sets.py` (`7800bd53`: shape-cache pair + spine, sequence
  gate), `mutations/resolvers.py` (`043a2d0b`: kind constants `FILE` /
  `RELATION_MULTI` / `RELATION_SINGLE` for the decode dispatch),
  `forms/inputs.py` (`6418753d`: record, build site, drop guard,
  collision walk, light namespace, name-set spine, `optional_input_field`,
  narrowing spine), `forms/sets.py` (shape-cache pair),
  `forms/converter.py` (kind re-exports + `FieldConversionBase`),
  `rest_framework/inputs.py` (`2410f380`: record, build site, skeleton
  name, spine, drop guard, collision walk, light namespace, shape-cache
  pair, sequence gate, `optional_input_field`, token, narrowing spine),
  `rest_framework/sets.py` (sequence gate),
  `rest_framework/serializer_converter.py` (kind re-exports + base +
  record), `rest_framework/resolvers.py` (`0d302782`:
  `optional_input_field` agreement recompute only).
- Cross-cutting: `auth/queries.py` (light namespace, 4th rider),
  `extensions/resource_policy.py` (`RELATION_MULTI` value-budget read at
  :718), `utils/write_values.py` (`iter_provided_input_fields` decode
  spine + 3 kind constants), `utils/converters.py` (`SCALAR` +
  `FieldConversionBase` for its converter factories).

Composed-by-name inputs (not rules of this file):
`exceptions.py::ConfigurationError/_safe_arg_repr/_safe_type_name`,
`canonical.py::base_container_values/canonical_sort_key` (`b9ded33b`),
`imports.py::import_attr_if_importable` (`291ecedd`),
`strings.py::flatten_lookup_path/graphql_camel_name` (`991f7dad`),
`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` +
`SetLifecycleAttrs.binding_attrs` (`ad8987ea`).

Oracles: `tests/utils/test_inputs.py` (`598f1440`; 61 test functions with
literal pins: names, wordings, `__code__`-identity twin-closure gate,
no-private-alias gate, `CategoryAutoFilter` / `CategoryAutoOrder`
spellings — independent of the owner), the family test modules
(`tests/filters/test_factories.py` `ffd06ab7`,
`tests/orders/test_factories.py` `4ec2ec05`, both `test_inputs.py`
modules exercising the `_camel_case` / `_iter_*` / `build_input_class`
aliases), and the structural ratchet
`tests/rest_framework/test_dry_import_ratchet.py` (object-identity pins
that the serializer flavor imports, never redefines, the substrate).
Projections: the target module docstring (incl. the parked-globals
lifecycle paragraph every clear surface cross-references); spec-027 /
spec-028 / spec-036 / spec-038 / spec-039 Decision prose; the
`input-type-generation` glossary anchor (shipped `0.0.11`).

## Verification

### Enumeration

Instrument: every name in `ast.Module.body` of the HEAD bytes
(`ee31d360`, 1823 lines), read via `git show HEAD:` plus an AST dump.
Count: 60 nodes. Every member lands below; nothing is unassigned.
(A = adoption/convergence into an open or verified family, transcribes
nothing; FL = file-local; R = rejection; F-NEW = new family named for
Worker 0.)

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (mechanics-vs-semantics split, parked-globals lifecycle) | Projection at the owner; FL-mechanics prose |
| 1 | `from __future__ import annotations` | Mechanics; no rule |
| 2 | `import sys` (`sys.modules` pinning) | Mechanics; no rule |
| 3 | `collections.abc` (`Callable`, `Iterator`, `Mapping`) | Mechanics; no rule |
| 4 | `dataclasses.dataclass` (two records) | Mechanics; no rule |
| 5 | `typing` (`Annotated`, `Any`, `ClassVar`) | Mechanics; no rule |
| 6 | `import strawberry` (`UNSET`, `lazy`, `field`, `input`) | Mechanics; no rule |
| 7 | `django.db.models as django_models` (model gate) | Mechanics; no rule |
| 8 | `..exceptions` (`ConfigurationError`, `_safe_*`) | Consumer link; wordings converge R-wordings |
| 9 | `.canonical` (`base_container_values`, `canonical_sort_key`) | Consumer link; arms dual-home A-baseslot / A-membership |
| 10 | `.imports` (`import_attr_if_importable`) | Consumer link; member 57 converges A-imports |
| 11 | `.strings` (`flatten_lookup_path`) | Consumer link; no rule here |
| 12 | `.strings` (`graphql_camel_name as graphql_camel_name` re-export) | FL-mechanics (re-export rule; oracle-pinned) |
| 13 | `GeneratedInputFieldSpec` | FL-set-provenance-record |
| 14 | `set_input_type_name` | FL-set-name-delegate (+ R-naming-ladder leg) |
| 15 | `optional_field_kwargs` | FL-set-optional-tail (+ R-alias-arm leg) |
| 16 | `optional_input_field` | FL-write-widen-tail (+ R-alias-arm leg) |
| 17 | `emit_set_input_field_triples` | FL-set-triple-emit-scaffold (+ R-collision-quartet leg) |
| 18 | `SCALAR` | FL-decode-kind-vocabulary |
| 19 | `RELATION_SINGLE` | FL-decode-kind-vocabulary |
| 20 | `RELATION_MULTI` | FL-decode-kind-vocabulary |
| 21 | `FILE` | FL-decode-kind-vocabulary |
| 22 | `FieldConversionBase` | FL-conversion-value-shape |
| 23 | `InputFieldSpec` | FL-write-reverse-map-record (+ R-record-shapes leg) |
| 24 | `make_input_namespace` | FL-light-input-namespace |
| 25 | `make_set_input_namespace` | FL-heavy-set-namespace |
| 26 | `_opaque_meta_value` | A-dynamic-getter (+ R-opaque-key converge leg) |
| 27 | `_sorted_meta_values` | A-dynamic-getter |
| 28 | `_MAX_META_VALUE_DEPTH` | A-dynamic-getter (+ R-depth-caps leg) |
| 29 | `_hashable_meta_value` | A-dynamic-getter; :523 dual-homes A-baseslot, :493-502 dual-homes A-membership |
| 30 | `make_hashable_meta_value` | A-dynamic-getter (+ D1 limb a) |
| 31 | `FILTERSET_FIELDS_ALIAS` | A-dynamic-getter |
| 32 | `_set_meta_has` | A-dynamic-getter (+ R-meta-duality leg) |
| 33 | `_set_meta_get` | A-dynamic-getter (+ R-meta-duality leg) |
| 34 | `resolve_set_meta_fields` | A-dynamic-getter |
| 35 | `canonicalize_set_meta_fields` | A-dynamic-getter; :632 dual-homes A-baseslot (+ D1 limb c) |
| 36 | `promote_set_meta_fields` | A-dynamic-getter |
| 37 | `read_set_meta_fields` | A-dynamic-getter |
| 38 | `make_set_meta_cache_key` | A-dynamic-getter (+ D1 limb b) |
| 39 | `normalize_set_meta_for_factory` | A-dynamic-getter (+ D1 limb d) |
| 40 | `create_dynamic_set_class` | A-dynamic-getter (+ R-model-gate leg) |
| 41 | `make_dynamic_set_getter` | A-dynamic-getter; :873-886 miss path dual-homes F-NEW |
| 42 | `make_shape_build_cache` | FL-shape-cache-plumbing |
| 43 | `get_or_store_shape_build` | FL-shape-cache-spine; F-NEW owner candidate |
| 44 | `pascalize_token` | FL-injective-token-encoder (+ R-token-encoder leg) |
| 45 | `generated_input_type_name` | A-provisional-name (owner) |
| 46 | `name_set_input_type_name` | FL-name-set-spine (+ R-naming-ladder leg) |
| 47 | `normalize_field_name_sequence` | FL-sequence-shape-gate (+ R-sequence-gates leg) |
| 48 | `resolve_effective_fields` | FL-narrowing-spine |
| 49 | `guard_dropped_required` | FL-drop-detection (+ R-model-guard routed to the maintainer) |
| 50 | `iter_provided_input_fields` | FL-provided-walk (+ R-provided-vs-set-walk leg) |
| 51 | `build_strawberry_input_class` | FL-construction-site |
| 52 | `materialize_generated_input_class` | FL-park-global-entry |
| 53 | `duplicate_name_message` | FL-collision-skeleton (+ R-name-vs-orphan leg) |
| 54 | `iter_input_field_collisions` | FL-write-collision-walk (+ R-collision-quartet leg) |
| 55 | `build_lazy_input_annotation` | FL-lazy-helper-body |
| 56 | `iter_set_subclasses` | FL-subclass-walk (+ R-graph-walks leg) |
| 57 | `_safe_import` | FL-heavy-clear-body (+ A-imports converge leg) |
| 58 | `clear_generated_input_namespace` | FL-heavy-clear-body (+ A-clear-bus converge leg) |
| 59 | `GeneratedInputArgumentsFactory` | A-factory-bfs (owner side) |

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. Both set flavors read whole
   (`filters/inputs.py`, `orders/inputs.py`: emission closes over the
   scaffold with family closures; operator bag is filter-only per
   spec-028 Decision 8, verified R-bag); all three write flavors read
   whole (model / form / serializer share the construction site, the
   narrowing spine, the naming ladder, the collision walk, the shape
   caches, and the kind vocabulary — each census closed in System trace).
   Genuine splits: leaf semantics (`leaf_of`), full-vs-descriptor name
   identity (serializer), `empty_message` / `source_of` / `waived`
   seams (each with stated owner prose), the model guard omission (O1,
   routed to the maintainer for lack of a contract source either way). No second
   owner found for any shared rule.
2. Sync/async twins — NO SUCH SURFACE. `git show HEAD:` grep for
   `async ` / `await ` / `sync_to_async` / `asyncio`: zero hits. Every
   member is construction-time or pure in-memory computation (class
   building, name derivation, namespace reset); no executor, no I/O, no
   await point. All consumers call from synchronous finalize / bind /
   clear paths.
3. Derived rather than repeated knowledge — SEARCHED. Names: three
   derivations, three rules — class-derived (`set_input_type_name` via
   `type_name_for`), name-set-derived (`name_set_input_type_name`),
   descriptor-derived (serializer; verified
   `serializer-descriptor-identity` file-local row) —
   R-naming-ladder. Field sets: one narrowing spine, three bases
   (FL-narrowing-spine). Defaults: the required-vs-optional contract
   lives once at the construction site; both tails exist to satisfy it
   (R-alias-arm for the shared 2-line arm). Membership: spelled 3x →
   A-membership. Miss path: spelled 3x → F-NEW. Token encoding:
   injective vs lowercasing pair → R-token-encoder.
4. Inverse / round-trip pairs — SEARCHED, no duplication. Emit
   (`emit_set_input_field_triples` + `FieldSpec` rows) vs normalize
   (family `normalize_input_value` walkers over those rows): one grammar,
   two halves, the record is the seam — no second encoder. Build
   (`build_strawberry_input_class`) vs provided-walk
   (`iter_provided_input_fields`): construct vs UNSET-strip, halves not
   twins. Ledger write (`build_lazy_input_annotation`) vs orphan read
   (finalizer subpasses 3-4): protocol halves over family-owned ledger
   sets. Materialize (park + ledger) vs clear (ledgers only): the
   parked-globals asymmetry is the owned rule, stated once. Get vs store
   (spine vs Layer-6 inline vs Range inline): same half three
   times → F-NEW.
5. Contracts restated in another medium — SEARCHED. Every medium a
   change moves is classified in System trace. Oracles spell literal
   pins, `__code__` identity, and no-private-alias gates; none reads
   the owner. One projection defect homed (D1: four docstring limbs
   claim bare-`repr` sorting where bodies use `canonical_sort_key`,
   judged fresh below) plus one same-shape limb outside the target (D2:
   `orders/sets.py:460`, owner verified File `orders/sets.py`).
6. Enforcement by omission — SEARCHED. `guard_dropped_required`: form
   (x2 guards) + serializer enforce; model omits with no contract
   source either way → R-model-guard routed to the maintainer (not a defect: no
   contract row broken). `read_set_meta_fields`: orders expansion
   reads; filters expansion is upstream-owned (`FilterSetOptions` +
   django-filter `get_filters`; Layer-6-created classes still agree
   because the factory canonicalizes before `type(...)`) — structural,
   not a gap. `optional_field_kwargs` direct call: filter logic-bag
   only; orders has no bag (Decision 8). `source_of` third arm:
   serializer-only (DRF-only axis). `waived`: serializer-only (form
   has no injected-field mechanism — owner prose). `empty_message`:
   model passes none (override-aware guard downstream — owner prose).
   `Mapping` leniency in `_ensure_built` vs strict sequence gates:
   BFS tolerance vs declaration validation, different jobs. No other
   omission; nothing else routes to the maintainer.

Standing triggers checked: `_request_body` J1 (shared `except` guard —
6 translating arms (`:480`, `:752`, `:1102`, `:1292`, `:1312`,
`:1320`), each translating a per-site failure into a per-subject
`ConfigurationError`; `:537` is an opaque-fallback, `:1586` an
attr-leniency, `:516` a `try/finally` with no `except` — none a
translation; CONVERGE with the standing J1 direction) and J2 (shared
exact-type gate — the `type(name) is not str` read and per-site
`isinstance` dispatches; CONVERGE with the standing J2 direction);
`utils/policies.py` R3
(per-subject-rejection-grammars — every refusal wording names its own
subject; CONVERGE); `utils/canonical.py` R1 (opaque token vs sort key;
CONVERGE); `serializer-descriptor-identity` name-set-vs-descriptor
split (CONVERGE);
`utils/imports.py` FL1 (`_safe_import` distinguished consumer;
CONVERGE); verified `subsystem-clear-lifecycle` (set-family clear
closures are bus members; CONVERGE); open `traversal-depth-cap-check`
(`_MAX_META_VALUE_DEPTH` distinguished — R-depth-caps); open
`registered-djangotype-definition-validation` (model gate
distinguished — R-model-gate). All unfired for this target.

### Challenges

Each rule, changes posited on its variation axes, authoritative
definitions counted (consumers, oracles, projections listed, never
counted). All counts against HEAD bytes.

| # | Rule | Changes posited | Count | Home |
|---|---|---|---|---|
| C1 | BFS walk + collision + cache + guard | 9th hook attr; FIFO->LIFO; new registry shape | 1 (base; 2 family declarations, not definitions) | A-factory-bfs |
| C2 | Dynamic-set skeleton (normalize/key/`type()`) | New normalize equivalence; new key branch; new skeleton gate | 1 per helper; 0 in families | A-dynamic-getter |
| C3 | Synonym rule (resolve/promote/read) | New alias; precedence flip; alias-drop change | 1 (spine) + 2 metaclass declarations | A-dynamic-getter |
| C4 | Provisional skeleton name | Suffix-rule change; full-vs-derived branch change | 2 (owner + `resolvers.py:1213` restatement = family evidence) | A-provisional-name |
| C5 | Base-slot reads | Snapshot-vs-live; sixth type | Disagree today / couples FA+FB (family items' questions) | A-baseslot |
| C6 | Container membership | Drop `frozenset`; add a type | 3 spellings (family evidence) | A-membership |
| C7 | Shape-cache get-or-store | Return stored-vs-built; miss counter; miss-order change | 3 (spine :938 + getter inline :874 + Range inline `filters/inputs.py:743`) | F-NEW |
| C8 | Set provenance record | 4th name; key-shape change | 1 (record; 2 aliases follow, not definitions) | FL-set-provenance-record |
| C9 | Triple-emission scaffold | New collision axis; new placeholder shape | 1 (scaffold) + 2 hook delegates | FL-set-triple-emit-scaffold |
| C10 | Decode-kind vocabulary | 5th shared kind; flavor axis change | 1 (vocabulary; flavor tables adopt) | FL-decode-kind-vocabulary |
| C11 | Conversion value shape | New axis; required-ness source change | 1 (base; 2 subclasses inherit) | FL-conversion-value-shape |
| C12 | Reverse-map record | New axis; serializer-only axis change | 1 (record; optional-default rule holds) | FL-write-reverse-map-record |
| C13 | Light/heavy namespaces | Idempotency change; clear-scope change; 5th rider | 1 per half (heavy composes light) | FL-light/heavy-namespace |
| C14 | Token encoder | New escape; head-rule change | 1 | FL-injective-token-encoder |
| C15 | Name-set spine | Token-order change; full-compare change | 1 (spine; 2 flavor wrappers follow) | FL-name-set-spine |
| C16 | Sequence-shape gate | New rejected shape; wording change | 1 (gate; flavor labels are params) | FL-sequence-shape-gate |
| C17 | Narrowing spine | New branch; order-of-checks change | 1 (spine; 4 knobs are params) | FL-narrowing-spine |
| C18 | Drop detection | Arithmetic change; new waived source | 1 (core; wordings stay per flavor) | FL-drop-detection |
| C19 | Provided-walk | UNSET-strip change; field-source change | 1 (walk; 3 flavors follow via the spine) | FL-provided-walk |
| C20 | Construction site | Required-contract change; pinning change; new kwarg | 1 (site; 5 builder call sites follow) | FL-construction-site |
| C21 | Park-global entry | Idempotency change; pinning change | 1 (entry; 6 namespace riders follow) | FL-park-global-entry |
| C22 | Collision skeleton | Sentence change; new noun | 1 (skeleton; 2 callers follow) | FL-collision-skeleton |
| C23 | Write collision walk | 4th arm; consumption-policy change | 1 (walk; policies stay at call sites) | FL-write-collision-walk |
| C24 | Lazy-helper body | Gate change; ref-form change | 1 (body; 2 family helpers follow) | FL-lazy-helper-body |
| C25 | Heavy clear | Best-effort change; reset-set change | 1 per half (import wrapper; `binding_attrs` declaration) | FL-heavy-clear-body |
| C26 | Subclass walk | Order change; liveness-rule change | 1 | FL-subclass-walk |
| C27 | Hashable walk (sort/depth/cycle/opaque) | Sort-key change; bound change; marker change | 0 here for ordering (composed by name from `canonical.py`), 1 per local rule | A-dynamic-getter |
| C28 | Module mechanics | New import; manifest posture change | 0 rules (no `__all__`; ratchet pins identity) | FL-module-mechanics |

No read-only probe was needed: every claim above is decided statically
against HEAD bytes (definition counts, import census, per-symbol
consumer censuses, grep-verified absences), so no `docs/dry/temp-tests/`
scope was created and no pytest ran. No workspace runs at all (all
inspection read-only in the shared tree: `git rev-parse` / `git show` /
`git grep HEAD` / `git hash-object` / worktree greps; nothing
source-mutating).

## Findings

### A-factory-bfs — CONVERGE into open `set-arguments-factory-bfs` (transcribes nothing)

Member 59 is the owner side the family row names
(`utils/inputs.py::GeneratedInputArgumentsFactory`): the BFS walk
(`_ensure_built`: FIFO queue, enqueue-time `seen` gate, per-class
collision check via the shared skeleton, idempotent
`input_object_types` cache), the 8 annotation-only hook attrs (a
forgetful family `AttributeError`s instead of sharing the base
namespace), the `__init_subclass__` grand-subclass rejection, the
`_collision_registry` property, the `arguments` ensure-then-index pair,
and `_build_class_type` (family-hook call + the zero-field remedy
wording passed as `empty_message` to the construction site, leaving
the rejection itself there). Fresh trigger checks, all unfired: both
family declarations still subclass the base directly (verified import
+ MRO shape at `ad5634c4` / `b9fd62bc`); the hook delegates are still
exactly the two `_build_input_fields` (+ filter `_build_logic_fields`);
consumers still the finalizer phase-2.5 subpass-5 materialization loop
and both heavy clears. C1 counts 1. No boundary change proposed.

Freshness: target HEAD `ee31d360`; `filters/factories.py`
`ad5634c4`, `orders/factories.py` `b9fd62bc`, `filters/inputs.py`
`82b52d97`, `orders/inputs.py` `6f6ec946`, `types/finalizer.py`
`de34ae2a` (all HEAD blobs; worktrees dirty, NOT traced).

### A-dynamic-getter — CONVERGE into open `dynamic-set-class-getter` (transcribes nothing)

Members 26-41 are the skeleton + helpers the family row names
(`make_dynamic_set_getter` + `normalize_set_meta_for_factory` +
`make_set_meta_cache_key` + `create_dynamic_set_class` +
`resolve_set_meta_fields`, plus the alias, promote/read/canonicalize,
`_set_meta_*` duality, and the hashing helpers). Fresh evidence,
re-derived at HEAD: both family getters are still bare
`make_dynamic_set_getter(...)` constructions
(`filters/factories.py:127`, `orders/factories.py:113`); the deferred
surface is still build-and-test-only — package-wide census for
`get_filterset_class` / `get_orderset_class` / `_get_*` finds zero
production callers outside the two factories (one in-target docstring
mention only); both metaclasses still call `promote_set_meta_fields`
with / without the alias; orders expansion still reads via
`read_set_meta_fields`. C2/C3/C27 count 1 per helper. The getter's
inline miss path (:873-886) additionally dual-homes to F-NEW below;
the hashing arms dual-home to A-baseslot / A-membership. No boundary
change proposed.

Freshness: target HEAD `ee31d360`; `filters/sets.py` `993e887a`,
`orders/sets.py` `6044ab1a`, factories + inputs blobs as in
A-factory-bfs (all HEAD; worktrees NOT traced).

### A-provisional-name — CONVERGE into open `canonical-input-provisional-name` (transcribes nothing)

Member 45 is the owner the family row names
(`utils/inputs.py::generated_input_type_name`): suffix rule +
full-vs-derived branching. Fresh evidence: the 5 composed calls all
still route through it (walk provisional at
`rest_framework/inputs.py:1692`, injected-specs provisional at :838,
`describe_serializer_input` canonical at :938,
`serializer_input_type_name` at :1105, plus the name-set spine :1041
in-target); the one restatement still stands at
`rest_framework/resolvers.py:1213`
(`f"{type(serializer).__name__}{'PartialInput' if ... else 'Input'}"`,
inside `_assert_field_agreement`); the descriptor-derived-name split
(name-set flavors compute token + full-shape here, serializer
supplies its own digest + decision) is unchanged. C4 counts 2 = the
family's evidence. No boundary change proposed.

Freshness: target HEAD `ee31d360`;
`rest_framework/inputs.py` `2410f380`,
`rest_framework/resolvers.py` `0d302782` (HEAD blobs; worktrees NOT
traced).

### A-baseslot — CONVERGE into open `base-slot-container-reads` (transcribes nothing)

Two inline restatements dual-home to the family the verified File
`utils/canonical.py` FA names (owner candidate
`base_container_values`): the `_hashable_meta_value` dict arm (:523
`dict.items(v)`) and the `canonicalize_set_meta_fields` dict branch
(:632 `dict.items(fields)`). Both build eagerly (tuple / dict
comprehension), matching the family's eager leg. The five
`base_container_values(...)` CALLS in this file (:481, :529, :533,
:695, :702) are consumers, not members; the `dict.get` / `dict.items`
reads on framework-built `safe_meta` (:688-689, :710, :753) are
framework-owned-container reads, excluded on the strength of their
bodies (converge with the canonical artifact's exclusion). C5 is the
family item's question, not this item's answer.

Freshness: target HEAD `ee31d360`; `utils/canonical.py` HEAD
`b9ded33b` (per the verified canonical artifact at this same HEAD).

### A-membership — CONVERGE into open `canonical-container-membership` (transcribes nothing)

The five-type gate in `_hashable_meta_value` (:493-502, order
dict/set/frozenset/list/tuple) dual-homes to the family the verified
File `utils/canonical.py` FB names: it is one of the three spellings
(the others: the `write_transaction.py` gate and the canonical
dispatch). The per-shape `isinstance` dispatches below it (:517,
:526) and in `make_set_meta_cache_key` (:690-698) dispatch, not
re-define, the membership (converge with the canonical artifact's
exclusion); `_sorted_meta_values` is ungated by design (translates
the refusal; converge with the exclusion). C6 counts 3 = the family's
evidence.

Freshness: target HEAD `ee31d360`; `utils/canonical.py` HEAD
`b9ded33b`, `utils/write_transaction.py` HEAD `eca9ad4d` (per the
verified canonical artifact at this same HEAD).

### A-clear-bus — CONVERGE into verified `subsystem-clear-lifecycle` (transcribes nothing)

The set-family `clear_fn` closures built by member 25 are bus members:
both `clear_*_input_namespace` wrappers register into
`registry.clear()` via `register_subsystem_clear` (same shape as the
verified rest-framework + optimizer rows). The helper BODY (members
57-58: best-effort lookups + binding-attr `delattr` walk) stays
file-local (FL-heavy-clear-body): the bus owns WHEN clears run, this
module owns WHAT a set-family clear resets. Converge verified on
fresh evidence (both registrations re-read at HEAD).

### A-imports — CONVERGE into verified `imports-best-effort-attr-lookup` (transcribes nothing)

Member 57 (`_safe_import`) is the distinguished consumer the verified
File `utils/imports.py` FL1 row records: it delegates to
`import_attr_if_importable` and adds the lifecycle's own rule
(`AttributeError` -> `None`, partial-load tolerance). Converge on
fresh evidence; the attr-lenient shape itself is homed file-local
(FL-heavy-clear-body).

### F-NEW — Shape-build get-or-store (NEW family `shape-build-get-or-store`, open)

Contract: an UNBOUNDED per-shape generated-input build cache
returns THE stored object on a hit and stores `factory()` on a miss,
with None as the miss signal — get, None-check, build, store,
return, in that order; no hit validation, no copy-out, no eviction,
no other miss signal. Variation axes: key identity (pre-build name
set vs post-build descriptor vs normalized-meta tuple vs Range
generation identity — all key-shape, all at call sites) and cache
location (family dict vs per-instance dict — likewise at the call
site, since the spine takes the dict as a parameter); build timing
via the factory closure.

Sites + roles: definition `utils/inputs.py::get_or_store_shape_build`
(:920-943; riders: model bind, form `cached_build_input`, serializer
`dedupe_serializer_input_shape` — all three verified composing at
HEAD); second spelling `make_dynamic_set_getter.<get_set_class>`
(:873-886: `cache.get` -> None-check -> `create_dynamic_set_class`
-> store -> return); third spelling
`filters/inputs.py::_build_range_input_class` (:743-752: `cache.get`
-> None-check -> `build_input_class` -> store -> return over the
per-instance `_range_input_classes` dict keyed by the full
generation identity). All three bodies are identical modulo the
build expression; the Layer-6 and Range uses (pre-build key +
generator factory) are exactly the shape the spine's docstring
blesses ("a pre-build key puts the generator in the factory").
Oracles: `test_get_or_store_...` (:882),
`test_write_flavor_shape_caches_share_get_or_store_owner` (:897,
pins the three riders), `test_make_dynamic_set_getter_...` (:805,
pins getter behavior incl. cache collapse),
`test_build_range_input_class_is_cached_on_the_filter_instance` and
`test_build_range_input_class_cache_is_keyed_by_owner_field_and_scalar`
(`tests/filters/test_inputs.py:1168/:1180`, pin the Range member).
Population: 3 members, closed by the package-wide
`git grep -n 'cache\.get(\|cache\[' HEAD --
django_strawberry_framework/` census (21 hits = 3 member pairs +
12 census-exclusion hits + 3 comment non-sites at `walker.py:1232`,
`types/resolvers.py:548`, `querysets.py:3541`), plus 2 off-census
exclusions below (BFS `not in`, materialize `ledger.get`).

Challenges: C7 counts 3 (return-stored-vs-built, miss counter,
miss-order each move all three). Owner candidate: the spine
(existing owner by responsibility: three riders already depend on
it; migration is one composed call each in the getter and the Range
builder — the Range dict's per-instance lazy attach stays at its
call site, orthogonal to the get-or-store).

Exclusions, each with its contract difference (all re-read at HEAD;
each falls out of the restated rule explicitly):

- BFS `if target_name not in input_object_types: build` (:1769-1770)
  — a graph-ensure building N classes per call with the collision
  gate interleaved, the store in `_build_class_type`, and
  return-via-property: not a slot get-or-store (see R-graph-walks).
- `materialize_generated_input_class` (:1395-1411) —
  idempotency-plus-RAISE: a same-name distinct-class entry raises
  instead of building; no miss path exists.
- `connection.py:1506` (`_connection_type_cache`) —
  provenance-check-on-hit: a warm cache serves only when
  `cached.definition is definition`, else raises; the rule returns
  unconditionally.
- `filters/sets.py:172` (`_lookups_for_field_class_cache`) —
  copy-out: the hit returns `list(cached)`, an equal-but-distinct
  object, so callers cannot corrupt the memo; the rule returns THE
  stored object (identity is load-bearing for registered classes).
- `optimizer/extension.py:610` (`_doc_key_cache`) and `:1333`
  (`_plan_cache`) — bounded LRU + eviction: hits promote
  (`move_to_end` with race guards), misses evict past the budget;
  the plan cache adds a cacheability gate plus a second
  per-execution tier. The rule is unbounded with no eviction.
- `types/definition.py` subscript memos (`:306/:347`
  `_related_target_cache`, `:367/:370`
  `_custom_id_resolver_cache`) — key-absence miss signal:
  `in`-then-`[]` caches None results (the related-target memo
  stores pre-resolution Nones, gated on `registry.is_finalized`);
  the rule's miss signal is None-absence.

Freshness: target HEAD `ee31d360`;
`filters/inputs.py` `82b52d97`, `connection.py` `4894f90f`,
`filters/sets.py` `993e887a`, `optimizer/extension.py` `e0e53a8e`,
`types/definition.py` `fa6c4d33` (all HEAD blobs; worktrees NOT
traced).

### FL-set-provenance-record — `GeneratedInputFieldSpec` (file-local)

The 3-name record (python attr / GraphQL name / Django source path)
the runtime normalizers walk, re-exported as `FieldSpec` by both set
families, tabled under `(set_cls, python_attr)` by the scaffold with
atomic stage-then-commit. C8 counts 1; reconsideration trigger: a
second provenance record for generated set inputs, or a third
consumer needing a 4th name the record refuses.

Freshness: target HEAD `ee31d360`.

### FL-set-name-delegate — `set_input_type_name` (file-local)

Thin root-name delegate to
`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for()` whose rule
is the PINNING: both family `inputs` modules re-export it as
`_input_type_name_for` (live consumers: both Decision-11 bodies +
both hook params + the factory's three internal calls) so no caller
wraps `type_name_for` again. Reconsideration trigger: a caller
deriving a set input name without this delegate.

Freshness: target HEAD `ee31d360`; `sets_mixins.py` HEAD `ad8987ea`.

### FL-set-optional-tail — `optional_field_kwargs` (file-local)

Every generated set input field is optional-with-`None` (an omitted
`default` means REQUIRED at the construction site) plus the
non-identity GraphQL alias. Riders: the scaffold (both families) +
the filter logic-bag builder. Reconsideration trigger: a set input
needing a non-`None` default or a second optional-tail spelling.

Freshness: target HEAD `ee31d360`.

### FL-write-widen-tail — `optional_input_field` (file-local)

The per-field tail the three write builders share: carry any `name=`
alias; when `widen` (per-flavor nullability rule, computed at call
sites), widen to `T | None` defaulting `strawberry.UNSET` (omittable)
else NO default (GraphQL-enforced presence). Fourth rider:
`rest_framework/resolvers.py:1215` re-derives the runtime annotation
through it for the schema/runtime agreement check (verified
R-recompute separation: recompute-vs-produce stay distinct).
Reconsideration trigger: a write input needing a third tail shape.

Freshness: target HEAD `ee31d360`.

### FL-set-triple-emit-scaffold — `emit_set_input_field_triples` (file-local)

Mechanics-here / semantics-at-call-site split: flatten -> camel ->
optional kwargs -> related-lazy-ref (with `Related*(None, ...)`
skip) vs `leaf_of` branch, plus the `FieldSpec` stage-then-commit and
the two-axis parity guard (flatten collision + camel collision).
Riders: both `_build_input_fields` with family closures.
Reconsideration trigger: a third set family, or a guard axis the
domain guards cannot see (see R-collision-quartet for the deliberate
non-unification).

Freshness: target HEAD `ee31d360`.

### FL-decode-kind-vocabulary — `SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE` (file-local)

The one-conceptual-enum vocabulary with the documented extension
rule: flavors extend at their own modules (`NESTED_*` DRF-only,
`EXCLUDED` model-only), converters re-export the four so existing
paths keep working. Consumers: 3 flavor converters + 3 flavor
resolvers + the resource-policy value walker. Reconsideration
trigger: a fifth SHARED kind, or a flavor re-spelling a shared kind.

Freshness: target HEAD `ee31d360`.

### FL-conversion-value-shape — `FieldConversionBase` (file-local)

The annotation + kind + required-ness value object behind both
flavor conversions (`SCALAR` default so consumer-registered
converters need not import the kinds; relation/file pass `kind`
explicitly; flavor tables store `make_*_converter` callables so the
VALUE shape stays one site). Reconsideration trigger: a conversion
axis the base cannot carry, or a hand-constructed shape bypassing
the factories.

Freshness: target HEAD `ee31d360`; `utils/converters.py` HEAD
`5332f054`.

### FL-write-reverse-map-record — `InputFieldSpec` (file-local)

The unified reverse-map record: neutral `target_name` decode key +
`input_attr` / `graphql_name` / `kind`, with the serializer-only
axes (`source`, `related_model`, `nested_specs`) as optional
defaults so form/model never carry unused mode flags, plus
`annotation_repr` / `required` for the agreement checks. All three
write flavors stamp it; the decoders route on `kind` through the
shared spine. Reconsideration trigger: a flavor axis that cannot be
an optional default (see R-record-shapes for the intentional splits).

Freshness: target HEAD `ee31d360`.

### FL-light-input-namespace — `make_input_namespace` (file-local)

The `(ledger, materialize_fn, clear_fn)` trio + the package's ONE
parked-globals lifecycle statement (real globals parked, ledgers
reset, `setattr` overwrite — cross-referenced, never restated, by
all six namespace riders). Riders: mutations, form, serializer, auth
(the 4th, `auth/queries.py:53`). Reconsideration trigger: a rider
needing ledger-plus-state reset (that is the heavy quartet) or a
second lifecycle statement.

Freshness: target HEAD `ee31d360`.

### FL-heavy-set-namespace — `make_set_input_namespace` (file-local)

The Decision-9 quartet: composes the light trio for ledger +
materialize, swaps in the heavy clear (both dicts + factory caches
+ `_lifecycle` binding via member 58). Riders: filter + order.
Reconsideration trigger: a third set family, or a write flavor
growing factory-cache state.

Freshness: target HEAD `ee31d360`.

### FL-shape-cache-plumbing — `make_shape_build_cache` (file-local)

The `(cache, clear_fn)` pair with the no-registration rule (each
flavor owns its dict + key type + bus registration). Riders: all
three write flavors. The walk the caches share is the spine (C7 /
F-NEW for the Layer-6 inline). Reconsideration trigger: a cache
needing registration or a non-dict store.

Freshness: target HEAD `ee31d360`.

### FL-injective-token-encoder — `pascalize_token` (file-local)

The single-leading-capital injective encoder (escapes for `_`,
capitals, leading non-lowercase, non-ASCII) so sorted concatenations
stay separable at uppercase boundaries. Riders: model + form (via
the name-set spine) + serializer (per-field token base). Distinct
from `pascal_case` by contract (R-token-encoder). Reconsideration
trigger: a token the escapes cannot encode, or a second injective
encoder.

Freshness: target HEAD `ee31d360`.

### FL-name-set-spine — `name_set_input_type_name` (file-local)

Sorted-name token concatenation + frozenset full-vs-narrowed
comparison into the skeleton. Riders: model + form wrappers (each
supplying base name + its own partial rule: `!= CREATE` vs `==
PARTIAL`, the FORM-sentinel split). Serializer identity stays out
(verified `serializer-descriptor-identity` file-local row).
Reconsideration trigger: a third name-set
flavor, or a partial rule the wrappers cannot supply.

Freshness: target HEAD `ee31d360`.

### FL-sequence-shape-gate — `normalize_field_name_sequence` (file-local)

The `None` / bare-string / set-frozenset / non-string / duplicate
ladder with the `flavor` + `label` message knobs. Riders: every
write `_validate_meta` (via the mutations/sets pair helper),
serializer class-creation + bind re-normalize, and the narrowing
spine. The set-side gate differs by contract (R-sequence-gates).
Reconsideration trigger: a sequence rule the ladder cannot express.

Freshness: target HEAD `ee31d360`.

### FL-narrowing-spine — `resolve_effective_fields` (file-local)

Normalize -> mutual-exclusion -> per-branch unknown-name raise
(single `_reject_unknown` loop) -> empty-effective raise, with the
four message knobs + caller-computed basis; order preservation rule
(`fields` order vs basis order). Riders: all three write flavors
(model passes no `empty_message` — its override-aware guard stays
downstream, owner prose at both ends). Reconsideration trigger: a
narrowing rule outside the five-step spine.

Freshness: target HEAD `ee31d360`.

### FL-drop-detection — `guard_dropped_required` (file-local)

The `sorted(required - effective - waived)` core with flavor-built
`make_error`. Riders: form create guard, form partial
column-less guard, serializer create guard (with `injected_fields`
as `waived`). The model omission is undecided (R-model-guard,
routed to the maintainer). Reconsideration trigger: a drop rule outside set
arithmetic, or the maintainer's ruling extending the population.

Freshness: target HEAD `ee31d360`.

### FL-provided-walk — `iter_provided_input_fields` (file-local)

The ONE "which fields did the client provide" walk: iterate the
bound input's strawberry fields, strip `UNSET` (omitted), keep
explicit `None` (provided). Consumer: the shared kind-dispatch
decode loop (`write_values.py::decode_provided_fields`) all three
flavors ride; per-field routing stays at call sites. Distinct from
the set-side traversal walks (R-provided-vs-set-walk).
Reconsideration trigger: a provided-ness rule outside UNSET-strip.

Freshness: target HEAD `ee31d360`; `utils/write_values.py` HEAD
`d28587c7` (call at :487 re-read at HEAD bytes).

### FL-construction-site — `build_strawberry_input_class` (file-local)

The `@strawberry.input` construction site: triple contract,
presence-of-`default` required-vs-optional rule, per-field +
per-type GraphQL name pinning (keeping Strawberry's converter out),
duplicate-attr / duplicate-wire-name backstop guards, `type(...)`
(not `make_dataclass`) construction preserving `strawberry.field`
metadata, and the optional `empty_message` seam (set factory +
model-override-aware caller stay out by documented rule). Riders:
all five `inputs` modules. Reconsideration trigger: a generated
input needing a construction rule outside the site.

Freshness: target HEAD `ee31d360`.

### FL-park-global-entry — `materialize_generated_input_class` (file-local)

The single `LazyType.resolve_type` pinning entry: `sys.modules`
global + ledger write, `(name, cls)` idempotent, distinct-class
collision via the skeleton. Sole composition point: every rider
reaches it through a namespace `materialize_fn` (6 riders; direct
callers: none outside the trio). Reconsideration trigger: a
materialization path bypassing the entry.

Freshness: target HEAD `ee31d360`.

### FL-collision-skeleton — `duplicate_name_message` (file-local)

The one "two distinct X claim one name" sentence with threaded
nouns keeping both call sites' pinned wording byte-stable
(materialize `verb="materialized"`, factory `verb="claimed"` +
factory-label head). Callers: exactly the two in-target sites.
Distinct from orphan wording (R-name-vs-orphan). Reconsideration
trigger: a third claimant, or a wording the nouns cannot pin.

Freshness: target HEAD `ee31d360`.

### FL-write-collision-walk — `iter_input_field_collisions` (file-local)

The seen-dict walk + three arms (input-attr remap collision,
GraphQL-name camel collapse, serializer-only shared-`source`
double-write) with threaded nouns + per-caller consumption (form
raises-first, serializer aggregates, model splits axes across
lifecycle points). Riders: all three write flavors. Deliberately
not unified with the other three collision points
(R-collision-quartet). Reconsideration trigger: a collision axis
outside the three arms.

Freshness: target HEAD `ee31d360`.

### FL-lazy-helper-body — `build_lazy_input_annotation` (file-local)

The Decision-11 body: `expected_base` subclass gate (`TypeError`
with family wording at the declaration site), family-ledger record
(the finalizer's orphan check reads it), canonical
`Annotated[str, strawberry.lazy(module)]` forward-ref (runtime
string, not interpolated literal, so the ForwardRef wrapping
holds). Riders: both family `__init__` helpers. Reconsideration
trigger: a lazy-ref rule outside gate + ledger + ref form.

Freshness: target HEAD `ee31d360`.

### FL-subclass-walk — `iter_set_subclasses` (file-local)

Depth-first `__subclasses__` walk, dedup by identity, live-only
contract (a collected definition has no binding state to reset —
the correct rule for a test-isolation clear). Consumers: the heavy
clear (in-target) + the `_iter_*set_subclasses` re-exports (test
oracles). Distinct from the BFS/audit graph walks
(R-graph-walks). Reconsideration trigger: a subclass enumeration
needing a different order or liveness rule.

Freshness: target HEAD `ee31d360`.

### FL-heavy-clear-body — `_safe_import` + `clear_generated_input_namespace` (file-local)

Best-effort subsystem lookups (the attr-lenient delegate: missing
module AND missing attr both `None`, so partial-load clears
whatever is reachable) + the reset body: both ledgers, the factory
caches, and every live set subclass's `_lifecycle.binding_attrs`
(delete-if-own-`__dict__` so inherited defaults restore). Bus
membership converges (A-clear-bus); the WHAT stays here.
Reconsideration trigger: a clear needing reachability failure to
raise, or binding state outside `binding_attrs`.

Freshness: target HEAD `ee31d360`.

### FL-module-mechanics — docstring + imports + re-export (file-local)

The mechanics-vs-semantics contract prose (with the parked-globals
paragraph owned here), 11 import statements all consumed
(`sys`/`dataclass`/`strawberry`/`django_models` each at their
documented sites; `Mapping` at the BFS tolerance read), the
`graphql_camel_name` explicit re-export (oracle-pinned by
`test_graphql_camel_name` through the `utils.inputs` path), and the
no-`__all__` posture (direct-name imports; the serializer ratchet
pins cross-flavor identity instead). Reconsideration trigger: an
imported-but-unused name, or a second lifecycle-statement site.

Freshness: target HEAD `ee31d360`.

### R-naming-ladder — class vs shape vs descriptor identity (rejected)

Three naming rules, three identities: `set_input_type_name`
(class-derived `FooInputType` via `type_name_for` — the name IS the
class), `name_set_input_type_name` (shape-derived
`<Base>[token](Partial)Input` — the name IS the effective field
set), serializer `serializer_input_type_name` (descriptor-derived —
the name IS the full emitted-field identity incl. annotation,
requiredness, source, description). A shared deriver would need the
descriptor's per-field digest AND the class's bare name AND the
name-set's frozenset — three populations under one signature.
Contract difference: what the name IDENTIFIES. The serializer leg
CONVERGES with the verified File `rest_framework/inputs.py`
file-local `serializer-descriptor-identity` row on fresh evidence.
Reconsideration trigger: a flavor whose name identifies two of the
three at once.

### R-token-encoder — `pascalize_token` vs `pascal_case` (rejected)

`pascalize_token` is injective BY CONTRACT (escapes preserve `_`,
capitals, leading non-letters, non-ASCII — the docstring's
`a_b`/`ab`, `field2_x`/`field2x`, `fooBar`/`foobar` triples pin
why); `utils/strings.py::pascal_case` lowercases per segment and
states its non-injectivity over case (`my_HTTP`/`my_http` share a
stem — the accepted set-family-stem domain). Both separations are
owner-recorded (`pascalize_token`: "kept visibly distinct from
`pascal_case`"; `pascal_case`: the injectivity paragraph).
Contract difference: injective token encoding vs lossy stem
derivation. Reconsideration trigger: either side changes what its
output guarantees.

### R-alias-arm — the shared `name=` alias arm (rejected)

`optional_field_kwargs` and `optional_input_field` both spell `if
python_attr != graphql_name: kwargs["name"] = graphql_name` — one
2-line arm under DIVERGENT contracts (always-optional
default-`None` vs required-vs-optional widen tail with `UNSET`).
Extracting the arm would name a 2-line helper both pinned oracles
already cover through their owners, obscuring the tails'
distinctness for zero change-obligation relief (C9-adjacent: an
alias-rule change moves both lines either way). Same-file
intentional separation. Reconsideration trigger: a third spelling,
or the arm gaining semantics (e.g. conditional aliasing).

### R-collision-quartet — four collision points stay four (rejected)

The package rejects silent-drop collisions at four points, and the
`emit_set_input_field_triples` docstring records WHY they are not
one walk: this scaffold + `iter_input_field_collisions` read
generated SPECS with consumer-actionable wording (flattened-`__`
vs `<name>_id` causes); `_audit_mutation_input_surface` reads
STRAWBERRY's resolved defs (merged-override naming is visible only
post-decoration); the construction site is the independent BACKSTOP
whose value is precisely body-independence ("one walk would mean
one bug disabling all of them"). `_audit_field_surface` adds the
type-surface leg (column-vs-column, pre-decoration). Contract
difference: input population + failure-independence per point.
Reconsideration trigger: two points reading one population with one
wording.

### R-graph-walks — three graph walks stay three (rejected)

`iter_set_subclasses` (DFS over the live subclass TREE for clear),
`_ensure_built` (BFS over the related-set GRAPH with collision
detection + build for materialization), finalizer
`_audit_unregistered_related_filter_targets` (transitive walk with
registration checks for audit). Same mechanism SHAPE (seen-set +
worklist), three responsibilities: a shared driver would take the
graph source + visit action + order + failure mode as parameters —
a mode flag adding branches no single path reaches (principle 5).
Contract difference: what is walked and what a visit DOES.
Reconsideration trigger: two walks over one graph with one visit
contract.

### R-record-shapes — provenance vs reverse-map vs identity (rejected)

`GeneratedInputFieldSpec` (set-side provenance: 3 names for the
normalizers), `InputFieldSpec` (write-side reverse-map: decode key
+ kind + relation/nested axes for the decoders),
`MutationInputShape` / `SerializerInputShape` (shape identity: the
name + cache-key derivation bundle). Disjoint populations, disjoint
readers; the model `_GeneratedInputFieldName` is an ADAPTER into
the shared collision walk (composition, not a fourth record).
Contract difference: what each record PROVES (provenance vs
decodability vs identity). Reconsideration trigger: one reader
needing two records' axes from one object.

### R-depth-caps — metadata depth vs traversal depth (rejected)

`_MAX_META_VALUE_DEPTH` (64: FIXED bound on a CONSTRUCTION-TIME
metadata-container walk for cache keys) vs the set-input traversal
cap (`_MAX_LOGIC_DEPTH`: CLASS-OVERRIDABLE bound on a REQUEST-TIME
input walk). Different walks, different lifetimes, different
variation rules — distinguished from the open
`traversal-depth-cap-check` family (no adoption: not a member).
Contract difference: what depth is BOUNDED and who may move the
bound. Reconsideration trigger: one walk needing both bounds, or
the metadata bound becoming overridable.

### R-sequence-gates — write vs set stances on sets (rejected)

`normalize_field_name_sequence` REJECTS set/frozenset (declared
order folds into generated type names + SDL order — hash
randomization would fork both); `sets_mixins.py::
require_re_readable_field_declaration` ACCEPTS sets (the set side
canonicalizes unordered shapes via `canonicalize_set_meta_fields`
/ `read_set_meta_fields`). Opposite stances, each with its stated
reason. Contract difference: order-IS-identity vs
order-gets-canonicalized. Reconsideration trigger: one side
adopting the other's stance.

### R-meta-duality — dict-or-class vs class-only Meta reads (rejected)

`_set_meta_has` / `_set_meta_get` read BOTH kwargs dicts (Layer-6
factory input) and Meta classes (declaration input) because the
synonym rule + normalize + cache key all flow both shapes. The
class-only readers (`types/base.py::_meta_attr`,
`rest_framework/inputs.py::_serializer_meta_value`) never see a
kwargs dict. Contract difference: which SHAPES flow through the
rule. Reconsideration trigger: a class-only reader gaining a dict
input, or the duality collapsing to one shape.

### R-name-vs-orphan — collision sentence vs orphan message (rejected)

`duplicate_name_message` (TWO CLASSES claim ONE name; remedy:
rename one class) vs finalizer `_format_orphan_sets_error` (ONE
helper referenced a set WIRED NOWHERE; remedy: wire it or drop the
reference). Different subjects, different remedies, different call
timing (materialize vs pre-materialize subpass 4).
Reconsideration trigger: one wording covering both misconfigurations.

### R-model-gate — Django-model gate vs definition validation (rejected)

`create_dynamic_set_class`'s gate validates a DJANGO MODEL CLASS
(`isinstance type` + `issubclass Model` — the `type(...)` skeleton
needs a model for `Meta.model` + the name stem) vs the open
`registered-djangotype-definition-validation` family (a REGISTERED
Djangotype DEFINITION — finalization state, not class shape).
Distinguished, not adopted: different subjects. Reconsideration
trigger: dynamic-set creation requiring registration state.

### R-provided-vs-set-walk — UNSET-strip vs set traversal (rejected)

`iter_provided_input_fields` walks a STRAWBERRY INPUT DATACLASS
(`__strawberry_definition__` fields + UNSET-strip) for the write
decoders; `utils/input_values.py` walks SET-INPUT VALUES (dataclass
/ dict / list shapes with depth + error context) for the set
normalizers. Different populations, different error contracts
(silent skip of unknown attrs vs typed walk errors).
Reconsideration trigger: one walk covering both populations with
one error contract.

### R-guards — shared-guard directions (rejected)

The six translating arms (`:480` hostile sort input, `:752`
unreadable meta entries, `:1102` unreadable sequence, `:1292`
unreadable specs, `:1312` malformed triple, `:1320` unmappable
kwargs) each translate a per-site failure into a per-subject
`ConfigurationError`; distinguished, not counted: `:537` is an
opaque-fallback (no raise — unhashables land as identity tokens),
`:1586` is an attr-leniency (`AttributeError` -> `None` for the
partial-load lifecycle), `:516` is a `try/finally` with no `except`
(active-path guard release). The exact-type reads (`type(name) is
not str`, per-shape dispatches) are per-site gates. CONVERGE with
the standing J1 (shared `except` guard) and J2 (shared exact-type
gate) directions on fresh evidence: no shared guard is owed.
Reconsideration trigger: a detail-less guard or a new exact-type
gate (the standing triggers).

### R-wordings — per-subject refusal wordings (rejected)

Every refusal wording in the target names its own subject and
remedy (metadata mapping, sequence shape, unknown field, dropped
required, collision pair, orphan-adjacent factory wording). CONVERGE
with verified File `utils/policies.py` R3
(per-subject-rejection-grammars) on fresh evidence: the package has
no owned rejection-message grammar, and none is owed.
Reconsideration trigger: the package adopts one.

### R-opaque-key — opaque token vs sort key (rejected)

`_opaque_meta_value` (fixed-marker NON-ALIASING token) vs
`canonical_sort_key` (content-headed TOTAL ORDER) share only the
identity-pair tail. CONVERGE with verified File `utils/canonical.py`
R1 on fresh evidence (contract difference recorded at the owner).
Reconsideration trigger: either site changes what its head
guarantees.

### R-model-guard — create-required guard on the model flavor (rejected; ROUTED TO MAINTAINER)

Form (create + partial column-less guards) and serializer (create
guard with `injected_fields` waived) enforce bind-time rejection of
a create narrowing that drops a still-required field; the model
flavor has no equivalent — and no contract source was found EITHER
establishing that the rule applies to model narrowings (spec-036 /
spec-039 / glossary / owner prose: zero rows) OR blessing its
absence (the `empty_message` override-aware rationale covers
EMPTINESS only, not required-ness; a merged `input_class` MAY
re-supply a dropped column, but that inference is mine, not a
stated contract). Per the axis-6 rule this is ambiguous, not a
defect: routed to the maintainer. Reconsideration trigger: a spec row requiring
model bind-time required-guarding (then a behavior defect + family
extension), a spec row blessing per-request `full_clean` failure
for dropped required columns (then a standing rejection), or the maintainer's
ruling.

## Defects

D1 — `utils/inputs.py` prose claims bare-`repr` sorting where the
bodies use `canonical_sort_key` (doc-only; owner: THIS file item;
homed here, NOT fixed — a file item makes no edits). Routed from
verified File `utils/canonical.py`; each limb judged fresh at HEAD
bytes (`ee31d360`), all four CONFIRMED live, and all four lines are
untouched diff context in the worktree (the truth-migration hunks
add adjacent sentences only):

- (a) `make_hashable_meta_value` docstring (:550-556): "Both unordered
  branches sort by ``repr`` ... so they stay total-ordered." The
  bodies sort by `canonical_sort_key` (:525 dict pairs, :531 set
  values), and bare `repr` is precisely what CANNOT promise totality
  — the identity tail exists for that. A reader acting on this prose
  would reintroduce the fail-open the canonical module exists to
  close. CONFIRMED.
- (b) `make_set_meta_cache_key` docstring (:681-682): "Dict-shaped
  ``fields`` keys sort via ``key=repr``." The body recurses into
  `make_hashable_meta_value`, which sorts (key, value) PAIRS by the
  canonical key — wrong noun twice over (pairs, not keys; canonical
  key, not `repr`). CONFIRMED.
- (c) `canonicalize_set_meta_fields` docstring (:622): "``repr``-sorted
  lists" for `_sorted_meta_values` (canonical key). CONFIRMED.
- (d) `normalize_set_meta_for_factory` docstring (:736 fields limb +
  :741 exclude limb): "``repr``-sorted lists" / "the same
  ``repr``-sorted list" for `canonicalize_set_meta_fields` /
  `_sorted_meta_values` (canonical key both). CONFIRMED (two
  sentences, one limb).
- Contrast (correct prose, same threat model, re-verified):
  `write_transaction.py::_field_fingerprint` docstring + comment
  ("ordered by the guarded key, never a bare ``repr``") and
  `_sorted_meta_values`' own docstring (names the canonical reads).

Freshness: `utils/inputs.py` HEAD `ee31d360` (all four limbs re-read
at these lines; worktree `b5af8255` NOT traced but the limbs are
diff context, byte-identical).

D2 — `orders/sets.py:460` prose claims the same bare-`repr` sorting
(doc-only; owner: verified File `orders/sets.py`; for Worker-0
closeout homing — that item is ticked, so no re-route target is
open). `_expand_meta_fields` docstring: "Unordered ``set`` /
``frozenset`` declarations expand in the same ``repr``-sorted order
Layer-6 factory kwargs hash (``read_set_meta_fields``)". The body
(:486) reads via `read_set_meta_fields` ->
`canonicalize_set_meta_fields` -> `_sorted_meta_values` ->
`canonical_sort_key`. Same defect shape as D1, fifth limb, outside
this target. Found by the package-wide `repr.*sort|sort.*repr`
census (all other hits are the D1 limbs, the correct canonical
prose, the already-rejected diagnostic/framework sorts, or
sorted-rendered-string diagnostics that sort output, not values).

Freshness: `orders/sets.py` HEAD `6044ab1a` (limb re-read at :460).

## Pending execution

None. All conclusions are static against HEAD bytes; no probe, no
pytest, no scratch scope, no workspace runs. Sharded and Postgres
cells are inapplicable by construction: the target is
construction-time class building plus pure in-memory computation
(name derivation, namespace reset, container walks) reaching no
database, alias, or dialect decision — the `django_models` import
serves one `issubclass` gate, and every consumer calls from
finalize / bind / clear paths over in-memory declarations.

## Judgment

Zero-edit file item: 60/60 members homed (5 open-family converges +
2 verified-family converges re-verified on fresh evidence, 1 new
family `shape-build-get-or-store` for Worker 0, 25 file-local rows,
16 rejections incl. 1 routed-to-the maintainer). The target single-owns the
generated-input mechanics both set families and all three write
flavors compose by name; the genuine second spellings found (the
Layer-6 miss path, the provisional-name restatement, the base-slot
inlines, the triple-spelled membership) all route to families, none
consolidated here. The routed D1 is homed in this file on fresh
evidence (4/4 limbs confirmed live); one same-shape limb in verified
`orders/sets.py` is filed as D2 for closeout homing. No pending
execution, no production edit, no test edit. All 28 worktree hunks
are concurrent-external truth-migration dirt predating the item
baseline; HEAD (`0c0537e2`) did not move during this item.

## Index rows for Worker 0

(Worker 0 alone edits the plan; rows named here for transcription.
Converges transcribe nothing and are not rows.)

- Family `shape-build-get-or-store` | Owner candidate
  `django_strawberry_framework/utils/inputs.py::get_or_store_shape_build`
  | Files `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/filters/inputs.py` | Holding item
  Family `shape-build-get-or-store` | open (spine :920-943 + Layer-6
  inline miss path :873-886 + Range inline
  `filters/inputs.py:743-752`; population 3, closed by the
  package-wide `cache.get(`/`cache[` census with recorded
  exclusions: BFS graph-ensure, materialize raise, connection
  provenance check, lookups copy-out, optimizer LRU/eviction,
  definition key-absence memos)
- `set-provenance-record` |
  `django_strawberry_framework/utils/inputs.py::GeneratedInputFieldSpec`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `set-name-delegate` |
  `django_strawberry_framework/utils/inputs.py::set_input_type_name` |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `set-optional-tail` |
  `django_strawberry_framework/utils/inputs.py::optional_field_kwargs`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `write-widen-tail` |
  `django_strawberry_framework/utils/inputs.py::optional_input_field`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `set-triple-emit-scaffold` |
  `django_strawberry_framework/utils/inputs.py::emit_set_input_field_triples`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `decode-kind-vocabulary` |
  `django_strawberry_framework/utils/inputs.py::SCALAR` (+
  `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`) |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `conversion-value-shape` |
  `django_strawberry_framework/utils/inputs.py::FieldConversionBase` |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `write-reverse-map-record` |
  `django_strawberry_framework/utils/inputs.py::InputFieldSpec` |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `light-input-namespace` |
  `django_strawberry_framework/utils/inputs.py::make_input_namespace`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `heavy-set-namespace` |
  `django_strawberry_framework/utils/inputs.py::make_set_input_namespace`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `shape-cache-plumbing` |
  `django_strawberry_framework/utils/inputs.py::make_shape_build_cache`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `injective-token-encoder` |
  `django_strawberry_framework/utils/inputs.py::pascalize_token` |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `name-set-spine` |
  `django_strawberry_framework/utils/inputs.py::name_set_input_type_name`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `sequence-shape-gate` |
  `django_strawberry_framework/utils/inputs.py::normalize_field_name_sequence`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `narrowing-spine` |
  `django_strawberry_framework/utils/inputs.py::resolve_effective_fields`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `drop-detection` |
  `django_strawberry_framework/utils/inputs.py::guard_dropped_required`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `provided-walk` |
  `django_strawberry_framework/utils/inputs.py::iter_provided_input_fields`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `construction-site` |
  `django_strawberry_framework/utils/inputs.py::build_strawberry_input_class`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `park-global-entry` |
  `django_strawberry_framework/utils/inputs.py::materialize_generated_input_class`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `collision-skeleton` |
  `django_strawberry_framework/utils/inputs.py::duplicate_name_message`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `write-collision-walk` |
  `django_strawberry_framework/utils/inputs.py::iter_input_field_collisions`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `lazy-helper-body` |
  `django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`
  | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `subclass-walk` |
  `django_strawberry_framework/utils/inputs.py::iter_set_subclasses` |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `heavy-clear-body` |
  `django_strawberry_framework/utils/inputs.py::clear_generated_input_namespace`
  (+ `_safe_import`) | `django_strawberry_framework/utils/inputs.py` |
  File `utils/inputs.py` | file-local
- `module-mechanics` | `django_strawberry_framework/utils/inputs.py`
  (docstring, imports, `graphql_camel_name` re-export, no-`__all__`
  posture) | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | file-local
- `naming-ladder-split` |
  `django_strawberry_framework/utils/inputs.py::set_input_type_name`
  (rejection recorded here; serializer leg CONVERGES with the
  verified File `rest_framework/inputs.py` file-local
  `serializer-descriptor-identity` row on fresh evidence) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/rest_framework/inputs.py` | File
  `utils/inputs.py` | rejected
- `token-encoder-vs-pascal-case` |
  `django_strawberry_framework/utils/inputs.py::pascalize_token`
  (rejection recorded here; owner-recorded separation both sides) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/strings.py` | File
  `utils/inputs.py` | rejected
- `alias-arm-split` |
  `django_strawberry_framework/utils/inputs.py::optional_field_kwargs`
  (rejection recorded here; same-file intentional separation) |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | rejected
- `collision-quartet-split` |
  `django_strawberry_framework/utils/inputs.py::emit_set_input_field_triples`
  (rejection recorded here; owner-recorded separation in-target) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/mutations/inputs.py`,
  `django_strawberry_framework/types/finalizer.py` | File
  `utils/inputs.py` | rejected
- `graph-walk-split` |
  `django_strawberry_framework/utils/inputs.py::iter_set_subclasses`
  (rejection recorded here; fresh triple, no prior verdict) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/types/finalizer.py` | File
  `utils/inputs.py` | rejected
- `record-shape-split` |
  `django_strawberry_framework/utils/inputs.py::GeneratedInputFieldSpec`
  (rejection recorded here; fresh triple, no prior verdict) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/mutations/inputs.py`,
  `django_strawberry_framework/rest_framework/inputs.py` | File
  `utils/inputs.py` | rejected
- `depth-cap-split` |
  `django_strawberry_framework/utils/inputs.py::_MAX_META_VALUE_DEPTH`
  (rejection recorded here; distinguished from open
  `traversal-depth-cap-check`, not a member) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/input_values.py` | File
  `utils/inputs.py` | rejected
- `sequence-gate-split` |
  `django_strawberry_framework/utils/inputs.py::normalize_field_name_sequence`
  (rejection recorded here; opposite stances, each owner-stated) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/sets_mixins.py` | File
  `utils/inputs.py` | rejected
- `meta-duality-split` |
  `django_strawberry_framework/utils/inputs.py::_set_meta_has`
  (rejection recorded here; fresh pair, no prior verdict) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/types/base.py`,
  `django_strawberry_framework/rest_framework/inputs.py` | File
  `utils/inputs.py` | rejected
- `name-vs-orphan-wording` |
  `django_strawberry_framework/utils/inputs.py::duplicate_name_message`
  (rejection recorded here; fresh pair, no prior verdict) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/types/finalizer.py` | File
  `utils/inputs.py` | rejected
- `model-gate-vs-definition-validation` |
  `django_strawberry_framework/utils/inputs.py::create_dynamic_set_class`
  (rejection recorded here; distinguished from open
  `registered-djangotype-definition-validation`, not a member) |
  `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | rejected
- `provided-vs-set-walk` |
  `django_strawberry_framework/utils/inputs.py::iter_provided_input_fields`
  (rejection recorded here; fresh pair, no prior verdict) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/input_values.py` | File
  `utils/inputs.py` | rejected
- `shared-guard-directions` |
  `django_strawberry_framework/utils/inputs.py` (rejection recorded
  here; CONVERGE with the standing J1 + J2 directions on fresh
  evidence) | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | rejected
- `per-subject-wordings` |
  `django_strawberry_framework/utils/inputs.py` (rejection recorded
  here; CONVERGE with verified File `utils/policies.py` R3 on fresh
  evidence) | `django_strawberry_framework/utils/inputs.py` | File
  `utils/inputs.py` | rejected
- `opaque-vs-sort-key` |
  `django_strawberry_framework/utils/inputs.py::_opaque_meta_value`
  (rejection recorded here; CONVERGE with verified File
  `utils/canonical.py` R1 on fresh evidence) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/canonical.py` | File
  `utils/inputs.py` | rejected
- `model-guard-applicability` |
  `django_strawberry_framework/utils/inputs.py::guard_dropped_required`
  (asymmetry recorded here; ROUTED TO MAINTAINER — no contract source;
  trigger: a spec row requiring model bind-time required-guarding, a
  spec row blessing per-request `full_clean` failure, or the maintainer's ruling)
  | `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/mutations/inputs.py` | File
  `utils/inputs.py` | rejected

## Independent verification (Worker-2)

Recorded BEFORE reading `## Findings` (expectation-first). All
evidence below is mine, against HEAD bytes (`0c0537e2`;
`utils/inputs.py` blob `ee31d360`, 1823 lines) unless noted.

### Own trace

Instrument: `ast.Module.body` over `git show HEAD:` bytes. My count:
60 nodes (docstring + 12 imports + 4 AnnAssign kind constants + 2
module Assigns + 4 ClassDefs + 37 FunctionDefs). Any complete homing
must land all 60.

Rules I posit, with roles, definition counts, and the owner I would
choose (C = consumer, O = oracle, P = projection; counts are
authoritative definitions only):

- T1 BFS substrate (`GeneratedInputArgumentsFactory` + member-14
  `set_input_type_name` delegate). Definitions: 1 (the base; both
  family factories subclass DIRECTLY at HEAD —
  `filters/factories.py:74` blob `ad5634c4`,
  `orders/factories.py:56` blob `b9fd62bc` — declarations, not
  definitions). C: both family factories, both family inputs
  modules, `types/finalizer.py`. Owner: the base. Posited changes
  (9th hook attr, FIFO->LIFO, new registry shape): count stays 1.
  Expect: converge open `set-arguments-factory-bfs`.
- T2 Layer-6 dynamic-set surface (members 26-41: opaque/sorted/
  hashable/cache-key/alias/resolve/canonicalize/promote/read/
  normalize/skeleton/getter). Definitions: 1 per helper; 0 in the
  families (both `_get_*` are one-line `make_dynamic_set_getter`
  calls; both metaclasses call `promote_set_meta_fields`; orders
  expansion reads `read_set_meta_fields`). Owner: the helpers.
  Expect: converge open `dynamic-set-class-getter`.
- T3 Provisional skeleton name (member 45
  `generated_input_type_name`). Definitions: 2 — the owner plus the
  inline suffix restatement at HEAD
  `rest_framework/resolvers.py:1211` (`'PartialInput' if operation
  == 'update' else 'Input'`, blob `0d302782`). C: member-46 spine,
  `serializer_input_type_name`, 3 provisional call sites. Owner: the
  skeleton. Expect: converge open
  `canonical-input-provisional-name` as family evidence.
- T4 Base-slot container reads. The target holds 0 definitions: 5
  call sites (`:481`, `:529`, `:533`, `:695`, `:702`) compose
  `canonical.py::base_container_values` by name. Expect: converge
  open `base-slot-container-reads`.
- T5 Container membership. `(set, frozenset)` spelled at target
  `:526`, `:627`, `:631`, `:697`, `:1094`, plus `canonical.py`
  (`:65` branch) and `write_transaction.py` (`:772`, `:958`,
  `:996`) — 3 modules, family evidence for the item to decide.
  Expect: converge open `canonical-container-membership`.
- T6 Namespace clear closures. Set heavy clears + write light
  clears + auth ledger all `register_subsystem_clear` at their own
  modules (filters `:1069`, forms `:169`, auth `:60` verified at
  HEAD). Expect: converge verified `subsystem-clear-lifecycle`.
- T7 `_safe_import`. Attr-lenient wrapper over verified
  `utils/imports.py::import_attr_if_importable` (plan row is a
  verified FILE-LOCAL row, FL1 — not a family item; label
  accordingly). Count 1 here as distinguished consumer. Expect:
  converge that verified verdict.
- T8 Shape-build get-or-store. Definitions: 2 — the spine
  (member 43, `:938-942`) and the getter inline miss path
  (`:874-876` + `:885`). Spine composed by name at 3 write
  flavors (`mutations/sets.py:242` via `cached_build_input` +
  `:1433` direct; form via `cached_build_input`;
  `rest_framework/inputs.py:1443`). Distinguished, not counted:
  BFS `:1769` check-then-build (collision gate interleaved,
  store in another method) and materialize `:1395-1411`
  idempotency-plus-raise (raises instead of building — different
  contract). Population closed at 2 on this rule statement.
  Owner: the spine (narrowest cohesive owner; the getter already
  imports downward). Expect: NEW family, endorsable if the record
  carries this closure reasoning.
- T9-T33 Single-owner mechanics (file-local each): provenance
  record (13), name delegate (14), set optional tail (15), write
  widen tail (16), triple scaffold (17), kind vocabulary (18-21),
  conversion shape (22), reverse-map record (23), light/heavy
  namespaces (24/25, heavy composes light), shape plumbing (42),
  token encoder (44), name-set spine (46), sequence gate (47),
  narrowing spine (48), drop guard (49), provided walk (50),
  construction site (51), park entry (52), collision skeleton
  (53), collision walk (54), lazy helper (55), subclass walk (56),
  heavy clear (57/58), module mechanics (0-12, no `__all__`).
  Count 1 each; families consume by name.
- Rejections I expect with contract differences: set-tail vs
  write-tail (`None` vs `UNSET` — different omission contracts);
  the collision quartet (scaffold / walk / mutation audit /
  backstop — different reads, deliberate non-sharing); three
  graph walks (BFS vs subclass-liveness vs hash-walk); three
  record shapes (provenance vs reverse-map vs identity);
  metadata depth vs traversal depth; write reject-sets vs set
  canonicalize-sets; dict-or-class vs class-only Meta reads;
  collision sentence vs orphan message; Django-model gate vs
  definition validation; UNSET-strip vs set traversal; shared
  `except`/exact-type guards (standing J1/J2); per-subject
  wordings (standing R3); opaque token vs sort key (canonical
  R1); model-guard omission — ROUTED TO MAINTAINER (form x2 at
  `forms/inputs.py:786,:830` + serializer at
  `rest_framework/inputs.py:1168` enforce; model omits;
  spec-038's dropped-required contract is form-scoped
  (`:1303-1315`), spec-039 form+serializer scoped; no source
  either way for the model flavor — ambiguous, so axis 6 routes
  rather than defects).

Matrix expectations: axis 2 no-surface (my HEAD grep for `async `
  / `await ` / `sync_to_async` / `asyncio`: 0 hits); axis 6
  model-guard routes to the maintainer; `read_set_meta_fields` filter-side
  non-read must be shown structural, not a gap.

Hunk prior: 28 hunks HEAD-vs-worktree; `git diff 722a927b --
<path>` empty, so all dirt predates the item baseline; content
scan must show truth-migration vocabulary only, and the plan
`## Owned changes` (`:1171-1236`) names no row for this file
(confirmed: zero matches).

D1 prior: all four limbs live at HEAD bytes — (a) `:550-556`
  "Both unordered branches sort by ``repr``" vs `canonical_sort_key`
  bodies `:525`/`:531`; (b) `:681-682` "`key=repr`" vs pair-sorting
  recurse; (c) `:627-628` "`repr`-sorted lists"; (d) `:734-736`
  "`repr`-sorted lists" — each contradicted by the composed
  canonical key. Homing here (no file-item edits) is correct.
D2 prior: `orders/sets.py:460-461` "`repr`-sorted order ... they
  hash (`read_set_meta_fields`)" live at HEAD blob `6044ab1a`
  (matches verified File `orders/sets.py`); same-shape limb filed
  for closeout homing against that verified file matches the run
  pattern.

Census flag (pre-Findings): my AST-precise HEAD importer census
counts 22 real production importers, not 19 — including
`mutations/resolvers.py` (kind constants `FILE` /
`RELATION_MULTI` / `RELATION_SINGLE`), which the System-trace
list I have read does not name. Consumers, not definitions: no
homing impact expected, but the census figure needs correction or
reconciliation.

### Reconciliation

Read `## Findings`, `## Defects`, `## Pending execution`,
`## Judgment`, `## Index rows` after recording the trace above.
Per-judgment results (V = verified, R = revision item):

1. Enumeration completeness: V. My independent AST count is 60/60
   over HEAD bytes and every member is homed; the dual-homes
   (41/F-NEW, 29/35/baseslot/membership, 57/58, 8/9/10) are
   documented, not double-counted. 25 file-local rows recounted.
2. Hunk attribution: V. 28/28 hunks are truth-migration
   vocabulary by content in BOTH directions (added lines:
   `truth.*` x42, `_is_one_of`/`_META_*` scaffolding,
   `BaseException` narrowing, `id` dedup, `# truth: ok` markers,
   reflows, real-class docstrings; removed lines: only their
   counterparts). `git diff 722a927b -- <path>` is empty and no
   `## Owned changes` row names this file, so all dirt predates
   the item baseline. HEAD bytes were the correct trace basis.
3. Convergences: V, all seven, re-verified on fresh evidence.
   Open: BFS (direct subclassing + blobs re-read), dynamic
   getter (both one-line constructions + zero-production-caller
   census confirmed — callers only in `tests/`), provisional
   name (`:1213` restatement re-read at blob `0d302782`; W1's
   line number is correct — my prior `:1211` was off by two),
   base-slot (2 eager inlines + 5 consumer calls + `safe_meta`
   exclusions, consistent with canonical FA), membership (gate
   vs dispatch distinction, consistent with canonical FB).
   Verified: clear-bus (registrations re-read), imports (body
   correctly cites the FL1 file-local row; the heading
   shorthand is harmless).
4. F-NEW `shape-build-get-or-store`: SUBSTANCE ENDORSED,
   POPULATION REJECTED — R1 (material). The spine + Layer-6
   inline genuinely share one rule (my T8 agrees). But
   "population closed at 2" is false: HEAD
   `filters/inputs.py:743-752` (Range sub-input cache:
   `cache.get` -> None-check -> `build_input_class` -> store ->
   return) is a THIRD member under the stated contract —
   per-shape generated-input build, unbounded, no provenance
   check, no copy-out, structurally identical to the Layer-6
   inline. The record's census ("`cache.get(` over the six
   cache-owning modules") silently scopes that file out without
   naming it, and the only recorded exclusion (BFS `:1769`)
   is not even a `cache.get(` site. Unrecorded
   `cache.get(`-shaped sites needing exclusion reasoning:
   `connection.py:1506` (provenance-check-on-hit — different
   contract), `filters/sets.py:172` (pure-derivation memo +
   copy-out), `optimizer/extension.py:610` + `:1333` (bounded
   LRU + eviction), `types/definition.py` subscript memos.
   The index row transcribes "closed at 2" — the falsehood
   would propagate into the plan. Resubmission must re-close
   the population (add the Range member or state a contract
   difference — none is visible), record the exclusions with
   contract differences, and fix the index row.
5. Rejections: all 16 probed independently; SUBSTANCE STANDS on
   all 16, with two record nicks bundled as R3/R4. Verified
   fresh: descriptor digest (R-naming-ladder),
   `pascal_case` non-injectivity prose (R-token-encoder), the
   2-line arm under divergent tails (R-alias-arm), strawberry-
   resolved-defs audit + transitive registration walk
   (R-collision-quartet, R-graph-walks), the three record
   shapes + adapter (R-record-shapes), class-overridable
   request-time cap vs fixed construction-time bound
   (R-depth-caps; open family row exists), Collection-contract
   set acceptance (R-sequence-gates), class-only reader
   signatures (R-meta-duality), orphan formatter
   (R-name-vs-orphan), open definition-validation family
   (R-model-gate), typed walk errors (R-provided-vs-set-walk),
   canonical R1 row (R-opaque-key), policies R3 direction
   (R-wordings). R-model-guard routing to the maintainer CONFIRMED: form
   x2 (`:786`, `:830`) + serializer (`:1168`) enforce, model
   omits, and my independent spec search finds the
   dropped-required contract only form-scoped (spec-038
   `:1303-1315`) and form+serializer-scoped (spec-039) — no
   source either way for the model flavor, so axis 6 routes
   rather than defects. Nicks: R-guards counts "five"
   translating arms but HEAD holds SIX (`:480`, `:752`,
   `:1102`, `:1292`, `:1312`, `:1320` — the `:1102`
   sequence-tuple arm is unlisted; plus the `:537` fallback
   and `:1586` leniency, neither a translation) — R3; the
   "verified FAM-NEW split" tag (R-naming-ladder + Matrix
   axis 3) mislabels the referent — the actual FAM-SRC new
   family is the source-axis one, while the split verdict is
   the verified file-local `serializer-descriptor-identity`
   row — R4. Neither nick moves any homing.
6. D1 homed here: V, 4/4 limbs confirmed live at HEAD bytes on
   my independent read (`:550-556`, `:681-682`, `:622`,
   `:736` + `:741`), each contradicted by the composed
   canonical key; all four lines verified as byte-identical
   diff context (or outside every hunk) in the worktree. No
   file-item edit owed; homing correct.
7. D2 filing: V. The `:460` limb is live at HEAD blob
   `6044ab1a` (matches verified File `orders/sets.py`), the
   body reads via `read_set_meta_fields` at `:486` exactly as
   cited, and my independent `repr.*sort|sort.*repr` census
   finds no further same-shape limb (remaining hits are the
   D1 limbs, correct canonical prose, rendered-string sorts,
   and framework/diagnostic sorts). Closeout-homing filing
   against the ticked file matches the run pattern.

Record nick R2 (System trace): "19 files" importer census —
my AST-precise HEAD census counts 22 real production
importers; the in-text list names 21 and omits
`mutations/resolvers.py` (kind constants `FILE` /
`RELATION_MULTI` / `RELATION_SINGLE`). No homing impact
(the FL-decode-kind-vocabulary finding already counts "3
flavor resolvers"), but the figure + list need correction.

AGENTS.md prose + lint gate: no process provenance, symbol
citations, no test tier owed (zero-edit file item);
`ruff format --check` + `ruff check` on the artifact pass
(md no-op). Pending execution: none claimed, none owed —
all conclusions are static against HEAD bytes and the
sharded/PG inapplicability reasoning (construction-time +
pure in-memory; `django_models` serves one `issubclass`
gate) is sound. HEAD `0c0537e2` unmoved throughout.

### Verdict: revision-needed (SAME W1 context)

The durable record is one material fix + three record nicks
from verified. Resubmission instructions (all reproducible
against HEAD bytes; no production edits; no plan edits):

- R1 (material): re-close F-NEW. Address HEAD
  `filters/inputs.py:743-752` (Range sub-input get-or-store)
  as a third member or state its contract difference;
  record exclusions with contract differences for
  `connection.py:1506`, `filters/sets.py:172`,
  `optimizer/extension.py:610` + `:1333`, and the
  `types/definition.py` subscript memos (or restate the
  rule so each falls out explicitly); correct the
  population count and the index row. Re-verify: `git grep
  -n 'cache\.get(\|cache\[' HEAD --
  django_strawberry_framework/`.
- R2: fix the importer census to 22 and name
  `mutations/resolvers.py` in the System-trace list.
  Re-verify: AST `ImportFrom` census for `utils.inputs`
  over `git show HEAD:` bytes.
- R3: fix R-guards to six translating arms (add the
  `:1102` sequence-tuple arm) and distinguish the `:537`
  opaque-fallback and `:1586` attr-leniency arms.
  Re-verify: `grep -n 'try:'` over HEAD bytes.
- R4: fix the "FAM-NEW" tag to the verified File
  `rest_framework/inputs.py` file-local
  `serializer-descriptor-identity` row (both uses).

Resubmission returns to THIS Worker-2 context (fresh only
if gone).

## Iterations

### Re-pass (Worker-2, same context) — `ready-for-verification/2` → `verified`

All four revision items reproduce against HEAD bytes; substance
otherwise untouched (my pass-1 section intact; D1/D2, Judgment,
enumeration, and all FL/R findings match the pass-1 reads).

- R1: Range member `filters/inputs.py::_build_range_input_class`
  (`:743-752`; def at `:704`) added with correct oracle pins
  (`tests/filters/test_inputs.py:1168/:1180`, line-exact). The
  restated rule (unbounded + None miss signal + returns THE
  stored object + no hit-validation/copy-out/eviction)
  excludes each recorded site on its stated difference, every
  one re-read at HEAD by me: BFS graph-ensure, materialize
  raise, connection provenance-check (`:1506-1516`), lookups
  copy-out (`return list(cached)`), optimizer LRU/eviction
  (doc-key `:610-622` + plan cacheability gate +
  per-execution tier `:1333-1375`), definition
  `in`-then-`[]` None-caching memos (gated on
  `registry.is_finalized()`). Census arithmetic closes
  exactly over my re-run sweep (21 hits = 6 member + 12
  exclusion + 3 comment non-sites). Index row fixed (3
  members, both files, exclusions named). All five
  freshness blobs match HEAD (`82b52d97`, `4894f90f`,
  `993e887a`, `e0e53a8e`, `fa6c4d33`). C7 counts 3;
  Matrix axis 3 updated. Family ENDORSED as re-closed.
- R2: census reads 22 with AST methodology; the list names
  all 22 including `mutations/resolvers.py` (blob `043a2d0b`
  matches HEAD; the three kind constants match my AST
  census exactly).
- R3: six translating arms with exact lines (`:480`, `:752`,
  `:1102`, `:1292`, `:1312`, `:1320`) plus `:537`/`:1586`
  distinguished and the `:516` finally noted — complete
  against the HEAD `try:` census (9 sites).
- R4: no `FAM-NEW` remains in W1's portion; every use cites
  the verified file-local `serializer-descriptor-identity`
  row. Tag-only; converge substance unchanged.

`ruff format --check` + `ruff check` on the artifact pass
(md no-op). No pending execution. HEAD `0c0537e2` unmoved;
target diff vs `ITEM_BASELINE` still empty. No production
edits; no plan edits.

## Iterations

### Resubmission pass 2 (Worker-1, same context)

Applied Worker-2's R1–R4 (record only); every item re-derived at
HEAD bytes before applying, substance unchanged (60/60, 28/28
attribution, 7 convergences, 16 rejections substance, D1 4/4, D2,
F-NEW substance all stand):

- R1 (material): F-NEW re-closed at 3. `filters/inputs.py:743-752`
  (Range sub-input get-or-store) judged independently — no
  contract difference visible (unbounded, None miss signal,
  stored-object return, no validation/copy/eviction) — added as
  the third member with its oracles
  (`tests/filters/test_inputs.py:1168/:1180`); rule restated so
  each exclusion falls out explicitly; recorded exclusions with
  contract differences: BFS graph-ensure + materialize raise
  (off-census), connection `:1506` provenance-check-on-hit,
  `filters/sets.py:172` copy-out, `optimizer/extension.py:610` +
  `:1333` bounded LRU + eviction, `types/definition.py`
  subscript memos (key-absence miss signal + cached Nones);
  census instrument corrected to the package-wide
  `cache.get(`/`cache[` grep (21 hits, accounted); C7 now
  counts 3; F-NEW index row rewritten (population 3, both
  files, exclusions named).
- R2: importer census 19 → **22** (full-AST `ImportFrom`
  census over every package `.py` at HEAD bytes; the pass-1
  "19" miscounted my own 21-name list and missed
  `mutations/resolvers.py`, now named with blob `043a2d0b`
  in the System-trace write-flavor list).
- R3: R-guards five → **six** translating arms (`:480`,
  `:752`, `:1102`, `:1292`, `:1312`, `:1320` — the `:1102`
  sequence-tuple arm added); `:537` opaque-fallback and
  `:1586` attr-leniency distinguished (plus `:516`
  `try/finally` with no `except`); Matrix J1 line matches.
- R4: "FAM-NEW" tag → verified File
  `rest_framework/inputs.py` file-local
  `serializer-descriptor-identity` row in all 5 pass-1 uses
  (Matrix axis 3 + standing triggers, FL-name-set-spine,
  R-naming-ladder, index row) — two more than the brief's
  "both", same fix.

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
