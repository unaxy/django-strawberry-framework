# Review: `django_strawberry_framework/list_field.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - resolver closures execute once per request per list field; validation at import/finalize

## Implementation (Worker-2)

Pass 1. Performance and Mechanics closed no-findings; Comments carried 6
Medium + 4 Low, all prose-only. Implemented the 6 Mediums plus the one Low
riding a Medium-touched file; deferred 3 Lows per the Severity ride rule.

Attribution (before any edit): `git diff <ITEM_BASELINE> --` on
`django_strawberry_framework/list_field.py` and
`examples/fakeshop/test_query/test_library_api.py` was empty (live tree
equals the item baseline; reviewer fingerprints reproduced: `450e87cd`,
`2cd1b6dd`). `git diff HEAD --` on the target shows only the recorded
concurrent truth-helper migration (+68/-126), and on the test file only
added tests (+158); both predate ITEM_BASELINE and are named on the run-3
Drift line covering each file. `## Owned changes` holds no row for either
path, and this item has no earlier pass. No foreign hunk; nothing stopped.
All concurrent hunks preserved byte-for-byte.

### Dispositions

- Performance: no findings (looks-for discharged 1-13; R1-R6 rejected with
  triggers) — nothing to implement.
- Mechanics: no findings (R1-R17 rejected with triggers) — nothing to
  implement.
