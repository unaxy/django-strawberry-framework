# DRY review: `filter-globalid-encode-decode-pair`

Status: verified
Run: 0.0.15 2026-10-12-22

## System trace

Encode half: `filters/inputs.py:801` `_encode_global_id_input` — a
`relay.GlobalID` OBJECT becomes the base64 wire string via upstream
`relay.to_base64(type_name, node_id)`; every other shape (incl. `str`)
passes through unchanged. Sole callers are the `_gid` / `_gid_multi`
arms of `normalize_input_value` (:704/:707), itself called once in
production (sets.py:3137 `_normalize_input`).
Decode half: `filters/base.py:971` `_decode_and_validate_global_id` —
object short-circuits, `str` parses via direct `relay.GlobalID.from_id`
(+ own non-str->ValueError route); then strategy gate (FRAMEWORK union),
accepted-name check, empty-id reject, target-pk coercion. Called by both
filter `filter()` bodies (:1154/:1285).
Codec census over 118 package files: executable GlobalID-grammar sites
are exactly the encode call (:820) + two `from_id` parses (base.py:1030,
types/relay.py:922); keyset (:545) + connections (:731) are different
grammars (cursor codecs); the `str(GlobalID)` mint (testing/relay.py:120)
is upstream's other spelling of the same grammar.

## Verification

### Matrix

1. Cross-flavor: write decodes compose `decode_global_id` (DecodeResult
contract); orders `normalize_input_value` is a disjoint function. No mirror.
2. Sync/async: both halves pure sync; one `_normalize_input` body both colors. N/A.
3. Derived-twice: `str(gid)` vs `to_base64(t, n)` are two upstream
spellings of one upstream grammar (equality test-pinned). Excluded, count 0.
4. Round-trip: THIS item — the halves compared as one pair below.
5. Media: spec-027 D4 pins both halves; spec-031 D13 pins strategy
validation; oracles listed under F1, not counted.
6. Omission: both GlobalID filters decode (scalar + per-element); pk/choice
filters take no GlobalID by contract; node/write paths are item 10. No gap.

### Challenges

