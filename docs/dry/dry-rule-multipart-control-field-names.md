# DRY review: `multipart-control-field-names`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule is the GraphQL multipart request wire vocabulary: the two control-field
names `operations` (the operations document) and `map` (the file map). An
exact-match AST census over the package found every code spelling before the
change: 6 string constants in 2 files - the `views.py` tuple
`_MULTIPART_CONTROL_FIELDS` (read side: the lossy-decode guard iterates it) and
the `testing/client.py` one-edit region (emit side: the reserved-key guard set,
the emitted envelope keys, plus a runtime message naming the fields). The
actual parse - upstream Strawberry's `parse_multipart` on both transports -
reads the same two literals in the installed dependency, outside the
consolidation population; it stands as the independent backstop.

Verdict: CONFIRM-consolidated. The three variation axes each force both
package definitions to move together (counts below); the reasons to change are
one (the specification and the parser it serves), and every oracle spells the
literals independently, so sharing the production spelling destroys no check.
The owner is the new dependency-free leaf [`_multipart.py`][multipart],
chosen by principle 7 after every existing candidate failed on
responsibility, dependency direction, or a standing rejection. Both consumers compose it by name in this
same change, with a source-census gate proving the single spelling.

Concurrency: both indexed files carry hunt/maintainer dirt (truth-migration
token swaps plus one except-`BaseException` deletion); neither file has an
`## Owned changes` row, so all of it is concurrent. Every hunk is attributed
by content below; one first-draft edit touched a hunt-dirtied line (the client
message line) and was reverted byte-for-byte - the message is projection and
stays literal. No other edit touches a concurrent line.

Baselines: `ITEM_BASELINE=89ca59723ffd5493157efbb73f2faed9d1976c4a`
(resolves); HEAD `dd0b6691` unmoved throughout. Dispatch pins verified at task
start: `testing/client.py` WT `00f62a11` / HEAD `4d6791fa`, `views.py` WT
`432c6e49` / HEAD `fbf00ddf`. Address `dry/multipart-f39/consolidate`
(slot-2; all proofs ran there).

## Verification

### Matrix

Each axis was searched against the rule's mechanism (the control-field names
as code, as prose, and as form reads), not the targets' neighbours.

1. Cross-flavor policy mirroring - searched. `consumers.py` (WebSocket
   transport) carries no multipart handling - body read, zero field-name
   literals; `scalars.py` owns the `Upload` value type, never the envelope;
   `middleware/request_body.py` mentions `request.POST` only in prose and runs
   the boundary without naming fields; `_request_body.py` is measurement-only
   per the standing J7 rejection (trigger unfired); `conf.py` reads settings,
   and these names are not a setting; `testing/_wrap.py` wraps
   connection methods (Trac #37064), unrelated by body. No second rule.
2. Sync/async twins - compared by behavior. The two `views.py`
   `parse_multipart` overrides both call the one mixin method
   (`request.post_data` sync / `await request.get_form_data()` async) which
   iterates the one tuple; the two client `query()` colors share the one
   `_build_body`. The names are spelled once per side across both colors.
   Upstream's twin parsers each read both literals (installed 0.324.0, both
   bodies read) - out of population, backstop only.
3. Derived rather than repeated knowledge - searched. No site derives the
   names (no concatenation, no `_meta` read, no settings read, no
   `getattr` default): every code site spelled literals. The client guard
   set was a restatement of the envelope keys, not a derivation; both now
   compose the owner.
4. Inverse / round-trip pairs - this family. Emit half (`client.py`
   `_build_body`: envelope keys + reserved set) and read half (`views.py`
   `_reject_lossy_multipart_control_fields`: guard iteration) of one wire
   grammar - consolidated at the owner. Upstream's parse is the third half
   and cannot be owned (R7).
