# DRY review: `django_strawberry_framework/extensions/error_policy.py`

Status: verified
Run: 0.0.15 2026-09-19-1 (prior evidence only; run-7 re-trace appended at tail, `Run: 0.0.15 2026-09-29-7`)

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one REUSED plan family (trigger re-checked fresh on
current evidence — never inherited), a file-local record with its proving
challenge, or a recorded rejection with difference + trigger + home. Zero
production edits; zero tracked files changed.

## System trace

Mid-size target (428 lines, 22 top-level statements): the enforcement half
of the production error policy. It DEFINES the masking classifier
([extensions-error-policy][extensions-error-policy]`::_is_unexpected`), the
client-safe replacement builder
([extensions-error-policy][extensions-error-policy]`::_masked`) with its two
fail-closed floors
([extensions-error-policy][extensions-error-policy]`::_degraded`,
[extensions-error-policy][extensions-error-policy]`::_replacement_for`), the
shape gate
([extensions-error-policy][extensions-error-policy]`::is_maskable_result`),
the activation gate
([extensions-error-policy][extensions-error-policy]`::masking_is_active`),
the schema policy reader
([extensions-error-policy][extensions-error-policy]`::schema_error_policy`),
the one pure application
([extensions-error-policy][extensions-error-policy]`::mask_execution_result`),
and the teardown site that applies it
([extensions-error-policy][extensions-error-policy]`::DjangoErrorPolicyExtension`).
It CONSUMES by name the configuration half
([error-policy][error-policy]`::ErrorPolicy` values,
[error-policy][error-policy]`::DEFAULT_ERROR_POLICY`,
[error-policy][error-policy]`::new_correlation_id`), the root logger, and
the per-operation state base
([extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`).
It does NOT define the policy record, its validation, its resolution
ladder, or its mint — those live at [error-policy][error-policy], which
this file imports one way (never the reverse). The module docstring
additionally STATES the install position (front of the chain), the two-seam
account, and the sync/async unity; the first is projection of
[schema.py][schema.py]`::_admitted_chain`, the rest is owned here and
verified against the bodies.

Connected code read for judgment, outside the item:
[consumers.py][consumers.py]`::_stop_aware_results` (full body — the per-event
seam) + `::_StopAwareSchema._stoppable` + module-docstring masking passages;
[error-policy][error-policy] (full read — the configuration half);
[schema.py][schema.py] (`_admitted_chain`, `_claimed_authority`,
`_consumer_extension_entries` declaration-folding, `error_policy` copy
property, `_SCHEMA_ENFORCEMENT` — install + authority lines);
[extensions-debug][extensions-debug]`::DjangoDebugExtension` class docstring
ordering passage + `on_execute` streaming-stash passage (the
`original_error` reader this file's copy-contract protects);
[extensions-resource-policy][extensions-resource-policy] (head + install
passages — the enforcement twin compared, not assumed);
[extensions-operation-state][extensions-operation-state] (base contract —
base-class role only); [utils-policies][utils-policies] (driver bodies —
configuration split corroborated); [extensions-init][extensions-init] +
[pkg-root][pkg-root] (leaf/root class bindings — consumer rows);
[test-error-policy][test-error-policy] (full `def test` census, 60+ rows;
key bodies: copy-contract pair, install-position row, hostile-shape
degrades, gate rows); [test-error-policy-api][test-error-policy-api]
(matrix docstring + 21-test census); `tests/test_routers.py` (stop-aware
partition row + incremental-passthrough row, titles only, stated
honestly); spec-048 body cited only as a pointer (defaults pinned by
oracles instead).

Swept package-wide for a second definition of each of the 8 functions +
the class (`django_strawberry_framework/`, 117 `.py`): hits only in this
file, the consumers seam (4 public helpers, by name), oracles, and prose
projections. Excluded on strength of body: every flavor folder (zero
masking vocabulary — flavors participate by RAISING deliberate
`GraphQLError`, which the classifier leaves untouched), `views.py` /
`routers.py` (no masking call), `schema.py` (installs the class, defines
no masking), `debug.py` (reads `original_error`, masks nothing).
Prior artifacts used only as rejected-candidate triggers, each re-derived
fresh from this side (`dry-file-error_policy.md` F1 configuration-vs-
application; `dry-file-consumers.md` F3 per-event consumer; the debug
artifact's bool-gate separation). Never read another worker's
`worker-memory/`. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched and hold none of this finding's
sites; concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** No sibling flavor masks errors:
package-wide sweep finds the masking vocabulary only here, in the
consumers seam, and in oracles/projections. The genuine twin shape is the
sibling enforcement half
([extensions-resource-policy][extensions-resource-policy]): request-side
budget gating vs response-side message masking, append-to-setup-last vs
prepend-to-tear-down-last, `on_parse`/`on_validate` hooks vs a single
`on_operation` teardown. Compared by contract, recorded as rejection J1
— same lifecycle family, opposite positions, not one rule. The flavors'
real participation (raising deliberate `GraphQLError`) is pinned by the
live matrix's untouched-deliberate column. Axis discharged.

**2. Sync/async twins.** No twin owed. The teardown is one plain
synchronous generator the engine enters on both paths (probe: zero
`AsyncFunctionDef`, the single textual `await` sits in the
`_is_unexpected` docstring prose); the per-event seam is an async
generator in [consumers.py][consumers.py], but its async-ness is the
transport's — it CALLS the shared sync `mask_execution_result`, so there
is no second masking implementation to keep in parity. The sync/async
dual-protocol scope machinery (`_BoundScope`) is owned at
[extensions-operation-state][extensions-operation-state], not here.
`one-sync-boundary` checked: zero `sync_to_async` in target — no
surface, do not inherit. Axis discharged by absence with reason.

**3. Derived rather than repeated knowledge.** Policy values are read by
attribute (`policy.message`, `policy.correlation_extension_key`,
`policy.enabled`), never restated; `DEFAULT_ERROR_POLICY` is composed by
name in `_degraded` + `schema_error_policy`; `settings.DEBUG` is read
directly in `masking_is_active` (one read site). The four location
retentions (`nodes`, `source`, `positions`, `path`) are four `getattr`
kwargs in one call — considered as a shared copy helper, refused in J2
(in-file machinery, no second site). No reconstructed copy found. Axis
discharged.

**4. Inverse / round-trip pairs.** No pair by contract: masking has no
unmask; correlation ids are minted and never parsed back (no consumer
reads one); the copy (not mutate) contract has no inverse. The two
adoption shapes — `_process_result` assigning three fields in place (the
teardown must rewrite the engine's result object) vs the seam yielding
the returned value — share the one builder by call; different transports,
not two definitions (C6 proves the split). Axis discharged with reason.

**5. Contracts restated in another medium.** Four media: production code
(this file); consumers composing by name (seam's four-helper import;
`schema.py` install + refused chains + copy property; leaf/root class
bindings); independent oracles
([test-error-policy][test-error-policy]: copy-contract pair,
install-position row, standalone-fallback rows, hostile-shape degrade
rows, gate rows; [test-error-policy-api][test-error-policy-api]: the
live category matrix + fresh-id-per-error + log-correlation +
retained-path + parity + both opt-outs + resolver-write rows; the
routers partition + incremental-passthrough rows); projections (both
module docstrings naming each other's seam — verified both directions;
`schema.py` install-position paragraph; `debug.py` ordering paragraph;
GLOSSARY/README/SECURITY/CHANGELOG prose + the spec pointer). No oracle
reads the owner to enumerate (literal spellings + behavior through the
public surface; a rename fails them). Axis discharged.

**6. Enforcement by omission.** The classification is a closed 4-case
partition (non-`GraphQLError` → masked; `original_error is None` →
untouched; `original_error` a `GraphQLError` → untouched; else masked),
extended through `located_error` wrapping to the completion phase by
structure, with hostile reads degrading fail-closed per entry and
unreadable result lists degrading whole-result. Deliberate omissions,
each with a contract source: incremental-delivery frames excluded by the
shape gate (masking one would defeat the transport's own refusal —
[consumers.py][consumers.py] docstring carries the argument); strawberry
`PreExecutionError` admitted contributing nothing (no `original_error`
to classify); DEBUG pass-through (the gate). No member lacks a guard its
contract requires. Axis discharged.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **22 top-level statements** — plus, better than the minimum,
every `DjangoErrorPolicyExtension`-body member (4). Every member lands
below; every challenge in `### Challenges` ends in a family row, a
file-local record, or a recorded rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (two-seam account, copy contract, install position, sync/async unity) | (none) | F1 owned prose + R1 projection (install position) |
| 2 | `from __future__ import annotations` | annotations | machinery |
| 3 | `import copy` | `copy` | machinery for F1 copy-contract |
| 4 | `from collections.abc import Iterator` | `Iterator` | machinery (`on_operation` generator) |
| 5 | `from typing import Any` | `Any` | machinery |
| 6 | `from django.conf import settings` | `settings` | F1 consumer edge (DEBUG read) |
| 7 | `from graphql import GraphQLError` | `GraphQLError` | machinery (F1 builder) |
| 8 | `from graphql.execution import ExecutionResult as GraphQLExecutionResult` | shape arm | F1 shape gate |
| 9 | `from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult` | shape arm | F1 shape gate |
| 10 | `from .. import logger` | `logger` | F2 consumer |
| 11 | `from ..error_policy import DEFAULT_ERROR_POLICY, ErrorPolicy, new_correlation_id` | 3 names | F1 configuration edge (root error_policy) |
| 12 | `from .operation_state import _OperationBoundExtension` | base | consumer edge (base owned at operation_state) |
| 13 | `__all__ = […4…]` | leaf manifest | R2, file-local |
| 14 | `def _is_unexpected` | classifier | F1 |
| 15 | `def _masked` | replacement builder | F1 |
| 16 | `def _degraded` | floor | F1 |
| 17 | `def masking_is_active` | activation gate | F1 |
| 18 | `def is_maskable_result` | shape gate | F1 |
| 19 | `def schema_error_policy` | policy reader | F1 |
| 20 | `def mask_execution_result` | application | F1 OWNER |
| 21 | `def _replacement_for` | per-entry degrade | F1 |
| 22 | `class DjangoErrorPolicyExtension` (`_OperationBoundExtension`) | teardown site | F1 |
| 22.1 | class docstring (entry-refusal + per-operation-state + DEBUG pass-through) | (none) | F1 owned prose; authority-refusal prose projects `schema.py` declaration-folding (R1) |
| 22.2 | `def _policy` | policy read | F1 (calls `schema_error_policy`) |
| 22.3 | `def _process_result` | in-place adoption | F1 (calls `mask_execution_result`) |
| 22.4 | `def on_operation` | teardown | F1 |

Rules: F1 masking cluster (statements 14–22 + owned prose); F2 logger
consumption (statement 10); R1 install/authority prose projection
(statement 1 install paragraph + 22.1 refusal paragraph); R2 leaf
manifest (statement 13). The plan's `## Responsibility index` already
carries `subscription-per-event-error-masking` (open, owner this file —
reused, trigger re-checked fresh below),
`typed-rejection-value-tail` (open — checked, no surface, F3),
`sealed-execution-queryset` (open — checked, no surface, F4),
`logger-single-sourcing` (open — consumer, F2). No other indexed family
owns a definition here. No new family is named: the masking cluster
counts 1 per axis at exactly one owner; the two considered shared forms
are rejections with contract differences + triggers (J1, J2).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | classifier | a new deliberate-rejection shape (e.g. consumer `GraphQLError` subclass carrying an `original_error`) | **1** (`_is_unexpected`; seam + teardown follow) | F1 |
| C2 | replacement structure | a new publish shape beside message+id (e.g. per-error severity) | **1** (`_masked`; mint format + key spelling stay at root error_policy, read by attribute — 0 here for those axes) | F1 |
| C3 | shape gate | a third maskable result flavor | **1** (`is_maskable_result`; both seams follow) | F1 |
| C4 | activation gate | a third gate input beside `enabled`/`DEBUG` | **1** (`masking_is_active`; both seams follow) | F1 |
| C5 | policy reader | a new schema attribute spelling for the policy | **1** (`schema_error_policy`; `_policy` + seam follow) | F1 |
| C6 | copy contract | mutate the result in place instead of returning a copy | **1** (`mask_execution_result`; `_process_result` + seam + debug-ordering prose follow — and the debug extension's `original_error` reads break, which is why the copy is load-bearing) | F1 |
| C7 | floor wording | reword the degrade (policy message alone) | **1** (`_degraded`; whole-result floor + teardown floor follow, all in-file) | F1 |
| C8 | per-entry degrade | change classify-then-degrade entry behavior | **1** (`_replacement_for`, in-file) | F1 |
| C9 | install position | append the extension instead of prepending | **0 here** / **1** at [schema.py][schema.py]`::_admitted_chain` (this file's paragraph becomes false prose) | R1 projection proof |
| C10 | third seam | a new transport masks per event (e.g. a views.py streaming path) | **0** new (composes the four helpers by name; the family's recorded trigger) | F1 trigger |
| C11 | log wording | reword one masking log line | **1** (the call site here; the `getLogger` definition stays at the root — 0 here for that axis) | F1 / F2 split |
| C12 | helper promotion | promote `mask_execution_result` to the leaf surface | **1** (owner definition; the leaf row follows — proves R2 separation) | independent |
| C13 | enforcement unification | unify with the resource-policy extension | refused — J1 (opposite lifecycle positions, distinct policies/hooks) | refused |
| C14 | location helper | share one copy-locations helper for the four `getattr` kwargs | refused — J2 (in-file machinery, no second site) | refused |

**Experiment.** Read-only probe (no source mutation, no Django setup, no
DB, no shared-tree pytest — the workspace recipe is for mutating proofs,
of which this zero-edit item has none):

```shell
python3 docs/dry/temp-tests/dry-file-extensions__error_policy/probe_w1.py
```

Output (`W1 PROBE: ALL OK`, 28 checks): 22-member module AST with exact
kind sequence + 8-function census + 4-member class census (§§1–2); zero
async defs with the single textual `await` inside docstring prose (§3);
zero tail/seal/queryset/boundary vocabulary (§4); one-way configuration
edge + both result shapes (§5); four-name manifest (§6); seam composes
the four helpers by one function-local import + single mask call (§7);
private helper single-filed (§8); item-baseline diff empty + working
blob equals `HEAD:` blob (§9); package population 117 (§10). Status:
`execution-verified` for every identity/count/shape/absence claim below.
Rejects the wrong results "a second masking definition exists", "an
async twin exists", "the seam restates classification", "the target
drifted from its baseline".

## Findings

No production edit is owed by a file item; F1 below is the REUSED plan
family this file owns (trigger re-checked fresh on current evidence),
F2 its consumer row, F3/F4 checked non-memberships, R1/R2 file-local
records, J1/J2 recorded rejections.

### F1 — subscription per-event error masking (existing family `subscription-per-event-error-masking`, status stays `open`)

- **Contract + variation.** One classifier, one replacement builder with
  its floors, one shape gate, one activation gate, one policy reader, one
  pure application — two application sites (query teardown + per-event
  transport seam). Variation: policy values (read by attribute) and
  result shapes (admitted pair vs incremental frames). This file OWNS the
  whole cluster:
  [extensions-error-policy][extensions-error-policy]`::mask_execution_result`
  (the pure application — the index's named owner),
  `::is_maskable_result`, `::masking_is_active`,
  `::schema_error_policy`, `::_is_unexpected`, `::_masked`,
  `::_degraded`, `::_replacement_for`,
  `::DjangoErrorPolicyExtension` (+ `_policy`, `_process_result`,
  `on_operation`).
- **Behavior/contract comparison (re-derived from this side).** The root
  [error-policy][error-policy] half holds the record, its validation,
  the resolution ladder, and the mint; this half holds every masking
  decision and every log record. Posit C2's key-axis (rename
  `correlationId`): root moves, nothing here does. Posit C6 (mutate in
  place): here moves, and the debug extension's `original_error` reads go
  blind — the copy is the debug-ordering contract made code. Posit C3
  (new shape): here moves, root doesn't. The dependency runs one way
  (three names imported here; root imports nothing from here), so no
  cycle can form. Configuration vs application, split at the import
  edge: distinct rules sharing an interface, not one rule twice. The
  consumers-side artifact's F3 named this same owner from the seam side;
  the root artifact's F1 drew the same split from the record side — both
  corroborated on fresh bodies, neither inherited.
- **Sites + roles.** *Definitions* (all here, unchanged): the 8
  functions + the class. *Consumers*: the extension teardown (owner
  side: `on_operation` → `_process_result` → `mask_execution_result`);
  [consumers.py][consumers.py]`::_stop_aware_results` (the ONLY external
  production consumer: resolves the policy once per subscription, reads
  the DEBUG gate per event, masks under the shared shape gate — one
  function-local import, one mask call, verified); `schema.py`
  (installs the class: admitted chain + refused chains + copy property —
  consumer of the class binding, not of masking);
  [extensions-init][extensions-init] + [pkg-root][pkg-root] (leaf/root
  class bindings — consumer rows). *Non-consumer neighbor*:
  [extensions-debug][extensions-debug]`::DjangoDebugExtension` reads
  `original_error` before masking runs (ordering, not masking — the
  copy-contract is what keeps both true). *Oracles*: the error-policy
  suite + live matrix + routers partition/passthrough rows (unchanged,
  all independent). *Projections*: both module docstrings (each names
  the other's seam — verified both directions), `schema.py`
  install-position paragraph, `debug.py` ordering paragraph.
- **Challenges.** C1–C8 → 1 each here; C9 → 0 here / 1 at `schema.py`;
  C10 → 0 new (the recorded trigger); C11 → 1 here (call site) with the
  logger definition staying at the root. Count stays 1 per axis at
  exactly one owner each.
- **Trigger re-checked fresh (not inherited).** A third application seam
  or a classifier change needed in two places. Measured today: still
  exactly two seams (teardown + `_stop_aware_results`, both bodies
  re-read, both composing the same four helpers by name — no restated
  classification, no local replacement builder, no local gate);
  `mask_execution_result` still the only classifier caller; private
  helpers still single-filed; no third seam, no restatement. The family
  stays open on fresh evidence, with nothing owed from any other file.
- **Owner + lifetime.** This file (unchanged — narrowest cohesive owner
  every legitimate consumer can depend on without reversing a
  dependency: the seam already imports it; the root record cannot own
  engine behavior without importing strawberry/graphql-core upward).
  Per-subscription policy local in the seam: lifetime one generator,
  validity the executing schema object (stated at the seam, not stored
  here). No stored derivation in this target.
- **Migration.** None (zero-edit item).
- **Distinct behavior.** The per-error granularity (call placement in
  `_masked`), the copy-vs-mutate contract (debug reads originals), the
  shape-gate exclusion (transport refusal intact), and the teardown
  in-place adoption (engine object must be rewritten) all stay here;
  policy values + mint format stay at the root; neither may be
  "simplified" into the other (C2/C6 prove the split).
- **Behavioral proof.** `execution-verified` for the import-direction
  census + literal/shape/call counts (probe §§4–8);
  `static-reviewed` for seam/teardown/oracle bodies (no shared-tree
  pytest per item rules). Rejects "this file defines policy values",
  "the seam restates classification", "a third seam exists".
- **Structural gate.** The existing per-event masking rows + the
  incremental-passthrough row + the copy-contract pair
  (`masking_returns_the_same_object…`,
  `masking_leaves_the_original…`): inlining a local classifier in the
  seam passes every happy-path oracle and fails exactly the new-shape
  rows the owner adds; mutating in place passes masking rows and fails
  the originals-holding row. Negative control (stated honestly, not
  run): a behavior-preserving hand copy of `mask_execution_result`
  into the seam passes every behavioral oracle and fails only the
  import census — so the seam's unity rests on the one-way import edge
  plus this finding, not on a behavioral gate; the trigger above is
  what re-opens it.
- **Coupling.** None.
- **Freshness.**
  `django_strawberry_framework/extensions/error_policy.py`
  `baea073f5615aaddc82c1f463071998bee7a6b62` (== `HEAD:` blob),
  `django_strawberry_framework/error_policy.py`
  `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91`,
  `django_strawberry_framework/consumers.py`
  `18f3ea161b6081a91445796902a9635cb7e2e3bc` (seam lines re-read),
  `django_strawberry_framework/schema.py`
  `2f72732123ca1156c4eb122ce7b53de6269de95e` (install + authority
  lines), `django_strawberry_framework/extensions/debug.py`
  `bf25c146111337ee0af590e7496b34c010c2f7be` (ordering + stash
  passages), `django_strawberry_framework/extensions/operation_state.py`
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9` (base contract),
  `django_strawberry_framework/utils/policies.py`
  `860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e`,
  `tests/test_error_policy.py`
  `4fa9852721b139c07274bdd73c9e0cda6d68f155`,
  `examples/fakeshop/test_query/test_error_policy_api.py`
  `5dbcf2013f98b10567b0dc8efddd9705141fa6c7`. Searched population for
  a second definition: whole package (117 `.py`) + seam + oracles;
  every hit lands in owner / consumer / oracle / projection as
  recorded. Excluded on strength of body: all flavor folders,
  `views.py`, `routers.py`, `debug.py` (masking vocabulary absent —
  probe §4 + package grep).

### F2 — logger single-sourcing (existing family `logger-single-sourcing`, consumer row, status stays `open`)

- **Contract difference from a finding.** This file defines no logger;
  it composes the family's owner by name (`from .. import logger`) and
  emits five records through it (`_masked` × 1, whole-result floor × 1,
  `_replacement_for` × 1, `_process_result` × 1, `on_operation` × 1).
  Posit moving `getLogger` → the root moves, nothing here does (0
  here / 1 at [pkg-root][pkg-root]`::logger`); posit C11 (reword one
  masking line) → exactly that call site moves (1 here). Shared token,
  separate responsibilities — the family's stated split, corroborated
  on this file's import line, not inherited.
- **Reconsideration trigger.** A `getLogger` (or second `logger`
  import) appearing in this module — then it becomes a second
  definition, not a consumer.
- **Durable home.** This finding + the root owner; no edit here to
  record it in.
- **Freshness.** Target as in F1 (probe §5: single `from .. import
  logger`, zero `getLogger`) + [pkg-root][pkg-root]
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`.

### F3 — typed rejection value tail (existing family `typed-rejection-value-tail`, checked, not a member)

- **Contract difference.** The family renders `got` tails for
  outside-package values through
  [exceptions.py][exceptions-py]`::describe_value`. This file renders
  no rejection tail at all: zero `describe_value`, zero
  `ConfigurationError` (probe §4) — its only strings are the stable
  mask message (read, never built) and log prose with no interpolated
  outside value. The debug artifact's bool-gate separation (debug
  acknowledgement vs `ErrorPolicy.enabled`) lives one layer down at
  the root record, never here. Posit a hostile-tail change at the
  renderer → nothing here moves; posit C11 here → no tail moves.
- **Reconsideration trigger.** A `ConfigurationError` (or any
  `describe_value` call) appearing in this module — then it becomes a
  consumer row.
- **Durable home.** This finding + the tail owner; nothing here.
- **Freshness.** Target as in F1 (absence probe-verified).

### F4 — sealed execution queryset (existing family `sealed-execution-queryset`, checked, not a member)

- **Contract difference.** The family seals querysets at execution
  boundaries. This file touches no queryset: zero `QuerySet` /
  `queryset` vocabulary (probe §4), no `_meta` read, no manager
  coercion, no visibility recheck — it rewrites result `errors` lists
  after execution completed. A sealing change moves the seal sites;
  nothing here does.
- **Reconsideration trigger.** Any queryset read, seal, or visibility
  check appearing in this module.
- **Durable home.** This finding + the seal owner; nothing here.
- **Freshness.** Target as in F1 (absence probe-verified).

### File-local records (no second definition after the matrix)

- **R1 — install-position + entry-authority prose (projection of `schema.py`).**
  The "FRONT of the extensions list" paragraph and the class-docstring
  entry-refusal paragraph state rules `schema.py` owns
  (`_admitted_chain` builds the list; `_consumer_extension_entries`
  folds declarations; `_claimed_authority` refuses subclasses). C9 → 0
  here / 1 at [schema.py][schema.py] — moving the position edits the
  chain builder while this paragraph becomes false prose, which proves
  the prose defines nothing. The refusal rationale (a resolver-reached
  shared instance as perpetual authority) is likewise enforced at the
  schema, described here. Trigger: `schema.py` ceasing to own the
  chain order would make this prose definitional. Freshness: target +
  `schema.py` as in F1.
- **R2 — leaf manifest.** `__all__` (four names; every public helper +
  the class exported, private helpers + operation-state machinery
  excluded — the same privacy the leaf manifest records from its side).
  C12 → 1 at the owner definition (a fifth public helper extends this
  tuple in exactly one place; the leaf row follows). The
  `package-root-public-surface` shape does not apply: that family is
  about re-export tables mirroring foreign homes, while this tuple
  mirrors same-file definitions in one edit region — checked, not a
  member, with this sentence as its difference. Trigger: a second
  manifest over these four names would make it a family. Freshness:
  target + [extensions-init][extensions-init]
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc` (privacy corroborated).

### J1 — error/resource enforcement unification (refused shared form, recorded here)

Both enforcement halves carry an extension, a policy object, and a
schema install — the symmetry the matrix compared, not assumed. Pair by
pair: resolution ladders already share
[utils-policies][utils-policies]`::resolve_policy`; copies share
`copy_policy`; tails share `describe_value`. What remains per side is
distinct mechanism, not shared vocabulary: pre-execution budget gating
over `on_parse`/`on_validate` with append-to-setup-last vs
post-execution message rewriting in one `on_operation` teardown with
prepend-to-tear-down-last; numeric bounds with a deadline vs three
string/bool options with a neutral message; `narrowed` existing only on
the resource side (an error policy has no maximums to tighten — a
deliberate omission, not a gap). Posit C13 here vs adding a resource
bound → exactly one side moves each time; posit swapping install
positions → both lifecycles break in opposite directions. Unifying the
pair would couple a request gate to a response rewrite across inverse
orderings. Reconsideration trigger: a third enforcement extension
arriving with the identical resolve→install→enforce shape — then the
SHAPE (not the policies) becomes a family with the schema chain as its
owner. Durable home: this finding + each module's install-position
paragraph (both already record the other's direction; no edit owed). No
new index row today.

### J2 — location-field copy helper (refused shared form, recorded here)

`_masked` retains four location fields via four `getattr` kwargs
(`nodes`, `source`, `positions`, `path`). Considered: one
copy-locations helper producing the four. Refused: all four sites are
arguments of a single call in a single function — one edit region, no
second site, no drift possible (C14: any retention change moves this
call and nothing else). A helper would obscure ownership (principle 11:
words/machinery alone never keep code) while the docstring's
"deliberately RETAINED" paragraph already states the rule where it is
enforced. Reconsideration trigger: a second location-retaining call
(e.g. the whole-result floor growing locations) — then the retention
becomes a family owned here. Durable home: this finding +
`_masked`'s docstring paragraph (already states it). No new index row
today.

## Defects

None. Every claim checked while tracing held: the one-way import edge
(root imports nothing from here); the copy contract against the debug
reads (masked copy out, engine originals intact — copy-contract oracle
pair exists); the `zip(..., strict=True)` arity (both lists derive from
the same materialization, so the strict flag is provable, not
aspirational); the whole-result floor dropping `data`/`extensions`
(documented in `_process_result`, adopted onto all three fields);
every `except` arm landing on a documented fail-closed value with a
server-side log; the install-position prose matching
`_admitted_chain`; the two-seam prose matching both bodies; the
DEBUG/`enabled` gate prose matching `masking_is_active`. Nothing routed
to any owner. (Static review only — no shared-tree pytest per item
rules; oracle bodies cited above are `static-reviewed`.)

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
117-file sweeps, command in `### Challenges`) already ran green against
the shared tree; they mutate no source, open no database, and import no
Django, so no workspace copy was owed and no `__file__`/DB `NAME`
record applies. No pytest was run in the shared tree, per item rules;
oracle bodies are `static-reviewed`. No `execution-deferred` items. No
`FAKESHOP_SHARDED` or Postgres cell is owed: the target's code path
reaches no database, alias, or dialect decision
(`inapplicable by construction` — pure result rewriting plus a
`settings.DEBUG` read; the only settings-adjacent value is a bool never
resolved here).

## Judgment

Backstop discharged: 22/22 `ast.Module.body` members enumerated plus all
4 `DjangoErrorPolicyExtension`-body members, 14 challenges run, every
rule terminating in the one existing family it touches (each trigger
re-checked fresh — `subscription-per-event-error-masking` confirmed
owned here with exactly two composing seams;
`logger-single-sourcing` as the consumed definition;
`typed-rejection-value-tail` and `sealed-execution-queryset` checked
with no surface, not inherited), a file-local record with its proving
challenge (R1, R2), or a recorded rejection with difference + trigger +
owner home (J1, J2) — no consolidation owed, no defect found, no new
family named. The configuration-vs-application split is drawn at the
import edge and holds in both directions probed. Zero-edit result is
legitimate.

No new `## Responsibility index` rows proposed for Worker 0: the only
families this target touches are already indexed (F1 owner, F2
consumer, F3/F4 checked non-members); the two refused shared forms live
at their owner paragraphs plus this finding.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
6700406c631b45e9dd6f97a130f4c8eaf4c22dc3 --
django_strawberry_framework/extensions/error_policy.py` is empty (0
bytes); the working blob
`baea073f5615aaddc82c1f463071998bee7a6b62` equals the item baseline,
the cycle-baseline member, and `HEAD:` — the target is CLEAN, so no
hunk attribution was owed. Before touching any path, the item-scoped
path was verified clean; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied, and no other dirty path was written
(sibling `dry-file-*.md` untracked artifacts are other items' work,
left alone). Dirt elsewhere left alone, not a stop. No commit.
Untracked scratch created (not tracked changes): this artifact
`docs/dry/dry-file-extensions__error_policy.md` and the read-only probe
`docs/dry/temp-tests/dry-file-extensions__error_policy/probe_w1.py`
(`W1 PROBE: ALL OK`, 28 checks; no source mutation, no Django import,
no DB, no shared-tree pytest). No ruff run owed (no tracked `.py`
edits; artifact is `.md` only; probe is untracked scratch). No
`__file__`/DB record (no workspace copy — no mutating proof exists).

## Independent verification (Worker 2)

Own trace re-derived from source (own `ast` dump + own `git grep`
sweeps; batch read had exposed the Findings headings first, so every
count below was re-computed, not copied):

- Classifier `::_is_unexpected`: closed 4-case partition
  (non-`GraphQLError` → masked; `original_error is None` → untouched;
  `original_error` a `GraphQLError` → untouched; else masked), direct
  attribute read, hostile reads contained by the caller's per-entry
  degrade. 1 definition. Owner: here.
- Replacement `::_masked`: stable message + fresh correlation id,
  retains exactly 4 location fields (`nodes`, `source`, `positions`,
  `path`) in one call, drops message/`original_error`, one
  `logger.error` with `exc_info`. 1 definition. Owner: here.
- Floors: `::_degraded` (message alone, guarded read, `DEFAULT`
  fallback) + `::_replacement_for` (per-entry classify-then-degrade)
  + whole-result floor in `::mask_execution_result` + teardown floor
  in `::on_operation` + adoption-failure floor in `::_process_result`.
  All 1-definition, all here.
- Shape gate `::is_maskable_result`: admits exactly the 2 stock
  result shapes, excludes incremental frames. 1 definition. Owner: here.
- Activation gate `::masking_is_active`: `enabled` AND `DEBUG is not
  True`, both reads fail toward masking. 1 definition. Owner: here.
- Policy reader `::schema_error_policy`: `getattr` + `isinstance`
  gate, fallback `DEFAULT_ERROR_POLICY`. 1 definition. Owner: here.
- Pure application `::mask_execution_result`: identity no-op,
  materialize-before-emptiness, order/arity preserved
  (`zip(..., strict=True)` over one materialization), shallow copy,
  whole-result degrade. Owner: `mask_execution_result` (agrees with
  W1 and the plan index).
- Consumers: extension teardown (`on_operation` → `_process_result`
  → `mask_execution_result`) + `consumers.py::_stop_aware_results`
  as the ONLY external production caller. Own sweep: each of the 4
  public helpers has exactly 2 production call sites (this file's
  teardown + the seam: mask at consumers:1385, gate+shape at
  consumers:1384, policy read at consumers:1377); private helpers
  (`_is_unexpected`, `_masked`, `_degraded`, `_replacement_for`)
  occur only in this file. "No third caller remains" verified, agree.
- Owners I would choose: identical — masking cluster here (seam
  already imports it; root record cannot own engine behavior),
  configuration half at root `error_policy.py`, logger at package
  root (single `getLogger` at `__init__.py:14`, 5 call sites here:
  146/308/322/384/413).

Reconciliation vs W1: agree on every row (F1 owner + trigger,
F2 consumer, F3/F4 non-membership, R1/R2 file-local, J1/J2
refusals), with three nuances, none revision-worthy: (i) one oracle
drives private `::_degraded` directly
(`tests/test_error_policy.py:732`) — pre-existing unit pinning of
the floor, not a rewrite (zero-edit item rewrote nothing), and it
does not weaken masking-rule independence since every classifier /
seam oracle drives behavior through the public surface with literal
expectations; (ii) the "a rename fails them" parenthetical is
imprecise (only the `_degraded` direct test fails a private rename;
the behavior oracles do not — which is the actual independence
property); (iii) the hand-copy negative control is honestly stated
as not run — accepted per the file-item standard (no shared-tree
pytest per item rules; structural claims are probe-executed instead).

Enumeration (member-by-member vs own count): own `ast` dump = 22
module members with the exact kind sequence W1 records, 8
functions in the exact order W1 names, class
`DjangoErrorPolicyExtension` with exactly 4 members (docstring +
`_policy`, `_process_result`, `on_operation`). Rows 1–22 +
22.1–22.4 all agree; every member is homed (F1 cluster, F2 logger
edge, R1 install/authority prose projection, R2 manifest,
machinery). 428-line target confirmed.

Matrix vs real surface: (1) cross-flavor — production masking
vocabulary hits only this file + the seam (own grep); twin
compared, not assumed (resource head + `on_parse`/`on_validate`
vs single `on_operation` read myself); (2) sync/async — no twin
owed (sync-generator teardown; seam's async-ness is the
transport's; zero `sync_to_async`); (3) derived knowledge — values
read by attribute, `DEFAULT` composed by name, one `DEBUG` read,
four `getattr` kwargs in one call (J2 correctly refused); (4)
round-trip — no unmask, no id parse-back, copy contract owns its
side (C6); (5) media — consumers compose by name (seam import +
single mask call re-read at consumers:1370–1385), install verified
at `schema.py::_admitted_chain` (`[ErrorPolicy(), *resolved,
ResourcePolicy(), ...]`), oracles independent (nuance (i) above);
(6) omission — 4-case partition + per-entry/whole-result degrades +
shape-gate frame exclusion, each omission contract-sourced. All
axes discharged, agree.

Counts + roles: C1–C8 = 1 here each; C9 = 0 here / 1 at `schema.py`
(chain builder re-read); C10 = 0 new (recorded trigger); C11 = 1
here (call site) / 0 at root (definition); C12 proves R2
separation; C13/C14 refused with mechanism reasons. Roles agree;
no oracle rewritten (nothing rewritten at all).

Equivalence (principle 8): vacuous behaviorally — zero production
edits, so observable behavior is identical by construction.
Structural claims (import direction, shape census, call counts,
absence vocabulary) are `execution-verified` (probe re-run below);
seam/teardown/oracle bodies are `static-reviewed`, honestly
labeled; no shared-tree pytest per item rules.

Zero-edit validation: `git diff
6700406c631b45e9dd6f97a130f4c8eaf4c22dc3 --
django_strawberry_framework/extensions/error_policy.py` re-run by
Worker 2: empty. Working blob `baea073f…` == `HEAD:` blob.
Coverage 22/22 + 4/4, assignment complete, no consolidation owed.
W1 names no new families and reuses masking-owner +
logger-consumer: judged correct — the cluster counts 1 per axis at
one owner; J1/J2 are correctly refusals, not families; F3/F4 are
correctly checked non-members.

Rejections: J1 (opposite lifecycle positions verified myself:
first-vs-last in `_admitted_chain`, pre-execution budget hooks vs
post-execution rewrite, `narrowed` one-sided) and J2 (single edit
region) carry difference + trigger + durable home; F3/F4 carry
difference + trigger with absence probe-verified (zero
`describe_value`/`ConfigurationError`/`QuerySet`/`queryset`/
`sync_to_async`/`seal` in target). Fingerprints: all 11 W1 values
re-hashed by Worker 2 — every one matches. Gates: copy-contract
pair (`test_masking_returns_the_same_object_when_nothing_needed_masking`,
`test_masking_leaves_the_original_result_holding_its_originals`)
confirmed present; failability analysis (hand copy passes behavior,
in-place mutation fails the originals row) accepted as honest
static review — no permanent new gate owed by a file item.
`## Pending execution`: absent, correctly — probe already ran
green (no mutation, no Django, no DB, no workspace owed);
`inapplicable by construction` for sharded/Postgres agreed (pure
result rewriting + one bool `DEBUG` read; no database, alias, or
dialect decision). Coupling: none, agreed.

AGENTS.md prose check: empty item-scoped diff → no code-rule
surface (no provenance, no citations, no tests, no ruff surface in
the diff). Artifact uses `path::Symbol` citations with
reference-style links; all 10 canonical link-definition groups
present; no `path:NN` outside the allowed scratch context (this
artifact is per-cycle scratch that closes with the cycle); no
commit; concurrent dirt untouched (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`,
sibling untracked artifacts — none edited, reverted, or tidied).

Scratch: W1 probe re-run by Worker 2: `W1 PROBE: ALL OK (28
checks)`. No new scratch created; no workspace copy (no mutating
proof exists); no shared-tree pytest.

Exact plan rows Worker 0 should write: no
`## Responsibility index` updates — the masking family row already
covers `extensions/error_policy.py` + `consumers.py` (owner + sole
external seam; `schema.py`/leaf bindings are consumer rows needing
no coverage), `logger-single-sourcing` already indexes its owner,
F3/F4 are correctly non-members, J1/J2 live at owner paragraphs +
this finding. Tick only:

- [x] File `extensions/error_policy.py` — [dry-file-extensions__error_policy.md](dry-file-extensions__error_policy.md) — verified (Run 0.0.15 2026-09-18-1; zero edits, no pending execution)

## Defects (Worker 2)

None. Every claim checked while tracing held (one-way import edge,
copy contract vs debug `original_error` reads, `strict=True` arity
over one materialization, three-field adoption with whole-result
floor, every `except` arm fail-closed with a server-side log,
install-position prose matching `_admitted_chain`, two-seam prose
matching both bodies, gate prose matching `masking_is_active`).
The two oracle-prose nuances in `## Independent verification
(Worker 2)` are artifact wording observations, not production
defects, and need no owner routing.

## Re-trace at bfaee91d (Worker 1)

Run: 0.0.15 2026-09-19-1. ITEM_BASELINE
`16f475471a8b8295117640f7b14d949603d7bbc0` == working blob == `HEAD:`
blob (`HEAD` is `bfaee91d`); item-scoped diff empty, target CLEAN, no
hunk attribution owed. The dispatch named blob `cd1c9855…`; that value
was not observed anywhere — working, `HEAD:`, and ITEM_BASELINE all
agree on `16f47547…`, which is what every fingerprint below binds.
Range `9031cb3d..bfaee91d` touches the target in exactly one commit
(`ffce6f29`); numstat on the target is 51 added / 19 deleted (70
changed lines — the dispatched "+70"). The plan's `## Owned changes`
ledger holds no row on this path (only `optimizer/walker.py`, two
fakeshop live files, `tests/base/test_init.py`,
`tests/optimizer/test_extension.py`); concurrent dirt touches none of
this finding's sites and the target file itself is clean. Prior
artifact used only as rejected-candidate triggers + enumeration to
reconcile (`dry-file-error_policy.md` F1, `dry-file-consumers.md` F3,
debug bool-gate separation); every verdict below re-derived fresh.
Never read another worker's `worker-memory/`.

### Enumeration (reconciled against the prior 22-row table)

Instrument unchanged: `ast.parse`, `ast.Module.body` members — now
**23 top-level statements** (prior 22, +1) — plus, better than the
minimum, every `DjangoErrorPolicyExtension`-body member (still 4).

| # | Statement | Delta vs prior | Home |
|---|---|---|---|
| 1 | module docstring | CHANGED: two-seam account → three-seam account + idempotency peg + plain-`Schema` caveat | F1 owned prose |
| 2–12 | future/copy/Iterator/Any/settings/`GraphQLError`/both result shapes/logger/config trio/base imports | unchanged | machinery / F1 edges / F2 edge |
| 13 | `__all__` | CHANGED: 4 names → 5 (`degraded_result` added) | R2, file-local |
| 14 | `def _is_unexpected` | unchanged | F1 |
| 15 | `def _masked` | unchanged | F1 |
| 16 | `def _degraded` | unchanged | F1 |
| 17 | `def degraded_result` | ADDED: whole-response floor builder | F1 |
| 18 | `def masking_is_active` | unchanged | F1 |
| 19 | `def is_maskable_result` | unchanged | F1 |
| 20 | `def schema_error_policy` | unchanged | F1 |
| 21 | `def mask_execution_result` | CHANGED: one line — unreadable-list floor now `return degraded_result(policy)` | F1 |
| 22 | `def _replacement_for` | unchanged | F1 |
| 23 | `class DjangoErrorPolicyExtension` | body CHANGED, membership same (docstring + `_policy`, `_process_result`, `on_operation`) | F1 |
| 23.1 | class docstring | unchanged | F1 owned prose |
| 23.2 | `def _policy` | unchanged | F1 |
| 23.3 | `def _process_result` | CHANGED: adoption-failure floor now `degraded_result(policy)` | F1 |
| 23.4 | `def on_operation` | CHANGED: docstring (three-seam account) + teardown floor now `degraded_result(policy)` | F1 |

Functions 8 → 9 in prior order with `degraded_result` after
`_degraded`. No member removed. The `+70` decomposes to: docstring
prose (third-seam paragraph, idempotency paragraph, plain-`Schema`
caveat), `__all__` +1, `degraded_result` +15 lines, three
call-substitutions (one line each), `on_operation` docstring rework.
No new branch restates classification, replacement, or gates.

### Matrix (vs the real surface at bfaee91d)

Wire-observable masking surface: masked message text (always the
policy message), `extensions` (fresh `correlationId` per masked error,
absent on deliberate errors and on whole-response floors), retained
`path`/`nodes`/`source`/`positions`, dropped `original_error`. Axes 4
and 5 below carry that weight.

**1. Cross-flavor mirroring.** Masking vocabulary still only here, the
seam, `schema.py`, oracles/projections (package grep re-run; flavors
participate by raising deliberate `GraphQLError`, pinned by the live
untouched-deliberate rows). The resource-policy twin compared fresh,
not assumed — J1 stands. Discharged.

**2. Sync/async twins.** Still no twin owed: teardown one sync
generator (zero `AsyncFunctionDef`, single textual `await` inside the
`_is_unexpected` docstring); seam async-ness is the transport's and
calls the shared sync application. New since prior: the schema return
seam exists in both sync (`execute_sync`) and async (`execute`) color
twins at [schema.py][schema.py], both one-line calls into
`_masked_return` — the color split lives at the schema, not here.
Zero `sync_to_async`. Discharged by absence with reason.

**3. Derived knowledge.** Policy values still read by attribute;
`DEFAULT_ERROR_POLICY` composed by name (`_degraded` +
`schema_error_policy`); one `settings.DEBUG` read; four `getattr`
location kwargs in one call (J2 stands — the new floor builder adds
no second retention site). Discharged.

**4. Round-trip pairs.** Still no pair by contract: no unmask, ids
minted never parsed back, copy-not-mutate unchanged. Wire half now
pins harder: per-error `correlationId` freshness, floor shape
(`data=None`, single policy-message error, no `extensions`), and the
identity no-op (already-masked result returns by identity, so no
second id minted or logged). Discharged with reason.

**5. Media.** Four media, all re-read: production (this file);
consumers composing by name — seam's four-helper function-local
import + single mask call (consumers.py:1385, gates at 1384, policy
read at 1377), `schema.py` five-name import + single mask call at
1083 + floor call at 1089 + `_masked_return` at 1050, leaf/root class
bindings; oracles — unit suite (3 return-seam rows, copy-contract
pair, floor/degrade rows, gate rows) plus live matrix (resolver rows
+ 6 hook rows over 4 hook halves × 2 colors); projections — both
module docstrings naming each other's seam (verified both directions
at bfaee91d; consumers module prose updated, one function sentence
stale → D1), `schema.py` install + return-seam paragraphs, `debug.py`
ordering paragraph. No oracle reads the owner to enumerate except the
pre-existing private-floor unit pin noted by W2 (unchanged).
Discharged.

**6. Omission.** Closed 4-case partition unchanged; located-error
wrap, per-entry + whole-result + unreadable-list degrades, hostile
reads degrading fail-closed per entry, shape-gate frame exclusion,
`PreExecutionError` contributing nothing, DEBUG pass-through — all
re-read. Deliberate omissions unchanged. The whole-response floor now
has one spelling (`degraded_result`) shared by all four landing
sites, so a new omission (a seam degrading by hand) is detectable by
census: `StrawberryExecutionResult(data=None` occurs exactly once in
the package (the builder body). Discharged.

### Challenges (counts are authoritative definitions only)

C1–C8 re-run unchanged → 1 each here (classifier, replacement,
shape gate, activation gate, policy reader, copy contract, floor
wording, per-entry degrade). C9 → 0 here / 1 at
[schema.py][schema.py]`::_admitted_chain` (R1). **C10 FIRED**: the
recorded trigger — "a new transport masks per event" generalized to
"a third seam arrives" — arrived as the schema return seam, and it
composed the four helpers + floor by name: **0** new
classification/replacement/gate definitions, **1** new consumer of
the floor builder (which was extracted in the same commit precisely
so the seam could share it). C11 → 1 here / 0 at root. C12 → R2
separation (now five names). C13/C14 refused (J1/J2, re-derived).
New: **C15** whole-response floor shape change (e.g. publish
`extensions` on the floor) → **1** (`degraded_result`; all four
landing sites follow — listed, not counted). **C16** fourth seam →
**0** new (recorded trigger: composes helpers + floor by name).

The `+70` per-branch accounting: docstring paragraphs = projection
of seams owned elsewhere (R1-adjacent, 0 definitions); `__all__` +1
= manifest follows owner (R2); `degraded_result` = the one floor
definition absorbing three in-file inline constructions (21→23.3→23.4
call sites, 0 new rules); `schema.py::_masked_return` = consumer
(policy read from the enforcement record, shared gates, shared
application, shared floor; zero local classifier/builder/gate —
counted 0 per every posited masking change); consumers.py range diff
= module-prose touch only (function body untouched).

### Findings

**F1 — `subscription-per-event-error-masking` (REUSED, owner here,
stays `open`).** Contract, sites, roles, challenges as in the prior
F1, re-derived: 9 functions + class here; consumers — teardown chain
(`on_operation` → `_process_result` → `mask_execution_result`) and
`consumers.py::_stop_aware_results` (sole external per-event caller,
four-helper import, one mask call) and now
[schema.py][schema.py]`::DjangoSchema._masked_return` (second
external caller: own policy-record read, shared gates, one mask
call, shared floor) — each composing by name, none restating.
Trigger re-checked fresh and found FIRED-as-foretold: the third seam
landed composing rather than duplicating, exactly what the trigger
demanded; no restatement found by package grep + probe §§E7–E8. Owner
unchanged (seam and schema both already import this module; the root
record cannot own engine behavior). No stored derivation here.
Behavioral proof: `execution-verified` for import direction, shape
census, call counts, absence vocabulary, floor-call census (probe,
41 checks, ALL OK); `static-reviewed` for seam/teardown/return bodies
(no shared-tree pytest per item rules — census and composition are
decidable by inspection, and no behavior was edited by this item, so
no focused test could beat inspection; none run). Structural gate:
copy-contract pair + return-seam identity row + once-only hook row
(see security rows); negative control honestly `static-reviewed`
(hand copy passes behavior, import census fails it). Coupling: none
(zero edits). Freshness: target `16f47547…`,
[error-policy][error-policy] `fa94fcd9…`,
[consumers.py][consumers.py] `936210e2…` (seam re-read),
[schema.py][schema.py] `c2e1b748…` (return seam re-read),
[extensions-debug][extensions-debug] `bf25c146…`,
[extensions-operation-state][extensions-operation-state] `b2674a22…`,
[utils-policies][utils-policies] `860b181f…`,
[test-error-policy][test-error-policy] `9ff5328e…`,
[test-error-policy-api][test-error-policy-api] `9a425677…`,
package root `0ef72601…`, [extensions-init][extensions-init]
`dc3ebdc2…`; population 117 `.py`; searched whole package + seam +
return + oracles.

**F2 — `logger-single-sourcing` (REUSED, consumer row, stays
`open`).** Still no definition here: one `from .. import logger`,
zero `getLogger`, five call sites (164/341/355/417/448 — same five
roles). Challenges C11 split unchanged. Trigger: a `getLogger` here.
Freshness: target + root as in F1.

**F3 — `typed-rejection-value-tail` (re-challenged fresh, not a
member).** Zero `describe_value`, zero `ConfigurationError`
(probe-verified); only strings are the stable mask message (read,
never built) and log prose with no interpolated outside value.
Trigger: any tail renderer appearing here.

**F4 — sealed-execution queryset (re-challenged fresh, not a
member).** Zero `QuerySet`/`queryset` vocabulary; rewrites result
`errors` lists post-execution only. Trigger: any queryset read/seal
here.

**F5 — `operation-bound-extension-mechanism` (re-challenged fresh,
base-class role only, not a definition).** The class inherits
[extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`;
no scope/bind/resume machinery defined here (probe: class holds only
docstring + `_policy`, `_process_result`, `on_operation`). Posit a
per-operation-state lifetime change → 0 here / 1 at the base; posit
a masking change → 1 here / 0 at the base. Distinct mechanisms
sharing an inheritance edge, not one rule. Trigger: any
runner-scope/bind/unbind definition appearing here. Durable home:
this finding + the base owner.

**R1 — install-position + entry-authority prose (file-local
projection of `schema.py`).** Unchanged in force; the module
docstring's FRONT paragraph and the class refusal paragraph still
describe rules `schema.py` owns (C9 → 0/1). Trigger: `schema.py`
ceasing to own chain order. Freshness: target + `schema.py` as F1.

**R2 — leaf manifest (file-local).** Now five names (C12/C15: a sixth
public helper extends the owner + this tuple in one region each).
The root re-export shape still does not apply (same-file mirror, one
edit region — checked, not a member). Trigger: a second manifest
over these names. Freshness: target + leaf as F1.

**J1 — error/resource enforcement unification (refused, stands).**
Re-compared fresh: pre-execution budget gating over
`on_parse`/`on_validate`, append-last, numeric bounds + deadline vs
post-execution message rewrite in one `on_operation` teardown,
prepend-first, three string/bool options + neutral message;
`narrowed` one-sided; ladders/copies/tails already shared at
[utils-policies][utils-policies] + [exceptions-py][exceptions-py].
One side moves per change; swapping positions breaks both
lifecycles oppositely. Trigger + home unchanged.

**J2 — location-field copy helper (refused, stands).** Four
`getattr` kwargs still arguments of one call in `_masked`; the new
floor builder retains no locations, so the refused trigger (a second
retaining call) did not fire. Home unchanged.

### Defects

**D1 (new, UNFIXED, owner `consumers.py`).**
[consumers.py][consumers.py]`::_stop_aware_results` docstring still
reads "one classifier, one replacement builder, two application
sites" while the package now has three application sites (teardown,
per-event seam, `schema.py::_masked_return`). Stale count left
behind by `ffce6f29`, which updated that module's top prose but not
this sentence. Prose-only: composition verified by name on all three
sites (probe §§E7–E8), so no wire impact; the sentence is false all
the same. Not fixed here (file item: zero edits). Routes to the
`consumers.py` re-trace / its holding family for the one-word repair.

### Security rows (trust boundary: an error masked for the right operation)

- Sync/async query/mutation via `execute`/`execute_sync`, resolver
  failure: teardown masks (`masking_is_active` + shape gate), return
  seam no-ops by identity (no second id/log). Oracles:
  `test_a_graphql_core_execution_result_is_rewritten_in_place_preserving_order`,
  `test_the_return_seam_passes_an_already_masked_result_through_by_identity`,
  live `test_an_unexpected_exception_reaches_the_client_as_the_policy_message_only`
  (+ retained-path, fresh-id-per-error, log-correlation rows).
- Subscription per-event: seam masks each event (policy once per
  subscription, gates per event); teardown sees only the end.
  Oracles: routers partition + incremental-passthrough rows (unchanged).
- Streamed query/mutation: seam masks the yielded single result.
  Oracle: same seam rows + shape-gate frame exclusion prose.
- Hook escape (any hook incl. this teardown): return seam masks;
  exactly one entry + one log record across both seams. Oracles: 6
  live hook rows (`where` × `color`) + unit return-seam degrade +
  disabled-no-op rows.
- Plain `strawberry.Schema` with the extension hand-installed:
  DOCUMENTED HOLE — no schema seam, hook failure unmasked (module
  docstring caveat). Oracle: standalone-fallback rows.
- `DEBUG is True` / `enabled False`: pass-through, no id. Oracles:
  gate rows + live debug/opt-out rows (resolver + hook halves).
- Fail-closed: per-entry degrade (policy message + log), whole-result
  floor (`data=None`, one policy-message error, no `extensions`, log
  at the failing seam). Oracles: hostile-shape/message/result rows +
  adoption/teardown-failure rows.
- Wire guarantee: masked text == policy message; `correlationId`
  fresh per masked error and joinable to exactly one server log
  record carrying the original exception + traceback;
  `original_error` never reaches the client.

### Pending execution

None. Read-only probe `docs/dry/temp-tests/dry-file-extensions__error_policy/probe_w1_retrace.py`
(`W1 RETRACE PROBE: ALL OK`, 41 checks) ran green; it mutates no
source, opens no DB, imports no Django — no workspace copy owed, no
`__file__`/DB record applies. No shared-tree pytest run per item
rules; oracle bodies `static-reviewed`. No `execution-deferred`
items. Sharded/Postgres cells `inapplicable by construction`
(pure result rewriting + one bool `DEBUG` read; no database, alias,
or dialect decision).

### Judgment

Backstop discharged at bfaee91d: 23/23 members + 4/4 class members
enumerated, every rule in F1 (owner) / F2 (consumer) / F5 checked
base-role / F3–F4 checked non-members / R1–R2 file-local / J1–J2
refusals — no consolidation owed (file item performs none), one
prose defect routed (D1), no new family named. C10's recorded
trigger fired and held: the third seam composes the one masking
implementation by name. Zero-edit result is legitimate.

No new `## Responsibility index` rows for Worker 0: F1 already
indexes `extensions/error_policy.py` + `consumers.py` + `schema.py`;
F2/F5 already indexed; F3/F4 correctly non-members; J1/J2 live at
owner paragraphs + this finding. Tick only.

## Implementation (Worker 1, re-trace)

Zero tracked changes. Item-scoped diff state: `git diff HEAD -- django_strawberry_framework/extensions/error_policy.py`
empty; working blob `16f47547…` == `HEAD:` == ITEM_BASELINE. The
`## Owned changes` ledger was read in full and holds no row on this
path; concurrent dirt (package hunks, test companions, staged
entries, sibling untracked artifacts) never edited, reverted, or
tidied. No commit. Untracked scratch created, not tracked changes:
this artifact's new section + read-only probe
`docs/dry/temp-tests/dry-file-extensions__error_policy/probe_w1_retrace.py`
(41 checks green; pre-existing `probe_w1.py` from the prior run left
alone). No ruff run owed (no tracked `.py` edits; artifact `.md`
only; probe untracked scratch). No `__file__`/DB record (no
workspace copy — no mutating proof exists).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[consumers.py]: ../../django_strawberry_framework/consumers.py
[error-policy]: ../../django_strawberry_framework/error_policy.py
[exceptions-py]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[schema.py]: ../../django_strawberry_framework/schema.py
[utils-policies]: ../../django_strawberry_framework/utils/policies.py

<!-- tests/ -->
[test-error-policy]: ../../tests/test_error_policy.py

<!-- examples/ -->
[test-error-policy-api]: ../../examples/fakeshop/test_query/test_error_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Re-trace verification at bfaee91d (Worker 2)

Reading-order note, stated honestly: the batch read exposed the
artifact's Findings headings before the independent counts below were
computed. Every count, hash, and site role below was re-derived from
source (own `ast` dump, own package greps, own blob hashes), not
copied; agreements are reconciliations, not repetitions.

### Own trace (re-derived)

- Target: **23 top-level statements** (own `ast.parse` dump; kind
  sequence matches the W1 table row-for-row), **9 functions** in prior
  order with `degraded_result` after `_degraded`, class
  `DjangoErrorPolicyExtension` with exactly **4 members** (docstring +
  `_policy`, `_process_result`, `on_operation`), `__all__` with
  **5 names** (incl. `degraded_result`). Zero `AsyncFunctionDef`; one
  textual `await` inside docstring prose. 460 lines.
- Masking cluster, sites + roles from this side: definitions ALL here
  — classifier `::_is_unexpected`, builder `::_masked`, floors
  `::_degraded` + `::degraded_result` + `::_replacement_for`,
  gates `::is_maskable_result` + `::masking_is_active`, reader
  `::schema_error_policy`, application `::mask_execution_result`,
  teardown `::DjangoErrorPolicyExtension` (`_policy`,
  `_process_result`, `on_operation`). Package-wide sweep: each masking
  `def` occurs exactly once in production (only
  [schema.py][schema.py]`::_masked_return` shares a name stem and is a
  differently-named consumer method, not a masking redefinition);
  private helpers occur nowhere outside this file (modulo its own
  bytecode cache).
- `degraded_result` is the one floor **definition**, not a second
  spelling: `StrawberryExecutionResult(data=None` occurs exactly once
  package-wide (the builder body); its four landing sites all call by
  name — in-file floors at the unreadable-list branch, the
  adoption-failure branch, the teardown floor, plus
  [schema.py][schema.py] at 1089. The `ff` commit extracted three
  in-file inline constructions into the one builder (21→23.3→23.4 call
  substitutions) so the new schema seam could share it: 1 definition,
  4 consumers-by-call.
- Consumers, confirmed consumer (never definition): the teardown chain
  (`on_operation` → `_process_result` →
  `mask_execution_result`); [consumers.py][consumers.py]`::_stop_aware_results`
  (function-local four-helper import, policy read at 1377, gates at
  1384, single mask call at 1385 — zero local
  classifier/builder/gate); [schema.py][schema.py]`::_masked_return`
  (own enforcement-record policy read, shared gates at 1081, single
  mask call at 1083, shared floor at 1089 — zero local
  classifier/builder/gate). From THIS side the schema re-trace's
  classification is confirmed: `_masked_return` composes 4 gates/helpers
  by name and defines no masking rule. Owner I would choose: here
  (both external seams already import this module; the root record
  cannot own engine behavior); configuration half at the root record;
  logger at the package root. Identical to W1 and the plan index.

### Enumeration check

Agree 23 (prior 22, +1 `degraded_result`), functions 8→9, `__all__`
4→5, class members 4 unchanged. Delta reconciled: docstring
two→three seams + idempotency + plain-`Schema` caveat, `__all__` +1,
`degraded_result` body, three one-line call substitutions,
`on_operation` docstring rework. `ff` range `9031cb3d..bfaee91d`
touches the target in exactly one commit (`ffce6f29`), numstat 51+/19−
(= dispatched +70), re-verified. Rows 1–23 + 23.1–23.4 all homed
(F1/F2/R1/R2/machinery); 23/23 + 4/4 coverage confirmed.

### C10 judgment

The prior artifact's C10 example row named a *transport per-event*
arrival (`a views.py streaming path`); what arrived was the *schema
return* seam (hook-escape, both `execute` colors). The family trigger
text, however, was already generic — "a third application seam or a
classifier change needed in two places" — and the return seam falls
inside that foretold population while composing (0 new
classification/replacement/gate definitions, verified by sweep).
Verdict: **fired-as-foretold holds at the trigger level**; the
concrete example was substituted, and W1's "generalized to a third
seam arrives" records that substitution openly rather than
back-dating it. Genuinely predictive trigger, retrospectively
instantiated example — accurately recorded, sufficient, no revision.

### D1 adjudication (Worker 2)

Reproduced: [consumers.py][consumers.py]`::_stop_aware_results`
docstring (1320–1321) reads "two application sites" while three are
live — teardown, per-event seam,
[schema.py][schema.py]`::_masked_return` — and that module's own top
prose (137–149) already names the third. `ffce6f29` updated the top
prose but left the function sentence stale. Prose-only: composition
verified by name on all three sites, so no wire impact. Defect-bar
(AGENTS.md / GOAL.md trust boundary): no contract row broken, no
wire or configuration input reaches it — **not a release blocker**.
DRY-class: docstring-contradicting-body, routed not fixed here.
**Card class: small prose-repair card** homed to the `consumers.py`
re-trace / holding family `subscription-per-event-error-masking`
(one-word "two"→"three" repair). D1 stands as W1 wrote it; homing
note for Worker 0 is under "Exact plan rows" below.

### Oracle-independence spot-check (Worker 2)

Package oracle ([test-error-policy][test-error-policy]): literal pin
`DEFAULT_ERROR_POLICY.message == "An unexpected error occurred."`
(99) anchors the message text at the configuration owner; masking
rows assert masked output equals that value AND assert the
`_SENSITIVE` literal appears nowhere — a masking break (leak,
passthrough) fails literals, not owner reads. Spot-checked the
lying-container row (746–758: falsy-but-populated list still
classified, order/arity preserved) — drives `mask_execution_result`
as subject-under-test through the public surface with literal
expectations; the one direct `::_degraded` pin (732) is a
pre-existing unit floor pin, honestly noted before, no rewrite here.
Live oracle ([test-error-policy-api][test-error-policy-api]): imports
neither `mask_execution_result` nor `degraded_result` (verified by
search); `_masked_error` asserts message verbatim + well-formed
`correlationId` + `_SENSITIVE`/`tenant-42`/`RuntimeError` absence over
real `/graphql` JSON. It defaults the extensions key from
`DEFAULT_ERROR_POLICY.correlation_extension_key` — a read from the
*configuration* owner, not the masking owner under check; the masking
rule itself is pinned behaviorally (an unmasked hook failure fails
`test_an_exception_from_a_consumer_hook_is_masked_like_a_resolver_exception`;
double-masking fails
`test_one_hook_failure_produces_exactly_one_masked_entry_and_one_log_record`
via entry count + single log record + id join). Independence holds:
no pinning oracle enumerates or reads the masking owner.

### Freshness (Worker 2, re-hashed)

Target `16f47547…` (type blob; == `HEAD:` == recorded ITEM_BASELINE;
`git diff HEAD --` the target empty, 0 bytes — file clean);
[error-policy][error-policy] `fa94fcd9…`;
[consumers.py][consumers.py] `936210e2…`;
[schema.py][schema.py] `c2e1b748…`;
[extensions-debug][extensions-debug] `bf25c146…`;
[extensions-operation-state][extensions-operation-state] `b2674a22…`;
[utils-policies][utils-policies] `860b181f…`;
[test-error-policy][test-error-policy] `9ff5328e…`;
[test-error-policy-api][test-error-policy-api] `9a425677…`; package
root `0ef72601…`; [extensions-init][extensions-init] `dc3ebdc2…`.
Every value matches W1's; population 117 `.py` confirmed. Dispatch
correction adjudicated: W1's mislabel record is accurate in
substance — `cd1c9855` resolves (type commit) as a stash commit
(`WIP on t3code/1cc21548`, parent `bfaee91d`), categorically not a
file blob, which corroborates rather than weakens the "mislabeled
stash id" diagnosis; ground truth confirmed thrice (worktree,
`HEAD:`, ITEM_BASELINE all `16f47547…`).

### Pending execution (Worker 2)

Empty, judged correct. The 41-check probe is read-only (no source
mutation, no Django import, no DB) so no workspace copy, no
`__file__`/DB record, and no `proof:` entry was owed. No shared-tree
pytest per item rules; oracle bodies above are `static-reviewed`
(spot-checked, not executed). Sharded/Postgres cells inapplicable by
construction (pure result rewriting + one bool `DEBUG` read; no
database, alias, or dialect decision) — agreed.

### AGENTS.md prose on the empty diff

Item-scoped diff empty → no code-rule surface (no provenance, no new
citations, no tests, no ruff surface in any diff). No tracked `.py`
touched (artifact `.md` only), so no `ruff check`/`format` run owed.
Citations above reuse the artifact's existing reference-style
link-definition groups; no `path:NN` outside this per-cycle scratch
artifact; no commit. Concurrent dirt (package hunks, test
companions, staged entries, sibling untracked artifacts) never
edited, reverted, or tidied.

### Defects (Worker 2, re-trace)

None new. D1 (W1's, owner `consumers.py`) adjudicated above: stands,
prose-only, card class named, homed below — no production route
from this item.

### Per-claim agreement / difference

F1 owner + fired trigger, F2 consumer, F3/F4 non-membership, F5
base-role, R1/R2 file-local, J1/J2 refusals, zero-edit legitimacy,
no new index rows, empty pending execution — **agree on all**.
Differences: none material. Precision notes only (not
revision-worthy): (i) prior-run nuance about the private-floor unit
pin and the "a rename fails them" parenthetical carries over
unchanged; (ii) `cd1c9855` does resolve as a stash commit object —
W1's "not observed anywhere" reads as "not observed as this file's
blob," which the hashes confirm.

### Exact plan rows for Worker 0

No `## Responsibility index` updates (F1 already covers
`extensions/error_policy.py` + `consumers.py` + `schema.py`;
F2/F5 indexed; F3/F4 correctly non-members; J1/J2 at owner
paragraphs + finding). Tick only:

- [x] File `extensions/error_policy.py` — [dry-file-extensions__error_policy.md](dry-file-extensions__error_policy.md) — verified (Run 0.0.15 2026-09-19-1; zero edits, no pending execution)

D1 homing note: home D1 on a NAMED owning card for the
`consumers.py` one-word repair ("two"→"three" application sites in
`::_stop_aware_results` docstring) via the `consumers.py` re-trace /
holding family `subscription-per-event-error-masking`; prose-only,
not a blocker.

## Run-7 scoped re-trace (Worker-1, REOPENED queue item d4)

Run: 0.0.15 2026-09-29-7. Everything above this section is PRIOR
EVIDENCE ONLY (09-18/19 artifact with its bfaee91d re-trace,
`Status: verified` at its stamp). This section re-traces the target
fresh at HEAD bytes and issues a CONFIRM or REVISE verdict for every
prior finding, with fresh evidence for each. No consolidation beyond
this file item; no production edits; no plan edits.

### Scope, attribution, fingerprints

Three states fingerprinted, all by blob id over exact bytes:

- Drift base `5ee86193:django_strawberry_framework/extensions/error_policy.py`
  = `7ee4e9dda5b0d5b1a84effdf98d2175ae0dd11d6`. Worker-0's
  measurement (base bytes == HEAD bytes) VERIFIED independently:
  identical hash. Nil committed delta across the HEAD move for this
  target.
- HEAD (`0c0537e2`, unmoved between dispatch and this trace):
  `HEAD:django_strawberry_framework/extensions/error_policy.py` =
  `7ee4e9dd…` (460 lines). All tracing below is against these bytes.
- Worktree: `a1defd394d8eda9b698964030a09efe6914278db` (425 lines).
  `git diff HEAD` shows exactly 7 hunks, 33+/68-, attributed by
  content below. Left untouched.
- Item baseline `d51a3ca5d0e5013b95fec8285eb4f2e5de9911d0` carries
  blob `a1defd39` for this path, so the item-scoped diff is empty (0
  bytes): the dirt predates the item and no stop is owed. This
  artifact itself is untracked (`??`), the only path written.

Hunk attribution (`git diff HEAD`, 7 hunks):

- Hunk 1 (module docstring): the three-sites rationale sentences —
  "The three sites become one only if the engine offers a single
  hook that sees every yielded frame and every result built after
  teardown; until then a check moved to any one of them observes
  different state than the other two." — OWNED: matches the
  `## Owned changes` ledger row (adopted orphan
  `subscription-per-event-error-masking`, three-sites rationale
  docstring) BY CONTENT, present verbatim at worktree lines 42–45,
  absent at HEAD (0 hits). Locator nuance, stated honestly: the
  plan's Family line places the rationale "on
  `::mask_execution_result`"; the bytes sit in the module docstring's
  three-seam paragraph. Content match is exact.
- Hunks 2–7 (imports `+ImproperlyConfigured` / `+truth`;
  `_degraded` docstring reword + guarded-read removal;
  `masking_is_active` enabled-`try` removal + `except` narrowed to
  `(AttributeError, ImproperlyConfigured)`; `schema_error_policy`
  `try` removal + `isinstance` → `truth.is_exact`;
  `on_operation` teardown-`try` removal): concurrent-EXTERNAL. No
  ledger row names these contents; the ledger's only row on this
  path is the docstring hunk above. Untouched, not a stop (zero
  production edits by this item).

Delta scoped fresh (prior stamp `16f47547` at bfaee91d ->
`7ee4e9dd` HEAD, blob diff, six sites, nothing else, commit
`9350eb8d`): (1) import line `DEFAULT_ERROR_POLICY` ->
`_PACKAGE_ERROR_POLICY`; (2) `_degraded` floor fallback, same
retarget; (3) `schema_error_policy` docstring "DEFAULT_ERROR_POLICY"
-> "the package's own policy"; (4–5) `schema_error_policy` both
code fallbacks, same retarget; (6) `on_operation` teardown-floor
fallback, same retarget. Numstat 6+/6-. Matches the dispatch
record exactly; no other drift exists between stamp and HEAD for
this target.

Freshness fingerprints (HEAD blobs, short; every file actually
inspected this pass): target `7ee4e9dd`, `error_policy.py`
`1a19cd7d`, `consumers.py` `936210e2`, `schema.py` `e6b52335`,
`extensions/debug.py` `bf25c146`, `extensions/operation_state.py`
`b2674a22`, `utils/policies.py` `8c881c0a`, `__init__.py`
`0ef72601`, `extensions/__init__.py` `dc3ebdc2`,
`extensions/resource_policy.py` `19e2309d`,
`tests/test_error_policy.py` `58129ec2`,
`test_error_policy_api.py` `20cf3807`. Note: `schema.py` reads
`e6b52335` here vs `19f90bf5` in the verified `utils/policies.py`
artifact because HEAD moved (`5ee86193` -> `0c0537e2`, async-window
rewrite `1b6a09b1` + `982537c3`); every `schema.py` cite below was
re-verified at `e6b52335`, and the install chain plus both seam
bodies are unaffected except the one-line floor seed recorded
under F1. The verified File `utils/policies.py` outcome (`Status:
verified`, run 5, HEAD-bytes trace) is cited for the
canonical-copy split wherever it touches this target: its F2
(`policy-authority-isolation`, open) owns the
template/canonical/resolved split and already classifies this
file's three fallback-read shapes as internal reads, citing this
exact HEAD blob `7ee4e9dd`; the verified File `error_policy.py`
run-7 re-trace covers the `_PACKAGE_ERROR_POLICY` declaration
side. Connected worktree files carry concurrent hunt dirt (all
`M` except the root and leaf, which are CLEAN); every cite below
is HEAD bytes, never worktree.

### Enumeration (fresh, HEAD bytes)

Instrument: `ast.parse` over `git show HEAD:` bytes. **23 top-level
statements** (same 23 as the prior re-trace; structure identical,
only the import row's token changed) plus all 4
`DjangoErrorPolicyExtension`-body members. Every member lands below.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (three-seam account, copy contract, install position, sync/async unity) | (none) | F1 owned prose + R1 projection (install position) |
| 2 | `from __future__ import annotations` | annotations | machinery |
| 3 | `import copy` | `copy` | machinery for F1 copy-contract |
| 4 | `from collections.abc import Iterator` | `Iterator` | machinery (`on_operation` generator) |
| 5 | `from typing import Any` | `Any` | machinery |
| 6 | `from django.conf import settings` | `settings` | F1 consumer edge (DEBUG read) |
| 7 | `from graphql import GraphQLError` | `GraphQLError` | machinery (F1 builder) |
| 8 | `from graphql.execution import ExecutionResult as GraphQLExecutionResult` | shape arm | F1 shape gate |
| 9 | `from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult` | shape arm | F1 shape gate |
| 10 | `from .. import logger` | `logger` | F2 consumer |
| 11 | `from ..error_policy import _PACKAGE_ERROR_POLICY, ErrorPolicy, new_correlation_id` | 3 names (REVISEd token) | F1 configuration edge (root error_policy) |
| 12 | `from .operation_state import _OperationBoundExtension` | base | consumer edge (base owned at operation_state; F5) |
| 13 | `__all__ = […5…]` | leaf manifest | R2, file-local |
| 14 | `def _is_unexpected` | classifier | F1 |
| 15 | `def _masked` | replacement builder | F1 |
| 16 | `def _degraded` | floor | F1 |
| 17 | `def degraded_result` | whole-response floor builder | F1 |
| 18 | `def masking_is_active` | activation gate | F1 |
| 19 | `def is_maskable_result` | shape gate | F1 |
| 20 | `def schema_error_policy` | policy reader | F1 |
| 21 | `def mask_execution_result` | application | F1 OWNER |
| 22 | `def _replacement_for` | per-entry degrade | F1 |
| 23 | `class DjangoErrorPolicyExtension` (`_OperationBoundExtension`) | teardown site | F1 |
| 23.1 | class docstring (entry-refusal + per-operation-state + DEBUG pass-through) | (none) | F1 owned prose; authority-refusal prose projects `schema.py` declaration-folding (R1) |
| 23.2 | `def _policy` | policy read | F1 (calls `schema_error_policy`) |
| 23.3 | `def _process_result` | in-place adoption | F1 (calls `mask_execution_result`) |
| 23.4 | `def on_operation` | teardown | F1 |

Verdict: enumeration CONFIRMed (23/23 + 4/4, same kind sequence,
same 9-function order, `__all__` still 5 names); only row 11's
imported token is REVISEd (DEFAULT -> _PACKAGE). 460 lines.

### Matrix (re-discharged at HEAD)

**1. Cross-flavor mirroring.** CONFIRM. Masking vocabulary still
only here, the seam, `schema.py`, oracles/projections (package
sweep re-run at HEAD: each masking `def` occurs in exactly one
production file — the `_masked`/`_masked_return` stem share is the
confirmed consumer method, not a redefinition). The resource twin
re-compared fresh at HEAD `19e2309d` (still `on_parse` /
`on_validate` budget gating; install first-vs-last in the
byte-identical `_admitted_chain`). J1 stands. Discharged.

**2. Sync/async twins.** CONFIRM. Still no twin owed: zero
`AsyncFunctionDef`, the single textual `await` still inside the
`_is_unexpected` docstring; the seam's async-ness is the
transport's and calls the shared sync application; the schema
return seam still exists in both `execute` color twins as one-line
calls. Zero `sync_to_async`. Discharged by absence with reason.

**3. Derived knowledge.** REVISE wording, verdict unchanged. Policy
values still read by attribute; the composed-by-name fallback is
now `_PACKAGE_ERROR_POLICY` (import + 4 code sites; `git grep -c`
5 in target, `DEFAULT_ERROR_POLICY` 0); one code `settings.DEBUG`
read (line 250; the second hit is docstring prose); four `getattr`
location kwargs still arguments of the single `_masked` call
(lines 172–175). J2 stands. Discharged.

**4. Round-trip pairs.** CONFIRM. Still no pair by contract: no
unmask, ids minted never parsed back, copy-not-mutate unchanged.
`degraded_result` still the one floor definition:
`StrawberryExecutionResult(data=None` occurs exactly once
package-wide at HEAD (the builder body). Discharged with reason.

**5. Media.** REVISE fingerprints, verdict unchanged. Production
(this file); consumers composing by name — seam's four-helper
function-local import + single mask call (consumers.py HEAD
`936210e2`, byte-identical to the prior stamp: policy read 1377,
gates 1384, mask 1385), `schema.py` five-name import + single mask
call at 1184 + floor call at 1190 (`_masked_return` 1151–1190,
diffed old-vs-HEAD: exactly one changed line, the floor seed
`DEFAULT` -> `_PACKAGE`; zero local classifier/builder/gate),
leaf/root class bindings (both CLEAN, blobs unchanged); oracles —
unit suite at HEAD `58129ec2` (copy-contract pair + return-seam
identity row all present by `def` census; suite pins
`DEFAULT_ERROR_POLICY` 56× as the template and `_PACKAGE_*` 0×,
which is the template-pinned oracle shape the canonical split
expects) plus live matrix at HEAD `20cf3807` (all three key rows
present; still imports no masking-owner name); projections — both
module docstrings naming each other's seam (verified both
directions at HEAD; the consumers function sentence is stale ->
D1 stands). Discharged.

**6. Omission.** CONFIRM. Closed 4-case partition byte-identical;
located-error wrap, per-entry + whole-result + unreadable-list
degrades, hostile reads degrading fail-closed per entry,
shape-gate frame exclusion, `PreExecutionError` contributing
nothing, DEBUG pass-through — all re-read at HEAD bytes.
Deliberate omissions unchanged. The whole-response floor still has
one spelling shared by all four landing sites (exactly-once
census above). Discharged.

### Challenges (counts are authoritative definitions only)

C1–C8 re-run unchanged → 1 each here (classifier, replacement,
shape gate, activation gate, policy reader, copy contract, floor
wording, per-entry degrade). C2's key-axis note is REVISEd: rename
`correlationId` -> the root moves (template plus its canonical
declaration, both in the root file per the verified error_policy
re-trace), still 0 here. C9 → 0 here / 1 at
[schema.py][schema.py]`::_admitted_chain` (R1; chain body
byte-identical old-vs-HEAD). C10 fired-as-foretold stands; no
fourth seam arrived (package-wide `def` census + seam-body
re-reads). C11 → 1 here / 0 at root (same five call sites,
identical lines 164/341/355/417/448). C12 → R2 separation (five
names). C13/C14 refused (J1/J2, re-derived). C15 → 1
(`degraded_result`; all four landing sites follow). C16 → 0 new
(recorded trigger: composes helpers + floor by name). New-shape
challenges: none owed — the drift introduces no new member, no new
branch, no new seam; the one new name this target reads
(`_PACKAGE_ERROR_POLICY`) is a declaration of the already-indexed
verified family `policy-authority-isolation`, whose record
classifies these reads (message attribute, schema fallbacks
flowing only to masking field reads, teardown fallback). Posit a
fallback-authority change (e.g. re-home the canonical copy) -> 1
at [utils-policies][utils-policies]`::canonical_policy` plus its
declarations, 0 new here: this file keeps reading the imported
name.

### Findings

**F1 — `subscription-per-event-error-masking` (REVISEd,
owner here, stays `open`).** Contract, sites, roles, challenges
as in the prior F1, except the configuration edge: this file now
composes `_PACKAGE_ERROR_POLICY` by name at 6 sites (import,
`_degraded` floor, `schema_error_policy` docstring + both code
fallbacks, teardown floor) instead of `DEFAULT_ERROR_POLICY`.
That retarget is the canonical-copy split, owned and verified
elsewhere: the verified File `utils/policies.py` F2
(`policy-authority-isolation`) classifies exactly these reads as
internal (never exposed to a consumer surface) and cites this
HEAD blob; the verified File `error_policy.py` re-trace owns the
declaration (`canonical_policy(DEFAULT_ERROR_POLICY, …)`). The
configuration-vs-application split drawn at the import edge holds
in both directions probed (C2 revised axis above; C6 unchanged).
Consumers re-verified at HEAD: teardown chain (in-file),
[consumers.py][consumers.py]`::_stop_aware_results` (sole
external per-event caller, byte-identical file, four-helper
import, one mask call, zero local masking rule),
[schema.py][schema.py]`::DjangoSchema._masked_return` (one-line
floor-seed drift only, shared gates, one mask call, shared floor,
zero local classifier/builder/gate). Trigger re-checked fresh:
still exactly three seams, all composing by name; no restated
classification, no local replacement builder, no local gate; no
fourth seam by package-wide `def` census over 117 HEAD `.py`.
Owner unchanged. No stored derivation here. Behavioral proof:
`execution-verified` for import direction, shape census, call
counts, absence vocabulary, floor-call census (read-only probes
against `git show HEAD:` bytes + `git grep HEAD`, no source
mutation, no Django import, no DB, no workspace copy owed);
`static-reviewed` for seam/teardown/return bodies (no shared-tree
pytest per item rules). Structural gate: copy-contract pair +
return-seam identity row + once-only hook row (all present at
HEAD by `def` census); negative control honestly
`static-reviewed` as before. Coupling: none (zero edits).
Freshness: every blob under "Scope, attribution, fingerprints";
population 117 `.py` at HEAD.

**F2 — `logger-single-sourcing` (CONFIRM, consumer row, stays
`open`).** Still no definition here: one `from .. import logger`,
zero `getLogger`, five call sites at identical lines
164/341/355/417/448 with the same five roles; package root blob
identical (`0ef72601`, CLEAN). C11 split unchanged. Trigger: a
`getLogger` here. Freshness: target + root as above.

**F3 — `typed-rejection-value-tail` (CONFIRM, not a member).**
Zero `describe_value`, zero `ConfigurationError` (re-grepped HEAD
bytes); only strings are the stable mask message (read, never
built) and log prose with no interpolated outside value.
Trigger: any tail renderer appearing here.

**F4 — `sealed-execution-queryset` (CONFIRM, not a member).**
Zero `QuerySet`/`queryset` vocabulary (re-grepped); rewrites
result `errors` lists post-execution only. Trigger: any queryset
read/seal here.

**F5 — `operation-bound-extension-mechanism` (CONFIRM, base-class
role only).** Base blob identical (`b2674a22`); class still holds
only docstring + `_policy`, `_process_result`, `on_operation`; no
scope/bind/resume machinery defined here. Per-operation-state
lifetime change -> 0 here / 1 at the base; masking change -> 1
here / 0 at the base. Trigger: any runner-scope/bind/unbind
definition appearing here.

**R1 — install-position + entry-authority prose (CONFIRM,
file-local projection of `schema.py`).** `_admitted_chain` body
byte-identical old-vs-HEAD (`[DjangoErrorPolicyExtension(),
*resolved, DjangoResourcePolicyExtension(), …]`); the FRONT
paragraph and the class refusal paragraph still describe rules
`schema.py` owns (C9 → 0/1). Trigger: `schema.py` ceasing to own
chain order.

**R2 — leaf manifest (CONFIRM, file-local).** Still five names;
C12/C15 separation unchanged. The root re-export shape still does
not apply (same-file mirror, one edit region — checked, not a
member). Trigger: a second manifest over these names.

**J1 — error/resource enforcement unification (CONFIRM,
refused, stands).** Re-compared fresh at HEAD blobs: pre-execution
budget gating over `on_parse`/`on_validate`, append-last, numeric
bounds + deadline vs post-execution message rewrite in one
`on_operation` teardown, prepend-first, three string/bool options
+ neutral message; `narrowed` one-sided; ladders/copies/tails
already shared at [utils-policies][utils-policies] +
[exceptions-py][exceptions-py]. One side moves per change.
Trigger + home unchanged.

**J2 — location-field copy helper (CONFIRM, refused, stands).**
Four `getattr` kwargs still arguments of the one `_masked` call;
the floor builder still retains no locations, so the refused
trigger (a second retaining call) did not fire. Home unchanged.

### Defects (run-7 re-trace)

None new. D1 (prior, owner `consumers.py`) STANDS unchanged:
[consumers.py][consumers.py]`::_stop_aware_results` docstring
still reads "two application sites" while three are live, and
that file is byte-identical to the prior stamp (`936210e2`), so
the sentence was re-verified rather than assumed. Prose-only, no
wire impact (composition verified by name on all three sites at
HEAD), not a release blocker per the prior W2 adjudication
(recorded above; no contract row broken, no wire or configuration
input reaches it). Homing from the prior artifact stands (NAMED
owning card via the `consumers.py` re-trace / holding family).

### Judgment (run-7 re-trace)

Backstop discharged at HEAD bytes `7ee4e9dd`: 23/23 members + 4/4
class members enumerated, matrix re-discharged on all six axes,
16 challenges re-run, every rule terminating in F1 (REVISEd owner
record: canonical fallback reads, still 1 per axis here) / F2
consumer / F5 checked base-role / F3–F4 checked non-members /
R1–R2 file-local / J1–J2 refusals — no consolidation owed (file
item performs none), no new defect, no new family named. The
drift since the prior stamp is exactly the six-site canonical
retarget, owned at verified `policy-authority-isolation` and
converged onto (not duplicated) here. Zero-edit result is
legitimate. `## Pending execution`: none (read-only HEAD-bytes
probes + `git grep HEAD` already ran; no mutation, no Django, no
DB, no workspace owed; no shared-tree pytest per item rules;
oracle bodies `static-reviewed`; sharded/Postgres cells
`inapplicable by construction` — pure result rewriting plus one
bool `DEBUG` read, unchanged by the drift).

## Index rows for Worker-0

(Worker-0 alone edits the plan; rows named here for transcription.
No new family is named and no plan-index text changes: every
family this target touches is already indexed with this file
listed, and the one REVISEd finding revises artifact wording
only.)

- CONFIRMed, unchanged text: `policy-authority-isolation` (open;
  already lists `extensions/error_policy.py`; this file's three
  fallback-read shapes converge onto its verified F2 record, HEAD
  blob `7ee4e9dd` as cited there); `logger-single-sourcing`
  (open; consumer census re-verified, no change);
  `typed-rejection-value-tail`, `sealed-execution-queryset`
  (open; checked, still non-members);
  `operation-bound-extension-mechanism` (base-role only, base
  byte-identical); J1/J2 refused shared forms (triggers unfired).
- REVISEd at artifact level, no transcription owed:
  `subscription-per-event-error-masking` (verified family item;
  F1 owner record now reads the canonical fallback at 6 sites,
  seam census re-verified with the schema floor-seed one-liner,
  trigger re-checked fresh — family row untouched); R1/R2
  file-local records (re-verified, no index rows); D1 prose
  defect (stands, homing unchanged).
- New rows: none.

## Independent verification (Worker-2, run 7)

Expectation-first note, stated honestly: this pass re-derived every
count, hash, and site role from source (own `ast` dump over `git show
HEAD:` bytes, own `git grep HEAD` sweeps, own blob hashes), then
reconciled against W1's run-7 section. Agreements below are
reconciliations, not repetitions. Verdict: **verified** — every
judgment stands.

Own trace (HEAD bytes `7ee4e9dd`, 460 lines): 23 top-level statements
(docstring, future, copy, Iterator, Any, settings, GraphQLError, both
result shapes, logger, config trio with the `_PACKAGE_ERROR_POLICY`
token, base, `__all__`, 9 functions in prior order with
`degraded_result` after `_degraded`, class), `__all__` 5 names,
`DjangoErrorPolicyExtension` 4 members (docstring + `_policy`,
`_process_result`, `on_operation`), zero `AsyncFunctionDef`, one
textual `await` at line 117 inside the `_is_unexpected` docstring.
Masking defs each occur in exactly one production file (the
`_masked`/`_masked_return` stem share is the confirmed schema
consumer, not a redefinition); `mask_execution_result(` has exactly
three production callers (in-file teardown, consumers.py:1385,
schema.py:1184) — no fourth seam. Owner I would choose: here for the
masking cluster, the root record for configuration, the package root
for the logger. Identical to W1 and the plan index.

Per-judgment results:

1. Enumeration: CONFIRM stands. 23/23 + 4/4 re-derived member by
   member; kind sequence and 9-function order match W1's table; only
   row 11's imported token changed (DEFAULT -> _PACKAGE).
2. Hunk attribution: CONFIRM stands. Hunk 1 is the pure-additive
   module-docstring three-sites rationale, verbatim at worktree lines
   42–45, 0 hits at HEAD — exact content match to the ledger's only
   row on this path (adopted orphan
   `subscription-per-event-error-masking`, three-sites rationale
   docstring). W1's locator nuance (Family line says "on
   `::mask_execution_result`", bytes in the module docstring) is
   accurate. Hunks 2–7 match W1's description line for line
   (`+ImproperlyConfigured` / `+truth`, `_degraded` reword +
   guarded-read removal, `masking_is_active` enabled-`try` removal +
   narrowed `except`, `schema_error_policy` `try` removal +
   `isinstance` -> `truth.is_exact`, `on_operation` teardown-`try`
   removal); no ledger row names them — concurrent-external,
   untouched, not a stop.
3. Drift scope: CONFIRM stands. Blob diff `16f47547` -> `7ee4e9dd`
   is exactly 6 changed lines (12 diff lines, 6+/6-), all
   DEFAULT -> _PACKAGE retargets at W1's six sites (import,
   `_degraded` floor, `schema_error_policy` docstring + both code
   fallbacks, teardown floor); commit `9350eb8d` stat shows this
   file at 12 changed lines. Nothing else drifted.
4. The 8 CONFIRMs: all stand, each spot-probed independently —
   F2 (one logger import, zero `getLogger`, five call sites at
   identical lines 164/341/355/417/448, root blob identical and
   CLEAN); F3/F4 (zero `describe_value` / `ConfigurationError` /
   `QuerySet` / `queryset` / `sync_to_async`, re-grepped); F5 (base
   blob identical, class holds no scope machinery); R1
   (`_admitted_chain` body byte-identical `5ee86193` vs HEAD, error
   FIRST / resource LAST); R2 (five names); J1 (twin still
   `on_parse` / `on_validate` budget gating at `19e2309d`,
   inverse install positions); J2 (four `getattr` kwargs still
   arguments of the one `_masked` call, lines 172–175; floor
   retains none). Supporting censuses also re-derived: `_PACKAGE`
   5 / `DEFAULT` 0 in target, one code `settings.DEBUG` read
   (line 250; the second `settings.DEBUG` hit is class-docstring
   prose), floor spelling once package-wide (line 225),
   `consumers.py` seam (import + policy 1377, gates 1384, mask
   1385), `_masked_return` 1151–1190 with mask 1184 / floor 1190
   and exactly one `bfaee91d`-vs-HEAD line (the floor seed;
   `5ee86193`-vs-HEAD is 0 lines), copy-contract pair +
   return-seam identity rows present, unit suite DEFAULT 56x /
   _PACKAGE 0x, live matrix three key rows present with no
   masking-owner names, population 117 `.py` at HEAD.
5. F1 REVISE: ENDORSED. The configuration edge retargeted at 6
   sites (proven by the blob diff); artifact wording only — the
   verified family item's owner record is untouched, and the
   retarget changes which imported name this file reads, not
   which findings own which rules.
6. Family convergence: ENDORSED. Verified File `utils/policies.py`
   F2 (`policy-authority-isolation`, `Status: verified`) cites
   this exact HEAD blob `7ee4e9dd` and classifies these reads as
   internal; the plan index row already lists this file; the
   verified File `error_policy.py` run-7 re-trace owns the
   declaration side.
7. NO plan-index text changes: ENDORSED. Every family touched is
   already indexed with this file listed (`policy-authority-isolation`
   row verified in plan); J1/J2 triggers unfired; the REVISE
   revises artifact wording only. No transcription owed.
8. D1 STANDS; zero-new-defect call STANDS. `consumers.py` is
   byte-identical to the prior stamp (`936210e2`); the stale
   "two application sites" sentence re-verified at :1321;
   prose-only, no wire impact, prior W2 adjudication (not a
   release blocker) stands with homing unchanged. No new defect
   found: the drift is a pure six-site retarget and every census
   holds.

Freshness: all 12 W1 fingerprints re-hashed — every one matches
(target `7ee4e9dd`, `error_policy.py` `1a19cd7d`, `consumers.py`
`936210e2`, `schema.py` `e6b52335`, `extensions/debug.py`
`bf25c146`, `extensions/operation_state.py` `b2674a22`,
`utils/policies.py` `8c881c0a`, root `0ef72601`, leaf `dc3ebdc2`,
`extensions/resource_policy.py` `19e2309d`, unit oracle `58129ec2`,
live oracle `20cf3807`). Drift base `5ee86193` bytes == HEAD bytes
re-verified (identical hash). Item baseline `d51a3ca5…` carries
`a1defd39` for this path, so the item-scoped diff is empty; window
diff vs baseline names the plan (Worker-0's, tracked) plus this
untracked artifact only — nothing concurrent. No production edits
by W1 or W2; no plan edits by W2. `## Pending execution`: none,
correctly (read-only HEAD-bytes probes + `git grep HEAD`, no
mutation, no Django, no DB, no workspace owed; no shared-tree
pytest per item rules; sharded/Postgres inapplicable by
construction — pure result rewriting plus one bool `DEBUG` read).
AGENTS.md prose: no tracked `.py` touched (artifact `.md` only),
so no ruff surface; citations above reuse the artifact's existing
reference-style link groups; no commit. HEAD `0c0537e2` unmoved
between dispatch and this verdict.
