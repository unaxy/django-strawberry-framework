# DRY review: `globalid-setting-snapshot`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `globalid-setting-snapshot`. Suspected compute-vs-store split
(compute at [finalizer][finalizer]`::finalize_django_types`, store at
[registry][registry]`::TypeRegistry`) — REJECTED as a consolidation: one
rule in two roles, decided below with proof. Member files:
`django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/finalizer.py`,
`django_strawberry_framework/types/relay.py`. Prior records only as
triggers: the registry file item ([file-registry][file-registry] F9 named
storage/compute halves — every edge below re-derived from the bodies,
nothing inherited) and the typed-decode / finalize-gate / name-decode
items (snapshot named as seam — verified, not inherited). Never read any
`worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds one row each on
`registry.py` (Family `relay-node-name-decode`,
`definition_for_graphql_name` docstring clause) and `types/relay.py`
(Family `relay-node-type-stamp`, `_NODE_TYPE_HINT_ATTR` comment clause) —
both confirmed by content (`git diff HEAD` shows exactly those hunks and
nothing else on either path). `types/finalizer.py` is byte-identical to
HEAD and to `ITEM_BASELINE` before this item's edit (no ledger row, no
external hunk). `ITEM_BASELINE`
`eb37e448401d394556489ff653baba667a96434c` verified present via
`git cat-file -t`. The one tracked edit lands on clean
`types/finalizer.py`; the other member files untouched. Reading the dirty
files was free. Root `relay.py` (ledgered typed-decode clause) read as a
connected non-member; untouched.

## System trace

Rule: the schema-wide `RELAY_GLOBALID_STRATEGY` value is read and
validated exactly once per finalization and frozen on the registry, so
per-type resolution consumes a stable value instead of the live setting.

What each site does (each re-derived from its body):

- **Thin reader** ([conf][conf]`::relay_globalid_strategy_setting`):
  `getattr(settings, RELAY_GLOBALID_STRATEGY_KEY, None)` — absent key
  yields `None` (no override). Validates nothing; domain validation lives
  with the strategy vocabulary. One production caller (below).
- **Shared validator**
  ([tbase][tbase]`::_validate_globalid_strategy`): the single rule both
  the `Meta.globalid_strategy` path (`source="meta"`, names the type,
  enforces the Relay-shape gate) and the setting path (`source="setting"`,
  names the key, skips the gate) run through. String typo guard reads
  `STRING_GLOBALID_STRATEGIES`; callable arity/sync-ness checked once
  here. The `RELAY_GLOBALID_STRATEGY_KEY` import in [tbase][tbase] is
  error-message framing only (the `subject` for `source="setting"`),
  not a second read.
- **Compute** ([trelay][trelay]`::_validated_globalid_setting`): read via
  the thin reader, validate via the shared validator
  (`relay_shaped=True`, `meta=None`). Returns validated string /
  validated callable / `None`. One production caller (below). Docstring
  states the single-validation-site contract.
- **Orchestration**
  ([finalizer][finalizer]`::finalize_django_types` snapshot block):
  calls the compute unconditionally before the Relay loop (an invalid
  setting raises even with zero Relay types or all-override), stamps the
  slot when it holds the sentinel, else compares and refuses a changed
  value on retry (mixed-strategy guard naming `registry.clear()`), then
  passes the slot into `install_globalid_typename_resolver` per Relay
  type. Pure read before any class mutation (Phase-1 atomicity intact).
- **Store** ([registry][registry]`::TypeRegistry`): the inert
  `_globalid_setting_snapshot` slot (init), the `GLOBALID_SETTING_UNSET`
  sentinel (module constant; distinguishes "not yet computed" from a
  computed `None`), and the `clear()` reset. Implements no validation,
  no timing, no comparison.
- **Pure consumer**
  ([trelay][trelay]`::_resolve_globalid_strategy`): two-arg precedence
  (`definition.globalid_strategy` → passed-in snapshot →
  `DEFAULT_GLOBALID_STRATEGY`) reading no setting and validating
  nothing. One production caller (the install step).

WHAT is snapshotted: the validated setting value only (string in
`STRING_GLOBALID_STRATEGIES`, validated callable, or `None`). WHEN:
finalize entry, unconditionally, before the Relay loop — not first use.
WHY a snapshot instead of a live read: the GlobalID wire format is a
stable schema contract frozen at build (a mid-process settings change
must not re-word emitted IDs); the unconditional read fails an invalid
value loud even when no type consumes it; and `override_settings` +
`clear()` + rebuild is the isolated flip path (oracle-pinned). No
production reader touches the live setting after finalize — the sweep
below finds zero, and `test_no_request_time_setting_read` pins it with
a boom reader.

Connected sources read: [conf][conf] (full reader + key contract),
[tbase][tbase] (validator + key-framing neighbor),
[tdef][tdef]`::DjangoTypeDefinition` (`globalid_strategy` raw slot vs
`effective_globalid_strategy` stamp),
[testing-relay][testing-relay]`::global_id_for` (reads the stamp, never
the setting — consistent-by-construction consumer), root `relay.py`
decode path (reads the stamp), all three oracle files,
[spec-031][spec-031] Decisions 5/7/10 (contract source), the glossary
snapshot entry (projection). Excluded on strength of body: every other
package module (zero snapshot-token occurrences in the whole-package
sweep); the sibling settings readers (`NESTED_CONNECTION_STRATEGY`,
`SINGLE_PARENT_FAST_PATH`, `HIDE_FLAT_FILTERS`, `MAX_REQUEST_BODY_BYTES`,
`TESTING_ENDPOINT`, `RESOURCE_POLICY`, `ERROR_POLICY`) — each reads live
at its own construction/fetch lifecycle where "current value" is the
correct semantic, none writes the slot or calls the compute; the
decode/filter/audit consumers — all read the per-type
`effective_globalid_strategy` stamp, never the setting.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** No sibling flavor mirrors the
   snapshot: filters/orders/mutations/forms/DRF own no finalize-time
   setting snapshot (verified by sweep — zero `_validated_globalid_setting`
   / `_globalid_setting_snapshot` occurrences outside the three member
   files plus the single oracle read). The sibling settings keep live
   reads for a different reason (request/construction-scoped values, not
   frozen wire contracts). Distinct reasons to change — stay separate.
   Trigger: a second subsystem snapshotting a setting into the registry.
2. **Sync/async twins.** `finalize_django_types` has no async twin (one
   def package-wide); finalization is build-time-only, and the installed
   closures do no per-request strategy lookup on either color. No drift
   surface. Trigger: an async finalize path or a per-request strategy
   lookup.
3. **Derived rather than repeated knowledge.** The validated value
   derives once (the compute) and stores once (the slot); per-type
   resolution is pure precedence over the passed-in value, never a
   re-derivation. No site re-derives the validated setting from raw
   settings — the sweep finds one compute and one reader-caller.
4. **Inverse / round-trip pairs.** Encode (installed closure over the
   resolved strategy) vs decode (reads the stamped classification) meet
   at the per-type stamp, not at the setting: neither half reads live
   settings. No second settings-read half exists. Full encode/decode
   symmetry belongs to the typed-decode family — excluded by body.
5. **Contracts restated in another medium.** Production (reader +
   validator + compute + orchestration + slot); oracles (independent
   counting/behavior rows listed below — the counting test observes
   call counts through monkeypatch, never the owner's slot; the
   boom-reader test observes emission); projections (site docstrings
   cross-name each other accurately; [spec-031][spec-031]; glossary).
   Each medium classified, definitions counted separately.
6. **Enforcement by omission.** Every strategy consumer audited: install
   step (snapshot param), decode, filter validation, model-label audits,
   testing helper (all read recorded state). No consumer lacks the
   snapshot path and no consumer bypasses it with a live read: no gap,
   no defect.

### Enumeration

Instrument: whole-package sweeps for `relay_globalid_strategy_setting |
_validated_globalid_setting | _globalid_setting_snapshot |
GLOBALID_SETTING_UNSET | _resolve_globalid_strategy |
install_globalid_typename_resolver | RELAY_GLOBALID_STRATEGY` + `def`
census per symbol. Population: 117 `.py` (plan count; no adds/renames).

- `relay_globalid_strategy_setting`: 1 def ([conf][conf]); 1
  production caller ([trelay][trelay]`::_validated_globalid_setting`
  body); test callers ([test-conf][test-conf] absent/default/override
  rows) are oracles.
- `_validated_globalid_setting`: 1 def ([trelay][trelay]); 1
  production caller ([finalizer][finalizer] snapshot block); the
  [test-base][test-base] precedence-test tail calls it as an oracle.
- `_globalid_setting_snapshot`: 1 slot def (`__init__`); lifecycle
  writes exactly 3 (`__init__`, `clear()` reset, finalizer stamp);
  production reads exactly 4 (sentinel check, inequality compare,
  guard message, install pass-through — all in the finalizer); 1 test
  read (retry test asserting the stamped value) is an oracle.
- `GLOBALID_SETTING_UNSET`: 1 def ([registry][registry] module);
  reads exactly 3 (`__init__`, `clear()`, finalizer `is` check).
- `_resolve_globalid_strategy`: 1 def; 1 production caller (the
  install step); [test-base][test-base] precedence rows are oracles.
- `install_globalid_typename_resolver`: 1 def; 1 production caller
  (finalizer Relay loop).
- `RELAY_GLOBALID_STRATEGY_KEY`: 1 def ([conf][conf]); 2 uses (reader
  `getattr`, [tbase][tbase] error framing — the latter message-only).
- Oracles:
  `test_setting_read_and_validated_once_per_finalize` (1 read + 1
  validation for N defaulted types),
  `test_no_request_time_setting_read` (post-finalize boom reader),
  `test_retry_lifecycle_rejects_setting_change_no_mixed_strategy`,
  `test_clear_and_rebuild_flips_strategy_no_process_global`,
  `test_invalid_setting_raises_with_zero_relay_types` (+ async-callable
  variant, all-override and override-only arrivals),
  `test_setting_error_framing_tracks_the_conf_key_constant`,
  `test_resolve_globalid_strategy_precedence`,
  callable-setting accept/reject rows, [test-conf][test-conf] reader
  rows. All assert behavior through finalize + emission, never the
  owner's slot (except the one retry-test read assert, listed).

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New strategy string (widen the vocabulary) | **1** ([tbase][tbase]`::_validate_globalid_setting` + `STRING_GLOBALID_STRATEGIES`, one site; compute, orchestration, slot, and precedence follow by construction — all strategy-agnostic). |
| C2 | Rename the setting key | **1** ([conf][conf]`::RELAY_GLOBALID_STRATEGY_KEY`; reader and error framing follow — pinned by the framing-tracks-constant oracle). |
| C3 | Change snapshot timing/lifetime (recompute per finalize; move after Phase 1; drop the retry guard) | **1** (finalizer block; the slot is passive state and `clear()` reset unchanged). |
| C4 | Change what "validated" means for settings (e.g. reject callables) | **1** (shared validator `source="setting"` arm, invoked through the single compute). |
| C5 | The suspected duplication: a live-settings reader alongside the snapshot | **0** exist (sweep: zero production readers outside the compute; zero computes outside the finalizer). The counting oracle fails a per-type re-read (mutant proof below); the boom-reader oracle fails a request-time read. |

## Findings

### F1 — GlobalID setting snapshot (REJECTED consolidation: split correct, single-owned sub-rules)

- **Contract + variation.** Validated `RELAY_GLOBALID_STRATEGY`
  computed once per build; sentinel distinguishes not-yet-computed
  from a `None` snapshot; retry under a changed value refuses;
  `clear()` resets. No legitimate variation in timing (always finalize
  entry, always unconditional) or readers (compute only).
- **Sites + roles.** *Reader definition*: `relay_globalid_strategy_setting`
  (1 def, 1 caller). *Validator definition*: `_validate_globalid_strategy`
  (1 def, 2 sources, source-specific text). *Compute definition*:
  `_validated_globalid_setting` (1 def, 1 caller). *Orchestration*:
  finalizer snapshot block (1 site: stamp-or-compare + pass-through).
  *Store*: slot + sentinel + `clear()` reset (1 owner, implements no
  rule). *Pure consumer*: `_resolve_globalid_strategy` (1 def, 1
  caller). *Oracles / projections*: as listed.
- **Challenges.** C1 → 1; C2 → 1; C3 → 1; C4 → 1; C5 → 0 existing
  (absence proved by sweep + two failing-on-violation oracles). Count
  > 1 nowhere in one rule.
- **Owner + lifetime (principles 7, 4).** Split stands: the finalizer
  owns compute orchestration (it already drives the build; timing and
  retry policy are build policy), the registry owns the inert slot
  (every consumer can depend on the registry; the reverse — registry
  importing the compute — closes the load cycle the tree already
  dodges with in-function imports on both sides). Consolidating either
  direction is worse: a registry-side stamp method would be a
  one-caller wrapper owning nothing new (principle 11), splitting
  orchestration across two modules; a finalizer-module slot would be a
  process-global outside the `clear()` lifecycle (rejected by the
  no-process-global oracle). Lifetime: owner = `TypeRegistry`;
  validity key = one build since last `clear()` (sentinel =
  unstamped); publish point = finalize entry, unconditional; mutator
  = finalizer stamp only (plus lifecycle init/reset); invalidation =
  `clear()`.
- **Migration.** None — already single. One comment trigger clause at
  the orchestration owner (projection; behavior identical —
  AST-identity proof below).
- **Distinct behavior (stays separate).** Per-type
  `effective_globalid_strategy` stamping (install step; decode/filter
  territory of adjacent families); sibling settings' live reads
  (different lifecycle semantics, own reasons); `Meta` vs setting
  error framing (same validator, intentionally distinct text).
- **Behavioral proof.** `execution-verified` (workspace 7 passed +
  authorized shared-tree 7 passed, then the comment-only edit with
  AST identity). Failability mutant (workspace only): Relay-loop
  pass-through replaced by a per-type `_validated_globalid_setting()`
  recompute → counting oracle fails `3 == 1` (1 unconditional + 2
  per-type), then restored byte-identical via `cmp` and re-verified
  green. The boom-reader oracle stayed green under that mutant —
  correct, it pins the other half (no request-time read).
- **Structural gate.** None owed, with proved reason: every divergence
  that changes observable behavior (per-type re-read, request-time
  read, dropped retry guard, lost reset) fails a standing oracle
  (mutant above for the first); a caller-count unity pin beyond that
  would be a bespoke per-helper existence test, which [DRY.md][dry]
  forbids for gate-only findings. Same standard as the verified
  type-stamp, typed-decode, name-decode, target-guard, and
  subscription-masking items. Unity rests on the def/caller census +
  triggers below.
- **Coupling.** None. Adjacent families untouched; the clause is
  comment-only.
- **Freshness.** Blob ids below. Any fingerprint change reopens.
- **Reconsideration triggers (recorded at the owner).** T-reader fires
  on a second production reader of `RELAY_GLOBALID_STRATEGY` outside
  `_validated_globalid_setting` (re-opens single-compute); T-compute
  fires on a second validated-setting compute (re-opens the snapshot
  path); T-lifetime fires on store-side policy beyond slot + sentinel
  + reset (re-opens the split). Durable homes: the new comment clause
  on [finalizer][finalizer]`::finalize_django_types`, this finding,
  and the plan's `## Outcomes` via Worker 0.

