# DRY review: `mutation-error-envelope`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `mutation-error-envelope`. Provisional owner
`mutations/inputs.py::FieldError` with code vocabulary at
`utils/errors.py` — CONFIRMED, not inherited. Known member files:
`mutations/inputs.py`, `utils/errors.py`,
`mutations/resolvers.py`, `auth/mutations.py`; the trace below adds
the flavor decoders and shared write primitives as absence-proved
members (`forms/resolvers.py`, `rest_framework/resolvers.py`,
`utils/write_values.py`, `utils/write_transaction.py`,
`mutations/sets.py`, `forms/sets.py`, `rest_framework/sets.py`).
Prior records only as triggers: the mutations-file items (a shared
`FieldError` envelope + code vocabulary was noted — re-derived from
source, nothing inherited). Never read any `worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds no row on
any envelope core path (full read: rows cover only
`optimizer/walker.py`, two fakeshop live files,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`, `registry.py`, `relay.py`,
`list_field.py`, `types/relay.py`, `types/finalizer.py`,
`types/resolvers.py`, `utils/relations.py`, `types/base.py`,
`inspect_django_type.py` + its test). `mutations/inputs.py` +
`utils/errors.py` are clean vs HEAD (confirmed). `mutations/resolvers.py`
+ `auth/mutations.py` carry EXTERNAL concurrent dirt, verified vs
`git show HEAD:`: the `_safe_class_name` / `_safe_arg_repr`
hostile-name hunk only (one import line each; five message sites in
resolvers, four in auth), with zero overlap against any envelope site
(`FieldError`, `build_payload`, `error_payload_builder`,
`run_write_pipeline_sync`, `field_error` call sites,
`_failed_login_payload`, `_register_write_step`,
`bind_auth_mutations`). `git diff 8c916988a892728d0c3c515d184c302f1afbbd4a
-- <the four paths>` is empty, so the dirt predates this item's
dispatch; no dirty path was edited, so no STOP arose — reading the
dirty files was free.

## System trace

Rule: every mutation flavor returns one shared
`errors: [FieldError!]!` envelope ([GOAL.md][goal] success criterion
6), with a structured code vocabulary no flavor re-spells.

The envelope is already one type, one payload builder, one leaf
constructor, one assembly, one code table:

- **Type.** [inputs][inputs]`::FieldError` (`field`, `messages`,
  additive `codes`, additive `path`) is the single `@strawberry.type`
  every payload references. Def census: exactly 1 `class FieldError`
  in the package; re-exported (not re-declared) at
  `mutations/__init__.py`.
- **Payload shape.** [inputs][inputs]`::build_payload_type` builds
  BOTH payload shapes from one body: model-backed
  (`<slot>: object_type | None` + `errors`) and model-less
  (`ok: bool` + `errors`). Def census: exactly 1
  `def build_payload_type`; the two `errors:
  strawberry.field(default_factory=list)` declarations are its two
  branches, not two definitions. Every materialization rides it:
  `mutations/sets.py::bind_mutation_outputs` (model, `ModelForm`,
  serializer — the serializer rides the same `bind_mutations()`
  drain as a `DjangoMutation` subclass; the model-less form rides
  `bind_form_mutations()` through the same
  `bind_write_declarations` spine) and `auth/mutations.py`
  `bind_auth_mutations` (login + logout holders).
- **Leaf.** [errors][errors]`::field_error` is the single leaf
  constructor. Construction census: exactly 1 `FieldError(` call in
  package source (inside `field_error` itself). Every other leaf is
  a named adapter composing it by name: `null_field_error`,
  `relation_field_error`, `empty_validation_error`,
  `validation_error_to_field_errors`, `integrity_error_field_errors`,
  `join_error_path`, plus the resolver-side adapters
  (`not_found_error`, `_invalid_lookup_id_error`,
  `_relation_null_error`, `_explicit_null_error`,
  `write_transaction.py::conflict_error`).
- **Assembly.** [mresolvers][mresolvers]`::run_write_pipeline_sync`
  is the skeleton the model (create/update/delete), `ModelForm`,
  plain form, serializer, and register riders all ride (decode /
  write / tail steps are the only per-flavor seams); its
  `error_payload_builder` closure (rollback-then-envelope) and
  `build_payload` (slotted instantiation) are each defined once.
  Auth login/logout compose `resolvers.build_payload` /
  `payload_cls_for` by name (the documented spec-040 reuse); the
  model-less success leaves (`payload_cls(ok=True, errors=[])` in
  the skeleton, `payload_cls(ok=ok, errors=[])` in
  `_logout_observation`) pass `ok=`/`errors=` kwargs to the shared
  TYPE — composition, not a second shape.
- **Decode spine.** All three flavors' relation decodes ride
  [wvalues][wvalues] (`type_check_relation_id`,
  `decode_visible_relation`, `decode_visible_relation_ids`,
  `unencodable_text_error`, `decode_scalar_leaf`), which compose
  `relation_field_error` / `field_error` by name. No flavor builds
  a relation error by hand.
- **Error mappers.** The flat Django mapper
  (`validation_error_to_field_errors`), the recursive DRF
  flattener
  [sresolvers][sresolvers]`::serializer_errors_to_field_errors`
  (with `_error_leaf` / `_error_node_children` / `_rekey_segment` /
  `_build_reverse_map` / `_error_detail_codes`), and the form
  adapter
  [fresolvers][fresolvers]`::_form_errors_to_field_errors` all
  terminate in the shared `field_error` leaf — the `"__all__"`
  sentinel + message coercion + `path`/`codes` derivation cannot
  drift between the flat and recursive flatteners.
- **Code table.** [errors][errors] owns exactly 7
  `FIELD_ERROR_CODE_*` constants (`INVALID`, `NULL`,
  `CONSTRAINT`, `NOT_FOUND`, `PROTECTED`, `CONFLICT`,
  `TRUNCATED`). Every framework `codes=` call site names a
  constant; the only other `codes=` values are Django/DRF-native
  passthroughs (`codes=codes`, `codes=leaf_codes`) — upstream
  vocabularies correctly NOT mirrored. Zero string-literal
  `codes=` in package source (AST census). The `extensions={"code":
  ...}` vocabulary (`GLOBALID_*`, `FILTER_INVALID`) is a different
  surface (top-level `GraphQLError`, not the in-band envelope) —
  intentional separation (R3).

Lifetime (principle 4): pure construction. No cache, memo, ledger,
or stored derivation anywhere on the envelope path
(`static-reviewed` over all five construction bodies); validity key
N/A — nothing is stored.

Connected sources read: [inputs][inputs] (full),
[errors][errors] (full), [mresolvers][mresolvers] (full),
[authmut][authmut] (factories, register pair, bind),
[fresolvers][fresolvers] (decoders, mappers, pipeline rider),
[sresolvers][sresolvers] (decoders, flattener, save mapping),
[wvalues][wvalues] (spine + atoms), [wtx][wtx]
(`conflict_error` + pipeline context), `mutations/sets.py`
(`bind_mutation_outputs`, `bind_write_declarations`),
`forms/sets.py` (model-less drain), `rest_framework/sets.py`
(`SerializerMutation.build_input` — same `bind_mutations()`
drain), `mutations/__init__.py` (re-export),
[test-errors][test-errors] (oracle bodies), live tiers
(products/auth/library rows below), [GOAL.md][goal]
(success criterion 6). Excluded on strength of body: every other
package module (zero envelope vocabulary over the whole-package
sweep for `FieldError\(|field_error\(|build_payload|_payload_type_name|codes=`).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Model, `ModelForm`, plain
   form, serializer, login, logout, register all return the same
   `FieldError` type through the one builder + one skeleton (site
   table above). No flavor keeps a second envelope body (def and
   construction censuses: 1 each). Flavor deltas are decode
   null/skip/projection adapters with per-decoder contract prose.
   Trigger: a flavor constructing `FieldError(` or declaring an
   `errors` payload field outside `build_payload_type`.
