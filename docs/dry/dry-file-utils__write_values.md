# DRY review: `utils/write_values.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits.

## System trace

Target `django_strawberry_framework/utils/write_values.py` is the flavor-neutral
owner of the per-value write checks every write flavor runs at decode time:
the invalid-Unicode storability preflight, choice-enum unwrapping, raw
relation-pk coercion, the GlobalID-or-raw-pk structural check, the scalar-leaf
compose, the single-relation visibility spine, the batched id-set decode, the
SCALAR / RELATION / FILE store-into-dest vocabulary, and the kind-routed walk
over a bound write input. Its module docstring states the nine-bullet shape
once. The file defines no queryset scoping of its own: both relation decoders
consume `utils/querysets.py` visibility primitives by name.

Target identity and attribution. HEAD blob
`d28587c7c8d9f0d25e0a01bf289a63d9c3291728` (494 lines); worktree blob
`13548c76605ec264cf95e7d10dc6a8bc813b360d` (524 lines). `git diff HEAD`
shows 7 hunks, 63+/33-, all attributed by content to concurrent-external
(hunt) work, none to this item (which made zero edits):

- Hunk 1 (module docstring): `decode_visible_relation_ids` bullet gains
  "batched NodeID mapping" wording. Prose half of hunk 7.
- Hunk 2 (imports): `from . import truth` added. `utils/truth.py` is
  absent at HEAD (untracked hunt file); the whole `utils/` tree carries
  the same `truth.*` migration dirt.
- Hunk 3 (`coerce_relation_pk_or_none`): the `_meta` read goes through
  `truth.static_attr`. Same migration.
- Hunk 4 (`type_check_relation_id` docstring): "WITHOUT a DB fetch" /
  "Neither branch touches the DB" rewritten to admit the GlobalID
  branch's NodeID-resolve query. Prose half of hunk 7; see O1.
- Hunks 5-6 (`materialize_relation_id_container`): "hostile iterator"
  prose narrowed; `except BaseException` narrows to `except TypeError`.
  Truthful-reads gate conformance (hunt's `scripts/check_truthful_reads.py`
  bans `BaseException` swallowing).
- Hunk 7 (`decode_visible_relation_ids` body): per-element
  `type_check_relation_id` loop replaced by a GlobalID/raw-pk split
  riding `relay.py::_decode_and_coerce` + `_resolve_real_pks_batched`.
  Both helpers are absent at HEAD `relay.py` (HEAD `c3c5aea5`; they
  exist only in worktree `f5760b45`) — the consumer half of hunt's
  relay batching change.

No `## Owned changes` ledger row names this file. `ITEM_BASELINE`
(`fe63056fcb082b85aa843e031f77dbc7233497e6`, a stash commit) resolves
this path to `13548c76`, identical to the worktree blob, proving zero
worktree change since the item baseline: the dirt predates this item.
This trace reads HEAD bytes only; worktree bytes are fingerprinted,
never reasoned from. The dirt's behavior deltas (the batched NodeID
resolve, the narrowed catch, the `truth` reads) are
observed-not-adjudicated: concurrent work outside this item.

Consumers, classified (HEAD bytes; every worktree counterpart is dirty,
so every citation below was re-derived via `git show HEAD:` /
`git archive HEAD`). Production callers:

- `mutations/resolvers.py` (HEAD `043a2d0b`): six names
  (`coerce_relation_pk_or_none`, `decode_provided_fields`,
  `decode_scalar_leaf`, `decode_visible_relation_ids`, `decoded_into`,
  `relation_into`). Scalar decode wraps the leaf with the model
  null-guard + naive-datetime coercion (:407-415); FK wraps one id
  into the batched set decoder (:523), M2M delegates after the
  null-reject (:558); the non-Relay `id:` locate arm coerces via
  `coerce_relation_pk_or_none` (:1241); the handler map composes
  `relation_into` / `decoded_into` directly (:418-443, incl. the
  model-only `EXCLUDED` arm).
- `forms/resolvers.py` (HEAD `35c282cc`): four names
  (`decode_field_handlers`, `decode_provided_fields`,
  `decode_visible_relation`, `materialize_relation_id_container`).
  Single colors the spine with `empty_values` skip + `to_field_name`
  projection (:200); multi materializes the container then maps the
  single per element (:243-260); the walk splits `provided_files`
  for Django `files=` (:293-308). Both form bases ride
  `_decode_form_data` (:449).
- `rest_framework/resolvers.py` (HEAD `0d302782`): five names
  (`decode_field_handlers`, `decode_provided_fields`,
  `decode_visible_relation`, `decode_visible_relation_ids`,
  `decoded_into`). Single colors the spine with None-skip + `obj.pk`
  projection (:233); multi batches (:262); nested recursion arrives
  via `decoded_into` + `extra_handlers` (:333-345); FILE lands in
  `data` (no `file_dest` split).
- `auth/mutations.py` (HEAD `d1a59c44`): `unencodable_text_error`
  only, via two function-local imports (login calls :636-637,
  register password call :1136). Pure consumption.
- Mention-only (docstring cites, zero calls): `mutations/sets.py`
  (:1044, :1527), `utils/querysets.py` (:318, :4221, :4275, :4298),
  `filters/base.py` (:483), `mutations/inputs.py` (:519),
  `utils/inputs.py` (:1220), `utils/errors.py` (:68, :325).

Internal-only members (no production caller outside the file):
`raw_choice_value`, `type_check_relation_id` (consumed by the leaf /
spine / batched bodies), `RELATION_ID_ATOM_TYPES`, `store_decoded`,
`scalar_into`, `file_into`, `_spec_field_name`, `_no_relation_extra`.
`tests/utils/test_write_values.py` (HEAD `8d09921b`, 27 tests) pins
`store_decoded` / `scalar_into` / `file_into` / `relation_into` /
`decoded_into` directly and the rest through the public bodies; the
GraphQL-representable envelopes live in the live tier
(`test_products_api.py`, `test_library_api.py`), which spell the
relation-error message independently.