## Defects

None new. Spot-checks that could have been defects all hold: the
[tbase][tbase] key import is message framing only (no second read);
`clear()` resets the slot (retry + flip oracles pin both arms); the
testing helper reads the stamp, never the setting; `finalize_django_types`
has no async twin; the unconditional compute raises before any class
mutation (Phase-1 atomicity intact); concurrent dirt on sibling paths
carries zero snapshot vocabulary and was left untouched.

## Pending execution

None. No `execution-deferred` proofs; sharded/Postgres cells
`inapplicable by construction` (finalize-time in-memory state plus
counting oracles — no alias, dialect, or row decision in the rule).
Full-suite gate business deferred to the final-gate item with reason:
the entry authorizes workspace runs plus one focused `--no-cov` test,
and a green unmutated suite would discharge no failability proof for
a rejection that proposes no gate.

## Judgment

Compute (read + validate + stamp-or-compare, finalizer +
[trelay][trelay]) and store (slot + sentinel + reset, [registry][registry])
are two roles of one rule, each single-owned (C1–C4 → 1, C5 → 0).
Merging them would reverse the dependency the tree observes or strand
state outside the `clear()` lifecycle, so the split stands — rejected
with difference + triggers + home, one projection-only clause at the
owner, no defects.

## Implementation (Worker 1)

