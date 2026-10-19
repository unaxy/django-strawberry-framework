# DRY review: `relay-pk-repair`

Status: verified
Run: 0.0.15 2026-10-10-15

Queue item 6c, decision 5e option (b): one owner for the Relay-pk suppression
rule, fixing row 52 at the root. Not the reverted consumer half verbatim: the
owner answers the consumer case its predecessor omitted.

## System trace

Pre-edit the rule lived twice: the performer inline in
[types-base][types-base]`::_build_annotations` (pre-edit 2061/2070/2111:
precomputed pair + scalar-branch conjunction, consumer-first) and the
predictor inline in [inspect-cmd][inspect-cmd]`::Command._is_suppressed_relay_pk`
(pre-edit 307-311: relation-first + shape + pk equality, NO consumer arm)
called from suppressed-first `_resolve_row` (275-278). That gap is row 52: a
consumer pk override kept its annotation at build time while the table claimed
the interface row. Package-wide mechanism sweep found no third definition.
Attribution vs `git show HEAD`: edited lines are HEAD-clean or DRY-ledger
dirt; hunt truth hunks adjacent but untouched, so no `blocked-on-hunt`.
Post-edit the decision lives once in the owner below; both sides call it.

## Verification

### Matrix

1. Cross-flavor: one synthesizer (types) + one diagnostic reader (mgmt command); no sibling flavor synthesizes annotations. Trigger: a second synthesizer.
2. Sync/async: pure sync predicate over class/model/field inputs; no await boundary, no twin, none owed.
3. Derived knowledge: pk identity read once from Django at the owner; the duplicated conjunction is now single-sited. Trigger: a third spelling.
4. Round-trip: build (emit-or-drop) vs display (predict) answer one question at different phases, not inverses; no encode/decode pair.
5. Other media: oracles use independent literals/records, never the owner; the predictor's 20-line prose restatement (a third copy) is deleted to a pointer; specs pin the fixed behavior.
6. Omission: population of 7 (relay/non-relay scalar pk, direct inheritance, relay/non-relay relation pk, non-`id` scalar pk, consumer pk) all carried; assigned-only overrides never finalize, outside the population.

### Enumeration

Instrument: package grep for `suppress_pk_annotation | _is_suppressed_relay_pk
| _meta\.pk\.name` over 120 `.py` + `def` census. Homes: owner 1 def
([types-base][types-base]:1960); adapter 1 def ([inspect-cmd][inspect-cmd]:285,
consumer role); performer call site 1; predictor call site 1 (`_resolve_row`
unchanged); validator `relay_pk_name` adjacent (listed); `connection.py`
pk-alias + `filters/base.py` GlobalID routing excluded (different rules);
oracles in [test-mgmt-inspect][test-mgmt-inspect] + fakeshop inspect module.

### Challenges

- C1 relation pks join the suppressed population -> 1 (owner relation-first arm; O2O/MTI twins listed).
- C2 pk-identity rule change -> 1 (owner read owns NAME-vs-attname; validator listed adjacent).
- C3 consumer pk displays its consumer row -> 1 (owner exemption arm; pre-edit this was defect D1).

## Findings

### F1 - relay-pk-suppression decision (CONFIRMED -> consolidated)

- **Contract + variation.** A selected field loses its synthesized annotation
  iff it is a NON-relation pk the consumer did not author, on a Relay-shaped
  type. Varies on the suppressed population and the pk-identity rule.
- **Sites + roles.** *Definition*: [types-base][types-base]
  `::_is_suppressed_relay_pk` (pure predicate; the consumer set is a required
  parameter). *Consumers*: the `_build_annotations` scalar branch and
  `Command._is_suppressed_relay_pk` (unpacks the definition, returns it).
- **Challenges.** C1/C2/C3 -> 1 each. **Owner + lifetime (7, 4).**
  `types/base.py`: synthesis owns the drop it performs; the command already
  imported from it; narrowest shared home. Pure per-call, not cached.
- **Migration.** Performer: locals + both comment blocks folded into the owner
  (knowledge moved, not dropped); loop calls it. Predictor: inline body +
  restatement replaced by delegation + pointer (full-path citation kept).
  `_resolve_row` untouched (suppressed-first now correct).
- **Distinct behavior.** Both pre-existing orders preserved; exactly one input
  class changes verdict (consumer non-relation pk on a Relay type: GlobalID
  row -> consumer row). All other verdicts byte-identical.
