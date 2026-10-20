# Review · Mechanics: `django_strawberry_framework/relay.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=04fd0769352ba604a1db2942738f8dab9f630b18

## Trace

Read the whole live target (634 lines) plus every contract source and
neighbor the trace leads through: the decode primitive
(`django_strawberry_framework/types/relay.py::decode_global_id`,
resolve-then-enforce incl. the uniform-`ConfigurationError` promise), the
stamp honor half
(`django_strawberry_framework/types/relay.py::install_is_type_of`), the
id-attr stamp/default
(`django_strawberry_framework/types/relay.py::_stamp_relay_id_attr`,
`::_resolve_id_attr_default`, `::_resolve_id_default`) and the composite-pk
gate (`::_check_composite_pk_for_relay_node`), the node defaults
(`::_resolve_node_default`, `::_resolve_nodes_default`,
`::_apply_node_filter`, `::_order_nodes`), the shared target guard
(`django_strawberry_framework/list_field.py::_validate_relay_djangotype_target`
+ `::_validate_djangotype_target`), the ledger read
(`django_strawberry_framework/types/finalizer.py` no-Node-types check), the
deadline (`django_strawberry_framework/resource_policy.py::check_deadline`),
the write consumers
(`django_strawberry_framework/mutations/resolvers.py::coerce_lookup_id`,
`django_strawberry_framework/utils/write_values.py::type_check_relation_id`
+ `::decode_visible_relation_ids`), the pipeline reader
(`django_strawberry_framework/utils/write_transaction.py::current_write_pipeline`),
the queryset primitives
(`django_strawberry_framework/utils/querysets.py::model_for`,
`::coerce_field_value_or_none`, `::reject_async_in_sync_context`),
`django_strawberry_framework/registry.py::definition_for_graphql_name` +
`::get`, `django_strawberry_framework/utils/truth.py::mro_attr` +
`::static_attr`, the package root exports, the own test module
(`tests/test_relay_node_field.py`, whole), spec-032 Decisions 3/4/5/8/11
and Edge cases, spec-031 Decision 11, spec-047 Decision 9, spec-053
Decision 3 contract 4 (the deferred-import whitelist), and both sibling
axis records whole with their Handoffs (they landed mid-pass; Performance
F1/C1 and Comments R10 bear directly on this record - see Findings and
Handoff). Orientation via `review_inspect.py` (leads only).

Target fingerprint as read: `e75e2b66a9b406f60d55e952a001d640392331c1`.
`git diff ITEM_BASELINE -- django_strawberry_framework/relay.py` is empty:
the concurrent dirt (truth/lazy migration) predates the item baseline and
the file has not moved since. The plan's Routed lead for this item
(connection.py Comments, observed: `test_relay_connection.py` temporal
wordings plus bare `(Decision 5)` pointer quality) is pure prose quality
with zero Mechanics content - judged out-of-axis; the owning Comments pass
has already judged it (its R1/R2).

Cells: default only. Sharded and pg are inapplicable by construction: L1
is import placement reaching no database, alias, or dialect decision; C1
and C2 are prose. The verifier judges; the gate re-runs the pinned
package-tier nodes in all three suites for free.

Probe evidence (all at `review/relay.py/mechanics`, package digest
`sha256:ecded019e560d47d15a90b09ad8e21899e087da4bbf0bf385f2cdef5855d7152`):

- `review-20260929T081127-022d81`: root-import closure
  (`write_transaction` already loaded).
- `review-20260929T081153-5261ab`, `review-20260929T081154-e3bf07`,
  `review-20260929T081154-0562e0`: hoisted import green in relay-first,
  root, and write_transaction-first orders (copy-only patch, since
  restored).
- `review-20260929T081200-e0b014`: `tests/test_relay_node_field.py`
  28 passed on the hoisted copy.
- `review-20260929T081227-243d7f`: 301 passed on the narrowed-except
  copy (relay + mutations + write_values + forms + serializer
  resolver modules; copy-only patch, since restored).