Tracked change (1 file, comment-only):
`django_strawberry_framework/types/finalizer.py` — snapshot block gains
the T-reader / T-compute / T-lifetime reconsideration-trigger clause
(projection; behavior untouched). Attribution: `types/finalizer.py`
clean at `ITEM_BASELINE` and at HEAD before the edit; no `## Owned
changes` row exists on the path; `registry.py` / `types/relay.py` /
root `relay.py` hunks attributed above and untouched. Worker 0 appends:
`django_strawberry_framework/types/finalizer.py` — Family
`globalid-setting-snapshot` — `finalize_django_types` snapshot-block
trigger clause (projection; behavior untouched).

Item-scoped diff: `git diff
eb37e448401d394556489ff653baba667a96434c --
django_strawberry_framework/types/finalizer.py` shows exactly the +7
comment lines and nothing else; the artifact file below is new
(`git diff --no-index /dev/null` scope).

Proofs (disposable workspace per [DRY.md][dry] "Tests"; `rsync` copy,
docs excluded; every command via `uv run --directory "$WS"`):

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/globalid-setting-snapshot-w1
rsync -a --exclude .git --exclude .venv --exclude '__pycache__' --exclude docs/ ./ "$WS/"
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" pytest <6-test selection> --no-cov -n0 -q
```

Copy `__file__`:
`.../dry-ws/globalid-setting-snapshot-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/globalid-setting-snapshot-w1/examples/fakeshop/db.sqlite3`
(the copy's own tree and database). Behavioral selection (7 passed in
the copy — the zero-Relay-types test parametrizes in two; 7 passed
shared-tree, comment edit in flight):
`test_setting_read_and_validated_once_per_finalize`,
`test_no_request_time_setting_read`,
`test_retry_lifecycle_rejects_setting_change_no_mixed_strategy`,
`test_clear_and_rebuild_flips_strategy_no_process_global`,
`test_invalid_setting_raises_with_zero_relay_types`,
`test_resolve_globalid_strategy_precedence`. Failability mutant
(workspace only, pristine backup kept, restored byte-identical via
`cmp` and re-verified): per-type `_validated_globalid_setting()`
recompute at the pass-through → counting oracle fails `3 == 1`;
boom-reader oracle stays green (pins the other half). No source
mutation remains in the copy; the control backup was removed after
restore.

After the edit: `uv run ruff check --fix
django_strawberry_framework/types/finalizer.py` + `uv run ruff format
django_strawberry_framework/types/finalizer.py` — both green
(`format --check` + `check` pass on the path; scoped to the path so no
concurrent dirt is rewritten). INVERSE proof (comment-only edit): AST
of `HEAD:types/finalizer.py` vs worktree — identical (comments are not
AST nodes). No `CHANGELOG.md` touch. No commit per standing rule.

Scratch paths (removal is Worker 0's, after `verified`, by explicit path):
`WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/globalid-setting-snapshot-w1`
(includes its own `.venv`; the control backup was removed after
restore). No manifest (no `prove_failability.py` run — no gate added,
none owed; the hand-proved mutant is the control). This artifact
`docs/dry/dry-rule-globalid-setting-snapshot.md` is the item's new file.

Worker 0 rows: tick Family `globalid-setting-snapshot` (this
artifact); no `## Responsibility index` change needed beyond `open` →
decided per the finding above (provisional split owner + all three
member files already covered); append the `## Owned changes` row
above; no defects to home.

