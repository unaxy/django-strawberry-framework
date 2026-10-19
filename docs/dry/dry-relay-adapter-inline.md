# DRY review: `relay-adapter-inline`

Status: verified
Run: 0.0.15 2026-10-11-16

## System trace

[inspect-cmd][inspect-cmd]`::Command._resolve_row` called the same-name
one-call static adapter `Command._is_suppressed_relay_pk`, which unpacked 5
definition attributes and delegated to the module-level owner
[types-base][types-base]`::_is_suppressed_relay_pk`. The owner also serves
the `_build_annotations` performer. Two oracles pin the predictor:
[test-mgmt-inspect][test-mgmt-inspect]`::test_inspect_suppressed_pk_mirror_matches_synthesis`
(predictor-vs-built mirror) and
`::test_inspect_consumer_authored_pk_on_relay_type_reports_consumer_row`
(consumer-pk table row). Census: 1 production caller, 1 oracle caller, 0
other importers; standing specs cite only the owner.

## Verification

### Matrix

1. Cross-flavor mirroring: searched package-wide; no sibling predictor.
2. Sync/async twins: pure sync predicate; no twin surface.
3. Derived knowledge: the adapter derived nothing; the unpack now sits at
   the call site, plus the oracle's independent spelling (by design).
4. Round-trip pairs: one verdict function; no pair.
5. Other media: specs cite the owner (still resolving; owner untouched);
   adapter cites live only in per-cycle scratch (exempt).
6. Enforcement by omission: single call site; no unenforced member.

### Challenges

- C1 (new exemption): the owner body moves; predictor call and oracle
  unpack unchanged. Count 1 before and after: a principle-11 inline, not
  a count-2 consolidation.
- C2 (owner gains a parameter): the owner moves; performer, predictor,
  and oracle unpacks (all consumers) follow. Count 1; one fewer unpack
  spelling after the inline.

## Findings

F1 (consolidated): inline the adapter into `_resolve_row`. Contract: the
suppressed-pk verdict for one table row; varies only with the owner's
decision. Sites: adapter (deleted delegation), call site (consumer, now
composes the owner by name), owner (kept), mirror + table oracles (kept,
retargeted). Owner: the existing module owner by responsibility (serves
performer + predictor; pure function, no lifetime). Migration: 5-attribute
unpack + dispatch-order prose to the call site; adapter and its "not
recursion" comment deleted. Behavioral proof: 24/24 oracles green
post-inline; 2 wrong-result mutants pinned (exemption-off fails both
oracles; call-site inversion fails the table oracle). Gate: the two
behavioral oracles (the bar forbids new census gates); bypass fails them,
proved. Coupling: none. Freshness: prod `43d8faf2`->`febf63a3`, test
`0f471094`->`7d11d68f`, owner `7e65b2bd` unchanged; HEAD `c37a08a0`;
ITEM_BASELINE `a06c5ef3`.

## Defects

None. Pre-edit baseline 24/24 green: no pre-existing failure.

## Pending execution

None. Sharded/pg cells inapplicable by construction (the command renders
from finalized in-memory metadata; no queryset, alias, or dialect
surface; oracles run default sqlite) for Worker-2's judgment.

## Judgment

The adapter carried no concrete responsibility: private, one production
caller, no boundary name, no isolation, no extension point. Inlined and
deleted; behavior pinned green, failability pinned red.

## Implementation (Worker-1)

