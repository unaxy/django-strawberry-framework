# DRY review: `traversal-depth-cap-check`

Status: verified
Run: 0.0.15 2026-10-01-11

Item kind: FAMILY (responsibility family). Owner candidate re-derived fresh,
not inherited: `django_strawberry_framework/utils/input_values.py::assert_set_traversal_depth`
CONFIRMED as the owner. Consolidation implemented in this same change
(6 check definitions -> 1; 5 filter sites compose by name).

Concurrency: both indexed files carry concurrent dirt (truth migration +
except-`BaseException` deletions, none of it ledgered); all of it is
attributed by diff content below and preserved byte-for-byte. Every edited
production line was byte-identical between HEAD and WT before the edit (hunk
map below); `utils/input_values.py` is untouched; the test diffs are additive
plus one docstring line. No concurrent line edited, reverted, or tidied. The
naming file artifact's line numbers are stale (drift since its stamp); every
site below was re-censused at current bytes.

Baselines: `ITEM_BASELINE=38dd09a1020ff1ebbc0982768771b6f801c3d365`
(resolves as a commit); HEAD `dd0b6691` unmoved throughout. Dispatch pins
verified at task start: `utils/input_values.py` WT `463f81a8` / HEAD
`929e81b5`, `filters/sets.py` WT `14884190` / HEAD `76abccb0`. Address
`dry/travcap-f51/consolidate` (slot-2; every proof ran there). Item-scoped
diff vs `ITEM_BASELINE` is exactly the 8 production hunks + 4 test hunks
below; zero unattributed hunks.

## System trace

The rule: a set-input walk fails closed when its depth counter passes the
set's budget - the `if depth > cap: raise the typed sentence` guard shape.
The budget VALUE (`set_traversal_depth_cap`), the SENTENCE
(`raise_set_traversal_depth_exceeded`), and the neutral default (`8`) were
already single-owned; this family is the CHECK half only.

Mechanism census (re-derived at WT bytes via `depth` / `_MAX_LOGIC_DEPTH` /
`assert_set_traversal_depth` / `set_traversal_depth_cap` / `nesting exceeded`
greps over all package `.py`, plus a `> .*DEPTH` comparison sweep; HEAD
cross-check via `git show HEAD:` for every member). Pre-change WT members,
exactly 6 check definitions:

- `utils/input_values.py::assert_set_traversal_depth` (`:249-264`): `if depth
  > set_traversal_depth_cap(set_cls)` + the shared raiser. One definition;
  the owner.
- `filters/sets.py::FilterSet._collect_nested_visibility_querysets_async`
  (`:3014-3015` WT, `:2920-2921` HEAD): `if _depth > cls._MAX_LOGIC_DEPTH:
  cls._raise_logic_depth_exceeded()`. Restatement 1, COMPOSED.
- `filters/sets.py::FilterSet._check_permission_depth` (`:3087-3088` WT,
  `:2991-2992` HEAD): same 2 lines. Restatement 2, COMPOSED. (The
  family-hook override called by the shared `_run_permission_checks`
  facade; the hook contract is the mixin's, the guard body was the
  restatement.)
- `filters/sets.py::FilterSet._evaluate_logic_tree` (`:3413-3414` WT,
  `:3317-3318` HEAD): same 2 lines. Restatement 3, COMPOSED.
- `filters/sets.py::FilterSet.apply_sync` (`:3729-3730` WT, `:3633-3634`
  HEAD): same 2 lines. Restatement 4, COMPOSED.
- `filters/sets.py::FilterSet.apply_async` (`:3793-3794` WT, `:3697-3698`
  HEAD): same 2 lines. Restatement 5, COMPOSED.

These are restatements, not enforcement sites: an enforcement site composes
the definition (the `pipeline_write_phase` precedent), while the five inline
the `>` comparison. All five raised through `FilterSet._raise_logic_depth_exceeded`,
which already composed the owner's raiser with the logical-branch triple -
so the sentence was shared and only the comparison was spelled six times.

Post-change shape: the five are one-line composers of the FilterSet-side
binding `FilterSet._assert_logic_depth` (`:2958-2983`), which binds the
(`logical-branch`, `filter`, `FilterSet`) triple once and composes the owner
by name. `_raise_logic_depth_exceeded` is gone (renamed-and-reshaped into
the binding; a raise-only helper with zero callers would be dead code, and
inlining the triple 5x would trade a 6->1 check consolidation for a new 5x
triple spelling). The binding carries a concrete responsibility - the
family's triple - so it stays per principle 11.

Roles of the connected sites:

- Consumer (pre-existing, untouched): `utils/permissions.py::run_active_input_permission_checks`
  (`:725`) composes the owner with the (`related-branch`, `related`, ``)
  triple for the related recursion shared by both families.
- Declaration (not a check): `FilterSet._MAX_LOGIC_DEPTH: ClassVar[int]`
  (`:1327`) binds the default; the C1 value challenge moves the constant
  alone (R6).
