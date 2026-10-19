# DRY review: `queryset-iterable-class-access`

Status: verified
Run: 0.0.15 2026-10-09-13
Item: Family `queryset-iterable-class-access` (queue item f67, run 13)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `8758cc9b04b596a9d759246494559f54feae7dbd` (resolves as commit)
HEAD: `23b5f42106ffd14805936560f5155dd90d7568da` (unmoved the whole item)
Slot: slot-2 `dry/f67-iterable-class/consolidate`
(`~/dry/ws/c3af387fc1324a21/dry/slots/slot-2`)

## System trace

The family target is access to Django's
`QuerySet._iterable_class` slot: the row-iterable class Django sets
to `ModelIterable` in `QuerySet.__init__` (installed 6.1.2,
`query.py:378`) and repoints on `values()` / `values_list()`. The
nomination (folder FAM-3, CC-3 row text) was re-derived fresh at
current bytes. The spelling count re-derives exactly, count-2, both
committed lines (pins shifted +1 in `querysets.py` under f66's
landed import line; the `nested_fetch.py` pin is stable):

- `utils/querysets.py:3974` (nomination `:3973`)
  `sealed._iterable_class = iterable` -- the seal rebuild write:
  a typed write of seal-validated state onto the framework-owned
  rebuild, sitting among five owner-composed sibling writes
  (`:3975` / `:3977` / `:3981` / `:3982` / `:3992`).
- `optimizer/nested_fetch.py:151`
  `iterable_class = getattr(queryset, "_iterable_class",
  ModelIterable)` -- the classifier probe: the last of six
  `getattr`-with-default probes in
  `::unwindowable_child_queryset_reason`, whose parameter is
  typed `object` (`:103`) and whose body never narrows it.

