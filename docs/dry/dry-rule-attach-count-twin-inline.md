# DRY review: `attach-count-twin-inline`

Status: verified
Run: 0.0.15 2026-10-11-18

Question: inline `connection.py::_attach_count_sync` /
`::_attach_count_async` (one production caller each at the `:854`
`isawaitable` dispatch) into one branch — or disprove (distinct
responsibilities) and return zero-edit with triggers.

## System trace

Selection-gated `totalCount` attach over the offset-fallback tail, all in
`connection.py`; guard + setter already shared. Definitions:
`_set_total_count` (:224, single writer of `_TOTAL_COUNT_ATTR`, lazy
`value`, `want_count` gate); `_guard_total_count_countable` (:1542,
`want_count` + non-QuerySet raises `GraphQLError`, spec-030 Decision 7);
`_attach_count_sync` (:1562, guard → early-return unless wanted → lazy
bound `.count` into the setter); `_attach_count_async` (:1582,
await-before-raise :1596 → guard → `await acount()` into the setter).
Dispatch: `_consume_fallback` :854-856 (`isawaitable` branch).
`want_count` origin :1389 (`_resolves_total_count and
_total_count_requested(info)`). Sibling setter composers (consumers, not
counted): empty-page :273, window :671, keyset :1145/:1152/:1175/:1193/:1200.
Caller census (fresh, whole repo): sync = 1 prod caller (:856), 0 direct
test callers; async = 1 prod caller (:855) + 1 direct test caller
(`tests/test_connection.py:1013`). Oracles: eager-`.count`-read pins
(`test_connection.py:790/:820`, schema-level), async set-source `:958`,
direct await-before-raise pin `:984`, async end-to-end `:1028`.
No `totalCount` surface in `list_field.py` (grep 0). No spec sentence
names the twins (grep 0 over `docs/spec-*.md` + `docs/SPECS/`).

## Verification

### Matrix

1. Cross-flavor mirroring: searched `total_count|totalCount` package-wide;
   only connections count; list-field has no count surface. No mirror.
2. Sync/async twins: the target itself. Compared by behavior (see
   Challenges): await boundary, ordering, value shape, branch spelling —
   each difference color-forced. Keyset's own count arms (:1193/:1200)
   converge on the same setter; not a new family.
3. Derived knowledge: `want_count` derived once (:1389), threaded as a
   bool; never re-derived. `.count` vs `.acount()` are two ORM calls,
   not two derivations of one fact.
4. Round-trip pairs: none — attach is one-way (queryset → int → attr).
5. Other media: oracles spell own expectations (message text,
   consumed-flag, GC no-leak probe); never read the owner. Contract prose
   owned by spec-030 Decision 7; KANBAN serial-count note is projection.
6. Enforcement by omission: family = 4 attach paths; guard enforced where
   non-querysets are admitted (fallback); keyset proves QuerySet at head,
   window reads annotations, empty-page takes served totals. No gap.

### Challenges

- C1 new guard arm → 1 def (`_guard_total_count_countable`; twins compose
  it by name).
- C2 new setter shape → 1 def (`_set_total_count`; 7 composing sites
  listed, not counted).
- C3 new `want_count` discipline → already 6 context-adapted spellings
  (:239, :1565, :1598, :1142, :1193/:1200, window probe); unifying the
  twins' two leaves four. No single owner exists.
- C4 new countable value shape → 2 defs (sync value arm + async value
  arm), and any sharing keeps 2: sync must pass a lazy bound method
  (eager-read `AttributeError` hazard), async must await an int (the
  setter takes `int`, not a coroutine).
- C5 new await ordering → 1 def (`_attach_count_async` only; sync has
  no await). Pinned behaviorally (direct pin, green below).
- C6 delete + inline at :854 → async arm cannot inline into sync
  `_consume_fallback` (await needs a coroutine): the result is the same
  body as an unnamed per-call closure, minus the boundary the direct
  pin test imports. P11 keep, both wrappers (see Findings).

## Findings

