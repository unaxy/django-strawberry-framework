# DRY review: `extensions/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights). Audits the UNASSIGNED remainder
of the `extensions/` folder and the families that cross its ownership
boundaries at current bytes (HEAD `23b5f421` + working tree). The five
member file artifacts are inputs, not verdicts: every assignment below
was re-derived fresh, and every assignment the tree has falsified is
flagged as a finding inside this item. No prior artifact is summarized.

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da` (detached, intended).
`ITEM_BASELINE=ff2da60b6705b02621dc204efa3c8b93a824cbd6` (its four
extensions blobs equal the working tree, so BASE=WT for all four dirty
targets and BASE=WT=HEAD for the clean leaf).

| Target | WT | HEAD | ITEM_BASELINE | State |
|---|---|---|---|---|
| `extensions/__init__.py` | `dc3ebdc2` | `dc3ebdc2` | `dc3ebdc2` | clean |
| `extensions/debug.py` | `7cf521f9` | `78e662f9` | `7cf521f9` | dirty |
| `extensions/error_policy.py` | `28b19d78` | `77b93f94` | `28b19d78` | dirty |
| `extensions/operation_state.py` | `276fdfb0` | `1acd9076` | `276fdfb0` | dirty |
| `extensions/resource_policy.py` | `2123cbef` | `4cd95703` | `2123cbef` | dirty |

Full blobs: WT init
`dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`, debug
`7cf521f94ca902daabfdaef0d0dbb6a63a3daa28`, error_policy
`28b19d78cfe6dadd4e5330c490876cb33410652b`, operation_state
`276fdfb04728fa9b1174c2c0dc73c7b489e99a9f`, resource_policy
`2123cbef8f634e8bcb8cb28dbd2cc551bbddf822`; HEAD debug
`78e662f9fa322a2ee378a746b8feb8fdfa72065e`, HEAD error_policy
`77b93f94acf83b18f00aecbc9b4a1915329cf4f6`, HEAD operation_state
`1acd90769e73a39c73c3e613d47c45245f16f0ad`, HEAD resource_policy
`4cd9570380b679fcdadf92d1f9f795a65255bb5d` (init identical).
WT line counts: init 35, debug 899 (HEAD 877), error_policy 446
(HEAD 481), operation_state 1007 (HEAD 1008), resource_policy 1765
(HEAD 1781).

## System trace

The folder owns the package's engine-seam enforcement surface: the
operation-binding mechanism every framework extension answers through
([ext-operation-state][ext-operation-state]), the response-side error
masking ([ext-error-policy][ext-error-policy]), the request-side
resource budget ([ext-resource-policy][ext-resource-policy]), the
development-only response diagnostic ([ext-debug][ext-debug]), and the
3-name leaf manifest ([ext-init][ext-init]). Everything else is composed
by name from outside the folder: policy objects from
[error-policy][error-policy] / [resource-policy][resource-policy],
handout/admission mechanics from [utils-policies][utils-policies], the
chain + runner + return seam from [schema][schema], the per-event seam
from [consumers][consumers], the optimizer consumer from
[optimizer-extension][optimizer-extension], budget/type/AST primitives
from [utils-typing][utils-typing] / [utils-context][utils-context] /
[utils-inputs][utils-inputs], the bind-spec bridge from
[mutations-fields][mutations-fields] / [mutations-sets][mutations-sets],
the AUTH-side nothing (no edge), and the root logger from
[package-init][package-init].

Population at WT (`ast.parse`, `len(ast.Module.body)` per file):
init 4 statements (docstring + 3 imports + `__all__`, 0 defs);
debug 32 module-level names (3 TypedDicts + 4 records/coordinator +
11 functions + 3 classes + 10 constants + `__all__`); error_policy 12
(10 functions + 1 class + `__all__`, plus the TypeVar); operation_state
35 (6 classes + 20 functions + 7 variables + `__all__`, plus 2 TypeVars);
resource_policy 37 (4 classes + 15 functions + 17 variables + `__all__`).
Connected sources read in full or at the cited bodies: all five
targets, the schema chain/runner/return-seam bodies, the consumers
per-event seam, the optimizer extension's bound half, every owner body
named in the census below, and each rejection counterpart body.
Searched population for second sites: the whole package
(`django_strawberry_framework/`, 121 `.py` files at WT), `tests/`,
and the fakeshop example suites.

### Attribution of the working-tree dirt (by diff content vs HEAD)

36 hunks across the four dirty files (`git diff HEAD`, enumerated):
debug 19, error_policy 8, operation_state 7, resource_policy 2. One
hunk is ledgered DRY work: error_policy `@@ -39,7 +39,10` (the
three-sites trigger clause, verbatim the `## Owned changes` adopted
orphan `subscription-per-event-error-masking` row; run-7 Hunk 1
confirmed). Thirty hunks are concurrent bug-hunt work (truth
migration: every `truth.*` read, the `utils/truth.py` import,
`# truth: ok` markers, `type() is` exactness; hostile-guard deletions:
the `_degraded` floor guard, the teardown `try`, the `_binds` guard,
both `_ValueBudget` `try` wrappers; `except` narrowings to
`(AttributeError, ImproperlyConfigured)`; bounded-collection hardening:
the `_collect_exceptions` early cap, the `_query_log_entries_since`
budget param + indexed tail, the `_build_payload` per-snapshot
remaining; precision-prose fixes: stash-gate version-dependence,
CHARACTERS-not-bytes, chain-peel counting, `_snapshots` accuracy).
Five hunks are prose-only and provenance-ambiguous (neither ledgered
nor hunt-shaped; behavior-neutral): debug `@@ -152` (marker comment),
`@@ -396` (docstring verb), `@@ -477` (docstring reword), `@@ -592`
(class-docstring first line), `@@ -729` (docstring verb). No hunk was
edited, reverted, or tidied by this item.

Consequence: any consolidation touching a hunt-dirtied line is
blocked-on-hunt (recorded per finding with its hunk, touching
nothing). All counts below are re-derived at WT bytes; where WT and
HEAD disagree the finding states both.

## Verification

### Matrix

Each axis discharged folder-wide against the targets' real WT surface.
A second site for any folder rule was swept package-wide, not just
among the five files.

**1. Cross-flavor policy mirroring.** The folder's deliberate
non-mirrors were re-checked: error masking (per-result rewrite, three
seams, one body) vs resource gating (pre-execution budget, four
hooks, one arming) vs debug capture (per-operation diagnostic, two
teardowns, one stash writer) vs optimizer binding (bound state +
plan cache). Shared machinery is still shared by call at every site
swept: handouts at `copy_policy` (6 calls, 3 files), admission at
`canonical_policy` / `_operation_policy`, masking at
`mask_execution_result` (3 seams), budget arm/disarm (1 pair),
verdict restatement (1 body, 2 positions), mode/nested reads (1
reader each), `unwrap_non_null` (1 def, 3 calls), the bind-spec
bridge (1 top-level + 3 nested calls), the leaf manifest (3
by-name rows). No flavor-local re-spelling found. One genuine
cross-file duplication CONFIRMED (the two fail-closed DEBUG reads;
FAM-1, blocked-on-hunt).

**2. Sync/async twins.** Seven `async def` spellings live in the
folder at WT, all in `operation_state.py`, all protocol members:
`_BoundScope.__aenter__/__aexit__` (dual-protocol adapters over one
binding primitive, twinhood justified in the class docstring under
principle 5), `_ResumedStream`'s four drive methods (one wrapper
line each over a distinct protocol call), and the runner's async
result collection (one scope over `super()`). Debug, error_policy,
and resource_policy carry ZERO `async def`: each hook is one sync
generator serving both colors (the engine enters sync hooks on the
async path too — stated at each owner). No `get_results_async`
exists anywhere in the package (debug publishes through sync
`get_results` alone). Zero `sync_to_async` calls in the folder (one
docstring prose mention); zero queryset execution (no `QuerySet`
token in debug/error_policy/operation_state; resource walks ASTs
and coerced values, never the ORM). No pair shares a body that
could drift silently, and no new twin appeared since the file
items. All separations justified; see FR-6.

