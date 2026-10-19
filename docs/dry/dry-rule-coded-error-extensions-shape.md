# DRY review: `coded-error-extensions-shape`

Status: verified
Run: 0.0.15 2026-10-01-11

Item kind: FAMILY (responsibility family). Owner candidate re-derived fresh,
not inherited: `django_strawberry_framework/utils/errors.py::coded_error_extensions`
CONFIRMED as the shape owner (narrowest module every consumer already
imports; pure construction, nothing stored). Consolidation implemented in
this same change: 3 shape definitions -> 1.

Concurrency: every indexed file carries concurrent dirt (truth migration +
except-deletion / prose rework; no `## Owned changes` row covers any of
them); all of it is attributed by diff content below and preserved
byte-for-byte. Every production edit line was byte-identical between HEAD
and WT before the edit; both import inserts are purely additive; the test
additions are purely additive. No concurrent line edited, reverted, or
tidied. `tests/utils/test_errors.py` is MIXED (adopted G1/G2/G3 gates +
hunt dirt): the gate was appended after the tail with zero new imports
(`ast`, `Path`, `errors_module` all pre-existing), touching no dirty line.

Baselines: `ITEM_BASELINE=35631dca467452a582ea8242df905e2dad293fe3`
(resolves); HEAD `dd0b6691` unmoved throughout. Dispatch pins verified at
task start: `utils/errors.py` WT `a4afaf43` / HEAD `53d74870`,
`schema.py` WT `c3f267aa` / HEAD `f3b6df8f`, `list_field.py` WT `b534ea32` /
HEAD `3842542a`, `filters/base.py` WT `9edbef64` / HEAD `058fcfb1`,
`filters/sets.py` WT `14884190` / HEAD `76abccb0`, `relay.py` WT
`63bbba0b` / HEAD `037723cd`, `resource_policy.py` WT `f95f1580` / HEAD
`9faff1a8`. Address `dry/codext-f47/consolidate` (slot-2; every proof ran
there). Post-edit WT blobs: `schema.py` `7390c985`, `list_field.py`
`f7b75c2a`, `tests/utils/test_errors.py` `b0c03fe1`.

## System trace

Rule: every coded framework rejection carries
`extensions == {"code": <CODE>, **detail}` so a client branches without
parsing prose. The placement rule beside it: a subsystem code constant
either lives at `utils/errors.py` (the three owned codes) or stays at its
own subsystem owner and is passed in (`RESOURCE_LIMIT_ERROR_CODE` at
`resource_policy.py`, `SCHEMA_CONFIGURATION_ERROR_CODE` at `schema.py`).
Detail keys are caller-chosen; conditional detail stays at the raise site.

Mechanism sweeps (whole package, re-derived fresh at current WT bytes;
HEAD spot-confirmed for the three construction sites):

- `coded_error_extensions` (grep): 1 def + 1 `__all__` entry + 1 docstring
  mention at the owner; 11 composing call expressions in 6 files
  (`filters/sets.py` 2, `filters/base.py` 5, `relay.py` 1,
  `resource_policy.py` 1, `schema.py` 1, `list_field.py` 1 — the last two
  landed by this change).
- `"code":` (grep): exactly 3 code constructions pre-change (owner
  `utils/errors.py:131`, `list_field.py:312`, `schema.py:708`) + 7 prose
  mentions (docstrings/comments) + 0 others. Post-change: 1 (the owner).
- `extensions=` (grep): the 9 pre-change coded call sites + the 2 bypass
  dicts + the correlation shape (`extensions/error_policy.py:192`) +
  strawberry chain config / response reads (each excluded by body, R4).
- Residual patterns (`dict(code`, `extensions[`, `.update(` into an
  extensions map, `GraphQLFormattedError` construction): zero hits — no
  second construction spelling exists.
- `GraphQLError` (grep, whole package): 11 coded constructions (all
  composing post-change) + 15 codeless message-only raises (R2) + the
  correlation replacement (R1) + catches / prose.

Site inventory (WT line numbers; roles per DRY.md vocabulary):

- Definition (shape): `utils/errors.py::coded_error_extensions` (:116-131)
  + the 3 owned code constants (:111-113).
- Former definitions, now composers: `schema.py::_RefusedConfiguration._refusal`
  (:704-709) and `list_field.py::ListArgumentError.__init__` (:258-322).
