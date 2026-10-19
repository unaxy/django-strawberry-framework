# DRY review: `relay-node-type-stamp`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `relay-node-type-stamp`. Provisional split ownership
(`types/relay.py::_NODE_TYPE_HINT_ATTR` + `::install_is_type_of` vs
`relay.py::_stamp_node_type`) — REJECTED as a consolidation: the split is
correct, decided below with proof. Member files:
`django_strawberry_framework/types/relay.py`,
`django_strawberry_framework/relay.py`. Prior records only as triggers: the
relay file item (F9 named the split — every edge below re-derived from the
body, nothing inherited) and the target-guard item (type-stamp named as seam —
verified, not inherited). Never read any `worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds one row on
`relay.py` (Family `typed-globalid-decode`, `decode_model_global_id`
docstring clause) — confirmed by content (`git diff HEAD --
django_strawberry_framework/relay.py` shows exactly that 5-line clause and
nothing else). `types/relay.py` is byte-identical to HEAD and to
`ITEM_BASELINE` before this item's edit (no ledger row, no external hunk).
`ITEM_BASELINE` `f996ed1150f20570f7c363f7b8434d9e3707d1dd` verified present
via `git cat-file -t`. The one tracked edit lands on clean
`types/relay.py`; `relay.py` untouched. Reading the dirty files was free.

## System trace

Rule: how a resolved object proves which Relay type it is. For a model with
two registered Relay types, plain `isinstance(obj, (type_cls, model))`
answers `True` on both candidates and graphql-core's candidate-iteration
order picks the `__typename` — regardless of which type the GlobalID named.
The root refetch fields therefore stamp the decode-resolved `DjangoType` on
each fetched instance, and the installed `is_type_of` honors that stamp
before its isinstance fallback, so `__typename` follows the type the
GlobalID named (contract source: [spec-032][spec-032] Decision 4, verified
against both bodies).

What each site does (each re-derived from its body):

- **Attribute contract** ([relay-types][relay-types]`::_NODE_TYPE_HINT_ATTR`
  = `"_dsf_node_type_hint"`): the one name both halves compose. Package-wide
  the literal occurs exactly once (the assignment); the stamp writes through
  the imported name, never a re-spelled string.
- **Honor** ([relay-types][relay-types]`::install_is_type_of` closure):
  hint-first (`hinted is type_cls`), isinstance fallback
  (`isinstance(obj, (type_cls, model))` — the upstream borrow, verified
  against `strawberry_django/type.py #"if \"is_type_of\" not in
  cls.__dict__"`: same `__dict__` discriminator preserving a
  consumer-declared `is_type_of`, same isinstance shape; the upstream
  `get_strawberry_type_cast` branch stays omitted per the docstring, and the
  hint-first branch is the new spec-032 arm). Installed at class-creation
  time for every `DjangoType` ([types-base][types-base] line 827). A hostile
  hint descriptor falls back to isinstance (oracle-pinned).
- **Stamp** ([root-relay][root-relay]`::_stamp_node_type`): copy-then-set,
  best-effort. `None` passes through; model instances are shallow-copied so
  a reused ORM object keeps no routing hint; a copy-rejecting or
  attribute-rejecting return stays unstamped and keeps the isinstance
  behavior. Async sibling `_await_and_stamp` shares the body by call, not
  by copy. Four stamp call sites: single sync tail, single async tail (via
  the sibling), batch sync loop, batch gather loop.
- **Callers of honor**: every `DjangoType` via `__init_subclass__`
  (construction phase). **Callers of stamp**: both root refetch resolvers
  only (execution phase). Relation resolvers and consumer resolvers never
  stamp — unstamped instances keep the pre-032 behavior by contract, not
  by gap.

Connected sources read: [relay-types][relay-types] (full),
[root-relay][root-relay] (full), [types-base][types-base] (install site +
`_is_relay_shaped` neighbor), both oracle files, [spec-032][spec-032]
Decision 4, upstream `strawberry_django/type.py` borrow site,
[target-guard][target-guard] + [typed-decode][typed-decode] (seams).
Excluded on strength of body: every other package module (zero rule
vocabulary over the whole-package sweep for the stamp/honor tokens;
`optimizer` "hints" share the English word only).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Only the root refetchers stamp;
   connection/list/relation resolvers never stamp (verified by sweep: zero
   `_stamp_node_type` / hint-literal occurrences outside the two member
   files). No sibling flavor mirrors the rule. Trigger: a stamper outside
   the root fields.
