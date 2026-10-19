# DRY review: `django_strawberry_framework/testing/_wrap.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, or is a rejection
carrying its contract difference + trigger. Zero production edits; zero
tracked files changed.

## System trace

Small target (147 lines): the wrap-time half of the Trac #37064
defense-in-depth. It DEFINES one enforcement protocol (decline-or-install on
the live connection slot, [spec-024][spec-024] Decision 8), one consumer-arg
guard (the non-callable `TypeError`, same Decision), and two postures by
omission (no restore — Non-goal 1; no `__all__` — single public name). It
COMPOSES one rule by name (the `_is_database_failure` predicate owned at
[django-patches][django-patches], the verified L2 row). The module + function
docstrings carry the wrap-side contract prose, a worked consumer
`setUp`/`tearDown` shape, and pointers to the unwrap half. No second `def`,
no branch beyond the guard + decline, no `try`/`except`, no `await`, no
settings read, no bus row, no queryset, no transport: the only effects are
the conditional `setattr` and the two documented raises (`TypeError` on a
non-callable wrapper, `AttributeError` propagated from `getattr` on a
missing method — both pinned by oracles).

Connected code read for judgment, outside the item: [django-patches][django-patches]
(full worktree read; judged regions — module-docstring framing,
`_is_database_failure` def + both call sites, the unwrap guard line —
byte-identical at both revisions, dirt characterized below),
[testing-init][testing-init] (full: the re-export consumer row + bullet
projection, CLEAN), [testing-client][testing-client] and
[testing-relay][testing-relay] (full worktree reads + HEAD token greps: zero
wrap tokens at both revisions), [test-wrap][test-wrap] (all 9 oracle bodies
at both revisions — byte-identical, 1 docstring-reflow hunk only), contract
sources [spec-024][spec-024] (Decisions 3/8/9, Non-goal 1, test plan — CLEAN)
and [spec-043][spec-043] Decision 4 (the root-re-export grain — CLEAN),
projections [glossary][glossary] (both entries — CLEAN), CHANGELOG (0.0.7
entries — CLEAN), [tree][tree] (both summary lines identical at both
revisions) and [docs-readme][docs-readme] (grep-0 at both revisions — no
projection there), the sibling `if not callable(` guard sites
([forms-sets][forms-sets], [registry][registry],
[serializer-converter][serializer-converter] — raise lines at both
revisions), [truth][truth]`::static_attr` (the refused live-slot
alternative — untracked concurrent input, judged region pinned by hash),
the installed debug-toolbar `tracking.py` (`wrap_cursor` mirror,
re-verified at installed bytes — external precedent, not a package site),
and the verified [django-patches][django-patches] file artifact (L1/L2/L6 +
F1/F2 scopes as trigger inputs only — every verdict below is re-derived
fresh at current bytes).

Dirt note (judged regions verified identical at both revisions; nothing
touched): the target itself is CLEAN — worktree
`0df97813659bea9ed2002f64e6885896c5cabd6f` equals
`HEAD:django_strawberry_framework/testing/_wrap.py`.
[testing-init][testing-init], [spec-024][spec-024], [spec-043][spec-043],
[glossary][glossary], and CHANGELOG are clean. Hunt-dirtied inputs, each
traced with both fingerprints recorded: [django-patches][django-patches]
(worktree `6918a213…` vs HEAD `ba98f585…`: 7 hunks — `truth` import +
3 call-site retargets + prose-only rewordings — all outside the judged
regions: framing docstring lines 1–114,
`_is_database_failure` body, both predicate call sites, the unwrap guard
line); [test-wrap][test-wrap] (worktree `6818d96b…` vs HEAD `4d3c1351…`:
one docstring reflow in the composition test — all 9 test bodies
byte-identical, oracle census 9 at both revisions); [testing-client][testing-client]
and [testing-relay][testing-relay] (0 wrap tokens at both revisions —
grep-verified, so no wrap site hides in either sibling at either revision);
[tree][tree] (cited `_wrap.py` lines 283/417 identical at HEAD) and
[docs-readme][docs-readme] (grep-0 both revisions); the three sibling-guard
files (dirt is the `truth.*` render/name migration — the per-subject
type/message difference holds at both revisions, regions quoted below).
[truth][truth] and the [django-patches][django-patches] file artifact are
untracked (no HEAD side; worktree hashes recorded). Every count below holds
at both revisions.

Excluded with reason: `one-sync-boundary` (names `testing/client.py`, not
this file — checked, no ORM execution and no boundary call here: C13),
`subsystem-clear-lifecycle` (verified; no bus row here — full read: C13),
`soft-dependency-require-guard` (open; hard deps only here: C13),
`hostile-mapping-hardening` (open; no mapping read in the full read — the
non-interpolating message defends a `__repr__` seam, not a mapping seam:
C13), `upstream-patch-lifecycle` (open; no capture/install/probe/validate/
`apply()` here — this file is not a patch module: C12),
`upstream-patch-refusal-wording` (open; the `RuntimeError`-hint grammar of
patch `apply()` refusals — the decline here returns silent `False` and the
`TypeError` is a spec-pinned consumer-arg guard: C12). The unwrap-half
machinery rows (L1/L3/L4/L5) are different rules at a different lifecycle
site — this file consumes only the L2 predicate (F1, R-A).
[testing-client][testing-client] internals beyond the zero-token sweep and
the debug-toolbar upstream source (external precedent, mirror verified, not
a package site) are excluded on strength of body.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target serves ONE subsystem (consumer
test instrumentation) with ONE public name. Sibling testing modules, each
fully read: [testing-client][testing-client] (556-line worktree read) owns
the HTTP-client family and carries zero wrap tokens at both revisions;
[testing-relay][testing-relay] (full read) owns the GlobalID helpers and
carries zero wrap tokens at both revisions. The only same-pattern
production site is the unwrap half at [django-patches][django-patches]
(different lifecycle site, different object surface — rejected at R-A with
the fresh trigger check, not inherited). The leaf re-export at
[testing-init][testing-init] is a consumer row owned by verified init-F1.
No second wrap site exists anywhere: whole-package grep for
`setattr(connection` finds exactly 4 hits — this file's install (:146),
the unwrap (:360), and 2 upstream-verbatim audited-source constants (not
executed code). The external mirror (`wrap_cursor`) is verified present at
installed bytes, excluded as non-package population.

**2. Sync/async twins.** Inapplicable with reason: the target defines no
colored pair — no `async def`, no `await`, no `sync_to_async` (full
147-line read; grep-0 for all three). The operation (attribute read +
conditional install) is a pure synchronous slot op with no await point to
twin. The check-then-act is non-atomic across threads — cleared as a
near-miss under Defects (no contract source requires atomicity; the
documented use is single-threaded test `setUp`).

