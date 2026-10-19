# DRY review: `django_strawberry_framework/keyset.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a REUSED responsibility family (re-challenged fresh on
the keyset side, two as consumers, two as re-derived rejections) or a
file-local record with its proving challenge, plus three recorded
rejections. Zero production edits; zero tracked files changed.

## System trace

Fresh target (708 lines, 49 top-level statements, working blob identical
to HEAD and to the item baseline). The package's keyset (value-encoded)
stable-cursor surface, the BACKLOG `stable_cursor_field` contract. It
DEFINES the cursor vocabulary (`keyset.py::KEYSET_CURSOR_PREFIX`, the
`dstcursor` namespace against upstream `arrayconnection` and
strawberry-graphql-django `orderedcursor`), the order grammar
(`keyset.py::split_order_ref`,
`keyset.py::validate_cursor_field_references`), the declared-vocabulary
derivation (`keyset.py::CursorColumn`,
`keyset.py::DeclaredCursorState`,
`keyset.py::cursor_columns_for`,
`keyset.py::declared_cursor_state_for_definition`,
`keyset.py::order_fingerprint`), the finalization column contract
(`keyset.py::validate_cursor_field_columns`,
`keyset.py::_is_supported_cursor_field`), the value codec
(`keyset.py::serialize_cursor_value`,
`keyset.py::_deserialize_cursor_value`), the two error shapes
(`keyset.py::keyset_contract_error`,
`keyset.py::_invalid_cursor_error`), the crypto lifecycle
(`keyset.py::_cursor_crypto_types`, `keyset.py::_cursor_aessiv`,
`keyset.py::_encrypt_cursor_payload`,
`keyset.py::_decrypt_cursor_payload`), the codec round-trip pair
(`keyset.py::encode_keyset_cursor`,
`keyset.py::decode_keyset_cursor`), and the seek machinery
(`keyset.py::keyset_seek_greater`, `keyset.py::KeysetSeekPlan`,
`keyset.py::build_keyset_seek_plan`, `keyset.py::keyset_seek_q`,
`keyset.py::keyset_seek_sql`, `keyset.py::KeysetSeek`,
`keyset.py::KeysetCursor`). It CONSUMES by name the import guard
(`utils/imports.py::require_optional_module`), the base64 framing
(upstream `strawberry.relay.utils::to_base64` /
`from_base64`), the order-ladder entry point
(`optimizer/plans.py::effective_connection_order`, at the connection
consumer), and the captured-definition discipline (reads
`definition.model` / `definition.cursor_field`, never a fresh
registry read). It ENFORCES nothing outside its own decode/mint/seek
boundaries; every queryset it touches arrives already
visibility-scoped (the permission-aware-decode contract).

Connected code read for judgment, outside the item:
`django_strawberry_framework/connection.py` (import block,
`connection.py::_keyset_order_ref`,
`connection.py::_resolve_order_path_field`,
`connection.py::_keyset_order_state`, `connection.py::_KeysetPage`,
`connection.py::_resolve_keyset_connection`,
`connection.py::_finalize_queryset`,
`connection.py::_generate_connection_class` keyset-vocabulary lines,
`connection.py::_resolve_from_window` keyset legs at def-line depth);
`django_strawberry_framework/utils/connections.py` (full read:
`derive_keyset_window_bounds`, `assert_relay_pagination_bound`,
`resolve_relay_max_results`, `window_range_plan` `keyset_counted`
arm, `NEXT_PAGE_PROBE_ROWS`);
`django_strawberry_framework/types/base.py`
(`types/base.py::_validate_cursor_field` full body);
`django_strawberry_framework/types/finalizer.py` (keyset
finalization-half call site);
`django_strawberry_framework/types/definition.py` (`cursor_field`
slot docstring);
`django_strawberry_framework/optimizer/plans.py`
(`optimizer/plans.py::order_entry_name_and_direction`,
`optimizer/plans.py::order_entry_has_explicit_nulls`,
`optimizer/plans.py::ends_in_unique_column`,
`optimizer/plans.py::effective_connection_order`,
`optimizer/plans.py::deterministic_order`,
`optimizer/plans.py::apply_window_pagination` keyset-seek legs);
`django_strawberry_framework/optimizer/lateral_fetch.py`
(`optimizer/lateral_fetch.py::_keyset_seek_sql`,
`optimizer/lateral_fetch.py::_keyset_seek_quals_match` full bodies);
`django_strawberry_framework/optimizer/nested_planner.py`
(`optimizer/nested_planner.py::_keyset_window_slice_from_arguments`,
`_extend_only_projection`, `declared_cursor_state_for_definition`
call site);
`django_strawberry_framework/optimizer/nested_fetch.py` (module
docstring keyset-index paragraph, `keyset.KeysetSeek` mention
lines);
`django_strawberry_framework/utils/querysets.py`
(`utils/querysets.py::coerce_field_value_or_none`,
`utils/querysets.py::model_for` + `base_queryset` def lines,
`_seal_or_defect` policy-name lines only);
`django_strawberry_framework/utils/relations.py`
(`utils/relations.py::classify_path` + `relation_kind` def lines);
`django_strawberry_framework/relay.py`
(`relay.py::_coerce_pk_or_none` + `_node_id_slot` bodies);
`django_strawberry_framework/utils/write_values.py`
(`utils/write_values.py::coerce_relation_pk_or_none` body);
`django_strawberry_framework/utils/imports.py`
(`utils/imports.py::require_optional_module` full body);
`django_strawberry_framework/exceptions.py`
(`exceptions.py::describe_value` full body);
upstream `.venv` `strawberry/relay/utils.py` (`to_base64` /
`from_base64` bodies);
`tests/test_keyset.py` (module head + codec/bounds/SQL claim
titles);
`tests/test_keyset_connection.py` (module head + state/order
claim titles);
`examples/fakeshop/test_query/test_keyset_api.py` (module head
contract list);
BACKLOG `stable_cursor_field` entry + KANBAN keyset-cursor
decision bullet (pointers only, bodies not relied upon except to
avoid re-homing).

