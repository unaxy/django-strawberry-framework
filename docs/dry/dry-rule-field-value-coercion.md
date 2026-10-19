# DRY review: `field-value-coercion`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Posited rule (index row; owner candidate
[querysets.py][querysets]
`::coerce_field_value_or_none`; indexed files
[querysets.py][querysets], [relay.py][relay],
[filters-base.py][filters-base],
[write-values.py][write-values],
[write-transaction.py][write-transaction],
[keyset.py][keyset], [types-relay.py][types-relay]
as composing consumer `_node_value_or_none` via the s4
F2 nomination, endorsed s14): a raw client literal is
coerced through a Django model field's `to_python` +
`run_validators`, and a value the column cannot hold
identifies no row (`None`) instead of leaking a raw
`ValueError` or backend `OverflowError`. No prior
family artifact exists; this trace is fresh at HEAD
bytes, census-first (the 7 indexed files were not
assumed complete). The index row's pre-run-8
`rejected` status is treated as prior record, not
evidence; the verdict below adjudicates fresh and
sets the final status.

Verdict: CONFIRM the consolidation. The field-value
coercion is one rule with a single mechanics body,
and every member composes it by name. Four
neighbor-merges are rejected with contract
differences and triggers.

- F: the field-value coercion -- the one primitive
  [querysets.py][querysets]
  `::coerce_field_value_or_none` (`:360`-`:395`) plus
  5 field-selecting composers (relay + write + 2
  filter wrappers + the GlobalID inline tail) and
  the transitive `_node_value_or_none` edge. Zero
  second mechanics bodies package-wide (probe R5).
- R1 (rejected merge): the canonical-pk equality
  [write-transaction.py][write-transaction]
  `::canonical_pk` (`:767`) / `::pks_match`
  (`:781`) -- `to_python`-ONLY, RAISING, for
  canonical pk comparison. Converges with the
  existing File row `write-txn-pk-vs-coercion`
  from the family side.
- R2 (rejected merge): the keyset cursor codec
  [keyset.py][keyset] `::_deserialize_cursor_value`
  (`:399`) -- `to_python` + RE-SERIALIZE
  round-trip check, RAISING the cursor error.
- R3 (rejected merge): the field-shaping neighbors
  -- the three form-field `to_python` DEFINITIONS
  (`:457` / `:1012` / `:1197`, a different
  population: Django calls them), the naive-datetime
  normalization
  [mutations-resolvers.py][mutations-resolvers]
  `::_make_aware_if_naive` (`:571`), the
  `full_clean` write envelope (`:1274`), and the
  `IntegerRangeFilter` gte/lte decomposition (an
  intentional non-coercion alternative).
- R4 (rejected merge): the envelope unwrap
  [types-relay.py][types-relay] `::_coerce_node_id`
  (`:334`) -- GlobalID-envelope-to-payload, the
  sequential stage BEFORE field coercion.
  Converges with the existing File row
  `types-relay-envelope-unwrap-vs-field-coercion`.

Sites and roles (all re-derived at HEAD `83998e08`
bytes):

- Definition (F, one mechanics body):
  `::coerce_field_value_or_none` (`:360`: the
  `isinstance` guard `:388`-`:389`, `to_python`
  `:391` + `run_validators` `:392`, `except
  Exception` -> `None` `:393`-`:394`). The
  validators arm is backend-aware (Django 6.1
  reads `connection.ops.integer_field_range`;
  on SQLite the signed-64-bit column range --
  probe R1 pins both boundaries).
- Field-selecting composers, all by name, zero
  inline `to_python` (probe R4 pins all six):
  [relay.py][relay] `::_coerce_pk_or_none`
  (`:158`, field via the shared `_node_id_slot`
  `:133`, tail call `:191`, non-concrete-slot
  raw pass-through); [write-values.py][write-values]
  `::coerce_relation_pk_or_none` (`:107`, lenient
  `_meta.pk` read, tail call `:126`);
  [filters-base.py][filters-base]
  `::_coerce_int_in_members` (`:518`, per-member
  map with `None`-drop `:541`), the GlobalID
  filter tail inside
  `::_decode_and_validate_global_id` (`:898`,
  `None` -> coded `GLOBALID_INVALID`), and
  `::_coerce_relation_identity` (`:1169`,
  unbound-filter pass-through, tail call
  `:1179`).
- Transitive composer (the s4/s14 nomination,
  CONFIRMED from the family side):
  [types-relay.py][types-relay]
  `::_node_value_or_none` (`:338`, unwrap +
  `:357` delegation, 0 mechanics -- the s14 W2
  derivation reproduced exactly).
- Second-level call sites: `_coerce_pk_or_none`
  <- `:334` (write decode), `:503` (node
  null-gate), `:598` (nodes hole-gate),
  [types-relay.py][types-relay] `:357`;
  `_node_value_or_none` <- `:391` (bulk map)
  + `:978` (single default);
  `coerce_relation_pk_or_none` <-
  [write-values.py][write-values] `:165`
  (shared type-check) +
  [mutations-resolvers.py][mutations-resolvers]
  `:1353` (`coerce_lookup_id` `:1299` raw-pk
  branch); `_coerce_int_in_members` <- `:600`;
  `_coerce_relation_identity` <- `:1234` +
  `:1270`.
