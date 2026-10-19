# DRY review: `plan-time-window-slice-resolution`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is plan-time window-slice resolution: how a
connection window slice is derived from pagination arguments at plan
time -- `first` / `last` / `after` / `before` into `(offset, limit,
reverse)` plus, on the keyset fork, the decoded cursor seek. Re-derived
fresh at WT bytes (`5c3496e0` + concurrent dirt), not inherited: the
population is the mechanism (argument reads, the `SliceMetadata`
engine call, the backward test, the page rewrite, the cap dig, the
cursor codec, the bounds record, the unwindowable signal), swept
package-wide by exact-match spelling, in every module, not just the
four indexed files.

What the trace found is an already-consolidated rule in three homes,
each holding what its importers can reach:

- The shared kernel in `utils/connections.py` (clean at HEAD blob
  `5bf8f5fa`): both bounds forks
  (`derive_connection_window_bounds`, `derive_keyset_window_bounds`),
  the page rewrite (`page_arguments`), the backward core
  (`is_backward_shape`), the parity bound
  (`assert_relay_pagination_bound`), the cap dig
  (`relay_max_results_from_info`) and cap resolve
  (`resolve_relay_max_results`), the bounds record
  (`ConnectionWindowBounds`), and the control signal
  (`UnwindowableConnection`). The module docstring states the reason:
  the planner and the resolver must spell the slice IDENTICALLY or
  optimizer-on/off behavior splits (the cursor-parity invariant), so
  the kernel lives where both import it without a cycle.
- The plan-time adapters in `optimizer/nested_planner.py`: the offset
  adapter `_connection_window_slice_from_arguments` (the index owner
  candidate), its keyset twin
  `_keyset_window_slice_from_arguments`, and the raw-token coercion
  `_coerce_pagination_int`. Each adapter coerces, reads the cap, calls
  the shared fork, and maps malformed pagination to `None`; neither
  re-derives the reverse/limit rule.
- The cursor codec and seek carrier in `keyset.py`:
  `decode_keyset_cursor` (verify + decode, uniform `GraphQLError`)
  and `KeysetSeek` (columns + cursor + direction).

Verified siblings enter as INPUT and are never re-litigated: f15
(`optimizer-hint-shape`) and f16 (`optimizer-hint-skip-predicate`)
own the hint value contract and the SKIP gate upstream of per-key
windows; f17 (`nested-connection-strategy-selection`) owns strategy
selection downstream of slice resolution; f18
(`nested-fetch-strategy-seam`) owns the request/wrapper seam that
carries the resolved slice (`NestedConnectionRequest`,
`LateralWindowSpec`, the windowed floor). The `is_supplied` /
`is_inactive_value` spelling enters from queued
`list-argument-supplied-spelling`, and `effective_bound` /
`policy_from_info` from verified f12/f13 -- composed, never
re-derived here.

Queued siblings converge or exclude with a contract difference, never
absorbed silently: `window-range-fetch-derivation`,
`recognized-fetch-queryset-skeleton`, `scalar-only-window-projection`,
`keyset-cursor-column-projection`, `optimizer-hint-dispatch`, and
`attached-prefetch-lookups-read` are each excluded under Findings
(R1-R6) on a fetch-vs-slice, mechanism-vs-derivation, or
projection-vs-resolution difference with a stated trigger.

Prior record, adjudicated fresh (never evidence): the run-6 item that
converged 9 symbols onto this open family, transcribing nothing, and
the s15 homing that gains `page_arguments` as a 10th definition. The
fresh census below re-derives membership symbol by symbol and
CONFIRMS the `page_arguments` homing: the page-argument rewrite is
composed by both bounds forks AND the fallback slicer
(`connection.py:841`), so it is a member definition of this rule, not
of the fetch family. Flat symbol counts from prior runs are not
reproduced -- the verdict rests on the sub-decision decomposition in
F1 (12 sub-decisions, each count 1).

## Verification

### Matrix

Each axis discharged against the family's real surface (argument
vocabularies, both cursor vocabularies, plan + resolve halves):

1. Cross-flavor policy mirroring -- DISCHARGED by comparison. The two
   pagination flavors are the offset fork (cursors parse through
   Strawberry's `SliceMetadata`) and the keyset fork (value cursors
   cannot). Both forks share every sharable sub-decision by name
   (`page_arguments`, `is_backward_shape`,
   `resolve_relay_max_results`, `assert_relay_pagination_bound`,
   `ConnectionWindowBounds`, `UnwindowableConnection`); what stays in
   each fork is vocabulary-forced (the `SliceMetadata` engine call on
   one side, forward-only `limit = first-or-cap` on the other).
   Searched for sibling flavors with pagination slicing:
   `list_field.py` carries no `first` / `last` read (grep 0);
   mutations / forms / rest_framework have no connection slicing;
   Relay Node ID decodes (`relay.py:422`, `types/relay.py:836`) are a
   different vocabulary, excluded (R10).
2. Sync/async twins -- DISCHARGED, no twin. Both derive helpers are
   pure sync; the keyset slicer derives `backward` / `page_size` /
   `fetch_limit` ONCE (`connection.py:1134-1143`) above the
   sync/async dispatch (`connection.py:1206`), so both colors slice
   identically. The resolve side needs no `_coerce_pagination_int`
   twin: Strawberry's engine coerces resolver arguments before the
   resolver sees them (`ConnectionExtension.resolve` is upstream),
   while plan time reads raw AST tokens -- one package coercion, one
   engine coercion, different subjects.