Excluded with reason: the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) - never touched, not in this finding's sites;
in-flight spec bodies (no owning spec exists for this surface -
the KANBAN decision bullet owns that question, not this item);
`docs/GLOSSARY.md` keyset passages (projections, not relied upon;
the missing-heading decision is the same KANBAN bullet);
`optimizer/walker.py` / `optimizer/extension.py` bodies beyond
the cited lines (planner-side window construction is the family
items' surface; this item traces the codec/seek side);
`auth/mutations.py` + `routers.py` disposal bodies (F-coerce
re-derivation needs only the querysets primitive's contract,
already indexed);
concurrent dirt (`django_strawberry_framework/connection.py`
working hunk, `tests/test_connection.py`,
`tests/utils/test_querysets.py` staged hunk,
`docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) - read where needed as oracles,
never edited, attribution unchanged.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Every sibling flavor was
checked for its own spelling of this file's rules. No list /
mutation / form / rest_framework / auth surface mints cursors,
fingerprints orders, derives seek predicates, or validates
`cursor_field`: the `cursor_field` literal outside this target
appears only at `types/base.py::_validate_cursor_field`
(stage-1 shape + gate, single consumer of
`validate_cursor_field_references`), `types/finalizer.py`
(stage-2 call site), `types/definition.py` (slot docstring),
`connection.py` + `optimizer/nested_planner.py` (codec/seek
consumers), and tests. The Relay global-ID codec
(`relay.py::_coerce_pk_or_none`) is a node-identity codec, not a
pagination cursor - different contract, no shared form (probe
`a5` single-def counts + `users()` census). The one genuine
second spelling found is the pre-existing F-coerce candidate
(rejected fresh); the two genuine near-misses are the path
resolver (F4, rejected) and the plans string parser (J1,
rejected).

**2. Sync/async twins.** The target holds zero `async def`,
zero `await`, zero `sync_to_async` (probe `a3-*`). Inapplicable
by construction, stated reason: every member is pure -
attribute reads off materialized rows (encode), authenticated
decryption + field coercion (decode), direction bits + `Q`
/ SQL-string rendering (seek). No ORM execution happens here
(no `.filter()` call, no `.count()` / `.acount()`, no
iteration), so there is no await point to color. The colored
halves live at the callers and already share these pure
decisions by name: `connection.py::_resolve_keyset_connection`
sync tail vs `_resolve_async` closure (both render
`KeysetSeek(...).q()`), the lateral fetcher (renders
`keyset_seek_sql` over `seek.plan(prepared)` inside its sync
recognizer). No twin owed.

**3. Derived rather than repeated knowledge.** Five facts this
file could have respelled are derived once from their owner:
the fingerprint from the order refs
(`keyset.py::order_fingerprint`, the sole `",".join(order_refs)`
package-wide - probe `a7`); the mint value source from the
field (`field.attname` in `cursor_columns_for`; the related-path
annotation alias is the connection consumer's per-query
derivation off the same `CursorColumn` record, not a second
rule); the plan from directions + values
(`keyset.py::build_keyset_seek_plan`, sole constructor besides
the dataclass literal it returns); the declared vocabulary
from the captured definition
(`keyset.py::declared_cursor_state_for_definition`, sole
`cursor_columns_for` + `order_fingerprint` composition);
the direction bit from `(descending, flip)`
(`keyset.py::keyset_seek_greater`, sole owner - the lateral
verifier reads `plan.greater`, never recomputes). No
reconstructed copy found.

**4. Inverse / round-trip pairs.** Four grammars, each with one
owner, all in this module: encode/decode (payload shape
`{"o", "v"}` spelled only here - probe `a9`; prefix framing
delegated to upstream `to_base64` / `from_base64`, never
re-spelled); serialize / `_deserialize` (field-authored
`value_to_string` / `to_python` with the re-serialization
equality gate); `keyset_seek_q` / `keyset_seek_sql` (two
renderers over the one `KeysetSeekPlan` - the uniform
row-value shortcut is a rendering optimization of the same
predicate: single-column `a > x` subsumes the redundant bound,
multi-column `(a,b) > (x,y)` is exactly the OR-expansion,
verified by reading both bodies); fingerprint mint/compare
(mint passes `fingerprint` in, decode compares
`payload.get("o") != fingerprint`). Keyset vs offset
vocabularies are mutually rejecting by prefix (`dstcursor` vs
`arrayconnection`), compared by contract in J2, never confused
silently.

**5. Contracts restated in another medium.** Four media carry
this file's contracts: production code (target); oracles that
spell expectations independently - `tests/test_keyset.py`
(codec internals, bounds arms, SQL shapes, forged-payload
matrix), `tests/test_keyset_connection.py` (class-cache slot,
order-state derivation, planner helpers),
`examples/fakeshop/test_query/test_keyset_api.py` (round-trip,
stability, tamper / offset / fingerprint rejection,
determinism, rotation, permission-aware replay) plus the
bound-error rows in `test_connection_pagination_api.py`;
projections (module + function docstrings, BACKLOG entry,
GLOSSARY passages). Every oracle checked pins behavior the
module could break (decoded tuples, SQL text, uniform error,
byte parity) rather than reading the owner. Intentional-change
media count: a payload-shape change moves the pair + the
forged-payload matrix + the live tamper rows (listed, never
counted in challenges). The BACKLOG future-tense wording and
the missing glossary heading / owning spec are the KANBAN
keyset-cursor decision bullet's surface - noted, not re-homed,
never counted.

**6. Enforcement by omission.** Three member-by-member checks.
(a) Declaration vs finalization: stage 1
(`types/base.py::_validate_cursor_field`) enforces shape
(non-empty non-string sequence), per-entry syntax + duplicate
columns (via the shared `validate_cursor_field_references`),
and the Relay-Node gate - and nothing column-level;
stage 2 (`keyset.py::validate_cursor_field_columns`)
enforces existence, local-concrete, non-nullable, JSON
exclusion, and terminal uniqueness - and re-runs the shared
reference check rather than re-spelling it. Each stage
enforces exactly what its inputs allow (settled fields exist
only at finalization); the generation-time derivation
(`declared_cursor_state_for_definition` at
`_generate_connection_class`) reuses the same syntax owner,
so no member accepts what another rejects.
(b) Query-time `orderBy:` seeks: anchorability + nullability
+ JSON enforced per effective entry at
`connection.py::_keyset_order_state` (composing
`_is_supported_cursor_field` + `keyset_contract_error` by
name); total-orderedness arrives via the shared
`optimizer/plans.py::effective_connection_order` ladder
(`deterministic_order` appends the pk tiebreak unless
`ends_in_unique_column`), which `_finalize_queryset` applies
BEFORE `_keyset_order_state` reads `query.order_by` - so the
per-query columns inherit the unique terminal, including
the related-path annotation shape. No unguarded member.
(c) Cursor-shape coverage: `before:` is decoded AND validated
at plan time (`_keyset_window_slice_from_arguments`) but its
seek is dropped for the forward-only window (raises
`UnwindowableConnection` for backward shapes) while the
root slicer applies it with `flip=True` - the two postures
are the planned-vs-per-parent contract, both reject
malformed cursors at their own locality. No member lacks a
guard its contract requires; no defect.

### Enumeration

Instrument: `ast.parse` over the working-tree blob, counting
`ast.Module.body` members - **49 top-level statements**
(working == HEAD == item baseline). Every member lands below;
every challenge in `### Challenges` ends in a family row, a
file-local record, or a recorded rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (surface contract) | (none) | projection |
| 1-17 | imports: future, base64, binascii, Sequence, dataclass, cache+lru_cache, SimpleNamespace, Any, settings, signing, FieldDoesNotExist+ValidationError, models, salted_hmac, GraphQLError, from_base64+to_base64, ConfigurationError, require_optional_module | machinery names | machinery (consumers: R3/R5 via ConfigurationError; R9 via settings/signing/salted_hmac/require_optional_module; R10 via from_base64/to_base64; R7/R8 via GraphQLError) |
| 18 | `KEYSET_CURSOR_PREFIX = "dstcursor"` | prefix literal | R1 |
| 19 | `_CURSOR_ENCRYPTION_SALT` | KDF salt | R9 |
| 20 | `_CURSOR_ENCRYPTION_CONTEXT` | AD bytes | R9 |
| 21 | `_CRYPTOGRAPHY_INSTALL_HINT` | soft-dep hint | R9 |
| 22 | `class CursorColumn` | column record | R4 |
| 23 | `class KeysetCursor` | decoded values | R10 |
| 24 | `class KeysetSeek` (+ `q`, `plan`) | seek carrier | R12 |
| 25 | `def order_fingerprint` | order grammar hash | R2 |
| 26 | `def split_order_ref` | ref syntax | R3 (+ J1) |
| 27 | `def validate_cursor_field_references` | ref sequence | R3 |
| 28 | `def _resolve_cursor_field_column` | local resolve | R13 (+ F4) |
| 29 | `def cursor_columns_for` | column specs | R4 |
| 30 | `class DeclaredCursorState` | declared vocab | R4 |
| 31 | `def declared_cursor_state_for_definition` | vocab derivation | R4 (+ F1) |
| 32 | `def validate_cursor_field_columns` | column contract | R5 |
| 33 | `def serialize_cursor_value` | value encode | R6 (+ F3) |
| 34 | `def _deserialize_cursor_value` | value decode | R6 (+ F3) |
| 35 | `def keyset_contract_error` | contract stem | R7 |
| 36 | `def _invalid_cursor_error` | invalid shape | R8 |
| 37 | `def _is_supported_cursor_field` | JSON predicate | R5 |
| 38 | `def _cursor_crypto_types` | soft-dep load | R9 |
| 39 | `def _cursor_aessiv` | primitive cache | R9 |
| 40 | `def _encrypt_cursor_payload` | payload seal | R9/R10 |
| 41 | `def _decrypt_cursor_payload` | payload open | R9/R10 |
| 42 | `def encode_keyset_cursor` | mint | R10 |
| 43 | `def decode_keyset_cursor` | verify+decode | R10 |
| 44 | `def keyset_seek_greater` | direction bit | R11 |
| 45 | `class KeysetSeekPlan` (+ `__post_init__`, `uniform`, `lead_greater`) | plan record | R12 |
| 46 | `def build_keyset_seek_plan` | plan builder | R12 |
| 47 | `def keyset_seek_q` | ORM renderer | R12 |
| 48 | `def keyset_seek_sql` | SQL renderer | R12 |

Rules: F1-F4 reuse the plan's existing family names (no new
family named); R1-R13 are file-local; J1-J3 are recorded
rejections. The plan's `## Responsibility index` already
carries `field-value-coercion` (rejected),
`orm-lookup-path-resolution` (open),
`queryset-seed-and-model-read` (open), and
`sealed-execution-queryset` (open) with the roles below -
reused, not renamed.

### Challenges

Each change posited against the rule's own variation axes; the
count is authoritative definitions only. Consumers, oracles,
projections listed, never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R2 fingerprint | fingerprint grammar gains a version tag | **1** (`order_fingerprint`; state + both codec params follow as consumers) | file-local |
| C2 | R3 syntax | a new order-ref prefix ships | **1** (`split_order_ref`; both validation stages follow) | file-local |
| C3 | R3 duplicates | duplicate detection must ignore direction | **1** (`validate_cursor_field_references`) | file-local |
| C4 | R5 columns | a new backend-divergent column kind joins JSONField | **1** (`_is_supported_cursor_field`; the finalizer + `_keyset_order_state` follow as consumers) | file-local |
| C5 | R5 terminal | terminal may be a non-unique index with a hidden tiebreak | **1** (`validate_cursor_field_columns`; BACKLOG "tiebreak DECLARED" prose moves with it) | file-local |
| C6 | R6 codec | cursor decode must run field validators | **refused** (would add rejection to a round-trip gate / drop the loud raise - F3) | rejection |
| C7 | R7 stem | reword the shared keyset stem | **1** (`keyset_contract_error`; the five detail sites + oracles move) | file-local |
| C8 | R8 shape | distinguish tampered vs stale-order cursors | **1** (`_invalid_cursor_error`; deliberately uniform today - oracle-detail discipline) | file-local |
| C9 | R9 crypto | key derivation switches salt | **1** (`_cursor_aessiv`; seal/open follow) | file-local |
| C10 | R10 payload | payload gains a third key | **1 owner** (encode + decode move together, one module) | file-local |
| C11 | R11 direction | `before:` seeks invert differently | **1** (`keyset_seek_greater`; plan + both renderers + lateral verifier follow) | file-local |
| C12 | R12 structure | drop the redundant leading bound | **1 owner** (q + sql move together; the SQL-shape oracles + `_keyset_seek_quals_match` move) | file-local |
| C13 | R13 resolve | route local resolution through `classify_path` | **refused** (declaration-local loud vs full-classifier contract - F4) | rejection |
| C14 | R3 parse | route ref parsing through the plans parser | **refused** (loud ConfigurationError vs fallback `None` + dash handling - J1) | rejection |
| C15 | keyset/offset | unify the two pagination forks | **refused** (value-seek vs positional-slice contracts - J2) | rejection |
| C16 | R1 prefix | namespace gains a version suffix | **1** (`KEYSET_CURSOR_PREFIX`; decode comparison follows) | file-local |
| C17 | R4 vocab | vocabulary keyed per field instead of per definition | **1** (`declared_cursor_state_for_definition`) | file-local |
| C18 | F2 seal | a new untrusted queryset shape must be rebuilt | **1** (the seal; the seek application follows as consumer) | consumer |
| C19 | F1 seed | default seed must pin a new routing fact | **1** (`utils/querysets.py::base_queryset`; the definition read follows) | consumer |

**Experiment.** Read-only probe (no source mutation, no SQL,
no Django setup, no shared-tree pytest - the workspace recipe
is for mutating proofs, of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-keyset/probe_w1.py
```

Output (`ALL OK`, 60 checks): 49-member AST (17 imports /
4 constants / 5 classes / 22 functions + docstring);
carrier method census (`KeysetSeek::{q,plan}`,
`KeysetSeekPlan::{__post_init__,uniform,lead_greater}`,
others method-free); zero async surface; zero queryset
construction; 19 single-definition counts (every public
keyset name + `coerce_field_value_or_none` +
`classify_path` + `_resolve_order_path_field` +
`order_entry_name_and_direction`); prefix defined once;
fingerprint join once; payload keys single-module; decode
raises funnel exclusively via `_invalid_cursor_error`;
consumer census per public name; `require_optional_module`
consumer role; item-baseline diff empty. Status:
`execution-verified` for every identity/count/shape/absence
claim below. Rejects the wrong results "a second definition
lives here", "the target drifted from its baseline", "decode
raises a second error shape".

## Findings

No production edit is owed by a file item; the four families
below are REUSED from the plan (keyset-side roles
re-challenged fresh), the rest are file-local records and
three recorded rejections.

### F1 - queryset seed and model read (existing family `queryset-seed-and-model-read`, stays `open`)

- **Contract + variation.** A surface seeds its default
  queryset from the relation's target model on the right
  connection and reads the model off the ONE
  construction-time definition, so seed and seal cannot be
  answered from two different reads.
- **Sites + roles.** *Definitions*: per the plan index,
  `utils/querysets.py::model_for` (single `_meta` read) +
  `utils/querysets.py::base_queryset` (seed with `using`
  arm) - owner side, bodies not re-read here beyond the def
  lines already traced by the connection item. *Consumer
  here*: `keyset.py::declared_cursor_state_for_definition`
  reads `definition.cursor_field` and `definition.model`
  (via `cursor_columns_for`) off the factory's captured
  definition - the same captured-read discipline the
  connection item records as J2: no per-read re-validation,
  no fresh registry lookup (probe `users()` census shows no
  `model_for` call in this file).
- **Challenges.** C19 - 1 at the seed; zero definitions
  here.
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No
  stored derivation here (the `DeclaredCursorState` is
  derived per generation call from the handed-down
  definition, then frozen on the connection class).
- **Migration.** None (zero-edit item; consumer role only).
- **Distinct behavior.** The definition-keying (docstring:
  "DEFINITION-keyed because every caller holds a captured
  definition") stays here - which vocabulary object anchors
  the derivation is this module's genuine decision; the
  model-read mechanics stay at the owner.
- **Behavioral proof.** `static-reviewed` for the consumer
  role (derivation body + `_generate_connection_class`
  capture lines read); `execution-verified` for the census.
  Rejects "this file re-reads the type registry".
- **Structural gate.** The default-field oracles (an
  unseedable model fails at field construction) plus the
  class-cache identity rows in
  `tests/test_keyset_connection.py` (the state object is
  the class-fixed one). Negative control: a derivation
  reading a fresh registry definition passes every
  happy-path oracle and breaks only under a stateful
  definition - which is why the captured read matters.
- **Coupling.** None.
- **Freshness.** Target `df4b5e2f...` + `utils/querysets.py`
  `1539b66c...` (def lines only) + `connection.py` HEAD
  `93e998f2...` (capture lines only) +
  `tests/test_keyset_connection.py` `eb5c4720...`.

### F2 - sealed-execution queryset (existing family `sealed-execution-queryset`, stays `open`)

- **Contract + variation.** A consumer-supplied or
  hook-returned queryset is untrusted state: validated and
  rebuilt by the seal; the keyset seek is always applied to
  the ALREADY-visibility-scoped queryset, so a cursor minted
  under one viewer replays under another's without leaking
  rows.
- **Sites + roles.** This file holds NO definition and
  performs NO sealing: it builds pure `Q` / SQL-string
  predicates and pure byte payloads. *Consumer discipline*:
  the module docstring's permission-aware-decode paragraph
  states the ordering (pipeline scopes first, seek second);
  `connection.py::_resolve_keyset_connection` and the
  plan-time window enforce it. Package-wide mechanism sweep
  for the seal's construction vocabulary
  (`models.QuerySet(...)`, `sql.Query`) was already run by
  the querysets item (one definition); this item
  re-confirms no such construction exists here (probe
  `a4-*` + full read).
- **Challenges.** C18 - 1 at the seal; zero definitions
  here.
- **Owner + lifetime.** `utils/querysets.py::_seal_or_defect`
  (unchanged). No stored derivation here.
- **Migration.** None.
- **Distinct behavior.** Nothing here rebuilds a queryset
  from state; the seek is a planning question rendered as a
  predicate, applied by the caller to its sealed object.
- **Behavioral proof.** `static-reviewed` (full target
  read); `execution-verified` for the census.
- **Structural gate.** The permission-aware replay rows in
  `test_keyset_api.py` (staff-minted cursor replays for an
  anonymous viewer over only visible rows). Negative
  control: applying the seek before visibility passes every
  oracle except those rows.
- **Coupling.** None.
- **Freshness.** Target `df4b5e2f...` + `utils/querysets.py`
  `1539b66c...` (policy names only) + `test_keyset_api.py`
  `a5e1fbdf...` (live rows cited, bodies not relied upon).

### F3 - REJECTED: cursor decode is not a second field-value coercion

- **Shared form considered.** Routing
  `keyset.py::_deserialize_cursor_value` through
  `utils/querysets.py::coerce_field_value_or_none`
  (replacing `field.to_python` + re-serialization gate with
  `to_python` + `run_validators`, `None` on failure).
- **Contract difference.** Three axes, all load-bearing.
  (1) Failure posture: coercion returns `None` ("identifies
  no row", dropped from a query); decode raises the uniform
  `_invalid_cursor_error` `GraphQLError` (an opaque cursor
  that fails its own round-trip is malformed input, never a
  missing row). (2) Validators: coercion range-checks
  (out-of-range pk must not reach a backend `OverflowError`);
  decode re-serializes and compares equality instead - the
  values ride as bind parameters into comparisons, never
  into `pk__in`, and the gate's job is detecting
  model-field drift between mint and decode, which
  validators cannot see. (3) `None`: coercion maps invalid
  to `None`; here `None` is rejected BEFORE the field codec
  (Char/Text `value_to_string(None)` mints the literal
  `"None"`, colliding with a real row of that title) at
  both `serialize_cursor_value` and `encode_keyset_cursor`.
  Merging would either soften a tamper signal into a
  missing row or add validator rejection to an equality
  test. Re-derived fresh from both bodies, not inherited
  from the querysets F6 record (which names this exact
  call as "a third contract").
- **Reconsideration trigger.** If cursor decode ever needs
  validator/out-of-range rejection (a decoded value
  reaching a backend adapter that can raise `OverflowError`
  outside a comparison) - then the two collapse into one
  rule. Grep decode's value flow for a non-comparison sink.
- **Durable home.** `keyset.py::_deserialize_cursor_value`
  docstring neighborhood (already states the drift-detection
  purpose) + this finding; the family item keeps
  `field-value-coercion` rejected.
- **Owner + lifetime.** `utils/querysets.py` keeps the
  primitive (unchanged); this module keeps its gate. No
  stored derivation.
- **Migration.** None.
- **Behavioral proof.** `static-reviewed` (both bodies +
  the three consumer call sites' contracts read).
- **Structural gate.** The forged-payload rejection matrix
  in `tests/test_keyset.py` (non-canonical values raise
  rather than coerce) plus the literal-`"None"` title seek
  row. A substitution passes the matrix's shape rows and
  fails the drift/canonical rows.
- **Coupling.** None.
- **Freshness.** Target `df4b5e2f...` + `utils/querysets.py`
  `1539b66c...` + `relay.py` `c3c5aea5...` +
  `utils/write_values.py` `d28587c7...` (consumer
  contracts, def lines only).

### F4 - REJECTED: the local column resolver is not a member of the lookup-path family

- **Shared form considered.** Routing
  `keyset.py::_resolve_cursor_field_column` (pk-alias +
  `get_field`, loud `FieldDoesNotExist`) through
  `utils/relations.py::classify_path` (the
  `orm-lookup-path-resolution` owner), or unifying it with
  `connection.py::_resolve_order_path_field`.
- **Contract difference.** Three different jobs.
  `classify_path` classifies arbitrary `__`-traversing
  lookup paths (relation kinds, to-many, transforms). The
  connection member resolves possibly-`__` order paths
  fail-SOFT (`None`) for per-query effective orders where a
  related path is legal (annotated onto rows). This
  module's resolver takes a bare local name, honors the
  `pk` alias, and lets `FieldDoesNotExist` propagate -
  because declaration columns must be LOCAL (any `__` is
  rejected one step earlier in `split_order_ref` with a
  `ConfigurationError`), and at declaration time an
  unresolvable name is a configuration error, not a
  per-request fallback. Unifying would either teach the
  declaration path to return `None` for typos (fail-open
  at schema build) or teach the query path to raise for
  expressions it must decline softly. Re-derived fresh
  from all three bodies, not inherited.
- **Reconsideration trigger.** If `cursor_field` ever
  allows related paths (the annotation machinery in
  `_keyset_order_state` promoted to declarations) - then
  this resolver and the connection member become one rule.
- **Durable home.** `keyset.py::_resolve_cursor_field_column`
  docstring neighborhood + this finding; the family item
  keeps `orm-lookup-path-resolution` open without this
  member.
- **Owner + lifetime.** `utils/relations.py::classify_path`
  (unchanged). No stored derivation.
- **Migration.** None.
- **Behavioral proof.** `static-reviewed` (all three
  bodies + both callers read).
- **Structural gate.** The finalization-shape oracles in
  `tests/test_keyset.py` (unknown/related/duplicate
  entries raise `ConfigurationError`) vs the order-state
  oracles in `tests/test_keyset_connection.py`
  (expression / nulls / nullable / JSON / multi-valued
  reject with `keyset_contract_error`, related required-FK
  paths accepted). A substitution swaps which entries
  raise where.
- **Coupling.** None.
- **Freshness.** Target `df4b5e2f...` +
  `utils/relations.py` `7662b0bb...` + `connection.py`
  HEAD `93e998f2...` (member body read).

### File-local records (no second definition after the matrix)

- **R1 - keyset cursor namespace.** `KEYSET_CURSOR_PREFIX =
  "dstcursor"` (C16 - 1). The package-owned third vocabulary
  beside upstream `arrayconnection` (offset) and
  strawberry-graphql-django `orderedcursor`: a cursor minted
  under one prefix is rejected by the others without
  decrypting (decode compares prefix first). No package
  second spelling (probe `a6`). Trigger: a fourth cursor
  vocabulary. Freshness: target + `tests/test_keyset.py`
  `0f742b6d...`.
- **R2 - order fingerprint.** `order_fingerprint` (C1 - 1).
  Plain comma join kept human-readable INSIDE the
  authenticated-encrypted payload; decode compares against
  the live effective order and rejects replay under a
  different `orderBy:`. Sole join site (probe `a7`).
  Trigger: a second order-identity scheme. Freshness:
  target + `tests/test_keyset_connection.py`
  `eb5c4720...`.
- **R3 - order-ref syntax.** `split_order_ref` +
  `validate_cursor_field_references` (C2, C3 - 1 each). The
  single syntax owner for BOTH validation stages (class
  creation via `types/base.py`, finalization via
  `validate_cursor_field_columns`): one optional leading
  `-`, local name only, no `__`, no duplicates, non-empty.
  Malformed here is always a loud `ConfigurationError`,
  never a fallback signal - the J1 twin records why the
  plans parser stays separate. Trigger: a second
  declaration surface parsing order refs. Freshness: target
  + `types/base.py` `91c58747...`.
- **R4 - declared-vocabulary derivation.**
  `CursorColumn`, `DeclaredCursorState`,
  `cursor_columns_for`,
  `declared_cursor_state_for_definition` (C17 - 1). The one
  derivation from captured definition to mint/decode
  vocabulary (columns + fingerprint), fixing the
  cross-strategy byte-parity invariant by construction:
  class generation, plan-time decode, and resolve-time
  mint all read the same object. The connection's
  per-query `CursorColumn` construction for `orderBy:`
  paths builds the same RECORD (owned here) for a different
  input (effective order, annotated value sources) - a
  second construction site of one record, not a second
  rule. Trigger: a second vocabulary derivation.
  Freshness: target + `connection.py` HEAD `93e998f2...`
  + `optimizer/nested_planner.py` `0ad8ff5d...`.
- **R5 - finalization column contract.**
  `validate_cursor_field_columns` +
  `_is_supported_cursor_field` (C4, C5 - 1 each). The v1
  column rules: local concrete non-nullable, JSON excluded
  (backend-divergent ordering), terminal unique
  (total-order anchor, tiebreak DECLARED not appended).
  Single predicate for the JSON rule, composed by name at
  the connection's query-time check (one def, two
  enforcement sites, one owner). The nullable-terminal
  question is closed by the per-entry null check running
  before the terminal check (matches
  `ends_in_unique_column`'s nullable exclusion).
  Trigger: a second column-contract enforcement.
  Freshness: target + `types/finalizer.py`
  `77fd9a2d...` + `tests/test_keyset.py`
  `0f742b6d...`.
- **R6 - value codec.** `serialize_cursor_value` +
  `_deserialize_cursor_value`. Field-authored round-trip
  surface (`value_to_string` / `to_python` + re-serialize
  equality gate); comparison happens only in the database
  as bind parameters, so collation governs string ordering,
  never Python. F3 records why the shared coercion
  primitive stays separate. Trigger: a second value-wire
  shape. Freshness: target + `tests/test_keyset.py`
  `0f742b6d...`.
- **R7 - contract-error stem.** `keyset_contract_error`
  (C7 - 1). The shared stem ("this connection uses keyset
  cursors...") single-sited after being re-typed at five
  sites across two modules; the per-site detail stays at
  its site. `exceptions.py::describe_value` considered and
  refused: that helper renders hostile/deployment values
  that must never break formatting; the values
  interpolated here (`column.value_source`, order names)
  are package-owned strings, never hostile input - a
  different contract, not a second tail. Trigger: a sixth
  keyset-contract site. Freshness: target +
  `exceptions.py` `e06b0b7f...` (considered, def lines).
- **R8 - invalid-cursor shape.** `_invalid_cursor_error`
  (C8 - 1). Every decode rejection - non-base64, foreign
  prefix, bad ciphertext, fingerprint mismatch, arity or
  shape mismatch - funnels through this one uniform
  `GraphQLError` (probe `a13`: decode's raises are exactly
  this one), deliberately leaking no oracle detail.
  Trigger: a second malformed-cursor shape. Freshness:
  target + `tests/test_keyset.py` `0f742b6d...` +
  `test_keyset_api.py` `a5e1fbdf...`.
- **R9 - crypto lifecycle.** `_cursor_crypto_types`,
  `_cursor_aessiv`, `_encrypt_cursor_payload`,
  `_decrypt_cursor_payload` + the salt / context / hint
  constants (C9 - 1). AES-SIV deterministic
  misuse-resistant seal over `SECRET_KEY` (fallbacks tried
  on decrypt, so rotation keeps live cursors valid);
  `cryptography` imported ONLY at mint/decode via the
  shared `require_optional_module` (consumer role - probe
  `a11`; fixtures mint and round-trip, never pin bytes).
  Trigger: a second cursor-seal mechanism. Freshness:
  target + `utils/imports.py` `291ecedd...` +
  `tests/test_keyset.py` `0f742b6d...`.
- **R10 - codec round-trip pair.** `KeysetCursor`,
  `encode_keyset_cursor`, `decode_keyset_cursor` (C10 - 1
  owner). Payload `{"o": fingerprint, "v": [serialized
  values]}` sealed then base64-wrapped under the prefix;
  `None` ordering values rejected loudly at both
  `serialize` and mint (the `"None"`-collision discipline).
  Both halves in one module sharing prefix, fingerprint,
  and value codec by name. Trigger: a second cursor
  payload grammar. Freshness: target +
  `tests/test_keyset.py` `0f742b6d...` +
  `test_keyset_api.py` `a5e1fbdf...`.
- **R11 - direction rule.** `keyset_seek_greater` (C11 -
  1). The single direction bit every seek dialect renders
  from (ascending seeks greater forward; descending flips;
  `before:` flips again) - shared by the plan builder and
  the lateral structural verifier, so the two dialects can
  never seek opposite sides. Trigger: a third seek
  polarity. Freshness: target +
  `optimizer/lateral_fetch.py` `db1ea315...`.
- **R12 - seek plan and its two renderers.** `KeysetSeek`
  (+ `q` / `plan`), `KeysetSeekPlan` (+ `__post_init__`
  arity guard, `uniform`, `lead_greater`),
  `build_keyset_seek_plan`, `keyset_seek_q`,
  `keyset_seek_sql` (C12 - 1 owner). The dialect-agnostic
  predicate (directions + values) with the redundant
  leading inclusive bound (index ACCESS, not filter);
  portable `Q` for the windowed floor, parameterized SQL
  for the lateral branch; the lateral adapter
  (`_keyset_seek_sql`: prepares values through
  `get_db_prep_value`, quotes refs, calls `seek.plan`)
  and the fetch-time verifier
  (`_keyset_seek_quals_match`: checks the exact `Q`-tree
  against the shared plan) both compose the plan by name
  rather than re-deriving directions. Trigger: a third
  seek dialect. Freshness: target +
  `optimizer/lateral_fetch.py` `db1ea315...` +
  `optimizer/plans.py` `cce98531...` +
  `tests/test_keyset.py` `0f742b6d...`.
- **R13 - local column resolver.**
  `_resolve_cursor_field_column`. The `pk`-aliasing
  `get_field` read for declaration columns. F4 records why
  the lookup-path family stays separate. Trigger: a second
  declaration-column resolver. Freshness: target (F4
  fingerprints apply).

### J1 - ref syntax vs plans entry parser (rejection, not a family)

`keyset.py::split_order_ref` (declaration strings: one
optional `-`, local only, malformed = loud
`ConfigurationError`) vs
`optimizer/plans.py::order_entry_name_and_direction`
(query-time entries: strings AND `OrderBy`/`F`
expressions, unresolvable = fallback `None`). Considered
shared form: one order-string parser. Contract difference:
loud vs fallback is the whole point (a malformed
declaration must fail the build; an unanchorable effective
entry must decline softly so the consumer names the
keyset boundary), and the dash handling differs
(`"--name"` rejected here, parsed as field `"-name"` there
- read both bodies). The docstring already records the
twinship and the separation. Reconsideration trigger: the
keyset path ever needs to parse expressions, or the plans
parser ever needs to raise. Durable home: the
`split_order_ref` docstring + this finding (a file item
lands no edit).

### J2 - keyset vs offset pagination (rejection, not a family)

The value-seek fork (`derive_keyset_window_bounds`,
`_resolve_keyset_connection`, the seek predicates) vs the
positional-slice path (`derive_connection_window_bounds`
via `SliceMetadata`, `ListConnection`). Considered shared
form: one pagination engine. Contract difference:
positioning by tuple-comparison seek (insert/delete-safe,
index access, forward-only, total-order required) vs
positioning by row-number offset (bidirectional,
stable only under a deterministic order, numbering-and-
discarding). What IS shared is shared by name, not
re-spelled: `assert_relay_pagination_bound` (one
first/last bound check, exact `SliceMetadata` error text),
`resolve_relay_max_results` (one cap ladder),
`is_backward_shape` (one backward core),
`NEXT_PAGE_PROBE_ROWS` (one sentinel count). The v1
backward-keyset gap (`last` / `before:` fall back
per-parent) is the BACKLOG `backward_nested_keyset_pagination`
surface, not drift. Reconsideration trigger: a third
positioning domain, or offset cursors gaining value
semantics. Durable home: `utils/connections.py`
`derive_keyset_window_bounds` docstring (already states the
twinship) + this finding.

### J3 - two-stage declaration validation (intentional separation, not duplication)

`types/base.py::_validate_cursor_field` (class-creation:
shape, syntax, duplicates, Relay-Node gate) vs
`keyset.py::validate_cursor_field_columns` (finalization:
existence, concreteness, nullability, JSON, terminal
uniqueness). Considered shared form: one validator.
Not duplication: each stage enforces what its inputs allow
(the settled field surface exists only at finalization),
and the shared sub-rule (reference syntax + duplicates)
already routes through the one
`validate_cursor_field_references`. Both owners document
the split (base docstring names the finalization half;
finalizer comment names the phase window). Reconsideration
trigger: a validation input available at both stages that
is checked twice with two spellings. Durable home: both
owners' prose + this finding.

## Defects

None. Every claim checked while tracing held: the 19
single-definition counts; the prefix defined once; the
fingerprint join once; the payload keys single-module; the
decode raise funnel; the Q/SQL predicate equivalence
(single-column subsumption, multi-column row-value
identity); the terminal-unique closure (per-entry null
check precedes the terminal check); the orderBy total-order
chain (finalize applies `effective_connection_order` with
its pk tiebreak BEFORE `_keyset_order_state` reads
`query.order_by`); the captured-read discipline (no
`model_for`, no registry read); the seal non-ownership (no
queryset construction); the colorless surface (no async
tokens). The two known keyset-adjacent doc debts keep
their existing home and are NOT re-homed here: the BACKLOG
`stable_cursor_field` future-tense wording and the missing
glossary heading / owning spec are the KANBAN
keyset-cursor decision bullet's surface (measured there with
its own populations), and this item's oracles confirm the
shipped behavior they describe.

## Pending execution

None. The execution proof (read-only probe driving the AST
plus the whole-tree sweeps, command in `### Challenges`)
already ran green against the shared tree; it mutates no
source and opens no database, so no workspace copy was
owed and no `__file__`/DB `NAME` record applies. No pytest
was run in the shared tree, per item rules; oracle bodies
are `static-reviewed`. No `execution-deferred` items. No
`FAKESHOP_SHARDED` or Postgres cell is owed: this
artifact's claims (statement counts, import census,
absence/single-site facts, baseline diff) touch no
database, alias, or dialect decision (`inapplicable by
construction` - the target reaches no database and the
lateral SQL text it renders is pinned by package-side
oracles that run on SQLite).

## Judgment

Zero-edit file item discharged: matrix run against the real
surface on all six axes, 49/49 members enumerated and
homed, 19 challenges with authoritative-definition counts,
four existing families reused (two consumers, two
re-derived rejections), thirteen file-local records, three
rejections with contract differences + triggers + homes, no
defect, no pending execution. No consolidation owed; no new
family named. Worker 0 note: rejections F3/F4/J1/J2 (and
the J3 separation) carry their durable homes above; the
plan index rows for `field-value-coercion` (rejected) and
`orm-lookup-path-resolution` (open) need no status change
on this item's account.

## Implementation (Worker 1)

No production edits (item forbids them): no tracked file
created, modified, or deleted by this worker. Deliverables
are the artifact itself (untracked until Worker 0 files it)
and the read-only probe below. No ruff run owed (no `.py`
edits outside untracked scratch; the probe formats clean
by construction - single quotes untouched, line length
within bounds).

- Item-scoped diff: `git diff
  f3c0c440d03d12f32613d6656e77f5f8749562fe --
  django_strawberry_framework/keyset.py` empty (probe
  `a12`); `git status --short --
  django_strawberry_framework/keyset.py
  docs/dry/dry-file-keyset.md` shows only the artifact as
  untracked. Concurrent dirt (`connection.py` hunk,
  `tests/test_connection.py`, staged
  `tests/utils/test_querysets.py` +31,
  `docs/bug_hunt/bug_hunt-0_0_15.md`,
  `docs/dry/dry-0_0_15.md`) read where needed as oracles,
  never touched; the `connection.py` working/HEAD split
  (`3c4d5dcb...` / `93e998f2...`) touches none of this
  item's fingerprinted keyset sites (the hunk is the
  offset negative-cursor guard + fallback-branch lines,
  attributed by content).
