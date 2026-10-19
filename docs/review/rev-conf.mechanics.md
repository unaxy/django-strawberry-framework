# Review · Mechanics: `django_strawberry_framework/conf.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=0ec338aef4e12fe5930ce0839d10d93ec3403c6d

## Trace

Required reading in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-conf.md` (skeleton). Sibling
`docs/review/rev-conf.performance.md` read whole (Status: no-findings;
Path class hot via two readers; four rejections; no Cross-axis section;
Handoff absorbed — its caller census concurs with mine below and its R1
live-read rejection is consistent with F1's Must-not-change). Sibling
`rev-conf.comments.md` did not exist when read.

Target read whole (570 lines) at blob `ae3de0a3` (live, dirty).
`ITEM_BASELINE` blob for the target equals the live blob (the item
baseline captured the dirty tree); HEAD blob is `c6ad46aa`. HEAD..live
is the concurrent truth-migration (message rendering through
`django_strawberry_framework/utils/truth.py::kind` /
`django_strawberry_framework/utils/truth.py::render`, hostile-iteration
containment replaced by documented propagation, docstrings and
`tests/base/test_conf.py` rows updated with it). Reviewed live as
dispatched; F1 is annotation-only and cites live oracles, so it does
not re-litigate the migration's behavior.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/conf/mechanics/inspect/` (json
`docs/review/temp-tests/conf/mechanics/conf.json`): 17 symbols, 0
Django/ORM markers, 3 import-time calls (`object()`, `Settings(None)`,
`setting_changed.connect`). Leads only.

Consumer edges verified by read (production reaches the `settings`
singleton only through the readers; no production `conf import
settings` outside docstrings):

- `django_strawberry_framework/conf.py::upstream_patches_enabled` — 4
  gates, one literal call site each in `_django_patches.py:418`,
  `_strawberry_patches.py:847`, `_cross_web_patches.py:343`,
  `_graphql_core_patches.py:124`, all inside `UPSTREAM_PATCH_DEPENDENCIES`.
- `django_strawberry_framework/conf.py::hide_flat_filters_setting` —
  `django_strawberry_framework/filters/inputs.py::_build_input_fields`
  (`filters/inputs.py:940`, coerces with `bool()`).
- `django_strawberry_framework/conf.py::nested_connection_strategy_setting` —
  `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`
  (function-local import under `if value is None`, no cycle: conf
  depends only on leaves).
- `django_strawberry_framework/conf.py::single_parent_fast_path_setting` —
  `django_strawberry_framework/optimizer/single_parent_fetch.py::_fetch_single_parent_rows`
  (function-local import with an in-code lazy justification).
- `django_strawberry_framework/conf.py::relay_globalid_strategy_setting` —
  `django_strawberry_framework/types/relay.py::_validated_globalid_setting`
  (function-local import; the block documents the `base.py` load cycle
  and forbids hoisting).
- `django_strawberry_framework/conf.py::max_request_body_bytes_setting` —
  `django_strawberry_framework/views.py::_resolved_max_request_body_bytes`.
- `django_strawberry_framework/conf.py::resource_policy_setting` /
  `django_strawberry_framework/conf.py::error_policy_setting` —
  `django_strawberry_framework/resource_policy.py::resolve_resource_policy` /
  `django_strawberry_framework/error_policy.py::resolve_error_policy`.
- `django_strawberry_framework/conf.py::testing_endpoint_setting` —
  `django_strawberry_framework/testing/client.py::TestClient` family.
- `RELAY_GLOBALID_STRATEGY_KEY` constant imported by `types/base.py:55`
  as an error-message subject label only
  (`django_strawberry_framework/types/base.py::_validate_globalid_strategy`);
  the setting itself is read through the reader in `types/relay.py`.
- `django_strawberry_framework/conf.py::reload_settings` wired once via
  `setting_changed.connect` at import with a dispatch UID; `apps.py`
  `ready()` dispatches only the four patch appliers and connects no
  signal (GLOSSARY apps anchor concurs).

