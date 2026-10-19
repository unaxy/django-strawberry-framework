# Review · Performance: `django_strawberry_framework/keyset.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=d6f1f0a4c4d291b03cf14e680ab3649aeda10851

## Trace

Target read whole (709 lines, blob `279ad7b0`). `git diff
<ITEM_BASELINE> -- <target>` is empty, so the tree reviewed is the item
baseline; `git diff HEAD -- <target>` is 11 insertions / 10 deletions of
concurrent work (the `truth.render` / `truth.is_instance` / `truth.name`
error-message conversions plus its import), all on cold
raise-paths, attributed to other sessions, not graded. The plan's
`## Owned changes` holds no row for this target. Skeleton
`docs/review/rev-keyset.md` read (`Status: reviewing`, blank Path
class); sibling axis records `rev-keyset.mechanics.md` /
`rev-keyset.comments.md` absent (concurrent run, not yet written).
Orientation: `review_inspect.py` overview + stripped source under
`<root>/performance/inspect/` (json `<root>/performance/keyset.json`):
0 per-row leads, 1 hot entry point (+0 reachable cross-module), 0
import-time work items, 0 database-shaped calls.

Hot-path map (every caller traced by `rg` over the package):

- `django_strawberry_framework/keyset.py::encode_keyset_cursor` runs once
  per edge (per row): `django_strawberry_framework/connection.py`
  windowed-page edge build and `_resolve_keyset_connection._build`.
- `django_strawberry_framework/keyset.py::decode_keyset_cursor` runs once
  per supplied `after:` / `before:` cursor per request: the slicer and
  `django_strawberry_framework/optimizer/nested_planner.py` keyset
  adapter (plan time).
- `django_strawberry_framework/keyset.py::KeysetSeek.q`
  (`keyset_seek_q`) runs once per supplied cursor per request;
  `django_strawberry_framework/keyset.py::keyset_seek_sql` once per
  lateral fetch per request via
  `django_strawberry_framework/optimizer/lateral_fetch.py::_keyset_seek_sql`
  (single `KeysetSeek.plan` build per fetch, traced).
- `django_strawberry_framework/keyset.py::declared_cursor_state_for_definition`
  runs at connection-class generation (cold, cached on the class) and
  once per nested connection plan build (plan-cache miss).
- Cold: `split_order_ref`, `validate_cursor_field_references`,
  `validate_cursor_field_columns`, `cursor_columns_for` (via the two
  callers above only), `order_fingerprint` except one join per
  `_keyset_order_state` resolve.

`Path class: hot` — the mint path runs per edge per row and the
decode/seek path runs per request per supplied cursor.

Measurements, copy `review/keyset.py/performance` (slot-2), package
digest `sha256:b164b5bc...1c3f10` on every run (all figures compare
with each other; the digest is not the `## Bench baseline` digest, so
no figure is claimed against the baseline table), instruments
`scripts/_bench_common.py` blob `253a3953`,
`scripts/importtime_report.py` blob `15f679c9` (equals gate-2's,
differs from the baseline's `bfce84b9`, so the importtime row
compares to nothing there). Provenance on every run: python 3.14.2,
django 6.1, strawberry-graphql 0.324.0, in-memory SQLite
(`file:dsf-bench-default?mode=memory&cache=shared`).

- `review-20260929T045544-a2f81a`: `probe_keyset_mint_costs.py` (probe
  blob `6acec2ca`; library `Issue`, `cursor_field ("-number", "id")`,
  2 columns; A/B pairs interleave 9 rounds and compare medians).
  Round-trip + variant byte-identity asserts pass. Medians:
  `encode_keyset_cursor` 5646 ns/row (interleaved before-block 6041);
  shared-serializer+AD-hoist variant 5929 (R2); fresh-vs-shared
  `JSONSerializer().dumps` 1615 vs 1583; fresh-vs-reused
  `value_to_string` shim 410 vs 286 ns/column (R3); decode 6905
  ns/cursor; `keyset_seek_q` 10772 ns; `keyset_seek_sql` 999 ns;
  `_cursor_aessiv` cache hit 168 ns; `settings.SECRET_KEY` read 137
  ns; `cursor_columns_for` 2256 ns; `declared_cursor_state_for_definition`
  2839 ns. JSON `<root>/performance/mint_costs.json`.
- `review-20260929T045636-f030ab`: `importtime_report.py --rounds 5`:
  `django_strawberry_framework.keyset` self 1318 us, cumulative 2999
  us, of package self 29037 us / cumulative 245216 us over 69
  modules; zero `cryptography` rows (the soft dependency stays out
  of package import). JSON `<root>/performance/importtime.json`.