2. **Sync/async twins.** Envelope construction is sync-only pure
   construction (no awaits, no ORM, no `async def` in
   [errors][errors]); every async entry runs the same sync body
   through `run_in_one_sync_boundary`. No twin exists, none owed.
   Trigger: an `async` envelope constructor.
3. **Derived rather than repeated knowledge.** The payload slot
   (`"node"`/`"result"`) derives once at
   `inputs::payload_object_slot`; build site, skeleton, and
   re-fetch compose it by name, never re-derive the Relay check.
   Codes derive from the constant table, never re-typed.
   Trigger: a second slot derivation or a re-typed code literal.
4. **Inverse / round-trip pairs.** Dotted-`field` ⇄ `path`
   segments: split once in `field_error`, join once in
   `join_error_path`; the serializer flattener joins while
   descending and the leaf splits on receipt — one grammar, two
   halves sharing the owner, not two grammars. Root rule
   (`field="__all__"` + `path=[]`) agreed by both flatteners.
   Trigger: a second split/join implementation.
5. **Contracts restated in another medium.** Production (above);
   oracles (independent literals — never reading the owner body);
   projections ([GOAL.md][goal] criterion 6, the three module
   docstrings verified against bodies, spec-036 D7/D8, spec-038
   D6/D8, spec-039 Decision 8, spec-040 D5/D6). Listed, not
   counted.
6. **Enforcement by omission.** All seven mutation surfaces
   enumerated (model create/update/delete, `ModelForm`, plain
   form, serializer, login, logout, register): each returns the
   envelope on every failure arm. `current_user` is a query, not
   a member. The login failure carries no code — the byte-identical
   enumeration-guard contract (spec-040 D5 + live pin), not a gap:
   no contract source extends codes to it. No defect.

### Enumeration

Instrument: whole-package sweeps for `FieldError\(` (2 hits: the
owner body + one `list_field.py` docstring mention of Django's
unrelated `FieldError`), `field_error\(|null_field_error\(|relation_field_error\(|empty_validation_error\(|validation_error_to_field_errors\(|integrity_error_field_errors\(`
(48 hits, each classified), `build_payload\(|error_payload_builder\(|build_payload_type\(|payload_cls_for\(`
(19 hits), `FIELD_ERROR_CODE_\w+` (38 hits),
`payload_cls\(|errors=\[|errors=errors` (payload
instantiations), `codes=` (21 hits), `class FieldError|def
build_payload_type|def field_error|def build_payload|def
error_payload_builder` (5 hits, 1 def each), string-literal
codes (0). Population: 117 `.py` (plan count; no adds/renames).

- Definitions (1 each): `FieldError`, `build_payload_type`,
  `payload_object_slot`, `field_error`, `null_field_error`,
  `relation_field_error`, `empty_validation_error`,
  `validation_error_to_field_errors`, `integrity_error_field_errors`,
  `join_error_path`, `build_payload`, `error_payload_builder`,
  `run_write_pipeline_sync`, `payload_cls_for`,
  `serializer_errors_to_field_errors`, `conflict_error`,
  `not_found_error`.
- Adapters composing by name (listed, not counted): model
  single/list decoders, form single/multi (+ `empty_values`
  skip / `to_field_name` projection), serializer single/multi/
  nested (+ `None` skip / `obj.pk` projection), register
  decode/write pair, login/logout payload helpers, form error
  adapter, save/delete/full-clean mappers.
- Oracles: [test-errors][test-errors] (38 tests: leaf shapes,
  codes, sentinel, hostile-metadata totality, layering pin);
  `tests/mutations/test_resolvers.py` (coerce + envelope rows);
  `tests/utils/test_write_values.py` (spine rows);
  `tests/rest_framework/test_resolvers.py` (flattener rows);
  `tests/auth/test_mutations.py` (auth envelope rows); live
  [live-products][live-products] (explicit-null rows pin
  `{"field", "messages", "codes"}` per flavor),
  [live-auth][live-auth] (login/logout/register envelopes),
  [live-library][live-library] (SDL golden
  `("errors", "[FieldError!]!", None)` + per-flavor `codes`
  rows).

### Challenges

Counts are authoritative definitions only; adapters, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New framework error code (e.g. a rate-limit code) | **1** (one `FIELD_ERROR_CODE_*` constant at [errors][errors]; call sites pass it by name — consumers, listed). Per-flavor tables would force 3+; none exist. |
| C2 | New additive envelope member (the `codes`/`path` precedent) | **1** ([inputs][inputs]`::FieldError`; payload builders reference the type by name; no per-flavor mirror moves). |
| C3 | Fourth flavor needing its own envelope/payload work | **0** new envelope definitions (composes `field_error` + skeleton + `build_payload_type` by name). Worked precedent: the register rider added only a decode/write STEP PAIR and reused skeleton, payload, and leaf unchanged. A genuinely new payload SHAPE adds **1** branch to `build_payload_type`. |