- Framework (not the rule): `sets_mixins.py::ActiveInputPermissionMixin._check_permission_depth`
  (`:712`, no-op default) and `._run_permission_checks` (`:764`, calls the
  hook). The no-op is intentional - orders have no operator bag (R4).
- Covered without its own check: `FilterSet._q_for_branch` re-enters
  `_evaluate_logic_tree` across the `.qs` boundary (counter via the
  `_logic_depth` stash), so the entry check covers both helpers (R5).

Oracles (all independent - they spell literal boundaries/messages or drive
real inputs; none reads the owner's body; the knob reads below are the
contract INPUT, and the raised-subclass row pins knob->behavior):

- `tests/utils/test_input_values.py`: resolution table (absent/None/int/
  garbage knob), boundary (4 passes / 5 raises at cap 4), knobless
  sentence, `FilterSet._MAX_LOGIC_DEPTH == DEFAULT` pin, plus the NEW
  structural gate.
- `tests/filters/test_sets.py`: one raise-past-cap row per site (all five),
  the raised-subclass row (`_MAX_LOGIC_DEPTH = 32` admits a 12-deep
  chain), the mixed logic+related recursion row, plus the NEW non-int-knob
  migration row.
- `tests/utils/test_permissions.py`: related-recursion cap, hostile-label
  cap, knobless-default rows through the shared walk.
- `tests/test_sets_mixins.py`: the no-op hook row.
- `examples/fakeshop/test_query/test_kanban_api.py::test_deeply_nested_self_referential_dependency_filter_is_capped`:
  live `/graphql` HTTP row - a 10-deep self-referential filter returns the
  typed cap error, never a 500.

Projections: the owner/binding/consumer docstrings (the binding docstring is
new in this change and carries the decided migration + the triple contract);
the standing `depth-cap-split` index row (R1's home); the naming file
artifact's F-NEW section (orientation only - line numbers stale, contract
re-derived). No GLOSSARY/TREE/KANBAN anchor (zero-hit grep) and no spec
owns the cap sentence (spec-028 mentions traversal prose only).

## Verification

### Matrix

1. Cross-flavor policy mirroring - SEARCHED. Orders: no operator bag, so
   no logic cap; its related recursion is capped inside the shared walk,
   which already composes the owner (R4). Mutations / forms /
   `rest_framework`: no set-input traversal caps; their depth-shaped rules
   are the excluded R1-R3 (different subject, phase, and message each).
   Types / optimizer / testing: no set-input walks; the remaining `depth`
   tokens are cache keys and overlap counters, not checks (R8). Census:
   pre-change `assert_set_traversal_depth` consumers = the permissions
   walk only; pre-change `_MAX_LOGIC_DEPTH` readers = the 5 sites + the
   declaration + the owner's two static reads.
2. Sync/async twins - SEARCHED. `apply_sync` / `apply_async` carry twin
   composers, kept in step (same one-liner, same binding). The async
   nested pre-walk has no sync twin by construction - it exists to await
   async-only `get_queryset`s before the sync `.qs` read. The permission
   core is single-colored with family hooks; both colors route through
   the same related-branch assert.
3. Derived rather than repeated knowledge - SEARCHED. The cap value flows
   one chain (constant -> declaration -> resolution); the message cap is
   read from the same helper as the check; the boundary now lives in one
   body. No remaining derivation of the rule's facts.
4. Inverse / round-trip pairs - SEARCHED. Check and raise are the two
   halves of one guard, each owned (assert / raiser); the binding joins
   them for the filter family. No encode/decode or pack/unpack pair.
5. Contracts restated in another medium - SEARCHED. Every medium a change
   moves is classified in System trace: production (1 definition +
   binding + 6 composers), oracles (behavioral pins per site + owner
   table + live row), the structural gate, prose (binding docstring).
   The one test docstring naming the old helper was updated in the same
   change; historical `dry-file-*` records keep their bytes (durable
   records, dot-form/bare mentions, invisible to the citations gate).
