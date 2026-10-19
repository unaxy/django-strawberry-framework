# Review: `django_strawberry_framework/exceptions.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: cold - every executable line beyond class definition runs only on the exceptional path (raise sites) or at import

## Implementation (Worker-2)

Pass 1. All findings in this item are prose-only (Performance no-findings;
Mechanics no in-axis findings; Mechanics cross-axis C1-C3 plus Comments 2
Medium + 2 Low, every one a docstring finding). Each owes steps 2 and 6 plus
the inverse `--code-digest` proof alone: no before/after numbers, no
permanent test, no failability. No bench figure moves (cold path, prose-only
diff). No `workspace.py` runs were made, so no run ids exist; every command
below is a static shared-tree command, re-runnable as written.

Attribution (step 2): both touched paths were dirty vs HEAD and clean vs
ITEM_BASELINE (`git diff c78eb5f1 -- <both paths>` empty before the first
edit; live blobs equalled every record's fingerprints). The HEAD-vs-live
diff on `django_strawberry_framework/exceptions.py` is exactly the
Worker-0-acknowledged concurrent truth migration the Mechanics record
inventories: module-docstring rewrite, deletion of the seven `_safe_*`
helpers plus `describe_value`, deletion of the base `__str__`/`__repr__`
guards, addition of `_model_label`/`_terminal_label` on `truth` with four
function-level `from .utils import truth` imports, and the two constructors
plus two `__reduce__` methods rebuilt on `truth`. The
`tests/test_exceptions.py` HEAD-vs-live diff is the same migration's test
side (module-docstring rewrite, hostile-arg/`_safe_*` suites replaced).
Every hunk matched that migration; no unmatched hunk, no stop. The
item-scoped diff after this pass (`git diff c78eb5f1 -- <both paths>`,
reproduced in shape under "Files changed") holds only the six prose hunks
below.

### Performance

No findings in the record. Nothing to implement. Disposition: n/a (0/0/0).

### Mechanics (in-axis)

No in-axis findings in the record. Nothing to implement. Disposition: n/a.

### Mechanics cross-axis (for Comments), implemented with the Comments axis

- C1 Medium (`OptimizerError` "Raise sites:" omits `_reverse_order_by`):
  implemented, once, jointly with Comments Low L1 (same bullet, same Proof,
  different severities; both Proofs govern). Landed one bullet after the
  reversed-keyset bullet (L1's placement, keeping the two backward-window
  bullets adjacent) with C1's direct attribution to the raise site (the
  `raise` statement lives in `_reverse_order_by` itself):
  `- Backward-window order reversal:
  ``optimizer/plans.py::_reverse_order_by`` rejects an order entry with
  neither a ``descending`` flag nor a callable ``desc()``, since a backward
  (``last``-only) window cannot be expressed for it.` Single-backtick
  spellings from the record normalized to the file's double-backtick RST
  convention. Proof: `grep -c "_reverse_order_by"
  django_strawberry_framework/exceptions.py` prints `1` (was `0`).
- C2 Medium (`PathResolutionError` enumeration omits the guard/conversion
  arms): implemented as the record's text-after (the header-scoping
  alternative would fail the Proof line, which governs). Added the guard-arms
  bullet naming the non-`str` `field_path` guard and the
  ``utils/relations.py::relation_bool`` malformed-metadata conversion;
  verified against `classify_path` (6 raise statements; guards at
  `relations.py:294-295` and `:306-309`) and `relation_bool` (whose own
  docstring calls a non-`bool` "malformed metadata"). Proof: `grep -c
  "relation_bool" django_strawberry_framework/exceptions.py` prints `1`
  (was `0`). Note: Comments R2 rejected this same candidate from the other
  side (omission acceptable); landing true bullets does not violate that
  rejection, which forbids nothing, and the Medium with an unmet Proof
  governs implementation. The Comments verifier grades the landed text.
- C3 Medium (`LookupValidationError` enumeration omits the guard/conversion
  arms): implemented as the record's text-after, same reasoning as C2.
  Added the guard-arms bullet naming the non-`str` `lookup_expr` guard and
  the `FieldError` conversion; verified against `validate_lookup_expr` (6
  raise statements; guards at `relations.py:383-384` and `:409-412`, the
  `e.g.` clause matching the inline comment there). Proof: `grep -c
  "FieldError" django_strawberry_framework/exceptions.py` prints `1` (was
  `0`).

### Comments

