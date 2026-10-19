# Review · Mechanics: `django_strawberry_framework/auth/mutations.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8a53fa0958877d9c10e62631deb5b38e2096d539

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for
this target and no Routed lead on this item),
`docs/review/rev-auth__mutations.md` (skeleton: `Status: reviewing`,
blank Path class). Sibling axis records
`rev-auth__mutations.performance.md` and
`rev-auth__mutations.comments.md` did not exist at close (siblings run
concurrently); no foreign Handoff or
`## Cross-axis (for Mechanics)` owed. The main artifact carries no
Worker-2 sections yet.

Target read whole, all 1367 lines, as it stands: blob
`84183c893fdbf258e112ccf6d1cc66f6bc50c513`. Dirty vs HEAD
(`+84/-113`, concurrent work — truth migration, the
`_authenticated_actor_or_none` simplification, compensation-clause
narrowing, `field_name_map` threading) — reviewed as it stands per
the dispatch, no hunk attributed here. `git diff ITEM_BASELINE --`
the target is empty: the live tree equals the item baseline, so the
fingerprints below are the baseline's.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/auth-mutations/mechanics/inspect/` (json
`docs/review/temp-tests/auth-mutations/mechanics/mutations.json`):
47 symbols, 14 hot entry points (+8 reachable), 2 import-time work
items, 0 TODOs. Leads only.

Contracts traced by hand: `docs/README.md` (auth surface,
transport matrix, production error policy incl. the structural
masking table, mutation envelope, security profile incl. the worked
login-throttle gate), `docs/GLOSSARY.md` (the `auth-mutations`
anchor whole, the factory index row, the `request_from_info`
anchor), `GOAL.md` "Trust boundary", the owner docstrings of every
reused seam, and the oracles: `tests/auth/test_mutations.py` (2689
lines, incl. the seal tests, the sync-bridge tests and the
derive tests), `tests/auth/test_queries.py`,
`tests/auth/test_sessions.py`, `tests/auth/_helpers.py`,
`tests/auth/conftest.py` (grepped; pins cited below),
`examples/fakeshop/test_query/test_auth_api.py` (module docstring +
enumeration-guard pins) and the consumer wiring
`examples/fakeshop/apps/accounts/schema.py`. Inbound edges:
`auth/__init__.py` (the 4 factories), `auth/queries.py` (5 private
imports: the family label, the actor classifier, the fixed-surface
declaration path, the field builder, the bridged async body),
`types/finalizer.py` (the phase-2.5 `bind_auth_mutations()` slot via
`loaded_attr`). Outbound edges verified at their owners:
`mutations/sets.py` (ledger factory, permission validation,
`DjangoMutation.check_permission`, the `build_input` /
`input_type_name` seams, `bind_mutation_outputs`,
`bind_write_declarations`), `mutations/resolvers.py` (pipeline
skeleton, decode/write steps incl. the EXCLUDED 4-tuple, wire-name
map, `authorize_or_raise`, `payload_cls_for`, `build_payload`,
`field_error` re-export), `mutations/inputs.py` (payload builder,
slot rule, emit ledger + pre-bind clear, narrowing validation),
`mutations/fields.py` (lazy refs, signature builder,
`DjangoMutationField` incl. create-passes-`UNSET`),
`mutations/permissions.py` (`run_permission_classes`),
`registry.py` (subsystem clears, `get` / `types_for`),
`utils/permissions.py`, `utils/querysets.py`, `utils/write_values.py`,
`utils/directives.py`, `utils/execution_mode.py`,
`utils/errors.py`, `utils/inputs.py`, `utils/sessions.py`,
`auth/sessions.py` (whole), `consumers.py` (checkpoint scope only),
and the package root (no auth import: the structural opt-in holds).

Cells: the `default` cell ran the probe and the seal nodes below.
`sharded` and `pg` are inapplicable by construction for F1: the
finding changes holder-class construction only (no database, alias
or dialect decision), and its Proof is a static gate plus two
database-free class-mechanics tests. No cell failed to run.