2. **Sync/async twins.** `_stamp_node_type` vs `_await_and_stamp`: the
   latter awaits then calls the former by name — one body, two colors. The
   single/batch sync/async tails differ only in color duties (await point,
   `reject_async_in_sync_context` on sync only). No drift possible: one
   stamp body exists.
3. **Derived rather than repeated knowledge.** The attribute NAME derives
   once (the constant); both halves read it (honor direct, stamp via
   import). The literal is spelled once package-wide. The VALUE convention
   (store the resolving type; compare by `is`) is spelled in two bodies —
   see C2: inverse halves, each single for its direction.
4. **Inverse / round-trip pairs.** Stamp (type → instance, execution phase)
   vs honor (instance → verdict, per-resolve read of a
   construction-installed closure) are opposite directions of one
   lifecycle, sharing one grammar (the attribute constant). They meet only
   in the multi-type `__typename` verdict. Kept as two halves composing
   one owner by name — the finding.
5. **Contracts restated in another medium.** Production (attribute +
   closure + stamp); oracles (independent wire-literal rows: multi-type
   `__typename` ×2, isolation, passthrough ×2, injected/preserved/hostile
   `is_type_of` — never reading the owner constant except three
   `hasattr` literal spells, listed not counted); projections (both
   docstrings cross-name the other half accurately; spec-032 Decision 4).
6. **Enforcement by omission.** Unstamped instances (relation/consumer
   resolvers, `None`, unstampable returns) fall back to isinstance — the
   documented contract with a contract source (spec-032), not a gap. No
   member lacks the behavior its contract requires: no defect.

### Enumeration

Instrument: whole-package sweep for `_NODE_TYPE_HINT_ATTR |
_dsf_node_type_hint | _stamp_node_type | _await_and_stamp |
install_is_type_of` + `def` census per symbol. Population: 117 `.py`
(plan count; no adds/renames).

- `_NODE_TYPE_HINT_ATTR`: 1 def ([relay-types][relay-types]:75); 1 literal
  occurrence package-wide (the assignment); 1 import
  ([root-relay][root-relay]:68); 2 name reads (honor closure, stamp body).
- `install_is_type_of`: 1 def; 1 production caller
  ([types-base][types-base]:827, every `DjangoType`); honor branch 1 site.
- `_stamp_node_type`: 1 def; `_stamp_node_type(` occurrences = 5 (def +
  4 call sites: sibling body, single sync tail, batch sync loop, gather
  loop); `_await_and_stamp`: 1 def, 1 call site (single async tail).