- Scratch: `docs/dry/temp-tests/dry-file-keyset/probe_w1.py`
  (`ALL OK`, 60 checks; rerun verbatim to reproduce).
  No workspace copy created (no mutating proof owed). No
  shared-tree pytest run.

## Independent verification (Worker 2)

Own trace, re-derived with an independent probe plus body reads
(no shared-tree pytest; read-only scratch
`docs/dry/temp-tests/dry-file-keyset-w2/probe_w2.py`, `ALL OK`,
35 checks; rerun verbatim to reproduce). Counts are authoritative
definitions only; consumers, oracles, projections listed, never
counted.

- Prefix vocab: `keyset.py::KEYSET_CURSOR_PREFIX` (`"dstcursor"`)
  is the sole package definition; decode compares it first and
  rejects foreign prefixes without decrypting. Owner: `keyset.py`.
- Order fingerprint: `keyset.py::order_fingerprint` is the sole
  `",".join(order_refs)` package-wide; mint takes `fingerprint`
  in, decode compares `payload.get("o")` against it. Owner:
  `keyset.py`.
- Ref syntax, both stages: `keyset.py::split_order_ref` (one
  optional `-`, local only, `__` rejected, `"--name"` loud) plus
  `keyset.py::validate_cursor_field_references` (non-empty,
  no-duplicate sequence) serve stage 1
  (`types/base.py::_validate_cursor_field`) and stage 2
  (`keyset.py::validate_cursor_field_columns`) by name. Owner:
  `keyset.py`.
