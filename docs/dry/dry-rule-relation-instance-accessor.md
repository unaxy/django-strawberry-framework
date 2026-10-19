# DRY review: `relation-instance-accessor`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

The instance-attribute name relation rows are reached through on a Django
instance (`book_set` vs the query/GraphQL name `book`). The provisional owner
holds the whole rule in one body:
[relations][relations]`::instance_accessor` (three-tier: precomputed
`accessor_name` slot, then live `get_accessor_name()`, then `name`, with typed
`ConfigurationError` guards).

Whole-package sweep for the mechanism (every `instance_accessor` import/call,
every `get_accessor_name()` call, every `accessor_name` slot read/write, every
hand-rolled `related_name`-or-default derivation, every `_set` string build,
one `def` census) finds exactly one authoritative derivation plus consumers
that compose it by name and neighbors with distinct contracts. No second
derivation exists: no `related_name or ...` expression, no `_set`
concatenation, no `.accessor_name` read outside the helper body, exactly one
`def instance_accessor`.

Definition (1): [relations][relations]`::instance_accessor`.

Consumers (compose by name, listed never counted): the
[field-meta][field-meta] stamp (`_from_field_shape` calls it once on the raw
descriptor into the `accessor_name` slot); `walker.py::_plan_prefetch_relation`
plus the hint-rebase path (call it on the `FieldMeta`, hitting the precomputed
tier, for prefetch lookup strings); `nested_planner.py` (same tier-1 call for
`NestedConnectionRequest.lookup`; the request separately carries the raw field
for strategies that never call the helper); `types/resolvers.py::
_make_relation_resolver` (one call on the raw field, threaded through the
many / reverse-O2O branches via `getattr` + `_prefetched_objects_cache` probes
+ `_check_n1(accessor_name=...)`); `types/finalizer.py` Phase-2.5 synthesis
(one call on the raw field, passed as the `accessor_name` string argument);
`connection.py::_build_relation_connection_resolver` (pure reader: receives the
string, never imports the helper, never computes).

Finalizer-vs-connection verdict (brief question): finalizer:777 is a consumer
of the owner that produces connection's argument; connection.py reads, never
computes. Single definition still holds.

Oracles: `tests/utils/test_relations.py` (three-tier pins + hostile pins, all
executing the helper); `tests/optimizer/test_field_meta.py` (stamp pins);
`tests/test_relay_connection.py::test_reverse_fk_without_related_name_resolves_list_and_connection`
(end-to-end S3 pin asserting Django's own `get_accessor_name()`, never the
owner); `tests/types/test_resolvers.py` (accessor-keyed cache probe);
`tests/utils/test_querysets.py` (project-wide default-accessor scan pin for
the R-A neighbor); live prefetch suites for the wire behavior.

Projections: spec-032 prose, build-003 D11 row, slot/arg docstrings,
`TREE.md` prose. Prior dry-0_0_11 record already calls this module the
single-source point (projection, re-derived fresh here).

The `## Owned changes` D1 row (walker seal-policy fix) sits on a family path
but this item makes zero edits there; ledger rows on the gate-only test files
touch no family site. No ledger row is built on.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The stamp serves every flavor from one
`field_map`; filters/orders/mutations/forms/REST never touch the accessor
machinery (zero `instance_accessor` / `accessor_name` / `get_accessor_name`
tokens in those five folders). Discharged.
2. **Sync/async twins.** No such surface: the derivation is pure metadata
reads plus contained calls, zero ORM I/O, zero await. Inapplicable by
construction.
3. **Derived rather than repeated knowledge.** Every site calls the helper by
name. Walker/nested-planner hit tier 1 (precomputed slot on the `FieldMeta`
`_resolve_field_map` yields on both paths); resolvers/finalizer hit tiers 2/3
on the raw descriptor. The four look-alikes are rejections below (R-A, R-B,
R-C, R-D), each with its difference. Discharged.
4. **Inverse / round-trip pairs.** No inverse grammar exists: nothing maps an
accessor back into the three-tier answer. The R-A scan matches live tier-2
spellings over a filtered population with a fail-open policy; it is not a
second half of this grammar. Discharged.
5. **Contracts restated in another medium.** Oracles execute the helper (unit
+ stamp pins) or Django's own API (S3 pin) or the wire (live suites); none
mirrors the tier table. Docstrings/specs/build rows are projections.
Discharged.
6. **Enforcement by omission.** Hidden (`+`) relations never reach the helper:
no `include_hidden` token exists anywhere in the package, so every
`get_fields()` walk (stamp, walker fallback, scans) uses Django's default
exclusion, matching `classify_path`'s `FieldDoesNotExist`. The symmetrical
self-M2M answer (`None`) fails typed-loud, never leaks. No member lacks a
guard its contract requires. Discharged.

