# DRY review: `types/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights in slot-2 only). Audits the
unassigned remainder of the `types/` folder and the families that
cross its ownership boundaries at current bytes (HEAD `23b5f421` +
working tree). The eight member file artifacts are run-7/run-8 era
inputs, not verdicts: every assignment below was re-derived fresh at
WT bytes, and every assignment the tree has falsified is flagged as a
finding inside this item for the closeout defect-homing pass. No prior
artifact is summarized and no row is reopened.

Verdict: zero-edit CONFIRM. 21 cross-file compositions hold by name
(FC-1..FC-21, each with a fresh census); the f44 consolidation holds
consolidated (owner + 2 bindings + 6 `except` uses, zero residue);
the three already-rowed duplications persist exactly as rowed (f41
gates, f42 walks, f37 template — all open+blocked, specified owners
absent package-wide — no new row); the UNAPPLIED suppression mirror
persists exactly as rowed (no new row); f43's extinction holds (zero
definitions at WT); 29 merges rejected with triggers (FR-1..FR-29,
11 folder-fresh, 18 converging on standing member/family rejections
whose bodies + triggers were re-read at current bytes); 13
tree-falsified prior assignments flagged for closeout (FF-1..FF-13,
rows not reopened); 0 FAM-N (the three load-bearing near-misses —
the unwrap trio, the sentinel quartet, and the six finalized
loop-heads — re-traced fresh and held separate on
wrapper-set/fallthrough, per-absent-question semantics, and
enforcement-site evidence, FR-1 / FR-2 / FR-14); 0 new defects (8
member defects re-verified persisting incl. 1 narrowed, 3 closed by
committed evolution, 1 retired per f43, 1 spent); 0 new Family-hold
rows (no consolidation is blocked beyond what the plan already rows).
The 571-row `tests/types` suite plus the 24-row inspect-CLI suite run
green in slot-2 at current bytes (595/595).

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da`.
`ITEM_BASELINE=86fde7f4eaeabe45299c90da832c23075bd94097`
(resolves as a commit; the item-scoped diff `ITEM_BASELINE` → WT
over the folder plus `tests/types/` is empty, so BASE=WT pre-edit
for every target; the full item-scoped diff names exactly one path,
`docs/dry/dry-0_0_15.md` — Worker-0's dispatch lines, expected).
Slot-2 (`dry/folder-types/consolidate`) verified byte-identical to
WT on all eight targets before tracing and again after the witness
suites (the suites wrote no source). Blob fingerprints are
`git hash-object` (WT) and `git rev-parse HEAD:<path>` (HEAD),
short-8:

| File | Lines WT / HEAD | WT | HEAD | State |
|---|---|---|---|---|
| `types/__init__.py` | 35 / 35 | `1bf69028` | `1bf69028` | clean |
| `types/base.py` | 2150 / 2156 | `f42bcee3` | `a63b7edf` | dirty |
| `types/converters.py` | 963 / 995 | `d8905d0a` | `38f102ab` | dirty |
| `types/definition.py` | 452 / 491 | `dfad92ca` | `2562cb6f` | dirty |
| `types/finalizer.py` | 2180 / 2229 | `8f699081` | `5934789a` | dirty |
| `types/relations.py` | 68 / 68 | `86f27f64` | `86f27f64` | clean |
| `types/relay.py` | 1210 / 1151 | `14f79e02` | `f1c0c6f4` | dirty |
| `types/resolvers.py` | 1034 / 1006 | `cab17014` | `10df9ea7` | dirty |

All eight run-7 member blobs resolve in the object store
(`1bf69028`, `dda91365`, `058f1081`, `fa6c4d33`, `de34ae2a`,
`5e9b5cdb`, `52439862`, `72d62dc4`) and were diffed against WT to
separate committed evolution from concurrent dirt. The run-7
`relations.py` blob (`5e9b5cdb`) differs from HEAD=WT (`86f27f64`)
by typing-only committed evolution (FF-7).

## System trace

The folder owns the type-system subsystem end to end: the leaf
manifest (`__init__.py`: 3-name re-export + dependency-direction
prose), the collection root (`base.py`: `DjangoType` subclass
pipeline, `Meta` orchestration, per-key validators, annotation
synthesis), the conversion layer (`converters.py`: scalar/enum/file
conversion, choice-enum core, relation annotation), the canonical
record (`definition.py`: `DjangoTypeDefinition` slots, GraphQL-name
derivation, relation lookup, custom-id detection), the build gate
(`finalizer.py`: four phases, relation synthesis, sidecar binding,
audits), the deferral records (`relations.py`: identity record +
unfinalized sentinel), the Relay foundation (`relay.py`: predicates,
installs, strategy compute, encode/decode, node defaults), and the
resolve layer (`resolvers.py`: cardinality factory, elision,
strictness, visibility re-check, file pair). Data flows
declare → collect → synthesize → register → finalize → resolve;
Relay flows shape-gate → inject → stamp → encode/decode.
Every cross-folder seam (registry, optimizer, keyset, connection,
filters/orders/mutations inputs, settings, the one-sync-boundary
owner, the visibility runners, upstream Strawberry/Django) is owned
outside and composed by name.

Member-file inputs re-derived at current bytes (not inherited):
[file-init][file-init], [file-base][file-base],
[file-converters][file-converters], [file-definition][file-definition],
[file-finalizer][file-finalizer], [file-relations][file-relations],
[file-relay][file-relay], [file-resolvers][file-resolvers]. Where the
tree falsified an assignment the record sits under Findings as FF
(flag for closeout; no row reopened, nothing re-applied).

### Attribution of the working-tree dirt (by diff content vs HEAD)

154 `@@` hunks across the six dirty files (base 47, converters 19,
definition 8, finalizer 42, relay 22, resolvers 16). Two
provenances, attributed by content against the `## Owned changes`
ledger (swept: zero ledger EDIT rows name `base.py`,
`converters.py`, `definition.py`, `finalizer.py`, `__init__.py`,
or `relations.py` — the lone ledger mention of `base.py` is a
specified-owner symbol cite inside the inspect row, not an edit):

- `resolvers.py` (16 hunks): 9 ledger + 7 hunt. Ledger: the
  `sync_to_async` import drop, the `run_in_one_sync_boundary`
  import, the f44 `_absence_catch_spec` owner, the boundary
  docstring reword, the 2 f44 composing bindings, and the 3
  boundary arms — all matching their ledger rows by content
  (one-sync-boundary orphan + f44). Hunt: the `truth` import,
  the elision-comment extension + new `_in_instance_namespace`,
  the deferred/stub rewrites (`BaseException` arm deletions,
  `except BaseException` → `except Exception`), the namespace
  read, and the `# truth: ok` comment.
- `relay.py` (22 hunks): 1 ledger + 21 hunt. Ledger: the
  `relay-node-type-stamp` reconsideration-trigger comment
  (pure additive, matches by content). Hunt: the `truth` /
  `lazy` / `MethodType` import reshapes, every `isinstance` /
  `getattr` / `__dict__` / `__mro__` / `_safe_*` retarget, the
  `BaseException` deletions, the lazy-proxy unwraps, and the
  new `_ID_NOT_CACHED` / `_classmethod_function` / `slot`
  threading (same wave, no ledger row).
- `base.py` (47), `converters.py` (19), `definition.py` (8),
  `finalizer.py` (42): 0 ledger — all 116 hunks external by
  content (the `truth.*` identity-read migration:
  exception-import narrowings, `model.__name__` → `truth.name`
  renders, `try/except BaseException` deletions, MRO/namespace
  read retargets, the `_class_map_lookup` identity scan +
  `_Missing` sentinel, `_unwrap_method`, prose). Never edited,
  reverted, or tidied here; the two clean files carry zero
  dirt.