- Declared-vocab derivation:
  `keyset.py::declared_cursor_state_for_definition` is the sole
  `cursor_columns_for` + `order_fingerprint` composition, keyed
  by the captured definition (`definition.model` /
  `definition.cursor_field`); no `model_for` call and no
  registry read in this file. Derivation owner: `keyset.py`;
  seed mechanics stay at `utils/querysets.py::base_queryset`.
- Finalization column + null check:
  `keyset.py::validate_cursor_field_columns` (local concrete,
  non-nullable, JSON excluded via
  `keyset.py::_is_supported_cursor_field`, terminal unique)
  with the per-entry null check running before the terminal
  check. Query-time `orderBy:` entries are enforced per
  effective column at `connection.py::_keyset_order_state`
  composing the same predicate by name; total-orderedness
  arrives via `optimizer/plans.py::effective_connection_order`
  applied in `connection.py::_finalize_queryset` before the
  order state reads `query.order_by`. Owner: `keyset.py`.
- Value codec: `keyset.py::serialize_cursor_value`
  (`value_to_string` over an attname shim, `None` rejected
  before the field codec) plus
  `keyset.py::_deserialize_cursor_value` (`to_python` with the
  re-serialization equality gate). Coercion-rejected: the
  shared `utils/querysets.py::coerce_field_value_or_none`
  (`to_python` + `run_validators`, `None` on failure) differs
  on three axes - raise vs `None`, drift gate vs validators,
  `None` rejected before the codec. Owner of the gate:
  `keyset.py`.
