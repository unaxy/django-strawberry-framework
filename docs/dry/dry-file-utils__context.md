# DRY review: `utils/context.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target `django_strawberry_framework/utils/context.py` is the single owner of
shape-agnostic read / write / delete dispatch over Strawberry's
`info.context` (`None` / object / dict / frozen / `__slots__`-mapping /
bridged-`__getitem__`). Two subsystems hand off through the request context
and share these helpers by name: the optimizer stashes
(`optimizer/_context.py`, which re-exports `get_context_value` and
`stash_on_context` for its subpackage) and the request resource policy
(`resource_policy.py`, `extensions/resource_policy.py`). No production edit:
the module already composes every consumer by name, and the round trip
(`restored_context_keys` + public `MISSING`) is the one body its sole
consumer cites.

Attribution of the dirty hunk. The worktree target (`edebf0ea`, 238 lines)
differs from HEAD (`cd0adcc5`) by exactly one hunk (9+/20-) inside
`get_context_value`: the read-side `except Exception` fail-closed contract
narrowed to `except (KeyError, TypeError, AttributeError)`, the
getattr-`try`/`except` removed, docstring rewritten to "anything else a
consumer context's own descriptor or mapping method raises is its behaviour
and propagates". No `## Owned changes` ledger row names this file, and the
hunk is byte-identical inside `ITEM_BASELINE=1c3c6220` (that tree carries
blob `edebf0ea`), so it predates this item and is concurrent-external by
content on both tests. Its oracle moves with it: HEAD
`tests/utils/test_context.py` pins fail-closed hostile reads
(`test_context_read_fails_closed_for_hostile_attribute_and_mapping_access`,
`test_context_read_tries_mapping_after_hostile_attribute`) while the
worktree pins propagation
(`test_context_read_propagates_a_consumer_descriptor_error`) — a coherent
concurrent code+oracle pair, observed here, not a defect, untouched. This
artifact traces HEAD bytes throughout; every dirty-file claim below was
verified against `git show HEAD:` (see `## Index rows for Worker-0`).

Consumer census (package-wide `grep` for the four helper names: 5 package
files, all composing by name, zero bypasses): `optimizer/_context.py`
(re-export + `optimizer_value` / `stash_for_optimizer` /
`clear_optimizer_context` delegation), `resource_policy.py`
(`_publish_budget_mirror`, `clear_resource_context`, `policy_from_info`,
`check_deadline`), `extensions/resource_policy.py` (sole
`restored_context_keys` consumer in `on_operation`), `optimizer/extension.py`
(`_stash_on_context` compat re-export + `_stash_union` via
`_optimizer_value`), `types/resolvers.py` (transitive, via
`optimizer_value`). A `setattr`/`delattr`/`del context[` sweep finds no
hand-rolled context-key write outside the target. Oracles:
`tests/utils/test_context.py` (unit pins incl. the two HOSTILE states above),
`tests/optimizer/test_extension.py` (the two `__slots__`/bridged pins the
docstring names, present at both heads), `tests/test_resource_policy.py`
(one comment cite), and live `test_query/test_extension_isolation_api.py`,
`test_list_field_api.py`, `test_list_field_async_api.py`.

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — searched. `hook_context.py`'s frozen
   hook record (R1, CONVERGE with the verified rejection), permission
   request decoding `request_from_info` (R2), frame-routed optimizer reads
   (R3), canonical container reads (R4), sibling absent-sentinels (R5),
   per-family key-set clears (R6) all examined on bodies; each carries a
   recorded contract difference.
2. **Sync/async twins** — inapplicable with reason: the four helpers are pure
   synchronous dispatch (no await, no ORM, no suspension point); the sole
   `restored_context_keys` consumer wraps a synchronous `on_execute` scope.
   No twin exists to drift.
3. **Derived rather than repeated knowledge** — searched. The six
   `getattr(info, "context", ...)` sites (`types/resolvers.py`,
   `resource_policy.py`, `utils/permissions.py`, + target docstring) are the
   helpers' designed call shape into the `None`-tolerant contract, not a
   second derivation; the helpers are deliberately info-agnostic (R2). Each
   `DST_*` key vocabulary is owned once by its family; no key set is
   re-derived from another.