## Verification

### Matrix

1. Cross-flavor: the folder serves ONE subsystem (the type
   system) with no flavor mirror. Sibling subsystems re-read
   fresh (mutations inputs compose the converter entries by
   name; filters/orders compose the scalar + sidecar seams;
   rest_framework composes scalar/enum/array/choice readers;
   the CLI predictor keeps its own walk — f42, rowed). The
   `truth.*` read idiom (296 call sites: 119 base + 98
   finalizer + 40 relay + 20 converters + 17 definition + 2
   resolvers) is hunt-owned migration vocabulary, not a
   package rule (FR-5). Discharged.
2. Sync/async: exactly 2 module-level `async def` in the
   folder, both in `relay.py` (`_resolve_node_async` :1069,
   `_resolve_nodes_async` :1142); `resolvers.py` carries 6
   nested async closures (2 visibility + 1 many + 3
   lazy-load offloads); base/converters/definition/finalizer/
   relations/init carry zero colored code tokens (base's 4
   `async def` hits are validator prose). Both relay colors
   share the pure node decisions below the color line
   (FC-17); the resolvers closures offload through the
   composed boundary (FC-6). No cross-file twinship (FR-9).
   Discharged.
3. Derived knowledge: every same-token population walked on
   body strength. Single owners with by-name composers: the
   leaf manifest (1 + root + tests), the collection pipeline
   (1 pipeline + 4 owned seams), the name regex (1 table +
   2 gate spellings — f41, rowed), the MRO walk (1 helper +
   2 legs + 1 predictor — f42, rowed), the enum template (2
   spellings — f37, rowed), the absence spec (1 owner + 2
   bindings + 6 uses — f44, consolidated), the boundary hop
   (1 owner + 3 arms), the strategy validator (1 + 2 paths),
   the memberships (2 sets + 6 readers), the gate wording
   (LEAD 1 + 5 sites, TAIL 1 + 4), the typo format (1 + 5),
   the four skeletons (1 + 2/2/2/3 adapters), the pending
   lifecycle (1 construction + 1 install + 1 resolve +
   ledger), the recheck gates (2 bodies + 9 calls), the
   finalized flag (1 slot + 6 loop-head enforcement sites +
   entry/collection/cache reads), the emit/accept names (1
   set + 2 direction readers). The unwrap trio (FR-1), the
   sentinel quartet (FR-2), the empty-default trio (FR-3),
   the plain-str pair (FR-4), the predicate triple (FR-7),
   and the stage split (FR-6) are distinct contracts or
   per-subject spellings with triggers. Discharged.
4. Round-trip: encode vs decode is one grammar per strategy
   with the memberships shared by both halves (FC-13);
   emit-vs-accept stays two names over one set with the
   split rationale on the set (FC-14); the pending
   record vs sentinel vs resolution is one lifecycle in
   three phases (FC-11); the collection-vs-finalize stage
   split keeps distinct checks per phase (FR-6). No second
   mint, no second resolution: the `PendingRelation(`
   census is 1, `resolved_relation_annotation(` is 1 call,
   `registry.discard_pending` is registry-owned.
   Discharged.
5. Other media: package oracles (`tests/types/`, 571 nodes
   green in slot-2 as `dry-20261010T055635-e2c26e`, incl.
   the f44 triple + the f41 gate pins + the f42 firing-row
   nodes; the 24-row inspect-CLI suite green as
   `dry-20261010T055709-735adf`, incl. the predictor pin),
   live `/graphql` rows (the relay/visibility/upload suites
   pin wire behavior through these rules), contract sources
   (spec-015/018/027/028/029/030/031/032/033/037/047/048/053
   decisions re-read intact where cited; the stale spec-011
   cites are gone — FF-1), projections (module/class/method
   docstrings; the persisting member D-defects ride to
   closeout per `## Defects` and are never fixed here). No
   medium carries a second definition of a folder rule.
   Discharged.
6. Omission: all eight files enumerated below (349 top-level
   statements); every member lands in a verified family row,
   a member-artifact assignment re-verified at current bytes,
   a facet note on a carried row, or one of this item's
   transcribed rows. The deliberate omissions (leaf
   withholding, no `choice_enum_name` / `is_valid_graphql_name`
   owners — both specified-but-unlanded, grep-0 package-wide;
   no second `auto` rule; no `except BaseException` in the
   folder at WT) each carry a contract source or a row. No
   unassigned member remains. Discharged.

### Enumeration