5. Contracts restated in another medium - classified, never counted.
   Oracles: `tests/testing/test_client.py` (emission keys, guard params,
   `no operations/map` JSON pin), `tests/test_views.py` (literal control
   dicts), live hand-built rows (`test_transport_api.py` lossy matrix,
   marker scope, map-shape rows), live round-trips (`test_client_api.py`,
   `test_uploads_api.py`) - all spell literals; zero imports of the
   constant anywhere in `tests/` or `examples/`. Projections: module and
   method docstrings plus comments in `views.py`, `client.py`, and
   `_strawberry_patches.py` (all prose - the regex census finds no code
   spelling there), and the client reserved message - all stay literal.
   Board: no `path::Symbol` cite of the constant (grep zero).
6. Enforcement by omission - family enumerated, each member checked.
   Multipart handlers: views sync + async (both guarded through the
   mixin), `_strawberry_patches.py` delegates (delegate upstream's parse,
   no field-name logic), middleware (no field logic), consumers (no
   multipart), client emit + guard (shared by both colors). No member
   lacks an applicable guard; the absences are no-rule, not gaps.

### Enumeration

Instrument one: exact-match AST census for string constants equal to
`operations` or `map` over `django_strawberry_framework/**/*.py`
(`rglob`, `ast.parse`, comments never parse, no docstring is exactly one
bare name so every hit is a code spelling). Pre-change: 119 files, 0
unparseable, 6 hits - `views.py:163` x2 (the tuple), `client.py:286` x2
(the guard set), `client.py:299` x2 (the envelope keys). The client
message line contributes zero hits (substring, not exact match).
Post-change: 120 files, 0 unparseable, 2 hits, both in `_multipart.py`
(lines 20, 23). Instrument two: regex sweeps for `["']map["']`,
`["']operations["']`, `post_data|get_form_data|form_data`,
`_MULTIPART_CONTROL_FIELDS` - same 6 pre-change code sites, no f-string
part or second reader anywhere else. Every hit is homed: F1 (below)
owns the definitions; the message is projection.

### Challenges

The rule's variation axes: spelling (a rename), cardinality (a third control
field), parser divergence (upstream reading different fields). Counts are
authoritative definitions: the views tuple is one; the client guard set +
envelope keys + message are one one-edit region (one function, one pass).
Consumers, oracles, projections listed under F1, never counted.

- C1 rename (spec renames `operations`): views tuple + client region must
  move together - count 2 pre, 1 post (the leaf). Decisive.
- C2 third field: required field - both move (the guard must cover it or
  bypass; the emitter must emit it or post spec-invalid bodies) - count 2.
  Optional field - the guard moves; the emitter need not, but the guard
  still correctly tracks the full spec set (a `files=` key colliding with
  any spec field name posts a body the server misreads, so reserving it
  stays the fail-at-the-source verdict). Count 2-or-1 with the nuance
  recorded; either horn keeps one contract.
- C3 upstream reads different fields: guard must cover what upstream
  parses, emitter must emit what servers parse - count 2 pre, 1 post.

Experiments: (a) the AST census probe, execution-verified in the shared
tree before and after (`uv run python /tmp/dryf39/census_probe.py`: 119
files / 6 hits pre, 120 files / 2 hits post, 0 unparseable both) - rejects
hidden spellings (f-string parts, second readers). Read-only; no package
import beyond `__file__` resolution. (b) The `RuntimeError` exoneration
probe for the D1 errors below: the conftest overflow loop re-run with
zero package imports reproduces the failure - rejects item causation.
(c) Import-direction check by reading: the leaf imports nothing
first- or third-party, so neither consumer can gain a cycle or weight;
execution-verified implicitly by every green suite importing both.

## Findings

### F1 - the multipart control-field names (consolidated)

- Contract + variation: the multipart request specification's control
  fields, `operations` and `map`. Varies only with the specification and
  the parser that reads it (rename, third field, parser divergence).
- Sites + roles. Definitions (2 pre, 1 post): `views.py`
  `_MULTIPART_CONTROL_FIELDS` (guard iteration set); `client.py`
  `_build_body` one-edit region (guard set + envelope keys). Consumers:
  `_reject_lossy_multipart_control_fields` (loop, both transports via the
  mixin), the guard expression, the emission dict. Oracles: the unit,
  view, live hand-built, and live round-trip rows named in axis 5, plus
  upstream's twin reads (0.324.0, both bodies read). Projections: the
  docstrings, comments, and client message named in axis 5.