4. **Inverse / round-trip pairs** — one grammar, one module: read
   (`get_context_value`), write (`stash_on_context`), delete
   (`clear_context_key`), snapshot-restore (`restored_context_keys`)
   composed by name, with `MISSING` as the public round-trip identity. The
   extension's own comment records that it deleted its hand-rolled sentinel
   for this body.
5. **Contracts restated in another medium** — inventoried, roles tagged.
   Definitions: the four helpers + `MISSING` (target only). Consumers: the
   five package files above. Oracles: the unit/live pins above (independent:
   they spell shapes and assert behavior, never import the dispatch table).
   Projections: the spec-047 cite, consumer docstrings citing this module by
   name, and this artifact. No restatement found a second definition.
6. **Enforcement by omission** — enumerated the family {read, write, delete,
   restore} × {`None`, dict, object, frozen, locked-`QueryDict`,
   `__slots__`-mapping, bridged-`__getitem__`}: every cell is documented and
   pinned; the locked-`QueryDict` `AttributeError` arm is covered on write
   AND delete. No member lacks a guard its contract requires; no bypass
   writer exists (sweep above). No defect.

### Enumeration

Instrument: every statement in `ast.Module.body` — 12 statements (module
docstring, 4 imports, `__all__`, `MISSING` + its docstring, 4 function
defs). Homed members: 7 (module docstring, import/`__all__` mechanics, and
the 5 public names). Every member lands below: F1–F5 cover all 7;
R1–R8 are the considered-and-rejected second sites; 0 families named.

| Member | Home |
|---|---|
| Module docstring (shape contract, two-subsystem share, defensive-coerce stance) | F5 |
| Imports + `__all__` (5 names) | F5 |
| `MISSING` | F4 |
| `get_context_value` | F1 |
| `stash_on_context` | F2 |
| `clear_context_key` | F3 |
| `restored_context_keys` | F4 |

### Challenges

Each rule's variation axes exercised; counts are authoritative definitions.

- **F1 read dispatch.** (a) New context shape (new exception class on item
  read) → 1 (`get_context_value` + its docstring; the module docstring
  names exactly this landing). (b) Narrow/widen the swallowed set → 1 —
  and the concurrent-external hunk IS this change, landing on one body with
  no second site to sync. (c) Flip dict-vs-attribute precedence (incl. the
  `Box`-subclass `__getitem__`-first rule) → 1. Consumers/oracles move as
  listed, uncounted.
- **F2 write dispatch.** (a) New frozen-shape error mode → 1 (the
  `(TypeError, AttributeError)` tail). (b) `None`-context posture → 1 for
  the write contract (skip); the read/delete guards are distinct return
  contracts (R8). (c) `setattr`-first vs `__setitem__`-first order → 1.
- **F3 delete dispatch.** (a) New read-only shape (e.g. a mapping raising a
  third error on `__delitem__`) → 1. (b) `.pop()`-fast-path vs guarded
  `del` tail → 1 (the docstring records why the tail is shared).
  (c) Missing-key posture (silent vs loud) → 1.
- **F4 round trip + sentinel.** (a) Restore order / restore-on-exception
  semantics → 1 (`restored_context_keys`). (b) `MISSING` identity → 1 (the
  public sentinel; the extension's deleted private sentinel proves the
  migration already happened). (c) Snapshot-vs-swap shape → 1 (docstring
  records snapshot-and-restore as the decision).
- **F5 mechanics.** No variation axis; docstring/imports/`__all__`
  scaffolding. No challenge owed.

## Findings

### File-local

- **F1 — shape-agnostic context read.** `get_context_value`: `None`
  short-circuit, dict-first via `.get`, attribute-first with `MISSING`
  fall-through to `context[key]` for non-dict mappings, missing-key tuple
  returning `default`. Single definition; HEAD bytes carry the
  `except Exception` fail-closed contract, worktree the narrowed tuple —
  one body either way.
- **F2 — shape-agnostic context write.** `stash_on_context`: dict guard
  around the `setattr` block, catch-and-chain to one shared mapping-write
  tail, frozen shapes silently skipped. Single definition.
- **F3 — shape-agnostic context delete.** `clear_context_key`: dispatch
  mirrors F2 exactly (guard + shared tail, locked-`QueryDict` routed
  through it, never a `.pop()` fast path). Single definition.
