# DRY review: `auth/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights). Audits the UNASSIGNED remainder
of the `auth/` folder and the families that cross its ownership boundaries
at current bytes (HEAD `23b5f421` + working tree). The four member file
artifacts are inputs, not verdicts: every assignment below was re-derived
fresh, and every assignment the tree has falsified is flagged as a finding
inside this item. No prior artifact is summarized.

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da` (detached, intended).
`ITEM_BASELINE=085c1d78ebe98f76a3925d6499e9d11440ff98a2` (resolves to a
commit; its four auth blobs equal the working tree, so BASE=WT for all
four targets and BASE=WT=HEAD for the two clean files).

| Target | WT | HEAD | ITEM_BASELINE | State |
|---|---|---|---|---|
| `auth/__init__.py` | `2e480818` | `2e480818` | `2e480818` | clean |
| `auth/mutations.py` | `217c6bff` | `c5be5fe9` | `217c6bff` | dirty |
| `auth/queries.py` | `b0c60920` | `b0c60920` | `b0c60920` | clean |
| `auth/sessions.py` | `6e5fadb7` | `1dc65564` | `6e5fadb7` | dirty |

Full blobs: WT init `2e480818424d4b130e613e3e2da027aaad7144ad`,
mutations `217c6bff744a8b5d8a573dee69dd29031254f224`, queries
`b0c60920eb9db4d8533fe5f29e86093dd81705fc`, sessions
`6e5fadb7afc1cf23d3e7f9dd76ae30e5f9d92f65`; HEAD mutations
`c5be5fe9241e9059dd6307718a053b32a76bffa3`, HEAD sessions
`1dc65564699d5730bb3666989fa5931bc3d8ef6e` (init/queries identical).
WT line counts: init 20, mutations 1511 (HEAD 1594), queries 148 (HEAD
148), sessions 293 (HEAD 385).

## System trace

The folder owns the package's opt-in session-auth surface: four field
factories (`login_mutation`, `logout_mutation`, `register_mutation` in
[auth-mutations][auth-mutations], `current_user` in
[auth-queries][auth-queries]), re-exported by the 4-name leaf manifest
[auth-init][auth-init]; the transport classification + capability boundary
[auth-sessions][auth-sessions] the login/logout state machines build on;
and the surface-keyed phase-2.5 bind (`bind_auth_mutations`) the
finalizer runs before `bind_mutations`. Everything else is composed by
name from outside the folder: declaration mechanics from
[mutations-sets][mutations-sets], payload/input builders from
[mutations-inputs][mutations-inputs], authorization + envelope leaves from
[mutations-resolvers][mutations-resolvers] and [utils-errors][utils-errors],
request resolution from [utils-permissions][utils-permissions], the sync
boundary from [utils-querysets][utils-querysets], scope/session primitives
from [utils-sessions][utils-sessions], the clear bus from
[registry][registry], and the bind slot from [finalizer][finalizer].

Population at WT (`ast.parse`, `len(ast.Module.body)`): init 4 statements
(docstring + 2 imports + `__all__`, 0 defs); mutations 74 statements, 33
defs (1 class + 32 functions); queries 19 statements, 2 defs; sessions 27
statements, 9 defs (1 enum + 8 functions). Connected sources read in full
or at the cited bodies: all four targets, the finalizer phase-2.5 window,
and each owner body named in the census below. Searched population for
second sites: the whole package (`django_strawberry_framework/`), the
`tests/auth/` oracles, the live fakeshop auth API suite, and the consumer
`accounts/schema.py`.

### Attribution of the working-tree dirt (by diff content vs HEAD)

The two dirty files carry three provenances, distinguished per hunk.
Ledgered DRY work (Run-7 e1, `awaitable-refusal-and-disposal`):
`auth/mutations.py` composes `_disposed_awaitable` (import + call site),
`_close_unawaited` deleted, `contextlib`/`inspect` imports dropped.
Concurrent bug-hunt work (truth migration, hostile-guard deletions,
`except`-arm narrowings, `_safe_*` removals, message-table collapse):
every `truth.*` read and cast, the `_authenticated_actor_or_none`
hostile-shape deletion, the `except BaseException` -> `except Exception`
narrowings plus `suppress`-arm deletions in the four critical sections,
the `classify_transport` / `require_session` / `_require_mutable_scope` /
`scope_session_lock` / `uses_signed_cookie_sessions` rewrites, and the
`ScopeSingletonMessages` 4-field -> 1-field collapse. Unattributed
external concurrent work (neither ledgered nor hunt-shaped, behavior
status noted per hunk): the bespoke `_SealedAuthHolderMeta` seal-class
deletion replaced by the `_SealedAuthHolderMeta = DjangoMutationMetaclass`
alias (+ `DjangoMutationMetaclass` import + comment rewrite, hunks
`@@ -61`, `@@ -250`, `@@ -265`); prose-only comment rewrites (family
label, ledger row, two spec-046 citations, UNSET-password note). No hunk
was edited, reverted, or tidied by this item.

Consequence: any consolidation touching a hunt-dirtied line is
blocked-on-hunt (recorded per finding with its hunk, touching nothing);
the seal-alias lines are unattributed external work (reported to Worker-0
for reconciliation, touching nothing). All counts below are re-derived at
WT bytes; where WT and HEAD disagree the finding states both.

## Verification

### Matrix

Each axis discharged folder-wide against the targets' real WT surface.
A second site for any folder rule was swept package-wide, not just among
the four files.

**1. Cross-flavor policy mirroring.** The folder's deliberate non-mirrors
were re-checked: read-vs-mutation envelope split (`me` returns the user
type directly, mutations return envelopes) holds at WT (queries factory
still builds the nullable alias ref, no envelope ctor); logout-only
schemas still bind with no user type (bind still surface-keys on
`user_typed`); register still rides the write skeleton
(`run_write_pipeline_sync` call intact). Shared machinery is still shared
by call at every site swept: declaration path, field seam, bridge,
anonymity definition, gate, lazy ref, family label, error leaves,
storability preflight, scope/session primitives. No flavor-local
re-spelling found. One index gap: `one-sync-boundary` files-covered names
`auth/mutations.py` but not `auth/queries.py`, which reaches the boundary
through the imported bridge (the run-7 W2 ruling, still unapplied).

**2. Sync/async twins.** Four twin pairs live in the folder at WT: login
bodies, logout bodies, register rider entries, and the `me` sync body +
shared bridge. Each pair was compared by behavior, not shape: the login
and logout pairs carry native per-transport awaits (`channels.auth` +
session persistence) with no sync counterpart; the register pair runs one
sync body in one boundary (no native async work exists); `me` rides the
shared bridge because reads perform no per-transport awaits. No pair
shares a body that could drift silently, and no new twin appeared since
the file items. The Django/Channels establish/teardown pairs are likewise
twins on await points with per-transport compensation bodies (login arms
flush, logout arms anonymize-only). All separations justified under
principle 5; see rejections R-F1 and R-F2.

**3. Derived rather than repeated knowledge.** Every shared derivation is
consumed by call or by imported constant at WT: the family label (1 const,
6 reference sites), the alias/module-path constants (1 literal each, 2
consumers each), the declaration key (1 rule), the dispatch seam (1 seam,
3 consumers), the bridge (1 def, 1 consumer), the anonymity classifier (1
def, 2 consumers), the transport prologue (1 def, 2 prologues), the
capability predicates (1 def each), the error leaves (direct imports, no
`resolvers.` re-spelling at either state), the storability preflight (1
owner, 2 call groups). The `ScopeSingletonMessages` collapse (4 fields to
1) happened in the owner, not here; this folder's one wording composes the
surviving field. No second spelling of any folder rule found.

**4. Inverse / round-trip pairs.** Three pairs: the alias-namespace
materialize/clear trio (materialize consumed by the bind, clear by the
pre-bind bus row; no `setattr`/`delattr` in code at WT); the declaration
register/clear pair (driver-owned mechanics over the disjoint auth store;
both ledger re-records identity-deduped); the login establish/compensate
and logout teardown/failure pairs (each critical section pairs its
mutation with its compensation inside one function). No hand-rolled second
half exists for any of them. The seal-alias change removed one half of a
formerly claimed pair (F6 head); recorded under FF-2, not here.

**5. Contracts restated in another medium.** Production + spec-040
(Decisions 3/5/7/8/9, edge table, D-directives) + independent oracles
(`tests/auth/` unit suites, live fakeshop auth API rows, SDL pins) +
projections (module/factory/body docstrings, consumer schema, READMEs).
Oracles were checked for independence, not re-run: the enumeration guard
spells the literal, the denial pins spell their strings, the dispatch
spies pin boundary counts, the alias test asserts identity by literal
attribute name. Hunt rewrote the hostile-shape oracles to propagation
pins; that media migration is concurrent work, and the folder's remaining
oracle pins still read the behavior, not the owner. Counts below count
definitions only.

**6. Enforcement by omission.** Swept the folder's guard surface member by
member at WT: every fixed field declares through the conflict-checked
path; every resolve path runs its gate (login/logout with their data
shapes, `me` gate-first with `instance=actor`); both login/logout
prologue paths enforce capability before authentication; both critical
sections compensate fail-closed; register validates + hashes before the
shared tail. Deliberate omissions each carry a contract source: no
transport prologue for `me`/register (spec edge table), no `get_queryset`
re-run anywhere in the folder (actor-not-lookup; zero `get_queryset`
code hits in all four files), no envelope for `me` (Decision 7), no
relation-visibility helper on the rider (D-N3, inherits the shared
decode). No member lacks a guard its contract requires. No defect.

### Enumeration

Folder population census (instrument: `ast.parse` per file, counts in
System trace): 124 top-level statements, 44 rule-bearing defs (1 snapshot
class, 1 enum, 42 functions) plus 18 module-level constants/ledgers/rows.
Assignment map (every rule-bearing member lands in exactly one home;
challenges below end in the same homes):

- Cross-boundary CONFIRM (single owner outside, folder composes by call):
  awaitable disposal (1 call site), sync boundary (6 call sites),
  actor lease + lock order (1 holding site), clear-bus rows (2 rows),
  soft-dependency guard (1 wrapper), error leaves (4 call sites),
  async dispatch (1 seam read), session primitives (4 compositions),
  storability preflight (2 call groups), request resolution (4 call
  sites), declaration mechanics (driver), input/payload builders (5
  compositions), write skeleton + model steps (3 compositions),
  directives validator (1 call site), deadline check (1 call site).
- Cross-boundary COUNT-2 STANDS (family-verified mirror): primary
  split (`_resolve_user_primary_or_raise` vs `_resolve_primary_type`).
- Falsified-at-current-bytes (flagged, see Findings): F6 head seal
  (bespoke class gone at WT), F12 hostile-shape list (rewritten by
  hunt), `errors-auth-resolvers-spelling` D1 (zero sites at both
  states), queries member count (15 -> 19, annotation-only growth).
- Folder-local CONFIRM (named as index rows for Worker-0): leaf
  manifest, structural opt-in, sessions privacy, family label, failure +
  capability wordings, register tables, declaration key + synthesis,
  field seam + bridge, anonymity classifier (WT contract), login/logout
  prologues, payload ctors, critical-section twins, resolve-body twins,
  factories, register derivation + steps + rider, phase-2.5 bind, `me`
  resolve contract, `me` factory wiring, alias identity, transport
  classification, scope lock, missing-session pre-check, capability
  answers (23 rows).
- Folder rejections (new, with triggers): R-F1..R-F7 below.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only (consumers, oracles, projections listed in
Findings, never counted). State is WT unless noted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | awaitable disposal | cancel futures too | 1 (owner; auth follows by call) | CONFIRM consolidated |
| C2 | sync boundary | change the worker | 1 (utils owner; 6 sites follow) | CONFIRM consumer |
| C3 | lease + lock order | change order | 1 (lease owner; one holding site) | CONFIRM |
| C4 | clear rows | add a phase | 1 (bus; 2 rows re-declare flags) | CONFIRM |
| C5 | primary split | change get->types_for | 2 (generic + auth; 1 wording each) | STANDS (family-verified) |
| C6 | slot seal | change seal behavior | 2 shapes (record vs snapshot) | REJECT family (mirror) |
| C7 | head seal | change seal behavior | 1 at WT (aliases generic; HEAD 2) | FALSIFIED (FF-2) |
| C8 | family label | respell the label | 1 (const; 6 sites by reference) | CONFIRM file-local |
| C9 | failure message | reword or branch it | 1 (const; oracle lists literal) | CONFIRM file-local |
| C10 | conflict key | admit a kwarg | 1 (auth-local rule) | CONFIRM file-local |
| C11 | dispatch seam | new executor mode | 1 (seam; write entries unaffected) | CONFIRM file-local |
| C12 | anonymity | change classification | 1 at WT (single fn; see FF-3) | CONFIRM shape, FLAG rewrite |
| C13 | prologue order | insert a step | 1 per prologue (3 prologues) | CONFIRM file-local |
| C14 | payload ctors | change a shape | 1 per ctor (3 ctors) | CONFIRM file-local |
| C15 | compensation | log instead of chain | 2 per pair (login, logout) | twins, REJECT merge |
| C16 | resolve contract | change login-vs-logout | 1 per surface (pairs are twins) | twins, REJECT merge |
| C17 | register steps | change hash/validate | 1 per step | CONFIRM file-local |
| C18 | bind keying | add a 5th surface | 1 (bind owns keying; slot outside) | CONFIRM file-local |
| C19 | alias spelling | rename the alias | 1 (const; bind imports it) | CONFIRM file-local |
| C20 | transport classify | new transport | 1 (single classifier) | CONFIRM file-local |
| C21 | scope lock | change the primitive | 1 (helper; owner trio intact) | CONFIRM file-local |
| C22 | capability | new engine rule | 1 per predicate | CONFIRM file-local |
| C23 | `me` gate order | reorder gate/null | 1 (resolve body) | CONFIRM file-local |
| C24 | leaf manifest | 5th factory | 1 (home def; 2 rows follow) | CONFIRM file-local |

## Findings

`Migration: none` and `Coupling: none` throughout (zero-edit folder
audit; nothing consolidates, nothing lands together) — stated once here,
not per finding. Proofs are `static-reviewed` throughout (import moves,
bodies composed by name, single spanning reads, grep-verified absences
over the 4-file population); ordering/transactional/async behavior rests
on the named pre-existing oracles, which this item neither weakens nor
re-runs. No finding carries an `execution-deferred` proof.

### FC-1 — awaitable disposal composition (CONFIRM consolidated)

- **Contract + variation.** A refused awaitable is released without being
  awaited (coroutine closed, future cancelled, other awaitables ignored).
  Varies only in the per-kind protocol.
- **Sites + roles.** *Definition*:
  [utils-querysets][utils-querysets]`::_disposed_awaitable` (exists once
  at WT and HEAD). *Consumer here*:
  [auth-mutations][auth-mutations]`::_authenticated_actor_or_none` (one
  call site; the two inline detect-then-dispose copies plus
  `_close_unawaited` are gone at WT). *Oracles*: hostile-awaitable
  collapse tests + the run-7 e1 oracles. *Projections*: the consumer
  docstring's disposal paragraph.
- **Challenges.** C1 → 1.
- **Owner + lifetime.** Indexed family owner; no stored derivation.
- **Behavioral proof.** `static-reviewed`. Rejects "auth holds a second
  disposal body" (zero `close()`/`cancel()` spellings remain in the
  folder; the import + call compose the owner by name).
- **Structural gate.** The family e1 oracles (pre-existing, in tree).
- **Freshness.** auth-mutations WT `217c6bff` / HEAD `c5be5fe9`;
  utils-querysets WT `e6660894`. Blocked-on-hunt note: the surrounding
  function body is hunt-rewritten (FF-3); the disposal call line itself
  is the ledgered e1 composition, verified intact inside the hunt hunk
  `@@ -552,75 +507,30`.

### FC-2 — sync-boundary consumers (CONFIRM + index gap)

- **Contract + variation.** Every async surface needing sync ORM work runs
  it in one `sync_to_async(thread_sensitive=True)` worker. No local
  variation.
- **Sites + roles.** *Definition*:
  [utils-querysets][utils-querysets]`::run_in_one_sync_boundary` (once at
  both states). *Consumer sites here (by call)*: `_sync_bridged_async_body`
  (1), `_login_resolve_body_async` (2 arms), `_logout_resolve_body_async`
  (2 arms), rider `resolve_async` (1); [auth-queries][auth-queries]
  reaches the boundary indirectly through the imported bridge. Zero
  `sync_to_async` spellings in the folder (grep over all four files).
- **Challenges.** C2 → 0 here (1 at the owner).
- **Owner + lifetime.** Indexed owner; no stored derivation.
- **Behavioral proof.** `static-reviewed` (call sites name the owner).
- **Structural gate.** The dispatch-spy tests (pre-existing).
- **Index gap for Worker-0.** The `one-sync-boundary` files-covered list
  still names `auth/mutations.py` without `auth/queries.py`; the queries
  bridge call (queries WT line 134) makes it a genuine indirect consumer.
  Correction owed: insert `auth/queries.py` after `auth/mutations.py`.
- **Freshness.** All four targets as pinned; utils-querysets WT `e6660894`.

### FC-3 — lease holding + clear rows (CONFIRM)

- **Contract + variation.** The actor lease serializes revalidation
  checkpoints against package-owned transitions (scope lock OUTER, lease
  INNER at the one site holding both); every subsystem registers teardown
  on the clear bus with a stable owner + phase flag.
- **Sites + roles.** *Definitions*: [utils-sessions][utils-sessions]
  `::actor_transition`/`::actor_lease` and [registry][registry]
  `::register_subsystem_clear` (each once at both states). *Holding site
  here*: `_channels_logout` (`scope_session_lock` OUTER at WT line 964,
  `actor_transition` INNER at WT line 969 — order intact). *Bus rows
  here*: `owner="auth.declarations"` full-clear-only (mutations WT line
  206, no flag) and `owner="auth.current_user_alias"` pre-bind (queries
  WT lines 76-80, `before_bind=True`).
- **Challenges.** C3, C4 → 1 each at the owners.
- **Owner + lifetime.** Indexed owners; lease is per-scope runtime state.
- **Behavioral proof.** `static-reviewed` (order + flags read off the
  bodies; prose verified verbatim at both ends).
- **Structural gate.** Revalidation + logout-interaction tests and the two
  ledger-drain tests (pre-existing).
- **Freshness.** auth-mutations WT `217c6bff`; auth-queries `b0c60920`;
  utils-sessions WT `de3cf2c9`; registry WT `c5aa2050`.

### FC-4 — primary-split mirror (STANDS, family-verified)

- **Contract + variation.** "What counts as the registered primary" (the
  `registry.get` → `types_for` two-case split) plus per-flavor finalize
  wording. The split mechanism is shared-shaped; each wording moves alone
  (Decision 8: the auth message names the consumer's factories and the
  phase-2.5 order lets it pre-empt the generic one).
- **Sites + roles.** *Existing definition*:
  [mutations-sets][mutations-sets]`::_resolve_primary_type` (WT lines
  1567/1570). *Mirror here*:
  [auth-mutations][auth-mutations]`::_resolve_user_primary_or_raise` (WT
  lines 1435/1439; same getter, same two-case split, auth wording).
  *Ordering*: finalizer runs the auth bind (WT lines 1105-1106) before
  `bind_mutations()` (WT line 1107) — verified at WT.
- **Challenges.** C5 → 2 for the split, 1 per wording.
- **Owner + lifetime.** Family `type-registry-model-type-map` owns the
  decision (verified zero-edit: the mirror stands). No stored derivation.
- **Distinct behavior.** The auth-first ordering is intentionally separate,
  owned by the finalizer slot.
- **Behavioral proof.** `static-reviewed` (both bodies + the slot read).
- **Structural gate.** The three auth bind-error tests (pre-existing; pin
  the auth wordings independently of the generic one).
- **Freshness.** auth-mutations WT `217c6bff` / HEAD `c5be5fe9`;
  mutations-sets WT `6f2fa2f9`; finalizer WT `8f699081`. Blocked-on-hunt
  note: the auth mirror's two `truth.name` lines sit in hunt hunk
  `@@ -1521`; a consolidation would touch them.

### FC-5 — leaf-composition census (CONFIRM)

- **Contract + variation.** The folder composes small shared leaves by
  call, never re-spelling them: error leaves, storability preflight,
  async dispatch, soft-dependency guard, session primitives, request
  resolution, declaration/input/payload builders, write skeleton + model
  steps, directives validator, deadline check.
- **Sites + roles.** Each owner exists exactly once at both states (25/25
  census: `_disposed_awaitable`, `run_in_one_sync_boundary`,
  `actor_transition`, `scope_singleton`, `scope_key`,
  `session_store_class`, `require_optional_module`, `field_error`,
  `null_field_error`, `async_execution`, `register_subsystem_clear`,
  `make_declaration_registry`, `_resolve_primary_type`,
  `DjangoMutationMetaclass`, `authorize_or_raise`, `build_payload`,
  `payload_cls_for`, `request_from_info`,
  [utils-inputs][utils-inputs]`::make_input_namespace`,
  `_lazy_ref`, `build_lazy_field_signature`,
  `validated_field_directives`, `unencodable_text_error`,
  `bind_auth_mutations`, `_AuthMutationMetaSnapshot`). Folder sites: 4
  error-leaf calls (direct `utils.errors` imports, zero `resolvers.`
  spellings at either state), 3 preflight calls in 2 groups, 1 dispatch
  read, 1 one-line guard wrapper, 4 primitive compositions, 4
  request-resolution calls under one label, driver + builder + skeleton
  compositions, 1 directives call, 1 deadline call.
- **Challenges.** One per leaf (C1/C8/C9/C11/C19-C22 representatives) → 1
  at each owner, 0 new here.
- **Owner + lifetime.** Each leaf's indexed owner; no stored derivations.
- **Behavioral proof.** `static-reviewed` (every composition off an import
  edge whose owner body was census-checked).
- **Structural gate.** The per-leaf oracles named in FL-1..FL-4
  (pre-existing).
- **Freshness.** All four targets as pinned; utils-errors WT `e9572ea9`;
  utils-imports WT `3ea52b16`; utils-execution WT `b86a08cd`;
  utils-permissions WT `f12edaf8`; utils-inputs WT `0b8d3daa`;
  utils-directives WT `23421f6b`; utils-write-values WT `1dc426d4`;
  mutations-fields WT `62a15151`; mutations-inputs WT `bb329e4d`;
  mutations-resolvers WT `9171b93f`.

### FC-6 — manifest, opt-in, privacy (CONFIRM)

- **Contract + variation.** The leaf manifest re-exports exactly the four
  factories by name with `__all__` mirroring in-file; the package root
  never imports auth (structural opt-in, Decision 3); transport internals
  stay submodule-private. Varies only in membership.
- **Sites + roles.** *Manifest*: [auth-init][auth-init] statements 1-3
  (WT blob `2e480818`, clean). *Definitions*: the four factories in
  their home modules. *Opt-in mechanism*: finalizer `loaded_attr` guard
  + registry self-registration (verified at WT finalizer lines
  1101-1106). *Privacy owner*: [auth-sessions][auth-sessions] docstring
  clause. *Oracles*: explicit-name consumer imports + the two
  auth-free-subprocess tests.
- **Challenges.** C24 → 1 (home def); opt-in lift → 0 here; privacy
  lift → 1 (sessions module).
- **Owner + lifetime.** Per-symbol homes (manifest), Decision 3 +
  finalizer/registry (opt-in), sessions module (privacy). No stored
  derivation.
- **Behavioral proof.** `static-reviewed` (zero `auth` imports in the
  package root at WT; zero `sessions` names bound in the manifest).
- **Structural gate.** Consumer-import breakage + the subprocess oracles
  (pre-existing); no bespoke manifest pin owed (principle-9 economy).
- **Freshness.** auth-init `2e480818` (all three states); root WT
  `b688e2fa`; finalizer WT `8f699081`; accounts-schema WT `dd2e81b3`.

### FF-1 — `errors-auth-resolvers-spelling` D1 is GONE (flag; do not reopen)

- **Contract + variation.** The defect-routed index row claims
  `auth/mutations.py` calls `resolvers.field_error` at two HEAD sites (a
  layering wart: the model mutation resolver spelled as the utility
  module).
- **Sites + roles.** Re-grepped at current bytes: zero `resolvers.`
  error-leaf spellings at WT *and* at HEAD `23b5f421`. Both sites import
  `field_error`/`null_field_error` directly from `utils.errors` (WT
  lines 547/1210). The fixing commit is `b20277fe`
  ("build(typing)...", ancestor of HEAD): parent shows 2 sites, the
  commit shows 0.
- **Challenges.** The posited fix (import from the owner at both sites)
  already holds; definitions forced by any error-leaf change: 1 (the
  owner, FC-5).
- **Owner + lifetime.** Row owned at File `utils/errors.py`; this item
  only flags staleness. No stored derivation.
- **Behavioral proof.** `static-reviewed` (exact-count grep at both
  states + the fixing commit's before/after).
- **Structural gate.** The `mutation-error-envelope` singularity gates
  (pre-existing, adopted).
- **Freshness.** auth-mutations WT `217c6bff` / HEAD `c5be5fe9`.
- **Worker-0 action owed.** Retire the `errors-auth-resolvers-spelling`
  `defect-routed` row at closeout (fixed by committed concurrent work
  `b20277fe`, not by this cycle); no reopen of File `utils/errors.py`.

### FF-2 — head-seal consolidation observed at WT (flag; needs attribution)

- **Contract + variation.** The file artifact's F6 nominated family
  `sealed-authorization-source` with two sub-rules: slot seal (generic
  record vs duck snapshot) and head seal (generic factory vs bespoke
  `_SealedAuthHolderMeta` class). At HEAD both counts stand (bespoke
  class at HEAD lines 272-302, seal arms intact). At WT the bespoke
  class is deleted and `_SealedAuthHolderMeta = DjangoMutationMetaclass`
  aliases the generic metaclass (WT lines 260-275 + import): head count
  2 → 1 by an unattributed consolidation (no ledger row, no family
  item, not hunt-shaped: it removes a `ConfigurationError` seal, not a
  `BaseException` arm or hostile guard).
- **Sites + roles.** *HEAD second definition*: the deleted class (hunks
  `@@ -250`/`@@ -265` + import hunk `@@ -61`). *WT composition*: the
  alias + the unchanged `_make_permission_holder` synthesis call. The
  WT change is external concurrent work: left untouched per the
  no-revert rule.
- **Challenges.** C7 → 1 at WT (generic seal), 2 at HEAD.
- **Owner + lifetime.** Attribution owed to Worker-0/the maintainer (which session
  landed the alias, and whether its seal-behavior delta — bespoke
  message vs generic message — was oracle-checked). No stored derivation.
- **Behavioral proof.** `static-reviewed` (HEAD class read; WT alias +
  synthesis call read). The seal-behavior equivalence is NOT proven by
  this item (concurrent work; the head-seal oracle lives in hunt-dirtied
  test files).
- **Structural gate.** `test_auth_permission_holder_head_is_sealed`
  (pre-existing; re-run belongs to the final gate, not this item).
- **Freshness.** auth-mutations WT `217c6bff` / HEAD `c5be5fe9`;
  mutations-sets WT `6f2fa2f9`.
- **Consequence.** No `sealed-authorization-source` family item is owed:
  at current bytes the head sub-rule is already single (by unknown
  hands) and the slot sub-rule is a documented mirror (FF-4). Worker-0
  reconciles the unattributed hunks before any dispatch touching them.

### FF-3 — anonymity contract rewritten by hunt (flag; shape CONFIRMs)

- **Contract + variation.** The file artifact's F12 states five hostile
  shapes collapse to anonymous with store errors propagating. At WT the
  function body is hunt-rewritten (hunk `@@ -552,75 +507,30`): only a
  pending awaitable collapses (via the ledgered `_disposed_awaitable`
  call); every attribute read, legacy call, and truthiness failure
  propagates to the error policy. The single-owner *shape* still holds
  (one classifier, two consumers by call: `_logout_observation` and the
  `me` resolve body), but the *contract sentence* in F12 is false at WT.
- **Sites + roles.** *Definition*: `_authenticated_actor_or_none` (WT
  lines 498-533). *Consumers*: unchanged (logout `ok`, `me` return).
  *Oracles*: hunt migrated the hostile-shape pins to propagation pins
  (concurrent media work).
- **Challenges.** C12 → 1 at WT for any classification change.
- **Owner + lifetime.** This module (classifier shape). No stored
  derivation. The propagation-vs-collapse policy is hunt-owned while
  the migration is in flight.
- **Behavioral proof.** `static-reviewed` (WT body read in full; zero
  `except` clauses remain in it).
- **Structural gate.** The WT propagation pins (concurrent; pre-existing
  at item scope).
- **Freshness.** auth-mutations WT `217c6bff` / HEAD `c5be5fe9`.
- **Blocked-on-hunt.** The whole function body is hunt dirt; any
  consolidation touching it (none is owed — count is 1) stays blocked.
  Index row named with the WT contract sentence (see `auth-anonymity`).

### FF-4 — sealed-slot mirror is REJECTED as a family (no dispatch)

- **Contract + variation.** `_ValidatedMutationMeta` (model-backed, full
  Meta record) vs `_AuthMutationMetaSnapshot` (model-less duck type:
  `operation` + `permission_classes` only). Contract difference: the
  generic record requires model constructor kwargs a model-less session
  field does not have, so the snapshot deliberately is not a generic
  record (stated in its docstring, verified against both bodies at WT).
  A seal-behavior change moves both (C6 → 2 shapes), but a carrier change
  moves exactly one: different responsibilities, different reasons to
  change. Shared seal idiom, not a shared rule.
- **Sites + roles.** Generic record in [mutations-sets][mutations-sets];
  snapshot in [auth-mutations][auth-mutations] (WT lines 209-252,
  intact). Oracles pin each shape independently.
- **Challenges.** C6 → 2 shapes for seal behavior; 1 per shape for
  carrier changes.
- **Owner + lifetime.** Each record's home module. No stored derivation.
- **Behavioral proof.** `static-reviewed` (constructor requirements read
  off both bodies).
- **Structural gate.** The two seal tests (pre-existing; each pins one
  shape).
- **Freshness.** auth-mutations WT `217c6bff`; mutations-sets WT `6f2fa2f9`.
- **Trigger to reconsider.** A shared seal-mixin need (a third sealed
  carrier, or a seal-behavior change that must land atomically on both)
  would make the sites one rule. Durable home: the snapshot docstring
  (already states the deliberate non-reuse).

### FF-5 — record-accuracy flags (no verdict change)

- **Queries enumeration drift.** The file artifact counts 15 top-level
  statements; WT has 19. The delta is annotation-only growth
  (`TYPE_CHECKING` block + `CurrentUserAlias` parked-global annotation +
  two trio-arm annotations): zero new rule-bearing defs, all six
  rule-bearing definitions home exactly as the artifact records (R1-R3,
  F1-F3). No assignment falsified; Worker-0 owes no action.
- **`ws-connection-actor-state` name.** The F3 family-row name was never
  transcribed to the plan and needs no row: the rule is covered by the
  existing `utils-sessions-actor-transition` + `utils-sessions-lease-order`
  file-local rows (which name this folder's holding site) and re-verified
  here as FC-3. No new row.
- **`auth-leaf-manifest` name.** The queries-F3 definition-site side is
  covered by the single `auth-leaf-manifest` row named below (manifest
  owner + both home modules). No second row.

### FL-1 — `auth/__init__.py` local rules (CONFIRM, 3 rows)

- **Contract + variation.** Covered by FC-6 (manifest membership,
  structural opt-in, sessions privacy). Each varies only as stated there.
- **Sites + roles.** Manifest statements 1-3 (consumers by import);
  contract sources Decision 3 + sessions docstring; oracles as FC-6.
- **Challenges.** C24 (+ opt-in/privacy lifts) → counts as FC-6.
- **Owner + lifetime.** Per FC-6. No stored derivation.
- **Behavioral proof.** `static-reviewed` (FC-6 evidence).
- **Structural gate.** FC-6 gates (pre-existing).
- **Freshness.** auth-init `2e480818` (all three states).
- **Rows named:** `auth-leaf-manifest`, `auth-structural-opt-in`,
  `auth-sessions-privacy-omission` (table below).

### FL-2 — `auth/mutations.py` local rules (CONFIRM, 13 rows)

- **Contract + variation.** Family label (C8: one const, wording-drift
  guard); failure + capability wordings (C9: undifferentiated message vs
  free top-level rejections); register tables (naming/exclusion/
  protection/surface-name); declaration key + synthesis (C10: schema
  args only, one synthesis site, dual-ledger re-record for the rider);
  field seam + interim bridge (C11: split sync/async bodies, injected
  lazy signature); anonymity classifier (C12: WT contract per FF-3);
  transport + login/logout prologues (C13: fixed order, no mutation);
  payload ctors (C14: failed envelope, result dispatch, ok-observation);
  critical-section twins (C15: per-transport establish/teardown with
  per-shape compensation); resolve-body twins (C16: prologue →
  payload-before-mutation → critical section); factories (thin
  declaration + wiring); register derivation + step pair + rider (C17:
  USERNAME-first narrowing, password capture, validate-then-hash before
  the shared tail, lazy rider); phase-2.5 bind (C18: surface-keyed,
  primary resolved at most once, payloads on the shared ledger).
- **Sites + roles.** Each rule defined once in this module at WT (full
  read); shared halves composed by call per FC-5; nested D-N2 rejection
  (direct `password` keying) and D-N3 omission (no rider visibility
  helper) re-verified intact at WT lines 1191-1236 and the rider `Meta`
  comment.
- **Challenges.** C8-C11, C12-C18 → 1 per rule (C15: 2 per twin pair).
- **Owner + lifetime.** This module (auth-surface policy); ledger
  lifetime process-scoped (full-clear-only). No stored derivation.
- **Behavioral proof.** `static-reviewed` (bodies read; delegation edges
  checked). Rejects "a second declaration path / seam / classifier /
  prologue / ctor / twin exists" (exact-count greps, each 1).
- **Structural gate.** The per-rule oracles (conflict trio, dispatch
  spies, enumeration guard, gate-string pins, compensation suite,
  derive quartet, orphan-payload trio, reload cycles — all pre-existing).
- **Freshness.** WT `217c6bff` / HEAD `c5be5fe9` / BASE `217c6bff`.
  Blocked-on-hunt lines: every `truth.*` read, the F12 body, the four
  narrowed `except` arms, the `ScopeSingletonMessages` consumer line —
  none owed a consolidation (all counts ≤1, twins rejected in FR-1/FR-2).
- **Rows named:** `auth-request-label`, `auth-failure-wordings`,
  `auth-register-tables`, `auth-declaration-machine`, `auth-field-seam`,
  `auth-anonymity`, `auth-prologues`, `auth-payload-ctors`,
  `auth-critical-twins`, `auth-resolve-twins`, `auth-factories`,
  `auth-register-rider`, `auth-phase-bind` (table below).

### FL-3 — `auth/queries.py` local rules (CONFIRM, 3 rows)

- **Contract + variation.** `me` resolve contract (C23: classify →
  gate-first with `instance=actor` → nullable return; no queryset work);
  factory wiring (fourth surface through the shared fixed path, nullable
  alias ref, no envelope); alias identity (C19: two single-spelled
  constants + the trio unpack homing ledger/materialize/clear).
- **Sites + roles.** `_current_user_resolve_body`, `current_user`, the
  constants + unpack (WT lines 48-80, 83-148, all clean-tree). Shared
  halves by call/import per FC-5. Rejections J1 (one-site nullable wrap),
  J2 (no native async: async arm is the bridge at line 134), J3 (pre-bind
  ledger vs full-clear payload ledger), J4 (no prologue: zero
  `_transport_prologue` calls), J5 (no envelope) all re-verified intact.
- **Challenges.** C19, C23 (+ C6-analogue for the factory) → 1 each.
- **Owner + lifetime.** This module (read-side shape). Ledger lifetime =
  process-emit (pre-bind reset, parked globals).
- **Behavioral proof.** `static-reviewed` (order + args + flags read;
  absences grep-verified over the file).
- **Structural gate.** Denial-string pin, dispatch-spy pair, alias
  identity, live `me` rows (pre-existing).
- **Freshness.** `b0c60920` (all three states; target clean).
- **Rows named:** `auth-me-resolve`, `auth-me-factory`, `auth-alias-names`
  (table below).

### FL-4 — `auth/sessions.py` local rules (CONFIRM, 4 rows)

- **Contract + variation.** Transport classification (C20: real-class
  check over the unwrapped candidate, then scope-type split, loud
  rejects); per-scope lock (C21: one helper over the shared singleton
  trio, auth-owned corrupted wording); missing-session pre-check (one
  collapsing guard with transport-specific wording); capability answers
  (C22: engine read + two predicates).
- **Sites + roles.** `classify_transport`, `scope_session_lock` (+ key +
  messages), `require_session`, `uses_signed_cookie_sessions` +
  `login_supported` + `logout_supported` (WT lines 104-293). Owner trio
  intact per FC-5; the 4→1 message collapse lives in the owner.
- **Challenges.** C20-C22 → 1 per rule.
- **Owner + lifetime.** This module (transport boundary). Lock lifetime =
  scope-living (lazy, in-scope store, no await between read and store).
- **Behavioral proof.** `static-reviewed` (single-site census per rule;
  reads verified against the owner trio bodies).
- **Structural gate.** Transport-matrix tests, lock-sharing tests,
  missing-middleware tests, capability tests (pre-existing).
- **Freshness.** WT `6e5fadb7` / HEAD `1dc65564` / BASE `6e5fadb7`.
  Blocked-on-hunt lines: the classifier reads, all deleted guard arms,
  the `is_subclass` line, the message-table consumer (hunks `@@ -10`
  through `@@ -343` except the install-hint const) — none owed a
  consolidation (all counts 1).
- **Rows named:** `auth-transport-classify`, `auth-scope-lock`,
  `auth-require-session`, `auth-capability` (table below).

### FR-1 — login vs logout compensation merge (REJECTED)

Considered: one shared compensation helper for the four critical
sections. Contract difference: login arms compensate by anonymizing AND
flushing the partially established durable row (establish-then-persist);
logout arms compensate by anonymizing only (the native teardown owns
durability; a logout-time flush would double-flush). Within each shape
the Django/Channels pair differs on await points (sync `flush()` vs
`aflush()` under the held scope lock). Posit "log instead of chain" →
two defs per pair move (C15), but posit "change the logout anonymize to
a flush" → only logout moves: separate reasons to change. Trigger: a
unified establish/teardown primitive with one compensation shape would
make the sites one rule. Durable home: the per-function docstrings
(already state the shape split).

### FR-2 — sync/async twin merge, any pair (REJECTED)

Considered: one body per surface with an execution adapter. Contract
difference per pair: login/logout twins exist because Channels arms must
await `channels.auth` + session persistence natively (no sync
counterpart, and the router forbids nested `async_to_sync` on async
consumers); the register twin exists because the pipeline is sync-only
(the async entry is the one-boundary bridge, no native work); the `me`
twin exists because reads have no per-transport awaits at all (bridge
only). Three different reasons for three different twin shapes; one
adapter would need mode flags for work that does not exist. Trigger:
transport primitives offering identical sync/async shapes would collapse
a pair. Durable home: the twin docstrings (already record the contrast
per principle 5).

### FR-3 — prologue merge beyond `_transport_prologue` (REJECTED)

Considered: one login/logout prologue. Contract difference: the common
prefix (resolve → classify → capability → require session) is already
the single `_transport_prologue`; past it login runs gate-with-username
+ storability preflight + exactly-one `authenticate` (D-N1, no local
query) while logout runs gate + payload-class resolution. Merging past
the shared prefix would parameterize the whole state machine. Trigger:
identical step sequences would make the remainder one rule. Durable home:
the three prologue docstrings.

### FR-4 — payload-ctor merge (REJECTED)

Considered: one ctor for failed-login envelope, login result dispatch,
and logout observation. Contract difference: undifferentiated
anti-enumeration envelope vs success/failure dispatch with
payload-before-mutation ordering vs pre-teardown `ok` observation with
under-lock capture. Three contracts, three callers, three oracle groups.
Trigger: a uniform auth envelope would make the sites one rule. Durable
home: the three ctor docstrings.

### FR-5 — factory-merge (REJECTED)

Considered: one factory for login/logout/register/`me`. Contract
difference: the fixed fields (login/logout/`me`) declare holders through
`_declare_fixed_auth_surface` and build fields through `_make_auth_field`,
while register synthesizes a model-backed rider through
`DjangoMutationField` with dual-ledger re-record; `me` is a query, not a
mutation. Everything already-shared (declaration path, seam, bridge) is
shared; the remainder is per-surface shape. Trigger: a uniform surface
shape would make the sites one rule. Durable home: the factory docstrings.

### FR-6 — transport-rejection merge (REJECTED)

Considered: one WebSocket rejection for login + logout. Contract
difference: login is unsupported on ANY WebSocket (cookie rotation can
never return); logout is unsupported only on signed-cookie-engine
WebSockets (no server-side record to revoke). Different predicates,
different firings, both wordings free by contract. Trigger: a uniform
transport capability would make the sites one rule. Durable home: the
two message comments.

### FR-7 — gate-call merge (REJECTED)

Considered: one `authorize_or_raise` wrapper for the three fixed sites.
Contract difference: the call arguments ARE the per-surface contract
(login: `data={"username"}`, `instance=None`; logout: `data=None`,
`instance=None`; `me`: `data=None`, `instance=actor`). A wrapper would
hide the exact args the gate-string oracles pin. Trigger: uniform gate
args would make the sites one rule. Durable home: the three call sites'
comments.

## Defects

None new. Tracing found no contract-row break with a feasible project
shape and a reaching wire input beyond what the file items already
routed. Two routed items changed state and are recorded here, not as new
defects:

- `errors-auth-resolvers-spelling` D1 (File `utils/errors.py`,
  defect-routed): GONE at both current states, fixed by committed
  concurrent work `b20277fe` (FF-1). Retirement owed at closeout.
- The WT seal-alias behavior delta (bespoke vs generic seal message,
  FF-2): observed concurrent work, explicitly NOT proven equivalent by
  this item. If the final gate's head-seal oracle passes at WT, the
  delta is cosmetic; if it fails, the failure routes to whoever owns
  the unattributed hunks. Either way the verdict belongs to the gate,
  not this audit.
- D1 (Worker-2, record-only): request-resolution consumer count is 4,
  not 5. `rg -n "request_from_info\("` over the folder minus the two
  import lines yields mutations 572/805/1024 + queries 101 at WT, and
  3+1 at HEAD; an AST call census agrees
  (mutations `[572, 805, 1024]`, queries `[101]`). The artifact claims
  5 in `### Enumeration` ("request resolution (5 call sites)") and
  FC-5 ("5 request-resolution calls"). Definition count (1, at the
  owner) and ownership are unaffected. Routes to the Worker-1
  resubmission on this pass, not to a code owner.

