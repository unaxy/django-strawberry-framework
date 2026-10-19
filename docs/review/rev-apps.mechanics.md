# Review · Mechanics: `django_strawberry_framework/apps.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=d4ff8d5067f177b771ba3870240d266cdc285f86

## Trace

Target read whole at blob `8ae1a3a3` (live; equals ITEM_BASELINE;
`git diff <ITEM_BASELINE> -- django_strawberry_framework/apps.py` empty;
working tree clean for the target, as dispatched). Orientation:
`review_inspect.py` into
`docs/review/temp-tests/apps/mechanics/inspect/` (json
`docs/review/temp-tests/apps/mechanics/apps.json`), leads only: 5
imports (1 module-level, 4 function-local), 2 symbols, 0 hotspots, 0
import-time work.

Callers and contracts followed: no production importer of
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig`
exists (grep over `django_strawberry_framework/`, `tests/conftest.py`,
`examples/fakeshop/test_query/conftest.py`: the only
`_*_patches import apply` sites are the four function-local imports in
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`;
Django's app loader resolves the class by dotted path);
`django_strawberry_framework/conf.py::upstream_patches_enabled` plus
`UPSTREAM_PATCH_DEPENDENCIES` (gate vocabulary and mapping contract,
read whole); the gate line of each
`apply()` (`_django_patches.py:418`, `_strawberry_patches.py:847`,
`_cross_web_patches.py:343`, `_graphql_core_patches.py:124`: each
`if not upstream_patches_enabled("<dep>")`);
`django_strawberry_framework/__init__.py` (no `apps` / `AppConfig`
reference: the non-export posture holds);
`examples/fakeshop/config/settings.py:71` (package-name
`INSTALLED_APPS` entry); `docs/README.md:14` (check/signal hooks
resolve through the AppConfig); `docs/GLOSSARY.md` anchors "Django
AppConfig" and "Upstream patches" (four appliers in order, self-gated,
idempotent, no checks / signals / `finalize_django_types`). Oracles
read whole: `tests/test_apps.py` (14 rows: import, subclass,
name/verbose_name pins, registry resolution, negative shape,
`ready` presence, four-applier dispatch plus re-fire,
per-module double-reload reinstall). Sibling patch-module items
`_django_patches.py`, `_graphql_core_patches.py`, `_strawberry_patches.py`
are `verified` this run; their Mechanics records were read for the
`apply()` contracts this dispatcher relies on (self-gate,
fail-loud validation, idempotent install). Plan
`docs/review/review-0_0_15.md` `## Owned changes` holds no `apps.py`
rows. Sibling axis records absent at read time (only
`docs/review/rev-apps.md` skeleton exists): no Handoff or Cross-axis
sections to absorb. `docs/dry/dry-file-apps.md` (concurrent DRY item,
zero-edit verdict) read for orientation; no finding imported.

Workspace runs, address `review/apps.py/mechanics`, package digest
`sha256:41e15d13e6b3319ad3be2833eed44c172f16590b77b202838bfc57cc2e52a54c`,
cell `default`, each copy `fresh`, shared tree unmoved since sync:

- `review-20260928T230611-2a3962`:
  `pytest tests/test_apps.py --no-cov -q`, 14 passed.
- `review-20260928T230634-0b4462`:
  `python docs/review/temp-tests/apps/mechanics/probe_import_locality.py`,
  `patch modules in sys.modules: []`, PASS: importing the apps module
  pulls in no patch module (the function-locality contract).

Cells: `sharded` and `pg` inapplicable by construction. The target
performs Django app registration and four in-process monkey-patch
installs at app load; it opens no database, names no alias, emits no
SQL, and branches on nothing dialect- or alias-count-dependent. The
verifier judges.

Looks-for discharge (each entry a finding, `none` + reason, or a
rejection + trigger): rule at caller vs owner -> R1, R5; policy in
adapter -> none (the `ready()` body is four imports plus four calls,
no policy); contract sources vs body -> none (every live source
agrees; the two stale counts are archived history, R7); unreachable
branch -> none (no branches); mode flag for named adapter -> none (no
flag in the target; the `APPLY_UPSTREAM_PATCHES` vocabulary lives in
`conf.py`, its own item); state owned twice -> none (one AppConfig
subclass, discovery pinned by the registry oracle, no `default`
attribute, no re-export); dependency direction -> none (module level
imports only `django.apps.AppConfig`; patch modules enter
function-locally at call time; nothing imports this module in
production; no `TYPE_CHECKING`); settings read at import -> none
(class body is two string literals); `__all__` disagreement -> none
(no `__all__`; the loader-facing non-export posture is pinned);
one rule twice -> R2, R6, R8; sync/async twins -> none (no async
surface; Django calls sync `ready()`); missing sibling guard -> R3,
R4.

