# DRY review: `recognized-fetch-queryset-skeleton`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule, re-derived fresh at HEAD bytes: how a nested-connection child
queryset is recognized as fetch-shaped and reduced to the skeleton the fetch
paths execute. Three sub-mechanisms: (a) the shared execution skeleton --
`optimizer/nested_fetch.py::RecognizedFetchQuerySet`, i.e. the
clone-surviving per-strategy spec slot plus the planned-window signature
capture at `rebind` plus the recognized-rows-or-windowed-body `_fetch_all`;
(b) the recognition vocabulary every fetch-time recognizer composes by name --
`optimizer/lateral_fetch.py::window_predicate_signature` and its five helpers;
(c) the boundary where recognition ends and fetching begins -- the
`_fetch_recognized_rows` rows-or-`None` verdict the skeleton's `_fetch_all`
consumes, with `None` executing the carried windowed body verbatim.

Sites found. Definition of the skeleton: `nested_fetch.py`
(`RecognizedFetchQuerySet` with `_clone`, `rebind`, `_fetch_recognized_rows`,
`_fetch_all`, `_dst_spec_attr`, `_dst_window_signature`). Adapters: exactly
two subclasses, `lateral_fetch.py::LateralQuerySet` and
`single_parent_fetch.py::SingleParentWindowQuerySet`, each a spec slot plus a
one-line `_fetch_recognized_rows` override delegating to its backend
recognizer (`_fetch_lateral_rows` via `_recognize_lateral_fetch`;
`_fetch_single_parent_rows` via `_single_parent_where_ids`). Definition of the
vocabulary: `lateral_fetch.py` (`window_predicate_signature`,
`_normalize_window_node`, `_is_window_qual`, `_parent_in_values`,
`_select_columns`, `_deduplicate_parent_ids`); consumers by name are
`single_parent_fetch.py` (five runtime imports), `nested_fetch.py::rebind`
(one lazy signature import), and the lateral recognizer itself. Consumers of
the skeleton: exactly two `rebind` call sites, the spec-guarded `wrap=`
lambdas in `LateralPrefetchStrategy.plan` and `WindowedPrefetchStrategy.plan`
(f18 seam ground, taken as input). Oracles: `tests/optimizer/test_nested_fetch.py`,
`tests/optimizer/test_lateral_fetch.py`, `tests/optimizer/test_single_parent_fetch.py`
(clone-carry, spec-`None` fallback, vendor/setting gates, signature-mismatch
downgrade, parent-id extraction rows), `tests/optimizer/test_walker.py` and
`tests/test_keyset.py` isinstance rows, and the live fastpath suite under
`examples/fakeshop/test_query/`. Projections: the skeleton, subclass,
recognizer, and helper docstrings (each states its contract and its
insufficiency or twin relation), spec-033 Decision 5/6 and spec-045 prose,
glossary and kanban entries.

Connected behavior examined and placed outside the rule: the
strategy-independent classifier `nested_fetch.py::unwindowable_child_queryset_reason`
(queued sibling `unwindowable-child-queryset-classification`; the recognizers
consume its verdict as their first gate); the planner's strategy-independent
recognition and refusal arms (queued sibling
`nested-connection-plan-orchestration`); the sealed-execution queryset
(verified s17); `connection.py::_resolve_from_window` and the
`connection_to_attr` probe (f18 handoff ground); the root-connection
`_guard_source_not_pre_sliced` misuse guard plus the `predicates.py`,
`extension.py`, and `walker.py` combinator reads (each its own operation's
legality check); the `__post_init__` twins, rebind wraps, spec-builder
custom-subclass arms, and row constructors (standing rejected rows, taken as
input); the installed Django 6.1 `QuerySet.__aiter__`, which funnels async
iteration through `sync_to_async(self._fetch_all)()`.

Dirt attribution (by diff content vs `git show HEAD:<path>`).
`nested_fetch.py` carries five hunks, all concurrent bug-hunt work: the
`truth` import swap, the `truth.is_subclass` classifier read, a `# truth: ok`
rebind comment, and the `resolve_strategy` docstring plus body migration
(`truth` reads, `except BaseException` deletion). None is in `## Owned
changes` (no row names this path) and none is touched by this zero-edit
verdict. `lateral_fetch.py` and `single_parent_fetch.py` are clean; all three
pins match dispatch exactly, so nothing drifted under the trace.

## Verification

### Matrix

Each axis discharged for the family as a whole; the target's whole-package
mechanism sweep is the floor, not the shape.