- Consumers by name (unchanged): `filters/sets.py`
  (`_reject_shared_bag_form_keys` :2766, `_validate_form_or_raise` :3157),
  `filters/base.py` (`_materialize_list_shaped_values` :227 with 4 coded
  callers, `_decode_and_validate_global_id` :821/:850/:870/:881), `relay.py`
  (`_decode_or_graphql_error` :137), `resource_policy.py`
  (`ResourceLimitExceeded.__init__` :147, passing its own code + detail).
- Oracles (independent, spell values literally): `tests/utils/test_errors.py`
  (vocabulary + shape pins, G1/G2/G3), `tests/test_list_field.py` (full-dict
  pin), `tests/test_error_policy.py` (refusal full-dict pin), live
  `test_query/test_list_field*.py` (wire code pins across reason arms),
  plus consumer pins in `tests/filters/`, `tests/test_relay_node_field.py`,
  `tests/test_resource_policy.py`, `tests/test_registry.py`.
- Projections: `utils/errors.py` module + function docstrings (shape and
  placement prose), `filters/base.py` + `relay.py` docstrings (spelled
  shapes), spec-050 (list error payload), spec-047 (limit payload),
  glossary (refusal / limit / masking contracts).

Connected behavior examined in full: the owner module; both bypass
classes end to end (constructors, `__reduce__`, callers, no subclasses);
all 9 composing raise sites with their messages; the 15 codeless raises
(each read for its contract); the correlation replacement; the DRF
`.code` readers; the strawberry chain-config `extensions=` sites; the
spec-050 payload contract; the glossary refusal/limit rows; every oracle
file above.

Freshness (short blobs are `git hash-object` WT / `git rev-parse HEAD:`;
full hashes in `## Implementation`):

| Input | WT / HEAD | State as cited |
|---|---|---|
| `utils/errors.py` | `a4afaf43` / `53d74870` | owner read whole; untouched by this item |
| `schema.py` | `7390c985` / `f3b6df8f` | read whole; bypass at HEAD `:703` too |
| `list_field.py` | `f7b75c2a` / `3842542a` | read whole; bypass at HEAD `:327` too |
| `filters/base.py` | `9edbef64` / `058fcfb1` | read whole; 8 raise sites |
| `filters/sets.py` | `14884190` / `76abccb0` | shape-token census closed; 2 regions read whole |
| `relay.py` | `63bbba0b` / `037723cd` | read whole |
| `resource_policy.py` | `f95f1580` / `9faff1a8` | read whole |
| `extensions/error_policy.py` | WT dirty / HEAD | `_masked` + `_degraded` re-read |
| `keyset.py`, `connection.py`, `mutations/resolvers.py` | WT dirty / HEAD | codeless sites re-read |
| `tests/utils/test_errors.py` | `b0c03fe1` / `631bf250` | read whole; gate appended |
| spec-050, spec-047, glossary | WT / HEAD | payload contracts cited by content |

Searched populations: whole package for `coded_error_extensions`, `"code":`,
`extensions=`, `ERROR_CODE`, `GraphQLError`, `dict(code`, `extensions[`,
`GraphQLFormattedError`; test trees + docs for all six wire code values.
Modules excluded on strength of body: every package module outside the
inventory above (zero rule tokens over the sweeps; each `extensions=`
non-hit classified in R4).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The write flavors (model / form /
   serializer / auth) carry no coded `GraphQLError` surface: their
   rejections are in-band `FieldError` envelopes (R3) plus one codeless
   auth denial (R2). The coded surface spans filters, relay, resource
   policy, schema, and list field; every one of its 11 constructions now
   composes the owner. No flavor-local second definition.
2. **Sync/async twins.** Inapplicable with reason: the shape is sync pure
   construction (one dict literal per call, no ORM, no await point); both
   bypasses construct inside exception `__init__` bodies that run
   identically under either executor. No twin and no boundary that could
   separate one.
3. **Derived rather than repeated knowledge.** The only derivation of the
   shape is the owner body; the two bypasses spelled it, they did not
   derive it by other means. Code VALUES flow by name except the one
   single-sited `LIST_ARGUMENT_INVALID` literal (R5: a naming note, not a
   second definition — a value change is one edit either way).
4. **Inverse / round-trip pairs.** Construct-only surface: no package code
   parses a coded `extensions` payload back (the testing client reads
   response extensions opaquely; error-policy classification reads
   `original_error`, never `"code"`). No inverse half exists to unify.
5. **Contracts restated in another medium.** Oracles spell every code and
   shape literally (17 test files; never read from the owner). Projections
   (docstrings, specs, glossary) describe the payloads. Neither medium
   constructs the shape; the AST gate (Dict nodes only) is blind to both
   by construction.
