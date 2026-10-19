# Review · Mechanics: `django_strawberry_framework/connection.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e6b022ba44f4e14da9e1825cea7047aa38d03298

## Trace

Required reading in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for
this target), `docs/review/rev-connection.md` (skeleton, Status:
reviewing, Path class blank). Sibling axis records
`docs/review/rev-connection.performance.md` and
`docs/review/rev-connection.comments.md` did not exist when read;
no Handoff or Cross-axis sections to absorb.

Target read whole (2285 lines) live at blob `68d1ea2c` (dirty).
`git diff ITEM_BASELINE -- django_strawberry_framework/connection.py`
is empty: the item baseline captured the dirty tree, so live IS the
baseline. HEAD blob for the target differs (`git diff HEAD -- <target>`
is +67/-99): the concurrent truth-migration (reads through
`django_strawberry_framework/utils/truth.py`, hostile-containment
replaced by documented propagation) plus the new
`django_strawberry_framework/connection.py::_reject_negative_offset_cursor`
guard. Reviewed live as dispatched; H1's path is behavior-identical
at HEAD and live (verified by hunk inspection: no HEAD..live hunk
touches the offset `last: 0` delegation), so the defect is not an
artifact of concurrent work.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/connection/mechanics/inspect/` (json
`docs/review/temp-tests/connection/mechanics/connection.json`): 56
symbols, 18 control-flow hotspots, 19 hot entry points. Leads only.

Edges traced by read (callers, importers, registrations, oracles):

- Producers/consumers:
  `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`
  imports
  `django_strawberry_framework/connection.py::_build_relation_connection_resolver`
  and
  `django_strawberry_framework/connection.py::_connection_type_for`
  function-locally (cycle accommodation, `_node_fields_declared`
  precedent); package root imports
  `django_strawberry_framework/connection.py::DjangoConnection` and
  `django_strawberry_framework/connection.py::DjangoConnectionField`
  explicitly; `register_subsystem_clear(clear_connection_type_cache)`
  wires the type cache into `registry.clear()` (co-clear pinned by
  `tests/test_registry.py`).
- Siblings read substantive:
  `django_strawberry_framework/list_field.py` (target guards,
  pipelines, synthesized signature, resolver bodies),
  `django_strawberry_framework/keyset.py` (cursor-field resolution,
  ref validation), `django_strawberry_framework/utils/connections.py`
  (window bounds, bound check, cap resolution),
  `django_strawberry_framework/optimizer/plans.py`
  (`effective_connection_order`, `deterministic_order`),
  `django_strawberry_framework/optimizer/selections.py`
  (`prime_selected_fields`, selection primitives),
  `django_strawberry_framework/utils/querysets.py` (seal policies,
  `prepared_resolver_source`), `django_strawberry_framework/relay.py`
  (shared validator import),
  `django_strawberry_framework/resource_policy.py` (`_windowed_rows`,
  `policy_from_info`), `django_strawberry_framework/types/resolvers.py`
  + `types/__init__.py` (import shape only).
- Upstream engine read in `.venv` (strawberry-graphql 0.324.0):
  `strawberry/relay/utils.py` (`SliceMetadata.from_arguments`,
  `should_resolve_list_connection_edges`) and
  `strawberry/relay/types.py` (`ListConnection.resolve_connection`,
  incl. the `edges[-last:]` tail branch).
- Oracles: `tests/test_connection.py` (93 tests),
  `tests/test_relay_connection.py` (63),
  `tests/test_keyset_connection.py` (18), `tests/test_keyset.py`
  (bounds shapes), `examples/fakeshop/test_query/test_keyset_api.py`
  (live keyset incl. the three `last: 0` cap twins),
  `examples/fakeshop/test_query/test_library_api.py::test_nested_connection_last_zero_serves_quirk_via_per_parent_fallback`;
  `examples/fakeshop/config/schema.py` (schema under probe).
- Contract sources: GLOSSARY anchors (`DjangoConnection`,
  `DjangoConnectionField`, `ResourcePolicy`, execution resource
  policy, connection-aware optimizer planning); `docs/README.md`
  (production error policy, connection pipeline order, `totalCount`
  post-filter pre-slice selection-gated); module + symbol docstrings;
  the oracles above.

Instrument: one workspace probe,
`docs/review/temp-tests/connection/mechanics/probe_last_zero_cap.py`,
final evidence run `review-20260929T004349-77be15` (address
`review/connection.py/mechanics`, cell default, copy slot-3 synced
2026-09-29T00:39:33Z, package digest
`sha256:4e7fd524092a2736ec9a7e6248d5f1c6d7c8e2447c30ec72aa0d70e75aa849be`,
exit 0, 10 assertions). Earlier iterations `review-20260929T004003-ce2c44`
(evidence observed, over-strict assertion), `review-20260929T004029-02a4d5`
(exit 0), and one uncaptured-id run are superseded by it. The probe
writes 105 uniquely-named rows to its copy's database and deletes
them in a `finally` (row count 132 before and after each run; the
copy reports `modified: 1 (examples/fakeshop/db.sqlite3)` at file
level only).

Cells: default probed. Sharded and pg are `inapplicable by
construction` for H1's path (no alias or dialect decision on the
`last: 0` offset delegation; `last: 0` is never window-planned so no
backend-specific SQL is involved) and were not run; the verifier
judges the claim.

Looks-for discharge (Mechanics floor):

- Rule enforced at a caller instead of its owner: H1's gap is the
  one hit (the `max_page_size` clamp sits at the right seam; the
  quirk path escapes the clamped value). Every other enforcement
  point is correctly placed: the `first` + `last` guard is owned
  here because Strawberry provides none (GLOSSARY concurs); the
  pre-sliced guard is owned here because the connection reorders
  and slices on every request; `prime_selected_fields` runs here
  because this module holds the only production
  `info.selected_fields` read and the optimizer extension is
  optional; strictness reuses the parameterized
  `django_strawberry_framework/types/resolvers.py::_check_n1`,
  never a second checker.
- Policy in an adapter, mechanism in a policy layer: none. The
  field reads `ResourcePolicy.max_page_size` and the deadline
  through the owned seams and authors no policy; the extension
  does setup-only per its anchor.
- Decision vs contract sources: H1. Everything else matches: the
  pipeline order, the error colors (`ConfigurationError` at
  construction, `GraphQLError` on the wire per the README error
  policy), `totalCount` post-filter pre-slice selection-gated,
  the keyset vocabulary fixing, the cursor-parity sharing.
- Branch no real path reaches: none. Three unreachable-by-
  construction tails, each deliberate and pinned: the reversed
  `last: 0` window guard (`test_resolve_from_window_last_zero_stays_a_defensive_guard`;
  GLOSSARY: `last: 0` unplanned), the backward-keyset wrapper arm
  (`test_backward_args_over_a_window_wrapper_fall_back_to_the_keyset_slicer`;
  backward keyset unwindowable per `test_derive_keyset_window_bounds_backward_shapes_are_unwindowable`),
  the no-order keyset shape (`test_keyset_order_state_default_order_reuses_declared_columns`;
  unreachable via the pipeline because
  `django_strawberry_framework/optimizer/plans.py::effective_connection_order`
  always returns non-empty).
- Mode flag standing in for a named adapter: none. `want_count`,
  `reverse`/`backward`, `last_zero_quirk` are page-description
  inputs, not adapter selections (recomputing `want_count` per
  site would fork the gating); the cursor-vocabulary fork IS by
  named adapter (`DeclaredCursorState`); `_resolves_total_count`
  is one boolean axis over two variants whose override
  alternative was rejected for single-siting (trigger: a second
  axis of variation).
- State owned in two places: none. Cache entries vs registry
  definitions (provenance reference, not ownership; co-clear
  wired + pinned); `want_count` (request verdict) vs
  `_TOTAL_COUNT_ATTR` (captured value; single writer
  `django_strawberry_framework/connection.py::_set_total_count`);
  class-baked `_dst_keyset_state` vs the definition (fixed-at-
  generation vocabulary, documented).
- Dependency pointing the wrong way: none. The top-level field
  surface imports types/optimizer/utils leaves; the finalizer's
  function-local connection import is the documented cycle
  accommodation; the filters/orders function-local imports serve
  the pinned lazy-subpackage contract; no `TYPE_CHECKING`.
- `django.conf.settings` read at import: none. Zero settings
  references in the module; keyset reads settings lazily at
  mint/decode, never at import.
- `__all__` disagreeing with the public surface: none. Absent,
  not disagreeing: matches keyset/schema/permissions/registry,
  and the root exports are explicit imports unaffected by a
  module `__all__`.
- Two sites implementing one rule: R1, R2, R3 (DRY challenges,
  every count 1).
- Sync/async twins that drifted: none.
  `django_strawberry_framework/connection.py::_pipeline_sync` vs
  `django_strawberry_framework/connection.py::_pipeline_async`
  differ only in the documented async-guard choice plus await
  color, sharing `_prepare_pipeline_source`, `_sidecar_steps`,
  `_sidecar_visibility_policy`, `_finalize_queryset`;
  `django_strawberry_framework/connection.py::_attach_count_sync`
  vs `django_strawberry_framework/connection.py::_attach_count_async`
  differ only in the await-before-raise discipline, both routing
  through the single writer. The synthesized signatures carry
  byte-identical `order_by` annotations; the return annotations
  differ by contract (`Iterable[T]` required by
  `ConnectionExtension` vs empty for nullability ownership).
- Guard one flavor has and a sibling lacks: H1 (cap binds keyset
  `last: 0`, escapes offset `last: 0`, contract sources cited);
  R4, R5.

Fingerprints (`git hash-object`, live tree):
`django_strawberry_framework/connection.py`
`68d1ea2c325eb8a3c34d34df7bc6125ad736ec16`;
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`django_strawberry_framework/list_field.py`
`450e87cde13edc1bfc3c4d4a161c5540d1ac5277`;
`django_strawberry_framework/keyset.py`
`279ad7b089de282e52b8210ad9c61101c8b3e401`;
`django_strawberry_framework/utils/connections.py`
`efcf749a26dc7d3fa9b3cc142789a11de2647070`;
`django_strawberry_framework/utils/querysets.py`
`8fc556d582b313e4aed7cddaa15f9a8480d88a46`;
`django_strawberry_framework/types/finalizer.py`
`b9d8acb2b9428cc8297550414ff86bdd98e0d1a7`;
`django_strawberry_framework/types/resolvers.py`
`640905c63f465db4de16c3a07492b27f3d12d3ad`;
`django_strawberry_framework/types/__init__.py`
`1bf69028dbdcac9a42f6b6ba05e1220fdde0a155`;
`django_strawberry_framework/optimizer/plans.py`
`33140a766cd3fb2484a40fe499d466c8ced8b4a6`;
`django_strawberry_framework/optimizer/selections.py`
`b189fa15639910e3f59a0e40203154b59f0c7589`;
`django_strawberry_framework/relay.py`
`e75e2b66a9b406f60d55e952a001d640392331c1`;
`django_strawberry_framework/resource_policy.py`
`cc3f9d80b9d55af8b725a77c73aba3d8110e0037`;
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`;
`docs/README.md`
`30978c34f63a833ffcc0fa11c80b773d241921be`;
`tests/test_connection.py`
`8e08b23fbf7eee84a94ab406d8713855056087a1`;
`tests/test_relay_connection.py`
`a4769a3dfb4aadc1e6bedf0677eb9c0f51fc22b0`;
`tests/test_keyset_connection.py`
`70db0483f461a4ef7befb11bc4acaf1302bb76d3`;
`tests/test_keyset.py`
`e5655de79cdb3d97c5025a4e69169a307272c10b`;
`examples/fakeshop/test_query/test_keyset_api.py`
`305b972f228cb1326e783ccb05f2e3eee3c429e0`;
`examples/fakeshop/test_query/test_library_api.py`
`2cd1b6dd1a2f3f9a5261ff9a4509611633fa3f20`;
`examples/fakeshop/config/schema.py`
`303ea2da9df1f8611c02926fd28c59e5ccf9ecac`;
`examples/fakeshop/apps/products/schema.py`
`04a5afe3dddff9279660ae1370924e03857d57e7`;
`examples/fakeshop/apps/products/models.py`
`02d3ea18e94fc70461decd57c081706f326d9b1b`;
`docs/review/review-0_0_15.md`
`c95d99994ec0d6c47cec63fa772dbadf82ed9b97`;
`docs/review/rev-connection.md`
`34a005b5c76f2e4748f4c0531f16a1632c55569e`;
probe
`docs/review/temp-tests/connection/mechanics/probe_last_zero_cap.py`
`fbea5264de2ecdd1a8a7b65737e92404087eb36c`.
Upstream (md5, installed strawberry-graphql 0.324.0):
`strawberry/relay/utils.py` `fe475e0f28c8474be52cb200f72d0c08`,
`strawberry/relay/types.py` `e9ccbd9baf2d9bf1eaf16f9419df66f7`.