Fingerprints (`git hash-object`, short + full in the report):

| File | Blob |
|---|---|
| `django_strawberry_framework/auth/mutations.py` | `84183c89` |
| `django_strawberry_framework/auth/queries.py` | `b036bdac` |
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
| `django_strawberry_framework/utils/write_values.py` | `13548c76` |
| `django_strawberry_framework/utils/directives.py` | `84f770d4` |
| `django_strawberry_framework/utils/execution_mode.py` | `9805cdaf` |
| `django_strawberry_framework/utils/errors.py` | `6a389474` |
| `django_strawberry_framework/utils/inputs.py` | `b5af8255` |
| `django_strawberry_framework/utils/sessions.py` | `21041723` |
| `django_strawberry_framework/consumers.py` | `0791c04a` |
| `django_strawberry_framework/__init__.py` | `0ef72601` |
| `docs/README.md` | `30978c34` |
| `docs/GLOSSARY.md` | `3413edc3` |
| `tests/auth/test_mutations.py` | `ff8a261d` |
| `tests/auth/test_queries.py` | `86fa35e3` |
| `tests/auth/test_sessions.py` | `b71c84ec` |
| `tests/auth/_helpers.py` | `996762b0` |
| `tests/auth/conftest.py` | `a7e8a55e` |
| `tests/auth/__init__.py` | `09e0f06d` |
| `examples/fakeshop/test_query/test_auth_api.py` | `17fc9ddb` |
| `examples/fakeshop/apps/accounts/schema.py` | `dd2e81b3` |
| `docs/review/review-0_0_15.md` | `c64670dd` |
| `docs/review/rev-auth__mutations.md` | `0d96992a` |

## Findings

### High

None.

### Medium

None.

### Low

#### F1: the holder metaclass re-implements the owner's `_mutation_meta` head seal

Discharges looks-for entry 10 (two sites implementing one rule).

- **Observation** — `django_strawberry_framework/auth/mutations.py::_SealedAuthHolderMeta`
  is a second authoritative definition of the `_mutation_meta` head
  seal owned by
  `django_strawberry_framework/mutations/sets.py::make_meta_validating_metaclass`.
  Both `__setattr__` bodies are the identical guard
  (`name == "_mutation_meta" and "_mutation_meta" in
  truth.class_dict(cls)`, raising `ConfigurationError`), and both
  `__delattr__` bodies likewise; only the message tail differs. The
  holder needs no `Meta` validation (it carries no `Meta`, and the
  owner's `__new__` skips `Meta`-less classes without registering),
  so the bespoke 26-line metaclass exists only to carry the
  auth-specific message tail.
- **Evidence** — Guard bodies compared by hand: the membership test,
  the sealed-head name, the raise type and the first message clause
  are identical; the tails are "the auth surface's validated
  permission set is captured once at declaration time" (target) vs
  "the validated authorization snapshot is captured once at class
  creation" (owner). `check_citations.py --cited-by` reports 0
  citing sites for both `_SealedAuthHolderMeta` and
  `_make_permission_holder` (550 files searched), so no standing
  doc or code comment constrains the consolidation. Probe
  `review-20260929T144009-1beb34` (exit 0, `F1-PROBE-OK`) builds
  the holder namespace on `DjangoMutationMetaclass` instead:
  creation succeeds without registering in the mutation ledger
  (ledger length unchanged), the allow-any `check_permission` ride
  returns `True`, rebind and delete raise the owner's seal
  `ConfigurationError`, unrelated attrs stay writable/deletable,
  and a denying permission class raises the `GraphQLError`
  denial. Pre-fix seal nodes green:
  `review-20260929T144302-7cb606` (`2 passed`).
- **Impact** — A guard-logic change (covering a further head,
  changing the membership test) must land in both metaclasses or
  the fixed auth surfaces (`login` / `logout` / `current_user`
  holders) silently keep the old seal. The behavioral delta of the
  fix is the diagnostic tail only; the register rider (a real
  `DjangoMutation`) is untouched.
- **Severity** — Low: bounded maintainability (single-sites a
  6-line guard x2, deletes ~26 lines); no correctness or contract
  impact beyond diagnostic wording.
- **Recommendation** — Delete `_SealedAuthHolderMeta`;
  `django_strawberry_framework/auth/mutations.py::_make_permission_holder`
  calls `DjangoMutationMetaclass(holder_name, (), ns)` with the
  identical namespace, importing the metaclass alongside the
  existing `mutations/sets.py` imports (no new dependency edge, no
  owner change). Update the one exact-message assertion in
  `test_sealed_holder_rebind_message_names_the_holder` to the
  owner's wording (keep both seal-test node ids; update only the
  expected string) and the `_SealedAuthHolderMeta` prose mention
  in `test_auth_permission_holder_head_is_sealed`'s docstring.
  Judgment call, stated for the implementer: the auth-specific
  tail is deliberately pinned today; this finding treats it as
  nominal variation, not a load-bearing diagnostic contract.