- Neighbor definitions (each single-owned, each
  excluded): `canonical_pk` 1 def + 1 caller
  (`pks_match` `:789`); `pks_match` 1 def + 4
  direct callers (`:807` inside
  `reject_substituted_row`,
  [rf-resolvers.py][rf-resolvers] `:2030` /
  `:2223` / `:2234`) + 3 transitive
  ([mutations-resolvers.py][mutations-resolvers]
  `:356` / `:392` / `:1146` via
  `reject_substituted_row`: post-authorization,
  update-result, delete-path backstops); keyset
  `serialize_cursor_value` 1 def (`:376`) + 2
  callers (`:407` self-check, `:537` encode
  path) and `_deserialize_cursor_value` 1 def
  (`:399`) + 1 decode caller (`:574`);
  `_coerce_node_id` 1 def + 1 caller
  (`:357`); `_make_aware_if_naive` 1 def + 1
  caller (`:501`).
- Intentional non-members: the three form-field
  `to_python` overrides (form population, not
  model fields); `IntegerRangeFilter`'s
  decomposition (delegates range handling to
  Django's range-aware lookups, never binds);
  the `full_clean` envelope (whole-instance
  validation, not per-literal coercion); the
  password `validate_password` mapping
  ([auth-mutations.py][auth-mutations] `:1266`,
  auth rule); `get_prep_value` (zero hits
  package-wide -- no second spelling exists).
- Oracles: owner --
  [test-querysets.py][test-querysets] `:188`
  (coerced), `:193` (non-numeric -> `None`),
  `:198` (out-of-range -> `None`), `:4631`
  (non-field -> `None`); relay --
  [test-relay-node-field.py][test-relay-node-field]
  `:452` (non-field slot pass-through); write
  -- [test-write-values.py][test-write-values]
  `:508` (hostile/non-model -> `None`),
  [test-mutations-resolvers.py][test-mutations-resolvers]
  `:834` (M2M out-of-range -> not-found);
  filters -- [test-filters-base.py][test-filters-base]
  `:1299` (`None`-column pass-through);
  canonical --
  [test-write-transaction.py][test-write-transaction]
  `:1719` (UUID canonicalization, forged ->
  mismatch), `:1742` (silent match); live --
  [test-library-api.py][test-library-api]
  `:1412` / `:5689` / `:5749` / `:9440`
  (uncoercible nulls/holes/FieldErrors),
  [test-products-api.py][test-products-api]
  `:1423` / `:1459` / `:1500` (not-found /
  FieldError, never 500),
  [test-scalars-api.py][test-scalars-api]
  `:222` (in-drop) / `:347` (range adapt),
  [test-uploads-api.py][test-uploads-api]
  `:712` (raw-pk not-found),
  [test-forms-resolvers.py][test-forms-resolvers]
  `:1335` (form raw-pk FieldError). Cited by
  content at HEAD bytes; no pytest run
  (dispatch forbids it).
- Projections (verified against their bodies):
  the owner module docstring (`:13`-`:16`,
  the sibling-primitive claim) and body
  docstring (three-copy history + per-caller
  field-selection clause -- both hold: the
  three named wrappers each select their own
  field and call once); the relay slot-sharing
  docstrings (`:139`, `:171`, `:254`, `:278`,
  `:316`); the in-members sibling docstring
  (`:530`-`:535`); the GlobalID tail docstring
  (`:818`-`:822`); the relation-identity
  verdict docstring (`:1173`); the write
  counterpart docstring (`:110`-`:116`); the
  node-value docstring (`:346`); the
  canonical/UUID docstrings (`:774`,
  `:784`, [rf-resolvers.py][rf-resolvers]
  `:2220`, [mutations-resolvers.py][mutations-resolvers]
  `:389`); the keyset codec docstrings
  (`:379`-`:386`, `:403`); the scalar-leaf
  call-site docstring (`:184`); the naive
  docstring (`:572`-`:583`). One stale cite
  found (D1, filed below); all other sharing
  claims hold transitively.

Dirt attribution (by diff content vs `git show
HEAD:`, not by dirty status; the ledger names
two indexed files plus one cited file -- each
located below; everything else is
concurrent-external):

- [querysets.py][querysets]: owner range
  (`:360`-`:395`) has TWO hunks: the `except
  Exception` narrows to `(ValidationError,
  TypeError, ValueError, OverflowError)` with
  a `DurationField` / `OverflowError`
  docstring reword (except-narrowing
  migration). Tail call shape unchanged.
- [relay.py][relay]: `::_coerce_pk_or_none`
  gains a `slot` parameter (precomputed
  slot threading, perf) + docstring reword;
  `decode_model_global_id` refactored to
  compose a new `_decode_and_coerce`
  query-free half (NodeID batching
  restructure) -- the coercion still flows
  through the one primitive by name. LEDGER
  (adopted orphan `typed-globalid-decode`,
  DRY-attributed): the trigger-docstring
  paragraph at worktree `:444` -- prose in
  the decode docstring, disjoint from the
  `:334` call mechanics.
- [filters-base.py][filters-base]: truth
  migration renames (`_safe_arg_repr` ->
  `truth.render`, `_safe_type_name` ->
  `truth.kind`, `_meta` reads ->
  `truth.static_attr`) + docstring rewords;
  coercion calls (`:541`, `:600`, `:898`,
  `:1179`, `:1234`, `:1270`) intact.
- [write-values.py][write-values]: `_meta`
  read -> `truth.static_attr` (worktree
  `:128`) + type-check docstring
  restructure (NodeID batching); tail call
  intact.
- [write-transaction.py][write-transaction]:
  `pks_match` narrows `except Exception` ->
  `(ValidationError, TypeError, ValueError)`
  + docstring (same except-narrowing
  family); `canonical_pk` untouched.
- [keyset.py][keyset]: codec range
  (`:376`-`:411`) has ZERO hunks (nearest
  is a `:416` docstring prose reword).
- [types-relay.py][types-relay]:
  `_node_value_or_none` gains `slot`
  threading + `_node_values` precomputes it
  (mirrors the relay perf change);
  composition by name intact. LEDGER
  (adopted orphan `relay-node-type-stamp`,
  DRY-attributed): the trigger comment at
  worktree `:94` -- far from the
  `:335`-`:357` / `:391` / `:978` ranges.
- Cited files:
  [auth-mutations.py][auth-mutations]
  (LEDGER e1 awaitable composition at
  `:498`-`:529` + import `:75` -- far
  from the cited `:1266` mapping),
  [forms-resolvers.py][forms-resolvers]
  (3 hunks at `:433`+, D1 cite `:30`
  byte-identical),
  [mutations-resolvers.py][mutations-resolvers]
  (truth-migration wording at `:394`,
  full_clean at `:1265`+, decoder ranges
  intact),
  [rf-resolvers.py][rf-resolvers]
  (truth-migration wording bracketing
  `:2030` / `:2223` / `:2234`, calls
  intact).
- Decision impact: none. The probe ran both
  states to prove the point (identical ALL
  OK).

Three-state fingerprints (indexed files):

- [querysets.py][querysets]: HEAD
  `392e50d0`, worktree `cfc773ba`,
  `9aaaad5d` `8fc556d5`;
  `36bd41ef` == worktree.
- [relay.py][relay]: HEAD `a09485a1`,
  worktree `fd88aafa`, `9aaaad5d`
  `f5760b45`; `36bd41ef` == worktree.
- [filters-base.py][filters-base]: HEAD
  `e2e683a8`, worktree `fc1cf61f`,
  `9aaaad5d` `3b1dcbce`;
  `36bd41ef` == worktree.
- [write-values.py][write-values]: HEAD
  `01a3318c`, worktree `4fa8118d`,
  `9aaaad5d` `13548c76`;
  `36bd41ef` == worktree.
- [write-transaction.py][write-transaction]:
  HEAD `c0a12b34`, worktree `49102e69`,
  `9aaaad5d` `4a83f43d`;
  `36bd41ef` == worktree.
- [keyset.py][keyset]: HEAD `8da76569`,
  worktree `49f0dfbe`, `9aaaad5d`
  `d1a6dec2`; `36bd41ef` == worktree.
- [types-relay.py][types-relay]: HEAD
  `968fb95a`, worktree `6c2e8c20`,
  `9aaaad5d` `4b2a9df5`;
  `36bd41ef` == worktree.
- Nothing moved since `ITEM_BASELINE`
  (`36bd41efb5d73abf34eb856ced712499825c20c2`
  -- window diff on package/tests/examples
  is empty); HEAD
  `83998e08d48c911199527ed0411ab8041805c8b5`;
  snapshot
  `9aaaad5de73f6ff36eea3264e5b085fef1b046cc`.
- Cited files (HEAD / worktree):
  [forms-resolvers.py][forms-resolvers]
  `ea839d84` / `6e613333`,
  [mutations-resolvers.py][mutations-resolvers]
  `7a25afea` / `dd00ec6e`,
  [rf-resolvers.py][rf-resolvers]
  `420fc3ca` / `3fc6a366`,
  [auth-mutations.py][auth-mutations]
  `72595bb1` / `d3853af4`.
  Oracles (HEAD / worktree):
  [test-querysets.py][test-querysets]
  `3ff4094a` / `b1fc954b`,
  [test-write-values.py][test-write-values]
  `8d09921b` / `9f459e2f`,
  [test-filters-base.py][test-filters-base]
  `2c507b75` / `b7ae27b6`,
  [test-write-transaction.py][test-write-transaction]
  `5f5e9d28` / `6b8c815a`,
  [test-relay-node-field.py][test-relay-node-field]
  `7c0f22ed` / `7f47c3dd`,
  [test-mutations-resolvers.py][test-mutations-resolvers]
  `4f94c05a` / `eeab4fbe`,
  [test-forms-resolvers.py][test-forms-resolvers]
  `66498cb4` / `6cab42c2`,
  [test-library-api.py][test-library-api]
  `91f0238b` / `099e25b9`,
  [test-products-api.py][test-products-api]
  `4186b4d9` / `fe78cf9d`,
  [test-scalars-api.py][test-scalars-api]
  `edc50088` (clean),
  [test-uploads-api.py][test-uploads-api]
  `dcbcbf61` (clean).

Prior records used as triggers only: the s4
F2 nomination + s14 endorsement (membership
edge re-derived from this side before being
relied on), the File rows
`write-txn-pk-vs-coercion` and
`types-relay-envelope-unwrap-vs-field-coercion`
(convergence checked, not assumed), and the
pre-run-8 `rejected` status itself
(adjudicated fresh -- the verdict below
supersedes it). The s13 standing note
(directory pathspec for censuses) was
honored for every census below.

## Verification

### Matrix

1. Cross-flavor mirroring: read (node/nodes
   gates + defaults), filter (in-members,
   GlobalID tail, relation identity), and
   write (relation-pk, lookup-id) coercions
   all compose the primitive by name (5
   direct + 1 transitive, 0 mechanics
   bodies). No flavor carries a second
   cast-then-validate body.
2. Sync/async twins: the coercion is pure
   (no I/O, no await) -- colorless by
   construction. The twin-shaped neighbors
   (node sync/async defaults) share the one
   sync coercion before dispatching, which
   is why the membership edge sits above
   the color fork.
3. Derived knowledge: `_meta.pk` is read
   once per composer (each read selects a
   DIFFERENT field -- relay slot, related
   pk, filter column -- the documented
   per-caller decision); the slot mapping
   is single-owned (`_node_id_slot`); the
   NodeID-to-real-pk mapping is single-owned
   (`_resolve_real_pk`). One Django fact,
   composed -- not re-derived.
4. Round-trip pairs: the coercion has no
   inverse (lossy by design: invalid maps
   to `None`). The keyset codec IS a
   round-trip pair (`value_to_string` /
   `to_python` + reserialize) -- a different
   contract, excluded in R2.
5. Other media: production (one mechanics
   body), oracles (listed above, every layer
   pinned incl. the overflow and hole
   tripwires), projections (docstrings,
   verified; 1 stale cite filed as D1).
   Listed, not counted.
6. Enforcement by omission: every surface
   feeding a raw literal to the ORM coerces
   first -- node/nodes, GlobalID decodes,
   relation ids (all three flavors),
   lookup ids, in-members, relation-identity
   filters. The two deliberate
   non-coercions each name their reason
   (non-concrete slot + unbound filter
   pass-throughs; the range decomposition).
   No member lacks a guard its contract
   requires.

### Enumeration

Instruments: `git grep` censuses with the
directory pathspec (`django_strawberry_framework`,
never `**/*.py`) plus full-body reads of every
hit file at HEAD bytes; the R5 AST census
re-pins the executable counts.

- `coerce_field_value_or_none`: 1 def (`:360`)
  + 5 direct callers (`:191`, `:126`, `:541`,
  `:898`, `:1179`) + imports + prose.
- `_coerce_pk_or_none`: 1 def (`:158`) + 4
  callers (`:334`, `:503`, `:598`,
  [types-relay.py][types-relay] `:357`) +
  prose.
- `_node_value_or_none`: 1 def (`:338`) + 2
  callers (`:391`, `:978`) + prose. The s4/s14
  membership edge (`:357`) re-derived from
  this side: unwrap + delegate, 0 mechanics.
- `coerce_relation_pk_or_none`: 1 def (`:107`)
  + 2 callers (`:165`, `:1353`) + prose.
- `_coerce_int_in_members`: 1 def (`:518`) + 1
  caller (`:600`) + prose.
  `_coerce_relation_identity`: 1 def (`:1169`)
  + 2 callers (`:1234`, `:1270`) + prose.
- `canonical_pk`: 1 def (`:767`) + 1 caller
  (`:789`) + prose. `pks_match`: 1 def
  (`:781`) + 4 direct callers (`:807`,
  `:2030`, `:2223`, `:2234`) + 3 transitive
  via `reject_substituted_row` (`:356` /
  `:392` / `:1146`) + prose.
- `.to_python(` executable: 4 sites --
  owner `:391`, keyset `:402`, canonical
  `:778`, form super-call `:1016`
  (definitions at `:457` / `:1012` /
  `:1197` are the form population).
  `run_validators(` executable: 1 site
  (`:392`). `get_prep_value`: 0 hits.
- `except ValidationError` catch sites: 5
  (`:410` keyset cursor error, `:1266` auth
  password mapping, `:1275` full_clean
  mapping, `:2455` / `:2457` serializer
  mappings) -- every one classified, none a
  second coercion body.
- Every member lands in F, R1, R2, R3, R4,
  or the exclusion list above. Nothing
  unassigned.

### Challenges

Merge tests (posit a change to the SHARED
rule; count definitions forced to move
together):

- M1 -- out-of-range must now RAISE instead
  of mapping to `None`: the owner body alone
  (1 + its oracles). Relay/write/filter/node
  all follow by call; canonical (already
  raising, no validators) and keyset
  (already raising, round-trip) never move.
  Count: 1.
- M2 -- the validators arm is dropped
  (`to_python`-only): the owner alone (1).
  Canonical is PROOF the merge is wrong
  today: it already is the `to_python`-only
  shape, and routing it through the owner
  would newly reject range-valid-but-
  validator-rejected pks from equality.
  Count: 1.
- M3 -- a new `to_python` exception type must
  map to `None`: the owner `except` alone
  (1). The worktree narrowing (enumerated
  tuple) is exactly this axis moving in one
  place.
- M4 -- canonical equality must ALSO run
  validators: `canonical_pk` alone (1) --
  and that change would be a semantic break
  (range-rejected values comparing unequal
  to themselves), which is why R1's trigger
  demands it explicitly.

Per-rule challenges:

- C1 -- a sixth field-selecting composer (a
  new surface): 1 adapter (field selection +
  `None`-mapping), 0 mechanics bodies
  (principle 5 -- the five existing composers
  are the worked examples).
- C2 -- the invalid verdict changes shape
  (e.g. sentinel instead of `None`): 1 body
  (the owner) + per-caller mappings (each
  caller's `None` arm is its own contract).
- C3 -- a new id-slot shape (a second
  non-concrete fall-through): `_node_id_slot`
  alone (1); both relay consumers follow.
- C4 -- the batch precompute widens (the
  worktree `slot` threading): relay +
  types-relay call shapes only (0 mechanics
  -- executed identically in both probe
  runs).
- C5 -- cursor forgery must now map to
  `None` instead of raising: keyset alone
  (1 -- and it would break the total-order
  contract, hence R2's trigger).
- C6 -- the form-field list contract changes:
  that override alone (1); model-field
  coercion untouched.
- C7 -- naive datetimes must now reject
  instead of localize: `_make_aware_if_naive`
  alone (1).

Every genuine rule change moves at most 1
definition. By DRY's counting rule that is
independence, even where the `to_python`
token coincides.

Probe (execution-verified, disposable copy;
read-only -- settings configured against an
in-memory SQLite that is never connected,
zero SQL): `/tmp/e4_probe.py` over a `git
archive HEAD` tree inside the copy (run
`dry-20261001T003743-c980ee`, exit 0,
package `__file__` under `head-tree/`), plus
the copy's own worktree bytes (run
`dry-20261001T003754-dfdc2d`, exit 0,
identical ALL OK). Slot venv lacks locked
deps (standing s13 infra finding); both runs
used the disclosed
`PYTHONPATH=<shared-venv>/site-packages` shim
with the probed package first on `sys.path`.

- R0: package resolves under the probed
  tree; owner + canonical + keyset import
  by name.
- R1: owner semantics execute (`"3"` -> 3,
  `"abc"` -> `None`, 2**63 -> `None`,
  2**63-1 passes, below-min -> `None`,
  UUID normalize, non-field -> `None`).
- R2: canonical raises where the owner maps
  (the R1 difference executes); UUID
  canonical equality incl. hex spelling.
- R3: keyset raises `GraphQLError` on
  malformed AND non-canonical (`"05"`) wire
  values (the R2 difference executes).
- R4: all 6 composers call the composed name
  x1 with zero inline `to_python` /
  `run_validators`.
- R5: package-wide AST census -- 1
  `run_validators`, 4 `to_python`, exactly
  the known files.

## Findings

### F -- CONFIRMED single-owned, no edit

Contract + variation: a raw client literal is
coerced through a caller-chosen model field's
`to_python` + `run_validators`; a value the
column cannot hold identifies no row
(`None`), mapped per caller to drop /
not-found / invalid / null-hole -- never a
raw crash. Varies by field selection (each
caller's genuine decision) and `None`-mapping
(each caller's contract); the mechanics are
fixed.
Sites + roles: definition = the one primitive
(`:360`-`:395`); composers = 5 direct call
sites (`:191` / `:126` / `:541` / `:898` /
`:1179`) + the transitive node edge (`:357`);
downstream links = 10 (3 relay + 2 node + 2
relation-pk + 1 in-members + 2
relation-identity).
Challenges: M1/M2/M3 = 1 (this contract
alone); C1 = 0 mechanics; C2/C3/C4 =
1 body each.
Owner + lifetime (principles 7/4): the
primitive owns the mechanics (the narrowest
cohesive owner every surface already
imports -- relay, filters, and both write
flavors depend on `utils/querysets`
without cycles); callers own field selection
and `None`-mapping; per-call, nothing
stored.
Migration: none -- already single (every
link composes by name, re-derived at every
level, probe-pinned).
Distinct behavior kept: per-caller
`None`-mappings (drop / coded error /
not-found / null-hole, each prescribed at
its call site); the non-concrete-slot and
unbound-filter pass-throughs (documented at
each composer); the `slot` precompute (call
shape, 0 mechanics).
Behavioral proof: execution-verified (probe
R0/R1 + R4/R5) + static (one mechanics body,
zero second bodies package-wide) + the
per-layer oracles above.
Structural gate: none proposed -- bypass
means inlining a new `to_python` +
`run_validators` pair, whose future-site
population cannot be enumerated without a
bespoke existence test per helper; the
per-layer overflow/uncoercible oracles plus
the documented primitive pin the composition
instead. The R5 census stands as trace
evidence, not a committed gate. A red result
would be a defect, not a gate.
Layering note (no ownership clash): the
file-local `types-relay-node-id-coerce-and-filter`
row owns the node-id COMPOSE
(unwrap-then-coerce-through-the-slot,
`_node_value_or_none` + bulk + filters);
this family owns the field-value MECHANICS
the `:357` edge delegates to. The s14 W2
derivation ("0 mechanics here") is the same
layering.
Freshness: fingerprints in System trace (all
three states for indexed files; HEAD/worktree
for cited + oracles).

### R1 -- REJECTED: canonical-pk merge

Shared form considered: treating
`::canonical_pk` / `::pks_match` as second
definitions of the coerce-through-the-field
rule, or routing one through the other.
Contract differences (each independently
fatal):

1. Mechanics: `to_python` ONLY, no
   `run_validators` -- vs the owner's
   cast-then-validate pair. M2 moves only
   the owner.
2. Failure contract: RAISES the field's
   `ValidationError` (callers map to
   "not equal" / configured wording) vs
   maps to `None`. M1 moves only the
   owner. Probe R2 executes the fork on
   the same input.
3. Subject: pk EQUALITY between two held
   values (authorization snapshots,
   substitution backstops) vs single-literal
   row identification. No caller of one
   could call the other.
4. Range posture: a range-rejected value
   still canonicalizes for comparison --
   routing through the owner would make it
   compare unequal to itself (M4).

Challenges: M1/M2/M4 = 1 per side; no
shared change exists.
Reconsideration trigger: `canonical_pk`
gains the validators arm AND maps failure to
`None` (i.e. becomes the owner spelling) --
or the family explicitly widens to "any
`to_python` call" (then the census
re-opens package-wide).
Durable home: already at both owners -- the
canonical docstrings state the raising +
equality contract, and the existing File row
`write-txn-pk-vs-coercion` records this
rejection (this R1 is the family-side
convergence it names as "F6"). No edit owed.
Record note for Worker-0: that row's
"CONVERGE with rejected ... F6" adjective
predates this adjudication -- the family
verdict is now `consolidated`; the
convergence target is this R1.

### R2 -- REJECTED: keyset codec merge

Shared form considered:
`::_deserialize_cursor_value`'s `:402`
`to_python` as a second definition of the
coerce-through-the-field rule.
Contract differences: subject is a CURSOR
wire value (opaque pagination position),
not a row-identifying literal; mechanics add
the RE-SERIALIZE round-trip check (`:407` --
a value whose wire shape is non-canonical
is rejected even when `to_python` accepts
it); failure RAISES the cursor
`GraphQLError`, never maps to `None` (a
`None` cursor position would corrupt the
total order). Probe R3 executes both forks
(`"abc"` and `"05"`).
Challenges: C5 = keyset only; M1/M2/M4
never move it.
Reconsideration trigger: the codec drops
the reserialize check AND maps failure to
`None` (abandoning the total-order
contract).
Durable home: already at the owner -- the
codec docstrings state the round-trip +
raising contract. No edit owed.

### R3 -- REJECTED: field-shaping neighbors

Shared form considered: folding the
remaining `to_python`-adjacent shapings
into the family.
Contract differences, per neighbor: the
three form-field `to_python` overrides
DEFINE the conversion Django's form
machinery calls (form population -- the
family CONSUMES model-field conversion;
opposite sides of the same dunder);
`_make_aware_if_naive` normalizes an
already-parsed `datetime` (no field, no
validators, no `None`, never fails);
`_full_clean_or_field_errors` validates a
whole instance into the error envelope
(not a per-literal gate);
`IntegerRangeFilter` deliberately does NOT
coerce -- it decomposes into gte/lte so
each bound flows through Django's
range-aware lookups (an intentional
alternative, recorded at its owner).
Challenges: C6/C7 = 1 per neighbor;
M1-M4 never move them.
Reconsideration trigger: any neighbor
starts coercing a raw literal through a
model field's `to_python` + `run_validators`
with a `None`-means-no-row verdict (i.e.
re-spells the owner).
Durable home: each behavior already
recorded at its verified file-item owner.
No edit owed.

### R4 -- REJECTED: envelope-unwrap merge

Shared form considered: treating
`::_coerce_node_id` (GlobalID object ->
`node_id` string) as part of the
field-value coercion.
Contract differences: envelope-to-payload
vs payload-to-field-value are sequential
stages with different inputs (a
`relay.GlobalID` vs a raw literal),
different failures (no failure -- a
pass-through one-liner -- vs `None`), and
different owners (the node-id compose vs
the mechanics primitive). The `:357` edge
already sequences them without merging
them.
Challenges: a change to either stage moves
1 definition; no shared change exists.
Reconsideration trigger: the unwrap gains
field awareness (validates against a
column).
Durable home: already at the owner -- the
node-value docstring ("unwrapped first")
plus the existing File row
`types-relay-envelope-unwrap-vs-field-coercion`,
which this R4 converges with from the
family side. No edit owed.

Worker-0 index rows (this family item names;
plan edits are Worker-0's):

- Family `field-value-coercion` -> status
  `consolidated` (F single-owned, no edit;
  R1-R4 exclusions with triggers; D1
  doc-only defect filed). This verdict
  supersedes the pre-run-8 `rejected`
  status, which had no artifact behind it.
- Files-covered: KEEP all 7 -- every file
  hosts the owner, a composer, or an
  adjudicated neighbor (unlike e3, no rule
  is hived off to its own row; the R1/R4
  neighbors already have File-homed rows
  and R2/R3 live in verified file-item
  territory).
- No new rows (R1 converges with
  `write-txn-pk-vs-coercion`, R4 converges
  with
  `types-relay-envelope-unwrap-vs-field-coercion`,
  R2/R3 carry their triggers in-artifact).

## Defects

- D1 (doc-only, owner
  [forms-resolvers.py][forms-resolvers]
  module docstring `:30`): cites
  ``_coerce_relation_pk_or_none`` (leading
  underscore), a name with exactly 1 live
  occurrence package-wide (this cite) and 0
  defs -- the helper is public
  `coerce_relation_pk_or_none`
  ([write-values.py][write-values] `:107`).
  Provenance: the underscore spelling was
  the 0.0.12 private name in
  `mutations/resolvers.py` (prior plan
  `docs/dry/dry-0_0_12.md` `:142`-`:143`
  pins it); the promotion to
  `write_values.py` left this cite behind.
  Persists in the worktree (`:30`,
  byte-identical; the file's 3 hunks are at
  `:433`+). Route: closeout doc correction
  (one cite reword, no behavior).

## Pending execution

- `proof:` `uv run python
  scripts/workspace.py run
  dry/fieldcoerce-e4/consolidate -- sh -c
  'PYTHONPATH=<shared-venv>/site-packages
  python3 /tmp/e4_probe.py head-tree'` --
  execution-verified (run
  `dry-20261001T003743-c980ee`, exit 0,
  `E4-PROBE ALL OK`, package `__file__`
  under `head-tree/` holding `git archive
  HEAD` bytes; discharges F R0/R1/R4/R5,
  R1 R2, R2 R3). `<copy>` =
  `/private/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/dsf-ws/0b901faeac791a7b/dry/slots/slot-2`,
  `<shared-venv>` =
  `~/.t3/worktrees/django-strawberry-framework/dry-0015/.venv/lib/python3.14/site-packages`.
  The `head-tree/` extraction + `/tmp/e4_probe.py`
  stay on disk for Worker-2; remove by
  explicit path after verification.
- Worktree comparison (same command, `.` as
  the tree): run `dry-20261001T003754-dfdc2d`,
  exit 0, identical ALL OK --
  decision-neutral drift proved behaviorally.
  Informational; discharges nothing.
- Shared-tree authorization unspent: zero
  edits landed, no oracle added, no pytest
  run -- no `gate:` command owed.

## Judgment

The field-value coercion is one rule with a
single mechanics body: the primitive owns
the `to_python` + `run_validators` /
`None`-means-no-row contract, five
field-selecting composers plus the
`_node_value_or_none` transitive edge
consume it by name across 5 direct and 10
downstream call sites,
and zero second bodies exist package-wide
(AST census: 1 `run_validators`, 4
`to_python`, each classified). The s4/s14
composing-consumer membership is confirmed
from the family side (real `:357` edge, 0
mechanics). The lookalikes are distinct
per-site rules -- the raising
`to_python`-only canonical equality, the
raising round-trip cursor codec, the
form-field definitions and scalar shapings,
and the envelope unwrap -- each
single-owned, each excluded on contract
differences with a trigger. Zero production
edits; one doc-only defect filed. The
family is CONFIRMED as consolidated,
superseding the artifact-less pre-run-8
`rejected` record.

Item-scoped diff state: no tracked edits;
one new untracked artifact (this file).
`git diff 36bd41ef --stat` on
package/tests/examples is empty; all
package dirt pre-dates the baseline
(verified `36bd41ef` tree bytes == worktree
bytes on all seven indexed files). Scratch:
`<copy>/head-tree/` (HEAD-bytes extraction,
copy-only) + `/tmp/e4_probe.py` (read-only
probe, OS temp).

## Independent verification (Worker-2)

Expectation-first at HEAD `83998e08` bytes
(the W1 sections above were the claim under
test, never evidence). All censuses ran with
the directory pathspec
(`django_strawberry_framework`, never
`**/*.py`); all execution ran in the
disposable copy at `dry/fieldcoerce-e4/verify`
(slot-3) with a self-authored probe
(`/tmp/e4w2_probe.py`, never opened W1's).
No pytest (read-only probe suffices; the
dispatch forbids it).

Own trace (re-derived, then reconciled --
no differences): the one mechanics body is
[querysets.py][querysets]
`::coerce_field_value_or_none` (`:360`:
guard `:388`-`:389`, `to_python` `:391` +
`run_validators` `:392`, `except` -> `None`
`:393`-`:394`); 5 field-selecting composers
call it by name (`:191` / `:126` / `:541` /
`:898` / `:1179`); the transitive edge is
[types-relay.py][types-relay]
`::_node_value_or_none` (`:338`, unwrap
`:334` + delegate `:357`, 0 mechanics); 10
downstream call sites; the R1-R4 neighbors
are each single-owned with the contract
differences stated. The primitive is the
owner I would choose (narrowest cohesive
owner every surface already imports). The
F verdict (CONFIRM, superseding the
artifact-less pre-run-8 `rejected`) stands
on my evidence.

Enumeration (member by member, mine ==
claimed): 1 def + 5 callers + imports +
prose for the primitive; `_coerce_pk_or_none`
1 + 4; `_node_value_or_none` 1 + 2;
`coerce_relation_pk_or_none` 1 + 2;
`_coerce_int_in_members` 1 + 1;
`_coerce_relation_identity` 1 + 2;
`canonical_pk` 1 + 1; `pks_match` 1 + 4 + 3
transitive; `.to_python(` executable 4
(`:391`, `:402`, `:778`, `:1016`) +
`def to_python` 3 (`:457` / `:1012` /
`:1197`, all form-field overrides);
`run_validators(` executable 1 (`:392`);
`get_prep_value` 0. The 5 catch sites are
exactly `:410` (tuple), `:1266`, `:1275`,
`:2455` / `:2457` (aliased) -- W1's
"`except ValidationError`" label is
shorthand for three spellings, but every
site is listed and none is a second
coercion body (cursor / password /
full-clean / serializer-save mappings,
each body-read). Nothing unassigned.

Matrix: all six axes discharged against
the real surface -- the colorless
argument (axis 2), the per-caller
field-selection argument (axis 3), and
the axis-6 guard census each check out
against the bodies and the package-wide
census. Challenges M1-M4 / C1-C7: every
count re-verified (M4's break is real:
validators in `canonical_pk` would make
`pks_match(m, 2**63, 2**63)` false).

Execution (my probe, my runs): HEAD-bytes
`head-tree/` run `dry-20261001T005352-db6129`
exit 0 `W2-PROBE ALL OK` (W0 resolve under
the probed tree; W1 owner semantics incl.
both 64-bit boundaries + UUID + non-field;
W2 canonical-raises fork + hex-spelling
equality; W3 keyset malformed + `"05"`
raise, `"5"` passes; W4 five x1 + one
transitive x1, zero inline mechanics; W5
AST census over 117 files exactly
1 + 4 + 0 at the known sites); worktree
run `dry-20261001T005417-262851` exit 0
identical (119 files -- the 2 untracked
`utils/lazy.py` + `utils/truth.py` carry
no coercion token; same 4 + 1 files, only
line drift, hence `--loose-lines`). Zero
SQL (cursor guard). This reproduces the
execution claim independently; the
`proof:` entry is discharged, no `gate:`
owed (zero edits, no pytest).

Convergence judged on the merits: the File
row's "F6" is phantom as a family label
(F6 lives in the querysets file artifact
and pairs `_stringified` against canonical
-- a different pair), so the true
convergence target is this R1, whose
contract differences match the File R2
text point for point; the "rejected"
adjective is superseded by `consolidated`.
R4 converges with the envelope row (same
pair, same sequential-stages difference,
same field-awareness trigger; R15 even
records the family row as artifact-less
prior input). D1: 1 source occurrence
(`:30`), 0 defs (the worktree's second
grep hit is a `__pycache__` binary only),
byte-identical in the worktree, survivor
the public `:107` helper; closeout routing
correct. No-gate justification accepted
(the census is line-fragile -- my worktree
run proves it -- and per-layer overflow
oracles pin the behavior).

Dirt (every hunk content-checked): owner
two hunks (docstring + the M3-axis
narrowing, tail shape unchanged); relay
slot threading + `_decode_and_coerce`
(`:322`) + ledger prose at WT `:444`
(disjoint from `:334`); types-relay slot
threading + ledger comment at WT `:94`;
truth-migration renames around (never in)
the `:898` tail, `:126`, `:2030` / `:2223`
/ `:2234`, `:1146`, `:394`; `field_name_map`
threading beside `:1266` / `:1275` /
`:2455` (mappings intact); keyset codec
range zero hunks; forms 3 hunks at `:433`+.
Decision impact: none -- anything moving
is call shape or prose.

Fingerprints: all 7 indexed files
HEAD/WT/BASE re-pinned, BASE == WT on all
7; all 4 cited + 11 oracle blobs match the
table above exactly (incl. the 2 clean
live files). Window diff vs
`ITEM_BASELINE` on package/tests/examples
is empty; the artifact is the sole
untracked item change. Index rows judged
as exact replacement text: family ->
`consolidated`, KEEP all 7 (each hosts
owner, composer, or adjudicated neighbor),
no new rows. Prose rules hold (reference
links, `::Symbol` + scratchpad `:NN`
cites, no `.py` touched so ruff is
inapplicable). Verdict: `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations.py]: ../../django_strawberry_framework/auth/mutations.py
[filters-base.py]: ../../django_strawberry_framework/filters/base.py
[forms-resolvers.py]: ../../django_strawberry_framework/forms/resolvers.py
[keyset.py]: ../../django_strawberry_framework/keyset.py
[mutations-resolvers.py]: ../../django_strawberry_framework/mutations/resolvers.py
[querysets.py]: ../../django_strawberry_framework/utils/querysets.py
[relay.py]: ../../django_strawberry_framework/relay.py
[rf-resolvers.py]: ../../django_strawberry_framework/rest_framework/resolvers.py
[types-relay.py]: ../../django_strawberry_framework/types/relay.py
[write-transaction.py]: ../../django_strawberry_framework/utils/write_transaction.py
[write-values.py]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-filters-base.py]: ../../tests/filters/test_base.py
[test-forms-resolvers.py]: ../../tests/forms/test_resolvers.py
[test-mutations-resolvers.py]: ../../tests/mutations/test_resolvers.py
[test-querysets.py]: ../../tests/utils/test_querysets.py
[test-relay-node-field.py]: ../../tests/test_relay_node_field.py
[test-write-transaction.py]: ../../tests/mutations/test_write_transaction.py
[test-write-values.py]: ../../tests/utils/test_write_values.py

<!-- examples/ -->
[test-library-api.py]: ../../examples/fakeshop/test_query/test_library_api.py
[test-products-api.py]: ../../examples/fakeshop/test_query/test_products_api.py
[test-scalars-api.py]: ../../examples/fakeshop/test_query/test_scalars_api.py
[test-uploads-api.py]: ../../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
...[truncated 11290 chars]