Dependencies consumed by name (HEAD bytes): `utils/errors.py`
(`field_error`, `relation_field_error`, `FIELD_ERROR_CODE_INVALID`;
HEAD `3e25e93b`), `utils/inputs.py` (`FILE`, `RELATION_SINGLE`,
`RELATION_MULTI`, `iter_provided_input_fields`, the single
`InputFieldSpec` record; HEAD `ee31d360`), `utils/querysets.py`
(`coerce_field_value_or_none`, `pks_all_present`,
`visible_related_object`, `visible_related_objects`; HEAD
`3616927d`), `relay.py::decode_model_global_id` (function-local
import, cycle dodge; HEAD `c3c5aea5`), `mutations/inputs.py::FieldError`
(TYPE_CHECKING only).

## Verification

### Enumeration

Instrument: `ast.Module.body` walk over HEAD bytes (`d28587c7`,
494 lines), cross-checked against the worktree walk (same 28-node
shape plus the one hunt import). 28 top-level nodes: module
docstring, 8 imports, the `TYPE_CHECKING` block, 1 constant, 17
function definitions. Every member is homed:

| # | Member (HEAD line) | Home |
|---|---|---|
| 1 | module docstring (:1-20) | L1 |
| 2-9 | 8 imports (:22-37) | L1 |
| 10 | `TYPE_CHECKING` block (:39-43) | L1 |
| 11 | `unencodable_text_error` (:45) | L2 |
| 12 | `raw_choice_value` (:79) | L3 |
| 13 | `coerce_relation_pk_or_none` (:97) | L5 |
| 14 | `type_check_relation_id` (:119) | L6 |
| 15 | `decode_scalar_leaf` (:161) | L4 |
| 16 | `decode_visible_relation` (:184) | L7 |
| 17 | `RELATION_ID_ATOM_TYPES` (:236) | L8 |
| 18 | `materialize_relation_id_container` (:245) | L9 |
| 19 | `decode_visible_relation_ids` (:270) | L10 |
| 20 | `_spec_field_name` (:318) | L11 |
| 21 | `_no_relation_extra` (:323) | L11 |
| 22 | `store_decoded` (:328) | L11 |
| 23 | `decoded_into` (:348) | L11 |
| 24 | `scalar_into` (:364) | L11 |
| 25 | `file_into` (:380) | L11 |
| 26 | `relation_into` (:391) | L11 |
| 27 | `decode_field_handlers` (:422) | L11 |
| 28 | `decode_provided_fields` (:465) | L12 |

No member is left unassigned. The file defines no classes, no async
bodies, no queryset construction (`objects.` / `.filter(` / `.get(`
/ `.exclude(` / `await` all absent at HEAD), and no second spelling
of any rule it owns.

### Matrix

Discharged against HEAD bytes (`d28587c7`); the worktree-only
GlobalID split inside `decode_visible_relation_ids` (hunk 7) is hunt
dirt and forms no part of any axis verdict.

1. **Cross-flavor policy mirroring.** Searched. The three write
   flavors (model / form / serializer) plus auth are the whole
   consumer population; every shared decode step is already promoted
   here and consumed by name (call-site census in System trace).
   Flavor-kept colorings verified intentional at their bodies: model
   null-reject + naive-datetime wrap, form `empty_values` /
   `to_field_name`, serializer None-passthrough + nested recursion +
   FILE-into-`data`. The model's FK-single rides the batched body
   rather than the spine (same contract as its M2M path, stated at
   `mutations/resolvers.py:494-507`) — consumer routing over shared
   bodies, not a second definition (R5). Form multi maps the single
   per element because it needs the object for `to_field_name`;
   model/serializer multi batch because they need pks only (R5).
2. **Sync/async twins.** Inapplicable with reason: all 17 bodies are
   sync; the write pipeline runs synchronously inside one
   `sync_to_async` boundary on the async surface (the three
   `_ASYNC_RECOURSE` wordings, single-sourced via
   `sync_pipeline_recourse`, name exactly this), and the visibility
   primitives raise `SyncMisuseError` on an `async def get_queryset`
   rather than awaiting it. No async twin exists or is owed; an
   `async_recourse: str` parameter is threaded, never branched on.
3. **Derived rather than repeated knowledge.** Searched. The decode
   reads one shared record (`utils/inputs.py::InputFieldSpec` — the
   only spec class in the package) by attribute (`input_attr`,
   `graphql_name`, `target_name`, `kind`, `related_model`); nothing
   is re-derived (`related_model` is build-recorded, never
   re-discovered per request; the form body states why at
   `forms/resolvers.py:181-186`). The `_meta.pk` read in
   `coerce_relation_pk_or_none` is the caller's field pick for the
   shared coercer (A3), not a pk derivation. The `{spec.input_attr:
   spec}` map (:486) is the sole decode-time build; the
   build-time collision audit (`utils/inputs.py:1487-1513`) maps the
   same key to a different value (declaration site, for
   clash detection) in a different phase — distinguished in L12.
4. **Inverse / round-trip pairs.** Searched. GlobalID decode is
   consumed (`relay.py::decode_model_global_id`); the encode half
   lives in `types/relay.py` + `testing/relay.py` and no second
   decode exists here (the worktree `_decode_and_coerce` split is
   hunt dirt). `materialize_relation_id_container` (`list()` once)
   has no un-materialize; the provided-fields walk (input→dict) has
   no dict→input inverse here — the build side is the flavor input
   modules over the single `InputFieldSpec` record. No pair owed.
5. **Contracts restated in another medium.** Classified. Production
   definitions: this file (L2-L12). Consumers: the four resolver
   modules + auth (listed, not counted). Independent oracles:
   `tests/utils/test_write_values.py` spells literals (`"invalid"`,
   `"displayName"`, hostile subclasses, `True`-identity checks) and
   never imports an owner constant for its expectations; the live
   tier spells `"Invalid id for relation 'categoryId'."` twice
   (`test_products_api.py:1140,5119`). Projections: spec-036/038/039
   decision prose cited in docstrings, the glossary `DjangoMutation`
   entry, and the consumer docstrings restating each spine contract
   at the call site (forms :266-290, serializer :294-321, model
   :499-562). No medium restates a rule as a second definition.