- **Behavioral proof.** `execution-verified` in workspace slot-2:
  fail-first `dry-20261010T194837-118047` exit 1 (gate `predictor True`,
  table `GlobalID!`); post-fix 2 + 48 (both inspect modules) + 137
  (relay-interfaces) + 39/189 (test_base) passed, final-bytes `...5835-92d7e7`
  2 passed. No census gate owed (4B; the mirror gate is behavioral).
- **Coupling.** None. **Freshness.** HEAD `23b5f421`; ITEM_BASELINE
  `608f1f5b`; sync digest `2d87dc60`; blobs `19d761b6` base / `43d8faf2` cmd
  / `0f471094` tests / `956a08dc` s019 / `96e16c8f` s029; 120 `.py`;
  contracts [spec-019][spec-019] + [spec-029][spec-029]; rest excluded on
  zero vocabulary. **Triggers** T-population/T-identity/T-exemption at owner.

## What shrinks

The rule is the Relay-pk suppression decision: on a Relay-Node-shaped type,
a selected field loses its synthesized annotation iff it is a NON-relation
field whose name is the model's pk name and the consumer did not author it.
Before this change the rule had two independently maintained definitions.
The first was the performer inline in
`django_strawberry_framework/types/base.py::_build_annotations` (pre-edit
lines 2061, 2070, 2111): a `_is_relay_shaped` precompute plus a
`source_model._meta.pk.name` precompute plus the scalar-branch conjunction,
with the consumer short-circuit running first. The second was the predictor
inline in
`django_strawberry_framework/management/commands/inspect_django_type.py::Command._is_suppressed_relay_pk`
(pre-edit lines 307-311): a relation-first guard plus `_is_relay_shaped`
plus pk equality, with no consumer arm at all, called from `_resolve_row`
before the consumer branch. The shape predicate was already shared; the
decision around it was not.

The concrete change that today must be made in two places is any correction
to the suppressed population or the exemption order - and it already went
wrong once: when the consumer-override contract landed, the performer gained
its exemption and the predictor did not, so for a Relay type over a code-pk
model with a `code: str` override the table reports `GlobalID!` / `relay.Node
id` while the schema exposes `code: String!` (defect-table row 52, family D1,
with wire proof in the [family artifact][mirror-artifact]). Missing one side
again misreports an operator-facing diagnostic against the schema it claims to
describe, and the two orders (consumer-first vs suppressed-first) make the
divergence silent.

The owner is the new module-level
`django_strawberry_framework/types/base.py::_is_suppressed_relay_pk`
(lines 1960-2007): relation-first, then the consumer exemption (a required
`consumer_authored_fields` parameter, so a future caller omits it only as a
loud `TypeError`), then `_is_relay_shaped`, then the pk-name read. Principle
7 picks `types/base.py` because synthesis owns the drop it performs - keeping
Strawberry's interface-supplied `id` from colliding is a type-construction
contract, the command already depended on the module, and no narrower shared
home exists; the real suppression loop itself cannot serve because it
synthesizes with side effects. The former performer definition becomes one
owner call in the scalar branch (its locals and both comment blocks folded
into the owner, knowledge kept); the former predictor definition becomes a
display adapter that unpacks the definition and returns the verdict (its
prose restatement deleted). `_resolve_row` dispatch, the performer consumer
short-circuit, relation-pk non-suppression, and every non-consumer verdict
stay exactly as they were; the only behavior change is the one input class
the defect named.

Net package lines vs ITEM_BASELINE: base.py +57/-27, inspect command
+18/-24, total +75/-51 (+24). The item clears the bar of 4A three ways: the
copies already drifted (row 52, shown with wire proof, not hypothesized);
each definition carries real multi-line decision logic (precompute pair +
branch conjunction vs guard + shape + identity); and the rule is
data-exposure relevant (an operator diagnostic misattributing which surface
the schema exposes). No new machinery: one predicate with two readers, one
deleted prose copy, zero mode flags.

## Defects

None new. Row 52 (family D1) is FIXED by this item, not homed: the consumer
arm lives in the owner and both proofs fail pre-fix / pass post-fix.

- D-W2-1 (Worker-2, minor, routes to the `types/base.py` owner card): `_build_annotations` Args
  says `source_model` resolves "the primary-key attname" but the read is `_meta.pk.name` — pre-existing,
  observably harmless, invites the warned-against `getattr` reuse. One-word fix, outside this item.

