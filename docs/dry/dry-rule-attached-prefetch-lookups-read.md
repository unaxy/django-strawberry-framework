# DRY review: `attached-prefetch-lookups-read`

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

The family target is the attached-prefetch-lookups read: how plan code
reads `QuerySet._prefetch_related_lookups`. The nomination (count-2 C18
pair: `optimizer/plans.py::_consumer_prefetch_lookups` lenient live-read
plus `optimizer/walker.py::_hint_prefetch_over_pk_set` strict forward)
was re-derived at current bytes and found half-retired: committed
`f2f18ba6` ("one private module reads Django's private QuerySet state")
created `utils/_queryset_private.py::queryset_prefetch_lookups` as the
strict typed read and converted the walker site to compose it by name
(`walker.py:1544` WT, `:1537` at HEAD `23b5f421`). The walker spelling
the nomination counted is extinct. The live pair at current bytes is
the new strict owner plus the one holdout that still spells the
attribute directly: `plans.py:619` (pre-change numbering)
`list(getattr(queryset, "_prefetch_related_lookups", ()) or ())`.

What each site owns now:

- `utils/_queryset_private.py::queryset_prefetch_lookups` (`:81`, body
  `:87`) owns the strict typed read: `QuerySet` in, the stored tuple
  out. Its module docstring claims the spelling once with every caller
  going through it. Package composers: the walker hint rewrite
  (`walker.py:1544`); the seal reads its lookups-to-seal from the
  snapshot key (see R1) and writes the rebuilt state through the owner
  (`set_queryset_prefetch_lookups`, `querysets.py:3976`). The module is
  imported by 4 package modules, 12 `tests/` files and 6 live-API
  files; the lookups-helper call sites among them are 27 across 5
  test files (`test_walker` 7, `test_plans` 10, `test_extension` 3,
  `test_multi_db` 1, `test_querysets` 6) plus the walker and the seal
  in-package.
- `optimizer/plans.py::_consumer_prefetch_lookups` (`:604`) owns the
  lenient consumer read: `object` in, `list` out, `[]` for a missing
  or `None` attribute. Two in-file callers, both reconciliation:
  `_diff_prefetch_related` (`:1455`, typed `QuerySet[_M]`) and
  `_prefetch_lookup_paths` (`:1532`, `inner: object` from a
  consumer-controlled `Prefetch.queryset`, `None`-guarded by the
  caller). Zero direct test callers before this item.
- `utils/querysets.py:3902` `state.get("_prefetch_related_lookups")`
  reads the seal's instance-namespace snapshot key, not the live
  attribute; the seal rebuilds through `set_queryset_prefetch_lookups`
  (`:3976`). Excluded under its own contract (R1, the corrected C18
  exclusion re-verified).
- Django upstream (installed 6.1.2, `.venv`): `QuerySet.__init__`
  sets `self._prefetch_related_lookups = ()` (`query.py:375`) and
  every later write assigns a tuple (`:1543`, `:1848`, `:1858`,
  `:2278`, `:2435`, `:2462`, `:2464`, `:2482`, `:2922`). On a genuine
  queryset the attribute is always present and always a tuple: never
  missing, never `None`.