6. **Enforcement by omission.** Enumerated the write-flavor × decode-step
   matrix at HEAD: scalar leaf — model direct (:412), form + serializer
   via `scalar_into`, auth login/register via the bare preflight
   (undifferentiated-envelope contract, no choice axis on
   credentials); relation visibility — model FK+M2M batched, form
   single+multi (per-element, object-needing), serializer
   single+multi (batched); container materialize — batched body +
   form multi direct (its per-element map cannot ride the batch).
   Model-less `DjangoFormMutation` rides the same `_decode_form_data`
   (`forms/resolvers.py:449`). `EXCLUDED` is model-emitted only and
   `NESTED_*` serializer-emitted only, by construction of the flavor
   builds (A6); unknown kinds fall back to `scalar_handler` by
   design (scalar is the default, `SCALAR` never appears in a
   handlers map). Null policy stays at callers (model rejects,
   form/serializer defer to bound validation) — three stated
   contracts, not a missing guard. No omission without a contract
   source; nothing routes to the maintainer.

### Challenges

Each rule challenged on its variation axes; counts are authoritative
definitions that must move together (consumers / oracles /
projections listed, never counted).

- L2 preflight: (a) "reject NUL as well as surrogates" → 1 (the
  `encode` test); auth ×2 + leaf ride it. (b) "a fifth flavor
  preflights credentials" → 0 new (calls it; auth is the proof).
  (c) "non-string JSON scalars need recursive preflight" → 1
  (the passthrough arm).
- L3 unwrap: (a) "unwrap must recurse into lists" → 1 here; filters
  `_unwrap_enum_member` explicitly declines the same change in its
  docstring (R1). (b) "choice values need lazy-str resolution" →
  1 (the `str.__str__` tail); no second tail exists.
- L4 leaf order: (a) "preflight must run before unwrap" → 1 (the
  two-line compose); the ordering test pins unwrap-first. (b) "a
  fourth flavor adds a scalar step" → 0 here (composes around the
  leaf; model null/datetime are the proof).
- L5 pk coercion: (a) "coercion must skip validators" → 0 here, 1
  in `coerce_field_value_or_none` (consumer; A3). (b) "a caller
  coerces against a non-pk field" → 0 (the field pick is the
  caller's arm; relay/filter prove it).
- L6 structural check: (a) "a third id shape (signed token)" → 1
  (the two-branch body); spine + batched ride it. (b) "GlobalID
  decode gains a status" → 0 here, 1 in `relay.py` (consumer of
  the status enum). (c) "raw-pk branch must query" → 1 (still
  query-free at HEAD by construction).
- L7 spine: (a) "skip must distinguish None from empty" → 0 here
  (adapter param; form vs serializer prove it). (b) "projection
  needs the info" → 1 (the `project(obj)` call shape) + 2
  adapter edits (consumers). (c) "visibility must use the
  object-set query" → 0 here, 1 in querysets (A1).
- L8 atoms: (a) "a sixth atom type" → 1 (the tuple); the errors
  twin moves only if its own contract changes (A4).
- L9 materialize: (a) "generators must stream, not list()" → 1
  (the `list(values)` line); the once-only test pins it. (b) "a
  new atom kind" → 0 (L8 owns the set).
- L10 batched: (a) "empty set must query" → 1 (the `if not pks`
  arm). (b) "subset compare must be type-strict" → 0 here, 1 in
  `pks_all_present` (consumer). (c) "per-element errors must
  accumulate" → 1 (the short-circuit loop).
- L11 vocabulary: (a) "a new kind needs a default dest" → 1
  (`decode_field_handlers` map; `extra_handlers` spread is the
  serializer proof). (b) "store must merge, not overwrite" → 1
  (`store_decoded`). (c) "scalar errors must key to target" → 1
  (`_spec_field_name` default) + 1 adapter (serializer nested
  prefix, consumer).
- L12 walk: (a) "omitted fields must reach handlers" → 0 here, 1
  in `iter_provided_input_fields` (consumer). (b) "unmapped attrs
  must raise" → 1 (the `continue` arm). (c) "handlers must
  accumulate errors" → 1 (the short-circuit return).
- A1 visibility: "the recheck must pin the write alias on reads"
  → 0 here (pure consumer via `visible_related_object(s)`).
- A2 envelope: "relation message gains a code" → 0 here, 1 in
  `utils/errors.py` (6 call sites ride it).
- R1-R8: each names the change that would collapse the pair as
  its trigger; all unfired at HEAD.

Behavioral proof: `static-reviewed` throughout (zero-edit file
item; every body composed by name, every census re-derived from
HEAD bytes). No finding needs execution: no ordering, transaction,
or async claim is made about this file's own bodies.

## Findings

### A1 — CONSUME open `related-object-visibility-recheck` (transcribes nothing)

Write_values holds zero visibility-scoping definitions at HEAD: the
single spine calls `visible_related_object` (:226) and the batched
body calls `visible_related_objects` (:312) plus `pks_all_present`
(:313), all by name; the file constructs no queryset (axis grep in
Enumeration). The open family's F5 contrast (`visible_related_object`
vs `types/resolvers.py::_visible_related_object`, both still at
HEAD — querysets :4308, types/resolvers :395 with 7 call sites) is
unaffected by anything here: this file is a consumer of the first
arm only. The family row already lists this file; the F5 append
(mutations/resolvers transitive consumer) matches the fresh census
(model FK :523 + M2M :558 ride the batched body). Converged, not
adopted: no new definition, no new row owed.

### A2 — CONSUME verified `mutation-error-envelope` (transcribes nothing)

`field_error` ×1 (:71), `relation_field_error` ×6 (:153, :157,
:228, :263, :267, :314), `FIELD_ERROR_CODE_INVALID` ×1 (:74) —
every relation rejection in the file rides the consolidated leaf
constructors by name, with the GraphQL wire name threaded as the
key. The family artifact already fingerprints this file at
`d28587c7` and lists it. No per-flavor error alias survives here
(spec-039 folded them). Converged; no row owed.

### A3 — CONVERGE with rejected `field-value-coercion` F6 (transcribes nothing)

`coerce_relation_pk_or_none` (:115-116) still composes
`coerce_field_value_or_none` by name against `_meta.pk` at HEAD —
the "WHICH field stays at the caller" split F6 endorses. Trigger
re-checked unfired: `pks_all_present` has exactly one production
caller (this file :313) whose pks passed `type_check`
first (:301-309), and `stringified_pks_present` is called only
from inside `visible_related_objects` (querysets :4374). The
three-consumer census (relay `_coerce_pk_or_none`, this body,
filters `_coerce_int_in_members`) reproduces at HEAD. Converged;
no row owed.

### A4 — CONVERGE with rejected `errors-text-atoms-vs-relation-id-atoms` (transcribes nothing)

