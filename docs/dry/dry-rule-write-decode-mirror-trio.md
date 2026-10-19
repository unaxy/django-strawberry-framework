# DRY review: `write-decode-mirror-trio`

Status: verified
Run: 0.0.15 2026-10-12-29

## System trace

One decode grammar with per-flavor adapters — already the shape.
`utils/write_values.py` owns the request-time spine (structural check,
single/batched visibility decodes, container guard, scalar leaf, handler
factories, kind-routed walk); the three resolvers hold thin adapters
(null/skip policy, projection, dests) composing it by name. Every mechanism
below counts 1 definition. Zero-edit REJECT; plan rows 586/1473/1558 CONFIRM.

| Mechanism | Owner, 1 def | Adapters |
|---|---|---|
| Structural id check | `write_values.py::type_check_relation_id` | single + set spines call it |
| Single-object decode | `write_values.py::decode_visible_relation` | form + serializer 1-call colorings |
| Batched set decode | `write_values.py::decode_visible_relation_ids` | model single wrap, model multi, serializer multi |
| Container guard | `write_values.py::materialize_relation_id_container` | form multi + set spine |
| Scalar leaf | `write_values.py::decode_scalar_leaf` | model compose + `scalar_into` (form, serializer) |
| Walk + handlers | `write_values.py::decode_provided_fields` + `decode_field_handlers` | 3 top walks; model uses lower `*_into` |
| Error leaves | `errors.py::relation_field_error` + `null_field_error` | all flavors; 8 production sites, 1 ctor each |
| GlobalID halves | `relay.py::_decode_and_coerce` | single primitive + batched set decode |
| Wire parse | `types/relay.py::decode_global_id` | upstream grammar, consumed not mirrored |

## Verification

### Matrix

1. Cross-flavor: the item itself — all 3 flavors + auth register rider traced; spine single, adapters distinct (F1-F8).
2. Sync/async: no async twin of any decoder; decode runs in the one sync body under one `sync_to_async` boundary by design.
3. Derived knowledge: `related_model`/`graphql_name`/`target_name` recorded on specs at bind (item 1 owns build), read by name; no re-derivation.
4. Round-trip: encode side is bind-time (item 1); `coerce_lookup_id` (locate) and relation decode (attach) share `decode_model_global_id`, mappers differ; offset/keyset cursor codecs are other grammars.
5. Other media: specs 036/038/039 prose, spelled-message oracles (live + package), owner docstrings; oracles spell literals, never read the ctors.
6. Omission: every flavor handles whole-None + element-None to a field-keyed envelope (P1, 0 queries); no member lacks an applicable guard.

### Enumeration

Instrument: `rg 'def (_decode|decode_|type_check|materialize_relation|coerce_relation)'` over the package = 24 defs; every hit lands above (9 owners), in a flavor adapter (F1-F8), or in an excluded grammar (filter post-form validation, node-field raising wrappers, cursor codecs).

### Challenges

- C1 new relation shape: dispatch is map-driven (`handlers.get(kind)`); shared default gains 1 arm, model holds a 1-line dest declaration. Count 1.
- C2 new id encoding: wire parse 1 def, decode/coerce half 1 def (`_decode_and_coerce`), raw-pk coerce 1 def; flavors 0 edits. Count 1 per layer.
- C3 new error code: 1 ctor per leaf; M2M-null + nested messages have no twin. Count 1 each.
- C4 nested-write depth: `_decode_input_object` + `_decode_nested` serializer-only, no second site. Count 1.
- P1 None-matrix probe (9 direct calls, 0 queries): form defers None, model decides None, serializer defers whole-None but its multi errors on None elements; each arm field-keyed. Execution-verified; run id under Freshness.

## Findings

### F1 `write-decode-single-composition` — REJECT

Contract: one relation id to the flavor's bound value, visibility-checked. Model wraps 1-list through the set decoder (same contract as its M2M sibling); form/serializer ride the object spine with skip/project adapters. Unifying removes no definition (both spines must exist) and reshapes SQL (`IN` vs `=`). Sites: D: the 2 spines; C: 3 singles; O: live hidden-relation tests per flavor; P: adapter docstrings. Proof: static-reviewed. Trigger: a single spine serving pk-assignment + object-projection without a mode flag.