- `review-20260929T082034-7a7f66`: reverse-relation id slot yields a
  `ManyToOneRel` (not `None`), coerces to `None`, decodes
  `UNCOERCIBLE_PK` with 0 queries (1 passed).
- `review-20260929T082419-4446b1`: GFK id slot yields the field,
  coerces by identity, and the raw literal raises Django `FieldError`
  at the filter (1 passed).

Fingerprints of everything inspected (a finding's Freshness lists only
files beyond these): `django_strawberry_framework/relay.py` e75e2b66,
`django_strawberry_framework/types/relay.py` 4b2a9df5,
`django_strawberry_framework/list_field.py` f5b0183e,
`django_strawberry_framework/resource_policy.py` cc3f9d80,
`django_strawberry_framework/types/finalizer.py` b9d8acb2,
`django_strawberry_framework/utils/write_transaction.py` 4a83f43d,
`django_strawberry_framework/utils/querysets.py` 8fc556d5,
`django_strawberry_framework/utils/truth.py` d5c96bc8,
`django_strawberry_framework/utils/lazy.py` 770f36ae,
`django_strawberry_framework/utils/__init__.py` 1a4c2ec8,
`django_strawberry_framework/utils/errors.py` 6a389474,
`django_strawberry_framework/utils/canonical.py` ce7f40f4,
`django_strawberry_framework/registry.py` 27358cbc,
`django_strawberry_framework/__init__.py` 0ef72601,
`django_strawberry_framework/mutations/resolvers.py` c9cff059,
`django_strawberry_framework/utils/write_values.py` 72f132f0,
`tests/test_relay_node_field.py` af4866a1,
`tests/test_relay_connection.py` fe2b2d24,
`docs/review/rev-relay.performance.md` c22ecb5e,
`docs/review/rev-relay.comments.md` 9847c1de,
`docs/review/review-0_0_15.md` 46017cde,
`docs/review/rev-relay.md` 046befd1 (all `git hash-object`,
abbreviated). No symbol is moved or renamed, so no `--cited-by`
sweep is owed.

## Findings

### High

None.

### Medium

None.

### Low

#### L1: `current_write_pipeline` hides at function level with no cycle behind it

- Observation:
  `django_strawberry_framework/relay.py::_resolve_real_pk` imports
  `current_write_pipeline` from
  `django_strawberry_framework/utils/write_transaction.py` inside the
  `using is None` branch, with no comment naming a cycle. There is no
  cycle: the `write_transaction` runtime closure (`..exceptions`,
  `..utils.errors`, `.truth`, `.canonical`) never reaches `relay`, no
  `utils` module imports package-`relay` at module top (the one
  utils-side edge, `write_values.py::type_check_relation_id`, is
  itself function-local per the spec-053 whitelist), and `relay`'s own
  top-level edges (`list_field`, `registry`, `resource_policy`,
  `types.relay`, `utils.*`) never lead back to it. The import also
  buys no laziness: `write_transaction` is already in the
  package-root import closure. Every sanctioned deferred import in the
  package documents its cycle (spec-053 Decision 3 contract 4 lists
  exactly three, and this site is not among them); this one neither
  documents nor needs deferral.
- Evidence: import-closure probe
  (`write_transaction loaded: True` at root import,
  `review-20260929T081127-022d81`); hoist patch (module-top import +
  bare call) verified green in all three import orders
  (`review-20260929T081153-5261ab`, `review-20260929T081154-e3bf07`,
  `review-20260929T081154-0562e0`) with the own module suite at 28
  passed (`review-20260929T081200-e0b014`); full edge inventory above
  read at the Trace fingerprints.
- Impact: a reader auditing the import graph must re-derive the
  negative; a future cycle-introducing edit gets no signal from this
  site either way. Bounded clarity/consistency fix; zero behavior
  change by construction.