- Superseded (probe bugs, no figures cited):
  `review-20260929T045511-0545b1` (`BenchProvenance` attribute),
  `review-20260929T045533-39fd9c` (`Periodical` kwargs).

Looks-for entries discharged `none` (the rest are Rejected below):

- N+1 / per-row queries: the module issues zero queries. Mint reads
  materialized row attributes via `value_source` (`attname` for local
  columns, the annotated alias for related-path entries); the
  only-projection extension that keeps those reads non-deferred lives
  at the caller
  (`django_strawberry_framework/connection.py::_keyset_order_state`
  via `_extend_only_projection`), traced, no deferred-load trap
  in-target. The seek predicate is a filter on the existing fetch,
  not a round trip — corroborated by the connection item's
  `count_queries.py` nested-keyset-forward 2/2/2 `batched`
  (`docs/review/rev-connection.performance.md`,
  `review-20260929T003955-e0c0a6`).
- `len(qs)` / `bool(qs)`: no queryset evaluation in the module.
- `only()` / `defer()`: not used; see the attname point above.
- Unbatched writes: no writes.
- `blog.id` vs `blog_id`: mint already reads the `attname` form.
- Repeated regex compilation: no regex in the module
  (`split_order_ref` is `startswith` / `in` checks on cold paths).
- Repeated schema / type lookups: none.
- `lru_cache` on methods (`B019`): none — `_cursor_crypto_types`
  (`lru_cache(maxsize=1)`) and `_cursor_aessiv` (`@cache`) are module
  functions, and the unbounded cache is keyed by configured secret
  (rotation list, documented at the site).
- Locks, cache reads, re-parses, extra round trips on the
  per-request path: no locks; the per-row cache reads are dict hits
  (168 ns, R4); the fingerprint is compared, never re-parsed; no
  round trips (first bullet).
- Per-row AES-SIV itself (~6 us/row): the documented contract
  (authenticated-encrypted, deterministic ciphertext for
  cross-strategy byte parity), not an implementation choice; no
  cheaper shape preserves it.

Cells: `sharded` and `pg` inapplicable by construction — the target
issues no query, references no alias, and branches on no
backend/vendor (the SQL renderer emits backend-agnostic parameterized
comparisons; backend selection lives in `lateral_fetch` /
`nested_fetch`, outside the fence). The CPU instruments measure
in-memory SQLite whatever the cell.

Freshness (`git hash-object` at read time):
`django_strawberry_framework/keyset.py` `279ad7b0`,
`django_strawberry_framework/connection.py` `1fca6266`,
`django_strawberry_framework/optimizer/nested_planner.py` `d32d1b7b`,
`django_strawberry_framework/optimizer/lateral_fetch.py` `db1ea315`.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

- R1 — eager `keyset` import at the package root (via `connection`,
  itself eager at `django_strawberry_framework/__init__.py:18`):
  self 1318 us one-time (4.5% of package self), cumulative 2999 us
  whose children the root imports regardless, `cryptography`
  provably absent from the import closure, no settings read at
  import. Lazily importing `keyset` alone would save ~1 ms of a 245
  ms import while complicating the hot module. Trigger: `keyset`
  self time exceeds 10 ms, or it gains an import-time settings read
  or an eager heavy dependency.
- R2 — shared `JSONSerializer` singleton + hoisted associated-data
  list in `_encrypt_cursor_payload`: interleaved full-mint 6041 ->
  5929 ns (-112 ns, -1.9%); component fresh-vs-shared `dumps` 1615
  -> 1583 ns (-32 ns); identical-code block medians differ by ~400
  ns (5646 vs 6041), exceeding the delta — noise, not a measured
  saving. The byte-identical variant stands in the probe as the
  re-test harness. Trigger: the mint sheds its crypto cost so the
  constructor dominates, or a tighter instrument shows a stable
  >5% delta.
