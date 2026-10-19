# Review · Mechanics: `django_strawberry_framework/auth/queries.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=f26a7dff116cf2968524bab663453025006e185b

## Trace

Required reading, in order: AGENTS.md, START.md,
REVIEW.md, worker-1.md, the plan
(`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3,
incl. its `## Owned changes`, which holds no row for this
target and no Routed lead on this item),
`docs/review/rev-auth__queries.md` (skeleton: `Status:
reviewing`, blank Path class). Sibling axis records
`rev-auth__queries.performance.md` and
`rev-auth__queries.comments.md` did not exist at close
(siblings run concurrently); no foreign Handoff or
`## Cross-axis (for Mechanics)` owed. The main artifact
carries no Worker-2 sections yet.

Target read whole, all 121 lines, as it stands: blob
`b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9`. `git diff
ITEM_BASELINE --` the target is empty: the live tree equals
the item baseline, so the fingerprints below are the
baseline's.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/auth-queries/mechanics/inspect/`
(json
`docs/review/temp-tests/auth-queries/mechanics/queries.json`):
2 symbols, 1 hot entry point (+0 reachable), 2 import-time
work items (the trio call, the clear row), 0 TODOs. Leads
only.

Contracts traced by hand: `docs/README.md` (session-auth
surface, transport matrix, production error policy incl.
the structural masking table), `docs/GLOSSARY.md` (the
`auth-mutations` anchor whole, the factory index row, the
`request_from_info` anchor), the owner docstrings of every
reused seam, and the oracles:
`tests/auth/test_queries.py` (whole, 407 lines),
`tests/auth/test_mutations.py` (grepped for the shared
seams), `tests/auth/test_sessions.py` (grepped),
`tests/auth/_helpers.py`, `tests/auth/conftest.py`,
`examples/fakeshop/test_query/test_auth_api.py` (the `me`
pins: SDL shape, happy path, anonymous `null`,
no-`AuthenticationMiddleware` `null`, visibility skip,
relay id, reload preservation, strictness visibility) and
the consumer wiring
`examples/fakeshop/apps/accounts/schema.py`. Inbound edges:
`auth/__init__.py` (`current_user` re-export),
`auth/mutations.py::bind_auth_mutations` (function-local
import of `CURRENT_USER_ALIAS_NAME` +
`materialize_current_user_alias`), tests (the trio +
constant imports). Outbound edges verified at their
owners: `auth/mutations.py` (the family label, the actor
classifier, the fixed-surface declaration path, the field
builder, the bridged async body, the surface-keyed bind),
`mutations/fields.py` (lazy refs, signature builder),
`mutations/resolvers.py::authorize_or_raise`,
`mutations/sets.py::check_permission`,
`mutations/permissions.py`, `registry.py` (subsystem
clears, full `clear()`), `types/finalizer.py` (the
phase-2.5 pre-bind reset + `bind_auth_mutations()` slot
via `loaded_attr`), `utils/inputs.py::make_input_namespace`
(+ the parked-global paragraph),
`utils/permissions.py::request_from_info`, and the package
root (no auth import: the structural opt-in holds).
Background (not a contract source):
`docs/SPECS/spec-040-auth_mutations-0_0_13.md` Decisions
7/8/9/10/11; the verified sibling-item records
`rev-auth__mutations.performance.md` and
`rev-auth__mutations.mechanics.md` incl. their Handoffs.

Cells: no finding, so no Proof reaches a cell. Had one
existed, `sharded` and `pg` would be `inapplicable by
construction`: the target passes no `using`, reads no
alias, holds no raw SQL and no dialect branch — the
resolver issues no queryset work by contract
(actor-not-lookup) and the only ORM touch is forcing the
middleware's own lazy user on the request's own alias. No
workspace run was needed (every candidate resolved
against owner bodies + pinned oracles) and no cell failed
to run.

Fingerprints (`git hash-object`):

