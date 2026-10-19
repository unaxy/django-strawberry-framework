# Review · Mechanics: `django_strawberry_framework/list_field.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8d5cb7ac968f96f5123ad24c3eb2e72c7249b897

## Trace

Read the whole live target (1748 lines) plus the inspect orientation
(`review_inspect.py` JSON + overview under scratch). Target is dirty vs HEAD
(truth-migration hunks); `git diff ITEM_BASELINE -- <target>` is empty, so the
reviewed text is exactly the item baseline. Fingerprint of the read:
`450e87cd` (full hashes below).

Callers/consumers followed: `connection.py::DjangoConnectionField` and
`relay.py::_validate_node_target` (the two importers of
`list_field.py::_validate_relay_djangotype_target`); package-root re-exports in
`__init__.py`; `orders/sets.py::OrderSet._input_has_active_terms` and
`orders/sets.py::capture_applied_order_normalization` (the guard's handoff
seam); `utils/querysets.py` runners and guards consumed by the pipelines
(`prepared_resolver_source`, `reject_awaitable_sync_source`,
`reject_residual_async_source`, `reject_async_iterable_in_sync_context`,
`is_async_only_iterable`, `wrap_async_queryset_adapter`,
`apply_orderset_sync` / `apply_orderset_async`,
`apply_type_visibility_sync` / `apply_type_visibility_async`, `base_queryset`,
`_LIST_ARGUMENT_VISIBILITY_POLICY`, `_SealPolicy`); `types/base.py`,
`types/definition.py`, `mutations/fields.py::_validate_mutation_target`
(twin-candidate validators); `extensions/resource_policy.py` and `schema.py`
(the other two `strawberry-definition` readers); `types/converters.py`
(the other `_field_label`).

Contract sources read: `docs/SPECS/spec-020-list_field-0_0_7.md` (shared
validator home), `docs/spec-050-list_field_arguments-0_0_15.md` Decision 1 +
wire-name/error-vocabulary sections, `docs/GLOSSARY.md`
`ListArgumentError` + list-offset-order-precondition anchors,
`tests/test_list_field.py` module docstring + defensive-branch pins,
installed Django 6.1 / strawberry 0.324.0 sources for every mirrored
behavior, and a scratch install of floor strawberry 0.316.0 for the two
upstream attributes the wire-name path reads.

Cells: no finding, so no cell-gated Proof exists; no workspace run was
needed. Every uncertainty below resolved to cited source (dependency
sources, specs, tests); nothing was measured. Cells unverified: none.

Fingerprints (`git hash-object` at review time):

- `django_strawberry_framework/list_field.py` 450e87cde13edc1bfc3c4d4a161c5540d1ac5277
- `django_strawberry_framework/connection.py` 1fca6266cd5f748915875badf1881680b599de37
- `django_strawberry_framework/relay.py` e75e2b66a9b406f60d55e952a001d640392331c1
- `django_strawberry_framework/orders/sets.py` 60859f2d54525acfdb3dc997d3e931ff3d58d956
- `django_strawberry_framework/orders/__init__.py` ed546f9c70d56d73e0d84a029e9e04f27da3934b
- `django_strawberry_framework/utils/querysets.py` 8fc556d582b313e4aedcddaa15f9a8480d88a46
- `django_strawberry_framework/utils/truth.py` d5c96bc8d191d3fce0a20140d8e91063bb466ec9
- `django_strawberry_framework/mutations/fields.py` 0e4d5ed1c7efbcbb4e70db9162f2ffc85460a699
- `django_strawberry_framework/extensions/resource_policy.py` 0134d83a9aa2db580b7b8180ded27a3d31b115c7
- `django_strawberry_framework/schema.py` 84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1
- `django_strawberry_framework/resource_policy.py` cc3f9d80b9d55af8b725a77c73aba3d8110e0037
- `django_strawberry_framework/sets_mixins.py` 088ddab0c0f68c0605bc4a440dfa3daa544452dd
- `django_strawberry_framework/__init__.py` 0ef72601ecac300ac87ff993af1b04a4f1bc335a
- `django_strawberry_framework/types/base.py` dc67f084cbc969d64b7b1f1ef18c388095d394f7
- `django_strawberry_framework/types/definition.py` 1c59a3feec53df2cc243557ab3aafde7fa6a518b
- `tests/test_list_field.py` d78aa5e79fee14b37564f856d3d4bc74e7d9630b
- `docs/GLOSSARY.md` 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd
- `docs/spec-050-list_field_arguments-0_0_15.md` 73fe1127a280bfcf791632f2b40dfd2f805b12ec
- `docs/SPECS/spec-020-list_field-0_0_7.md` 9fdf09b1eb3e65cbaf793cc0485139e4d8cae362
- `docs/review/review-0_0_15.md` 9301fdee767940dd08f192f16366259416ee473c
- `docs/review/rev-list_field.md` 3d23f97b9a75809e9ef634beda73d85335a72a88
- `docs/review/temp-tests/list_field/mechanics/list_field.json` 542b403876913dd392c4aea9ed07ec06b6610382

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

