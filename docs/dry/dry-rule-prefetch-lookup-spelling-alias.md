# DRY review: `prefetch-lookup-spelling-alias`

Status: verified
Run: 0.0.15 2026-10-09-13

Queue item f65 (`blocks nothing`). Family `prefetch-lookup-spelling-alias`.
Nomination (input, re-derived below, not inherited): f61 sub-rule S1,
endorsed by its Worker-2 — `PrefetchLookup: TypeAlias =
str | Prefetch[str]` spelled identically at two sites; a stored-entry-shape
change moves both; owner TBD, candidate `_queryset_private`.

## System trace

The rule is the Django prefetch-entry vocabulary: one
`QuerySet.prefetch_related` lookup is a plain lookup path or a `Prefetch`
object. Pre-change it had two independently maintained named definitions,
both under `if TYPE_CHECKING:`, both spelled
`PrefetchLookup: TypeAlias = str | Prefetch[str]`:

- `django_strawberry_framework/optimizer/plans.py:63` (WT; `:62` at HEAD),
  commented "One ``QuerySet.prefetch_related`` lookup: a plain lookup path
  or a ``Prefetch``."
- `django_strawberry_framework/utils/_queryset_private.py:31` (WT; `:24` at
  HEAD), commented "One ``prefetch_related`` lookup as Django stores it: a
  lookup path or a ``Prefetch``."

The second spelling was introduced by `f2f18ba6` (verified ancestor of
HEAD), which created `_queryset_private.py` as a new file carrying the
alias at what is now HEAD `:24`. A lower module cannot import down from
`utils` to `optimizer`, so the new module spelled its own alias; the
nomination's structural claim checks out.

Connected behavior examined:

- The f61 adapter `plans.py::_consumer_prefetch_lookups` converts the
  owner's `tuple[PrefetchLookup, ...]` to the consumer's
  `list[PrefetchLookup]` by a bare `list(...)` with no element mapping:
  the two aliases already denote one value domain, or the adapter's
  contract breaks.
- Plan entries flow into Django unconverted: `plans.py:342`
  (`queryset.prefetch_related(*self.prefetch_related)`),
  `plans.py:1496` (`prefetch_related(*keep)`), and
  `walker.py:1544` (`.prefetch_related(*queryset_prefetch_lookups(inner))`).
- Django (`django/db/models/query.py`, installed 6.1.2) stores what it
  accepts unconverted: `QuerySet.prefetch_related` validates each lookup
  (`Prefetch` or `str`, via `.split`) then concatenates the same tuple
  (`clone._prefetch_related_lookups + lookups`, `:1858`); `__init__`
  sets `()` (`:375`); `prefetch_related(None)` resets to `()`.
  Accept domain == store domain by construction.
- django-stubs (`django-stubs/db/models/query.pyi`) spells the accept
  domain as `*lookups: str | Prefetch[_LookupT, _PrefetchedQuerySetT,
  _ToAttrT]` (`:225`, `:279`), declares `Prefetch` generic over three
  covariant TypeVars with the 2nd/3rd defaulted (`:24-29`), and declares
  `_prefetch_related_lookups` zero times — the stored type is
  package-owned vocabulary over undeclared Django state, exactly as the
  `_queryset_private` module docstring claims.
- `tests/optimizer/test_plans.py:102` pins the domain boundary from the
  hostile side: `object()` as a prefetch entry is "deliberately impossible
  for generated plans".
- `tests/base/test_init.py::test_every_module_imports_without_django_stubs_ext_patch`
  and `::test_annotations_evaluate_without_django_stubs_ext_patch` pin the
  `TYPE_CHECKING` placement: an eager `Prefetch[str]` at module level
  raises `TypeError` in a consumer process the stubs patch never reached.
  The consolidation keeps the alias under `TYPE_CHECKING` at the owner
  and imports it under `TYPE_CHECKING` at every consumer.

Consumers pre-change: `plans.py` (17 `PrefetchLookup` mentions: the
`prefetch_related` field, `_lookup_path`, `_prefetch_indexed_list`,
`append_prefetch_unique`, `_consumer_prefetch_lookups`,
`_optimizer_can_absorb`, `_diff_prefetch_related`,
`_lookup_paths_from_parts`, `_prefetch_lookup_paths`, plus locals and
casts), `walker.py` (TYPE_CHECKING import + 3 casts), `nested_fetch.py`
(TYPE_CHECKING import + 1 cast), and the owner's own
`queryset_prefetch_lookups` / `set_queryset_prefetch_lookups` signatures.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched. The `Prefetch[`
   census over package + tests + examples finds hits only in
   `optimizer/hints.py`, `optimizer/plans.py`,
   `utils/_queryset_private.py`, `utils/querysets.py`, and three test
   files. The filters/orders/mutations/forms/`rest_framework`/types
   flavors define no prefetch-entry vocabulary. The `querysets.py`
   hit is `_SealedPrefetch` (R3); the `hints.py` hit is `_PrefetchAny`
   (R2). No flavor re-spells this union in local vocabulary.