### Enumeration

Instrument: whole-package content sweep over `django_strawberry_framework/`
for the mechanism vocabulary (`instance_accessor`, `accessor_name`,
`get_accessor_name`, `related_name`, `_set` spellings, `.accessor_name`
reads) plus a `def instance_accessor` census. Population triaged below.
Members: 1 definition, 6 consumer call sites across 5 modules, 1 pure reader,
6 rejection candidates. No member unassigned; every `### Challenges` row ends
in the definition or a rejection.

- `def instance_accessor`: exactly 1 ([relations][relations]).
- `instance_accessor` tokens (15 lines): def + `__all__` + field-meta
import/call + walker import/2 calls + nested-planner import/call + finalizer
import/call + resolvers import/call. All consumers, zero second bodies.
- `accessor_name` tokens (39 lines): owner body + field-meta slot/docstring +
resolvers threading + connection param/reads + finalizer comment + querysets
prose. Zero direct slot reads outside the helper body.
- `get_accessor_name` tokens (11 lines): owner 7 (docstring + tier-2 body) +
querysets scan 2 (docstring + R-A call) + field-meta/finalizer prose 2.
Exactly one live call outside the helper (R-A).
- `related_name` tokens (19 lines): prose + the R-A scan's contract notes +
partition-expr notes. Zero `related_name or <default>` derivations.
- `_set` construction: none (hits are prose examples + unrelated tokens).

### Challenges

Authoritative definitions only; consumers, oracles, and projections that also
move are listed, never counted.

- CH1 (Django changes the default accessor scheme, e.g. drops `_set`).
Definitions forced: **0 moves, 1 holder**. Tier 2 delegates to Django's own
`get_accessor_name()`; the scheme lives upstream, the package holds only the
dispatch. A scheme change flows through with zero package edits.
- CH2 (project overrides the naming: `related_name`, or
`related_name` + differing `related_query_name`). Definitions forced: **1**.
The helper reads the live Django answers; the stamp recomputes at class
creation; all 6 call sites follow. Probe cases 4/5/6 pin both the classic
split (`book` vs `book_set`) and the sharper one (`rq_books` vs `rq_book`,
divergent WITH `related_name` set).
- CH3 (exotic shape: symmetrical-`None`, slot-less snapshot, non-`str`
metadata). Definitions forced: **1** (the three-tier ladder + typed guards).
Probe case 11 (symmetrical `None` -> `ConfigurationError`, never a leak) plus
the unit hostile pins.
- Lifetime challenge (brief): is the stamp a cache needing invalidation?
**No.** Stamp inputs (`related_name`, model name, flags) are fixed at Django
class creation and `_meta` is immutable after; the walker unregistered
fallback rebuilds per walk with no cache layer; re-finalize re-stamps. Stamp
lifetime = definition lifetime; no invalidation story owed. Probe case 12
(stamp slot == live answer).

Execution proof (all `execution-verified`): disposable-workspace probe
`docs/dry/temp-tests/relation-instance-accessor/probe_accessor_boundary.py`
(21 checks green; `package:` prints the WS copy, `db:` is `:memory:`, no
shared checkout or database touched) + one focused shared-tree run
`uv run pytest tests/utils/test_relations.py -k "instance_accessor or accessor"
--no-cov -n0 -q` (6 passed). Each rejects the wrong result named beside it
(query-name-used-as-accessor, tier confusion, silent `None`).