- Severity: Low.
- Recommendation: hoist to the module-top import block (owner: this
  file). If Performance F1's batching lands first and relocates the
  recovery, fit the hoist to the code as F1 left it; if F1's
  restructure already removes the function-local import, record this
  finding discharged by F1.
- Must not change: the recovery behavior (explicit `using` still wins;
  `None` pipeline still keeps default-manager behavior), every
  `GlobalIDDecode` status, query counts.
- Proof: `grep -c '^from .utils.write_transaction import'
  django_strawberry_framework/relay.py` prints `1` and `grep -c '^ *
  from .utils.write_transaction import'
  django_strawberry_framework/relay.py` prints `1` (no indented
  duplicate); `uv run python scripts/workspace.py run
  review/relay.py/verify-mechanics-<n> -- python -c "import
  django_strawberry_framework.utils.write_transaction,
  django_strawberry_framework.relay"` exits 0; `uv run python
  scripts/workspace.py run review/relay.py/verify-mechanics-<n> --
  pytest
  tests/test_relay_node_field.py::test_decode_model_global_id_resolves_custom_node_id_to_real_pk
  tests/test_relay_node_field.py::test_decode_model_global_id_custom_node_id_no_row_is_uncoercible
  --no-cov -n0` reports `2 passed`. No new permanent test: the move
  is behavior-neutral (suite-green both sides) and the two pinned
  nodes exercise the recovery branch.
- Freshness: none beyond Trace.
- Owner + contract source: this file owns the import block; the
  layering contract is spec-053 Decision 3 contract 4 (deferred
  imports exist only to break real cycles and are whitelisted with
  their documented cycle).

## Rejected

Looks-for map (every entry discharged): rule at caller instead of
owner -> R5, R6; policy in adapter / mechanism in policy layer ->
R12; contract sources vs body -> C1, C2, R8; unreachable branch ->
R7; mode flag for named adapter -> R7; state in two places -> R7;
dependency direction -> L1, R9; settings at import -> R7;
`__all__` vs public surface -> R7; two sites one rule -> R2, R3, R4;
sync/async twins -> R3; guard one flavor lacks -> R1, R10, R11.

- R1: narrowing `decode_model_global_id`'s `except Exception` to
  `except ConfigurationError`. `decode_global_id` promises every
  failure mode as one uniform `ConfigurationError` (input gate,
  `ValueError` parse wrap, `LookupError` wrap, registry miss/ambiguity
  raises, strategy rejection - all read), and no reachable input
  raises anything else: the narrowed copy passes the exact same 301
  tests across all five decode-consumer modules
  (`review-20260929T081227-243d7f`). Narrowing is unobservable today,
  so per REVIEW it is not a finding. Trigger: a reachable input
  observed to raise non-`ConfigurationError` (then the breadth is
  load-bearing and owes a pinning test), or a maintainer decision
  that fail-loud-on-decode-bug beats non-raising totality.
- R2: consolidating the two factories' construction preludes
  (validate target + validate directives + ledger append). Change
  challenge ("add a construction guard"): 2 edit sites, but each is a
  distinct factory's declaration carrying its own name literal and
  its own ordering rationale; a shared helper still takes the name
  and hides the declaration-site comment. One rule, already
  single-sited in the three called primitives. Trigger: a third
  refetch factory, or a guard with shared non-name logic.
- R3: consolidating the sync/async per-type loops in
  `DjangoNodesField._resolve` (plus the single resolver's unified
  path). Compared line by line: resolve -> await-or-reject -> length
  check -> stamp -> interleave on both colors; differences are color
  duties only (await point, `reject_async_in_sync_context` on sync,
  sequential awaits per the documented Django connection rule), and
  the pure decisions (`_interleave`, `_check_nodes_result`,
  `_check_typed_match`, `_node_id_slot`) are colorless and shared.
  Trigger: a behavioral arm appearing on one color only.