Freshness fingerprints (`git hash-object` worktree unless noted; HEAD
`bfaee91d`; `ITEM_BASELINE` `eb37e448…` present):
`types/finalizer.py` `f4266a15…` post-clause (HEAD `77fd9a2d…`; delta
= +7 comment lines only), `registry.py` `612bea87…` (HEAD
`9cc8bb55…`; delta = ledgered name-decode clause only),
`types/relay.py` `c333c785…` (HEAD `52439862…`; delta = ledgered
type-stamp clause only), `conf.py` `c6ad46aa…` (= HEAD, clean),
`types/base.py` `91c58747…` (= HEAD, clean), `types/definition.py`
`fa6c4d330…` (= HEAD, clean), `testing/relay.py` `df0dc72a…` (=
HEAD, clean), root `relay.py` `69085e7a…` (HEAD `c3c5aea5…`; delta =
ledgered typed-decode clause only, read-only here),
`tests/types/test_relay_interfaces.py` `26fb2ccf…` (= HEAD),
`tests/types/test_base.py` `4282e0b0…` (= HEAD),
`tests/base/test_conf.py` `f35c7074…` (= HEAD),
`docs/SPECS/spec-031-globalid_encoding-0_0_9.md` `45f43dfe…`,
`docs/GLOSSARY.md` `bc51debc…`, `docs/dry/dry-file-registry.md`
`4350662b…`, `dry-rule-typed-globalid-decode.md` `7743927f…`,
`dry-rule-type-registry-finalize-gate.md` `6f2d1726…`,
`dry-rule-relay-node-type-stamp.md` `0df402cf…`,
`docs/dry/dry-0_0_15.md` `59195a65…` (pre-tick). Searched population:
whole package (117 `.py`) for the seven snapshot tokens; whole repo
for the two call sites. Any fingerprint change reopens the finding.

