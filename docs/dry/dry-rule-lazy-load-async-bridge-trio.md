# DRY review: `lazy-load-async-bridge-trio`

Status: verified
Run: 0.0.15 2026-10-11-18

## System trace

Target: three `_resolve_async` closures in
`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`
(reverse :772, forward-cheap :838, forward-keyed :910), each reached only
through its `_will_lazy_load_single and async_execution()` gate (:770/:836/:908).
Each closure spells: `await run_in_one_sync_boundary(getattr, root, accessor)`
+ `except <DoesNotExist-spec>` returning None + None-gate + scoped
short-circuit + `_visible_related_object` + `isawaitable` await. Sync siblings
(:792/:860/:935), stub path (:879), many path (:670) and helpers
(`_visible_related_object` :462, `_visible_many_rows` :486,
`_optimizer_scoped_relation` :517, `_absence_catch_spec` :558,
`_will_lazy_load_*` :201/:219, `instance_accessor`) all read in full.
Whole-package censuses re-derived fresh: `run_in_one_sync_boundary(getattr,`
3/3 in the target (11 bridge calls / 8 files otherwise pass pipeline bodies);
`_visible_related_object` 1 def + 7 calls; `_optimizer_scoped_relation` 1 def +
8 calls; `isawaitable` 15 sites (trio 3 + querysets 6 + relay 4 + connection 1 +
extension 1); `_absence_catch_spec` 1 def + 2 bindings (both trio specs already
one call). Standing oracles: `test_relations_async_api.py` (6 live async rows)
+ `tests/types/test_resolvers.py` async absence/scoped rows. Prior triggers
checked, not substituted: R5 half-fired (f44 unified absence; accessor
conjunction still open), R6/R12/R13 unfired, e3/f44 verdicts stand.

## Verification

### Matrix

1. Cross-flavor: searched `run_in_one_sync_boundary` package-wide (11 calls).
   Only the trio bridges descriptor `getattr`; orders/filters/mutations/auth/
   permissions/views bridge pipeline bodies and hooks. No second
   descriptor-bridge in any flavor.
2. Sync/async twins: compared all 3 sync siblings line by line; same
   composition minus bridge/await, color is structural (sync cannot bridge,
   async must). Many `_resolve` (:748) iterates querysets via `async for`;
   connection/list_field/relay async resolvers are pipelines. No hidden twin.
3. Derived knowledge: forward `field_name` vs `accessor_name` values coincide
   per branch (owner prose: forward fields have no `get_accessor_name`, name
   IS the attribute) -- spelling, not derivation. `precomputed_key` threads
   the identically-computed key (perf only). None-order computes identical
   verdicts, and `_visible_related_object(None)` returns None anyway.
4. Round-trip: inapplicable -- one-directional bridge (sync descriptor to
   async value), no encode/decode pair anywhere in the target.
5. Other media: oracles assert data/errors, never the composition spelling;
   module/factory docstrings describe the discipline (projection). No second
   definition in tests or docs.
6. Omission: enumerated reverse/forward-cheap/forward-keyed/many/file/stub/
   connection/relay. Many uses queryset `async for` (correct mechanism); file
   direct-getattr is relations-scoped per R13 (trigger unfired); stub guarded
   by the deferral probe. Absence is not a gap.

### Challenges

- C1 new getattr error: absence-like lands once at `_absence_catch_spec`
  (f44, count 1). A bridge-only error has no plausible instance: bridge
  failures propagate identically in sync, descriptor errors are Django-owned
  (not counted). Bridge count 0.
- C2 new scoped predicate: count 1 (`_optimizer_scoped_relation`); its 8 call
  sites are consumers, listed not counted.
- C3 new visibility signature: count 1 (`_visible_related_object`); its 7
  call sites are consumers, listed not counted.