## Findings

### F1 `relation-instance-accessor` (rejected: single-owned, no duplication)

- Contract + variation: instance-attribute name for relation rows. Diverges
from the query name exactly where Django's `get_accessor_name()` diverges
from `related_query_name()`: reverse many-side rels without `related_name`,
or any rel with an explicit differing `related_query_name` (probe case 6).
Coincide: every forward shape, reverse O2O without `related_name`
(`multiple=False`, no `_set`), named reverses, `GenericRelation`,
`GenericForeignKey`, MTI parent links.
- Sites + roles: definition at [relations][relations]; 6 consumer call sites
compose by name; connection.py is a pure string reader; oracles execute;
projections describe. No second definition.
- Challenges: CH1 count 0 moves / 1 holder, CH2 count 1, CH3 count 1,
lifetime count 0 (class-creation-stable, nothing to invalidate).
- Owner + lifetime: [relations][relations] (principle 7: narrowest cohesive
owner every consumer already imports without reversing a dependency; moving
the dispatch to the stamp would cycle the owner's other residents into the
optimizer). Stamp lifetime = definition lifetime, stated at the
`accessor_name` slot docstring (already present, verified).
- Migration: none (rejection; zero edits).
- Distinct behavior: everything below stays separate at its recorded home.
- Behavioral proof: execution-verified (WS probe + focused oracle run above).
- Structural gate: none, with reason. A bypass adds zero `instance_accessor`
imports, so an importer count is a bespoke existence test that cannot trip;
the misuse vocabulary (`field.name` reads) is pervasively legitimate, and the
one sound census (`get_accessor_name` direct calls) already has its second
legitimate member (R-A) — pinning it would be per-helper bespoke machinery
for a population of two. Same shape as the sibling `relation-kind-taxonomy`
no-gate verdict.
- Coupling: none.
- Freshness: fingerprints under `## Implementation (Worker 1)`.
- Principle 2 read: one grammar produces the name Django instance seams
resolve by; both the prefetch planners and the row resolvers read it.
Principle 11: deletion reviewed — the helper has 6 live callers across 5
modules; nothing dead.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A querysets accessor-map scan (`utils/querysets.py::
_reverse_relation_by_accessor_or_none` direct `get_accessor_name()`).
Difference: reverse question (accessor spelling -> field, over non-concrete
reverse rels) with a fail-open per-candidate policy (`None` on miss); the
helper raises typed errors by contract. Routing through the helper changes
raised exceptions (principle 8). Trigger: helper gains a lenient non-raising
mode AND the scan contract changes. Home: the scan docstring (present,
verified) + the project-wide oracle pin beside it.
- R-B parent-side partition expression (`join_taxonomy.py::_partition_expr` /
`plans.py::window_partition_for_prefetch`: `remote_field.attname or
remote_field.name`). Difference: the attach key Django's prefetch uses to map
child rows to parents — explicitly NOT the accessor (both docstrings state
it). Trigger: Django unifies the attach key with the accessor. Home: the
`_partition_expr` docstring (present, verified).
- R-C window `to_attr` grammar (`connection.py::relation_connection_to_attr`
/ `nested_fetch.py::NestedConnectionRequest.to_attr`: `_dst_<field>_connection`
`$`-delimited, keyed on the FIELD NAME by Decision 4). Difference: prefetch
attach namespace, not instance reading; the resolver needs BOTH (accessor for
rows, field name for the window probe) and the finalizer passes both.
Trigger: windows attach keyed on the accessor. Home: the connection resolver
docstring fast-path paragraph (present, verified).
- R-D forward-branch `field_name` reads (`types/resolvers.py::
forward_resolver` `getattr` / `_will_lazy_load_single` on `field_name`).
Difference: forward-only population where name IS the attribute by Django
contract (probe cases 1-3); no derivation present, nothing to centralize.
Trigger: a forward-shaped relation whose attribute differs from `name`
reaches the branch. Home: the "Instance reads go through the accessor"
comment (present, verified).
- R-E `_check_n1` `accessor_name or field_name` fallback. Difference:
`None`-tolerance for direct test-double callers; the helper never returns
`None`. Not a derivation. Trigger: helper gains a `None` return. Home: the
`_check_n1` docstring (already states it, verified).
- R-F projections (spec-032 prose, build-003 D11 row, slot/arg docstrings).
Difference: describe; never own. No home owed beyond the owner.