6. **Enforcement by omission.** All 27 package `GraphQLError`
   constructions enumerated: 11 coded (all composing), 15 codeless, 1
   correlation (R1). The
   codeless raises carry message-only contracts with no code vocabulary;
   two of them (relay + filter type mismatches) are documented-intentional
   (R2). No contract source assigns codes to any codeless site, so none is
   an omission gap; giving any of them a code would be a wire change, not
   a consolidation.

### Challenges

Counts name authoritative definitions only (consumers, oracles,
projections listed, never counted). Pre-change -> post-change.

| Id | Change posited | Count | Home |
|---|---|---|---|
| C1 | Universal `"code"` key renamed | 3 -> 1 | F1 |
| C2 | Universal key added to every coded error | 3 -> 1 | F1 |
| C3 | List conditional detail (`value`/`ceiling` arms) | 1 | F1 boundary (stays at the site) |
| C4 | Owned-code relocation (e.g. `FILTER_INVALID`) | 1 | F1 vocabulary |
| C5 | New subsystem code under the placement rule | 1 | F1 placement |
| C6 | `ResourceLimitExceeded` detail keys | 1 | consumer-local |
| C7 | Refusal message set / refusal triple | 1 | file-local `refusal-substitution` |

C1/C2 are the duplication (each bypass needed its own edit for a
mechanism change). C3 confirms the boundary: the owner parameterizes
detail but never decides it — spec-050's conditional arms stay in
`list_field.py` untouched. C4/C5 confirm the vocabulary and placement
halves were already single.

## Findings

### F1 — coded extensions shape (CONFIRMED + CONSOLIDATED, 3 -> 1)

- **Contract + variation.** Every coded framework rejection carries
  `extensions == {"code": <CODE>, **detail}`. Varies on code
  (per-subsystem vocabulary) and detail keys (caller-chosen, possibly
  conditional). The placement rule: a subsystem code lives at
  `utils/errors.py` or stays at its own owner and is passed in.
- **Sites + roles.** Definition: `utils/errors.py::coded_error_extensions`
  (+ the 3 owned constants). Former definitions, now composers:
  `schema.py::_RefusedConfiguration._refusal` and
  `list_field.py::ListArgumentError.__init__`. Consumers by name: the 9
  pre-existing call sites in `filters/sets.py`, `filters/base.py`,
  `relay.py`, `resource_policy.py`. Oracles: the vocabulary + shape pins
  and the per-site full-dict / wire-code pins (listed above, never
  counted). Projections: docstrings, spec-050, spec-047, glossary.
- **Challenges.** C1 3->1; C2 3->1; C3 1 (stays out); C4 1; C5 1.
- **Owner + lifetime.** `utils/errors.py::coded_error_extensions` by
  principle 7: it already owns the shape contract in prose and body; it
  is the narrowest module every legitimate consumer can import without
  reversing a dependency (`utils/errors.py` imports django + `truth`
  only); both bypass files already import `utils.*` and reach the owner
  transitively via `resource_policy.py`, so the new edges add no cycle.
  Lifetime: pure construction, nothing stored.
- **Migration.** `_refusal` passes its code to the owner (one line +
  import). `ListArgumentError.__init__` builds the `detail` dict with its
  two conditionals byte-identical and passes code + `**detail` to the
  owner (spec-050's conditional contract preserved exactly, key order
  preserved: code, argument, reason, value, ceiling).
- **Distinct behavior.** Conditional detail selection stays at the raise
  site (C3); code placement stays split per the rule (R7); the refusal
  triple stays file-local at `schema.py` (C7); codeless raises stay
  codeless (R2).
- **Behavioral proof.** Owner shape + vocabulary pins, both bypass
  full-dict pins, the full `test_list_field.py` /
  `test_error_policy.py` / `test_schema.py` suites (301 rows), and both
  live list-field API suites (219 rows) — all green against the migrated
  code (`execution-verified`, runs below). Each rejects the wrong result:
  a dropped, added, or reworded key fails the full-dict pins; a shape
  change on any reason arm fails the live wire pins. Key-order and
  no-cycle reasoning are `static-reviewed` (order read off both dict
  constructions; cycle freedom read off the import blocks).
