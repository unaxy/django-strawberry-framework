# REVIEW plan: 0.0.15

Status: in-progress
Mode: autonomous
Run: 0.0.15 2026-09-24-1
Scope: utils/strings.py

Method: `docs/review/REVIEW.md`. Fresh source review; findings from prior build, review, DRY or
hunt artifacts are not imported.

## Cycle baseline

`git status --short` at generation. Every path below is concurrent work: never edited, reverted,
tidied, or attributed to an item. Worker-0 appends the `CYCLE_BASELINE` stash object once at
start and nothing afterwards; drift goes on `Drift:` lines under the run heading.

```text
?? output/
```

CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 (`git stash create` empty; `git rev-parse HEAD`)
Untracked under django_strawberry_framework/: none

## Bench baseline

Each figure is bound by the package digest and instrument ids in its provenance
header; `CYCLE_BASELINE` is recorded beside it, and each run's workspace run id
(REVIEW.md "Workspace"). `<scratch>` is the absolute session scratchpad, `<phase>`
either `baseline` or `gate`, each its own copy. The nested-fetch row runs in that
copy's own Postgres database (REVIEW.md "Database cells").
Worker-0 fills Baseline at cycle entry, Gate and Delta at the final gate.

Gate: package digest `sha256:ffacb6907783cf474a9cb1c59e2c3aa0582979e08adcef97a54ba7ae42b08dcb` (the item's change), every instrument blob id identical to the baseline's, copy `review/bench/gate` synced after the item closed.
Baseline: package digest `sha256:df761b8225865985fd218f13f3288212bb3e0a5cf4ec546ec28f926d9b9f3130`, `_bench_common.py` blob 253a3953, `CYCLE_BASELINE` 6ac69870, copy `review/bench/baseline` synced 2026-09-25T03:32:07Z; python 3.14.2, django 6.1, strawberry-graphql 0.324.0.

| Command | Baseline | Gate | Delta |
|---|---|---|---|
| `uv run python scripts/workspace.py run review/bench/<phase> -- python scripts/bench_plan_cache.py --json <scratch>/bench/<phase>/plan_cache.json` | `review-20260925T033208-815a5f`; warm/cold us median: glossary scalar 710.8/790.5, nested 4062.6/4371.5, deep 6835.6/7457.0, products scalar 1204.9/1296.2, products nested (non-cacheable) 1840.7/1861.5; instrument `bench_plan_cache.py` blob 1d6203ad | `review-20260925T042312-b835a5`; warm/cold us median: glossary scalar 715.8/781.5, nested 4034.4/4290.3, deep 6920.8/7335.4, products scalar 1221.5/1316.0, products nested 1756.9/1856.0 | warm within spread on every row (+0.7%, -0.7%, +1.2%, +1.4%, -4.6%); no figure moves |
| `uv run python scripts/workspace.py run review/bench/<phase> -- python scripts/bench_optimizer_walk.py --json <scratch>/bench/<phase>/optimizer_walk.json` | `review-20260925T033406-a529d7`; min/median us: glossary scalar 5.25/5.50, nested 75.92/81.33, deep 145.92/154.33, products connection 4.50/4.71; instrument blob de745175 | `review-20260925T042505-43a836`; min/median us: glossary scalar 5.21/5.42, nested 76.12/82.00, deep 141.38/149.33, products connection 4.42/4.58 | medians -1.5%, +0.8%, -3.2%, -2.8%, inside run spread; plan shapes identical |
| `uv run python scripts/workspace.py run review/bench/<phase> --cell pg -- python scripts/bench_nested_fetch.py --json <scratch>/bench/<phase>/nested_fetch.json` | `review-20260925T033421-9c27d5`; pg 16.15, median ms count-free windowed 19.40 / lateral 17.51 / per-parent 68.41; totalCount 18.98 / 19.31 / 99.78; queries 2/2/101 and 2/2/201; instrument blob d7f8c39e | `review-20260925T042517-f3e320`; median ms count-free windowed 19.06 / lateral 17.52 / per-parent 66.93; totalCount 19.02 / 18.41 / 97.77; queries 2/2/101 and 2/2/201 | query counts identical; timings within spread |
| `uv run python scripts/workspace.py run review/bench/<phase> -- python scripts/importtime_report.py --rounds 5 --json <scratch>/bench/<phase>/importtime.json` | `review-20260925T033429-12e0bd`; package cumulative 177.4 ms, self 22.4 ms over 67 modules; instrument blob bfce84b9 | `review-20260925T042524-088936`; package cumulative 175.4 ms, self 22.1 ms over 67 modules | -2.0 ms cumulative, same module count; noise |

Gate, run 0.0.15 2026-09-25-2: package digest `sha256:181e02bcfb9a8ec93b85171b380acaf58a7988f625cbc5abfd5212add0a0b9ed` (this run's item plus the walker and fixture changes beside it), copy `review/bench/gate-2` synced after the item closed; `bench_plan_cache.py`, `bench_optimizer_walk.py`, `bench_nested_fetch.py`, `_bench_common.py` blobs identical to the baseline's; `importtime_report.py` blob 15f679c9 (changed in 4cc95b77), so its row compares nothing.

| Command (`<phase>` = `gate-2`) | Gate run 2 | Delta vs baseline |
|---|---|---|
| `bench_plan_cache.py` row | `review-20260925T174759-fef1f7`; warm/cold us median: glossary scalar 716.6/789.0, nested 4085.8/4355.2, deep 6908.1/7442.4, products scalar 1220.2/1317.1, products nested 1763.7/1859.4 | warm +0.8%, +0.6%, +1.1%, +1.3%, -4.2%: within spread, as at gate 1 |
| `bench_optimizer_walk.py` row | `review-20260925T174954-ec78d4`; min/median us: glossary scalar 5.29/5.58, nested 77.00/83.67, deep 141.00/151.88, products connection 4.42/4.62; plan shapes identical | medians +1.5%, +2.9%, -1.6%, -1.9%; nested +2.0% vs gate 1 is cross-session drift: the walker change measured interleaved before/after on the same copy pair gave nested 85.79 -> 84.33 us |
| `bench_nested_fetch.py` row (`--cell pg`) | `review-20260925T175006-70e564`; median ms count-free windowed 19.30 / lateral 17.49 / per-parent 65.33; totalCount 19.01 / 19.51 / 99.65; queries 2/2/101 and 2/2/201 | query counts identical; timings within spread |
| `importtime_report.py` row | `review-20260925T175014-d0ee46`; package cumulative 179.8 ms, self 22.6 ms over 67 modules | instrument id differs from the baseline's: compares nothing |

connection.py (run 0.0.15 2026-09-28-3): `bench_nested_fetch.py --cell pg` directional pair (Worker-2 before `review-20260929T010927-049ab0` / after `review-20260929T011305-20cfca`, instrument d7f8c39e both sides): windowed count-free 50.53 -> 33.04 ms (-34.6%), totalCount 44.92 -> 34.23 (-23.8%); lateral count-free 52.11 -> 27.62, totalCount 43.70 -> 32.60; queries identical (2/2/101 and 2/2/201). Verifier corroborating pair (before `review-20260929T015121-a54cc9` / after `review-20260929T015147-103e6c`): windowed count-free 20.76 -> 15.46 (-25.5%), lateral 21.78 -> 15.35 (-29.5%), totalCount 25.65 -> 16.59 / 20.83 -> 15.69; per-parent drift bound ~+9%. Directional only (neither pair interleaves; cross-session medians compare nothing); attributable numbers are the probe medians (F1 ~97us -> sub-us memo hit; F2 30 -> 0 constructions; F3 30 -> 0 calls).

## How to work one item

`docs/review/REVIEW.md` is the method; this section only points into it.

- Roles and dispatch order: "Roles", "Cycle per file item".
- Per-axis looks-for list, instrument and record fields: "The three axes", "Severity".
- Evidence and measurement: "Ground rules", "Workspace".
- Dirty paths, item baselines, ledger rows: "Baseline and ownership".
- Artifact shapes and names: "Artifacts".
- Folder and project items: "Integration passes"; the gate: "Final gate and closeout".
- Plan drift before the first dispatch and before the gate:
  `uv run python scripts/review_plan.py reconcile --plan <this plan>`.

## utils/

- [x] utils/strings.py
    - Status: verified
    - Result run 3: 0 findings implemented (0/0/0: all three axes no-findings on re-review), rejections stand (Performance 1 new cold-branch R1 + 5 carried; Mechanics R1-R6; Comments F8 deferred carried), 0 deferred new. Files: none (Implement pass 3 landed zero paths; run-1 ledger rows stand).
    - Verification run 3: Passed. Performance pass 2 (hot re-affirmed; exact-str delta 0.2 ns noise; strings 85 us self, zero child cost; no bench figure moves); Mechanics pass 2 (M1 intact, twin divergence + str-siblings rejected, numbers reproduced); Comments pass 3 (prose true, routed leads to utils/inputs.py + utils/ folder + owning items).
    - Cleanup run 3: Removed docs/review/temp-tests/utils__strings; copies released; unrelated work preserved.
    - Reopened: 2026-09-28 - utils/strings.py, optimizer/field_meta.py, types/base.py, types/finalizer.py, types/relations.py, optimizer/walker.py, management/commands/inspect_django_type.py, types/resolvers.py, optimizer/extension.py, optimizer/nested_planner.py, types/definition.py, tests/optimizer/test_extension.py, tests/optimizer/test_walker.py, tests/types/test_finalizer.py, tests/types/test_relay_interfaces.py, tests/utils/test_strings.py
    - Item baseline run 3: e79425515bb25b376f330ac50d46d9615b9aad19 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/utils/strings.py dirty w/ concurrent work)
    - Item baseline: 6ac698704402240b954f95072bed4639354ab831 (`git stash create` empty; HEAD); untracked under the package: none; dirty: none
    - Path class: hot - the optimizer walker calls `snake_case` once per selection on every plan build (plan-cache miss, every non-cacheable request); every other helper runs at declaration, finalize or behind an upstream memo
    - Artifacts: rev-utils__strings.md, rev-utils__strings.performance.md, rev-utils__strings.mechanics.md, rev-utils__strings.comments.md
    - Result: 12 findings implemented (1/5/6: M1 High; F1-F4, F9 Medium; L1, F5-F7, F10, F11 Low), 19 rejected with triggers (Performance 5; Mechanics 5 + 2 Comments cross-axis leads; Comments 7 + its looks-for discharges; each record's `## Rejected` / `## Cross-axis`), 1 deferred (F8 Low, `tests/utils/test_strings.py` provenance). Files: the 13 `## Owned changes` rows for this item.
    - Verification: Passed. Performance pass 1 (L1 `_plain_text` delta 0.6 ns <= 2.0 ns, parity ok; no bench figure moves); Mechanics pass 1 (M1 two package-tier nodes, prove pins exactly them, attacks async / connection / SKIP / inspect); Comments pass 2 (F1-F7, F9-F11 landed; prose-only re-pass proven by stripped-AST identity).
    - Cleanup: Removed docs/review/temp-tests/utils__strings; copies released; unrelated work preserved.

## Final gate

- [ ] Final gate
    - Status: pending
    - Run 0.0.15 2026-09-25-2: `gate-review-20260925T174743-8d66b3.json`, bound to `git stash create` a92a7fcee0f63d8cef957e48856a0ff5dbb1542d. lint `review-20260925T174040-4992e9` exit 0 (the nine `django.yml` lint commands); default `review-20260925T174056-b47518` exit 0, 8863 passed, 40 skipped, coverage 100%; sharded `review-20260925T174303-038b7a` exit 0, 8884 passed, 37 skipped; pg `review-20260925T174501-47dd81` exit 0, 2346 passed, 3 skipped. No `## Pending execution` commands. Inventory re-reconciled: `reconcile` exit 0.
    - Runs: `uv run python scripts/workspace.py gate review` (default, `FAKESHOP_SHARDED=1` and Postgres suites in a gate copy that keeps a git index, REVIEW.md "Final gate and closeout"), each w/ its own counts; every `## Pending execution` command from every artifact; the `## Bench baseline` commands at `<phase>` `gate`, delta recorded
    - Result: `gate-review-20260925T042258-72d2fd.json`, bound to `git stash create` 49456066d336cbedbedaeab24ab842d1b33752ee. default `review-20260925T041601-4e904e` exit 0, 8854 passed, 40 skipped, package coverage 100.00% (18636 statements); sharded `review-20260925T041812-70749d` exit 0, 8875 passed, 37 skipped; pg `review-20260925T042013-26eea0` exit 0, 2342 passed, 3 skipped. No `## Pending execution` commands (none recorded). Bench gate rows filled; no figure moves.
    - Inventory re-reconciled before the gate: `reconcile` exit 0.

## Out of scope this run

Not examined under `Scope: utils/strings.py`; an unticked box here is not a pending
review of this run. A later run moves an item into its scope under its own `## Run` heading.

- [ ] _boundary_ordering.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_boundary_ordering.md, rev-_boundary_ordering.performance.md, rev-_boundary_ordering.mechanics.md, rev-_boundary_ordering.comments.md
- [ ] _cross_web_patches.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_cross_web_patches.md, rev-_cross_web_patches.performance.md, rev-_cross_web_patches.mechanics.md, rev-_cross_web_patches.comments.md
- [x] _django_patches.py
    - Status: verified
    - Result: 7 findings implemented (0/5/2: F1-F5 Medium, L1-L2 Low), rejections stand (Performance R1-R5; Mechanics R1-R10; Comments R1-R14), 0 deferred. Files: django_strawberry_framework/_django_patches.py, tests/test_django_patches.py, tests/testing/test_wrap.py (prose-only, +18/-16).
    - Verification: Passed. Performance pass 1 (cold; no number moves on a prose-only diff); Mechanics pass 1 (behavior preserved by code-digest identity; lint gates green); Comments pass 1 (all 7 Proofs print 0; landed docstrings grade true; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/_django_patches; copies released; unrelated work preserved.
    - Path class: cold - every executable line runs at process start (import/ready()), test-class teardown, or consumer test setup; nothing per request, resolver, row, connection or outbound message
    - Item baseline run 3: 8482f9a925f3c073013b20e7ef783e9dc5c1ac3e (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/_django_patches.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-_django_patches.md, rev-_django_patches.performance.md, rev-_django_patches.mechanics.md, rev-_django_patches.comments.md
- [x] _graphql_core_patches.py
    - Status: verified
    - Result: 2 findings implemented (0/1/1: F1 Medium Comments, F1 Low Performance riding the same file), rejections stand (Performance R1-R6; Mechanics R1-R7; Comments per record), 0 deferred. Files: django_strawberry_framework/_graphql_core_patches.py (2 hunks: guard reorder + pragma wording).
    - Verification: Passed. Performance pass 1 (118 ns reorder reproduced before/after; 10 + 78 pin nodes pass; failability mutants fail exactly their nodes); Mechanics pass 1 (trigger set preserved; lint gates green); Comments pass 1 (Proof prints 0; pragma wording true; code-digest identity vs reconstruction).
    - Cleanup: Removed docs/review/temp-tests/_graphql_core_patches; copies released; unrelated work preserved.
    - Path class: hot - runs once per list-field completion on every executed operation (sync and async) while installed
    - Item baseline run 3: e4385002efab0df029451349a7738a02e19928e2 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/_graphql_core_patches.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-_graphql_core_patches.md, rev-_graphql_core_patches.performance.md, rev-_graphql_core_patches.mechanics.md, rev-_graphql_core_patches.comments.md
- [ ] _request_body.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-_request_body.md, rev-_request_body.performance.md, rev-_request_body.mechanics.md, rev-_request_body.comments.md
- [x] _strawberry_patches.py
    - Status: verified
    - Result: 16 findings implemented (0/10/6: F1-F10 Medium, L1-L6 Low), rejections stand (Performance R1-R6; Mechanics R1-R15; Comments R1-R25), 0 deferred. Files: target + tests/test_strawberry_patches.py + tests/test_views.py + 2 live-tier files (prose-only, +36/-29).
    - Verification: Passed. Performance pass 1 (hot; prose-only diff moves no number); Mechanics pass 1 (code-digest identity on all 5 files; lint gates green); Comments pass 1 (16/16 Proofs print 0; landed docstrings grade true incl. F5/F10 judgment calls; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/_strawberry_patches; copies released; unrelated work preserved.
    - Path class: hot - the installed wrappers run once per request body, query-param or multipart parse on every operation served by the installed Strawberry (sync and async)
    - Item baseline run 3: f3d32be142a493b44bf522d75471843f2fc86285 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/_strawberry_patches.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-_strawberry_patches.md, rev-_strawberry_patches.performance.md, rev-_strawberry_patches.mechanics.md, rev-_strawberry_patches.comments.md
- [x] apps.py
    - Status: verified
    - Result: 2 findings implemented (0/1/1: Medium dispatch-test masking paragraph + riding Low spec-Decision anchors), 2 deferred (Low class-mood + Low conjunction, apps.py touched by no higher finding), rejections stand. Files: tests/test_apps.py (2 hunks; target untouched).
    - Verification: Passed. Performance pass 1 (cold; test-only diff moves no number); Mechanics pass 1 (literals single-consumer, suite still 14 passed; lint green; deferrals correctly applied); Comments pass 1 (2/2 implemented Proofs print 0; deferred Proofs correctly still print 1; landed text true; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/apps; copies released; unrelated work preserved.
    - Path class: cold - every executable line runs at process start (app-loader ready()); nothing per request, resolver, row, connection or outbound message
    - Item baseline run 3: d4ff8d5067f177b771ba3870240d266cdc285f86 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/apps.py clean vs HEAD)
    - Path class:
    - Artifacts: rev-apps.md, rev-apps.performance.md, rev-apps.mechanics.md, rev-apps.comments.md
- [x] conf.py
    - Status: verified
    - Result: 4 findings implemented (0/3/1: F1-F3 Medium Comments, F1 Low Mechanics riding the same file), 1 deferred (Low F4 switch cardinality, file untouched by any higher finding), rejections stand. Files: django_strawberry_framework/conf.py (7 code + 3 prose hunks) + tests/base/test_conf.py (1 new row).
    - Verification: Passed. Performance pass 1 (hot class; annotation+prose diff moves no number); Mechanics pass 1 (6 -> Any + import; verbatim oracle + new row pass; 5 prove mutants fail exactly their rows; lint green); Comments pass 1 (F1-F3 Proofs print 0, F4 still 1; landed prose true; digest identity vs reconstruction).
    - Cleanup: Removed docs/review/temp-tests/conf; copies released; unrelated work preserved.
    - Path class: hot - Settings.__getattr__ + user_settings run once per request (body-cap reader) and once per single-parent-spec fetch evaluation
    - Item baseline run 3: 0ec338aef4e12fe5930ce0839d10d93ec3403c6d (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/conf.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-conf.md, rev-conf.performance.md, rev-conf.mechanics.md, rev-conf.comments.md
- [x] connection.py
    - Status: verified
    - Result: 16 findings implemented (2/8/6: H1 + V1 High, 3 Performance + 5 Comments Mediums, C1 hoist + L1-L5 Lows), 6 deferred (L6-L11 Lows, files untouched by any higher finding), rejections stand; V1 (async closure) was verify-found in pass 1 and fixed in pass 2. Files: django_strawberry_framework/connection.py + tests/test_relay_connection.py (F2 counter) + examples/fakeshop/test_query/test_keyset_api.py (H1 live test).
    - Verification: Passed. Performance pass 1 (F1 375ns < 5000, F2 0 constructions, F3 0 calls, 7 pins; bench directional corroborated); Mechanics pass 1 (H1 live 1 + compat 2+4, failability exact) then revision-needed on V1, pass 2 verified (V1 node + second async node + H1 rows green; lint green); Comments pass 1 (10/10 implemented Proofs 0, 6/6 deferred still 1, C1 anchored greps + 2 nodes; prose true).
    - Cleanup: Removed docs/review/temp-tests/connection; copies released; unrelated work preserved.
    - Path class: hot - the resolve path runs per connection field per request and per parent row for nested connections; the factory/cache path is cold
    - Item baseline run 3: e6b022ba44f4e14da9e1825cea7047aa38d03298 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/connection.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-connection.md, rev-connection.performance.md, rev-connection.mechanics.md, rev-connection.comments.md
- [x] consumers.py
    - Status: verified
    - Result: 11 findings implemented (0/2/9: Medium module enumeration + C2, 8 Comments Lows + C1), 0 deferred (all Lows ride), rejections stand. Files: django_strawberry_framework/consumers.py (9 prose hunks) + tests/test_routers.py (3 prose hunks).
    - Verification: Passed. Performance pass 1 (hot; prose-only diff moves no number); Mechanics pass 1 (digest identity; lint green); Comments pass 1 (13/13 Proofs hold; landed prose true incl. judgment calls; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/consumers; copies released; unrelated work preserved.
    - Path class: hot - admission runs once per operation (revalidate_operation_actor), the outbound checkpoint once per outbound frame
    - Item baseline run 3: cf28b509ad848b9219ef23444c4e99cbd19c1fb8 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/consumers.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-consumers.md, rev-consumers.performance.md, rev-consumers.mechanics.md, rev-consumers.comments.md
- [x] error_policy.py
    - Status: verified
    - Result: 11 findings implemented (0/5/6, all test prose; target grades true throughout), 0 deferred, rejections stand. Files: tests/test_error_policy.py (5 hunks incl. M1 rename) + examples/fakeshop/test_query/test_error_policy_api.py (6 hunks incl. M4 assertion); target untouched.
    - Verification: Passed. Performance pass 1 (cold; test-only diff moves no number); Mechanics pass 1 (rename collection-neutral, assert holds on 12 sites, suites 66+74 green; lint green); Comments pass 1 (11/11 Proofs hold incl. disjunctive M4; landed prose true; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/error_policy; copies released; unrelated work preserved.
    - Path class: cold - resolution/validation at schema construction and import; new_correlation_id once per masked error on the exceptional path only
    - Item baseline run 3: 59dad4a566f3718e6d99572ef853455d0aabc101 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/error_policy.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-error_policy.md, rev-error_policy.performance.md, rev-error_policy.mechanics.md, rev-error_policy.comments.md
- [x] exceptions.py
    - Status: verified
    - Result: 7 findings implemented (0/5/2: C1-C3 + M1-M2 Mediums, L1-L2 Lows riding; C1/L1 once jointly), 0 deferred, rejections stand. Files: django_strawberry_framework/exceptions.py (5 docstring hunks) + tests/test_exceptions.py (M2 hunk).
    - Verification: Passed. Performance pass 1 (cold; prose-only diff moves no number); Mechanics pass 1 (digest identity; lint green); Comments pass 1 (8/8 Proof counts hold; landed docstrings true; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/exceptions; copies released; unrelated work preserved.
    - Path class: cold - every executable line beyond class definition runs only on the exceptional path (raise sites) or at import
    - Item baseline run 3: c78eb5f150bcd2a5f448a135e078ef58a5594cf4 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/exceptions.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-exceptions.md, rev-exceptions.performance.md, rev-exceptions.mechanics.md, rev-exceptions.comments.md
- [x] keyset.py
    - Status: verified
    - Result: 5 findings implemented (0/4/1: M1-M4 Mediums + riding L1), 3 deferred (L2-L4 Lows, files untouched by any higher finding), rejections stand. Files: django_strawberry_framework/keyset.py (5 docstring hunks).
    - Verification: Passed. Performance pass 1 (hot; prose-only diff moves no number); Mechanics pass 1 (digest identity; lint green); Comments pass 1 (5/5 implemented Proofs 0, 3/3 deferred still 1; landed docstrings true; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/keyset; copies released; unrelated work preserved.
    - Path class: hot - the mint path runs per edge per row; decode/seek run per request per supplied cursor
    - Item baseline run 3: d6f1f0a4c4d291b03cf14e680ab3649aeda10851 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/keyset.py dirty w/ concurrent work)
    - Path class:
    - Artifacts: rev-keyset.md, rev-keyset.performance.md, rev-keyset.mechanics.md, rev-keyset.comments.md
- [x] list_field.py
    - Status: verified
    - Result: 9 findings implemented (0/6/3: M1-M6 Mediums, riding L1, verify-found V1 + gap G1 in pass 2), 3 deferred (L2-L4 Lows, files untouched by any higher finding), rejections stand. Files: django_strawberry_framework/list_field.py (6 prose hunks) + examples/fakeshop/test_query/test_library_api.py (2 prose hunks).
    - Verification: Passed. Performance pass 1 (hot; prose-only diff moves no number); Mechanics pass 1 (digest identity; lint green); Comments pass 1 (10/10 Proofs hold; landed prose true) then revision-needed on V1, pass 2 verified (V1 + G1 Proofs 0; re-pins resolve; no provenance/line-refs/we).
    - Cleanup: Removed docs/review/temp-tests/list_field; copies released; unrelated work preserved.
    - Path class: hot - resolver closures execute once per request per list field; validation at import/finalize
    - Item baseline run 3: 8d5cb7ac968f96f5123ad24c3eb2e72c7249b897 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/list_field.py dirty w/ concurrent work)
    - Routed: from connection.py Comments: list_field.py::_validate_djangotype_target "Shared by DjangoListField and DjangoConnectionField (and any future node field)" - node fields exist and share it today, future framing spent
    - Path class:
    - Artifacts: rev-list_field.md, rev-list_field.performance.md, rev-list_field.mechanics.md, rev-list_field.comments.md
- [x] permissions.py
    - Status: verified
    - Result: 9 findings implemented (0/4/5: Perf F1 Medium + riding F2 Low; Comments M1-M3 + riding L1-L4, incl. 3 new package-tier pins), 0 deferred, rejections stand. Files: django_strawberry_framework/permissions.py (6c97d887) + tests/test_permissions.py (c113d05e).
    - Verification: Passed. Performance pass 1 (hot; F1 2->1 `.filter` calls, F2 3->0 naming calls; SQL-identity + zero-round-trip pins green; B0 before/after medians); Mechanics pass 1 (no-findings stands; own module 75 passed 1 skipped + live cascade pins; R1/R2 fence + R15 routing intact); Comments pass 1 (7/7 Proofs 0; re-grades true). Deviation: first Mechanics verify returned pool-blocked revision-needed (4/4 bound: Worker-0 had not released the finished review copies); copies released, a followup retry landed in a restricted session, fresh re-dispatch verified.
    - Cleanup: Removed docs/review/temp-tests/permissions; copies released; unrelated work preserved.
    - Item baseline run 3: 623c43216c5c50961b3dc0f5448ae6d21926ece1 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/permissions.py dirty w/ concurrent work + tests/test_permissions.py dirty, both byte-stable at baseline per review fingerprints ef66f8b9/c22af728)
    - Path class: hot (root call once per resolver per request on every cascaded type; walk body once per forward edge)
    - Path class:
    - Artifacts: rev-permissions.md, rev-permissions.performance.md, rev-permissions.mechanics.md, rev-permissions.comments.md
- [x] registry.py
    - Status: verified
    - Result: 11 findings implemented (0/6/5: Comments F1-F6 Medium + riding F7-F10 Low; Mechanics L1 Low riding the same test file), 1 deferred (F11 Low, tests/orders/test_inputs.py untouched by any higher finding), rejections stand. Files: django_strawberry_framework/registry.py (27358cbc, prose-only) + tests/test_registry.py (8bd9a869, L1 rows + prose) + tests/orders/test_composition.py (9414d257, F6) + docs/SPECS/spec-018-meta_primary-0_0_6.md (9f7c3784, F10 sweep).
    - Verification: Passed. Performance pass 1 (hot-read/cold-mutator; no-findings stands; code-digest identity sha256:3949c414 both sides; no bench row moves); Mechanics pass 1 (L1 node 1 passed; both failability mutants fail; zero production change; R1-R6 stand); Comments pass 1 (10/10 Proofs hold incl. F9 pinpoint-ok after a Worker-0 one-token Proof-filter correction prescribed by the verifier; landed prose true). Notes: check_citations over the records flags only the frozen F10 Symbol cite of the renamed test (expected frozen-text citation, precedent); F10's dry-rule prose reference deliberately unswept (DRY flow's untracked file) - see Decisions.
    - Cleanup: Removed docs/review/temp-tests/registry; copies released; unrelated work preserved.
    - Item baseline run 3: da5c1882de6a2330b1ce41878b78c073ef5a36b4 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/registry.py dirty w/ concurrent work; tests/test_registry.py + tests/orders/test_composition.py clean; tests/orders/test_inputs.py dirty — F11 deferred, untouched)
    - Path class: hot - get/model_for_type/get_definition per resolver/plan-edge/filter-application; definition_for_graphql_name per type-name GlobalID decode; mutators cold
    - Routed: from connection.py Comments: tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule docstring describes an except-ImportError guard with cycle-safe local import in clear() (spec-030 P3b) but no such guard survives (clear() replays iter_subsystem_clears callbacks); order/relay twin tests may share the staleness
    - Path class:
    - Artifacts: rev-registry.md, rev-registry.performance.md, rev-registry.mechanics.md, rev-registry.comments.md
- [x] relay.py
    - Status: verified
    - Result: 13 findings implemented (0/3/10: Perf F1 Medium + riding F2/F3 Low; Perf C1 Medium prose; Mech L1 Low + C1 Medium + C2 Low prose; Comments F1-F6 Low), 0 deferred, rejections stand. Files: django_strawberry_framework/relay.py (f5760b45: _decode_and_coerce + _resolve_real_pks_batched new, slot threading, F2 guards, L1 hoist, C1/C2/F1/F2 prose) + utils/write_values.py (13548c76: F1 batched set decode, C1 reword) + tests/test_relay_node_field.py (d4ce0c7d: F2/F3 pins + F3-F6 prose) + tests/utils/test_write_values.py (9f459e2f: 2 F1 pins).
    - Verification: Passed. Performance pass 1 (hot; F1 exactly 2 queries at K=1/2/4 + 1-query no-row leg, failability on per-id revert; F2 zero owner names + SyncMisuseError rows green; F3 once-per-type + coercion rows green; R1-R11 stand); Mechanics pass 1 (L1 hoisted, 3 import orders green, recovery nodes pass; single-source decode preserved, twins in step, new function-local relay import whitelisted-shape; R1-R12 stand); Comments pass 1 (9/9 prose Proofs hold; landed docstrings true against the new bodies; F5+F6 pair landed). Deviation: first Mechanics verify BLOCKED (slot-4 venv corrupt, no verdict, no record); Worker-0 released the broken copy + the finished perf copy, probed a fresh address healthy on slot-3, and re-dispatched as verify-mechanics-2, which verified. The twin pipeline-alias recovery (change-challenge count 2) is accepted per the verifier (twin structure, docstring-documented).
    - Cleanup: Removed docs/review/temp-tests/relay; copies released; unrelated work preserved.
    - Item baseline run 3: 04fd0769352ba604a1db2942738f8dab9f630b18 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/relay.py + tests/test_relay_node_field.py + utils/write_values.py + tests/utils/test_write_values.py all dirty w/ concurrent work, all byte-stable at baseline per review fingerprints e75e2b66/af4866a1/72f132f0/6feaa49e)
    - Path class: hot - read resolvers per node(s) request; write decode per input id per mutation relation
    - Routed: from connection.py Comments (observed, not graded): test_relay_connection.py temporal wordings ("no longer plans", "anymore", "USED to ... now") + bare "(Decision 5)" pointer quality; owning Comments pass judges
    - Path class:
    - Artifacts: rev-relay.md, rev-relay.performance.md, rev-relay.mechanics.md, rev-relay.comments.md
- [x] resource_policy.py
    - Status: verified
    - Result: 8 findings implemented (0/5/3: Perf F1 Medium + riding Mech L1 Low; Comments F1-F4 Medium + riding F5-F6 Low), 0 deferred, rejections stand. F5 discharges the plan's Routed lead on this item (conf.py "Probed by the hunt"). Files: django_strawberry_framework/resource_policy.py (5b4a80f0: F1 guard, L1 arm, F2/F6 prose) + tests/test_resource_policy.py (a52bfb89: F1/F3/F5 prose) + examples/fakeshop/test_query/test_resource_policy_api.py (56b70d75: F4 prose).
    - Verification: Passed. Performance pass 1 (hot; probe 63.8 ns < 150 + seam 452.8 ns < 600; 9 pins green; 19/19 truth-table identity vs baseline; R1-R5 stand, R5 routed); Mechanics pass 1 (L1 6 pins green; 51-case narrowed/deadline matrix identical new-vs-reverted; F1 guard no defect; R1-R6 stand); Comments pass 1 (6/6 Proofs hold; landed prose true; cites intact). Note: Mechanics verify open thread (1) asks for an `## Implementation (Worker-2)` section in the main artifact - judged unneeded (no item in this run carries one; ledger + pass diff complete; verifier itself: no re-pass owed).
    - Cleanup: Removed docs/review/temp-tests/resource_policy; copies released; unrelated work preserved.
    - Item baseline run 3: e3af18216bc75ecbd6bd080d78cdb1b209458e79 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/resource_policy.py + tests/test_resource_policy.py dirty w/ concurrent work, both byte-stable at baseline per fingerprints cc3f9d80/585c536e; live-tier test_resource_policy_api.py clean ae7bef60)
    - Path class: hot - check_deadline per collection field per request + per parent row on nested paths; policy_from_info per collection field; begin/end once per operation
    - Routed: from conf.py Comments (observed, not graded): "Probed by the hunt" wording in tests/test_resource_policy.py; owning Comments pass judges
    - Path class:
    - Artifacts: rev-resource_policy.md, rev-resource_policy.performance.md, rev-resource_policy.mechanics.md, rev-resource_policy.comments.md
- [x] routers.py
    - Status: verified
    - Result: 7 findings implemented (0/2/5: Comments T1-T2 Mediums + 5 riding target Lows, prose-only in django_strawberry_framework/routers.py 299da0f5), 19 deferred (18 tests/test_routers.py Lows incl. the test rename + 19-site and 3-site mood batches + the plan's Routed wordings as judged, 1 tests/auth/test_mutations.py Low; files no higher finding touches, both byte-identical f513d869/ff8a261d), rejections stand. Performance no-findings (cold), Mechanics no-findings.
    - Verification: Passed. Performance pass 1 (cold; code-digest identity sha256:38c32db5 both sides; R1-R6 stand; no per-request caller); Mechanics pass 1 (prose-only, no defect introducible; T1 reword agrees with R1; R1-R7 stand); Comments pass 1 (7/7 Proofs 0; landed sentences true vs bodies; 19 deferred files confirmed untouched). Deviation: first Comments review child failed (native run failure, no record); its inspect/ + JSON scratch kept and re-dispatched as review-routers-comments-2, which completed findings-recorded.
    - Cleanup: Removed docs/review/temp-tests/routers; copies released; unrelated work preserved.
    - Item baseline run 3: eb71162ba7be2797bf4dbdb4e7d24da989e96eed (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/routers.py dirty w/ concurrent work, byte-stable at baseline per fingerprint e18772f7; tests/test_routers.py + tests/auth/test_mutations.py untouched - 19 Lows deferred per the ride rule)
    - Path class: cold - import / class materialization / router construction, once per process; per-connection dispatch is upstream
    - Routed: from consumers.py Comments (observed, not graded; that pass grades tests/test_routers.py whole): `_ws_communicator` "now that the HTTP branch no longer carries one" / "the branch now carries two independent handshake checks"; `test_the_websocket_pattern_is_keyword_only_...` "no longer" Decision-4 quotation; `test_a_factory_that_raises_from_its_body_...` "your factory"
    - Path class:
    - Artifacts: rev-routers.md, rev-routers.performance.md, rev-routers.mechanics.md, rev-routers.comments.md
- [x] scalars.py
    - Status: verified
    - Result: 9 findings implemented (0/6/3: Perf F1+F2 Medium; Mech C1 Medium prose; Comments M1-M3 Medium + riding L1-L3 Low), 0 deferred, rejections stand. Files: django_strawberry_framework/scalars.py (9e945168: F1/F2 fast paths, C1/M1/L1/L3 prose) + tests/test_scalars.py (ab5943d6: M2/M3/L2 prose + _HostileStr coverage leg for the F2 subclass-str branch).
    - Verification: Passed. Performance pass 1 (hot; agreement ok 29x2; serialize 88.2 ns < 300, parse-int/str below thresholds; 28 + 82 + 2 pins green; R1-R5 stand); Mechanics pass 1 (46-input x 2-seam equivalence, 92/92 identical incl. messages; all witnesses reachable, no dead code; R1-R10 stand); Comments pass 1 (7/7 Proofs 0; landed prose true; M1+C1 paragraph coherent).
    - Cleanup: Removed docs/review/temp-tests/scalars; copies released; unrelated work preserved.
    - Item baseline run 3: be73a504707bc57990681fc526ad5607c1e681d1 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/scalars.py + tests/test_scalars.py dirty w/ concurrent work, both byte-stable at baseline per fingerprints 5da8c140/156b57e1)
    - Path class: hot - serialize per BigInt field per row; parse per BigInt input value; config cold
    - Path class:
    - Artifacts: rev-scalars.md, rev-scalars.performance.md, rev-scalars.mechanics.md, rev-scalars.comments.md
- [x] schema.py
    - Status: verified
    - Result: 16 findings implemented (1/9/6: Mech F1 High defect + riding C1/C2 Low prose; Comments M1-M8 Medium + riding L1-L5 Low), 0 deferred, rejections stand. Files: django_strawberry_framework/schema.py (f4e807e9: `_subscribe` override + M1/M2/M3/L1/L2/L5/C2 prose) + tests/test_schema.py (83877a6a: F1 pin + M4/L3 prose) + tests/extensions/test_operation_state.py (6ce414b6: 11 un-skips) + tests/mutations/test_write_transaction.py (96416deb: M1 twin) + test_extension_isolation_api.py (61d57bab: M5-M7) + test_mutation_atomicity.py (69d7cc4d: M8/L4).
    - Verification: Passed. Performance pass 1 (hot; ceiling-inert: resume pins + 55-row operation-state green; R1-R11 stand); Mechanics pass 1 (F1: new pin 1 passed, failability exactly on override revert, wheel audit re-derived 0.316/no-subscribe 0.317-0.319/subscribe, 11 un-skipped pass, 4 staying-skipped genuine; R1-R16 stand); Comments pass 1 (15/15 Proofs hold incl. discriminating M7 pattern; L5 adaptation accepted; landed prose true; M1 version re-corroborated vs wheels). Bounds: F1's wire exposure unproven (package router tasking unverified) - judged a floor-band subset hole, not a ceiling regression.
    - Cleanup: Removed docs/review/temp-tests/schema; copies released; unrelated work preserved.
    - Item baseline run 3: 5ef09ed4565b774a3f9cda2f473514732bf12064 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/schema.py + tests/test_schema.py + tests/extensions/test_operation_state.py + tests/mutations/test_write_transaction.py dirty w/ concurrent work, all byte-stable at baseline per fingerprints 84f2d5aa/3676f7e8/7509c1cc/689e31f4; both live-tier files clean)
    - Path class: hot - chain build + runner construction per operation; marker check per field; mutation windows per field; resume gate per streamed op
    - Path class:
    - Artifacts: rev-schema.md, rev-schema.performance.md, rev-schema.mechanics.md, rev-schema.comments.md
- [x] sets_mixins.py
    - Status: verified
    - Result: 30 findings implemented (0/14/16: Perf F1 Medium + C1 Medium prose; Mech F1 Low; Comments M1-M8/M10-M12 Medium + riding L1-L17 Low; M9 closed via Mech F1 with no prose edit), 1 deferred (L18 Low, tests/filters/test_sets.py untouched by any higher finding, byte-identical ea6d0b04), rejections stand. Files: django_strawberry_framework/sets_mixins.py (1f8e078d: memo, __all__, converged + M/L prose) + tests/test_sets_mixins.py (8c1488d7: counting pin, completeness pin, M9/M10 + L13-L16 prose) + tests/filters/test_inputs.py (4e280999: M11) + tests/orders/test_base.py (00de6531: M12). Ruling: C1/M3/M4 converged on one memo-world text (record text-afters were no-memo); family docstring twins routed, not same-changed (flow rule).
    - Verification: Passed. Performance pass 1 (hot; probe medians below 500; 3 seam nodes green; counting pin + failability on revert; R1-R10 stand); Mechanics pass 1 (__all__ complete; strengthened pin 1 passed, fails pre-fix; memo no-defect; R1-R8 stand); Comments pass 1 (all Proofs at expected counts; converged text + F1-consequential seam-test line graded true; M9 stands true; family files confirmed byte-identical).
    - Cleanup: Removed docs/review/temp-tests/sets_mixins; copies released; unrelated work preserved.
    - Item baseline run 3: 569603863d594f6296d1c27cd8d0a2e6f2f4b3a5 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/sets_mixins.py + tests/test_sets_mixins.py + tests/filters/test_inputs.py + tests/orders/test_base.py dirty w/ concurrent work, all byte-stable at baseline per fingerprints 088ddab0/23946eb5/c5422da5/16ec8284; tests/filters/test_sets.py dirty but untouched - L18 deferred per the ride rule)
    - Path class: hot - related-target seam per request per active branch; permission facade per apply; declaration/expansion/naming cold
    - Artifacts: rev-sets_mixins.md, rev-sets_mixins.performance.md, rev-sets_mixins.mechanics.md, rev-sets_mixins.comments.md
- [ ] views.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-views.md, rev-views.performance.md, rev-views.mechanics.md, rev-views.comments.md
- [x] auth/mutations.py
    - Status: verified
    - Result: 13 findings implemented (0/6/7: Mech F1 Low consolidation; Comments M1-M6 Medium + riding L1-L6 Low), 0 deferred, rejections stand. Files: django_strawberry_framework/auth/mutations.py (98ae63f1: metaclass deleted, owner reuse, M1-M4/L1 prose) + tests/auth/test_mutations.py (4cb49982: seal-test updates + M5/L2-L6 prose) + tests/auth/conftest.py (a5c413ba: M6).
    - Verification: Passed. Performance pass 1 (hot; no-findings stands; seal nodes + query-count absolutes identical; no bench row moves); Mechanics pass 1 (F1: zero refs gate, 2 seal nodes pass, migration probe VERIFY-F1-OK, auth suite 135 passed; R1-R19 stand); Comments pass 1 (12/12 Proofs hold; landed prose true; F1-grade-moot handled). Notes: check_citations over the records flags only the 3 frozen `_SealedAuthHolderMeta` cites (expected frozen-text citations, precedent); the `## Implementation (Worker-2)` open thread judged unneeded (run precedent). Deviation: Mechanics verify found the `before`-copy venv broken (slot-1 site-packages corruption: 7 missing top-level modules + corrupt psycopg); Worker-0 repaired at pool level (uv sync --reinstall + psycopg force-reinstall; seal nodes pass on before; all 4 slots probed healthy).
    - Cleanup: Removed docs/review/temp-tests/auth-mutations; copies released; unrelated work preserved.
    - Item baseline run 3: 8a53fa0958877d9c10e62631deb5b38e2096d539 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/auth/mutations.py + tests/auth/test_mutations.py + tests/auth/conftest.py dirty w/ concurrent work, all byte-stable at baseline per fingerprints 84183c89/ff8a261d/a7e8a55e)
    - Path class: hot - login/logout/register resolver bodies once per mutation per request; factories/bind cold
    - Path class:
    - Artifacts: rev-auth__mutations.md, rev-auth__mutations.performance.md, rev-auth__mutations.mechanics.md, rev-auth__mutations.comments.md
