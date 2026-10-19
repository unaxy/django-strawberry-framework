# Review · Performance: `django_strawberry_framework/list_field.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8d5cb7ac968f96f5123ad24c3eb2e72c7249b897

## Trace

Read the whole live target (1748 lines). Fingerprint of what was read:
`450e87cde13edc1bfc3c4d4a161c5540d1ac5277`. It matches ITEM_BASELINE
byte-for-byte (empty diff against the baseline object), so nothing drifted
during this pass. Against HEAD the file is dirty (+68/-126), which is the
concurrent work the plan's run-3 Drift lines already record; reviewed as it
stands. No sibling axis record existed when this pass read (first reviewer);
only the skeleton `docs/review/rev-list_field.md` was present.

Orientation: `review_inspect.py` leads only, into
`docs/review/temp-tests/list_field/performance/inspect/` (stripped source +
overview) with `list_field.json` beside them; every lead followed statically.
No workspace run was needed: the discharge below rests on complete static
proofs (absence of evaluation, error-path-only call sites, cold construction
sites), and there is no finding whose before/after needs a number.

Traced out of the module:

- Import order: package `__init__.py` imports `.connection` (line 18) before
  `.list_field` (line 26), and connection.py line 74 imports list_field, so
  list_field loads during the connection import. Every third-party module it
  names is already loaded by then: `django.db.models.lookups` by
  `django.db.models` itself, `django.db.models.functions` via its aggregates
  import, `django.db.models.fields.related_lookups` via its related-fields
  import, `strawberry.schema.schema_converter` via plain `import strawberry`
  (`__init__` to `.schema` to `schema.py`), `graphql` via strawberry.
- Callers: root Query fields in `examples/fakeshop/apps/library/schema.py`
  (ten list fields), so the resolver closures run per request per field (hot).
  `django_strawberry_framework/list_field.py::_validate_relay_djangotype_target`
  is called from connection.py:2330 and relay.py:343, both inside field
  factories (construction, cold).
- Per-request callees, each cost-classified from its body:
  `django_strawberry_framework/resource_policy.py::policy_from_info`
  (contextvar read plus the documented copy-per-read policy copy) and
  `django_strawberry_framework/resource_policy.py::effective_bound` (two
  comparisons);
  `django_strawberry_framework/utils/querysets.py::base_queryset`
  (`_default_manager.all()`, unevaluated),
  `django_strawberry_framework/utils/querysets.py::prepared_resolver_source`
  (guard call plus isinstance coercion),
  `django_strawberry_framework/utils/querysets.py::is_async_only_iterable`
  and `django_strawberry_framework/utils/querysets.py::wrap_async_queryset_adapter`
  (isinstance checks, one small adapter object);
  `django_strawberry_framework/utils/execution_mode.py::async_execution`
  (contextvar read);
  `django_strawberry_framework/utils/truth.py::is_instance` (real-MRO scan,
  two classes for the per-request `str` check) and
  `django_strawberry_framework/utils/truth.py::text` (base-slot string copy);
  `django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms`
  (one conditional call; its re-normalization is that module's documented
  purity check) and
  `django_strawberry_framework/orders/sets.py::capture_applied_order_normalization`
  (one ContextVar set/reset pair).

Path class: hot. The `_default`/`_wrap` resolver closures execute once per
list field per request. The factory
`django_strawberry_framework/list_field.py::DjangoListField`, both target
validators, and
`django_strawberry_framework/list_field.py::_synthesized_list_signature` run
once per field at declaration (cold). The order-determinism classifier runs
per request only when `offset > 0`.

Cells run: none. No finding and no measurement, so no Proof needs a cell. The
target issues no SQL itself: every queryset it touches passes through
unevaluated to the optimizer and the executor (verified in discharge item 1),
so there is no per-cell number to take; query-shape verdicts belong to the
optimizer and resource_policy items.

Looks-for discharge (every Performance entry):