Instrument: `ast` top-level census (`len(ast.Module.body)`,
def / class / import / assign split) over the folder at WT bytes,
plus `grep` + AST composer censuses for every cross-file read.
349 top-level statements total. Every member below lands in a
verified family row (f-numbered), a member assignment re-verified
at current bytes, a facet note on a carried row, or one of this
item's transcribed rows (T-numbers in `## Index rows for
Worker-0`). Run-7 counts in parens; deltas are FF-8.

| File | Top-level members | Homes |
|---|---|---|
| `__init__.py` | 5 stmts: docstring + 3 ImportFrom + Assign (was 5) | F1/F2 converge (manifest / prose); R1..R4 stand (FR-22 + member rows) |
| `base.py` | 76 stmts: docstring + 3 Import + 23 ImportFrom + If + 10 Assign + 6 AnnAssign + 30 def + 2 classes (was 67) | 29 file-local converge + C1 adopt + C2..C6 converges + FAM-NEW (f41, FC-8) + R1..R21/R-MAINT1 stand-or-refresh; `_SidecarT` rides F-SIDECAR (typing facet); `_is_str_tuple` T-1; `_NO_FIELD_NAMES` FR-3 |
| `converters.py` | 57 stmts: docstring + 6 Import + 13 ImportFrom + If + 6 Assign + 20 def + 6 classes + 4 AnnAssign (was 40) | 13 file-local converge + C-ENUM adopt (f37, FC-9) + FAM-MRO (f42, FC-7) + R1..R11 stand-or-refresh; `_T` rides F-GUARD; `_Missing`/`_MISSING`/`_V`/`_class_map_lookup` ride f42; `array_element_field` T-2; the enum-core 5 ride F-ENUMCORE (T-3 cluster); `choice_column_*` T-4; `-_field_has_choices` FF-11 |
| `definition.py` | 21 stmts: docstring + 10 ImportFrom + 1 Import + If + 1 Assign + 1 class + 6 def (was 17) | 8 file-local converge + C1 (f41, FC-8) + C2/C3 converges + FAM-LENIENT (f43 extinction, FR-27) + R1..R19 stand-or-refresh; `_unwrap_method` FR-1 + F-CUSTOMID facet |
| `finalizer.py` | 68 stmts: docstring + 20 ImportFrom + 1 Import + If + 3 Assign + 41 def + 1 class (was 66) | 23 file-local converge (F-SAFE-RENDER HEAD-hold/WT-moot — FF-9) + C1..C18 converges/exclusions + R1..R10 stand-or-refresh; `_SetT` rides F-OWNER-SKELETON; the owner-axes 4: table axis T-5, generalized check = renamed facet (FF-10) |
| `relations.py` | 10 stmts: docstring + 5 ImportFrom + If + 3 classes (was 7: +TYPE_CHECKING block — FF-7) | 4 file-local converge + R1..R10 stand (bodies re-read; typing-only drift) |
| `relay.py` | 58 stmts: docstring + 16 ImportFrom + If + 7 Assign + 30 def + 2 async def + 1 AnnAssign (was 47, s14 53) | 15 file-local converge + A1 adoption + convergences + R1..R23 stand-or-refresh; `_ModelT` rides F-NODE-DEFAULTS; `_ID_NOT_CACHED` FR-2 + F-ID facet; `_classmethod_function` FR-1 + F-INSTALL facet; the node-fetch 4 ride F-COERCE/F-NODE-DEFAULTS (`_node_value_or_none` = e4 consumer); `_plain_globalid_slot` FR-4 + F-DECODE facet; `-_coerce_node_ids` FF-11 |
| `resolvers.py` | 54 stmts: docstring + 2 Import + 22 ImportFrom + If + 2 Assign + 2 classes + 4 AnnAssign + 20 def (was 42) | 14 file-local converge + C-SEAL/C-RECHECK/C-ONEBOUND/C-ORCH/C-GRAMMAR/C-MRO converges + FAM-ABSENCE (f44, FC-5) + R1..R13 stand-or-refresh; the typing 4 ride F-NAME/F-SENT/F-MECH; `_in_instance_namespace` hunt facet of F-ELIDE/F-PROBE; `_prefetch_cache_name` T-6; `_absence_catch_spec` f44; `_NO_SKIPPED_FIELDS` FR-3 |

### Challenges

Authoritative definitions only; consumers, oracles and projections
that also move are listed, never counted. Current bytes.

- C1 leaf membership/rename/home-move → 1 at the home module
  (import lines + `__all__` entries follow as consumers).
- C2 root-export lift → 0 here (the root moves; proves
  separation — FR-22).
- C3 name-grammar change (character class, `__` reservation) →
  2 (base :1398 + definition :271 — f41 persists).
- C4 MRO firing-rule change (order, source, membership test) →
  2 (`_class_map_lookup` + the inspect predictor — f42
  persists).
- C5 enum-template change (suffix, stem, assembly) → 2
  (converters :938 + serializer :1133 — f37 persists).
- C6 absence-catch change (spec members, empty-tuple posture) →
  1 (the f44 owner; 2 bindings + 6 uses follow).
- C7 boundary-hop change (worker, sensitivity) → 1 (the
  owner; 3 arms follow).
- C8 Relay-shape change per phase → 1 per predicate (the
  collection tuple-or-inheritance, the post-injection MRO
  test, the id-column probe move alone — FR-7).
- C9 strategy-vocabulary change (new string name) → 1 (the
  vocab set; payload memberships are separate accept/emit
  decisions, not co-movers — member R8 stands).
- C10 gate-wording change → 1 at the constants owner, 0 here
  for composers (follows by name); factory wordings move
  alone (FR-23).
- C11 target/sidecar/owner/binding rule change → 1 per
  skeleton (4 skeletons + their adapters move as units).
- C12 wrapper-unwrap change (new wrapper type, fallthrough) →
  1 per site (sets 1/3/2, fallthroughs value/value/None —
  FR-1).
- C13 absent-semantics change per sentinel → 1 per sentinel
  (4 sentinels, no co-move — FR-2).
- C14 stage-check change (cursor/shapes/strategy/connection) →
  1 per stage (raw-Meta vs settled-field vs recorded-value
  inputs — FR-6).
- C15 skip-rule change (a second condition beyond
  `finalized`) → the FR-14 trigger: today 1 attribute + 6
  enforcement sites; a second condition owes a predicate
  owner.
- C16 node key-shape change → 2 contracts + 1 machinery twin
  (index `str()` vs key `None`-passthrough differ by side;
  the :1138/:1163 pair is what the twin constraint forces
  into each color — R9 stands).
- C17 plain-str empty-posture change → 1 per side
  (None vs preserved-for-caller-reject — FR-4).
- C18 render-vocabulary change (`truth.*` → owner calls) → 0
  as consolidation (hunt-owned migration spelling — FR-5).
- C19 import-posture change per posture → 1 per posture
  (soft-optional / already-loaded-only / cycle-dodge /
  validated — FR-12).
- C20 audit-invariant change → 1 per audit (5 audits +
  driver, no co-move — FR-10).
- C21 except-spec change → 1 per arm (the f44 arms follow
  their owner; the 4 `NodeIDAnnotationError` fallbacks move
  alone — FR-11).
- C22 dotted-grammar change → 1 per grammar (4 grammars —
  FR-8).
- C23 `str()`-render change per subject → 1 per site
  (FieldFile name vs sanitize coerce vs surface labels vs
  id renders vs reorder keys — FR-13).
- C24 surface-read change per phase → 1 per reader
  (collection override scan vs finalize settled surface vs
  key gate — FR-15).
- C25 Meta-read change (new wrapper, new namespace) → 1 per
  reader (contained MRO vs own-namespace counterpart vs
  runtime rows — FR-16).
- C26 suppression-mirror landing → 0 landed (UNAPPLIED;
  maintainer decision owed — FR-28).
- C27 lenient-read change → 0 (extinct at WT — FR-27).
- C28 spec prose / bullet prose / framing prose changes → 0
  definitions here (projections follow).

## Findings

### Compositions (each holds by name at current bytes)

Leaf and withholding. FC-1 manifest: the leaf binds exactly 3
names (re-read) with `__all__` mirroring them (probed:
`sorted(__all__)` is exactly the 3); the by-name identity probed
(`types.DjangoType is base.DjangoType`, `finalize` is
`finalizer.finalize_django_types`, `SyncMisuseError` is
`relay.SyncMisuseError`); the root re-exports the same 3 from the
leaf (`__init__.py:52` + `__all__`, identity probed); in-package
code consumers resolve through the leaf (`list_field.py:85`) or
read submodules through it (test-only `types.base` /
`types.converters` / `types.relay` / `types.finalizer` /
`types.resolvers` module reads — re-censused, zero competing
manifests). FC-2 withholding: 10 dotted-path-only names probed
absent from the leaf (`PendingRelation`,
`PendingRelationAnnotation`, `DjangoTypeDefinition`,
`convert_scalar`, `convert_field_output`,
`convert_choices_to_enum`, `build_enum_from_choices`,
`decode_global_id`, `encode_typename`, `implements_relay_node`);
relations consumers go dotted (registry TYPE_CHECKING + 4 test
files, re-censused); converter/resolver/relay consumers import
the submodule path, never the leaf (name-level withholding, not
module-level — the docstring states it).

Collection and conversion. FC-3 pipeline: `__init_subclass__`
owns the orchestration; the definition record has its single
construction site (`base.py:850`); `PendingRelation` has its
sole construction (`base.py:2093`) + sentinel install (`:2102`);
`convert_field_output` has its sole production caller (`:2143`);
`install_is_type_of` has its sole call (`:881`). FC-4 entries:
`convert_scalar` 4 calls (recurse :498 + route :583 +
mutations :761 + serializer :1066), `scalar_for_field` 5
(in-file :519 + serializer ×2 + mutations :493 + filters :361),
`build_enum_from_choices` 2 (:941 + serializer :1136),
`array_element_field` 4 (in-file ×2 + serializer ×2),
`choice_column_values` / `choice_column_is_grouped` 1 each
(serializer :931/:1008) — every entry single-owned here,
composed cross-file by name.

Rowed families. FC-5 absence (f44): the owner (`:556`) + 2
bindings (reverse :763, forward :805) + 6 `except` uses;
`related_model.DoesNotExist` constructed exactly once
(`:576`, all other hits prose); the 3 f44 oracles green in
the witness. FC-6 boundary: the 3 `run_in_one_sync_boundary`
arms (:772/:838/:910) + import; zero `sync_to_async` code
tokens (sole folder token the `:642` never-a-copy prose).
FC-7 MRO (f42): the single in-folder walk body
(`_class_map_lookup` :359) + 2 leg composers (`:390`/`:541`);
the inspect predictor keeps its own walk (:502-518);
specified pair-owner unlanded. FC-8 name gate (f41): the
regex table (1 def, composed by the base import :75) + the 2
gate spellings (base :1398, definition :271); specified
`is_valid_graphql_name` grep-0 package-wide. FC-9 template
(f37): D1 (`:938`) + D2 (serializer :1133), same
interpolation + same stem; specified `choice_enum_name`
grep-0 package-wide. FC-10 recheck (e3): `_visible_many_rows`
+ 2 gated calls (:705/:733) and `_visible_related_object` +
7 gated calls (:782/:797/:851/:868/:887/:925/:945) —
re-derived exactly. FC-11 pending lifecycle: construct +
install (base) → Phase-1 resolve (finalizer :939, sole
caller of `resolved_relation_annotation`) → `discard_pending`
(registry-owned ledger).

Relay and strategy. FC-12 validation: `_validate_globalid_strategy`
1 def + 2 calls (meta path :1465, setting path relay :526 —
"one validator, two sources"); the vocab/default composed by
the precedence resolver (in-function import, :558).
FC-13 memberships: `MODEL_LABEL_STRATEGIES` /
`TYPE_NAME_STRATEGIES` 1 def each + readers (the 3 relay
predicates, finalizer :399/:423/:458, decode :968, the
strategy-aware filter) — never re-typed. FC-14 emit/accept:
one set + two direction-names with identical bodies and the
split rationale recorded on the set (C9: the memberships are
the accept/emit decisions, so a split moves the set while the
predicates keep reading their halves).
FC-15 custom-id: `origin_has_custom_id_resolver` 1 def +
the memoized method + the optimizer fallback
(`walker.py:1677-1679`, re-pinned). FC-16 wording: LEAD 1
def + 5 compose sites (4 in-file :296/:344/:400/:474 + the
testing helper :104); TAIL 1 + 4 (:297/:344/:474 + helper
:105); the relay.py:487 / connection.py:2427 parenthesized
variants stay inline (different subjects + byte shape —
FR-23). FC-17 node twins: both colors share `_node_values`,
`_apply_node_filter`, `_apply_nodes_filter`, `_order_nodes`,
`_raise_if_required`; the `coerced_keys` :1138/:1163 pair +
index :1007 stay per R9 (C16).

Finalize. FC-18 orchestration: the Phase-2 attachers have
their sole callers (:957/:971) with deliberately different
skip sets (assigned-only vs full union, spec-037); the
synthesis composes `_connection_type_for` + the resolver
builder + `DEFAULT_RELATION_SHAPE` + `implements_relay_node`
(all by name); the setting snapshot is computed once
(:877) with the retry-mix refusal; the audits read recorded
values, never re-validate. FC-19 typo format: 1 def + 5
compose sites (select ×2, hints ×2, skeleton :1629).
FC-20 skeletons: `_selected_meta_targets` 1 + 3 validators,
`_validate_set_sidecar` 1 + 2 wrappers, `_bind_set_owner_common`
1 + 2 binders, `_bind_sidecar_sets` 1 + 2 specs — each a
single body with named adapters, never mode flags. FC-21
finalized protocol: the registry owns the flag; the finalizer
entry-guards once (:854); 6 two-line loop-head guards
(:664/:955/:978/:1130/:1135/:1925) + the base collection
guard (:682) + the definition cache read (:318) are
enforcement sites of the rerun contract (FR-14), not copies;
zero window-`to_attr` constructions in the folder (the one
`_dst_`-prefixed def is the synthesis re-entrancy marker,
a different namespace).

### FAM verdict: none raised

Twenty-nine twin hypotheses were traced to a verdict; every one
resolves to single ownership, a standing rejection with an
unmet trigger, an already-rowed blocked duplication, or a
distinct contract (FR-1..FR-29). The three load-bearing
near-misses are FR-1 (the unwrap trio shares the
exact-type-then-`__func__` shape, but the wrapper sets are 1 /
3 / 2 by contract — Meta carries only `staticmethod`, id
markers ride three wrapper kinds, typename entries ride two —
and the fallthroughs are value / value / `None`: a shared
helper needs a mode flag for both axes, which is machinery,
not relief; C12 proves opposite move sets), FR-2 (the
sentinel quartet shares the one-member-enum / bare-object
shape, but each answers a different absent-question — map
miss vs unread plan vs uncached column vs absent member —
with different narrowing needs; a shared sentinel couples
four unrelated absence contracts), and FR-14 (the six
finalized loop-heads share the two-line spelling, but each
sits at its own phase loop as an enforcement site of the
rerun contract — `continue` cannot compose through a call,
and today the rule is one attribute read; C15 names the
trigger that would owe a predicate owner: a second skip
condition). The f41/f42/f37 count-2 verdicts persist but are
already rowed open+blocked with specified owners, the
suppression mirror is already rowed UNAPPLIED, and f43's
extinction holds — so no new Family-hold row is owed: no
consolidation is blocked beyond what the plan already rows.

### Rejections (each re-derived fresh; triggers re-checked)

Folder-fresh:

- FR-1 unwrap trio: `base._meta_attr`'s staticmethod arm
  (1 wrapper kind, falls through to the value) vs
  `definition._unwrap_method` (3 kinds, falls through to the
  value) vs `relay._classmethod_function` (2 kinds, falls
  through to `None`) — wrapper sets fixed by what each
  subject can hold, fallthroughs fixed by what each caller
  compares (C12). Trigger: one shared unwrap protocol with
  an aligned wrapper set + fallthrough.
- FR-2 sentinel quartet: converters `_MISSING` (map miss,
  narrowing `is`) vs resolvers `_PLAN_UNREAD` (unread plan,
  type-narrowing) vs relay `_ID_NOT_CACHED` (uncached column
  where `None` is a value) vs finalizer `_MISSING_CLASS_MEMBER`
  (absent member) — four absent-questions, four narrowing
  needs (C13). Trigger: a shared sentinel protocol with
  callers at all four questions.
- FR-3 empty-default trio: base `_NO_FIELD_NAMES` (4
  `_build_annotations` params) vs resolvers
  `_NO_SKIPPED_FIELDS` (2 attacher params) vs resolvers
  `_EMPTY_ELISIONS` (per-row elision branch) vs 5 inline
  `frozenset()` dataclass defaults — per-param defaults; a
  change to one default's call shape moves only that
  default, so zero definitions move together. No trigger
  (needs a reason for unrelated defaults to move as one).
- FR-4 plain-str pair: `definition._normalize_pk_name`
  (non-`str` → `None`, empty → `None`) vs
  `relay._plain_globalid_slot` (non-`str` → `None`, empty
  preserved for the caller's distinct empty-slot reject) —
  different empty postures + different caller error
  contracts (C17). Trigger: aligned empty postures under
  one caller contract.
- FR-5 `truth.*` vocabulary (296 call sites): hunt-owned
  migration spelling — every site is WT dirt over a HEAD
  `isinstance` / `getattr` / `_safe_*` / `__mro__` site,
  and no ledger row names four of the six files. No
  trigger (needs a package read rule; the consolidation
  would edit hunt-owned lines).
- FR-6 stage split: base stage-1 validators (raw-`Meta`
  shape + gates) vs base stage-2 target validators
  (settled fields + override union) vs finalizer audits
  (recorded strategies, settled targets, built surface) —
  each stage owns checks its inputs alone permit (C14).
  Trigger: one check that must run identically at two
  phases on the same inputs.
- FR-7 predicate triple: base `_is_relay_shaped`
  (pre-injection tuple-or-inheritance, 3 in-file calls) vs
  relay `implements_relay_node` (post-injection MRO test,
  8 + 6 calls) vs the definition id-column probe
  (fail-closed column read) — timing/phase split with the
  distinction recorded at both owners (C8). Trigger: shape
  knowledge available at a single phase.
- FR-8 model-label split: relay :943 (GlobalID type-name
  slot grammar) vs the client / error-path / filter splits —
  four dotted grammars, four contracts (C22). Trigger: one
  shared dotted-path grammar owner.
- FR-9 color confinement: the relay node pairs share their
  pure decisions below the color line (FC-17); the
  resolvers closures offload lazy reads through the
  composed boundary (FC-6); the remaining six files carry
  zero colored code tokens — no cross-file twin exists.
  No trigger (needs a second colored site of one rule).
- FR-10 audit cluster: 5 audits (ambiguity, surface,
  routing, unregistered targets, encode-only strategies) +
  the ordered subpass-2.5 driver + 13 formatters —
  per-invariant rules with per-subject messages; the shared
  skeletons already own what is shared (FC-20). Trigger: a
  second audit needing an existing audit's invariant.
- FR-11 `NodeIDAnnotationError` quartet: composite-gate
  pass vs stamp `"pk"` vs live-scan `"pk"` vs off-pk
  `False` — per-site fallbacks with per-site reasons
  (C21). Trigger: one shared no-annotation fallback
  policy.

Member/family-twin re-verifications (each body re-read fresh):

- FR-12 import postures (CONVERGE R19/R6): soft-optional
  postgres (`import_attr_if_importable`, absent-driver
  `None`) vs already-loaded-only auth (`loaded_attr`,
  opt-in contract) vs cycle-dodge locals (documented
  per-edge) vs validated settings reads — four contracts,
  four postures (C19). Triggers as membered.
- FR-13 `str()` pair (CONVERGE R4): FieldFile stored name
  vs sanitize coerce vs surface labels vs id renders vs
  reorder keys — per-subject renders (C23). Trigger as
  membered.
- FR-14 loop-head guards (CONVERGE C5/R10/R18): 6 two-line
  guards + entry/collection/cache reads are enforcement
  sites of the rerun contract, never definitions (FC-21);
  `continue` cannot compose through a call. Trigger: a
  second skip condition (C15).
- FR-15 surface reads (CONVERGE R15/C6): collection
  override scan (base) vs settled pre-decoration surface
  (finalizer) vs annotation-key gate — different phases,
  different questions (C24). Triggers as membered.
- FR-16 Meta reads (CONVERGE R17): contained MRO walk
  (`_meta_attr`) vs own-namespace counterpart (prose-pinned
  intentional split) vs runtime row reads (different phase:
  class bodies vs live rows) (C25). Trigger as membered.
- FR-17 sequence ladders (CONVERGE R13): fields spec
  (`__all__`/`None` semantics) vs sequence spec
  (set-acceptance + keyed messages) sharing only the
  `_is_str_tuple` guard (T-1). Trigger as membered.
- FR-18 `auto` solitude (CONVERGE R11): the `"auto"` /
  `"strawberry.auto"` marker (:643-644) is the folder's
  only `auto` rule — the strategy vocabularies hold no
  `auto` (census re-derived). No trigger (needs a second
  `auto` rule).
- FR-19 pk vocabularies (CONVERGE R7/R8-definition):
  2 name reads (base :1714/:2070) vs 1 column key (relay
  id-cache :355) vs 1 composite gate (relay :213) —
  name/column/object questions; zero `.attname` code in
  base. Trigger as membered.
- FR-20 coerce-vs-reject (CONVERGE R18/R5/R3): enum
  sanitize PREFIXES (`MEMBER_`, coerce verb) while the f41
  gates REJECT (reject verb) and the dunder reservation is
  one conjunct of the gate — three verbs, three owners.
  Trigger: one name-policy owner for coerce+reject.
- FR-21 MRO-scan exclusions (CONVERGE f42 R2/R3/R4):
  definition marker scan vs base declaration walk vs
  finalizer surface walk vs relay membership filter —
  each answers a different question than key lookup
  (bodies re-read). Triggers as f42'd.
- FR-22 leaf vs root (CONVERGE init R1): the root
  re-exports exactly the 3 from the leaf (identity
  probed — FC-1); lifting lives at the root (C2).
  Trigger as membered.
- FR-23 gate vs factory wording (CONVERGE R4): Meta-key
  gates (LEAD/TAIL constants) vs field-guard wordings
  (different subjects, parenthesized tail shape —
  re-read). Trigger as membered.
- FR-24 cache keyings (CONVERGE f37 R5): `(model,
  field)` registry keying vs descriptor-derived enum
  names — storage vs naming. Trigger as familied.
- FR-25 branch twins (CONVERGE R4/R5/R6/R8-resolvers):
  single/many probes, fetch arms, visibility gates,
  recourse wordings stay per-branch (bodies re-read).
  Triggers as membered.
- FR-26 file/column/postgres/ladder pairs (CONVERGE
  R9/R10/R11-converters): output nullability vs column
  null, column-type dispatch vs plan sentinel, fallback
  typing vs registry walk (bodies re-read). Triggers as
  membered.
- FR-27 lenient extinction (CONVERGE f43): zero surviving
  definitions at WT — definition :327-329 reads directly
  (C27). Trigger as familied (a second
  raising-read-containment site reopens).
- FR-28 suppression mirror (CONVERGE C3): UNAPPLIED —
  specified base owner grep-0, inspect predictor inline
  composing `_is_relay_shaped` (:309, re-read); maintainer
  decision still owed (C26). No trigger (decision-owned).
- FR-29 seam convergences (C-SEAL/C-ONEBOUND/C-ORCH/
  C-GRAMMAR/C-MRO + finalizer C1/C2/C3/C13/C14/C15):
  seal/boundary/orchestration/grammar/MRO/settings/
  factory/ledger/teardown seams all compose their outside
  owners by name at WT (3 boundary arms, `to_attr`
  threading with zero in-folder constructions, MRO
  mechanism via `truth`, snapshot once, factory
  arguments, teardown + subsystem clears — each
  re-pinned). Transcribe nothing.

### Falsifications (record-only; no row reopened, nothing re-applied)

- FF-1 base D1 CLOSED: `spec-011` greps 0 at HEAD and 0 at
  WT (fixer `ba9c2967`, committed). The run-7 five-cite
  record is spent; close with no home.
- FF-2 definition D1 CLOSED: the slot reads
  `TODO-BETA-059-0.1.1` at HEAD :87 and WT :88 (fixer
  `ba9c2967`, committed); dedups against the card-053
  bullet the defect already names. Close with no home.
- FF-3 finalizer D3 CLOSED: `set_model: object` at HEAD
  :1668 and WT :1623 (fixer `dfbea72b`, committed). The
  annotation now admits the documented `str` case. Close
  with no home.
- FF-4 init D1 NARROWED: `RelationKind` is a live import
  at WT (resolvers :71, landed committed `999a1aab`) but
  `relation_kind` still has zero importers folder-wide
  (re-censused); the parenthetical additionally misses the
  live `instance_accessor` / `is_many_side_relation_kind` /
  `is_single_column_foreign_key` names. Persists narrowed.
- FF-5 definition D3 RETIRED per f43: the guarded rung the
  defect cites no longer exists — WT :327-329 reads
  `model_field.is_relation` / `.related_model` directly
  (concurrent rewrite); f43 verified the extinction +
  inverted oracles package-wide and retired the coupling.
  No home (family-owned).
- FF-6 resolvers O1 SPENT: all three `except BaseException`
  arms reworked by hunt dirt (verified in the diff: 2
  deleted, 1 narrowed to `Exception`). No home (the
  observation named the hunt card, not a DRY card).
- FF-7 relations blob `5e9b5cdb` → `86f27f64` (committed
  typing: `TYPE_CHECKING` block + `ModelField` +
  `@override`, runtime-neutral, diff-read). The run-7
  "7 stmts" cite is stale (now 10); verdicts intact.
  Closeout refreshes the cites.
- FF-8 enumeration drift (record only, verdicts intact):
  base 67→76, converters 40→57, definition 17→21,
  finalizer 66→68, relay 47→53(s14)→58, resolvers 42→54 —
  every added/removed name diffed mechanically run-7→WT
  and homed in `### Enumeration` (6 T file-local rows +
  family rides + facet notes + FR homes). New-rule homes
  transcribe as T-1..T-6; carried rows stand.
