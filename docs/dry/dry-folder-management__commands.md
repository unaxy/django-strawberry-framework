# DRY review: `management/commands/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Verdict: one consolidation CONFIRMED and implemented
(FAM-1 `_strawberry_field_type`, 2→1, proved + gated);
24 folder-local rules single-owned (FL-1..FL-4); 11
cross-boundary compositions hold at WT (FC-1..FC-11);
16 merges rejected with triggers (FR-1..FR-16, 7
re-derived file rejections + RJkeywalk superseded by
f42 + 8 folder-new + 1 posture split); 4
tree-falsified prior assignments flagged for closeout
homing (FF-1..FF-4, no row reopened, nothing
re-applied); the 2 pre-rowed open families touching
the folder stay blocked-on-hunt with zero edits here
(FC-3/FC-4). 0 defects (3 edges investigated and
released).

## Pins and fingerprints

HEAD `23b5f421` (detached, intended).
`ITEM_BASELINE=888135dc3beddbd8d357c386e9fd5ef7fea872e2`
(before copy in warm slot-1). Blobs are `git
hash-object` (WT), `git show HEAD:<path> | git
hash-object --stdin` (HEAD), `git show
ITEM_BASELINE:<path> | git hash-object --stdin`
(BASE), short-8, re-verified after the last edit.
BASE equals pre-edit WT on all four folder files, so
the item-scoped diff is exactly this item's two
edited files.

| File | WT | HEAD | BASE | Lines WT/HEAD |
|---|---|---|---|---|
| `commands/__init__.py` | `31cb58b8` | `31cb58b8` | `31cb58b8` | 1/1 |
| `commands/_imports.py` | `0b3faec4` | `0b3faec4` | `0b3faec4` | 59/59 |
| `commands/export_schema.py` | `112390ff` | `9c4fceee` | `112390ff` | 72/71 |
| `commands/inspect_django_type.py` | `86785d55` | `86a308ab` | `77eaff4f` | 692/686 |

Pre-edit WT was `77eaff4f` on inspect (BASE pins
it); the post-edit WT `86785d55` is FAM-1 (+18/-10).
`export_schema.py` WT `112390ff` is hunt-only dirt
(see Attribution); this item touched nothing there.
Connected owners and oracles fingerprinted
(WT/HEAD, short-8): `management/__init__.py`
`beb4e0ee`/`beb4e0ee` (clean), `registry.py`
`c5aa2050`/`47b52c52`, `types/base.py`
`f42bcee3`/`a63b7edf`, `types/converters.py`
`d8905d0a`/`38f102ab`, `types/definition.py`
`dfad92ca`/`2562cb6f`, `types/finalizer.py`
`8f699081`/`5934789a`, `scalars.py`
`072432e6`/`5837c6dc`, `utils/relations.py`
`cc68c6ba`/`63f46750`, `utils/imports.py`
`3ea52b16`/`3ea52b16` (clean), `utils/typing.py`
`b7e69600`/`3a5dae39`, `testing/relay.py`
`8a31c1ad`/`f94b3577`, `sets_mixins.py`
`616dbf20`/`dd358f85`, `utils/sessions.py`
`de3cf2c9`/`e3c7142b`, `middleware/request_body.py`
`7422cee9`/`e038bdd1`,
`tests/management/test_imports.py`
`a9e30ec8`/`a9e30ec8` (clean),
`tests/management/test_export_schema.py`
`d3e4a8e9`/`d3e4a8e9` (clean),
`tests/management/test_inspect_django_type.py`
`c609de91`/`e54a8dfa` (post-edit WT; pre-edit WT
`de2711e9`), `examples/fakeshop/tests/test_export_schema.py`
`3b6ef51d`/`3b6ef51d` (clean),
`examples/fakeshop/tests/test_inspect_django_type.py`
`8cbbc6cf`/`8cbbc6cf` (clean). Upstream reads:
`strawberry/types/base.py` (protocol
`WithStrawberryObjectDefinition`, `:207-211`) and
`strawberry/types/field.py` (`StrawberryField`
dataclass) in the workspace `.venv`
(strawberry-graphql resolved there, read-only).
Member-file inputs re-derived at current bytes,
never inherited: [file-init][file-init],
[file-imports][file-imports], [file-export][file-export],
[file-inspect][file-inspect]. Family inputs:
[rule-mro][rule-mro], [rule-relay][rule-relay].
Rejection inputs: [file-testing-relay][file-testing-relay],
[file-types-definition][file-types-definition],
[file-types-finalizer][file-types-finalizer],
[file-utils-imports][file-utils-imports],
[file-utils-relations][file-utils-relations],
[file-utils-typing][file-utils-typing].

## System trace

The folder owns the CLI surface end to end:
`__init__.py` (1-line command-inventory marker),
`_imports.py` (CLI import-failure translation: the
`(ImportError, AttributeError)` → `CommandError`
core, absolute-path shape validation, the Strawberry
selector entry + the Django dotted-path entry),
`export_schema.py` (selector → SDL → stdout/`--path`,
7 `Command` rules), `inspect_django_type.py`
(type-name → per-field resolution table, 12 command
rules + the FAM-1 lookup). Data flows argparse →
shim import → gate → render. Every cross-folder seam
(selector/dotted grammars upstream, registry map,
relay-shape predicate, converter maps, scalar maps,
relation vocabulary + synthesis record, override
sets + sentinel, name-converter rule, truth reads)
is owned outside and composed by name; the folder
owns no cross-folder definition. The Responsibility
index holds zero rows with a `File
management/commands/*` holding item (verified: the
file items' rows were never transcribed, FF-2), so
all 24 folder-local rules below are unassigned
remainder, named as new rows for Worker-0.
Cross-boundary rows holding folder members were
checked at current bytes; convergences and
rejections stand except where flagged FF.

### Attribution of the working-tree dirt (by diff content vs HEAD)

- `commands/__init__.py`, `commands/_imports.py`:
  clean (WT = HEAD). `_imports.py` HEAD
  `0b3faec4` postdates its file artifact
  (`05e9de80`): one committed hunk, lambda →
  named `_import` def with the django-stubs-Any
  comment (Any-avoidance, behavior-preserving).
- `commands/export_schema.py` (WT `112390ff` vs
  HEAD `9c4fceee`): 2 hunks, both truth migration
  (`truth` import + `truth.kind` in the
  schema-location guard message). Concurrent work,
  untouched.
- `commands/inspect_django_type.py` (WT vs HEAD):
  13 hunk headers, all truth migration
  (`truth.is_subclass` / `truth.static_attr` /
  `truth.name` / `truth.label` / `truth.mro` /
  `truth.class_dict` / `truth.is_type` /
  `truth.text` + casts + `truth` import + the
  `_model_name` helper + `StrawberryType`
  TYPE_CHECKING import) plus one docstring
  citation-path reword on `_is_suppressed_relay_pk`.
  Concurrent work, untouched. Committed HEAD drift
  since the run-7 re-trace (`2807d0fc` →
  `86a308ab`): typing hardening (annotations,
  casts, TYPE_CHECKING block, `@override`) + the
  `forward ForeignObject` label arm in
  `_relation_row` (new display rule, audited in
  FL-4/F6).
- No `## Owned changes` row covers either dirty
  folder file except the run-3 adopted-orphan rows
  (a docstring citation fix on inspect beside a
  REVERTED consumer half; the mirror-gate test
  dirt). Every hunt hunk above matches the brief's
  concurrent-work shapes by content.
- `tests/management/test_inspect_django_type.py`
  (edited by this item): 4 pre-edit WT hunks, all
  attributed — H1 `Edition` import + H2 oracle
  docstring reword + H3 mirror gate (`_mirror_check`
  + `test_inspect_suppressed_pk_mirror_matches_synthesis`)
  match the run-3 ledger row (adopted, retained);
  H4 (`test_scalar_name_reads_a_non_class_leafs_declared_name_or_its_text`)
  pins hunt truth-migration behavior (concurrent).
  This item's addition (EOF append + 1 stdlib
  import line) touches none of those hunks' lines.

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched, twins
   read at current bytes. The commands are the
   only CLI surface; no sibling flavor re-implements
   import translation, SDL export, or type
   introspection. The twin `Command` shell is
   framework spelling over disjoint contracts
   (FR-1). The three direct `import_string` sites
   keep non-CLI contracts at WT bodies (FR-5).
   Soft-import helpers keep library error contracts
   on clean bytes (FR-3). Mint guard vs table-print
   guard stay surface-distinct (FC-11). Discharged.
2. Sync/async twins: discharged inapplicable by
   construction. Instrument (P1, AST walk): zero
   `AsyncFunctionDef`, zero `await` in all four
   folder files; management commands are sync by
   framework. No second pipeline exists to drift.
3. Derived rather than repeated knowledge: every
   same-token population in the folder was walked
   on body strength at WT bytes (P2). Single
   definitions with by-name consumers:
   `import_or_command_error` (1 + 2),
   `_validate_absolute_module_path` (1 + 2), the
   selector entry (1 + 2 command calls), the
   dotted entry (1 + 1), `print_schema` (1
   executable call + 2 prose), `schema_output`
   (1 binding, 2 emitters), `_sdl_type_name`
   (1 + 2), `_scalar_name` (1 + partial + 5
   or-defaults + 1 default-arg), `_yes_no`
   (1 + 2), `_consumer_nullable` (1 + 2),
   `origin.__annotations__[` (exactly 2, both
   auto-row reads), `default_symbol_name="schema"`
   (2 convergent pins, FR-7), `"no (list)"`
   (2 display sites, FR-8), `.get(kind, kind)`
   (2 lookup sites, FR-9), union-origin checks
   (predicate + renderer, FR-10),
   `scalar_namer or _scalar_name` (5 `or`-defaults
   over 1 owner, C58), `str(e)) from e` (2
   executable sites, FR-2). One true twin found:
   the finalized-fields fetch + find-by-name
   (FAM-1, consolidated). No fact re-derived.
   Discharged.
4. Inverse / round-trip pairs: SDL render is
   one-way (no parse-back); table render is
   one-way (no parse-back); the two annotation
   renderers walk disjoint object models over
   disjoint inputs and share only the leaf
   (FR-6). One grammar per pair, correctly
   separated halves. Discharged.