**3. Derived rather than repeated knowledge.** Every shared
derivation is consumed by call or by imported constant at WT: the
delimiter pairs (1 table, 2 derived sets), the connection/edge
shape vocabulary (1 literal each), the meta-field names (spec
vocabulary, unchangeable — no obligation), the `ids` / `Upload` /
`ID` charge keys (def-vs-ref across the schema-derivation and
upstream boundaries, no importable owner — FR-4's neighbors),
`_NODE_IDS_ARGUMENT` excepted nowhere, the marker/strategy/bool
config records (1 authority each, distinct payloads), the
correlation id (1 minter, 1 caller), the truncation marker (1
constant, 1 primitive), the chain-peel ceiling (1 ceiling per
failure policy — typing raises, debug stops; FL-2's neighbor
census: 3 counted peels, trigger unfired). The `limit + 1`
evidence idiom stays three contracts (J4 re-verified; trigger
unfired — the debug slice caps are caps, not evidence reads). No
second spelling of any folder rule found.

**4. Inverse / round-trip pairs.** Five pairs, each complete in one
owner: acquire/release (refcounted coordinator, saved-value
restore), arm/disarm (1 budget pair, lease-closed), bind/unbind (1
primitive, both protocols), record/restate (1 record, republished
at 2 positions + the execute backstop), mask/log (1 replacement, 1
server record per masked error). The `AdmissionGuard.on_validate`
vs extension `on_validate` identical 2-line bodies are two
POSITIONS of one restatement (the guard exists to be last), not
two definitions — enforcement sites under the DRY.md vocabulary
precedent. No hand-rolled second half exists for any of them.

**5. Contracts restated in another medium.** Production +
spec-047/spec-048 (resource passes, masking seams, install
positions, payload caps) + independent oracles
(`tests/extensions/test_debug.py`, `test_operation_state.py`,
`tests/test_error_policy.py`, `tests/test_resource_policy.py`,
the live `test_error_policy_api.py` / `test_resource_policy_api.py`
/ `test_extension_isolation_api.py` suites) + projections
(module/class/hook docstrings, the leaf usage block). Oracles were
checked for independence, not re-run: wire keys spelled as
literals (`isSlow` pinned by literal), floor shapes pinned by
value, seam identity pinned by object comparison, chain positions
pinned by name. Hunt migrated several oracle files (concurrent
work); the remaining pins still read the behavior, not the owner.
Counts below count definitions only.

**6. Enforcement by omission.** Swept the folder's guard surface
member by member at WT: all four stateful extensions bind through
the mechanism (marker/guard/refused excluded with contract —
f54 R6 re-verified); every policy enforcement resolves per
operation (error per-use read, resource per-op arming, debug
per-op gate); masking covers all three seams (3/3 callers each
gate); admission precedes every validation extension on every
transport (parse-hook position + trailing guard + execute
backstop); the debug stash gate admits only executed results.
Deliberate omissions each carry a contract source: no per-operation
error budget (f13 R-i), no resource degrade floor (f13 R-j —
propagation is not publishing), no masking of hook failures on a
plain schema (documented limitation), no isolation for shared
instances on a raw schema (documented limitation). No member lacks
a guard its contract requires. No defect.

### Enumeration

Folder population census (instrument: `ast.parse` per file, counts in
System trace): 117 module-level names (init 1 + debug 32 + error_policy
12 + operation_state 35 + resource_policy 37). Assignment map (every
rule-bearing member lands in exactly one home; challenges below end in
the same homes):

- Cross-boundary CONFIRM (single owner outside the folder member,
  folder composes by call): operation-bound mechanism (4 consumer
  declarations + runner seam), policy handouts (1 call site here),
  policy admission (canonical + flavor bindings), resource arming
  reads (2 callers), masking cluster (1 body, 3 seams), carried mode
  (1 marker, 1 nested reader), coded-error shape (raises compose),
  logger (2 importers), `unwrap_non_null` (3 calls), bind-spec bridge
  (1 + 3 calls), DST keys + mirror + deadline (composed), leaf
  re-exports (3 by-name rows).
- Cross-boundary COUNT-2 CONFIRMED (new family, blocked-on-hunt):
  fail-closed DEBUG read (2 gates; FAM-1).
- Falsified-at-current-bytes (flagged, see Findings): typed-tail F7
  consumer leg (owner deleted by hunt; no row in this plan), f13 F4
  contract sentence (exact-type migration), f13 F7 caller census
  (1+4 → 1+3), J3 contract (measure-or-reject → propagate),
  opstate J1 trigger (FIRED — rationale is now hunt's truth module),
  folder contract refinements within held assignments (debug ×4,
  opstate F1 ×6, error floor/gate ×2).
- Folder-local CONFIRM (named as index rows for Worker-0): leaf
  manifest, debug opt-in, root-export rationale, eager shape,
  privacy omission, cursor capture, wire serializers, chain walk,
  caps + truncation, acknowledgement gate, debug bound state, error
  install prose, error manifest, runner scope + nested fact,
  bind/unbind lifecycle, streamed resumption, runner lifetime,
  pre-parse scan, document walk, value walk, bind-spec bridge,
  extension configuration, admission lifecycle, resource manifest
  (24 rows).
- Folder rejections (new or converged, with triggers): FR-2..FR-13
  below (12 rows).

### Challenges

Each change posited against the rule's own variation axes; the count
is authoritative definitions only (consumers, oracles, projections
listed in Findings, never counted). State is WT unless noted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | bound membership | a fifth bound extension kind | 1 (new declaration; base + runner discover it) | CONFIRM F1 |
| C2 | base refusal | reword the base string | 1 (base; 3 overrides stand) | CONFIRM F1 |
| C3 | binding mechanics | change lease terms or unwind | 1 (base module) | CONFIRM F1 |
| C4 | compat branch | accept a new assignment shape | 1 (setter + predicate, same owner) | CONFIRM F1 |
| C5 | resume registration | a second whole-op value registers | 1 (state registry; 1 caller follows) | CONFIRM F1 |
| C6 | factory behavior | validate inside construction | 0 existing (2 one-line overrides) | REJECT merge (R1) |
| C7 | state scratch | add a slot to one state | 1 (that state) | REJECT merge (R4) |
| C8 | config authorities | change one record type | 1 (that authority) | REJECT merge (R5) |
| C9 | copy handout | change the duplicate build | 1 (`copy_policy`; 6 calls follow) | CONFIRM F1 |
| C10 | error admission | change the gate | 1 (`schema_error_policy`; 2 callers follow) | CONFIRM shape, FLAG sentence |
| C11 | masking | change classification | 1 (owner; 3 seams follow) | CONFIRM F1 |
| C12 | whole floor | change the floor shape | 1 (owner; 3 callers follow) | CONFIRM shape, FLAG census |
| C13 | DEBUG read | a third read-failure mode | 2 (both gates move) | CONFIRM new family (blocked) |
| C14 | carried mode | change the marker contract | 1 (marker + reader; 2 constructions are enforcement sites) | CONFIRM family |
| C15 | nested fact | change nestedness | 1 (runner settle; 1 reader follows) | CONFIRM file-local |
| C16 | coded shape | change the extensions shape | 1 (owner; raises follow) | CONFIRM family |
| C17 | correlation id | mint per result not per error | 1 (`_masked`; minter follows) | CONFIRM file-local |
| C18 | original_error readers | capture deliberately-raised chains only | 1 (debug; masking stands) | REJECT merge (FR-2) |
| C19 | degrade floors | publish locations on the floor | 1 (error; debug stands) | REJECT merge (FR-3) |
| C20 | pagination pair | a size-bearing `limit:` arg | 1 (the pair; key set stands) | REJECT merge (FR-4) |
| C21 | exact-bool gates | admit bool subclasses | 9 (package idiom, no shared behavior) | REJECT merge (FR-5) |
| C22 | hook bodies | share one `on_operation` body | 0 shared (engine protocol; 3 enforcements) | REJECT merge (FR-6) |
| C23 | result shape gates | admit strawberry shapes to the stash | 1 (stash gate; mask gate stands) | REJECT merge (FR-7) |
| C24 | debug surfaces | drive both from one switch | 2 (response vs toolbar; postures oppose) | REJECT merge (FR-8) |
| C25 | enforcement halves | add a resource bound | 1 (resource; error stands) | REJECT merge (FR-9) |
| C26 | location retention | retain on the floor too | 1 now (single call) | REJECT helper (FR-10) |
| C27 | cycle guards | unify on one predicate | 2 domains (names vs identity) | REJECT merge (FR-11) |
| C28 | bounded reads | share one measure-or-truncate read | 2 contracts (collect-or-propagate vs cut-and-mark) | REJECT merge, FLAG contract |
| C29 | capture bracket | change restore semantics | 1 (coordinator) | CONFIRM file-local |
| C30 | wire keys | respell `isSlow` | 1 (serializer; oracle lists literal) | CONFIRM file-local |
| C31 | chain walk | a fourth counted peel | 3 counted now (trigger unfired) | CONFIRM file-local |
| C32 | payload caps | raise the text budget | 1 (constant; 2 passes follow) | CONFIRM file-local |
| C33 | ack gate | admit truthy strings | 1 (ctor gate; policy stands) | CONFIRM file-local |
| C34 | install prose | move the masker last | 0 here (1 at schema) | CONFIRM projection |
| C35 | error manifest | a sixth export | 1 (tuple; homes follow) | CONFIRM file-local |
| C36 | bind/unbind | change unwind order | 1 (lifecycle; adapters follow) | CONFIRM file-local |
| C37 | resumption | bind by another path | 1 (resume + registrar) | CONFIRM file-local |
| C38 | runner scopes | add a fifth scope | 1 (runner) | CONFIRM file-local |
| C39 | pre-parse scan | charge a new text bound | 1 (scan body) | CONFIRM file-local |
| C40 | spread accounting | charge once per fragment | 1 (walk) | CONFIRM file-local |
| C41 | reference accounting | charge-once cache | 1 (value budget; refused by contract) | CONFIRM file-local |
| C42 | relation classification | drop the spec bridge | 1 (bridge + family charge) | CONFIRM file-local |
| C43 | explicit holding | hand out the authority | 1 (copy-per-read property) | CONFIRM file-local |
| C44 | restate position | restate after `yield` | 2 positions, 1 pipe (enforcement sites) | CONFIRM file-local |
| C45 | leaf manifest | a 4th extension | 1 (home def; leaf row follows) | CONFIRM file-local |

## Findings

`Migration: none` and `Coupling: none` throughout (zero-edit folder
audit except FAM-1, which is confirmed-but-blocked; nothing lands
together) — stated once here, not per finding. Proofs are
`static-reviewed` throughout (imports, bodies composed by name,
single spanning reads, grep-verified absences over the 5-file and
package populations); ordering/transactional/async behavior rests on
the named pre-existing oracles, which this item neither weakens nor
re-runs. No finding carries an `execution-deferred` proof.

### FC-1 — operation-bound mechanism (CONFIRM consolidated)

- **Contract + variation.** One state object per (resolved extension,
  runner), reachable only through a task-local carrier while that
  runner owns it. Varies only by declaration (per-extension scratch
  shape, refusal wording).
- **Sites + roles.** *Definition*:
  [ext-operation-state][ext-operation-state] (carrier mint +
  recall-or-refuse, lease-on-weakref read, managed mark + compat
  drop, compat predicate, selection, refusal point, factory default,
  compat setter, resume registry, runner scopes — all present at WT,
  `276fdfb0`). *Consumers by declaration (4, production)*: debug
  (`607`), error_policy (`358`), resource_policy (`1480`),
  [optimizer-extension][optimizer-extension] (`902`); test probes
  (4, oracles, not members). *Runner seam*:
  [schema][schema]`::create_extensions_runner` builds
  `DjangoExtensionsRunner` by name (`1092`/`1112`). *Oracles*: the
  55 seam rows (f54) + live shared-entry matrices.
- **Challenges.** C1–C5 → 1 each at the owner or the owning
  declaration (re-derived: 4 consumer declarations; 3 refusal
  overrides + base; 1 resume caller at resource_policy `1632`;
  membership census 4 production + 0 new).
- **Owner + lifetime.** Indexed family owner; principle-4 fields as
  recorded at f54 (carriers, marks, compat state, runner-owned
  states). No stored derivation changed.
- **Behavioral proof.** `static-reviewed`. Rejects "a fifth
  production subclass exists" (census: 4 + base + runner + marker;
  marker/guard/refused excluded per R6, re-verified stateless /
  fresh-per-chain) and "a consumer copies the mechanism" (C2 moves
  the base only; `_new_operation_state` overrides are 1 line each).
- **Structural gate.** The pre-existing seam/isolation oracles (f54:
  no gate owed; unity rests on declarations + oracles).
- **R1–R7 triggers, re-derived at WT.** R1 (factory): overrides
  still 1-line constructions, no validation — unfired. R2
  (`__init__` settles): three record types under three validations —
  unfired. R3 (refusals): four per-subject strings, no shared
  template — unfired. R4 (states): disjoint scratch (`payload` +
  `snapshots` vs `stashes`) — unfired. R5 (authorities): three
  record types + three read postures — unfired. R6 (non-bound):
  marker construction-fixed, guard stateless, refused
  fresh-per-chain (`_refused_chain` builds new instances) — unfired.
  R7 (exact vs subclass): exact marker test intact
  (`type(...) is`, untouched); subclass test preserved through
  `truth.is_subclass` (hunt hunk `@@ -465`, same contract) —
  unfired.
- **Freshness.** All five targets as pinned; optimizer-extension WT
  `49346716`; schema WT `3b68d694`. f54's blobs (Oct 1) all differ
  from WT — this finding re-derives, never inherits.

### FC-2 — policy authority isolation (CONVERGE, two flags)

- **Contract + variation.** Per f13: handouts at `copy_policy`,
  admission at `canonical_policy`, resource reads, error admission,
  schema record, extension holding, masking seams, narrowing-only.
- **Sites + roles.** *Held at WT*: F1 (1 def; 6 calls in 3 files —
  re-derived identical call set to f13's HEAD census: the artifact's
  "5 files" is record slack, stable, not drift); F2 (1 def, same
  call shape); F3 (`_resolved_policy` 1 + 2 callers at `1622` +
  `1697`; arming pair 1; restatement positions 2; `_policy`
  copy-per-read intact; schema reader `_entry_resource_policy`
  intact at `1388`); F5/F6 (record + holding untouched — zero
  hunks); F8 (all three statements present at their owners —
  defs re-verified at WT `435` / `839` / `1548`).
- **Challenges.** C9 → 1; C10/C12 → 1 with flags (FF-2/FF-3).
- **Behavioral proof.** `static-reviewed` (censuses + bodies).
  Rejects "a second handout/admission/holding body appeared"
  (zero `object.__new__` policy twins; zero second authorities).
- **Structural gate.** The pre-existing tamper/identity/precedence
  pins (f13: no new gate owed).
- **Flags, not reopens.** F4's contract sentence ("`isinstance`
  gate with hostile-schema containment, two fallback arms") is
  stale at WT (exact-type gate, no containment — hunt hunk
  `@@ -293`); ownership holds (1 read, 2 callers). F7's
  `degraded_result` census (1+4) is stale (teardown-failure arm
  deleted — hunt hunk `@@ -458`; now 1+3). See FF-2, FF-3.
- **Freshness.** error_policy `28b19d78`; resource_policy
  `2123cbef`; [utils-policies][utils-policies] WT `ca9914b8`;
  [error-policy][error-policy] WT `b8c9c2e5`;
  [resource-policy][resource-policy] WT `0ec4e891`; schema
  `3b68d694`; [consumers][consumers] WT `69b60dba`.

### FC-3 — masking three seams (CONFIRM consolidated)

- **Contract + variation.** Each subscription event, and each
  returned result, masked exactly once by the operation's error
  policy. Varies on policy values and result shapes only.
- **Sites + roles.** *Definition*: the masking cluster in
  [ext-error-policy][ext-error-policy] (classifier, replacement,
  floors, gates, admission read, application — all single at WT).
  *Consumers (3/3 intact)*: teardown via `_process_result`
  (`410`), [consumers][consumers]`::_stop_aware_results` (policy
  resolved once at `1170`, gates per event at `1177`, mask at
  `1178`, function-local import preserving the channels-free
  graph), [schema][schema]`::_masked_return` (floor pre-seeded
  with the package default at `1176`, gates at `1179`, mask at
  `1181`, floor at `1187`). Gate callers: `masking_is_active` 3,
  `is_maskable_result` 3, `mask_execution_result` 3 — the same
  three seams. *Oracles*: package + live masking rows (independence
  holds: literals and identity pins).
- **Challenges.** C11 → 1. The family trigger (a fourth site or a
  restated classifier) is unfired: mask callers still 3,
  `_is_unexpected` still the single classifier.
- **Owner + lifetime.** Indexed owner; no stored derivation.
  Hunt deleted the teardown's whole-operation `try` (hunk
  `@@ -458`): a teardown failure now unwinds to upstream, whose
  post-teardown result is masked at the return seam — the family
  contract (each result masked exactly once) holds through the
  surviving seam, idempotent by construction.