R1 — Relay-validator placement (rule at the wrong layer?). Rejected:
`list_field.py::_validate_relay_djangotype_target` is used only by
`connection.py` and `relay.py`, never by the list field itself, yet
spec-020 names `list_field.py` the home of the shared field-target
validation contract including the Relay-shaped superset. The placement is
contract, not drift. Trigger: the contract moves (spec edit) or a fourth
factory duplicates the guard instead of importing it.

R2 — Determinism-classifier placement (470 lines of ordering machinery in a
field module?). Rejected: `_has_deterministic_ordering`,
`_is_model_default_ordering_active`, `_selected_ordering`, and
`_check_nonzero_offset_guard` have no caller outside `list_field.py`; they
are module-private helpers of the list-only offset guard (connections are
cursor-based and need no offset rule). Trigger: a second surface needs the
verdict — then the classifier moves to an orders-owned home.

R3 — Contract-vs-body: glossary `ListArgumentError` anchor. Rejected (no
divergence). Dual bases, `__reduce__` shape (identical triple to
`resource_policy.py::ResourceLimitExceeded.__reduce__`; `vars(self)` vs
`self.__dict__` is the same object), stable `code`/`argument`/`reason`
extensions, `value` on both numeric reasons, `ceiling` only on
`over_ceiling`, neither on `queryset_required`, wire-type failures left to
GraphQL `Int` coercion — each verified against
`list_field.py::ListArgumentError.__init__` and its six raise sites. The
`argument always uses the active schema wire spelling` sentence reads on
the wire path, where it holds exactly; the `_DEFAULT_WIRE_NAMES` fallback
fires only for direct-call stubs with no executable schema, a shape
spec-050 sanctions explicitly. No reachable input produces a wrong active
spelling on supported strawberry (R9). Trigger: a wire execution reaching
the fallback with a live schema.

R4 — Contract-vs-body: offset-precondition anchor. Rejected (no
divergence). `offset: 0` accepted / positive refused with neither order
source (`_check_nonzero_offset_guard` early return + `order_required`
raise); extra ordering naming a real field qualifies as deterministic
(`_selected_ordering` EXTRA arm + field-path read) without authorizing
offset alone (model-default arm requires MODEL_DEFAULT source); a
resolver-private `.order_by` authorizes nothing by itself (EXPLICIT source
fails the model-default arm); `.reverse()` leaves the classified term set
unchanged (Django flips `standard_ordering` only); no pk tiebreaker or
`DISTINCT` anywhere in the pipelines. Trigger: a live verdict contradicting
any of these rows.

R5 — Unreachable branches. Rejected: every defensive branch is
test-reached. Package pins exist for the non-callable resolver, the
non-model definition, the unpublished wire name, the non-callable
`get_argument_definition`, and all four `_resolver_root_and_info`
`TypeError`s (`tests/test_list_field.py`); wire verdicts are live-pinned
per that module's docstring. Trigger: a branch surviving with neither a
package pin nor a live verdict.

R6 — Mode flags (`is_async_context`, `field`, `trusted_max_rows`).
Rejected: `is_async_context` selects one wrap call across two named call
sites (the default resolver always passes `False` because it dispatches
per call; the frozen sync consumer wrapper passes the ambient answer) —
a two-way branch, not an adapter family. `field` is a spec-sanctioned
message noun, `trusted_max_rows` a spec-047 policy coordinate.
Trigger: a third wrapping shape or a second consumer of the flag.