Dirt attribution by content (all vs `git show HEAD:`, HEAD `23b5f421`
unmoved the whole item): `plans.py` WT carries 3 hunt truth-migration
hunks (the `truth` import, `resolver_key`, `ends_in_unique_column`)
plus this item's 3 hunks; `walker.py` WT carries f56's ledgered
`target_definition=` consolidation (buildable) plus hunt `truth.*`
hunks; `_queryset_private.py` WT carries 1 hunt module-docstring hunk;
`querysets.py` WT is hunt dirt throughout. This item edits `plans.py`
target lines that are clean at HEAD (the new import sits adjacent to
but does not modify the hunt `truth` import line) and `test_plans.py`,
which was clean at HEAD and at `ITEM_BASELINE`. Nothing hunt-dirtied
is edited, reverted, or consolidated onto.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched. Optimizer siblings
   (`walker.py`, `nested_fetch.py`, `lateral_fetch.py`,
   `single_parent_fetch.py`, `nested_planner.py`, `extension.py`) and
   the filters/orders/mutations/types/`rest_framework` flavors hold no
   second live read: the package-wide literal census (### Enumeration)
   finds the attribute spelled in code at exactly the owner (read +
   write), the pre-change adapter, and the seal snapshot key. `walker`
   and `nested_fetch` already import from `_queryset_private`;
   `write_transaction.py` takes `queryset_db` from it. No flavor
   re-spells this read in local vocabulary.
2. **Sync/async twins.** Inapplicable with reason: a pure synchronous
   attribute read with no await boundary admits no async twin, and no
   `async def` reader of this attribute exists in the package.
3. **Derived rather than repeated knowledge.** Searched. The seal's
   snapshot-key read derives nothing: it reads a different population
   (R1). `_sealed_prefetch_related_lookups` receives lookups as a
   parameter and reads no attribute (R2). One genuine adjacent twin
   found and NOT touched: the `PrefetchLookup` alias spelled
   identically at `plans.py:63` and `_queryset_private.py:31` — a
   type-vocabulary rule, not this read rule; named as sub-rule S1 for
   Worker-0 to row.
4. **Inverse / round-trip pairs.** The write half,
   `set_queryset_prefetch_lookups`, is single-owned with one package
   caller (the seal clone-write, `querysets.py:3976`) plus tests. Read
   and write halves are co-owned in one module; no second writer
   exists. The old s11 clone-write spelling is extinct (converted by
   `f2f18ba6`).
5. **Contracts restated in another medium.** Tests compose the owner by
   name (consumers, listed in F1, not counted). The `test_querysets.py:3493`
   `vars(source).pop("_prefetch_related_lookups", None)` line is
   fixture sabotage for the seal's absent-key arm: setup, not a
   definition (it must name the key to remove it; it cannot go through
   the read helper). Docstring projections: the adapter's "Centralizes"
   overclaim (s11 D2, coupled here) is rewritten by this consolidation;
   the owner's "spelled here once" claim becomes true for live reads.
6. **Enforcement by omission.** The family enumerates every live-read
   site (### Enumeration); pre-change, the adapter was the one member
   not composing the owner. That gap is what this item closes.
   Post-change every live read composes the owner; no member lacks the
   rule. No behavior defect under this axis.

### Enumeration

Instrument: `rg -n "_prefetch_related_lookups" django_strawberry_framework/`
(16 hits, 4 files) plus an evasion sweep for computed spellings
(`getattr(*prefetch*)`, `__dict__`, `vars(`, quoted `_prefetch`).
Every hit homed:

| # | Site | Home |
|---|---|---|
| 1 | `_queryset_private.py:87` strict read body | F1 owner definition |
| 2 | `_queryset_private.py:97` write body | F1 round-trip half (owned, untouched) |
| 3 | `_queryset_private.py:85,95` checker notes | projection (suppression rationale) |
| 4 | `plans.py:619` pre-change getattr body | F1 second definition -> consumer |
| 5 | `plans.py:605,608,612` docstring | projection (rewritten; D2) |
| 6 | `querysets.py:3902` snapshot-key read | R1 (seal contract, excluded) |
| 7 | `querysets.py:2565` validator name + `:2573`, `:2637`, `:3009`, `:3703` prose | R2 + projections |
| 8 | `walker.py:680` comment cite | projection |
| 9 | `walker.py:1544` owner composition | F1 consumer (already composed) |
| 10 | Evasion sweep: `to_attr` / `prefetch_to` / `prefetch_through` getattr reads, module `__dict__` / pickle `vars()` / info-cache slots | out of mechanism (F-N path-read rule and unrelated namespaces; no queryset-lookups read among them) |

No third live-read site exists. The s11 walker strict-forward
second spelling is extinct at HEAD (composes the owner since
`f2f18ba6`); the s11 seal clone-write spelling is likewise extinct.

### Challenges

Counts count authoritative definitions only; consumers, oracles and
projections are listed under F1, not counted. "Before" = pre-change
bytes (the `6f2d0c70` region at HEAD); "after" = this item's tree.

- C1 (Django renames `_prefetch_related_lookups`; the s11 C18 rerun).
  Before: 2 live spellings move (the owner body, the adapter getattr).
  After: 1 (the owner body); the adapter, the walker site and every
  test follow by name with no edit. The seal snapshot key
  (`querysets.py:3902`) moves under the seal's snapshot-discipline
  contract either way (R1). Count: 2 -> 1.
- C2 (the non-queryset failure mode changes, e.g. a non-queryset must
  raise instead of yielding `[]`). Moves: the adapter alone, before
  and after; the strict owner is untouched. Count: 1 -> 1. This is
  the s11 keeping-separate reason preserved in layers rather than
  spellings: strict-fails-loud stays the owner's contract,
  lenient-silent stays the adapter's, and one spelling serves both.
- C3 (the adapter's result container changes, e.g. callers need an
  immutable snapshot so the adapter returns `tuple`). Moves: the
  adapter's one wrap expression alone, before and after. Count: 1 -> 1.

Not this finding's axis: the stored-entry shape (the entry union
grows) still moves twice, once per `PrefetchLookup` alias spelling.
That is the type-vocabulary twin named as sub-rule S1, with its own
owner decision owed; this consolidation neither claims nor moves it.

## Findings

### F1 — attached-prefetch-lookups live read (CONFIRMED, consolidated 2 -> 1)

- **Contract + variation.** One rule: a live read of the lookups
  Django attached to a queryset spells `QuerySet._prefetch_related_lookups`
  exactly once, in the strict typed owner; the plans-local lenient
  contract (`object` in, `list` out, `[]` for non-querysets) survives
  as an adapter over it. Varies on: the Django-private spelling
  (owner), the stored entry shape (owner signature), the
  non-queryset failure mode (adapter).
- **Sites + roles.**
  - Definition (owner, kept): `utils/_queryset_private.py::queryset_prefetch_lookups`.
  - Definition (converted to consumer): `optimizer/plans.py::_consumer_prefetch_lookups`
    (`:604`, body `:614`-`:616`).
  - Consumers: `plans.py:1455` (`_diff_prefetch_related`),
    `plans.py:1532` (`_prefetch_lookup_paths`), `walker.py:1544`
    (`_hint_prefetch_over_pk_set`), `querysets.py:3976` (write half),
    and 27 lookups-helper call sites across 5 `tests/` files
    (module imported more widely for its sibling helpers).
  - Oracles: the 5 new `TestConsumerPrefetchLookups` rows (independent
    literal expectations: `["entries"]`, `[]`; the spy asserts the
    composition, the boundary row asserts the `isinstance` arm).
  - Projections: the rewritten adapter docstring, the owner's module
    docstring (now true for live reads), this record.
- **Challenges.** C1 2 -> 1, C2 1 -> 1, C3 1 -> 1 (### Challenges).
- **Owner + lifetime.** Owner by responsibility: `_queryset_private`
  already owns every sibling private-attribute spelling, both
  consumers' modules import from it (`walker.py:18`, new
  `plans.py:46`), and the dependency runs optimizer -> utils with no
  cycle (`_queryset_private` imports stdlib + Django only). No stored
  derivation: both functions are pure reads ("not cached", principle 4).
- **Migration.** The adapter keeps its name, signature, module and
  both call sites; its body becomes an `isinstance` guard plus
  `list(owner(queryset))`. `QuerySet` moves from the `TYPE_CHECKING`
  import to the runtime import (same class, narrowed by the guard, no
  cast). The old getattr spelling is extinct.
- **Distinct behavior.** What stays separate: the strict owner still
  fails loud (`AttributeError`) on a missing attribute for its typed
  callers; the adapter still answers `[]` for non-querysets. The one
  dropped tolerance is undocumented incidental behavior, never a
  contract: a non-queryset carrying a truthy attribute of the same
  name used to contribute its contents and now contributes nothing.
  No test pinned it (census: zero direct test callers pre-change; the
  `SimpleNamespace` doubles in `test_plans.py` target the
  `deferred_loading` readers only); no production input reaches it
  (site 1 is typed `QuerySet`; site 2 values outside a genuine
  queryset are outside Django's own `Prefetch.queryset` contract).
  The old `or ()` `None` guard was dead code under a real queryset by
  the old docstring's own admission (upstream always stores a tuple)
  and its retirement trigger (stand-ins retired repo-wide) has fired.
  Recorded here and in the adapter docstring.
- **Behavioral proof.** `execution-verified` throughout:
  - New class, 5 rows green: shared-tree focused run plus workspace
    run `dry-20261009T203349-47a577` (`5 passed`).
  - Regression: full `tests/optimizer/test_plans.py`, 123 passed
    (`dry-20261009T203513-0dd788`); full
    `tests/optimizer/test_extension.py` (transitive: extension apply
    -> `diff_plan_for_queryset` -> adapter), 182 passed
    (`dry-20261009T202801-45f57e`).
  - Failability (`dry-20261009T203640-59e07c`, manifest
    `$TMPDIR/attachlook-f61-manifest.json`): entry 1 restores the
    previous inline getattr body (behavior-preserving hand copy) ->
    exactly the spy row + the boundary row fail, the 3 behavioral
    rows pass (composition pinned, behavior intact); entry 2 returns
    a fixed wrong list -> exactly the 3 queryset-arm rows fail. Both
    `pinned`, both restores byte-proved.
  - Type gates, all in the workspace copy on final bytes:
    `basedpyright` 0 errors (`dry-20261009T203354-75a5f2`),
    `basedpyright -p pyrightconfig.floor.json` 0 errors
    (`dry-20261009T203520-27314e`),
    `check_truthful_reads.py --check` 0 errors
    (`dry-20261009T203632-f22d41`). No new cast, widening or
    suppression: the replaced code needed none and neither does the
    replacement (`isinstance` narrows; `QuerySet` was already
    imported for annotations). `check_public_types.py` not owed: no
    public symbol touched.
- **Structural gate.** The spy row
    (`test_queryset_arm_reads_through_the_shared_owner`) plus the
    boundary row (`test_non_queryset_attribute_is_not_read`) jointly
    gate the composition: entry 1's negative control (inline getattr
    restored) fails exactly those two while every behavioral row
    passes, proving the gate guards the by-name composition rather
    than behavior. A name/existence assertion alone would pass that
    control, so none is used.
- **Coupling.** s11 D2 (the "Centralizes" overclaim) couples here and
    is closed by this consolidation: the rewrite lands in the same
    docstring the finding edits (## Defects). No other coupling; the
    walker and seal files are read-only for this item.
- **Freshness.** HEAD `23b5f421` (unmoved). WT / HEAD / `ITEM_BASELINE`
    (`6680965b`): `optimizer/plans.py`
    `39713c65` / `6f2d0c70` / `218be6d2`;
    `optimizer/walker.py` `57ab6770` / `bc6bc969` / `57ab6770`
    (untouched); `utils/_queryset_private.py` `a26a8d43` /
    `ff8b2b46` / `a26a8d43` (untouched);
    `utils/querysets.py` `e6660894` / `4d8a3d39` / `e6660894`
    (untouched); `tests/optimizer/test_plans.py` `832d0b55` /
    `fe606e15` / `fe606e15`; `tests/optimizer/test_extension.py`
    `4f935214` / `ee77ddf3` / `4f935214` (untouched). Population:
    full-package `rg` census above (16 hits + evasion sweep), upstream
    `query.py` reads at installed Django 6.1.2, `f2f18ba6` + `0c76625a`
    diffs, s11 File `optimizer/plans.py` artifact (C18/D2/C1 carried,
    re-verified, not inherited). Any fingerprint change reopens.

### R1 — seal snapshot-key read (rejected; distinct contract)

`querysets.py:3902` reads a key of the instance-namespace snapshot the
seal took without dispatching consumer code, not the live attribute.
Under a Django rename it moves, but under the seal's
snapshot-discipline contract (which key names which proven state),
not this family's live-read rule. This is the s11 C1 corrected
exclusion, re-verified at current bytes (the clone-write half now
composes `set_queryset_prefetch_lookups` at `:3976`). Trigger: the
seal starts reading live queryset attributes; that read joins F1.

### R2 — `_sealed_prefetch_related_lookups` (rejected; no read)

Takes already-obtained lookups as a parameter and validates them; it
never touches the attribute. The shared token is name vocabulary, not
a second definition. Trigger: it starts reading the attribute itself.

### R3 — `deferred_loading` lenient readers (rejected; distinct mechanism)

`deferred_loading_of`, `_consumer_only_fields`, `_consumer_projection`
read `query.deferred_loading`, a different attribute under a different
shape contract. Same file, same defensive style, different rule.
Trigger: none within this family (different mechanism entirely).

### R4 — shared lenient-readers module (rejected; standing trigger checked)

Standing `join_taxonomy` R13 rejects collecting the lenient readers
into one module. This consolidation is compatible, not a trigger
event: leniency stays local (the adapter in `plans.py`) while only
the strict spelling is shared. The R13 trigger stands unchanged.

### S1 — `PrefetchLookup` alias twin (sub-rule, named for Worker-0, untouched)

`PrefetchLookup: TypeAlias = str | Prefetch[str]` is spelled
identically at `plans.py:63` and `_queryset_private.py:31` (the
second introduced by `f2f18ba6`, which could not import down from
utils to optimizer). A change to the stored entry shape moves both.
That is a type-vocabulary rule, not this read rule: separate owner
decision (candidate: `_queryset_private`, the lower module both
spelling sites can import), separate index row. Proposed family name:
`prefetch-lookup-spelling-alias`. Untouched by this item.

## Defects

- D2 (s11 File `optimizer/plans.py`, prose-only): the adapter's
  "Centralizes the brittle Django-private contract" promised a single
  home that two live spellings falsified. CLOSED by this item: the
  consolidation restores single live ownership in
  `utils/_queryset_private.py::queryset_prefetch_lookups` and the
  adapter docstring now states the adapter contract instead of the
  centralization claim. Owner was and remains
  `optimizer/plans.py::_consumer_prefetch_lookups`; fix verified by
  the F1 proofs (the spy + boundary rows fail any re-introduced
  second spelling of the read).

No new defects found. The alias twin (S1) is a consolidation
candidate for its own family item, not a defect.

- D3 (Worker-2) (prose-only; NEW): the spec-003 rationale sentence
  "Reads of Django's private `_prefetch_related_lookups` go
  through one named reader,
  `django_strawberry_framework/optimizer/plans.py::_consumer_prefetch_lookups`"
  (`docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md`,
  "Lookup-path flattening") is newly falsified by this
  consolidation: the adapter no longer touches the attribute,
  the owner does. (It was already imprecise at BASE — the
  walker has read through the owner since `f2f18ba6` — but
  the narrow reading held until this item rewrote the body.)
  Fix (one sentence, for whoever owns spec-003 prose):
  reads go through
  `utils/_queryset_private.py::queryset_prefetch_lookups`,
  with `_consumer_prefetch_lookups` as the lenient plans
  adapter. The DONE build-doc D17 row carries the same stale
  "single reader" phrase but closed history stays as written.
  Owner: spec-003 rationale. Blocks nothing; home at closeout
  with the cycle's other doc-only defects.

## Pending execution

None. Every F1 proof executed in the workspace copy on final bytes
(see ## Implementation (Worker-1) for run ids); no `proof:` entry is
owed. No `gate:` entry is owed.

Cells: `--cell sharded` and `--cell pg` are inapplicable by
construction (Worker-2 judges): the consolidated code is a pure
attribute-read branch with no database, alias, or dialect decision,
and the new tests build lazy querysets without issuing a query, so no
cell-specific behavior exists to verify.

## Judgment

CONFIRM. The nomination's walker half retired under committed
`f2f18ba6`, but the re-derived trace finds the same count-2 shape in
new clothes: the strict owner plus the one holdout still spelling the
attribute. The consolidation layers the two genuine contracts (strict
owner, lenient adapter) over one spelling, closes coupled D2, and is
proved behavior-preserving with gates that fail exactly the rows a
regression must fail. One sub-rule (S1) is named for Worker-0; four
rejections carry triggers.

## Implementation (Worker-1)

Tracked change (item-scoped diff vs `ITEM_BASELINE=6680965b`, exactly
these hunks, nothing else):

- `django_strawberry_framework/optimizer/plans.py`: `_consumer_prefetch_lookups`
  becomes the lenient adapter (`isinstance` guard + `list(owner(...))`,
  docstring rewritten, D2 closed); `QuerySet` promoted from the
  `TYPE_CHECKING` import to the runtime import; owner import added.
  Net plans.py: +14/-16.
- `tests/optimizer/test_plans.py`: new `TestConsumerPrefetchLookups`
  (5 rows: 3 behavioral, 1 `isinstance`-boundary, 1 by-name spy) at
  the package tier — the lenient arms are unreachable from a real
  GraphQL query, so `tests/` is the mandated tier per AGENTS.md.
  Net: +52/-0.

Proof commands (all through `heavy`; pytest/basedpyright/prove in the
workspace copy at `dry/attachlook-f61/consolidate`, slot-2):

- `uv run python scripts/workspace.py run dry/attachlook-f61/consolidate --fresh -- pytest -n0 tests/optimizer/test_plans.py::TestConsumerPrefetchLookups --no-cov -q` -> 5 passed (`dry-20261009T203349-47a577`).
- `... -- pytest -n0 tests/optimizer/test_plans.py --no-cov -q` -> 123 passed (`dry-20261009T203513-0dd788`).
- `... -- pytest -n0 tests/optimizer/test_extension.py --no-cov -q` -> 182 passed (`dry-20261009T202801-45f57e`).
- `... -- basedpyright` -> 0 errors (`dry-20261009T203354-75a5f2`).
- `... -- basedpyright -p pyrightconfig.floor.json` -> 0 errors (`dry-20261009T203520-27314e`).
- `... -- python scripts/check_truthful_reads.py --check` -> 0 errors, 120 files (`dry-20261009T203632-f22d41`).
- `uv run python scripts/workspace.py prove dry/attachlook-f61/consolidate ~/dry/tmp/attachlook-f61-manifest.json` -> both entries `pinned`, restores byte-proved (`dry-20261009T203640-59e07c`).
- Shared tree (the one authorized focused run): `pytest -n0 tests/optimizer/test_plans.py::TestConsumerPrefetchLookups --no-cov -q` -> 5 passed.
- After every edit: `uv run ruff check --fix <path>` + `uv run ruff format <path>` on exactly the touched paths (clean), plus `check_trailing_commas.py --check` on both (0 violations after collapsing one over-exploded test signature).

Ledger rows owed to Worker-0 (`## Owned changes`):

- `django_strawberry_framework/optimizer/plans.py` — Family `attached-prefetch-lookups-read` (f61) — `_consumer_prefetch_lookups` composes `queryset_prefetch_lookups`; `QuerySet` runtime import; docstring (D2 closed).
- `tests/optimizer/test_plans.py` — Family `attached-prefetch-lookups-read` (f61) — `TestConsumerPrefetchLookups` (5 rows).

## Independent verification (Worker-2)

Recorded before reading `## Findings`, from a fresh trace at current
bytes (HEAD `23b5f421` + WT). Fingerprints: plans.py
WT `39713c65` / HEAD `6f2d0c70` / BASE `218be6d2`; walker.py
WT==BASE `57ab6770` / HEAD `bc6bc969` (untouched by this item);
`_queryset_private.py` WT==BASE `a26a8d43` / HEAD `ff8b2b46`
(untouched; WT dirt is concurrent prose); test_plans.py WT
`832d0b55` / BASE==HEAD `fe606e15` (clean at baseline, all dirt
this item's). Dispatch pins match all four.

### Own trace

Package-wide sweep for the mechanism (`_prefetch_related_lookups`
literal, `queryset_prefetch_lookups`, `PrefetchLookup`,
`getattr.*prefetch`) finds these touchpoints, nothing else:

- `django_strawberry_framework/utils/_queryset_private.py::queryset_prefetch_lookups`
  — strict direct read, typed `tuple[PrefetchLookup, ...]`.
  Role: authoritative definition (owner candidate).
- `django_strawberry_framework/optimizer/plans.py::_consumer_prefetch_lookups`
  — BASE: second spelling (`getattr(..., ()) or ()`), total over
  `object`. WT: lenient adapter (`isinstance` + `list(owner(...))`).
  Role: second definition pre-edit, consumer/adapter post-edit.
- `django_strawberry_framework/optimizer/walker.py::_hint_prefetch_over_pk_set`
  (`:1544`) — strict forward through the owner. Role: consumer.
  The nomination's walker half retired under committed `f2f18ba6`
  (read in full: walker hunk routes `inner._db`, `inner._hints`
  and `inner._prefetch_related_lookups` through the new owner;
  `optimizer/plans.py` production code untouched by that commit,
  only its tests) — verified, not inherited.
- `django_strawberry_framework/utils/querysets.py:3902`
  (`state.get("_prefetch_related_lookups")`) — seal snapshot-key
  read over `truth.instance_state`. Role: excluded sibling under
  its own trust contract (must not dispatch attribute access on
  an untrusted object, fails closed; spec-045). The s11 C1
  correction stands: it moves under seal contracts, not this
  read rule.
- `django_strawberry_framework/utils/querysets.py:3976`
  (`set_queryset_prefetch_lookups`) — seal clone-write through
  the owner. Role: consumer (write side of the round-trip pair,
  same owner module).
- `PrefetchLookup` alias twin (`plans.py:63` vs
  `_queryset_private.py:31`, textually identical). Role:
  sub-rule (element-type vocabulary, not the read).
- `deferred_loading_of` and the `prefetch_to` getattr sites are a
  different mechanism (different attribute) and do not move on
  this family's challenges.

Call sites of the adapter: `_diff_prefetch_related` (typed
`QuerySet`, always a real queryset in production) and
`_prefetch_lookup_paths` (`inner` typed `object` from a
consumer-controlled `Prefetch.queryset`). Django 6.1.2
(`Prefetch.__init__`) stores `.queryset` without a type check,
so the lenient arm's input shape is real; stock Django always
stores a tuple (`__init__` `:375`, `prefetch_related(None)`
resets to `()`), so the old `or ()` guard was dead code under a
real queryset, as its own docstring said.

### Own change challenges (pre-edit bytes)

- C-a Django renames `_prefetch_related_lookups`: the owner read
  + the plans getattr spelling move = 2 definitions. (Owner
  write, seal key, tests, docs move under their own rules, listed
  not counted.)
- C-b Django changes the stored container: owner return type +
  plans `list(...)` assumption = 2. (Seal exact-tuple gate moves
  under its own contract.)
- C-c Django admits a new lookups entry kind: both `PrefetchLookup`
  aliases move = 2 (S1 territory, distinct rule).

Count-2 CONFIRMED on the read rule; no third live read exists.

### Owner I would choose

`utils/_queryset_private.py::queryset_prefetch_lookups`, strict
owner + lenient plans adapter — for dependency direction (utils
is importable from optimizer; plans already imports the owner;
the reverse edge would be illegal), existing responsibility (the
module owns every Django-private QuerySet state spelling once,
with the ignore-consolidation rationale), and contract honesty
(the adapter's totality-over-`object` is a plans-domain need for
consumer-controlled `Prefetch.queryset`; pushing silence into
the shared owner would weaken the strict sites). Unify-into-one
rejected: one lenient body in utils would make the owner lie for
garbage inputs at strict call sites.

### S1 split judgment (pre-read)

ENDORSE the split, pending W1's reasons: the alias twin is the
element-type vocabulary, not the read; it needs its own owner
analysis (dependency direction points at `_queryset_private`,
but plans' broader optimizer-vocabulary role must be weighed);
the read consolidation ships complete without it.

### Reconciliation with `## Findings` (post-read)

Agreement, verified point by point rather than inherited:

- Sites and roles match exactly: strict owner, converted
  adapter, walker consumer, seal key excluded (R1), seal
  write-side consumer, alias sub-rule (S1), `deferred_loading` /
  `prefetch_to` different mechanism (R3). No third live read; my
  package-wide sweep found the same touchpoints and nothing else.
- Counts match on the decisive axis: my C-a and W1's C1 are the
  same rename challenge at 2 -> 1. W1's C2/C3 (failure-mode and
  result-container variation, both 1 -> 1) are challenges I did
  not posit and they strengthen the record: the keeping-separate
  reason survives as layers, not spellings.
- Correction to my own trace: my C-b (stored-container change)
  was miscounted at 2. The adapter's `list(...)` wrap is
  container-agnostic, so only the owner's return annotation
  moves: count 1, not 2. The CONFIRM rests on the rename axis
  and is unaffected.
- Owner choice matches for the same reasons (dependency
  direction, existing `_queryset_private` responsibility,
  contract honesty of strict-owner-plus-lenient-adapter). The
  adapter shape survives challenge: one lenient body in utils
  would make the shared owner lie for garbage inputs at the
  strict call sites.
- `f2f18ba6` retirement verified from the commit itself, not
  from W1's word: the walker hunk routes all three private
  reads through the new owner, and `optimizer/plans.py`
  production code is absent from that commit's stat.
- Enumeration matches member by member (rows 1-10, each home
  re-derived). The "16 hits" instrument count reproduces at
  BASE bytes (4 plans hits there vs 1 at WT; rows 4-5 are
  tagged pre-change). A bytes tag on the count would help the
  next reproducer; noted, not a defect.
- Matrix: axes 1, 3, 4, 5 searched and agreed (S1 found on
  axis 3 with my endorsement now final: separate rule,
  separate owner decision, zero behavior coupling, durable
  home via the new family row). Axis 2 inapplicable with
  reason, agreed. Axis 6 gap closed, no behavior defect.
- The dropped tolerance is named honestly in F1 and matches my
  executed grid exactly (see gate runs): agreement on real
  querysets, missing/`None` attributes, managers and `None`;
  intended narrowing on non-queryset tuple carriers; the
  real-queryset-with-`None` input raises where the old code
  returned `[]`, on an object Django's own `_chain` also
  rejects, so no legitimate path presents it.
- Every claimed census reproduced exactly: 27 lookups-helper
  sites (7/10/3/1/6), 12 `tests/` + 6 live-API module
  importers, zero direct test callers pre-change, BASE
  `SimpleNamespace` doubles targeting the `deferred_loading`
  readers only.
- D2 closure confirmed: the adapter docstring states the
  adapter contract (no "Centralizes" claim survives), live
  ownership is single, and my own entry-1 control proves the
  spy + boundary rows fail any re-introduced second spelling.
- Pending execution empty confirmed: every F1 proof exists
  with a run id and I re-ran each class of proof myself (see
  below). Sharded/pg inapplicable-by-construction ENDORSED:
  the consolidated lines branch only on `isinstance` plus one
  attribute read (no database, alias, or dialect decision)
  and the new tests build lazy querysets without issuing a
  query, so no cell-specific behavior exists.
- AGENTS.md prose rules: added lines carry no banned
  provenance word under strict boundaries (the one loose hit
  is the `optimizer.plans` module path in the spy's patch
  target); the docstring cites
  `utils/_queryset_private.py::queryset_prefetch_lookups` in
  `path::Symbol` form; `tests/` is the mandated tier (the
  lenient arms need a non-queryset `Prefetch.queryset`, which
  no wire input can construct, and the spy pins a by-name
  composition HTTP cannot observe; the queryset arm already
  executes under every live optimizer test).
- Concurrent work untouched, verified by diff content: the
  `truth` import line is hunk context (byte-identical, not
  modified), the `~429`/`~928` BASE hunks are absent from the
  item diff, `test_plans.py` was clean at BASE, walker/seal
  files read-only (WT==BASE on both). One phrasing nit: the
  artifact's "target lines clean at HEAD" is loose for the
  import hunk (HEAD lacks the adjacent `truth` line); the
  substance — no dirty line modified — holds.
- Type health without new machinery: the diff adds no cast,
  widening, suppression, or `Any`; the replaced code needed
  none and neither does the replacement. No public symbol
  touched (`check_public_types.py` not owed); no overrides.

Gate re-runs, all in my own copy at
`dry/attachlook-f61/verify-1` (slot-3, fresh sync) unless noted:

- New class 5/5 (`dry-20261009T204946-2a8541`) + the one
  authorized shared-tree focused run 5/5.
- Own old-vs-new grid 7/7 (`dry-20261009T205017-32dfa3`).
- `test_plans.py` 123/123 (`dry-20261009T205025-cc46ff`);
  `test_extension.py` 182/182 (`dry-20261009T205031-3a432a`).
- `basedpyright` 0 errors (`dry-20261009T205102-ab3068`);
  floor 0 errors (`dry-20261009T205213-4f7a26`).
- `check_truthful_reads.py --check` 0 errors over 120 files
  (`dry-20261009T205325-378e1d`).
- `prove` with my own manifest: entry 1 (inline getattr
  restored) pins exactly spy + boundary; entry 2 (fixed
  wrong list) pins exactly the 3 queryset-arm rows; both
  restores byte-proved (`dry-20261009T205353-368bc4`).
- `ruff format --check` + `ruff check` clean on both touched
  paths; `check_trailing_commas.py --check` 0 violations.

Verdict: `verified`. S1 endorsement stands (Worker-0 rows the
`prefetch-lookup-spelling-alias` index row + Family item). The
one new finding is D3 (Worker-2) under `## Defects`, doc-only,
for closeout homing like the cycle's other prose defects.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
