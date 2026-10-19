# DRY review: `stored-descriptor-unwrap`

Status: verified
Run: 0.0.15 2026-10-11-17
Item: Family `stored-descriptor-unwrap` (run 17, drifted twins + inline pair)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `02ccc4336c7c0c25b13bd57e5489dd71f43f81a0` (resolves as commit)
HEAD: `c37a08a085113d628a554ee199f4d741d7c86cdf`
Slot: `dry/stored-descriptor-unwrap/consolidate` (no source-mutating run needed; zero edits)

## System trace

Seed re-derived fresh, all four confirmed at current bytes. (A)
`types/definition.py:441` `_unwrap_method`: exact `{classmethod,
staticmethod, MethodType}` to `__func__`, else the value; 2 callers
(`:434-435`, both in `_is_framework_relay_id_resolver`). (B)
`types/relay.py:375` `_classmethod_function`: exact `{classmethod,
MethodType}` to `__func__`, else `None`; 5 callers (`:707`, `:728`,
`:733`, `:1207-1208`). (C) `_django_patches.py:160` + `:260`: identical
inline `descriptor.__func__ if truth.is_instance(descriptor, classmethod)
else None`. (D) `_django_patches.py:404-405`: guarded direct
`installed.__func__` read inside an is-installed predicate.
Whole-package sweep for the mechanism (`__func__` reads, unwrap helpers)
found three more definitions: (E) `types/base.py:596` `_meta_attr`
(staticmethod-only exact unwrap, value fallback, ~20 Meta-read callers);
(F) `forms/sets.py:231` (staticmethod to func for an arity check,
`FunctionType` passthrough, early return otherwise); (G)
`utils/typing.py:176` `_callable_inspection_target` (partial/staticmethod
peel loop with a depth cap for async detection). Excluded by body:
direct `Known.method.__func__(args)` call-throughs (`types/relay.py:221`,
`:270`, `:310`; `filters/sets.py:1166`); `utils/truth.py:105` (hunt-untracked
bound-method slot reader for naming); the mutations FAM-2 callability pair
(a different, already-closed rule); prose-only mentions. Row 899
(`types-relay-func-identity-vs-override-detection`) is the post-unwrap
comparison layer (F4); this item is the pre-comparison unwrap step.

## Verification

### Matrix

1. Cross-flavor: swept every flavor; E/F/G above are the finds, each a
   distinct contract (F3). No third override-detection unwrap exists.
2. Sync/async twins: inapplicable; all seven sites are pure sync predicates.
3. Derived knowledge: the `__func__` slot spelling is CPython-owned (not
   our rule); our rule per site is its accepted set + fallback, and those
   differ (F1-F3).
4. Inverse/round-trip pairs: none; every unwrap is one-way.
5. Contracts in another medium: spec-015 + spec-031 pin B's `None`
   semantics (oracles, listed not counted); A/E/F/G rest on docstrings.
6. Enforcement by omission: no guard family; each unwrap is complete for
   its own question. Discharged.

### Challenges

| Change posited | Definitions forced | Count |
|---|---|---|
| Recognize staticmethod as an override candidate at B | B only (A already unwraps; C-G answer elsewhere) | 1 |
| B adopts value fallback (plain function becomes an override) | B + spec-031 pin test breaks (`test_plain_function_...`) | 1, spec-barred |
| A adopts B's contract (drop sm arm, `None` fallback) | A only; realistic inputs agree, pathological ones flip | 1 |
| C/D adopt `is_exact` (builtin-slot guarantee) | both C inlines, but single expressions (below bar, F2) | 2, below bar |
| New wrapper type recognized package-wide | no shared set exists; each site answers its own spec | 1 per site |

## Findings

### F1 — A vs B: two contracts, not drifted copies (REJECTED)

A is a TOTAL normalizer: every input maps to a comparable function or the
value itself, and `_is_framework_relay_id_resolver` compares the result by
`is` against bare known functions. B is a PARTIAL detector: anything outside
exact `{classmethod, MethodType}` maps to `None`, and `None` is a spec'd
signal with per-caller meaning — preserve at `install_relay_node_resolvers`
(spec-015: the `existing_func is not None` clause `:1209` counts a
funcless attribute as an override) versus overwrite at
`_consumer_overrode_resolve_typename` (spec-031, pinned by
`tests/types/test_relay_interfaces.py:2271`, which installs over a plain
function). Substituting A at B's callers breaks that pin test on a realistic
input; substituting B at A's callers flips pathological-input verdicts
(bare/default-function assignment) and falsely couples elision safety to
override detection's spec. One helper serving both needs accepted-set +
fallback parameters: a barred mode flag. Proofs: the two spec sentences +
the pin test body, all static-reviewed. Trigger: a spec unifying both
questions' accepted set AND fallback.

### F2 — C pair below bar; D a different question (REJECTED)

The two C inlines are textually identical and share one question, but each
is a single conditional expression: below bar per the run-14 one-expression
precedent. D is an is-installed predicate, not an unwrap. C/D's
subclass-inclusive check differs from A/B/E's exactness guarantee; unifying
the style changes subclass-input behavior. Trigger: either inline gaining
branches, or the pair diverging.

### F3 — E/F/G each answer their own question (REJECTED)

E mirrors class-read for staticmethod only because Meta validators must see
a classmethod value still wrapped (unwrapping it changes validation
verdicts). F needs the `(function, declared-as)` pair plus skip-otherwise
for arity validation; a shared helper cannot express that shape. G is a
bounded peel loop with a `RuntimeError` contract for async detection.
Trigger per site: its question adopting another site's accepted set.