**3. Derived rather than repeated knowledge.** Nothing is re-derived: the
recognition predicate is composed by name from its L2 owner (1 def, 2 call
sites — the census, not a second definition); `method_name` passes through
as an opaque slot key and is never re-derived from Django's disallowed-pair
list (name-agnostic by contract — the arbitrary-name oracle pins
`chunked_cursor` so the helper cannot become cursor-specific); no settings
are read (no `conf` import in the full read); no default is computed. The
`TypeError` message literal is the one spelling (spec-pinned, oracle-pinned
by `match=`). The `__test__` collection-guard question ends here with no
surface: the module binds no `Test*`-prefixed name (single public name
`safe_wrap_connection_method`), so no guard is owed (F4).

**4. Inverse / round-trip pairs.** No package-owned inverse half: install
has no package restore — restoration is the consumer's by [spec-024][spec-024]
Non-goal 1 (F3). `True`/`False` are one function's two returns, not two
halves that can drift. The defense-in-depth composition (wrap-decline +
patched teardown) is exercised end-to-end by the composition oracle, which
pins the halves composing — not merging (R-A).

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (the 9-line body); authoritative contract
sources ([spec-024][spec-024] Decision 8 for the protocol + guard +
asymmetry, Decision 9 for the export path, Non-goal 1 for wrap-only);
independent oracles (9 rows in [test-wrap][test-wrap] — each spells its own
literals and drives real connections, never reads the owner body); and
projections (in-target docstrings F5, the [testing-init][testing-init]
bullet, the [django-patches][django-patches] docstring mentions, the two
[glossary][glossary] entries, CHANGELOG, [tree][tree] lines, spec code
blocks, the docstring worked example as consumer-code projection). A
protocol change moves 1 definition here (C1–C3); a retirement moves 0
definitions here (C10 — prose follows).