- [x] auth/queries.py
    - Status: verified
    - Result: 4 findings implemented (0/2/2: Comments F1+F2 Medium + riding L1+L2 Low), 0 deferred, rejections stand. Performance no-findings (hot), Mechanics no-findings. Files: tests/auth/test_queries.py (a57722d4: F1 first line, F2 rename + docstring, L1/L2 prose) + docs/TREE.md (5c9d6066: F1 render, exactly 2 rows). Target django_strawberry_framework/auth/queries.py byte-identical to baseline (b036bdac) — prose-only pass, no code change.
    - Verification: Passed. Performance pass 1 (target identical, digest sha256:27c0662b both sides; no bench row moves); Mechanics pass 1 (no defect introducible; rename is the only delta; render exactly 2 rows; R1-R7 stand); Comments pass 1 (4/4 Proofs hold incl. --list-docstrings; L2 paragraph graded against the final test list; landed prose true). Note: check_citations over the records flags only the 2 frozen cites of the renamed test (expected frozen-text citations, precedent).
    - Cleanup: Removed docs/review/temp-tests/auth-queries; copies released; unrelated work preserved.
    - Item baseline run 3: f26a7dff116cf2968524bab663453025006e185b (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/auth/queries.py clean, untouched by this prose-only pass; tests/auth/test_queries.py + docs/TREE.md dirty w/ concurrent work, both byte-stable at baseline per fingerprints 86fa35e3/769c2743)
    - Path class: hot - resolve body once per me field per request; factory/alias/bind cold
    - Path class:
    - Artifacts: rev-auth__queries.md, rev-auth__queries.performance.md, rev-auth__queries.mechanics.md, rev-auth__queries.comments.md