- Challenges: C1 count 2, C2 count 2-or-1 (nuance recorded), C3 count 2;
  all count 1 post. The file item's count-2 nomination (FC1) is confirmed
  on fresh evidence with independently derived axes.
- Owner + lifetime: new leaf `django_strawberry_framework/_multipart.py`
  by principle 7. Existing candidates fail: `views.py` would make test
  support import a sibling endpoint leaf for one constant (sibling
  machinery, R1); `testing/client.py` would reverse production onto test
  support and drag `django.test` into URLconf processes (R2);
  `_request_body.py` is barred by standing J7 (R3); `scalars.py` owns
  values, not envelope vocabulary (R4); `conf.py` owns settings (no row -
  not a setting, no shared form considerable). The leaf is the narrowest
  cohesive owner both consumers import with no reversed dependency and no
  sibling machinery: it imports nothing, holds three import-time
  constants (two names + the pair derived from them), never mutates, and
  has no invalidation - a pure derivation published at import.
- Migration: the leaf defines `_MULTIPART_OPERATIONS_FIELD`,
  `_MULTIPART_MAP_FIELD`, and `_MULTIPART_CONTROL_FIELDS` derived from
  them (grammar prose moved from `views.py` to the owner, principle 10).
  `views.py` deletes its definition and imports the pair; its consumer
  line is byte-identical. `client.py` imports all three: the guard reads
  `set(_MULTIPART_CONTROL_FIELDS)`, the emission keys on the two names.
- Distinct behavior: upstream's literals stay (R7); all test literals
  stay (R8); all prose stays literal including the client message (R9,
  which also records the hunt-line collision that barred interpolation).
  The pair-only leaf shape (positional indexing at the emitter) was
  refused (R5); the reverse import direction was refused (R2).
- Behavioral proof, each execution-verified in slot-2 unless noted:
  P-unit 252 passed combined - gate 2 + client 49 + views 201 (run
  `dry-20261001T170337-51d013` on final bytes; the gate is born green) -
  rejects changed emission/guard behavior and any second code spelling.
  P-live 12 passed over the lossy matrix (both colors), marker scope,
  survivor, and map-shape rows (run `dry-20261001T165834-e248ef`) -
  rejects changed wire behavior. P-roundtrip 3 passed, sync x2 + async
  x1 (run `dry-20261001T165945-eabc2f`) - rejects broken emit-to-parse
  coherence. P-types on final bytes: basedpyright 0/0/0 (run
  `dry-20261001T170340-790da5`), check_any 128 uses at 89 sites exit 0
  (run `dry-20261001T170347-0771a2`), truthful-reads tier-1 0 errors 0
  (run `dry-20261001T170347-4e08a2`) - no new cast, Any, or suppression
  (none added). Static-reviewed: the
  views consumer line is byte-identical apart from the import; the
  client compositions are name-for-literal with identical values.
  Cells sharded/pg: inapplicable by construction - the change moves
  wire-vocabulary constants and adds a source census; no queryset, DB
  alias, or dialect decision is touched. Worker-2 judges.
- Structural gate: `tests/test_multipart.py::test_control_field_names_are_spelled_only_in_the_owner`
  (exact-match AST census: hits must equal two in `_multipart.py`) plus
  `::test_control_fields_pair_derives_from_the_named_fields` (the pair
  derives, never re-spells). Negative control: the hand-copy mutant
  restoring `{"operations", "map"}` at the client guard - behavior
  preserved, gate red. Proved via [`prove`][prove] (runs
  `dry-20261001T170022-1d4c28`, `dry-20261001T170033-177537`): baseline
  green, mutant exactly 1 failed / 50 passed, verdict pinned, restore
  byte-proven (blob `ee6f26bc` before and after). Every behavior oracle
  passes the control, as required.
- Coupling: none. The leaf imports nothing; no other finding depends on
  this one; no defect blocks landing (D1 is environmental and disjoint).
