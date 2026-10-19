# DRY review: `upstream-patch-lifecycle`

Status: verified
Run: 0.0.15 2026-10-01-9

Family `upstream-patch-lifecycle`. Owner TBD by dispatch
- decided here: none; the family is rejected as one rule
and decomposes into ten sub-rules (nine rejections with
contract differences plus triggers, one single-owned),
re-derived, not inherited. Indexed files (4):
`django_strawberry_framework/_cross_web_patches.py`,
`django_strawberry_framework/_django_patches.py`,
`django_strawberry_framework/_strawberry_patches.py`,
`django_strawberry_framework/_graphql_core_patches.py`.
Trace at HEAD `5c3496e0` bytes (working tree carries
concurrent truth-migration plus docstring dirt on all four;
the dirt map below keeps every citation comparable);
`ITEM_BASELINE=cffde96104cf5d68f93c93d11c93bba4c9b5a6de`.
Prior record (run-2 File `_cross_web_patches.py` naming
this open family spanning all four patch modules,
W2-endorsed, transcribing nothing) used only as a
population hint; every verdict below re-derived fresh at
HEAD bytes. Never read any `worker-memory/`.

Verdict in one line: REJECT - the four patch modules share
a lifecycle TEMPLATE whose every member is a per-module
contract (descriptor kind, capture set, validation depth,
install shape, retirement ticket); nine rejections carry
contract differences plus triggers and the dispatch set is
single-owned at `apps.py::ready`. Zero edits; durable-home
clauses homed to closeout (every owner file hunt-dirty).
Not blocked-on-hunt: no consolidation confirmed, so no
landing is barred.

## System trace

The queued rule is the upstream monkeypatch lifecycle:
detection (is the patch installed), guarding (capture the
genuine upstream callable, refuse drifted shapes),
application (gate, validate, install, self-heal), and
retirement (upstream-status prose plus probes) across the
four patch modules. Each module patches one third-party
dependency: Django test teardown (`django`), Strawberry
HTTP views (`strawberry`), the `cross_web` sync request
adapter (`cross_web`), the `graphql-core` executor
(`graphql_core`).

Whole-package sweep over all 119 present
`django_strawberry_framework/` `.py` files (117 tracked
plus the untracked concurrent `utils/truth.py` and
`utils/lazy.py`) for the mechanism vocabulary
(`_PATCH_OWNER_ATTRIBUTE`, `_PATCH_ORIGINAL_ATTRIBUTE`,
`_PATCH_OWNER`, `_captured_upstream`, `_upstream_captures`,
`_validate_upstream_shape`, `_patch_is_installed`,
`^def apply`, `upstream_patches_enabled`,
`APPLY_UPSTREAM_PATCHES`, `UPSTREAM_PATCH_DEPENDENCIES`,
`__dict__.get`, `truth.class_dict`, `inspect.signature`,
`inspect.getsource`, `importlib.reload`, `retir`,
`setattr([A-Z]`, `= classmethod(`, `= property(`,
`startswith("django_strawberry_framework`): every
executable lifecycle hit lands in the four indexed files.
No fifth module defines, consumes, or mirrors the
lifecycle; the shadow candidates the sweep surfaced are
all excluded with contract differences (table below).
The `e11` sibling family owns refusal WORDING; this item
owns the lifecycle DECISIONS (which conditions refuse,
what installs, how retirement is detected). The boundary
is drawn, not absorbed: 11 apply-time refusal decision
points (3 plus 3 plus 3 plus 2 across the four
validators and capture gates) stay per-module here, and
their message text belongs to `e11`.

Lifecycle members per module at HEAD bytes (WT line
numbers; the dirt map keeps them comparable):

| member | cross_web | django | strawberry | graphql_core |
|---|---|---|---|---|
| missing-symbol sentinel import | Y (`:214`-`:220`) | Y (`:131`-`:139`) | Y (`:415`-`:436`) | Y (`:42`-`:52`) |
| capture fn | body_getter (`:228`, property kind) | descriptor (`:147`, classmethod kind) | method (`:444`, plain kind) | method (`:60`, plain kind) |
| recovery predicate | exact-owner | exact-owner | exact-owner | exact-owner OR package-prefix (`:64`-`:68`) |
| call-time captures gate | none | none | Y (`:548`) | Y (`:88`) |
| shape validation | sig 1-param (`:259`) | sig 1-param plus body SET of 2 (`:242`) | sig 2-param x4 plus body single (`:589`) | sig 6-param (`:108`) |
| replacement stamping | 2 inline setattrs (`:336`-`:337`) | 2 inline setattrs (`:381`-`:386`) | `_mark_patch_replacement` helper (`:890`) plus 4 calls | 2 inline setattrs (`:171`-`:176`) |
| installed probe | property-fget identity (`:340`) | classmethod-`__func__` identity (`:389`) | 4-member plain conjunction (`:909`) | 1-member plain identity (`:179`) |
| apply order | gate, validate, check, install (`:348`) | gate, validate plus record, check, install (`:407`) | gate, validate, check, install (`:930`) | gate, validate, check, install (`:187`) |
| retirement prose | status plus re-check plus probe | wontfix-ticket note only | status plus re-check plus probe | status plus retirement line |

HEAD-vs-WT dirt map for the four indexed files (all four
dirty with concurrent work; every hunk unattributed to
`## Owned changes`, attributed here by diff content so
Worker-2 can compare citations at either revision):

- All four: `from .utils import truth` added; every
  lifecycle `Owner.__dict__.get(name)` read migrated to
  `truth.class_dict(Owner).get(name)` (cross_web capture
  plus probe; django capture plus probe; strawberry
  capture plus 4 probe members; graphql_core capture
  plus probe). Decision points identical.
- django only: `getattr(x, "__func__", None)` replaced by
  `x.__func__ if truth.is_instance(x, classmethod) else
  None` at the capture, the validator, and the probe;
  the validator condition drops its now-redundant
  `not isinstance(descriptor, classmethod)` disjunct
  (equivalent: `function` is `None` exactly then).
  Comment plus docstring rewords: the audited-set
  comment and the validator docstring no longer name
  "the delegating siblings
  (`_cross_web_patches`/`_strawberry_patches`)" (HEAD
  wording) but "a delegating wrapper"; the replacement
  docstring reworded. Lifecycle shape unchanged.
- graphql_core only: wrapper predicate reordered to
  `isinstance(result, AsyncIterable)` first (subject
  matter, not lifecycle); `except ImportError` comment
  reworded.
