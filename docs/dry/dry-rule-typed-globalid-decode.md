# DRY review: `typed-globalid-decode`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `typed-globalid-decode`. Provisional owner
`django_strawberry_framework/relay.py::decode_model_global_id`
(+ `GlobalIDDecode` / `DecodeResult` / `_resolve_real_pk`) — CONFIRMED, not
inherited. Member files: `django_strawberry_framework/relay.py`,
`django_strawberry_framework/mutations/resolvers.py`,
`django_strawberry_framework/utils/write_values.py` (form/serializer decoders
via the shared pipeline). The only item hunk is a 5-line docstring trigger
clause on `relay.py`, below. Prior records only as triggers: the
`relay-node-name-decode` item (its open seam to this family:
`decode_model_global_id` composes `decode_global_id` by name + model/pk
rules — every edge below re-derived from the body, nothing inherited) and the
`field-value-coercion` rejection (the shared coercion primitive stays out of
this family's counts). Never read any `worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds no row on any family
path (rows cover only `optimizer/walker.py`, two fakeshop live files,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`, `registry.py`) — confirmed by full read.
`mutations/resolvers.py` carries EXTERNAL concurrent dirt: the diff vs HEAD
is the `_safe_class_name` hostile-name hunk only (one import line + five
message sites), with zero overlap against any decode site
(`coerce_lookup_id`, `_decode_single_relation_id`,
`_decode_relation_id_list`, `_decode_relations`, `locate_instance`) —
verified by hunk positions. `relay.py` + `utils/write_values.py` are clean
vs both HEAD and `ITEM_BASELINE` (`2812607d6028a3cfaeaad3044a3282990f3b9ab4`,
verified present via `git cat-file -t`). No dirty path was edited, so no
STOP arose; reading the dirty file was free.

## System trace

Rule: decoding a typed GlobalID (`type:pk` wire string) into a model + pk
with failure modes — the write-path counterpart of node decode.

The owner pipeline ([root-relay][root-relay]`::decode_model_global_id`):
decode the value via [relay-types][relay-types]`::decode_global_id`
(shape-only, composed by name) → verify the resolved type's model **is**
`expected_model` (identity, not string compare) → coerce `node_id` through
the resolved type's id field via `_coerce_pk_or_none` (the SAME coercer the
node field uses) → map to the real pk via `_resolve_real_pk`. Non-raising:
every outcome is a `DecodeResult` classified by `GlobalIDDecode`.

Wire shape accepted: a `relay.GlobalID` object or its base64 string with
both `type_name` / `node_id` slots non-empty, the type slot resolving (model
label via `apps.get_model` + `registry.get`, or type name via
`definition_for_graphql_name`) AND permitted under the candidate's recorded
strategy. Rejected to `DECODE_FAILED`: non-`(GlobalID, str)` input,
malformed base64, empty slots, unresolvable label/name, strategy-forbidden
shape, absent strategy — the broad `except Exception` is fail-closed by
construction (`decode_global_id` raises `ConfigurationError` on every arm;
anything else escaping is likewise not a typed id for this model).

Failure envelope per decode site (exact):

- `decode_model_global_id` → `DecodeResult`, never raises. `OK` carries the
  real pk; `DECODE_FAILED` / `WRONG_MODEL` / `UNCOERCIBLE_PK` carry `pk=None`
  (`resolved_type` set except on `DECODE_FAILED`).
- `coerce_lookup_id` (update/delete `id:`, [model-resolvers][model-resolvers])
  → `(pk|None, FieldError|None)`: `DECODE_FAILED` + `WRONG_MODEL` collapse
  to the invalid-id `FieldError` on `id` BEFORE any pk lookup (a raw pk
  string with no GlobalID shape lands here too — never coerced to a bare pk
  that would target the same-pk row of the right model);
  `UNCOERCIBLE_PK` maps to the not-found `FieldError` on `id` (same surface
  as a hidden row; the node field's `null` spelled in-band).
- `type_check_relation_id` ([write-values][write-values], every relation id
  on every flavor) → `(pk|None, FieldError|None)`: any non-`OK` GlobalID
  status is the uniform `relation_field_error`; the raw-pk branch coerces
  through `coerce_relation_pk_or_none` (`None` → the SAME error). No DB
  touched on either branch.
- `decode_visible_relation` / `decode_visible_relation_ids`
  ([write-values][write-values]) → `(projected|None, FieldError|None)`:
  per-id `type_check_relation_id`, then the visibility query
  (`visible_related_object` / one batched `pk__in` via
  `visible_related_objects`); hidden and missing are the same
  `relation_field_error`, no existence leak.
- Read side (contrast, not members): the node field raises `GraphQLError`
  (`GLOBALID_INVALID` collapse, code-less wrong-type, `null` on
  uncoercible); the filter `_decode_and_validate_global_id` raises
  `GraphQLError` on its own parse (sibling seam, below).

One pipeline, three flavor colorings. Census: exactly 1 `def
decode_model_global_id` with exactly 2 production callers
(`coerce_lookup_id`; `type_check_relation_id`); exactly 1 `def
type_check_relation_id`, called by `decode_visible_relation` and
`decode_visible_relation_ids`; exactly 1 `def _resolve_real_pk` with 1
caller; exactly 1 `def coerce_relation_pk_or_none` with 1 caller; zero
`from_id` parses in the write path (census: the only two production
`from_id` calls are `decode_global_id`'s and the filter's). Consumers
compose by name, never re-validate: the model path
(`_decode_single_relation_id` wraps one id into `[value]` for the batched
compose; `_decode_relation_id_list` adds the null-reject) rides
`relation_into` / `decode_provided_fields`; the form single decoder colors
the spine with `empty_values` skip + `to_field_name` projection (its multi
maps the single per element because it needs the object); the serializer
single colors it with `None`-skip + `obj.pk` projection (its multi rides
the batched compose). Null/skip/projection differ per flavor contract
(model rejects null M2M, form honors `empty_values`, serializer passes
`None` through) — documented adapters, each recorded at its own decoder,
never a second validation.

`_resolve_real_pk` maps a coerced NodeID-attr value to the row's real pk
through the default manager (or the pinned `using`; relation/serializer
riders recover the pipeline alias via `current_write_pipeline`). A value
matching no row returns `None` → the caller surfaces `UNCOERCIBLE_PK`; a
value matching a *hidden* row resolves and is rejected downstream —
indistinguishable from missing. The default (`id_attr == "pk"`) and a
NodeID over a non-concrete attr pass through with no query.

Lifetime (principle 4): there is no stored derivation — pure per-call
(`static-reviewed` over all four bodies: no cache, memo, or index).
`_resolve_real_pk` queries live on every call; decode answers follow
`clear()` / rebuild with no invalidation because every read
(`decode_global_id`'s scan, `model_for`, the manager query) is live.
Validity key = the registry store lifecycle; publish point = finalization
recording `effective_globalid_strategy`; mutation = store lifecycles only.

Connected sources read: [relay-types][relay-types] (`decode_global_id`
input gate + Steps 1/2 + strategy memberships), [model-resolvers][model-resolvers]
(`coerce_lookup_id`, `_decode_single_relation_id`,
`_decode_relation_id_list`, `_decode_relations`, `locate_instance`),
[form-resolvers][form-resolvers] (single/multi + module prose),
[serializer-resolvers][serializer-resolvers] (single/multi),
[filters-base][filters-base] (`_decode_and_validate_global_id`,
`_accepted_globalid_type_names` — seam only), [testing-relay][testing-relay]
(mint/decode pair), [write-tx][write-tx] (`current_write_pipeline`),
`utils/querysets.py` (`coerce_field_value_or_none`,
`visible_related_object(s)` — shared primitives, counted by their own
rejected family, not here), [list-field][list-field] (target-guard seam),
[root-relay][root-relay] stamp + typed-match arms (seams). Excluded on
strength of body: every other package module (zero rule vocabulary over
the whole-package sweep).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Model, form, and serializer relation
   decoders all ride `type_check_relation_id`; the update/delete `id:`
   rides `decode_model_global_id` directly. No flavor keeps a second
   GlobalID→model+pk body (def census: 1 each). Flavor deltas are null /
   skip / projection adapters with per-decoder contract prose. Trigger:
   a flavor decoding a GlobalID without `type_check_relation_id`.
2. **Sync/async twins.** Decode is sync dict/string work plus one sync ORM
   lookup; no `async` twin exists and none is owed (pipelines run it inside
   one sync boundary). Trigger: an async twin of the pipeline.
3. **Derived rather than repeated knowledge.** The pk derives once per call
   at the owner; no caller re-parses (`from_id` census above) or
   re-compares models (the identity check lives in one arm). A rename of
   the wire shape moves `decode_global_id` only (C1). Trigger: a second
   parse or model-compare site.
4. **Inverse / round-trip pairs.** Encode (`encode_typename`) vs decode
   share the recorded strategy; `decode_model_global_id` is the
   write-path specialization (model-check + pk-coercion + real-pk map),
   not a second decode. `global_id_for` mints via `encode_typename`.
   Oracles pin round trips at three tiers (unit, package, live).
5. **Contracts restated in another medium.** Production (pipeline +
   adapters); oracles (independent literals — genre/shelf GlobalIDs,
   raw-pk strings, garbage — never reading the owner body); projections
   (docstrings verified against bodies except the two stale names in
   `## Defects`; spec-031 Decisions 8/13, spec-032 Decisions 3–5,
   spec-036 Decision 10, spec-038 Decision 8, spec-039 Decision 7).
6. **Enforcement by omission.** Every write `id` entry funnels through
   the spine: update/delete `id:` via `coerce_lookup_id`; every relation
   id on all three flavors via `type_check_relation_id` (the raw-pk
   branch included). No member lacks the guard its contract requires:
   no defect.

### Enumeration

Instrument: whole-package sweep for `decode_model_global_id |
_resolve_real_pk | GlobalIDDecode | DecodeResult | decode_global_id |
type_check_relation_id | decode_visible_relation` (98 matches incl. prose,
each classified) + `from_id` census (2 production calls) + `def` census
per symbol. Population: 117 `.py` (plan count; no adds/renames).

- `decode_model_global_id`: 1 def; 2 production callers
  (`coerce_lookup_id`, `type_check_relation_id`).
- `_resolve_real_pk`: 1 def; 1 production caller.
- `GlobalIDDecode` / `DecodeResult`: 1 def each; mappers are the two
  callers above (adapters, listed).
- `type_check_relation_id` / `coerce_relation_pk_or_none` /
  `decode_visible_relation` / `decode_visible_relation_ids` /
  `coerce_lookup_id`: 1 def each.
- Adapters (consumers, listed not counted): model single/list,
  `_decode_relations`, form single/multi, serializer single/multi,
  `relation_into` / `decode_field_handlers` / `decode_provided_fields`.
- Parallel readers (listed not counted): node-field decode/match/coerce
  arms, filter `_decode_and_validate_global_id` (separate path — seam),
  testing re-export, `locate_instance` / visibility primitives.
- Oracles: `tests/test_relay_node_field.py` 3 decode rows (custom-NodeID
  real-pk, no-row uncoercible, non-field passthrough),
  `tests/mutations/test_resolvers.py` `coerce_lookup_id` rows (incl.
  parametrized non-GlobalID rejects),
  `tests/utils/test_write_values.py` type-check + batched-visibility rows,
  `tests/rest_framework/test_resolvers.py` wrong-model row, live
  mutation tiers.

### Challenges

Counts are authoritative definitions only; adapters, oracles,
projections listed, never counted. Workspace proofs map onto C0–C3
(20-test selection `execution-verified` in the copy and in the shared
tree; controls below `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New id format (new strategy payload shape) | **1** (`decode_global_id` Steps + strategy memberships; this pipeline composes unchanged). The filter accepted-set is the hardening family's site — listed, not counted. |
| C2 | New failure mode (fifth `DecodeResult` status) | **1** (the `GlobalIDDecode` taxonomy at `relay.py`) + 2 consumer mapper arms owed (`coerce_lookup_id`, `type_check_relation_id` — adapters, listed). Note: the `coerce_lookup_id` tail falls through to success for unlisted statuses, so the new status must add arms — trigger, not defect (no such status exists today). |
| C3 | Model-label vs type-name mismatch policy (which payload a strategy accepts) | **1** (`decode_global_id` Step 2 + the strategy membership sets; the `WRONG_MODEL` model-identity arm is orthogonal and unchanged). Owned outside this family — seam. |
| C0 | New write flavor's relation-id decode (the maintainer's pipeline question) | **1 per stage** (adapters over `type_check_relation_id` / the batched compose; the serializer promotion `e9c13f55` is the worked precedent: three flavors' bodies merged into one spine in a single commit). |

**Experiments (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --frozen --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/typed-globalid-decode-w1
uv run --frozen --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --frozen --directory "$WS" pytest <20-test selection> --no-cov -n0 -q
```

Proof (20 passed in the copy; 20 passed shared-tree, zero member edits
in flight): status taxonomy, both `coerce_lookup_id` envelopes,
type-check + batched-visibility + container hardening, the serializer
wrong-model row. Copy `__file__`:
`.../dry-ws/typed-globalid-decode-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/typed-globalid-decode-w1/examples/fakeshop/db.sqlite3`
(the copy's own tree and database). No source mutation in the proof;
restores N/A.

Negative controls (same workspace, pristine backups kept; each restored
byte-identical, re-verified):

- Control A2 (divergent: `UNCOERCIBLE_PK` arm returns `OK`):
  `pytest tests/test_relay_node_field.py -k decode_model_global_id` →
  1 failed (`custom_node_id_no_row_is_uncoercible`), 2 passed. The
  standing oracles can fail for the divergence they guard.
- Control A (divergent: `WRONG_MODEL` arm returns `OK`): full selection
  → 20 passed. NOT vacuous-oracle evidence — a defense-in-depth
  observation: `pk=None` still fails the downstream visibility query to
  the same field error. Recorded as robustness, not a second definition.
- Control B (behavior-preserving: byte-identical
  `decode_model_global_id_copy` serving `coerce_lookup_id`): full
  selection → 20 passed. No behavioral gate can pin call-unity; only a
  source census can, which [DRY.md][dry] forbids for gate-only findings.

One authorized shared-tree focused run (zero member edits in flight):
the same 20-test selection `--no-cov -n0` → 20 passed.

## Findings

### F1 — typed GlobalID decode pipeline (CONFIRMED single-owned: no consolidation owed)

- **Contract + variation.** A typed GlobalID decodes to a real pk for an
  expected model with four failure modes. Varies on: input shape
  (GlobalID object vs base64 string; raw pk accepted only at the
  relation seam); failure surface per caller (`id` envelope vs relation
  envelope vs `DecodeResult`); NodeID slot (pk passthrough vs custom-attr
  lookup vs non-field passthrough).
- **Sites + roles.** *Definition*: `decode_model_global_id` +
  `GlobalIDDecode` + `DecodeResult` + `_resolve_real_pk` (1 def each).
  *Composed primitive*: `decode_global_id` (owned by the hardening
  family; called by name). *Adapters*: the two status mappers + all
  flavor single/multi decoders. *Consumers / oracles / projections*: as
  listed in System trace.
- **Challenges.** C1 → 1; C2 → 1 (+2 adapter arms); C3 → 1 (external
  owner); C0 → 1 per stage. Count > 1 nowhere in one rule.
- **Owner + lifetime (principles 7, 4).**
  [root-relay][root-relay]`::decode_model_global_id` stands: the decode +
  model-check + pk-coercion contract is write-path-specific (the read
  node field raises where this returns); every write flavor can depend
  on it without reversing a dependency (`write_values` already imports
  it function-locally to dodge the `relay → utils.querysets` cycle;
  `mutations/resolvers` imports it directly); the status taxonomy and
  the NodeID→pk map are meaningless outside this contract, so splitting
  them would orphan the pieces. Stored-derivation lifetime: not cached
  (see System trace).
- **Migration.** None — the pipeline is already single. One 5-line
  docstring trigger clause at the owner (projection; behavior identical
  — AST-identity proof below). No test changes: taxonomy, envelope, and
  visibility rows already pin every arm.
- **Distinct behavior (stays separate).** Per-surface error shapes (the
  `id` invalid/not-found split vs the uniform relation error are
  different contracts, not two spellings); flavor null/skip/projection
  adapters (recorded at each decoder); the read node field's raising
  behavior; the filter raising path (hardening family's site — seam).
- **Behavioral proof.** `execution-verified` for taxonomy, envelopes,
  single-pipeline census, and lifetime-liveness (WS 20 passed +
  authorized shared-tree 20 passed, zero member edits in flight).
  `static-reviewed` for the zero-second-parse census, the oracle-body
  independence (plain test classes, literals), and the docstring prose.
  Control A2 rejects "the oracles cannot see divergence"; Control B
  rejects "a gate could pin unity"; Control A is recorded as
  defense-in-depth, not oracle cover.
- **Structural gate.** None owed, with proved reason: Control B (a
  correct copy serving one caller) passes every standing oracle, so no
  behavioral gate can pin unity — same standard as the verified
  name-decode, definition-store, enum-cache, and subscription-masking
  items. Unity rests on the def/caller census and triggers T-pipeline /
  T-status / T-shape below. Coverage that stays: the taxonomy rows
  (fail a lost arm — Control A2), the wrong-model serializer row, the
  visibility-indistinguishability rows.
- **Coupling.** None. Adjacent open families untouched; the clause is
  docstring-only (AST proof below).
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `relay.py` `69085e7a…` (post-clause; pre-clause `c3c5aea5…` — proofs
  ran against it, bridged by the AST-identity check below),
  `utils/write_values.py` `d28587c7…`,
  `mutations/resolvers.py` `a322d17a…` (external hostile-name hunk;
  cited decode lines verified outside it), `types/relay.py`
  `52439862…`, `filters/base.py` `ba52351c…`, `forms/resolvers.py`
  `4edb984b…`, `rest_framework/resolvers.py` `8024703e…`,
  `utils/querysets.py` `96618fba…`, `utils/write_transaction.py`
  `eca9ad4d…`, `testing/relay.py` `df0dc72a…`, `list_field.py`
  `ce682d5f…`, `tests/test_relay_node_field.py` `2fd9e458…`,
  `tests/mutations/test_resolvers.py` `c068aea1…`,
  `tests/utils/test_write_values.py` `ac35ddd0…`. `HEAD` `bfaee91d`;
  `ITEM_BASELINE` `2812607d…` (all five traced paths clean vs it before
  the clause). Searched population: whole package (117 `.py`) for the
  rule tokens. Any fingerprint change reopens the finding.
- **Reconsideration triggers (recorded at the owner).** T-pipeline fires
  if a write `id` decode bypasses this primitive; T-status fires on a
  fifth status (both mappers add arms); T-shape fires on a new wire
  shape (`decode_global_id` owns the parse). Durable homes: the new
  docstring clause on
  [root-relay][root-relay]`::decode_model_global_id`, this finding, and
  the plan's `## Outcomes` via Worker 0.

### Sibling seams (open families — stated, not decided)

- `relay-node-target-guard` ([list-field][list-field] target validation +
  runtime `locate_instance` / visibility): answers shape-of-target at
  construction and existence/visibility at runtime; decode answers
  shape-of-input + model-match + pk-coercibility. Different questions
  (shape vs existence vs policy) → no consolidation with decode.
  Trigger: a guard reading `DecodeResult` statuses. Home: the guard
  owner + this finding.
- `relay-node-type-stamp` (`_stamp_node_type`): downstream consumer of
  decode-routing output (carries the resolved type to `is_type_of`);
  never decodes. Trigger: stamping before decode. Home: the stamp
  owner + this finding.
- `globalid-relation-pk-marker` (the `_GLOBALID_RELATION_PK_ATTR` trio):
  read-path filter concern (non-pk `to_field` routing); the write path
  handles non-pk NodeIDs via `_resolve_real_pk`. Different populations.
  Trigger: a marker read in the write pipeline. Home: the marker owner
  + this finding.
- `globalid-decode-input-hardening` (`decode_global_id` input gate +
  slot normalization): this family already composes it by name (one
  call site; zero own parses) — consolidated by construction, nothing
  to move. The filter's separate `from_id` parse is that family's
  member site, not this family's second definition. Trigger: a third
  parse site. Home: `decode_global_id` + this finding.
- `globalid-setting-snapshot` (strategy resolution/recording): decode
  reads the recorded `effective_globalid_strategy`; the snapshot owns
  recording. Trigger: decode reading the setting directly. Home: the
  finalizer snapshot + this finding.

## Defects

Non-duplication defects found while tracing. Each with its owner;
unfixed inside this item per [DRY.md][dry].

- D1: [root-relay][root-relay]`::decode_model_global_id` docstring names
  the relation `<field>_id` decode consumer as
  ``_decode_relation_id_set`` — no such symbol exists in the package
  (the only other mention is a `tests/mutations/test_resolvers.py`
  comment). The name was removed by `e9c13f55` ("Share batched
  relation-id decode …"), which consolidated relation decode into
  `decode_visible_relation_ids` (via `_decode_single_relation_id` /
  `_decode_relation_id_list`); the two prose references were never
  swept. A reader verifying the relation decode path searches for an
  absent function. Owner: the `decode_model_global_id` docstring
  (projection) + the test comment (same root cause, same defect).
- D2: [form-resolvers][form-resolvers] module docstring names
  ``_coerce_relation_pk_or_none`` for the raw-pk relation branch — no
  such symbol exists; the single definition is
  [write-values][write-values]`::coerce_relation_pk_or_none` (no leading
  underscore; def census: 1). Owner: the `forms/resolvers.py` module
  docstring (projection).
- D3 (Worker 2): no oracle pins the `WRONG_MODEL` taxonomy arm or the
  `id:`-surface INVALID-vs-NOTFOUND distinction. `tests/` carries exactly
  3 `GlobalIDDecode.` status assertions (all OK / UNCOERCIBLE_PK, zero
  WRONG_MODEL); the coerce oracle
  (`tests/mutations/test_resolvers.py::test_coerce_lookup_id_rejects_non_globalid`)
  and the live wrong-model `id:` oracles
  (`test_update_item_wrong_type_global_id_on_id_is_field_error` + the
  delete twin) assert `field == "id"` + null + row-untouched only, never
  the INVALID code/message. Under the Control A mutant (WRONG_MODEL arm
  returns OK, pk stays None) the relation surface still yields the SAME
  `relation_field_error` via the visibility backstop, but the `id:`
  surface shifts from INVALID ("Invalid id.") to NOT_FOUND ("No matching
  row found.") — safe (pk=None never coerces cross-model; no leak) yet
  contract-distinct and unasserted. Owed oracle (test-only, blocks
  nothing): `decode_model_global_id(wrong_model_gid, Expected)` asserts
  `status is WRONG_MODEL` (pk None, `resolved_type` set), and/or
  `coerce_lookup_id(wrong_model_gid, ...)` asserts the INVALID
  code/message distinct from not-found. Owner: tests (oracle gap, same
  class as the run's definition-store D1).

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace; the one authorized shared-tree focused run executed green
(20 passed) with zero member edits in flight. No `execution-deferred`
items. `FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by
construction`: every executed claim is string/dict/enum work plus
single-alias ORM lookups on the default test database (the recorded
`NAME` is the copy's own file). Full-suite gate business is deferred to
the final-gate item with reason: the entry authorizes workspace runs
plus one focused `--no-cov` test, and a green unmutated suite would
discharge no failability proof for a confirmation that proposes no gate.

## Judgment

Write-path typed-ID decode is already one pipeline: one primitive
(`decode_model_global_id`, composing `decode_global_id` by name), one
structural check (`type_check_relation_id`), one batched visibility
compose, with per-flavor adapters for null/skip/projection only. The
maintainer's validation question resolves as: exact wire shape
accepted/rejected established per site (table above), failure envelopes
typed per surface (`DecodeResult` → `FieldError`-on-`id` vs
relation-`FieldError`, never raised, never `None`-as-success), and the
form/serializer/mutation decoders share ONE pipeline (1 def per stage;
C0). Sibling families answer different questions — seams stated with
triggers, none consolidated. Owner confirmed; one projection-only
trigger clause added; two stale-name defects recorded unfixed.

## Implementation (Worker 1)

Tracked change (1 file, docstring-only):
`django_strawberry_framework/relay.py` —
`decode_model_global_id` docstring gains the T-pipeline / T-status /
T-shape reconsideration-trigger clause (+5 lines; behavior untouched).
Attribution: `relay.py` clean at `ITEM_BASELINE` and at HEAD before the
edit; `git diff HEAD -- django_strawberry_framework/relay.py` shows only
it; no `## Owned changes` row exists on any family path, so no conflict;
Worker 0 appends: `django_strawberry_framework/relay.py` — Family
`typed-globalid-decode` — `decode_model_global_id` docstring trigger
clause (projection; behavior untouched).

After the edit: `uv run ruff check --fix
django_strawberry_framework/relay.py` + `uv run ruff format
django_strawberry_framework/relay.py` — both green (`format --check` +
`check` pass on the path; scoped to the path so no concurrent dirt is
rewritten). INVERSE proof (docstring-only edit): docstring-stripped AST
of `HEAD:relay.py` vs worktree — `AST-IDENTITY-NO-DOCSTRINGS: True`
(read-only check, not a test run). Per `AGENTS.md` no pytest after
edits; the pre-edit focused run (20 passed) still discharges the finding
by that AST identity. No `CHANGELOG.md` touch. No commit per standing
rule.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/typed-globalid-decode-w1`
(includes its own `.venv`, `relay.py.pristine`,
`write_values.py.pristine`, `mresolvers.py.pristine` holding the
pre-control backups). No manifest (no `prove_failability.py` run — no
gate added, none owed; Controls A/A2/B are the hand-proved pair).

Worker 0 rows: tick Family `typed-globalid-decode` (this artifact); no
`## Responsibility index` change (provisional owner + all three member
files already covered); append the `## Owned changes` row above; home
D1 + D2 each on a NAMED owning card at closeout (projection-only
docstring/test-comment repairs; block nothing).

## Independent verification (Worker 2)

Method note: the dispatch's required reading order routed the full
artifact (incl. `## Findings`) before this trace. Mitigation: every
count below was re-censused from source via package-wide grep and every
mechanism re-traced from the cited bodies; agreements and the one
difference are reconciled per claim at the end. Never read any
`worker-memory/`.

### Own trace

Rule: typed GlobalID (`type:pk` wire) -> (model, real pk) with a
4-status non-raising taxonomy, write-path only.

Definitions (def census, whole package): 1 `def
decode_model_global_id` ([root-relay][root-relay]:287), 1 `class
GlobalIDDecode` (:202), 1 `class DecodeResult` (:217), 1 `def
_resolve_real_pk` (:232) — no second def of any of the four anywhere.
Composed primitive: [relay-types][relay-types]`::decode_global_id`
(imported :68, called by name :318; shape-only) plus the shared coercer
`_coerce_pk_or_none` (the node field's body). Exactly 2 production call
sites of `decode_model_global_id(`: [model-resolvers][model-resolvers]
`::coerce_lookup_id` (:1232) and [write-values][write-values]
`::type_check_relation_id` (:151; function-local import dodging the
`relay -> utils.querysets` cycle). `type_check_relation_id` (1 def) is
called by `decode_visible_relation` (:219) and
`decode_visible_relation_ids` (:302); riders are the model single
(wraps `[value]`, :520) / model M2M (null-reject first, :555), the form
single (empty_values skip + to_field_name projection, :200) / form
multi (maps the single per element, :246-258 — needs the object), the
serializer single (None skip + obj.pk projection, :233) / serializer
multi (batched, :262); serializer nested routes RELATION_* through the
same pair (:340-341); downstream compose is `relation_into` /
`decode_field_handlers` / `decode_provided_fields`. `from_id` census: 2
production calls total — `decode_global_id`'s own (:751) + the filter's
(`filters/base.py:770`, the hardening family's site); zero in the write
path. `DecodeResult` is constructed only in the four arms (never
raised); OK is reachable only with non-None real pk (the two None
guards :324/:327); the `coerce_lookup_id` tail returns `result.pk` only
after excluding every non-OK status. `_resolve_real_pk` has 1 caller
(:326); live manager read per call, no cache. No second GlobalID->pk
body exists: the `filters/inputs.py`, `mutations/inputs.py`,
`mutations/sets.py`, `types/base.py` hits are input-shape declarations,
not decoders; no admin decoder exists. Population complete: model +
form + serializer + update/delete `id:` all ride the spine.

Change counts (authoritative definitions only): C1 new wire shape -> 1
(`decode_global_id` Steps + memberships); C2 fifth status -> 1
(taxonomy) + 2 mapper arms owed (:1233-1237, :152-154; the
`coerce_lookup_id` tail fall-through is a trigger, not a defect — no
such status exists); C3 label-vs-name -> 1 external (`decode_global_id`
Step 2 + `_accepts_*`, WRONG_MODEL identity arm orthogonal); C0 new
flavor -> 1 per stage. Precedent `e9c13f55` re-derived from its diff:
`decode_visible_relation_ids` added ONCE in `write_values.py`, model +
serializer riders switched to calls, the
`_coerce_relation_pk_or_none` alias deleted — a merge, not a copy.

Owner I would choose: [root-relay][root-relay]
`::decode_model_global_id` (principle 7: write-specific
decode+model-check+pk-coercion contract; every flavor depends on it
without reversing a dependency; taxonomy + NodeID map meaningless
outside it). Lifetime: not cached (principle 4). Same as W1.

### Reconciliation (W1 claims vs own trace)

1. Four defs 1-each — AGREE (re-censused). 2. `decode_global_id`
composed by name — AGREE. 3. Exactly 2 production callers — AGREE. 4.
Adapter shapes (incl. form-multi per-element vs serializer-multi
batched) — AGREE (all six decoder bodies opened). 5. Zero `from_id` in
write path — AGREE. 6. `DecodeResult` never raised / never
None-as-success — AGREE. 7. C1/C2/C3/C0 counts + `e9c13f55` merge +
tail-trigger note — AGREE. 8. Owner relay.py, live reads — AGREE. 9.
Sibling seams (difference+trigger+home each; hardening composes by
name) — AGREE. 10. No gate via Control B; Control A2 proves
non-vacuity — AGREE, with one DIFFERENCE on Control A (below). 11.
D1+D2 reproduced (all three stale refs opened: `relay.py:297`,
`forms/resolvers.py:30`, `test_resolvers.py:1165`; alias deletion
confirmed in the `e9c13f55` diff), prose-only non-blockers — AGREE. 12.
No pending execution; sharded/PG inapplicable (string/dict/enum +
default-DB single-alias lookups; alias passthrough covered by the
pinned-alias unit test) — AGREE. 13. relay.py +5 docstring-only,
AST-identity; resolvers dirt external (`_safe_class_name` hunks only,
zero decode overlap) — AGREE (AST check re-run True; ruff both green;
see below).

### Enumeration + matrix

`### Enumeration`: member-by-member confirmed against my census (defs,
2 callers, adapters listed-not-counted, parallel readers as seams,
oracles as named). `### Matrix`: all six axes discharged against the
real surface — cross-flavor (all three flavors + `id:` traced to the
spine), twins (sync-only, no async twin owed), derived knowledge (one
parse, one model-compare), round-trip (encode vs write-decode
specialization), media (oracles use independent literals; projections
verified except D1/D2), omission (every write `id` entry funnels
through the spine; no gap). No unsearched axis; no found consolidation
excusing one.

### Control A judgment (HARD): backstop real AND taxonomy unpinned

Mechanism re-traced (not inherited). Mutant: WRONG_MODEL arm returns
OK, pk stays None. Relation surface: OK+(None) returns `(None, None)`
as a success pk; downstream `visible_related_object(s)` with pk=None
matches no row -> the SAME `relation_field_error` — indistinguishable
BY CONSTRUCTION, so the serializer wrong-model row and the batched
wrong-model members stay green. Backstop REAL here: two layers, one
envelope. `id:` surface: OK+(None) falls through both mapper arms to
`(None, None)` SUCCESS -> `locate_instance(pk=None)` misses ->
NOT_FOUND ("No matching row found.") INSTEAD of INVALID ("Invalid
id."). The live update/delete wrong-type oracles assert field/`null`/
row-untouched only — all still hold — and the taxonomy level carries
zero WRONG_MODEL assertions package-wide. So the WRONG_MODEL arm is
UNPINNED at both levels while remaining SAFE (pk=None never coerces
cross-model; the dangerous same-pk-row case stays rejected; no leak).
W1's "defense-in-depth" is correct on safety, incomplete on contract
precision: the backstop masks the documented INVALID-vs-NOTFOUND
distinction rather than enforcing it. Owed item is an ORACLE (filed as
D3 above: test-only, blocks nothing), not a structural gate — Control
B stands (a correct copy still passes everything), and C2's counts are
unaffected (both mapper arms exist; one lacks a status-level pin).
Same card class as the run's definition-store D1 oracle-gap, which was
verified with the gap homed.

### Owner-edit, freshness, pending execution

Owner edit: `git diff ITEM_BASELINE --` the three family paths is
relay.py +5 docstring lines only (resolvers/write_values empty);
docstring-stripped AST of `HEAD:relay.py` vs worktree re-run
`AST-IDENTITY-NO-DOCSTRINGS: True`; `ruff format --check` +
`ruff check` on `relay.py` both green. Prose-only, behavior identical
— judgment: accept. Resolvers concurrent dirt (`_safe_class_name`
hunks) mapped, zero decode overlap, left untouched; no STOP arose.
Freshness: all 14 recorded blob ids re-hashed — every one matches
(`relay.py` `69085e7a`, `write_values.py` `d28587c7`,
`mutations/resolvers.py` `a322d17a`, `types/relay.py` `52439862`,
`filters/base.py` `ba52351c`, `forms/resolvers.py` `4edb984b`,
`rest_framework/resolvers.py` `8024703e`, `utils/querysets.py`
`96618fba`, `write_transaction.py` `eca9ad4d`, `testing/relay.py`
`df0dc72a`, `list_field.py` `ce682d5f`,
`test_relay_node_field.py` `2fd9e458`, `test_resolvers.py`
`c068aea1`, `test_write_values.py` `ac35ddd0`); HEAD still `bfaee91d`;
ITEM_BASELINE `2812607d` present. Nothing stale. `## Pending
execution` empty — judged correct: decode is wire validation and the
finding proposes no gate, so the final gate runs the standing oracles
(taxonomy 3 rows, coerce rows incl. parametrized non-GlobalID rejects,
type-check/batched/visibility rows, serializer wrong-model row, live
update/delete wrong-type `id:` + wrong-model/unresolvable relation
tiers) plus the owed-but-not-yet-existing D3 oracle via its owning
card. No `proof:` entries owed (W1's WS 20 + shared-tree 20 accepted
as recorded with `__file__` + DB NAME; my additions are static census).

### Verdict

`Status: verified`. CONFIRMED single-owned, zero moves; trigger clause
accepted; D1/D2/D3 homing owed at closeout (all projection/oracle,
block nothing).

Worker 0 rows (exact): tick `docs/dry/dry-0_0_15.md:564` (`typed-
globalid-decode` checkbox -> verified, Run 0.0.15 2026-09-19-1,
single-owned, docstring trigger only, no pending execution); index row
`:392` `open` -> verified (owner + member files unchanged); append
`## Owned changes`: `django_strawberry_framework/relay.py` — Family
`typed-globalid-decode` — `decode_model_global_id` docstring trigger
clause (projection; behavior untouched; AST-identity True re-verified
by Worker 2); home D1 + D2 + D3 (Worker 2) each on a NAMED owning card
at closeout; remove scratch
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/typed-globalid-decode-w1`
by explicit path after verified (still on disk, confirmed).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[form-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[list-field]: ../../django_strawberry_framework/list_field.py
[model-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[relay-types]: ../../django_strawberry_framework/types/relay.py
[root-relay]: ../../django_strawberry_framework/relay.py
[serializer-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[write-tx]: ../../django_strawberry_framework/utils/write_transaction.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
