# DRY review: `shape-build-get-or-store`

Status: verified
Run: 0.0.15 2026-10-01-12

## System trace

Owner candidate re-derived, not inherited:
`django_strawberry_framework/utils/inputs.py::get_or_store_shape_build`
(`utils/inputs.py:978-1005`; walk at `:1000-1005`) is the get-or-store
spine the write-flavor shape caches share. The spine body is byte-identical
HEAD vs WT (no `@@` hunk covers `:978-1005`).

Riders re-censused at WT bytes (all composing by name; every composing line
byte-identical HEAD vs WT — zero `^[+-]` dirt lines mention the spine or its
riders across the three files):

- `mutations/sets.py::cached_build_input` (`:217-251`, spine call `:251`) —
  guard-before-cache-lookup core; sole caller is the form seam.
- `mutations/sets.py::_materialize_input_for` (`:1621-1632`) — model bind,
  pre-build `MutationInputShape.cache_key`, generator factory.
- `rest_framework/inputs.py::dedupe_serializer_input_shape` (`:1433-1454`,
  spine call `:1450`) — post-build descriptor-keyed dedupe.
- `forms/sets.py` (`:367-372`) — transitive consumer via `cached_build_input`.

Nominated inline sites re-read at WT bytes:

- Layer-6 (`make_dynamic_set_getter.<get_set_class>`,
  `utils/inputs.py:930-943`): `cache.get` `:931` → None-check `:932-933` →
  `create_dynamic_set_class` `:934-941` → store `:942` → return `:943`.
  Walk lines HEAD-clean (the one nearby hunk touches only the closure
  `__name__`/`__qualname__` lines below).
- Range (`filters/inputs.py::_build_range_input_class`, `:861-884`):
  per-instance lazy attach `:864-873`, `cache.get` `:874` → None-check
  `:875-876` → name + `build_input_class` `:877-882` → store `:883` →
  return `:884`. Line `:877` (`truth.name` prefix) is hunt truth-migration
  dirt; the rest of the walk is HEAD-clean. (Would-be touch point under
  CONFIRM; moot under this verdict — recorded, untouched.)

Whole-package sweep for the mechanism (fresh; instrument + counts under
`### Enumeration`) finds SIX walk-shaped sites, not three: spine, Layer-6,
Range, plus `connection.py::_window_edge_class` (`:341-353`, WT-ONLY
concurrent dirt — at HEAD the function is a pure derivation with no memo),
`optimizer/walker.py::_forward_names` (`:380-402`, stability-gated), and
`optimizer/selections.py` converted-selections memo (`:196-257`, optional
per-execution memo). Twelve further memo/registration spellings were read
and excluded with contract differences (see Exclusions).

Oracles re-read and re-executed (one focused `--no-cov` run, 6/6 green):
spine store/reuse + write-flavor import gate
(`tests/utils/test_inputs.py:839/:854`), Layer-6 collapse/passthrough +
both-families-share-skeleton (`:762/:791`), Range instance-caching +
owner/field/scalar keying (`tests/filters/test_inputs.py:1449/:1461`;
live-tier owned names cited in the Range test docstring).

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. Write flavors (model / form /
   serializer) all compose the spine; set flavors (Layer-6, Range, BFS
   factory, materialize ledger, lookups memo), optimizer (two LRUs,
   walker memo, selections memo), connection (provenance cache, edge
   derivation), registry (enum protocol), types (definition memos,
   choices-enum split) each memoize under their own subject, key regime,
   and lifetime. No cross-flavor memo rule found beyond the spine's own
   write-flavor scope (which its docstring and gate both state).
2. Sync/async twins — INAPPLICABLE with reason. The walk is a synchronous
   dict walk at every site (six `def`s, zero awaits); no site suspends,
   crosses a sync boundary, or has an async twin. Checked the six bodies.
3. Derived rather than repeated knowledge — SEARCHED. Each key regime is
   derived once at its owner (`make_set_meta_cache_key`, Meta fingerprint;
   `mutation_input_shape.cache_key`; `SerializerInputShape.cache_key`;
   Range `(owner, field, scalar)` tuple; walker `(type, id(converter))`;
   selections node-id key). No duplicated derivation; only the 5-line walk
   idiom repeats, which is the rejected claim below.
4. Inverse / round-trip pairs — SEARCHED, none. The walk has no inverse;
   each dict's clear is owned once (write-flavor `make_shape_build_cache`
   pairs on the `registry.clear()` bus; connection clears; LRU internal
   eviction; definition memos live with the definition; Layer-6
   deliberately unclearable per verified f32 E-clear). No duplicated
   clear ownership.
5. Contracts restated in another medium — SEARCHED. Oracles pin behavior
   independently (own dicts, own keys, identity assertions — never read
   from the spine); the write-flavor import gate pins exactly the
   write-flavor scope (projection consistent with the three direct call
   sites re-censused above); the spine, Range, and `cached_build_input`
   docstrings state mutually consistent scope clauses, each verified
   against its body. No restated contract moves with the walk.