- **Behavioral proof.** `static-reviewed` (3×3 caller census +
  bodies + the ledgered trigger clause intact at WT lines 41–44).
- **Structural gate.** None owed (family record: unity rests on
  the one-way import edge + trigger).
- **Freshness.** error_policy `28b19d78`; schema `3b68d694`;
  consumers `69b60dba`; opstate `276fdfb0` (teardown reads the
  bound context).

### FC-4 — carried executor mode (CONFIRM consolidated)

- **Contract + variation.** The executor mode travels on the chain
  it was built for (a marker member), read once by the runner,
  bound everywhere state binds. Varies on the `sync` flag only.
- **Sites + roles.** *Definition*: the marker
  (`_OperationModeMarker`, construction-fixed `mode`, no hooks)
  + the exact-type chain read (`_declared_operation_mode`) +
  the runner settle (`_scope`). *Producers (2 enforcement
  sites)*: admitted chain ([schema][schema] `1300`) + refused
  chain (`753`) — each chain declares its own mode, the DRY.md
  enforcement-site shape, not two definitions. *Readers*: the
  runner (binds), mode readers via
  [utils-execution-mode][utils-execution-mode] (composed by call).
  *Oracles*: mode-carried rows.
- **Challenges.** C14 → 1 (marker contract + reader; the two
  constructions follow as positions). C15 → 1 for the nested
  fact (runner settle; optimizer the single reader at
  `optimizer/extension.py:1093`).
- **Owner + lifetime.** Indexed family owner for the mode half;
  the nested/scope half is file-local (FL-4). No stored
  derivation beyond the per-runner scope object.
- **Behavioral proof.** `static-reviewed`. Rejects "mode is
  re-sampled per hook" (one chain read, memoized scope) and "a
  third construction site exists" (census: 2, both in schema).
- **Structural gate.** Pre-existing mode/nested rows.
- **Freshness.** opstate `276fdfb0`; schema `3b68d694`;
  execution-mode WT `b86a08cd`; optimizer-extension `49346716`.

### FC-5 — coded-error shape (CONFIRM consolidated)

- **Contract + variation.** Every coded error extensions map is
  built once, at the owner; rejections carry `code` (+ detail).
- **Sites + roles.** *Definition*:
  [utils-errors][utils-errors]`::coded_error_extensions` (f47;
  the AST census gate pins the single construction site).
  *Consumers here*: `ResourceLimitExceeded` raises (all pass
  bound/limit/charged/detail; none constructs the extensions map
  — 0 `coded_error_extensions` calls in the folder); the
  `FIELD_ERROR_CODE_TRUNCATED` code (defined once at
  utils-errors `117`, composed by [rest-framework][rest-framework]
  import — the `"truncated"` substring shared with the debug
  text marker is vocabulary coincidence, distinct subjects).
  *Excluded*: the error-policy correlation id (codeless support
  identifier, still minted per masked error in `_masked`,
  still not a rejection code — the standing rejection holds).
- **Challenges.** C16 → 1; C17 → 1.
- **Owner + lifetime.** Indexed owner; stateless construction.
- **Behavioral proof.** `static-reviewed` (0 construction calls
  in the folder; raise sites pass the 4-tuple; correlation path
  codeless).
- **Structural gate.** The f47 AST census gate (pre-existing).
- **Freshness.** resource_policy `2123cbef`; error_policy
  `28b19d78`; utils-errors WT `e9572ea9`; top-level
  resource_policy `0ec4e891`.

### FC-6 — logger single-sourcing (CONFIRM consolidated)

- **Contract + variation.** One package logger, defined once at
  the root, imported by name where a record is emitted.
- **Sites + roles.** *Definition*:
  [package-init][package-init] `logger` (`14`, the single
  `getLogger`). *Consumers here*: debug + error_policy (`from ..
  import logger`, each intact). *Deliberate absence*:
  resource_policy emits zero log records (typed rejections
  travel the envelope; nothing to log) and operation_state
  emits zero (every failure path raises, answers `None`, or
  unwinds — absence probe re-verified empty). The root
  `getLogger` gate pins the definition.
- **Challenges.** Posit a second logger → 0 (one `getLogger`
  in the package root; this folder follows by import).
- **Behavioral proof.** `static-reviewed` (import lines +
  absence probes + the root gate).
- **Freshness.** debug `7cf521f9`; error_policy `28b19d78`;
  package-init WT `b688e2fa`.

### FC-7 — walk, typing, and measure pairs (CONVERGE, all triggers unfired)

- **Contract + variation.** Six standing rejections plus one
  file-local composition, each re-derived at WT against both
  sides' bodies.
- **Sites + roles.**
  - `_variable_names` (deep every-variable value-AST iterator,
    resource_policy `1090`) vs
    [optimizer-selections][optimizer-selections]`::directive_variable_names`
    (skip/include-only cache-key set, `357`): populations
    unchanged, neither generalized. The
    [optimizer-extension][optimizer-extension] pagination check
    (`300`) is a per-argument predicate composing the selections
    primitive by call — not a value-AST walk — so the "third
    walk" trigger is unfired.
  - `typing-non-null-only-peel`: 1 def, still exactly 3 call
    sites (`536`, `1054`, `1082`), all in this file; lists kept
    at each. Full-peel rejection holds: 0 `unwrap_graphql_type`
    in this file; `get_named_type` (upstream primitive) used at
    5 sites.
  - Per-domain pair/sequence idioms: this file's `isinstance`
    pairs intact (no `base_container_values` import — 0 hits);
    the canonical families' triggers unfired.
  - Testing-client walk: `_assert_file_placeholders` still a
    single-path verifier vs this file's full-traversal charge;
    difference stands.
  - Directives: `validated_field_directives` still a
    construction-time shape validation vs per-request cost
    charging; difference stands.
  - Write-values: `unencodable_text_error` still reject-closed
    (untouched by hunt — 0 diff hits) vs `_charge_leaf`'s
    never-raise `surrogatepass` measure (untouched — 0 hunks);
    the "one policy needing both verdicts" trigger is unfired.
- **Challenges.** Each pair re-posed against its trigger; every
  count and population matches the standing record.
- **Behavioral proof.** `static-reviewed` (both bodies per pair
  + absence probes + the pagination-call-site read).
- **Freshness.** resource_policy `2123cbef`; selections WT
  `e14e6e30`; [utils-typing][utils-typing] WT `b7e69600`;
  [testing-client][testing-client] WT `3b122fd5`;
  [utils-directives][utils-directives] WT `23421f6b`;
  [utils-write-values][utils-write-values] WT `1dc426d4`;
  optimizer-extension `49346716`.

### FC-8 — lease, mode-read, and state pairs (CONVERGE, all triggers unfired)

- **Contract + variation.** Six standing rejections naming
  `operation_state.py`, each re-derived at WT.
- **Sites + roles.**
  - Execution-mode shared-reader / bind-close / async-vs-nested:
    `_bound_state` / `_live_scope` reads, `_bind` lifecycle, and
    `operation_is_nested` intact (zero hunks in those bodies);
    the [utils-execution-mode][utils-execution-mode] counterparts
    unchanged in contract; all three triggers unfired.
  - Operation-lease reader shape: 4 readers, 0 shared
    obligations — the lease read in `_bound_state` /
    `_already_bound` / `_live_scope` intact.
  - Boundary ContextVar: `_RUNNER_SCOPES` still the one
    innermost-runner variable; sibling ContextVars distinct by
    subject.
  - Sessions state: connection lifetime
    (`ConnectionActorState`) vs operation lifetime — intact,
    trigger unfired.
  - Id-filed lifecycle (f53 R4): `OperationLease` still
    revocation-only (one payload slot, zero dict/table —
    the "mutable ledger" prose names the explicitly separate
    `orders/sets.py::_NormalizationLedger`); the
    identity-keyed-table trigger is unfired.
- **Challenges.** Each pair re-posed against its trigger;
  every contract difference verified on current bodies.
- **Behavioral proof.** `static-reviewed` (lease body read in
  full; reader censuses; absence of new readers).
- **Freshness.** opstate `276fdfb0`; execution-mode `b86a08cd`;
  [utils-operation-lease][utils-operation-lease] WT `d1d272c5`.

### FC-9 — guard-absence and boundary pairs (CONVERGE, all triggers unfired)

- **Contract + variation.** Seven standing absence / asymmetry
  records naming this folder, each re-probed at WT.
- **Sites + roles.**
  - Awaitable disposal (opstate R1): 0 `isawaitable` /
    disposal / `SyncMisuseError` tokens — trigger unfired.
  - Soft-dependency guard (debug R1): 0 `require_*`, every
    import hard (stdlib, Django, graphql-core, typing_extensions,
    first-party) — trigger unfired.
  - One-sync-boundary (debug + opstate R2): 0 `sync_to_async`
    calls, 0 queryset execution — triggers unfired.
  - Sealed execution (error F4, resource F4, opstate
    non-membership): 0 `seal` / `QuerySet` tokens in error_policy
    and operation_state; resource walks ASTs, executes nothing —
    holds.
  - Shared `limit + 1` (J4): three contracts intact
    (bounded-read bound, evidence over-collection with the
    one-past read preserved through the hunt hunk, pagination
    probe row) + the `seconds + 1` cousin intact; the durable-home
    content (never-joined / BytesIO paragraphs) present in
    `_measured_by_bounded_read`'s docstring; the "new
    bounded-read measurement" trigger is unfired (the debug
    slice caps are caps, not evidence reads).
  - Errors correlation shape: `_masked` still mints a codeless
    identifier (body untouched); still not a rejection code.
  - R-i / R-j asymmetries: 0 budget vocabulary in
    extensions/error_policy.py; 0 floor vocabulary in
    extensions/resource_policy.py; the one WIP spec (`spec-050`,
    list-field arguments) requires no per-operation error state.
- **Challenges.** Each absence re-probed (all probes empty);
  each trigger re-posed, none fired.
- **Behavioral proof.** `static-reviewed` (empty-probe
  censuses with populations stated + home-paragraph read).
- **Freshness.** All five targets as pinned;
  [_request-body][_request-body] WT `5672658f`;
  utils-write-values `1dc426d4`; utils-errors `e9572ea9`.

### FAM-1 — fail-closed DEBUG read (CONFIRMED count 2, blocked-on-hunt)