## Pending execution

None. Sharded/pg inapplicable by construction: class-creation synthesis plus
finalized-record reads only - no database row, alias, or dialect reached.

## Judgment

The decision was spelled twice with the consumer case answered once (row
52). It now has one owner both sides read, the consumer case a required
parameter, with fail-first behavioral proofs and full-module regressions
green. Row 52 closes with this item.

## Implementation (Worker-1)

Item-scoped diff vs `608f1f5b` is exactly 10 hunks; shared tree
`cmp`-identical to the proven copy. `types/base.py` (+57/-27): new owner +
loop call site (HEAD-clean lines only; hunt hunks at 2077/2146 untouched).
`inspect_django_type.py` (+18/-24): import swap + delegation (only the
ledger-described docstring + clean body lines rewritten).
`tests/management/test_inspect_django_type.py` (+58/-13): gate consumer arm +
new table test at the module's tier (command surface unreachable from a real
query; no new example model). Specs (+7/-5): 5 pinpoints retargeted, claims
unchanged; DONE plans, cycle artifacts, hunt record untouched. Gates: ruff
clean; source-layout 0; basedpyright main + floor 0 errors (one
`reportUnusedClass` fixed via the registry-assert pattern); truthful-reads 0;
citations resolve. No public symbol, no `check_public_types` owed. Copy
slot-2 + evidence kept per 5b; release is Worker-0's.

## Independent verification (Worker-2)

Own trace from WT bytes + ITEM_BASELINE `608f1f5b` + `git show HEAD:` (artifact read in
required-reading order; counts below are mine). 1 definition (`types/base.py::_is_suppressed_relay_pk`:
relation, consumer, shape, identity); 2 consumers (performer scalar-branch call; predictor adapter
under unchanged `_resolve_row`); adjacency, not definitions (`relay_pk_name` raise-guard;
`_is_relay_shaped` shape contract shared with the collision guard). C1/C2/C3 -> 1 each (validator
guards NAMES, stays `.name` under any identity change); row 52's consumer case answered once, as a
required parameter. My principle-7 owner: `types/base.py` module level (synthesis owns the drop;
command already imports it; loop has side effects; shape gate has a distinct contract + guard consumer).
Reconcile: agree with F1 on rule, roles, counts, owner, changed class. Verdict-neutral notes: (a) "10
hunks" recounts as 14 `@@` (3+2+4+4+1; all figures/blobs exact) — record slip, closeout-correctable;
(b) D-W2-1 above. Bar 4A holds three ways (drifted with wire proof; multi-line both sides; operator-table
data exposure); pre-fix 2-edit change: the consumer exemption (landed performer-only). Real owner, not
machinery (2 readers, 1 deleted prose copy, 0 flags); old half not re-applied verbatim (5e).
Equivalence: performer byte-identical all inputs; predictor differs only on consumer non-relation pk on
Relay (True -> False, consumer row); no new exceptions/queries/txns. Behavior: shared inspect module 24
green; copy `dry-20261010T200732-3d0198` 2/2; own fail-first `dry-20261010T200754-94e632` (arm excised: 2
FAILED exit 1; restored identical: 2 passed); regressions fakeshop inspect 24, test_base 189,
relay_interfaces 137. Cells inapplicable, concur. `tests/` tier right; Edition reused; oracles independent
(record + literals); no census gate (4B); no banned words. Attribution: base/cmd/test hunks on HEAD-clean
or ledger lines (hunt `truth.*` adjacencies byte-identical; zero `truth.` in test ranges; specs HEAD-clean)
— verifiable, not blocked. Gates: ruff x2 clean; basedpyright main+floor 0/0/0; truthful-reads 0 (120
files); source-layout 0; no new cast/Any/suppression; no public symbol, no `check_public_types` owed. Specs:
5 pinpoints true (cited return line exists); zero old-spelling residue; Decision-4/8 sentences still true;
spec-019 `code: String!` wire now matched. Judgment: verified; row 52 closes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[mirror-artifact]: dry-rule-relay-pk-suppression-read-mirror.md

<!-- docs/SPECS/ -->
[spec-019]: ../SPECS/spec-019-consumer_overrides_scalar-0_0_6.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[types-base]: ../../django_strawberry_framework/types/base.py

<!-- tests/ -->
[test-mgmt-inspect]: ../../tests/management/test_inspect_django_type.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