6. Enforcement by omission — SEARCHED. Every repeated-build site found has
   its own memo or a documented reason for none (walker uncacheable reads
   bypass by design; HEAD edge derivation unmemoized, WT dirt memoizes it
   as concurrent work — observed, out of scope; Layer-6 no-clear is
   verified-deliberate f32 E-clear, not a gap). No member lacks a guard a
   contract source requires. No defect.

### Enumeration

Instruments (all at WT bytes): `cache\.get(\|cache\[` census (22 hits =
20 code + 2 comment non-sites); `.get(` census (369 hits, triaged by
mechanism); `setdefault` census (19 sites); memo-name sweep (`_memo`,
`_cache`, `IdentityMap`, `ledger`, `input_object_types`, collision
registries, `register_enum`/`get_enum`, `index`). Every hit homed:

- Walk-shaped (get → None-check → build → store → return): 6 — spine
  (definition, write-flavor scope), Layer-6, Range, edge (WT dirt),
  walker (stability-gated), selections (optional memo). Verdict: the
  five inlines are independent memos, each excluded (F1).
- Consumers: 3 direct spine calls + 1 transitive + 2 spine oracles +
  1 scope gate. Listed, not counted.
- Excluded mechanisms: BFS graph-ensure, materialize raise,
  provenance-check, copy-out, 2 LRUs + exec-memo tier, 2 definition
  memos, enum registration split, registry registration, relay
  read-only index, 19 setdefault accumulations, 2 comment non-sites.

### Challenges

Variation axes per the nomination (key identity, cache location, build
timing) plus every walk-level change constructible. Counts are
authoritative WALK definitions forced to move together (consumers,
oracles, projections listed in F1, never counted):

- CH-key (add/rename a key axis, e.g. exclude-semantics or a new scalar
  discriminator): moves the owning key derivation only — each
  single-owned (`make_set_meta_cache_key`, `mutation_input_shape`,
  `SerializerInputShape`, Range tuple, walker key, selections key).
  Walk untouched. Count 0.
- CH-lifetime (change a cache's dict/clear — e.g. f32 E-clear's trigger,
  Layer-6 gaining eviction): moves that subsystem's dict + clear only.
  Walk untouched. Count 0.
- CH-timing (pre- vs post-build rekeying): moves the call-site keying
  discipline (`cached_build_input` guard-before-lookup,
  `dedupe_serializer_input_shape` build-first). Walk untouched. Count 0.
- CH-miss-signal (None-check → sentinel/`in`-check): DISCHARGED as
  implausible — no walk site can store None (values are classes/records
  by construction); the sites that cache None/False (definition memos)
  already use key-absence and are excluded. No contract source wants
  None-caching. No count.
- CH-eviction (bound the caches): moves ZERO sites together — actively
  breaking where identity is load-bearing (Layer-6 collision `is`
  checks, Range same-class expectation, dedupe idempotency) and
  pointless where scope already bounds (per-execution selections memo);
  each site's boundedness is already decided locally (the LRUs are
  bounded exactly where wanted). Count 0.
- CH-hit-validation (stale check on hit): validity is per-site
  (registry clears, finalized gates, provenance record). No site wants
  a walk-level check. Count 0.
- CH-reentrancy (guard a factory re-entering its cache): no factory
  re-enters (`type(...)`, `build_input_class`, input walks are all
  non-recursive through their caches; nested serializer shapes dedupe
  under distinct keys). Implausible. Count 0.
- CH-observability (miss counter/hook): no consumer, no schema-build
  logging surface. Implausible. Count 0.
- CH-locking (serialize check-then-act): build sites race-free by
  construction; request-path memos decide races locally (optimizer
  `suppress(KeyError)` arms) or are race-benign (pure derivations).
  A uniform lock moves none. Count 0.
- CH-copy-out (return a copy on hit): wrong for class identity; the one
  site needing it (lookups memo) has it locally. Count 0.

No posited change moves ≥2 walk definitions together. Per DRY.md that is
independence, even where the text is identical.

## Findings

### F1: the shape-build get-or-store walk is a shared idiom, not a shared rule (REJECT, zero-edit)

- Contract + variation: the nominated rule — unbounded None-signal
  get-or-store returning THE stored object. Its genuine variation (key
  regime, cache dict + lifetime, build expression, keying discipline)
  lives at call sites BY THE SPINE'S OWN DESIGN ("Descriptor-vs-name-set
  identity and each flavor's cache dict stay at the call site"). What
  remains as "the rule" is 5 lines of Python memo spelling with no
  plausible shared variation (Challenges: every count 0).