Bilateral separation intact at HEAD: `RELATION_ID_ATOM_TYPES`
(:233-243, adds `Mapping`) and `errors.py::_TEXT_ATOM_TYPES`
(`errors.py:69-75`, adds `Promise`) cite each other by name in
adjacent comments, each stating why its set differs (a message
atom vs a never-a-container atom). Converged; no row owed.

### A5 — CONVERGE with rejected `write-txn-pk-vs-coercion` (transcribes nothing)

`canonical_pk` (to_python-only equality, raises) vs this file's
coercion (to_python + validators, None) still answer "same row?"
vs "may this literal enter a query?" at HEAD; neither body moved
since the standing verdict (`write_transaction.py` HEAD
`eca9ad4d`, this file `d28587c7`). Converged; no row owed.

### A6 — CONVERGE with rejected `excluded-unreachability` (transcribes nothing)

`EXCLUDED` specs are emitted only by the model build
(`mutations/inputs.py:87` kind; model handler map
`mutations/resolvers.py:442`); form/serializer builds never emit
the kind, so their `decode_field_handlers` maps legitimately lack
the arm, and `decode_provided_fields`' scalar fallback is the
designed default, not a hole. Same construction holds for
serializer-only `NESTED_*` (via `extra_handlers`). Converged; no
row owed.

### L1 — Module mechanics (file-local)

Docstring (:1-20, nine-bullet shape manifest), 8 imports (:22-37,
all consumed: `Mapping` by L8, `Enum` by L3, `relay` by L6,
errors/inputs/querysets by the bodies), `TYPE_CHECKING`
`Callable` + `FieldError` (:39-43, annotation-only under
`from __future__ import annotations`). No `__all__` (utils-leaf
posture: imported by path). Challenge "a ninth import / a tenth
bullet" → 1. File-local: no second site states this module's
shape.

### L2 — Unencodable-text storability preflight (file-local)

`unencodable_text_error` (:45): lone-surrogate strings are
rejected at decode as a field-keyed `FieldError` before any
DB-bound work; non-strings pass through. The base-`str`-slot read
(`str.__str__(value).encode("utf-8")`) never dispatches a
consumer subclass override (pinned by the hostile-subclass
oracles). Consumers: L4 leaf + auth login (:636-637) + auth
register password (:1136, bypasses the leaf via the D6 exclusion
seam — stated at the call site). Challenge (a)-(c) → 1/0/1. File-local:
package census finds no second storability preflight (R2
distinguishes the measurer).

### L3 — Choice-enum unwrap + storage-str normalize (file-local)

`raw_choice_value` (:79): `Enum` member → `.value`, then
`str.__str__` normalization so a stored string is an exact `str`,
never consumer code (pinned by the normalize oracle). Explicit
`None` stays `None`. Sole consumer: L4 leaf. Challenge → 1; the
filters twin explicitly declines the same variation (R1).
File-local.

### L4 — Scalar-leaf compose order (file-local)

`decode_scalar_leaf` (:161): unwrap (L3) MUST precede preflight
(L2) — a member is not a string while its storage value can be
one (pinned by the invalid-choice-value oracle). Consumers: model
direct (:412, wrapped with flavor null/datetime steps),
form + serializer via `scalar_into`. Challenge → 1/0.
File-local: the compose exists once; flavor scalar steps stay at
call sites by design.

### L5 — Raw-pk coercion against the target pk field (file-local)

`coerce_relation_pk_or_none` (:97): the caller's field pick
(`related_model._meta.pk`, tolerant `None` → coercer returns
`None`) for the shared coercer (A3). Out-of-range/uncoercible →
"identifies no row", never a backend crash. Consumers: L6 raw-pk
branch + model `coerce_lookup_id` non-Relay arm
(`mutations/resolvers.py:1241`). Challenge → 0/0 here (1 at the
owned coercer). File-local: the field pick exists once per
caller by the endorsed split.

### L6 — Two-branch relation-id structural check (file-local)

`type_check_relation_id` (:119): GlobalID →
`decode_model_global_id` (non-OK → uniform error) | raw pk → L5
(None → uniform error). The single definition of "well-formed
relation id" all three flavors share; the relay import stays
function-local (cycle dodge, stated). Consumers: L7 spine + L10
per-element loop (:300-309). At HEAD the raw-pk branch is
query-free; the GlobalID branch queries only for a non-pk
concrete NodeID attr (see O1 — the "WITHOUT a DB fetch" title
overclaims that narrow case; hunt hunk 4 already rewrites it).
Challenge → 1/0/1. File-local.

### L7 — Single-relation decode spine + skip/project adapters (file-local)

`decode_visible_relation` (:184): skip → L6 → visible object
(A1) → project. Owner of the cross-flavor invariant "a writer
never attaches a row it cannot see"; hidden/missing collapse to
one error (no existence leak). Adapters keep flavor policy out:
form `empty_values`/`to_field_name`, serializer None/`obj.pk`.
Consumers: form single + serializer single. Challenge → 0/1/0.
File-local.

### L8 — Relation-id atom set (file-local)

`RELATION_ID_ATOM_TYPES` (:236-243): str/bytes/bytearray/memoryview/
Mapping are never a container OF ids. Sole consumer: L9. Challenge
→ 1. File-local (A4 converges the errors twin).

### L9 — Materialize-before-decode container rule (file-local)

`materialize_relation_id_container` (:245): atoms rejected
outright; the iterable listed ONCE before any member decode
(pinned by the generator oracle); a non-iterable collapses to
the uniform envelope (HEAD `except BaseException` — R8 converges
the standing except-guard direction; hunt hunk 6 narrows it,
observed-not-adjudicated). Consumers: L10 + form multi (:243).
Challenge → 1/0. File-local.

### L10 — Batched id-set decode (file-local)

`decode_visible_relation_ids` (:270): type-check every element
first (short-circuit before the visibility query), `[]` without
touch (valid M2M clear), one `pk__in` visibility confirm (A1),
hidden/missing → uniform error. Flavor null policy stays at
callers (model rejects, serializer passes through). Consumers:
model FK (:523) + M2M (:558), serializer multi (:262).
Challenge → 1/0/1. File-local.

### L11 — Store-into-dest handler vocabulary (file-local)