- **Structural gate.**
  `tests/utils/test_errors.py::test_coded_extensions_shape_is_constructed_only_in_the_owner`:
  exact-match AST census over all package sources for `Dict` nodes with
  a `"code"` key, asserting the single hit
  `("utils/errors.py", "coded_error_extensions")`. Negative control
  proved via `prove_failability.py`: a behavior-identical hand-restored
  bypass fails exactly the gate while 3 behavior oracles pass; restore
  byte-proved (run below).
- **Coupling.** None: the two compositions are independent one-site
  edits; either lands alone.
- **Freshness.** Owner blob unchanged by this item (`a4afaf43`);
  bypasses verified at HEAD bytes too (`schema.py:703`,
  `list_field.py:327`), so the duplication predates all WT dirt.

### R1 — correlation extensions (REJECTED, converge)

`extensions/error_policy.py::_masked` builds
`{correlation_key: correlation_id}`: a codeless per-error support
identifier, deliberately without a `"code"` key so masked errors stay
indistinguishable. Different readers (support staff vs branching
clients), different indistinguishability contract. CONVERGE with standing
File `utils/errors.py` `errors-coded-shape-vs-correlation-shape` on fresh
evidence (no trigger trip: the payload carries no client-branched code).
Trigger: the correlation payload gaining a `"code"` key. No new index
row (standing row stands).

### R2 — codeless raises (REJECTED, fresh)

15 message-only `GraphQLError` constructions (`connection.py` 9,
`keyset.py` 2, `mutations/resolvers.py` auth denial 1, `relay.py` typed
mismatch 1, `filters/base.py` type mismatch 1, `_degraded` 1) carry no
extensions at all and no code vocabulary. Shared form considered: route
all package `GraphQLError`s through the coded shape — rejected: the last
two are documented-intentional (the spec assigns a code only to
`GLOBALID_INVALID`; the mismatch keeps its code-less shape), and the
rest have message-only contracts with no contract source assigning
codes. Giving any of them a code is a wire change, never a
consolidation. Home: each raise site's own contract (documented pair at
`relay.py::_check_typed_match` + `filters/base.py::_decode_and_validate_global_id`).
Trigger: a spec or contract assigning a code to any of these surfaces.

### R3 — envelope codes (REJECTED, converge)

In-band `FieldError.codes` vs top-level `extensions.code`: different
clients at different layers. CONVERGE with standing File
`utils/errors.py` `errors-envelope-vs-extension-codes` (and verified
`mutation-error-envelope` R3) on fresh evidence — no unified reader
exists in tests, glossary, or `docs/README.md`. Trigger: a client
contract reading both as one vocabulary. No new index row.

### R4 — engine extension shapes (REJECTED, fresh)

Strawberry `extensions=[...]` chain config, `GraphQLArgument.extensions`
metadata reads, the testing client's response-`extensions` read, and the
runner's `extensions=` passthrough share the NAME `extensions` with the
error payload and nothing else: different types, different readers,
different writers. Shared form considered: one extensions vocabulary —
rejected: unifying engine configuration with an error payload couples
independent domains with no change obligation relieved. Home: each
site's own engine contract. Trigger: none foreseen (upstream shapes).

### R5 — `LIST_ARGUMENT_INVALID` literal (REJECTED, naming note)

The code VALUE literal is single-sited (1 package hit); a value change
is one edit with or without a name, so no definition count moves.
Shared form considered: a named constant at `list_field.py` — rejected:
it adds public API surface with no consistent export precedent (the root
exports the resource + schema codes but not the filter/globalid ones),
and no consumer branches on this value by name. Home:
`list_field.py::ListArgumentError` (specified, not written: the class
docstring region is hunt-dirtied). Trigger: a second site spelling the
value, or a consumer needing the name.

### R6 — DRF `.code` attribute reads (REJECTED, fresh)

`rest_framework/resolvers.py` `getattr(item, "code", None)` reads the
upstream `ErrorDetail.code` attribute vocabulary into leaf codes — an
input contract, not an error-payload construction (Call nodes, never
Dict nodes; outside the gate by design). Trigger: a DRF `.code` value
flowing into an error `extensions` payload.

### R7 — code placement split (REJECTED, fresh)

`RESOURCE_LIMIT_ERROR_CODE` and `SCHEMA_CONFIGURATION_ERROR_CODE` stay
at their subsystem owners while the three filter/globalid codes live at
`utils/errors.py`. Shared form considered: all codes at `utils/errors.py`
— rejected: the placement rule explicitly admits both homes, the
subsystem codes are each subsystem's public contract (both root-exported,
each consumed only inside its subsystem), and moving them would reverse
the ownership direction. Home: the placement prose at
`utils/errors.py::coded_error_extensions`. Trigger: a subsystem-homed
code gaining a cross-subsystem consumer.