- [x] auth/sessions.py
    - Status: verified
    - Result: 9 findings implemented (0/4/5: Comments F1-F4 Medium + riding F5-F9 Low), 0 deferred, rejections stand. Performance no-findings (hot), Mechanics no-findings. File: django_strawberry_framework/auth/sessions.py (e50011e6, prose-only) — no test edits, no TREE.md render, no symbol moves.
    - Verification: Passed. Performance pass 1 (code-digest identity sha256:d54bef37 both sides; no bench row moves); Mechanics pass 1 (no defect introducible; R1-R7 stand); Comments pass 1 (9/9 Proofs 0; landed prose true vs installed channels/Django). Note: Worker-0 one-token record correction (verifier's informal `contrib/auth/__init__.py::login` shorthand tripped check_citations; reworded, citations green).
    - Cleanup: Removed docs/review/temp-tests/auth-sessions; copies released; unrelated work preserved.
    - Item baseline run 3: 5bdea138317eca79e8727c89022df017e3e73d46 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/auth/sessions.py dirty w/ concurrent work, byte-stable at baseline per fingerprint 865d6e70)
    - Path class: hot - once per login/logout mutation per request (twice on async bodies); per-mutation, never per-row
    - Path class:
    - Artifacts: rev-auth__sessions.md, rev-auth__sessions.performance.md, rev-auth__sessions.mechanics.md, rev-auth__sessions.comments.md