`store_decoded` (:328, short-circuit-or-store under
`target_name`), `decoded_into` (:348, decode-then-store glue),
`scalar_into` (:364, L4 + store, re-keyable), `file_into`
(:380, Upload passthrough to the flavor dest), `relation_into`
(:391, single/multi sub-pick + shared kwargs + flavor extras),
`decode_field_handlers` (:422, the map + scalar pair, `file_dest`
split + `extra_handlers` spread), `_spec_field_name` (:318) +
`_no_relation_extra` (:323) defaults. The model rider composes
the `*_into` primitives directly (its FILE/M2M dest policies
replace every default but RELATION_SINGLE — stated at :444-446);
serializer nested recursion arrives via `extra_handlers`.
Challenge → 1/1/1. File-local: one vocabulary, three riders.

### L12 — Kind-routed provided-fields walk (file-local)

`decode_provided_fields` (:465): sole `{spec.input_attr: spec}`
build, `UNSET`-stripped walk (consumed from
`iter_provided_input_fields`), kind dispatch with scalar default,
first-error short-circuit. Consumers: all three flavors
(forms :301, model :444, serializer :345). The build-time
collision audit maps the same key to declaration sites in a
different phase — distinguished, not duplicated (Matrix axis 3).
Challenge → 0/1/1. File-local.

### R1 — Enum unwrap vs filter normalize unwrap (rejected)

`raw_choice_value` (L3) vs `filters/inputs.py::_unwrap_enum_member`
(:682-701). Shared form considered: one Enum→.value helper.
Contract difference: the write unwrap feeds storage — member →
raw choice value → exact-`str` normalize → preflight-ordered
(L4); the filter unwrap feeds a django-filter form `clean` —
member → `.value` as-is, explicitly single-level with nested
shapes declined to a future per-level walk. Posit "unwrap must
recurse" → the filter body is the one that would grow it, the
write body never sees nested enums (M2M ids are GlobalID/raw
pk); posit "storage must reject lazy strings" → only the write
tail moves. Trigger: a read surface needing the exact-str
posture, or a write input carrying nested enums.

### R2 — Storability preflight vs budget measurement (rejected)

`unencodable_text_error` (L2) vs
`extensions/resource_policy.py:795` (`str.encode(value, "utf-8",
errors="surrogatepass")`). Shared form considered: one
surrogate-aware UTF-8 rule. Contract difference: reject (fail
closed, field-keyed) vs measure (must never raise — a budget
walker that rejects is a denial-of-service lever). Posit "NUL
joins the reject set" → only L2 moves; posit "budgets count
graphemes" → only the measurer moves. Trigger: a single policy
needing both verdicts from one call.

### R3 — Write id check vs filter GlobalID decode (rejected)

`type_check_relation_id` (L6) vs
`filters/base.py::_decode_and_validate_global_id` (:715).
Shared form considered: one GlobalID-or-literal decode.
Contract difference: write-side pair-returning envelope input
(model identity via `decode_model_global_id`, no strategy
validation — the generated input exposes one shape) vs
read-side raising filter predicate (strategy-aware type-name
validation, `GLOBALID_INVALID` / `GLOBALID_UNVALIDATABLE` coded
errors, empty-id-as-widening refusal). Posit "filters gain a
fourth strategy" → only the filter body moves; posit "write
inputs validate type names" → only L6 moves. Trigger: a shared
strategy-membership rule both sides must honor.

### R4 — Write id check vs relay node-id unwrap (rejected)

`type_check_relation_id` (L6) vs
`types/relay.py:312` (`node_id.node_id if isinstance(...) else
node_id`). Shared form considered: one GlobalID-vs-literal
branch. Contract difference: a structural check with coercion +
envelope errors vs a one-line read-path accessor with no
validation. Posit any validation change → only L6 moves.
Trigger: the read accessor gaining a rejection.

### R5 — Single spine vs one-element batched (rejected, same-file separation)

`decode_visible_relation` (L7, object tail + projection) vs
`decode_visible_relation_ids` (L10, pk-set tail + subset
check) — both owned here, overlapping on a single id. Shared
form considered: one single-id body both arities ride. Contract
difference: the spine exists to return the OBJECT (form
`to_field_name`, serializer pk projection); the batch exists to
confirm a SET in one query. The model FK deliberately rides the
batch ("same contract the M2M path uses"); the form multi
deliberately maps the spine (needs objects). A merge is a mode
flag choosing a tail no single caller wants whole. Both share
L6 + the A1 base; only the tails differ. Trigger: a flavor
needing the object tail over a set, or the set tail gaining an
object projection.

### R6 — Relation sub-dispatch vs kind dispatch (rejected, same-file separation)

