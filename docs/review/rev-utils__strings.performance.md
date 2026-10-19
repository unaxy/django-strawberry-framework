# Review · Performance: `django_strawberry_framework/utils/strings.py`

Status: verified
Run: 0.0.15 2026-09-28-3

## Trace

Target read whole at blob `3ec3b262`. Release change (`git diff 0.0.14..HEAD`, commit a8f31a2d):
`pascal_case` now preserves leading/trailing underscore runs (two slices + an f-string); every
other symbol unchanged this release, all reviewed as they stand.

Callers (`rg` over `django_strawberry_framework/`, 30 call sites), classified by what runs them:

- Hot (per request on a plan-cache miss, and on every request for a non-cacheable plan):
  `snake_case` from `django_strawberry_framework/optimizer/walker.py::_resolve_selection_target`,
  `django_strawberry_framework/optimizer/walker.py::_walk_selections` (unresolved fallback) and
  `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names`, one call per
  selection. `flatten_lookup_path` from
  `django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions`, one call per
  to-many order entry per request, beside `classify_path` + an aggregate build that dwarf it.
- Hot but memoized upstream: `flatten_lookup_path` via
  `django_strawberry_framework/utils/permissions.py::_check_method_name` (`lru_cache(2048)`),
  so it runs once per declared path per process.
- Cold (declaration / finalize / schema build / management command): every `pascal_case`,
  `pascal_case_or_raise`, `graphql_camel_name` caller (`types/converters.py`, `mutations/inputs.py`,
  `forms/inputs.py`, `rest_framework/*`, `utils/inputs.py`, `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`,
  `filters/inputs.py::_pascal_case`), and the `snake_case` callers in `types/base.py`,
  `types/finalizer.py`, `management/commands/inspect_django_type.py`.

Measurements, all in copy `review/utils/strings.py/performance`, package digest
`sha256:df761b82...9f3130` = the `## Bench baseline` digest:

- `review-20260925T033654-ee614b`: `python probe_snake_case.py <root>/performance/probe_snake_case.json`
  (probe source `<root>/performance/probe_snake_case.py`, copied into the copy root; captures the
  four `bench_optimizer_walk.py` candidates through its own `_capture_walk_inputs`). `snake_case`
  calls per walk: glossary scalar 4, nested 11, deep 39, products connection 2. Schema-wide
  GraphQL field-name vocabulary 708 vs `lru_cache` maxsize 2048. Warm per-call ns (loop baseline
  19.9): `snake_case` 70.9, `_snake_case_cached` direct 26.0. `flatten_lookup_path("category__name")`
  119 ns.
- `review-20260925T033740-60a264`: `python probe_plain_text.py <root>/performance/probe_plain_text.json`
  (source `<root>/performance/probe_plain_text.py`), timeit median of 9 repeats, 300k calls,
  loop baseline 22.8 ns: see finding L1.
- `review-20260925T033834-757fb7`: `python scripts/importtime_report.py --rounds 5 --top 80 --json
  <root>/performance/importtime.json`: `django_strawberry_framework.utils.strings` self 83 us,
  cumulative 83 us, of package cumulative 196.5 ms.
- `review-20260925T033849-1e6564`: `snake_case.__doc__` at runtime (Cross-axis, below).

Cells: default, sharded, pg all `inapplicable by construction`: the module opens no connection,
reads no alias, makes no dialect decision and imports no ORM symbol; its inputs are Python
strings.

Fingerprints (`git hash-object`): `django_strawberry_framework/utils/strings.py` 3ec3b262ea8666d4ba36cf83807ca377fee5a680;
`optimizer/walker.py` 611e8fae4985321c24f09ab4891e23079f7e1b18; `orders/sets.py`
6044ab1a11c77a42b715f0d0722fe7c9695064bc; `utils/permissions.py` 9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec;
`utils/__init__.py` 1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee; `utils/inputs.py`
ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0; `sets_mixins.py` ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3;
`filters/inputs.py` 82b52d97b8f8b26d2846df24dabcabb793507c87; `exceptions.py`
e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b; `tests/utils/test_strings.py`
3dad1a9d42d88a061546f5ee11a37ca453436c4e; `scripts/bench_optimizer_walk.py`
de745175799b1d8c0efa5c75cd296f9dd6910e34; `scripts/importtime_report.py`
bfce84b9c167ca9720f8e4f839cae45fd3702f6c.

## Findings

### High

None.

### Medium

None.

### Low

#### L1: `_plain_text` tests the rare case before the common one