- Error stem: `keyset.py::keyset_contract_error` is the single
  stem with five detail sites (one here, four in
  `connection.py`). `exceptions.py::describe_value` refused:
  interpolated values here are package-owned strings, never
  hostile input. Owner: `keyset.py`.
- Invalid-cursor funnel: every raise inside
  `keyset.py::decode_keyset_cursor` is exactly
  `keyset.py::_invalid_cursor_error` (non-base64, foreign
  prefix, bad ciphertext, fingerprint mismatch, arity/shape
  mismatch). Owner: `keyset.py`.
- Crypto lifecycle: `keyset.py::_cursor_crypto_types`,
  `keyset.py::_cursor_aessiv`, `keyset.py::_encrypt_cursor_payload`,
  `keyset.py::_decrypt_cursor_payload` plus the salt/context/hint
  constants; soft dependency via consumer
  `utils/imports.py::require_optional_module`; fallbacks tried
  on decrypt. Owner: `keyset.py`.
- Codec round-trip: `keyset.py::encode_keyset_cursor` /
  `keyset.py::decode_keyset_cursor` share one module, one
  payload shape (`o` fingerprint, `v` values), one prefix, one
  value codec; base64 framing delegated to upstream
  `strawberry.relay.utils::to_base64` / `from_base64`, never
  re-spelled. One owner.
