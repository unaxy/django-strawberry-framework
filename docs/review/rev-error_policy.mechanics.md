# Review · Mechanics: `django_strawberry_framework/error_policy.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=59dad4a566f3718e6d99572ef853455d0aabc101

## Trace

Required reading in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-error_policy.md` (skeleton). Sibling axis records
`docs/review/rev-error_policy.performance.md`,
`docs/review/rev-error_policy.mechanics.md` (this record) and
`docs/review/rev-error_policy.comments.md` did not exist when read
(siblings run concurrently); no Handoff or Cross-axis section exists
to absorb yet.

Target read whole (191 lines) at blob `57a0bed1` (live, dirty).
`ITEM_BASELINE` blob for the target equals the live blob (the item
baseline captured the dirty tree); HEAD blob is `1a19cd7d`. HEAD..live
is the concurrent truth-migration (`describe_value` to
`django_strawberry_framework/utils/truth.py::describe` in the two
rejection messages plus the import swap, 4 insertions / 3 deletions),
whose message shape the committed oracle still pins byte for byte.
Reviewed live as dispatched.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/error_policy/mechanics/inspect/` (json
`docs/review/temp-tests/error_policy/mechanics/error_policy.json`):
5 top-level symbols, 0 Django/ORM markers, 2 import-time calls
(`ErrorPolicy()`, `canonical_policy`). Leads only.

Consumer edges verified by read (every masking fallback reads the
owner's canonical object; the exported template is read by no
production seam):

- `django_strawberry_framework/error_policy.py::resolve_error_policy` —
  `django_strawberry_framework/schema.py::DjangoSchema.__init__`
  (`schema.py:862`), once per construction; the shared ladder in
  `django_strawberry_framework/utils/policies.py::resolve_policy`.
- `django_strawberry_framework/error_policy.py::ErrorPolicy` — the
  `error_policy` annotation on
  `django_strawberry_framework/schema.py::DjangoSchema.__init__` and the
  `error_policy` / `resource_policy` property pair (`schema.py:507`,
  `schema.py:847`, `schema.py:985`); the exact-type gates in
  `django_strawberry_framework/extensions/error_policy.py::schema_error_policy`
  and the masking signatures there; root re-export in
  `django_strawberry_framework/__init__.py`.
- `django_strawberry_framework/error_policy.py::new_correlation_id` —
  one production call site,
  `django_strawberry_framework/extensions/error_policy.py::_masked`
  (`extensions/error_policy.py:165`), per masked error.
- `django_strawberry_framework/error_policy.py::_PACKAGE_ERROR_POLICY` —
  `django_strawberry_framework/schema.py::_FALLBACK_ENFORCEMENT`
  (`schema.py:568`) and
  `django_strawberry_framework/extensions/error_policy.py::schema_error_policy`
  (`extensions/error_policy.py:276`); the `default` argument of the
  resolver. Reachable from no exported name.
- `django_strawberry_framework/error_policy.py::DEFAULT_ERROR_POLICY` —
  read by no production seam: the package matches are the
  `django_strawberry_framework/__init__.py` re-export and the module's
  own comments; every other match is a test comparison value. The
  module docstring's "Nothing in the package reads this name" holds
  for masking reads.

Contract sources: `docs/README.md` "Production error policy" (wire
table, DEBUG pass-through, configuration ladder, opt-out);
GLOSSARY `ErrorPolicy` and production-error-policy anchors; the module,
class and function docstrings; `tests/test_error_policy.py` read whole
(construction, ladder, correlation id, install position oracles);
spec-048 (file table, Decisions 7-9, `__post_init__`-as-only-gate and
single-application invariants) at grep level for orientation;
DRY `dry-file-error_policy.md` at grep level (nothing imported as a
finding).

Instruments: the trace above; one workspace probe,
`docs/review/temp-tests/error_policy/mechanics/probe_hostile_values.py`
(copied into the copy as `tests/test_mech_probe_error_policy.py`), run
`review-20260929T031451-c0ab21` (address
`review/error_policy.py/mechanics`, cell default, package digest
`sha256:c8c864951ee13077f2aff5343d8247e4b67358622e379772a1e20fdcfe3a5af2`),
`4 passed`.

Cells: default probed. Sharded and pg are `inapplicable by
construction`: the target reaches no database, alias, or dialect
decision (pure in-memory dataclass validation and policy resolution;
no ORM import or usage), and the probe asserts pure-Python
construction outcomes.

Looks-for discharge (Mechanics floor):