R7 — State in two places (`_ListArguments` derived flags, wire-name
fallback, ceilings). Rejected: `order_by_supplied` /
`any_argument_supplied` are the record's own memo alongside normalized
values (no second writer); the fallback spelling exists only where no
schema does (R3); ceilings are read per request from the policy owner,
never cached. Trigger: a writer outside the normalizer or a cached
ceiling.

R8 — Dependency direction / hidden cycles. Rejected: nothing under
`types/` or in the `orders` import closure (`orders/*`, `sets_mixins.py`,
the `utils/*` leaves) imports `list_field`, `connection`, or `relay` at
module top, so the `TYPE_CHECKING` import of
`types/definition.py::DjangoTypeDefinition` and the two function-local
`orders` imports hide no cycle; the deferrals are the codebase's
subsystem-independence idiom. No `django.conf.settings` import exists in
the module; policy is read per request via
`resource_policy.py::policy_from_info`. Trigger: a new top-level import
edge into the flavor layer from below it.

R9 — Upstream seam range (`Info.get_argument_definition`,
`GraphQLCoreConverter.DEFINITION_BACKREF`, `Info._raw_info`). Rejected:
both attributes exist at the floor (strawberry 0.316.0, scratch-venv
grep) and at the installed 0.324.0 with the same key literal, and the
`getattr(info, "get_argument_definition", None)` read fails soft to the
spec-sanctioned fallback where absent. The `DEFINITION_BACKREF` read sits
behind that same presence check, so a version lacking both degrades to
the fallback instead of raising. Trigger: a supported strawberry lacking
either attribute, or a renamed backref key.

R10 — `__all__` vs public surface. Rejected: `__all__` names exactly the
two public symbols (`DjangoListField`, `ListArgumentError`); every other
module-level name is underscore-private; both are root-exported and
pinned by `tests/base/test_init.py`. Trigger: a new public name or a
root-export drift.

R11 — Duplication: offset/limit validation arms. Rejected under DRY's
change challenge: the arms differ in ceiling rule (offset is
policy-only regardless of trusted widening; limit is the effective bound
— two spec-050 rules, not one), and the shared wording already lives
once in `ListArgumentError.__init__`. A change to one ceiling must not
move the other. Trigger: the two ceilings unify, or a third numeric
argument joins the surface.

R12 — Duplication: sync/async queryset pipelines. Rejected (twins, no
drift): `_execute_queryset_pipeline_sync` and
`_execute_queryset_pipeline_async` agree stage for stage (fast path
without policy, visibility with `_LIST_ARGUMENT_VISIBILITY_POLICY`,
shared normalization scope, shared `_check_nonzero_offset_guard`,
windowed tail); the only differences are color (await points) and the
sync twin's `is_async_context` wrap, which matches the async twin's
unconditional wrap. The args-path-only combinator policy is sanctioned
by the `_SealPolicy` comment. Trigger: any stage, policy, or guard order
changing on one twin only.

R13 — Duplication: `strawberry-definition` spelled three ways (attribute
in `list_field.py`, named literal in `extensions/resource_policy.py`,
inline literal in `schema.py`). Rejected: three entries (argument-identity
vs field-marker reads), two failure postures (fail-loud `ConfigurationError`
vs tolerant `.get`), and the target holds the self-tracking spelling, not
a copy — there is no in-fence consolidation, and the DRY flow already
inventoried these readers and left them file-local. Trigger: a renamed
key (R9) or a fourth reader.

R14 — Duplication: `_synthesized_list_signature` vs
`connection.py::_synthesized_signature`; `_field_label` vs
`types/converters.py::_field_label`; `_validate_mutation_target`.
Rejected: the signature builders are a spec-050-sanctioned parallel with
different parameters and return-annotation ownership; the two
`_field_label`s answer different questions (resolver label from `info`
vs model-field diagnostic label); the mutation validator guards a
different family (mutation protocol, duck-typed per spec-038) and already
reads truthfully. Trigger: a shared parameter shape or a shared target
family.

R15 — Twin drift: sync/async `_wrap` + predicate choice
(`operation_is_async` vs `async_execution`). Rejected: the structural
asymmetry is reasoned — the sync wrapper diverts async-only iterables to
a coroutine return because Strawberry froze its handling, while the async
wrapper consumes them natively; `prepared_resolver_source` runs on both
with the correctly colored guard (`reject_residual_async_source` after
the await vs `reject_awaitable_sync_source` before it). The executor
predicate keys the misuse guard (nothing can await under `execute_sync`,
loop or not); the ambient predicate keys the wrap/dispatch decision (a
running loop means graphql-core completes the value asynchronously).
Each question gets its own correct answer. Trigger: a flavor returning a
value its executor cannot complete.