- FF-9 finalizer `_safe_*` trio deleted by hunt dirt
  (`_safe_qualified_class_name`, `_safe_field_label`,
  `_safe_str` grep-0 at WT): F-SAFE-RENDER holds at HEAD,
  moot at WT. Blocked-on-hunt: closeout revisits only
  after the hunt lands or is dropped.
- FF-10 owner-axes decomposition (committed evolution):
  `_check_filterset_owner_get_queryset_safety` generalized
  to `_check_set_owner_get_queryset_safety` (within-file
  consolidation, already landed); the table-identity axis
  (`_check_set_owner_table_identity` +
  `_format_owner_table_mismatch_error`) + the orders
  adapter are new (T-5). Carried homes stand; no new row
  for the rename.
- FF-11 renames/absorptions (committed evolution):
  converters `-_field_has_choices` (absorbed into
  `field.choices` truthiness :492/:506/:520);
  relay `-_coerce_node_ids` (→ `_node_values`). Carried
  homes stand; no action.
- FF-12 pin drift (record only): relay D1 :735-739 →
  :898-902; inspect 4th-consumer :401 → :420; f41 gates
  :1384/:269 → :1398/:271; s14 `coerced_keys` :1055/:1080
  → :1138/:1163. Verdicts intact; closeout refreshes.