## Findings

### High

#### H1: offset `last: 0` serves the whole table past the `relay_max_results` / `max_page_size` page cap

- **Observation (Defect)** — The offset branch of
  `django_strawberry_framework/connection.py::_consume_fallback`
  delegates `last: 0` (no `before:`) to Strawberry's
  `ListConnection` unbounded: the upstream slice engine resolves
  `end = sys.maxsize` for a `last`-only shape, materializes
  `nodes[start:maxsize]`, and takes `edges[-0:]` (the whole list),
  with the `max_results` bound check passing `0 <= cap` without
  constraining the served page. The package clamps `max_results`
  through the `max_page_size` ceiling in
  `django_strawberry_framework/connection.py::DjangoConnection.resolve_connection`
  and then hands the clamped value to an engine that ignores it
  for this shape — so `last: 0`, and `last: 0` + `after:`, serve
  every visible row. The keyset slicer in the same module caps
  the identical quirk at the resolved cap. Both queryset and
  non-queryset (list) sources escape: the branch serves both and
  the trim happens in neither.
- **Evidence** — HUNT evidence record. Workspace run
  `review-20260929T004349-77be15` (address
  `review/connection.py/mechanics`, cell default, copy slot-3,
  package digest `sha256:4e7fd52...`, exit 0, 10 assertions),
  command `uv run python scripts/workspace.py run
  review/connection.py/mechanics -- python
  docs/review/temp-tests/connection/mechanics/probe_last_zero_cap.py`.
  Reach: through-schema real queries against
  `examples/fakeshop/config/schema.py` (`allCategories` root
  offset connection, 132 rows / 120 public, default cap 100).
  Positive control: `first: 101` is rejected with `Argument
  'first' cannot be higher than 100.` (the cap binds ordinary
  pages). Figures: `last: 0` serves 120 edges; `last: 0` +
  `after:` serves 118; cap 100. Flavor control (committed
  oracles, not re-run): `test_root_keyset_last_zero_preserves_bounded_shipped_connection_semantics`
  (101 rows -> 100 edges) and
  `test_root_keyset_last_zero_with_after_stays_bounded_by_cap`
  (157-row tail -> 100 edges) pin the capped keyset quirk. The
  HEAD..live delta does not touch this path (hunk inspection),
  so the defect ships at HEAD too.