- **Must not change** — Seal behavior (post-creation rebind/delete
  of `_mutation_meta` raise `ConfigurationError`; unrelated attrs
  writable/deletable; holder construction registers nothing; the
  allow-any default and the denial shape stay byte-identical),
  except the seal message tail, which becomes the owner's wording.
- **Proof** —
  Static gate, shared tree (post-fix: no output, exit 0):
  `grep -rn "_SealedAuthHolderMeta" django_strawberry_framework/ tests/ examples/ --include='*.py' --exclude-dir=__pycache__; test $? -eq 1`
  Focused tests at the verify address (post-fix: `2 passed`):
  `uv run python scripts/workspace.py run review/auth/mutations.py/verify-mechanics-<n> -- pytest tests/auth/test_mutations.py::test_auth_permission_holder_head_is_sealed tests/auth/test_mutations.py::test_sealed_holder_rebind_message_names_the_holder --no-cov`
- **Freshness** — Covered by `## Trace`; no additional files.
- **Owner + contract source** — Owner:
  `django_strawberry_framework/mutations/sets.py`
  (`DjangoMutationMetaclass`, built by
  `make_meta_validating_metaclass`). Contract source: the seal
  contract both docstrings state (post-creation `_mutation_meta`
  writes raise `ConfigurationError`, closing the hook-rebind
  bypass class); the holder's own "Mirrors ..." docstring
  acknowledges the twin.