Contract sources: AGENTS.md settings/AttributeError rule; the module
and reader docstrings; GLOSSARY anchors (app-load gate, kill-switch
shapes, error-policy thin reader, resource precedence, GlobalID
precedence, body-cap `None` semantics, test-client endpoint ladder);
`docs/README.md` (error policy, single-parent fast path, endpoint
precedence); `tests/base/test_conf.py` read whole; specs 021/024/027/
031/043/046/047/048 plus DRY `dry-file-conf.md` at grep level for
orientation (F1 below is derived from live oracles plus the probe, not
imported).

Instruments: the trace above; `check_truthful_reads.py --report`
(tier-2 heuristics flag no `isinstance` rule; zero rows name conf.py);
one workspace probe,
`docs/review/temp-tests/conf/mechanics/probe_verbatim.py`, run
`review-20260928T234142-faef82` (address `review/conf.py/mechanics`,
cell default, package digest
`sha256:41e15d13e6b3319ad3be2833eed44c172f16590b77b202838bfc57cc2e52a54c`),
`1 passed`.

Cells: default probed. Sharded and pg are `inapplicable by
construction`: the target reaches no database, alias, or dialect
decision (pure in-memory settings reads; no ORM import or usage), and
the probe asserts pure-Python return values.

Looks-for discharge (Mechanics floor):

- Rule enforced at a caller instead of its owner: none, except F1's
  vocabulary mirror (filed Low; fix at the owner, no move). The shape
  contract is single-sited in
  `django_strawberry_framework/conf.py::_normalize_user_settings` (4
  call sites, 1 definition); domain validation at consumers is the
  specified thin-reader placement.
- Policy in an adapter, mechanism in a policy layer: none. The
  `APPLY_UPSTREAM_PATCHES` shape policy is owned here per spec-021/024
  and the GLOSSARY kill-switch anchor; the thin readers carry no
  domain policy.
- Decision vs contract sources: F1; every other behavior matches
  (GLOSSARY/README anchors and the AGENTS.md rule verified per reader).
- Branch no real path reaches: none. The `pragma: no cover`
  non-backed-`None` branch is unreachable via public API
  (init/reload invariant); all other branches have oracle rows,
  including the dunder short-circuit, the property-recursion guard,
  and the resync-fails-loud path.
- Mode flag standing in for a named adapter: none. The
  bool-or-mapping toggle is the specified global plus per-dependency
  form; the strategy string resolves to adapters in
  `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`.
- State owned in two places: none. Cache, live pointer, and backed
  flag are three distinct facts (loadedness, cache key, backing),
  each with pinned transitions; backed-ness is not derivable from
  cache-`None`-ness.
- Dependency pointing the wrong way: none. conf depends only on
  `exceptions` and the `utils` leaves (cycle scan: `relations`,
  `strings`, `typing`, `truth` import no conf module); no
  `TYPE_CHECKING`; the `from ...utils import truth` spelling is the
  package-wide idiom.
- `django.conf.settings` read at import: none. Import binds the
  `LazySettings` proxy only; `Settings(None)` is lazy (oracle pins
  `_user_settings is None` post-construction); the utils chain holds
  zero settings references; `connect()` reads nothing.
- `__all__` disagreeing with the public surface: none. No `__all__`
  in the module; the package root exports nothing from conf
  (internal API per the
  `django_strawberry_framework/conf.py::upstream_patches_enabled`
  docstring). Absence, not disagreement.
- Two sites implementing one rule: R2, R3, R6 (DRY challenges, every
  count 1).
- Sync/async twins that drifted: none (no async surface).
- Guard one flavor has and a sibling lacks: R1, R4.

