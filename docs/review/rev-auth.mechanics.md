# Review · Mechanics: `django_strawberry_framework/auth/` integration

Status: no-findings
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5676d4fc6310a5ff0d075771593a0f3068eb9406

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes` — the three auth file
items' rows stand verified — and the one Routed lead on this item,
from auth/queries.py Comments on
`tests/auth/test_mutations.py::_request_with_store`, judged below
under `## Cross-axis (for Comments)`),
`docs/review/rev-auth.md` (skeleton: `Status: reviewing`, blank
Path class). Sibling axis records `rev-auth.performance.md` and
`rev-auth.comments.md` did not exist at close (siblings run
concurrently); no foreign Handoff or
`## Cross-axis (for Mechanics)` owed. The main artifact carries no
Worker-2 sections yet. The three closed folder-file records
(`rev-auth__mutations.*`, `rev-auth__queries.*`,
`rev-auth__sessions.*`, all nine axis files incl. every Handoff
and verify section) were read whole for context; no finding below
re-files one of theirs — each prior verdict relied on is cited.

Target read whole as one component: the folder `__init__.py` (20
lines, blob `2e480818`, clean at ITEM_BASELINE per the plan),
`auth/queries.py` whole (121 lines), `auth/sessions.py` whole
(284 lines), and the `auth/mutations.py` seams (imports, family
label, message constants, `_SURFACE_FACTORY_NAMES`, the
declaration ledger + clear row, `_AuthMutationMetaSnapshot`,
`_make_permission_holder`, `_declared_auth_surface`,
`_reject_conflicting_permission_classes`, `_declare_auth_surface`,
`_declare_fixed_auth_surface`, `_sync_bridged_async_body`,
`_make_auth_field`, `_authenticated_actor_or_none`, the three
factories, `derive_register_fields`, the register step pair +
pipeline, `_synthesize_register_rider`, `register_mutation`,
`_resolve_user_primary_or_raise`, `bind_auth_mutations`).
`git diff ITEM_BASELINE --` the four folder files is empty: the
live tree equals the item baseline.

Orientation: `review_inspect.py` overviews at
`docs/review/temp-tests/auth-integration/mechanics/inspect/`
(json `init.json`, `mutations.json`, `queries.json`,
`sessions.json`). Leads only.

Seams traced by hand in both directions: the finalizer phase-2.5
slot (`types/finalizer.py`, `loaded_attr` guard + pre-bind reset
order), `registry.py` (`register_subsystem_clear`,
`iter_subsystem_clears`, `clear()`), the owners every shared rule
rides (`mutations/sets.py`, `mutations/inputs.py`,
`mutations/fields.py`, `utils/sessions.py`,
`utils/permissions.py`), the contract sources (`docs/README.md`
auth surface + transport matrix + error policy,
`docs/GLOSSARY.md` `auth-mutations` anchor, owner docstrings),
and the oracles (`tests/auth/test_mutations.py`,
`tests/auth/test_queries.py`, `tests/auth/test_sessions.py`,
`tests/auth/conftest.py`, `tests/auth/_helpers.py`,
`examples/fakeshop/test_query/test_auth_api.py`,
`examples/fakeshop/apps/accounts/schema.py`).

No symbol is moved or renamed by this record, so no `--cited-by`
sweep is owed; no defect (no HUNT fields) and no duplication (no
DRY fields). No workspace run was needed: every candidate
resolved against owner bodies, pinned oracles, and static greps
in the shared tree. No run ids.

Cells: no finding, so no Proof reaches a cell. For the record:
the folder reaches the database only through Django natives on
the request's own alias (session + user rows; zero `using` /
alias / raw-SQL / dialect decisions of its own — the one `using`
grep hit is the prose word "reusing"), so a resolver-path
finding here would run its Proof in all three cells, not claim
`inapplicable by construction`. No cell failed to run.

Fingerprints (`git hash-object`):