3. Derived rather than repeated knowledge -- DISCHARGED by census.
   `SliceMetadata.from_arguments` has exactly ONE package call site
   (`utils/connections.py:711`); every other mention is ``-quoted
   prose. `ConnectionWindowBounds(` is constructed at exactly two
   sites, one per fork (`utils/connections.py:743`, `:855`). The
   backward core is spelled once (`is_backward_shape`,
   `utils/connections.py:153`); `page_arguments`' either-bound test
   (`:171`) is a distinct predicate, not a re-spell. `last == 0`
   occurs once (`:169`). The `relay_max_results` attribute dig
   occurs once (`:788`). The pagination `int()` coercion occurs once
   (`nested_planner.py:835`); the only other package `int()` near
   pagination parses a cursor INDEX inside the negativity guard
   (`connection.py:807`, R8).
4. Inverse / round-trip pairs -- DISCHARGED. The keyset codec is the
   pair: `decode_keyset_cursor` (bytes to values, converges here)
   and `encode_keyset_cursor` (row to bytes, R9 -- output direction,
   each half single-owned, payload-grammar changes move both by the
   nature of a codec). `assert_relay_pagination_bound` is not an
   inverse of `SliceMetadata`: it is the deliberate parity spelling
   for the fork that cannot run the engine, owned once, consumed
   twice (S6).
5. Contracts restated in another medium -- DISCHARGED by role. Nine
   oracle files across three tiers spell expected bounds literally
   and never read the owner (listed under F1, never counted):
   `tests/utils/test_connections.py` (fork arms, shape table,
   UNSET arms), `tests/optimizer/test_walker.py` (adapter arms,
   coercion, per-key windows, alias vocabulary),
   `tests/optimizer/test_plans.py`, `tests/test_keyset.py`,
   `tests/test_keyset_connection.py` (keyset adapter arms),
   `tests/test_relay_connection.py` (`last: 0` / `first: 0` pins),
   plus live `/graphql` suites `test_keyset_api.py`,
   `test_library_api.py`, `test_products_api.py`.
   `page_arguments` / `is_backward_shape` have no BY-NAME oracles;
   they are pinned transitively through the derive-level and live
   page-shape tests, which is the independent-oracle shape (a
   by-name unit would couple tighter, not looser). Projections: the
   kernel/adapters/codec docstrings, the GLOSSARY nested-window and
   `DjangoConnection` anchors, spec-033 Decisions 3/4/5/7
   (`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`).
6. Enforcement by omission -- DISCHARGED by enumeration. Every
   package reader of pagination arguments was enumerated and roled:
   the two planner adapters (S1/S2), the resolve-time window probe
   (`connection.py:712-757`), the fallback slicer
   (`connection.py:814-876`, via `page_arguments` + the keyset
   slicer / upstream `ListConnection`), the keyset slicer bounds
   (`connection.py:1117-1143`), the alias-vocabulary normalizer
   (`walker.py:1730-1749`, consumer of S5), the `first` + `last`
   guard (R7), the negative-cursor guard (R8), the plan-cache
   argument-name vocabulary (R23), and the cost-charging page bound
   (R24). Every Slicing path composes the shared definitions; the
   four non-slicing readers are excluded with contract differences.
   No member lacks a guard the contract requires: malformed
   pagination maps to `None` at plan time and raises at resolve
   time by design (the error-locality split both adapters document).

### Enumeration

Family item: the population is the rule's mechanism, swept
package-wide by exact-match spelling (`SliceMetadata.from_arguments`,
`derive_connection_window_bounds`, `derive_keyset_window_bounds`,
`page_arguments`, `is_backward_shape`, `assert_relay_pagination_bound`,
`relay_max_results_from_info`, `resolve_relay_max_results`,
`ConnectionWindowBounds`, `UnwindowableConnection`,
`_connection_window_slice_from_arguments`,
`_keyset_window_slice_from_arguments`, `_coerce_pagination_int`,
`decode_keyset_cursor`, `encode_keyset_cursor`, `KeysetSeek`,
`isinstance(last`, `isinstance(first`, `last == 0`,
`arguments.get("first"|"last"|"before"|"after")`,
`"first"|"last"|"before"|"after"` literals, `from_base64(`,
`[^a-zA-Z_]int(`, `_guard_first_and_last`,
`_reject_negative_offset_cursor`, `_page_bound`,
`_PAGINATION_ARG_NAMES`, `_normalized_alias_payload`,
`_divergent_key_windows`). Hits land in 14 production files: the 4
indexed files plus `connection.py` (resolve halves + guards),
`optimizer/plans.py` (window mechanism, consumer -- R11),
`optimizer/nested_fetch.py` + `optimizer/lateral_fetch.py` +
`optimizer/single_parent_fetch.py` (f18 seam carriers/consumers --
R20), `optimizer/extension.py` (cache vocabulary -- R23),
`optimizer/selections.py` (prose only -- no coercion twin),
`extensions/resource_policy.py` (cost bound -- R24), `relay.py` +
`types/relay.py` (Node vocabulary -- R10), `list_field.py` (grep 0,
clean), `resource_policy.py` + `utils/typing.py` +
`utils/input_values.py` (composed inputs -- R15/R16). Each was read
(or grep-cleared with a stated population) and either roled or
excluded with a contract difference under Findings. Nothing reachable
was left unassigned: 14 member definitions in 12 sub-decisions, 8
consumer groups, 1 upstream engine + 1 upstream slicer, 24
exclusions, 9 oracle files plus live suites, projections.

### Challenges

Each variation axis of the slice rule, posited change plus the
authoritative definitions forced to move (consumers, oracles,
projections listed, never counted):

- C1, the `last: 0` page stops meaning `first: 0` (e.g. an empty
  backward page): `page_arguments` only
  (`utils/connections.py:169`). Both derive forks and the fallback
  slicer follow by construction (3 call sites, 0 re-spells). Count 1.