### F2 `write-decode-multi-composition` — REJECT

Contract: id list to bound values, one visibility verdict. Model + serializer share the batched set decoder; form maps the shared single per element because it needs the object for `to_field_name` (recorded at the owner). A batched object-returning spine would be new machinery for zero relief. Sites: D: set spine + shared single; C: 3 multis; O: spine unit tests + live M2M tests. Proof: static-reviewed. Trigger: an independently-motivated batched object query.

### F3 `write-decode-walk-dest-policy` — REJECT

Contract: route provided fields by kind into bound-data dests. All three tops ride `decode_provided_fields`; form/serializer share `decode_field_handlers`, model composes lower `*_into` primitives for its split dests + `EXCLUDED` capture (recorded at the factory). The 1-line `_decode_serializer_data` entry keeps its top-specs boundary responsibility. Sites: D: walk + factories; C: 3 tops + auth register via model. Proof: static-reviewed. Trigger: model dest policy converging with the shared default.

### F4 `write-decode-null-policy` — REJECT

Contract: None handling per position. Four distinct contracts in 1-3 lines each: model decides at decode (clear vs `null` error; M2M "send an empty list"), form defers to bound-form `empty_values`, serializer defers whole-None to `is_valid`, nested passes None through. Sharing is a mode flag. Whole-None is wire-reachable; None elements are wire-unreachable (`list[X]` elements non-null) and each side stays field-keyed (P1). Sites: D: 4 policies at adapters; O: live null tests + P1. Proof: P1 execution-verified. Trigger: one documented None philosophy for all flavors.

### F5 `write-decode-scalar-leaf` — REJECT

Contract: choice-unwrap then Unicode preflight. `decode_scalar_leaf` single-owned; model extras (explicit-null rejection, naive-datetime coercion) are model-only — form/serializer defer to `is_valid` — with no second site. Sites: D: leaf + 2 model extras; C: model scalar + `scalar_into`. Proof: static-reviewed. Trigger: a second flavor needing decode-time null/datetime decisions.

### F6 `write-decode-error-shaping` — REJECT

Contract: bad input to field-keyed `FieldError`, no existence leak. Single ctors; all 8 relation rejections route through one helper; the M2M "empty list" message is deliberately not `null_field_error` (recorded); nested "list/object" errors are serializer-only. Sites: D: 3 ctors + 3 singleton messages; O: spelled-message oracles live + package. Proof: static-reviewed. Trigger: a second producer of any shaped message.

### F7 `write-decode-nested-recursion` — REJECT

Contract: nested input objects to nested serializer-keyed dicts with dotted paths. Serializer-only; `_decode_nested` materializes its own list because its subject (objects), error ("Expected a list of items"), and None-item passthrough differ from the relation container guard — composing it would mislabel failures. Sites: D: `_decode_input_object` + `_decode_nested`; no twin. Proof: static-reviewed. Trigger: nested inputs on a second flavor.

### F8 `write-decode-globalid-coercion` — REJECT, converges with open f63

Contract: GlobalID to real pk. Decode/coerce half single-shared; the single-vs-batched resolve pair is the confirmed count-2 of blocked family `write-pipeline-alias-recovery` (f63, same hunks) — converged, no new row, untouched. Locus and top-locate mappers consume the same primitive with caller-specific error shapes. Proof: static-reviewed + f63 record. Trigger: f63's landing, which re-points both resolve arms at once.

## Defects

None. The direct-call-only None-element divergence (F4) has no contract source requiring agreement and every arm returns a field-keyed envelope with zero queries.

## Judgment

The trio is one grammar with per-flavor adapters, not three contracts — and it already is. No plausible change forces edits at 2+ definitions carrying real logic; every unification on offer is a wash (F1), a mode flag (F3, F4), or new machinery (F2). All eight sub-rules reject with triggers; f63 keeps the resolve pair.

### Freshness