1. N+1 and per-row queries: none. The module never evaluates or iterates a
   queryset. No loop ranges over rows (all `for` loops range over published
   argument maps on error paths, lookup pieces, ordering terms, and
   expression sources); every `await` is a single sequential await, none in a
   loop; there is no `.filter()`, `.exclude()`, or `.get()` in the module.
   Resolvers return lazy querysets or thin adapters; slicing is delegated to
   `django_strawberry_framework/resource_policy.py::_windowed_rows`, row
   fetching to the executor plus the optimizer extension.
2. `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none. No `.count()`,
   `.exists()`, or `bool()` on any queryset; the five `len()` calls measure
   resolver `args` tuples and lookup-piece lists.
3. `only()` / `defer()`: none in the module; select planning is owned by the
   optimizer extension.
4. Unbatched writes: none. The module performs zero writes.
5. `blog.id` vs `blog_id`: none. No related-object attribute reads exist; the
   one model read is off the construction-time definition.
6. Repeated `_meta` walks: none on the request path. `_meta` and `get_field`
   appear only in the `offset > 0` classifier
   (`django_strawberry_framework/list_field.py::_resolve_order_field_path`
   plus `query.get_meta()` reads); each walk is bounded by the ordering terms
   supplied, and classification of the selected ordering runs at most once
   per request (the second guard call classifies only for a model-default
   source, which the first call's active-input classification implies away;
   the surviving double `_selected_ordering` is attribute reads, R3).
7. Repeated settings reads: none. No settings import or read in the module.
   The one policy read per argument-bearing request is a contextvar plus a
   copy, not a settings read; duplicating it is rejected, R2.
8. Repeated regex compilation: none. No regex in the module.
9. Repeated schema or type lookups per request: none on success paths. The
   only schema read (the published-args scan in
   `django_strawberry_framework/list_field.py::_published_wire_name`) runs
   exclusively on error branches: all call sites of
   `django_strawberry_framework/list_field.py::_resolve_argument_wire_name`
   sit inside `raise` expressions or build errors the caller raises, and the
   non-error return of
   `django_strawberry_framework/list_field.py::_build_non_queryset_rejection_error`
   performs zero wire-name calls. The registry read and the orders
   input-type build are construction-only.
10. `lru_cache` on methods: none. No `lru_cache` and no `functools` import in
    the module.
11. Locks, cache reads, re-parses, extra round trips on the per-request path:
    none. No locks, no cache reads, no re-parses, no queries issued. The one
    deferred import reachable per request (the normalization scope's
    `orders.sets` import, only when `offset > 0` arrives with `orderBy`) is a
    `sys.modules` hit after first use and stays deferred to keep `orders` out
    of the package-root import graph (R5).
12. Import-time cost: none beyond the module body. list_field rides the
    package import but pulls zero new third-party modules (all pre-loaded, see
    Trace); its first-party imports are shared with connection.py, which
    triggers the load. The body itself is definitions plus small constant
    frozensets; no settings read and no I/O at import.
13. Allocation in the walk: none beyond small bounded objects. The per-request
    success path allocates one frozen `_ListArguments`, one two-element set
    difference, and short-circuit comparisons; classifier string and frozenset
    work runs only when `offset > 0` and is linear in the ordering supplied.

Fingerprints (`git hash-object`) of every file inspected:

- `450e87cde13edc1bfc3c4d4a161c5540d1ac5277` django_strawberry_framework/list_field.py
- `0ef72601ecac300ac87ff993af1b04a4f1bc335a` django_strawberry_framework/__init__.py
- `1fca6266cd5f748915875badf1881680b599de37` django_strawberry_framework/connection.py
- `e75e2b66a9b406f60d55e952a001d640392331c1` django_strawberry_framework/relay.py
- `cc3f9d80b9d55af8b725a77c73aba3d8110e0037` django_strawberry_framework/resource_policy.py
- `8fc556d582b313e4aed7cddaa15f9a8480d88a46` django_strawberry_framework/utils/querysets.py
- `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9` django_strawberry_framework/utils/execution_mode.py
- `d5c96bc8d191d3fce0a20140d8e91063bb466ec9` django_strawberry_framework/utils/truth.py
- `60859f2d54525acfdb3dc997d3e931ff3d58d956` django_strawberry_framework/orders/sets.py
- `9682db07a0054937c80900d20519265b87121606` examples/fakeshop/apps/library/schema.py

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

### R1: unused policy copy on order_by-only requests

`django_strawberry_framework/list_field.py::_normalize_list_arguments` reads
the policy whenever ANY argument is supplied, but only the offset and limit
branches consume it, so an order_by-only request pays a contextvar read plus
a small policy copy for nothing. Rejected: sub-microsecond cost on a
millisecond request, and threading the read lazily would complicate the
straight-line validator. Trigger: profiles attribute a material share of
list-request time to the unused copy, or the validator is restructured
anyway.

### R2: policy copied twice per argument-bearing request

Once here and once inside
`django_strawberry_framework/resource_policy.py::_windowed_rows`. Rejected:
copy-per-read is the documented isolation contract (the reader never returns
the armed object or the default singleton); threading one copy across seams
would reunite the authority the copies separate. Trigger: a contract change
making policy reads shareable, which is a maintainer and security decision,
not a performance fix.

### R3: `_selected_ordering` runs twice per offset-guard evaluation

Once via
`django_strawberry_framework/list_field.py::_has_deterministic_ordering` and
once via
`django_strawberry_framework/list_field.py::_is_model_default_ordering_active`
when the active-input branch runs. Rejected: the duplicated work is a
handful of attribute reads, and term classification itself runs at most once
per request (verified in discharge item 6). Trigger: profiler evidence.

### R4: non-integer values render twice on the rejection path

The call site passes an already-described value and
`django_strawberry_framework/list_field.py::ListArgumentError.__init__`
passes it through
`django_strawberry_framework/utils/truth.py::text` again. Rejected: the
error path only, and both passes are small string renders. Trigger: error
construction becomes hot (control-flow-by-exception in a loop; no such
caller exists). Noted for the Mechanics sibling in Handoff.

### R5: deferred orders import per qualifying request

`django_strawberry_framework/list_field.py::_order_normalization_scope`
imports the capture scope when `offset > 0` arrives with `orderBy` on an
orderset target. Rejected: a `sys.modules` hit after first use, and the
deferral keeps `orders` out of the package-root import graph by design.
Trigger: an import-graph change permitting a module-level import.

### R6: active-terms check re-normalizes input on every offset request

`django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms`
runs the consumer normalization one to two extra times per `offset > 0`
request. Rejected here: the re-normalization is that module's documented
purity check, linear in the input size, and from this file it is one
conditional call owned by the orders item. Trigger: the owning item
redesigns the attestation check.

Handoff: This pass is complete with no findings: the file builds lazy
querysets per request and never evaluates, iterates, counts, or writes
anything, so every query-shape and per-row entry discharges statically; the
only schema reads sit on error branches (verified at all three call-site
families); the import-time story closes because every third-party module
list_field names is loaded before it; and the six rejections above are the
closest calls, each with its trigger. The sync and async pipelines are
symmetric in cost (the async side adds sequential awaits only, none in
loops), so no coloring-specific finding exists. Two notes for siblings: the
plan's Routed Comments lead on `_validate_djangotype_target`'s
future-framing sentence is left untouched for the Comments pass, and R4's
error-path double render is flagged for the Mechanics pass to judge as
redundancy, not performance. No workspace run was taken and none is owed;
if a verifier wants numbers behind the rejections, the probe shape is a
timeit-median scratch script at this item's performance address, but nothing
in this record depends on it.

## Verification (Performance)

Tree check (Verify step 1): `git diff
8d5cb7ac968f96f5123ad24c3eb2e72c7249b897 --
django_strawberry_framework/list_field.py
examples/fakeshop/test_query/test_library_api.py` hashes
`e2855a5e71b34f320a52ca37c38f857678573c5071bdcada3f96d37451ed98bf`,
equal to `docs/review/temp-tests/list_field/diff/pass-1.diff`. The tree
carries exactly the change sent; grading it. The unfiltered ITEM stat
adds only `docs/dry/dry-0_0_15.md` and `docs/review/review-0_0_15.md`
(Worker-0/other-flow bookkeeping outside the item fence, matching the
`## Implementation (Worker-2)` attribution).