- **DRY record** — Contract: post-creation rebind/delete of the
  `_mutation_meta` head raises `ConfigurationError`. Variation:
  the diagnostic tail (auth-specific vs owner-generic), pinned by
  `test_sealed_holder_rebind_message_names_the_holder` on the
  auth side; the migration resolves it in favor of the owner's
  wording. Sites + roles: the `MetaValidatingMetaclass` produced by
  `make_meta_validating_metaclass` (owner, authoritative for
  write-flavor mutations) and
  `auth/mutations.py::_SealedAuthHolderMeta` (mirror,
  authoritative for the three fixed holders). Challenges:
  "the seal must cover a further head or change its predicate"
  counts 2 authoritative definitions (> 1); "reword the seal
  diagnostic" counts 2 sites (the cosmetic variation). Owner +
  lifetime: `DjangoMutationMetaclass` (the public binding of that
  factory's product in `mutations/sets.py`), the process-lifetime
  metaclass whose `__new__` already skips `Meta`-less
  classes. Migration: as in Recommendation; no owner edit, no
  citation impact. Behavioral proof: the probe above plus the two
  seal nodes post-fix. Structural gate: the `grep` Proof (0 refs
  in source + tests + examples). Negative control: the same
  `grep` on the current tree prints 3 hits (the class, its call
  site, one test docstring) and fails the gate.

## Rejected

Discharge map (looks-for entry -> verdict): 1 none (R1), 2 none
(R2), 3 none + one routed glossary lead (R3), 4 none (R4), 5 none
(R5), 6 none (R6), 7 none (R7), 8 none (R8), 9 none (R9),
10 finding F1 + rejections R10-R14, 11 none (R15), 12 rejections
R16-R19.

#### R1 [1: rule at caller] none — every shared rule rides its owner by call

Permission validation/normalization rides `_validate_permission_classes`;
gate iteration rides `DjangoMutation.check_permission` ->
`run_permission_classes` (the holder instance supplies
`type(self)._mutation_meta`); denial mapping rides
`authorize_or_raise`; payload construction rides `build_payload` /
`payload_cls_for` / `build_payload_type`; request resolution rides
`request_from_info` under the single `_AUTH_FAMILY_LABEL`;
transport/session/capability ride `auth/sessions.py`; declaration
mechanics ride `make_declaration_registry`; lazy refs and the
field signature ride `mutations/fields.py`; storability rides
`unencodable_text_error`; directives ride
`validated_field_directives`; decode/write/envelope ride
`_model_decode_step` / `_model_write_step` / `run_write_pipeline_sync`.
No caller re-spells an owner's rule.

#### R2 [2: policy/mechanism layering] none — auth policy sits in the auth flavor

The AllowAny default (`unset_default=()`), the undifferentiated
login envelope, the protected register fields, the conflict rule
and the capability rejections are auth-surface policy, owned by
the auth flavor that declares them; every mechanism underneath is
ridden by call (R1). The one deliberate non-reuse (password
failures keyed directly, not via `validation_error_to_field_errors`)
is documented with its structural reason (a list-style
`ValidationError` carries no `error_dict`).

#### R3 [3: contract sources differ] none for the body — one glossary parenthetical routed

README (auth surface, transport matrix, masking table, envelope,
security profile) and the GLOSSARY `auth-mutations` anchor agree
with the body on every checked row: the `"Incorrect
username/password"` bytes, the `__all__` + message-only failed
envelope (`codes=[]` via the shared leaf default), the AllowAny
default, the 5-field protected set, `validate_password(user)` +
`set_password`-before-`full_clean`, the transport matrix and its
top-level-error shape, fail-closed compensation, login skipping
visibility/re-fetch while register rides the pipeline re-fetch,
and the phase-2.5 bind order (verified in the finalizer: pre-bind
reset -> `bind_auth_mutations()` via `loaded_attr` -> `bind_mutations()`).
The single discrepancy is GLOSSARY prose, not body behavior: the
anchor's parenthetical lists four protected fields, omitting
`is_active`, while README + body + tests pin five. Routed lead
for Worker-0 (glossary-DB edit + render, outside the item fence).
Trigger: a contract source is amended to demand behavior the body
lacks.

#### R4 [4: unreachable branch] none — every cold arm has a pinned real path

The sync `CHANNELS_HTTP` arms are pinned through the
directly-invoked `SyncGraphQLHTTPConsumer` shape (a feasible
consumer-mounted project; the package router serves no HTTP since
spec-046, as the docstrings state), `test_sync_channels_http_bridge_establishes_and_persists_the_session`
and `test_sync_channels_http_logout_bridge_tears_down_the_session`.
WebSocket-under-sync shares the reachable logout `else` (no
distinct dead arm). The awaitable/non-`str`/`None` password paths
are fail-closed defensive leaves with pins; compensation paths
are pinned via fault injection (store outage, raising receivers,
cleanup failure incl. cancellation); the bind early-return, both
`_resolve_user_primary_or_raise` raises, the conflict raise and
all seal raises are pinned via schema/declaration shapes. The
100% gate corroborates execution; reachability per arm is as
above.

#### R5 [5: mode flag] none — keys and a named enum, no behavior flag

`_auth_surface` is a closed-set registry key (dispatch-by-key in
the surface-keyed bind, message lookup in the conflict raise),
never a behavior switch inside one body. `Transport` is the named
enum with per-mode native paths (the mode-flag alternative done
right). The `supported` predicate in `_transport_prologue` is
strategy injection, and operation strings are domain names for
the gates.

#### R6 [6: state in two places] none — one ledger, one object, natives own the rest

The declaration ledger single-sites declaration + same-args cache
+ conflict state (draining drains all three, pinned by the
clear-then-redeclare test). The rider's dual-ledger membership
references one class object for two binds' distinct concerns and
both ledgers are full-clear-only (the pre-bind reset touches
neither), so they cannot diverge. Holder bind outputs are written
once at bind; session/user/backend/`last_login`/CSRF stay with
the Django/Channels natives (no framework second copy);
anonymity has the one `_authenticated_actor_or_none` definition
shared by logout and `current_user`.

#### R7 [7: dependency direction] none — downward edges plus one documented lazy back-edge

Auth imports `mutations/*`, `utils/*` and `registry` (downward;
the flavor depends on the foundation). The one upward edge
(`bind_auth_mutations` -> `auth/queries.py`) is function-local
with the cycle documented at the site, matched by
`queries.py` -> `mutations.py` at top level (folder-internal,
laziness-broken). No `TYPE_CHECKING` imports exist. The
function-local `resolvers` / `write_values` / `errors` /
`channels.auth` / `asgiref` imports hide no cycle
(`mutations/*` and `utils/*` import nothing from `auth`,
verified by grep): soft-dependency gating and the codebase's
bind/resolver-time import idiom. Trigger: an `auth` import
appearing in `mutations/*` or `utils/*` would make the lazy
`resolvers` imports load-bearing.

#### R8 [8: settings at import] none — all settings/user-model reads are lazy

No `django.conf.settings` import. `get_user_model()` runs at
first factory call and at bind, never at module import; the
`SESSION_ENGINE` read sits at request time inside the
`sessions.py` capability predicate. The module import's only side
effect is the standard `register_subsystem_clear` row.

#### R9 [9: `__all__` disagreement] none — no `__all__` here, deliberate curation above

The target carries no `__all__`. The folder `__init__`
deliberately exports only the four consumer factories
(`auth/sessions.py` records the deliberate non-export of the
transport module). The unexported public helpers
(`derive_register_fields`, `bind_auth_mutations`, the ledger
trio) are module-internal seams reached by dotted path (the
finalizer via `loaded_attr`, tests directly); `derive_register_fields`
is public-for-tests by documented intent (takes the model as an
argument so default and custom user models are directly
testable).

#### R10 [10: duplication] rejected — the snapshot mirror is structural

`_AuthMutationMetaSnapshot` shares the seal idiom with
`_ValidatedMutationMeta` but is a model-less 2-slot record vs a
15-slot model record, and its docstring records the deliberate
non-subclassing with the structural reason (no `model` /
`operation` kwargs to give the model constructor). Sharing it
needs a new base abstraction in the owner for an 8-line idiom
with pinned per-side messages — owner surgery, unlike F1's
in-fence reuse. Trigger: a third sealed snapshot appears, or
the owner extracts a sealed-record base — the auth snapshot
rides it.

#### R11 [10: duplication] rejected — the bind payload arms are owner-blessed legs

The login/logout materialize arms share only the already
single-sited builder + ledger calls; the arms themselves are the
surface-keyed bind's explicit per-surface legs (user-typed vs
model-less), and `bind_mutation_outputs` documents why holders
stay local (fixed payload name, no `_input_class`). A helper
would hide the surface keying to save four lines. Trigger: a
third fixed-payload arm lands — extract the helper then.