### F4 — Row 899 adjacency, no reopen

Row 899 rejected merging the post-unwrap comparisons (three questions, one
shared spelling). This item tests the pre-comparison unwrap layer, which
row 899's file list does not fully cover (C/D/E/F/G outside it) and whose
verdict row 899's reasoning does not reach: differing questions stay
separate whether or not the unwrap feeding them is shared. This item finds
the unwraps themselves differ in contract, which is consistent with row 899
and fires none of its triggers.

## Defects

None. The apparent staticmethod asymmetry between B's callers (preserve at
install, overwrite at typename) is specified on both sides (spec-015,
spec-031), not a gap.

## Judgment

Disproved: seven unwrap sites, four contracts (total normalizer, partial
detector, faithful Meta read, arity/async specialists), zero shared rule.
No consolidation removes a change obligation; no edit is owed.

## What shrinks

- The rule: none shared. The family decomposes into F1 (total-vs-partial
  identity recovery, spec-pinned both sides), F2 (below-bar inline pair +
  predicate exclusion), F3 (three single-owned specialists), F4 (row-899
  adjacency without reopen).
- The change: zero edits. Attribute-before-edit never triggered (no path
  touched); all six candidate files stay exactly as found.
- The owner: none (no consolidation, no new abstraction).
- Net lines: +0/-0 over ITEM_BASELINE.
- Machinery attestation: no new helper, driver, registry, mode flag, or
  test; nothing added that obscures ownership.
- Freshness fingerprints (WT bytes via `git hash-object`): definition.py
  `cde8437f`, relay.py `3b4447ae`, _django_patches.py `553cbada`,
  base.py `7e65b2bd`, forms/sets.py `6681c33c`, typing.py `b7e69600`,
  test_relay_interfaces.py `5c5ed7fe`. Searched population: package-wide
  `__func__` census (7 code sites + prose), `unwrap` census, per-helper
  caller census. Contract sources: spec-015 identity-test sentence,
  spec-031 Decision 10 + pin test, the six owner docstrings.

## Independent verification (Worker-2)

Own trace (derived before opening `## Findings`). Whole-package
`__func__` sweep: 7 logic sites — (A) `types/definition.py:441`
`_unwrap_method`, total, exact `{cm, sm, mt}`, value fallback, 2
callers (`:434-435`); (B) `types/relay.py:375`
`_classmethod_function`, partial, exact `{cm, mt}`, `None`
fallback, 5 call sites (`:707`, `:728`, `:733`, `:1207-1208`);
(C) `_django_patches.py:160` + `:260`, inline, `is_instance`
(not exact), `None` fallback; (D) `:404-405`, is-installed
identity predicate; (E) `types/base.py:596` `_meta_attr`,
sm-only exact, value fallback; (F) `forms/sets.py:231`,
sm-to-func + `FunctionType` passthrough + early return for the
arity error shape; (G) `utils/typing.py:176` bounded
partial/sm peel (`RuntimeError` ceiling, classmethod out of
contract). Excluded by body: direct `Known.m.__func__(...)`
call-throughs (`types/relay.py:221`, `:270`, `:310`;
`filters/sets.py:1166`); `utils/truth.py:105` (MethodType-only
slot getter for name derivation, no descriptor gate);
`mutations/sets.py:1036` + `mutations/fields.py:140`
(callability checks, no `__func__` read); prose. Challenges:
staticmethod-override at B → B only; B value-fallback →
breaks the `:2271` pin (plain func becomes override,
`custom`, no install); A adopts B → A only (bare-function
flip); C/D `is_exact` → 2 single expressions, below bar;
new wrapper type → 1 per site, no shared set. Owner I would
choose: none — two irreconcilable contracts (A total vs B
partial, `None` load-bearing in opposite directions at
`:1209` preserve vs `:729` overwrite) plus below-bar pair
and three specialists; any shared helper needs
accepted-set + fallback parameters (barred mode flags).

Reconciliation: W1's census matches mine site for site,
including all four exclusion classes and both caller
counts (re-grepped exact). F1's spec pins re-derived:
spec-031 test-plan sentence + `:2271` pin the overwrite
side; spec-015 pins preserve. F2's below-bar call stands
(single conditional expressions; Django-owned storage
shape is someone else's rule per DRY.md). F3's splits
stand (E's sm arm additionally oracle-pinned at `:1764`,
see note 1). F4's row-899 adjacency verified against the
row text (post-unwrap layer, file list excludes C–G).
Zero-edit confirmed: `git diff ITEM_BASELINE` names only
the plan file (Worker-0 hunks), artifact untracked, no
package/test tracked edits. All 7 fingerprints re-hashed
identical. No `## Pending execution` owed (all proofs
static-reviewed, nothing execution-deferred). Matrix all
six axes discharged with reasons; verdict-neutral record
notes: (1) axis 5 underclaims E (docstring + `:1764`
oracle, strengthens F3); (2) F1's preserve-side
attribution rests on spec-015's general preserve contract
rather than a funcless-specific sentence — the
irreconcilability stands regardless. Prose rules hold
(per-cycle `path:NN` allowed, no process provenance, no
Markdown links so no scaffold owed); ruff has no `.py`
to check (zero tracked edits). No package defects found,
so no `(Worker-2)` entry under `## Defects`. Status slip
ruled accept-and-verify: this `verified` stamp overwrites
the `designed` line (the dispatch brief itself offered
`designed` as a return word, and the content meets the
zero-edit `ready-for-verification` bar).