## Defects

None.

Observed, not homed: spec-050 cites
`django_strawberry_framework/exceptions.py::describe_value` for the
non-integer safe value while concurrent WT dirt removes that name (the
`list_field.py` import hunk + `truth.describe` respellings). That drift
belongs to the migration's own wake in uncommitted bytes, not to this
item; no action.

## Pending execution

None. Every proof executed (runs below). Sharded/PG cells:
inapplicable-by-construction — the migrated lines are pure dict
construction of exception payloads (no database, alias, or dialect read)
and the gate is a source AST census; no new branching on cell state. The
error paths themselves run under every cell in the full suite, unchanged
in behavior. Worker-2 judges.

## Judgment

CONFIRM-consolidated. The coded shape had three independently maintained
definitions (the owner + two bypasses, all present at HEAD); one
mechanism change now lands in one body. Counts: C1 3->1, C2 3->1, C3/C4/
C5/C6/C7 independence confirmed at 1; seven rejections with triggers
(R1/R3 converge on standing rows, R2/R4/R5/R6/R7 fresh with named
homes); zero sub-rule families beyond the five fresh rejection rows;
zero defects; zero pending execution. Net tracked change +58/-9 over
three files, 548 proof rows green, failability proved.

## Implementation (Worker-1)

Tracked edits (5 hunks vs
`ITEM_BASELINE=35631dca467452a582ea8242df905e2dad293fe3`, all attributed
to this item; every other hunk on these paths predates the baseline and
was left byte-identical):

- `django_strawberry_framework/schema.py` (+2/-1): import `:98` (purely
  additive, isort order); `_refusal` `:708` composes the owner.
- `django_strawberry_framework/list_field.py` (+8/-8): import `:89`
  (purely additive, isort order); `__init__` `:311-321` builds `detail`
  with both conditionals byte-identical and passes code + `**detail` to
  the owner.
- `tests/utils/test_errors.py` (+48/-0): `_coded_shape_construction_sites`
  helper + the census gate
  `test_coded_extensions_shape_is_constructed_only_in_the_owner`
  (zero new imports; body appended after the tail).
- `django_strawberry_framework/utils/errors.py` untouched.

Concurrency attribution by diff content vs `git show HEAD:<path>` before
the first edit: `schema.py` carries 20 hunt hunks (truth migration +
prose), none covering `_refusal` `:704-709` (verified: HEAD `:703`
identical); `list_field.py` carries 25 hunt/maintainer hunks, none
covering `:311-321` (verified: the flanking hunks end at WT `:306` and
resume at WT `:324`); both import inserts land on clean lines adjacent
to hunt-added lines without modifying them; the test append touches no
existing line. No concurrent line edited, reverted, or tidied.
Proposed Worker-0 transcription: Family `coded-error-extensions-shape`
-> consolidated; index row likewise; `## Owned changes` rows for the 3
paths above (+58/-9).

Gates (all in workspace copy `dry/codext-f47/consolidate`, slot-2):
ruff `check` + `format` on the 3 touched paths clean, 3 files unchanged
(shared tree, post-edit); `check_trailing_commas.py --check` on the 3
touched paths 0 violations; basedpyright 0/0/0
(`dry-20261001T194814-b31de6`); check_any 128 uses at 89 sites exit 0
(`dry-20261001T194822-db6009`, ALLOWED_ANY untouched — zero new
Any/cast/suppression); truthful-reads tier-1 0 / errors 0
(`dry-20261001T194823-0d212a`). Behavior runs: owner suite + both bypass
pins 28 passed (`dry-20261001T194830-09f390`); `test_list_field.py` +
`test_error_policy.py` + `test_schema.py` 301 passed
(`dry-20261001T194838-558d69`); live `test_list_field_api.py` +
`test_list_field_async_api.py` 219 passed
(`dry-20261001T194849-e7a135`). Failability record
(`dry-20261001T194958-4c441d` report, `dry-20261001T195007-2e0d2d`
verdict): baseline 4 passed, mutant 1 failed exactly the declared gate
with 3 behavior oracles passing, restore filecmp + sha256 proved
(`f7b75c2a` before and after). Banned-word sweep of the item diff:
`plan audit sweep restored hardening previously worker grader feedback`
zero hits (case-insensitive whole-word grep over `/tmp/f47-item.diff`).
No `pragma: no cover`. `mypy` never run, never cited.

