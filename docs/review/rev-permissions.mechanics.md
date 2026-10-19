# Review · Mechanics: `django_strawberry_framework/permissions.py`

Status: no-findings
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=623c43216c5c50961b3dc0f5448ae6d21926ece1

## Trace

Read in dispatch order: AGENTS.md, START.md, docs/review/REVIEW.md,
docs/review/worker-1.md, docs/review/review-0_0_15.md (ledger: no
`## Owned changes` rows for this item yet; item `reviewing`),
docs/review/rev-permissions.md (skeleton, `Status: reviewing`). Sibling axis
records `rev-permissions.performance.md` / `.mechanics.md` / `.comments.md`:
absent at open and at close (siblings run concurrently; nothing to read).
Then the whole live target (740 lines).

The target is dirty with concurrent work (`git status` shows
`M django_strawberry_framework/permissions.py`, matching the plan's item
note). Fingerprinted what was read: `ef66f8b9` at open and at close, and
`git diff ITEM_BASELINE -- django_strawberry_framework/permissions.py` is
empty, so the file did not drift mid-pass.

Traced out of the target: production callers
(`examples/fakeshop/apps/products/schema.py` four hooks,
`examples/fakeshop/apps/library/schema.py` five hooks incl. one
`fields=`-scoped), package-root exports
(`django_strawberry_framework/__init__.py`, both symbols imported by name
and pinned in `tests/base/test_init.py`), the seal/boundary owner
(`django_strawberry_framework/utils/querysets.py`:
`::apply_type_visibility_sync`, `::_prepared_visibility_source`,
`::_normalized_visibility_result`, `::run_in_one_sync_boundary`,
`::reject_async_in_sync_context`, `::base_queryset`, `::model_for`,
`::SyncMisuseError`), the registry resolve
(`django_strawberry_framework/registry.py::TypeRegistry.get`), sibling
authorization seams
(`django_strawberry_framework/utils/permissions.py`,
`django_strawberry_framework/mutations/permissions.py`), contract sources
(spec-034 incl. its rationale, the GLOSSARY `apply_cascade_permissions`
anchor, module/owner docstrings), and oracles
(`tests/test_permissions.py`, 57 tests; live
`examples/fakeshop/test_query/test_products_visibility_api.py` and the
`VisibleBranch` proxy twin in `test_library_inheritance_api.py`).
`review_inspect.py` orientation under
`docs/review/temp-tests/permissions/mechanics/inspect/`. One workspace probe
(run `review-20260929T063755-300c88`, default cell): 93 models / 703
`get_fields()` members, zero SQL asserted in-probe. Sharded/pg cells:
inapplicable by construction for the probe (it opens no database and
asserts zero queries, so no cell can vary it); no finding carries a
cell-bound Proof.