R16 — Guard parity across flavors (default vs consumer resolvers; list vs
connection). Rejected: the default resolver correctly bypasses
`prepared_resolver_source` (its source is the known-queryset
`base_queryset` seed); every consumer path runs it. Non-queryset
rejections are equivalent per color (sync raise vs async close-plus-raise;
 sync sources need no close). The connection's pre-sliced/sidecar guards
have no list twin because the shared visibility seal already answers
pre-sliced sources with `ConfigurationError` (spec-050) and sidecars are
a connection-only surface. Trigger: a consumer shape reaching iteration
without its visibility seal, or a list input silently accepted where the
spec demands a rejection.

R17 — Classifier input dispatch (containers by `isinstance`, Q children
by unpack, `annotation.output_field`). Rejected: each mirrors the
compiler frame it shadows. Django's `Query.build_filter` unpacks
`(arg, value)` pairs itself, so a malformed Q child raises `ValueError`
in either frame with the identical masked wire verdict; stored
annotations are resolved at `add_annotation` time, so `output_field` is
set before the guard ever runs; iterating value containers is inherent
to the rule (a nested `Random()` must refuse) and a hostile member
breaks Django's own compilation the same way. Ordering structure is
developer-written query AST, not a client-reachable trust boundary.
Trigger: a client/wire input placing hostile structure into a classified
ordering.

Handoff: Mechanics review closed `no-findings` with zero defects, zero
routed leads, and seventeen rejections each carrying its reopen trigger.
Beyond the record's trace: the `__reduce__` shape comparison against
`ResourceLimitExceeded`, the `QuerySet.reverse` / `add_annotation` /
`build_filter` reads in installed Django 6.1, the floor-strawberry 0.316.0
attribute grep in a scratch venv, and the DRY-file orientation greps
(which informed only the R13 trigger wording — every verdict above is
derived from first-party source, specs, glossary, and tests). Sibling
axis records were absent when read (concurrent dispatch); the plan's
routed Comments line on `_validate_djangotype_target`'s docstring was
left untouched for the Comments pass. Open threads: none. No workspace
copy was opened and no cell-gated proof was owed; if a sibling or the
verifier wants a live corroboration of any rejection, the natural nodes
live in `tests/test_list_field.py` plus the live
`test_list_field_api.py` / `test_list_field_async_api.py` suites.

## Verification (Mechanics)

Pass 1. Implement landed prose-only hunks for 6 Mediums + 1 riding Low
(Comments axis) in 2 files; 3 Lows deferred per the ride rule; Performance
and Mechanics had no findings, so this axis verifies a change it did not
ask for.

Step 1 — item diff freshness: `git diff
8d5cb7ac968f96f5123ad24c3eb2e72c7249b897 --
django_strawberry_framework/list_field.py
examples/fakeshop/test_query/test_library_api.py` is byte-identical to
`docs/review/temp-tests/list_field/diff/pass-1.diff` (`cmp` IDENTICAL,
sha256 `e2855a5e71b34f320a52ca37c38f857678573c5071bdcada3f96d37451ed98bf`
both sides, 5514 bytes). The tree did not move under the pass.

Proofs — none exist on this axis, so none ran. This record carries no
Proof line (its only `Proof` mention states no cell-gated Proof exists),
and no `## Cross-axis (for Mechanics)` section exists in any of the three
axis records — the only `cross-axis` hits are Comments-record prose
confirming both siblings have none. No workspace run was owed or taken;
no run ids.

Behavior preservation — code-digest identity, both exit 0 with equal
digests reproducing Worker-2's claimed values exactly:

- `review_inspect.py --code-digest
  8d5cb7ac968f96f5123ad24c3eb2e72c7249b897:django_strawberry_framework/list_field.py
  django_strawberry_framework/list_field.py` → both
  `sha256:95fb1b0d9d05ce013be06fbfbbf712a09a8cc52642e8ba878b5d83e7b014fc68`.
- Same form for `examples/fakeshop/test_query/test_library_api.py` → both
  `sha256:43b8fbed999ed6705137d3b1531bccdf360a756f91dc78858333ccec9a99dc1a`.