`relation_into`'s `multi if spec.kind == RELATION_MULTI else
single` (:410) vs `decode_provided_fields`'
`handlers.get(spec.kind, scalar_handler)` (:491). Shared form
considered: one kind router. Contract difference: relation
sub-pick (both arms relation decoders, extras threaded) vs top
routing with a scalar default (`SCALAR` never appears in a map
by design). Posit "a third relation kind" → only the sub-pick
moves; posit "unknown kinds must raise" → only the top dispatch
moves. Trigger: a kind taxonomy both dispatches must read from
one table.

### R7 — Storage str-reads vs error-render str-reads (rejected)

L2/L3's `str.__str__` storage reads vs
`exceptions.py::_safe_text` (never-raising renderer with
fallback + `<unprintable>` placeholder, consumed by
`utils/errors.py`). Shared form considered: one hostile-str
read. Contract difference: storage must return the EXACT value
or reject (non-strings pass through untouched — coercing a dict
to `"..."` would corrupt the write); rendering must never raise
and coerces everything. The remaining `str.__str__` sites
package-wide are the same language token applied to per-site
values, not a rule. Posit "storage rejects subclasses" → only
L2/L3 move; posit "renders gain a new fallback" → only
`_safe_text` moves. Trigger: a read needing both exactness and
never-raise.

### R8 — Container except-arm vs shared except-guard driver (rejected)

HEAD `materialize_relation_id_container`'s `except BaseException`
(:266-267) vs the 85-site `except` population. CONVERGE with the
standing J1 shared-except-guard direction on fresh evidence:
per-site verdict (collapse a malformed container to the envelope)
with a per-site blast radius; a shared driver pins nothing about
which refusals collapse. Trigger re-checked unfired (no owned
guard exists at HEAD). Note: hunt hunk 6 narrows this arm to
`TypeError` — concurrent work, observed-not-adjudicated; if it
lands, this rejection's cited arm text goes stale while the
direction stands.

## Defects

None filed. One observation, hunt-owned lines, closeout-conditional:

- O1 (observed-not-homed): HEAD `type_check_relation_id`'s title
  ("WITHOUT a DB fetch", :125) and "Neither branch touches the DB"
  (:134-135) overclaim the GlobalID branch for a consumer `id:
  relay.NodeID[...]` over a non-pk concrete column: `relay.py::
  decode_model_global_id` → `_resolve_real_pk` issues one
  default-manager lookup per id in exactly that case
  (`relay.py:252-261, :281-284` at HEAD `c3c5aea5`; pk and
  non-concrete attrs return query-free). Same narrow gap in L10's
  "(i)... short-circuiting before any query" for a no-match
  NodeID value. Hunt hunk 4 already rewrites the L6 sentence and
  hunk 7 re-batches the resolve; if that dirt lands, O1 is moot,
  else closeout homes a doc correction. Not a DRY defect (no
  second definition), not a behavior defect (the query is the
  documented resolve, alias-pinned).

## Pending execution

None. Zero-edit file item; all proofs `static-reviewed`.

## Judgment

`utils/write_values.py` at HEAD (`d28587c7`) is a clean
single-owner module: twelve file-local rules (L1-L12), six
consumed/converged families (A1-A6, all transcribing nothing),
eight rejections (R1-R8, two same-file separations, six
cross-file). Every cross-flavor decode step the three write
flavors plus auth share is already promoted here and consumed by
name; the open `related-object-visibility-recheck` family gains
no new definition from this file (consumer-only converge). The 7
worktree hunks are hunt dirt (relay batching + `truth` migration
+ except narrowing), attributed by content and excluded from
every verdict. No production edit owed, no test owed, no defect
filed, no family opened.

## Families

None new. One consumer-only converge onto open
`related-object-visibility-recheck` (A1 — row already lists this
file; no new row owed). One consume of verified consolidated
`mutation-error-envelope` (A2 — row already lists this file).
Four converges onto standing rejections (A3 `field-value-coercion`
F6, A4 `errors-text-atoms-vs-relation-id-atoms`, A5
`write-txn-pk-vs-coercion`, A6 `excluded-unreachability` — rows
already list this file; triggers re-checked unfired).

## Index rows for Worker-0

| `write-values-module-mechanics` | `django_strawberry_framework/utils/write_values.py` (module docstring 9-bullet manifest + 8 consumed imports + TYPE_CHECKING Callable/FieldError, no `__all__`) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-storability-preflight` | `django_strawberry_framework/utils/write_values.py::unencodable_text_error` (lone-surrogate reject-at-decode; base-str-slot read; consumers L4 + auth login/register) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-choice-unwrap` | `django_strawberry_framework/utils/write_values.py::raw_choice_value` (Enum member to raw choice value + exact-str normalize; sole consumer the scalar leaf) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-scalar-leaf-order` | `django_strawberry_framework/utils/write_values.py::decode_scalar_leaf` (unwrap-then-preflight compose; flavor steps compose around it) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-raw-pk-field-pick` | `django_strawberry_framework/utils/write_values.py::coerce_relation_pk_or_none` (the `_meta.pk` field pick for the shared coercer; consumers L6 + model locate arm) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-relation-id-check` | `django_strawberry_framework/utils/write_values.py::type_check_relation_id` (GlobalID-or-raw-pk two-branch structural check; function-local relay import) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-single-spine` | `django_strawberry_framework/utils/write_values.py::decode_visible_relation` (skip/type-check/visible-object/project spine; cross-flavor no-attach-unseen invariant) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-relation-id-atoms` | `django_strawberry_framework/utils/write_values.py::RELATION_ID_ATOM_TYPES` (never-a-container atom set incl. Mapping; sole consumer L9) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-container-materialize` | `django_strawberry_framework/utils/write_values.py::materialize_relation_id_container` (atoms-outright + list-once-before-decode; consumers L10 + form multi) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-batched-decode` | `django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids` (type-check-each + empty-no-touch + one-query visibility + subset fail; flavor null at callers) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-store-vocabulary` | `django_strawberry_framework/utils/write_values.py::decode_field_handlers` (+ `store_decoded`, `decoded_into`, `scalar_into`, `file_into`, `relation_into`, `_spec_field_name`, `_no_relation_extra`; three riders + serializer nested) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-provided-walk` | `django_strawberry_framework/utils/write_values.py::decode_provided_fields` (sole input_attr map + UNSET-stripped kind dispatch + scalar default + first-error short-circuit) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | file-local |
| `write-values-enum-unwrap-vs-filter` | `django_strawberry_framework/utils/write_values.py::raw_choice_value` (rejection recorded here; fresh pair — storage unwrap + exact-str tail vs filter form-clean passthrough; trigger: nested write enums or a read surface needing the tail) | `django_strawberry_framework/utils/write_values.py`, `django_strawberry_framework/filters/inputs.py` | File `utils/write_values.py` | rejected |
| `write-values-preflight-vs-budget-measure` | `django_strawberry_framework/utils/write_values.py::unencodable_text_error` (rejection recorded here; fresh pair — reject-closed vs never-raise measure; trigger: one policy needing both verdicts) | `django_strawberry_framework/utils/write_values.py`, `django_strawberry_framework/extensions/resource_policy.py` | File `utils/write_values.py` | rejected |
| `write-values-id-check-vs-filter-decode` | `django_strawberry_framework/utils/write_values.py::type_check_relation_id` (rejection recorded here; fresh pair — envelope-pair write check vs raising strategy-aware filter decode; trigger: a shared strategy-membership rule) | `django_strawberry_framework/utils/write_values.py`, `django_strawberry_framework/filters/base.py` | File `utils/write_values.py` | rejected |
| `write-values-id-check-vs-relay-unwrap` | `django_strawberry_framework/utils/write_values.py::type_check_relation_id` (rejection recorded here; fresh pair — validating check vs one-line read accessor; trigger: the accessor gaining a rejection) | `django_strawberry_framework/utils/write_values.py`, `django_strawberry_framework/types/relay.py` | File `utils/write_values.py` | rejected |
| `write-values-spine-vs-batched` | `django_strawberry_framework/utils/write_values.py::decode_visible_relation` (rejection recorded here; fresh same-file separation — object tail vs pk-set tail, model rides batched deliberately; trigger: object-tail-over-set need) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | rejected |
| `write-values-subdispatch-vs-topdispatch` | `django_strawberry_framework/utils/write_values.py::relation_into` (rejection recorded here; fresh same-file separation — relation sub-pick vs kind routing with scalar default; trigger: one shared kind table) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | rejected |
| `write-values-storage-read-vs-render-read` | `django_strawberry_framework/utils/write_values.py::raw_choice_value` (rejection recorded here; fresh pair — exact-or-reject storage reads vs never-raise `_safe_text` render; trigger: a read needing both) | `django_strawberry_framework/utils/write_values.py`, `django_strawberry_framework/exceptions.py` | File `utils/write_values.py` | rejected |
| `write-values-except-arm-vs-shared-guard` | `django_strawberry_framework/utils/write_values.py::materialize_relation_id_container` (rejection recorded here; CONVERGE with the verified J1 shared-except-guard direction on fresh evidence — per-site collapse verdict; hunt narrows the arm, direction stands) | `django_strawberry_framework/utils/write_values.py` | File `utils/write_values.py` | rejected |

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