- **F4 — snapshot-restore round trip + absent-marker.** `restored_context_keys`
  composes F1/F2/F3 by name under `finally`; public `MISSING`
  distinguishes absent from stashed-`None`. Single definition; the only
  producer/consumer pair is the target + `extensions/resource_policy.py`.
- **F5 — module mechanics.** Docstring contract (shape list, two-subsystem
  share, spec-047 cite, defensive-coerce stance), 4 imports, 5-name
  `__all__`. Scaffolding, single-owned.

### Rejected

- **R1 — hook-record vs request-context helpers.** CONVERGE with verified
  `hook-context-vs-request-context-helpers` (File
  `rest_framework/hook_context.py` R6) on fresh evidence: that module owns
  frozen hook-argument records (`SerializerHookContext`, `UploadMetadata`)
  handed to consumer code; this module owns shape-agnostic key access over
  Strawberry `info.context` with no record shape and no hook surface. The
  shared token is the English word "context". Trigger: none foreseeable
  (disjoint domains).
- **R2 — info→request decoding.** `utils/permissions.py::request_from_info`
  resolves request IDENTITY from `info` (attribute/mapping/Channels shapes,
  `ChannelsRequestAdapter`, raises `ConfigurationError` naming
  `family_label`); this module stores opaque KEYS on an already-resolved
  context and never touches `info` (info-agnostic by contract: callers pass
  `getattr(info, "context", None)`). Opposite failure postures (fail-loud
  vs fail-closed/bounded-default) prove distinct contracts. Trigger: a spec
  unifying request resolution with key storage.
- **R3 — frame-routed optimizer access.** `optimizer_value` /
  `stash_for_optimizer` are not second read/write definitions: outside a
  managed execution they delegate to F1/F2; inside one they route to the
  lease-gated execution frame (nested-operation isolation), a routing rule
  this module has no surface for. Single call path each, composing by name.
  Trigger: a second frame-routing consumer duplicating the
  frame-vs-context branch.
- **R4 — canonical container reads.** `utils/canonical.py` reads consumer
  containers through interpreter base slots for fingerprint walks and
  REFUSES non-built-ins with `ConfigurationError`; this module reads one
  key off a Strawberry context through the context's own access modes and
  answers `default` on a miss. Refuse-vs-default and
  iterate-vs-key-access are disjoint contracts. Holds at both states of
  that file's concurrent `truth` migration. Trigger: a fingerprint walk
  over `info.context` itself.
- **R5 — sibling absent-sentinels.** `finalizer.py::_MISSING_CLASS_MEMBER`,
  `utils/querysets.py::_ATTR_MISSING`, `utils/relations.py::_MISSING`
  (HEAD-confirmed; `converters.py::_MISSING` is worktree-only concurrent
  dirt) are private per-module markers with distinct lifetimes; merging
  them with public `MISSING` would couple the round-trip identity to
  unrelated internals. `MISSING` is public exactly because the restore
  decision (`clear` vs `re-stash`) crosses a module boundary. Trigger: a
  cross-module identity check against one sentinel.
- **R6 — per-family key-set clears.** `clear_optimizer_context` /
  `clear_resource_context` each loop their own `DST_*` vocabulary through
  F3. The vocabularies and call points differ (start-of-execution reset vs
  budget teardown); the shared mechanism (per-key delete) is already
  composed by name, and the residual two-line loop is below the
  machinery bar. Trigger: a third family clearing a key set with identical
  boundary semantics.
- **R7 — `None`-tolerant call shape.** The `getattr(info, "context", None)`
  call sites are consumers of the helpers' `None` contract, not a
  restatement: hoisting `info` into the helpers would break their
  info-agnostic shape contract (R2). Trigger: a call site branching on
  `None` itself instead of passing it through.
- **R8 — per-helper dispatch guards.** The `if context is None` guard and
  the `if not isinstance(context, dict)` guard are spelled once per helper
  (3×). Counted 3 under "change the `None`/dict contract", but each guard
  encodes its helper's own return contract (default-value vs effect-skip;
  getattr vs setattr vs delattr bodies), all co-located in one 238-line
  module with per-helper docstrings and oracles. Unifying them needs a
  return-parametrized predicate — machinery that obscures ownership.
  Trigger: a `None`/dict-semantics change landing on a strict subset
  (divergence proof), or a fourth spelling.

## Defects