- **Impact** — Any client sends `last: 0` to any offset
  connection (the default flavor) over a table wider than the
  cap and receives every visible row in one page: the
  per-collection bound the resource policy advertises does not
  hold. Visibility is intact (private rows stay excluded —
  120 served of 132), so this is a width/availability failure,
  not a leak; it still materializes an unbounded page per
  request on a hot path with no log or signal.
- **Severity** — High: public-contract failure (the glossary
  bound below) with an availability edge. Aggravating: default
  flavor, trivial wire input, silent. Mitigating: visibility
  intact, degenerate input, under-cap quirk shape is intended
  behavior and stays.
- **Recommendation** — Owner:
  `django_strawberry_framework/connection.py::_consume_fallback`
  (the single offset-delegation tail; the resource-policy
  extension is setup-only per its anchor, and collection bounds
  are the fields' job). Bound the served offset `last: 0` page
  at the already-resolved `max_results`, mirroring the keyset
  quirk handling: serve at most the cap, keep
  `hasPreviousPage` False per the quirk, flip `hasNextPage`
  True when the trim drops rows (the keyset oracles specify
  exactly this shape, incl. the `after:` tail). Cover queryset
  AND non-queryset sources — a 200-item list escapes
  identically. Considered and rejected: carving the quirk out
  of the policy claim instead (upstream-parity rationale).
  Rejected because the glossary, the keyset oracles' `must
  never` wording, and the clamp comment all state the bound
  absolutely, and every pinned serve-all oracle uses an
  under-cap fixture, so capping breaks no oracle. Trigger to
  revisit: a maintainer decision that upstream parity beats
  the bound — which must then carve consistently across the
  glossary sentence, the clamp comment, and the keyset
  oracles.
- **Must not change** — The under-cap quirk shape: every
  pinned serve-all oracle keeps passing unchanged (fixtures
  below the cap); `hasPreviousPage` False for `last: 0`;
  cursors and edges bytes for under-cap pages; the `first` /
  `last` bound-error vocabulary; keyset slicing bytes; window
  planning (`last: 0` stays unplanned).
- **Proof** — At `review/connection.py/verify-mechanics-<n>`:
  (1) new live test `test_offset_last_zero_stays_bounded_by_relay_cap`
  in examples/fakeshop/test_query/test_keyset_api.py (beside
  the keyset `last: 0` cap twins; >100 visible rows; asserts
  `last: 0` serves exactly 100 with `hasPreviousPage` False +
  `hasNextPage` True, and `last: 0` + `after:` likewise) —
  plain-text name, Worker-2 creates it: run that node with
  `uv run python scripts/workspace.py run review/connection.py/verify-mechanics-<n> -- pytest` plus `--no-cov`;
  must report `1 passed`. (2) under-cap serve-all pins
  unaffected: `uv run python scripts/workspace.py run review/connection.py/verify-mechanics-<n> -- pytest tests/test_relay_connection.py::test_fast_path_last_zero_quirk_parity_via_fallback examples/fakeshop/test_query/test_library_api.py::test_nested_connection_last_zero_serves_quirk_via_per_parent_fallback --no-cov`
  must report `2 passed`. (3) keyset path untouched: `uv run python scripts/workspace.py run review/connection.py/verify-mechanics-<n> -- pytest examples/fakeshop/test_query/test_keyset_api.py::test_root_keyset_last_zero_preserves_bounded_shipped_connection_semantics examples/fakeshop/test_query/test_keyset_api.py::test_root_keyset_last_zero_with_after_matches_offset_pageinfo examples/fakeshop/test_query/test_keyset_api.py::test_root_keyset_last_zero_with_after_stays_bounded_by_cap examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_last_zero_with_after_matches_root_pageinfo --no-cov`
  must report `4 passed`. Failability: reverting the
  production hunk must fail exactly command (1)'s row;
  commands (2)–(3) pass before and after (compatibility set).
- **Freshness** — Trace fingerprints cover every cited file.
- **Owner + contract source** — Owner:
  `django_strawberry_framework/connection.py::_consume_fallback`.
  Contract sources: GLOSSARY `ResourcePolicy` anchor (`the rows
  a request can return are bounded per collection by
  max_page_size`) + execution-resource-policy anchor
  (`COLLECTION bounds the fields enforce`); the clamp comment
  in
  `django_strawberry_framework/connection.py::DjangoConnection.resolve_connection`
  (`stops a client from asking ... for a page wider than the
  policy`); the live keyset cap oracles named above (`must
  never let after widen the page past the Relay cap`).

#### V1 (verify 1): the H1 async trim wrapper awaits itself, breaking every async `last: 0` page

- **Observation (Defect)** — Pass 1's `_consume_fallback` async arm
  defines `_trim_async` closing over `conn` and then reassigns `conn`
  to the wrapper itself. Python closures capture the variable, so
  `resolved = await conn` inside the wrapper awaits the wrapper
  coroutine while it is running, raising `ValueError: coroutine
  already executing` (surfaced as `GraphQLError('coroutine already
  executing')`). Every async offset `last: 0` query errors instead of
  serving. Sync is unaffected.
- **Evidence** — Attack run `review-20260929T014540-6b9353`
  (address `review/connection.py/verify-mechanics-1`): the pre-existing
  async under-cap oracle
  `tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`
  fails with `GraphQLError('coroutine already executing')` plus an
  unawaited-coroutine teardown error. Control run
  `review-20260929T014509-f582b4` at `review/connection.py/before`
  (unfixed code): the same node reports `1 passed`. The regression is
  introduced by pass 1. Worker-2 never ran this node (its report lists
  no async run) despite claiming the wrapper covered.
- **Impact** — Async offset `last: 0` (any cap, any size) is a hard
  error on a hot path. The sync H1 fix is correct; the async arm is
  not.
- **Severity** — High: correctness failure on a shipped async shape,
  introduced by the item.
- **Recommendation** — Owner:
  `django_strawberry_framework/connection.py::_consume_fallback`.
  Capture the untrimmed awaitable before defining the wrapper (a
  separate local or a default-arg bind), so the wrapper awaits the
  upstream coroutine, not itself. No signature or helper change.
- **Must not change** — The sync trim bytes; the helper contract;
  every H1 Proof row (1+2+4) stays green.
- **Proof** — At `review/connection.py/verify-mechanics-<n>`:
  `uv run python scripts/workspace.py run review/connection.py/verify-mechanics-<n> -- pytest tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo --no-cov`
  must report `1 passed` (today `1 failed, 1 error`).
- **Freshness** — `django_strawberry_framework/connection.py`
  `c8b9670109d05f9a09f2f8a113e491baa7511317`;
  `tests/test_relay_connection.py`
  `fe2b2d24ab6e71e6238183690b02821abb239497`.
- **Owner + contract source** — Owner:
  `django_strawberry_framework/connection.py::_consume_fallback`.
  Contract sources: the pre-existing async oracle named above (fails
  today, passed before pass 1); the H1 Must-not-change (under-cap
  quirk shape preserved on every color).

### Medium

None.

### Low

None in-Mechanics (C1 rides as Cross-axis for Comments).

## Rejected

### R1: three order-path field resolvers are not one rule twice

`django_strawberry_framework/connection.py::_resolve_order_path_field`
(`__` traversal, `None` on failure, rejects nullable /
reverse / multi-valued intermediates and non-concrete
terminals),
`django_strawberry_framework/keyset.py::_resolve_cursor_field_column`
(single segment, raises, declaration-time), and
`django_strawberry_framework/list_field.py::_resolve_order_field_path`
(`LOOKUP_SEP` traversal, `(field, opts)` or `None`, reverse
relations allowed for compiler-following certification) share
only the one-line `pk`-alias clause, which restates Django's
own lookup convention, not a package rule. DRY change
challenge: posit `change the pk alias` — the clause is
Django-mirrored convergent text, not an authoritative
definition. Posit `change the traversal nullability rule` —
exactly one definition (connection's; the others have no such
rule). Posit `change reverse-relation handling` — exactly one
(list's). Every package-rule count is 1; the contracts
(cursor-anchoring vs determinism-certification vs
declaration-resolution) give separate reasons to change.
Trigger: a shared traversal semantic, or a fourth resolver.

### R2: the negative-cursor guard mirrors but does not duplicate the window verdict

`django_strawberry_framework/connection.py::_reject_negative_offset_cursor`
(vs-HEAD-new concurrent hunk) pre-classifies a forged negative
offset cursor before the offset fallback delegates to
`ListConnection`, while
`django_strawberry_framework/utils/connections.py::derive_connection_window_bounds`
reads negativity off the engine's `SliceMetadata.start/end`.
The detection mechanisms differ by necessity (the fallback
cannot run the engine for validation: it would mis-spin
`UnwindowableConnection` shapes `ListConnection` serves, and
a re-sliceable list would wrap silently without the
pre-check); only the message literal mirrors, deliberately
(`SliceMetadata` wording, so every cursor-vocabulary
rejection reads alike). Posit `change which cursors count as
negative` — the verdicts are mechanism-distinct by path, not
two spellings of one rule. Trigger: a verdict divergence
between the paths, or a third spelling.

### R3: the keyset count-only page does not duplicate the empty-page helper

`django_strawberry_framework/connection.py::_empty_page_connection`
serves real empty pages with pipeline-parity flag arithmetic
(`offset > 0`, `total > offset`); the count-only branch of
`django_strawberry_framework/connection.py::_resolve_keyset_connection`
serves an inert placeholder (`False`/`False`, nothing under
`edges`/`pageInfo` selected) with a sync/async color fork the
helper cannot express (its `value` slot takes a sync lazy,
not an awaitable). DRY change challenge: posit `change the
empty-page parity arithmetic` — one definition (the helper).
Posit `change the inert placeholder` — one definition (the
branch). Shared bytes are Relay's empty shape, not a package
rule. Trigger: a second inert-placeholder site, or the helper
growing a placeholder mode.

### R4: the relation resolver has no async branch (specified, fail-loud)

`django_strawberry_framework/connection.py::_build_relation_connection_resolver`
runs `_pipeline_sync` only, while root connections commit an
async branch per construction. Rejected, not filed: the
docstring explicitly scopes async out (`Async-get_queryset
posture (0.0.9)`), an async hook fails loud via the inherited
`SyncMisuseError` rather than silently, and the recourse
(`relation_shapes = {"<field>": "list"}`) is documented. No
contract source promises async relation connections.
Trigger: an async connection pipeline landing, or a contract
promising async relation connections.

### R5: no per-field page cap on connections (no contract)

`DjangoListField` takes per-field `max_rows` /
`trusted_max_rows`; `DjangoConnectionField` takes no
per-field cap (schema `relay_max_results` default + the
`max_page_size` ceiling apply). No contract source — glossary,
README, or oracle — promises a per-field connection cap, so
the list/conection asymmetry is a specified surface
difference, not a missing guard. Trigger: a contract
promising per-field connection caps.

## Cross-axis (for Comments)

### C1 (Low): in-function `FieldDoesNotExist` import cites an idiom with a single member

- **Observation** —
  `django_strawberry_framework/connection.py::_resolve_order_path_field`
  imports `FieldDoesNotExist` in-function with the comment `In-function
  import mirrors the file's defensive-Django-imports idiom.` The
  idiom has no other member: it is the only in-function Django
  import in the file (the filters/orders in-function imports
  serve the documented lazy-subpackage contract, a different
  idiom), the file already imports `django.db.models` at top
  level so the deferral saves nothing, and the identical import
  sits at top level in `django_strawberry_framework/keyset.py`
  and `django_strawberry_framework/list_field.py`, proving
  top-level placement cycle-safe.
- **Evidence** — Static: `grep -rn
  defensive-Django-imports django_strawberry_framework/` prints
  only the one line; `grep -n ^from\|^import
  django_strawberry_framework/connection.py` shows
  `django.db.models` at top; the keyset/list top-level
  `FieldDoesNotExist` imports at the fingerprinted blobs.
- **Impact** — A reader is told to copy a pattern whose stated
  reason is false (wrong stated reason), and the import
  statement re-executes per effective-order entry on the
  keyset-`orderBy` path. Bounded.
- **Severity** — Low: bounded clarity/maintainability; no
  behavioral consequence either way.
- **Recommendation** — Hoist to top level (`from
  django.core.exceptions import FieldDoesNotExist` in the
  Django import group; Worker-2 owns ruff order) and delete
  the false sentence with the line it sits on. Fallback if
  the hoist is disputed: delete the sentence alone.
- **Must not change** — Resolution behavior, incl. every
  `test_resolve_order_path_field_*` arm.
- **Proof** — Static: `grep -c "^from django.core.exceptions import FieldDoesNotExist" django_strawberry_framework/connection.py`
  must print `1`, and `grep -c "^    from django.core.exceptions import" django_strawberry_framework/connection.py`
  must print `0`. Grade: the landed import carries no comment
  or one grading true (no idiom claim). Behavior: `uv run python scripts/workspace.py run review/connection.py/verify-comments-<n> -- pytest tests/test_keyset_connection.py::test_resolve_order_path_field_arms tests/test_keyset_connection.py::test_resolve_order_path_field_accepts_mti_parent_link --no-cov`
  must report `2 passed`.
- **Freshness** — Trace fingerprints cover every cited file.
- **Owner + contract source** — Owner:
  `django_strawberry_framework/connection.py`. Contract
  sources: the top-level precedent in
  `django_strawberry_framework/keyset.py` +
  `django_strawberry_framework/list_field.py` (fix shape) and
  the file's own top-level `django.db` import (falsifies any
  laziness benefit).

Handoff: Beyond the record's trace I read the upstream slice
engine whole (both sync/async `ListConnection` branches),
the seal-policy definitions and their `reject_sliced` /
`reject_combined` matrix, the resource-policy extension at
grep level (setup-only confirmed; no post-hoc edge counting
exists, which is what makes H1 a field-side gap), and the
list flavor's pipelines, signatures, and rejection builders
for the twin/guard comparisons — all discharged above, none
filed. The module is already heavily consolidated (shared
predicates for bounds, caps, sidecar detection, selection
walks, order derivation, edge-class resolution, async
refusals, visibility policies); H1 is a bound the sharing
missed, not a pattern of forking. Two observations I did not
promote: (a) list-field scalar sources route through
`normalized_row_source`, whose verdict I did not verify —
an observation for the future `list_field` reviewer, not a
routed defect (no contract source found requiring a named
rejection there); (b) per-call definition/selection walks
(`_window_edge_class`, the `want_count`/`hasNextPage`
predicates) and the C1 import cost are Performance-territory
numbers I leave to that axis. Open threads: H1's fix must
cover non-queryset sources too (same branch, same escape);
C1 rides with Comments; sharded/pg cells were not run
(inapplicable-by-construction claimed for H1's path only —
verifier judges).

## Verification (Mechanics)

Item diff hash: `git diff e6b022ba44f4e14da9e1825cea7047aa38d03298 --
django_strawberry_framework/connection.py tests/test_relay_connection.py
examples/fakeshop/test_query/test_keyset_api.py` is byte-equal to
`docs/review/temp-tests/connection/diff/pass-1.diff`
(sha256 `ef54683033035551709fa8a005924e2440c1232d72705e96eb8049db53a837eb`,
429 lines each). The tree carries the change sent to grade.

Reading-order note: the hash check above ran before any artifact read,
but the `## Implementation (Worker-2)` section was read before the
Proof runs below (Worker-1 Verify step 1 orders Proofs first). The
Proofs still ran verbatim at the verify address and their results are
recorded as observed, so the slip costs order, not evidence.

Proofs (all at `review/connection.py/verify-mechanics-1` unless noted):

- H1 (1) new live test:
  `uv run python scripts/workspace.py run review/connection.py/verify-mechanics-1 -- pytest examples/fakeshop/test_query/test_keyset_api.py::test_offset_last_zero_stays_bounded_by_relay_cap --no-cov`
  → `1 passed` (`review-20260929T013848-ddddd5`, exit 0).
- H1 (2) under-cap serve-all pins:
  `... -- pytest tests/test_relay_connection.py::test_fast_path_last_zero_quirk_parity_via_fallback examples/fakeshop/test_query/test_library_api.py::test_nested_connection_last_zero_serves_quirk_via_per_parent_fallback --no-cov`
  → `2 passed` (`review-20260929T014005-4f326a`, exit 0).
- H1 (3) keyset path untouched (4 nodes):
  `... -- pytest examples/fakeshop/test_query/test_keyset_api.py::test_root_keyset_last_zero_preserves_bounded_shipped_connection_semantics examples/fakeshop/test_query/test_keyset_api.py::test_root_keyset_last_zero_with_after_matches_offset_pageinfo examples/fakeshop/test_query/test_keyset_api.py::test_root_keyset_last_zero_with_after_stays_bounded_by_cap examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_last_zero_with_after_matches_root_pageinfo --no-cov`
  → `4 passed` (`review-20260929T014036-c65bf4`, exit 0).
- Cross-axis for Mechanics (Comments hoist), static in the shared tree:
  `grep -c "from django.core.exceptions import FieldDoesNotExist"
  django_strawberry_framework/connection.py` prints `1` at top level
  (line 53); nested `grep -c "^    from django.core.exceptions import"`
  prints `0`; `uv run python scripts/build_tree_md.py --list-docstrings
  django_strawberry_framework/connection.py` prints `ok` (1 module,
  0 breaking). Pass.

Worker-2 numbers reproduced: the H1 live `1 passed` and compat
`2 passed` + `4 passed` above match the report's shared-tree figures;
the C1 behavior pair
  `tests/test_keyset_connection.py::test_resolve_order_path_field_arms`
  + `::test_resolve_order_path_field_accepts_mti_parent_link`
  reports `2 passed` at the verify address
  (`review-20260929T014440-b5691e`, the C1 half of a 3-node run whose
  third node is the V1 attack below). No timing number is owed on this
  axis.

Fix at the owner: confirmed. `_consume_fallback` detects
`is_backward_shape(first, last) and last == 0 and not is_supplied(before)`
and bounds the served page via the new `_cap_offset_last_zero_page`
(at most `cap` edges, `hasPreviousPage` False, `hasNextPage` True on
trim, cursors re-anchored). The quirk predicate mirrors the keyset
definition; the trim sits after `super().resolve_connection` outside
the queryset guard, so queryset and non-queryset sources share it.

Must-not-change oracles: the H1 Proof compat set (2+4) is green, but
the async under-cap oracle is red (V1 below), so the Must-not-change
claim does not hold on every color.

Failability (`workspace.py prove` at the verify address):
`docs/review/temp-tests/connection/verify-mechanics-1/prove-h1.json`
(anchor `if len(conn.edges) > cap:` → `if False:`, scope the 7 H1
rows) → `review-20260929T014212-f6a435` exit 0: baseline `7 passed`,
mutant `1 failed, 6 passed`, exactly
`test_offset_last_zero_stays_bounded_by_relay_cap` fails (crash
`assert 200 == 100`), restore byte-proved. Pass.

Live tier: confirmed. The new test lives in
`examples/fakeshop/test_query/test_keyset_api.py`, first line
`seed_data(30)`, and serves real `allItems(last: 0)` pages through
`graphql_client.assert_graphql_success` (live HTTP). Strongest
reachable tier; no fixture gap.

Open thread judged: Worker-2 discloses the async over-cap trim as
covered-by-line but exercised over-cap only via sync. That disclosure
assumes the async wrapper works. It does not (V1): the wrapper awaits
itself, so async `last: 0` errors at any size. The thread is
superseded by V1; after the closure fix, the residual combination
(async + over-cap) remains line-covered via the shared helper plus the
sync over-cap pin, which is acceptable without a dedicated async
over-cap row (the helper is pure and color-free, and the H1 Proof
governs sync).

Whole-diff reading (Mechanics): the Performance hunks preserve
observable behavior. F1 memoizes `_window_edge_class` per class with a
`registry.clear()`-wired clear; derivation byte-identical. F2 moves
the relation source build after the window check but before `_check_n1`
(non-window error precedence preserved); the windowed path with a
missing accessor no longer raises, but the accessor derives from
`field.name` and always exists in production, so no real behavior
changes. F3 reorders a pure conjunction (flags before the selection
walk); truth table identical. No symbol was renamed or moved (only new
helpers plus the single-caller `_build_windowed_fallback` signature
change), so no `--cited-by` sweep is owed beyond the caller census
(one production caller, updated). Comments prose moves no behavior.

Attacks: the async under-cap oracle
`test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`
fails with the fix (`review-20260929T014540-6b9353`: `1 failed,
1 error`, `GraphQLError('coroutine already executing')`) and passes
without it (`review-20260929T014509-f582b4` at
`review/connection.py/before`: `1 passed`). Filed as V1 above; no
other attack was run once the regression was established.

Disputes: none recorded in `## Implementation (Worker-2)`; nothing to
judge.

Lint gates (`--check` forms only): `ruff check` on the three touched
paths passes; `ruff format --check` passes (3 files formatted);
`check_trailing_commas.py --check` passes (0 violations);
`check_citations.py --check` passes tree-wide (1297 resolve). All
green; the defect is behavioral, not stylistic.

Cells: default run for every Proof and attack above. Sharded and pg
remain `inapplicable by construction` for H1's path (no alias or
dialect decision on the offset `last: 0` delegation; concur with the
record) and were not run. No cell left unverified beyond that claim.

Verdict: `revision-needed`. One concrete gap: V1 (the async closure
bug; Proof: the existing async node must report `1 passed`). The H1
sync fix, its live test, its failability, the hoist, and all lint
gates are verified and stand; the re-pass owes only the closure fix
plus a re-run of this record's Proofs and the V1 Proof.

Handoff: The V1 regression is narrow (async `last: 0` only) with a
one-line fix shape (bind the untrimmed awaitable before the wrapper).
The re-pass verifier needs no new scratch beyond re-running the five
Proof lines above plus the V1 Proof at `verify-mechanics-2`; the
`prove-h1.json` manifest under `verify-mechanics-1/` can be reused by
copy. Watch for a second closure of the same shape if the re-pass
restructures the arm, and confirm the full async connection suite
(`-k async` over `tests/test_relay_connection.py`) stays green, since
Worker-2's focused scope never included it.

## Verification (Mechanics) pass 2

Item diff hash: `git diff e6b022ba44f4e14da9e1825cea7047aa38d03298 --
django_strawberry_framework/connection.py tests/test_relay_connection.py
examples/fakeshop/test_query/test_keyset_api.py` is byte-equal to
`docs/review/temp-tests/connection/diff/pass-2.diff`
(sha256 `158ed7f4088a63a3c9ba88715298b9c583b8619f3efbbf77e984c65d915fc53f`,
20724 bytes, 430 lines each). The tree carries the change sent to grade.

Reading-order note: the hash check above ran before any artifact read,
but the `## Implementation (Worker-2)` pass-2 section was read before
the Proof runs below (the dispatch's required-reading order places the
artifact first). The Proofs still ran verbatim at the verify address
and their results are recorded as observed, so the slip costs order,
not evidence.

Pass-2 delta (diff of `pass-1.diff` vs `pass-2.diff`): code-only, one
added line (`untrimmed = conn`) plus one changed line (`resolved =
await conn` -> `resolved = await untrimmed`) inside
`_consume_fallback`'s async arm; the remaining diff lines are the blob
index and hunk-header offsets. No prose line and no test-file hunk
differs between the passes. Test-file fingerprints equal the pass-1
after-values (`tests/test_relay_connection.py`
`fe2b2d24ab6e71e6238183690b02821abb239497`,
`test_keyset_api.py` `88a432b0858c54afc91a79cedbf8938983ab2c23`);
`connection.py` is `1fca6266cd5f748915875badf1881680b599de37`.
Performance and Comments pass-1 verdicts (verified) stand untouched.

Sync trim bytes and helper contract: unchanged. The sync line
(`conn = _cap_offset_last_zero_page(conn, cap)`) and the whole
`_cap_offset_last_zero_page` body are context-identical in both pass
diffs; the V1 Must-not-change holds.

Proofs (all at `review/connection.py/verify-mechanics-2`, cell
default, copy slot-2, package digest `sha256:d2021bf2...`; run log
under `docs/review/temp-tests/connection/verify-mechanics-2/runs.txt`):

- V1 Proof:
  `uv run python scripts/workspace.py run review/connection.py/verify-mechanics-2 -- pytest tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo --no-cov`
  -> `1 passed` (`review-20260929T021200-df5bd5`, exit 0, fresh copy).
- Performance verifier's second async node:
  `... -- pytest tests/test_relay_connection.py::test_consume_window_unservable_window_runs_the_async_fallback --no-cov`
  -> `1 passed` (`review-20260929T021236-6c993e`, exit 0).
- H1 (1) live:
  `... -- pytest examples/fakeshop/test_query/test_keyset_api.py::test_offset_last_zero_stays_bounded_by_relay_cap --no-cov`
  -> `1 passed` (`review-20260929T021301-403e64`, exit 0).
- H1 (2) under-cap serve-all pins (2 nodes)
  -> `2 passed` (`review-20260929T021329-7aa359`, exit 0).
- H1 (3) keyset path untouched (4 nodes)
  -> `4 passed` (`review-20260929T021400-f228df`, exit 0).

Every H1 Proof row from pass 1 is green again on the pass-2 tree, and
both async oracles that failed under the bug now pass.

Whole-delta reading (Mechanics): the bind is the recommended fix at
the owner (`_consume_fallback`). `untrimmed` captures the upstream
awaitable before `_trim_async` is defined, so the wrapper awaits the
upstream coroutine instead of itself; the rebinding of `conn` to the
wrapper call no longer aliases anything the closure reads. No signature
changed, no helper changed, no caller changed, no symbol renamed or
moved, so no `--cited-by` sweep is owed and no other axis's line moves.

Attacks:

- Second closure of the same shape: swept all 5 `async def` sites in
  `connection.py` (shared tree, static). `_resolve_count_only_async`
  and `_resolve_async` are returned directly without rebinding any
  closed-over name; `_attach_count_async`, `_pipeline_async` and the
  async `_resolve` are parameter-driven with no closure rebinding.
  Only `_trim_async` ever had the shape. No sibling defect. PASS.
- Full async scope:
  `... -- pytest tests/test_relay_connection.py -k async --no-cov`
  -> `2 passed` (`review-20260929T021554-fdeff2`, exit 0): the
  selection is exactly the two oracles above, both green. PASS.
- Revert-in-copy (pre-fix was worse): hand-reverted the pass-2 hunk
  inside the verify copy only (deleted the `untrimmed` bind, restored
  `resolved = await conn`), then ran the V1 node with
  `-o log_cli=true --log-cli-level=ERROR` ->
  `1 failed, 1 error` (`review-20260929T021650-90ac88`, exit 1) with
  `ValueError: coroutine already executing` at `_trim_async`
  (`connection.py:839`), matching V1's Evidence exactly. The copy was
  restored to the fixed bytes afterwards (grep-verified). The fix is
  what makes the oracles pass. PASS.

Disputes: none recorded in `## Implementation (Worker-2)` pass 2
(the only `disput*` hits are its "nothing disputed" lines); nothing
to judge.

Lint gates (`--check` forms only): `ruff check` on the three item
paths passes (All checks passed); `ruff format --check` passes (3
files already formatted); `check_trailing_commas.py --check` passes
(0 violations); `check_citations.py --check` passes tree-wide (1297
resolve). All green.

Cells: default run for every Proof and attack above. Sharded and pg
remain `inapplicable by construction` for this path (a pure-Python
closure bind on an already-fetched awaitable: no alias, `using`,
dialect or vendor token; concur with the record) and were not run.
No cell left unverified beyond that claim.

No new finding. No `verify 2` label owed.

Verdict: `verified`. V1 is fixed at the owner by the recommended bind;
every pass-1 Proof (H1 rows 1+2+4) re-runs green; the async arm
withstands the closure sweep, the full `-k async` scope, and the
revert demonstration; all lint gates pass.

Handoff: Mechanics on this item is closed: H1 sync fix plus V1 closure
fix, both pinned by pre-existing or live oracles, all proofs green at
`verify-mechanics-2` with run ids in `runs.txt` beside this record.
The verify copy (slot-2) was hand-reverted mid-pass for the
demonstration run and then restored to the fixed bytes, so its current
content equals the shared tree; Worker-0 should still treat the
`021650-90ac88` log as the modified-copy run it is. No thread is left
open for a further Mechanics pass.