- Freshness: HEAD `dd0b6691`; `testing/client.py` dispatch-WT `00f62a11`
  / HEAD `4d6791fa` / final-WT `ee6f26bc`; `views.py` dispatch-WT
  `432c6e49` / HEAD `fbf00ddf` / final-WT `c944b4be`; `_multipart.py`
  final-WT `ea88e966` (no HEAD blob, new); `tests/test_multipart.py`
  final-WT `12437287` (no HEAD blob, new). Excluded by body:
  `_strawberry_patches.py` WT `6257eaa0` / HEAD `521b5cff`,
  `consumers.py` WT `6e48bd70` / HEAD `8e33fc3c`, `scalars.py` WT
  `54f53f9b` / HEAD `f203b79e`, `middleware/request_body.py` WT
  `1febddbc` / HEAD `63a9a4a8`, `_request_body.py` WT `3a91f361` /
  HEAD `fdeb041f`, `conf.py` WT `372b2344` / HEAD `9c858b9a`,
  `testing/_wrap.py` WT==HEAD `4a6c4098`. Oracles as read:
  `tests/testing/test_client.py` WT `517cf1e6` / HEAD `fe01478e`,
  `tests/test_views.py` WT `a1de5141` / HEAD `715f3808`,
  `test_transport_api.py` WT `6d65274f` / HEAD `b1681e8c`,
  `test_client_api.py` WT==HEAD `4a04369d`,
  `test_uploads_api.py` WT==HEAD `dcbcbf61`. Searched population: 119
  files pre, 120 post (census probe, 0 unparseable both). Upstream
  strawberry-graphql 0.324.0, both `parse_multipart` bodies read.
  Prior nomination `dry-file-testing__client.md` WT `a71d60d5`
  (untracked; trigger input only, re-derived fresh). Any fingerprint
  change reopens the finding.

### R1 - client imports the views tuple, no new leaf (rejected)

Contract difference: none on the names - refused on dependency shape
(principle 7): test support importing a sibling endpoint leaf for one
constant is importing a sibling flavor for its machinery, and layers
test support over the production endpoint. Durable home: the leaf
module docstring states both transports read it. Trigger: `views.py`
slimming to an import-weightless kernel - architectural, never
expected.

### R2 - views imports the names from the test client (rejected)

Contract difference: direction. Production URLconf code depending on
test support reverses the dependency and drags `django.test` into
serving processes. Durable home: this record (no code cites the
reversed edge). Trigger: none - the direction is fixed.

### R3 - home the vocabulary in `_request_body.py` (rejected)

Converges with the verified J7 rejection on fresh evidence: that
module answers one boolean about bytes and never inspects their
meaning; the trigger (a measurement genuinely depending on declared
type) has not fired. Durable home: the standing J7 row.

### R4 - home the vocabulary in `scalars.py` beside `Upload` (rejected)

Contract difference: the scalar owns the file value type; the envelope
field names are transport vocabulary read by the view guard and the
upload builder, never by the scalar. Durable home: the leaf docstring.
Trigger: the envelope collapsing into the scalar type - never
expected.

### R5 - pair-only leaf, emitter indexes positions (rejected)

Contract difference: shape, not names. Naming only the pair forces the
emission into `FIELDS[0]` / `FIELDS[1]`, coupling the wire order to
positional indexing no reader can check. The leaf names both fields
and derives the pair. Durable home: the leaf (the shape it has).
Trigger: none - a refused shape, recorded so no cycle re-litigates.

### R6 - derive the guard from the emission dict instead (rejected)

Considered: build the envelope dict first, then `set(envelope) &
set(files)`, removing the guard's set without a leaf. Contract
difference: it removes the within-client restatement but leaves the
client region and the views tuple as two definitions - the cross-file
count stays 2. The leaf subsumes it: both lines read the owner.
Durable home: the leaf. Trigger: none.

### R7 - consolidate upstream's `parse_multipart` literals (rejected)

Contract difference: population. Those spellings live in the installed
dependency and cannot be owned; they stand as the independent backstop
(a mistyped owner fails against them). Durable home: the leaf
docstring states the backstop. Trigger: upstream vendoring - never.

### R8 - tests import the constant instead of spelling literals (rejected)