- **Contract + variation.** `settings.DEBUG` read as exact-`True`,
  with an unreadable setting answering absent: deleting the
  attribute raises `AttributeError`, answering outside a
  configured Django process raises `ImproperlyConfigured` — both
  fail toward the safe direction. Varies on nothing; the two
  gates compose opposite polarities (permit vs active) plus
  their own ack/enabled clauses around the one read.
- **Sites + roles.** *Definitions (2)*:
  [ext-debug][ext-debug]`::DjangoDebugExtension._disclosure_permitted`
  (`765`–`771`: ack short-circuit, then the read) and
  [ext-error-policy][ext-error-policy]`::masking_is_active`
  (`242`–`246`: the read, then the `enabled` conjunction).
  Identical except tuples, identical read, identical rationale
  prose (both name the deleted-attribute + unconfigured-process
  failure modes). *Non-member*:
  [optimizer-nested-planner][optimizer-nested-planner] `703`
  (truthy log-level selection, fail-soft advisory — different
  contract, excluded with difference). *Oracles*: the
  DEBUG-matrix rows at both tiers (deleted-setting + debug +
  opt-out verdicts — independent: they drive the setting, never
  the gates).
- **Challenges.** C13 → 2: posit a third read-failure mode (or
  an exactness change) — both bodies move. Consumers, oracles,
  projections listed, never counted.
- **Owner + lifetime.** For the family item to decide (new
  family, no owner yet): the narrowest cohesive home both
  extensions can import without a sibling-machinery edge —
  candidates a new utils-adjacent micro-home or the settings
  owner; NOT either gate's own module (principle 7: no reversed
  dependency, no sibling-flavor machinery import). No stored
  derivation (per-operation read).
- **Migration.** Blocked: both bodies' exact lines are
  hunt-dirtied (debug hunk `@@ -742,13 +755,20`, error_policy
  hunk `@@ -239,29 +230,20`). Record the hunks, touch
  nothing. When unblocked: one exact-read predicate at the
  chosen owner; both gates compose it, keeping their
  polarity/ack/enabled compositions.
- **Distinct behavior.** Ack short-circuit (debug only),
  `enabled` conjunction (error only), gate polarities — all stay
  at the gates. The planner's truthy advisory read stays out.
- **Behavioral proof.** `static-reviewed` for the count (two
  identical reads, one world-fact). No equivalence proof is
  owed because nothing moves.
- **Structural gate.** Owed at consolidation time (a census
  pinning the single read); not now — nothing to pin yet.
- **Freshness.** debug `7cf521f9` / HEAD `78e662f9`;
  error_policy `28b19d78` / HEAD `77b93f94`; nested-planner WT
  `a9875bbb` (non-member read).

### FL-1 — leaf rules (CONFIRM file-local, 5 rows)

- **Contract + variation.** The leaf manifest (exactly three
  extension classes, by-name rows + mirroring `__all__`); the
  debug no-root-re-export rationale (opt-in diagnostic, never the
  default recipe); the error/resource root-export rationale (both
  installed on every schema, part of the default recipe); the
  eager shape (hard deps only, no lazy machinery); the helper +
  operation-state privacy omission (masking helpers and binding
  machinery deliberately unexported). Each varies on membership
  or rationale wording only.
- **Sites + roles.** *Definitions*: the three home classes
  (owned at their modules); *consumer rows here* (3 imports +
  `__all__`); *oracles*: explicit-name consumer imports (the
  heaviest in-package consumers import from submodule paths, so
  the leaf is convenience, never a hub) + root identity rows
  for the two root-exported names; *projections*: the usage
  block + rationale paragraphs.
- **Challenges.** C45 → 1 (home def; leaf row follows). The
  whole file is byte-identical across WT/HEAD/BASE
  (`dc3ebdc2`), so every member-artifact challenge replays
  unchanged.
- **Owner + lifetime.** Home modules (principle 6: this file
  composes by name). No stored derivation.
- **Behavioral proof.** `static-reviewed` (bindings are
  by-name imports — `is`-identical by construction of the
  import system; `__all__` names exactly the three).
- **Structural gate.** None owed (no exact-`__all__` oracle
  exists; every consumer imports explicitly, so a dropped
  binding fails loud as `ImportError` — gate economy per the
  member record, re-verified: still no `import *`, still no
  manifest assertion).
- **Freshness.** `dc3ebdc2` at all three states (clean).

### FL-2 — debug rules (CONFIRM file-local, 6 rows)

- **Contract + variation.** F1 overlap-safe cursor capture +
  log slice (refcounted coordinator keyed by wrapper object,
  saved-value restore, indexed tail slice); F2 wire serializers
  + threshold (graphene's six keys + triple, deliberate
  literals, 10s threshold); F3 chain walk + collection guards +
  stash gate (bounded best-effort `original_error` walk, bearer
  filter, graphql-core-only stash); F4 caps + truncation +
  degrades (per-row cut, earliest-rows kept, exceptions-first
  shared budget, per-row/per-list degrades); F5 acknowledgement
  gate + fail-closed lifecycle (exact-bool ctor gate, settled
  ack, per-operation disclosure gate, inert path); F6
  operation-bound state + refusal override (state subclass +
  per-subject refusal string, mechanism composed from the base).
- **Sites + roles.** *Definitions*: all in
  [ext-debug][ext-debug] (coordinator, serializers, walk,
  collectors, caps, ack authority, state, class — each single).
  *Consumers*: the two teardowns share the one stash writer;
  both row families share the one truncation primitive.
  *Oracles*: `tests/extensions/test_debug.py` (wire literals,
  caps, fail-closed rows — independent) + live debug rows.
  *Non-members classified*: `FIELD_ERROR_CODE_TRUNCATED`
  (error-code vocabulary vs text marker — vocabulary
  coincidence); `get_named_type` (unused here — no peel need).
- **Challenges.** C29–C33 → 1 each. C31's trigger census
  re-derived: 3 counted chain-peels (`unwrap_graphql_type`,
  `_callable_inspection_target`, `_terminal_original_error`),
  2 excluded narrow specializations, 1 one-layer helper, 1
  upstream primitive — "a fourth" unfired. The
  `_collect_exceptions` early cap and the caps-pass slice spell
  the same CONSTANT (one bound, two enforcement points — the
  early break bounds serialization work); hunt-dirtied,
  untouched.
- **Owner + lifetime.** This module throughout (each rule's
  narrowest home; the binding mechanism composed from the
  base). Snapshots + payload live per operation on the state.
- **Behavioral proof.** `static-reviewed` (single bodies +
  constant spellings + the stash-gate shape read).
- **Structural gate.** Pre-existing wire/cap/gate rows; no new
  gate owed.
- **Freshness.** debug WT `7cf521f9` / HEAD `78e662f9`;
  utils-typing `b7e69600` (peel census); utils-errors `e9572ea9`
  (code exclusion). Contract refinements within held
  assignments: see FF-6.

### FL-3 — error file-local records (CONFIRM, 2 rows)