- C4 new `isawaitable` handling: trio tails are 3 of a 15-site package idiom
  spanning unrelated rules (refusal/disposal, node fetch, pipeline); each is
  a 4-line mechanical await of a Strawberry-owned `AwaitableOrValue`
  (someone else's rule, not counted). Trio-local count 0.
- C5 new accessor kind: count 1 (`instance_accessor`); forward `field_name`
  reads are the provable-identity case (Django owns forward vocabulary, not
  counted). Examined and cleared: a test double carrying
  `get_accessor_name` down the forward path is test-only; real forward
  fields never carry it.
- C0 composition-order change (None/scoped order): count 0. Both gates are
  pure optimizations with identical verdicts either way (None short-circuits
  to None at :468; scoped recheck "would only repeat the query" per the
  :517 docstring). No correctness contract, no definition.

## Findings

### F1 lazy-load async bridge (rejected -- enforcement sites, not definitions)

- Contract + variation: candidate "async single-valued lazy bridge". Axes:
  absence-spec already unified (f44, identical tuples); accessor spelling
  with provably equal values per branch; `precomputed_key` perf threading;
  None-order spelling with identical verdicts. Nothing varies by contract.
- Sites + roles: 3 closures = consumers/enforcement sites (each composes 4
  single-owned rules by name + 1 stdlib predicate;
  `pipeline_write_phase()` precedent). Definitions: `run_in_one_sync_boundary`
  (s20-verified end-state), `_absence_catch_spec` (f44), scoped pair (e3).
  Oracles: live async suite + package async rows. Projections: factory +
  owner docstrings.
- Challenges: C1-C5 + C0 above; every count is 0 or 1, none is 2+.
- Owner + lifetime: no new owner; existing owners stand. Nothing stored.
- Migration: none (zero-edit). Shrinkage 0. Machinery: none added.
- Distinct behavior: sync twins stay (color structural); many `async for`
  stays (queryset mechanism); file direct-read stays (R13). Separations
  already have prose homes (factory color paragraph, accessor forward
  clause); no new durable-home clause owed.
- Behavioral proof: standing oracles pin the observable behavior
  (lazy-load serves data, absence serves None, unscoped rechecks);
  static-reviewed -- a rejection with no observable delta owes no new
  proof. Bridge failures are loud, never silent exposure: the live
  suite's own docstring records pre-arm reads raising
  `SynchronousOnlyOperation` as a top-level error.
- Negative control: none -- the exposure verdict lives at e3's shared
  sync/async gate; the async-only remainder carries no verdict of its own.
- Coupling: none.
- Freshness: `types/resolvers.py` WT `8cd980b0`, `utils/querysets.py`
  `1b0cf162`, `utils/relations.py` `b0cc6c33`,
  `test_relations_async_api.py` `f002b718`, `tests/types/test_resolvers.py`
  `d4133fb6`. Population: whole package (`django_strawberry_framework/`,
  6 sweeps above). Contract sources: owner docstrings + live suite
  docstring + f44/e3/s20 verdicts (triggers re-checked).
- Trigger: a bridge-composition correctness contract appears (an ordering
  the composition must hold for correct rows, not just fewer queries), or
  a second module bridges descriptor `getattr`, or C-RECHECK redesigns
  the dual-color return (R12).

## Defects

None found.

## Pending execution

None -- zero-edit rejection; no proof or gate command owed.

## Judgment

Zero-edit rejection. The closures compose four owned rules by name; every
variation axis is already-unified, spelling, or perf threading; the
composition carries no correctness contract. The bar fails on all horns: no
2-definition change obligation, exposure contract owned at e3, no behavioral
drift. Triggers recorded above.

## What shrinks

- Rule: lazy-load async bridge (3 `_resolve_async` closures).
- Change: none -- rejected, zero-edit.
- Owner: unchanged (`run_in_one_sync_boundary`, `_absence_catch_spec`,
  `_optimizer_scoped_relation`, `_visible_related_object` stand).
- Net lines: 0 package, 0 tests.
- Machinery attestation: none added (no helper, driver, flag, or registry).

Index rows for Worker-0 (family decompositions, all `rejected`):

- `lazy-load-async-bridge` | owner
  `django_strawberry_framework/types/resolvers.py::_make_relation_resolver`
  (enforcement sites; definitions at the four owners above) | files
  `django_strawberry_framework/types/resolvers.py` | holding item Family
  `lazy-load-async-bridge-trio` | rejected (F1: composition carries no
  correctness contract; trigger: a composition correctness contract, a
  second bridging module, or the R12 dual-color redesign)
- `lazy-load-async-await-tail` | owner
  `django_strawberry_framework/types/resolvers.py::_visible_related_object`
  (dual-color producer; tails are per-value idiom) | files
  `django_strawberry_framework/types/resolvers.py` | holding item Family
  `lazy-load-async-bridge-trio` | rejected (C4: 3 of a 15-site package
  idiom across unrelated rules; Strawberry owns `AwaitableOrValue`;
  trigger: a package-owned await protocol with multi-line logic at 2+
  tails)
- `lazy-load-async-accessor-spelling` | owner
  `django_strawberry_framework/utils/relations.py::instance_accessor` |
  files `django_strawberry_framework/types/resolvers.py`,
  `django_strawberry_framework/utils/relations.py` | holding item Family
  `lazy-load-async-bridge-trio` | rejected (C5: forward `field_name`
  provably equals the accessor; converge forward-name-reads; trigger:
  a forward kind whose accessor diverges from `name`)

## Independent verification (Worker-2)

### Pre-read trace (formed before opening `## Findings`)

Sites: three `_resolve_async` closures in
`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`
(C1 reverse-O2O, C2 forward-cheap, C3 forward-keyed) plus three sync
siblings, the elision stub path, and the many-side `_resolve`.
Roles: closures/siblings are enforcement sites; each composes by name
the single-owned `run_in_one_sync_boundary` (bridge worker),
`_absence_catch_spec`, `_optimizer_scoped_relation`,
`_visible_related_object`, `_will_lazy_load_single`, and stdlib
`inspect.isawaitable`. Oracles: live `test_relations_async_api.py` +
`tests/types/test_resolvers.py` async rows; projections: factory and
owner docstrings. Definition counts per posited change: absence-spec
change 1 (owner); scoped/visibility-order change 0-or-1 (sequencing,
no independent logic per site); bridge-mechanism change 1 (worker
owner); key-threading 0 (identical key value, perf only); None-order
0 (De Morgan identical). Owner if it were one rule:
`types/resolvers.py`; held: not one rule, no new owner.

Own hunt (all negative): (a) second lazy-load bridge — all 11
non-trio `await run_in_one_sync_boundary` calls pass named pipeline
bodies, zero bridge descriptor `getattr`; no `sync_to_async` in
`types/`; `_will_lazy_load_*` confined to the target. (b) shareable
pure decision — strongest candidate (scoped+visible 3-line sequence
at 7 sites) is call-sequencing, enforcement per the DRY.md
`pipeline_write_phase()` precedent; a helper would need
key-threading/color-split params (machinery) and P5 already holds
(pure decisions shared, colored bodies kept). (c) P11 deletion —
every target helper carries a named rule or boundary (census
re-derived); no no-responsibility abstraction.

### Reconciliation

Full agreement with F1 on sites, roles, counts, and no-new-owner.
Two framing notes, both verdict-neutral: my trace counts the lazy
gate as a sixth composed rule where F1 folds it into the enclosing
level (same bytes, same count-1); my hunt names the 7-site
scoped+visible sequence explicitly where F1 carries it under C0/R6
(same verdict: enforcement, not definitions). Record correction
(verdict-neutral, run-13 precedent): the "11 bridge calls / 8 files"
census mixes populations — exact figures are 11 non-trio
`await` calls across 6 files (14 calls / 7 files total); the
load-bearing claim (trio-only descriptor bridge, all other calls
pass bodies) re-verified true, and axis 1 names all 6 call files.

### Checks

Freshness re-hashed: all five blobs match (`8cd980b0`,
`1b0cf162`, `b0cc6c33`, `f002b718`, `d4133fb6`). `isawaitable`
census re-derived exactly (15, same per-file split). Scoped diff
empty (`git diff a26cc304 -- package/tests/examples` prints
nothing); all 8 untracked files pre-date the run (2026-10-10
mtimes + plan resume note), none item-added. Matrix judged axis by
axis against the real surface: axis 1/2/3/6 searches re-derived
fresh and concur; axis 4 inapplicability sound (one-directional
bridge); axis 5 sound (oracles pin data/errors). Prior rows
re-checked, not substituted: R5 genuinely half-fired (f44 unified
absence, accessor conjunction open — trigger needs both, stands);
R6/R12/R13 triggers unfired at current bytes. F1 + 3 index rows
each carry contract difference + trigger. Artifact prose: no
process-provenance narrative, `path::Symbol` citations, bare `:NN`
allowed in `dry-*.md` scratchpads; 136 lines + What shrinks,
within caps. `## Pending execution` carries no entries (None
convention matches the sibling zero-edit artifact). Ruff:
vacuous — zero touched paths, not run (never over `.`).
No defects found; none filed.

Verdict: verified. Zero-edit rejection stands: the trio composes
owned rules by name, every variation is spelling/perf/provable
identity, and the composition carries no correctness contract.
