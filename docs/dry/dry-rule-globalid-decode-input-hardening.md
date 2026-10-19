# DRY review: `globalid-decode-input-hardening`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `globalid-decode-input-hardening`. Provisional owner
`django_strawberry_framework/types/relay.py::decode_global_id` (input gate +
slot normalization; confirmed, not inherited). Member sites:
`django_strawberry_framework/types/relay.py` (the gate) and
`django_strawberry_framework/filters/base.py::_decode_and_validate_global_id`
(the site the plan index notes lacks both). Prior records only as triggers:
the two verified GlobalID families (`typed-globalid-decode`,
`relay-node-name-decode` — each composes `decode_global_id` by name;
every composition edge below re-derived from the bodies, nothing inherited).
Never read any `worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds no row on either
member path (rows cover only `optimizer/walker.py`, two fakeshop live files,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`, `registry.py`, root `relay.py`) — confirmed by
full read. Both member files are worktree-clean and byte-identical to
`ITEM_BASELINE` (`059e3f27234851e1eb6023408364a56175b970e6`) and to `HEAD`
(`bfaee91d`): `git diff <baseline> -- <both paths>` is empty. Dirty paths
elsewhere (`filters/inputs.py` concurrent range-shape hunk,
`docs/dry/` concurrent artifacts) were read-only; every line cited in
`filters/inputs.py` (`_encode_global_id_input`, lines 659-679) sits outside
its concurrent hunk (`@@ -772,18 +772,49 @@`, verified by diff). No dirty
path was edited, so no STOP arose. Zero tracked edits; this artifact (new,
untracked) is the only write.

## System trace

**What the hardening IS** (read from the `decode_global_id` body,
[relay-types][relay-types] lines 742-783; seven arms, each oracle-pinned):

1. **Input gate.** `not isinstance(gid, (relay.GlobalID, str))` →
   `ConfigurationError` naming the received type via `_safe_type_name`.
   Rejects `None`, `int`, `bytes`, arbitrary objects, lazy objects — before
   any parse. Oracles: `test_decode_non_str_input_raises` (`None`, `42`,
   `object()`, `b"bytes"`), `test_decode_hostile_input_type_name_stays_typed`
   (hostile metaclass `__name__` contained by the safe renderer).
2. **Raw-string normalization.** `raw_gid = str.__str__(gid)` — a `str`
   subclass's hostile `__str__` / `__format__` cannot escape the parse or
   the diagnostic. Oracle: `test_decode_hostile_string_subclass_stays_typed`.