C1 wire shape (`type:node` base64): upstream owns `to_base64`/`from_id`;
the package calls both by name → 0 own definitions.
C2 object/str acceptance: dropping objects is implausible (spec'd); a
third shape touches decode only (encode forwards unknowns) → no 2-logic change.
C3 type_name preservation: encode re-encodes (0 own logic) so the
single-sited decode check can run → 1 validation definition.
C4 empty-id posture / C5 error codes / C6 strategy+coercion: decode-only → 1.
C7 decode-via-`decode_global_id`: different envelopes + subjects → item 10.

## Findings

### F1: filter halves are complementary contracts, not one grammar (REJECT)

Contract: pre-form shaping (object→wire `str`, validation-free) vs
post-form acceptance+validation (parse + strategy + name + empty + pk).
Sites: encode = shaping definition (inputs.py:801, 1 helper + 2 arms);
decode = validation definition (base.py:971, 5 raises, 1 function);
`str`/`list[str]` convert annotations (:576/:579) = consumers; spec-027
D4 + tests = oracles/projections.
Challenges C1–C6: every plausible change moves at most 1 logic-carrying
definition. The shared `isinstance(·, relay.GlobalID)` arms are a
single-expression upstream-type predicate with position-specific actions
(pre-form MUST be `str` for the django-filter clean step; post-form may
be object) — below bar per the run-21 single-expression precedent.
Contract difference: encode enforces nothing (forwards malformed str,
empty-id and wrong-type objects untouched for decode to reject); decode
enforces everything. No drift: object→wire→parse round-trips exactly
(pinned), and every forwarded shape classifies in decode identically to
a direct-to-filter call.
Trigger: a THIRD GlobalID-input pipeline position needing the
object→wire/object decision — then one shared accept/parse spine pays.
The separation is already recorded at both owners (encode docstring
names "the canonical decode-and-validate path"; decode docstring owns
the grammar) + spec-027 D4 — no prose edit owed.
Behavioral proof: the two `normalize_input_value` GlobalID tests re-run
green this run (2/2, execution-verified); wrong-type rejection, the
empty-id live trio, and strategy round-trips stand on existing oracles
(static-reviewed). Negative control: none — no bypass threat exists
when validation lives in exactly one definition.

### F2: trio coupling — filter `from_id` vs `decode_global_id` (NO VERDICT)

Trace contribution for item 10 (`globalid-decode-trio`): filter decode
resolves against a BOUND definition and raises coded GraphQLError with
index + a code-less mismatch; `decode_global_id` resolves against the
GLOBAL registry and raises uniform ConfigurationError; filter rejects
an empty node_id only (empty type_name falls to mismatch/fallback),
node-decode rejects both slots. The composition verdict belongs to item 10.

## Defects

None. Empty-type_name fallback acceptance is within the spec'd
node-id-only contract, and object-path slot hardening is absent by
trust-boundary (objects are consumer-constructed; wire input is `str`-only).

- D-W2-1 (Worker-2): `filters/sets.py::FilterSet._normalize_input` docstring
says normalize maps `relay.GlobalID` -> `node_id` (sets.py:3041), but
`normalize_input_value` returns the base64 wire string since the re-encode
(inputs.py:810-817 owns the change; spec-027 D4 pins re-encode, not
pre-decode). Stale on HEAD-clean lines, no concurrent dirt. Owner:
filters/sets.py docstring. Non-blocking (zero-edit item).

## Pending execution

None.

## Judgment

Zero-edit: the halves share only upstream-owned grammar plus a
single-expression predicate; validation lives in exactly one definition.
Reject with triggers; the trio question rides item 10.

## What shrinks

Rule: filter GlobalID input shaping (encode half) + acceptance/validation
(decode half). Change: none — rejected as complementary contracts (F1);
trio composition recorded without verdict for item 10 (F2).
Owner before/after: shaping stays `_encode_global_id_input`
(filters/inputs.py:801); validation stays `_decode_and_validate_global_id`
(filters/base.py:971).
Net lines: 0 package, 0 tests, 0 specs. Machinery attestation: no new
helper, wrapper, constant, or edit of any kind — the live tree carries
only this artifact.
Attribution: no source path touched, so no ledger/hunk attribution is
owed; the item-1 FRAMEWORK comment (base.py:87-96) and item-2 owner were
read but not modified; the workspace copy was never written (no
source-mutating run needed).
Freshness (HEAD `c37a08a0`, ITEM_BASELINE `660be6d1`): `filters/inputs.py`
`4114d171`, `filters/base.py` `137ea59f`, `types/relay.py` `f3673a1b`,
`relay.py` `edfa8d6d`, `filters/sets.py` `befa6d92`,
`tests/filters/test_inputs.py` `9e69f40e`, spec-027 `a73f8674`, spec-031
`6d526739`; population 118 tracked package files; contract sources
spec-027 Decision 4 + spec-031 Decision 13; focused run 2/2 green
(`heavy uv run pytest
tests/filters/test_inputs.py::test_normalize_input_value_encodes_globalid_object_to_wire_form
tests/filters/test_inputs.py::test_normalize_input_value_global_id_list -n0
--no-cov`).
Index rows for Worker-0: `filter-globalid-encode-decode-pair` → rejected
(trigger: a third GlobalID-input pipeline position; trio coupling rides
`globalid-decode-trio`).

## Independent verification (Worker-2)

Trace committed BEFORE reading ## Findings (lines 51-90 unread; all else source-derived):

Sites+roles (own): `_encode_global_id_input` (inputs.py:801) DEFINITION
(shaping: object->wire via upstream `to_base64`, else passthrough); `_gid`/:707
+`_gid_multi`/:704 arms consumers, `normalize_input_value` driver, sets.py:3137
sole production caller. `_decode_and_validate_global_id` (base.py:971)
DEFINITION (validation: accept->strategy->name->empty->pk-coerce); both
`filter()` bodies (:1154/:1285) enforcement consumers; `_target_definition_for`
+`resolve_globalid_target_definition`+`_accepted_globalid_type_names`
sub-definitions of the one rule. Upstream `to_base64`/`from_id`/`str` external
grammar (Strawberry-owned, uncounted). `decode_global_id` (types/relay.py:856)
trio-adjacent, read for context only. Oracles: test_inputs.py (wire-form),
test_base.py (decode contract), test_library_api.py (live INVALID pins) —
all spell own expectations, none reads the owner.
Challenges (own counts): C1 wire-shape -> 0 own defs (upstream owns; package
calls by name). C2 drop-objects implausible AGREE (spec-027 "Accepts both raw"
+ test pins); third shape -> decode body only (1), encode forwards unknowns
by contract -> no 2-logic change. C3 type-preservation -> 1 (decode check;
encode re-encode is 0 own logic, one upstream call). C4/C5/C6 empty/codes/
strategy+coerce -> 1 (decode). C7 filter-via-`decode_global_id` -> envelopes
(GraphQLError vs ConfigurationError) + subjects (known target vs resolved
candidate) + empty-slot postures differ -> item 10, no verdict here.
Predicate `isinstance(...,GlobalID)` x6 (encode/decode/trio-gate/
_coerce_node_id/write x2): bodies diverge (wire/object/strip/model-decode),
spelling is the upstream-class test, carries no logic -> below bar AGREE.
Str-vs-object asymmetry load-bearing AGREE: pre-form shaping must not reject
("42" passthrough pinned) while post-form validation fail-closes; a shared
spine needs a mode flag (barred machinery).
Owner (own): no move — shaping stays inputs.py (input-shaping module beside
the dispatch it serves), validation stays base.py (filter-behavior module
beside its consumers + checks).
Candidates hunted, all negative: shared accept/parse spine (opposite
directions + pipeline positions); `from_id` pair merge (item-10 envelopes/
subjects — recorded there, not here); `_gid` vs `_pk` arm merge (element
contracts differ; the shared TABLE already single-owned via
`_FILTER_INPUT_KIND_TYPES`+zip). Census re-derived: 118 tracked .py
(`git ls-files`; 121 on disk = +3 untracked concurrent, grep covers WT so no
missed site); executable GlobalID-grammar sites exactly encode :820 +
`from_id` x2 (:1030, relay:922); keyset/connections are different grammars
(prefix+payload); testing `str(GlobalID)` mint == `to_base64` (verified
`__str__` delegates in venv source), equality pinned by the cited tests.
Matrix discharged (own): 1 write decodes compose by name (DecodeResult),
orders `normalize_input_value` disjoint signature, no mirror; 2 pure sync,
one body both colors, N/A; 3 upstream spellings one call, count 0; 4 this
item; 5 spec-027 D4 + spec-031 D13 pin, oracles uncounted; 6 scalar +
per-element both decode, pk/choice take no GlobalID by contract, node/write
ride item 10 — no gap. Scoped diff vs ITEM_BASELINE over
package/tests/examples EMPTY (verified); live blobs + spec blobs all match
What-shrinks fingerprints; zero tests touched (verified).
Reconciliation vs ## Findings (read after trace commit): F1 contract, sites,
counts, predicate verdict, asymmetry, owner all CONVERGE pre-read — no delta.
Two supplements, no conflict: convert `str`/`list[str]` annotations as
consumers (agree: declare the shaped type, implement nothing); my isinstance
census x6 vs F1's arms (superset, same below-bar verdict — bodies diverge
further). Nit, no action: "spec-027 D4 + tests = oracles/projections" lumps
roles (spec is the contract projection, tests the oracles). F1 difference
(enforces-nothing vs enforces-everything) + trigger (THIRD pipeline position)
both concrete and firable (grep-able position count). F2 contribution verified
clause-by-clause against both bodies; no-verdict-here CORRECT — the trio
verdict is item 10's dispatched question. Proof: W1's 2/2 re-run green by me
independently (execution-verified); static-reviewed remainder fits zero-edit
(existing oracles, nothing deferred) → Pending-execution None STANDS. AGENTS
prose: raw :NN allowed in dry-*.md; link scaffold 10/10; no provenance; ruff
N/A (touched paths: this artifact only; W1 touched none). Verdict: verified.

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
