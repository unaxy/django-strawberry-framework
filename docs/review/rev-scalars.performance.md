# Review · Performance: `django_strawberry_framework/scalars.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=be73a504707bc57990681fc526ad5607c1e681d1

Path class: hot — `django_strawberry_framework/scalars.py::_serialize_bigint`
runs per BigInt field per row on every response carrying a 64-bit column,
and `django_strawberry_framework/scalars.py::_parse_bigint` runs per BigInt
input value per request; `django_strawberry_framework/scalars.py::strawberry_config`
is cold (schema construction only).

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target and no Routed
lead on this item), `docs/review/rev-scalars.md` (skeleton: `Status:
reviewing`, blank Path class). Sibling axis records
(`rev-scalars.{performance,mechanics,comments}.md`) did not exist when this
pass closed; no Handoff or Cross-axis text was available.

Target read whole (179 lines, blob `5da8c140`). Live matches ITEM_BASELINE
byte for byte (`git diff be73a50 -- <target>` empty: no drift since the
item baseline). Dirty vs HEAD (`+34/-62`) is concurrent work, reviewed as
it stands: the truthful-reads migration (`isinstance` to
`truth.is_instance`, `str.__str__` to `truth.text`, `_safe_arg_repr` /
`_safe_type_name` to `truth.render` / `truth.kind`). A re-review is owed
if concurrent work lands another caller of any target symbol.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/scalars/performance/inspect/` (json
`docs/review/temp-tests/scalars/performance/scalars.json`): 3 symbols, 0
Django/ORM markers, 0 per-row leads, 0 hot entry points (the scalar seams
are invoked through Strawberry's registry, invisible to the static
reachability heuristic), 2 import-time calls (`re.compile`,
`strawberry.scalar`).

Callers traced by `grep` over the package, tests, and examples, plus reads
of the wiring on both sides. Outbound:
`django_strawberry_framework/types/converters.py::SCALAR_MAP` maps
`BigIntegerField` and `PositiveBigIntegerField` to `BigInt`, so every
64-bit column serializes through `_serialize_bigint` once per row;
Strawberry's scalar factory wires `definition.serialize` directly into
`GraphQLScalarType` with no memoization layer (read as
`_make_scalar_type` in the installed strawberry-graphql 0.324.0 tree),
and graphql-core completes each field value through it.
Live per-row legs: `ScalarSpecimen.signed_big` / `unsigned_big`
(`examples/fakeshop/apps/scalars/models.py`) and
`Patron.lifetime_fines_cents` (`examples/fakeshop/apps/library/models.py`).
Inbound: `scalar_specimen_by_signed_big(signed_big: BigInt)` exercises
`parse_value` per request
(`examples/fakeshop/apps/scalars/schema.py`), as does every BigInt filter
bound. `strawberry_config` runs at schema construction only
(`examples/fakeshop/config/schema.py`, once per process in production).
`inspect_django_type.py` reads `_PACKAGE_SCALAR_MAP` at command time
(cold). The package root re-exports `BigInt`, `Upload`,
`strawberry_config`, so the module joins every package import
(import-time row below). `truth.is_instance` walks the real MRO in Python
(`django_strawberry_framework/utils/truth.py::is_instance`); bare
`type(x) is T` reads `ob_type` directly and is the precedent on hot paths
(`resource_policy.py:254`, `consumers.py:573`, `conf.py:204`), and the
gate's TR001 set (`scripts/check_truthful_reads.py`) does not flag it.

Measurements, address `review/scalars.py/performance`, package digest
`sha256:5c16fc5c26601a47414759f8ac8cbe8e9d797d25d69709512ac1156e3aa8605c`
on every run, python 3.14.2, macOS arm64:

- `review-20260929T113237-957d3f`: `probe_hot.py` (timeit 20k x 9
  medians; A/B pairs interleaved 20k x 11). Standalone medians:
  `truth_is_instance_int` 201.6 ns, `type_is_int` 35.8 ns (with lambda
  overhead), `serialize_exact_int` 566.7 ns, `parse_exact_int` 523.1 ns,
  `parse_exact_str` 1234.1 ns, `strawberry_config` 911.6 ns. A/B legs:
  serialize 592.1 to 95.0 ns, parse-int 549.0 to 61.0 ns, parse-str
  1275.3 to 793.9 ns. Agreement battery: 29 inputs x 2 seams identical
  (values and exception types), including a hostile int subclass and a
  lying str subclass.
- `review-20260929T113256-130592`: `importtime_report.py --rounds 5`
  (instrument `15f679c9`, same digest): `scalars` self 235 us,
  cumulative 235 us, against 243.7 ms package cumulative.
- Before-state behavior pins, all green: `tests/test_scalars.py`
  `review-20260929T113319-54c85b` (28 passed);
  `tests/types/test_converters.py` BigInt pair
  `review-20260929T113328-c42096` (2 passed); live
  `examples/fakeshop/test_query/test_scalars_api.py`
  `review-20260929T113336-5218a2` (82 passed).

No bench-baseline figure moves: none of the four plan benches executes
scalar parse/serialize (plan-cache, walk, and nested-fetch shapes touch
no BigInt value path; importtime is unaffected since the change moves no
import), and the saving is sub-bench-spread CPU either way.

Cells: default, sharded, and pg are all `inapplicable by
construction`: the target reaches no database, no alias read, and no
dialect branch (0 inspect markers; pure functions plus a schema-config
factory; no `connections` / `using` / vendor branch), and the probe
opens no database. The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/scalars.py`
`5da8c14052321d214d3e9dfff2bde3d59c90d92c` (live, whole, equals
ITEM_BASELINE);
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9` (whole);
`django_strawberry_framework/types/converters.py`
`f6cadb0856c725d96ce316abb4418b4c9d55bf9d` (SCALAR_MAP rows);
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` (re-export lines);
`tests/test_scalars.py`
`156b57e13222c7586de017c2c2575c9f995f25f3` (subclass and message pins);
`tests/types/test_converters.py`
`ddf24f5997a5185dec079598d7506b6c7d3cf6a3` (BigInt section);
`examples/fakeshop/config/schema.py`
`303ea2da9df1f8611c02926fd28c59e5ccf9ecac` (config call site);
`examples/fakeshop/apps/scalars/schema.py`
`6bd2375ee3647fff3c7cfb9e5fc1365416848c36` (input-position field);
`examples/fakeshop/apps/scalars/models.py`
`6f65052e83c0aab1af268784e45bd50bf3a37905` (64-bit columns);
`examples/fakeshop/test_query/test_scalars_api.py`
`edc50088330abef73c3b33dcd8b7f04c5e9e4467` (live pins, file list only);
`scripts/check_truthful_reads.py`
`3c7ad51154d4b5a716f8599696110bd3dedcc4eb` (TR001 set, IDENTITY_CALLS).
Installed-tree reads (no git blob): strawberry-graphql 0.324.0
scalar factory and converter wiring (installed `schema` package).