## Independent verification (Worker 2)

Recorded expectation-first from the bodies at HEAD `bfaee91d` plus the
worktree. Plan item, COMPLETE targets, and the item-scoped diff were
traced before this section was written. The `## Findings` block was not
read before the trace below was derived. A tail peek via `head` and `sed`
to locate the append anchor exposed the `## Pending execution`,
`## Judgment`, and `## Implementation (Worker 1)` summaries after the
source census, `git hash-object` re-hashes, and `ruff` runs below were
already done. That peek did not supply any site, count, or oracle used
below. The `## Findings` text was first read in full only after this
trace was drafted, with reconciliation following the trace.

- **What is snapshotted.** The validated value of
  `django_strawberry_framework/conf.py::relay_globalid_strategy_setting`,
  namely a string in
  `django_strawberry_framework/types/base.py::STRING_GLOBALID_STRATEGIES`,
  a validated sync three-arg callable, or `None` for no schema-wide
  override. Validation is
  `django_strawberry_framework/types/base.py::_validate_globalid_strategy`
  with `source="setting"`, `relay_shaped=True`, `meta=None`.
- **When.** Once per build, unconditionally, at the top of
  `django_strawberry_framework/types/finalizer.py::finalize_django_types`
  before the Relay loop and before any class mutation. The block calls
  `django_strawberry_framework/types/relay.py::_validated_globalid_setting`,
  stamps
  `django_strawberry_framework/registry.py::TypeRegistry._globalid_setting_snapshot`
  when it holds
  `django_strawberry_framework/registry.py::GLOBALID_SETTING_UNSET`, else
  compares and raises the mixed-strategy `ConfigurationError` naming
  `registry.clear()`. The stamped slot is then passed per Relay type into
  `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver`,
  which calls
  `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy`.