3. **Contained parse.** `relay.GlobalID.from_id(raw_gid)`, catching the
   `ValueError` superset (covers Strawberry's `GlobalIDValueError`).
   Oracle: `test_decode_malformed_base64_raises_configuration_error`.
4. **Slot-read guard.** `decoded.type_name` / `decoded.node_id` read inside
   `try/except BaseException` → `ConfigurationError("fields could not be
   read")`. Oracle: `test_decode_hostile_globalid_slots_stay_typed`.
5. **Non-string slot reject.** Either slot not a `str` →
   `ConfigurationError("fields must be strings")`, before truthiness.
   Oracle: `test_decode_globalid_rejects_non_string_slots`.
6. **Slot normalization.** Both slots re-read through `str.__str__` so a
   hostile slot `__str__` cannot escape splitting or registry lookups.
7. **Empty-slot reject.** Either slot empty → `ConfigurationError("empty
   slot")` (`from_id` does not enforce; the encoder never emits empties).
   Oracles: `test_decode_empty_type_name_raises`,
   `test_decode_empty_node_id_raises`.

Answers to the item's exact questions: non-string input — rejected (arm 1);
wrong shape (bad base64 / no colon) — rejected (arm 3); extra slots
(`"a:b:c"` → `node_id "b:c"` via upstream `split(":", 1)`) — accepted
identically at both sites, owned by neither (upstream parse, challenge C4);
null bytes — no dedicated check exists at either site (grep for null-byte
vocabulary over both files: zero hits outside an unrelated SQL-`NULL`
docstring); a null-bearing slot fails downstream as unresolvable /
mismatched, not at a dedicated guard (challenge C5).

**WHERE it applies.** `decode_global_id` is composed by name at exactly two
production call sites (re-censused, whole package): root
[relay][relay]`::_decode_or_graphql_error` (line 117, collapsing every
`ConfigurationError` to wire `GLOBALID_INVALID`) and root
[relay][relay]`::decode_model_global_id` (line 318, shape-only stage of the
write pipeline), plus the public same-function-object re-export
[testing-relay][testing-relay]`::decode_global_id`. Its docstring names
exactly these three call paths ("arbitrary client-controlled input ... ONE
uniform `ConfigurationError`") — the filter is not among them. Production
`from_id` census: exactly two calls package-wide — the gate's own
([relay-types][relay-types] line 751) and the filter's
([filters-base][filters-base] line 770). `str.__str__` census: four hits in
`types/relay.py`, zero in `filters/base.py`.

**The filter site today** ([filters-base][filters-base] lines 766-849).
`isinstance(value, relay.GlobalID)` short-circuits the parse, else
`from_id(value)` catching only `ValueError`. No input gate, no slot-read
guard, no non-`str` slot check, no slot normalization. What each wire input
does (execution-verified probe P1, thirteen distinct cases; agreed paths
D1/D2 malformed and E2 empty-id reject coded at both sites):

- Scalar garbage (`42`, `b"bytes"`): coded `GraphQLError GLOBALID_INVALID`
  — contained, but by upstream `from_base64`'s `except Exception →
  ValueError` chain, not by an owned gate (probes A3, F2).
- Hostile-slot `GlobalID` object (slot read raises): raw `RuntimeError`
  leaks (probe B2; `decoded.node_id in EMPTY_VALUES` at line 823 is the
  read that detonates). `decode_global_id` contains the same object (B1).
- Non-`str` slot (`type_name=123`), unbound owner: silently returns the
  node id (probe C2) — the specified node-id-only fallback, not a reject.
  `decode_global_id` rejects the same object (C1).
- Empty `node_id`: coded `GLOBALID_INVALID` with the widen-guard rationale
  (E2; scalar and multi paths, index named). Empty `type_name`: the
  code-less mismatch error (fails the accepted-set membership), never the
  empty-slot error — both reject, with different errors by design.

**What wire input reaches the filter.** The real pipeline delivers `str`
only: GraphQL `String`/`ID` coercion yields plain `str`, and
[filters-inputs][filters-inputs]`::_encode_global_id_input` (lines 677-678)
re-encodes a direct-Python `relay.GlobalID` object back to its base64 wire
string upstream of the filter so the bound filter always runs the canonical
decode-and-validate path. The `isinstance(value, relay.GlobalID)` branch
serves direct-Python callers (and the `test_filter_model_strategy_accepts_
predecoded_global_id` oracle) — the same population that can hand the
filter a hostile-slot object. Over-the-wire hostile subclasses cannot
arrive: nothing upstream of the filter mints them.

Connected sources read: both member bodies in full; root [relay][relay]
(decode consumers, error collapse, typed pipeline seam);
[filters-inputs][filters-inputs] (wire-form normalization);
[testing-relay][testing-relay] (re-export identity); [spec-031][spec-031]
Slice 3 + Decision 8 (decode resolve-then-enforce + the four
input-containment cases pinned against `decode_global_id`) + Decision 13
(filter strategy-aware validation, UNVALIDATABLE backstop, retained
unbound node-id-only path); [spec-027][spec-027] (filter accepts raw `str`
and `GlobalID` objects, closed reject list: malformed, empty-id, mismatch,
per-element index); glossary `Meta.globalid_strategy` anchor (encode-only
strategies fail closed on filters); both oracle files' hostile/containment
rows (bodies opened, independence confirmed: plain literals, no owner
reads). Excluded on strength of body: every other package module (zero
`from_id` / `decode_global_id` / `_decode_and_validate_global_id`
vocabulary over the whole-package sweep). Installed strawberry-graphql
`0.324.0` read as contract anchor (`from_id` → `from_base64`, `except
Exception → ValueError`, `split(":", 1)`), not a fingerprinted input.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Read path (node fields), write path
   (`decode_model_global_id`), and filter path inventoried. Write composes
   the gate by name; filter runs its own parse with its own error surface
   — different contracts (Findings), not a mirroring gap.
2. **Sync/async twins.** Decode and filter validation are sync string/dict
   work; no async twin exists at either site and none is owed.
3. **Derived rather than repeated knowledge.** The wire parse is upstream's
   (`from_base64`, zero owned copies); resolve-then-enforce is owned once
   by `decode_global_id`; the accepted-set is owned once by
   `_accepted_globalid_type_names`, derived from the single
   `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` memberships by name
   (`FRAMEWORK_GLOBALID_STRATEGIES` is a union, not a re-typing).
4. **Inverse / round-trip pairs.** Encode (`encode_typename`) vs decode vs
   filter-validate share the recorded strategy by name; three halves, one
   membership source. No second parse grammar exists to unify (C4: the
   parse itself is upstream's).
5. **Contracts restated in another medium.** Production (gate + validation);
   oracles (containment rows pin decode's arms; the filter's hostile-repr
   row pins its message assembly; all spell literals independently);
   projections ([spec-031][spec-031] containment list, [spec-027][spec-027]
   filter reject list, both docstrings verified against bodies).
6. **Enforcement by omission.** The item's shape. The filter lacks the gate
   + normalization, but no contract source extends the hardening rule to
   it (Findings F1/Q1): [spec-031][spec-031]'s containment cases are pinned
   against `decode_global_id`; [spec-027][spec-027]'s filter list is closed
   without subclass containment; the gate's owner prose names three call
   paths excluding the filter. Absence here is a routed question, never a
   verdict — no defect filed.

### Enumeration

Instrument: whole-package sweep for `from_id(`, `decode_global_id(`,
`_decode_and_validate_global_id`, `str.__str__` over all 117 package `.py`
(plan count; no adds/renames) + per-symbol def census + upstream body read.
Population complete; every member lands below.

- `decode_global_id` hardening (gate + arms 1-7): 1 definition
  ([relay-types][relay-types] lines 742-783). Consumers (listed, not
  counted): node-field boundary, typed write pipeline, testing re-export.
- Filter parse + validation: 1 definition ([filters-base][filters-base]
  lines 766-849). Consumers: `GlobalIDFilter.filter`,
  `GlobalIDMultipleChoiceFilter.filter` (per-element, index threaded).
- Upstream parse (`from_base64`): 0 owned (contract anchor only).
- Oracles: decode containment rows
  ([test-relay-interfaces][test-relay-interfaces] lines 2812-2911),
  filter hostile-repr row + empty-id rows + predecoded row
  ([test-filters-base][test-filters-base]).
- Projections: both docstrings, [spec-031][spec-031] Slice 3 / Decisions
  8+13, [spec-027][spec-027] filter adaptation block, glossary strategy
  anchor.

### Challenges

Counts are authoritative definitions of the hardening rule only;
consumers, oracles, projections listed, never counted. Probe P1 maps onto
C1-C3 (13 distinct cases `execution-verified`); C4-C5 `static-reviewed`
(upstream body + null-grep + agreed wire behavior).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New hostile scalar input class (lazy object, new numeric type) | **1** (the `isinstance` gate; filter arm needs 0 owned moves — upstream `except Exception` contains it to the coded reject, execution-verified A3/F2). |
| C2 | New hostile/non-`str` slot shape (raising descriptor, new scalar) | **1** (decode arms 4-6; the filter has no hardening definition — B2 leaks, C2 falls through to the specified fallback — the omission, not a second definition). |
| C3a | Permit empty `node_id` at decode | **1** (decode arm 7 only; the filter's `GLOBALID_INVALID` arm does not move — still rejects). |
| C3b | Filter treats empty `node_id` as no-op | **1** (filter arm only, against its widen-guard rationale + live oracles; decode arm 7 does not move). |
| C4 | New wire shape (second separator, new payload grammar) | **0 owned** (upstream `split(":", 1)`; both sites inherit identically). Boundary note, not a definition. |
| C5 | Null-byte slot policy | **0 owned** (no check at either site; rejected downstream as unresolvable/mismatched). Boundary note. |

**Experiments (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command with the copy as cwd via
`uv run --frozen --directory "$WS"`:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/globalid-decode-input-hardening-w1
uv run --frozen --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --frozen --directory "$WS" python probe_w1_hardening.py
```

Proof P1 (`PROBE-DONE`, all 13 distinct cases as analyzed in System trace):
A1/A2/F1 decode gate rejects; A3/F2 filter scalar garbage coded-rejects;
B1 decode contains hostile slots / B2 filter leaks `RuntimeError`;
C1 decode rejects int slot / C2 filter unbound silently returns node id;
D1/D2 malformed agreed-coded; E1/E2 empty-id both reject with
surface-specific errors. Status: `execution-verified`. Copy `__file__`:
`.../dry-ws/globalid-decode-input-hardening-w1/django_strawberry_framework/__init__.py`;
settings minimal-configured in-probe (`DATABASES` empty — no DB opened by
any case; all work is string/dict/exception). No source mutation; restores
N/A. No structural negative control was run: this finding proposes no gate
(see F1), so there is no enforcement to prove fail-capable — the probe's
B2/C2 divergence IS the demonstrated difference, and the standing oracles
that pin each side are named in Enumeration.

One authorized shared-tree focused run (zero member edits in flight):
`uv run pytest
tests/filters/test_base.py::test_decode_global_id_hostile_repr_still_raises_the_coded_error
--no-cov -n0` → 1 passed (the filter's existing hostile arm stays green at
`HEAD`).

## Findings

### F1 — filter composes the decode gate (REJECTED consolidation)

- **Contract + variation.** Client-controlled GlobalID input must fail
  closed. Varies on: entry surface (refetch/write/filter); error envelope
  (`ConfigurationError` vs coded `GraphQLError` vs `FieldError`);
  resolution root (registry primary vs owner-related target); bound vs
  unbound filter.
- **Sites + roles.** *Definition*: the gate + arms 1-7 in `decode_global_id`
  (1). *Separate definition*: the filter's parse + strategy-aware
  validation + pk coercion (1, different rule). *Composed primitive*:
  upstream `from_base64` (0 owned). *Consumers / oracles / projections*:
  as listed in Enumeration.
- **Challenges.** C1 → 1 (+0 filter); C2 → 1 (+0 filter — the omission);
  C3a/C3b → 1 each (intentional separation: per-change count never exceeds
  1); C4/C5 → 0 owned. Count > 1 nowhere in one rule: no duplication.
- **Owner + lifetime (principles 7, 4).** No ownership change.
  `decode_global_id` keeps its gate (its contract — uniform
  `ConfigurationError` for its three named call paths — is decode-specific;
  every legitimate consumer already depends on it without reversing a
  dependency). `_decode_and_validate_global_id` keeps its validation (the
  owner-target resolution, accepted-set, pk coercion, and unbound fallback
  are meaningless outside the filter contract). Stored-derivation
  lifetime: there is none at either site — both are pure per-call (no
  cache, memo, or index); validity key = the registry/finalizer lifecycle
  both read live; nothing to invalidate.
- **Migration.** None — nothing moves. Adding the missing guard would
  change what is accepted (B2 `RuntimeError` → coded reject; C2 silent
  accept → reject): explicitly never "behavior-preserving".
- **Distinct behavior (stays separate).** D-a: different resolution roots —
  the filter validates against the owner's related target (the
  [spec-027][spec-027] strict exact-type-name multi-owner match), decode
  resolves via the registry primary; composing decode Step 1 into the
  filter would validate secondary-type owners against the primary's name.
  D-b: different error surfaces — composing decode's `ConfigurationError`
  into the filter path rewrites wire errors (`GLOBALID_INVALID` /
  `UNVALIDATABLE` / code-less mismatch). D-c: the unbound node-id-only
  fallback ([spec-031][spec-031] Decision 13, retained by design) has no
  decode counterpart. D-d: different wire grammars in practice — the filter
  path receives upstream-normalized wire strings
  (`_encode_global_id_input`); decode's gate serves arbitrary
  client-controlled input including direct-Python shapes.
- **Behavioral proof.** `execution-verified` for the gap's exact shape
  (P1: B2 leak, C2 fallback-accept, A3/F2 scalar containment, D/E
  agreement) + the one authorized shared-tree test. `static-reviewed`
  for C4/C5 (upstream body, null-grep), oracle-body independence, and
  the resolution-root difference (both bodies opened).
- **Structural gate.** None owed, with proved reason: a rejection proposes
  no enforcement to pin. Unity rests on the `from_id` census (exactly 2
  production calls), the `str.__str__` census (4 vs 0), and triggers
  T-compose / T-errors / T-fallback below.
- **Coupling.** None. Adjacent open families untouched; zero edits.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `types/relay.py` `52439862…`, `filters/base.py` `ba52351c…` (both equal
  to `HEAD` and to `ITEM_BASELINE` blobs — member diff vs baseline empty),
  `filters/inputs.py` `06797dc7…` (concurrent range-shape hunk; cited
  lines 659-679 verified outside `@@ -772,18 +772,49 @@`),
  root `relay.py` `69085e7a…`, `testing/relay.py` `df0dc72a…`,
  `tests/filters/test_base.py` `04da73cd…`,
  `tests/types/test_relay_interfaces.py` `26fb2ccf…`,
  `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` `45f43dfe…`,
  `docs/SPECS/spec-027-filters-0_0_8.md` `ca463bdd…`,
  `docs/GLOSSARY.md` `bc51debc…`. `HEAD` `bfaee91d`; `ITEM_BASELINE`
  `059e3f27…` present. Installed strawberry-graphql `0.324.0` read as
  contract anchor, not a fingerprinted input. Searched population: whole
  package (117 `.py`). Any fingerprint change reopens the finding.
- **Reconsideration triggers (recorded here and, if the maintainer orders the work,
  at the filter owner).** T-compose fires if filter type-name validation
  ever resolves via the registry primary instead of the owner target (the
  D-a difference dissolves — recompose then). T-errors fires if the filter
  ever surfaces `ConfigurationError` instead of coded `GraphQLError`.
  T-fallback fires if the unbound node-id-only path is removed (D-c
  dissolves). Durable homes: this finding and the plan's `## Outcomes`
  via Worker 0.

### Q1 — the maintainer question: should the filter gain equivalent hardening as new behavior?

Not decided here (ambiguous contract, per the axis-6 rule). The question
for Worker 0 to route: extend the input-gate + slot-normalization rule to
`_decode_and_validate_global_id` (new behavior on a card, never this item).

- **Evidence for:** probe B2 leaks a raw `RuntimeError` where every other
  filter seam fails closed with a coded error (the `ArrayFilter` /
  `ListFilter` / `IntegerInFilter` containment precedents show the
  package's direction, each with oracles); the shape is reachable through
  the filter's own supported input grammar (a `relay.GlobalID` object per
  [spec-027][spec-027] "accepts both raw").
- **Evidence against:** no contract source extends the rule — the
  [spec-031][spec-031] containment list is pinned against `decode_global_id`
  only, and [spec-027][spec-027]'s filter reject list is closed without it;
  the wire path cannot deliver hostile objects (GraphQL coercion mints
  plain `str`; `_encode_global_id_input` re-encodes objects upstream), so
  reachability is direct-Python-only; scalar garbage already fails closed
  via the upstream chain (A3/F2); C2's silent accept is the specified
  unbound fallback, not an oversight; and any added guard changes what is
  accepted — never behavior-preserving. Candidate owner if ordered (principle
  7): `filters/base.py::_decode_and_validate_global_id` — the validation
  contract lives there and both filter flavors already depend on it with no
  new imports. Lifetime if ordered (principle 4): pure per-call, not cached.

## Defects

None. Tracing found no contract break: every resemblance candidate resolved
to the F1 separation or to upstream-owned behavior. The B2 `RuntimeError`
leak is Q1 material, not a defect — no spec, glossary anchor, owner prose,
or oracle establishes the hardening rule for the filter member, and its
reaching input is direct-Python-only (the wire grammar cannot deliver it),
so the trust-boundary test for a defect is not met. No other bugs found
while tracing.

## Pending execution

- `proof:` none. P1 is `execution-verified` in the disposable workspace
  (command above, `PROBE-DONE`, copy `__file__` recorded, no DB opened).
- `gate:` `uv run pytest
  tests/filters/test_base.py::test_decode_global_id_hostile_repr_still_raises_the_coded_error
  --no-cov -n0` → 1 passed in the shared tree (zero member edits in
  flight; anchors the filter's existing hostile arm at `HEAD`).
- Full-suite gate business deferred to the final-gate item with reason: the
  entry authorizes workspace runs plus one focused `--no-cov` test, a green
  unmutated suite would discharge no failability proof for a rejection that
  proposes no gate, and `FAKESHOP_SHARDED=1` / Postgres cells are
  `inapplicable by construction` (every executed claim is string/dict/
  exception work with no database opened).

## Judgment

The hardening is single-owned by `decode_global_id` (seven oracle-pinned
arms); the filter runs a separate, contract-distinct validation it cannot
compose without breaking its owner-target resolution, its coded error
surface, and its specified unbound fallback. Consolidation rejected with
triggers; the hardening gap is a maintainer question (evidence both ways, no
decision); no defects; zero tracked edits.

## Independent verification (Worker 2)

Order note: this worker read the full artifact during discovery before
recording (ordering breach, stated honestly). The trace below re-derives
every claim from fresh body reads cited per arm, plus two upstream facts
W1 did not fingerprint; the reconciliation that follows lists each
agreement and difference explicitly.

### T2-1 — gate site, `django_strawberry_framework/types/relay.py::decode_global_id`

Def at line 686; hardening arms at lines 742-783 (each confirmed in the
body, not inherited):

1. Input gate (742-746): `not isinstance(gid, (relay.GlobalID, str))` →
   `ConfigurationError` naming the type via `_safe_type_name`.
2. Raw-string normalization (749): `raw_gid = str.__str__(gid)`.
3. Contained parse (750-756): `relay.GlobalID.from_id(raw_gid)` catching
   `ValueError`. Independently confirmed `GlobalIDValueError ⊂ ValueError`
   (MRO read from the installed strawberry `relay/types.py`), so the
   catch covers it.
4. Slot-read guard (760-767): `decoded.type_name` / `decoded.node_id`
   read inside `try/except BaseException` → `ConfigurationError`.
5. Non-`str` slot reject (768-772), before truthiness.
6. Slot normalization (777-778): both slots re-read through
   `str.__str__`.
7. Empty-slot reject (779-783).

Count: 7 arms — agrees with W1. Precision note: 3 `str.__str__` hits
live inside the function (749, 777, 778); the file-wide "4" includes
line 525 on the encode path, and `filters/base.py` has 0 file-wide.
Upstream facts independently verified in the installed strawberry
`0.324.0` equivalent: `from_base64` does
`base64.b64decode(value.encode()).decode().split(":", 1)` inside
`except Exception → ValueError` (so `42` dies on missing `.encode`,
`b"bytes"` on missing `.encode`, both contained without any owned
gate); `split(":", 1)` makes `"a:b:c"` decode to `node_id "b:c"`;
`GlobalID.__post_init__` rejects non-`str` slots at construction, so a
non-`str`-slot object needs exotic in-process construction (frozen
dataclass `object.__setattr__` or a hostile subclass), never a wire
shape. Null-byte grep over both member files: zero hits — no dedicated
check at either site, agrees with W1.

### T2-2 — filter site, `django_strawberry_framework/filters/base.py::_decode_and_validate_global_id`

Def at line 715; body lines 766-849 (confirmed in the body):

- 766: `isinstance(value, relay.GlobalID)` short-circuits the parse.
- 769-787: `from_id(value)` catching only `ValueError` → coded
  `GraphQLError` (`GLOBALID_INVALID`). No input gate, no raw-string
  normalization, no slot-read guard, no non-`str` slot check, no slot
  normalization — each absence confirmed by reading the body.
- 791-815: encode-only / lifecycle-defect backstop (`UNVALIDATABLE`).
- 816-822: accepted-set mismatch (code-less error). The `decoded.type_name`
  read at 817 is OUTSIDE any `try` — a raising descriptor detonates here.
- 823-836: `decoded.node_id in EMPTY_VALUES` then the empty-id coded
  reject. The `decoded.node_id` read at 823 is likewise unguarded —
  the detonation point W1 names.
- 837-848: pk coercion → `GLOBALID_INVALID`; 849: unbound fallback
  returns `decoded.node_id` (via the `None` accepted-set at 704-705).

C2 mechanism confirmed precisely: with an unbound owner, line 816
short-circuits (`accepted is None`), line 823 evaluates
`123 in EMPTY_VALUES` → `False`, `target_model` is `None`, line 849
returns the node id — silent accept, exactly as W1 states. With a bound
owner the same object takes the mismatch error instead (no silent
accept there).

### T2-3 — wire inputs reaching each site

Gate site: GraphQL `node(id:)` / `nodes(ids:)` args arrive as plain
`str` (graphql-core coercion); the write pipeline
(`relay.py::decode_model_global_id`, line 318) receives consumer input
values; direct-Python callers may pass anything, including hostile
shapes — which arms 1-7 contain.
Filter site: GraphQL filter variables are JSON → plain `str` only; a
`relay.GlobalID` OBJECT reaches the `isinstance` branch via
direct-Python callers only (spec-027 "accepts both raw"). The bound
filter path additionally runs `_encode_global_id_input`
(`filters/inputs.py` lines 677-678) upstream, which re-encodes a
`GlobalID` object via `relay.to_base64(value.type_name, value.node_id)`
with NO guard — a hostile-slot object detonates THERE first on the
normalize path, before `_decode_and_validate_global_id` is reached.
A hostile-slot or non-`str`-slot object is unmintable from JSON
variables: B2/C2 reaching inputs are direct-Python-only. TRUE —
W1's reachability claim holds, with the `_encode_global_id_input`
pre-detonation as an additional confirmed detail.

### T2-4 — sweep population (enumeration check, whole package)

- `from_id(` production calls: exactly 2 (`types/relay.py` line 751,
  `filters/base.py` line 770). Two further hits are docstring
  mentions (`filters/base.py` lines 13, 856), not calls. No third
  parse. Agrees.
- `decode_global_id(`: 1 def + 2 production call sites (`relay.py`
  lines 117, 318) + 1 same-function-object re-export
  (`testing/relay.py` line 47, `from ... import ...` + `__all__` —
  confirmed same object, not a copy). Agrees.
- `_decode_and_validate_global_id`: 1 def + 2 internal callers
  (`filters/base.py` lines 893, 1017). Agrees.
- `str.__str__`: 4 file-wide in `types/relay.py` (3 in decode + 1
  encode-path), 0 in `filters/base.py`. Agrees with the "4-vs-0"
  census read file-wide.
- Challenges C1→1, C2→1 (+0 filter — the omission, B2 leak and C2
  fallback confirmed real above), C3a/C3b→1 each (intentional
  separation: decode arm 7 vs the filter's widen-guard arm move
  independently), C4/C5→0 owned (upstream `split(":", 1)` + null-grep).
  All agree.

### T2-5 — owner choice

Gate stays with `decode_global_id`; validation stays with
`_decode_and_validate_global_id`. Rejection grounds confirmed from the
bodies: different resolution roots (registry primary at
`types/relay.py` lines 795-804 vs owner-target accepted-set at
`filters/base.py` lines 704-712), different error surfaces
(`ConfigurationError` vs coded `GraphQLError` trio), the unbound
node-id-only fallback has no decode counterpart, and the filter path
receives upstream-normalized wire strings. Adding any guard changes
what is accepted (B2 `RuntimeError` → coded reject; C2 silent accept
→ reject) — never behavior-preserving. Consolidation REJECTED. Agrees.

### T2-6 — reconciliation vs `## Findings`

- F1 (REJECTED consolidation, counts, owner, migration, D-a..D-d,
  triggers T-compose/T-errors/T-fallback): AGREE on every row. The
  four distinct-behavior grounds were each re-derived from the bodies
  above. Triggers are homed at the finding with plan-Outcomes
  durability — correct per the rejected-candidate rule.
- 7-arm definition of the hardening: AGREE (count + per-arm oracles
  re-verified by citation; no oracle was rewritten to read the owner —
  containment rows spell plain literals).
- B2 leak real + direct-Python-only: AGREE, with one ADDED detail
  (the `_encode_global_id_input` pre-detonation at
  `filters/inputs.py` lines 677-678, unguarded slot reads upstream of
  the filter — same in-process-only population, no wire path).
- C2 silent-accept as specified fallback: AGREE (Decision 13 unbound
  path; mechanism re-derived at T2-2).
- C4/C5 → 0 owned: AGREE (upstream body + null-grep both re-run).
- Q1 routed to the maintainer, no defect: AGREE — see T2-7.
- Freshness blobs: AGREE (`git hash-object` re-run: `types/relay.py`
  `52439862…`, `filters/base.py` `ba52351c…`, both equal to `HEAD`
  `bfaee91d`; member diff vs `059e3f27` empty, re-run). Discrepancy
  noted: the dispatch states "current `8bee8949`" but `git rev-parse
  HEAD` prints `bfaee91d` (matching the artifact) — no drift affects
  this item either way since both member blobs match both baselines.
- `## Pending execution` (no `proof:`, one `gate:`): AGREE — see T2-8.
- Zero tracked edits / empty item-scoped diff: AGREE (re-run
  `git diff <baseline> -- <both paths>` empty; `git status --short`
  on both paths clean).

### T2-7 — C2-wire-reachability + Q1/defect routing judgment

C2 question judged FALSE for wire-reachability: JSON filter variables
decode to plain `str`/lists/dicts — never to `GlobalID` objects with
hostile descriptors or non-`str` slots; the `isinstance` branch is
reachable only from direct-Python callers, and upstream
`__post_init__` bars non-`str` slots at ordinary construction.
Observable wire effect of B2/C2: NONE (no 500, no masked error, no
wrong result over GraphQL — the shapes cannot arrive over the wire).
In-process effect: raw `RuntimeError` (B2; or earlier at
`_encode_global_id_input` on the normalize path) and silent node-id
return (C2 unbound, the specified fallback).
Defect test (`AGENTS.md` + `GOAL.md` "Trust boundary"): a defect needs
a broken contract row + a feasible project shape under supported
public API + a wire or configuration input reaching it, and
application Python is TRUSTED ("does not promise to contain code
running inside its own process"). B2 names no contract row extending
the hardening to the filter (spec-031 containment is pinned against
`decode_global_id`; spec-027's filter list is closed without it), and
its reaching input is in-process-only. NOT a defect — W1's no-defect
call stands on harder ground after this trace. Q1 "route to the maintainer" is
CORRECT: whether the filter should gain equivalent hardening is new
behavior (axis-6 ambiguous contract), ownable at
`filters/base.py::_decode_and_validate_global_id` on a card, never in
this item. Q1 stands; no D-entry filed (nothing meets the defect bar).

### T2-8 — gate, pending-execution, AGENTS-prose judgments

- The single `gate:` entry (focused filter hostile-repr test, 1
  passed at `HEAD` with zero member edits in flight) is a genuine
  WITNESS, not a finding-discharger: F1 proposes no enforcement, so
  there is no negative control to run (`scripts/prove_failability.py`
  has no target); the B2/C2 divergence it documents IS the
  demonstrated difference, pinned by the named standing oracles.
  Correctly typed `gate:`, correctly not `proof:`. P1
  `execution-verified` (disposable-workspace probe, copy `__file__`
  recorded, no DB opened) is accepted on its record — string/dict/
  exception work only, so `FAKESHOP_SHARDED=1`/Postgres
  `inapplicable by construction` is judged SOUND.
- No-gate reasoning judged SOUND under the same standard as the
  verified siblings (a rejection proposes no enforcement to pin;
  unity rests on the re-verified `from_id`/`str.__str__` censuses and
  homed triggers, not on a bespoke existence test).
- Freshness re-hashed above (T2-6): all member blobs match; any
  fingerprint change reopens.
- AGENTS.md prose on the empty diff: no process provenance in the
  artifact beyond the allowed baseline/diff record, `path::Symbol`
  citations throughout, tests at the mandated tier (existing oracles
  cited, none rewritten), no production edits so no ruff/format gate
  applies to member paths. The artifact is untracked (only write).
  Concurrent dirt (`filters/inputs.py` range-shape hunk, other
  `docs/dry/` artifacts) preserved — untouched, correctly scoped out
  via the `@@ -772,18 +772,49 @@` check, which still bounds the
  cited lines 659-679 outside the hunk.
- Matrix axes: each judged discharged against the real surface
  (cross-flavor inventoried incl. the write path; twins correctly
  N/A — sync string/dict work; derived-knowledge, round-trip, and
  medium-restatement each owned once with oracles spelling literals;
  axis 6 correctly routed, never a verdict).

## Defects

None (Worker 2 concurs — see T2-7: B2/C2 are wire-unreachable and
name no filter-side contract row, so neither meets the defect bar;
Q1 remains the correct home).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->
[spec-027]: spec-027-filters-0_0_8.md
[spec-031]: spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[relay]: ../../django_strawberry_framework/relay.py
[relay-types]: ../../django_strawberry_framework/types/relay.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py

<!-- tests/ -->
[test-filters-base]: ../../tests/filters/test_base.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
