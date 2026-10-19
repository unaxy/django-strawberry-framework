# DRY review: `rest_framework/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights in slot-2 only). Audits the
unassigned remainder of the `rest_framework/` folder and the families that
cross its ownership boundaries at current bytes (HEAD `23b5f421` +
working tree). The six member file artifacts are run-6/run-7 era
inputs, not verdicts: every assignment below was re-derived fresh at
WT bytes, and every assignment the tree has falsified is flagged as a
finding inside this item for the closeout defect-homing pass. No prior
artifact is summarized and no row is reopened.

Verdict: zero-edit CONFIRM. 22 cross-file compositions hold by name
(FC-1..FC-22, each with a fresh census); the f35 consolidation holds
consolidated (owner + 2 call sites, zero residue); the three
already-rowed duplications persist exactly as rowed (f36 + f37 +
`mutation-discovery-own-snapshot-read`, all open+blocked — no new
row); 28 merges rejected with triggers (FR-1..FR-28, 6
folder-fresh, 22 converging on standing member rejections whose
bodies + triggers were re-read at current bytes); 14
tree-falsified prior assignments flagged for closeout (FF-1..FF-14,
rows not reopened); 0 FAM-N (the three load-bearing near-misses —
the relation-target peel pair, the identifier-gate pair, and the
KeyError-translation pair — re-traced fresh and held separate on
projection/posture/contract-surface evidence, FR-1 / FR-2 / FR-3);
0 new defects (resolvers D1+D2 and converter D1+D2 re-verified
persisting and riding to closeout; converter D3 closed by a landed
fix; converter D4 falsified at current bytes with evidence, no home
owed); 0 new Family-hold rows (no consolidation is blocked beyond
what the plan already rows). The 564-row `tests/rest_framework`
suite runs green in slot-2 at current bytes.

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da`.
`ITEM_BASELINE=08632975ba228a351553464683a366190aab3ce0`
(resolves as a commit; the item-scoped diff `ITEM_BASELINE` → WT
over the folder is empty, so BASE=WT pre-edit for every target).
Slot-2 (`dry/folder-rest-framework/consolidate`) verified
byte-identical to WT on all six targets before tracing and again
after the witness suite (the suite wrote no source). Blob
fingerprints are `git hash-object` (WT = BASE) and `git rev-parse
HEAD:<path>` (HEAD), short-8:

| File | Lines | WT = BASE | HEAD | State |
|---|---|---|---|---|
| `rest_framework/__init__.py` | 65 | `0fff4c42` | `0fff4c42` | clean |
| `rest_framework/hook_context.py` | 55 | `c2d2df8a` | `c2d2df8a` | clean |
| `rest_framework/inputs.py` | 1816 | `0e2638fd` | `b7f4a6ba` | dirty |
| `rest_framework/resolvers.py` | 2615 | `4d05a330` | `14ffc9c8` | dirty |
| `rest_framework/serializer_converter.py` | 1317 | `077a4ee2` | `e804b074` | dirty |
| `rest_framework/sets.py` | 1046 | `d3a16114` | `2ecaab56` | dirty |

Item-scoped diff (`ITEM_BASELINE` → WT over the folder): empty. This
item landed zero edits in slot-2 and zero in the shared tree; the
four dirty files' WT-vs-HEAD hunks are attributed below, none made
here.

## System trace

The folder owns the DRF-serializer write flavor end to end: the
soft-dependency guard leaf (`__init__.py`: install hint, thin
guard, import-time posture), the frozen hook surface
(`hook_context.py`: the two records), the leaf converter
(`serializer_converter.py`: scalar registry + MRO dispatch,
relation/file/list/nested prechecks, naming rule, description
synthesis, source-axis owner, backing-column resolve, strict
primary policy, serializer-only relation routing, conflict policy,
choice-enum upgrade, dual-routing seam), the input namespace
(`inputs.py`: module-path constant, namespace lifecycle, nested
opt-in machinery, discovery default, drift fingerprint, writable
basis + ownership detection + raise, narrowing, injected specs,
descriptor identity + naming, required guard, collision
collection, per-field walk, recursion guards, builders, caches),
the declaration surface (`sets.py`: Meta matrix, schema-map
validation, nested validation, ownership walk, discovery hook,
namespace binding, input seams, construction-hook defaults,
resolver seams), and the runtime pipeline (`resolvers.py`:
decode coloring + recursion, error flattener, hook views,
injection merge, constructor merge, agreement guards, queryset
scoping + pinning, intent ledger + walk, attestation, write
witness, saved-result validation, skeleton adapters). Data flows
declaration → schema-time build → bind → decode → construct →
validate → write → attest → re-fetch. Every cross-folder seam
(write skeleton, boundary, decode spine, visibility query, error
leaf + key maps + mappers, input-namespace quartet, shape-build
spine, naming spine, kind vocabulary, string helpers, converter
skeleton, read-side converters, relation annotators, queryset
pinners + guards, permission helpers, clear bus, lazy-export
table) is owned outside and composed by name.

Member-file inputs re-derived at current bytes (not inherited):
[file-init][file-init], [file-hook][file-hook],
[file-inputs][file-inputs], [file-resolvers][file-resolvers],
[file-converter][file-converter], [file-sets][file-sets]. Where
the tree falsified an assignment the record sits under Findings
as FF (flag for closeout; no row reopened, nothing re-applied).
Run-6/run-7 blobs (`45cf7b63`, `f4910159`, `9b17d952`,
`8024703e`, `6652d092`, `2c4c4930`) all resolve in the object
store and were diffed against WT to separate committed
evolution from concurrent dirt.

### Attribution of the working-tree dirt (by diff content vs HEAD)

Two provenances. The `## Owned changes` ledger names two
`rest_framework/` paths (run-10 f35, verified, uncommitted):
exactly four WT-vs-HEAD hunks match those ledger rows by content
(the `normalize_serializer_source` owner def + docstring home
clauses, the two call-site compositions, the owner import) and
are DRY-owned concurrent work. Every other WT-vs-HEAD hunk is
the concurrent bug-hunt `truth.*` identity-read migration
(import swaps, `_safe_*` → `truth.*`, `getattr` →
`truth.static_attr`, `__name__` → `truth.name`, `except`
narrowings, new hunt-owned helpers, prose) — external by
content. Never edited, reverted, or tidied here; the two clean
files carry zero dirt.

- `inputs.py` (32 `@@` hunks): 2 f35 ledger hunks (owner
  import; `_resolve_nested_field` call site) + 30 hunt hunks
  (module-docstring guard prose; `truth` import;
  `NESTED_STABLE_FIELDS_INSTRUCTION` deletion with its text
  inlined; `get_serializer_for_schema` + `read_nested_serializer_fields`
  `except`-narrowing; `_fingerprint_nested` composing the
  shared reader; `_default_full_shape_identity` probe split;
  label/name/render migrations).