- Rule enforced at a caller instead of its owner: none. Domain
  validation lives in
  `django_strawberry_framework/error_policy.py::ErrorPolicy.__post_init__`
  (the owner; spec-048's only-gate invariant); the precedence ladder,
  unknown-key and shape rejections live in the shared
  `django_strawberry_framework/utils/policies.py::resolve_policy`
  driver both twins delegate to by spec; every masking fallback reads
  `_PACKAGE_ERROR_POLICY`, never a caller-side restatement.
- Policy in an adapter, mechanism in a policy layer: none beyond R1.
  The module is pure policy (record, resolution, id primitive);
  enforcement lives in
  `django_strawberry_framework/extensions/error_policy.py`.
- Decision vs contract sources: all match. README wire table, DEBUG
  pass-through, ladder and opt-out; GLOSSARY field defaults,
  exact-type rule, ladder, thin-reader split. The one prose
  divergence (GLOSSARY's "frozen, so a resolver holding it cannot
  loosen" reason, which the class docstring explicitly refutes) is a
  wrong stated reason in a standing doc, not a target behavior; see
  the Handoff's Routed lead.
- Branch no real path reaches: none. Both `__post_init__` arms,
  the empty-string leg, the ladder's instance / mapping / absent /
  rejection legs, and the id format each carry a committed oracle;
  the import-time canonical copy executes on every import.
- Mode flag standing in for a named adapter: none. `enabled` is the
  specified on/off switch with exact-`bool` validation; no adapters
  hide behind it.
- State owned in two places: none. The exported template vs the
  canonical copy is the specified authority separation, pinned by
  `tests/test_error_policy.py::test_a_written_exported_default_reaches_no_resolution`;
  one write to the export reaches no resolution.
- Dependency pointing the wrong way: none. The module depends on
  `conf` (one reader), `exceptions`, and the `utils` leaves
  (`truth`, `policies`); none of them imports this module back
  (conf's mentions are docstring citations); no `TYPE_CHECKING`.
- `django.conf.settings` read at import: none. Import builds the
  canonical copy from literal defaults; the setting is read only
  inside resolution at schema construction.
- `__all__` disagreeing with the public surface: none. All four
  names defined; the root re-exports exactly the two policy values
  (R4), symmetric with the resource twin.
- Two sites implementing one rule: R3 (DRY challenge, count 1).
- Sync/async twins that drifted: none (no async surface; the
  extension module documents one shared masking path).
- Guard one flavor has and a sibling lacks: none standing. The
  historical hunt lead (unguarded `isinstance` on policy values at
  construction) is closed on this file by the exact-type tests;
  probe rows 1-3 prove a hostile `__class__` still answers the
  typed `ConfigurationError` through construction and the mapping
  ladder. The hostile-render variant is R2.

Fingerprints (`git hash-object`, live tree):
`django_strawberry_framework/error_policy.py`
`57a0bed1ba730f8e4c1f4c879d852274eac39f12`;
`django_strawberry_framework/utils/policies.py`
`0a2b7dbad96594b5d668774218809c6a94d136be`;
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9`;
`django_strawberry_framework/extensions/error_policy.py`
`a1defd394d8eda9b698964030a09efe6914278db`;
`django_strawberry_framework/schema.py`
`84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1`;
`django_strawberry_framework/conf.py`
`3820c575bfd4e3c384244d1bed460b75d3bb7681`;
`django_strawberry_framework/resource_policy.py`
`cc3f9d80b9d55af8b725a77c73aba3d8110e0037`;
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`tests/test_error_policy.py`
`0f0fec24b03ca8472f224cc7cefc3b6062f147bb`;
`docs/README.md`
`30978c34f63a833ffcc0fa11c80b773d241921be`;
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

### R1: `new_correlation_id` sits in the policy module while its only consumer is the extension

`django_strawberry_framework/error_policy.py::new_correlation_id` is
called from exactly one production site,
`django_strawberry_framework/extensions/error_policy.py::_masked`,
and spec-048's file table attributes "the correlation id" to
`extensions/error_policy.py`. Kept in place: the spec row is a
coarse behavior inventory (it names no other function in that
module either, and the per-masked-error minting behavior does live
in the extension's `_masked`), while the primitive itself is public
dotted-path API in the module `__all__`, its 32-lowercase-hex format
is part of the policy's wire contract pinned by
`tests/test_error_policy.py::test_a_correlation_id_is_thirty_two_lowercase_hex_characters`,
and the DRY pass traced this file without a placement challenge.
Moving it would break the dotted import for no contract gain.
Trigger: a contract source naming the extension module as the
function's home, or a second consumer establishing a shared-printer
rule with a different owner.

### R2: a hostile-`__repr__` config value propagates raw instead of the typed rejection

`ErrorPolicy(message=<object whose __repr__ raises>)` raises that
raw `RuntimeError` out of
`django_strawberry_framework/error_policy.py::ErrorPolicy.__post_init__`
rather than `ConfigurationError` (probe row 4,
`review-20260929T031451-c0ab21`): `truth.describe` renders
non-scalars through their own `__repr__` by documented stance
(`django_strawberry_framework/utils/truth.py::render`: "whatever it
raises propagates"). Not a defect: the failure is loud and at
startup (fail-closed; no disclosure, no masking bypass — the schema
never serves), the exact-type machinery's threat is consumer code
running on the wire path at masking time rather than a hostile
render in the deployment's own configuration, and containing it
here alone would be whack-a-mole against a package-wide documented
rendering rule owned by `utils/truth.py`. Trigger: a contract
source requiring typed rejection of hostile-render config values,
or evidence the raw error escapes startup into serving.

### R3: `ErrorPolicy` / `ResourcePolicy` records and resolvers mirror each other

DRY change challenge. Posit "change the error-policy fields":
exactly one definition
(`django_strawberry_framework/error_policy.py::ErrorPolicy`).
Posit "change the resolution ladder": exactly one definition
(`django_strawberry_framework/utils/policies.py::resolve_policy`,
which both resolvers delegate to). Posit "change the no-override
guarantee": the one driver docstring plus its two one-line
callers. The two resolvers are declarative parameterizations
(`policy_cls`, `default`, `read_setting`, `display_name`, `unit`)
over one shared contract, and the records carry distinct
vocabularies (switch/message/key vs bounds) with distinct reasons
to change — the GLOSSARY "one policy-object idiom" anchor pins the
mirroring as deliberate. Not duplication. Trigger: a third policy
whose resolver cannot be expressed as the same parameterization,
or a ladder behavior change landing in one twin but not the other.

### R4: the resolvers and `new_correlation_id` are module-public but not root-exported

`django_strawberry_framework/error_policy.py::__all__` exports four
names; the package root re-exports two (`ErrorPolicy`,
`DEFAULT_ERROR_POLICY`). Not a disagreement: the root surface is
curated (pinned by the `tests/base/test_init.py` export rows), the
resolver twin `resolve_resource_policy` is likewise absent from the
root, and construction-time helpers stay on the dotted path by the
same rule that keeps `canonical_policy` out of it. Trigger: a
consumer contract requiring the root spelling, or one twin's
resolver root-exported while the other is not.

Handoff: Mechanics review is closed with no findings and four
rejections. Read beyond the record's trace: spec-048 and DRY
`dry-file-error_policy.md` at grep level only (orientation; nothing
imported), `tests/test_error_policy.py` whole, the extension,
schema-fallback, shared-driver, truth, conf-reader and
resource-twin neighbors whole at the cited spans, and the
HEAD-vs-live diff to attribute the concurrent truth-migration
(which the probe deliberately exercises through the live
`truth.describe` spelling). The judgment call most likely to be
revisited is R2's direction (documented propagation over a local
containment): containment in this file alone would leave every
other rejection message in the package on the same documented
behavior, so the trigger names the only consistent fix site.
Routed lead for Worker-0 (not a finding on this item; the target
body is correct): GLOSSARY `ErrorPolicy` anchor,
`docs/GLOSSARY.md:843` ("it is **frozen**, so a resolver holding it
cannot loosen its own request's policy") states the wrong reason
for a true outcome — the class docstring
(`django_strawberry_framework/error_policy.py::ErrorPolicy`,
"Frozen is not what establishes that") and the copy-per-read plus
off-schema-record machinery establish it instead. Suggested home:
plan `## Decisions` beside the other routed prose observations;
the fix is a glossary-DB edit plus render, outside this item's
fence. Open threads: none. Cells sharded/pg inapplicable by
construction (reason in Trace).

## Verification (Mechanics)

Verify step 1: `git diff 59dad4a5 -- tests/test_error_policy.py
examples/fakeshop/test_query/test_error_policy_api.py` hashes equal
to `docs/review/temp-tests/error_policy/diff/pass-1.diff`
(sha256 `364ed475...01b2a` both sides, `diff` empty). The tree did
not move under the pass.

Proof lines: none exist to run. This record is no-findings and
carries no Proof line; the Performance record is no-findings; the
Comments record carries no `## Cross-axis` section and its Handoff
states "No Cross-axis findings: nothing in this pass belongs to
Performance or Mechanics". No record holds a `## Cross-axis (for
Mechanics)` section. Stated, nothing run verbatim.

Numbers reproduced (address `review/error_policy.py/verify-mechanics-1`,
cell default): `tests/test_error_policy.py` 66 passed
(`review-20260929T040324-fe5a57`); live module 74 passed
(`review-20260929T040347-b19545`); the renamed node collected
exactly once, 1 passed
(`review-20260929T040445-f4d966`). The `before` copy reports the
same package module 66 passed
(`review-20260929T040329-a77fdf`): the rename is
collection-neutral, verdict-neutral. Worker-2's 66+74 evidence
holds, independently re-run.

Behavior preservation, independently rebuilt: own reconstructions
under `docs/review/temp-tests/error_policy/verify-mechanics-1/`
(ITEM_BASELINE text plus only the `def` rename /
`recon_rename_only.py`, plus only the assert line /
`recon_assert_only.py`, each transformation asserted to hit
exactly once) give `--code-digest` exit 0 against the live files
with digests identical to Worker-2's (`e3e57697...`,
`9a19bd5e...`); whole-file digests exit 1 with baseline digests
identical to Worker-2's (`d6861ddb...`, `a5b4beed...`). Exactly
two AST-significant lines changed; all nine prose hunks moved no
code. The target is absent from the item diff
(`git diff 59dad4a5 -- django_strawberry_framework/error_policy.py`
empty, blob still `57a0bed1`).

Failability (`workspace.py prove`, same address): reverting the
M4 assert hunk fails 0 rows and reverting the M1 rename hunk
fails 0 rows (`review-20260929T040537-89fae8`, both entries
`expect_failing: []` met, restores byte-proved) - the change is
additive-only tightening plus a neutral rename. Attack: a
smuggled `"code"` key in
`django_strawberry_framework/extensions/error_policy.py::_masked`
fails exactly the one declared live row, crashing at the new
assert (`review-20260929T040718-dad262`, `pinned`, crash
`test_error_policy_api.py:598: assert {'code', 'correlationId'} ==
{'correlationId'}`) - the added gate is live, and the crash line
is the assert, not an earlier row.

Whole-diff read (11 hunks, 2 files, target absent): 9 prose-only
hunks (Comments verifier's grades, not regraded here), the M1
rename, the M4 assert. Census correction: `_masked_error(` has
13 call sites, not the 12 Worker-2 reports (def at live-module
line 584 plus calls at 627, 653, 668, 683, 948, 958, 997, 1006,
1037, 1091, 1212, 1231, 1355; 12 in test bodies, the 1091st inside
`_assert_masked_and_clean`, itself called by 2 collected tests).
`key=` appears only on the `def` line, so all 13 use the default
key, and the 74-passed / 0-skipped suite executes every one
green. The miscount is report accuracy only: no verdict, tier, or
behavior claim depends on the number. The assert reads only
`error["extensions"]` (already fetched above) and the in-scope
`key`, and is consistent with the read above it under any key
spelling; set equality is deterministic, no order dependence.

Renamed symbol: `--cited-by` reports 0 citing sites for the old
and the new node id across 550 files; repo-wide grep finds the
old name only in the two per-cycle review records' prose and
Worker-2's scratch reconstruction (both exempt artifacts), the
new name only on its `def` line plus the scratch twin. No
standing doc or code citer rots.

Tiers (AGENTS.md): the M4 assert sits in the live tier, correct -
the masked extensions shape is wire behavior reachable from a
real query; the M1 rename sits in the package tier, correct -
frozen/construction behavior is unreachable from a real query.
No tier violation; no finding moved tiers.

Disputes: none recorded (Worker-2: zero disputes). The M5
build-then-flip row Worker-2 deliberately did not add was
explicitly "not required by this Proof" in the finding's own
terms - a judgment call inside the fence, not a dispute; concur,
and it has no Mechanics impact either way.

Lint gates (`--check` forms only): `ruff check` on both touched
paths passes; `ruff format --check` on both passes (already
formatted); `check_trailing_commas.py --check` on both passes (0
violations); `check_citations.py --check` tree-wide passes (1297
citations resolve, matching Worker-2's count).

Cells: default verified above. Sharded and pg remain
`inapplicable by construction`: the change is test-only, the
target reaches no database, alias, or dialect decision (reason in
Trace, concurred), and no hunk adds DB reach. Cells unverified:
none.

New findings: none. Rejections R1-R4 and the glossary Routed
lead stand untouched (no hunk bears on any of them).

Fingerprints (`git hash-object`, post-verify):
`tests/test_error_policy.py`
`9a72cdb83d4739be4018a3c58d0bf2736b63f569`;
`examples/fakeshop/test_query/test_error_policy_api.py`
`071b113feeaf9cee30ccda5941614c423251459c`;
`django_strawberry_framework/error_policy.py`
`57a0bed1ba730f8e4c1f4c879d852274eac39f12` - all three match
Worker-2's post-edit values, so nothing drifted after the pass.

Handoff: Mechanics verification is closed, `Status: verified`.
The one correction for Worker-0's plan line is the call-site
count (13, all default-key, all executed green - evidence above,
not a gap). Read beyond this section's trace: the live target
whole (unchanged, matches review fingerprints), the `_masked`
builder for the smuggle anchor (unique `extensions={` site),
and the `_masked_error` helper plus all 13 call scopes. Open
threads: none. The Comments verifier owns the prose grades; the
M1 docstring's generalized second sentence and the M5 text-after
were deliberately not graded here.