**6. Enforcement by omission.** The helper is name-agnostic over an open
family (every string is a member), so no member can lack the guard — the
decline check runs on whatever slot is named, and the arbitrary-name oracle
pins a non-`cursor` member. Consumers who never call the helper are covered
by the unwrap backstop — explicitly the contract ([spec-024][spec-024]
Risks: "the wrap-time half is advisory ... which is exactly why the
unwrap-time half exists"), so the non-user path is a covered member, not a
gap. Three examined non-gaps, each cleared for lack of a contract source
(Defects): no runtime `connection`-type check, no `method_name`-type check
(stdlib `TypeError` precedes any mutation), no cross-thread atomicity. No
member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **6 top-level statements**, binding **5 module-level names**
(3 annotation-only imports + the `_is_database_failure` re-binding +
`safe_wrap_connection_method`). Every
member lands below; every challenge in `### Challenges` ends in a
file-local row, a rejection, or a no-surface routing.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (wrap-half framing + toolbar mirror + shared-predicate drift note + backstop pointer) | (none) | prose, F5 (+ R-D) |
| 1 | `from collections.abc import Callable` | annotation-only | F4 |
| 2 | `from typing import Any` | annotation-only | F4 |
| 3 | `from django.db.backends.base.base import BaseDatabaseWrapper` | annotation-only | F4 |
| 4 | `from ..._django_patches import _is_database_failure` | predicate re-binding | F1 (consumer row of verified L2; no index edit owed) |
| 5 | `def safe_wrap_connection_method(...)` (body :139–147 + full docstring) | 1 public name | body → F1 + F2; omission → F3; docstring → F5; no `__all__` → F4 |

Rules: R1 wrap-decline protocol (guard→read→check→install order,
decline-False-untouched, name-agnostic install-True); R2 non-callable
`TypeError` guard (callable check + non-interpolating message, first);
R3 wrap-only restoration posture (no restore — the omission + the worked
example as consumer projection); R4 module mechanics (single public name,
no `__all__`, annotation-only imports, no `Test*` guard question); R5
contract prose (both docstrings as the wrap-side statement). No indexed
family is adopted (see Excluded with reason above); three convergences are
recorded as nested rejections (R-A → L1/L2 halves direction, R-B →
per-subject-rejection-grammars, R-D → hints-R4 bilateral prose); one fresh
rejection (R-C); no new family is named. Nine index rows are named for
Worker 0 (5 file-local + 4 rejected).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. All bodies judged identically at HEAD and worktree bytes
(see Dirt note: every dirt hunk sits outside every judged region,
grep-verified per input).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 recognition source | Django renames `_DatabaseFailure` | **1** (the L2 predicate; both halves follow by name — wrap degrades per Decision 8, unwrap aborts per Decision 4; the symbol-missing oracles on both suites pin the arms) | independent — consumer by name |
| C2 | R1 decline posture | decline raises instead of returning `False` | **1** (here; the unwrap half is untouched — it skips foreign replacements regardless of how the wrap half declines) | independent |
| C3 | R1 operation set | add a read-only slot probe (e.g. `is_wrapped`) | **1** new def here; **0** new recognition defs (the predicate is reused by name) | independent |
| C4 | R2 message | reword the `TypeError` text | **1** (here; the two `match=` oracles follow as oracles) | independent |
| C5 | R2 accepted set | reject callables that are classes | **1** (here; the accepts-instance oracle flips as oracle) | independent |
| C6 | R2 interpolation | interpolate `wrapper` into the message | **1** (here; the hostile-repr oracle must flip — and the flip reintroduces exactly the Decision-8-pinned failure) | independent |
| C7 | R3 restore support | the helper gains restoration | **1** (here; Non-goal 1 retires; the worked example becomes the implementation sketch) | independent — the omission lives here |
| C8 | R3 example shape | rewrite the worked `setUp`/`tearDown` | **0** defs (projection edit inside this docstring only) | no definition — consumer projection |
| C9 | R4 membership | add a second public name | **1** (here: def + docstring; the leaf import line + `__all__` entry follow as consumer rows per verified init-F1) | independent |
| C10 | R5 retirement | Django fixes Trac #37064 | **0** defs here (prose follows; the retirement moves L6 prose + the unpatched-crash detector + oracles; the shared-form question is settled by R-D) | no definition here — prose follows |
| C11 | R5 example tokens | Django renames `chunked_cursor` | **0** defs (prose token follows; the name-agnostic body is untouched — proves the prose/body split) | no definition here — prose follows |
| C12 | lifecycle/refusal-wording checks | change the patch lifecycle or a refusal wording | **0** here (no `apply`/capture/install/probe/validate in the full read; the decline returns silent `False`, never a `RuntimeError`-hint wording) | no surface — do not inherit |
| C13 | boundary/clear/guard/mapping checks | change the one-boundary rule, the clear bus, a soft-dep guard, a hostile-mapping read | **0** here (no ORM execution, no bus row, hard deps only, no mapping read in the full read) | no surface — do not inherit |
| C14 | truth-reader routing | read/install the slot through `truth.*` | **0**-as-consolidation (rejected R-C: different contract — the missing-method oracle pins `getattr`'s `AttributeError`) | rejected — behavior differs |
| C15 | shared callable-guard driver | one driver for every `if not callable(` site | **1** per side (rejected R-B: per-subject types + messages + reasons to change) | rejected — 13 subjects, not 1 rule |
| C16 | halves merge | one body for wrap-decline + patched teardown | **1** per side (rejected R-A: different lifecycle site, surface, caller, timing, failure posture) | rejected — 2 rules, 1 shared predicate |

No executable proof was run beyond one read-only `uv run python -c`
(import Django, print version, import `_DatabaseFailure` — non-mutating;
installed Django 6.1, symbol importable as a `type`) plus read-only greps
and `git show` reads. Every behavior this file owns is pinned by the 9
permanent oracles (bodies read at both revisions, byte-identical), which
the cycle gate runs; a file item owes no equivalence proof for edits it
does not make. Every other claim below is `static-reviewed`. No workspace
runs (nothing source-mutating was needed), no `docs/dry/temp-tests/`
scratch was created, no shared-tree pytest run — inspection + the oracles
settle every judgment.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — wrap-decline protocol (file-local)

- **Contract + variation.** Install-or-decline on the live slot, in fixed
order: non-callable guard first (F2), read `current` via `getattr`
(`AttributeError` propagates on a missing method — pinned), decline
(`return False`, slot untouched) iff the L2 predicate holds, else
`setattr`-install and `return True`. Name-agnostic: `method_name` is an
opaque slot key, never validated against Django's pair list. Contract
source: [spec-024][spec-024] Decision 8 paragraph 1. Legitimate variation:
recognition source (the predicate), decline posture (`False` + untouched),
operation set (this op only).
- **Sites + roles.** *Definition*: this file's body (:139–147 — the only
wrap installer in the package: the `setattr(connection` census is exactly
4 hits, of which only :146 installs a consumer wrapper). *Owner composed
by name*: the L2 predicate (1 def at [django-patches][django-patches]:281,
2 call sites — here :144 and the unwrap :359). *Enforcement sites*: none
in production — zero package call sites (package grep hits are the def,
docstrings, the re-export, and the message literal); callers are the 9
[test-wrap][test-wrap] oracles + the docstring worked example.
*Oracles*: install/decline/symbol-missing/arbitrary-name/composition rows
(independent: each spells its own literals, drives real connections,
never reads the owner). *Projections*: F5 docstrings, the
[testing-init][testing-init] bullet, the [django-patches][django-patches]
mentions, [glossary][glossary], CHANGELOG, [tree][tree], spec blocks.
- **Challenges.** C1 → 1 (the predicate; both halves follow) — the proof
no second recognition definition exists; C2 → 1 (here); C3 → 1 new def
here + 0 new recognition defs. C16's merge direction is rejected at R-A.
- **Owner + lifetime.** This function (existing narrowest site by
responsibility: the consumer-callable wrap boundary; the unwrap loop
cannot serve consumers and the leaf cannot carry behavior). No stored
derivation — a pure slot op, so no lifetime fields are owed. Import-time
predicate binding is the healthy compose-by-name shape: the drift point is
the *symbol* (read from the patch module's globals at predicate-call
time), not the predicate object, and the symbol-missing oracle proves the
drift path flows through this binding.
- **Migration.** None (zero-edit item): single installer stands; the
predicate stays single-sourced at L2.
- **Distinct behavior.** The unwrap half (R-A), the guard order + message
(F2), the absent restore (F3). The declined call mutates nothing (code
order: `return False` precedes any `setattr` — plus the oracle's
`connection.cursor is django_wrapper` identity assert). The module
docstring's "shared predicate so a future move degrades the helper
instead of crashing the public import" holds verbatim: this module never
imports `_DatabaseFailure` (census: its 7 mentions here are docstring
prose only) and the predicate import is symbol-safe by the patch module's
`try`/`except`.
- **Behavioral proof.** `static-reviewed` (full body read + all 9 oracle
bodies read at both revisions — byte-identical). Rejects "a second
installer exists" (the 4-hit `setattr` census), "the decline mutates"
(code order + identity oracles), "the helper re-derives Django's pair
list" (no such read in the full read + the arbitrary-name oracle).
- **Structural gate.** Gate-only justification, no new gate: single
definition; the recorded `setattr(connection` population (1 here + 1
unwrap + 2 upstream-verbatim constants) is the sweep that would surface a
second installer — a bespoke existence test per helper would violate the
gate-only economy (principle 9).
- **Coupling.** F2 (the guard precedes every read), F3 (no restore half),
L2 (the composed predicate), R-A + R-C (the two refused reshapes).
- **Freshness.** Target `0df97813659bea9ed2002f64e6885896c5cabd6f` (CLEAN),
[django-patches][django-patches] HEAD `ba98f585…` / worktree `6918a213…`
(dirt outside the predicate def, both call sites, and the guard line —
byte-verified), [test-wrap][test-wrap] HEAD `4d3c1351…` / worktree
`6818d96b…` (9/9 bodies identical), [spec-024][spec-024] `46335d7e…`
(clean; Decision 8), installed `tracking.py`
`046b254a52f7849f4edf8178a6b860b9d0c66e0f` (`wrap_cursor` :59,
`isinstance` check :68 — mirror verified, excluded as external),
installed Django 6.1 with `_DatabaseFailure` importable (read-only probe).
Searched populations: `setattr(connection` → 4 hits (above);
`_is_database_failure` → 1 def + 2 call sites; `safe_wrap…` in production
→ def + re-export + prose, zero call sites; wrap tokens in
[testing-client][testing-client]/[testing-relay][testing-relay] → 0 at
both revisions. Excluded on strength of body: the unwrap loop (R-A), the
toolbar mirror (external), sibling `callable` guards (R-B subjects).
- **Rejection (nested R-A).** Considered: one body for wrap-decline +
patched teardown (both center an `_is_database_failure` check).
Contract difference here: wrap is install-time, consumer-callable, on a
connection-instance attribute, returning `bool`, raising `TypeError` /
`AttributeError`, running at `setUp`; unwrap is teardown-time,
Django-invoked, inside the `SimpleTestCase` pair-list loop, returning
`None`, raising nothing, running at `tearDownClass`. Different inputs,
outputs, errors, timing, callers, and failure posture (decline-`False`
vs skip-silently) — C2/C16 prove opposite move sets (a decline-posture
change moves here alone; a loop-shape change moves there alone). The
shared part — recognition — is already one definition at L2; what
remains at each site is its own lifecycle behavior, not a second copy.
CONVERGE with verified [django-patches][django-patches] L1/L2 on fresh
evidence (this item's own censuses, order analysis, and C2/C16 — L2's
"halves still separate lifecycle sites" trigger re-checked at current
bytes: yes). Trigger to reconsider: a single lifecycle site owning both
(the package-owned wrapper + owner sentinel [spec-024][spec-024] names
from the cache-panel precedent) would make them one rule. Durable home:
[spec-024][spec-024] Decisions 3/8 + both module docstrings (already
state the split). Named for Worker 0 as rejected index row
`testing-wrap-vs-unwrap-halves` (no such row exists in the current plan).
- **Rejection (nested R-C).** Considered: reading/installing the slot
through [truth][truth] readers instead of `getattr`/`setattr`. Contract
difference here: the helper's contract IS the live slot — what
`connection.<method>` resolves to through normal lookup, the same
resolution Django's add-side and every consumer mutates through. That is
a different question from what truth readers answer (stored value with
live lookup bypassed): concretely, a missing method raises
`AttributeError` today (pinned oracle), while a default-returning static
read would yield `None` → predicate `False` → *install*, silently
creating an attribute the connection never had. Different errors,
different state effects — C14 forces 0-as-consolidation. The install
half has no reader counterpart at all: raw `setattr` is the specified
mechanism ("calls the helper instead of raw `setattr`"). Fresh
rejection, no prior verdict. Trigger to reconsider: a truth write
protocol plus a spec row redefining the missing-method contract would
reopen the read half. Durable home: [spec-024][spec-024] Decision 8 +
the missing-method oracle. Named for Worker 0 as rejected index row
`testing-wrap-slot-read-vs-truth-readers` (no such row exists in the
current plan).

### F2 — non-callable `TypeError` guard (file-local)

- **Contract + variation.** `callable(wrapper)` else `TypeError` naming
the function and the condition, never interpolating `wrapper` (a hostile
or broken consumer `__repr__` must not replace the intended error).
First statement — precedes any slot read or install (both
`__dict__`-intact oracles pin zero mutation). Accepts every callable
including class instances (oracle). Contract source: [spec-024][spec-024]
Decision 8 paragraph 1 (message rule + hostile-repr reason). Legitimate
variation: message text, accepted-callable set, interpolation (never).
- **Sites + roles.** *Definition*: this file's :139–142 (the one
`raise` in the module — full-read verified). *Oracles*: the
raises/hostile-repr/accepts-instance rows (independent: the first two
spell `match="non-callable wrapper"` and drive `42` + a hostile repr;
never read the owner). *Projections*: the `Raises:` docstring block (F5),
the spec Error-shapes row.
- **Challenges.** C4/C5/C6 → 1 each (here; oracles follow as oracles —
C6's flip would reintroduce the pinned failure, which is why the
hostile-repr row exists). C15's shared-driver direction is rejected at
R-B.
- **Owner + lifetime.** This function (existing narrowest site: the guard
validates this function's own argument at its own entry; verified L2
"Distinct behavior" explicitly leaves it here for this item to
enumerate). No stored derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single guard stands.
- **Distinct behavior.** Message rule (name function + condition, no
interpolation) vs the guard predicate (`callable()`) — both live in the
same 4 lines and move together (C4/C5/C6 each force the same 1
definition), so they are one rule, not two.
- **Behavioral proof.** `static-reviewed` (guard body + all three oracle
bodies read at both revisions — byte-identical). Rejects "the message
interpolates" (literal body + the hostile-repr oracle, which fails any
interpolating spelling by raising `RuntimeError` instead of the pinned
`TypeError`) and "the guard is shared" (R-B: 13 sites, per-subject).
- **Structural gate.** The two `match=` + `__dict__`-intact oracles ARE
the gate (pre-existing, run at the cycle gate — not newly built for this
finding). Negative control shape (named, not executed — a zero-edit file
item owes no source-mutating run to re-prove a permanent oracle): an
interpolating message raises the hostile `RuntimeError` instead of
`TypeError`, failing both rows; a guard placed after the slot read fails
the intact asserts. Deductively airtight; execution would mutate without
distinguishing anything further.
- **Coupling.** F1 (order: guard precedes read), R-B (the refused driver).
- **Freshness.** Target `0df97813…`, [test-wrap][test-wrap] HEAD
`4d3c1351…` / worktree `6818d96b…` (guard-row bodies identical),
[spec-024][spec-024] `46335d7e…` (Decision 8 message rule),
[forms-sets][forms-sets] HEAD `36ce80b4…` / worktree `2642a647…`,
[registry][registry] HEAD `81bd561c…` / worktree `492654d2…`,
[serializer-converter][serializer-converter] HEAD `6652d092…` / worktree
`96d2b56a…` (dirt is the `truth.*` render/name migration — per-subject
difference quoted at both revisions below). Searched population: `if not
callable(` → 13 package sites (this one + 12 siblings; three witnessed
below, all per-subject by the same construction).
- **Rejection (nested R-B).** Considered: one shared callable-guard
driver for every `if not callable(` site. Contract difference here: each
site guards its own subject with its own type + message + interpolation
rule — this one raises spec-pinned non-interpolating `TypeError`
("…received a non-callable wrapper"); [forms-sets][forms-sets] raises
interpolating `ConfigurationError` naming `get_form_fields` (HEAD
`mutation_cls.__name__`, worktree `truth.name(...)` — same subject both
revisions); [registry][registry] raises a differently-worded `TypeError`
naming `register_subsystem_clear` (identical both revisions);
[serializer-converter][serializer-converter] raises interpolating
`ConfigurationError` naming the converter contract (same subject both
revisions). A shared form would own `if not callable(x)` + `raise` — two
lines — while every remainder kept its type, message, subject, and
reason to change; C4/C15 prove opposite move sets (rewording here moves
spec-024-pinned text alone). Same predicate spelling, not the same rule.
CONVERGE with verified per-subject-rejection-grammars (utils/policies
R3) on fresh evidence (trigger re-checked at current bytes: no shared
guard protocol has appeared — every site still raises its own subject's
type/message). Trigger to reconsider: a package-wide guard protocol (one
type + message rule for all seams) would make them one rule. Durable
home: [spec-024][spec-024] Decision 8 (pins this message). Named for
Worker 0 as rejected index row
`testing-wrap-guard-vs-shared-callable-guards` (no such row exists in
the current plan).