F1 (rejected): the twins stay two bodies. Shared pure decisions (guard,
setter) are already single-owned; each twin's remainder is color-forced
execution — sync: eager-attribute-read hazard isolation + lazy-method
contract; async: await-before-raise effect isolation (unawaited coroutine
= `RuntimeWarning`, hard failure under `-W error`) + the named boundary
the direct pin oracle imports. The `if not` vs `if` spelling fork is
forced, not drift: the lazy read must early-return, the await expression
must sit inside the wanted arm. No posited change moves 2+ definitions
that a consolidation could reduce to one without machinery (C4's 2 is
irreducible: `count` vs `acount` are different ORM calls). Converges
with `dry-file-connection.md` R2 (file-local), re-derived fresh here:
caller censuses re-taken, R2 trigger re-checked (second countable
surface still 0 hits). Keep rationale already lives at the owner (twin
comments + guard docstring); no owner-prose edit owed.
Triggers: (T1) a list-field `totalCount` surface appears; (T2) a
package-wide maybe-await primitive lands (dry-0_0_11 trigger); (T3) the
twins drift (guard-then-set order forks, or a third caller appears).
Index rows for Worker-0: `attach-count-twin-inline` (rejected, owner
`connection.py` R2 cluster); `offset-fallback-count-branch-shape`
(rejected, color-forced spelling fork, same owner).
Proofs: existing behavioral oracles (wrong value/message/leak each fail);
direct async pin re-run green 1/1 on current bytes (authorized single
shared-tree run, `--no-cov -n0`). Freshness: `connection.py` worktree
`3e111147` vs HEAD `b984ca99`; traced bytes (:224-241, :844-856,
:1542-1606) byte-identical to HEAD (no `-U0` hunk covers them).

## Defects

None found while tracing.

## Pending execution

None.

## Judgment

Disproved: the twins share all shareable decisions already; the remainder
is color-forced execution with a test-imported boundary. Inlining removes
no change obligation and trades a named module body for a per-call
closure. Zero-edit, triggers T1-T3. Scope respected (sibling item 1's
files untouched); concurrent dirt left alone; no commit.

## What shrinks

Nothing: zero-edit verdict, net 0 lines, no machinery added, no spec
sentence falsified (none names the twins), no test rewritten. What the
trace established, measured on current bytes:

- Production callers: `_attach_count_sync` 1 (`:856`), `_attach_count_async`
  1 (`:855`) — plus 1 direct test caller for the async twin
  (`tests/test_connection.py:1013`), which corrects the brief's "1 caller
  each" premise: the async wrapper is a test-imported boundary, not a
  1-caller wrapper, and inlining it would force the await-before-raise pin
  through the full `_consume_fallback` path.
- Shared-decision census: guard 1 def / 2 composers, setter 1 def / 7
  composing call sites, `want_count` origin 1 site (`:1389`).
- Irreducible-2 proof (C4): any "new countable shape" change must still
  touch both color arms however they are arranged, because the ORM offers
  no colorless count call and the setter accepts `int`, not a coroutine.
- Prior-trigger checks: R2's "second countable surface" still 0 hits
  (`list_field.py` has no count surface); dry-0_0_11's maybe-await
  primitive still absent package-wide. Both rejections stand on fresh
  evidence, not inheritance.
- Oracle liveness: `test_attach_count_async_awaits_before_guard_raises`
  passes on current bytes (1/1, `--no-cov -n0`, shared tree).

## Independent verification (Worker-2)

Traced from source before reading `## Findings`; reconciled after.

Sites + roles (mine): `connection.py::_set_total_count` = DEFINITION
(single `_TOTAL_COUNT_ATTR` writer, lazy value, `want_count` gate; 7
composing call sites, all by name); `::_guard_total_count_countable` =
DEFINITION (Decision 7 rule + wording; 2 composing call sites);
`::_attach_count_sync` = CONSUMER (guard-compose + `want_count`-gated
eager `.count` READ + lazy bound-method into the setter; 1 production
caller at `:856`, 0 direct test callers); `::_attach_count_async` =
CONSUMER (await-conn + guard-compose + `await acount()` + setter with an
int; 1 production caller at `:855` + 1 direct test caller at
`tests/test_connection.py:1013` - verified the import at
`tests/test_connection.py:78` myself, so the brief's 1-caller premise
fails for the async twin exactly as flagged); `::_consume_fallback`
`:854` = CONSUMER (color dispatch); keyset arms (`:1142-1152`,
`:1188-1201`) = CONSUMERS of the setter (own inline gated reads over a
proven-QuerySet source, different contract); window path = CONSUMER
(setter only, guard bypass by construction); `want_count` origin =
`resolve_connection:1389` (`_resolves_total_count and
_total_count_requested(info)`), threaded as a parameter everywhere.

