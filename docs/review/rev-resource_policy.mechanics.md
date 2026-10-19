# Review · Mechanics: `django_strawberry_framework/resource_policy.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e3af18216bc75ecbd6bd080d78cdb1b209458e79

## Trace

Required reading in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run
0.0.15 2026-09-28-3, incl. its `## Owned changes`, which holds
no row for this target), `docs/review/rev-resource_policy.md`
(skeleton). Sibling axis records
`docs/review/rev-resource_policy.performance.md`,
`docs/review/rev-resource_policy.mechanics.md` (this record) and
`docs/review/rev-resource_policy.comments.md` did not exist when
read (siblings run concurrently; listing showed only the
skeleton); no Handoff or Cross-axis section exists to absorb
yet. The plan item carries one Routed lead (from conf.py
Comments, observed, not graded: "Probed by the hunt" wording in
`tests/test_resource_policy.py`); judged below, out of axis,
routed onward.

Target read whole (1371 lines) at blob `cc3f9d80` (live, dirty).
`ITEM_BASELINE` blob for the target equals the live blob (the
item baseline captured the dirty tree); HEAD blob is
`4b69e974`. HEAD..live is the concurrent truth-migration plus a
cleanup-seam simplification: `describe_value` to
`truth.describe` (4 sites), `self.__class__` to `type(self)` in
`__reduce__`, `isinstance` to `truth.is_instance` in
`_deadline_expired`, `_attach_cleanup_note` rebuilt on
`truth.static_attr` / `truth.is_exact`, and
`_is_cleanup_diagnostic` deleted with its two
`except BaseException` call sites narrowed to
`except Exception`. `narrowed` (the one finding's site) is
identical at HEAD, `ITEM_BASELINE`, and live. Reviewed live as
dispatched.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/resource_policy/mechanics/inspect/`
(json
`docs/review/temp-tests/resource_policy/mechanics/resource_policy.json`):
18 imports, 44 symbols, 6 control-flow hotspots, 8 hot entry
points (+9 reachable), 3 import-time calls. Leads only.

Edges verified by read:

- `django_strawberry_framework/resource_policy.py::resolve_resource_policy` —
  called at construction by `schema.py::DjangoSchema` (line 859)
  and in tests; delegates to
  `utils/policies.py::resolve_policy` with the
  `resource_policy.py::_PACKAGE_RESOURCE_POLICY` default and the
  `conf.py::resource_policy_setting` reader. Twin
  `error_policy.py::resolve_error_policy` shares the helper with
  `unit="option"`; instance/mapping/absent arms verified same
  shape.
- `django_strawberry_framework/resource_policy.py::begin_resource_budget` /
  `end_resource_budget` — armed once per operation by
  `extensions/resource_policy.py::DjangoResourcePolicyExtension.on_operation`
  (line 1504), disarmed in its `finally`; the scope triple
  crosses to the runner via `budget_resume_binding` /
  `adopt_budget_binding` (lines 1507-1508). `end_resource_budget`
  foreign-token arm pinned by
  `tests/test_resource_policy.py::test_disarming_with_a_token_from_another_variable_is_not_swallowed`.
- `django_strawberry_framework/resource_policy.py::armed_resource_policy` —
  package-internal read (not in `__all__`); called by the
  extension's scan and admission paths (lines 1512, 1564) and in
  tests. Never handed to consumer code.
- `django_strawberry_framework/resource_policy.py::record_admission_rejection` /
  `admission_rejection` — verdict write/read; called by the
  extension (lines 1574, 1350, 1609) and in tests. Not in
  `__all__`.
- `django_strawberry_framework/resource_policy.py::policy_from_info` —
  called by `_raw_list_bound`,
  `list_field.py::_normalize_list_arguments` (line 447),
  `utils/connections.py::resolve_relay_max_results` (line 758),
  `check_deadline` (unarmed arm), and in tests. Always copies
  out (`copy_policy`); mirror admits the exact class only.
- `django_strawberry_framework/resource_policy.py::check_deadline` —
  called at the pre-query seam by `_raw_list_bound`,
  `connection.py` (line 1356), `relay.py` (lines 593, 677),
  `types/resolvers.py` (5 sites), `mutations/resolvers.py`
  (line 204).
- `django_strawberry_framework/resource_policy.py::bounded_rows` /
  `bounded_rows_async` — called by `list_field.py` resolvers and
  `types/resolvers.py` (line 57 import); both delegate to the
  package-private `_windowed_rows` / `_windowed_rows_async`,
  which `list_field.py` also calls directly with validated
  coordinates (lines 1382-1732), as spec-047 prescribes.
- `django_strawberry_framework/resource_policy.py::effective_bound` —
  called by `_raw_list_bound` (with `trusted` from the field),
  `utils/connections.py::resolve_relay_max_results` (ceiling,
  never trusted), and
  `list_field.py::_normalize_list_arguments` (line 475, client
  `limit` ceiling).
- `django_strawberry_framework/resource_policy.py::validate_collection_bound` /
  `validate_trusted_flag` — production callers are the
  `DjangoListField` factory lines only (`list_field.py:1541-1542`).
- `django_strawberry_framework/resource_policy.py::stash_resource_policy` /
  `clear_resource_context` — no production callers; consumer
  surface for publish-without-arming (plain-schema callers)
  plus the reuse-guard clear. Heavily oracle-pinned.
- `django_strawberry_framework/resource_policy.py::_PACKAGE_RESOURCE_POLICY` —
  read by `schema.py::_FALLBACK_ENFORCEMENT` (line 568) and the
  extension's `_resolved_policy` fallback (line 1470). Every
  path that answers with it copies first: the schema property
  via `copy_policy` (line 982), the extension via
  `begin_resource_budget` / `_operation_policy` /
  `canonical_policy`. Verified no uncopied escape: the only
  `.resource_policy` reads on the enforcement record are the
  copy-per-read property and the extension's resolve-then-arm
  path.
- `django_strawberry_framework/resource_policy.py::ResourcePolicy.narrowed` —
  no production callers; the per-request tightening primitive
  pinned at package tier (6 nodes named in L1's Proof).

Contract sources: `docs/README.md` (enforcement-configured,
error-envelope, refuse-before-parse rows);
`docs/GLOSSARY.md` (`ResourcePolicy`, `DjangoResourcePolicyExtension`,
execution-resource-policy, `ErrorPolicy`, row-bound,
value-budget-walker anchors); the owner docstrings;
`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`
(the package-private window delegation, row 63a132be);
`tests/test_resource_policy.py` (spans read for every behavior
cited); `django_strawberry_framework/utils/policies.py` read
whole (`resolve_policy` / `canonical_policy` / `copy_policy`
ladder); `django_strawberry_framework/utils/truth.py`
(`is_instance` / `is_exact` / `static_attr` / `describe`)
spans.

Instruments: the trace above; no workspace runs (every behavior
read is oracle-pinned and every rejection rests on a read, not a
measurement; no probe is owed). Cells: sharded and pg are
`inapplicable by construction` for L1's Proof (pure-dataclass
narrowing logic over six package-tier nodes; no queryset,
alias, or dialect decision). The target's queryset-slicing
paths carry no finding.

Looks-for discharge (Mechanics floor):

- Rule enforced at a caller instead of its owner: none. The
  coordinate check lives at its documented owner
  (`list_field.py::_normalize_list_arguments`; the
  `_windowed_rows` docstring names it); the bound-domain rule
  lives once in `_require_positive_int` behind both spellings
  (`__post_init__`, `validate_collection_bound`); the trusted
  opt-in is checked at the factory line AND at the primitive
  (`effective_bound`'s `is True`), the documented defense in
  depth; mirror admission (exact class only) lives at
  `policy_from_info`, the one seam a foreign object reaches.
- Policy in an adapter, mechanism in a policy layer: none. The
  async-cleanup trio (`_attach_cleanup_note`,
  `_close_async_iterator`, `_cleanup_rejected_async_iterable`)
  is the mechanism the async window owns; the note helper has
  no twin elsewhere (sole `__notes__` writer in the package)
  and two file-local call sites.
- Decision vs contract sources: all match. Bool rejected as a
  bound, upper cap at `MAX_RESOURCE_BOUND`, `narrowed` naming
  both values, exact-bool trusted opt-in, offset-vs-limit
  ceiling asymmetry, copy-per-read schema attribute,
  instance-behind-setting ladder — each verified against the
  README / GLOSSARY / rationale row that states it. No
  correctness defect found: no HUNT fields owed.
- Branch no real path reaches: L1 (the `narrowed` int-arm
  `None` conjuncts). Every other arm carries an oracle: the
  foreign-token `ValueError` re-raise, the `OverflowError`
  deadline arms, the hand-written-deadline `configured is None`
  arm, the zero-width windows, the no-budget verdict no-op,
  the `aclose`-absent arm, the `aiter`-failure arm.
- Mode flag standing in for a named adapter: none. `trusted`
  is a two-way opt-in with one widening value, not N-way
  dispatch.
- State owned in two places: none beyond the three deliberate
  authority/mirror pairs (ContextVar budget vs `DST_*` mirror;
  recorded verdict vs published pre-execution errors; armed
  deadline vs stashed mirror), each with stated ownership and
  a narrowing-only seam between the halves.
- Dependency pointing the wrong way: none. All seven package
  imports point down (`conf`, `exceptions`, six `utils`
  leaves); no `TYPE_CHECKING`; no settings read at import
  (the reader is called at resolve time). The upward
  cross-module reads of this module's privates
  (`_PACKAGE_RESOURCE_POLICY`, `_operation_policy` by schema
  and the extension; `_windowed_rows*`,
  `_cleanup_rejected_async_iterable` by the list field) are
  the spec-047 shape, not a layer inversion.
- `django.conf.settings` read at import: none. Import-time
  work is `ResourcePolicy()`, `canonical_policy(...)`, and
  the `ContextVar` construction; no settings, no database.
- `__all__` disagreeing with the public surface: none. The
  five public-but-unlisted names (`armed_resource_policy`,
  `budget_resume_binding`, `adopt_budget_binding`,
  `record_admission_rejection`, `admission_rejection`) are
  extension-internal seams (the `relay.py::__all__`
  precedent: consumer fields listed, package-internal
  `decode_model_global_id` et al. importable but unlisted),
  used only by the extension plus tests, named in no
  README / GLOSSARY row. Root `__all__` carries exactly the
  four documented names.
- Two sites implementing one rule: R1, R2 (DRY challenges;
  separate domains, separate reasons to change); the
  extension-local exact-int pair is routed to that item (see
  Handoff: it sits outside this item's fence).
- Sync/async twins that drifted: none. Both colors derive
  from `_raw_list_bound`; the async-only arm mirrors the
  sync counting branch (skip `start`, collect `window`,
  `[]` on zero width); `None` and sync iterables delegate
  to `_windowed_rows` unchanged; the rejection-path cleanup
  has no sync twin because the sync path acquires nothing.
- Guard one flavor has and a sibling lacks: R3 (connection
  ceiling vs list-field trusted widening is the contract,
  not a gap), R4 (`__reduce__` spelling twin is behaviorally
  identical).

Fingerprints (`git hash-object`, live tree):

`django_strawberry_framework/resource_policy.py`
`cc3f9d80b9d55af8b725a77c73aba3d8110e0037`;
`tests/test_resource_policy.py`
`585c536e65aba030c920d86dfaf95dbabe95807e`;
`django_strawberry_framework/utils/policies.py`
`0a2b7dbad96594b5d668774218809c6a94d136be`;
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9`;
`django_strawberry_framework/extensions/resource_policy.py`
`0134d83a9aa2db580b7b8180ded27a3d31b115c7`
(arming flow, `_charge_upload`, `_page_bound` spans);
`django_strawberry_framework/schema.py`
`84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1`
(enforcement-record spans);
`django_strawberry_framework/list_field.py`
`f5b0183e290322952fd2dad1f76ab9b2de9736ba`
(imports, `_normalize_list_arguments`, factory, window
call-site spans);
`django_strawberry_framework/utils/connections.py`
`efcf749a26dc7d3fa9b3cc142789a11de2647070`
(`resolve_relay_max_results` span);
`django_strawberry_framework/error_policy.py`
`57a0bed1ba730f8e4c1f4c879d852274eac39f12`
(`__all__`, resolver spans);
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`
(imports, `__all__` spans);
`django_strawberry_framework/connection.py`
`1fca6266cd5f748915875badf1881680b599de37`
(`max_results` spans);
`django_strawberry_framework/relay.py`
`f5760b45f161cccf9dce6d2c84b45311b5b03291`
(`__all__`, `check_deadline` spans);
`django_strawberry_framework/types/resolvers.py`
`640905c63f465db4de16c3a07492b27f3d12d3ad`
(import, `check_deadline` spans);
`django_strawberry_framework/mutations/resolvers.py`
`c9cff0590157de85bd9374ab85588b00e62080e0`
(`check_deadline` span);
`django_strawberry_framework/conf.py`
`3820c575bfd4e3c384244d1bed460b75d3bb7681`
(setting-reader spans);
`tests/test_list_field.py`
`d78aa5e79fee14b37564f856d3d4bc74e7d9630b`
(pickle-twin span);
`tests/extensions/test_operation_state.py`
`7509c1ccaa1c56c50be2ca3bc4337b75bcca90ce`
(import span);
`docs/README.md`
`30978c34f63a833ffcc0fa11c80b773d241921be`;
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`;
`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`
`7f321ce6c677f4fb580cc028d19f11d085aa1e6b`
(package-private-window row).

## Findings

### High

None.

### Medium

None.

### Low

#### L1: dead `None` conjuncts in the `narrowed` int arm

- Observation:
  `django_strawberry_framework/resource_policy.py::ResourcePolicy.narrowed`
  decides the non-deadline widen check as `value is not None and
  current is not None and value > current`
  (`resource_policy.py:427`), but neither operand can be `None`:
  the candidate was just rebuilt by `replace`, whose
  `__post_init__` rejects any non-positive-int field (including
  `None`) with `ConfigurationError`, and `self` was validated at
  its own construction ("an invalid policy cannot exist"). The
  two conjuncts are always true, so the line reads as guarding a
  case the invariant excludes. The deadline arm above it needs
  its `None` checks; this arm echoes their shape for no live
  input.
- Evidence: the trace above;
  `tests/test_resource_policy.py::test_narrowing_validates_override_domains_before_comparing_them`
  pins that `replace` validates before any comparison runs, and
  `tests/test_resource_policy.py::test_a_hostile_int_subclass_narrowing_a_bound_is_typed_rejected`
  pins that the comparison runs on exact built-in values. Even a
  `__dict__`-corrupted `None` (the module's own frozen-bypass
  vector) fails closed at `replace` before the widen check, so
  the conjuncts guard nothing there either.
- Impact: reader time and a standing invitation to misread the
  invariant: a maintainer must re-derive that the `None` case is
  impossible on every visit, and a future edit could lean on the
  conjuncts as though they admitted one. No behavior changes.
- Severity: Low — bounded clarity improvement on a cold path;
  factor: dead sub-expression, zero behavioral delta.
- Recommendation: simplify the arm to `widens = value >
  current` at the owner, `resource_policy.py::ResourcePolicy.narrowed`
  (the check lives and stays there; no move). Contract source:
  the `__post_init__` docstring ("an invalid policy cannot
  exist") plus the `narrowed` docstring's narrowing contract.
- Must not change: `narrowed` accept/reject behavior and
  messages on every input, including the deadline arms and the
  unknown-name refusal.
- Proof: `grep -n "widens = value" django_strawberry_framework/resource_policy.py`
  prints the single-operand line `widens = value > current`
  (prints the three-operand line now; static, shared tree);
  and
  `uv run python scripts/workspace.py run review/resource_policy.py/verify-mechanics-<n> -- pytest tests/test_resource_policy.py::test_narrowing_a_bound_returns_a_tighter_policy tests/test_resource_policy.py::test_widening_a_bound_is_refused tests/test_resource_policy.py::test_narrowing_an_unknown_bound_is_refused tests/test_resource_policy.py::test_a_deadline_narrows_from_absent_to_present_but_never_back tests/test_resource_policy.py::test_narrowing_validates_override_domains_before_comparing_them tests/test_resource_policy.py::test_a_hostile_int_subclass_narrowing_a_bound_is_typed_rejected --no-cov`
  reports `6 passed`. Self-contained; `<n>` is the verify pass
  number.
- Freshness: Trace fingerprints cover every file; no additional
  file.

## Rejected

### R1: the exact-type-test family is not one rule

DRY change challenge. Posit "change what counts as a usable
number": the sites are
`resource_policy.py::_is_builtin_number` (exact int-or-float, the
deadline domain), `resource_policy.py::_require_positive_int`
(exact int, 1..`MAX_RESOURCE_BOUND`, the bound domain),
`extensions/resource_policy.py::_charge_upload` (exact int,
non-negative, unmeasurable-size rejection),
`extensions/resource_policy.py::_page_bound` (exact int,
non-negative, conservative fallback),
`list_field.py::_normalize_list_arguments` (exact int per
coordinate, `ListArgumentError` contract),
`resource_policy.py::policy_from_info` (exact `ResourcePolicy`),
and `resource_policy.py::_bounds_by_its_own_slice` (exact
sequence-type membership). Count > 1, but the contracts differ
(float admitted for deadlines, rejected for sizes; each site
pairs its test with its own range check and its own rejection),
so they have separate reasons to change — notably, calling
`_is_builtin_number` where a float must be rejected would widen
the domain, which is why each domain states its test inline.
Similar-looking code with separate reasons to change stays
separate. Trigger: a change to the threat model for numeric
subclasses itself (then all sites re-audit together), or a new
consumer-number seam with no domain of its own to state.

### R2: the three narrowings are three rules, one direction

`ResourcePolicy.narrowed` (override vs policy),
`resource_policy.py::_effective_deadline` (stashed mirror vs
armed deadline), and `resource_policy.py::effective_bound`
(declared field value vs policy value) all narrow, but over
different inputs with different `None` semantics (override-None
on the deadline is the widest move; mirror-None is absence;
declared-None is "the policy governs"). Consolidating them
would merge three call-site contracts into one branching
primitive. Trigger: a fourth narrowing seam, or two of the
three inputs unifying.

### R3: connection `max_results` has no trusted-widening twin — by contract

`list_field.py` validates `max_rows` /
`trusted_max_rows` at its factory line and widens past the
policy on the literal `True`; the connection path resolves
`max_results` through
`utils/connections.py::resolve_relay_max_results` into
`effective_bound(policy.max_page_size, cap)` with no trusted
spelling — the policy is always a ceiling (spec-047 Decision
7, GLOSSARY `max_page_size` row). No contract source promises
constructor-site validation or trusted widening for
connections, so the asymmetry is not a missing guard.
Trigger: a contract naming connection-cap construction
validation or a trusted page widening.

### R4: `__reduce__` twin spells state as `self.__dict__`, siblings as `vars(self)`

`resource_policy.py::ResourceLimitExceeded.__reduce__` passes
`self.__dict__` where the three twin methods
(`exceptions.py::PathResolutionError.__reduce__`,
`exceptions.py::LookupValidationError.__reduce__`,
`list_field.py::ListArgumentError.__reduce__`) pass
`vars(self)`. Behaviorally identical on these dict-carrying
classes (same object, no consumer code runs either way), and
the GLOSSARY contract is "same pickle-safe `__reduce__`
shape", which holds (class plus complete constructor args
plus instance state, pinned by
`tests/test_resource_policy.py::test_resource_limit_exceeded_pickle_and_copy_fidelity`).
Normalizing the spelling would be style, not a finding; sharing
an implementation would trade four explicit methods for
indirection. Trigger: a behavioral divergence between the
spellings, or a fifth error joining the shape with a different
state need.

### R5: `stash_resource_policy` / `clear_resource_context` have no production callers

Both are consumer surface, not dead code:
`stash_resource_policy` is the publish-without-arming entry for
callers outside any budget (a direct stash, a plain
`strawberry.Schema` with no extension), and
`clear_resource_context` is the `context_value`-reuse guard;
both are in `__all__` and pinned by dozens of oracle rows.
Trigger: removal of the plain-schema path they serve, or a
release that stops exporting them.

### R6: budget-scope helpers take `scope: Any`

`budget_resume_binding`, `adopt_budget_binding`,
`begin_resource_budget`'s return, and `end_resource_budget`
type the scope as `Any` though `_BudgetScope` is defined in
this module. No contract is broken (the extension passes the
object through opaquely; misuse fails loud on attribute
access), and tightening the annotation is a typing judgment,
not a Mechanics looks-for entry. Trigger: a consumer-facing
typing contract for the scope object.

Handoff: read beyond the record's trace: the extension's
`_resolved_policy` fallback hands `_PACKAGE_RESOURCE_POLICY`
itself to `begin_resource_budget`, which is safe only because
arming canonicalizes (verified, not a finding); the sole
`_FALLBACK_ENFORCEMENT.resource_policy` readers copy first
(verified, not a finding); `test_list_field_api.py:2926`
monkeypatches `list_field_module._windowed_rows`, confirming
the package-private window is the seam tests observe. The
plan's Routed lead (conf.py Comments, observed, not graded)
is the "(Probed by the hunt: ...)" parenthetical in
`tests/test_resource_policy.py::test_an_instance_through_the_setting_slot_resolves_on_the_same_terms`
(`test_resource_policy.py:340-341`): process provenance in
test prose, out of Mechanics scope — the pinned behavior
(instance-behind-setting ladder) is mechanically sound and
owned by `utils/policies.py::resolve_policy`. Route onward to
the Comments pass. New lead for the
`extensions/resource_policy.py` Mechanics pass (same axis,
other item, out of this item's fence):
`extensions/resource_policy.py::_charge_upload`
(`type(size) is not int or size < 0`) and
`extensions/resource_policy.py::_page_bound`
(`type(value) is int and value >= 0`) both spell exact-int
plus non-negative inline with prose citations to
`resource_policy.py::_is_builtin_number`; whether that
fragment is one rule with one owner inside that module is for
that item to judge — no evidence taken here beyond noting the
pair. Open threads: none on this axis; L1 is the whole
change surface, and it rides only if Worker-2 is already in
the file for a higher finding (Low rule), else deferred.

## Verify mechanics

Precondition: the live tree carries exactly the change under
grade. `git diff e3af18216bc75ecbd6bd080d78cdb1b209458e79 --
<the three item paths>` hashes `d5ef0679`, identical to
`docs/review/temp-tests/resource_policy/diff/pass-1.diff`
(`git hash-object` both `d5ef0679`). Live fingerprints
`resource_policy.py` 5b4a80f0, `tests/test_resource_policy.py`
a52bfb89, `test_resource_policy_api.py` 56b70d75 are the
pass-diff end states. All runs below at
`review/resource_policy.py/verify-mechanics-1` (slot-3,
package digest `sha256:336177e5f3a6244f24d84b18dd83b27467d21f61077572e3b7c8c6a39675b2b4`
on the changed code, copy `fresh` except the one noted
copy-mutating run).

### L1 Proof, static half - pass

Shared-tree `grep -n "widens = value"
django_strawberry_framework/resource_policy.py` prints line
426 `widens = value is None and current is not None` (the
deadline arm, intact) and line 429 `widens = value >
current` (the single-operand arm, landed). The
three-operand int arm is gone; the deadline arm above it is
byte-identical context in the diff.

### L1 Proof, six pins - pass

`review-20260929T101821-027a7b` (fresh, default cell):
the record's six nodes verbatim —
`test_narrowing_a_bound_returns_a_tighter_policy`,
`test_widening_a_bound_is_refused`,
`test_narrowing_an_unknown_bound_is_refused`,
`test_a_deadline_narrows_from_absent_to_present_but_never_back`,
`test_narrowing_validates_override_domains_before_comparing_them`,
`test_a_hostile_int_subclass_narrowing_a_bound_is_typed_rejected`
— report `6 passed`.

### Narrowed accept/reject + messages identical on every input - pass

Attack probe `verify-mechanics-1/probe_matrix.py` (30
narrowed cases: tighten / widen / equal / floor / unknown /
unknown-plus-valid / zero / negative / bool / float / str /
None / int-subclass / mixed tighten+widen / no-op /
second-field tighten+widen; deadline None->value,
None->None, None->0, None->True, 30->10, 30->60, 30->30,
30->None, 30->0, 30->float-subclass; `__dict__`-tampered
self with None / True / str): new-code leg
`review-20260929T102046-b77701` vs both-production-hunks-reverted
leg `review-20260929T102127-283332` (copy `modified: 1`,
digest `sha256:3f1e56cc...`, reverted by `patch -R` of
`verify-mechanics-1/revert-code-hunks.diff` inside the copy
only) — all 30 narrowed lines byte-identical, messages
included. The tampered-self cases fail closed with
`ConfigurationError` from `replace` on both legs (never
`TypeError`), confirming the record's invariant that the
dropped conjuncts guarded no live input. Deadline arms and
the unknown-name refusal are textually untouched context in
the diff and behaviorally pinned by d01-d10, n05-n06.

### F1's guard introduces no Mechanics defect - pass

The same A/B pair carries the 21-row `_deadline_expired`
truth table (None, True/False, 0, 1, -5, 2**100, 1.5, NaN,
+-Inf, str, bytes, object, tuple, int/float subclasses, far
future/past monotonic float and int): 21/21 byte-identical
across the guard's removal, so the Performance record's
Must-not-change table holds exactly. The guard's only
consumer is `check_deadline:942` (sole non-docstring caller
in the package). The F1 pin set (7 nodes, 9 rows) passes on
the changed code: `9 passed` baseline inside
`review-20260929T102259-aef19e`.

### Rejections R1-R6 stand - pass

Whole-diff read: the only code hunks are the L1 arm and the
F1 guard; every R-site symbol is absent from the diff except
`_is_builtin_number(deadline)` as unchanged context. R1 (the
guard preserves the exact-type ladder's `None` answer, shown
by e01); R2 (`_effective_deadline`, `effective_bound`
untouched); R3-R6 (connection ceiling, `__reduce__`,
stash/clear, scope `Any`: no hunk, no new caller, no
contract change). No finding's trigger tripped.

### Own module green - pass

`review-20260929T102210-826adb` (`--fresh`, restoring the
copy after the revert run): `tests/test_resource_policy.py`
`283 passed`.

### Failability, both hunks behavior-preserving - pass

`workspace.py prove` `review-20260929T102259-aef19e`,
manifest `verify-mechanics-1/prove-behavior-preservation.json`:
entry 1 (L1 arm reverted) `behaviour preserved: no row
failed, as expect_failing: [] declares` (baseline `6
passed`); entry 2 (F1 guard deleted) `behaviour preserved`
(baseline `9 passed`). Restores byte-proved (blob 5b4a80f0
before == after). `--show-capture=no` in both scopes per the
plan's `prove_failability.py` captured-log workaround.

### Lint gates - pass

Shared tree, `--check` forms only, on the three touched
paths: `ruff check` clean, `ruff format --check` (3 files
already formatted), `check_trailing_commas.py --check`
(violations 0); `check_citations.py --check` on the tree
(`1303 citations resolve`).

### Cited-by, tier, disputes, cross-axis

`--cited-by`: nothing owed — L1 moves and renames no symbol.
Test tier: no new test is owed for a behavior-identical
simplification; the pins sit at package tier, the strongest
reachable (`narrowed` has zero package or example
non-test callers — consumer/test-only API, verified by
grep). Disputed: none to judge — the main artifact
`rev-resource_policy.md` still carries no `## Implementation
(Worker-2)` section (observation for Worker-0, not a
Mechanics gap: the diff is complete and matches the plan's
`## Owned changes` rows). Cross-axis: none owed
(Performance: no Cross-axis proofs; Comments `## Cross-axis`:
None).

### Cells

Default cell verified (all runs above). Sharded and pg are
`inapplicable by construction`, judged independently: L1 is
pure-dataclass narrowing over six package-tier nodes and F1
is a truth-table guard whose probe opens no database —
neither hunk reaches a queryset, alias, or dialect decision.

New defects: none. Attacks beyond the Proof (equal-value,
mixed multi-override, hostile domains, tampered self,
deadline downgrade/upgrade/equal/None-both-ways, 21
deadline shapes): all identical, recorded above with run
ids.

Status: verified. Open threads: (1) main artifact
`rev-resource_policy.md` lacks its `## Implementation
(Worker-2)` section — Worker-0 to chase; the diff and
ledger rows are complete so no re-pass is owed.