## Pending execution

No `proof:` entries (zero `execution-deferred` proofs; every finding is
`static-reviewed` by kind with ordering/async pinned by the named
pre-existing oracles). Gate entries for the final gate (re-run as
listed; results bind to the tree state at gate time):

- `gate: uv run python scripts/workspace.py run dry/folder-auth/consolidate -- basedpyright`
- `gate: uv run python scripts/workspace.py run dry/folder-auth/consolidate -- basedpyright -p pyrightconfig.floor.json`
- `gate: uv run python scripts/workspace.py run dry/folder-auth/consolidate -- python scripts/check_truthful_reads.py --check`
- `gate: uv run pytest -n0 tests/auth/test_queries.py -q --no-cov`
- `gate: uv run pytest -n0 tests/auth/test_mutations.py -q --no-cov`
- `gate: uv run pytest -n0 tests/auth/test_sessions.py -q --no-cov`

Cells: `sharded` and `pg` stay `unverified` (auth paths reach the user
table: `authenticate` reads, register writes, `me` forces the lazy actor;
inapplicable-by-construction is correctly NOT claimed). They need the
maintainer's separate word per the entry brief.

## Judgment

Zero-edit folder item, ready for verification. CONFIRM: every
cross-boundary composition the file artifacts claimed still composes by
call at WT (FC-1/FC-2/FC-3/FC-5/FC-6, 25/25 owner census); the
family-verified mirrors stand (FC-4); all 23 unassigned folder-local
rules are single-owned with proving challenges (FL-1..FL-4); seven
folder-level merges are rejected with triggers (FR-1..FR-7). FLAG (tree
falsified the assignment, rows not reopened): D1 gone via `b20277fe`
(FF-1, retire at closeout); head-seal count 2→1 at WT via unattributed
concurrent consolidation (FF-2, needs Worker-0/the maintainer attribution); F12
contract sentence replaced by hunt's propagation policy while the
single-owner shape holds (FF-3); slot mirror rejected as a family, no
dispatch (FF-4). No consolidation confirmed; no production edit, no test
edit, no ledger row. Blocked-on-hunt: every hunt-dirtied line cited in
FC-1/FC-4/FL-2/FL-4 (exact hunks recorded; nothing touched).
Needs-maintainer: attribution of the seal-alias hunks (`@@ -61`,
`@@ -250`, `@@ -265` in `auth/mutations.py`) + the five prose-only
external hunks before any dispatch touching them; `sharded`/`pg` cell
authorization.