- **Contract + variation.** R1 install-position + entry-authority
  prose (a PROJECTION: 0 definitions here — the FRONT position
  and the declaration-folding/subclass-refusal rules are owned
  at [schema][schema]); R2 leaf manifest (5 names: the class +
  four masking helpers; `schema_error_policy` deliberately
  public-by-import, the seam API posture shared with the
  resource module's walk functions).
- **Sites + roles.** *Definitions*: none here for R1 (prose
  mirrors `chain-admission`); the five home defs for R2.
  *Oracles*: chain-order rows (schema side) + explicit helper
  imports (consumers seam imports 4 names by path).
- **Challenges.** C34 → 0 here / 1 at schema (move the masker
  and this prose goes false — proves it defines nothing);
  C35 → 1 (a sixth export extends the tuple once).
- **Owner + lifetime.** Schema owns the chain; home defs own
  the helpers. No stored derivation.
- **Behavioral proof.** `static-reviewed` (prose verified
  against the chain builder; tuple mirrors same-file defs).
- **Structural gate.** The chain-order oracles (pre-existing).
- **Freshness.** error_policy `28b19d78` / HEAD `77b93f94`;
  schema `3b68d694`; consumers `69b60dba`.

### FL-4 — operation-state file-local rules (CONFIRM, 4 rows)

- **Contract + variation.** F2 runner scope + nested fact (one
  scope per runner settled at first binding; nested from a live
  outer lease; the mode half converges into the carried-mode
  family — FC-4); F3 bind/unbind lifecycle + dual-protocol
  adapters (one `_bind`/`_unbind` primitive, rebind-on-resume
  registry, `_BoundScope` sync/async wrappers); F4 streamed
  resumption + resume registrar (per-drive rebinding, adopted
  tokens, no token spanning a yield); F5 runner lifetime +
  operation/result/stream scopes (states owned by the runner,
  bindings at every readable scope).
- **Sites + roles.** *Definitions*: all in
  [ext-operation-state][ext-operation-state] (scope record,
  scope variable, bind/unbind, bound-scope, resumed-stream,
  runner — each single). *Consumers*: the four bound
  extensions (state + refusal + factory declarations); the
  runner seam (schema); the single resume-registration caller
  (resource arming). *Oracles*: `test_operation_state.py`
  (nested matrix, copied-context rows, scope rows) + live
  isolation rows.
- **Challenges.** C15, C36–C38 → 1 each. The `_BoundScope`
  enter/exit pairs and the four `_ResumedStream` drive methods
  are protocol members over one primitive each (principle 5 —
  stated at the owners).
- **Owner + lifetime.** This module (the only point seeing
  chain + context together). Principle-4 fields: scopes bound
  per operation, leases closed on unwind, states owned by the
  runner, resume bindings adopted per drive.
- **Behavioral proof.** `static-reviewed` (single primitives +
  reader censuses: nested 1, resume 1, runner constructions 1
  site + tests).
- **Structural gate.** Pre-existing nested/scope/resume rows;
  no new gate owed.
- **Freshness.** opstate `276fdfb0` / HEAD `1acd9076`; schema
  `3b68d694`; execution-mode `b86a08cd`; operation-lease
  `d1d272c5`.

### FL-5 — resource file-local rules (CONFIRM, 7 rows)

- **Contract + variation.** R1 pre-parse text scan (one lexer
  sweep, whole-document token + depth bounds, syntax errors
  left to the parser); R2 document walk (multi-root walk: shape
  on the selected operation, values everywhere validation
  converts — incl. `_DocumentWalk`, `_variable_names`,
  `_type_system_directives`, `_declared_input_type`, and the
  committed-drift `charge_fragment` + fragment counter);
  R3 value walk (iterative charge-every-reference walk with
  ancestor-path cycle guards, bind-spec + scalar-name family
  classification, upload accounting); R4 bind-spec bridge
  (graphql-core view → bind-time reverse map, top-level + nested
  maps); R5 extension configuration (acceptance canonicalization,
  authority holding, copy-per-read, resolve ladder); R6
  admission-verdict lifecycle (record + publish + empty-rules at
  parse, restate at validate ×2 positions, refuse at execute);
  R7 leaf manifest (1 name; walk/seam functions deliberately
  public-by-import).
- **Sites + roles.** *Definitions*: all in
  [ext-resource-policy][ext-resource-policy] (scan, walk + 7
  members + 5 shape helpers, value budget + 11 members, bridge fns,
  record + authority + property + ladder, verdict fn + 4 hooks,
  manifest — each single). *Second key-readers classified*:
  the `strawberry-definition` key is also read by the schema
  transaction seam — shared upstream vocabulary, distinct
  contracts (spec classification vs completion spanning).
  *Consumers*: arming hook (1 resolve), parse hook (1 walk),
  validate hooks (2 restates), schema (guard append).
  *Oracles*: `tests/test_resource_policy.py` + live budget
  rows (bounds pinned by rejection code + charged counts).
- **Challenges.** C39–C44 → 1 each (C44: 2 positions, 1 pipe —
  enforcement sites). `charge_fragment` (committed drift
  `3cc1b249`, absent at the run-7 blob): fragment entries
  sharing the field count instead of their own → 1
  (`_DocumentBudget`) — same home, no new row.
- **Owner + lifetime.** This module (the one place spending the
  budget). Budgets live per walk; the armed snapshot per
  operation under lease; the explicit record per construction.
- **Behavioral proof.** `static-reviewed` (single bodies +
  caller censuses: scan 1, walk 1, restate 2, record 1, arm 1).
- **Structural gate.** Pre-existing bound/verdict rows; no new
  gate owed.
- **Freshness.** resource_policy `2123cbef` / HEAD `4cd95703`;
  top-level resource_policy `0ec4e891`; schema `3b68d694`;
  mutations-fields WT `62a15151`; mutations-sets WT `6f2fa2f9`;
  utils-inputs WT `0b8d3daa`.

### FR-2 — shared `original_error` reader (REJECT, converge R4)

Considered: one shared reader for the debug capture side and the
masking side (the only two executable `original_error` readers in
the package — consumers/schema hits are prose, re-verified).
Contract difference: debug reads chains to PUBLISH unmasked
originals for diagnosis (best-effort walk, captures deliberately
raised chains too — its population is a SUPERSET of the masked
population); masking reads them to STRIP unexpected messages for
production (fail-closed classifier, deliberate chains travel
unchanged). Same GraphQL object, opposite responsibilities; the
only shared rule (debug listed after masking so its teardown runs
first) is owned by upstream LIFO semantics, not by either file.
C18 → 1 (debug moves alone). Trigger: a single pipeline owning
both capture and masking (one reader, two downstream maps).
Durable home: the debug class-docstring list-order passage + the
schema admitted-chain comment (both state it; error module
docstring restates the order from its side). Row named below.

### FR-3 — degrade floors (REJECT, new)

Considered: one shared degrade between the debug diagnostic
degrades (per-row drop, per-list empty/degraded, operation data
never at risk) and the error-policy floors (entry floor +
whole-response floor, data deliberately dropped when
uncertifiable). Contract difference: a diagnostic degrades by
publishing LESS of itself while the operation is untouched; a
policy floor degrades by publishing the policy message ALONE
while dropping the operation's data — opposite data handling,
opposite failure direction (keep-what-survives vs
nothing-uncertified). C19 → 1 (error moves alone). Trigger: a
degrade that must both preserve surviving diagnostic rows and
certify response data (no such seam exists). Durable home: this
finding + each floor's docstring (both state their direction).
Row named below.

### FR-4 — pagination pair vs cache-key set (REJECT, new)

Considered: `_page_bound`'s inline `("first", "last")` composing
`optimizer/extension.py::_PAGINATION_ARG_NAMES` (the 4-set
`{first, last, before, after}`, documented single source of
truth). Contract difference: size-bearing pair (only `first` /
`last` VALUES bound rows — cursors are not sizes, so composing
the 4-set would misread `before` / `after` as bounds) vs
cache-key family (all four affect plan identity). The sets differ
BY CONTRACT: a `search:` extension joins the key set without
touching the pair (stated at the set's own comment). C20 → 1
(the pair). Trigger: size-bearing membership defined as an
operation over the key family (or vice versa). Durable home:
this finding + the set's comment. Row named below.

### FR-5 — exact-bool gates (REJECT, new)

Considered: one shared exact-bool predicate for the debug ctor
gate (which cites `ErrorPolicy.__post_init__` as "the same rule")
and its siblings. Census: NINE `type(x) is not bool` sites in 7
files — a package-wide IDIOM, not a two-site rule (per-domain
pair-gates precedent: shared idiom, not a shared rule). Contract
difference per site: each gate carries its own subject, message,
and construction context (dataclass post-init vs extension ctor
vs knob validation); the shared content is one line + a raise
whose text is necessarily per-subject. Sharing it would save one
line per site at the cost of an import + indirection (principle
11: the abstraction should not exist). C21 → 9 (idiom). Trigger:
exact-bool gates gaining shared behavior beyond the one-line
predicate (a common message or contract). Durable home: this
finding (the debug cite stays a documentation cross-reference).
Row named below.

### FR-6 — extension hook twins (REJECT, new)

Considered: one shared body for the `on_operation` ×3 /
`on_execute` ×2 / `on_parse` + `on_validate` hook family.
Contract difference: the shared shape (sync generator, yield
once, setup-before / teardown-after) is the ENGINE's hook
protocol (upstream), while each body is a distinct enforcement
(bracket-and-capture vs mask-at-teardown vs arm / charge /
restate / refuse). C22 → 0 shared. Unifying any two would couple
independent enforcements across opposite lifecycle positions
(mask-last vs gate-first). Trigger: a package-owned hook body
shared by 2+ extensions (none exists — every hook body is
per-extension today). Durable home: this finding + each hook
docstring (each states its own position rule). Row named below.

### FR-7 — result-shape gates (REJECT, new)

Considered: one shared result-shape gate for the debug stash
gate (`isinstance(result, GraphQLExecutionResult)` — execution
only) and the masking shape gate (`is_maskable_result` — both
execution shapes). Contract difference: the stash gate EXCLUDES
strawberry pre-execution shapes (nothing executed → no `debug`
key — the no-key contract); the mask gate ADMITS them (harmless
no-op — admitted, contributes nothing to mask). Deliberately
different populations for different reasons. C23 → 1 (stash
gate). Trigger: the stash admitting shapes nothing executed, or
the mask gate excluding a shape carrying maskable errors.
Durable home: this finding + both gate docstrings (each states
its population). Row named below.

### FR-8 — debug-surface counterpart (REJECT, converge R5)

Considered: one "debug surface" rule spanning the response
extension and [middleware-debug-toolbar][middleware-debug-toolbar].
Contract difference, re-verified at WT: per-operation diagnostic
INSIDE the GraphQL response extensions map under the `debug` key
(engine seam, fail-closed under `DEBUG`, bounded text) vs
`debugToolbar` payload injected into tagged HTTP responses + HTML
(server-side seam, toolbar opt-in at leaf import, panels/history
store — key still `debugToolbar`, WT `301e43dc`). Different
transports, different keys, opposite gating postures. C24 → 2
(neither moves with the other). Trigger: a decision to drive
both surfaces from one switch (contradicts both fail-closed
postures today). Durable home: the debug module-docstring
paragraph 1 (still names the middleware as the counterpart).
Row named below.

### FR-9 — enforcement unification (REJECT, converge J1 ×3)

Considered: unifying the error and resource enforcement halves
(one extension + policy + install each). Contract difference,
corroborated from all three sides at WT: pre-execution budget
gating over `on_parse`/`on_validate` (admit-last position,
numeric bounds + deadline) vs post-execution message rewriting
in one `on_operation` teardown (mask-last position, string/bool
options + neutral message); `narrowed` exists only on the
resource side (deliberate — no maximums to tighten on the error
side). What already shares (ladders, copies, arming) composes by
name. C25 → 1 per side. Trigger: a third enforcement extension
arriving with the identical resolve→install→enforce shape —
still exactly two enforcement extensions at WT (debug and
optimizer are diagnostic/optimization, not enforcement).
Durable home: this finding + the error module's install-position
paragraph (records both directions) + the schema chain builder
(the resource module records only its own admission position —
the member "both modules" phrasing corrected here). Row named
below.

### FR-10 — location-field copy helper (REJECT, converge J2)

Considered: one helper producing the four retained location
fields (`nodes`, `source`, `positions`, `path`). Refused: all
four are kwargs of a SINGLE call in a SINGLE function
(`_masked`, WT `186`–`194`, body untouched) — one edit region,
no second site, no drift possible. C26 → 1 now. Trigger: a
second location-retaining call (e.g. the whole-result floor
growing locations) — re-verified absent (`GraphQLError(`
constructions in the folder: exactly 2, locations on one;
`ResourceLimitExceeded` takes bound/limit/charged/detail, no
locations). Durable home: this finding + `_masked`'s
"deliberately RETAINED" paragraph (states it). Row named below.

### FR-11 — cycle-guard unification (REJECT, converge J2)

Considered: one cycle predicate for the fragment spread-path
guard (name domain) and `_closes_a_cycle` (`is`-identity over
the ancestor path). Contract difference: fragment-name
membership on an immutable path set vs object-identity scan
over strong references — different domains, different
termination arguments, different callers (shape walk vs value
walk). The drift's new descents (`_variable_names`,
`_type_system_directives`) are finite AST descents over
tree-shaped nodes, not reference-charging walks — the "third
charge-every-reference walk" trigger is not met (run-7
classification re-verified). C27 → 2 domains. Trigger: a third
charge-every-reference walk, or one domain adopting the
other's predicate. Durable home: this finding + both guard
docstrings. Row named below.

### FR-12 — measure-or-truncate sharing (REJECT, converge J3)

Considered: one shared bounded-read between `_bounded_members`
/ `_charge_upload` and debug's `_truncate`. Refused at both
states: HEAD's typed refusals and WT's propagation both differ
from cut-and-mark by contract (collect-or-decide vs
shorten-and-label — a chargeable member list is not truncatable
text, and a diagnostic string is not a bound). C28 → 2
contracts. The WT contract (propagation) is hunt's concurrent
rewrite — see FF-4; the REFUSAL holds at both states (no
shared form appeared). Trigger: a second
measure-or-reject/propagate read, or a truncation that charges
a bound. Durable home: this finding + each reader's docstring.
Row named below.

### FR-13 — leaf-vs-root manifest (REJECT, converge init)

Considered: one manifest rule for the leaf `__all__` (3 names,
by-name rows, no pin oracle) and the root manifest (exact-tuple
oracle pins it). Contract difference: a re-export table
mirroring FOREIGN homes (consumer convenience; heaviest
in-package consumers bypass it via submodule paths) vs the
package surface table (load-bearing; pinned by identity rows).
Different subjects, different pin postures — the leaf-vs-leaf
sibling rejections (types/utils rows, trigger unfired,
`dc3ebdc2` clean) already exclude the sibling direction.
Trigger: the leaf gaining load-bearing consumers or a pin
oracle. Durable home: this finding + the leaf docstring (states
the convenience posture). Row named below.

### FF-1 — typed-tail consumer leg dissolved (FALSIFIED, record-only)

- **Prior assignment.** Debug F7: this file the "freshest
  consumer site" of `typed-rejection-value-tail` (2
  `describe_value` occurrences: import + `__init__` tail),
  owner `exceptions.py::describe_value`.
- **Tree evidence.** At WT: 0 `describe_value` occurrences in
  the folder (hunt hunk `@@ -697` replaced the import + call
  with `truth.describe`); 0 `describe_value` occurrences
  package-wide including tests (the owner is deleted); no
  `typed-rejection-value-tail` row exists in this plan's index
  (0 mentions). The consumer leg migrated to hunt's
  `utils/truth.py` (untracked, concurrent — untouched).
- **Verdict.** Assignment falsified. Closeout action: NONE in
  this plan (no row to retire — the cited row is not here);
  the member artifact's F7 no longer describes the tree.
  Collateral staleness recorded once here: error F3 /
  resource F2 / opstate checked-non-membership non-memberships
  now hold vacuously (nothing to be a member of); error J1's
  "tails share `describe_value`" sentence is stale prose in a
  closed artifact; opstate's "raises interpolate only
  `type(...).__name__`" detail now reads `truth.name` at one
  site (hunk `@@ -415`).
- **Freshness.** debug `7cf521f9`; [exceptions][exceptions] WT
  `9c02e960` (owner absent).

### FF-2 — f13 F4 contract sentence stale (FALSIFIED, record-only)

- **Prior assignment.** `schema_error_policy`: "admit under an
  `isinstance` gate with hostile-schema containment, two
  fallback arms."