1. Cross-flavor policy mirroring -- searched every public surface
(`types`, `filters`, `orders`, `mutations`, `forms`, `rest_framework`,
`utils`, `connection.py`) for queryset-recognition shapes (`_fetch_all`,
`__class__` swaps, `QuerySet` subclasses, `Window`-identity reads,
`_result_cache` writes, `Prefetch(`/`to_attr` construction). The only
adjacent shapes are the verified s17 seal (contract: visibility sealing of
consumer querysets under policy -- different inputs, outputs, and layer),
the `_guard_source_not_pre_sliced` resolver-contract guard (fail-loud
misuse error vs silent fallback), and the per-operation combinator reads
(own-operation legality, partly the queued classifier sibling's ground).
No second recognition definition in any flavor.

2. Sync/async twins -- no twin exists, by construction. The installed
Django 6.1 `QuerySet.__aiter__` runs `await
sync_to_async(self._fetch_all)()` over the same override the sync path
runs, so the skeleton covers both colors with one body. The package's
`async for` sites iterate already-bound querysets and never bypass the
skeleton. Nothing to mirror, no gap.

3. Derived rather than repeated knowledge -- the projection derives once
through the plans owner (`deferred_loading_of`, composed by
`_select_columns`, never re-derived); the parent-link column and table
are read off the join descriptor (f22/f23 ground, taken as input); the
window-annotation grammar (`WINDOW_*` names) is composed from the plans
owner at both membership sites. The lateral-vs-single-parent order freeze
is a recorded parallel with separate needs (verified lateral FL13, taken
as input). The annotation-membership pair (`_WINDOW_ANNOTATIONS` vs the
singleton `{WINDOW_ROW_NUMBER}`) shares that grammar with per-backend
membership dictated by the pinned contract (R3).

4. Inverse / round-trip pairs -- the signature round trip (capture at
`rebind` from the planned body, compare in the recognizers against the
fetch-time query) runs through one function on both halves
(`window_predicate_signature`, count 1). `rebind` (wrap) and `_clone`
(carry) share one slot discipline (`_dst_spec_attr` plus the signature).
Spec build (plan time) vs spec consume (fetch time) is per-backend with no
cross-backend inverse. No separated grammar halves.

5. Contracts restated in another medium -- oracles import the owners and
assert behavior (clone-carry identity, `is None` fallbacks, signature
equality/inequality, extraction lists, engagement end to end); none
re-derives the skeleton, the signature, or any helper. The two backend
clone-carry tests intentionally mirror each other as independent
behavioral pins, not as a shared helper (each must fail for its own
backend's breakage). Projections (docstrings, specs, glossary, kanban)
describe; the skeleton and helper docstrings additionally carry the
principle-10 grammar. No second definition in any medium.

6. Enforcement by omission -- the family enumerates closed: exactly three
`QuerySet` subclasses in the package (the skeleton plus its two
adapters); zero direct constructions outside `rebind`; exactly two
`rebind` callers, both spec-guarded wraps; every strategy routes through
the shared floor (f18). No member lacks the guard, no third backend
exists, no `Prefetch` with a hand-shaped queryset bypasses recognition.
Absence is not invoked anywhere as a verdict.

### Enumeration

Family item: the mechanism census over `django_strawberry_framework/`
at HEAD bytes via exact-match spelling instruments, each cross-checked at
WT bytes (identical results; the hunt dirt touches none of these lines).
Counts are definitions unless noted:

- `class` with a `QuerySet` base: 3 -- the skeleton plus the two
adapters. Every other queryset in the package is a plain `QuerySet`.
- `_fetch_all` definitions: 1, the skeleton's. No subclass overrides it;
the one `super()._fetch_all()` call is the nested-prefetch pass plus the
fallback executor.
- `__class__ =` writes: 1, in `rebind`.
- `_fetch_recognized_rows` definitions: 3 -- the skeleton's
`NotImplementedError` hook plus two one-line overrides, each delegating
to its backend recognizer. The overrides are declarations, not
definitions (principle 1).
- `_dst_spec_attr` bindings: 3 -- the `ClassVar` declaration plus one
member value per adapter. `_dst_window_signature` writes: 3
(declaration, `_clone` carry, `rebind` capture); reads: 2 (one per
recognizer comparison).
- `.rebind(` call sites: 2 -- the lateral and windowed `wrap=` lambdas,
each reached only behind its spec builder's eligibility gate.
- Vocabulary definitions: 6, all in `lateral_fetch.py`
(`window_predicate_signature`, `_normalize_window_node`,
`_is_window_qual`, `_parent_in_values`, `_select_columns`,
`_deduplicate_parent_ids`). Importers: `single_parent_fetch.py` (five,
runtime), `nested_fetch.py::rebind` (one, lazy), the lateral recognizer
(local). Zero re-derivations.
- `Window`-identity reads (`isinstance(..., Window)`): 2 sites, both
inside the vocabulary. No other module classifies window quals.
- `where.children` walks: 4 -- the lateral recognizer walk, the
signature gather, the single-parent walk, and the spec builder's
presence check. All in-family; the twin walks are intentionally
separate (R1).
- Classifier (`unwindowable_child_queryset_reason`) definitions: 1;
callers: the planner plus both recognizers' first gate. Sibling-owned
(R5); counted here only to fix the consumption boundary.
- Test-tree subclassing of the skeleton: 0. Test references are
`isinstance` oracles and direct owner imports; no test calls `rebind`
or defines a fetch queryset.

### Challenges

Each change posited on a variation axis; only authoritative definitions
counted (consumers, oracles, projections listed, never counted). All
proof `static-reviewed`: source reads plus the censuses above; no
behavioral equivalence is claimed because nothing moves.

- C1, carried clone state: a second per-strategy slot rides every clone.
Moves `RecognizedFetchQuerySet._clone` and `rebind` only (one body
each); neither subclass body moves (each declares its slot name).
Count 1.
- C2, signature grammar: the signature also covers the `ORDER BY`, or
`None`-on-unreadable becomes a loud error. Moves
`window_predicate_signature` (plus `_normalize_window_node`) only; the
`rebind` capture and both recognizer comparisons compose by name.
Count 1.
- C3, fallback contract: the fallback must re-verify a property before
running the windowed body. Moves `RecognizedFetchQuerySet._fetch_all`
only (the one override, the one `super()` call). Count 1.
- C4, `__in` semantics: expression right-hand sides admitted, or the
column/table match extended. Moves `_parent_in_values` only; both
WHERE walks compose by name. Count 1.
- C5, window-qual classification: a new `Window`-annotation shape.
Moves `_is_window_qual` only; both walks plus the signature gather
compose by name. Count 1.
- C6, parent-id dedup semantics: `NULL` ids match a branch, or ordering
changes. Moves `_deduplicate_parent_ids` only; both executors compose
by name. Count 1.
- C7, projection model: `defer()` shapes supported, or the
deferred-loading read changes. Moves `_select_columns` only; the
lateral spec builder, the lateral guard, the single-parent spec
builder, and the single-parent guard compose by name. Count 1.
- C8, residue separation (the twin-walk challenge): single-parent
tolerates a carried scope in the fetch-time WHERE. Moves
`_single_parent_where_ids` and `_fetch_single_parent_rows` only; the
lateral walk and its keyset/visibility matchers do not move. Count 1
-- per-adapter variation, confirming the walks are separate rules
(R1), not one rule spelled twice.
- C9, hook contract: `_fetch_recognized_rows` returns a sentinel record
instead of `None`. Moves the skeleton's `_fetch_all` plus the two
one-line overrides (adapter declarations under principle 1). Count 1
definition.

Consumers moving under these changes (listed, not counted): the two
`wrap=` lambdas under C1/C9; the oracles pinning each verdict; the
docstring projections. Oracles never read the owners they check beyond
direct behavioral assertion.

## Findings

One finding: the recognized-fetch queryset skeleton is single-owned;
CONFIRM as a proved zero-edit verdict.

- Contract + variation -- a windowed-prefetch queryset with a recognized
fast path: (i) the spec slot named by `_dst_spec_attr` plus the
`_dst_window_signature` survive every clone; (ii) `rebind` captures the
signature off the planned body before the prefetch `__in` lands, with
`None` failing closed; (iii) `_fetch_all` executes the strategy's rows
when `_fetch_recognized_rows` recognizes the fetch-time query completely
and otherwise runs the carried windowed body (whose nested-prefetch pass
the superclass call still performs). Varies over backend count, carried
clone state, signature grammar, and per-backend residue contracts.
- Sites + roles -- definition: `nested_fetch.py::RecognizedFetchQuerySet`
(all four methods, both attributes). Vocabulary definitions:
`lateral_fetch.py` (all six helpers). Adapters (declarations): the two
subclasses plus the two backend recognizer/executor bodies. Consumers:
the two spec-guarded `wrap=` call sites, the planner and recognizer
callers of the sibling classifier. Oracles: the three optimizer test
files, the walker/keyset isinstance rows, the live fastpath suite.
Projections: docstrings, specs 033/045, glossary/kanban entries.
- Challenges -- C1-C9, every count 1 (see `### Challenges`).
- Owner + lifetime -- the skeleton class in `nested_fetch.py`, the
narrowest module both backends already import at runtime (principle 7);
the vocabulary stays with its existing owner `lateral_fetch.py`, which
holds the window-identity-proof responsibility (relocating it would move
lines without relieving any change obligation -- R15). Lifetime: per
queryset clone chain for the carried state, per wrap for the signature
capture; no cached derivation, no cross-request state (principle 4:
nothing stored beyond the queryset's own ride-along).
- Migration -- none. Nothing moves, nothing is renamed, no call site is
rewritten.
- Distinct behavior -- the two recognizers prove different queries
(lateral SQL over parent ids vs a pristine-clone plain `LIMIT` re-query)
with different residue contracts (matcher-verified keyset/visibility
residue vs at-most-one-`IN` fail-closed); the two gate chains differ
per execution need (vendor gate vs fetch-time setting read; projected
vs frozen `select_related`; full window-annotation membership vs the
pinned singleton). Sharing stops at the skeleton plus the named
vocabulary by design (principle 5: shared lifecycle, kept adapters).
Each separation carries its trigger below.
- Behavioral proof -- `static-reviewed` throughout: the per-backend
clone-carry oracles (spec identity, signature equality, verbatim
windowed body across `.using().filter()`), the spec-`None`/vendor/
setting fallback rows, the signature-mismatch downgrade rows, the
parent-id extraction rows, and the live fastpath suite pin every
contract verdict. Nothing lands, so no failability proof is owed.
- Structural gate -- no new gate owed, and the rule currently holds
(the HEAD/WT censuses above are the first-run check). The plausible
bypass is a third backend hand-rolling clone-carry/rebind/fallback
instead of subclassing. Against it stand two composing exemplars, the
owner-stated grammar (principle 10, in the skeleton docstring), and
per-backend oracles pinning every contract verdict, so a divergent
copy fails behaviorally where it matters. A subclass census over
exactly two adapters would be a bespoke existence test, the forbidden
shape; a package-wide queryset-subclass AST census is machinery
disproportionate to a docstring-governed seam with no observed
bypass. Negative control reasoned: a behavior-correct hand copy
passes every behavior oracle (the copy is correct), which is exactly
why no new oracle is proposed as a gate. Trigger: a third
`RecognizedFetchQuerySet` subclass landing, or any `QuerySet`
subclass appearing in the package outside the skeleton.
- Coupling -- none. No defect blocks landing because nothing lands.
- Freshness -- HEAD `5c3496e0` (matches dispatch; ITEM_BASELINE
`471f36423d162b6a4824d750c4925a4b8968656b` resolves). Inspected files,
HEAD then WT: `optimizer/nested_fetch.py` HEAD `bedaa76e`, WT
`c36826bb` (five hunt-dirt hunks, attributed above, none in the rule's
lines); `optimizer/lateral_fetch.py` HEAD/WT `a48cb0a4` (clean);
`optimizer/single_parent_fetch.py` HEAD/WT `3a4bb89b` (clean);
`optimizer/nested_planner.py` HEAD `8c3a45f5`, WT `b6ff0a0e`;
`connection.py` HEAD `99969652`, WT `48de0243`;
`optimizer/plans.py` HEAD `97a524e2`, WT `2e962ae2`;
`utils/connections.py` HEAD/WT `5bf8f5fa` (clean); `optimizer/walker.py`
HEAD `13e1be20`, WT `4fd8077f`; `utils/querysets.py` HEAD `69ac3ea3`,
WT `3e392d48`; `keyset.py` HEAD `6af980b8`, WT `7d43c6b1`;
`optimizer/join_taxonomy.py` HEAD `8026dc8d`, WT `aa289013`;
`optimizer/extension.py` HEAD `b7b6c434`, WT `8e3fe7c1`;
`optimizer/predicates.py` HEAD `965d1282`, WT `d9e2f789`;
`optimizer/_context.py` HEAD/WT `274a138b` (clean); `optimizer/hints.py`
HEAD `f6776564`, WT `ee68ae03`; `conf.py` HEAD `eccddc21`, WT `d239302a`;
oracles `tests/optimizer/test_nested_fetch.py` HEAD `7fbd957b`, WT
`0b65aa96`, `tests/optimizer/test_lateral_fetch.py` HEAD/WT `c5aab598`
(clean), `tests/optimizer/test_single_parent_fetch.py` HEAD/WT
`1f48c6ec` (clean), `tests/optimizer/_builders.py` HEAD/WT `567defa9`
(clean). Searched population: the eleven spelling instruments under
`### Enumeration` over `django_strawberry_framework/`, the oracle sweep
over `tests/` and `examples/`, the installed Django 6.1 `query.py`
(`__aiter__` funnel), and the contract sources spec-033/spec-045. Any
fingerprint change reopens the finding.

Exclusions, each with its contract difference and reconsideration
trigger (verified verdicts taken as input, never re-litigated; queued
siblings converged or excluded, never absorbed):

- R1, the twin WHERE walks: considered merging
`_single_parent_where_ids` into `_recognize_lateral_fetch`'s walk;
rejected -- different proven queries (window-plus-`IN` only vs
window-plus-`IN` plus keyset/visibility residue) and different residue
contracts (at-most-one-`IN` fail-closed vs matcher-verified residue
collection). The shared primitives (`_is_window_qual`,
`_parent_in_values`) are already composed by name; only the residue
control differs, and it differs because the executors differ (a
pristine re-query cannot express residue a raw-SQL splice can).
Trigger: a third recognizer needing the shared walk core.
- R2, one parameterized queryset vs two subclasses: considered deleting
the subclasses in favor of one class taking the spec slot name and a
recognizer callable; rejected -- the subclasses are five-line
declarations (principle 1), and parameterizing would move the same
per-backend identity from the type to a stored callable while losing
the `isinstance` oracle vocabulary and the signature-level backend
distinction. No change obligation relieved. Trigger: a third backend
whose recognizer is identical to an existing one's.
- R3, annotation membership: considered deriving single-parent's
`{WINDOW_ROW_NUMBER}` exact-match from `_WINDOW_ANNOTATIONS`;
rejected -- the grammar is already shared (both spell plans-owned
names); the membership differs by pinned contract (lateral executes
counted/reversed/probe shapes, single-parent pins count, reverse, and
keyset out at spec time, so exactly-the-singleton IS its contract's
spell). Trigger: single-parent supporting counted or reversed shapes.
- R4, order freeze (standing lateral FL13, trigger-checked clean):
`_order_columns` (SQL `(column, descending)` pairs for the raw-SQL
renderer) vs `tuple(request.order_by)` (ORM order entries for
re-application) -- parallel freezes with separate needs. No drift at
HEAD bytes. Trigger: a shared order-codec both backends render from.
- R5, the classifier (queued sibling
`unwindowable-child-queryset-classification`): excluded, not absorbed.
Contract difference: strategy-independent plan-time classification of
consumer queryset shapes (sliced/locking/combined/distinct/values)
vs per-backend fetch-time proof of a planner-built window. This
family consumes its verdict; how many definitions the classification
has is the sibling's question. Trigger: the sibling redrawing the
consumption boundary.
- R6, planner recognition (queued sibling
`nested-connection-plan-orchestration`): excluded. Contract
difference: plan-time recognition of a RELATION as a plannable nested
connection (relation kind, field map, refusal arms, window slice)
vs fetch-time proof of a QUERYSET as the planned window plus the
prefetch `__in`. Different inputs, outputs, and times. Trigger: the
sibling moving a refusal across the plan/fetch boundary.
- R7, the sealed-execution queryset (verified s17): excluded. Contract
difference: policy-governed sealing of consumer querysets for
visibility-safe execution (rebuild under `_seal_or_defect` policies)
vs recognition of a planner-built windowed body for fast-path
execution. The `_result_cache` writes serve different masters (seal
carry-forward vs recognized-rows population). Trigger: a seal policy
gating on fetch-shape recognition.
- R8, verified family ground (f17 selection, f18 seam, f20
window-range derivation, f22 join shape, f23 attach projection):
excluded by boundary. This family consumes `resolve_strategy`
verdicts, the `attach_windowed_prefetch` floor, `window_range_plan`
decisions, `LateralJoinShape` membership, and
`prefetch_attach_columns` -- each single-owned elsewhere. Trigger:
any of those owners redrawing its contract.
- R9, the two rebind wraps (standing plan row, trigger-checked clean):
the lateral and windowed `wrap=` lambdas each name their backend's
class and spec -- backend-member declarations under the f18 seam,
not a second wrapping rule. Trigger: a wrap adding logic beyond
naming its class.
- R10, spec-builder custom-subclass arms (standing single_parent-R-d /
plan row, trigger-checked clean): both spec builders refuse
non-plain `QuerySet`s for the shared rebind safety premise, each
stating the rationale at its own arm. No drift at HEAD bytes.
Trigger: a scope change merging the plan gates.
- R11, row constructors (standing single_parent-R-c / plan row,
trigger-checked clean): `_instantiate_row` (`from_db` plus window
attributes plus M2M prefetch aliases) vs Python row-number synthesis
on pristine-clone rows -- different row sources, different
construction. Trigger: a shared row-materialization record.
- R12, the two `__post_init__` twins (standing plan row,
trigger-checked clean): probe/count mutual exclusion enforced at two
construction sites through one shared guard
(`assert_window_fetch_mode_for`) -- enforcement sites, not
definitions. Trigger: the guard's contract changing.
- R13, neighboring queryset-state guards
(`connection.py::_guard_source_not_pre_sliced`, `predicates.py` /
`extension.py` / `walker.py` combinator reads): excluded. Each checks
its own operation's legality (root-connection resolver contract,
existence-predicate attach, root optimization, hint rebuild) with its
own verdict (raise vs skip vs reroute); none proves a fetch-time
window. Trigger: any of them branching on the planned-window
signature.
- R14, `connection.py::_resolve_from_window` (f18 handoff ground):
excluded. Contract difference: consuming landed `to_attr` ROWS
(cursor parity, marker classification, strictness) vs proving the
fetch-time QUERY that produces them. Trigger: the resolver
re-deriving fetch-shape proof instead of reading row attributes.
- R15, vocabulary homing: considered moving the six lateral-owned
helpers to `nested_fetch.py` so no sibling imports a sibling flavor
for machinery; rejected -- relocation without a count reduction is
not a consolidation (every helper already counts 1), the import graph
is acyclic in practice (the skeleton's signature import is lazy),
and the verified file record homes the vocabulary laterally. The
sibling import is a layering fact, not a second owner. Trigger: a
third consumer outside the nested-fetch trio, or an import cycle
forcing the move.

No new index rows: the vocabulary sub-rules converge inside this
family (its row already covers all three files); the R5/R6 siblings
keep their queued rows.

## Defects

None. The trace checked the twin-walk residue handling, the
annotation-membership pair, the order comparisons
(`tuple(query.order_by)` vs the frozen specs), the signature
capture-before-`__in` ordering, the `None`-fails-closed arms, the
Django async funnel, and the oracle import discipline; every behavior
read matches its stated contract at HEAD bytes.

## Pending execution

None. No `proof:` entry (nothing lands, so no failability proof is
owed) and no `gate:` entry. The `--cell sharded` and `--cell pg` cells
read `unverified` under the settled run-9 binary: the fetch paths reach
the database, and `--cell` runs were not authorized (inapplicable by
construction is not claimed). No workspace run and no shared-tree test
run was used; evidence is source reads plus exact-match grep censuses
at HEAD bytes with WT cross-checks.

## Judgment

CONFIRM: the recognized-fetch queryset skeleton is single-owned -- the
skeleton (C1, C3, C9), the signature round trip (C2), and the five
vocabulary helpers (C4-C7), one definition each (C8 confirms the twin
walks are separate rules); every backend, recognizer, and reader
composes by name -- and the consolidation is therefore a proved
zero-edit verdict: no tracked file changed, no test added, no `##
Owned changes` row owed, no `## Implementation` section. Fifteen
exclusions carry contract differences plus triggers (R1-R15, including
five standing records trigger-checked clean and two queued-sibling
boundary rows); f17/f18/f20/f22/f23/s17 verdicts taken as input, never
re-litigated; no defects; no new index rows.

Type gates (observed, read-only, shared tree, WT bytes): `uv run mypy`
clean (`Success: no issues found in 119 source files`); `uv run
basedpyright` clean (`0 errors, 0 warnings, 0 notes`); `uv run python
scripts/check_any.py` clean (`130 allowed use(s) of Any at 90
site(s)`). Zero-edit verdict, so no symbol was added, moved, or
removed; the gates confirm the verdict changes nothing they check.

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

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (headers + `Status`/`Run` lines only).
HEAD `5c3496e0`; WT pins verified: nested_fetch `c36826bb` (= ITEM_BASELINE
blob, hunt dirt predating the item), lateral `a48cb0a4`, single_parent
`3a4bb89b`. `git diff ITEM_BASELINE --name-only` = plan edit alone. All
censuses below are exact-match greps over `django_strawberry_framework/`
(excluding `__pycache__`), plus `tests/` + `examples/` for oracles.

### Own trace: sites + roles

Skeleton (owner candidate `optimizer/nested_fetch.py::RecognizedFetchQuerySet`):

- `RecognizedFetchQuerySet` class def: 1 (nested_fetch.py:148). Subclasses:
  exactly 2 (`LateralQuerySet`, `SingleParentWindowQuerySet`); no
  sub-subclasses anywhere incl. tests; no third `QuerySet[` subclass.
- `def _clone`: 1 (nested_fetch.py:174). Copies spec slot + signature.
- `def rebind`: 1 (nested_fetch.py:184). Sole `__class__`-swap site (1
  package-wide), sole `_chain()` site (1 package-wide), sole signature
  CAPTURE site. `rebind_on_resume` (extensions/operation_state.py) is a
  different name/contract (extension resume), excluded.
- `def _fetch_all`: 1 production (nested_fetch.py:214). The 2
  `tests/utils/test_querysets.py` doubles are test-local seal fakes in a
  non-population medium; Django's own 2 in `.venv` are the framework super.
- `_fetch_recognized_rows`: 1 base contract def (raises) + 2 overrides, one
  per backend. Overrides are adapters (principle 5), not two definitions of
  one rule: lateral proves raw-SQL inputs, single-parent proves the
  degenerate ORM shape.
- `_dst_spec_attr`: 1 declaration + 2 per-adapter values (declarations, not
  definitions). `_dst_window_signature`: 1 slot; written by `_clone` (copy)
  + `rebind` (capture), read by both recognizers. Slots never escape the 3
  optimizer modules in production.

Signature round trip (grammar owner `lateral_fetch.py::window_predicate_signature`):

- `window_predicate_signature`: 1 def; call sites = capture (`rebind`) +
  2 compares (recognizers). `_normalize_window_node`: 1 def, called only by
  the grammar + itself (one rule unit). `WindowSignature`: 1 TypeAlias.
- The two `planned is None or derive != planned` compare guards are two
  ENFORCEMENT sites of one rule (slot docstring + grammar singly own the
  None-fails-closed semantics), per the DRY.md `pipeline_write_phase`
  vocabulary: boolean glue stays at each recognizer's boundary. Extracting
  a 3-line helper would couple the two fail-closed sequences to save 1
  line (principle 11).

Vocabulary (owner `optimizer/lateral_fetch.py`, each 1 def, all imported by
name into `single_parent_fetch.py`, none inlined, none restated):

- `_is_window_qual` (structural classifier; also used by the grammar
  itself), `_parent_in_values` (column+table IN matcher), `_select_columns`
  (projection via `plans.py::deferred_loading_of`), `_deduplicate_parent_ids`
  (hashable fast path + unhashable fallback + NULL drop),
  `window_predicate_signature` (above). 5 doctrine names, 6 defs counting
  the normalizer sub-step.

Consumers (all by name): `WindowedPrefetchStrategy.plan` (single wrap),
`LateralPrefetchStrategy.plan` (lateral wrap), `AutoNestedConnectionStrategy`
(delegates); `rebind(` call sites exactly 2, both `wrap=` lambdas.
Cross-module prose refs (join_taxonomy, utils/connections, module
docstrings) are projections. Oracles: `test_lateral_fetch.py`,
`test_single_parent_fetch.py`, `test_nested_fetch.py`, `test_walker.py`,
`test_keyset.py`, `test_lateral_pg_parity.py`,
`examples/.../test_generic_connection.py` (lateral spec mention),
live `test_query/test_single_parent_fastpath_api.py`. Oracle spot-checks:
signature tests assert literal `()` / `None` + independently-specified
equality relations; `_parent_in_values` / `_deduplicate_parent_ids` tests
assert literals; `test_keyset.py` uses `_is_window_qual` as setup partition
only. No oracle derives its expectation from the owner it checks.

### Own challenges (W2-C1..C9, each with forced-definition count)

- W2-C1 second clone-carried slot: moves `_clone` (1) + subclass slot
  declarations (per-adapter declarations). Count 1.
- W2-C2 extra planned-state proof at wrap: moves `rebind` (1) + a new
  grammar helper (1, same rule unit); recognizer compare arms are
  consumers. Count 1.
- W2-C3 third backend (e.g. portable correlated-subquery per the floor
  docstring): moves 0 existing definitions (add subclass + override +
  wrap + spec builder). Extension by declaration. Count 0.
- W2-C4 signature grammar change (cover annotations / drop `lookup_name`):
  moves grammar + normalizer (1 rule unit). Count 1.
- W2-C5 skeleton split (one backend needs its own `_fetch_all`): adds 1
  override; base stays for the other. Tolerance, not a fork. Count 1.
- W2-C6 vocabulary change per helper (e.g. tuple-only rhs, defer shapes):
  1 def each; both recognizers follow by name. Count 1 x5.
- W2-C7 hook protocol change (return a result object): base contract (1)
  + 2 adapter overrides + `_fetch_all` read (same skeleton). The two
  overrides implement different backends, not one rule twice. Count 1.
- W2-C8 twin WHERE walks (lateral partition-for-dispatch vs single-parent
  prove-degenerate): separate rules. Residue-arm addition moves 1 walk;
  Django drift moves 0 (fail-closed is the specified behavior, no move
  owed); second-IN semantics differ by construction (residue-for-arms vs
  fatal). Max forced count 1. The shared spine (root-AND check, skip,
  first-IN) composes `_is_window_qual` / `_parent_in_values` by name; the
  root-AND one-liner is Django `WhereNode` vocabulary, not a package rule.
- W2-C9 capture-ordering change (capture after the prefetch IN): 1 capture
  site (`rebind`); the grammar ignores non-window children either way, so
  the BEFORE ordering is defense-in-depth documenting intent. Count 1.

No posit forced count > 1 with a landable owner. A shared walk-partitioner
or a shared 3-line compare helper would relieve no change obligation
(principles 5/11): residue disposition is load-bearing-different, and the
fail-closed glue is the enforcement shape.

### Owner choice (principle 7)

Skeleton: `nested_fetch.py::RecognizedFetchQuerySet` — both backends already
depend on it; it never imports them at module scope (dependency direction
wins). Vocabulary: `lateral_fetch.py` module functions — cohesive with the
windowed-body-mirroring knowledge + primary recognizer; sibling import is
one-directional and backend-neutral (window identity, not lateral SQL);
moving to `nested_fetch` would couple the seam to recognition internals to
kill one documented lazy cycle-break (a reshuffle, not a consolidation).
New-module split fails principle 11. Matches the dispatched candidate.

### Own matrix discharge

1. Cross-flavor: census — `QuerySet[` subclasses package-wide are exactly
   the 3; no sibling flavor defines fetch machinery. Discharged.
2. Sync/async: 0 `async def` in all 3 modules; `_fetch_all` runs under
   Django prefetch; async callers run ORM in one `sync_to_async` worker
   (`utils/querysets.py::` verified). No twin. Inapplicable with reason.
3. Derived knowledge: one owner per fact (link via join_taxonomy f22,
   bounds via window_range_plan f20, projection via deferred_loading_of,
   mode via fetch-mode assert); signature derived once at wrap,
   re-derived at fetch (round trip, not a second derivation). Discharged.
4. Round trips: signature capture/compare owned by the grammar (this
   family); SQL/ORM dual renders are f19/f20 input, untouched. Discharged.
5. Other media: oracles + projections classified above, none counted.
6. Omission: subclass population exactly 2, both set slot + override hook
   (read-verified); eligibility refusals read-verified (keyset, counted,
   reversed, custom-subclass, non-DIRECT_FK, non-first-page); vendor gate
   lateral-only by construction (single re-queries vendor-neutral ORM).
   No gap.

### Own exclusions (contract difference + trigger each)

- E1 twin walks: partition-for-dispatch vs prove-degenerate (W2-C8).
  Trigger: a lateral single-parent ORM mode sharing the exact residue
  grammar (cf. standing single_parent R-b).
- E2 signature-gather loop vs walks: gather vs partition/prove. Trigger:
  a shared residue grammar across gather + walks.
- E3/E4 twin guard pairs (signature compare, unwindowable first-gate):
  enforcement sites, not definitions; unwindowable owned by QUEUED
  `unwindowable-child-queryset-classification` (real open index row).
  Trigger: a third recognizer duplicating the glue instead of composing.
- E5 `__post_init__` twins: one-line shared-assert consumers (standing
  R11). Trigger: either body beyond delegation — re-check below.
- E6 rebind wraps x2: one-line compositions (standing R12). Trigger: wrap
  logic beyond `Subclass.rebind(qs, spec)` or a third wrap — re-check.
- E7 spec builders: degenerate-eligibility vs SQL-expressibility
  (standing R-d/R13); the shared exact-type rationale is stated per site.
  Trigger: v1 scope admitting M2M/keyset/counted into single-parent.
- E8 row constructors: pristine-clone synthesis vs `from_db` (standing
  R-c/R14). Trigger: one shared materialization primitive.
- E9 spec records: ORM re-query record vs raw-SQL record (standing R-a).
  Trigger: third shape needing both renderings / lockstep subset.
- E10-E14 verified-input boundaries, untouched: f17 selection, f18 seam,
  f19/f20 range + dual render, f22 join taxonomy, f23 attach columns.
- E15 s17 seal: zero seal refs in `optimizer/` — disjoint populations.
- E16 `_plain_single_table_where` vs `_is_window_qual`: recursive
  Col-admission vs Window-lhs classifier. Trigger: one predicate serving
  both admission + classification.
- E17 `_keyset_seek_quals_match` vs `_visibility_quals_match`: structural
  proof vs byte-equal-compile proof, mutually exclusive arms. Trigger: one
  residue-proof primitive.
- E18 per-backend guard comparands (order slots, annotation sets,
  select_related, extra): different contracts (e.g. exact-`{rn}` vs
  window-superset). Trigger: backends converging on one planned shape.
- E19 `rebind_on_resume`: extension-resume contract, token coincidence.
  No trigger (different domains).

### Reconciliation (read `## Findings` AFTER the trace above; every difference)

F1 / C1-C9: ENDORSED. My W2-C1..C9 posits are independent but converge:
skeleton bodies, signature grammar+normalizer, and all five vocabulary
helpers count 1; adapters (overrides/slots/wraps) are declarations, not
definitions. Census agreement is exact (3 `QuerySet` subclasses, 1
`_clone`, 1 `rebind`, 1 production `_fetch_all`, 1+2 hook, 3
`_dst_window_signature` writes / 2 reads, 2 `rebind(` sites, 6 vocabulary
defs, 2 `isinstance-Window` reads, 4 `where.children` walks, 0 test
subclasses). C8 verdict (twin walks separate) matches my W2-C8 under
different posits; the standing R-b trigger ("a lateral single-parent ORM
mode sharing the exact residue grammar") is sharper than R1's paraphrase
but both are unmet (O2 below).

R1-R15: ALL ENDORSED on fresh evidence.
R1 separate walks (residue control differs because executors differ);
R2 parameterization rejected (sound; I had not posited it);
R3 pinned-singleton membership (matches my E18);
R4 FL13 opened fresh, parallel freeze confirmed at HEAD bytes, no shared
codec, clean;
R5/R6 both name REAL open index rows
(`unwindowable-child-queryset-classification`,
`nested-connection-plan-orchestration`), boundaries sound;
R7 s17 disjoint (zero seal refs in `optimizer/` re-verified);
R8 input families all verified elsewhere (f20 owns `window_range_plan`
per its index row), consumed-not-relitigated, nothing dropped
(`deferred_loading_of` has no family verdict anywhere; 1 def, every read
composes by name — re-censused);
R9-R12 standing rows all opened in home artifacts and trigger-re-checked
fresh at HEAD bytes: 2 one-line wraps, no third; v1 eligibility refusals
all present; distinct row mechanisms; both `__post_init__` bodies still
one-line delegations — CLEAN (trigger-wording notes in O2);
R13 guard + 3 combinator reads verified to exist with own verdicts;
R14 `connection.py` reads no signature (grep-clean);
R15 vocabulary homing matches my independent principle-7 analysis
(nested_fetch-homing considered and rejected as a reshuffle).

Matrix: axis 2's Django 6.1 `__aiter__` funnel re-verified verbatim in the
installed source (`await sync_to_async(self._fetch_all)()`); axis 3's
never-re-derived claim re-censused clean; axis 5's mirrored clone-carry
tests both located (`test_lateral_queryset_clones_carry_the_spec`,
`test_clone_carries_the_spec`); axis 6's enumeration confirmed for
production (O1 carves the test-only exceptions).
Gate: no new gate owed — ENDORSED (bypass named, negative control
reasoned, population judged, trigger given; a third-subclass census
would be the forbidden bespoke shape).
Freshness: all 34 cited pins re-verified EXACT (HEAD `5c3496e0` unmoved);
no drift under the trace. Pending-`None`: correct, plain `verified`
(no `proof:` owed — nothing lands). Cells `unverified`: correct
application of the settled binary (fetch paths reach the DB; `--cell`
unauthorized; inapplicability not claimed). Index rows: none owed —
ENDORSED (vocabulary converges in the covering row; R5/R6 keep theirs).
Tracked diff: EMPTY re-verified (`git diff ITEM_BASELINE --name-only` =
plan edit alone; no `## Implementation`; 3/3 WT pins match dispatch;
`git status` 472 = 471 + this artifact's 1 untracked entry).

Observations (scratch nits, non-blocking; W1 sections left byte-intact):
O1 (Worker-2): two unqualified census phrases — "the hunt dirt touches
none of these lines" (a comment-only `# truth: ok` hunk sits ON the
rebind swap line; counts unaffected) and "zero direct constructions
outside rebind" (2 TEST constructions pin the spec-None fallback:
`test_lateral_fetch.py:657`, `test_single_parent_fetch.py:128` —
oracles, not family members). Accurate: no behavioral dirt on rule
lines; zero PRODUCTION constructions outside rebind.
O2 (Worker-2): standing-trigger paraphrases — R1 looser than R-b, R9
drops R12's third-wrap arm (covered in practice by the gate trigger: a
wrap exists only per backend subclass), R12 swaps R11's breaking event
(body-beyond-delegation) for a non-breaking one (guard-contract change).
Every trigger verified clean under BOTH wordings; sharper triggers
survive in home artifacts. No verdict impact.

Gates (re-run whole-package, shared venv, this session): `uv run mypy`
clean (119 files); `uv run basedpyright` 0/0/0; `uv run python
scripts/check_any.py` 130/90 — all match W1's reads and the baseline.
Ruff: VACUOUS (zero tracked `.py` touched; artifact is untracked
scratch `.md`). No workspace run used (source reads + grep censuses at
HEAD/WT bytes; `/tmp/f24w2` HEAD snapshots only); no slot touched.

Defects found by Worker-2: NONE (the 7 behaviors W1 lists plus the
empty-`IN` arms, spec-`None` constructions, and oracle-tool uses were
re-checked; every behavior matches its stated contract).

VERDICT: `verified` (plain — no `proof:` correctly remains).