Proof lines: none. The review record carries no Proof line (no findings;
"no Proof needs a cell"), and neither sibling record holds a
`## Cross-axis (for Performance)` section (both record no cross-axis).
Zero lines to run verbatim, zero workspace runs taken, none owed.

Numbers reproduced: none exist. The reviewer recorded no before/after
figure and took no workspace run; Worker-2 reported no number (prose-only
inverse proof instead). There is no "before" figure to confirm against
the bench baseline or the `before` copy. No bench figure moves.

Whole-diff reading: read all 27 changed lines of `pass-1.diff` (14+/13-,
7 hunks, 2 files) through this axis. Every changed line is docstring
prose or a `#` / `#:` comment: M1 `_validate_djangotype_target`
docstring, M3 `_APPROVED_ORDER_AGGREGATES` comment, L1
`_handle_non_queryset_rejections_async` docstring, M4 `DjangoListField`
docstring, M2 factory-site comment, M5/M6 live-test docstrings. Zero
executable lines. Corroboration: both `--code-digest` commands exit 0
with digests identical to the report —
`sha256:95fb1b0d9d05ce013be06fbfbbf712a09a8cc52642e8ba878b5d83e7b014fc68`
(list_field.py) and
`sha256:43b8fbed999ed6705137d3b1531bccdf360a756f91dc78858333ccec9a99dc1a`
(test_library_api.py). No number can move on this diff.