### F3 — wrap-only restoration posture (file-local)

- **Contract + variation.** The wrap step only; restoration is the
consumer's — no restore parameter, no restore branch, no restore return
(full-read verified omission). The docstring carries the worked
`setUp`/`tearDown` shape (:85–109) as consumer-code projection, plus the
pointer that the unwrap backstop makes omitting the restoration
non-fatal. Contract source: [spec-024][spec-024] Non-goal 1 ("handles the
wrap step only") + Decision 8 restoration paragraph. Legitimate
variation: the omission holds or it is lifted — a one-decision binary.
- **Sites + roles.** *Definition (by omission)*: this function's
signature + body (the one place that decides the helper's steps).
*Contract sources*: Non-goal 1 + the Decision 8 paragraph. *Projection*:
the worked example (consumer-shaped: it calls the helper by name —
composition, not a second implementation). *Oracle*: the composition row
(proves omission non-fatal end-to-end: decline, then patched teardown
restores the original with no consumer restore step).
- **Challenges.** C7 → 1 here (the omission lives in this signature);
C8 → 0 defs (rewriting the example edits a projection only).
- **Owner + lifetime.** This function (existing narrowest site: the
omission lives in this signature; verified L2 "Distinct behavior"
explicitly leaves restoration semantics here for this item to
enumerate). No stored derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): the omission stands; lifting it
would be one edit here plus the Non-goal-1 retirement.
- **Distinct behavior.** The example restores whatever `setUp` found —
correct whether or not Django wrapped the slot (if the class disallows
the connection, the saved "original" IS Django's wrapper and restoring
it restores Django's wrapper; if allowed, the bound method). Read line
by line, not assumed.
- **Behavioral proof.** `static-reviewed` (signature + body + example
read at both revisions — target CLEAN so one revision). Rejects "the
example is a second wrap implementation" (it calls the helper by name)
and "omission strands consumers" (the composition oracle + the
backstop pointer).
- **Structural gate.** None owed (absence with a contract source; the
composition oracle pins the non-fatality the omission relies on).
- **Coupling.** F1 (the step that exists), F5 (the example lives in the
docstring).
- **Freshness.** Target `0df97813…` (CLEAN), [spec-024][spec-024]
`46335d7e…` (Non-goal 1 + Decision 8), [test-wrap][test-wrap] HEAD
`4d3c1351…` / worktree `6818d96b…` (composition body identical).
Excluded on strength of body: the unwrap loop (the backstop the pointer
names — different rule, R-A).

### F4 — module mechanics (file-local)

- **Contract + variation.** One public name, no `__all__` (full-read
verified — the module binds `safe_wrap_connection_method` only);
`Callable`/`Any`/`BaseDatabaseWrapper` imported for annotations only
(signature use, no runtime reference); the predicate import (member 4)
is a by-name consumer row of verified L2 (principle 6). The single name
flows to the leaf re-export ([testing-init][testing-init]:46 + `__all__`
entry — verified init-F1's consumer rows). Varies only with membership
(C9).
- **Sites + roles.** *Definitions*: member 5 (the name), members 1–3
(the annotation imports), the absent `__all__` (posture by omission).
*Consumer rows*: the leaf import + list entry (init-F1 owns that rule).
*Contract sources*: [spec-024][spec-024] Decision 9 (submodule export
path, never the root) + [spec-043][spec-043] Decision 4
(root-re-exported because it predates that card). *Oracle*: the
[test-wrap][test-wrap] import block (`from ...testing import
safe_wrap_connection_method` — resolves through the leaf).
- **Challenges.** C9 → 1 (here; leaf rows follow). C12/C13 → 0 (no
patch lifecycle, no refusal wording, no boundary call, no bus row, no
guard call, no mapping read — the full read is the evidence).
- **Owner + lifetime.** This module (the posture lives in this file's
binding set; no narrower owner exists). No stored derivation; no
lifetime fields owed.
- **Migration.** None (zero-edit item): the posture stands; a second
name would add its def plus leaf consumer rows.
- **Distinct behavior.** No `__all__` is correct for a single-public-name
module: the leaf's explicit import is the enforcement of what flows
upward, so a manifest here would list one name to no effect. No
`Test*`-prefixed name exists, so the `__test__` collection-guard
question (cf. init-C15) ends here with no surface — nothing to guard.
- **Behavioral proof.** `static-reviewed` (AST census: 6 members, every
binding classified). Rejects "a second public name hides here"
(full-read + census) and "the leaf leaks an unlisted name" (the leaf
imports exactly this one name — verified init-F1).
- **Structural gate.** None owed (import census; the leaf's explicit
import fails loudly on any drift).
- **Coupling.** Init-F1 (the leaf-side consumer rule), F1 (the member-4
consumer row of L2).
- **Freshness.** Target `0df97813…` (CLEAN),
[testing-init][testing-init] `48b45d1b…` (clean; import + list entry),
[spec-024][spec-024] `46335d7e…` (Decision 9),
[spec-043][spec-043] `a31a06f1…` (clean; Decision 4 passage),
[test-wrap][test-wrap] `4d3c1351…`/`6818d96b…` (import block identical).

### F5 — contract prose (file-local)

- **Contract + variation.** Both docstrings as the wrap-side statement:
the module docstring (wrap-half framing, toolbar mirror, shared-predicate
drift note, backstop pointer) and the function docstring (contract, why,
worked example, Args/Returns/Raises). Bounded: it states the wrap-side
contract + pointers and carries no audit mechanics — no audited-source
set, no capture/install/probe lifecycle, no validation tiers
(full-read verified). Varies only with the wrap contract it states.
- **Sites + roles.** *Prose definition*: this file's docstrings (members
0 + 5-docstring). *Oracles*: none read it (the 9 rows drive behavior,
never prose — independence holds by construction). *Downstream
projections*: the [testing-init][testing-init] bullet (init-F3 owns that
rule), the two [glossary][glossary] entries, CHANGELOG, the [tree][tree]
summary lines ×2 (generated render of the first line), spec code blocks.
No [docs-readme][docs-readme] projection (grep-0 both revisions).
- **Challenges.** C10 → 0 defs here (retirement prose follows); C11 → 0
defs (example tokens follow while the name-agnostic body stands — the
proof prose and body are split).
- **Owner + lifetime.** This module (the wrap-side statement lives with
the wrap-side code; dies with the module at retirement). No stored
derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): prose stands, pointers stand.
- **Distinct behavior.** Every checkable claim verified sentence-against-body
this pass: decline semantics at :144–145, the guard at :139–142, the
example's import path (resolves via the leaf — verified init-F1), the
shared-predicate drift note (F1 census), the "both ends / unwrap end"
pair (composition oracle), the toolbar mirror (code verified at
installed `tracking.py` blob `046b254a…` :59/:68 — the GitHub + Trac
URLs are citations, not behavior). The L6 file-local framing row's
trigger ("a second framing owner") was checked fresh: this prose
restates no framing mechanics — trigger unfired, that row stands
untouched.
- **Behavioral proof.** `static-reviewed`. Rejects "the prose duplicates
the rules" (C10/C11 prove every mechanics change moves zero
definitions here — prose follows, nothing is maintained twice).
- **Structural gate.** Gate-only justification, no new gate: prose drift
between a contract statement and its body is caught by reading, not by
a mechanical oracle — every claim above was verified against its body
in this pass. A bespoke prose-equality test would violate the gate-only
economy (principle 9).
- **Coupling.** R-D (the refused single-sourcing with L6).
- **Freshness.** Target `0df97813…` (CLEAN),
[django-patches][django-patches] HEAD `ba98f585…` / worktree `6918a213…`
(framing docstring lines 1–114 byte-identical — the L6 side of R-D),
[glossary][glossary] `3413edc3…` (clean; 8 hits both revisions),
[tree][tree] HEAD `5d562733…` / worktree `769c2743…` (both `_wrap.py`
lines 283/417 identical), CHANGELOG `d4e10355…` (clean; 0.0.7 entries),
[docs-readme][docs-readme] HEAD `1497164f…` / worktree `30978c34…`
(grep-0 both revisions), [spec-024][spec-024] `46335d7e…` (Decision 8 +
code blocks). Excluded on strength of body: L6's audit record (the
other side of R-D) and the toolbar upstream source (external).
- **Rejection (nested R-D).** Considered: single-sourcing the
Trac-plus-toolbar-plus-two-halves framing in one docstring (this prose
vs the L6 record). Contract difference here: this prose states the
wrap-side consumer contract (what the helper does + why + how to use
it, for readers deciding whether to call it); L6 states the
package-internal audit record (audited set, sentinel analysis,
surface-visibility, for readers maintaining the backstop). Different
audiences, opposite move sets — posit a wrap-side guard addition:
this docstring moves with it while L6 is untouched; posit a third
audited body: L6 moves while this prose is untouched. Same rationale
sentences, not the same rule.
CONVERGE with verified hints-R4 bilateral-import-rationale-prose (+
testing-leaf F2-nested) on fresh evidence (trigger re-checked: neither
passage carries the other's mechanics — this prose names no audited
set/capture/probe/tiers, L6 names no wrap signature/guard/example).
Trigger to reconsider: either passage starts restating the other's
mechanics instead of pointing → shrink that passage to a pointer (a
projection consolidation, never a definition change). Durable home:
[spec-024][spec-024] Decision 8 (already states the split) + both
docstrings. Named for Worker 0 as rejected index row
`testing-wrap-framing-vs-patch-framing` (no such row exists in the
current plan).