- C2, the default page when neither bound is an `int` stops being
  the cap (e.g. unbounded or a fixed 20): `page_arguments` only
  (`:171-173`). Same three followers. Count 1.
- C3, the backward core changes (e.g. a new inactive spelling must
  not count as supplied): `is_backward_shape` only (`:153`). The
  three call sites (offset `+ not before`, keyset `or before`,
  slicer bare) keep their explicit per-site terms; only the core
  moves. Count 1.
- C4, the offset reverse/limit rule changes (e.g. `before` + `last`
  becomes a reversed window, or a new shape joins the unwindowable
  set): `derive_connection_window_bounds` only (`:652-743`). The
  planner adapter and the resolve probe follow by name; the keyset
  fork is untouched. Count 1.
- C5, the keyset limit rule changes (e.g. the cap default goes away
  on the keyset fork): `derive_keyset_window_bounds` only
  (`:813-855`). The before-seek half of a hypothetical backward
  keyset window would live in the planner adapter's seek assembly
  (S2), count 1 there -- a feature spanning two sub-rules, each
  single-owned. Count 1 per sub-rule.
- C6, the plan-time coercion changes (e.g. float-like tokens coerce,
  or non-castable values fail loudly): `_coerce_pagination_int`
  only (`nested_planner.py:822-837`). Both adapters and the alias
  normalizer follow by name. Count 1.
- C7, the cap changes: split per the standing `cap-dig-vs-cap-resolve`
  row (upheld, never re-litigated). A dig change (a new `info`
  shape) moves `relay_max_results_from_info` only (`:773-788`); a
  precedence / terminal-default / ceiling change moves
  `resolve_relay_max_results` only (`:791-810`, composing the dig
  and f12/f13 by name). Count 1 each.
- C8, the keyset cursor payload grammar changes (e.g. a version
  field): the DECODE direction moves `decode_keyset_cursor` only
  (`keyset.py:549-592`); planner adapter and resolve slicer follow.
  The mint half (`encode_keyset_cursor`, R9) moves as the codec's
  inherent second direction, single-owned itself. Count 1 per
  direction.
- C9, the bounds record gains a field or the signal gains context:
  `ConnectionWindowBounds` (`:638-649`) / `UnwindowableConnection`
  (`:84-102`) only; the two constructions / three raises / two
  catches follow by name. Count 1 each.

Execution: none owed and none used. Every challenge above is decided
by an exact-match single-site census (definition counts, not
behavioral equivalence), which needs no execution; nothing lands, so
no failability proof is owed. All oracle citations are
static-reviewed. No workspace run and no shared-tree run was needed
for this zero-edit verdict.

## Findings

### F1: plan-time window-slice resolution is single-owned (CONFIRM, zero-edit)

Contract + variation. One rule: pagination arguments resolve to a
window slice -- `(first, last, after, before)` into
`ConnectionWindowBounds(offset, limit, reverse)` on the offset fork,
plus a `KeysetSeek` on the keyset fork -- identically at plan time
and resolve time (the cursor-parity invariant). Legitimate variation
axes: the page rewrite (`last: 0`, default cap), the backward test,
the reverse/limit rule per fork, the unwindowable shape set, the
token coercion, the parity bound text, the cap precedence, the cursor
payload grammar, the bounds record, the signal. The rule varies by
cursor vocabulary (offset vs keyset) at the fork and is IDENTICAL
across plan/resolve halves within a fork.

Sites + roles. 14 member definitions in 12 sub-decisions, each
count 1 (challenges C1-C9):

- S1, offset slice: `derive_connection_window_bounds` (kernel,
  owns the reverse predicate + limit rule + the single
  `SliceMetadata.from_arguments` call) fronted at plan time by
  `_connection_window_slice_from_arguments` (the index owner:
  coerce + cap read + shared call + `ValueError`/`TypeError` to
  `None`; `UnwindowableConnection` propagates). The adapter is a
  consumer + enforcement site, not a second derivation -- it never
  re-spells the rule. Resolve-time consumer calls the kernel
  directly and lets pagination errors propagate (the documented
  error-locality split).
- S2, keyset slice: `derive_keyset_window_bounds` (forward-only,
  offset 0, `limit = first-or-cap`, backward shapes unwindowable)
  fronted by `_keyset_window_slice_from_arguments` (coerce +
  decode `after:` into the seek + validate `before:` + shared call
  + `GraphQLError`/`ValueError`/`TypeError` to `None`).
- S3, page rewrite: `page_arguments` (`last: 0` without `int`
  `first` is the `first: 0` page; neither bound an `int` is the
  cap). Three composing call sites: both derive forks + the
  fallback slicer. This CONFIRMS the s15 homing fresh.
- S4, backward core: `is_backward_shape` (shared core; the
  `before` term stays explicit per call site -- three call sites,
  one core).
- S5, token coercion: `_coerce_pagination_int` (int-like to
  `int`; `None`/non-castable pass through to the engine's own
  gate). Three composing consumers: both adapters + the alias
  normalizer. The standing File `nested_planner.py` rejection
  (coercion stays plan-time, never folded into the shared helper)
  is trigger-checked clean and upheld.
- S6, parity bound: `assert_relay_pagination_bound` (Relay
  negative/over-cap `ValueError`s with `SliceMetadata`-exact text
  for the fork that cannot run the engine). Two consumers: the
  keyset fork (`first` only -- backward raises unwindowable
  upstream) and the keyset slicer (`first` + `last`, which serves
  backward pages).
