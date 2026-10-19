# Review: `django_strawberry_framework/_graphql_core_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - runs once per list-field completion on every executed operation (sync and async) while installed

## Implementation (Worker-2)

Pass 1, axis order Performance -> Mechanics -> Comments. One production file
changed, two one-line hunks, no test file changed.

Attribution (before any edit): the target was dirty vs HEAD by exactly the
concurrent truthful-reads switch (`from .utils import truth` plus
`truth.class_dict` in `_captured_upstream_method` and `_patch_is_installed`;
HEAD blob `1cd579fb`, live `a188b290`), matching the Performance record
`## Trace` and the Mechanics record `## Trace` and covered by the plan's run-3
`Drift:` lines. `git diff e4385002 -- <target + own tests>` was empty, and the
plan's `## Owned changes` holds no row for this target. Both concurrent hunks
are preserved verbatim; the item-scoped diff below adds exactly my two hunks.

### Performance F1 (Low): implemented

Swapped the first two guard conjuncts in
`django_strawberry_framework/_graphql_core_patches.py::_patched_complete_list_value`
to `isinstance(result, AsyncIterable) and not is_iterable(result) and
self.is_awaitable(res)` (94 chars, one line). All three conjuncts, the
delegate-first call and the residual double-await are untouched; no order
rationale comment added (the record: welcome but not required).

Numbers (interleaved timeit probe, blob `3c415038`, identical to the record's;
10000 iters, min-of-5 per round, median of 9 rounds):