Definition counts (mine): C1 new guard arm -> 1 (`_guard_total_count_countable`);
C2 new setter shape -> 1 (`_set_total_count`, 7 composers); C3
`want_count` discipline -> 1 (origin `:1389`); C4 new countable shape ->
1 (guard `isinstance`; twin casts follow as consumers); C5 await
ordering -> 1 (async twin only); C6 inline-ability (P11) -> keep both:
the sync wrapper carries the eager-read-gate responsibility (named
hazard + regression pins), the async wrapper is test-imported and
carries await-before-raise, and one merged branch is the deferred
maybe-await shape (color ambiguity + machinery). Owner I would choose:
no new owner; rejection. Target blob at my trace:
`3e11114788a0f2448f0544025418d87575792285` == item-baseline blob.

Hazard re-derivation (mine, probe green): the SYNC eager read is the
hazardous shape - `value=nodes.count` evaluates the attribute at
call time, and a set/generator/list-iterator has no `.count`
(`AttributeError`), so the READ (not just the call) is gated on
`want_count`. The async arm cannot pass lazy because the setter
evaluates `value() if callable(value) else value` synchronously: a
coroutine is NOT callable (stored verbatim = wrong count), while the
bound `acount` method IS callable (called un-awaited, coroutine stored
verbatim = wrong count). Probe:
`docs/dry/temp-tests/attach-count-twin-inline-verify1/hazard_probe.py`
(`uv run python`, exit 0, 6/6 facts).

Independent hunt (mine): whole-package `.count()`/`.acount()` execution
= connection.py only (`:1148`, `:1193`, `:1200`, `:1605`) + lazy
bound-method passes (`:1152`, `:1579`); `orders/sets.py:871` is prose.
`list_field.py` has no count surface (only `Count`-aggregate prose + a
loop variable). `want_count` is connection.py-local (origin `:1389`,
threaded param; no cross-module spelling to share). `_TOTAL_COUNT_ATTR`
has one writer (`:240`) + one reader (field resolver). `isawaitable`
dispatches elsewhere (relay/types/resolvers/querysets/extension) are
different rules, not count-attach. No second countable surface, no
shareable spelling, no P11 deletion: hunt finds nothing.

Reconciliation (after full read): two framing deltas, both compatible,
same verdict. (a) C3: I counted the `want_count` ORIGIN as 1 def
(`:1389`); W1 counts 6 context-adapted branch spellings with no single
owner. Agree with W1's stronger statement - the twins' `if not` vs `if`
fork is forced by context (lazy-read early-return vs await-inside-arm),
and the four further spellings prove no one branch rule exists; the
"branch spelled twice" premise dissolves. (b) C4: I counted the guard
`isinstance` as the definitional 1; W1 counts both value arms as an
irreducible 2. Agree - my probe confirms W1's exact grounds (lazy bound
method vs awaited int, setter takes `int` not a coroutine). All other
rows match exactly (guard 1 def / 2 composers, setter 1 def / 7
composers, twins consumers, origin `:1389`, keyset/window composers,
test-import correction at `tests/test_connection.py:78` + `:1013`,
matrix axes discharged on the real surface, T1-T3 + 2 index rows, no
spec sentence naming the twins - my own greps over `docs/SPECS/` +
`docs/spec-*.md` both 0). Freshness verified independently: worktree
blob `3e11114788a0f2448f0544025418d87575792285` == item-baseline blob;
HEAD blob `b984ca99...` as claimed; all three traced blocks
byte-identical HEAD-vs-worktree (setter 730B, dispatch-tail 406B,
guard-twins 3725B; 38 `-U0` hunks, none covering the ranges).
Maybe-await primitive still absent (only upstream imports + prose
rejecting the abstraction). `## Pending execution` reads "None." rather
than literal absence - substance correct (zero deferred proofs, all
oracles execution-verified), verdict-neutral shape, accepted. Zero-edit
stands: item-scoped diff vs `ebd94e4` over tracked package/test/example
paths EMPTY; untracked `.py` files are pre-existing cycle-baseline
concurrent work, not item additions. No oracle rewritten (nothing
touched). W1's one shared-tree oracle rerun is the entry's authorized
focused test; my probe is pure-Python semantics (no suite, no source
touched). Ruff over touched paths: VACUOUS (zero-edit, no paths
touched; no run over `.`). No defects found (Worker-2: none).

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