Fingerprints (`git hash-object`):
`django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`tests/test_apps.py` 5ca8b62c53185343ebfec95315f59ec6104fc851;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/_django_patches.py`
6918a213170ea902386a5845da8c6cd1f901baf2;
`django_strawberry_framework/_strawberry_patches.py`
90f711fb420b8902434406735c2e367f011e4177;
`django_strawberry_framework/_cross_web_patches.py`
52bf8f5712d632817587f93c4eeb881fd74ffaae;
`django_strawberry_framework/_graphql_core_patches.py`
90ac4f3cc15be1c24dc1f0281206e260d7555cb6;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`examples/fakeshop/config/settings.py`
e2ba51142ef2921163a7d3b8a880ed109df4e3a8;
`docs/README.md` 30978c34f63a833ffcc0fa11c80b773d241921be;
`docs/GLOSSARY.md` 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd;
`docs/TREE.md` 769c274392d055c566a2b2d3006afc7baa5d0a9c.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

- **R1: no gate around the dispatch in `ready()`.** Correct as is:
  the gate lives inside each `apply()` by recorded contract
  (`docs/GLOSSARY.md` "the gate lives inside each `apply()` rather
  than in `ready()`"; `conf.py::upstream_patches_enabled` "the only
  callers are the four patch modules' `apply()` gates"), and all four
  gates verified present with canonical names. A dispatcher-side gate
  would double-gate and couple the dispatcher to the dependency
  vocabulary it deliberately does not spell. Reopen: an `apply()`
  reachable from `ready()` that does not self-gate.
- **R2: the four `apply()` install scaffolds look alike; consolidate
  at this target.** The definitions live in the patch modules, not
  here: this target holds only the consumer side (four imports plus
  four calls, spelling no gate and no patch inventory). A shared
  driver owned here would couple four disjoint retirement dates to
  one call site; retiring one upstream deletes its module while the
  dispatcher drops two lines by construction. Out of this item's
  fence either way (owner: the patch modules or the project pass).
  Reopen: a sequence-level change needed in two or more patch
  modules, or a fifth patch module arriving with an identical
  install shape.
- **R3: the dispatch order is a dependency order, or should be
  reordered.** The order (django, strawberry, cross_web,
  graphql_core) is stated fact, not a claimed reason: the four
  appliers replace disjoint upstream targets (test-case teardown,
  Strawberry view slots, the `cross_web` adapter property,
  graphql-core list completion), so no order is forced, and the
  dispatch oracle asserts installation, never sequence. Reopen: a
  future applier whose install depends on another applier's
  installed state.
- **R4: `ready()` lets an `apply()` failure propagate instead of
  warning and continuing.** Fail-loud is the contract: an unaudited
  upstream body raises rather than patching silently (pinned by each
  patch module's drift rows), and masking it at the dispatcher would
  boot a consumer project onto an unpatched upstream it believes is
  patched. Reopen: a patch module whose failure mode is
  advisory rather than a contract break.
- **R5: `strawberry` and `cross_web` jointly own one fix but gate
  independently.** Documented behavior owned by `conf.py` ("disabling
  one of the pair alone is safe but leaves upstream's sync view
  unfixed"): per-dependency opt-out with independent outright
  deletion per module. Co-gating the pair in `ready()` would move
  gate vocabulary into the dispatcher (R1). Reopen: a state of the
  pair that is unsafe rather than merely unfixed.
- **R6: a fifth patch module would touch dispatcher, vocabulary,
  oracles, and prose together.** DRY change challenge ("a fifth
  patch module arrives"): one new lifecycle defined once in the new
  module; `ready()` gains two lines as consumer, `conf.py` gains one
  vocabulary name, oracles and projections follow. Dispatch defined
  once; consumers, oracles, and projections listed, not counted.
  Reopen: the fifth module arrives (its dispatch lines are that
  change's consumer follow, not a count owed today).
- **R7: archived spec-021 says "three appliers", CHANGELOG 0.0.7
  says one.** Both are historical records of their release, never
  rewritten; every live contract source (glossary anchors, the
  `ready()` docstring, the dispatch oracle, the gate vocabulary)
  says four and agrees with the body. Not a target defect and not
  this item's prose to sync. Reopen: a live contract source
  disagreeing with the body.
- **R8: the `name` literal repeats in `INSTALLED_APPS` and test
  spellings.** The settings entry is the consumer typing the same
  string per spec-021 Decision 7 (which forbids rewriting it to the
  dotted config path); the test spellings are oracles. One
  definition, in the class body. Reopen: a second consumer-facing
  spelling the package itself must keep in sync.

Handoff: The dispatcher is four imports plus four calls with every
placement decision pinned by oracles and every contract sentence
verified against a live source; the interesting Mechanics questions
all resolve one layer down (gate vocabulary in `conf.py`, install
lifecycles in the four patch modules, three of them verified this
run). The probe and the 14-node oracle run above are the behavior
evidence; nothing else in the target admits a behavioral probe (no
branches, no I/O, loader-resolved). No threads left open for a
verifier beyond the standard re-read: a re-pass would re-run the
same oracle file and re-grep the same absences.

## Verification (Mechanics)

Step 1: `git diff
d4ff8d5067f177b771ba3870240d266cdc285f86 -- tests/test_apps.py
django_strawberry_framework/apps.py` hashes
`sha256:aba74b2e...` equal to
`docs/review/temp-tests/apps/diff/pass-1.diff` (`cmp` clean). The
tree has not moved under the pass; grading proceeds.

Proof lines: none owed. Case-insensitive grep for "proof" in this
record prints 0, and grep for `^## Cross-axis` across all three axis
records prints 0 (the sole "Cross-axis" mention is this record's
Trace line stating no such sections existed to absorb; both sibling
Handoffs confirm they place none). No verbatim Proof run exists on
this axis.

Behavior preservation (test-only change): holds. The F4 `why`
literals' only consumer is the fail-message f-string
(`tests/test_apps.py:83`; grep for "why" shows lines 65/73/83 only,
identical shape at baseline), so the literals can alter failure
text but never pass/fail; node ids are stable (`ids=[...]` and the
first tuple elements untouched in the diff). The suite result is
unchanged: `review-20260928T232010-ea4ee4` (`pytest
tests/test_apps.py --no-cov -q` at
`review/apps.py/verify-mechanics-1`, fresh copy, package digest
`sha256:41e15d13...` matching the review digest, shared tree
unmoved) reports 14 passed, matching the pre-change
`review-20260928T230611-2a3962` (14 passed). Independently rebuilt
F4-only reconstruction
(`verify-mechanics-1/recon_f4_only.py`, baseline plus the three
literal swaps) diffs against live by exactly the Medium docstring
hunk; scoped `--code-digest` recon-vs-live exits 0 (`075c6d2f`
both) and baseline-vs-live exits 1 (`3e41253c` vs `075c6d2f`),
reproducing Worker-2's figures: the Medium hunk moves no code and
the delta is exactly the F4 literals.

Whole-diff read: two hunks in `tests/test_apps.py` only;
`django_strawberry_framework/apps.py` is a 0-byte diff vs
ITEM_BASELINE (hash `8ae1a3a3` unchanged). No placement, contract,
dependency, state, duplication, sync/async, or guard question
arises from a docstring paragraph plus fail-message literals. No
symbol moved or renamed, so `--cited-by` is not owed. No new test
owed (Comments findings owe none); the touched file stays package
tier, correct per its module docstring (loader state, not a wire
shape; live tier inapplicable). No `prove` owed: no production
hunk exists to revert and no behavior fix relies on a test.

Attacks (all passing): A1 oracle suite 14 passed
(`review-20260928T232010-ea4ee4`); A2 import-locality probe `patch
modules in sys.modules: []`, PASS (`review-20260928T232020-cdfe2e`,
same copy, still fresh, same digest); A3 production-importer
census still 0 executable importers (only Sphinx `:meth:` prose
refs and `django.apps` imports; the sole executable importer
anywhere is `tests/test_apps.py:37`); A4 independent
reconstruction plus scoped digests above. Cells: sharded and pg
inapplicable by construction (concur): the target runs at app load
with no database contact, and the change touches test prose plus
fail-message literals only.

Disputes: none recorded (grep "disputed" in `rev-apps.md` prints
0). Worker-2's "Proof-shape qualification" is explicitly not a
dispute; that classification is correct - it is a proof-scope note
with its own evidence, judged sound above.

Deferred Lows F2/F3: ride-rule deferral correctly applied. Per
REVIEW.md Severity, a Low rides only on a file already changing for
a higher finding; the Medium lives in `tests/test_apps.py` while
F2/F3 live in `django_strawberry_framework/apps.py`, which no
higher finding touches. The reason is recorded in `##
Implementation (Worker-2)` and visible for `## Outcomes`; `apps.py`
confirmed byte-identical.

Lint gates (`--check` forms only): `ruff check
tests/test_apps.py` exit 0; `ruff format --check
tests/test_apps.py` exit 0; `check_trailing_commas.py --check
tests/test_apps.py` exit 0 (0 violations);
`check_citations.py --check` exit 0 (1297 resolve). All green.

No new findings, no gaps. Status: verified.

Fingerprints: `django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`tests/test_apps.py`
fe912987087b560314b04274ffca6ad8a1ca7f02. Scratch:
`docs/review/temp-tests/apps/verify-mechanics-1/`
(`probe_import_locality.py`, `baseline_test_apps.py`,
`recon_f4_only.py`). Runs: `review-20260928T232010-ea4ee4`,
`review-20260928T232020-cdfe2e`.

Handoff: Read beyond the record's trace: `rev-apps.md` `##
Implementation (Worker-2)` whole, both sibling axis records with
their Handoffs, the live `tests/test_apps.py` whole, and the
pass-1 diff. The one judgment call - Worker-2's F4 proof shape
(fail-message literals cannot carry whole-file `--code-digest`
identity) - is sound and was reproduced from an independently
built reconstruction, not trusted from the report. Deferred F2/F3
(class-docstring mood, `ready()` double conjunction) stay live for
the next item that touches `apps.py`. No open threads; nothing
further for a re-pass to re-check beyond the standard re-read.