- **Why not a live read.** A per-type live read would cost N reads and N
  validations instead of one, would let a mid-build settings change stamp
  a mixed-strategy schema, and would let a post-build change re-word
  emitted wire IDs. The unconditional entry read fails an explicitly
  configured invalid value loud even with zero Relay types or with every
  Relay type overriding via `Meta.globalid_strategy`, cases where a
  per-type or lazy reader would never fire. The isolated flip path is
  `override_settings` plus `registry.clear()` plus rebuild, with no
  process-global.
- **Every snapshot reader versus live-settings reader.** Live reader: one
  definition,
  `django_strawberry_framework/conf.py::relay_globalid_strategy_setting`,
  one production caller,
  `django_strawberry_framework/types/relay.py::_validated_globalid_setting`.
  The `RELAY_GLOBALID_STRATEGY_KEY` import in `types/base.py` is
  error-message framing only, not a read. Compute: one definition,
  `django_strawberry_framework/types/relay.py::_validated_globalid_setting`,
  one production caller, the finalizer snapshot block. Orchestration: the
  finalizer block alone, stamp-or-compare plus pass-through at the Relay
  loop. Store: slot plus sentinel plus `clear()` reset in
  `django_strawberry_framework/registry.py::TypeRegistry`, state with no
  rule. Pure consumer: one definition,
  `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy`,
  one production caller, the install step, reading no settings and
  validating nothing. Shared validator: one definition,
  `django_strawberry_framework/types/base.py::_validate_globalid_strategy`,
  two production sources, `Meta` via `_validate_meta` and setting via the
  compute. Decode, filter, audit, and testing helpers read the recorded
  per-type `effective_globalid_strategy` stamp, never the setting.