- Comments Mediums, all `implemented` (record's text-after, rewrapped to
  the 99-col layout except M4, noted below):
  - M1 `_validate_djangotype_target` docstring (spent "any future node
    field" framing): now names the three live sharers (list, connection,
    Relay node fields via `_validate_relay_djangotype_target`).
  - M2 factory-site async-commitment comment (bare `Decision 3` plus wrong
    `spec-020 Decision 1`): now `spec-020 Decision 3; spec-020 Decision 2`
    (asymmetry paragraph sits under Decision 2; same-subject Decision 3 is
    spec-020's).
  - M3 `_APPROVED_ORDER_AGGREGATES` comment (false `Count` emission claim):
    emission claim scoped to Min/Max; `Count` admitted for what a consumer
    ordering may annotate.
  - M4 `DjangoListField` ordering contract (false `DISTINCT` contrast
    implication about connection fields): implemented with one wording
    change from the text-after, recorded here — the reviewer's after
    retains the substring the Proof keys on (`nor ``DISTINCT``` contains
    `or ``DISTINCT```), which would leave the Proof at `1` instead of the
    governed `0` (same trap as connection.py F2-Comments). Landed `flat
    lists inject no tiebreaker and no ``DISTINCT```, true on both halves
    as the bodies prove; the Proof now prints `0`.
  - M5 live Manager-coercion docstring (phantom `_post_process_consumer_sync`
    entry): now names the live `prepared_resolver_source` entry both `_wrap`
    colorings call.
  - M6 live nullable-outer docstring (phantom package companion test pin):
    companion clause dropped; the live test stands as the only pin.
- Comments Lows:
  - L1 `_handle_non_queryset_rejections_async` docstring (bare `Decision 8`):
    `implemented` — rides `list_field.py`, changed for M1-M4 above.
  - L2 `tests/test_list_field.py` validation banner (bare `Decision 5`):
    `deferred` — Low whose file no higher finding in this item changes.
  - L3 `tests/base/test_init.py` export pins (card/version-cut provenance):
    `deferred` — same reason.
  - L4 `test_list_field_api.py` parity-oracle block (`legacy`/`pre-card`/card
    vocabulary + test-local identifier renames): `deferred` — same reason,
    and its vocabulary mirrors in-flight spec-050 DoD 17/22, so it may
    belong at the spec's close rather than mid-flight (record Handoff).
- Routed leads: none new. The record's `utils/directives.py` census route
  and the `optimizer/extension.py` + `tests/base/test_init.py` observations
  are already on their items' `Routed:` lines.

### Files changed and why

- `django_strawberry_framework/list_field.py` — 5 prose hunks (M1-M4, L1):
  two docstring sentences, one docstring opening, two comment blocks. The
  only package file.
- `examples/fakeshop/test_query/test_library_api.py` — 2 docstring hunks
  (M5, M6) in live prose about the target's pipeline. The deferred-Low
  files are untouched. No permanent test is owed: prose-only findings owe
  steps 2 and 6 and the inverse proof alone (worker-2 step 3.7).
- No module first line changed, so no TREE.md render is owed
  (`build_tree_md.py --list-docstrings` on both paths: 2 modules, 0
  breaking).

### Before/after numbers

None owed: prose-only change. Inverse proof instead (exit 0, two equal
digests each):

- `uv run python scripts/review_inspect.py --code-digest
  8d5cb7ac968f96f5123ad24c3eb2e72c7249b897:django_strawberry_framework/list_field.py
  django_strawberry_framework/list_field.py` → both
  `sha256:95fb1b0d9d05ce013be06fbfbbf712a09a8cc52642e8ba878b5d83e7b014fc68`.
- `uv run python scripts/review_inspect.py --code-digest
  8d5cb7ac968f96f5123ad24c3eb2e72c7249b897:examples/fakeshop/test_query/test_library_api.py
  examples/fakeshop/test_query/test_library_api.py` → both
  `sha256:43b8fbed999ed6705137d3b1531bccdf360a756f91dc78858333ccec9a99dc1a`.

No workspace run (no `before`/`after` measurement exists for prose); no
run ids. No bench figure moves.

### Permanent tests

None (prose-only). No focused pytest run; AGENTS.md bars test runs
otherwise.

### Proof greps

Implemented Proofs (each prints `0`): `and any future`, `Decision 3;
spec-020 Decision 1`, `and a row count orders by`, `or ``DISTINCT```,
`^    Decision 8 promises` — all `0` in
`django_strawberry_framework/list_field.py`; `_post_process_consumer_sync`
and `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`
— both `0` in `examples/fakeshop/test_query/test_library_api.py`. Deferred
Proofs (still at their today counts): `# Validation tests (Decision 5)`
`1` in `tests/test_list_field.py`; `card 050 lands` / `version cut adds`
`2` in `tests/base/test_init.py`; `legacy` / `pre-card` / `the card` `36`
in `examples/fakeshop/test_query/test_list_field_api.py`.

### Failability proofs

None owed (no gate relies on a prose finding).

### Formatter result

On both touched paths (named explicitly): `uv run ruff check --fix` →
All checks passed; `uv run python scripts/check_trailing_commas.py` → 2
files, 0 violations; `uv run ruff format` → 2 files left unchanged. Verify
pass: `ruff check`, `ruff format --check`, `check_trailing_commas.py
--check` all pass, and `check_citations.py --check` passes on the whole
tree (1299 citations resolve). No rewrites; the digests above were taken
after the final text and the linters changed nothing.

### Scratch paths and run ids

- `docs/review/temp-tests/list_field/implement/` (created; holds no probe —
  prose-only pass owes no manifest, probe, or workspace run).
- No `review/list_field.py/implement` workspace runs; no run ids. Reviewer
  scratch under `docs/review/temp-tests/list_field/{performance,mechanics,
  comments}/` read only where the records cite it, otherwise untouched.

### Fingerprints (`git hash-object`; live tree at write time)

Touched, before -> after: `django_strawberry_framework/list_field.py`
`450e87cde13edc1bfc3c4d4a161c5540d1ac5277` ->
`6a1dba1af04428d4fc67864c2beb1af755fc387c`;
`examples/fakeshop/test_query/test_library_api.py`
`2cd1b6dd1a2f3f9a5261ff9a4509611633fa3f20` ->
`4acc4821d8adb23b2de8a743d351f94567932c14`.

Read unchanged (8-char; equal to the records' Trace): `relay.py`
`e75e2b66`, `connection.py` `1fca6266`, `orders/sets.py` `60859f2d`,
`tests/test_list_field.py` `d78aa5e7`, `tests/base/test_init.py`
`239648ed`, `test_list_field_api.py` `4c85f779`, spec-020 `9fdf09b1`,
spec-050 `73fe1127`. Read beyond the records: `filters/base.py`
`3b1dcbce` (M4 `.distinct()` census). Review inputs: `AGENTS.md`
`6475a8cf`, `START.md` `983d16a2`, `docs/review/REVIEW.md` `47ff82f1`,
`docs/review/worker-2.md` `b44e01da`, `docs/review/review-0_0_15.md`
`c0b19c37`, this artifact `fffef6aa` (pre-section),
`rev-list_field.performance.md` `122571cb`, `.mechanics.md` `1a72beb1`,
`.comments.md` `a3ccbf82`.

Item-scoped diff check: `git diff <ITEM_BASELINE> --` the two touched
paths shows exactly the 7 hunks above (14+/13-); the two other paths in
the unfiltered ITEM stat (`docs/dry/dry-0_0_15.md`,
`docs/review/review-0_0_15.md`) are Worker-0/other-flow bookkeeping,
untouched by this pass.

### Proposed owned changes

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/list_field.py` | list_field.py | Comments | `_validate_djangotype_target` docstring (live sharers); `DjangoListField` factory comment (spec-020 Decision pointers); `_APPROVED_ORDER_AGGREGATES` comment (`Count` admission); `DjangoListField` docstring (tiebreaker-only contrast); `_handle_non_queryset_rejections_async` docstring (spec-050 Decision 8 anchor) |
| `examples/fakeshop/test_query/test_library_api.py` | list_field.py | Comments | `test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http` docstring (live coercion entry); `test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves` docstring (phantom companion dropped) |

Handoff: pass 1 is a pure Comments prose pass — 5 prose hunks on the
target plus 2 on the live test file, digest-identical code, 3 Lows
deferred by the ride rule with their Proofs still printing 1/2/36. One
judgment call, recorded above: M4 drops `neither/nor` for `no/and` so its
Proof prints the governed `0` (the reviewer's after carries the keyed
substring). The verifier grades the landed docstrings whole against the
record's text-afters and re-runs the two `--code-digest` identities plus
the 10 Proof greps. Open for Worker-0: L2/L3/L4 stay visible in
`## Outcomes` (L4 may belong at spec-050's close). Nothing disputed,
blocked, or stopped; no missing fixture; no bench delta.

## Iterations

### Implement pass 2

Answers the Comments `revision-needed` gap V1 (Low) plus gap G1
(offered by the Comments verifier for pass 2). Pass 1 stands
otherwise (Performance verified, Mechanics verified, all implemented
prose graded true); nothing below relitigates it.

Attribution (before the first edit): `git diff <ITEM_BASELINE> --`
the two pass-1 paths hashes
`e2855a5e71b34f320a52ca37c38f857678573c5071bdcada3f96d37451ed98bf`,
byte-identical to
`docs/review/temp-tests/list_field/diff/pass-1.diff`, and both
`git hash-object` values equalled the pass-1 after-values
(`6a1dba1a`, `4acc4821`): the tree carried exactly pass 1 over the
item baseline, no drift. `git diff HEAD --` the same paths is
240+/139-, exactly the concurrent HEAD-to-ITEM_BASELINE work
(226+/126-: the run-3 Drift truth-helper migration on the target and
the added tests on the live file) plus the pass-1 14+/13-. Hunk
count is 30 HEAD vs 24 concurrent + 7 pass-1: the one merge is the
M2 factory-comment hunk adjacent to concurrent factory changes
(`@@ -1593,16 +1539,15 @@`); the other 6 pass-1 hunks stand alone.
`## Owned changes` holds no row for either path, and no other path
is touched. No foreign hunk; nothing stopped. All concurrent hunks
preserved byte-for-byte.

### Dispositions

- V1 (Comments verify 1, Low: stale `README.md #"Coverage rule"`
  pinpoint in the M5 docstring): `implemented` -- re-pinned per the
  record's text-after to `#"Live-first, both verdicts"`, kept on one
  source line (98 chars). The pinpoint resolves: the live
  `Live-first, both verdicts, and the must-not` paragraph is README
  line 42.
- G1 (Comments verify gap, the M3 twin in
  `_is_deterministic_order_term`): `implemented` -- the docstring's
  `one of the aggregates the shipped surface emits` is fixed the way
  M3 was fixed: emission scoped to ``Min`` / ``Max``, ``Count``
  admitted for what a consumer ordering may annotate.
- Performance, Mechanics: no findings, both verified -- nothing to
  implement. Pass-1 Comments dispositions stand (M1-M6 + L1
  implemented, L2-L4 deferred).

### Files changed and why

- `examples/fakeshop/test_query/test_library_api.py` -- 1 prose line
  (V1 re-pin inside the M5 docstring; merges into the pass-1 M5
  hunk).
- `django_strawberry_framework/list_field.py` -- 1 prose hunk, +3/-2
  (G1 docstring in `_is_deterministic_order_term`). The only package
  file.
- No module first line changed, so no TREE.md render is owed
  (`build_tree_md.py --list-docstrings` on both paths: 2 modules, 0
  breaking). No permanent test is owed: prose-only findings owe
  steps 2 and 6 and the inverse proof alone (worker-2 step 3.7).

### Before/after numbers

None owed: prose-only change. Inverse proof instead (exit 0, two
equal digests each, reproducing the pass-1 values):

- `uv run python scripts/review_inspect.py --code-digest
  8d5cb7ac968f96f5123ad24c3eb2e72c7249b897:django_strawberry_framework/list_field.py
  django_strawberry_framework/list_field.py` → both
  `sha256:95fb1b0d9d05ce013be06fbfbbf712a09a8cc52642e8ba878b5d83e7b014fc68`.
- `uv run python scripts/review_inspect.py --code-digest
  8d5cb7ac968f96f5123ad24c3eb2e72c7249b897:examples/fakeshop/test_query/test_library_api.py
  examples/fakeshop/test_query/test_library_api.py` → both
  `sha256:43b8fbed999ed6705137d3b1531bccdf360a756f91dc78858333ccec9a99dc1a`.

No workspace run (no `before`/`after` measurement exists for prose);
no run ids. No bench figure moves.

### Permanent tests

None (prose-only). No focused pytest run; AGENTS.md bars test runs
otherwise.

### Proof greps

Pass-2 Proofs (each prints `0`): `README.md #"Coverage rule"` in
`examples/fakeshop/test_query/test_library_api.py` (V1; 1 before
this pass); `aggregates the shipped surface` in
`django_strawberry_framework/list_field.py` (G1; 1 before this
pass). Pass-1 Proofs re-run unchanged: all 7 implemented still `0`
in their files; deferred still `1` / `2` / `36`.

### Failability proofs

None owed (no gate relies on a prose finding).

### Formatter result

On both touched paths (named explicitly): `uv run ruff check --fix`
→ All checks passed; `uv run python
scripts/check_trailing_commas.py` → 2 files, 0 violations; `uv run
ruff format` → 2 files left unchanged. Verify pass: `ruff check`,
`ruff format --check`, `check_trailing_commas.py --check` all pass,
and `check_citations.py --check` passes on the whole tree (1299
citations resolve). `--paths ... --substrings` on the live test
file now reports 19 citations / 0 violations (was 1: the V1
pinpoint, now resolving); the target holds 7 / 0. No rewrites; the
digests above were taken after the final text and the linters
changed nothing.

### Scratch paths and run ids

- `docs/review/temp-tests/list_field/implement/` (pre-existing,
  empty; holds no probe -- prose-only pass owes no manifest, probe,
  or workspace run).
- No `review/list_field.py/implement` workspace runs; no run ids.
  The before copy `review/list_field.py/before` was not opened
  (nothing executable owed). Reviewer and verifier scratch under
  `docs/review/temp-tests/list_field/` read only where cited,
  otherwise untouched.

### Fingerprints (`git hash-object`; live tree at write time)

Touched, before -> after: `django_strawberry_framework/list_field.py`
`6a1dba1af04428d4fc67864c2beb1af755fc387c` ->
`f5b0183e290322952fd2dad1f76ab9b2de9736ba`;
`examples/fakeshop/test_query/test_library_api.py`
`4acc4821d8adb23b2de8a743d351f94567932c14` ->
`26dd0abb537df74f06fe864bd0e3c22634307541`.

Read unchanged (8-char): this artifact `94cfd23d` (pre-section;
differs from the verify-time `42fc4e72` -- untracked file, no history
to diff, but the full 183-line read holds only the skeleton plus the
pass-1 section, so nothing foreign), `.performance.md` `98645808`,
`.mechanics.md` `0f3543b4` (both equal their verify-time values),
`.comments.md` `748d4cbc` (includes its Verification section;
pre-section was `a3ccbf82`), `review-0_0_15.md` `5b3ae591`,
`worker-2.md` `b44e01da`, `pass-1.diff` `a0b67d71`, test_query
`README.md` `0dbf3a35` (equal to the Trace value).

Item-scoped diff check: `git diff <ITEM_BASELINE> --` the two touched
paths shows 8 hunks (18+/16-): the 7 pass-1 regions (V1 merged into
the M5 hunk) plus the new G1 hunk; the two other paths in the
unfiltered ITEM stat (`docs/dry/dry-0_0_15.md`,
`docs/review/review-0_0_15.md`) are Worker-0/other-flow bookkeeping,
untouched by this pass.

### Proposed owned changes

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/list_field.py` | list_field.py | Comments | `_is_deterministic_order_term` docstring (`Count` admission; M3 twin) |
| `examples/fakeshop/test_query/test_library_api.py` | list_field.py | Comments | `test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http` docstring (README re-pin to the live rule) |

Handoff: pass 2 is a two-hunk Comments prose re-pass -- the V1
README re-pin plus the G1 `Count`-admission twin fix, digest-identical
code, pass-1 proofs all re-confirmed (7 at `0`, deferred at 1/2/36).
The verifier re-runs the two `--code-digest` identities plus the ten
record Proofs and the two new Proofs (`README.md #"Coverage rule"`
and `aggregates the shipped surface`, both `0`), and grades the two
landed units whole. Open for Worker-0: the delta ledger rows above
amend pass 1's two proposed rows (same paths, new symbols); L2/L3/L4
stay visible in `## Outcomes`; G2 (`test_products_api.py:4710`)
stays unowned by this item. Nothing disputed, blocked, or stopped;
no missing fixture; no bench delta.