- R4: consolidating `_coerce_pk_or_none` with
  `write_values.py::coerce_relation_pk_or_none`, or
  `_decode_or_graphql_error` with `decode_model_global_id`'s
  try/except. The coercers differ in their field basis (resolved
  id-slot field vs `_meta.pk` - the documented counterpart split,
  and unifying them reintroduces the `"007"` mistyping the docstring
  pins); the decoders differ in surface (raising `GraphQLError` vs
  non-raising status). Similar shape, separate contracts. Trigger: a
  caller needing one surface's shape from the other body.
- R5: moving the write-pipeline alias recovery out of
  `_resolve_real_pk` (e.g. into `type_check_relation_id`, or forcing
  every caller to thread `using`). The current split is the
  documented API: `coerce_lookup_id` threads explicitly because it
  holds the alias, while the relation riders reach the primitive
  through flavor handlers that cannot thread one - both owner
  docstrings prescribe exactly this. Trigger: a rider that can thread
  its alias but does not.
- R6: rule-at-caller placements (typed-match check, ledger check,
  stamp/honor split, guard wrapper). Each sits at its spec owner:
  Decision 4's mismatch error at the field (it needs both decoded
  types plus GraphQL names), Decision 8's ledger check at the
  finalizer (factories run before type imports - the only settled
  reader), the stamp here with the honor half in `install_is_type_of`
  (verified both directions), the target guard delegating to
  `list_field.py::_validate_relay_djangotype_target` (single site,
  connection field co-caller). Trigger: a second definition of any
  of these rules.
- R7: the structural non-issues. No unreachable branch (every arm
  carries a test or a live caller: `FieldDoesNotExist` fall-through,
  `using`-recovery, generator materialization, the `AttributeError`
  suppress, empty-ids, all four statuses); no mode flag (`using` and
  bare/typed-`None` are documented spec shapes); no dual state (the
  ledger is appended here, read by the finalizer, cleared over the
  bus - one record); no settings read at import (corroborates
  Performance R6); `__all__` matches the root exports while the
  internal shared names follow the package pattern (cf.
  `mutations/resolvers.py::coerce_lookup_id`, shared by path, never
  re-exported). Trigger: any listed shape appearing.
- R8: `check_deadline` running before the decode (and the batch
  empty-list exemption). The seam is spec-047 Decision 9's enumerated
  `relay.py` placement ("before the decode ... after the empty-ids
  short circuit"), quoted verbatim in the comments (Comments R8
  verified the language); the single field has no empty case to
  exempt. Trigger: Decision 9 reworded, or an oracle pinning
  decode-before-deadline precedence.
- R9: `_check_typed_match` reading
  `__django_strawberry_definition__` by direct attribute access while
  siblings migrated to `truth.*`. The gate is green
  (`check_truthful_reads.py --check`: tier-1 0, errors 0, shared
  tree), and both reads sit past decode on framework-registered
  types. A style migration with no contract behind it is not a
  Mechanics finding. Trigger: the gate flagging the site, or a
  hostile-metaclass input reaching it.
- R10: single-vs-batch guard parity. Deadline, typed-match, coercion,
  async-in-sync rejection, and the stamp run on both flavors; the
  length check is batch-only because the single path has no
  positional contract to check. Trigger: a guard added to one flavor
  only.
- R11: reverse-relation id slots (e.g. `resolve_id_attr()` ->
  `"items"`). Verified fail-closed: the slot yields the `ManyToOneRel`
  object, coercion maps it to `None` (not a `Field`), and the write
  decode reports `UNCOERCIBLE_PK` with zero queries
  (`review-20260929T082034-7a7f66`); the read path nulls before any
  query the same way. No contract row promises more for an
  incoherent slot, so no defect; the docstring sentence describing
  this sub-case is imprecise, which is C2, not this. Trigger: a
  reachable incoherent slot crashing or leaking existence (see the
  routed GFK lead in Handoff for the one sharp edge).