## Findings

### High

None.

### Medium

#### F1: `_serialize_bigint` pays two MRO-walking type tests per value

- Observation:
  `django_strawberry_framework/scalars.py::_serialize_bigint` classifies
  every value through `truth.is_instance(value, bool)` then
  `truth.is_instance(value, int)`, each of which fetches a real MRO and
  identity-scans it in Python (~200 ns apiece). The overwhelmingly
  common input, an exact `int` materialized by the ORM for a 64-bit
  column, takes the slowest branch: two MRO walks before
  `int.__repr__`.
- Evidence: timeit medians at `review-20260929T113237-957d3f` (same
  digest as above): `serialize_exact_int` 566.7 ns standalone;
  interleaved A/B of current vs an exact-type-first variant 592.1 vs
  95.0 ns. Single-call attribution: `truth.is_instance(int)` 201.6 ns
  vs `type() is` 35.8 ns. The probe's agreement battery (29 inputs x 2
  seams, values and exception types, incl. hostile subclasses) passes,
  so the variant is behavior-identical.
- Impact: the seam runs per BigInt field per row (see Path class). A
  100-row connection over a type with two BigInt fields pays ~0.5 us x
  200 = ~100 us of classification per request today, ~20 us after.
- Severity: Medium (measured cost on a hot path, no N+1).
- Recommendation: open `_serialize_bigint` with an exact-type fast
  path, before the bool check (exact `int` excludes `bool`, since
  `type(True) is bool`):
  `if type(value) is int: return int.__repr__(value)`.
  Two lines, same expressions as today; every non-exact input flows
  exactly as now. Bare `type() is` is gate-clean (TR001 set read) and
  the hot-path precedent (`resource_policy.py:254`).