- Direction bit: `keyset.py::keyset_seek_greater` is the sole
  `(descending, flip)` owner; the lateral structural verifier
  (`optimizer/lateral_fetch.py::_keyset_seek_quals_match`)
  reads `plan.greater` / `plan.values`, never recomputes.
  Owner: `keyset.py`.
- Plan + Q/SQL renderers: `keyset.py::KeysetSeekPlan` (arity
  guard, `uniform`, `lead_greater`),
  `keyset.py::build_keyset_seek_plan`,
  `keyset.py::keyset_seek_q` (redundant leading bound plus
  OR-expansion), `keyset.py::keyset_seek_sql` (uniform
  row-value shortcut as the same predicate, mixed directions
  as the same expansion), carried by `keyset.py::KeysetSeek`
  (`q` / `plan`). The lateral adapter prepares values and
  quotes refs, then renders the shared plan by name. One
  owner.
- Local resolver: `keyset.py::_resolve_cursor_field_column`
  (`pk` alias + `get_field`, loud `FieldDoesNotExist`) stays
  separate from `utils/relations.py::classify_path`
  (arbitrary `__` classification) and
  `connection.py::_resolve_order_path_field` (fail-soft `None`
  for per-query effective orders). Declaration-local loud vs
  query-path soft is the contract difference.