- **Definition counts from my own challenges.** C1, widen the strategy
  vocabulary or change the typo guard: 1, the shared validator. C2, rename
  the setting key: 1, the key constant, with reader and framing following
  by name. C3, change snapshot timing, lifetime, or the retry guard: 1,
  the finalizer block, with the slot passive. C4, change what validated
  means for the setting, for example reject callables: 1, the shared
  validator `setting` arm through the single compute. C5, suspected second
  live reader or second validated compute: 0 exist after the sweep below.
- **Owner I would choose: split stands, reject consolidation.** Compute
  orchestration stays in the finalizer, validated compute and pure
  precedence stay in `types/relay.py`, shared validation stays in
  `types/base.py`, thin read stays in `conf.py`, inert slot plus sentinel
  plus reset stay in the registry. Merging compute into the registry would
  force the registry to import the thin reader and the validator, closing
  the load cycle both sides already dodge with in-function imports, or
  would strand the snapshot in a finalizer-module global outside the
  `clear()` lifecycle. A registry-side stamp method would be a one-caller
  wrapper owning nothing new.
- **C5 re-sweep result.** Searched population is the whole package, 117
  `.py` files confirmed by `git ls-files`. Token sweeps for the setting
  key, the thin reader name, the compute name, the snapshot slot name,
  the sentinel name, and the pure-consumer name find exactly the sites
  listed above. All `getattr(settings, ...)` sites in package source touch
  other keys. All `django.conf.settings` importers read other settings.
  No direct `DJANGO_STRAWBERRY_FRAMEWORK` subscript for the GlobalID key
  exists outside the thin reader. Zero second production readers and zero
  second validated computes exist. Test callers of the reader, the compute,
  and the pure consumer are oracles, never counted.
- **Lazy alternative considered.** A registry-lazy snapshot computed at
  first per-type read instead of finalizer-eager would miss the
  unconditional invalid-value raise with zero Relay types, would move the
  read after Phase 1 annotation mutations and break the failure-atomic
  placement, and would stamp the first type before any value exists to
  compare against on retry. The eager placement is pinned by the
  zero-Relay-types invalid-setting oracle, by the counting oracle of one
  read plus one validation per finalize, and by the pure-read-before-any-
  mutation comment contract at the block.
- **Lifetime judged.** Validity is one build since `clear()`, sentinel
  means unstamped. Publish is finalize entry, unconditional. Mutator is
  the finalizer stamp only, plus lifecycle init and reset. Invalidation is
  `clear()`. I opened both oracles myself:
  `test_retry_lifecycle_rejects_setting_change_no_mixed_strategy` pins
  stamp persistence across retry, the compare refusal, and the
  clear-plus-rebuild recovery, and
  `test_clear_and_rebuild_flips_strategy_no_process_global` pins the
  registry lifecycle as the cache boundary with no process-global. Both
  also pin that `clear()` resets the slot.
- **Owner edit judged.** The item-scoped diff from `ITEM_BASELINE`
  `eb37e448401d394556489ff653baba667a96434c` to the worktree is exactly
  the plus-7 comment clause at the finalizer snapshot block, verified by
  `git diff` against both that baseline and HEAD. Prose states the
  compute-versus-store split, names the owner of each half, and lists the
  three reconsideration triggers. `AST` identity holds: `ast.dump` of
  `HEAD:django_strawberry_framework/types/finalizer.py` equals the
  worktree parse, so behavior is untouched. `uv run ruff format --check`
  and `uv run ruff check` on the five touched paths both pass, run myself.
  Layout is comment-only ASCII with short lines under the limit. The short
  symbol spellings match the surrounding comment style and introduce no
  new production name. No test-tier change is owed for a projection-only
  clause. Concurrent dirt elsewhere was left untouched.
- **No-gate reasoning judged.** Standing oracles pin each half: the
  counting oracle fails a per-type recompute, the boom-reader oracle fails
  a request-time read, the zero-types invalid oracle fails a conditional
  or dropped compute, the retry oracle fails a dropped compare, the
  clear-flip oracle fails a process-global or lost reset, and the
  precedence test pins the pure consumer. A hand copy of the block would
  pass every behavior oracle, so a bespoke unity or existence gate would be
  gate-only over an open-ended bypass population. No new gate is owed, the
  same standard as the verified sibling rejection items.