- R12: the write-side primitive living in the root-fields module
  (`decode_model_global_id`, `GlobalIDDecode`, `DecodeResult`,
  `_resolve_real_pk` beside the factories). Spec-032's placement
  Decision puts the whole typed-`GlobalID` consumption contract here
  precisely so read and write share `_node_id_slot` and
  `_coerce_pk_or_none` - verified shared by call, never re-derived.
  Trigger: a second id-slot or coerce definition appearing anywhere.

## Cross-axis (for Comments)

### C1: `decode_model_global_id` docstring names a consumer that no longer exists

- Observation: the docstring's single-source sentence names the root
  `id:` decode (``coerce_lookup_id``) and the relation ``<field>_id``
  decode (```_decode_relation_id_set```) as the two consumers. The
  second name is dead: package-wide, ``_decode_relation_id_set`` has
  zero definitions and zero calls - its only occurrence is this very
  docstring. The live relation consumer is
  `django_strawberry_framework/utils/write_values.py::type_check_relation_id`
  (called from `::decode_visible_relation_ids`, which the model, form,
  and serializer flavors share).
- Evidence: `django_strawberry_framework`-scoped search for
  `_decode_relation_id_set` returns the single docstring line;
  `mutations/resolvers.py:1281` (`coerce_lookup_id`) and
  `write_values.py:152` (`type_check_relation_id`) are the only live
  `decode_model_global_id(` call sites. Corroborated by
  `docs/dry/dry-rule-typed-globalid-decode.md` ("no such symbol exists
  in the package").
- Impact: a reader tracing the typed-id contract chases a phantom
  second consumer; the single-source claim stays true but its census
  is stale. (Note for Worker-0: Comments R10 in this run asserts
  "both named consumers call it" - the package-wide grep above
  contradicts that sentence; the Comments verifier grades the landed
  text, not the disagreement.)
- Severity: Medium (stale cross-reference in a shared helper's
  contract docstring; the Comments verifier grades the landed text).
- Recommendation: reword at the owner (this docstring) to name the
  live consumers (`coerce_lookup_id`, `type_check_relation_id` /
  `decode_visible_relation_ids`).
- Must not change: n/a (prose finding).
- Proof: `grep -c '_decode_relation_id_set'
  django_strawberry_framework/relay.py` prints `0` (1 today); the
  landed docstring names only live consumers and earns grade true.
- Freshness: none beyond Trace.

### C2: `_node_id_slot` docstring overclaims the non-concrete handling

- Observation: "a consumer ``relay.NodeID[...]`` over a NON-concrete
  attr yields ``None`` ... both consumers fall through with the raw
  literal" describes only the non-field sub-case (`FieldDoesNotExist`
  -> `None` -> raw passthrough for consumer overrides). A reverse
  relation yields its `Rel` object (not `None`) and both consumers
  see `None` via the coerce (read: `null` with no query; write:
  `UNCOERCIBLE_PK`) - verified in R11's probe. A non-concrete
  forward field (e.g. `GenericForeignKey`) yields the field object
  and the raw literal flows onward (verified through the coerce;
  filter behavior is the routed lead in Handoff). Three sub-cases,
  one sentence.
- Evidence: R11 probe (`review-20260929T082034-7a7f66`); GFK probe
  (`review-20260929T082419-4446b1`, slot yields the field, coerce is
  identity).
- Impact: bounded; a maintainer extending the id-slot rule misreads
  which shapes take which path.
- Severity: Low (internal precision; behavior fails closed).
- Recommendation: distinguish the three sub-cases at the owner (this
  docstring): non-field -> `None` -> raw passthrough; reverse
  relation -> `Rel` object -> `None` via the coerce; non-concrete
  forward field -> field object -> raw onward.
- Must not change: n/a (prose finding).
- Proof: `grep -c 'NON-concrete attr yields'
  django_strawberry_framework/relay.py` prints `0` (1 today at line
  137); the landed docstring distinguishes the sub-cases and earns
  grade true.
- Freshness: none beyond Trace.

