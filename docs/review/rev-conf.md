# Review: `django_strawberry_framework/conf.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - Settings.__getattr__ + user_settings run once per request (body-cap reader) and once per single-parent-spec fetch evaluation

## Implementation (Worker-2)

Implement pass 1. Axis order Performance -> Mechanics -> Comments. Baselines:
CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831,
ITEM_BASELINE=0ec338aef4e12fe5930ce0839d10d93ec3403c6d.

Attribution (Baseline and ownership): before editing, both dirty paths were
diffed against `git show HEAD:<path>`. Every HEAD-vs-live hunk is the
run-3 Drift-documented concurrent truth-migration (message rendering through
`utils/truth.py`, hostile-iteration containment replaced by documented
propagation, docstrings and `tests/base/test_conf.py` rows updated with it),
acknowledged on the plan item's own `Item baseline run 3:` line and reviewed
live per the dispatch. The item baseline captured that dirty tree: live
conf.py blob `ae3de0a3` and live test_conf.py blob `55b333eb` both equalled
their ITEM_BASELINE blobs, and `git diff ITEM_BASELINE -- <both paths>` was
empty before the first edit, so no external hunk arrived after dispatch. The
item diff after this pass holds only the 11 hunks below (10 in conf.py, 1 in
test_conf.py); the full item diff
also names `docs/dry/dry-0_0_15.md` and `docs/review/review-0_0_15.md`,
concurrent work in files this pass never touched.

### Performance: no findings, nothing applied

The record is `Status: no-findings` (R1-R4 rejected with triggers). No code,
no test, no bench figure moves. Its R1 live-read stance concurs with
Mechanics F1's Must-not-change (verbatim pass-through preserved).

### Mechanics F1 (Low): implemented

Six thin readers declared narrow return types their `getattr` bodies do not
ensure. All six annotations widened to `-> Any`, matching the two honest
siblings; no validation or coercion added, per the record. The relay widening
orphaned the file's only `Callable` use, so the import narrowed to
`from collections.abc import Mapping` (else ruff F401); that import hunk is
part of the Mechanics code change and is included in the Comments
reconstruction below.

Static Proof (shared tree, no run id by construction):
`grep -cE "def (...six readers...)() -> Any:"` prints `0` on the
ITEM_BASELINE blob and `6` on the live file. Behavior Proof: the committed
single-parent toggle oracle plus the new row below pass together (focused
run, 2 passed).

Must-not-change holds: the toggle oracle, the default/override sweep, and
the delattr-defaults sweep pass unchanged (full module, 56 passed).

### Comments F1-F3 (Medium): implemented; F4 (Low): deferred

F1 (`UPSTREAM_PATCH_DEPENDENCIES` comment): the overclaim `A package view is
unaffected by every state of this setting` rescoped to the strict UTF-8 wire
contract with the body-envelope-guard exception named, both halves named;
the joint-ownership first half and the `views.py::_RawBodyRequestAdapter`
citation kept intact on one line. Proof `grep -c` prints `1` before, `0`
after.
F2 (`Settings.__getattr__` comment): the wrong `@property`-avoids-recursion
reason replaced with the real mechanism (descriptor read, one guarded
`AttributeError` re-entry, `ConfigurationError` straight out); no
ConfigurationError-causes-lookup claim in any form. Proof `grep -c` prints
`1` before, `0` after.
F3 (`_normalize_user_settings` docstring): the sharer inventory now names all
four writers and attributes the signal path to `_reload_from_django` with its
keeps-backing note. Proof `grep -c` prints `1` before, `0` after.
All three texts-after match the record sentences modulo line wrapping.

F4 (Low, `test_transport_api.py` module docstring cardinality): deferred per
the Severity ride rule. No higher finding touches that file: this pass edits
conf.py and test_conf.py only, and the file's live blob `6d65274f` still
equals the Comments record's Trace fingerprint. Its Proof still prints `1`.

Inverse prose-only proofs (shared tree): the reconstruction
`docs/review/temp-tests/conf/implement/reconstruction/conf.py` is the
ITEM_BASELINE text plus exactly the 7 Mechanics code hunks (each replacement
asserted to match exactly once at build time); `diff` reconstruction-vs-live
shows only the three prose hunks above, and
`review_inspect.py --code-digest <reconstruction> <live>` prints two equal
digests (`sha256:9dd8dac3...`, exit 0).

### Files changed and why

- `django_strawberry_framework/conf.py`: the 7 Mechanics code hunks (6
  annotations + the orphaned `Callable` import) and the 3 Comments prose
  hunks. All findings live here; no owner move.
- `tests/base/test_conf.py`: one new row,
  `test_setting_reader_helpers_return_wrong_typed_values_verbatim`, pinning
  verbatim pass-through for the five readers the suite did not pin
  (nested=5, endpoint=None, hide-flat=1, relay=5, body-cap="1024", mirroring
  the Mechanics probe values); placed beside the single-parent verbatim
  oracle it complements. Package tier is the mandated tier: thin-reader
  Python return values are unreachable from a real query (the module's own
  docstring draws that line; the single-parent sibling sets the precedent).
  No missing fixture.
- No TREE.md change: no module first line changed. No other file touched.

### Before / after numbers

No timing or query-count numbers: Performance has no findings and the change
is annotations plus prose, so no bench figure moves. The before/after pairs
are the static Proof counts above (Mechanics 0 -> 6; Comments F1/F2/F3
1 -> 0 each), measured on the ITEM_BASELINE blob vs the live file.