- Oracles: `test_bare_node_field_multi_type_model_typename_follows_gid`,
  `test_bare_nodes_field_multi_type_model_typenames_follow_gids`,
  `test_node_type_hint_does_not_poison_reused_model_instance`,
  `test_stamp_node_type_passes_through_none_and_unstampable_objects`,
  `test_stamp_node_type_returns_a_model_instance_that_rejects_copying`,
  `test_is_type_of_injected_for_all_djangotypes`,
  `test_consumer_declared_is_type_of_is_preserved`,
  `test_is_type_of_hostile_hint_descriptor_falls_back_to_instance_check`.
  All use independent literals (package oracles
  [test-relay-node-field][test-relay-node-field] +
  [test-relay-interfaces][test-relay-interfaces]).

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace proofs map onto the
behavioral rows (8-test selection `execution-verified` in the copy and in
the shared tree; both mutants `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Rename the attribute (e.g. `_dsf_node_type`) | **1** (`_NODE_TYPE_HINT_ATTR`; the import, the honor read, and the stamp write follow by name; 3 test-literal `hasattr` spells listed as oracles). |
| C2 | Second hint scheme, or a stored value beyond the resolving type (pair/payload instead of the type) | **1** grammar def (the name) + both directional halves move as consumers (stamp `setattr` spell, honor `is` spell — each the single site for its direction; cf. `_emits_model_label` / `_accepts_model_label_decode`: identical bodies kept as two names for opposite halves). No third body spells the value. |
| C3 | A type that resolves without the stamp (unstamped instance) — fallback or loud? | **0** move: fallback IS the contract (honor lines 121-123; spec-032 pins pre-032 isinstance for unstamped; unit rows pin `None`/unstampable passthrough). |

## Findings

### F1 — node type routing stamp/honor (REJECTED consolidation: split correct, single grammar)

- **Contract + variation.** The decode-routing decision carried into
  abstract-type resolution: stamp the resolved `DjangoType` on the fetched
  instance (copy-then-set, best-effort), honored before the isinstance
  fallback. No legitimate variation in attribute or precedence; the value
  is always the resolving type; unstamped always falls back.
- **Sites + roles.** *Grammar definition*: `_NODE_TYPE_HINT_ATTR` (1 def,
  1 literal). *Honor half*: `install_is_type_of` closure (1 site).
  *Stamp half*: `_stamp_node_type` + `_await_and_stamp` by call (1 body,
  4 call sites). *Installer*: `types/base.py:827` (enforcement site,
  construction phase). *Oracles / projections*: as listed.
- **Challenges.** C1 → 1; C2 → 1 grammar + 2 directional halves (each
  single for its direction); C3 → 0 (fallback is the contract). Count > 1
  nowhere in one rule.
- **Owner + lifetime (principles 7, 4).** The attribute site owns the
  contract: both halves already compose it by name, and every `is_type_of`
  reader depends on `types/relay.py` while only the root refetchers read
  decode routing. Moving the stamp beside the attribute would drag
  root-field decode routing (`decode_global_id`, slot coercion, copy
  semantics) into the type-construction foundation and risk the load cycle
  the module already dodges with in-function imports; moving the honor
  beside the stamp would make every `DjangoType`'s construction depend on
  the root-field module (`types/base.py` → `relay.py` → `list_field.py`
  — reversed). Dependency direction wins: stamp stays in
  [root-relay][root-relay] (execution phase, decode owners), honor stays
  in [relay-types][relay-types] (construction-installed, per-resolve
  read). Lifetime: per-instance hint, published at resolve
  (copy-then-set), valid for the response only (the copy prevents
  cross-field leak — oracle-pinned), read per abstract-type resolution,
  mutated by no one (no deleter; overwrite-only by a later stamp on the
  same in-place non-model object, best-effort by contract).
- **Migration.** None — already single. One comment trigger clause at the
  attribute owner (projection; behavior identical — AST-identity proof
  below).
- **Distinct behavior (stays separate).** Consumer-declared `is_type_of`
  preserved via the `__dict__` discriminator (upstream borrow); hostile
  hint descriptor → isinstance fallback; `None`/uncopyable/unstampable →
  passthrough; unstamped → pre-032 isinstance. The sibling
  `_RELAY_ID_ATTR_SLOT` / `_stamp_relay_id_attr` pair shares the English
  word "stamp" only: it pins the id COLUMN per class at finalize, this
  family pins the resolving TYPE per instance at resolve — different
  inputs, timing, lifetime, readers. Trigger: an id-attr read honoring a
  routing hint or vice versa.
- **Behavioral proof.** `execution-verified` (WS 8 passed + authorized
  shared-tree 8 passed, zero member edits in flight). Mutant B
  (stamp writes a wrong attr): 3 multi-type rows fail — standing oracles
  pin the shared attribute (failability proved). Mutant A (correct
  hand-copy inlined at the single tail, owner unbypassed elsewhere):
  8 passed — no behavioral gate can pin call-unity (proved negative
  control). `static-reviewed` for import identity, oracle independence,
  prose accuracy.
- **Structural gate.** None owed, with proved reason: every divergence
  that changes observable behavior (dropped stamp, dropped honor,
  re-spelled attribute) fails the standing multi-type oracles (mutant B);
  the one divergence no behavior oracle can catch (call-unity bypass,
  mutant A) would need a bespoke per-helper existence test, which
  [DRY.md][dry] forbids for gate-only findings. Same standard as the
  verified typed-decode, name-decode, target-guard, and
  subscription-masking items. Unity rests on the def/caller census +
  triggers T-attr / T-value / T-lifecycle below; correctness of each arm
  rests on the standing rows (which fail a lost/weakened arm).
- **Coupling.** None. Adjacent families untouched; the clause is
  comment-only.
- **Freshness.** Blob ids below. Any fingerprint change reopens.
- **Reconsideration triggers (recorded at the owner).** T-attr fires on a
  second hint scheme or rename (the constant owns the name); T-value
  fires on a stored value beyond the resolving type (re-opens the
  `setattr`/`is` spells on both halves); T-lifecycle fires on stamping
  before decode or a stamper outside the root fields (re-opens stamp
  ownership). Durable homes: the new comment clause on
  [relay-types][relay-types]`::_NODE_TYPE_HINT_ATTR`, this finding, and
  the plan's `## Outcomes` via Worker 0.

## Defects

None new. Spot-checks that could have been defects all hold: the honor
closure reads the hint through the module constant (not a re-spelled
literal — package literal count is 1); the stamp copies only model
instances and stamps in place otherwise, which matches the documented
best-effort contract (the uncopyable/unstampable unit rows pin both
arms); no deleter or second writer of the hint exists; relation and
consumer resolvers are unstamped by contract (spec-032), not by omission.
No `## Owned changes` coupling (comment-only edit).

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace; the one authorized shared-tree focused run executed green
(8 passed) with zero member edits in flight. No `execution-deferred`
items. `FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by
construction`: every executed claim is construction-time injection plus
default-DB single-alias ORM reads (the recorded `NAME` is the copy's own
file). Full-suite gate business is deferred to the final-gate item with
reason: the entry authorizes workspace runs plus one focused `--no-cov`
test, and a green unmutated suite would discharge no failability proof
for a confirmation that proposes no gate.

## Judgment

Stamp (write at resolve) and honor (read per resolve) are two halves of
one rule with one grammar: `_NODE_TYPE_HINT_ATTR` owns the attribute
(C1 → 1, C2 → 1 grammar, C3 → 0). Consolidating the halves into one
module would reverse the dependency the tree already observes
(foundation ← root fields), so the split stands — rejected with
difference + triggers + home, one projection-only clause at the owner,
no defects.

## Implementation (Worker 1)

Tracked change (1 file, comment-only):
`django_strawberry_framework/types/relay.py` — `_NODE_TYPE_HINT_ATTR`
comment gains the T-attr / T-value / T-lifecycle reconsideration-trigger
clause (projection; behavior untouched). Attribution: `types/relay.py`
clean at `ITEM_BASELINE` and at HEAD before the edit; no `## Owned
changes` row exists on the path; `relay.py` hunks attributed above and
untouched. Worker 0 appends: `django_strawberry_framework/types/relay.py`
— Family `relay-node-type-stamp` — `_NODE_TYPE_HINT_ATTR` comment trigger
clause (projection; behavior untouched).

Item-scoped diff: `git diff
f996ed1150f20570f7c363f7b8434d9e3707d1dd --
django_strawberry_framework/types/relay.py
django_strawberry_framework/relay.py` shows exactly the +8 comment lines
on `types/relay.py` and nothing on `relay.py`.

Proofs (disposable workspace per [DRY.md][dry] "Tests"; `rsync` copy,
docs excluded; every command via `uv run --frozen --directory "$WS"` —
run here as `uv run --directory "$WS"`, the copy's own lockfile):

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-node-type-stamp-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" pytest <8-test selection> --no-cov -n0 -q
```

Copy `__file__`:
`.../dry-ws/relay-node-type-stamp-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/relay-node-type-stamp-w1/examples/fakeshop/db.sqlite3`
(the copy's own tree and database). Behavioral selection (8 passed in the
copy; 8 passed shared-tree, zero member edits in flight):
`test_bare_node_field_multi_type_model_typename_follows_gid`,
`test_bare_nodes_field_multi_type_model_typenames_follow_gids`,
`test_node_type_hint_does_not_poison_reused_model_instance`,
`test_stamp_node_type_passes_through_none_and_unstampable_objects`,
`test_stamp_node_type_returns_a_model_instance_that_rejects_copying`,
`test_is_type_of_injected_for_all_djangotypes`,
`test_consumer_declared_is_type_of_is_preserved`,
`test_is_type_of_hostile_hint_descriptor_falls_back_to_instance_check`.
Negative control A (same workspace, pristine backup kept, restored
byte-identical via `cmp` and re-verified): bypass mutant inlining a
correct hand-copy of the stamp body at the single tail → selection still
8 passed. Failability mutant B (stamp writes a wrong attr): 3 multi-type
rows fail exactly (candidate-order `__typename`), then restored
byte-identical. No source mutation remains in the copy; the control
backup was removed after restore.

After the edit: `uv run ruff check --fix
django_strawberry_framework/types/relay.py` + `uv run ruff format
django_strawberry_framework/types/relay.py` — both green (`format --check`
+ `check` pass on the path; scoped to the path so no concurrent dirt is
rewritten). INVERSE proof (comment-only edit): AST of
`HEAD:types/relay.py` vs worktree — identical including docstrings
(comments are not AST nodes). Per `AGENTS.md` no pytest after edits; the
pre-edit focused run (8 passed) still discharges the finding by that AST
identity. No `CHANGELOG.md` touch. No commit per standing rule.

Scratch paths (removal is Worker 0's, after `verified`, by explicit path):
`WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-node-type-stamp-w1`
(includes its own `.venv`; the control backup was removed after restore).
No manifest (no `prove_failability.py` run — no gate added, none owed; the
hand-proved mutants are the controls). This artifact
`docs/dry/dry-rule-relay-node-type-stamp.md` is the item's new file.

Worker 0 rows: tick Family `relay-node-type-stamp` (this artifact); no
`## Responsibility index` change needed beyond `open` → decided per the
finding above (provisional split owner + both member files already
covered); append the `## Owned changes` row above; no defects to home.

Freshness fingerprints (`git hash-object` worktree unless noted; HEAD
`bfaee91d`; `ITEM_BASELINE` `f996ed1150…` present):
`types/relay.py` `c333c785…` post-clause (HEAD `52439862…`; delta = +8
comment lines only), `relay.py` `69085e7a…` (ledgered decode clause;
stamp/honor lines outside it), `types/base.py` `91c58747…` (= HEAD,
clean), `tests/test_relay_node_field.py` `2fd9e458…`,
`tests/types/test_relay_interfaces.py` `26fb2ccf…`,
`docs/SPECS/spec-032-full_relay-0_0_9.md` `1e96ad41…`,
`docs/dry/dry-0_0_15.md` `24b56ea9…`, `docs/dry/dry-file-relay.md`
`191ba3c7…`, `dry-rule-relay-node-target-guard.md` `5f4b74f3…`,
`dry-rule-typed-globalid-decode.md` `7743927f…`. Searched population:
whole package (117 `.py`) for the stamp/honor tokens. Any fingerprint
change reopens the finding.

## Independent verification (Worker 2)

Recorded before reading `## Findings` (independent re-derivation from the
bodies at HEAD `bfaee91d` + worktree; Worker 1's sections above unread
except the append anchor).

- **Attribute contract.** `django_strawberry_framework/types/relay.py::_NODE_TYPE_HINT_ATTR`
  = `"_dsf_node_type_hint"` (worktree line 83). One grammar: my package-wide
  census finds exactly 1 occurrence of the string literal in package source
  (the assignment); zero f-string/dynamic builds (a `dsf_node` sweep outside
  the literal and the symbol name returns nothing). Every other site composes
  by name: `relay.py:68` imports the constant (`from .types.relay import
  _NODE_TYPE_HINT_ATTR, decode_global_id`), `types/relay.py:123` reads it
  (`getattr(obj, _NODE_TYPE_HINT_ATTR, None)` inside a hostile-descriptor
  `except`), `relay.py:435` writes it (`setattr(node, _NODE_TYPE_HINT_ATTR,
  resolved_type)`). Test-file spellings of the literal (`hasattr` asserts in
  `tests/test_relay_node_field.py`, one name comparison in
  `tests/types/test_relay_interfaces.py`) are oracles, not definitions.
- **Stamp sites.** `django_strawberry_framework/relay.py::_stamp_node_type`
  (def line 403): `None` passes through; the decode-resolved `DjangoType` is
  set on a `copy.copy` of the node when the node is an instance of the
  resolved type's model (copy failure returns the node unstamped);
  `setattr` is best-effort (`contextlib.suppress(AttributeError)`), so a
  `__slots__`/non-model object from a consumer override falls back to
  pre-032 behavior. `::_await_and_stamp` (lines 439-441) is the async sibling
  sharing the stamp by call (`return _stamp_node_type(resolved_type, await
  awaitable)`). Call sites (4): line 441 (inside `_await_and_stamp`), line
  507 (`DjangoNodeField` single), lines 605 and 622 (`DjangoNodesField`
  async-gather and sync branches). 5 occurrences total = 1 def + 4 calls.
- **Honor sites.** `django_strawberry_framework/types/relay.py::install_is_type_of`
  (def line 86): closure reads the hint first (`hinted is type_cls`) and
  falls back to `isinstance(obj, (type_cls, model))` — the upstream borrow
  (same `cls.__dict__` discriminator preserving a consumer-declared
  `is_type_of`, same isinstance shape as `strawberry_django/type.py`
  `_process_type`). Installed per-`DjangoType` at
  `django_strawberry_framework/types/base.py:827` (`install_is_type_of(cls)`
  at the end of the type-creation pipeline; the module imports it top-level
  at `types/base.py:64`).
- **Definition counts.** C1 (rename the attribute): 1 — the
  `_NODE_TYPE_HINT_ATTR` assignment; import, honor read, and stamp write
  follow by name. C2 (a second hint scheme): 1 grammar + 2 directional
  halves — stamp and honor are distinct decisions (decode-routing write vs
  concrete-type-selection read) sharing one name, not two definitions of one
  rule. C3 (an unstamped instance): 0 — the isinstance fallback IS the
  contract ([spec-032][spec-032] Decision 4: unstamped relation/consumer
  resolvers keep pre-032 behavior exactly), so absence is not a second
  definition and not an enforcement gap.
- **Owner I would choose: SPLIT stays.** Grammar owner
  `types/relay.py::_NODE_TYPE_HINT_ATTR`; stamp stays in root `relay.py`
  (it reads decode routing only the root refetchers own); honor stays in
  `types/relay.py` (every `is_type_of` reader already depends on that
  module). Top-level import edges I traced: `types/base.py` → `types/relay.py`
  (`install_is_type_of`); `relay.py` → `types/relay.py` (constant +
  decode) and `relay.py` → `list_field.py` (target guard);
  `list_field.py` → `types/base.py`; `types/relay.py` → nothing upward at
  top level (its `.base`/`conf`/`registry` imports are all in-function,
  cycle-dodge documented at lines 377-382). Housing the attribute in
  `relay.py` would force the honor half to import upward (`types/relay.py`
  → `relay.py`), closing a `relay → list_field → types/base → types/relay`
  load cycle — the dependency-direction claim is REAL. Per principle 7,
  dependency direction wins over narrowness here; the leaf already is the
  narrowest valid owner.
- **Lifetime.** Per-instance, response-scoped: the stamp lives on the
  shallow copy of one fetched row and dies with it; no class-level storage,
  no cache, no invalidation. Stored-derivation fields: owner = the fetching
  root field call; validity = the instance copy; publish = stamp call;
  mutators = none; invalidation = garbage collection.
- **My freshness (worktree `git hash-object`, HEAD `bfaee91d`):**
  `types/relay.py` `c333c785…`, `relay.py` `69085e7a…`,
  `types/base.py` `91c58747…` (= HEAD), `list_field.py` `d6af6164…`
  (worktree; HEAD `ce682d5f…` — concurrent dirt, outside this family),
  `types/definition.py` `fa6c4d330…`, `types/finalizer.py` `77fd9a2d…`,
  `tests/test_relay_node_field.py` `2fd9e458…`,
  `tests/types/test_relay_interfaces.py` `26fb2ccf…`,
  `docs/SPECS/spec-032-full_relay-0_0_9.md` `1e96ad41…`. Searched population:
  whole `django_strawberry_framework/` tree for the four tokens. Excluded on
  body strength: `testing/relay.py` (decode/encode helpers only, no
  stamp/honor), `types/finalizer.py` relay-resolver installs (four
  `resolve_*` defaults, distinct discriminator), `connection.py` /
  `list_field.py` resolvers (unstamped by contract).

Reconciliation (Worker 2, after reading `## Findings`): agree on every
point, differ on none. Per-point:

- Grammar definition + literal-count-1: AGREE. My census matches (1
  assignment; zero builds; name-composition everywhere else). The
  Enumeration's `[relay-types]:75` label is HEAD numbering; post-edit the
  def sits at worktree line 83 — expected shift from the item's own +8,
  symbol path resolves, not a defect.
- Honor half + `types/base.py:827`: AGREE (upstream-borrow shape confirmed
  against the docstring's cited discriminator; per-`DjangoType`
  installation confirmed in the creation pipeline).
- Stamp half + `_await_and_stamp` by call, 4 sites / 5 occurrences: AGREE
  (def 403; calls 441, 507, 605, 622; sibling def 439-441 with its 1 call
  at 506).
- `relay.py:68` by-name import: AGREE.
- C1 → 1 / C2 → 1 grammar + 2 directional halves / C3 → 0: AGREE. C1's "3
  test-literal `hasattr` spells" is exact for `hasattr` (a fourth literal,
  the `==` comparison at `test_relay_interfaces.py:349`, is correctly not
  counted as `hasattr`); all four are oracles either way.
- Owner SPLIT: AGREE, and the dependency-cycle claim is REAL (traced
  myself, top-level edges only): `types/base.py` → `types/relay.py`,
  `relay.py` → `types/relay.py` + `relay.py` → `list_field.py`,
  `list_field.py` → `types/base.py`, `types/relay.py` → nowhere upward
  (its `.base`/`conf`/`registry` imports are in-function with a
  do-not-hoist note). Housing the attribute in `relay.py` forces
  `types/relay.py` → `relay.py` and closes the cycle. Dependency direction
  wins per principle 7; the leaf is also the narrowest valid owner.
- Lifetime per-instance response-scoped: AGREE.
- REJECT with triggers homed at the attribute owner (+8 clause): AGREE.
  The clause text matches F1's T-attr/T-value/T-lifecycle.
- Owner-edit judgment (ran myself): prose-only CONFIRMED —
  `ast.dump` of `HEAD:types/relay.py` == worktree (comments are not AST
  nodes); `uv run ruff format --check` + `uv run ruff check` on both
  member paths pass; `scripts/check_trailing_commas.py --check` on both
  passes; added lines max 78 chars (limit 99), ASCII-only, no code
  touched. The sibling `relay.py` +5 is a docstring clause (AST differs
  in that one Constant, behavior identical) owned by Family
  `typed-globalid-decode` — attributed, not mine to judge beyond scope.
  No pytest run by me per `AGENTS.md` (not asked); the AST identity is the
  discharge for a comment-only edit, same basis the artifact states.
- No-gate reasoning: AGREE under the mutant-A-green standard. Mutant B
  (wrong attr → 3 multi-type rows fail) proves the standing oracles pin
  the shared name; mutant A (correct copy → green) proves call-unity is
  behavior-invisible, and a unity-pinning test would be a bespoke
  per-helper existence assertion of exactly the kind [DRY.md][dry]
  forbids for gate-only findings. Same standard as the verified
  typed-decode / name-decode / target-guard / subscription-masking items.
- `## Pending execution` (none): AGREE. No `execution-deferred` proofs;
  sharded/Postgres `inapplicable by construction` accepted (no alias or
  dialect decision in the rule: construction-time injection + default-DB
  single-alias reads); full-suite gate correctly deferred to the
  final-gate item. The 8 named tests all exist at the stated paths (5 +
  3); doc fingerprints re-hashed by me match (`dry-0_0_15.md`
  `24b56ea9…`, `dry-file-relay.md` `191ba3c7…`, target-guard `5f4b74f3…`,
  typed-decode `7743927f…`).
- `AGENTS.md` prose on the diff: TWO hunks vs HEAD confirmed and both
  attributed — `relay.py` +5 (sibling `typed-globalid-decode` ledger
  row, in `ITEM_BASELINE` already) + `types/relay.py` +8 (this item);
  vs `ITEM_BASELINE f996ed11…` exactly the +8, nothing else. No process
  provenance in either clause; citations are symbol paths; no tests
  owed for a projection-only change; no `CHANGELOG.md` touch; no commit.
- Defects: AGREE (none). No (Worker 2) entries filed. Concurrent dirt
  (`list_field.py` worktree `d6af6164…` vs HEAD `ce682d5f…`, plus the
  wider `git status` dirt) carries zero rule vocabulary for this family
  and was left untouched.

Verdict: `verified`, no pending execution.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[target-guard]: dry-rule-relay-node-target-guard.md
[typed-decode]: dry-rule-typed-globalid-decode.md

<!-- docs/SPECS/ -->
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[relay-types]: ../../django_strawberry_framework/types/relay.py
[root-relay]: ../../django_strawberry_framework/relay.py
[types-base]: ../../django_strawberry_framework/types/base.py

<!-- tests/ -->
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py
[test-relay-node-field]: ../../tests/test_relay_node_field.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