A revert proof is vacuous: no production hunk exists — added-line and
removed-line scans of pass-1.diff for `def` / `class` / `import` /
`from` / `__all__` / decorator tokens both come back empty — so there is
no behavior to pin with `prove` and no test the change relies on. No
symbol was moved or renamed, so no `--cited-by` sweep is owed; no module
first line changed, so no TREE.md render is owed. Test tier: nothing
added or behaviorally changed (the test-file hunks are docstring-only per
the digest above).

Diff read through the axis — 7 prose hunks, all docstring or comment
(M1 docstring, M3 `#:` comment, L1 docstring, M4 docstring, M2 `#`
comment on the target; M5, M6 docstrings on the live test file). No
placement, dependency, state-ownership, or duplication question arises
from prose; grading the prose's truth belongs to the Comments verifier.

Attacks on the current state (Mechanics lens: the landed prose must not
assert a contract the bodies contradict):

- M1 sharing claim: `relay.py` imports
  `_validate_relay_djangotype_target` (line 65), `_validate_node_target`
  wraps it (line 343) backing `DjangoNodeField` / `DjangoNodesField`
  (lines 462, 550), and the relay validator delegates its base checks to
  `_validate_djangotype_target` (list_field.py line 224). The three-live-
  sharers sentence introduces no contract-vs-body defect.
- M4 contrast: the only executable `.distinct(` in the package is
  `filters/base.py:138` (a consumer-filter effect, not a connection
  injection; the other two hits are a comment and a docstring); the pk
  terminal tiebreaker is connection-side prose; inside `list_field.py`
  the only `distinct|tiebreaker` hits are the landed sentence itself.
  Both halves hold; no new defect.
- M5 live entry: `prepared_resolver_source` is called in both `_wrap`
  colorings (list_field.py lines 1660 async, 1707 sync). True.
- R-trigger sweep: R10 `__all__` intact (line 107, both names, unchanged);
  every code-dependent trigger in R1-R17 cannot fire under digest
  identity. No trigger fires.
- Item fence: the unfiltered ITEM stat names 4 files; the 2 beyond the
  item's paths (`docs/dry/dry-0_0_15.md`, `docs/review/review-0_0_15.md`)
  are Worker-0/other-flow bookkeeping, matching Worker-2's attribution.
  The 3 deferred-Low files (`tests/test_list_field.py`,
  `tests/base/test_init.py`,
  `examples/fakeshop/test_query/test_list_field_api.py`) diff 0 bytes vs
  ITEM_BASELINE — the ride rule was applied correctly, and no Low rides
  unexamined.

Disputes — none recorded. The artifact's only `disputed` hit is the
Handoff's "Nothing disputed"; no `disputed: <reason>` row exists to
judge.

Lint gates (`--check` forms only), all green:

- `uv run ruff check` on the two touched paths: All checks passed,
  exit 0.
- `uv run ruff format --check` on the two touched paths: 2 files already
  formatted, exit 0.
- `uv run python scripts/check_trailing_commas.py --check` on the two
  touched paths: 2 files, 0 violations, exit 0.
- `uv run python scripts/check_citations.py --check` tree-wide: 1299
  citations resolve, exit 0.

Cells: sharded and pg inapplicable by construction (prose-only diff; no
database-reaching probe). Cells unverified: none.

No new finding on this axis. Live fingerprints (`git hash-object`):
`django_strawberry_framework/list_field.py`
`6a1dba1af04428d4fc67864c2beb1af755fc387c`,
`examples/fakeshop/test_query/test_library_api.py`
`4acc4821d8adb23b2de8a743d351f94567932c14` — both equal Worker-2's
after-values; axis records unchanged since the implement read
(`1a72beb1`, `122571cb`, `a3ccbf82`). Scratch:
`docs/review/temp-tests/list_field/verify-mechanics-1/` (created; holds
no probe — nothing executable was owed).

Handoff: Mechanics verify pass 1 closes `verified`. Beyond the checks
above: the whole live target (1751 lines) was re-read; the M2/M3/M6
landed wordings were left entirely to the Comments verifier (no
Mechanics content — a spec-Decision pointer, an admission-scope comment,
a dropped phantom pin); the M4 `no/and` judgment call reads true on both
halves from the bodies cited. Open threads: none. Deferred L2/L3/L4 stay
visible for `## Outcomes` per the implement Handoff; nothing on this
axis reopens them.