- Seek-applies-to-scoped: the target builds pure `Q` /
  SQL-string predicates and byte payloads only - no
  `models.QuerySet(` construction, no `.filter()` call, no
  ORM execution. The ordering (pipeline scopes first, seek
  second) is stated in the module docstring and enforced by
  `connection.py::_resolve_keyset_connection` and the
  plan-time window. No definition here; consumer discipline
  only.
- Captured-definition read: `definition.cursor_field` /
  `definition.model` off the factory-handed definition; the
  connection's per-query `CursorColumn` construction for
  `orderBy:` paths builds the same record for a different
  input (effective order, annotated value sources) - a second
  construction site of one record, not a second rule.
- Cursor decode permission-aware by construction: staff-minted
  cursors replay for restricted viewers over visible rows
  only (live rows in `test_keyset_api.py`).

Reconciliation vs Worker 1, per row: F1 consumer (agree -
census shows no `model_for` call here); F2 consumer
discipline (agree - no queryset construction, `a4` checks
green); F3 rejection (agree - all three axes re-derived
from both bodies fresh); F4 rejection (agree - all three
bodies re-read, loud vs soft confirmed); R1-R13 file-local
(agree - every trigger present and plausible: fourth
vocabulary, second order-identity scheme, second
declaration surface, second vocabulary derivation, second
column-contract enforcement, second value-wire shape,
sixth contract site, second malformed-cursor shape, second
seal mechanism, second payload grammar, third polarity,
third dialect, second declaration resolver); J1 rejection
(agree - `"--name"` raises here vs `("-name", True)` there,
loud vs fallback `None`, expressions only there); J2
rejection (agree - value-seek vs positional-slice, shared
bound/cap/backward/sentinel helpers already shared by
name); J3 separation (agree - each stage enforces what its
inputs allow, shared sub-rule already routed through
`validate_cursor_field_references`). Zero rows
disagree; zero candidates rerouted.