None. The concurrent-external `get_context_value` hunk is a coherent
behavior change (code + docstring + oracle move together across the two
states); its landing decision belongs to its author, not this item. No
guard gap (axis 6), no docstring/body contradiction, no bypass writer.

## Pending execution

None. Read-only trace; no `proof:` owed. Sharded/PG cells inapplicable by
construction: the target performs no database, alias, or dialect decision
(pure in-memory dispatch over a caller-held object).

## Judgment

Zero-edit file item. `utils/context.py` already owns its rule once: every
consumer composes the four helpers by name, the round trip and its
sentinel are single-sited, and the eight considered second sites each
carry a recorded contract difference (one converge, seven fresh). No
family item owed, no consolidation, no defects. The one dirty hunk is
attributed concurrent-external by content (no ledger row; byte-identical in
the item baseline) and traced at HEAD bytes.

## Index rows for Worker-0

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `request-context-read-dispatch` | `django_strawberry_framework/utils/context.py::get_context_value` | `django_strawberry_framework/utils/context.py` | File `utils/context.py` | file-local |
| `request-context-write-dispatch` | `django_strawberry_framework/utils/context.py::stash_on_context` | `django_strawberry_framework/utils/context.py` | File `utils/context.py` | file-local |
| `request-context-delete-dispatch` | `django_strawberry_framework/utils/context.py::clear_context_key` | `django_strawberry_framework/utils/context.py` | File `utils/context.py` | file-local |
| `request-context-round-trip` | `django_strawberry_framework/utils/context.py::restored_context_keys` (+ `MISSING`) | `django_strawberry_framework/utils/context.py` | File `utils/context.py` | file-local |
| `request-context-module-mechanics` | `django_strawberry_framework/utils/context.py` (docstring, imports, `__all__`) | `django_strawberry_framework/utils/context.py` | File `utils/context.py` | file-local |
| `hook-context-vs-request-context-helpers` | `django_strawberry_framework/rest_framework/hook_context.py` (CONVERGE with the verified rejection on fresh evidence; see R1) | `django_strawberry_framework/rest_framework/hook_context.py`, `django_strawberry_framework/utils/context.py` | File `utils/context.py` | rejected |
| `request-context-vs-request-identity-decode` | `django_strawberry_framework/utils/context.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/context.py`, `django_strawberry_framework/utils/permissions.py` | File `utils/context.py` | rejected |
| `request-context-vs-frame-routed-access` | `django_strawberry_framework/utils/context.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/context.py`, `django_strawberry_framework/optimizer/_context.py` | File `utils/context.py` | rejected |
| `request-context-vs-canonical-reads` | `django_strawberry_framework/utils/context.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/context.py`, `django_strawberry_framework/utils/canonical.py` | File `utils/context.py` | rejected |
| `request-context-vs-sibling-absent-sentinels` | `django_strawberry_framework/utils/context.py::MISSING` (rejection recorded here; fresh set, no prior verdict) | `django_strawberry_framework/utils/context.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/utils/querysets.py`, `django_strawberry_framework/utils/relations.py` | File `utils/context.py` | rejected |
| `request-context-vs-key-set-clears` | `django_strawberry_framework/utils/context.py::clear_context_key` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/context.py`, `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/resource_policy.py` | File `utils/context.py` | rejected |
| `request-context-none-call-shape` | `django_strawberry_framework/utils/context.py` (rejection recorded here; fresh idiom, no prior verdict) | `django_strawberry_framework/utils/context.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/resource_policy.py`, `django_strawberry_framework/utils/permissions.py` | File `utils/context.py` | rejected |
| `request-context-per-helper-dispatch-guards` | `django_strawberry_framework/utils/context.py` (rejection recorded here; fresh, no prior verdict) | `django_strawberry_framework/utils/context.py` | File `utils/context.py` | rejected |

Freshness fingerprints (`git hash-object` = worktree, `git rev-parse
HEAD:` = HEAD; dirty-file claims verified against HEAD bytes as noted):

| Input | Worktree | HEAD | State |
|---|---|---|---|
| `utils/context.py` (target) | `edebf0ea` | `cd0adcc5` | DIRTY, traced at HEAD; worktree = item-baseline blob |
| `optimizer/_context.py` | `dbc30630` | `dbc30630` | CLEAN |
| `resource_policy.py` | `cc3f9d80` | `4b69e974` | DIRTY, cited lines HEAD-identical (import + 6 call sites) |
| `extensions/resource_policy.py` | `0134d83a` | `19e2309d` | DIRTY, cited lines HEAD-identical (import + restore block) |
| `optimizer/extension.py` | `39a8739c` | `e0e53a8e` | DIRTY, cited lines HEAD-identical (re-export + `_stash_union`) |
| `utils/permissions.py` | `1c9cfd39` | `9889d6fe` | DIRTY, `request_from_info` contract read at HEAD bytes |
| `utils/canonical.py` | `ce7f40f4` | `b9ded33b` | DIRTY, refuse-vs-default contract holds at both states |
| `rest_framework/hook_context.py` | `646377d9` | `646377d9` | CLEAN (excluded on body) |
| `types/resolvers.py` | `640905c6` | `72d62dc4` | DIRTY, cited lines HEAD-identical (import + 6 read sites) |
| `types/finalizer.py` | `b9d8acb2` | `de34ae2a` | DIRTY, sentinel read at HEAD bytes |
| `types/converters.py` | `f6cadb08` | `058f1081` | DIRTY, `_MISSING` worktree-only (not cited) |
| `utils/querysets.py` | `8fc556d5` | `3616927d` | DIRTY, sentinel read at HEAD bytes |
| `utils/relations.py` | `05ff55b0` | `8dbc3fe6` | DIRTY, sentinel read at HEAD bytes |
| `tests/utils/test_context.py` | `004b76d5` | `a31eaf2f` | DIRTY, both oracle states cited explicitly |
| `tests/optimizer/test_extension.py` | `8b3e2e1c` | `912cd47f` | DIRTY, both named pins present at both heads |
| `tests/test_resource_policy.py` | `585c536e` | `9206e812` | DIRTY, comment cite only |
| `test_query/test_extension_isolation_api.py` | `2744212c` | `2744212c` | CLEAN |
| `test_query/test_list_field_api.py` | `4c85f779` | `4c85f779` | CLEAN |
| `test_query/test_list_field_async_api.py` | `49e423ea` | `49e423ea` | CLEAN |

## Independent verification (Worker-2)

Expectations recorded before reading `## Findings` (from the target,
the item-scoped diff, and system-wide consumer/projection reads only).
Target read whole at worktree bytes; HEAD bytes via `git show HEAD:`.