The CC-3 adjudication the folder explicitly deferred
(defensive-probe vs typed-access, "on the actual gate mechanics
at the read site") resolves the opposite way from f66: this
read half is a genuine defensive probe, so the nominated
count-2 is two contracts counting 1+1, not one rule counting
2. The mechanical proof is f66's inverted. f66's read sat
below `normalize_query_source`, which returns every
non-queryset early and narrows the survivor through a
discriminated union -- proved by the direct owner call
type-checking clean. Here there is no gate: `:142`-`:150`
return reasons only, so a non-queryset falls through every
probe (`.query` answers `None`, each `Query` probe answers
its default) and reaches `:151`, where the `ModelIterable`
default fires and the function returns `None`. The default
arm is live BY CONSTRUCTION of the fall-through chain -- the
chain routes unknown shapes to defaults, which is what
`getattr`-with-default chains do. Converting `:151` to a
strict typed read would need new narrowing the replaced code
does not need (banned) and would change declared-domain
behavior (`None` -> `AttributeError` on non-queryset input --
principle 8). The owner charter agrees with the split in its
own words (`_queryset_private.py:11-12`: the functions "suit
a queryset the framework built, sealed or already proved a
``QuerySet``" -- the classifier's input is none of those).
A getter-with-default in the strict owner -- the only shape
that would preserve the probe exactly -- pushes leniency
into the fail-loud owner, the shape f61's Worker-2 rejected
(f66 record, F1 adjudication).

The honest-caller shape does not rescue typed-access: all
three call sites pass `QuerySet`-typed values (two typed
subclass signatures, one `Callable[..., QuerySet]` builder
whose hook output passes the seal). Caller-typedness held in
f66 too; f66's proof was the narrowing gate, which does not
exist here. Doubt about a default arm's deadness blocks a
conversion; only proof unblocks it.

Consequence: the typed-access rule has exactly one
definition (the seal write) -- independence, not duplication
("Count = 1 = independence"; "Token single-owned rule ≠
admission ticket"). A setter-only move of the seal write
into the owner is 1 -> 1 under every challenge below, a
one-caller wrapper principle 11 forbids extracting, and
still leaves the probe's string spelling moving under its
own contract -- so the "one edit" promise fails for this
slot regardless. The visible asymmetry with f66 (the
`_result_cache` seal write composes the owner, this one
stays inline) is the correct output of the deferred
adjudication, not an oversight: f66 moved a count-2 rule
whose read was typed-access-in-fact; here each rule counts
1. Zero-edit submission; copy untouched.

Folder pin note (record-only, not a defect): the folder's
FC-QPRIVATE "4 setters" pins (`:3974`/`:3976`/`:3980`/`:3981`)
are stale by f66's +1 shift (now `:3975`/`:3977`/`:3981`/
`:3982`, plus f66's fifth at `:3992`).

Dirt attribution by content, all vs `git show HEAD:` (HEAD
unmoved): every site line this item traces is committed
content. The probe line is diff context inside a hunt hunk
(`@@ -147,7`, whose `-`/`+` pair rewrites only the
`:152` subclass check as truth-migration); the whole-file
`querysets.py` diff carries zero `-`/`+` hits on the slot
spelling, so the seal write, snapshot key, and wording are
all committed (HEAD carries them at `:4024` / `:3835` /
`:3942`). The f66 ledger rows name `_queryset_private.py`
and `querysets.py` but touch neither f67 line (f66's seal
hunk is the `:3992` carry + the `:115` import). No ledger
row names `nested_fetch.py` for this family. Nothing was
edited, so no hunk is in any plan ledger from this item.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched. No second live
   read or write of the slot exists in any flavor: the
   package-wide literal census (### Enumeration) finds live
   spellings only at the seal write and the classifier probe,
   and the evasion sweep finds zero computed spellings. The
   `ModelIterable` census is bounded at 11 hits / 2 files
   (import + probe + subclass check in `nested_fetch.py`;
   import + comment + table + three prose (`:2723` /
   `:2934` / `:3736`) + policy gate `:3924` + local
   rebind `:3944` in `querysets.py`) --
   every hit homes to the seal or the classifier. The `:152`
   subclass check operates on the probe's local result, not
   the slot.
2. **Sync/async twins.** Inapplicable with reason: pure
   synchronous attribute access admits no async twin, and no
   `async def` reader of this slot exists.
3. **Derived rather than repeated knowledge.** Searched. The
   seal's snapshot-key read derives nothing: it reads a
   different population (the no-dispatch instance snapshot)
   under seal discipline (R1). The exact-identity helper
   (`:2446`) vs the classifier's subclass check (`:152`) is
   the one similar-looking pair found; it separates on
   contract (R3).
4. **Inverse / round-trip pairs.** The typed write has no
   typed-read inverse: the only slot read is the defensive
   probe, a different contract. No second writer exists.
5. **Contracts restated in another medium.** Tests that spell
   the slot do so to PLANT hostile state (`qs._iterable_class
   = ...`) -- setup, which must name the slot to sabotage it
   and would go circular through an owner (f66 Matrix-5
   precedent). Oracles assert behavior (fail-closed defects,
   reason strings, `None`) without reading any owner; the
   envelope oracles pin only "cannot be sealed...".
   Docstring/comment projections homed in ### Enumeration.
6. **Enforcement by omission.** The family enumerates every
   live access (### Enumeration); each access follows its own
   rule (typed write, defensive probe, seal discipline,
   error vocabulary). No member lacks a rule. No behavior
   defect under this axis.

### Enumeration

Instrument: `rg -n "_iterable_class"`
`django_strawberry_framework/` (9 hits, 3 files, current
bytes) plus an evasion sweep for computed spellings
(`getattr` / `setattr` / `hasattr` with the slot, `del` /
`pop` / `delattr`, `"iterable"` key strings). Every hit
homed:

| # | Site | Home |
|---|---|---|
| 1 | `querysets.py:3974` seal write | F1 single typed definition |
| 2 | `nested_fetch.py:151` classifier probe | F1 defensive probe (rejected half) |
| 3 | `querysets.py:3788` snapshot-key read | R1 (seal discipline, FR-7) |
| 4 | `querysets.py:3895` f-string wording | R2 (error vocabulary) |
| 5 | `querysets.py:2446` helper def + `:3893` gate call | R3 (exact-identity rule) |
| 6 | prose ×3 (`_queryset_private.py:140`, `querysets.py:2430` + `:3691`) | projections |
| 7 | evasion sweep: 0 hits (the `:151` `getattr` is the only dispatch form; no `del` / `pop` of the slot anywhere) | F1 (dispatch bounded) |

No third live-access site exists. Bare-`iterable_class`
sweep: 1 hit (the `:152` local use). Helper consumers:
`_is_django_iterable_class` 1 (`:3893`),
`_DJANGO_ITERABLE_CLASSES` 1 (`:2452`). Test/example
spellings: 5 plantings (`test_nested_fetch.py:378` /
`:385`, `test_querysets.py:491` / `:1193`,
`test_resolvers.py:1897`) + 2 prose
(`test_querysets.py:1180-1182` / `:1628`) -- setup and
oracle, Matrix-5.

### Challenges

Counts count authoritative definitions only, per rule.
"Before" is current bytes; there is no "after" (zero-edit).

- C1 (Django renames `_iterable_class`; the FAM-3 rerun).
  Moves: the seal write (typed-access rule, count 1), the
  probe string (defensive-probe rule, count 1), the snapshot
  key (seal discipline, count 1), the wording (error
  vocabulary, count 1). Rename co-movement is necessary,
  not sufficient (f66 R1/R2/R3 precedent): each moves under
  its own contract. No rule counts above 1. A setter-only
  owner move keeps it 1 -> 1 on the typed rule while the
  other three move anyway.
- C2 (Django changes the stored shape). Moves: the seal's
  validation (gate + table) under seal discipline; the seal
  write under the typed rule. The probe never moves (the
  subclass question is shape-agnostic: a non-class value
  answers `False` -> `"values"`, test-pinned). Count per
  rule: 1 -> 1.
- C3 (the non-queryset failure mode changes). Moves: the
  probe alone, under its totality contract; the seal write
  is untouched (its input is always the framework-owned
  rebuild). Count: 1 -> 1. Contrast f66 C3, where a gate
  owned this axis -- here the probe IS the totality
  contract, which is why it cannot join the strict owner.

## Findings

### F1 -- `_iterable_class` live access (REJECTED: two contracts, 1+1)

- **Contract + variation.** As nominated: one rule spelling
  the fetched-iterable slot. Re-derived: two rules sharing
  a substring. (a) Typed write of seal-validated state onto
  a framework-owned queryset -- varies on the Django-private
  spelling and the stored shape. (b) Defensive probe of an
  `object`-typed classifier input that must never raise --
  varies on the classifier's totality contract (which
  unknown shapes map to which reason-or-`None`).
- **Sites + roles.**
  - Single typed definition: the seal write
    (`utils/querysets.py:3974`).
  - Defensive probe (rejected half):
    (`optimizer/nested_fetch.py:151`).
  - Oracles: the classifier matrix
    (`test_unwindowable_child_queryset_reason_matrix`,
    incl. the CustomModelIterable-subclass -> `None` and
    hostile `"invalid"` -> `"values"` rows), the seal
    hostile-iterable rows
    (`test_injected_custom_iterable_result_fails_closed`,
    `test_unsealable_source_fails_closed`,
    `test_an_unsealable_prefetch_cache_is_refused_under_the_accessor_it_was_read_from`),
    and the seal positive-path oracle
    (`test_hostile_source_all_override_is_neutralized_by_sealing`,
    which plants no iterable)
    -- all independent literal expectations.
  - Projections: the enumeration rows 5-6, this record.
- **Challenges.** C1 no rule above 1, C2 1 -> 1, C3 1 -> 1
  (### Challenges).
- **Owner + lifetime.** No owner: nothing is consolidated.
  The read half was adjudicated defensive-probe on four
  bars (## System trace): the fall-through chain proves the
  default arm live (inverse of f66's narrowing proof); the
  owner charter's domain sentence excludes unproven input;
  strict conversion needs banned new narrowing and changes
  declared-domain behavior (principle 8); lenient-getter is
  a rejected shape. The write half stands alone (count-1
  independence); a setter-only move is 1 -> 1 plus a
  principle-11 one-caller wrapper.
- **Migration.** None (zero-edit).
- **Distinct behavior.** No behavior changes. What stays
  separate: the probe's `None`-on-non-queryset totality
  (declared `object` domain, incidental-or-intentional but
  load-bearing by declaration) vs the seal write's typed
  exactness. Recorded here.
- **Behavioral proof.** `static-reviewed`: the verdict rests
  on bytes-derived contract differences (signature, chain
  structure, charter sentence, stubs declaration), each
  re-verified first-hand. The wrong result it rejects is a
  probe conversion changing declared-domain behavior
  (`None` -> `AttributeError`) -- discharged by inspection
  of the fall-through chain, which no test needs to
  execute. Witnesses (27 green in slot-2, run ids under ##
  Judgment) confirm the traced tree is healthy; they route
  nowhere and owe no `proof:` entry.
- **Structural gate.** None, with reason: no owner exists
  for this slot, and a single-site census gate would be a
  bespoke existence test per helper, which the finding
  record forbids ("never a bespoke existence test per
  helper"). A gate becomes ownable only alongside
  an owner: while the spelling census counts one
  typed definition plus a different-contract probe,
  any gate over the spelling pins the rejection, not
  a rule.
- **Coupling.** None. Zero-edit: nothing lands,
  nothing rides, nothing blocks.
- **Freshness.** HEAD `23b5f421` (unmoved the whole
  item). WT == slot-2 byte-identical on every
  retraced input (`git hash-object`):
  `utils/querysets.py` `641b158e`,
  `optimizer/nested_fetch.py` `67b69ebc`,
  `utils/_queryset_private.py` `61527cd9`,
  `tests/optimizer/test_nested_fetch.py`
  `c96e95af`, `tests/utils/test_querysets.py`
  `0a2e52bf`, `tests/types/test_resolvers.py`
  `a6e548c3`. Call-site modules (read first-hand;
  caller-typedness never narrows the callee):
  `optimizer/nested_planner.py` `a9875bbb`,
  `optimizer/lateral_fetch.py` `995f1aa2`,
  `optimizer/single_parent_fetch.py` `bd6beb1c`.
  Population: full-package `rg` census over 121
  `.py` files (9 hits / 3 files + evasion 0) +
  `ModelIterable` census (11 / 2) + test/example
  sweep (5 plantings + 2 prose, no example hit),
  upstream `query.py` at installed Django 6.1.2 +
  `query.pyi:83` at installed django-stubs, f61/f66
  family records (precedent shapes, re-verified
  not inherited). Any fingerprint change reopens.
- **Reconsideration trigger.** A narrowing gate
  above `:151` proving `QuerySet` -- or restricting
  the declared domain from `object` -- reunites
  the read half with typed-access; until then 1+1.

### R1 -- seal snapshot-key read `:3788` (rejected; seal discipline, FR-7)

Reads the `_iterable_class` key of the instance-namespace
snapshot the seal took without dispatching consumer code
(`truth.instance_state(candidate)`, `:3782`), not the live
attribute. Under a Django rename it moves, but under the
seal's snapshot-discipline contract, not this family's
live-access rule (f66 R1 precedent; folder FR-7 home).
The C2 challenge moves it with the seal's validation,
never with the write. Trigger: the seal starts reading
live queryset attributes; that read joins F1.

### R2 -- seal wording `:3895` (rejected; error vocabulary, not access)

`f"{cls_name}._iterable_class is {detail}"` names the slot
in an `("untrusted", ...)` defect message; it reports
Django state, it does not touch it. Moves under the
error-wording contract, not the access rule (f66 R3
precedent for the split) -- and unlike f66 no oracle
pins it: zero hits for the wording in tests + examples,
the envelope oracles assert only "cannot be sealed...".
Trigger: the wording is generated from a shared
slot-name grammar.

### R3 -- exact-identity rule `:2446` + `:3893` (rejected; identity vs subclass)

`_is_django_iterable_class` answers exact identity (`is`
against `_DJANGO_ITERABLE_CLASSES`, `:2452` -- set
membership would dispatch a consumer metaclass
`__hash__` / `__eq__`), while the classifier's `:152`
check answers MRO membership (`truth.is_subclass`,
accepting a `ModelIterable` subclass as windowable).
Same slot, opposite questions: the seal refuses
anything not exactly Django's; the classifier admits
subclasses. Pinning is one-sided: classifier-side
subclass acceptance is pinned (matrix `:373`-`:379`);
the seal side pins foreign-class refusal x3 (all
`list`: `:491` / `:1193` / resolvers `:1897`); seal
subclass refusal follows from the identity bytes
(`:2452`), unpinned. Trigger: the seal adopts subclass
acceptance (or the classifier exact identity) -- a
contract change at the owner, not this item's.

## Defects

None. No non-duplication bug surfaced while tracing:
the charter sentence matches the owner body, the `:152`
subclass check matches the classifier's windowability
contract, and the folder's stale FC-QPRIVATE pins are a
record-only note (## System trace), not a defect. No
pre-existing failures: the witness scope (27 rows) ran
green on final bytes.

## Pending execution

None. Every witness executed green in slot-2 on final
bytes (run ids under ## Judgment); no `proof:` entry is
owed. No `gate:` entry is owed.

Cells: `--cell sharded` and `--cell pg` are inapplicable
by construction (Worker-2 judges): this family is an
in-memory attribute rule -- a direct slot write, a
`getattr` probe, snapshot keys, wording -- with zero
database, alias, routing, or dialect decision, zero
edits, and default-cell witnesses. The slot mechanics
relied on (Django sets `ModelIterable` in `__init__`,
`values()` repoints, `_chain` carries) hold identically
on every backend.

## Judgment

REJECTED as one rule; zero-edit. The nominated count-2
re-derived exactly at current bytes (both committed
lines), but the deferred CC-3 adjudication resolves the
read half as a genuine defensive probe on four bars --
the fall-through chain proves the default arm live, the
owner charter excludes unproven input, strict conversion
needs banned narrowing and changes declared-domain
behavior, and a lenient getter is a rejected shape --
so the spelling counts 1+1 across two contracts, not 2
under one. The write half stands alone (count-1
independence); a setter-only move is 1 -> 1 plus a
principle-11 wrapper. R1/R2/R3 are excluded on distinct
contracts with triggers. Copy untouched; tracked diff
vs ITEM_BASELINE over package/tests/examples is empty.

Witnesses (slot-2 `dry/f67-iterable-class/consolidate`,
copy fresh, HEAD `23b5f421` unmoved):
- `dry-20261010T091046-5c940a`:
  `tests/optimizer/test_nested_fetch.py` full file --
  19 passed.
- `dry-20261010T091053-86a873`: 7 seal oracles in
  `tests/utils/test_querysets.py` (all-override
  positive path, unsealable-source, injected-result,
  values-projection source, non-queryset prefetch
  child, foreign-inner-query prefetch, seal-policy
  pin) -- 7 passed.
- `dry-20261010T091105-98809b`:
  `tests/types/test_resolvers.py` prefetch-cache
  refusal -- 1 passed.

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

Verdict: revision-needed. D-1
(blocking): the record ends mid-sentence
("A gate becomes o" + a literal
truncation marker); the F1 tail, the
R1/R2/R3 records, freshness, Defects,
Pending execution and Judgment are
absent from the disk bytes. D-2: F1's
visible text states the contract
difference but no explicit
reconsideration trigger. Substance
CONCUR: the rejection stands; no
consolidation is supported (no
overturn). The repair is clerical
log-recovery, no re-trace; then a
same-verifier fast re-pass against the
fingerprints below.

Sequencing: the brief required reading
the artifact first, so blind tracing was
impossible. Mitigated throughout: every
count, pin and census below was
re-grepped first-hand at current bytes,
the load-bearing mechanics were executed
in-copy, and the f66 record was opened
only after the mechanics positions were
fixed.

### Own trace

Census `rg -n "_iterable_class"` over
the package: 9 hits / 3 files, every hit
homed independently: the seal write
(`utils/querysets.py:3974`), the
classifier probe
(`optimizer/nested_fetch.py:151`), the
snapshot-key read (`:3788`), the wording
(`:3895`), the helper def (`:2446`) +
gate call (`:3893`), prose x3
(`_queryset_private.py:140`, `:2430`,
`:3691`). Evasion sweep (dispatch
forms, del/pop/delattr, quoted key
strings, bare `iterable_class`): 0
unhomed (the only extra hit is the
`:152` local use). Tests + examples: 5
plantings + 2 prose, no example hit. No
third live-access site exists.

Roles: the seal write is the single
typed definition (seal-validated state
onto the framework-owned rebuild, among
five owner-composed sibling writes
`:3975` / `:3977` / `:3981` / `:3982` /
`:3992`, all pins exact). The probe is a
defensive probe under a different
contract:
`nested_fetch.py::unwindowable_child_queryset_reason(queryset:
object)` (`:103`) runs six
getattr-with-default probes
(`:142`-`:151`) with zero narrowing --
`:142`-`:150` return reasons only -- so
a non-queryset falls through to the
`ModelIterable` default and answers
`None` (`truth.is_subclass` is False
for a non-class, never raises). The
charter (`_queryset_private.py:11-12`)
suits the owner only to
framework-built, sealed or proved
querysets, excluding this input. Three
production call sites re-derived
(`nested_planner.py:1339` via
`Callable[..., QuerySet]`,
`lateral_fetch.py:640`
(`LateralQuerySet`),
`single_parent_fetch.py:244`
(`SingleParentWindowQuerySet`)); caller
typedness does not narrow the callee.
Strict conversion would answer
`AttributeError` on the declared
`object` domain where today is `None`
-- executed, not inferred (probe rows
under Gates). A setter-only move stays
1->1 under every challenge and the
wrapper would carry no responsibility:
stubs declare the slot (`query.pyi:83`),
so the direct write type-checks (both
checker passes green). R3 separates on
bytes: identity (`:2452`) vs
MRO-membership (`:152`); Django itself
probes this slot defensively at
`query.py:2579` while typed-accessing
it elsewhere. Django 6.1.2 mechanics
confirmed (`:378` init, values
repoints, clone carry). Owner: none
(concur).

Challenges concur: C1 moves four rules
at count 1 each (rename co-movement
necessary, not sufficient); C2 1->1
(the probe is shape-agnostic, pinned by
the hostile "invalid" -> "values" row);
C3 moves the probe alone (it IS the
totality contract). Overturn search:
setter-only, lenient-getter and strict
conversion each fail on a distinct bar
above; no consolidation supportable.

Matrix judged: axes 1/3/4/6 searched
and bounded by the census; axis 2
inapplicable with reason (pure sync
attribute access; no async reader
exists) -- AGREE; axis 5 holds except
CC-4. Sharded/pg inapplicable by
construction -- AGREE (in-memory
attribute rule, zero-edit, default-cell
witnesses; no alias, routing or dialect
decision).

### Gates (slot-3, serialized, all heavy)

- sync dry-20261010T085502-afcb38:
  slot-3 bound fresh, package digest
  matches slots 1-2.
- witnesses dry-20261010T090021-0407b1:
  `test_nested_fetch.py` 19 passed.
- witnesses dry-20261010T090031-8a33aa:
  5 seal oracles passed (both hostile
  plantings, the all-override
  positive path, the prefetch-cache
  refusal, the policy/combinator pin).
- probe dry-20261010T090054-9ba2f9:
  None/object()/namespace-shape ->
  None; strict read -> AttributeError
  on all three; values-list ->
  "values"; plain -> None. 8/8 as
  predicted.
- basedpyright
  dry-20261010T090101-51de81: 0
  errors. Floor
  dry-20261010T090229-e0958e: 0
  errors.
- truthful-reads --check
  dry-20261010T090401-123d3b: tier-1
  0, errors 0.
- zero-edit: tracked diff vs
  ITEM_BASELINE over package/tests/
  examples empty; the 10 untracked
  files all predate this item (9
  cycle-baseline era, 1 f66's test
  file). Concurrent move during the
  run: `docs/dry/dry-0_0_15.md` only
  (docs, out of scope); copy stayed
  fresh.

Fingerprints (re-pass base):
`querysets.py`
641b158e797c6f50dce8200b81fc9f3e653f0117,
`nested_fetch.py`
67b69ebc871aaee697632912e1f5bec893a340e5,
`_queryset_private.py`
61527cd913310579955a3623ec314e42727291f1,
`test_nested_fetch.py`
c96e95af47cd66f354b237eb474747eb0ae950a4,
`test_querysets.py`
0a2e52bf3f9a359bf9b9e73d76007ebd995efb70,
`test_resolvers.py`
a6e548c35b172b55dd54bc20639c3b7b2b80d4523f.
HEAD 23b5f421 unmoved; file pins match
the dispatch record exactly.

Defects (Worker-2): none.

### Corrections

- D-1 (blocking): restore the
  truncated tail from the submission
  log (complete the cut F1 gate
  sentence; R1/R2/R3 records with
  contract differences + triggers;
  freshness fingerprints; Defects;
  Pending execution; Judgment with
  slot-2 run ids).
- D-2 (blocking): state F1's
  reconsideration trigger
  explicitly: a narrowing gate above
  `:151` proving `QuerySet` -- or
  restricting the declared domain
  from `object` -- reunites the read
  half with typed-access; until then
  1+1.
- CC-1: Matrix-1 census breakdown
  sums to 10, not 11 ("two prose").
  Fix: three prose (`:2723` /
  `:2934` / `:3736`). Total 11/2
  stands.
- CC-2: F1 oracles:
  `test_hostile_source_all_override...`
  plants no iterable (seal
  positive-path oracle). Fix:
  re-label it and add the omitted
  hostile planting
  `test_unsealable_source_fails_closed`
  (`:476`).
- CC-3: R3 "test-pinned both sides"
  overstates. Fix: classifier
  subclass acceptance pinned (matrix
  `:373`-`:379`); seal side pins
  foreign-class refusal x3 (all
  `list`); seal subclass refusal
  follows from identity bytes
  (`:2452`), unpinned.
- CC-4: Matrix-5 "wording oracle
  pins the R2 f-string" is wrong
  (zero hits for the wording in
  tests + examples). Fix: drop it;
  envelope oracles pin only "cannot
  be sealed...".

Transcribable index row (rows after
the repair re-pass):

`| queryset-iterable-class-access |
none (rejected as one rule) |
django_strawberry_framework/utils/querysets.py,
django_strawberry_framework/optimizer/nested_fetch.py,
django_strawberry_framework/utils/_queryset_private.py
(charter exclusion) | Family
queryset-iterable-class-access |
rejected (f67: count-2 spelling splits
1+1 -- seal typed write vs defensive
probe -- on the four-bar adjudication;
R1-R3 exclusions with triggers; trigger:
a narrowing gate above the probe proving
QuerySet reunites the read half with
typed-access) |`

### Reconciliation vs W1

Exact matches: census 9/3, evasion 0,
all site pins, the six-probe count, the
three call sites + their types, the
charter sentence, the five sibling
writes, HEAD pins `:4024`/`:3835`/
`:3942`, the `@@ -147,7` context-line
probe, zero `-`/`+` slot hits vs HEAD,
Django/stubs mechanics, the folder pin
note, the f66 inversion framing, zero
defects, no pending execution,
sharded/pg inapplicability. Differences:
the on-disk truncation (transmission,
not authorship -- D-1), the missing F1
trigger (D-2), precision fixes CC-1 to
CC-4, and the witness set (mine: 24 =
19 + 5, covering every traced behavior
including the omitted planting and the
projection pin; W1's 27 cited run ids
sit in the truncated Judgment).

## Iterations

### Pass 2 (revision; fresh Worker-1)

Pass-1 verification returned revision-needed with
substance CONCUR (the REJECTED verdict stands; no
overturn): D-1 a truncated transmission (the record
ended mid-sentence at old line 265 with a literal
truncation marker), D-2 a missing F1 trigger, CC-1
to CC-4 precision fixes. The pass-1 tail was
unrecoverable from the prior log (it holds only the
same truncated write), so every missing section was
re-derived from current bytes: the structural-gate
completion, F1 Coupling / Freshness / trigger, the
R1/R2/R3 records, Defects, Pending execution, the
Judgment with fresh run ids, and the link scaffold.
The appendix pins served as cross-checks only -- the
9/3 census with every pin, evasion 0, the 11/2
`ModelIterable` breakdown, 5 plantings + 2 prose, the
six-probe chain, the charter sentence, all three
call-site types, the five sibling writes, the HEAD
pins, the `@@ -147,7` context probe, zero `-`/`+`
slot hits, the Django 6.1.2 mechanics, stubs
`query.pyi:83`, and all six fingerprints were each
re-grepped first-hand and matched exactly. Fresh
slot-2 witness ids minted: 19 + 7 + 1 = 27 green
(ids under ## Judgment). D-1 completed; D-2 trigger
stated; CC-1 (three prose + pins), CC-2 (re-label +
the `:476` planting), CC-3 (one-sided pinning in
R3), CC-4 (wording sentence dropped) applied. The
`## Independent verification (Worker-2)` appendix
is untouched. Status: ready-for-verification/2.

### Verification pass 2 (Worker-2)

Verdict: verified. The /2 repair is
complete and correct: all eight
sections present (System trace,
Verification, Findings, Defects,
Pending execution, Judgment, link
scaffold, Iterations), zero literal
truncation markers (every remaining
mention is defect-description
prose), every D-1 section accurate
against current bytes.

Re-derived first-hand at current
bytes (HEAD 23b5f421 unmoved): the
9/3 census with every pin exact;
evasion 0 (plus the bare :152
local-use hit only); the 11/2
ModelIterable census with the CC-1
three-prose breakdown
(:2723 / :2934 / :3736); the
test/example sweep (5 plantings +
2 prose, no example hit); the R2
wording at zero hits with envelope
oracles pinning only "cannot be
sealed..." (CC-4); all six
freshness fingerprints full-hash
exact plus the three call-site
shorts; 121 package .py files; the
five sibling writes; the six-probe
chain under the :103 object
signature; the charter :11-12; all
three call-site types (the Callable
at nested_planner :1145 plus the
two typed subclass signatures);
the HEAD pins
:4024 / :3835 / :3942; Django :378
and :2579 plus stubs :83; the
matrix :373-:379 and hostile
"invalid" rows; the :476 planting
(list); the all-override oracle
planting no iterable (CC-2); the
seal plantings (list x3) with
one-sided pinning (CC-3); the R3
identity bytes :2452; helper
consumers 1 + 1; R1 :3782; the dirt
attribution (@@ -147,7 context
probe, -/+ only the :152
truth-migration; querysets diff
zero slot hits; f66 :3992 carry +
:115 import); and the three slot-2
Judgment run ids, real in the
evidence logs with 19 / 7 / 1
counts. The D-2 trigger is verbatim
as specified. CC-1 through CC-4 are
applied exactly. No revision number
differed from pass-1, so no full
re-derivation was owed.

Carried from pass-1 (bytes
identical, fingerprints match): the
F1 four-bar adjudication with its
overturn search, the 8/8 execution
probe, the C1/C2/C3 counts, the
matrix judgments, and the
sharded/pg inapplicability. The
plan cross-record (pass-1 verdict
and /2 resubmission entries)
matches the appendix substance
independently.

Zero-edit holds: the tracked diff
vs ITEM_BASELINE over
package/tests/examples is empty;
every untracked file is concurrent
work, none f67. The pass-1
appendix is byte-untouched
(uniform narrow wrap, no
mixed-style insertion; every pin
re-confirmed). ## Iterations is
accurate in every claim. The
transcribable index row stands
as-is; no further corrections
(no CC-5+).

Gates (verify-2 copy slot-3,
serialized, all heavy, copy fresh;
concurrent move during the run was
docs/dry/dry-0_0_15.md only, docs,
out of scope):

- bind dry-20261010T091531-3e7d7c
- witnesses
  dry-20261010T091810-070a2d (19
  passed), dry-20261010T091818-7d7133
  (7 passed),
  dry-20261010T091833-c9a291
  (1 passed)
- basedpyright
  dry-20261010T091839-84d7dd: 0
  errors; floor
  dry-20261010T092009-ef6b0f: 0
  errors
- truthful-reads --check
  dry-20261010T092138-80f168:
  tier-1 0, errors 0

Defects (Worker-2 pass 2): none.