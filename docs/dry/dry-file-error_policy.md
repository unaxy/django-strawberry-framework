# DRY review: `django_strawberry_framework/error_policy.py`

Status: verified
Run: 0.0.15 2026-09-18-1 (prior evidence only; run-7 re-trace appended at tail, `Run: 0.0.15 2026-09-29-7`)

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, trigger
re-checked fresh against its difference — never inherited) or a file-local
record with its proving challenge. Zero production edits; zero tracked files
changed.

## System trace

Small target (152 lines, 14 top-level statements): the policy-object half of
the production error policy. It DEFINES the immutable record
(`error_policy.py::ErrorPolicy`, three fields with fail-closed defaults), the
per-field domain gate (`error_policy.py::ErrorPolicy.__post_init__`), the
package default (`error_policy.py::DEFAULT_ERROR_POLICY`), the
construction-time resolution ladder
(`error_policy.py::resolve_error_policy`, delegating to the shared driver),
the correlation-id mint (`error_policy.py::new_correlation_id` with its
per-masked-error contract), and the leaf manifest (`__all__`, four names). It
ENFORCES field validation at construction on every path and the fail-closed
default a deployment gets by doing nothing. It does NOT define the masking
itself — classification, replacement, the DEBUG gate, both application seams,
and every log record live in the sibling enforcement half
(`extensions/error_policy.py`), which this file supplies with values and ids.
The module and class docstrings additionally STATE the sibling's,
`schema.py::DjangoSchema`'s, and `conf.py::error_policy_setting`'s contracts
(structural classification, resolve-once, copy/off-schema authority); those
paragraphs are projections of behavior owned elsewhere, verified against the
owning bodies, not definitions here.

Connected code read for judgment, outside the item:
`django_strawberry_framework/extensions/error_policy.py` (full read — the
enforcement half: `mask_execution_result`, `is_maskable_result`,
`masking_is_active`, `schema_error_policy`, `_masked`, `_degraded`,
`DjangoErrorPolicyExtension`);
`django_strawberry_framework/utils/policies.py` (full read — the shared
`resolve_policy` driver plus `canonical_policy` / `copy_policy`);
`django_strawberry_framework/resource_policy.py` (symmetry sweep: `ResourcePolicy`
shape, `__post_init__`, `DEFAULT_RESOURCE_POLICY`, `resolve_resource_policy`,
`validate_trusted_flag`, `effective_bound`, narrowing contract);
`django_strawberry_framework/conf.py::error_policy_setting` and its
`ERROR_POLICY_KEY` block (full read — thin reader);
`django_strawberry_framework/exceptions.py::describe_value` (full read — the
consumed tail renderer plus its scope paragraph);
`django_strawberry_framework/schema.py` (enforcement record
`_SCHEMA_ENFORCEMENT` / `_FALLBACK_ENFORCEMENT`, `DjangoSchema.__init__`
resolve lines, `DjangoSchema.error_policy` copy property, `_admitted_chain`
prepend position, `_claimed_authority` / `_declared_authority` refusal rows);
`django_strawberry_framework/__init__.py` (root re-export + `logger` home);
`django_strawberry_framework/consumers.py::_stop_aware_results` (full read —
the per-event seam);
`django_strawberry_framework/extensions/debug.py::DjangoDebugExtension.__init__`
(bool-gate lines — the sibling security-bool wording) and its
`_disclosure_permitted` DEBUG read;
`django_strawberry_framework/extensions/__init__.py` and
`extensions/resource_policy.py` (install-recipe lines);
`tests/test_error_policy.py` (full read, 1022 lines — every oracle row);
`examples/fakeshop/test_query/test_error_policy_api.py` (matrix docstring +
wire-shape rows, spot-read bodies);
`tests/base/test_conf.py` (`error_policy_setting` rows, spot-read) and
`tests/base/test_init.py` (export rows, spot-read);
`docs/GLOSSARY.md` (`ErrorPolicy`, production-error-policy,
correlation-identifier entries), `docs/README.md` (policy section),
`SECURITY.md` (masking paragraph), `CHANGELOG.md` (0.0.14 bullet) as
projections.

Swept and excluded on the strength of the bodies (zero production hits for
the `ErrorPolicy`/`error_policy`/`ERROR_POLICY` vocabulary unless named
above): `filters/`, `types/`, `mutations/`, `orders/`, `forms/`,
`rest_framework/`, `optimizer/`, `middleware/`, `auth/`, every other
`utils/` module, `views.py`, `routers.py`, `permissions.py`,
`list_field.py`, `relay.py`, `keyset.py`, `registry.py`, `scalars.py`,
`sets_mixins.py`, `testing/`, `management/`. Spec-048 body cited only as a
pointer (defaults pinned by oracles instead, bodies not relied upon).
Prior artifacts used only as rejected-candidate triggers, each re-checked
fresh below (`dry-file-consumers.md` F3/F4, `dry-file-conf.md` F1/R12/R13,
`dry-file-__init__.md` F1, `dry-file-utils__querysets.md` F3/F7). Never read
another worker's `worker-memory/`. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched and are not in this finding's sites;
concurrent dirt (`connection.py`, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) was never edited, reverted, or tidied.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Every sibling flavor surface was swept
for the policy vocabulary (`ErrorPolicy`, `error_policy`, `ERROR_POLICY`):
`filters/`, `types/`, `mutations/`, `orders/`, `forms/`, `rest_framework/`,
`optimizer/`, `middleware/`, `auth/` return zero production hits; the only
production holders are this file (definitions), `extensions/error_policy.py`
(enforcement), `schema.py` (resolution + authority), `__init__.py`
(re-export), `conf.py` (thin reader + comments), `utils/policies.py`
(precedent pointers), `exceptions.py` (scope-docstring line),
`extensions/debug.py` (precedent pointer line), `consumers.py` (seam
docstring + function-local sibling import). The flavors participate not by
mirroring but by RAISING: every framework rejection is a deliberate
`GraphQLError`, which the sibling classifier leaves untouched — confirmed by
the live matrix rows (`GLOBALID_INVALID`, `RESOURCE_LIMIT_EXCEEDED`,
`Not authorized to ...`, consumer `GraphQLError`). No second policy
vocabulary exists in any flavor. Axis discharged.

**2. Sync/async twins.** Target has no async surface (probe §3: zero
`AsyncFunctionDef`, zero `Await`). Resolution runs at schema construction
(sync by Strawberry contract); validation is pure; the mint is pure
(`uuid.uuid4().hex`, no I/O, no clock read). The sibling docstring states the
teardown is one plain sync generator the engine enters on both paths, so
there is exactly one masking code path and no color-specific branch here to
keep in parity. No twin owed. Axis discharged by absence.

**3. Derived rather than repeated knowledge.** Each default is spelled once
in production (probe §§7–9: the neutral message once as the field default,
`correlationId` once as the field default, `uuid.uuid4().hex` once as the
return). `DEFAULT_ERROR_POLICY = ErrorPolicy()` DERIVES from the field
defaults by construction rather than restating them. `resolve_error_policy`
passes the default object and the field names by reference; the driver's
unknown-key check reads `fields(policy_cls)` at runtime, so the vocabulary
has one spelling. The `display_name="error policy"` / `unit="option"`
wording seeds live once at the call site; the driver owns producing text
from them. Every other spelling is a consumer, oracle, or projection, listed
never counted (sibling reads `policy.message` /
`policy.correlation_extension_key` / `DEFAULT_ERROR_POLICY.message`;
oracles spell all three literals directly; GLOSSARY/README/CHANGELOG restate
them as prose). No reconstructed copy found. Axis discharged.

**4. Inverse / round-trip pairs.** No pair in the target. The mint has no
parse twin by contract: ids are opaque grep tokens, never decoded — the
sibling publishes the id into `extensions` and into the log message text and
nothing anywhere reads one back (sweep: no consumer parses a correlation
id). Resolution has no inverse: construction-only normalization, the schema
never serializes a policy back to a mapping. The `copy_policy` direction
(schema property hands out duplicates) is owned at `schema.py` + the shared
helper, not here. Axis discharged by absence with the stated reason.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target); consumers composing by name (sibling
import of three names; `schema.py` import + resolve call + kwarg default +
copy property; `__init__.py` re-export; `consumers.py` indirect via the
sibling); oracles spelling literals directly and driving behavior through
the public surface (`tests/test_error_policy.py`: default-values row,
per-field parametrized rejection rows, frozen-assignment row,
precedence-ladder rows, unknown-option row, id-format + uniqueness rows,
schema-resolves row, copy-identity row, install-position rows, fallback
rows, teardown no-op rows, fail-closed degrade rows, gate rows;
`test_error_policy_api.py`: the live category matrix + fresh-id-per-error +
log-correlation + retained-path + parity + both opt-outs + resolver-write
rows; `test_conf.py`: setting-supplies / absent-means-None rows;
`test_init.py`: export-membership rows) — all independent (a rename fails
them, none enumerates the owner's internals); projections (all docstrings
here + `schema.py` class/property docstrings + `conf.py` reader docstring +
GLOSSARY/README/SECURITY/CHANGELOG prose + the spec pointer). No oracle
reads the owner to enumerate (the unknown-option oracle spells a typo and
matches the message; it would fail, not follow, a vocabulary change).
Axis discharged.

**6. Enforcement by omission.** The validated population is closed and fully
guarded: all three fields (`enabled` exact-bool arm; `message` /
`correlation_extension_key` shared non-empty-string loop arm — one template,
two members, already shared in-file, not copied). Every construction path
runs the gate: direct construction (`__post_init__` by dataclass
construction), explicit-instance override (driver `canonical_policy`
rebuilds through `policy_cls(**values)` → gate runs again), mapping
override (driver builds `policy_cls(**plain)` → gate runs), absent (the
import-time default, gated once at import). The resolve ladder's own slots
(non-mapping rejection, unknown-key rejection with valid vocabulary) are
owned at the shared driver, already consolidated, consumed here by
arguments. Deliberate omissions with contract sources: (a) no per-field
narrowing (`ResourcePolicy.narrowed` has no counterpart — an error policy
has no maximums to tighten; adding per-field masking granularity would be a
new rule, trigger in R1); (b) the opt-out is spelled `{"enabled": False}`
(a recorded decision, never an omission — `schema.py` + live opt-out rows
pin it); (c) no async twin (axis 2). No member lacks a guard its contract
requires. Axis discharged.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **14 top-level statements** — plus, better than the minimum, every
`ErrorPolicy`-body member (5). Every member lands below; every challenge in
`### Challenges` ends in a family row, a file-local record, or a recorded
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (production-error-policy contract: structural classification, correlation id, DEBUG pass-through, resolve-once) | (none) | projection of F1/F2/R4/R5 owners (see findings) |
| 2 | `from __future__ import annotations` | annotations | machinery |
| 3 | `import uuid` | `uuid` | machinery for R5 |
| 4 | `from collections.abc import Mapping` | `Mapping` | machinery for R4 |
| 5 | `from dataclasses import dataclass` | `dataclass` | machinery for R1 |
| 6 | `from typing import Any` | `Any` | machinery for R4 |
| 7 | `from .conf import error_policy_setting` | setting reader | consumer edge to `conf.py`, R4 |
| 8 | `from .exceptions import ConfigurationError, describe_value` | guard + tail renderer | R2; renderer consumed from open family `typed-rejection-value-tail`, F2 |
| 9 | `from .utils.policies import resolve_policy` | shared driver | R4 (driver owned at `utils/policies.py`) |
| 10 | `__all__ = (…4…)` | leaf manifest | R6, file-local |
| 11 | `class ErrorPolicy` (`@dataclass(frozen=True)`) | policy record | R1/R2 |
| 11.1 | class docstring (field contracts + copy/off-schema authority boundary) | (none) | field prose = projection of R1; boundary prose = projection of `schema.py` authority (R1 distinct-behavior) |
| 11.2 | `enabled: bool = True` | masking switch | R1, file-local |
| 11.3 | `message: str = "An unexpected error occurred."` | stable mask text | R1, file-local |
| 11.4 | `correlation_extension_key: str = "correlationId"` | id publish key | R1, file-local |
| 11.5 | `def __post_init__(self)` | domain gate | R2, file-local |
| 12 | `DEFAULT_ERROR_POLICY = ErrorPolicy()` | package default | R3, file-local |
| 13 | `def resolve_error_policy(explicit)` | resolution ladder | R4, file-local |
| 14 | `def new_correlation_id()` | id mint | R5, file-local |

