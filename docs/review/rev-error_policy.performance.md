# Review · Performance: `django_strawberry_framework/error_policy.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=59dad4a566f3718e6d99572ef853455d0aabc101

Path class: cold — `resolve_error_policy` runs once per schema construction
(`schema.py::DjangoSchema.__init__`); `ErrorPolicy.__post_init__` at
construction and import; `new_correlation_id` once per masked error on the
exceptional path only. Nothing in this file runs per request, resolver, row,
connection, or outbound message.

## Trace

Read the whole live target (191 lines) plus every caller and callee the
Performance axis needs: `schema.py::DjangoSchema.__init__` (sole production
caller of `resolve_error_policy`), `extensions/error_policy.py::_masked` (sole
production caller of `new_correlation_id`), `utils/policies.py::resolve_policy`
and `::canonical_policy` (the delegated resolution both policies share),
`conf.py::error_policy_setting` (the settings read), and
`utils/__init__.py` (the parent package `from .utils import truth` executes).
`review_inspect.py` orientation only (1 getattr lead, 0 per-row leads).
Sibling axis records did not exist when this pass ran (concurrent dispatches).

The target is dirty vs HEAD (the `describe_value` → `truth.describe` migration)
but identical to ITEM_BASELINE (`git diff <ITEM_BASELINE> -- <target>` empty),
so the fingerprints below are what was reviewed.

Cells: default, sharded, and pg are all inapplicable by construction — the
target reaches no database, alias, or dialect decision (no ORM, no connections,
no raw SQL, no `using`). No cell runs were made.

Fingerprints (`git hash-object` of every file read):

- `django_strawberry_framework/error_policy.py` 57a0bed1ba730f8e4c1f4c879d852274eac39f12
- `django_strawberry_framework/utils/policies.py` 0a2b7dbad96594b5d668774218809c6a94d136be
- `django_strawberry_framework/extensions/error_policy.py` a1defd394d8eda9b698964030a09efe6914278db
- `django_strawberry_framework/schema.py` 84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1
- `django_strawberry_framework/conf.py` 3820c575bfd4e3c384244d1bed460b75d3bb7681
- `django_strawberry_framework/utils/__init__.py` 1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee

## Findings

### High

None.

### Medium

None.

### Low

None.

## Looks-for discharge

Every entry below is `none` with the reason, measured where a number backs it.
Probe run `review-20260929T031305-d63dcf` (medians over 20000 repeats, Django
configured, package digest `sha256:c8c86495...`):
`ErrorPolicy()` 333 ns, `resolve_error_policy(None)` 2250 ns,
`resolve_error_policy(mapping)` 2417 ns, `new_correlation_id()` 1208 ns.
Import run `review-20260929T031312-772cb5` (`importtime_report.py --rounds 5`,
same digest): `error_policy` self 293 us, cumulative 293 us, vs package
cumulative 199494 us over 69 modules.

- N+1 / per-row queries: none. No ORM access anywhere in the file; the only
  loop iterates a 2-tuple of field names at construction.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none. No querysets.
- `only()` / `defer()`: none. No querysets.
- Unbatched writes: none. No writes of any kind.
- `blog.id` vs `blog_id`: none. No model attribute access.
- Repeated `_meta` walks: none. No `_meta` use; the `dataclasses.fields()`
  walk in `canonical_policy` lives in `utils/policies.py` (another item) and
  runs once per schema construction.
- Repeated settings reads: none. One settings read per schema construction
  via `resolve_policy` → `error_policy_setting`; no per-request read from
  this file. (The per-operation `settings.DEBUG` read is
  `extensions/error_policy.py::masking_is_active`, owned by that item.)
- Repeated regex compilation: none. No regex.
- Repeated schema / type lookups per request: none. No schema or type lookups.
- `lru_cache` on methods: none. No caching decorators.
- Locks, cache reads, re-parses, extra round trips on a per-request path:
  none. `new_correlation_id` is `uuid.uuid4().hex`, ~1.2 us, no I/O, and
  fires only when an unexpected exception is actually masked.