- **Tree evidence.** At WT (hunt hunk `@@ -293`): exact-type
  gate (`truth.is_exact`), no containment, single expression.
  Ownership HOLDS: still 1 admission read, still 2 callers
  (`390` + consumers `1170`), fallback still the masking
  package policy.
- **Verdict.** Sentence falsified, assignment (single-owned
  at `schema_error_policy`) holds. Closeout action: update the
  family record's contract sentence when hunt lands. Row NOT
  reopened.
- **Freshness.** error_policy `28b19d78` / HEAD `77b93f94`.

### FF-3 — f13 F7 caller census stale (FALSIFIED, record-only)

- **Prior assignment.** `degraded_result`: "1 + 4 (mask failure,
  adopt failure, teardown failure, `_masked_return` floor)".
- **Tree evidence.** At WT: 3 callers (mask failure `341`,
  adopt failure `421`, return floor schema `1187`); the
  teardown-failure arm is deleted (hunt hunk `@@ -458`).
  Ownership HOLDS: still the single whole-response floor.
- **Verdict.** Census falsified (1+4 → 1+3), assignment holds.
  Closeout action: update the census when hunt lands. Row NOT
  reopened.
- **Freshness.** error_policy `28b19d78`; schema `3b68d694`.

### FF-4 — J3 contract replaced by propagation (FALSIFIED, record-only)

- **Prior assignment.** `_bounded_members` / `_charge_upload`:
  "a refusal to measure is a typed rejection of the bound
  being measured" (HEAD verdict, run-7).
- **Tree evidence.** At WT (hunt hunks `@@ -462`, `@@ -888`):
  container-iteration behavior propagates; the size read is
  unguarded-then-type-checked. Run-7 already recorded these
  hunks as concurrent-external J3 inversions ("the dirt is a
  deletion, not a second definition") — CONVERGED here: still
  1 `_bounded_members`, 1 size read, no second site.
- **Verdict.** Contract sentence falsified, file-local
  assignment + FR-12 refusal hold at both states. Closeout
  action: update the J3 record's contract sentence when hunt
  lands. Row NOT reopened.
- **Freshness.** resource_policy `2123cbef` / HEAD `4cd95703`.

### FF-5 — opstate J1 trigger FIRED by concurrent work (record-only)

- **Prior assignment.** Three type-identity predicates refuse
  unification; trigger: "a FOURTH identity predicate with the
  same hostile-`__class__` rationale — then the rationale (not
  the predicates) becomes a family."
- **Tree evidence.** The rationale HAS become a family:
  hunt's `utils/truth.py` (`is_subclass` / `is_exact` /
  `is_instance` / `name` / `describe`), composed by all three
  predicates (`_is_operation_bound`, `_declared_operation_mode`
  excepted — still raw `type() is`;
  `schema._is_extension` + `_is_resolvable_extension_entry`).
  The predicates' DISTINCTNESS still holds (subclass-accepting
  vs exact vs resolvability — each moves alone, re-verified on
  current bodies).
- **Verdict.** Trigger fired; outcome exists as concurrent
  hunt work (untracked module — untouched, unrowed). Closeout
  action: update J1's trigger clause (fired; rationale lives
  at `utils/truth.py`). Row NOT reopened.
- **Freshness.** opstate `276fdfb0`; schema `3b68d694`;
  truth uses in folder: exactly 5 call sites + 3 markers.

### FF-6 — folder contract refinements within held assignments (record-only)

Single-owner shapes hold; only sentences changed (all hunt
hunks, all untouched). Debug: `_collect_exceptions` gained the
early `_MAX_EXCEPTION_ROWS` cap (`@@ -360`); slice by indexed
tail + `budget` param (`@@ -396`); DEBUG gate by try/except
(`@@ -742` — the FAM-1 half); ctor bool gate by exact type
(`@@ -697`). Operation-state F1: six truth-migration bodies
(`@@ -415`, `@@ -454`, `@@ -465`, `@@ -473`, `@@ -573`,
`@@ -599`) — contracts refined (real-class reads, unguarded
schema read), composition by declaration intact. Error floor:
`_degraded` guard removal + `masking_is_active` enabled-read
simplification (`@@ -200`, `@@ -239` — the FAM-1 half).
Closeout action: refresh the member records' sentences when
hunt lands. No row reopened.

## Defects

None. Every claim checked while tracing held or is flagged
above: no docstring contradicts its body (the debug class
"reads `[]`" line is qualified by its own streaming
parenthetical; the module states the full rule), no flavor
lacks a guard its contract requires (axis 6 swept; the two
plain-schema limitations are documented at their owners), no
layering claim is contradicted by the imports (extensions
import leaves + the deferred schema edge only).

## Pending execution

No `proof:` entries (zero `execution-deferred` proofs; every
finding is `static-reviewed` by kind with ordering/async pinned
by the named pre-existing oracles). Gate entries for the final
gate (re-run as listed; results bind to the tree state at gate
time):

- `gate: uv run python scripts/workspace.py run dry/folder-extensions/consolidate -- basedpyright`
- `gate: uv run python scripts/workspace.py run dry/folder-extensions/consolidate -- basedpyright -p pyrightconfig.floor.json`
- `gate: uv run python scripts/workspace.py run dry/folder-extensions/consolidate -- python scripts/check_truthful_reads.py --check`
- `gate: uv run pytest -n0 tests/extensions/test_debug.py -q --no-cov`
- `gate: uv run pytest -n0 tests/extensions/test_operation_state.py -q --no-cov`
- `gate: uv run pytest -n0 tests/test_error_policy.py -q --no-cov`
- `gate: uv run pytest -n0 tests/test_resource_policy.py -q --no-cov`

Cells: `sharded` and `pg` stay `unverified` (the debug bracket
iterates `connections.all()` — connection/alias reach is real,
so inapplicable-by-construction is correctly NOT claimed). They
need the maintainer's separate word per the entry brief.

## Judgment

Zero-edit folder audit with one confirmed new family: every
cross-boundary composition still composes by call at WT (FC-1
through FC-9, all family triggers re-posed, none fired except
FF-5's, whose outcome is hunt's truth module); all 24
folder-local rules single-owned with proving challenges
(FL-1..FL-5, incl. the committed `charge_fragment` drift homed
in R2); 12 folder-level merges rejected with triggers
(FR-2..FR-13, seven converged with standing member records,
five new); one count-2 duplication CONFIRMED
(`fail-closed-debug-read`, FAM-1 — blocked-on-hunt, touching
nothing). Six falsification flags recorded for closeout
homing (FF-1..FF-6 — no row reopened, nothing re-applied).
`## Index rows for Worker-0` names 24 file-local + 12
rejection + 1 family row (owed at verification; no `## Families`
item is dispatchable while FAM-1 is blocked). No defects.

## Implementation (Worker-1)

Zero-edit item: no tracked file was created, modified, or
deleted. Item-scoped diff vs
`ff2da60b6705b02621dc204efa3c8b93a824cbd6` over the package,
tests, and examples trees is empty (0 bytes — the only path
written is the untracked artifact itself). All five WT
fingerprints re-derived identical to the pins. No `proof:`
runs (static reads only — `rg`, `ast.parse`, `git show`;
no pytest, no basedpyright, no workspace runs in this item).
Type gates ride the final gate via the `gate:` entries above.

## Index rows for Worker-0

Strict single-line rows for the plan's `## Responsibility index`
(37: 24 file-local + 12 rejected + 1 family). No `## Families`
item is dispatchable while FAM-1 is blocked-on-hunt.