## Index rows for Worker-0

23 new file-local rows + 1 rejection row + 2 corrections. Holding item
for all new rows: Folder integration `auth/`. No `## Families` item is
owed (FF-2/FF-4: no dispatch; FF-5: names covered).

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `auth-leaf-manifest` | `django_strawberry_framework/auth/__init__.py::__all__` (4-name mirror; defs in home modules) | `django_strawberry_framework/auth/__init__.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-structural-opt-in` | spec-040 Decision 3 + `django_strawberry_framework/types/finalizer.py` loaded-attr slot (projection at `django_strawberry_framework/auth/__init__.py`) | `django_strawberry_framework/auth/__init__.py` | Folder integration `auth/` | file-local |
| `auth-sessions-privacy-omission` | `django_strawberry_framework/auth/sessions.py` (module docstring clause; enforced by omission at `django_strawberry_framework/auth/__init__.py`) | `django_strawberry_framework/auth/__init__.py`, `django_strawberry_framework/auth/sessions.py` | Folder integration `auth/` | file-local |
| `auth-request-label` | `django_strawberry_framework/auth/mutations.py::_AUTH_FAMILY_LABEL` (1 const, 6 reference sites) | `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-failure-wordings` | `django_strawberry_framework/auth/mutations.py::_INCORRECT_CREDENTIALS_MESSAGE` (+ 2 free WS rejections) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-register-tables` | `django_strawberry_framework/auth/mutations.py::_REGISTER_INPUT_NAME` (+ exclusion/protection/surface-name tables) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-declaration-machine` | `django_strawberry_framework/auth/mutations.py::_declare_auth_surface` (key + synthesis; mechanics at the driver) | `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-field-seam` | `django_strawberry_framework/auth/mutations.py::_make_auth_field` (+ `_sync_bridged_async_body` bridge) | `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-anonymity` | `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none` (WT contract: awaitable collapses, all else propagates; 2 consumers) | `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-prologues` | `django_strawberry_framework/auth/mutations.py::_transport_prologue` (+ login/logout prologues; fixed order, no mutation) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-payload-ctors` | `django_strawberry_framework/auth/mutations.py::_failed_login_payload` (+ result dispatch + ok-observation) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-critical-twins` | `django_strawberry_framework/auth/mutations.py::_django_http_login_establish` (+ 3 arms; per-shape compensation, principle-5 twins) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-resolve-twins` | `django_strawberry_framework/auth/mutations.py::_login_resolve_body` (+ 3 arms; principle-5 twins) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-factories` | `django_strawberry_framework/auth/mutations.py::login_mutation` (+ logout/register thin wrappers) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-register-rider` | `django_strawberry_framework/auth/mutations.py::derive_register_fields` (+ decode/write steps + lazy rider; D-N2/D-N3 recorded) | `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-phase-bind` | `django_strawberry_framework/auth/mutations.py::bind_auth_mutations` (surface-keyed; slot owned by finalizer) | `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-me-resolve` | `django_strawberry_framework/auth/queries.py::_current_user_resolve_body` (gate-first, instance=actor, nullable) | `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-me-factory` | `django_strawberry_framework/auth/queries.py::current_user` (4th surface, nullable alias ref, no envelope) | `django_strawberry_framework/auth/queries.py` | Folder integration `auth/` | file-local |
| `auth-alias-names` | `django_strawberry_framework/auth/queries.py::CURRENT_USER_ALIAS_NAME` (+ module path + trio unpack) | `django_strawberry_framework/auth/queries.py`, `django_strawberry_framework/auth/mutations.py` | Folder integration `auth/` | file-local |
| `auth-transport-classify` | `django_strawberry_framework/auth/sessions.py::classify_transport` (single classifier; reads hunt-rewritten) | `django_strawberry_framework/auth/sessions.py` | Folder integration `auth/` | file-local |
| `auth-scope-lock` | `django_strawberry_framework/auth/sessions.py::scope_session_lock` (+ key + corrupted wording) | `django_strawberry_framework/auth/sessions.py` | Folder integration `auth/` | file-local |
| `auth-require-session` | `django_strawberry_framework/auth/sessions.py::require_session` (one collapsing guard) | `django_strawberry_framework/auth/sessions.py` | Folder integration `auth/` | file-local |
| `auth-capability` | `django_strawberry_framework/auth/sessions.py::login_supported` (+ logout predicate + engine read) | `django_strawberry_framework/auth/sessions.py` | Folder integration `auth/` | file-local |
| `auth-sealed-slot-mirror` | `django_strawberry_framework/auth/mutations.py::_AuthMutationMetaSnapshot` (rejection: model-less duck type vs model-backed record; trigger = shared seal-mixin need; home = snapshot docstring) | `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/mutations/sets.py` | Folder integration `auth/` | rejected |

Corrections owed on existing rows (Worker-0 edits, not new rows):

- `one-sync-boundary`: insert `auth/queries.py` into files-covered after
  `auth/mutations.py` (FC-2; run-7 W2 ruling re-verified at WT).
- `errors-auth-resolvers-spelling`: retire at closeout (FF-1; fixed by
  committed `b20277fe`).

## Independent verification (Worker-2)

Pass 1. Read order kept: target (all four files, full), scoped diff
(`git diff 085c1d78 -- <4 paths>` empty; `git status` shows only the
two known WT dirties; no new files under `auth/`), every touched
site's consumers/tests, then this artifact. Pins re-derived, all
match: init `2e480818` clean, mutations WT `217c6bff`/HEAD `c5be5fe9`,
queries `b0c60920` clean, sessions WT `6e5fadb7`/HEAD `1dc65564`;
baseline `085c1d78` is a commit whose four blobs equal WT, so the
scoped diff is empty and the zero-edit claim holds mechanically.

### My trace (before reconciling)

Instrument: full read + `ast.parse` per file + `rg`/`git show HEAD:`
sweeps + an AST call census. WT census of mine: init 4 stmts/0 defs;
mutations 74 stmts/33 defs (1 class + 32 fns); queries 19/2; sessions
27/9 (1 enum + 8 fns); 124 stmts, 44 defs, 18 rule-level
non-def members (1 + 8 consts/ledger/row + 2 consts/trio/row + 3).
Line counts 20 / 1511 (HEAD 1594) / 148 / 293 (HEAD 385). Owners I
would choose: every shared leaf at its existing outside owner (no
second body found package-wide for disposal, boundary, lease, bus,
guard, error leaves, dispatch, primitives, preflight, request
resolution, declaration mechanics, builders, skeleton, directives,
deadline); the 23 folder rules each at their single folder site; the
primary split as a documented mirror (generic wording vs auth wording,
1 each); the sealed slot as a documented non-family (model-backed
record vs model-less duck type — generic `__init__` requires a `model`
kwarg, snapshot carries 3 slots).

Counts of mine per rule (definitions only): disposal 1; boundary 1
owner + 6 folder call sites (436/807/814/1026/1027/1376); lease+bus 1
each; primary split 2 mechanisms/1 wording each; head seal 1 at WT
(alias), 2 at HEAD (bespoke class at HEAD 272ff); slot seal 2 shapes;
label 1 const + 6 non-import refs (+1 import edge); failure message 1;
conflict key 1; seam 1 + 3 consumers; bridge 1 + 1 consumer (queries
134); anonymity 1 + 2 consumers; prologues 3 (1 shared prefix + 2);
payload ctors 3; compensation 2 per twin pair; resolve twins 1 per
surface; register steps 1 each; bind 1; alias 1 per const; classifier
1; scope lock 1; session guard 1; capability 1 per predicate; `me`
contract 1; manifest 1 per home. Request-resolution call sites of
mine: 4 (mutations 572/805/1024, queries 101), both states, two
instruments.

Second-site sweeps of mine (all negative): `sync_to_async` 8 prose
hits, 0 code; `get_queryset` 3 prose hits, 0 code; `resolvers.`
error-leaf spellings 0 both states; `close()`/`cancel()` 0;
`classify_transport` 1 def package-wide; `bind_auth_mutations` 1 def;
`family_label=` literals 0 (all pass the const); `is_authenticated`
siblings are a lazy-proxy evaluation touch (views 1022), revalidation
reads (consumers 1025/1066), and doc prose — different contracts, not
second classifiers; declaration-registry flavors are 3 disjoint
driver-owned stores (mutation/auth/form), not rival mechanics. No
real consolidation exists; the seal alias already took the only
count-2 head rule, by unknown hands.

### Reconciliation (every difference)

Exactly one: my request-resolution census is 4 where the artifact
says 5 (Enumeration + FC-5). D1 (Worker-2) filed above; definition
count and ownership unaffected. Everything else in my trace agrees:
all pins, line counts, AST figures, all 24 other census figures, all
owner choices, all four twin separations, all seven rejections'
contract differences, and all four flags' observations. The two
`sealed-authorization-source` sub-rules split exactly as Worker-1 has
it (head already-single at WT, slot rejected with trigger); the F12
contract sentence in the file artifact ("exactly five hostile shapes
collapse") is indeed false at the WT body I read (awaitable-only
collapse, zero `except`); the D1 row in the plan is `defect-routed`
and indeed gone at both states via `b20277fe` (verified: parent 2
sites, commit 0, ancestor of HEAD).

FF rulings: FF-1 endorse (retire at closeout, no reopen — committed
fix, zero sites both states). FF-2 endorse (hunks `@@ -61/250/265`
read: import add, comment + TYPE_CHECKING rename, bespoke-class
deletion + alias; content is seal consolidation, matches neither the
sole auth ledger row (e1 disposal) nor hunt shapes; verdict correctly
to the final gate — the head-seal oracle
`test_auth_permission_holder_head_is_sealed` sits in gated
`tests/auth/test_mutations.py`; attribution need stands).
FF-3 endorse (body read in full; shape count 1 holds; propagation
policy correctly attributed to the in-flight hunt; index row carries
the WT sentence). FF-4 endorse the no-dispatch call (contract
difference verified at both bodies; reconsideration trigger and
durable home adequate; no family item owed, and none exists in the
plan to close).

### Index-row rulings (26/26)

Endorse all 23 file-local rows (each re-derived single-owned with its
challenge: manifest/opt-in/privacy via FC-6 evidence re-checked —
zero root `auth` imports, `loaded_attr` guard + `bind_auth()` before
`bind_mutations()` at finalizer 1105-1107, zero `sessions` names in
the manifest; label/failure/tables/machine/seam/anonymity/prologues/
ctors/twins/factories/rider/bind via full-body reads; `me`
contract/factory/alias via the clean-tree read incl. J4 zero-prologue
re-check; transport/lock/session/capability via WT reads with
hunt-dirt boundaries noted). Endorse the `auth-sealed-slot-mirror`
rejection row (FF-4 verified). Endorse both corrections:
`one-sync-boundary` +`auth/queries.py` (plan verified lacking it;
bridge call at queries 134 verified) and `errors-auth-resolvers-spelling`
retirement (FF-1 verified). All 24 new names absent from the plan —
no collisions. No `## Families` item owed (FF-2/FF-4/FF-5 concur).