## Defects

None. Every docstring claim checked held: the decline/install/ordering
semantics (verified against the body + the 9 oracles), the guard message
rule (literal body + `match=` rows), the shared-predicate drift note
(import census + symbol-missing oracle), the worked example (restores
whatever `setUp` found — correct in both Django states), the
both-ends/unwrap-end pair (composition oracle), and the toolbar mirror
(installed `tracking.py` :59/:68). The axis-6 sweep finds no missing
guard: the name-agnostic family cannot lack one, non-users are covered
by the backstop contract, and every examined non-gap below breaks no
contract row. Four near-misses examined and cleared (each checked
against its contract source, not assumed):

- Oracle census 9 vs [spec-024][spec-024]'s "7": the suite grew two rows
since the spec archived (`accepts_callable_class_instance`,
`raises_attribute_error_on_missing_method` — both present at HEAD too).
Both pin behavior consistent with the documented contract (Args types
`wrapper: Callable`, `getattr` propagation); the spec count is archived
prose, and archived specs are not revised. Stale count, not a behavior
defect — no contract row breaks.
- No runtime `connection`-type check: [spec-024][spec-024] Decision 8
types the parameter (`BaseDatabaseWrapper`) and specifies no check and
no error shape for a mistyped connection; no oracle pins one. The
annotation is the contract; runtime behavior is duck-typed by
construction. No contract source requires more — not a defect.
- Non-`str` `method_name`: outside the typed contract, and `getattr`
raises stdlib `TypeError` before any state access — failure precedes
mutation by construction. No contract row requires a friendlier error —
not a defect.
- Non-atomic check-then-act across threads: no contract source requires
atomicity, and the documented use is single-threaded test `setUp`.
Not a defect.