## Independent verification (Worker-2) — pre-Findings trace (recorded before opening `## Findings`)

Target `django_strawberry_framework/utils/write_values.py`. HEAD `0c0537e2`
(blob `d28587c7`, 494 lines); worktree blob `13548c76` (524 lines).
`git diff fe63056f -- <target>` is empty: W1 made zero target edits.
`git diff HEAD -- <target>` counts 7 `@@` hunks; all predate the item
baseline (worktree digest recorded at dispatch matches current bytes).

### Own enumeration (HEAD bytes, `ast.Module.body`)

28 nodes expected: 1 module docstring + 8 imports (`__future__`,
`collections.abc.Mapping`, `enum.Enum`, `typing.TYPE_CHECKING/Any`,
`strawberry.relay`, `.errors` x3 names, `.inputs` x4 names, `.querysets`
x4 names) + 1 `TYPE_CHECKING` If + 17 FunctionDefs
(`unencodable_text_error`, `raw_choice_value`,
`coerce_relation_pk_or_none`, `type_check_relation_id`,
`decode_scalar_leaf`, `decode_visible_relation`,
`materialize_relation_id_container`, `decode_visible_relation_ids`,
`_spec_field_name`, `_no_relation_extra`, `store_decoded`,
`decoded_into`, `scalar_into`, `file_into`, `relation_into`,
`decode_field_handlers`, `decode_provided_fields`) + 1 Assign
(`RELATION_ID_ATOM_TYPES`). Worktree adds exactly 1 node (`from . import
truth`). Count verified independently via AST dump (28 HEAD / 29
worktree).

### Own hunk attribution (by content, before reading W1)

H1 module-docstring "batched NodeID mapping" wording; H2 `from . import
truth`; H3 `truth.static_attr` in `coerce_relation_pk_or_none`; H4
`type_check_relation_id` docstring (GlobalID branch now query-bearing);
H5 `materialize_relation_id_container` docstring (iteration-behavior
clause); H6 `except BaseException` -> `except TypeError`; H7
`decode_visible_relation_ids` batched rewrite over relay
`_decode_and_coerce` / `_resolve_real_pks_batched` (both absent from HEAD
`relay.py`: grep count 0). Themes: relay batching (H1/H4/H7), truth
migration (H2/H3, untracked `utils/truth.py` substrate), except narrowing
(H5/H6). None in DRY `## Owned changes` (relay.py row is a docstring-only
orphan adoption), none in `## Cycle baseline` (target clean at entry):
external by rule. Hunt file-items for both `write_values.py` and
`relay.py` closed No-bugs with zero edits, so the batch postdates them;
"hunt dirt" is the run-7 standing label for such concurrent hardening
(same convention as verified siblings `utils/errors.py`,
`utils/write_transaction.py`).

### Own sites / roles / definition counts

Definitions (all single-owned here): the 17 functions + the atom tuple.
Consumers by import: `forms/resolvers.py` (4 names),
`mutations/resolvers.py` (6 names), `rest_framework/resolvers.py` (5
names), `auth/mutations.py` (`unencodable_text_error` x2 call sites).
Oracles: `tests/utils/test_write_values.py` (27 tests at HEAD; imports
owner by name, pins envelopes/outcomes incl. live-tier companions cited
in its docstring). Projections: module + function docstrings, bilateral
atoms separation prose (`errors.py` comment + module comment here).
Posited changes and counts: (a) scalar-leaf order/step change ->
1 (`decode_scalar_leaf`); (b) relation-id well-formedness change -> 1
(`type_check_relation_id`); (c) set-visibility shape change -> 1
(`decode_visible_relation_ids`); (d) atom-membership change -> 1
(`RELATION_ID_ATOM_TYPES`); (e) handler-vocabulary change -> 1 (the
`*_into` ladder, already composed through `decoded_into` /
`store_decoded`). Owner I would choose: this file stands (flavor-neutral;
dependency direction matches verified `mutation-error-envelope` F1
reasoning).

### Own matrix discharge (HEAD bytes)

1. Cross-flavor: the file IS the shared owner; per-flavor null policy
(model M2M reject / form `empty_values` / serializer `None`) stays at
callers per envelope-F1 distinct-behavior record; no local twin found in
any of the three resolver import blocks. 2. Sync/async: inapplicable —
no async def in file; `async_recourse` is a threaded string. 3. Derived
knowledge: `graphql_name`/`target_name` read off caller-built spec
records (single derivation at spec build); pk-field read once;
`relay.py::_coerce_pk_or_none` is the GlobalID counterpart on a different
seam (`resolve_id_attr` vs `_meta.pk`) — expected rejection, not twin.
4. Round-trip: generation (per-flavor inputs/converters) vs decode (this
file); decode reads spec records, restates no shape. 5. Other media:
oracles + projections as above; envelope triggers re-checked unfired at
HEAD (zero `FieldError(` occurrences; one `codes=` using the
`FIELD_ERROR_CODE_INVALID` constant; no payload-type declaration).
6. Omission: all three flavors route SCALAR/RELATION/FILE through the
shared walk; form MULTI maps the single spine per element
(object-preserving for `to_field_name`) while model/serializer share the
batched pk-only compose — intentional contract split, not a gap.