Handoff: I read the whole target, all decode/coerce/stamp/ledger
neighbors, both write-consumer chains, the own test module whole, the
spec placement and seam Decisions, and both sibling records whole.
Result: one Low Mechanics finding (L1, hoist the cycless local
import), two Comments cross-axis findings (C1 dead consumer name -
Medium, contradicting this run's Comments R10 sentence with a
package-wide grep; C2 id-slot docstring precision - Low), twelve
rejections with triggers, zero defects. Three notes for Worker-0.
(1) Performance R7 calls the L1 import "a documented import-cycle
dodge" - it is neither documented (no comment names a cycle) nor a
dodge (hoist proven green in all three import orders, module already
in the root closure, site absent from the spec-053 whitelist); R7's
own trigger anticipates the hoist with F1's batching, so L1 and R7
converge rather than conflict, but the R7 premise sentence should
not block L1. (2) Performance F1 implements before this axis: if its
restructure already removes the function-local import, L1 is
discharged by F1 and its Proof's end-state greps still govern. (3)
Routed leads for other items: (a) the `types/relay.py` item
(Mechanics): a NodeID/override id slot naming a `GenericForeignKey`
(or any unfilterable attr) reaches a raw Django `FieldError` at
request time on both read and write (verified through the coerce and
the filter call,
`review-20260929T082419-4446b1`) - no contract demands graceful
handling of a non-column slot, so this is a new-guard question
(fail-loud at declaration/finalize beside
`_check_composite_pk_for_relay_node`), not a defect here; (b) the
`mutations` item (Comments): the
`tests/mutations/test_resolvers.py:1173` ``_decode_relation_id_set``
docstring mention is the C1 twin in that item's file. Open threads:
none on this axis; the GFK filter exception type is verified Django
`FieldError`, and every other behavior claim above carries its run
id. Scratch: `docs/review/temp-tests/relay/mechanics/` (`inspect/`,
`relay.json`, `test_probe_revslot.py`, `test_probe_gfkslot.py`); the
workspace copy is restored to pristine (both copy-only patches
reverted; the probe test files removed from the copy).

## Verify mechanics

Precondition: the live tree carries exactly the change under grade.
`git hash-object` gives `relay.py` f5760b45, `utils/write_values.py`
13548c76, `tests/test_relay_node_field.py` d4ce0c7d,
`tests/utils/test_write_values.py` 9f459e2f - the end-state blob ids of
`docs/review/temp-tests/relay/diff/pass-1.diff`, and the live item diff
is byte-identical to it (`cmp` IDENTICAL). All runs below at
`review/relay.py/verify-mechanics-2` (slot-3, package digest
`sha256:d677641c...`, the same digest the Performance verifier measured,
copy `fresh` on every run except the two noted copy-mutating runs).
This address is the re-dispatch after verify-mechanics-1 was
infrastructure-BLOCKED (slot-4 venv corrupt, no verdict); its probe file
was reused and fixed here (see Attacks).

### L1: hoisted, not discharged-by-F1 - pass

End-state greps (shared tree, static): `grep -c
'^from .utils.write_transaction import'
django_strawberry_framework/relay.py` prints `1`; `grep -c '^ *from
.utils.write_transaction import'` prints `1` (no indented duplicate).
Import orders, all exit 0: relay-first
`review-20260929T093848-090f1e`, write_transaction-first (the Proof's
exact form) `review-20260929T093859-45a35c`, package root
`review-20260929T093902-b39556`. Pinned recovery nodes
`review-20260929T093906-63b0f6`, `2 passed`. Verdict on the
disposition: HOISTED as its own hunk (module-top import plus bare
calls in both `_resolve_real_pk` and the F1 twin
`_resolve_real_pks_batched`) - F1's restructure kept the recovery at
the primitive, so L1 landed rather than discharged. The hoisted edge
is acyclic: `write_transaction`'s live top-level closure is exactly
the record's inventory (`..exceptions`, `..utils.errors`, `.truth`,
`.canonical`, none reaching `relay`), and no `utils` module imports
package-`relay` at module top.