- Sites + roles: definition `utils/inputs.py::get_or_store_shape_build`
  (write-flavor scope — stated by its docstring "the three write-flavor
  shape caches" and pinned by the write-flavor import gate, both
  verified fresh against the 3-direct + 1-transitive consumer census);
  consumers `mutations/sets.py::cached_build_input`,
  `mutations/sets.py::_materialize_input_for`,
  `rest_framework/inputs.py::dedupe_serializer_input_shape` (direct),
  form seam (transitive); five inline memos, each an independent
  definition of its OWN rule (Layer-6 set synthesis, Range per-instance
  identity, walker stability-gated names, selections execution memo,
  edge derivation) — excluded below, not members; oracles (6 tests,
  re-run green); projections (spine / Range / `cached_build_input`
  docstrings, scope gate).
- Challenges: CH-key / CH-lifetime / CH-timing count 0 on the walk
  (each moves a single-owned call-site derivation); CH-miss-signal /
  CH-reentrancy / CH-observability discharged implausible;
  CH-eviction / CH-hit-validation / CH-locking / CH-copy-out count 0
  (each decided per-site already, or actively breaking).
- Owner + lifetime: no new owner (rejected). The spine keeps its
  write-flavor scope. Per-dict lifetimes (principle 4; walk-agnostic):
  write-flavor per-pass dicts cleared on `registry.clear()`; Layer-6
  process-lifetime, never cleared (verified f32 E-clear — keys embed
  model identity); Range filter-instance lifetime; selections
  per-execution (None outside); walker finalized-gated process memo;
  connection IdentityMaps test-cleared on the bus.