5. Contracts restated in another medium: counted
   1 definition per rule; everything else
   classified. Contract sources: [spec-022][spec-022]
   Decisions 1–10 (export shape, shared-helper
   pin, render delegation, byte identity,
   CommandError surface, non-goals) +
   [spec-029][spec-029] Decision 4 (inspect shape,
   dispatch, `--schema`-first, error populations)
   + the maintainer's `0c76625a` behavior note (export
   non-str guard). Oracles:
   [test-imports][test-imports] (wrapping, guards,
   passthrough), [test-export-schema][test-export-schema]
   + [live-export][live-export] (argparse, bytes,
   messages, kwargs), [test-inspect][test-inspect] +
   [live-inspect][live-inspect] (rows, titles,
   labels, messages) + the new FAM-1 gate: all
   assert literals through the public surface,
   never owner internals. Projections: module /
   class / method docstrings (clause-verified),
   TREE folder lines (rendered from the
   docstrings), glossary + README command entries.
   No medium holds an independently maintained
   copy. Discharged.
6. Enforcement by omission: families enumerated
   per rule against contract sources. Import
   surface: both commands route every import
   failure through the shim (3 calls, 0 direct
   upstream code imports). Field-kind family
   (auto scalar / auto relation / suppressed
   Relay pk / relation pks / 4-corner consumer
   overrides / file-image output / choice enum /
   connection-only): every member reaches a row
   builder via most-specific-first dispatch, each
   pinned at its tier. `CommandError` families:
   every member pinned. Two omission probes
   investigated and released (no contract source,
   no wire reach): inspect's missing non-str
   option guard (export guards, inspect does not —
   see Defects) and the ForeignObject arm's
   absence on the connection-only path (correct
   scoping: synthesis is many-side-only — see
   Defects). The relay D1 (predictor ignores
   consumer sets) is recorded, not duplicated.
   No member lacks a guard its contract requires.
   Discharged.

### Enumeration

Instrument: `ast.parse` over post-edit WT bytes
(P1), `len(ast.Module.body)` per file. Counts:
`__init__.py` 1 (docstring → FL-1);
`_imports.py` 11 (docstring + 5 imports + `T` +
4 defs → FL-2, homes as the member artifact's
F1–F4; the nested `_import` def is F4 machinery);
`export_schema.py` 9 (docstring + 7 imports +
`class Command` → FL-3, F1–F5 + the NEW
location-type gate); `inspect_django_type.py` 45
(docstring + 24 imports + TYPE_CHECKING block +
7 constants + `class Command` (12 methods) + 11
module defs → FL-4, F1–F12 + FAM-1). 66/66
members homed; every `### Challenges` row ends in
a file-local row, a family row, or a rejection.

### Challenges

Authoritative definitions counted only;
consumers, oracles, and projections that move
alongside are listed, never counted. Read-only
probes live under
`$TMPDIR/dry-folder-mgmtcmds/` (`p1_census.py`
AST + async census, `p2_twins.py` twin +
single-site battery, plus `rg` censuses quoted
below); all ran green against WT bytes (no
package import, no DB). FAM-1 counts are
`execution-verified` (workspace runs
`dry-20261010T020126-db9e35`,
`dry-20261010T020157-71c6b3`); all other
ownership verdicts are `static-reviewed` with
named oracles. No shared-tree pytest beyond the
one authorized single
(`test_connection_and_consumer_rows_compose_the_shared_field_type_lookup`,
1 passed); no `docs/dry/temp-tests/` scratch.

| Id | Change posited | Definitions forced |
|---|---|---|
| C1 | Widen the translation catch to `ValueError` | 1 (core; passthrough oracles fail — listed) |
| C2 | Drop the `from e` chaining | 1 (core; cause-identity oracles fail) |
| C3 | Add a third malformed-path shape | 1 (validator; both entries follow) |
| C4 | Reword the empty-path message | 1 (validator) |
| C5 | Change the colon-split grammar | 1 (selector entry; upstream owns resolution, 0) |
| C6 | Change the `"schema selector"` label | 1 (selector entry) |
| C7 | Change the `rpartition` grammar | 1 (dotted entry) |
| C8 | Drop the missing-module guard | 1 (dotted entry) |
| C9 | Unify the lambda/def importer spellings | refused (FR-14: Any-contract asymmetry) |
| C10 | Add a third export flag | 1 (Command; Decision 6 forbids) |
| C11 | Restore bare-`--path` tolerance | 1 (Command) |
| C12 | Re-add Django's trailing newline | 1 (routing; byte twins fail) |
| C13 | Drop `newline=""` on the write | 1 (routing; kwargs pin fails) |
| C14 | Route on truthiness (`if path:`) | 1 (routing; empty-path oracles fail) |
| C15 | Admit a second accepted Schema type | 1 (Schema gate) |
| C16 | Accept whitespace-only `--path` | 1 (emptiness gate) |
| C17 | Create missing write parents | 1 (write branch) |
| C18 | Widen the write catch to `Exception` | 1 (write branch) |
| C19 | Drop the schema-location type guard | 1 (guard; non-str oracle fails) |
| C20 | Change the guard message/kind naming | 1 here (message; `truth.kind` 0 here) |
| C21 | Add a third inspect flag | 1 (Command) |
| C22 | Import `--schema` lazily | 1 (handle; cold-path twins fail) |
| C23 | Resolve dotted paths via the registry | 1 (dispatch; Decision 4 forbids retry) |
| C24 | Match bare names on `__name__` only | 1 (SDL surface twins fail) |
| C25 | Change the SDL-name rule itself | 0 here (upstream converter + `graphql_type_name`) |
| C26 | Ambiguity becomes first-match | 1 (ambiguity twins fail) |
| C27 | Admit non-`DjangoType` symbols | 1 (subclass gate) |
| C28 | Merge no-definition + unfinalized | 1 (Decision 4 pins distinct) |
| C29 | Stop suppressing the Relay pk | 1 here + owner (relay family, FC-3) |
| C30 | Suppress relation pks too | 2 (relay family, FC-3) |
| C31 | Reorder dispatch (scalar before consumer) | 1 (four-corner matrix fails) |
| C32 | Add a sixth `RelationKind` literal | 0 vocab + 1 label row (FC-6) |
| C33 | Rename `relation_connections` | 0 record + 1 read site (FC-7) |
| C34 | Re-derive nullability via `convert_scalar` | 1 (override oracle inverts) |
| C35 | Print the `StrawberryAnnotation` repr | 1 (absence oracle fails) |
| C36 | Swallow UNRESOLVED as a type | 1 (forward-ref oracle fails) |
| C37 | Title with `__name__` | 1 (title twins fail) |
| C38 | Hardcode a second `"BigInt"` | 1 (table; live twin fails) |
| C39 | Merge the two renderers | refused (FR-6: disjoint object models) |
| C40 | Change the finalization evidence for the fields read | 1 (FAM-1; was 2, consolidated) |
| C41 | Change the find-by-name rule | 1 (FAM-1; was 2, consolidated) |
| C42 | Change the MRO firing rule | mro family (FC-4; RJkeywalk superseded) |
| C43 | Share one `Command` skeleton | refused (FR-1: framework spelling) |
| C44 | Share one `CommandError` policy | refused (FR-2: disjoint populations) |
| C45 | One resolve-anything entry | refused (FR-4: disjoint grammars) |
| C46 | Fold the direct `import_string` sites | refused (FR-5: non-CLI contracts) |
| C47 | Merge with `utils/imports.py` | refused (FR-3: library vs CLI) |
| C48 | Default/constant the schema symbol | refused (FR-7: callers choose) |
| C49 | Constant the `"no (list)"` token | refused (FR-8: display vocabulary) |
| C50 | Share the label-lookup fallback | refused (FR-9: real axis moves 1) |
| C51 | Share a union-args helper | refused (FR-10: typing mechanics) |
| C52 | Record-type the row tuple | refused (FR-11: relieves nothing) |
| C53 | Constant the column widths | refused (FR-12: adjacent layout) |
| C54 | Merge title/disambiguation formats | refused (FR-13: distinct purposes) |
| C55 | Merge the Union-suppression prose | refused (FR-15: tool-required) |
| C56 | Unify the options-typing posture | refused (FR-16: no shared rule) |
| C57 | Add a third command | 1 (inventory gains a name; FR-1 trigger watch) |
| C58 | Change the default scalar namer | 0 here (owner `_scalar_name`; 5 or-defaults + partial + default-arg follow by reference) |
| C59 | Reword a help string | 1 per command (RJskeleton surfaces) |
| C60 | Add a sixth cold-path scalar row | 1 (table; BigInt arm stays derived) |
| C61 | Extend connection synthesis to the single side | 0 synthesis + 1 label site (gains the arm; FC-7) |

Probe commands and what each proved (census
figures `execution-verified`; ownership verdicts
`static-reviewed` with named oracles):

- `uv run python $TMPDIR/dry-folder-mgmtcmds/p1_census.py`:
  AST member counts 1/11/9/45 post-edit (44
  pre-edit + FAM-1); 0 async defs, 0 awaits, all
  four files (matrix axis 2 + FF-4 delta).
- `uv run python $TMPDIR/dry-folder-mgmtcmds/p2_twins.py`:
  1 executable `print_schema` call (+ 2 prose);
  exactly 2 `origin.__annotations__[` spellings;
  `default_symbol_name="schema"` ×2 (FR-7);
  `"no (list)"` ×2 (FR-8); `finalized_origin`
  twin ×2 pre-edit, 1 post-edit (FAM-1);
  `.get(kind, kind)` ×2 (FR-9); union-origin
  checks ×2 (FR-10); executable `from e` ×2 —
  shim :24 + export :71, inspect 0 (FR-2);
  `truth.*` fns export {kind} / inspect
  {class_dict, is_subclass, is_type, label, mro,
  name, static_attr, text} (FC-10); `class
  Command(BaseCommand)` ×2 (FR-1); 0 direct
  upstream-importer code imports in either
  command (FC-1); `_is_suppressed_relay_pk`
  exactly 2 hits, both the CLI predictor
  (FC-3); label keys == the 5 `RelationKind`
  literals (FC-6).
- `rg import_module_symbol_or_command_error\(|import_string_or_command_error\(`:
  exactly 3 call sites, all in-folder (FC-1).
- `rg __all__` in-folder: 0 hits (manifest
  posture: docstring-only markers).
- `rg "no \(list\)"` package-wide outside
  inspect/tests: 0 hits (FR-8 display-only).