## Pending execution

None. No `execution-deferred` proof: the target's behaviors are pinned
by the 9 permanent oracles (bodies read at both revisions,
byte-identical) which the cycle gate runs, and every other conclusion
rests on full reads + censuses re-derived at current bytes. No workspace
run was owed (nothing source-mutating was needed) and none was made.
Sharded / Postgres cells are inapplicable by construction: the target
reaches no database, alias, or dialect decision — it operates on a
passed-in connection object ([test-wrap][test-wrap]'s own docstring
states the suite needs no sharded mode).

## Judgment

Zero-edit file item. Five rules traced: five file-local with proving
challenges (F1 protocol, C1–C3; F2 guard, C4–C6; F3 wrap-only, C7–C8;
F4 mechanics, C9; F5 prose, C10–C11), four rejections with contract
differences + triggers (R-A halves merge in F1, R-C truth readers in
F1, R-B shared guard driver in F2, R-D framing single-source in F5).
Three lawful convergences transcribed as nested rejections (R-A → L1/L2,
R-B → per-subject-rejection-grammars, R-D → hints-R4), each re-derived
fresh with its trigger re-checked unfired. Six indexed families checked
with no surface (C12–C13). Enumeration covers 6/6 statements and 5/5
bound names (3 annotation-only + 2 runtime). No defects, no pending
execution, no production edits.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs
`ITEM_BASELINE=3b352404a2d3629180c4d70757c4e3820bcfcd45`:
`git diff <baseline> -- django_strawberry_framework/testing/_wrap.py` is
empty, and `git diff <baseline> HEAD -- <target>` is empty too — the
target [testing-wrap][testing-wrap] is CLEAN at
`0df97813659bea9ed2002f64e6885896c5cabd6f` (worktree == HEAD at
`0c0537e2`), so no hunk attribution was owed and the item never stopped.
The artifact itself is a new untracked file at the exact dispatched path
`docs/dry/dry-file-testing___wrap.md`, the item's only output. The
`## Owned changes` ledger gains no row from this item. Concurrent dirt
(hunt edits across `django_strawberry_framework/`, `tests/testing/*`,
`docs/README.md`, `docs/TREE.md`, `docs/dry/dry-0_0_15.md`) left
untouched. No `uv run ruff` run (no `.py` touched; `.md` is outside ruff
format scope; no `.py` scratch created). No shared-tree pytest run
(inspection + the read-only import probe + the 9 permanent oracles
suffice — see `### Challenges` note; a run could settle nothing further).
No workspace runs (nothing source-mutating was needed). No
`docs/dry/temp-tests/` scratch created. No commit.