- Import-time cost: none, measured. Self 293 us with cumulative equal to
  self, i.e. every dependency was already in `sys.modules` (the `import
  uuid` charges nothing here); 0.15% of package import. `from .utils import
  truth` executes no new package body: importing `utils.policies` already
  forces the `utils` parent-package import.
- Allocation in the walk: none. No walker, no hot loop; `__post_init__`
  builds at most two f-strings on its raising path.

## Rejected

- R1: mint correlation ids with something cheaper than `uuid4().hex`
  (counter, timestamp, request id). Rejected: cross-process uniqueness
  without coordination, no deployment information, and fixed-width greppability
  are the documented contract, and 1.2 us fires only per masked error.
  Trigger: correlation ids appear on a non-exceptional path, or masking
  overhead dominates a measured error-heavy response profile.
- R2: skip `canonical_policy` re-validation on the no-override path (hand
  back `_PACKAGE_ERROR_POLICY` directly, saving ~2 us once per schema
  construction). Rejected: returning the shared module-level object across
  schemas breaks the authority boundary the copy exists to enforce, on a
  cold path where plainness wins by rule. Trigger: schema-construction time
  becomes a measured bottleneck and a safe hand-back exists.

Handoff: The file is four cold pieces plus one exceptional-path id mint; the
only request-time symbol (`new_correlation_id`) is one `uuid4` call behind an
already-allocated log record and `GraphQLError` build, so no optimization here
could move any bench figure — the `## Bench baseline` rows stand. Open thread
for the owning passes, not this one: the per-operation `settings.DEBUG` read
in `extensions/error_policy.py::masking_is_active` and the `dataclasses.fields`
walk in `utils/policies.py::canonical_policy` are both single-digit-microsecond
cold-or-cheap reads I observed while tracing; neither is a lead, recorded here
only so a later pass does not re-derive them. Sibling records were absent at
review time, so no cross-axis sections of theirs were read.

## Verification (Performance)

Step 1 — item diff identity. `git diff
59dad4a566f3718e6d99572ef853455d0aabc101 -- tests/test_error_policy.py
examples/fakeshop/test_query/test_error_policy_api.py` hashes
`sha256:364ed475b177c422db80426ba8c0dcee8f082119300000afb79c6d8897e01b2a`,
identical to `docs/review/temp-tests/error_policy/diff/pass-1.diff`. The tree
did not move under the pass. (`git diff <ITEM_BASELINE> --stat` on the two
paths: 2 files, +32/-23, matching the diff.)

Proof lines — none to run. This record carries no Proof line (no findings),
and neither sibling carries a `## Cross-axis (for Performance)` section: the
Mechanics record states no Cross-axis section exists, and the Comments Handoff
states "No Cross-axis findings: nothing in this pass belongs to Performance
or Mechanics" (confirmed by grep over all three records; the Comments
record's 11 Proof lines are Comments-axis Proofs, out of this axis's fence).
This was established before `## Implementation (Worker-2)` was read.