Production, 2 hunks: the call site unpacks the 5 attributes beside a
dispatch-order comment and calls the owner; the adapter is deleted. Tests
(companion, same change): `_mirror_check` unpacks and calls the owner;
1 import + 3 prose rewords. Scope note: the binding bar ("show them green
post-inline") entails the companion — without it the mirror gate cannot
reach its predictor; it lands on 100% ledgered lines with zero hunt
overlap, for Worker-2's ruling. Attribution of every WT hunk vs HEAD:
ledgered run-13 FAM-1 (`_strawberry_field_type` + 2 compositions) and
run-15 repair (import swap + adapter body) — mine builds on the adapter
body + the HEAD-clean call-site line only; all `truth.*` hunks
(`@@ -60` import, `handle`, `_resolve_bare_name`, `_print_table`,
`_scalar_row`, `_consumer_authored_row` prose half, `@@ -510,8 +515,8`
f42, `_sdl_type_name`, `_model_name`, `_scalar_name`) are concurrent hunt
work, untouched. Runs: baseline `dry-20261011T060209-d3ad4f` 24/24; ruff
`dry-20261011T060307-9f5d29` clean + `dry-20261011T060314-e3c74c`
unchanged; post `dry-20261011T060319-4743f9` 24/24; prove
`dry-20261011T060345-6b7fbc` 2/2 pinned, restores byte-identical;
basedpyright `dry-20261011T060410-0af60c` 0/0/0. The copy holds the 2
modified files + this artifact; prove manifest at
`docs/dry/temp-tests/relay-adapter-inline/prove.json` (live scratch for
Worker-0's removal).

## What shrinks

Production `inspect_django_type.py`: +10/-24 (net -14). The +10 is the
inlined call: a 3-line dispatch-order comment plus the 7-line owner call
with the 5-attribute unpack. The -24 is 1 replaced call line plus the 23
deleted adapter lines: decorator, signature, 11-line docstring, 2-line
"not recursion" comment, 7-line delegating return, blank separator.
Tests `test_inspect_django_type.py`: +17/-10 (net +7): the oracle's own
unpack + owner call (+7/-1), 1 import, 3 prose rewords keeping the two
docstrings accurate about which symbol the predictor flows through.
Overall: +27/-34 (net -7), 0 new functions, 0 new tests, 0 new gates.

What leaves the tree: the same-name indirection (1 method), its
docstring, and the comment that existed only to disambiguate the
same-name call from recursion. The unpack is spelled twice in production
now (performer call, predictor call) instead of three; the oracle keeps
its independent spelling by design (an oracle that read the owner's
unpack from production would pass whatever it says). The next owner-arity
change touches 2 production unpacks instead of 3, and no reader must
resolve "which `_is_suppressed_relay_pk`" again. No machinery added: the
call site is a plain call expression, the oracle a plain call, and the
owner byte-identical.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

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

## Independent verification (Worker-2)

Own trace (before Findings). Sites: owner
[types-base][types-base]`::_is_suppressed_relay_pk` (definition, pure
5-param verdict); baseline adapter `Command._is_suppressed_relay_pk`
(delegation, unpacked 5 attrs, deleted); predictor
[inspect-cmd][inspect-cmd]`::Command._resolve_row` (consumer, suppressed-first,
now unpacks + calls owner); performer `_build_annotations` (consumer, calls
owner). Oracles: `_mirror_check` + mirror test (predictor-vs-built),
consumer/direct/O2O/MTI table rows + fakeshop `BookType`/`GenreType` rows
(end-to-end via `call_command`). Census: 1 prod caller, 1 oracle caller, 0
other importers; specs cite the owner only. Counts: C1 new exemption → 1
before/after; C2 owner arity → 1 (consumers follow); C3 new suppressed
member → 1. Verdict: inline — the adapter is private, one prod caller, no
boundary name, isolation, or extension point; the "not recursion" comment
proves the same-name indirection is a liability, not a responsibility.

Reconciliation: concur on every row — sites, roles, census, both
challenges, owner choice, migration, and the principle-11 (not count-2)
framing. No differences.

Scope: accept the forced companion. Without it the mirror gate cannot run
(`AttributeError` on the deleted adapter); the bar requires green
post-inline, and the companion lands on 100% ledgered lines, disclosed.
Revision alternative (leave the oracle calling a deleted symbol, delete the
oracle, or keep an alias) either breaks the suite, loses the gate, or
defeats the inline. None is viable.

Oracle: the retargeted mirror still pins agreement and was not rewritten to
pass. It keeps its own unpack spelling, compares against the independent
built record (`origin.__annotations__`), and asserts both sides against
independent expected literals — a divergent edit at either side fails while
a behavior-preserving hand copy still passes (correct: behavioral mirror,
not a census gate, per the bar). The inlined predictor unpack is pinned by
the table oracles via `call_command` (origin by the direct test, consumer
set by the consumer test, field by O2O/MTI, interfaces by fakeshop
`BookType`); the mirror now pins owner-vs-built, transitively closing
predictor-vs-synthesis through the shared owner. Proved: W2 origin→`object`
mutant fails the direct test; W2 relation-check-off fails mirror + O2O +
MTI.

Equivalence (principle 8): pure predicate inline — dispatch order intact
(suppressed before consumer), no new exceptions, no query/transaction,
async, or timing surface; the moved prose is a comment. Re-ran fresh in
`dry/relay-adapter-inline/verify-1`: 24/24 green
(`dry-20261011T061027-2e3540`); prove 2/2 pinned
(`dry-20261011T061116-af4756`), restores byte-identical.

Matrix + cells: all six axes discharged against the real surface (pure sync
verdict, one call site, no twin/pair/sibling; specs cite owner, adapter
cites only in exempt per-cycle scratch). Sharded/pg inapplicable by
construction: the command renders from finalized in-memory metadata with no
queryset, alias, or dialect surface; oracles run default sqlite with no DB
queries. Agree.

Freshness/pending/coupling: prod `43d8faf2`->`febf63a3`, test
`0f471094`->`7d11d68f`, owner `7e65b2bd` unchanged, HEAD `c37a08a0`,
baseline `a06c5ef3`, diff +27/-34 — all re-derived. Pending none (every
proof executed). Coupling none (2 files; queue file-disjoint).

Prose/ruff: diff carries no process provenance, no line-number cites, tests
at the `tests/` tier (command unreachable from GraphQL; throwaway shapes).
`ruff format --check` + `ruff check` clean on both paths. Defects: none
(Worker-2).