- `rg unwrap_graphql_type` in-folder: 0 hits
  (FC-11 R3 trigger unfired).
- `rg CommandError` in `utils/imports.py` (WT +
  HEAD): 0 hits (FC-11 R2 basis; file clean).
- `grep -c management-import-*-entry` over the
  plan: 0 hits (FF-2); the names are cited by
  the export + inspect member artifacts only.
- Bodies read whole at WT: the 3 RJ4 sites
  (FR-5), `global_id_for` gate (FC-11 J4),
  synthesis many-side gate
  (`field_map[name].is_many_side`, Defects),
  `_validate_relation_shapes` vocabulary,
  `RelationKind` literal, `WithStrawberryObjectDefinition`
  protocol (`:207-211`), `StrawberryField`
  dataclass, the mirror-gate test (FC-3),
  both oracle tiers' cited rows.

## Findings

Proof status: FAM-1 `execution-verified`
(workspace runs cited); every other finding
`static-reviewed` (zero-edit compositions and
rejections; behavior pinned by the named
permanent oracles, re-run via the `gate:`
entries). Census figures are
`execution-verified` (probes above). Freshness
for every finding: the Pins table (all four
folder files in WT/HEAD/BASE + the
connected-owner/oracle fingerprints) plus the
per-finding deltas noted inline.

### FAM-1 — `management-inspect-finalized-field-type-lookup` (CONFIRMED count-2, CONSOLIDATED 2→1)

- Contract + variation: the finalized
  Strawberry field type for a python name on a
  finalized `DjangoTypeDefinition` — the
  `origin.__strawberry_definition__.fields`
  record (present because `handle` refused an
  unfinalized type) projected by `python_name`,
  `StopIteration` on a missing name. Varies on
  the finalization evidence (C40) and the
  find-by-name rule (C41) only.
- Sites + roles: 2 byte-identical 5-line blocks
  (comment + cast + fields read + find) in
  `_connection_only_relation_row` (key:
  synthesized `generated`) and
  `_consumer_authored_row` (key: `field.name`).
  Same inputs shape (definition + name), same
  output, same absence behavior, same reasons
  to change — and the hunt's ongoing migration
  of these very `__strawberry_definition__`
  reads (already landed on `_scalar_name` +
  `_sdl_type_name` at WT) is a live axis both
  would move on. Both blocks HEAD-identical
  (verified verbatim at HEAD :399-403 /
  :463-467); neither block carries WT dirt
  (the adjacent hunt hunks are the UNRESOLVED
  f-string and the import block — disjoint).
  Excluded on body strength: the 3
  mutations-side `.fields` reads (input-class
  fields, no cast, no finalization evidence —
  different contracts) and `_sdl_type_name`'s
  presence check (fallback gate, not a fields
  read).
- Challenges: C40 count 2 → 1; C41 count 2 → 1.
- Owner + lifetime: module-level
  `_strawberry_field_type(definition,
  python_name)` (new, this item) — principle 7:
  both callers are in-file, no consumer outside
  needs the lookup, so the defining module is
  the narrowest cohesive owner; the record
  stays upstream (Strawberry metadata). Pure
  read; nothing stored.
- Migration: the two blocks become
  `field_type = _strawberry_field_type(definition,
  generated)` / `(definition, field.name)`;
  the cast + justification comment move into
  the helper verbatim; the `next()` find moves
  with its key parameterized. No cast, widening,
  or suppression added: the return is `object`,
  matching the file's existing treatment
  (`_render_strawberry_type(field_type:
  object)`), and the moved cast is the same
  cast, not a new one.
- Distinct behavior: the UNRESOLVED refusal,
  the sibling-vs-override key choice, and the
  downstream renders stay per-site; absence
  stays loud (`StopIteration`) at both.
- Behavioral proof: `execution-verified` —
  26/26 green in slot-2
  (`dry-20261010T020126-db9e35`: the full
  package module incl. the UNRESOLVED,
  consumer-row, and OddShape oracles + both
  live connection-only params), plus the
  authorized shared-tree single (1 passed).
  Principle-8 axes preserved: same values,
  same read order, same raise sites
  (`StopIteration` still escapes uncaught from
  the same logical point — the helper is not a
  generator, so no PEP 479 translation).
- Structural gate:
  `test_connection_and_consumer_rows_compose_the_shared_field_type_lookup`
  (exact AST multiset: 1 fields-read + 2
  composers), green both trees.
- Failability: re-inlining one composer fails
  exactly the gate row (`prove` entry 1,
  `dry-20261010T020157-71c6b3`, verdict
  pinned, 25/25 other scope rows green,
  byte-identical restore).
- Coupling: none — the relay D1 (dispatch
  order) and the mro migration (walk body)
  touch neither the helper nor its call lines.
- Freshness: Pins table + pre-edit WT
  `77eaff4f` (BASE) vs post-edit `86785d55`.

### FC-1 — shim import entries (CONFIRM consolidated posture)

The two entries are each defined once in
[_imports.py][commands-imports] and composed by
name at exactly 3 call sites, all in-folder:
the selector entry from export `:50` +
inspect `:145`, the dotted entry from inspect
`:180` (P2 + rg census). Zero direct
`django.utils.module_loading` /
`strawberry.utils.importer` code imports in
either command file (the inspect docstring's
two prose mentions are projections). Internal
composition holds too: `import_or_command_error`
1 def + 2 calls, `_validate_absolute_module_path`
1 def + 2 calls. The committed lambda →
`_import` def drift is F4 machinery (Any
avoidance), not a new rule (FR-14). Posture
CONFIRMED; no second site.

### FC-2 — registry map consumer (CONFIRM)

`_resolve_bare_name` + `_print_table` read
`registry.iter_definitions()` /
`registry.model_for_type()` by name (both
exist at WT `c5aa2050`); the map stays owned
by `registry.py::TypeRegistry` (indexed family
`type-registry-model-type-map`). The match +
ambiguity listing stay owned here (C24/C26
count 1). Posture CONFIRMED.

### FC-3 — relay suppression mirror (CONFIRM blocked-on-hunt, UNAPPLIED)

The predictor
`Command._is_suppressed_relay_pk` is still
inline at WT (is_relation-first + shared
`_is_relay_shaped` + pk-name identity); the
owner `types/base.py::_is_suppressed_relay_pk`
is still 0 hits package-wide (P2 census:
exactly 2 hits, def + call site, both the
CLI); the mirror-gate test survives WT-only
(`_mirror_check` + 6-arm gate, ledger dirt);
the maintainer decision (a/b/c) is still
owed. Owner-side order claim re-verified at
WT bytes (relation branch precedes the
suppression check in `_build_annotations`).
The migration would rewrite the predictor
body + docstring (whose citation hunk is hunt
dirt) and insert the owner into hunt-dirtied
`types/base.py`. Block CONFIRMED; zero edits
here. The standing D1 (predictor ignores
consumer sets) is referenced, not duplicated.

### FC-4 — MRO-map key lookup (CONFIRM blocked-on-hunt, CONFIRMED family)

Family [rule-mro][rule-mro] F1 (verified,
pending execution) owns this rule now; the
file-item RJkeywalk is SUPERSEDED by that
confirmation (its trigger — a `key_for_field`
entry beside `scalar_for_field` — is the
specified owner). Folder site
`_matched_scalar_key` still spells its own
walk at WT (`truth.mro` + `in` + `truth.name`,
:509-512 — hunt dirt); the 7-step migration
(f42) rewrites that hunk and rides the hunt's
`truth` import. The two value legs now live
behind the hunt's `_class_map_lookup`; the
predictor divergence the family proved still
stands. Block CONFIRMED; zero edits here.
C42 counts through the family, not here.

### FC-5 — scalar maps + schema config (CONFIRM consumers)

`_GRAPHQL_SCALAR_NAMES` still merges
package-defined names from
`scalars._PACKAGE_SCALAR_MAP` (exists at WT
`072432e6`, annotated dict) instead of a
second literal — no second `"BigInt"` spelling
in the folder (C38/C60 count 1); `_scalar_name`
still prefers the schema `scalar_map` entry,
then the table, then definition metadata, then
`__name__` (WT tail truth-migrated, same
precedence). The maps and the live config stay
with their owners. Posture CONFIRMED.

### FC-6 — relation vocabulary + display labels (CONFIRM)

`RelationKind` is still exactly the 5 literals
(`many`, `reverse_many_to_one`,
`reverse_one_to_one`, `forward_single`,
`generic`) at WT `cc68c6ba`; the label map
keys equal them (P2); the raw-token fallback
covers a sixth (C32: 0 vocab + 1 label row).
The committed `forward ForeignObject` arm
refines the `_relation_row` lookup only — the
connection-only path correctly lacks it
(synthesis is many-side-only; see Defects).
R13's trigger (a production reader of the
labels as data) is unfired: both `.get`
sites render into display strings (FR-9).
Posture CONFIRMED.

### FC-7 — synthesis record consumer (CONFIRM)

`_suppressed_connection_name` still reads the
finalizer's own `relation_connections`
record (exists at WT `8f699081`) by inverted
lookup, never by string building; the
popped-annotation detection and the sibling
render stay owned here (C33: 0 record + 1
read site; C61 pins the many-side scoping).
The record and `_suppress_relation_list_form`
stay with the finalizer. Posture CONFIRMED.

### FC-8 — override sets + sentinel (CONFIRM)

`_consumer_authored_row` still reads the
finalized `__strawberry_definition__` record
(now via FAM-1) and the four-corner override
sets (all exist at WT `f42bcee3` /
`dfad92ca`); the UNRESOLVED refusal still
raises `CommandError` with the recovery hint
(C35/C36 count 1). The sets stay with
`types/base.py`, the sentinel upstream.
Posture CONFIRMED.

### FC-9 — SDL-name rule consumers (CONFIRM)

`_sdl_type_name` still applies
`name_converter.from_type` over the finalized
object definition (WT read via
`truth.class_dict`, same class-owned gate)
with the `graphql_type_name` fallback for the
unfinalized path (exists at WT); 1 def + 2
calls (bare-name match + title). The converter
rule stays upstream, the fallback name with
`types/definition.py` (C25: 0 here; the
class-owned distinction counts 1 here).
Posture CONFIRMED.

### FC-10 — truth reads (CONFIRM consumer posture, concurrent owner)