| `extensions-leaf-manifest` | `django_strawberry_framework/extensions/__init__.py::__all__` (3-name mirror; defs in home modules) | `django_strawberry_framework/extensions/__init__.py` | Folder integration `extensions/` | file-local |
| `extensions-debug-opt-in` | `django_strawberry_framework/extensions/__init__.py` (module docstring: class-entry opt-in, no root re-export) | `django_strawberry_framework/extensions/__init__.py` | Folder integration `extensions/` | file-local |
| `extensions-error-resource-root-export` | `django_strawberry_framework/extensions/__init__.py` (module docstring: default-recipe rationale for both) | `django_strawberry_framework/extensions/__init__.py` | Folder integration `extensions/` | file-local |
| `extensions-eager-shape` | `django_strawberry_framework/extensions/__init__.py` (module docstring: hard deps, no lazy machinery) | `django_strawberry_framework/extensions/__init__.py` | Folder integration `extensions/` | file-local |
| `extensions-helper-privacy-omission` | `django_strawberry_framework/extensions/__init__.py` (module docstring: helpers + binding machinery unexported) | `django_strawberry_framework/extensions/__init__.py` | Folder integration `extensions/` | file-local |
| `extensions-cursor-capture` | `django_strawberry_framework/extensions/debug.py::_CursorCaptureCoordinator` (+ `::_query_log_entries_since`, indexed tail + budget) | `django_strawberry_framework/extensions/debug.py` | Folder integration `extensions/` | file-local |
| `extensions-wire-serializers` | `django_strawberry_framework/extensions/debug.py::_serialize_sql_row` (+ `::_serialize_exception`, `::_SLOW_QUERY_SECONDS`) | `django_strawberry_framework/extensions/debug.py` | Folder integration `extensions/` | file-local |
| `extensions-chain-walk` | `django_strawberry_framework/extensions/debug.py::_terminal_original_error` (+ `::_collect_exceptions`, `::DjangoDebugExtension._stash_payload_if_executed`) | `django_strawberry_framework/extensions/debug.py` | Folder integration `extensions/` | file-local |
| `extensions-payload-caps` | `django_strawberry_framework/extensions/debug.py::_apply_payload_caps` (+ `::_truncate`, `::_row_cost`, `::_build_payload`, `::_serialized_sql_row_or_dropped`) | `django_strawberry_framework/extensions/debug.py` | Folder integration `extensions/` | file-local |
| `extensions-acknowledgement-gate` | `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension` (+ `::_ACKNOWLEDGEMENT`, exact-bool ctor gate, disclosure gate) | `django_strawberry_framework/extensions/debug.py` | Folder integration `extensions/` | file-local |
| `extensions-debug-bound-state` | `django_strawberry_framework/extensions/debug.py::_DebugOperationState` (mechanism at `extensions/operation_state.py::_OperationBoundExtension`) | `django_strawberry_framework/extensions/debug.py` | Folder integration `extensions/` | file-local |
| `extensions-error-install-prose` | `django_strawberry_framework/extensions/error_policy.py` (install-position + entry-authority paragraphs; projection of `schema.py`, 0 defs here) | `django_strawberry_framework/extensions/error_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-error-manifest` | `django_strawberry_framework/extensions/error_policy.py::__all__` (5 names; `schema_error_policy` public-by-import) | `django_strawberry_framework/extensions/error_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-runner-scope-nested` | `django_strawberry_framework/extensions/operation_state.py::_RunnerScope` (+ `::operation_is_nested`; mode half in carried-mode family) | `django_strawberry_framework/extensions/operation_state.py` | Folder integration `extensions/` | file-local |
| `extensions-bind-lifecycle` | `django_strawberry_framework/extensions/operation_state.py::_bind` (+ `::_unbind`, `::_BoundScope`, `::OperationState.rebind_on_resume`) | `django_strawberry_framework/extensions/operation_state.py` | Folder integration `extensions/` | file-local |
| `extensions-streamed-resumption` | `django_strawberry_framework/extensions/operation_state.py::_ResumedStream` (+ `::DjangoExtensionsRunner.resumed`, `::_register_resumed_binding`) | `django_strawberry_framework/extensions/operation_state.py` | Folder integration `extensions/` | file-local |
| `extensions-runner-lifetime` | `django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner` (+ `::_operation_states`, scope methods) | `django_strawberry_framework/extensions/operation_state.py` | Folder integration `extensions/` | file-local |
| `extensions-pre-parse-scan` | `django_strawberry_framework/extensions/resource_policy.py::scan_document_text` (+ delimiter table + derived sets) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-document-walk` | `django_strawberry_framework/extensions/resource_policy.py::charge_document` (+ `::_DocumentWalk`, `::_variable_names`, `::_type_system_directives`, `::_declared_input_type`, shape helpers, `::_DocumentBudget`) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-value-walk` | `django_strawberry_framework/extensions/resource_policy.py::_ValueBudget` (+ `::_closes_a_cycle`, `::_EXACT_SEQUENCE_TYPES`, scalar/id/upload/`ids` vocabulary) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-bind-spec-bridge` | `django_strawberry_framework/extensions/resource_policy.py::_mutation_input_specs` (+ `::_nested_specs_map`, `::_STRAWBERRY_DEFINITION_BACKREF`) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-explicit-holding` | `django_strawberry_framework/extensions/resource_policy.py::_EXPLICIT_POLICY` (+ `::_AcceptedPolicy`, acceptance canonicalization, copy-per-read `_policy`) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-admission-lifecycle` | `django_strawberry_framework/extensions/resource_policy.py::restate_admission_verdict` (+ `::DjangoResourcePolicyExtension` hooks, `::AdmissionGuard`) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-resource-manifest` | `django_strawberry_framework/extensions/resource_policy.py::__all__` (1 name; walk/seam fns public-by-import) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | file-local |
| `extensions-original-error-reader` | `django_strawberry_framework/extensions/debug.py::_terminal_original_error` (rejection recorded here; CONVERGE with File `extensions/debug.py` R4 — publish-unmasked vs strip-unexpected; trigger: one pipeline owning both) | `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/extensions/error_policy.py` | Folder integration `extensions/` | rejected |
| `extensions-degrade-floors` | `django_strawberry_framework/extensions/error_policy.py::degraded_result` (rejection recorded here; keep-what-survives vs nothing-uncertified; trigger: a degrade needing both) | `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/extensions/error_policy.py` | Folder integration `extensions/` | rejected |
| `extensions-pagination-pair-vs-key-set` | `django_strawberry_framework/extensions/resource_policy.py::_page_bound` (rejection recorded here; size-bearing pair vs cache-key family; trigger: membership defined as an operation over the other) | `django_strawberry_framework/extensions/resource_policy.py`, `django_strawberry_framework/optimizer/extension.py` | Folder integration `extensions/` | rejected |
| `extensions-exact-bool-idiom` | `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension.__init__` (rejection recorded here; 9-site package idiom, one line + per-subject raise; trigger: gates gaining shared behavior) | `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/error_policy.py`, `django_strawberry_framework/resource_policy.py`, `django_strawberry_framework/conf.py`, `django_strawberry_framework/optimizer/hints.py`, `django_strawberry_framework/utils/querysets.py`, `django_strawberry_framework/utils/relations.py` | Folder integration `extensions/` | rejected |
| `extensions-hook-twins` | `django_strawberry_framework/extensions/error_policy.py::DjangoErrorPolicyExtension.on_operation` (rejection recorded here; engine hook protocol, per-extension enforcements; trigger: a package-owned body shared by 2+ extensions) | `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/extensions/error_policy.py`, `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | rejected |
| `extensions-shape-gates` | `django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._stash_payload_if_executed` (rejection recorded here; execution-only stash vs both-shapes mask; trigger: either gate admitting the other's excluded population) | `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/extensions/error_policy.py` | Folder integration `extensions/` | rejected |
| `extensions-debug-surface-split` | `django_strawberry_framework/extensions/debug.py` (rejection recorded here; CONVERGE with File `extensions/debug.py` R5 — response `debug` vs server-side `debugToolbar`; trigger: one switch driving both) | `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/middleware/debug_toolbar.py` | Folder integration `extensions/` | rejected |
| `extensions-enforcement-unification` | `django_strawberry_framework/extensions/error_policy.py` (rejection recorded here; CONVERGE with error J1 + opstate J2 + resource J1 — gate-first vs mask-last; trigger: a third enforcement extension) | `django_strawberry_framework/extensions/error_policy.py`, `django_strawberry_framework/extensions/resource_policy.py`, `django_strawberry_framework/extensions/operation_state.py` | Folder integration `extensions/` | rejected |
| `extensions-location-copy` | `django_strawberry_framework/extensions/error_policy.py::_masked` (rejection recorded here; CONVERGE with error J2 — single call, no second site; trigger: a second location-retaining call) | `django_strawberry_framework/extensions/error_policy.py` | Folder integration `extensions/` | rejected |
| `extensions-cycle-guards` | `django_strawberry_framework/extensions/resource_policy.py::_closes_a_cycle` (rejection recorded here; CONVERGE with resource J2 — name domain vs identity domain; trigger: a third charge-every-reference walk) | `django_strawberry_framework/extensions/resource_policy.py` | Folder integration `extensions/` | rejected |
| `extensions-measure-vs-truncate` | `django_strawberry_framework/extensions/resource_policy.py::_ValueBudget._bounded_members` (rejection recorded here; CONVERGE with resource J3 — collect-or-decide vs cut-and-mark, both states; trigger: a second measure read or a charging truncation) | `django_strawberry_framework/extensions/resource_policy.py`, `django_strawberry_framework/extensions/debug.py` | Folder integration `extensions/` | rejected |
| `extensions-leaf-vs-root-manifest` | `django_strawberry_framework/extensions/__init__.py::__all__` (rejection recorded here; CONVERGE with File `extensions/__init__.py` package-root-public-surface — convenience vs load-bearing; trigger: load-bearing leaf consumers or a pin oracle) | `django_strawberry_framework/extensions/__init__.py`, `django_strawberry_framework/__init__.py` | Folder integration `extensions/` | rejected |
| `fail-closed-debug-read` | TBD by family item (candidates: new utils-adjacent micro-home; NOT either gate's module) | `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/extensions/error_policy.py` | Family `fail-closed-debug-read` | open (blocked-on-hunt: debug `@@ -742,13 +755,20` + error_policy `@@ -239,29 +230,20`; no Families item until unblocked) |

Corrections to existing rows: none. Every standing row naming this
folder was re-derived trigger-by-trigger; censuses either match
(`copy_policy` 6 calls, `unwrap_non_null` 3 calls, `is_maskable_result`
3 callers, `_variable_names` populations) or are flagged above as
record updates for closeout homing (FF-2/FF-3 — no plan text names
the stale figures, so no correction is owed).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[package-init]: ../../django_strawberry_framework/__init__.py

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[_request-body]: ../../django_strawberry_framework/_request_body.py
[consumers]: ../../django_strawberry_framework/consumers.py
[error-policy]: ../../django_strawberry_framework/error_policy.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[ext-debug]: ../../django_strawberry_framework/extensions/debug.py
[ext-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[ext-init]: ../../django_strawberry_framework/extensions/__init__.py
[ext-operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[ext-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-selections]: ../../django_strawberry_framework/optimizer/selections.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[rest-framework]: ../../django_strawberry_framework/rest_framework/resolvers.py
[schema]: ../../django_strawberry_framework/schema.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[utils-context]: ../../django_strawberry_framework/utils/context.py
[utils-directives]: ../../django_strawberry_framework/utils/directives.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-operation-lease]: ../../django_strawberry_framework/utils/operation_lease.py
[utils-policies]: ../../django_strawberry_framework/utils/policies.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Recorded before opening `## Findings` (only the plan row, the
artifact's headings/`## Pins and fingerprints` block, and the
`## Index rows for Worker-0` row titles were seen; every count
below is re-derived from source reads and `rg` censuses run by
Worker-2).

### Own surface census (AST `ast.Module.body`, Worker-2 run)

- `extensions/__init__.py`: 1 module-level definition
  (`__all__`) + 3 re-exported names.
- `extensions/debug.py`: 32 top-level definitions.
- `extensions/error_policy.py`: 12 top-level definitions.
- `extensions/operation_state.py`: 35 top-level definitions.
- `extensions/resource_policy.py`: 37 top-level definitions.

### Own cross-boundary composition checks (all by-name, all hold)

- C1 — operation-bound mechanism. Owner
  `extensions/operation_state.py::_OperationBoundExtension`.
  Consumers by declaration: the three folder extensions plus
  `optimizer/extension.py::DjangoOptimizerExtension` (fourth
  subclass, confirmed by `rg`). `AdmissionGuard` extends
  `SchemaExtension` directly — different contract (fresh
  per-chain instance, no per-operation state), not a fifth
  definition. Count 1.
- C2 — policy authority. Folder sites consume
  `utils/policies.py::canonical_policy` /
  `copy_policy` / `_operation_policy` and the
  `_PACKAGE_*` fallbacks by name
  (`schema_error_policy`, `_resolved_policy`,
  `_policy`, `__init__` canonicalization). No
  second admission/handout body in the folder. Count 1
  (owner outside the folder).
- C3 — masking seams. `mask_execution_result` /
  `is_maskable_result` / `masking_is_active` /
  `schema_error_policy` / `degraded_result` owned
  once in `extensions/error_policy.py`; consumers by
  name in `schema.py::_masked_return` and
  `consumers.py::_stop_aware_results` (confirmed by
  `rg`: no other call sites). Count 1.
- C4 — executor mode. `_OperationModeMarker` /
  `_declared_operation_mode` compose
  `utils/execution_mode.py::bind_operation_mode` /
  `OperationMode` by name. Count 1.
- C5 — coded-error shape.
  `extensions/resource_policy.py` raises
  `ResourceLimitExceeded` (owned in
  `resource_policy.py`, shaped by
  `utils/errors.py::coded_error_extensions`); the
  folder defines no second coded shape. Consumer
  only.
- C6 — package logger. `debug.py` and
  `error_policy.py` both `from .. import logger`;
  no second `getLogger` in the folder. Count 1
  (owner at root).
- C7 — typing/measure consumers.
  `unwrap_non_null` (3 call sites incl. folder),
  `_variable_names` (folder) vs the optimizer
  cache-key variable walk: different populations
  (every-variable iterator vs skip/include set).
  Prior rejection stands unless its trigger fired;
  trigger check owed in reconciliation.
- C8 — lease/mode-read/state readers.
  `OperationLease`, mode readers, and the
  operation-state carrier are consumed, not
  redefined, in the folder. Prior rejections stand
  unless triggers fired.
- C9 — standing guard idioms (shared-except J1,
  shared exact-type J2, limit+1 J4). Each folder
  site keeps its own pair/gate; triggers re-posed
  in reconciliation.

### Own folder-local census (each count 1 unless noted)

Debug (13): graphene wire serializers + slow
threshold; exception triple; `original_error`
chain walk (cycle set + hop ceiling +
best-effort stop); bearer filter + row cap;
query-log window read (clamp + budget); payload
caps ladder (truncate, row-cap, exceptions-first
budget, stop-not-skip); per-row + per-list
degrade pair; overlap-safe coordinator
(refcount, saved-value restore); acknowledgement
record + exact-bool ctor gate; disclosure gate
minus the DEBUG read; two-teardown stash +
pure `get_results`; per-operation capture state.
Error (9): structural classifier; masked
replacement (retained locations + correlation +
server log); per-entry + whole-response floors;
shape gate; materialize-then-mask with
identity-return + shallow copy; per-entry
degrade; schema policy resolution with
exact-type gate; teardown adoption with degrade
fallback; masking composition minus the DEBUG
read. Operation-state (10): carrier-per-extension
+ lease-on-weakref model; one-way
package-managed mark; runner scope + nested
settlement at first binding; mode marker in
chain; compatibility branch; resume registrar +
`rebind_on_resume`; `_ResumedStream`
per-drive rebinding; single-body sync/async
`_BoundScope`; runner scope coverage
(operation/stream/resumed/results×2);
reconstruction-refusal base + per-subclass
messages (one mechanism, four wordings — merge
rejected: each names its own replaced state).
Resource (16): pre-parse token/depth scan;
delimiter-pair derivation; value-budget walk;
bounded member enumeration; list-family
classification ladder; relation-id dual
counter; leaf/file charging; document/shape
walk; collection accounting (page bound +
connection test + edges exemption); admission
verdict record/publish/restate across four
hooks + guard; policy resolution ladder
(explicit copy, schema, package); explicit-policy
record + accept-time canonicalization;
`on_operation` arming scope; mutation spec
bridge; `_closes_a_cycle` (identity domain) vs
spread-path guard (name domain) — two guards,
merge rejected. Leaf (1 grouped): eager
re-export shape + root/debug-exclusion prose +
unexported-helpers omission. Total distinct
folder-local rules by Worker-2's cut: 49; the
count differs from any coarser grouping only by
cut, and reconciliation maps every member.

