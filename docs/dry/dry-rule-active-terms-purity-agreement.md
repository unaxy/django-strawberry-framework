# DRY review: `active-terms-purity-agreement`

Status: verified
Run: 0.0.15 2026-10-01-10

## System trace

The rule candidate is the active-terms guard's two-term agreement
check: two term readings for one (class, input) that disagree fail
closed with the not-pure `ConfigurationError` naming
`_normalize_input`. The two candidate definitions sit 8 lines apart
inside [orders-sets][orders-sets]`::OrderSet._input_has_active_terms`:
arm B, the ledger path (attested terms vs one fresh read, WT
616-625), and arm C, the fallback path (two fresh reads, WT
627-633). Their 4-line `raise` blocks are byte-identical except the
operand line (`diff` of WT 621-624 vs 629-632 shows one differing
line; the `raise` line, the first f-string line, and the closing are
identical including indent), and the operand lines share one
skeleton shape with only the rendered operands differing. The
excluded sibling is [orders-sets][orders-sets]`::_NormalizationLedger.claim`'s
inter-application verdict (WT 184-190), whose middle names a
different event. The owner is re-derived below from the bytes, not
inherited: the guard method itself via operand-select-then-check-once
restructure, no helper.

Verdict: CONFIRM the consolidation (challenges P1-P3 count 2), but
the landing is blocked-on-hunt: every shape that unifies the two
sites rewrites the truth-migration hunk
`@@ -611,18 +617,18 @@` in `git diff HEAD --
django_strawberry_framework/orders/sets.py`, which is concurrent
external dirt in neither the `## Owned changes` ledger nor the
`## Cycle baseline`. Zero edits; the migration sketch, the owed
structural gate shape, and the proposed rejection clause are recorded
here for the unblocking change.

Scope held in this item: the guard method whole (WT 587-636);
`claim` / `publish` / `_record_applied_normalization` (the attested
side is `tuple()` of the validated list, WT 265);
`_validate_normalized_terms` (both compares run on its trusted
primitives); `_normalize_input` (the obligated method, WT 639-653);
the three `_apply_orderings` attestation points (WT 801/809/814) plus
both `apply_*` colorings through the shared tail; the sole production
caller [list-field][list-field]`::_check_nonzero_offset_guard` (WT
1351) plus `_order_normalization_scope`; the filters twin whole-file
mechanism sweep; the relay encoder purity prose; the package oracles
in [test-order-sets][test-order-sets] plus the live oracle in
[test-async-api][test-async-api]; [spec-028][spec-028] plus
[glossary][glossary] (negative: no purity-verdict anchor in either —
the contract lives at owner prose plus oracles).

Fingerprints (short blob per state; baseline is the item baseline
object `a7e5efe0`, copy is the synced workspace copy at slot-2):

| File | HEAD `5c3496e0` | WT | Baseline | Copy |
|---|---|---|---|---|
| `django_strawberry_framework/orders/sets.py` | `a8cd33c7` | `8ce11495` | `8ce11495` | `8ce11495` |
| `django_strawberry_framework/list_field.py` | `37d2e6dc` | `6c0992f2` | `6c0992f2` | `6c0992f2` |
| `django_strawberry_framework/filters/sets.py` | `85699ac2` | `697ffd40` | `697ffd40` | `697ffd40` |
| `django_strawberry_framework/types/relay.py` | `2d1efd00` | `9903f6ea` | `9903f6ea` | `9903f6ea` |
| `django_strawberry_framework/types/base.py` | `e8416cc0` | `763a5acc` | `763a5acc` | `763a5acc` |
| `tests/orders/test_sets.py` | `9e9bb5d9` | `d66b482d` | `d66b482d` | `d66b482d` |
| `tests/test_list_field.py` | `9efccda3` | `6d74fcd1` | `6d74fcd1` | `6d74fcd1` |
| `examples/fakeshop/test_query/test_list_field_async_api.py` | `4a570915` | `4a570915` | `4a570915` | `4a570915` |
| `docs/SPECS/spec-028-orders-0_0_8.md` | `94a3141c` | `94a3141c` | `94a3141c` | `94a3141c` |

Baseline == WT on all nine; copy == WT on all nine; the live
oracle and the spec are clean (WT == HEAD). The rule-region
definition count is identical at HEAD and WT (`is not pure`
census 3 at both; `returned different results` census 2 at both).
`git status` count 480 at dispatch, 480 at trace time (this
artifact adds one untracked file); HEAD unmoved at `5c3496e0`;
item-scoped diff vs `a7e5efe0` on the target is empty.