- Must not change: hostile int subclasses still normalize through the
  base slot (pinned by
  `tests/test_scalars.py::test_bigint_int_subclasses_are_normalized_before_serialization`);
  `bool` still raises `TypeError` with the same message; non-int kinds
  still raise with the `truth.kind` spelling. A failability revert of
  this finding must change nothing (`expect_failing=[]`): the change
  is behavior-identical by construction.
- Proof:
  - `uv run python scripts/workspace.py run review/scalars.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/scalars/performance/probe_hot.py` prints `agreement: ok over 29 inputs x 2 seams` and `serialize_exact_int: median_ns=` below `300.0` (before `566.7`).
  - `uv run python scripts/workspace.py run review/scalars.py/verify-performance-<n> -- pytest tests/test_scalars.py --no-cov -p no:randomly -q` reports `28 passed` (before-state green at `review-20260929T113319-54c85b`).
  - `uv run python scripts/workspace.py run review/scalars.py/verify-performance-<n> -- pytest examples/fakeshop/test_query/test_scalars_api.py --no-cov -p no:randomly -q` reports `82 passed` (before-state green at `review-20260929T113336-5218a2`).
- Freshness: all files in `## Trace`.
- Path class: hot - per BigInt field per row (see `## Trace`).
- Instrument: `timeit` median over 20k x 9 (A/B pair interleaved 20k x
  11); no database opened.
- Before: `serialize_exact_int` 566.7 ns standalone, 592.1 ns A/B leg
  (run `review-20260929T113237-957d3f`).
- After (predicted): ~95 ns (the A/B fast leg).
- Delta (predicted): ~-0.5 us per serialization. No bench figure
  moves (see `## Trace`).
- Permanent test: none timing-based (flaky by construction); behavior
  pinned by the Proof nodes (the change is behavior-identical, so no
  new test can pin the saving), the number reproduced by the probe
  rerun.

#### F2: `_parse_bigint` pays up to four MRO-walking type tests per value

- Observation:
  `django_strawberry_framework/scalars.py::_parse_bigint` classifies
  every value through up to three `truth.is_instance` MRO walks (bool,
  int, str), and the str leg then calls `truth.text(value)`, which
  re-runs the str MRO walk the outer check just established before
  copying through `str.__str__`. Exact `int` inputs pay two walks;
  exact `str` inputs, the wire shape for large values, pay four.
- Evidence: timeit medians at `review-20260929T113237-957d3f`:
  `parse_exact_int` 523.1 ns standalone, A/B 549.0 vs 61.0 ns;
  `parse_exact_str` 1234.1 ns standalone, A/B 1275.3 vs 793.9 ns. Same
  agreement battery as F1 (29 inputs x 2 seams, incl. a lying str
  subclass whose forged `__str__` never leaks through either shape).
  Slot-identity facts asserted in the probe: `int.__int__` and
  `str.__str__` return the same object for exact types, so exact
  inputs need no copy.
- Impact: the seam runs per BigInt input value per request
  (arguments, filter bounds). Each value pays ~0.5 us of
  classification today on top of the regex and conversion the
  contract requires.
- Severity: Medium (measured cost on a hot path, no N+1).
- Recommendation: open `_parse_bigint` with `if type(value) is int:
  return int.__int__(value)`, and take the str leg through an
  exact-type branch that skips both the outer walk and `truth.text`'s
  inner one:
  `if type(value) is str: plain_value = value` /
  `elif truth.is_instance(value, str): plain_value = truth.text(value)`
  / `else: raise ...`, sharing today's regex tail unchanged.
  Subclass inputs keep today's spelling (`truth.text`), so the
  concurrent migration's chosen contract is untouched where it can
  matter.
- Must not change: the full accept/reject table in the docstring, the
  exact rejection messages (pinned by
  `tests/test_scalars.py::test_bigint_rejection_messages_are_pinned`),
  subclass normalization with exact-`int` results (pinned by the
  subclass test named in F1), and the `bool` / `float` / `None`
  `ValueError` legs. A failability revert of this finding must change
  nothing (`expect_failing=[]`).
