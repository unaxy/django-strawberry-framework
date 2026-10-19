# DRY review: `walker-dead-selection-aliases`

Status: verified
Run: 0.0.15 2026-10-11-20

## System trace

Target: the selections import plus the underscore alias
block in [walker.py][walker] (HEAD `:49-58`, `:80-98`;
live/slot pre-edit +1 from a concurrent `:17` hunk).
Eight `selections.py` helpers bound to underscore
spellings; three suspects (`:96-98`) plus their feed
imports (`:52`, `:53`, `:57`). [walker.py][walker] is
dirty, but every hunk vs HEAD sits outside the touch
lines (concurrent hunt work, not ledger) — touch lines
verified HEAD-clean; siblings own disjoint files.
Two instruments over 497 tracked + 9 untracked `.py`
(506): word-exact `rg` (`\b` defeats the
`_with_runtime_prefix`-inside-the-longer-name trap) and
an AST visitor (497/497 parsed, Name/Attribute/import/
string roles). `_named_children`: 7 hits — walker
comment + store, extension comment + store + body load
(`:703`), test import from extension + call. Second
alias: 7 hits, same shape (`:706`). Third: exactly 2 —
walker comment + store, zero elsewhere; the 18-line
substring census is fully enumerated (longer names,
defs, prose). Extension's pair is live and stays; all
five kept walker aliases have readers (bodies/tests).
No star import from walker (16 repo-wide, none his),
no quoted/attr/getattr reader, no `__all__`, no
TYPE_CHECKING use. Specs cite public names only; the
spec-033 "both import them" lines are family-level
(they list names walker never imported), unfalsified.

## Verification

### Matrix

1. Cross-flavor: the walker/extension mirrors ARE the
target; no third mirror binds these names. Extension
pair live, kept.
2. Twins: inapplicable — import-time bindings, no await.
3. Derived-twice: both modules alias, never re-derive;
the deletion removes a dead binding, no logic.
4. Round-trip: inapplicable — one-way bindings.
5. Other media: specs cite public names; oracles
literal; `docs/dry` records describe this same
deadness, consistent; zero spec sentences falsified.
6. Omission: full family enumerated — 8 walker imports
(5 kept w/ readers, 3 dead), 2 extension aliases live.

### Challenges

- C1 (rename/remove a helper): dead import + binding
break at walker import — 2 touch points per alias, zero
logic. Principle-11 horn: obligation, no responsibility.
- C2 (signature change): transparent bindings need no
edit — count 0, confirming zero logic.
- C3 (a future reader via walker): would bless a dead
spelling as API; deletion closes the trap. Control:
deleting `_is_fragment` instead breaks bodies + tests.

## Findings

### F1: three dead aliases + three orphaned imports — deleted

- Contract: transparent private re-exports; no axes.
- Sites: walker imports + `:96-98` = dead definitions;
`:87-90` comment = projection, trimmed;
[selections.py][selections] = owner, untouched; extension
aliases = live, kept; test imports/calls = oracles.
- Challenges C1-C3; bar met on the principle-11 horn.
- Owner/lifetime: selections; import-time bindings,
no stored derivation.
- Migration: deleted 3 bindings + 3 imports + 4 comment
lines; nothing becomes a call (zero readers).
- Shrinkage: -10 net; see `## What shrinks`.
- Distinct: 5 kept walker aliases (body/test readers
each); extension's live pair; `:1964` prose still names
the selections function; nested_planner/connection zero
code hits. Index row for Worker-0:
`walker-dead-selection-aliases`, owner selections,
files walker/extension/selections, `consolidated`.
- Proof, all execution-verified: suites green before
AND after, identical counts — walker 199, extension
182, selections 30 (a live reader fails collection or
diverges across 411 tests). Probe: 6 names gone, 5
keeps + 2 extension aliases present. Census
failability: a planted reader found by BOTH instruments,
deleted uncommitted. No new tests — a non-existence
assertion is a barred census test. Six gates green.
- Negative control: none; bypass not the threat.
- Coupling: none; one file, HEAD-clean lines.
- Freshness: HEAD `c37a08a0`, baseline `ede7cfc3`;
blobs: walker live `02752d50`, HEAD `ddb35b44`,
slot post-edit `61d02873`; extension `36a733df`;
selections `e14e6e30`; tests `b1607a02`,
`9ade4151`, `303d0674`; spec-033 `019c8221`.
Population 506 `.py` (497 tracked + 9 untracked).

## Defects

None.

## Pending execution

None — every proof execution-verified.

## Judgment

Dead under two instruments over 506 files with a
failability pin; keeps and extension's pair evidenced.
10-line deletion, suite-green before/after, gate-clean,
zero spec sentences falsified. Ready to port.

## Independent verification (Worker-2)