Contract difference: role. Test expectations are independent oracles:
the map changes, the tests fail, the oracles never update ([DRY][dry]
vocabulary). Every oracle in `tests/` and `examples/` spells literals
today; zero import the constant. Durable home: each oracle file (as
written). Trigger: none - principle-level.

### R9 - prose mentions compose by name (rejected)

Contract difference: role. Docstrings, comments, and the client
reserved message are projections: they describe, never own, and stay
literal. This includes the client message line, whose interpolation
was additionally barred because the line is hunt-dirtied
(truth-migration `_safe_arg_repr` to `truth.render`): a first draft
interpolated it, was caught by the attribution check, and was reverted
byte-for-byte. Durable home: the leaf docstring (grammar) for the
rule; each prose site for its wording. Trigger: none - projections
are never owned.

No sub-rule index rows are owed: the client triple is one region of
F1, not a family, and every considered separation above terminates in
a rejection. Worker-0 adds no rows for this item.

## Defects

D1 (pre-existing, environmental - route to the maintainer via Worker-0; blocks
nothing in this item): `test_transport_api.py::test_a_multipart_operations_document_nested_past_the_c_stack_is_refused`
and its async twin error at setup because the session fixture
`deepcopy_overflow_operations_text` (`conftest.py:322`) raises
`RuntimeError`: `json.loads` parsed a 262144-deep document without
overflowing on this interpreter (CPython 3.14.2), so
`_json_loads_overflow_depth` (`conftest.py:253`) finds no overflow
depth. Failing command: `uv run python [scripts/workspace.py][workspace] run
dry/multipart-f39/consolidate -- pytest -n0 --no-cov
"examples/fakeshop/test_query/test_transport_api.py::test_a_multipart_operations_document_nested_past_the_c_stack_is_refused"`.
Exoneration: the probe loop re-run with zero package imports
reproduces the same outcome, so no tree edit of any item can cause
it - the fixture's recursion assumption no longer holds on this
interpreter. Owner: the root `conftest.py` transport fixture. The
item's behavioral proof does not depend on these two rows.

No new defect was found while tracing. The file item's D1 (non-`str`
`files=` key) and D2 are already homed to closeout and are untouched
by this change (the walker is not among the edited lines).

## Judgment

One rule, two definitions, one contract: the package spelled the
specification's control-field names in the view guard and the test
client emitter, and every variation axis moved both. The vocabulary
now lives once in `_multipart.py`, both consumers compose it by name,
all oracles still spell literals, and the census gate fails exactly
the bypass it guards. Net: +2 files (leaf + gate), the 6 consumer
code spellings replaced by 2 owned ones, zero behavior change across
267 passing rows.

## Implementation (Worker-1)

Tracked changes (all vs `ITEM_BASELINE=89ca5972`, content-attributed;
hunt/maintainer hunks in the same files preserved byte-for-byte):

- NEW [`django_strawberry_framework/_multipart.py`][multipart] - owner:
  `_MULTIPART_OPERATIONS_FIELD`, `_MULTIPART_MAP_FIELD`,
  `_MULTIPART_CONTROL_FIELDS` (derived pair) + grammar docstring.
- [`django_strawberry_framework/views.py`][views] - deleted the definition +
  its comment (moved to the owner); added the pair import. Consumer
  line unchanged.
- [`django_strawberry_framework/testing/client.py`][client] - added the leaf
  import; guard set, emission keys compose by name. Message line
  untouched (projection + hunt-dirtied).
- NEW [`tests/test_multipart.py`][gate] - structural gate:
  `test_control_field_names_are_spelled_only_in_the_owner` (AST
  census), `test_control_fields_pair_derives_from_the_named_fields`
  (derivation pin).

Proposed `## Owned changes` row for Worker-0 to transcribe: Run-11
Family `multipart-control-field-names` (CONFIRM-consolidated;
+98/-8: new leaf 29 + new gate 57 + consumer reshapes +12/-8): the
four paths above with the symbols named here. After
every edit I ran `uv run ruff check --fix` then `uv run ruff format`
on exactly the touched `.py` paths (never `.`), plus
`check_trailing_commas.py --check` on the same paths - all clean.
The three whole-scope gates ran green in slot-2 (run ids under F1).
No `pragma: no cover`, no new `Any`/cast/suppression, no public
symbol without its docstring clause, no `ALLOWED_ANY` change (no
allowlisted site moved).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[client]: ../../django_strawberry_framework/testing/client.py
[multipart]: ../../django_strawberry_framework/_multipart.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[gate]: ../../tests/test_multipart.py