- [x] auth/ integration
    - Status: verified
    - Result: 0 findings implemented, 1 deferred (F1 Low, tests/auth/__init__.py census gaps — no file changes for a higher finding, byte-identical 09e0f06d), rejections stand incl. the R1 routed-lead uphold. Implement pass 1: zero paths. Performance no-findings (cold), Mechanics no-findings.
    - Verification: Passed. Performance pass 1 (zero-change 0 bytes; init 2e480818; no bench row moves); Mechanics pass 1 (no defect introducible; rejections stand); Comments pass 1 (deferral confirmed; R1 uphold agreed; F1 gaps real-but-deferred).
    - Cleanup: Removed docs/review/temp-tests/auth-integration; copies released; unrelated work preserved.
    - Item baseline run 3: 5676d4fc6310a5ff0d075771593a0f3068eb9406 (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (init file django_strawberry_framework/auth/__init__.py clean at baseline 2e480818; tests/auth/__init__.py untouched 09e0f06d — F1 deferred)
    - Path class: cold - import/finalize/bind only (per-folder-file hot seams unchanged)
    - Routed: from auth/queries.py Comments (observed, not graded): tests/auth/test_mutations.py::_request_with_store opens descriptively like the filed L1, but its file's item is verified/closed and the helper is not prose about the queries target's symbols — a folder mood sweep may take it; owning Comments pass judges
    - Init files: `auth/__init__.py`
    - Artifacts: rev-auth.md, rev-auth.performance.md, rev-auth.mechanics.md, rev-auth.comments.md
- [ ] extensions/debug.py
    - Status: implementing
    - Item baseline run 3: 2dae90d03c0749ebc2f4a512dd7668b1706b51bc (`git stash create`); untracked under the package: django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py; dirty: run-3 Drift lines (target django_strawberry_framework/extensions/debug.py dirty w/ concurrent work)
    - Path class: hot per operation when installed (both teardowns drain + collect; fail-closed gate once per op)
    - Review: Performance findings-recorded (F1/F2 Medium, R1-R11); Mechanics findings-recorded (F1 Medium defect, C1 Medium cross-axis, R1-R8, R4 -> Decisions); Comments findings-recorded (F1-F4 Medium, F5-F17 Low, R1-R8)
    - Implement scope: Perf F1 + F2 + 2 new count-pin tests; Mech F1 + gate-comment reword + 1 new gate test; Mech C1 3-site reword; Comments F1-F15. Converged text: Comments F1 text-after adopts Mech C1 wording (sync None-or-strawberry-shape, version-dependent) — the record's "sync leaves result as None" half is stale per C1. Deferred under ride rule: Comments F16 (live tier), F17 (governance) — files no higher finding touches.
    - Artifacts: rev-extensions__debug.md, rev-extensions__debug.performance.md, rev-extensions__debug.mechanics.md, rev-extensions__debug.comments.md
- [ ] extensions/error_policy.py
    - Status: pending
    - Routed: from error_policy.py Comments: extensions/error_policy.py::is_maskable_result "what the gate excludes" lists the operation-teardown seam meeting a sync parse/validation early-return, but on the installed engine the early return is ADMITTED (a strawberry ExecutionResult); same floor-model staleness as the _run_teardown finding (behavioral split 0.316.0 vs 0.324.0)
    - Path class:
    - Artifacts: rev-extensions__error_policy.md, rev-extensions__error_policy.performance.md, rev-extensions__error_policy.mechanics.md, rev-extensions__error_policy.comments.md
- [ ] extensions/operation_state.py
    - Status: pending
    - Path class:
    - Artifacts: rev-extensions__operation_state.md, rev-extensions__operation_state.performance.md, rev-extensions__operation_state.mechanics.md, rev-extensions__operation_state.comments.md
- [ ] extensions/resource_policy.py
    - Status: pending
    - Routed: from resource_policy.py Mechanics (same axis, no evidence taken beyond noting the pair): _charge_upload (`type(size) is not int or size < 0`) and _page_bound (`type(value) is int and value >= 0`) both spell exact-int plus non-negative inline with prose citations to resource_policy.py::_is_builtin_number; whether that fragment is one rule with one owner inside that module is for this item to judge
    - Path class:
    - Artifacts: rev-extensions__resource_policy.md, rev-extensions__resource_policy.performance.md, rev-extensions__resource_policy.mechanics.md, rev-extensions__resource_policy.comments.md
- [ ] extensions/ integration
    - Status: pending
    - Init files: `extensions/__init__.py`
    - Artifacts: rev-extensions.md, rev-extensions.performance.md, rev-extensions.mechanics.md, rev-extensions.comments.md
- [ ] filters/base.py
    - Status: pending
    - Routed: from sets_mixins.py Performance C1 + Comments (same root as M3; memo world now shipped): `RelatedFilter.filterset` docstring "Re-stores the resolved class so the next access is a plain attribute read" (filters/base.py:1148) — judge against the memoized `_resolved_target` (repeat reads of an identical value skip re-validation); owning Comments pass judges. Also observed: the "Target acceptance shapes" list omits the callable-factory shape (`resolve_lazy_class` accepts it; pinned by `test_related_order_accepts_callable_factory`).
    - Path class:
    - Artifacts: rev-filters__base.md, rev-filters__base.performance.md, rev-filters__base.mechanics.md, rev-filters__base.comments.md
- [ ] filters/factories.py
    - Status: pending
    - Path class:
    - Artifacts: rev-filters__factories.md, rev-filters__factories.performance.md, rev-filters__factories.mechanics.md, rev-filters__factories.comments.md
- [ ] filters/inputs.py
    - Status: pending
    - Routed: from conf.py Comments (observed, not graded): bare "Decision 11" in tests/filters/test_inputs.py; owning Comments pass judges
    - Routed: from utils/strings.py Comments run 3: "used to ... now" narrative wording in tests/filters/test_inputs.py (2 docstrings); behavioral claims graded true
    - Path class:
    - Artifacts: rev-filters__inputs.md, rev-filters__inputs.performance.md, rev-filters__inputs.mechanics.md, rev-filters__inputs.comments.md
- [ ] filters/sets.py
    - Status: pending
    - Path class:
    - Artifacts: rev-filters__sets.md, rev-filters__sets.performance.md, rev-filters__sets.mechanics.md, rev-filters__sets.comments.md
- [ ] filters/ integration
    - Status: pending
    - Init files: `filters/__init__.py` (defines `_clear_helper_referenced_filtersets`, `filter_input_type`)
    - Artifacts: rev-filters.md, rev-filters.performance.md, rev-filters.mechanics.md, rev-filters.comments.md
- [ ] forms/converter.py
    - Status: pending
    - Path class:
    - Artifacts: rev-forms__converter.md, rev-forms__converter.performance.md, rev-forms__converter.mechanics.md, rev-forms__converter.comments.md
- [ ] forms/inputs.py
    - Status: pending
    - Path class:
    - Artifacts: rev-forms__inputs.md, rev-forms__inputs.performance.md, rev-forms__inputs.mechanics.md, rev-forms__inputs.comments.md
- [ ] forms/resolvers.py
    - Status: pending
    - Path class:
    - Artifacts: rev-forms__resolvers.md, rev-forms__resolvers.performance.md, rev-forms__resolvers.mechanics.md, rev-forms__resolvers.comments.md
- [ ] forms/sets.py
    - Status: pending
    - Path class:
    - Artifacts: rev-forms__sets.md, rev-forms__sets.performance.md, rev-forms__sets.mechanics.md, rev-forms__sets.comments.md
- [ ] forms/ integration
    - Status: pending
    - Init files: `forms/__init__.py`
    - Artifacts: rev-forms.md, rev-forms.performance.md, rev-forms.mechanics.md, rev-forms.comments.md
- [ ] management/commands/_imports.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-management__commands___imports.md, rev-management__commands___imports.performance.md, rev-management__commands___imports.mechanics.md, rev-management__commands___imports.comments.md
- [ ] management/commands/export_schema.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-management__commands__export_schema.md, rev-management__commands__export_schema.performance.md, rev-management__commands__export_schema.mechanics.md, rev-management__commands__export_schema.comments.md
- [ ] management/commands/inspect_django_type.py
    - Status: pending
    - Path class:
    - Artifacts: rev-management__commands__inspect_django_type.md, rev-management__commands__inspect_django_type.performance.md, rev-management__commands__inspect_django_type.mechanics.md, rev-management__commands__inspect_django_type.comments.md
- [ ] management/commands/ integration
    - Status: pending
    - Init files: `management/commands/__init__.py`
    - Artifacts: rev-management__commands.md, rev-management__commands.performance.md, rev-management__commands.mechanics.md, rev-management__commands.comments.md
- [ ] management/ integration
    - Status: out-of-scope
    - Init files: `management/__init__.py`
    - Artifacts: rev-management.md, rev-management.performance.md, rev-management.mechanics.md, rev-management.comments.md
- [ ] middleware/debug_toolbar.py
    - Status: pending
    - Path class:
    - Artifacts: rev-middleware__debug_toolbar.md, rev-middleware__debug_toolbar.performance.md, rev-middleware__debug_toolbar.mechanics.md, rev-middleware__debug_toolbar.comments.md
- [ ] middleware/request_body.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-middleware__request_body.md, rev-middleware__request_body.performance.md, rev-middleware__request_body.mechanics.md, rev-middleware__request_body.comments.md
- [ ] middleware/ integration
    - Status: pending
    - Init files: `middleware/__init__.py`
    - Artifacts: rev-middleware.md, rev-middleware.performance.md, rev-middleware.mechanics.md, rev-middleware.comments.md
- [ ] mutations/fields.py
    - Status: pending
    - Path class:
    - Artifacts: rev-mutations__fields.md, rev-mutations__fields.performance.md, rev-mutations__fields.mechanics.md, rev-mutations__fields.comments.md
- [ ] mutations/inputs.py
    - Status: pending
    - Routed: from utils/strings.py Comments run 3: "was pinned ... now pins" narrative wording in tests/mutations/test_inputs.py; behavioral claims graded true
    - Path class:
    - Artifacts: rev-mutations__inputs.md, rev-mutations__inputs.performance.md, rev-mutations__inputs.mechanics.md, rev-mutations__inputs.comments.md
- [ ] mutations/operations.py
    - Status: pending
    - Path class:
    - Artifacts: rev-mutations__operations.md, rev-mutations__operations.performance.md, rev-mutations__operations.mechanics.md, rev-mutations__operations.comments.md
- [ ] mutations/permissions.py
    - Status: pending
    - Path class:
    - Artifacts: rev-mutations__permissions.md, rev-mutations__permissions.performance.md, rev-mutations__permissions.mechanics.md, rev-mutations__permissions.comments.md
- [ ] mutations/resolvers.py
    - Status: pending
    - Routed: from relay.py Mechanics C1 (twin): tests/mutations/test_resolvers.py:1173 `_decode_relation_id_set` docstring mention - the dead consumer name the relay item reworded at its owner; owning Comments pass judges
    - Routed: from auth/mutations.py Mechanics R14: `_run_register_pipeline_sync` builds `_build_wire_name_map` per request exactly as the model flavor's own write path does (the `skeleton` call site in `resolvers.py`); any memoization belongs to the owner — owning Performance pass judges
    - Path class:
    - Artifacts: rev-mutations__resolvers.md, rev-mutations__resolvers.performance.md, rev-mutations__resolvers.mechanics.md, rev-mutations__resolvers.comments.md
- [ ] mutations/sets.py
    - Status: pending
    - Routed: from auth/mutations.py Comments: `make_declaration_registry` docstring gives the label pair `("DjangoMutation" / "DjangoFormMutation")` and says "the two ledgers stay disjoint", omitting the auth third flavor (`"AuthMutation"` ledger) that spec-040 added; pre-existing phrasing — owning Comments pass judges
    - Path class:
    - Artifacts: rev-mutations__sets.md, rev-mutations__sets.performance.md, rev-mutations__sets.mechanics.md, rev-mutations__sets.comments.md
- [ ] mutations/ integration
    - Status: pending
    - Init files: `mutations/__init__.py`
    - Artifacts: rev-mutations.md, rev-mutations.performance.md, rev-mutations.mechanics.md, rev-mutations.comments.md
- [ ] optimizer/_context.py
    - Status: pending
    - Path class:
    - Artifacts: rev-optimizer___context.md, rev-optimizer___context.performance.md, rev-optimizer___context.mechanics.md, rev-optimizer___context.comments.md
- [ ] optimizer/extension.py
    - Status: pending
    - Routed: from list_field.py Comments (observed): tests/optimizer/test_extension.py line 1927 "(spec line 350: ...)" line-number citation to an unnamed spec in optimizer-subject prose (cache-key rule); owning Comments pass cites the decision
    - Path class:
    - Artifacts: rev-optimizer__extension.md, rev-optimizer__extension.performance.md, rev-optimizer__extension.mechanics.md, rev-optimizer__extension.comments.md
- [ ] optimizer/field_meta.py
    - Status: pending
    - Path class:
    - Artifacts: rev-optimizer__field_meta.md, rev-optimizer__field_meta.performance.md, rev-optimizer__field_meta.mechanics.md, rev-optimizer__field_meta.comments.md
- [ ] optimizer/hints.py
    - Status: pending
    - Path class:
    - Artifacts: rev-optimizer__hints.md, rev-optimizer__hints.performance.md, rev-optimizer__hints.mechanics.md, rev-optimizer__hints.comments.md
- [ ] optimizer/join_taxonomy.py
    - Status: pending
    - Path class:
    - Artifacts: rev-optimizer__join_taxonomy.md, rev-optimizer__join_taxonomy.performance.md, rev-optimizer__join_taxonomy.mechanics.md, rev-optimizer__join_taxonomy.comments.md
- [ ] optimizer/lateral_fetch.py
    - Status: pending
    - Path class:
    - Artifacts: rev-optimizer__lateral_fetch.md, rev-optimizer__lateral_fetch.performance.md, rev-optimizer__lateral_fetch.mechanics.md, rev-optimizer__lateral_fetch.comments.md
- [ ] optimizer/nested_fetch.py
    - Status: pending
    - Path class:
    - Artifacts: rev-optimizer__nested_fetch.md, rev-optimizer__nested_fetch.performance.md, rev-optimizer__nested_fetch.mechanics.md, rev-optimizer__nested_fetch.comments.md
- [ ] optimizer/nested_planner.py
    - Status: pending
    - Routed: from connection.py Comments (L2 twin): nested_planner _divergent_key_windows "the single-window scheme sends the legacy shared-to_attr request" - "legacy" mislabels the live common path
    - Routed: from keyset.py Comments (adjacent twin, same fix): nested_planner line 1165 "`None` keeps the legacy shared `to_attr`" shares the "legacy" mislabel
    - Path class:
    - Artifacts: rev-optimizer__nested_planner.md, rev-optimizer__nested_planner.performance.md, rev-optimizer__nested_planner.mechanics.md, rev-optimizer__nested_planner.comments.md
- [ ] optimizer/plans.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__plans.md, rev-optimizer__plans.performance.md, rev-optimizer__plans.mechanics.md, rev-optimizer__plans.comments.md
- [ ] optimizer/predicates.py
    - Status: pending
    - Path class:
    - Artifacts: rev-optimizer__predicates.md, rev-optimizer__predicates.performance.md, rev-optimizer__predicates.mechanics.md, rev-optimizer__predicates.comments.md
- [ ] optimizer/selections.py
    - Status: pending
    - Routed: from connection.py Comments: optimizer/selections.py::prime_selected_fields "calls this immediately after the first + last guard" - only "immediately" is false (spec-047 deadline check sits between; "ahead of both reads" still holds)
    - Path class:
    - Artifacts: rev-optimizer__selections.md, rev-optimizer__selections.performance.md, rev-optimizer__selections.mechanics.md, rev-optimizer__selections.comments.md
- [ ] optimizer/single_parent_fetch.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-optimizer__single_parent_fetch.md, rev-optimizer__single_parent_fetch.performance.md, rev-optimizer__single_parent_fetch.mechanics.md, rev-optimizer__single_parent_fetch.comments.md
- [ ] optimizer/walker.py
    - Status: pending
    - Routed: from utils/strings.py Comments run 3: "Before ... now" / "Gap 2a" / "Site 3" / "B2:" narrative wording in tests/optimizer/test_walker.py (3 docstrings, as run 1); behavioral claims graded true
    - Path class:
    - Artifacts: rev-optimizer__walker.md, rev-optimizer__walker.performance.md, rev-optimizer__walker.mechanics.md, rev-optimizer__walker.comments.md
- [ ] optimizer/ integration
    - Status: pending
    - Routed: from connection.py Comments (observed, not graded): test_glossary_api.py:211 "optimizer-folder High" twin (provenance, optimizer subject) of the test_library_api residue finding; owning Comments pass judges
    - Init files: `optimizer/__init__.py`
    - Artifacts: rev-optimizer.md, rev-optimizer.performance.md, rev-optimizer.mechanics.md, rev-optimizer.comments.md
- [ ] orders/base.py
    - Status: pending
    - Routed: from sets_mixins.py Performance C1 + Comments (same root as M3; memo world now shipped): `RelatedOrder.orderset` docstring, the same "plain attribute read" sentence (orders/base.py:135) — judge against the memoized `_resolved_target`; owning Comments pass judges. Also observed: the "Target acceptance shapes" list omits the callable-factory shape; and the module docstring "after the neutral module was extracted" (orders/base.py:10) is provenance.
    - Path class:
    - Artifacts: rev-orders__base.md, rev-orders__base.performance.md, rev-orders__base.mechanics.md, rev-orders__base.comments.md
- [ ] orders/factories.py
    - Status: pending
    - Path class:
    - Artifacts: rev-orders__factories.md, rev-orders__factories.performance.md, rev-orders__factories.mechanics.md, rev-orders__factories.comments.md
- [ ] orders/inputs.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-orders__inputs.md, rev-orders__inputs.performance.md, rev-orders__inputs.mechanics.md, rev-orders__inputs.comments.md
- [ ] orders/sets.py
    - Status: pending
    - Routed: from exceptions.py Performance: orders/sets.py::OrderSet._resolve_order_expressions calls the uncached classify_path per request per order term, six lines above the cached _path_traverses_to_many probe over the same pair - owning Performance pass should check whether the strict result can ride the cached wrapper
    - Path class:
    - Artifacts: rev-orders__sets.md, rev-orders__sets.performance.md, rev-orders__sets.mechanics.md, rev-orders__sets.comments.md
- [ ] orders/ integration
    - Status: pending
    - Init files: `orders/__init__.py` (defines `_clear_helper_referenced_ordersets`, `order_input_type`)
    - Artifacts: rev-orders.md, rev-orders.performance.md, rev-orders.mechanics.md, rev-orders.comments.md
- [ ] rest_framework/hook_context.py
    - Status: pending
    - Path class:
    - Artifacts: rev-rest_framework__hook_context.md, rev-rest_framework__hook_context.performance.md, rev-rest_framework__hook_context.mechanics.md, rev-rest_framework__hook_context.comments.md
- [ ] rest_framework/inputs.py
    - Status: pending
    - Path class:
    - Artifacts: rev-rest_framework__inputs.md, rev-rest_framework__inputs.performance.md, rev-rest_framework__inputs.mechanics.md, rev-rest_framework__inputs.comments.md
- [ ] rest_framework/resolvers.py
    - Status: pending
    - Path class:
    - Artifacts: rev-rest_framework__resolvers.md, rev-rest_framework__resolvers.performance.md, rev-rest_framework__resolvers.mechanics.md, rev-rest_framework__resolvers.comments.md
- [ ] rest_framework/serializer_converter.py
    - Status: pending
    - Path class:
    - Artifacts: rev-rest_framework__serializer_converter.md, rev-rest_framework__serializer_converter.performance.md, rev-rest_framework__serializer_converter.mechanics.md, rev-rest_framework__serializer_converter.comments.md
- [ ] rest_framework/sets.py
    - Status: pending
    - Path class:
    - Artifacts: rev-rest_framework__sets.md, rev-rest_framework__sets.performance.md, rev-rest_framework__sets.mechanics.md, rev-rest_framework__sets.comments.md
- [ ] rest_framework/ integration
    - Status: pending
    - Routed: from routers.py Mechanics + Comments (confirming, not duplicating): `rest_framework/__init__.py::require_drf` says "the three soft-dependency guards are identical thin wrappers" while four named wrappers over `require_optional_module` exist (`routers.require_channels`, `auth.sessions.require_channels`, `require_drf`, `middleware.debug_toolbar.require_debug_toolbar`, plus `keyset.py`'s two direct call sites which are not named guards); pre-existing phrasing - owning Comments pass judges whether the count means names or sites
    - Init files: `rest_framework/__init__.py` (defines `require_drf`)
    - Artifacts: rev-rest_framework.md, rev-rest_framework.performance.md, rev-rest_framework.mechanics.md, rev-rest_framework.comments.md
- [ ] testing/_wrap.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-testing___wrap.md, rev-testing___wrap.performance.md, rev-testing___wrap.mechanics.md, rev-testing___wrap.comments.md
- [ ] testing/client.py
    - Status: pending
    - Path class:
    - Artifacts: rev-testing__client.md, rev-testing__client.performance.md, rev-testing__client.mechanics.md, rev-testing__client.comments.md
- [ ] testing/relay.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-testing__relay.md, rev-testing__relay.performance.md, rev-testing__relay.mechanics.md, rev-testing__relay.comments.md
- [ ] testing/ integration
    - Status: pending
    - Init files: `testing/__init__.py`
    - Artifacts: rev-testing.md, rev-testing.performance.md, rev-testing.mechanics.md, rev-testing.comments.md
- [ ] types/base.py
    - Status: pending
    - Routed: from connection.py Comments (observed true, not graded): "for 0.0.9" dating in types/base.py (fact still true); owning Comments pass judges
    - Routed: from conf.py Comments (observed, not graded): "no longer reads" narrative wording in tests/types/test_base.py; owning Comments pass judges
    - Path class:
    - Artifacts: rev-types__base.md, rev-types__base.performance.md, rev-types__base.mechanics.md, rev-types__base.comments.md
- [ ] types/converters.py
    - Status: pending
    - Path class:
    - Artifacts: rev-types__converters.md, rev-types__converters.performance.md, rev-types__converters.mechanics.md, rev-types__converters.comments.md
- [ ] types/definition.py
    - Status: out-of-scope
    - Path class:
    - Artifacts: rev-types__definition.md, rev-types__definition.performance.md, rev-types__definition.mechanics.md, rev-types__definition.comments.md
- [ ] types/finalizer.py
    - Status: pending
    - Routed: from connection.py Comments (observed true, not graded): "silently" in finalizer prose (true implicit/explicit contrast); owning Comments pass judges
    - Path class:
    - Artifacts: rev-types__finalizer.md, rev-types__finalizer.performance.md, rev-types__finalizer.mechanics.md, rev-types__finalizer.comments.md
- [ ] types/relations.py
    - Status: pending
    - Reopened: 2026-09-28 - types/base.py, registry.py, tests/types/test_finalizer.py, tests/types/test_relay_interfaces.py, tests/utils/test_relations.py, docs/TREE.md (target types/relations.py unchanged)
    - Item baseline: b43e2f2fb07e4c13ee93056c09a5a94ede07065f (`git stash create`); untracked under the package: none; dirty: docs/bug_hunt/HUNT.md, docs/dry/DRY.md, docs/dry/worker-1.md, docs/review/review-0_0_15.md (none under the package)
    - Path class: cold - records are built once per relation field at `DjangoType` declaration and read once per `finalize_django_types()`; nothing runs per request, resolver or row
    - Artifacts: rev-types__relations.md, rev-types__relations.performance.md, rev-types__relations.mechanics.md, rev-types__relations.comments.md
    - Result: 9 findings implemented (0/4/5: F1-F3, V1, V2 Medium; M1, M2, F4 Low; F5 discharged by M1), rejected Performance 4, Mechanics 6, Comments 9 with triggers; 0 deferred. Files: types/relations.py, types/base.py, registry.py, tests/types/test_relations.py, tests/test_registry.py, tests/types/test_finalizer.py, tests/types/test_definition_order.py, tests/types/test_relay_interfaces.py, tests/utils/test_relations.py, docs/TREE.md.
    - Verification: Passed. Performance pass 1 (cold; record build ~850 -> ~690 ns, hash 565-947 -> ~18 ns, 0 hash/eq calls per fakeshop build; no bench figure moves); Mechanics pass 1 (M1 `eq=False` pinned by `tests/types/test_relations.py::test_equal_valued_pending_relations_stay_distinct`, prove exact 4 rows; value-eq-with-guarded-hash mutant fails exactly 2; copy suite 8861 passed, the 2 git-census rows by construction); Comments pass 2 (pass 1 revision-needed: V1, V2 prose M1 falsified; code-digest identity on every prose-only file).
    - Cleanup: Removed docs/review/temp-tests/types__relations; copies released; unrelated work preserved.
- [ ] types/relay.py
    - Status: pending
    - Routed: from conf.py Comments (observed, not graded): "new fail-loud scope" / "prior ... design" narrative wording in tests/types/test_relay_interfaces.py; owning Comments pass judges
    - Routed: from relay.py Mechanics (new-guard question, not a defect): a NodeID/override id slot naming a GenericForeignKey (or any unfilterable attr) reaches a raw Django FieldError at request time on both read and write (verified through the coerce and the filter call, review-20260929T082419-4446b1); no contract demands graceful handling of a non-column slot - candidate fail-loud at declaration/finalize beside _check_composite_pk_for_relay_node; owning Mechanics pass judges
    - Path class:
    - Artifacts: rev-types__relay.md, rev-types__relay.performance.md, rev-types__relay.mechanics.md, rev-types__relay.comments.md
- [ ] types/resolvers.py
    - Status: pending
    - Routed: from resource_policy.py Performance R5: the forward-FK resolver calls check_deadline before its elision early return, so an elided (zero-work) row still pays the ~1.0 us check; call placement in this file, and moving a safety check is a boundary tradeoff for this item's Mechanics pass (F1 shrinks every call regardless); owning Performance pass judges
    - Path class:
    - Artifacts: rev-types__resolvers.md, rev-types__resolvers.performance.md, rev-types__resolvers.mechanics.md, rev-types__resolvers.comments.md
- [ ] types/ integration
    - Status: pending
    - Init files: `types/__init__.py`
    - Artifacts: rev-types.md, rev-types.performance.md, rev-types.mechanics.md, rev-types.comments.md
- [ ] utils/canonical.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__canonical.md, rev-utils__canonical.performance.md, rev-utils__canonical.mechanics.md, rev-utils__canonical.comments.md
- [ ] utils/connections.py
    - Status: pending
    - Routed: from connection.py Comments (F2 twin): utils/connections.py::split_window_rows "a future keyset-cursor backend (which makes rn page-relative)" is stale the same way (page-relative keyset backend live in _resolve_from_window today); also observed-true "NO LONGER" x2 + "formerly" for the owning pass
    - Path class:
    - Artifacts: rev-utils__connections.md, rev-utils__connections.performance.md, rev-utils__connections.mechanics.md, rev-utils__connections.comments.md
- [ ] utils/context.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__context.md, rev-utils__context.performance.md, rev-utils__context.mechanics.md, rev-utils__context.comments.md
- [ ] utils/converters.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__converters.md, rev-utils__converters.performance.md, rev-utils__converters.mechanics.md, rev-utils__converters.comments.md
- [ ] utils/directives.py
    - Status: pending
    - Routed: from list_field.py Comments: utils/directives.py module docstring "Every field factory in the package (...)" census omits a real caller (DjangoConnectionField takes directives= and calls validated_field_directives; connection.py lines 2301, 2347); register_mutation() passthrough half verified true
    - Path class:
    - Artifacts: rev-utils__directives.md, rev-utils__directives.performance.md, rev-utils__directives.mechanics.md, rev-utils__directives.comments.md
- [ ] utils/errors.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__errors.md, rev-utils__errors.performance.md, rev-utils__errors.mechanics.md, rev-utils__errors.comments.md
- [ ] utils/execution_mode.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__execution_mode.md, rev-utils__execution_mode.performance.md, rev-utils__execution_mode.mechanics.md, rev-utils__execution_mode.comments.md
- [ ] utils/imports.py
    - Status: pending
    - Routed: from routers.py Comments: `tests/utils/test_imports.py` module docstring "(``routers.py::require_channels()`` / ``rest_framework::require_drf()``)" names two of the four `require_optional_module` wrappers; written 2026-07-08, rotted when the auth (2026-07-21) and debug-toolbar guards landed; the sentence is about that item's symbol, so the pass grading that module whole owns it
    - Path class:
    - Artifacts: rev-utils__imports.md, rev-utils__imports.performance.md, rev-utils__imports.mechanics.md, rev-utils__imports.comments.md
- [ ] utils/input_values.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__input_values.md, rev-utils__input_values.performance.md, rev-utils__input_values.mechanics.md, rev-utils__input_values.comments.md
- [ ] utils/inputs.py
    - Status: pending
    - Routed: from utils/strings.py Comments run 3 (rev-utils__strings.comments.md run-3 section): tests/utils/test_inputs.py::test_graphql_camel_name stale head claim ("Head lowercased" false, graphql_camel_name("Foo_bar")=="FooBar"; suggested "Head kept as written"); plus "was pinned ... now pins" narrative wording in tests/utils/test_inputs.py
    - Path class:
    - Artifacts: rev-utils__inputs.md, rev-utils__inputs.performance.md, rev-utils__inputs.mechanics.md, rev-utils__inputs.comments.md
- [ ] utils/operation_lease.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__operation_lease.md, rev-utils__operation_lease.performance.md, rev-utils__operation_lease.mechanics.md, rev-utils__operation_lease.comments.md
- [ ] utils/permissions.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__permissions.md, rev-utils__permissions.performance.md, rev-utils__permissions.mechanics.md, rev-utils__permissions.comments.md
- [ ] utils/policies.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__policies.md, rev-utils__policies.performance.md, rev-utils__policies.mechanics.md, rev-utils__policies.comments.md
- [ ] utils/private_state.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__private_state.md, rev-utils__private_state.performance.md, rev-utils__private_state.mechanics.md, rev-utils__private_state.comments.md
- [ ] utils/querysets.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__querysets.md, rev-utils__querysets.performance.md, rev-utils__querysets.mechanics.md, rev-utils__querysets.comments.md
- [ ] utils/relations.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__relations.md, rev-utils__relations.performance.md, rev-utils__relations.mechanics.md, rev-utils__relations.comments.md
- [ ] utils/sessions.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__sessions.md, rev-utils__sessions.performance.md, rev-utils__sessions.mechanics.md, rev-utils__sessions.comments.md
- [ ] utils/typing.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__typing.md, rev-utils__typing.performance.md, rev-utils__typing.mechanics.md, rev-utils__typing.comments.md
- [ ] utils/write_transaction.py
    - Status: pending
    - Routed: from schema.py Mechanics (open `@pytest.mark.xfail` currently in this item's evidence trail only): whether nested atomic blocks target separate databases by design or hide a defect is still undecided - the owning item's Mechanics pass decides, then fixes or files the finding
    - Path class:
    - Artifacts: rev-utils__write_transaction.md, rev-utils__write_transaction.performance.md, rev-utils__write_transaction.mechanics.md, rev-utils__write_transaction.comments.md
- [ ] utils/write_values.py
    - Status: pending
    - Path class:
    - Artifacts: rev-utils__write_values.md, rev-utils__write_values.performance.md, rev-utils__write_values.mechanics.md, rev-utils__write_values.comments.md
- [ ] utils/ integration
    - Status: pending
    - Routed: from utils/strings.py Comments run 3, standing since run 1: django_strawberry_framework/utils/__init__.py "case conversion (``snake_case``, ``pascal_case``)" two-helper framing
    - Init files: `utils/__init__.py`
    - Artifacts: rev-utils.md, rev-utils.performance.md, rev-utils.mechanics.md, rev-utils.comments.md
- [ ] Project integration
    - Status: pending
    - Routed: from list_field.py Comments (observed): tests/base/test_init.py lines 180-187 0.0.14 card narrative ("The secure-output card (spec-048) ... All of these cards shipped in 0.0.14") surrounding the ListArgumentError tail; project-subject prose (public-surface assertion history)
    - Routed: from auth/mutations.py Comments (extends the existing test_init.py 0.0.14 lead): tests/base/test_init.py:171-174 "(the auth-mutations card) owns the ``0.0.13`` cut (Decision 12)" card/version narrative inside the public-surface census comment; the behavioral claim beside it (no package-root auth exports, submodule-only per Decision 3) is true — only the card/version framing is provenance
    - Covers: package-root modules as one component; public exports; import-time cost vs `## Bench baseline`; end-to-end lifecycle across folders; the package-root `__init__.py` (each folder's `__init__.py` is on its folder item)
    - Init files: `__init__.py` (defines `__getattr__`)
    - Artifacts: rev-project.md, rev-project.performance.md, rev-project.mechanics.md, rev-project.comments.md

## Decisions

Maintainer decisions the run surfaced: ruff rules to enable, trade-offs, contracts nobody could cite.
- list_field.py Comments verify 1 (gap G2; no owning open item): test_products_api.py:4710 "(the README \"Coverage rule.\")" - the V1 vocabulary twin in a file this item does not touch.
- keyset.py Comments (routed; owner: types/definition.py, out of this run's scope): types/definition.py `cursor_field` comment "it orders by these columns, mints value-encoded SIGNED cursors (``keyset.py``), and rejects offset cursors" - cursors are AES-SIV authenticated-encrypted and the keyset module docstring explicitly rejects the merely-signed shape; "signed" misstates the confidentiality contract (born-stale in 51421e54).
- keyset.py Comments (observed, no owning open item): "(Revision 2 P1)" process provenance in test_library_api.py::test_stale_after_cursor_no_error.
- error_policy.py Comments (routed; owner: conf.py, verified/closed): conf.py::ERROR_POLICY_KEY doc-comment "as a mapping of ErrorPolicy option names to values" omits the supported ErrorPolicy-instance spelling (deliberate per utils/policies.py::resolve_policy setting-instance branch; twin RESOURCE_POLICY_KEY comment and GLOSSARY ErrorPolicy anchor share the omission).
- error_policy.py Mechanics (routed; suggested home here): docs/GLOSSARY.md ErrorPolicy anchor ("it is **frozen**, so a resolver holding it cannot loosen its own request's policy") states the wrong reason for a true outcome (the class docstring "Frozen is not what establishes that" + copy-per-read + off-schema-record machinery establish it); fix is a glossary-DB edit plus render, outside the item fence.
- conf.py Comments (routed; owner: _cross_web_patches.py, out of this run's scope): django_strawberry_framework/_cross_web_patches.py module docstring "a package view does not consult it" is literally true as "call" (only production call sites are the four apply() gates) but implies the behavioral independence the conf.py F1 finding disproves for the envelope guard (a defect workaround the package mount rides). Suggested judgment: scope to the wire contract the way views.py does, or clarify "consult" as "call".
- _django_patches.py Comments (routed; owner: testing/_wrap.py, out of this run's scope): django_strawberry_framework/testing/_wrap.py module docstring claims "the unwrap-time backstop the package's AppConfig.ready installs unconditionally" but apply() returns before touching SimpleTestCase when APPLY_UPSTREAM_PATCHES is False or {"django": False}.
- utils/strings.py Comments run 3 (routed; owner: orders/inputs.py, out of this run's scope): alias-background narrative sentence in tests/orders/test_inputs.py; behavioral claims graded true.
- permissions.py Mechanics (routed R15; no owning open item): docs/GLOSSARY.md `apply_cascade_permissions` "Hook returns are validated" omits the field-specific `distinct(...)` rejection, which spec-034 promises is "documented in the GLOSSARY body" and which the module docstring + `test_hook_return_rejections_fail_closed[distinct]` pin; fix = `GlossaryTerm.body` ORM edit + `build_glossary_md.py` render, outside the item fence.
- registry.py Comments F10 (routed; owner: DRY flow): `docs/dry/dry-rule-already-registered-error-wording.md:148` still cites the pre-rename `test_register_second_type_for_same_model_no_longer_raises_collision`; the file is untracked concurrent DRY work, deliberately unswept by this run. Sweep to `test_register_second_type_for_same_model_does_not_raise` when that flow lands.
- relay.py Comments (routed; owner: none - connection item verified/closed): `tests/test_relay_connection.py::test_count_less_window_with_count_observer_falls_back_defensively` lines 2372-2374 read "The conditional-count drift guard in _resolve_from_window, narrowed by / The count-policy overhaul leaves only a totalCount observer ..." (fused sentence, two finite verbs); connection-subject prose outside the routed wordings this pass owned.
- relay.py Mechanics verify (routed; spec-prose update vs leave): spec-053 Decision 3 contract 4's "exactly three" deferred-import sentence is stale by one site of the same sanctioned shape (the new function-local `from ..relay import` in `utils/write_values.py::decode_visible_relation_ids`, write_values.py:311); no enforcing gate exists, so the whitelist is prose-only either way.
- relay.py Comments verify (recorded; owner: KANBAN TODO-ALPHA-056-0.0.17): F5+F6 landed as a pair, discharging that card's spec-032 stranded-ordinal row per its own per-spec rule (both sites lived in tests/test_relay_node_field.py).
- schema.py Mechanics (routed; glossary-DB edit + render, outside the item fence): GLOSSARY `DjangoResourcePolicyExtension` lead bullet "as an Extension CLASS" vs body "as a class-not-an-instance" phrasing - Worker-0 routes as glossary prose, not a finding.
- sets_mixins.py Comments (routed; glossary-DB edit + render, outside the item fence): GLOSSARY RelatedOrder anchor ("`sets_mixins.LazyRelatedClassMixin` ... not `filters.base` as named in earlier revisions") — resolution account true, "as named in earlier revisions" temporal.
- auth/mutations.py Mechanics R3 (routed; glossary-DB edit + render, outside the item fence): GLOSSARY `auth-mutations` anchor parenthetical lists four protected fields, omitting `is_active`, while README + body + tests pin five.
- auth/ integration Comments (routed; glossary-DB edit + render, outside the item fence): GLOSSARY `request_from_info` label parenthetical (`FilterSet`/`OrderSet`/`DjangoMutation`) omits the `AuthMutation` + `SerializerMutation` labels though its own sentence lists those callers.

- utils/strings.py (M1): missing fakeshop fixture, a model with a mixed-case scalar, a mixed-case forward FK and a reverse `related_name`, so `tests/optimizer/test_extension.py::test_mixed_case_model_field_selection_projects_its_real_column` and `::test_mixed_case_relation_selections_plan_through_their_django_names` can move to `examples/fakeshop/test_query/`. An item adds no example model.
- Pre-existing, blocks the gate row's CI parity only: `build_tree_md.py --check` is red at HEAD 6ac69870 because `tests/test_workspace.py` (committed in cd6a74aa) has no `docs/TREE.md` row; not this run's item. Fix = render TREE.md in its own change.
- `scripts/prove_failability.py` counts pytest captured-log `ERROR <logger>` lines as collection/setup errors (run `review-20260925T035307-0da5c6` INVALID COUNT); workaround `--show-capture=no` in the scope. Script defect outside the package, no item owns it.
- utils/strings.py (Performance verifier gap, no in-scope owner): a mixed-case or digit-boundary selection costs 7.5-8.4 us per plan build in `optimizer/walker.py::_resolve_selection_target` (reverse miss rebuilds `_graphql_names_by_python_name` and scans via `_field_by_graphql_name`) vs ~150 ns for a lowercase field (`review-20260925T040111-52f3c0`, `-040057-e51263`). Owner: a Performance pass on `optimizer/walker.py`, outside this run's scope; candidate fixes and reopen trigger in `rev-utils__strings.performance.md` `## Verification (Performance)`. Closed 2026-09-25 by a maintainer-approved change beside this run: `optimizer/walker.py` builds one GraphQL-name table per (finalized type, name converter) in `_forward_names_memo`, emptied by `registry.clear()`; a miss costs ~0.53 us (from 8.4-9.4 us; lowercase ~0.23 us), `bench_optimizer_walk.py` digit query 42.25 -> 30.71 us, explicit-name query 15.12 -> 10.25 us, built-in set flat; three new `tests/optimizer/test_walker.py` rows, four failability mutations pinned (evidence under the session scratchpad; the `perfwalk` flow was gc'd, so its run ids no longer audit).
- utils/strings.py (Mechanics, rejected): generated input field names are pinned camelCase and ignore `auto_camel_case=False`; no contract source says they follow the naming config. Decide whether they should. Decided 2026-09-25: they should (upstream strawberry-graphql-django and this package's own list arguments follow the config); card-sized, homed on `TODO-BETA-077-0.1.7` "Generated input field names follow the schema naming config" (probe `camel-20260925T170213-b85bf2`).
- types/relations.py (Comments, routed; owner: the `types/base.py` item): `django_strawberry_framework/types/base.py::_build_annotations` relation-branch comment narrates history ("closed by spec-018", "The earlier eager-bind branch"); the `types/base.py` module docstring step 4 "records unresolved relations" is stale the same way as the relations module docstring (every relation is recorded).
- types/relations.py (Comments, routed; owner: the `utils/relations.py` item): `django_strawberry_framework/utils/relations.py::relation_kind` calls `PendingRelation` "the registry's typed sentinel".
- types/relations.py (Mechanics, rejected, new card candidate): a skipped `finalize_django_types()` surfaces as Strawberry's generic "Unexpected type" `TypeError` under both `strawberry.Schema` and `DjangoSchema`; `DjangoSchema` could re-raise it as a `ConfigurationError` naming `finalize_django_types()`. No contract promises the diagnosis.
- types/relations.py (Comments verify 1, routed; owner: the item whose tests these are, `tests/types/test_relay_interfaces.py` rides with `types/relay.py`): provenance wording in the docstrings of `test_non_relay_type_keeps_id_int` and `test_extended_node_interface_subclass_suppresses_id_annotation`; pre-existing, outside this item's hunks.
- Closed 2026-09-25 (utils/strings.py M1 fixture gap): library `Distributor.displayName`, `Consignment.distributorRef` and `related_name="consignmentItems"` (migration `0008_distributor_consignment.py`) carry the mixed-case shapes; `examples/fakeshop/test_query/test_library_shapes_api.py` pins them live (redundancy proof `fixture-20260925T170318-907f54`, pinned) and the two `tests/optimizer/test_extension.py` stand-ins are deleted. Outside this run's items; landed by a maintainer-approved change beside it.

## Owned changes

One row per tracked edit or new file a verified item landed. A later item may build on a path
listed here; any other dirty hunk is external.

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/utils/strings.py` | utils/strings.py | Performance, Comments | `_plain_text` (branch order, docstring); module docstring; `_snake_case_cached` docstring; `snake_case` (`functools.wraps` `assigned`, docstring); `pascal_case`, `pascal_case_or_raise`, `graphql_camel_name`, `flatten_lookup_path` docstrings |
| `django_strawberry_framework/types/base.py` | utils/strings.py | Mechanics | `DjangoType.__init_subclass__` (field-map key), `_validate_relation_shape_targets`, `_build_annotations`; `snake_case` import removed |
| `django_strawberry_framework/types/finalizer.py` | utils/strings.py | Mechanics | `_synthesize_relation_connections`, `finalize_django_types`; `snake_case` import removed |
| `django_strawberry_framework/management/commands/inspect_django_type.py` | utils/strings.py | Mechanics | `Command._resolve_row`; `snake_case` import removed |
| `django_strawberry_framework/types/relations.py` | utils/strings.py | Mechanics | `PendingRelation` docstring |
| `django_strawberry_framework/optimizer/walker.py` | utils/strings.py | Mechanics | `_resolve_field_map` docstring |
| `django_strawberry_framework/types/__init__.py` | utils/strings.py | Mechanics | module docstring (dependency paragraph) |
| `django_strawberry_framework/optimizer/field_meta.py` | utils/strings.py | Comments | `FieldMeta` docstring (`name` attribute) |
| `tests/optimizer/test_extension.py` | utils/strings.py | Mechanics | `_unmanaged_tables`, `test_mixed_case_model_field_selection_projects_its_real_column`, `test_mixed_case_relation_selections_plan_through_their_django_names` (new) |
| `tests/optimizer/test_walker.py` | utils/strings.py | Mechanics | `_register_type_definition`, `test_scalar_only_secondary_resolver_uses_secondary_field_map`, `test_optimizer_walker_uses_primary_for_nested_relation_target`; `snake_case` import removed |
| `tests/optimizer/test_multi_db.py` | utils/strings.py | Mechanics, Comments | `_register_type_definition`; `snake_case` import removed; module docstring (AGENTS.md citation) |
| `tests/types/test_relay_interfaces.py` | utils/strings.py | Mechanics | `_field_map_for`; `snake_case` import removed |
| `tests/types/test_finalizer.py` | utils/strings.py | Mechanics | `test_malformed_pending_field_name_is_rejected_before_relation_lookup` docstring |
| `django_strawberry_framework/types/relations.py` | types/relations.py | Mechanics, Comments | `PendingRelation` (`eq=False`; fields `relation_kind`, `nullable` removed; `__hash__` removed; docstring); `_hash_component` removed; `RelationKind` import removed; `_PendingRelationAnnotationMeta` comment removed; `PendingRelationAnnotation` docstring; module docstring |
| `django_strawberry_framework/types/base.py` | types/relations.py | Mechanics | `_build_annotations` (`field_map` parameter, `field_meta` local and the two snapshot kwargs removed); `DjangoType.__init_subclass__` (`field_map` argument removed) |
| `tests/types/test_relations.py` | types/relations.py | Mechanics, Comments | module docstring (first line); `_NonHashableField` docstring; `_build_pending`; `test_pending_relation_hash_supports_non_hashable_django_field` docstring; `test_equal_valued_pending_relations_stay_distinct` (new); `test_pending_relation_equality_still_works_with_non_hashable_django_field`, `test_equal_pending_relations_have_equal_hashes`, `test_pending_relation_hash_falls_back_when_value_and_type_hashing_fail` removed |
| `django_strawberry_framework/registry.py` | types/relations.py | Comments | `TypeRegistry.discard_pending` (docstring) |
| `tests/test_registry.py` | types/relations.py | Mechanics, Comments | `test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation`, `test_discard_pending_uses_identity_match_with_real_pending_relation` (docstring, comment, sanity assert), `test_discard_pending_tolerates_non_hashable_django_field`, `test_mutators_reject_calls_after_mark_finalized`, `test_unregister_removes_pending_relations_sourced_from_type`; `relation_kind` import removed; `test_discard_pending_uses_identity_match_with_real_pending_relation` docstring (Comments, pass 2) |
| `tests/types/test_finalizer.py` | types/relations.py | Mechanics | `test_unresolved_relation_diagnostic_survives_hostile_model_name`, `test_malformed_pending_field_name_is_rejected_before_relation_lookup`, `test_pending_relation_without_source_definition_is_typed` |
| `tests/types/test_definition_order.py` | types/relations.py | Mechanics | `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`, `test_auto_annotation_emits_synthesized_annotation` |
| `tests/types/test_relay_interfaces.py` | types/relations.py | Mechanics | `_field_map_for` removed; `FieldMeta` import removed; `test_relay_node_strips_django_id_annotation`, `test_extended_node_interface_subclass_suppresses_id_annotation`, `test_non_relay_type_keeps_id_int`, `test_direct_relay_node_inheritance_suppresses_id_annotation` (`field_map=` argument removed) |
| `tests/utils/test_relations.py` | types/relations.py | Comments | `test_relation_kind_reverse_many_to_one_is_in_literal` docstring |
| `docs/TREE.md` | types/relations.py | Comments | `tests/types/test_relations.py` rows (two) |
| `django_strawberry_framework/_django_patches.py` | _django_patches.py | Comments | audited-set comment block (F1); `_validate_upstream_shape` docstring (F2); `_patched_remove_databases_failures` docstring first line (L1) and symmetry sentence (L2) |
| `tests/test_django_patches.py` | _django_patches.py | Comments | `test_apply_is_idempotent` docstring (F4); `test_reload_preserves_the_installed_patch_teardown` docstring (F5) |
| `tests/testing/test_wrap.py` | _django_patches.py | Comments | `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth` docstring first line (F3) |
| `django_strawberry_framework/_graphql_core_patches.py` | _graphql_core_patches.py | Performance, Comments | `_patched_complete_list_value` (guard conjunct order); `except ImportError` pragma comment (test-mechanism wording) |
| `django_strawberry_framework/_strawberry_patches.py` | _strawberry_patches.py | Comments | module docstring shield paragraph (F1) and Upstream-status currency (F8); `_patched_parse_json` docstring first line (L2) and guard-coverage paragraph (F2); `_translated_parse_json` docstring first line (L1); `_patched_parse_query_params` docstring first line (L3) |
| `tests/test_strawberry_patches.py` | _strawberry_patches.py | Comments | module docstring gap-1 summary (F9), shield sentence (F3), coverage-map pointer (L4) and cause inventory (F10) |
| `tests/test_views.py` | _strawberry_patches.py | Comments | `_strawberry_patch_opted_out` docstring (F6) |
| `examples/fakeshop/test_query/test_products_api.py` | _strawberry_patches.py | Comments | `test_get_query_with_object_variables_executes_like_upstream` docstring (F4); `test_get_query_with_malformed_variables_param_is_the_upstream_parse_400` docstring (F5); `test_post_utf16_json_body_is_rejected_as_400` docstring (L6) |
| `examples/fakeshop/test_query/test_transport_api.py` | _strawberry_patches.py | Comments | `_strawberry_patch_opted_out` docstring (F7); `test_the_utf8_wire_contract_survives_the_upstream_patch_kill_switch` docstring (L5) |
| `tests/test_apps.py` | apps.py | Comments | `test_ready_dispatches_all_four_patch_appliers_and_refires_safely` (docstring masking paragraph); `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` (parametrize `why` literals) |
| `django_strawberry_framework/conf.py` | conf.py | Mechanics, Comments | six reader annotations (`-> Any`); `Callable` import removed; `UPSTREAM_PATCH_DEPENDENCIES` comment (F1); `Settings.__getattr__` comment (F2); `_normalize_user_settings` docstring (F3) |
| `tests/base/test_conf.py` | conf.py | Mechanics | `test_setting_reader_helpers_return_wrong_typed_values_verbatim` (new) |
| `django_strawberry_framework/connection.py` | connection.py | Performance, Mechanics, Comments | `_window_edge_class` (memo) + `_window_edge_class_cache`, `clear_window_edge_class_cache` (new); `_build_windowed_fallback` (factory) + `_resolve` (lazy source); `_resolve_from_window` (guard reorder; docstring); `_consume_window` docstring; `_cap_offset_last_zero_page` (new) + `_consume_fallback` (quirk trim + V1 untrimmed bind); `_resolve_order_path_field` (import hoist); `_KeysetPage`, `_resolve_keyset_connection`, `_build_relation_connection_resolver` docstrings; `resolve_connection` comments |
| `tests/test_relay_connection.py` | connection.py | Performance | `test_windowed_fast_path_constructs_no_fallback_queryset` (new) |
| `examples/fakeshop/test_query/test_keyset_api.py` | connection.py | Mechanics | `test_offset_last_zero_stays_bounded_by_relay_cap` (new); `seed_data` import |
| `django_strawberry_framework/consumers.py` | consumers.py | Comments | module docstring (import-graph enumeration, `__all__` site, voice); `revalidate_operation_actor`, `_RevalidatingGraphQLWSHandler.handle`, `DjangoWebSocketHostValidator` first lines; `_actor_is_current` comment; `_contain_message_loop_failure` docstring |
| `tests/test_routers.py` | consumers.py | Comments | non-string-query comment (C2 via Mechanics cross-axis); two test docstrings (provenance/tense) |
| `tests/test_error_policy.py` | error_policy.py | Comments | frozen-test rename + docstring (M1); schema-policy, teardown, hostile-message, unreadable-settings docstrings (M2/M3/L1/L2) |
| `examples/fakeshop/test_query/test_error_policy_api.py` | error_policy.py | Comments | `_masked_error` (key-set assertion); opt-out, hook, globalid, debug docstrings; `HOOK_HALVES` comment |
| `django_strawberry_framework/exceptions.py` | exceptions.py | Comments | `PathResolutionError` (M1 paragraph, C2 bullet, L2 sentence); `LookupValidationError` (C3 bullet); `OptimizerError` (C1/L1 bullet, fallback fix) |
| `tests/test_exceptions.py` | exceptions.py | Comments | `test_empty_args_render_empty_string` docstring (M2) |
| `django_strawberry_framework/keyset.py` | keyset.py | Comments | `KeysetSeek`, `encode_keyset_cursor`, `KeysetSeekPlan`, module docstring (M1-M4); `keyset_contract_error` docstring (L1) |
| `django_strawberry_framework/list_field.py` | list_field.py | Comments | `_validate_djangotype_target` docstring (live sharers); `DjangoListField` factory comment (spec-020 pointers); `_APPROVED_ORDER_AGGREGATES` comment (`Count` admission); `DjangoListField` docstring (tiebreaker-only contrast); `_handle_non_queryset_rejections_async` docstring (spec-050 anchor); `_is_deterministic_order_term` docstring (G1 aggregate emission) |
| `examples/fakeshop/test_query/test_library_api.py` | list_field.py | Comments | Manager-coercion docstring (live entry + V1 README re-pin); nullable-outer docstring (phantom companion dropped) |
| `django_strawberry_framework/permissions.py` | permissions.py | Performance, Comments | `_walk` (accumulated conditions, single guarded `.filter`, F1); `_root_error_renderer`, `_edge_error_renderer` (lazy `truth.name` in `_render`, F2); import comment + `_cascadable_edge_names`, `_validate_fields`, `apply_cascade_permissions` x4, `aapply_cascade_permissions` docstrings (spec-034 Decision anchors, L1); `aapply_cascade_permissions` docstring (imperative first line, L2) |
| `tests/test_permissions.py` | permissions.py | Performance, Comments | `_count_filter_calls` + `test_two_edge_cascade_issues_a_single_filter_call`, `test_zero_edge_root_issues_no_filter_call`, `test_error_renderers_build_without_naming_calls` (new F1/F2 pins); module + identity-test docstrings (four-root census, M1); `test_aapply_runs_walk_off_event_loop` (traversal state, M2); `_StaffOnlyCategoryOrder` docstring (false parenthetical dropped, M3); `_cascade_only`, `_exclude_private`, `_gate_info`, `_assert_contextvar_clean` (imperative first lines, L3; dedup history dropped, L4) |
| `django_strawberry_framework/registry.py` | registry.py | Comments | `TypeRegistry.iter_types` docstring (real consumer only, F4); `TypeRegistry.register_with_definition` docstring first line (imperative, F7); `TypeRegistry._detach_type_from_model` docstring (helper-bound clause, F8) |
| `tests/test_registry.py` | registry.py | Mechanics, Comments | `test_mutators_reject_calls_after_mark_finalized` (first line guarded-scope, F5; teardown + unknown-unregister rows, L1); `test_clear_tolerates_unimportable_connection_submodule` + `test_clear_tolerates_unimportable_relay_module` docstrings and comments (replay framing, F1/F2); unregister section comment (present-tense scope, F3); `test_unregister_of_primary_leaves_state_that_audit_rejects` docstring (one-line pinpoint, F9); `test_register_second_type_for_same_model_does_not_raise` renamed (F10) |
| `tests/orders/test_composition.py` | registry.py | Comments | `_isolate_registry` docstring (replay mechanism, F6) |
| `docs/SPECS/spec-018-meta_primary-0_0_6.md` | registry.py | Comments | test-name sweep for the F10 rename |
| `django_strawberry_framework/relay.py` | relay.py | Performance, Mechanics, Comments | `current_write_pipeline` import hoisted (L1); `_node_id_slot` docstring (C2 sub-cases); `_coerce_pk_or_none` + `_resolve_real_pk` (`slot` threading); `_decode_and_coerce` + `_resolve_real_pks_batched` (new, F1); `decode_model_global_id` (half compose + live-consumer docstring C1); both `_resolve` (F2 isawaitable guards, F3 slot memo, F1/F2 Decision pointers) |
| `django_strawberry_framework/utils/write_values.py` | relay.py | Performance | `decode_visible_relation_ids` (F1 batched NodeID mapping); `type_check_relation_id` docstring (C1 reword); module docstring (compose line) |
| `tests/test_relay_node_field.py` | relay.py | Performance, Comments | `test_sync_node_path_builds_no_owner_name`, `test_batch_coercion_computes_id_slot_once_per_type` (new F2/F3 pins); module docstring + 3 test docstrings (F3-F6 prose) |
| `tests/utils/test_write_values.py` | relay.py | Performance | `test_custom_node_id_relation_set_batches_real_pk_lookup`, `test_custom_node_id_relation_set_mapping_uses_pipeline_alias` (new F1 pins) |
| `django_strawberry_framework/resource_policy.py` | resource_policy.py | Performance, Mechanics, Comments | `_deadline_expired` (`None`-first guard, Perf F1); `ResourcePolicy.narrowed` int arm (`widens = value > current`, Mech L1); `ResourcePolicy` docstring (single-object relation seam family, Comments F2); `check_deadline` docstring (admission-walk precedent pointer, Comments F6) |
| `tests/test_resource_policy.py` | resource_policy.py | Comments | `test_bounded_rows_bounds_a_mapping_shaped_result` docstring (exact-type rationale, F1); `test_an_instance_through_the_setting_slot_resolves_on_the_same_terms` docstring (present-tense counterfactual, F5); "A copied context is not an armed one" banner (survivor-test pointer, F3) |
| `examples/fakeshop/test_query/test_resource_policy_api.py` | resource_policy.py | Comments | module docstring (false `examples/fakeshop/tests` half-pointer dropped, F4) |
| `django_strawberry_framework/routers.py` | routers.py | Comments | `_CHANNELS_INSTALL_HINT` comment (T1 hint census + T2 Django ceiling); `require_channels`, `_build_router_class_uncached` docstrings (T1 scoping); module docstring, `_MISSING_DJANGO_APPLICATION_HINT` comment, `_validated_websocket_url_pattern`, `_factory_application`, `DjangoGraphQLProtocolRouter` docstrings (5 riding Lows) |
| `django_strawberry_framework/scalars.py` | scalars.py | Performance, Mechanics, Comments | `_serialize_bigint` (exact-`int` fast path, F1; subclass comment voice, L3); `_parse_bigint` (exact-`int` fast path + exact-`str` branch, F2); module docstring (BigInt mechanism gloss, M1; bare-int-literal reason, C1; spec-037 Decision 5 pointer, L1); re-export comment (spec-037 Decision 5, L1) |
| `tests/test_scalars.py` | scalars.py | Comments, Performance | module docstring (Upload placement bullet, M2; subclass bullet); `test_bigint_rejects_none` docstring (M3); `test_strawberry_config_returns_strawberry_config_instance`, `test_strawberry_config_default_scalar_map_includes_bigint`, `test_strawberry_config_collision_with_package_scalar_raises_value_error`, `test_strawberry_config_rejects_scalar_map_kwarg`, `test_strawberry_config_scalar_map_excludes_upload` docstrings (spec anchors, L2); `test_bigint_int_subclasses_are_normalized_before_serialization` (`_HostileStr` leg covering the F2 subclass-`str` line, same test) |
| `django_strawberry_framework/schema.py` | schema.py | Mechanics, Comments | `DjangoSchema._subscribe` (new F1 floor-band override); `DjangoSchema._stream` docstring (C2 override-set restatement); `DjangoMutationExecutionContext._execution_errors` docstring (M1/C1 3.2.10 re-pin); `_SCHEMA_ENFORCEMENT` comment (M2 recount); `_UNREADABLE_CONFIGURATION` comment (M3 live diagnostic); module docstring (L1 version strip, L2 dangling pointer); `DjangoMutationExecutionContext`, `_RefusedConfiguration` first lines (L5 descriptive) |
| `tests/test_schema.py` | schema.py | Mechanics, Comments | `test_a_subscribe_whose_runner_is_not_the_packages_is_handed_back_untouched` (new F1 direct-call pin); `DjangoExtensionsRunner` import; `test_a_refused_request_never_asks_a_transport_policy_whether_it_is_empty` docstring (M4); `test_an_extension_entry_strawberry_could_not_resolve_is_refused` docstring (L3 repoint) |
| `tests/extensions/test_operation_state.py` | schema.py | Mechanics | 11 subscribe-only `_SKIP_WITHOUT_STREAM` rows un-skipped (F1b, incl. both Proof nodes); 4 genuine-`stream` rows stay skipped |
| `tests/mutations/test_write_transaction.py` | schema.py | Comments | `test_execution_errors_reads_both_graphql_core_error_shapes` docstring (M1 twin 3.2.10 re-pin) |
| `examples/fakeshop/test_query/test_extension_isolation_api.py` | schema.py | Comments | module docstring (M5 four-claim opener); `_LADDER_FACTORIES` comment (M6 prose reword); `_REFUSED_OPERATION_NAMES` comment (M7 string census) |
| `examples/fakeshop/test_query/test_mutation_atomicity.py` | schema.py | Comments | module docstring (M8 agency fix; L4 biography strip) |
| `django_strawberry_framework/sets_mixins.py` | sets_mixins.py | Performance, Mechanics, Comments | `RelatedSetTargetMixin._resolved_target` (success-only identity memo `_validated_target_memo`, Perf F1; docstring C1/M4 converged + L7 + memo paragraph); `RelatedSetTargetMixin` class docstring (C1/M3 converged memo text, L6, distinct-value); `_validate_target` message (distinct-value); `__all__` (+3 names, Mech F1); module docstring (M1, M2, L3); `ClassBasedTypeNameMixin` docstring (L1); `type_name_for` docstring (M7, L4); `LazyRelatedClassMixin` docstring (L2, L5); `resolve_lazy_class` docstring (M5); `expanded_once` docstring (M6, L8, L17); `should_cache_expansion` docstring (L9); `is_re_readable_field_declaration` docstring (M8); `ActiveInputPermissionAttrs` docstring (L10, L11); `_input_traversal` docstring (L12) |
| `tests/test_sets_mixins.py` | sets_mixins.py | Performance, Mechanics, Comments | `test_resolved_target_validates_each_distinct_value_once` (new Perf F1 counting pin); `test_sets_mixins_all_exports_are_complete` (Mech F1 completeness); `test_related_set_target_mixin_gates_resolved_targets_at_the_seam` docstring (L13, distinct-value); `test_re_readable_gate_rejects_one_shot_and_text_atoms` docstring (M10); `test_filter_normalizer_consumes_the_family_permission_traversal` docstring (L14); `test_filter_normalizer_honors_a_subclass_unset_sentinel_override` docstring (L15); `test_re_readable_gate_accepts_every_sized_collection` docstring (L16) |
| `tests/filters/test_inputs.py` | sets_mixins.py | Comments | `test_type_name_for_raises_for_no_word_character_field_path` docstring (M11) |
| `tests/orders/test_base.py` | sets_mixins.py | Comments | `test_related_order_orderset_setter_assigns_underscore_orderset` docstring (M12) |
| `django_strawberry_framework/auth/mutations.py` | auth/mutations.py | Mechanics, Comments | `_SealedAuthHolderMeta` removed; `_make_permission_holder` rides `DjangoMutationMetaclass` (+ import, Mech F1); `_AUTH_FAMILY_LABEL` comment (three-fixed-fields scope, M2); declaration-ledger comment (owner-registered row, M1); `_register_decode_step` docstring (UNSET-`None` handoff, M3); `_channels_logout` docstring (empty-row reason, M4); `_login_resolve_body` + `_logout_resolve_body` docstrings (spec-046 Decision 2 pointer, L1) |
| `tests/auth/test_mutations.py` | auth/mutations.py | Mechanics, Comments | `test_auth_permission_holder_head_is_sealed` docstring (owner guard, F1); `test_sealed_holder_rebind_message_names_the_holder` expected string (owner tail, F1); dispatch docstring (`async_execution`, M5); `_channels_router` docstring (L2); five `Row N` openers dropped (L3); two `Stage 0` parentheticals dropped (L4); enumeration-guard banner removed (L5); logout banner census (L6) |
| `tests/auth/conftest.py` | auth/mutations.py | Comments | `_sync_boundary_spy` docstring (bridge-vs-native, M6) |
| `tests/auth/test_queries.py` | auth/queries.py | Comments | module docstring first line (F1 `visibility` dropped); module docstring residue paragraph (L2 five-pin enumeration); `_channels_context` docstring (L1 imperative); `test_async_me_dispatch_awaits_the_bridged_async_body_exactly_once` renamed + docstring (F2 bridge vocabulary) |
| `docs/TREE.md` | auth/queries.py | Comments | `tests/auth/test_queries.py` rows (two, F1 render) |
| `django_strawberry_framework/auth/sessions.py` | auth/sessions.py | Comments | module docstring (F1 `auth`-subpackage scoping; F2 downstream-failure shape); `_CHANNELS_INSTALL_HINT` comment (F3 arrival path + type discipline + later failure); `login_supported`, `logout_supported` docstrings (F4 dangling plan pointer dropped; F8/F9 imperative); `_SCOPE_LOCK_MESSAGES` comment (F5 present tense); `classify_transport` docstring (F6 unwrap candidate); `require_session` docstring (F2 downstream-failure shape); `uses_signed_cookie_sessions` docstring (F7 imperative) |

## Outcomes

Filled by Worker-0 at closeout before any scratch is removed; a scoped run adds "Scope of this run".

### utils/strings.py

- Performance: L1 Low `_plain_text` exact-`str` test first, implemented; `_plain_text` 36.7 -> 29.3 ns vs the reordered reference (delta 8.4 -> 0.6 ns, before `review-20260925T034653-e76c46`, after `review-20260925T035407-988276`, verifier reproduced 9.0 / 0.6 ns); no bench figure moves. 5 rejections w/ triggers (inline `snake_case` fast path, `lru_cache` sizing, cached char loop, cold string building, `flatten_lookup_path` loop).
- Mechanics: M1 High defect fixed at the owner. `DjangoTypeDefinition.field_map` was keyed by `snake_case(f.name)`, so a mixed-case model field (legal Django) crashed every optimized query selecting it (`FieldDoesNotExist`, masked as an internal error; unoptimized path served it). Now keyed by the raw Django name; five readers in `types/base.py`, `types/finalizer.py`, `inspect_django_type.py` stop re-applying `snake_case`; the walker alone still reverses GraphQL selection names. Permanent tests `tests/optimizer/test_extension.py::test_mixed_case_model_field_selection_projects_its_real_column` and `::test_mixed_case_relation_selections_plan_through_their_django_names` (package tier; fixture gap under `## Decisions`); `prove` pins exactly those two; verifier attacks (async, `relation_shapes` connection, `OptimizerHint.SKIP`, `inspect_django_type`) pass and three of them fail on revert. 7 rejections w/ triggers incl. two Comments cross-axis leads.
- Comments: F1-F4 Medium (stale module docstring; `snake_case` contract overclaimed and hidden behind `functools.wraps`; `graphql_camel_name` "Lowercase the head"; `pascal_case` false reasons), F5-F7 Low, all implemented pass 1; verify 1 added F9 Medium (`FieldMeta.name` "snake_case"), F10 Low ("every request" -> "every plan build"), F11 Low (stale `AGENTS.md #"..."` citation in `tests/optimizer/test_multi_db.py`), implemented pass 2 and verified; prose-only re-pass proven by stripped-AST identity. F8 Low (provenance in `tests/utils/test_strings.py`) deferred: no higher finding touches that file. 7 rejections w/ triggers.
- Out-of-item leads, owners named: `utils/__init__.py` "case conversion (``snake_case``, ``pascal_case``)" framing -> `utils/` folder item Comments; past-tense narrative in `tests/optimizer/test_walker.py` docstrings -> an `optimizer/walker.py` item; walker slow path for mixed-case / digit-boundary selections -> `## Decisions`.

### Run

- Bench baseline vs gate: every row within spread, instrument ids identical, query counts identical (table above).
- Decisions owed to the maintainer: four, under `## Decisions` (mixed-case fakeshop fixture; pre-existing `docs/TREE.md` drift for `tests/test_workspace.py` at HEAD, CI `build_tree_md.py --check` red independent of this run; `prove_failability.py` captured-log miscount; generated inputs vs `auto_camel_case=False`), plus the walker slow-path lead.
- Cells unverified: none. sharded and pg `inapplicable by construction` for every finding (verifiers concurred); both suites ran green in the gate.
- Blocked items: none.
- Net source change vs cycle baseline 6ac69870: package 8 files +105/-92; tests 5 files +162/-14; uncommitted.
- Gate record: `gate-review-20260925T042258-72d2fd.json`, all three suites exit 0, coverage 100%.
- Concurrent work untouched: the cycle baseline held only `output/`; no drift during the run.
- Scope of this run: `utils/strings.py` and the final gate. Every other file, folder and the project item were out of scope and not examined; their boxes stay unticked. The M1 fix edited files outside the target as its root-cause owner (13 ledger rows); those files' own items were not reviewed.

## Run 0.0.15 2026-09-25-2

Scope: types/relations.py
Drift: 2026-09-25 HEAD 6ac698704402..4cc95b771ecd; dirty + docs/bug_hunt/HUNT.md, docs/dry/DRY.md, docs/dry/worker-1.md
Drift: 2026-09-25 HEAD 4cc95b771ecd (unmoved); dirty + django_strawberry_framework/optimizer/walker.py, tests/optimizer/test_extension.py, examples/fakeshop/README.md, examples/fakeshop/apps/library/{filters,models,orders,schema}.py,
  examples/fakeshop/apps/library/tests/test_models.py, examples/fakeshop/test_query/README.md, examples/fakeshop/test_query/test_library_shapes_api.py; untracked + examples/fakeshop/apps/library/migrations/0008_distributor_consignment.py (maintainer-approved changes beside this run, not this item's)

Already itemized above, worked this run:

- `types/relations.py`
- `Final gate`

### types/relations.py

- Performance: no findings; path class cold (records built once per relation field at declaration, read once per finalize). Rejected with triggers: the per-call `__hash__` tuple, frozen-dataclass construction cost, the module's import cost, the `registry.py` pending-list rebuilds. Verify measured record build ~850 -> ~690 ns and hash 565-947 -> ~18 ns after M1; 0 hash / eq calls per fakeshop build before and after; no bench figure moves.
- Mechanics: M1 Low, `PendingRelation` value equality and the guarded `__hash__` / `_hash_component` (which swallowed `BaseException`) had no production reader (every consumer matches by identity); now `@dataclass(frozen=True, eq=False)`, helpers deleted, pinned by `tests/types/test_relations.py::test_equal_valued_pending_relations_stay_distinct` (prove: reverting `eq=False` fails exactly 4 rows; value equality behind a guarded hash fails exactly 2). M2 Low, the `relation_kind` / `nullable` snapshot fields copied `FieldMeta` and were never read; removed with `_build_annotations`'s now-dead `field_map` parameter (Worker-2 went past the Recommendation; the verifier upheld it). Rejected with triggers: diagnosing a skipped `finalize_django_types()` (new-card candidate in `## Decisions`), the sentinel error string, deleting its metaclass, the `related_model` / `source_model` copies, the `TYPE_CHECKING` import, the finalizer's defense branch.
- Comments: F1-F3 Medium (module and `PendingRelation` docstrings claimed records exist only for unregistered targets; the test module gave a false reason, unhashable Django relations, for the guarded hash: 303 of 303 real relations hash), F4 Low (sentinel repr docstring named the wrong trigger), F5 Low discharged by M1. Verify 1 revision-needed: V1, V2 Medium, prose M1 made false (`tests/test_registry.py` identity-test docstring; `registry.py::TypeRegistry.discard_pending` "identity is a stronger contract than `__eq__`"); pass 2 prose-only, Comments alone re-verified. Every prose-only file carries a `--code-digest` identity; where M1 / M2 changed a file's code, against a reconstruction of the baseline plus those hunks. TREE.md: the two `tests/types/test_relations.py` rows.
- Routed out of the item into `## Decisions`: `types/base.py` comment and docstring, `utils/relations.py::relation_kind` wording, `tests/types/test_relay_interfaces.py` provenance, the skipped-finalize diagnosis.
- Board: `TODO-ALPHA-053-0.0.15` item (c) marked resolved (M2 deleted the comment it named).

### Run 0.0.15 2026-09-25-2

- Bench baseline vs gate 2: plan cache, walk and nested fetch within spread, query counts and plan shapes identical; importtime compares nothing (instrument changed in 4cc95b77).
- Decisions owed: none newly blocking. Closed this run beside the item (maintainer-approved): the mixed-case fakeshop fixture gap, the walker mixed-case slow path, and the `auto_camel_case` question (decided: follow the config; homed on `TODO-BETA-077-0.1.7`). Open and routed: the `types/base.py`, `utils/relations.py` and `types/relay.py` leads, the skipped-finalize diagnosis card candidate.
- Cells unverified: none; sharded and pg inapplicable by construction for the item, all three suites green at the gate.
- Blocked items: none.
- Net source change vs cycle baseline this run: the item's 10 ledger rows, plus concurrent maintainer-approved changes (Drift lines) to `optimizer/walker.py`, `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`, the library app, its live tests and READMEs, and the board (`KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`).
- Gate record: `gate-review-20260925T174743-8d66b3.json`, all four suites exit 0, coverage 100%.
- Concurrent work untouched: the item's attribution matched every hunk; `docs/bug_hunt/`, `docs/dry/` edits were this session's, outside the item.
- Scope of this run: `types/relations.py` and the final gate. Every other file, folder and the project item were out of scope and not examined; the item's edits to `types/base.py`, `registry.py` and six test modules were root-cause and prose owners, their own items not reviewed.

## Run 0.0.15 2026-09-28-3

Scope: changed since 0.0.14 (92c37bf4b05a)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + django_strawberry_framework/management/commands/inspect_django_type.py, django_strawberry_framework/optimizer/field_meta.py, django_strawberry_framework/optimizer/walker.py, django_strawberry_framework/registry.py, django_strawberry_framework/types/base.py, django_strawberry_framework/types/finalizer.py, django_strawberry_framework/utils/strings.py, docs/TREE.md, tests/optimizer/test_extension.py, tests/types/test_finalizer.py, tests/types/test_relay_interfaces.py, tests/utils/test_relations.py
Drift: 2026-09-28 HEAD 4cc95b771ecd..0c0537e2dd94; dirty + .github/workflows/django.yml, .pre-commit-config.yaml, KANBAN.html, KANBAN.md, START.md, django_strawberry_framework/_cross_web_patches.py, django_strawberry_framework/_django_patches.py, django_strawberry_framework/_graphql_core_patches.py, django_strawberry_framework/_request_body.py, django_strawberry_framework/_strawberry_patches.py, django_strawberry_framework/auth/mutations.py, django_strawberry_framework/auth/sessions.py, django_strawberry_framework/conf.py, django_strawberry_framework/connection.py, django_strawberry_framework/consumers.py, django_strawberry_framework/error_policy.py, django_strawberry_framework/exceptions.py, django_strawberry_framework/extensions/debug.py, django_strawberry_framework/extensions/error_policy.py, django_strawberry_framework/extensions/operation_state.py, django_strawberry_framework/extensions/resource_policy.py, django_strawberry_framework/filters/base.py, django_strawberry_framework/filters/inputs.py, django_strawberry_framework/filters/sets.py, django_strawberry_framework/forms/converter.py, django_strawberry_framework/forms/inputs.py, django_strawberry_framework/forms/resolvers.py, django_strawberry_framework/forms/sets.py, django_strawberry_framework/keyset.py, django_strawberry_framework/list_field.py, django_strawberry_framework/middleware/debug_toolbar.py, django_strawberry_framework/middleware/request_body.py, django_strawberry_framework/mutations/fields.py, django_strawberry_framework/mutations/inputs.py, django_strawberry_framework/mutations/operations.py, django_strawberry_framework/mutations/permissions.py, django_strawberry_framework/mutations/resolvers.py, django_strawberry_framework/mutations/sets.py, django_strawberry_framework/optimizer/extension.py, django_strawberry_framework/optimizer/hints.py, django_strawberry_framework/optimizer/join_taxonomy.py, django_strawberry_framework/optimizer/nested_fetch.py, django_strawberry_framework/optimizer/nested_planner.py, django_strawberry_framework/optimizer/plans.py, django_strawberry_framework/optimizer/predicates.py, django_strawberry_framework/optimizer/selections.py, django_strawberry_framework/orders/base.py, django_strawberry_framework/orders/inputs.py, django_strawberry_framework/orders/sets.py, django_strawberry_framework/permissions.py, django_strawberry_framework/relay.py, django_strawberry_framework/resource_policy.py, django_strawberry_framework/rest_framework/inputs.py, django_strawberry_framework/rest_framework/resolvers.py, django_strawberry_framework/rest_framework/serializer_converter.py, django_strawberry_framework/rest_framework/sets.py, django_strawberry_framework/routers.py, django_strawberry_framework/scalars.py, django_strawberry_framework/schema.py, django_strawberry_framework/sets_mixins.py, django_strawberry_framework/testing/client.py, django_strawberry_framework/testing/relay.py, django_strawberry_framework/types/converters.py, django_strawberry_framework/types/definition.py, django_strawberry_framework/types/relay.py, django_strawberry_framework/types/resolvers.py, django_strawberry_framework/utils/canonical.py, django_strawberry_framework/utils/connections.py, django_strawberry_framework/utils/context.py, django_strawberry_framework/utils/converters.py, django_strawberry_framework/utils/directives.py, django_strawberry_framework/utils/errors.py, django_strawberry_framework/utils/input_values.py, django_strawberry_framework/utils/inputs.py, django_strawberry_framework/utils/permissions.py, django_strawberry_framework/utils/policies.py, django_strawberry_framework/utils/private_state.py, django_strawberry_framework/utils/querysets.py, django_strawberry_framework/utils/relations.py, django_strawberry_framework/utils/sessions.py, django_strawberry_framework/utils/typing.py, django_strawberry_framework/utils/write_transaction.py, django_strawberry_framework/utils/write_values.py, django_strawberry_framework/views.py, docs/README.md, docs/bug_hunt/bug_hunt-0_0_15.md, docs/dry/dry-0_0_15.md, docs/dry/dry-file-utils__querysets.md, examples/fakeshop/db.sqlite3, examples/fakeshop/test_query/README.md, examples/fakeshop/test_query/conftest.py, examples/fakeshop/test_query/test_auth_api.py, examples/fakeshop/test_query/test_error_policy_api.py, examples/fakeshop/test_query/test_library_api.py, examples/fakeshop/test_query/test_products_api.py, pyproject.toml, tests/auth/_helpers.py, tests/auth/conftest.py, tests/auth/test_mutations.py, tests/auth/test_queries.py, tests/auth/test_sessions.py, tests/base/test_conf.py, tests/base/test_init.py, tests/extensions/test_debug.py, tests/extensions/test_operation_state.py, tests/filters/test_base.py, tests/filters/test_finalizer.py, tests/filters/test_inputs.py, tests/filters/test_sets.py, tests/forms/test_converter.py, tests/forms/test_inputs.py, tests/forms/test_resolvers.py, tests/forms/test_sets.py, tests/management/test_inspect_django_type.py, tests/mutations/test_fields.py, tests/mutations/test_inputs.py, tests/mutations/test_operations.py, tests/mutations/test_permissions.py, tests/mutations/test_resolvers.py, tests/mutations/test_sets.py, tests/mutations/test_write_transaction.py, tests/optimizer/test_field_meta.py, tests/optimizer/test_hints.py, tests/optimizer/test_join_taxonomy.py, tests/optimizer/test_nested_fetch.py, tests/optimizer/test_nested_index_advisory.py, tests/orders/test_base.py, tests/orders/test_finalizer.py, tests/orders/test_inputs.py, tests/orders/test_sets.py, tests/rest_framework/test_converter.py, tests/rest_framework/test_inputs.py, tests/rest_framework/test_resolvers.py, tests/rest_framework/test_sets.py, tests/test_connection.py, tests/test_consumers.py, tests/test_error_policy.py, tests/test_exceptions.py, tests/test_list_field.py, tests/test_permissions.py, tests/test_relay_connection.py, tests/test_relay_node_field.py, tests/test_resource_policy.py, tests/test_routers.py, tests/test_scalars.py, tests/test_schema.py, tests/test_sets_mixins.py, tests/test_views.py, tests/testing/test_client.py, tests/testing/test_relay.py, tests/types/test_base.py, tests/types/test_converters.py, tests/types/test_definition_relations.py, tests/types/test_resolvers.py, tests/utils/test_canonical.py, tests/utils/test_context.py, tests/utils/test_directives.py, tests/utils/test_errors.py, tests/utils/test_input_values.py, tests/utils/test_inputs.py, tests/utils/test_permissions.py, tests/utils/test_policies.py, tests/utils/test_querysets.py, tests/utils/test_sessions.py, tests/utils/test_strings.py, tests/utils/test_write_values.py, django_strawberry_framework/utils/lazy.py, django_strawberry_framework/utils/truth.py, docs/bug_hunt/bug_hunt-0_0_15-historical.md, docs/dry/dry-file-__init__.md, docs/dry/dry-file-_boundary_ordering.md, docs/dry/dry-file-_cross_web_patches.md, docs/dry/dry-file-_django_patches.md, docs/dry/dry-file-_graphql_core_patches.md, docs/dry/dry-file-_request_body.md, docs/dry/dry-file-_strawberry_patches.md, docs/dry/dry-file-apps.md, docs/dry/dry-file-auth____init__.md, docs/dry/dry-file-auth__mutations.md, docs/dry/dry-file-auth__queries.md, docs/dry/dry-file-auth__sessions.md, docs/dry/dry-file-conf.md, docs/dry/dry-file-connection.md, docs/dry/dry-file-consumers.md, docs/dry/dry-file-error_policy.md, docs/dry/dry-file-exceptions.md, docs/dry/dry-file-extensions____init__.md, docs/dry/dry-file-extensions__debug.md, docs/dry/dry-file-extensions__error_policy.md, docs/dry/dry-file-extensions__operation_state.md, docs/dry/dry-file-extensions__resource_policy.md, docs/dry/dry-file-filters____init__.md, docs/dry/dry-file-filters__base.md, docs/dry/dry-file-filters__factories.md, docs/dry/dry-file-filters__inputs.md, docs/dry/dry-file-filters__sets.md, docs/dry/dry-file-forms____init__.md, docs/dry/dry-file-forms__converter.md, docs/dry/dry-file-forms__inputs.md, docs/dry/dry-file-forms__resolvers.md, docs/dry/dry-file-forms__sets.md, docs/dry/dry-file-keyset.md, docs/dry/dry-file-list_field.md, docs/dry/dry-file-management____init__.md, docs/dry/dry-file-management__commands____init__.md, docs/dry/dry-file-management__commands___imports.md, docs/dry/dry-file-management__commands__export_schema.md, docs/dry/dry-file-management__commands__inspect_django_type.md, docs/dry/dry-file-middleware____init__.md, docs/dry/dry-file-middleware__debug_toolbar.md, docs/dry/dry-file-middleware__request_body.md, docs/dry/dry-file-mutations____init__.md, docs/dry/dry-file-mutations__fields.md, docs/dry/dry-file-mutations__inputs.md, docs/dry/dry-file-mutations__operations.md, docs/dry/dry-file-mutations__permissions.md, docs/dry/dry-file-mutations__resolvers.md, docs/dry/dry-file-mutations__sets.md, docs/dry/dry-file-optimizer____init__.md, docs/dry/dry-file-optimizer___context.md, docs/dry/dry-file-optimizer__extension.md, docs/dry/dry-file-optimizer__field_meta.md, docs/dry/dry-file-optimizer__hints.md, docs/dry/dry-file-optimizer__join_taxonomy.md, docs/dry/dry-file-optimizer__lateral_fetch.md, docs/dry/dry-file-optimizer__nested_fetch.md, docs/dry/dry-file-optimizer__nested_planner.md, docs/dry/dry-file-optimizer__plans.md, docs/dry/dry-file-optimizer__predicates.md, docs/dry/dry-file-optimizer__selections.md, docs/dry/dry-file-optimizer__single_parent_fetch.md, docs/dry/dry-file-optimizer__walker.md, docs/dry/dry-file-orders____init__.md, docs/dry/dry-file-orders__base.md, docs/dry/dry-file-orders__factories.md, docs/dry/dry-file-orders__inputs.md, docs/dry/dry-file-orders__sets.md, docs/dry/dry-file-permissions.md, docs/dry/dry-file-registry.md, docs/dry/dry-file-relay.md, docs/dry/dry-file-resource_policy.md, docs/dry/dry-file-rest_framework____init__.md, docs/dry/dry-file-rest_framework__hook_context.md, docs/dry/dry-file-rest_framework__inputs.md, docs/dry/dry-file-rest_framework__resolvers.md, docs/dry/dry-file-rest_framework__serializer_converter.md, docs/dry/dry-file-routers.md, docs/dry/dry-file-scalars.md, docs/dry/dry-file-schema.md, docs/dry/dry-file-sets_mixins.md, docs/dry/dry-file-utils__policies.md, docs/dry/dry-file-views.md, docs/dry/dry-rule-already-registered-error-wording.md, docs/dry/dry-rule-child-queryset-alias-inheritance.md, docs/dry/dry-rule-generated-mutation-input-identity.md, docs/dry/dry-rule-globalid-decode-input-hardening.md, docs/dry/dry-rule-globalid-relation-pk-marker.md, docs/dry/dry-rule-globalid-setting-snapshot.md, docs/dry/dry-rule-logger-single-sourcing.md, docs/dry/dry-rule-mutation-error-envelope.md, docs/dry/dry-rule-mutation-input-reverse-map.md, docs/dry/dry-rule-one-sync-boundary.md, docs/dry/dry-rule-optimizer-execution-frame.md, docs/dry/dry-rule-orm-lookup-path-resolution.md, docs/dry/dry-rule-relation-instance-accessor.md, docs/dry/dry-rule-relation-kind-taxonomy.md, docs/dry/dry-rule-relay-node-name-decode.md, docs/dry/dry-rule-relay-node-target-guard.md, docs/dry/dry-rule-relay-node-type-stamp.md, docs/dry/dry-rule-relay-pk-suppression-read-mirror.md, docs/dry/dry-rule-seal-defect-code-wording.md, docs/dry/dry-rule-sealed-execution-queryset.md, docs/dry/dry-rule-shared-write-skeleton.md, docs/dry/dry-rule-subscription-per-event-error-masking.md, docs/dry/dry-rule-subsystem-clear-lifecycle.md, docs/dry/dry-rule-type-registry-definition-store.md, docs/dry/dry-rule-type-registry-enum-cache.md, docs/dry/dry-rule-type-registry-finalize-gate.md, docs/dry/dry-rule-type-registry-model-type-map.md, docs/dry/dry-rule-type-registry-pending-ledger.md, docs/dry/dry-rule-type-teardown-lifecycle.md, docs/dry/dry-rule-typed-globalid-decode.md, docs/dry/dry-rule-version-single-sourcing.md, docs/dry/dry-rule-write-relation-id-typing.md, examples/fakeshop/test_query/test_relation_deadline_api.py, honest_postfix.txt, honest_prefix.txt, scripts/check_truthful_reads.py, tests/test_check_truthful_reads.py, tests/utils/test_lazy.py, tests/utils/test_truth.py

Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-rest_framework__sets.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-testing____init__.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-testing___wrap.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-testing__client.md, docs/dry/dry-file-testing__relay.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-types____init__.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-types__base.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-types__converters.md, docs/dry/dry-file-types__definition.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-types__finalizer.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-types__relations.md, docs/dry/dry-file-types__relay.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-types__resolvers.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils____init__.md, docs/dry/dry-file-utils__canonical.md, docs/dry/dry-file-utils__connections.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +52 mid-item (registry baseline da5c1882 vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__context.md, docs/dry/dry-file-utils__converters.md, docs/dry/dry-file-utils__directives.md, docs/dry/dry-file-utils__errors.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__execution_mode.md, docs/dry/dry-file-utils__imports.md, docs/dry/dry-file-utils__input_values.md; docs/dry/dry-0_0_15.md grew +260 mid-item (relay baseline 04fd0769 vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__inputs.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +127 mid-item (resource_policy baseline e3af1821 vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__operation_lease.md, docs/dry/dry-file-utils__permissions.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +148 mid-item (routers baseline eb71162b vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__private_state.md, docs/dry/dry-file-utils__relations.md, docs/dry/dry-file-utils__sessions.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +91 mid-item (scalars baseline be73a504 vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__strings.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +163 mid-item (schema baseline 5ef09ed4 vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__typing.md, docs/dry/dry-file-utils__write_transaction.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +133 mid-item (sets_mixins baseline 56960386 vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); dirty + docs/dry/dry-file-utils__write_values.md
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +125 mid-item (auth/mutations baseline 8a53fa09 vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +58 mid-item (auth/queries baseline f26a7dff vs live; concurrent DRY work, untouched)
Drift: 2026-09-28 HEAD 0c0537e2dd94 (unmoved); docs/dry/dry-0_0_15.md grew +19 mid-item (auth/sessions baseline 5bdea138 vs live; concurrent DRY work, untouched)

Already itemized above, worked this run:

- `_django_patches.py`
- `_graphql_core_patches.py`
- `_strawberry_patches.py`
- `apps.py`
- `conf.py`
- `connection.py`
- `consumers.py`
- `error_policy.py`
- `exceptions.py`
- `keyset.py`
- `list_field.py`
- `permissions.py`
- `registry.py`
- `relay.py`
- `resource_policy.py`
- `routers.py`
- `scalars.py`
- `schema.py`
- `sets_mixins.py`
- `auth/mutations.py`
- `auth/queries.py`
- `auth/sessions.py`
- `auth/ integration`
- `extensions/debug.py`
- `extensions/error_policy.py`
- `extensions/operation_state.py`
- `extensions/resource_policy.py`
- `extensions/ integration`
- `filters/base.py`
- `filters/factories.py`
- `filters/inputs.py`
- `filters/sets.py`
- `filters/ integration`
- `forms/converter.py`
- `forms/inputs.py`
- `forms/resolvers.py`
- `forms/sets.py`
- `forms/ integration`
- `management/commands/inspect_django_type.py`
- `management/commands/ integration`
- `middleware/debug_toolbar.py`
- `middleware/ integration`
- `mutations/fields.py`
- `mutations/inputs.py`
- `mutations/operations.py`
- `mutations/permissions.py`
- `mutations/resolvers.py`
- `mutations/sets.py`
- `mutations/ integration`
- `optimizer/_context.py`
- `optimizer/extension.py`
- `optimizer/field_meta.py`
- `optimizer/hints.py`
- `optimizer/join_taxonomy.py`
- `optimizer/lateral_fetch.py`
- `optimizer/nested_fetch.py`
- `optimizer/nested_planner.py`
- `optimizer/predicates.py`
- `optimizer/selections.py`
- `optimizer/walker.py`
- `optimizer/ integration`
- `orders/base.py`
- `orders/factories.py`
- `orders/sets.py`
- `orders/ integration`
- `rest_framework/hook_context.py`
- `rest_framework/inputs.py`
- `rest_framework/resolvers.py`
- `rest_framework/serializer_converter.py`
- `rest_framework/sets.py`
- `rest_framework/ integration`
- `testing/client.py`
- `testing/ integration`
- `types/base.py`
- `types/converters.py`
- `types/finalizer.py`
- `types/relations.py`
- `types/relay.py`
- `types/resolvers.py`
- `types/ integration`
- `utils/canonical.py`
- `utils/connections.py`
- `utils/context.py`
- `utils/converters.py`
- `utils/directives.py`
- `utils/errors.py`
- `utils/execution_mode.py`
- `utils/imports.py`
- `utils/input_values.py`
- `utils/inputs.py`
- `utils/operation_lease.py`
- `utils/permissions.py`
- `utils/policies.py`
- `utils/private_state.py`
- `utils/querysets.py`
- `utils/relations.py`
- `utils/sessions.py`
- `utils/strings.py`
- `utils/typing.py`
- `utils/write_transaction.py`
- `utils/write_values.py`
- `utils/ integration`
- `Project integration`
- `Final gate`