2. **Sync/async twins.** Inapplicable with reason: a type alias has no
   execution and no await boundary; both spellings sit under
   `TYPE_CHECKING` and are erased at runtime, so no twin can exist.
3. **Derived rather than repeated knowledge.** Searched. No site
   derives the union (`Union[` spellings: zero; reversed
   `Prefetch | str` order: zero; `get_args` over the alias: zero —
   the only `get_type_hints` traffic is `hints.py`'s documented
   runtime-fallback contract, R2 territory). The two sites spell it
   identically. Test-local `list[str | Prefetch[str]]` annotations
   (`test_plans.py:345`, `:367`) are anonymous oracle annotations,
   not named definitions (R4). `_PrefetchAny` and `_SealedPrefetch`
   are narrower/different contracts (R2/R3).
4. **Inverse / round-trip pairs.** Inapplicable with reason: a
   vocabulary type, not a codec; there are no encode/decode halves.
   (The read/write halves of the stored lookups live under f61's
   read rule, already consolidated.)
5. **Contracts restated in another medium.** Tests compose the
   vocabulary (consumers and oracle-local annotations, listed in F1,
   not counted). `test_init.py` docstrings project the
   `TYPE_CHECKING` placement rationale. No spec, glossary, or README
   cites `PrefetchLookup` (grep over `docs/` + `examples/` hits only
   this cycle's own `dry-0_0_15.md`, f61, and f62 artifacts —
   projections of in-flight work, not contract sources).