- FF-13 suppression-mirror endpoints re-pinned: specified
  base owner grep-0 (unlanded); inspect :285-309 inline
  predictor composing `_is_relay_shaped` (the run-3
  reverted state, re-read). Row stands UNAPPLIED.

## Defects

None found while tracing. Checks run: every member's docstring
re-read against its body at WT (leaf consumption claims —
FF-4; gate-census comments — testing-relay D1 below;
converter mechanism/census prose — converters D1/D2;
finalizer subpass prose — finalizer D2; no NEW
contradiction); every guard family enumerated for omission
against its contract source (the 6 loop-head guards +
entry/collection/cache reads, the 4 LEAD / 3 TAIL in-file
gate-wording sites + the testing helper, the 4
NodeIDAnnotationError fallbacks, the 9 recheck gates, the 22
executable `except` arms (28 token lines less 6 prose/comment)
— no missing member); layering claims hold (resolvers imports
nothing from base; definition
imports base only under TYPE_CHECKING; relay→base and
finalizer→filters/orders/mutations edges are the documented
in-function cycle dodges; the walker lazy read is the single
sanctioned exception — no reversed import, no cycle).

Member defects re-verified at current bytes (record-only;
each already rides to closeout under its member item — no
new homing except where noted):

- init D1 NARROWED (FF-4): `RelationKind` now live
  (resolvers :71), `relation_kind` still dead, live names
  unlisted. Persists narrowed — closeout amends the fix
  shape, same owner.