- R3 — one reused `SimpleNamespace` shim across the serialize loop
  instead of one allocation per column per row: 410 -> 286 ns/column
  (-124 ns, ~250 ns/row on a ~6 us mint, ~4%). Rejected under the
  hot-path rule's plainness clause: `serialize_cursor_value` is the
  shared mint+decode-validation contract surface ("the field-authored
  round-trip surface"), and the saving needs either a restructured
  signature or a duplicated None-check in `encode`'s loop; a
  module-global shim would be thread-unsafe (resolvers run on
  threads). Trigger: the mint sheds its crypto cost, or a real-page
  profile puts shim construction above noise.
- R4 — per-row `settings.SECRET_KEY` read (137 ns) + `_cursor_aessiv`
  `@cache` hit (168 ns): the read must stay per-call for key
  rotation and `override_settings` test-safety; only the expensive
  `salted_hmac`+`AESSIV` derivation is cached, which is the right
  split. Trigger: a cached-at-import secret with explicit
  rotation invalidation.
- R5 — `cursor_columns_for` `_meta.get_field` walks (2256 ns) plus
  `declared_cursor_state_for_definition` (2839 ns) per nested plan
  build: plan-time, once per plan-cache miss against a millisecond
  plan build; offset targets cost one `getattr` (`None` return);
  the `split_order_ref` re-parse is ~100 ns of the total.
  Trigger: the derivation moves per-request or per-row.
- R6 — `keyset_seek_q` 10.8 us per request per supplied cursor:
  one `Q`-tree construction per call, single `build_keyset_seek_plan`
  per call, no repeated sub-build. Trigger: Q construction profiled
  above noise on real pages.
- R7 — `KeysetSeekPlan.uniform` set allocation per `keyset_seek_sql`
  render: sub-microsecond inside a 999 ns per-request render.
  Trigger: the render moves per-row.
- R8 — decode's re-serialization validation (`serialize` after
  `to_python`, per column per request): the field-drift /
  malformed-payload contract check; removing it would weaken a
  boundary to buy a number, which no worker does. Trigger: a
  cheaper canonical-shape check that preserves the drift detection.

Handoff: the mint path is crypto-bound (~6 us/row, inherent to the
authenticated-encryption contract) and every removable micro-cost
around it measured at noise (R2) or fails the plainness clause (R3);
the per-request figures (decode 6.9 us, seek-Q 10.8 us, seek-SQL 1.0
us, declared-state 2.8 us plan-time) are single-construction costs
with no repeated sub-work. The concurrent `truth.*` diff touches
cold raise-paths only and moves no figure. No bench-baseline figure
can move on a no-findings record; the next Performance eyes on the
surrounding pipeline should be the `connection.py` item's F1–F3
verdicts (already recorded) and any future `lateral_fetch` pass for
the SQL the seek renders into. Sibling keyset axis records were
absent at write time — the verifier should confirm no Mechanics /
Comments finding landed code this record's numbers no longer
describe.

## Verification (Performance)

Step 1 (the tree still carries the change):
`git diff d6f1f0a4c4d291b03cf14e680ab3649aeda10851 -- django_strawberry_framework/keyset.py`
sha256 `96670bf91b70e3f7e77d91ece2413b74f20c4ffaa463e8c56b34cb67b0b80043` equals
`docs/review/temp-tests/keyset/diff/pass-1.diff` sha256 `96670bf91b70e3f7e77d91ece2413b74f20c4ffaa463e8c56b34cb67b0b80043` — pass,
graded. (`## Implementation (Worker-2)` read only after this check.)

Proof lines: none owed, none run. This record is no-findings with no Proof
line and no `## Cross-axis` section; `rev-keyset.mechanics.md` carries no
Proof lines and no `## Cross-axis` section (it records their absence);
`rev-keyset.comments.md` carries 8 Comments-axis Proofs and no
`## Cross-axis (for Performance)` section. Zero Performance Proofs exist to
run verbatim, so the verbatim-run step is vacuous.

Worker-2 numbers reproduced: Worker-2 reported no Performance numbers
(prose-only; inverse proof `review_inspect.py --code-digest
d6f1f0a4c4d291b03cf14e680ab3649aeda10851:django_strawberry_framework/keyset.py
django_strawberry_framework/keyset.py` exit 0, both
`sha256:bb01f2e8fe76bba0d0884be6ec485830283e6853df51348e7507551e6549ee05`).
Re-ran verbatim in the shared tree: exit 0, both digests
`sha256:bb01f2e8fe76bba0d0884be6ec485830283e6853df51348e7507551e6549ee05` —
pass. No `before` figure exists to confirm against the bench baseline or the
`before` address; the reviewer's figures were explicitly never claimed
against the baseline (different package digest, stated in Trace).

Reviewer numbers reproduced from the recorded commands at
`review/keyset.py/verify-performance-1` (copy fresh, python 3.14.2, django
6.1, strawberry-graphql 0.324.0, in-memory SQLite
`file:dsf-bench-default?mode=memory&cache=shared`; probe blob `6acec2ca` and
`_bench_common.py` blob `253a3953` identical both sides; package digest
`b164b5bc...` -> `67e231b4...` since the tree moved, so absolute medians
compare directionally only):