6. **Enforcement by omission.** The family enumerates every
   prefetch-entry-typed site (### Enumeration). Pre-change, `plans.py`
   was the one member not composing the owner; this item closes that
   gap. Post-change every member composes the single spelling. No
   behavior defect under this axis.

### Enumeration

Instruments (all run at WT HEAD `23b5f421` + worktree):

- `rg -n "PrefetchLookup" --type py .` — 28 hits, 5 files
  (`plans.py` 17, `_queryset_private.py` 3, `walker.py` 4,
  `nested_fetch.py` 2, `test_plans.py` 2).
- `rg -n "Prefetch\[" --type py django_strawberry_framework/ tests/
  examples/` — package hits only at `hints.py:59`, `plans.py:63`,
  `_queryset_private.py:31`, `querysets.py:135`; test hits at
  `test_walker.py:141,143`, `test_plans.py:345,367`, plus
  `test_init.py` prose (`:546`, `:560`).
- Evasion sweeps: `Union[.*Prefetch`, reversed `Prefetch | str`,
  `: Prefetch[ ,)]`, `Sequence[Prefetch`, `list[Prefetch`,
  `tuple[Prefetch`, `plans.Prefetch`, `from .*plans import` +
  bare `Prefetch` — all zero outside the homed sites.

Every hit homed:

| # | Site | Home |
|---|---|---|
| 1 | `_queryset_private.py:31` alias spelling | F1 owner definition (kept) |
| 2 | `_queryset_private.py:83,92` read/write signatures | F1 owner-adjacent consumers |
| 3 | `plans.py:63` alias spelling | F1 second definition -> import |
| 4 | `plans.py` 16 remaining mentions (field, 9 signatures, locals, casts) | F1 consumers (unchanged text) |
| 5 | `walker.py:76` import + `:1166,:1192,:1429` casts | F1 consumers (import retargeted) |
| 6 | `nested_fetch.py:99` import + `:358` cast | F1 consumers (import retargeted) |
| 7 | `plans.py:40` runtime `Prefetch` import | F1 collateral: sole code use was the alias (AST proof: exactly one `Name('Prefetch')` load at `:63`; zero `plans.Prefetch` readers; zero re-export importers) -> dropped |
| 8 | `hints.py:59` `_PrefetchAny` | R2 (narrower + runtime leg) |
| 9 | `querysets.py:135` + `:2458` `_SealedPrefetch` | R3 (rebuilt-Prefetch contract) |
| 10 | `plans.py:67` `OrderEntry` (+ `nested_fetch.py` import) | R1 (no storage counterpart) |
| 11 | `test_plans.py:345,367` inline `list[str \| Prefetch[str]]` | R4 (oracle annotations) |
| 12 | `test_walker.py:141,143` `list[Prefetch[str]]` helper | R4 (Prefetch-only test helper) |
| 13 | `test_plans.py:102` comment + `test_init.py:546,560` prose | projections |
| 14 | `docs/dry` S1/split mentions (f61, f62, plan) | projections (this cycle's own) |

No third named spelling exists. Post-change the union-shape census
pins exactly one spelling (the gate, F1).

### Challenges

- C1 — Django admits a new stored entry kind (a third member beside
  `str`/`Prefetch`): the owner alias must widen (reads return it),
  and the consumer alias must widen identically (the f61 adapter
  returns those same entries; `_lookup_path` /
  `_prefetch_lookup_paths` must handle the kind; reconciliation
  compares consumer entries against plan entries). Count 2 -> 1.
- C2 — django-stubs revs the `Prefetch` generics (arity, covariance,
  or defaults of `_LookupT`/`_PrefetchedQuerySetT`/`_ToAttrT`): both
  `Prefetch[str]` spellings move together — both rely on the
  stubs-covariance assumption `hints.py` documents ("the string-lookup
  form with its defaults is the universal one"). Count 2 -> 1.
- C3 — Django narrows the domain (one member deprecated and removed):
  the owner narrows (stored shape) and the consumer narrows (the
  walker must stop emitting, and reconciliation must stop accepting,
  the removed member). Count 2 -> 1.
- S-a — accept-vs-store split (posit a change moving one alone):
  considered and weighed. It does not hold today: Django
  concatenates its inputs unconverted (`query.py:1858`), so the
  accept domain and the store domain are the same objects, and the
  f61 adapter's mapping-free `list(...)` conversion already bets the
  consolidation on that identity. Recorded as the reconsideration
  trigger: if Django ever normalizes between accept and store,
  `plans.py` regrows an accept-domain spelling.
- S-b — plans-as-optimizer-vocabulary-hub (f61 Worker-2's weighing
  instruction): weighed. `plans.py`'s module docstring owns the plan
  shape, not optimizer-wide type vocabulary; the `walker` /
  `nested_fetch` imports from `plans` are proximity imports, not a
  designed hub. Principle 7 prefers the stated-responsibility owner:
  "Each one is spelled here once, under the type Django stores."
  The checker corroborates: basedpyright refuses the re-export
  (`reportPrivateLocalImportUsage`, forcing direct composition —
  recorded under Implementation), so the hub shape is not even
  expressible under this repo's gates.

## Findings

### F1 — `PrefetchLookup` alias twin (CONFIRMED, consolidated 2 -> 1)

- **Contract + variation.** The Django prefetch-entry domain:
  `str | Prefetch[str]`. Varies on member set (C1/C3) and member
  parameterization (C2). The name is stable shared vocabulary.
- **Sites + roles.** Two definitions pre-change (#3 and #1 in
  ### Enumeration); consumers #4/#5/#6; oracles #11/#12 (listed, not
  counted); projections #13/#14 (listed, not counted).
- **Challenges.** C1/C2/C3 count 2 -> 1; S-a/S-b weighed with the
  S-a trigger recorded above.
- **Owner + lifetime.** `utils/_queryset_private.py`: dependency
  direction (utils is importable from optimizer; the reverse edge
  would invert the layering — the reason `f2f18ba6` spelled its
  own); existing stated responsibility (the "spelled here once"
  module); colocation with the f61 read/write owner (the type lives
  with the functions that produce and consume it). No lifetime
  fields: a type alias is erased at runtime, not a stored
  derivation.
- **Migration.** `plans.py` deletes its spelling and imports the
  owner's under `TYPE_CHECKING`; its runtime `Prefetch` import is
  dropped (sole code use was the alias); `walker.py` and
  `nested_fetch.py` import the owner directly (checker-forced, see
  Implementation). `_queryset_private.py` is byte-untouched.
- **Distinct behavior.** None behavioral: the entire change is
  `TYPE_CHECKING`-erased except the dropped unused import, whose
  zero-reader sweeps (#7) prove unobservable. `OrderEntry`,
  `_PrefetchAny`, `_SealedPrefetch`, and the test-local unions stay
  separate (R1-R4).
- **Behavioral proof.**
  - Static-reviewed: import moves + alias deletion under
    `TYPE_CHECKING`; the dropped runtime import has zero importers
    and zero attribute readers (two zero-hit sweeps).
  - Execution-verified: 2 new gate tests green; `test_plans.py`
    125/125 + `test_walker.py` + `test_nested_fetch.py` 343/343;
    both `test_init.py` unpatched-process guards green;
    basedpyright + floor 0/0; truthful-reads 0 errors; failability
    3/3 pinned (each mutation fails exactly its declared row while
    the sibling row stays green). Run ids under Implementation.
- **Structural gate.** `TestPrefetchLookupSingleOwner`: an exact
  union-shape AST census over the package (exactly one
  `str | Prefetch[str]` spelling, at the owner) plus a composition
  pin (`plans.py` imports the name from the owner). Negative
  control: the hand-copy mutation (entry A) is behavior-preserving
  — every behavioral oracle passes it — and fails exactly the
  census row. Born green on the post-change tree (positive control
  in the same runs).
- **Coupling.** None: `TYPE_CHECKING`-only; no generated slots; no
  cycles (`_queryset_private` imports no optimizer module).
- **Freshness.** Fingerprints (WT / HEAD / ITEM_BASELINE
  `841e659c`):

| File | WT | HEAD | BASE |
|---|---|---|---|
| `optimizer/plans.py` | `37e0e789` | `6f2d0c70` | `39713c65` |
| `optimizer/walker.py` | `da114199` | `bc6bc969` | `57ab6770` |
| `optimizer/nested_fetch.py` | `67b69ebc` | `c2ccc321` | `b4c30994` |
| `utils/_queryset_private.py` | `a26a8d43` | `ff8b2b46` | `a26a8d43` |
| `tests/optimizer/test_plans.py` | `a8e5dbac` | `fe606e15` | `832d0b55` |

  Searched populations: the three census instruments + evasion
  sweeps above (whole package + tests + examples). Contract
  sources: Django `query.py` (`:375`, `:1858`, `Manager`
  `:2462-2464`), stubs `query.pyi` (`:24-29`, `:225`, `:279`,
  zero `_prefetch_related_lookups`), `f2f18ba6` (verified HEAD
  ancestor). Excluded modules: every `.py` under the package not
  in ### Enumeration, on the strength of the zero-hit sweeps.

### R1 — `OrderEntry` (rejected; no storage counterpart)

`plans.py:67` owns the connection-order vocabulary
(`str | F | Expression`) for `QuerySet.order_by` + `Window`
`order_by`. It is optimizer-specific: no Django-storage
counterpart exists in `_queryset_private`, and it is already
single-owned. Contract difference: order entries vs prefetch
entries. Trigger: `_queryset_private` gains ordering-storage
vocabulary. Durable home: the alias's own comment (unchanged).

### R2 — `_PrefetchAny` (rejected; narrower contract + runtime leg)

`hints.py:59` is `Prefetch`-object-only (no `str` member) with a
runtime fallback (`_PrefetchAny = Prefetch`) for
`typing.get_type_hints(OptimizerHint)`; it types hint-held and
generated `Prefetch` parameters (`walker.py:1476,1510,1549`).
Contract difference: a `Prefetch` object vs a lookup that may be a
bare string, plus a runtime leg the erased alias must not grow.
Trigger: the hint prefetch parameter widens to the entry union —
then it composes the owner. Durable home: the existing
`hints.py` covariance comment (unchanged).

### R3 — `_SealedPrefetch` (rejected; rebuilt-Prefetch contract)

`utils/querysets.py:135` is a fully-parameterized
`Prefetch[str, models.QuerySet[models.Model], str]` — a `Prefetch`
as the seal rebuilds it, not the entry union. Contract difference:
one reconstructed object shape vs the accepted/stored domain.
Trigger: seal output widens to bare strings. Durable home: the
existing "as the seal rebuilds it" comment (unchanged).

### R4 — test-local inline unions (rejected; oracle annotations)

`test_plans.py:345,367` (`list[str | Prefetch[str]]`) and
`test_walker.py:141,143` (`list[Prefetch[str]]`) are anonymous
local annotations in oracle code, not named definitions: moving
the rule does not force them to move (they change only if their
test constructs a new kind). Listed, not counted. Trigger: tests
grow a named alias for the union — then it composes the owner.

## Defects

None found. No non-duplication defect surfaced while tracing; the
basedpyright re-export refusal met during implementation is a
migration constraint (recorded below), not a defect.

## Pending execution

None. Every proof executed in the workspace copy (run ids under
Implementation); the entry-authorized focused run executed in the
shared tree. `sharded` / `pg` cells are inapplicable by
construction — the change is `TYPE_CHECKING`-erased (no database,
alias, or dialect surface exists at all) and the gate tests parse
source without touching a database — for Worker-2's judgment.

## Judgment

CONFIRM F1: one rule, one owner. `PrefetchLookup` is defined once
in `utils/_queryset_private.py`; `plans.py`, `walker.py`, and
`nested_fetch.py` compose it by name. Production net: one
definition removed across a 4-file touch (owner byte-untouched).
R1-R4 rejected with contract differences and triggers. No
defects. No pending execution.

## Implementation (Worker-1)

Tracked edits (item-scoped diff vs `841e659c`, 4 files, every hunk
mine — verified by `git diff 841e659c -- --name-only` plus
Worker-0's `docs/dry/dry-0_0_15.md` dispatch block, which is not
mine):

- `django_strawberry_framework/optimizer/plans.py` (+2/-3):
  deleted the `#:` comment + alias spelling; added
  `from ..utils._queryset_private import PrefetchLookup` in the
  `TYPE_CHECKING` block (alphabetical: between `..keyset` and
  `..utils.connections`); dropped `Prefetch` from the runtime
  `django.db.models` import (sole code use was the alias — AST
  proof). The runtime-import hunk edits the f61-ledgered line
  only; the adjacent hunt `truth` import line is byte-identical
  context, untouched. The `TYPE_CHECKING` hunk lands on
  BASE-clean lines.
- `django_strawberry_framework/optimizer/walker.py` (1-line
  swap): `from .plans import PrefetchLookup` ->
  `from ..utils._queryset_private import PrefetchLookup`.
  Checker-forced (below). Lands on BASE-clean lines
  (byte-verified vs `git show HEAD:`); nearest worktree hunks
  are 50+ lines away in both directions.
- `django_strawberry_framework/optimizer/nested_fetch.py`
  (+2/-1): added the owner import (alphabetical:
  between `..keyset` and `..utils.typing`); narrowed
  `from .plans import OrderEntry, PrefetchLookup` to `OrderEntry`.
  Checker-forced (below). Lands on BASE-clean lines; the file
  carries hunt-only dirt (no ledger row) and none of it is
  touched — nearest hunt hunk ends 4+ lines above the edit.
- `tests/optimizer/test_plans.py` (+84): module imports (`ast`,
  `pathlib.Path`, `django_strawberry_framework`) + appended
  `_prefetch_lookup_union_hits` walker +
  `TestPrefetchLookupSingleOwner` (census + composition pin).
  Appended past the f61-ledgered block; zero overlap. The sole
  banned-substring occurrence in added lines is the
  `"plans.py"` filename in a path literal (the module's real
  name; unavoidable and precedented by the f55 census gate) —
  no banned word in any identifier, docstring, or comment.
- `django_strawberry_framework/utils/_queryset_private.py`:
  intentionally untouched (WT blob still `a26a8d43`); its hunt
  docstring hunk is concurrent work.

Checker-forced retarget: the first shape kept `walker.py` /
`nested_fetch.py` importing through `plans` (re-export). The
workspace basedpyright run failed it:
`reportPrivateLocalImportUsage: "PrefetchLookup" is not exported
from module ".plans" — Import from
"django_strawberry_framework.utils._queryset_private" instead`
(run `dry-20261009T223009-f13969`, 2 errors). The retarget above
is what the repo's own gates demand, and it is the cleaner
principle-6 shape (every consumer composes the owner by name).
No cast, widening, or suppression was added anywhere.

Ledger rows owed at verification (4):

- `django_strawberry_framework/optimizer/plans.py` — Family
  `prefetch-lookup-spelling-alias` (f65) — `PrefetchLookup`
  spelling deleted, owner import; `Prefetch` runtime import
  dropped.
- `django_strawberry_framework/optimizer/walker.py` — Family
  `prefetch-lookup-spelling-alias` (f65) — `PrefetchLookup`
  import retargeted to the owner.
- `django_strawberry_framework/optimizer/nested_fetch.py` —
  Family `prefetch-lookup-spelling-alias` (f65) — `PrefetchLookup`
  import retargeted to the owner; `OrderEntry` import narrowed.
- `tests/optimizer/test_plans.py` — Family
  `prefetch-lookup-spelling-alias` (f65) —
  `TestPrefetchLookupSingleOwner` (2 rows) +
  `_prefetch_lookup_union_hits`.

Proofs (all through `heavy`; workspace address
`dry/aliasf65/consolidate`, slot-2; shared tree unmoved during
each run per provenance headers):

- `run ... -- pytest -n0
  tests/optimizer/test_plans.py::TestPrefetchLookupSingleOwner
  --no-cov -q` -> 2 passed (`dry-20261009T222945-87e9f8`).
- `run ... -- pytest -n0 tests/optimizer/test_plans.py --no-cov
  -q` -> 125 passed (`dry-20261009T222952-5138a1`).
- `run ... -- pytest -n0 <the two test_init.py unpatched-process
  guards> --no-cov -q` -> 2 passed
  (`dry-20261009T223000-f88b21`).
- `run ... --fresh -- basedpyright` -> 0 errors, 0 warnings
  (`dry-20261009T223211-c33184`, post-retarget).
- `run ... -- basedpyright -p pyrightconfig.floor.json` -> 0/0/0
  (`dry-20261009T223325-4d8483`).
- `run ... -- python scripts/check_truthful_reads.py --check` ->
  120 files, 0 errors (`dry-20261009T223438-f98f80`).
- `run ... -- pytest -n0 tests/optimizer/test_plans.py
  tests/optimizer/test_walker.py
  tests/optimizer/test_nested_fetch.py --no-cov -q` -> 343 passed
  (`dry-20261009T223441-c2b2a6`).
- `prove dry/aliasf65/consolidate
  $TMPDIR/aliasf65-manifest.json` -> 3/3 pinned, restores
  byte-proved (`dry-20261009T223516-52a9e5`): hand-copy control
  fails exactly the census row; dropped composition fails
  exactly the composition row; corrupted owner value fails
  exactly the census row. Each entry's pre-mutation scope was 2
  passed; each failure is a single exact row with its sibling
  green, which is the precise failability shape for a
  two-assertion gate (a broader failing set would indicate
  bleed, not strength).
- Shared tree (the one authorized focused run): `pytest -n0
  tests/optimizer/test_plans.py::TestPrefetchLookupSingleOwner
  --no-cov -q` -> 2 passed.
- `ruff check` + `ruff format --check` clean on all 4 touched
  paths; `check_trailing_commas.py` 0 violations on all 4.

Not run, with reason: `check_public_types.py` — the alias is
`TYPE_CHECKING`-only in both modules (absent at runtime, hence
outside `--verifytypes` scope); the gate is green at HEAD with
the alias present, so it provably does not measure it, and no
runtime-public symbol was touched. `sharded` / `pg` cells —
inapplicable by construction (above); no maintainer word was
sought. Full suite — never (Final gate owns it).

No commit. Item-scoped diff is exactly the 4 files above; status
count 522 at dispatch, +1 for this artifact on write.

## Independent verification (Worker-2)

Recorded before opening `## Findings` (pass 1). All states
fingerprinted from this tree: HEAD `23b5f421`, item baseline
`841e659c3ce98bde92b9d742ac67bd1bbfddfde3`, WT as read.

### Own trace

Rule as I state it: one `prefetch_related` entry as Django
accepts and stores it — a lookup path or a `Prefetch`. Django
concatenates `prefetch_related(*inputs)` onto
`_prefetch_related_lookups` unconverted, so the accepted and the
stored vocabularies are the same objects.

Sites found (whole-package sweeps, current bytes):

- D1 (definition, pre-change only):
  `django_strawberry_framework/optimizer/plans.py::PrefetchLookup`
  (`PrefetchLookup: TypeAlias = str | Prefetch[str]`, BASE line 63,
  HEAD line 63, inside `if TYPE_CHECKING`). Deleted by the item.
- D2 (definition, all three states):
  `django_strawberry_framework/utils/_queryset_private.py::PrefetchLookup`
  (line 31, identical spelling, inside `if TYPE_CHECKING`).
  WT blob `a26a8d43` == BASE blob: byte-untouched.
- Consumers (annotation / cast-string positions only, all
  runtime-erased): `plans.py` (~14: `_lookup_path`,
  `_prefetch_indexed_list`, `OptimizationPlan.prefetch_related`,
  three `cast("...")` strings, `_consumer_prefetch_lookups`,
  `_optimizer_can_absorb`, `_diff_prefetch_related`,
  `_lookup_paths_from_parts`, `_prefetch_lookup_paths`);
  `walker.py` (3 `cast("...")` strings);
  `nested_fetch.py` (1 `cast("...")` string). BASE walker /
  nested_fetch imported D1 from `.plans`; WT imports D2 from
  `..utils._queryset_private`.
- Near-misses, not definitions of this rule:
  `optimizer/hints.py::_PrefetchAny` (`Prefetch[str]` only, plus a
  runtime `else` leg); `utils/querysets.py::_SealedPrefetch`
  (`Prefetch[str, QuerySet, str]`, the seal-rebuilt vocabulary) and
  its `str | _SealedPrefetch` compositions;
  `optimizer/plans.py::OrderEntry` (disjoint union).

Missed-third-spelling sweeps (each over the full package, WT):

1. Name `PrefetchLookup`: 1 definition + 3 by-name imports +
   annotation uses; no other `X = ...` binding.
2. Regex `Prefetch\[str\]`: D2 plus `_PrefetchAny` (Prefetch-only).
3. AST `BitOr` mentioning `Prefetch`: D2, `_PrefetchAny | None`,
   `_SealedPrefetch | None`, `str | _SealedPrefetch` (x2) — every
   non-owner hit composes a narrower alias by name; no swapped
   `Prefetch[str] | str`, no inline union annotation.
4. AST `Union[...]` / `Optional[...]` mentioning `Prefetch`: none.
5. String constants mentioning `Prefetch` with `str` + `|`: one
   module docstring (prose) + one `cast` string composing
   `_SealedPrefetch` by name.
6. `from *plans import Prefetch` / `*`, and `plans.PrefetchLookup`
   attribute reads, repo-wide (package + tests + examples +
   scripts): none.

### Own change challenges (definition counts)

- Stored-entry shape gains a member: pre 2 (D1 + D2), post 1 (D2).
- Entry vocabulary narrows to `Prefetch`-only: pre 2, post 1.
- `Prefetch[str]` parameter restyle: pre 2, post 1.
Consumers, oracles, projections move with the owner by name and
are listed, not counted.

### Owner I would choose

`utils/_queryset_private.py`, for dependency direction plus
responsibility: D2's module already binds the alias in its own
signatures (`queryset_prefetch_lookups`,
`set_queryset_prefetch_lookups`), so owning it in `plans.py`
would force a utils-to-optimizer import, reversing the layering
`f2f18ba6` established (optimizer already imports runtime helpers
from `_queryset_private` at `walker.py` and `nested_fetch.py`);
and the module's stated job is spelling each Django-private
attribute "once, under the type Django stores". Shape:
compose-by-name direct imports in each consumer; no re-export
through `plans` (indirection with no remaining consumer needing
`plans` as the surface).

### Prefetch-drop pre-verification

BASE `plans.py` AST: bare `Name(id="Prefetch")` nodes at exactly
[line 63] (the deleted alias); WT: zero bare `Name` / `Attribute`
nodes; remaining `Prefetch` mentions are docstrings/comments plus
the substring inside `PrefetchLookup`. Both alias spellings lived
in `TYPE_CHECKING` blocks pre-change, so the alias never existed
at runtime on either side; `plans.py` carries
`from __future__ import annotations`, and every walker /
nested_fetch use is an explicit `cast("...")` string. The dropped
runtime `Prefetch` import has no remaining reader.

### Findings reconciliation (every difference)

Rule, sites, roles, counts, owner, shape: AGREE. My D1/D2 are
their #3/#1; my consumers match #4/#5/#6; my near-misses match
R1/R2/R3 (+ R4 oracle annotations, which my package-only sweeps
did not cover but I verified at `test_plans.py` WT `:348,:370`
and `test_walker.py:141,143`). My three challenges cover the
same axes as C1/C2/C3 (member set both directions +
parameterization); S-a is my Django-concatenation identity with
the same trigger; S-b matches my proximity-import weighing.
Owner and direct-compose shape identical, same dependency
reasoning.

1. Enumeration state + the unhomed hit (CORRECTED HERE, no
   finding affected). Their "28 hits, 5 files" is the BASE
   (pre-edit) census, not post-change WT: BASE `test_plans.py`
   has 2 hits (the `:102` comment homed in row 13 + the
   f61-ledgered `TestConsumerPrefetchLookups` class name, BASE
   `:517`). Post-change WT has 30: +2 are the gate's own class
   name + `"PrefetchLookup"` string literal (self-hits outside
   the package-only census population). The f61 class hit was
   COUNTED but never HOMED: its home is inert name substring —
   its body carries zero `PrefetchLookup` hits (verified by
   region `rg`), it is f61-ledgered and untouched by this item
   (no BASE->WT hunk there), and a class name cannot spell an
   alias. Likewise the cited line numbers are BASE-state:
   `nested_fetch.py:99/:358` (WT: owner import `:97`, plans
   import `:100`, cast `:359`), `OrderEntry :67` (WT `:66`),
   R4 `:345,:367` (WT `:348,:370`, +3 from the new imports),
   row 13 `:102` (WT `:105`). All resolve to a real state; the
   instrument header should have said pre-edit/BASE. Future
   re-runs: expect 30 at post-change WT, 28 at BASE.
2. Prefetch-drop: AGREE, proof reproduced exactly — BASE AST
   bare `Name("Prefetch")` at `[63]` only, WT zero (no `Name`,
   no `Attribute`), zero `from *plans import Prefetch` / `*`
   importers and zero `plans.PrefetchLookup` attribute readers
   repo-wide (package + tests + examples + scripts).
3. Checker-forced retarget: AGREE, refusal reproduced verbatim
   in my copy (revert walker to the plans re-import):
   `"PrefetchLookup" is not exported from module ".plans"` --
   `Import from
   `"django_strawberry_framework.utils._queryset_private"`
   instead (reportPrivateLocalImportUsage)`, exit nonzero
   (`dry-20261009T225205-549241`). The diagnostic prescribes
   the shipped shape. The rule is on under `typeCheckingMode =
   "all"` (absent from the pyproject off-list); `reportPrivateUsage
   = "none"` is a different rule and does not cover it.
4. Banned substring: ALLOWED, no rewording exists. Added-lines
   sweep: `plan` x1 (the disclosed `"plans.py"` path literal),
   `audit`/`sweep`/`restored`/`hardening`/`previously`/`worker`/
   `grader`/`feedback` x0. The pin must name the module it pins
   and the module is named `plans` — even an import-form
   reference (`optimizer.plans`, `plans.__file__`) contains the
   substring. Filename literal naming the test subject, not
   process provenance; precedented by the f55 exact-match AST
   census (`tests/utils/test_connections.py::test_unset_identity_comparisons_live_only_at_named_separations`,
   path literals in the expected list).
5. R1–R4 triggers: ACCEPTED, with one reading pinned. R3's
   trigger ("seal output widens to bare strings") refers to the
   `_SealedPrefetch` ALIAS widening from Prefetch-only — the
   use-site `str | _SealedPrefetch` unions already include
   pass-through strings and are outside the finding's subject.
   (Those use-site unions are a possible future family of their
   own — different member type, out of this item's rule.)
6. Test tier: `tests/` CORRECT. The consolidation is
   runtime-erased (both spellings `TYPE_CHECKING`-only pre and
   post; the one runtime delta is a zero-reader import binding),
   so no live `/graphql` query can distinguish the trees; the
   static census is the strongest tier that observes the rule.
   No oracle reads from the owner: both rows assert AST text
   against literal expectations. No fixture gap exists (nothing
   to fixture), so no `## Defects` entry is owed.
7. Observable equivalence (principle 8): PROVED. Import graph:
   three added edges, all `TYPE_CHECKING`-only; one removed
   runtime binding with zero readers (item 2). Exceptions,
   query/transaction effects, cancellation, observation points:
   untouched — no executable statement changed. `get_type_hints`
   / `get_args` traffic: my repo sweep finds no evaluation of
   any `plans.py` annotation (the `get_args` sites operate on
   unrelated annotations), corroborating the axis-3 zero.
8. Gates re-run in my copy (`dry/aliasf65/verify-1`, slot-3,
   copy fresh, shared unmoved): gate-2 tests 2 passed
   (`dry-20261009T224801-41167a`); basedpyright 0/0/0
   (`dry-20261009T224807-c8a30d`); floor 0/0/0
   (`dry-20261009T224921-6dac2e`); truthful-reads 120 files 0
   errors (`dry-20261009T225034-745b19`). Shared tree: gate-2 2
   passed (the one authorized focused run). `ruff format --check`
   + `ruff check` clean on all four touched paths (the COM812
   notice is a pre-existing config warning, not a failure).
   Consolidation type-checks with no new cast, widening,
   suppression, or `Any` (verified by diff content); new test
   symbols all carry docstrings; no overrides added.
9. Failability re-derived (my own driver, mutations restored
   byte-identical, copy fresh throughout): (A) hand-copy second
   union in `plans.py` -> full `test_plans.py` fails EXACTLY the
   census row, 124 behavioral tests pass
   (`dry-20261009T225132-cad19c`); (B) dropped composition import
   -> exactly the composition row fails, sibling green
   (`dry-20261009T225145-9868a9`); (C) corrupted owner value ->
   exactly the census row fails, sibling green
   (`dry-20261009T225155-15c85f`). Each gate fails its negative
   control with no bleed.
10. Freshness: all 15 table blobs re-verified byte-exact
    (`plans.py` WT `37e0e789` / HEAD `6f2d0c70` / BASE
    `39713c65`; `walker.py` `da114199` / `bc6bc969` /
    `57ab6770`; `nested_fetch.py` `67b69ebc` / `c2ccc321` /
    `b4c30994`; `_queryset_private.py` `a26a8d43` / `ff8b2b46` /
    `a26a8d43`; `test_plans.py` `a8e5dbac` / `fe606e15` /
    `832d0b55`). Searched populations and contract sources as
    listed; excluded modules stand on the zero-hit sweeps, which
    my six independent sweeps corroborate.
11. Attribution re-verified by diff content (not status): the
    item diff vs `841e659c` is exactly the 4 claimed files plus
    Worker-0's plan block; no new `.py` anywhere (untracked
    `.py` files are all hunt concurrent work). `plans.py`
    runtime hunk edits the f61-ledgered `django.db.models` line
    only, hunt `truth` line byte-identical context;
    `TYPE_CHECKING` hunk touches only alias lines + insertion
    between stable imports. Walker hunk 56+ lines from any dirt
    (HEAD hunk at the same lines contains ONLY the swap).
    Nested HEAD hunk at the same lines contains ONLY the item
    hunk; the hunt hunk ends 4+ lines above. `test_plans.py`
    BASE dirt is 100% f61-ledgered; item hunks (imports + EOF
    append) disjoint. `_queryset_private.py` BASE->WT empty
    (its one HEAD hunk is hunt docstring dirt).
12. `sharded` / `pg` inapplicable-by-construction: ENDORSED.
    The target's code path reaches no database, alias, or
    dialect decision (item 7); the gate tests parse source
    without touching a database. `check_public_types.py` skip:
    ENDORSED — no runtime-public symbol touched (alias absent
    at runtime both sides), and the dropped binding was never an
    export. `## Pending execution` empty: CONFIRMED, nothing
    owed. Coupling none: CONFIRMED (`_queryset_private`
    imports no optimizer module). `## Defects` none: AGREE, and
    I add none.

Verdict rationale: the item is complete. The enumeration blemish
(item 1) is finding-neutral and its correction is durable in this
section of the same artifact; a resubmission round-trip would
change no production byte, test, or decision. Status set to
`verified` (plain — no `proof:` entry remains).

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