| File | Blob |
|---|---|
| `django_strawberry_framework/auth/__init__.py` | `2e480818` |
| `django_strawberry_framework/auth/mutations.py` | `98ae63f1` |
| `django_strawberry_framework/auth/queries.py` | `b036bdac` |
| `django_strawberry_framework/auth/sessions.py` | `e50011e6` |
| `django_strawberry_framework/types/finalizer.py` | `b9d8acb2` |
| `django_strawberry_framework/registry.py` | `27358cbc` |
| `django_strawberry_framework/mutations/sets.py` | `21c15c0b` |
| `django_strawberry_framework/mutations/inputs.py` | `840da733` |
| `django_strawberry_framework/mutations/fields.py` | `0e4d5ed1` |
| `django_strawberry_framework/utils/sessions.py` | `21041723` |
| `django_strawberry_framework/utils/permissions.py` | `1c9cfd39` |
| `django_strawberry_framework/__init__.py` | `0ef72601` |
| `docs/README.md` | `30978c34` |
| `docs/GLOSSARY.md` | `3413edc3` |
| `tests/auth/test_mutations.py` | `4cb49982` |
| `tests/auth/test_queries.py` | `a57722d4` |
| `tests/auth/test_sessions.py` | `b71c84ec` |
| `examples/fakeshop/test_query/test_auth_api.py` | `17fc9ddb` |
| `examples/fakeshop/apps/accounts/schema.py` | `dd2e81b3` |
| `docs/review/review-0_0_15.md` | `3f5d15c2` |
| `docs/review/rev-auth.md` | `0dd3f19b` |

All owner/oracle blobs match the closed file-item records — no
concurrent drift entered through any file the verdicts rest on.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

Discharge map (looks-for entry -> verdict): 1 none, 2 none, 3
none, 4 none, 5 none, 6 none, 7 none, 8 none, 9 none, 10
rejections R1-R2 (+ filed file-item verdicts adopted, not
re-filed), 11 none, 12 rejection R3 (+ filed file-item verdicts
adopted).

#### [1: rule at caller] none — shared machinery has one in-folder owner, ridden by call

`auth/queries.py` takes five privates from `auth/mutations.py`
(the family label, the anonymity definition, the fixed-surface
declaration path, the field builder, the bridged async body);
the bind order (pre-bind reset -> `bind_auth_mutations()` ->
`bind_mutations()`) lives in `types/finalizer.py`, the owner of
bind order, with the opt-in lookup owned by
`utils/imports.py::loaded_attr`. No caller re-spells an owner's
rule. On the placement question the mutations item homed here
(whether the query-shared helpers belong in `mutations.py`):
they are auth-family machinery with exactly two in-folder
consumers and one documented direction — extracting a third
module would split one family's declaration mechanics across
two owners for zero behavioral change. Trigger: a non-auth
consumer needs the machinery — extract it to the shared owner
then.

#### [2: policy/mechanism layering] none — the folder split is policy over mechanism

`auth/sessions.py` answers transport facts (classification,
capability, lock, missing-session pre-check); the
`auth/mutations.py` state machines carry the auth policy (gates,
envelopes, compensation). The capability predicates
(`login_supported` / `logout_supported`) sit with the
classification they derive from, and the state machines gate on
them by call. No policy in the boundary, no mechanism in the
policy layer.

#### [3: contract sources differ] none — the folder's own claims agree with its body

`auth/__init__.py` promises four field factories and names them
in `__all__`, the import example, and the re-export lines —
all three agree. The structural opt-in holds: the package root
carries zero `auth` references, the finalizer reaches the bind
only through already-loaded-only `loaded_attr`, and every
README/GLOSSARY row the file items checked (surface, transport
matrix, envelope, masking, bind order) stands — all contract
blobs byte-stable since those passes.

#### [4: unreachable branch] none — every folder-level branch has a pinned real path