- `review-20260929T051856-cc2938` exit 0, reviewer probe re-run by absolute
  path with `--json .../verify-performance-1/mint_costs.json`: all 14
  medians uniformly ~15-26% faster (encode 5646 -> 4542 ns,
  encode-before 6041 -> 4853, encode-after 5929 -> 4739, dumps fresh/shared
  1615/1583 -> 1265/1235, shim fresh/reused 410/286 -> 311/212 ns/column,
  decode 6905 -> 5563, seek-Q 10773 -> 8332, seek-SQL 999 -> 832,
  columns-for 2256 -> 1812, declared-state 2839 -> 2219, aessiv-hit 168 ->
  139, secret-read 137 -> 116 ns). Within-run A/B verdicts reproduce: R2
  shared-serializer delta -112 ns (-1.9%) vs -113 ns (-2.3%), still inside
  identical-code block spread (reviewer 5646 vs 6041, verifier 4542 vs
  4853) — noise, rejection stands; R3 shim delta -124 vs -99 ns/column,
  still ~4-5% of the mint — plainness-clause rejection stands. Round-trip
  + variant byte-identity asserts pass both sides.
- `review-20260929T051916-765689` exit 0,
  `importtime_report.py --rounds 5 --json
  .../verify-performance-1/importtime.json` (instrument `15f679c9` both
  sides): 69 modules both, zero `cryptography` rows both; keyset self 1318
  -> 1169 us, cumulative 2999 -> 2600 us; package self 29037 -> 25150 us,
  cumulative 245216 -> 206196 us. R1 verdict stands (~0.5% of cumulative,
  trigger 10 ms self far away).
- Binding note: cross-session absolutes measure drift (REVIEW.md timing
  rule), and the digests differ; the binding no-move evidence is the
  `--code-digest` identity above — executable code identical, so no figure
  can move due to this pass. The uniform ~20% shift across every row,
  including untouched shims, confirms drift, not a change.

Whole-diff reading (Performance): `pass-1.diff` is 5 hunks, 21+/13-, all
inside docstrings (module, `KeysetSeek`, `keyset_contract_error`,
`encode_keyset_cursor`, `KeysetSeekPlan`); no executable token in added or
removed lines; module first line unchanged (no TREE.md render); no import
added; no query-issuing, alias, or vendor-branching line touched — the
module still issues zero queries, so the connection item's nested-keyset
2/2/2 `batched` corroboration stands unmoved. No bench-baseline figure
moves. No number moves.

Attacks (all pass, no new finding):

1. Runtime-docstring consumer: no `__doc__` / `getdoc` / `inspect.` use in
   the target; no keyset-docstring consumer package-wide (sole grep hit is
   the target's own `.pyc`, compiled bytecode, not a consumer) —
   docstring-only edits cannot execute.
2. Hidden code: added- and removed-line executable-token greps empty; all
   five hunk contexts are docstring bodies; `--code-digest` identity is the
   inverse proof.
3. Other cells: sharded/pg remain inapplicable by construction — the diff
   adds no query, alias reference, or backend branch (static; the CPU
   instruments measure in-memory SQLite whatever the cell).
4. Other callers/flavors: single-file diff, no caller touched; no async
   surface (R11), no flavor split to diverge.
5. Import-time: 69 modules both sides, no new import edge, first line
   unchanged.

Disputes: none — Implementation records zero `disputed` findings; nothing
to judge.

Test-tier/failability: none owed — prose-only change carries no permanent
test and no gate relies on a prose finding (REVIEW.md Comments: no
before/after, no test, no failability); no `prove` manifest.

Cells unverified: none. Default cell ran twice (both exit 0); sharded/pg
inapplicable by construction, concurred.

Verdict: no-findings stands on the shipped tree. `Status: verified`.

Scratch: `docs/review/temp-tests/keyset/verify-performance-1/`
(`mint_costs.json`, `importtime.json`; no probe — the reviewer's probe was
re-run by absolute path). Runs: `review-20260929T051856-cc2938`,
`review-20260929T051916-765689` (both `review/keyset.py/verify-performance-1`,
cell=default, exit 0). Fingerprints at read time: `keyset.py` `d1a6dec2`
(baseline `279ad7b0`), `rev-keyset.performance.md` `b9cde7cb`,
`rev-keyset.mechanics.md` `04309b97`, `rev-keyset.comments.md` `d2e942ac`,
`rev-keyset.md` `bcbaf44c` (post-Implementation; Worker-2 recorded `f2f1367d`
pre-section), probe `6acec2ca`, `_bench_common.py` `253a3953`,
`importtime_report.py` `15f679c9`.

Handoff: Performance verify 1 is a clean pass on a prose-only diff — Step 1
hash-equal, zero Proofs to run, `--code-digest` identity reproduced, both
reviewer instruments re-run with A/B verdicts intact (uniform ~20% absolute
drift, digests differ, binding is code identity), whole diff read as 5
docstring hunks with no executable token, five attacks passing, no disputes,
no failability owed, no cell unverified. The sibling Mechanics record asked
this verifier to confirm no Comments finding landed code its numbers no
longer describe: confirmed — code-digest identity holds, and the
Mechanics/Comments verifiers own their own axes. Nothing is left open for a
further Performance pass.