- Before, `review-20260928T214839-a311a1` (`review/_graphql_core_patches.py/before`,
  fresh, digest `sha256:c5a27421...` = the record's digest): sync current
  210.5 ns vs swapped 90.0 ns median, delta 120.5 ns; round ranges 205.3-212.0
  vs 86.5-91.8, non-overlapping; async 176.1 vs 172.6 ns (delta 3.5 ns noise).
- After, `review-20260928T214853-8534e9` (`review/_graphql_core_patches.py/implement`
  `--fresh`, digest `sha256:508a77eb...` = baseline plus the reorder): sync
  211.5 vs 87.6 ns median, delta 123.9 ns; ranges 210.0-214.2 vs 86.6-88.9,
  non-overlapping, swapped 0.41x current; async 173.1 vs 168.5 ns (noise).
- Reproduces the record's pair (205.8 / 87.5 ns, delta 118.3 ns) within run
  noise. No bench figure moves (ns-scale, sub-spread); nothing claimed against
  `## Bench baseline`.

Permanent tests: none added, per the record (no test can pin 118 ns; the
trigger set is pinned by the existing behaviour nodes):

- `tests/test_graphql_core_patches.py`: 10 passed focused in the shared tree
  (`uv run pytest tests/test_graphql_core_patches.py --no-cov -q`), and
  10 passed in the implement copy, `review-20260928T214947-2c06b5`.
- `examples/fakeshop/test_query/test_list_field_async_api.py`: 78 passed in
  the implement copy, `review-20260928T214955-e6b810` (digest `sha256:a5e0fd4e...`
  = final state including the Comments hunk).

Failability:

- Static Proof (record's exact command): fails before (`AssertionError:
  conjunct order`, exit 1), passes after (exit 0).
- `workspace.py prove review/_graphql_core_patches.py/implement
  <root>/implement/failability_manifest.json`, run `review-20260928T215115-b5d4e7`,
  exit 0. Entry 1 (guard `if False:`, trigger set narrowed to nothing) fails
  exactly `test_async_iterable_with_awaitable_children_completes_over_http`
  (baseline 1 passed / mutant 1 failed). Entry 2 (guard `if True:`, trigger
  set widened to everything) fails exactly
  `test_async_queryset_completion_default_resolver` (baseline 1 passed /
  mutant 1 failed). Both restores byte-proved (blob `90ac4f3c` before and
  after). A plain revert-prove is meaningless for a semantics-preserving
  reorder, so the mutants break the trigger set in each direction instead.

### Mechanics: no findings

Nothing to implement. Rejections R1-R7 untouched; no rule moved to any owner.

### Comments F1 (Medium): implemented

Adopted the siblings' wording verbatim:
`except ImportError:  # pragma: no cover - exercised via monkeypatch in tests`
(byte-identical to the `_django_patches.py`, `_strawberry_patches.py` and
`_cross_web_patches.py` lines). No error string touched (the DRY
`upstream-patch-refusal-wording` family owns those).

- Proof: `grep -c "exercised through patched imports"
  django_strawberry_framework/_graphql_core_patches.py` prints `0`.
- Inverse proof (code moved in this file under Performance, so against a
  reconstruction): `<root>/implement/reconstruction.py` = ITEM_BASELINE text
  plus only the Performance reorder hunk (verified: recon-vs-baseline diff is
  exactly line 94; live-vs-recon is exactly line 25).
  `review_inspect.py --code-digest <reconstruction> <live>` prints two equal
  digests `sha256:cf6be5b1...`, exit 0.
- Control: `--code-digest <baseline text> <reconstruction>` exits 1 with
  differing digests, so the instrument sees code movement and the equal result
  is meaningful.
- No before/after, permanent test or failability owed (prose-only).

### Files changed

- `django_strawberry_framework/_graphql_core_patches.py` only: line 94 guard
  conjunct order (Performance), line 25 pragma comment wording (Comments).
  Single-site wordings in the target; no owner move, no new test (existing
  nodes pin the trigger set), no new fixture, no TREE.md render (no module
  first-line change).

Item-scoped diff (`git diff e4385002 -- <target>`): exactly the two hunks
above, `a188b290..90ac4f3c`. No hunk unexplained.

### Lint

On the touched path, in order: `ruff check --fix` (All checks passed, 0
fixed), `check_trailing_commas.py` (0 violations), `ruff format` (unchanged);
verify: `ruff check` pass, `ruff format --check` pass,
`check_trailing_commas.py --check` pass, `check_citations.py --check` whole
tree: OK, 1297 citations resolve.

### Scratch paths and run ids

All under `docs/review/temp-tests/_graphql_core_patches/implement/`:

- `probe_predicate_order.py` (probe copy, blob `3c415038` = the record's)
- `before_probe.json` / `before_probe.stderr` (`review-20260928T214839-a311a1`):
  `workspace.py run review/_graphql_core_patches.py/before -- python <abs probe path>`
- `after_probe.json` / `after_probe.stderr` (`review-20260928T214853-8534e9`):
  `workspace.py run review/_graphql_core_patches.py/implement --fresh -- python <abs probe path>`
- `parity_unit.log` / `parity_unit.stderr` (`review-20260928T214947-2c06b5`):
  `... run review/_graphql_core_patches.py/implement --fresh -- pytest tests/test_graphql_core_patches.py --no-cov -q`
- `parity_live.log` / `parity_live.stderr` (`review-20260928T214955-e6b810`):
  `... run review/_graphql_core_patches.py/implement -- pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov -q`
- `failability_manifest.json` (prove run `review-20260928T215115-b5d4e7`, exit 0)
- `reconstruction.py` (ITEM_BASELINE + reorder hunk), `baseline_text.py`
  (ITEM_BASELINE text, digest-control input)

`workspace.py audit` binds all four cited run ids (each `ok`, package and
database inside its copy).

### Fingerprints (`git hash-object`)

Touched: `django_strawberry_framework/_graphql_core_patches.py`
`90ac4f3cc15be1c24dc1f0281206e260d7555cb6`. Read, all equal to the axis
records' (nothing drifted): `tests/test_graphql_core_patches.py`
`53dca51737e6163c09549d015713ebf9dfcdec88`;
`examples/fakeshop/test_query/test_list_field_async_api.py`
`49e423ea593b8883c4c07593accd822390e82468`;
`django_strawberry_framework/apps.py` `8ae1a3a3b12f0c9792094959c573ea6fab5d804f`;
`django_strawberry_framework/conf.py` `ae3de0a36e2f7737a2c8350e532cdb761b295bcf`;
`tests/test_apps.py` `5ca8b62c53185343ebfec95315f59ec6104fc851`;
`tests/base/test_conf.py` `55b333eb2fff714365058d0a8651fc3a57c603e3`.

### Proposed owned changes

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/_graphql_core_patches.py` | _graphql_core_patches.py | Performance, Comments | `_patched_complete_list_value` (guard conjunct order); `except ImportError` pragma comment (test-mechanism wording) |

Handoff: The change is two lines in one file with no judgement calls beyond
what the records prescribed: the reorder follows the Recommendation exactly
(no rationale comment, since not required), and the comment adopts the
siblings' wording byte-for-byte. The one subtlety a later pass must keep is
the before/after framing the Performance record states: the probe
characterizes the two conjunct orders absolutely, so both reruns reproduce the
same pair and only the static Proof asserts which order the file uses — the
delta is not measured off the file. Digests: before `c5a27421` equals the
record's (same bytes); after-probe `508a77eb` is baseline+reorder; parity
`a5e0fd4e` adds the Comments hunk. The `prove` mutants (`if False:` /
`if True:`) are the failability evidence for the parity gate, not reverts.
Open threads: none. Cross-axis: none (Mechanics no-findings; Comments F1
touches no behavior).