### Gates, prose, pending execution

Re-ran in my own copy (`workspace.py run dry/folder-auth/verify-1`,
slot-3, fresh sync, shared unmoved): basedpyright `0 errors,
0 warnings, 0 notes`, exit 0; floor `0/0/0`, exit 0; truthful-reads
`--check` 120 files, errors 0, exit 0. `check_any.py` not run (gone).
Ruff: touched-`.py` set is empty (zero-edit; this artifact is `.md`)
— stated explicitly, no run owed. AGENTS.md prose on the item diff:
empty set, nothing to grade. `## Pending execution`: complete and
correctly typed — no `proof:` owed (every finding `static-reviewed`
by kind with pre-existing oracles named; nothing `execution-deferred`
hides in the text) and the 6 `gate:` entries are well-formed with all
three target suites on disk. Cells: `sharded`/`pg` honestly
`unverified` — the user-table reach is real (`authenticate` reads,
register writes, `me` forces the lazy actor) so inapplicability is
correctly NOT claimed; the honesty is right and complete.

### Verdict

`revision-needed` for the single record-only fix: 5→4 in the two
request-resolution census lines (D1), reproducible by the `rg` + AST
commands above. Nothing else moves: no owner, finding, flag, row,
rejection, or gate changes. Resubmission returns to this Worker-2.