Own trace. `ast.Module.body` = 12 statements (module docstring, 4
imports, `__all__`, `MISSING` + its docstring, 4 function defs). I
expected 7 homes: the read rule (`get_context_value`: `None`
short-circuit, dict-first `.get`, getattr-first with `MISSING`
fall-through to `context[key]`, narrow miss tuple), the write rule
(`stash_on_context`: dict guard, setattr-first catch-and-chain to one
mapping tail, frozen silently skipped), the delete rule
(`clear_context_key`: mirrors the write dispatch, no `.pop()` fast
path), the round trip (`restored_context_keys` + public `MISSING`),
the `__all__` manifest, and the module-docstring shape taxonomy.
Definitions: all in the target, one each. Consumers composing by
name: `optimizer/_context.py` (imports 3, re-exports 2, builds the
frame-routing adapters on top), `resource_policy.py`,
`extensions/resource_policy.py` (`restored_context_keys`),
`optimizer/extension.py` (private alias), `types/resolvers.py`
(transitive via `optimizer_value`). Oracles:
`tests/utils/test_context.py`, the two named pins in
`tests/optimizer/test_extension.py`, `tests/test_resource_policy.py`,
live `test_query/` suites. Owner for every rule: the target itself;
expected zero families.

Reconciliation. Every expectation matches: W1's F1–F5 home all 12
members into the same 7 I posited, with the same sites, roles, and
owners. No difference to reconcile.

Judgment 1 — enumeration completeness. STANDS. Independent AST count
is 12 with the identical member list; F1–F5 cover all 7 homes
(module docstring + imports/`__all__` → F5, `MISSING` →
F4, 4 functions → F1/F2/F3/F4). HEAD bytes carry the same 12: the
dirty hunk is intra-`get_context_value` only.