Full fingerprints: WT `schema.py`
`7390c98557decfa396d37c06d1f13738dd3d5466` /
`list_field.py` `f7b75c2aee43b1ce5a35418f8b1a238758700ed9` /
`test_errors.py` `b0c03fe190901ffbc164e834d3772e6e75f1b163`;
HEAD `schema.py` `f3b6df8f0003a54e1f0bd6a7ba4c8201dd5b17c1` /
`list_field.py` `3842542aa96ada6f73bea299df7de83f4df30fd5` /
`test_errors.py` `631bf2501dc77ee6d5beb1139cb8b51dcca37694` /
`utils/errors.py` `53d7487088c16a60b8c3d332e16c96aab7d0b8a6`.

## Index rows for Worker 0

(Worker-0 alone edits the plan; rows named here for transcription.)

- Family `coded-error-extensions-shape` | Owner
  `django_strawberry_framework/utils/errors.py::coded_error_extensions` |
  Files `utils/errors.py`, `schema.py`, `list_field.py`, `filters/base.py`,
  `filters/sets.py`, `relay.py`, `resource_policy.py` | Holding item
  Family `coded-error-extensions-shape` | consolidated (F1: 3->1, C1/C2;
  R1/R3 converge on standing rows, R2/R4/R5/R6/R7 rejected with triggers)
- `codeless-raises-vs-coded-shape` |
  `django_strawberry_framework/relay.py::_check_typed_match` (rejection
  recorded here; 15 message-only raises with no code vocabulary, two of
  them documented-intentional) |
  `django_strawberry_framework/relay.py`,
  `django_strawberry_framework/connection.py`,
  `django_strawberry_framework/keyset.py` | Family
  `coded-error-extensions-shape` | rejected (trigger: a spec or contract
  assigning a code to any codeless surface)
- `engine-extension-shapes-vs-error-extensions` |
  `django_strawberry_framework/list_field.py::_published_wire_name`
  (rejection recorded here; chain config + metadata/response reads share
  the name only) | `django_strawberry_framework/list_field.py`,
  `django_strawberry_framework/schema.py`,
  `django_strawberry_framework/testing/client.py` | Family
  `coded-error-extensions-shape` | rejected (trigger: none foreseen,
  upstream shapes)
- `list-argument-code-literal-vs-named-constant` |
  `django_strawberry_framework/list_field.py::ListArgumentError`
  (rejection recorded here; single-sited value literal, no export
  precedent; home specified, region hunt-dirtied) |
  `django_strawberry_framework/list_field.py` | Family
  `coded-error-extensions-shape` | rejected (trigger: a second site
  spelling the value, or a consumer needing the name)
- `drf-code-attribute-reads-vs-extensions-shape` |
  `django_strawberry_framework/rest_framework/resolvers.py`
  (rejection recorded here; upstream input vocabulary, Call nodes never
  Dict nodes) |
  `django_strawberry_framework/rest_framework/resolvers.py`,
  `django_strawberry_framework/utils/errors.py` | Family
  `coded-error-extensions-shape` | rejected (trigger: a DRF `.code`
  value flowing into an error `extensions` payload)
- `extension-code-placement-split` |
  `django_strawberry_framework/utils/errors.py::coded_error_extensions`
  (rejection recorded here; subsystem-homed vs errors-homed codes, both
  homes admitted by the rule) |
  `django_strawberry_framework/utils/errors.py`,
  `django_strawberry_framework/resource_policy.py`,
  `django_strawberry_framework/schema.py` | Family
  `coded-error-extensions-shape` | rejected (trigger: a subsystem-homed
  code gaining a cross-subsystem consumer)

## Independent verification (Worker-2)

Address `dry/codext-f47/verify-1` (slot-3, synced after W1's edits;
provenance `dry-20261001T195834-7d9b04`, copy fresh, shared tree unmoved
throughout). HEAD `dd0b6691` unmoved. All counts below re-derived by
fresh grep/AST-equivalent sweeps at WT bytes before reconciliation; all
executions ran in the copy unless noted shared-tree read-only.

### Own trace (pre-reconciliation)

Rule: a coded framework `GraphQLError` carries
`extensions == {"code": <CODE>, **detail}`.

- Owner I would choose: `utils/errors.py::coded_error_extensions` —
  already owns the shape in body + prose, is the narrowest module every
  consumer can import (imports django + `truth` + stdlib only; `truth`
  imports stdlib only; `utils/__init__` pulls relations/strings/typing
  leaves whose only package imports are `truth` and leaf
  `exceptions.py`), and 9 call sites already compose it. No other
  candidate: the bypasses sit in heavier modules no peer could import.