### F1/F2/F3 introduce no Mechanics defect - pass

- Delegation boundaries intact. `decode_global_id(` has exactly two
  call sites (`relay.py:120` the raising READ path, `relay.py:331`
  the shared `_decode_and_coerce` half); `except Exception` exactly
  one site (`:332`, the breadth moved verbatim). No second decoder:
  the batched mapping lives beside the primitive in `relay.py` (the
  spec-032 owner per R12) and composes the shared half.
  `decode_model_global_id(` production callers are exactly
  `mutations/resolvers.py:1281` and `write_values.py:152`;
  `_decode_and_coerce(` callers exactly `relay.py:432` and
  `write_values.py:318`; `_resolve_real_pk` still called at
  `relay.py:437`.
- Fail-closed preserved on every status arm. The four
  `_decode_and_coerce` arms match the old single-half verbatim
  (DECODE_FAILED / WRONG_MODEL / UNCOERCIBLE_PK / OK);
  `decode_model_global_id` returns non-OK intermediates as-is and
  maps no-row to UNCOERCIBLE_PK; the set decoder maps every non-OK
  plus every no-row mapping to the uniform `relation_field_error`.
  The decode-before-any-query phase structure (Decision 5) is
  intact, and the only error-order delta vs the old loop (a later
  malformed member now wins over an earlier no-row) is unobservable
  (identical uniform surface; fewer queries on error paths only).
  Reverse-relation slots still fail closed (the coerce gates the
  mapper: `None` never reaches it); GFK slots behave exactly as
  before (identity coerce, raw literal to the filter) and stay the
  routed `types/relay.py` lead. Pinned: the five-module run below,
  the F1 count pin's no-row leg, and my probe (WRONG_MODEL /
  DECODE_FAILED / UNCOERCIBLE through the new set path, all uniform
  error with zero queries).
- No dead code. Both mappers called; `type_check_relation_id`'s
  GlobalID branch still serves the single decoders; ruff F-clean.
  The `slot=None` fallbacks are live API (`_coerce_pk_or_none`'s
  via the single resolver; `_resolve_real_pk`'s as the documented
  omitted-slot default), not dead branches.
- Sync/async twins not drifted. The pass diff holds zero
  `_gather`/`await result` lines (async untouched); F2 guards are
  sync-only and behavior-neutral (the added condition is the
  helper's own `inspect.isawaitable(value)` line, raise-path
  arguments byte-identical); F3's memos sit before the color split.
  R3's trigger (a behavioral arm on one color only) not tripped.
- No new settings-at-import: `settings`/`django.conf` greps empty
  in both touched production files; the hoisted import pulls no
  settings reader (closure above). `__all__` byte-identical.
- Import graph still acyclic. New edges: the L1 top-level edge
  (clean closure, above) and the function-local `from ..relay
  import` at `write_values.py:311` (deferred, acyclic by
  construction; same file, target, and cycle as the whitelisted
  site (ii)). One staleness, not a defect: spec-053 Decision 3
  contract 4 says "exactly three" sanctioned deferred imports, and
  this is a fourth site of the same sanctioned shape - no
  import-linter gate exists (absent from pyproject/uv.lock/
  pre-commit/CI), so it is archived-spec prose, routed to Worker-0
  under Open threads, never a code finding.

### Suites - pass

Own modules `review-20260929T093921-599407`, `60 passed`.
Five decode-consumer modules (relay_node_field, write_values,
mutations + forms + serializer resolvers - each confirmed to
exercise the decode surface) `review-20260929T093947-028d6b`,
`305 passed` = the record's 301 baseline plus exactly the 4 new
F1/F2/F3 pins.

### Attacks and revert demonstration - pass