The bind's empty-ledger no-op (every auth-free schema build),
the finalizer's `bind_auth is None` skip (opt-in boundary),
the surface-keyed per-arm binds (partial schemas incl. the
logout-only bind with no user type registered), and both clear
rows (pre-bind reset drains the alias + emit ledgers only;
`clear()` drains all three rows — verified in `registry.py`:
`clear()` iterates `iter_subsystem_clears()` unfiltered while
the finalizer selects `before_bind=True`). Per-module arms were
pinned by their file items.

#### [5: mode flag] none — keys and a named enum, no behavior flag

`Transport` is the classifier output with per-mode native paths
in the state machines; the surface keys (`"login"` / `"logout"`
/ `"register"` / `"current_user"`) are ledger keys, gate
operation names, and bind keys — dispatch-by-key, never a
behavior switch inside one body.

#### [6: state in two places] none — one ledger, one alias namespace, natives own the rest

Declarations single-site in the auth ledger (also the
same-args cache + conflict state — draining drains all three);
the alias namespace single-sites in the queries trio;
holder bind outputs (`_primary_type`, `_payload_type_name`)
are written once at bind; session/user/backend/CSRF stay with
the Django/Channels natives; the engine expression
single-sites outside the folder in `utils/sessions.py` for the
documented opt-in reason. The rider's dual-ledger membership
references one class object for two binds' distinct concerns,
both full-clear-only, so the memberships cannot diverge. The
`_SURFACE_FACTORY_NAMES` values are pinned message data
naming the consumer's factory, not state — the bind holds no
factory refs to derive them from.

#### [7: dependency direction] none — downward edges plus the blessed folder-internal pair

`auth` imports `mutations/*`, `utils/*`, `registry`,
`exceptions` (downward; verified at this tree that
`mutations/*` and `utils/*` import nothing from `auth` — the
only two hits are prose citations). `queries.py` ->
`.mutations` at top level is load-bearing in that direction
(it guarantees the bind is loaded whenever `current_user` is
declared, which the finalizer's already-loaded-only lookup
requires); the back edge (`bind_auth_mutations` ->
`.queries`) is function-local with the cycle documented at the
site, and can only run when `queries` is already loaded (the
arm requires a declared `current_user` surface). No
`TYPE_CHECKING` imports in the folder. External `auth.*`
hits are `channels.auth` (upstream) or prose; the one real
external edge is the finalizer's `loaded_attr` string.
Trigger: an `auth` import appearing in `mutations/*` or
`utils/*` would make the lazy imports load-bearing.

#### [8: settings at import] none — all reads are call-time

No `django.conf.settings` import in the folder (the one grep
hit is a docstring mention). `get_user_model()` runs at
factory call and at bind; the `SESSION_ENGINE` read sits at
request time inside the capability predicate. Import side
effects are the trio construction plus the two standard
`register_subsystem_clear` rows.

#### [9: `__all__` disagreement] none — the folder exports exactly its consumer surface

`auth.__all__` names the four factories and nothing else; the
siblings deliberately carry no `__all__` (the only hits are
envelope prose and a docstring citation of `auth.__all__`
itself). The unexported publics are module-internal seams
reached by dotted path (`derive_register_fields`, the ledger
trio, the alias trio + constant), by `loaded_attr`
(`bind_auth_mutations`), or not at all from production
(`sessions`, deliberately unexported — the channels-free
import is pinned). No star import from `auth` exists in
package, tests, or the accounts app.

#### R1 [10: duplication] rejected — surface-name spellings serve two contracts, one owner holds the rule