- Definitions pre-change: 3 — the owner body
  (`return {"code": code, **detail}`), `schema.py::_refusal`'s inline
  `{"code": ...}` dict, `list_field.py::ListArgumentError.__init__`'s
  inline dict + conditional appends. Post-change: 1 (the owner).
- Composing calls post-change: 11 in 6 files — `filters/sets.py` 2,
  `filters/base.py` 5 (one via `_materialize_list_shaped_values`, itself
  called with a coded `code=` at 4 sites), `relay.py` 1,
  `resource_policy.py` 1, `schema.py` 1, `list_field.py` 1.
- `"code":` code constructions: 3 pre (owner + 2 bypasses) / 1 post;
  remaining hits are docstring/comment prose. Residual spellings zero:
  `dict(code`, `GraphQLFormattedError`, `["code"]`, `'code':` all zero;
  `extensions={` has one code site, the correlation shape (non-`"code"`
  key); `extensions[` only prose (`extensions["debug"]`,
  `extensions["strawberry-definition"]`).
- `GraphQLError` census: 27 = 11 coded (9 literals + 2 subclass
  `super().__init__` compositions) + 15 codeless message-only
  (`connection.py` 9, `keyset.py` 2, `mutations/resolvers.py` 1,
  `relay.py` typed mismatch 1, `filters/base.py` type mismatch 1,
  `_degraded` 1) + 1 correlation replacement. Every site read and
  classified.
- Code vocabulary closed at 6 wire values: 3 owned at `utils/errors.py`,
  `RESOURCE_LIMIT_EXCEEDED` at `resource_policy.py`,
  `SCHEMA_CONFIGURATION_UNAVAILABLE` at `schema.py`, the single-sited
  `LIST_ARGUMENT_INVALID` literal. `FIELD_ERROR_CODE_*` is the separate
  in-band envelope vocabulary (different readers, different layer).
- Challenges: universal key rename / universal key added both 3->1
  (the duplication); list conditional detail, owned-code relocation, new
  subsystem code, limit detail keys, refusal triple all 1 (independent).

### Reconciliation

Every load-bearing number matches W1 exactly (11 calls / 6 files, 3->1,
27 = 11+15+1, per-file splits, C1–C7 homes). One annotation differs, and
it is mine that is right: the freshness table says `filters/base.py`
"8 raise sites", but WT carries 6 `raise GraphQLError(` sites
(:227, :821, :850, :858, :870, :881); 8 is the HEAD count — concurrent
except-deletions removed 2 composing wrappers (the `_materialize`
`try/except` and the EMPTY_VALUES guard) between HEAD and WT. The
artifact's own per-site inventory lists exactly the 6 WT sites, so no
count, challenge, gate population, or rejection moves; Worker-0 may
transcriptionally correct the parenthetical to "6 at WT (8 at HEAD)".
No other difference.

### Points (a)–(f)

(a) Equivalence, executed. Key order: pre-change construction builds
code, argument, reason, then conditional value, then conditional
ceiling; post-change `detail` preserves that insertion order and the
owner prepends `code` — byte-identical order on all 5 reason arms plus
the refusal, asserted key-by-key in the copy
(`dry-20261001T200013-5ed020`): over_ceiling carries value + ceiling,
negative/non_integer/order_required carry value only, queryset_required
carries neither — exactly spec-050's conditional arms, which I read
independently. The `value`/`ceiling` conditionals are line-identical
modulo the dict name. Refusal triple (on_parse/on_validate/on_execute),
both `__reduce__` bodies, and the no-subclass claims verified by
reading; pickle roundtrip re-executed green
(`dry-20261001T200023-8f7447`).

(b) Gate re-derived. The exact-match assertion is right: the single hit
`("utils/errors.py", "coded_error_extensions")` is the only Dict node
with a `"code"` key in the package, and Dict-node-only scope is the
right cut — docstrings/comments parse to Constant nodes, DRF `.code`
reads are Call/Attribute nodes (`getattr(item, "code", None)`), no
package source reads `extensions["code"]` back. Negative control
re-proved in my own copy: a hand-restored `_refusal` dict fails exactly
the gate with the extra hit
`('schema.py', '_RefusedConfiguration._refusal')`
(`dry-20261001T200050-8761a2`) while both bypass behavior oracles pass
(`dry-20261001T200102-2f356d`); restore sha256-proved
(`eda45134` before/after). W1's prove record judges sound.