<!-- examples/ -->

<!-- scripts/ -->
[prove]: ../../scripts/prove_failability.py
[workspace]: ../../scripts/workspace.py

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Own trace, formed before opening `## Findings` (address
`dry/multipart-f39/verify-1`; HEAD `dd0b6691` unmoved throughout).

(a) Sites + roles. Pre-change authoritative definitions: 2 maintenance
units - the `views.py` tuple `_MULTIPART_CONTROL_FIELDS` (lossy-guard
iteration set) and the `client.py` `_build_body` vocabulary (guard set
+ emission keys, one method, one edit moment). Consumers: the views
lossy loop (both transports via the one mixin method), the client
guard expression, the client emission dict. Oracles: unit / view /
live hand-built / live round-trip rows spelling literals, plus
upstream's twin `parse_multipart` reads (installed 0.324.0, both
bodies read by me: `sync_base_view.py` and `async_base_view.py` each
`.get("operations")` / `.get("map")`). Projections: docstrings,
comments, the client reserved message. Post-change: 1 definition
(the leaf), 3 consumer compositions by name. Owner I would choose:
a new dependency-free leaf - the client must not inherit views'
import weight and production must not depend on test support, so no
existing candidate works and dependency direction (principle 7) wins.
That is exactly the owner W1 built; no difference to reconcile.

(b) Counts. My own exact-match AST census (`/tmp/w2-f39/census.py`):
pre 6 hits (`testing/client.py:286` x2, `:299` x2, `views.py:163`
x2), post 2 hits (`_multipart.py:20`, `:23`), 0 unparseable both.
File-population arithmetic reconciled: 117 tracked `.py` at
`89ca5972` + 2 untracked (`utils/truth.py`, `utils/lazy.py`) = 119
pre; + `_multipart.py` = 120 post. W1's "2->1" matches my "2
maintenance units (3 spelling sites, 6 hits) -> 1 owner (2 hits)";
the only wording gap is W1 naming the client message inside the
"one-edit region" while also (correctly) classifying it as
projection - immaterial, since projections are never counted and the
message contributes zero census hits either way.