Own trace (before reading Findings): full [walker.py][walker]
read (2026 lines). 8 selection imports feed 8 alias stores
only — zero bare code reads (the `response_key` hits are
locals). `_named_children`/`_node_children_with_runtime_prefix`/
`_with_runtime_prefix`: stores + comment, zero body/call/
import readers through walker. Kept: `_should_include`
test-only (8 calls), `_is_fragment` bodies + tests,
`_response_key` x4 / `_response_keys` x1 /
`_included_field_selections` x2 bodies.
[extension.py][extension] twins live (`:703`/`:706` +
test imports/calls) and survive — diff touches walker
only. Owner: [selections.py][selections] (pure deletion,
nothing to move). Bar: principle-11 horn, no machinery.

Census, two instruments: (1) word-exact `rg` with `\b`
(the `_`-is-word-char rule defeats the substring trap;
verified no false hit at the longer name) over all repo
`.py` — 16 name-hits on 14 lines in exactly 3 files:
7/7/2 per name; (2) AST visitor over 502 files, 0 parse
failures — from-walker WANT imports only
`_is_fragment`/`_should_include` in test_walker;
from-extension only the twin pair in test_extension;
zero attribute reads, zero string literals. Population:
497 tracked + 9 untracked = 506 (my 4-tree 502 + root
conftest/line_count/examples-init/docs-py, all
zero-hit). No `walker._X` reads, no unprefixed
from-walker reads, no star-from-walker (16 repo-wide),
no `__all__`, no `__getattr__`, no importlib/reload;
`walker_mod` reads 3 unrelated attrs. Principle-8:
import-time bindings only; observable surface unchanged
but private-name introspection, zero readers.

Reconciliation: every figure matches — 7/7/2, 506,
16 stars, all 9 fingerprints recomputed identical
(walker live `02752d50`/HEAD `ddb35b44`/post `61d02873`,
extension `36a733df`, selections `e14e6e30`, tests
`b1607a02`/`9ade4151`/`303d0674`, spec-033 `019c8221`,
HEAD `c37a08a0`). Line convention confirmed: artifact
cites HEAD, live/slot +1 via the `:17` hunk. Matrix:
axes 2/4 inapplicability sound (import-time bindings,
no await, one-way); axis 5 concur — spec-033 `:54`/`:535`
list `connection_node_children`, which walker never
imported, so the literal per-name reading was already
false pre-edit; family-level holds post-edit. C1-C3 and
no-new-tests (barred census test) concur. Pending
execution: correctly None.

Execution (pool full — no verify-1 copy; verified
read-only against slot-4 = live + exactly the 10
deletions, fingerprints prove freshness): 411 passed
post-edit (199/182/30; pre-edit collect identical);
surface probe (6 gone, 5 keeps + 2 extension present)
green; `ruff check` + `format --check` on post-edit
walker green. AGENTS.md prose: no process provenance,
`:NN` allowed for `docs/dry/dry-*.md`, 10 link headers
present. Defects: none. Verdict: verified.

## Implementation (Worker-1)

Address `dry/walker-dead-selection-aliases/consolidate`
(slot-4); live untouched, Worker-0 ports. Diff exactly
10 deleted lines in [walker.py][walker]; `ruff check
--fix` + `format` clean. Before → after: 199 → 199,
182 → 182, 30 → 30. Gates exit 0: truthful-reads,
trailing-commas, citations (3347), basedpyright,
floor, public-types 100.00% (2 pre-existing allows).

## What shrinks

Net package change over ITEM_BASELINE: +0/-10 lines in
[walker.py][walker] (3 dead bindings, 3 orphaned imports,
4 deadness-comment lines). No machinery added: no new
driver, registry, flag, helper, wrapper, or constant; no
test added (a non-existence test would be a barred census
test); no spec edit (no sentence falsified — the spec-033
"both import them" lines are family-level and already
list names walker never imported). What the deletion
removes: one import-time change obligation per alias (a
rename/removal in [selections.py][selections] could no
longer break walker at import for helpers walker never
calls), plus the trap where a future reader imports a
dead spelling from walker and silently blesses it as API.
Reader counts before → after, word-exact over 506 `.py`:
`_named_children` 7 → 5 (walker comment + store gone;
extension store/load/comment + test import/call stay),
`_node_children_with_runtime_prefix` 7 → 5 (same shape),
`_with_runtime_prefix` 2 → 0 (comment + store gone; the
kept `:1964` prose names the public selections function,
not the walker spelling). Owner
[selections.py][selections] keeps all three public defs;
[extension.py][extension] keeps its two live aliases
(body loads `:703`/`:706` + test imports/calls); the five
kept walker aliases keep their imports and bindings with
the readers evidenced in F1. Behavioral equivalence: the
411-test touching selection is green with identical counts
before and after, the import probe asserts the exact
post-edit surface, both type gates and the public-surface
gate verify the reduced module, and the census failability
pin (planted reader found by both instruments) proves the
zero is measured, not assumed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[extension]: ../../django_strawberry_framework/optimizer/extension.py
[selections]: ../../django_strawberry_framework/optimizer/selections.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
