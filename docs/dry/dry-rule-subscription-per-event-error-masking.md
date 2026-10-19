# DRY review: `subscription-per-event-error-masking`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `subscription-per-event-error-masking`. Provisional owner
`extensions/error_policy.py::mask_execution_result`. Seed sites
`extensions/error_policy.py` teardown, `consumers.py:1385` per-event,
`schema.py:1083` return seam; re-derived below, not trusted. Prior
records used only as rejected-candidate triggers: the three file items
re-traced at `bfaee91d` (`schema.py` R7 return seam as consumer composing
4 gates by name; `extensions/error_policy.py` F1 masking cluster as owner
incl. the shared floor `degraded_result`, C10 fired-as-foretold;
`consumers.py` F3 per-event consumer site + D1 prose drift). Never read
any `worker-memory/`.

## System trace

Rule: per-event error masking — each subscription event, and each
returned result, is masked exactly once by the operation's error policy.
One classifier, one replacement builder with its floors, one shape gate,
one activation gate, one policy reader, one pure application
(`extensions/error_policy.py::mask_execution_result`); three application
sites, each composing by name, none restating.

What each seam sees, and what masking means there:

- **Teardown**
  (`extensions/error_policy.py::DjangoErrorPolicyExtension.on_operation`
  → `_process_result` → `mask_execution_result`). Sees the completed
  result assigned to `execution_context.result`: the whole response for a
  query/mutation run through `schema.execute`/`execute_sync` and finished
  normally; only the operation's end for anything streamed. Masking
  means classify-then-replace under `masking_is_active` +
  `is_maskable_result`, adopted IN PLACE onto the engine's result object
  (all three fields, so the fail-closed degrade drops `data` too).
- **Per-event** (`consumers.py::_stop_aware_results`). Sees each in-flight
  yielded value before the transport renders it: one `ExecutionResult`
  per subscription event, or the single result of a query/mutation run
  over `stream`, yielded from inside the operation lifecycle. Masking
  means the same classify-then-replace returning a COPY, so the engine's
  object keeps its originals for the extensions that read
  `GraphQLError.original_error` (notably `debug.py`). Policy resolved
  once per subscription; `DEBUG` gate read per event. The shape gate lets
  an unmaskable incremental-delivery frame reach upstream's own refusal
  instead of being degraded into a shape that refusal no longer
  recognizes.
- **Return** (`schema.py::DjangoSchema._masked_return`). Sees the value
  `execute`/`execute_sync` hand back: the teardown's result on the normal
  path, but a FRESH result built by upstream's outer `except` when an
  exception escaped any hook after every teardown unwound (verified in
  the installed Strawberry `Schema.execute_sync`/`Schema.execute`
  bodies). Masking means the same gates + application + floor under the
  enforcement-record policy; structurally idempotent, so a second pass is
  a no-op by identity (no second id minted, no second log record).

Connected sources read for judgment, outside the seeds:
`django_strawberry_framework/error_policy.py` (full: record, validation,
ladder, mint — configuration half, one-way import edge confirmed);
`django_strawberry_framework/extensions/operation_state.py` (module head:
per-operation binding — teardown reads the result off the bound engine
context, which is why the mask lands on the right operation);
`django_strawberry_framework/extensions/debug.py` (ordering passages: the
`original_error` reader the copy contract protects); installed
`.venv` `strawberry/schema/schema.py::Schema.execute_sync`,
`::Schema.execute` (outer-`except` coercion after teardown), and
`::Schema.subscribe` (thin wrapper over `stream` — no override owed);
`tests/test_error_policy.py` return-seam + copy-contract rows (bodies
read); `examples/fakeshop/test_query/test_error_policy_api.py` hook rows
(names verified present); `tests/test_routers.py` partition +
incremental-frame + async-iterator rows (names verified present).
Excluded on strength of body: every flavor folder (zero masking
vocabulary — flavors participate by raising deliberate `GraphQLError`,
which the classifier leaves untouched), `views.py` / `routers.py` (no
masking call), upstream `MaskErrors` (prose mentions in `debug.py` only;
never installed).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Masking vocabulary lives only in
   the owner, the two external seams, and oracles/projections (package
   sweep re-run). No sibling flavor masks. The resource-policy twin is a
   different rule (pre-execution budget gating, append-last) vs this
   post-execution rewrite (prepend-first) — compared, not assumed.