- `8710bfa94692d8e210542d1125aff89680272507` `django_strawberry_framework/mutations/resolvers.py`
- `bb12a611b4dd8e4dc024e21fb6c20fdf36a25e73` `django_strawberry_framework/forms/resolvers.py`
- `274610bf9caa0a1c692a986f01b3bd69224d2e74` `django_strawberry_framework/rest_framework/resolvers.py`
- `947325a40405c80ec34261875a8b8b2efc2e2cd0` `django_strawberry_framework/utils/write_values.py`
- `ddec038a370f6e62acba029c0e0ddd9c43e428f2` `django_strawberry_framework/utils/errors.py`
- `edfa8d6ddb5694cc347e1b8838c0852dd56f689f` `django_strawberry_framework/relay.py`
- Read-only context (named, not pinned): `utils/querysets.py`, `utils/inputs.py`, `auth/mutations.py`, specs 036/038/039.
- P1 probe: `dry-20261012T144724-5f55f2`, copy digest `sha256:423e64b7…`, exit 0, 0 queries; shared tree unmoved since copy sync; HEAD `c37a08a0`.

## Independent verification (Worker-2) — pre-Findings trace (recorded before opening `## Findings`)

Disclosure: header-map grep + 5 artifact lines via package search (System-trace rows, one F5 line) seen before writing; all positions below fixed first by own source reads/greps. No Findings body read.

Spine D (`utils/write_values.py`, each 1 def): `unencodable_text_error`, `raw_choice_value` (+`_raw_choice_scalar`), `coerce_relation_pk_or_none`, `type_check_relation_id`, `decode_scalar_leaf`, `decode_visible_relation`, `materialize_relation_id_container` (+`RELATION_ID_ATOM_TYPES`), `decode_visible_relation_ids`, walk/store vocabulary (`store_decoded`, `decoded_into`, `scalar_into`, `file_into`, `relation_into`, `decode_field_handlers`, `decode_provided_fields`). 9 mechanisms x1.
Adapters — model (`mutations/resolvers.py`): `_decode_relations`, `_decode_single_relation_id`, `_decode_relation_id_list` + `_explicit_null_error`, `_make_aware_if_naive`, `_relation_null_error`. Form (`forms/resolvers.py`): `_decode_form_relation_single`, `_decode_form_relation_multi`, `_decode_form_data` + `_to_form_key_value`, `_is_empty_form_value`. Serializer (`rest_framework/resolvers.py`): `_decode_relation_single`, `_decode_relation_multi`, `_decode_serializer_data`, `_decode_input_object`, `_decode_nested` (own count 5; dispatch `x2` undercounts — it names only the walk pair).
Consumers: `_model_decode_step`, `_modelform_decode_step` (+`_reconstruct_partial_data`), `_serializer_decode_step`, `run_write_pipeline_sync` skeleton, `make_resolver_entries` (one sync body; async is `sync_to_async` — no twin), auth login/register riders (`unencodable_text_error` by name). Oracles: `tests/utils/test_write_values.py`, `tests/mutations/test_resolvers.py`, `tests/forms/test_resolvers.py`, `tests/rest_framework/test_resolvers.py`, live `test_library_api.py`. Projections: module docstrings, specs 036/038/039, `utils/errors.py` leaves.
Challenges (each count = definitions forced): C1 leaf order → 1 (`decode_scalar_leaf`); C2 list unwrap → 1 (`raw_choice_value`); C3 preflight text → 1 (`unencodable_text_error`, auth consumes); C4 new id shape → 1 (`type_check_relation_id`); C5 single-compose order → 1 (`decode_visible_relation`; form/serializer singles are 1-call skip/project colorings); C6 batch/visibility shape → 1 (`decode_visible_relation_ids`; model single-wrap + model/serializer multis call it; form multi maps single per element for `to_field_name` — distinct object tail, not a second batch def); C7 atom/container rule → 1 (`materialize_relation_id_container`, called by both multis); C8 new kind/walk → 1 (`decode_provided_fields` + `*_into` factories; riders declare dest only); C9 one flavor's null rule → 1 (that adapter; no shared null def — model reject vs form `empty_values` clear vs serializer `None` passthrough are wire-distinct); C10 nested → 1 (serializer-only); C11 relation message → 1 (`relation_field_error`; `_relation_null_error` is a distinct M2M message, not a second relation def); C12 NodeID mapping → 1 per stage at `relay.py` (spine consumes; converges with blocked f63 alias-recovery, untouched).
Closest unifications considered, all below bar: form multi onto batched set (needs object for `to_field_name`; 2-query re-fetch + precedence change = observable query effect, principle 8); model single onto single-spine (forks FK off the M2M batched contract it deliberately shares); null-policy merge (changes wire acceptance); model extras into leaf (forces form/serializer to inherit model validation). Owner I would choose: spine stays `utils/write_values.py` (narrowest all flavors can import; `mutations/resolvers.py` would reverse the dependency), leaves in `utils/errors.py`, visibility in `utils/querysets.py`, GlobalID taxonomy in `relay.py`, skip/project/dest/null at flavor adapters. No new machinery.