Worker-2 numbers — none claimed for this axis ("No number was owed and none
moves"), so nothing to reproduce from the implementer. The reviewer's own
numbers were reproduced instead, at `review/error_policy.py/verify-performance-1`:

- Probe (reviewer's `probe_error_policy.py`, copied verbatim to my scratch):
  run `review-20260929T035946-ccb467`, exit 0, package digest
  `sha256:c8c864951ee13077f2aff5343d8247e4b67358622e379772a1e20fdcfe3a5af2`
  — identical to the reviewer's digest, so the same code bytes were
  measured. Medians over 20000 repeats: `ErrorPolicy()` 458 ns (reviewer
  333), `resolve_error_policy(None)` 3292 (2250), `resolve_error_policy(mapping)`
  3917 (2417), `new_correlation_id()` 2125 (1208). Same order of magnitude on
  every entry point; the uniform upward shift is shared-machine drift (the
  target is byte-identical, so no delta is attributable to the change).
- Import time (`importtime_report.py --rounds 5`): run
  `review-20260929T035956-bd9dfa`, exit 0, package digest identical to the
  reviewer's and both instrument ids identical (`_bench_common.py`
  253a3953, `importtime_report.py` 15f679c9), so the figures compare.
  `error_policy` self 455 us (reviewer 293), cumulative equal to self both
  sides (dependency-free import holds); package cumulative 363223 us
  (reviewer 199494). Share of package import: 0.13% vs 0.15% — the same
  fraction; both levels scaled together with machine load.

Item-diff read through this axis — all 11 hunks in pass-1.diff are test-only:
10 docstring/comment prose hunks, one test-function rename (M1), one added
`assert set(error["extensions"]) == {key}, error` in the live-tier helper
`_masked_error` (M4). Production impact: zero. `git diff <ITEM_BASELINE> --
django_strawberry_framework/error_policy.py` is empty, and the live target
fingerprint `57a0bed1ba730f8e4c1f4c879d852274eac39f12` matches all three
review records and Worker-2's post-edit fingerprint. The whole live target
was re-read on this axis: construction/import resolution plus one
exceptional-path `uuid4` mint — the cold path class stands.

Attacks on the current state:

- Digest-identity attack: the reviewer's pre-implement digest (`c8c86495…`)
  equals my post-implement digest (`c8c86495…`), so the pass moved no
  digested package byte and no `## Bench baseline` row can move. Holds.
- M4-assert attack: the added line reads `error["extensions"]` (already
  fetched on the line above) and the in-scope `key` — an O(1) dict op in a
  test helper, 12 default-key call sites per Worker-2's census. No
  production path is reachable from it. Holds (test-time only).
- Rename attack: the M1 rename is collection-only; Worker-2's scoped
  `--code-digest` reconstruction isolates it as the single AST-significant
  line in that file. Nothing runtime to move. Holds.
- Cell attack: the diff adds no database, alias, or dialect reach, so the
  reviewer's "all three cells inapplicable by construction" stands;
  concurred, no cell runs owed.

Disputes — none. `## Implementation (Worker-2)` carries no `disputed:`
line, and Worker-2 reports zero disputes.

Failability / test tier — none owed. Performance closed no-findings, no
gate is relied upon, and no production (or production-reaching) change
exists to fail. The M4 assertion is Comments-owned; its judgment belongs to
the Comments verifier.

Cells unverified: none (all three inapplicable by construction, concurred).

Scratch: `docs/review/temp-tests/error_policy/verify-performance-1/` holds
`probe_error_policy.py` (verbatim reviewer copy) and `importtime.json` (this
pass's report). Run ids: `review-20260929T035946-ccb467` (probe),
`review-20260929T035956-bd9dfa` (importtime).

Fingerprints (`git hash-object`, post-verify):
`django_strawberry_framework/error_policy.py`
`57a0bed1ba730f8e4c1f4c879d852274eac39f12` (unchanged);
`tests/test_error_policy.py`
`9a72cdb83d4739be4018a3c58d0bf2736b63f569`;
`examples/fakeshop/test_query/test_error_policy_api.py`
`071b113feeaf9cee30ccda5941614c423251459c` (both match Worker-2's post-edit
fingerprints — nothing drifted after the implement pass).

Handoff: Performance verify pass 1 is closed with `Status: verified`. The
change is test-only (10 prose hunks + rename + one test assert), the target
is byte-identical to what all three axes reviewed, and the reproduced probe
and import-time figures — on the identical package digest and instrument ids
— confirm no number moves. No new finding, no gap, no open thread; the two
Routed leads in sibling records belong to other items and are untouched by
this diff.