Judgment 2 — hunk attribution. STANDS, re-verified by content.
`git diff 1c3c6220 -- <target>` is empty (baseline blob =
`edebf0ea` = worktree blob); HEAD blob `cd0adcc5`; exactly one `@@`
hunk, 9+/20- excluding diff headers, inside `get_context_value`
(broad `except Exception` → `(KeyError, TypeError, AttributeError)`
plus getattr-`try` removal plus docstring rewrite). No
`## Owned changes` ledger row names the target (ledger spans plan
lines 1073–1137; the sole `context.py` hit nearby is run-history
prose). Concurrent-external on both attribution tests. The oracle
pair moves coherently: HEAD pins the two hostile fail-closed tests,
the worktree pins the propagation test.

Judgment 3 — rejections R1–R8, each probed independently.
R1 STANDS: the `hook-context-vs-request-context-helpers` rejection
exists in the verified File `rest_framework/hook_context.py`
artifact (R6 + index row + W2 endorsement) with the same contract
difference (shared token is the English word "context") and trigger
(none foreseeable); current `hook_context.py` read fresh (two frozen
dataclasses, no shape dispatch, no hook surface over `info.context`)
— disjoint on fresh evidence. R2 STANDS: `request_from_info` read
at HEAD bytes — resolves request identity, Channels shapes,
raises `ConfigurationError`; target never touches `info`. R3
STANDS: `optimizer_value` / `stash_for_optimizer` delegate to F1/F2
outside a frame and route to the lease-gated frame inside —
routing, not a second dispatch. R4 STANDS: `canonical.py` reads
built-ins through interpreter base slots and refuses the rest with
`ConfigurationError` at both states (worktree `truth` migration
confirmed in the body). R5 STANDS: `querysets.py::_ATTR_MISSING`,
`relations.py::_MISSING`, `finalizer.py::_MISSING_CLASS_MEMBER`
confirmed at HEAD bytes; `converters.py::_MISSING` confirmed
worktree-only (absent at HEAD) and correctly excluded; `MISSING`'s
publicity rationale verified (`__all__` + cross-module restore
decision + the extension's migration comment). R6 STANDS: both
clears loop their own `DST_*` vocabulary through F3 by name
(`clear_optimizer_context` called from the optimizer's `on_execute`;
`clear_resource_context` exported and oracle-exercised). R7 STANDS:
5 code sites + the target docstring = the claimed 6; all pass
`None` through to the helpers' contract. R8 STANDS: the 3× guards
confirmed in the source; counted 3 with a machinery-bar rejection
(shared predicate over divergent return contracts — default-value
vs effect-skip, getattr vs setattr vs delattr tails) and a
divergence trigger. Ten of ten freshness fingerprints recomputed
and matching; artifact blob and HEAD stable across the pass.

Judgment 4 — zero families / zero defects. STANDS. No second
definition exists for any of the 7 homes; the
`setattr`/`delattr`/`del context[` sweep finds no bypass writer;
axis 6 verified against the source (locked-`QueryDict`
`AttributeError` arm present on write AND delete); no
docstring/body contradiction at the traced HEAD bytes
(`except Exception` + "BaseException not swallowed" cohere);
sharded/PG inapplicable-by-construction reason holds (pure
in-memory dispatch, no database/alias/dialect decision). Item-scoped
diff is empty, so no prose-rule or ruff gate applies to source.

Observations (record-accuracy nits, none verdict-affecting, no
revision demanded). O1 (Worker-2): matrix axis 2 says the sole
`restored_context_keys` consumer "wraps a synchronous `on_execute`
scope" — the method is `on_operation` (sync `def`, confirmed); the
inapplicability reason itself is correct. O2 (Worker-2): R6's
"call points differ (start-of-execution reset vs budget teardown)"
gloss — the optimizer side is confirmed at its `on_execute` call
site; the resource side has no in-package caller (exported +
oracle-exercised). The rejection rests on distinct vocabularies over
an already-composed mechanism and does not hinge on the gloss. O3
(Worker-2, for Worker-0): the converged-upon
`rest_framework/hook_context.py` target drifted since its run-6
verification (`f4910159` → `646377d9`); per the freshness rule that
item's finding reopens for Worker-0 to disposition — this item's R1
rests on fresh evidence and is unaffected.

Verdict: `Status: verified`. Zero-edit file item stands as traced.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[optimizer-_context]: ../../django_strawberry_framework/optimizer/_context.py
[target]: ../../django_strawberry_framework/utils/context.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