Rules: R1 record shape + defaults; R2 domain validation; R3 package
default; R4 resolution ladder; R5 correlation-id mint; R6 leaf manifest.
The plan's `## Responsibility index` already carries
`subscription-per-event-error-masking` (open),
`typed-rejection-value-tail` (open), `seal-defect-code-wording` (open),
`sync-boundary-recourse-wording` (rejected), `logger-single-sourcing`
(open), `upstream-patch-install-lifecycle` (rejected) — all six reused
below with triggers re-checked fresh, not renamed. No other existing family
owns a definition here (the resolve/copy/describe sharing lives at
`utils/policies.py` / `exceptions.py`, which this target only feeds and
consumes). No new family is named: R1–R6 each count 1 with no second
definition site; the two considered shared forms are rejections with
contract differences + triggers (J1, J2).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 fourth option | add a field (e.g. per-severity message) | **1** (declaration + `__post_init__` arm here; driver derives the vocabulary, oracles follow) | file-local |
| C2 | R1 message default | stable text → another string | **1** (field default; `DEFAULT_ERROR_POLICY` derives, sibling reads, oracles spell literally) | file-local |
| C3 | R1 key default | `correlationId` → another name | **1** (field default; sibling publishes under it, oracles follow) | file-local |
| C4 | R1 enabled default | `True` → `False` | **1** (field default; the fail-closed direction flips deployment-wide, default-row + live rows follow) | file-local |
| C5 | R2 hostile value | bool subclass / raising-`__str__` string / huge-int option value | **1** (this body; `describe_value` is the consumed renderer, unchanged) | file-local |
| C6 | R1+R4 vocabulary | rename an option | **1** (the field declaration; driver's unknown-key check reads `fields()` at runtime — no second spelling to move) | file-local |
| C7 | R4 precedence | setting outranks the constructor argument | **1** at the driver (`utils/policies.py::resolve_policy` ladder; both policy resolvers follow) — **0** here | shared-driver consumer (see R4) |
| C8 | R4 display wording | rename `"error policy"` / `"option"` seeds | **1** (call-site kwargs here; driver produces the text; resource side has its own seeds and doesn't move) | file-local |
| C9 | R5 id format | `uuid4().hex` → another token | **1** (mint body; sibling calls it, format + uniqueness oracles follow) | file-local |
| C10 | R5 granularity | one id per operation instead of per masked error | **0** here / **1** at the sibling (call placement in `extensions/error_policy.py::_masked` owns the granularity; this file's docstring states it as projection) | independent (see R5) |
| C11 | R2 message reword | reword the `enabled` rejection | **1** (this raise; the debug bool message doesn't move — proves J1) | file-local |
| C12 | R2 template reword | reword the string-field template | **1** (loop body; both fields share the template by loop, not by copy — sharing already in-file) | file-local |
| C13 | R3/R4 new reader | a third consumer reads the resolved policy | **0** new definitions (readers compose by name: sibling `_policy`/`schema_error_policy`, `consumers.py` seam, property) | independent |
| C14 | R2 gate placement | validate in the resolve path instead of `__post_init__` | refused — one gate, not two: every driver path rebuilds through `policy_cls(…)` so the gate runs on all of them (see R2) | refused |
| C15 | R1+R3+R4 symmetry | unify `ErrorPolicy`/`ResourcePolicy` records, defaults, or resolvers | refused — J2 (shared driver already owns the ladder; remainder is distinct vocabulary) | refused |

**Experiment.** Read-only probe (no source mutation, no Django setup, no
DB, no shared-tree pytest — the workspace recipe is for mutating proofs, of
which this zero-edit item has none):

```shell
python3 docs/dry/temp-tests/dry-file-error_policy/probe_w1.py
```

Output (`W1 PROBE: ALL OK`, 22 checks): 14-member module AST with field
defaults (§§1–2); zero async nodes (§3); four-name manifest (§4); all three
literals single-sited, zero logger/patch-lifecycle vocabulary (§5);
import/use census (§6: setting reader 2, renderer 3, driver 3, two raises,
one class, two functions); item-baseline diff empty + working blob equals
`HEAD:` blob (§7); package population 117 (§8). Status:
`execution-verified` for every identity/count/shape/absence claim below.
Rejects the wrong results "a fifth mask literal exists", "a logger site
exists here", "an async twin exists", "the target drifted from its
baseline".

## Findings

No production edit is owed by a file item; the six families below are
REUSED from the plan (each trigger re-checked fresh on current evidence),
the rest are file-local records and two recorded rejections.

### F1 — subscription per-event error masking (existing family `subscription-per-event-error-masking`, status stays `open`)

- **Contract + variation.** One classifier, one replacement builder, two
  application sites (query teardown + per-event transport seam). Variation:
  policy values and result shapes. This file holds NONE of the masking
  machinery; it supplies the configuration the machinery reads
  (`ErrorPolicy` values) and the primitive the replacement builder calls
  (`new_correlation_id`).
- **Behavior/contract comparison (before calling anything here unique).**
  The sibling's `_masked` reads `policy.message` /
  `policy.correlation_extension_key` and calls `new_correlation_id()` once
  per masked error; `mask_execution_result` / `is_maskable_result` /
  `masking_is_active` / `schema_error_policy` neither import nor restate
  anything defined here beyond those three names. Posit C10 (per-operation
  id): the mint doesn't move, the call placement does — the granularity is
  the sibling's contract, stated here only as docstring projection. Posit a
  new maskable shape: `is_maskable_result` moves, nothing here does. The
  two modules are configuration vs application, split at the import edge
  (`extensions/error_policy.py` imports three names from here; this file
  imports nothing from it — the dependency runs one way, so no cycle can
  form). Distinct rules sharing an interface, not one rule twice.
- **Sites + roles.** *Definitions* (all at the owner, unchanged):
  `extensions/error_policy.py::mask_execution_result`,
  `::is_maskable_result`, `::masking_is_active`, `::schema_error_policy`.
  *Consumers*: the extension teardown and
  `consumers.py::_stop_aware_results` (owner side); this file's
  `ErrorPolicy` values + `new_correlation_id` are the consumed
  configuration/primitive (listed, never counted). *Oracles*: the
  error-policy suite + live matrix + subscription rows (unchanged).
  *Projections*: both module docstrings (each names the other's half —
  verified both directions: this module's "owns the policy object" line and
  the sibling's enforcement lines).
- **Challenges.** C9 → 1 here (mint format); C10 → 0 here / 1 at the owner
  (granularity); every masking-shape change → 0 here. Count stays 1 per
  axis at exactly one owner each.
- **Trigger re-checked fresh (not inherited).** The recorded trigger is a
  third application seam or a classifier change needed in two places.
  Measured today: still exactly two seams (teardown +
  `_stop_aware_results`, both bodies re-read, both composing the same four
  helpers by name); `mask_execution_result` still the only classifier
  caller; no third seam, no restated classification. The family stays open
  on fresh evidence, with nothing owed from this file.
- **Owner + lifetime.** `extensions/error_policy.py` (unchanged). No stored
  derivation in this target (the default singleton is import-time
  construction, not a cached derivation; the mint is pure per call).
- **Migration.** None (zero-edit item).
- **Distinct behavior.** The per-error granularity + shape gate stay at the
  owner; the mint's format + the three defaults stay here; neither may be
  "simplified" into the other (C10 proves the split).
- **Behavioral proof.** `execution-verified` for the import-direction
  census + literal/shape counts (probe §§5–6); `static-reviewed` for seam
  bodies + oracle bodies (no shared-tree pytest per item rules). Rejects
  "this file classifies or masks".
- **Structural gate.** The existing per-event masking rows + the
  copy-contract rows (`masking_returns_the_same_object…`,
  `masking_leaves_the_original…`): inlining a local mint or a local
  message default here passes nothing new and fails the format/uniqueness
  rows on divergence. Negative control (stated honestly, not run): a
  behavior-preserving hand copy of `new_correlation_id` into the sibling
  passes every behavioral oracle and fails only the import census — so the
  seam's unity rests on the one-way import edge plus this finding, not on a
  behavioral gate; the reconsideration trigger above is what re-opens it.
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/error_policy.py`
  `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91`,
  `django_strawberry_framework/extensions/error_policy.py`
  `baea073f5615aaddc82c1f463071998bee7a6b62`,
  `django_strawberry_framework/consumers.py`
  `18f3ea161b6081a91445796902a9635cb7e2e3bc` (seam lines),
  `tests/test_error_policy.py`
  `4fa9852721b139c07274bdd73c9e0cda6d68f155`,
  `examples/fakeshop/test_query/test_error_policy_api.py`
  `5dbcf2013f98b10567b0dc8efddd9705141fa6c7`.

### F2 — typed rejection value tail (existing family `typed-rejection-value-tail`, status stays `open`)

- **Contract + variation.** Every typed rejection whose value came from
  outside the package renders its `got` tail through
  `exceptions.py::describe_value`, so the message cannot raise while being
  formatted. Variation: per-domain prose; the renderer fixed. This file's
  two `__post_init__` raises are consumers (both tails via the renderer),
  not definitions.
- **Sites + roles.** *Definition*:
  `exceptions.py::describe_value` (unchanged; its scope paragraph already
  names `error_policy.py` among the in-scope rejections — corroborated).
  *Consumers verified here*: the `enabled` raise + the string-field loop
  raise. *Oracles*: the huge-int/hostile-`__repr__` rows at the owner
  (bodies cited, not re-litigated). *Projections*: the owner scope
  paragraph.
- **Challenges.** C5 → 1 at the renderer for a renderer change; **1 here**
  for a prose change (C11/C12 — per-domain wording stays per site, which
  is the family's stated split). The tail is shared; the sentences are
  not.
- **Index note for Worker 0 (additive only, never an edit by this worker).**
  The plan's index row lists `exceptions.py`, `consumers.py`, `views.py`,
  `routers.py` under Files covered; the owner's own scope paragraph plus
  this trace establish `error_policy.py` (and, seen in passing,
  `resource_policy.py`, `extensions/debug.py`) as further consumers.
  Whether the row's file list gains them is Worker 0's call; no definition
  count changes either way.
- **Trigger re-checked fresh.** A second tail renderer (a site
  interpolating `{value!r}` directly for an outside-package value) would
  reopen. Swept: this file's only two tails both go through the renderer
  (probe §6: three `describe_value` spellings = import + two uses).
- **Owner + lifetime.** `exceptions.py` (unchanged). Pure derivation, never
  cached.
- **Migration / Coupling.** None.
- **Behavioral proof.** `execution-verified` for the use census (probe);
  `static-reviewed` for renderer body + scope paragraph. Rejects "this
  file interpolates the value itself".
- **Structural gate.** The owner's hostile-tail rows (direct interpolation
  raises `ValueError` instead of `ConfigurationError`). Negative control:
  `f"{value!r}"` in `__post_init__` passes every small-value oracle and
  fails exactly those rows.
- **Freshness.** Target as in F1 +
  `django_strawberry_framework/exceptions.py`
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`.

### F3 — seal defect code wording (existing family `seal-defect-code-wording`, checked, not a member)

- **Contract difference.** The seal family renders `(code, detail)` tuples
  through `utils/querysets.py::_defect_message` with a fixed position per
  code. This file publishes ONE stable neutral string that interpolates
  nothing by construction. A seal code names an internal invariant for the
  deployment's logs; the mask names nothing for an untrusted reader. Posit
  adding a seal code → the seal ladders move, nothing here does (C1's
  analogue at the seal). Posit rewording the mask → the seal ladders don't
  move (C2). Shared form considered (one "stable message" vocabulary for
  seal defects and masked errors): refused — different readers, different
  variation axes, opposite disclosure directions.
- **Reconsideration trigger.** A wire vocabulary shared between seal
  defects and masked errors (a seal code published to clients verbatim, or
  the mask gaining a code enum) — then the wording becomes one rule.
- **Durable home.** This finding + the seal owner
  (`utils/querysets.py::_defect_message`); no edit here to record it in.
- **Freshness.** Target as in F1 (no second site visited beyond the
  family's own record; bodies not re-litigated).

### F4 — sync boundary recourse wording (existing family `sync-boundary-recourse-wording`, checked, not a member)

- **Contract difference.** The recourse family generates per-hook remedy
  sentences naming hooks (`has_permission` / `check_permission`,
  `check_<field>_permission`) and remedies. This file's prose names no
  hook and offers no remedy; its rejections name the offending field and
  stop. Posit rewording a recourse sentence → nothing here moves (C11's
  analogue there); posit C11/C12 here → no recourse sentence moves. The
  family's standing rejection (rejected in the index) is corroborated, not
  inherited: only one clause is ever shared ("runs synchronously…"), and
  this file doesn't share even that.
- **Reconsideration trigger.** A recourse sentence quoting the policy
  message contract (masking remedy pointing at `ErrorPolicy`) — then the
  shared clause becomes the rule.
- **Durable home.** This finding + the recourse owners
  (`utils/querysets.py::sync_pipeline_recourse` and its decliners).
- **Freshness.** Target as in F1.

### F5 — logger single-sourcing (existing family `logger-single-sourcing`, checked, not a member)

- **Contract difference.** The family owns the one `getLogger` call at the
  package root. This file emits no log record at all — masking logs live in
  the sibling's `_masked` / `_degraded` / teardown, which composes the
  family by name (`from .. import logger`). Probe §§5: zero `getLogger`,
  zero `import logger` in the target; package-wide sweep still finds the
  single call at `django_strawberry_framework/__init__.py::logger`.
- **Reconsideration trigger.** A log record emitted from this module (a
  second `logger` import here) — then it becomes a consumer row.
- **Durable home.** This finding + the root owner; nothing to record here.
- **Freshness.** Target as in F1 +
  `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`.

### F6 — upstream patch install lifecycle (existing family `upstream-patch-install-lifecycle`, checked, not a member)

- **Contract difference.** The lifecycle owns gate→validate→check→install
  per patch module plus the `conf.py` gate vocabulary. The target holds
  none of it: no `apply()`, no gate read, no dependency name (probe §5).
  Its install story is "no install" — import-time dataclass construction
  plus schema-construction resolution, enforced by Strawberry's own
  constructor path.
- **Reconsideration trigger.** A patch module arriving for this file's
  dependencies (none exist — it imports only `conf`, `exceptions`,
  `utils.policies`) or a sequence-level install change spanning modules.
- **Durable home.** This finding + the rejected index row; nothing here.
- **Freshness.** Target as in F1.

### File-local records (no second definition after the matrix)

- **R1 — policy record shape + fail-closed defaults.**
  `error_policy.py::ErrorPolicy` (`enabled=True`, neutral `message`,
  `correlation_extension_key="correlationId"`, frozen). C1, C2, C3, C4, C6
  → 1 each (declaration; driver derives vocabulary, `DEFAULT_ERROR_POLICY`
  derives values, sibling reads by attribute, oracles spell literally).
  The class-docstring boundary prose (copy per read, off-schema authority)
  is projection of `schema.py::DjangoSchema.error_policy` +
  `schema.py::_SCHEMA_ENFORCEMENT` + `utils/policies.py::copy_policy`,
  verified against those bodies — this file defines no boundary code, so
  no second definition exists to consolidate. Frozen rejects `setattr`
  (oracle-pinned) and the docstring honestly records it admits
  `__dict__` writes — which is WHY the authority lives off-schema; the
  honesty is load-bearing, not a gap. Trigger: a second policy record
  with the same three options the package must keep in sync would make it
  a family (see J2 for why the resource policy isn't that). Freshness:
  target + `schema.py`
  `2f72732123ca1156c4eb122ce7b53de6269de95e` (authority lines) +
  `utils/policies.py`
  `860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e` +
  `tests/test_error_policy.py` as in F1.
- **R2 — per-field domain validation.**
  `error_policy.py::ErrorPolicy.__post_init__` (exact-`bool` arm for
  `enabled`; shared non-empty-string loop arm for the two string fields;
  both tails via `describe_value`, F2). C5, C11, C12 → 1 each; C14 refused
  (one gate: every driver path rebuilds through `policy_cls(…)`, so
  direct, explicit-instance, mapping, and default paths all run this same
  body — verified in `utils/policies.py::canonical_policy` /
  `::resolve_policy`). The bool arm uses `not isinstance(x, bool)` while
  `resource_policy.py::validate_trusted_flag` uses exact `type(x) is not
  bool` — an owned strictness difference (see J1), not drift. Trigger: a
  second validator over these same three fields would make it a family.
  Freshness: target + `exceptions.py` as in F2 +
  `tests/test_error_policy.py` as in F1.
- **R3 — package default.** `error_policy.py::DEFAULT_ERROR_POLICY`
  (single construction from the field defaults; the fail-closed answer by
  doing nothing). No other spelling of the three defaults exists in
  production (probe §§7–8). The sibling's masking fallback and the
  schema's kwarg default + `_FALLBACK_ENFORCEMENT` compose it by name.
  Trigger: a second default-construction site would make it a family.
  Freshness: target + `extensions/error_policy.py` + `schema.py` as above.
- **R4 — construction-time resolution ladder.**
  `error_policy.py::resolve_error_policy` (explicit argument > setting >
  default; instance → `canonical_policy` duplicate; mapping over defaults;
  rejections at the driver). C7 → 0 here / 1 at the driver; C8 → 1 (the
  `display_name`/`unit` seeds); C13 → 0 new. The ladder BEHAVIOR is the
  shared `resolve_policy` driver (already consolidated — nothing owed
  here); this function is the error-side declaration feeding it
  (`policy_cls`, `default`, `read_setting`, seeds). The thin reader
  `conf.py::error_policy_setting` validates nothing by its documented
  split (consumer docstring + rejection rows pin it). Trigger: a third
  schema-construction policy arriving with the same ladder would feed the
  same driver (the driver's own trigger, not a new row here). Freshness:
  target + `utils/policies.py` + `conf.py`
  `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25` + `schema.py` +
  `tests/base/test_conf.py`
  `f35c70742354d0ab123b163a92c6a8a503c6ea29`.
- **R5 — correlation-id mint + per-error contract.**
  `error_policy.py::new_correlation_id` (`uuid.uuid4().hex`; not a
  counter/timestamp/request-id; fixed-width grep-safe; one id PER MASKED
  ERROR). C9 → 1 (format); C10 → 0 here / 1 at the sibling (granularity
  owned by call placement in `_masked` — the docstring's per-error clause
  is projection, honestly placed where a deployer looks). The mint lives
  here rather than beside its caller so this module stays engine-free
  (imports: `conf`, `exceptions`, `utils.policies` — no strawberry,
  graphql-core, or Django imports; the sibling carries those), keeping the
  dependency one-way. Trigger: a second id mint (per-operation ids, or a
  second token shape) would make it a family. Freshness: target +
  `extensions/error_policy.py` as in F1 +
  `tests/test_error_policy.py` as in F1 (format + uniqueness rows).
- **R6 — leaf manifest.** `__all__` (four names; every top-level
  definition exported, nothing else). Imported by name at the root (two
  names) and by `schema.py` (three names); `new_correlation_id` additionally
  by the sibling. A fifth public helper would extend this tuple in one
  place. Trigger: a second manifest over these names (a root-level
  re-spelling) would make it a family. Freshness: target +
  `django_strawberry_framework/__init__.py` as in F5 +
  `tests/base/test_init.py`
  `4cc121057689409213beb5ec31772130cdacb975`.

### J1 — shared security-bool helper (refused shared form, recorded here)

Three bool gates share the `must be a bool; got {tail}` token shape:
`ErrorPolicy.enabled` (`not isinstance`, default `True`, guards a masking
switch), `extensions/debug.py::DjangoDebugExtension.__init__`'s
`allow_unsafe_production` (`not isinstance`, default `False`, guards a
disclosure acknowledgement), `resource_policy.py::validate_trusted_flag`
(exact `type(x) is not bool`, no default, guards a widening opt-in).
Posit rewording one message (C11) → exactly one moves; posit flipping one
default → exactly one moves (and two of the three defaults point opposite
ways, so no shared default exists to own); posit tightening one check to
exact-type → the other two don't move (the resource side already proves
the stricter spelling is a per-site decision). The per-site prose names
the deployment danger each refusal prevents (silent opt-out vs armed
disclosure vs silent widening) — unifying the helper would couple three
unrelated dangers to one sentence. Reconsideration trigger: a fourth
security-bool gate arriving with identical rationale AND no per-site
danger prose — then the mechanism (not the messages) becomes the shared
rule with this finding as its seed. Durable home: this finding + each
owner's own rationale paragraph (all three already state their danger; no
edit owed). No new index row today.

### J2 — error/resource policy unification (refused shared form, recorded here)

Both policies carry a `DEFAULT_*`, a frozen dataclass, an extension, and a
`resolve_*` — the symmetry the task named to sweep, not assume. Pair by
pair: the ladders already share one driver
(`utils/policies.py::resolve_policy` — C7 proves it: one precedence change
moves the driver, both resolvers follow); copies share `copy_policy`;
tails share `describe_value`; canonicalization shares `canonical_policy`.
What remains per policy is distinct vocabulary, not shared mechanism:
three string/bool options with a neutral message vs twenty numeric bounds
with a deadline; `display_name`/`unit` seeds differing per side; install
positions inverse by lifecycle (masking prepends to tear down last,
budget appends to set up last — each docstring records the other's
direction); `narrowed` existing only on the resource side (R1's deliberate
omission (a)). Posit C15 (one base record): the driver would own the
mechanism but pin neither vocabulary, and a change to either side's fields
(C1 vs a new bound) moves exactly one body today. Reconsideration trigger:
a third schema-construction policy arriving with the identical
declare→canonicalize→resolve→copy shape — then the SHAPE (not the fields)
becomes a family with the driver as its owner. Durable home: this finding
+ the driver's module docstring (already states the two-resolver contract)
+ each resolver's "structural twin" paragraph. No new index row today.

## Defects

None. Every claim checked while tracing held: all three defaults match
their documented values with single production spellings (probe §§7–8);
the import-direction edge runs one way (sibling imports three names from
here, never the reverse); every construction path runs the one gate
(driver bodies read); the copy/off-schema boundary prose matches
`schema.py` bodies (`copy_policy` per read, `_SCHEMA_ENFORCEMENT` holding
the authority, `_FALLBACK_ENFORCEMENT` carrying this default); the
per-error granularity prose matches the sibling's per-error call placement;
the thin-reader split matches `conf.py`; the DEBUG pass-through and
classification prose match the sibling's `masking_is_active` /
`_is_unexpected` bodies; oracles pin each behavior they describe. Nothing
routed to any owner.

(Worker 2) Re-traced independently: every claim above held on current
bytes (own probe, 32 checks, `W2 PROBE: ALL OK`; all twelve re-hashed
fingerprints match). No additional defect found.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
117-file sweeps, command in `### Challenges`) already ran green against the
shared tree; they mutate no source, open no database, and import no Django,
so no workspace copy was owed and no `__file__`/DB `NAME` record applies.
No pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. No `FAKESHOP_SHARDED` or
Postgres cell is owed: the target's code path reaches no database, alias,
or dialect decision (`inapplicable by construction` — pure dataclass
construction plus a settings-dict read at schema construction; the only
settings-adjacent value is a string key default never resolved here).

## Judgment

Backstop discharged: 14/14 `ast.Module.body` members enumerated plus all 5
`ErrorPolicy`-body members, 15 challenges run, every rule terminating in
one of the six existing families it touches (each trigger re-checked
fresh — `subscription-per-event-error-masking` compared by
behavior/contract and held distinct; `typed-rejection-value-tail` as the
consumed renderer with an additive index note; `seal-defect-code-wording`,
`sync-boundary-recourse-wording`, `logger-single-sourcing`,
`upstream-patch-install-lifecycle` all checked and held non-members), a
file-local record with its proving challenge (R1–R6), or a recorded
rejection with difference + trigger + owner home (J1, J2) — no
consolidation owed, no defect found, no new family named. The
error/resource symmetry is already consolidated at the shared driver; what
remains per side is distinct vocabulary with opposite lifecycle positions.
Zero-edit result is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: the only
families this target touches are already indexed (F2 carries one additive
Files-covered note, for Worker 0 to accept or decline); the two refused
shared forms live at their owner paragraphs plus this finding.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
399ce748491f6e57a75d023802dbb3e89b8e81e6 --
django_strawberry_framework/error_policy.py` is empty (0 bytes,
re-measured after the probe run via probe §7); the working blob
`fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91` equals the item baseline, the
cycle-baseline member, and `HEAD:` — the target is clean, so no hunk
attribution was owed. Before touching any path, the item-scoped paths were
verified clean; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt (`connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied, and no other dirty path was written (sibling
`dry-file-*.md` untracked artifacts and the `dry-file-utils__querysets.md`
modification are other items' work, left alone). Dirt elsewhere left alone,
not a stop. No commit. Untracked scratch created (not tracked changes):
this artifact `docs/dry/dry-file-error_policy.md` and the read-only probe
`docs/dry/temp-tests/dry-file-error_policy/probe_w1.py` (`W1 PROBE: ALL
OK`, 22 checks; no source mutation, no Django import, no DB, no
shared-tree pytest). No ruff run owed (no tracked `.py` edits; artifact is
`.md` only; probe is untracked scratch). No `__file__`/DB record (no
workspace copy — no mutating proof exists).

## Independent verification (Worker 2)

Own trace recorded BEFORE reading `## Findings` above (read order held:
AGENTS.md, DRY.md, worker-2.md, plan item, target, item-scoped diff,
consumers/tests, then the artifact; never worker-memory).

### Own rule derivation

From the target's 152 lines I derive six rules, each with one authoritative
definition, all owned here:

- **R1 record shape + fail-closed defaults** — `error_policy.py::ErrorPolicy`:
  three fields (`enabled=True`, neutral `message`, `correlation_extension_key`
  `"correlationId"`), frozen. Owner: here (narrowest cohesive record every
  legitimate consumer — sibling, schema, root re-export — can depend on
  without reversing a dependency).
- **R2 domain gate** — `error_policy.py::ErrorPolicy.__post_init__`: exact-bool
  arm for `enabled`, shared non-empty-string loop arm for the two string
  fields. Owner: here (validation lives with the record it guards).
- **R3 package default** — `error_policy.py::DEFAULT_ERROR_POLICY`: single
  `ErrorPolicy()` construction deriving the field defaults. Owner: here.
- **R4 resolution ladder** — `error_policy.py::resolve_error_policy`:
  explicit argument > setting > default. The LADDER BEHAVIOR is owned at
  `utils/policies.py::resolve_policy` (already consolidated); this function
  is the error-side declaration feeding it (`policy_cls`, `default`,
  `read_setting`, `display_name`/`unit` seeds). Owner split: mechanism at
  the driver, declaration here.
- **R5 correlation-id mint** — `error_policy.py::new_correlation_id`:
  `uuid.uuid4().hex` per call. FORMAT owned here; per-masked-error
  GRANULARITY owned at the call placement in
  `extensions/error_policy.py::_masked` (one call per masked error).
- **R6 leaf manifest** — `__all__` with four names. Owner: here.

Counts: R1–R6 each count **1** authoritative definition. No second
definition site found for any of them after the sweep below.

### Sibling comparison (behavior/contract, before calling anything unique)

- **Masking family** (`extensions/error_policy.py`): configuration vs
  application, split at a one-way import edge (sibling imports
  `DEFAULT_ERROR_POLICY`, `ErrorPolicy`, `new_correlation_id` from here;
  this file imports nothing from it — verified by text census in probe W2).
  All of `mask_execution_result`, `is_maskable_result`, `masking_is_active`,
  `schema_error_policy`, `_masked`, `_degraded`, `_is_unexpected`,
  `on_operation` live at the sibling and nowhere here. Posit per-operation
  ids: the mint doesn't move, the call placement does — granularity is the
  sibling's contract. Owner per row: masking rows at the sibling, mint
  format + policy values here. Agree with W1 F1 (distinct, family stays
  open on fresh trigger check: still exactly two seams, teardown +
  `consumers.py::_stop_aware_results`, both re-read composing by name).
- **Resource-policy symmetry**: ladders already share the driver
  (`policy_cls=ErrorPolicy` here vs `policy_cls=ResourcePolicy` there, both
  into `utils/policies.py::resolve_policy`); copies share `copy_policy`;
  tails share `describe_value`; canonicalization shares `canonical_policy`.
  Remainder is distinct vocabulary (3 string/bool options with a neutral
  message vs ~20 numeric bounds with a deadline; `narrowed` only on the
  resource side — an error policy has no maximums to tighten, so the
  omission is deliberate, not a gap). Install positions are inverse by
  lifecycle (masking prepends to tear down last, budget appends to set up
  last). No unification owed. Agree with W1 J2.
- **Bool-gate trio** (W1 J1): confirmed the owned strictness difference
  myself — here `not isinstance(self.enabled, bool)` (admits bool
  subclasses), `resource_policy.py::validate_trusted_flag` exact
  `type(declared) is not bool`, `extensions/debug.py` `not isinstance`;
  defaults point different ways (`True` masking switch vs `False`
  disclosure acknowledgement vs no default on a widening opt-in). Three
  unrelated deployment dangers, no shared default to own. Refusal stands.
  Agree with W1 J1.

### Reconciliation vs W1

Per-row verdicts: F1 agree (distinct, open). F2 agree (consumer, open) —
with the index-note ruling below. F3 agree (checked, not a member: seal
codes name an internal invariant for logs, the mask names nothing for an
untrusted reader; opposite disclosure directions). F4 agree (checked, not
a member: recourse sentences name hooks and remedies, these rejections
name the field and stop). F5 agree (checked, not a member: zero
`getLogger`/`import logger` in target, verified by probe). F6 agree
(checked, not a member: no `apply()`, no gate read, no dependency name).
R1–R6 agree (file-local with proving challenges C1–C15; C7/C10/C13–C15
correctly counted 0 here). J1/J2 agree (refused with difference +
trigger + durable home). Zero defects agree (every claim I re-checked
held). Zero pending agree.

**Ruling on the F2 index files-covered note** (the one judgment W1 left to
the verifier): the plan's `typed-rejection-value-tail` row lists
`exceptions.py`, `consumers.py`, `views.py`, `routers.py`. ADD
`error_policy.py` — verified-correct: the owner's own scope paragraph
(`exceptions.py::describe_value` scope clause) explicitly names
`error_policy.py` among the in-scope rejections, and both `__post_init__`
raises route their tails through the renderer (probe: three
`describe_value` spellings = import + two uses). HOLD the
`resource_policy.py` / `extensions/debug.py` mentions as unverified from
this item: the owner paragraph plausibly covers them and I saw their
imports in passing, but their consumption claims belong to their own file
items to verify member-by-member — Worker 0 should add them only when
those items confirm, not on this item's evidence.

### Enumeration check (member by member, own instrument)

Own `ast.parse` run (probe W2, independent of W1's): **14**
`ast.Module.body` members (docstring, 5 imports incl. `__future__`, 3
from-imports, `__all__`, class, default assign, 2 functions) and **5**
`ErrorPolicy`-body members (docstring, 3 `AnnAssign`, `__post_init__`).
W1's table rows 1–14 + 11.1–11.5 land every member: 1 projection,
2–6 machinery, 7 consumer edge (R4), 8 guard + consumed renderer (R2/F2),
9 shared driver (R4), 10 R6, 11/11.1–11.5 R1/R2, 12 R3, 13 R4, 14 R5.
No member unassigned, no row without a member. Matrix judged against the
real surface: axis 1 swept all nine flavor folders for the policy
vocabulary (only raising, never a second vocabulary — confirmed via the
grep census); axis 2 absence proved (zero `AsyncFunctionDef`/`Await`,
probe-verified); axis 3 single-spellings proved (each literal once);
axis 4 absence-with-reason (opaque ids never parsed back; resolution has
no inverse); axis 5 four media classified with roles; axis 6 closed
population (all three fields gated on every construction path via
`canonical_policy` rebuild — bodies read). No claimed inapplicability
accepted on assertion alone.

### Counts, roles, oracles

Definition counts confirmed per challenge axis (C1–C6/C8/C9/C11/C12 → 1
here; C7 → 0 here / 1 at driver; C10 → 0 here / 1 at sibling; C13 → 0
new; C14/C15 refused with stated reason). Roles confirmed: sibling +
`schema.py` + `__init__.py` + `consumers.py` seam consume by name; oracles
(`tests/test_error_policy.py`, live `test_error_policy_api.py`,
`test_conf.py`, `test_init.py`) spell literals directly and drive behavior
through the public surface — no oracle reads the owner to enumerate
(`resolve_policy`/`canonical_policy`/`fields(` absent from the suite;
unknown-option rows spell typos `mesage`/`nope` and match the message, so
a vocabulary change fails them rather than follows). No oracle rewritten.

### Equivalence (principle 8)

Zero-edit item: no observable behavior exists to preserve across a change,
so the principle-8 obligation reduces to (a) confirming the diff is empty
(done below) and (b) confirming no finding smuggles a behavior change —
all six file-local records and both rejections route to documentation-only
homes (owner paragraphs + this finding), none to production. Satisfied.

### Zero-edit confirmation

Ran the item-scoped diff myself: `git diff
399ce748491f6e57a75d023802dbb3e89b8e81e6 --
django_strawberry_framework/error_policy.py` is empty (exit 0); working
blob `fa94fcd9…` equals `HEAD:` blob. No production edit demanded: as a
FILE item this target owes coverage + assignment only, both discharged
(14/14 + 5/5 enumerated; every rule in a family row, file-local record,
or rejection). No candidate found that a family item should take — the
two considered shared forms are recorded rejections with triggers, not
consolidations.

### Rejections, fingerprints, gates, pending, coupling

J1/J2 carry contract difference + reconsideration trigger + durable home
(owner paragraphs + finding); no new index row proposed for either —
correct, since neither names a second definition. Fingerprints re-hashed
by me against the tree — all match W1's record: target `fa94fcd9…`,
sibling `baea073f…`, `exceptions.py` `e06b0b7f…`, `__init__.py`
`0ef72601…`, `utils/policies.py` `860b181f…`, `consumers.py`
`18f3ea16…`, `tests/test_error_policy.py` `4fa98527…`, live API
`5dbcf201…`, `test_conf.py` `f35c7074…`, `test_init.py` `4cc12105…`,
`schema.py` `2f727321…`, `conf.py` `c6ad46aa…` (resource-policy blob
`647133d2…` and `extensions/debug.py` `bf25c146…` hashed for the record;
neither was fingerprinted by W1). Nothing stale. Gates: F1 honestly
carries no behavioral gate (one-way import edge + trigger instead) —
accepted, since the unity claim is structural and the trigger re-opens
it; F2's gate (`test_describe_value_on_printable_and_unprintable_values`
hostile/huge-int rows — a direct `f"{value!r}"` in `__post_init__`
raises `ValueError` instead of `ConfigurationError`) fails its negative
control by construction; both are family-owned gates referenced, not
introduced, so no new gate is owed here. `## Pending execution` absent —
correct: the probes mutate nothing, open no DB, import no Django (pure
AST + text + git hashes), and no shared-tree pytest was run per item
rules; `inapplicable by construction` holds for sharded/Postgres cells
(pure dataclass construction + settings-dict read at schema
construction). Coupling: none marked — correct, nothing lands together.

### AGENTS.md prose check

Item-scoped diff empty → no source edits to format/lint, no tests tier
owed, no changelog, no commit. Artifact citations use `path::Symbol`
form throughout (spot-checked: no raw `path:NN` outside the allowed
scratch context). No process provenance in the artifact. Concurrent dirt
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`, sibling untracked `dry-file-*.md` artifacts)
never edited, reverted, or tidied — verified via `git status --short`
after my work: only pre-existing dirt plus this artifact and the two
probe files. My scratch lives strictly under
`docs/dry/temp-tests/dry-file-error_policy-w2/` (fresh `probe_w2.py`, 32
checks, `W2 PROBE: ALL OK`, read-only); W1's scratch untouched.

### Verdict (Worker 2)

**Verified**, no pending execution. Backstop discharged (14/14 +
5/5, 15 challenges with counts, six existing families reused with
triggers re-checked fresh, six file-local records, two recorded
rejections, zero defects). The error/resource symmetry is already
consolidated at the shared driver; what remains per side is distinct
vocabulary with opposite lifecycle positions. Zero-edit result
legitimate for a file item.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[worker-1]: worker-1.md
[worker-2]: worker-2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Bounded re-review at bfaee91d (Worker 2, Q2)

Phase 1 independent re-derivation. Prior findings not opened. No status set. No verdict proposed.
Scope: whether the error-policy floor behavior recorded for the ROOT error_policy.py module
still holds at current bytes after the extension module changed under it.

### 1. Floor behavior re-derived from current source

Read whole: django_strawberry_framework/extensions/error_policy.py (worktree bytes),
django_strawberry_framework/error_policy.py (whole), plus diff 9031cb3d..bfaee91d scoped to
the extension module, plus consumers and oracles listed under Freshness.

Classification: django_strawberry_framework/extensions/error_policy.py::_is_unexpected.
Non-GraphQLError in errors list is unexpected and masked. GraphQLError with
original_error None is deliberate and travels (parse, syntax, validation, engine-built).
GraphQLError whose original_error is itself a GraphQLError is deliberate and travels
(framework rejections, mutation authorization denial, consumer-raised GraphQLError).
Anything else (plain Python exception behind GraphQLError, including every
graphql-core located_error wrap from resolve and from completion: non-null null
propagation, list-item completion, scalar serialize) is unexpected and masked.
The original_error read is a direct attribute access. A read that raises is not
answered as deliberate; it unwinds to the per-entry degrade (fail closed).

Replacement: django_strawberry_framework/extensions/error_policy.py::_masked.
One fresh new_correlation_id per masked error (uuid4 hex, 32 chars). Server log via
logger.error with exc_info set to the behind-exception and the correlation id in the
message text. Wire replacement is a fresh GraphQLError carrying policy.message only,
with nodes, source, positions, path retained, original_error None, and extensions set
to exactly one entry under policy.correlation_extension_key. No part of the original
message or exception travels.

Per-entry floor: django_strawberry_framework/extensions/error_policy.py::_degraded.
Policy message alone, no location, no correlation id, no extensions. Nothing is read
off the offending error. The policy.message read itself is guarded by try/except;
a raising, non-string, or empty answer is replaced by DEFAULT_ERROR_POLICY.message,
which validated itself at construction. Applied by _replacement_for on any
classify-or-mask raise, preserving order and arity for the surviving entries.

Whole-response floor: django_strawberry_framework/extensions/error_policy.py::degraded_result.
StrawberryExecutionResult with data None and errors [_degraded(policy)]. Drops data,
errors, and extensions together: the seam that reached it could not certify the result,
so no half-response is published. The failure itself is logged by the caller that
knew what it was doing. Shared by all three seams so every fail-closed path publishes
the same shape.

Gates: django_strawberry_framework/extensions/error_policy.py::masking_is_active,
django_strawberry_framework/extensions/error_policy.py::is_maskable_result,
django_strawberry_framework/extensions/error_policy.py::schema_error_policy.
masking_is_active answers policy.enabled and settings.DEBUG is not True, both reads
failing toward masking (enabled raise answers True; DEBUG raise answers not True).
is_maskable_result admits only GraphQLExecutionResult and StrawberryExecutionResult
(PreExecutionError admitted, contributes nothing since original_error is None);
excludes None, incremental-delivery frames, and any non-result shape.
schema_error_policy answers schema.error_policy when it is an ErrorPolicy instance,
else DEFAULT_ERROR_POLICY (absent, wrong-typed, or raising attribute all fall back
to the masking default).

mask_execution_result composes the above. None errors or materialized-empty list
returns the input by identity. Else one _replacement_for per entry; all-identical
returns the input by identity (no allocation, no id minted, no log). Otherwise a
shallow copy carries the rewritten list, leaving the engine-assigned object holding
its originals for later original_error readers. An unreadable error list degrades
to degraded_result(policy) with a logged traceback (the only arity-changing path).

Per operation at HEAD plus worktree bytes:
Normal query or mutation via schema.execute: operation teardown reads the completed
result off the operation engine context, gates on masking_is_active and
is_maskable_result, adopts via _process_result (field-wise data, errors, extensions
copy; adoption failure replaces execution_context.result with degraded_result).
Then schema return seam re-masks the returned value under the same gates. Idempotent
by construction: a teardown-masked error carries original_error None, which the
classifier reads as deliberate, so the second pass returns by identity with no second
id or log record.
Streamed operation (every subscription; query or mutation over a streaming
transport): each yielded event masked at the transport result source
(consumers.py::_stop_aware_results) via masking_is_active plus is_maskable_result
plus mask_execution_result copy semantics; operation-end teardown sees only the end.
Hook-escape (exception from any hook, including this extension teardown): upstream
builds the result after every teardown unwound, so no teardown saw it; the schema
return seam (schema.py::DjangoSchema._masked_return) masks it under the same gates,
degrading to degraded_result on its own failure. Plain strawberry.Schema with the
extension hand-installed has no return seam, so hook failure there is the stated
uncovered case.

### 2. Definition counts

New error class: 0. The delta introduces no new exception or error type. Both floors
reuse GraphQLError and StrawberryExecutionResult. Hostile shapes in tests
(_HostileError, _HostileResult, raising policies) are test-only senders, not new
production error classes.

Floor change: 1 new shared floor definition plus 3 floor-line conversions plus 1
export. degraded_result is the one new definition (whole-response floor over
_degraded). Three former inline constructions of
StrawberryExecutionResult(data None, errors [_degraded(policy)]) become calls to it:
mask_execution_result outer degrade, DjangoErrorPolicyExtension._process_result
adoption failure, DjangoErrorPolicyExtension.on_operation teardown failure. __all__
gains degraded_result. Net effect is 3 consumers of 1 floor where 3 inline spellings
stood before; _degraded itself is unchanged.

New enforcement seam: 1 new enforcement site, 0 new masking definitions. The schema
return seam (schema.py::DjangoSchema._masked_return with execute and execute twins)
is the new site; it calls the extension owner gates and mask_execution_result and
falls back to degraded_result. It re-states no classification, replacement, floor,
or gate. The extension file documents the third seam and shares the floor but adds
no second masking body. consumers.py::_stop_aware_results call shape is unchanged
apart from prose.

### 3. Owner I would choose

Masking classification, replacement, and floors belong in
django_strawberry_framework/extensions/error_policy.py. Responsibility: response-side
enforcement of ErrorPolicy for every operation, owning what counts as unexpected,
what the safe replacement looks like, what fail-closed publishes, and when masking
applies. Every legitimate consumer (extension teardown, transport per-event source,
schema return) can depend on it without reversing a dependency: the extension module
already imports the root policy, strawberry, graphql-core, and logging, while the
root module owns only the immutable policy object and its construction precedence
and must stay free of engine and transport imports. Root owning masking would force
engine imports into configuration; schema or consumers owning it would force sibling
imports and re-split the three seams. Distinct decisions stay at adapters: per-seam
assignment (in-place adoption vs copy vs return) and per-seam logging stay with the
seam; only the common mechanism (classify, replace, floors, gates) is shared.

### 4. Root-module and code-table interactions

Root module django_strawberry_framework/error_policy.py defines ErrorPolicy,
DEFAULT_ERROR_POLICY, resolve_error_policy, new_correlation_id. It imports from conf,
exceptions, utils.policies only. It imports nothing from extensions.error_policy,
schema, consumers, or mutations. Diff 9031cb3d..bfaee91d for the root path is empty
(confirmed: no output; worktree blob fa94fcd9 equals HEAD blob fa94fcd9).
Changed floor lines live entirely in the extension module and touch only
extension-local _degraded, StrawberryExecutionResult construction, __all__, and
prose. They read policy.message only through the pre-existing _degraded guard; they
introduce no new read of the root module and no new write to it. Dependency direction
is one-way extension consumes root (DEFAULT_ERROR_POLICY, ErrorPolicy,
new_correlation_id). The root does not depend on any changed floor line.
No envelope or code table lives in the root module: the consumer-facing FieldError
envelope and coded rejections (GLOBALID_INVALID, RESOURCE_LIMIT_EXCEEDED, mutation
denial) are produced at their own rejection sites as GraphQLError with
original_error set to a GraphQLError, which is exactly the deliberate branch the
classifier preserves. The delta changes no code value and no envelope shape.

### 5. Breakage assessment

No breakage found in the delta. The three degraded_result call sites are
behavior-preserving rewrites of the inline shapes they replaced (same data None,
same single _degraded entry, same caller-side logging). Idempotence claim verified
against current bytes: teardown-masked errors carry original_error None, the
classifier returns them unchanged, mask_execution_result returns by identity, so the
return seam mints no second id and logs no second record; oracles
test_the_return_seam_passes_an_already_masked_result_through_by_identity and
test_one_hook_failure_produces_exactly_one_masked_entry_and_one_log_record pin this.
Fail-closed direction preserved at every gate: unreadable enabled or DEBUG keeps
masking on; unreadable errors degrade to the floor with data dropped; adoption
failure drops extensions as well. No new leak path: retained path and nodes are
client-document attribution, correlation key is the configured publishable id, and
the floor carries neither. If a defect existed it would need a GOAL.md Trust boundary
contract row (error masked for the right operation; in-band per-field codes travel
as data or deliberate GraphQLError), a feasible project shape under supported public
API, and a wire or configuration input reaching it; no such triple was found.
Concurrent docstring dirt in the worktree (4 insertions, 1 deletion, prose only,
adding the single-hook unification sentence) changes no wire behavior.

### 6. Freshness fingerprints

HEAD bfaee91dcd332a5f86250fff90ab21b377bc674e. Base 9031cb3d.
Delta commit for the extension path ffce6f29.
Worktree extension blob bd763bcc428ce0f495448e6d228061dd0bc08688 differs from HEAD
extension blob 16f475471a8b8295117640f7b14d949603d7bbc0 by prose only (git diff shows
one docstring hunk, 4 insertions 1 deletion, no code hunk). Old extension blob at
9031cb3d baea073f5615aaddc82c1f463071998bee7a6b62.
Root blob worktree and HEAD fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91 (clean).
Schema blob c2e1b748c26c31d944f5a7a12e45b399c81f7ea5.
Consumers blob 936210e2993ddca4b77ffebf65e728f59d17079c.
Package oracle blob tests/test_error_policy.py 9ff5328eaed329a5fd69ac2e7002cf0052452241.
Live oracle blob examples/fakeshop/test_query/test_error_policy_api.py
9a425677bb9763cb05776e0521afa06ad4197307.
Contract sources: AGENTS.md e42247fa310bf7a85914d7efa7f177ee5307b860, GOAL.md
7dfbef5c784519d5f95311aaeb8c6766ee966b02, docs/dry/DRY.md
e8151123ff7e129fe9881ec342231e9e1795148e, docs/dry/worker-2.md
4f089ea4a58d73295638e83abf8c612bf31487f8.
Searched population: full extension module body (all defs and class named in
findings scope), root module body (all 4 public names), schema return seam and
consumers per-event seam bodies, package grep for degraded_result, _degraded,
mask_execution_result, masking_is_active, is_maskable_result, schema_error_policy
across django_strawberry_framework (44 matches in 3 files), both oracle files read
whole (package tier plus live matrix, hook halves, entry spellings). Excluded on body
strength: resource-policy extension (separate gate-before-execution authority),
debug extension (original_error reader ordered before masking), mutation FieldError
envelope (data, never classified). Item-scoped diff on tracked paths left empty by
this phase (artifact append only to untracked docs/dry/dry-file-error_policy.md).


## Bounded re-review at bfaee91d (Worker 2, Q2) -- Phase 2 reconciliation

Scope: Q2 only (floor findings affected by the extension delta). Settled rows
(mint, values, import edge) confirmed unchanged, not re-litigated. No status
changed by this worker. No verdict on anything outside Q2.

### Phase-1 integrity

My phase-1 section `## Bounded re-review at bfaee91d (Worker 2, Q2)` is intact
at the artifact tail (prior file end 890 lines, now 1084 lines before this
append; header plus sections 1-6 present as drafted). It was recorded before
exposure: phase-1 message ended PHASE-1-TRACE-RECORDED without opening the
artifact, and the prior findings (a)/(b)/(c) were first seen in the phase-2
prompt. No prior line touched: `Status: verified`, `Run: 0.0.15 2026-09-18-1`,
F1-F6, R1-R6, J1-J2, Defects, Judgment, Implementation, Independent
verification all byte-untouched by me (artifact remains untracked `??`).

### (a) Split finding -- HOLDS, extended by one floor

Root still mint-only plus values/defaults. Verified at current bytes:
`django_strawberry_framework/error_policy.py` defines exactly ErrorPolicy (3
fields), `__post_init__`, DEFAULT_ERROR_POLICY, resolve_error_policy,
new_correlation_id, `__all__` (4 names). No masking definition here.
Sibling owns all eight prior names plus the new floor: mask_execution_result,
is_maskable_result, masking_is_active, schema_error_policy, _masked,
_degraded, _is_unexpected, on_operation (all present), plus degraded_result
(new shared whole-response floor), plus sub-helpers _replacement_for and
_process_result (also at sibling, also 0 here). Challenges unchanged: C9
(mint format) 1 here; C10 (per-operation vs per-error granularity) 0 here / 1
at owner call placement in _masked; every masking-shape change 0 here.
Import edge still one-way: sibling carries
`from ..error_policy import DEFAULT_ERROR_POLICY, ErrorPolicy,
new_correlation_id` (3 names); root imports nothing from the sibling module
(the `extensions` hits in root are the GraphQL extensions map prose, not a
module import). No cycle possible. The +1 floor definition does not move any
count here: degraded_result is 1 definition at the sibling, 3 conversions at
the sibling, 0 here.

### (b) Trigger -- FIRED and HONORED

Prior trigger: "a third application seam or a classifier change needed in two
places", measured THEN as exactly two seams (teardown + _stop_aware_results).
At bfaee91d there are three: teardown
(extensions/error_policy.py::DjangoErrorPolicyExtension.on_operation via
_process_result), per-event (consumers.py::_stop_aware_results), return
(schema.py::DjangoSchema._masked_return via execute/execute_sync twins). The
mechanism WORKED: the family item
`subscription-per-event-error-masking` opened the firing and is `verified`
(Run 0.0.15 2026-09-19-1) with three seeds listed (teardown, per-event at
consumers.py:1385, return at schema.py:1083), owner
extensions/error_policy.py::mask_execution_result, trigger recorded as
FIRED-as-foretold composing rather than duplicating. Sibling re-traces agree:
File `extensions/error_policy.py` verified re-trace at bfaee91d (F1
FIRED-as-foretold, floor-call census, probe 41 checks ALL OK); File
`schema.py` verified re-trace at bfaee91d (R7 return seam as consumer
composing 4 gates by name). What the ROOT item owes now: NOTHING blocking.
The stale two-seam sentence in this artifact's prior F1 trigger paragraph is
historical measurement, preserved per no-erase rule; the firing is recorded
at the family (and extension re-trace), not here. A future full re-trace may
refresh the prose to three seams; definition counts (0 here) are unaffected,
so no revision is owed.

### (c) Oracles -- STILL PIN THE SPLIT

Spot-checks at current bytes (names verified present, not re-litigated):
tests/test_error_policy.py::test_a_hostile_policy_message_read_degrades_to_the_package_message
pins the per-entry floor surviving a hostile policy; 
tests/test_error_policy.py::test_the_return_seam_passes_an_already_masked_result_through_by_identity
pins third-seam idempotence (identity, no second id/log);
examples/fakeshop/test_query/test_error_policy_api.py::test_an_unexpected_exception_reaches_the_client_as_the_policy_message_only
pins the masked column;
examples/fakeshop/test_query/test_error_policy_api.py::test_an_exception_from_a_consumer_hook_is_masked_like_a_resolver_exception
(pinned over HOOK_ROWS: 4 halves x 2 colors) pins the hook-escape seam the
third site exists for. Projections unchanged in force: both module docstrings
each name the other's half (root "owns the policy object", sibling
enforcement + three-seam account).

### Freshness re-hashed (just now)

Root `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91` worktree == HEAD, unchanged
from prior F1 record. Extension worktree `bd763bcc428ce0f495448e6d228061dd0bc08688`
= HEAD `16f475471a8b8295117640f7b14d949603d7bbc0` + this cycle's ledgered +4/-1
docstring clause (plan `## Owned changes`: Family
subscription-per-event-error-masking module-docstring trigger clause;
`git diff` shows one docstring hunk only, the single-hook unification
sentences, no code hunk). Clause is OUTSIDE the floor findings: it touches
neither degraded_result, _degraded, nor any of the three floor call sites.
Old extension blob at 9031cb3d `baea073f5615aaddc82c1f463071998bee7a6b62`.
Schema `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`, consumers `936210e2`,
package oracle `9ff5328e`, live oracle `9a425677` all match family W2
re-hashes. Searched population for Q2: both bodies whole, package grep for
degraded_result (7 hits: 4 extension + 1 export + 2 schema), import-edge
census, oracle name checks above. Excluded as before: resource-policy,
debug (ordering reader), FieldError envelope (data).

### Verdict

`verified` -- stands at bfaee91d. Carried by: root still mint-only with
one-way import edge; sibling still owns all masking names plus the one new
shared floor with 3 behavior-preserving conversions; third seam composes the
same owner by name with structural idempotence (family + schema re-traces
verified, focused return-seam test passed); cited oracles still pin the
split; zero tracked edits by this re-review.

### Defects

None new. (Worker 2) No defect found in Q2 scope.

### Exact plan rows (for Worker 0; this worker edits no plan)

- `docs/dry/dry-0_0_15.md` File `error_policy.py` tick: from `verified (Run
  0.0.15 2026-09-18-1; zero edits, no pending execution)` to `verified (Run
  0.0.15 2026-09-18-1; bounded re-review Q2 at bfaee91d, zero edits, no
  pending execution)`.
- Responsibility index `subscription-per-event-error-masking` row: stays
  `consolidated`, no change.
- Q2 queue note (`File error_policy (root; extension floors changed)`):
  close as done by this reconciliation.
- `## Owned changes`: no new row (zero tracked edits).

## Run-7 scoped re-trace (Worker-1, REOPENED queue item d2)

Run: 0.0.15 2026-09-29-7. Everything above this section is PRIOR EVIDENCE
ONLY (09-18/19 artifact, `Status: verified` at its stamp, plus the Q2
bounded re-review). This section re-traces the target fresh at HEAD bytes
and issues a CONFIRM or REVISE verdict for every prior finding, with fresh
evidence for each. No consolidation beyond this file item; no production
edits; no plan edits.

### Scope, attribution, fingerprints

Three states fingerprinted, all by blob id over exact bytes:

- Drift base `5ee86193:django_strawberry_framework/error_policy.py` =
  `1a19cd7d9c15964847ae21122b3032d27f60d546`. Worker-0's measurement
  (base bytes == HEAD bytes) VERIFIED independently: identical hash.
- HEAD (`0c0537e2`, unmoved between dispatch and this trace):
  `HEAD:django_strawberry_framework/error_policy.py` = `1a19cd7d…`
  (190 lines). All tracing below is against these bytes.
- Worktree: `57a0bed1ba730f8e4c1f4c879d852274eac39f12` (191 lines).
  `git diff HEAD` shows exactly 2 hunks, 4+/3-: `describe_value` ->
  `truth.describe` (two f-string call sites) plus the import split
  (`from .exceptions import ConfigurationError` /
  `from .utils import truth`). Content-attributed as concurrent-external:
  no `## Owned changes` ledger row names this file (the ledger's only
  error-policy row adopts `extensions/error_policy.py`), and the hunks
  match no cycle-baseline or ledger content. Left untouched.
- Item baseline `f4aff9a777f10e58b509ff107ce470de2c67643e` carries blob
  `57a0bed1` for this path, so the item-scoped diff is empty (0 bytes):
  the dirt predates the item and no stop is owed. This artifact itself is
  untracked (`??`), the only path written.

Delta scoped fresh (`fa94fcd9` prior stamp -> `1a19cd7d` HEAD, blob diff,
six parts, nothing else): (1) module docstring +6 lines (DEFAULT-as-TEMPLATE
paragraph); (2) `canonical_policy` added to the `utils.policies` import;
(3) `ErrorPolicy.__post_init__` docstring expanded with the exact-type
rationale citing `resource_policy.py::_require_positive_int`, and all
three type tests tightened (`not isinstance` -> `type(x) is not <builtin>`);
(4) `DEFAULT_ERROR_POLICY` comment rewritten as template-not-authority
prose; (5) NEW `error_policy.py::_PACKAGE_ERROR_POLICY =
canonical_policy(DEFAULT_ERROR_POLICY, …)` declaration; (6)
`resolve_error_policy` passes `default=_PACKAGE_ERROR_POLICY` instead of
`default=DEFAULT_ERROR_POLICY`. Matches the dispatch record exactly; no
other drift exists between stamp and HEAD for this target.

Freshness fingerprints (HEAD blobs, short; every file actually inspected
this pass): target `1a19cd7d`, `extensions/error_policy.py` `7ee4e9dd`,
`schema.py` `e6b52335`, `consumers.py` `936210e2`, `conf.py` `c6ad46aa`,
`exceptions.py` `e06b0b7f`, `__init__.py` `0ef72601`,
`utils/policies.py` `8c881c0a`, `resource_policy.py` `4b69e974`,
`extensions/debug.py` `bf25c146`, `tests/test_error_policy.py`
`58129ec2`, `test_error_policy_api.py` `20cf3807`, `test_conf.py`
`f35c7074`, `test_init.py` `4cc12105`. Note: `schema.py` reads `e6b52335`
here vs `19f90bf5` in the verified `utils/policies.py` artifact because
HEAD moved (`5ee86193` -> `0c0537e2`); the target's bytes are identical
across that move (verified above) and every `schema.py` cite below was
re-verified at `e6b52335`. The verified File `utils/policies.py` outcome
(`Status: verified`, run 5, HEAD-bytes trace) is cited for the
canonical-copy split: its F1 owns the resolution ladder, its F2
(`policy-authority-isolation`) owns the template/canonical/resolved split
and already names `error_policy.py::_PACKAGE_ERROR_POLICY` as a
declaration.

### Enumeration (fresh, HEAD bytes)

Instrument: `ast.parse` over `git show HEAD:` bytes. **15 top-level
statements** (was 14; +1 is the `_PACKAGE_ERROR_POLICY` assign) plus all
5 `ErrorPolicy`-body members. Every member lands below.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (+ TEMPLATE paragraph) | (none) | projection of R1/R3/F1 owners |
| 2 | `from __future__ import annotations` | annotations | machinery |
| 3 | `import uuid` | `uuid` | machinery for R5 |
| 4 | `from collections.abc import Mapping` | `Mapping` | machinery for R4 |
| 5 | `from dataclasses import dataclass` | `dataclass` | machinery for R1 |
| 6 | `from typing import Any` | `Any` | machinery for R4 |
| 7 | `from .conf import error_policy_setting` | setting reader | consumer edge, R4 |
| 8 | `from .exceptions import ConfigurationError, describe_value` | guard + tail renderer | R2; renderer consumed from open family `typed-rejection-value-tail`, F2 |
| 9 | `from .utils.policies import canonical_policy, resolve_policy` | canonical builder + shared driver | R3/R4 (both owned at `utils/policies.py`) |
| 10 | `__all__ = (…4…)` | leaf manifest | R6, file-local |
| 11 | `class ErrorPolicy` (`@dataclass(frozen=True)`) | policy record | R1/R2 |
| 11.1 | class docstring (unchanged) | (none) | field prose = projection of R1; boundary prose = projection of `schema.py` authority |
| 11.2 | `enabled: bool = True` | masking switch | R1, file-local |
| 11.3 | `message: str = "An unexpected error occurred."` | stable mask text | R1, file-local |
| 11.4 | `correlation_extension_key: str = "correlationId"` | id publish key | R1, file-local |
| 11.5 | `def __post_init__(self)` (exact-type arms + rationale docstring) | domain gate | R2, file-local (REVISEd) |
| 12 | `DEFAULT_ERROR_POLICY = ErrorPolicy()` | value template | R3, file-local (REVISEd: template, not authority) |
| 13 | `_PACKAGE_ERROR_POLICY = canonical_policy(…)` (NEW) | fallback authority | declaration of existing family `policy-authority-isolation` (verified, open) |
| 14 | `def resolve_error_policy(explicit)` (`default=_PACKAGE_ERROR_POLICY`) | resolution ladder | declaration of existing family `schema-construction-policy-ladder` (verified, open); seeds file-local (REVISEd) |
| 15 | `def new_correlation_id()` | id mint | R5, file-local |

### Matrix (re-discharged at HEAD)

1. **Cross-flavor mirroring.** `git grep -l` for
   `ErrorPolicy|error_policy|ERROR_POLICY` over all nine flavor folders
   at HEAD: zero hits (unchanged). Production holders now:
   `error_policy.py` (definitions incl. `_PACKAGE_*`), sibling
   (enforcement, 4 `_PACKAGE_*` code reads + import),
   `schema.py` (import + `_FALLBACK_ENFORCEMENT` + `_masked_return`
   floor), `__init__.py` (re-export), `conf.py` (reader), `utils/policies.py`
   (driver + precedent pointers), `exceptions.py` (scope-docstring line),
   `extensions/debug.py` (precedent pointer), `consumers.py` (seam
   docstring + function-local sibling import). Exactly two `_PACKAGE_*`
   declarations exist package-wide (error + resource, both via
   `canonical_policy`). Axis discharged.
2. **Sync/async twins.** Zero `AsyncFunctionDef`, zero `Await` in HEAD
   bytes (re-verified by AST walk). Import-time canonical copy adds no
   await point. No twin owed. Axis discharged by absence.
3. **Derived knowledge.** Neutral message still spelled once in
   production (field default, line 96); `correlationId` once as a value
   (line 97; second hit is comment prose); `uuid.uuid4().hex` once as
   code (line 190; other two hits are docstring prose). `_PACKAGE_*`
   DERIVES from the template via `canonical_policy` rebuild (reads
   fields, constructs anew) rather than restating values; the resolved
   policy derives again at resolution (no-override arm canonicalizes, per
   verified `utils/policies.py` F1/F2). Chain is template ->
   canonical -> resolved -> handout copies, each step a derivation.
   Axis discharged.
4. **Round-trip pairs.** Still none. Id parse-back sweep at HEAD
   (`parse|decode` near `correlation`): zero hits. `new_correlation_id`
   has exactly one production caller (sibling line 160). Resolution
   still has no inverse. Axis discharged by absence with reason.
5. **Other media.** Structure holds (production / consumers / oracles /
   projections), membership updated: consumers now read `_PACKAGE_*`
   (sibling import line 82, schema import line 83); oracles gained the
   exact-type rows (`test_a_str_subclass_is_rejected_at_construction`,
   `test_a_schema_refuses_a_policy_option_carrying_a_str_subclass`,
   `test_a_str_subclass_cannot_survive_into_the_private_record`,
   `test_a_written_exported_default_reaches_no_resolution`) and the live
   tamper row
   (`test_a_written_exported_default_cannot_unmask_a_later_schema`);
   projections gained the template/canonical docstrings. All oracles
   still spell expectations independently (literals, subclass probes,
   tamper writes); none enumerates the owner. Axis discharged.
6. **Enforcement by omission.** All three fields still gated, now with
   exact-type arms (`type(…) is not bool/str`); every construction path
   still runs the one gate (direct; explicit-instance and mapping via
   driver rebuild; absent via `_PACKAGE_*` default, itself
   canonicalized again on the no-override resolve arm). Deliberate
   omissions unchanged: no `narrowed` counterpart, `{"enabled": False}`
   opt-out, no async twin. Zero enforcement readers of the exported
   template remain (census: only declaration, export, prose, and the
   `_PACKAGE_*` build read `DEFAULT_ERROR_POLICY`). Axis discharged.

### Challenges

C1–C6, C8, C9, C11, C12 still count 1 here (re-verified against HEAD
bodies; C11's debug-bool non-move now contrasts exact-vs-`isinstance`
rather than message-only — see J1). C7 still 0 here / 1 at the driver.
C10 still 0 here / 1 at the sibling (mint's single caller unchanged).
C13 still 0 new (the two new `_PACKAGE_*` readers compose by name).
C14/C15 refusals stand. New-shape challenges: **C16** posit tampering
the exported template (`__dict__` write) → 0 enforcement definitions
move (fallbacks read `_PACKAGE_*`; pinned by the two tamper oracles).
**C17** posit a `str`-subclass message → 1 (the gate rejects; no second
validator exists). **C18** posit a fourth option → still 1
(declaration + gate arm; `_PACKAGE_*` and the unknown-key check derive
via `fields()`). **C19** posit lazy instead of import-time canonical
build → 1 (the declaration site; timing is its own axis, owned there).

### Verdicts on prior findings (fresh evidence each)

- **F1 subscription-per-event masking — REVISE** (family stays open).
  Split holds (configuration here, application at the sibling; one-way
  import edge intact) but the census changed: the sibling now imports
  `_PACKAGE_ERROR_POLICY, ErrorPolicy, new_correlation_id` (line 82;
  `_PACKAGE_*` replaces `DEFAULT_ERROR_POLICY`), and the seam count is
  three at HEAD (teardown `on_operation` line 423, per-event
  `_stop_aware_results` at `consumers.py` lines 1310/1385, return seam
  `_masked_return` at `schema.py` lines 1136/1149/1151) — consistent
  with the Q2 record, superseding the stale two-seam sentence in the
  prior F1 trigger paragraph (preserved above as history).
- **F2 typed-rejection tail — CONFIRM.** `describe_value` census at HEAD
  is still exactly import + two uses (lines 53/116/122); both raises
  route their tails through the renderer; owner unchanged. (The
  worktree `truth.describe` rename is concurrent-external dirt, traced
  at HEAD only; Worker-0 re-fingerprints if it lands.)
- **F3 seal-defect wording — CONFIRM.** The mask is still one stable
  neutral string interpolating nothing (single production spelling,
  line 96); no code enum gained; trigger (shared wire vocabulary)
  unfired.
- **F4 sync-boundary recourse — CONFIRM.** Both rejections still name
  the offending field and stop; no hook/remedy prose added by the
  exact-type change; trigger unfired.
- **F5 logger single-sourcing — CONFIRM.** Zero `getLogger`/`import
  logger` in HEAD bytes (re-counted); still a non-member.
- **F6 patch lifecycle — CONFIRM.** Still no `apply()`, gate read, or
  dependency name; the new import is the sibling-policy driver, not a
  patch target; trigger unfired.
- **R1 record shape + defaults — CONFIRM.** Three fields, same defaults,
  still frozen; class docstring byte-unchanged (absent from the stamp
  diff); C1–C4/C6 counts hold.
- **R2 domain gate — REVISE (stays file-local).** All three arms are now
  exact-type (`type(…) is not …`, lines 114/120) with a rationale
  docstring citing `resource_policy.py::_require_positive_int`; the
  prior `not isinstance` spellings are gone. One gate still guards all
  four construction paths; subclass probes + tamper rows pin it. No
  second validator over these fields exists (searched: only this body
  raises `ErrorPolicy.*must be`).
- **R3 package default — REVISE (stays file-local; new member
  assigned).** `DEFAULT_ERROR_POLICY` is now an exported value TEMPLATE
  (comment prose + module docstring + GLOSSARY, all corroborating);
  enforcement reads the NEW `_PACKAGE_ERROR_POLICY` declaration, which
  is assigned as a declaration of the existing verified family
  `policy-authority-isolation` (its F2 already names this declaration;
  plan index already lists this file). No new family.
- **R4 resolution ladder — REVISE (declaration of existing family).**
  Behavior still the shared driver (C7: 1 at driver, 0 here); the
  declaration now passes `default=_PACKAGE_ERROR_POLICY` with unchanged
  seeds — assigned to existing verified family
  `schema-construction-policy-ladder` (its F1 already names this
  adapter; plan index already lists this file). Seeds + reader edge
  stay file-local.
- **R5 correlation mint — CONFIRM.** Body still `uuid.uuid4().hex`
  (line 190, single code spelling); docstring unchanged; exactly one
  production caller (sibling line 160); granularity still the sibling's
  (C10: 0 here / 1 there).
- **R6 leaf manifest — CONFIRM.** `__all__` still the same four names
  (byte-unchanged); `_PACKAGE_*` deliberately unexported; root
  re-export still `DEFAULT_ERROR_POLICY` + `ErrorPolicy`.
- **J1 shared security-bool helper — REVISE (refusal stands, evidence
  updated).** The recorded strictness difference is gone: this gate now
  matches `resource_policy.py::validate_trusted_flag` (exact `type(…)
  is not bool`, line 1354) and its docstring cites the resource-side
  rationale as precedent. The trio is now two exact + one `not
  isinstance` (`extensions/debug.py` line 693). Refusal still holds:
  per-site danger prose (silent opt-out vs silent widening vs armed
  disclosure), defaults still point different ways (`True` vs none vs
  `False`), and C11 still moves exactly one message. Trigger:
  reworded — a fourth gate arriving with identical rationale AND no
  per-site danger prose (strictness no longer discriminates two of the
  three).
- **J2 error/resource unification — CONFIRM.** The drift EXTENDS the
  recorded symmetry through the same shared driver (`canonical_policy`
  now builds both `_PACKAGE_*` copies; `resource_policy.py` line 457
  mirrors line 145 here); remainder still distinct vocabulary (3
  string/bool options vs numeric bounds + `narrowed`);
  reconsideration trigger (third policy with the identical shape)
  unfired.
- **Q2(a) split — REVISE.** Root still mint-only plus values/defaults
  (now in template + canonical roles); sibling still owns all masking
  names; import census updated to `_PACKAGE_ERROR_POLICY` (three
  names, one way, no cycle). Counts unaffected (0 here for every
  masking-shape change).
- **Q2(b) trigger fired-and-honored — CONFIRM.** Three seams verified
  present at HEAD (cites above); family item verified; nothing owed
  from this file.
- **Q2(c) oracles pin the split — CONFIRM.** All four cited oracle
  names verified present at HEAD (`tests/test_error_policy.py` lines
  784/1119; live API lines 609/1191).

Tally: 11 CONFIRM (F2, F3, F4, F5, F6, R1, R5, R6, J2, Q2b, Q2c),
6 REVISE (F1, R2, R3, R4, J1, Q2a), 0 new families, 0 new index rows
owed (both touched families already index this file).

### Defects

None. Every re-checked claim held at HEAD bytes: template/canonical
prose matches the bodies (zero enforcement readers of the template;
`_PACKAGE_*` built once via the driver); the exact-type gate matches
its rationale docstring and its oracles; the import edge runs one way;
the copy/off-schema boundary prose still matches `schema.py`
(`copy_policy` per read, lines 980/994) and the `_SCHEMA_ENFORCEMENT`
record; granularity prose still matches the sibling's single per-error
call site. The worktree `truth.describe` rename is concurrent-external
dirt outside this trace, not a defect in HEAD bytes. Nothing routed.

### Pending execution

None. All conclusions are static against HEAD bytes (AST enumeration,
blob fingerprints, `git grep` censuses at HEAD); no probe ran, no
pytest ran, no scratch scope created, no source mutated. Sharded and
Postgres cells inapplicable by construction (unchanged: pure dataclass
construction + import-time canonical copy + settings-dict read at
schema construction; no database, alias, or dialect decision).

## Judgment (run-7 re-trace)

Backstop re-discharged at HEAD bytes: 15/15 module members + 5/5 class
members enumerated, matrix re-discharged on all six axes, 15 prior
challenges re-counted + 4 new-shape challenges (C16–C19), every prior
finding CONFIRMed or REVISed with fresh evidence. The drift since the
prior stamp is exactly the recorded canonical-copy split plus
exact-type gates: both converge onto already-verified, already-indexed
families (`policy-authority-isolation` for `_PACKAGE_ERROR_POLICY`,
`schema-construction-policy-ladder` for the resolver), so no new
family, no consolidation, no defect, and no production edit is owed.
Zero-edit result legitimate for a file item.

## Index rows for Worker-0

(Worker-0 alone edits the plan; rows named here for transcription.
No new family is named and no plan-index text changes: both families
the drift touches already list `error_policy.py` under Files covered.)

- CONFIRMed, unchanged text: `subscription-per-event-error-masking`
  (open; F1 revised at artifact level only, family row untouched);
  `typed-rejection-value-tail` (open; consumer census re-verified,
  no file-list change); `seal-defect-code-wording`,
  `sync-boundary-recourse-wording`, `logger-single-sourcing`,
  `upstream-patch-install-lifecycle` (all checked, still non-members);
  J2 error/resource symmetry (refused shared form, trigger unfired).
- REVISEd at artifact level, no transcription owed:
  `policy-authority-isolation` (open; `_PACKAGE_ERROR_POLICY`
  declaration converges onto the verified F2 record, file already
  listed); `schema-construction-policy-ladder` (open;
  `resolve_error_policy` `default=` retarget converges onto the
  verified F1 record, file already listed); R2 exact-type gate + J1
  bool-trio evidence (file-local records, no index rows).
- New rows: none.

## Run-7 verification (Worker-2, REOPENED queue item d2)

Run: 0.0.15 2026-09-29-7. Expectation-first: from the dispatch record
(canonical-copy split + exact-type gates since the prior stamp) I
expected a +1-member enumeration, a template/authority re-homing of R3,
evidence-only revisions to R2/R4/J1/F1, and convergence onto the two
verified policy families — then checked every claim below against HEAD
bytes independently (own `ast.parse`, own `git show HEAD:` censuses, own
blob diff; never W1's probe, never worker-memory).

### 1. Enumeration — STANDS

Own AST run over `git show HEAD:` bytes: **15** `ast.Module.body`
members (docstring, `__future__`, `uuid`, 3 more from-imports, `conf`
reader, `exceptions` guard+renderer, `utils.policies` pair, `__all__`,
class, `DEFAULT_*` assign, `_PACKAGE_*` assign, 2 functions) plus **5**
`ErrorPolicy`-body members (docstring, 3 `AnnAssign`, `__post_init__`).
Row-by-row against W1's table: every member lands, every row has a
member. Zero `AsyncFunctionDef`/`Await`. HEAD is 190 lines, worktree
191.

### 2. Hunk attribution — STANDS (concurrent-external)

`git diff HEAD` shows exactly the 2 claimed hunks
(`describe_value` -> `truth.describe` at two f-string sites + the
import split). Content verdict, independent: `utils/truth.py` is
untracked (`??`, absent from HEAD) with `describe` at line 564
carrying the same `got <kind> <render>` / `an unprintable` tail
contract; worktree `exceptions.py` no longer defines it;
`truth.describe` already spans 11+ worktree files. The hunks are one
mechanical rename inside a package-wide truth-migration. Ledger
check: no `## Owned changes` row names `error_policy.py` or `truth`
(the only error-policy row adopts `extensions/error_policy.py`), and
the hunks match no cycle-baseline content. Left untouched, correctly.
Item baseline `f4aff9a7` carries worktree blob `57a0bed1` for this
path, so the item-scoped diff is 0 bytes: dirt predates the item, no
stop owed.

### 3. Drift scope — STANDS

Blob diff `fa94fcd9` -> `1a19cd7d` contains exactly W1's six parts
(TEMPLATE docstring paragraph; `canonical_policy` import;
`__post_init__` rationale docstring + three exact-type tests; DEFAULT
comment rewrite; new `_PACKAGE_ERROR_POLICY` declaration;
`default=` retarget) and nothing else. Drift base `5ee86193` blob
equals HEAD blob `1a19cd7d` (re-hashed). Class docstring, `__all__`,
mint body absent from the diff, as claimed.

### 4. CONFIRMs — all 11 STAND (spot-probed at HEAD)

F2: `describe_value` census exactly import + 2 uses (lines 53/116/122).
F3: mask string spelled once. F4: both rejections name the field, no
hook/remedy prose. F5: zero `getLogger`. F6: no `apply()`, gate read,
or dependency name. R1: frozen, same three defaults, class docstring
untouched. R5: `uuid4().hex` one code spelling (line 190), exactly one
production caller (sibling line 160). R6: same four `__all__` names;
`_PACKAGE_*` unexported; root re-exports `DEFAULT_ERROR_POLICY` +
`ErrorPolicy`. J2: mirror `_PACKAGE_RESOURCE_POLICY =
canonical_policy(` at `resource_policy.py` line 457; remainder
distinct vocabulary; trigger unfired. Q2b: three seams present at the
cited lines (sibling `on_operation` 423, `consumers.py`
`_stop_aware_results` 1310, `schema.py` `_masked_return`
1136/1149/1151). Q2c: all four oracle `def` names present (1 hit each).
New-shape oracles cited in the matrix (three str-subclass rows, two
tamper rows) all present at HEAD.

### 5. REVISEs — all 6 ENDORSED

- **F1**: sibling import is now `_PACKAGE_*` + 2 names (line 82);
  4 `_PACKAGE_*` code reads (209/295/296/455); three seams. Census-only
  revision, counts unaffected. Endorse.
- **R2**: exact-type arms at HEAD lines 114/120; package-wide only this
  body raises `ErrorPolicy.*must be`. Stays file-local. Endorse.
- **R3**: template prose corroborated (module docstring, comment block,
  GLOSSARY value-template entries); zero enforcement readers of the
  template (only declaration, export, prose, `_PACKAGE_*` build);
  `_PACKAGE_*` declaration converges onto verified
  `policy-authority-isolation` F2. Endorse.
- **R4**: `default=_PACKAGE_ERROR_POLICY`, seeds unchanged, behavior at
  the driver (C7: 0 here); converges onto verified
  `schema-construction-policy-ladder` F1. Endorse.
- **J1**: trio verified at HEAD (here exact, resource exact line 1354,
  debug `not isinstance` line 693); strictness no longer discriminates
  two of three; refusal re-grounded on danger prose + divergent
  defaults + C11 single-move, trigger reworded accordingly. Endorse.
- **Q2a**: root still mint-only plus values/defaults in template +
  canonical roles; import census updated, one way, no cycle. Endorse.

### 6. Family convergence — both STAND

`dry-file-utils__policies.md` is `Status: verified` (run 5). Its F1
names `error_policy.py::resolve_error_policy` as a declaration at
HEAD `1a19cd7d`; its F2 names
`error_policy.py::_PACKAGE_ERROR_POLICY` as a declaration. Plan index
rows `schema-construction-policy-ladder` and
`policy-authority-isolation` both already list `error_policy.py` under
Files covered (re-read at plan lines 365-366). No new family, no
transcription owed.

### 7. "NO plan-index text changes" — STANDS

Follows from §6: both touched families already index this file; the
six REVISEs are artifact-level; no new row is named. Correct call.

### 8. Zero-defect — STANDS

Every re-checked claim held; my own probes found no defect. The
worktree `truth.describe` rename is concurrent-external dirt outside
the HEAD trace, not a defect in these bytes. Nothing routed.

### Freshness, gates, pending, prose

All 14 run-7 fingerprints re-hashed by me against HEAD — every one
matches W1's record (`1a19cd7d`, `7ee4e9dd`, `e6b52335`, `936210e2`,
`c6ad46aa`, `e06b0b7f`, `0ef72601`, `8c881c0a`, `4b69e974`,
`bf25c146`, `58129ec2`, `20cf3807`, `f35c7074`, `4cc12105`).
Item-scoped diff empty (0 bytes); HEAD unmoved at `0c0537e2`
(re-checked after probing). Zero-edit file item: no production edit
demanded or made, no ruff run owed (no tracked `.py` touched), no
pytest run, no pending execution, `inapplicable by construction`
holds for sharded/Postgres cells. Artifact citations use
`path::Symbol`; raw line numbers appear only in this per-cycle
scratchpad context, as allowed. No tracked file touched except this
artifact's `Status:` line and this section; plan edits left to
Worker-0.

### Verdict (Worker-2, run 7)

**Verified.** Backstop re-discharged at HEAD bytes (15/15 + 5/5,
six axes, 15 re-counted + 4 new-shape challenges, 11 CONFIRM + 6
REVISE each with fresh evidence, both drift halves converging onto
already-verified already-indexed families, zero defects).
Zero-edit result legitimate for a file item.