| File | Blob |
|---|---|
| `django_strawberry_framework/auth/queries.py` | `b036bdac` |
| `django_strawberry_framework/auth/mutations.py` | `98ae63f1` |
| `django_strawberry_framework/auth/sessions.py` | `865d6e70` |
| `django_strawberry_framework/auth/__init__.py` | `2e480818` |
| `django_strawberry_framework/mutations/sets.py` | `21c15c0b` |
| `django_strawberry_framework/mutations/resolvers.py` | `c9cff059` |
| `django_strawberry_framework/mutations/inputs.py` | `840da733` |
| `django_strawberry_framework/mutations/fields.py` | `0e4d5ed1` |
| `django_strawberry_framework/mutations/permissions.py` | `55e5edf8` |
| `django_strawberry_framework/registry.py` | `27358cbc` |
| `django_strawberry_framework/types/finalizer.py` | `b9d8acb2` |
| `django_strawberry_framework/utils/permissions.py` | `1c9cfd39` |
| `django_strawberry_framework/utils/querysets.py` | `8fc556d5` |
| `django_strawberry_framework/utils/directives.py` | `84f770d4` |
| `django_strawberry_framework/utils/execution_mode.py` | `9805cdaf` |
| `django_strawberry_framework/utils/inputs.py` | `b5af8255` |
| `docs/README.md` | `30978c34` |
| `docs/GLOSSARY.md` | `3413edc3` |
| `tests/auth/test_mutations.py` | `4cb49982` |
| `tests/auth/test_queries.py` | `86fa35e3` |
| `tests/auth/test_sessions.py` | `b71c84ec` |
| `tests/auth/_helpers.py` | `996762b0` |
| `tests/auth/conftest.py` | `a5c413ba` |
| `tests/auth/__init__.py` | `09e0f06d` |
| `examples/fakeshop/test_query/test_auth_api.py` | `17fc9ddb` |
| `examples/fakeshop/apps/accounts/schema.py` | `dd2e81b3` |
| `docs/review/review-0_0_15.md` | `6e025258` |
| `docs/review/rev-auth__queries.md` | `8d754393` |

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

Discharge map (looks-for entry -> verdict): 1 none (R6
records the one consumer-spelling pair as entry-10
business), 2 none, 3 none + one frozen-spec observation
(R1), 4 none, 5 none, 6 none + the literal-vs-`__name__`
convention (R2), 7 none, 8 none, 9 none, 10 rejections
R6-R7, 11 none, 12 rejections R3-R5.

#### R1 [3: contract sources differ] none — body matches all four sources; the archived spec paragraph is frozen history

README (session-auth surface, transport matrix, masking
table), the GLOSSARY `auth-mutations` anchor, the owner
docstrings and the oracles agree with the body on every
checked row: `me = current_user()` with the AllowAny
default and a `permission_classes=` seam; the gate-first
`authorize_or_raise(holder, info, "current_user", None,
instance=actor)` with the pinned `"Not authorized to
current_user UserT."` denial (a framework `GraphQLError`,
unchanged on the wire per the masking table);
allowed-but-anonymous -> `null`, never an error; no
`get_queryset` re-run and no re-fetch (actor-not-lookup,
pinned live against a hide-everyone `get_queryset`); the
`me: UserType` SDL via the bind-materialized
`CurrentUserAlias` lazy ref; the pre-bind alias-ledger
row beside the full-clear-only declaration ledger; a
raising consumer `is_authenticated` propagating to the
policy mask (`"An unexpected error occurred."`, pinned).
The one differing text is NOT a contract source:
spec-040 Decision 7's hostile-collapse paragraph
(hostile actor shapes collapse to `null`) describes a
behavior the shipped `_authenticated_actor_or_none`
(propagate, never classify) and its oracles superseded;
the owning symbol lives in `auth/mutations.py`, verified
this run. Trigger: a contract source (README, GLOSSARY,
owner docstring, oracle) is amended to demand behavior
the body lacks — the owner changes and this surface
follows by call.

#### R2 [6: state in two places] none — the module-path literal is the shared namespace convention, not a second copy

