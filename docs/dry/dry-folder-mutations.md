# DRY review: `mutations/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights). Audits the UNASSIGNED remainder
of the `mutations/` folder and the families that cross its ownership
boundaries at current bytes (HEAD `23b5f421` + working tree). The seven
member file artifacts are inputs, not verdicts: every assignment below was
re-derived fresh at WT bytes, and every assignment the tree has falsified
is flagged as a finding inside this item for the closeout defect-homing
pass. No prior artifact is summarized and no row is reopened.

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da` (detached, intended).
`ITEM_BASELINE=b8082cb016c67ec4739ab855ad355fc0749ef968` (resolves to a
commit; its seven mutations blobs equal the working tree as dispatched, so
BASE=WT pre-edit for all seven targets and BASE=WT=HEAD for the one clean
file). Post-edit WT (FAM-3 landed) moves `inputs.py` only.

| Target | WT | HEAD | ITEM_BASELINE | State |
|---|---|---|---|---|
| `mutations/__init__.py` | `c13283f8` | `c13283f8` | `c13283f8` | clean |
| `mutations/fields.py` | `62a15151` | `3908afa9` | `62a15151` | dirty |
| `mutations/inputs.py` | `a9428e11` | `f821661e` | `bb329e4d` | dirty + mine |
| `mutations/operations.py` | `612c458d` | `0d9ee2e9` | `612c458d` | dirty |
| `mutations/permissions.py` | `127575bb` | `57e7ca20` | `127575bb` | dirty |
| `mutations/resolvers.py` | `9171b93f` | `bb6c630d` | `9171b93f` | dirty |
| `mutations/sets.py` | `6f2fa2f9` | `a123aea8` | `6f2fa2f9` | dirty |

Full blobs, WT post-edit: init
`c13283f85f65c7d8864d961489d2a089a9e6b3f7`, fields
`62a151519cc5d8942fb2a8d0fef95d9538819059`, inputs
`a9428e115ce5d87a75483948fa43d454ab1bef73` (pre-edit
`bb329e4d6cc981c6fc8cba5cf91b7504b4858f0d`), operations
`612c458d65283dd10f90d56da6517cf698dbbe7c`, permissions
`127575bb623fb08b213feb6ac18e11654cdd9b68`, resolvers
`9171b93faef5a0263db842fc4c917fe5f63fef05`, sets
`6f2fa2f9f73505c2007388df5eb9feaffa94bf8d`; tests
`tests/mutations/test_inputs.py`
`12aacb735681d81fe00a7df7bea84982c6eaa287`. WT line counts post-edit:
init 36, fields 342, inputs 1153 (HEAD 1118), operations 157,
permissions 263, resolvers 1545, sets 1953.

## System trace

The folder owns the package write side end to end: the operation
vocabulary (`operations.py`), the generation substrate
(`inputs.py`: `<Model>Input` / `<Model>PartialInput`, `FieldError`,
`<Name>Payload`), the declarative surface + phase-2.5 bind (`sets.py`:
`DjangoMutation`, metaclass, ledgers, `bind_mutations`), the default
write authorization (`permissions.py`), the sync/async pipeline +
skeleton every flavor rides (`resolvers.py`), the root-field factory
(`fields.py`), and the 4-name leaf manifest (`__init__.py`). Served by
call, inheritance, and factory instantiation: the form flavors
(`forms/sets.py`, `forms/inputs.py`, `forms/resolvers.py`), the
serializer flavor (`rest_framework/*`), and the auth surfaces
(`auth/mutations.py`, `auth/queries.py`).

Population at WT post-edit (`ast.parse`, `len(ast.Module.body)`):
init 7 statements (0 defs); fields 24 statements, 8 defs; inputs 59
statements, 30 defs; operations 21 statements, 5 defs; permissions 14
statements, 4 defs; resolvers 62 statements, 32 defs; sets 71
statements, 35 defs. Connected sources read in full: all seven
targets at WT bytes. Connected bodies read at the cited sites: the
form / serializer / auth riders and overrides, the finalizer phase-2.5
window, the marker readers, the recourse twins, every upstream owner
this folder composes, and the `tests/mutations/` oracles. Searched
population for second sites: the whole package
(`django_strawberry_framework/`), `tests/`, and `examples/`; every
census below names its pattern and count.

### Attribution of the working-tree dirt (by diff content vs HEAD)

Three provenances, distinguished per hunk; only the third is mine.

Ledgered DRY work (run-2 adopted orphan
`mutation-input-reverse-map`): `inputs.py` owns
`relation_input_python_attr` + 3 composed sites (generator,
index x2) + docstring. Present in WT, uncommitted since adoption;
this item builds nothing on it beyond re-verifying the gate.

Concurrent bug-hunt work (truth migration, hostile-guard deletions,
`except`-arm deletions, `_safe_*` removals): every `truth.*` read and
cast in all six dirty files, the new `fields.py::_ABSENT` /
`_is_callable_member` / identity-scan ledger check, the deleted
`sets.py::_safe_frozenset_membership`, and the message/comment
rewrites riding those hunks. Never edited, reverted, or tidied here;
a consolidation touching those lines is blocked-on-hunt.

Mine (this item, FAM-3): `inputs.py` gains
`_operation_kind_display_word` + 2 composed call sites (all on
HEAD-clean lines); `tests/mutations/test_inputs.py` gains 1 import, 3
tests, and 1 census walker. Item-scoped diff vs `ITEM_BASELINE`
confirms exactly those hunks plus concurrent `dry-0_0_15.md` plan
edits outside my paths (untouched).

## Verification

### Matrix

1. Cross-flavor: the three write flavors + auth compose this
   folder by name (FC-2, FC-6, FC-7, FC-8); per-flavor matrices,
   seams, and name grammars stay at the flavors with recorded
   differences (see Rejections). No mirrored body found.
   Discharged.
2. Sync/async: `operations.py`, `inputs.py`, `permissions.py`,
   `sets.py`, `fields.py`, `__init__.py` carry zero `async def` /
   `await` in code (remaining hits are docstrings); both code
   `async def`s live in `resolvers.py` (`run_pipeline_async`, a
   one-line delegate of the open `one-sync-boundary` primitive,
   awaited once inside the entry factory's `resolve_async`
   closure). No twinship beyond the factory pair. Discharged.
3. Derived knowledge: walked every same-token population on body
   strength. Genuine re-derivations: the payload-suffix pair
   (FAM-1, blocked), the static-callability pair (FAM-2, blocked),
   the kind-word pair (FAM-3, consolidated). Everything else is
   one definition with by-name composers (FC-1..FC-16) or a
   distinct contract with a trigger (FR-1..FR-12 + the
   converge-reaffirmed list). Discharged.
4. Round-trip: payload build (`inputs.py`) vs stash read-back
   (`resolvers.py::payload_cls_for`) compose through the stashed
   name; input build (`inputs.py` + bind hand-off) vs decode
   (`resolvers.py` + `write_values.py` spine) share the
   `InputFieldSpec` record; GlobalID encode (annotation) vs decode
   (primitive) meet at `typed-globalid-decode`; the `EXCLUDED`
   tag write (bind) vs capture (decode) share the imported tag.
   One grammar per pair, correctly separated halves. Discharged.
5. Other media: package oracles (`tests/mutations/`, 83 rows in
   `test_inputs.py` alone, all green post-edit), live `/graphql`
   rows (products/library write suites pin wire behavior),
   projections (module/class/method docstrings; spec-036..040
   decisions cited, never re-verified against archived text).
   No medium carries a second definition of a folder rule.
   Discharged.
6. Omission: all seven files enumerated below; every member
   lands in a member-artifact assignment re-verified at current
   bytes, an indexed family row, or one of this item's 55 rows.
   The flavor x guard matrix (model / ModelForm / plain /
   serializer / auth-fixed against target-guard, walk, locate,
   decode, save, tail) shows no member lacking a guard its
   contract requires. No unassigned member remains. Discharged.

### Enumeration

Instrument: `ast` top-level census at WT post-edit bytes plus
`rg -c` anchor censuses over the package; every anchor count
re-verified (zero misses across the full seven-file inventory).

| File | Top-level members | Homes |
|---|---|---|
| `__init__.py` | 7 (docstring + future + 4 imports + `__all__`) | member F1/F2 stand; 2 folder rows |
| `fields.py` | 24 (8 defs: guard trio + `_is_callable_member` + lazy + signature x2 + factory; marker; `_ABSENT`) | FAM-1/FAM-2 sites + 6 folder rows |
| `inputs.py` | 59 (30 defs incl. FAM-3 helper; tokens; envelope; namespace; spine; generator; payload) | FAM-1/FAM-3 + N1/N5/N6/N7 families + 15 folder rows |
| `operations.py` | 21 (record + 4 declarations + registry + 3 predicates + 5 derivations + reject) | 1 folder row |
| `permissions.py` | 14 (recourse + result contract + walk + 2 classes) | 4 folder rows + 2 rejections |
| `resolvers.py` | 62 (32 defs: skeleton + factory + riders + seams + mappers + tail) | F1/F2 families + 8 folder rows |
| `sets.py` | 71 (35 defs: vocabulary + kit + seals + base + bind) | 17 folder rows |

### Challenges

Authoritative definitions only; consumers, oracles, and projections
that also move are listed, never counted. Post-edit bytes.

- C1 payload-suffix rename (`Payload` -> `Result`) -> 2
  (`build_payload_type` + fields prediction; FAM-1, blocked).
- C2 static-read callability new arm (e.g. recognize a further
  descriptor) -> 2 (named helper + inline site; FAM-2, blocked).
- C3 new generator kind display -> 1 (`_operation_kind_display_word`;
  was 2; FAM-3).
- C4 new model operation / per-member flag change -> 1 (descriptor
  table; derivations follow by comprehension).
- C5 pipeline reorder / new flavor middle -> 1 (skeleton; 5 rider
  call sites follow) / 1 branch + declarations.
- C6 `UNSET` normalization change -> 1 (entry factory; 3 products
  follow; register stays).
- C7 hook-vocabulary collapse / recourse template -> refused (3
  contracts; 4 clauses differ).
- C8 seal slot / head change -> 1 each (record / factory; auth
  mirrors excluded with differences).
- C9 shape identity / name grammar change -> 1 (descriptor /
  utils spine; bind, merge, seam follow).
- C10 relation id-type / classification / annotation change -> 1
  each (scalar rule / classifier / triple; flavors follow).
- C11 payload slot / reserved-attrs change -> 1 each.
- C12 basis / requiredness / audit / normalizer / namespace /
  generator / collision / key / tag change -> 1 each.
- C13 auth-result shape change -> 1 here (seam decisions) / 0
  (contract owner); walk change -> 1; closed-default change -> 1.
- C14 null contract / exclude mechanism / `EXCLUDED` second kind /
  delete mapping / race mapping / id status / tail shape -> 1 each.
- C15 Meta key / gate / cache / ledger / seam / base / bind change
  -> 1 per helper (16 locals).
- C16 hostile construction target (5 axes) -> 1 (guard trio;
  oracles move as media).
- C17 operation-literal sites (`!= "form"`, `== "delete"`,
  `== "update"`) vs predicates -> refused (call/dispatch/backstop
  vs vocabulary; triggers unfired).

## Findings

### FAM-1 — `mutation-payload-name` (CONFIRMED count-2, BLOCKED-ON-HUNT)

Challenge C1 re-derived at WT: renaming the payload suffix moves
two grammar definitions, both in-folder. Site A
(`inputs.py::build_payload_type`, `type(f"{mutation_name}Payload",
...)`) materializes the runtime class; site B
(`fields.py::_synthesized_mutation_signature`,
`_lazy_ref(f"{truth.name(mutation_cls)}Payload", ...)`) predicts the
same name for the lazy root-field return. Package sweep for
`Payload`-suffix constructions (`rg '}Payload"'`) returns exactly
these 2 in production: `sets.py` passes the base name through with
zero constructions (P2 re-verified), `resolvers.py` reads the stash,
form flavors consume `build_payload_type`, serializer payloads reuse
the model type by seam override, and auth's `LoginPayload` /
`LogoutPayload` / `RegisterPayload` / `CurrentUserPayload` /
`UpdateCurrentUserPayload` / `RequestPasswordResetPayload` are full
literal names passed to the builder, not base+suffix constructions.
Specified migration: a pure
`payload_type_name_for(mutation_name: str) -> str` in `inputs.py`
with site B composing it, plus a spy gate (diverted name surfaces
in both the materialized class and the synthesized signature) and
an AST census pinning 1 suffix construction. BLOCKED: site B sits
inside the truth-migration hunk (`git diff HEAD --
mutations/fields.py`, hunk `@@ -254,7 +277,7`, line
`return_annotation = _lazy_ref(f"{truth.name(mutation_cls)}Payload",
INPUTS_MODULE_PATH)`); rewriting it touches hunt dirt. Zero source
edits. Family row named below: holding item
Family `mutation-payload-name`, status open, blocked-on-hunt; no
Families item until unblocked.

### FAM-2 — `static-read-callability` (CONFIRMED count-2, BLOCKED-ON-HUNT)

Challenge C2, newly derived by this item (no member artifact named
it; it crystallized under the truth migration). Two spellings of
one rule: "a member read through `truth.static_attr` counts as
callable when it is callable OR a stored `classmethod` object", the
second arm required because static reads bypass descriptor
binding. Site A (`fields.py::_is_callable_member`, named helper,
3 call sites) probes protocol membership; site B
(`sets.py::_validate_permission_classes`, inline
`callable(has_perm) or truth.is_instance(has_perm, classmethod)`)
validates consumer permission entries. Package sweep for
`is_instance\(.*classmethod\)` returns exactly these 2 plus 3
`_django_patches.py` descriptor-unwrap reads (extract `__func__`,
do not test callability: excluded by body). Change challenge: a
new recognized descriptor or a `truth`-level callability predicate
moves both sites for the same reason (binding semantics of the
read primitive). Pinned by
`test_classmethod_protocol_members_are_read_from_the_class_namespace`
(site A) and the permission-entry validation oracles (site B).
Specified migration (option A): site B composes the named helper
via a top-level `sets` -> `fields` import (cycle-safe: `fields.py`
imports `sets` only inside one function body); option B (a
`truth.py` predicate) waits on the hunt landing. BLOCKED: both
lines are hunt dirt (site A added wholesale by the migration;
site B inside hunk `@@ -1038,27 +1016,28`). Owner choice
deferred to unblock; zero source edits. Family row named below:
holding item Family `static-read-callability`, status open,
blocked-on-hunt; no Families item until unblocked.

### FAM-3 — `generator-kind-display-word` (CONFIRMED count-2, CONSOLIDATED 2→1)

Challenge C3, newly derived by this item. Two identical lines
mapped the generator kind to the human-facing word for
configuration-error subjects: `kind = "create" if operation_kind
== CREATE else "update"` in `_reject_generated_input_collisions`
(collision subject) and in `build_mutation_input` (empty-input
message). Census: `operation_kind == CREATE` returns 4 hits
package-wide (2 display mappings + 1 boolean + 1
override-attr selection in `sets.py`, a different rule); no
`== PARTIAL` display mapping and no third display site in
forms/serializer/auth. All `build_mutation_input` callers pass
`CREATE`/`PARTIAL` only (map values + auth `CREATE`), so behavior
is preserved exactly. Landed: `_operation_kind_display_word` in
`inputs.py` + 2 composers, on HEAD-clean lines only (the subject
f-strings carrying `truth.name` are untouched). Gates: a unit test
(both arms), an exact-match AST census (1 mapping inside the
helper + 1 composer per message site), and a diversion spy
(diverted word surfaces in both errors; a bypassed site ignores
it). Failability proved in the workspace copy: the wrong-word
mutant fails exactly the unit + census + pre-existing empty-input
oracle; the re-inline mutant fails exactly the census + spy
(record
`.../evidence/proofs/folder-mutations/consolidate/dry-20261010T032915-add592.json`,
exit 0, both entries `pinned`, restores byte-identical). Index row
named below with status consolidated. Considered and excluded: a
full-subject helper merging the `DjangoMutation {kind} input for
{model}` prefix (touches hunt lines and couples two message
contracts; trigger: a third message needing the subject).

### FC-1 — operation-descriptor vocabulary (CONFIRM single-owned)

`operations.py` holds the only `MutationOperationDescriptor`
constructions (census 4, all in-file), the registry, the 3
predicates, the 5 derived maps (all comprehensions), and the
reject helper. Consumers compose by name at WT: `sets.py`
(validation, naming, perm, override), `fields.py` (call gates),
`resolvers.py` (step selection), `permissions.py` (action
default), `forms/sets.py` + `rest_framework/sets.py` (kind maps,
now direct imports — see FF-7), `forms/inputs.py` (FORM bridge).
Committed evolution since the member artifact: the `Any` import
became `truth`. No hand-spelled operation map exists anywhere
(the only `"add"`/`"change"` literals are the 2 descriptor
members). Converges with the member record; homed by 1 folder
row.

### FC-2 — skeleton, riders, entry factory, register (CONFIRM)

`resolvers.py::run_write_pipeline_sync` is the single write
pipeline (6 phases; the `check_deadline` head is committed
evolution every rider inherits). Riders re-derived at WT: 5 call
sites forming 4 step-pairs (model create/update, model delete,
form middle, serializer middle; auth register repacks into
`_model_write_step` then rides, per the stored-listing/802
identity suite). `make_resolver_entries` has exactly 3 products
(model, form, serializer; auth login/logout/current_user bind
directly, 0 products — J2 stands on the fixed/no-id + fixed-arity
difference). The 3 `sync_pipeline_recourse` nouns compose the
template. `run_pipeline_async` is awaited once (inside the
factory closure); the pack docstrings name it as the async seam.
Converges with the `shared-write-skeleton` family row; no index
change.

### FC-3 — seal pair and auth mirrors (CONFIRM, differences stand)

Slot seal (`_ValidatedMutationMeta.__setattr__`/`__delattr__`,
record-level) and head seal (`make_meta_validating_metaclass`,
2 instances: model + plain-form) are two rules with different
subjects, each single-owned here. `permissions.py` walks the slot,
`schema.py` reads the head constant, `resolvers.py` reads the slot.
Auth mirrors stay excluded with differences: `_AuthMutationMetaSnapshot`
(model-less duck type, own `__slots__` contract) and
`_SealedAuthHolderMeta` (framework-pinned names; now subclasses
the model metaclass — committed evolution, see FF-8). Converges
with the auth folder item's `auth-sealed-slot-mirror` rejection.
Homed by 2 folder rows.

### FC-4 — error envelope and leaves (CONFIRM family posture)

`FieldError` is defined once (`inputs.py`); the shape rule
(`EXCLUDED`/`None`/`""` -> `None`, whitespace verbatim, explicit
`None`), the payload builder (`error_payload_builder` with the
model-less branch), the `set_rollback` single write, and the
`ok=True` convention all stand at WT with the same composers the
family row records (model/auth/serializer payloads + 3 serializer
error surfaces as `null_field_error`/`field_error` consumers).
No second envelope, no inline payload construction in any flavor
(the model-less `payload_cls(ok=True, errors=[])` is the single
construction, one site). No index change.

### FC-5 — input identity and the adopted reverse map (CONFIRM)

`MutationInputShape` + `mutation_input_shape` + name wrapper stay
the sole identity descriptor (consumers: `build_mutation_input`
default, `input_type_name`, both materializers, auth register;
`mutation_input_type_name` has 1 caller). The adopted orphan is
intact at WT: owner `relation_input_python_attr` + the 3 composed
sites + docstring, byte-matching the ledger adoption, and the
diversion gate (`test_relation_naming_scheme_is_single_sited`)
runs green inside the 83-pass focused file. No index change.

### FC-6 — relation-typing spine (CONFIRM compositions)

The four layers stand at WT with flavor composers unchanged:
`relation_id_scalar`/`relation_id_annotation` (1 caller up the
chain; leaf + spine consumers), the column-less trio
(`related_model_of_queryset`, `require_queryset_related_model`,
`annotate_queryset_relation`; called from forms/serializer),
`model_column_write_kind` (called from specs, both annotation
wrappers, forms, serializer), and the annotation triple
(`relation_input_annotation`, `model_column_write_annotation`,
`model_column_input_annotation`; called from the generator,
naming, bind, and both flavors). `decode_visible_relation_ids`
has 3 callers (2 model decoders + 1 serializer wrapper) — the
`related-object-visibility-recheck` consumer edge stands (line
cites refreshed in the corrections list). Homed by 4 folder rows
(N1 already has its family row).

### FC-7 — permission walk, seams, defaults (CONFIRM)

`run_permission_classes` has 2 seam callers (model,
plain-form; serializer inherits; ModelForm inherits the model
seam); `DjangoModelPermission` is composed as the model-backed
default (no second action map — `_OPERATION_PERMISSION_ACTION`
has 1 read); `DenyAll` is the model-less closed default
(2 wirings + docstring). The two identical
`return run_permission_classes(...)` delegation lines are the
blessed declaration shape, and `_require_sync_bool_auth_result`
guards all 3 bool-decision seams. No index change beyond 4
folder rows.

### FC-8 — bind drain, ledgers, clears, finalize gate (CONFIRM)

`bind_write_declarations` has 2 riders (model, plain-form;
ModelForm/serializer ride the model ledger/drain). Ledgers:
`make_declaration_registry` has 3 products (model, plain-form,
auth); `make_input_namespace` has 5 family products (mutations,
forms, serializer, auth-queries, +1 utils-internal) — this
folder owns its ledger's make/consume/clear/materialize
(recorded split). Clear rows: 3 bus registrations in-folder
(input namespace, declarations, shape cache); the form-flavor
rows stand outside. `finalizer.py:bind_mutations` calls the
model drain inside the phase-2.5 window; the separate
`input-module-join-vs-bind-phase` ordering items are untouched.
Homed by 3 folder rows (drain trio, registry mechanics,
namespace lifecycle).

### FC-9 — class marker stamp and readers (CONFIRM, paths updated)

`MUTATION_CLASS_MARKER` is stamped once (field factory, guarded
by the registered-target check) and read by name at 2 sites:
`schema.py` (execution context) and
`extensions/resource_policy.py` (input-spec read). The member
artifact's reader paths are stale (FF-6); the composition
(import-the-constant) holds. Homed by 1 folder row.

### FC-10 — lazy machinery and directives (CONFIRM)

`_lazy_ref` + `build_lazy_field_signature` are composed by name
at 4 auth call sites (`_lazy_ref` x3, `build_lazy_field_signature`
x1); the signature's return-type grammar (sync/async x4,
with/without `id`) stands. `validated_field_directives` has 5
consumer files (list-field, connection, relay, auth,
mutations-fields) against 1 owner; the default-deny posture and
the optimistic-stale-read guard are untouched here. Homed by 2
folder rows.

### FC-11 — recourse wordings (CONFIRM pair + template)

The write recourse (`_PERMISSION_ASYNC_RECOURSE`: "do not run in
async context" / "define an async-native has_permission" /
plain-bool note / queryset methods) and the gate recourse
(`_GATE_ASYNC_RECOURSE`: "not supported in async" / override note /
presence-probe footnote / registry surfaces) still differ on the
same 4 clauses — the shared-template merge stays refused. The 3
pipeline nouns compose `sync_pipeline_recourse` by template.
No index change.

### FC-12 — literal enforcement sites (CONFIRM, triggers unfired)

`fields.py != "form"` (call gate; `with_id=False` still only at
the plain-form declaration — J3 stands), `resolvers.py ==
"delete"` (step dispatch) + `== "update"` (null backstop), and
the `sets.py` delete-literal validation branches all stand with
their recorded triggers unfired (no second id-only operation, no
new flavor, no UNSET-in-delete decoding). The delete-has-no-input
quartet (field gate, materialize short-circuit, naming raise,
matrix rejection) composes the kind maps at every site. No
index change.

### FC-13 — indexed-family consumer edges (CONFIRM)

Re-derived at WT: `run_in_one_sync_boundary` delegate (open
`one-sync-boundary` family; zero in-repo importers of the compat
name — kept as the documented historical alias, FR-10),
`model_for`/`initial_queryset` call (open
`queryset-seed-and-model-read` family), `apply_type_visibility_sync`
call (rides the sealed applier as a consumer while holding no
seal body — J5 and the `sealed-execution-queryset` files cell both
stand), `reject_async_in_sync_context` call (rides the
`awaitable-refusal-and-disposal` refusal), error-envelope sub-row
consumers, and the `get_or_store_shape_build` call (rides the
`shape-build-get-or-store` memo). No index change.

### FC-14 — open discovery family still blocked (CONFIRM)

`snapshot_or_meta_backing` is still absent package-wide
(`rg`: zero hits); the form/serializer ownership-verdict reads
remain the specified-not-landed count-2 behind the open
`mutation-discovery-own-snapshot-read` row. This item specifies
nothing and touches nothing. No index change.

### FC-15 — deadline single write-path site (CONFIRM)

`run_write_pipeline_sync` holds the one write-path
`check_deadline` call; form/serializer/register riders inherit it
through the skeleton, and auth login's separate call guards a
non-skeleton surface at its own boundary (consumer, not copy).
Read-surface calls guard their own boundaries likewise. No
index change.

### FC-16 — `backing_model_of` new shared leaf (CONFIRM)

Committed evolution since the member artifacts: a 1-body
`backing_model_of` leaf with 16 call sites (7 sets-internal, 6
serializer, 2 auth, 1 form). Single definition, by-name
composers, no twin. Homed inside the type-gate-kit folder row.

### FF-1 — `_safe_frozenset_membership` is gone (flag for closeout)

The `sets.py` FL2 assignment (hostile-hash membership guard) is
falsified at WT: the hunt's `except`-arm deletion removed the
definition, and the two former call sites (operation gate,
Meta-operation validation) now normalize through `truth.text()`
before a plain membership test. Package sweep for the symbol
returns zero references outside historical docs — no dangling
call, no `NameError` defect. The `resolvers.py` R2 reference to
the same deleted arm is falsified alongside. Closeout homing:
retire the FL2/R2 assignments at the member records; the
hostile-hash protection now rides `truth.text()` normalization
(hunt design, not re-litigated here). No index row ever cited
the symbol, so no row correction is owed.

### FF-2 — fields 19 → 24; guard trio rewritten (flag for closeout)

The `fields.py` member enumeration (19 statements) is falsified
at WT (24): +`truth` import, +`Sequence` import, +`TYPE_CHECKING`
block, +`_ABSENT`, +`_is_callable_member`. The guard-trio bodies
were rewritten by the truth migration (identity-scan ledger
check, `truth.static_attr` protocol reads, rendered messages).
The member's three pending-settle flags SETTLE here: the trio
contract stands (typed `ConfigurationError` at construction for
all 5 hostile axes; pinned by the target-guard oracles plus the
new
`test_classmethod_protocol_members_are_read_from_the_class_namespace`),
only the mechanism changed (truthful reads + the named
callability helper). Closeout homing: refresh the F-windows
enumeration and settle the flags; verdicts stand.

### FF-3 — inputs 52 → 58 (+ FAM-3 helper → 59) (flag for closeout)

The `inputs.py` member enumeration (52 statements) is falsified
at WT: +3 header statements (`types` import, `truth` import,
`TYPE_CHECKING` block) and +3 definitions
(`relation_input_python_attr` — the ledgered DRY adoption;
`_carrier_backed_link` + `_carrier_backed_link_error` —
committed ForeignObject evolution), then +1 for this item's
FAM-3 helper. The `Any` import is gone (replaced by `cast`).
Closeout homing: refresh the N/FL enumeration; the carrier pair
is homed by this item's `mutation-editable-basis` folder row.

### FF-4 — sets 61/44 → 71 statements (flag for closeout)

The `sets.py` member enumeration (61 statements, 44 named) is
falsified at WT (71 statements): `_safe_frozenset_membership`
deleted (FF-1); `backing_model_of`, `_id_resolver_seams`,
`_id_less_resolver_seams` added (committed evolution); `truth`
import + `TYPE_CHECKING` names added. The member's pending-settle
flags (seal messages, validation, bind) SETTLE here: every cited
contract stands under truthful reads. Closeout homing: refresh
the F/FL enumeration; the 3 new definitions are homed by this
item's folder rows (type-gate kit, seam factory).

### FF-5 — resolvers 57 → 62; small-file counts (flag for closeout)

The `resolvers.py` member enumeration (57; run-7 re-trace 58) is
62 at WT: +`resource_policy` import, +`truth` import,
+`TYPE_CHECKING` block, +2 re-export annotation statements. The
8 member R-records stand (all bodies re-read; `check_deadline`
call is committed evolution inside the owned skeleton).
`permissions.py` 12 → 14 (+`truth` import, +`TYPE_CHECKING`
block; 4 rules stand). `operations.py` still 21 (the `Any` ->
`truth` swap is count-neutral; vocabulary stands).
`__init__.py` still 7, byte-clean. Closeout homing: refresh the
four enumerations; verdicts stand.

### FF-6 — marker readers moved files (flag for closeout)

The `fields.py` F2 record cites readers that committed evolution
has moved: `schema::_marked_mutation_class` is now the
`schema.py` execution-context read, and
`resource_policy::_mutation_input_specs` is now the
`extensions/resource_policy.py` read. Both still import the
constant by name (FC-9). Closeout homing: refresh the reader
paths; the single-owner verdict stands.

### FF-7 — sets re-export wrinkle is gone (flag for closeout)

The `operations.py` F4 record notes `forms/sets.py` and
`rest_framework/sets.py` importing the kind map through the
`sets.py` re-export; at WT both import directly from
`mutations.operations`. The composition verdict stands on a
cleaner path. Closeout homing: strike the wrinkle note.

### FF-8 — auth holder metaclass now subclasses (flag for closeout)

The `sets.py` F2 record describes `_SealedAuthHolderMeta` as a
separately-pinned holder; at WT it subclasses
`DjangoMutationMetaclass` while keeping the framework-pinned
`__setattr__`/`__delattr__` names. The recorded contract
difference (name pinning) stands. Closeout homing: refresh the
mechanism note; converges with the auth folder item.

### FL-1 — `mutations/__init__.py` local rules (CONFIRM, 2 rows)

File is byte-clean at all three states; member F1/F2 re-read
verbatim. The 4-name `__all__` mirror + re-export block
(`mutations-leaf-manifest`) and the Decisions 4/5/15 module-map
prose (`mutations-module-map-prose`) are unchanged and have no
second site (the `forms/__init__.py` twin stays a same-shape
sibling, never a shared template). 2 folder rows.

### FL-2 — `mutations/operations.py` local rule (CONFIRM, 1 row)

The descriptor table + registry + predicates + derivations +
reject (`mutation-operation-descriptors`) is the folder's
operation vocabulary, single-owned, with the cross-folder
consumer census re-derived (FC-1). The `FORM` member bridges
the forms-owned kind sentinel without owning it (recorded
namespace split); the kind-token pair it derives from stays in
`inputs.py` (row `mutation-kind-tokens`). 1 folder row.

### FL-3 — `mutations/fields.py` local rules (CONFIRM, 6 rows)

Guard trio + `_ABSENT` (`mutation-construction-target-guard`;
FF-2 settles the mechanism), lazy leaf
(`write-field-lazy-forward-ref`), signature builder
(`lazy-root-field-signature`), synthesis
(`mutation-signature-synthesis`), factory body
(`mutation-field-factory-body`), marker
(`mutation-class-marker`). Each re-derived at WT with its
consumer census (FC-9, FC-10, FC-12); FAM-1 site B and FAM-2
site A are named separately above. 6 folder rows.

### FL-4 — `mutations/inputs.py` local rules (CONFIRM, 15 rows)

Column-less trio (`column-less-relation-typing`), classifier
(`model-column-write-classification`), annotation triple
(`model-column-write-annotation`), normalizer
(`mutation-input-attr-normalizer`), basis + carrier pair
(`mutation-editable-basis`), requiredness
(`mutation-create-requiredness`), surface audit
(`mutation-input-surface-audit`), namespace lifecycle
(`mutation-input-namespace-lifecycle`, incl. the zero-importer
`_pascalize_token` legacy alias), generator
(`mutation-input-generator`), collision policy
(`mutation-collision-policy`), key pin (`mutation-non-field-key`),
`EXCLUDED` tag (`mutation-excluded-kind`), kind tokens
(`mutation-kind-tokens`), slot rule
(`mutation-payload-slot-rule`), and the landed
`generator-kind-display-word` (consolidated). N1/N5/N6/N7 ride
their existing family rows. 15 folder rows.

### FL-5 — `mutations/permissions.py` local rules (CONFIRM, 4 rows)

Result contract (`write-auth-result-contract`), walk
(`permission-class-walk`), model default check
(`model-permission-default-check`), closed default
(`model-less-deny-default`). The vocabulary-collapse and
recourse-template merges stay refused (C7, FC-11). 4 folder
rows.

### FL-6 — `mutations/resolvers.py` local rules (CONFIRM, 8 rows)

Decode coloring (`model-relation-decode-coloring`), exclude
carve-out (`mutation-exclude-carve-out`), decode/write steps
(`model-decode-write-steps`, incl. the `EXCLUDED` strict-unpack
arm), delete rider (`mutation-delete-rider`), authorization seam
(`mutation-authorization-seam`), validation/save mappers
(`mutation-validation-save-mappers`), locate/lookup
(`mutation-locate-lookup`), tail
(`mutation-error-refetch-payload-tail`). The F1 skeleton and F2
factory ride their family row; F3..F10 are consumers (FC-2,
FC-13). 8 folder rows.

### FL-7 — `mutations/sets.py` local rules (CONFIRM, 17 rows)

Slot seal (`sealed-mutation-meta-slot`), head seal
(`sealed-mutation-meta-head`), key vocabulary
(`write-meta-shape-vocabulary`), non-delete gate
(`non-delete-operation-gate`), type-gate kit
(`backing-resolution-type-gate-kit`, incl. `backing_model_of`),
hook shape (`construction-hook-shape`), cache discipline
(`shape-build-cache-discipline`), registry mechanics
(`declaration-registry-mechanics`), snapshot record
(`snapshot-record-shape`), permission/lock validation
(`permission-lock-validation`), seam factory
(`resolver-seam-factory`, incl. the 2 private builders), base
matrix (`model-flavor-base`), naming gate
(`custom-input-naming-gate`), primary-type errors
(`primary-type-error-shapes`), materialize pair
(`input-materialize-pair`), shape lock (`override-shape-lock`),
bind drain (`bind-drain-trio`). FL2 is retired by FF-1. The
sister-file matrices stay refused merges (see the
converge-reaffirmed list under Rejections). 17 folder
rows.

### FR-1 — payload full-subject helper (REJECTED)

Merging the `DjangoMutation {kind} input for {model}` prefix
shared by the collision subject and the empty-input message is
refused: both prefix lines are hunt dirt, and the prefix couples
two message contracts (a subject noun vs a sentence head) that
change for different reasons. The kind-word half is consolidated
(FAM-3); the prefix stays spelled twice. Trigger: a third message
needing the same subject. Home: FAM-3 record.

### FR-2 — FAM-2 into `truth.py` now (REJECTED)

Placing the static-callability predicate in `truth.py` is
refused: that file is untracked concurrent hunt work and cannot
receive a consolidation. Option A (sets site composes the
fields helper) is specified for unblock. Trigger: the hunt
lands. Home: FAM-2 record.

### FR-3 — seam-builder merge (REJECTED)

Merging `_id_resolver_seams` and `_id_less_resolver_seams` is
refused: they are signature adapters (with/without the `id`
argument), not twins — the seam-name/permission-shape grammar is
already shared through the factory body they both feed. Trigger:
the two signatures converge. Home: `resolver-seam-factory` row.

### FR-4 — save-mapper merge (REJECTED)

Merging `save_or_field_errors`, `forced_save_or_field_errors`,
and `_delete_or_field_errors` is refused: three race contracts
(policy-guarded write, recovery write, guarded delete) with
different retry/timeout postures. Trigger: the race contracts
unify. Home: `mutation-validation-save-mappers` /
`mutation-delete-rider` rows.

### FR-5 — error-constructor merge (REJECTED)

Merging `not_found_error` and `_invalid_lookup_id_error` is
refused: distinct verdicts (absent row vs malformed id) with
distinct messages and callers. Trigger: the id-lookup verdicts
collapse. Home: `mutation-locate-lookup` row.

### FR-6 — step-list extraction (REJECTED)

Extracting the two `isinstance(..., list)` step-error checks in
the skeleton is refused: one body, two steps, and the check IS
the value-or-errors convention — a helper would name the
convention twice (once per call) while hiding the phase it
guards. Trigger: a third step joins the skeleton. Home: family
`shared-write-skeleton` (no row change).

### FR-7 — decode-tuple unification (REJECTED)

Unifying the 4-tuple model path and the 3-tuple relation-only /
empty paths is refused: the strict unpack is the arity guard,
and `_decoded_or_raise` is the single verdict both ride. Trigger:
arity stops distinguishing the paths. Home:
`model-decode-write-steps` row.

### FR-8 — `EXCLUDED`-vs-scalar decode merge (REJECTED)

Merging the `EXCLUDED` capture arm with the scalar decode arms
is refused: capture (validate-and-drop with empty-list/membership
guards) vs write (coerce-and-carry) are opposite verbs; the null
guard is already the shared leaf. Trigger: capture and write
stop diverging. Home: `model-decode-write-steps` row.

### FR-9 — relation type-vs-coercion merge (REJECTED)

Merging `relation_id_scalar` (annotation-time type selection)
with `coerce_relation_pk_or_none` (decode-time value coercion)
is refused: opposite phases of the same relation, each with its
own failure mode (unknown identity vs unparseable value).
Trigger: annotation and decode stop separating. Home:
`write-relation-id-typing` family (no row change).

### FR-10 — compat re-export deletion (REJECTED)

Deleting the `run_in_one_sync_boundary` re-export from
`resolvers.py` is refused despite zero in-repo importers: the
export is a documented historical-compatibility contract for
out-of-tree importers, and deletion would be a behavior change,
not a duplication removal. Trigger: a deprecation window opens
for the alias. Home: FC-13 (no row).

### FR-11 — mutation-class alias merge (REJECTED)

Merging `WriteMutationClass` (declaration-time union incl. the
string forward reference) with `_AuthorizedClass`
(pipeline-time protocol for `authorize_or_raise`) is refused:
declaration subjects vs call subjects, consumed at different
phases by different seams. Trigger: declaration and pipeline
subjects unify. Home: `snapshot-record-shape` /
`mutation-authorization-seam` rows.

### FR-12 — delete-input seam-vs-materialize merge (REJECTED)

Merging the `input_type_name` delete raise with the
`_materialize_input_for` delete short-circuit is refused: the
seam raises because it is never consulted (fail-loud contract),
while the materializer returns `None` because bind always
consults it (total-function contract). Both compose the kind
maps. Trigger: bind stops consulting the materializer. Home:
`model-flavor-base` / `input-materialize-pair` rows.

### Converge-reaffirmed rejections (re-derived at WT, triggers unfired)

Each merge below was re-derived at current bytes (bodies
re-read, censuses re-run); the recorded difference stands and
its trigger has not fired. Homes are the cited member records
and folder rows; no index change.

- Partial-decoding mechanisms (J1): model decode, form
  `partial=True`, serializer partial stay three substrates.
  Trigger: a shared partial substrate.
- Register vs entry factory (J2): fixed/no-id + fixed-arity
  fixed surfaces stay out of the factory. Trigger: register
  gains an id operation. (FC-2)
- `!= "form"` call gate vs `with_id` seam flag (J3): gate vs
  seam-mirror; `with_id=False` still only at the plain form.
  Trigger: seam-shape divergence. (FC-12)
- `operation_takes_id` vs `!= "form"` vs `with_id` (R3/C3):
  predicate vs gate vs flag, three layers. Trigger: the layers
  collapse.
- Update/delete/change trio vs `has_data_arg` (R4): validation
  sequencing vs resolver dispatch. Trigger: a second id-only
  operation.
- `== "delete"`/`== "update"` vs descriptor flags (R5):
  control-flow vs vocabulary. Trigger: flag-driven dispatch.
- Sealed-execution non-membership (J5): resolvers holds no seal
  body while riding the sealed applier as a consumer. Trigger: a
  seal body lands here. (FC-13)
- Seam delegation-line extraction: the 2 identical
  `return run_permission_classes(...)` returns stay spelled
  (declaration shape, one per seam). Trigger: a third seam or a
  delegation change needing one edit.
- Hook vocabulary collapse (F2): queryset-validated /
  queryset-less / verdict triple stays. Trigger: a queryset +
  verdict hook.
- `input_module_path` flavors: disjoint namespaces stay.
  Trigger: namespace overlap.
- `MODEL_BACKED` vs `COMMON` key sets: inclusion, not
  duplication. Trigger: key divergence.
- `EXCLUDED` vs `None` policy: explicit tag vs absent value.
  Trigger: policy unification.
- `_frozenset_of_attr_names` vs `normalize_field_name_sequence`:
  set-freeze vs sequence-validate. Trigger: caller overlap.
- `_audit_mutation_input_surface` vs finalizer audit: fail-fast
  vs exhaustive. Trigger: audit unification.
- `editable_input_fields` vs orders selector: column basis vs
  orderable subset (opposite selections). Trigger: shared
  basis.
- Input requiredness vs form/serializer requiredness:
  key-space split. Trigger: key-space merge.
- `relation_input_annotation` vs `resolved_relation_annotation`:
  input triple vs output annotation. Trigger: phase merge.
- `_strawberry_field_shape` vs `unwrap_graphql_type`: the
  folder composes the utility. Trigger: shape-rule drift.
- `_mutation_meta` slot spellings (S1): direct attribute reads
  stay un-centralized. Trigger: a second slot name. (FC-13)
- `operation ==` string checks vs predicates: enforcement vs
  vocabulary. Trigger: predicate-driven control flow. (C17)

## Defects

None found. The trace specifically cleared the two suspected
sites: the deleted `_safe_frozenset_membership` leaves zero
dangling references package-wide (no `NameError` risk), and the
truth-migration hunks this item's consolidations touch were
re-checked line by line (FAM-3 edits HEAD-clean lines only;
FAM-1/FAM-2 record their blocking hunks and touch nothing).

## Pending execution

No `proof:` entries outstanding: the FAM-3 failability record
(both entries `pinned`, restores byte-identical) executed in the
workspace copy, and the focused suite ran green in the shared
tree (see Implementation). The final gate re-runs the witnesses
below as listed.

- gate: `uv run pytest -n0 tests/mutations/test_inputs.py --no-cov -q`
  (FAM-3 home: helper + census + spy + all substrate oracles)
- gate: `uv run pytest -n0 tests/mutations/test_sets.py --no-cov -q`
  (bind/seal/matrix regression witness)
- gate: `uv run pytest -n0 tests/mutations/test_fields.py --no-cov -q`
  (factory/guard/signature regression witness)
- gate: `uv run pytest -n0 tests/mutations/test_resolvers.py tests/mutations/test_permissions.py --no-cov -q`
  (pipeline/authorization regression witness)
- gate: `uv run pytest -n0 examples/fakeshop/test_query/test_products_api.py --no-cov -q`
  (live write-surface witness)

Cells: the sharded and pg cells stay unverified (no maintainer
word for `--cell` runs). FAM-3's own proofs are inapplicable by
construction (a pure string mapping exercised with no database);
the audit verdicts are otherwise static. Worker-2 judges the
inapplicability claim.

## Judgment

CONFIRM with one landing: the folder holds no unassigned rule
and no unrecorded cross-boundary twin. FAM-3 consolidated 2→1
with gates and proved failability; FAM-1 and FAM-2 are confirmed
count-2 pairs blocked on exact hunt hunks with specified
migrations; 16 cross-boundary compositions and 12 fresh
rejections plus 20 converge-reaffirmed rejections are recorded
with evidence; 8 falsified member assignments are flagged for
the closeout homing pass (FF-1..FF-8); no defect was found. The
member file artifacts' never-transcribed N/F/R/FL rows are
superseded by the 55 folder rows below at current bytes — no
separate transcription of the member rows is owed.

## Implementation (Worker-1)

Tracked change at the owner, same change as the audit.

`django_strawberry_framework/mutations/inputs.py` (+15/-2):
`_operation_kind_display_word(operation_kind: str) -> str`
(pure, private, documented) + 2 composed call sites in
`_reject_generated_input_collisions` and `build_mutation_input`.
All touched lines are HEAD-clean; the hunt-dirtied subject
f-strings are untouched. No new public symbol (no
`check_public_types` obligation), no `Any`, no cast, no
suppression, no `pragma: no cover`.

`tests/mutations/test_inputs.py` (+130/-1): `import ast`, the
unit test (both arms), the exact-match AST census (1 mapping +
2 composers), the diversion spy (both message sites), and the
`_kind_display_word_spellings` walker. Test prose avoids the
banned words.

Proofs executed (machine `pressure` GREEN throughout, every
heavy command through `heavy`, one heavy job at a time):

- `uv run ruff check --fix` + `uv run ruff format` on exactly
  the 2 touched paths: clean (`All checks passed!`, `2 files
  left unchanged` by the formatter).
- `uv run basedpyright`: `0 errors, 0 warnings, 0 notes`.
- `uv run basedpyright -p pyrightconfig.floor.json`: `0 errors,
  0 warnings, 0 notes`.
- `uv run python scripts/check_truthful_reads.py --check`:
  `checked 120 file(s); ... errors 0`.
- Focused suite (the one authorized shared-tree run):
  `uv run pytest -n0 tests/mutations/test_inputs.py --no-cov
  -q`: `83 passed in 0.81s` (80 pre-existing items + 3 new).
- Failability:
  `uv run python scripts/workspace.py prove
  dry/folder-mutations/consolidate
  ~/dry/tmp/fam3-failability.json --fresh`: exit 0;
  entry 1 (wrong-word mutant) fails exactly the unit + census +
  pre-existing empty-input oracle; entry 2 (re-inline mutant)
  fails exactly the census + spy; both entries `pinned`, both
  restores byte-identical (record
  `.../evidence/proofs/folder-mutations/consolidate/dry-20261010T032915-add592.json`).
  The copy's `blob_before` (`a9428e11…`) matches the shared-tree
  post-edit blob, proving the mutants ran against the landed
  bytes.

Ledger naming for Worker-0 (append under the folder item's run):
`mutations/inputs.py` FAM-3 +15/-2 (helper + 2 composers);
`tests/mutations/test_inputs.py` +130/-1 (import + 3 tests +
walker).

## Index rows for Worker-0

Holding-item cell for every row: Folder integration
`mutations/`. Member file items never received index rows, so
the N/F/R/FL records below are superseded by — not duplicated
with — these folder rows; transcribe as listed. Two rows name
new families (`mutation-payload-name`, `static-read-callability`)
without Families items (blocked-on-hunt; no item until
unblocked). One row is consolidated (FAM-3, this run).

| `mutations-leaf-manifest` | `django_strawberry_framework/mutations/__init__.py::__all__` (4-name mirror + re-export block; member F1 homed here) | `django_strawberry_framework/mutations/__init__.py` | Folder integration `mutations/` | file-local | |
| `mutations-module-map-prose` | `django_strawberry_framework/mutations/__init__.py` module docstring (Decisions 4/5/15 quartet+2 map; member F2 homed here) | `django_strawberry_framework/mutations/__init__.py` | Folder integration `mutations/` | file-local | forms twin stays a same-shape sibling |
| `mutation-operation-descriptors` | `django_strawberry_framework/mutations/operations.py::MutationOperationDescriptor` (4 declarations + registry + 3 predicates + 5 derivations + reject; cross-folder consumers re-derived) | `django_strawberry_framework/mutations/operations.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/mutations/permissions.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | |
| `mutation-construction-target-guard` | `django_strawberry_framework/mutations/fields.py::_validate_mutation_target` + `_has_mutation_protocol` + `_is_registered_mutation_target` + `_ABSENT` (5 axes to typed ConfigurationError; FF-2 settles the truth mechanism) | `django_strawberry_framework/mutations/fields.py` | Folder integration `mutations/` | file-local | |
| `write-field-lazy-forward-ref` | `django_strawberry_framework/mutations/fields.py::_lazy_ref` (lazy leaf; 3 auth call sites) | `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `mutations/` | file-local | |
| `lazy-root-field-signature` | `django_strawberry_framework/mutations/fields.py::build_lazy_field_signature` (sync/async x4 return grammar; 1 auth call site) | `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `mutations/` | file-local | |
| `mutation-signature-synthesis` | `django_strawberry_framework/mutations/fields.py::_synthesized_mutation_signature` (implementation + lazy annotation + parametrization) | `django_strawberry_framework/mutations/fields.py` | Folder integration `mutations/` | file-local | FAM-1 site B named separately |
| `mutation-field-factory-body` | `django_strawberry_framework/mutations/fields.py::DjangoMutationField` (dispatch + marker stamp + directives + name fallback) | `django_strawberry_framework/mutations/fields.py` | Folder integration `mutations/` | file-local | |
| `mutation-class-marker` | `django_strawberry_framework/mutations/fields.py::MUTATION_CLASS_MARKER` (1 stamp + 2 readers) | `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/schema.py`, `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `mutations/` | file-local | reader paths refreshed (FF-6) |
| `column-less-relation-typing` | `django_strawberry_framework/mutations/inputs.py::annotate_queryset_relation` + related/require pair (column-less id-typing; forms/serializer call) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | Folder integration `mutations/` | file-local | member N2 homed here |
| `model-column-write-classification` | `django_strawberry_framework/mutations/inputs.py::model_column_write_kind` (5-way classification + FILE early arm) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | Folder integration `mutations/` | file-local | member N3 homed here |
| `model-column-write-annotation` | `django_strawberry_framework/mutations/inputs.py::relation_input_annotation` + write/input wrappers (scalar/relation kinds stay apart) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | Folder integration `mutations/` | file-local | member N4 homed here |
| `mutation-input-attr-normalizer` | `django_strawberry_framework/mutations/inputs.py::_frozenset_of_attr_names` (bare-str hostile arm; 2 callers) | `django_strawberry_framework/mutations/inputs.py` | Folder integration `mutations/` | file-local | member FL1 homed here |
| `mutation-editable-basis` | `django_strawberry_framework/mutations/inputs.py::editable_input_fields` + `_carrier_backed_link` pair (full-vs-selected basis pair in the descriptor + bind/auth callers) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member FL2 + carrier evolution homed here |
| `mutation-create-requiredness` | `django_strawberry_framework/mutations/inputs.py::input_field_required` (CREATE/PARTIAL table + form-necessary arm) | `django_strawberry_framework/mutations/inputs.py` | Folder integration `mutations/` | file-local | member FL3 homed here |
| `mutation-input-surface-audit` | `django_strawberry_framework/mutations/inputs.py::_audit_mutation_input_surface` (single guardrail call) | `django_strawberry_framework/mutations/inputs.py` | Folder integration `mutations/` | file-local | member FL4 homed here |
| `mutation-input-namespace-lifecycle` | `django_strawberry_framework/mutations/inputs.py::make_input_namespace` + consume/clear/materialize + bus row (legacy `_pascalize_token` alias: 0 importers) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member FL5+FL8 homed here |
| `mutation-input-generator` | `django_strawberry_framework/mutations/inputs.py::build_mutation_input` (assembly + selected-field pre-walk + FAM-3 composer) | `django_strawberry_framework/mutations/inputs.py` | Folder integration `mutations/` | file-local | member FL6 homed here |
| `mutation-collision-policy` | `django_strawberry_framework/mutations/inputs.py::_reject_generated_input_collisions` + `_GeneratedInputFieldName` (2 guards + record + FAM-3 composer) | `django_strawberry_framework/mutations/inputs.py` | Folder integration `mutations/` | file-local | member FL7 homed here |
| `mutation-non-field-key` | `django_strawberry_framework/mutations/inputs.py::NON_FIELD_ERROR_KEY` (pin + 2 readers) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/rest_framework/resolvers.py` | Folder integration `mutations/` | file-local | member FL9 homed here |
| `mutation-excluded-kind` | `django_strawberry_framework/mutations/inputs.py::EXCLUDED` (tag + membership duel + 3 handler sites) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member FL10 homed here |
| `mutation-kind-tokens` | `django_strawberry_framework/mutations/inputs.py::CREATE` + `PARTIAL` (display bridge for the descriptor vocabulary) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/operations.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | |
| `mutation-payload-slot-rule` | `django_strawberry_framework/mutations/inputs.py::payload_object_slot` + `_RESERVED_PAYLOAD_ATTRS` (6 call sites) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member payload-subrule homed here |
| `generator-kind-display-word` | `django_strawberry_framework/mutations/inputs.py::_operation_kind_display_word` (2 sites to 1 + 2 composers; unit + census + spy; both mutants proved) | `django_strawberry_framework/mutations/inputs.py` | Folder integration `mutations/` | consolidated | FAM-3 landed this run |
| `mutation-payload-name` | `django_strawberry_framework/mutations/inputs.py::build_payload_type` (owner candidate; suffix spelled twice: materializer + fields prediction; named FAM-1 by Folder integration `mutations/`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/fields.py` | Family `mutation-payload-name` | open (run 13 FAM-1: CONFIRMED count-2 but blocked-on-hunt — fields site inside the truth-migration hunk, migration specified but unlanded, zero edits; verified pending W2, pending execution) | |
| `static-read-callability` | `django_strawberry_framework/mutations/fields.py::_is_callable_member` (owner candidate; static-read callability spelled twice: named helper + sets.py inline; named FAM-2 by Folder integration `mutations/`) | `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/mutations/sets.py` | Family `static-read-callability` | open (run 13 FAM-2: CONFIRMED count-2 but blocked-on-hunt — both lines hunt dirt, owner choice deferred, zero edits; verified pending W2, pending execution) | |
| `write-auth-result-contract` | `django_strawberry_framework/mutations/permissions.py::_require_sync_bool_auth_result` (sync-bool verdict; 3 seam decisions) | `django_strawberry_framework/mutations/permissions.py`, `django_strawberry_framework/mutations/resolvers.py` | Folder integration `mutations/` | file-local | member F3 homed here |
| `permission-class-walk` | `django_strawberry_framework/mutations/permissions.py::run_permission_classes` (first-deny + closed-default walk; 2 seam callers) | `django_strawberry_framework/mutations/permissions.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | Folder integration `mutations/` | file-local | member F4 homed here |
| `model-permission-default-check` | `django_strawberry_framework/mutations/permissions.py::DjangoModelPermission` (action-map read + staff/superuser arms) | `django_strawberry_framework/mutations/permissions.py`, `django_strawberry_framework/mutations/sets.py` | Folder integration `mutations/` | file-local | composed as the model-backed default |
| `model-less-deny-default` | `django_strawberry_framework/mutations/permissions.py::DenyAll` (closed default; 2 wirings) | `django_strawberry_framework/mutations/permissions.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | Folder integration `mutations/` | file-local | member F6 homed here |
| `model-relation-decode-coloring` | `django_strawberry_framework/mutations/resolvers.py::_decode_relations` + single/list decoders + visibility re-checks | `django_strawberry_framework/mutations/resolvers.py` | Folder integration `mutations/` | file-local | member R1 homed here |
| `mutation-exclude-carve-out` | `django_strawberry_framework/mutations/resolvers.py::_model_excluded_decode` (per-model exclusion + records) | `django_strawberry_framework/mutations/resolvers.py` | Folder integration `mutations/` | file-local | member R2 homed here |
| `model-decode-write-steps` | `django_strawberry_framework/mutations/resolvers.py::_model_decode_step` + `_model_write_step` (strict-unpack arms incl EXCLUDED) | `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member R3 homed here; register repacks then rides |
| `mutation-delete-rider` | `django_strawberry_framework/mutations/resolvers.py::_run_delete` + `_delete_write_step` + `_delete_or_field_errors` (fetch/authorize/delete/refetch + message) | `django_strawberry_framework/mutations/resolvers.py` | Folder integration `mutations/` | file-local | member R4 homed here |
| `mutation-authorization-seam` | `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` + `_authorized_or_none` (decision routing + target naming) | `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `mutations/` | file-local | member R5 homed here; auth fixed surfaces compose |
| `mutation-validation-save-mappers` | `django_strawberry_framework/mutations/resolvers.py::save_or_field_errors` + `forced_save_or_field_errors` + `_full_clean_or_field_errors` (3 race/validation contracts) | `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/forms/resolvers.py` | Folder integration `mutations/` | file-local | member R6 homed here |
| `mutation-locate-lookup` | `django_strawberry_framework/mutations/resolvers.py::locate_instance` + `coerce_lookup_id` + not-found/invalid-id errors (status verdicts) | `django_strawberry_framework/mutations/resolvers.py` | Folder integration `mutations/` | file-local | member R7 homed here |
| `mutation-error-refetch-payload-tail` | `django_strawberry_framework/mutations/resolvers.py::error_payload_builder` + `payload_cls_for` + `refetch_optimized` (builder + stash read + refetch; single set_rollback write) | `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member R8 homed here |
| `sealed-mutation-meta-slot` | `django_strawberry_framework/mutations/sets.py::_ValidatedMutationMeta` (record-level set/del seal; walk reads the slot) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/mutations/permissions.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/schema.py` | Folder integration `mutations/` | file-local | auth snapshot mirror excluded with differences |
| `sealed-mutation-meta-head` | `django_strawberry_framework/mutations/sets.py::make_meta_validating_metaclass` (2 instances: model + plain-form) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py` | Folder integration `mutations/` | file-local | auth holder excluded with differences (FF-8) |
| `write-meta-shape-vocabulary` | `django_strawberry_framework/mutations/sets.py::COMMON_WRITE_META_KEYS` + `MODEL_BACKED_WRITE_META_KEYS` + typo guard + `normalize_meta_field_selection` | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | member FL1 homed here |
| `non-delete-operation-gate` | `django_strawberry_framework/mutations/sets.py::require_non_delete_operation` (ModelForm + serializer matrices call; model validates directly, plain is fixed-create) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | member FL3 homed here |
| `backing-resolution-type-gate-kit` | `django_strawberry_framework/mutations/sets.py::backing_model_of` + require/resolve 5 (cross-flavor gates + leaf) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member FL4 + `backing_model_of` homed here |
| `construction-hook-shape` | `django_strawberry_framework/mutations/sets.py::construction_kwargs` + `_hook_overridden` (declared-construction capture) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | member FL5 homed here |
| `shape-build-cache-discipline` | `django_strawberry_framework/mutations/sets.py::cached_build_input` + `build_and_stash_input` + cache + clear row | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | member FL6 homed here |
| `declaration-registry-mechanics` | `django_strawberry_framework/mutations/sets.py::make_declaration_registry` + record + model ledger + aliases (3 products) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `mutations/` | file-local | member FL7 homed here |
| `snapshot-record-shape` | `django_strawberry_framework/mutations/sets.py::_ValidatedMutationMeta` slots + `_snapshot_from_validated_meta` (slot census) | `django_strawberry_framework/mutations/sets.py` | Folder integration `mutations/` | file-local | member FL8 homed here; form/serializer slots ride |
| `permission-lock-validation` | `django_strawberry_framework/mutations/sets.py::_validate_permission_classes` + `validate_select_for_update` + `model_backed_permission_and_lock` | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | member FL9 homed here; FAM-2 site B named separately |
| `resolver-seam-factory` | `django_strawberry_framework/mutations/sets.py::resolver_seams` + 2 private builders + 4 declarations (sync/async x with/without id) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py` | Folder integration `mutations/` | file-local | member FL10 homed here |
| `model-flavor-base` | `django_strawberry_framework/mutations/sets.py::DjangoMutation` (matrix + seams + slots + input_module_path default) | `django_strawberry_framework/mutations/sets.py` | Folder integration `mutations/` | file-local | member FL11 homed here |
| `custom-input-naming-gate` | `django_strawberry_framework/mutations/sets.py::_validate_input_class` + `_expected_input_attr_names` (suffix + surface match) | `django_strawberry_framework/mutations/sets.py` | Folder integration `mutations/` | file-local | member FL12 homed here |
| `primary-type-error-shapes` | `django_strawberry_framework/mutations/sets.py::_resolve_primary_type` (resolution + error shapes) | `django_strawberry_framework/mutations/sets.py` | Folder integration `mutations/` | file-local | member FL13 homed here |
| `input-materialize-pair` | `django_strawberry_framework/mutations/sets.py::_materialize_input_for` + `_materialize_merged_input` (generated vs merged) | `django_strawberry_framework/mutations/sets.py` | Folder integration `mutations/` | file-local | member FL14 homed here |
| `override-shape-lock` | `django_strawberry_framework/mutations/sets.py::_validate_relation_override_types` + shape helpers (override-half lock) | `django_strawberry_framework/mutations/sets.py` | Folder integration `mutations/` | file-local | member FL15 homed here |
| `bind-drain-trio` | `django_strawberry_framework/mutations/sets.py::bind_mutation_outputs` + `bind_write_declarations` + `bind_mutations` (drain + 2 riders + finalizer call) | `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/types/finalizer.py` | Folder integration `mutations/` | file-local | member FL16 homed here |

### Corrections to existing rows

- C-1 `related-object-visibility-recheck`: the files/notes cell
  cites the transitive consumer via stale line numbers
  (`:618`/`:654`). Refresh to symbol cites (durable):
  `mutations/resolvers.py::_decode_single_relation_id` /
  `::_decode_relation_id_list` composing
  `decode_visible_relation_ids` (calls at WT `:640`/`:676`,
  defs at `:611`/`:653`). Evidence: FC-6 census (exactly 2
  model decoders + 1 serializer wrapper call the primitive).

## Independent verification (Worker-2)

### Pre-read trace (written before opening ## Findings)

Sequencing disclosure: this trace was derived from pins, the item-scoped diff,
all seven target files at WT bytes, `git show HEAD` / `git show BASE` reads, and
my own package greps — all on record before I opened any finding. Navigation
leaks: (a) I scanned the artifact's `^## ` / `^### ` heading titles to place this
section, which revealed the finding IDs under ## Findings (FAM-1
`mutation-payload-name`, FAM-2 `static-read-callability`, FAM-3
`generator-kind-display-word`, FC-1..FC-16, FF-1..FF-8, FL-1..FL-7, FR-1..FR-12)
before this trace was written; (b) anchoring this insert exposed ~19 tail lines
of ## Implementation (index rows FL10–FL16 + correction C-1). Mitigation: the
payload-name and display-word analyses below were fully derived pre-exposure
(greps on record); FAM-2's *identity* came from the heading, but its *count*
(two exact spellings, neighbours excluded on contract) and its *block* (both
sites hunt-owned, byte-attributed below) are my own derivation. I claim no
independent discovery of FAM-2's name, of the FC/FL/FR row set, or of any FF
flag. All of ## Findings lines 201–842 remained unread until this section was
complete.

Pins (verified, not trusted): HEAD `23b5f421` resolves; WT blobs match dispatch
for six files; `mutations/inputs.py` WT is `a9428e11`, NOT the pinned `bb329e4d`
— because `bb329e4d` is the ITEM_BASELINE blob
(`git rev-parse BASE:.../inputs.py` → `bb329e4d…`), i.e. the dispatch "WT" pin
was the baseline-time state and the delta `bb329e4d → a9428e11` is exactly
Worker-1's landed consolidation. HEAD blob `f821661e` matches dispatch.
Item-scoped diff `git diff BASE -- mutations/ tests/mutations/`:
`M inputs.py (+15/-2)`, `M tests/mutations/test_inputs.py (+130/-0)`,
total +145/-2, zero new files, no other path touched. (Other `tests/mutations/`
and folder dirt vs HEAD is concurrent work outside the item baseline.)
My numstat read already fixes the diff-figure question (ruled below): the test
file is +130/-0; any `-1` on the test file is a record slip.

My AST census (own instrument: every `ast.Module.body` member that is
FunctionDef/AsyncFunctionDef/ClassDef/Assign/AnnAssign, imports and the
TYPE_CHECKING block excluded): `__init__` 1, `fields` 10, `inputs` 37 (incl.
the NEW `_operation_kind_display_word`), `operations` 15, `permissions` 5,
`resolvers` 35, `sets` 46 — 149 members. I check the artifact's Enumeration
against this member by member in reconciliation (instrument differences are
expected; every member must still land somewhere).

Candidate 1 — generator-kind display word (my FAM-3 pre-read).
BASE sites: `inputs.py:922` (`_reject_generated_input_collisions`) and
`inputs.py:1032` (`build_mutation_input`), both spelling
`kind = "create" if operation_kind == CREATE else "update"` byte-identically;
HEAD carries the same two spellings (`:904`, `:1014`), so both swapped lines are
HEAD==BASE clean — concurrent work touched only ADJACENT lines (the
`truth.name(model)` subjects, already in BASE). Package-wide sweep for the rule
(`"create" if`, `operation_kind ==`, `operation_kind !=`): no third word-mapping
spelling exists. Nearest neighbours, each a different contract, count-1 and
correctly left alone: `sets.py:1701`
(`"input_class" if operation_kind == CREATE else "partial_input_class"` —
override-attr vocabulary, not message words; renaming a Meta key must not
reword errors); `inputs.py:987` (`is_create` bool); `inputs.py:838`
(`is_partial=` bool, deliberately `!= CREATE` where forms uses `== PARTIAL`
because the FORM sentinel is create-shaped); every `rest_framework` /
`forms` `== PARTIAL` / `== CREATE` use (bools or guard dispatch).
Change challenge: add a third generator kind (or reword "update") → both
message sites must move together: count 2, one rule, one responsibility
(human-facing word for a generator kind in configuration-error subjects).
Owner I would choose: module-private `_operation_kind_display_word` in
`mutations/inputs.py` — the same choice. Alternatives refused on the merits:
(a) `operations.py` reverse map (`{op.input_kind: op.name}`) — dependency
direction forbids it (`operations.py` imports CREATE/PARTIAL FROM `inputs.py`;
an `inputs → operations` module edge is a cycle), and descriptor `name` is
operation vocabulary while CREATE/PARTIAL is generator vocabulary;
(b) hoisting to `utils/inputs.py` — wrong breadth: forms' FORM sentinel is
create-shaped yet `!= CREATE`, so a shared helper would mis-word a form reuse;
(c) a dict lookup — changes unknown-kind behaviour (KeyError vs "update");
the IfExp preserves exact semantics. Shape: pure private function, both sites
compose by name. Test tier: package tier is correct — the collision subject
needs a colliding model (no fakeshop fixture may be added in-item) and the
empty-input guard is unreachable via a real query (class-creation validation
rejects empty narrowings first), so live-tier coverage is impossible by
construction, not by fixture gap.

Candidate 2 — `<Name>Payload` grammar (my FAM-1 pre-read).
Definitions: `inputs.py` builder (`type(f"{mutation_name}Payload", …)`,
WT:1150 — HEAD==BASE==WT clean, concurrent diff never touches the line) and
`fields.py` return forward-ref
(`_lazy_ref(f"{truth.name(mutation_cls)}Payload", …)`, WT:280). Consumers that
derive, not define: `sets.py:1884` + `auth/mutations.py:1491,1497`
(`truth.name(payload_cls)` read-backs) and `resolvers.py:1451`
(`getattr(inputs, _payload_type_name)`). Change challenge: rename the payload
suffix → exactly the two definition sites move: count 2, CONFIRMED. Block: the
fields.py site is hunt-owned — BASE spells `truth.name(mutation_cls)` where
HEAD spells `mutation_cls.__name__` (truth migration), and no ## Owned changes
row covers `mutations/fields.py` or any truth line (ledgered DRY dirt in the
folder is only the adopted `relation_input_python_attr` orphan). A
consolidation must rewrite that line (no landable subset: an owner + a
single-spelling gate without migrating the field side is born red, and DRY.md
bars born-red gates). BLOCKED-ON-HUNT, independently confirmed. Owner I would
choose once unblocked: `mutations/inputs.py` (the builder's module; fields.py
already imports INPUTS_MODULE_PATH from it — no new edge).

Candidate 3 — static-read callability (identity from heading, count/block my
own). Exact rule `callable(x) or truth.is_instance(x, classmethod)` spelled
twice: `fields.py:140` (`_is_callable_member`, with 3 in-file composers at
`:158–160`) and `sets.py:1036` (inline in `_validate_permission_classes`).
Neighbours excluded on contract: `_django_patches.py` `__func__`-unwrap reads,
`schema.py:1232` SchemaExtension-or-callable, plain `callable()` checks —
different predicates, count-1 each. Change challenge: static/class method
callability semantics change (e.g. staticmethod handling) → both sites move:
count 2, CONFIRMED. Block: BOTH sites are hunt-owned — the fields.py helper is
ABSENT at HEAD (added whole by the truth migration) and the sets.py inline
spelling rewrote HEAD's `getattr(entry, "has_permission", None)` shape; no
ledger row covers either. BLOCKED-ON-HUNT, independently confirmed. Owner once
unblocked: the fields.py helper promoted or a shared leaf — a pass-2 decision;
today any edit touches concurrent work.

Missed-consolidation sweep (my own, pre-read): (i) `DjangoMutation {kind}
input for {model}` subject PREFIX shared by `inputs.py:938` and `:1047` — a
plausible count-2 display-subject rule, but both lines are hunt-owned
(`truth.name`) and the full messages differ (subject vs sentence); at most a
blocked family, never a landable miss; (ii) `== "delete"` / `!= "delete"` /
`!= "form"` discriminations (`sets.py:1260,1279`, `resolvers.py:933`,
`fields.py:313`, `operations.py:124`) — each answers a different question
(input? pipeline? id-kwarg? set membership) against single-owned predicates;
rejections; (iii) `payload_object_slot` — one definition, six composers;
(iv) `NON_DELETE_OPERATION_INPUT_KIND.get` — one table, two consumers;
(v) no other `}Payload` producer beyond the FAM-1 pair. No landable
consolidation missed: FAM-3 was the only shippable 2→1 in the folder.

Matrix pre-read (what each axis must cover from my own reading): axis 1
cross-flavor — forms/serializer/auth ride `run_write_pipeline_sync`,
`resolver_seams`, `payload_object_slot`, `payload_cls_for`, the bind drain;
axis 2 sync/async — `make_resolver_entries` + `run_pipeline_async` single-site
the boundary; axis 3 derived knowledge — `_relation_field_index` rides
`relation_input_python_attr` (adopted orphan, in BASE), `input_type_name` rides
`mutation_input_shape().type_name`; axis 4 round-trip — build
(`build_mutation_input`) vs reverse map (`mutation_input_field_specs`) vs
decode (`decode_provided_fields` riders); axis 5 other media — docstrings carry
owner clauses, tests pin behaviour; axis 6 omission — delete-takes-no-input
(`input_type_name` raise + `_materialize_input_for` None + field-factory
`operation_takes_data` gate), DenyAll-vs-model-permission defaults. Judged
against Worker-1's discharge in reconciliation.

Banned-word sweep (own): added test lines contain none of plan/audit/sweep/
restored/hardening/previously/worker/grader/feedback (substring grep, clean).
Production helper docstring states the invariant with zero process provenance.

### Reconciliation (post-read)

FAM-3 — CONCUR fully. Both BASE sites, the count-2 challenge, the owner, and
the no-third-site sweep match my pre-read derivation exactly, including the
`sets.py:1701` override-attr neighbour excluded on vocabulary grounds and the
forms-FORM-sentinel reason against hoisting. Ownership challenge answered:
`operations.py` is cycle-blocked (it imports CREATE/PARTIAL from `inputs.py`),
`utils/inputs.py` is breadth-wrong (FORM sentinel), a dict changes
unknown-kind behaviour. Test tier judged correct (collision needs a
non-addable fixture; empty-input unreachable via queries). Observable
equivalence on principle-8 axes: same IfExp evaluated once at the same program
point in both forms — no exception, ordering, query, transaction, or
cancellation surface exists to differ. No oracle rewritten (test diff is pure
addition). One record correction: the census sentence omits the serializer
guard hit — CC-2 below. Verdict impact: none (family count and gates stand).

FAM-1 — CONCUR (count-2 CONFIRMED, BLOCKED-ON-HUNT). My pre-read pair (builder
WT:1150 HEAD-clean + field prediction WT:280 hunt-owned) matches sites A/B;
my `}Payload"` sweep independently returns exactly 2 in production; the
`sets.py`/stash/form/serializer/auth exclusions check out (auth names are full
literals, spot-verified `auth/mutations.py:1059`). Block verified by diff
content: site B's line is inside hunt's truth-migration hunk (HEAD
`__name__` vs BASE `truth.name`), no ledger row covers `mutations/fields.py`,
and no landable subset exists (owner+gate without migrating B is born red).
Specified migration (pure `payload_type_name_for` in `inputs.py` + spy + AST
census) is sound for unblock; my owner choice agrees (`inputs.py` — fields.py
already imports from it). Freshness: hunk `@@ -254,7 +277,7` + exact line
recorded; excluded modules named. Family-row-without-Families-item shape
matches the run-13 extensions/filters blocked precedents.

FAM-2 — CONCUR (count-2 CONFIRMED, BLOCKED-ON-HUNT). Identity came from the
heading (disclosed); count and block are my own: exact rule
`callable(x) or truth.is_instance(x, classmethod)` spelled at `fields.py:140`
(+3 composers) and `sets.py:1036`, with `_django_patches.py` (3 unwrap reads),
`schema.py:1232`, and plain checks excluded on contract by my own grep. Block
verified: helper ABSENT at HEAD (added whole by the hunt), inline site rewrote
HEAD's `getattr` shape, no ledger row covers either. Migration option A is
cycle-safe as claimed (fields→sets import is function-local, verified at
`fields.py:173`); option B correctly waits on the hunt landing. Pins verified:
site-A test exists (`test_fields.py:175`), site-B oracles exist
(`test_sets.py:537,566`).

Diff-figure ruling: TRUE figures are production +15/-2, test +130/-0, total
+145/-2 (my own numstat read, corroborated by Worker-0's zero-`-` count). The
artifact's two `+130/-1` strings (Implementation + Ledger naming) are record
slips — CC-1, verdict-neutral carried correction (load-bearing only as the
ledger's durable figure, and the true figure is mechanically unambiguous, so
no Worker-1 rework is owed; Worker-0 records +130/-0).

Enumeration — VERIFIED member by member. Worker-1's instrument
(`len(ast.Module.body)` + def/class counts) reproduces exactly at WT under my
own run: 7/0, 24/8, 59/30, 21/5, 14/4, 62/32, 71/35. Cross-checked against my
independent 149-member def/assign census: every member lands in a FAM site, an
indexed-family consumer edge (FC-2/FC-13), or an FL row's cited owner set —
including the members most likely to strand (`_ABSENT`, `_pascalize_token`,
`EXCLUDED`, `MUTATION_CLASS_MARKER`, `DenyAll`, the nested
`_model_excluded_decode`, `resolve_mutation_sync/async`, `_DeclarationT`).
No unassigned member; sampling played no role.

Matrix — DISCHARGED against the real surface on all six axes. Axis 2
re-derived: exactly 2 code `async def`s (both in `resolvers.py`), zero code
`await`s in the other six files (remaining hits are a docstring line and a
recourse string literal — both read). Axes 1/3/4/6 substance is the FC/FR
record, each claim re-verified below. Axis 5: oracle count (83) corroborated
by my own 83-passed run; live rows cited as pins, not re-run (correct — gates
re-run them).

Challenges C1–C17 — CONCUR. C1/C2/C3 are the FAM counts (re-derived above);
C4–C16 each name a genuine single owner I confirmed by body read; C17's
refusal matches my pre-read judgment (call/dispatch/backstop vs vocabulary —
`fields.py:313`, `sets.py:1260,1279`, `resolvers.py:933,414` each answers a
different question).

FC-1–FC-16 — all CONCUR, every census re-derived: FC-1 (`"add"`/`"change"` in
exactly 2 descriptor members); FC-2 (5 rider call sites, 3 entry products,
3 recourse nouns, 1 code `await` of `run_pipeline_async`, `check_deadline`
head present at `resolvers.py:288`); FC-3 (slot + head seals, 2 metaclass
products, `_SealedAuthHolderMeta(DjangoMutationMetaclass)` at
`auth/mutations.py:262`); FC-4 (single envelope; ok=True success 1 site +
ok=False inside the single error builder — both halves accounted); FC-5
(adopted orphan byte-intact per ledger, `mutation_input_type_name` 1 caller,
naming-scheme gate present at `test_inputs.py:1517` and green in my run);
FC-6 (4 relation-typing layers + 3 `decode_visible_relation_ids` callers at
`:640`/`:676`/`rf:313`); FC-7 (2 seam callers, 1 action-map read,
`DenyAll` 2 wirings); FC-8 (2 drain riders, 3 declaration-registry + 5
input-namespace products, 3 in-folder bus registrations, finalizer calls the
model drain); FC-9 (1 stamp + 2 by-name readers at `schema.py` and
`extensions/resource_policy.py`); FC-10 (`_lazy_ref` x3 + signature builder
x1 auth call sites, 5 `validated_field_directives` consumer files);
FC-11 (verdict CONCUR — the two runtime sentences differ and the template
merge stays refused — but the parenthetical clause LABELS are invented; the
real difference is the member-F1 record's: write owns hook naming + bool
clause + has_perm/backend clause, gate owns gate naming + subject clause,
one shared clause — CC-15);
FC-12 (all literal sites stand with triggers unfired); FC-13 (compat
re-export has zero in-repo importers — verified; seal non-membership holds);
FC-14 (`snapshot_or_meta_backing` zero hits package-wide); FC-15 (one
write-path `check_deadline`, forms/serializer inherit, auth/login separate);
FC-16 (`backing_model_of` 1 body + 16 call sites at 7/6/2/1 across
sets/rf/auth/forms — exact).

FF-1–FF-8 — evidence verified for all eight; non-reopening correct in every
case (each flag retires or refreshes member-record TEXT at closeout; no plan
index row cites any falsified content, so no row reopens). Two corrections:
FF-1's core stands (helper gone, zero refs package-wide incl. tests/examples,
no plan row cites it) but its second sentence is FALSE — member R2 never
referenced the deleted arm (no "safe" string in the member artifact; HEAD
bodies don't call it; `-S` archaeology: the helper never touched
`resolvers.py` in history) — CC-7 strikes it, and member R2 stays homed (CC-4
fixes its symbol). FF-7's substance stands (both flavors import directly from
`mutations.operations`, verified) but the cited ID is wrong — the operations
member artifact has no F4; the re-export note lives in F1's consumer census
— CC-8. FF-2/FF-3/FF-4/FF-5 WT counts reproduce exactly under my own
statement census; FF-6 reader paths verified; FF-8 subclass verified.

FL-1–FL-7 — the row-group claims hold (2/1/6/15/4/8/17 = 53 file-local rows +
2 family rows = 55, recounted); per-row rulings in the table below, with 9
row corrections (all record-only, all exact).

FR-1–FR-12 — every rejection carries its contract difference + trigger +
durable home; all CONCUR. FR-1 matches my pre-read candidate (i) including
the hunt-line + message-contract reasons. FR-2's premise verified
(`utils/truth.py` confirmed untracked). FR-7's REJECTION stands (strict
unpack is the arity guard — verified at `resolvers.py:1053`) but its
evidence clause names phantom `_decoded_or_raise` — CC-3 replaces it with
the real mechanism. FR-10's keep-the-alias judgment is sound (documented
compat; deletion would be behavior change, verified zero in-repo importers).

Converge-reaffirmed — 20 bullets, recounted; each names its trigger. Spot
re-derivation of the riskiest (J1 partial substrates, R5/FC-13 seal
non-membership, `_mutation_meta` S1 spellings, C17 literal-vs-predicate)
confirms bodies unchanged and triggers unfired. No index change — correct.

### Carried corrections (verdict-neutral; Worker-0 applies at transcription)

All are record-only: each underlying verdict/count/owner/gate stands on
tree bytes, and each fix below is the exact mechanical string. No Worker-1
rework is owed, so none of these is revision-needed.

- CC-1 (diff figure, 2 spots): Implementation "`tests/mutations/test_inputs.py`
  (+130/-1)" → (+130/-0); Ledger naming "`tests/mutations/test_inputs.py`
  +130/-1" → +130/-0. Proof: item numstat `15/2` + `130/0` = `145/2`.
- CC-2 (FAM-3 census sentence): "`operation_kind == CREATE` returns 4 hits
  package-wide (2 display mappings + 1 boolean + 1 override-attr selection in
  `sets.py`)" → 5 hits pre-edit (2 display + 1 boolean `inputs.py:987` + 1
  override-attr `sets.py:1701` + 1 serializer per-declaration guard dispatch
  `rest_framework/sets.py:886`, a different contract, excluded); post-edit 4
  (1 mapping in the helper + the same 3 non-members). Family count unchanged.
- CC-3 (FR-7 evidence): strike "and `_decoded_or_raise` is the single verdict
  both ride" (`_decoded_or_raise` exists nowhere package-wide); the real
  mechanism is the strict 3-tuple unpack at `resolvers.py:1053` plus the
  skeleton's two `isinstance(..., list)` step checks. Rejection unchanged.
- CC-4 (row `mutation-exclude-carve-out`): owner
  `resolvers.py::_model_excluded_decode` (the EXCLUDED-tag capture handler,
  nested in `_decode_relations` — member-R3 territory, homed under
  `model-relation-decode-coloring`) → the member-R2 trio
  `resolvers.py::_provided_attr_names` + `::_unprovided_exclude` +
  `::_unique_constraint_groups`; description "(per-model exclusion + records)"
  → "(full_clean exclude-set carve-out minus co-constrained members)".
- CC-5 (row `mutation-authorization-seam`): drop phantom `_authorized_or_none`
  (exists nowhere); owner is `resolvers.py::authorize_or_raise` alone —
  decision routing + model-less target-name fallback both live in that one
  body (`resolvers.py:1238-1277`). Files cell (auth composes it) stands.
- CC-6 (row `snapshot-record-shape`): drop phantom `_snapshot_from_validated_meta`
  (exists nowhere); owner is `sets.py::_ValidatedMutationMeta` (`__slots__` +
  `__init__`) per member FL8. Seal aspect stays in `sealed-mutation-meta-slot`.
- CC-7 (FF-1 second sentence): strike "The `resolvers.py` R2 reference to the
  same deleted arm is falsified alongside" — member R2 never referenced the
  helper (zero "safe" strings in the member artifact) and `-S` archaeology
  proves the helper never touched `resolvers.py` in history. FF-1 core + R2
  homing (CC-4) stand; closeout retires only the sets-FL2 assignment.
- CC-8 (FF-7 cite): "The `operations.py` F4 record" → F1 record (the member
  artifact has no F4; the re-export note is in F1's consumer census).
  Substance (direct imports now) verified true.
- CC-9 (row `model-permission-default-check`): strike "staff/superuser arms" —
  `has_permission` (`permissions.py:188-226`, read in full) has no such arms
  (superuser pass-through, if any, is Django's `has_perm`, not this body).
- CC-10 (row `model-column-write-classification`): "5-way classification" → 4
  outcomes (RELATION_MULTI / RELATION_SINGLE / FILE / SCALAR); EXCLUDED is
  applied by callers under its own row.
- CC-11 (row `mutation-create-requiredness`): "(CREATE/PARTIAL table +
  form-necessary arm)" → "(has_default/null/blank predicate; consulted for
  create only)" — the body has no kind table (PARTIAL-forces-optional lives
  at the `build_mutation_input` call site) and no form arm.
- CC-12 (row `mutation-field-factory-body`): strike "name fallback" — no such
  behavior in `DjangoMutationField` (dispatch + marker stamp + directives
  verified).
- CC-13 (row `lazy-root-field-signature`): "(sync/async x4 return grammar; 1
  auth call site)" → "(root/info + keyword-only args + lazy return; 1 auth
  call site)" — the x4 grammar belongs to the seam declarations, not this
  builder.
- CC-14 (row `mutation-input-namespace-lifecycle`): owner cite
  `inputs.py::make_input_namespace` names an IMPORTED factory; read owner as
  the in-module `materialize_mutation_input_class` +
  `clear_mutation_input_namespace` + ledger + bus row.
- CC-15 (FC-11 parenthetical): the quoted clause labels ("queryset methods",
  "presence-probe footnote", etc.) appear nowhere in the runtime sentences;
  read the difference as the member-F1 record proves it (see FC-11 ruling).
  Refusal verdict unchanged.

(Fifteen entries, CC-1–CC-15.)

### Row rulings (all 55 + SUPERSEDE)

| # | Row | Rule | Reason |
|---|---|---|---|
| 1 | `mutations-leaf-manifest` | endorse | byte-clean file re-read; 4-name mirror verified |
| 2 | `mutations-module-map-prose` | endorse | docstring map verified; forms-twin note matches tree |
| 3 | `mutation-operation-descriptors` | endorse | 4 decls + registry + 3 preds + 5 derivations + reject verified |
| 4 | `mutation-construction-target-guard` | endorse | trio + `_ABSENT` verified; FF-2 settles mechanism |
| 5 | `write-field-lazy-forward-ref` | endorse | 3 auth call sites verified |
| 6 | `lazy-root-field-signature` | correct | owner + 1 auth site verified; see CC-13 for the parenthetical |
| 7 | `mutation-signature-synthesis` | endorse | FAM-1 site-B note consistent |
| 8 | `mutation-field-factory-body` | correct | dispatch + stamp + directives verified; see CC-12 |
| 9 | `mutation-class-marker` | endorse | 1 stamp + 2 readers verified |
| 10 | `column-less-relation-typing` | endorse | trio + both-flavor callers verified |
| 11 | `model-column-write-classification` | correct | classifier verified; see CC-10 (4 outcomes, not 5-way) |
| 12 | `model-column-write-annotation` | endorse | triple + wrappers + cross-flavor callers verified |
| 13 | `mutation-input-attr-normalizer` | endorse | 2 callers verified |
| 14 | `mutation-editable-basis` | endorse | basis + carrier pair + sets/auth callers verified |
| 15 | `mutation-create-requiredness` | correct | predicate verified; see CC-11 (no kind table / form arm) |
| 16 | `mutation-input-surface-audit` | endorse | single call from materialize verified |
| 17 | `mutation-input-namespace-lifecycle` | correct | lifecycle + 0 alias importers verified; see CC-14 (owner cite) |
| 18 | `mutation-input-generator` | endorse | FAM-3 composer noted; assembly verified by full read |
| 19 | `mutation-collision-policy` | endorse | 2 guards + record + FAM-3 composer verified |
| 20 | `mutation-non-field-key` | endorse | pin + 2 reader files verified |
| 21 | `mutation-excluded-kind` | endorse | tag + 3 handler sites mappable (bind/decode/tuple-check) |
| 22 | `mutation-kind-tokens` | endorse | CREATE/PARTIAL + cross-file importers verified |
| 23 | `mutation-payload-slot-rule` | endorse | 6 call sites verified |
| 24 | `generator-kind-display-word` | endorse | landed 2→1; gates re-proved at my address |
| 25 | `mutation-payload-name` | endorse | FAM-1 count + block verified; open/blocked shape per precedent |
| 26 | `static-read-callability` | endorse | FAM-2 count + block verified; open/blocked shape per precedent |
| 27 | `write-auth-result-contract` | endorse | 3 seams verified |
| 28 | `permission-class-walk` | endorse | 2 seam callers verified |
| 29 | `model-permission-default-check` | correct | action-map read verified; see CC-9 (no staff/superuser arms) |
| 30 | `model-less-deny-default` | endorse | 2 wirings verified |
| 31 | `model-relation-decode-coloring` | endorse | decoders + 3-caller edge verified; nested EXCLUDED arm homes here |
| 32 | `mutation-exclude-carve-out` | correct | see CC-4 (owner is the R2 trio, not the EXCLUDED capture) |
| 33 | `model-decode-write-steps` | endorse | strict unpack + register repack verified |
| 34 | `mutation-delete-rider` | endorse | members verified by full read |
| 35 | `mutation-authorization-seam` | correct | see CC-5 (phantom dropped; auth files cell stands) |
| 36 | `mutation-validation-save-mappers` | endorse | 3 mappers + forms use verified |
| 37 | `mutation-locate-lookup` | endorse | members + verdict pair verified |
| 38 | `mutation-error-refetch-payload-tail` | endorse | builder + stash + refetch + single rollback verified |
| 39 | `sealed-mutation-meta-slot` | endorse | seal pair + readers incl. `schema.py:193` verified |
| 40 | `sealed-mutation-meta-head` | endorse | 2 factory products verified; FF-8 noted |
| 41 | `write-meta-shape-vocabulary` | endorse | keys + guard + normalizer + cross-flavor use verified |
| 42 | `non-delete-operation-gate` | endorse | ModelForm + serializer callers verified |
| 43 | `backing-resolution-type-gate-kit` | endorse | leaf + 5 gates; 16 call sites exact |
| 44 | `construction-hook-shape` | endorse | both helpers + forms composition verified |
| 45 | `shape-build-cache-discipline` | endorse | helpers + cache + clear verified; rf rides tail only (recorded) |
| 46 | `declaration-registry-mechanics` | endorse | 3 products verified |
| 47 | `snapshot-record-shape` | correct | see CC-6 (owner is `__slots__` + `__init__`) |
| 48 | `permission-lock-validation` | endorse | 3 helpers verified; FAM-2 site-B note consistent |
| 49 | `resolver-seam-factory` | endorse | factory + 2 builders + 4 declarations verified |
| 50 | `model-flavor-base` | endorse | matrix + seams + slots verified by full read |
| 51 | `custom-input-naming-gate` | endorse | validator + expected-names verified |
| 52 | `primary-type-error-shapes` | endorse | resolution + both error shapes verified by full read |
| 53 | `input-materialize-pair` | endorse | generated vs merged verified |
| 54 | `override-shape-lock` | endorse | lock + 2 shape helpers verified |
| 55 | `bind-drain-trio` | endorse | drain + 2 riders + finalizer call verified |

46 endorse, 9 correct (rows 6/8/11/15/17/29/32/35/47), 0 reject. Every member
ID cited in a row's homing note exists in its member artifact (all inputs
N/FL, fields F1/F2, perms F3/F4/F6, resolvers R1–R8, sets FL1/FL3–FL16, init
F1/F2 verified present; operations cite corrected F4→F1 per CC-8).

SUPERSEDE claim — ENDORSED. Verified zero Responsibility-index rows held by
any `File mutations/*` item (only the seven plan checkbox rows reference the
member artifacts, plus the run-13 dispatch brief) and zero `mutation-*` /
`static-read-callability` family rows that the folder rows could duplicate —
so the member N/F/R/FL records were never transcribed, the 55 folder rows
supersede them at current bytes, and no separate member transcription is
owed. Worker-0 transcribes the 55 rows with CC-4/CC-5/CC-6/CC-9/CC-10/CC-11/
CC-12/CC-13/CC-14 applied, plus correction C-1 (verified: calls WT `:640`/
`:676`, defs `:611`/`:653`).

### Pending execution, cells, gates, verdict

Pending execution — COMPLETE and correctly typed: zero `proof:` (FAM-3's
failability executed, both entries pinned — re-proved by me below) and five
`gate:` witnesses (4 package-file regression witnesses + 1 live
write-surface witness). No finding is execution-deferred; nothing else the
gate must run is missing.

Cells / inapplicability — JUDGED SOUND on the merits. FAM-3's proofs run
zero database statements: the helper is a pure str→str mapping, and the
three new tests execute only `_meta` reads, AST parsing, and the two
configuration-error raises (the spy's `build_mutation_input(fields=())`
raises before any query; the collision call passes explicit names). The
claim is correctly scoped to "FAM-3's own proofs", not the whole gate
files. Sharded/pg cells stay unverified for lack of maintainer word —
correctly recorded, not claimed.

Gate re-runs (all my own, `pressure` GREEN, everything via `heavy`):
ruff `format --check` + `ruff check` on both touched paths — pass
("2 files already formatted", "All checks passed!"); focused
`pytest -n0 tests/mutations/test_inputs.py --no-cov -q` in the shared tree
(my one authorized run) — 83 passed; failability `prove` at
`dry/folder-mutations/verify-1` (fresh copy, blob_before `a9428e11` =
shared post-edit) — exit 0, entry 1 pinned (3/3 declared), entry 2 pinned
(2/2 declared), restores byte-identical (record
`.../verify-1/dry-20261010T035100-1c2a37.json`); `basedpyright`,
`basedpyright -p pyrightconfig.floor.json`, and
`check_truthful_reads.py --check` in my copy — 0/0/0, 0/0/0, errors 0.
The consolidation type-checks with no new cast, `Any`, suppression, or
public symbol; helper + tests carry docstrings; no overrides exist.

Diff hygiene (re-verified independently): NEW helper sits between
HEAD==BASE-identical context lines; both composer swaps rewrite
HEAD==BASE-identical `kind = ...` lines with only unchanged-context
adjacency to preserved hunt f-string hunks (changed hunt lines
byte-identical); test additions are pure (+130/-0) at end-of-file, far
from the BASE-vs-HEAD concurrent test hunks (`:100`, `:985`). The item
diff is exactly the 2 claimed files, zero new files. AGENTS.md prose:
zero process provenance in code/docstrings/tests, same-module short cites
only (convention-conformant), tests at the mandated (strongest reachable)
tier, mandated Status/Run header block present (extra Pins/Index-rows
sections acceptable per the run-13 filters precedent). Banned-word sweep
of added test lines: clean (own substring grep).

Defects — none found in code. The fifteen CC entries above are record
slips in Worker-1's prose/rows, each with its exact fix; none touches a
count, owner, gate, or shipped byte, so no `## Defects` entry is owed and
no Worker-1 rework exists to request.

VERDICT: `verified`. FAM-3 landed correctly (2→1, owner + shape + tier +
equivalence + failability all confirmed by independent re-derivation and
re-execution); FAM-1/FAM-2 correctly CONFIRMED count-2 and correctly
blocked on exact hunt hunks with sound specified migrations; 16 FC / 12 FR
/ 20 converge / 8 FF all concur with evidence re-derived; 55 rows ruled
(46 endorse, 9 correct, 0 reject) with SUPERSEDE endorsed; pending list is
`gate:`-only. Worker-0: transcribe rows with the CC fixes, record ledger
figures +15/-2 and +130/-0 (CC-1), home FF-1–FF-8 + C-1 at closeout.

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