### Permanent tests and focused results (shared tree, `--no-cov`)

- `tests/base/test_conf.py::test_setting_reader_helpers_return_wrong_typed_values_verbatim`
  + `::test_single_parent_fast_path_setting_is_an_unvalidated_toggle`: 2 passed.
- Full `tests/base/test_conf.py`: 56 passed (55 pre-existing + 1 new), covering
  every Must-not-change oracle.

### Failability proofs

`uv run python scripts/workspace.py prove review/conf.py/implement
docs/review/temp-tests/conf/implement/failability-manifest.json`:
run `review-20260929T000559-4b795e`, exit 0. Five entries, one per newly
pinned reader, each coercing that reader's body (`str()` on four, `int()` on
the body-cap since `str("1024")` would still equal); each mutant fails
exactly the declared new row (`pinned: the 1 failing row(s) are exactly the
declared expect_failing`), baselines green, restores byte-proved
(conf.py blob before/after `3820c575`, the post-edit blob). Cells sharded/pg
inapplicable by construction (pure in-memory settings reads; all three axis
records concur). A first attempt, run `review-20260929T000109-54439d`,
exited 1 on manifest JSON syntax (unescaped quotes) before any mutation and
is superseded, not evidence.

### Formatter and lint result

Named paths only, in gate order, all green:
`ruff check --fix` (All checks passed), `check_trailing_commas.py`
(0 violations), `ruff format` (2 files left unchanged); check-mode re-runs
(`ruff check`, `ruff format --check`, `check_trailing_commas.py --check`)
pass; `check_citations.py --check` on the whole tree: 1297 citations
resolve.

### Scratch paths and run ids

- `docs/review/temp-tests/conf/implement/failability-manifest.json` (5-entry
  manifest; the JSON record sits at the prove run's evidence path).
- `docs/review/temp-tests/conf/implement/reconstruction/conf.py`
  (ITEM_BASELINE + 7 Mechanics code hunks; inverse-digest source).
- Run ids: `review-20260929T000559-4b795e` (prove, exit 0);
  `review-20260929T000109-54439d` (prove attempt, exit 1, superseded).
  Static grep/digest/test commands ran in the shared tree and carry no run id.

### Fingerprints (`git hash-object`, post-edit)

`django_strawberry_framework/conf.py`
`3820c575bfd4e3c384244d1bed460b75d3bb7681`;
`tests/base/test_conf.py`
`7275af6887559055b90f4d83a088abfcd6c0ff5f`;
`examples/fakeshop/test_query/test_transport_api.py`
`6d65274f9e7b5589d60777d7e0484b3ad10df394` (grepped for the F4 deferral check,
not edited); reconstruction
`ef7f2f9e692d7cde8991765371e1557e5f307514`; manifest
`8d189cbe164ba87ed2e7192830be19c1b4c87636`. Read, in order: AGENTS.md
`6475a8cfb64fab5371372c19d512560840bc116f`, START.md
`983d16a2f3d6ed8ca2ee6ff998570a2d864cdc41`, REVIEW.md
`47ff82f1d52b1cac05403622b2a5ed1ec60ed1e0`, worker-2.md
`b44e01dabc84e8e31e80528152270b3d0defc173`, review-0_0_15.md
`e21bd4e6423d27c158516b424758cd1df371b052` (differs from ITEM_BASELINE by
concurrent work in files this pass never touched; read at pass start),
rev-conf.md `32e07277`
(pre-section), rev-conf.performance.md `750a9080`, rev-conf.mechanics.md
`968e26d6`, rev-conf.comments.md `dee8785d`, conf.py `ae3de0a3`
(pre-edit), test_conf.py `55b333eb` (pre-edit), prove_failability.py
docstring `27ba5402`.

### Proposed owned changes

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/conf.py` | conf.py | Mechanics, Comments | `nested_connection_strategy_setting`, `single_parent_fast_path_setting`, `testing_endpoint_setting`, `hide_flat_filters_setting`, `relay_globalid_strategy_setting`, `max_request_body_bytes_setting` (annotations `-> Any`); `Callable` import removed; `UPSTREAM_PATCH_DEPENDENCIES` comment (F1); `Settings.__getattr__` comment (F2); `_normalize_user_settings` docstring (F3) |
| `tests/base/test_conf.py` | conf.py | Mechanics | `test_setting_reader_helpers_return_wrong_typed_values_verbatim` (new) |

Handoff: Pass 1 is complete: Performance no-findings (nothing applied),
Mechanics F1 implemented with its new row, Comments F1-F3 implemented
prose-only (digest identity vs the Mechanics reconstruction), F4 deferred
with its file untouched. Beyond the records' traces I read only the lint
gate outputs and the prove JSON verdicts; no new mechanism was probed and no
dispute arose. Two threads for the verifiers: (1) the `Callable` import
removal rides inside the Mechanics code hunks and the reconstruction, so the
Mechanics verifier's revert-attack must carry all 7 hunks, not just the 6
annotations; (2) the whole-tree `check_citations.py --check` passed, but the
F1 comment's rewrap moved the `views.py::_RawBodyRequestAdapter` citation to
a new line, so a line-pinned citer elsewhere would have rotted silently --
none exists (16/16 resolve in the target). Open for Worker-0: the F4
deferral stands unless a later item touches `test_transport_api.py`.