#### R12 [10: duplication] rejected — establish/teardown twins are execution twins

The sync/async establish and teardown pairs share the fail-closed
protocol but every statement differs by execution context (sync
vs awaited natives, scope lock vs none, `request` vs `scope`
actor). Consolidation needs a sync/async abstraction worse than
the twin; drift is covered by R15. No trigger (structural).

#### R13 [10: duplication] rejected — prologue residue already factored

`_login_authenticate` vs `_logout_prologue` share their common
prefix via `_transport_prologue`; the residue differs per
surface (gate data, `authenticate` vs not, payload needs). The
sync/async resolve bodies share prologue + payload helpers; the
residual sequencing is the twin structure itself. Trigger: a
third surface needs the same prologue shape — extend
`_transport_prologue`'s parameters instead of adding a twin.

#### R14 [10: duplication] rejected — the per-request wire-name map matches the owner

`_run_register_pipeline_sync` builds `_build_wire_name_map` per
request exactly as the model flavor's own write path does (the
`skeleton` call site in `resolvers.py`); any memoization belongs
to the owner. Routed lead for the `mutations/resolvers.py`
item's Performance pass. Trigger: the owner memoizes — the
rider adopts.

#### R15 [11: twin drift] none — five pairs compared, symmetric with documented deltas

Login resolve sync/async, logout resolve sync/async, login
establish Django/Channels, logout teardown Django/Channels, and
register resolve sync/async: all share prologue/payload helpers
where the execution allows, construct payloads before mutation,
and early-return identically. Deltas are per-transport and
documented (scope lock + actor lease are Channels-only; the
async dispatch polarity differs because login's native path is
Channels-HTTP-only while logout's is Channels-any). Spot
attacks: WebSocket login under async bridges then raises the
same `ConfigurationError` inside the boundary; signed-cookie
WebSocket logout raises the same error from the in-boundary
prologue.

#### R16 [12: guard asymmetry] rejected — gate shapes differ by surface necessity

`current_user` passes `instance=actor` (object gates need it; the
actor read necessarily precedes the gate), login passes
`data={"username"}` (no actor exists pre-`authenticate`; the
password is deliberately excluded), logout/register pass
`instance=None` with per-surface data. The write-pipeline
authorize-before-decode invariant holds for every write (login
gates before `authenticate`, so denied credentials are never
checked; register rides the pipeline; logout gates before
teardown). No contract source demands uniform gate shapes.
Trigger: README/GLOSSARY is amended to promise object-level
gates an instance on logout.

#### R17 [12: guard asymmetry] rejected — the actor lease is inapplicable off-Channels

Only `_channels_logout` holds `actor_transition`: the lease
excludes multiplexed-connection revalidation checkpoints, which
exist only on the WebSocket consumer (`consumers.py`). Django
HTTP requests have no scope and no checkpoints (inapplicable by
construction), and login serves HTTP-only scopes (WebSocket
rejected before authentication), so no checkpoint can interleave
its establish. Trigger: checkpoints ever run on non-WebSocket
scopes.

#### R18 [12: guard asymmetry] rejected — no contract covers timestamp fields

`last_login` / `date_joined` (editable timestamps a pathological
`REQUIRED_FIELDS` could expose) are not privilege or activation
state; no contract source demands their rejection. A robustness
consideration at most, never a blocker. Trigger: the
registration-surface contract is extended to timestamps.

#### R19 [12: guard asymmetry] rejected — hook misuse fails loud by design

Custom `has_permission` hooks must key on `info` / `operation` /
`data`, never on the holder's absent `Meta` — a documented,
not factory-guarded, constraint; misuse raises `AttributeError`
loudly. No contract demands factory guarding. Trigger: a
supported hook contract promises `Meta` access on fixed
surfaces.

Handoff: Beyond the record I read the plan's `## Owned changes`
(no row for this target) and `## Decisions` (for routing
precedent: glossary prose and owner-performance items route out,
they are not findings here), the `review_inspect.py` overview
whole, and every owner body named in the trace. Conclusions not
in the findings: the per-request micro-costs I noticed
(`payload_cls_for` + slot per login, the doubled
request/classify in the async bodies, function-local imports per
request) are nanoseconds against a bcrypt-and-DB path and the
Performance sibling owns them — deliberately not raised
cross-axis; the `request.session.save()` double-write is
documented cookie mechanics, not waste; README's informal
"AllowAny" next to the target's "no `AllowAny` class exists" is
docs-prose precision worth one maintainer glance, not a finding;
the five private imports `queries.py` takes from this module are
correct single-sourcing whose placement belongs to the `auth/`
folder integration item. Open threads for Worker-2/verifier: F1's
message-wording judgment call (stated in the Recommendation);
the GLOSSARY `is_active` omission and the `resolvers.py`
wire-map memoization are routed, not owned here; `sharded`/`pg`
inapplicability for F1 is stated with its reason for the
verifier to judge.

## Verify mechanics

Precondition: the live tree carries exactly the change under
grade. `git diff 8a53fa09 -- <the three item paths>` is
byte-identical (`cmp`) to
`docs/review/temp-tests/auth-mutations/diff/pass-1.diff`.
Live fingerprints: `auth/mutations.py` 98ae63f1,
`tests/auth/test_mutations.py` 4cb49982,
`tests/auth/conftest.py` a5c413ba. All runs below at
`review/auth/mutations.py/verify-mechanics-1` (slot-4,
package digest
`sha256:6b2d9c42a88afa2fdfb82dfc7abb78b083aba7b4005ed7cf5cefd6442d75a092`,
copy `fresh`, default cell) unless noted.

### F1 Proof, static gate - pass

Shared-tree `grep -rn "_SealedAuthHolderMeta"
django_strawberry_framework/ tests/ examples/
--include='*.py' --exclude-dir=__pycache__; test $? -eq 1`
prints nothing and the gate passes: zero refs in source +
tests + examples. The record's negative control (3 hits
pre-fix) is reproduced in the revert experiment below (2
hits in production after reverting that file alone; the
test docstring stays rewritten).