- Proof:
  - `uv run python scripts/workspace.py run review/scalars.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/scalars/performance/probe_hot.py` prints `agreement: ok over 29 inputs x 2 seams`, `parse_exact_int: median_ns=` below `300.0` (before `523.1`), and `parse_exact_str: median_ns=` below `1050.0` (before `1234.1`).
  - `uv run python scripts/workspace.py run review/scalars.py/verify-performance-<n> -- pytest tests/test_scalars.py --no-cov -p no:randomly -q` reports `28 passed` (before-state green at `review-20260929T113319-54c85b`).
  - `uv run python scripts/workspace.py run review/scalars.py/verify-performance-<n> -- pytest tests/types/test_converters.py::test_bigint_in_input_position_with_null_via_schema_execution tests/types/test_converters.py::test_bigint_resolver_returning_bool_raises_via_schema_execution --no-cov -p no:randomly -q` reports `2 passed` (before-state green at `review-20260929T113328-c42096`).
- Freshness: all files in `## Trace`.
- Path class: hot - per BigInt input value per request (see
  `## Trace`).
- Instrument: `timeit` median over 20k x 9 (A/B pairs interleaved 20k
  x 11); no database opened.
- Before: `parse_exact_int` 523.1 ns standalone, 549.0 ns A/B leg;
  `parse_exact_str` 1234.1 ns standalone, 1275.3 ns A/B leg (run
  `review-20260929T113237-957d3f`).
- After (predicted): ~61 ns int, ~794 ns str (the A/B fast legs).
- Delta (predicted): ~-0.5 us per parsed value on both legs. No bench
  figure moves (see `## Trace`).
- Permanent test: none timing-based (flaky by construction); behavior
  pinned by the Proof nodes, the number reproduced by the probe
  rerun.

### Low

None.

Looks-for discharge (REVIEW.md "Performance"), each a finding, `none`
with the reason, or a rejection:

- N+1 and per-row queries: none. No ORM call, no `await`, no queryset
  built (0 inspect markers); both seams are pure functions of their
  argument.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none - no
  queryset; the only truthiness read is `if collisions:` on a
  cold-path list.
- `only()` / `defer()`: none - no projection exists to narrow.
- Unbatched writes: none - the module issues no writes of any kind.
- `blog.id` vs `blog_id`: none - no model attribute reads.
- Repeated `_meta` walks, settings reads, regex compilation,
  schema/type lookups: the regex compiles once at module level
  (correct); no `_meta`, no settings read, no schema or type lookup
  per request. The repeated per-value cost is MRO-walking truth
  checks: F1, F2.
- `lru_cache` on methods (`B019`): none - no `functools` import, no
  decorator in the module.
- Locks, cache reads, re-parses, extra round trips on a per-request
  path: none beyond F1/F2. No lock, no cache backend, no round trip;
  the str leg's double MRO walk is folded into F2.
- Import-time cost: none with numbers - `scalars` self 235 us
  min-of-5, 0.1% of the 243.7 ms package cumulative (R4); every import
  is load-bearing (`strawberry`, `truth`, stdlib).
- Allocation in the hot loop: none beyond the contract. Error
  f-strings (`truth.render` / `truth.kind`) build on raise paths
  only; every success path allocates nothing beyond the value the
  contract requires (R5 for the one conversion).

## Rejected

- **R1: the `^...$` anchors are redundant under `fullmatch`.** The
  engine work they add is unmeasurable against the match itself, and
  the anchors state the full-string contract at the pattern. Reopens
  if `parse_exact_str` stays above its threshold after F2 and a
  profile attributes it to the regex engine.
- **R2: `truth.text(value)` re-walks the str MRO for str-subclass
  inputs.** No wire-reachable input is a subclass (JSON decode yields
  exact `str` / `int`; only direct Python calls pass subclasses), and
  F2's exact-str branch already removes the walk from every
  wire-reachable input. Re-spelling the subclass leg as
  `str.__str__` would fight the concurrent migration for zero
  wire-reachable gain. Reopens on a wire-reachable str-subclass
  input.
- **R3: `strawberry_config` copies two dicts and sorts a collision
  scan per call.** Cold: 911.6 ns per schema build, once per process
  in production, over a 1-entry package map. Reopens if schema
  construction ever moves onto a per-request path.