The folder composes 9 `truth.*` readers by
name — export {kind}, inspect {class_dict,
is_subclass, is_type, label, mro, name,
static_attr, text} — plus the hunt-added
`_model_name` helper and the `StrawberryType`
TYPE_CHECKING import. Owner
`utils/truth.py` is untracked concurrent work:
composed, never defined here; untouched by
this item (FAM-1's lines are truth-free —
the cast + `.fields` read predate the
migration and the hunt hasn't rewritten them).
Posture CONFIRMED.

### FC-11 — rejected-pair triggers (CONFIRM all stand)

- J4 (`testing-relay-finalized-gate-vs-cli-check`):
  `global_id_for` still guards minting
  (ConfigurationError + finalize-first
  remediation + stamp read, WT `8a31c1ad`);
  the CLI still guards table-printing
  (`CommandError`, no remediation, no stamp
  read). No shared guard vocabulary
  introduced; no cross-import either way.
  Trigger unfired.
- R12 (`types-definition-custom-id-vs-suppression-mirror`):
  safety predicate vs identity
  performer/predictor still disjoint (a custom
  resolver without suppression and vice versa
  both exist). UNAPPLIED re-checks fresh:
  owner 0 hits, predictor inline, mirror gate
  WT-only, decision owed. Trigger (collapse
  to one question) unfired.
- R2 (`imports-vs-command-path-translators`):
  `utils/imports.py` still soft-lookup only —
  0 `CommandError` hits at WT and HEAD on
  clean bytes (`3ea52b16`), no shape
  validation. Trigger (a command needing
  optional degradation) unfired: neither
  command imports the soft helpers.
- R3 (`typing-peel-vs-render`): both renders
  still descend-to-render; 0
  `unwrap_graphql_type` callers in-folder.
  Trigger (a render needing the core as a
  value) unfired.
- Leaf manifests (`types-` + `utils-leaf-vs-sibling-manifest`):
  this folder's member `commands/__init__.py`
  is byte-unchanged (`31cb58b8`,
  docstring-only, no `__all__`); the parent
  marker is byte-unchanged (`beb4e0ee`).
  Neither moved posture, so neither fired the
  shared trigger from this side.

### FL-1 — inventory marker (1 rule, single-owned)

R1 command inventory statement: the
`commands/__init__.py` docstring names both
shipped commands (`export_schema`,
`inspect_django_type`); the directory holds
exactly those two command modules (plus the
discovery-excluded `_imports.py` and the
marker itself — `ls` census). C57 counts 1.
The parent-marker separation stands (both
markers byte-unchanged; opposite change
responses). No test reads the wording; the
TREE render is a projection.

### FL-2 — import-translation rules (4 rules, single-owned)

- R1 translation core
  (`import_or_command_error`): runs the
  importer, returns its value unchanged,
  re-raises `(ImportError, AttributeError)` as
  `CommandError(str(e)) from e`. C1/C2 count
  1. The narrow catch stays intentional
  (passthrough oracles pin it).
- R2 shape validation
  (`_validate_absolute_module_path`): rejects
  empty + leading-dot module paths with
  value+label messages, pre-import. C3/C4
  count 1 (both entries follow as consumers).
- R3 selector entry
  (`import_module_symbol_or_command_error`):
  colon-split, validate (`"schema selector"`),
  delegate with `default_symbol_name`. C5/C6
  count 1 (resolution upstream, 0 here).
- R4 dotted-path entry
  (`import_string_or_command_error`):
  `rpartition`, missing-module guard, validate
  (`"dotted object path"`), delegate. C7/C8
  count 1. The committed nested `_import` def
  is R4 machinery (Any avoidance), not a new
  rule; the lambda/def asymmetry is FR-14.

### FL-3 — export rules (6 rules, single-owned)

- R1 CLI shape + selector delegation:
  `BaseCommand` + `help`, positional `schema`
  + `--path` (both `type=str`, no `nargs`),
  resolve via the selector entry with
  `default_symbol_name="schema"`. C10/C11
  count 1 (C5-grammar 0 here via FC-1).
- R2 SDL render + three-branch routing:
  single `print_schema` call (P2: the only
  executable call package-wide), `path is
  None` → stdout with `ending=""`, else F4/F5.
  C12–C14 count 1.
- R3 non-`Schema` gate: verbatim
  backticked message, subclass admitted.
  C15 counts 1.
- R4 `--path` emptiness gate: non-str or
  blank → verbatim message. C16 counts 1.
- R5 destructive UTF-8 write + failure
  translation + success report: `write_text`
  with `encoding`/`newline`, `(OSError,
  ValueError)` → `CommandError(str(e)) from
  e`, `SUCCESS` report. C17/C18 count 1.
- R6 schema-location type gate (NEW since
  file verification, committed `0c76625a`):
  a direct `handle` call bypasses argparse's
  `type=str`, so non-str `options["schema"]`
  raises `CommandError` naming
  `truth.kind(...)` instead of escaping as
  `AttributeError`. C19/C20 count 1. Pinned
  by
  `test_export_schema_raises_command_error_for_a_non_string_schema_location`
  (direct `handle(schema=5)`). Distinct
  behavior: the twin keeps its `Any`-typed
  options without this guard — unifying
  postures is a refactor, not a rule merge
  (FR-16), and the behavioral half is the
  released axis-6 edge (Defects).

### FL-4 — inspect rules (13 rules, single-owned)

- R1 CLI shape + `--schema`-first handle +
  type dispatch: positional `type` +
  `--schema`, import-first order, `"." in arg`
  dispatch (not fallback). C21–C23 count 1
  (C5-grammar 0 here via FC-1).
- R2 bare-name registry resolution: two-surface
  match (SDL name + `__name__`),
  dedupe-by-iteration, hint/ambiguity wordings.
  C24/C26 count 1 (C25 name rule 0 here via
  FC-9; map 0 here via FC-2).
- R3 type gates: non-`DjangoType`,
  no-definition, unfinalized — three distinct
  branches. C27/C28 count 1.
- R4 suppressed-Relay-pk row: the inline
  predictor + `GlobalID!` / `no` /
  `relay.Node id` literals. C29/C30 count
  through FC-3 (relay family).
- R5 most-specific-first row dispatch:
  suppressed → consumer → relation → scalar
  over the single `field_map[field.name]`
  index. C31 counts 1.
- R6 relation rows + labels + connection-only
  shape: annotation render, friendly labels
  with raw-token fallback, `no (list)` /
  yes-no tokens, sibling detection via the
  synthesizer record. C32/C33/C61 count as
  tabled (vocabulary + record 0 here via
  FC-6/FC-7). Includes the committed
  `forward ForeignObject` arm (label
  refinement for non-`ForeignKey` forward
  links, pinned by
  `test_inspect_labels_a_forward_foreign_object_by_its_link`).
- R7 scalar rows + converter naming:
  annotation-read nullability, output-map /
  choice-enum / `SCALAR_MAP[ancestor]`
  spellings. C34 counts 1 (C42 firing rule
  via FC-4).
- R8 consumer-authored rows + labels: metadata
  source (now via FAM-1), UNRESOLVED refusal,
  four-corner label grammar, wrapper tokens.
  C35/C36 count 1.
- R9 table render + SDL title: converter-applied
  title + model, fixed header/rule/rows in
  selection order. C37 counts 1.
- R10 SDL-name resolution: converter-first
  application + class-owned fallback gate.
  Counts via FC-9.
- R11 scalar-name fallback table + precedence:
  schema map → built-in/derived table →
  metadata → `__name__`; no second literal.
  C38/C60 count 1 (maps 0 here via FC-5).
- R12 annotation renderers + tokens: the two
  renderers + shared leaf + token mappers.
  C39 refused (FR-6); C58 default 0 here.
- R13 finalized field-type lookup (FAM-1, this
  item): `_strawberry_field_type`, 1 def + 2
  composers, gated. C40/C41 count 1.

### FR-1 — shared `Command` skeleton (REJECTED, re-derived)

Considered: one driver for the `class
Command(BaseCommand)` / `help` /
`add_arguments` / `handle` shell in both
commands. Contract difference: Django owns
the class name, base class, and hook names —
no package rule selects them, and the two
bodies enforce disjoint contracts
(selector→SDL→stdout/file vs
type-name→field-table). A third command
module still does not exist (`ls` census).
The only shared rule beyond framework
spelling — the selector-helper import — is
already composed by name (FC-1). A shared
args/handle abstraction would add a mode
flag no real path reaches (principle 5).
Trigger: a third command whose argument
surface genuinely overlaps one of these two
(then extend the `_imports` precedent per
[spec-022][spec-022] Decision 3, not the
shell). Durable home: this clause (either
twin copy reopens both).

### FR-2 — shared `CommandError` message/cause policy (REJECTED, re-derived)

Considered: one `str(e)`/`from e` policy
driver covering the shim core (`:24`) and
the export write branch (`:71`) — still the
only two executable spellings (P2; inspect
has 0). Contract difference:
import-failure population (operator named an
unimportable path) vs file-write-failure
population (operator named an unwritable
path). Narrowing either catch must not move
the other; rewording write failures with the
path must not move import failures. Same
spelling, not the same rule. Trigger: a
decision that every `CommandError` shares
one message/cause policy (checked absent in
both specs + the plan index). Durable home:
this clause.

### FR-3 — merge with `utils/imports.py` (REJECTED, re-derived)

Considered: one import-handling owner for
the CLI translators and the soft-import
helpers. Contract difference: library
soft-lookup (returns `None` / raises
hint-carrying `ImportError`; `CommandError`
unavailable and meaningless outside a
command) vs CLI failure (raises
cause-chained `CommandError` for an
operator-facing path, with shape
pre-validation). `utils/imports.py` re-read
at WT: still no `CommandError`, still no
shape validation (file clean, `3ea52b16`).
Routing commands through soft lookup would
mistranslate a typo'd schema path as an
absent optional dependency. Trigger: a
command needing optional-module degradation.
Durable home: this clause (converges with
the utils-side R2).

### FR-4 — one resolve-anything entry (REJECTED, re-derived)

Considered: a single helper taking either
grammar. Contract difference: Strawberry
`module[:symbol]` (upstream owner
`import_module_symbol`, default-symbol
contract) vs Django dotted path (upstream
owner `import_string`, missing-module
contract) — disjoint grammars with distinct
upstream owners and distinct guards (the
missing-module guard has no selector
analogue). Callers still dispatch by shape
before calling (inspect on `"." in arg`;
export always a selector), so a merged entry
adds shape-sniffing — a mode flag no real
path needs (principle 5). Trigger: callers
stop dispatching by shape and one grammar's
guards become the other's. Durable home:
this clause.

### FR-5 — fold the direct `import_string` sites (REJECTED, re-derived)

Considered: routing the three direct
`import_string` call sites through the shim.
Contract differences, each re-read on body
strength at WT: `resolve_lazy_class`
(absolute attempt + module-relative retry,
else propagate — consumer-declared class
reference); `session_store_class`
(deployment-facing `ConfigurationError`
after hostile-setting flattening);
`_require_boundary_before_csrf` (raw startup
import; only the misorder raises
`ConfigurationError`). None can raise
`CommandError` (no command context) and none
pre-validates shapes. Shared upstream token,
not a shared rule. Trigger: a CLI surface
resolving consumer-declared class references
through a command. Durable home: this clause.

### FR-6 — merge the annotation renderers (REJECTED, re-derived)

Considered: one dispatcher merging
`_render_annotation` (typing annotations)
and `_render_strawberry_type` (Strawberry
wrappers). Contract difference: disjoint
object models (`get_origin`/`get_args` vs
`StrawberryOptional`/`StrawberryList`
isinstance) over disjoint inputs
(post-finalize `__annotations__` values vs
finalized field-metadata `.type`s); they
already share the `_scalar_name` leaf, so a
merge buys a per-node dispatch branch at the
cost of the call site. Trigger: a third
caller needing both input shapes through one
entry (the leaf stays shared; only the
dispatch is new). Durable home: this clause.

### FR-7 — default/constant the schema symbol (REJECTED, folder-new)

Considered: one home for the
`default_symbol_name="schema"` literal at
export `:52` + inspect `:147`. Contract
difference: the shim REQUIRES the argument
(no default) — the signature owns the
"callers choose" contract; each caller's
choice is pinned by its own command's oracles
(bare-`"config.schema"` selectors) under
distinct specs ([spec-022][spec-022] vs
[spec-029][spec-029]). Posit an inspect-only
`--schema-attr` override → export must not
move. Convergent choice, not one rule; the
ecosystem convention it spells
(`schema`-modules-expose-`schema`) has no
plausible rename axis. A shim-level default
would change the required-parameter design,
not consolidate a rule. Trigger: a third
schema-selector call site, or a
framework-wide default-symbol decision.
Durable home: this clause.

### FR-8 — constant the `"no (list)"` token (REJECTED, folder-new)

Considered: one constant for the token at
`:352` (relation row, `FieldMeta`-decided)
and `:542` (consumer row, wrapper-decided).
Contract difference: two nullability
DECISIONS over one display vocabulary — the
mechanisms differ (field metadata vs
Strawberry wrappers) while the emitted token
agrees. The token is display-only (0
production matchers package-wide; tests
match as oracles). A column restyle moves
the whole token family (`yes`/`no`/`no
(list)`), not just this pair — extracting
one token's constant relieves no coherent
obligation (principle 11). Trigger: a third
spelling site, or a consumer that must MATCH
the token (then it becomes data, not
display). Durable home: this clause.

### FR-9 — share the label-lookup fallback (REJECTED, folder-new)

Considered: one helper for
`_RELATION_KIND_LABELS.get(kind, kind)` at
`:346` + `:403`. Contract difference: the
rule's REAL variation axis — a new literal —
moves the map alone (1 site either way);
only the hypothetical fallback-policy change
moves both. The policy is stated once in the
map comment (projection at the owner); the
two calls are one stdlib read idiom each,
and the `:346` site is subsequently refined
by the ForeignObject arm while the `:403`
site is final — a shared helper taking just
`kind` would hide that the relation-row
label is intermediate. Machinery for a
`dict.get` (principle 11). Trigger: a third
lookup site, or the fallback gaining
behavior (logging, normalization).
Durable home: this clause.

### FR-10 — share a union-args helper (REJECTED, folder-new)

Considered: one helper for the
`get_origin in (Union, UnionType)` checks at
`:489` (predicate: is `None` present) and
`:676` (renderer: strip `None`, render the
rest). Contract difference: boolean
nullability test vs per-member render —
different contracts over the same `typing`
mechanics (the origin check + `get_args` are
stdlib spelling, not a package rule). A
shared helper returning non-`None` args
would still need the presence/length
distinction at each site (a `None`-less
union renders multi but is not optional),
so it moves the branch without removing a
definition. Trigger: a third union consumer
needing the same filtered tuple. Durable
home: this clause.

### FR-11 — record-type the row tuple (REJECTED, folder-new)

Considered: a `NamedTuple` for the
`(graphql_type, nullable, converter)` row
shape shared by 4 producers + `_resolve_row`
+ the `_print_table` unpacker. Contract
difference: none separable — the producers
construct distinct content; only the
3-positional shape is shared, and a shape
change inherently moves producers +
unpacker (they ARE the shape's
implementation, as a signature is shared by
def + callers). A record relieves nothing
today: the same sites move either way, and
no consumer needs named access. Speculative
generality (a defaulted 4th column) is not a
current axis. Trigger: an optional column
or a second consumer needing named access.
Durable home: this clause.

### FR-12 — constant the column widths (REJECTED, folder-new)

Considered: shared width constants for the
20/20/32/10 layout spelled in the header,
rule, and row f-strings of `_print_table`.
Contract difference: three ADJACENT layout
literals in one method (same screen, mutual
visibility) — a widen-column change touches
3 lines with negligible partial-update risk.
A widths table + format helper would obscure
the self-evident layout for no risky
obligation relieved (principle 11: a helper
obscuring ownership makes the system less
DRY). Trigger: a second table needing the
widths, or data-driven (computed) widths.
Durable home: this clause.

### FR-13 — merge title/disambiguation formats (REJECTED, folder-new)

Considered: one `(model …)` format for the
`_print_table` title (`(model:
{qualified-label})`) and the ambiguity
listing (`(model {short-name})` + dotted
path). Contract difference: the title names
the schema surface of the inspected type
(qualified label, no path needed); the
listing distinguishes CANDIDATES (short name
for scanning + copyable dotted path for
recovery). Different purposes, different
fields; unifying the punctuation would
couple two displays that change for
different reasons. Trigger: a shared
type-mention format decision across CLI
surfaces. Durable home: this clause.

### FR-14 — unify the importer spellings (REJECTED, folder-new)

Considered: one spelling for the selector
entry's `lambda` and the dotted entry's
`def _import`. Contract difference: the def
carries an explicit `-> object` contract +
the django-stubs-Any rationale comment that
a lambda cannot carry (no annotation slot);
the two importer expressions differ in
their upstream typing (precisely-typed
`import_module_symbol` vs Any-typed
`import_string`), so the spelling difference
tracks a real difference. Unifying for
symmetry alone adds lines and drops the
rationale. Trigger: upstream types
`import_string` precisely (then the def can
revert to a lambda). Durable home: this
clause.

### FR-15 — merge the Union-suppression prose (REJECTED, folder-new)

Considered: one home for the identical
basedpyright rationale comments above the
two `# pyright: ignore[reportDeprecated]`
lines (`:487-488`, `:674-675`). Not a rule:
each suppression MUST sit on its line (tool
requirement — unshareable by construction),
and the prose explains the local
suppression. Prose-only production edits
remove no duplication. Trigger: none
foreseen; the tool owns the placement.
Durable home: this clause.

### FR-16 — unify the options-typing posture (REJECTED, folder-new)

Considered: one posture for export's
`**options: object` + isinstance-guard and
inspect's `**options: typing.Any` without
one. Not a shared rule: typing postures are
per-signature style, not a maintained
package definition (no second definition
exists to merge). The executable delta —
adding the non-str guard to inspect — is the
axis-6 edge released in Defects (no contract
source, no wire reach), never
behavior-preserving. Trigger: a
CommandError-only-surface decision spanning
both commands. Durable home: this clause.

### FF-1 — checklist blob pins cite a commit, not blobs (FLAG for closeout)

The four `File management/commands/*` plan
rows each pin "target blob unchanged at
`5ee86193`" — `5ee86193` is a commit sha,
not a blob (same kind as the verified
forms FF-1). Real blobs at verification era:
`31cb58b8` / `05e9de80` / `e27adae9` /
`46dffb3d` (per the member artifacts).
Closeout should re-pin each row to its real
target blob or drop the pin. No row
reopened.

### FF-2 — `management-import-*` names cited as indexed but never transcribed (FLAG for closeout)

The export + inspect member artifacts cite
`management-import-selector-entry` and
`management-import-dotted-path-entry` as
indexed consumer relations (the export W2
even claims "the plan index confirms the
row exists"). `grep -c` over the plan
returns 0 hits for both names, and zero
index rows carry any `File
management/commands/*` holding item — the
file items' rows were never transcribed
(the run-7 re-trace confirmed the gap for
inspect; it spans all four files). The
citations dangle, not the rules: this item
names the same two spellings as new rows 4–5
below, so transcribing them heals the old
citations. No row reopened, nothing
re-applied.

### FF-3 — R8 pair absorbed into hunt-owned `truth.*` at WT (FLAG for closeout)

The `types-finalizer-qualified-label-vs-raw`
rejection (guarded `_safe_qualified_class_name`
vs raw `__module__` interpolations, inspect
×3) holds at HEAD but its sites are gone at
WT: the guarded renderer is deleted from
`types/finalizer.py` and the raw
interpolations are `truth.label(...)` calls
in inspect — both halves absorbed into the
hunt's untracked `utils/truth.py`
(concurrent, unlanded). The contract
difference the rejection records
(hostile-metadata diagnostic vs trusted
display) cannot be re-derived until the
hunt lands. Closeout re-derives post-landing;
the finalizer row stays `rejected` (no
reopen — the WT state is not a verdict).

### FF-4 — member-count drift since file verification (FLAG for closeout)

WT member counts vs the verified pins:
export 7 → 9 (+`override` + `truth`
imports), inspect 40 → 45 post-edit
(-`models` +`override` +`is_single_column_foreign_key`
+`truth` +TYPE_CHECKING block +`_model_name`
+FAM-1), `_imports.py` 11 + 1 nested
(`_import` def inside the dotted entry).
Homes preserved under the shift (Enumeration
above carries the current keying); closeout
should use these lists, not the pre-shift
numbers, when transcribing. Informational
only; no assignment moves.

## Defects

None. Three investigated edges released
without a defect (no contract row broken):

- Inspect's missing non-str option guard
  (axis 6): export guards a non-str
  `options["schema"]` (FL-3 R6); inspect
  guards neither `options["type"]` (raw
  `TypeError` escapes) nor `options.get("schema")`
  (degrades to `CommandError` via the
  translation catch). Released: no contract
  source extends the rule to inspect
  ([spec-029][spec-029] pins seven
  `CommandError` populations, non-str is not
  among them; no oracle pins it), and no wire
  input reaches the gap (argparse +
  `call_command` both guarantee `str` — the
  export oracle's own docstring says
  `call_command` cannot carry the value).
  the maintainer's `0c76625a` documents export only.
  Robustness row at best; reconsideration
  trigger is FR-16's (a two-command
  CommandError-only decision).
- ForeignObject arm absent on the
  connection-only path: `_relation_row`
  refines `forward_single` non-`ForeignKey`
  links to `forward ForeignObject`; the
  connection-only sibling render does not.
  Released, correct scoping: the finalizer
  synthesizes connections only for
  many-side relations
  (`if not definition.field_map[name].is_many_side:
  continue`, read at WT), so a
  `forward_single` ForeignObject can never
  reach `_connection_only_relation_row` — the
  arm would be dead code there (C61 pins the
  scoping).
- Relay D1 (predictor ignores
  `consumer_authored_fields`, dispatch
  suppressed-first): standing family defect
  routing to `Command._resolve_row`,
  recorded in [rule-relay][rule-relay];
  referenced here, not duplicated. FAM-1
  touches neither the dispatch nor the
  predictor (no coupling).

The WT-only deltas (truth migration,
`_model_name`, mirror-gate + scalar-name
test rows) are concurrent hunt WIP or
ledger dirt, observed never filed.

## Pending execution

No `proof:` entries (FAM-1's behavioral
proof + failability are `execution-verified`
in-workspace: `dry-20261010T020126-db9e35`,
`dry-20261010T020157-71c6b3`; every other
finding is `static-reviewed` by kind with
ordering/async pinned by the named
pre-existing oracles). Gate entries for the
final gate (re-run as listed; results bind
to the tree state at gate time):

- `gate: uv run python scripts/workspace.py run dry/folder-mgmtcmds/consolidate -- basedpyright`
- `gate: uv run python scripts/workspace.py run dry/folder-mgmtcmds/consolidate -- basedpyright -p pyrightconfig.floor.json`
- `gate: uv run python scripts/workspace.py run dry/folder-mgmtcmds/consolidate -- python scripts/check_truthful_reads.py --check`
- `gate: uv run pytest -n0 tests/management/test_imports.py -q --no-cov`
- `gate: uv run pytest -n0 tests/management/test_export_schema.py -q --no-cov`
- `gate: uv run pytest -n0 tests/management/test_inspect_django_type.py -q --no-cov`
- `gate: uv run pytest -n0 examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_connection_only_relation_shape_renders_row -q --no-cov`

Cells: `sharded` and `pg` are inapplicable
by construction (stated reason for Worker-2
to judge): both commands' code paths reach
no database, alias, or dialect decision —
inspect reads the type registry +
annotations + Strawberry metadata, export
renders SDL; FAM-1 is a pure metadata
read. The oracles above run under the
default sqlite cell (verified). They need
the maintainer's separate word only if
Worker-2 rejects the reason.

## Judgment

Folder item with one implementation. The
folder owns its 24 rules singly (FL-1..FL-4,
C1–C61 all count ≤1 at their owner with
grammars/maps/records upstream); the one
true twin found (finalized-fields fetch +
find, HEAD-identical 5-line blocks in two
row methods) is consolidated 2→1 at a new
module helper with a proved census gate
(FAM-1); every cross-boundary composition
re-derived at WT bytes holds (FC-1..FC-11,
censuses 3/0/2/5/9 re-derived); every
plausible merge dissolves on a contract
difference with a trigger (FR-1..FR-16);
the 2 pre-rowed open families touching the
folder stay blocked on hunt-owned lines
this item never touched (FC-3/FC-4); four
prior assignments the tree falsified are
flagged for closeout homing without
reopening (FF-1..FF-4). No defect found.
Submission `ready-for-verification/1`.

## Index rows for Worker-0

24 new `file-local` rows (holding item
`Folder integration \`management/commands/\``;
all re-derived at post-edit WT bytes
`31cb58b8`/`0b3faec4`/`112390ff`/`86785d55`;
transcribe verbatim). Rows 4–5 reuse the
spellings the export + inspect member
artifacts cite (FF-2), healing those
citations.

| `management-commands-inventory-marker` | `django_strawberry_framework/management/commands/__init__.py` docstring (2 shipped commands; `ls` census) | `django_strawberry_framework/management/commands/__init__.py` | Folder integration `management/commands/` | file-local |
| `management-import-translation-core` | `django_strawberry_framework/management/commands/_imports.py::import_or_command_error` (narrow catch + `str(e)`/`from e`, value passthrough) | `django_strawberry_framework/management/commands/_imports.py` | Folder integration `management/commands/` | file-local |
| `management-import-shape-validation` | `django_strawberry_framework/management/commands/_imports.py::_validate_absolute_module_path` (empty + relative rejects, value+label wording) | `django_strawberry_framework/management/commands/_imports.py` | Folder integration `management/commands/` | file-local |
| `management-import-selector-entry` | `django_strawberry_framework/management/commands/_imports.py::import_module_symbol_or_command_error` (colon grammar + `"schema selector"` label + upstream delegation) | `django_strawberry_framework/management/commands/_imports.py` | Folder integration `management/commands/` | file-local |
| `management-import-dotted-path-entry` | `django_strawberry_framework/management/commands/_imports.py::import_string_or_command_error` (rpartition + missing-module guard + `"dotted object path"` label + nested `_import`) | `django_strawberry_framework/management/commands/_imports.py` | Folder integration `management/commands/` | file-local |
| `management-export-cli-shape-delegation` | `django_strawberry_framework/management/commands/export_schema.py::Command` args + `default_symbol_name="schema"` selector call (2-arg surface, Decision 6) | `django_strawberry_framework/management/commands/export_schema.py` | Folder integration `management/commands/` | file-local |
| `management-export-render-routing` | `django_strawberry_framework/management/commands/export_schema.py::Command.handle` single `print_schema` + `is None`/blank/value routing with `ending=""` | `django_strawberry_framework/management/commands/export_schema.py` | Folder integration `management/commands/` | file-local |
| `management-export-schema-gate` | `django_strawberry_framework/management/commands/export_schema.py::Command.handle` non-`Schema` gate (verbatim backticked message, subclass admitted) | `django_strawberry_framework/management/commands/export_schema.py` | Folder integration `management/commands/` | file-local |
| `management-export-path-emptiness-gate` | `django_strawberry_framework/management/commands/export_schema.py::Command.handle` `--path` blank gate (verbatim message, whitespace counts) | `django_strawberry_framework/management/commands/export_schema.py` | Folder integration `management/commands/` | file-local |
| `management-export-file-write` | `django_strawberry_framework/management/commands/export_schema.py::Command.handle` destructive UTF-8 `write_text` + `(OSError, ValueError)` translation + `SUCCESS` report | `django_strawberry_framework/management/commands/export_schema.py` | Folder integration `management/commands/` | file-local |
| `management-export-schema-location-type-gate` | `django_strawberry_framework/management/commands/export_schema.py::Command.handle` non-str schema guard (direct-handle bypass, `truth.kind` message; NEW in `0c76625a`) | `django_strawberry_framework/management/commands/export_schema.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-cli-shape-dispatch` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command` args + `--schema`-first order + `"." in arg` dispatch (no registry fallback) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-bare-name-resolution` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command._resolve_bare_name` (SDL + `__name__` match, dedupe, hint/ambiguity listing) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-type-gates` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command.handle` non-`DjangoType` / no-definition / unfinalized gates (3 distinct branches) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-suppressed-relay-pk-row` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command._is_suppressed_relay_pk` + `GlobalID!`/`no`/`relay.Node id` literals (predictor half; rule via Family `relay-pk-suppression-read-mirror`) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-row-dispatch` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command._resolve_row` (suppressed → consumer → relation → scalar over one `field_map` index) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-relation-rows-labels` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command._relation_row` + `_RELATION_KIND_LABELS` + `forward ForeignObject` arm + connection-only sibling render | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-scalar-rows-key-naming` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command._scalar_row` (annotation-read nullability + output-map/choice/`SCALAR_MAP[ancestor]` spellings) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-consumer-authored-rows` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command._consumer_authored_row` (metadata source + UNRESOLVED refusal + four-corner labels + wrapper tokens) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-table-render-title` | `django_strawberry_framework/management/commands/inspect_django_type.py::Command._print_table` (SDL title + fixed header/rule/rows in selection order) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-sdl-name-resolution` | `django_strawberry_framework/management/commands/inspect_django_type.py::_sdl_type_name` (converter-first application + class-owned fallback gate) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-scalar-name-fallback` | `django_strawberry_framework/management/commands/inspect_django_type.py::_GRAPHQL_SCALAR_NAMES` + `::_scalar_name` (precedence + derived BigInt, no second literal) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-annotation-renderers-tokens` | `django_strawberry_framework/management/commands/inspect_django_type.py::_render_annotation` + `::_render_strawberry_type` + shared `_scalar_name` leaf + `_yes_no`/`_consumer_nullable` | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |
| `management-inspect-finalized-field-type-lookup` | `django_strawberry_framework/management/commands/inspect_django_type.py::_strawberry_field_type` (1 def + 2 composers + AST census gate; FAM-1 this item) | `django_strawberry_framework/management/commands/inspect_django_type.py` | Folder integration `management/commands/` | file-local |

### Corrections to existing rows

1. The four `File management/commands/*`
   plan checklist rows each pin "target blob
   unchanged at `5ee86193`" — `5ee86193` is a
   commit sha, not a blob (FF-1). Closeout
   should re-pin each row to its real target
   blob (`31cb58b8` / `05e9de80` /
   `e27adae9` / `46dffb3d` at verification
   era) or drop the pin. No row reopened.
2. No other existing-row correction: the
   run-7 re-trace note on the inspect row is
   accurate, and the ten cross-boundary rows
   holding folder members keep their
   verdicts (FC-3/FC-4/FC-11 + FF-3 carried
   as findings, not row edits).

## Implementation (Worker-1)

Tracked edits (2 files, +82/-10 vs
`ITEM_BASELINE=888135dc3beddbd8d357c386e9fd5ef7fea872e2`;
`git status` count 527 at dispatch, 528 with
this new untracked artifact; HEAD `23b5f421`
unmoved):

- `django_strawberry_framework/management/commands/inspect_django_type.py`
  (+18/-10) — FAM-1: new module-level
  `_strawberry_field_type(definition,
  python_name)` + 2 one-line compositions in
  `_connection_only_relation_row` /
  `_consumer_authored_row` (5-line blocks
  deleted). No cast/widening/suppression the
  replaced code did not need (the moved cast
  is verbatim; `-> object` matches the
  file's existing `field_type` treatment);
  no `Any`; docstring on the new (private)
  helper; no overrides touched. Hunt hunks
  on the path left byte-identical (verified
  by item-scoped diff: only the 3 FAM-1
  hunks).
- `tests/management/test_inspect_django_type.py`
  (+64/-0) — FAM-1 structural gate:
  `_strawberry_field_type_spellings` walker
  + `test_connection_and_consumer_rows_compose_the_shared_field_type_lookup`
  (exact AST multiset 1 + 2) + `import ast`
  line. EOF append + 1 import line; the 4
  pre-edit hunks (ledger ×3, hunt ×1) left
  byte-identical. No banned test words
  (`plan`, `audit`, `sweep`, `restored`,
  `hardening`, `previously`, `worker`,
  `grader`, `feedback` — grep-clean).

Ledger rows owed (Worker-0 transcribes):

- `django_strawberry_framework/management/commands/inspect_django_type.py`
  — Folder integration `management/commands/`
  — new `_strawberry_field_type` + 2
  compositions (FAM-1).
- `tests/management/test_inspect_django_type.py`
  — Folder integration `management/commands/`
  — gate walker + composition test + `ast`
  import (FAM-1).

Proofs (all through `heavy`; workspace copy
slot-2, synced post-edit, `shared unmoved
since sync` on every run):

- `dry-20261010T020126-db9e35`:
  `pytest tests/management/test_inspect_django_type.py
  examples/...::test_inspect_connection_only_relation_shape_renders_row
  -n0 --no-cov -q` → 26 passed (FAM-1
  behavioral proof).
- `dry-20261010T020157-71c6b3`: `prove`
  (1 entry: re-inline one composer) →
  verdict pinned (exactly the gate row
  fails; 25/25 others green; sha256
  byte-identical restore).
- `dry-20261010T020255-55bac5`:
  `basedpyright` → 0 errors, 0 warnings, 0
  notes.
- `dry-20261010T020408-b665ab`:
  `basedpyright -p pyrightconfig.floor.json`
  → 0 errors, 0 warnings, 0 notes.
- `dry-20261010T020522-08db88`:
  `check_truthful_reads.py --check` →
  120 files, errors 0.
- Shared tree (the one authorized focused
  run): the new gate test alone → 1 passed.
- `check_public_types.py` not run: no public
  symbol touched (private helper + test
  only) — stated reason.
- `uv run ruff check --fix` + `uv run ruff
  format` on exactly the 2 touched `.py`
  paths → clean, no collateral (both files
  were ruff-clean pre-edit; post-edit diff
  holds only FAM-1 hunks).

`git status --short` count 528 (527 + this
artifact). No commit, no stash, no branch
operation. Scratch confined to
`$TMPDIR/dry-folder-mgmtcmds/` (3 probes +
1 manifest — outside the repo, kept for
Worker-2); no `docs/dry/temp-tests/`
scratch; the consolidate workspace copy
(slot-2) stays for Worker-2's `verify-1`
addressing (release is Worker-0's call).

## Independent verification (Worker-2)

### Trace provenance (sequencing disclosure)

This trace was derived from pins, the
item-scoped diff, the four target bodies
at WT, `git show HEAD:` / `BASE:` bytes,
and my own `rg` / AST censuses — all
recorded here BEFORE reading any finding
body. One exposure to disclose: to place
this section I listed the artifact's
heading map (`rg ^#{1,4}`), which names
per-section verdicts in one line each
(e.g. that a union-args pair and the
schema-symbol default were considered and
rejected). Mitigation: every position
below was already fixed by my own greps
before the map listing (populations,
counts, owner choice); the map told me
*nothing* about Worker-1's reasons, and
reconciliation judges those reasons
against my evidence, never inherits them.
A candidate the map does not obviously
cover (the `scalar_namer or _scalar_name`
idiom x5) stays an open question below.

### Pins re-derived (Worker-2)

HEAD `23b5f421` confirmed
(`git rev-parse`). `git hash-object` (WT)
vs `git rev-parse HEAD:` / `BASE:`:

- `commands/__init__.py`: WT `31cb58b8`
  = HEAD = BASE (clean).
- `commands/_imports.py`: `0b3faec4`
  everywhere (clean).
- `commands/export_schema.py`: WT
  `112390ff` = BASE, HEAD `9c4fceee` —
  its dirt predates the item.
- `commands/inspect_django_type.py`: WT
  `86785d55`, BASE `77eaff4f`, HEAD
  `86a308ab` — BASE pins match dispatch.
- `tests/.../test_inspect_django_type.py`:
  WT `c609de91`, BASE `de2711e9`, HEAD
  `e54a8dfa`.

### Item-scoped diff (Worker-2)

`git diff BASE -- <folder + tests>` names
exactly 2 files, matching the claim:
`inspect_django_type.py` (3 hunks: two
5-line call-site replacements + the new
helper) and `test_inspect_django_type.py`
(pure additions: `import ast` + census
helper + 1 gate test, 0 deletions).
New-file check: no new file under
`django_strawberry_framework/` or `tests/`
belongs to this item (the 9 untracked
paths there are all hunt-attributed:
`truth.py`, `lazy.py`, truth/lazy/multipart
tests, the live deadline test).
`HEAD..BASE` on the inspect file is pure
concurrent work (truth migration,
`_model_name`, a docstring citation fix).
Changed lines are HEAD==BASE-clean: the
two replaced 5-line blocks are byte-absent
from the `HEAD..BASE` diff, and the one
adjacency (hunk 2 context vs the
truth-migration f-string) is context-only —
the hunt line
(`truth.name(definition.origin)...`) is
preserved byte-identical at WT:459. At
HEAD the two blocks (HEAD:399-403,
HEAD:463-467) are identical modulo the
lookup key (`generated` vs `field.name`),
the genuine variation the helper
parameterizes as `python_name`.

### Folder enumeration (Worker-2, AST)

`ast.Module.body` top level: `__init__.py`
1 member (docstring); `_imports.py` 5
(`T` + 4 functions); `export_schema.py` 2
(docstring + `Command[add_arguments,
handle]`); `inspect_django_type.py` 7
module assigns + `Command` (12 methods) +
11 module functions (incl. new
`_strawberry_field_type`). In-repo
importers of the folder: the two
`Command` modules import `_imports`; the
only other hits are the folder's own 3
package test modules plus an unrelated
app-commands module and a tracked-path
constant list. The folder is a leaf CLI
surface: no GraphQL field, resolver, or
package runtime path imports it.

### FAM-1 — my own change challenge

Rule: fetch the finalized Strawberry
field list + find one field's `.type` by
`python_name`, missing name =
`StopIteration`. Sites at HEAD/BASE: (D1)
`Command._connection_only_relation_row`,
(D2) `Command._consumer_authored_row` —
both definitions (independently
maintained 5-line bodies: comment + cast
+ `.fields` read + `next` find).

- Change A (Strawberry moves/renames
  `.fields`, or the unfinalized-cast
  justification changes): D1 + D2 move =
  count 2.
- Change B (missing-name posture:
  `StopIteration` vs `CommandError` vs
  `None`): D1 + D2 move = count 2.
- Change C (find key: `python_name` vs
  another identity): D1 + D2 move =
  count 2.

Consumers: none beyond the two (post-fix:
both compose the helper). Oracles: the new
AST census gate + the two pre-existing
behavior rows (connection-only example
test asserting `IssueTypeConnection!` /
`relation: reverse FK (connection-only)`;
consumer-authored example + package tests
incl. the UNRESOLVED `CommandError`
test) — all spell expectations literally,
none reads the owner. Projections: the two
method docstrings (unchanged, still
accurate) + the helper docstring (moved
comment, same words).

Owner I choose: a private module-level
helper in `inspect_django_type.py`
taking `(definition, python_name)` —
exactly the landed shape. Alternatives
rejected by me: `Command` staticmethod
(needless class coupling; the module's
pure helpers `_matched_scalar_key`,
`_consumer_nullable` are already module
functions of the same arity shape); a
`DjangoTypeDefinition` method (widens a
shared record's surface for one CLI
consumer); `utils/` (couples utils to the
definition type — reversed dependency).
Second-site search beyond the folder:
`__strawberry_definition__.fields` reads
at `mutations/inputs.py` (x2) and
`mutations/sets.py` (x1) iterate
INPUT-class fields — no cast, no
find-by-name, different population and
contract, not the same rule;
`_sdl_type_name` / `_scalar_name` read the
definition OBJECT, not the fields list.
No third definition exists. Count at WT:
1.

Principle-8 equivalence (by inspection,
behavior tests cited above): same
exception type/value (`StopIteration`
from the same `next()` expression),
same short-circuit order, same
observation point (first statement after
the `scalar_namer` default in each
caller), no query/transaction/
cancellation surface; the extra stack
frame is not an observable axis.

### Missed-consolidation search (Worker-2)

Populations I censused myself, with my
own verdict BEFORE reconciliation:

- `scalar_namer or _scalar_name` x5 (4
  row methods + `_render_strawberry_type`;
  `_render_annotation` uses it as a
  default arg instead). Each site owns
  its optional test-seam parameter; the
  shared token is one default
  expression. My verdict: idiom, not a
  rule — no consolidation — but I did
  not see an obvious FR heading for it
  in the map, so reconciliation must
  confirm where it is discharged.
- `default_symbol_name="schema"` x2
  (both `handle` methods): same literal
  argument to the same owner. My
  verdict: two consumers composing one
  owner with the conventional value, not
  two definitions; a constant would be
  machinery (principle 11).
- `_RELATION_KIND_LABELS.get(kind, kind)`
  x2: the TABLE is the single owner; the
  two `.get` calls carry different
  adaptations (ForeignObject override vs
  `(connection-only)` suffix). My
  verdict: consumers, not a second
  definition — borderline, judge
  Worker-1's stated difference.
- Union-origin membership
  `(typing.Union, pytypes.UnionType)` x2
  (`_annotation_is_optional:497`,
  `_render_annotation:684`, same
  basedpyright comment; package-wide
  population is exactly these two).
  Change challenge: a 3.14 spelling
  change moves both. My verdict: real
  shared sub-rule but different
  contracts (bool predicate vs render
  dispatch — the renderer also handles
  multi-member unions the predicate
  never sees); sharing needs a
  `_union_args`-shaped helper both call
  shapes must bend to. Lean REJECT, but
  this is the one pair I derived that
  could legitimately go either way —
  reconciliation judges Worker-1's
  difference + trigger on the merits.
- `raise CommandError` x14 (4 + 4 + 6
  per file): per-subject wordings, each
  site its own contract; cause policy
  (`from e` + `str(e)`) single-owned in
  `import_or_command_error`, with the
  export `--path` write arm a different
  exception contract (`OSError` /
  `ValueError`). My verdict: no merge.
- `_consumer_nullable` (2 consumers),
  `_render_strawberry_type` (2 +
  recursion), `_render_annotation` (2 +
  recursion), `import_or_command_error`
  (2), `_validate_absolute_module_path`
  (2): all already single-owned with
  exact censuses. The two renderers
  differ by input domain (Strawberry
  wrappers vs typing annotations),
  not by spelling.
- Table column widths (`<20`/`<32`/`<10`
  header + separator + row): all three
  live in the single method
  `_print_table` — one owner already.
- `UNRESOLVED` guard only in the
  consumer row (axis 6): the connection
  sibling is finalization-synthesized,
  never a forward ref — omission is
  structural, not a gap, pending the
  contract source Worker-1 cites.

### Matrix on the real surface (Worker-2)

1. Cross-flavor: the two commands share
   `_imports` by name; CLI surface is
   unique (no sibling flavor re-spells
   it). 2. Sync/async: inapplicable —
   both commands are sync-only
   `BaseCommand.handle` with no await
   boundary and no async twin anywhere.
3. Derived knowledge: `_GRAPHQL_SCALAR_NAMES`
   merges `_PACKAGE_SCALAR_MAP` by name
   (no re-derivation); field sets come
   from `definition.*` records; SDL
   names via the converter, never
   concatenation. 4. Round-trip:
   inapplicable — render-only
   diagnostics, no parse/encode half
   exists. 5. Other media: docstrings +
   literal-spelling tests + spec prose;
   each behavior row has an independent
   oracle (verified by reading bodies,
   e.g. the `IssueTypeConnection!`
   assertion). 6. Omission: families
   enumerated above (UNRESOLVED guard,
   `scalar_namer` defaults x5 complete,
   import translation complete via
   `_imports`).

### Cell inapplicability (Worker-2)

SOUND by construction: `rg` over the
folder finds no database, alias, or
dialect surface (the only
`connections` hits are the GraphQL
`relation_connections` record); the
touched test file has no `django_db`,
no `.objects.`, no transaction use —
model CLASSES serve as metadata
fixtures only. Both commands read
in-process type metadata and print
text; sharded/pg cells cannot observe
a difference.

### Reconciliation (Worker-2 vs Findings)

Substance: full agreement, no divergent
verdict. FAM-1 sites/counts/owner match
my trace exactly (2 defs at HEAD/BASE on
every axis I posited — Worker-1's C40/C41
plus my key-identity axis — 1 at WT;
module helper, same rejected
alternatives); the mutations-side
exclusion matches my census (3 reads,
input-class iteration, no cast/find).
Every missed-consolidation candidate I
derived is discharged: the `scalar_namer`
idiom x5 as C58 (0 here, owner
`_scalar_name` — my census of 5
or-defaults + partial + default-arg
matches byte for byte); the schema
default as FR-7 (Worker-1's
required-parameter argument is stronger
than mine — accepted); the label
fallback as FR-9 (the real-axis-moves-1
argument resolves my borderline —
accepted); the union pair as FR-10 (the
None-less-union-renders-multi point is
decisive — my lean-reject becomes a
firm reject). Matrix axes 1:1 with mine,
including both inapplicability claims
(zero `AsyncFunctionDef`/`await`,
render-only diagnostics — re-verified).
Enumeration 1/11/9/45 matches my AST
exactly; 66/66 homing arithmetic holds.
No oracle rewritten (test diff pure
additions); new gate at the mandated
tier (AST-over-source, unexecutable
from any GraphQL path by construction);
added lines banned-word clean
(re-swept); ruff format-check + check
green on both paths (re-run). No
coupled findings (FAM-1 touches
neither dispatch nor predictor —
verified by diff). `check_any` absent
from the artifact; public-types
correctly skipped (private helper
only). Pending execution: no `proof:`
(correct — I re-verified the behavior
proof's 25 rows plus failability in my
own copy), 7 `gate:` entries all
witnesses, correctly typed. FC-3/FC-4
blocks confirmed by diff content: the
predictor body + its citation hunk and
the `_matched_scalar_key` walk are hunt
dirt (`HEAD..BASE`), the owners live in
hunt-dirtied files, owner 0 hits, both
family artifacts record blocked-on-hunt.
Inapplicability: SOUND (my own
derivation above stands unmodified).

Corrections (transcription-level;
analysis unaffected — Worker-0
transcribes the corrected text):

- C-ROW-11 (Worker-2): the row pins
  "`truth.kind` message" but HEAD's
  guard spells
  `type(...).__name__` — `truth.kind`
  is unlanded hunt dirt. Transcribe
  instead: `management-export-schema-location-type-gate`
  | `.../export_schema.py::Command.handle`
  non-str schema guard (direct-handle
  bypass; names the received kind).
  (Also drops the transient "NEW in"
  pin.)
- C-ROW-15 (Worker-2): the predictor
  half is held by open Family
  `relay-pk-suppression-read-mirror`
  (its index row covers this file) —
  claiming it file-local double-homes
  it (sibling precedent: family-held
  halves get Family holding, never
  file-local). Transcribe instead:
  `management-inspect-suppressed-relay-pk-row`
  | `...::_GLOBAL_ID_GRAPHQL_TYPE` +
  `::_RELAY_PK_CONVERTER` + the `no`
  token in `::Command._resolve_row`
  (suppressed-pk row display literals;
  predictor held by Family
  `relay-pk-suppression-read-mirror`).
- C-FF-1 (Worker-2): "four rows each
  pin `5ee86193`" is three — init,
  `_imports`, export pin the commit;
  the inspect row already pins
  `2807d0fc` via run-7. Remedy
  endorsed with corrected scope:
  re-pin the three to `31cb58b8` /
  `05e9de80` / `e27adae9` (all
  confirmed: member artifacts +
  `git show 5ee86193:`) or drop.
  `46dffb3d` confirmed as the inspect
  09-18-era blob (no action needed).

Freshness supplement (Worker-2):
FAM-1's body-strength exclusions lacked
fingerprints — `mutations/inputs.py`
WT `bb329e4d` / HEAD `f821661e`,
`mutations/sets.py` WT `6f2fa2f9` /
HEAD `a123aea8` (read at verification
time; exclusion re-derived, stands).
All artifact pins spot-checked current
(no drift).

Observation (non-blocking): the `gate:`
list omits the live-export tier; the
final gate's full suite covers it.

Row rulings (all 24 + correction):
endorse rows 1-10, 12-14, 16-24;
CORRECT rows 11, 15 (text above);
endorse the FF-1 re-pin-or-drop remedy
with the C-FF-1 count fix. FF-2/FF-3/FF-4:
evidence re-derived and confirmed
(0 plan hits + 0 holding rows + 3+8
member citations; HEAD 3+5 sites
present, WT 0+0 absorbed into
untracked concurrent `truth.py`;
7/40 pins + exact +5 delta);
non-reopening correct in each case.
Defect releases: all three evidentiary
claims verified (spec-029's seven
populations enumerated sans non-str;
finalizer `:673` many-side gate; relay
D1 in the family artifact; wire-reach
grounded in the oracle docstring) —
release correct, no maintainer routing owed
(no feasible wire input reaches any).

Gate re-runs (Worker-2, own copy
slot-3, `shared unmoved` throughout):
basedpyright `dry-20261010T022018-a4d3bd`
0/0/0; floor `dry-20261010T022134-a27760`
0/0/0; truthful-reads
`dry-20261010T022245-2a0924` 120 files
errors 0; negative control
`dry-20261010T022313-ba8dda` — gate
FAILS with exactly the expected
multiset diff, other 25 rows green,
byte-identical restore. Shared tree:
the one authorized focused run, new
gate test 1 passed. Consolidation
type-checks with zero new
cast/widening/suppression (cast moved
verbatim; `-> object` matches the
file's existing treatment), no `Any`.

Verdict: verified. No production gap,
no missed consolidation, no stale
fingerprint; the three corrections are
Worker-0 transcription text.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-export]: dry-file-management__commands__export_schema.md
[file-imports]: dry-file-management__commands___imports.md
[file-init]: dry-file-management__commands____init__.md
[file-inspect]: dry-file-management__commands__inspect_django_type.md
[file-testing-relay]: dry-file-testing__relay.md
[file-types-definition]: dry-file-types__definition.md
[file-types-finalizer]: dry-file-types__finalizer.md
[file-utils-imports]: dry-file-utils__imports.md
[file-utils-relations]: dry-file-utils__relations.md
[file-utils-typing]: dry-file-utils__typing.md
[rule-mro]: dry-rule-mro-map-key-lookup.md
[rule-relay]: dry-rule-relay-pk-suppression-read-mirror.md

<!-- docs/SPECS/ -->
[spec-022]: ../SPECS/spec-022-export_schema-0_0_7.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[commands-imports]: ../../django_strawberry_framework/management/commands/_imports.py

<!-- tests/ -->
[test-export-schema]: ../../tests/management/test_export_schema.py
[test-imports]: ../../tests/management/test_imports.py
[test-inspect]: ../../tests/management/test_inspect_django_type.py

<!-- examples/ -->
[live-export]: ../../examples/fakeshop/tests/test_export_schema.py
[live-inspect]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