Worker-0 instructions: (a) tick the plan item `File testing/_wrap.py`
as verified under Run `0.0.15 2026-09-28-7` once Worker 2 agrees; (b) add
the nine `## Responsibility index` rows under `## Index rows for Worker-0`
verbatim (holding item `File testing/_wrap.py`); (c) add the
`## Families` items under `## Families` (none). No commit.

## Index rows for Worker-0

| `testing-wrap-decline-protocol` | `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` (guard→read→check→install; predicate composed by name from verified L2) | `django_strawberry_framework/testing/_wrap.py` | File `testing/_wrap.py` | file-local |
| `testing-wrap-noncallable-guard` | `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` (callable check + non-interpolating `TypeError`, first) | `django_strawberry_framework/testing/_wrap.py` | File `testing/_wrap.py` | file-local |
| `testing-wrap-only-no-restore` | `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` (wrap step only, by omission per spec-024 Non-goal 1; worked example is consumer projection) | `django_strawberry_framework/testing/_wrap.py` | File `testing/_wrap.py` | file-local |
| `testing-wrap-module-mechanics` | `django_strawberry_framework/testing/_wrap.py` (single public name, no `__all__`, annotation-only imports) | `django_strawberry_framework/testing/_wrap.py` | File `testing/_wrap.py` | file-local |
| `testing-wrap-contract-prose` | `django_strawberry_framework/testing/_wrap.py` (module + function docstrings as the wrap-side statement) | `django_strawberry_framework/testing/_wrap.py` | File `testing/_wrap.py` | file-local |
| `testing-wrap-vs-unwrap-halves` | `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` (rejection recorded here; CONVERGE with verified _django_patches L1/L2 on fresh evidence; durable home spec-024 Decisions 3/8 + both docstrings) | `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/_django_patches.py` | File `testing/_wrap.py` | rejected |
| `testing-wrap-guard-vs-shared-callable-guards` | `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence; durable home spec-024 Decision 8) | `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/registry.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | File `testing/_wrap.py` | rejected |
| `testing-wrap-slot-read-vs-truth-readers` | `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` (rejection recorded here; fresh pair, no prior verdict; durable home spec-024 Decision 8 + the missing-method oracle) | `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/utils/truth.py` | File `testing/_wrap.py` | rejected |
| `testing-wrap-framing-vs-patch-framing` | `django_strawberry_framework/testing/_wrap.py` (rejection recorded here; CONVERGE with verified hints-R4 bilateral prose on fresh evidence; durable home spec-024 Decision 8 + both docstrings) | `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/_django_patches.py` | File `testing/_wrap.py` | rejected |

## Families

None. No new family named, no adoption into an open family (all six
considered families checked with no surface at this file, C12–C13; the
composed predicate stays owned by verified L2 with this file as its
by-name consumer — no index edit owed). No holding family is routed to:
every enumerated member is homed above.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-024]: ../SPECS/spec-024-django_trac_37064_hardening-0_0_7.md
[spec-043]: ../SPECS/spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[django-patches]: ../../django_strawberry_framework/_django_patches.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[testing-wrap]: ../../django_strawberry_framework/testing/_wrap.py
[truth]: ../../django_strawberry_framework/utils/truth.py

<!-- tests/ -->
[test-wrap]: ../../tests/testing/test_wrap.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Read order (honest record): AGENTS.md, DRY.md, worker-2.md, the plan
item + `## Run 0.0.15 2026-09-28-7`, the full target, the window diff,
then site greps + fingerprint sweeps of my own. One deviation: I
peeked at the artifact's header + `## System trace` (first 60 lines)
before running my site sweep, but every number below was re-derived
via independent commands (`ast.parse`, `git hash-object` /
`git rev-parse HEAD:`, `git show HEAD:`, `git grep HEAD`, worktree
greps) — never copied. `## Findings` was opened only after the trace
below was fixed.

### My trace (pre-findings)

Target `django_strawberry_framework/testing/_wrap.py`: 147 lines,
6 `ast.Module.body` statements (module docstring + 4 `ImportFrom` +
1 `FunctionDef`), binding 5 names (`Callable`, `Any`,
`BaseDatabaseWrapper`, `_is_database_failure`,
`safe_wrap_connection_method`). Body: guard → `getattr` → predicate
check → `setattr` → `bool`; no `try`, no `await`, no settings read.

Sites + roles (mine): the function body DEFINES the decline-or-install
protocol + the non-callable guard + the `AttributeError`-propagation and
no-restore postures; the `_is_database_failure` import/call is a
CONSUMER of the L2 predicate owned at
`django_strawberry_framework/_django_patches.py`; the leaf re-export is
a consumer row + bullet projection; `tests/testing/test_wrap.py` (9
`def test` rows) are ORACLES; spec-024 Decisions 3/8/9 + Non-goal 1 are
contract sources; glossary/CHANGELOG/TREE/docstrings are PROJECTIONS;
debug-toolbar `tracking.py` is external precedent, not package
population.

Definition counts per posited change (mine): decline→raise 1 (here);
guard/message/interpolation 1 each (here); Django symbol move 1 (at
L2, here unchanged — consumer); restore addition 0 existing (Non-goal);
method-name validation 1 (here, currently omission). Homes (mine):
protocol/guard/AttributeError-posture/no-restore/no-`__all__` →
file-local; predicate → converge onto verified L2 (no index edit);
sibling callable-guards, wrap/unwrap-merge, truth-readers, framing
single-source → rejections with triggers.