### Pass-2 re-verification

Fresh Worker-2 (pass-1 context gone; its trace above is on-disk input,
re-verified, not inherited). Read order kept: pins, scoped diff, all
four targets, every cited consumer/owner/test, then this artifact.
HEAD `23b5f421` confirmed; all four WT/HEAD/BASE fingerprints match
the pins; scoped diff `git diff 085c1d78 -- <4 paths>` is 0 bytes; no
new files under `auth/`; line counts 20/1511/148/293 WT, 1594/385
HEAD. No production file moved since the pins.

D1 fix, my own repro, both instruments, both states: WT
`rg request_from_info\(` yields mutations 572/805/1024 + queries 101;
HEAD `git grep` yields mutations 662/891/1110 + queries 101; AST call
census agrees exactly (WT `[572, 805, 1024]` + `[101]`, HEAD `[662,
891, 1110]` + `[101]`). 4/4 at both states. Both edited lines read 4
(Enumeration line "request resolution (4 call sites)", FC-5 "4
request-resolution calls"); the remaining "5" mentions are historical
record only (D1 text, pass-1 trace, pass-2 note). Every other census
figure I re-derived below agrees with the artifact — no second
record defect.

Re-derivation (all at current bytes): AST census exact (init 4/0,
mutations 74/33, queries 19/2, sessions 27/9; 124 stmts, 44 defs).
Owner census 25/25 at BOTH states via a package-wide AST script (WT
121 files, HEAD archive 118 files): 24 names resolve to exactly one
top-level def each; `DjangoMutationMetaclass` sits conditional-nested
(TYPE_CHECKING stub class + the runtime factory product at
`mutations/sets.py:1110`, documented in place, identical shape at
HEAD) — one runtime owner, a checker twin, not a second definition.
Corroboration nuance, not a defect. Negative sweeps: `sync_to_async`
8 prose/0 code, `get_queryset` 3 prose/0 code, `resolvers.` error-leaf
spellings 0 at both states, `close()`/`cancel()` 0. Consumer counts:
boundary 6 (436/807/814/1026/1027/1376, exact), anonymity 2 (queries
106, mutations 880), label 1 const + 6 refs + 1 import edge,
`family_label=` literals 0, bridge consumer queries 134.

Full-body re-reads: `queries.py` all 148 lines (R1-R3/F1-F3 homing,
J1-J5 incl. zero-prologue re-check, trio unpack, pre-bind row
`before_bind=True`) and `sessions.py` all 293 lines (classifier,
lock over the intact owner trio with the 1-field messages, collapsing
pre-check, engine read + two predicates, privacy clause) — every
FL-3/FL-4 claim confirmed. Targeted reads: snapshot 209-252 +
generic `__init__` requiring `model` (FF-4 contract difference);
seal alias 275 + HEAD bespoke class + hunks `@@ -61/250/265` (FF-2);
anonymity body 498-533 in full, zero `except`, awaitable-only collapse
with the e1 disposal call intact (FF-3, FC-1); login flush vs logout
anonymize-only arms with the narrowed inner `except Exception`
(artifact's attribution names the inner arms — confirmed; R-F1);
`_transport_prologue` 1 def + 2 consumers, one `auth.authenticate`
call at 648 (R-F3, D-N1); register dual-ledger 1410-1411 +
`DjangoMutationField` 1412 (R-F5); gate args 636/860/queries-107, three
distinct shapes (R-F7); bind 1453-1480 surface-keyed, primary resolved
once (C18); finalizer 1105-1107 auth-before-generic (FC-4/FC-6); root
zero `auth` mentions; manifest 4 names, zero `sessions` names.

FF rulings: FF-1 endorse — `b20277fe` is an ancestor of HEAD, parent
2 sites, commit 0, zero at both current states; retire at closeout, no
reopen. FF-2 endorse — the 3 hunks are a seal consolidation matching
neither the sole auth production ledger row (run-7 e1 disposal,
verified as the only auth entry under plan `## Owned changes`) nor
hunt shapes; the 5 prose-only hunks confirmed comment-only (family
label, ledger row, two spec-046 citations, UNSET note); the oracle
`test_auth_permission_holder_head_is_sealed` sits at
`tests/auth/test_mutations.py:446`, the generic seal wording
(`mutations/sets.py:725/735`) matches its pins, and my one authorized
focused run passes 1/1 at WT — the delta is currently cosmetic, and
the verdict still belongs to the final gate's re-run. FF-3 endorse —
shape count 1 holds, propagation policy correctly hunt-attributed, the
index row carries the WT sentence. FF-4 endorse the no-dispatch call —
contract difference verified at both bodies, trigger + durable home
adequate, `sealed-authorization-source` absent from the plan so no
family item dangles. All seven rejection triggers (R-F1..R-F7)
restated-meets-body: each names its contract difference and its
reconsideration trigger; all stand.

Index-row rulings (26/26): endorse all 23 file-local rows (each
re-derived single-owned with its challenge per the reads above),
endorse the `auth-sealed-slot-mirror` rejection row, endorse both
corrections (`one-sync-boundary` verified lacking `auth/queries.py`;
`errors-auth-resolvers-spelling` verified `defect-routed` at File
`utils/errors.py`). All 24 new names absent from the plan — no
collisions. No `## Families` item owed. My ruling governs
transcription.

`## Pending execution` is complete and correctly typed: no `proof:`
owed (every finding `static-reviewed` by kind, nothing
`execution-deferred` hides in the text), 6 `gate:` entries well-formed
with all three suites on disk. Cells `sharded`/`pg` honestly
`unverified` — user-table reach re-confirmed (one `auth.authenticate`
read, the register write pipeline, `me` forcing the lazy actor), so
inapplicability is correctly NOT claimed.

Gates, my copy (`workspace.py run dry/folder-auth/verify-2`, slot-3,
fresh sync 2026-10-09T23:24:01Z, shared unmoved, digest
`sha256:d06adc7d...`): basedpyright 0 errors/0 warnings/0 notes, exit
0 (`dry-20261009T232402-4330b1`); floor 0/0/0, exit 0
(`dry-20261009T232515-5eb5e7`); truthful-reads `--check` 120 files,
errors 0, exit 0 (`dry-20261009T232627-e1ac2c`). Shared-tree focused
test (the one authorized): head-seal oracle 1 passed. Ruff
touched-`.py` set is empty (zero-edit; this artifact is `.md`) —
stated explicitly, no run owed. AGENTS.md prose on the item diff:
empty set, nothing to grade.

New defects: none found — no `## Defects` addition. Verdict:
`verified`.

## Iterations

Pass-2 note (Worker-1, record-only): applied D1 (Worker-2) exactly —
5→4 in the two request-resolution census lines only (`### Enumeration`
"request resolution (5 call sites)" and FC-5 "5 request-resolution
calls"). No owner, finding, flag, row, rejection, or gate changed;
`Run: 0.0.15 2026-10-09-13` kept; `Status:` advanced to
`ready-for-verification/2`.

Repro (both instruments, both states — agrees with Worker-2, no
disagreement): `rg -n "request_from_info\("
django_strawberry_framework/auth/` at WT yields queries 101 +
mutations 572/805/1024 (4 total); `git grep -n "request_from_info("
HEAD -- django_strawberry_framework/auth/` yields queries 101 +
mutations 662/891/1110 (4 total). AST call census
(`ast.Call` with `func.id == "request_from_info"`) agrees: WT
mutations `[572, 805, 1024]`, queries `[101]`; HEAD mutations `[662,
891, 1110]`, queries `[101]`.

Tree-confirmed unmoved: HEAD still `23b5f421`, the item-scoped diff
`git diff 085c1d78 -- <4 auth paths>` still empty, and the four WT
fingerprints re-derived identical to the pins (`2e480818`,
`217c6bff`, `b0c60920`, `6e5fadb7`). Pass-1 gate run ids stand; no
gate re-run (record-only `.md` fix).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