Fingerprints (`git hash-object`, live tree):
`django_strawberry_framework/conf.py`
`ae3de0a36e2f7737a2c8350e532cdb761b295bcf`;
`tests/base/test_conf.py`
`55b333eb2fff714365058d0a8651fc3a57c603e3`;
`django_strawberry_framework/utils/__init__.py`
`1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee`;
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9`;
`django_strawberry_framework/utils/relations.py`
`05ff55b098382a4a7aafe5a097c3b5e906f8f985`;
`django_strawberry_framework/utils/strings.py`
`5a4f481132f87cc83abeb2a4a4a679990fa5b9bc`;
`django_strawberry_framework/utils/typing.py`
`a672cd6b4f65eb080acd971a6b98`;
`django_strawberry_framework/types/relay.py`
`4b2a9df59d6dc99270e3aa8ffac397468f7eee1b`;
`django_strawberry_framework/types/base.py`
`dc67f084cbc969d64b7b1f1ef18c388095d394f7`;
`django_strawberry_framework/optimizer/nested_fetch.py`
`1678609e8f331dceb173cddea118e9e0bfe72a61`;
`django_strawberry_framework/optimizer/single_parent_fetch.py`
`e995270af9b213b7f931c03d7dc8f7c084819e1b`;
`django_strawberry_framework/filters/inputs.py`
`a932dbf85d89791280774b0600a40b5fb43b89e4`;
`django_strawberry_framework/resource_policy.py`
`cc3f9d80b9d55af8b725a77c73aba3d8110e0037`;
`django_strawberry_framework/error_policy.py`
`57a0bed1ba730f8e4c1f4c879d852274eac39f12`;
`django_strawberry_framework/views.py`
`48ee582ecdba41d49beb2434f2a9e0af992d39d4`;
`django_strawberry_framework/testing/client.py`
`b14394431f882c022ae7f07b93e3bb0a3774a753`;
`django_strawberry_framework/_django_patches.py`
`6918a213170ea902386a5845da8c6cd1f901baf2`;
`django_strawberry_framework/_strawberry_patches.py`
`90f711fb420b8902434406735c2e367f011e4177`;
`django_strawberry_framework/_cross_web_patches.py`
`52bf8f5712d632817587f93c4eeb881fd74ffaae`;
`django_strawberry_framework/_graphql_core_patches.py`
`90ac4f3cc15be1c24dc1f0281206e260d7555cb6`;
`django_strawberry_framework/apps.py`
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f`;
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`django_strawberry_framework/exceptions.py`
`206e9f8d914f640134cf72e374fadeac41d13a39`;
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`;
`docs/README.md`
`30978c34f63a833ffcc0fa11c80b773d241921be`.

## Findings

### High

None.

### Medium

None.

### Low

#### F1: six thin readers declare narrow return types but return configured values verbatim

- **Observation** — Six readers in
  `django_strawberry_framework/conf.py` promise a narrow type their
  bodies do not ensure:
  `django_strawberry_framework/conf.py::nested_connection_strategy_setting`
  (`-> str`),
  `django_strawberry_framework/conf.py::single_parent_fast_path_setting`
  (`-> bool`),
  `django_strawberry_framework/conf.py::testing_endpoint_setting`
  (`-> str`),
  `django_strawberry_framework/conf.py::hide_flat_filters_setting`
  (`-> bool`),
  `django_strawberry_framework/conf.py::relay_globalid_strategy_setting`
  (`-> str | Callable[..., str] | None`),
  `django_strawberry_framework/conf.py::max_request_body_bytes_setting`
  (`-> int | None`). Each body is `getattr(settings, KEY, default)`,
  which hands back any explicitly configured value unchanged; only a
  *missing* key falls back to the default. The sibling readers
  `django_strawberry_framework/conf.py::resource_policy_setting` and
  `django_strawberry_framework/conf.py::error_policy_setting` declare
  the honest `-> Any`.
- **Evidence** — Committed oracle
  `tests/base/test_conf.py::test_single_parent_fast_path_setting_is_an_unvalidated_toggle`
  pins verbatim pass-through (`0` returns `0`, `"yes"` returns
  `"yes"`); the endpoint docstring pins `None` passing through to
  `Client.post`; the remaining reader docstrings pin the
  thin-reader/no-validation discipline with validation owned by
  `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`,
  `django_strawberry_framework/views.py::_resolved_max_request_body_bytes`,
  `django_strawberry_framework/types/relay.py::_validated_globalid_setting`,
  and the `bool()` coercion in
  `django_strawberry_framework/filters/inputs.py::_build_input_fields`.
  Workspace probe `review-20260928T234142-faef82` (`1 passed`)
  observes all six at once: `hide_flat` returns `1`,
  `testing_endpoint` returns `None`, `max_body` returns `"1024"`,
  `nested_strategy` returns `5`, `relay_globalid` returns `5`,
  `single_parent` returns `0`.
- **Impact** — A type-checker consumer (and a reader of the signature)
  is promised a `bool`/`str`/`int` the configuration input need not
  deliver; the relay union additionally mirrors vocabulary owned by
  `django_strawberry_framework/types/base.py::_validate_globalid_strategy`,
  so it rots if that vocabulary changes. No runtime effect today: no
  consumer relies on the narrow type (each coerces or validates).
- **Severity** — Low: bounded clarity/maintainability; false declared
  contract with no runtime consequence and no enforcing gate.
- **Recommendation** — Owner:
  `django_strawberry_framework/conf.py` (the annotations live here).
  Widen all six annotations to `-> Any`, matching the two honest
  siblings (`Any` is already imported). Do NOT validate or coerce in
  the readers: that would break the committed pass-through oracle
  and the thin-reader discipline the specs pin. Add one permanent
  row in `tests/base/test_conf.py` pinning verbatim pass-through for
  the five readers the suite does not pin (the single-parent reader
  is already pinned).
- **Must not change** — Verbatim pass-through for all six readers:
  the committed single-parent toggle oracle, the reader
  default/override sweep
  (`tests/base/test_conf.py::test_setting_reader_helpers_default_and_override_values`),
  and the delattr-defaults sweep
  (`tests/base/test_conf.py::test_delattr_clears_stale_cache_and_restores_defaults`)
  keep passing unchanged.
- **Proof** — Static (shared tree):
  `grep -cE "def (nested_connection_strategy_setting|single_parent_fast_path_setting|testing_endpoint_setting|hide_flat_filters_setting|relay_globalid_strategy_setting|max_request_body_bytes_setting)\(\) -> Any:" django_strawberry_framework/conf.py`
  must print `6` (`grep`, not `rg`: `rg` is not on PATH in this
  environment). Behavior (verify address):
  `uv run python scripts/workspace.py run review/conf.py/verify-mechanics-<n> -- pytest tests/base/test_conf.py::test_single_parent_fast_path_setting_is_an_unvalidated_toggle --no-cov`
  must report `1 passed`, plus the new test
  `test_setting_reader_helpers_return_wrong_typed_values_verbatim`
  in tests/base/test_conf.py covering the other five readers, which
  must pass alongside it.
- **Freshness** — Trace fingerprints cover every file this finding cites.
- **Owner + contract source** — Owner:
  `django_strawberry_framework/conf.py`. Contract sources: the
  committed pass-through oracle and reader docstrings (behavior),
  the GLOSSARY error-policy thin-reader anchor (discipline), and
  the honest `-> Any` sibling readers (fix shape).

## Rejected

### R1: bare `isinstance(x, Mapping)` at the two shape gates

`django_strawberry_framework/conf.py::_normalize_user_settings` and
`django_strawberry_framework/conf.py::upstream_patches_enabled` use
bare `isinstance` while the mapping-key check uses
`django_strawberry_framework/utils/truth.py::is_instance`. Rejected:
bare `isinstance` implements the documented ABC contract exactly
("a `Mapping`"), while `truth.is_instance` (real-MRO membership)
would narrow it by rejecting `Mapping.register()` virtual
subclasses. The truthful-reads gate has no `isinstance` rule and
names conf.py in zero rows; no live docstring promises containment
of a hostile `__class__` liar at the probe (iteration propagation
is the documented and pinned stance). A liar is off-contract input,
so this is speculative risk without a reachable supported input,
not a finding. Trigger: a supported input shape reaching the probe
hostilely, or a new gate rule flagging these lines.

### R2: the thin-reader family repeats one `getattr` body eight times

DRY change challenge. Posit "change the missing-key default
mechanism": zero definitions change (the mechanism is
`getattr`-with-default over the single
`django_strawberry_framework/conf.py::Settings.__getattr__`
definition, owned by Python plus that method). Posit "change one
key's default": exactly one definition (that reader's literal).
Posit "rename a key": the one constant plus its mechanical
references. Every count is 1; the per-key defaults, consumers, and
validation homes differ by spec. The identical
`resource_policy_setting` / `error_policy_setting` bodies are the
same verdict (spec-047 vs spec-048 own each key). Not duplication.
Trigger: a second reader or default for one key, or a shared
default-computation rule spanning keys.

### R3: `None` is handled at three sites

`django_strawberry_framework/conf.py::_normalize_user_settings`
(`None` -> `{}`),
`django_strawberry_framework/conf.py::Settings.reload` (`None` ->
restore backing), and
`django_strawberry_framework/conf.py::Settings._reload_from_django`
(`None` -> delegate) each name `None` distinctly: empty-settings
vs override-exit protocol vs delegation. The module docstring
documents both meanings and defers tightening them together.
Trigger: the deferred tightening lands (then all three plus the
`Meta.optimizer_hints` seam change under one card).

### R4: six readers validate nothing while `upstream_patches_enabled` validates strictly

Not a missing guard: the thin-reader discipline is specified per
key (reader docstrings; specs 031/043/046/047/048; GLOSSARY
thin-reader anchor), each owner validates at its own site
(`django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`,
`django_strawberry_framework/views.py::_resolved_max_request_body_bytes`,
`django_strawberry_framework/types/relay.py::_validated_globalid_setting`,
`django_strawberry_framework/filters/inputs.py::_build_input_fields`,
both policy resolvers, the test client), and committed oracles pin
pass-through. No contract source requires conf-side validation.
Trigger: a contract source requiring validation of a key in conf.

### R5: three consumers import their reader function-locally

`types/relay.py` documents the `base.py` load cycle and forbids
hoisting; `nested_fetch.py` imports under the `None` arm at its
single use; `single_parent_fetch.py` carries an in-code lazy
justification. Direction is correct (consumers depend on conf,
which depends only on leaves; no cycle exists), and no contract
breaks. Hoisting would be style. Trigger: an import cycle
involving conf, or a measured import-time regression attributed to
these lines.

### R6: consumer mappings are copied with `dict(x)` at two sites

`django_strawberry_framework/conf.py::_normalize_user_settings` and
`django_strawberry_framework/conf.py::upstream_patches_enabled`
each copy once. The shared primitive is the `dict` builtin, owned
by Python; the surrounding framing (top-level shape vs
per-dependency toggle, distinct error messages and oracles)
differs per site. A shared helper would abstract a one-liner.
Trigger: a third copy site or a shared framing requirement.

Handoff: Mechanics review is closed with one Low finding (F1,
narrow return annotations vs verbatim pass-through) and six
rejections. Read beyond the record's trace: spec and DRY files at
grep level only (orientation; nothing imported as a finding), the
sibling Performance record whole (concur on call sites; its R1
live-read stance matches F1's Must-not-change), and the
HEAD-vs-live diff to attribute the concurrent truth-migration
(which F1 deliberately does not touch — annotation-only fix, no
behavior change). The judgment call most likely to be revisited is
F1's fix direction (widen annotations rather than coerce in the
readers): coercion would break the committed toggle oracle and the
spec-pinned thin-reader discipline, so widening is the only
direction consistent with the oracles. Open threads: none. Cells
sharded/pg unverified by construction (reason in Trace).

## Verification (Mechanics)

Verify pass 1 at address `review/conf.py/verify-mechanics-1`, scratch
`docs/review/temp-tests/conf/verify-mechanics-1/`, item diff
`docs/review/temp-tests/conf/diff/pass-1.diff`.

Step 1 (tree still carries the change):
`git diff 0ec338aef4e12fe5930ce0839d10d93ec3403c6d --
django_strawberry_framework/conf.py tests/base/test_conf.py` hashes equal to
`pass-1.diff` (`sha256:6baebb46...`, `diff` empty, HASH_EQUAL). The unscoped
item diff additionally names `docs/dry/dry-0_0_15.md` and
`docs/review/review-0_0_15.md`, concurrent work in files this pass never
touched, as Worker-2 reported. Graded the two owned paths only.

Proof lines, run verbatim BEFORE reading `## Implementation (Worker-2)`:

- Static: `grep -cE "def (...six readers...)() -> Any:"
  django_strawberry_framework/conf.py` prints `6` (shared tree, no run id
  by construction). Pass.
- Behavior: `workspace.py run review/conf.py/verify-mechanics-1 -- pytest
  tests/base/test_conf.py::test_single_parent_fast_path_setting_is_an_unvalidated_toggle
  --no-cov` → `review-20260929T001228-aef9af`, `1 passed`. Pass.
- New row: `... -- pytest
  tests/base/test_conf.py::test_setting_reader_helpers_return_wrong_typed_values_verbatim
  --no-cov` → `review-20260929T001235-288989`, `1 passed`. Pass.
- Other records' `## Cross-axis (for Mechanics)`: Performance has no
  Cross-axis section; Comments `## Cross-axis` is `None`. Nothing to run.

Numbers reproduced (Worker-2's Mechanics claims):

- `0` on the ITEM_BASELINE blob / `6` live: reproduced —
  `git show 0ec338a...:conf.py | grep -cE ...` prints `0`, live prints `6`.
  ITEM_BASELINE blob `ae3de0a3...` equals the Trace fingerprint; live
  `3820c575...` (conf.py) and `7275af68...` (test_conf.py) equal Worker-2's
  post-edit fingerprints.
- Must-not-change oracles green, at the verify address:
  `test_setting_reader_helpers_default_and_override_values` +
  `test_delattr_clears_stale_cache_and_restores_defaults` →
  `review-20260929T001257-734393`, `2 passed`; full
  `tests/base/test_conf.py` → `review-20260929T001304-e2ed97`, `56 passed`
  (55 pre-existing + 1 new), matching Worker-2's count.

Failability (own `prove`, new manifest, whole-module scope):

- `workspace.py prove review/conf.py/verify-mechanics-1
  docs/review/temp-tests/conf/verify-mechanics-1/failability-manifest.json`
  → `review-20260929T001503-8e0358`, exit 0 (re-run
  `review-20260929T001533-4a11b3` identical verdicts).
- Entry 1, falsy-collapse mutant (`or "/graphql/"` on the endpoint body, a
  different shape from Worker-2's `str()` coercions): pinned — the 1
  failing row is exactly the new row, over the whole 56-row module
  (baseline `56 passed`, 0 pre-existing failures). This strengthens
  Worker-2's evidence two ways: a second mutant shape fails the same row,
  and the module-wide scope proves no collateral (Worker-2's single-node
  scope could not observe any; the in-module endpoint census — `None`
  only in the new row, every other value a truthy string — is why
  exactly-one fails).
- Entry 2, `reverse_patch` of the 7 Mechanics code hunks (6 annotations +
  `Callable` import, extracted verbatim from `pass-1.diff` into
  `verify-mechanics-1/mechanics-hunks.diff`), `expect_failing: []`:
  behaviour preserved, no row failed. This is the direct failability
  judgment for the shipped change: the production edit is
  annotations-only and runtime-invisible by construction, so a revert
  cannot fail any test — and the revert that must change nothing changed
  nothing, restores byte-proved. Worker-2's coercion mutants remain the
  correct failability evidence for the new test row itself (it pins the
  verbatim behavior the annotations now honestly describe), and my
  entry 1 independently confirms that evidence holds.

Whole-diff reading (Mechanics lens): 10 conf.py hunks + 1 test hunk, all
attributed. The 7 Mechanics code hunks widen exactly the 6 readers F1
named plus the orphaned `Callable` import (`Any` was already imported;
the 2 honest siblings untouched). The 3 Comments prose hunks are
comment/docstring-confined per the diff and move no code; their truth is
the Comments verifier's grade, but through this axis: F3's four-writer
inventory verified by AST census (`__init__:237`, `user_settings:282`,
`reload:304`, `_reload_from_django:313`, no fifth site), the
keeps-backing note verified against `_reload_from_django` (`_django_backed
= True` on the mapping leg, `reload(None)` delegation on the `None`
leg); F2's mechanism verified against the body (guard set holds
`"user_settings"`, `ConfigurationError` propagates per the `__getattr__`
docstring). No owner move was owed or made.

Attacks (all pass, recorded, owe nothing):

- `Callable` removal: zero `Callable` remnants in conf.py; zero
  `from ...conf import ...Callable` importers across package, tests and
  examples. The import hunk is runtime-safe.
- Reader-annotation census: all 8 thin readers now `-> Any`;
  `upstream_patches_enabled -> bool` retained, correct (it validates
  strictly; untouched by the diff).
- Handoff thread 1 (revert must carry all 7 hunks): my entry-2
  `reverse_patch` carried exactly those 7, byte-extracted from the item
  diff. Covered.
- Handoff thread 2 (citation rewrap): tree-wide `check_citations.py
  --check` resolves 1297/1297, same count Worker-2 reported. Covered.
- No symbol was moved or renamed, so no `--cited-by` sweep is triggered.

Disputes: none. `## Implementation (Worker-2)` records `disputed:`
nowhere (`grep -i disput` hits only "no dispute arose").

Test tier: the new row grows `tests/base/test_conf.py` — permitted
(AGENTS.md: `tests/base/` holds exactly `test_init.py` + `test_conf.py`,
both may grow, no new files; no new file added). Package tier is the
mandated tier: the record's own Recommendation named this file, the
thin-reader return values are unreachable from a real GraphQL query, and
the single-parent sibling oracle sets the precedent. No missing fixture.

Lint gates (`--check` forms only, touched paths unless noted):

- `ruff check` — All checks passed.
- `ruff format --check` — 2 files already formatted.
- `check_trailing_commas.py --check` — 0 violations.
- `check_citations.py --check` (tree-wide) — 1297 citations resolve.

Cells: default verified (every run above). Sharded and pg remain
`inapplicable by construction`: the target reaches no database, alias or
dialect decision (pure in-memory settings reads; no ORM import or
usage), and the new test asserts pure-Python return values. All three
axis records concur.

Verdict: `Status: verified`. F1 implemented exactly as recommended (widen
annotations, no coercion); Must-not-change holds; the new row passes and
is pinned by two independent mutant shapes; the annotation revert
proves runtime invisibility; lint green; no new findings, no gaps.

Handoff: Mechanics verification is closed, pass 1 verified. Beyond the
records' traces I read only the item diff, the `__getattr__` /
`reload` / `_reload_from_django` bodies for the F2/F3 mechanism checks,
the endpoint-reader census in `tests/base/test_conf.py` (for the
whole-module prove scope), and `prove_failability.py`'s manifest
docstring. The judgment call most likely to be revisited is the
failability split (annotations revert `[]` + coercion mutants pin the
row): it is the only coherent reading of an annotations-only change —
the revert proves the production edit changes nothing, the mutants
prove the test row guards the behavior the annotations describe. Open
threads: none. The Comments verifier owns prose-truth grades; nothing
here contradicts its record.