### F1 Proof, seal nodes - pass

`review-20260929T151424-314f70` (fresh, default cell): the
record's two nodes verbatim -
`test_auth_permission_holder_head_is_sealed`,
`test_sealed_holder_rebind_message_names_the_holder` -
report `2 passed`. Repeated pre-provenance
(`review-20260929T151400-40f887`, `2 passed`) and
post-restore (`review-20260929T151908-91c9e7`, `2 passed`).

### F1 migration, behavioral probe - pass

`review-20260929T151615-cb8c2c` (exit 0,
`VERIFY-F1-OK`): `verify-mechanics-1/probe_f1_migration.py`
drives the shipped `_make_permission_holder`, not a
reconstruction. `type(holder) is DjangoMutationMetaclass`;
ledger `0 -> 0` across synthesis and the holder is absent
from `iter_mutations()` (the owner's `__new__` Meta-less
skip, read at `sets.py:599-602`); allow-any
`check_permission` returns `True`; rebind and delete raise
`ConfigurationError`; unrelated `_primary_type` writes and
deletes freely; the denial is `GraphQLError "Not authorized
to logout Session."`, byte-identical to the string
`test_gated_logout_denies_with_the_session_holder_string`
pins. The message tail is the owner's: the probe triggers
the seal on `DjangoMutation` itself and the holder tails
equal that tail exactly
("the validated authorization snapshot is captured once at
class creation."), with `DjangoMutation._mutation_meta`
still `None` afterwards.

### Before/after delta is exactly the two tails - pass

The pre-fix messages read from `git show 8a53fa09:...`:
rebind carried "the auth surface's validated permission
set is captured once at declaration time.", delete "the
validated authorization snapshot is captured once at
declaration time.". Post-fix both carry the owner's "at
class creation" tail (probe-measured above). Executing the
probe in the `before` copy was impossible - its venv is
broken (`ModuleNotFoundError: No module named
'asgiref.sync'`, `review-20260929T151624-90700b`, exit 1;
open thread 1, pool hygiene, no Proof needs that copy) -
so the before side rests on the baseline text plus the
revert experiment below, which executes the old code and
shows the old tail returning.

### No new dependency edge - pass

The diff adds `DjangoMutationMetaclass` to the existing
`from ..mutations.sets import (...)` block beside
`DjangoMutation` (same module, already imported); owner
file `mutations/sets.py` has zero diff vs ITEM_BASELINE;
the function-local `bind_auth_mutations -> auth/queries.py`
back-edge is untouched. R7 stands.

### Code delta is F1-only (AST identity) - pass

Static `verify-mechanics-1/ast_diff.py` (docstrings
stripped; comments never parse): the target code-AST delta
is exactly the import alias, the `_SealedAuthHolderMeta`
`ClassDef` deletion, and the call-site `Name` swap - every
Comments M/L hunk in the file is prose-only. The test
code-AST delta is exactly the one expected-string constant
(owner wording). `truth` is still used 11 times: no
orphaned import (ruff concurs).

### Rejections R1-R19 stand - pass

R1-R6, R8-R9, R11-R19 judge behavior and placement the
AST proof shows untouched (callers still ride owners;
AllowAny default, envelope bytes, transport matrix,
compensation, twin symmetry, gate shapes all pinned by the
green suite below). R7 stands (same-module import, above).
R10 stands (`_AuthMutationMetaSnapshot` untouched; its
trigger - a third sealed snapshot or an owner-extracted
base - did not occur). The M2 comment rescoping (three
fixed fields, register rides pipeline gates) agrees with
R1/R16 rather than undermining them.

### Failability: revert restores the mirror, the test catches it - pass

`review-20260929T151848-8872af` (exit 1): with the
baseline production file restored inside the copy (test
file kept new), the message test fails showing the old
tail ("the auth surface's validated permission set ... at
declaration time") against the new expectation, while the
seal-behavior test still passes - the delta is exactly the
wording, and the pin fails without the change. The static
gate fails on the reverted copy (2 production hits). The
copy was byte-restored (`cmp` vs the shared tree) and the
seal nodes report `2 passed` again
(`review-20260929T151908-91c9e7`).

### Auth package suite green - pass

`review-20260929T151757-9600bf` (fresh, default cell):
`pytest tests/auth/ --no-cov -q` reports `135 passed`
(exit 0), covering the holder seal rows, the
allow-any/denial pins, the queries/sessions suites, and
the register-rider rows. ("Shared moved: 4" on that run
is docs-only concurrent work - dry records plus the two
sibling axis records - no package impact.)

### Lint gates - pass

Shared tree: `ruff check` (all checks passed), `ruff
format --check` (3 files already formatted), and
`check_trailing_commas.py --check` (0 violations) on the
three touched paths; `check_citations.py --check` on the
tree (1302 citations resolve).

### Whole-diff reading - pass

Only F1 changes behavior; the register rider is a real
`DjangoMutation` in an untouched owner file; all three
fixed holders share the one synthesis site so the seal
moves uniformly; the conftest hunk is prose-only. No
`## Cross-axis (for Mechanics)` exists in either sibling
record; no finding was disputed; the record's
message-wording judgment call is accepted (the tail is
pinned to the owner's wording and the failability run
bounds the delta to it). The routed GLOSSARY `is_active`
and `resolvers.py` wire-map leads stay routed. No
`## Implementation (Worker-2)` section exists in the main
artifact; per this run's precedent (resource_policy) the
ledger rows plus the pass diff are complete and no
re-pass is owed (open thread 2, same as that item's).

### Cells - judged

Default ran every probe and suite above. `sharded` and
`pg` are `inapplicable by construction` for F1, as the
record states: holder-class construction is
declaration-time (no database, alias, or dialect
decision), the owner's Meta-less skip is pure Python, and
both Proof nodes are database-free class-mechanics tests.
No cell failed to run for a reason the item owns (open
thread 1 is pool hygiene).

New defects: none.

Handoff: Verification is closed with F1 implemented
exactly as recommended. Beyond the record I read the
pass-1 diff whole, the live target's import/holder
regions, the owner's `__new__`/seal bodies, the seal and
denial test rows, and the sibling review scratch probes
for instrument precedent (my probe drives the shipped
function; the AST script is my own). Open threads for
Worker-0: (1) the `before` copy's venv is broken
(`review-20260929T151624-90700b`) - release/repair at
pool level; (2) the main artifact lacks
`## Implementation (Worker-2)` - judged unneeded, same as
the resource_policy item. Fingerprints verified this
pass: target 98ae63f1, tests 4cb49982, conftest a5c413ba.

Status: verified. Open threads: (1) `before`-copy venv
broken (pool hygiene, no Proof affected); (2) main
artifact lacks `## Implementation (Worker-2)` (judged
unneeded, run precedent).