- strawberry only: module-docstring GET-shield paragraph
  reworded (HEAD: nested parses call "the captured
  `_original_parse_json` directly"; WT: "the shared
  translator"); three function one-liners reworded.
  Lifecycle shape unchanged.

No dirt hunk adds, removes, renames, or reorders a
lifecycle decision point; the verdicts below read HEAD
semantics at WT line numbers.

Role census. Consumers: `apps.py::ready` (the sole
package caller of all four `apply()`, imports `:48`-`:51`,
calls `:53`-`:56`, order django, strawberry, cross_web,
graphql_core); the four `apply()` gates consuming
`conf.py::upstream_patches_enabled` (`:361`) with the
`conf.py::UPSTREAM_PATCH_DEPENDENCIES` key set (`:76`);
`testing/_wrap.py` importing `_is_database_failure` from
`_django_patches` (subject matter, not lifecycle).
Oracles: 80 per-module tests (`test_cross_web_patches`
14, `test_django_patches` 25, `test_strawberry_patches`
33, `test_graphql_core_patches` 8); `test_apps.py` 8
tests owning the dispatch contract (`:121`) plus the
four-module double-reload recovery contract (`:204`,
parametrized django, strawberry, cross-web,
graphql-core); `test_conf.py` 11 gate tests (`:199`-`:308`);
live `test_transport_api.py` restore-by-identity blocks
asserting both probe directions (`:1821`, `:1921`,
`:2042`) plus the cross_web-half retirement row, the
strawberry opt-out row, and the multipart-map rows;
live `test_products_api.py` non-object-body rows.
Projections: module docstrings (bug, gate, status,
re-check, visibility sections); `apps.py::ready`
docstring (dispatch inventory, deliberately repeating
none of the per-module bug inventory);
`conf.py::UPSTREAM_PATCH_DEPENDENCIES` comment (joint
strawberry plus cross_web ownership);
`test_query/README.md` suite-map rows; spec-050 one
config-shape mention (`:1606`). No test and no script
spells the stamp literals or reads the stamp constants;
the stamp pairs are written and read only inside their
own module.

Shadow candidates excluded with contract differences
(each swept, read, and excluded fresh; none is a second
lifecycle definition):

- `types/relay.py:833` (`type_cls.resolve_typename =
  classmethod(...)`): patches a package-owned generated
  type, not an upstream symbol; no capture, stamp,
  validation, gate, or retirement. First-party type
  assembly, not third-party monkeypatching.
- `utils/private_state.py` (`owner.__dict__[name]`
  writes): files the package's own private state past
  descriptors; never touches a foreign class, never
  validates an upstream shape.
- `filters/sets.py::_AUDITED_DJANGO_FILTER_RANGE` plus
  `_release_is_audited`: an audited-VERSION-RANGE gate
  for optimizer routing that fails closed to the
  unoptimized path. Different subject (routing vs
  install), different failure mode (degraded path vs
  loud refusal), different reason to change (new
  django-filter release vs new patched-body shape).
- `utils/querysets.py` (`_pk_membership_query_or_defect`
  read, "audited over every published Django ... read,
  never patched"): an audited upstream READ, explicitly
  never a patch; no install or retire half exists.
- `routers.py::signature` plus `types/base.py::bind`
  (`inspect.signature` uses): validate
  consumer-supplied callables with bind semantics, not
  upstream methods with exact-arity plus kind
  strictness. Consumer contract vs upstream shape pin.
- `extensions/operation_state.py:597`
  (`self.__dict__.get`): own-instance read with a
  truth marker, not a foreign-class probe.
- `utils/inputs.py` (`sys.modules[...].__dict__[name]`):
  lazy-input materialization from a module namespace,
  not upstream patching.
- `views.py::_RawBodyRequestAdapter` plus
  `_RequestBodyBoundaryMixin.parse_json`: package-owned
  enforcement that behaves identically with the
  cross_web patch installed or not (stated in both
  module docstrings); a coexistence contract, not a
  lifecycle member. It subclasses the patched adapter
  rather than reusing `_patched_body`, deliberately.
- `testing/_wrap.py::safe_wrap_connection_method`:
  wrap-time consumer helper complementing the django
  patch's unwrap-time guard; subject-matter companion,
  no lifecycle machinery.
- `filters/sets.py:720`, `:819` plus
  `optimizer/plans.py:576` "retired" mentions: dead
  mechanism history and a window-case note, not
  upstream-patch retirement.

Freshness pins (WT `git hash-object`, 12 hex, then HEAD
`git rev-parse`, 12 hex; `=` means identical):

- indexed `_cross_web_patches.py`: WT `16c05c78e104`,
  HEAD `e5a69a5500bb` (dirt per map above)
- indexed `_django_patches.py`: WT `5ca5493ffa49`,
  HEAD `20bfb1f87de2` (dirt per map above)
- indexed `_strawberry_patches.py`: WT `ec4926749e9e`,
  HEAD `aa08b628c84a` (dirt per map above)
- indexed `_graphql_core_patches.py`: WT `2d1dd0cd6331`,
  HEAD `8ede2487994c` (dirt per map above)
- excluded `types/relay.py`: WT `9903f6ea32bf`,
  HEAD `2d1efd0025e5`
- excluded `utils/private_state.py`: WT `613a28ca463f`,
  HEAD `ec4d8fc8fa6f`
- excluded `filters/sets.py`: WT `697ffd4029a4`,
  HEAD `85699ac22e1d`
- excluded `utils/querysets.py`: WT `3e392d487b81`,
  HEAD `69ac3ea3fc6e`
- excluded `routers.py`: WT `16b68dcb1b24`,
  HEAD `74dae93836fc`
- excluded `types/base.py`: WT `763a5acc9295`,
  HEAD `e8416cc0a497`
- excluded `extensions/operation_state.py`: WT
  `bafa39e1e68c`, HEAD `1b43066c9946`
- excluded `utils/inputs.py`: WT `0575e9b265e3`,
  HEAD `0caa341637aa`
- excluded `views.py`: WT `d1ff2aba3ca6`,
  HEAD `d627d5dd9866`
- consumer `apps.py`: `64e82ce1e9e7` = HEAD (clean)
- consumer `conf.py`: WT `d239302afaa5`,
  HEAD `eccddc21c635`
- consumer `testing/_wrap.py`: `a5caa4307e3e` = HEAD
  (clean)
- oracle `tests/test_cross_web_patches.py`:
  `70c16389aa5d` = HEAD (clean)
- oracle `tests/test_django_patches.py`: WT
  `6e62c784389b`, HEAD `e26a26099c12`
- oracle `tests/test_strawberry_patches.py`: WT
  `1da2333dc91b`, HEAD `64f25eeb77b1`
- oracle `tests/test_graphql_core_patches.py`:
  `53dca51737e6` = HEAD (clean)
- oracle `tests/test_apps.py`: WT `fe912987087b`,
  HEAD `5ca8b62c531`
- oracle `tests/base/test_conf.py`: WT `7275af688755`,
  HEAD `f35c70742354`
- oracle `test_transport_api.py`: WT `6d65274f9e7b`,
  HEAD `b1681e8c725c`
- oracle `test_products_api.py`: WT `fe78cf9d4862`,
  HEAD `4186b4d92c22`
- untracked `utils/truth.py` sha256 `49a9d56250c74da7`
  (16 hex); untracked `utils/lazy.py` sha256
  `90c37be7393b95af` (16 hex)
- population: 117 tracked plus 2 untracked = 119
  present package `.py` files; sweeps ran over all
  present files plus `tests/`, `test_query/`, `scripts/`
  for readership. Searched vocabulary listed above.
- contract sources: the four module docstrings, the
  `apps.py::ready` docstring, the
  `conf.py::UPSTREAM_PATCH_DEPENDENCIES` comment plus
  `upstream_patches_enabled` docstring, the `test_apps`
  dispatch plus reload tests, spec-050 `:1606`
  (projection only).

## Verification

### Matrix

1. Cross-flavor policy mirroring: swept types, filters,
   orders, mutations, forms, `rest_framework` for
   patch machinery (capture, stamp, validate, install,
   gate reads). None patches upstream; none reads
   `upstream_patches_enabled`; none keeps a second
   install probe. The only flavor-adjacent hits are the
   excluded `types/relay.py:833` first-party assembly
   and the `filters/sets.py` version-range gate, both
   excluded above with contract differences.
2. Sync/async twins: the lifecycle has no async twin -
   capture, validation, install, and probing are
   import-time plus app-load-time synchronous operations
   with no await boundary. The
   `_patched_sync_parse_multipart` /
   `_patched_async_parse_multipart` pair is a
   subject-matter twin inside one module's patch, not a
   lifecycle twin; both members install through the one
   `apply()` and probe through the one conjunction.
   No twin drift surface exists for the rule itself.
3. Derived rather than repeated knowledge: each
   installed probe re-derives state from a live
   class-dict read plus identity comparison rather than
   a cached flag; that derivation is finding F-A
   (rejected: each probe mirrors its own installer's
   descriptor kind). The `test_apps` reload test
   re-derives nothing from the owner: it restores
   upstream slots by the `_original_*` identity the
   modules captured, which is the oracle spelling the
   contract, not the rule restated.
4. Inverse / round-trip pairs: install has no uninstall
   half - `apply()` installs only, and tests restore
   upstream slots by hand. Capture and install are not
   inverses (capture reads upstream, install writes the
   replacement). The lifecycle's closing half is
   retirement (delete the module once upstream fixes
   the defect), finding F-J, not an uninstall routine.
   No hidden second half found.
5. Contracts restated in another medium: production
   (the four modules), oracles (80 per-module tests
   plus dispatch, reload, gate, and live rows),
   projections (module docstrings, `ready` docstring,
   gate comment, suite map, spec-050 line). The stamp
   literals appear ONLY in production (zero oracle or
   tooling spellings); the refusal messages appear in
   production plus oracle `match=` pins (e11's medium
   pair). The joint strawberry plus cross_web ownership
   is stated in three prose sites (both module
   docstrings plus the gate comment) with live rows
   pinning the behavior; the prose triplication is
   recorded under F-J, not consolidated (projections
   never own).
6. Enforcement by omission: member census per module is
   the table above. `_upstream_captures` exists only
   where wrappers delegate at call time
   (strawberry, graphql_core); django reimplements
   without calling its original and cross_web's
   installed property never calls its getter (stated in
   its docstring), so neither can use a call-time gate
   - principled absence, not a gap. django carries no
   retirement section because its ticket is wontfix
   (no retirement event exists). graphql_core's
   capture and probe carry no docstrings while their
   siblings do; style only, out of scope, noted under
   F-B because the unstated prefix arm lives there. No
   omission has a contract source demanding the member,
   so no defect is filed.

### Enumeration

Instrument: whole-package mechanism-vocabulary grep over
all 119 present files (vocabulary listed in System
trace) plus full reads of the four indexed modules at
HEAD bytes, the `apps.py` dispatcher, the `conf.py`
gate, and the oracle headers named above. 57 mechanism
sites enumerated; every one lands in a sub-rule row or
an exclusion below. Counts: stamp-literal definitions
8 (2 per module), owner-value declarations 4, capture
functions 4, recovery predicates 4, call-time capture
gates 2, shape validators 4, audited-body data
definitions 3 (django 2 bodies plus SET, strawberry 1
body), replacement stampings 4 (3 inline pairs plus 1
helper with 4 calls), installed probes 4 (7 member
checks: 1 property, 1
classmethod, 5 plain), `apply()` definitions 4, gate
call sites 4, dispatch calls 4, sentinel import blocks
4 (9 sentinel symbols: 1 plus 1 plus 5 plus 2;
django's SimpleTestCase imports unconditionally),
retirement docstring sections 3 plus 1 wontfix note.

Every site homes as follows (Worker-0 rows each
sub-rule; the names below are the proposed index rows):

- 4 installed probes -> `patch-installed-detection`
  (F-A, rejected)
- 4 capture functions plus 4 recovery predicates ->
  `patch-upstream-capture` (F-B, rejected)
- 8 stamp literals plus 4 stamping acts ->
  `patch-stamp-vocabulary` (F-C, rejected; the 4 owner
  values recorded as intentional identity separation)
- 4 sentinel import blocks plus their None checks ->
  `patch-missing-symbol-sentinel` (F-D, rejected)
- 2 call-time capture gates ->
  `patch-call-time-captures` (F-E, rejected)
- 4 arity checks (1 plus 1 plus 4-loop plus 6 params) ->
  `patch-arity-tripwire` (F-F, rejected)
- 2 body-pin stanzas plus 3 audited-body data
  definitions -> `patch-body-pin` (F-G, rejected)
- 4 apply orders -> `patch-apply-order` (F-H, rejected)
- 4 dispatch calls plus `ready` ->
  `patch-dispatch-set` (F-I, single-owned)
- 3 retirement sections plus 1 wontfix note plus the
  joint-ownership prose ->
  `patch-retirement` (F-J, rejected)
- 4 gate call sites plus key set plus gate body ->
  pre-existing single owner `conf.py`
  (not a finding; consumed, not duplicated)
- 10 shadow candidates -> exclusions in System trace
  (no index rows; each excluded with a contract
  difference, none with a trigger except the
  version-range pair noted in F-G)

### Challenges

Each sub-rule challenged on its own variation axes;
only authoritative definitions counted (consumers,
oracles, and projections listed, never counted).
Refusal message text never counted here: it is e11's.

- F-A installed detection. (1) "Upstream moves the
  patched attribute": each probe reads its own slot,
  so exactly 1 definition moves per upstream; forced
  together 0. (2) "Derive installed-state from a
  cached flag instead of a live read": all 4 probes
  move, count 4 - but the live derivation is load
  bearing for self-healing (a cached flag lies after
  a third-party revert; stated at django's probe
  docstring and every `apply()` docstring), and the
  change is a deliberate per-module redesign, not a
  rule edit. (3) "Change the namespace read for all
  plain-method member checks" (the 5 identical
  `class_dict.get is expected` checks across
  strawberry plus graphql_core): count 2 - a codemod
  either way (the concurrent truth migration proves
  it), relieving no change obligation. Consumers of
  the probes: 4 `apply()` bodies, `test_apps` dispatch
  plus reload tests, live restore blocks. Verdict
  input: count 4 on an implausible change only.
- F-B upstream capture. (1) "Change the
  descriptor-kind slot read": moves exactly the
  modules of that kind (property 1, classmethod 1,
  plain 2). (2) "Change reload-recovery semantics"
  (e.g. stop recovering the carried original): all 4
  capture functions move, count 4 - except the four
  predicates are not one rule: graphql_core also
  recovers any `django_strawberry_framework.`-stamped
  wrapper (`:66`) while the other three recover
  exact-owner stamps only, and that arm is unstated
  (no docstring on the function) and unpinned (the
  reload oracle exercises same-module stamps only,
  where the first disjunct short-circuits). The
  honest count is 3 plus 1 variant. (3) "Add a new
  descriptor kind" (e.g. staticmethod): moves 0
  existing definitions. Verdict input: kind split
  plus an unadjudicated variant.
- F-C stamp vocabulary. (1) "Rename the stamp
  attributes": correctness requires within-module
  read/write agreement only (zero cross-module
  readers swept across package, tests, and scripts),
  so each pair moves independently; forced together
  0 as definitions, 4 as convention. (2) "Stamp a
  third attribute on every replacement": 4 spellings
  move (3 inline pairs plus the helper), count 4 -
  but no queued or plausible change does this; the
  names are collision-proof by namespace. (3) "Add a
  fifth patch module": adds a fifth spelling, moves 0
  existing. The owner values (4 distinct) move 1 per
  module rename by design. Verdict input: no
  plausible change touches 2 plus existing
  definitions.
- F-D missing-symbol sentinel. "Change the sentinel
  value or check shape" (e.g. tri-state): 4 import
  blocks plus their None checks move, count 4 - but
  the None sentinel is Python idiom and the symbol
  sets differ per module; no shared owner can own
  which symbols exist. No plausible change posited
  beyond a deliberate cross-module redesign.
- F-E call-time captures. "Change the gate protocol"
  (check-then-bundle): 2 gates move, count 2 - but
  the capture sets differ (9 fields vs 3) and the
  proof predicates differ (`inspect.isfunction` for
  the utility whose code object is read vs `callable`
  for a plain delegate), each following its
  downstream use. The two modules without the gate
  cannot use it (no call-time delegation).
- F-F arity tripwire. (1) "Upstream adds a parameter":
  exactly 1 validator moves (re-audit is per
  upstream by nature). (2) "Relax strictness globally
  (tolerate keyword-only extras)": 4 checks move,
  count 4 - but the strictness carries different
  contractual weight per kind (sole shape contract
  for delegators vs tier 1 of 3 ahead of the body
  pin for reimplementers, stated in both validator
  docstrings), and a global relaxation changes what
  each per-upstream audit gets to see. Same answer
  today, separate reasons to change.
- F-G body pin. (1) "A new `getsource` failure mode":
  both stanzas move, count 2 - implausible, since
  `OSError` plus `TypeError` is exhaustive per the
  `inspect.getsource` contract. (2) "Change the
  normalization": both stanzas plus both pinned
  literals move - the data re-pins per module
  regardless, so the stanza never moves alone.
  (3) "A second body joins strawberry's pin": the
  comparisons unify (`not in` SET x2) - the trigger,
  not today's count. The audited DATA (2 Django
  bodies vs 1 Strawberry body) is per-upstream by
  definition.
- F-H apply order. "Check installed before validating
  (skip revalidation on re-entrant apply)": all 4
  orders move, count 4 - but the order's load-bearing
  reason differs (django records the validated source
  for teardown reads on every apply; the others
  revalidate so drift raises on refire, pinned by the
  fail-loud tests that run while installed). A change
  whose safety must be examined per module is 4
  rules with identical current answers, not 1 rule.
- F-I dispatch set. "Add or drop a patch module":
  exactly `ready()` plus the gate key set move (2
  coordinated sites, 1 rule, single-owned at the
  dispatcher by responsibility). Dispatch ORDER
  moves 0 definitions under any permutation: no
  install-time cross-dependency exists (each `apply`
  touches only its own symbols), and the dispatch
  oracle asserts the set, not the sequence.
- F-J retirement. "Upstream fixes the defect": exactly
  1 module retires (per-ticket events in 4 different
  repositories); forced together 0. The section
  template (status plus re-check plus probe) is prose
  convention x3, and probedness differs by defect
  nature (cross_web's uninstall state discriminates
  live; strawberry gap 1 has no live diagnostic, as
  its docstring states).
- Maximal driver ("one patch-driver owning the whole
  lifecycle per principle 1, members as declared
  records"): considered and rejected as machinery.
  The members differ structurally on every axis
  (kind, set, depth, shape, ticket), so the driver
  would carry adapter hooks nearly as large as
  today's modules while every real change (an
  upstream shape change) still moves exactly one
  module's adapters. Net change obligations
  relieved: zero. The lifecycle is a template with
  bespoke members, and the DRY end-state for a
  template is stated convention, not shared code.

No executable experiments were run: every claim above
rests on full-module reads plus the vocabulary census
(shared-tree grep and `git show` only; no package
import, no workspace copy, no pytest). Nothing was
executed, so no cell verdicts are owed and the
sharded plus pg cells are inapplicable (no database,
alias, or dialect decision anywhere in the rule).

## Findings

Ten sub-rule records. Each carries contract plus
variation, sites plus roles, challenges plus counts,
owner plus lifetime, migration, distinct behavior,
behavioral proof, structural gate, coupling, and
freshness per DRY.md, abbreviated where a field is
vacuous for a rejection. Freshness pins for every
input sit in the System trace table; each finding
names its inputs so Worker-2 can compare. No finding
moves production, tests, or docs: all durable-home
owner files are hunt-dirty, so every clause below is
homed to closeout (Worker-0 transcribes the plan-side
rejection list; the docstring clauses land once the
hunt releases the files).

### F-A `patch-installed-detection` (rejected)

Contract plus variation: each `_patch_is_installed`
answers whether its own module's replacement currently
occupies the upstream slot, derived live from the
class dict plus identity comparison so a reverted
install is re-detected. Varies on descriptor kind
(property, classmethod, plain) and member count (1, 1,
4, 1). Sites plus roles: 4 definitions (cross_web
`:340` property-fget, django `:389` classmethod
`__func__`, strawberry `:909` 4-plain conjunction,
graphql_core `:179` 1-plain); consumers are the 4
`apply()` bodies plus the `test_apps` dispatch and
reload oracles plus the live restore blocks; no
projection owns the derivation. Challenges: upstream
moves its attribute (1 definition per upstream);
cached-flag derivation (count 4, implausible -
breaks the stated self-healing requirement);
namespace-read change for the 5 plain member checks
(count 2, a codemod either way). Owner plus
lifetime: none shared; each probe stays with its
installer (no stored derivation; the live read IS
the lifetime). Migration: none. Distinct behavior:
each probe is the kind-specific mirror of its own
install statement - property install vs classmethod
install vs plain assigns - and the mirror holds by
adjacency in one module. Sharing the probes while
the installers stay per-module would keep kind
agreement by matching call arguments instead of
adjacent code, strictly weaker, relieving no change
obligation. The strawberry 4-member conjunction
additionally owns its partial-install-equals-False
rule, which no other module shares. Behavioral
proof: static-reviewed (no behavior change; the
claim is structural). Structural gate: none owed
for a rejection. Coupling: none. Freshness: the 4
indexed files (dirt: read-migration only) plus
`test_apps.py` and `test_transport_api.py` pins.
Durable-home clause (closeout, per probe docstring):
"kind-mirrored with this module's install
statement; do not share across patch modules."
Trigger: a second patch module sharing BOTH the
same descriptor kind AND the same member shape
whose probe differs only in (owner, name, expected)
- then the kind-probe becomes one rule with 2
definitions; or a semantic change to the identity
comparison itself adopted jointly.

### F-B `patch-upstream-capture` (rejected)

Contract plus variation: each `_captured_upstream_*`
returns the genuine upstream callable for its slot,
recovering the carried original across an in-process
reload when the live slot holds the module's own
prior wrapper. Varies on descriptor-kind slot read
(3 kinds) and recovery predicate (exact-owner x3 vs
exact-or-package-prefix x1). Sites plus roles: 4
definitions (cross_web `:228`, django `:147`,
strawberry `:444`, graphql_core `:60`); consumers
are the module-level `_original_*` captures plus
the validators and retirement probes that read
them; oracle is the `test_apps` double-reload test
(`:204`) pinning capture retention for all four.
Challenges: kind-read change (1, 1, or 2
definitions by kind); recovery-semantics change
(3 plus 1 variant, not 4 - graphql_core `:66`
recovers any `django_strawberry_framework.`-stamped
wrapper while the siblings recover exact-owner
stamps only); new descriptor kind (0 existing).
Owner plus lifetime: none shared; the kind read
plus the predicate stay per module (captures are
import-time values, validity = process lifetime or
until the next reload re-captures). Migration:
none. Distinct behavior: the kind-specific shape
guards are different contracts (property
readability vs classmethod unwrap vs direct slot
read with distinct failure modes), and the
graphql_core prefix arm is an unadjudicated
variant: unstated (the function has no docstring,
unlike its three siblings) and unpinned (the
reload oracle exercises same-module stamps, where
the first disjunct short-circuits; no test installs
a foreign-stamped wrapper). Consolidating the
recovery would first have to bless one predicate,
changing the exotic-case behavior of either 1 or 3
modules with no contract source to decide. That
arm is NOT filed as a defect (no contradicted
contract, no failing behavior); it is the reason
this finding rejects instead of confirming.
Behavioral proof: static-reviewed. Structural
gate: none owed. Coupling: none. Freshness: the 4
indexed files plus `test_apps.py` pins. Durable-home
clause (closeout, per capture docstring):
"descriptor-kind-specific; recovery predicate is
this module's own." Trigger: adjudicate the prefix
arm (test plus document it as deliberate package
policy, or delete it to exact-owner) - if it
unifies to exact-owner, the plain-kind capture
(None guard plus slot read plus exact recovery)
becomes one rule with 2 definitions (strawberry,
graphql_core) and this finding reopens as a
confirmation candidate.

### F-C `patch-stamp-vocabulary` (rejected)

Contract plus variation: the two stamp attribute
names plus the act of stamping a replacement with
(owner, carried original). No legitimate variation:
the 8 literals are byte-identical. Sites plus
roles: 4 spelling sites of the act (3 inline pairs
at cross_web `:336`-`:337`, django `:381`-`:386`,
graphql_core `:171`-`:176`, plus strawberry's
`_mark_patch_replacement` helper `:890` with 4
calls); 8 literal definitions; zero readers outside
the owning module (swept package, tests, scripts).
The 4 `_PATCH_OWNER` values are declarations, not
definitions: each names its own module and moves 1
per module rename by design (intentional identity
separation, recorded here). Challenges: rename the
attributes (forced together 0 as definitions -
within-module agreement is all correctness needs;
4 as convention); stamp a third attribute (count 4
on a change nothing plausibly proposes); add a
fifth module (moves 0 existing). Owner plus
lifetime: none shared; each read/write pair stays
adjacent in its module (stamps live on the
replacement function objects for the process
lifetime). Migration: none. Distinct behavior: a
shared stamper would need a neutral new micro-module
(`conf.py` owns settings, not runtime marking;
sibling-to-sibling import reverses the
one-module-per-dependency rule), and the constants
it would own never change (collision-proof by
namespace), so the abstraction relieves no change
obligation while coupling every module's
retirement story. The fifth-module typo hazard is
real but is addressed by template prose, not by a
shared owner for unchanging strings. Behavioral
proof: static-reviewed. Structural gate: none owed
(the considered gate - asserting all four stamp
names agree - would pin convention, not behavior,
and needs no bespoke existence test per helper).
Coupling: none. Freshness: the 4 indexed files.
Durable-home clause (closeout, per module above
the stamp constants): "package marking
convention, spelled per module; keep the read/write
pair adjacent." Trigger: a real change to the
marking convention (new stamp attribute, rename, or
a cross-module stamp reader such as an audit tool)
that must land identically on all spellings.

### F-D `patch-missing-symbol-sentinel` (rejected)

Contract plus variation: `try` the upstream import,
bind `None` on `ImportError`, refuse the sentinel
before any patch installs or runs. Symbol sets
differ per module (1, 1, 5, 2). Sites plus roles: 4
import blocks (cross_web `:214`-`:220`, django
`:131`-`:139`, strawberry `:415`-`:436`, graphql_core
`:42`-`:52`) plus their None checks in captures,
gates, and probes; consumers are the validators
that refuse the sentinel. Challenges: sentinel
protocol change (count 4 on a deliberate redesign,
no plausible instance posited). Owner plus
lifetime: none shared; each block declares its own
symbols (sentinel validity = import time).
Migration: none. Distinct behavior: no shared owner
can own which symbols exist per upstream; the None
choice is Python idiom, and unifying it would add
import edges for zero change obligation. Behavioral
proof: static-reviewed. Structural gate: none owed.
Coupling: none. Freshness: the 4 indexed files.
Durable-home clause: none owed beyond the existing
per-block comments (already stated at each site).
Trigger: a change to the sentinel protocol itself
(value or check shape) that must land identically
on all four modules.

### F-E `patch-call-time-captures` (rejected)

Contract plus variation: refuse None sentinels at
call time and bundle the proven-present captures
for wrappers that delegate per request. Capture
sets differ (9 fields vs 3); proof predicates
differ. Sites plus roles: 2 definitions
(strawberry `:548`, graphql_core `:88`); consumers
are the delegating wrappers plus the install steps
that read the same bundle the validator pinned;
the 2 modules without the gate (django, cross_web)
are principled absences (no call-time delegation:
django reimplements without calling its original,
cross_web's installed property never calls its
getter per its docstring). Challenges: gate-protocol
change (count 2, but the fields and predicates
follow distinct downstream uses). Owner plus
lifetime: none shared; each bundle stays with its
wrappers (bundle validity = one call; module
globals re-read every call). Migration: none.
Distinct behavior: strawberry must prove its upload
utility is a plain function (`inspect.isfunction`)
because the provenance check reads its code object;
graphql_core needs mere callability. Unifying the
gates would either weaken strawberry's proof or
strengthen graphql_core's without a reader.
Behavioral proof: static-reviewed. Structural
gate: none owed. Coupling: none. Freshness: the 2
indexed files. Durable-home clause (closeout, per
gate docstring): "this module's capture set only;
the proof predicate follows the wrapper's use."
Trigger: a change to the gate protocol itself
(check-then-bundle shape, or a shared capture
record) adopted jointly by both gates.

### F-F `patch-arity-tripwire` (rejected)

Contract plus variation: every patched method keeps
its exact `(self, ...)` arity with all parameters
positional-or-keyword, else installation refuses.
Arities differ per call site (1, 1, 2 x4 in a loop,
6). Sites plus roles: 4 checks (cross_web `:284`-`:291`,
django `:267`-`:274`, strawberry `:606`-`:622`,
graphql_core `:110`-`:121`); consumers are the 4
`apply()` bodies (via the validators); oracles are
the per-module signature-drift fail-loud tests.
Challenges: upstream adds a parameter (exactly 1
validator moves - re-audit is per upstream by
nature); global strictness relaxation (count 4,
rejected - see below). Owner plus lifetime: none
shared; each check stays in its validator (check
validity = one `apply()` call). Migration: none.
Distinct behavior: the strictness carries different
contractual weight per patch kind - the SOLE shape
contract for delegators (cross_web, graphql_core,
strawberry's `parse_json` arm) vs tier 1 of 3 ahead
of the body pin for reimplementers (django,
strawberry's shield arm), stated in both validator
docstrings ("delegators pin the call shape,
reimplementers pin the body"). A shared tripwire
predicate returning bool (messages stay e11's)
would invite a global relaxation that changes what
each per-upstream audit gets to see; the policy
and the per-upstream response cannot be separated.
Same answer today, separate reasons to change
(principle 3). Behavioral proof:
static-reviewed. Structural gate: none owed.
Coupling: e11 owns the 4 then-message wordings of
these checks; this finding touches only the
predicate, and proposes no sharing. Freshness: the
4 indexed files plus the 4 per-module oracle files.
Durable-home clause (closeout, per validator
docstring): "strictness is this patch kind's own;
re-audit stays per upstream." Trigger: a change to
the tripwire strictness that both validator
docstrings adopt jointly as one package policy
(e.g. tolerating keyword-only extras with a
uniform safety argument covering delegators and
reimplementers alike).

### F-G `patch-body-pin` (rejected)

Contract plus variation: a reimplementing patch
reads the superseded upstream body as dedented
source (unverifiable, including a bytecode-only
distribution, means drift, never silent
supersede) and pins it against its audited set.
Varies on data shape (django SET of 2 vs
strawberry single source) and comparison
(membership vs equality). Sites plus roles: 2
read stanzas (django `:275`-`:279`, strawberry
`:623`-`:627`, byte-identical except subject and
operator) plus 3 data definitions (django's 2
bodies `:189`-`:221` plus SET `:218`, strawberry's
source `:510`); consumers are the 2 validators;
oracles are the body-drift and source-unavailable
fail-loud tests plus the django exactly-two-shapes
test. Strawberry's docstring cites django's as the
reimplementer's-contract precedent, which is
already the DRY end-state for the shared
rationale clause ("an unverifiable body must not
be silently superseded", verbatim in both).
Challenges: new `getsource` failure mode (count 2,
implausible - the catch is exhaustive per the
`inspect` contract); normalization change (moves
data too, so the stanza never moves alone).
Owner plus lifetime: none shared for the stanza;
the audited DATA stays per upstream by definition
(data validity = until the next upstream body
change forces re-audit). Migration: none.
Distinct behavior: the comparison operator follows
the data shape, and the only plausible stanza
changes either cannot happen (third exception) or
force per-module data re-pinning anyway. A shared
`upstream_source_or_none` reader would be a 4-line
abstraction over stable idiom in a neutral new
micro-module (strawberry importing the helper from
django's module would couple the production HTTP
patch to the never-retiring test patch - a
reversed dependency). Behavioral proof:
static-reviewed. Structural gate: none owed.
Coupling: the `filters/sets.py` audited-RANGE gate
is the deliberate contrast (version range for
routing vs body set for superseding); no trigger
owed there beyond its own family. Freshness: the 2
indexed files plus the 2 per-module oracle files.
Durable-home clause (closeout, per validator
docstring): "reimplementer's contract; the pin
data is this upstream's own." Trigger: a new
`getsource` failure mode the `inspect` docs add,
or a second body joining strawberry's pin (both
comparisons unify to SET membership - then the
read plus compare becomes one rule with 2
definitions and this finding reopens).

### F-H `patch-apply-order` (rejected)

Contract plus variation: gate, then validate, then
installed-check, then install - uniform across all
4 `apply()` bodies, with django additionally
recording the validated source between validate
and check. No variation in order; variation in
what validate-then-check means per module. Sites
plus roles: 4 orders (cross_web `:358`-`:366`,
django `:436`-`:447`, strawberry `:958`-`:970`,
graphql_core `:189`-`:195`); consumers are `ready()`
plus every per-module test driving `apply()`;
oracles pin validate-before-check (the
signature-drift fail-loud tests mock only the
`_original_*` global while the wrapper is still
installed, so a swapped order would no-op instead
of raising). Challenges: check-before-validate
reorder (count 4, rejected - safety differs per
module). Owner plus lifetime: none shared; each
order stays in its `apply()` (django's recorded
source validity = until the next apply
revalidates, reload-safe by the preserved-global
comment at `:222`-`:239`). Migration: none.
Distinct behavior: django MUST validate on every
apply (the teardown read path depends on the
recorded source); the others revalidate so drift
raises on refire. Identical order, different
load-bearing reasons - 4 rules with identical
current answers, not 1 rule (principle 3). A
shared `run_patch_apply` driver would unify what
must be examined per module while saving no lines
(the install adapters plus docstrings stay
regardless). Behavioral proof: static-reviewed.
Structural gate: none owed. Coupling: none.
Freshness: the 4 indexed files plus the 4
per-module oracle files. Durable-home clause
(closeout, per `apply()` docstring): "validate
before the installed check for this module's own
reason (record vs refire); do not reorder
jointly." Trigger: a lifecycle reorder whose
safety argument holds uniformly - e.g. django's
record moves out of `apply()` - adopted by all
four `apply()` docstrings as one policy.

### F-I `patch-dispatch-set` (single-owned)

Contract plus variation: `ready()` dispatches
exactly the four patch `apply()`s, each
self-gated, each idempotent and self-healing, so
repeated `ready()` calls are safe. Varies only by
membership (add or drop a module). Sites plus
roles: 1 definition (`apps.py::ready`, imports
`:48`-`:51`, calls `:53`-`:56`); consumers are
Django's app loader plus the `test_apps`
dispatch oracle (`:121`); the gate key set plus
gate body in `conf.py` are the coordinated
single-owned companion (pre-existing, untouched).
Dispatch ORDER is not a rule: no install-time
cross-dependency exists (verified: each `apply`
touches only its own upstream symbols), and the
oracle asserts the installed set, not the
sequence. Challenges: membership change (exactly
`ready()` plus the key set move - 2 coordinated
sites, 1 rule); order permutation (moves 0
definitions). Owner plus lifetime: `apps.py::ready`
by responsibility (the dispatcher; its docstring
already states the inventory rule and refuses to
repeat per-module detail). Migration: none owed -
already single. Distinct behavior: none; this is
the family's one confirmation of single ownership.
Behavioral proof: static-reviewed (the dispatch
oracle pins the set; the refire half pins
idempotence). Structural gate: none owed (the
existing dispatch test IS the gate, with real
uninstall-plus-refire failability). Coupling:
none. Freshness: `apps.py` (clean pin) plus
`test_apps.py` and `conf.py` pins. Durable home:
already stated at the owner; no clause owed.

### F-J `patch-retirement` (rejected)

Contract plus variation: each module documents its
upstream defect's status, how to re-check whether
upstream fixed it, and (for 2 of 4) an executable
probe over its captured original; the module is
deleted outright once its defects all retire.
Varies on upstream ticket, release range,
permalink, probe subject, and probedness. Sites
plus roles: 3 retirement sections (cross_web
"Upstream status" plus "Re-checking", strawberry
"Upstream status" plus "Re-checking" plus "Three
lifecycles", graphql_core status plus retirement
line) plus 1 wontfix note (django: no retirement
event exists); 2 executable probes (cross_web's
getter probe, strawberry's gap probes); projections
only beyond that. Challenges: upstream fixes the
defect (exactly 1 module moves; forced together
0 across 4 repositories). Owner plus lifetime:
none shared; each retirement story stays with its
defect. Migration: none. Distinct behavior:
probedness differs by defect nature, not by
thoroughness - cross_web's uninstalled state
discriminates live (uninstalled-400 means
retirable, pinned by the cross_web-half row),
while strawberry gap 1 has no live diagnostic
(every fakeshop body row posts to a package view
whose strict decode answers first, as its
docstring states). The shared section template is
prose convention, and projections never own. The
joint strawberry plus cross_web ownership prose
(2 module docstrings plus the gate comment) is
the same category: 3 prose definitions of one
coupling contract with live rows pinning the
behavior; single-sourcing it is editorial, not a
consolidation, and every home is hunt-dirty.
Behavioral proof: static-reviewed. Structural
gate: none owed. Coupling: none (retirement
deletes code; it couples to no other finding).
Freshness: the 4 indexed files plus
`test_transport_api.py` and `test_products_api.py`
pins. Durable-home clause (closeout, per module
docstring status section): "retires on this
module's upstream ticket alone." Trigger: a
second module retiring on the SAME upstream
ticket (one shared retirement event) - then the
retirement decision becomes one rule with 2
definitions.

## Defects

None found. Two examined-and-cleared notes (not
defects, recorded so closeout need not re-derive
them):

- The graphql_core package-prefix recovery arm
  (`:66`) is unstated and unpinned but not
  demonstrably wrong: no contract contradicts it
  and no behavior fails because of it. It is homed
  in F-B as the reason that finding rejects, with
  the adjudication trigger. Filing it as a defect
  would assert a bug where only an unexplained
  variant exists.
- graphql_core's capture (`:60`) and probe (`:179`)
  carry no docstrings while their six siblings do.
  Style inconsistency only; no contract broken;
  out of scope (and the file is hunt-dirty).

Ticked-row fact check (per the drift binding;
reopens nothing): plan rows 336-337 claim both
families span exactly the four indexed files -
CONFIRMED by the whole-package sweep (no fifth
module). The file-local rows for `_cross_web`,
`_django`, and `_graphql_core` (property-descriptor
handling, classmethod-descriptor spelling,
plain-method spelling, the two-body audited set,
the delegation-vs-reimplementation rejections)
were spot-checked against HEAD bytes; no factual
errors found. No finding is owed to closeout
homing.

## Judgment

The upstream-patch lifecycle is a template, not a
rule: four modules follow the same shape
(capture, validate, install, probe, retire) while
every member encodes a per-module contract. Nine
sub-rules reject with contract differences plus
triggers; the tenth (dispatch set) was already
single-owned. The sibling wording family (e11)
keeps the 11 refusal messages; this item never
counts or proposes sharing them. Zero tracked
files changed, zero tests added, zero
`## Owned changes` rows owed. Durable-home clauses
for the nine rejections are specified above and
homed to closeout. No execution was performed;
type gates and ruff are vacuous on a zero-edit
verdict (no `.py` path touched; this artifact is
untracked per-cycle scratch).

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (only the
`### F-*` headings were listed for structure, plus
`Status:`/`Run:`/`## ` lines; no finding body read).
Headings seen: F-A installed-detection, F-B capture,
F-C stamp-vocabulary, F-D missing-symbol-sentinel,
F-E call-time-captures, F-F arity-tripwire, F-G
body-pin, F-H apply-order, F-I dispatch-set, F-J
retirement.

### Own trace: sites + roles

Population (HEAD `5c3496e0`, WT = dispatch pins,
re-verified below): exactly four `_*_patches.py`
modules (`ls` census; no fifth), plus
`conf.py::upstream_patches_enabled` +
`UPSTREAM_PATCH_DEPENDENCIES` (gate owner) and
`apps.py::ready` (dispatcher). Importer census
(package-wide grep): production importers are
`apps.py` (four `apply` imports) and
`testing/_wrap.py` (imports only the
`_is_database_failure` predicate, not lifecycle);
every other importer is a test/oracle
(`tests/test_*_patches.py`, `tests/test_views.py`,
`tests/testing/test_wrap.py`,
`test_query/test_transport_api.py`) or a docstring
probe snippet. No second production dispatcher.

Roles: each patch module = candidate authoritative
definition of its lifecycle members; `conf.py` =
definition of the gate rule (the four
`if not upstream_patches_enabled("<dep>")` lines
are consumers composing by name); `apps.py::ready`
= sole enforcement site of the dispatch set;
module docstrings = projections (retirement prose,
re-check probes); tests = oracles (never read the
owner they check: gate tests spell literals, patch
tests restore upstream by identity).

### Own decomposition (10 members, blind)

W2-A capture-with-sentinel (`try/except ImportError`
+ `None` drift sentinel): 4 sites, symbol sets
1/1/5/2. Posit "add a sixth strawberry symbol":
only `_strawberry_patches.py` moves. Count 1 per
change; the shared residue is the `None`-means-drift
convention, not a rule. Verdict: reject.

W2-B reload-retaining capture (`_captured_upstream_*`):
4 sites, descriptor-kind-specific unwrap (property
fget / classmethod `__func__` / plain-method x4 via
`(owner, name)` helper / plain-method + sibling-owner
prefix acceptance). Posit "upstream switches body to
a plain method": only cross_web's capture moves.
Count 1. Verdict: reject.

W2-C owner/original stamps (two attribute-name
literals + per-module `_PATCH_OWNER` value): the
strongest candidate - the two literals are
byte-identical in all 4 modules, so "rename the
attribute" touches 4. BUT each module docstring
records independent retirement-by-deletion as the
organizing rule (strawberry even keeps
`_UPSTREAM_JSON_PARSE_REASON` un-imported to stay
"importable (and deletable)"); a shared stamp-constants
home would couple four independently-deletable
modules. The graphql_core sibling-prefix acceptance
shows the protocol is cross-module by recognition,
not by shared definition. Verdict: reject as an
intentional separation, trigger = modules no longer
required to be independently deletable.

W2-D validation depth (`_validate_upstream_shape`):
4 sites, two depths - delegators pin call shape only
(cross_web 1-arg, strawberry 2-arg x4, graphql_core
6-arg), reimplementers also pin body source (django
a two-body SET, strawberry ONE body). Posit "upstream
adds a parse_json parameter": only strawberry moves.
Posit "Django 6.2 changes the teardown body": only
django's audited set moves. Count 1 per change.
Verdict: reject (two sub-contracts, each per-module).

W2-E call-time captures tuple (`_UpstreamCaptures`):
2 sites (strawberry 9 fields, graphql_core 3 fields),
different refusal predicates (strawberry demands
`isfunction` for the utility; graphql_core demands
`callable`). cross_web/django validate inline instead.
Posit "harden the utility check": only strawberry
moves. Count 1. Verdict: reject.

W2-F installed-detection (`_patch_is_installed`):
4 sites, descriptor-kind + member-count specific
(property-fget-identity / classmethod-`__func__` /
4-method conjunction / plain-method identity).
Posit "strawberry gains a fifth patched method": only
its conjunction moves. Count 1. Verdict: reject.

W2-G apply skeleton (gate -> validate -> installed? ->
assign): 4 sites share the ORDER, but each install
step is descriptor-kind-specific (`property(...)`
wrap / `classmethod(...)` wrap / 4 plain assigns / 1
plain assign via captures) and the gate + validate +
installed-check are each owned elsewhere/per-module.
The 0.0.11 scaffold note is prior record, not
evidence; re-derived: a shared driver would need
per-module install adapters for exactly one caller
each = machinery, no change obligation relieved
(posit "cross_web needs a pre-install flush": the
driver gains a branch no other member reaches).
Verdict: reject.

W2-H gate call (`if not upstream_patches_enabled(...)`):
4 call sites, ONE definition in `conf.py` (already
owned; `ValueError` on unknown names keeps the
vocabulary single-sourced with `UPSTREAM_PATCH_DEPENDENCIES`).
Count 1. Single-owned, no finding.

W2-I dispatch set (which appliers `ready()` calls):
ONE site (`apps.py::ready`, 4 calls; census above
finds no second dispatcher). Count 1. Single-owned,
no finding.

W2-J retirement (probes + prose): 4 per-module
projections (sync-decode probe / Trac wontfix record /
three-lifecycle probes / executor probe), each naming
its own upstream defect + version + permalink. Posit
"cross-web 0.7.1 fixes the decode": only that module's
prose moves, and the module deletes outright. Count 1.
Verdict: reject (projections, not definitions).

Owner choice: NONE - no consolidation; every member
is per-module contract or already single-owned.

### Matrix (own discharge)

1. Cross-flavor: the four modules ARE the flavors;
swept package-wide for a fifth module / second
dispatcher / extra gate call site: none found.
2. Sync/async twins: the only twin pair (strawberry
multipart delegates) is patched BEHAVIOR installed by
one apply, not lifecycle; the lifecycle itself is
sync-only with no twin.
3. Derived knowledge: gate keys derive from
`UPSTREAM_PATCH_DEPENDENCIES` (single-owned,
`ValueError`-guarded); refusal messages restating keys
belong to e11, excluded here.
4. Round-trip: no production uninstall exists (tests
restore by identity); no pair to unify.
5. Other media: docstrings project, tests check; no
contract restated as a second definition.
6. Omission: every module carries capture + validate +
installed-check + apply + stamps; the captures-tuple
"absence" in cross_web/django is a different
validation shape, not a missing enforcement (no
contract source requires the tuple).

### e11 boundary (own)

`raise RuntimeError` census: cross_web 3, django 4,
strawberry 3, graphql_core 2 = 12. Django's 4th
(`_disallowed_connection_methods` "ran without a
validated upstream body") is a teardown-time guard,
not an install refusal - so install refusals = 11,
matching the plan's "11 raise sites". Lifecycle vs
wording separates cleanly: this item owns shapes and
counts, e11 owns message text; the teardown guard is
the one site to watch for silent dropping (it is
neither install-refusal nor lifecycle-template).

### Cells + gates (own, pre-read)

Lifecycle path (import capture, apply-time validate,
setattr install) reaches no database, alias, or
dialect decision - the django module's `connections`
iteration is patched teardown BEHAVIOR, not the
lifecycle under review, and zero-edit changes no
behavior under any cell. Expectation: sharded/pg
`inapplicable by construction` is acceptable IF W1
states the reason. Gates: no `.py` touched means
ruff-on-touched-paths is vacuous; e8/e9 precedent
re-ran whole-package gates and recorded tree-state -
W2 will do the same for comparability.

Fingerprints (own): WT `16c05c78` / `5ca5493f` /
`ec492674` / `2d1dd0cd`, HEAD `e5a69a55` / `20bfb1f8` /
`aa08b628` / `8ede2487` - all match dispatch pins;
HEAD still `5c3496e0`; item diff vs ITEM_BASELINE is
the plan edit alone.

### Reconciliation (after reading `## Findings`)

Blind decomposition converged 10-for-10 with W1's
F-A-F-J (mine split validation as one member W2-D;
W1's F-F/F-G split is finer and better; my W2-G
skeleton maps to F-H order plus F-A's
installer/probe mirror argument plus the maximal
driver). Every difference reconciled:

- F-A: ENDORSE. Re-derived: 4 probes, 5 plain
member checks across 2 modules; kind+count
contract difference confirmed from full reads.
Trigger (second module sharing kind+shape) exact.
- F-B: ENDORSE. The 3+1 variant re-derived
independently (prefix arm read at `:64`-`:68`);
W1's sharper sub-claims verified: capture has no
docstring (full read), reload oracle exercises
same-module stamps only
(`test_apps.py:204`-`:259` - reloads each module
under its own installed replacement, never a
foreign-stamped wrapper). Trigger (adjudicate the
arm; exact-owner unification reopens as a
2-definition confirmation) is concrete and
correct. Examined-and-cleared (not a defect):
agreed, no contradicted contract.
- F-C: ENDORSE. Byte-identical literals confirmed;
zero cross-module readers confirmed by own grep
(4 hits, all inside the owning modules). Framing
differs (W1: 0-as-definitions/4-as-convention +
adjacency; W2-blind: deletability separation) -
compatible, W1's more precise. Trigger exact.
- F-D: ENDORSE. Symbol sets 1/1/5/2 plus
django's unconditional SimpleTestCase import
confirmed from reads. No clause owed beyond
existing comments: agreed.
- F-E: ENDORSE. 9-vs-3 fields and
`isfunction`-vs-`callable` predicates confirmed;
principled absence (django reimplements,
cross_web never calls its getter per docstring)
confirmed. Trigger exact.
- F-F: ENDORSE. Arities 1/1/2x4/6 confirmed;
delegator-sole vs reimplementer-tier-1 weight
confirmed in both validator docstrings. e11
coupling for message text correctly noted.
- F-G: ENDORSE. Read stanzas verified
byte-identical except `getsource` subject and
`not in` vs `!=` by direct comparison. Data
per-upstream; reversed-dependency argument
(strawberry must not import from django's
module) sound. Trigger (second strawberry body
unifies to SET x2) exact.
- F-H: ENDORSE. Uniform order + django record
confirmed; the load-bearing oracle claim
spot-verified
(`test_cross_web_patches.py:180`-`:182` mocks
only `_original_body_fget` while installed, so
a swapped order would no-op instead of raise).
Install-shape differences live in F-A's mirror
argument + F-H's "adapters stay regardless" -
adequate; no gap. Trigger exact.
- F-I: ENDORSE. Census re-derived independently:
sole dispatcher, 4 calls, no second production
site (importer grep); set-not-sequence oracle
confirmed (`test_apps.py:121`-`:179` asserts
the 4-tuple, refire included). Already
single-owned; existing test is the gate.
- F-J: ENDORSE. 3 sections + wontfix note +
2 probes confirmed from reads; probedness
difference confirmed (cross_web-half live row
exists; strawberry gap-1 no-live-diagnostic
stated in its docstring). Joint-ownership prose
triplication correctly classed projection.
Trigger (shared retirement ticket) exact.
- Maximal driver: ENDORSE rejection as
machinery (zero change obligations relieved) -
matches W2-blind W2-G.
- e11 exclusion: ENDORSE. 11 refusal decision
points re-derived (3+3+3+2); message text
never counted here. The teardown guard
(django's 4th raise) is NOT dropped between
items: it is homed at plan row 344
(`_disallowed_connection_methods`, file-local).
- Closeout homing: ACCEPTABLE. All four owner
files hunt-dirty (status + pins re-verified),
so owner-site clauses are barred edits; each
clause names its docstring site + exact text
and is landable later. F-D correctly needs
none.
- Ticked-row check: ENDORSE. Rows 336-337
re-read directly (both families span exactly
the four files). Own file-local sample: row
340 (property kind unique to cross_web),
row 343 (two-body set read in full), row 345
(classmethod unique to django) all true; row
349's plain-method spelling has its second
site in strawberry, which is exactly F-B's
adjudicated pair (now a rejection with
trigger) - consistent, no factual error.
- `## Pending execution` absent: CORRECT. All
proofs `static-reviewed`, zero-edit, no
behavior changes hands; nothing deferred.
- Matrix: ENDORSE on all six axes; W2-blind
discharge converged independently (only twin
is subject-matter inside one module; no
uninstall half; captures-tuple absence is
principled, no contract source demands it).
- Enumeration counts: every headline count
re-verified against full-module reads (8
stamp literals, 4+4 captures/predicates,
2 gates, 4 validators, 3 body-data defs,
4 stampings, 4 probes / 7 member checks,
4 apply, 4 gate calls, 4 dispatch calls,
4 sentinel blocks / 9 symbols, 3+1
retirement sections). No member unhomed.
- Structural gates: none owed for rejections
per DRY.md; F-I's dispatch test has real
revert-plus-refire failability. Correct.
- Freshness: indexed pins match W2's own
hashes exactly (12-hex); `apps.py` clean pin
`64e82ce1e9e7` re-verified; HEAD-vs-WT dirt
map spot-confirmed (`__dict__.get` at HEAD
vs `truth.class_dict` in WT;
"delegating siblings" HEAD wording).
Exclusion pins accepted: W2 re-derived the
no-fifth-site verdict via independent sweeps
(`ls` census, importer grep, gate-call census).
- Zero-edit: CONFIRMED. No `## Implementation`;
4/4 WT pins match dispatch pins; item diff vs
ITEM_BASELINE is the plan edit alone; HEAD
unmoved at `5c3496e0`.
- Cells: W1's `inapplicable` (no database,
alias, or dialect decision in the rule)
JUDGED SOUND - the lifecycle path is
import-capture plus apply-time validate plus
setattr; the django `connections` iteration
is patched teardown behavior, not the rule,
and zero-edit changes nothing under any
cell. W2 performed no execution either
(static census only; shared venv unused for
probes, used only for gates below).
- Defects: W2 found ZERO; the two
examined-and-cleared notes verified (prefix
arm unstated+unpinned confirmed above;
missing docstrings confirmed by full read).
Nothing to file under `## Defects`.
- Gates (W2 re-ran whole-package per e8/e9
precedent, shared project venv via `uv run`):
`ruff check` All checks passed;
`ruff format --check` 119 files formatted;
`mypy` clean 119 files; `basedpyright`
0/0/0. Tree-state matches the plan
baseline. W1's vacuous-gates claim is
accepted as consistent AND superseded by
these green runs.

Verdict: `verified` (plain - no `proof:`
remains, no `## Pending execution`). No
revision candidate: the independent search
for a real consolidation (stamp literals,
captures tuple, arity predicate, body-pin
reader, apply driver) found each either
already single-owned or blocked by a
per-module contract difference W1 states
exactly. No W1/W2 disagreement stands.