Attacks, all passing, all static in the shared tree:

- Import-time: 0 import lines in the diff; the import graph in the
  review Trace still holds byte for byte.
- No `__doc__` / `getdoc` reader exists in `list_field.py`, so no
  runtime observes the changed text.
- Path class re-affirmed hot for the same reason: the `_default` /
  `_wrap` resolver closures are byte-identical per the digest.
- R1-R6 reopen triggers: none tripped. Each needs a code, profile, or
  contract change; prose moves none.
- Other cardinality, flavor, cell, caller: the change is color-blind
  (no pipeline line touched), cell-blind (no SQL, alias, or dialect
  surface), and caller-blind (no signature or behavior change).
  Sharded and pg remain inapplicable by construction, as at review.

Disputes: none recorded. Worker-2 disputed nothing (every finding
`implemented` or `deferred`); nothing judged.

Test tier / failability: none owed. No code change exists to fail, and
no gate relies on a prose finding (prose-only owes no permanent test
and no manifest). State so.

Cells unverified: none.

Fingerprints (`git hash-object` at verify time): list_field.py
`6a1dba1af04428d4fc67864c2beb1af755fc387c`, test_library_api.py
`4acc4821d8adb23b2de8a743d351f94567932c14` (both equal Worker-2's
after); rev-list_field.md `42fc4e72`, .performance.md `122571cb`
(pre-section), .mechanics.md `1a72beb1`, .comments.md `a3ccbf82`.

Verdict: verified. Prose-only pass on a no-findings axis; no number
moves, no new problem, no gap.

Handoff: Performance verification is complete with nothing open. The
only evidence a future pass could want is the two `--code-digest`
identities re-run above (exit 0, digests match the report) and the
27-line prose census of `pass-1.diff`. No workspace copy was opened;
scratch `docs/review/temp-tests/list_field/verify-performance-1/` holds
no probe because every check was static. The Comments verifier owns the
grade of the landed wording; nothing in this section constrains it.