(c) Enumeration + matrix, member by member. Every census hit homed
(F1 owns the definitions; message is projection). My own regex
sweeps (both quote styles, `post_data|get_form_data|form_data`,
`_MULTIPART*`) agree: no f-string part or second reader. Axis 1/6
exclusions re-verified by body: no code spelling in
`_strawberry_patches.py` (its `_MULTIPART_TRAVERSAL_ERRORS` /
`_UPSTREAM_MULTIPART_PARSE_REASON` are map-content/upstream-reason
contracts, not field names; its delegates wrap upstream's parse),
`consumers.py`, `middleware/request_body.py` (prose only),
`testing/_wrap.py`, `scalars.py`, `conf.py`. Axis 2: both views
`parse_multipart` overrides + both client `query()` colors share the
one method each - read, confirmed. Axis 3: no derivation anywhere
pre (all sites spelled literals). Axis 4 is the family. Axis 5:
see (d).

(d) Roles + oracles intact. Only `tests/test_multipart.py` imports
the owner, and only for the structural pair-derivation pin (which
pins shape, never values); its census `wanted` set spells literals.
Every behavior oracle still spells literals (`tests/testing/test_client.py`,
`tests/test_views.py`, `tests/test_strawberry_patches.py`,
`test_transport_api.py`, round-trip files). Upstream backstop
untouched.

(e) Observable equivalence (principle 8). Emission: same keys,
same values, same insertion order - wire order verified EXPLICITLY
by execution (`/tmp/w2-f39/order_probe.py`: `list(body) ==
["operations", "map", "f"]`, matching the baseline literal's
construction order). Guard: `set(pair) & set(files)` is the
identical set operation; all three reserved shapes rejected by
execution. Lossy-guard iteration: identical tuple values in
identical order (first-raising-field order preserved). Both
transport colors share the one method per side; untouched lines.
No behavior gap; nothing returns to W1.

(f) Rejections R1-R9: each carries contract difference + trigger;
homes verified where claimed - R1/R7 leaf-docstring clauses exist
(both-transports lines 5-10, backstop lines 12-16), R3 standing J7
row exists (plan line 369), R8 oracle files as written (zero owner
imports, re-grepped), R9 message line byte-identical to
`89ca5972` (re-compared). R2/R4/R5/R6 homes are thin ("this
record", "the leaf", shape-as-home) but each names a real reason
the refused shape has no code site worth a prose clause; accepted.
Freshness: final pins re-hashed same-kind (`git hash-object`) 4/4
(`ee6f26bc`, `c944b4be`, `ea88e966`, `12437287`); HEAD pins
re-derived same-kind (`git rev-parse HEAD:<path>`) 8/8 including
`_wrap.py` WT==HEAD `4a6c4098`. Gate: born green in my copy (run
`dry-20261001T170954-e74af3`); failability RE-DERIVED with my own
manifest (`/tmp/w2-f39/manifest.json`, hand-copy guard mutant,
run `dry-20261001T171159-e13aad`): baseline 51 passed, mutant
exactly 1 failed (the census only) / 50 passed, verdict pinned,
restore byte-proven (`ee6f26bc` before and after) - W1's prove
record judged sound. Pending-None correct (every proof cites an
execution run; the two static-reviewed items are import moves /
name compositions, inspection-sufficient per DRY.md). Coupling
none (leaf imports nothing - read). Concurrency re-derived from
`git diff HEAD` content: all non-W1 hunks are the truth migration
+ the len-try deletion, all concurrent (no ledger row covers
either file - ledger read, lines 1435-1524); W1's 5 hunks avoid
every concurrent line (both import inserts purely additive,
guard/emission vs the message-line dirt on adjacent-but-distinct
lines, tuple-deletion region clean); the reverted first-draft
claim is consistent with current bytes.

(g) AGENTS.md prose + gates + rows. New files: no process
provenance, no banned word (9-word sweep clean), citations use
the package-relative `path::Symbol` form matching `views.py`'s
own precedent. Gate tier `tests/` judged right (a source census
is unreachable from GraphQL; precedent: the version/logger and
envelope census gates). `ruff format --check` + `ruff check` on
all four touched paths: clean. Type gates re-run in my copy:
basedpyright 0/0/0 (`dry-20261001T171117-f4f8aa`), check_any 128
uses at 89 sites exit 0 (`dry-20261001T171127-f0472d`),
truthful-reads tier-1 0 errors 0 (`dry-20261001T171131-00ea71`)
- all vs run-11 baseline, no new cast/Any/suppression, no
`ALLOWED_ANY` move owed (diff adds none). Behavior rows re-run
in my copy: gate 2 + client 49 + views 201 + live 12 + roundtrip
3 = 267 green, matching W1 row for row. Sharded/PG
inapplicable-by-construction judged sound (constants + census;
no queryset, alias, or dialect decision). mypy never run, never
cited.

(h) D1 judged truly pre-existing/environmental, correctly routed,
correctly non-blocking. Reproduced in my copy: both rows ERROR at
fixture setup with `RuntimeError: json.loads parsed a
262144-deep document without overflowing` (`conftest.py:269`;
run `dry-20261001T171059-0a0475`). Root `conftest.py` imports
stdlib + pytest only and is clean at HEAD; my standalone probe
with zero package imports reproduces the no-overflow outcome on
CPython 3.14.2 - no tree edit of any item can cause it. Owner
root `conftest.py`; disjoint from this item's proof; blocks the
gate row only.

Defects found by Worker-2: none.

Verdict: verified. Proposed Worker-0 transcription: the Run-11
`## Owned changes` row W1 drafted (4 paths, +98/-8) + tick Family
`multipart-control-field-names`; D1 to the maintainer routing at defect
homing.