- S7/S8, cap dig / cap resolve: `relay_max_results_from_info`
  (`None`-preserving config dig, the single attribute read) and
  `resolve_relay_max_results` (explicit wins, else dig, else
  Strawberry's terminal default, narrowed by the policy ceiling).
  Distinct contracts per the standing `cap-dig-vs-cap-resolve`
  row (upheld); the planner passes the dig as `max_results` and
  the kernel re-resolves idempotently (narrowing ceiling).
- S9, bounds record: `ConnectionWindowBounds` (two constructions,
  one per fork -- each fork producing the shared shape, not two
  shapes).
- S10, control signal: `UnwindowableConnection` (three raises, all
  inside the two derive forks; two catches: the planner's
  per-key fallback classifier and the resolve probe's
  offset-raises / keyset-recovers split).
- S11/S12, cursor decode + seek carrier: `decode_keyset_cursor`
  (four call sites: planner after-decode + before-validate,
  slicer after-seek + before-seek) and `KeysetSeek` (plan time
  builds `flip=False` only; the slicer builds both arms).

Consumers (listed, never counted): `_divergent_key_windows` +
`plan_connection_relation` (per-key orchestration, scheme owned by
queued `nested-connection-plan-orchestration`); `_consume_window` +
`_resolve_from_window` (resolve probe + window consumer);
`_consume_fallback` + `_resolve_keyset_connection` + upstream
`ListConnection` (fallback slicing); `_normalized_alias_payload` +
the divergence/conflict detectors (vocabulary-insensitive alias
comparison); the f18 seam carriers (`NestedConnectionRequest`,
`LateralWindowSpec`, `apply_window_pagination`) threading resolved
bounds downstream.

Oracles + projections: as inventoried under Matrix axis 5 (9 files,
3 tiers; docstrings + GLOSSARY + spec-033). All static-reviewed.

Owner + lifetime (principle 7). CONFIRM the index candidate
`optimizer/nested_planner.py::_connection_window_slice_from_arguments`:
the narrowest plan-time symbol fronting the whole plan-time
derivation, which every plan-time consumer already depends on
without reversing a dependency. The kernel CANNOT move into the
planner (both the planner and `connection.py` import it; its
cycle-safe `utils/` home is load-bearing for the parity invariant),
the codec CANNOT move out of `keyset.py` (cursor-vocabulary owner),
and the keyset twin sits beside the owner in the same module. Pure
derivation, not cached -- no principle-4 lifetime fields owed (plan
caching downstream is extension-owned input).

Migration: none -- zero-edit. Every member is already the single
spelling; every non-member already composes by name.

Distinct behavior: R1-R24 below, each with its contract difference
and reconsideration trigger. Recorded here (per-cycle artifact, raw
`path:NN` allowed); durable prose already exists at the owners
(kernel module docstring, adapter docstrings, codec docstrings), so
no docstring edit is owed for this CONFIRM verdict.

Behavioral proof: static-reviewed. The verdict is a definition-count
verdict over exact-match censuses, each reproducible by the
Enumeration spellings; behavioral equivalence needs no proof because
nothing moves. The independent behavior oracles (derive shape
tables, adapter arms, live `last: 0` / `first: 0` / offset / keyset
suites) fail on divergence by spelling expected bounds literally.
No `proof:` entry owed.

Structural gate: none proposed, deliberately. A name-census test per
helper (e.g. "exactly one `SliceMetadata.from_arguments` call") is
the bespoke existence test DRY.md forbids; the plausible bypass
(an inline re-derivation of bounds) has no population beyond the
enumerated consumers, all proven composing by name. The independent
behavior oracles are the guard that fails on divergence.

Coupling: none -- zero-edit lands nothing.

Freshness. HEAD `5c3496e0`, ITEM_BASELINE `aadff1ef`. Pins (WT /
HEAD, `git hash-object` / `git rev-parse HEAD:`):
indexed `optimizer/nested_planner.py`
`b6ff0a0e998291c5acdf204fd363fd015bb1e1bb` /
`8c3a45f55533cbaf9697013e5d87f599aae65adb`;
`optimizer/walker.py`
`4fd8077fca391111ceb343a693c0a0c52571f01b` /
`13e1be20e63b8848562e62446b11c64d5893e0aa`;
`utils/connections.py` `5bf8f5fa533f4c075cbb9915d471dedf028ff41e`
(clean, both states); `keyset.py`
`7d43c6b14f900712e92979177d4864673d5ed8c9` /
`6af980b8ff8b677d1762e7526bcb0ddb263031fc`. Resolve side
`connection.py`
`48de0243613555312478aaeb7b1a2f198923e91a` /
`999696529e18160aff1e465951ebe7e88dd4613b`. Consumers/exclusions
`optimizer/plans.py` `2e962ae2` / `97a524e2`,
`optimizer/nested_fetch.py` `c36826bb` / `bedaa76e`,
`optimizer/lateral_fetch.py` `a48cb0a4` (clean),
`optimizer/single_parent_fetch.py` `3a4bb89b` (clean),
`optimizer/extension.py` `8e3fe7c1` / `b7b6c434`,
`optimizer/selections.py` `1f6d3e04` / `f49ea7fa`,
`extensions/resource_policy.py` `a7f7363f` / `11e2a9ac`,
`relay.py` `63bbba0b` / `037723cd`, `types/relay.py` `9903f6ea` /
`2d1efd00`, `list_field.py` `6c0992f2` / `37d2e6dc`,
`resource_policy.py` `814eb7e9` / `c554a679`, `utils/typing.py`
`1fa47d59` / `defbe7ee`, `utils/input_values.py` `905451cc` /
`929e81b5` (8-char prefixes; full hashes in the work notes above).
Oracle pins: `tests/utils/test_connections.py` `65d54027` (clean),
`tests/optimizer/test_walker.py` `ca5c32d7` (clean),
`tests/optimizer/test_plans.py` `df714065` (clean),
`tests/test_keyset.py` `e5655de7` (clean),
`tests/test_keyset_connection.py` `70db0483` (clean),
`tests/test_relay_connection.py` `e6b4b556` / `29a2be59`,
`test_query/test_products_api.py` `fe78cf9d` / `4186b4d9`,
`test_query/test_keyset_api.py` `315c0372` (clean),
`test_query/test_library_api.py` `099e25b9` / `91f0238b`. Searched
population: every `.py` under `django_strawberry_framework/`
(exact-match censuses above); contract sources: spec-033 + GLOSSARY
anchors + owner docstrings. Dirt check: the slice regions match HEAD
except WT-added `_reject_negative_offset_cursor` (R8, concurrent
work -- 0 occurrences at HEAD, traced at WT bytes; the exclusion
holds at both states) and prose-only touches (spec-047 Decision 7
citation, keyset prefix-refusal line). Any pin change reopens F1.

### Rejections and exclusions (contract difference + trigger each)

Queued siblings (all open `- [ ]` rows; converge-or-exclude, never
absorbed):

- R1, `window-range-fetch-derivation`: `window_range_plan` /
  `WindowRangePlan` derive FETCH bounds, markers, and the probe from
  an already-resolved `(offset, limit, reverse)`. Slice resolution
  ENDS at `ConnectionWindowBounds`; fetch derivation STARTS there.
  Trigger: `window_range_plan` starts reading pagination arguments,
  or a derive fork starts emitting fetch bounds.
- R2, `recognized-fetch-queryset-skeleton`: the fetch queryset shape
  (`RecognizedFetchQuerySet`: clone, rebind, fetch-all dispatch)
  CARRIES the slice; it never derives bounds. Trigger: the skeleton
  starts deriving bounds from arguments.
- R3, `scalar-only-window-projection`: which COLUMNS a scalar-only
  window fetches vs which ROWS the slice selects. Trigger: the
  projection starts reading pagination arguments for bounds.
- R4, `keyset-cursor-column-projection`: `_extend_only_projection`
  adds cursor columns to the projection -- column membership vs
  slice derivation. Trigger: it starts deriving bounds or seeks
  from arguments.
- R5, `optimizer-hint-dispatch`: hint application transforms child
  querysets from HINT values, a different input and output from
  argument-to-slice derivation. Trigger: hint dispatch starts
  resolving pagination windows.
- R6, `attached-prefetch-lookups-read`: introspecting attached
  `_prefetch_related_lookups` state vs deriving a slice from client
  arguments. Trigger: the read starts computing slices.

Guards, validators, and the upstream engines:

- R7, `_guard_first_and_last` (`connection.py:1225-1240`):
  VALIDATION (reject the illegal `first` + `last` combination) vs
  DERIVATION (map legal arguments to bounds). Single-sited at the
  resolve seam every connection shape passes through, before any
  window is consumed -- so no plan-time twin is needed or exists.
  Trigger: the guard starts deriving bounds, or a derive fork
  starts rejecting combinations.
- R8, `_reject_negative_offset_cursor` (`connection.py:776-811`,
  WT-added concurrent work): a negativity verdict on the list-slice
  branch vs slice derivation -- it classifies one malformed shape
  and computes no bounds. Trigger: the guard starts computing
  slice bounds.
- R9, `encode_keyset_cursor` (`keyset.py:515-546`): the codec's mint
  half (row to cursor bytes, two call sites) vs the decode half
  (S11). One grammar, two directions, each single-owned; a payload
  change moves both by the nature of a codec, not by duplication.
  Trigger: a third codec direction appears, or a grammar change
  moves only one half.
- R10, Relay Node ID decodes (`relay.py:422`,
  `types/relay.py:836`): the Node global-ID vocabulary vs the
  pagination cursor vocabularies (offset `arrayconnection` /
  keyset `dstcursor`), owned by verified global-ID families.
  Trigger: pagination cursors start sharing the Node ID codec.
- R11, `apply_window_pagination` (`plans.py:1010+`): the window
  MECHANISM (annotate row numbers / counts, filter to the range)
  consuming resolved `(offset, limit, reverse)` inputs vs deriving
  them. Trigger: it starts reading pagination arguments.
- R12, orchestration and scheme (`_divergent_key_windows`,
  `_plan_connection_relation`, `_normalized_alias_payload`):
  per-key iteration, fallback classification, and
  vocabulary-insensitive alias comparison CONSUMING the adapters --
  scheme selection owned by queued
  `nested-connection-plan-orchestration`. Trigger: the
  orchestration starts deriving bounds outside the adapters.
- R13, upstream `ListConnection.resolve_connection`: the offset
  fallback SLICER. The package deliberately runs no second
  offset-slice implementation; the slicer receives
  `page_arguments`-rewritten bounds. Trigger: the package forks
  offset slicing.
- R14, upstream `SliceMetadata.from_arguments`: the offset ENGINE,
  called once (`utils/connections.py:711`). Not package-owned; the
  package owns the rule around it (reverse/limit, unwindowable
  classification, parity spelling). Trigger: a second package call
  site appears.

Composed inputs (boundaries held, never re-litigated):

- R15, `is_supplied` / `is_inactive_value`: the active-input
  spelling, input from queued `list-argument-supplied-spelling`.
  Trigger: a slice site re-spells the rule inline.
- R16, `effective_bound` / `policy_from_info`: the policy ceiling,
  input from verified f12/f13. Trigger: the cap resolve stops
  composing the ceiling.
- R17, seek renderers (`KeysetSeek.q` / `.plan`,
  `keyset_seek_q`, `keyset_seek_sql`, `build_keyset_seek_plan`):
  predicate RENDERING from a resolved seek vs seek RESOLUTION from
  arguments (S2/S12). Trigger: a renderer starts reading
  pagination arguments.
- R18, walker alias bindings (`walker.py:104-112`): pure name
  re-exports of the planner bodies for historical importers; zero
  bodies, zero definitions. Trigger: a body appears behind an
  alias.
- R19, `_relay_max_results_from_info` (`nested_planner.py:46`):
  import alias of S7 under its historical private spelling (tests
  import it via the walker); one function, two names. Trigger: the
  planner stops importing the shared dig.
- R20, seam carriers (`NestedConnectionRequest`,
  `LateralWindowSpec`, `_WindowedConnectionRows`): f18-verified
  input carrying resolved bounds downstream. Trigger: a carrier
  starts deriving bounds.
- R21, `_resolve_from_window` + `_KeysetPage`: edge/pageInfo
  CONSUMPTION from bounds + rows (page flags derive from fetched
  DATA -- overfetch, markers, counts -- vs bounds deriving from
  ARGUMENTS). Trigger: flag derivation recomputes bounds, or
  bounds derivation reads rows.
- R22, `schema.py` execution windows: transaction/execution windows
  (a vocabulary collision -- "window" as a lifetime, never a row
  range). No pagination read. Trigger: the execution window starts
  slicing connections.
- R23, `_PAGINATION_ARG_NAMES` (`optimizer/extension.py:190-201`):
  the four argument NAMES as a plan-cache-key vocabulary
  (spec-033 Decision 7) vs deriving a slice from their VALUES.
  Trigger: the collector starts deriving bounds, or slice
  derivation starts keying the cache.
- R24, `_page_bound` (`extensions/resource_policy.py:988-1010`):
  CONSERVATIVE cost charging (`min(value, max_page_size)` over raw
  AST with exact-type hostile-input gates) vs the EXACT served
  slice. Genuine keeping-separate reasons: estimate vs exactness,
  hostile-AST posture vs engine-coerced values, cost domain vs
  fetch domain. Sharing a helper would couple exact pagination
  semantics to cost heuristics. Trigger: `_page_bound` starts
  determining served rows, or slice derivation starts charging
  cost.

Standing rows trigger-checked (upheld, none reopened): File
`utils/connections.py` s15 C1 (`page_arguments` homed here --
CONFIRMED above as S3) and the discharged R14 hold (single
`last == 0` site, three composing readers -- census reproduced
exactly); `cap-dig-vs-cap-resolve` (S7/S8 separation -- upheld in
C7); File `nested_planner.py` coercion-vs-shared-derivation (S5
stays plan-time -- upheld). No ticked row was found factually
wrong, so no closeout-homing finding is owed.

## Defects

None found. The trace surfaced no behavior defect, no stale
contract prose at an owner, and no ticked plan row that is
factually wrong.

## Pending execution

None. Zero-edit census verdict: no `proof:` entry owed (definition
counts need no execution), no `gate:` entry. Cells per the run-9
f18 typing ruling: the canonical binary binds and the slice paths
reach the database (windowed prefetch querysets, the keyset
slicer), while inapplicable-by-construction is NOT claimed -- so
both cells read `unverified` (`--cell sharded` and `--cell pg` were
not authorized; the gate lists them). The verdict itself is
cell-independent (source censuses are identical across cells).

## Judgment

CONFIRM: plan-time window-slice resolution is already single-owned
-- 14 member definitions in 12 sub-decisions, every challenge count
1, every other site composing by name -- so the consolidation is
proved with ZERO edits. The index owner
`optimizer/nested_planner.py::_connection_window_slice_from_arguments`
is CONFIRMED fresh (principle 7: narrowest plan-time symbol
fronting the derivation; kernel and codec homes are
dependency-forced), and the s15 `page_arguments` homing is
CONFIRMED fresh (S3: both forks plus the fallback slicer compose
it). All six queued siblings are excluded with contract
differences; f15/f16/f17/f18 enter as input untouched; four
standing rows trigger-check clean. No new index rows owed, no
defects, no pending execution; cells `unverified` per the typing
ruling. Zero-edit proof: no tracked `.py` touched (no `## Implementation`
section), status count 466 with HEAD unmoved at `5c3496e0`, the
artifact the only new file. Ruff and the three type gates are
vacuous (nothing to lint or check -- none run, none owed).

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (expectation-first; only the
artifact's title/status/header lines and Judgment tail seen, no
findings/challenges detail). Traced at HEAD bytes (`5c3496e0`);
WT dirt on 3 of the 4 indexed files verified disjoint from the
population (hunt-owned `truth.*` hardening + advisory prose; see
fingerprints below), so HEAD == WT on every slice line.

### Own trace: sites and roles

Family rule as I posit it: deriving the plan-time window slice
`(offset, limit, reverse)` (+ keyset seek) from `first` / `last` /
`after` / `before` argument payloads. Swept package-wide by exact
symbol spelling, not by neighbours.

Authoritative definitions (15 by my count):

Kernel (`django_strawberry_framework/utils/connections.py`, clean,
HEAD == WT `5bf8f5fa`):
- D1 `derive_connection_window_bounds` -- offset fork: engine call,
  reverse predicate, limit rule, unwindowable classification,
  negative-cursor `TypeError` arms.
- D2 `derive_keyset_window_bounds` -- keyset fork: forward-only
  bound rule, backward refusal.
- D3 `page_arguments` -- page rewrite (`last: 0` -> `first: 0`;
  default `cap` page).
- D4 `is_backward_shape` -- core Relay shape test.
- D5 `assert_relay_pagination_bound` -- SliceMetadata-parity bound
  check + wording.
- D6 `relay_max_results_from_info` -- config dig.
- D7 `resolve_relay_max_results` -- cap precedence + policy ceiling.
- D8 `ConnectionWindowBounds` -- bounds record.
- D9 `UnwindowableConnection` -- control-flow signal type.

Adapters (`django_strawberry_framework/optimizer/nested_planner.py`):
- D10 `_connection_window_slice_from_arguments` -- offset adapter
  (coercion + cap read + ValueError/TypeError -> None mapping).
- D11 `_keyset_window_slice_from_arguments` -- keyset adapter
  (coercion + cursor validation/decode + seek + bounds + error
  mapping).
- D12 `_coerce_pagination_int` -- plan-time-only int coercion.
- D13 `_divergent_key_windows` -- per-key window fan-out with
  sidecar / unwindowable / malformed classification (boundary
  candidate: arguments-derived window pass per its docstring; the
  orchestration family may alternatively claim the fan-out loop).

Codec/carrier (`django_strawberry_framework/keyset.py`):
- D14 `decode_keyset_cursor` -- canonical cursor codec.
- D15 `KeysetSeek` -- seek carrier (+ `.q()` render).

Consumers (compose by name, verified by sweep): walker
`_normalized_alias_payload` (D12) + re-export aliases (no logic);
`connection.py` resolve paths (D1/D2 fork call, D3 in
`_consume_fallback`, D4/D5/D7 in the keyset slicer, D14/D15 in
both keyset paths); `plans.py`/`nested_fetch.py` docstring
mentions (projections). Oracles: `tests/utils/test_connections.py`
(D1/D2 behaviors), `tests/optimizer/test_walker.py` (D12 + D6 via
walker aliases, literal expectations), `tests/test_keyset_connection.py`
(D11 arms), `tests/optimizer/test_plans.py` (D10 literal
commentary) -- expectations spelled as literals, not read from
owners (spot-checked, not exhaustively audited).

Structural singles verified: `SliceMetadata.from_arguments`
called once (connections.py `derive_connection_window_bounds`
body); `ConnectionWindowBounds(...)` constructed once per fork
(offset + keyset arms); `UnwindowableConnection` raised once per
classification (offset after+last, inverted interval,
keyset-backward) with one signal type; both `except
UnwindowableConnection` handlers (planner per-key fallback,
resolver recovery) are phase-appropriate consumers.

### Own trace: change challenges and counts

- WC1 new pagination argument: each fork defines the new arg's
  meaning in its own vocabulary (D1/D10 vs D2/D11 arms) -- two
  sub-decisions, each count 1, not two copies of one rule.
- WC2 second coercion path (e.g. reject bool page sizes):
  D12 only = 1; walker + both adapters compose it by name.
- WC3 cursor vocabulary beyond keyset: new codec + new fork; the
  fork discrimination derives once via
  `declared_cursor_state_for_definition` (plan-side definition
  read and resolve-side class-slot read are consumers) = 1.
- WC4 cap precedence change: D7 only = 1 (D6 is its dig, not a
  second precedence).
- WC5 backward-shape redefinition: core D4 = 1; the offset
  `not before_supplied` term is one explicit per-site arm = 1.
- WC6 bound-error wording: D5 = 1 (offset wording is upstream
  Strawberry's, mirrored deliberately).
- WC7 unwindowable reclassification: one arm per shape, each = 1
  (offset after+last, inverted interval, keyset-backward v1
  scope are three distinct classifications).
- WC8 keyset validate-before-classify order: D11 only = 1.
- WC9 default-page / cap rule: D3 = 1; both kernel forks plus
  the fallback slicer compose it (s15 homing, re-derived).

Adjacent exclusions (mine, with reasons): `_guard_first_and_last`
(resolve-side only, single-sited, one caller; planner leaves
first+last combined for it by documented design -- deliberate
asymmetry, not a missing twin);
`_reject_negative_offset_cursor` (resolve-time fallback
negativity verdict vs D1's `TypeError` arms -- same wording, but
different path (ListConnection would wrap silently), different
error type, documented split; outside the plan-time boundary --
flagged for reconciliation against W1's sibling/standing
treatment); vocabulary derivation
(`declared_cursor_state_for_definition` -- keyset-vocabulary
family's, adjacent input).

### Own trace: owner choice (principle 7)

Three homes by dependency direction: kernel in
`utils/connections.py` (cycle-safe; both planner and resolver
import it, so it cannot live in either caller), plan-time
adapters + coercion in `optimizer/nested_planner.py` (Strawberry
already coerced the resolver's arguments; the walker's
graphql-core info has no `.config`), codec/carrier in
`keyset.py` (soft-crypto boundary). The narrowest plan-time
symbol fronting the derivation is
`_connection_window_slice_from_arguments` (D10; D11 its
documented twin) -- I CONFIRM the indexed owner. Dependency
direction wins over narrowness for the kernel/codec homes.

### Fingerprints (Worker-2, fresh)

- HEAD `5c3496e0` unmoved; `git status --short | wc -l` = 467
  (466 pre-artifact + this artifact; matches Worker-0's
  accounting, not W1's in-artifact 466 which predates it).
- Indexed pins: nested_planner HEAD `8c3a45f5` / WT `b6ff0a0e`;
  walker HEAD `13e1be20` / WT `4fd8077f`; connections HEAD/WT
  `5bf8f5fa` clean; keyset HEAD `6af980b8` / WT `7d43c6b1` --
  all 4/4 WT pins match dispatch pins.
- WT-vs-HEAD hunks on the three dirty files: `truth.*`
  hardening + `_advise_composite_index` m2m silence + docstring
  prose; zero hunks touch D1--D15 lines (grep-verified).

### Reconciliation (every difference vs `## Findings`)

- Member count (mine 15 vs F1's 14): the delta is exactly my
  boundary candidate D13 `_divergent_key_windows`, which W1 homes
  in R12 as orchestration/scheme consuming the adapters (scheme
  owned by queued `nested-connection-plan-orchestration`, with
  trigger). My own trace named this alternative. ACCEPT W1's
  homing: the loop iterates payloads and classifies via composed
  predicates, deriving no bounds itself; the R12 trigger guards
  the boundary. Converged population: my D1-D12 + D14-D15 = F1's
  S1-S12 (S1 = D1+D10, S2 = D2+D11 kernel+adapter pairs).
- Challenges: W1 C1-C9 map onto my WC2/WC4-WC9 one-to-one
  (C1+C2 split my WC9 finer; C6's float-tokens example and my
  bool-rejection example both land count-1 on D12). My extra
  stress cases WC1 (new argument) and WC3 (new vocabulary) are
  addressed structurally (fork design; single vocabulary
  derivation) and force no count > 1: a new arg defines meaning
  once per fork (two sub-decisions, not two copies), a new
  vocabulary adds a codec + fork with the discrimination still
  derived once. W1's C8 (codec grammar, 1 per direction) is
  stronger than anything I posited -- adopted, agreed.
- Owner: full agreement, same principle-7 reasoning
  (dependency direction wins for kernel/codec homes).
- s15 homing: full agreement -- single `last == 0` site,
  three composing call sites, reproduced independently.
- Flagged neighbor `_reject_negative_offset_cursor`: W1
  excludes as R8 with trigger and notes it is WT-added
  concurrent work (0 occurrences at HEAD -- re-verified by me).
  The same-wording verdict is resolve-time fallback, outside the
  plan-time boundary; exclusion holds at both states. ACCEPT.
- `_guard_first_and_last`: W1 R7 matches my exclusion. ACCEPT.
- No other differences: matrix censuses (single engine call,
  two constructions, single dig, single coercion), consumer
  roles, oracle pattern, and the no-gate justification all match
  my independent sweep.

### Adjudication

- F1 sub-decisions (all 12) + owner: ENDORSED. Every C1-C9
  count re-derived at 1; owner CONFIRMED fresh.
- s15 `page_arguments` homing: ENDORSED (both forks +
  fallback slicer compose it; census reproduced exactly).
- Sibling exclusions (R1-R6): ENDORSED -- all six name real
  open/queued plan rows (verified in-plan), each with a
  contract difference + trigger. R7-R24: ENDORSED (guards,
  upstream engines, composed inputs; R23/R24 symbols verified
  at stated sites).
- Standing rows (4): ENDORSED -- s15 C1/R14 census
  reproduced, `cap-dig-vs-cap-resolve` row verified in-plan,
  coercion rejection upheld on fresh evidence (resolver
  arguments arrive engine-coerced; no resolve twin exists).
- f15-f18 boundary: ENDORSED -- hint shape/skip, strategy
  selection, and the f18 seam enter as composed input only
  (imports + carriers); nothing re-litigated, f18's
  closeout-owed D1+O3 homing correctly untouched.
- Index-rows-owed: NONE -- endorsed. No new family, rejection,
  or file-local row is owed; R1-R6 converge onto existing rows.
- Pending-execution "None": CORRECT -- census verdict, nothing
  moves, no gate proposed, so no `proof:`/`gate:` owed.
  Verdict: `verified` PLAIN.
- Cells `unverified`: CORRECT application of the run-9 f18
  typing ruling (canonical binary binds; slice paths reach the
  database -- windowed prefetch querysets, keyset slicer --
  while inapplicable-by-construction is NOT claimed).
- Structural gate (none, deliberate): ACCEPTED. A per-helper
  name-census test is the bespoke existence test DRY.md
  forbids; W1 documents the no-population justification, and
  the literal-spelling behavior oracles fail on divergence.
  Consistent with the verified f12-f18 zero-edit precedent.
- Freshness: W1's indexed pins match mine byte-for-byte (all
  four files, both states); `connection.py` pins re-verified
  exact; dirt attribution (WT guard + prose) confirmed.
- Zero-edit proof: RE-VERIFIED -- no `## Implementation`
  section (single prose mention only), 4/4 WT pins match
  dispatch pins, `git diff ITEM_BASELINE --name-only` is the
  plan edit alone, status 467 = 466 + this artifact, HEAD
  `5c3496e0` unmoved, untracked `truth.py`/`lazy.py` are
  hunt-owned concurrent work unrelated to the family.
- Ruff: VACUOUS -- no tracked `.py` touched, nothing to lint
  (artifact is per-cycle scratch; raw `path:NN` allowed, no
  style cleanup owed). Not run over `.` per constraint.
- Type gates (Worker-2 re-ran whole-package, shared venv):
  `uv run mypy` -> Success, no issues, 119 files, exit 0;
  `uv run basedpyright` -> 0 errors/warnings/notes, exit 0;
  `uv run python scripts/check_any.py` -> 130 allowed Any at
  90 sites, exit 0. (Static gates; slot damage irrelevant.
  No pytest: not authorized by this task.)
- Defects: NONE (Worker-2). No `## Defects` entry owed.

VERDICT: `verified` (plain -- no `proof:` correctly remains).