- `resolvers.py` (45 `@@` hunks): 0 ledger hunks — all 45
  hunt (`truth` import; read migrations; `except`
  narrowings; new `_is_one_of` / `_is_frozen_container` /
  `_model_name_repr` helpers; `_upload_metadata` reshape;
  `_hook_mapping` materialize direct).
- `serializer_converter.py` (24 `@@` hunks): 2 f35 ledger
  hunks (owner def + docstring; `resolve_serializer_field`
  call site) + 22 hunt hunks (`truth`/`types`/`typing`/
  `ValidationError` imports; read migrations; wrap removal
  in `_finish_serializer_conversion`; description-guard
  removal; `_scalar_name` rewrite; `to_python` narrowing;
  docstring prose).
- `sets.py` (18 `@@` hunks): 0 ledger hunks — all 18 hunt
  (`keyword`/`truth` imports; identifier gate added to
  `_validate_schema_field_map`; entry-shape checks; read
  migrations; own-namespace reads).

`utils/truth.py` itself exists on disk but is untracked and
absent from HEAD; the migration is unlanded by definition.

## Verification

### Matrix

1. Cross-flavor: every form/model twin re-read fresh at current
   bytes (converter table + fallthrough + triple + model-less
   relation + basis + narrowing + guard + discovery + decode
   spine + construction default + hooks + name deriver +
   own-snapshot default + identifier gate + operation
   vocabulary). The serializer side composes shared owners by
   name and declares per-flavor adapters; all twin
   separations re-derive with unmet triggers (FR-7..FR-28),
   except FF-5 (the hook-annotation posture
   moved the committed tree's way) and FF-14 (a maintainer-routed
   asymmetry the WT hunt dirt now addresses — ruling still
   owed). The `truth.*` read idiom is hunt-owned migration
   vocabulary, not a package rule. Discharged.
2. Sync/async: the folder carries zero `async def` and zero
   `await` tokens (re-grepped; `async` appears only in
   prose/docstrings/comments). No twinship: both resolver
   entries come from the one shared factory over the one sync
   body (FC-18). Discharged.
3. Derived knowledge: every same-token population in the
   folder was walked on body strength. Genuine single owners
   with by-name composers: the install hint (1 wrapper + 1
   import-time call + root call), the guard (4 DRF-importing
   submodules rely-via-order + root call), the hook records (1
   producer each + 3 call sites + 3 defaults + root rows), the
   source-axis fold (2 call sites), the nested `.fields` read
   (3 consumers), the discovery default (2 internal + 1
   override delegate), the fingerprint (2 windows), the
   writable basis (4 consumers), the runtime-fields read (2
   consumers), the ownership raise (2 walkers), the narrowing
   (6 call sites), the injected specs (1 consumer), the
   nested-config validators (2 callers each), the recursion
   guard (2 walkers), the builders + dedupe + materialize
   (FC-10), the dispatch seam (3 converter-internal + 3
   cross-file callers), the naming rule (3 internal
   branches), the choice-enum builder + cache, the
   hook-mapping gate (3 call sites), the freeze view (2
   consumers), the write-surface list (7 walkers), the
   provisional-name owner (5 calls + 1 restatement — f36),
   the module-path constant (1 binding), the kind
   vocabulary (re-export + pair). The peel pair (FR-1), the
   identifier-gate pair (FR-2), the KeyError-translation
   pair (FR-3), the effective-source reads (FR-4), and the
   operation comparisons (FR-5) are distinct contracts or
   consumer spellings with triggers. Discharged.
4. Round-trip: emit halves compose one build spine
   (provisional naming during the walk, final naming after —
   f36 R1 stands); the agreement guard's recompute-and-compare
   is a deliberate round-trip check, not a second producer
   (FR-12/J12); materialize idempotency + collision raise are
   one directional pin at the quartet owner; the
   decode is encode-only (nothing re-encodes serializer data
   back to GraphQL input); the hook
   freeze has no inverse by design (a descriptor must never
   reconstruct the stateful value). Discharged.
5. Other media: package oracles (`tests/rest_framework/`, 6
   modules, 564 rows, all green in slot-2 at current bytes,
   `dry-20261010T045957-ed746a`; the import ratchet pins 19
   identity bindings + 2 shared bodies), live `/graphql`
   rows (the library/products mutation suites pin wire
   behavior), projections (module/class/method docstrings;
   the four persisting member D1s/D2s ride to closeout per
   `## Defects` and are never fixed here). No medium carries
   a second definition of a folder rule. Discharged.
6. Omission: all six files enumerated below; every member
   lands in a verified family row, a member-artifact
   assignment re-verified at current bytes, or one of this
   item's transcribed rows. No unassigned member remains.
   Discharged.

### Enumeration