- converters D1 persists (module docstring :26-28 + map
  comment :282-288 still claim dict order decides; the
  walk iterates MRO — `_class_map_lookup` :369-374
  re-read). Converters D2 persists (walk shared by 4
  production sites — in-file :581 + resolvers :1032 +
  base :1799 + inspect :420 — against the "only ... and"
  prose). Both ride.
- definition D2 persists (the "Do NOT hoist" cycle
  rationale :301-303 re-read verbatim). Rides.
- finalizer D1 persists (subpass-1 skip :1925-1926 +
  ledger-compare :1954-1960 re-read; helper ledgers still
  register without `before_bind`, so the pre-bind sweep
  still preserves them across rerun). Finalizer D2
  persists ("four" ×4 + driver 1-5 + fractional body
  comments, all re-read). Both ride.
- relations D1 persists (the parenthetical at
  `utils/relations.py:150` WT, double-backtick form;
  the record still carries no kind and is still not the
  sentinel — re-read). Rides.
- relay D1 persists (the cycle rationale + mispoint at
  :898-902 WT, re-read). Rides.
- testing-relay D1 persists (the :139-151 census comments
  still say "three" against 4 LEAD / 3 TAIL in-file sites +
  the helper — FC-16). Rides under its member item.
- base D1, definition D1, finalizer D3: CLOSED (FF-1/FF-2/
  FF-3) — they do not ride.
- definition D3: RETIRED per f43 (FF-5). Resolvers O1:
  SPENT (FF-6). Neither rides.

## Pending execution

No `proof:` owed (zero-edit: nothing to prove beyond the
green witness already run). `gate:` entries for the final
gate:

- `gate:` `uv run python scripts/workspace.py run
  dry/folder-types/verify-1 -- python -m pytest tests/types
  -q --no-cov -p no:cacheprovider` (re-run the 571-row
  witness; ran green in slot-2 as
  `dry-20261010T055635-e2c26e`).
- `gate:` `uv run python scripts/workspace.py run
  dry/folder-types/verify-1 -- python -m pytest
  tests/management/test_inspect_django_type.py -q --no-cov
  -p no:cacheprovider -n0` (re-run the 24-row CLI witness;
  ran green in slot-2 as `dry-20261010T055709-735adf`).
- `gate:` the P1 leaf probe (manifest mirror + identity +
  10-name withholding + root identity; ran green in slot-2
  as `dry-20261010T055627-617e9e`) — re-runnable from
  `~/dry/tmp/folder_types_p1.py` with the
  verify copy root as argv[1].
- `gate:` the final gate's live `/graphql` suites carrying
  type-system rows (relay, visibility, uploads, choices,
  multi-db) — named by the gate, not re-run here.
- Cells `inapplicable by construction` for this item's own
  verdicts: the folder makes no database, alias, or dialect
  decision (sole `.using()` honors the row's own alias;
  node-fetch, visibility, bound, and seal primitives are
  owned elsewhere and cell-covered by their own suites) —
  the same construction the relay member ruled.

## Judgment

The folder is at single ownership: 21 compositions hold by
name with fresh censuses and probes, the f44 consolidation
holds with zero residue, the three already-rowed duplications
plus the UNAPPLIED mirror persist exactly as rowed
(open+blocked / decision-owed), f43's extinction holds, 29
twin hypotheses resolve without a new second definition, and
the witness suites run 595/595 green at current bytes. The 6
new file-local rules + the 11 folder-fresh rejections
transcribe below as T-1..T-17 for Worker-0 to row. Zero
edits, zero new defects, zero new blocked consolidations.

## Index rows for Worker-0