- **Observation** — `django_strawberry_framework/utils/strings.py::_plain_text` runs
  `isinstance(value, str)` before `type(value) is str`, so every exact-`str` call (every call the
  walker makes: `sel.name` comes from graphql-core's AST) pays the `isinstance` builtin call
  before the identity test that returns it. All five public helpers enter through it.
- **Evidence** — `review-20260925T033740-60a264`, warm, same names: `_plain_text` shipped 38.7 ns
  vs exact-`str`-first 30.1 ns (net of loop 15.9 vs 7.3); `snake_case` 70.6 vs 63.6 ns. Parity
  asserted in the probe on `str`, a `str` subclass, and `None` / `3` / `b"x"` (same return type,
  same `ConfigurationError`).
- **Impact** — Path class hot: the walker calls `snake_case` once per selection on every plan
  build (plan-cache miss, every non-cacheable request); 39 calls on the deep glossary shape, so
  about 0.3 us of the 154.33 us `bench_optimizer_walk.py` glossary-deep median (baseline
  `review-20260925T033406-a529d7`). Below that bench's spread: it cannot resolve the move, and no
  query count exists to pin.
- **Severity** — Low: bounded hot-path saving under 1% of the walk, invisible end to end.
- **Recommendation** — at the owner, reorder to `if type(value) is str: return value`, then the
  `isinstance` rejection, then `return str.__str__(value)`. Same three branches, no new code.
- **Must not change** — non-`str` input raises `ConfigurationError` with "must be a string"; a
  `str` subclass (including one whose `__str__`, `__hash__`, `split`, `replace` raise) is
  normalized through `str.__str__` to an exact `str` before any method or cache lookup; exact
  `str` returned unchanged.
- **Proof** — at `review/utils/strings.py/verify-performance-<n>`: copy
  `<root>/performance/probe_plain_text.py` into the copy root, run
  `workspace.py run <address> -- python probe_plain_text.py <root>/verify-performance-<n>/probe_plain_text.json`;
  landed = `parity: ok` and (`plain_text shipped` - `plain_text reordered`) <= 2.0 ns (before:
  8.6 ns); and `workspace.py run <address> -- pytest tests/utils/test_strings.py --no-cov`
  passes (`test_string_helpers_normalize_hostile_string_subclasses`,
  `test_string_helpers_reject_non_string_inputs` pin the Must-not-change rows). Bench figure:
  none moves measurably; this is the micro-benchmark claim only.
- **Freshness** — `utils/strings.py` 3ec3b262; `exceptions.py` e06b0b7f; `tests/utils/test_strings.py` 3dad1a9d.

## Rejected

- **Inline exact-`str` fast path in `snake_case`** (bypassing the `_plain_text` frame: 48.2 vs
  70.9 ns per call, `review-20260925T033654-ee614b`; walk replay interleaved 7 x 5000, deep 155.1
  vs 150.5 us, nested 85.2 vs 85.0 us, within run spread). Rejected: it respells the
  normalization guard at a second site for a sub-1% walk saving; plainness wins. Reopens if a
  measured walk shows `snake_case` above 2% of `bench_optimizer_walk.py` time (a schema whose
  non-cacheable operations select thousands of fields per request).
- **`lru_cache(maxsize=2048)` sizing** on `django_strawberry_framework/utils/strings.py::_snake_case_cached`.
  Walker inputs are validated GraphQL field names, so the key set is bounded by the schema
  vocabulary (708 in fakeshop, 2.9x headroom); cache hits after warm-up. Reopens if a supported
  schema exceeds 2048 distinct field names, where a cyclic walk order would thrash LRU; the fix
  then is sizing from the schema, not `maxsize=None`.
- **Char-by-char rebuild in `_snake_case_cached`** (list append per character): runs once per
  distinct name per process behind the cache; cold.
- **`camel +=` string building in `graphql_camel_name`; slices and join in `pascal_case`** (incl.
  this release's leading/trailing slices): cold, every caller is declaration or finalize time;
  plainness wins.
- **`while "__" in flattened: replace` in `flatten_lookup_path`**: 119 ns per call, one call per
  to-many order entry per request next to path classification and an aggregate; the permission
  mangle is memoized upstream. A regex would be slower and less plain.

Looks-for discharged, `none`: N+1 / per-row queries, `len(qs)` / `bool(qs)`, `only()` /
`defer()`, unbatched writes, `blog.id` vs `blog_id` (no ORM use); repeated `_meta` walks,
settings reads, regex compilation, schema or type lookups (none in the module); `lru_cache` on
methods / B019 (the one cache decorates a module function); locks, cache reads, re-parses, round
trips on a per-request path (only the `lru_cache` lookup, the intended memo); import-time cost
(83 us self, stdlib-only imports plus `exceptions`, no settings read at import); allocation in the
walk (cached path allocates nothing; only L1's call-order cost remains).

## Cross-axis

None placed here by other reviewers at close.

Out-of-axis lead for Comments, routed through Worker-0 because `rev-utils__strings.comments.md`
did not exist when this pass closed (creating it would race its owner):
`django_strawberry_framework/utils/strings.py::snake_case` carries a literal docstring
("Normalize ``name`` before consulting the bounded conversion cache.") that never exists at
runtime: `functools.wraps(..., assigned=(..., "__doc__", ...))` replaces it with
`_snake_case_cached.__doc__` at import (`review-20260925T033849-1e6564` prints the cached
function's first line). Dead text on a public symbol; Comments owns the grade.

Handoff: Read beyond the trace: `scripts/bench_optimizer_walk.py` capture path (reused in the
probe), `tests/utils/test_strings.py` whole. The only hot entry into this module is the walker's
per-selection `snake_case`; everything else is build time or memoized, so the module has no
query or bench-visible cost. L1 is a micro saving the bench cannot resolve; if Worker-2 lands no
other change in `strings.py` it is a deferred Low by REVIEW "Severity". The verifier should
check the reordered `_plain_text` still reaches `str.__str__` for subclasses (the hostile
subclass test covers it). The `snake_case` duplicate call in `_walk_selections`' fallback branch
(after `_resolve_selection_target` already reversed the same name) is walker-owned, miss-path
only, not this item's edit. Probes and JSON under
`docs/review/temp-tests/utils__strings/performance/`.

## Verification (Performance)

Address `review/utils/strings.py/verify-performance-1`, copy synced from the shared tree at
digest `sha256:a7408aee...c703e8` (= Worker-2's final digest), copy `fresh` at first run; scratch
`docs/review/temp-tests/utils__strings/verify-performance-1/`. Item diff
`docs/review/temp-tests/utils__strings/diff/pass-1.diff` (12 files).

Proof results (run before reading `## Implementation (Worker-2)`):

- L1 probe, `review-20260925T035708-962a32` (`probe_plain_text.py` copied to the copy root,
  JSON `verify-performance-1/probe_plain_text.json`): `plain_text shipped` 30.0 ns vs
  `reordered` 29.4 ns, delta 0.6 ns <= 2.0 bound; `parity: ok`. Landed.
- `pytest tests/utils/test_strings.py --no-cov`, `review-20260925T035715-1c1132`: 41 passed. Landed.

Numbers reproduced:

- Before, read-only at `review/utils/strings.py/before` (probe by absolute path, copy not
  edited), `review-20260925T035730-bad80a`, digest `sha256:df761b82...9f3130` (= `## Bench
  baseline`): shipped 37.5 vs reordered 28.5, delta 9.0 ns (Worker-2 8.4, reviewer 8.6);
  `snake_case` 68.0 vs 62.9. After (above) 0.6 ns, matching Worker-2's 0.6 ns
  (`review-20260925T035407-988276`).
- Worker-2's "44 passed" (`review-20260925T035345-9110fa`) = `test_strings.py` 41 +
  `test_init.py` 3; its scope line confirms. `workspace.py audit docs/review/rev-utils__strings.md`:
  every Worker-2 run id `ok`, package and database inside the copy.

Failability, `workspace.py prove review/utils/strings.py/verify-performance-1
<root>/verify-performance-1/l1.json`, `review-20260925T035811-98e2b4`, exit 0, restore
byte-checked (blob 536d175c before and after):

1. L1 reverted (isinstance rejection first) over `tests/utils/test_strings.py`: behaviour
   preserved, `expect_failing: []` met (41 passed both runs). L1 is timing-only, as recorded.
2. Positive control, `return str.__str__(value)` -> `return value`: exactly
   `test_string_helpers_normalize_hostile_string_subclasses` fails (1 row).
3. Positive control, rejection deleted: exactly the 4 `test_string_helpers_reject_non_string_inputs`
   rows fail.
   So both Must-not-change rows are pinned under the reordered code. Row 2 is one node: a
   pre-existing test's granularity, not a boundary this item adds.

Whole-diff reading (Performance): production changes are L1 (hot, measured above); M1's
`field_map` key change in `types/base.py`, `types/finalizer.py`, `inspect_django_type.py` (cold:
declaration, finalize, management command; it drops one `snake_case` call per field there, a cold
saving nobody needs to measure); `functools.wraps` `assigned` minus `__doc__` (import time, no
per-call effect); docstrings. The walker's code is unchanged; its `field_map` lookups now index
raw names, identical to snake keys for every lowercase Django name (Mechanics'
`review-20260925T033937-78b854`).

Attacks:

- Walk bench, interleaved `before` / verify copy x2, same instrument blob de745175:
  `review-20260925T035834-cc9ba2`, `-035900-77a1f3`, `-035935-3a710b`, `-040002-00b01e`. Plan
  shapes identical on all four candidates (`sr/pf/only/fk/keys` 0/0/4/0/0, 0/5/1/0/5,
  0/6/4/1/10, 0/0/2/0/0). Deep median before 195.35 / 180.83 vs after 213.25 / 169.19 us, nested
  111.21 / 97.29 vs 110.00 / 95.67: the order alternates, run-to-run swing (~15%) exceeds any
  difference on this loaded machine, and every figure sits above the 154.33 us baseline for the
  same reason. No regression is visible; none is expected, since fakeshop's maps are unchanged.
- Mixed-case query shape at a second cardinality: Worker-2's
  `test_mixed_case_relation_selections_plan_through_their_django_names` pins `{1: (1, 2), 3: (1, 2)}`
  (batched, absolute counts); both new nodes pass in my copy, `review-20260925T040024-60fb84`.
- Mixed-case selection on the walker's hot path, probe `verify-performance-1/test_zz_probe_miss.py`
  (copied to `tests/optimizer/` in the copy), `review-20260925T040111-52f3c0`, 21-field
  `managed=False` type, `info=None`: reversible lowercase hit `plainJ` 150.4 ns per
  `_resolve_selection_target` call; mixed-case `mixedCase0` 7544.5 ns, `mixedCase9` 8437.8 ns (the
  reverse lookup misses, `_graphql_names_by_python_name` rebuilds the type's name dict, then
  `_field_by_graphql_name` scans the map). A first run, `review-20260925T040057-e51263`, used
  `plain9` as the control and measured 8144.1 ns: a digit-boundary name takes the same miss path
  today. Not a finding against this item: before the change a mixed-case selection crashed the
  query (M1), so there is no working "before" to regress from, and the miss path's cost is
  pre-existing walker behaviour shared with digit-boundary names. Named gap for Worker-0 to route
  to an `optimizer/walker.py` Performance review (out of this run's scope): ~50x per-selection
  cost on the miss path, paid per plan build (plan-cache miss, every non-cacheable request);
  candidates to measure there are a per-type memo of the forward name map or a raw
  `field_map.get(graphql_name)` probe before the scan. Reopens here only if the walker item shows
  the miss path above 2% of `bench_optimizer_walk.py` time on a supported schema.

Cells: default only. Sharded and pg `inapplicable by construction`, judged and upheld for L1 (pure
`str -> str`, no connection, alias or dialect); M1's cells are the Mechanics verifier's to judge.

Disputes: none in `## Implementation (Worker-2)` for this axis. Cross-axis findings placed here:
none. The Performance record's out-of-axis `snake_case.__doc__` lead landed as Comments F2 (graded
by the Comments verifier).

Verdict: L1 verified; no new Performance finding on this item.

Fingerprints (`git hash-object`, shared tree, all equal to Worker-2's): `utils/strings.py`
536d175cd605; `optimizer/walker.py` 73d6929a5881; `types/base.py` 49057fad2058;
`types/finalizer.py` de34ae2aaed1; `management/commands/inspect_django_type.py` 2807d0fc9d75;
`tests/utils/test_strings.py` 3dad1a9d42d8; `tests/optimizer/test_extension.py` 4101bbd3805e;
`scripts/bench_optimizer_walk.py` de745175799b; probe `performance/probe_plain_text.py`
d239152c6bc4; `diff/pass-1.diff` b8c938472fac.

Handoff: Read beyond the record: the walker's `_resolve_selection_target`,
`_field_by_graphql_name`, `_graphql_names_by_python_name` bodies (the miss path), Worker-2's
`proofs.json` and before/after JSON, the whole diff. The only open thread is the walker miss-path
cost above, which belongs to `optimizer/walker.py`, not this item; with a converter in `info` it
will be higher than the `info=None` figure measured here (one `converter.get_graphql_name` per
Strawberry field per miss). The walk bench on this machine swung ~15% between identical runs, so
a later pass comparing walk figures should interleave copies as done here rather than compare to
the baseline table. The miss probe's source is kept under `verify-performance-1/`; its copy under
`tests/optimizer/test_zz_probe_miss.py` lives only in slot-3.

## Review pass 2 (run 0.0.15 2026-09-28-3)

Reopened: fingerprints moved. Every run-1 section above stands (L1 implemented and verified,
5 rejections, looks-for discharged); this pass appends the re-review of the live target and
records zero new findings.

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831
ITEM_BASELINE=e79425515bb25b376f330ac50d46d9615b9aad19.

Path class: hot - unchanged. `django_strawberry_framework/optimizer/walker.py` still calls
`django_strawberry_framework/utils/strings.py::snake_case` once per selection on every plan
build (plan-cache miss, every non-cacheable request); every other helper runs at declaration,
finalize, or behind an upstream memo.

### Trace (run 3)

Live target read whole at blob `5a4f4811`. Its only delta vs HEAD (`991f7dad`, the verified
post-pass-2 state; `git diff HEAD`, 5 insertions, 3 deletions) is concurrent work from the
truthful-reads flow, not this item's: `from . import truth`, and
`django_strawberry_framework/utils/strings.py::_plain_text` now calls
`django_strawberry_framework/utils/truth.py::is_instance` where it called `isinstance`, and
`django_strawberry_framework/utils/truth.py::kind` where it called the now-deleted
`exceptions._safe_type_name`. The exact-`str` fast path L1 ordered first is byte-identical.
`git diff e7942551 -- <target>` is empty: the concurrent edit predates the item baseline.

Caller census (whole package, calls only, imports / defs / prose excluded): `snake_case` 3
(walker lines 411, 769, 1421 - the same three sites as run 1);
`flatten_lookup_path` 3 (`utils/inputs.py:200` input building,
`utils/permissions.py:78` behind the unchanged `lru_cache(2048)`
`django_strawberry_framework/utils/permissions.py::_check_method_name`,
`django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions` line 731
per to-many order entry beside `classify_path` + an aggregate build);
`graphql_camel_name` 12 (forms / mutations / `utils/inputs.py` /
`rest_framework/serializer_converter.py` / `rest_framework/inputs.py`, all declaration-time
input building; the `_camel_case = graphql_camel_name` aliases in `filters/inputs.py:69` and
`orders/inputs.py:56` predate HEAD and have no package call sites - test-only use);
`pascal_case` 2 + the internal `pascal_case_or_raise` call (choice-enum names, declaration);
`pascal_case_or_raise` 2 (`filters/inputs.py:261`, `sets_mixins.py:116`, declaration). No new
hot caller; every caller's path class matches run 1. The walker miss path now reads the
`_forward_names` memo (the run-1 routed lead, closed beside the run), but the `snake_case`
reverse probe still runs first per selection, so call counts are unchanged.

Orientation: `review_inspect.py` into `<root>/performance/inspect/` + `strings.json` (leads
only; its `utils/imports.py` `_plain_text` callers are the pass-through twin, a name
collision confirmed by reading).

Measurements, both in copy `review/utils/strings.py/performance`, package digest
`sha256:c9db5de2...0eae97c9`:

- `review-20260928T202314-2c0073`: `probe_plain_text_ab.py` (source
  `<root>/performance/probe_plain_text_ab.py`, run by absolute path; JSON
  `<root>/performance/plain_text_ab.json`), timeit median of 9 repeats, HEAD logic
  reconstructed verbatim (incl. the full HEAD `_safe_type_name` body) vs the live import in
  one process. Parity ok on exact `str`, a `str` subclass, a hostile subclass, `None` / `3` /
  `b"x"` (same outcomes, same `ConfigurationError` texts). Exact-`str`: head 34.2 ns vs live
  34.4 ns (delta 0.2 ns, noise on identical bytecode - the hot path is untouched).
  Subclass: 69.2 vs 247.2 ns (+178 ns). Error: 335.0 vs 681.2 ns (+346 ns).
- `review-20260928T202329-201d65`: `importtime_report.py --rounds 5 --top 80 --json
  <root>/performance/importtime.json` (instrument `15f679c9`, so the row compares nothing
  numerically to run 1's `bfce84b9` baseline; the verdict below is session-internal).
  Minimum across rounds: `utils.strings` self 85 us, cumulative 85 us;
  `utils.truth` self 163 us; `utils.relations` cumulative 916 us; package cumulative
  178.2 ms, self 22.1 ms over 69 modules. Strings cumulative equals its self: the
  `from . import truth` contributes nothing, because `utils/__init__.py` imports
  `.relations` (line 44, itself `from . import truth`) before `.strings` (line 45), so
  `truth` is already in `sys.modules` when `strings.py:24` executes (a dict hit). Run 1's
  83 us figure is context, not a delta.

Cells: default only. Sharded and pg `inapplicable by construction`, as in run 1: the module
is pure `str -> str`, opens no connection, reads no alias, makes no dialect decision, and
imports no ORM symbol (`functools`, `collections.abc`, `exceptions`, `truth` only).

Fingerprints (`git hash-object`): `utils/strings.py`
5a4f481132f87cc83abeb2a4a4a679990fa5b9bc; `utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9; `optimizer/walker.py`
d5759ef8533a6218942a0a2a33e64f59599a93a7; `utils/permissions.py`
1c9cfd398e6096e03bda82ba93dfd66a6d2fb890; `orders/sets.py`
60859f2d54525acfdb3dc997d3e931ff3d58d956; `exceptions.py`
206e9f8d914f640134cf72e374fadeac41d13a39; `utils/__init__.py`
1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee (unchanged since run 1); `utils/inputs.py`
b5af8255dfa18a2ff423cdd2de211723c5a15590; `filters/inputs.py`
a932dbf85d89791280774b0600a40b5fb43b89e4; `orders/inputs.py`
2d258da74ee36f5d851ffa6550462b0fd65bd460; `mutations/inputs.py`
840da733f95678be5ea494bb6ab595c8425a1884; `forms/inputs.py`
259afbb2d5c7eeadb2ec3e996b26567328dd7295; `rest_framework/serializer_converter.py`
96d2b56a043e7f17000a654d1b6320bec39fdac3; `rest_framework/inputs.py`
eab5cf34112f691e87faaec9119a974d145ffc00; `types/converters.py`
f6cadb0856c725d96ce316abb4418b4c9d55bf9d; `sets_mixins.py`
088ddab0c0f68c0605bc4a440dfa3daa544452dd; `scripts/bench_optimizer_walk.py`
de745175799b1d8c0efa5c75cd296f9dd6910e34 (same blob as the run-1 baseline instrument);
`scripts/importtime_report.py` 15f679c9ad736b71215d8ead0733116f56083cef;
`examples/fakeshop/apps/library/models.py` b980e82c5e5a73690a18befd1eb5c7db1cf05691;
`tests/utils/test_strings.py` 2a822a3fff4c910407968165ee34e242c551a41b.

### Findings (run 3)

#### High

None.

#### Medium

None.

#### Low

None.

### Rejected (run 3)

- **R1 (new): the truth-call cost on `_plain_text`'s cold branches is not a finding.**
  Subclass inputs cost +178 ns/call and the error branch +346 ns/raise
  (`review-20260928T202314-2c0073`), buying the truthful-reads property (no consumer
  `__instancecheck__` / metaclass hook runs). Both branches are cold-only: the hot path
  passes exact `str` (graphql-core AST names, declared paths), which returns before either
  call at zero delta (+0.2 ns, noise). Cold-path performance needs a stated reason to
  implement, and none exists: any "fix" would re-spell the guard or weaken a security
  property owned by concurrent work outside this item's fence. Reopens if a hot caller
  starts passing non-exact-`str` per request (then the +178 ns lands on the hot path), or
  if a measured plan build shows `_plain_text` above 2% of walk time.
- **Inline exact-`str` fast path in `snake_case`: rejection stands.** Trigger was snake
  above 2% of `bench_optimizer_walk.py` time. Bench candidates are unchanged (same script
  blob `de745175`, same four lowercase hit-path queries), the per-call cache-hit cost is
  unchanged (identical code below `_plain_text`), and per-candidate call counts are
  unchanged (same three walker sites, probe-first). The `_forward_names` memo only
  cheapens miss paths the bench never hits. Not re-measured: every term of the trigger
  inequality is unchanged by reading.
- **`lru_cache(maxsize=2048)` sizing: rejection stands.** Vocabulary was 708 in run 1;
  since then fakeshop gained two models totalling four fields (`displayName`, `label`,
  `distributorRef`, `consignmentItems`), so the vocabulary stays an order of magnitude
  below `maxsize`. Same trigger: a supported schema exceeding 2048 distinct field names.
- **Char-by-char rebuild in `_snake_case_cached`: rejection stands.** Code unchanged
  (the target diff touches only imports and `_plain_text`); still once per distinct name
  per process behind the cache.
- **`camel +=` / `pascal_case` slices / joins: rejection stands.** Code unchanged; every
  caller still declaration/finalize time (census above).
- **`while "__" in flattened` in `flatten_lookup_path`: rejection stands.** Code
  unchanged; still one call per to-many order entry beside classification + aggregate,
  memoized on the permission path.

Looks-for discharged, `none` (run 3): N+1 / per-row queries, `len(qs)` / `bool(qs)`,
`only()` / `defer()`, unbatched writes, `blog.id` vs `blog_id` (still no ORM use);
repeated `_meta` walks, settings reads, regex compilation, schema or type lookups (none in
the module); `lru_cache` on methods / B019 (the one cache still decorates a module-level
function); locks, cache reads, re-parses, round trips on a per-request path (only the
`lru_cache` lookup, the intended memo); import-time cost (strings 85 us self with zero
child cost; no settings read at import); allocation in the walk (cached path allocates
nothing; the exact-`str` path is two byte-identical bytecode ops).

### Cross-axis (run 3)

None. No out-of-axis finding; the `truth.kind` vs `_safe_type_name` message-text
equivalence under hostile metaclasses is intended behavior of the concurrent work that owns
it (observed equal on `None` / `3` / `b"x"` as the timing probe's control), not a lead.

Handoff: Read beyond the trace: `utils/truth.py::is_instance` / `::kind` bodies (a
Python-level MRO identity walk, structurally slower than the C `isinstance` it replaces -
the measured +178 ns), the walker's three `snake_case` sites and the `_forward_names` memo
shape, the `OrderSet._resolve_order_expressions` to-many branch, the `_check_method_name`
memo, both `_camel_case` aliases (pre-existing, test-only use). The only target delta is
concurrent work outside this item's fence; Worker-2 must not touch it from this record.
The sibling Mechanics and Comments reviewers run concurrently on the same live target;
their records held only run-1 content when this pass closed, so no run-3 cross-axis text
existed to answer. If a later pass re-opens the inline-fast-path trigger, it must measure
a walk, not argue shares: the bench candidates are lowercase-only, so a miss-heavy
consumer query is the shape that could move the share. Scratch kept under
`docs/review/temp-tests/utils__strings/performance/` (inspect/, strings.json,
probe_plain_text_ab.py, plain_text_ab.json, importtime.json). Superseded run
`review-20260928T202301-4e1750` (exit 1, probe `repr()` tripped the hostile subclass)
measured nothing; its fix is the static-label loop in the kept probe.

## Verification (Performance) pass 2

Address `review/utils/strings.py/verify-performance-2`, copy slot-3 synced
2026-09-28T20:43:34Z from the shared tree, package digest
`sha256:c9db5de2...0eae97c9` (= the run-3 reviewer's digest on both runs);
scratch `docs/review/temp-tests/utils__strings/verify-performance-2/`.
Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831,
ITEM_BASELINE=e79425515bb25b376f330ac50d46d9615b9aad19. Run-1 sections stand;
this pass verifies run 3's `no-findings` against Implement pass 3's zero-path
landing.

Step 1: `git diff e7942551 -- django_strawberry_framework/utils/strings.py`
is empty (0 bytes), hash-equal to the empty item diff
`docs/review/temp-tests/utils__strings/diff/pass-3.diff` (0 bytes, by design:
all three run-3 reviews closed `no-findings`). Re-checked after the last probe
run: still 0 bytes. The tree did not move under the pass. (`git status` shows
the target `M` vs HEAD: the concurrent truth switch, which predates
ITEM_BASELINE and sits in none of this item's hunks, as the run-3 records
state.)

Proof lines: none exist for run 3 (zero findings, zero Proof lines in this
record, in the siblings' `## Cross-axis (for Performance)` - both "None" -
and in Implement pass 3). Run-1 Proof lines were not re-run as expectations
(closed run; several oracles moved since); nothing below depends on them.

Numbers reproduced, every run-3 reviewer number for this axis from its
recorded command (no `before` figure exists or is owed: both run-3 numbers
are session-internal, the A/B probe carrying its own HEAD reconstruction):

- A/B probe, `review-20260928T204334-686afe` (reviewer's
  `performance/probe_plain_text_ab.py` by absolute path, copy unedited, JSON
  `verify-performance-2/plain_text_ab.json`, exit 0): `parity: ok`; exact-str
  head 31.4 vs live 31.7 ns (delta 0.3 ns; reviewer 34.2 vs 34.4, delta 0.2);
  subclass head 66.3 vs live 289.2 ns (+222.9; reviewer +178.0); error head
  361.0 vs live 748.2 ns (+387.2; reviewer +346.2). Same verdict on the same
  digest: the hot exact-`str` path is untouched (sub-nanosecond noise on
  identical bytecode), the cold branches carry the truth cost.
- Import time, `review-20260928T204341-320afa` (`importtime_report.py --rounds
  5 --top 80`, instrument blob `15f679c9` = reviewer's, JSON
  `verify-performance-2/importtime.json`, exit 0): `utils.strings` self 88 us,
  cumulative 88 us (reviewer 85/85); `utils.truth` 167/167 (reviewer 163/163);
  package cumulative 182.6 ms, self 23.0 ms over 69 modules (reviewer 178.2 /
  22.1 / 69; machine spread). Strings cumulative equals its self: the
  `from . import truth` is a `sys.modules` dict hit, zero child cost.
  Reproduced.

Whole-diff reading (Performance): the item diff is empty - there is no hunk to
grade, no branch-order, cache, import or call-site change on any path class.
Path class hot stands (three walker `snake_case` sites, confirmed at 411,
769, 1421); every rejection trigger is evaluated below, not re-argued.

Attacks (current state, other cardinality / caller / input class):

- A. R1's reopen trigger ("a hot caller starts passing non-exact-`str` per
  request") does not fire. All three walker sites pass `sel.name`, which
  `selections.py::included_field_selections` and
  `walker.py::_merge_aliased_selections` pass through untouched from
  Strawberry's selection objects (built from the graphql-core parser's
  `NameNode.value`, an exact `str`; no rebuild, no subclass feeder in the
  package). The `OrderSet._resolve_order_expressions` `flatten_lookup_path`
  input is a coerced GraphQL input string beside `classify_path` + an
  aggregate build; the permissions path stays behind the unchanged
  `lru_cache(2048)` `_check_method_name`. Static reading, shared tree; no
  finding.
- B. Cache-sizing rejection measured at full-vocabulary cardinality (the
  reviewer carried 708 + arithmetic). Probe
  `verify-performance-2/probe_vocab.py` boots the live fakeshop schema and
  counts distinct introspected field + input-field names,
  `review-20260928T204636-ff9174` (exit 0, same digest): vocabulary 732 vs
  `maxsize` 2048, 2.8x headroom (and this count includes input fields the
  walker never reverses, so the true walker vocabulary is smaller). Full-vocab
  `snake_case` sweep: cold pass 0.45 ms, warm pass 0.044 ms (~60 ns/name);
  cache after warm `hits 8784, misses 732, currsize 732`: zero evictions. The
  rejection stands, now measured. Superseded `review-20260928T204623-f31aaf`
  (exit 1, probe bug: `cache_parameters()` is a dict on this interpreter).

Disputes: none recorded in `## Implementation (Worker-2)` / Implement pass 3
for this axis. Cross-axis findings placed here: none.

Failability: none owed. No change exists to fail - Implement pass 3 landed
zero paths, so no test-fails-without-the-change proof is possible or
required. Stated, not skipped.

Cells: default only. Sharded and pg `inapplicable by construction`, judged and
upheld: the module is pure `str -> str`, imports `functools`,
`collections.abc`, `exceptions`, `truth` (stdlib-only) only, opens no
connection, reads no alias, makes no dialect decision. Siblings concur.

New findings: none. Verdict: verified.

Fingerprints (`git hash-object`, shared tree, all equal to the run-3 records
and Implement pass 3): `utils/strings.py` 5a4f481132f8; `utils/truth.py`
d5c96bc8d191; `optimizer/walker.py` d5759ef8533a; `tests/utils/test_strings.py`
2a822a3fff; `scripts/importtime_report.py` 15f679c9ad73;
`scripts/bench_optimizer_walk.py` de745175799b. Item diff `pass-3.diff`
0 bytes.

Handoff: Read beyond the record: the live `_plain_text` body against
`truth.is_instance` / `truth.kind`, the walker's three `snake_case` sites
plus the `sel.name` passthrough chain in `selections.py`, the
`OrderSet._resolve_order_expressions` to-many branch, the `_check_method_name`
memo, the run-3 probe sources and JSON, Implement pass 3's attribution (the
`cmp` identity proof holds: item diff still 0 bytes). Conclusions the checks
do not state: the concurrent truth switch is the only live delta and it is
outside this item's fence; every run-1 rejection trigger was re-evaluated
against current state (R1 trigger read at all five hot call sites, cache
sizing measured at 732, bench candidates unchanged per the pinned
`de745175` blob). Open threads, none this item's: sibling verifiers run
concurrently (the Mechanics record moved mid-pass; its run-3 content as read
still routes nothing to Performance). Scratch kept under
`docs/review/temp-tests/utils__strings/verify-performance-2/`
(plain_text_ab.json, importtime.json, probe_vocab.py, vocab.json).