6. Enforcement by omission - SEARCHED. Order no-op (R4, contract source:
   mixin docstring + no operator bag exists), `_q_for_branch` (R5,
   covered by re-entry), knobless sets taking the default (oracle-pinned,
   the owner's contract). No gap: each absence has a contract source or
   a covering check. Zero defects filed from this axis.

### Challenges

Each change posited against the pre-change tree, counting authoritative
definitions of the CHECK (consumers, oracles, projections listed, never
counted):

- C1 (boundary): `>` becomes `>=`, or the off-by-one moves. Pre: 6 (the
  owner body + 5 inline comparisons). Post: 1. Oracles pin the boundary
  both sides (4 passes / 5 raises at cap 4 at the owner; cap+1 raises at
  every site). F1.
- C2 (budget sourcing): a subclass raises the knob; a set drops it; a
  knob arrives None or non-int. Pre: 5 strict direct reads + 1 lenient
  resolution - agreeing on int/absent knobs, differing on None/non-int
  (strict: `TypeError`/`AttributeError` on the comparison; lenient: the
  neutral default). Post: 1 (lenient). The owner's oracles pin the full
  table including `_NoneKnob`/`_Garbage` -> default, and no oracle
  anywhere pins the strict `TypeError`; the knob contract is
  `ClassVar[int]`, so the divergence sits outside the supported domain,
  and the raise half of the SAME check already used the lenient read for
  the message cap. Decision: adopt lenient (the disclosed migration
  point, decided here with evidence, recorded at the binding). F1.
- C3 (refusal sentence): wording change. Pre: 1 (the raiser; all 6 paths
  already composed it). Post: 1. No change; confirms the sentence was
  never part of this family's count.
- C4 (walk identity): the `logical-branch` / `filter` / `FilterSet`
  words change. Pre: 1 (the old wrapper). Post: 1 (the binding). The
  related-branch triple at the permissions call site is a different
  walk's parameter, not a second definition (R7).

## Findings

### F1 - Set-traversal depth-cap check (CONFIRMED + CONSOLIDATED, 6 -> 1)

Contract + variation: a set-input walk fails closed when its depth
counter passes the set's budget. Varies on the boundary (C1), the budget
sourcing (C2), the sentence (C3, already single), and the walk-identity
words (C4, per-walk parameters).

Sites + roles: owner `utils/input_values.py::assert_set_traversal_depth`
(definition); 5 former definitions now one-line composers via the
`FilterSet._assert_logic_depth` binding (consumer of the owner,
definition of the filter triple); 1 pre-existing consumer (the
permissions walk); oracles and projections as inventoried above.

Owner + lifetime (principle 7): state = depth counter + set class;
effects = return or raise the typed error; lifetime = pure derivation,
nothing stored ("not cached", principle 4). The narrowest cohesive owner
every legitimate consumer can import: `utils/input_values.py` already
owns the budget, the sentence, and the check shape, and both families
import it without a cycle (its own docstring states the no-cycle
contract). No reversed dependency; host-module size not a criterion.
The triple binding stays at `FilterSet`: family-specific words the
related-branch call site must not share (a shared triple needs a mode
flag, principle 5).

Migration: each former 2-line site -> `cls._assert_logic_depth(_depth)`;
`_raise_logic_depth_exceeded` -> `_assert_logic_depth` (triple binding
kept, check delegated); `raise_set_traversal_depth_exceeded` import
dropped from `filters/sets.py` (still used inside the owner);
`NoReturn` dropped from the `typing` import (only the deleted signature
used it). Net production +26/-24 over `ITEM_BASELINE`.

Distinct behavior: the C2 lenient sourcing (non-int knob caps at the
default with the typed error instead of an incidental `TypeError`) is
the only observable change, on contract-violating input only, recorded
at the binding docstring. Supported inputs (int knob incl. raised
subclass, absent knob) behave identically - the direct read and the
owner agree there by construction (`ClassVar[int]` + the oracle-pinned
resolution table).

Behavioral proof (all execution-verified in slot-2, fresh sync):

- Post-change depth scope (owner module + all 8 filter depth rows +
  permissions + mixin modules): 120 passed, 0 failed
  (`dry-20261001T210820-8ad783`). Rejects: the consolidation breaking
  any site, the boundary, the raised-subclass knob, or the shared walk.
- Full `tests/filters/test_sets.py` + the live HTTP cap row: 311 passed
  (`dry-20261001T211058-37e5dd`). Rejects: regressions outside the depth
  rows and any wire-shape change at the live tier.
- Pre-change baseline of the owner module: 25 passed
  (`dry-20261001T210658-518881`).
- Failability entry 1 (hand copy of the owner body at one site,
  behavior-preserving): gate fails, all 33 behavioral rows pass -
  `pinned` (`dry-20261001T210929-b5607c` full run +
  `--only 1` re-measurement agreeing). Rejects: a gate that cannot fail
  and a control that is not behavior-preserving.
- Failability entry 2 (strict inline read restored at one site): exactly
  the gate + the migration test fail; the migration row crashes with the
  predicted `TypeError: '>' not supported between instances of 'int'
  and 'str'` (`dry-20261001T210929-b5607c`). Rejects: a migration test
  that passes pre-change.

Structural gate: `tests/utils/test_input_values.py::test_filter_depth_cap_checks_compose_the_shared_assert`
- exact 7-hit AST census over `filters/sets.py` (1 knob declaration, 0
attribute reads, 1 owner call inside the binding, 5 composers in the 5
known methods). Population justification: all five historical bypasses
lived in this file; the plausible bypass is re-inlining here. Negative
control: entry 1 above (composers 5 -> 4; every behavioral oracle
passes the control). `tests/` tier: the gate asserts a package-source
structural property unreachable from any GraphQL query (f39/f45
precedent); the behavior it guards is covered live.
`test_evaluate_logic_tree_caps_a_non_int_knob_at_the_neutral_default`
pins the C2 decision end to end at a consumer (`tests/` tier: no
fakeshop filterset carries a non-int knob, and none may be added inside
an item).

Coupling: none. Single-file production edit plus two test files; no
generated slot, no import cycle (the `filters/sets.py` ->
`utils/input_values.py` edge predates this change).

Freshness: `utils/input_values.py` WT `463f81a8` / HEAD `929e81b5`
(pins verified, file untouched); `filters/sets.py` HEAD `76abccb0`,
WT pre-edit `14884190` (pin verified), WT post-edit `17dae905` (equals
the prove record's pre-mutation blob - copy==shared corroborated);
`tests/filters/test_sets.py` post `ecdc8d57`;
`tests/utils/test_input_values.py` post `02885e26`;
`utils/permissions.py` WT `bb3e0493` / HEAD `0e13b869`;
`sets_mixins.py` WT `c496feb2` / HEAD `42e8c862`;
`orders/sets.py` WT `8ce11495` / HEAD `a8cd33c7`;
`orders/inputs.py` WT `2f6e1a2c` / HEAD `c7a91946`;
`utils/inputs.py` WT `8839b38d` / HEAD `0b7d353c`;
`rest_framework/inputs.py` WT `af8cea5c` / HEAD `6ad29171`;
`extensions/resource_policy.py` WT `2971618b` / HEAD `289dc159`;
`optimizer/selections.py` WT `3b1c0bf8` / HEAD `ed22de27`;
`extensions/debug.py` WT `b26a7897` / HEAD `fe67aad2`;
`utils/truth.py` WT `711352b1`, untracked (no HEAD blob; read-only
inspection for reader semantics);
`tests/utils/test_permissions.py` WT `71e1ff4b`;
`tests/test_sets_mixins.py` WT `05c2bc8e`;
`examples/fakeshop/test_query/test_kanban_api.py` WT==HEAD `7dcb922b`
(clean). Searched population: every package `.py` (`depth` +
knob/assert/cap/nesting greps + the `> .*DEPTH` sweep) at WT bytes,
HEAD cross-check per member. Any fingerprint change reopens this
finding.

### R1 - Meta-value container cap (EXCLUDED, converge with `depth-cap-split`)

`utils/inputs.py::_MAX_META_VALUE_DEPTH` (64) bounds the
schema-construction metadata cache-key walk, with its own cycle guard,
cap, and metadata-flavored message. Different subject, phase, cap, and
sentence from the set-input traversal budget. Standing rejection
trigger re-checked at WT bytes: still unfired. Recorded home: the
standing row. Trigger: a set-input walk composing the meta walker for
its budget.

### R2 - Nested-serializer write cap (EXCLUDED)

`rest_framework/inputs.py::_NESTED_MAX_DEPTH` (5, `>=` on path length)
bounds nested serializer write paths. Different subject (write-path
serializer nesting vs read-path set traversal), operator, and message.
Trigger: nested writes adopting set-traversal budgets.

### R3 - Request policy caps (EXCLUDED)

`ResourcePolicy.max_depth` / `max_value_depth` bound the request's
query AST and variable values. Per-request policy objects, not
per-set-class knobs; different enforcement point (extension walk vs
set recursion). Trigger: policy caps expressed per set class.

### R4 - Order-side hook no-op (EXCLUDED, intentional)

The mixin default `_check_permission_depth` is a no-op because orders
have no logical operator bag; order related recursion IS capped, inside
the shared walk that composes the owner. Contract source: the mixin
docstring plus the family semantics (no `logic_keys` on the order
traversal). Recorded home: the mixin docstring (already states it).
Trigger: `OrderSet` gaining logical operators.

### R5 - `_q_for_branch` carries no own check (EXCLUDED, covered)

`_q_for_branch` re-enters `_evaluate_logic_tree` across the `.qs`
boundary (counter via the `_logic_depth` stash), so the entry check
covers both helpers - the "both helpers cap" prose describes one
check, not two. Trigger: a `_q_for_branch` recursion path that
bypasses `_evaluate_logic_tree`.

### R6 - Knob declaration stays at `FilterSet` (EXCLUDED, declaration)

`_MAX_LOGIC_DEPTH: ClassVar[int] = DEFAULT_SET_INPUT_TRAVERSAL_DEPTH`
declares the default binding; it is not a check restatement (C1 moves
the constant alone). Declaration-vs-mechanism split, principle 1.
No trigger foreseen.

### R7 - Walk-identity triples stay per walk (EXCLUDED, parameters)

The filter triple (at the binding) and the related-branch triple (at
the permissions call site) name WHICH walk hit the cap - per-caller
words, not a shared rule. Sharing them needs a mode flag (principle
5). Recorded homes: the binding docstring + the existing call sites.
Trigger: a third walk needing one of the existing triples verbatim
(it then composes that binding).

### R8 - Non-cap `depth` counters (EXCLUDED, different mechanism)

`optimizer/selections.py` (cache-key component) and
`extensions/debug.py` (overlap bracket counter) count but never cap;
not checks at all. No trigger (different mechanism entirely).

Sub-rules for Worker-0: none beyond F1. R1 converges on the existing
`depth-cap-split` row; R2-R8 are exclusions recorded at their homes
above, not decomposed rules. (Owner-docstring clauses for R2/R3/R5
would touch concurrent-dirtied lines and are owed only if Worker-0
judges the artifact record insufficient; R1/R4/R6/R7 already have
durable homes.)

## Defects

- D1 (minor, cosmetic, misuse-input-only): `utils/input_values.py::raise_set_traversal_depth_exceeded`
  renders the RESOLVED cap in the `_MAX_LOGIC_DEPTH={cap}` detail, so a
  non-int knob (e.g. `"10"`, falling back to 8) reports
  `_MAX_LOGIC_DEPTH=8` - misattributing the fallback as the knob.
  Pre-existing at HEAD (same logic under `getattr`), outside the knob's
  `ClassVar[int]` contract, and on lines currently concurrent-dirtied
  (truth migration), so unfixed here. The consolidation does not depend
  on it (the migration test matches only `nesting exceeded`, deliberately
  not pinning the detail). Owner: `utils/input_values.py::raise_set_traversal_depth_exceeded`.
  Routes to the maintainer via Worker-0.

## Pending execution

None. Every proof executed. Sharded/PG cells: inapplicable-by-construction
for Worker-2 to judge - the changed lines are a pure integer comparison
plus a raise that fires before any database touch, with no alias,
routing, or dialect branch; the in-DB regression witness (full filter
module + live HTTP cap row) ran green on the default cell.

## Judgment

CONFIRM-consolidated: the check half of the traversal-depth rule was
spelled 6 times (1 owner body + 5 filter-inline restatements) and now
lives in 1, with the 5 sites composing by name through a FilterSet-side
triple binding. Challenges C1/C2/C4 count 1 post-change (C3 already
did); 8 exclusions carry contract differences + triggers; 1 minor
pre-existing defect routed; 0 pending executions.

## Implementation (Worker-1)

Production (`django_strawberry_framework/filters/sets.py`, +26/-24 vs
`ITEM_BASELINE`, 8 hunks, all on HEAD-clean lines verified by hunk map
- the import-block hunk adds `truth` on an adjacent line, attributed by
content, untouched):

- import `assert_set_traversal_depth`, drop
  `raise_set_traversal_depth_exceeded` (still used inside the owner);
- drop `NoReturn` from the `typing` import (only the deleted signature
  used it);
- `_raise_logic_depth_exceeded` -> `_assert_logic_depth` (triple binding
  + owner composition, with the decided C2 contract in the docstring);
- 5 sites -> `cls._assert_logic_depth(_depth)` one-liners.

Tests: `tests/filters/test_sets.py` (+25/-1: the non-int-knob migration
row + the helper-name docstring line);
`tests/utils/test_input_values.py` (+69/-0: the 7-hit AST census gate +
walker). `tests/` tier for both (structural property / unreachable
knob). Banned-word check on all additions: zero hits. No `pragma: no
cover`, no new cast/Any/suppression, `ALLOWED_ANY` untouched, no
CHANGELOG.

Gates (all in slot-2, post-edit bytes): `ruff check` + `ruff format
--check` clean on the 3 touched paths; `basedpyright` 0 errors, 0
warnings, 0 notes (`dry-20261001T211038-33dbbd`); `check_any.py` 128
uses at 89 sites, exit 0 (`dry-20261001T211048-1ee603`);
`check_truthful_reads.py --check` errors 0 (`dry-20261001T211049-3a1159`).
Orphan sweep for the renamed helper across package/tests/examples/
scripts: zero hits (historical `dry-file-*` records keep their bytes).

Ledger-ready rows for Worker-0 (not applied - workers never edit the
plan):

- `django_strawberry_framework/filters/sets.py` - Family
  `traversal-depth-cap-check` (f51) - `FilterSet._assert_logic_depth`
  (NEW binding) + 5 one-line compositions + 2 import-line changes
  (`_raise_logic_depth_exceeded` removed).
- `tests/filters/test_sets.py` - Family `traversal-depth-cap-check`
  (f51) - `test_evaluate_logic_tree_caps_a_non_int_knob_at_the_neutral_default`
  + helper-name docstring line.
- `tests/utils/test_input_values.py` - Family `traversal-depth-cap-check`
  (f51) - `test_filter_depth_cap_checks_compose_the_shared_assert` +
  `_filter_depth_cap_spellings` walker.

## Independent verification (Worker-2)

Pass 1, address `dry/travcap-f51/verify-1` (slot-3, synced after W1's
edits; copy fresh, shared tree unmoved at every run). HEAD `dd0b6691`
unmoved; `ITEM_BASELINE=38dd09a1` resolves as a commit. Procedural note:
the dispatch order had me read this artifact after the target, the
item-scoped diff, and every touched site; every number below is
re-derived from bytes via the cited command, nothing inherited. Raw
`path:NN` below is the per-cycle scratchpad form this artifact class
allows.

### Own trace (re-derived from bytes)

Rule: a set-input walk fails closed when its depth counter passes the
set's budget (`if depth > cap: raise the typed sentence`).

Pre-change check definitions, exactly 6, censused at baseline
(= pre-edit WT) via `git show 38dd09a1:` and cross-checked at HEAD via
`git show HEAD:`:

- `utils/input_values.py::assert_set_traversal_depth` — baseline
  `:249-264`, HEAD `:272-282`. `if depth > set_traversal_depth_cap(...)`
  + the shared raiser. The one composed definition.
- `filters/sets.py::FilterSet._collect_nested_visibility_querysets_async`
  — baseline `:3014-3015`, HEAD `:2920-2921`. Inline 2-liner.
- `filters/sets.py::FilterSet._check_permission_depth` — baseline
  `:3087-3088`, HEAD `:2991-2992`. Inline 2-liner.
- `filters/sets.py::FilterSet._evaluate_logic_tree` — baseline
  `:3413-3414`, HEAD `:3317-3318`. Inline 2-liner.
- `filters/sets.py::FilterSet.apply_sync` — baseline `:3729-3730`,
  HEAD `:3633-3634`. Inline 2-liner.
- `filters/sets.py::FilterSet.apply_async` — baseline `:3793-3794`,
  HEAD `:3697-3698`. Inline 2-liner.

All five inline `if _depth > cls._MAX_LOGIC_DEPTH:` then
`cls._raise_logic_depth_exceeded()`, which composed the owner's raiser
with the logical-branch triple — sentence shared pre-change,
comparison spelled six times.

Single-ownership around the check (package-wide grep, current WT):
budget `set_traversal_depth_cap` 1 def + 2 internal reads (raise `:234`,
assert `:258`); sentence `raise_set_traversal_depth_exceeded` 1 def + 1
internal call (`:259`); default `DEFAULT_SET_INPUT_TRAVERSAL_DEPTH` 1
def (`:65`), read at the declaration and the owner fallback. Zero
second bodies.

Roles (mine): owner `assert_set_traversal_depth` (definition);
declaration `FilterSet._MAX_LOGIC_DEPTH: ClassVar[int]` (`:1327`,
baseline `:1327`, HEAD `:1300`); pre-existing consumer
`utils/permissions.py::run_active_input_permission_checks` (`:725`,
triple `related-branch`/`related`/no-subject); framework
`sets_mixins.py::ActiveInputPermissionMixin._check_permission_depth`
(`:712`, docstring-pinned no-op default) and `._run_permission_checks`
(`:742`, calls the hook); covered-without-own-check
`FilterSet._q_for_branch` (`:3437`, stashes `_depth` on the sibling,
re-enters `_evaluate_logic_tree` via `filter_queryset`, zero own cap
lines). Post-change the five are one-line composers of the NEW
`FilterSet._assert_logic_depth` (`:2958-2983`), which binds the
(`logical-branch`, `filter`, `FilterSet`) triple once and holds the
single owner call (`:2976`); composers at `:3021`, `:3093`, `:3418`,
`:3733`, `:3796`, mapped by AST to the five known methods.

Challenges (my counts): C1 boundary 6 pre / 1 post. C2 budget
sourcing 5 strict direct reads + 1 lenient resolution pre (agreeing on
int/absent, differing on None/non-int) / 1 lenient post. C3 sentence 1
pre / 1 post (never in this family's count). C4 walk identity 1 pre
(old wrapper) / 1 post (binding); the related-branch triple is a
different walk's parameter (all three words differ, read both call
sites).

Owner I would choose: `utils/input_values.py::assert_set_traversal_depth`
— already owns budget + sentence + check shape, both families import
it without a cycle (runtime edge one-way; its `FilterSet` import is
`TYPE_CHECKING`-only), pure derivation with nothing stored. The triple
binding stays at `FilterSet` (family words the related-branch site
must not share).

### Reconciliation with ## Findings

Zero material differences: same 6 members with identical baseline/HEAD
line numbers, same roles, same owner, same C1–C4 counts pre and post,
same migration shape. Two verdict-neutral observations carried for
Outcomes transcription: (O-W2-1) R5's durable home already exists
in-code — the `_evaluate_logic_tree` docstring states both helpers cap
at the entry check — so the owed-only-if-insufficient clause is moot
for R5. (O-W2-2) R2/R3 owner-docstring clauses stay deferred; the
artifact + plan-index record is sufficient per cycle precedent and no
ledger expansion into far-field files is warranted.

### Enumeration, matrix, roles, oracles (steps 2–3)

Member-by-member: my census above reproduces all six definitions at
both byte-states; the budget/sentence/default single-ownership, the 5
filter readers, the declaration, and the framework sites all match.
Baseline package-wide `git grep` confirms the matrix census verbatim:
pre-change `assert_set_traversal_depth` consumers = the permissions
walk only (import + `:725` call; `filters/sets.py` used the raiser);
pre-change `_MAX_LOGIC_DEPTH` code readers = 5 sites + declaration +
owner's two static reads (`:212`, `:240`) — every other hit a
docstring, comment, or the f-string literal. Orders carries zero
`_MAX_LOGIC_DEPTH` hits and its traversal binds
`logic_keys=frozenset()` — no operator bag, no logic cap. All six
matrix axes were SEARCHED (no inapplicability claimed); each holds
against the real surface: twins kept in step (both `apply_*` compose
the binding; the async pre-walk awaits async-only querysets by
construction); cap chain constant → declaration → resolution with the
message cap read from the same helper as the check; check + raise as
owned halves joined by the binding; every medium classified
(production 1 + binding + 6 composers, oracles, gate, binding
docstring); omission axis clean (order no-op with mixin-docstring
contract source, `_q_for_branch` covered by re-entry, knobless default
oracle-pinned). Oracle integrity: the 25 minus-lines are production +
1 test docstring line; zero `assert`/`raises`/`match`/`expect`
expectation lines touched; literal boundaries/messages intact; no
oracle reads the owner's body (test knob reads are the contract
INPUT).

### Observable equivalence + points (a)–(b) (step 4)

Point (a) — THE call, lenient migration: IN-MANDATE, decided
correctly. (1) No oracle anywhere pins the strict `TypeError`:
searched `tests/` (all tiers) + `examples/` incl. live suites —
non-int-knob rows exist only as lenient pins (owner resolution table
`_NoneKnob`/`_Garbage` → default; the NEW migration test) and every
`TypeError` pin in the depth files is unrelated (form-field, UNSET,
MappingProxy). (2) Divergence outside the `ClassVar[int]` contract:
declaration `:1327` with raise-the-cap-on-a-subclass prose; int,
raised-int, and absent knobs agree between the direct read and the
owner by construction. (3) Raise-half-already-lenient: the deleted
helper called the raiser, which resolves its message cap through the
lenient `set_traversal_depth_cap` — pre-change behavior on non-int
knobs was incoherent (strict accident at the comparison, lenient
default in the unreachable message), and the consolidation resolves
the incoherence toward the shipped half. (4) Supported inputs
identical: boundary (cap 4: 4 passes / 5 raises), raised-subclass (32
admits 12-deep), absent-knob (default) rows all green in my own
120-run below; my faithful-strict control showed int-knob rows pass
under both shapes. Preserving the strict accident would have required
growing a strict arm in the owner to pin an unpinned `TypeError` no
shipped consumer can produce — the worse trade on every principle-8
axis. The migration point was disclosed in the plan index row itself
("migration decision: strict-vs-lenient knob sourcing"), decided with
evidence, recorded at the binding docstring, and pinned by the
migration test. No maintainer word needed.

Point (b) — binding shape: `FilterSet._assert_logic_depth` correct,
5 direct owner calls correctly refused. The binding carries the
family's triple (principle 11: boundary name five callers depend on);
inlining the triple 5× would trade a 6→1 consolidation for a new 5×
spelling, and sharing one triple across walks needs a mode flag
(principle 5) the genuinely-differing related-branch triple (verified
all three words differ) cannot take. The binding docstring records
the triple contract, the five sites, and the decided C2 semantics.

### Rejections, freshness, points (c)–(d), pending, coupling, concurrency (step 6)

R1–R8 each carry contract difference + trigger + home, verified by
reading: R1 meta cap 64 with own cycle guard/message, standing
`depth-cap-split` row re-checked unfired at WT bytes (converge, home
stands); R2 nested-write cap 5 with `>=` on path length; R3
per-request policy pair enforced in the extension walk; R4 mixin
no-op with docstring contract source + empty order `logic_keys`; R5
re-entry cover (no own cap lines; entry docstring states the cover);
R6 declaration-vs-mechanism split; R7 per-walk parameters with
mode-flag refusal; R8 cache-key/overlap counters that never cap. The
R2/R3/R5 owed-only-if-insufficient deferral is judged sufficient
(O-W2-1/O-W2-2 above).

Freshness re-hashed same-kind, all exact: `filters/sets.py`
`17dae905` (hash-object), `test_sets` `ecdc8d57`, `test_input_values`
`02885e26`, `input_values` `463f81a8` untouched (item diff 0 lines;
baseline blob identical); HEAD `76abccb0`/`929e81b5`; baseline
`14884190`/`fc21a7a8`/`69f7b2c0`. Connected pins spot-checked 10/10
exact incl. `truth.py` `711352b1` untracked and `test_kanban_api.py`
`7dcb922b` clean both bytes.

Point (c) — orphan sweep for `_raise_logic_depth_exceeded`: zero hits
in package/tests/examples/scripts, verified myself. Historical hits
survive only in this artifact (the migration record itself),
untracked `temp-tests/` scratch copies, and two `dry-file-*` durable
records in dot-form/bare/`cls.` mentions — none a `path::Symbol`
citation, and `docs/` is deliberately out of `check_citations.py`
(the gate resolves `path::Symbol` in first-party `.py` + KANBAN only).
Exception judged sound.

Point (d) — gate negative control, re-derived with FRESH controls at
my address (not W1's entries): (i) behavior-preserving bypass
(composer → direct owner call, same triple) at `_evaluate_logic_tree`:
PINNED — exactly the gate fails, all 11 behavior rows pass
(pre-mutation 12 passed). (ii) Faithful pre-change shape (strict
inline `if _depth > cls._MAX_LOGIC_DEPTH:` + shared sentence via the
raiser): PINNED — exactly gate + migration test fail, int-knob rows
pass, migration crashes with the verbatim predicted `TypeError: '>'
not supported between instances of 'int' and 'str'`. Both restores
proved by byte comparison (blob `17dae905` before == after). The
7-hit census is exact per my independent AST re-derivation (1
knob-spelling at `FilterSet`, 0 knob-reads, 1 owner-call in the
binding, 5 composers in the 5 known methods); `filters/sets.py`-only
scope is right (all five historical bypasses lived there; the
plausible bypass is re-inlining there, exactly the knob-read arm).

Pending-None correct (every proof executed; cells inapplicable, not
unverified — judged below). Coupling none correct (single-file
production edit + 2 test files; the `filters/sets.py` →
`utils/input_values.py` edge predates, direction unchanged, no cycle).

Concurrency re-derived from `git diff HEAD` on all touched paths: the
12 item hunks avoid every concurrent hunk. Typing-import hunk
byte-identical in both diffs; input-values import swap sits below the
hunt-added `truth` line (present in baseline AND WT, absent at HEAD —
preserved); binding + all 5 composers byte-identical hunks in clean
spans with the truth-migration neighbors (`-2965`/`-2976`) split into
separate hunks; `test_sets.py` migration test purely additive and the
docstring minus-line clean; `test_input_values.py` import + gate
hunks purely additive on baseline bytes (HEAD-diff merges there are
adjacency-only: baseline already carries the concurrent docstring and
the hostile-qualname deletion). `input_values.py` HEAD-drift (11
hunks) is entirely truth-migration + except-`BaseException`
deletions. Zero concurrent lines edited, reverted, or tidied.

### Prose rules, point (f), point (e), gates, behavior (step 7)

AGENTS.md prose: no process provenance (banned-word sweep of
additions zero hits); `path::Symbol` citations only (binding
docstring cites the resolving owner; zero `path:NN` in added code);
zero stale `::_raise_logic_depth_exceeded` citations in gated `.py`;
additions ASCII-clean, all ≤ 99 chars; no CHANGELOG, no new
`tests/base/` files, no `pragma: no cover`, no new cast/Any/
suppression, `ALLOWED_ANY` untouched (0-line diff on
`scripts/check_any.py`), `NoReturn` drop safe (zero remaining uses).

Point (f) — `tests/` tier for BOTH new tests: correct. The AST gate
asserts a package-source structural property unreachable from any
GraphQL query (precedent-cited; the guarded behavior is covered
live). The migration test's non-int knob is query-unreachable: zero
fakeshop filtersets carry any `_MAX_LOGIC_DEPTH`, let alone non-int
(all six filterset files + `test_library_api.py` checked), and DRY.md
Tests forbids adding the fixture inside an item ("never a new example
model inside an item") — correctly, since a contract-violating knob
must never ship in the example project; no missing-fixture defect is
owed.

Point (e) — D1: pre-existing at HEAD (same `cap_detail` logic under
`getattr`), consolidation-independent (migration test matches only
`nesting exceeded`, never the detail; D1 lines untouched, 0-line item
diff, currently concurrent-dirtied so correctly unfixed), correctly
routed to the maintainer via Worker-0 as minor/cosmetic/misuse-input-only,
non-blocking. Filing against the owner file is fully compatible with
the untouched claim — DRY.md Defects routes traced defects without
fixing inside the item.

Ruff on all three touched paths: `ruff format --check` 3 files
already formatted; `ruff check` all passed. Type gates re-run in my
copy, matching the run-11 baseline exactly: basedpyright 0/0/0
(`dry-20261001T212137-6d902a`); `check_any.py` 128 uses at 89 sites,
exit 0; `check_truthful_reads.py --check` tier-1 0, errors 0. mypy
never run, never cited.

Behavior re-run myself in slot-3: depth scope (owner module + 8
filter depth rows + permissions + mixin modules) 120 passed
(`dry-20261001T211859-0806b2`); full `tests/filters/test_sets.py` +
live HTTP cap row 311 passed (`dry-20261001T211914-60a8da`). Zero
Worker-2 defects. Sharded/PG inapplicable-by-construction judged
sound: the changed lines are a pure integer comparison + raise firing
before any database touch, with no alias, routing, or dialect branch;
the in-DB regression witness ran green on the default cell.

### Verdict

`verified`, plain. F1 CONFIRM + CONSOLIDATED 6→1 stands on
independently re-derived evidence; R1–R8 exclusions stand with
triggers + homes; D1 routed; no pending execution; no coupling. No
`## Defects` entries from Worker-2 (zero found). Ledger-ready rows in
`## Implementation (Worker-1)` are endorsed as written.