## Defects

- D1 (UNFIXED): `connection.py::_build_relation_connection_resolver`
docstring states "``accessor_name`` is the same ``field.name`` the shipped
many-side list resolver reads", but the list resolver reads
`instance_accessor(field)` (`types/resolvers.py::_make_relation_resolver`
#"accessor_name = instance_accessor(field)"), which DIVERGES from `field.name`
for a reverse relation without `related_name` (the S3 oracle pins
`plainbook` vs `plainbook_set`). The parity conclusion holds only because
BOTH go through the helper, not because accessor IS `field.name`; the same
docstring's next paragraph states the divergence correctly, so the docstring
contradicts itself within six lines. A reader trusting the sentence would pass
`field.name` and reintroduce the S3 `AttributeError`. Sentence is HEAD text
(verified via `git show HEAD:`), not concurrent dirt; file carries unrelated
concurrent cursor-guard hunks, left alone. Routes to Worker 0 for a NAMED
owning card; never fixed inside this item.

## Pending execution

None. The WS probe and the focused oracle run both executed green; no proof
is `execution-deferred`. Gate business (full suite + coverage) is deferred
with reason: zero-edit rejection with an argued no-gate outcome needs no
gate run from this item; the cycle gate covers the tree.

## Judgment

Single authoritative derivation; CH1 holds with zero moves, CH2/CH3 count 1,
lifetime needs no invalidation. Every neighbor is a consumer composing by
name, a distinct contract with its own reasons to change, or a projection.
The finalizer produces connection's argument by calling the owner;
connection.py only reads. Outcome: reject the consolidation, zero edits,
rejections recorded with triggers and homes, one docstring defect routed
unfixed.

## Implementation (Worker 1)

No tracked changes. Production and test trees untouched
(`git diff 7b6c01ea99dfef860df2ce46153f404339ef161c -- django_strawberry_framework/
tests/` empty for this item's paths; this artifact + untracked probe scratch
are the only new files). No `ruff` input (no `.py` touched, tracked or
otherwise — probe scratch is untracked). No commit (maintainer only).

Attribution stop-rule check: the `## Owned changes` ledger holds nothing on
the owner, stamp, walker, planner, resolver, or finalizer paths (its walker
row is the D1 seal-policy fix, untouched here). `connection.py` worktree
`3c4d5dcb` vs HEAD `93e998f2` hunks are the cursor-guard feature (`@@ -54`,
`@@ -703`, `@@ -734`: import, `_offset_cursor_prefix` /
`_reject_negative_offset_cursor`, fallback branch); the family sites (resolver
arg region, no `instance_accessor` import anywhere in the file) sit outside
every hunk — left alone, no edit made. Item-baseline diff for the file is
empty (dirt predates the baseline). All other member files are clean
(worktree == HEAD).

Freshness fingerprints (`git hash-object`; `HEAD:` shown where the worktree
is dirty):

- `utils/relations.py` `7662b0bb669c4dfba4a437f3b8f309357f718dca`
- `optimizer/field_meta.py` `7215c887aa26b1d828503ca30dd3b02546fe68b3`
- `optimizer/walker.py` `9b111ed938951a073a9226ccbcfacabc3af981e8`
- `optimizer/nested_planner.py` `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04`
- `optimizer/nested_fetch.py` `4d8d37a7f52cf94d2916f17db3a8a21393e28d57`
- `optimizer/join_taxonomy.py` `9b355a5090ce471e373849dd0a61da8f808e78b9`
- `optimizer/plans.py` `cce985319c8833f3660653327d3003f1f03655a5`
- `types/resolvers.py` `f3341e6a9f52659925762bce097033bac67e3b51`
- `types/finalizer.py` `77fd9a2dd229eb9de5f29188c5058035d3606323`
- `utils/querysets.py` `96618fba4eafb6a87e73414770014e3aee5b41ef`
- `connection.py` worktree `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a`;
`HEAD:` `93e998f2c7ea1d7f18607a6e37e394466ac75ad4`
- Oracles: `tests/utils/test_relations.py`
`37db9b64c74756f5d300031513ee8008824a9ec9`;
`tests/optimizer/test_field_meta.py`
`5212e9368b98ad727eef684ee23d91d20d56532e`;
`tests/test_relay_connection.py`
`b6bd90d979cf7c25325f24f1a9f5dada58b82134`;
`tests/types/test_resolvers.py`
`88f7fb07bf8346eb0744f8ae208e5edf9b032737`.
Dirty-oracle hunks adjudicated: `tests/optimizer/test_extension.py` hunk at
`@@ -3962` (optimizer-context exports), far from the `:167` prefetch pin;
`tests/utils/test_querysets.py` hunks at `@@ -32` / `@@ -4688+` (imports,
prefetch-child seal), far from the `:4980+` accessor pins — both left alone.
- Upstream contract: Django 6.1
`.venv/lib/python3.14/site-packages/django/db/models/fields/reverse_related.py`
(`ForeignObjectRel.name` -> `related_query_name()`; `get_accessor_name()`
`related_name`-or-`<model>[_set]`; `multiple` default `True`,
`OneToOneRel` `False`).
- Searched population: whole `django_strawberry_framework/` mechanism sweep
triaged under `### Enumeration`; prior `field_meta.py` file-item census
re-derived; sibling `relation-kind-taxonomy` separations re-checked as
inputs (its no-gate reasoning adopted for the structurally identical gate
question here).
- Scratch: `docs/dry/temp-tests/relation-instance-accessor/
probe_accessor_boundary.py` + `probeapp/__init__.py` (untracked; Worker 0
removes by explicit path after verification);
`<scratch>/dry-ws/relation-instance-accessor` (WS copy, cycle edits included
at copy time; `package:` line proves the WS import, `db: :memory:` proves no
shared database).

Plan rows for Worker 0: tick Family `relation-instance-accessor` (this
artifact); responsibility-index row `relation-instance-accessor` `open` ->
`rejected`; home defect D1 on a NAMED owning card (owner
`connection.py::_build_relation_connection_resolver` docstring); no sub-rule
decomposed, so no new index rows.

## Independent verification (Worker 2)

Own sweep, re-derived from the bodies (counts below were established by
opening each site before reconciling against `## Findings`; every
agreement/difference is stated explicitly).

- `def instance_accessor`: exactly 1
 ([relations][relations]`::instance_accessor`). No second body anywhere.
- `instance_accessor` call sites: 6 across 5 modules, each opened.
 `optimizer/field_meta.py::_from_field_shape` (1, raw descriptor -> tiers
 2/3, stamps the `accessor_name` slot: the single producer);
 `optimizer/walker.py` (2: `_plan_prefetch_relation` lookup path and the
 hint-rebase path — both pass `FieldMeta` objects from `_resolve_field_map`,
 so both hit tier 1, the precomputed slot); `optimizer/nested_planner.py`
 (1: `instance_accessor(django_field)` where `django_field` is the
 `FieldMeta`, tier 1 for `NestedConnectionRequest.lookup`, while the
 request separately carries `raw_relation_field` for strategies that never
 call the helper); `types/resolvers.py::_make_relation_resolver` (1, raw
 field -> tiers 2/3, threaded through many / reverse-O2O branches via
 `getattr` + cache probes + `_check_n1`); `types/finalizer.py` Phase-2.5
 synthesis (1, raw field -> tiers 2/3, forwarded as the `accessor_name`
 string argument). `connection.py`: 0 calls, 0 imports of the helper.
- `get_accessor_name` live calls outside the helper: exactly 1
 (`utils/querysets.py::_reverse_relation_by_accessor_or_none`, the R-A
 scan). Owner-body use is via `relation_attr` + contained call.
- Direct `.accessor_name` slot reads outside the helper body: 0. The only
 `relation_attr(field, "accessor_name", None)` read is inside the owner;
 every other token is the slot declaration/docstring, a local variable, a
 `str` parameter, or prose.
- Hand-rolled `related_name`-or-default derivations: 0. `_set`
 constructions: 0 (remaining hits are `"book_set"` prose examples).
- Compute-vs-read: the sole compute is the owner body. The field-meta
 stamp is a producer (calls the owner once, publishes the slot). Walker,
 nested-planner, resolvers, finalizer are consumers (call the owner by
 name). Connection is a pure reader (receives `accessor_name: str`,
 single `getattr(root, accessor_name).all()` row read; fast-path probes
 derive from `relation_field_name`-keyed `to_attr`, never the accessor).
 Finalizer:777 is therefore a consumer-that-forwards, not a second
 definition and not connection's competitor: single definition holds.

Agreements: definition count 1, producer 1 (field-meta stamp, one call),
consumer calls 6 across 5 modules with the tier split above,
connection pure-reader, CH1 0-moves/1-holder, CH2 1, CH3 1. No
differences: W1's site roles and tier claims match the bodies as opened
(in particular walker/nested-planner genuinely receive `FieldMeta`, so
the tier-1 reading is correct, and the request's separate raw-field
carriage is as described).

Lifetime challenge, judged: the stamp is REALLY invalidation-free.
A post-creation `related_name` mutation is out-of-contract
monkey-patching, not a supported Django operation: `_meta` is built at
class creation and the apps registry, migrations, and system checks all
assume its immutability, while Django's own `get_accessor_name()`
answers live with no invalidation contract of its own. The stamp is
rebuilt at `DjangoType` creation, re-finalize re-stamps, and the walker
unregistered fallback rebuilds per walk with no cache layer. No
invalidation story is owed; W1's reasoning stands.

Zero production change, confirmed: `git diff`
`7b6c01ea99dfef860df2ce46153f404339ef161c` across the eight package
paths plus oracles is empty; `connection.py` HEAD-diff touches only the
cursor-guard regions (import + `_offset_cursor_prefix` /
`_reject_negative_offset_cursor`) with 0 `instance_accessor` /
`accessor_name` hunks, and the resolver-arg family region sits outside
every hunk; all other member files are worktree == HEAD. All concurrent
dirt preserved and untouched.

Zero-edit consolidation search, done independently: (a) resolvers'
raw-field call taking the `FieldMeta` slot instead — tier shift only,
no definition removed, and it would couple the resolver to a successful
`FieldMeta` build on the test-double path; (b) finalizer:777 composing
the stamp — worse coupling (ties synthesis to `field_map` readiness)
for zero definitional gain; (c) walker/planner reading `.accessor_name`
directly — a guard-bypassing read outside the owner, strictly worse
than the helper seam (breaks on `None` hand-built instances); (d)
routing the R-A scan through the helper — changes raised exceptions
(typed raise vs fail-open `None`), a principle-8 violation; (e)
connection importing the helper — zero-benefit dependency since the
finalizer already computed the string. There is truly nothing to
consolidate; the zero-edit outcome is accepted, not merely tolerated.

Gate judgment: no gate, accepted. The sibling `relation-kind-taxonomy`
is the correct precedent, not the logger family: the bypass population
here is open-ended (a hand-rolled `field.name` read or a second
`get_accessor_name()` call adds zero `instance_accessor` imports, so an
importer census cannot trip; the misuse vocabulary is pervasively
legitimate; the one sound census already has its second legitimate
member in R-A, so pinning it is bespoke per-helper machinery the method
forbids). The logger gate owned a closed constructor census with a
plausible duplication; that shape does not obtain here. No gate is
demanded, by name.

Rejections R-A through R-F, each opened at its home: R-A (reverse
question accessor-spelling -> field, fail-open `None` vs typed raise;
trigger + scan docstring present); R-B (parent-side attach key
`remote_field.attname or remote_field.name`, both docstrings state it
is NOT the accessor); R-C (`_dst_<field>_connection` grammar keyed on
the field name by Decision 4, resolver needs both strings); R-D
(forward-only `field_name` reads where name IS the attribute by Django
contract; probe cases 1-3); R-E (`_check_n1` `accessor_name or
field_name` `None`-tolerance for test doubles; helper never returns
`None`); R-F (projections describe, never own). All six carry
difference + trigger with existing homes. Agreed in full.

D1, reproduced and adjudicated: the sentence at
`connection.py::_build_relation_connection_resolver` ("`accessor_name`
is the same `field.name` the many-side list resolver reads") is HEAD
text (HEAD lines for the same paragraph), while the list resolver reads
`instance_accessor(field)`
(`types/resolvers.py::_make_relation_resolver` #"accessor_name =
instance_accessor(field)"), which diverges from `field.name` for a
reverse relation without `related_name` (S3 oracle pins `plainbook` vs
`plainbook_set`), and the same docstring's next paragraph states the
divergence correctly — a self-contradiction within six lines.
In-item-unfixable as claimed: `connection.py` is externally dirty
(cursor-guard hunks only) and the family region sits outside every
hunk, so any edit would breach the attribution stop-rule. Defect-bar
verdict: MET. Contract row (the method's own defect class,
docstring-contradicts-body, plus the stated parity invariant thereof);
feasible project shape under supported public API (any reverse FK
without `related_name` — the Django default); reaching input (any
GraphQL query over such a relation's connection/list pair, where a
reader trusting the sentence passes `field.name` and reintroduces the
`AttributeError`). Card class: low-severity prose repair owning the one
sentence (parity holds because BOTH resolvers call the shared helper,
not because accessor IS `field.name`); NAMED owning card at closeout,
correctly NOT fixed in-item, no coupling to the rejection, never a
release blocker for this item.

Freshness, re-hashed (`git hash-object`): all 15 blobs identical to the
W1 listing (`utils/relations.py` `7662b0bb…`, `optimizer/field_meta.py`
`7215c887…`, `optimizer/walker.py` `9b111ed9…`,
`optimizer/nested_planner.py` `0ad8ff5d…`, `optimizer/nested_fetch.py`
`4d8d37a7…`, `optimizer/join_taxonomy.py` `9b355a50…`,
`optimizer/plans.py` `cce98531…`, `types/resolvers.py` `f3341e6a…`,
`types/finalizer.py` `77fd9a2d…`, `utils/querysets.py` `96618fba…`,
`connection.py` worktree `3c4d5dcb…`, plus the four oracle blobs) — no
drift since W1's trace.

`## Pending execution` empty, judged correct: no proof is
`execution-deferred` (WS probe 21/21 + focused oracle 6 passed, inputs
unchanged per the re-hash above); the full-suite gate belongs to the
cycle gate, not to this zero-edit item. No test run performed or owed
here (no edits; runs only on explicit request).

AGENTS.md prose on the item diff: artifact citations use
`path::Symbol` form with reference-style links and the canonical link
group block intact; raw `:NN` pins (`finalizer:777`, oracle `:167` /
`:4980+`) are permitted inside `docs/dry/dry-*.md` scratchpad artifacts;
no process provenance, no test-tier debt (zero edits, oracles cited at
their tiers), no `ruff` input (no `.py` touched), no commit. Compliant.

## Defects

None new from Worker 2. D1 above is W1's entry, reproduced, adjudicated,
and routed (NAMED owning card at closeout, owner
`connection.py::_build_relation_connection_resolver` docstring).

## Judgment (Worker 2)

Verdict: `verified`. Single authoritative derivation with 6 composing
call sites across 5 modules plus 1 pure reader; challenges and lifetime
as claimed; all 6 rejections carry difference + trigger with existing
homes; no gate owed (taxonomy precedent, logger distinguished); D1 meets
the defect bar as a prose-repair card, correctly left unfixed on
externally dirty ground; freshness re-hashed clean; pending execution
correctly empty. Exact plan rows: tick Family
`relation-instance-accessor`; responsibility-index row
`relation-instance-accessor` `open` -> `rejected`; home D1 on a NAMED
owning card at closeout (no new index rows; no coupling).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