## Independent verification reconciliation (Worker-2) — verdict `verified` (plain)

Reconciliation (every difference vs pre-trace): grouping (own unencodable/raw/coerce/leaf/single/materialize/batch/walk cut vs W1 structural/single/batch/container/leaf/walk/errors/GlobalID/wire cut) — same 1-def mechanisms, no count differs; serializer 5 vs dispatch x2 — W1 F1-F3+F7 cover all 5, dispatch shorthand only; null 3-vs-4 — accept W1's finer cut (nested None is a 4th, 1 each); scalar/error/nested splits — same counts, and W1 F7's nested-list-vs-relation-container distinction (verified: own `list()` + "Expected a list of items." + None-item passthrough vs container guard) strengthens the reject; challenges map (W1 C1/C2/C3/C4/P1 ≈ own C8/C4+C12/C11/C10/C9; own C5-C7 add granularity, all count 1); owner identical. Matrix 1-6 confirmed on the merits (auth riders traced; one sync body, no twin; specs read by name, form avoids `queryset.model`; `coerce_lookup_id` vs relation mappers share the primitive with caller-specific shapes, cursor codecs other grammars; oracles spell `field`/`codes` literals, stub `field_error` uses only; P1 contains axis 6). Diff empty confirmed (`git diff` baseline→WT over the 4 targets empty; log empty; artifact the only new file; plan delta is Worker-0 dispatch). Freshness: all 6 blobs re-hashed identical. F8 accurate: `_resolve_real_pk` :315-:323 + `_resolve_real_pks_batched` :404-:406 match f63 WT lines exactly, f63 `verified` blocked-on-hunt pending execution, zero edits so untouched — no new row owed. P1 suffices and reproduces: log + script read, re-ran in own copy (`dry-20261012T145729-1f5bcc`, same digest, fresh, shared unmoved) byte-identical (10 rows, 0 queries, exit 0) — proves containment (no exception, 0 queries); arm mapping is source-evident 1-3-line adapters. No oracle rewritten (tree untouched). AGENTS.md prose clean (run id in Freshness sanctioned; `path::Symbol` basename form; no tests owed); ruff check/format on the .md pass trivially; layout script excludes this path (0 violations). `## Pending execution` absent: COMPLIANT per DRY.md "Absent when none" (no deferred proofs; static apt for composition-by-name; P1 verified needs no entry) — run-20/24 precedent, not a shape violation. Independent consolidation search: none found; closest unifications (pre-trace) all below bar. Record slips, verdict-neutral, no W1 rework: S1 Enumeration 24→26 (same instrument; all 26 home: 11 owner hits + 11 adapters + 4 excluded); S2 P1 "9 calls"→10 rows (materialize setup row); S3 F4/Defects "every arm returns a field-keyed envelope" overstates the 4 deferral arms (`(value, None)`) — accurate: each arm field-keys at decode or defers to its own validator, 0 queries, never top-level; reject stands (wire-unreachable divergence, no contract source). 0 package defects; `## Defects` "None." stands.

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