- **R4: module import cost (`re.compile`, `strawberry.scalar`, the
  `truth` import).** Measured 235 us self, 0.1% of package import;
  all three are the module's reason to exist. Reopens if `scalars`
  self exceeds 1% of package cumulative.
- **R5: `int(plain_value)` conversion cost on huge digit strings.**
  Inherent to the documented arbitrary-precision contract, and the
  input size is bounded upstream by the request body caps. Capping
  digits would break the contract, which needs a maintainer decision,
  not a review finding. Reopens if a body-cap analysis shows the
  conversion exceeds the per-request CPU budget.

Handoff: Performance review is closed with two Medium findings (F1
serialize, F2 parse: exact-type fast paths ahead of MRO-walking truth
checks) and five rejections. The judgment calls a verifier could
revisit are the F2 str-leg shape (the if/elif/else shares the regex
tail rather than duplicating the 6-line error; either shape passes
the thresholds) and the R5 digit-cap non-finding (a real CPU
amplification shape, deliberately left as a contract question for
Rio). Everything else was discharged by absence (no ORM, no settings,
no functools, no locks) or by sub-noise measurement (import,
config factory). The target was dirty vs HEAD (the truthful-reads
migration, which is what put the MRO walks on this hot path) but
byte-identical to ITEM_BASELINE; the fast paths preserve that
migration's contract exactly (`type()` reads `ob_type`, the truthful
primitive itself) and the probe's 29-input agreement battery pins the
identity. No defects; no cross-axis text placed or owed; no bench
figure moves. Cells unverified: none beyond the stated
inapplicable-by-construction judgments for all three cells
(default/sharded/pg - no database reached).

## Verify performance

Precondition: the live tree carries exactly the change under grade.
`git diff ITEM_BASELINE -- <both paths>` is byte-identical to
`docs/review/temp-tests/scalars/diff/pass-1.diff` (ITEMDIFF-MATCH);
live blobs `scalars.py` 9e945168, `tests/test_scalars.py`
ab5943d6. The landed code hunks match both Recommendations
verbatim (F1 two-line exact-int return ahead of the bool check;
F2 exact-int return plus the if/elif/else str branch sharing the
regex tail).

All runs at `review/scalars.py/verify-performance-1` (slot-3,
package digest `sha256:b4b25dfd...`, cell default, copy `fresh`
except where noted). Scratch:
`docs/review/temp-tests/scalars/verify-performance-1/` (`probe.log`,
`test_scalars.log`, `test_scalars_api.log`,
`test_converters_bigint.log`, `probe-before.log`,
`probe-before-repro.log`, `probe-after-rerun.log`, `collect.log`).

### F1: serialize fast path - pass

- Probe `review-20260929T120150-34be10`: `agreement: ok over 29
  inputs x 2 seams`; `serialize_exact_int: median_ns=88.2`, below
  the `300.0` threshold (record before `566.7`; same-session
  baseline repro `657.3`, below). Post-change A/B legs agree
  (`89.4` vs `89.0`): the landed code IS the fast shape.
- `tests/test_scalars.py` `review-20260929T120200-49481e`: `28
  passed`. Collect-only `review-20260929T120450-5a86ca`: `28
  items`, the subclass test a single node - the `_HostileStr`
  leg sits inside the existing test, no new node.
- Live `test_scalars_api.py` `review-20260929T120208-7c2d01`:
  `82 passed`.

### F2: parse fast paths - pass

- Same probe run: `parse_exact_int: median_ns=55.8` below `300.0`
  (before `523.1`; repro `612.3`); `parse_exact_str:
  median_ns=702.9` below `1050.0` (before `1234.1`; repro
  `1449.7`). Post-change A/B legs agree on both legs (int `59.6`
  vs `58.2`, str `727.9` vs `748.0`).
- `tests/test_scalars.py`: `28 passed` (same run as F1).
- Converters BigInt pair `review-20260929T120240-c4fa2c`: `2
  passed`.