Census: 18 double-quoted surface spellings across the folder
(16 in `mutations.py`, 2 in `queries.py`). They occupy two
contracts: ledger/bind identity (dict keys, declaration keys,
bind lookups, the rider class attr) and gate-operation wording
(the three `authorize_or_raise` operation strings, which feed
the pinned user-visible denials, e.g. `"Not authorized to
current_user UserT."`). A folder-level constant would couple
denial prose to ledger identity — renaming a ledger key must
not silently reword a denial. The identity rule is authored in
`auth/mutations.py`; `queries.py` holds two consumer
spellings of the owner-held name (the queries item's R6, same
verdict, not re-filed). Change challenge (rename a surface):
count 1 per contract. Trigger: the owner single-sites the
operation string — consumers adopt it.

#### R2 [10: duplication] rejected — the rider's async twin follows the framework seam, not the auth seam

`_synthesize_register_rider.resolve_async` wraps
`_run_register_pipeline_sync` in `run_in_one_sync_boundary`
directly instead of via `_sync_bridged_async_body`. Not a
fork: the rider is a `DjangoMutation` following the framework's
`resolve_sync` / `resolve_async` seam, while the bridge helper
serves the fixed-field dispatch seam — different seams,
different owners, and both twins wrap the same sync body, so
drift is impossible by construction. Trigger: the framework
seam changes shape — the rider follows it, not the auth helper.

Adopted without re-filing: the sealed-snapshot mirror, bind-arm
legs, establish/teardown twins, and prologue residue (mutations
R10-R14, incl. the F1 consolidation now landed); the
`require_channels` / install-hint twin with `routers.py`
(sessions R2, hint-ownership rule owned by `utils/imports.py`);
the `_is_request` accepted-set overlap (sessions R3).

#### [11: twin drift] none — one bridge discipline across the family

Login/logout resolve twins, the register twin, and the bridged
`current_user` body all route async work through the one
`run_in_one_sync_boundary` discipline; the three fixed fields
share `_sync_bridged_async_body`, and the rider twin wraps its
own identical sync body (R2). Deltas are per-transport and
documented at the file items (mutations R15; queries entry 11).

#### R3 [12: guard asymmetry] rejected — register has no transport gate because it mutates no session

Login/logout classify the transport, probe the session stack,
and check capabilities; register (like `current_user`) runs
none of that. Correct by contract: the register path
(decode + write steps, `mutations.py` lines 998-1120) carries
zero session references — it creates a user row, never
touches `request.session` — and transport gates guard session
mutation. The README matrix covers login/logout only. Trigger:
a session-mutating step added to the register path.

Adopted without re-filing: gate-shape differences by surface
necessity (mutations R16, queries R4), the Channels-only actor
lease (mutations R17), timestamp fields (mutations R18), hook
`Meta` misuse failing loud (mutations R19), the read path's
missing prologue/middleware probe (queries R3, R5), the bound
`.get` + sync-bridge caveats (sessions R1, R4-R6).

## Cross-axis (for Comments)

Routed lead (plan, from auth/queries.py Comments):
`tests/auth/test_mutations.py::_request_with_store` opens
descriptively ("A Django request wired to an explicit session
store, anonymous actor."), in the mood of that item's filed L1.
Read and judged out of this axis's scope: it is pure test-prose
mood with no placement, contract, or dependency content. The
plan already homes it on this item's Comments pass — nothing
for Mechanics to add, no finding taken.

## Handoff

Beyond the record I read the nine closed file-item axis files
with every Handoff and verify section, the finalizer phase-2.5
slot whole, the registry clear/select semantics, and every
owner body named in the trace. Conclusions not in the findings:
(1) the folder's lifecycle is coherent end to end —
declaration ledgers survive the pre-bind reset while emit
ledgers drain, the bind re-materializes surface-keyed, and
full `clear()` drains all three rows; (2) the two clear-row
owners (`auth.declarations`, `auth.current_user_alias`) plus
the ridden `mutations.input_namespace` row are the complete
folder lifecycle — no fourth state site exists; (3) the
mutations item's open placement question (five privates shared
from `mutations.py`) is judged here under entry 1: keep, with
a named trigger; (4) the `bind_auth_mutations` direct
`declaration._auth_surface` read vs `_declared_auth_surface`'s
`getattr` default is deliberate strictness at the bind (every
ledger member carries the attr) vs tolerance at lookup — not
a discrepancy. Open threads: none. No verification owed (no
findings, no Proofs). Cells: no finding reaches a cell; the
DB-reach note under Trace stands for the verifier to judge.