### Own FAM-1 assessment (`fail-closed-debug-read`)

Two definitions, no more: `rg` for
`except \(AttributeError, ImproperlyConfigured\)`
returns exactly the two folder sites
(`extensions/error_policy.py::masking_is_active`
WT lines 242-246,
`extensions/debug.py::_disclosure_permitted` WT
lines 765-771). Both spell one rule: a `DEBUG`
that cannot be read fails closed
(`debug is not True` / `return False`), and only
the exact boolean `True` opens the permissive
path. Challenges (all count 2): a third
unreadable-reason exception; a settings proxy
with different failure modes; an exact-`True`
vs truthy semantics change. Exclusion:
`optimizer/nested_planner.py` line 703
truthiness read selects a log level — no
fail-closed contract, different rule. Owner
Worker-2 would choose: a new small helper in
`utils/` returning "DEBUG is exactly True,
unreadable reads False", composed as
`enabled and not debug()` /
`acknowledged or debug()`. Block: BOTH call
sites sit inside working-tree hunks the
`git diff HEAD` attributes by content to the bug
hunt (except-arm narrowing + `getattr`-to-`try`
rewrite; the `## Owned changes` ledger carries
no row covering either hunk — its one
extensions row is the adopted three-sites
docstring). Every consolidation shape edits at
least one call site, so no shape avoids the
hunt dirt: blocked-on-hunt is correct, and the
row must transcribe unticked + blocked.

### Own rejected-merge list (12, each with trigger)

M1 shared `original_error` reader (direct
fail-closed read vs bearer filter vs
log-best-effort `getattr`): three contracts,
reject. M2 degrade floors (keep-what-survives
debug rows vs nothing-uncertified error
floors): reject. M3 exact-bool/exact-type gates
(package idiom, per-subject raises): reject.
M4 engine hook twins (`on_operation` etc.
across extensions; `_BoundScope` enter/exit
pairs): engine protocol, reject. M5
result-shape gates (stash `isinstance` vs
`is_maskable_result` vs `_binds_operation_state`):
different admitted populations, reject. M6
debug vs `middleware/debug_toolbar.py`
(in-response vs server-side): reject. M7
shared-except driver: per-site pairs differ,
reject. M8 `PrivateAuthority` records
(acknowledgement vs explicit policy vs
carriers vs managed flag): different payloads
and lifetimes, reject. M9
`_reconstruction_refusal` wordings (4 sites):
reject. M10 leaf-vs-root manifest: converge
prior rejection. M11 cycle-guard unification
(identity vs name vs hop-ceiling+identity):
reject. M12 truncate/measure sharing
(`_truncate` vs `_bounded_members` vs leaf
sizes): reject.

### Questions carried into reconciliation

Q1 — `schema_error_policy` uses an exact-type
gate while `resource_policy._resolved_policy`
uses `isinstance`: is the asymmetry recorded
with its reason (schema-construction
validation vs standalone fallback)? Q2 — does
every claimed file-local row carry a proving
challenge that names the searched population?
Q3 — do the six falsification flags each carry
evidence and a correct non-reopening per the
standing instruction? Q4 — is the `gate:` list
complete (type gates + final witness) with no
owed `proof:`?

### Reconciliation (Worker-2, after reading `## Findings`)

Zero-edit confirmed twice: `git diff
ff2da60b6705b02621dc204efa3c8b93a824cbd6 --
django_strawberry_framework tests examples`
is empty (the only post-baseline tracked
change is Worker-0's concurrent plan
bookkeeping in `docs/dry/dry-0_0_15.md`,
out of scope), and no untracked file exists
under `django_strawberry_framework/extensions/`.
The WT-vs-HEAD dirt (36 hunks: 19/8/7/2,
recounted by Worker-2) attributes by content
exactly as the artifact states: 1 ledgered
DRY docstring hunk, 30 hunt-shaped hunks,
5 behavior-neutral prose hunks. HEAD
`23b5f421` unmoved. Touched-path set for
ruff/AGENTS.md-prose purposes: EMPTY
(zero-edit; no run, nothing to violate;
raw `path:NN` in the artifact is permitted
per-cycle scratch).

Surface census: Worker-2's AST counts match
the artifact exactly (1/32/12/35/37 =
117). Cross-boundary checks C1–C9 match
FC-1–FC-9 one for one; every caller census
re-derived identical (masking 3×3,
`copy_policy` 6 calls / 3 files,
`unwrap_non_null` 3 calls, `degraded_result`
1+3 at WT vs 1+4 at HEAD, 4 probe
subclasses, 7 `async def` all in
operation_state, 0 `get_results_async`
package-wide, 9 exact-bool sites / 7 files,
exactly 2 `GraphQLError(` constructions,
3 counted chain-peels). All 22
cross-boundary freshness fingerprints
re-derived identical; the 5 target pins
match the dispatch pins.

Folder-local cut: Worker-2's 49-rule cut
vs the artifact's 24 rows is grouping only —
every one of Worker-2's 49 members lands in
exactly one artifact home (consolidated
family, FAM-1, file-local row, or
rejection); the error/operation-state
members live mostly in already-consolidated
families (f13, f47, f54, masking), which
correctly takes them out of the file-local
rows. Rejected merges M1–M12 match FR-2…FR-13
(M8/M9 live in FC-1 R5/R3, correctly
unrowed as f54 members; FR-4/FR-10 are
Worker-1 finds Worker-2 confirms on bodies).
The package-wide shared-except J1 trigger is
implicitly discharged (no folder `except`
site shares a contract — pairs range over
`(AttributeError, ImproperlyConfigured)`,
bare `Exception`, `GraphQLError`,
`(ValueError, RuntimeError)`,
`suppress(RuntimeError)`, `BaseException`
unwind); Worker-2 re-derives the rejection
independently. No consolidation missed.

FAM-1: full agreement — count 2 (the
`except (AttributeError,
ImproperlyConfigured)` census returns
exactly the two gates), planner exclusion
correct (truthy log-level read, no
fail-closed contract), owner direction
agrees (utils-adjacent micro-home, not
either gate's module), and the
blocked-on-hunt verdict is correct: both
call sites sit inside hunt-attributed hunks
(`@@ -742` / `@@ -239`), the ledger covers
neither, and every consolidation shape edits
at least one call site.

FF-1…FF-6: each flag's evidence re-verified
(0 `describe_value` package-wide incl.
tests; 0 plan mentions; exact-type hunk +
2 callers; HEAD 1+4 / WT 1+3;
propagation hunks; truth composition with
`_declared_operation_mode` still raw
`type() is`; 5 truth call sites + 3
markers; all FF-6 hunks present) and each
non-reopening is correct per the standing
instruction — ownership holds in every
case, only record sentences went stale,
and FF-5's fired trigger follows the
established blocked pattern (outcome is
untracked hunt work, no HEAD blob, same as
the `utils/truth.py` precedent).

Q1 (exact-type vs `isinstance` asymmetry
between `schema_error_policy` and
`_resolved_policy`): observed, NOT a
defect. The supported DjangoSchema path
canonicalizes to exact `ResourcePolicy`
before any bound is read
(`begin_resource_budget` arms
`_operation_policy` only); the `isinstance`
leniency bites solely for a consumer-set
attr on a raw schema, i.e. consumer-vs-self,
outside the trust boundary. Both postures
defensible; no `## Defects` entry owed.
Q2: every file-local row carries its
challenge (leaf rationale rows via the
byte-identical replay claim + C45; R7 via
the same-file mirror + 0 `import *` —
challenge implied, see REVISE-2). Q3: yes
(above). Q4: the 7 `gate:` entries are
complete and correctly typed (3 type gates
+ 4 oracle files; public-types/ruff/commas
correctly absent for zero-edit; live suites
ride the final gate; no `proof:` owed —
Worker-2's own runs close the gap).

Cells: the honesty is right and complete.
The debug bracket iterates
`connections.all()` (real alias reach) and
the payload carries backend-interpolated
SQL, so inapplicable-by-construction is
correctly NOT claimed; `sharded`/`pg` stay
`unverified` pending the maintainer's word,
exactly per DRY.md "Tests".

Worker-1's zero execution is adequate for
this zero-edit audit (static-review kind +
named unweakened oracles, the verified
auth-folder pattern), and Worker-2
compensated with own execution: 481/481
oracle tests green plus all three type
gates green in the verify-1 workspace copy
(run ids `dry-20261009T235849-183f46`
(tests), `dry-20261009T235916-06fbb0`
(basedpyright: 0/0/0),
`dry-20261010T000054-30777f` (floor:
0/0/0), `dry-20261010T000207-65e8f4`
(truthful-reads: 0 errors); copy fresh,
shared tree unmoved).

REVISE-1 (record accuracy, verdict
unaffected): FC-9's "0 budget vocabulary
in extensions/error_policy.py" is
overstated — `budget` occurs once, at WT
line 65 (counterpart-describing prose in
the install-position paragraph, not
machinery). The supported claim (R-i: no
per-operation error budget) still holds.
REVISE-2 (record completeness, verdict
unaffected): the R7 resource-manifest row
has no dedicated `### Challenges` row
(its proof is the same-file mirror + 0
`import *`, both verified). Neither note
propagates to any index row.

### Index-row rulings (Worker-2, all 37)

File-local (24) — all ENDORSE:
`extensions-leaf-manifest`,
`extensions-debug-opt-in`,
`extensions-error-resource-root-export`,
`extensions-eager-shape`,
`extensions-helper-privacy-omission`,
`extensions-cursor-capture`,
`extensions-wire-serializers`,
`extensions-chain-walk`,
`extensions-payload-caps`,
`extensions-acknowledgement-gate`,
`extensions-debug-bound-state`,
`extensions-error-install-prose`,
`extensions-error-manifest`,
`extensions-runner-scope-nested`,
`extensions-bind-lifecycle`,
`extensions-streamed-resumption`,
`extensions-runner-lifetime`,
`extensions-pre-parse-scan`,
`extensions-document-walk`,
`extensions-value-walk`,
`extensions-bind-spec-bridge`,
`extensions-explicit-holding`,
`extensions-admission-lifecycle`,
`extensions-resource-manifest` — each
single-owned at its named owner with its
challenge/count re-derived by Worker-2.
Rejections (12) — all ENDORSE:
`extensions-original-error-reader`,
`extensions-degrade-floors`,
`extensions-pagination-pair-vs-key-set`,
`extensions-exact-bool-idiom`,
`extensions-hook-twins`,
`extensions-shape-gates`,
`extensions-debug-surface-split`,
`extensions-enforcement-unification`,
`extensions-location-copy`,
`extensions-cycle-guards`,
`extensions-measure-vs-truncate`,
`extensions-leaf-vs-root-manifest` — each
carries its contract difference +
reconsideration trigger, verified on
bodies. Family (1) — ENDORSE:
`fail-closed-debug-read` — count 2
confirmed, transcribe unticked +
blocked-on-hunt as rowed (no `## Families`
item until unblocked).

Verdict: `verified` (REVISE-1/REVISE-2
are non-propagating record notes; no
`## Defects` entries; `gate:` entries
alone leave the item `verified`).