One line per row; Worker-0 alone edits the plan. Holding
item for all: Folder integration `types/`.
Freshness: WT blobs in `## Pins and fingerprints` (BASE =
WT); HEAD troupes listed there for the six dirty files.
No tracked files changed (item-scoped diff names only
`docs/dry/dry-0_0_15.md` — Worker-0's dispatch lines; no
ledger rows); HEAD unmoved at `23b5f421`; slot-2
byte-identical re-verified after the witness suites; NO
`## Families` item (no new multi-definition rule — the
three blocked duplications + the UNAPPLIED mirror are
already rowed); no `docs/dry/temp-tests/` scratch was
created (the P1 probe lives at
`~/dry/tmp/folder_types_p1.py`, outside both
trees). No commit.

File-local (new rules at WT bytes, each single-owned):

- T-1 `types-base-str-tuple-guard` (FR-17/`### Enumeration`)
  — files `types/base.py` — file-local (`_is_str_tuple`:
  1 def + 3 calls :336/:984/:1020).
- T-2 `types-converters-array-element-reader`
  — files `types/converters.py`,
  `rest_framework/serializer_converter.py` — file-local
  (`array_element_field`: 1 def + 4 calls, 2 in-file +
  2 serializer).
- T-3 `types-converters-enum-core-decomposition`
  — files `types/converters.py` — file-local (the 5
  enum-core helpers as facets of F-ENUMCORE: group test,
  entry unpack, pair normalization, blank insert,
  empty-string admission).
- T-4 `types-converters-write-side-choice-readers`
  — files `types/converters.py`,
  `rest_framework/serializer_converter.py` — file-local
  (`choice_column_values` + `choice_column_is_grouped`:
  1 def each, composing the shared core by name,
  1 serializer caller each).
- T-5 `types-finalizer-owner-table-identity`
  — files `types/finalizer.py` — file-local (the table
  axis: check + formatter + orders adapter).
- T-6 `types-resolvers-prefetch-cache-name`
  — files `types/resolvers.py` — file-local
  (`_prefetch_cache_name`: Django's manager cache-name
  rule, 1 def + in-file callers).

Rejections (folder-scope merges considered; each with trigger):

- T-7 `types-unwrap-trio-merge` (FR-1) — files
  `types/base.py`, `types/definition.py`,
  `types/relay.py` — rejected (wrapper sets 1/3/2 +
  fallthroughs value/value/None; trigger: one shared
  unwrap protocol with an aligned set + fallthrough).
- T-8 `types-sentinel-quartet-merge` (FR-2) — files
  `types/converters.py`, `types/resolvers.py`,
  `types/relay.py`, `types/finalizer.py` — rejected
  (four absent-questions + narrowing needs; trigger: a
  shared sentinel protocol with callers at all four).
- T-9 `types-empty-default-merge` (FR-3) — files
  `types/base.py`, `types/resolvers.py`,
  `types/definition.py` — rejected (per-param defaults;
  no trigger — needs a reason for unrelated defaults
  to move as one).
- T-10 `types-plain-str-merge` (FR-4) — files
  `types/definition.py`, `types/relay.py` — rejected
  (empty→None vs empty-preserved + caller contracts;
  trigger: aligned empty postures under one contract).
- T-11 `types-render-vocabulary-merge` (FR-5) — files
  `types/base.py`, `types/converters.py`,
  `types/definition.py`, `types/finalizer.py`,
  `types/relay.py`, `types/resolvers.py` — rejected
  (hunt-owned migration spelling, 296 sites; no
  trigger — needs a package read rule).
- T-12 `types-stage-merge` (FR-6) — files
  `types/base.py`, `types/finalizer.py` — rejected
  (each stage owns checks its inputs alone permit;
  trigger: one check identical at two phases on the
  same inputs).
- T-13 `types-predicate-triple-merge` (FR-7) — files
  `types/base.py`, `types/relay.py`,
  `types/definition.py` — rejected (timing/phase split,
  recorded at both owners; trigger: shape knowledge at
  a single phase).
- T-14 `types-model-label-split-merge` (FR-8) — files
  `types/relay.py` (+ the client / error-path / filter
  split owners) — rejected (four dotted grammars;
  trigger: one shared dotted-path grammar owner).
- T-15 `types-color-confinement` (FR-9) — files
  `types/relay.py`, `types/resolvers.py` — rejected
  (colors confined per file, shared decisions below
  the line; no trigger — needs a second colored site
  of one rule).