(c) MIXED append judged clean. Item diff on `tests/utils/test_errors.py`
is +48/-0: the baseline file is 397 lines ending at G3's tail, WT is
445, the gate + helper append after the tail touching zero existing
lines (the adopted G1/G2/G3 gates included). Zero-new-imports accurate
(`ast`, `Path`, `errors_module` all pre-existing). Production
attribution: both import inserts purely additive in isort position
below hunt-added lines; `_refusal` spans HEAD-identical except the one
composed line; the `__init__` deletion sits above the `__reduce__` dirt
(`self.__class__` vs `type(self)`) with the boundary in shared context.
No concurrent line touched.

(d) Rejections judged complete. R1–R7 each carry contract difference +
trigger + home. Converges verified against standing records: R1 matches
File `utils/errors.py` R3 byte-for-byte in contract difference
(rejection code vs codeless support identifier) and trigger (payload
gaining a client-branched `"code"` key — absent at
`extensions/error_policy.py:192`); R3 matches standing R5 and its
trigger re-check (no unified envelope+extension reader in tests,
glossary, or README — spot-swept, only per-site pins). Freshness
re-hashed same-kind (`git hash-object` WT vs `git rev-parse` HEAD):
schema `7390c985`/`f3b6df8f`, list_field `f7b75c2a`/`3842542a`, test
`b0c03fe1`/`631bf250`, errors `a4afaf43`/`53d74870` untouched, all four
connected pins exact. Pending-None correct (every proof executed; my
re-runs below add no new deferral). Coupling none correct (two
independent one-site edits). Sharded/PG inapplicable-by-construction
judged sound: pure dict construction + a source AST census, no
database/alias/dialect read, no new cell-state branch.

(e) Tier + prose judged clean. The AST census reads package source, a
surface no GraphQL query reaches, so `tests/` is the mandated tier;
f39 (`tests/test_multipart.py` census gate) and f45
(`tests/utils/test_canonical.py` census gate) are exact precedents, both
verified plain. AGENTS.md prose: banned-word sweep over the item diff
zero hits; no process provenance; no new comments, so no citation debt;
line numbers appear only in this per-cycle artifact (allowed). Ruff
`format --check` + `check` on all three touched paths green in the copy
(`dry-20261001T195846-1aac0d`, `dry-20261001T195847-c7a6a1`);
`check_trailing_commas.py --check` 0 violations
(`dry-20261001T200401-e3f862`).

(f) No cycle; type gates match baseline. New edges point downward into
`utils/errors.py`, whose transitive runtime imports (stdlib, django,
`truth`, utils leaves, `exceptions.py`) reach back to nothing —
cycle-free by construction, and 9 files already import from the
owner (10 import statements, some function-local). Re-ran all three gates in the copy: basedpyright 0/0/0
(`dry-20261001T200122-e99e8a`), check_any 128 uses at 89 sites exit 0
(`dry-20261001T200145-603968`), truthful-reads tier-1 0 / errors 0
(`dry-20261001T200150-a27335`) — all equal to the run-11 baseline; added
lines contain no Any/cast/ignore/noqa/`type:` and ALLOWED_ANY semantics
hold (identical counts). mypy never run, never cited.

### Behavior re-runs (copy slot-3, one suite at a time)

Owner suite `tests/utils/test_errors.py` 26 passed incl. the new gate
(`dry-20261001T195851-ac1966`); bypass suites `test_list_field.py` +
`test_error_policy.py` + `test_schema.py` 301 passed
(`dry-20261001T195916-7dfb32`, count matches W1 exactly); live sample
`examples/fakeshop/test_query/test_list_field_api.py` 141 passed
(`dry-20261001T200235-c3ab23`). Full-dict oracle pins in
`tests/test_list_field.py` and `tests/test_error_policy.py` spell
literals and were untouched by the diff — no oracle reads from the
owner.

### Defects

None. (Worker-2) No new defect: the codeless sites carry message-only
contracts with no code-assigning source (R2 trigger covers the future);
W1's observed-not-homed spec-050/`describe_value` drift note correctly
belongs to the migration's uncommitted wake, not this item.

### Verdict

Verified. F1 CONFIRM + CONSOLIDATED 3->1 stands on my independent
trace; R1–R7 stand with triggers; the gate pins the single site and
fails its negative control; equivalence is executed, not just read.