### Own standing-row expectations

A1 onto open `related-object-visibility-recheck` as consumer-only:
expected, matching querysets-F5 which cites `write_values.py:226` as a
consumer (HEAD line verified: `visible_related_object` call). A2 onto
verified `mutation-error-envelope`: expected consumer-only, triggers
unfired (see axis 5). Four standing-rejection converges expected, all
triggers unfired at HEAD: querysets-F6 `field-value-coercion` (HEAD
batched body type-checks every element before `visible_related_objects`
+ `pks_all_present` gate — read at HEAD lines ~298-313); errors-R1
text-atoms (`_TEXT_ATOM_TYPES` 5th member `Promise` vs
`RELATION_ID_ATOM_TYPES` 5th member `Mapping` — both read at HEAD);
rest_framework-J19 `EXCLUDED` unreachability (fallback
`handlers.get(spec.kind, scalar_handler)` unchanged at HEAD; trigger
lives in `serializer_converter.py` bytes); write_transaction-R2
(canonical-pk separation, same F6 trigger). Zero-defect expectation:
no second definition found anywhere above; any observation must be
hunt-conditional to stand.

## Independent verification reconciliation (Worker-2) — verdict `verified`

Reconciliation of the pre-Findings trace against W1's `## Findings`.
Every check below re-derived from HEAD bytes (`git show HEAD:`), not
from W1's prose.

- **Enumeration (28/28): PASS, member by member.** My AST dump (28 HEAD
  nodes) matches W1's table row for row; all 28 HEAD line numbers
  cross-checked against the 7-hunk diff arithmetic (import +1, materialize
  +2, batched-body +27 shifts all reconcile). Every member lands in
  L1–L12; no second spelling of any owned rule (axis grep confirmed).
- **Hunk attribution (7/7): PASS.** My content map matches W1's hunk for
  hunk: relay batching (docstring / type-check docstring / batched-body
  rewrite over worktree-only `_decode_and_coerce` +
  `_resolve_real_pks_batched` — HEAD `relay.py` grep count 0, blobs
  `c3c5aea5`/`f5760b45` re-hashed exact), truth migration (import +
  `static_attr`, untracked `utils/truth.py`), except narrowing (docstring
  + `BaseException`→`TypeError`). Zero-edit proved (`git diff
  fe63056f -- <target>` empty); external by rule (no ledger row, clean
  at cycle entry); run-7 "hunt dirt" label matches verified siblings.
- **A1 (open `related-object-visibility-recheck`, consumer-only): PASS.**
  Converges with querysets-F5: consumer call at HEAD :226 re-read;
  F5 contrast sites re-verified at HEAD (querysets :4308 def,
  types/resolvers :395 def + 7 call sites). No new definition here.
- **A2 (verified `mutation-error-envelope`): PASS.** Census re-derived
  at HEAD: zero `FieldError(`, one `field_error(` (:71), six
  `relation_field_error` calls (:153/:157/:228/:263/:267/:314; 5 further
  hits are import + docstrings), one constant `codes=` (:74). All three
  triggers + R1 trigger unfired.
- **A3–A6 (standing rejections): PASS, all triggers re-checked unfired.**
  F6: exactly one production `pks_all_present` caller (HEAD :313,
  post-`type_check` loop) + `stringified_pks_present` only inside
  `visible_related_objects` (:4374 re-read); three-consumer census
  reproduces. Errors-R1: both 5-tuples re-read at HEAD (5th members
  `Mapping` vs `Promise`). Txn-R2: same F6 trigger, both bodies at
  cited blobs (`eca9ad4d`/`d28587c7`). J19: `EXCLUDED` model-emitted
  only (`mutations/inputs.py:87`, model map :442, both re-read);
  fallback `handlers.get(spec.kind, scalar_handler)` unchanged at HEAD.
- **R1–R8: PASS, each probed independently at HEAD.** R1 filter unwrap
  (:682-701: single-level, `.value` as-is, nested declined in
  docstring). R2 surrogatepass measurer (:795: never-raise budget
  walk). R3 filter GlobalID decode (:715: raising, strategy-aware,
  coded errors). R4 one-line read accessor (`types/relay.py:312`
  re-read). R5/R6 same-file separations (both bodies + cited lines
  :410/:491 re-read; object-vs-set tails, sub-pick-vs-routing).
  R7 `_safe_text` (never-raise renderer + fallback + placeholder
  re-read). R8 converges with standing J1 (`dry-file-_request_body.md`
  rejection re-read; no owned guard at HEAD; hunt-narrowing note
  accurate).
- **O1 + zero-defect: PASS.** HEAD `relay.py::_resolve_real_pk`
  docstring + tail query re-read: non-pk concrete NodeID attrs issue
  one alias-pinned default-manager lookup; pk/non-concrete return
  query-free — the overclaim is real, narrow, and doc-only. Hunt hunk 4
  rewrites the L6 sentence (verified in worktree diff), so the
  closeout-conditional moot/else-correct framing is exactly right. Not
  a DRY defect, not a behavior defect. No second definition found in my
  own trace either; nothing routes to the maintainer.
- **Reconciled differences: none material.** My expected
  `relay._coerce_pk_or_none` twin-check is answered by A3's census
  placement (fellow consumer under the endorsed field-pick split).
  W1's R2/R7 pairs exceed my candidate list; both probed and stand.
- **Gates:** all cited fingerprints re-hashed exact (target pair +
  relay pair + 8 consumer/oracle blobs); cited consumer/oracle lines
  spot-verified (model :412/:523/:558, forms :200/:449, serializer
  :233/:262, auth :636-637/:1136, live pins :1140/:5119); item diff is
  this untracked artifact only (no `.py` touched — ruff n/a;
  `check_trailing_commas.py --check` on the artifact: excluded class,
  0 violations); no banned provenance tokens (only `H1/H4/H7` hunk
  labels in my own section); `## Pending execution` correctly empty
  (static-reviewed zero-edit, no ordering/txn/async claim about own
  bodies); HEAD unmoved (`0c0537e2`).

**Verdict: `verified`.** 28/28 homed (12 file-local, 6
consume/converge transcribing nothing, 8 rejections); 7 hunks external;
zero defects with O1 observed-not-homed closeout-conditional. 20
pipe-table index rows in artifact for Worker-0; no new families.