Matrix (mine): axis 1 searched (sibling connection-wrap tokens 0/0
both revisions; `setattr(connection` census exactly 4); axis 2
inapplicable (no `async def`/`await`/`sync_to_async` in the full read);
axis 3 searched (predicate by name, opaque slot key, no settings, one
message spelling); axis 4 searched (wrap/unwrap = two rules sharing one
predicate; restore absent per Decision 8); axis 5 searched (spec +
9 oracles + projections classified); axis 6 searched (callable-guard
family enumerated, each own contract; non-users covered by the
backstop per spec Risks).

### Reconciliation (zero differences)

- Enumeration: AGREE — 6/6 statements + 5/5 names member-by-member;
  my AST census is identical (docstring + 4 imports + 1 def).
- Matrix: AGREE all 6 axes — axis-1 censuses re-derived
  (`setattr(connection` exactly 4: install :146, unwrap :360, 2
  upstream-verbatim constants; `_is_database_failure` 1 def + 2 call
  sites; zero package call sites); axis-2 inapplicability judged on
  its reason (pure sync slot op); axes 3–6 each searched, not sampled.
- Challenges C1–C16: AGREE every count — C1 1 at L2 (degrade/abort
  asymmetry verified in the predicate body + both suites' oracles);
  C2/C4/C5/C6 1 here; C3 1 new + 0 recognition; C7 1 here; C8/C10/C11
  0; C9 1 here; C12/C13 0 no-surface (no `apply`/capture/probe/
  validate/`RuntimeError`, no ORM/bus/mapping tokens — the "install"
  hits are the helper's own contract prose, note N6); C14/C15/C16
  rejected (below). C15 census note N3: strict `if not callable(`
  is 13 at worktree, 12 at HEAD (delta = untracked `truth.py`);
  the rejection is unaffected.
- Convergences (3, all on fresh evidence): AGREE. R-A → L1/L2:
  halves still separate lifecycle sites at current bytes
  (consumer-callable `bool` at setUp vs Django-invoked `None` at
  tearDownClass; C2/C16 move sets opposite) — note N7 on trigger
  phrasing. R-B → per-subject-rejection-grammars: trigger
  ("one owned rejection-message grammar") re-checked unfired — all
  13 strict sites still raise their own subject's type/message,
  witnessed 3 + target at both revisions. R-D → hints-R4 (+ leaf
  F2-nested, confirmed present): neither passage carries the other's
  mechanics at current bytes; literal R4 contradiction trigger also
  unfired — note N4.
- Rejections (4): AGREE — each carries a contract difference +
  trigger + durable home. R-C (fresh) re-derived: `truth.static_attr`
  returns `default` on absence and bypasses live lookup (read at
  `truth.py` :401–427), so routing through it would install where
  the pinned oracle demands `AttributeError` — behavior differs,
  trigger (truth write protocol + spec row) unfired.
- Near-misses (4): AGREE cleared by my own checks — spec-7 vs suite-9
  (both extra rows present at HEAD too, consistent with the typed
  contract; archived spec); no connection-type check (Decision 8
  specifies none); non-`str` method_name (stdlib `TypeError`
  precedes mutation by code order); non-atomic check-then-act
  (single-threaded `setUp` use documented, no atomicity source).
- Index rows: AGREE 9/9 match their findings (5 file-local ↔ F1–F5,
  4 rejected ↔ R-A/R-B/R-C/R-D with correct CONVERGE annotations);
  all 9 names absent from the plan (0 hits — no collision);
  `## Families` none correct.
- Freshness: every cited pin re-derived digit-for-digit MATCH —
  target `0df97813…` CLEAN both revisions; `_django_patches`
  HEAD `ba98f585…`/worktree `6918a213…` (7 hunks, all outside the
  judged regions: framing :1–114, predicate def + both call sites —
  HEAD :280/:358 vs worktree :281/:359, content-identical shift —
  guard line); `test_wrap` HEAD `4d3c1351…`/worktree `6818d96b…`
  (1 docstring-reflow hunk, 9/9 bodies identical, oracle census 9
  both); init `48b45d1b…`; spec-024 `46335d7e…`; spec-043
  `a31a06f1…`; glossary `3413edc3…`; CHANGELOG `d4e10355…`;
  TREE `5d562733…`/`769c2743…` (`_wrap.py` lines identical);
  docs-readme `1497164f…`/`30978c34…` (grep-0 both); tracking.py
  `046b254a…` (`wrap_cursor` :59, check :68); forms-sets
  `36ce80b4…`/`2642a647…`; registry `81bd561c…`/`492654d2…`;
  serializer-converter `6652d092…`/`96d2b56a…` (per-subject
  difference holds both revisions, witnessed). Django 6.1 +
  `_DatabaseFailure` importable (probe claim consistent with the
  installed tree). Gap repaired: N1/N2 below.
- Pending execution: AGREE None — 9 permanent oracles pin every
  owned behavior; sharded/PG inapplicable by construction (no DB,
  alias, or dialect reach; the suite's own docstring states no
  sharded need).
- Zero-edit: CONFIRMED — target worktree == HEAD (`0df97813…`);
  window holds only the plan + `review-0_0_15.md` + this untracked
  artifact; no `.py` touched so no ruff run owed (confirmed instead).
- AGENTS.md prose: PASS — `:NN` refs allowed in `dry-*.md`
  scratchpads; symbols cited `path::Symbol`; 10-header link
  scaffold present; no provenance words; no plan edit.

Record notes (immaterial — none moves a home, count, or gate):
N1: the System trace promises `truth.py` "pinned by hash" but no
hash literal appears — repaired here: worktree
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9` (untracked, no HEAD
side), judged region `static_attr` :401–427 semantics re-verified
(default-on-absence + lookup bypass); any byte change reopens R-C.
N2: the prior `_django_patches` file artifact hash likewise unrecorded
— `9b3eec4b4157cb70311ffe6fc675e7672007abbd` (non-load-bearing;
all triggers re-derived fresh). N3: C15/R-B "13 sites" is the
worktree strict census; HEAD strict is 12 (delta = untracked
`truth.py`). N4: R-D checked mechanics-separation while hints-R4's
literal trigger is contradiction — both unfired, verdict stands.
N5: "0 wrap tokens" in `client.py` = connection-wrap tokens (0/0
verified); HTTP-"wrapper" prose is a different sense. N6: C12's
"no install" overstates by one word — "install" is the helper's own
contract prose; no patch-lifecycle machinery exists. N7: R-A's
"L2 trigger" is L2's own re-check of a 0_0_11 verdict, not a
forward trigger literal — the separation itself is re-verified
fresh at current bytes.

No defects (nothing breaks a contract row). No workspace runs (all
inspection read-only in the shared tree: `git hash-object`,
`git rev-parse`/`git show`/`git grep HEAD`, worktree greps; nothing
source-mutating, no pytest). Verdict: verified.