Fingerprints (`git hash-object`): target `ef66f8b9ce5c17813558d10150f945d0c9420bef`;
`utils/querysets.py` `8fc556d582b313e4aed7cddaa15f9a8480d88a46`;
`utils/permissions.py` `1c9cfd398e6096e03bda82ba93dfd66a6d2fb890`;
`mutations/permissions.py` `55e5edf80c601f373c1802d34fc4e497919d17e7`;
`registry.py` `492654d219d1061fef33f186d962dc5369b71ebe`;
`__init__.py` `0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`tests/test_permissions.py` `c22af72892e3430ea51d5e4bef0112871445c604`;
`docs/GLOSSARY.md` `3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`;
`docs/SPECS/spec-034-permissions-0_0_10.md`
`788245cbf8ee394a661fb4c23ef8f818046a0bfc`; `KANBAN.md`
`39bb608e8f7122d7e2e133fdd6b3e7d9ccf46c7a`;
`apps/library/models.py` `b980e82c5e5a73690a18befd1eb5c7db1cf05691`;
`apps/library/schema.py` `9682db07a0054937c80900d20519265b87121606`;
`apps/products/schema.py` `04a5afe3dddff9279660ae1370924e03857d57e7`.

## Findings

### High

None.

### Medium

None.

### Low

None.

### Looks-for discharge (no finding)

- Rule enforced at caller instead of owner: none. The re-projection
  battery
  (`django_strawberry_framework/permissions.py::_validated_target_subquery`)
  lives in the cascade because only the
  cascade calls `.values(...)` on a hook return; shape / table / alias /
  slice / combined stay in the shared boundary, reached with cascade
  renderers. The values-root admission is coherent per boundary: the
  cascade admits `.values()` because its own downstream re-projects it
  (pinned by
  `tests/test_permissions.py::test_values_root_is_supported_input`);
  outer surfaces reject a values
  hook return under their own model-rows policy, which is the correct
  fail-closed for a boundary that cannot normalize one.
- Policy in an adapter, mechanism in a policy layer: none. Per-edge hook
  invocation is delegated whole to `apply_type_visibility_sync` (spec-034
  Decision 10, one sync-misuse site); the async twin delegates the thread
  hop to `run_in_one_sync_boundary` (spec-040 D17 neutral owner). No
  routing re-decided here.
- Contract sources vs body: none for the code. Module docstring, spec-034
  (Decisions 5/8/9/10), and oracles agree with the body on every bullet
  checked (identity-hook composition incl. the FK-to-proxy
  `VisibleBranch` mechanism, MTI parent links, preflight-before-hooks,
  nullable-only disjunct, `fields=` tri-state, alias pinning, cycle
  fail-closed with the `fields=[]` escape). The one prose gap (GLOSSARY
  omits the `distinct(...)` rejection) is R15: the body is correct, the
  fix is outside the fence.
- Branch no real path reaches: the `_defect_message` fallback arms are
  deliberate tripwires (an unrendered seal code must mislabel loudly),
  not dead code; both renderers' arm sets match the reachable codes of
  the cascade seal policy exactly (no `projection` arm, policy never
  raises it). The two genuinely dead shapes are R1/R2.
- Mode flag standing in for a named adapter: none. The `fields`
  tri-state (`None` = all, `[]` = none, names = subset) is documented
  sentinel semantics pinned by spec-034, not a mode flag; nothing
  dispatches on it adapter-style.
- State owned in two places: none. One `_TraversalState`
  (`alias`/`active`/`path` are distinct data: membership vs render, and
  `path` carries edge names `active` cannot derive). `_edge_plan` is
  pure model metadata, registry-independent, so no `registry.clear()`
  coupling is owed; `names_to_walk` is per-call derived.
- Dependency pointing the wrong way: none. Edges run
  `permissions.py` -> `exceptions`, `registry`, `utils.truth`,
  `utils.querysets` (the neutral substrate direction its docstring
  establishes); no reverse import exists (grep over `registry.py` and
  `utils/querysets.py` finds prose mentions only), no `TYPE_CHECKING`
  block. The cross-module `_`-private imports are established house
  convention, explicitly closed as not-a-defect on TODO-ALPHA-053
  (line 310 bullet, 76 statements tree-wide): not re-raised.
- `django.conf.settings` read at import: none. The import block touches
  no settings; module level defines only the `ContextVar`, the plan
  cache, and constants.
- Sync/async twins drifted: none. `aapply_cascade_permissions` is a
  one-call wrapper over the single sync walk (argument order verified);
  no second walk exists to drift. Both variants raising
  `SyncMisuseError` on an async target hook is pinned by
  `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` and
  `test_aapply_async_target_hook_still_raises`.

## Rejected

- R1: `django_strawberry_framework/permissions.py::_cascadable_edges` +
  `::_cascadable_edge_names` are production-dead
  (`_cascadable_edges`: exactly one reader, its sibling;
  `_cascadable_edge_names`: zero production readers -- one import + two
  call sites, `tests/test_permissions.py:96,472,612`; every production
  path reads `_edge_plan(model)` directly). Independently re-derived;
  the KANBAN count ("three call sites") has drifted by one. Rejected:
  owned by TODO-ALPHA-053-0.0.15 Scope ("Delete the dead cascade edge
  helpers", line 315 bullet) with paths undecided including (c) keep as
  documented test seams; deleting here preempts the card. Trigger: the
  card closes keep-path or deletes.
- R2: `::_is_unsupported_forward_edge` reads
  `getattr(field, "is_relation", False)` while the two sibling
  predicates on the same line read attributes directly. Probe
  `review-20260929T063755-300c88` proves the default unreachable (703
  members, `default_fired=[]`, zero SQL). Rejected: owned by
  TODO-ALPHA-053-0.0.15 Scope (line 314 bullet) with paths (a) direct
  read vs (b) keep + docstring undecided; hardening, not a bug fix.
  Trigger: a `get_fields()` member without `is_relation` exists (then
  the whole predicate needs rework anyway, since `many_to_many` /
  `one_to_many` are direct reads).
- R3: the module defines no `__all__`. Rejected: no contract promises
  star-import behavior; root imports by name and pins them in
  `tests/base/test_init.py`; several top-level siblings
  (`connection.py`, `keyset.py`, `schema.py`, `consumers.py`, `conf.py`,
  `registry.py`) are equally bare. Trigger: a spec pins module
  `__all__` coverage.
- R4 (duplication challenge -- renderer prose): posit rewording the
  `untrusted` seal explanation; authoritative wordings are many (root
  renderer, edge renderer, every surface default). Rejected: separate
  reasons to change by design (path-rich edge attribution vs root
  attribution vs generic); what is shared is the dispatch and
  exhaustiveness (`_defect_message`), never the wording, per its
  docstring. Trigger: two sites required to render byte-identical text.
- R5 (duplication challenge -- edge taxonomy): posit a new Django
  relation kind must classify; `_is_cascadable_edge` vs
  `django_strawberry_framework/utils/relations.py::relation_kind`.
  Rejected: different rules (a
  single-column-composability predicate with the `column` guard vs a
  kind taxonomy for many consumers); one definition of "cascadable
  edge", two internal callers, no second spelling (grep). Trigger: a
  second cascadable-edge spelling appears.
- R6 (duplication challenge -- async recourses): posit rewording the
  async-hook recourse across `_ASYNC_RECOURSE`,
  `sync_pipeline_recourse`, `_GATE_ASYNC_RECOURSE`,
  `_PERMISSION_ASYNC_RECOURSE`. Rejected: genuinely different wordings
  (the cascade has no async walk, so its recourse names the two working
  options and pointedly not the twin); the template docstring declines
  these two. Trigger: the recourses converge to one sentence.
- R7 (duplication challenge -- `SyncMisuseError` re-export chain
  through `types/relay.py`, this module, and the root): re-exports are
  projections, listed not counted; one authoritative definition in
  `utils/querysets.py`. Trigger: a second definition appears.
- R8 (duplication challenge -- `group_by` / `distinct_fields` reads):
  the cascade's rejection vs the `lateral_fetch.py` /
  `single_parent_fetch.py` `group_by is not None` classifiers.
  Rejected: different rules (a visibility fail-closed vs a
  fetch-strategy classifier). Trigger: a second visibility
  re-projection battery appears.
- R9 (cycle guard vs filter/order depth caps): different contracts
  (fail-closed cycle detection with a path vs an input-depth budget);
  the mechanisms must not converge. Trigger: a contract unifies them.
- R10 (sibling-guard parity -- re-projection battery absent on
  list/connection surfaces): contract difference, not a missing guard;
  only the cascade re-projects via `.values()`. Trigger: a surface
  gains `.values()` re-projection -- it then owes the battery.
- R11 (sibling-guard parity -- the async twin cannot await an async
  target hook while `apply_type_visibility_async` awaits natively):
  documented spec-034 Decision 10 posture ("dead-end", recourses
  documented, async-native walk additive if a real consumer hits the
  wall). Trigger: a real consumer needs async cascade targets (carded
  with the filter child-branch surface, which moves with it).
- R12 (sibling-guard parity -- the cascade omits the `model=` captured
  seam, so source and result seals each read `model_for(target_type)`):
  consistent with eight other type-keyed `apply_type_visibility_sync`
  callers (only `list_field.py` passes `model=`, because it holds the
  definition at construction); the seam is perf/convenience, and
  mid-request definition mutation is unsupported monkeypatching.
  Trigger: a supported shape mutates type definitions mid-request.
- R13 (values root admitted here, rejected by outer surfaces): coherent
  boundaries, each enforcing what it normalizes (this item's
  Looks-for discharge states the mechanism). Trigger: a
  values-rooted cascade output accepted somewhere it cannot compose.
- R14 (`model_for` raises a raw `AttributeError` on an unregistered
  `cls`): identical on every visibility surface; callers responsible
  per the `model_for` docstring. Trigger: a contract promises a typed
  error for an unregistered cascade root.
- R15 (contract-vs-body -- GLOSSARY `apply_cascade_permissions` "Hook
  returns are validated" omits the field-specific `distinct(...)`
  rejection, which spec-034 promises is "documented in the GLOSSARY
  body" and which the module docstring and
  `test_hook_return_rejections_fail_closed[distinct]` pin): rejected
  as a Mechanics defect -- the body is correct on all three remaining
  contract sources. The prose gap routes to the plan's `## Decisions`
  (fix = `GlossaryTerm.body` ORM edit + `build_glossary_md.py` render,
  outside the item fence; precedent: the `error_policy.py` Mechanics
  glossary routing this run). Trigger: none -- routed, not closed.

