# Bug hunt: 0.0.15

Status: in-progress
Mode: defensive correctness review
Scope decision: maintainer approved defensive correctness review including baseline failures,
excluding autonomous vulnerability discovery and exploit reproduction. Earlier blocked notes
are historical; no completed hunt verdict is implied.
Run id: `0.0.15-bf02c227486c59da9677c5d5707279815dfa9353`
Baseline commit: `bf02c227486c59da9677c5d5707279815dfa9353`
Historical record: `docs/bug_hunt/bug_hunt-0_0_15-historical.md` (the Sep-3 97-item
campaign, Status complete; reconstructed 2026-09-21 from HEAD bytes + the verified
closeout patch after this active file replaced its path — read it, never this file, for
the historical verdicts).
Drift: 2026-09-19 HEAD bf02c227486c59da9677c5d5707279815dfa9353..bfaee91dcd332a5f86250fff90ab21b377bc674e
  (maintainer fast-forward onto main; 15 commits; uncommitted work preserved incl. staged/unstaged
  split; sole merge conflict a test-module docstring with both descriptions retained; no tests run
  during the fast-forward); dirty + 23 hunt-owned paths (10 production fixes, 11 package tests,
  1 live test row, this file) + DRY-agent paths (docs/dry/dry-0_0_15.md,
  docs/dry/dry-file-utils__querysets.md, ~60 untracked docs/dry/dry-file-*.md) + stray root scratch
  honest_prefix.txt honest_postfix.txt (resolvers stale re-pass honest captures; closeout cleanup).
Drift: 2026-09-19 mid-campaign concurrent dirt (not hunt-owned, never touched, never
  attributed): registry.py (+4), relay.py (+5), types/finalizer.py (+7), types/relay.py (+8),
  tests/base/test_init.py (+116), tests/optimizer/test_extension.py (+51),
  extensions/error_policy.py (+5) and list_field.py (+8) carry foreign hunks atop hunt-stale
  targets — re-hunts must attribute before editing.
Drift: 2026-09-21 Worker-0 resume: HEAD bfaee91d..bfaee91d (unchanged, baseline ancestor);
  dirty + hunt-ws/ (WT-root, 4 untracked w2-*.txt work products, Sep 20-21); item baseline
  e9f4c22d; staged entries (this file, tests/utils/test_querysets.py) are another session's
  index, untouched.
Drift: 2026-09-21 worktree migration (maintainer-authorized): campaign moved from the t3
  worktree (detached at bfaee91d by the authorized branch switch; read-only throughout,
  status byte-identical pre/post) to the main worktree (branch t3code/1cc21548 @ bfaee91d;
  HEAD unchanged, baseline bf02c227 ancestor re-confirmed). Moved 54 ledger-attributed
  paths (26 production incl. 2 foreign-filtered, 26 tests incl. 11 merged, 2 live) + this
  file (t3 worktree version; the t3 staged copy was 743+/176- stale, worktree
  authoritative; the main worktree's historical closeout preserved as scratch patch, see
  Current status) + hunt-ws/ + honest_prefix/postfix.txt. Excluded: foreign spec-015 hunks
  (3), foreign globalid docstring (1), all non-ledger t3 dirt (DRY-agent files, stray
  scratch, 9 non-ledger production files, 3 non-ledger test overlaps). T3 worktree left
  intact as the safety copy.
Drift: 2026-09-21 hunt relocated to worktree
  `/Users/riordenweber/.t3/worktrees/django-strawberry-framework/t3code-1cc21548`
  on branch `t3code/1cc21548` @ 69a25369 by Rio; main checkout clean of hunt paths;
  HEAD bfaee91d..69a25369 (1dd7d147 kanban live re-tiering, a01a2ab8 live re-tiering +
  committed hunt proxy-fixture rows, 69a25369 working-note clear); baseline commit
  bf02c227 unchanged (ancestor re-confirmed). Supersedes the worktree-migration note
  above (that move's direction is reversed).
Drift: 2026-09-21 ~22:45 HEAD 69a25369..24e6b4d3 (Rio fast-forward, 11 commits:
  9350eb8d, fee87ac4, 44712901, 357e5487, 1f68871a, ec0d21de, fa6d48f8, 9fb725c8,
  c87f4f98, 3c53842f, 24e6b4d3); hunt dirt re-applied 3-way, no conflicts; baseline
  commit bf02c227 unchanged (ancestor re-confirmed). Main rewrote 11 production
  paths: connection.py, error_policy.py, extensions/error_policy.py,
  extensions/resource_policy.py, list_field.py, optimizer/nested_planner.py,
  optimizer/walker.py, resource_policy.py, schema.py, utils/policies.py,
  utils/querysets.py. Every ITEM_BASELINE / target digest recorded at 69a25369 or
  earlier for those paths is stale; re-derived from 24e6b4d3 before trusting.
  Verified ticks converted to stale re-passes: connection.py (recorded 3c4d5dcb;
  hunt negative-cursor hunk intact inside main-rewritten `_consume_fallback`,
  worktree 9c5b8724 vs HEAD 4894f90f exactly the ledgered fix), error_policy.py
  (fa94fcd9 → HEAD 1a19cd7d, clean), extensions/resource_policy.py (recorded
  583bf460; ledgered charging fix intact atop the rewrite, worktree 2549591a vs
  HEAD 38801833 exactly the fix hunks), optimizer/nested_planner.py (recorded
  e69dbf5f; ledgered M2M gate intact, worktree 225011b6 vs HEAD b4dfd4a6 exactly
  the fix hunk), optimizer/walker.py (9b111ed9 → HEAD e8d80005, clean),
  resource_policy.py (647133d2 → HEAD 4b69e974, clean), schema.py (c2e1b748 →
  HEAD 19f90bf5, clean). Already-stale notes updated to new HEAD digests:
  extensions/error_policy.py (HEAD 7ee4e9dd; worktree d526a7bd adds only the
  concurrent DRY docstring hunk), list_field.py (HEAD 21380eb7; worktree 616ca7f6
  adds only the concurrent DRY docstring hunk). utils/policies.py (860b181f →
  HEAD 8c881c0a, clean) re-hunts fresh at the new digest; utils/querysets.py
  (96618fba → HEAD b68be0e3, clean, +251 main-side) still pending, hunts at the
  new digest. No tick kept silently: stale queue now 16.
Drift: 2026-09-21 ~22:45 evidence hygiene: 86 of the 96 `hunt-ws/w2-*expectation.txt`
  files this record cites no longer exist (Worker-0 recount: 96 unique citations,
  13 files present, 3 of them uncited; the handoff note said 70 — recount governs).
  Several `Cleanup:` lines promised retention until closeout. From here every
  verification keeps its expectation file in `hunt-ws/` until closeout, and
  `hunt-ws/` (1.4 GB, not gitignored) is trimmed at every item close.
Drift: 2026-09-22 ~08:45 HEAD 24e6b4d3..5ee86193 (Rio fast-forward, 4 commits:
  174a109c, 29ddc0a8, 3ad0dfd6, 5ee86193). The single overlapping dirty file
  (filters/sets.py) 3-way merged with no conflicts: both hunt hunks intact
  (the Meta.fields isinstance guard and the declared-filter multi-lookup
  rejection) and HEAD's two docstring lines present ("materialized queryset"
  -> "lazy queryset"); production diff is docstring-only, no behaviour
  changed; baseline commit unchanged. Zero ledger test files touched
  (file-level intersection of the fast-forward with every ledger test path is
  empty, so no ledgered node id lives in the rewritten test files and no hunt
  row could have been deleted without a conflict signal); both live hunt rows
  re-run focused green (2 passed) against the new library models + migration
  0006. optimizer/walker.py, optimizer/nested_planner.py and connection.py
  remain on the stale list from the previous fast-forward; this one adds no
  new stale production targets.
Drift: 2026-09-22 HEAD 5ee86193..ae52bdec (Rio fast-forward onto main, 11 commits:
  e5914bc4, 39811dab, f306459d, 2c66416e, b38184b3, b3458ee8, cb4415b7, 9518e484,
  c25a34e3, 4667db4f, ae52bdec; uncommitted hunt + DRY work carried 3-way, conflicts
  resolved by the maintainer; baseline bf02c227 ancestor re-confirmed by merge-base).
  Package: exactly 2 files, comment/docstring-only by diff content (filters/sets.py one
  comment line ~1708; utils/relations.py `instance_accessor` docstring ~703); reverse-applying
  main's per-file diff to the worktree bytes reproduces recorded c1a0f1b2 / 1cf81e58
  byte-exact (method: scratch copy + `patch -R` + `git hash-object` compare; YES/YES).
  Tests/examples: 56 paths — main's real-fakeshop-model re-tiering; tests/optimizer/conftest.py
  deleted (restore now in tests/conftest.py; zero references in record or tests, clean);
  async `django_db` now requires `transaction=True`; new migrations library 0007 /
  products 0003 (`Item` hold) / scalars 0002; 14 ledgered test files + test_schema.py
  (pending-scenario item-record nodes) touched — full inventory + focused 147/147 green
  in the resume Fold; RED decision test unchanged.
  Maintainer merge edits (not drift, preserved, never reverted): join_taxonomy Genre port
  (2/2 green); test_resolvers/test_converters re-tiering wins with live covers green;
  big_auto + relation-primary + unplanned-login package rows removed as superseded (all
  non-hunt by record grep; zero hunt tests removed).

## Cycle baseline

`git status --short` at generation. Every path below is concurrent work: never edited, reverted, tidied, or attributed to an item. Worker 0 appends the `CYCLE_BASELINE` stash object once at start and nothing afterwards.

Clean tree at generation.

CYCLE_BASELINE: `bf02c227486c59da9677c5d5707279815dfa9353` (`git stash create`
returned empty before regeneration; HEAD used). The maintainer authorized replacing the
historical progress file. No prior item verdict carries into this run.

## Package questions

No maintainer-authored probing questions were supplied. Explore the live source freely; shadow inputs are orientation only.

## How to hunt one item
Each file item uses one source file as its entry point into the live system;
scenario items own one cross-file contract. The target is narrow; the
investigation and root-cause fix cross files. `docs/bug_hunt/HUNT.md` is the
method; this brief is a reminder, not a substitute.

- Read the shadow overview and stripped source for baseline orientation, then
  read the complete live target. Shadow markers and stripped line numbers are
  never authoritative.
- Record the contract row for every boundary before probing it: boundary,
  failure class, promised wire shape, masking, rollback, absent unauthorized
  effects. A contract nobody can cite is reported blocked, never fixed.
- Trace callers, dependencies, state, framework hooks, tests, examples, and
  public contracts far enough to understand the target's real behavior. Clean
  layers often fail only when several reasonable assumptions stack together;
  hunt those interactions, not only suspicious local lines.
- Break things, break things, break things, inside the disposable workspace
  copy only: mutate throwaway state, force hostile sequences, interrupt
  lifecycles, and try to make every connected layer fail. A probe that imports
  the shared checkout or opens its database is invalid whatever it found.
- For every extreme, test the opposite extreme and then combine them across
  layers. Discharge every axis of the mandatory matrix. Try to disprove every
  candidate and record only confirmed defects.
- Every claim links to an evidence record: workspace path, imported package
  path, database target, exact command, source digests, collected and executed
  counts, the assertion proving the boundary was reached, a positive control.
- Do not clean up scratch probes, workspaces, or disposable state. Report every
  path and leave it intact so Worker 2 can replay it and Worker 0 can remove it
  only after the item is verified.
- Implement the root-cause fix at the layer that owns the broken invariant in
  the shared tree, attributing every hunk of a dirty path first, including
  connected files when required. Add a permanent behavioral test for every
  production fix at the strongest tier required by `AGENTS.md`.
- After edits run `uv run ruff check --fix .`, then `uv run ruff format .` last
  (`AGENTS.md` order governs; format last).
- Report evidence, changed files, tests, and validation to Worker 0. Do not edit
  this progress file; Worker 0 runs the mechanical checks, a fresh Worker 2
  verifies, and Worker 0 advances it.

## Hunt items

- [x] django_strawberry_framework/_boundary_ordering.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md
    - Prompt:
        - Use django_strawberry_framework/_boundary_ordering.py as the entry point. Read docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py and docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: workspace probe battery 9 passed + tests/test_views.py corroboration 26 passed; W2 replay + 7 attack probes passed; always-True/always-False mutation controls failed both ways for the intended reason with bytes restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-boundary-ordering-expectation.txt. Evidence: hunt-ws/boundary-ordering-verify/ records, target digest 197eea8e.
    - Cleanup: Removed hunt-ws/boundary-ordering, hunt-ws/boundary-ordering-verify; unrelated work preserved.

- [x] django_strawberry_framework/_cross_web_patches.py
    - Status: verified
    - Result: No bugs. Evidence: W1 battery 8 passed + oracle 15/15 + live 500/400 row 2/2; W2 replay + 11 attack probes passed; in-workspace decode-mutation control failed the live row for the intended reason with bytes restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-cross-web-patches-expectation.txt. Evidence: hunt-ws/cross-web-patches-verify/ records, target digest 6b3a7c35.
    - Cleanup: Removed hunt-ws/cross-web-patches, hunt-ws/cross-web-patches-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_cross_web_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_django_patches.py
    - Status: verified
    - Result: No bugs. Evidence: W1 battery 17 passed + 1 skipped (unconstructible shape with reason) + oracle 25/25; W2 replay + 10 attack probes passed; `__class__`-liar re-examined and confirmed non-defect (no feasible project shape); corrupted-body mutation control refused loud with bytes restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-django-patches-expectation.txt. Evidence: hunt-ws/django-patches-verify/ records, target digest ba98f585.
    - Cleanup: Removed hunt-ws/django-patches, hunt-ws/django-patches-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_django_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_graphql_core_patches.py
    - Status: verified
    - Result: No bugs. Evidence: W1 matrix 16 passed + unpatched leak control LEAK-CONFIRMED + oracle 10/10; W2 replay + 11 attack probes passed; own single-await mutation failed red for the intended reason with bytes restored byte-identical (one W1 env-probe path-literal failure judged non-product).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-graphql-core-patches-expectation.txt. Evidence: hunt-ws/graphql-core-patches-verify/ records, target digest 1cd579fb.
    - Cleanup: Removed hunt-ws/graphql-core-patches, hunt-ws/graphql-core-patches-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___graphql_core_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___graphql_core_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_graphql_core_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___graphql_core_patches.stripped.py and docs/shadow/current/django_strawberry_framework___graphql_core_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_request_body.py
    - Status: verified
    - Result: No bugs. Evidence: W1 battery 22 passed + `return False` control failing exactly the 2 over-limit rows + corroboration 204/204; W2 replay + 18 independent probes passed (244 combined); flipped fail-closed control failed 6 stream-family tests for the intended reason with bytes restored byte-identical; all 4 disproved candidates re-confirmed.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-request-body-expectation.txt. Evidence: hunt-ws/request-body-verify/ records, target digest a70571ff.
    - Cleanup: Removed hunt-ws/request-body, hunt-ws/request-body-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework___request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/_request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework___request_body.stripped.py and docs/shadow/current/django_strawberry_framework___request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_strawberry_patches.py
    - Status: verified
    - Result: No bugs. Evidence: W1 battery 30 passed + 11-failure mutation set for intended reasons (restored byte-identical) + oracle 43/43 + live 3/3; W2 replay + 22 attack probes passed; removed-RecursionError-clause control failed red for the intended reason with bytes restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-strawberry-patches-expectation.txt. Evidence: hunt-ws/strawberry-patches-verify/ records, target digest f77df349.
    - Cleanup: Removed hunt-ws/strawberry-patches, hunt-ws/strawberry-patches-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_strawberry_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/apps.py
    - Status: verified
    - Result: No bugs. Evidence: W1 battery 14 passed with positive controls + oracle 14/14; W2 replay + 8 attack probes passed; dropped-apply mutation control failed 17 for the intended reason with bytes restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-apps-expectation.txt. Evidence: hunt-ws/apps-verify/ records, target digest 8ae1a3a3.
    - Cleanup: Removed hunt-ws/apps, hunt-ws/apps-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Use django_strawberry_framework/apps.py as the entry point. Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/mutations.py
    - Status: verified
    - Iteration: 3. Re-opened: mutations/sets.py verification confirmed same-class residuals at `auth/mutations.py:230,238` (seal messages) + `:319` — producer-controlled holder, no upstream normalization. Prior verified verdict stands for all else; narrow re-pass queued (same hostile-`__name__` contract, `_safe_class_name` precedent).
    - Iteration: 4. Worker 1 stale re-pass: Fixed (7 mechanical label swaps, no logic change: seal rebind/delete, conflict declared/new comprehensions, register-exclusion model, bind ambiguity/no-type model; verdict degraded label throughout — display-only inside already-typed paths). Audit remainder: :1236/:1375/1376/:1381/1382 read package-built classes as materialize keys (not producer-controlled, out of class); :228/:236 `cls.__dict__` reads hit `type`'s descriptor under the fixed holder metaclass (no consumer dispatch). New shape found in-audit: `__name__` poisoned with a hostile `str` subclass escapes via `__format__` (seal sites) — reproduced + covered. +6 tests in `tests/auth/test_mutations.py` (+142 lines; tier `tests/auth/` — declaration-time label paths wire-unreachable). Failability: 5 failed pre-fix / 6 passed post-fix; honest byte-identical (8950557d both); shared 173 + live 46 passed; ruff + trailing-commas clean; banned-token grep clean. Out-of-scope observation (not touched): `auth/sessions.py:371` `type(exc).__name__` is the same textual shape in a separate verified item. Worker-0 mechanical checks pass (post-fix digests 0b5fdd30/262d2a6f == worktree; attribution clean — only item paths; prose scan clean). Concurrent work noted (not item-attributed, untouched): untracked root `honest_postfix.txt` (another session's scratch). Fresh Worker 2 re-verification dispatched.
    - Iteration: 5. Worker 2 verdict: revision-needed (expectation-first `-r2`, digest c0b550ed). Verified sub-results (do not regress): all 7 `__name__` sites TYPED post-fix with degraded labels; fail-without 5× RAW pre-fix; honest-identity `cmp` identical; 6 new tests 5-failed/1-passed pre-fix → 6 passed post-fix; tiers 173 + 46 green; audit remainder AGREED; degraded-label verdict CONFIRMED all 7; prose + ruff clean. Challenge in the same function: `derive_register_fields` line 1056 renders `{protected!r}` where `protected` holds producer-controlled `USERNAME_FIELD`/`REQUIRED_FIELDS` values — a `str`-subclass field name with raising `__repr__` escapes raw `RuntimeError` (repro `w2_probe_hostile_value.py` in `hunt-ws/auth-mutations-stale-verify`, left intact). Same bug class, same raise, same owner/line: safe-coerce the value labels + 1 test alongside the 6. sessions.py:371 assessment: REFUTED as same-class lead (labels the exception's own class, no consumer-`__name__` route) — no action, that item stands verified. Item back to Worker 1 with workspaces intact; shared tree untouched by W2.
    - Iteration: 6. Worker 1 follow-up fix for the W2 challenge (same function, same raise, same owner/line): `{protected!r}` → per-element `_safe_arg_repr` join (whole-list `repr()` would dispatch to the hostile element and collapse the whole label; `_safe_text` would strip quotes and change honest bytes; `_safe_arg_repr("is_staff")` reproduces list-`repr` grammar byte-identically, pinned by the existing `_PROTECTED_FIELD_REJECT` regex row) + 1 test `test_derive_register_fields_hostile_field_value_stays_typed` alongside the 6. Failability: new test red pre-fix / green post-fix (WS-only revert, `cmp`-identical restore); honest `_PROTECTED_FIELD_REJECT` row green both ways; shared `test_mutations.py` 99 + `tests/auth/` 174 passed; ruff + trailing-commas clean; banned-token grep clean. Worker-0 mechanical checks pass (post-fix digests 200805d2/8ef261eb == worktree; attribution clean — only item paths; prose scan clean). Fresh Worker 2 re-verification dispatched.
    - Iteration: 7. Worker 2 verified (delta expectation `-r3`, digest 5c01ecc2): fresh-WS original-probe replay TYPED post-fix; one-line-only revert → RAW ESCAPE (load-bearing proven); restored `cmp`-identical; honest `['is_staff']` grammar independently proven byte-identical to list-`repr`; targeted 13 + full file 99 + dir 174 + live 46 green, zero red. No-regression on all iteration-5 sub-results (7 sites still safe; audit remainder holds by fresh trace). Verdict-on-fix: right owner, root-cause label swap, per-element renderer correct, tier correct.
    - Result: No bugs (iterations 1–2) + stale `__name__` residuals fixed (iterations 3–4: 7 sites + 6 tests) + value-label residual fixed (iterations 5–7: 1 site + 1 test). Files changed: django_strawberry_framework/auth/mutations.py (7 safe-class swaps + 1 safe-value join) + tests/auth/test_mutations.py (7 hostile tests).
    - Verification: Passed (iterations 2 + 5 + 7). Expected-before-diagnosis: hunt-ws/w2-auth-mutations-expectation.txt + -r2 + -r3. Evidence: hunt-ws/auth-mutations-stale-verify2/ records, post-fix digest 200805d2.
    - Iteration: 8. Fast-forward drift check 2026-09-19: production digest 200805d2 still matches;
      main-side test edits are adjacent (+21 logout signal-failure test, no overlap); all 7 hunt
      hostile tests intact. Focused re-run `-k hostile` 12 passed in shared tree (7 hunt + 5
      pre-existing hostile rows). Verdict stands.
    - Cleanup: Removed hunt-ws/auth-mutations, hunt-ws/auth-mutations-verify, hunt-ws/auth-mutations-stale, hunt-ws/auth-mutations-stale-verify, hunt-ws/auth-mutations-stale-verify2; unrelated work preserved.
    - Result: No bugs. Evidence: W1 matrix 23 passed (axis-6 isolation with forbidden-row absence) + oracles 167 package + 46 live; W2 replay + 9 attack probes passed (incl. register post_save-boom atomicity, save-side IntegrityError race, login/logout durability outages); `if True:` / message-mutation controls failed for intended reasons with bytes restored byte-identical. Shared-tree `cp` incident corroborated harmless by both workers and Worker-0.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-auth-mutations-expectation.txt. Evidence: hunt-ws/auth-mutations-verify/ records, target digest dbe64995.
    - Cleanup: Removed hunt-ws/auth-mutations, hunt-ws/auth-mutations-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/mutations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py and docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/queries.py
    - Status: verified
    - Result: No bugs. Evidence: W1 battery 15 passed (isolation incl. zero-query revoke read) + oracles 23 + 46 live; W2 replay + 11 independent probes passed (lazy-user outage propagation, gate-first ordering, all-5 anonymity shapes, non-contained error propagation, async bridge); gate-skipping mutation control failed red for the intended reason with bytes restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-auth-queries-expectation.txt. Evidence: hunt-ws/auth-queries-verify/ records, target digest 5c59ba75.
    - Cleanup: Removed hunt-ws/auth-queries, hunt-ws/auth-queries-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/queries.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py and docs/shadow/current/django_strawberry_framework__auth__queries.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/sessions.py
    - Status: verified
    - Result: No bugs. Evidence: W1 matrix 40 passed (shared-scope single-lock proof, capability-flip immediacy) + oracle 52 + live 46; W2 replay + 17 attack probes passed (reentrancy deadlock by design, cancelled-waiter propagation, subclass capability, 3x2 capability matrix); fail-open/capability/login_supported mutations failed for intended reasons with bytes restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-auth-sessions-expectation.txt. Evidence: hunt-ws/auth-sessions-verify/ records, target digest fad7feb8.
    - Cleanup: Removed hunt-ws/auth-sessions, hunt-ws/auth-sessions-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/conf.py
    - Status: verified
    - Result: No bugs. Evidence: W1 matrix 44 passed + oracle 64/64; W2 replay + 11 independent probes passed (119 combined); `plain.get(dependency, True)`→`False` control failed 1 new + 5 oracle tests red, restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-conf-expectation.txt. Evidence: hunt-ws/conf-verify/ records, target digest c6ad46aa.
    - Cleanup: Removed hunt-ws/conf, hunt-ws/conf-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Use django_strawberry_framework/conf.py as the entry point. Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/connection.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (fee87ac4 OrderSet seal at the connection field + c87f4f98 shared sidecar seal; recorded post-fix digest 3c4d5dcb obsolete, HEAD now 4894f90f). Prior verified verdict stands for the old digest only. Hunt negative-cursor hunk intact inside main-rewritten `_consume_fallback` (worktree 9c5b8724 vs HEAD exactly the ledgered fix: import + 2 helpers + branch hook). Re-pass queued at the new bytes: re-prove the negative-cursor rejection against the sealed pipelines + hunt the new sidecar-seal surface (filter/order arms, routing snapshot, visibility-policy asymmetry).
    - Iteration: 4. Worker 1 stale re-pass dispatched 2026-09-22, ITEM_BASELINE 3c00404f, workspace hunt-ws/connection-stale-r1; worktree 9c5b8724 vs HEAD 4894f90f exactly the ledgered fix (re-confirmed), tests b950c960 vs HEAD dcf1b382 (ledgered 4-node test). Scope per Iteration 3.
    - Iteration: 5. Prior stale W1 dispatch (baseline 3c00404f) died on provider 429 with the Worker-0 session 2026-09-22 05:11 before reporting; its created workspace (no probes on disk) is retained as UNVERIFIED orientation only, treated as unused. Fresh Worker 1 dispatched 2026-09-22 14:14 UTC, ITEM_BASELINE 706f2219, workspace hunt-ws/connection-stale-r1 (rebuild, exclude hunt-ws); worktree 9c5b8724 vs HEAD 4894f90f re-confirmed exactly the ledgered fix by digest, tests b950c960 vs HEAD dcf1b382. Same scope as Iteration 3.
    - Iteration: 6. Worker 1 stale re-pass reported No bugs (5 contract rows R0-R4; 16-probe battery green default + floor cells; oracles 182 + 88 live; biting guard-removal control restored cmp-identical; ledgered fix intact + load-bearing; 3 candidates rejected). Zero shared-tree edits; no permanent test owed. Worker-0 mechanical checks pass (item diff vs 706f2219 empty; worktree 9c5b8724 + tests b950c960 == dispatch == WS; probe digest 7c2ba4f9 on disk; collection 16 exact; no nested hunt-ws; sharded/PG honestly unverified). One out-of-fence observation (apply_filterset_sync None-guard lead, no contract row, direct-call-only, mislabeled target status) rides the report for W2 judgment — no stale trigger. Report /tmp/w1-connection-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/connection-stale-verify, expectation-first.
    - Iteration: 7. Worker 2 verified (expectation-first `hunt-ws/w2-connection-stale-expectation.txt` ebe806a7, full R0-R4 agreement, no contradiction): fresh-WS replay 16/16 both cells + oracles 182 + 88 live; own guard-hook-removal control failed N1/N2/N4/N5 silent, restored cmp-identical; 19/19 independent attacks both cells (6 first-pass reds all proven probe bugs); ledgered fix re-derived exact + load-bearing; R1 windowed leg re-derived; sharded/PG stays honestly unverified (multi-DB pin unauthorized + wouldn't prove this arm); out-of-fence None-guard observation judged correctly non-routed (real at code level, no contract row, direct-call-only; W1's "pending" label wrong but no re-open warranted); item diff 0 bytes; ruff clean.
    - Result (stale re-pass): No bugs. The ledgered negative-cursor fix holds against the sealed pipelines; the sidecar-seal surface (filter/order arms, routing snapshot, visibility policy) holds.
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-connection-stale-expectation.txt. Evidence: hunt-ws/connection-stale-verify/ records, worktree digest 9c5b8724.
    - Cleanup (stale re-pass): Removed hunt-ws/connection-stale-r1, hunt-ws/connection-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Result: Fixed Low. Files changed: django_strawberry_framework/connection.py (`_offset_cursor_prefix`, `_reject_negative_offset_cursor`, `_consume_fallback` hook) + tests/test_connection.py (`test_consumer_resolver_sequence_negative_cursor_raises_graphql_error`, 4 nodes). Validation: pre-fix WS 4 failed wrong-rows-not-error, post-fix 4 passed, bytes restored byte-identical; W2 attack battery 8 passed (unit reject matrix, minted-cursor slicing, QuerySet provenance, after+before combos); neighbors 208 + live 50 + 3 regression passed.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-connection-expectation.txt. Evidence: hunt-ws/connection-verify/ records, post-fix digest 3c4d5dcb. Tier `tests/` correct (list/tuple resolver shape unreachable from shipped queries); owner `_consume_fallback` tail correct; Low concurred; diff hygiene clean (path::Symbol, ASCII-only, ruff clean).
    - Cleanup: Removed hunt-ws/connection, hunt-ws/connection-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Use django_strawberry_framework/connection.py as the entry point. Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/consumers.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-19: main-side fast-forward changed the target
      (recorded digest 18f3ea16, current 936210e2; delta 6 lines). Prior verified verdict stands
      for the old digest only; re-hunt queued at the new digest before the gate.
    - Iteration: 4. Worker 1 stale re-hunt dispatched 2026-09-22, ITEM_BASELINE 91307d53, workspace hunt-ws/consumers-stale-r1; target 936210e2 stable since Sep-20 and clean vs HEAD (fast-forward untouched this file); tests/test_consumers.py 9e8ef0d5 clean vs HEAD. Scope: the 6-line delta (3+/3-) + re-proof of the prior verdict's load-bearing rows at the new bytes; full re-hunt not warranted — prior No-bugs verdict stands for all unchanged behavior.
    - Iteration: 5. Prior stale re-hunt W1 dispatch (baseline 91307d53, workspace hunt-ws/consumers-stale-r1) died on provider error before building its workspace (path absent — nothing to retain). Fresh Worker 1 dispatched 2026-09-22 ~08:45, ITEM_BASELINE 3c00404f, workspace hunt-ws/consumers-stale-r1; target 936210e2 + tests 9e8ef0d5 re-confirmed == HEAD. Same scope: the 6-line delta + re-proof of the load-bearing rows at the new bytes.
    - Iteration: 6. Worker 1 stale re-pass reported No bugs (delta confirmed exactly the recorded 3+/3- via ffce6f29, all module-docstring; AST-identical with docstrings stripped; R1-R4 + R0 verified behaviorally with biting controls: 14/14 delta probes; regression anchor 114 + 212 + 69 green; live sibling 97 passed + 3 pre-existing env fixture errors reproduced identically in shared tree; plain-schema candidate rejected by contract citation at its owner). Zero shared-tree edits; no permanent test owed. Worker-0 mechanical checks pass (item diff empty; target 936210e2 + tests 9e8ef0d5 == HEAD; probe digest 5562fc5d on disk; old blob 18f3ea16 confirmed; delta 6 lines; no nested hunt-ws; test_00 anchor asserts WS import + prints DB; controls biting; sharded/PG/floor listed unverified). Report /tmp/w1-consumers-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/consumers-stale-verify, expectation-first.
    - Iteration: 7. Worker 2 verified the stale re-pass (expectation-first `hunt-ws/w2-consumers-stale-expectation.txt`, full R0-R4 agreement): fresh-WS replay 14/14 + oracles 114/212/69 exact + live 97+3 same env errors; selective _masked_return control (05/06 red, 04/10 green) restored byte-identical; 11/11 independent attacks (whole-package census, mutation twins, hook-shape + DEBUG arms, delegation edges, behavioral plain-schema boundary); cells honestly unverified; no test owed with owner pins; item diff empty; all 4 digests re-confirmed.
    - Result (stale re-pass): No bugs. The 6-line docstring delta is behavior-neutral and true; prior No-bugs verdict carries to digest 936210e2.
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-consumers-stale-expectation.txt. Evidence: hunt-ws/consumers-stale-verify/ records.
    - Cleanup (stale re-pass): Removed hunt-ws/consumers-stale-r1, hunt-ws/consumers-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Result: No bugs. Evidence: W1 matrix 43 passed (T1-T8 interruption suite) + unshielded-close / skipped-aclose controls red for intended reasons (restored hash-identical) + oracles 114 + 208; W2 replay + 19 attack probes passed; bound-2→1 mutation control failed retry/T2 red, restored hash-identical, 62/62 green. Communicator django_db/wait contract confirmed in WS runs.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-consumers-expectation.txt. Evidence: hunt-ws/consumers-verify/ records, target digest 18f3ea16.
    - Cleanup: Removed hunt-ws/consumers, hunt-ws/consumers-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__consumers.stripped.py
    - docs/shadow/current/django_strawberry_framework__consumers.overview.md
    - Prompt:
        - Use django_strawberry_framework/consumers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__consumers.stripped.py and docs/shadow/current/django_strawberry_framework__consumers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/error_policy.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (9350eb8d canonical-copy default path + exact-type `__post_init__` tests; recorded digest fa94fcd9 obsolete, HEAD now 1a19cd7d, worktree clean). Prior verified verdict stands for the old digest only. Re-pass queued at the new bytes (canonical-copy semantics, subclass-closing, fallback seams).
    - Iteration: 4. Worker 1 stale re-pass dispatched 2026-09-22, ITEM_BASELINE 3c00404f, workspace hunt-ws/error-policy-stale-r1; target 1a19cd7d clean vs HEAD (re-confirmed), tests/test_error_policy.py d7c467dc. Scope per Iteration 3.
    - Iteration: 5. Prior stale W1 dispatch (baseline 3c00404f) died on provider 429 with the Worker-0 session 2026-09-22 05:11 before building its workspace (path absent — nothing to retain). Fresh Worker 1 dispatched 2026-09-22 14:14 UTC, ITEM_BASELINE 706f2219, workspace hunt-ws/error-policy-stale-r1; target 1a19cd7d + tests d7c467dc re-confirmed == HEAD. Same scope as Iteration 3.
    - Iteration: 6. Worker 1 stale re-pass reported No bugs (6 contract rows C1-C6; 45-probe battery + 8 disproof probes green; oracles 69 + 70 live + 24 neighbor; floor-310 subset green; 2 biting WS-only controls restored cmp-identical; rewrite delta confirmed exactly 6 semantic lines; 4 candidates disproved). Zero shared-tree edits; no permanent test owed. Worker-0 mechanical checks pass (item diff empty; target 1a19cd7d + tests d7c467dc == HEAD == WS; probe digests 511ef8ab/21520002 on disk; collection 53 = 45 + 8 exact; test_00 anchor asserts WS import; WS DB inside workspace; no nested hunt-ws; no stray files; sharded/PG inapplicable-by-construction for W2 to judge). Report /tmp/w1-error-policy-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/error-policy-stale-verify, expectation-first.
    - Iteration: 7. Worker 2 verified (expectation-first `hunt-ws/w2-error-policy-stale-expectation.txt`, C1-C6 all met, no contradiction): fresh-WS replay 52/52 (test_00 anchor excluded — hardcodes W1's WS name; substance re-printed) + oracles 69 + 24 + 70 live; 23/23 independent attacks; biting constant-correlation-id control failed exactly the 8 id-touching assertions, restored cmp-identical; all 5 digests match; rewrite delta re-derived from `git show 9350eb8d` as exactly the 6 semantic lines + canonicalization + seam re-pointing; sharded/PG judged inapplicable-by-construction; all 8 axes judged discharged.
    - Result (stale re-pass): No bugs. The 9350eb8d rewrite (canonical-copy default path + exact-type `__post_init__`) holds; prior No-bugs verdict carries to digest 1a19cd7d.
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-error-policy-stale-expectation.txt. Evidence: hunt-ws/error-policy-stale-verify/ records.
    - Cleanup (stale re-pass): Removed hunt-ws/error-policy-stale-r1, hunt-ws/error-policy-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Result: No bugs. Evidence: W1 battery 44 passed + isinstance-mutation control failing exactly the 2 int-enabled probes (restored byte-identical) + oracles 61 + live 38; W2 replay + 19 independent probes passed; own isinstance-mutation control failed 1 new + 5 oracle tests red, restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-error-policy-expectation.txt. Evidence: hunt-ws/error-policy-verify/ records, target digest fa94fcd9.
    - Cleanup: Removed hunt-ws/error-policy, hunt-ws/error-policy-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/exceptions.py
    - Status: verified
    - Result: No bugs. Evidence: W1 31 render-safety checks green + oracle 37/37 + except-BaseException-removal control escaped raw (restored byte-identical); W2 own 18-probe battery + oracle 37/37 + 55/55 combined green; C1 re-examined with correct patch target (genuine path has no SyncMisuseError raiser); same control failed red with xdist INTERNALERROR on the KeyboardInterrupt test, restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-exceptions-expectation.txt. Evidence: hunt-ws/exceptions-verify/ records, target digest e06b0b7f.
    - Cleanup: Removed hunt-ws/exceptions, hunt-ws/exceptions-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Use django_strawberry_framework/exceptions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/extensions/debug.py
    - Status: verified
    - Result: No bugs. Evidence: W1 matrix 48 passed + `_MAX_SQL_ROWS 100→0` control red at the cap oracle (restored sha-identical) + oracles 72 + 136-group; W2 replay + 60 independent probes passed (180 combined); own `is True`→`bool(...)` gate mutation failed 2 gate corners red, restored hash-identical. W1's "136" grouping not reproduced under any grouping; all superset groupings green — grouping-description gap, not product gap.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-extensions-debug-expectation.txt. Evidence: hunt-ws/extensions-debug-verify/ records, target digest bf25c146.
    - Cleanup: Removed hunt-ws/extensions-debug, hunt-ws/extensions-debug-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/debug.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/extensions/error_policy.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-19: main-side fast-forward changed the target
      (recorded digest baea073f, current 16f47547; delta 70 lines). Prior verified verdict stands
      for the old digest only; re-hunt queued at the new digest before the gate. Note 2026-09-20:
      concurrent session still editing (digest moved again to bd763bcc) — re-hunt waits for stability.
    - Iteration: 4. Fast-forward 69a25369..24e6b4d3 (9350eb8d) rewrote the target again (HEAD now 7ee4e9dd; worktree d526a7bd adds only the concurrent DRY docstring hunk — re-hunt attributes-first, never touches it). Re-hunt runs at HEAD 7ee4e9dd once the concurrent editing settles.
    - Iteration: 5. Settled: worktree d526a7bd vs HEAD 7ee4e9dd is exactly the recorded concurrent DRY docstring hunk (+4/-1, stable since 2026-09-21 ~22:45). Fresh Worker 1 dispatched 2026-09-22 14:30 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/ext-error-policy-stale-r1; no dedicated tests/extensions/test_error_policy.py — oracles shared (tests/test_error_policy.py d7c467dc, now free after that item verified, + live). Scope: the 9350eb8d rewrite at the new bytes + re-proof of the prior verdict's load-bearing rows; attribution-first, never touches the DRY hunk.
    - Iteration: 6. Worker 1 stale re-pass reported No bugs (8 contract rows R1-R8; 42-probe battery green default + floor; oracles 69 + 70 live + 4 router; 3 biting controls; rewrite delta re-derived as exactly 6 semantic lines; 6 candidates disproved/characterized with 1 robustness row). Zero shared-tree edits; DRY hunk untouched; no permanent test owed. Worker-0 mechanical checks pass (item diff vs c9e39d31 empty; target d526a7bd == dispatch == WS; probe digest 3ccfbf6a on disk; collection 42 exact; REACHED asserts present; no nested hunt-ws; WS DB inside; sharded/PG inapplicable-by-construction for W2 to judge). Report /tmp/w1-ext-error-policy-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/ext-error-policy-stale-verify, expectation-first.
    - Iteration: 7. Worker 2 verified (expectation-first `hunt-ws/w2-ext-error-policy-stale-expectation.txt` 650b683c, full R1-R8 agreement, no contradiction): fresh-WS replay 41/41 behavioral (test_00 fails only on W1's hardcoded WS-name literal, its stdout proving isolation) + oracles 69 + 70 live + 4 router; own 40-node attack battery green both cells; WS-only gate-inversion control failed 27 with raw-secret-on-wire signature, restored cmp-identical; rewrite delta re-derived as exactly the 6 DEFAULT-to-PRIVATE lines with zero DEFAULT reads left; sharded/PG judged inapplicable-by-construction (grep-proven: no db/connections/alias surface); all 4 robustness rows concurred with own evidence; axis 3 confirmed surfaceless; item diff 0 bytes; ruff clean.
    - Result (stale re-pass): No bugs. The 9350eb8d fallback-seam re-pointing holds at HEAD 7ee4e9dd; prior No-bugs verdict carries to worktree digest d526a7bd (HEAD + the untouched concurrent DRY docstring hunk).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-ext-error-policy-stale-expectation.txt. Evidence: hunt-ws/ext-error-policy-stale-verify/ records.
    - Cleanup (stale re-pass): Removed hunt-ws/ext-error-policy-stale-r1, hunt-ws/ext-error-policy-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Result: No bugs. Evidence: W1 matrix 34 passed + `_is_unexpected` True→False control failing 4 for intended reasons (restored digest-identical, 95/95 green) + oracles 61 + live 38 + router seam 4; W2 replay + 8 attack probes passed (located_error masking, DEBUG per-event flip, copy isolation, non-result exclusion); own True→False control failed 2 red, restored byte-identical, 42/42 green.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-extensions-error-policy-expectation.txt. Evidence: hunt-ws/extensions-error-policy-verify/ records, target digest baea073f.
    - Cleanup: Removed hunt-ws/extensions-error-policy, hunt-ws/extensions-error-policy-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/extensions/operation_state.py
    - Status: verified
    - Iteration: 1. Worker 1 dispatched with item baseline c0a1a6f3, workspace hunt-ws/operation-state; reported No bugs (13-probe battery + 56-node oracle suite = 69 passed; managed-ignore-disable control failed exactly at forged-graph retention, restored byte-identical; 5 candidates disproved). Worker-0 mechanical checks pass; fresh Worker 2 dispatched. Concurrent work flagged by W1 (not item-attributed, untouched): `?? docs/dry/dry-file-_cross_web_patches.md`.
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-operation-state-expectation.txt`; W1 battery 13 + oracle 56 replayed green in fresh `hunt-ws/operation-state-verify`; 7 independent attack probes passed; lease-close-loop-removal control failed exactly the closure-discriminating rows, restored byte-identical). HEAD moved f8a75753 -> 9031cb3d during verification (concurrent test-tier moves + seal/resource-policy fixes); Worker-0 confirms the verdict stands: target digest b2674a22 identical in shared tree, both workspaces and HEAD blob; the schema.py delta is docstring-prose-only (no behavior change to the runner path); other HEAD deltas (permissions, top-level resource_policy, types/resolvers, utils/querysets seal) touch none of R1-R8's machinery.
    - Result: No bugs. Evidence: W1 69 passed + control; W2 replay + 7 attack probes passed; control failed 4 rows for the intended reason, restored byte-identical.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-operation-state-expectation.txt. Evidence: hunt-ws/operation-state-verify/ records, target digest b2674a22.
    - Cleanup: Removed hunt-ws/operation-state, hunt-ws/operation-state-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__extensions__operation_state.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__operation_state.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/operation_state.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__operation_state.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__operation_state.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/extensions/resource_policy.py
    - Status: verified
    - Iteration: 4. Re-opened 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (9350eb8d canonical-copy unconfigured read; recorded post-fix digest 583bf460 obsolete, HEAD now 38801833). Prior verified verdict stands for the old digest only. Ledgered directive-charging fix intact atop the rewrite (worktree 2549591a vs HEAD exactly the fix hunks: 2 helpers + 5 call sites + imports). Re-pass queued at the new bytes (charging fix vs canonical-copy read).
    - Iteration: 5. Fresh Worker 1 dispatched 2026-09-22 14:30 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/ext-resource-policy-stale-r1; worktree 2549591a vs HEAD 38801833 re-confirmed exactly the ledgered fix by digest, tests a89ac120 vs HEAD b9db7c2f, live 9cb2bb5e vs HEAD bd32df87. Same scope as Iteration 4.
    - Iteration: 6. Worker 1 stale re-pass reported Fixed Low (D1: spread-site directives on unknown/cyclic fragments escaped charging — spread charge ran below the unresolvable/cyclic guard while `_referenced_variables` collected above its own; fix moves the spread-site charge above the guard + comment + docstring refinement; scope (a) re-proven incl. `is _PACKAGE_RESOURCE_POLICY` pin, scope (b) canonical-copy surface holds) + 4 permanent tests (3 unit + 1 live). Files changed: extensions/resource_policy.py (d83a45eb) + tests/test_resource_policy.py (04bb52b6) + live test_resource_policy_api.py (3760eb99). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the fix + 4 tests; all 5 digests match claims incl. probe 3dc51f38; collection 48 exact; no nested hunt-ws; ruff + trailing-commas + banned-word + pragma scans clean — re-run by Worker-0 on touched paths; W1's check-only-instead-of---fix noted, outcome-equivalent since all pass; failability claimed 4/4 red pre-fix for W2 to re-prove; O1/O2/O3 + inapplicability ride for W2 judgment). Report /tmp/w1-ext-resource-policy-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/ext-resource-policy-stale-verify, expectation-first.
    - Iteration: 7. Worker 2 verified (expectation-first `hunt-ws/w2-ext-resource-policy-stale-expectation.txt` 88299f3d, full R0-R5 + D1 agreement, zero contradiction): fresh-WS replay 47/47 behavioral (test_00 dispensation as before) + oracles 299 + 146 live; WS-only production revert → 4801cf2c with d31-d34 + all 4 permanent tests failing `DID NOT RAISE`, restored cmp-identical; 26/26 attacks + 2 O-row probes green incl. exact-count double-charge pins (moved charge cannot double-count; definition fires once per expansion); fix comment's single-conversion claim re-proven; O1 concurred-as-framed (specified filter, narrowing is a maintainer decision), O2/O3 confirmed pre-existing robustness rows; Low concurred (plus pre-parse token-scan cap argument); W1's 320/145/492 counts corrected as report errata (measured 299/146/492-decomposed, all green); tiers + owner + compat confirmed; gates clean.
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/extensions/resource_policy.py (spread-site charge above the unresolvable/cyclic guard + comment + docstring clause) + tests/test_resource_policy.py (3 unit tests) + examples/fakeshop/test_query/test_resource_policy_api.py (1 live row).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-ext-resource-policy-stale-expectation.txt. Evidence: hunt-ws/ext-resource-policy-stale-verify/ records, post-fix digest d83a45eb.
    - Cleanup (stale re-pass): Removed hunt-ws/ext-resource-policy-stale-r1, hunt-ws/ext-resource-policy-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 1. Worker 1 dispatched with item baseline 08efb685, workspace hunt-ws/extensions-resource-policy; reported Fixed Low (directive argument values + unread variable defaults never charged while validation converts them pre-execution). Fix at owner `extensions/resource_policy.py::_charge_directive_values` + `_referenced_variables` (calls at all five directive sites incl. unknown fields; unread defaults charged once at definition via `type_from_ast`) + `charge_document` docstring; permanent tests `tests/test_resource_policy.py` (7 unit tests) + live `test_query/test_resource_policy_api.py` (`/rp-values/` row). Failability: pre-fix 6 failed/1 passed (digest 52084078), post-fix 7/7 (digest 583bf460); shared focused runs 295 + 144 + 189 passed; ruff format/check + trailing-commas clean. Worker-0 mechanical checks pass (pre-fix digest == HEAD blob; post-fix digests == worktree; attribution clean — target untouched at HEAD; prose rules clean; W1's editable-install invalid mode caught via `tests/test_which_pkg.py` and discarded, valid runs via `python -m`). Wall times reported imprecisely (`<30s` each) — Worker 2 to re-measure. Fresh Worker 2 dispatched.
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-extensions-resource-policy-expectation.txt`, digest 644de62f, no contradiction): fresh `hunt-ws/extensions-resource-policy-verify` imports inside `$WS`; replay 6/6 green post-fix (0.314s) vs directive-literal ADMITTED pre-fix; 7/7 bypass admissions pre-fix; 5/5 attack probes green (used/unused parity + no double-charge, all five sites, built-in widths, inline==spread + cyclic termination, mutation + per-operation binding); permanent tests fail-without-fix (6 unit + live row red), restored byte-identical (sha256 2c4005fa both trees), 7/7 green; focused suites re-measured precisely (295 in 9.087s, 144 in 24.483s, 189 in 4.159s).
    - Result: Fixed Low. Files changed: django_strawberry_framework/extensions/resource_policy.py (`_charge_directive_values`, `_referenced_variables`, `charge_document` hook + docstring) + tests/test_resource_policy.py (7 unit tests) + examples/fakeshop/test_query/test_resource_policy_api.py (live `/rp-values/` row).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-extensions-resource-policy-expectation.txt. Evidence: hunt-ws/extensions-resource-policy-verify/ records (`w2_replay.py` 9f773d94, `w2_prefix_bypass.py` 66c12326, `w2_attack.py` 4a1e55b0), post-fix digest 583bf460. Tier correct (custom-directive shapes unit, built-in shape live); owner `charge_document` correct; top-level resource_policy.py diff 0 bytes; Low concurred; prose clean.
    - Iteration: 3. Fast-forward drift check 2026-09-19: production digest 583bf460 still matches;
      main-side edits to the live test file are additive mounts the hunt row uses (`/rp-values/`
      probe views); hunt hunk intact (`git diff HEAD` shows only the +22 row). Focused re-run
      `test_directive_arguments_are_charged_as_input_nodes` 1 passed in shared tree. Verdict stands.
    - Cleanup: Removed hunt-ws/extensions-resource-policy, hunt-ws/extensions-resource-policy-verify; unrelated work preserved.
    - Iteration: 8. Fresh Worker 1 dispatched 2026-09-23 UTC, ITEM_BASELINE 9d0cdf64, workspace hunt-ws/5e-rp-prose (bounded prose revision: [5e] row 2, tests/test_resource_policy.py :3011 "proves the fix reaches a real request" test-docstring provenance; test-only — production d83a45eb + live file untouched). W2 verification follows in-unit.
    - Iteration: 9. Worker 1 revision landed (test-docstring-only +2/-2: "proves the fix reaches a real request" -> "this row runs on the shipped probe schema"; tests 04bb52b6 -> e18a7d06, production d83a45eb + live 801d17ae untouched). Worker-0 mechanical checks pass (item diff vs 9d0cdf64 exactly the hunk; old phrase count 0; focused 1 green — re-run by Worker-0; ruff check + format clean — re-run by Worker-0; no new pragma). Note: W1's ledger shows an out-of-role `git stash create` (harmless — writes no ref; baselines remain Worker-0-minted). Fresh Worker 2 verification dispatched (ITEM_BASELINE 0169b69a, workspace hunt-ws/5e-rp-prose-verify).
    - Iteration: 10. Worker 2 VERIFIED the prose revision (expectation-first, K1-K6 all PASS: exact hunk; production + live diffs empty; new prose timeless + each claim tied to the test body/helpers; independent co_code proof over the whole module + reverse-apply failability to 04bb52b6; touched test green + module 299 collected clean; ruff clean; W1 report audited — ZERO discrepancies). Shared tree never edited by W2 (fences re-hashed e18a7d06/d83a45eb/801d17ae; fence-vs-0169b69a empty). Report: hunt-ws/reports/w2-5e-rp-prose-report.txt. Workspaces removed; expectation file retained in hunt-ws/ until closeout. [5e] row 2 CLOSED; item stays verified.
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/base.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-20: sets_mixins.py hunt fixed liar escapes at this file's `_validate_target` gate (guarded interrogation preserving the family typed error; digest ba52351c → 91c41b1f). Prior verified verdict stands for the old digest only. Bounded re-verification queued (gate probes + honest behavior; full re-hunt not warranted — change is one guarded interrogation, fully exercised by the sets_mixins verification).
    - Iteration: 4. Fresh Worker 1 dispatched 2026-09-22 14:41 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/filters-base-stale-r1; worktree 91c41b1f vs HEAD ba52351c re-confirmed exactly the ledgered family-gate fix by digest, tests 1741df8b vs HEAD 04da73cd. Bounded scope per Iteration 3 (gate probes + honest behavior).
    - Iteration: 5. Worker 1 stale re-pass reported Fixed Low (C1: `_validate_target`'s owner-label line did unguarded `isinstance(owner, type)` — a raising-`__class__` bound owner escaped the typed rejection as raw `RuntimeError`; fix is a 4-line `try/except BaseException → owner_is_type=False` mirroring the ledgered diamond guard + docstring sentence; gate/honest re-proof otherwise green) + 2 permanent tests (defect + pass-path pin, tier `tests/`). Files changed: filters/base.py (0236c495) + tests/filters/test_base.py (07392d2a). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the fix + 2 tests; digests match claims incl. probe 97536e4f; collection 21 exact; no nested hunt-ws; ruff + trailing-commas + banned-word + pragma scans clean — re-run by Worker-0 on touched paths; failability claimed raw-pre/typed-post for W2 to re-prove; BaseException-breadth consistency + inapplicability ride for W2 judgment). Out-of-fence flag (orders/base.py identical line) routed to that sibling re-pass, untouched here. Report /tmp/w1-filters-base-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/filters-base-stale-verify, expectation-first.
    - Iteration: 6. Worker 2 verified (expectation-first `hunt-ws/w2-filters-base-stale-expectation.txt` 6565b275, agreement on every row, no contradiction): fresh-WS replay 21/21 + oracles 210 + 593 + 268 live (+29 with 1 pre-existing sharded-gated skip); production-only revert → defect + g06 fail raw `RuntimeError: boom-class` from the unguarded line, pin green, restored cmp-identical; 24/24 attacks incl. no-over-capture proof (unresolvable-string stays raw ImportError, raising factories raw — G1 rewrap key intact); honest-byte proof 18 identical + exactly the 4 RAW→typed flips; BaseException breadth judged CORRECT (adjacent-guard + 6 sets_mixins precedents); owner right; only other `isinstance(owner` site (orders/base.py:135) correctly left; Low concurred; inapplicability grep-proven; gates + prose clean.
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/filters/base.py (guarded owner `isinstance` in the rejection label + docstring) + tests/filters/test_base.py (defect + pass-path pin).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-filters-base-stale-expectation.txt. Evidence: hunt-ws/filters-base-stale-verify/ records, post-fix digest 0236c495.
    - Cleanup (stale re-pass): Removed hunt-ws/filters-base-stale-r1, hunt-ws/filters-base-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 1. Worker 1 dispatched with item baseline bc4b53f6, workspace hunt-ws/filters-base; reported No bugs (22-probe matrix passed; 3 WS-only mutation controls failed 3/5/5 oracle rows for intended reasons, restored sha-verified; oracles 155 + live 7 + 236 passed; ForeignObject/pbugs-16 lead disproved with real composite-FK probe). Target digest ba52351c == HEAD. Worker-0 mechanical checks pass; fresh Worker 2 dispatched.
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-filters-base-expectation.txt`, digest 9201335e, all 7 cells confirmed): fresh `hunt-ws/filters-base-verify` imports inside `$WS`; W1 battery 22/22 replayed; oracles 155 + live 7 + 236 replayed; 31 independent attack probes passed (lying containers at all list gates, range single-predicate + exclude routing, real-model PK coercion branch the fake-model oracles never enter, hostile-metaclass fail-closed, sets-level AND-intersection with forbidden-row absence); gutted-materialize mutation failed 2 probes raw, restored byte-identical.
    - Result: No bugs. Evidence: W1 battery + 3 controls + oracles; W2 replay + 31 attack probes + control. Target digest ba52351c.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-filters-base-expectation.txt. Evidence: hunt-ws/filters-base-verify/ records.
    - Cleanup: Removed hunt-ws/filters-base, hunt-ws/filters-base-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/factories.py
    - Status: verified
    - Iteration: 1. Worker 1 dispatched with item baseline 94f39e91, workspace hunt-ws/filters-factories; reported No bugs (20-probe matrix passed; flag-flip control failed the oracle for the intended reason, restored byte-identical; oracles 105 passed; exclude-True/non-class/abstract candidates disproved as declared-path parity). Target digest 366e0490 == HEAD. Worker-0 mechanical checks pass; fresh Worker 2 dispatched.
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-filters-factories-expectation.txt`, digest 53c7bf9c; one expectation error was W2's own — subclass rejection is `TypeError`, correct Pythonic choice): fresh `hunt-ws/filters-factories-verify` imports inside `$WS`; W1 battery 20/20 + oracles 105/105 replayed; 15 independent attack probes passed (set/frozenset collapse, exclude equivalence, filter_overrides discrimination, reserved-key stripping strengthened, declared-vs-dynamic parity for all malformed shapes); reserved-keys-emptying control failed A7, restored byte-identical.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 15 attack probes + control. Target digest 366e0490.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-filters-factories-expectation.txt. Evidence: hunt-ws/filters-factories-verify/ records.
    - Cleanup: Removed hunt-ws/filters-factories, hunt-ws/filters-factories-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/inputs.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (silent predicate drop in `_normalize_range_value`) with fix + 5 permanent tests; Worker-0 mechanical checks pass (digests match, attribution clean, tier correct).
    - Iteration: 2. Worker 2: correctness verified (expectation-first; fresh-WS replay green; reverted-WS control 8 failed/1 passed with silent-`{}` proven; 14 attack probes; oracles 258 + shared 93 + live 2 green; owner/tier/Low concurred) BUT prose revision-needed (banned "previously" in new test docstring; exact restatement supplied).
    - Iteration: 3. Worker 1 applied the exact restatement (docstring-only; focused 93 passed; lint clean; banned-token grep clean). Worker 2 prose re-check: PASS (restatement exact; production byte-identical 06797dc7; item-scoped diff = fix hunk + 5 tests only; focused 93 passed in 6.64s). Note: W1's interim "5debe0ad" production digest was a misreport — ground truth bytes are 06797dc7, confirmed by Worker-0 and Worker-2 independently.
    - Result: Fixed Low. Files changed: django_strawberry_framework/filters/inputs.py (`_normalize_range_value` fail-loud guard + contract docstring) + tests/filters/test_inputs.py (5 range-shape tests, 9 nodes).
    - Verification: Passed (correctness iteration 2 + prose iteration 3). Expected-before-diagnosis: hunt-ws/w2-filters-inputs-expectation.txt. Evidence: hunt-ws/filters-inputs-verify/ records, post-fix digest 06797dc7.
    - Iteration: 4. Fast-forward drift check 2026-09-19: production digest 06797dc7 still matches;
      main-side test edits are adjacent (+75, no overlap); hunt hunks intact (5 range tests).
      Focused re-run of the 5 range rows 9 passed in shared tree (5 hunt incl. parametrization +
      4 neighbors matched by selection). Verdict stands.
    - Iteration: 5. Behavior change recorded (review 5d, W2-challenged): `_normalize_range_value` (~:807) raises a typed error on unparseable/empty range bounds where the old code silently dropped the predicate (silent-to-error; direct-Python only per the review — reach claim part of the challenge). Verdict pending.
    - Iteration: 6. Worker 2 product-semantics challenge (Q1-Q3, workspace hunt-ws/5d-filters-verify): verdict (a) CONCUR — guard stands; reach "direct-Python only" CONFIRMED (wire range shapes always meet their own arm; single-caller census + B25 annotation census). Q1: post-fix typed `ConfigurationError` naming class + axes + remedy; pre-fix exact silence (every non-range shape -> `{}` — unfiltered rows). Q2: 39 honest rows byte-identical, 28 trigger rows pre-OK/post-RAISE. Q3: nothing contracted the silence; deprecate-first named and declined. Erratum (record-only): hunt range tests are 8 nodes, not 9. Shared tree never edited (fences re-hashed; fence-vs-d4f70cda empty). Report: hunt-ws/reports/w2-5d-filters-report.txt. Workspace removed. Item stays verified.
    - Iteration: 7. Fresh Worker 1 dispatched 2026-09-23 UTC, ITEM_BASELINE 55810cc7, workspace hunt-ws/5e-inputs-prose (bounded prose revision: [5e] row 1, :783 docstring hunt-added "SPLATTED" provenance; :637 HEAD phrase stays). W2 verification follows in-unit.
    - Iteration: 8. Worker 1 revision landed (docstring-only -4/+2: "previous arms SPLATTED" sentence -> timeless contract prose; production 06797dc7 -> f4d41917, tests 3baeabee untouched). Worker-0 mechanical checks pass (item diff vs 55810cc7 exactly the hunk; :637 cmp-identical; SPLATTED count 1; focused 8 green — re-run by Worker-0; ruff check + format clean — re-run by Worker-0; no new pragma). Fresh Worker 2 verification dispatched (ITEM_BASELINE 2396091c, workspace hunt-ws/5e-inputs-prose-verify).
    - Iteration: 9. Worker 2 VERIFIED the prose revision (expectation-first, K1-K6 all PASS: exact hunk; :637 cmp-identical; new prose timeless + each claim tied to code/tests; independent co_code proof + reverse-apply failability to 06797dc7; focused 8 + full module 92 green; ruff clean; W1 report audited — 3 immaterial discrepancies only). Shared tree never edited by W2 (fences re-hashed f4d41917/3baeabee; fence-vs-2396091c empty). Out-of-scope observation (NOT a finding): provenance-adjacent wording survives in untouched test docstrings (~:823/:842) — outside the bounded [5e]-row-1 scope; recorded for awareness only. Report: hunt-ws/reports/w2-5e-inputs-prose-report.txt. Workspaces removed; expectation file retained in hunt-ws/ until closeout. [5e] row 1 CLOSED; item stays verified.
    - Cleanup: Removed hunt-ws/filters-inputs, hunt-ws/filters-inputs-verify; unrelated work preserved.
    - Iteration: 2. Worker 2 verdict: correctness verified (expectation-first `hunt-ws/w2-filters-inputs-expectation.txt`; fresh-WS replay green; reverted-WS control 8 failed/1 passed with silent-`{}` proven; 14 attack probes passed; oracles 258 + shared focused 93 + live 2 passed; owner/tier/Low all concurred) BUT prose revision-needed: new test docstring uses banned "previously" — must be restated as a plain invariant clause per W2's exact restatement. Item back to Worker 1 for the docstring-only edit (workspace intact); no correctness re-proof owed beyond the focused test + lint.
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/sets.py
    - Status: verified
    - Stale 2026-09-23 (Deep dive 4 B21 fix landed in the verified file): recorded 5d fence ed84cf43, worktree 1968a1e6; delta is exactly the B21 overlap-head reroute (+14/-1 in FilterSet._normalize_input declared branch) + 5 permanent tests, verified in-dive by the dive-4 W2. Prior verified verdict stands for the old digest only. Bounded Worker 2 re-verification of the item (5d raises intact + fix interaction + item batteries) queued after the dive-4 W2 closes.
    - Stale resolved 2026-09-23 (bounded W2 VERIFIED, no challenges): 5d rows re-proved both eras (raise trigger + byte-pinned message, honest singles, B06/B07 texts, non-walkable trio, range/CSV, B19/B24/B25 via REAL generated classes); E8 flip exact (3/28 outcome rows differ, all else byte-identical); failability re-proved (committed 3-red + W2 2-red, cmp-identical restores); census recounted (64 sets, merged=[], 591 pre-finalize grouping-exact); corollary routing concurred + behavior unchanged; R1/R2/R3 untripped; floor subset green (bed untouched); inputs.py docstring delta AST-identical; diff exactness + gates clean. Expectation-first hunt-ws/w2-filters-sets-deep4-expectation.txt (pinned 1c42b558); report hunt-ws/reports/w2-filters-sets-deep4-report.txt. Workspace removed at close.
    - Iteration: 9. Fresh bounded Worker 2 dispatched 2026-09-23, ITEM_BASELINE a568a13e976b7104e30b268774694122be976947, workspace hunt-ws/filters-sets-deep4-verify; expectation-first hunt-ws/w2-filters-sets-deep4-expectation.txt (LANDED, contamination PASS with zero hits, sealed 15:51:43, hash-pinned 1c42b558); phase-2 drop written (hunt-ws/filters-sets-deep4-phase2/DIAGNOSIS.txt) with 9 bounded ride-alongs (item batteries, 5d-row re-probes, overlap family + revert differential, gate-pin both-eras, committed-test + diff judgments, inputs.py AST-strip, corollary adjacency, R1/R2/R3, floor subset).
    - Stale 2026-09-22 (digest-driven, comment-only drift): recorded c1a0f1b2, worktree ed84cf43; delta vs recorded is exactly main's one comment line (ae52bdec fast-forward), reverse-apply proven byte-exact. Prior verified verdict stands for the old digest only. Bounded Worker 2 re-verification on the diff queued (order 6c).
    - Stale 2026-09-21, mechanical: worktree digest 61e1b2c9 ≠ recorded 4a40e51b (HEAD blob 4ab65a26 untouched by all three new commits — drift is worktree-only). Cause: the get_fields `is_str` guard hunk (+10/-1) is CONFIRMED as inputs-item D8 (reported with evidence). Prior verified verdict stands for the declared-key guard; re-pass queued AFTER the inputs item closes (settled bytes): the D8 hunk rides with the inputs verification, and the re-pass additionally assesses the UNPROBED 7-site qualname-interpolation mention from input_values verification + the inputs-hunt `!= "__all__"` Collection-hostile-`__eq__` lead (confirm-or-disprove before any edit).
    - Stale narrowed 2026-09-21 ~22:45: inputs item verified — D8 hunk + appended test ledgered under utils/inputs.py (post-fix digest 61e1b2c9 re-confirmed == worktree). The re-pass now covers ONLY the non-D8 region: the declared-key guard at the new settled bytes + the two leads above. Main fast-forward untouched this file.
    - Scope 2026-09-22 (from querysets verification, UNPROBED mention): similar `cls.__name__` reads in this target, not probed by W2 — rides the same re-pass inspection scope (confirm-or-disprove with contract rows before any edit).
    - Iteration: 3. Fresh Worker 1 dispatched 2026-09-22 14:49 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/filters-sets-stale-r1; worktree d56c21f0 vs HEAD 722e0c77 (both hunt hunks + HEAD docstring lines per the 08:45 Drift), tests 5d8e0f13 vs HEAD 85d31c4b (2 ledgered tests + 4 foreign maintainer live-re-tiering hunks: module docstring, 2 r6 docstrings, deletion of `test_r6_relation_isnull_filters_correctly_no_500` whose live sibling is committed in HEAD — continuation of e9e4d45c; preserve byte-identically). Scope: the narrowed non-D8 region + the 3 inspection leads above; confirm-or-disprove with contract rows before any edit.
    - Iteration: 4. Worker 1 stale re-pass reported Fixed Low (one bug class, all 3 leads confirmed: refusing/unformattable metaclass `__name__`/`__qualname__` in 19 error-label reads + refusing `__ne__` on a gate-passing custom Collection at the `get_fields` narrowing check; fix is safe renderers at all 19 reads + guarded `!=`; honest messages byte-identical; scope (a) re-proven) + 19 permanent tests (tier `tests/`). Files changed: filters/sets.py (eaede28b) + tests/filters/test_sets.py (db71588e). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the fix + 19 tests; digests match claims; 4 foreign maintainer hunks verified byte-identical — deletion still absent, 3 docstrings present; probe collection 42 exact with RECORD.md pins + REACHED asserts; no nested hunt-ws; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0; no new pragma; failability claimed 18/18 red + orphan pin for W2 to re-prove). Routed lead (sets_mixins.py:549 hostile-cls + generator escape, evidence in scratch) rides for W2 judgment — no stale trigger now. The `_safe_text` import saga is resolved (imported + used, gates green). Report /tmp/w1-filters-sets-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/filters-sets-stale-verify, expectation-first.
    - Iteration: 5. Worker 2 verdict: revision-needed on ONE concrete challenge C1 (expectation-first `hunt-ws/w2-filters-sets-stale-expectation.txt`; everything else verified, listed so the re-pass stays narrow). C1: the `!=` guard's except arm misroutes upstream-truthy + `!=`-refusing declarations — `_EvilAllStr("__all__")` (==-honest str subclass, `__ne__` raising) passes class creation silently post-fix with the PK-add/M2M-strip narrowing skipped, vs loud raw `RuntimeError` pre-fix: a loud→silent-divergent regression breaking the narrowing contract + the fix's own invariant. Repro `w2-attacks/test_w2_attacks.py::test_w2_a1_evil_str_shorthand_end_to_end` (+A2/A3 twins), both cells agree, Low, no severity dispute. Remedy direction: `not (meta_fields == "__all__")` (consult the same dunder upstream consulted); acceptance: full deterministic ==/!= matrix matches upstream every cell + all greens stay green + honest identical + new test(s) pinning the truthy-== half. Verified scope preserved: replay 42/42 + oracles 320 + 268; revert 22F/20P + 18/18 red with pin green (3 cycles, cmp-identical); honest identity independently proven; all 19 label sites solid (KI/Exit breadth, double-hostile, completeness grep); N-rows concurred; owner/tier/files/gates/prose clean; cells: both executed, PG/sharded inapplicable-for-the-diff by own analysis. Routed lead sets_mixins.py:549 judged HAS STANDING (A20 reproduces; contract row + feasible shape + reaching input named) — Worker 0 opens a narrow sets_mixins stale re-pass, fenced out of this revision. Same item back to Worker 1 with workspaces intact.
    - Iteration: 6. Fresh Worker 1 revision dispatched 2026-09-22 15:38 UTC, ITEM_BASELINE c9e39d31 (retained), workspace hunt-ws/filters-sets-stale-r1 intact (+ W2 repro at hunt-ws/filters-sets-stale-verify/w2-attacks/ for reference); scope: C1 only, all verified scope must stay green. Report /tmp/w2-filters-sets-stale-report.txt is the challenge text.
    - Iteration: 7. Worker 1 revision landed (C1 corrected per the remedy: `not (meta_fields == "__all__")` with no `try` + same-dunder comment + NOTE with `# noqa: SIM201`; 56-cell matrix + str shapes: pre 22F/41P exactly the divergent inventory with A1 byte-exact, post 63/63 every cell = upstream; prior greens re-proven both cells — battery 42, tests 320→324, live 268, honest capture diff-empty) + 4 new permanent tests (truthy-== half + falsy-!= agreement). Production c1a0f1b2, tests 52ad6629. Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the C1 replacement + 4 tests; 19 swaps/D8/guard/19 tests untouched — test-side 0 `-` lines, foreign hunks preserved; digests match; collection 69 = 65 matrix/honest/anchor + 4 preview mapped per-file exact; ruff + trailing-commas clean — re-run by Worker-0; the 1 banned-token hit is domain "sweep" in a production comment, not test provenance — assessed clean; no new pragma; failability claimed 22-node re-open + 4/4 for W2). Fresh Worker 2 re-verification dispatched (criteria K1-K5: matrix agreement, prior greens, failability, gates/foreign, SIM201-noqa justification).
    - Iteration: 8. Worker 2 re-verified (expectation-first `hunt-ws/w2-filters-sets-stale-expectation-r2.txt`, from the upstream oracle + acceptance criteria before the rev1 report): K1 PASS (replay 69/69; A1/A2/A3 twins narrow on revised bytes with PK in/M2M out end-to-end; upstream verdict independently re-derived per cell incl. zero-falsy/NotImplemented/dict shapes; own recording `__ne__` zero calls revised; KI never invoked; `__eq__`-raising stays loud from the upstream frame); K2 PASS (battery 42 + 324 + 268 live + 17 round-1 attacks; own 7-row captures byte-identical; A4/A18 moves intended toward upstream); K3 PASS (C1-hunk revert reproduces eaede28b byte-exactly — sole production delta; exactly the 22-node inventory + A1 byte-exact + 4/4 fail; restored cmp-identical; pristine spot-revert 2 red + pin green); K4 PASS (all gates; "sweep" independently judged domain vocabulary; pragma 2=2; test file = baseline + 637 pure additions, 0 `-` lines, deletion absent; sets_mixins untouched); K5 PASS (SIM201 noqa justified — the rule's suggestion IS the bug; no-noqa equivalent noted as taste). Cells: floor executed, honest identical across cells; sharded/PG inapplicable-for-the-hunk by own grep.
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/filters/sets.py (19 safe label renderers + `not (==)` narrowing guard + comment/NOTE) + tests/filters/test_sets.py (23 tests: 19 + 4 C1).
    - Verification (stale re-pass): Passed after one revision round (C1 challenged, corrected, re-verified). Expected-before-diagnosis: hunt-ws/w2-filters-sets-stale-expectation.txt + hunt-ws/w2-filters-sets-stale-expectation-r2.txt. Evidence: hunt-ws/filters-sets workspaces (removed post-verify), post-revision digest c1a0f1b2.
    - Cleanup (stale re-pass): Removed hunt-ws/filters-sets-stale-r1, hunt-ws/filters-sets-stale-verify, hunt-ws/filters-sets-stale-reverify; both expectation files retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 9. Worker 2 bounded drift re-verification (criteria K1-K5, mini-expectations before runs; workspace hunt-ws/filters-sets-drift-verify): K1 recorded bytes reconstructed in-WS + c1a0f1b2 reproduced byte-exact, sole delta :1736 comment reword (`target__pk` → absolute `<relation>__pk`), cmp single position; K2 AST dumps identical (len + sha256) + both compile/import with FilterSet present; K3 25/25 ledgered nodes + 1/1 foreign live sibling + 268/268 WS live green at ed84cf43; K4 declared-form-key guard neuter red DID-NOT-RAISE + cmp-identical restore + green; K5 ruff-format/check + commas detection-only clean + fence-vs-ITEM 0 bytes + comment judged timeless without provenance. Verdict: verified, prior verdict stands at ed84cf43. Foreign maintainer hunks preserved byte-identically. No new ledger row (re-proof, no change).
    - Iteration: 1. Worker 1 dispatched with item baseline b44eb63d, workspace hunt-ws/filters-sets; reported Fixed Low (multi-entry operator bag over declared filter: last-wins silent drop) with owner fix + 1 permanent test; Worker-0 mechanical checks pass (digests match, attribution clean, tier/prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-filters-sets-expectation.txt`, digest ec6d024a, matches fix exactly): fresh-WS replay green post-fix; reverted-WS control 1 failed with `SILENT-DROP-OUT: {'custom': 'a'}` printed (last-wins confirmed); bytes restored byte-identical; 8 attack probes passed (single-active/UNSET/None partials scalar; all-inactive no-raise; three-active counts 3; generated bags unaffected); WS suites 301 + 590 green; ruff + banned-token grep clean. Owner/tier/Low concurred.
    - Result: Fixed Low. Files changed: django_strawberry_framework/filters/sets.py (declared-form-key active-entry guard) + tests/filters/test_sets.py (1 two-lookup test).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-filters-sets-expectation.txt. Evidence: hunt-ws/filters-sets-verify/ records, post-fix digest 4a40e51b.
    - Cleanup: Removed hunt-ws/filters-sets, hunt-ws/filters-sets-verify; drift re-proof removed hunt-ws/filters-sets-drift-verify; drift report retained in hunt-ws/reports/ until closeout; unrelated work preserved.
    - Iteration: 10. Behavior change recorded (review 5d, W2-challenged): the ~:2403 raise fires where the old code silently did nothing (silent-to-error; direct-Python only per the review — reach claim part of the challenge). Verdict pending.
    - Iteration: 11. Worker 2 product-semantics challenge on the `FilterSet._normalize_input` declared-filter multi-lookup raise (:2403-2412; Q1-Q3, workspace hunt-ws/5d-filters-verify): verdict (a) CONCUR on the behavior, with a REQUIRED RECORD CORRECTION on reach: trigger is wire-reachable through the declared+generated overlap shape (B19 2-field bag census + B23 generated-class instance trigger), so reach is "direct-Python + overlap-wire", NOT "direct-Python only" — the [5d] row and Iteration 10 annotations are corrected accordingly. Q1: post-fix typed `ConfigurationError` (sorted lookups + remedy); pre-fix last-wins overwrite with a container-dependent winner. Q2: honest declared usages byte-identical; overlap two-lookup was never honored (no correct behavior existed to preserve). Q3: two-active bag over one key undefined under the one-form-key contract; deprecate-first named and declined (no defensible warn semantics for "applied one of your two constraints"). Reopen conditions R1-R3 in the report; absent them the reach wording dispute is closed. Shared tree never edited. Report: hunt-ws/reports/w2-5d-filters-report.txt. Workspace removed. Item stays verified.
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/converter.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (41-node matrix; JSON→str control failed for intended reason, restored sha-identical; oracles 95 + live 34; 4 candidates disproved as documented divergence/parity); Worker-0 mechanical checks pass (digest b717fd0f == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-forms-converter-expectation.txt`, digest c359e519, all axes matched): fresh-WS replay 41/41 + oracles 54/54 + live 34/34; 7 attack probes passed (subclass mapping, reversed-registry precedence, Image/TypedChoice/FilePath corners, fail-loud naming, NullBoolean extended, lying-metaclass, column-path agreement); own JSON→str control failed as intended, restored byte-identical.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 7 attack probes + control. Target digest b717fd0f.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-forms-converter-expectation.txt. Evidence: hunt-ws/forms-converter-verify/ records.
    - Cleanup: Removed hunt-ws/forms-converter, hunt-ws/forms-converter-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py and docs/shadow/current/django_strawberry_framework__forms__converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/inputs.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (fail-loud diagnostic escape in `_form_field_basis`: bare-`isinstance` comprehension let hostile-`__class__` values escape raw) with owner fix + 1 permanent test; Worker-0 mechanical checks pass (digests match, attribution clean, tier/prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-forms-inputs-expectation.txt`, digest ffbdac6e): fresh-WS 7-probe replay green post-fix; reverted-WS control failed raw `RuntimeError: boom-class` (plain-42 control passed); permanent test FAILED pre-fix / PASSED post-fix; bytes restored byte-identical; armed-required path still raw (narrow scope concurred, robustness row). Owner/tier/Low concurred; prose clean.
    - Result: Fixed Low. Files changed: django_strawberry_framework/forms/inputs.py (`_form_field_basis` guarded per-value loop) + tests/forms/test_inputs.py (`test_basis_diagnostic_typed_for_hostile_class_value`).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-forms-inputs-expectation.txt. Evidence: hunt-ws/forms-inputs-verify/ records, post-fix digest 436fcf42.
    - Cleanup: Removed hunt-ws/forms-inputs, hunt-ws/forms-inputs-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/resolvers.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (5-probe matrix; skip→False control failed exactly the null-passthrough row, restored byte-identical; oracles 36 + live 409; 5 candidates disproved); Worker-0 mechanical checks pass (digest 4edb984b == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-forms-resolvers-expectation.txt`, digest afa8e765): fresh-WS replay 5/5 + oracle 36/36 + combined 48/48; 7 attack probes passed (denial-before-decode with zero-decode-call proof, hidden/missing/wrong-model/uncoercible byte-identical envelopes, empty-value arms incl. M2M null divergence, container-first with zero-visibility-call proof, partial reconstruction, duplicate-unique envelope); own skip-mutation control failed 2 instruments, restored byte-identical.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 7 attack probes + control. Target digest 4edb984b.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-forms-resolvers-expectation.txt. Evidence: hunt-ws/forms-resolvers-verify/ records.
    - Cleanup: Removed hunt-ws/forms-resolvers, hunt-ws/forms-resolvers-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/sets.py
    - Status: verified
    - Iteration: 3. Re-opened: mutations/sets.py verification confirmed same-class residuals at `forms/sets.py:577,804` (+180,206,216,852,899) — form-metaclass validation path, same bug class, other owner. Prior verified verdict stands for all else; narrow re-pass queued.
    - Iteration: 4. Worker 1 stale re-pass: Fixed (8 mechanical label swaps, no logic change: :577/:804 `name = _safe_class_name(cls)`; :180/:206/:216 typed hook-label messages; :218 `type(exc).__name__` → `_safe_type_name(exc)`; :852/:899 form_class/entry names; only remaining `__name__` is :725 package-owned `module=__name__`, out of scope) + 10 new tests in `tests/forms/test_sets.py` (valid plain+modelform register; invalid stay typed; hook/exc-name/redirect/perm-entry rows typed). Verdict per site: degraded label throughout — each read is display-only inside an already-typed path; rejection would orphan a legal declaration (both precedents). Failability: 9 failed raw + 1 INTERNALERROR pre-fix → 13 green post-fix; honest messages byte-identical (95dc0a7c both); shared focused 113 + neighbors 390 passed; ruff + trailing-commas clean; banned-token grep clean. Worker-0 mechanical checks pass (post-fix digests 98ef150d/159b55ec == worktree; attribution clean — only item paths; prose scan clean). Fresh Worker 2 re-verification dispatched.
    - Iteration: 1. Worker 1 reported No bugs (24-probe matrix; oracles 174 + 159 + live 29; 5 candidates disproved; LIAR-OUT/DESCRIPTOR-OUT characterized as robustness rows); Worker-0 mechanical checks pass (digest 36ce80b4 == HEAD; shared-venv-with-cwd runs satisfy the table via test_00 WS-path/DB asserts).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-forms-sets-expectation.txt`, digest 9e9bff1f): fresh-WS replay (W1 battery 23 passed — test_00 path-literal failure is mechanical, isolation confirmed; oracles 174 + 159 + live 34); 19 attack probes passed (operation/hook/snapshot/narrowing/guard-ordering/waiver/naming/collision/bind-drain); guard-disabled control failed C3 + strict-first, restored byte-identical; LIAR-OUT confirmed not overturned (infeasible shapes, loud, owner is separate pending item).
    - Iteration: 5. Worker 2 verified (delta expectation `hunt-ws/w2-forms-sets-expectation-r2.txt`, digest 89e43cf8): fresh-WS replay 10/10 typed-or-registered + `-k hostile` 13 green + full file 113 + neighbors 390; fail-without control (10/10 RAW + 7 failed + INTERNALERROR, restored cmp-identical); honest-identity independently re-proven (95dc0a7c); verdict-on-verdict: degradation correct at all 8 sites (labels display-only; offending keys still named; :218 must wrap); independent audit clean (sole `__name__` is package-owned :725; no qualname/class/str/repr reads on producer objects); prose + lint clean.
    - Result: No bugs (iterations 1–2) + stale residuals fixed (iterations 3–5). Files changed: django_strawberry_framework/forms/sets.py (8 safe-renderer swaps) + tests/forms/test_sets.py (10 hostile-name tests).
    - Verification: Passed (iterations 2 + 5). Expected-before-diagnosis: hunt-ws/w2-forms-sets-expectation.txt + -r2. Evidence: hunt-ws/forms-sets-stale-verify/ records, post-fix digest 98ef150d.
    - Cleanup: Removed hunt-ws/forms-sets, hunt-ws/forms-sets-verify, hunt-ws/forms-sets-stale, hunt-ws/forms-sets-stale-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py and docs/shadow/current/django_strawberry_framework__forms__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/keyset.py
    - Status: verified
    - Bounded lead assessment 2026-09-20 (cursor evil-str downstream, from types/base.py stale re-pass): ROBUSTNESS ROW, not a defect — keyset.py stays verified, no stale. Reproduced narrowly: `EvilStr("id")` in `Meta.cursor_field` passes validation by design (valid shape, local concrete column), rides into `CursorColumn.name`, detonates raw only at the seek-Q f-string at execution time; encode/decode/determinism/NULL-loud/direction-table all hold; wire cursors always plain str (no reaching input); actor is the schema author sabotaging own declaration (fails GOAL.md defect test: no row + no feasible shape + no wire/config input). If ever carded, owner would be types/base.py `_validate_cursor_field` (normalize to base str), not keyset.py. Evidence: hunt-ws/keyset-lead-assess/ (18 probes, WS import/DB printed, keyset digest df4b5e2f unmodified); workspace removed after determination, probes summarized here.
    - Iteration: 1. Worker 1 reported No bugs (15-test battery; flipped-seek control failed 5 probes, restored sha-identical; oracles 73 + live 39 + 33; redundant-bound/bool-first/composite-pk/pbugs-8 candidates disproved); Worker-0 mechanical checks pass (digest df4b5e2f == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-keyset-expectation.txt`, digest d01c2b70, all 7 rows matched): fresh-WS replay (W1 battery 14/14 product-green — test_00 path literal is mechanical; oracles 73 + live 39 + 33); 8 attack probes passed (rejection-message equality, determinism + NULL-loud, first-extremes, marker split, fast-path 6-edge eligibility, Q-vs-SQL agreement both flips + brute force, loud column paths, direction truth table); own seek-flip control failed 4 for intended reason, restored byte-identical.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 8 attack probes + control. Target digest df4b5e2f.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-keyset-expectation.txt. Evidence: hunt-ws/keyset-verify/ records.
    - Cleanup: Removed hunt-ws/keyset, hunt-ws/keyset-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__keyset.stripped.py
    - docs/shadow/current/django_strawberry_framework__keyset.overview.md
    - Prompt:
        - Use django_strawberry_framework/keyset.py as the entry point. Read docs/shadow/current/django_strawberry_framework__keyset.stripped.py and docs/shadow/current/django_strawberry_framework__keyset.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/list_field.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-19: main-side fast-forward changed the target
      substantially (recorded digest f357eded, current ce682d5f; delta 538 lines incl. the
      spec-050 list_field_arguments feature: offset-guard ordering forms, relation-ordering
      expansion, hook-failure masking). Prior verified verdict stands for the old digest only;
      re-hunt queued at the new digest before the gate.
    - Iteration: 4. Fast-forward 69a25369..24e6b4d3 (fee87ac4 shared-seal move) rewrote the target again (HEAD now 21380eb7; worktree 616ca7f6 adds only the concurrent DRY docstring hunk — re-hunt attributes-first, never touches it). Re-hunt runs at HEAD 21380eb7.
    - Iteration: 5. Fresh Worker 1 dispatched 2026-09-22 15:06 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/list-field-stale-r1; worktree 616ca7f6 vs HEAD 21380eb7 re-confirmed exactly the concurrent DRY docstring hunk (+8) by digest, tests d3bfa877 clean vs HEAD. Scope per Iteration 4 (spec-050 feature + shared-seal move at the new bytes); attribution-first, never touches the DRY hunk. Oracle note: tests/test_list_field.py carries the known-RED maintainer-decision test (hostile-metaclass guard) — reproduce-but-don't-chase, not this item's to resolve.
    - Iteration: 6. Prior W1 dispatch (baseline c9e39d31, workspace hunt-ws/list-field-stale-r1) died on model-stream idle timeout with no report; shared tree untouched (item diff empty), its partial workspace retained as UNVERIFIED orientation only. Fresh Worker 1 dispatched 2026-09-22 15:15 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/list-field-stale-r2 (may glance at the dead workspace top level only; re-derive everything); worktree 616ca7f6 + tests d3bfa877 re-confirmed. Same scope + oracle note as Iteration 5.
    - Iteration: 7. Worker 1 (r2) reported Fixed Low (D1: four unguarded interrogations in the shared construction validator `_validate_djangotype_target` — `isclass`/`issubclass`/registry-lookup/`origin` — escaped raw for hostile targets; fix is four contained interrogations + docstring paragraph; full re-hunt otherwise clean incl. relation-expansion classifier mirror-proven, capture-scope lifecycle, sync/async parity) + 4 permanent tests (tier `tests/`). Files changed: list_field.py (f979f0d6) + tests/test_list_field.py (5036f969). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the fix + 4 tests; DRY hunk preserved — zero DRY lines in the item diff; digests match claims incl. probe 35f5c759; collection 16 exact; no nested hunt-ws; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0; banned-token file-wide 0 — W1's "1 foreign hit" reproduces nowhere; no new pragma; known-RED reproduced + untouched; failability claimed 4-raw-red both WS-revert and HEAD-bytes for W2 to re-prove). Out-of-fence observations A5/A7 (raw detonations at class creation inside types/base.py + registry.py, no contract rows cited) ride for W2 judgment — no stale trigger now. Report /tmp/w1-list-field-stale-r2-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/list-field-stale-verify, expectation-first.
    - Iteration: 8. Worker 2 verified (expectation-first `hunt-ws/w2-list-field-stale-expectation.txt` 54fee87f, full E1-E13 agreement, zero contradiction): fresh-WS replay 15/16 behavioral (P0 dispensation as before) + oracles 113 + known-RED + 137 + 78 live + 230 neighbors; WS-only revert → battery 11 + A1-A4 raw + all 4 permanent tests raw-fail, restored cmp-identical; 18/18 attacks incl. all-3-factories × all-4-sites typed-each-naming-itself; `except Exception` breadth judged CORRECT (KI/Exit propagate uncollapsed both eras); A5 judged HAS STANDING (raw `__mro__` detonation outside the BaseException gate at creation — routed to the queued types/base re-pass, Low at most), A7 closed as robustness row (no containment row, unregistrable-in-principle, unreachable from the seam); known-RED confirmed the ONLY red, failing at class creation via types/base.py:708, untouched by construction; floor executed; W1's 109 count corrected as report erratum (109+4=113); Low concurred; sharded/PG inapplicable-for-the-diff by own grep, pipeline-level unverified; gates + prose clean.
    - Result (stale re-hunt): Fixed Low. Files changed: django_strawberry_framework/list_field.py (4 contained interrogations in `_validate_djangotype_target` + docstring) + tests/test_list_field.py (5 hostile helpers + 4 tests + docstring line).
    - Verification (stale re-hunt): Passed. Expected-before-diagnosis: hunt-ws/w2-list-field-stale-expectation.txt. Evidence: hunt-ws/list-field-stale-verify/ records, post-fix digest f979f0d6.
    - Cleanup (stale re-hunt): Removed hunt-ws/list-field-stale-r1, hunt-ws/list-field-stale-r2, hunt-ws/list-field-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 1. Worker 1 reported No bugs (58-test matrix; guard-neuter 13/20 + isinstance-widening 3 failures, restored byte-identical; oracles 90 + live 172; nested-Q/extra-raw-SQL/sum-semantrics/spec-risk candidates disproved); Worker-0 mechanical checks pass (digest f357eded == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-list-field-expectation.txt`, digest 8ba73461, 10 rows): fresh-WS replay 58/58 + oracle 90/90 + live 172/172; 25 attack probes passed (cleared ordering, dead-input/live-QS, extra-over-random precedence, sum-at-2x-ceiling, truthy-non-True trusted, -? loud, F/RawSQL/Now/Subquery/Case/Upper rules, no-DISTINCT/no-tiebreaker SQL, async aclose, pipeline parity, non-QS windowing, group_by suppression); own guard-neuter control failed 8/25, restored byte-identical, 83/83 re-green; compiler mirror verified vs installed Django 6.1.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 25 attack probes + control. Target digest f357eded.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-list-field-expectation.txt. Evidence: hunt-ws/list-field-verify/ records.
    - Cleanup: Removed hunt-ws/list-field, hunt-ws/list-field-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Use django_strawberry_framework/list_field.py as the entry point. Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/_imports.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (13-probe battery; narrowed-catch control failed exactly the 2 AttributeError rows raw, restored byte-identical; oracles 62; 4 candidates disproved); Worker-0 mechanical checks pass (digest 05e9de80 == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-mgmt-imports-expectation.txt`, digest ef0c2f9b; 3 initial exact-shape guesses corrected by evidence, all in code's favor): fresh-WS replay 13/13 + 17 attack probes passed (exact classes/labels/cause-identity, default-symbol, passthroughs, upstream parity, call_command wire) + oracles 62/62; own narrowed-catch control failed 3 rows raw, restored byte-identical, 30/30 combined green. Drift pin judged adequate (pre-validation immune; translations pinned at package + live tiers; upstream change breaks a test rather than slipping through).
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 17 attack probes + control. Target digest 05e9de80.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-mgmt-imports-expectation.txt. Evidence: hunt-ws/mgmt-imports-verify/ records.
    - Cleanup: Removed hunt-ws/mgmt-imports, hunt-ws/mgmt-imports-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/_imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/export_schema.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (20-test battery; ending→"\n" + weakened-blank-guard controls failed A1/A8 — latter reproducing the historical whitespace bug — restored byte-identical; combined 62 passed; 4 candidates disproved); Worker-0 mechanical checks pass (digest e27adae9 == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-mgmt-export-schema-expectation.txt`, digest 7e8b915a): fresh-WS replay 20/20 (2 pre-existing path-literal asserts need mechanical rename, zero product assertions changed) + 11 attack probes passed (three-way byte identity, overwrite truncation, extended blank family incl. NBSP, selector edges, falsy non-Schema symbols, padded-path literal, Path-kwarg loud, directory-target intact, exact SUCCESS) + oracles 42/42; own M1/M2 controls failed 2+2, restored byte-identical; combined 73 green. Count note: W1's "62" = battery(20) + oracles(42); W2 confirms 42 oracle items — no discrepancy. No writes escaped WS.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 11 attack probes + 2 controls. Target digest e27adae9.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-mgmt-export-schema-expectation.txt. Evidence: hunt-ws/mgmt-export-schema-verify/ records.
    - Cleanup: Removed hunt-ws/mgmt-export-schema, hunt-ws/mgmt-export-schema-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/export_schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/inspect_django_type.py
    - Status: verified
    - Stale 2026-09-22 (digest-driven, concurrent DRY hunk landed after verification): recorded 46dffb3d (== HEAD at verify), worktree 9d0aec73; delta is the DRY 7-line docstring citation fix (dry-0_0_15.md ~700-704), never hunt's, never touched. Prior verified verdict stands for the old digest only. Bounded Worker 2 re-verification queued (order 6c).
    - Iteration: 1. Worker 1 reported No bugs (21-probe battery; `_yes_no` flip control failed 1, restored sha-identical; oracle 24; 6 candidates disproved as unreachable-or-convention); Worker-0 mechanical checks pass (digest 46dffb3d == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-mgmt-inspect-type-expectation.txt`, digest 74fe2ce3): fresh-WS replay 21/21 + oracle 24/24; 12 attack probes passed (custom NameConverter end-to-end, schema scalar_map precedence, real UNRESOLVED forward-ref CommandError, dotted non-type, case-sensitivity, renderer shapes + all four-corner label branches, `__name__`-surface ambiguity, stdout shape + None return + DB-bytes-identical read-only proof); own `_yes_no` control failed 4/57, restored byte-identical; combined 33 green (one W2 probe-authoring error corrected in-probe).
    - Iteration: 3. Worker 2 bounded drift re-verification (criteria K1-K5, mini-expectations before runs; workspace hunt-ws/inspect-drift-verify): K1 worktree-vs-HEAD exactly the DRY docstring hunk (`Command._is_suppressed_relay_pk`, 6+/5-, citation rooted + rewrap), content-matching the DRY run-3 attribution, recorded == HEAD blob 46dffb3d, no second delta; K2 behavior-null via sound method (naive AST honestly differs; docstring-stripped AST identical len 47542 + opname/const cross-check identical across 32 code objects with only the __doc__ slot differing) + both compile/import; K3 19/19 package oracle both trees (24→19 via recorded main re-tiering + maintainer port, all green) + 24/24 WS example tier; K4 `_yes_no` flip neuter red 4/39 (same family as W2's control) + sha256-identical restore + 19 green; K5 3 gates clean + fence-vs-ITEM 0 bytes + drift paragraph byte-identical modulo citation spelling (mirror gate passes, no new contract burden). Verdict: verified, prior No-bugs verdict stands at 9d0aec73. No new ledger row (re-proof, no change).
    - Result: No bugs. Evidence: W1 battery + control + oracle; W2 replay + 12 attack probes + control. Target digest 46dffb3d.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-mgmt-inspect-type-expectation.txt. Evidence: hunt-ws/mgmt-inspect-type-verify/ records.
    - Cleanup: Removed hunt-ws/mgmt-inspect-type, hunt-ws/mgmt-inspect-type-verify; drift re-proof removed hunt-ws/inspect-drift-verify; drift report retained in hunt-ws/reports/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/inspect_django_type.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/middleware/debug_toolbar.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (43-probe matrix; neutered-payload control observed absent; oracles 70 + live 15; soft-dep present + absent; 6 candidates disproved); Worker-0 mechanical checks pass (digest 5360149b == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-middleware-toolbar-expectation.txt`, digest 0b37cfac, all 7 rows matched): fresh-WS replay 43/43 (WS-path assert repointed, workspace-only) + oracle 70/70 + live 15/15; 16 attack probes passed (view_class edges, xhtml/length rules, JSON family, falsy-id, empty-encoding mirroring stock, raising-subtitle bytes-unchanged, stock chaining); own isinstance-guard-removal control failed 3 tagging probes TypeError, restored byte-identical.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 16 attack probes + control. Target digest 5360149b.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-middleware-toolbar-expectation.txt. Evidence: hunt-ws/middleware-toolbar-verify/ records.
    - Cleanup: Removed hunt-ws/middleware-toolbar, hunt-ws/middleware-toolbar-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/debug_toolbar.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/middleware/request_body.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (14-probe matrix; status=200 + audit-neutering controls failed exactly 2+2, restored byte-identical; oracles 51 + live 18; forged-setup/forged-stamp/generator-args/MIDDLEWARE-None disproved); Worker-0 mechanical checks pass (digest e6e32e78 == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-middleware-request-body-expectation.txt`, digest c5f7472d, all predictions held): fresh-WS replay 14/14 (test_00 dirname literal adapted, workspace-only) + oracle test_views.py 204/204; 29 attack probes passed (genuine prepared-instance dispatch + consumption/deletion, single-measurement count, cross-request exemption, nested restore, async-cancel reset, markcoroutinefunction split, setup-None parity, _NO_SETUP path, property-descriptor decline, initkwargs shapes, mount-read-raise, stamped-skip, refusal byte-parity, misordering duplicates, real-chain 413/403); own audit-neuter + stamp-removal controls failed exactly the dependent tests, restored byte-identical; combined 247 green.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 29 attack probes + 2 controls. Target digest e6e32e78.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-middleware-request-body-expectation.txt. Evidence: hunt-ws/middleware-request-body-verify/ records.
    - Cleanup: Removed hunt-ws/middleware-request-body, hunt-ws/middleware-request-body-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/fields.py
    - Status: blocked
    - Iteration: 5. Re-opened: mutations/sets.py verification confirmed a same-class residual at `mutations/fields.py:297` (`f"{mutation_cls.__name__}Payload"` at ordinary field construction) — same producer-controlled object, no upstream normalization (post-fix hostile names register). Prior verified verdict stands for all else; narrow re-pass queued.
    - Iteration: 6. Worker 1 stale re-pass: Fixed (one-line owner fix `f"{_safe_class_name(mutation_cls)}Payload"` + 1 test `test_hostile_name_registered_target_builds_field_with_safe_payload_label`). Verdict: degraded label, not typed reject — class is already registered, and phase-2.5 bind derives the payload name through the identical renderer, so rejection would orphan a legal mutation; honest Payload naming byte-identical (ForwardRef + lazy ref + CreateItemPayload pin green both sides). Failability: new test 1 failed raw pre-fix / 22 green post-fix; shared focused 22 + 350 passed; ruff clean. Audit: the only raw `__name__` read on the producer-controlled class in this file was this line. Worker-0 mechanical checks pass (post-fix digests 64410c86/c6821b06 == worktree; attribution clean — only item paths; prose scan clean). Fresh Worker 2 re-verification dispatched.
    - Iteration: 7. Worker 2 verified (delta expectation `hunt-ws/w2-mutations-fields-expectation-r3.txt`, digest 21f80fe3): fresh-WS repro DEGRADED-BUILD post-fix; line-297-only revert → raw escape (load-bearing proven); restored byte-identical; honest ForwardRef byte-identical both sides; independent bind-agreement probe (`lazy ref == materialized == _payload_type_name == 'HostileNameMetaPayload'`); 7 hostile + 22 file + 350 suite green. Verdict-on-verdict: degrade is correct (identical renderer/input/suffix traced live; rejection would orphan a legal mutation). File audit: no other raw `__name__` on the producer class remains. Out-of-scope observation (not a challenge): `mutations/resolvers.py` has raw `mutation_cls.__name__` reads at a runtime seam — different file/contract (that item is separately stale for its own named sites).
    - Iteration: 8. Behavior change recorded (review 5d, W2-challenged): the ERROR-LABEL renderer routes into GraphQL TYPE NAMING — this file's ~:297 + mutations/sets.py ~:1243/:1661. A mutation whose `__name__` raises now publishes a `<MetaclassName>Payload` type instead of failing (pinned by tests/mutations/test_fields.py ~:211). Prior W2 judged degrade-correct (It7: identical renderer traced live; rejection would orphan a legal mutation). Fresh Worker 2 challenge dispatched (shared question with the mutations/sets.py item; workspace hunt-ws/5d-naming-verify; ITEM_BASELINE 0c354262): concur (record + stand) or product-semantics dispute → blocked for Rio, never regraded by fiat.
    - Iteration: 9. W2 challenge verdict BLOCKED-FOR-RIO (product-semantics dispute; report hunt-ws/reports/w2-5d-naming-report.txt): Q1 reproduced exactly (HostileNameMetaPayload in SDL/type_map/field type; pre-fix raised raw); Q2 feasible-shape invariance proven (11-shape battery diff EMPTY both eras incl. identical typed collision); Q3: degraded name CAN collide with a real type's name (typed ledger raise, confusing message), orphan premise REFUTED (trigger never registers at HEAD; fix-created state), fail-loud-at-definition alternative PROVEN non-orphaning + battery-neutral, trigger fails Rule-35 legs 2+3 (robustness posture choice, no severity), surfacing is silent (no degraded flag); Q3-R7 correction: sets.py :1243 is LABEL-ONLY (true naming sites sets :1661 + this file's :297; decision point is sets :1105 register-or-reject). It7 concur NOT sustained (orphan justification conditional + unweighed collision/silence facts). EXACT QUESTION FOR RIO: (A) publish degraded `<MetaclassName>Payload` [status quo, ~:211 pin stands] or (B) reject at definition with typed ConfigurationError [fail loud, pin + hostile-register tests rewritten]? Options/consequences/non-binding-read (B)/reopen-conditions in the report. Item blocked pending Rio; prior Fixed-Low verification stands for the hunt verdict, the dispute is product semantics only.
    - Result: Fixed Low (iterations 1–4) + stale residual fixed (iterations 5–7). Files changed: django_strawberry_framework/mutations/fields.py (guarded isinstance, wrapped protocol probe, `_safe_class_name` labels, guarded own-`__dict__` read, identity-scan ledger, Payload safe label) + tests/mutations/test_fields.py (6 hostile tests).
    - Verification: Passed (correctness iterations 2+4, stale re-verification iteration 7). Expected-before-diagnosis: hunt-ws/w2-mutations-fields-expectation.txt + -r2 + -r3. Evidence: hunt-ws/mutations-fields-verify2/ + hunt-ws/mutations-fields-stale-verify/ records, post-fix digest 64410c86.
    - Cleanup: Removed hunt-ws/mutations-fields, hunt-ws/mutations-fields-verify, hunt-ws/mutations-fields-verify2, hunt-ws/mutations-fields-stale, hunt-ws/mutations-fields-stale-verify; unrelated work preserved.
    - Iteration: 1. Worker 1 reported Fixed Low (H1–H3 hostile-dunder raw escapes) with owner fix + 3 permanent tests; Worker-0 mechanical checks pass.
    - Iteration: 2. Worker 2: revision-needed — H1/H2/H3 verified, but two residual raw escapes in the same R1 guard reproduced post-fix (R-a: `__dict__` read; R-b: ledger `in` vs hostile `__eq__`), with repros + suggested direction; item back to Worker 1, workspaces intact.
    - Iteration: 3. Worker 1 re-pass closed both (guarded own-`__dict__` read → branch-1 reject `from None`; identity-scan ledger citing `mutations/sets.py::make_declaration_registry` #"Identity-scan dedup"; docstring restated as the exact guarded set) + 2 new tests; failability on WS pre-fix bytes; honest messages byte-identical; H1–H3 green; shared focused 21 + 344; ruff clean. Worker-0 mechanical checks pass (digests 8c60a5c6/53e39ccb == worktree; attribution + prose clean).
    - Iteration: 4. Worker 2 verified (delta expectation `hunt-ws/w2-mutations-fields-expectation-r2.txt`, digest 868b93b9, matches on every point): fresh-WS replays TYPED post-fix; fail-without on 99c9a56f (R-a/R-b raw, H1/H2/H3 still typed; 2 failed/3 passed); restored byte-identical; honest-identity independently re-proven (eb5dbfe3 both eras); 7 hostile + 21 file + 344 suite + shared 21 green; ruff clean. Third-residual audit: none — every interrogation guarded; post-validation reads reachable only for ledger members (hostile `__name__` dies at definition in sets.py:1105); identity-scan preserves honest semantics (registration appends the exact object); prose clean. Forwarded lead (not a challenge): W2's invalid branch-3-hostile-`__name__` probe fails inside `mutations/sets.py::_validate_meta` (`cls.__name__` unguarded) — recorded on the mutations/sets.py item for its own contract row.
    - Result: Fixed Low. Files changed: django_strawberry_framework/mutations/fields.py (guarded isinstance, wrapped protocol probe, `_safe_class_name` labels, guarded own-`__dict__` read, identity-scan ledger) + tests/mutations/test_fields.py (5 hostile-dunder tests).
    - Verification: Passed (correctness iterations 2+4). Expected-before-diagnosis: hunt-ws/w2-mutations-fields-expectation.txt + -r2. Evidence: hunt-ws/mutations-fields-verify2/ records, post-fix digest 8c60a5c6.
    - Cleanup: Removed hunt-ws/mutations-fields, hunt-ws/mutations-fields-verify, hunt-ws/mutations-fields-verify2; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/fields.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/inputs.py
    - Status: verified
    - Stale 2026-09-22 (digest-driven, concurrent DRY code hunk landed after verification): recorded fc442047 (== HEAD at verify), worktree fcbb964d; delta is DRY's new `relation_input_python_attr` + 3 composed sites, a CODE change the hunt never verified, never hunt's, never touched. Prior verified verdict stands for the old digest only. Real Worker 2 re-verification of the item on current bytes queued (order 6c).
    - Iteration: 1. Worker 1 reported No bugs (19-probe matrix; neutered-guard control failed exactly the 3 guard probes, restored sha-identical; oracles 75 + 415 + live 180; 6 candidates as no-contract robustness rows); Worker-0 mechanical checks pass (digest fc442047 == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-mutations-inputs-expectation.txt`, digest 6eaf8bb8, all 8 rows matched): fresh-WS replay 19/19 + oracle 75/75 + 409 (delta vs W1's 415 is exactly the 6 concurrent-work tests W2 reset to HEAD in its own WS — reconciled) + live 180/180; 12 attack probes passed (requiredness/UNSET totality, relation naming, lazy audit-atomicity/idempotence/collision/clear, reverse-map totality, payload matrix, selection drops, column-less arms, envelope defaults); own guard-neuter control failed exactly the 3 guard probes, restored byte-identical, 31/31 re-green. Robustness rows concurred non-defects.
    - Iteration: 3. Worker 2 REAL re-verification on current bytes (two-phase; expectation `hunt-ws/w2-mutations-inputs-expectation-r2.txt`, W0-sealed 15da4e46 pre-run, zero contamination; fenced phase 1, drop-gated phase 2): AREA 0 delta equivalence proven (P0 differential suite parity + 646-field spelling sweep 0 divergence + 82-model 21,219-line artifact dumps byte-identical A-vs-B; S1 double-read characterized as diverging ONLY on a lying descriptor — new robustness row, infeasible shape); P1-P8 34 biting probes green + 10 neuter cycles with byte-identical restores; 206/206 lines + 62/62 branches reached; floor 97/97 (3.10.19); PG/sharded inapplicable re-grepped; 2091-node oracle replay + full suite 8851 x2 identical (non-green fully classified: standing RED decision + own-scratch governance transient + 2 docs-absent WS artifacts + 11 B-identical environmental). Phase-2 reconciliation: 8/8 areas match settled dispositions verbatim; DRY intent matches diff exactly; S5 untouched; 75 exactly attributed; 415/409 + 180 compositions + 6 robustness-row contents unrecoverable from surviving sources (lived in cleaned scratch) but behaviorally subsumed by superset replays — recorded honestly, no behavioral delta unexplained, nothing contradicts the settlement. Verdict: verified, No-bugs position HOLDS at fcbb964d. No new ledger row (re-proof, no change).
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 12 attack probes + control. Target digest fc442047.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-mutations-inputs-expectation.txt. Evidence: hunt-ws/mutations-inputs-verify/ records.
    - Cleanup: Removed hunt-ws/mutations-inputs, hunt-ws/mutations-inputs-verify; code-delta re-proof removed hunt-ws/mutations-inputs-verify2, hunt-ws/mutations-inputs-verify2-head, hunt-ws/inputs-verify2-phase2, hunt-ws/dumpA.json, hunt-ws/dumpA.cmp.json, hunt-ws/dumpA.nodigest.json, hunt-ws/dumpB.json, hunt-ws/dumpB.cmp.json, hunt-ws/dumpB.nodigest.json; expectation + phase-1 record + report retained in hunt-ws/ until closeout; floor-310 kept; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/operations.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (14-test unit matrix + 8-test live battery: actor permission matrix with forbidden-row absence, no-effect interruption rows, live SDL shapes; has_id_arg sabotage failed exactly 3, restored cmp-identical; oracles 35 + live 4; 4 candidates disproved); Worker-0 mechanical checks pass (digest 16223c6b == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-mutations-operations-expectation.txt`, digest f15173d7): fresh-WS replay 14/14 + 8/8 (test_00 suffix repointed, mechanical) + oracles 35/35 + full mutations 344/344 + forms/sets 103/103; 7-probe attack passed (descriptor table, derived-map drift-proofing, short-circuits, require_non_delete extremes, error single-sourcing, takes_* extremes); own permission_action-flip control failed exactly 2, restored byte-identical, 21/21 re-green. C1–C8 hold; disputed candidates stay disproved; C8 transaction-ownership confirmed (no atomic/SQL tokens in target).
    - Result: No bugs. Evidence: W1 batteries + control + oracles; W2 replay + 7 attack probes + control. Target digest 16223c6b.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-mutations-operations-expectation.txt. Evidence: hunt-ws/mutations-operations-verify/ records.
    - Cleanup: Removed hunt-ws/mutations-operations, hunt-ws/mutations-operations-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__operations.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__operations.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/operations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__operations.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__operations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/permissions.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (26-probe matrix incl. pbugs-5 shapes + axis-6 sequences; user-None-guard control failed for intended reason, restored digest-identical; oracles 28 + live 4; 5 candidates disproved); Worker-0 mechanical checks pass (digest 54f770ae == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-mutations-permissions-expectation.txt`, digest 293fc1ee, all 6 rows confirmed): fresh-WS replay 26/26 + oracles 28/28 + live 4/4; 16 attack probes passed (wrong-perm specificity ×6, anonymous update/delete, no-user-attr, bool/coroutine seams, mid-walk-clear snapshot + sealed-record refuse, exactly-once, non-bool/coroutine reject, context shapes, empty-walk allow, no-has_perm fail-loud); own fail-open control failed exactly the 2 user-None instruments, restored byte-identical, 70/70 re-green. (2 initial W2 probe failures were harness bugs, fixed in-probe.)
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 16 attack probes + control. Target digest 54f770ae.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-mutations-permissions-expectation.txt. Evidence: hunt-ws/mutations-permissions-verify/ records.
    - Cleanup: Removed hunt-ws/mutations-permissions, hunt-ws/mutations-permissions-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/resolvers.py
    - Status: verified
    - Iteration: 3. Re-opened: mutations/sets.py verification confirmed same-class residuals at `mutations/resolvers.py:266,289,322,1036,1127,1136` — registered hostile-named classes reach request-time message assembly; validation never normalizes `__name__` (producer-gated, not client-reachable by untrusted input — severity context for the re-pass). Prior verified verdict stands for all else; narrow re-pass queued.
    - Iteration: 4. Worker 1 stale re-pass: Fixed (7 label swaps + import, no logic change: :266 guard owner, :289/:1036 drift messages, :322/:323 write-step drift incl. same-class `model.__name__`, :1127 auth owner, :1136 eager-default `getattr(primary, "__name__", …)` → explicit None branch — doubly unsafe before: eager default escaped even for honest primaries + suppressed only AttributeError; plus in-audit `str`-subclass `__format__` escape) + 8 new tests in `tests/mutations/test_resolvers.py` (+306 lines; tier `tests/` — hostile metaclass producer-authored, wire-unreachable; honest rows pinned live and re-run green). Verdict per site: degrade (post-registration, inside already-typed paths; names display-only, never routing/identity/lookup — no abstract security report owed). Failability: 7 probes raw pre-fix → 7/7 post-fix; 8 new tests red pre-fix / full file 51 green post-fix (revert↔restore `cmp`-identical both ways); honest captures `cmp` IDENTICAL; shared 51 + 63 + 8 + live 6 passed; ruff + trailing-commas clean. Worker-0 mechanical checks pass (post-fix digests a322d17a/56047f2f == worktree; attribution clean — docstring-manifest line + 8-test block only; prose scan clean) and resolve W1's count note: no anomaly — 43 pre-existing + 8 new = 51; the cited "106" was always the two-file sum (43 + 63), and test_write_transaction.py is untouched at 63. Fresh Worker 2 re-verification dispatched.
    - Iteration: 1. Worker 1 reported No bugs (9-probe matrix; authorize-after-decode reorder control failed the ordering test, restored byte-identical; oracles 106 + 8 + 186; ownership in write_transaction.py, scenario corroborated); Worker-0 mechanical checks pass (digest 3fd1e571 == HEAD).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-mutations-resolvers-expectation.txt`, digest 7b7cbbe7): fresh-WS replay 9/9 (one path-string patched WS-only) + oracles 106 + atomicity 8 + permissions/products 186; 7 attack probes passed (hidden-vs-missing byte-equality with public-row control, lock True/False, null matrix, non-bool/async check_permission, delete-snapshot gid, pre-transaction deadline, async commit); own true authorize-after-decode inversion failed the ordering probe with the exact leak, restored byte-identical, 16/16 re-green (naive duplicate-decode control correctly passed — auth still first, documented). Shallow cells covered by standing oracles (judged, cited by line).
    - Iteration: 5. Worker 2 verified (delta expectation `-r2`, digest ee04ca58): fresh-WS repro 7/7 post-fix; production-only revert → 7/7 raw + 8 new tests failed; restored byte-identical; honest captures byte-identical (2736ac55 both, matching W1's); regression 51 + 63 + 8 + live 6 green; own hostile-model/hostile-primary attacks 2 red pre-fix → 2 green post-fix. Verdict-on-verdict per site: degrade correct everywhere (guard owner routes on alias sets; drift decisions via name-free pk coercion; auth decides by bool; denial text display-only; renderer traced total). Full-file audit: zero raw reads remain (5 remaining getattr lines are Django introspection / validated-name access / build-time keys). Prose clean (one bare-filename nit, acceptable). `def test` 48 vs 51 collected is parametrization, not a discrepancy.
    - Result: No bugs (iterations 1–2) + stale residuals fixed (iterations 3–5). Files changed: django_strawberry_framework/mutations/resolvers.py (7 safe-label swaps) + tests/mutations/test_resolvers.py (8 hostile-name tests).
    - Iteration: 6. Fast-forward drift check 2026-09-19: production digest a322d17a still matches;
      main-side test edits include the resolved docstring conflict (both descriptions retained) +
      adjacent rows; all 8 hunt hostile tests intact. Focused re-run `-k hostile` 10 passed in
      shared tree (8 hunt + 2 pre-existing hostile rows). Verdict stands.
    - Verification: Passed (iterations 2 + 5). Expected-before-diagnosis: hunt-ws/w2-mutations-resolvers-expectation.txt + -r2. Evidence: hunt-ws/mutations-resolvers-stale-verify/ records, post-fix digest a322d17a.
    - Cleanup: Removed hunt-ws/mutations-resolvers, hunt-ws/mutations-resolvers-verify, hunt-ws/mutations-resolvers-stale, hunt-ws/mutations-resolvers-stale-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/sets.py
    - Status: blocked
    - Iteration: 1. Worker 1 reported Fixed Low (6 raw `__name__` reads; forwarded-lead premise disproved — hostile-named class IS constructible via the public factory) with owner fix + 5 tests; Worker-0 mechanical checks pass (digests match, attribution clean, tier/prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-mutations-sets-expectation.txt`, digest 16256bcc, matches on every point): fresh-WS replay 18/18 + 112/112 (test_00 dirname literal mechanical); pre-fix revert 5 battery + 5 permanent raw; restored byte-identical; 9 attack probes passed (identity, ledger-untouched, dedup, late-finalize, SystemExit, non-str, fallback); honest messages byte-identical (0bca0373 both); owner/tier/Low concurred; prose + lint clean.
    - Iteration: 3. Behavior change recorded (review 5d, W2-challenged): the ERROR-LABEL renderer routes into GraphQL TYPE NAMING — this file's ~:1243/:1661 + mutations/fields.py ~:297. A mutation whose `__name__` raises now publishes a `<MetaclassName>Payload` type instead of failing (pinned by tests/mutations/test_fields.py ~:211). Fresh Worker 2 challenge dispatched (shared question with the mutations/fields.py item — whose prior W2 judged degrade-correct; workspace hunt-ws/5d-naming-verify; ITEM_BASELINE 0c354262): concur (record + stand) or product-semantics dispute → blocked for Rio, never regraded by fiat.
    - Iteration: 4. W2 challenge verdict BLOCKED-FOR-RIO (product-semantics dispute; report hunt-ws/reports/w2-5d-naming-report.txt): Q1 reproduced exactly (HostileNameMetaPayload in SDL/type_map/field type; pre-fix raised raw); Q2 feasible-shape invariance proven (11-shape battery diff EMPTY both eras incl. identical typed collision); Q3: degraded name CAN collide with a real type's name (typed ledger raise, confusing message), orphan premise REFUTED (trigger never registers at HEAD; fix-created state), fail-loud-at-definition alternative PROVEN non-orphaning + battery-neutral, trigger fails Rule-35 legs 2+3 (robustness posture choice, no severity), surfacing is silent (no degraded flag); Q3-R7 correction: this file's :1243 is LABEL-ONLY (true naming sites this file's :1661 + fields :297; decision point is this file's :1105 register-or-reject). EXACT QUESTION FOR RIO: (A) publish degraded `<MetaclassName>Payload` [status quo, ~:211 pin stands] or (B) reject at definition with typed ConfigurationError [fail loud, pin + hostile-register tests rewritten]? Options/consequences/non-binding-read (B)/reopen-conditions in the report. Item blocked pending Rio; prior Fixed-Low verification stands for the hunt verdict, the dispute is product semantics only.
    - Out-of-item leads assessed by W2 (read-only, none fixed): confirmed same-class residuals at `mutations/fields.py:297` (Payload line), `forms/sets.py:577,804` (+180,206,216,852,899), `rest_framework/sets.py:552` (+238,251), `auth/mutations.py:230,238` (+319), `mutations/resolvers.py:266,289,322,1036,1127,1136` — all producer-controlled, no upstream normalization; refuted for `mutations/inputs.py` (Django-model domain, breaks app loading first). Worker 0 routes them below: the four closed items go `stale` for narrow re-pass; the pending rest_framework/sets.py item carries the lead.
    - Result: Fixed Low. Files changed: django_strawberry_framework/mutations/sets.py (6 `__name__` → `_safe_class_name` hunks) + tests/mutations/test_sets.py (5 hostile-name tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-mutations-sets-expectation.txt. Evidence: hunt-ws/mutations-sets-verify/ records, post-fix digest 936f5ae7.
    - Cleanup: Removed hunt-ws/mutations-sets, hunt-ws/mutations-sets-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/_context.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (10 contract rows; 17-probe battery + 7 oracles green; 2 positive controls failing for intended reasons, restored cmp-identical; reasonable-app lead pursued with both-directions checks; no shared-tree edits). Worker-0 mechanical checks pass (digest 3d8dcfdf == HEAD; no shared changes; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-optimizer-context-expectation.txt`, digest 2ff5da83): W1 probes replayed 17/17 + 19 independent attack probes passed (sequential reuse both context kinds, actor-change on shared context, opposites, plain-schema nesting, hostile-hash boundary held as trust-boundary-correct, strictness/memo/short-circuit rows); clear-disabled control fails the unit oracle while live data stays correct via fresh per-operation frame stashes (consistent with R2/R3/R7, not a defect); 4 own probe bugs root-caused, not findings. Unverified cells: PG, sharded, async transport.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 19 attack probes + control. Target digest 3d8dcfdf.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-context-expectation.txt. Evidence: hunt-ws/optimizer-context-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-context, hunt-ws/optimizer-context-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/extension.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (11 contract rows E1-E11; 16-probe battery + 3 clear/cycle/settings probes + 200 combined oracles green; C1/C2/C2b/C3 controls failing exactly the intended rows, restored cmp-identical; cross-actor leak and dead-clear candidates disproved both-directions; concurrent +51 test in tests/optimizer/test_extension.py observed, untouched). Worker-0 mechanical checks pass (digest 49667a93 == HEAD; item-scoped optimizer diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-optimizer-extension-expectation.txt`, digest 815ffcb0): W1 probes 19/19 + oracles 182/182 (incl. the concurrent +51 row, passed, out of scope) + walker 13 + live 4 + 3 green; 7 independent attacks passed (fragment-depth guard, cross-shape reuse, strictness-warn clear extension, generator passthrough, async-cancel closure, unused-fragment tiers); key-discrimination + cache-hit controls pass; 3 own probe bugs root-caused, not findings. Unpinned no-publish clear is behaviorally correct; promoting a C2-style permanent row is a maintainer call, not a verdict condition. Unverified cells: PG, sharded.
    - Result: No bugs. Evidence: W1 battery + 4 controls + oracles; W2 replay + 7 attacks + 2 controls. Target digest 49667a93.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-extension-expectation.txt. Evidence: hunt-ws/optimizer-extension-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-extension, hunt-ws/optimizer-extension-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/extension.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/field_meta.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; t01 51 + t02 26 + t03 17 live + t04 26 hostile + t05 edges green; C1/C2 controls biting exactly on target, restored cmp-identical; GFK-fallback/snapshot/truthy-gate characterized as non-defects; no shared-tree edits). Worker-0 mechanical checks pass (digest 7215c887 == HEAD; item-scoped optimizer diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-optimizer-field-meta-expectation.txt`, digest 9c460806): W1 probes replayed 51+26+17+26+8; oracles 33 + 126 + 323 + live 250 + elision 5 green (prompt-vs-file count notes: 126 not 159, 5 elision-named not 8 — not findings); R1-flip + R2-gate controls bite exactly; independent attacks passed (unique-FK reverse shape, real CompositePrimaryKey elision refusal, N=0 relations, GFK unreachability + loud apply, 6.1 flags, deferred-elision oracles). Reason-only axes judged sound; PG/sharded/5.2-arm unverified. Concurrent +51 test file not replayed (out of scope).
    - Result: No bugs. Evidence: W1 probes + 2 controls + oracles; W2 replay + attacks + 2 controls. Target digest 7215c887.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-field-meta-expectation.txt. Evidence: hunt-ws/optimizer-field-meta-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-field-meta, hunt-ws/optimizer-field-meta-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/field_meta.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/hints.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (D1: `__class__`-liar escaping raw `RuntimeError` from `_require_prefetch`'s bare `isinstance`; guarded interrogation + liar-safe label, both entry points; no honest behavior change) + 1 permanent test in tests/optimizer/test_hints.py (tier `tests/` — hostile declaration, wire-unreachable). Worker-0 mechanical checks pass (pre-fix da46ef89 == HEAD blob; post-fix 8064af14 == worktree; attribution clean — one production hunk + one test; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-optimizer-hints-expectation.txt`, digest 2d508408): fresh-WS reproducer typed post-fix; WS-only revert → factory + direct both RAW via `hints.py:64`, permanent node failed; restored byte-identical; honest/`None`/str shapes identical pre/post. Attacks green (`__class__`→non-type, hostile bool/eq, skip-path liars, repeat, frozen, KI/SystemExit breadth acceptable per precedent, `_safe_type_name` 3/3 liar-safe). `__class__`-returns-Prefetch spoof accepted — trusted-boundary self-spoof, not a defect. Owner/tier/Low concurred. Forwarded leads (not blocking, both empirically real): `types/base.py` bare-`isinstance` trio (W1-routed, routing correct) + NEW `strategy(__class__-liar)` raw escape via `nested_fetch.py:439` (pre-existing text, owner `nested_fetch.py` — routed to that pending item). W1's overbroad strategy-path sentence noted, owned elsewhere. Suites: test_hints 43 + walker/nested_fetch/extension/base 464 green; ruff + trailing-commas clean. Unverified cells: sharded/PG (inapplicable by construction), live HTTP (unwireable shape), full suite.
    - Result: Fixed Low. Files changed: django_strawberry_framework/optimizer/hints.py (guarded `isinstance` interrogation in `_require_prefetch`) + tests/optimizer/test_hints.py (`test_prefetch_obj_rejects_class_liar_safely`).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-hints-expectation.txt. Evidence: hunt-ws/optimizer-hints-verify/ records, post-fix digest 8064af14.
    - Cleanup: Removed hunt-ws/optimizer-hints, hunt-ws/optimizer-hints-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/hints.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/join_taxonomy.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Medium (D1: reverse hop over multi-column `ForeignObject` misclassified `windowable=True` with the relation name as partition column; queryset-rooted nested connection died loud with `data=None` at path where the per-parent fallback returns exact rows) + 5 tests in tests/optimizer/test_join_taxonomy.py (tier `tests/` — no composite-PK/`ForeignObject` models in fakeshop, in-item example model forbidden; live fixture owed to Rio as blocked line). Worker-0 mechanical checks pass (pre-fix 9b355a50 == HEAD blob; post-fix e1cbb3e3 == worktree; attribution clean — one helper + three guarded sites + tests; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-join-taxonomy-expectation.txt`, digest c70f676b): fresh-WS wire reproducer exact rows + 0 window queries post-fix; WS-only revert → classification `True/"parent"/"parent"` + `FieldError` with `data=None`; restored byte-identical. 18 attacks passed (forward-FO, to_field both dirs, M2M sym/asym/self, reverse O2O/generic/self-FK/MTI/proxy still window; historical double reads preserved; lateral refuses with `None`; idempotence; planner/connector shims). Over-rejection: optimizer 849 + connection/relay/lateral 171 green. Owner correct (one check degrades all three consumers); descriptor assertions grounded by row/SQL proof; Medium concurred; live blocked line correctly scoped. Ruff + trailing-commas clean. Unverified cells: PG-lateral execution, sharded, live HTTP.
    - Result: Fixed Medium. Files changed: django_strawberry_framework/optimizer/join_taxonomy.py (`_child_link_is_virtual` + three guarded sites) + tests/optimizer/test_join_taxonomy.py (4 classification + 1 execution test).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-join-taxonomy-expectation.txt. Evidence: hunt-ws/join-taxonomy-verify/ records, post-fix digest e1cbb3e3.
    - Cleanup: Removed hunt-ws/optimizer-join-taxonomy, hunt-ws/join-taxonomy-verify; unrelated work preserved.
    - Blocked: live-tier row for the composite-`ForeignObject` fallback wants a composite-PK/`ForeignObject` fixture in fakeshop; Rio decides.
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/join_taxonomy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/lateral_fetch.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows R1-R8; 15+12 probe matrices + 93 oracles green; C1/C2 controls biting exactly, restored byte-identical; `strategy(__class__-liar)` correctly left for the nested_fetch item; PG execution explicitly unverified — refused to infer from SQLite; no shared-tree edits). Worker-0 mechanical checks pass (digest db1ea315 == HEAD; item-scoped optimizer diff empty apart from ledgered hints/join_taxonomy fixes; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-lateral-fetch-expectation.txt`, digest 7a9b286a): W1 matrices 25 passed (2 provenance-only rows deselected, provenance proven directly) + oracles 93 green + PG parity 33 skipped (no DSN); 10 independent attacks passed (`qs.none()` hook → `None`/exact `[]`, annotation-collision → `None`, visibility-IN fails closed, 5 range shapes mirror window plan field-for-field, stateful visibility row-identity); dedupe control discriminates. Reason-only axes + SQLite/PG split judged correct; PG execution explicitly unverified (not closable on SQLite). Unverified cells: PG, sharded, async.
    - Result: No bugs. Evidence: W1 matrices + 2 controls + oracles; W2 replay + 10 attacks + control. Target digest db1ea315.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-lateral-fetch-expectation.txt. Evidence: hunt-ws/lateral-fetch-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-lateral-fetch, hunt-ws/lateral-fetch-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/lateral_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/nested_fetch.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (forwarded lead D1 confirmed: raising-`__class__` liar raw at the `isinstance(value, str)` gate across 4 paths; plus adjacent D2: spoofed `__class__ → str` passing the gate then raw `TypeError` in `str.__eq__`) + 2 tests in tests/optimizer/test_nested_fetch.py (tier `tests/` — declaration-time hostile shape, wire-unreachable). Worker-0 mechanical checks pass (pre-fix 4d8d37a7 == HEAD blob; post-fix 29ce5201 == worktree; attribution clean — two guarded interrogations + docstring + tests; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-nested-fetch-expectation.txt`, digest 17e9efcc): fresh-WS reproducer 5/5 hostile typed + 6/6 honest identical post-fix; WS-only revert → 4x raw `RuntimeError` + 1x raw `TypeError`, honest 10/10 identical; restored byte-identical. 40 attack checks green (non-type/raising `__class__` incl. KI/SI breadth acceptable per precedent, hostile mro/subclasshook/eq/hash/repr/plan, repeat stability, spoof-never-matches, `CallableLiar` typed). Owner correct (single choke point; hints.py untouched correctly); ruled-out `_iterable_class` seam agreed contract-less; Low concurred. Suites: nested_fetch 20 + hints/extension 225 green; ruff + trailing-commas clean. Unverified cells: PG/sharded (inapplicable by construction), live wire (correctly absent).
    - Result: Fixed Low. Files changed: django_strawberry_framework/optimizer/nested_fetch.py (`issubclass(type(), str)` + guarded `isinstance(value, type)` gates) + tests/optimizer/test_nested_fetch.py (2 liar/spoof tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-nested-fetch-expectation.txt. Evidence: hunt-ws/nested-fetch-verify/ records, post-fix digest 29ce5201.
    - Note 2026-09-22 (maintainer edit, NOT drift, verdict stands): maintainer deleted the unreached `except BaseException` arm around `issubclass(type(), str)` + docstring rewording; worktree digest now d67e8d9d (was 29ce5201); focused trio re-run 340 passed; recorded digest updated to d67e8d9d.
    - Cleanup: Removed hunt-ws/optimizer-nested-fetch, hunt-ws/nested-fetch-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/nested_planner.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (44712901 sliced-child refusal via the connection-builder seam; recorded post-fix digest e69dbf5f obsolete, HEAD now b4dfd4a6). Prior verified verdict stands for the old digest only. Ledgered M2M silent gate intact (worktree 225011b6 vs HEAD exactly the fix hunk). Re-pass queued at the new bytes (M2M gate + slice-licence seam).
    - Iteration: 4. Fresh Worker 1 dispatched 2026-09-22 15:07 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/nested-planner-stale-r1; worktree 225011b6 vs HEAD b4dfd4a6 re-confirmed exactly the ledgered M2M gate by digest, tests 103a19da vs HEAD beee6b7d. Same scope as Iteration 3.
    - Iteration: 5. Worker 1 stale re-pass reported No bugs (8 contract rows R-A1-A3/R-B1-B5; 25-probe battery green ceiling + floor; oracles 72 + 3 + 2 live; 2 biting WS-only controls restored cmp-identical; main delta claimed docstring-only 6 lines with the M2M gate intact; 3 candidates disproved/characterized). Zero shared-tree edits; Blocked live-tier line stands, not relitigated. Worker-0 mechanical checks pass (item diff vs c9e39d31 empty — verified with corrected git, see Fold; digests match; probe digest b19eb077 on disk; collection 25 exact; no nested hunt-ws; WS DB inside; PG/sharded/async honestly unverified with a partial inapplicable reason for W2). Environment flag from W1 (confirmed by Worker-0): a concurrent harness set `core.worktree=/private/tmp/dsf-gate-050-Mebdp9` in the shared repo config — bare git commands describe a /tmp copy until released. Report /tmp/w1-nested-planner-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/nested-planner-stale-verify, expectation-first.
    - Iteration: 6. Worker 2 verified (expectation-first `hunt-ws/w2-nested-planner-stale-expectation.txt` 4484db29, every row confirmed): fresh-WS replay 25/25 + oracles 72 + 5 + full tests/optimizer 903; 29/29 independent attacks; WS-only gate-inversion control failed exactly the 22 warn/silence instruments both directions, restored cmp-identical; floor 126/126; delta re-derived as exactly the docstring hunk (2-/4+); R-B4 wiring re-proven by source read; all axes + rulings concurred (axis 3 strengthened via GraphQLSyntaxError); cells: ceiling + floor executed, PG/sharded narrowly inapplicable for the pinned rows, async resolve-time unverified with planning sync-only by construction; item diff 0 bytes; Blocked live-tier line stands.
    - Result (stale re-pass): No bugs. The 44712901 target-side delta is docstring-only and true; the ledgered M2M gate holds and the slice-licence seam degrades silently without leaking.
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-nested-planner-stale-expectation.txt. Evidence: hunt-ws/nested-planner-stale-verify/ records, worktree digest 225011b6.
    - Cleanup (stale re-pass): Removed hunt-ws/nested-planner-stale-r1, hunt-ws/nested-planner-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 1. Worker 1 reported Fixed Low (D1: M2M composite-index advisory naming an unserving child-table `(parent_id, title, id)` shape; M2M windows partition by the through parent key) + 2 tests in tests/optimizer/test_nested_index_advisory.py (tier package — helper wire-unreachable; live M2M-ordering fixture owed to Rio as blocked sub-line). Worker-0 mechanical checks pass (pre-fix 0ad8ff5d == HEAD blob; post-fix e69dbf5f == worktree; attribution clean — one gate + docstring + tests; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-nested-planner-expectation.txt`, digest 3889cb62): fresh-WS full advisory file 72 green post-fix; WS-only revert → exact wrong WARNING; restored byte-identical. Captured-SQL proof (PARTITION BY through parent key both directions; FK control by child column). 26 attacks green (M2M silent both joins; identical FK still warns — not neutered; absent-attr doubles preserve old behavior; DEBUG-off/dedup intact; window-vs-ORM identity agreement). Full tests/optimizer 853 green. Owner/tier/Low concurred (real defect, not robustness row). Ruff + trailing-commas clean. Unverified cells: PG, sharded, async.
    - Result: Fixed Low. Files changed: django_strawberry_framework/optimizer/nested_planner.py (M2M silent gate in `_advise_composite_index`) + tests/optimizer/test_nested_index_advisory.py (`test_m2m_window_stays_silent` + taxonomy pin).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-nested-planner-expectation.txt. Evidence: hunt-ws/nested-planner-verify/ records, post-fix digest e69dbf5f.
    - Cleanup: Removed hunt-ws/optimizer-nested-planner, hunt-ws/nested-planner-verify; unrelated work preserved.
    - Blocked: live-tier M2M-ordering discriminating row wants a fakeshop M2M-ordering fixture; Rio decides.
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_planner.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/plans.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (6 contract rows; 47 probes + 123 oracles green; C1/C2 controls biting exactly, restored byte-identical; 4 candidates disproved as infeasible/data-correct/owned-elsewhere; no shared-tree edits). Worker-0 mechanical checks pass (digest cce98531 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-optimizer-plans-expectation.txt`, digest a7c91008): W1 probes 41+5 + oracles 123 replayed green (P0 stale path-literal, controls re-established directly); 8 independent attacks passed (single-row partition matrix vs ORM, structural order parity, path collisions, `.only()`+keyset seeks); disproved candidates re-proven (prune elisions data-correct + unreachable, keyset conjunct row-identical/documented). Own 2 oracle bugs corrected, instruments proven fallible. Unverified cells: PG, sharded.
    - Result: No bugs. Evidence: W1 probes + 2 controls + oracles; W2 replay + 8 attacks. Target digest cce98531.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-plans-expectation.txt. Evidence: hunt-ws/optimizer-plans-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-plans, hunt-ws/optimizer-plans-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/plans.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/predicates.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; 45-battery + 6 edges green; C0/C1/C2 controls biting, restored; sole production consumer is `FilterSet._apply_flat_leaves` — walker/selections corrected as non-consumers; candidates disproved with evidence; no shared-tree edits). Worker-0 mechanical checks pass (digest 4e87c733 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-optimizer-predicates-expectation.txt`, digest 1f477c78): W1 battery 45 + edges 6 replayed green; oracles 11 + live row-preserving pins 2 green (PG EXPLAIN read, 2 skipped); 23 independent attacks passed (fan-out Counter preservation, alias double-occupation, guard completeness incl. combinator/execution loudness, cache-key code-read + live two-request differing-values probe, OR parity, hostile seam loud). A1 `AttributeError` non-defect agreed (internal seam, sole-consumer `isinstance` gate). Own probe-expectation bug corrected (production right). Unverified cells: PG, sharded, cross-DB execution.
    - Result: No bugs. Evidence: W1 battery + 3 controls + oracles; W2 replay + 23 attacks. Target digest 4e87c733.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-predicates-expectation.txt. Evidence: hunt-ws/optimizer-predicates-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-predicates, hunt-ws/optimizer-predicates-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/predicates.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/selections.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows R1-R8; 12 live probes + 12 unit + 2 cycle + 30 shared + 5 anon-inline rows green; C1/C3 controls biting, restored byte-identical; C2 alias-blind mutant reds unit rows only, live green via sibling fallback — recorded transparently; hostile-object escapes characterized robustness-only; no shared-tree edits). Worker-0 mechanical checks pass (digest a48f6172 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-optimizer-selections-expectation.txt`, digest 1fc2a5f6): unit 14 + oracles 30 + anon-inline 5 replayed green; 10 independent live attacks passed (fragments, directives both polarities, divergent aliases, `__typename` zero-query, count-observer gating, subtree prune, cyclic rejection). Rulings: (a) C2 alias branch load-bearing — mutant reds 3 oracle rows (count correction, not 2), prefix collapse proven, genuinely consumed planner input; (b) U5 unreachable — one frame per `on_execute`, memo frame-leased, no production two-infos shape; (c) hostile escapes robustness-only — zero `raise` in module, no wire path, no ConfigurationError promise. Discrepancy noted (W1's "live probes 12" file absent on disk; coverage reconstructed, not a finding). Own invalid-shape rows failed then passed — instruments discriminate. Unverified cells: PG, sharded, async.
    - Result: No bugs. Evidence: W1 probes + 3 controls + oracles; W2 replay + 10 live attacks + controls. Target digest a48f6172.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-selections-expectation.txt. Evidence: hunt-ws/optimizer-selections-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-selections, hunt-ws/optimizer-selections-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/selections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/single_parent_fetch.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; 98 combined probes+oracles green; 2 positive controls failing for intended reasons, restored cmp-identical; staff-vs-anon visibility dimension with forbidden-row absence; no shared-tree edits). Worker-0 mechanical checks pass (digest e995270a == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-single-parent-fetch-expectation.txt`, digest 77211308): W1 batteries 38+5+8+3 + oracles 33 + live 11 replayed green; 28 independent attacks passed (three-way agreement incl. Lower-tie pair, spec-None matrix, first:0/multi-parent, staff-fast vs anon-windowed live, drift fail-closed); 3 own probe bugs corrected (production right). Unverified cells: PG, sharded, async.
    - Result: No bugs. Evidence: W1 probes + 2 controls + oracles; W2 replay + 28 attacks + control. Target digest e995270a.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-single-parent-fetch-expectation.txt. Evidence: hunt-ws/single-parent-fetch-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-single-parent-fetch, hunt-ws/single-parent-fetch-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/single_parent_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/walker.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (44712901 policy-taking child builder + `_LIST_RELATION_CHILD_POLICY` sliced refusal; recorded digest 9b111ed9 obsolete, HEAD now e8d80005, worktree clean). Prior verified verdict stands for the old digest only. Re-pass queued at the new bytes (child-policy split, slice-licence seam via `_build_connection_child_queryset`).
    - Iteration: 4. Fresh Worker 1 dispatched 2026-09-22 15:29 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/walker-stale-r1; target e8d80005 + tests 78c0f7a4 re-confirmed == HEAD. Same scope as Iteration 3. Dispatch carries the git-hazard workaround (bare git describes a /tmp copy until the harness releases `core.worktree`).
    - Iteration: 5. Worker 1 stale re-pass reported No bugs IN-FENCE + 1 confirmed Low defect D1 OUT-OF-FENCE, routed unfixed (8 contract rows R1-R8; 37-probe battery green both cells + live HTTP; oracles 189; 2 biting controls restored sha-identical; delta re-derived as policy parameter + seam + call-site swap + comments). D1: hook returning union/intersection/difference on plain-list relations passes `_LIST_RELATION_CHILD_POLICY` (`reject_combined=False`) then escapes raw `NotSupportedError` at `plans.py::apply:298` (or fetch-time refilter) instead of the sealed typed `ConfigurationError` — contract row README:395 + feasible hook shape + wire input cited, 5-way evidence incl. live, fix prescription + de-risked S1 flip supplied; owner utils/querysets.py (verified), left untouched per fence. Worker-0 mechanical checks pass (item diff vs c9e39d31 empty; digests match; 5 probe digests on disk; collection 37 exact; no nested hunt-ws; sharded/PG honestly unverified). D1 rides for W2 standing/routing judgment — the querysets re-pass opens ONLY if W2 confirms standing (no premature stale marking). Report /tmp/w1-walker-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/walker-stale-verify, expectation-first.
    - Iteration: 6. Worker 2 verified BOTH duties (expectation-first `hunt-ws/w2-walker-stale-expectation.txt` 561e54f8, E1-E12 zero contradiction incl. an independently derived E10 predicting D1). (A) Walker No-bugs verified: replay 36/36 behavioral both cells (+test_00 dispensation) + oracles 189 + 2 live rows; 32/32 own attacks incl. `difference()` e2e + real fetch-time escape + live wire; 2 biting controls (one novel gate-blind) restored cmp-identical; delta re-derived exact; R4 census re-derived; floor executed, sharded/PG + async-Channels unverified; item diff empty; digests confirmed. (B) D1 HAS STANDING, routing to utils/querysets.py CONFIRMED, with scope extension: own evidence (README:395 read directly + feasible hook shape + live L1/B2/B3 incl. genuine fetch-time escape); Low concurred; prescription assessed (S1 converts all 11 nodes; prose trap confirmed verbatim; unpinned cells confirmed); EXTENSION: same class live-proven on _DEFAULT surfaces (L4/L5, S1 provably doesn't fix) + spender census + _DEFAULT-flip simulation (6910 pass, 2 premise pins fail, Decision-8 ripple) — narrow-_LIST-now with recorded _DEFAULT deferral recommended, combined-axis scope as Rio's call. Worker 0 opens the narrow re-pass now; the _DEFAULT flip rides as a recorded Rio decision (see querysets Stale note). O1-O4 noted (registry-fixture gap closed by W2; O3 oracle reckoning rides the re-pass scope).
    - Result (stale re-pass): No bugs in-fence; 1 confirmed Low defect (D1 combinator-seal escape) routed to a new utils/querysets.py narrow re-pass.
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-walker-stale-expectation.txt. Evidence: hunt-ws/walker-stale-verify/ records, digest e8d80005.
    - Cleanup (stale re-pass): Removed hunt-ws/walker-stale-r1, hunt-ws/walker-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 1. Worker 1 reported No bugs (10 contract rows R1-R10; 37 probes + 187 oracles + 18 live pins green; C1/C2/C3 controls biting exactly, restored cmp-identical; SKIP-2N+1 adjudicated perf-only, empty-hint fallthrough documented, robustness rows loud-by-contract; PG/sharded/async unverified; no shared-tree edits). Worker-0 mechanical checks pass (digest 9b111ed9 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-optimizer-walker-expectation.txt`, digest 83d2bbdb): W1 probes 36/37 replayed green (1 env-guard string-pin artifact, intent re-verified) + oracles 187 + live 343 green; 7 independent attacks passed (hook-downgrade sweep, nested poison incl. corrected expectation, only()-soundness, extremes, staff-then-anon, empty-hint rows-exact); wrong-row control fails as designed. Rulings: (a) SKIP-2N+1 agree perf-only (rows exact; R2 promises SKIP-unplanned only); (b) empty-hint fallthrough agree documented + rows-exact (one maintainer-semantics corner observed, unreachable, not a defect); (c) robustness rows agree non-blocking (loud-AttributeError posture documented, unreachable via wire/supported API). Unverified cells: PG, sharded, async.
    - Result: No bugs. Evidence: W1 probes + 3 controls + oracles; W2 replay + 7 attacks + control. Target digest 9b111ed9.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-optimizer-walker-expectation.txt. Evidence: hunt-ws/optimizer-walker-verify/ records.
    - Cleanup: Removed hunt-ws/optimizer-walker, hunt-ws/optimizer-walker-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/walker.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/base.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-20: sets_mixins.py hunt fixed liar escapes at this file's `_validate_target` gate (guarded interrogation preserving the family typed error; digest 4736fda0 → 77b8aa77). Prior verified verdict stands for the old digest only. Bounded re-verification queued (gate probes + honest behavior; full re-hunt not warranted — change is one guarded interrogation, fully exercised by the sets_mixins verification).
    - Iteration: 4. Fresh Worker 1 dispatched 2026-09-22 15:40 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/orders-base-stale-r1; worktree 77b8aa77 vs HEAD 4736fda0 re-confirmed exactly the ledgered family-gate fix by digest, tests 17ca7a2f vs HEAD db14a99e. Bounded scope per Iteration 3 PLUS the routed C1-twin flag from the filters/base re-pass (unguarded `isinstance(owner, type)` at orders/base.py:135 — confirm-or-disprove with contract rows before any edit, same owner).
    - Iteration: 5. Worker 1 stale re-pass reported Fixed Low (C1-twin CONFIRMED with probe before editing: `bind_orderset(<raising-__class__>)` + non-family target escaped the typed rejection as raw `RuntimeError: boom-class` from :135; fix is the 4-line diamond guard + docstring sentence mirroring the verified filters twin; gate + honest scope re-proven green incl. G4 no-over-capture + L1 retry) + 2 permanent tests (defect + pass-path pin, tier `tests/`). Files changed: orders/base.py (afd55efd) + tests/orders/test_base.py (dac87bf7). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the fix + 2 tests; production diff the exact twin shape; digests match claims incl. probe 0be0f831; collection 19 exact; no nested hunt-ws; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0; no new pragma; failability claimed defect-red/pin-green for W2 to re-prove; W1 scoped its own gates to fenced files). Report /tmp/w1-orders-base-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/orders-base-stale-verify, expectation-first.
    - Iteration: 6. Worker 2 verified (expectation-first `hunt-ws/w2-orders-base-stale-expectation.txt`, agreement on every row, no contradiction): fresh-WS replay 19/19 + permanent 26/26 + oracles 394/394; WS-only revert → 1 raw + 18 pass with the exact :135 traceback, restored cmp-identical (twice); honest bytes identical + C1 flip only; 29/29 attacks + 5/5 breadth probes with BaseException CORRECT re-derived (not inherited — swallowing converts interruption into a still-loud typed raise; narrower breadth would re-create the defect); floor 45/45; owner right (last unguarded read); tier + Low concurred; inapplicability with full trace; gates + prose clean. Out-of-fence: (a) RelatedOrder(".") raw ValueError noted (mixin-owned, identical pre/post, finalize types it — no action); (b) bool-hostile `if bound_class:` truthiness escape in sets_mixins.py::resolve_lazy_class folded into the queued sets_mixins re-pass scope as confirm-or-disprove (same owner already queued).
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/orders/base.py (guarded owner `isinstance` in the rejection label + docstring) + tests/orders/test_base.py (defect + pass-path pin).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-orders-base-stale-expectation.txt. Evidence: hunt-ws/orders-base-stale-verify/ records, post-fix digest afd55efd.
    - Cleanup (stale re-pass): Removed hunt-ws/orders-base-stale-r1, hunt-ws/orders-base-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; 23 probes + 125 oracles + 273 consolidated green; to-many fan-out + gate-gut controls biting, restored sha-verified; hostile-`__bool__` field_name lead routed to pending orders/inputs.py, unfixed; no shared-tree edits). Worker-0 mechanical checks pass (digest 4736fda0 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-orders-base-expectation.txt`, digest 11c8e167): W1 probes 23 replayed green; oracles 225 + live 136 + 5 + 1 green; 25 independent attacks passed (R1 completeness incl. raising-factory slot-unpoisoned; extremes no-op incl. unknown-key silent-drop pinned as observed wire-unreachable behavior; binding first-wins; scalar/to-one exact sequences; denial pre-mutation; R3 import-graph runtime proof). Lead routing CORRECT (detonation in inputs.py frames; no truthiness-safety row; honest int-typo already typed). Unverified cells: PG, sharded.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 25 attacks. Target digest 4736fda0.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-orders-base-expectation.txt. Evidence: hunt-ws/orders-base-verify/ records.
    - Cleanup: Removed hunt-ws/orders-base, hunt-ws/orders-base-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/factories.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (6 contract rows R1-R6; 38 battery + 5 live + 29/225 oracles green; M1/M2/M3 controls biting, restored cmp-identical; exclude-accepted-but-ignored noted as lead for pending orders/sets.py; FilterSet-as-root raw escape fail-closed parity; no shared-tree edits). Worker-0 mechanical checks pass (digest 4f35b66b == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-orders-factories-expectation.txt`, digest 35973313): W1 battery 38 + live 5 + oracles 29/225 replayed green; 10 + 6 live independent attacks passed (self-loop/diamond single-build, clear-then-fresh rebuild, ordered-list split, placeholder-only typed raise, camel injectivity, all-six-Ordering round-trip, nested/M2M live row orders). Exclude-deferral CORRECT (no caller, no OrderSet read; exclude-distinct metas fail loud, never silent). Own probe bug corrected. Unverified cells: PG/sharded (construction-only; R6 rows on SQLite).
    - Result: No bugs. Evidence: W1 battery + 3 controls + oracles; W2 replay + 16 attacks + control. Target digest 4f35b66b.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-orders-factories-expectation.txt. Evidence: hunt-ws/orders-factories-verify/ records.
    - Cleanup: Removed hunt-ws/orders-factories, hunt-ws/orders-factories-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/inputs.py
    - Status: verified
    - Stale 2026-09-21: input_values verification names a PROBED same-class residual at `orders/inputs.py:332` (`owner_name` unguarded `__qualname__` interpolation; real-path probe `w2-probes/test_w2_oos_orders332.py` digest d9216a9c in removed WS `hunt-ws/utils-input-values-verify/`, expectation blob 90dbcbed — lead with provenance, re-derive on current source). Target digest unchanged at 6f6ec946; prior verified verdict stands for all else. Narrow bounded re-pass queued before the gate: confirm-or-disprove :332 with a probe, fix at this owner only if confirmed; inspection scope also covers the UNPROBED qualname-interpolation mentions at orders/sets.py + sets_mixins.py + the probed orders/sets.py `== "__all__"` hostile-`__eq__` lead from the inputs hunt (confirm-or-disprove only — a confirmed defect at another owner opens its own stale re-pass).
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; 24-probe matrix + 225 oracles + 25 live green; lead reproduced then disproved as defect — developer source, no containment promise, honest misuse typed downstream, `is not-none` rewrite breaks `""` semantics; mutation control biting, restored byte-identical; no shared-tree edits). Worker-0 mechanical checks pass (digest 6f6ec946 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-orders-inputs-expectation.txt`, digest 77a785e0): W1 matrix 24 + oracles 225 + live 25 + R5-focused 2 replayed green; 11 independent attacks passed (all-six leaves typed, None/UNSET/omitted identical, explicit/absent/`""` prefix rules, list concatenation, resolve sentinels, extremes incl. staged-commit purity). Lead ruling: agree NON-DEFECT (in-process declaration only, no feasible wire/config shape, no row violated; `""`-fallback proven, int-typo typed downstream). 2 own probe bugs corrected. Unverified cells: PG/sharded/async (pure normalization, inapplicable by construction).
    - Result: No bugs. Evidence: W1 matrix + control + oracles; W2 replay + 11 attacks + control. Target digest 6f6ec946.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-orders-inputs-expectation.txt. Evidence: hunt-ws/orders-inputs-verify/ records.
    - Cleanup: Removed hunt-ws/orders-inputs, hunt-ws/orders-inputs-verify; unrelated work preserved.
    - Iteration: 3. Fresh Worker 1 dispatched 2026-09-22 15:51 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/orders-inputs-stale-r1; target 6f6ec946 + tests baf23440 re-confirmed == HEAD. Narrow scope per the Stale note (:332 confirm-or-disprove + sets_mixins qualname-mention inspection; the orders/sets leads stay with that item's own re-pass).
    - Iteration: 4. Worker 1 stale re-pass reported Fixed Low (:332 CONFIRMED with probe before editing: raising `__qualname__` escaped raw at :332 (`getattr` default catches only `AttributeError`) and unformattable `str`-subclass escaped raw at :334 (f-string `__format__`), replacing the promised typed leaf-direction rejection; fix is `owner_name = _safe_class_name(orderset_cls, qualified=True)` + import, mirroring orders/base.py:141; honest bytes proven identical; also drops the eager `_safe_arg_repr` default evaluation) + sets_mixins :549 independently CONFIRMED end-to-end (raw `name-boom`, already queued — no new trigger) + 2 permanent tests (tier `tests/`). Files changed: orders/inputs.py (889b5971) + tests/orders/test_inputs.py (a0300a00). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the 2-line fix + 2 tests; digests match claims incl. 5 probes d40b086b/bea33683/e2709c6d/6f40233d/c3f28c86; collection 16 = 15 behavioral + 1 anchor mapped per-file exact; no nested hunt-ws; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0 from root after a cwd-misfired gate run; no new pragma; failability claimed both-red-raw for W2 to re-prove; inapplicability rides for W2). Report /tmp/w1-orders-inputs-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/orders-inputs-stale-verify, expectation-first.
    - Iteration: 5. Worker 2 verified (expectation-first `hunt-ws/w2-orders-inputs-stale-expectation.txt`, agreement on every row, no contradiction): fresh-WS replay 15 passed/1 failed (:549 raw by design); WS-only revert → both permanent tests fail raw + :332 probes escape (exact frames), restored cmp-identical twice; 21/21 independent attacks (incl. str-subclass hostile-`__str__`-AND-`__format__` inert, non-str shapes typed, KI/SystemExit breadth tested not inherited, purity pins, byte-exact honest grammar; 1 own probe bug found + fixed); honest-identity proof with exactly the 2 RAW→TYPED flips; oracles 280/280 (265→280 is concurrent tree growth, superset green); floor 71/71; owner right as the last unguarded read (mirror-consistent); tier + Low concurred; :549 opinion confirms independent reproduction (verdict stays with the queued re-pass); PG/sharded inapplicable by own entry→raise trace; gates + prose clean. W1 pre-fix count corrected as reporting erratum (4/12 not 3/12 — KI probe ran standalone post-fix only).
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/orders/inputs.py (`_safe_class_name(qualified=True)` label read + import) + tests/orders/test_inputs.py (2 hostile tests).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-orders-inputs-stale-expectation.txt. Evidence: hunt-ws/orders-inputs-stale-verify/ records, post-fix digest 889b5971.
    - Cleanup (stale re-pass): Removed hunt-ws/orders-inputs-stale-r1, hunt-ws/orders-inputs-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/sets.py
    - Status: verified
    - Stale 2026-09-22: querysets-verification adjacent lead, CHARACTERIZED in-WS (not merely mentioned): `orders/sets.py` `_NormalizationLedger.claim` interpolates raw `orderset_class.__name__` plus two more in the purity-check arms — raw `RuntimeError: name-boom` escapes there (W2 evidence in `hunt-ws/utils-querysets-verify/probes/test_uq_w2_attack.py`, re-derive on current source; target 6044ab1a == recorded, clean vs HEAD). Prior verified verdict stands for all else. Narrow re-pass queued (ledger + purity-check label sites; confirm-or-disprove with contract rows before any edit). This also absorbs the two older leads below into the item's own re-pass instead of the orders/inputs inspection scope.
    - Lead 2026-09-21 (from input_values verification, UNPROBED family mention): unguarded `__qualname__` interpolation claimed in this target, same escape class as input_values D1. No contract row, feasible shape, or reaching input established — verdict stands. Assessment rides as inspection scope on the queued orders/inputs stale re-pass (confirm-or-disprove; a confirmed defect opens its own stale re-pass). PLUS lead 2026-09-21 (from the inputs hunt, probed): `_expand_meta_fields` `== "__all__"` hostile-`__eq__` raw (evidence in `hunt-ws/utils-inputs-r1/probes/test_ui_21_hostile_labels.py`, re-derive on current source) — rides the same re-pass inspection scope.
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows R1-R8; 19 probes + 103/225 oracles + 25 live green; Min/Max-swap + gate-skip controls biting exactly, restored sha-verified; exclude deferral assessed, no action; no shared-tree edits). Worker-0 mechanical checks pass (digest 6044ab1a == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-orders-sets-expectation.txt`, digest fd68a4cd): W1 probes 19 + oracles 103/225 + live 25 replayed green; 9 independent attacks passed (to-one+to-many mix with nulls carried, gate timing sync+async incl. ledger silence, invalid paths loud at both layers, first-wins binding, async parity with one-sync-boundary proof, all-null deterministic). DESC-tiebreak control discriminates; 4 own probe bugs corrected. Deferral ruling: CORRECT (zero callers; key-only participation verified; no wire reach). Unverified cells: PG, sharded.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 9 attacks + control. Target digest 6044ab1a.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-orders-sets-expectation.txt. Evidence: hunt-ws/orders-sets-verify/ records.
    - Cleanup: Removed hunt-ws/orders-sets, hunt-ws/orders-sets-verify; unrelated work preserved.
    - Iteration: 3. Fresh Worker 1 dispatched 2026-09-22 15:58 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/orders-sets-stale-r1; target 6044ab1a + tests 9e9bb5d9 re-confirmed == HEAD. Narrow scope per the Stale note (ledger + purity-check label sites, confirm-or-disprove) absorbing the two older leads per that note.
    - Iteration: 4. Worker 1 stale re-pass reported Fixed Low (one bug class, 11 sites, all three confirmed with contract rows + probes before editing: (a) ledger + purity-check `__name__` reads incl. an in-census 4th site at :497 fixed with the family and disclosed; (b) 6 `__qualname__` family sites; (c) `_expand_meta_fields == "__all__"` hostile-`__eq__` with the C1 twin structurally impossible here — single dunder, no upstream `==` to contradict; fix is 10 safe label renderers + `cls_label` hoist + guarded `bool(==)` with `except BaseException → False` + comment; honest 9-site capture diff-empty) + 15 permanent tests (tier `tests/`). Files changed: orders/sets.py (f09d9983) + tests/orders/test_sets.py (d8cb5bdb). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the 12-hunk fix + 15 tests; digests match claims incl. probe e938be6c; collection 20 exact; no nested hunt-ws; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0; no new pragma; failability claimed 14/15 red + pin green for W2 to re-prove; inapplicability + :497 family inclusion ride for W2 judgment). Routed lines: sets_mixins:549 (already queued, deliberately gate-passing probes here) + orders/inputs:332 (landed, untouched) — no new triggers. Report /tmp/w1-orders-sets-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/orders-sets-stale-verify, expectation-first.
    - Iteration: 5. Worker 2 verified (expectation-first `hunt-ws/w2-orders-sets-stale-expectation.txt` E1-E7, before the W1 report): fresh-WS replay 20/20 (one WS-name anchor edit in-copy only); WS-only revert to 6044ab1a twice → exact census 5+6+2+2 with chained context lines + 14/15 red with pin green + 103 pre-existing green, restored cmp-identical both times; 28/28 own attacks (incl. bool+repr-hostile str against the fix's own dispatch, single-dunder proof with `__ne__` counter 0, routed-seam D26/D27 mapping the sets_mixins fence; 3 own probe bugs found + fixed); C1-twin-impossibility CONFIRMED by independent static + behavioral trace (`except → False` the correct form); :497 judged legitimate same-family fix (the genuinely out-of-fence :549 correctly left); owner/tier/Low concurred; honest bytes identical 15/15 own captures; PG/sharded inapplicable by construction; async by oracle; floor 48/48; item diff exactly fix + 15 tests, test diff purely additive; gates + prose clean; the 2 long lines pre-existing outside the append range.
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/orders/sets.py (10 safe label renderers + `cls_label` hoist + guarded `==` shorthand gate + comment) + tests/orders/test_sets.py (15 hostile tests).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-orders-sets-stale-expectation.txt. Evidence: hunt-ws/orders-sets-stale-verify/ records, post-fix digest f09d9983.
    - Cleanup (stale re-pass): Removed hunt-ws/orders-sets-stale-r1, hunt-ws/orders-sets-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/permissions.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (GOAL one-rule + README visibility + module fail-closed rows; 8 live actor tests + 8 hostile-shape probes + 77/15/21 oracles green; `_walk`-disabled control 7 failed/1 passed, restored byte-identical; no shared-tree edits). Worker-0 mechanical checks pass (digest 757dce34 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-permissions-expectation.txt`, digest fb2b44dd): W1 probes 8+8 + oracles 77 + live 15 + 21 + fail-closed 21 replayed green; 7 independent attacks passed (cursor-walked pages, transitive Entry→Item/Property→Category, staff-write vs non-staff not-found + zero writes, can-view≠can-write contrast, actor-order swaps, async parity, hidden-null vs malformed-id). 2 own test-authoring failures corrected. No SECURITY.md path (nothing client-reachable). Unverified cells: PG, sharded.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 7 attacks. Target digest 757dce34.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-permissions-expectation.txt. Evidence: hunt-ws/permissions-verify/ records.
    - Cleanup: Removed hunt-ws/permissions, hunt-ws/permissions-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/registry.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; 21 probes + 80/122/142/9/34 oracles green; first-match + clear-skip controls biting, restored cmp-identical; hostile-`__name__` escape judged non-defect; foreign single-inverse tripwire assessed holds/doesn't-fire, hunk untouched; one shared-cwd control-restore incident self-reported, repaired, shared tree verified unmodified; no shared-tree edits). Worker-0 mechanical checks pass (worktree digest 612bea87 = HEAD blob + foreign hunk only; no W1 edits; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-registry-expectation.txt`, digest d4861f5b): W1 probes 21 + oracles 80/122/151 + live 32 + library 10 replayed green (two count readings documented, not findings); 16 independent attacks passed (all-mutator guard, collisions, own-call-only rollback, extremes incl. corrected probe expectation, scan scoping, hostile-`__name__` reproduced + wire-normalization + exact-str proof). Rulings: hostile-name agree NON-DEFECT (no feasible shape/input/row); tripwire agree holds (one scan, one caller, docstring-only hunk); incident handling sound. Unverified cells: sharded/PG; importlib.reload accumulation unexercised.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 16 attacks. Target worktree digest 612bea87 (HEAD blob 9cc8bb55 + foreign docstring hunk, untouched).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-registry-expectation.txt. Evidence: hunt-ws/registry-verify/ records.
    - Cleanup: Removed hunt-ws/registry, hunt-ws/registry-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Use django_strawberry_framework/registry.py as the entry point. Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/relay.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (9 contract rows C1-C9; 52 probes + 34 oracles + live rows green; decode-mutation control 13 red, restored byte-identical; hostile/override escapes loud-by-contract; foreign +5 docstring hunk attributed, intact; no shared-tree edits). Worker-0 mechanical checks pass (worktree digest 69085e7a = HEAD blob + foreign hunk only; no W1 edits; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-relay-expectation.txt`): W1 probes 52 replayed green (digests match); oracles 30 (full file — prompt said 34, no missing subset) + live 30 green; 13 independent attacks passed (strategy round-trips minted live, forged/colliding IDs safe, secondary collapse both directions via nodes(), batch positions + whole-field failures, write matrix incl. documented absent-pk passthrough, short/generator overrides, empty-ids zero queries). Length-check control red-then-green. 3 own misreadings corrected. Foreign hunk confirmed docstring-only, untouched. Unverified cells: PG, sharded, async.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 13 attacks + control. Target worktree digest 69085e7a (HEAD blob c3c5aea5 + foreign docstring hunk, untouched).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-relay-expectation.txt. Evidence: hunt-ws/relay-verify/ records.
    - Cleanup: Removed hunt-ws/relay, hunt-ws/relay-verify; unrelated work preserved.
    - Routed lead 2026-09-22 (from the finalizer stale re-pass, W2-judged NO STANDING — robustness row, no stale trigger): Node-shaped hostile-`__mro__` detonates raw first at relay-owned seams (:154 `apply_interfaces` dedup pre-scan + :245 upstream scan), reproduced pre AND post fix with both eras pinned. The Decision-1 candidate row fails verbatim (promises TypeError-from-`__bases__`-assignment only; observed is RuntimeError from the pre-scans). Fail-loud both eras, flag False, Low-at-most even if a row is later named. Verdict stands.
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/resource_policy.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (9350eb8d canonical-copy default path; recorded digest 647133d2 obsolete, HEAD now 4b69e974, worktree clean). Prior verified verdict stands for the old digest only. Re-pass queued at the new bytes (canonical-copy semantics, bound widening surface).
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows R1-R8 + Scenario-1 share; 51 + 7 probes + 295/144 oracles green; exact-type + trusted-widening controls biting, restored cmp-identical; 4 harness bugs corrected in-probe; astronomic-deadline + direct-call observations fail-closed/documented, not defects; no shared-tree edits). Worker-0 mechanical checks pass (digest 647133d2 == HEAD; item-scoped diff empty; test-file dirt is the ledgered extension-item hunks only; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-resource-policy-expectation.txt`, digest 7c97876c): W1 probes 51+7 + oracles 295/144 replayed green; 21 independent attacks passed (admit/reject boundaries with side-effect flags, monotonicity incl. double-spread charging, dimension check with corrected walker-typing premise, literal-True-only widening, no disable spelling, hostile shapes bounded, deadline matrix, isolation incl. sync_to_async + refused-schema paths). Every rejection paired with at-limit admit twin. Unverified cells: PG, sharded.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 21 attacks. Target digest 647133d2.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-resource-policy-expectation.txt. Evidence: hunt-ws/resource-policy-verify/ records.
    - Cleanup: Removed hunt-ws/resource-policy, hunt-ws/resource-policy-verify; unrelated work preserved.
    - Iteration: 3. Fresh Worker 1 dispatched 2026-09-22 16:14 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/resource-policy-stale-r1; target 4b69e974 == HEAD (clean — the target never moved; the ladder under it did). Shared oracles carry the VERIFIED extensions fix hunks (tests 04bb52b6 vs HEAD b9db7c2f, live 3760eb99 vs HEAD bd32df87): attribution baseline, never touch. Scope: re-hang the boundary contract at the new canonical-copy bytes per the Stale note.
    - Iteration: 4. Worker 1 stale re-pass reported No bugs (8 contract rows R1-R8 re-proven at the new bytes; 75-probe battery + 4 disproofs green default + floor; oracles 299 + 146 live; 2 biting controls restored sha-identical; main delta confirmed as exactly the 5-hunk canonical-copy re-pointing; 8 candidates disproved/characterized). Zero shared-tree edits; no permanent test owed. Worker-0 mechanical checks pass (delta since dispatch empty — target 0 diff bytes, oracles exactly the dispatch digests; the diff vs c9e39d31 shows the VERIFIED sibling extensions fix that landed mid-re-pass, correctly attributed by W1; collection 79 exact; no nested hunt-ws; WS DB inside; cells nuanced per the prior verdict for W2). CAVEAT WITHDRAWN (see Fold 16:45): the "drift" was Worker-0's hash-function error — probes match the claims exactly under sha256 (b4b3da12/b48100eb); no drift. Counts + anchors + oracles verify; W2 re-hashes from disk as briefed. Report /tmp/w1-resource-policy-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/resource-policy-stale-verify, expectation-first.
    - Iteration: 5. Worker 2 verified (expectation-first `hunt-ws/w2-resource-policy-stale-expectation.txt`, full R1-R8 agreement, zero contradiction): fresh-WS replay 79/79 + oracles 299 + 146 live, both cells (floor stronger than W1's — full oracles too); 19/19 own attacks both cells; WS-only miss-path mutation failed exactly the 2 tamper pins, restored cmp-identical with the sha256 corroborating W1's independently reported hash; drift-caveat dissolved (same bytes, different hash functions — matching Worker-0's withdrawal); delta re-derived as exactly the 5 hunks; item diff = target 0 bytes + oracle 71 insertions exactly the sibling D1 tests; split-cell judgment holds; C1-C8 concurred with one erratum (C3's "sole caller" is two syntactic sites — evidenced non-defect per the trust-boundary rule); ruff clean.
    - Result (stale re-pass): No bugs. The boundary contract re-hangs cleanly on the canonical-copy ladder.
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-resource-policy-stale-expectation.txt. Evidence: hunt-ws/resource-policy-stale-verify/ records, digest 4b69e974.
    - Cleanup (stale re-pass): Removed hunt-ws/resource-policy-stale-r1, hunt-ws/resource-policy-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/rest_framework/hook_context.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; 11 matrix + 6 live + 494/20/29 oracles green; instance_pk=None mutant failing as intended, restored cmp-identical; hook isolation + pk-snapshot-authority proven; no shared-tree edits). Worker-0 mechanical checks pass (digest f4910159 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-hook-context-expectation.txt`, digest ee886194): W1 matrix 11 + oracles 494 + live 29/20 replayed green; 8 independent attacks passed (hostile setattr/TypeError with exact write after, validation field-keyed + zero rows, empty/partial payloads, forged instance_pk still injects real instance end-to-end, denied caller zero constructions/writes, create/update pk recording, upload descriptor isolation). No SECURITY.md path. Unverified cells: PG, sharded, async.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 8 attacks. Target digest f4910159.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-hook-context-expectation.txt. Evidence: hunt-ws/hook-context-verify/ records.
    - Cleanup: Removed hunt-ws/rest-framework-hook-context, hunt-ws/hook-context-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/hook_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/rest_framework/inputs.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows C1-C7; 10 probes + 2 raw-escape records + 494/20/29 oracles green; generated-input fidelity holds both directions via real serializers; 2 confirmed Low behaviors forwarded to pending rest_framework/sets.py as leads with tracebacks, unfixed here; no shared-tree edits). Worker-0 mechanical checks pass (digest 9b17d952 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-rf-inputs-expectation.txt`, digest f6be4c15): W1 battery 10 + 2 records + oracles 494/20/29 replayed green; 15 independent attacks passed (scalar round-trip, FK required, nested opt-in/out, many=True, extremes incl. canonical-name divergence, benign-invalid typed). Lead rulings: Lead 1 real (frame-pinned to `_validate_schema_field_map`) / routing correct / Low agree; Lead 2 real (bind + direct) / routing correct / Low agree. Own probe bug corrected. Unverified cells: PG/sharded/async (pure substrate, inapplicable by construction).
    - Result: No bugs. Evidence: W1 battery + 2 records + oracles; W2 replay + 15 attacks. Target digest 9b17d952.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-rf-inputs-expectation.txt. Evidence: hunt-ws/rf-inputs-verify/ records.
    - Cleanup: Removed hunt-ws/rest-framework-inputs, hunt-ws/rf-inputs-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/rest_framework/resolvers.py
    - Status: verified
    - Iteration: 3. Re-opened 2026-09-19: rest_framework/sets.py verification confirms ~15 raw `__name__` runtime sites in this target now reachable via valid hostile-named registrations (same pattern as the mutations/resolvers.py stale re-pass after mutations/sets.py). Prior verified verdict stands for all else; narrow re-pass queued.
    - Iteration: 4. Worker 1 stale re-pass: Fixed (53 label swaps, no logic change: 41 `mutation_cls.__name__` + 6 `type(serializer)` + 4 `type(runtime)` + 1 validator + 6 model, via `_safe_class_name`/`_safe_type_name`; guarded leaf label + `getattr(x, '__name__', x)` pair + zero qualname/dict reads confirmed untouched by design) + 23 hostile-label tests / 27 nodes (register/bind premise, per-function sites, `EvilStr` format escape, 2 honest byte-pins, 2 end-to-end write-step rows; tier `tests/` — producer-authored metaclasses wire-unreachable). Verdict per site: degrade (post-registration, display-only, inside already-typed paths). Failability: 20 raw escapes pre-fix with registered hostile class → 28 green post-fix; honest captures HONEST-IDENTICAL; WS-only revert re-reddens 3/3 sampled; shared focused 30 + full 202 + dir 547 green; ruff + trailing-commas clean. Worker-0 mechanical checks pass (post-fix digests c0b54039/d4eb65c7 == worktree; attribution clean — label swaps + docstring + test block only; prose scan 0 hits). Fresh Worker 2 re-verification dispatched.
    - Iteration: 1. Worker 1 reported Fixed Low (D1-D4: raw escapes at hook boundaries with explicit typed contracts — liar mapping, liar freeze leaf, liar context/hostile-eq/hostile-repr alias, hostile-repr key) + 7 hostile-hook tests in tests/rest_framework/test_resolvers.py (tier `tests/` — producer-authored hook shapes, wire-unreachable). Out-of-scope left correctly: sets.py:552 construction site + `__name__` runtime labels (unreachable until sibling fixes construction). Worker-0 mechanical checks pass (pre-fix 8024703e == HEAD blob; post-fix 531aca26 == worktree; attribution clean — guarded interrogations + safe renderers + docstrings + tests; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-rf-resolvers-expectation.txt`, digest 9706b33a): fresh-WS 7/7 typed post-fix; WS-only revert → 7 raw escapes for intended reasons; restored byte-identical. 11 attacks passed (hostile hash/iter/len, nested liars, metaclass-`__name__` leaf, equal-but-hostile-repr alias ACCEPTED, None context, KI/SI breadth interrogation-only with hook-body KI propagating). Honest invariance byte-identical (benign renderer ≡ repr). Owner correct (sets.py:552 correctly OUT); C1-C5 intact (175 + 501 + 250-live green); Low concurred. Ruff + trailing-commas clean. Unverified cells: sharded/PG (pure-Python dunder interrogations).
    - Iteration: 5. Worker 2 verified (delta expectation `-r2`, digest fce3bedc): fresh-WS 30/30 hostile green post-fix + 7 independent probes; production-only revert → 23 failed raw + 4 honest-path passes (honest unaffected); restored byte-identical. Regression: full rest_framework 547 green. No-logic-change audit (label swaps + docstrings + import + one formatter explosion only). Degrade holds per site (raise-site/display strings; `{name}` never branched; alias-only routing). Untouched pair proved (hostile model fails at ModelBase construction). Lint/prose/tier clean. Robustness rows for Rio as new-card candidates (out of slice, pre-existing, byte-identical across versions, producer-only): hostile-`__str__` dict key in hand-built `ValidationError` detail at `_error_node_children::str(key)`; hostile-`__repr__` custom-`save()` return at `{saved!r}`. Unverified cells: sharded/PG (inapplicable), async, live HTTP.
    - Result: Fixed Low (iterations 1–2) + stale residuals fixed (iterations 3–5). Files changed: django_strawberry_framework/rest_framework/resolvers.py (hook-boundary guards + 53 safe-label swaps) + tests/rest_framework/test_resolvers.py (7 hostile-hook + 23 hostile-label tests).
    - Verification: Passed (iterations 2 + 5). Expected-before-diagnosis: hunt-ws/w2-rf-resolvers-expectation.txt + -r2. Evidence: hunt-ws/rf-resolvers-stale-verify/ records, post-fix digest c0b54039.
    - Cleanup: Removed hunt-ws/rest-framework-resolvers, hunt-ws/rf-resolvers-verify, hunt-ws/rest-framework-resolvers-stale, hunt-ws/rf-resolvers-stale-verify; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/rest_framework/serializer_converter.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (D1 list nullable-element loss; D2 choice allow_blank loss; D3-D6 hostile `__name__` escapes in typed raises) + 6 tests in tests/rest_framework/test_converter.py (tier `tests/` — no ListField/allow_blank fixtures; live rows blocked on fixture, owed to Rio). Worker-0 mechanical checks pass (pre-fix 32904418 == HEAD blob; post-fix 95568390 == worktree; attribution clean — converter hunks + tests; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-serializer-converter-expectation.txt`, digest 299b458a): DRF↔GraphQL acceptance agreement proven both defects post-fix; WS-only revert → 6 failures (assertion diffs + raw RuntimeErrors) + wire proof of both gaps; restored byte-identical, 101 green. Design rulings: D1 widen correct (spec-039 rule one level down; orthogonal to outer widening; no conflicting forms rule); D1/D2 asymmetry principled (widen when representable, decline when not — FilePath precedent); no other allow_* gaps (MultipleChoice+allow_blank verified round-trip; empty/no-child/file still loud). No remaining raw field-instance reads (residuals are trusted registration/Django/scalar names). Owner single-file correct; tier + blocked live line correctly scoped; Low concurred. Ruff + trailing-commas clean. Unverified cells: PG/sharded (no DB decision), live HTTP D1/D2 (blocked fixtures).
    - Result: Fixed Low. Files changed: django_strawberry_framework/rest_framework/serializer_converter.py (nullable-element widening, allow_blank exclusion, 6 safe-name swaps) + tests/rest_framework/test_converter.py (2 conversion + 4 hostile tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-serializer-converter-expectation.txt. Evidence: hunt-ws/serializer-converter-verify/ records, post-fix digest 95568390.
    - Cleanup: Removed hunt-ws/rest-framework-serializer-converter, hunt-ws/serializer-converter-verify; unrelated work preserved.
    - Blocked: live-tier rows for `ListField(nullable child)` and `Choice(allow_blank)` want fakeshop serializer fixtures; Rio decides.
    - Behavior change recorded (review 5d): the allow_blank fix changes the PUBLISHED schema (enum → String). DECISION REQUEST: Rio signs off before the gate. No Worker challenge dispatched (decision-owned, not evidence-owned).
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/serializer_converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/rest_framework/sets.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (Lead A: 6 `__name__` sites → safe renderers; Lead B: 2 guarded `isinstance`; Lead C: identifier gate extending plain-str gate) + 10 tests / 13 nodes in tests/rest_framework/test_sets.py (tier `tests/` — hostile declaration shapes, wire-unreachable). Worker-0 mechanical checks pass (pre-fix 2c7117d6 == HEAD blob; post-fix def19a9e1 == worktree; attribution clean — guarded interrogations + gate + renderers + docstrings + tests; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-rf-sets-expectation.txt`, digest bd8d9857): fresh-WS 17/17 + full 107 green post-fix; WS-only revert → 13 failures (9 raw RuntimeErrors + 4 accepted-then-SyntaxError); restored byte-identical. Lead C end-to-end: pre-fix raw SyntaxError at finalize → post-fix typed at class creation. Attacks: hostile hash/eq/str/repr keys typed; gate exactly identifiers-minus-keywords; drift+hostile-name bind typed with degraded label; equal-valid re-declaration dedupes. No remaining raw reads except :911 framework-generated class. Owner single-file correct; tier + Low concurred; new-lead routing correct and OUT. Ruff + trailing-commas clean (per W1; W2 confirms format/check clean). Live compatibility: products 160 green. Unverified cells: sharded/PG, async.
    - Iteration: 3. Behavior change recorded (review 5d, W2-challenged): new rejection of non-identifier keys from `get_serializer_for_schema` (~:196 — the identifier gate; the maintainer's arm deletion removed only the dead `except` around the check, the rejection itself stands). Fresh Worker 2 challenge dispatched (workspace hunt-ws/5d-rfsets-verify; ITEM_BASELINE 3e27c255): concur (record + stand) or product-semantics dispute → blocked for Rio, never regraded by fiat.
    - Result: Fixed Low. Files changed: django_strawberry_framework/rest_framework/sets.py (safe renderers + guarded interrogations + identifier gate) + tests/rest_framework/test_sets.py (10 hostile/identifier tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-rf-sets-expectation.txt. Evidence: hunt-ws/rf-sets-verify/ records, post-fix digest def19a9e1.
    - Note 2026-09-22 (maintainer edit, NOT drift, verdict stands): maintainer deleted the unreached `except BaseException` arm around the identifier check + docstring rewording; worktree digest now 70a1e1b1 (was def19a9e1); focused trio re-run 340 passed; recorded digest updated to 70a1e1b1.
    - Cleanup: Removed hunt-ws/rest-framework-sets, hunt-ws/rf-sets-verify; unrelated work preserved.
    - Iteration: 4. Worker 2 product-semantics challenge on the recorded non-identifier gate (Q1-Q3, workspace hunt-ws/5d-rfsets-verify): verdict (a) CONCUR — rejection stands. Q1: post-fix typed `ConfigurationError` at class creation naming mutation + hook + rule + key; pre-fix class creation passed and finalize raised raw `SyntaxError` naming nothing. Q2: honest DRF shapes byte-identical pre/post; every accepted->rejected shape requires producer-authored non-identifier bindings (producer bug, no wire reach). Q3: deprecate-first alternative named and declined. Shared tree never edited (digests 70a1e1b1/85c4c3a0; fence-vs-3e27c255 empty). Report: hunt-ws/reports/w2-5d-rfsets-report.txt. Workspace removed. Item stays verified.
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/routers.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (hostile interrogation shapes escaping the consumer-injection seam raw; guarded all four interrogations, `issubclass` deliberately unguarded) + 4 nodes in tests/test_routers.py (tier `tests/` — construction-time validation, no WS mount in fakeshop). Worker-0 mechanical checks pass (pre-fix a18c5001 == HEAD blob; post-fix d5c43509 == worktree; attribution clean — guarded interrogations + docstrings; prose clean).
    - Iteration: 2. Worker 2 verified (expectation-first `hunt-ws/w2-routers-expectation.txt`, digest 79bedec6): fresh-WS reproducer 5/5 typed post-fix; production-only revert → 4 raw + 1 typed (subclasscheck pin, safe by design); restored byte-identical. Honest constructions byte-identical pre/post. Attacks: repr-liars typed, async factory rejected + closed, hostile subclasscheck never consulted, KI/SI breadth acceptable, branch order preserved. Two apparent holes closed by evidence (`__call__`-property liar genuinely callable → factory-body passthrough by design; hostile django_application genuinely callable → R5 N/A). Owner/compatibility/tier/Low concurred (212 green incl. composition + isolation rows). Ruff + trailing-commas clean. Unverified cells: PG/sharded (inapplicable by construction); async via suite rows.
    - Result: Fixed Low. Files changed: django_strawberry_framework/routers.py (guarded seam interrogations) + tests/test_routers.py (4 hostile-interrogation nodes).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-routers-expectation.txt. Evidence: hunt-ws/routers-verify/ records, post-fix digest d5c43509.
    - Note 2026-09-22 (maintainer edit, NOT drift, verdict stands): maintainer deleted the two unreached `except BaseException` arms around `callable()` + docstring rewording; worktree digest now bc30430e (was d5c43509); focused trio re-run 340 passed; recorded digest updated to bc30430e.
    - Cleanup: Removed hunt-ws/routers, hunt-ws/routers-verify; unrelated work preserved.
    - Iteration: 3. Fresh Worker 1 dispatched 2026-09-23 UTC, ITEM_BASELINE 33b70ed1, workspace hunt-ws/5e-layout-prose (bounded layout revision: [5e] row 3, routers.py :256 mis-indented renumbered list; comment-only — tests 25836232 untouched). W2 verification follows in-unit.
    - Iteration: 4. Worker 1 layout revision landed (whitespace-only 5 lines 8->7 spaces in `_factory_application` docstring; production bc30430e -> 2f906095, tests 25836232 untouched). Worker-0 mechanical checks pass (item diff vs 33b70ed1 exactly the two hunks; -w diff empty; focused test green — re-run by Worker-0; ruff check + format clean — re-run by Worker-0; no new pragma). Fresh Worker 2 verification dispatched (ITEM_BASELINE 96833df4, workspace hunt-ws/5e-layout-prose-verify; joint over both files).
    - Iteration: 5. Worker 2 VERIFIED the joint layout revision (expectation-first, K1-K6 all PASS: exact two hunks; independent indent re-measurement of every touched + sibling line; whitespace-stripped content diff 0 lines; independent co_code proof 13/13 + 40/40 + reverse-apply failability to bc30430e/a4b301c3; own nearest-test selection green + both modules collect clean + W1 nodes replayed; ruff clean; W1 report audited — ZERO discrepancies). Shared tree never edited by W2 (fences re-hashed; fence-vs-96833df4 empty). Report: hunt-ws/reports/w2-5e-layout-prose-report.txt. Workspaces removed; expectation file retained in hunt-ws/ until closeout. [5e] row 3 CLOSED (routers half); item stays verified.
    - docs/shadow/current/django_strawberry_framework__routers.stripped.py
    - docs/shadow/current/django_strawberry_framework__routers.overview.md
    - Prompt:
        - Use django_strawberry_framework/routers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__routers.stripped.py and docs/shadow/current/django_strawberry_framework__routers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/scalars.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows C1-C7; 21 hunt probes + 32/80/79/15 oracles green; regex-neuter + collision-disable controls biting, restored byte-identical; huge-digit edge fail-closed characterized; no shared-tree edits). Worker-0 mechanical checks pass (digest 5e354042 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-scalars-expectation.txt`, digest 90337fc8; no diagnosis supplied — uncontaminated by construction): hunt probes 21 + oracles 32/80/7/15/72 replayed green (243 consolidated); 16 independent attacks passed (serialize(parse) identity incl. past-safe-int/past-64-bit, float-integrals rejected both directions, base-slot str bypass, 4000-digit round trip; 19-malformed + 11-literal + 9-variable sweeps all `data None`; extra-map/generator merge, hostile keys contained, map immutability, relay/camel parity + SDL; builtins live; 5001-digit/10**5000 ValueError never truncated; bytes/Decimal/NaN/complex rejected; C6 masked-message + data-None pin). 2 own caller-side literal bugs corrected. Unverified cells: PG (psycopg2 absent), sharded (pure functions + sqlite live only).
    - Durable evidence (compact): expectation C1-C7 strict parse/serialize/symmetry/config/Upload/masking/dispatch; replay = hunt_probes (21) + test_scalars (32) + live scalars/filter/uploads/converters; controls = regex-widen + collision-disable (bite red, restore identical); attacks = identity/round-trip + malformed sweeps + hostile shapes + digit-limit edges, all `data None` on rejection. Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 16 attacks. Target digest 5e354042.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-scalars-expectation.txt. Evidence: hunt-ws/scalars-verify/ records.
    - Cleanup: Removed hunt-ws/scalars, hunt-ws/scalars-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Use django_strawberry_framework/scalars.py as the entry point. Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/schema.py
    - Status: verified
    - Stale 2026-09-22: txn-scenario W1 fix landed in this verified file (async shield-handoff in `_execute_mutation_field_async`, 19f90bf5 → d0c79838; tests/test_schema.py +4 handoff tests + 5 helpers). Prior verified verdict stands for the old digest only. The scenario verification covers the handoff delta; a bounded re-pass (re-proof of the R0-R9 load-bearing rows at the new bytes, no full re-hunt) is queued after the scenario closes, before the gate. Evidence: /tmp/w1-scenario-txn-r1-report.txt + scenario_txn/TX10A probes + TX10A-PREFIX.log (pre-fix witness); re-derive on current source at dispatch.
    - Iteration: 3. Re-opened 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (9350eb8d canonical-copy enforcement record; recorded digest c2e1b748 obsolete, HEAD now 19f90bf5, worktree clean). Prior verified verdict stands for the old digest only. Re-pass queued at the new bytes (enforcement record vs canonical copy).
    - Iteration: 1. Worker 1 reported No bugs (9 contract rows C1-C9; 17 fresh probes + 143/64/63/30/8 oracles green; always-on-masking + isinstance controls biting, restored byte-identical; cancel-during-close race analyzed timing-only; no shared-tree edits). Worker-0 mechanical checks pass (digest c2e1b748 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-schema-expectation.txt`, digest 50ac7467; no diagnosis supplied): hunter probes 17 + oracles 143/64/63 + live 69/8 + 23 independent attacks green (double-declaration both orders, 4 subclass refusals, object entry, raising-factory per-op refusal, distinct authorities + copies, sequential+concurrent isolation, refused identical sync/async + still bounded, completion rollback, hook masking + plain-Schema leak control). All replays passed against concurrently-edited extensions/error_policy.py (bd763bcc) — no breakage to report; that stale re-hunt still waits for stability. Streamed-refusal via oracle stream cases. Unverified cells: PG, sharded.
    - Durable evidence (compact): expectation C1-C9 (construction validation, per-op isolation, refused behavior, transaction spanning, masking seam); replay = hunt_probes (17) + schema/errorpolicy/writetx oracles + live hooks/atomicity; controls = always-on-masking + isinstance-neuter (bite red, restore identical) + embedded tight/raw/clean variants; attacks = isolation identity-freshness, concurrency, rollback, seam-ownership leak control. Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 23 attacks. Target digest c2e1b748.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-schema-expectation.txt. Evidence: hunt-ws/schema-verify/ records.
    - Cleanup: Removed hunt-ws/schema, hunt-ws/schema-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 4. Fresh Worker 1 dispatched 2026-09-22 16:27 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/schema-stale-r1; target 19f90bf5 + tests b98ddb8f re-confirmed == HEAD (the Stale note's ebe68a27 waypoint predates 9350eb8d — the dispatch bytes already include that rewrite plus ffce6f29/f7192bfb/3efa11a9; no new drift, scope stands). Scope per Iteration 3 (enforcement record vs canonical copy).
    - Iteration: 5. Worker 1 stale re-pass reported No bugs (10 contract rows R0-R9; 38-probe battery green both cells; oracles 640 package + 216 live; 3 biting WS-only controls restored cmp-identical; rewrite confirmed as exactly 9350eb8d's 10-line delta — the ffce6f29/f7192bfb/3efa11a9 commits predate the baseline, correcting the dispatch brief's range imprecision; 2 candidates characterized as non-defects with no-row reasons). Zero shared-tree edits; no permanent test owed. Worker-0 mechanical checks pass (item diff empty; digests match; 4 probe sha256 match claims exactly — 9a412fda/a65f781d/4cbd0c89/b110f34d; collection 38 exact; no nested hunt-ws; WS DB inside; PG unverified + sharded partial-verdict for W2 to judge). Report /tmp/w1-schema-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/schema-stale-verify, expectation-first.
    - Iteration: 7. Bounded second re-pass (post-scenario) reported No bugs on scope, zero shared-tree edits: R0-R9 all re-proven HOLDS at 6f238a09/266a09e0 (46-node scratch battery + 369 oracle nodes green ceiling; 263+6 floor); compatibility C-A/C-C/C-E behavioral + C-D source-proof clean; drift account byte-exact (HEAD blob 19f90bf5, main log empty, worktree-vs-HEAD exactly the 5 settled handoff hunks 108+/4- + window tests 879+/1-); M1/M2 neuters bite exactly the comparison-driven rows with cmp-identical restores; R7 cross-alias + PG window legs honestly unverified, R0-R6/R8 PG/sharded inapplicability claimed by grep-proof for W2 to judge. Worker-0 mechanical checks PASS (digests match; fence-vs-ITEM a79056f2 EMPTY — only this file moved; HEAD blob + log + diffstat + hunk counts all re-verified; WS hashes equal shared; anchor re-run green WS/WS; battery collects exactly 46; strays only pre-existing honest_*.txt; no /tmp cites; report under hunt-ws/reports/). Fresh Worker 2 two-phase dispatched (fenced phase 1 from quoted R0-R9 + current-bytes diff; expectation hunt-ws/w2-schema-stale-expectation-r2.txt; workspace hunt-ws/schema-stale-verify2; phase-2 drop gated on W0 contamination check).
    - Iteration: 8. Worker 2 verified the bounded re-pass (expectation-first `hunt-ws/w2-schema-stale-expectation-r2.txt`, W0-sealed ae2902ef pre-run, re-hashed unmodified at close; fenced phase 1, drop-gated phase 2): 102 own probes green both cells + 46/46 W1-battery replay + 291 package / 256 live oracles + M1/M2 neuter spot-replays with cmp-identical restores + byte-exact drift inventory (HEAD blob, 5+3 hunks, empty ITEM diff, main log re-verified); all 8 ride-alongs agree (R2 genuinely proven incl. trigger-irrelevance-by-construction; line-480 inapplicability re-grepped wider; R7 PG honestly unverified with sqlite cross-alias going further; floor independently confirmed; seams S1-S5 agree with W1's C-A..C-E with strengths compared; rule-35 agree, N1/N2 concur non-defect); 2 nits explicitly NOT challenges (M1 selection unnamed; axis-1 extensions=[7] vs =7, same standing). Verdict: verified, No bugs on this scope; zero shared-tree edits by either worker (digests 6f238a09/266a09e0 re-hashed at close). No new ledger row (re-proof, no change); the single verdict triple below stands, this cycle carried by Iterations 7-8.
    - Iteration: 6. Worker 2 verified (expectation-first `hunt-ws/w2-schema-stale-expectation.txt`, full R0-R9 agreement, no contradiction): fresh-WS replay 37/37 behavioral (test_00 dispensation, stdout-proven) + oracles 603 + 216 live exact; 31/31 own attacks both cells (floor 68/68); WS-only rollback-comparison neuter failed exactly the 4 comparison-driven rows, restored cmp-identical (sha256 matches W1's pristine pin); delta re-derived as exactly 10 +/- lines (9350eb8d sole toucher, merge-base proven); both non-defects concurred with own evidence; axes re-discharged with greps; cells: floor executed, PG unverified, sharded R7-leg unverified, R0-R6/R8 inapplicable grep-proven; gates clean. W1's "640" corrected as erratum (641 = 38 + 603).
    - Result (stale re-pass): No bugs. The canonical-copy enforcement record holds at the rewritten bytes.
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-schema-stale-expectation.txt. Evidence: hunt-ws/schema-stale-verify/ records, digest 19f90bf5.
    - Cleanup (stale re-pass): Removed hunt-ws/schema-stale-r1, hunt-ws/schema-stale-verify; second re-pass removed hunt-ws/schema-stale-r2, hunt-ws/schema-stale-verify2, hunt-ws/schema-verify2-phase2; both expectation files + all four re-pass reports retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__schema.stripped.py and docs/shadow/current/django_strawberry_framework__schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/sets_mixins.py
    - Status: verified
    - Stale 2026-09-22: filters-sets W2 verification reproduces (A20, identical pre/post-fix) a hostile-cls + generator-fields raw `RuntimeError: name-boom` escaping at `require_re_readable_field_declaration:549` via `sets.py get_fields:1482` — contract row (the gate's typed "Meta.fields must be" rejection) + feasible shape + reaching input through real class creation all named: HAS STANDING. Prior verified verdict stands for all else. Narrow re-pass queued in inventory order (after the schema.py re-pass, before types/base.py): label reads in this file's messages; confirm-or-disprove with contract rows before any edit. Evidence: A20 repro text in /tmp/w2-filters-sets-stale-report.txt (the w2-attacks/ workspace was consumed at that item's closeout) + /tmp/w1-orders-inputs-stale-r1-report.txt for the :549 corroboration; re-derive on current source at dispatch. Scope addition 2026-09-22 (from orders/base verification, lead (b)): bool-hostile `if bound_class:` truthiness escape in `resolve_lazy_class` (raw `RuntimeError: bool-boom`, pre-existing, finalize still types it) — confirm-or-disprove alongside the :549 labels. Corroboration 2026-09-22: the orders/inputs re-pass independently confirmed :549 end-to-end (own probe, raw `name-boom`) — second confirmation, same queued re-pass.
    - Lead 2026-09-21 (from input_values verification, UNPROBED family mention): unguarded `__qualname__` interpolation claimed in this target, same escape class as input_values D1. No contract row, feasible shape, or reaching input established — verdict stands. Assessment rides as inspection scope on the queued orders/inputs stale re-pass (confirm-or-disprove; a confirmed defect opens its own stale re-pass).
    - Iteration: 1. Worker 1 reported Fixed Low (liar escapes at 9 sites across sets_mixins.py + filters/base.py + orders/base.py; hook-level guards + `_bind_related_declaration` helper) + 9 hostile tests (tier `tests/`). Worker-0 mechanical checks pass (pre-fix digests == HEAD blobs; post-fix 48b8ca20/91c41b1f/77b8aa77 == worktree; attribution clean — 6 files, all hunks hunt's; prose scan 0 hits). Filters/base.py + orders/base.py marked stale (bounded re-verification queued).
    - Iteration: 2. Worker 2 phase-1 verified the fix (expectation-first `hunt-ws/w2-sets-mixins-expectation.txt`, digest a6d5bbb0): liar replay typed post-fix + raw pre-fix (21/21), restored byte-identical; 26 attacks green; ImportError passthrough holds; owner/hook-level/tier/Low concurred. Residual lead routed out (end-to-end `Meta.fields` raising-liar at filters/sets.py get_fields + utils/inputs.py canonicalize + upstream django_filters — pre-existing, out of 6-file diff).
    - Iteration: 3. Worker 2 phase-2 reconciliation: revision-needed on ONE item-scoped gap — new diamond-`except` guard lines (`sets_mixins.py` 375-376) uncovered by the entire related surface (198 stmts, 2 missed, 99%; honest values never raise under `isinstance`, so only a hostile test reaches it). Pragma route NOT sanctioned here (branch is runner-reachable). All else stands verified. Same item back to Worker 1 with workspace intact.
    - Iteration: 4. Worker 1 revision: +1 test (`test_collect_related_declarations_reconciliation_drops_unclassifiable_selected`, +38 lines, only file edited; production byte-identical); focused 490 green; coverage 198/0/100%; ruff + trailing-commas clean.
    - Iteration: 5. Worker 2 confirmed the revision (criteria-first `w2-revision-verify-criteria.txt`, digest d6ef7139): 490/490 green; 198/0/100% sets-only; neuter-guard control fails raw, restored identical; test diff exactly the 38-line addition; ruff clean. Phase-2 reconciliation: no contradictions (counts/coverage/identical/lint all match). Final verdict verified.
    - Iteration: 6. Fresh Worker 1 dispatched 2026-09-22 17:03 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/sets-mixins-stale-r1; target 48b8ca20 + tests/test_sets_mixins.py 9fca9442 re-confirmed == c9e39d31 blobs (CORRECTION: this line first read "ae162e6e/6c42079f == HEAD" from a stale memory — wrong on both counts; W1's start-state check and Worker-0's `git rev-parse c9e39d31:<path>` agree on 48b8ca20/9fca9442, and c9e39d31 is a stash-created WIP commit so HEAD comparison is meaningless; both stable since Sep-21; parts of the original verdict's oracles now live in tests/filters/test_base.py 07392d2a and tests/orders/test_base.py dac87bf7 via the sibling re-passes). Narrow scope per the Stale note: (a) :549 hostile-cls + generator-fields raw-`name-boom` escape (two prior confirmations: filters-sets W2 A20 + orders/inputs W1 probes — re-derive a THIRD time on current bytes before any edit, with contract rows; memory of prior confirmations is not standing); (b) `resolve_lazy_class` bool-hostile `if bound_class:` twin (orders/base lead (b)); (c) the UNPROBED `__qualname__` family mention from the input_values verification (confirm-or-disprove). Prior verdict stands for all else; attribution-first.
    - Iteration: 7. Worker 1 stale re-pass reported Fixed Low (one bug class, all three leads CONFIRMED with own contract rows + probes before editing: (a) :549 refusing/unformattable `__qualname__` replacing the gate's typed `Meta.fields` rejection — third independent A20 derivation, x4 frame-pinned through real creation/expansion both filter+order chains; (b) `if bound_class:` refusing-`__bool__` replacing the promised ImportError propagation — x3 e2e + BaseException breadth + KI abort; (c) AST census proves :549 the sole `__qualname__` read, so (c) IS (a); fix is the hoisted `_safe_class_name(qualified=True)` label + guarded `bool(bound_class)` (`except BaseException → False`) + import + docstring, 4 hunks) + 9 permanent tests (4 gate-label + 4 bool-owner + 1 honest-matrix pin, tier `tests/`). Files changed: sets_mixins.py (a4b301c3) + tests/test_sets_mixins.py (b73e245e). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the 4-hunk fix + test delta; pins match both eras; the 2 test `-` lines are exactly the replaced import lines; all 7 probe sha256 pins match; WS fix bytes cmp-identical to shared; siblings 07392d2a/dac87bf7 untouched; no nested hunt-ws; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0; pragma 1 == 1 pre-existing; failability claimed 8-red + pin-green for W2 to re-prove). TRIVIAL SLIP flagged for W2: "265 pure additions" is 263 `+` lines incl. the 2 import replacements (261 purely new). B1 BOUNDARY rides for W2 standing judgment: hostile-`__module__` raw at the attempt-2 assembly, pinned green pre AND post (fix leaves the seam byte-identical), routed by W1 as a narrow same-file lead WITH standing (same row family, feasible shape, reaching `.filterset`/`.orderset` read) — if W2 confirms standing it returns to W1 as a same-item revision (same file, same row family, re-pass still open). The UNPROBED `__name__` reads (`type_name_for` + `_validate_target` NotImplementedError) ride for W2 opinion (confirm correctly-out-of-family or flag). Report /tmp/w1-sets-mixins-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/sets-mixins-stale-verify, expectation-first.
    - Iteration: 8. Worker 2 verified (expectation-first `hunt-ws/w2-sets-mixins-stale-expectation.txt` 54ebd585, E1-E11 full agreement, zero contradiction): fresh-WS replay 22/22 both cells (7/7 probe pins match); WS-only revert → exactly the 8 hostile permanent tests red-raw + pin green + battery 9F/12P with the census delta RECONCILED (final bytes assert post-fix zero-reads; reverted output re-derives the (c)-IS-(a) proof) + KI standalone abort, restored cmp-identical, 67/67 both cells; honest five-way capture sha-identical (d3e1afa2); 27/27 own attacks both cells (gate extremes incl. double-hostile two-level degrade; bool extremes incl. fail-closed B3 + no-poison B10; `except BaseException → False` CORRECT by own evidence); fix shape minimal-in-contract M1-M5 (M3 `False` the only fail-closed default by consequence; no-dodge proof at the bool seam); oracle superset GENUINELY anchors (1075/1075 both cells, per-file exact, O1 file-level proof + O2 surface-not-padding + O3 arithmetic; full-suite 7148 + SAME 9 reds pre AND post with revert control — nothing outside observes the diff); B1 judged NO STANDING (blocking): legs 2+3 confirmed STRONGER than W1's claim (real-path probes both families) but leg 1 fails four independent ways (R-B text covers truthiness-un-testable owners only; attempt-2 ImportError-ness is import_string's honest contract; remedy undetermined — C1-lesson contradiction vs invented import semantics; GOAL trust-boundary + `_bind_related_declaration` precedent decline) — robustness row / new-card candidate with suggested text, NO same-item revision; unprobed `__name__` reads correctly-out-of-family on own probes (N1 loud-at-output, N2 GIGO, N3/N4 fail-closed holds); floor executed throughout; sharded/PG/async inapplicable own-traced; owner/tier/Low concurred. Report /tmp/w2-sets-mixins-stale-report.txt.
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/sets_mixins.py (hoisted `cls_label` + guarded `bool(bound_class)` + import + docstring, 4 hunks) + tests/test_sets_mixins.py (9 hostile tests).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-sets-mixins-stale-expectation.txt. Evidence: hunt-ws/sets-mixins-stale-verify/ records (w2_replay/ + w2_attacks/), post-fix digests a4b301c3/b73e245e.
    - Cleanup (stale re-pass): Removed hunt-ws/sets-mixins-stale-r1, hunt-ws/sets-mixins-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Durable evidence (compact): expectation C1-C10 (bind/naming/collect/expansion/cache/re-readability/resolution/permissions/lifecycle/neutral-home); replay = liar matrices at all 9 sites (typed post, raw pre) + ImportError passthrough; controls = WS-only revert 21/21 raw + neuter-guard raw + honest-identical restores; attacks = dunder-breadth/decl-spoof/cache-decline/bind-interleavings (26); coverage = 198/0/100% focused sets-only + 490 selection green. Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: Fixed Low. Files changed: django_strawberry_framework/sets_mixins.py (4 guarded seams + bind helper) + filters/base.py + orders/base.py (family gate guards) + tests/test_sets_mixins.py + tests/filters/test_base.py + tests/orders/test_base.py (10 hostile tests).
    - Verification: Passed (iterations 2+5, two-phase). Expected-before-diagnosis: hunt-ws/w2-sets-mixins-expectation.txt + criteria note. Evidence: hunt-ws/sets-mixins-verify/ + hunt-ws/sets-mixins-revision-verify/ records, post-fix digests 48b8ca20/91c41b1f/77b8aa77.
    - Cleanup: Removed hunt-ws/sets-mixins, hunt-ws/sets-mixins-verify, hunt-ws/sets-mixins-revision-verify; expectation + key logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - ITEM_BASELINE: `1fb7cc1563d598a2d0b04aa946590852e5afad72`.
    - Iteration: 1. Worker 1 reported Fixed Low (liar escapes at 9 sites across sets_mixins.py + filters/base.py + orders/base.py; hook-level guards + `_bind_related_declaration` helper) + 9 hostile tests (tier `tests/`). Worker-0 mechanical checks pass (pre-fix digests == HEAD blobs; post-fix 48b8ca20/91c41b1f/77b8aa77 == worktree; attribution clean — 6 files, all hunks hunt's; prose scan 0 hits). Filters/base.py + orders/base.py marked stale (bounded re-verification queued).
    - Iteration: 2. Worker 2 phase-1 verified the fix (expectation-first `hunt-ws/w2-sets-mixins-expectation.txt`, digest a6d5bbb0): liar replay typed post-fix + raw pre-fix (21/21), restored byte-identical; 26 attacks green; ImportError passthrough holds; owner/hook-level/tier/Low concurred. Residual lead routed out (end-to-end `Meta.fields` raising-liar at filters/sets.py get_fields + utils/inputs.py canonicalize + upstream django_filters — pre-existing, out of 6-file diff).
    - Iteration: 3. Worker 2 phase-2 reconciliation: revision-needed on ONE item-scoped gap — new diamond-`except` guard lines (`sets_mixins.py` 375-376) uncovered by the entire related surface (198 stmts, 2 missed, 99%; honest values never raise under `isinstance`, so only a hostile test reaches it). Required: cover with a hostile test (liar as `selected` from a base's `base_declarations_attr` map while inherited `collection_attr` holds honest decl — assert drop, no raw escape). Pragma route NOT sanctioned here (branch is runner-reachable). All else stands verified. Same item back to Worker 1 with workspace intact.
    - Iteration: 9. Fresh Worker 1 dispatched 2026-09-23 UTC, ITEM_BASELINE 33b70ed1, workspace hunt-ws/5e-layout-prose (bounded layout revision: [5e] row 3, sets_mixins.py :466 misaligned docstring line; docstring-only — tests b73e245e untouched). W2 verification follows in-unit.
    - Iteration: 10. Worker 1 layout revision landed (whitespace-only 1 line 8->7 spaces in `should_cache_expansion` docstring; production a4b301c3 -> c37c7b87, tests b73e245e untouched). Worker-0 mechanical checks pass (item diff vs 33b70ed1 exactly the two hunks; -w diff empty; focused test green — re-run by Worker-0; ruff check + format clean — re-run by Worker-0; no new pragma). Fresh Worker 2 verification dispatched (ITEM_BASELINE 96833df4, workspace hunt-ws/5e-layout-prose-verify; joint over both files).
    - Iteration: 11. Worker 2 VERIFIED the joint layout revision (expectation-first, K1-K6 all PASS — see routers Iteration 5 for the joint evidence; sets_mixins half: 1 line 8->7, siblings 462-464 at 7, co_code 40/40, failability to a4b301c3). Shared tree never edited by W2. Report: hunt-ws/reports/w2-5e-layout-prose-report.txt. Workspaces removed; expectation file retained in hunt-ws/ until closeout. [5e] row 3 CLOSED (mixins half); item stays verified.
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Use django_strawberry_framework/sets_mixins.py as the entry point. Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/testing/_wrap.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows C1-C8; 37 probes + 34 oracles green; decline/callable controls biting exactly, restored sha-identical; 7 candidates disproved as documented/caller-responsibility/correct-loud; no shared-tree edits). Worker-0 mechanical checks pass (digest 0df97813 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-testing-wrap-expectation.txt`, digest e64b0c42, no diagnosis supplied): probes 37 + oracles 34 + 16 independent attacks green (dispatch both directions, guard ordering, teardown composition, dunder/missing loud, hostile raw-escape per C7, drift install, arbitrary names). Phase-2 reconciliation: all points agreed (coverage 1:1, counts match, controls discriminate same gates without re-run need, 7 disproved correctly non-defects, C7 raw-escape contract-correct). Final verdict verified. Unverified cells: PG/sharded/async (pure helper, inapplicable by construction).
    - Durable evidence (compact): expectation C1-C8 (wrap/decline, fail-at-source, missing-method, drift, arbitrary names, composition, trust boundary, fidelity); replay = hunt probes (37) + wrap/django-patches oracles (34); controls = decline-neuter + callable-neuter (bite exactly, restore identical) + TypeError/AttributeError discrimination; attacks = dispatch/composition/dunder/hostile/drift (16). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 16 attacks + reconciliation. Target digest 0df97813.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-testing-wrap-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/testing-wrap-verify/ records.
    - Cleanup: Removed hunt-ws/testing-wrap, hunt-ws/testing-wrap-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/_wrap.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/testing/client.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (10 contract rows C1-C10; 27-battery + 93 oracles green; raise-neuter control biting exactly, restored byte-identical; 6 candidates disproved as faithful/robustness/documented; no shared-tree edits). Worker-0 mechanical checks pass (digest 91d61442 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-testing-client-expectation.txt`, digest 187e7c90, no diagnosis supplied): probes 27 + oracles 66 + 19 independent attacks green (agreement wrapper-vs-raw incl. second-op dispatch, gate both directions + mixin opt-in, multipart guards, login exactly-once both colors, endpoint ladder, CSRF agreement, gate-disabled exactness). Engine-base trace confirms package deltas are the owned contract. 2 own probe bugs corrected. Phase-2 reconciliation: all points agreed (counts 93 = 27+55+11 match; neuter control corroborates single raise site; 6 disproved correctly non-defects; multipart content-direct read is the documented asymmetry, not a C7 violation). Final verdict verified. Unverified cells: PG, sharded (no SQL branch except login/session on default DB).
    - Durable evidence (compact): expectation C1-C10 (gate, endpoint ladder, operationName, multipart guards, decode triple, content-type/url, transport ValueError, login colors, mixin, exports); replay = hunt battery (27) + package/live oracles (66); controls = raise-neuter (2 rows red, restore identical) + wrong-expectation fail + gate-direction variants; attacks = agreement/equality/guard/login/ladder/CSRF/exactness (19). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 19 attacks + reconciliation. Target digest 91d61442.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-testing-client-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/testing-client-verify/ records.
    - Cleanup: Removed hunt-ws/testing-client, hunt-ws/testing-client-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/client.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/testing/relay.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (6 contract rows R1-R6; 17-battery + 12 oracles + 2 live green; node_id-suffix control 14 failed/3 passed, restored cmp-identical; 5 candidates disproved as robustness/documented/caller-owned; no shared-tree edits). Worker-0 mechanical checks pass (digest df0dc72a == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-testing-relay-expectation.txt`, digest c2e93470, no diagnosis supplied): probes 17 + oracles 12 + live 2 + 8 independent attacks green (type/type+model live refetch, secondary asymmetry identical helper-vs-live, typed rejections incl. instance-instead-of-class, malformed→GLOBALID_INVALID, exotic round-trips, hostile-__str__ escape + uncorrupted later mints, clear()-is-terminal lifecycle). 3 own probe bugs corrected. Phase-2 reconciliation: full agreement on R1-R6, counts (17/12/2 identical node sets), control validity, and all C1-C5 dispositions (C1 robustness row coincide; C2 loud-null closed). Final verdict verified. Unverified cells: PG/sharded (no DB branch, inapplicable by construction).
    - Durable evidence (compact): expectation R1-R6 (mint==wire, strategy branches, typed rejections, secondary asymmetry, malformed mapping, README binding); replay = agreement battery (17) + oracles (12) + live round-trip/secondary (2); controls = node_id-suffix mutation (14 red, restore identical) + exact-message rejection asserts + wire-equality reach asserts; attacks = strategy refetch, asymmetry identity, rejection matrix, exotic round-trips, hostile-str boundary, lifecycle terminality (8). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 8 attacks + reconciliation. Target digest df0dc72a.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-testing-relay-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/testing-relay-verify/ records.
    - Cleanup: Removed hunt-ws/testing-relay, hunt-ws/testing-relay-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/relay.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/types/base.py
    - Status: verified
    - Stale resolved 2026-09-23 (bounded W2 VERIFIED with one NON-BLOCKING challenge C1): move proven a pure 11-line region relocation (sorted-span sha256 identical; counterfactual ea1d6083; cmp-identical restore); pin matrix 15/15 both orders with delta exactly D1-D6; item battery 233/233 both orders; pinning test green both orders (move never affected it); mixed trailing nodes exactly 2 green (DRY census+gates untouched); floor 10/10 read-only (bed untouched); gates clean; no other item file moved. C1: the known-red guard test flipped red->GREEN via D3 (its probe is meta-less + hostile-__name__; counterfactual reproduces the settled base.py:699 signature to the line number) — judged a non-blocking robustness row (hostile-only, no contract row pins meta-less hostile-name rejection, the green satisfies the test's own written expectation — class creation outside the `with` block now reaches the hardened list_field guard — no coherent revision exists). Guard-comment universal-vs-Meta-only narrowing rides as a judged prose lead for Rio. Naming-posture items never touched, never re-opened (7 candidates observed green read-only). Expectation-first hunt-ws/w2-types-base-reorder-expectation.txt (pinned 0a5b857b); report hunt-ws/reports/w2-types-base-reorder-report.txt. Workspace removed at close.
    - Stale 2026-09-23 (mid-task concurrent drift, NOT hunt work): the `_is_default_get_queryset` sentinel stamping moved above the `__name__` guard in `__init_subclass__` (+11/-11 region move, mtime 15:09, external hand — unattributable from tree evidence, no record drift; never reverted per the concurrent-work rule). Pinning test `test_has_custom_get_queryset_inherits_through_abstract_base_without_meta` is committed history (b5c12f41). Prior verified verdict stands for the old bytes only. Bounded Worker 2 re-verification on the diff queued in the post-dive-4 stale queue (after the filters/sets re-verify). Naming-posture items untouched (this file is not one of the two blocked files; no naming verdict re-opened).
    - Iteration: 2. Fresh bounded Worker 2 dispatched 2026-09-23, ITEM_BASELINE f6ac7b0a006ba4a82d400a81da8af99891f70669, workspace hunt-ws/types-base-reorder-verify; expectation-first hunt-ws/w2-types-base-reorder-expectation.txt (LANDED: current-bytes map + move reconstruction by elimination + G1-G7 + D1-D6 delta prediction + P1-P7 + cells; contamination PASS with sole fence-declaration hit, sealed 16:24:36, hash-pinned 0a5b857b); phase-2 drop written (hunt-ws/types-base-reorder-phase2/DIAGNOSIS.txt) with 7 bounded ride-alongs (item battery, mixed trailing nodes, known-red observation, targeted re-probes, move-equivalence + counterfactual, floor subset, gates + diff-exactness).
    - Stale 2026-09-22 (review-driven, digests match at 40af4d12 — NOT digest-driven): maintainer review 5c — 4 hunt-added `except BaseException` arms reached by NO test (~:386, :686, :865, :1737) block the gate under `fail_under = 100`; bounded Worker 1 re-pass queued (order 6d) under the standing deletion ruling (unreached + infeasible = DELETE, never a new hostile shape, never `pragma: no cover`) + docstring spaces (~:664, :675) + false `bool`-subclass comment (~:1589); behavior change at ~:713 (`__name__` non-exact-`str` rejection) recorded on the item. Prior verified verdict stands for the guard behavior; the re-pass changes only the 4 arms + prose.
    - Scope 2026-09-22 (from list-field verification, W2-judged HAS STANDING): `_detect_custom_get_queryset:982` (`for base in cls.__mro__`) detonates raw outside its `except BaseException` gate at class creation (row: the helper's own fail-closed docstring posture; shape: raising-`__mro__` metaclass; input: consumer class declaration) — rides this re-pass as confirm-or-disprove, Low at most. The sibling A7 flag (registry.py hostile-hash) was judged NO STANDING by the same W2 and is closed.
    - Migration 2026-09-21: the worktree move excluded the foreign spec-015 hunks this verdict was recorded with (recorded digest 07aaa2f2 = HEAD 91c58747 + foreign + hunt guards; current 1fe9e5ad; all hunt-guard hunks byte-identical). Prior verified verdict stands for the old digest only; re-verification queued at the new digest before the gate.
    - Iteration: 3. Re-opened 2026-09-20: types/definition.py verification confirms a same-class residual at this target — liar `Meta.name` escapes raw `TypeError` via unguarded `str.__str__(raw_name)` in `_validate_meta` (escape happens at class creation, before any definition object exists — definition.py structurally cannot own it). Prior verified verdict stands for all else; narrow bounded re-pass queued (single seam + full-file same-class audit).
    - Iteration: 4. Worker 1 stale re-pass: Fixed (named slice + 19 same-class residuals at the collection seam: entry gate, model guard, primary real-type check, interfaces raw/entry/issubclass/tuple + 3 label swaps, type-name gate, namespace enumeration, sidecar/connection/cursor/shapes/globalid/normalizer gates, `_format_name_list` helper + 8 join sites, `_detect` guard; verdicts typed-reject at gates, degrade at display labels; T18/T19 + middle-base-`__dict__`/Mapping/description/direct-helper/model-`__name__` reads characterized out-of-contract) + 20 funcs / 43 nodes in tests/types/test_base.py (tier `tests/`). Failability: stale probes red pre-fix (20 + 10 + 20-red rows) / 40 green post-fix (3 characterized reds by design); honest 7 byte-proofs + 4 pins; shared focused 231 + dir green; ruff + trailing-commas clean. Foreign hunks verified present post-format. Bounded lead for the keyset item: cursor evil-str downstream. Worker-0 mechanical checks pass (post-fix digests ecaba4e4/a5b66826 == worktree; attribution clean — foreign + iteration-1 + stale hunks in separate regions, no interleave; prose scan 0 hits).
    - Iteration: 5. Worker 2 phase-1 (expectation-first `-r2`, digest ea0a41f8): revision-needed on ONE concrete gap — `_interfaces_shape_error(meta, type(raw).__name__)` (~1402/1407) interpolates a bare label, so a hostile/raising-named raw `Meta.interfaces` value detonates raw (2 probes red post-fix); suggested fix `_safe_class_name(type(raw))` at both call sites + 2 liar nodes. Everything else verified (89 own probes + 231 module + 607 types-dir green; revert control 42/47 + 39/192 raw; honest-identity doubly proven; per-site defect rulings G1-G15 concurred with Low; robustness R1-R5 explicitly agreed). Forwarded lead (new card, non-blocking): non-string hostile annotation key escapes raw at the string-keys gate (outside stale diff). Count note: 24 funcs/39 nodes observed vs 20/43 claimed — superset either way, non-blocking. Same item back to Worker 1 with workspace intact.
    - Iteration: 1. Worker 1 reported Fixed Low (forwarded liar trio confirmed: 4 guarded `isinstance` + `_is_optimizer_hint_value` helper + liar-safe label; honest-identity pin byte-identical) + 8 tests in tests/types/test_base.py (tier `tests/`). Same-class liar shapes at adjacent gates (N1/N2/N3/N5/N4) assessed robustness rows, not fixed. Foreign spec-015 hunks kept byte-intact. Worker-0 mechanical checks pass (pre-fix worktree 4bd9ad16 = HEAD blob + foreign; post-fix bc8dcdb6 == worktree; attribution clean — foreign intact, hunt separate; prose scan 0 hits).
    - Iteration: 2. Worker 2 verified under two-phase dispatch (expectation-first `hunt-ws/w2-types-base-expectation.txt`, digest e729a748, no diagnosis supplied): liar reproducer 10/10 typed post-fix; hunt-hunks-only revert → 7/7 raw; restored byte-identical; honest identical. Attacks green (raising-__eq__ keys, unhashable EvilMapping, hostile metaclass direct+creation, KI/SI breadth correct, re-declaration/edges/primary-bool). Permanent 8: 7 failed + 1 honest-pin passed pre-fix. C4/C5/C6 spots green (incl. foreign-helper composition). Connected modules 230 green. Ruff + trailing-commas clean. Phase-2 reconciliation: full agreement (C1-C7, counts consistent as strict superset, honest-identity, foreign intact); N1-N5 robustness routing explicitly agreed (fail trust-boundary test: self-sabotaging consumer code, wire-unreachable, no promised row — card fodder, never release blocker). Final verdict verified. Unverified cells: sharded/PG (pure guards, inapplicable by construction).
    - Durable evidence (compact): expectation C1-C7 (mapping/keys/values typed, registration/primary, pk suppression, unregistered loud, primary-bool); replay = liar matrices direct+creation (typed post, raw pre) + honest-identity diff; controls = hunt-hunks-only revert (raw) + honest-pin green both eras + EvilMapping typed; attacks = dunder-breadth/metaclass/re-declaration/edges (10+); C4/C5/C6 spots incl. foreign composition. Full probe files + logs in hunt-ws until closeout cleanup.
    - Iteration: 6. Worker 1 revision: `_safe_class_name(type(raw))` at both shape-error call sites (honest `type(42)` → `"int"` verified) + 2 liar nodes (evil + raising raw instance → typed); failability 2 raw pre-fix / 233 green post-fix; W2 challenge probes copied verbatim green; ruff clean; foreign hunks present post-format. Post-fix digests 07aaa2f2/cbbe20f3.
    - Iteration: 7. Worker 2 confirmed the revision (criteria-first `w2-revision-verify-criteria.txt`, digest 449283f2): liar-2 green; full 233 green; single-site neuter → 2 raw, restored identical; honest-identity spot green; diffs exact (4+/2- prod, 27+ test); ruff clean. Phase-2 reconciliation: full agreement (2-site fix; both nodes hit site 1 with site 2 covered statically + via existing hostile-iteration test — sufficient, not a blocker; counts/identical/foreign/lint match). Final verdict verified. Unverified cells: sharded/PG (no DB decision), live HTTP, full suite.
    - Result: Fixed Low (iterations 1–2) + stale residuals fixed (iterations 4–7). Files changed: django_strawberry_framework/types/base.py (optimizer_hints guards + collection-seam guards + label swaps + 2 shape-error labels) + tests/types/test_base.py (8 + 43 + 2 hostile nodes). New-card candidates: non-string hostile annotation key at string-keys gate; keyset cursor evil-str downstream.
    - Verification: Passed (iterations 2 + 5-partial + 7, two-phase throughout). Expected-before-diagnosis: hunt-ws/w2-types-base-expectation.txt + -r2 + criteria note. Evidence: hunt-ws/types-base-stale-verify/ + hunt-ws/types-base-revision-verify/ records, post-fix digest 07aaa2f2 (worktree = HEAD blob 91c58747 + foreign spec-015 hunks + hunt guards).
    - Cleanup: Removed hunt-ws/types-base-stale, hunt-ws/types-base-stale-verify, hunt-ws/types-base-revision-verify; armcut re-pass removed hunt-ws/types-base-armcut-r1, hunt-ws/types-base-armcut-verify, hunt-ws/armcut-verify-phase2; armcut expectation + 3 reports retained in hunt-ws/ until closeout; unrelated work (incl. foreign spec-015 hunks) preserved.
    - Cleanup (resume 2026-09-21): also removed docs/bug_hunt/temp-tests/types-base-raw-label/ (W2-challenge focused-run scope the iteration-7 cleanup missed; item verified, scratch ignored+untracked).
    - Iteration: 8. Fresh Worker 1 dispatched 2026-09-22 16:37 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/types-base-stale-r1; worktree 1fe9e5ad vs HEAD 91c58747 (all hunt-guard hunks byte-identical per the Migration line; foreign spec-015 excluded at migration), tests d740084a vs HEAD 4282e0b0. Scope: re-verification at the new digest + the A5 confirm-or-disprove per the Scope note. Oracle note: the known-RED maintainer-decision test lives in THIS item's `__init_subclass__` guard — reproduce-but-don't-chase, not this re-pass's to resolve (see the standing decision at the end of the record); the A5 flag is a different seam in the same file and IS in scope.
    - Iteration: 9. Worker 1 stale re-pass reported Fixed Low (A5 CONFIRMED with probe before editing: raising-`__mro__` metaclass detonated raw out of `_detect_custom_get_queryset:982` at class creation, violating the helper's documented `False` posture; fix is the minimal in-contract guarded `cls.__mro__` read + docstring clause — read-through-`type` and whole-loop guard explicitly rejected with reasons; all prior load-bearing rows re-verified green) + 2 permanent tests (direct + creation, tier `tests/`). Files changed: types/base.py (40af4d12) + tests/types/test_base.py (30dc72f5). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the +7/-1 fix + 2 tests; digests match; collection 7 = 5 battery + anchor + finalize-obs mapped per-file exact — the report's "6" is battery + anchor; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0; no new pragma; known-RED reproduced + untouched; failability claimed 2-fail on revert for W2). CAVEAT: probe bytes differ from the reported sha256 pins (claimed 6fefaeb9/e9f8b68e, on-disk 3b2b241f/e37b13f9 — content polish post-pin, counts reconcile) — flagged for W2, which replays current bytes. O1 (finalizer/relay raw `__mro__` reads) forwarded to the running finalizer re-pass as an FYI lead; O2 (lying non-raising `__mro__`) rides for W2 opinion. Report /tmp/w1-types-base-stale-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/types-base-stale-verify, expectation-first.
    - Iteration: 10. Worker 2 verified (expectation-first `hunt-ws/w2-types-base-stale-expectation.txt` 4440e4cc, E1-E18 full agreement, zero contradiction): fresh-WS replay 6 + escape-DID-NOT-RAISE post-fix, polarity inverts exactly on WS-only revert to 1fe9e5ad (escape PASSES raw via :982, both permanent tests FAIL raw), restored cmp-identical; 28/28 own attacks (KI/SI breadth contained, garbage-`__mro__`/injected-entry raw-helper-framed as characterized, GIGO symmetry); fix shape judged minimal-in-contract BY CONSEQUENCE (D1 read-through-`type` contradicts the routed row, D2 whole-loop flips the pinned E10 characterization, D3 middle option undemanded without a citable row); safety case closed empirically (contained-`False` can never mislead — every finalize path detonates first, `is_finalized()` stays `False`); honest 20-line capture byte-identical across a second revert cycle; oracles 235 + 604 (+2 new, arithmetic exact) + 113 + known-RED; floor EXECUTED (269 + 1 by-design flip); known-RED the ONLY red, via :708, untouched (fence :970-993 + tests); O1 HAS STANDING as correctly-forwarded lead (already with the running finalizer re-pass — its current rawness is load-bearing for this safety case); O2 robustness row (new card at most); owner/tier/Low concurred; cells: floor executed, sharded/PG inapplicable grep-proven. Minor errata: probe-pin polish caveat confirmed-benign (current bytes replayed as truth); production is +8/-2 not +7/-1; dir oracle 604 not 602.
    - Iteration: 11. Worker 1 bounded armcut re-pass reported (4 unreached arms deleted + 2 prose spots fixed, tests byte-identical): (a) `_validate_relation_shapes` items-handler unwrapped (deleted message byte-identical to surviving gate); (b) `_is_auto_annotation` second-try unwrapped + consequential docstring sentence narrowed + (e) both stray spaces removed; (c) Relay-id assignment check unwrapped (typed rejection untouched); (d) per-key str-gate handler unwrapped (rejection structure intact) + consequential docstring reword; (f) bool comment corrected to finality truth. Coverage proof: full-suite WS pre-delete missing exactly the 4 arm pairs (614 stmts, 8 missed), post-delete 602/602 0 missing; oracle-file pre/post consistent (other-suite lines renumbered, no new gaps); differential battery 31 rows DIFF-IDENTICAL pre/post (sha256 94fc685d); RED-test identical failure modulo :708→:699 frame shift; floor oracle 233 swapped-in green + restored hash-verified; full-suite classifications (RED + 11 env + own-scratch governance transient). Deliverables base ea1d6083 + tests 1cd6cce3 unchanged. Worker-0 mechanical checks PASS (digests match; fence-vs-ITEM 547c2790 exactly base 14+/28- in 7 hunks, tests 0 lines; all hunks read and matched incl. :713-guard region clean; oracle 233 green independent; RED identical message at :699; sweep 0; no pragma; ruff + commas re-run clean; venv intact; no strays; coverage re-proof rides to W2). Fresh Worker 2 two-phase dispatched (fenced phase 1 from arm locations + current diff + oracles; expectation hunt-ws/w2-types-base-armcut-expectation.txt; workspace hunt-ws/types-base-armcut-verify; drop gated on contamination check).
    - Iteration: 12. Worker 2 verified the armcut (expectation-first `hunt-ws/w2-types-base-armcut-expectation.txt`, W0-sealed f20bd7e6 pre-run, re-hashed unmodified at close; fenced phase 1, drop-gated phase 2): full-suite coverage pre (614 stmts, 8 missed exactly the 4 handler pairs) + post (602/602, 0 missing) with annotate-level proof (11 physical lines unexecuted) + positive control (attacks flip all 4 pairs covered); honest differential 82/82 ROW-identical (+6 gapclose twins, +4 intended PROSE flips); hostile/out-of-contract attacks inside predicted envelopes, all judged hostile-only; RED identical failure modulo the explained -9 frame shift (R5: W1's arithmetic holds, W2's -6 self-corrected pre-drop); oracles 233 + 113/RED green-identical; covering set enumerated (64 static, 5 tiers dynamic, tests/types/ alone at 100%); floor cell VERIFIED (3.10.19 mirror); gates/fence exact. Phase-2 reconciliation: zero outcome deltas across all 9 ride-alongs; 6 non-blocking remarks (R-rep erratum: "31 rows" is 27 = 9+9+3+6 — CORRECTS Iteration 11's folded number, product-orthogonal; R-a/R-d/R-b/R-c complete the infeasibility arguments in union, same outcomes; R-floor cured by independent re-execution; R-parity robustness remark: connection sibling contains dict-spoofs while relation_shapes now lets a lying-dict escape raw — no contract row promises cross-boundary containment, recorded, never a blocker). Verdict: verified. New digest ea1d6083; ledger row appended (deletion, Class: robustness).
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/types/base.py (guarded `cls.__mro__` read + docstring clause in `_detect_custom_get_queryset`) + tests/types/test_base.py (`_RaisingMROMeta` helper + 2 tests).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-types-base-stale-expectation.txt. Evidence: hunt-ws/types-base-stale-verify/ records (w2-replay/ + w2-attacks/), post-fix digests 40af4d12/30dc72f5.
    - Cleanup (stale re-pass): Removed hunt-ws/types-base-stale-r1, hunt-ws/types-base-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__base.stripped.py and docs/shadow/current/django_strawberry_framework__types__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/types/converters.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (hostile `__class__` escapes at 5 declaration seams: Array dispatch + base_field fetch + nested check, HStore dispatch, enum entry precheck + grouped-check; guarded interrogations + doc bullets) + 6 liar/spoof/unreadable tests in tests/types/test_converters.py (tier `tests/` — hostile declaration shapes, wire-unreachable; honest behavior pinned live). Reasonable-application verdict holds (26 SCALAR_MAP rows, MRO, relation refusal, unmapped loud incl. CompositePrimaryKey-as-pk, SDL pins, live enum row). Worker-0 mechanical checks pass (pre-fix 9ceb34af == HEAD blob; post-fix 679c9448 == worktree; attribution clean — 6 hunks in claimed areas + tests; prose scan 0 hits).
    - Iteration: 2. Worker 2 verified under two-phase dispatch (expectation-first `hunt-ws/w2-types-converters-expectation.txt`, digest 1482808e, no diagnosis supplied): liar reproducer 6/6 typed post-fix; hunt-hunks-only revert → 6 raw escapes (full file 6 failed/72 passed); restored byte-identical → 78 passed. 12 attacks green (incl. KI-breadth chained acceptable, EvilMapping, honest edges). Owner single-file correct; tier + Low concurred; reasonable-application spot-checked (10 rows + SDL byte-identical). Ruff clean. Phase-2 reconciliation: full agreement (R1-R8, 5-seam/6-test mapping consistent, honest-identity doubly proven, counts match, disproved items corroborated, KI chaining observed, CompositePrimaryKey-as-pk non-material residual). Final verdict verified. Unverified cells: PG live (psycopg2 absent), sharded (no DB decision).
    - Iteration: 3. 2026-09-21 test-hardening correction: Worker 1 returned the both-sentinels-explicit HStore pin + separate ArrayField control (test-only diff, production byte-identical, lock identical; scope + lint + shared-stability checks pass). Worker 0 applied it and proved 2/2 green in pg-less AND ambient-pg cells plus a neuter control (raw RuntimeError red, restored identical). Evidence imported to hunt-ws/converters-pin-verify/. Fresh expectation-first Worker 2 dispatched; verdict stands pending W2.
    - Iteration: 4. Worker 2 verified the correction under two-phase dispatch (expectation-first `hunt-ws/w2-converters-pin-expectation.txt`, digest 8f6936f2, no diagnosis supplied): both pins replayed green in pg-less AND real-pg venvs; own neuter control failed the HStore pin raw (RuntimeError) while the Array control stayed green (bonus order confirmation); 5 independent attack probes green in both states; production byte-identical; uv.lock identical. Pin-hardening cycle complete — the verified verdict now rests on driver-determinate pins.
    - Durable evidence (compact): expectation E1-E10 (seam typing, honest identity, breadth consistency); replay = liar matrices (typed post, raw pre) + honest probe + SDL snapshot (byte-identical both eras); controls = hunt-hunks-only revert (6 raw) + honest-pin stability; attacks = dunder-breadth/unreadable/edges (12). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: Fixed Low. Files changed: django_strawberry_framework/types/converters.py (5 guarded interrogations + doc bullets) + tests/types/test_converters.py (6 liar/spoof/unreadable tests).
    - Verification: Passed (two-phase). Expected-before-diagnosis: hunt-ws/w2-types-converters-expectation.txt. Evidence: hunt-ws/types-converters-verify/ records, post-fix digest 679c9448.
    - Cleanup: Removed hunt-ws/types-converters, hunt-ws/types-converters-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__converters.stripped.py and docs/shadow/current/django_strawberry_framework__types__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/types/definition.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (liar escapes at 4 seams: graphql_type_name, related_target_for, _normalize_pk_name, _resolves_id_off_pk id-attr; guarded interrogations + normalization, honest bytes unchanged) + 4 liar tests in tests/types/test_definition_relations.py (tier `tests/` — hostile declaration shapes, wire-unreachable). Forwarded lead NOT fixed: `types/base.py::_validate_meta` `Meta.name` liar (`str.__str__(raw_name)` unguarded) escapes raw — same class, types/base.py owns it (bounded stale re-pass queued). Worker-0 mechanical checks pass (pre-fix fa6c4d33 == HEAD blob; post-fix 01f78d93 == worktree; attribution clean — 4 hunks in claimed seams + tests; prose scan 0 hits).
    - Iteration: 2. Worker 2 verified under two-phase dispatch (expectation-first `hunt-ws/w2-types-definition-expectation.txt`, digest c71ca082, no diagnosis supplied): replay 21/21 contained post-fix; hunt-hunks-only revert → 9 pass/12 fail raw; restored byte-identical. 33 attacks green (incl. KI/SI contained acceptable, no cache poisoning, lifecycle extremes). Owner single-file correct; tier + Low concurred; forwarded-lead routing independently proven OUT (escape before any definition object exists). Ruff clean. Phase-2 reconciliation: full agreement (R1-R8, seam shape as strict superset, honest-identity doubly proven, counts exact, KI stands). Final verdict verified. Unverified cells: sharded/PG (no DB path, inapplicable by construction).
    - Durable evidence (compact): expectation R1-R8 (name derivation, target mapping/memo, id-resolver predicates, lifecycle, registry agreement, error policy, isolation, trust boundary); replay = liar/raising matrices per seam (contained post, raw pre) + honest controls; controls = hunt-hunks-only revert (raw) + byte-identical restore + routing probe; attacks = dunder-breadth/cache-purity/lifecycle (33). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: Fixed Low. Files changed: django_strawberry_framework/types/definition.py (4 guarded seams) + tests/types/test_definition_relations.py (4 liar tests).
    - Verification: Passed (two-phase). Expected-before-diagnosis: hunt-ws/w2-types-definition-expectation.txt. Evidence: hunt-ws/types-definition-verify/ records, post-fix digest 01f78d93.
    - Cleanup: Removed hunt-ws/types-definition, hunt-ws/types-definition-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/definition.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__definition.stripped.py and docs/shadow/current/django_strawberry_framework__types__definition.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/types/finalizer.py
    - Status: verified
    - Migration 2026-09-21: the worktree move excluded the foreign +7 globalid-snapshot docstring hunk this verdict was recorded with (recorded digest 8b6708fb, current 35ff5286; the fix hunk byte-identical). Prior verified verdict stands for the old digest only; re-verification queued at the new digest before the gate.
    - Iteration: 1. Worker 1 reported Fixed Low (raw escape in `_field_surface_names`: `__class__`-liar → raw RuntimeError, spoof → raw AttributeError at :269/:272; guarded classify+label interrogation, honest paths unchanged) + 2 hostile-attribute tests in tests/types/test_finalizer.py (tier `tests/`). Robustness rows (not fixed): R-a misreading corrected (direct cross-model reuse raises loud); R-b inheritance/no-entries silent bind benign in every reachable shape; R-c pending preserved converging on retry; R-d snapshot-before-audits clean. Foreign +7 docstring hunk kept byte-intact. Worker-0 mechanical checks pass (pre-fix worktree f4266a15 = ITEM_BASELINE incl. foreign; post-fix 8b6708fb / tests d9bc52a6 == worktree; attribution clean — fix + foreign + tests, no interleave; prose scan 0 hits; shared focused 19 passed).
    - Iteration: 2. Worker 2 verified under two-phase dispatch (expectation-first `hunt-ws/w2-types-finalizer-expectation.txt`, digest 4499d08e, no diagnosis supplied): liar/spoof replay 2/2 typed post-fix; hunt-hunk-only revert → 2/2 raw + module 2 failed/17 passed; restored byte-identical (honest log identical). 7 attacks green (incl. KI/SI breadth acceptable, fail→fix→retry with no ghosts, A7 both-orders typed). Owner single-file correct; tier + Low concurred. Ruff + trailing-commas clean. Phase-2 reconciliation: full agreement (C1-C10 split coverage stated — seam defect surface mine, regression surface via 17 identical pre/post + verified siblings + W1 battery/neuter control; defect lines match :269/:272; 19s agree; R-a confirmed by A7; R-b precisely resolved — silent shape narrower than A7, no C5 row broken since all owner-dependent behavior resolves to the three checked axes, fixing rejects working builds; R-c/R-d agreed; KI stands; Low agreed). Final verdict verified. Unverified cells: sharded/PG (no DB branch), live GraphQL N/A.
    - Durable evidence (compact): expectation (both hostile shapes typed with attribution, honest identical); replay = liar/spoof matrices (typed post, raw pre) + honest surface/byte-diff; controls = hunt-hunk-only revert (raw) + unresolved-gate neuter (DID NOT RAISE) + identical restores; attacks = dunder-breadth/both-callers/retry-drain/orders-stability (7). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: Fixed Low. Files changed: django_strawberry_framework/types/finalizer.py (guarded `_field_surface_names` interrogation) + tests/types/test_finalizer.py (2 hostile-attribute tests).
    - Verification: Passed (two-phase). Expected-before-diagnosis: hunt-ws/w2-types-finalizer-expectation.txt. Evidence: hunt-ws/types-finalizer-verify/ records, post-fix digest 8b6708fb (worktree = HEAD blob 77fd9a2d + foreign docstring hunk + hunt guard).
    - Cleanup: Removed hunt-ws/types-finalizer, hunt-ws/types-finalizer-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work (incl. foreign hunk) preserved.
    - Iteration: 3. Fresh Worker 1 dispatched 2026-09-22 16:51 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/types-finalizer-stale-r1; worktree 35ff5286 vs HEAD 77fd9a2d is exactly the ledgered `_field_surface_names` guard hunk (stable since before 08:45; the ledger's foreign-docstring note no longer materializes in the diff), tests 534f40d1 vs HEAD 462275e5 (2 ledgered hostile tests). Scope per the Migration line (re-verification at the new digest: the guard intact without the foreign hunk + load-bearing rows; HEAD blob 77fd9a2d already includes aadca5a2, so no new main surface — an earlier draft of this line misstated the scope and is superseded).
    - Iteration: 4. Worker 1 stale re-pass reported Fixed Low (O1 CONFIRMED with own probes before editing: `_field_surface_names` read the inherited-surface inputs raw — `type_cls.__mro__` (:249) + each base's `__strawberry_definition__` (:250) escaped raw `RuntimeError`, breaking the C10/C10-MRO posture; fix is one guard around the inherited-surface unit (mro snapshot + walk → typed `ConfigurationError` via `_safe_*`, `from exc`, `except BaseException` per precedent); prior verdict re-proven intact without the foreign hunk incl. hunk-revert control failing exactly the 2 ledgered tests) + 2 permanent tests (tier `tests/`). Files changed: types/finalizer.py (f866fcf0) + tests/types/test_finalizer.py (6ec1a1ec). Worker-0 mechanical checks pass (item diff vs c9e39d31 exactly the +25/-13 guard hunk + 53-line pure test addition; pins match; probes present in stale-probes/; no nested hunt-ws; ruff + trailing-commas + banned-word scans clean — re-run by Worker-0; no new pragma; failability claimed 2-red-raw for W2 to re-prove). COUNT SLIP flagged for W2: "header + 25 scratch + 21 module = 45" miscounts (1+25+21=47) and floor says 26 scratch vs default 25 — reconcile per-file. Out-of-fence observations O1-b/O1-c (relay.py:154 `apply_interfaces` + :245 upstream MRO scan detonate FIRST for Node-shaped hostile-`__mro__`, raw pre and post — relay-owned, with a Decision-1 candidate row named) ride for W2 standing/routing judgment — no stale trigger now. Report persisted by Worker-0 to /tmp/w1-types-finalizer-stale-r1-report.txt (W1 printed but never wrote it; bytes extracted verbatim from its session log). Fresh Worker 2 dispatched, workspace hunt-ws/types-finalizer-stale-verify, expectation-first, with an explicit coupling criterion: the types/base A5 safety case ("hostile never finalizes") now rests on THIS fix's typed containment — W2 must re-prove flag-stays-`False` + no-partial-decoration + retry-converges for both O1 shapes (typed containment must still refuse finalization, never silent-`False` into the schema).
    - Iteration: 5. Worker 2 verified (expectation-first `hunt-ws/w2-types-finalizer-stale-expectation.txt` e8cff575, E1-E10 full agreement, zero contradiction): fresh-WS replay 47/47 post-fix; WS-only revert → exactly the 2 new tests red-raw + ledgered-guard control green + O1 scratch 3 red-raw with o1b/o1c STAYING green (relay-first detonation proven pre-fix), restored cmp-identical; honest identity re-derived (W1 instrument sha match + own wider capture across a second revert cycle); 18/18 own attacks incl. synthesis-caller O1 shape W1 never reached; fix shape one-guard-minimal BY CONSEQUENCE (micro-guards ruled out empirically — walk-interior booms; whole-function ruled out empirically — annotation misattribution; read-through-`type` ruled out by row contradiction); COUPLING HOLDS for both O1 shapes (flag False + undecorated + retry converges + `is_finalized()` False — the types/base A5 safety case may rest on this containment); counts reconciled (47 true; floor 26 = header-inclusive); O1-b/O1-c judged NO STANDING (row prong fails: Decision 1 promises TypeError-from-`__bases__`-assignment only, observed is RuntimeError from the pre-scans — robustness row / Routed lead to relay, relay untouched, Low-at-most); breadth ACCEPTED per E7 criteria; floor 65/65 executed; sharded/PG inapplicable own-traced; owner/tier/Low concurred. Report /tmp/w2-types-finalizer-stale-report.txt.
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/types/finalizer.py (inherited-surface guard in `_field_surface_names`) + tests/types/test_finalizer.py (2 O1 tests).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-types-finalizer-stale-expectation.txt. Evidence: hunt-ws/types-finalizer-stale-verify/ records (w2-replay/ + w2-attacks/), post-fix digests f866fcf0/6ec1a1ec.
    - Cleanup (stale re-pass): Removed hunt-ws/types-finalizer-stale-r1, hunt-ws/types-finalizer-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/finalizer.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/types/relations.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows R1-R8; 23 probes + 137 oracles green; unguarded-hash + dropped-list-wrap controls biting, restored byte-identical; C1-C3 disproved as trusted/safe-by-construction; no shared-tree edits). Worker-0 mechanical checks pass (digest 6bd7c63d == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-types-relations-expectation.txt`, digest edfbc300, no diagnosis supplied): probes 21 + oracles 137 + 13 independent attacks green (nullable-vs-required shapes, two-target naming + retry, self-FK/symmetric-M2M/no-related_name corrected, hash totality incl. BaseException, discard/clear/rebuild/double-finalize); inverted-assertion controls discriminate. Phase-2 reconciliation: full agreement on R1-R8, controls, C1-C3, KI breadth — with one evidence correction: W1's "23 passed" does NOT reproduce; 2 hunter nodes (reverse-without-related_name, self-referential/symmetric-M2M) fail at setup in every environment (`isolate_apps("relprobes")` label misuse → ModuleNotFoundError; deterministic, not environmental). W2's corrected equivalents pass, so the substance is closed — a scratch-instrument reporting defect, not a production defect, no revision implicated. Final verdict verified. Unverified cells: PG, sharded, async (no DB/async branch, pure annotation/registry logic).
    - Durable evidence (compact): expectation R1-R8 (loudness, order independence, shapes, vocabulary reuse, discard-by-id, sentinel rewrite, hash totality); replay = shapes (8) + hash/lifecycle (15, 2 with broken setup noted) + oracles (137); controls = unguarded-hash + dropped-wrap (bite red, restore identical) + inverted assertions; attacks = shapes/targets/self-hash/lifecycle (13). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 13 attacks + reconciliation (incl. instrument correction). Target digest 6bd7c63d.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-types-relations-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/types-relations-verify/ records.
    - Cleanup: Removed hunt-ws/types-relations, hunt-ws/types-relations-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relations.stripped.py and docs/shadow/current/django_strawberry_framework__types__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/types/relay.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows R1-R8 + trust boundary; 19-battery + 184/48 oracles green; S3 hint-disabled control discriminating; D1/D2 typed both eras; 4 leads disproved by reading; 2 robustness rows characterized, no fix; zero shared-tree edits; foreign hunk intact; tripwire assessed no-action). Worker-0 mechanical checks pass (worktree digest c333c785 = HEAD blob + foreign hunk only; no hunter edits; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-types-relay-expectation.txt`, digest 27f3cd72, no diagnosis supplied): battery 19 + oracles 184 + live full-file 250 + 13 independent attacks green (zero-query malformed battery, callable extremes, hostile-subclass normalization, consumer is_type_of/hostile-hint, NodeID chains, DoesNotExist/order/duplicates, finalize-twice; 3 own setup errors corrected). Phase-2 reconciliation: full agreement (R1-R8 every row dual-instrumented; counts consistent — 250 is the superset of W1's 48-subset; S3 discriminates; reading-leads closed empirically; robustness row 1 out-of-contract — trusted-caller + masked; row 2 fail-safe and leak-free — public-shape error only, dead branch falls to same ConfigurationError; tripwire agrees, no action). Final verdict verified. Unverified cells: PG, sharded (no SQL branch); async via sqlite async rows only.
    - Durable evidence (compact): expectation R1-R8 (encode, decode-uniform, collapse, stamp/honor, id resolution, dispatch, composite gate, typename install); replay = battery (19) + oracles (184) + live full file (250); controls = S3 hint-disabled misroute + zero-query instrument proof; attacks = malformed/callable/hostile-dunder/chain/dispatch/finalize (13). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 13 attacks + reconciliation. Target worktree digest c333c785 (HEAD blob 52439862 + foreign docstring hunk, untouched).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-types-relay-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/types-relay-verify/ records.
    - Cleanup: Removed hunt-ws/types-relay, hunt-ws/types-relay-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work (incl. foreign hunk) preserved.
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relay.stripped.py and docs/shadow/current/django_strawberry_framework__types__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/types/resolvers.py
    - Status: verified
    - Stale resolved 2026-09-23 (bounded W2 VERIFIED, no challenges): landed bytes == handoff (22f10c3f x3 observations; patch 69c965a1 + battery f8ebf5d4 pins match; call sites L57/613/618/670/694/767 exact); battery 4/4 green + docstring delta comment-only (stripped-AST identical); R1-R8 re-proved (8/8 settled rows + 11/11 interaction pins incl. armed many-side via bounded_rows, elision-under-deadline, deadline-before-strictness both directions, all 3 async closures); failability re-proved (3 fail without / 4 green with, cmp-identical restore); DRY interaction clean (pin green, docstring hunk comment-only); floor substrate 4/4 (battery unrunnable on the pre-fix bed — file absent — fix lines version-agnostic by inspection; bed untouched); diff inventory exact (fix + battery + index row; other test_query deltas grep-proven concurrent); gates clean. Expectation-first hunt-ws/w2-types-resolvers-deep3-expectation.txt (pinned 75500611); report hunt-ws/reports/w2-types-resolvers-deep3-report.txt. Workspace removed at close.
    - Stale 2026-09-23 (dive-3 Low fix LANDED by an external hand mid-dive-4): recorded 5f4cce2b (HEAD blob + DRY one-sync-boundary hunks, verified as foreign), worktree ddbe46a8; delta is EXACTLY the 6-line D-3A-1 handoff (check_deadline import + 5 single-resolver calls, sha256 22f10c3f byte-identical to hunt-ws/reports/d3a1-resolvers-fix.patch, mtime 15:45) + the 4-test battery landed complete as untracked examples/fakeshop/test_query/test_relation_deadline_api.py (mtime 15:44; ONE docstring line reworded vs handoff f8ebf5d4 — "no plan covers the root" to "the optimizer does not cover the root", behavior-neutral) + the test_query/README.md index row + link def for the new battery file (mtime 15:46:55 — the landing ran battery 15:44, production 15:45, index 15:46). External hand unattributable from tree evidence (no record drift; never reverted per the concurrent-work rule). Prior verified verdict stands for the old bytes only. Bounded Worker 2 re-verification on the diff queued in the post-dive-4 stale queue (landed-bytes == verified-bytes confirmation + battery focused run + item batteries). Dive-3 decision-request (2) (landing order) is MOOT — landed.
    - Iteration: 2. Fresh bounded Worker 2 dispatched 2026-09-23, ITEM_BASELINE c3494d3a30d0b9c6d27bb6d77e3ddeb0503ad381, workspace hunt-ws/types-resolvers-deep3-verify; expectation-first hunt-ws/w2-types-resolvers-deep3-expectation.txt (LANDED: R1-R8 + D1-D8 + P1-P8 + cells; contamination PASS with zero hits, sealed 16:08:46, hash-pinned 75500611); phase-2 drop written (hunt-ws/types-resolvers-deep3-phase2/DIAGNOSIS.txt) with 8 bounded ride-alongs (item batteries, landed battery + docstring delta, R1-R8 re-probes incl. armed interactions, failability, landed-bytes compare, DRY interaction, floor subset, diff/gates).
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows R1-R8; 15 probes + 2 controls + oracles + live async = 70 green; foreign async-boundary consolidation read as live path — one hop preserved, predicate first, region untouched; 3 robustness rows characterized, no fix; no shared-tree edits). Worker-0 mechanical checks pass (worktree digest 5f4cce2b = HEAD blob + foreign hunks only; no hunter edits; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-types-resolvers-expectation.txt`, digest 74c37a45, no diagnosis supplied): probes 17 + oracles 50/3 + 7 independent attacks green (M2M/O2O agreement, elision paths, actor switches, hop counts, strictness/misuse/hook-failure, R8 propagation, file-resolver passthrough; boundary-boom + wrong-name controls discriminate). Foreign region independently confirmed (import gone, ≥3 sites routed, hop behavior preserved). Phase-2 reconciliation: full agreement (R1-R8 same rows; counts consistent — 77 = 70 + 7 attacks; foreign no-defect; all 3 robustness rows out-of-contract with the missing row named for each). Final verdict verified. Unverified cells: PG, sharded (ORM SQL only; stub db touch only).
    - Durable evidence (compact): expectation R1-R8 (value/cost, parity, elision, scoping, hook re-check, misuse, strictness, containment); replay = battery (15) + controls (2) + oracles (50) + live async (3); controls = boundary-boom path + wrong-name identity; attacks = M2M/O2O/connection_to_attr/dict-assignment/passthrough (7). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 7 attacks + reconciliation. Target worktree digest 5f4cce2b (HEAD blob f3341e6a + foreign async-boundary hunks, untouched).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-types-resolvers-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/types-resolvers-verify/ records.
    - Cleanup: Removed hunt-ws/types-resolvers, hunt-ws/types-resolvers-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work (incl. foreign hunks) preserved.
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/canonical.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (5 contract rows R1-R5 + trust boundary; 45-battery + 8 controls + 79/63 oracles green; P4/P5 liar escapes reproduced then ruled non-defect (a)-(e): out-of-domain, no feasible path, fail-loud, precedent, reachable path ledgered to pending utils/inputs.py; no shared-tree edits). Worker-0 mechanical checks pass (digest b9ded33b == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-utils-canonical-expectation.txt`, digest 5b5d6e14, no diagnosis supplied): battery 45 + controls 8 (both seeds) + oracles 14/65/63 + 54 independent attacks green (base-slot exactness, 0-call bypass, hostile repr/huge-int/metaclass safety, key-triple exactness, consumer-walk agreement, 50k/seed stability). Liar call independently converged (reproduced both shapes; three-layer identical-behavior proof — primitive + both consumers fail-closed loud together; no promised row; robustness row). Count note: inputs oracle collects 65, not 79 (file clean vs HEAD — stale dispatch count, no action). Phase-2 reconciliation: full agreement (R1-R5, counts, liar rule with complementary proofs, consumer walks, cells). Final verdict verified. Unverified cells: PG/sharded/async (pure stdlib, inapplicable by construction).
    - Durable evidence (compact): expectation E1-E9 (base reads, refusal, total key, 0-call bypass, consumer agreement, liar rule, cells); replay = battery (45) + controls (8) + oracles (14/65/63); controls = hostile-surface existence + naive-alternative failure + cross-seed identity; attacks = shapes/refusal/bypass/key-triple/consumer-walks/edges (54). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + controls + oracles; W2 replay + 54 attacks + reconciliation. Target digest b9ded33b.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-canonical-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/utils-canonical-verify/ records.
    - Cleanup: Removed hunt-ws/utils-canonical, hunt-ws/utils-canonical-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__canonical.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__canonical.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/canonical.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__canonical.stripped.py and docs/shadow/current/django_strawberry_framework__utils__canonical.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/connections.py
    - Status: verified
    - Iteration: 1. Worker 1 reported Fixed Low (empty-string `before:""` divergence: `is_supplied` vs engine truthiness; `bool()` + parity comment) + 1 live test (`test_genre_books_connection_empty_before_behaves_like_absent`; live-first). Brute 180-case sweep 0 divergences. Worker-0 mechanical checks pass (pre-fix f549389e == HEAD blob; post-fix efcf749a / live dc0540b4 == worktree; attribution clean — fix + live test only; prose scan 0 hits; shared focused 50 + new live row 1 passed).
    - Iteration: 2. Worker 2 verified under two-phase dispatch (expectation-first `hunt-ws/w2-utils-connections-expectation.txt`, digest 32f78560, no diagnosis supplied): live red pre-fix ([a..e] with 200) / green post-fix ([d,e]); attack battery 9/10 pre-fix (only empty-cursor fails) → 10/10 post-fix (first:+after/before:"", after-alone, valid before+last flags, after+last fallback, inverted, whitespace loud, over-cap errors, probe flags, truth table, sidecar presence, keyset decode("") raises); 3 neighbors green. Owner single-file correct (walker + resolver both derive here); no-leak individually verified per site (bool() only at :675-676; keyset bounds/slicer/keyset_after correctly keep is_supplied — "" must reach decode and fail loud). Tier live-first correct; Low concurred. Ruff clean. Phase-2 reconciliation: full agreement (one scoping note — untouched window_range_plan/split/fetch rows covered by read + green neighbors + verified siblings, byte-identical pre/post; defect shape consistent; batteries complementary; truth-table edges no divergence — "0"/whitespace truthy both, 0/False wire-unreachable, "" the sole divergence fixed). Final verdict verified. Unverified cells: sharded/PG (no vendor/alias branch).
    - Durable evidence (compact): expectation (parity bool() vs is_supplied per seam); replay = live tail-vs-empty ([d,e] vs [a..e] with 200 pre-fix, both [d,e] post-fix); controls = hunt-hunk-only revert (red) + byte-identical restore + None/valid controls; attacks = falsy/edge cursor matrix + sidecar/keyset presence (10). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/connections.py (`bool()` cursor presence + parity comment) + examples/fakeshop/test_query/test_library_api.py (1 live test).
    - Verification: Passed (two-phase). Expected-before-diagnosis: hunt-ws/w2-utils-connections-expectation.txt. Evidence: hunt-ws/utils-connections-verify/ records, post-fix digest efcf749a.
    - Cleanup: Removed hunt-ws/utils-connections, hunt-ws/utils-connections-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/connections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py and docs/shadow/current/django_strawberry_framework__utils__connections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/context.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (8 contract rows C1-C8; 43 probes + 14/182/327 oracles green; 6 controls failing for intended reasons; 4 candidates disproved as unreachable-misuse/documented/delegated/misuse; no shared-tree edits). Worker-0 mechanical checks pass (digest cd0adcc5 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-utils-context-expectation.txt`, digest a08aee8c, no diagnosis supplied): probes 43 + oracles 196/295/32/144 (725 total) + 15 independent attacks green (object-shape isolation, precedence, nested publish, frozen/None reset, exceptional restore, CancelledError/custom-BaseException all paths, falsy round-trips). 2 infeasible probe shapes characterized robustness (everything-raising __getattribute__ breaks isinstance first; setattr-without-getattr contradicts documented dispatch — no feasible shape, no row). Phase-2 reconciliation: full agreement (C1-C8 1:1; counts consistent — 327 = 32+295; controls discriminate; 4 disproved correctly non-defects; infeasible shapes stay robustness; KI/SI/BaseException covered both sides). Final verdict verified. Unverified cells: PG/sharded/async (pure helper, inapplicable by construction).
    - Durable evidence (compact): expectation C1-C8 (fail-closed reads, loud-narrow writes, clear completeness, symmetry, restore, frame contracts, bounded default, trust boundary); replay = matrix (37) + controls (6) + oracles (14/182/295/32/144); controls = 6 seam mutations + BaseException instrument proof; attacks = precedence/isolation/restore/dunder-breadth/falsy (15). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + 6 controls + oracles; W2 replay + 15 attacks + reconciliation. Target digest cd0adcc5.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-context-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/utils-context-verify/ records.
    - Cleanup: Removed hunt-ws/utils-context, hunt-ws/utils-context-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__context.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__context.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__context.stripped.py and docs/shadow/current/django_strawberry_framework__utils__context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/converters.py
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (7 contract rows R1-R7; 36 probes + 249 oracles green; `is not`→`!=` control biting exactly, restored byte-identical; 2 residuals characterized robustness, not defects; no shared-tree edits). Worker-0 mechanical checks pass (digest 5332f054 == HEAD; item-scoped diff empty; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-utils-converters-expectation.txt`, digest 90314c3d, no diagnosis supplied): probes 35 + oracles 249 + 17 independent attacks green (MRO orders/diamond, precheck shadowing, CONTINUE/None, unmapped loud, enum-None unwrap, metaclass-mro lie, hash-flip bypass, eq-liar CONTINUE, value shapes, R7 parity incl. convert-only catchall). Both residuals independently reproduced and ruled robustness (instance-__class__ liar: escape is in isinstance itself, no promised row, no feasible shape; non-exact-dict registry: all riders exact-dict, no public registry input). Count note: 35 vs 36 = test_00 WS-path identity excluded, own identity proven separately. Phase-2 reconciliation: full agreement (R1-R7, counts consistent, is-not control independently confirmed via EqLiar instrument, residuals converge, R7 entailed). Final verdict verified. Unverified cells: PG/sharded/async (pure dispatch, inapplicable by construction).
    - Durable evidence (compact): expectation R1-R7 (nearest-wins, precheck order, continue/null, fallthrough, liar-safe walk, value shape, kind parity); replay = battery (35) + oracles (249); controls = is-not mutation + naive-mro-read + type-asserts; attacks = MRO/precheck/values/parity/hostile (17). Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 17 attacks + reconciliation. Target digest 5332f054.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-converters-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/utils-converters-verify/ records.
    - Cleanup: Removed hunt-ws/utils-converters, hunt-ws/utils-converters-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py and docs/shadow/current/django_strawberry_framework__utils__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/directives.py
    - Status: verified
    - ITEM_BASELINE: `4be81a10c4c55dd06863e462cd84ce34d4161923`.
    - Status at dispatch: hunt-owned uncommitted fixes + DRY-agent paths + concurrent package dirt (see Drift lines) + stray root scratch; target digest 380786cf, clean vs HEAD.
    - Iteration: 2. Resume 2026-09-21: iteration-1 workers ran (hunt-ws/utils-directives,
      hunt-ws/utils-directives-verify, w2-utils-directives-expectation.txt, all 2026-09-21)
      but the prior session ended before any report reached Worker 0; no verdict adopted.
      Target digest still 380786cf. Fresh Worker 1 dispatched, ITEM_BASELINE e9f4c22d,
      workspace hunt-ws/utils-directives-r2; orphaned scratch retained as UNVERIFIED
      orientation (re-derive every conclusion; cleaned with the item at completion).
    - Iteration: 3. Takeover 2026-09-21 (post-migration): old counterpart established inactive — sole reachable peer disclaims (DRY Worker-0, no directives work), no t3-harness processes, t3 ledger untouched since 10:46, and the referenced orphaned scratch (hunt-ws/utils-directives*, r2 workspace) never materialized anywhere — nothing to inherit, re-derive everything. Target digest still 380786cf, clean vs HEAD. Fresh Worker 1 dispatched here, ITEM_BASELINE bea285e4, evidence slug utils-directives-r3. NOTE: tests/utils/test_directives.py carries concurrent non-hunt hunks in this tree — attribution-first, pins added without disturbing them.
    - Iteration: 4. Resume 2026-09-21 (relocated worktree): no report ever reached Worker 0 for iterations 1–3 and nothing is running; the r3 workspace never materialized. Target digest still 380786cf, clean vs HEAD; tests/utils/test_directives.py now clean vs HEAD (iteration-3 concurrent-hunk note stale — verify by content anyway). Fresh Worker 1 dispatched, ITEM_BASELINE 4d579e5b, workspace hunt-ws/utils-directives-r4; re-derive everything.
    - Iteration: 5. Worker 1 reported Fixed Low (D1: raising-`__class__` liar escapes the char-wise `isinstance` interrogation raw — it sat before the `try`; fix moves it inside the single containment, char-wise values fall through to the unchanged reject; + 3 permanent tests in tests/utils/test_directives.py, tier `tests/`). Evidence: WS battery 54/57 pre (3 red raw) → 67/67 post; factory E2E typed with `__cause__` identity; 3 neuter controls red-for-reason, restored cmp-identical; shared focused 17 passed; honest messages byte-identical both eras. Worker-0 mechanical checks pass (item diff exactly the 2 files +69/−6, digests db304b50/aada70c9 == live, pre == HEAD, gates + prose clean, dry-0_0_15.md in-window drift attributed concurrent by content). Fresh Worker 2 dispatched.
    - Iteration: 6. Worker 2 verified (expectation-first `hunt-ws/w2-utils-directives-expectation.txt`, digest 623ed32f, written before opening the W1 report, unchanged at close): fresh-WS W1 battery replay 66/66 (1 mechanical identity-literal failure proving correct import); WS-only revert → exactly the 7 hostile-`__class__` probes RAW + 59 honest green, restored cmp-identical; defect test fails-without-fix, 2 pins era-identical; 51-case attack battery green; 25/25 pre/post byte-equivalence + 2 divergence controls; red oracle confirmed pre-existing identical both eras outside the path (typed surface, firing guard in concurrently-dirty types/base.py); caller files 183 + 1 known-red; owner/tier/Low concurred; gates clean.
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/directives.py (single-`try` containment of the char-wise interrogation + docstring paragraph) + tests/utils/test_directives.py (3 hostile-class tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-directives-expectation.txt. Evidence: hunt-ws/utils-directives-verify/ records, post-fix digest db304b50.
    - Cleanup: Removed hunt-ws/utils-directives-r4, hunt-ws/utils-directives-verify; expectation file retained until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__directives.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__directives.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/directives.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__directives.stripped.py and docs/shadow/current/django_strawberry_framework__utils__directives.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/errors.py
    - Status: verified
    - ITEM_BASELINE: `25db4782d4cbff490010a5ce06d4484aa11b239e`.
    - Status at dispatch: post-migration tree (26 hunt-owned production fixes + merged tests + concurrent re-tiering/docs dirt, see Drift lines); target digest 3e25e93b, clean vs HEAD.
    - Iteration: 2. Resume 2026-09-21 (relocated worktree): no report ever reached Worker 0 for iteration 1 and nothing is running. Target digest still 3e25e93b, clean vs HEAD; tests/utils/test_errors.py carries +123 DRY-owned additive tail hunks (single-owner envelope pins — concurrent, attribution-first, pins added without disturbing them). Fresh Worker 1 dispatched, ITEM_BASELINE 8285bbd2, workspace hunt-ws/utils-errors-r2; re-derive everything.
    - Iteration: 3. Worker 1 reported Fixed Low (D1: raising-`__class__` liar escapes the per-field atom interrogation raw at `errors.py:383` — the only unguarded interrogation in the file; fix guards it with `try/except BaseException → is_atom=False`, falling through to the existing tuple/single-item/`<unprintable>` chain) + 2 permanent tests in tests/utils/test_errors.py (tier `tests/` — hostile producer-authored metadata, wire-unreachable; duck-typed exc + real `ValidationError` with assigned hostile value, the feasible project shape). Evidence: WS battery 26 passed/2 failed pre-fix (digest 3e25e93b, exit 1, 1.3s) → 29 passed post-fix; WS-only revert re-reddens exactly the 2 D1 probes, restore `cmp`-identical; shared focused 43 passed; honest 41-oracle suite green both eras; ruff + trailing-commas clean. Worker-0 mechanical checks pass (item diff vs 8285bbd2 exactly the 2 files, 42+/1-; pre == HEAD blob; post digests 6bb0ad3f/31676bdb == worktree; probe digest b1f35f11 matches; test_00 pins WS import + WS DB; DRY +123 tail undisturbed; in-window docs/dry drift attributed concurrent by content; gates + prose clean). Prior session's Worker 2 child died on a transport failure before verdict — nothing inherited. Fresh Worker 2 dispatched.
    - Iteration: 4. Worker 2 verified (expectation-first `hunt-ws/w2-utils-errors-expectation.txt`, blob 2682ffab, written before opening the W1 report): fresh-WS 22-node battery 22 passed post-fix; WS-only revert → exactly the 3 seam-hitting probes red (18 pass, 1 deselected, exit 1) with pre-fix traceback at `errors.py:383` raw `RuntimeError`, restored `cmp`-identical; attacks green (spoofed `__class__` shapes pinned, hostile `__str__`/`__iter__`/midway/`__bool__`, unhashable, all six sibling interrogations, honest snapshot byte-identical via `diff`); `KeyboardInterrupt`-via-`__class__` discriminator proves `except BaseException` breadth load-bearing (contained post-fix, aborts pre-fix); suites 43 + 253 + live 159 with the 3 pre-existing `pathological_json_text` fixture-overflow errors (interpreter cell, setup-phase, identical to W1's record); permanent tests fail-without/pass-with; tier `tests/` + Low + owner all concurred; item diff exactly 42+/1-, gates + prose clean. Unverified cells: sharded/PG/async inapplicable by construction (pure module, AST-pinned zero settings reads).
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/errors.py (guarded per-field atom interrogation in `validation_error_to_field_errors`) + tests/utils/test_errors.py (2 hostile-class mapper tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-errors-expectation.txt. Evidence: hunt-ws/utils-errors-verify/ records, post-fix digest 6bb0ad3f.
    - Cleanup: Removed hunt-ws/utils-errors-r2, hunt-ws/utils-errors-verify; expectation file retained until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__errors.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/errors.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py and docs/shadow/current/django_strawberry_framework__utils__errors.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/execution_mode.py
    - Status: verified
    - ITEM_BASELINE: `25db4782d4cbff490010a5ce06d4484aa11b239e`.
    - Status at dispatch: post-migration tree (26 hunt-owned production fixes + merged tests + concurrent re-tiering/docs dirt, see Drift lines); target digest 9805cdaf, clean vs HEAD.
    - Iteration: 2. Resume 2026-09-21 (relocated worktree): no report ever reached Worker 0 for iteration 1 and nothing is running. Target digest still 9805cdaf, clean vs HEAD; tests/utils/test_execution_mode.py clean vs HEAD. Fresh Worker 1 dispatched, ITEM_BASELINE 50914191, workspace hunt-ws/utils-execution-mode-r2; re-derive everything.
    - Iteration: 3. Worker 1 reported No bugs (19-probe battery 19 passed, exit 0; oracles 64 + 2 refusal rows green; 3 WS-only controls biting exactly — flipped-mode 6 red, neutered-raise 3 red, skipped-close 1 stale-ASYNC — restored `cmp`-identical; upstream strawberry seam audited at 0.324.0 runtime + 0.316.0 floor statically; 4 candidates characterized — non-enum mode fails toward SYNC, docstring both-None case, masking wires via error_policy, no permanent-test equivalent for the subscribe/nesting rows — none a defect). Zero shared-tree edits. Worker-0 mechanical checks pass (probe digest 50643629 matches; test_00 pins WS PKG + TARGET + DB; target 9805cdaf == HEAD; `git diff 50914191` names only this progress file; counts non-trivial; controls discriminate; cells stated with PG/sharded inapplicable-by-construction for W2 to judge). Fresh Worker 2 dispatched.
    - Iteration: 4. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-execution-mode-expectation.txt`, blob d037e6ab, written before opening the W1 report): fresh-WS replay 19/19 + 31 independent attacks 50/50 combined (nesting matrix both directions, copied-before-bind, close-then-rebind, bind/unbind exception restore, zero-frame `aclose`, disagreement readers, stream cancel drives, R7 pushed past W1 — admitted + all three resolution-refusal shapes carry the matching marker through the real runner); refusal-neutering control reds exactly the 4 refusal-sensitive probes, restored `cmp`-identical; oracles 64 + 2 match; per-axis judgments concur (1/3/5 reason-only, rest probed); all 4 characterizations correctly non-defects, plus w20/w22 (nested plain schema reads outer binding — contract-consistent, mixed-spelling consequence loud); upstream seam independently audited at 0.324.0 + floor 0.316.0; item-scoped diff empty; zero tracked-file edits. One documented WS deviation: `--exclude hunt-ws/` added to the rsync (literal recipe would nest 522M of sibling scratch); isolation pins hold. Unverified cells: floor-runtime, floor-Python; PG/sharded inapplicable by construction (ContextVar + loop check only, full 153 lines read).
    - Result: No bugs. Evidence: W1 battery 19 + 3 controls + oracles; W2 replay + 31 attacks + control + upstream audit. Target digest 9805cdaf.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-execution-mode-expectation.txt. Evidence: hunt-ws/utils-execution-mode-verify/ records.
    - Cleanup: Removed hunt-ws/utils-execution-mode-r2, hunt-ws/utils-execution-mode-verify; expectation file retained until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__execution_mode.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__execution_mode.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/execution_mode.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__execution_mode.stripped.py and docs/shadow/current/django_strawberry_framework__utils__execution_mode.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/imports.py
    - Status: verified
    - ITEM_BASELINE: `25db4782d4cbff490010a5ce06d4484aa11b239e`.
    - Status at dispatch: post-migration tree (26 hunt-owned production fixes + merged tests + concurrent re-tiering/docs dirt, see Drift lines); target digest 291ecedd, clean vs HEAD.
    - Iteration: 2. Resume 2026-09-21 (relocated worktree): no report ever reached Worker 0 for iteration 1 and nothing is running. Target digest still 291ecedd, clean vs HEAD; tests/utils/test_imports.py clean vs HEAD. Fresh Worker 1 dispatched, ITEM_BASELINE f84b6fdf, workspace hunt-ws/utils-imports-r2; re-derive everything.
    - Iteration: 3. Worker 1 reported No bugs (27-probe battery 27 passed, exit 0; oracles 180 passed + 2 pg-skips across every consumer incl. live mutation-atomicity seam row; 4 WS-only controls biting exactly — normalization-drop 3 red, `except→raise` dies via the converters postgres-sentinel chain, loaded-no-import 1 red, hint-drop 3 red — restored identical; every production caller passes plain-str literals per grep; body-`ImportError`-masking + `__class__`-liar-loud characterized as documented/no-contract, not defects). Zero shared-tree edits. Worker-0 mechanical checks pass (probe 6d433859 on disk; test_00 pins WS import + prints DB/CWD; target 291ecedd == HEAD; tests/pyproject digests match; `git diff f84b6fdf` names only this progress file + in-window DRY drift; counts non-trivial; controls discriminate; cells stated with PG/sharded inapplicable-by-construction for W2 to judge). Fresh Worker 2 dispatched.
    - Iteration: 4. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-imports-expectation.txt`, blob a17e7d5a, written before opening the W1 report): fresh-WS replay 27/27 (verbatim run fails only test_00's path literal while printing correct verify-WS isolation — mechanical, repointed WS-only with zero product assertions changed) + 27 independent attacks green (`__cause__` identity, hint never evaluated on success, `_plain_text` identity semantics, unhashable/hostile-hash loud, dotted-attr no-traversal lock, submodule-vs-attr, require→evict→loaded sequence, rebind-v2 all helpers, 32 concurrent agree, partially-initialized self-lookup both directions, `__getattr__` loud family, pollution snapshot empty, unicode incl. EvilStr, all 6 flavor seams + 7 hint sites, keyset crypto both ways, `ValueError` never reframed); own normalization-drop control 6 red for intended reasons, restored `cmp`-identical, 54/54 re-green; oracles 670 + 2 pg-skips + 1 live (superset of W1's 180); caller-literals claim independently re-verified by W2's own grep incl. both parameterized chains; all characterizations correctly non-defects (one reason-note: masking ground is no-promised-row + documented policy, not W1's imprecise sentinel-contract sentence — disposition unchanged); item-scoped diff empty; zero tracked-file edits. Unverified cells: PG/sharded as runs, concurred inapplicable by construction (importlib/sys/typing only, whole 139 lines read).
    - Result: No bugs. Evidence: W1 battery 27 + 4 controls + oracles; W2 replay + 27 attacks + control + oracle superset. Target digest 291ecedd.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-imports-expectation.txt. Evidence: hunt-ws/utils-imports-verify/ records.
    - Cleanup: Removed hunt-ws/utils-imports-r2, hunt-ws/utils-imports-verify; expectation file retained until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py and docs/shadow/current/django_strawberry_framework__utils__imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/input_values.py
    - Status: verified
    - ITEM_BASELINE: `25db4782d4cbff490010a5ce06d4484aa11b239e`.
    - Status at dispatch: post-migration tree (26 hunt-owned production fixes + merged tests + concurrent re-tiering/docs dirt, see Drift lines); target digest f2566609, clean vs HEAD.
    - Iteration: 2. Resume 2026-09-21 (relocated worktree): no report ever reached Worker 0 for iteration 1 and nothing is running. Target digest still f2566609, clean vs HEAD; tests/utils/test_input_values.py clean vs HEAD. Fresh Worker 1 dispatched, ITEM_BASELINE 3e156a2b, workspace hunt-ws/utils-input-values-r2; re-derive everything.
    - Iteration: 3. Worker 1 reported Fixed Low (D1: `str`-subclass `__qualname__` escapes the depth-cap raise raw — the label read accepts any `str` instance and interpolates it, running hostile `__str__`/`__format__` while the already-decided failure assembles; fix coerces via `str.__str__` inside the contained read with `_safe_type_name` fallback + docstring sentence) + 1 permanent test in tests/utils/test_input_values.py (tier `tests/` — hostile label is declaration-time, wire-unreachable; honest trigger already pinned live). Evidence: D1 battery 3 red raw pre-fix (recording probe proves hostile code executed via `"INJECTED"`) → 3 green post-fix; full battery 62 green; oracles 89 + live 1; M1/M2/M3 mutation controls red-for-reason, restored `cmp`-identical; failability twin 1 failed/37 passed; shared focused 34 passed; gates pass on touched paths (repo-wide `--fix`/format deliberately skipped — 2722 errors/25 unformatted files from concurrent dirt + nested workspaces, documented). Out-of-scope leads: L1 filters/sets.py non-int-depth (claimed historically accepted), L2 orders normalizer uncapped recursion (W1 mislabels that item "pending" — it is verified; W2 to judge the characterization), L3 liar/knob escapes as robustness rows. Worker-0 mechanical checks pass (item diff vs 3e156a2b exactly the 2 files; pre == HEAD blob; post digests d4ebeeb6/d3ab2892 == worktree; probe digests 48451587/bbfa54be/5d19e730 match; test_00 pins WS import + WS DB; in-window dry drift attributed concurrent by content; gates + prose clean). Fresh Worker 2 dispatched.
    - Iteration: 4. Worker 2 verified (expectation-first `hunt-ws/w2-utils-input-values-expectation.txt`, blob 90dbcbed, sealed before opening the W1 report; W1 probes never opened — full independent reconstruction): fresh-WS battery 30 passed post-fix; WS-only revert (differing from the pre-fix blob only by the docstring sentence, diff-proven) → 7 failed raw + 22 passed + the KI probe aborting the session pre-fix, restored `cmp`-identical; permanent file 1 failed/33 passed pre-fix; attacks green (str-only/format-only/recording with `fired==[]`, KI containment, absent/non-str/raising qualname, liar-label collapse, noisy dunders, repeated-call identity, subject composition); honest exact-message rows + cap-boundary identical pre/post; `subject` trace complete (only literal `"FilterSet"` + none callers; hostile subject/branch/knob shapes raw-by-design, identical pre/post); single live `nesting exceeded` site grep-proven, both walks delegate; suites 120 + live 1, zero red; tier `tests/` + Low + owner concurred; L1 confirmed no-contradiction (historical "EXAMINED AND ACCEPTED" + guard digest intact), L2 stands as robustness row (permission-first structurally proven; W1's "pending" label wrong but immaterial), L3 confirmed; repo-wide `--fix` skip judged correct (touched-path gates are the criterion); item diff exactly the hunk + docstring + 1 test; gates + prose clean. New out-of-scope lead (not this verdict): orders/inputs.py:332 `owner_name` same-class escape, real-path probe d9216a9c + unprobed family mentions at filters/sets.py (7 sites), orders/sets.py, utils/inputs.py, sets_mixins.py — routed by Worker 0 (see stale/lead notes). Unverified cells: none unrun; PG/sharded/async inapplicable by construction (pure helper).
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/input_values.py (`str.__str__` label coercion + `_safe_type_name` fallback in `raise_set_traversal_depth_exceeded`) + tests/utils/test_input_values.py (1 hostile-qualname test).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-input-values-expectation.txt. Evidence: hunt-ws/utils-input-values-verify/ records, post-fix digest d4ebeeb6.
    - Cleanup: Removed hunt-ws/utils-input-values-r2, hunt-ws/utils-input-values-verify; expectation file retained until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/input_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/inputs.py
    - Status: verified
    - Forwarded lead (from sets_mixins.py verification, robustness row, pre-existing): end-to-end `Meta.fields = <raising-liar>` on a real FilterSet/OrderSet escapes raw at `utils/inputs.py::canonicalize_set_meta_fields` (`isinstance(fields, (set, frozenset))` via `orders/sets.py::_expand_meta_fields`) and at `filters/sets.py::FilterSet.get_fields` pre-check; filter-side class-body decl-spoof detonates inside upstream django_filters (`creation_counter` sort). Producer-authored only, no fail-open. Assess at this owner; bounded stale-check note on filters/sets.py (verified Fixed — re-check only its get_fields pre-check seam).
    - ITEM_BASELINE: `712db5d3b3dd1242dccf8a18d7e7bb34c1ac9aaa`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-21, workspace hunt-ws/utils-inputs-r1; target digest ee31d360, clean vs HEAD; tests/utils/test_inputs.py clean vs HEAD; filters/sets.py carries the ledgered declared-key-guard fix (attribution-first; bounded stale-check of its get_fields pre-check seam per the forwarded lead).
    - Lead 2026-09-21 (from input_values verification, UNPROBED family mention): unguarded `__qualname__` interpolation claimed in this target, same escape class as input_values D1. Assess within this hunt (confirm-or-disprove with a probe on current source); forwarded to the running Worker 1 by message (folded into D7). SEPARATE: the get_fields `is_str` guard hunk (+10/-1) in `filters/sets.py` is CONFIRMED as this item's D8 (reported with evidence, see Iteration 2).
    - Iteration: 2. Worker 1 reported Fixed Low, 8 defects one bug class (loud-but-untyped → typed at declaration seams: D1 `canonicalize_set_meta_fields` liar read; D2 factory mapping gate 4× `isinstance`; D3 `_hashable_meta_value` dispatch; D4 field-name-sequence dispatches; D5 dynamic-class model gate; D6 lazy-annotation subclass check + `{set_class!r}` label; D7 six label sites via `_safe_class_name` + new `_safe_module_qualname`; D8 filters/sets.py get_fields pre-check guard at the bounded seam) + 13 hostile tests in tests/utils/test_inputs.py + 1 appended test in tests/filters/test_sets.py (tier `tests/` — hostile declarations wire-unreachable). Evidence: battery 49 passed (lead frames, honest matrix, hostile labels); failability WS 14 red raw on surgical revert → 18 green on `cmp`-identical restore; honest 12-row capture `diff`-empty pre/post (`PYTHONHASHSEED=0`); neighbors 1069 passed; gates pass on all 4 touched paths. Forwarded leads (out of fence, evidence in probes): orders/sets.py `== "__all__"` hostile-`__eq__` raw; filters/sets.py `!= "__all__"` Collection-hostile-`__eq__` raw (outside the D8 seam); utils/strings.py `_plain_text` unguarded `isinstance` (unreachable via this module's callers). Worker-0 mechanical checks pass (item diff vs 712db5d3 exactly the 4 item files + 2 ledgered input_values files + this progress file + concurrent dry drift; pre digests == baseline blobs; post digests 47b2af21/61e1b2c9/049cb40c/5d8e0f13 == worktree; D8 hunk only vs baseline, ledgered guard predates it; test_sets.py delta is the 1 append, priors incl. the ledgered two-lookups test intact; probes on disk with WS pins; counts/controls/reach stated; gates + prose clean). Fresh Worker 2 dispatched.
    - Iteration: 3. Worker 2 verified Fixed Low (expectation-first `hunt-ws/w2-utils-inputs-expectation.txt`, bug-class + E1–E8 rows, written before opening the W1 report): all 14 permanent tests red on production-only revert in fresh `hunt-ws/utils-inputs-verify/` (13 in tests/utils/test_inputs.py + the filters/sets.py append), green post-fix; D8 `filters/sets.py` get_fields pre-check proven necessary and sufficient for the FilterSet end-to-end liar shape; independent attack battery on disk (`w2-probes/test_w2_inputs_attacks.py`, 47 nodes + honest capture) with WS PKG + DB pins. Owner/tier/Low concurred; ruff + prose clean. Folded by the resume Worker-0 from the handoff verdict + on-disk expectation and probes (the W2 /tmp report itself did not survive the dead session); post-fix digests 47b2af21/61e1b2c9/049cb40c/5d8e0f13 re-confirmed == worktree (main fast-forward untouched these files).
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/inputs.py (D1–D7 declaration-seam guards + `_safe_module_qualname`) + django_strawberry_framework/filters/sets.py (D8 get_fields pre-check guard) + tests/utils/test_inputs.py (13 hostile tests) + tests/filters/test_sets.py (1 appended liar test).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-inputs-expectation.txt. Evidence: hunt-ws/utils-inputs-verify/ records, post-fix digests 47b2af21/61e1b2c9/049cb40c/5d8e0f13.
    - Cleanup: Removed hunt-ws/utils-inputs-r1, hunt-ws/utils-inputs-fail, hunt-ws/utils-inputs-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/operation_lease.py
    - Status: verified
    - ITEM_BASELINE: `d169e8a117533e4b73dc7eef695c2d48c307560b`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-21, workspace hunt-ws/utils-operation-lease-r1; target digest 10c164b7, clean vs HEAD; no dedicated tests/utils/test_operation_lease.py — nearest suite tests/extensions/test_operation_state.py clean vs HEAD (attribution-first if a permanent test lands there).
    - Iteration: 2. Worker 1 reported No bugs (33-node battery 30 passed + 3 strict-xfail controls biting, exit 0; oracles 359 + 847 green; M1 close-neuter 20 red exact rows + M2 held-None 16 red exact rows, both restored `cmp`-identical with digest re-confirmed; 5 construction sites all non-None + unexported ⇒ None-payload infeasible; re-arm/copy/pickle characterized with infeasibility; full 922-line runner + all readers traced; no permanent test — every row pinned at owner tiers). Zero shared-tree edits. One disclosed incident: t09 stranded a task under M2 (probe bug — reach-assert before release; own PIDs killed, fixed with release-in-finally, M2 re-ran clean; verdict rests on the clean re-run). Worker-0 mechanical checks pass (probe digests 68f58211/167ef3c7/10c164b7 match; test_00 pins WS PKG + DB + target identity; target 10c164b7 == HEAD; `git diff d169e8a1` names only other items' files + this progress file + concurrent dry drift; counts non-trivial; controls discriminate; cells stated with PG/sharded inapplicable-by-construction for W2 to judge). Fresh Worker 2 dispatched.
    - Iteration: 3. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-operation-lease-expectation.txt`, E1–E7 + L8 characterization, written before opening the W1 report): W1 battery replayed 30 passed + 3 xfailed in fresh `hunt-ws/utils-operation-lease-verify/` (PKG + DB pins printed inside `$WS`); independent 17-probe attack battery all green (close-before-read, 10k-lease half-release, outstanding-handle-survives-close, pre-bind copy, task-cancel, thread handoff, subclass surface, 1000× interleave, iteration-survives-close, caller-exception, two-scope both orders, payload-vs-lease lifetime, wrong-type generics, `==`-vs-`is`, 1000 cycles, closed-bind-fails-closed); own `close→del`-slot control failed exactly the 15 close-touching items with `AttributeError`, restored `cmp`-identical; oracles 359 + 847 match W1 with zero reds; censuses redone (5/5 constructions non-None, zero exports, zero re-arms, zero lease copies, all 7 `held()` readers `is`-compared); item-scoped diff empty. Floor-Python 3.10 unverified (only 3.14.2 on the machine); PG/sharded inapplicable by construction, concurred. Folded by the resume Worker-0 from the surviving W2 report; target digest 10c164b7 re-confirmed == HEAD (main fast-forward untouched this file).
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 17 attacks + control. Target digest 10c164b7.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-operation-lease-expectation.txt. Evidence: hunt-ws/utils-operation-lease-verify/ records.
    - Cleanup: Removed hunt-ws/utils-operation-lease-r1, hunt-ws/utils-operation-lease-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__operation_lease.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__operation_lease.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/operation_lease.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__operation_lease.stripped.py and docs/shadow/current/django_strawberry_framework__utils__operation_lease.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/permissions.py
    - Status: verified
    - ITEM_BASELINE: `f98f4eedfb6121b25574eb27d4c3b7a135e6110e`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-21, workspace hunt-ws/utils-permissions-r1; target digest 9889d6fe, clean vs HEAD; tests/utils/test_permissions.py clean vs HEAD.
    - Iteration: 2. Worker 1 died by infra failure 2026-09-21 (model-stream idle timeout, no report, no verdict — not evidence of anything); shared tree untouched (`git diff f98f4eed` names only the inputs-item files + this progress file + concurrent dry drift; target/tests clean, digest still 9889d6fe). Orphaned `hunt-ws/utils-permissions-r1/` retained as UNVERIFIED orientation (re-derive every conclusion; removed with the item at completion). Fresh Worker 1 dispatched, ITEM_BASELINE 387acb73, workspace hunt-ws/utils-permissions-r2; re-derive everything.
    - Iteration: 3. Worker 1 (r2) reported No bugs (43-node battery green: shapes incl. order-tuple-inert twins, absent-vs-null, lexical, hostile objects, config incl. boom-router proofs, live load-bearing stateful both-direction immediacy, interruption, channels-absent; oracles 56 + 25 + 3 green; gate-neuter + flat-walk-neuter controls biting, restored `cmp`-identical; 8 candidates disproved with C1/C2/C8 as robustness observations). Zero shared-tree edits. Worker-0 mechanical checks pass (probes on disk with WS PKG + DB pins; target 9889d6fe + tests abf30ad3 == HEAD; item diff vs 387acb73 empty on target/tests; reach asserts in-probe; controls discriminate; PG/sharded/async-transport listed unverified). One drift note for W2: the run's `utils/querysets.py` freshness digest 96618fba predates the 69a25369..24e6b4d3 fast-forward (HEAD now b68be0e3) — re-derive everything at current bytes. Fresh Worker 2 dispatched, workspace hunt-ws/utils-permissions-verify, expectation-first.
    - Iteration: 4. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-permissions-expectation.txt`, E1–E8 all confirmed, written before opening the W1 report/probes): 43/43 W1 probes replayed green in the fresh WS at current bytes (43 collected / 0 skipped / exit 0 / 7.06s; package + DB proven inside WS); 33/33 independent attacks green (non-dict Mappings, falsy reads, UNSET whole-input, duplicate-decl determinism, overshoot/garbage, callable-gate propagation, scope/request precedence pins, delegation rawness, AUTH edges, depth off-by-one 8-pass/9-raise, retry semantics, cache isolation, wrapper equivalence, zero-SQL aliases measured, sync-walk-under-loop, channels-never-imported, non-coroutine awaitable, 4 live wire probes); package oracle 56/56 + live 31 + 10 green (final combined 132 passed); 2 WS-only mutants each failed the intended instruments, restored `cmp`-identical (digest 9889d6fe); item-scoped diff empty. Drift discharged: querysets delta confined to the seal region (lines 2404+), the `reject_async_in_sync_context` region byte-identical across the fast-forward and the sole import — no permissions claim affected; every other W1 freshness digest matches. Axes 1–7 hold extended to opposite arms; C1/C2/C5/C6/C8 dispositions agreed; R7 inapplicability UPGRADED to measured zero-query evidence; PG/sharded/async-transport stay unverified. Folded by Worker-0 from the W2 verdict (full text recovered from the child session log after a truncated delivery); target 9889d6fe + tests abf30ad3 re-confirmed == HEAD.
    - Result: No bugs. Evidence: W1 battery + 2 controls + oracles; W2 replay + 33 attacks + 2 controls + drift discharge. Target digest 9889d6fe.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-permissions-expectation.txt. Evidence: hunt-ws/utils-permissions-verify/ records.
    - Cleanup: Removed hunt-ws/utils-permissions-r1, hunt-ws/utils-permissions-r2, hunt-ws/utils-permissions-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/policies.py
    - Status: verified
    - ITEM_BASELINE: `2e546fd4725aafc8ecafb8d3b9e874d054ba2fae`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-21, workspace hunt-ws/utils-policies-r1; target digest 860b181f, clean vs HEAD; tests/utils/test_policies.py clean vs HEAD.
    - Iteration: 2. Worker 1 died mid-probe by infra failure 2026-09-21 (no report, no verdict — not evidence of anything); shared tree untouched (target/tests clean). Orphaned `hunt-ws/utils-policies-r1/` retained as UNVERIFIED orientation (re-derive every conclusion; removed with the item at completion). Main fast-forward 69a25369..24e6b4d3 rewrote the target meanwhile (9350eb8d canonical-copy seams; 860b181f → HEAD 8c881c0a, worktree clean). Fresh Worker 1 dispatched, ITEM_BASELINE 7c2d4c4f, workspace hunt-ws/utils-policies-r2; hunts the new bytes, re-derives everything.
    - Iteration: 3. Worker 1 (r2) reported Fixed Low, one bug class at four seams of `resolve_policy`: hostile `__class__` on the explicit/setting classification reads (D1) + the key-type guard (D2), hostile `__eq__` on valid-name membership (D3), hostile `__lt__` in `sorted(unknown)` (D4) — all raw `RuntimeError` where the contract promises typed `ConfigurationError`. Fix at the owner: 4 guarded `isinstance` reads with the existing typed messages + `str.__str__` key normalization before membership/`sorted`/`join`/construction with a typed "key comparison failed" arm (+56/-7) + 5 permanent tests in tests/utils/test_policies.py tier `tests/` (explicit liar, setting liar, key liar, hostile-eq acceptance, hostile-lt vocabulary rejection). Evidence: battery green (shapes 19, realnull 9, stateful 6/6 incl. 9350eb8d canonical-copy isolation, interruption, benign subclasses); preview 5 red raw pre-fix → 5 green post-fix, restored byte-identical (sha256 7cc567ee); copy-identity control biting; oracles 382/382 pre+post; shared focused 22 passed. Worker-0 mechanical checks pass (post-fix digests 3f2066a9/60384e37 == worktree; item diff vs 7c2d4c4f exactly the 2 files; probes on disk with WS pins; counts/controls/reach stated; ruff format --check + check clean; banned-token scan clean). Report recovered verbatim from the child session log to `/tmp/w1-policies-r2-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-policies-verify, expectation-first.
    - Iteration: 4. Worker 2 verdict: revision-needed on ONE gap (report recovered verbatim to `/tmp/w2-policies-verify-report.txt`): the fix is correct at the owner and all 5 permanent tests fail-raw-pre / pass-post (WS-only revert control, restored cmp-identical sha256 7cc567ee), but two new guard arms have no reaching test — coverage 67 stmts / 4 miss / 94%, missing lines 172-173 (`isinstance(overrides, Mapping)` except arm) and 225-226 (normalization "key comparison failed" except arm) — breaking `fail_under = 100`. Both arms proven reachable by W2 probes in the same liar style at the same tier (`w2probes/test_w2_reach.py` in the verify WS, left intact): arm 1 via a stateful-`__class__` liar in the SETTING slot (explicit-slot variant does NOT reach it — second guard fires first), arm 2 via a non-str key whose `__class__` lies `str`. Everything else stands verified: 13 attacks green (7 discriminate pre-fix), owner/tier/Low concurred, ruff + prose clean, inapplicable-by-construction reason sound with cells kept unverified. Full-suite attribution control: the known DECISION REQUEST red fails identically with the production hunk reverted — independent of this fix. Same item back to Worker 1 with workspaces intact for the 2-test revision (no production change owed).
    - Iteration: 5. Worker 1 revision: +2 tests in tests/utils/test_policies.py (`test_a_second_read_hostile_setting_override_is_typed_rejected` → arm 172-173 via the setting slot; `test_a_str_lying_key_is_typed_rejected_at_normalization` → arm 225-226; helpers `_SecondReadHostile`, `_StrLyingKey`), production byte-identical. Proof: WS-only production revert → 2 new tests fail raw as intended (`RuntimeError: hostile __class__`, `TypeError` from `join`), restored cmp-identical (3f2066a9 / 7cc567ee); shared focused 24 passed; coverage 67/0/100% on the module with flavor oracles (focused-file-only misses are other-tier lines). Worker-0 mechanical checks pass (production 3f2066a9 unchanged; tests 60384e37 → 763ee8ca, exactly 7 added `def test_` vs HEAD; ruff format --check + check clean; banned-token scan clean). Report recovered verbatim to `/tmp/w1-policies-revision-report.txt`. Fresh Worker 2 re-verification dispatched (criteria-first: the 2 new tests fail-without-fix, 100% module coverage, no regression on iteration-4 verified results).
    - Iteration: 6. Worker 2 re-verified (criteria K1–K5 all hold; expectation stands with no delta): K1 the 2 new tests fail raw without the fix (`RuntimeError: hostile __class__`, `TypeError` from `join` at pre-fix `policies.py:184`) and pass with it (WS-only revert, restored cmp-identical sha256 7cc567ee); K2 lines 172-173 + 225-226 covered (focused 67/5/93% with only pre-existing other-tier misses 55-57/94-95; + flavor oracles 389 passed, 67/0/100%); K3 production 3f2066a9 cmp-identical to the r1 gold; K4 no regression (7/7 fail pre, 24/24 pass post, twice; oracles 389 green); K5 tier/prose/ruff clean (purely additive hunk, zero banned tokens, `utils/policies.py::resolve_policy` cited). Replay: 24/24 green, revert 7/7 raw, restored 24/24, oracles 389. Folded by Worker-0 from the verdict (recovered verbatim to `/tmp/w2-policies-reverify-report.txt`); digests 3f2066a9/763ee8ca re-confirmed == worktree.
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/policies.py (4 guarded `isinstance` reads + `str.__str__` key normalization with typed "key comparison failed" arm) + tests/utils/test_policies.py (7 hostile tests).
    - Verification: Passed (iterations 4 + 6, two-phase). Expected-before-diagnosis: hunt-ws/w2-utils-policies-expectation.txt. Evidence: hunt-ws/utils-policies-verify/ + hunt-ws/utils-policies-reverify/ records, post-fix digests 3f2066a9/763ee8ca.
    - Cleanup: Removed hunt-ws/utils-policies-r1, hunt-ws/utils-policies-r2, hunt-ws/utils-policies-verify, hunt-ws/utils-policies-reverify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__policies.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__policies.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/policies.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__policies.stripped.py and docs/shadow/current/django_strawberry_framework__utils__policies.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/private_state.py
    - Status: verified
    - ITEM_BASELINE: `48ef3650b7c37c2aecb518411169cb05e8e71b85`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-21 ~22:45, workspace hunt-ws/utils-private-state-r1; target digest 08088b82, clean vs HEAD; no dedicated tests/utils/test_private_state.py and no test file references the module — nearest suites TBD by the W1 trace (attribution-first if a permanent test lands anywhere). Consumers at current bytes: optimizer/extension.py, extensions/resource_policy.py, extensions/debug.py, extensions/operation_state.py, schema.py (resource_policy extension + schema are stale re-passes post-fast-forward; read at live bytes, fix across only on a confirmed crossing invariant with a named reason).
    - Iteration: 2. Worker 1 reported No bugs (66-probe battery green: authority/identity/membership/box/adversarial/lifecycle/e2e-schema; 9 contract rows R1–R9; 3 WS-only mutation controls biting exactly the intended probes, restored sha-verified; consumer oracles 636 + 284 passed with 1 red = the campaign-recorded DECISION REQUEST test, disclosed as unrelated; 4 candidates disproved with 2 robustness notes, no edit). Zero shared-tree edits. Worker-0 mechanical checks pass (target 08088b82 == HEAD; item diff empty; 8 probe files on disk with WS PKG + DB env anchor; counts/controls/reach stated; inapplicable-by-construction cells reasoned, floor-3.10 unverified; no stray files). Report recovered verbatim from the child session log to `/tmp/w1-private-state-r1-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-private-state-verify, expectation-first.
    - Iteration: 3. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-private-state-expectation.txt`, R1–R9 + C1–C8, written before opening the W1 report/probes; WS built + anchored first): W1 battery replayed 66/66 green in the fresh WS (exit 0, 2.59s; PKG + DB pins inside `$WS`); independent 83-node attack battery 82 passed + 1 allocator-luck skip (successor-guard canary closing W1's hollow M3, mid-accept atomicity incl. reentrant-during-evidence, 22-row evidence-vs-attribute matrix, box-binding routes, detonating-owner authority, threaded death storms, 5000-scale, e2e opposites incl. `__dict__.clear()` loud refusal + copy-mutation no-widening); combined 148 + 1 green post-restore; positive-control mutation bit exactly the 2 predicted probes, restored `cmp`-identical (sha256 361469fc matches W1's pristine record); oracles 636 + 284 with only the campaign-known red; floor cell EXECUTED (28 checks identical on 3.10/3.11/3.12/3.14 — upgrades W1's floor-unverified for target logic; Django-consumer e2e stays 3.14-only). All 4 candidate rulings + 2 robustness notes agreed evidence-backed; inapplicable axes/cells agreed per-consumer; severity n/a. Folded by Worker-0 from the W2 verdict (recovered verbatim to `/tmp/w2-private-state-verify-report.txt` after a truncated delivery); target 08088b82 re-confirmed == HEAD.
    - Result: No bugs. Evidence: W1 battery + 3 controls + oracles; W2 replay + 83 attacks + control + floor cell. Target digest 08088b82.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-private-state-expectation.txt. Evidence: hunt-ws/utils-private-state-verify/ records.
    - Cleanup: Removed hunt-ws/utils-private-state-r1, hunt-ws/utils-private-state-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__private_state.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__private_state.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/private_state.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__private_state.stripped.py and docs/shadow/current/django_strawberry_framework__utils__private_state.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/querysets.py
    - Status: verified
    - Stale 2026-09-22: walker verification (W2, own evidence) confirms D1 HAS STANDING — hook-returned union/intersection/difference on plain-list relations escapes the `_LIST_RELATION_CHILD_POLICY` seal raw (`NotSupportedError` at `plans.py::apply` / fetch-time refilter) instead of the sealed typed `ConfigurationError` (row README:395 read directly; shape: legitimate combinator hook return; input: wire query selecting the relation, live-proven L1/B2/B3; Low concurred). Prior verified verdict stands for all else. Narrow re-pass queued after types/finalizer, before the scenarios: the `_LIST` reject_combined seam, re-derived at dispatch from the W2 evidence (W1 prescription advisory only; prose trap + unpinned matrix + O3 oracle reckoning ride along). RECORDED RIO DECISION (deferred scope, non-blocking): the same class live-proven on `_DEFAULT` surfaces (L4/L5 — S1 provably doesn't fix) + spender census + `_DEFAULT`-flip simulation (2 premise pins fail, Decision-8 ripple). The re-pass confirms-or-disproves the `_DEFAULT` extension and REPORTS; it must NOT flip `_DEFAULT` without Rio. Evidence: /tmp/w1-walker-stale-r1-report.txt + /tmp/w2-walker-stale-report.txt + hunt-ws/w2-walker-stale-expectation.txt (workspaces removed post-verify — re-derive on current source at dispatch; target 799139be unchanged since verification).
    - Note 2026-09-21 ~22:45: main fast-forward 69a25369..24e6b4d3 rewrote the target (+251 lines: shared sidecar-seal helpers, child policies; HEAD digest b68be0e3, worktree clean — never hunted post-seal). Hunts at the new bytes; shadow orientation is stale for this file, live source authoritative.
    - ITEM_BASELINE: `2db65089f46f5eafc6f3299287573a612a607934`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/utils-querysets-r1; target digest b68be0e3, clean vs HEAD; tests/utils/test_querysets.py clean vs HEAD (the committed proxy-fixture rows are baseline-scenario ledger, settled). Entry point into the seal/sidecar/child-policy system: read connection.py + list_field.py + optimizer/walker.py + optimizer/nested_planner.py at live bytes (all stale re-passes post-fast-forward; fix across only on a confirmed crossing invariant with a named reason).
    - Iteration: 2. Worker 1 reported Fixed Low, one defect D1 at two sites: `_apply_sidecar_sync` + `_apply_sidecar_async` built `method_name` from raw `set_class.__name__` — a raising metaclass `__name__` escaped raw `RuntimeError` (breaking even the honest path), a str-subclass `__name__` dispatched hostile `__format__` (1 call observed) — violating the module's own R13 safe-label row. Fix at the owner: both reads via `_safe_class_name(set_class)` (2 lines; honest message byte-identical, `cmp`-clean) + 5 permanent tests in tests/utils/test_querysets.py tier `tests/` (sync/async honest-path survival, sync/async typed rejection, `__format__`-never-dispatched pin). Evidence: 13 contract rows R1–R13; battery 154/154 green post-fix (P0–P9; header says 152 — minor count slip for W2 to reconcile); 6/6 mutation controls biting with `cmp`-identical restores; oracles 334/334 + 428/428 + list_field 109 + the 1 known DECISION REQUEST red reproduced exactly, untouched; honest pre/post `cmp`-identical; shared focused 5/5. 4 robustness rows recorded without fix (prefetch-entry `__class__` liars fail closed with no public-API shape; exact-QuerySet cache trust; shared-list carry aliasing per glossary; unresolvable-path documented fail-open). No new scenario (raw-list bound hunted at the owner; plan-cache actor isolation stays with standing Scenario 2). Worker-0 mechanical checks pass (post-fix digests 799139be/5aae2be4 == worktree; item diff vs 2db65089 exactly the 2 files; probes on disk with WS pins; counts/controls/reach stated; neighbors unmoved; ruff + trailing-commas + banned-token scan clean; PG/sharded/async-over-Channels listed unverified). Report recovered verbatim to `/tmp/w1-querysets-r1-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-querysets-verify, expectation-first.
    - Iteration: 3. Worker 2 verified Fixed Low (expectation-first `hunt-ws/w2-utils-querysets-expectation.txt`, E1–E8, written before opening the W1 report/test bodies/probes): 5/5 permanent tests green post-fix; WS-only 2-line revert → 5/5 raw-fail (`RuntimeError: name-boom` ×4 incl. both honest paths, `format-boom` ×1 proving `__format__` dispatch pre-fix), restored cmp-identical; W1 battery replayed 154/154 (count slip reconciled: 154 true, header "152" the slip); 32/32 independent attack probes green (non-str names degrade, dunder counters 0, raising incl. BaseException/KI/SI degrade, async hostile-format + SyncMisuseError disposal, both sidecar entries, extremes byte-identical; one own probe-label bug corrected); honest message cmp-identical; positive control (neutered `_safe_class_name`) biting, restored identical; oracles 339/339 + 428/428 + known-red only; all three lint gates clean. Owner/tier/Low concurred; all 4 robustness rows agreed (R2 with an infeasibility-overstatement note, conclusion holds); changed-lines PG/sharded judged inapplicable by construction, pipeline-level cells stay unverified. Adjacent lead routed out (non-blocking, different owner): `orders/sets.py` `_NormalizationLedger.claim` + 2 purity-check arms raw `__name__` escape characterized in-WS → that item stale for a narrow re-pass; `filters/sets.py` similar unprobed reads → its existing stale re-pass scope. Folded by Worker-0 from the verdict (recovered verbatim to `/tmp/w2-querysets-verify-report.txt`); digests 799139be/5aae2be4 re-confirmed == worktree.
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/querysets.py (2 `_safe_class_name` label swaps in `_apply_sidecar_sync`/`_apply_sidecar_async`) + tests/utils/test_querysets.py (5 hostile-set-name tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-querysets-expectation.txt. Evidence: hunt-ws/utils-querysets-verify/ records, post-fix digests 799139be/5aae2be4.
    - Cleanup: Removed hunt-ws/utils-querysets-r1, hunt-ws/utils-querysets-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 4. Fresh Worker 1 dispatched 2026-09-22 17:33 UTC, ITEM_BASELINE c9e39d31, workspace hunt-ws/querysets-stale-r1; target 799139be + tests/utils/test_querysets.py 5aae2be4 re-confirmed == c9e39d31 blobs (item diff empty; unchanged since verification). Narrow scope per the Stale note: (a) the walker-D1 `_LIST` reject_combined seam — hook-returned union/intersection/difference on plain-list relations escaping raw instead of the sealed typed `ConfigurationError` — RE-DERIVE on current bytes with own contract rows + probes before any edit (W2 evidence: live L1/B2/B3; W1 prescription advisory only; prose trap + unpinned matrix + O3 oracle reckoning ride along); (b) the `_DEFAULT` extension (L4/L5): confirm-or-disprove AND REPORT, must NOT flip `_DEFAULT` without Rio (recorded Rio decision — the flip simulation showed 2 premise-pin failures + Decision-8 ripple). Prior verdict stands for all else; attribution-first. Evidence paths: /tmp/w1-walker-stale-r1-report.txt + /tmp/w2-walker-stale-report.txt + hunt-ws/w2-walker-stale-expectation.txt (walker workspaces were consumed at closeout — re-derive from text on current source).
    - Iteration: 5. Prior narrow W1 dispatch (Iteration 4, baseline c9e39d31, workspace hunt-ws/querysets-stale-r1) died with the Worker-0 session 2026-09-22 17:39 UTC before reporting (~5 min of work, no probes on disk — nothing to retain); workspace deleted by explicit path. Fresh Worker 1 dispatched 2026-09-22 17:41 UTC, ITEM_BASELINE 785953ca, workspace hunt-ws/querysets-stale-r2; target 799139be + tests/utils/test_querysets.py 5aae2be4 re-confirmed == 785953ca blobs (item diff empty; unchanged since verification; baseline re-minted because the worktree tree moved past c9e39d31 via verified landings + maintainer edits). Same narrow scope as Iteration 4: (a) the walker-D1 `_LIST` reject_combined seam — RE-DERIVE on current bytes with own contract rows + probes before any edit (W1 prescription advisory only; prose trap + unpinned matrix + O3 oracle reckoning ride along); (b) the `_DEFAULT` extension: confirm-or-disprove AND REPORT, must NOT flip `_DEFAULT` without Rio. Same evidence paths; prior verdict stands for all else; attribution-first.
    - Iteration: 6. Worker 1 stale re-pass reported Fixed Low (D1 `_LIST` combinator-seal escape CONFIRMED with own rows R1-R8 + 44-probe battery before editing: hook-returned union/intersection/difference passed `reject_combined=False`, then escaped raw `NotSupportedError` plan-time via the child plan's `.only()` at `plans.py::apply:298` (0 queries) or fetch-time via Django's refilter (1 parent SELECT); fix is the one behavior line `reject_combined=True` on `_LIST_RELATION_CHILD_POLICY` + 5 probed-true prose restatements; `_PREFETCH` keeps admitting per the R4 gate classification) + `_DEFAULT` extension CONFIRMED (9-surface census: optimizer-dependent L4/L5 RAW, optimizer-independent node/derive/locate/decode RAW, admittable surfaces serving rows; S2 flip simulation exactly 2 premise-pin failures + Decision-8 collapse) AND REPORTED, NOT flipped per the recorded Rio decision + 3 permanent tests (5 nodes: parametrized seal refusal, hook-naming runner refusal negating the old sentence, hostile-`__name__` degradation; tier `tests/` — no combinator-hook fakeshop fixture exists, live unreachable without a new example model) + preset-matrix pins closing both unpinned cells + 5298 pin rewording. Files changed: utils/querysets.py (e0b0651a) + tests/utils/test_querysets.py (c82e77c6). Worker-0 mechanical checks pass (item diff vs 785953ca exactly the 2 files, 118+/25-; digests match; collection 44 exact; 10/11 probe sha256 pins match — q00 differs post-pin, current bytes correct for r2, flagged for W2; pristine restore source matches the 799139be blob; simulated tests byte-identical to landed; no strays; reach markers in all probes; ruff check + format --check + trailing-commas + banned-token scans clean — re-run by Worker-0; no new pragma; failability claimed C1 (exactly 2 red) + C2 (6/6 red `DID NOT RAISE`) for W2 to re-prove; floor executed both cells, sharded/PG + async-Channels honestly unverified; F5 pre-existing reds named). Follow-ups ride for W2 judgment: F1 walker.py:427-429/:459-460 prose now false (two axes) — W1 says prose-only, no behavior-stale; F3 preserved-false-clause (the "cannot take [a slice] after ordering" sentence kept in the `reject_combined` bullet despite Q-probed order+slice serving rows) — acceptability; F4 order-by-expression raw `TypeError` inside Django — needs own contract row. Report /tmp/w1-querysets-stale-r2-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/querysets-stale-verify, expectation-first.
    - Iteration: 7. Worker 2 verified (expectation-first `hunt-ws/w2-querysets-stale-expectation.txt` 5f43be5d, E1-E12: zero contradiction on E1-E5/E7-E9, E6 honestly flipped to W1's position by the no-dependence grep + digest mechanics, E10-E12 resolved by probe): fresh-WS replay 44 collected = 30 green + the predicted 13 + q00 literal (same dispensation as prior items, intent re-verified by own prints); WS-only flag revert re-proves C2 6/6 red + battery 42/44, restored sha-identical; C1 resolved as prose-half neuter (precisely the 2 wording pins red, own first-attempt over-count corrected); 126-node attack battery green BOTH cells (7x3 seal matrix incl. skipped `_RAW_LIST_SOURCE`, code-order pins, cross-model `table` precedence, async runner, `_build_child_queryset` 0-query refusal, R4-live e2e closing the admission premise with exact rows, ladder-verb matrix x3 x2cells, F4 Lower/Case raw `TypeError` x3 x2cells with hook-pre-ordered reaching input x6, `_DEFAULT` intersection re-derivation, honest byte-identity, S2 re-derived exactly); owner/tier/Low concurred (live challenge attempted and closed: zero fakeshop combinator hooks, new example model forbidden in-item); F1 judged prose-only follow-up, NO behavior-stale (W1's "walker behavior untouched" loose but outcome right — the change IS the intended routed fix); F3 judged acceptable with reason (pre-existing false-on-its-own-date sentence, true replacement needs unpinned rows HUNT.md forbids fixing without cited rows, partial fix worse; one family card advised); F4 standing CONFIRMED within deferred scope (README:395 row + feasible hook + reaching input, all 3 combinators x both cells — same `_DEFAULT` class, new compile-time shape, rides Rio's decision, extends the census); O3 reckoning correct, no oracle change owed; prose-trap handling correct and required (cascade always own renderer; `_DEFAULT` doc-slip fix corrects a false-since-birth line); item diff exactly the 2 files, `_DEFAULT_SEAL_POLICY` 0 changed lines + runtime admission re-proven; ruff clean; `plan` hits OptimizationPlan domain vocab; floor executed (126/126 + identical split + byte-identical matrix); sharded/PG + async-Channels `unverified` judged correct. Report /tmp/w2-querysets-stale-report.txt; shared tree untouched by W2 (digests unchanged throughout).
    - Result (stale re-pass): Fixed Low. Files changed: django_strawberry_framework/utils/querysets.py (`reject_combined=True` on `_LIST_RELATION_CHILD_POLICY` + 5 prose restatements) + tests/utils/test_querysets.py (3 tests, 5 nodes + preset-matrix pins + 5298 rewording). `_DEFAULT` 9-surface census CONFIRMED and REPORTED, not flipped (recorded Rio decision; F4 extends the census within deferred scope).
    - Verification (stale re-pass): Passed. Expected-before-diagnosis: hunt-ws/w2-querysets-stale-expectation.txt. Evidence: hunt-ws/querysets-stale-verify/ records (qs2 replay + w2/ battery), post-fix digests e0b0651a/c82e77c6.
    - Cleanup (stale re-pass): Removed hunt-ws/querysets-stale-r2, hunt-ws/querysets-stale-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - Iteration: 8. Behavior change recorded (review 5d, W2-challenged): the "combined" message reworded on the list-argument surfaces (message-only; no predicate change claimed — challenger to verify no behavioral delta rides with the reword). Verdict pending.
    - Iteration: 9. Worker 2 product-semantics challenge on the `_visibility_result_error` "combined" arm reword (Q1-Q3, workspace hunt-ws/5d-querysets-verify): verdict (a) CONCUR — reword stands. Q1: old/new texts reproduced verbatim on L1-L4 + runners + direct render, both eras; pins 7/7 post, 6 failed + 1 passed pre. Q2: no-delta PROVEN — co_code identical both eras, exactly one differing const (the message literal); 13 honest inputs byte-identical (sqlsha + row pks); error class stable; old-text caller census zero affirmative matchers (one negation pin). Q3: no contract row pins prose; old sentence false on C1; keep-old-text named and declined. Shared tree never edited (fences re-hashed; fence-vs-b38957c6 empty). Report: hunt-ws/reports/w2-5d-querysets-report.txt. Workspace + expectation file removed. Item stays verified.
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/querysets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/relations.py
    - Status: verified
    - Stale 2026-09-22 (digest-driven, comment-only drift): recorded 1cf81e58 (incl. the concurrent DRY hunk, untouched at verify), worktree 8ec60c33; delta vs recorded is exactly main's `instance_accessor` docstring hunk (ae52bdec fast-forward), reverse-apply proven byte-exact. Prior verified verdict stands for the old digest only. Bounded Worker 2 re-verification on the diff queued (order 6c).
    - ITEM_BASELINE: `9b0dc6ad2772b657ec6b7af90bbc0cf60c07f98d`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/utils-relations-r1; target worktree digest 1cf81e58 vs HEAD 7662b0bb — the delta is exactly the concurrent DRY docstring hunk (+14 "Four other _meta path walkers", `classify_path` docstring; verified by Worker-0 via `git show HEAD`), never hunt's: hunt reads the worktree bytes, attributes-first, and never touches that hunk. tests/utils/test_relations.py digest b82f9cc1, clean vs HEAD.
    - Iteration: 2. Worker 1 reported No bugs (12 contract rows R1–R12; 185-probe battery green with REACHED/agreement assertions; both cells EXECUTED — floor 3.10.19/Django 5.2.17 offline-built + ceiling 3.14.2/6.1, each 311 passed incl. the 126 oracle; 62-path cross-version agreement battery; unique-reverse-FK proved correct two ways incl. real rows; LRU bound + discriminating cache-clear pinned; 3 WS-only mutation controls biting exactly, restored sha256-identical; 6 candidates disproved; 3 robustness rows without fix incl. a test-gap observation left untouched). Zero shared-tree edits. Worker-0 mechanical checks pass (target still exactly the +14 DRY hunk, untouched; tests clean; item diff empty; 10 probe files on disk; counts/controls/reach stated — 58 test defs parametrized to 185 nodes, W2 to reconcile exact collection; floor cell executed, PG row-shape unverified, taxonomy inapplicable-by-construction with grep proof). Report recovered verbatim to `/tmp/w1-relations-r1-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-relations-verify, expectation-first.
    - Iteration: 3. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-relations-expectation.txt`, written after reading the target + exceptions + all 13 callers + oracle + docs sweep, before opening the W1 report/probes): W1 battery replayed 185/185 + oracle 126/126 (count reconciled: 58 defs → 185 collected, 311 combined — W1's numbers exact); 42 independent attack probes green (opposite extremes incl. m2m short-circuit order, tuple/mixed path_infos, to_field both legs, composite bare-pk, whole-fixture sweep, 4-thread clear-storm; one own probe bug fixed and kept as a vocabulary pin); two WS-only controls with exact signatures (R9 gate inversion → 2 True-arm reds; cache-clear neuter → W1 probe red + oracle green, first-hand proof of the test-gap observation), restored cmp-identical; floor cell EXECUTED here too (offline-built 3.10.19/5.2.17: full 353 passed, incl. the 62-path agreement battery green both cells). All 6 disproved + 3 robustness rows agreed evidence-backed; inapplicable axes/cells judged SOUND per surface; PG row-shape stays unverified; DRY hunk still exactly +14, untouched. Folded by Worker-0 from the verdict (recovered verbatim to `/tmp/w2-relations-verify-report.txt`); target 1cf81e58 + tests b82f9cc1 re-confirmed.
    - Iteration: 4. Worker 2 bounded drift re-verification (criteria K1-K5, mini-expectations before runs; workspace hunt-ws/relations-drift-verify): K1 recorded bytes reconstructed in-WS + 1cf81e58 reproduced byte-exact, sole delta `instance_accessor` docstring :717-719 (-2/+3), DRY +14 proven byte-identical in both eras and absent from both base blobs, three-way attribution complete (worktree-vs-HEAD = DRY only; worktree-vs-recorded = docstring only; recorded-vs-5ee86193 = DRY only), no fourth category; K2 behavior-null via sound method (naive AST honestly differs as warned; docstring-normalized AST identical sha256 + 26 code objects identical co_code/names/varnames/non-str-consts with only the one docstring const differing + firstlineno shifts line-table-only below the delta) + both compile/import + zero observability hits; K3 126/126 oracle green both trees at 8ec60c33/b82f9cc1 (scratch batteries confirmed removed per Cleanup, DRY gate none named); K4 Control A replayed with the exact recorded signature (2 reds at :1086/:1150, 124 green) + cmp-identical restore + 126/126; K5 3 gates clean + fence-vs-ITEM 0 bytes + drift docstring judged timeless, provenance-free, source-verified accurate (three example models confirmed lacking related_name), contract-free. Verdict: verified, prior No-bugs verdict stands at 8ec60c33. No new ledger row (re-proof, no change).
    - Result: No bugs. Evidence: W1 battery + 3 controls + dual-cell oracles; W2 replay + 42 attacks + 2 controls + executed floor cell. Target digest 1cf81e58.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-relations-expectation.txt. Evidence: hunt-ws/utils-relations-verify/ records.
    - Cleanup: Removed hunt-ws/utils-relations-r1, hunt-ws/utils-relations-verify; drift re-proof removed hunt-ws/relations-drift-verify; expectation file + drift report retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/sessions.py
    - Status: verified
    - ITEM_BASELINE: `430faa880b1db34d126ebc38013a779970d67004`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/utils-sessions-r1; target digest f0d9297c, clean vs HEAD; tests/utils/test_sessions.py digest eba7df50, clean vs HEAD.
    - Iteration: 2. Worker 1 died by infra failure 2026-09-22 (child run failed, no report, no verdict — not evidence of anything); shared tree untouched (target f0d9297c + tests eba7df50 == HEAD; item diff empty). Orphaned `hunt-ws/utils-sessions-r1/` (WS copy built, no probes directory — died before probing) retained as UNVERIFIED orientation (re-derive every conclusion; removed with the item at completion). Fresh Worker 1 dispatched, ITEM_BASELINE b934257d, workspace hunt-ws/utils-sessions-r2; re-derive everything.
    - Iteration: 3. Worker 1 (r2) reported Fixed Low, one defect D with 7 triggers: hostile/masquerading `SESSION_ENGINE` escaped raw where R4/R5 promise `ConfigurationError` — the flatten ran after the emptiness check and the `isinstance` gate + flatten were unguarded (raising `__bool__`/`__len__` → raw `RuntimeError` at `if not engine:`; `__class__`-liar → raw `TypeError` at `str.__str__`; raising `__class__` → raw `RuntimeError` at `isinstance`; lying-`True` empty subclass → wrong typed arm). Fix at the owner: guarded `isinstance` (typed arm on raise) + flatten BEFORE the truthiness check + guarded flatten (liar → non-string arm), mirroring the verified `utils/policies.py::resolve_policy` precedent + widened docstring + 8 permanent tests in tests/utils/test_sessions.py tier `tests/` (7 fail pre / pass post + 1 benign-subclass pin green both eras). Evidence: 12 contract rows R1–R12; 76/76 probes green; red logs with tracebacks + honest `cmp` (modulo addresses) + revert/promoted red proofs + PC1/PC2/PC3 biting with sha256-identical restores; oracles 188 + 34 + 63 green pre+post; shared focused 29/29; module 100% (80/0) with owning files; ceiling 3.14 + floor 3.10 both executed. 6 disproved + 7 robustness rows without fix. Worker-0 mechanical checks pass (post-fix digests 54c41be7/42a8d631 == worktree; item diff vs b934257d exactly the 2 files; probes + logs on disk with WS pins; counts/controls/reach stated; neighbors unmoved incl. concurrent strings dirt correctly attributed by W1; ruff + trailing-commas + banned-token scan clean; PG/sharded inapplicable-by-construction reasoned). Report recovered verbatim to `/tmp/w1-sessions-r2-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-sessions-verify, expectation-first.
    - Iteration: 4. Worker 2 verified Fixed Low (expectation-first `hunt-ws/w2-utils-sessions-expectation.txt`, E1–E15, written before opening the W1 report/probes/logs/tests): post-fix replay 138/138 (29 permanent + 75 W1 probes + 34 new W2 attacks); WS-only revert → 8 permanent 7-fail-intended (4× raw `RuntimeError` bool/len, 1× `TypeError` liar, 1× `RuntimeError` isinstance, 1× wrong-arm) + pin green both eras, restored cmp-identical (sha256 1aeeb588 matches W1); attack red-subset fails pre-fix as predicted (incl. session-aborting `KeyboardInterrupt`; revoke holds 4/4 pre-fix — containment predates the fix, confirming severity); oracles 196 + 99 + 212 green (W1's "188 pre+post" corrected: 188 pre → 196 post with the 8 new; full files supersede the `-k` subsets); module 80/0/100%; floor 3.10 re-executed 63/63 (`-S` isolation defeating the floor venv's W1-pointing hook); all 7 robustness rows + 6 disproved candidates agreed evidence-backed; owner/tier/Low concurred (zero `SESSION_ENGINE` refs in fakeshop — wire-unreachable); all 3 lint gates + prose clean; PG/sharded inapplicable-by-construction verified against the surface; known-red never in selection. Folded by Worker-0 from the verdict (recovered verbatim to `/tmp/w2-sessions-verify-report.txt`); digests 54c41be7/42a8d631 re-confirmed == worktree.
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/sessions.py (guarded `isinstance` gate + flatten-before-truthiness + guarded flatten in `session_store_class` + widened docstring) + tests/utils/test_sessions.py (8 engine-shape tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-sessions-expectation.txt. Evidence: hunt-ws/utils-sessions-verify/ records, post-fix digests 54c41be7/42a8d631.
    - Cleanup: Removed hunt-ws/utils-sessions-r1, hunt-ws/utils-sessions-r2, hunt-ws/utils-sessions-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved (`hunt-ws/floor-310/` shared floor-testbed kept — read-only testbed, not this item's scratch).
    - docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/strings.py
    - Status: verified
    - Lead 2026-09-21 (from the inputs hunt, probed as unreachable-via-that-module): `_plain_text` unguarded `isinstance` (evidence in `hunt-ws/utils-inputs-r1/probes/test_ui_21_hostile_labels.py`, re-derive on current source). Assess at this owner when hunted.
    - ITEM_BASELINE: `11e859a1c17274e557524b8cbeca16d3b66b35b3`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/utils-strings-r1; target digest 3ec3b262, clean vs HEAD; tests/utils/test_strings.py digest 3dad1a9d, clean vs HEAD. Carries the inputs-hunt `_plain_text` lead above (assess at this owner with contract rows; the cited WS was removed at the inputs close — re-derive on current source).
    - Iteration: 2. Worker 1 reported Fixed Low, one defect D1 (the lead, confirmed on current source with fresh probes): `_plain_text`'s unguarded `isinstance` + unguarded `str.__str__` normalization — a `__class__`-spoof (`isinstance` True, then `TypeError` from the base slot) and a raising `__class__` (raw `RuntimeError`) escaped instead of the R1 typed `ConfigurationError`; all 5 helpers affected. Fix at the owner (+19/-3): both reads guarded with `except Exception … from exc` raising the existing typed message via spoof-proof `_safe_type_name` (KI/SI propagate — pinned) + 4-line contract docstring + 4 permanent tests in tests/utils/test_strings.py tier `tests/` (spoof ×4, raising ×4, or-raise ×1 incl. factory-never-runs, KI-propagation ×4; 13 nodes). Evidence: 8 contract rows R1–R8 (R4 pins `pascal_case` acronym-lowering/idempotence-absence as designed); 9331-name round-trip corpus + injectivity + 1296-name uppercase corpus + unicode/10k extremes green pre+post; hostile mega-subclass green; WS battery 133 passed; failability 9 red raw pre → green post with `cmp`-identical restores; M1/M2 controls biting exactly; live oracle 9/9 both ways; module coverage 76/1 with the 1 miss pre-existing (other-tier all-underscore arm, also missed on pristine); floor 3.10 logic executed identical. 5 disproved/robustness rows without fix (incl. C3 `make_error`-argument shape carded to `sets_mixins.py::type_name_for` if ever, fence respected). Worker-0 mechanical checks pass (post-fix digests ffa4fee0/77109707 == worktree; item diff vs 11e859a1 exactly the 2 files; probes on disk with WS pins; counts/controls/reach stated; neighbors unmoved; ruff + trailing-commas + banned-token scan clean; PG/sharded/async inapplicable-by-construction reasoned, floor executed). One report slip corrected by Worker-0 (not bounced — all bytes accounted for): the 6 stated probe digests are rotated one label off actual (true mapping: test_00_env a079aca9, s01 418ae0e6, s02 a053bca5, s03 2834b7f3, s04 08fcf538, floor_310 3f75d864) — W2 replays from disk and re-hashes. Report recovered verbatim to `/tmp/w1-strings-r1-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-strings-verify, expectation-first.
    - Iteration: 3. Worker 2 verified Fixed Low (expectation-first `hunt-ws/w2-utils-strings-expectation.txt` digest 7d562e05, E1–E14, written before opening the W1 report/probes/test bodies): 54/54 green post-fix; WS-only pristine revert → 9 fail raw (spoof `TypeError`, raising `RuntimeError`, or-raise; 4 KI pass both ways), restored cmp-identical; W1 battery replayed 133 with the Worker-0-corrected probe digests CONFIRMED (W1's labels rotated one off); live 9 + 9 identical; 39-node attack battery green (novel liar shapes: class-attr `__class__`, str-subclass answer, `__getattribute__` spoof/raising, non-type answers, genuine-subclass-with-lying-class converting correctly, SystemExit code intact, hostile `__str__` cause, fast path, factory identity + SystemExit + None-fault, cache sharing, hostile-hash-never-hashed, 256-byte totality, second-alphabet 1555 corpus, flatten 100k); positive control (first guard → `except ValueError`) fails exactly the 9 raising-shape nodes, restored identical → 172 combined green; floor 3.10.19 re-executed by W2 (`FLOOR-3.10-LOGIC OK`); coverage fixed 76/1@237 = pristine 69/1@221 shifted, miss covered other-tier (focused+orders 100%, 102 passed); owner/tier/Low concurred; all 5 robustness rows agreed with evidence (C3 owner `sets_mixins.py::type_name_for` verified: bare `{bad!r}` line 117 vs filters' safe line 263); all 3 lint gates clean; inapplicable cells judged against the real import surface. One non-blocking observation: a W1 scratch comment's exponent list off by one (asserted count correct; scratch-only). Folded by Worker-0 from the verdict (recovered verbatim to `/tmp/w2-strings-verify-report.txt`); digests ffa4fee0/77109707 re-confirmed == worktree.
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/strings.py (D1 guarded `isinstance` + `str.__str__` reads in `_plain_text` + contract docstring) + tests/utils/test_strings.py (4 liar tests, 13 nodes).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-strings-expectation.txt. Evidence: hunt-ws/utils-strings-verify/ records, post-fix digests ffa4fee0/77109707.
    - Cleanup: Removed hunt-ws/utils-strings-r1, hunt-ws/utils-strings-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/strings.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/typing.py
    - Status: verified
    - ITEM_BASELINE: `1bee00f93ee8a5e95f393dd50efdb5e7c83002ae`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/utils-typing-r1; target digest de6309f6, clean vs HEAD; tests/utils/test_typing.py digest 70a257a1, clean vs HEAD.
    - Iteration: 2. Worker 1 reported No bugs (7 contract rows R1–R7; 71-node battery green on ALL FIVE interpreters 3.10–3.14 with a 42-cell vector agreement — sole real divergence `partialmethod→True` on 3.13+ unreachable, all seams reject typed first; feasible-shape E2E over real `DjangoListField` + real documents both transports; lazy-proxy lead disproved; TOCTOU closed; depth edges pinned; 3 WS-only mutation controls biting exactly, restored `cmp`-identical vs shared tree; oracles 42+14+41+17+30+2+78 green; one fix considered and rejected per HUNT — containment no row promises). Zero shared-tree edits. Worker-0 mechanical checks pass (target + tests == HEAD; item diff empty; w1-probes on disk with env anchor + 5 vectors; counts/controls/reach stated; inapplicable cells reasoned; known-red avoided). Report recovered verbatim to `/tmp/w1-typing-r1-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-typing-verify, expectation-first.
    - Iteration: 3. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-typing-expectation.txt` digest 2e41ff2c, written before opening the W1 report/probes): W1 battery replayed 71/71 on ALL FIVE interpreters; 5/5 vectors re-executed identical; oracle 42/42 (3.14 + 3.10); independent 53-node attack green on 3.14 + 3.10 (33-shape ground-truth matrix incl. opposite extremes W1 never tried; partialmethod divergence closed at BOTH ends with mechanism pinned to upstream `inspect` + typed rejection proved at all three seams on both verdict ends — connection factory new; ordering proof at both factories; storage audit re-done with counting-probe pin; two-cycles loud; 65-finite infeasibility evidenced via graphql-core's own assert; R5 domain locked with the `of_type`-beats-list clause defensive-only); positive control (R7 flip) exactly 2 red, restored cmp-identical; one invalid run discarded en route (vectors imported W1's WS package without PYTHONPATH — rerun correctly). All disproved candidates + the rejected-containment-fix ruling agreed; inapplicable axes/cells agreed by source audit; NO unverified cells; known-red named in the list-field oracle run, not chased. Folded by Worker-0 from the verdict (recovered verbatim to `/tmp/w2-typing-verify-report.txt`); target de6309f6 + tests 70a257a1 re-confirmed == HEAD.
    - Result: No bugs. Evidence: W1 battery + 3 controls + multi-cell oracles; W2 replay + 53 attacks + control + re-executed vectors. Target digest de6309f6.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-typing-expectation.txt. Evidence: hunt-ws/utils-typing-verify/ records.
    - Cleanup: Removed hunt-ws/utils-typing-r1, hunt-ws/utils-typing-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/typing.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/write_transaction.py
    - Status: verified
    - ITEM_BASELINE: `f925a39ec55fb524bafbae9ca013dafdf13d9ce1`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/utils-write-transaction-r1; target digest eca9ad4d, clean vs HEAD; nearest suite tests/mutations/test_write_transaction.py digest 56cb20e4, clean vs HEAD. Standing Scenario 3 (transaction/session lifecycle under interruption) is still pending — hunt the file item fully; name any cross-file contract found lacking a scenario so Worker 0 can append it.
    - Iteration: 2. Worker 1 reported Fixed Low, one defect D1 at 5 typed seams (R1–R5): raw `__name__` escapes — `:215` `mutation_cls.__name__`, `:516` `sender.__name__`, `:687` `queryset.model.__name__`, `:710` `model.__name__`, `:1085` `type(instance).__name__`. Feasibility proven: hostile-named mutations register by design; EvilStr-`__name__` models survive Django construction (`object_name` stores the subclass) and detonate at all four model seams via public API (raising-`__name__` models die inside Django's own construction — infeasible, robustness). Fix at the owner: `_safe_class_name` at all 5 + import (6 hunks, honest-identical degraded labels) + 5 permanent tests in tests/mutations/test_write_transaction.py tier `tests/` (producer-authored metaclasses wire-unreachable). Evidence: 12 contract rows R1–R12; battery 71/71 green; 5/5 fail pre → pass post across a WS-only revert, restored `cmp`-identical; neighbors 566 + 265 green; M1/M2 controls biting with byte-identical restores; shared focused 5/5. 8 robustness rows without fix (incl. disarm-failure masking characterized, fingerprint `__format__` trust-boundary exclusion). No new scenario (cross-file contracts found fall inside pending Scenario 3). Worker-0 mechanical checks pass (post-fix digests 9ad493b6/7a29fb80 == worktree; item diff vs f925a39e exactly the 2 files; probes on disk with WS pins; counts/controls/reach stated; neighbors unmoved; ruff + trailing-commas + banned-token scan clean; PG/sharded unverified, floor unexecuted with reason, label cells inapplicable-by-construction for W2 to judge). Report recovered verbatim to `/tmp/w1-write-transaction-r1-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-write-transaction-verify, expectation-first.
    - Iteration: 3. Worker 2 verified Fixed Low (expectation-first `hunt-ws/w2-utils-write-transaction-expectation.txt` digest a89008d9, written before opening the W1 report/probes/tests): 5/5 green post-fix; WS-only revert → 5/5 raw-fail (`RuntimeError` hostile/format escapes), restored cmp-identical; 49-probe attack battery green (5 seams × 6 hostile-name shapes incl. None/empty/non-str/str-only/hostile-`__eq__` W1 never tried; honest template-exact + pristine byte-parity side-by-side; guard phase matrix; conflict/fingerprint/lock/read-surface extremes); positive control (one-seam revert) biting exactly, restored identical; floor-3.10 cell EXECUTED 5/5 (W1's reason judged sound + now run); oracle file 68/68 + neighbors 566/566; known-red confirmed red once, not chased; all 3 lint gates clean. Owner/tier/Low concurred (all 6 + 1 call sites audited — no bypass; out-of-fence note on `rest_framework/resolvers.py` relation-mismatch labels routed to that owning item, no action); all 8 robustness rows agreed with two-interpreter grounding (incl. `NotUpdated`-trap inert-on-6/raw-on-5.2-only); label cells inapplicable-by-construction concurred, PG barrier + PG `FOR UPDATE` stay unverified. Folded by Worker-0 from the verdict (recovered verbatim to `/tmp/w2-write-transaction-verify-report.txt`); digests 9ad493b6/7a29fb80 re-confirmed == worktree.
    - Result: Fixed Low. Files changed: django_strawberry_framework/utils/write_transaction.py (import + 5 `_safe_class_name` label swaps) + tests/mutations/test_write_transaction.py (5 hostile-name tests).
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-write-transaction-expectation.txt. Evidence: hunt-ws/utils-write-transaction-verify/ records, post-fix digests 9ad493b6/7a29fb80.
    - Cleanup: Removed hunt-ws/utils-write-transaction-r1, hunt-ws/utils-write-transaction-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_transaction.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/write_values.py
    - Status: verified
    - ITEM_BASELINE: `f46bd1f488b19e9189e15fecdf034ff1571bba9f`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/utils-write-values-r1; target digest d28587c7, clean vs HEAD; tests/utils/test_write_values.py digest 8d09921b, clean vs HEAD.
    - Iteration: 2. Worker 1 reported No bugs (8 contract rows R1–R8; 67-probe battery green with REACHED/`*-OUT` lines; 3 mutation controls biting red-for-reason with sha256-identical restores; oracles 317 package + 7 live green; floor 3.10 cell 29 green via the shared testbed read-only; 4 liar shapes reproduced with armed instruments and ruled robustness — no promised row, no reaching wire input, container always plain `list`; prose-drift + scale + BaseException rows disproved/characterized without fix; one out-of-fence observation on a verified item, no action). Zero shared-tree edits. Worker-0 mechanical checks pass (target + tests == HEAD; item diff empty; probes on disk with WS pins; counts/controls/reach stated; all 8 connected digests match worktree — no drift; PG/sharded/async-transport unverified; known-red avoided). Report recovered verbatim to `/tmp/w1-write-values-r1-report.txt` (delivery truncated). Fresh Worker 2 dispatched, workspace hunt-ws/utils-write-values-verify, expectation-first.
    - Iteration: 3. Prior W2 dispatch died on provider error after writing a partial expectation file (hunt-ws/w2-utils-write-values-expectation.txt, UNVERIFIED — the fresh verifier must never open it); its partial workspace hunt-ws/utils-write-values-verify is retained as orientation only. The W1 r1 No-bugs verdict + passed mechanical checks stand (report /tmp/w1-write-values-r1-report.txt, probes hunt-ws/utils-write-values-r1/probes/). Fresh Worker 2 dispatched 2026-09-22 ~08:45 (W2 only, no new W1), ITEM_BASELINE 3c00404f, workspace hunt-ws/utils-write-values-verify2, expectation file hunt-ws/w2-utils-write-values-expectation-r2.txt; target d28587c7 + tests 8d09921b re-confirmed == HEAD.
    - Iteration: 4. Worker 2 verified No bugs (expectation-first `hunt-ws/w2-utils-write-values-expectation-r2.txt`, R1-R8 + falsifiers, written before opening the W1 report; dead predecessor files never opened): fresh-WS replay 66 behavioral green (test_00 path pin fails by design with isolation pins proving verify2) + oracles 317/317 + live 7/7; 47 independent attacks green on ceiling + floor re-executed; 2 own biting controls restored sha256-identical (52520eeb matches W1 pristine); all candidate/robustness rulings agreed with own armed instruments; axis-5 re-proved inapplicable; PG/sharded/async stay unverified; item diff empty (checked 3x); all 10 digests match; ruff gates clean.
    - Result: No bugs. Evidence: W1 battery + 3 controls + oracles + floor; W2 replay + 47 attacks + 2 controls + floor re-executed. Target digest d28587c7.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-utils-write-values-expectation-r2.txt. Evidence: hunt-ws/utils-write-values-verify2/ records.
    - Cleanup: Removed hunt-ws/utils-write-values-r1, hunt-ws/utils-write-values-verify, hunt-ws/utils-write-values-verify2, and the dead partial hunt-ws/w2-utils-write-values-expectation.txt; r2 expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/views.py
    - Status: verified
    - ITEM_BASELINE: `22ca1f8f6b504d7cb79752717a292a4b8f8a2317`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22, workspace hunt-ws/views-r1; target digest 9f85b0df, clean vs HEAD; tests/test_views.py digest 4dc9a257, clean vs HEAD. Last pending file item (pending queue now empty).
    - Iteration: 2. Prior W1 dispatch (baseline 22ca1f8f, workspace hunt-ws/views-r1) died on provider error with no report; its partial workspace (incl. nested hunt-ws recursion bloat) is retained as UNVERIFIED orientation only. Fresh Worker 1 dispatched 2026-09-22 ~08:45, ITEM_BASELINE 3c00404f, workspace hunt-ws/views-r2; target 9f85b0df + tests 4dc9a257 re-confirmed == HEAD. Re-derive everything; exclude hunt-ws from the workspace copy.
    - Iteration: 3. Worker 1 (r2) reported No bugs (12 contract rows R1-R12; 58-probe battery green on ceiling + floor via the shared testbed; oracles 208 package both cells + 97 live with 3 pre-existing 3.14 fixture errors reproduced identically in shared tree; 3 biting WS-only controls restored sha256-identical; 8 candidates disproved/characterized with 3 robustness rows). Zero shared-tree edits. Worker-0 mechanical checks pass (item diff empty; all 7 digests match; probe digests on disk; no nested hunt-ws; 28+8 defs; REACHED log captured; PG/sharded inapplicable-by-construction for W2 to judge; one count slip flagged: intermediate 57 floor run and run-4 7-node F-file vs final 58 = 50 + 8 — W2 reconciles exact collection from disk). Report /tmp/w1-views-r2-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/views-verify, expectation-first.
    - Iteration: 4. Prior W2 dispatch (workspace hunt-ws/views-verify) died on provider 429 with the Worker-0 session 2026-09-22 05:11 before reporting; its partial workspace is retained as UNVERIFIED orientation only and its partial expectation file is never to be opened. Fresh Worker 2 dispatched 2026-09-22 14:14 UTC, ITEM_BASELINE 706f2219, fresh workspace hunt-ws/views-verify2 + fresh expectation file, expectation-first; W1 r2 report still on disk, mechanical checks PASS per Iteration 3, count slip still flagged for reconciliation.
    - Iteration: 5. Worker 2 verified (expectation-first `hunt-ws/w2-views-expectation.txt`, written before opening the W1 report; dead workspaces never opened): fresh-WS replay 58/58 ceiling + floor (one WS-only test_00 path-literal edit, shared probes untouched); oracles 208/208 + 97 live with the 3 pre-existing 3.14 fixture errors reproduced identically in shared tree; 37/37 independent attacks both cells; guard-neutering mutation failed 11 oracle + 8 probe rows `DID NOT RAISE`, restored cmp-identical; both count slips reconciled exact from disk (W1 "P02x17" a report typo summing to 54 vs its own 50; run-4 7-def F-file + intermediate 57 = same pre-final state); PG/sharded judged inapplicable-by-construction (full-file read + AST scan); item diff empty; ruff clean.
    - Result: No bugs. Evidence: W1 r2 58-probe battery green ceiling + floor + oracles 208 + 97 live; W2 replay + 37 attacks + biting control, count slips reconciled exact.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-views-expectation.txt. Evidence: hunt-ws/views-verify2/ records, target digest 9f85b0df.
    - Cleanup: Removed hunt-ws/views-r1, hunt-ws/views-r2, hunt-ws/views-verify, hunt-ws/views-verify2; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__views.stripped.py
    - docs/shadow/current/django_strawberry_framework__views.overview.md
    - Prompt:
        - Use django_strawberry_framework/views.py as the entry point. Read docs/shadow/current/django_strawberry_framework__views.stripped.py and docs/shadow/current/django_strawberry_framework__views.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

## Scenarios

- [x] Baseline failure: collection-time model fixture isolation
    - Status: verified
    - Iteration: 1. Previous dispatch cancelled before a report; fresh Worker 1 requested.
    - Iteration: 2. Worker-0 resume: HEAD rebased bf02c227 -> f8a75753 (11 commits, baseline is ancestor; 6 package files modified baseline->HEAD, no adds/removes; shadow orientation stale for those 6, live source authoritative). W1 fix + W2 red/green proof recorded pre-rebase against digest d46503bc; current tree digest fce83b65. Focused 7-node selection re-run on rebased tree: 7 passed, exit 0. Fresh Worker 2 re-verification on the rebased diff required before ledger/tick.
    - ITEM_BASELINE: `f81220b2f76af510eb572b4245c0c7a51906dff4`.
    - Status at dispatch: only this coordinator-owned progress file is modified.
    - Entry points: `tests/utils/test_querysets.py`, `tests/types/test_base.py`.
    - Scope: diagnose existing finalization and missing-table test failures without changing
      security checks or suppressing correct finalizer rejections.
    - Workspace: `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/hunt-ws/baseline-fixture-pollution`.
    - Iteration: 3. Fresh Worker 2 re-verified on rebased tree (file digest fce83b65, HEAD f8a75753): expectation-first record `hunt-ws/w2-fixture-expectation-r2.txt`; green post-fix (combined reproducer 1 passed / 326 deselected; 2 regression tests passed; negative oracle passed); red with only the two `apps =` lines reverted in-workspace (1 call-phase failure / 1 passed, exit 1); bytes restored byte-identical and 5 `proxy_target` nodes green. Honest limitation recorded: the Meta reproducer node passes with and without the `Apps([])` fix (`related_name="+"` already suppresses the reverse accessor); C1 wrongness is carried by the registry-isolation test, deletion regression stands as collector-path guard. Unverified cells: full suite, PG, sharded.
    - Result: Fixed Low. Files changed: tests/utils/test_querysets.py (fixture-only; no production code); validation: focused 7-node selection 7 passed on rebased tree + workspace red/green proof.
    - Iteration: 4. Fast-forward drift check 2026-09-19: hunt fixture hunks intact
      (`_proxy_target_apps`, `_ProxyTargetCategory`, `_ProxyTargetHolder`); main-side test edits
      are adjacent seal rows incl. one new test building on the hunt fixture
      (`test_prefetch_child_over_unrelated_table_still_fails_for_proxy_target`). Focused re-run
      `-k proxy_target` 3 passed in shared tree. Verdict stands.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-fixture-expectation-r2.txt. Evidence: hunt-ws/verifier-out/ + hunt-ws/w2r2-*.log + hunt-ws/w2r2-evidence.json, file digest fce83b65.
    - Cleanup: Removed hunt-ws/baseline-fixture-pollution, hunt-ws/baseline-fixture-verifier, hunt-ws/baseline-fixture-reverify; cited evidence records preserved until final closeout; unrelated work preserved.

- [x] Scenario: Pagination window semantics
    - Status: verified
    - Iteration: 1. Worker 1 reported No bugs (17-battery green: offset/keyset/nested walks exact, backward walks, first:0/overshoot/inverted, tampered/cross-vocabulary/order-change rejections, exact-bound charge monotonicity, probe parity; C1-C5 disproved with live evidence; probe-rows mutant control biting exactly, restored byte-identical; suites 51 + 252 green; no shared-tree edits). Worker-0 mechanical checks pass (item-scoped package diff empty — connection hunks are the ledgered file-item fix, relay hunk is concurrent docstring dirt; workspace import/DB valid).
    - Iteration: 2. Worker 2 verified No bugs under two-phase dispatch (expectation-first `hunt-ws/w2-scenario-pagination-expectation.txt`, digest 522614c6, written with NO diagnosis in prompt): 17 probes + oracles 51/53 + library 250 replayed green (250 vs 252 = concurrent drift, all-green); 13 independent attacks passed (backward full walks both flavors, foreign/filter-change determinism, empty-flag shapes, fragment/variable charge monotonicity, beyond-page-1 parity, window-SQL shape + fallback-vs-ORM agreement); 2 own wrong expectations corrected (bare last:0 quirk pinned by oracles; variable-charge seeding). Phase-2 reconciliation: diagnosis disclosed after verdict — all points agreed; one exposed gap (C2 exact before:-1 shape) closed with own live probe (root/nested identical verdicts); own E1a schema-identity over-claim corrected to fingerprint+arity+scoping contract. Unverified cells: PG, sharded, async (sqlite sync only); per-viewer scoping observed without dedicated fixture.
    - Durable evidence (compact): expectation E1-E5 (context binding, algebra, monotonicity, window-fallback agreement, wire trust) + falsifiers C1-C6; replay = scenario_probes (17) + keyset/pagination oracles (51) + library (250) + window-proof; controls = probe-rows mutant (2 nested walks red, restore identical) + rejection no-traceback asserts + fail-then-pass attack corrections; attacks = backward walks, context-change determinism, charge monotonicity, SQL-shape asserts. Full probe files + logs in hunt-ws until closeout cleanup.
    - Result: No bugs. Evidence: W1 battery + control + oracles; W2 replay + 13 attacks + reconciliation probe. Entry digests: connection 3c4d5dcb, keyset df4b5e2f, relay 69085e7a.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-scenario-pagination-expectation.txt (phase 1, no diagnosis supplied; phase 2 reconciled). Evidence: hunt-ws/scenario-pagination-verify/ records.
    - Cleanup: Removed hunt-ws/scenario-pagination, hunt-ws/scenario-pagination-verify; expectation file + W2 logs retained in hunt-ws/ until closeout; unrelated work preserved.
    - Prompt:
        - connection.py, keyset.py, relay.py: cursor round trips fix schema, order and key context; first/last/after/before algebra; a bigger document never charges less on a named charge dimension. Hunt the contract across every entry point; implement every confirmed root-cause fix.

- [x] Scenario: Authorization and visibility across actors
    - Status: verified
    - Prompt:
        - utils/querysets.py seal, mutations/permissions.py, resource_policy.py, optimizer/_context.py: forbidden rows absent across actor switches, prefetch and reverse relations, cache reuse across executions, awaitable truthiness, point-in-time authorization. Hunt the contract across every entry point; implement every confirmed root-cause fix.
    - ITEM_BASELINE: `ba67c0e6d4cf660026640b69202f81f479bd1809`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22 18:29 UTC, workspace hunt-ws/scenario-authz-r1. Entry points per the prompt at post-querysets-re-pass bytes (querysets.py e0b0651a verified this session). Single hunter (not marked high-risk; the pagination precedent). Standing leads to re-derive, never trust: HUNT.md's three historical client-reachable shapes (prefetch leak failing open on reverse relations w/o `related_name`, awaitable-truthiness silent allow, cross-execution sentinel leak); plan-cache actor isolation (deferred to this scenario by the strings item); per-viewer scoping (observed without dedicated fixture by the pagination scenario); the `_DEFAULT` census surfaces (node refetch, RelatedFilter derive, mutation locate, write decode) as visibility-adjacent. Sensitive-findings rule armed: a client-reachable isolation/authorization defect is reported ABSTRACTLY with evidence held in scratch (SECURITY.md maintainer path before any reproducer lands in a tracked file).
    - Iteration: 2. Worker 1 scenario hunt reported No bugs (8 contract rows R1-R8; 57-probe battery: 38 live-combined + 19 isolated, all green on ceiling + 10 floor; all 4 standing leads re-derived on current bytes, none confirmed — no-related_name reverse, awaitable truthiness, cross-execution sentinels, plan-cache actor isolation with `_plan_cache` emptiness + cacheability pins, per-viewer scoping now pinned by AZ01/AZ02, `_DEFAULT` census bytes-unchanged and unflipped; independent oracles via direct ORM + raw SQL throughout; 4 biting WS-only controls restored sha-identical; 2 robustness rows without fix: (i) consumer-authored relation-resolver ownership, (ii) gate False-without-raise not denying under the raise-to-deny contract). Zero shared-tree edits; no permanent test owed (scenario evidence not promoted — pinned behaviors already covered by cited live/package rows, isolated shapes wire-unreachable). Worker-0 mechanical checks pass (item diff vs ba67c0e6 empty for package/tests/examples; all 10 input digests == worktree incl. types/resolvers.py clean vs baseline; 16/16 probe sha256 pins match; 4/4 control restores match; live-combined re-run 38 passed in WS; isolated 4+5+2+5+3 = 19 exact, all green; AZ00 asserts WS import + DB; no strays; sharded/PG honestly unverified). Ride-alongs for W2 judgment: the 2 robustness rows; the cited-not-probed deferrals (subscribe-then-expire → consumers item; cancel/timeout → Scenario 3); the PG validate-then-change execution gap; independent depth search per HUNT.md W2 duty 6; floor re-execution. Report /tmp/w1-scenario-authz-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/scenario-authz-verify, expectation-first.
    - Iteration: 3. Worker 2 verified (expectation-first `hunt-ws/w2-scenario-authz-expectation.txt` befbc584, E1-E13 + D1-D4 + L1-L4, zero contradiction; one honest self-correction: E4 over-claimed "custom hook => plan uncached", refined by probe to the sharp rule — only plans EMBEDDING a request-scoped queryset are cacheable=False, relation-free root plans cache correctly with per-request hook re-run — pinned by new W2-09 with measured cross-actor HIT + exact rows): fresh-WS replay 38 + 19 exact (one-line AZ00 WS-literal retarget in W2's copy, same dispensation); all 2107 W1 lines re-examined file by file with oracles judged genuine (forbidden-row-exists oracle + wire-absence assert + staff positive control per probe); 17 own K2 probes green (four-actor rotation both directions, nested totalCount, live reverse-M2M + join-table SQL, exact async rotation, grant/revoke flap, forward-M2M warm orders, nested execution sharing the outer context with actor flip, gate True/None/non-callable, `.none()`-hook cached-plan rotation); all 3 deferrals ACCEPTED on reasons (subscribe-then-expire → consumers verified; cancel/timeout → Scenario 3's fence with check_deadline code-verified ahead of DB work; PG lock-execution honestly UNVERIFIED); both robustness rows agreed with cited rows ((i) consumer-resolver ownership, (ii) raise-to-deny with the mutation-bool contrast + doc-line card fodder); no-permanent-test rationale ACCEPTED (nothing changed; promotable behaviors covered by existing rows); K4 no finding, sensitive rule never triggered; item diff confirmed EMPTY with 10/10 digests fresh; 3 own biting controls restored sha-identical (shas equal W1's — identical starting bytes); floor re-executed 10/10; sharded/PG unverified for cause, async HTTP covered. Report /tmp/w2-scenario-authz-report.txt; shared tree untouched by W2.
    - Result: No bugs. Evidence: W1 57-probe battery green ceiling + 10 floor + 4 biting controls; W2 replay + 17 independent probes + 3 controls + floor re-executed.
    - Verification: Passed. Expected-before-diagnosis: hunt-ws/w2-scenario-authz-expectation.txt. Evidence: hunt-ws/scenario-authz-verify/ records.
    - Cleanup: Removed hunt-ws/scenario-authz-r1, hunt-ws/scenario-authz-verify; expectation file retained in hunt-ws/ until closeout; unrelated work preserved.

- [x] Scenario: Transaction and session lifecycle under interruption
    - Status: verified
    - Prompt:
        - utils/write_transaction.py, the three write pipelines, consumers.py: locks, rollback, commit hooks, cancellation, sync_to_async boundaries, failure during failure handling. Hunt the contract across every entry point; implement every confirmed root-cause fix.
    - ITEM_BASELINE: `edf27c59f0ae9a4acc2006e0e20af9356bd8d46b`.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-22 19:12 UTC, workspace hunt-ws/scenario-txn-r1. Entry points per the prompt at current bytes (write_transaction.py 9ad493b6, consumers.py 936210e2, both verified). Single hunter (not marked high-risk; the pagination + authz precedent). Standing leads to re-derive, never trust: the write_transaction item's 8 robustness rows (disarm-failure masking, fingerprint `__format__` trust boundary, `NotUpdated`-trap version split); the consumers T1-T8 interruption suite + reentrancy/cancelled-waiter characterizations; cancel/timeout deferred here by the authz scenario (check_deadline-ahead-of-DB code-verified on node + connection paths); register post_save-boom atomicity + save-side IntegrityError race (file-level probes exist). The three write pipelines = mutations + forms + rest_framework write paths.
    - Iteration: 2. Worker 1 scenario hunt reported Fixed — Defect 1 High (product): cancel-during-window-enter strands the transaction open — the boundary thread ALWAYS finishes `atomic.__enter__` while the task abandons the bare await, so the alias lock releases over an open window on the shared worker connection and every later mutation nests inside: success payloads for writes that never commit + cross-request contamination. Fix at the owner (`schema.py::_execute_mutation_field_async`): opener shield-handoff — the opener is awaited to its KNOWN outcome across repeated cancellation; completed enter is exited to completion before the cancellation propagates; failed enter reports its own error; failed handoff-exit surfaces chained. + Defect 2 Medium (test choreography): the new tests' enter-gate released AFTER `await task` is a circular wait against the handoff (every suite touching them hung 30+ min at ~0 CPU); fix moves `release_gate.set()` before `await task` with no yield between cancel and release. Battery 42/42 green post-fix (TX00 + TX10/20/21/30/40/50/60/99 with independent oracles: second-connection row reads, session-alias DBs, worker-state probes, fresh-mutation follow-ups); pre-fix witness TX10A carried forward (`in_atomic: True` + nested follow-up, TX10A-PREFIX.log on disk — NOT re-run pre-fix this session, failability re-proof is W2's sharpest duty). Files changed: schema.py (d0c79838, +50/-1) + tests/test_schema.py (ba2e24fe, 4 handoff tests + 5 helpers, pure addition). Worker-0 mechanical checks pass (item diff vs edf27c59 exactly the 2 files; schema.py was clean-vs-HEAD at baseline so the whole delta is the fix — schema.py marked STALE, bounded re-pass queued after scenario close; collection 42 exact; 4/4 permanent tests pass in shared tree 2.85s; ruff + format + trailing-commas + banned-token scans clean — re-run by Worker-0; no new pragma; PG cells honestly unverified). Report errata flagged for W2 (non-blocking): spikes/ + TX10A-PREFIX.log live under scenario_txn/, not the WS root; /tmp/w1-hang-dump.txt is non-empty (the xdist faulthandler dump), not "empty". Ride-alongs for W2 judgment: full failability re-proof via WS-only revert (all 4 tests + TX10A red pre-fix); the Defect-2 determinism claim (does release-before-await still test abandonment faithfully — neuter-the-shield discrimination proof); High/Medium severity factors; live-tier reachability of cancel-during-enter; lock-release proof on all arms; async flake resistance (repeated runs); floor cell (W1 never ran it). Report /tmp/w1-scenario-txn-r1-report.txt. Fresh Worker 2 dispatched, workspace hunt-ws/scenario-txn-verify, expectation-first.
    - Iteration: 3. Maintainer review 2026-09-22 (Rio): revision-needed, back to a FRESH Worker 1 (dead r1 workspace orientation only; the dispatched W2 never started — workspace never built). Defect 1 stands as real; new challenges: exit-side hole A (bare `_exit_clean` ~:422 / `_exit_with_error` ~:409 awaits; one helper for all three transitions), cancellation swallowing B (~:365/:390 vs `_AsyncAliasLock` precedent), opener self-cancel C (~:368); test errata T1 (false docstring ~:568-571), T2 (passes pre-fix ~:635), T3 (cleanup not in `finally` ~:751), T4 (no shield discrimination ~:758); record corrections R1 (Defect 2 is test-construction errata, not a defect, no severity), R2 (tiered severity: HTTP heals via `close_old_connections`, Channels process-lifetime, High stands for WebSocket), R3 (contract rows GOAL.md ~:546 + GLOSSARY.md ~:41). Full text in Current status; W2 criteria W2.1-W2.8 ride the next verification.
    - Iteration: 4. r2 W1 revision reported (first r2 dispatch died infra-clean, no state; this is the re-dispatch): one `_drive_window_transition` helper drives all three transitions to known outcome across cancellation (first CancelledError re-raised, worker error chained as cause, no `.exception()` on cancelled futures) + `_settle_window_if_open` worker-thread guard by Atomic membership; T1 docstring rewritten, T2 REPLACED (enter-failure-during-cancel), T3 renamed (chains-under-cancellation, `finally` reset), T4 rewritten pre-submit (green on r1 — determinism erratum — discriminating vs an abandoning scratch variant); 6 new timeout/taskgroup rows B1-B6 (real `asyncio.timeout`/`TaskGroup`, `_SKIP_BEFORE_311` floor gates); R1/R2/R3 corrections claimed for the record; rule-35 three legs stated for A/B/C; red-pre claimed 7F/3P vs r1 bytes + 9F/1P vs HEAD bytes (B6 cannot-fail-vs-HEAD with stated gate-abandon reason); F1 informational (3.10 floor drops cancel causes through `await task`, `_TASK_BOUNDARY_KEEPS_CANCEL_CAUSE` gates cause asserts to 3.11+); deliverables schema.py 6f238a09 + tests 0b82f80b. Worker-0 mechanical checks PASS (digests match; fence diff vs 38d6fc98 exactly the 2 files, 663+/164-, hunk headers in-fence; baseline erratum confirmed — 22:11 Fold cited dead-dispatch 39e2512e, live used 38d6fc98, empty fence diff; venv restored 3.14.2, lock clean; no strays; banned tokens only lowercase domain "worker" x12, assessed clean per the 16:01 "sweep" precedent; no new pragma — the 1 hit is pre-existing context; ruff re-run clean; test-def delta reconciles 2 removed + 2 renamed + 6 new; WS anchor probe on disk + W0-run green with WS import + WS DB; independent 12/12 focused green 5.69s; counts/controls/reach all stated and biting; cells honest). Ride-alongs for W2 phase-2 reconciliation: blind-vs-claimed polarity inventories (esp. B6-vs-HEAD, T4-vs-r1), F1 version-gating soundness, T4 discrimination independence, severity tier factors, tier/flavor placement, "worker" prose re-judgment, /tmp-scratch volatility (W2 re-derives; descriptions suffice), full-suite shared-tree run note (unauthorized strictly, harmless — focused-only reminder in the W2 brief). Fresh Worker 2 two-phase dispatched (workspace hunt-ws/scenario-txn-verify, path unused; phase 1 fenced: contract + reproducer + diff only, expectation to hunt-ws/w2-scenario-txn-expectation.txt, then polls for hunt-ws/txn-verify-phase2/DIAGNOSIS.txt; gate-free probe staged verbatim at hunt-ws/txn-verify-inputs/, sha256 65d1ad35 both copies; diagnosis disclosed only after W0 verifies the expectation uncontaminated).
    - Iteration: 5. W2 verdict revision-needed (2 narrow challenges; everything else verified with preserved scope — report hunt-ws/reports/w2-scenario-txn-report.txt). CH-1 (prose): R5 docstring ~:948-949 carries hunt-internal labels ("rode out in r1 ... green before and after the revision"), unique repo-wide in permanent .py; remedy timeless reword. W0 owns the miss: the mechanical token scan covered the 9 brief-listed words only — lesson recorded: sweep vocabulary now also covers iteration labels (`r[0-9]`, "the revision", "re-pass") on added lines. CH-2 (missing Proof for defect C): teardown arm REAL (W1 P4-C2/C4/C5 + W2 A3 both strand on r1 bytes, clean post-fix; rule-35 legs ACCEPTED) but no permanent test — `_cancel_all_but_current` added yet uncalled, cancelled-call arms execute nowhere in-tree; remedy one deterministic teardown pin, red-on-ITEM / green-post / 3x. Reconciliation 1-10 all agree (polarity exact incl. R4@HEAD refinement immaterial; B6 "cannot" logic confirmed; T4 via independent V-comp/V-enter variants, /tmp never opened; F1 confirmed with own repro, version-gating sound; tier placement agree; "worker" x12 domain agree; /tmp never used; suite note no fence interaction). R2 MECHANISM CORRECTION (W2-verified, code-traced — amends review-R2 and r2-R2 as recorded): the HTTP heal is ThreadSensitiveContext isolation + per-request executor shutdown (asgi.py:172, sync.py:146-148), NOT `request_finished` → `close_old_connections` (loop-thread-local over thread-local connections, db/__init__.py:57-63, cannot touch the worker strand); tiers STAND (HTTP Low-at-most, Channels High for the WebSocket path). O1 subsumed by CH-2 (pin calls the helper or it goes); O2 scratch-only; O3 per-node-isolation methodology; O5 N1 exotic, correctly not demanded. Preserved scope frozen: mechanism, 10+2 rows, both polarity inventories, W2.2-W2.8 proofs, 153/153 file, sync path. Re-pass acceptance: CH-1 exact-timeless + CH-2 red/green/3x + full file green + 3 gates clean + no new pragma + no other fence bytes. Fresh Worker 1 narrow re-pass dispatched (ITEM_BASELINE 1bb311a9, workspace hunt-ws/scenario-txn-r2 REUSED intact + hash/anchor re-verified at start, scenario-txn-verify read-only; first W2 rejection on this item — nowhere near the two-failed-re-pass block).
    - Iteration: 6. r3 W1 narrow re-pass reported (CH-1 + CH-2 only, r2 workspace reused intact): CH-1 exact-timeless reword (old phrasing retired repo-wide, 0 .py hits — the 1 grep hit is a stale .pyc cache, not source); CH-2 new pin test_async_window_teardown_with_completed_enter_exits_and_releases (C2 capture + A3 release tail for RUF006; calls `_cancel_all_but_current`, helper KEPT, O1 closed by use; floor-clean by construction, self-healing per R1 precedent, no finally); red-proof bytes correctly interpreted as r1 blob d0c79838 (NOT the r3 no-change baseline — same bytes the W2 acceptance meant); deliverables schema.py 6f238a09 unchanged + tests 266a09e0. Worker-0 mechanical checks PASS (digests match; fence diff vs 1bb311a9 exactly tests-only, 2 hunks, 79+/3- reconciled with diffstat 82 = 79+3, hunk headers @945/@1275 in-fence, schema.py 0 lines; CH-1 hunk read: docstring-only, timeless; banned + iteration-label sweep 0/79; ruff + commas re-run clean; no new pragma; full file 154 green independent; new row 3x green independent 1.49/1.48/1.51s; WS anchor re-run green; db.sqlite3 untouched; no strays; red-proof rides to re-W2). Fresh Worker 2 narrow re-verification dispatched (criteria K1-K5: timelessness, genuine-Proof incl. vacuity attacks, stability + preserved scope, fence discipline + gates, determinism + floor; fresh workspace hunt-ws/scenario-txn-verify2; mini-expectations before runs; report hunt-ws/reports/w2-scenario-txn-reverify-report.txt).
    - Result: Fixed High (exit-side hole A, WebSocket tier) with two Low hardenings (B cancellation identity, C teardown arm). Files changed: django_strawberry_framework/schema.py (`_drive_window_transition` driver + `_settle_window_if_open` guard + `_cancel_all_but_current` helper, 6f238a09) + tests/test_schema.py (11 window rows: 4 reworked + 7 new incl. the teardown pin, 266a09e0); validation: blind polarity exact on all three eras (7F/3P vs r1, 9F/1P vs HEAD), gate-free + both-flavor + floor + flake proofs, K1-K5 re-verified. Record position (all W2-verified): R1 "Defect 2" is test-construction errata, not a defect, no severity; R2 tiered severity (HTTP Low-at-most, Channels High stands for WebSocket) with the corrected mechanism (ThreadSensitiveContext isolation + per-request executor shutdown, NOT close_old_connections); R3 contract rows GOAL-6 + GLOSSARY-41.
    - Verification: Passed after one revision round (CH-1 prose + CH-2 missing Proof challenged, corrected, re-verified K1-K5). Expected-before-diagnosis: hunt-ws/w2-scenario-txn-expectation.txt (fenced phase 1, W0 contamination-checked zero hits, hash-pinned f1b3b805, never modified). Evidence: hunt-ws/reports/w1-scenario-txn-r2-report.txt + w1-scenario-txn-r3-report.txt + w2-scenario-txn-phase1.txt + w2-scenario-txn-report.txt + w2-scenario-txn-reverify-report.txt; workspaces removed post-verify; digests 6f238a09/266a09e0 re-hashed at close.
    - Cleanup: Removed hunt-ws/scenario-txn-r1, hunt-ws/scenario-txn-r2, hunt-ws/scenario-txn-verify, hunt-ws/scenario-txn-verify2, hunt-ws/txn-verify-inputs, hunt-ws/txn-verify-phase2; expectation file + 5 reports retained in hunt-ws/ until closeout; floor-310 kept; unrelated work preserved.

- [x] Deep dive 1: nested read execution over real relation shapes
    - Status: verified
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-23, ITEM_BASELINE 71d66ababfd8f8bf34a723f1f0b0ecc48211b821, workspace hunt-ws/deep-1-read-shapes-r1 (rsync excl. .git/.venv/__pycache__/docs/hunt-ws). Tree at dispatch: ledgered hunt dirt + DRY concurrent files + honest_*.txt + this file; attribution-first per HUNT.md.
    - Iteration: 2. Worker 1 reported No bugs (11 contract rows; 3 promotions all still-blocked with exact fixtures; live falsifier per shape + named unreachability; fix-neighborhood attacks; 60-probe battery + floor 296; zero shared-tree edits). Worker-0 mechanical checks PASS (item diff vs baseline empty excl. this file; 18/18 input digests match pins; collection 60 exact via WS --collect-only; attribution gate asserts WS import + WS/memory DB with prints in all 21 logs; WS nested_planner == shared 225011b6 with .bak identical + .sha pin consistent; no nested hunt-ws; cells honestly stated; controls named with logs for W2 to judge). Report: hunt-ws/reports/w1-deep-1-read-shapes-report.txt. Fresh two-phase Worker 2 dispatched (workspace hunt-ws/deep-1-read-shapes-verify; expectation hunt-ws/w2-deep-1-read-shapes-expectation.txt; drop gated on contamination check).
    - Iteration: 3. W2 phase-1 expectation LANDED (21.5 KB: own trace + Part A A1-A19 with falsifiers + T1-T10 attack plan + cell plan; own digests match W1 pins). Contamination check PASS (sole grep hit is the line-12 fence declaration; sealed 10:20:11 before any probe run). Hash-pinned b4bdab78 (no further modification). Phase-2 drop written (hunt-ws/deep-1-verify-phase2/DIAGNOSIS.txt) with 10 ride-alongs (P1/P2/P3 census re-derivations, P3 tier adjudication, archive_genres A7-vs-W1 adjudication, remaining unreachability, robustness note, reason-only axes, floor re-execution, control re-derivation, independent depth). Live divergence flags for phase 2 (no pre-judgment): P3 holder-HTTP promotability (A17) vs W1 still-blocked; A7 archive_genres readability vs W1 omission ruling.
    - Entry points: optimizer/join_taxonomy.py, optimizer/nested_planner.py, optimizer/nested_fetch.py, optimizer/lateral_fetch.py, optimizer/single_parent_fetch.py, optimizer/plans.py, optimizer/walker.py, optimizer/field_meta.py, optimizer/selections.py, utils/querysets.py (child policies), utils/relations.py, utils/connections.py, connection.py, keyset.py, relay.py.
    - Contract citations: README ordered-offset + Relay connection + FK-id elision rows; GLOSSARY nested-fetch/window/keyset/relation_shapes entries; per-parent fallback exactness (join_taxonomy fix row); M2M advisory silence (nested_planner fix row); cursor presence parity (connections fix row); optimizer plan/apply + child-policy docstrings.
    - Actors: staff/anon/view-perm readers (row-correctness only — forbidden-absence belongs to Deep dive 3); consumer hook authors (combinator-hook shapes out of scope, the _DEFAULT decision stands).
    - Input domain: live /graphql/ nested selections (lists + connections + node/nodes) over every legal relation shape fakeshop now carries: text pk (Edition.isbn_13), O2O pk (PatronProfile), to_field FK (favorite_genre), MTI parent link (LendingDesk), proxies, GFK/GenericRelation, non-editable M2M, relations without related_name, two-node FK cycle, self/symmetric M2M; forward + reverse + to-many + deep nesting; first/last/after/before incl. empty-string/overshoot/inverted cursors.
    - Lifecycle and state: plan (walker/extension/cache) -> child querysets (policies/seal) -> fetch (windowed/per-parent/lateral-refusal) -> row assembly; per-operation frames, cross-request plan cache.
    - Observations and independent oracle: wire rows + order + pageInfo/totalCount vs direct ORM + raw SQL on the same seed; EXPLAIN/SQL-shape asserts for window-vs-fallback; query-count bounds; cache-hit measurement where claimed.
    - Dependency edges: roots/relations -> walker -> child policies -> plans/fetch; keyset <-> connection cursors; relations.py classify_path feeds join_taxonomy; seal runners under every child.
    - Applicable cells: default ceiling sqlite (executed); floor-310 (executed via the shared testbed); live /graphql/ HTTP (primary tier); in-process async paths; PG-lateral execution + FAKESHOP_SHARDED=1 stay unverified without Rio's word (recorded, never passed).
    - Owning files: the entry points above.
    - Prompt (deeper than before): the first pass proved exotic shapes with invented package models at unit tier and left live-tier rows Blocked for missing fixtures. Now: (1) check whether the join_taxonomy composite-ForeignObject block (record :806), the nested_planner M2M-ordering block (record :851) and the connection negative-cursor unit pin can reach live /graphql/ with the c25a34e3 shapes — promote each reachable one, record still-blocked with the exact missing fixture otherwise (never add an example model); (2) re-derive row-correctness LIVE for text-pk/O2O-pk/to_field/MTI/proxy/GFK/no-related_name/cycle/self-M2M nested reads incl. window-vs-fallback agreement and FK-id elision; (3) falsifiers first — for every shape either a live probe proving exact rows or a named reason it cannot be reached; (4) attack the three fixes' neighborhoods (virtual-link classification incl. new shapes; advisory silence incl. M2M-ordered windows; cursor presence incl. ""/whitespace/0). Out of scope: visibility decisions (Dive 3), cost charging (prior verdicts stand), the _DEFAULT combinator flip (Rio decision stands).
    - Result: verified. No bugs. All three promotions honestly still-blocked with exact fixtures for Rio: (P1) composite-PK parent + multi-column ForeignObject reverse as a nested connection (gated census: 0 virtual links over 248/257 fakeshop relations, W2-recounted); (P2) nested M2M connection with non-pk effective order + absent coverage (only 2 live nested M2M, both pk-terminal-silent both eras, W2-re-proved with own revert + firing control); (P3) root connection field with a sequence-returning consumer resolver for project-schema /graphql/ (AST 11 fields / 0 resolver=, W2 spy-superset n=11 all QuerySet) — with a TIER SPLIT: holder-schema-over-HTTP promotion is constructible today (W2 2 probes, no new model, beside its /graphql-test/ precedent) and rides as a judged lead for Rio (test placement, not a defect). Live falsifier per reachable shape (text-pk/O2O-pk/to_field/MTI/proxy/no-related_name/cycle/self-M2M incl. window-vs-fallback + elision map); named unreachability for GFK/GenericRelation/archive_genres (schema-author omission — W2's A7 readability expectation probe-contradicted, W1 right)/to_field-reverse/symmetric-M2M/MTI-reverse/proxy-reverses/ItemHold. Dangling-to_field null CONFORMS to the absence-containment row (W2 corrects W1's rationale, no defect). Strongest new probes: W2's TRUE Decision-5 deferred-FK pair (W1's probe misattributed its own green run — elision firing, not fallback; both true paths correct) and R7 revert (mine + permanent before:"" pin bite; W1's 9 cursor probes provably non-discriminating). Report-accuracy notes only (promotion "6" typo, W1's unnamed 296 unverified-by-construction, R-f rationale, Note-1 misattribution) — none revision grounds. Zero shared-tree edits.
    - Verification: two-phase W2 VERIFIED. Expectation-first (19 rows + T1-T10, fenced, sealed 10:20:11, contamination PASS, hash-pinned b4bdab78, unmodified); phase-2: 60/60 replay + 33 independent attacks green; all censuses recounted by independent methods; 2 WS-only revert cycles cmp-identical; floor-310 re-executed read-only (387 named nodes, bed untouched); 16/19 expectation rows confirmed, 1 contradicted-admitted, 1 split-adjudicated; no claim reached two rule-35 legs. No ledger rows (nothing changed). No stale triggers.
    - Cleanup: Removed hunt-ws/deep-1-read-shapes-r1, hunt-ws/deep-1-read-shapes-verify, hunt-ws/deep-1-verify-phase2; expectation file + 2 reports retained; floor-310 kept (W2-proven untouched); unrelated work preserved.

- [x] Deep dive 2: write-input parity across mutation flavors
    - Status: verified
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-23, ITEM_BASELINE b3e98960d35281ca4dcdd2342447cbd4257fa6cd, workspace hunt-ws/deep-2-flavor-parity-r1 (rsync excl. .git/.venv/__pycache__/docs/hunt-ws). Tree at dispatch: ledgered hunt dirt (incl. integration-seam hunks in this dive's files — verify-against, never relitigate) + DRY concurrent files + honest_*.txt + this file; attribution-first per HUNT.md.
    - Iteration: 2. Worker 1 reported No bugs (22 contract rows; 100-probe wire-differential battery green on ceiling + floor; 6 executed splits adjudicated validator-inherent/documented; ROB1 prose over-claim record-only; D1/D2 live rows still-blocked with exact fixtures; L1-L3 routed leads; zero shared-tree edits). Worker-0 mechanical checks PASS (item diff vs baseline empty excl. this file; 12/12 input digests match pins; collection 100 exact; full battery RE-RUN by Worker-0 in the W1 WS: 100 passed / 25.00s; anchor pins WS import + WS DB; no nested hunt-ws; floor-310 untouched — zero post-11:00 non-venv writes; cells honestly stated). Report: hunt-ws/reports/w1-deep-2-flavor-parity-report.txt. Fresh two-phase Worker 2 dispatched (workspace hunt-ws/deep-2-flavor-parity-verify; expectation hunt-ws/w2-deep-2-flavor-parity-expectation.txt; drop gated on contamination check).
    - Iteration: 3. W2 phase-1 expectation LANDED (22.9 KB: 22 rows W2-R1..R22 + 9 predicted splits S1-S9 with falsifiers + 11 parity predictions P1-P11 + A1-A14 attack plan + cell plan; acceptance-vs-reporting fence self-imposed; own digests match integration pins). Contamination check PASS (sole grep hit is convergent source discovery; sealed 11:32:53 before any probe run). Hash-pinned b7d6ad9c (no further modification). Phase-2 drop written (hunt-ws/deep-2-verify-phase2/DIAGNOSIS.txt) with 10 ride-alongs (replay, split-rationale re-derivation + convergence reconciliation, B1/B2 recounts, ROB1, leads, matrix rulings, controls, floor, independent depth, hygiene). Live flags for phase 2 (no pre-judgment): W2's S2 stale-value update vs W1 coverage; S9-vs-C1 / S1-vs-C2 / S3-vs-C3 / S4-vs-C4 reconciliations; C6 custom-input neighborhood.
    - Entry points: mutations/resolvers.py, mutations/inputs.py, mutations/operations.py, forms/resolvers.py, forms/inputs.py, rest_framework/resolvers.py, rest_framework/inputs.py, rest_framework/serializer_converter.py, auth/mutations.py, utils/write_values.py, utils/errors.py (mapper seam, acceptance side only).
    - Contract citations: README three-flavors-one-shape + FieldError envelope rows; GLOSSARY djangomutation/form/serializer entries; spec-039 converter rules (incl. Decision 7 allow_blank); relation-id input naming (global id vs raw pk); payload slot parity (node/result/ok+errors).
    - Actors: staff writers; anon/denied callers (denial SHAPE only — denial DECISIONS belong to Dive 3; error KEYING belongs to Dive 5); consumer form/serializer authors (declared fields, relations, nested writes, files).
    - Input domain: the same logical payloads across model/form/serializer/plain-form flavors: null vs missing vs UNSET per field kind; relation ids (global/relay pk/raw pk/invalid/missing); nested writes; M2M sets; file/image uploads; multi-word field names; CharField/ListField/ChoiceField shapes incl. allow_blank.
    - Lifecycle and state: input coercion -> decode (relation resolution, null handling) -> validation (full_clean/form/serializer) -> write tail; rolled-back writes for parity probes, committed writes only where the contract needs them.
    - Observations and independent oracle: wire payloads (accepted values + error sets) compared ACROSS flavors for identical logical inputs (differential method — the K6 lesson: no vocabulary-filtered grep survey may stand in for execution); direct ORM reads for written rows; serializer/form twins as the DRF/Django oracles.
    - Dependency edges: flavors -> shared decode/write tails -> mapper seam; inputs.py/hook_context shape the payloads each flavor validates; converter rules fix the input SDL all flavors share.
    - Applicable cells: default ceiling sqlite (executed); floor-310 (executed); live /graphql/ HTTP (primary tier wherever a fakeshop mutation exists); PG/sharded stay unverified without Rio's word.
    - Owning files: the entry points above.
    - Prompt (deeper than before): integration found ONE cross-flavor split (FieldError.field keying) with a survey method that missed 3 pins (K6 blind spot: single-word Django!=wire names). Now: (1) re-derive flavor parity from scratch by WIRE-DIFFERENTIAL, never by survey — the same logical payloads through all reachable flavors, asserting identical acceptance and identical error SETS; (2) chase the recorded divergence leads (rf/inputs canonical-name divergence in extremes; forms/resolvers M2M null divergence; omission-matrix corners; nested-write and file-input parity); (3) check whether the serializer D1/D2 live blocks (record :1096) can reach live /graphql/ now — a CharField allow_blank fixture exists (library/serializers.py:284) but D2 needs the Choice shape: promote if the exact shape exists, record still-blocked with the exact missing fixture otherwise (never add an example model); (4) falsifier per flavor pair: either a differential probe proving parity or a confirmed split with rule-35 legs. Out of scope: error keying/message wording (Dive 5), auth decisions (Dive 3), tx atomicity mechanics (scenario verdict stands).
    - Result: verified. No bugs. Seven executed splits all adjudicated validator-inherent or spec-documented (C1 form-scalar-null "" / C2 form-M2M-null clear / C3 subtitle NULL-vs-"" / C4 required-M2M [] / C5 whitespace / C6 custom-input-partial-required / C7 coercion-vs-envelope channels), each re-derived by W2 against the installed raw validators + governing rows (S9/C1, S1/C2, S3/C3 convergences; S4-vs-C4 different cells both holding; C6 behavior agreed with an R21 citation erratum — build_custom_partial_input_class does not exist, true path mutations/sets.py::_materialize_merged_input, prose-only in scratch). Strongest new probes: W2's S2 stale-value differential (W1-uncovered: model/serializer accept, form rejects naming the STALE field — documented README sharp edge), D11 omit-vs-null file matrix (spareImage omit stores '' byte-identical to raw-ORM twin), D12 plain-form all-NON_NULL introspection, D5 Django-spelling coercion battery (K6 single-word lesson). D1/D2 live rows honestly still-blocked with exact fixtures (zero ListFields of any kind incl. prose + constructibility audit closing W1's except-swallow; 2 ChoiceFields neither allow_blank; CharField-vs-Choice arm distinction code-confirmed). ROB1 (null_field_error "every write flavor" docstring) agreed record-only per F1 precedent. L1/L3 routing agreed; L2 GlobalID-scalar masked failure re-proved byte-identical on all 4 legs with correlationId — parity holds (no Dive-2 defect) and a DIVE-5 RIDE-ALONG NOTE carries it (Dive 5 must place this producer in the masking table + code pins; reproducer: D3 tests, removed with the W2 WS — re-drive from the report's wire shape). Zero shared-tree edits.
    - Verification: two-phase W2 VERIFIED. Expectation-first (22 rows + S1-S9 + P1-P11 + A1-A14, fenced, sealed 11:32:53, contamination PASS, hash-pinned b7d6ad9c, unmodified); phase-2: 100/100 replay (99 verbatim + anchor-literal mechanical, 100/100 after WS-only repoint) + 55 own probes green; all splits re-derived; censuses recounted with stated vocabulary; floor re-executed W1's-way (155/155, bed-untouched); 4 expectation gaps self-corrected (G1-G4); no challenges. No ledger rows (nothing changed). No stale triggers.
    - Cleanup: Removed hunt-ws/deep-2-flavor-parity-r1, hunt-ws/deep-2-flavor-parity-verify, hunt-ws/deep-2-verify-phase2, hunt-ws/w2-floor-marker (bed-proof marker; method + outcome in the report); expectation file + 2 reports retained; floor-310 kept (proven untouched twice); /tmp/w2-floor-marker left (stale first-attempt marker in OS temp, volatile, ignored); unrelated work preserved.

- [ ] Deep dive 3: authorization on the deferred paths (HIGH-RISK: two independent W1 hunters)
    - Status: blocked
    - Iteration: 1. Fresh Worker 1-A dispatched 2026-09-23 (lens: contract + state transitions), ITEM_BASELINE 9cb7bbb928274c24c2d606300fe348c3a3fd2ee1, workspace hunt-ws/deep-3-authz-a-r1 (rsync excl. .git/.venv/__pycache__/docs/hunt-ws). Tree at dispatch: ledgered hunt dirt + DRY concurrent files + honest_*.txt + this file; attribution-first per HUNT.md. W1-B (lens: implementation + failure paths) follows blinded after A reports; reports exchanged read-only after both report.
    - Iteration: 2. Worker 1-A REPORTED (result sealed pending W1-B per the high-risk protocol — no diagnosis recorded here until both report). Zero shared-tree edits. Worker-0 mechanical evidence-table checks PASS (item diff vs baseline empty excl. this file; all input digests match pins; collection exact; full battery RE-RUN by Worker-0 in the A workspace green as left; provenance gates present in all probe modules; no nested hunt-ws; floor-310 untouched; cells honestly stated). Handoff bytes (if any) preserved verbatim under hunt-ws/reports/ with pins (recorded post-B). Fresh Worker 1-B dispatched blinded (workspace hunt-ws/deep-3-authz-b-r1; same ITEM_BASELINE 9cb7bbb9 — tree unchanged; sealed paths: A's report + A's workspace + any d3a1-* handoff files; cite-audit enforced).
    - Iteration: 3. Worker 1-B REPORTED Blocked (sensitive-findings rule APPLIED — abstract only below, all exploit-shaped evidence sealed in the B workspace, never executed by Worker 0): one confirmed HIGH client-reachable visibility defect — surface: nested relation reads through a consumer-provided Prefetch optimizer hint over a hiding target type; rows: get_queryset traversal survival + the optimizer-trust statement (types/resolvers.py::_custom_visibility_type); location: optimizer/walker.py::_apply_hint consumer-prefetch branch; legs (abstract): documented Meta.optimizer_hints + ordinary anon nested query. Evidence seat: hunt-ws/deep-3-authz-b-r1/d3b/test_d3b_hint.py (5 nodes by --collect-only; the file was NEVER executed outside B's session). 60 no-bug probes green (RE-RUN by Worker-0 excl. the hint file: 60 passed / 8.70s). Zero shared-tree edits. Blinding audit PASS (zero sealed-path cites). Mechanical PASS (item diff empty; 14/14 digests match; no nested hunt-ws; floor untouched; PG/sharded honestly unverified). Leads: L1 async-auth fail-closed (converges with A's J1 under different probe names — independence signal), L2 masked GlobalID (Dive-5 shape), L3 blocked fixture (hiding hook on VenueBadgeType/VenueSponsorType — example-model change, Rio's).
    - Iteration: 4. Worker 1-A result UNSEALED (both hunters reported): Fixed Low IN WORKSPACE, blocked on shared-tree landing — nested forward-FK/OneToOne + reverse-OneToOne resolvers never call check_deadline (sync+async), so lazy loads + re-checks proceed past an expired deadline (rows + 7 queries pre-fix; sibling seams reject the identical shape). Legs: CR10 summary sentence + hand-resolver root + ResourcePolicy deadline + wire query (sync+async, budget-only instrument, no stash). Fix: 6 lines in types/resolvers.py (import + 5 head/closure calls; no-op unarmed). Battery: 70/70 ceiling + 70/70 floor (66 scratch + 4 permanent live, fail-without-fix/pass-with-fix both cells, revert cmp-identical 22f10c3f, regression 127+168). STOP verified CORRECT by Worker 0: production insertion points sit inside DRY-owned one-sync-boundary hunks (DRY ledger :302/:608/:698/:723; fix diff = exactly the 6 lines) — with one correction: the battery-file +41 is hunt-owned (both defs ledgered, one by name :414, one by content), so path (b)-alt was arguably landable but MOOT (fix blocked; red-without-fix). Handoff preserved verbatim: hunt-ws/reports/d3a1-resolvers-fix.patch (69c965a1) + hunt-ws/reports/d3a1-test_relation_deadline_api.py (f8ebf5d4). Follow-up carried (not in A's fence): resource_policy.py CR10 dash-list gains the seam when the fix lands. A's L1-L5 leads recorded in its report. DIVERGENCE for exchange+W2 (no pre-judgment): A reads CR10's summary sentence as governing unenumerated seams (defect); B reads CR10's dash-list enumeration as bounding (in-contract, executed as a green pin). Facts agree (both behaviorally confirmed the missing check); the contract reading diverges. Exchange dispatched (bounded read-only concurrence both ways; A forbidden from B's sealed evidence and from reproduction attempts).
    - Iteration: 5. EXCHANGE COMPLETE (both read-only, no probes, no edits). A->B-abstract: contract rows AGREE (both); coverage GAP admitted (A's D1/D2 cover framework-built fetches + no-hint controls only — consistent with B's passing control, not contradictory; the consumer-Prefetch branch untested by A). B->A-report: reading CHANGES — B CONCURS with the Low defect (universal sentence governs; dash-list unqualified; purpose sentence resolves ambiguity; B's "collections-only" bound textually unanchored; oversight likelier than decision), concurs on Low/availability-only/fix shape/regression; coverage concurrence with closest-probe map both ways (B-mine-only: the sealed HIGH surface). The CR10 divergence is hunter-resolved (W2 still adjudicates independently). Item set BLOCKED per the sensitive-findings rule (abstract recorded; evidence sealed; Rio decides disclosure — see DECISION REQUEST in Current status). Fenced two-phase W2 dispatched over the VERIFIABLE UNION ONLY (A's fix + A's battery + B's 60 non-sensitive probes via exclusion-copy + B-abstract plausibility from the abstract alone; B's hint file never opened/copied/executed; verdict covers the union and explicitly excludes the sealed defect; the item remains blocked regardless). Workspace hunt-ws/deep-3-authz-verify; expectation hunt-ws/w2-deep-3-authz-expectation.txt; drop gated on contamination check. NO cleanup until Rio answers (B's WS is the evidence seat; A's WS + handoff needed for W2 + landing).
    - Iteration: 6. W2 phase-1 expectation LANDED (23.6 KB: 12 rows W2-D3-R1..R12 with falsifiers + A1-A15 attack plan + cell plan; R6 hint-trust derived from code+contract with a non-overlap pledge; R10 adopts (E)numerated-only — DIVERGING from both hunters' exchange concurrence, which proves phase-1 independence). Contamination check PASS (sole grep hit is the line-27 exposure-log declaration; sealed 13:37:22 before any probe run; the grep-preview exposure disclosed and ruled immaterial; cae99200 resolved as byte-derived fresh — Worker 0 recomputed 18/18 sha pins, all match, gate present; the git-hash-object "broken" claim is environment-local erratum). Hash-pinned cb481f33 (no further modification). Phase-2 drop written (hunt-ws/deep-3-verify-phase2/DIAGNOSIS.txt) with 9 ride-alongs (A-70 replay, A-fix verification + INDEPENDENT CR10 adjudication, B-60 exclusion replay with sealed-file prohibitions, abstract plausibility from the abstract alone, STOP re-derivation, floor, non-sensitive depth, leads, hygiene). Verdict covers the verifiable union and explicitly excludes the sealed defect.
    - Iteration: 7. W2 VERIFIED ON THE VERIFIABLE UNION ONLY (sealed defect explicitly excluded — neither confirmed nor denied; item REMAINS BLOCKED). Expectation-first (12 rows, sealed 13:37:22, contamination PASS, pinned cb481f33, unmodified); phase-2: A-70 replay (63+7 pre-fix with EXACT red IDs, 70/70 post-fix, revert/restore cmp-identical twice) + B-60 exclusion replay (60/60, copy proven hint-free, sealed file never opened/copied/executed) + 17 independent attacks green; fix verified (handoff applies cleanly to 22f10c3f byte-exact, placement/no-op-unarmed/regression 127+168 all confirmed, Low/availability-only concurred); CR10 adjudicated INDEPENDENTLY for universal via the previously-unread spec-047 Decision 9 (enumeration = audit product with explicit carve-outs, "collection resolvers" explicitly rejected as scope — hunters' concurrence consistent but not the basis); B's stale deadline pin flips red post-fix (cross-battery corroboration); STOP re-verified (DRY fingerprints byte-exact; closure insertions inside DRY spans — A's "line-disjoint" over-claims, STOP strengthened); abstract plausibility COHERENT (rows verified to exist with stated content, location the unique hook-unseen-keys site, severity well-formed — explicitly NOT verified); floor re-executed (B37 + A70, 8815-file bed inventory diff clean); leads routed (J1 converged card, A-L2 Dive-1 card, A-L3 Rio wording, A-L4 robustness, A-L5/B-L3 fixtures verified exact, B-L2 to Dive 5); hygiene airtight (zero shared edits all parties). Report delivered truncated at line 264 (delivery defect, verdict unaffected) + completed by bounded followup (118 appended lines, boundary verified). No ledger rows (nothing landed). NO cleanup until Rio answers (evidence seat + handoff + W2 WS all retained).
    - Entry points: permissions.py, mutations/permissions.py, utils/querysets.py (seal + runners), optimizer/_context.py, optimizer/extension.py, optimizer/walker.py, types/resolvers.py (relation re-check), relay.py (node/nodes locate + decode + check_deadline), connection.py, list_field.py, utils/permissions.py (gates), consumers.py (subscription lifetime), mutations/resolvers.py (locate/authorize/decode order).
    - Contract citations: README visibility-and-permissions + node null-with-no-leak + mutation locate not-found + raise-to-deny gate rows; GLOSSARY visibility-boundary/sealed-execution-queryset/djangomodelpermission/plan-cache request-scope-safety entries; point-in-time authorization (glossary djangomutation); R8 post-write re-fetch exemption (deliberate, root only).
    - Actors: anonymous; staff; single-view-perm; no-perm; mid-test granted/revoked (grant/revoke/flap incl. MID-OPERATION); secondary-connection SQL writer (visibility flip + revoke); expired-session subscriber.
    - Input domain: roots, nested lists/connections, node/nodes (mixed-visibility batches), mutations with nested selections under the re-fetched node, cursor replays across actors, totalCount root + nested, filter/order gates (flat + nested + async), subscriptions over Channels (subscribe -> expire/revoke -> next event).
    - Lifecycle and state: per-request actor -> per-execution frame -> cross-request plan cache (cacheable only) -> per-operation state; subscription lifetime across events; revoke/grant/flap between AND within operations.
    - Observations and independent oracle: forbidden rows ABSENT on the wire (never merely errored) with a forbidden-row-exists ORM oracle + staff positive control per probe; denial = top-level GraphQLError byte-compared hidden-vs-missing; second-connection SQL for flip/revoke proofs; communicator event asserts for subscriptions.
    - Dependency edges: every read surface -> apply_type_visibility_* -> seal; mutations -> locate -> authorize -> decode; gates -> request_from_info; plan cache trusts cacheable marks only; relation resolvers trust optimizer-scoped relations only.
    - Applicable cells: default ceiling sqlite (executed); floor-310 (executed); live /graphql/ HTTP + in-process Channels communicator (both executed); PG lock-execution + FAKESHOP_SHARDED=1 stay unverified without Rio's word.
    - Owning files: the entry points above.
    - Prompt (deeper than before): the authz scenario verified No bugs but left reason-only (code-verified, never probed) deferrals and isolated-only shapes. Now, behaviorally: (1) subscribe-then-expire — subscribe over Channels, expire the session / revoke the permission, prove the next event is denied/absent (first pass: cited-not-probed); (2) check_deadline-ahead-of-DB on EVERY read path — node + connection were code-verified only; prove list/nodes/nested/mutation-locate behaviorally, plus cancel/timeout mechanics at those paths; (3) re-derive the no-related_name reverse shapes LIVE with the real c25a34e3 fixtures (first pass: AZ03 isolated-only); (4) mid-operation revoke/flip (visibility evaluated per-operation or per-resolver? pin it either way); (5) nested selections under the R8 re-fetched write root (exemption is root-only — prove nested rows re-scope); (6) nodes() mixed-visibility batches. Falsifier per path: forbidden-absent proof or a confirmed leak with rule-35 legs (sensitive-findings rule armed: client-reachable isolation defect -> abstract blocked report, evidence held in scratch). Out of scope: row-correctness (Dive 1), error shapes (Dive 5), the _DEFAULT combinator flip (Rio decision stands).

- [x] Deep dive 4: sidecar merge and normalization contract
    - Status: verified
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-23, ITEM_BASELINE ffa05511e43f2a3febb395701e8b0a2ca65c8e46, workspace hunt-ws/deep-4-sidecar-merge-r1 (rsync excl. .git/.venv/__pycache__/docs/hunt-ws). Tree at dispatch: ledgered hunt dirt (incl. hunt-owned 5d raises in this dive's files) + DRY concurrent files (incl. DRY one-sync-boundary hunks in filters/sets.py + orders/sets.py — MIXED files, attribution-first, STOP if landing lines are DRY-owned per the dive-3 precedent) + honest_*.txt + this file; dive-3 workspaces retained (blocked item, evidence seat — never open the sealed B evidence: hunt-ws/deep-3-authz-b-r1/d3b/test_d3b_hint.py).
    - Iteration: 2. Worker 1 reported Fixed 1 Low + LANDED (B21 single-lookup overlap misbinding: named generated lookup on an overlap head bound the declared form key — silent wrong rows; fix +14/-1 in FilterSet._normalize_input declared branch; 5 permanent tests). Also: 5d residual link closed (in-process coercion proof), 5 silences re-derived (4 wire-unreachable proven, S-F4 refined to contracted-reachable), gate matrix complete (incl. previously-unpinned permission-first ordering, now a permanent test), R1 watch no-reopen, orders twin clean, live-overlap pin blocked with exact fixture (no new model needed). Worker-0 mechanical checks PASS (item diff vs baseline exactly the 2 files; fix hunk +14/-1 with pre-image ed84cf43 == 5d fence; 11/11 digests match pins; fix sha256 dbbb5ee8 shared == workspace; DRY-in-HEAD verified (5 refs) so no STOP owed; 5 new test defs + 0 removed lines; collection 70 exact; focused 7/7 pass in shared tree; ruff check + format + trailing-commas clean; banned-word + pragma scans clean; no nested hunt-ws; floor untouched; cells honestly stated). Report: hunt-ws/reports/w1-deep-4-sidecar-merge-report.txt. Ledger rows appended. filters/sets.py item marked STALE (verified file changed — bounded re-verify queued after the dive W2). Fresh two-phase Worker 2 dispatched (workspace hunt-ws/deep-4-sidecar-merge-verify; expectation hunt-ws/w2-deep-4-sidecar-merge-expectation.txt; drop gated on contamination check).
    - Iteration: 3. W2 phase-1 expectation LANDED but INVALIDATED by exposure (Worker-0 brief defect, not worker fault: the item block lays Iteration lines BEFORE the scope detail, so the "stop at the first Iteration line" instruction was unimplementable — the contiguous scope read necessarily exposed the W1 verdict + fix shape pre-seal, honestly self-reported in the expectation's section 2). Contamination check: FAIL (verdict-critical fix shape known pre-seal; the settled-background reads — prior item records, 5d R1-R3 header — were legitimate). Remedy: phase-1 discarded, worker stood down (workspace + expectation file left in place; the file stays as an invalidated artifact), FRESH W2 dispatched with the scope QUOTED IN-BRIEF (the record never needs opening). New workspace hunt-ws/deep-4-sidecar-merge-verify2; new expectation hunt-ws/w2-deep-4-sidecar-merge-expectation-r2.txt (campaign -r2 convention). Lesson recorded: all future W2 briefs quote scope in-brief.
    - Iteration: 4. Fresh W2 phase-1 expectation LANDED (r2, 24.5 KB: contract rows C1-C9 + overlap rule B1-B6 + census C + B21 D + orders E + silences S1-S5 + gates G1-G7 + range + reopen watch + attack plan I1-I8 + cell plan; novel predictions incl. B6 B23-proxy, S3 related-check-first, S4 EXPECTED-REFUTED, S5 docs-flag, G3 raise-before-gates order). Contamination check PASS (forbidden grep hits are fence-declaration lines only; sealed 15:19:34; byte-frozen after pre-drop census run — seal holds, eagerness noted with zero integrity impact; oracle pins 3/3). Hash-pinned 018b6309 (no further modification). Phase-2 drop written (hunt-ws/deep-4-verify-phase2/DIAGNOSIS.txt) with 12 ride-alongs (replay, failability, census, residual link, silences incl. S4 adjudication + S5 docs-flag, corollary-vs-E-OVL-5, orders twin, gates, R1 watch, independent depth, diff audit, 1019+431 spot-verify).
    - Entry points: filters/sets.py, filters/inputs.py, filters/base.py, orders/sets.py, orders/inputs.py, orders/base.py, sets_mixins.py, utils/inputs.py, utils/input_values.py, optimizer/predicates.py.
    - Contract citations: spec-027 per-field operator-bag design + Decision 4 range row; "a declared filter binds ONE form key"; generated-bag merge (_build_input_fields head-grouping); fail-loud shape contracts (_require_list_container, _require_range_patch_filter, range guard, multi-lookup raise); gate raise-to-deny + permission-first ordering.
    - Actors: query authors (wire filter/order arguments incl. declared+generated overlap shapes); FilterSet/OrderSet authors (declared filters, Meta.fields dicts, RelatedFilter/RelatedOrder, check_* gates); direct-Python apply_sync/apply_async callers.
    - Input domain: declared-only, generated-only, and declared+generated same-head (overlap) bags; single-active + multi-active lookup bags; range shapes (mappings/objects/lists/scalars/exotics); CSV arms; null/UNSET/omitted/empty siblings; unknown keys; exclude/metaclass edge declarations; nested RelatedFilter/RelatedOrder trees; async apply.
    - Lifecycle and state: GraphQL coercion -> bag normalization (_normalize_input, _normalize_range_value) -> form binding -> gate checks -> queryset application; no persistent state (pure normalization + registry reads).
    - Observations and independent oracle: normalized form-data patches asserted EXACT (key-by-key) vs hand-derived expectations; wire rows vs direct ORM for overlap queries; django-filter twin behavior for honest shapes; differential pre/post intent NEVER by code-reading alone (execute both eras where a behavior is pinned).
    - Dependency edges: roots -> normalize -> bind -> gates -> apply; predicates.py consumes flat leaves; input_values guards traversal depth; sets_mixins resolves lazy classes and expansions feeding both sidecars.
    - Applicable cells: default ceiling sqlite (executed); floor-310 (executed); live /graphql/ HTTP wherever fakeshop carries the shape (primary tier); PG/sharded inapplicable-by-construction for pure normalization (grep-proven per claim, W2 judges).
    - Owning files: the entry points above.
    - Prompt (deeper than before): the 5d challenge PROVED first-pass reach reasoning wrong once (sets.py "direct-Python only" REFUTED -> overlap-wire via B19/B23) and left a residual link plus an observed-only wrongness. Now: (1) census EVERY declared+generated same-head pair in fakeshop (ItemFilter.category/category__name, EntryFilter.property/property__*, BookOrder shelf__code, any other) — determine which merge into one bag and live-probe the merged ones; close the 5d residual link (Strawberry coercion into the generated bag class) with a live-overlap pin if the shape exists, else record still-blocked (never add example surface); (2) confirm-or-disprove the B21 single-lookup overlap misbinding (icontains value bound under the declared exact key — observed-only, pre-existing) with contract rows FIRST — if it stands it is a wire-reachable wrong-rows defect, the sharpest lead of this dive — plus its orders-side twin; (3) re-derive wire-reachability for EVERY silence the campaign ruled "wire-unreachable" (orders unknown-key silent-drop, orders exclude deferral, first-wins binding, empty-bag {}, CSV sibling guards) — falsifier per silence: a wire probe reaching it or a proof no wire shape reaches it (the method that failed once may not be reused without a second instrument); (4) gate completeness: every check_* gate fires on declared + generated + overlap + nested + async paths (permission-first ordering pinned); (5) reopen-R1 watch: any wire-coercible input reaching either 5d raise through a NON-overlap head reopens that row. Out of scope: error envelope wording (Dive 5), row visibility (Dive 3), hostile-declaration guard posture (5b stands — hostile-only reproducers are robustness rows, no fix).
    - Result: verified. Fixed 1 Low + LANDED (B21 single-lookup overlap misbinding: named generated lookup bound the declared form key — silent wrong rows; +14/-1 reroute in FilterSet._normalize_input + 5 permanent tests). 5d residual link closed (in-process coercion proof with explicit transport-equivalence reasoning); live-overlap pin honestly blocked with exact minimal fixture (no new model needed). 5 silences re-derived with live second instruments (4 wire-unreachable proven; S-F4 refined to contracted-reachable — converged independently by W2); filters-loud/orders-silent posture divergence pinned (no harmonization row); orders twin clean (cookbook-faithful); gate matrix complete (permission-first ordering newly pinned); R1/R2/R3 no-reopen. New-card candidates: B21 corollary (foreign-single on declared-only head — counter-case noted: misbinds unsafely vs ignore-safely family posture) + filters/orders harmonization question. Docs lead: README:283 over-generalizes integer in:[] (W2-executed: ALL rows vs the sentence's NONE). Zero merged heads in fakeshop (64/579/[] recounted + SDL cross-check).
    - Verification: two-phase W2 VERIFIED (fresh r2 after the r1 phase-1 was invalidated by brief-defect exposure — recorded, worker faultless). Expectation-first (contract rows + overlap rule + census + B21 + orders + silences + gates + range + reopen watch + attack plan, sealed 15:19:34, contamination PASS, pinned 018b6309, byte-frozen); phase-2: 70/70 replay both cells + 29 own probes green; failability re-proved (EXACT 5 red IDs x2 cycles + committed 3-red cycle, cmp-identical restores; EXACTLY the B21 rows flip, all 5d rows byte-identical); census recounted (64/579/[] + 666-prefix note); silences all re-derived live; corollary routing concurred; floor re-executed (bed untouched); suites spot-verified (1970 stated scope + 431 + 3 pre-existing errors confirmed identical pre-fix); diff audit exactly 2 files + gates clean. Nits only (numstat 15/1 vs prose +14/-1; W1's "1019" selection unspecified — W2's stated scope subsumes it; drop carried r1-only vocabulary, mapped harmlessly). Ledger rows appended (counts 10/38/2/1 = 51). filters/sets.py marked STALE (bounded re-verify queued next).
    - Cleanup: Removed hunt-ws/deep-4-sidecar-merge-r1, hunt-ws/deep-4-sidecar-merge-verify, hunt-ws/deep-4-sidecar-merge-verify2, hunt-ws/deep-4-verify-phase2; r2 expectation + 2 reports retained; invalidated r1 expectation retained as a recorded artifact; floor-310 kept (proven untouched); unrelated work preserved.

- [x] Deep dive 5: error reporting contract across producers
    - Status: verified
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-23, ITEM_BASELINE 9abcbc1f5ef7abf14d63286f4463abec95e65334, workspace hunt-ws/deep-5-error-reporting-r1 (rsync excl. .git/.venv/__pycache__/docs/hunt-ws). Tree at dispatch: ledgered hunt dirt (incl. the dive-4 B21 fix, now item-re-verified) + externally-landed dive-3 Low (item-re-verified) + E1 reorder (item-re-verified) + DRY concurrent files + honest_*.txt + this file; attribution-first per HUNT.md. Ride-ins: dive-2 L2 + dive-3 B-L2 (GlobalID-scalar masked failure on all legs with correlationId — place this producer in the masking table + code pins; the dive-2 W2's D3 battery was removed with its WS, re-drive from the wire shape). Dive-3 sealed evidence stays sealed (never open hunt-ws/deep-3-authz-b-r1/d3b/test_d3b_hint.py).
    - Iteration: 2. Worker 1 reported No bugs (12 contract rows; ride-in placed as C4 conformance with log linkage + byte-identity on 6 legs + M2M + async; masking table proven live row-by-row; seam neighborhood exact incl. renamed-serializer message+code+path; rejection codes + ListArgumentError vocabulary + transport + per-event masking all pinned live; 6 permanent pins, 4 defs + 0 removals, tests-only, no production touched). Worker-0 mechanical checks: item diff exactly the 2 test files; 20/20 digests match; test_products_api.py drift-free vs baseline (the W1-cited concurrent hunk predates the baseline); collection 29 exact; focused 6/6 pass in shared tree; ruff check + format clean; banned-word + pragma scans clean; no nested hunt-ws; floor untouched — BUT 1 trailing-commas gate violation in added lines (test_error_policy_api.py:1329 over-exploded def, 92 collapsed chars). Recycled to the SAME Worker 1 for a bounded test-side revision (collapse by hand, re-gate, re-run pins). Report: hunt-ws/reports/w1-deep-5-error-reporting-report.txt.
    - Iteration: 3. Revision COMPLETE (same worker): def collapsed 5 lines -> 1 (92 chars) by hand; ruff check + format --check + trailing-commas --check all clean; focused 6-pin run green. Worker-0 verified: item diff still exactly the 2 test files (+89/+43); gates clean; new digest a8331a9d. Fresh two-phase Worker 2 dispatched with scope QUOTED IN-BRIEF (workspace hunt-ws/deep-5-error-reporting-verify; expectation hunt-ws/w2-deep-5-error-reporting-expectation.txt; drop gated on contamination check).
    - Iteration: 4. W2 phase-1 expectation LANDED (31.8 KB: 5-row table A1-A6 with falsifiers + per-producer ownership map B (D3 malformed-relation->Row-4 DERIVED independently, converging with W1) + seam exactness C1-C8 (key-only asserts VOID) + rejection codes D1-D5 + transport E1-E4 + subscriptions F1-F3 + attack plan G1-G10 + cells + contradiction statement). Contamination check PASS (sole grep hit is the line-10 fence declaration; sealed 16:56:27 before any probe run). Hash-pinned c2ae6f05 (no further modification). Phase-2 drop written (hunt-ws/deep-5-verify-phase2/DIAGNOSIS.txt) with 11 ride-alongs (replay, placement re-derivation, N>=10 uniqueness, hook seam, seam neighborhood, rejection codes, transport + E11 claim, subscriptions, in-process-only producers, routings + diff audit, floor).
    - Entry points: utils/errors.py (mapper seam + relation/null/surrogate errors), mutations/resolvers.py, forms/resolvers.py, rest_framework/resolvers.py, auth/mutations.py (all error-label call sites), error_policy.py, extensions/error_policy.py, exceptions.py, resource_policy.py + extensions/resource_policy.py (rejection codes), relay.py + types/relay.py (GLOBALID_INVALID), list_field.py (ListArgumentError), filters/sets.py + orders/sets.py (FILTER_INVALID vs query-time ConfigurationError), schema.py (hook-masking seam), consumers.py + routers.py (transport rejections).
    - Contract citations: docs/README production-error-policy table (5 rows: parse/validation unchanged; framework GraphQLError unchanged + code; own GraphQLError unchanged; other -> policy message + correlationId; envelopes are data); GLOSSARY FieldError envelope (byte-identical shape, wire-name keying per R1/R2); RESOURCE_LIMIT_EXCEEDED / GLOBALID_INVALID / FILTER_INVALID code pins; ListArgumentError reason vocabulary; masking-after-teardown ordering + per-event subscription masking.
    - Actors: API clients (correct, malformed-document, over-budget, unauthenticated, wrong-password, invalid-relation-id authors); staff vs anon (denial byte-identity); server operator (log linkage via correlationId).
    - Input domain: every failure producer: validation envelopes (model/form/serializer/auth incl. nested/relation/non-field errors, null-vs-invalid relation ids); auth denials; resource rejections (document/value/collection bounds); globalid malforms; list-argument violations; filter-invalid inputs; unexpected resolver/hook exceptions (DEBUG on/off); transport rejections (body caps, nested documents, multipart); subscription event failures.
    - Lifecycle and state: error raised -> envelope-or-top-level decision -> masking pass (extension first, hook seam on schema) -> wire; per-operation isolation of policy extensions; per-event masking on subscriptions; log emission under correlationId.
    - Observations and independent oracle: wire errors/extensions asserted EXACT (message + code + field + correlationId presence/uniqueness) per producer; log capture asserting the masked original + traceback under the same correlationId; DEBUG-on vs DEBUG-off differential; pre/post intent for the integration seam via WS-only revert (differential method — no survey may stand in for execution).
    - Dependency edges: producers -> envelope mapper / top-level raise -> policy extensions -> wire; hook exceptions bypass extensions to the schema seam; transport guards precede parsing; subscription events re-enter masking per event.
    - Applicable cells: default ceiling sqlite (executed); floor-310 (executed); live /graphql/ HTTP (primary tier — every row must be wire-proven); Channels event assertions in-process; PG/sharded stay unverified without Rio's word.
    - Owning files: the entry points above.
    - Prompt (deeper than before): each producer was hunted alone; the ERROR TABLE was never verified as a table, and the integration seam (wire-name re-key across 5 verified files) landed after most verifications with in-unit-only coverage. Now: (1) prove the README 5-row masking table LIVE, row by row, incl. DEBUG-off masking + correlationId uniqueness + server-log linkage under the same id, and the hook-seam (schema, not extension) ownership; (2) re-attack the integration seam neighborhood: nested errors, relation errors, non-field errors, null-vs-invalid relation ids, auth-mutation errors — across ALL flavors + auth, asserting wire-name keying AND message exactness (the R2(c) lesson: key-only asserts pass under their own counterfactual); (3) pin every rejection code live (RESOURCE_LIMIT_EXCEEDED incl. refused-schema-still-bounded; GLOBALID_INVALID incl. malformed/exotic/secondary-collapse; FILTER_INVALID vs query-time ConfigurationError — map which producer emits which, and record the family-envelope question WITHOUT relitigating it); (4) ListArgumentError reason vocabulary live (order_required + unreadable-order refusal); (5) transport rejections live (body caps, nested bodies, multipart); (6) subscription per-event masking + per-event isolation. Falsifier per producer: exact wire shape proven or a confirmed contract break with rule-35 legs. Out of scope: input acceptance parity (Dive 2), visibility decisions (Dive 3), the naming posture (blocked, Rio decides — never touch mutations/sets.py + mutations/fields.py naming hunks or the :211 pin).
    - Result: verified. No bugs. The error table verified as a table: all 5 masking rows proven live (per-error correlationId uniqueness, fail-closed malformed DEBUG, custom message/key, masker-first ordering, refused SCHEMA_CONFIGURATION_UNAVAILABLE); hook seam owned by schema (C8 pair pins — plain-schema negative previously unpinned); per-event masking + copy semantics; transport (413 counted-bytes + multipart carve-out, UTF-8 400, map shape); ListArgumentError vocabulary (order_required for absent AND unreadable); FILTER_INVALID producers mapped vs masked ConfigurationError (family-envelope question recorded, not relitigated); seam neighborhood exact (keys+messages+codes+path together) incl. renamed-serializer message+code+path; rejection codes live (RESOURCE incl. refused-still-bounded live pin, GLOBALID exotics, FILTER_INVALID detail + Row-1 split). Ride-in placed as C4 CONFORMANCE (malformed relation GlobalID fails in Strawberry arg conversion as plain ValueError → masked with correlationId + log linkage, byte-identical 6 legs + M2M + async, no-write; documented split cited) — independently derived AND re-proven by W2 on 8 legs with neighbors differing. 6 permanent pins (2 package + 4 live nodes), tests-only, no production touched. Strongest new probes: W2's N=12 uniqueness battery (12 distinct ids + 12 matched logs), 5-cause login byte-identity, hook 8-halves ordering witness, DEBUG-flip-mid-stream subscription proof. Errata (not challenges): sync nested-body twins ALSO error on this interpreter (5 defs / 6 items fixture-unexercisable — W1's "sync twin green" wrong); secondary collapse already live-pinned (W1 understated); UNVALIDATABLE live row impossible by construction (finalizer audit — closed as inapplicable, NOT a Rio blocked line). No ledger rows (tests-only pins for a No-bugs verdict — authz/pagination precedent; pins named here for the sweep).
    - Verification: two-phase W2 VERIFIED, no challenges. Expectation-first (31.8 KB: table + ownership map + seam exactness with key-only asserts VOID + codes + transport + subscriptions + attack plan, sealed 16:56:27, contamination PASS, pinned c2ae6f05, unmodified); phase-2: 28/29 replay (1 workspace-coupled anchor artifact, judged mechanical) + 63 own probes green (9+13+8+17+12+4); every placement re-derived live; floor re-executed read-only (16 nodes, bed-untouched via before/after snapshot; bed drift vs BUILD.md recorded — 5.2.17 + 0.327.7, direction holds; new pins compile-only at floor since the bed predates them); PG/sharded judged inapplicable-by-construction per claim family (formally unverified). W1 recycled once for a bounded test-side gate fix (over-exploded def collapsed; all gates clean). No stale triggers (zero production edits).
    - Cleanup: Removed hunt-ws/deep-5-error-reporting-r1, hunt-ws/deep-5-error-reporting-verify, hunt-ws/deep-5-verify-phase2, hunt-ws/w2-deep-5-floor-bed/ (bed snapshots; method + outcome in the report); expectation file + 2 reports retained; floor-310 kept (proven untouched); /tmp/d5_probe_shape.py left (superseded W1 scratch print in OS temp, volatile, ignored); unrelated work preserved.

## Integration and final gate


- [x] Package integration
    - Status: verified
    - Prompt:
        - Hunt the final live package across boundaries, including public exports and `__init__.py` files; implement every confirmed root-cause fix.
    - Iteration: 1. Fresh Worker 1 dispatched 2026-09-23 UTC, ITEM_BASELINE 2aa42403, workspace hunt-ws/integration (cross-boundary hunt: lifecycle phases, double-owned state, circular init, divergent flavors, impl/tests/examples/docs gaps; re-inventory attached — 9 added + 1 removed .py, all main-side examples/scripts, zero package/tests structural change; digest-vs-record sweep required step 1, stale flags to Worker-0, no unilateral flips). W2 verification follows in-unit.
    - Iteration: 2. Worker 1 reported Fixed Low, 1 defect in Area D (model + form flavors keyed validation `FieldError.field` by Django snake_case while serializer + relation/null errors key by GraphQL wire name; root-cause fix at the shared `validation_error_to_field_errors` seam via optional `field_name_map` + per-flavor maps; Areas A-C No bugs). Files changed: 5 production (auth/mutations.py 93752409, forms/resolvers.py be9632e7, mutations/resolvers.py 80dbee45, rest_framework/resolvers.py 81241de4, utils/errors.py d4f4b6b2) + 3 tests (mutations/test_resolvers.py b8ef2b69, rest_framework/test_resolvers.py 63002e1a, test_library_api.py d3386f14; 4 new tests: 1 live + 3 package). Sweep verdict CLEAN (zero unexplained mismatches — W2 to re-derive). Worker-0 mechanical checks pass (item diff vs 2aa42403 exactly the 8 files + progress file; all 8 sha256 match W1 section 6; index lines match; focused 4/4 green — re-run by Worker-0; ruff check + format clean on all 8 — re-run by Worker-0; pragma counts identical pre/post, no new pragma). Fresh Worker 2 verification dispatched (ITEM_BASELINE bb993f4b, workspace hunt-ws/integration-verify).
    - Iteration: 3. Worker 2 verdict: REVISION-NEEDED, test-side only (8/9 criteria pass; production fix verified-correct, stands as-is). K6 FAIL: 3 existing tests pin the old snake/Django keying and break post-fix (forms/test_resolvers.py:666 `["category"]`, mutations/test_resolvers.py:1138 `"object_id"`, test_products_api.py:3787 `"category"` + leak-enshrining docstring); W1's "existing-test safety" claim materially false (survey blind spot: single-word Django≠wire pins). Remedy (exact): update the 3 pins to wire names + reword the products_api docstring to the message/code distinction; production hunks UNTOUCHED. Out-of-scope findings for Worker-0: 1 pre-existing list_field hostile-metaclass failure (identical pre/post) + 11 environmental conftest stack-probe errors (identical pre/post) — gate-time triage. Shared tree never edited by W2 (fences re-hashed 8/8; fence-vs-bb993f4b empty). Report: hunt-ws/reports/w2-integration-report.txt. Fresh narrow Worker 1 re-pass dispatched (ITEM_BASELINE a6862498, workspace hunt-ws/integration-repass; test-side only).
    - Iteration: 4. Worker 1 re-pass landed (exact W2 remedy, test-side only: forms :666 -> `["categoryId"]`, mutations :1138 -> `"objectId"` + comment, products_api docstring reworded to message/code + `categoryId` pin; tests e6677d42/d702057c/5dd2cc04, all 5 production guards byte-identical). Full suite 3 failed + 8862 passed + 42 skipped + 11 errors, decomposed: (a) pre-existing list_field failure identical pre/post, (b) 11 environmental conftest errors identical pre/post, (c)+(d) 2 census-contamination failures attributed to concurrent scratch (proven red without the re-pass workspace; version-census passes hunt-ws-free, sweep-census fails on 1_introspect.py alone) — gate-time triage. Worker-0 mechanical checks pass (item diff vs a6862498 exactly the 3 test hunks + progress; production diff empty; all 8 digests match; focused 3/3 green — re-run by Worker-0; ruff check + format clean on all 3 — re-run by Worker-0; no new pragma). Note: W1 ledger shows another out-of-role `git stash create` (harmless — writes no ref). Fresh Worker 2 re-verification dispatched (ITEM_BASELINE c2bff9e4, workspace hunt-ws/integration-repass-verify; K6/K8 re-verify + report audit).
    - Iteration: 5. Worker 2 re-verdict: REVISION-NEEDED, narrow test-side-only, test 3 only (R1/R3/R4/R5/R6 pass; tests 1-2 fully verified; production untouched). R2 FAIL: the products_api null-FK test no longer proves its contract — post-fix both paths key `categoryId` with node null (wire-proven), while the body asserts the key only, so it passes under the counterfactual it was written to exclude; "message/code is load-bearing" unenforced. Remedy (exact): add a required-message pin on the categoryId-keyed error (`by_field["categoryId"] == ["This field is required."]`) + failability proof against the invalid-id payload `["Invalid id for relation 'categoryId'."]`; optional docstring "message/code" -> "message". Shared tree never edited by W2 (fences re-hashed 8/8; fence-vs-c2bff9e4 = progress file only). Report: hunt-ws/reports/w2-integration-repass-report.txt. Fresh narrow Worker 1 re-pass-2 dispatched (ITEM_BASELINE 4d3dfc79, workspace hunt-ws/integration-repass-2; test 3 only).
    - Iteration: 6. Worker 1 re-pass-2 landed (exact R2 remedy, test 3 only: dict-form required-message pin `by_field["categoryId"] == ["This field is required."]` + docstring "message/code" -> "message" after verifying codes unselected; test_products_api 5dd2cc04 -> f57d9a0a, all 7 guards byte-identical). Failability proven both directions (invalid-gid counterfactual payload pinned exactly `["Invalid id for relation 'categoryId'."]`; landed pin reddens on it). Module run 162 passed + 3 pre-attributed stack-probe errors. Worker-0 mechanical checks pass (item diff vs 4d3dfc79 exactly the 1 file + progress; package+tests diffs empty; digests match; focused 1/1 green — re-run by Worker-0; ruff check + format + trailing-commas clean — re-run by Worker-0; no new pragma). Fresh Worker 2 narrow re-verification dispatched (ITEM_BASELINE 7e6ff4a1, workspace hunt-ws/integration-repass-2-verify; R2(c) only per the prior W2's scoping: pin present + discriminating + gates clean).
    - Iteration: 7. Worker 2 narrow VERIFIED unconditional (expectation-first, N1-N5 all PASS, zero discrepancies: exact 1-test hunk; pin present in preferred dict form + docstring tighten proven accurate from the query bytes; own 2-shape live probe confirms the counterfactual payload + old key-only assertions pass under it + landed pin reddens raw on the pin line; touched test green + module 162P + 3 pre-attributed errors; all 3 gates clean; full report audit). Shared tree never edited by W2 (fences re-hashed 8/8; fence-vs-7e6ff4a1 empty). Report: hunt-ws/reports/w2-integration-repass-2-report.txt. Item CLOSED.
    - Result: Fixed Low. Files changed: 5 production (auth/mutations.py 93752409, forms/resolvers.py be9632e7, mutations/resolvers.py 80dbee45, rest_framework/resolvers.py 81241de4, utils/errors.py d4f4b6b2 — shared-seam wire-name re-key) + 5 tests (4 new: 1 live + 3 package; 3 stale pins updated + 1 message pin added: forms/test_resolvers.py e6677d42, mutations/test_resolvers.py d702057c, rest_framework/test_resolvers.py 63002e1a, test_library_api.py d3386f14, test_products_api.py f57d9a0a). Areas A-C No bugs.
    - Verification: Passed after two test-side revision rounds (K6 stale pins → remedy → R2(c) message pin → verified). Expected-before-diagnosis: hunt-ws/w2-integration-expectation.txt + hunt-ws/w2-integration-repass-expectation.txt + hunt-ws/w2-integration-repass-2-expectation.txt. Evidence: hunt-ws/integration*/ records (removed post-verify), post-fix digests above.
    - Cleanup: Removed hunt-ws/integration, hunt-ws/integration-verify, hunt-ws/integration-repass, hunt-ws/integration-repass-verify, hunt-ws/integration-repass-2, hunt-ws/integration-repass-2-verify; reports + expectation files retained in hunt-ws/ until closeout; unrelated work preserved.

- [ ] Final test gate
    - Status: pending
    - Owner: Worker 0
    - Prompt:
        - Run `uv run pytest`; require a passing suite and 100% configured package coverage.

## Owned changes

Path, item, symbols for every tracked edit or new file a verified item landed. A later item may build on a path listed here; any other dirty hunk is external.

- tests/utils/test_querysets.py — Baseline failure: collection-time model fixture isolation — Class: stale-row. `_proxy_target_apps`, `_ProxyTargetCategory`, `_ProxyTargetHolder`, `test_proxy_target_fixtures_leave_category_relations_unchanged`, `test_proxy_target_fixtures_allow_category_deletion`.
- django_strawberry_framework/connection.py + tests/test_connection.py — connection.py — Class: defect. `_offset_cursor_prefix`, `_reject_negative_offset_cursor`, `_consume_fallback` negative-cursor hook, `test_consumer_resolver_sequence_negative_cursor_raises_graphql_error`.
- django_strawberry_framework/extensions/resource_policy.py + tests/test_resource_policy.py + examples/fakeshop/test_query/test_resource_policy_api.py — extensions/resource_policy.py — Class: defect. `_charge_directive_values`, `_referenced_variables`, `charge_document` directive/default charging, 7 unit tests, live `/rp-values/` row.
- django_strawberry_framework/filters/inputs.py + tests/filters/test_inputs.py — filters/inputs.py — Class: robustness. `_normalize_range_value` fail-loud guard, 5 range-shape tests.
- django_strawberry_framework/filters/sets.py + tests/filters/test_sets.py — filters/sets.py — Class: robustness. declared-form-key active-entry guard, 1 two-lookup test.
- django_strawberry_framework/forms/inputs.py + tests/forms/test_inputs.py — forms/inputs.py — Class: robustness. `_form_field_basis` guarded per-value loop, `test_basis_diagnostic_typed_for_hostile_class_value`.
- django_strawberry_framework/forms/sets.py + tests/forms/test_sets.py — forms/sets.py — Class: robustness. 8 safe-renderer swaps, 10 hostile-name tests.
- django_strawberry_framework/mutations/fields.py + tests/mutations/test_fields.py — mutations/fields.py — Class: robustness. guarded `isinstance`, wrapped protocol probe, `_safe_class_name` labels, guarded own-`__dict__` read, identity-scan ledger, Payload safe label, 6 hostile tests.
- django_strawberry_framework/mutations/resolvers.py + tests/mutations/test_resolvers.py — mutations/resolvers.py (stale re-pass) — Class: robustness. 7 safe-label swaps, 8 hostile-name tests.
- django_strawberry_framework/mutations/sets.py + tests/mutations/test_sets.py — mutations/sets.py — Class: robustness. 6 `__name__` → `_safe_class_name` hunks, 5 hostile-name tests.
- django_strawberry_framework/auth/mutations.py + tests/auth/test_mutations.py — auth/mutations.py (stale re-pass) — Class: robustness. 7 safe-class swaps + 1 safe-value join, 7 hostile tests.
- django_strawberry_framework/optimizer/hints.py + tests/optimizer/test_hints.py — optimizer/hints.py — Class: robustness. guarded `isinstance` in `_require_prefetch`, 1 class-liar test. Forwarded leads: `types/base.py` bare-`isinstance` trio (carried by that pending item) + `strategy(__class__-liar)` raw escape via `nested_fetch.py:439` (carried by that pending item).
- django_strawberry_framework/optimizer/join_taxonomy.py + tests/optimizer/test_join_taxonomy.py — optimizer/join_taxonomy.py — Class: defect. `_child_link_is_virtual` + three guarded degrade sites, 4 classification + 1 execution test. Blocked: live-tier row wants a composite-PK/`ForeignObject` fakeshop fixture; Rio decides.
- django_strawberry_framework/optimizer/nested_fetch.py + tests/optimizer/test_nested_fetch.py — optimizer/nested_fetch.py — Class: robustness. `issubclass(type(), str)` + guarded `isinstance(value, type)` strategy gates, 2 liar/spoof tests. Maintainer edit 2026-09-22: 29ce5201→d67e8d9d (arm deletion), verdict stands.
- django_strawberry_framework/optimizer/nested_planner.py + tests/optimizer/test_nested_index_advisory.py — optimizer/nested_planner.py — Class: defect. M2M silent gate in `_advise_composite_index`, discriminating test + taxonomy pin. Blocked: live-tier M2M-ordering row wants a fakeshop fixture; Rio decides.
- django_strawberry_framework/rest_framework/resolvers.py + tests/rest_framework/test_resolvers.py — rest_framework/resolvers.py — Class: robustness. guarded hook-boundary interrogations + safe renderers, 7 hostile-hook tests (iterations 1–2) + 53 safe-label swaps, 23 hostile-label tests (stale re-pass iterations 3–5). New-card candidates (robustness rows, out of slice): hostile-`__str__` dict key at `_error_node_children::str(key)`; hostile-`__repr__` custom-`save()` return at `{saved!r}`.
- django_strawberry_framework/rest_framework/sets.py + tests/rest_framework/test_sets.py — rest_framework/sets.py — Class: robustness. safe renderers + guarded interrogations + identifier gate, 10 hostile/identifier tests. Maintainer edit 2026-09-22: def19a9e1→70a1e1b1 (arm deletion), verdict stands.
- django_strawberry_framework/sets_mixins.py + tests/test_sets_mixins.py + tests/filters/test_base.py + tests/orders/test_base.py — sets_mixins.py — Class: robustness. 4 guarded seams + bind helper; family gate guards in filters/base.py + orders/base.py; 10 hostile tests. Residual lead (robustness, out of diff): end-to-end `Meta.fields` raising-liar at filters/sets.py get_fields + utils/inputs.py canonicalize + upstream django_filters — carried by the pending utils/inputs.py item with a bounded stale-check note on filters/sets.py.
- django_strawberry_framework/routers.py + tests/test_routers.py — routers.py — Class: robustness. guarded seam interrogations, 4 hostile-interrogation nodes. Maintainer edit 2026-09-22: d5c43509→bc30430e (arm deletion), verdict stands.
- django_strawberry_framework/types/base.py + tests/types/test_base.py — types/base.py — Class: robustness. guarded optimizer_hints gates + helper + safe label, 1 honest pin + 7 liar tests (iterations 1–2) + collection-seam guards + label swaps + 2 shape-error labels, 43 + 2 hostile nodes (stale re-pass iterations 4–7). New-card candidates: non-string hostile annotation key at string-keys gate; keyset cursor evil-str downstream. Robustness rows noted (N1/N2/N3/N5/N4 adjacent-gate liar shapes — card fodder, not blockers). Foreign spec-015 hunks in the same file untouched.
- django_strawberry_framework/types/converters.py + tests/types/test_converters.py — types/converters.py — Class: robustness. 5 guarded interrogations + doc bullets, 6 liar/spoof/unreadable tests.
- django_strawberry_framework/utils/connections.py + examples/fakeshop/test_query/test_library_api.py — utils/connections.py — Class: defect. `bool()` cursor presence + parity comment, 1 live test.
- django_strawberry_framework/types/definition.py + tests/types/test_definition_relations.py — types/definition.py — Class: robustness. 4 guarded seams, 4 liar tests.
- django_strawberry_framework/types/finalizer.py + tests/types/test_finalizer.py — types/finalizer.py — Class: robustness. guarded `_field_surface_names` interrogation, 2 hostile-attribute tests. Robustness row noted (order-dependent cross-model FilterSet-inheritance silent bind — benign everywhere reachable, fixing rejects working builds; not a blocker). Foreign globalid-snapshot docstring hunk in the same file untouched.
- django_strawberry_framework/rest_framework/serializer_converter.py + tests/rest_framework/test_converter.py — rest_framework/serializer_converter.py — Class: defect. nullable-element widening, allow_blank exclusion, 6 safe-name swaps; 2 conversion + 4 hostile tests. Blocked: live-tier D1/D2 rows want fakeshop serializer fixtures; Rio decides.
- tests/rest_framework/test_sets.py — Lint ledger item (trailing-comma layout) — Class: lint. exploded two 4-element parametrize lists one-per-line (whitespace-only, AST-identical); CI lint gate green.
- tests/types/test_base.py — Lint ledger item (trailing-comma layout) — Class: lint. collapsed one over-exploded 3-element meta-attrs dict (whitespace-only, AST-identical); CI lint gate green.
- django_strawberry_framework/utils/directives.py + tests/utils/test_directives.py — utils/directives.py — Class: robustness. char-wise interrogation inside the single containment + docstring paragraph, 3 hostile-class tests.
- django_strawberry_framework/utils/errors.py + tests/utils/test_errors.py — utils/errors.py — Class: robustness. guarded per-field atom interrogation in `validation_error_to_field_errors`, 2 hostile-class mapper tests.
- django_strawberry_framework/utils/input_values.py + tests/utils/test_input_values.py — utils/input_values.py — Class: robustness. `str.__str__` label coercion with `_safe_type_name` fallback in `raise_set_traversal_depth_exceeded`, 1 hostile-qualname test.
- django_strawberry_framework/utils/inputs.py + tests/utils/test_inputs.py — utils/inputs.py — Class: robustness. D1 `canonicalize_set_meta_fields` liar read + D2 factory mapping gates + D3 `_hashable_meta_value` dispatch + D4 field-name-sequence dispatches + D5 dynamic-class model gate + D6 lazy-annotation subclass check + D7 six label sites via `_safe_class_name` + new `_safe_module_qualname`, 13 hostile tests.
- django_strawberry_framework/filters/sets.py + tests/filters/test_sets.py — utils/inputs.py (D8 bounded seam) — Class: robustness. get_fields pre-check `is_str` guard (+10/-1), 1 appended liar test; rides with the inputs verification.
- django_strawberry_framework/utils/policies.py + tests/utils/test_policies.py — utils/policies.py — Class: robustness. 4 guarded `isinstance` reads in `resolve_policy` + `str.__str__` subclass-key normalization with typed "key comparison failed" arm, 7 hostile tests (5 + 2 coverage-revision).
- django_strawberry_framework/utils/querysets.py + tests/utils/test_querysets.py — utils/querysets.py — Class: robustness. 2 `_safe_class_name` label swaps in `_apply_sidecar_sync`/`_apply_sidecar_async`, 5 hostile-set-name tests.
- django_strawberry_framework/utils/strings.py + tests/utils/test_strings.py — utils/strings.py — Class: robustness. guarded `isinstance` + `str.__str__` reads in `_plain_text` with typed rejections (KI/SI propagate) + contract docstring, 4 liar tests (13 nodes).
- django_strawberry_framework/utils/sessions.py + tests/utils/test_sessions.py — utils/sessions.py — Class: robustness. guarded `isinstance` gate + flatten-before-truthiness + guarded flatten in `session_store_class` + widened docstring, 8 engine-shape tests.
- django_strawberry_framework/utils/write_transaction.py + tests/mutations/test_write_transaction.py — utils/write_transaction.py — Class: robustness. import + 5 `_safe_class_name` label swaps at the refusal-message seams, 5 hostile-name tests.
- django_strawberry_framework/extensions/resource_policy.py + tests/test_resource_policy.py + examples/fakeshop/test_query/test_resource_policy_api.py — extensions/resource_policy.py (stale re-pass) — Class: defect. spread-site charge above the unresolvable/cyclic guard + comment + docstring clause, 3 unit + 1 live spread-charging test.
- django_strawberry_framework/filters/base.py + tests/filters/test_base.py — filters/base.py (stale re-pass) — Class: robustness. guarded owner `isinstance` in the rejection label + docstring, defect + pass-path pin tests.
- django_strawberry_framework/list_field.py + tests/test_list_field.py — list_field.py (stale re-hunt) — Class: robustness. 4 contained interrogations in `_validate_djangotype_target` + docstring, 4 hostile-target tests.
- django_strawberry_framework/orders/base.py + tests/orders/test_base.py — orders/base.py (stale re-pass) — Class: robustness. guarded owner `isinstance` in the rejection label + docstring, defect + pass-path pin tests.
- django_strawberry_framework/filters/sets.py + tests/filters/test_sets.py — filters/sets.py (stale re-pass) — Class: robustness. 19 safe label renderers + `not (==)` narrowing guard + comment/NOTE, 23 hostile tests (19 + 4 C1).
- django_strawberry_framework/orders/inputs.py + tests/orders/test_inputs.py — orders/inputs.py (stale re-pass) — Class: robustness. `_safe_class_name(qualified=True)` label read + import, 2 hostile tests.
- django_strawberry_framework/orders/sets.py + tests/orders/test_sets.py — orders/sets.py (stale re-pass) — Class: robustness. 10 safe label renderers + `cls_label` hoist + guarded `==` shorthand gate, 15 hostile tests.
- django_strawberry_framework/types/base.py + tests/types/test_base.py — types/base.py (stale re-pass, iterations 8–10) — Class: robustness. guarded `cls.__mro__` read + docstring clause in `_detect_custom_get_queryset`, `_RaisingMROMeta` helper + 2 hostile tests. O1 (finalizer/relay raw `__mro__` reads) confirmed HAS STANDING by W2 as a correctly-forwarded lead, carried by the running finalizer re-pass; O2 (lying non-raising `__mro__`) a robustness row (new card at most).
- django_strawberry_framework/types/finalizer.py + tests/types/test_finalizer.py — types/finalizer.py (stale re-pass, iterations 3–5) — Class: robustness. inherited-surface guard in `_field_surface_names` (mro snapshot + walk → typed `ConfigurationError`), 2 O1 hostile tests. Routed lead (robustness row, out of fence): Node-shaped hostile-`__mro__` detonates raw first at relay-owned seams (relay.py:154 `apply_interfaces` pre-scan + :245 upstream scan) — no Decision-1 row violation (promises TypeError-from-assignment only), relay stays verified, Low-at-most even if a row is later named.
- django_strawberry_framework/sets_mixins.py + tests/test_sets_mixins.py — sets_mixins.py (stale re-pass, iterations 6–8) — Class: robustness. hoisted `_safe_class_name(qualified=True)` gate label + guarded `bool(bound_class)` (`except BaseException → False`) + import + docstring, 9 hostile tests (4 gate-label + 4 bool-owner + 1 honest-matrix pin). New-card candidate (robustness row, non-blocking): harden `resolve_lazy_class` attempt-2 assembly against hostile `bound_class.__module__` (raw RuntimeError replaces the attempt-2 ImportError; real-path repro both families; remedy a Rio design decision — safe-render the module so unresolvable strings stay ImportError, no treat-as-unbound contradiction).
- django_strawberry_framework/utils/querysets.py + tests/utils/test_querysets.py — utils/querysets.py (stale re-pass, iterations 5–7) — Class: defect. `reject_combined=True` on `_LIST_RELATION_CHILD_POLICY` + 5 prose restatements, 3 combinator tests (5 nodes) + preset-matrix pins + 5298 rewording. `_DEFAULT` 9-surface census confirmed-and-reported, NOT flipped (recorded Rio decision; F4 order-by-expression raw `TypeError` extends the census within deferred scope). Follow-ups (non-blocking): F1 walker one-axis prose now false (prose-only, no behavior-stale); F3 kept slice-after-ordering sentence acceptable (one family card advised).
- django_strawberry_framework/schema.py + tests/test_schema.py — Scenario: Transaction and session lifecycle — Class: defect. `_drive_window_transition` driver + `_settle_window_if_open` guard + `_cancel_all_but_current` helper; 11 window rows (4 reworked + 7 new incl. teardown pin); R1/R2/R3 record corrections (Defect-2 errata, tiered severity + ThreadSensitiveContext mechanism, contract rows). 9th defect row (5b classified the first 48; legs accepted by W2).
- django_strawberry_framework/types/base.py — types/base.py (armcut re-pass) — Class: robustness. DELETED 4 test-unreached `except BaseException` arms (relation-shapes items, auto-annotation string-form, Relay-id assignment, optimizer-hints per-key) + fixed 2 prose spots (docstring spaces, bool-finality comment); no behavior change on any feasible shape, tests byte-identical, module coverage 602/602. Ledger counts now 9 defect / 38 robustness / 2 lint / 1 stale-row = 50.
- django_strawberry_framework/filters/sets.py (Deep dive 4) — Class: defect (Low). Overlap-head single foreign lookup binds the generated form key (was: declared key — silent wrong rows, B21 with rule-35 legs L1 spec-027:292 attr->lookup mapping, L2 public-API overlap shape, L3 same wire path as 5d). +14/-1 in FilterSet._normalize_input declared branch; multi-raise, declared-own binding, and non-overlap behavior unchanged.
- tests/filters/test_sets.py (Deep dive 4) — Class: defect (Low). +5 (overlap dataclass, overlap mapping, overlap rows-vs-twin, declared-own no-regression, denial-precedes-validation). Ledger counts now 10 defect / 38 robustness / 2 lint / 1 stale-row = 51.

## Outcomes

Restart authorized and generated from HEAD; the "no verdicts, no fixes, no source changed"
statements below this paragraph describe the restart point, not the present. As of the
2026-09-21 ~22:45 resume: 75 file items + 2 scenario items verified, 16 file items stale
(9 pre-existing + 7 from the 69a25369..24e6b4d3 fast-forward; filters/sets.py narrowed to the non-D8 region), 2 items
hunting (utils/permissions.py in W2 verification, utils/policies.py in fresh W1 hunt),
9 file items pending, 2 scenarios + integration + final gate pending. The `## Owned
changes` ledger holds 32 rows of verified hunt fixes (production guards + permanent
tests + live rows); every one of those tracked edits is uncommitted hunt dirt in the
shared tree. "Selected campaign complete" + the unexamined list will replace this
paragraph at closeout — never whole-package clearance.

Scope: maintainer approved defensive correctness review including baseline failures,
excluding autonomous vulnerability discovery and exploit reproduction (header Scope
decision). The historical Blocked paragraph below is superseded; no completed hunt
verdict is implied by it.

Blocked (historical, superseded): the requested workflow includes autonomous
vulnerability discovery and exploit reproduction. Continuing requires a narrower
defensive correctness-review scope; this record must not be represented as a completed
full hunt.

An early shared-tree baseline run of `uv run pytest` was performed, not the final gate:
17 failed, 8289 passed, 41 skipped, exit 1, 209.95 seconds; 18456 statements,
2 missed, 99.99% reported coverage. The preceding attempt timed out at 120 seconds.
The completed run log is
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/pytest_gate_1.log`.
These baseline failures are not independently verified hunt findings. Additional focused
shared-tree diagnostic runs were performed, but did not follow the required disposable-workspace
and independent-worker procedure and do not close any item.

Sharded and Postgres modes were not run except where an item record names a cell result.
Scratch evidence is deleted only at item close per each item's `Cleanup:` line.

## Current status (appended 2026-09-19; history above preserved)

The "no verdicts, no fixes" statements above describe the restart point, not the present:
since then 40 file items + the baseline scenario verified, with 12 ledgered corrections
(negative-cursor rejection, resource-charge accounting, range fail-loud, declared-key guard,
form basis guard, 4 hostile-name stale re-passes, fixture isolation). Fast-forward to
`bfaee91d` moved 3 verified targets (`consumers.py`, `extensions/error_policy.py`,
`list_field.py`) to `stale` for re-hunt; every other verified verdict was digest-reconciled
and stands, with hunt test hunks in 5 main-touched test files confirmed intact and green by
focused re-runs. Pending: ~62 file items from `optimizer/_context.py` onward, 3 standing
scenarios, integration, final gate. Baseline suite result above is historical, not the gate.

Resume 2026-09-21 (Worker 0): run id, baseline ancestry, and cycle baseline validated;
HEAD unchanged at bfaee91d; resume Drift line recorded. Stale-target stability check:
consumers.py 936210e2, extensions/error_policy.py bd763bcc (stable since Sep-20),
filters/base.py 91c41b1f, orders/base.py 77b8aa77 all match their stale notes;
list_field.py moved again (ce682d5f -> d6af6164, concurrent edits continue) — its re-hunt
dispatches as a takeover with attribution-first. Order of work: orphaned hunting item
utils/directives.py (fresh Worker 1, iteration 2), then pending file items in inventory
order, then the 5 stale re-passes, then scenarios, integration, gate.

Migration record (Worker 0, 2026-09-21; this paragraph supersedes the order-of-work line
above). METHOD: every ledger path's t3-vs-HEAD diff was hunk-attributed to ledger symbols
before moving (41 clean byte-copies incl. the 2 pure family gates, 10 auto-merged
overlaps, 1 manual union, 2 foreign-filtered applies). EXCLUDED and why: types/base.py foreign spec-015 set
(helper def + call site + the assignment-deletion hunk the token check first missed — the
miss caused a `suppress_pk_annotation` NameError caught by the proof run, fixed by restoring
the 10 HEAD lines verbatim; root cause was a substring collision, "shape" in
"_is_relay_shaped", disclosed so the next attribution pass uses word boundaries);
types/finalizer.py foreign +7 globalid-snapshot docstring (fix hunk kept); 9 non-ledger t3
production files (extensions/error_policy.py, list_field.py, inspect_django_type.py,
mutations/inputs.py, registry.py, relay.py, types/relay.py, types/resolvers.py,
utils/relations.py); 3 non-ledger t3 test overlaps (optimizer/test_extension.py,
types/test_resolvers.py, utils/test_errors.py); ~60 DRY-agent files; stray scratch. The
single manual union (tests/mutations/test_resolvers.py) was a docstring-only region resolved
by keeping both wordings; focused proof 50/50. VERIFICATION: all migrated files compile;
76/76 t3-added tests present in the 11 merged files; focused sweep of the 26 migrated
package files 2913/2914 (the 1 red is a pg-group environment artifact, see below) and the 2
migrated live files 402/402. DIGEST RECONCILIATION: the 5 prior stale verdicts stand at
consumers 936210e2, error_policy 16f47547 (t3-only movement to bd763bcc NOT migrated —
re-hunt runs at 16f47547), filters/base 91c41b1f, list_field ce682d5f (t3-only movement to
d6af6164 NOT migrated — re-hunt runs at ce682d5f), orders/base 77b8aa77. The 11 merged test
files keep their verdicts per the fast-forward precedent (hunt hunks confirmed intact +
focused runs green). Two NEW stale: types/base.py (recorded 07aaa2f2 incl. foreign, current
1fe9e5ad) and types/finalizer.py (recorded 8b6708fb incl. foreign, current 35ff5286) —
re-verification scope is narrow (same guards minus foreign bytes). PG-CELL OBSERVATION
(converters item keeps verified): test_convert_scalar_class_liar_at_hstore_dispatch_stays_typed
passes iff `django.contrib.postgres.fields` is unimportable (both dispatch sentinels None);
this worktree's shared venv has psycopg v3 installed (pg tier, concurrent session) so the
ArrayField arm fires first and the pin is red here. Proven identical behavior under t3's
interpreter (HStore message reproduced on the migrated bytes). The pg-group-installed cell
was never in campaign scope — recorded as unverified, never passed; Rio decides whether to
harden the pin. HISTORICAL CLOSEOUT: the main worktree's prior ledger content (Status:
complete, +463/-2) survives ONLY as scratch patch
migrate-0_0_15/historical-closeout.patch (verified byte-identical on re-application) — it
needs a commit before scratch evaporates. COUNTS NOW: 79 verified / 7 stale / 1 hunting
(utils/directives.py) / 21 pending. ORDER OF WORK: unchanged (directives takeover, pending
in inventory order, now 7 stale re-passes, scenarios, integration, gate). CHECKPOINT: no
dispatch yet — the hunting item may have a live t3 counterpart and the migration wants
Rio's eyeball first. T3 worktree intact (safety copy); branch t3code/1cc21548 lives here,
t3 detached. Post-record item baseline:
`0fcde47ad963238b48976aef51061e60599d4c8a`.

Resume 2026-09-21 (Worker 0, fresh session in the relocated worktree): run id,
baseline ancestry (bf02c227 ancestor of 69a25369), and cycle baseline validated;
relocation Drift recorded above; prior session's dispatches confirmed not running, so
all 5 `hunting` items need fresh Worker 1 (no report ever reached Worker 0 for any of
them). Tree object at resume: `c444697e262053243e37948d0c316adb141a869c`.
Digest reconciliation vs 69a25369: hunting targets all clean vs HEAD (directives
380786cf, errors 3e25e93b, execution_mode 9805cdaf, imports 291ecedd, input_values
f2566609); stale — consumers 936210e2 clean (re-hunt at HEAD), error_policy worktree
bd763bcc vs HEAD 16f47547 and list_field worktree d6af6164 vs HEAD ce682d5f (concurrent
dirt atop HEAD — re-hunts attribute-first, never touch foreign hunks), filters/base
91c41b1f vs HEAD ba52351c and orders/base 77b8aa77 vs HEAD 4736fda0 (hunt family-gate
fixes intact), types/base 1fe9e5ad vs HEAD 91c58747 (hunt guards minus foreign),
finalizer 35ff5286 vs HEAD 77fd9a2d (fix hunk intact). tests/utils/test_querysets.py
has zero diff vs HEAD — the proxy-fixture rows committed under a01a2ab8, so the
baseline-scenario ledger entry is now committed and its verdict stands as recorded.
Known hunt-owned defects to fix as a lint ledger item first (CI lint red):
`scripts/check_trailing_commas.py --check` reports 3 violations —
tests/rest_framework/test_sets.py (2 four-element lists not exploded) and
tests/types/test_base.py (1 three-element dict over-exploded). Order of work: lint
ledger item (Worker 1 fix, Worker 2 verify), then the 5 hunting items fresh in
inventory order, then pending file items, then the 7 stale re-passes, then scenarios,
integration, gate.

Lint ledger item 2026-09-21 (CI-red trailing-comma violations): VERIFIED. Worker 1
fixed exactly the 3 violations (test_sets.py 2→12-line explosion, test_base.py
5→1-line collapse), whitespace-only with AST identity (171750/260085 chars both eras),
whitespace-stripped streams differing by exactly +2/−1 commas, and focused 5/5
pre+post. Worker-0 mechanical checks passed (item-scoped diff exactly the 3
corrections; gates green; digests match; AST independently confirmed). Worker 2
verified expectation-first (hunt-ws/w2-lint-expectation.txt, digest 030b2fd9, written
before opening the W1 report; tripartite agreement incl. two independently derived
non-violations) with a fresh-workspace revert control (pre-fix exit 1 naming exactly
the 3 violations → post-fix byte-identical restore exit 0), independent AST +
comma-edit proofs, full-file gates green, ownership clean (no production file moved).
Ledger rows appended above. Minor non-blocking observation (no action): the
types/base.py ledger prose says "43 + 2 hostile nodes" for the tail hunk; W2 counts 46
— ownership holds by content either way. Cleanup: removed
hunt-ws/lint-trailing-commas/ and hunt-ws/lint-trailing-commas-verify/; expectation
file retained until closeout; unrelated work preserved. The hunt-attributed CI lint
red is cleared (concurrent/DRY paths, if any fail, are not hunt's).

Session progress 2026-09-21 (Worker 0): utils/errors.py VERIFIED Fixed Low (D1
guarded atom interrogation + 2 tests); utils/execution_mode.py VERIFIED No bugs
(19 + 31 probes, upstream seam audited both ends); utils/imports.py VERIFIED No
bugs (27 + 27 probes, 670-node oracle superset, caller-literals re-verified);
utils/input_values.py VERIFIED Fixed Low (D1 `str.__str__` label coercion + 1
test; W2 independent reconstruction, subject-trace + L1/L2/L3 dispositions). Two
ledger rows appended (errors, input_values); no-bugs items land nothing. Routing
from the input_values verification's new lead (probed orders/inputs.py:332
`owner_name` escape, probe d9216a9c): orders/inputs.py → stale for a narrow
re-pass (which also inspection-sweeps the unprobed qualname mentions at
orders/sets.py + sets_mixins.py — those verdicts stand with bounded lead notes);
filters/sets.py → stale mechanically (unreported in-flight get_fields hunk,
presumed inputs-hunt work, attribution check sent; re-pass after inputs closes);
utils/inputs.py hunting W1 gets the family mention by message. Stale queue now 9
(7 prior + orders/inputs + filters/sets). Next: permissions.py W1 in dispatch;
in flight: inputs, operation_lease hunts.

Resume 2026-09-21 ~22:45 (Worker 0, fresh session; two prior Worker-0 sessions
died on provider errors, nothing they dispatched still running). Run id, baseline
ancestry (bf02c227 ancestor of 24e6b4d3), and cycle baseline validated; HEAD-move
Drift + evidence-hygiene Drift recorded above (86/96 cited expectation files gone
by recount — the handoff said 70; `## Outcomes` corrected from "no fixes, no source
changed" to the ledgered present). Unfolded the dead session's verdicts BEFORE any
new dispatch: utils/operation_lease.py VERIFIED No bugs (W2 report survived; E1–E7
+ L8, replay 30+3, 17 attacks, own control, censuses redone) and utils/inputs.py
VERIFIED Fixed Low (W2 /tmp report lost; verdict from the handoff + on-disk
expectation + 47-node attack battery; 14/14 permanent tests red on
production-only revert; D8 proven necessary and sufficient) — ledger rows appended
(inputs D1–D7 + D8 seam), both ticked, 5 workspaces removed (r1/fail/verify).
filters/sets.py stale narrowed to the non-D8 region. utils/permissions.py W1 r2
No bugs folded through mechanical checks (PASS; one drift note: its querysets
freshness digest predates the fast-forward) → fresh Worker 2 dispatched.
utils/policies.py W1 died mid-probe → fresh Worker 1 at the rewritten bytes
(8c881c0a). Stale queue now 16 (9 prior + 7 fast-forward conversions; no tick kept
silently). Tree object at dispatch: `7c2d4c4f88e4005f3c2c1bc2c975e0d92bfd68b9`.
In flight: permissions W2 verification, policies W1 hunt, private_state W1 hunt
(third dispatch same session; item baseline 48ef3650).

Fold 2026-09-22 (Worker 0): utils/permissions.py VERIFIED No bugs (W2
expectation-first E1–E8; replay 43/43 + attacks 33/33 + oracles 56/56 and 31+10
live; 2 WS-only mutants biting, restored identical; querysets-drift discharged
by region identity; R7 inapplicability upgraded to measured zero-query evidence;
PG/sharded/async-transport stay unverified). No ledger (No bugs). Ticked;
removed `hunt-ws/utils-permissions-{r1,r2,verify}`; expectation retained. In
flight now: policies W1 hunt, private_state W1 hunt, querysets W1 hunt (fresh
dispatch, item baseline 2db65089).

Fold 2026-09-22 (Worker 0): utils/policies.py W1 r2 reported Fixed Low (one
bug class, D1–D4 hostile-dunder raw escapes at `resolve_policy` seams; owner
fix +56/-7 with guarded interrogation + key normalization + 5 permanent tests;
preview 5 red raw → 5 green, oracles 382/382). Mechanical checks PASS (digests
3f2066a9/60384e37 match; item diff exactly the 2 files; probes on disk; ruff +
prose clean). Report recovered verbatim to `/tmp/w1-policies-r2-report.txt`.
Fresh Worker 2 dispatched. utils/private_state.py W1 r1 reported No bugs
(66-probe battery, R1–R9, 3 biting controls, oracles 636 + 284 with the 1 red
being the campaign DECISION REQUEST test — independent corroboration of the
red, still unrelated to the target). Mechanical checks PASS (target clean,
probes + env anchor on disk, no stray files). Report recovered verbatim to
`/tmp/w1-private-state-r1-report.txt`. Fresh Worker 2 dispatched. In flight
now: policies W2 verification, private_state W2 verification, querysets W1
hunt.

Fold 2026-09-22 (Worker 0): utils/policies.py W2 verdict revision-needed on
ONE coverage gap (fix + 5 tests otherwise fully verified: revert control,
13 attacks, owner/tier/Low, ruff/prose): guard arms 172-173 + 225-226 unreached
(67/4/94%), both proven reachable by W2 probes — revision is 2 more permanent
tests, no production change. Same item back to Worker 1 with workspaces
intact. In flight now: policies W1 revision, private_state W2 verification,
querysets W1 hunt.

Fold 2026-09-22 (Worker 0): utils/private_state.py VERIFIED No bugs (W2
expectation-first R1–R9 + C1–C8; replay 66/66 + attacks 82 + 1 luck-skip +
control biting exactly the 2 predicted probes with sha256 matching W1's
pristine record; floor cell executed identical on 3.10–3.14; all candidate
rulings agreed). No ledger (No bugs). Ticked; removed
`hunt-ws/utils-private-state-{r1,verify}`; expectation retained. In flight
now: policies W1 revision, querysets W1 hunt, relations W1 hunt (fresh
dispatch, item baseline 9b0dc6ad; target carries the concurrent DRY docstring
hunk, hunt reads worktree bytes attribution-first).

Fold 2026-09-22 (Worker 0): utils/policies.py W1 revision landed (+2 tests,
production byte-identical 3f2066a9; WS-only revert proof, shared focused 24
passed, module 67/0/100% with flavor oracles). Mechanical checks PASS (tests
763ee8ca, exactly 7 added tests, ruff + prose clean). Fresh Worker 2
re-verification dispatched (criteria K1–K5). utils/querysets.py W1 r1 reported
Fixed Low (D1 hostile sidecar-set label, 2 sites → `_safe_class_name`, honest
bytes identical; 5 permanent tests; battery 154/154, 6/6 controls, oracles
334/334 + 428/428 + the known red reproduced exactly). Mechanical checks PASS
(digests 799139be/5aae2be4 match; item diff exactly the 2 lines + 5 tests;
probes on disk; neighbors unmoved; ruff + trailing-commas + prose clean; one
minor count slip 152-vs-154 flagged for W2). Fresh Worker 2 dispatched. In
flight now: policies W2 re-verification, querysets W2 verification, relations
W1 hunt.

Fold 2026-09-22 (Worker 0): utils/policies.py VERIFIED Fixed Low (W2
re-verification criteria K1–K5 all hold; expectation stands with no delta;
revert 7/7 raw → 24/24 green; module 67/0/100% with flavor oracles;
production cmp-identical to the r1 gold). Ledger row appended (fix + 7 tests).
Ticked; removed `hunt-ws/utils-policies-{r1,r2,verify,reverify}`; expectation
retained. In flight now: querysets W2 verification, relations W1 hunt,
sessions W1 hunt (fresh dispatch, item baseline 430faa88).

Fold 2026-09-22 (Worker 0): utils/querysets.py VERIFIED Fixed Low (W2
expectation-first E1–E8; 5/5 revert raw → green; replay 154/154 with the
152-slip reconciled; 32/32 attacks; honest cmp-identical; oracles 339/339 +
428/428 + known-red only; all 3 lint gates clean; 4 robustness rows agreed).
Ledger row appended (2-line fix + 5 tests). Ticked; removed
`hunt-ws/utils-querysets-{r1,verify}`; expectation retained. Adjacent lead
routed: orders/sets.py → stale for a narrow re-pass (`_NormalizationLedger`
+ purity-check raw `__name__`, characterized in-WS; absorbs its two older
leads into its own re-pass); filters/sets.py re-pass scope gains the unprobed
`cls.__name__` mention. Stale queue now 17. In flight now: relations W1 hunt,
sessions W1 hunt, strings W1 hunt (fresh dispatch, item baseline 11e859a1).

Fold 2026-09-22 (Worker 0): utils/relations.py W1 r1 reported No bugs (12
contract rows; 185-probe battery; floor 3.10 + ceiling 3.14 cells BOTH
executed at 311 passed; 62-path cross-version agreement; 3 biting controls;
6 disproved; 3 robustness rows). Mechanical checks PASS (target still exactly
the +14 DRY hunk untouched; tests clean; probes on disk; 58 defs → 185 nodes
flagged for W2 collection reconciliation). Fresh Worker 2 dispatched.
utils/sessions.py W1 r1 died by infra failure before probing (no verdict;
tree untouched) → fresh Worker 1 dispatched (baseline b934257d, workspace
hunt-ws/utils-sessions-r2). In flight now: relations W2 verification,
sessions W1 hunt (r2), strings W1 hunt.

Fold 2026-09-22 (Worker 0): utils/strings.py W1 r1 reported Fixed Low (D1
`_plain_text` liar escapes — the inputs-hunt lead confirmed on current source;
owner fix +19/-3 with guarded reads + 4 permanent tests, 13 nodes; battery
133 passed; 9 red raw pre → green post; M1/M2 controls biting; live 9/9 both
ways; module 76/1 with the miss pre-existing; floor 3.10 executed).
Mechanical checks PASS (digests ffa4fee0/77109707 match; item diff exactly
the fix + tests; probes on disk; neighbors unmoved; ruff + trailing-commas +
prose clean). One report slip corrected without bouncing: the 6 stated probe
digests are rotated one label off (all bytes accounted for; true mapping in
the item block; W2 re-hashes from disk). Fresh Worker 2 dispatched. In flight
now: relations W2 verification, sessions W1 hunt (r2), strings W2
verification.

Fold 2026-09-22 (Worker 0): utils/relations.py VERIFIED No bugs (W2
expectation-first; replay 185/185 + oracle 126/126 with the 58→185 count
reconciled exact; 42 independent attacks green both cells; 2 exact-signature
controls incl. first-hand proof of the cache-clear test-gap observation;
offline floor cell executed here too at 353 passed; all candidate/robustness
rulings agreed; DRY hunk untouched). No ledger (No bugs). Ticked; removed
`hunt-ws/utils-relations-{r1,verify}`; expectation retained. In flight now:
sessions W1 hunt (r2), strings W2 verification, typing W1 hunt (fresh
dispatch, item baseline 1bee00f9).

Fold 2026-09-22 (Worker 0): utils/strings.py VERIFIED Fixed Low (W2
expectation-first E1–E14; 54 green → 9 raw on revert → 54 restored; W1
battery 133 replayed with the corrected probe digests confirmed; live 9+9;
39-node attacks green incl. novel liar shapes; positive control exact;
floor 3.10 re-executed by W2; coverage miss proven pre-existing other-tier;
all 5 robustness rows agreed; C3 owner verified). Ledger row appended (fix +
4 tests). Ticked; removed `hunt-ws/utils-strings-{r1,verify}`; expectation
retained. In flight now: sessions W1 hunt (r2), typing W1 hunt,
write_transaction W1 hunt (fresh dispatch, item baseline f925a39e).

Fold 2026-09-22 (Worker 0): utils/sessions.py W1 r2 reported Fixed Low (D
hostile/masquerading SESSION_ENGINE raw escapes, 7 triggers; owner fix with
guarded gate + flatten-first + guarded flatten per the policies precedent +
8 permanent tests; 76/76 probes; 7 red pre → green post; PC1-3 biting;
oracles 188+34+63; shared 29/29; module 80/0; ceiling + floor executed).
Mechanical checks PASS (digests 54c41be7/42a8d631 match; item diff exactly
the 2 files; probes + logs on disk; neighbors unmoved; ruff +
trailing-commas + prose clean). Fresh Worker 2 dispatched. In flight now:
typing W1 hunt, write_transaction W1 hunt, sessions W2 verification.

Fold 2026-09-22 (Worker 0): utils/sessions.py VERIFIED Fixed Low (W2
expectation-first E1–E15; replay 138/138; revert 7-fail-intended + pin;
attack red-subset pre-fix incl. session-aborting KI; revoke holds pre-fix;
oracles 196+99+212 with W1's 188 count corrected; module 80/0; floor
re-executed 63/63; all robustness/candidate rulings agreed; inapplicability
verified against the surface). Ledger row appended (fix + 8 tests). Ticked;
removed `hunt-ws/utils-sessions-{r1,r2,verify}` (shared `floor-310/` testbed
kept); expectation retained. In flight now: typing W1 hunt,
write_transaction W1 hunt, write_values W1 hunt (fresh dispatch, item
baseline f46bd1f4).

Fold 2026-09-22 (Worker 0): utils/typing.py W1 r1 reported No bugs (7
contract rows; 71-node battery green on interpreters 3.10–3.14 with a 42-cell
vector agreement; feasible-shape E2E both transports; lazy-proxy disproved;
TOCTOU closed; 3 biting controls; oracles green; one fix considered and
rejected per HUNT). Mechanical checks PASS (target + tests == HEAD; probes +
vectors on disk; counts/controls/reach stated; known-red avoided). Fresh
Worker 2 dispatched. In flight now: write_transaction W1 hunt, write_values
W1 hunt, typing W2 verification.

Fold 2026-09-22 (Worker 0): utils/typing.py VERIFIED No bugs (W2
expectation-first; replay 71/71 on all five interpreters with 5/5 vectors
re-executed identical; 53-node attacks green on 3.14 + 3.10 incl.
partialmethod closed at both ends + ordering proof + re-done storage audit;
exact control; invalid run discarded + rerun; no unverified cells;
known-red named, not chased). No ledger (No bugs). Ticked; removed
`hunt-ws/utils-typing-{r1,verify}`; expectation retained. In flight now:
write_transaction W1 hunt, write_values W1 hunt, views W1 hunt (fresh dispatch,
item baseline 22ca1f8f; last pending file item — pending queue now empty).

Fold 2026-09-22 (Worker 0): utils/write_transaction.py W1 r1 reported Fixed
Low (D1 raw `__name__` at 5 typed seams; feasibility proven via registered
hostile mutations + EvilStr models surviving Django construction; owner fix
import + 5 `_safe_class_name` swaps + 5 permanent tests; battery 71/71; 5/5
fail→pass with `cmp` restore; neighbors 566+265; M1/M2 biting; shared 5/5).
Mechanical checks PASS (digests 9ad493b6/7a29fb80 match; item diff exactly
the 2 files; probes on disk; ruff + trailing-commas + prose clean).
utils/write_values.py W1 r1 reported No bugs (8 contract rows; 67-probe
battery; 3 biting controls; oracles 317+7; floor 29; 4 liar shapes ruled
robustness with armed instruments; prose/scale/BaseException rows
disproved). Mechanical checks PASS (target + tests == HEAD; probes on disk;
all 8 connected digests match — no drift). Fresh Worker 2 dispatched for
both. In flight now: views W1 hunt, write_transaction W2 verification,
write_values W2 verification.

Fold 2026-09-22 (Worker 0): utils/write_transaction.py VERIFIED Fixed Low
(W2 expectation-first; 5/5 revert raw → green; 49-probe attacks incl. shapes
W1 never tried; honest template-exact + pristine parity; exact control;
floor-3.10 executed 5/5; oracles 68/68 + 566/566; known-red confirmed once,
not chased; all 8 robustness rows agreed with two-interpreter grounding;
out-of-fence rf/resolvers label note routed to that owner, no action).
Ledger row appended (fix + 5 tests). Ticked; removed
`hunt-ws/utils-write-transaction-{r1,verify}`; expectation retained. In
flight now: views W1 hunt, write_values W2 verification, consumers stale
re-hunt W1 (first of the 17 stale re-passes; baseline 91307d53; 6-line
delta, verdict stands for the rest).

DECISION REQUEST (maintainer, not hunt-resolvable):
`tests/test_list_field.py::test_djangolistfield_unregistered_guard_survives_a_hostile_metaclass_name`
is RED because the ledgered `types/base.py::DjangoType.__init_subclass__`
unreadable-`__name__` collection guard now rejects the test's class at creation,
outside its `pytest.raises`. Either the guard stands and the test is retired or
rewritten, or the guard narrows. Worker 0 takes neither branch; the gate stays
blocked on this until Rio rules. Recorded 2026-09-21 ~22:45, handed off from the
prior session, not re-proven by a new run in this session.

Fold 2026-09-22 ~08:45 (Worker 0, fresh session; the prior Worker-0 died on API
429 quota exhaustion, nothing it dispatched still running). Run id, baseline
ancestry (bf02c227 ancestor of 5ee86193), and cycle baseline validated;
HEAD-move Drift recorded above (24e6b4d3..5ee86193, 4 commits; production
docstring-only; zero ledger test files touched; both live rows 2 passed
focused). All three dead dispatches re-dispatched fresh with shared
ITEM_BASELINE 3c00404f and all 6 target/test digests re-confirmed: views W1
(new workspace hunt-ws/views-r2; dead r1 workspace kept as orientation),
write_values W2-only (new workspace hunt-ws/utils-write-values-verify2 +
fresh expectation file; dead W2's partial expectation never to be opened),
consumers stale W1 (workspace hunt-ws/consumers-stale-r1, path was unused).
Disk 13 GB free, hunt-ws 2.2 GB; new copies exclude hunt-ws. In flight now:
views W1 hunt (r2), write_values W2 verification (r2), consumers stale W1
re-hunt.

Fold 2026-09-22 (Worker 0): consumers stale W1 re-pass reported No bugs
(docstring-only 6-line delta, AST-neutral, both new sentences behaviorally
true; anchor 114 + 212 + 69 green). Mechanical checks PASS (item diff empty;
digests match; delta confirmed 6 lines; no nested hunt-ws). Fresh Worker 2
dispatched. In flight now: views W1 hunt (r2), write_values W2 verification
(r2), consumers stale W2 verification.

Fold 2026-09-22 (Worker 0): utils/write_values.py VERIFIED No bugs (W2
expectation-first; replay 66 behavioral + oracles 317/317 + live 7/7; 47
attacks ceiling + floor; 2 biting controls; all rulings agreed; dead files
never opened). No ledger (No bugs). Ticked; removed
`hunt-ws/utils-write-values-{r1,verify,verify2}` + dead expectation; r2
expectation retained. Disk 9.2 GB free (3 live workspaces), above the 6 GB
line. In flight now: views W1 hunt (r2), consumers stale W2 verification,
connection stale W1 re-hunt (fresh dispatch, item baseline 3c00404f).

Fold 2026-09-22 (Worker 0): consumers.py stale re-pass VERIFIED No bugs (W2
expectation-first; replay 14/14 + oracles exact + live 97+3 same env errors;
selective control; 11/11 attacks incl. mutation twins + behavioral boundary).
No ledger (No bugs). Ticked; removed `hunt-ws/consumers-stale-{r1,verify}`;
expectation retained. Disk 11 GB free, hunt-ws 1.5 GB. In flight now: views
W1 hunt (r2), connection stale W1 re-hunt, error_policy stale W1 re-hunt
(fresh dispatch, item baseline 3c00404f).

Fold 2026-09-22 (Worker 0): views.py W1 r2 reported No bugs (58 probes
ceiling + floor; oracles 208 + 97 with 3 pre-existing env errors; 3 biting
controls; 8 candidates ruled). Mechanical checks PASS (item diff empty; all
digests match; count slip flagged for W2). Fresh Worker 2 dispatched. In
flight now: connection stale W1 re-hunt, error_policy stale W1 re-hunt,
views W2 verification.

Fold 2026-09-22 14:14 UTC (Worker 0, fresh session; the prior Worker-0 died
on provider 429 2026-09-22 05:11, nothing it dispatched still running —
fourth Worker-0 death this campaign). Run id, baseline ancestry (bf02c227
ancestor of 5ee86193), and cycle baseline validated; HEAD unchanged at
5ee86193, no new Drift line owed. Tree moved since 3c00404f (progress file
Fold lines + the maintainer-rewritten DRY plan only — no production or test
movement; `git diff 3c00404f --stat` names exactly those two docs files),
so a fresh shared ITEM_BASELINE 706f2219 was minted; all 6 target/test
digests re-confirmed (views 9f85b0df + tests 4dc9a257 clean; connection
worktree 9c5b8724 vs HEAD 4894f90f exactly the ledgered fix by digest;
error_policy 1a19cd7d + tests d7c467dc clean). All three dead dispatches
re-dispatched fresh: views W2-only (new workspace hunt-ws/views-verify2 +
fresh expectation file; dead W2's partial expectation never to be opened),
connection stale W1 (workspace hunt-ws/connection-stale-r1, no probes on
disk, rebuild excluding hunt-ws), error_policy stale W1 (path absent,
fresh build). Disk 25 GB free, hunt-ws 1.5 GB; no nested hunt-ws in the
live workspaces. In flight now: views W2 verification (r2), connection
stale W1 re-hunt, error_policy stale W1 re-hunt.

Fold 2026-09-22 14:23 UTC (Worker 0): error_policy stale W1 re-pass
reported No bugs (C1-C6; 53 probes; oracles 69 + 70 live + 24; floor
subset; 2 biting controls; rewrite delta exactly 6 semantic lines).
Mechanical checks PASS (item diff empty; digests match; collection exact;
anchor + DB valid; no stray files). Fresh Worker 2 dispatched. In flight
now: views W2 verification (r2), connection stale W1 re-hunt,
error_policy stale W2 verification.

Fold 2026-09-22 14:30 UTC (Worker 0): views.py VERIFIED No bugs (W2
expectation-first; replay 58/58 both cells + oracles 208 + 97 with 3
pre-existing errors shared-identical; 37 attacks; biting control
cmp-identical; both count slips reconciled exact; PG/sharded judged
inapplicable-by-construction). No ledger (No bugs). Ticked — the last
pending file item is closed; removed `hunt-ws/views-{r1,r2,verify,verify2}`;
expectation retained. Connection stale W1 re-pass reported No bugs (R0-R4;
16 probes both cells; oracles 182 + 88 live; biting control
cmp-identical; ledgered fix intact + load-bearing). Mechanical checks PASS
(item diff empty; digests match; collection 16 exact; sharded/PG honestly
unverified; one out-of-fence observation rides for W2 judgment, no stale
trigger). Fresh Worker 2 dispatched (baseline 706f2219 retained for the
item).

Fold 2026-09-22 14:30 UTC (Worker 0): error_policy stale re-pass VERIFIED
No bugs (W2 expectation-first C1-C6, no contradiction; replay 52/52 +
oracles 69 + 24 + 70 live; 23 attacks; biting control exact; all digests
match; rewrite delta re-derived as exactly the 6 semantic lines;
inapplicability judged). No ledger (No bugs). Ticked; removed
`hunt-ws/error-policy-stale-{r1,verify}`; expectation retained. Fresh
ITEM_BASELINE c9e39d31 minted for new dispatches (movement since 706f2219
is only this file + 5 DRY plan lines — no production/test drift).
Dispatched next two stale W1 re-hunts in inventory order:
extensions/error_policy.py (settled at d526a7bd = HEAD + the DRY docstring
hunk; oracles shared, now free) and extensions/resource_policy.py
(2549591a = HEAD + ledgered fix). Disk 23 GB free, hunt-ws 340 MB. In
flight now: connection stale W2 verification, extensions/error_policy
stale W1 re-hunt, extensions/resource_policy stale W1 re-hunt.

Fold 2026-09-22 14:41 UTC (Worker 0): connection.py stale re-pass VERIFIED
No bugs (W2 expectation-first, full R0-R4 agreement; replay 16/16 both
cells + oracles 182 + 88; own biting control; 19 attacks both cells;
ledgered fix re-derived exact; sharded/PG honestly unverified; out-of-fence
observation judged correctly non-routed). No ledger (No bugs). Ticked;
removed `hunt-ws/connection-stale-{r1,verify}`; expectation retained.
extensions/error_policy stale W1 re-pass reported No bugs (R1-R8; 42
probes both cells; oracles 69 + 70 live + 4; 3 biting controls; delta
exactly 6 semantic lines; DRY hunk untouched). Mechanical checks PASS
(item diff empty; digests match; collection 42 exact). Fresh Worker 2
dispatched. Dispatched filters/base.py bounded W1 re-pass (91c41b1f = HEAD
+ ledgered gate). In flight now: extensions/error_policy stale W2
verification, extensions/resource_policy stale W1 re-hunt, filters/base
stale W1 re-hunt.

Fold 2026-09-22 14:49 UTC (Worker 0): extensions/error_policy stale
re-pass VERIFIED No bugs (W2 expectation-first, full R1-R8 agreement;
replay 41/41 behavioral + oracles 69 + 70 live + 4; 40 attacks both
cells; biting gate-inversion control cmp-identical; delta re-derived as
exactly the 6 DEFAULT-to-PRIVATE lines; inapplicability grep-proven; all
4 robustness rows concurred). No ledger (No bugs). Ticked; removed
`hunt-ws/ext-error-policy-stale-{r1,verify}`; expectation retained.
Attribution note for the next dispatch: tests/filters/test_sets.py carries
4 foreign uncommitted maintainer live-re-tiering hunks (module docstring,
2 r6 docstrings, deletion of the E2E test whose live sibling is committed
in HEAD — continuation of e9e4d45c), alongside the 2 ledgered hunt tests;
production carries exactly the 2 ledgered hunks. Dispatched filters/sets.py
narrowed W1 re-pass (d56c21f0; foreign hunks preserve-only). In flight
now: extensions/resource_policy stale W1 re-hunt, filters/base stale W1
re-hunt, filters/sets stale W1 re-hunt.

Fold 2026-09-22 14:55 UTC (Worker 0): extensions/resource_policy stale W1
re-pass reported Fixed Low (D1 spread-site charge below the
unresolvable/cyclic guard; moved above + comment + docstring; 3 unit + 1
live tests; scope (a)/(b) re-proven). Mechanical checks PASS (fences
clean — the 5 item files only; diffs exactly the fixes + tests; digests
match; collections 48/21 exact; Worker-0 re-ran all gates + prose scans
on touched paths, clean; failability for W2). Fresh Worker 2 dispatched.
filters/base bounded W1 re-pass reported Fixed Low (C1 unguarded owner
`isinstance` in the rejection label; 4-line diamond guard + docstring; 2
tests). Mechanical checks PASS (same sweep). Its orders/base.py identical
line flag is routed to that sibling re-pass. Fresh Worker 2 dispatched.
In flight now: filters/sets stale W1 re-hunt, extensions/resource_policy
stale W2 verification, filters/base stale W2 verification.

Fold 2026-09-22 15:06 UTC (Worker 0): extensions/resource_policy stale
re-pass VERIFIED Fixed Low (W2 expectation-first, full R0-R5 + D1
agreement; replay 47/47 + oracles 299 + 146; WS-only revert re-opens the
hole with the exact escape signature, all 4 permanent tests fail,
restored cmp-identical; 26 attacks incl. exact-count double-charge pins;
single-conversion claim re-proven; O1 concurred-as-framed, O2/O3
robustness rows; Low concurred; W1 count errata corrected, all green).
Ledger row appended (fix + 4 tests). Ticked; removed
`hunt-ws/ext-resource-policy-stale-{r1,verify}`; expectation retained.
Dispatched list_field.py W1 re-hunt (616ca7f6 = HEAD + DRY hunk; tests
clean; known-RED decision test flagged reproduce-don't-chase). In flight
now: filters/sets stale W1 re-hunt, filters/base stale W2 verification,
list_field stale W1 re-hunt.

Fold 2026-09-22 15:07 UTC (Worker 0): filters/base stale re-pass VERIFIED
Fixed Low (W2 expectation-first, agreement on every row; replay 21/21 +
oracles 210 + 593 + 268 live; production-only revert fails raw with the
pin green, restored cmp-identical; 24 attacks incl. no-over-capture
proof; honest-byte proof 18 identical + 4 RAW-to-typed flips;
BaseException breadth judged correct; orders/base.py:135 correctly left;
Low concurred; inapplicability grep-proven). Ledger row appended (fix + 2
tests). Ticked; removed `hunt-ws/filters-base-stale-{r1,verify}`;
expectation retained. Dispatched nested_planner.py W1 re-hunt (225011b6
= HEAD + ledgered M2M gate). In flight now: filters/sets stale W1
re-hunt, list_field stale W1 re-hunt, nested_planner stale W1 re-hunt.

Correction 2026-09-22 15:07 UTC (Worker 0): the post-edit `ruff check
--fix` applied 1 auto-fix to the filters-sets W1's in-flight
filters/sets.py (the only .py that moved since the last clean gate run —
by elimination the import-block comma/order normalization; all
substantive hunks — the `__all__` guard + label swaps — are the worker's,
verified by reading the diff). Worker notified by message to
confirm/adjust in its report. Going forward Worker-0 runs detection-only
gates (`ruff check` + `ruff format --check`, no --fix/rewrite) after
progress-file edits: .md edits cannot break ruff, and repo-wide --fix can
land in a sibling's in-flight fix (HUNT.md "never edit a fix" outranks
the --fix letter).

Fold 2026-09-22 15:15 UTC (Worker 0): list_field stale W1 dispatch died
on model-stream idle timeout with no report (infra failure, 1415 log
lines deep; shared tree untouched, item diff empty). Its partial
workspace is retained as UNVERIFIED orientation only. Fresh Worker 1
dispatched (workspace hunt-ws/list-field-stale-r2, glance-only at the
dead workspace, same scope). In flight now: filters/sets stale W1
re-hunt, nested_planner stale W1 re-hunt, list_field stale W1 re-hunt
(r2).

Fold 2026-09-22 15:18 UTC (Worker 0): filters/sets narrowed W1 re-pass
reported Fixed Low (one bug class, all 3 leads confirmed: 19 hostile
label reads + refusing-`__ne__` narrowing check; safe renderers +
guarded `!=`; 19 tests; scope (a) re-proven). Mechanical checks PASS
(fences clean; diffs exactly the fix + tests; digests match; foreign
hunks byte-identical; collection 42 exact with RECORD.md; all gates +
prose scans re-run clean; no new pragma; failability for W2). The
sets_mixins.py:549 routed lead rides for W2 judgment, no stale trigger.
Amendment to the 15:07 Correction: the W1 report says a `ruff --fix`
pass dropped the `_safe_text` import (restored by hand); given the
timing, my 15:07 pass is the likely source, not a comma/order tweak as
inferred — end state verified correct regardless (import present, gates
green). Fresh Worker 2 dispatched. In flight now: nested_planner stale
W1 re-hunt, list_field stale W1 re-hunt (r2), filters/sets stale W2
verification.

ENVIRONMENT ALERT 2026-09-22 15:29 UTC (Worker 0, confirmed first-hand):
a concurrent gate harness (`dsf-gate-050-*` in /private/tmp) set
`core.worktree=/private/tmp/dsf-gate-050-Mebdp9` in the shared main-repo
config. Bare git commands in this worktree currently describe that /tmp
copy (`rev-parse --show-toplevel` proves it; `status` shows 7 foreign
paths). The main checkout is off-limits so the config is left alone.
Workaround until released: prefix worktree-describing git with
`git --work-tree=<this-worktree>` and sanity-check toplevel (verified:
toplevel + 195-path status + HEAD correct under the override).
`git hash-object <path>` and `git show <commit>:<path>` are unaffected.
The flip landed after the 15:18 checks (those outputs were
self-consistent with this tree) and before the nested-planner W1's
mid-session notice; that W1 closed attribution config-independently.
Both running siblings messaged with the workaround; all new dispatches
carry it. ALL-CLEAR 2026-09-22 ~15:35 UTC: `core.worktree` unset, bare
git describes this worktree again (toplevel + 196-path status + HEAD
verified). The `--work-tree` override remains harmless; workers keep or
drop it freely.

Fold 2026-09-22 15:29 UTC (Worker 0): nested_planner stale W1 re-pass
reported No bugs (R-A/R-B rows; 25 probes both cells; oracles 72 + 3 + 2
live; 2 biting controls; main delta claimed docstring-only, M2M gate
intact). Mechanical checks PASS under corrected git (item diff empty;
digests match; collection 25 exact). Fresh Worker 2 dispatched.
Dispatched walker.py W1 re-hunt (e8d80005 clean). In flight now:
list_field stale W1 re-hunt (r2), filters/sets stale W2 verification,
nested_planner stale W2 verification, walker stale W1 re-hunt (4 —
one over the usual 3 to cover the re-hunt while two verifications run).

Fold 2026-09-22 15:38 UTC (Worker 0): filters/sets W2 verdict
revision-needed on ONE concrete challenge C1 (everything else verified
and fenced: replay 42/42 + oracles 320 + 268, revert 22F/20P + 18/18
red, honest identity independently proven, all 19 label sites solid,
gates/prose clean). C1: the `!=` guard's except arm regresses
upstream-truthy + `!=`-refusing declarations from loud to
silent-divergent (narrowing skipped); repro + twins + remedy direction
(`not (==)`) + acceptance criteria all supplied, Low, no dispute. Same
item back to Worker 1 with workspaces intact (fresh revision worker, C1
only). The sets_mixins.py:549 routed lead was judged HAS STANDING
(reproduced A20 with row + shape + input) — sets_mixins.py marked stale,
narrow re-pass queued in inventory order (after schema, before
types/base). In flight now: list_field stale W1 re-hunt (r2),
nested_planner stale W2 verification, walker stale W1 re-hunt,
filters/sets stale W1 revision.

Fold 2026-09-22 15:39 UTC (Worker 0): list_field stale W1 (r2) reported
Fixed Low (D1: four unguarded interrogations in the shared construction
validator escaped raw; four contained interrogations + docstring + 4
tests; full re-hunt otherwise clean). Mechanical checks PASS (fences
clean; DRY hunk preserved; digests match; collection 16 exact; all gates
+ prose scans re-run clean; no new pragma; known-RED reproduced +
untouched; A5/A7 ride for W2 judgment). Fresh Worker 2 dispatched. In
flight now: nested_planner stale W2 verification, walker stale W1
re-hunt, filters/sets stale W1 revision, list_field stale W2
verification.

Fold 2026-09-22 15:40 UTC (Worker 0): nested_planner stale re-pass
VERIFIED No bugs (W2 expectation-first, every row confirmed; replay
25/25 + oracles 72 + 5 + full 903; 29 attacks; biting gate-inversion
control with exact specificity, restored cmp-identical; floor 126/126;
delta re-derived as the docstring hunk; wiring re-proven; cells judged
narrowly). No ledger (No bugs). Ticked; removed
`hunt-ws/nested-planner-stale-{r1,verify}`; expectation retained.
Dispatched orders/base.py bounded W1 re-pass (77b8aa77 = HEAD + ledgered
gate, plus the routed C1-twin flag at :135). In flight now: walker
stale W1 re-hunt, filters/sets stale W1 revision, list_field stale W2
verification, orders/base stale W1 re-hunt.

Fold 2026-09-22 15:47 UTC (Worker 0): orders/base bounded W1 re-pass
reported Fixed Low (C1-twin CONFIRMED with probe before editing: raw
`RuntimeError: boom-class` from :135 for a raising owner + mistyped
target; 4-line diamond guard mirroring the verified twin + docstring + 2
tests; gate + honest + G4 + L1 re-proven). Mechanical checks PASS
(fences clean; production diff the exact twin shape; digests match;
collection 19 exact; all gates + prose scans re-run clean; no new
pragma; failability for W2). Fresh Worker 2 dispatched. In flight now:
walker stale W1 re-hunt, filters/sets stale W1 revision, list_field
stale W2 verification, orders/base stale W2 verification.

Fold 2026-09-22 15:51 UTC (Worker 0): list_field stale re-hunt VERIFIED
Fixed Low (W2 expectation-first, full E1-E13 agreement; replay 15/16 +
oracles 113 + 137 + 78 live + 230 neighbors; WS-only revert fails raw on
all 4 + battery 11/4, restored cmp-identical; 18 attacks incl. 3
factories × 4 sites; `except Exception` judged correct; A5 HAS STANDING
→ routed to the queued types/base re-pass as scope, A7 closed; known-RED
confirmed isolated; W1 count erratum corrected; Low concurred). Ledger
row appended (fix + 4 tests). Ticked; removed
`hunt-ws/list-field-stale-{r1,r2,verify}`; expectation retained. Walker
stale W1 re-pass reported No bugs in-fence + confirmed Low D1
out-of-fence, routed unfixed (37 probes both cells + live; 2 biting
controls; D1: combinator hook returns escape the list seal raw —
prescription + de-risking supplied, owner querysets verified untouched).
Mechanical checks PASS (item diff empty; digests match; collection 37
exact). Fresh Worker 2 dispatched with D1-standing judgment duty — the
querysets re-pass opens only on W2 confirmation. Dispatched orders/inputs
narrow W1 re-pass (6f6ec946 clean). In flight now: filters/sets stale W1
revision, orders/base stale W2 verification, walker stale W2
verification, orders/inputs stale W1 re-hunt.

Fold 2026-09-22 15:58 UTC (Worker 0): orders/base stale re-pass VERIFIED
Fixed Low (W2 expectation-first, agreement on every row; replay 19/19 +
26/26 + 394 oracles; WS-only revert fails the exact C1 nodes, restored
cmp-identical twice; honest bytes identical; 29 attacks + 5 breadth with
BaseException CORRECT re-derived, not inherited; floor 45/45; owner
right as the last unguarded read; tier + Low concurred). Ledger row
appended (fix + 2 tests). Ticked; removed
`hunt-ws/orders-base-stale-{r1,verify}`; expectation retained.
Out-of-fence (a) noted without action; (b) folded into the queued
sets_mixins re-pass scope. Dispatched orders/sets narrow W1 re-pass
(6044ab1a clean). In flight now: filters/sets stale W1 revision, walker
stale W2 verification, orders/inputs stale W1 re-hunt, orders/sets stale
W1 re-hunt.

Fold 2026-09-22 16:01 UTC (Worker 0): filters/sets C1 revision landed
(`not (==)` per the remedy + 56-cell matrix green + prior greens
re-proven both cells + 4 new tests). Mechanical checks PASS (diffs
exactly the C1 replacement + tests; verified scope untouched with
test-side 0 deletions; digests match; collection 69 mapped per-file
exact; all gates + prose scans re-run clean; the "sweep" hit is domain
vocabulary in a production comment, not test provenance; no new pragma).
Fresh Worker 2 re-verification dispatched (K1-K5). In flight now: walker
stale W2 verification, orders/inputs stale W1 re-hunt, orders/sets stale
W1 re-hunt, filters/sets stale W2 re-verification.

Fold 2026-09-22 16:08 UTC (Worker 0): orders/inputs narrow W1 re-pass
reported Fixed Low (:332 CONFIRMED with probe before editing: two raw
escapes replacing the promised typed leaf-direction rejection; 2-line
`_safe_class_name` fix + import + 2 tests; honest bytes identical) with
sets_mixins :549 independently confirmed end-to-end (second
confirmation, already queued). Mechanical checks PASS (fences clean;
diffs exactly the fix + tests; digests match; collection 16 mapped
per-file exact — 15 behavioral + anchor; all gates + prose scans re-run
clean from root; no new pragma; failability for W2). Fresh Worker 2
dispatched. In flight now: walker stale W2 verification, orders/sets
stale W1 re-hunt, filters/sets stale W2 re-verification, orders/inputs
stale W2 verification.

Fold 2026-09-22 16:14 UTC (Worker 0): filters/sets C1 re-verification
VERIFIED Fixed Low (K1-K5 all pass: matrix 69/69 + twins narrow with PK
in/M2M out; upstream independently re-derived; K2 greens + own captures;
K3 revert byte-exact with the 22-node inventory; K4 gates + foreign
intact + pragma 2=2; K5 noqa justified). Ledger row appended (fix + 23
tests). Ticked; removed all 3 workspaces; both expectations retained.
orders/inputs narrow re-pass VERIFIED Fixed Low (replay 15/1-by-design;
revert twice; 21 attacks; honest identity; owner/tier/Low concurred;
:549 opinion confirms reproduction for the queued re-pass; W1 pre-fix
count corrected as erratum). Ledger row appended (fix + 2 tests).
Ticked; workspaces removed; expectation retained. orders/sets narrow W1
re-pass reported Fixed Low (11 sites, all three confirmed with rows +
probes before editing; 15 tests). Mechanical checks PASS (fences clean;
diffs exactly the fix + tests; digests match; collection 20 exact; all
gates + prose scans re-run clean; no new pragma). Fresh Worker 2
dispatched. Dispatched resource_policy W1 re-pass (4b69e974 clean;
oracles carry the verified extensions hunks as baseline). In flight
now: walker stale W2 verification, orders/sets stale W2 verification,
resource_policy stale W1 re-hunt.

Fold 2026-09-22 16:27 UTC (Worker 0): orders/sets narrow re-pass
VERIFIED Fixed Low (W2 expectation-first E1-E7; replay 20/20; WS-only
revert twice with the exact census + 14/104 polarity, restored
cmp-identical; 28 attacks incl. single-dunder proof; C1-twin
impossibility confirmed by independent trace; :497 judged legitimate;
owner/tier/Low concurred; honest bytes identical; floor 48/48; gates +
prose clean). Ledger row appended (fix + 15 tests). Ticked; workspaces
removed; expectation retained. Dispatched schema.py W1 re-pass
(19f90bf5 clean — includes 9350eb8d; no new drift). In flight now:
walker stale W2 verification, resource_policy stale W1 re-hunt, schema
stale W1 re-hunt.

Fold 2026-09-22 16:37 UTC (Worker 0): resource_policy W1 re-pass
reported No bugs (R1-R8 re-proven; 75 + 4 probes both cells; oracles 299
+ 146 live; 2 biting controls; delta exactly the 5-hunk re-pointing).
Mechanical checks PASS with one caveat (probe digests drifted
post-report — flagged for W2, which re-hashes from disk; counts +
anchors + oracles verify; the c9e39d31 diff shows the verified sibling
fix, delta since dispatch empty). Fresh Worker 2 dispatched. Walker
stale re-pass VERIFIED No bugs in-fence (W2 both duties: replay 36/36 +
189 oracles; 32 attacks; 2 biting controls; delta + census re-derived)
with D1 judged HAS STANDING + routing confirmed + a _DEFAULT scope
extension (own live evidence L1/B2/B3/L4/L5; prescription assessed).
No ledger (No bugs in-fence). Ticked; workspaces removed; expectation
retained. utils/querysets.py marked stale: narrow _LIST re-pass queued
after types/finalizer; the _DEFAULT flip recorded as a non-blocking Rio
decision (confirm-or-disprove-and-report, no flip without Rio).
Dispatched types/base W1 re-pass (1fe9e5ad = HEAD + byte-identical hunt
guards, spec-015 excluded; A5 in scope, RED decision test
reproduce-don't-chase). In flight now: schema stale W1 re-hunt,
resource_policy stale W2 verification, types/base stale W1 re-hunt.

Fold 2026-09-22 16:45 UTC (Worker 0): CORRECTION — the resource-policy
"probe digest drift" caveat is withdrawn: workers pin scratch probes
with sha256, and both digests match the claims exactly (b4b3da12 /
b48100eb); Worker-0's check wrongly used git-hash-object. Same
understanding applied to schema (4/4 sha256 match). Running
resource-policy W2 messaged with the withdrawal. Going forward Worker-0
checks probe pins with sha256sum. — Schema stale W1 re-pass reported No
bugs (R0-R9; 38 probes both cells; oracles 640 + 216 live; 3 biting
controls; rewrite exactly 9350eb8d's 10 lines). Mechanical checks PASS
(item diff empty; digests match; collection 38 exact). Fresh Worker 2
dispatched. In flight now: resource_policy stale W2 verification,
types/base stale W1 re-hunt, schema stale W2 verification.

Fold 2026-09-22 16:51 UTC (Worker 0): resource_policy stale re-pass
VERIFIED No bugs (W2 expectation-first, full R1-R8 agreement; replay
79/79 + oracles 299 + 146 both cells; 19 attacks; biting control with
hash corroboration; drift-caveat dissolved matching the withdrawal;
delta re-derived as the 5 hunks; item diff = target 0 bytes + sibling
D1 tests; split-cell holds; C1-C8 concurred with one evidenced
erratum). No ledger (No bugs). Ticked; workspaces removed; expectation
retained. Dispatched types/finalizer W1 re-pass (35ff5286 = HEAD +
exactly the ledgered guard, stable since before 08:45; the ledger's
foreign-docstring note no longer materializes). In flight now:
types/base stale W1 re-hunt, schema stale W2 verification,
types/finalizer stale W1 re-hunt.

Fold 2026-09-22 16:57 UTC (Worker 0): types/base W1 re-pass reported
Fixed Low (A5 CONFIRMED with probe before editing: raw `__mro__`
detonation violating the helper's `False` posture; minimal in-contract
guard + docstring + 2 tests; all load-bearing rows re-verified green;
known-RED reproduced + untouched). Mechanical checks PASS with one
caveat (probe bytes differ from reported pins — content polish
post-pin, counts reconcile per-file exact; flagged for W2). O1
forwarded to the running finalizer re-pass as an FYI lead; O2 rides
for W2 opinion. Fresh Worker 2 dispatched. In flight now: schema stale
W2 verification, types/finalizer stale W1 re-hunt, types/base stale W2
verification.

Fold 2026-09-22 17:03 UTC (Worker 0): schema stale re-pass VERIFIED
No bugs (W2 expectation-first, full R0-R9 agreement; replay 37/37 +
oracles 603 + 216 live; 31/31 attacks both cells; biting neuter
restored cmp-identical against W1's pristine pin; delta exactly the
10 +/- canonicalization lines; W1's "640" corrected as a 641-superset
erratum). No ledger (No bugs). Ticked; workspaces removed; expectation
retained. Dispatched sets_mixins narrow W1 re-pass (:549 third
re-derivation + bool-hostile twin + qualname mention; stale A20 WS
path corrected to the persisted /tmp repro texts). In flight now:
types/base stale W2 verification, types/finalizer stale W1 re-hunt,
sets_mixins stale W1 re-hunt.

Fold 2026-09-22 17:13 UTC (Worker 0): types/base stale re-pass
VERIFIED Fixed Low (W2 expectation-first E1-E18, zero
contradiction; replay polarity inverts exactly on WS-only revert;
28/28 attacks; fix shape minimal-in-contract by consequence with
the E10 pin stable; safety case closed empirically; honest bytes
identical; 235 + 604 + 113 + known-RED oracles; floor executed;
known-RED the only red, untouched). Ledger row appended (guard +
2 tests; O1 rides the running finalizer re-pass, O2 a robustness
row). Ticked; workspaces removed; expectation retained. Worker-0
mechanical checks pass (pins 40af4d12/30dc72f5; item diff +8/-2
+24/-0 pure, fence :972-991 + helper + 2 tests; probes in
stale-probes/ + w2-replay/ + w2-attacks/; no nested hunt-ws; gates
clean; prose clean). No new dispatch: the querysets re-pass is
queued behind the still-running finalizer re-pass. In flight now:
types/finalizer stale W1 re-hunt, sets_mixins stale W1 re-hunt.

Fold 2026-09-22 17:21 UTC (Worker 0): finalizer W1 re-pass
reported Fixed Low (O1 inherited-surface raw escape confirmed
with own probes: `:249` mro + `:250` definition reads; one-guard
fix + 2 tests; prior verdict re-proven without the foreign
hunk). Mechanical checks PASS with a count slip flagged for W2
(1+25+21=47 not 45; floor 26 vs default 25 scratch). O1-b/O1-c
relay observations ride for W2 judgment. Fresh Worker 2
dispatched with the A5-safety-case coupling criterion. In
flight now: finalizer stale W2 verification, sets_mixins stale
W1 re-hunt (its report landed during this Fold — folded next).

Fold 2026-09-22 17:21 UTC (Worker 0): sets_mixins W1 re-pass
reported Fixed Low (all three leads confirmed with own rows:
:549 third A20 derivation x4, bool-owner x3 + breadth + KI,
census proves (c) IS (a); 4-hunk fix + 9 tests). Mechanical
checks PASS (pins both eras; test `-` lines exactly the 2
imports; 7/7 probe sha256 match; WS cmp-identical; siblings
untouched; gates + prose clean; pragma pre-existing).
CORRECTION folded: the dispatch line's ae162e6e/6c42079f pins
were a stale memory — ground truth is 48b8ca20/9fca9442 ==
c9e39d31 blobs. B1 `__module__` boundary rides for W2 standing
judgment (same-item revision if confirmed); unprobed `__name__`
reads ride for W2 opinion. Fresh Worker 2 dispatched. In
flight now: finalizer stale W2 verification, sets_mixins stale
W2 verification.

Fold 2026-09-22 17:33 UTC (Worker 0): finalizer stale re-pass
VERIFIED Fixed Low (W2 expectation-first E1-E10, zero
contradiction; 47/47 replay + exact-polarity revert; honest
identity re-derived + own wider capture; 18/18 attacks incl.
the synthesis-caller shape; one-guard-minimal by consequence;
COUPLING HOLDS — the A5 safety case may rest here; 47-count
reconciled; O1-b/O1-c no standing as routed; floor 65/65).
Ledger row appended; relay routed-lead note recorded (verdict
stands). Worker-0 mechanical checks pass (expectation e8cff575;
pins + diff stable since the W1 fold; probes on disk; no
nesting). Ticked; workspaces removed; expectation retained.
Dispatched querysets narrow W1 re-pass (unblocked by the
finalizer close; `_LIST` re-derivation + `_DEFAULT`
confirm-and-report, no flip without Rio). In flight now:
sets_mixins stale W2 verification, querysets stale W1 re-hunt.

Fold 2026-09-22 17:38 UTC (Worker 0): sets_mixins stale re-pass
VERIFIED Fixed Low (W2 expectation-first E1-E11, zero
contradiction; 22/22 replay both cells; exact-polarity revert
with the census delta reconciled as designed; five-way honest
identity; 27/27 attacks both cells; M1-M5 minimal-in-contract;
oracle superset genuinely anchors with full-suite red-set
control; B1 NO STANDING — robustness row with card text, no
revision; unprobed names correctly-out-of-family; floor
throughout). Ledger row appended (4-hunk fix + 9 tests + B1
card text). Worker-0 mechanical checks pass (expectation
54ebd585; pins + diff stable; probes on disk; no nesting).
Ticked; workspaces removed; expectation retained. No new
dispatch: querysets is the last open file item. In flight now:
querysets stale W1 re-hunt (only).

Fold 2026-09-22 17:41 UTC (Worker 0, fresh session; the prior
Worker-0 was STOPPED BY THE MAINTAINER at 17:39 UTC, not a
provider error; nothing it dispatched is still running). Resume
validated: HEAD 5ee86193 unchanged (no Drift owed); census
108 items / 104 checked / 4 unchecked, 103 verified / 1 stale
(utils/querysets.py) / 4 pending — matches the 17:38 Fold.
Maintainer arm-deletions confirmed by diff content vs c9e39d31
(exactly the `except BaseException` removals + docstring
rewording, production-only): one-line notes on the routers.py,
rest_framework/sets.py and optimizer/nested_fetch.py items +
Owned changes, recorded digests updated to bc30430e / 70a1e1b1
/ d67e8d9d, verdicts stand, no stale opened; focused trio
340 passed. Disk 21 GB free, hunt-ws 337 MB, no nested
recursion. Dead querysets W1 workspace (no probes on disk)
deleted by explicit path. Dispatched fresh querysets narrow W1
re-pass (ITEM_BASELINE 785953ca re-minted — tree moved past
c9e39d31 via verified landings + maintainer edits; workspace
hunt-ws/querysets-stale-r2; `_LIST` re-derivation +
`_DEFAULT` confirm-and-report, no flip without Rio). In
flight now: querysets stale W1 re-hunt (only).

Fold 2026-09-22 18:08 UTC (Worker 0): querysets W1 re-pass
reported Fixed Low (D1 CONFIRMED with own R1-R8 + 44
probes before editing: raw plan-time/fetch-time
`NotSupportedError` escape; one-line `reject_combined=True`
fix + 5 prose restatements; `_DEFAULT` 9-surface census
CONFIRMED and REPORTED, not flipped) + 3 tests (5 nodes).
Mechanical checks PASS (item diff exactly the 2 files;
digests match; 44 collected exact; 10/11 pins + q00
caveat; pristine/simulated byte proofs; gates clean).
F1/F3/F4 ride for W2 judgment. Fresh Worker 2 dispatched
(workspace hunt-ws/querysets-stale-verify,
expectation-first, criteria K1-K6). In flight now:
querysets stale W2 verification (only).

Fold 2026-09-22 18:29 UTC (Worker 0): querysets stale re-pass
VERIFIED Fixed Low (W2 expectation-first E1-E12, zero
contradiction; 44 replay + C2 6/6 + C1 resolved; 126
attacks both cells; owner/tier/Low concurred; F1
prose-only no-stale, F3 acceptable with card advice, F4
standing-confirmed inside deferred scope extending the
`_DEFAULT` census; `_DEFAULT` byte-untouched; floor
executed). Ledger row appended. Ticked; workspaces
removed; expectation retained. Last file item closed:
104/104 checked, 104 verified, 0 stale. Dispatched
Scenario: Authorization and visibility across actors W1
(ITEM_BASELINE ba67c0e6, workspace
hunt-ws/scenario-authz-r1, single hunter, sensitive rule
armed, four standing leads named). In flight now:
authz scenario W1 hunt (only).

Fold 2026-09-22 18:56 UTC (Worker 0): authz scenario W1
reported No bugs (R1-R8; 38 live + 19 isolated green
ceiling + 10 floor; all 4 leads re-derived, none
confirmed; ORM + raw-SQL oracles; 4 biting controls;
2 robustness rows). Zero shared-tree edits.
Mechanical checks PASS (item diff empty; all 10
digests match; 16/16 pins + 4/4 restores; 38 + 19
re-run green in WS; no strays). Fresh Worker 2
dispatched (workspace hunt-ws/scenario-authz-verify,
expectation-first, duties K1-K6 with the deferrals +
robustness rows + depth search to judge). In flight
now: authz scenario W2 verification (only).

Fold 2026-09-22 19:12 UTC (Worker 0): authz scenario
VERIFIED No bugs (W2 expectation-first E1-E13, zero
contradiction with one honest self-refinement pinned
by W2-09; 38 + 19 replay exact; 17 independent probes;
deferrals + robustness rows + no-test rationale all
accepted with cited rows; 3 own controls; floor
re-executed; sharded/PG unverified for cause).
No ledger (No bugs). Ticked; workspaces removed;
expectation retained. Dispatched Scenario:
Transaction and session lifecycle W1 (ITEM_BASELINE
edf27c59, workspace hunt-ws/scenario-txn-r1, single
hunter, four standing leads named). In flight now:
txn scenario W1 hunt (only).

Fold 2026-09-22 20:53 UTC (Worker 0): txn scenario W1
reported Fixed — D1 High (cancel-during-enter
strands the window open: bare await abandoned while
the worker finishes `__enter__`; later mutations
nest inside: success payloads never committing) with
the shield-handoff owner fix + 4 tests, and D2 Medium
(test choreography circular-wait against the
handoff, gate released before await). Battery 42/42
green; pre-fix witness carried forward on disk
(TX10A-PREFIX.log) but NOT re-run pre-fix —
failability re-proof is W2's sharpest duty.
Mechanical checks PASS (item diff exactly schema.py
+ tests/test_schema.py; schema.py clean at baseline
so the delta is all fix — schema.py marked STALE,
bounded re-pass queued after scenario close;
collection 42 exact; 4/4 green in shared tree;
gates clean). Fresh Worker 2 dispatched (workspace
hunt-ws/scenario-txn-verify, expectation-first,
criteria K1-K6 incl. revert re-proof, D2
discrimination proof, severity + tier challenges,
flake runs, floor cell). Census: 104 verified /
1 stale (schema.py) / 3 pending. In flight now:
txn scenario W2 verification (only).

Fold 2026-09-22 22:11 UTC (Worker 0, fresh session; the prior Worker-0 was
FROZEN BY THE MAINTAINER right after its 20:53 UTC Fold and has now been
STOPPED, not a provider error). Nothing is running: the 20:53 Fold's "In
flight now: txn scenario W2 verification" names a dispatch whose workspace
hunt-ws/scenario-txn-verify/ does not exist — that Worker 2 never started.
Resume validated: run id 0.0.15-bf02c227486c59da9677c5d5707279815dfa9353;
baseline bf02c227 ancestor of HEAD (merge-base proven); cycle baseline block
untouched; HEAD ae52bdec confirmed by `git rev-parse --short`; Drift line
recorded above (5ee86193..ae52bdec, 11 commits). Disk 21 GB free, hunt-ws
328 MB, no nested recursion.

Drift inventory (all mechanical): package diff exactly filters/sets.py +
utils/relations.py, comment/docstring-only by diff content (one comment line
~1708; `instance_accessor` docstring ~703); reverse-apply reproduces recorded
c1a0f1b2 / 1cf81e58 byte-exact (YES/YES). tests/examples diff 56 paths:
main's real-model re-tiering, tests/optimizer/conftest.py deleted (restore now
in tests/conftest.py after every test; zero references in record or tests),
async `django_db` requires `transaction=True`, new migrations library 0007 /
products 0003 / scalars 0002. Ledgered test files touched (14, by
intersection): test_resource_policy_api.py, auth/test_mutations.py,
filters/test_base.py, filters/test_sets.py, forms/test_inputs.py,
mutations/test_resolvers.py, mutations/test_sets.py,
optimizer/test_nested_index_advisory.py, rest_framework/test_converter.py,
test_list_field.py, test_routers.py, types/test_base.py,
types/test_converters.py, utils/test_querysets.py; plus test_schema.py
(pending-scenario item-record nodes). Maintainer merge edits preserved
untouched: join_taxonomy Genre port; test_resolvers/test_converters
re-tiering wins; big_auto/relation-primary/unplanned-login removals (all
non-hunt by record grep).

Mechanical duty: every hunt-ledgered node in those 15 files re-run focused
(`--no-cov -n0`) in the shared tree — batch A 39 passed, B 44 passed, C 56
passed, D 8 passed = 147/147 green, 0 collection errors, 0 failures; zero
hunt tests removed (4 removed-test lines all attributed non-hunt).
Reconciliation vs the brief's file list: mutations/test_inputs.py +
optimizer/test_extension.py carry only DRY/concurrent tests (zero hunt nodes,
no runs owed); resource_policy_api.py (2 live nodes, green) is
ledgered-and-touched and ran. Extras: join_taxonomy port 2/2 green, scalars
big-auto live cover green, HStore pin green in this cell (standing pg
observation stays with Rio), RED decision test still red with the identical
guard error (DECISION REQUEST unchanged). No item goes stale from this duty.

Census (re-derived by production-digest sweep over all 102 file items):
worktree digest absent from the block for exactly 4 verified items —
filters/sets.py (comment drift), utils/relations.py (docstring drift),
inspect_django_type.py 46dffb3d→9d0aec73 (DRY docstring),
mutations/inputs.py fc442047→fcbb964d (DRY code); all 38 ledger production
paths dirty-vs-HEAD (no fix lost); 9 non-ledger dirty files all attributed.
Digest-rule census: 100 verified / 5 stale / 3 pending — AGREES with the
brief exactly. Review-driven delta: types/base.py marked stale now per 5c
(digests match at 40af4d12; stale for the coverage re-pass, not digest
drift) — going census 99 verified / 6 stale / 2 pending + 1
revision-needed. Scenario entry digests are historical anchors (drift
reconciled at verification), not staleness triggers.

Evidence hygiene 5f: recount 131 unique cited w2 files, 44 cited-present +
1 uncited-present (w2-types-base-expectation-r2.txt) = 45 on disk, 87
missing — recorded honestly, never back-filled. hunt-ws/converters-pin-verify/
+ hunt-ws/converters-pin-w2verify/ removed by explicit path (436K): no
Cleanup line accounts for them; sole citation is the historical import note
(the standing verdict rests on the permanent pins + retained
w2-converters-pin-expectation.txt) — judged not live evidence, removal
recorded here. From now on Worker reports go under hunt-ws/reports/ (in
every dispatch brief). hunt-ws/floor-310/ stays.

Maintainer review 2026-09-22 (Rio):
- [5a-A High] Exit-side hole in the same function: `schema.py::_execute_mutation_field_async` still does bare `await run_in_one_sync_boundary(_exit_clean)` (~:422) and `(_exit_with_error)` (~:409); asgiref cancels QUEUED work outright, so one client `complete` while the exit is queued behind another socket's call strands the row in an open atomic after lock release; the "lock-release on every arm" claim is false for this function; expected shape is one helper driving a boundary call to its known outcome across cancellation and re-raising the first cancellation afterwards, for all three transitions (enter, `_exit_with_error`, `_exit_clean`), replacing the special-cased enter block. → txn W1 revision.
- [5a-B Low] Two arms swallow the cancellation: `opener_cancelled` overwritten by the enter error (~:365, raised ~:395); failed handoff exit replaces the `CancelledError` (~:390); `asyncio.timeout` no longer yields `TimeoutError`, `TaskGroup` sees an error instead of a cancel, `task.cancelling()` stays raised; precedent `_AsyncAliasLock.__aenter__` (~:127-145) catches only `CancelledError` and always re-raises it; the new code catches `BaseException`. → txn W1 revision.
- [5a-C Low] Opener self-cancel (loop teardown): `opener.exception()` (~:368) raises `CancelledError` and a completed enter is left open. → txn W1 revision.
- [5a-T1] tests/test_schema.py ~:568-571 docstring ("delete `task.cancel()` and every assertion still passes") is false. → txn W1 revision.
- [5a-T2] Test 2 (~:635) passes pre-fix and does not cover the arm it names (enter failed DURING a cancel). → txn W1 revision.
- [5a-T3] Test 3 cleanup (~:751) is not in a `finally`: a failure leaves the worker thread inside an atomic and poisons later tests. → txn W1 revision.
- [5a-T4] Test 4 (~:758) does not discriminate the closer's shield loop (gate submits the exit before gating, so a bare await passes too; pre-fix fails only via the 10 s timeout). → txn W1 revision.
- [5a-R1] "Defect 2 Medium (test choreography)" names no contract row: under AGENTS.md rule 35 it is not a defect and carries no severity; re-record as test-construction errata. → txn W1 revision (record correction).
- [5a-R2] Mechanism overstated for real deployments: Django ASGI HTTP heals via `request_finished` → `close_old_connections` (Low at most); Channels (shared executor, no `ThreadSensitiveContext`) likely errors every later query on that thread for the process lifetime; "nested success never commits" observed only where nothing closes connections (the test harness); High stands for the WebSocket path; severity factors must say which tier and why. → txn W1 revision (record correction).
- [5a-R3] Contract rows: GOAL.md ~:546 (goal 6) and GLOSSARY.md ~:41 (`DjangoMutationExecutionContext` holds the transaction until completion). → txn W1 revision.
- [5a-W2.1] The fresh W2 MUST prove the permanent tests fail against HEAD's `schema.py` where they claim to (and say which cannot). → txn W2 criterion.
- [5a-W2.2] The fresh W2 MUST prove a gate-free reproduction (slow `__enter__`, e.g. delay in `ensure_connection`, unmodified asgiref) leaks pre-fix and is clean post-fix. → txn W2 criterion.
- [5a-W2.3] The fresh W2 MUST prove the exit-side hole A is red pre-revision and green post-revision. → txn W2 criterion.
- [5a-W2.4] The fresh W2 MUST prove swapping each shield loop for a bare await turns at least one test red. → txn W2 criterion.
- [5a-W2.5] The fresh W2 MUST prove cancellation or `TimeoutError` identity is preserved on every arm. → txn W2 criterion.
- [5a-W2.6] The fresh W2 MUST prove repeated runs show no flake. → txn W2 criterion.
- [5a-W2.7] The fresh W2 MUST prove the floor cell passes. → txn W2 criterion.
- [5a-W2.8] The fresh W2 MUST prove both flavors are covered: HTTP ASGI and Channels. → txn W2 criterion.
- [5b] 8 ledger rows meet all three rule-35 legs (connection.py negative cursor; resource_policy directive/default charging; resource_policy spread-site charge; utils/connections.py empty-cursor presence; join_taxonomy multi-column ForeignObject; serializer_converter nullable-element + allow_blank; utils/querysets combinator reject; nested_planner M2M advisory). → recorded as `Class: defect` on those rows.
- [5b] 37 rows are ROBUSTNESS rows (reproducers only raising/lying `__class__`, metaclasses with raising `__name__`/`__mro__`/`__dict__`/`__hash__`/`__getattr__`/`__module__`, `str` subclasses with raising dunders; no feasible project shape, no wire/settings input reaches them). → recorded as `Class: robustness`; NOT reverted/re-dispatched; whether reached guards stay is an open Rio decision, carried.
- [5b] 2 rows are whitespace-only lint rows → `Class: lint`; row 1 (fixture isolation, symbols committed at HEAD) is stale → `Class: stale-row`. → recorded.
- [5b] Standing rule from now on: every W1 report names all three rule-35 legs per claimed defect; every W2 rejects (`revision-needed`) a "Fixed <severity>" whose reproducer is only a hostile/lying metaclass, dunder or class shape (record as robustness row, no fix, no severity). → in every dispatch brief.
- [5c] Coverage blockers: 106 hunt-added `except BaseException` arms, 4 reached by NO test, all in types/base.py (~:386 dict-spoof `relation_shapes`; ~:686 near-unreachable behind :682; ~:865 liar `id` on Relay shape; ~:1737 unreachable at class creation behind :1195); `fail_under = 100` fails the gate. → types/base.py marked stale now; bounded W1 re-pass queued (order 6d).
- [5c] Standing ruling (2026-09-22 arm deletions): an arm no test reaches and no feasible project shape reaches is DELETED, never tested with a new hostile shape, never `pragma: no cover`. → in the re-pass brief.
- [5c] Same re-pass also fixes the stray spaces inside docstrings (~:664, :675) and the false comment at ~:1589 ("Honest `bool` subclasses keep passing"; `bool` cannot be subclassed). → types/base re-pass scope.
- [5c] Behavior change recorded on the item: the new rejection at ~:713 (a DjangoType whose `__name__` is not an exact `str` fails at class creation). → types/base re-pass scope (the standing RED decision test is this guard's casualty — unchanged).
- [5c] DECISION REQUEST (Rio): posture contradiction — utils/directives.py ~:31 documents `BaseException` deliberately NOT caught (`KeyboardInterrupt`/`SystemExit` propagate) while hunt arms swallow both into False; whether hostile-value arms narrow to `Exception`. Carried, not acted on.
- [5d] mutations/sets.py ~:1243/:1661 + mutations/fields.py ~:297 route the ERROR-LABEL renderer into GraphQL TYPE NAMING (raising `__name__` publishes a `<MetaclassName>Payload` type instead of failing; tests/mutations/test_fields.py ~:211 pins it). → record on owning items + fresh W2 challenge (order 6e); product-semantics dispute → `blocked` for Rio, never regraded.
- [5d] rest_framework/sets.py ~:196 rejects non-identifier keys from `get_serializer_for_schema` (new rejection). → same routing (order 6e).
- [5d] filters/inputs.py ~:807 + filters/sets.py ~:2403 raise where the old code silently did nothing (direct-Python only). → same routing (order 6e). CORRECTION (W2 6e-3, concur with record fix): sets.py reach is "direct-Python + overlap-wire" (declared+generated merged bag, B19/B22/B23); inputs.py reach confirmed direct-Python-only.
- [5d] utils/querysets: the "combined" message is reworded on the list-argument surfaces. → same routing (order 6e).
- [5d] serializer_converter allow_blank fix changes the PUBLISHED schema (enum → String). → DECISION REQUEST: Rio signs off before the gate.
- [5e] filters/inputs.py ~:782 docstring "the previous arms SPLATTED" (hunt-added process provenance; the :637 same-phrase is HEAD's, not ours). → bounded W1 revision on the owning item (order 6e).
- [5e] tests/test_resource_policy.py ~:3011 "proves the fix reaches a real request" (process provenance in a test). → bounded W1 revision on the owning item (order 6e).
- [5e] routers.py ~:256 mis-indented renumbered list + sets_mixins.py ~:466 misaligned docstring line. → bounded W1 revisions, each on its owning item, or folded into an already-queued re-pass (order 6e).
- [5f] 131 cited w2 expectation files, 44 present (+1 uncited-present), 87 missing incl. 15 on retained-until-closeout items (scalars, schema, sets_mixins, testing/_wrap, client, relay, types/base, converters, types/relay, types/resolvers, utils/canonical, connections, context, converters, pagination scenario) — recorded honestly, never re-created or back-filled. → recorded; retention rule re-asserted in dispatch briefs.
- [5f] converters-pin-verify/ + converters-pin-w2verify/ unaccounted by any `Cleanup:` line → removed by explicit path (this Fold), recorded. → done.
- [5f] 49 cited Worker reports under bare `/tmp` (volatile) → from now on hunt-ws/reports/ (in dispatch briefs). → done.
- [5f] hunt-ws/floor-310/ stays (shared testbed). → kept.

Routing + order of work: 6a txn revision dispatched now (fresh W1,
ITEM_BASELINE 39e2512e81bf5e396237f07c286071a9606e253f, workspace
hunt-ws/scenario-txn-r2; r1 orientation only; brief carries 5a A/B/C + T1-T4
+ R1-R3, the W2.1-W2.8 acceptance preview, the rule-35 three-legs standing
rule, hunt-ws/reports/, hunt-ws exclusion). Then 6b schema bounded re-pass
after scenario close; 6c four stale re-verifications (filters/sets.py +
utils/relations.py comment-drift bounded W2; inspect_django_type.py DRY-doc
bounded W2; mutations/inputs.py DRY-code real W2); 6d types/base re-pass;
6e 5d W2 challenges + 5e revisions; 6f integration (re-inventory `.py`
added/removed incl. main's new migrations + scripts/census_test_models.py);
6g gate (blocked while any naming DECISION REQUEST is open). Open decisions
carried unchanged (10 standing + guards-stay + BaseException-narrowing +
allow_blank schema sign-off). In flight now: txn scenario W1 revision
(only).

Fold 2026-09-22 22:19 UTC (Worker 0): txn revision W1 dispatch died on
model-stream idle timeout (infra failure, 730 log lines, never acted): no
workspace built, no report, no shared-tree edits (fence diff vs 39e2512e
empty; only movement is this file's own Fold). Nothing to inherit, nothing
to clean. Fresh Worker 1 dispatched (ITEM_BASELINE 38d6fc98 re-minted —
tree moved by the Fold; workspace hunt-ws/scenario-txn-r2, path was
unused; identical brief + the death noted). In flight now: txn scenario W1
revision (only).

Fold 2026-09-22 23:46 UTC (Worker 0): txn r2 W1 revision reported (one
driver helper for all three transitions + settlement guard; T1 fixed, T2
replaced, T3 renamed with `finally`, T4 rewritten pre-submit, 6 new B1-B6
rows; R1/R2/R3 corrections claimed; rule-35 legs stated). Mechanical
checks PASS (digests/fence/erratum/venv/strays/tokens/pragma/ruff/delta/
anchor/independent 12/12/counts/controls/cells — full list in Iteration
4). Fresh Worker 2 two-phase dispatched (workspace
hunt-ws/scenario-txn-verify; fenced phase 1, drop-gated phase 2; staged
probe sha-verified). Census unchanged: 99 verified / 6 stale / 2 pending
+ 1 revision-needed. In flight now: txn scenario W2 verification phase 1
(expectation pending W0 contamination check before the phase-2 drop).

Fold 2026-09-22 23:52 UTC (Worker 0): txn W2 phase-1 expectation LANDED
(hunt-ws/w2-scenario-txn-expectation.txt, 15.9 KB: C1-C4 contract
derivation, M1-M7 mechanism model from live source + diff, R1-R10
per-row expectations with falsifiers, blind polarity tables incl.
R10@HEAD-green + floor R2/R3-green "cannot fail" predictions, W2.2-W2.8
expectations, A1-A9 attack plan). Contamination check PASS (zero
forbidden-source cites by grep; sealed before first run by mtime +
the R4@HEAD refinement honestly recorded in the run record, not the
expectation). Hash-pinned f1b3b805 (W2 forbidden to modify it further).
Phase-1 runs so far: R0 post-fix 10/10, blind ITEM revert GRRGGRRRRR
exact match, blind HEAD revert RRRRRRRRRG exact match, restore
hash-proved; WS anchor inside $WS. Phase-2 drop written
(hunt-ws/txn-verify-phase2/DIAGNOSIS.txt) with 10 ride-alongs (inventory
reconciliation, B6, T4, F1, tiers, placement, prose, /tmp, suite note,
rule-35 legs). In flight now: txn scenario W2 verification phase 2
(reconciliation + verdict).

Fold 2026-09-23 00:10 UTC (Worker 0): txn W2 verdict revision-needed —
CH-1 (R5 docstring iteration labels; W0 scan-miss owned, vocabulary
widened) + CH-2 (defect C real but Proof missing; helper uncalled).
Everything else verified: blind polarity exact on both eras, B6/F1/T4/
tiers/placement/prose all agreed, W2.1-W2.8 proven with independent
variants/probes/flavors/floor. R2 mechanism corrected to
ThreadSensitiveContext isolation (W2 code-traced; tiers stand). Narrow
W1 re-pass dispatched (ITEM_BASELINE 1bb311a9, r2 workspace reused
intact, preserved scope frozen). Census unchanged: 99 verified / 6
stale / 2 pending + 1 revision-needed. In flight now: txn scenario W1
narrow revision r3 (CH-1 + CH-2 only).

Fold 2026-09-23 00:17 UTC (Worker 0): txn r3 narrow re-pass reported
(CH-1 timeless + retired; CH-2 teardown pin calling the helper, O1
closed; red bytes correctly read as r1 blob d0c79838). Mechanical
checks PASS (digests, tests-only 2-hunk 79+/3- fence, schema.py 0
lines, sweeps/gates/pragma clean, independent 154-file + 3x-pin
greens, anchor green). Fresh W2 narrow re-verification dispatched
(K1-K5, fresh workspace hunt-ws/scenario-txn-verify2). Census
unchanged: 99 verified / 6 stale / 2 pending + 1 revision-needed. In
flight now: txn scenario W2 re-verification (only).

Fold 2026-09-23 00:23 UTC (Worker 0): txn re-verification VERIFIED K1-K5
(timeless + retired + AST-identical; pin red-on-r1-blob with arm reached
+ green post + red under all 3 vacuity attacks; 3x + 154/154 + 12/12;
exact 2-hunk fence + 3 gates + no pragma + zero-hit sweeps; event-driven
pin + clean adjacency + 3.10 floor collect AND pass). Scenario CLOSED:
Result Fixed High (A) + 2 Lows (B, C), ledger row 49 (Class: defect,
9th), 6 scratch paths removed by explicit path (hunt-ws 328 MB to 151
MB; expectation + 5 reports retained). Order 6a DONE. Census now: 100
verified / 6 stale / 2 pending (integration + gate). Order 6b
dispatched: bounded schema.py stale re-pass W1 (ITEM_BASELINE a79056f2,
workspace hunt-ws/schema-stale-r2; R0-R9 re-proof at 6f238a09/266a09e0
+ compatibility with the verified handoff, no full re-hunt). In flight
now: schema stale W1 re-pass (only).

Fold 2026-09-23 00:36 UTC (Worker 0): schema bounded re-pass reported
No bugs, zero edits (R0-R9 re-proven at 6f238a09; compat clean; drift
byte-exact; M1/M2 bite with cmp-identical restores; cells honest).
Mechanical checks PASS (digests, empty fence-vs-ITEM, HEAD blob + log +
diffstat + hunk counts re-verified, WS hashes equal, anchor green,
battery collects 46, strays pre-existing only, no /tmp cites). Fresh
W2 two-phase dispatched (fenced phase 1 from quoted R0-R9; expectation
hunt-ws/w2-schema-stale-expectation-r2.txt; workspace
hunt-ws/schema-stale-verify2; drop gated on contamination check).
Census unchanged: 100 verified / 6 stale / 2 pending. In flight now:
schema stale W2 verification phase 1 (only).

Fold 2026-09-23 00:42 UTC (Worker 0): schema W2 phase-1 expectation
LANDED (hunt-ws/w2-schema-stale-expectation-r2.txt, 29.7 KB: byte eras
verified, R0-R9 expectations with falsifiers, standing rows, own
attack plan, S1-S5 compat seams, drift + oracle plan). Contamination
check PASS (only hits are the declaration lines 9-13; sealed before
first run). Hash-pinned ae2902ef (no further modification). Phase-2
drop written (hunt-ws/schema-verify2-phase2/DIAGNOSIS.txt) with 8
ride-alongs (reconciliation, R2 trigger, R7/PG/sharded, controls,
floor, zero-edit, seams, rule-35). In flight now: schema stale W2
verification phase 2 (reconciliation + verdict).

Fold 2026-09-23 01:06 UTC (Worker 0): schema bounded re-pass VERIFIED
(102 own probes both cells + 46/46 replay + 547 oracles + neuter
spot-replays; all 8 ride-alongs agree; 2 nits not challenges).
Item closed per single-triple practice (Iterations 7-8 carry this
cycle; Cleanup accumulates; Result cites original bytes). 3 scratch
paths removed. Order 6b DONE. Census now: 101 verified / 5 stale /
2 pending. Order 6c dispatched (1/4): filters/sets.py comment-drift
bounded W2 (ITEM_BASELINE 53f8c2be, workspace
hunt-ws/filters-sets-drift-verify; K1-K5 incl. recorded-digest
reproduction + AST-equivalence + oracle replay + failability spot).
In flight now: filters/sets drift W2 (only).

Fold 2026-09-23 01:14 UTC (Worker 0): filters/sets drift re-proof
VERIFIED K1-K5 (recorded bytes reproduced; AST-identical; 25/25 + 1/1
+ 268/268 green; guard neuter red + cmp-identical restore; gates +
fence clean; comment timeless). Item closed per single-triple
practice (Iteration 9 carries this cycle; Cleanup accumulates).
Workspace removed. Census now: 102 verified / 4 stale / 2 pending.
Order 6c dispatched (2/4): relations docstring-drift bounded W2
(ITEM_BASELINE c59f1ceb, workspace hunt-ws/relations-drift-verify;
K1-K5 with the docstring-AST soundness warning + DRY-hunk
byte-identity + oracle replay + biting-control spot). In flight now:
relations drift W2 (only).

Fold 2026-09-23 01:19 UTC (Worker 0): relations drift re-proof
VERIFIED K1-K5 (recorded bytes reproduced; three-way attribution
complete with DRY hunk byte-identical; sound docstring-null proof;
126/126 both trees; Control A exact signature; gates + fence clean;
drift text source-verified accurate). Item closed per single-triple
practice (Iteration 4 carries this cycle; Cleanup accumulates).
Workspace removed. Census now: 103 verified / 3 stale / 2 pending.
Order 6c dispatched (3/4): inspect DRY-docstring bounded W2
(ITEM_BASELINE 2ebd788b, workspace hunt-ws/inspect-drift-verify;
K1-K5 with DRY-record content-match + docstring-AST soundness
warning + oracle replay + control spot). In flight now: inspect
drift W2 (only).

Fold 2026-09-23 01:23 UTC (Worker 0): inspect drift re-proof
VERIFIED K1-K5 (DRY hunk content-matched; sound docstring-null proof;
19/19 + 24/24 green; _yes_no neuter same-family red + restore;
gates + fence clean; paragraph identical modulo citation). Item
closed per single-triple practice (Iteration 3 carries this cycle;
Cleanup accumulates). Workspace removed. Census now: 104 verified /
2 stale / 2 pending. Order 6c dispatched (4/4): inputs REAL
re-verification W2 two-phase (ITEM_BASELINE 8b033541, workspace
hunt-ws/mutations-inputs-verify2; fenced phase 1 from contract
sketch + shadow baseline + DRY diff; expectation
hunt-ws/w2-mutations-inputs-expectation-r2.txt; drop gated on
contamination check). In flight now: inputs W2 phase 1 (only).

Fold 2026-09-23 01:29 UTC (Worker 0): inputs W2 phase-1 expectation
LANDED (hunt-ws/w2-mutations-inputs-expectation-r2.txt, 17 KB: byte
eras verified, AREA 0 delta analysis with S1-S5 seams incl. the
double-read bound, Areas 1-8 with falsifiers, P0-P8 attack plan with
A-vs-B differential + lying-descriptor bound probe, oracle + cell
plan). Contamination check PASS (zero forbidden cites; sealed before
first run — workspace did not exist yet). Hash-pinned 15da4e46 (no
further modification). Phase-2 drop written
(hunt-ws/inputs-verify2-phase2/DIAGNOSIS.txt) with 9 ride-alongs
(reconciliation, S1 bound, equivalence, robustness rows, S5,
oracle counts, cells, DRY intent, fence). In flight now: inputs W2
phase 2 (reconciliation + verdict).

Fold 2026-09-23 01:58 UTC (Worker 0): inputs REAL re-verification
VERIFIED (P0 differential parity + 646-field sweep + 82-model dumps
identical; 34 probes + 10 neuters; 206/206 + 62/62 reach; floor
green; 2091 oracles + 8851x2 full-suite identical with all non-green
classified; 8/8 reconciled; S1 bound as new robustness row).
Item closed per single-triple practice (Iteration 3 carries this
cycle; Cleanup accumulates). 9 scratch paths removed by explicit
path. Order 6c DONE (4/4). Census now: 105 verified / 1 stale /
2 pending (types/base + integration + gate). Order 6d dispatched:
types/base bounded W1 re-pass (ITEM_BASELINE 547c2790, workspace
hunt-ws/types-base-armcut-r1; delete 4 unreached arms under the
standing ruling + 2 prose fixes; :713 guard frozen; coverage proof
in WS only). In flight now: types/base armcut W1 (only).

Fold 2026-09-23 02:14 UTC (Worker 0): types/base armcut re-pass
reported (4 arms deleted + (e)/(f) prose + 2 consequential sentences;
tests byte-identical; ea1d6083). Mechanical checks PASS (digests;
fence exactly base 14+/28- in 7 hunks read-and-matched with :713
region clean; oracle 233 independent green; RED identical message
at :699; sweeps/pragma/gates clean; venv intact; no strays).
Coverage re-proof rides to W2. Fresh W2 two-phase dispatched
(fenced phase 1 from arm locations + diff + oracles; expectation
hunt-ws/w2-types-base-armcut-expectation.txt; workspace
hunt-ws/types-base-armcut-verify; drop gated on contamination
check). Census unchanged: 105 verified / 1 stale / 2 pending. In
flight now: types/base armcut W2 phase 1 (only).

Fold 2026-09-23 02:25 UTC (Worker 0): armcut W2 phase-1 expectation
LANDED (hunt-ws/w2-types-base-armcut-expectation.txt, 30 KB: fence
verified by reading, ruling under test, verbatim pre-delete arms,
coverage predictions, per-arm infeasibility derivations with quoted
guards, prose + RED + oracle + differential + attack predictions).
Contamination check PASS (only hit is the declaration line 437).
Hash-pinned f20bd7e6 (no further modification). Noted for phase 2:
coverage granularity (11 physical vs 8 reported) + a RED frame-shift
arithmetic discrepancy (W2 predicts -6, W1 claims -9) — both ride as
reconciliation items, runs decide. Phase-2 drop written
(hunt-ws/armcut-verify-phase2/DIAGNOSIS.txt) with 9 ride-alongs. In
flight now: types/base armcut W2 phase 2 (reconciliation + verdict).

Fold 2026-09-23 02:51 UTC (Worker 0): armcut W2 VERIFIED (full-suite
coverage pre 8-miss + post 602/602 + annotate proof + positive
control; 82/82 differential + gapclose twins; attacks in-envelope;
RED identical modulo explained -9; oracles + covering set + floor
mirror; 9/9 ride-alongs agree; 6 non-blocking remarks incl. R-rep
erratum correcting Iteration 11's "31 rows" to 27). Item closed per
single-triple practice (Iteration 12 carries this cycle; Cleanup
accumulates; ledger row 50, Class: robustness — counts now 9/38/2/1).
3 scratch paths removed. Order 6d DONE. Census now: 106 verified /
0 stale / 2 pending (integration + gate). Order 6e dispatched (1/7):
5d naming W2 challenge (mutations/sets.py + mutations/fields.py;
ITEM_BASELINE 0c354262, workspace hunt-ws/5d-naming-verify; Q1-Q3;
verdict concur-or-blocked, never regrade). Behavior changes recorded
on both items + allow_blank DECISION on serializer_converter (no
challenge — decision-owned). In flight now: 5d naming W2 (only).

Fold 2026-09-23 02:59 UTC (Worker 0): 5d naming challenge verdict
BLOCKED-FOR-RIO (Q1 reproduced exactly; Q2 11-shape invariance
proven; Q3: collision possible + orphan refuted + fail-loud
alternative proven + trigger infeasible + surfacing silent; Q3-R7
correction: :1243 label-only, decision point :1105). It7 concur NOT
sustained. EXACT QUESTION FOR RIO recorded on both items: (A)
publish degraded `<MetaclassName>Payload` or (B) reject at
definition typed. DECISION REQUEST open (naming posture). Both items
blocked (prior Fixed-Low verifications stand for the hunt; dispute
is product semantics only). Workspace removed. Census now: 104
verified / 0 stale / 2 pending / 2 blocked. Order 6e dispatched
(2/7): 5d rfsets identifier W2 challenge (ITEM_BASELINE 3e27c255,
workspace hunt-ws/5d-rfsets-verify; Q1-Q3; concur-or-blocked).
Behavior change recorded on the item. 5d rfsets identifier W2
challenge CONCURRED (Q1 both-eras exact; Q2 honest byte-identical,
accepted->rejected shapes all need producer-authored non-identifier
bindings; Q3 deprecate-first named and declined; shared tree never
edited, digests 70a1e1b1/85c4c3a0, fence-vs-ITEM empty; report
hunt-ws/reports/w2-5d-rfsets-report.txt; workspace removed; item stays
verified). Census unchanged: 104 verified / 0 stale / 2 pending / 2
blocked. Order 6e dispatched (3/7): 5d filters silent-to-error W2
challenge (ITEM_BASELINE d4f70cda, workspace hunt-ws/5d-filters-verify;
inputs.py ~:807 `_normalize_range_value` + sets.py ~:2403, Q1-Q3 each;
concur-or-blocked). Behavior changes recorded on both items. 5d
filters silent-to-error W2 challenge joint-CONCURRED (Q1 both-eras
exact incl. pre-fix silence shapes; Q2 39 honest rows byte-identical,
28 trigger rows inventoried; Q3 both silences uncontracted-wrong,
deprecate-first named and declined; (a) reach direct-Python-only
CONFIRMED; (b) reach CORRECTED to direct-Python + overlap-wire per the
required record correction — [5d] row + Iteration 10 annotations
amended, no maintainer question; 8-node erratum noted; shared tree
never edited, fences re-hashed, fence-vs-ITEM empty; report
hunt-ws/reports/w2-5d-filters-report.txt; workspace removed; both
items stay verified). Census unchanged: 104 verified / 0 stale / 2
pending / 2 blocked. Order 6e dispatched (4/7): 5d querysets reword W2
challenge (ITEM_BASELINE b38957c6, workspace hunt-ws/5d-querysets-verify;
"combined" message reword, Q1-Q3; concur-or-blocked). Behavior change
recorded on the item. 5d querysets reword W2 challenge CONCURRED (Q1
old/new verbatim both eras on L1-L4 + runners; Q2 no-delta proven —
co_code identical, single literal const differs, honest inputs
byte-identical, old-text census zero affirmative; Q3 no prose
contract, keep-old-text named and declined; shared tree never edited,
fences re-hashed, fence-vs-ITEM empty; report
hunt-ws/reports/w2-5d-querysets-report.txt; workspace + expectation
removed; item stays verified). Census unchanged: 104 verified / 0
stale / 2 pending / 2 blocked. Order 6e dispatched (5/7): 5e prose W1
revision row 1 (ITEM_BASELINE 55810cc7, workspace hunt-ws/5e-inputs-prose;
filters/inputs.py :783 SPLATTED docstring; :637 stays; W2 follows
in-unit). 5e inputs-prose W1 LANDED (docstring-only -4/+2, f4d41917;
Worker-0 mechanical checks pass: exact hunk, :637 identical, focused 8
green, ruff clean, tests fence untouched). Fresh Worker 2 verification
dispatched in-unit (ITEM_BASELINE 2396091c, workspace
hunt-ws/5e-inputs-prose-verify). Census unchanged: 104 verified / 0
stale / 2 pending / 2 blocked. 5e inputs-prose W2 VERIFIED (K1-K6
all PASS; independent co_code proof + failability; 3 immaterial
discrepancies; test-docstring provenance observation out-of-scope,
awareness only; shared tree never edited, fences re-hashed,
fence-vs-ITEM empty; report hunt-ws/reports/w2-5e-inputs-prose-report.txt;
workspaces removed, expectation retained). [5e] row 1 CLOSED; item
stays verified. Census unchanged: 104 verified / 0 stale / 2 pending /
2 blocked. Order 6e dispatched (6/7): 5e prose W1 revision row 2
(ITEM_BASELINE 9d0cdf64, workspace hunt-ws/5e-rp-prose;
tests/test_resource_policy.py :3011 test-docstring provenance;
test-only; W2 follows in-unit). 5e rp-prose W1 LANDED (test-docstring-only
+2/-2, e18a7d06; Worker-0 mechanical checks pass: exact hunk, old phrase
gone, focused 1 green, ruff clean, production + live untouched; W1's
out-of-role `git stash create` noted harmless). Fresh Worker 2
verification dispatched in-unit (ITEM_BASELINE 0169b69a, workspace
hunt-ws/5e-rp-prose-verify). 5e rp-prose W2 VERIFIED (K1-K6 all PASS;
whole-module co_code proof + failability; touched test green + 299
collected; ruff clean; ZERO report discrepancies; shared tree never
edited, fences re-hashed, fence-vs-ITEM empty; report
hunt-ws/reports/w2-5e-rp-prose-report.txt; workspaces removed,
expectation retained). [5e] row 2 CLOSED; item stays verified. Census
unchanged: 104 verified / 0 stale / 2 pending / 2 blocked. Order 6e
dispatched (7/7): 5e layout W1 revision row 3 (ITEM_BASELINE 33b70ed1,
workspace hunt-ws/5e-layout-prose; routers.py :256 list indent +
sets_mixins.py :466 docstring alignment; comment/docstring-only; W2
follows in-unit). 5e layout-prose W1 LANDED (whitespace-only 6 lines
across both files, 2f906095/c37c7b87; Worker-0 mechanical checks pass:
exact two hunks, -w diff empty, focused 2 green, ruff clean, both test
fences untouched). Fresh Worker 2 verification dispatched in-unit
(ITEM_BASELINE 96833df4, workspace hunt-ws/5e-layout-prose-verify;
joint). Census unchanged: 104 verified / 0 stale / 2 pending / 2
blocked. 5e layout-prose W2 VERIFIED joint (K1-K6 all PASS;
independent indent re-measurement + content-invariance; co_code 13/13 +
40/40 + failability; own nearest tests + collections + W1 replay;
ruff clean; ZERO report discrepancies; shared tree never edited,
fences re-hashed, fence-vs-ITEM empty; report
hunt-ws/reports/w2-5e-layout-prose-report.txt; workspaces removed,
expectation retained). [5e] row 3 CLOSED on both items; both stay
verified. ORDER 6e COMPLETE (7/7). Census unchanged: 104 verified / 0
stale / 2 pending (integration + gate) / 2 blocked. 6f re-inventory
(Worker-0 mechanical, tracked .py CYCLE_BASELINE -> now): 9 added
(library migrations 0005/0006/0007, products 0003, scalars 0002,
test_input_shapes_api, test_library_inheritance_api,
test_library_shapes_api, scripts/census_test_models.py) + 1 removed
(kanban test_mutations.py); zero package/tests structural change; zero
untracked non-hunt-ws .py. Dispositions: closing notes (main-side
examples/scripts, outside package scope) unless the integrator shows a
file is package-surface-relevant. Integration W1 dispatched
(ITEM_BASELINE 2aa42403, workspace hunt-ws/integration; brief carries
the inventory + digest-vs-record sweep step). Integration W1
REPORTED Fixed Low (1 defect Area D: FieldError.field wire-name split
across mutation flavors; root-cause fix at the shared mapper seam + 4
new tests; Areas A-C No bugs; sweep CLEAN). Worker-0 mechanical checks
pass (item diff exactly the 8 files + progress; all 8 sha256 match;
focused 4/4 green; ruff clean; no new pragma). Fresh Worker 2
verification dispatched in-unit (ITEM_BASELINE bb993f4b, workspace
hunt-ws/integration-verify; K1-K9 incl. independent sweep re-derivation).
Census unchanged: 104 verified / 0 stale / 2 pending / 2 blocked.
Lint note: repo-wide `ruff check` surfaces 1 pre-existing error (D100 on
untracked 0-byte concurrent scratch `1_introspect.py`, dated before this
run's edits) — concurrent work, left untouched; all hunt-owned files
pass. Integration W2 verdict: REVISION-NEEDED test-side only (defect
real, seam fix correct, 8/9 pass; K6 FAIL on 3 stale snake-key pins
W1's survey missed; production stands; shared tree never edited,
fences re-hashed, fence-vs-ITEM empty; report
hunt-ws/reports/w2-integration-report.txt; pre-existing list_field
failure + 11 environmental conftest errors noted identical pre/post
for gate-time triage). Fresh narrow W1 re-pass dispatched
(ITEM_BASELINE a6862498, workspace hunt-ws/integration-repass; exact
W2 remedy, test-side only, production untouched). Integration W1
re-pass LANDED (exact 3-hunk remedy; production guards byte-identical;
focused 3/3 green; full suite 3F + 8862P + 42S + 11E fully decomposed —
(a) pre-existing list_field, (b) 11 environmental, (c)+(d) 2
census-contamination by concurrent scratch, all proven not-the-repass).
Worker-0 mechanical checks pass (exact scope, digests match, 3/3
re-run green, ruff clean, no new pragma; out-of-role `git stash
create` noted harmless). Fresh Worker 2 re-verification dispatched
(ITEM_BASELINE c2bff9e4, workspace hunt-ws/integration-repass-verify;
K6/K8 + attribution audit). Census unchanged: 104 verified / 0 stale /
2 pending / 2 blocked. Integration W2 re-verdict: REVISION-NEEDED
narrow (test 3 only): the null-FK test's key-only body passes under
its own counterfactual post-fix (both paths key categoryId, node
null — wire-proven); remedy = required-message pin + failability
proof vs the invalid-id payload. Tests 1-2 verified, R1/R3/R4/R5/R6
pass, production untouched, shared tree never edited by W2
(fences re-hashed, fence-vs-ITEM = progress only; report
hunt-ws/reports/w2-integration-repass-report.txt). Fresh narrow W1
re-pass-2 dispatched (ITEM_BASELINE 4d3dfc79, workspace
hunt-ws/integration-repass-2; test 3 only). Census unchanged: 104
verified / 0 stale / 2 pending / 2 blocked. Integration W1
re-pass-2 LANDED (exact R2 remedy: message pin + docstring tighten;
f57d9a0a; all 7 guards byte-identical; failability proven both
directions; module 162P + 3 pre-attributed errors). Worker-0
mechanical checks pass (exact 1-file scope, digests match, 1/1
re-run green, all 3 gates clean, no new pragma). Fresh Worker 2
narrow re-verification dispatched (ITEM_BASELINE 7e6ff4a1, workspace
hunt-ws/integration-repass-2-verify; R2(c) only). Census unchanged:
104 verified / 0 stale / 2 pending / 2 blocked. Integration W2
narrow VERIFIED unconditional (N1-N5 all PASS, zero discrepancies:
exact hunk, pin + tighten proven from the query bytes, own 2-shape
live discrimination probe, 1/1 + 162P + 3 pre-attributed errors, all
gates clean, full audit; shared tree never edited, fences re-hashed,
fence-vs-ITEM empty; report
hunt-ws/reports/w2-integration-repass-2-report.txt). Integration item
CLOSED (Fixed Low; all 6 workspaces removed; reports + expectations
retained). Census now: 105 verified / 0 stale / 1 pending (gate) / 2
blocked. NOTHING RUNNING. ## Current status: GATE 6g BLOCKED ON RIO
DECISION (genuine maintainer block — Worker-0 stops here). DECISION
REQUEST (naming posture; recorded on mutations/sets.py + mutations/fields.py
items; full options/consequences/non-binding-read/reopen-conditions in
hunt-ws/reports/w2-5d-naming-report.txt): (A) publish degraded
`<MetaclassName>Payload` [status quo, ~:211 pin stands] or (B) reject
at definition with typed ConfigurationError [fail loud, pin +
hostile-register tests rewritten]? A Rio (B) answer re-opens both
items for a W1 revision + W2 re-verification before the gate; a Rio
(A) answer closes the dispute with zero code change and the gate runs.
Carried with the decision: allow_blank enum-to-String schema sign-off,
BaseException narrowing, guards-stay, PG/sharded cells (all recorded;
none blocks the gate per the 6e routing — only the naming posture
does). In flight now: nothing.

Deep-dive selection 2026-09-23 (Worker 0):
Resume validation: HEAD ae52bdec confirmed by `git rev-parse --short`
(no Drift line owed); census re-derived by Status-line grep — 105
verified / 0 stale / 1 pending (gate) / 2 blocked — AGREES with the
handoff exactly (105 `- Status: verified`, 2 blocked, 1 pending).
Housekeeping folded below (1_introspect.py verdict + removal;
census-contaminant identification; red-test confirmation).
Sources read: every item record + Owned changes ledger + Maintainer
review block in this file; all 54 retained hunt-ws/w2-*-expectation
files (swept for gap language — boilerplate cell rows only, no
limitation text beyond what the item records already fold in); all 30
hunt-ws/reports/ (full-read: w1/w2-integration, w1-integration-repass,
w2-integration-repass, 5d-filters/5d-naming/5d-querysets/5d-rfsets,
txn r2/r3/reverify, schema-stale r2, armcut; swept: 5e prose/layout,
drift re-proofs); surviving /tmp reports (full-read: w1/w2-authz,
w1/w2-walker-stale, w1/w2-querysets-stale, w2-sets-mixins-stale;
swept: remainder); docs/bug_hunt/temp-tests/ ABSENT (never created
this campaign); hunt-ws/floor-310/ confirmed shared testbed only;
named probe workspaces all removed per Cleanup lines. Permanent-test
spot check: integration live wire-name test present at
test_library_api.py:9145 (live tier); txn teardown pin present at
tests/test_schema.py:1280 (package tier — real ASGI cancel is
live-inexpressible, tier correct); every Fixed item carries a
W2-re-proven WS-only revert control (failability proven, not claimed);
hostile-shape tests are producer-authored by construction (unit tier
correct, wire-unreachable). New-shape verification on disk: no
ForeignObject/composite fixture anywhere in fakeshop (join_taxonomy
block stands unless the hunter finds otherwise); M2M fixtures exist
(library genres/archive_genres/alt_branches/venues); CharField
allow_blank fixture exists (library/serializers.py:284) but D2 needs
the Choice shape (dive checks); no declared-scalar+generated same-head
overlap FilterSet found in library/products (RelatedFilter+generated
same-head pairs exist — ItemFilter.category, EntryFilter.property —
merge semantics unknown, dive censuses); test_library_shapes_api.py
(9 live pins) + test_input_shapes_api.py (6 live pins) are the new
live ground truth the dives build on.
Candidates considered (14, one line each):
C1 nested read execution over real relation shapes — join_taxonomy
  Blocked :806 + nested_planner Blocked :851 + c25a34e3 shapes + 9 new
  live shape pins + connections window rows covered-by-read only.
C2 write-input parity across flavors — integration Area D split + K6
  survey blind spot + rf/inputs canonical-name divergence + forms
  M2M-null divergence + serializer D1/D2 Blocked :1096.
C3 authz on deferred paths — authz W1 deferrals cited-not-probed
  (subscribe-then-expire, cancel/timeout) + W2 accepted-on-reasons +
  AZ03 isolated-only no-related_name now live-fixtured + R8-nested
  and mid-operation-revoke never probed.
C4 sidecar merge + normalization — 5d reach correction (REFUTED
  "direct-Python only" -> overlap-wire) + B21 misbinding
  observed-only + live-overlap pin timeboxed + orders silences ruled
  by the same reasoning class that failed once.
C5 error reporting across producers — integration seam fresh in 5
  verified files (in-unit cover only) + README 5-row masking table
  never verified as a table + rejection-code pins + R2(c) key-only
  lesson + FILTER_INVALID-vs-ConfigurationError family map.
C6 transaction lifecycle 4th pass — deepest hunt of the campaign
  (3 W1 + W2.1-W2.8); remaining gaps need Rio (PG) or are
  live-inexpressible (real ASGI cancel).
C7 _DEFAULT seal census extension — confirmed-and-reported with F4;
  flip is a recorded Rio decision (querysets Stale note).
C8 subscription cost charging — document charging deep (2 fixes +
  exact-count pins); per-event subscription charging never examined;
  O1 maintainer-decision, O2/O3 robustness.
C9 utils/inputs D1-D8 folded verdict — W2 /tmp report lost, verdict
  folded from handoff + expectation + probes; robustness class
  under 5b (no fixes possible by standing rule).
C10 construction/lifecycle seam — schema 3 cycles + finalizer O1 +
  relay O1-b/c closed + registry A7 closed; all residual leads
  robustness-closed.
C11 TestClient instrument — 27+19 probes with wrapper-vs-raw
  agreement proofs; instrument risk retired by agreement method.
C12 session-auth races — 23+9 + live 46; IntegrityError race +
  post_save-boom atomicity covered; expiry-during-subscription open.
C13 naming posture items — task-excluded (blocked, Rio decides).
C14 masking seams alone — error_policy 44+19, ext 34+8+42+40,
  debug 48+60; deep, producer-isolated.
Chosen 5 (scored a=admitted gaps, b=newly-unblockable live rows,
c=proven-recurring class, d=thin/unit-only close, e=revision heat):
Dive 1 (C1): a=yes (3 live blocks + read-only window rows), b=yes
  (shapes landed), c=yes (visibility/fetch proved cross-shape
  sensitive), d=yes (unit-tier defect pins), e=medium (2 stale
  re-passes). Highest b-score of any candidate.
Dive 2 (C2): a=yes (K6 blind spot = method failure), b=yes (D2
  shape to check), c=yes (flavor split PROVEN this campaign),
  d=no, e=high (2 test-side revisions). Only candidate that
  re-derives with a different method than the one that failed.
Dive 3 (C3): a=yes (reason-only deferrals), b=yes (no-related_name
  live fixtures), c=yes (authz recurs every campaign), d=partial
  (isolated-only shapes), e=low (clean verify — which is WHY it
  needs the deeper look). HIGH-RISK (authorization): two W1 hunters.
Dive 4 (C4): a=yes (residual link + observed-only B21), b=maybe
  (overlap census decides), c=yes (reach reasoning failed once),
  d=no, e=high (C1 revision + 5d challenge). Sharpest single lead
  (B21 wire-reachable wrong rows if it stands).
Dive 5 (C5): a=yes (table never verified as a table; seam fresh),
  b=yes (every row wire-provable today), c=yes (envelope split
  proven; R2(c) counterfactual lesson), d=no, e=high (integration
  revisions). Doubles as the stale re-cover of 5 verified files.
Closest 5 not chosen, why not: C8 — sharpest rejected lead
  (per-event subscription charging unexamined) but a one-question
  dive on top of already-deep document charging; re-propose if a
  dive closes early. C6 — honest remainder is unrunnable (PG needs
  Rio; live cancel inexpressible); a 4th pass without new cells has
  the lowest expected yield. C12 — expiry-during-subscription folds
  into Dive 3 (authz-owned); the residue (login/logout races) is
  thinner than every chosen dive. C11 — agreement probes retired
  the instrument risk; no admitted gap names it. C9 — an evidence
  gap (lost report), not a depth gap, and 5b forbids the only fixes
  that surface could yield; re-verification, not a hunt.
Housekeeping: 1_introspect.py verdict HUNT-CREATED — root file birth
  Sep 23 01:14:54 EDT (0 bytes, never written) correlates 1 minute
  before the integration W1's /tmp/w1_introspect.py (518 bytes,
  01:15, the BookInput probe from its ledger :687); the "introspect"
  stem appears in no other worker log/report/record; the integration
  W1 session was live in that minute. A path slip, misclassified as
  concurrent by three readers without the birth-time correlation.
  Removed by explicit path per task authorization (untracked, no git
  entry; nothing references its bytes). Sweep-census still names
  hunt-ws/floor-310/**. Census contaminants for the gate (confirmed
  on disk just now, 3 failed): version-census
  (test_package_defines_exactly_one_version_declaration — skips no
  hunt-ws/) fails on hunt-ws/floor-310's package copy (+ any live
  workspace copy); sweep-census
  (test_the_sweep_corpus_covers_every_committable_python_file) fails
  on hunt-ws/floor-310/**/*.py (1_introspect.py now removed).
  Gate tension recorded: floor-310 is hunt scratch HUNT.md closeout
  deletes but the record keeps ("floor-310 kept") — the gate runs
  before closeout deletion, so Rio triages (remove floor-310 pre-gate
  or accept the 2 census reds with cause). Red test STILL RED on
  disk post-armcut: test_djangolistfield_unregistered_guard_survives_
  a_hostile_metaclass_name fails at types/base.py:699
  (ConfigurationError, armcut frame shift :708->:699 confirmed).
Census now: 105 verified / 0 stale / 6 pending (5 deep dives + gate)
  / 2 blocked. In flight now: deep-dive selection recorded; Deep
  dive 1 dispatch next.

Fold 2026-09-23 (Worker 0): Deep dive 1 W1 dispatched (ITEM_BASELINE
71d66aba, workspace hunt-ws/deep-1-read-shapes-r1; brief carries the
item Prompt + rule-35 legs + robustness-only-no-fix + no-new-guards +
live-first + no-new-model + hunt-ws/reports/ rules). Dives run
sequentially (shared-tree fences overlap across dives; heavy suites
one at a time per the disk rule). Census unchanged: 105 verified /
0 stale / 6 pending / 2 blocked. In flight now: deep dive 1 W1
hunt (only).

Fold 2026-09-23 (Worker 0): Deep dive 1 VERIFIED (No bugs; two-phase
W2: 16/19 expectation rows confirmed, 1 contradicted-admitted, 1
split-adjudicated; 60/60 replay + 33 independent attacks; censuses
recounted; floor re-executed; zero shared edits). Exact fixtures for
Rio: composite-PK+ForeignObject nested connection (P1), non-pk-ordered
M2M nested target (P2), sequence-resolver connection field (P3, with
the holder-HTTP tier split riding as a judged lead). Workspaces
removed, expectation + 2 reports retained, floor-310 proven untouched.
Census: 106 verified / 0 stale / 5 pending (4 deep dives + gate) / 2
blocked. In flight now: deep dive 2 W1 hunt (only; ITEM_BASELINE
b3e98960, workspace hunt-ws/deep-2-flavor-parity-r1).

Fold 2026-09-23 (Worker 0): Deep dive 2 VERIFIED (No bugs; two-phase
W2: 7/7 splits re-derived with validator-inherent/documented rationales,
100/100 replay + 55 own probes, censuses recounted, floor re-executed,
zero shared edits). D1/D2 live rows honestly still-blocked with exact
fixtures; ROB1 record-only; L2 masked-scalar failure rides to Dive 5 as
a named producer. Workspaces + floor marker removed, expectation + 2
reports retained. Census: 107 verified / 0 stale / 4 pending (3 deep
dives + gate) / 2 blocked. In flight now: deep dive 3 W1-A hunt
(HIGH-RISK protocol: sequential blinded hunters — A hunts+implements
first, B hunts the post-A tree blinded to A's diagnosis with A's hunks
in-scope-as-native, reports exchanged read-only after both report, then
one W2 over the union; ITEM_BASELINE 9cb7bbb9, workspace
hunt-ws/deep-3-authz-a-r1).

Fold 2026-09-23 (Worker 0): Deep dive 3 is BLOCKED (sensitive-findings
rule). W1-B confirmed one HIGH client-reachable visibility defect
(abstract: consumer-Prefetch optimizer hints over hiding targets;
get_queryset traversal survival + optimizer-trust rows; location
optimizer/walker.py::_apply_hint consumer-prefetch branch; documented
Meta.optimizer_hints + ordinary anon nested query). Evidence sealed in
hunt-ws/deep-3-authz-b-r1/d3b/test_d3b_hint.py (5 nodes; never executed
outside B's session; B's WS retained as the evidence seat until Rio
answers — no cleanup). W1-A (contract lens) Fixed Low in workspace
(missing check_deadline on nested single-object resolvers, 6 lines +
4 live tests) but STOPped on landing (insertion regions DRY-owned;
STOP verified correct; handoff preserved as
hunt-ws/reports/d3a1-resolvers-fix.patch 69c965a1 +
hunt-ws/reports/d3a1-test_relation_deadline_api.py f8ebf5d4).
Exchange complete: A concurs on B's abstract rows + admits the branch
gap; B changed its CR10 reading and concurs on A's Low (defect stands
on both hunters' executions; W2 still adjudicates independently).
Blinding held (cite-audit zero). Fenced W2 dispatched over the
verifiable union (A's fix+battery, B's 60 non-sensitive probes,
B-abstract plausibility; sealed evidence never opened; verdict
excludes the sealed defect). Census: 107 verified / 0 stale / 3
pending (dives 4, 5 + gate) / 3 blocked (2 naming + dive 3).
DECISION REQUEST (Rio — abstract; no exploit-shaped material in this
file): (1) Dive-3 HIGH sealed defect — decide disclosure/handling
(SECURITY.md maintainer path); evidence seat named above; the item
stays blocked until you answer. (2) Dive-3 Low fix landing — the
6-line + 4-test handoff applies only after the DRY one-sync-boundary
hunks in types/resolvers.py settle; decide landing order (hold for
DRY resume vs land-first with DRY rebase). (2) UPDATE 2026-09-23:
MOOT — the fix + battery landed complete in the shared tree by an
external hand mid-dive-4 (production bytes 22f10c3f identical to the
handoff; battery with a 1-line docstring polish; see the types/
resolvers.py stale note for exact diffs + mtimes); types/resolvers.py
marked stale with a bounded re-verify queued. (3) L3 fixture — a hiding
get_queryset on VenueBadgeType or VenueSponsorType needs an
example-model change; decide whether to add it. In flight now: dive
3 fenced W2 phase 1 (only).

Fold 2026-09-23 (Worker 0): Deep dive 3 verification round COMPLETE,
item stays BLOCKED. W2 VERIFIED the verifiable union (A-fix byte-exact
via handoff, failability re-proved, regressions clean, CR10 adjudicated
for universal from the previously-unread Decision 9, STOP re-verified
with DRY fingerprints byte-exact, B-60 replayed via proven hint-free
exclusion copy, B-abstract judged COHERENT from the abstract alone,
floor re-executed with bed-untouched inventory proof, leads routed,
hygiene airtight) and explicitly excluded the sealed HIGH (neither
confirmed nor denied). Truncated delivery (line 264) completed by
bounded followup (118 lines, boundary verified). No cleanup until Rio
answers (evidence seat + handoff + all three dive-3 workspaces
retained; hunt-ws/ at 0.92 GB, boot volume 15 GB free — above the
6 GB line). Census unchanged: 107 verified / 0 stale / 3 pending
(dives 4, 5 + gate) / 3 blocked (2 naming + dive 3). The dive-3
DECISION REQUEST stands open. In flight now: deep dive 4 W1 hunt
(only; ITEM_BASELINE ffa05511, workspace
hunt-ws/deep-4-sidecar-merge-r1).

Fold 2026-09-23 (Worker 0): Deep dive 4 VERIFIED (Fixed 1 Low B21,
landed: +14/-1 reroute + 5 tests; two-phase W2 with a fresh r2
expectation after the r1 brief-defect invalidation; failability
re-proved with exact red IDs; census recounted; silences re-derived
live; gates + R1 watch clean; verdict verified, no challenges).
filters/sets.py marked STALE (bounded re-verify queued next).
MID-TASK CONCURRENT DRIFT recalculated (two events, both external,
both recorded, never reverted): (E1, 15:09) types/base.py sentinel
reorder (+11/-11 region move; committed pinning test) — types/base.py
marked STALE with a narrowed note; naming-posture items untouched.
(E2, 15:44-15:46) the dive-3 Low landing COMPLETE by an external hand
(battery 15:44 with a 1-line docstring polish, production 15:45
byte-identical 22f10c3f to the handoff, README index row + link def
15:46) — dive-3 decision-request (2) MOOT; types/resolvers.py marked
STALE with a narrowed note. Attribution: unattributable from tree
evidence (no record drift in docs/dry/ or elsewhere; my workers'
fences + diffs prove neither event is hunt work). The dive-4 verdict
stands for its bytes (W2 WS predates E2; E1/E2 outside the dive fence
and behaviorally orthogonal; the stale re-verifies run on current
bytes and cover any interaction). Census: 105 verified / 3 stale
(filters/sets, types/resolvers, types/base) / 2 pending (dive 5 +
gate) / 3 blocked (2 naming + dive 3). In flight now: filters/sets
bounded stale re-verify (only; ITEM_BASELINE a568a13e, workspace
hunt-ws/filters-sets-deep4-verify).

Fold 2026-09-23 (Worker 0): filters/sets STALE RESOLVED (bounded W2
VERIFIED, no challenges: 5d rows re-proved both eras, E8 flip exact
3/28, failability re-proved, census recounted, corollary + R1/R2/R3 +
floor + inputs-AST all clean). Workspace removed, expectation +
report retained. Census: 106 verified / 2 stale (types/resolvers,
types/base) / 2 pending (dive 5 + gate) / 3 blocked. In flight now:
types/resolvers bounded stale re-verify (only; ITEM_BASELINE
c3494d3a, workspace hunt-ws/types-resolvers-deep3-verify).

Fold 2026-09-23 (Worker 0): types/resolvers STALE RESOLVED (bounded
W2 VERIFIED, no challenges: landed == handoff byte-exact, battery
4/4 + docstring delta AST-identical, R1-R8 + 11 interaction pins,
failability re-proved, DRY interaction clean, floor substrate 4/4,
diff inventory exact, gates clean). Workspace removed, expectation +
report retained. Census: 107 verified / 1 stale (types/base) / 2
pending (dive 5 + gate) / 3 blocked. In flight now: types/base
bounded stale re-verify (only; ITEM_BASELINE f6ac7b0a, workspace
hunt-ws/types-base-reorder-verify).

Fold 2026-09-23 (Worker 0): types/base STALE RESOLVED (bounded W2
VERIFIED with one NON-BLOCKING challenge C1: pure-move proven,
15/15 pins both orders with delta exactly D1-D6, 233/233 both
orders, pinning green both orders, floor 10/10, gates clean; C1 =
the known-red guard test flipped red->GREEN via D3, judged a
non-blocking robustness row with no coherent revision — hostile-only,
satisfies the test's own written expectation). Worker 0 CONFIRMED
the flip on disk (focused run: 1 passed). Naming-posture items never
touched, never re-opened. Stale queue EMPTY (all three resolved).
Census: 108 verified / 0 stale / 2 pending (dive 5 + gate) / 3
blocked (2 naming + dive 3). In flight now: deep dive 5 W1 hunt
(only; ITEM_BASELINE 9abcbc1f, workspace
hunt-ws/deep-5-error-reporting-r1).

CLOSING FOLD 2026-09-23 (Worker 0 — deep-dive round complete, gate still blocked):
Per deep dive (result / strongest new probe / cells now covered vs still unverified):
- Dive 1 nested reads: VERIFIED No bugs. Strongest: W2's TRUE Decision-5 deferred-FK pair (W1's probe misattributed its own green run — elision firing, not fallback; both true paths correct) + R7 revert proving W1's 9 cursor probes non-discriminating (permanent before:"" pin load-bearing). Covered: live falsifier per reachable shape (text-pk/O2O-pk/to_field/MTI/proxy/no-related_name/cycle/self-M2M), window-vs-fallback agreement, 3 promotions honestly still-blocked with exact fixtures (P3 with the holder-HTTP tier split riding as a judged lead). Still unverified: PG-lateral execution, sharded (need Rio); composite-ForeignObject + M2M-ordered + sequence-resolver fixtures (blocked lines, no new model added).
- Dive 2 flavor parity: VERIFIED No bugs. Strongest: W2's S2 stale-value differential (W1-uncovered: model/serializer accept, form rejects naming the STALE field — documented sharp edge) + D11 omit-vs-null file matrix + D5 Django-spelling coercion battery (K6 lesson). Covered: 7 executed splits all validator-inherent/documented, re-derived by W2 against installed validators; D1/D2 honestly still-blocked (zero ListFields incl. prose audit; 2 ChoiceFields neither allow_blank). Still unverified: PG/sharded (need Rio); ListField + Choice-allow_blank live fixtures (blocked lines).
- Dive 3 authz deferred paths: BLOCKED (sensitive-findings rule). W1-B confirmed one HIGH client-reachable visibility defect (abstract: consumer-Prefetch optimizer hints over hiding targets; traversal-survival + optimizer-trust rows; walker.py::_apply_hint consumer-prefetch branch) — evidence sealed, never executed outside B's session. W1-A Fixed Low in workspace (missing check_deadline on nested single resolvers, 6 lines + 4 live tests) — STOPped on DRY-owned landing lines (STOP verified correct), handoff preserved, then LANDED COMPLETE by an external hand mid-dive-4 (E2: production byte-identical 22f10c3f, battery + 1-line docstring polish, README index row) and item-re-verified. Strongest: B's 4 leak demonstrations (sealed) + A's 7-query pre-fix / rejection post-fix differential + the CR10 universal adjudication from Decision 9 (W2, independent of the hunters' exchange concurrence). Covered: subscribe-then-expire behaviorally (S1/S3 + B-sub), deadline-ahead-of-DB on every read path (live), no-related_name live, R8 nested re-scope, mid-operation revoke pinned per-resolver, nodes() mixed batches. Still unverified: PG lock-execution, sharded (need Rio); L3 hiding-hook fixture (blocked line).
- Dive 4 sidecar merge: VERIFIED Fixed 1 Low + LANDED (B21 single-lookup overlap misbinding — silent wrong rows; +14/-1 reroute + 5 tests; filters/sets item re-verified after). Strongest: the live wire-shape overlap instance proof (B19 construction + W2's both-eras recount 64/579/[]) + S-F4 contracted-reachable adjudication (dict-{} unreachable proven, dataclass-{} reachable-but-contracted) + permission-first ordering pin (previously unpinned). Covered: 5d residual link closed (in-process coercion proof), 5 silences re-derived with live second instruments, gate matrix complete, R1/R2/R3 no-reopen, orders twin clean. Still unverified: PG/sharded-by-construction claims (grep-proven per claim, formally unverified); live-overlap pin blocked (exact minimal fixture, no new model needed).
- Dive 5 error reporting: VERIFIED No bugs + 6 tests-only pins (no ledger rows — authz/pagination precedent). Strongest: W2's N=12 uniqueness battery (12 distinct ids + 12 matched logs) + 5-cause login byte-identity + hook 8-halves ordering witness + DEBUG-flip-mid-stream proof. Covered: the error table as a table (all 5 rows live), ride-in placed as C4 conformance (independently derived + re-proven on 8 legs), seam exactness all flavors + auth, every rejection code live, transport + per-event masking live. Still unverified: PG/sharded (formally, judged inapplicable per claim family); UNVALIDATABLE live row closed as impossible-by-construction (finalizer audit — NOT a Rio line); async nested-body row fixture-unexercisable on this interpreter (5 defs / 6 items, sync twins erratum-corrected); 25 key-only sites = test-hardening card.
Updated counts: 109 verified / 0 stale / 1 pending (the final gate) / 3 blocked (2 naming + dive 3). Ledger: 51 rows (10 defect / 38 robustness / 2 lint / 1 stale-row).
Open DECISION REQUESTS (all in this file): (i) naming posture (A)/(B) — the gate blocker, still unanswered, do not run the gate; (ii) dive-3 HIGH sealed defect disclosure/handling (SECURITY.md path; evidence seat hunt-ws/deep-3-authz-b-r1/d3b/test_d3b_hint.py retained, never cleaned); (iii) dive-3 L3 hiding-hook fixture (example-model change); (iv) dive-1 P3 holder-HTTP tier split (judged lead: holder-schema-over-HTTP promotion constructible today vs project-schema block); (v) B21 corollary + filters/orders harmonization (new-card candidates); (vi) dive-3 CR10 dash-list follow-up (resource_policy.py gains the seam — A's fence excluded it); (vii) guard-comment universal-vs-Meta-only narrowing (judged prose lead).
Carried (with record lines, per the round brief): allow_blank enum->String schema sign-off (record :2923-2932, 5d review routing — D2 Choice shape still fixtureless per Dive 2 B2); BaseException narrowing (record :2933-2937 — maintainer deletions stand; no new arms added this round); guards-stay (record :2938-2943 — standing 5b held: every hostile-only reproducer this round recorded as robustness, zero new guards); PG/sharded authorization (authz item + dive-3 cells — still unverified without Rio's word); the red naming-guard test (record :2197-2204 + TB C1) — NO LONGER RED: flipped green via the E1 reorder's D3 path (bounded W2-verified mechanism + counterfactual reproducing the :699 signature; Worker-0 focused run confirms 1 passed). The gate triage for it is now: green, mechanism understood, robustness-row judgment recorded.
Digest-vs-record sweep (this round): PASS, zero unexplained. Method: (a) 6/6 record pins match current bytes (B21 fix, dive-5 pins, landed D-3A-1, E1 reorder); handoff pins + landed bytes unchanged; all 9 expectation seals intact (dive 1 b4bdab78, dive 2 b7d6ad9c, dive 3 cb481f33, dive 4 r2 018b6309 + invalidated r1, dive 5 c2ae6f05, 3 stale pins); (b) round drift vs the dive-1 baseline is EXACTLY 7 tracked files, all explained (dive-4 fix 2, dive-5 pins 2, E1 1, E2 2) + 4 untracked, all explained (historical preserved, E2 battery, honest_*.txt pair); tracked count reconciled 99->101 by the dive-5 pins; (c) per-dive mechanical digests re-verified 60+ file digests this round (every W1 pin set matched); the integration K3 full-ledger verification (12h old) stands for untouched files. No new stale items (queue empty).
Housekeeping closed: 1_introspect.py removed as hunt-created (birth-time correlation, selection block); census contaminants recorded (version-census + sweep-census fail on hunt-ws/floor-310/** + retained dive-3 workspaces — gate triage: remove scratch pre-gate or accept with cause; the red-test leg of that triage is now green per C1); honest_*.txt pair left for closeout cleanup; /tmp/d5_probe_shape.py + /tmp/w2-floor-marker left in OS temp (volatile, ignored); floor-310 bed drift recorded (5.2.17 + 0.327.7 vs BUILD.md 5.2.16 + 0.316.0 — direction holds, read-only reuse held every dive).
Process lessons recorded: (1) W2 briefs must quote scope in-brief (the stop-line is unimplementable when Iterations precede scope — cost one phase-1 redo on dive 4); (2) W1 briefs must name check_trailing_commas.py --check alongside ruff (dive-5 needed a bounded gate revision without it); (3) census greps must use the indented-item pattern (my own selection prose contains a backticked `- Status: verified` that inflates naive grep -c by one — true census by awk: 109/0/1/3).
Mid-task concurrent drift log (all external, all recorded, never reverted): E1 types/base.py reorder 15:09 (item re-verified, C1 non-blocking); E2 dive-3 Low landing 15:44-15:46 (production + battery + README index; item re-verified; decision-request (2) MOOT). Attribution unattributable from tree evidence either event (no record drift; fences + diffs prove neither is hunt work).
In flight now: NOTHING. The round is complete. The final gate stays BLOCKED until Rio answers the naming posture — do not run it.