**Experiments (executed, disposable workspace).** Copy per
[DRY.md][dry] "Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/mutation-error-envelope
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python envelope_gate.py django_strawberry_framework
uv run --directory "$WS" python -m pytest tests/utils/test_errors.py -n0 --no-cov -q -p no:cacheprovider
uv run --directory "$WS" python -m pytest examples/fakeshop/test_query/test_products_api.py::test_update_item_explicit_null_scalar_name_is_field_error -n0 --no-cov -q -p no:cacheprovider
```

Copy `__file__`:
`.../dry-ws/mutation-error-envelope/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/mutation-error-envelope/examples/fakeshop/db.sqlite3`
(the copy's own tree and database; the shared tree's database
is untouched — `git status` shows no db modification).

Candidate structural gate (`envelope_gate.py`, scratch-only):
G1 exactly one `FieldError(` site; G2 one def each of the five
owner symbols; G3 zero string-literal `codes=`. On the clean copy:
GATE GREEN (117 files walked). Negative control (same copy):
a behavior-preserving hand copy of the owner's body
(`_hand_copied_null_error` in `mutations/resolvers.py`,
constructing `FieldError` directly, serving
`_explicit_null_error`) → GATE RED (`G1: expected 1
FieldError\( site, found 2`), while 38/38
[test-errors][test-errors] behavior oracles PASS and the live
explicit-null wire oracle
(`test_update_item_explicit_null_scalar_name_is_field_error`,
the rerouted path) PASSES. Every behavior oracle passes the
control; only the structural gate sees the bypass — the proved
shape a landed gate must take. No source mutation in the shared
tree; the WS copy carries the control (disposable).

One authorized shared-tree focused run (zero member edits in
flight): `tests/utils/test_errors.py::test_null_field_error_and_empty_validation_error_leaf_shapes`
`--no-cov -n0` → 1 passed.

## Findings

### F1 — envelope type + payload builder + assembly (CONFIRMED single-owned)

- **Contract + variation.** One `errors: [FieldError!]!`
  envelope across model/form/serializer/auth. Varies on: payload
  shape (model-backed slot vs model-less `ok`); leaf condition
  (null, relation, not-found, invalid-id, protected, conflict,
  constraint, validation, login-failure); code source
  (framework constant vs Django/DRF passthrough).
- **Sites + roles.** Definitions: [inputs][inputs]`::FieldError`
  + `::build_payload_type`; [errors][errors]`::field_error` +
  code table; [mresolvers][mresolvers]`::run_write_pipeline_sync`
  + `::error_payload_builder` + `::build_payload` +
  `::payload_cls_for`. Adapters/consumers/oracles/projections:
  as listed in System trace.
- **Challenges.** C1 → 1; C2 → 1; C3 → 0 (+1 per new payload
  shape). Count > 1 nowhere in one rule.
- **Owner + lifetime (principles 7, 4).**
  [inputs][inputs]`::FieldError` stands for the type (the public
  GraphQL symbol; every flavor and the schema already depend on
  it); [errors][errors] stands for leaf construction + the code
  table (flavor-neutral: all flavors including model-less ones
  depend on `utils` without importing the mutations package at
  module time — the function-local import is the established
  seam, and dependency direction wins over co-location).
  Lifetime: pure construction, nothing stored.
- **Migration.** None — already single. Zero tracked edits.
- **Distinct behavior (stays separate).** Model M2M
  null-reject vs form `empty_values` / serializer `None`
  pass-through (per-flavor validation contracts, each recorded
  at its decoder); codeless failed-login envelope
  (byte-compatibility contract); register `password` keyed
  directly (validate_password yields no `error_dict`);
  recursive serializer flattener vs flat Django mapper (nested
  vs flat contracts).
- **Behavioral proof.** `execution-verified` (WS: gate GREEN
  clean, gate RED + 38/38 + live wire oracle green on the
  control; shared-tree focused run green, zero member edits in
  flight). `static-reviewed` (def/construction censuses, oracle
  independence, docstring prose).
- **Structural gate.** Design proved in-workspace (above);
  landing DEFERRED with reason: single-ownership is confirmed
  with zero present divergence, the wire shape is already
  pinned per flavor by live oracles (SDL golden + per-flavor
  rows), and the two most-adjacent files carry unsettled
  concurrent dirt — a package-wide AST gate lands cleanest
  after settle, at Worker 0's closeout call. Owed shape: G1–G3
  as proved (`envelope_gate.py` logic, population = package
  source, bypass = hand-rolled `FieldError(` construction, the
  exact bypass the promotion history shows flavors attempt).
- **Coupling.** None.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `mutations/inputs.py` `fc442047…`,
  `utils/errors.py` `3e25e93b…`,
  `mutations/resolvers.py` `a322d17a…` (external hostile-name
  hunk; cited envelope lines verified outside it),
  `auth/mutations.py` `200805d2…` (same),
  `forms/resolvers.py` `4edb984b…`,
  `rest_framework/resolvers.py` `8024703e…`,
  `utils/write_values.py` `d28587c7…`,
  `utils/write_transaction.py` `eca9ad4d…`,
  `mutations/sets.py` `936f5ae7…`, `forms/sets.py`
  `98ef150d…`, `rest_framework/sets.py` `2c7117d6…`,
  `tests/utils/test_errors.py` `83662dee…`. `HEAD`
  `bfaee91d`; `ITEM_BASELINE`
  `8c916988a892728d0c3c515d184c302f1afbbd4a` (all four
  known-member paths identical to it). Searched population:
  whole package (117 `.py`) for the rule tokens. Any
  fingerprint change reopens the finding.
- **Reconsideration triggers (recorded here + plan
  Outcomes via Worker 0).** T-construct fires if a second
  `FieldError(` site appears; T-shape fires if an `errors`
  payload field is declared outside `build_payload_type`;
  T-code fires on a string-literal `codes=` or a second code
  table. No owner-docstring clause added (zero-edit
  confirmation; triggers live in this finding).

### R1 — per-condition leaf wrappers (REJECTED consolidation)

Named ctors (`null_field_error`, `relation_field_error`,
`not_found_error`, `_invalid_lookup_id_error`,
`_relation_null_error`, `conflict_error`,
`empty_validation_error`, the two mappers, the DRF flattener)
stay: each pairs one condition with its message + code + path,
with distinct reasons to change (a null-wording change must not
move the conflict leaf). Shared form considered: one
parametrized ctor — already exists (`field_error`); the
remainder (which condition maps where) stays at call sites by
principle 7. Trigger: two wrappers collapsing to one
condition. Home: [errors][errors] + this finding.

### R2 — model-less `ok` payload inline constructions (REJECTED)

Three `payload_cls(ok=…, errors=…)` sites (skeleton success,
error-builder failure, logout observation) stay inline: generic
success vs pre-teardown observation have separate reasons to
change, and all three compose the shared TYPE by name. Shared
form considered: `build_model_less_payload(payload_cls, ok)` —
owns 2 lines, remainder stays; coupling auth observation to the
generic skeleton makes things worse (principle 3/11).
Trigger: a third model-less success site. Home: the three call
sites + this finding.

### R3 — envelope codes vs `GraphQLError` extension codes (REJECTED)

In-band `FieldError.codes` (validation envelope, per-field)
vs top-level `extensions.code` (request rejections) answer
different clients at different layers; unifying them would
couple the write envelope to every transport rejection.
Trigger: a client contract reading both as one vocabulary.
Home: [errors][errors] module docstring (already states the
split) + this finding.

## Defects

None found while tracing. The two closest candidates were
examined and cleared (not defects): the codeless failed-login
leaf is the byte-compatibility contract pinned by the live
enumeration-guard test (spec-040 D5 establishes it); the three
inline model-less constructions compose the shared payload
type by name and fail loud (not silent) on a shape change.

## Pending execution

None. All behavioral proofs `execution-verified` in the
disposable workspace; the one authorized shared-tree focused
run executed green (1 passed) with zero member edits in
flight. The proved-but-unlanded gate design carries no
`proof:` entry (its proof already ran); landing it is Worker
0's closeout call, not a pending command. `FAKESHOP_SHARDED=1`
and Postgres cells `inapplicable by construction`: every
executed claim is string/dict/enum construction plus
single-alias default-DB reads (the recorded `NAME` is the
copy's own file); the traced construction path reaches no
alias or dialect decision.

## Judgment

The shared mutation error envelope is already single-owned:
one `FieldError` type, one payload builder, one leaf
constructor, one assembly skeleton, one code table — model,
form, serializer, and auth compose all five by name, with
per-flavor adapters only for decode null/skip/projection and
per-condition message/code pairs. No consolidation exists to
perform; the three rejections carry contract differences +
triggers. Gate design proved in-workspace with a passing
negative control; landing deferred with reason. Zero tracked
edits; item-scoped diff is the new artifact only
(`git status --short` shows `?? docs/dry/dry-rule-mutation-error-envelope.md`
and no modification under `django_strawberry_framework/` or
`tests/` from this item).

Scratch paths (removal is Worker 0's, after `verified`, by
explicit path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/mutation-error-envelope`
(includes its own `.venv`; the `mutations/resolvers.py` in the
copy carries the `_hand_copied_null_error` negative control —
shared-tree file untouched) + gate script
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/envelope_gate.py`.

Worker 0 rows: tick Family `mutation-error-envelope` (this
artifact, `ready-for-verification/1`, zero edits, no pending
execution); no `## Responsibility index` change (provisional
owner + all four member files already covered); no
`## Owned changes` row (nothing landed); no defects to home.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[authmut]: ../../django_strawberry_framework/auth/mutations.py
[errors]: ../../django_strawberry_framework/utils/errors.py
[fresolvers]: ../../django_strawberry_framework/forms/resolvers.py
[inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mresolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[sresolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[wtx]: ../../django_strawberry_framework/utils/write_transaction.py
[wvalues]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-errors]: ../../tests/utils/test_errors.py

<!-- examples/ -->
[live-auth]: ../../examples/fakeshop/test_query/test_auth_api.py
[live-library]: ../../examples/fakeshop/test_query/test_library_api.py
[live-products]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Worker 2 independent trace — recorded BEFORE reading `## Findings`
(item `mutation-error-envelope`, Run `0.0.15 2026-09-19-1`).
Sources: package source only (`mutations/inputs.py`, `utils/errors.py`,
`mutations/resolvers.py`, `auth/mutations.py`, `forms/resolvers.py`,
`rest_framework/resolvers.py`, `rest_framework/sets.py`, `mutations/sets.py`,
`utils/write_values.py`, `utils/write_transaction.py`); item-scoped diff
checked separately. No artifact `## Findings` read before this section.

### Envelope shape (as found)

- `mutations/inputs.py::FieldError` — the ONE `@strawberry.type` with
  `field: str`, `messages: list[str]`, `codes: list[str] = []`,
  `path: list[str] = []`. Docstring states additive-only, shared by
  model/form/serializer/auth flavors. No second `class FieldError` in package
  (`FieldError(` hits: sole construction at `utils/errors.py::field_error`
  `return FieldError(...)`; other hit is prose in `list_field.py` docstring).
- `mutations/inputs.py::build_payload_type(mutation_name, *, object_type,
  object_slot)` — the ONE payload-type builder, both branches in one def:
  `object_type is None` -> `{ok: bool, errors: list[FieldError]}` (model-less);
  else `{<slot>: object_type | None, errors: list[FieldError]}` with
  `slot` defaulting via `payload_object_slot` and reserved-attr guard
  (`ok`/`errors`). Single `type(f"{mutation_name}Payload", ...)` +
  `strawberry.type(cls)` tail.
- `utils/errors.py::field_error(path, messages, *, codes=None)` — the SOLE
  leaf constructor; normalizes empty path to `NON_FIELD_ERROR_KEY`
  (`"__all__"`, imported function-locally from `mutations/inputs.py`),
  splits dotted path to `path` segments (root `__all__` -> `[]`, nested keeps
  segments), coerces messages/codes via `_str_list`. Sole `FieldError(`
  construction site in package source.
- Code vocabulary `utils/errors.py::FIELD_ERROR_CODE_*` — exactly 7 constants:
  `INVALID="invalid"`, `NULL="null"`, `CONSTRAINT="constraint"`,
  `NOT_FOUND="not_found"`, `PROTECTED="protected"`, `CONFLICT="conflict"`,
  `TRUNCATED="truncated"`. Docstring states open vocabulary (not Enum, not
  validated) so Django/DRF codes flow through same `codes=` param.
- Assembly: `mutations/resolvers.py::build_payload(payload_cls, slot, obj,
  errors)` (`payload_cls(**{slot: obj, "errors": errors})`) — single success/
  error instantiation for slotted payloads;
  `mutations/resolvers.py::error_payload_builder(payload_cls, slot, using)`
  — single rollback-then-envelope closure (`set_rollback` + `slot is None ?
  payload_cls(ok=False, errors=...) : build_payload(...)`); skeleton
  `mutations/resolvers.py::run_write_pipeline_sync` — single
  locate->authorize->decode->write->tail orchestration all write flavors ride;
  `mutations/resolvers.py::payload_cls_for` — single `getattr(inputs,
  _payload_type_name)` lookup; bind drain `mutations/sets.py::
  bind_mutation_outputs` + `bind_write_declarations` — single
  `build_payload_type` call site + `materialize_mutation_input_class` ledger.

### Construction census per flavor (does any flavor build its own type/list?)

- Model (`DjangoMutation` create/update/delete):
  rides `run_write_pipeline_sync` (`_run_pipeline_sync` / `_run_delete`).
  No own payload-type def, no own `FieldError(`. Error lists are
  `[decode_error]` / `[write_error]` / `[id_error]` / `[not_found]` short-circuits
  mapped by skeleton/`_error_payload` to envelope. Leaves via shared helpers:
  `validation_error_to_field_errors`, `integrity_error_field_errors` (via
  `save_or_field_errors` / `forced_save_or_field_errors`), `relation_field_error`
  (via `decode_visible_relation_ids` / `type_check_relation_id`),
  `null_field_error`/`field_error(... NULL)` (M2M null, scalar null),
  `not_found_error`/`_invalid_lookup_id_error`/`conflict_error`/`protected`
  leaves — all terminate in `field_error`. Success via `build_payload`.
- Form (`ModelForm` + plain `DjangoFormMutation`):
  rides SAME skeleton via `forms/resolvers.py::_run_form_pipeline_sync` ->
  `run_write_pipeline_sync` (decode `_modelform_decode_step` via
  `decode_provided_fields` + `_decode_form_relation_single/multi` calling
  `decode_visible_relation`; write `_modelform_write_step` /
  `_plain_form_write_step` via `save_or_field_errors`). No own payload-type
  def, no own `FieldError(`. Form validation maps via
  `_form_errors_to_field_errors` -> `validation_error_to_field_errors`
  (`ValidationError(form.errors.as_data())`). Model-less plain tail is skeleton
  `payload_cls(ok=True, errors=[])` (slot None), not a flavor-owned builder.
- Serializer (`SerializerMutation(DjangoMutation)`):
  rides SAME skeleton via
  `rest_framework/resolvers.py::_run_serializer_pipeline_sync` ->
  `run_write_pipeline_sync`, and SAME bind drain
  (`bind_mutations` via `bind_write_declarations`; `sets.py` comment names
  ModelForm+serializer as riders). No own payload-type def, no own
  `FieldError(`. Flattener `serializer_errors_to_field_errors` is recursive but
  terminates in shared leaf `_error_leaf` -> `field_error` (codes =
  `leaf_codes` passthrough of DRF `ErrorDetail.code`); save maps
  `serializer_errors_to_field_errors(exc.detail)` /
  `validation_error_to_field_errors(exc)` / `integrity_error_field_errors()`.
- Auth login (`login_mutation` holders):
  does NOT ride `run_write_pipeline_sync` (own transport prologue +
  `_login_authenticate` + `_login_resolve_body[_async]`), but composes envelope
  BY NAME: payload class via `build_payload_type("Login", object_type=primary)`
  (auth bind), lookup via `resolvers.payload_cls_for`, success/failure via
  `resolvers.build_payload`, failure leaf via `resolvers.field_error("",
  _INCORRECT_CREDENTIALS_MESSAGE)` with NO `codes` arg (codeless). No own
  payload-type def, no own `FieldError(`. Single `_failed_login_payload` +
  `_login_result_payload` pair shared by sync+async bodies.
- Auth logout (`logout_mutation` holders):
  model-less `build_payload_type("Logout", object_type=None)` + inline
  `payload_cls(ok=ok, errors=[])` in `_logout_observation` (ok = authenticated
  actor present, errors always `[]`). No `field_error`, no error list
  construction — logout never emits a `FieldError` (failures are raised, not
  enveloped). Inline `ok` is the model-less spelling (no slot -> cannot call
  `build_payload(slot, ...)`), same as skeleton `slot is None` tails; not a
  second builder.
- Auth register (`Register` rider, `DjangoMutation` subclass):
  rides SAME skeleton via `_run_register_pipeline_sync` ->
  `run_write_pipeline_sync` with password-aware decode/write pair only
  (structural fourth STEP PAIR, not fourth plumbing kit). Leaves via shared
  `null_field_error("password")`, `field_error("password", ..., INVALID)`,
  `unencodable_text_error`, `resolvers.field_error("password", exc.messages,
  codes=codes)` (Django `validate_password` codes passthrough). Payload via
  standard `bind_mutations` (`RegisterPayload`). No own type/leaf defs.

Flatteners: flat Django mapper (`validation_error_to_field_errors`) and
recursive DRF flattener (`serializer_errors_to_field_errors` via `_error_leaf`)
both terminate in the SAME `field_error` leaf (sentinel + coercion + path/codes
derivation single-sited). Form reuses the flat mapper directly.

`codes=` census (package source, 21 hits): every framework site names a
`FIELD_ERROR_CODE_*` constant; remaining values are passthroughs
(`codes=codes`, `codes=leaf_codes`, `codes=_str_list(codes)` inside leaf) —
Django `ValidationError.code` / DRF `ErrorDetail.code` flow unmirrored by
design. Zero string-literal `codes="..."` / `codes='...'` in package source.

### Definition counts (change challenge, independent)

- C1 (new framework error code, e.g. rate-limit): 1 — add one
  `FIELD_ERROR_CODE_*` constant at `utils/errors.py`; call sites pass by name.
  No per-flavor code tables exist.
- C2 (new envelope member, e.g. add a field to `FieldError`): 1 — edit
  `mutations/inputs.py::FieldError` (+ leaf defaults in `field_error` if
  populated). No per-flavor mirror types to update.
- C3 (fourth write flavor / fourth decode-write step pair): 0 new envelope
  definitions — new flavor declares decode/write steps and rides
  `run_write_pipeline_sync` + `field_error` + `build_payload_type` by name
  (register is the proof: step pair only, no new plumbing).

Counts: `class FieldError` 1; `def build_payload_type` 1 (both branches);
`def field_error` 1 + sole `FieldError(` call 1; `def build_payload` 1 +
`def error_payload_builder` 1 + skeleton `def run_write_pipeline_sync` 1;
`FIELD_ERROR_CODE_*` constants 7 in one table; `codes=` string literals 0.

### Owner I would choose

Split, as found: type `FieldError` (+ `build_payload_type`,
`NON_FIELD_ERROR_KEY`) at `mutations/inputs.py` (strawberry-typed, schema/bind
surface; every flavor already depends toward mutations); leaf `field_error`
(+ wrappers `relation_field_error`/`null_field_error`/
`validation_error_to_field_errors`/`integrity_error_field_errors`/
`join_error_path`) + `FIELD_ERROR_CODE_*` table at `utils/errors.py`
(flavor-neutral; model/form/serializer/auth can all import downward without
`utils -> mutations` import cycle at module load — function-local import is the
established seam). Dependency direction wins over co-location (DRY principle 7):
moving the leaf into `mutations/inputs.py` would force `forms`/`rest_framework`
/`auth` to import a sibling flavor for machinery; moving the type into
`utils/errors.py` would push strawberry schema typing below its consumer.
Narrowest valid owner per piece, not one file for both.

### Freshness (Worker 2 hashes, worktree at `bfaee91d`)

- `mutations/inputs.py` `fc442047...` == `HEAD` (clean).
- `utils/errors.py` `3e25e93b...` == `HEAD` (clean).
- `mutations/resolvers.py` worktree `a322d17a...` vs `HEAD 3fd1e571...`
  (dirty, concurrent — read only, never edited).
- `auth/mutations.py` worktree `200805d2...` vs `HEAD dbe64995...`
  (dirty, concurrent — read only, never edited).
- Item-scoped diff (`git diff 8c916988... -- <4 family paths>`): EMPTY —
  confirms Worker 0 ground truth; the two dirty files were already dirty at
  `ITEM_BASELINE` (baseline blobs equal worktree blobs).


## Independent verification reconciliation (Worker 2) — verdict `revision-needed`

Reconciliation against `## Findings` (read AFTER the trace above).
Per-point agree-or-differ; gate-deferral challenged per role brief.

### Census vs W1 (per-flavor construction) — AGREE

Worker 2 re-derived every construction site from package source; counts match
W1 exactly. No flavor builds its own payload type or error list:

- Model create/update/delete rides `mutations/resolvers.py::
  run_write_pipeline_sync` (`_run_pipeline_sync` / `_run_delete`); error lists
  are short-circuit `[decode_error]` / `[write_error]` / `[id_error]` mapped by
  `_error_payload`; leaves via `validation_error_to_field_errors`,
  `integrity_error_field_errors` (`save_or_field_errors` /
  `forced_save_or_field_errors`), `relation_field_error`,
  `null_field_error`, `not_found_error`, `_invalid_lookup_id_error`,
  `protected`, `conflict_error` — all terminate in `field_error`. Success via
  `build_payload`. No own `FieldError(`. AGREE.
- Form (`ModelForm` + plain) rides SAME skeleton via
  `forms/resolvers.py::_run_form_pipeline_sync`; decode via
  `decode_provided_fields` + visibility-checked relation decoders; validation
  via `_form_errors_to_field_errors` -> `validation_error_to_field_errors`;
  save via `save_or_field_errors`. Model-less plain tail is skeleton
  `payload_cls(ok=True, errors=[])`, not a flavor builder. No own type/leaf.
  AGREE.
- Serializer (`SerializerMutation(DjangoMutation)`) rides SAME skeleton via
  `_run_serializer_pipeline_sync` and SAME bind drain (`bind_mutations` via
  `bind_write_declarations`); flattener `serializer_errors_to_field_errors`
  terminates in `_error_leaf` -> `field_error` (`codes=leaf_codes`
  passthrough). Save maps all three DRF/Django/Integrity arms to shared
  leaves. No own type/leaf. AGREE — "rides same drain" confirmed.
- Login composes BY NAME (`build_payload_type("Login")`,
  `payload_cls_for`, `resolvers.build_payload`,
  `resolvers.field_error("", ...)` codeless); sync+async share
  `_failed_login_payload` + `_login_result_payload`. Does not ride skeleton
  (own transport prologue) but does not duplicate envelope machinery. AGREE.
- Logout is model-less `build_payload_type("Logout", object_type=None)` +
  `payload_cls(ok=ok, errors=[])` with `errors` always `[]`; never emits a
  `FieldError`. Inline `ok` is the no-slot spelling, not a second builder.
  AGREE.
- Register is a `DjangoMutation` subclass riding SAME skeleton with a
  password-aware decode/write STEP PAIR only (`null_field_error`,
  `field_error(INVALID)`, `unencodable_text_error`,
  `resolvers.field_error(codes=codes)` passthrough). AGREE — fourth step pair,
  not fourth plumbing kit.
- Flatteners: flat Django mapper + recursive DRF flattener both terminate in
  shared `field_error`; form reuses flat mapper. AGREE.
- `codes=` 21 hits: framework sites name `FIELD_ERROR_CODE_*`; rest are
  `codes=codes` / `codes=leaf_codes` passthroughs; zero string literals.
  AGREE.
- Counts: 1 `class FieldError`; 1 `def build_payload_type` (both branches are
  one def's branches); 1 `def field_error` + sole `FieldError(` call;
  1 `build_payload` + 1 `error_payload_builder` + 1 skeleton
  `run_write_pipeline_sync` (+ `payload_cls_for` lookup, `bind_*` drain);
  7 `FIELD_ERROR_CODE_*`; 0 literal `codes=`. C1->1, C2->1, C3->0. AGREE.
- Owner split (type at `mutations/inputs.py`, leaf+table at
  `utils/errors.py`, dependency direction wins): AGREE — narrowest valid owner
  per piece; moving either across the seam reverses a dependency.

### R-judgments — AGREE (all three rejections stand)

- R1 (per-condition leaf wrappers stay): AGREE. Each wrapper pairs one
  condition with message+code+path and owns a distinct reason to change;
  the shared parametrized ctor (`field_error`) already exists. Difference +
  trigger recorded (two wrappers collapsing to one condition). No
  consolidation owed.
- R2 (inline model-less `ok` constructions stay inline): AGREE on outcome,
  with reasoning confirmed independently. The three
  `payload_cls(ok=..., errors=...)` sites (skeleton `ok=True` success,
  `error_payload_builder` `ok=False` failure, `_logout_observation`
  `ok=ok` pre-teardown observation) compose the SHARED type by name; none
  re-derives slot logic, none constructs `FieldError`. `build_payload`
  requires a slot, so the no-slot shape cannot call it — inline is the only
  spelling, not a second envelope. A `build_model_less_payload` helper would
  own 2 lines while coupling logout's pre-teardown observation to the generic
  skeleton (principles 3/11). These are NOT second envelope spellings; they
  are the same builder's model-less tail. Trigger (third model-less success
  site) stands.
- R3 (envelope `codes` vs `GraphQLError` `extensions.code` stay separate):
  AGREE. In-band per-field validation vocabulary vs top-level transport
  rejection vocabulary; unifying couples write envelope to every transport
  rejection. Split already stated at `utils/errors.py` module docstring.
  Trigger (client contract reading both as one vocabulary) stands.

### Login-codelessness — AGREE (contract, not gap; opened independently)

Opened as ordered: a login error with NO code while all others carry codes
looks like a gap. It is the byte-compatibility enumeration-guard contract:

- Source: `auth/mutations.py::_failed_login_payload` docstring states "No
  error code, deliberately" + collapse of wrong-password / unknown-user /
  inactive / unstorable to one byte-identical payload.
- Oracles pin it: live `examples/fakeshop/test_query/test_auth_api.py::
  test_wrong_password_and_unknown_username_return_identical_envelope`
  asserts `"codes": []` alongside `field "__all__"` + single message;
  surrogate-username/password rows assert the same `"codes": []` envelope;
  package `tests/auth/test_mutations.py::
  test_async_channels_http_wrong_password_is_failed_login_envelope_session_untouched`
  pins `(field, messages)` shape with no codes. A code added to login would
  redden the live `codes==[]` pins — the contract is fenced. No defect.
  AGREE with W1 clearing.

### Gate-deferral — DIFFER (gate should LAND NOW → `revision-needed`)

W1 proves G1–G3 in WS (green clean / red on hand-copy bypass / 38 behavior
oracles + live wire oracle stay green) but defers landing to closeout for
"single-ownership confirmed + wire already pinned + adjacent files unsettled".
Worker 2 judges each prong; deferral does NOT stand:

- Where would the gate live? `tests/utils/test_errors.py` — owner-adjacent,
  already holds the 38 leaf/sentinel/hostile-metadata oracles, CLEAN in
  worktree (`83662dee...` == `HEAD` == finding fingerprint) and NOT under
  concurrent edit. Correct tier per `AGENTS.md` (AST singularity walk is
  unreachable via a real GraphQL query, so `tests/` not `test_query/`; no
  new example model needed). Must NOT live in `tests/base/test_init.py`
  (dirty `239648ed...` vs `HEAD 4cc12105...`) nor in
  `tests/mutations/test_resolvers.py` / `tests/auth/test_mutations.py`
  (both dirty `M`) — those homes would touch unsettled files; the clean
  home avoids them entirely.
- Is the population justified (not a bespoke-existence-test)? YES. Mechanism:
  package-wide AST walk (117 `.py`, the plan population) asserting G1 exactly
  one `FieldError(` site (inside `field_error`), G2 one def each of the five
  owner symbols (`FieldError`, `build_payload_type`, `field_error`,
  `build_payload`, `error_payload_builder`), G3 zero string-literal `codes=`.
  Plausible bypass: hand-rolled `FieldError(` construction to tweak a message
  — the EXACT bypass the promotion history shows flavors attempt (model
  resolver as utility for form/serializer/auth; DRF empty-leaf hand-build;
  auth reaching through `mutations/resolvers.py`; see `utils/errors.py`
  module docstring) and the EXACT control W1 ran (`_hand_copied_null_error`
  serving `_explicit_null_error`). The control PROVES behavior oracles are
  blind to this bypass (38/38 + live explicit-null wire oracle green while
  gate red) — without the structural gate the divergence ships invisible.
  This is the `DRY.md` principle-9 shape (one canonical form + check proving
  every copy against it under an enumerated population + negative control),
  not a per-helper existence test. Precedent: `logger-single-sourcing`,
  `version-single-sourcing`, `optimizer-execution-frame` all landed gate-only
  cardinality/singularity pins with zero production edits on CONFIRMED-single
  owners — same shape, same justification.
- Does "adjacent files unsettled" hold? The two adjacent files
  (`mutations/resolvers.py` `a322d17a...` vs `HEAD 3fd1e571...`,
  `auth/mutations.py` `200805d2...` vs `HEAD dbe64995...`) carry the
  hostile-name hunk with ZERO overlap against any envelope site (verified vs
  `git show HEAD:`; `ITEM_BASELINE` blobs equal worktree blobs so dirt
  predates dispatch). Landing a TEST-ONLY gate in the clean file touches NO
  dirty path (no production edit, no dirty test edit), reads dirty package
  files only (inspection is unfenced; the edit fence is what matters), and
  the gate's green is stable across the hunk (hunk touches imports/messages,
  not counted defs/constructions/literals). "Lands cleanest after settle" is
  aesthetic, not a `DRY.md` block: dirty does not equal untouchable, and a
  clean-file test addition is explicitly allowed while other paths are dirty.
  The wire-already-pinned prong cuts the other way (see above): live oracles
  passing the bypass is WHY the structural gate is needed, not why it can
  wait.

Owed landing (Worker 1, then SAME Worker 2 re-verifies): add G1–G3 to
`tests/utils/test_errors.py` (clean) as AST singularity pins implementing the
proved `envelope_gate.py` logic (walk `django_strawberry_framework/`,
docstring-stripped AST; G1 count `FieldError(` construction sites excluding
the `list_field.py` Django-prose mention; G2 count defs of the five owner
symbols; G3 assert no `codes=` keyword with a string-constant value),
following the landed `tests/base/test_init.py` cardinality-pin style;
`uv run ruff check --fix .` then `uv run ruff format .`; focused run
`uv run pytest tests/utils/test_errors.py -n0 --no-cov -q -p no:cacheprovider`
plus WS negative-control re-proof per `DRY.md` "Tests" (`prove_failability`
shape). No production edit; no dirty file touched.

### Freshness — RE-HASHED, all match (no reopen)

Worker 2 `git hash-object` (worktree, `HEAD bfaee91d`):
`mutations/inputs.py` `fc442047...`, `utils/errors.py` `3e25e93b...`,
`mutations/resolvers.py` `a322d17a...`, `auth/mutations.py` `200805d2...`,
`forms/resolvers.py` `4edb984b...`, `rest_framework/resolvers.py`
`8024703e...`, `utils/write_values.py` `d28587c7...`,
`utils/write_transaction.py` `eca9ad4d...`, `mutations/sets.py`
`936f5ae7...`, `forms/sets.py` `98ef150d...`,
`rest_framework/sets.py` `2c7117d6...`,
`tests/utils/test_errors.py` `83662dee...` — every prefix matches the
finding's recorded fingerprints (dirty two recorded as dirty with
zero-overlap attribution). `HEAD bfaee91d`; `ITEM_BASELINE`
`8c916988a892728d0c3c515d184c302f1afbbd4a`; item-scoped diff
(`git diff 8c916988... -- <four family paths>`) EMPTY — Worker 0 ground truth
CONFIRMED. Searched population: whole package (117 `.py`) for rule tokens;
excluded modules on strength of body (zero envelope vocabulary). Any
fingerprint change reopens.

### `## Pending execution` — AGREE (empty stands)

All proofs `execution-verified`: WS gate GREEN + WS negative-control RED with
38/38 + live wire oracle green (disposable copy, `$WS` cwd, copy `__file__` +
copy DB `NAME` recorded), plus one authorized shared-tree focused run
(`tests/utils/test_errors.py::
test_null_field_error_and_empty_validation_error_leaf_shapes --no-cov -n0`,
1 passed, zero member edits in flight — the entry-authorized focused shape).
No `proof:` entry owed (nothing deferred); `gate:` witnesses alone would leave
`verified`, and none are listed. `FAKESHOP_SHARDED=1` / Postgres
`inapplicable by construction` ACCEPTED: counted claims are AST construction
sites + pure string/dict/enum leaf assembly plus a single-alias default-DB
wire read; the traced construction path reaches no alias or dialect decision,
and the skeleton pins the same envelope on any alias. No pending command.

### `AGENTS.md` prose on empty diff — AGREE (compliant)

Zero tracked edits claimed; item-scoped diff is the new artifact only
(`?? docs/dry/dry-rule-mutation-error-envelope.md`, no modification under
`django_strawberry_framework/` or `tests/` from this item) — CONFIRMED
(`git status --short` shows artifact untracked; `git diff 8c916988...` empty
on family paths; owners clean vs `HEAD`). Concurrent dirt (resolvers/auth +
listed paths) attributed by content vs `git show HEAD:` as external,
pre-dispatch, left untouched; no revert, no commit (maintainer-only commits).
Citations use `path::Symbol` (no line numbers as authority); artifact carries
the canonical `<!-- LINK DEFINITIONS -->` reference-style block; test-tier
rule respected (structural AST gate belongs in `tests/`, live wire pins stay
in `test_query/`); no `ruff` run owed (no `.py` touched); no `pytest` run
beyond the authorized focused proof. Markdown/line-length handling is
Worker 0's closeout concern; no prose violation found.

### Defects — none new (Worker 2)

W1's two cleared candidates (codeless login, inline model-less payloads) were
independently opened above and stand cleared as contracts. No additional
defect found while tracing. No `(Worker 2)` defect entry owed.

### Verdict

`revision-needed` on ONE point only: land proved G1–G3 in
`tests/utils/test_errors.py` (clean) now; everything else verified as found.
Worker 1 lands the gate; resubmission returns to THIS Worker 2 (trace above
already on disk). Preserve all concurrent dirt; do not commit. Plan stays
unticked until re-verification passes.

## Iterations

### Pass 2 (Worker 1) — landed G1–G3, resubmission `ready-for-verification/2`

Owed landing only; no finding, challenge, count, owner, rejection,
trigger, or defect changed — all prior reasoning stands. The F1
"landing DEFERRED" bullet above is SUPERSEDED by this landing (kept
for history, not edited).

Attribution re-checked before editing: `tests/utils/test_errors.py`
worktree blob `83662dee…` == HEAD (clean); every other dirty path
read-only. The edit touches that one clean file only (+118/−0).

Gate added to `tests/utils/test_errors.py` (owner-adjacent `tests/`
tier; implements the proved `envelope_gate.py` logic in the landed
`tests/base/test_init.py` cardinality-pin style):

- `_OWNER_SYMBOLS` + `_strip_docstrings` + `_envelope_singularity_census`
  (docstring-stripped AST walk over the package population; the
  `list_field.py` prose exclusion is structural — prose is a string
  constant, never a Call/Def node — made explicit by the strip).
- `test_envelope_leaf_has_exactly_one_construction_site` (G1 —
  file-pinned to `utils/errors.py`, never a line number).
- `test_envelope_owner_symbols_are_defined_once_each` (G2 — key set
  plus per-symbol count).
- `test_envelope_codes_carry_no_string_literals` (G3).
- Each asserts `unparseable == []` (fail-closed walk) and
  `scanned > 0`; no production edit.

Proofs: `uv run ruff check --fix` + `uv run ruff format` on the
touched path (one SIM102 combine + one format pass inside the new
block; `format --check` + `check` both green after). Focused
`uv run pytest tests/utils/test_errors.py -n0 --no-cov -q
-p no:cacheprovider` in the shared tree → 41 passed (38 + 3).
WS negative-control re-proof with the LANDED tests (same
disposable copy, `$WS` cwd, copy `__file__` re-verified):
G1 FAILED exactly on the hand-copy bypass
(`['mutations/resolvers.py@461', 'utils/errors.py@171']`),
G2/G3 passed; then `mutations/resolvers.py` in the copy restored
from the shared tree — `git hash-object` `a322d17a…` identical on
both sides — and all 41 passed again. Shared-tree database
untouched throughout.

Freshness delta this pass: `tests/utils/test_errors.py`
`83662dee…` → `db7da59a…` (the gate only); all eleven finding
fingerprints re-verified unchanged (`mutations/inputs.py`
`fc442047…`, `utils/errors.py` `3e25e93b…`,
`mutations/resolvers.py` `a322d17a…`,
`auth/mutations.py` `200805d2…`, `forms/resolvers.py`
`4edb984b…`, `rest_framework/resolvers.py` `8024703e…`,
`utils/write_values.py` `d28587c7…`,
`utils/write_transaction.py` `eca9ad4d…`,
`mutations/sets.py` `936f5ae7…`, `forms/sets.py` `98ef150d…`,
`rest_framework/sets.py` `2c7117d6…`). HEAD still `bfaee91d`.

Worker 0 rows: tick Family `mutation-error-envelope` (this
artifact, `ready-for-verification/2`, gate landed, no pending
execution); append `## Owned changes`:
`tests/utils/test_errors.py` — Family `mutation-error-envelope`
— G1–G3 envelope singularity pins (gate-only; production
untouched); no defects to home.

### Pass 3 (Worker 1) — prescribed layout explode, resubmission `ready-for-verification/3`

Blocking cause only; no finding, challenge, count, owner,
rejection, trigger, defect, or gate logic changed — all prior
reasoning stands.

Fix (touched path only, exactly the prescribed shape):
`tests/utils/test_errors.py::_strip_docstrings` — the 4-tuple
`(ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),`
exploded one-per-line with the magic trailing comma. Nothing
else moved (item diff +123/−0 on the test file: +118 gate
plus 5 net lines from the explode, zero deletions outside it).

Proofs on the touched path: `python3
scripts/check_trailing_commas.py --check tests/utils/test_errors.py`
exit 0; `uv run ruff format --check` → already formatted (magic
trailing comma is formatter-stable, no conflict); `uv run ruff
check` → all checks passed; focused `uv run pytest
tests/utils/test_errors.py -n0 --no-cov -q -p no:cacheprovider`
→ 41 passed. Pre-existing concurrent dirt untouched; no commit.

Worker 0 rows: tick Family `mutation-error-envelope` (this
artifact, `ready-for-verification/3`, gate landed + layout
gate green, no pending execution); `## Owned changes` row from
pass 2 stands (same file, same gate).

## Independent re-verification (Worker 2) — pass 2, verdict `revision-needed`

Re-read `## Independent verification (Worker 2)` (own trace, unchanged) then
`## Iterations` pass-2 record above; re-derived only what the landing
disturbs. Prior `revision-needed` (gate must land) is DISCHARGED — the gate
landed in the owed file with the owed shape. One new blocking cause below.

### Landing-diff check — PASS (exactly +118/-0, nothing else moved)

`git diff HEAD -- tests/utils/test_errors.py` is one hunk, +118/-0, appended
after line 502 (`test_validation_error_mapper_treats_a_text_atom_error_list...`
untouched; no deletion/modification lines anywhere in the diff). Added lines:
118, all ASCII, none over 99 chars. Imports reused (`ast`, `Path`,
`errors_module` already at file head) — no import churn. Contents are exactly
the owed three pins + census helper: `_OWNER_SYMBOLS` (5 names),
`_strip_docstrings`, `_envelope_singularity_census`,
`test_envelope_leaf_has_exactly_one_construction_site` (G1),
`test_envelope_owner_symbols_are_defined_once_each` (G2),
`test_envelope_codes_carry_no_string_literals` (G3). Matches the pass-2 claim
line for line.

### Lint/layout — MIXED (one blocking violation, new not pre-existing)

- `uv run ruff format --check tests/utils/test_errors.py` → `1 file already
  formatted` (exit 0). PASS.
- `uv run ruff check tests/utils/test_errors.py` → `All checks passed!`
  (exit 0). PASS.
- `python3 scripts/check_trailing_commas.py --check
  tests/utils/test_errors.py` → FAIL:
  `tests/utils/test_errors.py:525: should explode (>= threshold, no trailing
  comma)` (exit 1). BLOCKING.
- Provenance: the HEAD version (`git show HEAD:...` to scratch) passes the
  same `--check` (exit 0), so the violation is NEW in the +118 block, not
  inherited. Line 525 is the 4-tuple
  `(ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),` on one
  line inside `_strip_docstrings` — threshold 4 per `AGENTS.md`, so it must
  explode one-per-line with a magic trailing comma. `AGENTS.md` enforces this
  script pre-commit + CI `--check`; landing as-is reddens CI.

Concrete cause (Worker 1 fix, touched path only — do NOT touch concurrent
dirt): replace lines 523–526 with

```python
        if not isinstance(
            node,
            (
                ast.Module,
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
```

Verified on a scratch copy (never the tree): the script's auto-fix produces
exactly this shape, `--check` re-passes (exit 0), and `ruff format --check`
still reports already-formatted (magic trailing comma is formatter-stable —
no format conflict). Then rerun `uv run ruff check` on the touched path +
the focused suite below and resubmit `ready-for-verification/3` (returns to
THIS Worker 2; trace already on disk).

### Focused-run result — PASS (41 passed)

`uv run pytest tests/utils/test_errors.py -n0 --no-cov -q -p no:cacheprovider`
in the shared tree → `41 passed in 0.88s` (38 + 3). Matches the pass-2 claim.
No other test run owed by this item.

### Census fail-closed judgment — PASS

- Unparseable files append to `unparseable` and every test asserts
  `unparseable == []`: a `SyntaxError` fails the gate, never silently drops
  a file from the census. Fail-closed confirmed.
- Population is the full package: `package_root` resolves from
  `errors_module.__file__` up two levels (`django_strawberry_framework/`)
  and walks `rglob("*.py")`; `scanned > 0` asserted per test. (`> 0` rather
  than `== 117` is correct: an exact file count would brittly couple the
  gate to inventory growth, which plan reconciliation already covers; the
  exact-match assertions on sites/defs carry the weight.)
- `list_field.py` exclusion is structural, not textual: matching runs on
  docstring-stripped AST `Call`/`Def` nodes, so Django's unrelated
  `FieldError` prose (a `Constant` string, never a `Call`) cannot match with
  or without the strip; the strip is explicit belt-and-braces. G1 additionally
  pins the file list to `["utils/errors.py"]`, so prose-turned-code anywhere
  would red. Confirmed.
- Walk is over package source only (never `tests/`), so the gate cannot
  count itself; `sorted(rglob(...))` is deterministic.

### G1 file-pin judgment — PASS

G1 compares `[site.split("@")[0] for site in construct_sites]` (linenos
recorded for the failure message only) against `["utils/errors.py"]`: robust
to line moves within the owner, reds on any owner-file move or second site —
the correct sensitivity for a singularity pin. No line number pinned.

### Production-unchanged judgment — PASS

`git diff 8c916988a892728d0c3c515d184c302f1afbbd4a --stat --
django_strawberry_framework/` is EMPTY: item diff = test file +118 +
untracked artifact only, as claimed. `git diff HEAD --stat --
django_strawberry_framework/` lists the 24 pre-existing concurrently-dirty
files, none touched by this item. Re-hashed: `mutations/inputs.py`
`fc442047…`, `utils/errors.py` `3e25e93b…`, `mutations/resolvers.py`
`a322d17a…`, `auth/mutations.py` `200805d2…` (dirty pair unchanged from
pass 1), `tests/utils/test_errors.py` `db7da59a…` (the gate only). HEAD still
`bfaee91d`. WS negative-control re-proof (G1 red naming both sites,
G2/G3 pass, hash-identical restore → 41 pass) is internally consistent with
the landed test logic and is accepted as recorded (disposable-copy proof;
shared-tree database untouched).

### Verdict

`revision-needed` on the single layout cause above; all substance verified
(census, pins, fail-closedness, file-pin, 41 green, zero production
movement). Worker 1 applies the prescribed explode, re-runs the three checks
+ focused suite on the touched path, resubmits; no new finding, challenge,
owner, rejection, trigger, or defect is opened by this pass.

## Independent re-verification (Worker 2) — pass 3, verdict `verified`

Re-read the pass-2 `## Independent re-verification (Worker 2)` (blocking
layout cause + prescription) and the pass-3 `## Iterations` entry above;
re-derived only what the comma fix disturbs. The blocking cause is
DISCHARGED; nothing else moved.

### Byte-identity check — PASS (prescribed explode only)

`git diff HEAD -- tests/utils/test_errors.py` is one hunk, +123/-0, zero
deletion lines: the +118 gate block byte-identical to the pass-2 read
(`_OWNER_SYMBOLS`, `_strip_docstrings` logic, `_envelope_singularity_census`,
G1/G2/G3 bodies, comments) apart from the single prescribed region, now
exactly

```python
        if not isinstance(
            node,
            (
                ast.Module,
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
```

(+5 net lines = +123). The 3-tuple in `_envelope_singularity_census`
correctly stays single-line (below threshold 4). Item diff vs `8c916988` =
test file +123/-0 + untracked artifact only; production diff EMPTY
(`mutations/inputs.py` `fc442047…`, `utils/errors.py` `3e25e93b…`,
`mutations/resolvers.py` `a322d17a…`, `auth/mutations.py` `200805d2…` —
all match prior fingerprints; HEAD still `bfaee91d`).

### Four command results (all run by Worker 2 in the shared tree) — ALL GREEN

- `python3 scripts/check_trailing_commas.py --check
  tests/utils/test_errors.py` → exit 0, no output. PASS.
- `uv run ruff format --check tests/utils/test_errors.py` → `1 file already
  formatted`. PASS.
- `uv run ruff check tests/utils/test_errors.py` → `All checks passed!`.
  PASS.
- `uv run pytest tests/utils/test_errors.py -n0 --no-cov -q -p
  no:cacheprovider` → `41 passed` (38 + 3). PASS.

### Verdict

`verified`. Gate G1–G3 landed in the owed clean file with the owed shape,
layout gate green, 41 green, zero production movement, no pending execution
(prior judgment stands — every proof `execution-verified`). No new finding,
challenge, owner, rejection, trigger, or defect opened. Concurrent dirt
untouched; no commit.