Handoff: The module is in good shape: delegation boundaries are clean,
every looks-for entry discharged, both dead-code shapes independently
confirmed but owned by TODO-ALPHA-053-0.0.15 with undecided paths (my
reader count for `::_cascadable_edge_names` is 2 call sites, not the
card's 3 -- its next reader must re-derive). Only thread for Worker-0:
the R15 `Routed:` glossary lead for `## Decisions`. No `check_citations
--cited-by` run: no recommendation moves or renames a symbol. Verifier
note: there are no Proof lines (no findings); the single run id above
backs a rejection. Sibling records never appeared during this pass; if
the Comments sibling grades the module docstring's historical
asides ("The previous ... contract ..."), that is their scope, not a
gap in this record.

## Verify mechanics

No-findings-stands confirmation: the pass-1 change introduces no
Mechanics defect. Read whole, in order: AGENTS.md, START.md,
docs/review/REVIEW.md, docs/review/worker-2.md, the plan incl.
`## Owned changes` (two permissions.py rows: target Performance +
Comments, own tests Performance + Comments), all four records with
every Handoff, the pass diff whole (13 target hunks + 12 own-test
hunks), the whole live target (745 lines). Step-1 gate holds:
`git diff ITEM_BASELINE -- <both paths>` is byte-equal to
`docs/review/temp-tests/permissions/diff/pass-1.diff`
(`diff` exit 0, `ITEM_DIFF_EQUALS_PASS1`). My record carries no
Proof lines and neither sibling carries a `## Cross-axis (for
mechanics)`, so no Proof run was owed.

Disturbance check (F1/F2 through the Mechanics looks-for):

- Delegation intact. `_walk` still invokes each target hook
  through `apply_type_visibility_sync` (spec-034 Decision 10, the
  one sync-misuse site) and still re-projects each return through
  `_validated_target_subquery` before composition; hook order,
  per-edge `registry.get` skip gate, nullable `__isnull`
  disjunct, and the edge path-frame install/reset are untouched
  context lines. The async twin still wraps the single sync
  walk in one `run_in_one_sync_boundary` hop
  (`django_strawberry_framework/permissions.py:739-745`,
  argument order `cls, queryset, info, fields` verified); exactly
  one `def _walk` exists, so no second walk to drift.
- Fail-closed preserved. F1 only defers `.filter` composition to
  a guarded post-loop call: an edge whose hook raises still
  raises before any composition, and the old partial queryset
  was likewise discarded on exception, so observable behavior is
  identical; the `if conditions` guard keeps the 0-edge path
  filter-free (no bare `.filter()` clone). F2 only delays
  `truth.name` / edge-label evaluation from factory time to the
  defect-path `_render`; both factory signatures and call sites
  are unchanged, and both renderer bodies are byte-identical to
  baseline modulo the moved lines (mechanical diff under
  `<root>/verify-mechanics-1/root-render-*.txt` and
  `edge-render-*.txt`: `ROOT_RENDERER_IDENTICAL`,
  `EDGE_RENDERER_IDENTICAL`), so R4's per-site wordings and the
  `_defect_message` tripwire arm sets are untouched.
- No dead code added: `conditions` is consumed by the guarded
  call; the two added comment lines describe the grouping.
- No new settings-at-import: the import block is identical to
  baseline except the L1 comment anchor (a comment, not an
  import); `grep settings|django.conf` over the target is clean;
  module level still defines only the `ContextVar`, plan cache
  and constants.
- Test tier per AGENTS.md: the three new pins count
  `QuerySet.filter` calls and `truth.name` invocations, both
  unobservable on the wire, so package tier is correct; SQL
  identity stays pinned by
  `test_identity_hook_targets_compose_default_manager` and the
  live `test_cascade_query_count_fixed`, rendered prose by the
  existing defect-path nodes.

Fence check (R1/R2/R15): R2's
`_is_unsupported_forward_edge` body is byte-identical to
baseline (`R2_IDENTICAL`); the R1 pair's bodies are untouched --
the single differing line is the implemented L1 docstring
anchor (`Decision 5 step 1` -> `spec-034 Decision 5 step 1`),
which adds no seam rationale and deletes nothing, so the
TODO-ALPHA-053 fence (paths undecided) is respected. R15: no
glossary/body edit smuggled -- `docs/GLOSSARY.md` still hashes
`3413edc3...` (record fingerprint), `git diff ITEM_BASELINE --
docs/GLOSSARY.md docs/SPECS/` is empty, and the target module
docstring has no hunk. No symbol moved or renamed, so no
`--cited-by` run is owed. Neither module first line changed
(test first line verified identical), so no TREE.md render is
owed. Four lint gates, `--check` forms, all green: `ruff
check` (All checks passed), `ruff format --check` (2 files
already formatted), `check_trailing_commas.py --check`
(violations 0), `check_citations.py --check` (1299 resolve).

Runs: NONE executed -- the review pool is 4/4 bound (`before`,
`performance`, `mechanics`, `implement`; `workspace.py status`
observed), and release is Worker-0's, so both attempts of the
prescribed `uv run python scripts/workspace.py run
review/permissions.py/verify-mechanics-1 -- pytest
tests/test_permissions.py --no-cov -p no:cacheprovider -q`
exited with the bind refusal and no run id. The live cascade
pins (`examples/fakeshop/test_query/test_products_visibility_api.py`,
22 tests; `test_library_inheritance_api.py::test_signage_on_a_city_less_branch_is_hidden_by_the_proxy_default_manager`)
likewise unrun. Cells judged: default owes the suite run above;
sharded/pg are `inapplicable by construction` for the F1/F2
delta (zero-SQL grouping + string-timing move; no alias read,
query text or dialect branch moves -- concurring with the
Performance record), though a sharded run would additionally
exercise the alias pin on the new grouping once a slot frees.

Fingerprints (`git hash-object`): target
`6c97d887744e2bb389e2fd957346540dacf85533` (= pass-1 `after`
blob); own tests
`c113d05eef6172f9837ed6b2d70676ff8957a4f8`; GLOSSARY
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`. Scratch:
`docs/review/temp-tests/permissions/verify-mechanics-1/`
(renderer identity pairs only; no copies touched, nothing
released).

Handoff: Static verification is complete and clean; behavioral
confirmation is blocked on pool release, not on the change. No
Worker-2 rework is owed -- the open thread below is a
Worker-0 coordination step with runnable commands. The main
artifact `docs/review/rev-permissions.md` still holds only the
skeleton (`Status: verifying`, no `## Implementation
(Worker-2)`); flagging, not grading -- artifact ownership is
Worker-0/Worker-2's.

Open thread (blocks `verified`, owned by Worker-0 release then
re-dispatch): (1) `uv run python scripts/workspace.py release
review/permissions.py --keep before`; (2) re-run at
`review/permissions.py/verify-mechanics-2`: the own-module
command above, then `pytest
examples/fakeshop/test_query/test_products_visibility_api.py
examples/fakeshop/test_query/test_library_inheritance_api.py::test_signage_on_a_city_less_branch_is_hidden_by_the_proxy_default_manager
--no-cov -p no:cacheprovider -q`.

Behavioral addendum (fresh dispatch; Worker-0 released the
reviewer copies, so `review/permissions.py/verify-mechanics-1`
bound directly at slot-2 and no `-2` address was needed).
Step-1 gate re-held at dispatch: `git diff ITEM_BASELINE --`
on both touched paths is byte-equal to `pass-1.diff`
(`ITEM_DIFF_EQUALS_PASS1`), fingerprints `6c97d887` /
`c113d05e`, GLOSSARY `3413edc3...` untouched, no
glossary/spec diff. Both copies report package digest
`sha256:04203a6a...5dba6`, matching the Performance
verifier's after-tree digest, `copy is fresh`, `shared
unmoved since sync`.

- Own module: `uv run python scripts/workspace.py run
  review/permissions.py/verify-mechanics-1 -- pytest
  tests/test_permissions.py --no-cov -p no:cacheprovider -q`
  -> `review-20260929T071855-dc5af8`, exit 0, `75 passed, 1
  skipped` (76 items; the skip is the file's standing
  conditional skip, present before and after).
- Live cascade pins: `pytest
  examples/fakeshop/test_query/test_products_visibility_api.py
  examples/fakeshop/test_query/test_library_inheritance_api.py::test_signage_on_a_city_less_branch_is_hidden_by_the_proxy_default_manager
  --no-cov -p no:cacheprovider -q` -> `review-20260929T071906-0cabee`,
  exit 0, `23 passed` (22 products visibility + the
  VisibleBranch twin).
- F1/F2 behavioral corroboration (Mechanics reading of the
  Performance verifier's reproduced numbers, not re-measured
  here): SQL sha identical before/after, all 11 rendered
  messages byte-equal, 0-edge path filter-free on both trees;
  the suite greens above confirm no delegation, fail-closed
  or twin regression on the final tree.
- Lint gates re-run green on the touched paths: `ruff
  check` (All checks passed), `ruff format --check` (2 files
  already formatted), `check_trailing_commas.py --check`
  (violations 0), `check_citations.py --check` (1299
  resolve).

Cells judged: default covered by the two runs above.
Sharded/pg `inapplicable by construction` for the F1/F2
delta (zero-SQL `.filter` regrouping plus defect-path string
timing; no alias read, query text or dialect branch moves),
concurring with the Performance record -- whose
`--cell sharded` alias-pin attack (`1 passed`) additionally
exercises the new grouping on the multi-db path, so no
further cell run is owed.

Scratch extended:
`docs/review/temp-tests/permissions/verify-mechanics-1/`
now holds the renderer identity pairs plus `own-module.log`
(`-dc5af8`) and `live-pins.log` (`-0cabee`).

Open thread closed: the pool released, both prescribed
commands ran green, no new defect found. No-findings stands.

Handoff: Behavioral confirmation complete; the static
section above is unchanged and still holds. Nothing released
(the copy and scratch belong to Worker-0's closeout). The
main artifact still holds only the skeleton -- same flag as
before, still Worker-0/Worker-2's, not a gap in this record.

Status: verified
