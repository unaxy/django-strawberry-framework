# DRY review: `relay-node-name-decode`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `relay-node-name-decode`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry.definition_for_graphql_name`
(confirmed, not inherited). Member files:
`django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/relay.py`
(both worktree-clean at `ITEM_BASELINE`
`e3c494be19ae06ebccb0de6b5c23707d1c5da2ce`; the only item hunk is a
4-line docstring trigger clause on `registry.py`, below).
Prior records used only as triggers: the definition-store item's R-F
(which assigned this rule here rule-wise —
[definition-store][dry-rule-definition-store] — verified, not inherited;
every edge below re-derived) and the relay file item
(`docs/dry/dry-file-relay.md`, verified). Never read any
`worker-memory/`.

## System trace

Rule: decoding a GraphQL type name back to its registered definition —
the inverse of the type-naming rule. Encode half: `Meta.name`
(validated once at class creation in
[base][base]`::DjangoType.__init_subclass__` via `_validate_meta`) →
stored as `definition.name` → derived once as
[definition][definition]`::DjangoTypeDefinition.graphql_type_name`
(`name` or `origin.__name__`, validated) → emitted on the wire by the
`type` branch of [relay-types][relay-types]`::encode_typename`.
Decode half: [registry][registry]`::TypeRegistry.definition_for_graphql_name`
scans `iter_definitions()` for a unique `graphql_type_name` match over
Relay-Node definitions only (miss / ambiguity arms), called from
exactly one production site: the no-dot branch of
[relay-types][relay-types]`::decode_global_id` Step 1.

The scan reads the encode grammar by name
(`definition.graphql_type_name == name`); it never re-derives the name
from `Meta` or `__name__` (probe E8). One grammar, one reader per
direction — the consolidation question is whether the two halves are
owned in two places. They are not: the decode owns no grammar copy.

Sites + roles. *Definition* (1): `definition_for_graphql_name`
(probe E7 census). *Encode grammar owner*:
`DjangoTypeDefinition.graphql_type_name` (1 property) +
`_validate_meta`'s `Meta.name` validation (1 site). *Sole production
caller*: `decode_global_id` no-dot branch
([relay-types][relay-types] line 803; the line-720 mention is prose).
*Downstream consumers* (compose by name, listed not counted): the root
`node`/`nodes` fields via
[root-relay][root-relay]`::_decode_or_graphql_error`
(`GLOBALID_INVALID` collapse); the write-side typed-id primitive
[root-relay][root-relay]`::decode_model_global_id` (Family
`typed-globalid-decode`, open); the public re-export
[testing-relay][testing-relay]`::decode_global_id`. *Parallel readers
of the same property* (each classified under Findings, listed not
counted): [filters-base][filters-base]`::_accepted_globalid_type_names`
(accepted-set validation, never a resolve); the inspect bare-name
resolver ([inspect][inspect]`::Command._resolve_bare_name`, SDL +
Python surfaces, all types, `CommandError`); connection naming
(`<TypeName>Connection`); finalizer audits + error text; both
`relay.py` typed-match error arms; `global_id_for` (mint side).
*Oracles*: the `tests/test_registry.py` 5-pack (match, Meta-name key,
non-Relay miss, unknown miss, ambiguity); `test_relay_interfaces.py`
round-trip rows (Meta-name round trip, parametrized encode→decode
over `model` / `type` / `type+model`, both-directions Step-2
rejections, non-Node raise); `tests/testing/test_relay.py` public
round trip; live `test_node_refetch_genre`,
`test_node_malformed_id_live` (+ async twin) in
[live-library][live-library]. All spell literals independently; none
reads the scan body. *Projections*: the scan docstring (contract +
arms + the new trigger clause), the `decode_global_id` Step-1
docstring, [spec-031][spec-031] Decision 8 (type-name branch),
[spec-032][spec-032] Decisions 3–5 (nullable refetch + `GLOBALID_INVALID`
boundary), [spec-035][spec-035] R3 (the all-types scan defined as a
separate primitive — see R-E).