- Set-decode arms probe (scratch, 4 tests):
  `review-20260929T094039-a44e3a`, `3 passed` (WRONG_MODEL,
  short-circuit, and single-bad-member zero-query arms), extended
  to `review-20260929T094324-beccf9`, `4 passed` with the
  mixed raw-pk + GlobalID positional test (the new positional-fill
  composition: `[raw, gid, raw]` resolves each member into its own
  position). The probe's first run (`review-20260929T094011-bd8b50`,
  3 failed) was a probe fixture bug (`Item` needs a `category`),
  fixed in the probe; no code involved. Probe files removed from
  the copy after each run.
- Revert in copy: baseline `write_values.py` (per-id loop) under
  live `relay.py`, `review-20260929T094208-8d59bb` - the F1 count
  pin fails exactly as predicted (3 vs 2 queries at K=2; the `pks`
  assertion passes, so pre-fix behavior differs only in count:
  worse). Copy restored to the graded digest and the pin re-run
  green (`review-20260929T094220-efb5d3`, `1 passed`).

### Rejections R1-R12 - all stand

R1 (breadth preserved at the one moved site; 305 green subsume the
301); R2 (factory preludes untouched); R3 (above); R4 (coerce split
intact, rule body untouched); R5 (recovery stays at the primitive,
riders thread nothing); R6 (placements untouched, new helpers at
the R12 owner); R7 (every new arm covered: `slot is None` both
sides, `if not groups`, `if pending` both sides, isawaitable both
sides; `slots` dicts are per-call locals, no new module state; no
settings; `__all__` identical); R8 (deadline placement untouched);
R9 (no new truth-shape reads; `check_truthful_reads.py --check`
tier-1 0, errors 0); R10 (both sync flavors got the identical F2
guard; length check still batch-only by contract); R11 (reverse
slots fail closed through the new path, coerce before mapper);
R12 (one slot rule, one coercer - call-site census above).
No trigger tripped. C1/C2's code facts corroborated (live-consumer
census exact; slot rule body untouched); the landed prose is the
Comments verifier's pass, not re-graded here.

### Cells

Default only. Sharded and pg are inapplicable by construction: L1
is import placement reaching no database; the status arms and
query counts are backend-agnostic; the alias pin is a mock. The
Performance verifier additionally ran every pin green in both
cells; the gate re-runs the whole orbit in all three suites.

### Lint gates - pass

Shared tree: `ruff check` (All checks passed), `ruff format
--check` (4 files already formatted),
`check_trailing_commas.py --check` (violations 0) on the four
touched paths; `check_citations.py --check` on the tree (1303
resolve, 0 violations).

Scratch: `docs/review/temp-tests/relay/verify-mechanics-2/`
(`test_probe_set_decode_arms.py`, the fixed+extended probe).

Status: verified. Open threads: (1) spec-053 Decision 3 contract
4's "exactly three" sentence is stale by one site of the same
sanctioned shape (`write_values.py:311`; no enforcing gate
exists) - Worker-0 routes to `## Decisions` (spec-prose update vs
leave). (2) Observation, not a defect: the 3-line pipeline-alias
recovery now sits in two sites (single + batched twins) -
change-challenge count 2, accepted (twin structure, rule-of-three
size, both docstring-documented; a helper would trade 3 lines for
indirection). No new defects; no `disputed` findings to judge
(Worker-2 disputed none on this axis).

Handoff: Mechanics pass 1 verifies clean. L1 is hoisted (own
hunk, all three import orders exit 0, pinned nodes green); F1/F2/F3
preserve every status arm, delegation boundary, twin, and the
acyclic import graph; 305/305 decode-consumer rows green; the
revert run shows pre-fix worse by count alone; R1-R12 stand with
triggers. Judgment calls for a later reader: (1) the mixed-set
error-order delta is unobservable only because every arm maps to
the identical uniform surface - a future caller distinguishing
those arms reopens it; (2) the `==`-vs-`=` match parity rests on
the supported SQLite/Postgres matrix (Performance Handoff), and
any divergence there fails closed (spurious uniform error, never
a wrong row); (3) the twin-recovery acceptance above. Copy left
pristine (probe + baseline file removed; final digest d677641c).