Instrument: `ast` top-level census (`len(ast.Module.body)`,
def / class / assign split) over the folder at WT bytes, plus
`grep` composer censuses for every cross-file read. Every
member below lands in a verified family row (f-numbered), a
member assignment re-verified at current bytes, or one of
this item's transcribed rows (T-numbers in `## Index rows for
Worker-0`).

| File | Top-level members | Homes |
|---|---|---|
| `__init__.py` | 8 stmts, 1 def, 1 annassign | F1/F2/F3 converge (hint / guard family / posture) + J1/J2/J4/J5/J6 stand (FF-4 refreshes the J3 cite) |
| `hook_context.py` | 5 stmts, 2 classes | F1/F2 converge (records) + R1/R2/R3/R4/R6/R7/R8 stand; R5 stands (FR-14); FF-6 refreshes the pk cite |
| `inputs.py` | 68 stmts, 39 defs, 2 classes | F-PATH/F-NS/F-ENRICH/F-SHAPE/F-DISC/F-FP/F-WRITE/F-NARROW/F-INJ/F-WALK/F-NEST converge (FF-10 notes hunt body evolutions, verdicts intact) + FAM-SRC consolidated (f35, FC-3) + R-path/R-mutid/R-disc/R-narrow/R-stamp/R-walk/R-coll/R-guard/R-nestname/R-partial/R-split/R-nonorm stand; F-BUILD subject deleted (FF-1); R-fpread subject hunt-deleted (FF-3); remap basis stale (FF-13) |
| `resolvers.py` | 98 stmts, 50 defs, 1 class | C1..C12 converge (skeleton/factory/boundary/envelope/recourse/visibility/ownership/nested/taxonomy/seal/guard/hardening/hook-production) + R1..R22 converge (FF-11 refreshes the R22 cite) + J1..J5/J7..J19 stand (J6 subject deleted, FF-2); FAM-NEW persists open+blocked (f36, FC-20) |
| `serializer_converter.py` | 77 stmts, 36 defs, 1 class | F-TABLE/F-REG/F-DISPATCH/F-FAILLOUD/F-NESTED/F-REL-GATE/F-LIST/F-EXTBOUND/F-NAME/F-DESC/F-SOURCE-GUARD/F-BACKING/F-PRIMARY/F-SERONLY-REL/F-CONFLICT/F-CHOICE-ENUM/F-RESOLVE/F-SHAPE/F-KINDS converge (FF-10 notes hunt body evolutions, verdicts intact) + FAM-SRC adopted (f35) + FAM-ENUM persists open+blocked (f37, FC-12); R-EXCEPT subject hunt-deleted (FF-9) |
| `sets.py` | 26 stmts, 5 defs, 1 class (+ 14 class-body members) | F-KEYS/F-SCHEMAMAP/F-DET/F-SHAPETAIL/F-WRITEMAP/F-NESTVAL/F-OWNWALK/F-MATRIX/F-RESOLVEMODEL/F-HOOK/F-NS/F-SLOTS/F-BUILD/F-NAME/F-HOOKS/F-SEAMS/F-MECH converge (FF-5 overturns the F-HOOKS untyped-seam verdict — committed) + FAM-OWN persists blocked (mutation-discovery family) + 13 rejections stand; 2 the maintainer-routed rows persist (FF-14 notes one's tree-state change) |

### Challenges

Authoritative definitions only; consumers, oracles and projections
that also move are listed, never counted. Current bytes.

- C1 hint wording/floor → 1 here (oracles/config/contract
  source follow by role).
- C2 primitive shape / new dep / memoization → 1 at the
  primitive / 1 new wrapper / 1 here (the member's
  primitive/wrapper triple, unchanged).
- C3 leaf manifest / hook / floor const → 0 here (J4/J5/J6
  stand; any eager binding breaks the posture).
- C4 hook-context field set / upload triple / frozen
  posture → 1 here each (sole producers follow as
  consumers).
- C5 `operation` typing → 1 today (unvalidated carrier;
  typing would CREATE a second spelling — R2).
- C6 source-axis fold (falsy/equal/default-vs-renamed) → 1
  (the f35 owner; 2 call sites follow; effective-source
  reads untouched — FR-4).
- C7 one-segment detection → 1 (the guard; 2 callers
  follow with their nouns).
- C8 nested `.fields` read (KeyError translation, stable
  contract) → 1 (3 consumers follow); discovery-default
  translation → 1 (separate contract — FR-3).
- C9 fingerprint axis (new SDL-affecting axis, nested
  gating, cycle marker) → 1 (the recursive core; 2
  windows follow).
- C10 writable basis / runtime-fields read / star-vs-
  collision detection / raise wording → 1 each here (4 +
  2 + 2 consumers follow).
- C11 narrowing spine / unknown-noun / empty message →
  1 (the shared spine; 6 call sites follow with knobs).
- C12 injected-specs provisional / agreement contract →
  1 (sole consumer follows).
- C13 required-guard drop rule / wording → 1 (the shared
  spine + own wording; sole declaration consumer).
- C14 collision arms (attr / GraphQL / source) → 1 (the
  shared walker; collect-vs-raise stays per flavor).
- C15 walk (requiredness / nullability / triples /
  aggregation) → 1 (canonical-gate re-walk follows).
- C16 nested recursion (cycle / depth / config keys /
  per-level validation) → 1 each (2 walkers follow).
- C17 builder (shape identity / canonical gate / naming)
  → 1 (top-level + recursive callers follow); dual
  builder → 0 (deleted — FF-1).
- C18 dedupe / materialize / namespace lifecycle → 1
  each (the quartet owner; 2 + 2 + 3 composers follow).
- C19 dispatch order / registry / fallthrough / nested
  default / relation gate / list recursion / extension
  boundary → 1 each here (converters follow).
- C20 GraphQL naming (suffix rule / multi plain) → 1
  (3 internal branches follow).
- C21 description synthesis → 1 (2 consumers follow;
  guard removed by hunt — FF-9).
- C22 backing resolve / primary policy / serializer-only
  routing / conflict policy → 1 each here (model-less
  twin untouched — FR-17).
- C23 choice-enum upgrade (members / BLANK / cache /
  collision) → 1 (2 annotation paths follow); name
  template → 2 (f37 persists blocked).
- C24 dual-routing seam (nested-first, column-vs-
  column-less, spec record) → 1 (3 callers follow).
- C25 decode (scalar leaf / relation pk / nested
  recursion / file-into-data) → 1 per handler (spine
  + colorings follow).
- C26 flattener (path join / re-key / budget / cycle) →
  1 (2 failure paths follow); freezer merge → split
  stands (FR-10).
- C27 hook-mapping gate / freeze / injection exact-match
  / constructor merge / save-kwarg guards → 1 each (3 +
  2 + 1 + 1 + 1 consumers follow).
- C28 agreement (presence / source / kind / relation /
  nested / requiredness / annotation) → 1 per guard
  (write-surface walk follows); provisional input → 2
  (f36 persists blocked).
- C29 scope / pin / ledger / walk / snapshot / attest /
  witness / saved-result → 1 each (pipeline follows).
- C30 write-step order / savepoint / three-branch mapper
  / decode step / entries / seams → 1 each (skeleton +
  factories follow).
- C31 Meta matrix (keys / gates / narrowing / hooks /
  snapshot) → 1 (bind + name seams follow).
- C32 own-snapshot read order → 2 (mutation-discovery
  family persists blocked).
- C33 hook-context annotation → the record (typed
  composition; untyped-seam verdict overturned — FF-5).
- C34 identifier rule (sets gate vs forms gate) →
  separation stands (postures differ — FR-2).
- C35 relation-target peel (fingerprint vs agreement) →
  separation stands (projections differ — FR-1).

## Findings

### Compositions (each holds by name at current bytes)

Guard leaf and hook surface. FC-1 guard: the hint lives once
(`__init__.py:33`); the wrapper delegates (one call, re-read);
the import-time call + the root `__getattr__` call are the
exactly-2 production `require_drf(` sites (re-censused; every
other hit is prose); no submodule calls it (re-grepped: the
one submodule hit is docstring prose). The root table still
routes 7 DRF names (re-read). FC-2 records: `SerializerHookContext`
has exactly 1 production construction site
(`resolvers.py:2331`, re-censused) and `UploadMetadata`
exactly 1 (`resolvers.py:663`); the 3 hook call sites forward
the context; the 3 sets defaults now TYPE their context
parameter (FF-5); the root routes both names lazily.

Source axis and nested reads. FC-3 fold: the f35 owner
(`serializer_converter.py:731`, ledger-owned) with its 2
call sites composing by name (`serializer_converter.py:1228`,
`inputs.py:1523`, re-censused); zero residue spellings
package-wide (the fold's one spelling lives only in the
owner body). FC-4 nested read: `read_nested_serializer_fields`
serves 3 consumers (input build, fingerprint, schema
ownership walk — re-censused, incl. the hunt-added
fingerprint composition); the deleted instruction constant
(FF-3) leaves the message single-sited in the reader. FC-5
discovery: the module default serves 2 internal call sites +
the classmethod override delegates to it (re-censused); the
override's own-snapshot read persists (mutation-discovery
family, blocked).

Fingerprint and ownership. FC-6 fingerprint: 2 windows (class
validation + bind check, re-censused) compose the one
recursive core; the nested arm composes FC-4. FC-7 writable
basis: `writable_serializer_fields` serves 4 consumers,
`runtime_validated_data_fields` 2, and the one raise serves
both ownership walkers (all re-censused); star/collision
detection stays internal to the raise.

Narrowing and nested opt-in. FC-8 narrowing: 6 call sites
compose the shared spine with serializer knobs
(re-censused); `resolve_optional_fields` serves 2 (class
validation + build). FC-9 opt-in: the config record +
normalizer (1 external caller + self-recursion) +
`require_*` pair (2 callers each) + per-level key
validation (2 callers) + recursion guard (2 walkers) — all
re-censused; the sets class-creation validation and the
inputs per-level validation share the `require_*` helpers
(FR-8 keeps the validators split).

Build and dispatch. FC-10 build: the single builder serves
the sets shape helper + the recursive nested build; dedupe
serves 2 (nested + top-level); materialize serves 1 direct
call + the promoted stash callback (all re-censused); 3 bus
rows registered (input namespace, shape cache, choice
enums). FC-11 dispatch: `convert_serializer_field` serves
3 converter-internal callers (list child, model-backed,
dual-routing seam); `resolve_serializer_field` serves 3
(build walk, injected specs, agreement recompute);
backing-resolve, naming, primary, serializer-only routing
are internal-only (re-censused, zero external callers).
FC-12 choice enum: the builder + name-keyed cache + clear
row serve both annotation paths (re-read); the name
template stays count-2 (f37 persists blocked — model-side
line inside hunk `@@ -944,32 +929,15` of
`types/converters.py`).

Decode and errors. FC-13 decode: the input-object decoder
recurses via the nested handler; both relation decoders
color the shared spine; the nested-spec accessor serves 7
call sites (re-censused). FC-14 errors: the recursive flattener
serves 2 failure paths (validate + DRF-detail,
re-censused); both terminate in the shared leaf; key maps
come from the shared builder (the deleted reverse-map
builder's successor — FF-2) + the save-time map.

Hooks and agreement. FC-15 hooks: the mapping gate serves
all 3 hook call sites; the freeze view serves 2 consumers
(constructor merge + shared frozen data); injection
exact-match, constructor merge, and both save-kwarg guards
are single-owned (all re-censused). FC-16 agreement: the
write-surface list serves 7 walkers (re-censused); field /
relation / nested guards compose it; the runtime
ownership walk composes FC-7; the annotation recompute
composes FC-11 under the f36 provisional (blocked).

Pipeline tail and seams. FC-17 tail: scope (1 top call +
recursion), validator pinning, ledger (record/consume/
assert), intent walk + manifest, M2M snapshot, attestation,
witness, saved-result check — each single-owned, composed
in pipeline order (re-read). FC-18 skeleton: the
decode/write adapters ride the shared skeleton; both
entries come from the one entry factory; both seams from
the one seam factory (function-local import preserved).

Namespace and vocabulary. FC-19 lifecycle: the quartet
unpack + one-line wrappers + 2 bus rows hold (re-read);
the ratchet pins 19 identity bindings + 2 shared bodies
(green in the witness). FC-20 provisional: the owner
serves 5 composing calls (4 here + the name-set spine,
re-censused); the guard f-string restates it (f36 persists
blocked — the guard line carries hunt dirt on its base
half, suffix half byte-identical). FC-21 module path: the
sets `ClassVar` binds the constant (1 binding, re-read).
FC-22 kinds: the 4 base kinds re-export the shared
vocabulary; the nested pair is declared here with the
recursion owned in `inputs.py` (ratchet-pinned).

### FAM verdict: none raised

Twenty-eight twin hypotheses were traced to a verdict; every
one resolves to single ownership, a standing rejection with
an unmet trigger, an already-rowed blocked duplication, or a
distinct contract (FR-1..FR-28). The three load-bearing
near-misses are FR-1 (the relation-target peel pair shares
the peel shape, but the fingerprint projects a label string
for schema-time tuples while the agreement returns the
model object for runtime identity comparison — different
projections, phases, and caller guarantees; a helper would
be machinery coupling the two), FR-2 (the identifier-gate
pair shares the rationale prose, but the sets gate
strict-rejects `str`-subclass keys under the exact-str
precedent while the forms gate copies-and-interrogates them
— different accepted sets on a real input class, so
unifying changes behavior; the shared core is stdlib idiom),
and FR-3 (the KeyError-translation pair shares the trigger
shape, but the nested read names the opt-in contract while
discovery names the override contract — different contract
surfaces; a helper parameterizing the whole message is
machinery). The f36, f37, and mutation-discovery count-2
verdicts persist but are already rowed open+blocked, so no
new Family-hold row is owed: no consolidation is blocked
beyond what the plan already rows.

### Rejections (each re-derived fresh; triggers re-checked)

Folder-fresh:

- FR-1 relation-target reads: the fingerprint label
  projection (schema tuples) vs the agreement
  model-object return (runtime identity) share the DRF
  peel shape but differ in projection, phase, and
  caller guarantees; a third spelling lives in forms
  without the peel; the taxonomy reads
  (`utils/relations.py::classify_path`, re-read)
  classify ORM string paths — a different subject and
  question. Trigger: a third DRF peel site or the peel
  gaining logic.
- FR-2 identifier-gate pair: strict-exact (sets) vs
  copy-and-interrogate (forms) on `str`-subclass keys;
  shared core is stdlib idiom. Trigger: one shared key
  posture plus a package name grammar.
- FR-3 KeyError-translation pair: nested-opt-in contract
  vs default-discovery contract; shared trigger shape
  only (both sides hunt-dirty). Trigger: the messages
  converging on one contract text.
- FR-4 effective-source reads vs the f35 fold: reads
  answer "which attribute" (`spec.source or target`, 7
  read sites re-censused) and never fold; the fold records.
  Trigger: the f35 docstring's own (a consumer needing
  the default-vs-renamed distinction).
- FR-5 operation comparisons: `== CREATE` (sets) vs raw
  `"create"`/`"update"` (resolvers) vs `== PARTIAL`
  (inputs) are vocabulary consumers, never definitions;
  spelling unification relieves no change obligation. No
  trigger (needs a second vocabulary definition).
- FR-6 guard `-> ModuleType` annotations ×4: annotations,
  not definitions; all four moved together by committed
  evolution. Trigger: a shared lazy-export/guard protocol
  (the refreshed J3 trigger).

Member-twin re-verifications (each body re-read fresh):

- FR-7 ownership walks (CONVERGE sets row): schema
  recursion over the config tree vs runtime recursion
  over data+specs; shared raise composed. Trigger: one
  walker over one tree.
- FR-8 nested-validation pair (CONVERGE sets row):
  class-creation schema-map check + write-method
  override vs per-level effective-set check; shared
  `require_*` helpers composed. Trigger: single-phase
  validation.
- FR-9 cycle walkers (CONVERGE J3): budget+active-set
  flattener vs memo+active-set freezer; different
  termination contracts. Trigger: one traversal
  mechanism need.
- FR-10 None arms (CONVERGE J2): per-kind None semantics
  (skip / passthrough / clear / empty-dict); 5 sites
  re-read. Trigger: one None policy.
- FR-11 nested-structure walks (CONVERGE J1): 6 surviving
  walks with per-walk contracts (the 7th member deleted
  — FF-2). Trigger: one nested-walk driver.
- FR-12 annotation recompute (CONVERGE J12): deliberate
  round-trip check, not a second producer (f36 R4).
  Trigger: the guard abandoning recompute-and-compare.
- FR-13 decode mirror (CONVERGE J13/J16/J17): shared
  spine with per-flavor colorings; batched multi here
  vs per-element multi in forms (body re-read);
  null-M2M policies per flavor. Trigger: one decode
  entry.
- FR-14 frozen-vs-live hooks (CONVERGE J14/R5): spec'd
  per-flavor contracts; forms still takes the live
  instance (signature re-read). Trigger: a spec
  unifying the hook signatures.
- FR-15 partial mechanisms (CONVERGE J15): framework
  partial injection vs form/model mechanisms. Trigger:
  one partial mechanism.
- FR-16 file routing (CONVERGE J18): DRF `data` vs form
  `files=`; deliberate contrast, shared factories.
  Trigger: one file channel.
- FR-17 model-less relation (CONVERGE F-SERONLY-REL):
  missing-primary RAISE + id-like-suffix naming here vs
  raw-pk FALLBACK + plain scheme in forms (both bodies
  re-read; the forms docstring states the contrast).
  Trigger: the flavors merging.
- FR-18 resolve-vs-triple (CONVERGE R-TRIPLE +
  R-BACKING): source axis + strict primary +
  nested-first here, source-keyed backing resolve
  (renames + dotted/star reject) vs name-keyed form
  resolve (reverse/GFK guards) — forms triple re-read.
  Trigger: the flavors merging.
- FR-19 converter twins (CONVERGE R-TABLES/R-EXT-HOOK/
  requiredness): DRF-keyed vs model-keyed vs form-keyed
  spaces stay separate; extension hooks mirror;
  requiredness is `field.required` here vs the form
  `form_field_required` decision (re-read). Trigger:
  one keyed table / one requiredness decision.
- FR-20 rejection grammars (CONVERGE fallthrough/code/
  branch rows): per-subject wordings (fallthroughs, DRF
  vs Django code readers, three save branches).
  Trigger: a shared grammar.
- FR-21 guard posture (CONVERGE init-J1/J2,
  resolvers-C10/J4): parent-init order covers all
  submodules (census: zero submodule calls); wrappers
  already share the primitive (f34); context-gate vs
  mapping-gate split stands. Trigger: a submodule
  reachable without the parent init.
- FR-22 leaf posture (CONVERGE init-J4/J5/J6): still no
  `__all__`, no `__getattr__` (exactly 2 module hooks
  package-wide, re-censused), single-sited hint.
  Triggers: hard-DRF / owned lazy names / second hint
  site.
- FR-23 hook-context separations (CONVERGE R1/R2/R3/R4/
  R6/R7/R8): pipeline interior still mutable (body
  re-read); operation still an unvalidated carrier;
  frozen idiom still stdlib; sibling records answer
  different questions; request helpers + traversal
  state disjoint; root routes by name. Triggers: as
  membered.
- FR-24 saved-result guards (CONVERGE J8/J9/J5/J10/
  J11): alias/pk/shadow/model-field/container/operation
  checks each guard a distinct seam the skeleton does
  not own. Trigger: the skeleton owning the seam.
- FR-25 declaration twins (CONVERGE slots/matrix/keys/
  namespace/naming/build/lock/discovery/write-method
  rows): base-blessed per-flavor slots, per-flavor
  matrices, the partial `build_and_stash_input` ride
  (re-read), no coarse constructor (re-grepped: zero
  defs), the operation-to-write-method map (not an
  operation vocabulary). Trigger: the flavors merging.
- FR-26 inputs-vs-forms twins (CONVERGE R-disc/R-narrow/
  R-guard/R-coll/R-partial/R-path/R-mutid/R-split/
  R-nestname/R-stamp/R-nonorm): lazy-`.fields` vs
  `base_fields` discovery; distinct writable bases;
  shared spines with own wordings; collect-aggregate vs
  raise-first; per-family paths; descriptor digest +
  owner call; module split; plain nested names; stamp
  separation; decode-only by design (no build
  normalizer — verified by full read). Triggers: as
  membered.
- FR-27 cache + classifier + sentinel rows (CONVERGE
  R-CACHE/cardinality/J19): name-keyed vs registry-
  keyed caches; refused classifier derivations;
  `EXCLUDED` still unreferenced in the folder
  (re-grepped). Triggers: as membered.
- FR-28 the maintainer-routed persistences: `serializer-operation-
  vocabulary` (no contract source; forms kinds + raw
  literals re-read) and `serializer-hook-invocation-
  typed-wrap` (no typed wrap; call sites re-read) both
  persist — rulings still owed. (`serializer-hook-key-
  identifier-gate` rides FF-14.)

### Falsifications (record-only; no row reopened, nothing re-applied)

- FF-1 dual builder deleted (committed `899cb35b`
  "delete test-only package code"): run-6
  `inputs.py:1778 build_serializer_inputs` is gone at
  HEAD and WT; tests carry a `_build_serializer_inputs`
  helper (44 call sites). The `serializer-dual-builder`
  row names a deleted subject → closeout retires it
  (the single builder + per-operation bind is the new
  shape; no new row — both are rowed).
- FF-2 `_build_reverse_map` deleted (committed
  `7517eab2`, the shared-key-map consolidation): run-6
  `resolvers.py:597` + its `:2175` call site are gone;
  error key mapping rides shared `build_error_key_map`
  (2 failure-path calls + `_save_time_error_key_map`,
  re-censused). The `build-reverse-map-vs-mutation-
  input-reverse-map` row names a deleted subject →
  closeout retires it; the `nested-structure-walk-
  unification` subject list drops to 6 (FR-11).
- FF-3 `NESTED_STABLE_FIELDS_INSTRUCTION` deleted in WT
  by hunt dirt (present at HEAD:301,329,498; zero
  production/test refs at WT): the `serializer-
  fingerprint-framings` row names a WT-deleted subject,
  and `_fingerprint_nested` gained its `FC-4`
  composition. Blocked-on-hunt: closeout retires/
  revises only after the hunt lands or is dropped.
- FF-4 `require_drf() -> Any` → `-> ModuleType`
  (committed; all four guards moved together —
  routers:239, sessions:118, toolbar:104, leaf:39
  re-read). The `rest-framework-guard-return-idiom`
  cite is stale; verdict intact (FR-6). Closeout
  refreshes the cite.
- FF-5 `hook_context: Any` → typed
  `hook_context: SerializerHookContext` (committed:
  HEAD sets.py:955,998,1022 + the TYPE_CHECKING
  import). The `serializer-hook-context-record-
  annotation` "keep untyped" verdict is OVERTURNED by
  committed evolution. Closeout revises the row to the
  typed posture (C33).
- FF-6 `instance_pk: Any` → `instance_pk: object`
  (committed; hook_context WT=HEAD). The F1 "Any-
  typed pk" cite is stale; carrier-choice verdict
  intact. Closeout refreshes the cite.
- FF-7 converter D3 CLOSED: the `allow_null` element
  widening is at HEAD bytes (function body re-read) →
  the closeout condition ("if that dirt lands") is
  satisfied; no home.
- FF-8 converter D4 does NOT reproduce at current
  bytes: an `allow_blank` choice field's `""` IS
  representable via the `BLANK` member (`include_blank`
  at converter:1140 + docstring :1120-1123, re-read),
  and over a model column the column-list check refuses
  `""`-admitting fields the column does not list. The
  hunt exclusion the observation conditioned on is
  absent from WT. No home owed.
- FF-9 `serializer-except-guard-vs-shared` subject
  deleted by hunt dirt: `serializer_field_description`
  is straight-line at WT:686-706 (the `try/except`
  removed). Verdict moot until the hunt lands.
  Closeout-conditional.
- FF-10 hunt body evolutions, verdicts intact (each
  body re-read; single ownership unchanged):
  `_finish_serializer_conversion` consumer-raise
  propagation; `_default_full_shape_identity` probe
  split; both discovery `except`-narrowings;
  `_validate_schema_field_map` + `_validate_serializer_
  nested_fields` entry-shape checks; `_scalar_name`
  rewrite; `_stored_choice_value` narrowing. Record
  only.
- FF-11 R22 cite stale ("import block, members 2–33"):
  the block is 29 `ImportFrom` + 7 `Import` at current
  bytes; totality re-verified by full read (every
  imported name referenced). Record only.
- FF-12 three new hunt-owned module members, each
  single-owned, never touched: `_is_one_of` /
  `_is_frozen_container` (resolvers:755,760),
  `_model_name_repr` (resolvers:1069). No rows (hunt
  owns them). Record only.
- FF-13 `serializer-spec-construction-vs-remap` basis
  note stale ("owner absent"): `relation_input_
  python_attr` exists at HEAD:571 + WT:571. Verdict
  stands (nested construction never remaps — kinds
  are never relations). Record only.
- FF-14 the maintainer-routed `serializer-hook-key-identifier-
  gate` tree state changed: WT now HAS the sets
  identifier gate (hunt dirt, sets.py:187-198); the
  committed tree still lacks it. the maintainer's ruling stays
  owed; the WT gate must not be read as the ruling.
  Record only.

## Defects

None found while tracing. Checks run: every hunt-evolved
member's docstring re-read against its body (nested-read
KeyError contract, discovery KeyError contract,
fingerprint reader composition, full-shape probe split,
description straight-line body, finish-conversion
propagation clause, scalar-name origin rule, stored-choice
narrowing, schema-map identifier + entry-shape gates,
nested-fields entry-shape gate, own-namespace reads,
upload-metadata sizing comment, hook-mapping iteration
clause, freeze real-class clause, `_is_one_of` /
`_is_frozen_container` / `_model_name_repr` one-liners) —
no contradiction; every guard family enumerated for
omission against its contract source (the 7 hook-context
production/consumption points, the 2 guard call sites
covering the 4 DRF-importing submodules, the 3 bus rows,
the write-surface walkers — no missing member); layering
claims hold
(sets imports inputs + converter at module scope with a
function-local resolver edge, inputs imports converter,
converter imports neither, hook_context imports nothing
beyond `dataclass` — no reversed import).

The four member D1/D2 defects re-verified persisting at
current bytes (record-only; each already rides to closeout
under its member item — no new homing): resolvers D1 (the
substitute-branch message still says "or pop" at
`resolvers.py:1936` while popping fails closed);
resolvers D2 (the FK attestation `.get(pk=saved.pk)` at
`resolvers.py:2061` still bare); converter D1 (the
`(spec-039 Decision 7 / )` dangling cite at
`serializer_converter.py:716-717`); converter D2 (the
`# #6` marker at `serializer_converter.py:1303`).
Converter D3 is CLOSED (FF-7) and converter D4 does not
reproduce (FF-8) — neither rides.

## Pending execution

No `proof:` owed (zero-edit: nothing to prove beyond the
green witness already run). `gate:` entries for the final
gate:

- `gate:` `uv run python scripts/workspace.py run
  dry/folder-rest-framework/verify-1 -- python -m pytest
  tests/rest_framework -q --no-cov -p no:cacheprovider` (re-run the
  564-row witness; ran green in slot-2 as
  `dry-20261010T045957-ed746a`).
- `gate:` the final gate's live `/graphql` suites carrying
  serializer-mutation rows (library/products create/update,
  nested writes, relation decode, visibility scoping,
  injected fields, save kwargs) — named by the gate, not
  re-run here.
- Cells `unverified` with inapplicability correctly NOT
  claimed: the pipeline threads real database aliases
  (pinned write alias, `using(alias)` reads, cross-alias
  guards) and issues ORM queries evaluated against the
  database, so sharded + pg reach is real; both cells
  await the maintainer's word.

## Judgment

The folder is at single ownership: 22 compositions hold by
name with fresh censuses, the f35 consolidation holds with
zero residue, the three already-rowed duplications persist
exactly as rowed (open+blocked), 28 twin hypotheses
resolve without a new second definition, and the witness
suite runs 564/564 green at current bytes. The folder-fresh
rejections transcribe below as T-1..T-6 for Worker-0 to
row. Zero edits, zero new defects, zero new blocked
consolidations.

## Index rows for Worker-0

One line per row; Worker-0 alone edits the plan. Holding
item for all: Folder integration `rest_framework/`.
Freshness: WT blobs in `## Pins and fingerprints` (BASE =
WT); HEAD troupes listed there for the four dirty files.
No tracked files changed (item-scoped diff empty; no
ledger rows); HEAD unmoved at `23b5f421`; slot-2
byte-identical re-verified after the witness suite; NO
`## Families` item (no new multi-definition rule — the
three blocked duplications are already rowed); no
`docs/dry/temp-tests/` scratch was created. No commit.

Rejections (folder-scope merges considered; each with trigger):

- T-1 `rest-relation-target-read-merge` (FR-1) —
  files `rest_framework/inputs.py`,
  `rest_framework/resolvers.py`, `forms/inputs.py`,
  `utils/relations.py` — rejected (label projection vs
  model-object return; forms spelling; taxonomy reads
  a different subject; trigger: third DRF peel site
  or peel logic).
- T-2 `rest-identifier-gate-merge` (FR-2) — files
  `rest_framework/sets.py`, `forms/inputs.py` —
  rejected (strict-exact vs copy-and-interrogate
  postures; shared core is stdlib idiom; trigger: one
  shared key posture plus a package name grammar).
- T-3 `rest-keyerror-translation-merge` (FR-3) — files
  `rest_framework/inputs.py` — rejected (nested-opt-in
  vs default-discovery contract surfaces; trigger: the
  messages converging on one contract text).
- T-4 `rest-effective-source-reads-vs-fold` (FR-4) —
  files `rest_framework/inputs.py`,
  `rest_framework/resolvers.py`,
  `rest_framework/serializer_converter.py` — rejected
  (reads answer "which attribute", fold records;
  trigger: the f35 docstring's own).
- T-5 `rest-operation-comparison-spellings` (FR-5) —
  files `rest_framework/inputs.py`,
  `rest_framework/resolvers.py`,
  `rest_framework/sets.py` — rejected (vocabulary
  consumers, never definitions; no trigger — needs a
  second vocabulary definition).
- T-6 `rest-guard-annotation-merge` (FR-6) — files
  `rest_framework/__init__.py`, `routers.py`,
  `auth/sessions.py`,
  `middleware/debug_toolbar.py` — rejected
  (annotations, not definitions; trigger: a shared
  lazy-export/guard protocol).

Closeout notes (not rows): FF-1 (retire
`serializer-dual-builder`); FF-2 (retire
`build-reverse-map-vs-mutation-input-reverse-map`,
refresh `nested-structure-walk-unification` to 6
subjects); FF-3 (conditional: retire/revise
`serializer-fingerprint-framings` only after the hunt
lands or is dropped); FF-4/FF-6 (refresh the cited
annotations); FF-5 (revise
`serializer-hook-context-record-annotation` to the
typed posture); FF-7 (close converter D3, no home);
FF-8 (converter D4 needs no home); FF-9 (conditional:
`serializer-except-guard-vs-shared` moot until the
hunt lands); FF-10/FF-11/FF-12/FF-13 (no plan change —
verdicts intact); FF-14 (the maintainer ruling still owed);
f36 + f37 + `mutation-discovery-own-snapshot-read`
persist open+blocked (no change); the four member
D1s/D2s ride (no new homing).

## Independent verification (Worker-2)

Verdict: verified. Zero-edit CONFIRM stands: the item
diff is empty, every pin/census I re-derived matches,
the witness suite re-runs 564/564 green in slot-3, the
three near-miss separations hold on body evidence, the
FF-5 overturn and the D3-closed / D4-falsified calls
are confirmed at current bytes, and my own sweep finds
no missed consolidation (no FAM-N owed). Two
record-precision corrections below (CC-1 substantive
but verdict-neutral, CC-2 minor) for Worker-0 to apply
at closeout transcription; neither reopens a verdict.

Sequencing disclosure: the dispatch brief required
reading the full artifact before anything, so I read
`## Findings` before tracing (deviation from the
findings-last order). Mitigation: every position below
was fixed by my own pins, greps, AST censuses, and
body reads first, then compared to W1's record; CC-1
and the CC-2 trigger gap were found by my own sweep,
not by re-reading W1.

### Pins, diff, enumeration (all re-derived)

- Blob pins: all six WT short-8 (`0fff4c42`,
  `c2d2df8a`, `0e2638fd`, `4d05a330`, `077a4ee2`,
  `d3a16114`) plus HEAD pins and line counts
  (65/55/1816/2615/1317/1046) reproduce exactly via
  `git hash-object` / `git rev-parse HEAD:<path>`.
- Item diff `08632975ba228a351553464683a366190aab3ce0`
  → WT over `django_strawberry_framework/`,
  `tests/`, `examples/`: empty. Zero-edit confirmed.
- AST census reproduces the enumeration table
  exactly: 8/1/1annassign, 5/2 classes, 68/39/2,
  98/50/1, 77/36/1, 26/5/1 + 14 class-body members.
- Slot-3 (`dry/folder-rest-framework/verify-1`)
  `git hash-object` on all six targets matches WT:
  the copy is byte-identical; verification ran at
  current bytes.
- Matrix axis 2: zero `async def` / `await` code
  tokens in the folder (the one `async def` hit is
  a comment; `async` counts 0/0/0/13/0/5, all
  prose). Inapplicability-by-absence holds.

### Witness gate (re-run in slot-3)

- `workspace.py run dry/folder-rest-framework/verify-1
  -- python -m pytest tests/rest_framework -q
  --no-cov -p no:cacheprovider` →
  `dry-20261010T051835-84a99c`, 564 passed, exit 0.
- Sharded/pg cells: correctly left `unverified`
  with inapplicability NOT claimed. The pipeline
  threads a real pinned write alias
  (`context["write_alias"]`), pins author
  querysets to it, and evaluates ORM reads
  (`using(alias)` paths, FK attestation
  `.get(pk=...)`), so both cells have real reach
  and await the maintainer's word. Judgment: correct.

### Compositions (census spot-checks, my own greps)

- FC-1: exactly 2 production `require_drf(` call
  sites (root `__init__.py:145` inside
  `__getattr__`, leaf `:65` import-time); every
  other hit is docstring prose; root table routes
  exactly 7 DRF names. Holds.
- FC-2: exactly 1 production construction site
  per hook record (`resolvers.py:663`,
  `:2331`). Holds.
- FC-3/f35: owner `serializer_converter.py:731`
  + import + 2 call sites (`:1228`,
  `inputs.py:1523`) + oracle tests; the fold
  spelling (`field.source != field_name`) occurs
  package-wide only in the owner body; the
  `spec.source or target` reads answer "which
  attribute" (FR-4), never fold. Zero residue
  holds.
- FC-4: 3 `read_nested_serializer_fields` call
  sites (`sets.py:436`, `inputs.py:490`,
  `:1524`). FC-8: 6
  `resolve_effective_serializer_fields` calls +
  2 `resolve_optional_fields` calls. FC-13: 7
  `_nested_specs_of` calls. FC-16: 7
  `_write_surface_specs` walkers. FC-20: 5
  `generated_input_type_name` calls (4 + the
  name-set spine). All hold.
- f36 persists count-2: guard f-string
  (`resolvers.py:1290`) restates the owner's
  full-shape `<Base><suffix>` branch; the suffix
  ternary occurs package-wide only there.
  f37 persists count-2: `...}Enum"` occurs
  package-wide only at `serializer_converter.py:
  1133` and `types/converters.py:938` (+ its
  docstring). No third site in either family.

### Near-miss pairs (both sides read fresh)

- FR-1: `_fingerprint_relation_target`
  (`inputs.py:397`) returns `truth.label(model)`
  (a string for schema-time tuples);
  `_relation_model_of` (`resolvers.py:1074`)
  returns the model object for runtime identity
  comparison. Same peel shape; different
  projection, phase, and caller guarantees. A
  shared helper would couple schema fingerprint
  to runtime attestation = machinery.
  Separation holds.
- FR-2: sets gate (`sets.py:180-186`, WT hunt
  dirt) strict-rejects with `type(...) is not
  str`; forms gate (`forms/inputs.py:254-261`)
  accepts subclasses via `truth.is_instance`
  and interrogates a `truth.text` copy.
  Different accepted sets on a real input
  class (`str` subclass); unifying changes
  behavior. Separation holds.
- FR-3: nested read (`inputs.py:298-329`) names
  the opt-in contract; discovery default
  (`:365-395`) names the default-discovery
  contract; shared trigger shape only. A helper
  parameterizing the whole message = machinery.
  Separation holds.

### Falsifications (committed vs WT provenance)

- FF-1: `build_serializer_inputs` absent at
  HEAD (0 refs); `899cb35b` message matches
  ("delete test-only package code"); test
  helper has exactly 44 call sites (51 lines
  minus def, comment, docstring, 3
  `test_build_...` name lines). Holds.
- FF-2: `_build_reverse_map` absent at HEAD
  (0 refs). Holds.
- FF-3: constant at HEAD `:301,:329,:498`,
  zero production/test refs at WT. WT-deletion
  holds; blocked-on-hunt qualifier correct.
- FF-4: `-> ModuleType` at the four cited WT
  lines; all four committed at HEAD (routers
  `:234`, sessions `:122`, toolbar `:103`,
  leaf clean). Holds.
- FF-5: `hook_context: SerializerHookContext`
  at HEAD `sets.py:955,998,1022` + the
  `TYPE_CHECKING` import at `:124`. The
  committed tree types the seam, so the member
  "keep untyped" verdict is genuinely
  OVERTURNED by evolution. Holds.
- FF-6: `instance_pk: object` (`hook_context.
  py:40`, clean file). Holds.
- FF-7: HEAD `_list_child_conversion` body
  contains the `if child.allow_null:
  element = ... | None` widening + docstring
  paragraph. The closeout condition ("if that
  dirt lands") is satisfied at HEAD. D3 closed,
  no home. Holds.
- FF-8: `include_blank=field.allow_blank`
  reaches the shared enum builder in the body
  (`:1140`), so `""` is representable via
  `BLANK`; `_reject_choice_values_the_column_
  does_not_list` (`:907-963`) refuses
  over-column fields; WT `_is_enumerable_...`
  has no `allow_blank` exclusion. D4's premise
  is falsified at current bytes. No home owed.
  Holds.
- FF-9: HEAD `serializer_field_description`
  (lines 679-721) contains `try`; WT (674-706)
  is straight-line. Hunt deletion holds.
- FF-10: spot-checked bodies exist as
  described (`_scalar_name` `:877`,
  `_stored_choice_value` `:893`); verdicts
  intact. FF-11: 29 `ImportFrom` + 7 `Import`
  reproduced. FF-12: all three helpers exist
  at the cited lines. FF-14: WT gate at
  `sets.py:187-198` (hunt dirt: `truth.*`
  calls); HEAD has zero `identifier`
  occurrences. All hold.
- FF-13: DOES NOT HOLD as written — see CC-1.
- Dirt attribution: hunk counts 32/45/24/18
  reproduce; exactly 4 WT-vs-HEAD hunks carry
  f35 lines (matching the plan ledger rows);
  all other 115 hunks carry hunt content (I
  inspected the 11 without crude markers:
  `TypeIs` import, `_is_frozen_container`
  composition, `types`/`typing` imports,
  prose, except-narrowings, entry-shape
  checks). `utils/truth.py` is untracked and
  absent from HEAD. Holds.

### No consolidation owed (my own sweep)

- Suffix ternaries package-wide: 1 (the f36
  guard). Enum `<Type><Field>Enum` templates:
  2 (the f37 pair). `except KeyError` in the
  folder: 2 (the FR-3 pair).
- `isidentifier` third hit
  (`mutations/inputs.py:1136`) validates the
  public `object_slot` payload parameter
  (reserved-attrs contract) — a different
  subject and question from the hook-key
  gates, not a third FR-2 member.
- Peel-shape consumers beyond FR-1
  (`resolvers.py:1334` shape check consuming
  `_relation_model_of`; `:1472-1474` and
  `:1537` queryset-pinning peels) peel without
  reading the target model — different
  contracts (shape/pinning vs target
  identity), not third definitions. See CC-2
  for the trigger wording this sharpens.
- `EXCLUDED` occurs in the folder only in
  prose; exactly 2 module `__getattr__`
  package-wide (root + routers). FR-22/FR-27
  spot-checks hold.
- The four member D1/D2 lines persist
  verbatim at the cited lines; none is fixed
  here (correctly riding to closeout).
- Conclusion: 0 FAM-N, 0 new Family-hold
  rows, 0 new defects. No consolidation is
  blocked beyond the three already-rowed
  open+blocked duplications.

### Index rows T-1..T-6 (transcription check)

T-1..T-6 match FR-1..FR-6 on files,
rationale, and triggers, with two corrections:

- CC-1 (FF-13 + its closeout note; exact
  fix): `relation_input_python_attr` does NOT
  exist at HEAD — `git grep HEAD` over the
  package is empty, and every WT occurrence
  is a `+` line (hunt-added in
  `mutations/inputs.py`, WT `:571`; HEAD
  `:571` is an unrelated docstring line). The
  member row's basis note ("judged at HEAD
  bytes where the reverse-map owner is
  absent") is ACCURATE at committed bytes,
  not stale; the owner exists at WT bytes
  only via uncommitted hunt dirt. Rewrite
  the FF-13 bullet to: "owner exists at WT
  (`mutations/inputs.py:571`) only,
  hunt-added and uncommitted; absent from
  HEAD — member basis note accurate at
  committed bytes; verdict stands (nested
  construction never remaps)". The closeout
  consequence ("no plan change") is
  unchanged, now for the correct reason.
- CC-2 (T-1/FR-1 trigger; exact fix): the
  trigger "a third DRF peel site" already
  misfires on shape-only peel consumers that
  never read the target (`resolvers.py:
  1334`, `:1472-1474`, `:1537`). Reword to
  "a third relation-target read, or the
  peel gaining logic". Verdict unaffected.

### Gates and prose rules

- Gate re-run: witness suite 564/564 green
  in slot-3 (`dry-20261010T051835-84a99c`).
- `Pending execution` needs no `proof:` (zero
  edit); its `gate:` entries are correctly
  typed (witness re-run + gate-named live
  suites).
- Prose rules: no `feedback*.md` reference;
  `path:NN` cites are permitted (this
  artifact is a per-cycle scratchpad
  artifact); ruff gates are vacuous (zero
  source paths touched). No `docs/dry/
  temp-tests/` scratch was created; probes
  were read-only greps/AST.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-converter]: dry-file-rest_framework__serializer_converter.md
[file-hook]: dry-file-rest_framework__hook_context.md
[file-init]: dry-file-rest_framework____init__.md
[file-inputs]: dry-file-rest_framework__inputs.md
[file-resolvers]: dry-file-rest_framework__resolvers.md
[file-sets]: dry-file-rest_framework__sets.md
[self]: dry-folder-rest_framework.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