- T-16 `types-audit-cluster-merge` (FR-10) — files
  `types/finalizer.py` — rejected (per-invariant rules
  + per-subject messages; trigger: a second audit
  needing an existing audit's invariant).
- T-17 `types-nodeid-fallback-merge` (FR-11) — files
  `types/relay.py`, `types/definition.py` — rejected
  (per-site fallbacks with per-site reasons; trigger:
  one shared no-annotation fallback policy).

Closeout notes (not rows): FF-1/FF-2/FF-3 (close base D1,
definition D1, finalizer D3, no home); FF-4 (amend init
D1's fix shape to the narrowed record, same owner);
FF-5/FF-6 (no action — f43-retired / spent); FF-7/FF-8/
FF-10/FF-11/FF-12/FF-13 (no plan change — cite refreshes
+ evolution notes, verdicts intact); FF-9 (conditional:
revisit F-SAFE-RENDER only after the hunt lands or is
dropped); f41/f42/f37 persist open+blocked (no change);
suppression mirror persists UNAPPLIED (no change); the 8
persisting member D1s/D2s ride (no new homing).

## Independent verification (Worker-2)

Verdict: verified (plain; no pending execution owed by this item — every
`gate:` entry re-ran green in slot-3; the live `/graphql` suites stay the
final gate's, named not run).

Sequencing disclosure: the dispatch brief ordered reading the full
artifact before tracing, so the worker-2.md expectation-first order was
not followed literally. Mitigation: every pin, census, and body below
was re-derived with my own greps/pins/censuses at WT bytes and only
then compared against W1's record. No W1 count was trusted without an
independent re-count.

Slot-3 (`dry/folder-types/verify-1`) was already `ready`; I re-verified
it byte-identical to WT on all eight targets before running anything
(all short-8 match). HEAD `23b5f421` unmoved throughout.

Pins (own `git hash-object` / `git rev-parse HEAD:<path>` / `wc -l`):
all eight match W1 exactly — `__init__` 1bf69028=HEAD clean (35/35),
base f42bcee3/a63b7edf dirty (2150/2156), converters d8905d0a/38f102ab
dirty (963/995), definition dfad92ca/2562cb6f dirty (452/491),
finalizer 8f699081/5934789a dirty (2180/2229), relations 86f27f64=HEAD
clean (68/68), relay 14f79e02/f1c0c6f4 dirty (1210/1151), resolvers
cab17014/10df9ea7 dirty (1034/1006). All eight run-7 blobs resolve.

Zero-edit: `git diff ITEM_BASELINE --name-only` names exactly
`docs/dry/dry-0_0_15.md` (Worker-0 dispatch lines, read: 8 insertions);
over `django_strawberry_framework`/`tests`/`examples` the diff is empty.
The artifact itself is untracked (the item's only addition). No ledger
row owed. Ruff gates N/A — zero `.py` touched.

Dirt attribution: 154 `@@` hunks exactly as rowed (47/19/8/42/22/16;
both clean files zero bytes). Ledger sweep over `## Owned changes`
confirms zero rows naming base/converters/definition/finalizer/`__init__`/
relations (the lone `base.py` mention is the specified-owner symbol cite
in the inspect row). Ledger halves confirmed by content: resolvers
`sync_to_async` import drop (HEAD :30 gone at WT), `run_in_one_sync_boundary`
import, f44 owner + 2 bindings, boundary docstring, 3 arms; relay
`relay-node-type-stamp` trigger comment (pure additive hunk). Hunt halves
match the `truth.*` migration spelling throughout.

Enumeration: own AST census 5/76/57/21/68/10/58/54 = 349 with every
def/class/import/assign split exact. `truth.*` 296 exactly
(119/98/40/20/17/2). Async: 2 module-level in relay (:1069/:1142), 6
nested closures in resolvers (:476/:499/:746/:770/:836/:908), base's 4
hits all validator prose, four files zero tokens. 22 executable `except`
arms (1/2/2/2/7/8).

Compositions FC-1..FC-21: all hold. Independently re-censused:
leaf 3-name mirror + identity + root identity + 10-name withholding
(P1 probe re-run green, see gates); pipeline single sites (:850, :2093,
:2102 sentinel install, :2143, :881); converter entries 4/5/2/4/1/1 with
exact cross-file callers; f44 owner :556 + bindings :763/:805 + 6
`except` uses (:777/:792/:843/:860/:915/:935) + single `DoesNotExist`
construction :576; boundary 3 arms + zero code `sync_to_async`; f42
walk :359 + legs :390/:540 (see O-1) + predictor :502 with own walk;
f41 table :35 + gates :1398/:271 with `is_valid_graphql_name` grep-0
package-wide; f37 :938 + serializer :1133 with `choice_enum_name`
grep-0; recheck 2 + 7 calls at the cited lines; pending lifecycle
(sole `PendingRelation(` :2093, sole `resolved_relation_annotation`
caller :939, registry `discard_pending`); validator 1+2 (:415 def,
:1465/:526 calls); memberships never re-typed (finalizer reads via the
predicates :399/:423/:458); emit/accept identical bodies over one set;
custom-id def + memoized method + walker fallback :1677-1679; LEAD
1+5 / TAIL 1+4 at the cited lines; node twins share the 5 pure helpers
with the :1138/:1163 pair + :1007 per R9; attachers :957/:971 with the
documented differing skip sets; snapshot :877; typo formatter 1+5
(:1575/:1585 hints, :1630 skeleton — see O-2, :1930/:1944 select);
skeletons 1+3/1+2/1+2/1+2 (base :1600/:164 + finalizer :1146/:1901 with
exact callers); finalized flag 6 two-line guards + :854/:682/:318.

Near-misses re-traced on bodies: FR-1 wrapper sets 1/3/2 with
fallthroughs value/value/`None` (exact-type checks read); FR-2 four
sentinels answering four absent-questions with distinct narrowing;
FR-14 six `if definition.finalized: continue` loop-heads (each read) —
enforcement sites, `continue` cannot compose through a call, C15 trigger
names the predicate-owing change. No FAM-N owed: my own twin-hunt
(duplicate top-level defs across the folder, second finalize/`auto`/
`PendingRelation` construction, `Prefetch(`, strategy-literal residue,
folder dotted-splits — exactly one, :943) is negative throughout.

Blocked/extinct families: f41/f42/f37 persist exactly as rowed
(count-2 bodies re-read, specified owners grep-0); suppression mirror
UNAPPLIED (specified `types/base.py::_is_suppressed_relay_pk` absent —
only the inspect command's own method exists; inline predictor :285-309
composing `_is_relay_shaped`; ledger run-3 revert row confirms);
f43 extinct (zero `lenient` tokens in `types/`, :327-329 reads directly;
plan row concurs).

Falsifications FF-1..FF-13: each confirmed — spec-011 grep-0 at HEAD
and WT; TODO slot :87/:88; `set_model: object` :1668/:1623; FF-4
narrowing (`RelationKind` live :71, bare `relation_kind` zero folder
importers, three live names unlisted); FF-5 direct reads; FF-6
(HEAD 3 `except BaseException` arms → 2 deleted + 1 narrowed to
`Exception` in the diff); FF-7 typing-only blob diff; FF-8 drift homed;
FF-9 trio grep-0 at WT / 3 defs at HEAD; FF-10 generalization present
in both HEAD and WT (committed pre-HEAD evolution) with table axis +
orders adapter; FF-11 both names grep-0 with `:492/:506/:520`
absorption; FF-12 all four pin moves land; FF-13 endpoints re-pinned.
Fixers `ba9c2967`/`dfbea72b`/`999a1aab` all resolve as commits.

Defects: 8 member defects persist as rowed and ride (converters D1/D2
prose re-read against the MRO-outer walk + 4 production sites :581/
:1032/:1799/:420; definition D2 verbatim; finalizer D1/D2; relations D1
double-backtick parenthetical :150 with the kind-less non-sentinel
record; relay D1 :898-902; init D1 narrowed per FF-4), plus
testing-relay D1 persisting at the owner comments (base :139-151 still
say "three" against 4+helper / 3+helper — see O-6). 3 closed, 1
f43-retired, 1 spent — all confirmed. No new defect found: docstrings
re-read against bodies, guard families enumerated (6 loop-heads, LEAD/
TAIL sites, 4 `NodeIDAnnotationError` fallbacks, 9 recheck gates, 22
`except` arms — no missing member), layering holds (no reversed
imports; the walker lazy read is the single sanctioned exception).

Index rows T-1..T-17: transcription corrections CC-N: none. Every row's
files, counts, and triggers match the verified FR bodies (T-1 1+3 at
:336/:984/:1020; T-2 1+4 split 2+2; T-3 the five helpers; T-4 1+1 at
serializer :931/:1008; T-5 check + formatter + orders adapter; T-6 def
+ in-file callers; T-7..T-17 triggers verbatim against FR-1..FR-11).

Cells: sharded/pg inapplicable by construction — CONFIRMED. Sole
`.using()` (resolvers :471) propagates the row's own `related._state.db`
alias, never chooses one; zero database/alias/dialect tokens
folder-wide (every `connections` hit is GraphQL-connection prose or the
`relation_connections` record/synthesis identifiers).

Gates run in slot-3 (serialized, GREEN pressure, no competing suite):
`tests/types` 571 passed (`dry-20261010T061354-ce177f`); `tests/management/
test_inspect_django_type.py` 24 passed (`dry-20261010T061430-cd0b65`);
P1 leaf probe P1-PASS (`dry-20261010T061439-f77d01`, package inside the
copy). f44 triple, f41 gate pins, and f42 firing-row oracles confirmed
present in the witnessed files. Copy reported fresh on all three runs;
shared-tree move is the plan file only.

Verdict-neutral observations (no action owed): O-1 FC-7 leg cite
":541" — the composing call is :540, :541 is its `return`. O-2 FC-19
"skeleton :1629" — the `raise` is :1629, the formatter call :1630.
O-3 predictor span ":502-518" — the function runs :502-520 (walk return
:517-520; load-bearing walk line :518 correct). O-4 "relay.py:487" —
resolves in top-level `relay.py`, matching the owner's own "relay.py /
connection.py" shorthand (base :149-150); `types/relay.py:487` is a
comment. O-5 FC-21 "`_dst_`-prefixed def" — no such def exists; the
marker is the string constant at finalizer :490 (zero window-`to_attr`
constructions still holds). O-6 count gloss — 9 defects verified
persisting, 8 homed to this item's members; testing-relay D1 rides
under its own item per the folder-testing closeout, so "8 member
defects" is the homed-here count.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-base]: dry-file-types__base.md
[file-converters]: dry-file-types__converters.md
[file-definition]: dry-file-types__definition.md
[file-finalizer]: dry-file-types__finalizer.md
[file-init]: dry-file-types____init__.md
[file-relations]: dry-file-types__relations.md
[file-relay]: dry-file-types__relay.md
[file-resolvers]: dry-file-types__resolvers.md
[self]: dry-folder-types.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