`AUTH_QUERIES_MODULE_PATH` spells the module's own import
path where `__name__` would auto-track a rename. It is
one definition (not state held twice: nothing else owns
the path as state), shared by the trio call and the
`_lazy_ref`, imported — never re-spelled — by the bind,
and it matches the pinned-literal convention of every
sibling namespace (`INPUTS_MODULE_PATH` and the per-flavor
paths). A `__name__` swap here alone would diverge this
namespace from all of them. Trigger: the owner convention
moves to `__name__` — this namespace adopts it.

#### R3 [12: guard asymmetry] rejected — no transport/session prologue on the read path is the contract

Login/logout classify the transport, probe the session
stack and check capabilities; `current_user` runs none of
that and is transport-neutral by construction (spec-040
D11; GLOSSARY: `current_user` works over the router via
`request_from_info`; the README transport matrix covers
login/logout only). The shape guard IS present and
shared: an unrecognized context raises `ConfigurationError`
from `request_from_info` before the gate. A session probe
would be dead policy — the resolver never touches
`request.session`. Trigger: a contract is amended to
require session presence for reads.

#### R4 [12: guard asymmetry] rejected — `instance=actor` vs logout's `instance=None` is surface necessity

`current_user` passes the forced actor (object gates need
it; the read necessarily precedes the gate),
login passes `data={"username"}` (no actor exists
pre-`authenticate`; the password deliberately excluded),
logout passes `instance=None` (model-less). The
write-pipeline authorize-before-mutation invariant holds
for every write; this read gates before returning. No
contract source demands uniform gate shapes (sibling
item's R16, same verdict). Trigger: README/GLOSSARY is
amended to promise object-level gates an instance on
logout.

#### R5 [12: guard asymmetry] rejected — no AuthenticationMiddleware probe is the nullable contract

A request with no `user` attribute at all resolves to
`null` rather than raising (GLOSSARY: anonymous is an
expected state, never an error; spec-040 Decision 7;
pinned live). Probing for the middleware would invert the
contract. Trigger: the nullable contract is amended to
fail loud without the middleware.

#### R6 [10: duplication] rejected — the dual `"current_user"` spelling is two consumer positions of an owner-held name

`_declare_fixed_auth_surface("current_user", ...)` (ledger
key + holder snapshot operation) and
`authorize_or_raise(..., "current_user", ...)` (gate
operation + denial wording) spell the surface name twice,
in exactly the positions login/logout occupy. The rule
"the fourth surface is named `current_user`" is authored
in `auth/mutations.py` (`_SURFACE_FACTORY_NAMES`, the
bind's surface tuple, the holder synthesis); this module
holds zero authoritative definitions, two consumer
spellings. A local constant would not consolidate the
rule — it would hide one consumer while the owner still
spells it. Change challenge (rename the surface): the
count is owned in `auth/mutations.py` (verified/closed
this run). Trigger: the owner single-sites the operation
string — this module adopts it.

#### R7 [10: duplication] rejected — every other sharing candidate already rides its owner by call

Change challenges, each count 1: rename `CurrentUserAlias`
-> the constant (the bind imports it); change the
anonymity definition -> `_authenticated_actor_or_none`
(logout + `current_user` follow by call); change the
denial shape -> `authorize_or_raise`; change the
forward-ref shape -> `_lazy_ref`; change the namespace
lifecycle -> `make_input_namespace` + the parked-global
paragraph; change the dispatch seam -> `_make_auth_field`
(the `| None` nullability is this surface's own contract,
not a copy of the payload refs). The holder snapshot
`operation` has no package reader (every `meta.operation`
read is a model/form/serializer meta) — carried data in
the owner-verified shape, not a fork. No trigger
(structural: reuse by call).

#### [1: rule at caller] none

Anonymity, gate iteration + denial mapping, request
resolution, declaration/conflict, field dispatch +
signature injection, the forward ref and the namespace
lifecycle all ride their owners by call (R7). No caller
re-spells an owner's rule.

#### [2: policy/mechanism layering] none

Gate-first-then-nullable, actor-not-lookup, the AllowAny
default via the standard validator and the
one-declaration rule are auth-flavor policy implemented
in the flavor's own resolver/factory; every mechanism
underneath is ridden by call. No policy in an adapter
(the module has no transport branch) and no mechanism in
a policy layer.

#### [4: unreachable branch] none — the module is branchless

No `if`, loop or `try` in 121 lines (the inspect overview
confirms 0 control-flow hotspots). Every line executes
under a pinned path: import runs the trio + the clear
row; declaration runs the factory; a request runs the
resolver; finalize runs the bind's alias arm. The 100%
gate corroborates execution.

#### [5: mode flag] none — keys and domain names, no behavior switch

`"current_user"` / `"CurrentUser"` are a ledger key, a
gate operation name and a holder label (cf. sibling R5),
never a behavior switch inside one body. No flag exists.

#### [7: dependency direction] none — downward edges plus the blessed folder-internal pair

`mutations.fields`, `registry`, `utils.inputs` and
`utils.permissions` are downward (flavor on foundation).
`queries.py` -> `.mutations` at top level is
folder-internal, and it is load-bearing in that
direction: it guarantees `bind_auth_mutations` is loaded
whenever `current_user` is declared, which the
finalizer's already-loaded-only `loaded_attr` lookup
requires. The function-local `from ..mutations import
resolvers` matches `_logout_prologue`'s idiom; re-verified
at this tree that `mutations/*` and `utils/*` import
nothing from `auth` (two name-only hits:
`auth_aliases_for_permission_classes`,
`_require_sync_bool_auth_result`), so it hides no cycle.
No `TYPE_CHECKING` imports. Trigger: an `auth` import
appearing in `mutations/*` or `utils/*` would make the
lazy `resolvers` import load-bearing.

#### [8: settings at import] none

No `django.conf.settings` import. `get_user_model()`
runs at bind (in `auth/mutations.py`), never at this
module's import; the import's only side effects are the
trio construction and the standard `register_subsystem_clear`
row.

#### [9: `__all__` disagreement] none — no `__all__` here, deliberate curation above

The target carries no `__all__`. The folder `__init__`
deliberately exports only the four consumer factories
(the structural opt-in). The unexported publics are
module-internal seams reached by dotted path: the bind
imports `CURRENT_USER_ALIAS_NAME` +
`materialize_current_user_alias` (function-local; the
only production importer), the registry holds
`clear_current_user_alias_namespace`, tests read the
ledger + clear — the same posture the sibling item's R9
blessed for `auth/mutations.py`.

#### [11: twin drift] none — one body plus the shared bridge, no twin to drift

`current_user` has no native async body: the whole
gate-then-return body runs inside the one
`run_in_one_sync_boundary` worker via
`_sync_bridged_async_body`, which is complete (not
interim debt) for this transport-neutral surface — there
is no per-transport specialization to twin. The bridge
preserves the semantics: the forced lazy-user load and
the gate both run in-boundary (pinned async: exactly one
boundary entry, the recorded gate `instance` is the real
user row, no `SynchronousOnlyOperation`), and the
`SyncMisuseError` discipline is unchanged (an `async def
has_permission` is still rejected in the sync worker).
Login/logout route their Django-HTTP async arms through
the same worker around their sync bodies — one discipline
across the family.

Handoff: Beyond the record I read spec-040 Decisions
7/8/9/10/11 whole (background only; grounding stays in
README/GLOSSARY/owner docstrings/oracles), the verified
sibling-item records `rev-auth__mutations.performance.md`
and `rev-auth__mutations.mechanics.md` with their
Handoffs, the finalizer's pre-bind reset + phase-2.5 slot,
and the registry clear semantics (a `before_bind` row
runs both pre-bind and under full `clear()`). Conclusions
not in the findings: (1) the top-level `.mutations`
import must stay top-level — laziness there would
silently drop the bind under the finalizer's
already-loaded-only lookup; (2) the archived spec-040 D7
hostile-collapse paragraph is stale against the shipped
propagate-and-mask behavior (owner verified this run);
(3) the GLOSSARY/`request_from_info` illustrative family
parenthetical omits `AuthMutation` though the anchor
sentence covers `current_user` — a prose nit for the
owning passes, not a discrepancy. Open threads: none. No
verification owed (no findings, no Proofs). Cells: no
finding reaches a cell; `sharded`/`pg` inapplicable by
construction as stated for the verifier to judge.

## Verify mechanics

No-findings-stands confirmation. The target is byte-identical to
ITEM_BASELINE: `git hash-object
django_strawberry_framework/auth/queries.py` =
`b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9` (the record's
fingerprint), `git diff ITEM_BASELINE --` the target is 0 bytes,
and `--code-digest` exits 0 with equal digests
(`sha256:27c0662b...` both sides). No production code changed, so
no Mechanics defect could have been introduced. All 12
owner/contract/oracle fingerprints re-read from the live tree
match the record's Trace table exactly (`auth/mutations.py`
98ae63f1, `auth/sessions.py` 865d6e70, `auth/__init__.py`
2e480818, `mutations/sets.py` 21c15c0b, `mutations/resolvers.py`
c9cff059, `mutations/fields.py` 0e4d5ed1, README 30978c34,
GLOSSARY 3413edc3, `test_mutations.py` 4cb49982,
`test_sessions.py` b71c84ec, `conftest.py` a5c413ba,
`test_auth_api.py` 17fc9ddb).

F2 rename: the only code delta in the item is the single test
rename `test_async_me_dispatch_awaits_the_native_async_body_exactly_once`
-> `test_async_me_dispatch_awaits_the_bridged_async_body_exactly_once`.
Symbol census 39/39 with exactly that one name delta;
docstring-stripped AST of the renamed body is identical across
the rename (kind + args + decorators included); all other 24
functions and all module-level statements identical. Old name has
zero live references (only frozen per-cycle prose still cites it;
the `test_mutations.py` native-body twins are the login/logout
tests where "native" is correct). No production symbol moved.

Rejections R1-R7 stand: every trigger needs a contract amendment,
an owner-convention move, or an owner single-siting, and the
target, all owners, and both contract sources are byte-stable, so
none fired. Spot-confirmed live: R2 literal single-sited
(definition line 38, consumed by name at lines 53/117, no
re-spelling in the package); R6 dual `"current_user"` spelling
intact (lines 88/111); R7 bind still imports
`CURRENT_USER_ALIAS_NAME` + `materialize_current_user_alias`
(`auth/mutations.py:1340-1342`); entry-4 branchless (0
if/for/while/try lines). Handoff (1) (top-level `.mutations`
import must stay) holds by byte-identity; Handoff (2) is frozen
spec archive; Handoff (3) stays folder/project business.

TREE.md render: exactly 2 rows (4 +/- lines in the TREE.md diff),
both the `tests/auth/test_queries.py` row at lines 514/765, text
equal to the live module first line; `--list-docstrings` green.
The pass is prose-only outside the one test rename; the
Performance Handoff's conditional probe re-run is not owed (no
resolver body touched).

Disturbance check. Live item diff
(`git diff ITEM_BASELINE -- tests/auth/test_queries.py
docs/TREE.md`, 4921 bytes) is byte-identical to
`docs/review/temp-tests/auth-queries/diff/pass-1.diff`
(DIFF-MATCH). Item scope holds exactly 2 files, no new files; the
target is clean in `git status`. Whole-diff reading on this axis:
the four test hunks are the Comments F1/L2/L1/F2 prose + rename
only; nothing in them moves a rule, a guard, or a dependency.
Lint gates green: `ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` on the touched paths (0
violations), `check_citations.py --check` on the tree (1302
resolve). Fully static; no workspace copy bound. Scratch:
`docs/review/temp-tests/auth-queries/verify-mechanics-1/`
(`live-item-diff.diff`, `baseline-test_queries.py`,
`live-test_queries.py`). New defects: none. Open threads: none.

Status: verified