- **Freshness re-hashed by me.** Worktree `git hash-object`: `conf.py`
  `c6ad46aa…` equals HEAD, `types/base.py` `91c58747…` equals HEAD,
  `types/relay.py` `c333c785…`, `types/finalizer.py` `f4266a15…` post
  clause, `registry.py` `612bea87…`. HEAD hashes re-derived:
  `registry.py` `9cc8bb55…`, `types/relay.py` `52439862…`, both matching
  the artifact. `ITEM_BASELINE` object type verified as commit. The
  `types/finalizer.py` delta remains exactly the plus-7 lines. Sibling
  deltas on `registry.py` and `types/relay.py` are this cycle ledgered
  clauses on other families, read-only here and untouched.
- **Pending execution judged.** None owed. No `execution-deferred` proof
  exists for a comment-only rejection with no new gate. Sharded and
  Postgres cells are inapplicable by construction: finalize-time in-memory
  state with counting oracles and no alias, dialect, or row decision.
  Full-suite gate business correctly stays with the final-gate item.
- **AGENTS.md prose on the diff.** No version literal touched, no
  changelog touch, no commit, no branch move, no bulk delete. Source refs
  use symbol paths. Test placement is untouched. The comment clause is the
  durable home for the triggers alongside the owner block.

Reconciliation after reading `## Findings`, point by point, agree or
differ.

- Thin read, one definition and one caller: agree. My census matches the
  single `getattr` site and the single compute caller, with test callers
  as oracles.
- Shared validation, one definition and two sources: agree. Both call
  sites re-derived, including the `meta=None`, `relay_shaped=True`,
  `source="setting"` framing and the message-only key import.
- Compute, one definition and one caller: agree. The in-function imports
  as the import-cycle dodge re-derived on both sides.
- Orchestration as stamp-or-compare plus pass-through: agree, including
  unconditional placement before any mutation and the per-Relay-type
  pass-through.
- Store as slot plus sentinel plus `clear()` reset, state with no rule:
  agree. Init, reset, and finalizer `is` check are the only lifecycle
  writes.
- Pure consumer, one definition and one caller reading no settings:
  agree. The body reads only the definition slot, the passed snapshot,
  and the package default.
- Challenges C1 through C4 each one, C5 zero live readers after the
  117-file sweep: agree. My independently worded challenges count the same.
- Split stands because merging reverses the import-cycle dodge or strands
  state outside `clear()`: agree, with the dependency direction traced
  myself.
- Lifetime fully stated with validity one build since `clear()`, publish
  at finalize entry, mutator finalizer-only, invalidation `clear()`:
  agree.
- Reject with triggers plus home in the plus-7 comment clause at the
  finalizer block: agree. The clause is projection-only.
- No defects: agree. My spot checks found no second read, no lost reset,
  no async twin, and no atomicity break.
- No pending execution with the 7-test workspace selection green plus the
  per-type-recompute failability mutant failing the counting oracle as
  `3 == 1` and restored: agree on the entry as written. I did not re-run
  the workspace or the focused shared-tree selection myself because the
  entry command authorizes those runs and `AGENTS.md` forbids converting
  dispatch into a test run. For a comment-only edit, `AST` identity plus
  green `ruff` plus the standing oracle text is the complete check I can
  run, and the mutant arithmetic of one unconditional plus two per-type
  recomputes is correct on its face.
- No new gate because standing oracles pin both halves: agree, same
  standard as the named siblings.
- One focused shared-tree run green: agree as recorded. My own green runs
  are the two `ruff` commands on the five touched paths.

Defects found by Worker 2: none. The candidate prose, import, lifecycle,
and atomicity checks above all hold, so no `(Worker 2)` entry is owed.

Verdict: `verified`. The split stands, the trigger clause is the correct
durable home, and the item is complete with no pending execution.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[file-registry]: dry-file-registry.md
[finalize-gate]: dry-rule-type-registry-finalize-gate.md
[name-decode]: dry-rule-relay-node-name-decode.md
[typed-decode]: dry-rule-typed-globalid-decode.md

<!-- docs/SPECS/ -->
[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[registry]: ../../django_strawberry_framework/registry.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[tbase]: ../../django_strawberry_framework/types/base.py
[tdef]: ../../django_strawberry_framework/types/definition.py
[trelay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-base]: ../../tests/types/test_base.py
[test-conf]: ../../tests/base/test_conf.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