Dirt attribution (by diff content vs `git show HEAD:<path>`; the
`## Owned changes` ledger carries no row for the target, and the
`## Cycle baseline` names no package path, so every hunk below
pre-dates the item and is concurrent work, left untouched): the
target carries 11 hunks, all truth-migration
(`_safe_arg_repr`/`_safe_type_name`/`__name__`/`__qualname__`/`getattr`
to `truth.render`/`truth.kind`/`truth.name`/`truth.qualname`/`truth.static_attr`,
plus the `truth` import). The two judged verdict blocks sit inside
hunk `@@ -611,18 +617,18 @@`; the excluded `claim` verdict sits
inside hunk `@@ -183,9 +184,9 @@`. Cited oracle regions are
HEAD-clean: the package purity/sequence oracles (WT 1283-1328,
1715-1768) avoid the file's single dirt hunk (`@@ -2321,53
+2321,24 @@`); the consumer call site plus scope docstring (WT
1325-1400) sit between dirt hunks `@@ -1355,7 +1299,7 @@` and
`@@ -1584,8 +1528,9 @@`; the live oracle file is clean.

## Verification

### Matrix

Discharged against the rule's real surface at WT bytes.

1. **Cross-flavor policy mirroring.** `is not pure`
package-wide is exactly 3 sites, all in [orders-sets][orders-sets]
(WT 187, 622, 630); `returned different results` is exactly the 2
guard sites. The filters twin carries no purity verdict and no
active-terms guard (`claim|attest|purity|disagree` over
[filters-sets][filters-sets] yields 3 unrelated prose hits: a
total-safety remark, a generated-leaf remark, a frozen remark).
Forms, mutations, and rest carry no `is not pure` site (covered by
the package census). The relay GlobalID encoder purity prose
([types-relay][types-relay] WT 654-657,
[types-base][types-base] WT 419-421) states an UNENFORCED consumer
obligation with arity/sync-ness/return-type checks only — a
different rule (E-relay). No second agreement rule in any flavor.
2. **Sync/async twins.** One `async def` in the target
(`apply_async`, WT 851) against its sync twin, both returning the
shared uncolored `_apply_orderings` tail (WT 848, 875); all three
attestation points live in that tail, so both colorings publish
through one recorder. The guard itself is sync-only with no async
twin; its single caller is the sync offset guard. The ledger lock
covers worker-thread publish with no await point of its own
(body-read plus the concurrent-publish oracle). No twin drift is
expressible: there is one tail, one recorder, one guard.
3. **Derived rather than repeated knowledge.** The verdict is
spelled twice (the finding); no site derives it. Oracles spell
literals (`match="is not pure; returned different results"`,
`match=r"_normalize_input is not pure"`) — independent, never
reading the owner. `_validate_normalized_terms` is the
return-contract gate (shape validation, a different rule —
E-validate); class labels render via composed `truth.name` (0
definitions here). No local re-derivation of any shared fact.
4. **Inverse / round-trip pairs.** The verdict is a raise-only
terminal with no decode/parse half; publish/claim are the ledger
rule's halves (file-local F-LEDGER boundary, decided by File
`orders/sets.py`, not re-litigated here). Normalize/validate is
delegate-then-gate, sequential, not inverse. No pair.
5. **Contracts restated in another medium.** Three media carry the
rule: production (2 definitions); owner prose (the purity
obligation in `_normalize_input`'s docstring, WT 642-651, plus the
guard docstring's two-path contract, WT 591-609 — the contract
sources, since [spec-028][spec-028] and [glossary][glossary] carry
no purity-verdict anchor, grep-verified); independent oracles (9
package `raises` sites spelling the verdict plus 1 live HTTP
assertion, none reading the owner). A verdict reword moves the 2
definitions; every oracle/projection follows (Challenges).
6. **Enforcement by omission.** The family is the 2 guard arms;
both enforce. Enumerated candidates for a missing member:
FilterSet (no twin guard — but no contract source requires one;
filters feed no offset guard; withheld, not a defect);
`_apply_orderings` (the attester the check compares AGAINST, not a
guard — not a member); the term-less/expression-less attestation
points (publishers; purity enforced at claim plus guard — not
members). No missing guard with a contract source behind it, no
omission defect filed.

### Enumeration

Instrument: package-wide mechanism-vocabulary sweeps (`is not
pure`, `returned different results`, `two applications of the same
input`, `_input_has_active_terms(`, `claim|attest|purity|disagree`
per flavor file) plus whole-method body reads of the guard (WT
587-636), `claim` (WT 158-191), `_record_applied_normalization`
(WT 249-265), `_validate_normalized_terms` (WT 284-320),
`_apply_orderings` (WT 779-815), both `apply_*` colorings, and the
consumer plus scope ([list-field][list-field] WT 1325-1410).
Population: 2 guard verdict definitions (arms B/C) plus 1 excluded
sibling verdict (`claim`); 1 production caller of the guard;
3 publishers through 1 recorder; 9 package oracle `raises` sites
plus 1 live oracle assertion; 0 second agreement rules. Every
member lands below: one CONFIRM finding (blocked-on-hunt), 1
rejection with difference plus trigger plus proposed owner clause,
5 exclusions each with difference plus trigger, zero unassigned.

### Challenges

Authoritative definitions only; consumers, oracles, and
projections that also move are listed, never counted. All
challenges static-reviewed at WT bytes; the twin-arm verdict
agreement is additionally pinned by one executed oracle re-run
fresh in the shared venv
(`tests/orders/test_sets.py::test_input_has_active_terms_purity`
plus
`tests/orders/test_sets.py::test_input_has_active_terms_sequence_controls_sync`,
2 passed).

- P1 Verdict wording. Posit rewording `returned different
results`: 2 definitions move (both raise blocks, WT 621-624 and
629-632 — the first f-string lines byte-identical). The 9 package
`match=` literals plus the live message assertion follow (listed,
not counted).
- P2 Comparison. Posit an order-insensitive or multiset compare: 2
definitions move (both `!=` predicates; arm B's `tuple()` wrap
moves with its predicate as representation plumbing). Both
compares run on validated primitives with deterministic equality
(the gate docstring states `consumer __eq__ in the purity
compare` fires nowhere — corroborating projection).
- P3 Verdict type. Posit `ConfigurationError` to a dedicated
purity subclass: 2 definitions move (both `raise` sites). Oracle
`pytest.raises` targets follow (listed, not counted).
- P4 Counter-challenge (proves the R-CLAIM split). Posit rewording
the inter-application middle (`two applications of the same input
in one resolution`): 1 definition moves (`claim` only; arms B/C
untouched). Reverse: P1 moves arms B/C only, `claim` untouched.
- P5 Counter-challenge (proves the operand-selection boundary).
Posit changing attested storage tuple-to-list: arm B's `tuple()`
wrap alone moves (1 of the 2) — representation shaping forced by
the ledger's storage type, not the verdict rule. Under the
restructure this shaping stays per-arm (`list(applied_data)` vs
`data_check`); only verdict plus comparison unify.
- P6 Counter-challenge (proves the count boundary). Posit changing
the fallback path's normalization count (2 reads to 1 plus a
cached read): arm C's acquisition alone moves; the verdict rule
is untouched. Counts live in operand acquisition, pinned per path
by the `normalize_count` oracles and the A/B/B + A/A/B/A sequence
controls, all preserved by the restructure.

## Findings

### F1: the guard's two agreement checks are one rule in two definitions (CONFIRM, blocked-on-hunt, zero-edit)

- **Contract + variation.** Two term readings for one (class,
input) that disagree fail closed with the not-pure
`ConfigurationError` naming `_normalize_input`. Legitimate
variation: the verdict (type plus wording) and the comparison
only — operand selection, normalization counts, and walk targets
stay per path by construction (P5/P6).
- **Sites + roles.** *Definitions*: arm B (WT 618-625, attested
vs fresh) and arm C (WT 627-633, fresh vs fresh) inside
[orders-sets][orders-sets]`::OrderSet._input_has_active_terms`.
*Callers*: the guard's two arms (operand selection per arm).
*Consumer*: [list-field][list-field]`::_check_nonzero_offset_guard`
(the sole production caller — census: one `_input_has_active_terms(`
call site package-wide). *Oracles*: the purity, purity-structure,
sequence-control, child-task, and nested-application tests (all
drive disagreeing normalizations and match the verdict; the live
A/B/B test matches `BranchOrder._normalize_input is not pure`
over HTTP) — independent. *Projections*: the purity-obligation
docstring plus the guard docstring (the contract sources).
- **Challenges.** P1 → 2 here; P2 → 2 here; P3 → 2 here. Count 2
= duplication. The disproof attempts failed in both directions:
the arms share inputs (two validated term lists), output (None or
raise), error skeleton, timing, hooks, and reasons to change; and
the codebase proves it distinguishes events in message middles
when they differ — `claim`'s middle does — while arms B/C share
one middle because the author considers the two paths the same
check.
- **Owner + lifetime.** The guard method itself, via restructure
to select operands then check once — no helper (principles 7 +
11: the verdict exists solely for this guard's two arms, no other
consumer exists or is plausible, and a module helper would add a
second name plus call indirection for a rule with exactly one use
site after the restructure; dependency direction is moot, all in
one method). No stored derivation; per-guard-call lifetime.
- **Migration (NOT APPLIED — blocked, sketch for the unblocking
change).** Select `(first, second, data_to_walk)` per arm, then
one compare plus one raise:
`applied_data` arm → `first, second = list(applied_data),
data_check`, walk `list(applied_data)`; fallback arm →
`data_check2` read stays inside the `else` (counts load-bearing),
`first, second = data_check, data_check2`, walk `data_check`;
then `if first != second: raise` with the current first f-string
line and `({truth.render(first)} != {truth.render(second)})`.
Per-path messages stay byte-identical (operand order preserved);
`applied_data != tuple(data_check)` becomes `list(applied_data)
!= data_check` (same elements, sequence equality on validated
primitives); call order, counts, claim timing, exception type,
and walk targets unchanged. Each former definition becomes the
one check; the `first_repr` local disappears.
- **Distinct behavior.** Operand pairs stay per arm
(attested-vs-fresh vs fresh-vs-fresh — forced by which readings
each path holds); normalization counts stay per arm (2 vs 3
total); walk targets stay per arm (attested vs fresh). The
`claim` verdict stays ledger-owned (R-CLAIM below).
- **Behavioral proof.** `static-reviewed` for the unification
shape (byte comparison of the two blocks; sequence-equality
equivalence on validated primitives; per-path message identity
by operand-order preservation) plus `execution-verified` for the
twin-arm verdict agreement both oracles pin: `uv run pytest
tests/orders/test_sets.py::test_input_has_active_terms_purity
tests/orders/test_sets.py::test_input_has_active_terms_sequence_controls_sync
--no-cov -n0 -q` → 2 passed in the shared venv. Rejects "the two
arms check different contracts" (same inputs/outputs/error, same
reasons to change — P1-P3) and "unification needs machinery" (the
sketch shares the verdict with no helper and no import move).
Sharded/PG cells: inapplicable by construction — the verdict plus
comparison run on validated in-memory term lists with no
queryset evaluation, alias read, or dialect branch in the rule
(Worker-2 judges).
- **Structural gate (OWED at application time, not landed).**
Shape: an AST census over `_input_has_active_terms` asserting
exactly one `returned different results` verdict site. Negative
control: a behavior-preserving hand copy of the unified check
back into two arms — every behavior oracle passes that control
(the copy is correct), the census fails it. Born red today (2
sites); a gate born red gets weakened, not fixed — so none
lands with this blocked item. Failability via `prove` at
application time.
- **Coupling.** Blocked-on-hunt: the landing rewrites hunk
`@@ -611,18 +617,18 @@` of `git diff HEAD --
django_strawberry_framework/orders/sets.py` (the `first_repr` line
plus both raise blocks' label/render lines), which is concurrent
truth-migration dirt in neither the ledger nor the baseline.
Couples to nothing else (one method, no import move, no second
file). The proposed R-CLAIM owner clause below rides the same
unblocking change.
- **Freshness.** Target HEAD `a8cd33c7` / WT `8ce11495` /
baseline `8ce11495` / copy `8ce11495`; consumer
[list-field][list-field] `37d2e6dc` / `6c0992f2` / `6c0992f2` /
`6c0992f2` (cited region HEAD-clean); oracles
[test-order-sets][test-order-sets] `9e9bb5d9` / `d66b482d` /
`d66b482d` / `d66b482d` (cited regions HEAD-clean),
[test-async-api][test-async-api] `4a570915` throughout (clean);
excluded bodies [filters-sets][filters-sets] `85699ac2` /
`697ffd40` throughout WT states, [types-relay][types-relay]
`2d1efd00` / `9903f6ea` throughout, [types-base][types-base]
`e8416cc0` / `763a5acc` throughout; contract-negative
[spec-028][spec-028] `94a3141c` throughout. Searched population:
whole package for `is not pure` (3 sites), `returned different
results` (2 sites), `_input_has_active_terms(` (1 call site),
plus per-flavor `claim|attest|purity|disagree` sweeps. Any
fingerprint change reopens the finding.

### R-CLAIM: `claim`'s disagreement verdict stays ledger-owned (REJECT inclusion)

Considered: include [orders-sets][orders-sets]`::_NormalizationLedger.claim`'s
verdict (WT 184-190) in the family — same `is not pure` verdict
family, same exception type. Contract difference: `claim` detects
INTER-application disagreement (two attestations for one pair,
possibly from different tasks/threads) and its middle names that
event (`two applications of the same input in one resolution`),
while the family detects guard-time read disagreement with the
same-input middle — different events, different diagnostic
information (cross-task vs local nondeterminism), different owning
class (ledger claim integrity vs guard agreement). Unifying the
middles would lose the distinction; parameterizing it couples the
ledger to the guard over verdict wording (the per-message-grammars
class: each message renders its own event). P4 proves the split
(an inter-application reword moves `claim` only). Trigger to
reconsider: the three events collapsing to one diagnostic (for
example the ledger retiring, leaving one guard). Durable home: the
two message middles (each already states its own event) plus one
plain clause at the guard docstring — PROPOSED, application
blocked with the owner file:

> The two guard arms share one agreement verdict (same event:
> two readings of one input disagreeing); `_NormalizationLedger.claim`'s
> verdict names a different event (two applications disagreeing)
> and stays ledger-owned.

### Exclusions (contract difference plus reconsideration trigger each)

- E-twin: no FilterSet purity guard. Difference: filters feed no
offset guard and carry no attestation machinery — absence with no
contract source behind it, not a second definition. Trigger: a
contract source requiring filter normalization purity checks.
- E-relay: GlobalID encoder purity ([types-relay][types-relay] WT
654-657, [types-base][types-base] WT 419-421). Difference:
documented-but-unenforced consumer obligation (withholding `info`
cannot prevent I/O); enforced checks are arity/sync-ness/return-type
only — no agreement verdict anywhere. Trigger: the framework
gaining an encoder agreement check.
- E-validate: `_validate_normalized_terms` (WT 284-320).
Difference: return-shape gate (exact-type hostile-subclass
discipline on one reading) vs agreement check (equality across
two readings) — orthogonal contracts; the gate's output feeds the
family's inputs. Trigger: none plausible.
- E-obligated: `_normalize_input` (WT 639-653). Difference: the
obligated method (purity producer, pure delegation to
`normalize_input_value`) vs the check enforcing the obligation —
producer/consumer, not two definitions. Trigger: none plausible.
- E-publish: the three `_apply_orderings` attestation points (WT
801/809/814) plus `_record_applied_normalization`. Difference:
publishers attesting one successful normalization each vs the
guard comparing two readings — the check compares AGAINST what
these attest. Trigger: none plausible.

## Defects

None. Tracing found no non-duplication bug: the arm-B
tuple-vs-list comparison asymmetry is representation plumbing over
validated primitives with deterministic equality (pinned by the
sequence oracles), not a defect; the FilterSet guard absence has
no contract source behind it (axis 6, withheld).

## Pending execution

None. The one executed proof ran fresh in the shared venv (see
Challenges). No `proof:` entry is owed: the unification sketch is
`static-reviewed` by byte comparison, and its execution (full
purity-oracle file plus the live A/B/B test) belongs to the
unblocking change, which re-proves then. Type gates (`mypy`,
`basedpyright`, `check_any`) are vacuous on a zero-edit item and
were not run by Worker-1; Worker-2 judges. Sharded/PG cells are
`inapplicable by construction` (stated in F1; Worker-2 judges).

## Judgment

The guard's two agreement checks are one rule — same contract,
same verdict skeleton, same reasons to change — held in two
adjacent definitions. The consolidation (operand-select-then-check-once
at the guard, no helper) is CONFIRMED with its owner derived from
responsibility, but its landing is blocked-on-hunt on truth-migration
dirt it must rewrite. The item is complete as a proved zero-edit
record: finding, migration sketch, owed gate shape, proposed owner
clause, and triggers are all durable here for the unblocking change.

## Implementation (Worker-1)

Zero-edit: no tracked file changed, no new tracked file, no
`## Owned changes` row owed. The artifact itself
(`docs/dry/dry-rule-active-terms-purity-agreement.md`, untracked)
is the item's only output. Item-scoped diff vs `a7e5efe0` is
empty; `git status` count 480 at trace time; HEAD `5c3496e0`
unmoved. No ruff run owed (no `.py` touched).

## Independent verification (Worker-2)

Ordering note: the dispatch brief stated W1's verdict, so full
blindness was impossible; the trace below was built from my own
sweeps (censuses, whole-method body reads, diff attribution)
before I opened `## Findings`, and every W1 figure I rely on
was re-derived, not inherited.

### My trace

Rule: the guard-time agreement — two term readings for one
(class, input) that disagree fail closed with the not-pure
`ConfigurationError` naming `_normalize_input`.

- Arm B ([orders-sets][orders-sets] WT 618-625, attested vs
fresh): DEFINITION 1. `applied_data != tuple(data_check)` plus
the `returned different results` raise.
- Arm C (WT 627-633, fresh vs fresh): DEFINITION 2.
`data_check != data_check2` plus the same-skeleton raise.
- [orders-sets][orders-sets]`::_NormalizationLedger.claim` WT
183-191: excluded sibling. N-way attestation-vs-attestation scan
under the ledger lock with the `two applications of the same
input in one resolution` middle — ledger coherence across
published applications, not guard-time read verification.
- Consumer: [list-field][list-field]`::_check_nonzero_offset_guard`
WT 1351 — the sole production call site (package census: one
`_input_has_active_terms(` call outside the definition).
- Oracles: 9 package `raises` sites in
[test-order-sets][test-order-sets] plus the live HTTP assertion
in [test-async-api][test-async-api] WT 2125 — all spell
literals, none reads the owner.
- Projections: the `_normalize_input` purity-obligation
docstring (WT 642-651) plus the guard docstring (WT 591-609);
[spec-028][spec-028] carries no purity anchor (grep 0) and the
one [glossary][glossary] `purity` hit is the relay-encoder prose
(E-relay's subject), not a guard-verdict anchor.
- Owner I would choose: the guard method itself via
operand-select-then-check-once, no helper — the verdict exists
solely for these two arms; a module helper adds a second name
for a rule with exactly one post-restructure use site.
- Challenges (mine): reword the family middle → 2 move
(`claim` untouched, different middle); order-insensitive
compare → 2 move (the `claim` scan is a different algorithm
over a different domain, see the count-3 probe below); verdict
type → 2 move for the family's verdict (`claim`'s verdict is a
separate event's verdict, its type a separate decision).

### Reconciliation

No verdict difference: F1 CONFIRM count-2 blocked-on-hunt,
R-CLAIM reject-inclusion, the five exclusions, zero defects,
and `## Pending execution` None all match my trace. Figure
checks, each re-derived: `is not pure` 3 (WT 187/622/630),
`returned different results` 2, guard call sites 1 production,
oracles 9 package plus 1 live, filters
`claim|attest|purity|disagree` 3 unrelated prose hits, relay
prose unenforced-obligation confirmed by body read, raise
blocks byte-identical except the operand line (`diff` of WT
621-624 vs 629-632 shows one differing line), all nine
fingerprint pairs re-derived equal (target `a8cd33c7` /
`8ce11495`, consumer `37d2e6dc` / `6c0992f2`, live oracle and
spec clean), cited oracle regions HEAD-clean (tests dirt is
the single `@@ -2321,53 +2321,24 @@` hunk; consumer region WT
1325-1400 sits between the `@@ -1355,7 +1299,7 @@` and
`@@ -1584,8 +1528,9 @@` hunks).

Count-3 probe (discharged, not a difference): the sharpest
threat to count-2 is P2/P3 framed at policy level — "purity
agreement becomes order-insensitive / gets a dedicated
subclass everywhere" would touch `claim` too. It fails the
MUST-move test: `claim`'s N-way scan under lock over published
attestation records vs the arms' pairwise check-time compare
over fresh readings are different code with independent
reasons to change (keep-first-wins at `claim` moves `claim`
only; fallback-count changes move arm C only), and the message
middles name different events with different diagnostics
(cross-task vs local nondeterminism). Shared token `is not
pure` is not a shared definition. No lawful consolidation
including `claim` exists: a shared raise helper would
parameterize the event middle, coupling ledger to guard over
wording to save one skeleton — machinery, not a rule.

Blocked-on-hunt (confirmed, hunk exactly identified): both
verdict blocks sit inside `@@ -611,18 +617,18 @@` of `git diff
HEAD -- django_strawberry_framework/orders/sets.py`, verified
present with exactly that header; all 11 target hunks are
truth-migration (`_safe_*`/`__name__`/`getattr` to `truth.*`),
all pre-dating the item (item baseline diff on the target is
0 lines; no ledger row covers the target). Every unification
shape rewrites those lines, so no partial consolidation was
legally landable — including the tempting message-line-only
share, which still touches the dirty hunk and leaves count 2.
Migration sketch judged sound on all principle-8 axes:
`applied_data != tuple(data_check)` to `list(applied_data) !=
data_check` is sequence equality over exact-typed validated
primitives with deterministic equality; operand order
preserved so both per-path messages stay byte-identical;
`data_check2` stays in the `else` (counts load-bearing, pinned
by the sequence oracles); claim timing, call order, exception
type, and walk targets unchanged; no awaits, no query effects.

R-CLAIM carries its contract difference (inter-application vs
guard-time read disagreement, with the diagnostic and owning
class stated) plus trigger (the three events collapsing to
one diagnostic) plus a proposed durable clause riding the
unblocking change. E-twin and E-relay carry real triggers.
E-validate / E-obligated / E-publish carry `Trigger: none
plausible`: accepted — these are role-classified neighbors
(one-reading gate, producer, publishers), never plausible
definitions, and a fictional trigger would be worse than the
honest none. `## Pending execution` None is correct: the
sketch is `static-reviewed` by byte comparison with its
message/count/timing preservation argued per path, the twin-arm
agreement claim is `execution-verified` (re-run below), and
the full re-proof belongs to the unblocking change; the owed
structural gate is correctly NOT landed (born red at 2 sites).

Matrix judged axis by axis against the real surface: flavors
covered by whole-package censuses plus per-file sweeps (no
second agreement rule); sync/async correctly inapplicable as
drift (one uncolored tail, one recorder, sync-only guard with
a sync caller); derived-knowledge correctly reports the
spelled-twice verdict with oracles independent; round-trip
correctly finds no pair (publish/claim is the ledger rule's
boundary, decided by its file item); cross-medium count (2
definitions, owner prose, 9+1 oracles) re-derived; omission
correctly withholds FilterSet (no contract source) and
non-members the attesters. No unsearched axis hides behind
the found consolidation.

### Gates and probes (shared venv, `uv run`)

- Item diff: `git diff a7e5efe0 --name-only` names the plan
file alone; target diff 0 lines; artifact untracked. Zero
production edits confirmed.
- Ruff: W1 touched zero tracked `.py`, so `ruff format
--check` / `ruff check` on touched paths are vacuous — stated,
not run. The artifact carries the 10-group link scaffold with
every ref-id used and defined.
- `uv run pytest
tests/orders/test_sets.py::test_input_has_active_terms_purity
tests/orders/test_sets.py::test_input_has_active_terms_sequence_controls_sync
--no-cov -n0 -q` → 2 passed (shared venv; corroborates W1's
executed proof, the one focused run this address allows).
- `uv run mypy` → `Success: no issues found in 119 source
files`, exit 0.
- `uv run basedpyright` → `0 errors, 0 warnings, 0 notes`,
exit 0.
- `uv run python scripts/check_any.py` → `130 allowed use(s)
of Any at 90 site(s)`, exit 0.
- Sharded/PG `inapplicable by construction`: accepted on its
stated reason — the verdict plus comparison run on validated
in-memory term lists with no queryset evaluation, alias read,
or dialect branch in the rule. No defect found; nothing added
to `## Defects`.

Verdict: `verified` plain. F1 CONFIRM count-2 stands with the
guard-method owner and a sound sketch; the blocked-on-hunt
landing call is exact; R-CLAIM plus all five exclusions are
durable; the item is complete as a proved zero-edit record.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[list-field]: ../../django_strawberry_framework/list_field.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-order-sets]: ../../tests/orders/test_sets.py

<!-- examples/ -->
[test-async-api]: ../../examples/fakeshop/test_query/test_list_field_async_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