- M1 Medium (`PathResolutionError` "swallows resolution failure and answers
  ``False``"): implemented verbatim as the record's text-after, reflowed to
  the line length. Verified against `_traverses_to_many` (`except
  PathResolutionError: return _lenient_traverses_to_many(...)`) and
  `_lenient_traverses_to_many` (returns `True` the instant a many-side hop
  precedes the failure). Proof: `grep -c "swallows resolution failure and
  answers" django_strawberry_framework/exceptions.py` prints `0` (was `1`).
- M2 Medium (`tests/test_exceptions.py::test_empty_args_render_empty_string`
  "never hits the placeholder path"): implemented verbatim as the record's
  text-after. The base render overrides are deleted (confirmed in the HEAD
  diff above), so the clause named a deleted mechanism. Proof: `grep -c
  "never hits the placeholder path" tests/test_exceptions.py` prints `0`
  (was `1`).
- L1 Low (`OptimizerError` eighth site + `a fall back` typo): implemented
  jointly with C1 (see above); the same touch fixes `a fall back` to `a
  fallback` in the window-partition bullet. Proof: `grep -c "_reverse_order_by"
  ...` prints `1` and `grep -c "a fall back to per-parent" ...` prints `0`
  (was `1`). Ride rule: rides on the C1 Medium in the same docstring.
- L2 Low (`PathResolutionError` "so a lenient caller cannot silently
  downgrade it"): implemented verbatim as the record's text-after ("so the
  failure is actionable", aligning the twins). Proof: `grep -c "cannot
  silently downgrade" django_strawberry_framework/exceptions.py` prints `0`
  (was `1`). Ride rule: rides on the M1 Medium in the same docstring.

No finding disputed, discharged, or deferred. Deferred count: 0 (both Lows
ride on Mediums in their files).

Files changed and why:

- `django_strawberry_framework/exceptions.py` — the five target-docstring
  hunks (M1 paragraph, C2 bullet, L2 sentence, C3 bullet, C1/L1 bullet plus
  the `fallback` fix). Owner of all seven prose findings; no code touched.
- `tests/test_exceptions.py` — the M2 test-docstring hunk. Owner of the
  stale test clause; no code touched.

Before/after numbers: none owed (prose-only). The Proof counts above are
the before/after, taken in the shared tree without run ids.

Permanent tests: none owed (prose-only). No pytest run.

Failability proofs: none owed (prose-only). Inverse proofs instead, both
exit 0 with equal digest pairs:

- `uv run python scripts/review_inspect.py --code-digest
  c78eb5f150bcd2a5f448a135e078ef58a5594cf4:django_strawberry_framework/exceptions.py
  django_strawberry_framework/exceptions.py` ->
  `sha256:2c01d2206db9375350a3187b100dfb2564f59b80ca9d97280f434ab7ab8b8d10`
  both sides.
- `uv run python scripts/review_inspect.py --code-digest
  c78eb5f150bcd2a5f448a135e078ef58a5594cf4:tests/test_exceptions.py
  tests/test_exceptions.py` ->
  `sha256:bdbf204b881d7adc1058be55d7cae89094d389a7a87130e72faab40cfc4714c5`
  both sides.

Formatter result: `uv run ruff check --fix <both paths>` (0 fixed), `uv run
python scripts/check_trailing_commas.py <both paths>` (0 violations), `uv
run ruff format <both paths>` (unchanged); then `ruff check`, `ruff format
--check`, and `check_trailing_commas.py --check` all pass on both paths,
and `uv run python scripts/check_citations.py --check` passes on the whole
tree (`OK: 1299 citations resolve`). Spot check: `--paths
django_strawberry_framework/exceptions.py --substrings --json` reports 10
citations (was 8), 0 violations — the two new cites
(`optimizer/plans.py::_reverse_order_by`,
`utils/relations.py::relation_bool`) resolve. No module first line changed,
so no TREE.md render owed.

Scratch paths and run ids: `docs/review/temp-tests/exceptions/implement/`
(created; holds no files — every instrument here is a static shared-tree
command). No workspace addresses used, no run ids.

Fingerprints (`git hash-object`, after this pass):

- `django_strawberry_framework/exceptions.py` 93401220b5e2c528a421481721f0e2ac460aa0bd (touched)
- `tests/test_exceptions.py` 1374fef552bcc5c34c47d921a6db2f1f9c7ae07f (touched)
- `django_strawberry_framework/utils/relations.py` 05ff55b098382a4a7aafe5a097c3b5e906f8f985 (read; unchanged vs all three records)
- `django_strawberry_framework/optimizer/plans.py` 33140a766cd3fb2484a40fe499d466c8ced8b4a6 (read; unchanged vs all three records)
- `django_strawberry_framework/utils/truth.py` d5c96bc8d191d3fce0a20140d8e91063bb466ec9 (read; unchanged vs all three records)

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/exceptions.py` | exceptions.py | Comments | `PathResolutionError` docstring (M1 paragraph, C2 bullet, L2 sentence); `LookupValidationError` docstring (C3 bullet); `OptimizerError` docstring (C1/L1 bullet, `fallback` fix) |
| `tests/test_exceptions.py` | exceptions.py | Comments | `test_empty_args_render_empty_string` docstring (M2) |

Handoff: Pass 1 is prose-complete: 7 findings implemented across 2 files, 0
disputed/discharged/deferred, every Proof green, both inverse digests exit
0, lint and citation gates green. Judgment calls the verifiers may revisit:
(1) the C1/L1 hybrid (L1's head and placement, C1's direct `_reverse_order_by`
attribution, RST double-backticks) — both Proofs constrain only the grep
counts plus the true grade, so any true wording with one `_reverse_order_by`
holds; (2) implementing C2/C3 text-after over Comments R2's omission-is-fine
rejection — R2 permits omission but the Medium Proofs demand the bullets,
and added true bullets cannot grade stale; the Comments verifier judges the
landed text, not the choice. Beyond the records I read `classify_path`,
`validate_lookup_expr`, `relation_bool`, `_traverses_to_many`,
`_lenient_traverses_to_many`, `path_traverses_to_many`, and
`_reverse_order_by` bodies whole to verify every landed clause. Open
threads: none. No defects found; no pre-existing failure encountered (no
pytest run — none owed).

## Defects

None fixed and none encountered in this item (prose-only change; no pytest
run, none owed).