2. **Sync/async twins.** No masking twin owed: the teardown is one sync
   generator the engine enters on both paths; the seam's async-ness is
   the transport's and calls the shared sync application. The
   `execute`/`execute_sync` override pair is the schema's placement
   adapter (one `super()` call + one `_masked_return(` each), not a
   masking twin.
3. **Derived rather than repeated knowledge.** Policy values read by
   attribute; `DEFAULT_ERROR_POLICY` composed by name; one
   `settings.DEBUG` read; four location `getattr` kwargs in one call;
   the floor spelled once (`degraded_result`). No reconstructed copy.
4. **Inverse / round-trip pairs.** No unmask; correlation ids minted,
   never parsed back; copy-not-mutate owns its side (C-C proves the
   split). Mask-twice idempotence is structural, not a flag.
5. **Contracts restated in another medium.** Production (owner + three
   composing sites); independent oracles (below — all spell literals,
   none reads the owner to enumerate, except one pre-existing private
   floor unit pin, honestly noted); projections (both module docstrings
   naming each other's seam, verified both directions at `bfaee91d`;
   install + return-seam paragraphs; debug ordering paragraph).
6. **Enforcement by omission.** Closed 4-case classifier partition;
   per-entry + whole-result degrades; hostile reads fail closed;
   incremental frames excluded by the shape gate (deliberate — masking
   one would defeat the transport's own refusal); `PreExecutionError`
   admitted contributing nothing; `DEBUG` pass-through. The plain
   `strawberry.Schema` hole (no return seam there) is stated in both
   docstrings, not an omission. No member lacks a guard its contract
   requires.

### Enumeration

Instrument: `ast.parse` over the worktree blobs + package-wide token
sweeps over the 117-file population (`git ls-files
'django_strawberry_framework/*.py'` = 117). Every member assigned;
every challenge ends in the family row, a file-local record, or a
recorded rejection (none — no second rule found).

- `def mask_execution_result`: exactly 1 (owner). Calls: exactly 3 —
  teardown (`extensions/error_policy.py`, line 410), per-event
  (`consumers.py`, line 1385), return (`schema.py`, line 1083).
- `def degraded_result`: exactly 1 (owner). Calls: exactly 4 — the three
  in-file floors plus the return-guard (`schema.py`, line 1089).
- `def _is_unexpected` / `::_masked` / `::_degraded` /
  `::_replacement_for`: exactly 1 each, all in-file; zero production
  hits outside the owner.
- Gates/readers (`masking_is_active`, `is_maskable_result`,
  `schema_error_policy`): exactly 1 def each; composed by name at all
  three sites (teardown, seam gates at `consumers.py`, lines
  1377/1384, return gates at `schema.py`, line 1081).
- Placements (`_masked_return`, `_stop_aware_results`): exactly 1 def
  each; the overrides/wrapper call them once per entry point.
- `StrawberryExecutionResult(data=None`: exactly 1 package-wide (the
  floor builder body) — a seam degrading by hand is detectable by
  census.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C-A | New error class: a new deliberate-rejection shape, or a new plain-exception kind reaching the wire | **1** (`_is_unexpected`; all three sites follow with zero edits) |
| C-B | New operation type: a new streamed kind, or a new executor entry needing coverage | **0 existing moved** (the new site becomes a consumer composing the four helpers + floor by name — the C10/C16 fired-as-foretold precedent: the schema return seam landed exactly this way); a new result flavor moves `is_maskable_result` (**1**, all sites follow) |
| C-C | Mask-twice path: a teardown-masked result meeting the return seam; a per-event-masked frame meeting teardown at end | **0 moved** (exactly-once is structural: `original_error=None` reads deliberate, `mask_execution_result` answers by identity — executed in the workspace proof: second pass `is` first, one id, one log record) |

Corroborating axes (same pattern, not separately counted as rules): a
new publish shape moves `_masked` (1); a floor-shape change moves
`degraded_result` (1, four landing sites follow); a gate-input change
moves `masking_is_active` (1). Count stays 1 per axis at exactly one
owner each.

**Experiment (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/subscription-per-event-error-masking
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
```

Proof (`W1 FAMILY PROOF: ALL OK`): 117-file AST walk (single defs for
`mask_execution_result`, `degraded_result`, `_is_unexpected`,
`_masked_return`, `_stop_aware_results`); schema-module helper identity
(`sm.<helper> is ep.<helper>` for all four); seam single-call +
owner-import check by source; mask-twice identity with one 32-hex
correlation id and intact engine originals; deliberate passthrough by
identity; shape gate accept/reject; `masking_is_active` failing toward
masking on unreadable `DEBUG`. Status: `execution-verified`. Rejects
"a seam restates classification", "a fourth site exists", "mask-twice
double-logs". The one server-side log line in the output is the single
expected record for the one masked error. Copy `__file__`:
`.../dry-ws/subscription-per-event-error-masking/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/subscription-per-event-error-masking/examples/fakeshop/db.sqlite3`
(copy's own tree and database; never the shared tree). No source
mutation in the proof; restores N/A (nothing mutated).

## Findings

### F1 — subscription per-event error masking (REJECTED consolidation: three seams correctly compose one rule)

- **Contract + variation.** Each subscription event, and each returned
  result, masked exactly once by the operation's error policy.
  Variation: policy values (read by attribute) and result shapes
  (admitted pair vs incremental frames).
- **Sites + roles.** *Definition*: the masking cluster in
  `django_strawberry_framework/extensions/error_policy.py`
  (`mask_execution_result` owner with `_is_unexpected`, `_masked`,
  `_degraded`, `degraded_result`, `_replacement_for`,
  `is_maskable_result`, `masking_is_active`, `schema_error_policy`,
  `DjangoErrorPolicyExtension`). *Consumers*: the teardown (owner
  side), `consumers.py::_stop_aware_results` (sole external per-event
  caller), `schema.py::DjangoSchema._masked_return` (return caller).
  *Oracles*: `tests/test_error_policy.py` (identity no-op, copy-contract
  pair, three return-seam rows, hostile-shape rows — bodies read);
  `examples/fakeshop/test_query/test_error_policy_api.py` (resolver
  matrix + 6 hook rows over `where` x `color` + DEBUG/opt-out/deliberate
  rows — names verified present); `tests/test_routers.py` (stop-aware
  partition + incremental-frame + async-iterator rows — names verified
  present). All spell literals independently; none enumerates the owner.
  *Projections*: both module docstrings (each names the other's seam),
  install + return-seam paragraphs, debug ordering paragraph.
- **Challenges.** C-A → 1; C-B → 0 existing (+1 only for a new result
  flavor, at the gate owner); C-C → 0 (structural idempotence,
  executed). Count > 1 nowhere: no duplication.
- **Owner + lifetime (principles 7, 4).** `extensions/error_policy.py`
  stands: every legitimate consumer already imports it without reversing
  a dependency (the seam imports it function-locally precisely to keep
  the channels/strawberry-free import graph); the root record cannot own
  engine behavior without importing strawberry/graphql-core upward
  (dependency direction wins over narrowness); the schema owns placement
  (only it sees the returned value), never classification. Host-module
  size is not a criterion. Lifetime: no stored derivation at the owner
  (pure function, call-locals only). Per-operation state lives where the
  operation lives and dies — teardown reads the bound engine context
  (operation-state base), the seam holds one policy per generator
  (validity: the executing schema object; `DEBUG` re-read per event, the
  same granularity as teardown), the return seam reads the enforcement
  record per call. Nothing cached, nothing invalidated; masking
  decisions are per-operation by construction.
- **Migration.** Production behavior: none (zero behavior hunks).
  Projection: one trigger clause added at the owner module docstring
  (below). No call-site change at any seam.
- **Distinct behavior (stays separate).** Per-error granularity, the
  copy-vs-adopt split (debug reads originals), the shape-gate exclusion
  (transport refusal intact), in-place teardown adoption vs yielded copy
  vs returned value — each is its transport's requirement, never a
  shared rule. Moving any check earlier observes different state:
  teardown-only misses in-flight events already on the wire;
  per-event-only misses the post-teardown coerced result; return-only
  misses streamed frames (which never pass through `execute`).
- **Behavioral proof.** `execution-verified` for composition identity,
  census counts, idempotence, gates (workspace proof + the one
  authorized shared-tree focused run:
  `uv run pytest tests/test_error_policy.py::test_the_return_seam_passes_an_already_masked_result_through_by_identity --no-cov -n0 -q`
  → 1 passed); `static-reviewed` for teardown/seam/return bodies and
  both upstream `except` bodies. Observable wire behavior pinned:
  masked text == policy message, fresh `correlationId` per masked error
  joined to exactly one server log record with traceback,
  `original_error` never on the wire, floor shape (`data=None`, single
  message-only error, no extensions). Rejects "the seams duplicate" and
  "a moved check sees the same state".
- **Structural gate.** Deferred with reason: every behavior oracle
  passes a hand-copy negative control by construction (the copy is
  correct), so no behavioral gate can pin unity — only a source census
  could, and that is a bespoke existence test per helper, which
  [DRY.md][dry] forbids for gate-only findings. Coverage that stays: the
  copy-contract pair, the return identity row, the hook rows, the
  per-event + incremental rows — each fails a real masking break (the
  return-seam rows landed with the seam as the intentional contract
  change). Unity rests on the one-way import edge + the recorded
  trigger, which re-opens the family on a fourth site or a restated
  classifier.
- **Coupling.** None.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `extensions/error_policy.py`
  `bd763bcc428ce0f495448e6d228061dd0bc08688` (post-trigger-clause;
  pre-edit `16f475471a8b8295117640f7b14d949603d7bbc0` == `HEAD:`),
  `consumers.py`
  `936210e2993ddca4b77ffebf65e728f59d17079c`,
  `schema.py` `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`,
  `error_policy.py` `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91`,
  `extensions/operation_state.py`
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9`,
  `extensions/debug.py` `bf25c146111337ee0af590e7496b34c010c2f7be`,
  `utils/policies.py` `860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e`,
  package root `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  `extensions/__init__.py` `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  `tests/test_error_policy.py`
  `9ff5328eaed329a5fd69ac2e7002cf0052452241`,
  `test_error_policy_api.py`
  `9a425677bb9763cb05776e0521afa06ad4197307`,
  `tests/test_routers.py` `17842b601bca5a3ef1ff845f9a66efcceadf5aa6`
  (all clean vs `HEAD:`). Searched population: whole package (117
  `.py`); excluded on strength of body: all flavor folders,
  `views.py`, `routers.py` (masking vocabulary absent). Any fingerprint
  change reopens the finding.
- **Reconsideration trigger (recorded at the owner).** The three sites
  become one only if the engine offers a single hook that sees every
  yielded frame and every result built after teardown; until then a
  check moved to any one of them observes different state than the
  other two. Durable home: the owner module docstring paragraph (clause
  added in this change) + this finding. The plan's `## Responsibility
  index` row for `subscription-per-event-error-masking` already covers
  all three files; no new row owed.

## Defects

None new. Every claim checked while tracing held. D1 prose drift
(`consumers.py::_stop_aware_results` "two application sites" vs three
live) is already filed, confirmed by both file items, owned by the
`consumers.py` re-trace and homed via this family — referenced here,
not re-filed, and not fixed in this item (a file item's one-word repair
belongs to its card).

## Pending execution

None. The workspace proof ran green (`execution-verified`); the one
authorized shared-tree focused test ran green post-edit (1 passed);
oracle bodies above are `static-reviewed`. No `execution-deferred`
items. `FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by
construction`: every executed claim touches no database, alias, or
dialect decision (pure result rewriting + one bool `DEBUG` read; the
only DB-adjacent string is the alias parameter name threaded through
unrelated code, never resolved here).

## Judgment

Three seams correctly compose one rule: one authoritative masking
cluster, three placements each observing state the other two cannot
reach. Consolidation rejected with the contract difference (placement
vs classification) and the trigger above, recorded at the owner.
Zero behavior edits; one trigger clause at the owner; no new tests owed
(the behavior is pinned by standing oracles at both mandated tiers).

## Implementation (Worker 1)

Tracked changes (item-scoped diff vs `ITEM_BASELINE`
`848ff0f38da8d6e81193c8d80fa63d5f0e4343b0`; `HEAD` is `bfaee91d`):

- `django_strawberry_framework/extensions/error_policy.py` (+4/-1):
  one trigger clause in the module docstring (the three-sites-become-one
  paragraph). Docstring-only proved: docstring-stripped AST digest
  identical pre/post (`git show HEAD:` vs worktree), raw bytes differ.
  Pre-edit target confirmed clean (working == `HEAD:` ==
  `16f47547…`); item diff vs `ITEM_BASELINE` empty for `consumers.py`
  and `schema.py`. The plan's `## Owned changes` ledger holds no row on
  any family path (only `optimizer/walker.py`, two fakeshop live files,
  `tests/base/test_init.py`, `tests/optimizer/test_extension.py`) —
  confirmed by full read. Concurrent dirt (package hunks, test
  companions, staged entries, sibling untracked artifacts) never edited,
  reverted, or tidied. No commit.
- New untracked artifact: this file
  (`docs/dry/dry-rule-subscription-per-event-error-masking.md`).

After the edit: `uv run ruff check --fix
django_strawberry_framework/extensions/error_policy.py` then
`uv run ruff format
django_strawberry_framework/extensions/error_policy.py` until
`ruff format --check` and `ruff check` both pass on the touched path
(all green; 1 file unchanged). No `CHANGELOG.md` touch.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/subscription-per-event-error-masking`
(includes its own `.venv`, created by the authorized run; holds no
scratch files — proofs ran via `python -c`). No manifest (no
`prove_failability.py` run — no gate added, none owed).

Worker 0 rows: tick Family `subscription-per-event-error-masking`
(this artifact); no `## Responsibility index` change (owner + all three
files already covered, status stays `open`); append to
`## Owned changes`: `django_strawberry_framework/extensions/error_policy.py`
— Family `subscription-per-event-error-masking` — module-docstring
trigger clause (projection; behavior untouched).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Own trace, re-derived with fresh commands before reconciling
with `## Findings` (counts via package grep, seam bodies read,
upstream `strawberry/schema/schema.py` read, `git log -S`,
docstring-stripped AST digest, ruff run, hash re-hashes).

Sites + roles. Definition: the masking cluster in
`extensions/error_policy.py` (`mask_execution_result` owner with
`_is_unexpected`, `_masked`, `_degraded`, `degraded_result`,
`_replacement_for`, `is_maskable_result`, `masking_is_active`,
`schema_error_policy`, `DjangoErrorPolicyExtension`). Consumers:
the teardown (`_process_result`/`on_operation`, in-place adopt);
`consumers.py::_stop_aware_results` (per-event COPY, policy once
per subscription, `DEBUG` per event, shape gate); `schema.py`'s
`DjangoSchema._masked_return` (fresh post-teardown return value,
enforcement-record policy, shared floor). Oracles: the
`test_error_policy.py` / `test_error_policy_api.py` /
`test_routers.py` rows named in the artifact (existence
confirmed: return-seam rows at `test_error_policy.py` lines
1031/1051/1080, copy row at line 248, stop-aware rows at
`test_routers.py` lines 5410/5529/5580). Projections: both
module docstrings plus install/return-seam/debug paragraphs.

Counts (agree throughout). `mask_execution_result(` = 4: 1 def
(line 302) + 3 calls (lines 413, `consumers.py` 1385,
`schema.py` 1083). `degraded_result(` = 5: 1 def (line 216) +
4 calls (lines 348/424/461, `schema.py` 1089).
`StrawberryExecutionResult(data=None` = 1 (line 228).
`_is_unexpected` / `_masked` / `_degraded` / `_replacement_for`
/ `_masked_return` / `_stop_aware_results` = 1 def each.
Gates = 1 def each, composed by name at all three sites.

Owner. `extensions/error_policy.py` — concur. Dependency
direction decides: `consumers.py` must stay
channels/strawberry-free (function-local import proves it);
classification cannot live in `schema.py` without reversing
that edge; the root record cannot own engine behavior.
Schema owns placement, never classification.

Rejection challenge (principle 8, every merge direction).
Per-event into teardown: REJECT — teardown observes the
completed result at end; in-flight frames are already yielded
and rendered, so the moved check sees post-hoc state while
the leak is on the wire. Teardown into per-event: REJECT —
`_stop_aware_results` wraps only `subscribe`/`stream` sources;
a query/mutation answered via `execute` never passes through
it. Return into teardown: REJECT — verified in the installed
upstream `execute_sync`/`execute` bodies: the outer `except`
builds a FRESH `ExecutionResult` after the
`extensions_runner.operation()` context (and every teardown)
has unwound, over a context whose `result` was still `None`;
teardown observes absence, not the coerced result. Teardown
into return: REJECT — streamed frames never pass through
`execute`/`execute_sync`, so return-only misses every one.
Mask-twice: structural (masked errors carry
`original_error=None`, read as deliberate; `is`-identity
pass-through), executed by W1. Outcome REJECT: concur —
moving any seam observes different state.

Owner-clause edit. Prose: the added clause states the
contract trigger only (sites become one iff the engine
offers a single hook seeing every frame plus every
post-teardown result); no process provenance, no line
numbers. Compliant. AST-identity: verified myself —
docstring-stripped AST sha256 identical pre/post
(`1ac53d33...`), raw bytes differ; `git diff` shows +4/-1
prose only. Ruff: `ruff format --check` + `ruff check` on
the touched path both pass (ran myself). No revision.

C-B "0 moved". Concur on the count, with a precedent gloss.
History shows the return seam landed in `ffce6f29`, which DID
touch the owner: it ADDED `degraded_result` (+ export) and
recomposed one inline floor line into a call of it. So "0
existing moved" holds in the narrow DRY sense — no existing
definition's contract moved; the commit extracted the shared
floor instead of duplicating it — but the shorthand
elides the +1 owner addition. The forward challenge still
counts 0 (the floor now exists; a new site composes the four
helpers + floor by name, verified: `schema.py` imports all
by name, restates nothing). Not revision-worthy; nuance
recorded here.

Gate judgment. Concur: no gate owed. A hand-copy second
`mask_execution_result` def with an identical body, called
from one seam, passes every behavior oracle — wire
text/message rows, correlation-id shape, the copy-contract
pair (a copy still leaves engine originals), the return
identity row (identical body still answers `is`), hook,
per-event and incremental rows. No standing oracle asserts
cross-module function identity or a def census; only a
bespoke source census could pin unity, which the method
forbids for gate-only findings. For a rejection the trigger
at the owner is the durable instrument, and it is in place.

D1. Correctly not re-filed and still homed.
`consumers.py` line 1321 still reads "two application
sites" with three live; this item left it untouched, as
scoped (a file item's one-word repair belongs to its card).
Homing stands via the plan's Run 2026-09-19-1 note
(`consumers.py` re-trace / this family).

Freshness re-hashed (myself, just now; all match the
artifact, no staleness): `error_policy.py` worktree
`bd763bcc` (post-clause; `HEAD:` `16f47547` = pre-edit),
`consumers.py` `936210e2`, `schema.py` `c2e1b748`,
`error_policy.py` (root) `fa94fcd9`,
`operation_state.py` `b2674a22`, `debug.py` `bf25c146`,
`utils/policies.py` `860b181f`, package root `0ef72601`,
`extensions/__init__.py` `dc3ebdc2`,
`test_error_policy.py` `9ff5328e`,
`test_error_policy_api.py` `9a425677`,
`test_routers.py` `17842b60`.

`## Pending execution` empty: judged correct. Masking is
wire-observable; the final gate executes the standing
oracles — `tests/test_error_policy.py`,
`examples/fakeshop/test_query/test_error_policy_api.py`,
`tests/test_routers.py` stop-aware/incremental rows —
inside full `uv run pytest`. Sharded/Postgres cells
inapplicable by construction (pure result rewriting plus
one `DEBUG` bool read; no database, alias, or dialect
decision on the path): concur.

Focused shared-tree test: authorized. The entry command
authorizes one focused `--no-cov` test; the run was `uv run
pytest
tests/test_error_policy.py::test_the_return_seam_passes_an_already_masked_result_through_by_identity
--no-cov -n0 -q` → 1 passed, `--no-cov` present, test
confirmed present at `tests/test_error_policy.py:1031`.
Concur.

Item-scoped diff: `extensions/error_policy.py` +4/-1 only;
`consumers.py` / `schema.py` empty (confirmed). The one
other hunk in range (`docs/bug_hunt/bug_hunt-0_0_15.md`)
is another cycle's concurrent artifact, untouched here.
Concurrent package/test dirt left alone; no commit.

Per-claim ledger: counts AGREE; three consumers AGREE;
C-A → 1 AGREE; C-B → 0 AGREE with precedent gloss above;
C-C → 0 AGREE; owner AGREE; lifetime AGREE; REJECT AGREE;
trigger AGREE; no defects AGREE; no pending execution
AGREE; no gate AGREE; focused test AGREE.

Defects (Worker 2): none new.

Verdict: `Status: verified`, no pending execution.