## Verify mechanics

Pass 1, fully static (no copy bound, no workspace run — none
owed on a zero-path implement pass).

Zero-change check: `git diff ITEM_BASELINE --`
over `django_strawberry_framework/auth/` + `tests/auth/` is
empty (0 bytes), ITEM_BASELINE
5676d4fc6310a5ff0d075771593a0f3068eb9406. Live
fingerprints equal the review's: init
2e480818424d4b130e613e3e2da027aaad7144ad (matches the
plan's baseline), mutations
98ae63f1965a08d28332ae6e24aa24ea39d9d511, queries
b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9, sessions
e50011e6cae837a7b1322d704a7f8adbb69bcec3,
tests/auth/__init__.py
09e0f06d9c93719e6e75dbcd54e8c03255c655b0 (F1 deferred,
untouched). Nothing attributable to this item; the
`auth/mutations.py` + `auth/sessions.py` dirty-vs-HEAD hunks
are the two verified file items' own ledger rows, as the
review already states. The plan's `## Owned changes` holds
no row for this item. No Mechanics defect could have been
introduced: no executable line moved.

No-findings stands: the Implement pass took zero paths
(Performance + Mechanics recorded no-findings; Comments F1
Low deferred per the ride rule). No Proof lines to run (the
record carries none); no symbol moved or renamed, so no
`--cited-by` sweep is owed; the whole-diff reading is an
empty diff, so there is nothing to attack and no failability
manifest is owed. Rejections stand, re-derived: R1 census
reproduces exactly (16 double-quoted surface spellings in
`mutations.py`, 2 in `queries.py`, same two-contract split,
no constant introduced); R2 rider still wraps
`_run_register_pipeline_sync` directly in
`run_in_one_sync_boundary` at the framework seam
(`mutations.py:1216`); R3 register path (`mutations.py`
lines 998-1120) still carries 0 session references. Every
trigger still false: no non-auth consumer of the shared
machinery (sole outside hit is a prose citation), no
framework-seam shape change, no session-mutating register
step. All owner/oracle fingerprints reproduce
(finalizer b9d8acb2, registry 27358cbc, mutations sets
21c15c0b / inputs 840da733 / fields 0e4d5ed1,
utils/sessions 21041723, utils/permissions 1c9cfd39,
package `__init__` 0ef72601, README 30978c34, GLOSSARY
3413edc3, test_mutations 4cb49982, test_queries a57722d4,
test_sessions b71c84ec, live test_auth_api 17fc9ddb,
accounts schema dd2e81b3), so no concurrent drift entered
through any file the verdicts rest on. Sibling check:
Performance carries only `## Cross-axis` with none (no
Mechanics finding to judge), Comments carries no Cross-axis
section and its F1 is a deferred test-docstring census with
no placement/contract/dependency content. Record citations
resolve (`check_citations.py --paths` on this record: 3/3
OK). Cells: no finding reaches a cell; the DB-reach note is
judged standing (a resolver-path finding here would run all
three cells, not claim inapplicable). None unverified. No
new defects.

Scratch: `docs/review/temp-tests/auth-integration/verify-mechanics-1/`
(`item-diff.diff`, `fingerprints.txt`, `r1-census.txt`,
`r2-twins.txt`, `r3-session-refs.txt`, `citations.txt`).

Handoff: Mechanics verification closes with no-findings
standing on a byte-identical tree. Nothing here depends on
the Performance or Comments verifiers' verdicts beyond the
sibling cross-axis check above, which is satisfied. Open
threads: none.

Status: verified. Open threads: none.