- Migration: none — zero edits. Folding the inlines in would add an
  import + lambda-wrapped builds + an AST-census gate with six
  exclusions (each needing its own negative control) while relieving
  zero evidenced change obligations: machinery, not DRY ("relieving no
  change obligation ≠ finding, whatever it moves").
- Distinct behavior: the five memos stay inline; differences + triggers
  in Exclusions. The spine's riders are one rule by SHARED SUBJECT
  (write-flavor input builds), lifecycle (per-pass cleared), and
  discipline (guard-before-cache/dedupe + the scope gate) — not by
  walk text. Forcing Meta-fingerprint keys and live-object identity
  keys under the spine's descriptor-vs-name-set axes would stretch its
  contract past its documented variation until it owns nothing but
  the idiom.
- Behavioral proof: static-reviewed — zero-edit verdict, no behavior
  changes; current behavior pinned by the 6 re-run oracles (command in
  Implementation). No `proof:` entry owed.
- Structural gate: none owed (rejection). The existing write-flavor
  gate stands with scope unchanged; Layer-6 (same module — an import
  assertion would be vacuous) and Range need no pinning precisely
  because they are not riders.
- Coupling: none.
- Freshness: all fingerprints WT == item baseline (zero drift since
  dispatch); HEAD pins match the dispatch (`utils/inputs.py`
  WT `8839b38d` / HEAD `0b7d353c`; `filters/inputs.py` WT `993f365c` /
  HEAD `08516597`; HEAD `dd0b6691`; baseline `0412709a`). Full table:
  `mutations/sets.py` WT `a1035397`/HEAD `50f9d6a1`,
  `rest_framework/inputs.py` WT `af8cea5c`/HEAD `6ad29171`,
  `forms/sets.py` WT `b8643610`/HEAD `76520347`,
  `connection.py` WT `6c4b01f9`/HEAD `38491372`,
  `filters/sets.py` WT `17dae905`/HEAD `76abccb0`,
  `types/definition.py` WT `e79d7129`/HEAD `ff80ef02`,
  `optimizer/extension.py` WT `8e3fe7c1`/HEAD `b7b6c434`,
  `optimizer/walker.py` WT `b71db9e0`/HEAD `57a27b4a`,
  `optimizer/selections.py` WT `3b1c0bf8`/HEAD `ed22de27`,
  `types/converters.py` WT `97f3399e`/HEAD `312bd290`,
  `registry.py` WT `e95c39e7`/HEAD `5480c2eb`,
  `optimizer/_context.py` `274a138b` (clean),
  `tests/utils/test_inputs.py` WT `220fecd2`/HEAD `ef303037`,
  `tests/filters/test_inputs.py` WT `5e124e4e`/HEAD `11d6f32b`.
  Searched population: package-wide censuses above (22 + 369 + 19 +
  memo-name sweep). Modules excluded on body strength: every site in
  Exclusions (each re-read at WT bytes, line-cited).

### Exclusions (contract difference plus reconsideration trigger each)

- E-layer6 (`utils/inputs.py:930-943`): set-CLASS SYNTHESIS from Meta
  kwargs (Layer-6 construction, existence homed at DRY-squeeze WP-D per
  verified f32 — not re-litigated), process-lifetime never-cleared memo
  (verified f32 E-clear), normalized-Meta-fingerprint key regime
  (model + fields + extras incl. exclude/alias axes — outside the
  spine's descriptor-vs-name-set axes). Spine = input builds,
  per-pass cleared. Trigger: a walk-level requirement arising in BOTH
  the write-flavor and Layer-6 caches (miss signal, hit validation,
  eviction, re-entrancy guard, observability) — the first co-moving
  walk change; E-clear's eviction trigger alone is insufficient
  (dict-level, not walk-level). Specified home: spine docstring riders
  clause (not landed — zero-edit precedent).
- E-range (`filters/inputs.py:861-884`): per-INSTANCE cache with lazy
  attach, live-object generation-identity key (owner class + field +
  scalar; the keyed oracle mutates `field_name` mid-test), filter-instance
  lifetime, own documented caching contract ("Classes are cached on the
  filter instance by their full generation identity"). Same generic
  trigger. Specified home: spine docstring riders clause (not landed).
  Concurrent-work note: `:877` is hunt truth-migration dirt — the
  would-be CONFIRM touch point; untouched.
- E-walker (`optimizer/walker.py:380-402`): stability-gated runtime
  derivation memo — uncacheable reads bypass get AND store entirely
  (`:382-389`), a walk-level bypass the spine has no form for;
  optimizer name-map subject. Trigger: gate removal (all reads
  cacheable) plus a co-moving walk change. Specified home: spine
  docstring (not landed).
- E-selections (`optimizer/selections.py:196-257`,
  `optimizer/_context.py:326-329`): optional execution-scoped memo
  (None outside a managed execution; read `:203-205` and store `:257`
  both presence-gated); per-execution lifetime. Trigger: memo made
  unconditional plus a co-moving walk change. Specified home: spine
  docstring (not landed).
- E-edge (`connection.py:341-353`, decl `:1449-1465`): WT-ONLY unlanded
  concurrent dirt (at HEAD the function is a pure derivation with NO
  memo — verified via `git show HEAD:`); identity-keyed NON-dict
  container (`truth.IdentityMap`, `utils/truth.py:625` — plain Generic,
  not a dict subclass: structural bar to the `dict`-typed spine);
  runtime derivation subject. Observed-not-decided-final: excluded on
  current bytes; re-check when the hunt lands it. Trigger: landing as
  an unconditional plain-dict memo plus a co-moving walk change.
- E-enum (`types/converters.py:784-794` + `registry.py::register_enum`
  `:627-636` / `get_enum`): registration-protocol split — the store
  half RAISES on distinct re-registration and read/store are registry
  methods; already single-owned by verified family
  `type-registry-enum-cache` (owner TypeRegistry F4). Folding into the
  spine reverses verified ownership. Trigger: registry enum protocol
  redesign. Home: that family (owned elsewhere — no new home).
- E-register (`registry.py` registration methods): value supplied by
  the caller + raise-on-distinct; no build expression. Different
  mechanism, never the walk. Trigger: none.
- E-relay (`types/relay.py:1006-1018`): function-local read-only index,
  no store into any persistent cache. Not the mechanism. Trigger: none.
- E-setdefault (19 sites, 14 files): grouping accumulation
  (`setdefault(k, []).append`), nested-map ensure, first-wins put, env
  default — no build expression anywhere. Not the mechanism. Trigger:
  none.
- E-bfs (`utils/inputs.py:1859-1860` + `:1876-1910`): graph-ensure
  building N classes per call with the collision gate interleaved, the
  store in `_build_class_type`, return via property. Not a single-slot
  walk. Trigger: reduction to an unconditional single-slot walk
  (implausible — the BFS needs its gate).
- E-materialize (`utils/inputs.py:1465-1481`): idempotency-plus-RAISE;
  a same-name distinct-class entry raises instead of building — no miss
  path exists. Trigger: raise removal (breaks Decision 9).
- E-provenance (`connection.py:1653-1687`): hit validates
  `cached.definition is definition` else raises; stores a record and
  returns a PROJECTION (`.connection_type`) — not identity return.
  Trigger: provenance-check removal.
- E-copyout (`filters/sets.py:192-199`): hit returns `list(cached)`,
  equal-but-distinct, so callers cannot corrupt the memo (documented).
  The rule returns THE stored object. Trigger: callers audited
  non-mutating plus copy removal.
- E-lru (`optimizer/extension.py:636-650` doc-key; `:1384-1426` plan +
  `:1402-1405` exec-memo tier): bounded + `move_to_end` promotion with
  race guards + eviction sweeps + cacheability gate + second
  per-execution tier. Trigger: unbounded redesign (memory blowup — no).
- E-defmemo (`types/definition.py:317-335`, `:353-357`): key-absence
  miss signal (`in`-then-`[]`) caching None (`_related_target_cache`)
  and False (`_custom_id_resolver_cache`) results; the rule's miss
  signal is None-absence. Trigger: values made non-None-able plus
  signal unification (related-target None is semantic — unlikely).
- E-comments (`types/resolvers.py:660`, `utils/querysets.py:3834`):
  comment non-sites. Not code. Trigger: none.

## Defects

None. No non-duplication bugs found while tracing. Concurrent-work
observations (out of scope, untouched, recorded for freshness only):
the `_window_edge_class` memo walk + `IdentityMap` declarations are
WT-only hunt dirt; `utils/truth.py` / `utils/lazy.py` remain untracked;
the Range `:877` prefix line and the Layer-6 closure-naming lines are
truth-migration hunks; rider composition lines are byte-identical
HEAD vs WT.

## Pending execution

None. Zero-edit verdict: every proof is static-reviewed over bodies
read at WT bytes, corroborated by the executed 6/6 oracle run below.
Cell typing: `default` executed (that run, shared venv); `sharded` and
`pg` are `inapplicable by construction` — the family decides
construction-time class-derivation memo identity (dict walks, key
regimes, no queryset, alias, or dialect decision); cache keys embed
model identity but no query is built. Worker-2 judges the typing.

## Judgment

REJECT: the Layer-6, Range, walker, selections, and edge memos share
Python's memo spelling with the `get_or_store_shape_build` spine, not
its rule. No posited change moves ≥2 walk definitions together; the
spine's riders are one rule by shared subject, lifecycle, and
discipline — none of which the inlines share. The spine keeps its
write-flavor scope; the inlines stay as the independent memos they
are, each with its contract difference and trigger above. Zero edits,
zero defects.

## Implementation (Worker-1)

No production or test edits (REJECT, zero-edit verdict) and no new
tracked files besides this artifact (untracked until Worker-0
records it). No ruff run — zero tracked `.py` touched, vacuous, none
owed (f32 precedent). No workspace run — no source-mutating proof
exists to need one. Concurrent dirt explicitly untouched (see
`## Defects` observations).

Focused oracle corroboration (one `--no-cov` run, shared tree, exit 0):

```text
uv run pytest -n0 --no-cov \
  tests/utils/test_inputs.py::test_get_or_store_shape_build_stores_on_miss_and_reuses_on_hit \
  tests/utils/test_inputs.py::test_write_flavor_shape_caches_share_get_or_store_owner \
  tests/utils/test_inputs.py::test_make_dynamic_set_getter_collapses_equivalent_meta_and_passthroughs_explicit \
  tests/utils/test_inputs.py::test_filter_and_order_dynamic_caches_ride_make_dynamic_set_getter \
  tests/filters/test_inputs.py::test_build_range_input_class_is_cached_on_the_filter_instance \
  tests/filters/test_inputs.py::test_build_range_input_class_cache_is_keyed_by_owner_field_and_scalar
6 passed in 2.88s
```

Type gates (shared venv, whole-scope, own runs):

```text
uv run basedpyright → 0 errors, 0 warnings, 0 notes
uv run python scripts/check_any.py → 128 allowed use(s) of Any at 89 site(s)
uv run python scripts/check_truthful_reads.py --check → 119 file(s); errors 0
```

Pins: HEAD `dd0b6691` unmoved; `ITEM_BASELINE=0412709a`; WT == baseline
on all 16 fingerprinted files (table in F1); dispatch pins confirmed
(`8839b38d`/`0b7d353c`, `993f365c`/`08516597`).

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (own trace from fresh reads of
both indexed targets at WT bytes, the `cache.get(` / `memo[` /
`cached = *.get(` package censuses, every consumer, and `git show HEAD:`
for the connection sites).

### Own sites + roles (WT lines)

- S-spine — `django_strawberry_framework/utils/inputs.py::get_or_store_shape_build`
  (:978-1005): DEFINITION. Unconditional get-or-store over an always-present
  dict, `is not None` hit-test, factory-on-miss, always stores. Values never
  `None` (classes / `(cls, shape)` pairs). Docstring scopes it to the three
  write-flavor shape caches.
- S-layer6 — `django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter.get_set_class`
  (:922-943; walk :931-943): walk-shaped candidate. Same 4-line shape; key is
  the Layer-6 meta cache key; miss path builds via `create_dynamic_set_class`
  (raises `ConfigurationError` on missing/non-model `model`); class-level cache
  with heavy-namespace-clear lifetime.
- S-range — `django_strawberry_framework/filters/inputs.py::_build_range_input_class`
  (:861-884; lazy per-instance slot :864-873, walk :874-884): walk-shaped
  candidate. Same shape plus its own cache-container lifecycle (slot created on
  the filter instance); key `(filterset_cls, field_name, inner)`.
- S-edge — `django_strawberry_framework/connection.py::_window_edge_class`
  (:341-352): walk-shaped but WT-ONLY — `git show HEAD:` shows the function
  computing uncached (`type_def` … `return cast(…)`), and HEAD has no
  `_window_edge_class_cache` symbol at all. Observed, not decided-final;
  uncommitted concurrent work, no verdict can rest on it.
- S-walker — `django_strawberry_framework/optimizer/walker.py::_forward_names`
  (:381-402; walk :391-401 under the `:382-389` cacheability gate):
  walk-shaped with a load-bearing gate (caches only when finalized +
  converter present, else builds uncached).
- S-sel — `django_strawberry_framework/optimizer/selections.py` faithful-mirror
  converter (:196-258; hit :203-205, store :254-258): walk-shaped with an
  OPTIONAL per-execution memo (`memo is None` → no caching) plus the
  single-node `id` fast path.
- Consumers, direct (3 call expressions of the spine): CONSUMER each —
  `django_strawberry_framework/mutations/sets.py::cached_build_input` (:251,
  guard-then-get-or-store); `django_strawberry_framework/mutations/sets.py::_materialize_input_for`
  (:1621, model bind); `django_strawberry_framework/rest_framework/inputs.py::dedupe_serializer_input_shape`
  (:1450, post-build dedupe).
- Consumers, transitive (callers of those wrappers): CONSUMER each —
  `django_strawberry_framework/forms/sets.py::_cached_build_form_input` (:367 →
  `cached_build_input`); `django_strawberry_framework/rest_framework/inputs.py::_dedupe_and_materialize_nested`
  (:1474 → dedupe); `django_strawberry_framework/rest_framework/sets.py` top-level
  bind (:283 → dedupe); `django_strawberry_framework/mutations/sets.py` model-default
  bind (:1354 → `_materialize_input_for`).
- Exclusion population (own sweep; every `cache.get(`/`memo[`/`cached = *.get(`
  site plus the `in`+`[]` memos): `django_strawberry_framework/filters/sets.py:192-200`
  (lookups copy-out: `is None` hit-test + `list(cached)` on EVERY read);
  `django_strawberry_framework/types/definition.py:317-335` (finalized-gated,
  `None`-cacheable via `in`); `:353-357` (`in`+`[]` bool memo);
  `django_strawberry_framework/optimizer/extension.py:636-652` (LRU promotion +
  bounded eviction + uncacheable fallback), `:1384-1431` (two-tier LRU +
  hit/miss counters + cacheable-gated store), `:1607-1623` (optional
  per-execution memo); `django_strawberry_framework/connection.py:1653-1687`
  (provenance-checked hit: raises when the cached entry's definition is not the
  caller's; committed at HEAD :1585-1619, only the `IdentityMap` typing is WT
  dirt); `django_strawberry_framework/rest_framework/serializer_converter.py:969-979`
  (build-ALWAYS + verify-on-hit + raise on member-set divergence);
  `django_strawberry_framework/utils/inputs.py:1465-1481` (materialize
  get-or-raise: idempotent same-class, raise distinct-class);
  `django_strawberry_framework/registry.py:627-635` (enum register-or-raise);
  `django_strawberry_framework/utils/inputs.py:1843-1860` (BFS
  collision-registry get-or-raise + `not in` graph-ensure);
  `django_strawberry_framework/sets_mixins.py:407-416` (`expanded_once`:
  reentry guard + build-owned cache-write);
  `django_strawberry_framework/utils/querysets.py:1966-2036` (cycle-termination
  memo, stores BEFORE complete); `django_strawberry_framework/rest_framework/resolvers.py:894-915`
  (freeze memo + active-set cycle guard); stdlib `lru_cache` sites
  (`keyset.py:444`, `relations.py:478/510`, `permissions.py:243`,
  `strings.py:68` — decorator mechanism, not hand walks). Pure reads with no
  store (`types/resolvers.py:672`, `types/relay.py:362`) are out of population.

### Own change challenges + definition counts

- P1 — route Layer-6's walk through the spine
  (`get_or_store_shape_build(cache, cache_key, lambda: create_dynamic_set_class(…))`):
  mechanically behavior-preserving, but relieves NO change obligation — key
  derivation, normalize, explicit-passthrough, create-time raises, and the
  class-level heavy-clear lifetime all stay at the getter. Every REAL change
  still lands on exactly one site → count 1 per change (independence).
  Consolidation would be indirection without obligation relief (principle 11).
- P2 — route Range's walk through the spine: same as P1, plus the per-instance
  slot lifecycle stays → count 1 per change (independence).
- P3 — change the hit-test to key-presence (`in`) so `None` values memoize:
  count 0 — inapplicable to spine/Layer-6/Range (values never `None`);
  the definition memos already use `in`.
- P4 — add LRU eviction/bounding to the walk: sites do NOT move together.
  Layer-6 actively vetoes (evict → re-create → same-name DISTINCT class →
  BFS duplicate-name collision / `is`-identity breakage); write-flavor
  per-pass caches gain nothing; per-instance / request-scoped sites have no
  bound to enforce. Not one rule.
- P5 — add hit/miss observability to the walk: no consumer; speculative →
  count 0.
- P6 — unify the gated (walker/definition), LRU (extension), provenance
  (connection), copy-out (lookups), verify-on-hit (serializer enum), and
  `None`-caching (definition) arms behind `(cache, key, factory)`: impossible
  without mode flags (principle 5); each arm's extra semantics is load-bearing
  (proven above per site). Count 1 per site per change.

### Owner I would choose

No consolidation. The spine keeps its write-flavor scope (3 direct call
expressions + transitive flavor binds); S-layer6 / S-range / S-walker / S-sel
keep their own walks with their own lifetimes (`make_shape_build_cache`
per-pass vs class-level heavy clear vs per-instance slot vs finalized-gated
vs per-execution frame — principle 4 lifetimes differ, so not one rule). If a
future cross-cutting memo policy ever needed one home it would be
`utils/inputs.py` beside the spine; no such change exists. Reconsideration
trigger: a walk-level semantic (e.g. a lock, a bound, a hit-test change) that
every lifetime above must share — implausible as one rule given the lifetimes.

## Reconciliation (Worker-2 vs Worker-1)

Verdict: AGREE — REJECT stands. My independent trace (sites, roles,
counts P1-P6, owner: no consolidation) converges with W1 on every
decision-relevant point, and my independent consolidation search over a
strictly larger census (below) finds no real consolidation. All
differences are record-level, cured by addition here; none requires a
W1 re-trace or re-decision.

### Convergences (verified on bodies, not inherited)

- Same owner candidate, same spine lines; W1's six walk-shaped
  sites all check out with same roles (a seventh, C3 below, extends
  the census); edge WT-only confirmed via `git show HEAD:` (no
  `_window_edge_class_cache` symbol at HEAD; WT decl `:1449-1465`).
- Same 3 direct spine call expressions (`mutations/sets.py:251`,
  `:1621`, `rest_framework/inputs.py:1450`).
- Instruments re-derived EXACT: `cache.get(|cache[` 22 = 20 code + 2
  comment non-sites (`types/resolvers.py:660`,
  `utils/querysets.py:3834`, both `#` lines); `.get(` 369; setdefault
  19 sites / 14 files (incl. the `truth.py:691` `def`).
- 13 of 16 exclusions verified line-by-line (E-layer6, E-range,
  E-walker, E-selections, E-edge incl. the `IdentityMap(Generic)`
  non-dict bar at `utils/truth.py:625`, E-enum, E-bfs, E-materialize,
  E-provenance, E-copyout, E-lru, E-defmemo, E-comments); E-register
  scope coherent with E-enum (non-enum registration methods
  `register_definition`/:460 + `:482`/`:289`/`:81` — value supplied,
  raise-on-distinct, no build; no double-count); E-relay
  `:1006-1018` is a function-local read-only index as claimed.
- f32 E-clear grounding real (`dry-rule-dynamic-set-class-getter.md:389`);
  Layer-6 no-clear verified (neither `_dynamic_*_cache` has a `.clear`).
- Challenge counts converge: my P1/P2 = independence (count 1 per
  real change, obligation-free fold); P3/P5 = 0; P4 = sites do not
  co-move (Layer-6 veto); P6 = mode-flag bar. W1's seven 0s +
  implausibles match.
- Matrix axes 1-6 judged sound on reasons (axis 2: six sync `def`s,
  zero awaits, no twins — reason holds); sharded/pg
  `inapplicable by construction` correctly typed (construction-time
  dict walks + request-path name/AST memos; no queryset, alias, or
  dialect decision anywhere in the family).
- Zero-edit proved (`git diff 0412709a -- .` minus plan is empty);
  ruff vacuous (zero tracked `.py` touched); AGENTS.md prose rules
  hold (artifact is a `docs/dry/dry-*.md` scratchpad artifact, so raw
  `:NN` cites are allowed; `path::Symbol` form used; 10-group link
  scaffold present; no provenance in code — no code touched).

### CORRECTION C1 — transitive census 1 → 4 (W0-h)

W1's "1-transitive" counts only the form seam. True transitive edges
(callers of the three direct wrappers, all composing by name):
`forms/sets.py:367` (`_cached_build_form_input` → `cached_build_input`),
`rest_framework/inputs.py:1474` (`_dedupe_and_materialize_nested` →
dedupe), `rest_framework/sets.py:283` (top-level bind → dedupe),
`mutations/sets.py:1354` (model default → `_materialize_input_for`).
Zero second bodies either way — strengthens single-ownership.

### CORRECTION C2 — rider byte-identity clause narrowed (W0-h)

"Zero `^[+-]` dirt lines mention the spine or its riders" overclaims:
one changed line at `mutations/sets.py:1354`
(`cls.__name__` → `truth.name(cls)`, truth-migration, at the missed
transitive caller above) mentions `_materialize_input_for`. The
COMPOSING lines (spine calls `:251`/`:1621`/`:1450` + wrapper bodies)
are byte-identical HEAD vs WT — verified: no `^[+-]` line matches
composing-call patterns. Substance stands; clause corrected.

### CORRECTION C3 — walk-shaped count 6 → 7 (W0-a/i)

W1 missed `optimizer/extension.py::_build_cache_key` `:1607-1623`
(optional per-execution id-memo: `memo.get` → `is None` → build →
store → return) — exactly walk-shaped under W1's own definition, same
family as S-sel. Excluded (Worker-2): optional memo (recompute
outside `on_execute`), `id(operation)` key, `(doc_key, relevant_vars)`
value, `_cache_key_parts_memo` lifetime. Trigger: memo made
unconditional plus a co-moving walk change. Pairwise vs S-sel: same
idiom, different memo/subject/key/value — a shared optional-memo
helper would own ~6 lines and relieve no obligation (principle 11).
No consolidation.

### CORRECTION C4 — three further missed exclusions (W0-i)

- M1 `rest_framework/serializer_converter.py:969-979` (serializer
  choice-enum memo): build-ALWAYS + verify-on-hit + raise on
  member-set divergence. Different mechanism from E-enum's
  register-or-raise (different subject/store/equivalence — checked
  pairwise, no consolidation). Trigger: verify-on-hit removal plus
  pre-build keying.
- M3 `sets_mixins.py:407-416` (`expanded_once`): get-or-delegate with
  reentry guard; the STORE is owned by `build()`, not the walk.
  Trigger: guard removal plus walk-owned store (breaks cycle safety).
- M4 `utils/querysets.py:1966-2036` (reconstructor cycle memo) +
  `rest_framework/resolvers.py:894-915` (freeze memo + active-set):
  store-BEFORE-complete inverts the spine's order; graph-traversal
  mechanism, not build caching. Trigger: none statable short of
  replacing the traversal (recorded as mechanism-gain: a miss-gated
  build cache appearing in either traversal).
- Out-of-population confirmed (pure reads, no store):
  `types/resolvers.py:672`, `types/relay.py:362`; `lru_cache` sites
  are stdlib-decorator mechanism, not hand walks.

### CORRECTION C5 — freshness additions (W0-f)

W1's 16 fingerprints re-hashed 16/16 EXACT (zero drift). Missing rows
supplied (WT/HEAD): `types/relay.py` `a9b90a17`/`a200f190` (cited by
E-relay — fingerprint was owed); `rest_framework/serializer_converter.py`
`a22dcbe3`/`469a4959`; `sets_mixins.py` `c496feb2`/`42e8c862`;
`utils/querysets.py` `6d471bd7`/`adc74b64`;
`rest_framework/resolvers.py` `08310034`/`5e80bbf7`;
`rest_framework/sets.py` `0062e647`/`25f6c55c`; `utils/truth.py` WT
`711352b1`, no HEAD blob (untracked concurrent work).

### RULING R1 — four `Trigger: none` entries (W0-b)

Form deviation, cured: a non-mechanism exclusion's honest trigger is
a MECHANISM-GAIN clause — E-register: a registration method gaining
a build expression; E-relay: the index gaining a persistent store;
E-setdefault: a site gaining a build expression; E-comments: a walk
appearing at those lines. Supplied; no W1 rewrite needed.

### RULING R2 — implausibility discharges (W0-c)

CH-miss-signal "No count" is a wording slip for "Count 0"
(inapplicable — no walk site stores `None`; my P3 independently 0).
CH-reentrancy / CH-observability carry explicit "Count 0" with the
reason no site moves — sound (a sourceless change moving no site IS
count 0). No definition count is wrong.

### RULING R3 — gate + unlanded homes (W0-e)

No structural gate owed for a REJECT (no new bypassable owner; the
existing scope gate stands unchanged) — correct. Specified-but-unlanded
docstring homes ACCEPTED: landing prose now would convert a zero-edit
rejection into tracked edits on hunt-dirtied files; the rejection
record (difference + trigger) is durable in artifact + plan row, and
the landing site (spine docstring riders clause) is specified for the
next touching edit.

### RULING R4 — E-edge handling (W0-g)

Observed-not-decided-final is the only honest handling of WT-only
concurrent work; independently confirmed the memo is absent at HEAD.
No verdict rests on it (the six committed walk-shaped sites suffice).

### RULING R5 — citation-range slips (immaterial)

E-copyout `:192-199` omits `:200` (`return list(cached)`); E-enum
`:784-794` omits `:795-796` (register + return); E-lru `:1384-1426`
omits `:1431` (exec-memo store); E-register lacks line cites (methods
above). Substance verified correct in each case; ranges noted.

### Worker-2 gates + pins (own runs, shared venv)

- `uv run basedpyright` → 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_any.py` → 128 allowed at 89 sites.
- `uv run python scripts/check_truthful_reads.py --check` → 119
  files; errors 0. (mypy never run, never cited.)
- Focused oracle re-run (one `--no-cov` shared-tree run): 6/6 green
  in 2.73s — corroborates W1's 6/6. No oracle rewritten (zero-edit).
- Pins: HEAD `dd0b6691` unmoved; `ITEM_BASELINE=0412709a`;
  `utils/inputs.py` WT `8839b38d`/HEAD `0b7d353c`,
  `filters/inputs.py` WT `993f365c`/HEAD `08516597` — all confirmed.
- Defects (Worker-2): none — zero package defects found; no
  `## Defects` entry owed. Pending execution: none.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
