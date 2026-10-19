# DRY review: `utils/write_transaction.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits.

## System trace

Target `django_strawberry_framework/utils/write_transaction.py` owns the
mutation write discipline every write flavor shares: the managed
completion-spanning transaction alias, the one-router-alias pin, the
phase-separated alias guard, the read-only authorization barrier, the
pk-canonical equality trio, the locate-time snapshot / pre-save drift
check, the base-manager row lock, and the disappearing-row conflict
envelope. Its module docstring states the shape once (five bullets plus
the SECURITY MODEL: containment is transactional, never lexical).

Target identity and attribution. HEAD blob
`eca9ad4d3f765964df05884e080eb3ea63190ca8` (1195 lines); worktree blob
`4a83f43dfd8970ade29f4c89a021ae7adf88645b` (1191 lines). `git diff HEAD`
shows 17 hunks, 61+/65-, all attributed by content to concurrent-external
work, none to this item (which made zero edits):

- Hunk 1 (imports): `ValidationError` + `from . import truth` in,
  `..exceptions._safe_arg_repr/_safe_type_name` out.
- Hunks 2-6 (name reads): five bare `__name__` reads become `truth.name`
  (`require_managed_write`, the save guard's `sender`, `pin_write_queryset`'s
  `queryset.model`, `check_instance_write_alias`'s `model`, the drift
  message's `type(instance)`).
- Hunk 7 (`pks_match`): `except Exception` narrows to
  `(ValidationError, TypeError, ValueError)` plus a docstring widening.
- Hunk 8 (new): `_FINGERPRINT_CONTAINER_TYPES` plus `_is_one_of`.
- Hunks 9/17 (fail-closed narrowing): the `try/except Exception`
  wrappers in `_FileNameSnapshot.matches` and `assert_no_target_drift`
  are removed; reads go straight through (`truth.is_instance` for the
  `FieldFile` test).
- Hunks 10-12, 14-15 (prose): `guarded repr` becomes `its repr`,
  `guarded key` becomes `canonical sort key`, `hostile-safe` becomes
  plain `treatment`.
- Hunks 11, 13-16 (membership/dispatch): every fingerprint `isinstance`
  becomes `truth.is_instance` or `_is_one_of`; the inline gate tuple
  becomes `_is_one_of(item, _FINGERPRINT_CONTAINER_TYPES)` over the
  same five-member set.

Every hunk is the shared-tree `truth.*` migration plus its adjacent
fail-closed narrowing (untracked
`django_strawberry_framework/utils/truth.py` and `lazy.py` on disk, the
whole `utils/` tree dirty the same way). `ITEM_BASELINE`
(`ba38518cd7807d397a7510c32a032986dc14d115`) resolves this path to
`4a83f43d`, identical to the worktree blob, proving zero worktree change
since the item baseline: the dirt predates this item. No `## Owned
changes` ledger row names this file. This trace reads HEAD bytes only;
worktree bytes are fingerprinted, never reasoned from. The dirt's
behavior deltas (the narrowed catches, the removed wrappers) are
observed-not-adjudicated: concurrent work outside this item.

Consumers, classified (HEAD bytes). Production importers:

- `schema.py` (HEAD `e6b52335`): `managed_write_transaction` (:410, :464)
  and `resolve_write_alias` (:256). Opens the managed transaction.
- `mutations/resolvers.py` (HEAD `043a2d0b`): thirteen names (:108-121).
  The `run_write_pipeline_sync` skeleton opens `open_write_pipeline`
  (:218), installs `pipeline_alias_guard` (:269) and
  `authorization_phase` (:278), captures `snapshot_target_state` (:253),
  pins the locate (:615) and re-checks the instance alias (:240),
  locks via `base_locked_queryset` (:624), backstops with
  `reject_substituted_row` (:287, :320, :1034), marks two write phases
  (:932 model save, :1054 delete), and maps conflicts (:339, :976-977,
  :1098). Its nested `transaction.atomic` (:972) is a savepoint inside
  the pipeline atomic, not a competing boundary.
- `forms/resolvers.py` (HEAD `35c282cc`): `pipeline_write_phase` only
  (:508, :539); both form bases otherwise ride the skeleton (:582).
- `rest_framework/resolvers.py` (HEAD `0d302782`): seven names
  (:158-165). Checks `assert_no_target_drift` (:2333) then marks the
  write phase (:2336), compares with `pks_match` (:1937, :2123, :2134),
  pins author/relation querysets (:1364, :1439, :1456), locks (:1459),
  and runs a second save-guard witness (:2017). Its nested atomic
  (:2350) is likewise a savepoint inside the pipeline.
- `utils/querysets.py` (HEAD `3616927d`): `current_write_pipeline`
  (:4040), `pin_write_queryset` (:4042), `pipeline_scoped_queryset`
  (:4290, :4348). Shared relation checks pin transitively, which is how
  the form flavor (zero direct pin calls) stays pinned.
- `relay.py` (HEAD `c3c5aea5`): lazy `current_write_pipeline` (:277-279)
  to recover the pinned alias for NodeID lookup.
- `auth/mutations.py` (HEAD `d1a59c44`): rides the skeleton unchanged
  (:1159-1161); no direct import.

Composed-by-name inputs (not rules of this file): `ConfigurationError`
plus `_safe_arg_repr`/`_safe_type_name` from `exceptions.py` (HEAD
`e06b0b7f`); `field_error`/`FIELD_ERROR_CODE_CONFLICT` from
`utils/errors.py` (HEAD `3e25e93b`, verified consolidated
`mutation-error-envelope`); `base_container_values`/`canonical_sort_key`
from `utils/canonical.py` (HEAD `b9ded33b`).

Oracles: `tests/mutations/test_write_transaction.py` (HEAD `a6cc3385`;
71 test functions, 2222 lines; spells literal SQL strings, literal
conflict prose, and literal fingerprint expectations — the one owner
read, `_SNAPSHOT_NODE_BUDGET` at :1972/:2006, sizes the over-budget
input while the verdict, a raised `ConfigurationError`, stays
independent), plus the `managed_write_transaction` rows in
`tests/mutations/test_resolvers.py` (HEAD `4f94c05a`) and
`tests/rest_framework/test_resolvers.py` (HEAD `a9162094`). Worktree
oracles dirty (truth migration), NOT traced. Projections: the module
SECURITY MODEL docstring and per-function docstrings; GLOSSARY
`djangomutation` concurrency (row locks plus `conflict`) and
point-in-time authorization rows; the `serializermutation` hardened and
drift-detection rows; the `docs/README.md` conflict sentence; consumer
docstrings restating the phase/alias contract.

## Verification

### Enumeration

Instrument: every name in `ast.Module.body` of the HEAD bytes
(`eca9ad4d`, 1195 lines), read via `git show HEAD:` plus an AST dump.
Count: 53 nodes. Every member lands below; nothing is unassigned.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (five-bullet shape + SECURITY MODEL) | Projection at the owner; supports L1-L13 (prose, not a definition) |
| 1 | `from __future__ import annotations` | Mechanics; no rule |
| 2 | `import threading` | Mechanics (L6 thread scope); no rule |
| 3 | `from contextlib import ...` | Mechanics; no rule |
| 4 | `from contextvars import ContextVar` | Mechanics (L1/L2 state); no rule |
| 5 | `from typing import Any` | Mechanics; no rule |
| 6 | `from django.db import ...` | Mechanics; no rule |
| 7 | `FieldFile` import | Mechanics (L9); no rule |
| 8 | `pre_save` import | Mechanics (L6); no rule |
| 9 | `..exceptions` import (`ConfigurationError`, `_safe_*`) | Consumer link to `exceptions.py`-owned rules; no rule here |
| 10 | `..utils.errors` import | A3 consumer link (verified `mutation-error-envelope`) |
| 11 | `.canonical` import | A1/A2 consumer link |
| 12 | `_MANAGED_WRITE_ALIAS` | L1 (managed-alias flag) |
| 13 | `_WRITE_PIPELINE` | L2 (pipeline context flag) |
| 14 | `_UNMANAGED_SCHEMA_MESSAGE` | L1 (refusal wording) |
| 15 | `WriteAliasContext` | L2 (pipeline record; R1 records the hook-context separation) |
| 16 | `resolve_write_alias` | L1 (one router read) |
| 17 | `managed_write_transaction` | L1 (execution-context seam) |
| 18 | `require_managed_write` | L1 (fail-before-write) |
| 19 | `write_pipeline` | L2 (context installer) |
| 20 | `open_write_pipeline` | L2 (nested atomic + pin substrate) |
| 21 | `pipeline_write_phase` | L3 (phase flag flip) |
| 22 | `_READ_ONLY_BARRIER_VENDORS` | L4 (barrier capability set) |
| 23 | `_enforce_read_only_barrier` | L4 (database-enforced barrier) |
| 24 | `authorization_phase` | L4 (rolled-back auth window) |
| 25 | `_READ_ONLY_SQL_PREFIXES` | L5 (phase allow-list) |
| 26 | `_sql_statement_token` | L5 (comment-stripping tokenizer) |
| 27 | `is_read_only_sql` | L5 (pinned-alias phase predicate) |
| 28 | `make_cross_alias_save_guard` | L6 (pre_save early error) |
| 29 | `pipeline_alias_guard` | L6 (alias + phase net) |
| 30 | `current_write_pipeline` | L2 (read-surface-tolerant read) |
| 31 | `require_write_pipeline` | L2 (misuse-loud read) |
| 32 | `pin_write_queryset` | L7 (explicit-`.using()` fail-closed) |
| 33 | `check_instance_write_alias` | L7 (instance-router re-check) |
| 34 | `canonical_pk` | L8 (to_python equality basis; R2 records the coercion separation) |
| 35 | `pks_match` | L8 (fail-closed compare) |
| 36 | `reject_substituted_row` | L8 (caller-worded backstop) |
| 37 | `_MUTABLE_SNAPSHOT_TYPES` | L9 (snapshot set; R10 records the fingerprint-set separation) |
| 38 | `_ValueSnapshot` | L9 (compare-closing base) |
| 39 | `_FileNameSnapshot` | L9 (name-capture wrapper) |
| 40 | `_SNAPSHOT_NODE_BUDGET` | L10 (walk budget) |
| 41 | `_SnapshotClose` | L10 (stack marker) |
| 42 | `_FieldFingerprint` | L10 (digest wrapper) |
| 43 | `_leaf_token` | L10 (leaf grammar; R3/R4 convergences) |
| 44 | `_field_fingerprint` | L10 (digest walk) + A1 (gate dual-homed; R5 convergence) |
| 45 | `_snapshot_field_value` | L9 (capture ladder) |
| 46 | `snapshot_target_state` | L9 (loaded-fields capture) |
| 47 | `assert_no_target_drift` | L11 (pre-save compare) |
| 48 | `base_locked_queryset` | L12 (base-manager lock) |
| 49 | `pipeline_scoped_queryset` | L12 (pin-plus-conditional-lock) |
| 50 | `conflict_error` | L13 + A3 (envelope leaf) |
| 51 | `not_updated_exceptions` | L13 (version-compat catch set) |
| 52 | `forced_update_conflict_errors` | L13 (usable-plus-absent probe) |

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. The file exists to be the
   one spelling: all flavors ride `run_write_pipeline_sync` (model
   directly; form and serializer as riders; auth register unchanged),
   and the flavor-local `transaction.atomic` sites (`mutations:972`,
   `rest_framework:2350`) are savepoints inside the pipeline atomic,
   never competing boundaries. No flavor re-spells alias resolution,
   pinning, locking, or conflict mapping: the write-alias
   `db_for_write` reads live only here (`resolve_write_alias`,
   `check_instance_write_alias`), which the schema composes by name
   (:256); the one other package read
   (`utils/querysets.py::_snapshot_routing_intent` :2963) is the
   read-surface routing-intent freeze — effective-alias resolution
   with hints for seal comparison, not a write pin.
   `select_for_update()` is attached only by `base_locked_queryset`.
   The five `pipeline_write_phase()` sites
   (model save, model delete, two form saves, serializer save) are five
   enforcement sites around five distinct persist calls, not five
   copies — DRY.md's own vocabulary example.
2. Sync/async twins — NO SUCH SURFACE. Zero `async def` in the target
   (AST-verified); the write pipeline is one sync body the async path
   wraps in a single `sync_to_async(thread_sensitive=True)` call
   (`mutations/resolvers.py::run_pipeline_async`), per principle 5's
   recorded contrast (ORM work must not interleave with awaits inside
   a transaction). No twin to drift.
3. Derived rather than repeated knowledge — SEARCHED. Alias: the hook
   test reads `queryset._db` (explicit `.using()` only), never
   `queryset.db` (L7 states why); instance routing re-derives from the
   router (L7); NodeID lookup recovers the pinned alias from the
   pipeline (relay). Pk equality derives through the pk field's own
   `to_python` (L8), never `str()`; the one `str(pk)` basis in the
   package (`querysets.py::_stringified`) is the F6-rejected membership
   convenience on pre-canonicalized sides (R2). Name rendering is
   two-tier by trust: bare `__name__` for framework-known classes
   (five sites), guarded `_safe_*` for consumer-controlled values
   (the `_leaf_token` opaque arm) — one tier each, composed not
   restated.
4. Inverse / round-trip pairs — SEARCHED. `snapshot_target_state` /
   `assert_no_target_drift` are one capture/compare grammar closed by
   `_ValueSnapshot.matches` (a new kind needs no compare-side edit);
   `_field_fingerprint` / `_leaf_token` are walk/leaf halves;
   `managed_write_transaction` / `require_managed_write` are
   open/consult halves; `write_pipeline` install / `reset` is token
   scoped. All pairs live in this module under one owner each; no half
   is re-spelled elsewhere.
5. Contracts restated in another medium — SEARCHED. Every medium a
   change moves is classified in System trace: 71 package oracles spell
   literal expectations (one setup-only owner read); GLOSSARY carries
   the concurrency, point-in-time, hardening, and drift rows; README
   carries the conflict sentence. No oracle reads the rule it checks.
6. Enforcement by omission — SEARCHED. `assert_no_target_drift` runs on
   the serializer flavor only — intended, contract-sourced (its
   docstring: model/form legitimately mutate inside their own write
   steps). The conflict trio serves the model flavor's forced-update
   path only; the serializer's DRF-owned save is attested differently
   (witness plus post-save attestation, GLOSSARY `serializermutation`
   rows) and no contract source extends forced-update mapping to it.
   The form flavor pins transitively (skeleton locate plus shared
   helpers through `pipeline_scoped_queryset`). No omission gap; nothing
   routes to the maintainer.

Standing triggers checked: `_request_body` J1 (shared `except` guard —
each broad catch here maps a different failure to a different
fail-closed value: `False`, drifted-`True`, envelope-or-raise; R7) and
J2 (shared exact-type gate — subclass-inclusive `isinstance` is the
contract for consumer values; the one exact-type test dispatches the
internal `_SnapshotClose` marker, never a consumer value). Prior-verdict
triggers re-checked on fresh HEAD bytes: canonical FB (A1 converge),
canonical R2/R4/R7 (R3/R4/R5 converge), canonical FA exclusion of
dispatch (A2), `mutation-error-envelope` plus errors R-per-condition
(A3), hook-context R1 (R1 converge), querysets F6 (R2 converge),
policies R3 (R6 converge), operation-lease separation (R9 converge).
No trigger fired for reopening.

### Challenges

Each rule, changes posited on its variation axes, authoritative
definitions counted (consumers, oracles, projections listed, never
counted):

- Managed alias: posit a second managed flag — 1 definition (the
  ContextVar plus its open/consult pair); every flavor follows.
- Pipeline substrate: posit a new write flavor — 0 definitions (rides
  the skeleton); posit a second nesting order — 1 (`open_write_pipeline`).
- Write phase: posit a sixth persist call — 0 definitions (a sixth
  enforcement site, same flag); posit renaming the phase — 1.
- Barrier: posit a third vendor — 1 (the frozenset plus one arm);
  posit weakening to rollback-only — refused (L4 states why).
- SQL gate: posit admitting `WITH` — 1 (the prefix tuple); the
  pin/phase boundaries it backs do not move.
- Alias guard: posit a second guarded phase — 1 (the guard body);
  the save receiver and the statement net move together by
  construction (one factory, one installer).
- Pinning: posit honoring `.using()` — 1 (`pin_write_queryset`);
  posit instance-tolerant routing — 1 (`check_instance_write_alias`).
- Pk trio: posit validator-inclusive equality — refused (R2: answers
  "same row?", not "may this literal enter a query?"); posit a
  `str()`-based compare — refused (the UUID comment plus oracle rows).
- Snapshot ladder: posit a fourth snapshot kind — 1 arm plus 1
  subclass (compare side closed); posit capturing deferred fields —
  refused (L9: lazy-load on capture reads as drift).
- Fingerprint: posit a sixth container — 3 spellings move (A1 family
  evidence: two gates plus the canonical dispatch); posit dropping
  the identity tail — 1 (`_leaf_token`); posit recursion — refused
  (L10: `RecursionError` on deep data).
- Drift compare: posit comparing M2M — 0 here (concrete-fields-only
  is the contract; a new population is a new rule).
- Locks: posit locking the consumer queryset — refused (L12: joins /
  unions cannot carry `FOR UPDATE`); posit a `NOWAIT` arm — 1.
- Conflict: posit a new zero-row signal — 1 (`not_updated_exceptions`);
  posit envelope-without-probe — refused (L13: genuine errors must
  propagate).

No read-only probe was needed: every claim above is decided statically
against HEAD bytes (definition counts, import census, producer census,
grep-verified absences), so no `docs/dry/temp-tests/` scope was created
and no pytest ran. No workspace runs at all (all inspection read-only in
the shared tree: `git rev-parse`/`git show`/`git grep HEAD`,
`git hash-object`, worktree greps; nothing source-mutating).

## Findings

### A1 — CONVERGE into open `canonical-container-membership` (transcribes nothing)

The five-type gate in `_field_fingerprint` (:951-959, order
dict/list/tuple/set/frozenset) is one of the three spellings the
verified File `utils/canonical.py` FB names (the others: the
`inputs.py` gate and the canonical dispatch). Re-read at HEAD: the
tuple holds exactly the five builtins, `isinstance` order is cosmetic
(the two gates already differ in order), and the follow-on dispatches
(dict arm, list/tuple arm, set arm) dispatch, never re-define, the
membership — converge with the canonical artifact's exclusion. The
per-shape dispatches plus `_snapshot_field_value`'s ladder are
dispatch, not membership. Observed (NOT reasoned from): the worktree
refactors this gate to `_is_one_of` over `_FINGERPRINT_CONTAINER_TYPES`
holding the same five-member set — the family evidence survives the
refactor either way.

Freshness: target HEAD `eca9ad4d`; `utils/canonical.py` HEAD
`b9ded33b`, `utils/inputs.py` HEAD `ee31d360` (per the verified
canonical artifact at this same HEAD).

### A2 — CONSUME open `base-slot-container-reads` (transcribes nothing)

The `members = base_container_values(item)` call (:977) composes the
family's owner candidate by name; this file holds zero inline
`dict.items(x)` / `list.__iter__` restatements (HEAD grep for
`dict.items`, `__iter__(`, `__repr__(` outside `_leaf_token`'s atom
arms: no hits). The atom base-slot reads inside `_leaf_token`
(`int.__repr__`, `str.__repr__`, the `memoryview` buffer) are the
per-atom content rendering the canonical R4 already separates from
member enumeration — converge with that rejection (R4), not a new
family leg.

Freshness: target HEAD `eca9ad4d`; `utils/canonical.py` HEAD
`b9ded33b`.

### A3 — CONSUME verified `mutation-error-envelope` (transcribes nothing)

`conflict_error` composes `field_error` plus `FIELD_ERROR_CODE_CONFLICT`
by name — a consumer of the consolidated family, not a definition.
Converge with verified File `utils/errors.py`
`errors-per-condition-wrappers` on fresh evidence: the per-condition
wrapper stays at the call site (the conflict prose plus the `id` key
is this pipeline's rule), the constructor stays in `errors.py`.
The oracles spell the literal `conflict` code, never the imported
constant.

Freshness: target HEAD `eca9ad4d`; `utils/errors.py` HEAD `3e25e93b`.

### L1 — Managed write alias (file-local)

`_MANAGED_WRITE_ALIAS` plus `_UNMANAGED_SCHEMA_MESSAGE`,
`managed_write_transaction` (execution-context seam),
`require_managed_write` (fail-before-write), and `resolve_write_alias`
(the one router read; model-less forms take `DEFAULT_DB_ALIAS`).
One definition; consumers are the schema (opens) and the skeleton
(requires). Challenge: a second managed flag counts 1; a new flavor
counts 0. Reconsideration trigger: a second write-alias router-read
site.

Freshness: target HEAD `eca9ad4d`; `schema.py` HEAD `e6b52335`.

### L2 — Pipeline context substrate (file-local)

`_WRITE_PIPELINE` plus `WriteAliasContext` (the `(alias, lock)` record
with `authorized_pk`, `target_state`, phase flags),
`write_pipeline`/`open_write_pipeline` (nested atomic plus pin),
`current_write_pipeline` (read-surface-tolerant) and
`require_write_pipeline` (misuse-loud). One substrate; every flavor
rides it through the skeleton. Challenge: a new flavor counts 0; a
second nesting order counts 1. Reconsideration trigger: a second
pipeline-context record or a flavor bypassing the skeleton.

Freshness: target HEAD `eca9ad4d`.

### L3 — Write-phase flag (file-local)

`pipeline_write_phase()` flips `WriteAliasContext.write_phase` for
exactly one save/delete call; five enforcement sites (model save,
model delete, two form saves, serializer save) each wrap their own
persist call. Challenge: a sixth persist call adds a sixth site and
moves 0 definitions. Reconsideration trigger: a phase the flag cannot
express (a second flag, not a sixth site).

Freshness: target HEAD `eca9ad4d`; consumers at `mutations/resolvers.py`
HEAD `043a2d0b`, `forms/resolvers.py` HEAD `35c282cc`,
`rest_framework/resolvers.py` HEAD `0d302782`.

### L4 — Read-only barrier plus authorization window (file-local)

`_READ_ONLY_BARRIER_VENDORS` (postgresql, sqlite),
`_enforce_read_only_barrier` (transaction-scoped `SET TRANSACTION READ
ONLY`, connection-scoped `PRAGMA query_only` with save/restore), and
`authorization_phase` (rolled-back barrier transactions over
non-pinned auth aliases for exactly the permission call). Fail-closed
by construction: an unlistable vendor raises, never degrades.
Challenge: a third vendor counts 1 set plus 1 arm. Reconsideration
trigger: a second read-only-barrier need or a barrier surviving the
auth window.

Freshness: target HEAD `eca9ad4d`.

### L5 — Pinned-alias SQL phase gate (file-local)

`_READ_ONLY_SQL_PREFIXES` (SELECT plus savepoint verbs),
`_sql_statement_token` (comment-stripping, paren-skipping tokenizer
over base-string content; non-strings unclassifiable), and
`is_read_only_sql` (allow-list predicate). Phase-ordering discipline
only — the SECURITY MODEL states why a lexical gate is acceptable
here and nowhere else. Challenge: admitting a token counts 1.
Reconsideration trigger: a second SQL-classification need, or any
cross-alias use of this predicate (forbidden by contract).

Freshness: target HEAD `eca9ad4d`.

### L6 — Alias guard pair (file-local)

`make_cross_alias_save_guard` (thread-scoped `pre_save` early error,
shared with the serializer witness) plus `pipeline_alias_guard` (the
`execute_wrapper` net: pinned connection phased, every other
connection rejecting outright except auth aliases inside the auth
window). One factory, one installer; the receiver and the net move
together by construction. Challenge: a second guarded phase counts 1.
Reconsideration trigger: a guard installed outside the skeleton, or a
third `pre_save` blocker not built by the factory.

Freshness: target HEAD `eca9ad4d`.

### L7 — Alias pinning pair (file-local)

`pin_write_queryset` (an explicit `.using()` elsewhere fails closed;
un-routed hooks take the pin — `queryset.db` is deliberately NOT the
test) plus `check_instance_write_alias` (the post-locate router
re-check with the instance known). Challenge: honoring `.using()`
counts 1; instance-tolerant routing counts 1. Reconsideration trigger:
a legitimately cross-alias write pipeline.

Freshness: target HEAD `eca9ad4d`.

### L8 — Canonical pk trio (file-local)

`canonical_pk` (equality through the pk field's own `to_python`;
raises on uncoercible), `pks_match` (fail-closed compare), and
`reject_substituted_row` (caller-worded backstop over `pks_match`).
Answers "same row?", never "may this literal enter a query?" (R2).
Challenge: validator-inclusive equality and `str()` comparison are
both refused with pinned reasons. Reconsideration trigger: a second
pk-equality basis not routed through `to_python`.

Freshness: target HEAD `eca9ad4d`.

### L9 — Snapshot capture ladder (file-local)

`_MUTABLE_SNAPSHOT_TYPES` (six members: five containers plus
bytearray), `_snapshot_field_value` (FieldFile by name, mutables by
fingerprint, scalars aliased), `snapshot_target_state` (loaded
concrete fields only; deferred fields excluded), `_ValueSnapshot`
(the compare-closing base), and `_FileNameSnapshot` (the
database-relevant `name`). The capture/compare contract is one
grammar: a fourth kind is one arm plus one subclass. Challenge:
a fourth kind counts 1 arm (compare side closed). Reconsideration
trigger: a second snapshot population (M2M, deferred) or a wrapper
compared outside `matches`.

Freshness: target HEAD `eca9ad4d`.

### L10 — Structural fingerprint walk (file-local)

`_field_fingerprint` (iterative stack walk: cycle guard, node budget
`_SNAPSHOT_NODE_BUDGET`, base-iterator reads, canonical ordering,
dict keys walked as nodes), `_leaf_token` (two-tier leaf grammar:
base-slot atoms, identity-discriminated opaque), `_FieldFingerprint`
(digest wrapper), and `_SnapshotClose` (stack marker). The membership
gate dual-homes to A1; the leaf tail converges with R3, the atom reads
with R4, the output encoding with R5. Challenge: dropping the tail
counts 1; recursion is refused (`RecursionError` on deep data).
Reconsideration trigger: a second fingerprint walk or a persisted
(not request-scoped) digest.

Freshness: target HEAD `eca9ad4d`.

### L11 — Pre-save drift compare (file-local)

`assert_no_target_drift` re-reads loaded concrete fields against the
post-locate snapshot: by-value wrappers compare via `matches`,
scalars by identity-or-equality, unreadable comparisons fail closed
into the typed envelope. Serializer-flavor-only by contract (matrix
axis 6). Challenge: a second drift population is a new rule, 0 here.
Reconsideration trigger: a second flavor adopting the check with
divergent compare semantics.

Freshness: target HEAD `eca9ad4d`.

### L12 — Row-lock pair (file-local)

`base_locked_queryset` (lock rides the base manager constrained by a
visibility pk subquery — never `select_for_update()` on the
consumer queryset) plus `pipeline_scoped_queryset` (pin plus
conditional lock for shared helpers; identity on read surfaces).
Challenge: locking the consumer queryset is refused (unions/joins
cannot carry `FOR UPDATE`); a `NOWAIT` arm counts 1.
Reconsideration trigger: a lock not routed through the base manager.

Freshness: target HEAD `eca9ad4d`.

### L13 — Disappearing-row conflict trio (file-local)

`conflict_error` (A3 consumer), `not_updated_exceptions` (typed
`Model.NotUpdated` on Django 6, bare `DatabaseError` on 5.2), and
`forced_update_conflict_errors` (conflict ONLY on usable-transaction
plus row-absent probe; anything else re-raises). Challenge: a new
zero-row signal counts 1; envelope-without-probe is refused (genuine
errors must propagate and roll back). Reconsideration trigger: a
second conflict-mapping path not routed through the probe.

Freshness: target HEAD `eca9ad4d`.

### R1 — Pipeline record versus hook-context record (rejected)

CONVERGE with verified File `rest_framework/hook_context.py`
`hook-context-vs-pipeline-interior` on fresh evidence:
`WriteAliasContext` is MUTABLE interior lifecycle state the guard,
skeleton, and flavors mutate through the operation;
`SerializerHookContext` is a FROZEN triple crossing a trust boundary
into indefinitely-held consumer code. Handing hooks the interior
would expose phase flags and loaded target state. One projection
line copies the two overlapping values — not a second definition.
Reconsideration trigger: a second consumer-facing hook surface
needing the same triple.

### R2 — Pk equality versus field-value coercion (rejected)

CONVERGE with rejected `field-value-coercion` (querysets F6) on fresh
evidence: `canonical_pk`/`pks_match` compare two uncoerced sides for
row identity, raise-or-mismatch, deliberately skipping
`run_validators`; `coerce_field_value_or_none` coerces one literal
for query entry, `None`-on-invalid, validators included. The UUID
comment re-read at HEAD still warns exactly the case the
`_stringified` membership basis cannot cover (both its sides are
pre-canonicalized). Reconsideration trigger: uncoerced pks reaching
`stringified_pks_present` (F6's trigger, re-stated).

### R3 — Leaf-token identity tail versus the sort key (rejected)

CONVERGE with verified File `utils/canonical.py` R2 on fresh evidence:
the `_leaf_token` opaque arm ends its fragment with the identity pair
for fingerprint-suffix uniqueness — an ordering of nothing — versus
`canonical_sort_key`'s content-headed total order. Reconsideration
trigger: leaves needing ordering, or keys needing fingerprint grammar.

### R4 — Atom base-slot reads versus container iteration reads (rejected)

CONVERGE with verified File `utils/canonical.py` R4 on fresh evidence:
`_leaf_token`'s per-atom-type content rendering (which atoms are
content-honest, which opaque, bytes type-insensitive) versus
`base_container_values`' member enumeration. Same threat model, no
single contract. Reconsideration trigger: a base-slot primitive
spanning atoms and containers with one contract.

### R5 — Fingerprint output encoding versus hashable meta encoding (rejected)

CONVERGE with verified File `utils/canonical.py` R7 on fresh evidence:
the flat digest string (request-scoped drift check) versus the
hashable structure (construction-time cache key). Disjoint variation
axes; unifying them couples a cache to a check. Reconsideration
trigger: a third consumer needing both encodings from one walk.

### R6 — Per-message rejection wording versus a shared grammar (rejected)

CONVERGE with verified File `utils/policies.py` R3 on fresh evidence:
twelve `raise ConfigurationError(...)` sites carry eleven own wordings
— each naming its own subject (alias, phase, vendor, field) — plus one
caller-worded raise (`reject_substituted_row`, :758): zero shared
template beyond the exception type. The package has no owned
rejection-message grammar, and none is owed. Reconsideration trigger:
the package adopts one.

### R7 — Shared `except`-guard driver (rejected)

The broad catches map different failures to different fail-closed
values: `pks_match` to `False`, `_FileNameSnapshot.matches` to
`False`, `assert_no_target_drift` to drifted-`True`, the conflict
probe to re-raise. A shared driver would take the outcome as a
parameter and pin nothing — each site's mapping IS its contract.
Standing J1 trigger checked and unfired. Reconsideration trigger: two
sites mapping the same failure to the same value for the same reason.

### R8 — Field drift versus the relation-intent ledger (rejected)

The serializer flavor's relation-intent ledger (which resolved objects
each relation field's validation produced) and this module's
field-value drift check (loaded scalar/container columns) police
different populations against different substitutions: relation
resolution versus in-memory field mutation. A unified pre-save
attestation primitive would own the audit moment but no single
comparison. Reconsideration trigger: one comparison spanning resolved
relations and loaded columns.

### R9 — Pipeline ContextVar versus the operation lease (rejected)

CONVERGE with the owner-recorded lease separation (verified
`orders-ledger-vs-operation-lease`) on fresh evidence:
`_WRITE_PIPELINE` is ambient cooperative context (set/reset tokens,
read-tolerant on read surfaces); `utils/operation_lease.py` is a
revocable capability over operation-owned state. The pipeline needs
no revocation. Reconsideration trigger: the pipeline needing to
revoke mid-operation access.

### R10 — Snapshot set versus fingerprint set (rejected)

In-file intentional separation: `_MUTABLE_SNAPSHOT_TYPES` holds six
members (five containers plus bytearray — "must fingerprint rather
than alias"), the `_field_fingerprint` gate holds five (bytearray
excluded — "walk as a container"). A bytearray IS snapshotted (mutable
in place) but fingerprinted as a LEAF (base-buffer read), never walked.
Different sets by contract, stated at the owner by this record since a
file item lands no edit. Reconsideration trigger: bytearray walked as
a container, or a seventh mutable kind joining one set but not the other.

## Defects

None. Near-misses ruled out against HEAD bytes: the three broad
`except Exception` catches are contracted fail-closed mappings (R7),
each pinned by oracle rows — no contract source asks for narrower;
the `type(item) is _SnapshotClose` exact-type test dispatches an
internal stack marker, never a consumer value (J2 inapplicable);
`authorization_phase`'s `resolve_auth_aliases` citation resolves
(`utils/permissions.py:291`). The worktree's narrowed catches and
removed wrappers are concurrent-external behavior deltas, observed
and fingerprinted, never adjudicated here.

## Pending execution

None. All conclusions are static against HEAD bytes; no probe, no
pytest, no scratch scope, no workspace runs. No finding relies on
execution, so no cell-specific proof is owed (the module reaches
databases, so no inapplicable-by-construction claim is made — there
is simply nothing to execute).

## Judgment

Zero-edit file item: the target single-owns the write discipline its
module docstring states, composed by name across six production
consumers plus the skeleton's transitive riders, with one open-family
convergence (A1 into `canonical-container-membership`), two
consume-by-name convergences (A2, A3), thirteen file-local rows, ten
rejections (eight converging with prior verdicts on fresh evidence,
two fresh), and zero defects. No pending execution, no production
edit, no test edit. All seventeen worktree hunks are
concurrent-external truth-migration dirt predating the item baseline;
HEAD (`0c0537e2`) did not move during this item.

## Index rows for Worker 0

(Worker 0 alone edits the plan; rows named here for transcription.
A1/A2/A3 converge into existing rows and transcribe nothing.)

- Managed write alias | `utils/write_transaction.py` (`_MANAGED_WRITE_ALIAS`, `_UNMANAGED_SCHEMA_MESSAGE`, `resolve_write_alias`, `managed_write_transaction`, `require_managed_write`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single definition; trigger: second write-alias router-read site)
- Pipeline context substrate | `utils/write_transaction.py` (`_WRITE_PIPELINE`, `WriteAliasContext`, `write_pipeline`, `open_write_pipeline`, `current_write_pipeline`, `require_write_pipeline`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single substrate; trigger: second pipeline record or skeleton bypass)
- Write-phase flag | `utils/write_transaction.py::pipeline_write_phase` | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (five enforcement sites, one flag; trigger: a phase the flag cannot express)
- Read-only barrier plus authorization window | `utils/write_transaction.py` (`_READ_ONLY_BARRIER_VENDORS`, `_enforce_read_only_barrier`, `authorization_phase`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single barrier; trigger: second barrier need or window survival)
- Pinned-alias SQL phase gate | `utils/write_transaction.py` (`_READ_ONLY_SQL_PREFIXES`, `_sql_statement_token`, `is_read_only_sql`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single predicate; trigger: second SQL-classification need or cross-alias use)
- Alias guard pair | `utils/write_transaction.py` (`make_cross_alias_save_guard`, `pipeline_alias_guard`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (one factory, one installer; trigger: guard outside the skeleton or third blocker)
- Alias pinning pair | `utils/write_transaction.py` (`pin_write_queryset`, `check_instance_write_alias`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single pin contract; trigger: legitimately cross-alias pipeline)
- Canonical pk trio | `utils/write_transaction.py` (`canonical_pk`, `pks_match`, `reject_substituted_row`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single basis; trigger: second pk-equality basis outside `to_python`)
- Snapshot capture ladder | `utils/write_transaction.py` (`_MUTABLE_SNAPSHOT_TYPES`, `_ValueSnapshot`, `_FileNameSnapshot`, `_snapshot_field_value`, `snapshot_target_state`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (compare side closed; trigger: second snapshot population or out-of-`matches` compare)
- Structural fingerprint walk | `utils/write_transaction.py` (`_field_fingerprint`, `_leaf_token`, `_FieldFingerprint`, `_SnapshotClose`, `_SNAPSHOT_NODE_BUDGET`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (gate dual-homed to open `canonical-container-membership`; trigger: second walk or persisted digest)
- Pre-save drift compare | `utils/write_transaction.py::assert_no_target_drift` | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (serializer-only by contract; trigger: second flavor with divergent semantics)
- Row-lock pair | `utils/write_transaction.py` (`base_locked_queryset`, `pipeline_scoped_queryset`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single lock route; trigger: lock outside the base manager)
- Disappearing-row conflict trio | `utils/write_transaction.py` (`conflict_error`, `not_updated_exceptions`, `forced_update_conflict_errors`) | `utils/write_transaction.py` | File `utils/write_transaction.py` | file-local (single probe; trigger: second conflict path outside the probe)
- Pipeline record versus hook-context record | `utils/write_transaction.py::WriteAliasContext` (rejection recorded here; CONVERGE with verified File `rest_framework/hook_context.py` R1) | `utils/write_transaction.py`, `rest_framework/hook_context.py` | File `utils/write_transaction.py` | rejected
- Pk equality versus field-value coercion | `utils/write_transaction.py::canonical_pk` (rejection recorded here; CONVERGE with rejected `field-value-coercion` F6) | `utils/write_transaction.py`, `utils/querysets.py`, `utils/write_values.py`, `relay.py`, `filters/base.py`, `keyset.py` | File `utils/write_transaction.py` | rejected
- Leaf-token identity tail versus the sort key | `utils/write_transaction.py::_leaf_token` (rejection recorded here; CONVERGE with verified File `utils/canonical.py` R2) | `utils/write_transaction.py`, `utils/canonical.py` | File `utils/write_transaction.py` | rejected
- Atom base-slot reads versus container iteration reads | `utils/write_transaction.py::_leaf_token` (rejection recorded here; CONVERGE with verified File `utils/canonical.py` R4) | `utils/write_transaction.py`, `utils/canonical.py` | File `utils/write_transaction.py` | rejected
- Fingerprint output encoding versus hashable meta encoding | `utils/write_transaction.py::_field_fingerprint` (rejection recorded here; CONVERGE with verified File `utils/canonical.py` R7) | `utils/write_transaction.py`, `utils/inputs.py`, `utils/canonical.py` | File `utils/write_transaction.py` | rejected
- Per-message rejection wording versus a shared grammar | `utils/write_transaction.py` (rejection recorded here; CONVERGE with verified File `utils/policies.py` R3) | `utils/write_transaction.py` | File `utils/write_transaction.py` | rejected
- Shared except-guard driver | `utils/write_transaction.py` (rejection recorded here; standing J1 trigger checked) | `utils/write_transaction.py` | File `utils/write_transaction.py` | rejected
- Field drift versus the relation-intent ledger | `utils/write_transaction.py::assert_no_target_drift` (rejection recorded here; fresh pair) | `utils/write_transaction.py`, `rest_framework/resolvers.py` | File `utils/write_transaction.py` | rejected
- Pipeline ContextVar versus the operation lease | `utils/write_transaction.py::_WRITE_PIPELINE` (rejection recorded here; CONVERGE with the owner-recorded lease separation) | `utils/write_transaction.py`, `utils/operation_lease.py` | File `utils/write_transaction.py` | rejected
- Snapshot set versus fingerprint set | `utils/write_transaction.py::_MUTABLE_SNAPSHOT_TYPES` (rejection recorded here; in-file intentional separation) | `utils/write_transaction.py` | File `utils/write_transaction.py` | rejected

## Independent verification (Worker-2)

Trace recorded expectation-first (HEAD bytes `eca9ad4d`, 1195 lines;
before opening `## Findings`): instrument `ast.Module.body` gives 53
nodes (docstring + 11 imports + 2 ContextVars + 1 message const +
WriteAliasContext + 37 defs/assigns/classes) — matches W1's 53/53
member by member, all homed. Consumers: 6 production importers
(schema, mutations/resolvers, forms/resolvers,
rest_framework/resolvers, utils/querysets, relay) plus auth riding
the skeleton import-free; `pipeline_write_phase` has exactly 5
enforcement sites (mutations :932/:1054, forms :508/:539, serializer
:2336). No `async def` (axis 2 inapplicable). All 15 cited HEAD
fingerprints re-hashed exact; all cited consumer line numbers
spot-checked against `git show HEAD:` exact (incl. the `:291`
`resolve_auth_aliases` def — worktree dirt moved it to :271).

Judgments. (1) Enumeration: STANDS, 53/53 over HEAD bytes.
(2) Hunks: STANDS — 17 `@@` headers, 61+/65- re-counted;
ITEM_BASELINE resolves this path to `4a83f43d` = worktree blob
(predates baseline); no ledger row names the file; `truth.py` +
`lazy.py` untracked; every hunk is `truth.*` migration or adjacent
narrowing by content. (3) A1/A2/A3: STAND — the :951-960 gate spells
the FB five-set; `:977` composes `base_container_values` by name
with zero inline restatements (HEAD grep re-run); `conflict_error`
composes the consolidated envelope by name with literal-`conflict`
oracles (:1132/:1178). (4) Rejections: 9 of 10 STAND on fresh
evidence (R1/R3/R4/R5/R7/R8/R9/R10 verified; R2's F6 trigger
re-checked unfired — both `stringified_pks_present` caller chains
type-check first at HEAD). R6's CONVERGE direction stands but its
evidence sentence is wrong — see V1. (5) Zero-defect call: STANDS —
the three `except Exception` catches are contracted fail-closed and
HEAD-oracle-pinned (`not pks_match(...,"not-a-uuid")`,
`test_assert_no_target_drift_fails_closed_on_a_hostile_eq`,
`test_file_name_snapshot_fails_closed_on_a_hostile_replacement`;
worktree rewrites of those rows are concurrent dirt);
`type(item) is _SnapshotClose` dispatches an internal marker (J2
inapplicable); `resolve_auth_aliases` resolves. Matrix axis-1
`select_for_update()` census re-verified (sole code call :1104);
the `db_for_write` census is wrong — see V2. HEAD unmoved
(`0c0537e2`). Nothing tracked touched (artifact untracked); no
ruff gate owed on scratch `.md`.

V1 (R6 count): "fourteen distinct wordings" is false at HEAD.
AST count of `raise ConfigurationError(...)` = 12 (:215, :310,
:515, :580, :610, :664, :688, :709, :758, :946, :964, :1083), and
:758 (`reject_substituted_row`) raises the CALLER's message, so
eleven own wordings + one caller-worded. Repro: AST-walk
`git show HEAD:django_strawberry_framework/utils/write_transaction.py`
counting `Raise` nodes whose func is `ConfigurationError` (= 12).
Fix: restate the sentence with 12/11+1; conclusion unchanged.

V2 (axis-1 census): "`db_for_write` is read only here ... plus the
schema's one call" is false at HEAD. `git grep -n db_for_write
HEAD -- django_strawberry_framework` shows (a)
`utils/querysets.py::_snapshot_routing_intent` :2963 (`resolve =
router.db_for_write if for_write ...`, read-surface routing-intent
freeze — distinct contract: effective-alias resolution with hints
for seal comparison, not a write pin) and (b) NO `db_for_write`
hit in `schema.py` (schema.py:256 composes `resolve_write_alias`
by name). Fix: census the seal read with its contract difference
and correct the schema clause; tighten L1's trigger to "a second
write-alias router-read site" so the read-surface seal cannot
fire it. L1 homing unchanged.

Resubmission (SAME Worker-2 context): fix V1 + V2 sentences only,
keep `Status: revision-needed` until re-verified; no production or
test edits; no new families, rows, or defects.

## Iterations

### Pass 2 (Worker-1 resubmission; record accuracy only)

V1 + V2 per `## Independent verification (Worker-2)`, both
independently re-derived against HEAD bytes before editing: AST
`Raise`-node walk over HEAD `eca9ad4d` = 12 `ConfigurationError`
sites (:215/:310/:515/:580/:610/:664/:688/:709/:758/:946/:964/:1083),
:758 raising the caller's message; `git grep db_for_write HEAD`
census = this file's :184/:707 plus `querysets.py:2963`
(routing-intent freeze), schema.py zero hits with :256 composing
`resolve_write_alias` by name. Sentences moved: R6 count (12 sites =
eleven own wordings + one caller-worded :758), axis-1 census (seal
read added with its contract difference, schema clause corrected),
L1 trigger plus its index row (tightened to "a second write-alias
router-read site"). Every judgment stands; no new families, rows,
findings, or defects; no production or test edits. HEAD unmoved
(`0c0537e2`).

### Re-pass (Worker-2, same context)

V1 re-derived: AST `Raise`-walk = 12 sites at the same 12 lines;
R6 now reads twelve/eleven-plus-caller-worded-:758 — reproduces.
V2 re-derived: `git grep db_for_write HEAD` = this file :184/:707
+ `querysets.py:2963`, schema.py zero hits; axis-1 sentence, L1
trigger, and index row corrected — reproduces. All other sections
byte-stable, W2 section untouched, target diff vs ITEM_BASELINE
still empty, worktree blob still `4a83f43d`, HEAD still `0c0537e2`.
Verdict: verified.