Enumeration, member by member against my own
`ast.Module.body` count: 49 total = 1 module docstring + 17
imports (15 `ImportFrom` + 2 `Import`) + 4 constants
(`KEYSET_CURSOR_PREFIX`, `_CURSOR_ENCRYPTION_SALT`,
`_CURSOR_ENCRYPTION_CONTEXT`,
`_CRYPTOGRAPHY_INSTALL_HINT`) + 5 classes
(`CursorColumn`, `KeysetCursor`, `KeysetSeek`,
`DeclaredCursorState`, `KeysetSeekPlan`) + 22 functions in
file order (`order_fingerprint`, `split_order_ref`,
`validate_cursor_field_references`,
`_resolve_cursor_field_column`, `cursor_columns_for`,
`declared_cursor_state_for_definition`,
`validate_cursor_field_columns`, `serialize_cursor_value`,
`_deserialize_cursor_value`, `keyset_contract_error`,
`_invalid_cursor_error`, `_is_supported_cursor_field`,
`_cursor_crypto_types`, `_cursor_aessiv`,
`_encrypt_cursor_payload`, `_decrypt_cursor_payload`,
`encode_keyset_cursor`, `decode_keyset_cursor`,
`keyset_seek_greater`, `build_keyset_seek_plan`,
`keyset_seek_q`, `keyset_seek_sql`). Carrier methods:
`KeysetSeek::{plan,q}`,
`KeysetSeekPlan::{__post_init__,lead_greater,uniform}`,
other three carriers method-free. Every member lands in
the artifact's table (rows 0-48); the import row's
machinery mapping (R3/R5 via `ConfigurationError`, R9 via
settings/signing/salted_hmac/`require_optional_module`,
R10 via `from_base64`/`to_base64`, R7/R8 via
`GraphQLError`) matches the bodies. No orphan, no double
count.

Matrix vs real surface: axis 1 discharged against sibling
flavors (no other flavor mints cursors or parses
`cursor_field`; Relay global-ID codec is node identity,
not pagination); axis 2 inapplicable by construction (zero
`async def`, zero `await`, zero ORM execution - pure
attribute reads, decryption, coercion, string rendering);
axis 3 discharged (fingerprint, value source, plan,
vocabulary, direction bit each derived once); axis 4
discharged (four grammars, one owner each, all in this
module; keyset-vs-offset fork compared in J2); axis 5
discharged (oracles in `tests/test_keyset.py`,
`tests/test_keyset_connection.py`,
`test_keyset_api.py` pin behavior independently - decoded
tuples, SQL text, uniform error, byte parity - never
reading the owner; BACKLOG/GLOSSARY debts left at the
KANBAN bullet, not re-homed); axis 6 discharged
(declaration vs finalization split, query-time seeks with
inherited unique terminal, plan-time `before:` validated
but unwindowed while root applies `flip=True`). No axis
excused on a found consolidation.

Counts + roles: all 19 single-definition counts
re-hashed green (15 keyset names + `coerce`,
`classify_path`, `_resolve_order_path_field`,
`order_entry_name_and_direction`); prefix defined once;
fingerprint join once; payload keys single-module; decode
funnel exclusive; `require_optional_module` consumer role
confirmed. No oracle rewritten to read from its owner
(checked: forged-payload matrix, SQL-shape rows,
permission-replay rows, determinism/rotation rows all pin
literals or behavior).

Equivalence (principle 8): zero-edit item - no observable
behavior to preserve, nothing to prove equivalent. No
production bytes changed, so no short-circuit, exception,
query, transaction, or timing surface moved.

Zero-edit confirmation: `git diff
f3c0c440d03d12f32613d6656e77f5f8749562fe --
django_strawberry_framework/keyset.py` is empty (probe
`w2-diff-empty`); `git status --short` shows the target
clean and only this artifact untracked. Coverage and
assignment validate: 49/49 homed, challenges C1-C19 each
end in a family row, file-local record, or rejection.
No new candidate found that needs a holding family: the
two consumer roles (F1 seed, F2 seal) and two rejections
(F3 coercion, F4 path) reuse existing index rows with no
status change; J1/J2/J3 are recorded separations with
durable homes. A file item never owes a production edit.

Rejections: F3 (three-axis difference + trigger: a decoded
value reaching a non-comparison sink), F4 (three-job
difference + trigger: `cursor_field` allowing related
paths), J1 (loud vs fallback + dash handling + trigger:
keyset parsing expressions or plans raising), J2
(value-seek vs positional contracts + trigger: third
positioning domain or value-semantic offsets), J3 (stage
inputs + trigger: a twice-checked input with two
spellings) - each carries its concrete difference and
reconsideration trigger. Freshness re-hashed: target
`df4b5e2f...` plus all fourteen cited blobs match the
artifact except `connection.py`, whose working
`3c4d5dcb...` vs HEAD `93e998f2...` split is the
attributed concurrent offset negative-cursor guard
(`_offset_cursor_prefix`,
`_reject_negative_offset_cursor`, fallback-branch lines)
touching none of the fingerprinted keyset sites. Gates:
the cited oracles exist with the claimed titles
(forged-payload matrix, `None`-title rows, determinism,
rotation, permission-aware replay, order-state and
bounds arms); negative controls are coherent by
inspection (fresh-registry read, seek-before-scope,
coercion substitution, resolver substitution each pass
happy paths and fail exactly the guarding rows); no
consolidation gate needs a `prove_failability` run, and
none was run. `## Pending execution` correctly absent
(the read-only probe already ran green; no DB, alias, or
dialect decision involved - inapplicable by
construction). Coupling correctly `None` on every row.

AGENTS.md prose check: no process provenance, no
`Co-Authored-By`, no `path:NN` citations (grep clean), no
inline markdown links, `path::Symbol` citation style
throughout, no test-tier violation (zero-edit item lands
no tests), concurrent dirt untouched (connection hunk,
staged querysets tests, `test_connection.py`,
`bug_hunt-0_0_15.md`, plan file - read as oracles where
needed, never edited).

Defects (Worker 2): none. Every spot-checked claim held:
terminal-null ordering, finalize-before-order-state
chain, Q/SQL shape identity, captured-read discipline,
seal non-ownership, colorless surface.

Verdict: `Status: verified`, no pending execution.

Worker 0 exact plan rows: tick `- [ ] File keyset.py`
to `- [x] File keyset.py —
[dry-file-keyset.md](dry-file-keyset.md) — verified (Run
0.0.15 2026-09-18-1; zero edits, no pending execution)`;
no `## Responsibility index` row added or restated (F1/F2
reuse open/rejected rows unchanged; F3/F4/J1/J2/J3 add
no family); no `## Owned changes` row (zero-edit item);
no `## Families` item (no new family named).