Before confirmation (two independent legs, since the `before`
copy's venv is broken - see open threads): the review-time
evidence log `review-20260929T113237-957d3f.log` survives and
prints the record's before figures verbatim (`566.7` / `523.1` /
`1234.1`, digest `5c16fc5c`); and the staged-baseline repro
`review-20260929T120433-7c5bff` (ITEM_BASELINE blob `5da8c140`
written into my copy, no `--fresh`) prints agreement ok plus
`657.3` / `612.3` / `1449.7` with A/B legs `653.8` vs `98.8`,
`611.6` vs `64.2`, `1345.7` vs `813.6` - the review's A/B
finding reproduced same-session, same venv. `--fresh` restore
rerun `review-20260929T120443-63e013` prints `89.2` / `55.8` /
`701.5`: restoration confirmed, after-numbers stable across
runs. Same-session delta: `-86%` / `-91%` / `-52%`.

Behavior identity per Must-not-change: the 29-input battery
(hostile int subclass, two lying str subclasses, bool, float,
None, object, malformed strings) agrees in BOTH directions
(after run and baseline repro); bool messages, the
`truth.kind` spelling, and both Accepts/Rejects docstring
tables are byte-unchanged in pass-1.diff (no hunk touches
them); `test_bigint_rejection_messages_are_pinned` passes
inside the 28; `type(True) is not int` is asserted by the
probe and the bool rejection tests pass. No timing test was
added (`grep -c` over timeit/median/threshold/perf_counter
tokens in `tests/test_scalars.py` prints `0`), by design; no
failability is owed (`expect_failing=[]` by construction, no
gate relies on the change, `implement/` correctly holds no
manifest).

Cells: default run performed for every leg. Sharded and pg
stand `inapplicable by construction`: the target carries zero
DB surface (no `connections` / `using` / `vendor` / `alias` /
queryset token; 0 inspect markers), the probe opens no
database, scalar behavior is dialect-independent, and the
live suites' DB use is vehicle-only.

No bench row moves: none of the four bench scripts nor
`_bench_common.py` references `BigInt` / `_parse_bigint` /
`_serialize_bigint` / `scalars` (grep exit 1); the diff adds
no import and leaves the cold `strawberry_config` factory
untouched (`847.2` / `812.8` ns across after-runs is noise).
Rejections R1-R5 stand: R1's trigger needs `parse_exact_str`
above threshold (`702.9`, closed); R2 no new wire-reachable
subclass input exists; R3/R4 the config factory and the import
list are untouched; R5 the digit-cap contract is untouched.

Prose edits disturb no Performance claim: M1's
`(int.__repr__ of the accepted int)` is true of the fast path
too (exact `int` returns `int.__repr__`); C1's bare-int-literal
wording names the hot parse population, consistent with the
Path class; M2/M3/L1/L2/L3 touch test prose and spec pointers
only; both strict-body docstrings are byte-unchanged.
Whole-diff reading: every hunk is an F1/F2 fast path, C1/M1/L1/L3
target prose, or test prose plus the test-only `_HostileStr`
coverage leg - no other hot-path code is touched.

Attacks, all passing, no new finding: (1) bool must miss both
fast paths - probe assertion plus the bool tests in the 28;
(2) agreement battery both directions (after + baseline);
(3) post-change A/B identity proves the landed shape;
(4) after-number stability across two runs (`88.2`/`89.2`,
`55.8`/`55.8`, `702.9`/`701.5`). Disputes: none (no
`## Implementation (Worker-2)` section exists, as on every
other item this run - nothing to judge).

Open threads: (1) the item's `before` copy venv is broken
(`review-20260929T120329-e50de2` exits 1:
`ModuleNotFoundError: No module named 'typing_extensions'`) -
Worker-0 note for sibling verifiers, not a gap (before
confirmed two stronger ways above); never `--fresh`-ed nor
edited. (2) Shared-tree drift during the pass:
`docs/dry/dry-file-utils__strings.md` moved (concurrent DRY
flow, unrelated to this item).

Handoff: Performance verification is closed: F1/F2 both pass
with agreement-ok plus all medians below threshold on three
after-side runs and a same-session baseline repro; 28 + 82 +
2 pins green; node count 28 with the subclass leg inside the
existing test; no timing test; cells judged (sharded/pg
inapplicable by construction); no bench row moves; R1-R5
stand; prose edits Performance-clean. The only follow-up is
Worker-0's: the broken `before` venv, which the Mechanics and
Comments verifiers will also hit if they address that copy.

Status: verified