Connected sources read for judgment, outside the members:
[definition][definition] (property + mirror clauses),
[base][base] (`Meta.name` validation + sole construction site),
[root-relay][root-relay] (decode consumers, stamp seam),
[testing-relay][testing-relay] (mint/decode helper pair),
[filters-base][filters-base] (strategy-aware validation),
[inspect][inspect] (`_resolve_bare_name` + `_sdl_type_name`),
[list-field][list-field] (target guard owns construction-time),
[connection][connection] (encode-side derivation),
[sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin.type_name_for`
(different namespace — see R-D), [filters-inputs][filters-inputs]
(set-name delegate, read for exclusion only). Excluded on strength of
body: every other package module (zero `definition_for_graphql_name`
vocabulary over the whole-package sweep; the E7 census walks the
package directory).

Attribution: the plan's `## Owned changes` ledger holds no row on any
family path (rows cover only `optimizer/walker.py`, two fakeshop live
files, `tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`) — confirmed by full read. Dirty paths in
the tree (`connection.py`, `filters/inputs.py`, `auth/mutations.py`,
forms/mutations/optimizer sets, tests, docs) are concurrent work;
every line this trace cites in `connection.py` / `filters/inputs.py`
sits outside their concurrent hunks (`git diff HEAD` grep for the
three rule tokens over both files: 0 hits). Member files were clean;
the one hunk below is this item's.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** `set-type-naming`
(`ClassBasedTypeNameMixin.type_name_for`) names FilterSet/OrderSet
input types from class names + suffixes — a different namespace with
no decode half (nothing maps a set GraphQL name back to a set class).
It is not this family's encode counterpart; the true encode side is
the `graphql_type_name` property + the `encode_typename` `type`
branch (see R-D). No flavor keeps a second name→definition map
(E7 census: 1 def, 1 production call).
2. **Sync/async twins.** The scan + property + Step-1 resolve are sync
dict work and string compares; `decode_global_id` is `def` with no
`async` twin. The node resolvers have sync/async twins but consume
`(type, node_id)` — they never re-decode. Trigger: an async twin of
the scan.
3. **Derived rather than repeated knowledge.** The name derives once
(the property); decode reads it (E8: body keys on the property,
`definition.name` absent, `Meta` absent, the single `__name__` read
is the ambiguity error text). A rename moves exactly one definition
(C1). Trigger: a second derivation site.
4. **Inverse / round-trip pairs.** Encode (property → wire slot) vs
decode (wire slot → definition via the scan) share one grammar — the
property — with one reader per direction. Decode is already the
single inverse (rejection F1); the same holds for the mint helper
(`global_id_for` calls `encode_typename` directly) and the testing
re-export (same function object).
5. **Contracts restated in another medium.** Production (grammar +
scan); oracles (independent literals, round-trip + arms pinned at
three tiers); projections (docstrings verified against bodies;
spec-031 Decision 8 pins the Step-1 branch; spec-032 pins the wire
envelope the scan's errors collapse into). The 5-pack's SDL remark
names the live tier without reading the owner.
6. **Enforcement by omission.** Non-Relay definitions are excluded by
an explicit predicate (`implements_relay_node`), oracle-pinned
(`ignores_non_relay_definitions`) — not omission. Unfinalized /
strategy-`None` candidates pass the scan but die at Step 2
(`test_decode_non_node_graphql_name_raises` pins the nearer arm).
No member lacks a guard its contract requires: no defect.

### Enumeration

Instrument: whole-package `definition_for_graphql_name` sweep (4 hits:
1 `def`, 1 production call at `types/relay.py` Step-1, 2 prose
mentions) + directory-walk caller census (E7: exactly
`types/relay.py:803`) + `graphql_type_name` reader classification
(above) + `Meta.name` write census (1 validation site, 1 record
slot, 1 property). Population: 117 `.py` (plan count, unchanged; no
adds/renames).

- `definition_for_graphql_name`: exactly 1 def; exactly 1 production
caller; Relay-only predicate + miss/ambiguity arms in one body.
- `graphql_type_name`: exactly 1 derivation (the property); construction
writes `definition.name` at exactly 1 site (`__init_subclass__`);
validation of `Meta.name` at exactly 1 site (`_validate_meta`).
- `encode_typename` `type` branch + `global_id_for`: the two mint
paths, both reading the property, neither duplicating it.
- `decode_global_id` model-label branch (`apps.get_model` +
`registry.get`): sibling key space (dot-presence dispatch), not a
second type-name definition (see R-F).

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace probes E1–E8 map onto
C1–C5 (8/8 `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Rename a type's GraphQL name (add/change/remove `Meta.name`) | **1** (property + creation-time validation; the scan reads the property, 0 added). Oracles: Meta-name key row, Meta round-trip row, live SDL row. Probes E1/E2. |
| C2 | Second naming scheme as decode keys (converter-applied SDL names) | **1** (the scan predicate; the inspect scan stays operator-side). No contract source requires SDL-name decode today (encode emits the property under the default converter; custom-converter wire shape is unspecified) — boundary noted, not a defect. Probe E8. |
| C3 | Second Relay type sharing one GraphQL name | **1** (the ambiguity arm names both). Oracle: ambiguous row. Probe E5. |
| C4 | `clear()` / rebuild between decode calls | **1 owner, 0 added** (the scan is an uncached live read; answers follow the store with no invalidation). Probe E6. |
| C5 | Answer name→type by cached index instead of the scan | **0 sites** (no index exists; adding one lands inside the scan body, co-located with the store — supports the owner choice). Probe E7. |

**Experiments (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --frozen --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-node-name-decode-w1
uv run --frozen --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --frozen --directory "$WS" python probe_name_decode.py
```

Proof (`CHECKS_PASSED=8/8`): round trip, Meta-name key (+ `__name__`
miss), miss naming, non-Relay invisibility, ambiguity naming both,
clear-then-rebuild with no stale answer, sole-caller census, body-read
shape. Status: `execution-verified`. Copy `__file__`:
`.../dry-ws/relay-node-name-decode-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/relay-node-name-decode-w1/examples/fakeshop/db.sqlite3`
(copy's own tree and database; the probes open no DB at all). No
source mutation in the proof; restores N/A.

Negative controls (same workspace, `registry.py` only, pristine backup
kept; each restored byte-identical, `9cc8bb55…`, re-verified):

- Control A (divergent: key on `type_cls.__name__`, Relay filter kept):
`pytest tests/test_registry.py -k definition_for_graphql_name` →
2 failed (`honors_meta_name`, `ambiguous_raises`), 3 passed. The
standing oracles can fail for the divergence they guard.
- Control B (behavior-preserving: inline `(definition.name or
type_cls.__name__)` re-derivation): same selection → 5 passed. No
behavioral gate can pin unity; only a source census could, which
[DRY.md][dry] forbids for gate-only findings.

One authorized shared-tree focused run (zero member edits in flight):
`uv run pytest tests/test_registry.py
tests/types/test_relay_interfaces.py tests/testing/test_relay.py -k
"definition_for_graphql_name or decode_type_name_routes or
meta_name_round_trip or encode_decode_round_trip or
type_plus_model_decodes or rejects_type_name_id or
rejects_model_label_id or routes_to_primary or non_node_graphql_name
or public_decode_round_trip" --no-cov -n0` → 17 passed.

## Findings

### F1 — name decode (REJECTED consolidation: decode is already the single inverse)

- **Contract + variation.** A GraphQL type-name slot resolves to the
unique Relay-Node definition whose `graphql_type_name` matches; miss
and shared-name raise. Varies on: Relay vs non-Relay population
(predicate, not omission); miss vs ambiguity (two arms, one body);
live store vs cleared store (answers follow, uncached).
- **Sites + roles.** *Definition*: the scan (1). *Encode grammar*:
the property (1) + creation validation (1). *Caller*: Step-1 no-dot
branch (1). *Consumers / oracles / projections*: as listed in System
trace.
- **Challenges.** C1 → 1; C2 → 1; C3 → 1; C4 → 1 owner, 0 added;
C5 → 0. Count > 1 nowhere in one rule: no duplication.
- **Owner + lifetime (principles 7, 4).**
[registry][registry]`::TypeRegistry.definition_for_graphql_name`
stands: the scan's answers are the store's lifecycle (E6 — `clear()` /
`unregister()` change them with no invalidation precisely because
the scan reads live F2 state through `self`); the sole caller already
holds the registry import; a free function in `types/relay.py` would
split the name-key rule from the store a future index must land in;
miss/ambiguity errors are registry-canonical `ConfigurationError`;
the predicate import stays in-function so the module-top edge keeps
its direction. Stored-derivation lifetime: there is no stored
derivation — pure per-call scan ("not cached"); validity key =
declare → `clear()`/`unregister()`; publish point = the F2 pair
inside `__init_subclass__`; who may mutate = the store lifecycles
only; reads = this scan + Step 1 (unguarded by design — the
finalized snapshot serves request-time decode).
- **Migration.** Decode body untouched. One 4-line docstring trigger
clause at the owner (projection; behavior identical — AST-identity
proof below). No test changes: the 5-pack + round-trip + live rows
already pin every arm.
- **Distinct behavior (stays separate).** The property derivation
(R-A: `Meta.name`-or-`__name__` + validation lives at the record);
Step-2 strategy enforcement (reads the recorded classification, a
different rule); the filter accepted-set (validates against a known
target, never resolves — R-C); the inspect scan (operator surfaces,
all-types, `CommandError` — R-B); connection `<TypeName>`
derivation (encode-side); the set-naming namespace (no decode half
— R-D); the model-label branch (different key space — R-F); the
spec-035 all-types scan (different population + ambiguity contract,
defined elsewhere — R-E).
- **Behavioral proof.** `execution-verified` for symmetry, keying,
all three arms, lifetime, sole-caller census, body-read shape
(workspace 8/8 + authorized 17-passed focused run, zero edits in
flight). `static-reviewed` for the zero second-scan census, the
oracle-body independence (plain test classes, literals), and the
docstring-vs-body prose. Observable behavior pinned: rename moves
one definition and the scan follows; unknown / non-Relay / shared
names raise with the pinned messages; cleared answers stay cleared
until rebuild. Control A rejects "the oracles cannot see divergence";
Control B rejects "a gate could pin unity".
- **Structural gate.** None owed, with proved reason: Control B (a
correct copy) passes every standing oracle, so no behavioral gate
can pin unity — same standard as the verified definition-store,
enum-cache, and subscription-masking items. Unity rests on the
sole-caller census (E7), the property-read body (E8), and triggers
T-scan / T-key / T-population below. Coverage that stays: the 5-pack
(fails a lost arm or a re-keyed predicate — Control A), the
round-trip rows (fail a broken inverse), the live node rows (fail a
broken wire path).
- **Coupling.** None. Adjacent verified items untouched; no edit here
can stale them (docstring-only; AST proof below).
- **Freshness.** Working-tree blob ids (`git hash-object`):
`registry.py` `612bea87…` (post-clause; pre-clause `9cc8bb55…` —
proofs ran against it, bridged by the AST-identity check below),
`types/relay.py` `52439862…`, `testing/relay.py` `df0dc72a…`,
`types/definition.py` `fa6c4d330…`, `types/base.py` `91c58747…`,
`relay.py` `c3c5aea5…`, `filters/base.py` `ba52351c…`,
`inspect_django_type.py` `46dffb3d…`, `sets_mixins.py`
`ad8987ea…`, `types/finalizer.py` `77fd9a2d…`,
`connection.py` `3c4d5dcb…` (concurrent cursor-guard hunk; cited
lines verified outside it), `filters/inputs.py` `06797dc7…`
(concurrent range-shape hunk; cited lines verified outside it),
`tests/test_registry.py` `e330cfb8…`,
`tests/types/test_relay_interfaces.py` `26fb2ccf…`,
`tests/testing/test_relay.py` `55e43ed2…`,
`test_library_api.py` `0e032df0…`. `HEAD` `bfaee91d`;
`ITEM_BASELINE` `e3c494be…` (member diff vs baseline: the clause
hunk only). Searched population: whole package (117 `.py`) for the
rule tokens; installed Strawberry read as contract anchor, not a
fingerprinted input. Any fingerprint change reopens the finding.
- **Reconsideration triggers (recorded at the owner).** T-scan fires
if a second production name-to-definition path appears; T-key fires
if decode keys on anything but `graphql_type_name`; T-population
fires if the Relay-only predicate widens. Durable homes: the new
docstring clause on
[registry][registry]`::TypeRegistry.definition_for_graphql_name`,
this finding, and the plan's `## Outcomes` via Worker 0.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A encode grammar vs decode scan. Difference: the property derives
and validates the name once; the scan inverts it by comparison,
deriving nothing (E8). A rename moves one definition. Trigger: T-key.
Home: the property docstring + the scan docstring + this finding.
- R-B inspect bare-name scan. Difference: operator tooling over SDL +
Python surfaces across all types (`CommandError`) vs wire decode over
one surface across Relay-Node types (`ConfigurationError` + Step-2
strategy gate). Different populations, keys, errors, consumers.
Trigger: the inspect path resolving a wire GlobalID slot (or decode
accepting SDL-converter names — see C2). Home: both docstrings + this
finding.
- R-C filter accepted-set. Difference: validates a presented name
against a known target's strategy; never resolves name → definition.
Trigger: a filter resolving an unknown target by name. Home:
[filters-base][filters-base]`::_accepted_globalid_type_names` + this
finding.
- R-D set-type-naming (`type_name_for`). Difference: class-derived
names for set input types; a different namespace with no decode half
— not this family's encode side. Trigger: a set-name→class resolve
path appearing (it would be its own family). Home:
[sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin` + this finding.
- R-E optimizer all-types scan ([spec-035][spec-035] R3). Difference:
sibling-concrete-type planning needs a non-Relay lookup with its own
ambiguity contract (fail closed, never first-match) — defined there
as a separate primitive because this scan's Relay filter and raise
contract cannot serve it. Trigger: that primitive landing (it must
not call this scan for non-Relay types). Home: spec-035 R3 + this
finding.
- R-F model-label branch. Difference: dot-presence dispatches two key
spaces — `app_label.modelname` via `apps.get_model` + `registry.get`
vs bare names via this scan. A change to one key space does not move
the other. Trigger: a unified key space. Home:
[relay-types][relay-types]`::decode_global_id` + this finding.

## Defects

None. Tracing found no contract break: every resemblance candidate
resolved to a separation above or to the single inverse. The
custom-`NameConverter` wire shape (live `type`-strategy emission
keeps Strawberry's default while decode keys on the property) is
unspecified by every contract source read — a boundary note, not a
defect; no owner, no fix inside this item.

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace; the one authorized shared-tree focused run executed green
(17 passed) with zero member edits in flight. No
`execution-deferred` items. `FAKESHOP_SHARDED=1` and Postgres cells
`inapplicable by construction`: every executed claim is import-time
class construction plus in-memory dict scans and string compares; the
probes open no DB (recorded `NAME` is the copy's own file, never
touched). Full-suite gate business is deferred to the final-gate item
with reason: the entry authorizes workspace runs plus one focused
`--no-cov` test, and a green unmutated suite would discharge no
failability proof for a rejection that proposes no gate.

## Judgment

Decode is already the single inverse of encode: one grammar (the
`graphql_type_name` property), one reader per direction, one
production caller, uncached lifetime bound to the store. The
maintainer's round-trip question resolves as: same table both
directions (the property), exact inverse, owned once — the scan
composes it by name and owns only the Relay-only match + miss /
ambiguity arms. Consolidation rejected; owner confirmed; one
projection-only trigger clause added; no defects.

## Implementation (Worker 1)

Tracked change (1 file, docstring-only): 
`django_strawberry_framework/registry.py` —
`TypeRegistry.definition_for_graphql_name` docstring gains the
reconsideration-trigger clause (+4 lines; behavior untouched).
Attribution: all three member paths clean at `ITEM_BASELINE` and at
`HEAD` before the edit; the hunk is this item's alone
(`git diff e3c494be19ae06ebccb0de6b5c23707d1c5da2ce --
django_strawberry_framework/registry.py` shows only it; the other
two member paths diff empty). No `## Owned changes` row exists on
any family path, so no conflict; Worker 0 appends:
`django_strawberry_framework/registry.py` — Family
`relay-node-name-decode` — `TypeRegistry.definition_for_graphql_name`
docstring trigger clause (projection; behavior untouched).

After the edit: `uv run ruff check --fix
django_strawberry_framework/registry.py` + `uv run ruff format
django_strawberry_framework/registry.py` — both green
(`format --check` + `check` pass on the path; scoped to the path so
no concurrent dirt is rewritten). INVERSE proof (docstring-only edit):
docstring-stripped AST of `HEAD:registry.py` vs worktree —
`AST-IDENTITY-NO-DOCSTRINGS: True` (read-only check, not a test run).
Per `AGENTS.md` no pytest after edits; the pre-edit focused run
(17 passed) still discharges the finding by that AST identity. No
`CHANGELOG.md` touch. No commit per standing rule.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-node-name-decode-w1`
(includes its own `.venv`, `probe_name_decode.py` holding the 8
executed checks, and `registry.py.pristine` holding the pre-control
backup). No manifest (no `prove_failability.py` run — no gate added,
none owed; Controls A/B are the hand-proved negative/positive pair).

Worker 0 rows: tick Family `relay-node-name-decode` (this artifact);
no `## Responsibility index` change (provisional owner + both member
files already covered); append the `## Owned changes` row above; no
defects to home.

## Independent verification (Worker 2)

Own trace first (derived before reconciling with `## Findings`).

**Sites + roles (mine).** *Definition* (1):
`django_strawberry_framework/registry.py::TypeRegistry.definition_for_graphql_name`
— scans `iter_definitions()`, predicate
`implements_relay_node(type_cls) and definition.graphql_type_name == name`,
three arms (unique / miss / ambiguity) in one body.
*Encode grammar* (1 property + 1 validation site):
`django_strawberry_framework/types/definition.py::DjangoTypeDefinition.graphql_type_name`
(`self.name or self.origin.__name__`, validated) +
`django_strawberry_framework/types/base.py::_validate_meta` (`Meta.name`
validation; sole construction site `__init_subclass__`).
*Sole production caller* (1):
`django_strawberry_framework/types/relay.py::decode_global_id` no-dot
branch (line 803; line 720 is prose). *Downstream* (compose by name,
not counted): `django_strawberry_framework/relay.py::_decode_or_graphql_error`
(`GLOBALID_INVALID` collapse),
`django_strawberry_framework/relay.py::decode_model_global_id` (seam to
`typed-globalid-decode`, left open),
`django_strawberry_framework/testing/relay.py::decode_global_id`
(re-export, same function object). *Parallel readers of the property*
(validation/display, never resolution, not counted):
`filters/base.py::_accepted_globalid_type_names` (accepted-set for a
known target), `relay.py::_check_typed_match` (error text on
already-resolved types), `connection.py` (`<TypeName>Connection`),
`inspect _resolve_bare_name` (operator SDL+Python surfaces, all types,
`CommandError`), finalizer audits/error text, `global_id_for` (mint
via `encode_typename`). *Oracles*: `tests/test_registry.py` 5-pack
(independent literals, no owner reads — confirmed by reading the
bodies), round-trip rows in `tests/types/test_relay_interfaces.py`,
`tests/testing/test_relay.py`, live node rows in
`test_library_api.py`. *Projections*: scan docstring (+4 trigger
clause), Step-1 docstring, spec-031 Decision 8, spec-032 Decisions
3–5, spec-035 R3.

**Definition counts (mine).** C1 rename → 1 (property + validation;
scan reads the property). C2 second scheme → 1 (scan predicate).
C3 shared name → 1 (ambiguity arm). C4 clear/rebuild → 1 owner,
0 added (uncached live read). C5 cached index → 0 (no index
exists). No second `definition_for_graphql_name` def anywhere;
no second production call site.

**Owner I would choose.** Same:
`TypeRegistry.definition_for_graphql_name`. Answers are store
lifecycle (`clear()` drops `_definitions`; `unregister()` detaches;
definitions are created fresh after every clear, so an uncached
scan cannot go stale); the sole caller already holds the registry
import; a free function in `types/relay.py` would split the
name-key rule from the store a future index must land in; errors
are registry-canonical `ConfigurationError`; the in-function
`implements_relay_node` import keeps the module-top edge direction.
Owning it at the caller (`decode_global_id`) would divorce
lifecycle answers from lifecycle ownership. Concur.

**Population completeness (sole-caller re-census, mine).**
`grep -rn definition_for_graphql_name --include=*.py
django_strawberry_framework tests examples`: package hits are the
`def` (registry.py:462), an inline comment (registry.py:487), a
docstring mention (types/relay.py:720), and the call
(types/relay.py:803) — exactly 1 production call. Test-only hits:
`tests/test_registry.py` (5-pack) + two prose mentions in
`tests/types/test_relay_interfaces.py`. Zero hits in
`consumers.py`, `management/`, `relay.py` (root), examples
production code; no `subscriptions` module exists. The sole-caller
claim is TRUE.

**Round-trip judgment.** Encode `type` branch returns
`definition.graphql_type_name` verbatim (types/relay.py:536);
decode compares `definition.graphql_type_name == name`
(registry.py:494) — the SAME property object, no parallel
spelling. Body-read probe (fresh WS): code body keys on the
property; `definition.name` absent; `Meta` absent;
`__name__` occurs exactly once, in the ambiguity error text.
`set-type-naming.type_name_for` (`f"{cls.__name__}{suffix}"`) is a
different namespace with no decode half — NOT the encode
counterpart. Concur: same table both directions, scan composes by
name and owns only Relay-only match + miss/ambiguity arms.

**C4 caching judgment.** Uncached is CORRECT here, not merely
tolerable. `clear()`/`unregister()` mutate the answer set with no
invalidation protocol; a cached index would need new shared state
on the register/unregister/clear paths, which principle 4 forbids
("pure derivation says 'not cached'"). Perf: one linear scan per
`node()` decode over # registered types — no hot-path pressure
shown; a future index lands inside the scan body co-located with
the store (C5 = 0 supports the owner). Live-read probe:
decode → clear → miss → re-register → decode-new-identity, all
pass. Concur.

**Owner-clause edit judgment.** Item-scoped diff vs
`ITEM_BASELINE`: registry.py +4 docstring-only (trigger clause);
types/relay.py empty — confirmed. `git diff HEAD --
registry.py` shows ONLY that hunk (the `M` status on registry.py
is this item's own edit). The clause carries no source refs, no
process provenance, ASCII-only; no test/CHANGELOG touch needed
(projection). AST-identity re-verified myself
(`AST-IDENTITY-NO-DOCSTRINGS: True`, HEAD vs worktree). Ruff run
myself on the path: `format --check` + `check` both pass.
Concurrent dirt (`connection.py`, `filters/inputs.py`, etc.)
preserved: diff hunks there contain 0 hits for the three rule
tokens. Compliant.

**Gate judgment.** Concur — no gate owed, Control B standard.
Re-executed both controls myself in a fresh post-edit WS:
Control A (divergent `type_cls.__name__` key):
`pytest tests/test_registry.py -k definition_for_graphql_name` →
2 failed (`honors_meta_name`, `ambiguous_raises`), 3 passed —
oracles are not vacuous. Control B (correct
`(definition.name or type_cls.__name__)` re-derivation) → 5
passed — no behavioral gate can pin unity; only a source census
could, which DRY.md forbids for gate-only findings. Same
standard as the verified definition-store / enum-cache /
subscription-masking items. Unity rests on the E7 census +
property-read body + T-scan/T-key/T-population triggers. Concur.

**Freshness re-hashed (mine, `git hash-object`, worktree).**
`registry.py` `612bea87…`, `types/relay.py` `52439862…`,
`testing/relay.py` `df0dc72a…`, `types/definition.py`
`fa6c4d330…`, `types/base.py` `91c58747…`, root `relay.py`
`c3c5aea5…`, `filters/base.py` `ba52351c…`,
`inspect_django_type.py` `46dffb3d…`, `sets_mixins.py`
`ad8987ea…`, `types/finalizer.py` `77fd9a2d…`,
`connection.py` `3c4d5dcb…`, `filters/inputs.py` `06797dc7…`,
`tests/test_registry.py` `e330cfb8…`,
`test_relay_interfaces.py` `26fb2ccf…`,
`tests/testing/test_relay.py` `55e43ed2…`,
`test_library_api.py` `0e032df0…`. Every prefix matches W1's
claim — no fingerprint changed; verification is fresh. HEAD
`bfaee91d`; member diff vs `ITEM_BASELINE` is the clause hunk
only.

**Pending execution: empty — judged.** No `execution-deferred`
proofs exist. My fresh-WS probe 9/9 `execution-verified`
(round-trip, Meta-key miss, no-dot decode branch, non-Relay
invisibility, unknown miss, ambiguity naming both,
clear-rebuild live read, sole-caller census, body-read shape;
copy `__file__`
`.../dry-ws/relay-node-name-decode-w2/django_strawberry_framework/__init__.py`,
DB `NAME`
`.../dry-ws/relay-node-name-decode-w2/examples/fakeshop/db.sqlite3`,
never opened). `FAKESHOP_SHARDED=1`/Postgres
`inapplicable by construction`: every executed claim is
class construction + in-memory dict scans + string compares.
W1's authorized focused shared-tree run (17 passed, zero member
edits in flight) still discharges via AST-identity. Full-suite
gate belongs to the final-gate item.

**Open seam.** `decode_model_global_id` (root relay.py:313)
composes `decode_global_id` by name and adds model-check + pk
coercion — a distinct rule correctly left open to Family
`typed-globalid-decode`, a seam not a decision. Concur.

**Per-claim agreement.** REJECT verdict ✓; single inverse ✓;
same table both directions ✓; scan composes encode by name ✓;
`set-type-naming` not the encode half ✓; 1 definition ✓;
1 `Meta.name` validation site ✓; exactly 1 production caller ✓;
`DjangoNodeField`/`DjangoNodesField` collapse +
`decode_model_global_id` seam ✓; C1–C5 counts ✓ (all
re-derived, C4/C5 judgments independently reasoned above);
owner + lifetime ✓; R-A..R-F separations ✓ (each re-opened:
R-D namespace+no-decode-half confirmed in `sets_mixins.py`
body; R-B operator-vs-wire confirmed in `_resolve_bare_name`
body; R-E spec-035 primitive correctly not built here);
probe 8/8 + Controls A/B ✓ (independently re-executed as 9/9 +
2-fail + 5-pass); 17-pass focused run ✓ (bridged by my
AST-identity re-check); docstring-only edit ✓; no defects ✓.
No differences. No new candidates found on any matrix axis.

**Defects found (Worker 2, homed under `## Defects` above).**

None. No contract break found while tracing; every
resemblance candidate resolves to the single inverse or to a
separation R-A..R-F above. The custom-`NameConverter` wire-shape
boundary stays a note, not a defect — concur, no owner, no fix.

Worker 0 rows: tick Family `relay-node-name-decode` as
`verified (Run 0.0.15 2026-09-19-1; REJECTED single-owned,
trigger at owner docstring, no gate; docstring clause only; no
pending execution)`; Responsibility index row status `open` →
`rejected`; append Owned changes row
`` `django_strawberry_framework/registry.py` — Family
`relay-node-name-decode` — `TypeRegistry.definition_for_graphql_name`
docstring trigger clause (projection; behavior untouched) ``;
no defects to home; remove by explicit path after `verified`:
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-node-name-decode-w2`
(holds `probe_w2.py` + its own `.venv`).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[dry-rule-definition-store]: dry-rule-type-registry-definition-store.md

<!-- docs/SPECS/ -->
[spec-031]: spec-031-globalid_encoding-0_0_9.md
[spec-032]: spec-032-full_relay-0_0_9.md
[spec-035]: spec-035-optimizer_hardening-0_0_10.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[connection]: ../../django_strawberry_framework/connection.py
[definition]: ../../django_strawberry_framework/types/definition.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[list-field]: ../../django_strawberry_framework/list_field.py
[registry]: ../../django_strawberry_framework/registry.py
[relay-types]: ../../django_strawberry_framework/types/relay.py
[root-relay]: ../../django_strawberry_framework/relay.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py

<!-- tests/ -->

<!-- examples/ -->
[live-library]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Bounded re-review (Worker 2, Q11)

Phase 1 trace only. Prior findings not read; no status set; no verdict on prior findings proposed.
Role: Worker 2, reconciliation queue Q11, bounded re-review of whether name-decode findings still
hold after the worktree hardening of the graphql_type_name property. Zero source edits made.

Scope traced from CURRENT source, HEAD bytes vs worktree bytes distinguished:

- django_strawberry_framework/types/definition.py::DjangoTypeDefinition.graphql_type_name
  (CURRENT worktree body read in full, lines 229-272; HEAD body via git show HEAD: same path).
- django_strawberry_framework/registry.py::TypeRegistry.definition_for_graphql_name (HEAD bytes).
- django_strawberry_framework/types/relay.py::decode_global_id plus
  django_strawberry_framework/types/relay.py::encode_typename type branch (HEAD bytes).
- Applicable contracts: DRY.md principle 2 (one owned translation), DRY.md principle 7
  (choose owner by responsibility); GOAL.md Trust boundary (type names come from application
  Python, TRUSTED side; wire is untrusted; package does not promise to contain hostile
  in-process objects).

Freshness fingerprints (HEAD blob vs worktree hash, separately):

- HEAD commit: bfaee91dcd332a5f86250fff90ab21b377bc674e (branch not switched, no commit).
- django_strawberry_framework/types/definition.py HEAD blob fa6c4d330e72d7dceb5f2af7f56e460c6cf72383
  (git ls-tree HEAD); worktree hash 01f78d93baf8fb6ca3ab11df1a2a495640fb7655 (git hash-object).
- django_strawberry_framework/registry.py HEAD blob 9cc8bb553fd417fc465809a541769a8383469cda;
  worktree hash 612bea87fdcf5e5a254caf70c9947b9535f638c3.
- django_strawberry_framework/types/relay.py HEAD blob 5243986223547af7bcab691032e1d6792655fd9d;
  worktree hash c333c785614be2e7a66d6c12e3c6d3d247cbc8c9.
- Prior verification fingerprinted HEAD fa6c4d33 (clean then); confirmed above as HEAD blob for
  definition.py.

Hunk attribution (never edited):

- Worktree vs HEAD diff for definition.py is 4 hunks, all guarded-interrogation hardening by
  another concurrent session (uncommitted, no ledger row claimed here): (1) graphql_type_name
  isinstance guard plus str.__str__ guard; (2) related_target_for isinstance plus
  str.__str__ guard; (3) _normalize_pk_name guard; (4) _resolves_id_off_pk id-attr guard.
  Scoped hunk for this phase is (1) only. Left untouched as concurrent dirt.
- registry.py worktree diff is doc-only prose (reconsideration-trigger paragraph on the scan);
  no behavior change in definition_for_graphql_name. types/relay.py worktree diff is doc-only
  prose (relay-node-type-stamp reconsideration triggers); no behavior change in decode_global_id
  or encode_typename. Verified by git diff HEAD for each path.

(1) Benign-input equivalence verdict: SAME VALUES HEAD vs worktree (proved by body comparison).

- HEAD property body: try name = self.name if not None else origin.__name__ except
  BaseException to ConfigurationError Could not inspect; if not isinstance(name, str) to
  ConfigurationError must be a non-empty string with _safe_arg_repr; normalized =
  str.__str__(name) UNGUARDED; if not normalized to empty-name ConfigurationError; if regex
  miss or startswith __ to valid-GraphQL-name ConfigurationError; return normalized.
- Worktree property body: identical except two guarded interrogations: isinstance wrapped in
  try/except BaseException to False, and str.__str__(name) wrapped in try/except BaseException
  to ConfigurationError must be a non-empty string with _safe_arg_repr. _safe_type_name and
  _safe_arg_repr rendering unchanged (already present at HEAD); only the guards are new.
- Benign shapes take the identical path in both: absent Meta.name (None) reads
  origin.__name__; valid Meta.name string (for example Category in
  tests/types/test_base.py::test_meta_name_overrides_graphql_type_name) passes isinstance True
  and str.__str__ succeeds; empty string, bad-name, __-prefixed names hit the same two
  downstream ConfigurationError branches with byte-identical messages; benign non-string
  (for example int) hits the same must-be-a-non-empty-string branch (isinstance False in
  both, guard not triggered). No benign input reaches the new except arms. Therefore every
  benign value and every benign rejection is unchanged.

(2) Hostile-input behavior delta (raw escape at HEAD vs typed ConfigurationError at worktree):

- Plain non-string hostile (HostileName object with raising __str__/__repr__ but honest
  __class__): BOTH raise typed ConfigurationError must be a non-empty string with
  _safe_arg_repr rendering as <unprintable HostileName>. No delta; rejected before the
  str.__str__ line in both.
- Liar str (instance whose __class__ property returns str, so isinstance(x, str) is True
  although x is not a real str): HEAD passes the isinstance gate then str.__str__(x) raises
  raw TypeError (descriptor layout mismatch) escaping untyped. Worktree passes the guarded
  isinstance as True then catches the str.__str__ BaseException into typed ConfigurationError
  must be a non-empty string. Delta: raw TypeError vs typed ConfigurationError.
- Raising __class__ (property __class__ raises RuntimeError, so isinstance itself raises):
  HEAD escapes the raw RuntimeError from the bare isinstance call. Worktree catches it into
  is_str_name False and raises typed ConfigurationError must be a non-empty string. Delta:
  raw RuntimeError vs typed ConfigurationError.
- Str subclass with raising __str__ override: str.__str__(x) via the base descriptor bypasses
  the override and returns an inert exact str in both; no observable delta (both succeed).
  Noted for completeness; not a divergence.
- Hostile origin.__name__ access raising: BOTH raise typed Could not inspect the GraphQL type
  name (first try/except unchanged). No delta.

(3) Decode-scan dependence verdict: scan observes ONLY benign values; hardened behavior is
unreachable on the production decode path.

- HEAD registry.py::TypeRegistry.definition_for_graphql_name body: in-function import of
  implements_relay_node, list comprehension over iter_definitions filtering Relay-Node types
  with definition.graphql_type_name == name, 1 match returns, 0 raises miss
  ConfigurationError, 2-plus raises ambiguity ConfigurationError naming colliding origins.
  Worktree body is behavior-identical (only added prose paragraph).
- HEAD types/relay.py::decode_global_id body: input gate, GlobalID parse, slot read,
  str.__str__ normalization of slots, dot test routing to apps.get_model plus registry.get
  (model-label) or registry.definition_for_graphql_name (type-name, no dot), then
  effective_globalid_strategy enforcement via _accepts_model_label_decode /
  _accepts_type_name_decode. Worktree body behavior-identical for these lines.
- HEAD types/relay.py::encode_typename type branch: return definition.graphql_type_name
  (model/model+label branches return label_lower; callable branch validates). Unchanged.
- The scan calls definition.graphql_type_name per Relay-Node definition at decode time. Real
  registry definitions are built by types/base.py::_validate_meta at class creation, which
  rejects hostile Meta.name before any definition exists. _validate_meta Meta.name block is
  UNGUARDED isinstance plus UNGUARDED str.__str__(raw_name) at BOTH HEAD and worktree
  (verified worktree lines vs git show HEAD range; worktree diff touches optimizer_hints and
  new helpers, never the Meta.name hunk). Hence a liar/raising Meta.name escapes raw at type
  creation in both trees and never materializes a registry definition for the decode scan to
  read. Directly constructed _malformed_definition hostile names (test-only seam) never enter
  the registry. Therefore the worktree property hardening changes no value the decode scan
  can observe on any feasible production population.

(4) Definition counts (change challenge, per DRY.md):

- New naming scheme (change the derivation rule itself, for example prefix, case folding,
  fallback from origin.__name__): count 1. The single authoritative definition is
  django_strawberry_framework/types/definition.py::DjangoTypeDefinition.graphql_type_name
  (plus its owned _GRAPHQL_NAME_RE grammar). Every other site reads the property by name:
  registry scan, encode_typename type branch, connection generated name, filters/base
  accepted-type-names, filters/inputs owner-name helper, finalizer labels and audits,
  root relay expected/received comparison, testing/relay labels, inspect command. No second
  derivation found: origin.__name__ appears only inside the property (plus its docstring);
  no site re-derives self.name vs origin.__name__ inline. Consumers move by construction.
- Renamed type (change one type's declared name, for example Meta.name ItemType to Item):
  count 0 definitions. This is a declaration (consumer data via Meta.name, validated once in
  types/base.py::_validate_meta), not a rule change. Encode emits the new property value and
  the decode scan inverts the same property live, so the round trip follows with no owner
  edit. Verified against oracles below.

(5) Owners I would choose (DRY.md principle 7):

- GraphQL surface-name derivation: django_strawberry_framework/types/definition.py::
  DjangoTypeDefinition.graphql_type_name. Narrowest cohesive owner every legitimate consumer
  (registry, relay encode/decode, finalizer, filters, connection, inspect) can depend on
  without reversing a dependency or importing a sibling flavor; dependency direction wins.
  The _GRAPHQL_NAME_RE grammar lives with it (principle 10 prose at the owner).
- Type-name to definition inversion: django_strawberry_framework/registry.py::
  TypeRegistry.definition_for_graphql_name stays the single decode entry (type-name branch),
  keyed on the owner above, Relay-Node population only. No second production
  name-to-definition path exists; the BACKLOG non-Relay lookup is future scope, not a second
  definition today.
- Per DRY.md principle 2, encode (encode_typename type branch emitting the property) and
  decode (scan comparing the property) are two halves of one grammar owned at the property.

(6) Whether the delta breaks anything derived:

- No defect. No contract row is broken. Benign contract (valid/invalid/absent Meta.name
  mapping to the same emitted string or the same typed ConfigurationError) is preserved
  exactly. The hostile delta (raw escape to typed ConfigurationError on liar and
  raising-__class__ shapes) tightens fail-loud behavior without changing any accepted value.
- Reaching-input test under GOAL.md Trust boundary: a hostile Meta.name object (liar
  __class__, raising __class__, raising __str__ on a non-str) is application-Python shape.
  Feasible project shape under supported public API means code that could feasibly exist in a
  project using Meta.name as documented (a string literal such as name Item). No feasible
  project writes a __class__-lying object as Meta.name. Therefore the liar/raising shapes are
  the hostile-object robustness row, explicitly outside the package promise (GOAL: package
  does not promise to contain code running inside its own process; Django policy model).
  A behavior change here still needed a verdict, and the verdict is: tightening raw to typed
  is compatible, not a break; it needs no contract-row defect, never a release blocker. If a
  card is wanted it is a robustness row, not a defect.
- Decode findings dependence: because the scan only observes validated benign names, the
  delta cannot change miss vs hit vs ambiguity outcomes on any registry reachable through
  supported API. No prior-name-decode behavior is invalidated by this hunk on the evidence
  traced here.

Oracles READ (not written; standing behavior pins):

- tests/types/test_definition_relations.py::test_graphql_type_name_rejects_hostile_metadata
  (plain HostileName non-str): pins typed ConfigurationError with safe <unprintable
  HostileName> rendering. Holds at HEAD and worktree. Checked.
- tests/types/test_definition_relations.py::test_graphql_type_name_rejects_invalid_graphql_names
  (bad-name): pins typed valid-GraphQL-name rejection. Holds at both. Checked.
- tests/types/test_definition_relations.py::test_graphql_type_name_rejects_liar_name (NEW
  worktree-only, same session as the hardening; absent at HEAD per git show tail): pins typed
  must-be-a-non-empty-string for liar plus raising-__class__. Passes at worktree; would raw-
  escape at HEAD. Therefore no standing HEAD oracle pins raw-escape; the new oracle pins the
  hardened typed-reject. Checked, attributed as concurrent-test dirt, not edited.
- tests/types/test_base.py::test_meta_name_rejects_hostile_values_at_type_creation (plain
  HostileName at creation): pins typed Meta.name rejection. Exists at HEAD and worktree.
  Holds at both. Checked.
- tests/types/test_base.py::test_meta_name_overrides_graphql_type_name (Meta.name Category
  threads to Strawberry name): pins benign equivalence. Holds at both. Checked.
- tests/types/test_base.py::test_meta_name_rejects_an_empty_string and
  ::test_meta_name_rejects_invalid_graphql_names_at_type_creation: benign invalid pins,
  hold at both. Checked by inspection.
- No oracle found pinning raw escape for liar/raising names on graphql_type_name; nothing read
  requires raw behavior.

Method: body comparison HEAD vs worktree for the property; git diff HEAD for registry and
relay behavior lines; _validate_meta range comparison HEAD vs worktree; oracle reads at the
named test symbols. No execution run (no pytest per constraints); no source edits; concurrent
dirt preserved.

PHASE-1-TRACE-RECORDED docs/dry/dry-rule-relay-node-name-decode.md
