# Review · Mechanics: `django_strawberry_framework/exceptions.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=c78eb5f150bcd2a5f448a135e078ef58a5594cf4

## Trace

Required reading in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-exceptions.md` (skeleton). Sibling axis records
`docs/review/rev-exceptions.performance.md`,
`docs/review/rev-exceptions.mechanics.md` (this record) and
`docs/review/rev-exceptions.comments.md` did not exist when read
(siblings run concurrently; listing showed only the skeleton); no
Handoff or Cross-axis section exists to absorb yet.

Target read whole (232 lines) at blob `206e9f8d` (live, dirty).
`ITEM_BASELINE` blob for the target equals the live blob (the item
baseline captured the dirty tree); HEAD blob is `e06b0b7f`. HEAD..live
is the concurrent truth-migration: module docstring rewritten
(no-internal-imports to `utils/truth.py`-only plus the deferred-import
note), the seven `_safe_*` helpers and `describe_value` deleted,
`_model_label` / `_terminal_label` added on `truth`, four
function-level `from .utils import truth` imports added, and the
base-class `__str__` / `__repr__` guards removed for standard
`Exception` rendering. Reviewed live as dispatched.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/exceptions/mechanics/inspect/` (json
`docs/review/temp-tests/exceptions/mechanics/exceptions.json`):
5 imports (1 future + 4 deferred `truth`), 11 symbols, 0 hotspots,
2 `getattr` calls of interest. Leads only.

Edges verified by read:

- `django_strawberry_framework/exceptions.py::DjangoStrawberryFrameworkError` —
  base of `ConfigurationError`, `OptimizerError` (this module),
  `ListArgumentError` (`list_field.py:229`), `ResourceLimitExceeded`
  (`resource_policy.py:122`), and transitively `SyncMisuseError`,
  `PathResolutionError`, `LookupValidationError`. Caught nowhere in
  package code (only a docstring mention at `resource_policy.py:130`):
  a consumer catch surface, pinned by
  `tests/test_exceptions.py::test_inheritance_lattice`.
- `django_strawberry_framework/exceptions.py::ConfigurationError` —
  raised across dozens of modules; caught in-package at
  `utils/relations.py:308` (converted to `PathResolutionError`),
  `relay.py:120`, `rest_framework/inputs.py:130,1326,1615`,
  `rest_framework/resolvers.py:1228`.
- `django_strawberry_framework/exceptions.py::PathResolutionError` —
  raised only in `utils/relations.py::classify_path` (6 statements:
  `relations.py:295,305,309,312,315,333`); caught at
  `relations.py:474` (lenient fallback), `filters/sets.py:990`,
  `orders/sets.py:539,723`.
- `django_strawberry_framework/exceptions.py::LookupValidationError` —
  raised only in `utils/relations.py::validate_lookup_expr`
  (6 statements: `relations.py:384,386,390,398,412,413`); caught
  nowhere in package code (a terminal validation failure).
- `django_strawberry_framework/exceptions.py::OptimizerError` —
  12 raise statements in 6 modules
  (`types/resolvers.py:340`; `optimizer/predicates.py:147,161,168`;
  `optimizer/field_meta.py:210,215,250`;
  `optimizer/plans.py:935,941,1066,1242`;
  `utils/connections.py:448,450,502`); caught nowhere in package
  code (deliberately not `ValueError` / `TypeError` so the
  walker's leave-unplanned handler cannot swallow it).
- `django_strawberry_framework/exceptions.py::_model_label` — one
  caller (`PathResolutionError.__init__`);
  `django_strawberry_framework/exceptions.py::_terminal_label` — one
  caller (`LookupValidationError.__init__`).
- The `ConfigurationError` docstring's `SyncMisuseError` paragraph
  verified: `django_strawberry_framework/utils/querysets.py:123`
  multiple-inherits `ConfigurationError` and `RuntimeError`, and the
  root re-exports it (`__init__.py` imports it from `.types` and
  lists it in `__all__`).

Contract sources: `docs/README.md` "Production error policy" and the
"Identity is read from the interpreter" paragraph; the GLOSSARY
`ConfigurationError` anchor; the module, class and function
docstrings; `tests/test_exceptions.py` read whole (lattice,
standard rendering, roundtrips, pinned messages, GraphQL
`located_error`); `django_strawberry_framework/utils/truth.py`
stance docstrings (`render` / `text` propagation rule) at the cited
spans.

Instruments: the trace above; no workspace runs (every behavior read
is oracle-pinned by `tests/test_exceptions.py`; no probe is owed for
a rejection). Cells: default, sharded and pg are all `inapplicable
by construction`: the target reaches no database, alias, or dialect
decision (a pure exception hierarchy plus two message-label builders;
no Django / Strawberry import, no ORM usage), and the cross-axis
Proofs are static greps in the shared tree.

Looks-for discharge (Mechanics floor):

- Rule enforced at a caller instead of its owner: none. The non-str
  guards live at the callers (`classify_path`, `validate_lookup_expr`)
  because the exceptions must render, not reject, the offending value
  (each guard passes it as the segment / part so the message names
  it); validation ownership stays with the classifiers.
- Policy in an adapter, mechanism in a policy layer: none. The module
  is pure mechanism (hierarchy plus message builders); no settings,
  no DEBUG branches, no policy.
- Decision vs contract sources: all match except the three
  enumeration gaps routed to Comments (C1-C3). Each omission sits in
  the owner prose while the body raises the right type (notably
  `_reverse_order_by`'s `OptimizerError`, whose own docstring states
  the not-`ValueError` posture). Lattice, rendering stance,
  bottom-of-graph claim, deferred-import note, and the
  `SyncMisuseError` paragraph each verified against its source.
- Branch no real path reaches: none. Every `__init__` / `__reduce__`
  line and both label branches carry an oracle (the `Book` plus
  `object()` arms in the pinned-message tests; the
  pickle / copy / deepcopy roundtrips); the empty-label `truth.text`
  fallback is a defensive expression sharing R2's trigger.
- Mode flag standing in for a named adapter: none (no flags).
- State owned in two places: none. Message plus structured attributes
  is the specified shape (the tests pin both `str(err)` and
  `err.model` identity); `__reduce__`'s arg tuple is pickle protocol,
  not ownership.
- Dependency pointing the wrong way: none. The only package edge is
  the deferred `truth` import, logically bottom-to-bottom
  (`truth.py` imports stdlib only), documented in the module
  docstring, with no `TYPE_CHECKING` and a clean truthful-reads gate
  (tier-1 0 errors; both `truth: ok` markers inventoried).
- `django.conf.settings` read at import: none (no settings reads at
  all; no import-time work).
- `__all__` disagreeing with the public surface: none. All five names
  defined; both helpers private; HEAD's public-but-unlisted
  `describe_value` is gone with the migration. The root-export
  asymmetry is R4.
- Two sites implementing one rule: R3 (DRY challenges; separate
  reasons to change).
- Sync/async twins that drifted: none (no async surface).
- Guard one flavor has and a sibling lacks: R2 (no contract source
  establishes the rule; gate clean).

Fingerprints (`git hash-object`, live tree):
`django_strawberry_framework/exceptions.py`
`206e9f8d914f640134cf72e374fadeac41d13a39`;
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9`;
`django_strawberry_framework/utils/relations.py`
`05ff55b098382a4a7aafe5a097c3b5e906f8f985`;
`django_strawberry_framework/utils/__init__.py`
`1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee`;
`django_strawberry_framework/optimizer/plans.py`
`33140a766cd3fb2484a40fe499d466c8ced8b4a6`;
`django_strawberry_framework/optimizer/predicates.py`
`4673e81bc65013f5391682fb482bbb07f9c89345`;
`django_strawberry_framework/optimizer/field_meta.py`
`bcddf517b0145be6c06c717d5379e29c271cfea5`;
`django_strawberry_framework/types/resolvers.py`
`640905c63f465db4de16c3a07492b27f3d12d3ad`;
`django_strawberry_framework/utils/connections.py`
`efcf749a26dc7d3fa9b3cc142789a11de2647070`;
`django_strawberry_framework/utils/querysets.py`
`8fc556d582b313e4aed7cddaa15f9a8480d88a46`;
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`tests/test_exceptions.py`
`4b5818c22d24865a38a44e73782b49ee3dc9f94d`;
`docs/README.md`
`30978c34f63a833ffcc0fa11c80b773d241921be`;
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`;
`django_strawberry_framework/filters/sets.py`
`e47c6758e540e0bd9caa8cb90103263b26e905e1` (except-site span only);
`django_strawberry_framework/orders/sets.py`
`60859f2d54525acfdb3dc997d3e931ff3d58d956` (except-site spans only).

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

### R1: Django-shape reads (`_meta.label` / `.name`) live in the bottom module

`django_strawberry_framework/exceptions.py::_model_label` knows a
model carries `_meta.label` and
`django_strawberry_framework/exceptions.py::_terminal_label` knows a
field carries `.name`: Django-shape knowledge in the module whose
docstring claims the bottom of the import graph. Kept in place: the
message is owned by the exception (the structured attributes are the
specified surface — the tests pin `err.model is Book` beside
`str(err)`), the module imports no Django (it reads the shape through
`truth` plus `getattr`, never imports it), and moving the labels to
`utils/relations.py` would either split each message from its
attributes or duplicate the helpers toward the twelve raise sites.
Trigger: a contract source naming the raise-site module as the
message home, or a second label consumer establishing a shared
label-reader rule with a different owner.

### R2: guard asymmetry — `static_attr` vs unguarded `getattr`, no `BaseException` guards

`_model_label` reads `_meta` through `truth.static_attr` (hook-free)
but then `label` through plain `getattr`, and `_terminal_label`
reads `.name` through plain `getattr`; neither guards
`BaseException` (HEAD did both reads under `BaseException` guards
with type-name fallbacks). Not a defect: no contract source requires
hook-free `.name` / `.label` reads (README's identity paragraph
covers class identity — name, module, bases, subclass relations — not
instance attribute reads; the truthful-reads gate reports tier-1 0
errors on the live tree and flags neither line); every
supported-API path hands these constructors framework objects
(`validate_lookup_expr`'s terminal is a `ClassifiedPath.terminal`, a
hostile terminal arriving only through a direct `utils` import outside
the supported surface); and a hostile answer fails loud at definition
time into the error policy rather than silently downgrading. Trigger:
a supported-API path passing a consumer-controlled model or terminal,
a gate flag on either line, or evidence of a silent downgrade.

### R3: DRY twins — the `__init__` pair, the `__reduce__` pair, the label-helper mirror

DRY change challenge. Posit "change `PathResolutionError`'s message
grammar": exactly one definition (its `__init__`); the two
constructors carry different grammars, different label helpers, and
different attribute triples. Posit "drop `vars(self)` state
preservation": two methods, but each follows its own `__init__`
signature, so each changes for its own class's sake — a shared base
`__reduce__` would trade two explicit six-line methods for
introspection or indirection. Posit "change the empty-label fallback":
two helpers, but the sources differ (a two-hop `_meta.label` read on
a model class vs a one-hop `.name` read on a field instance) with
different object kinds and different docstrings. Similar-looking code
with separate reasons to change stays separate. Trigger: a third
exception joining the reduce shape, or the two `__init__` signatures
unifying.

### R4: the hierarchy is module-public but not root-exported (`SyncMisuseError` excepted)

`exceptions.py::__all__` exports five names; the package root
re-exports none of them, while `SyncMisuseError` — defined in the
private `utils/querysets.py` — is root-exported through `.types`.
Not a disagreement: the root surface is curated (pinned by the
`tests/base/test_init.py` export rows), every package import uses the
dotted path (`from ..exceptions import ...` /
`from django_strawberry_framework.exceptions import ...`), and the
`SyncMisuseError` root export exists precisely because its home is
private (its docstring says so), while `exceptions.py` is itself the
public home. Trigger: a consumer contract requiring the root spelling,
or the root gaining one hierarchy member but not its siblings.

## Cross-axis (for Comments)

### C1: `OptimizerError` "Raise sites:" omits `_reverse_order_by`

- Observation: the
  `django_strawberry_framework/exceptions.py::OptimizerError`
  docstring heads its enumeration "Raise sites:" and lists seven
  bullets, but an eighth site raises it:
  `django_strawberry_framework/optimizer/plans.py::_reverse_order_by`
  (`plans.py:1242`), present at HEAD, `ITEM_BASELINE`, and live.
- Evidence: census of 12 raise statements in 6 modules (Trace) groups
  into 8 logical sites; 7 match the 7 bullets one for one (resolver
  strictness; `attach_exists`'s three guards; the `FieldMeta`
  input guards; `window_partition_for_prefetch`'s two arms;
  `apply_window_pagination`'s keyset-plus-reverse arm;
  `assert_window_fetch_mode`; `window_range_plan`'s two arms). Only
  the order-entry-reversal arm is unlisted, and its own docstring
  ("Raises `OptimizerError` for an entry with neither a ...") states
  the behavior the enumeration should index.
- Impact: a maintainer auditing `OptimizerError` handling misses the
  backward-window order-reversal failure; no caller depends on the
  list (the first-line contract is true).
- Severity: Medium — stale-by-omission enumeration on a public
  (`__all__`) symbol; factor: bookkeeping list, first-line contract
  true, no caller dependence.
- Recommendation: add the eighth bullet at the owner (this module's
  `OptimizerError` docstring; contract source: the
  `_reverse_order_by` docstring and body). Owner + contract source as
  required.
- Must not change: no code behavior; prose-only (a `--code-digest`
  identity is owed).
- Proof: `grep -c "_reverse_order_by" django_strawberry_framework/exceptions.py`
  prints `1` (prints `0` now); the `OptimizerError` docstring grades
  true. Static, shared tree; self-contained.
- Freshness: Trace fingerprints cover every file; no additional file.
- Symbol: `django_strawberry_framework/exceptions.py::OptimizerError`
  docstring. Grade: stale (omission). Text before: the seven-bullet
  list ending with the `attach_exists` bullet and closing `"""`.
  Text after: that list plus this eighth bullet before the closing
  `"""`: "- Order-entry reversal:
  `optimizer/plans.py::_reverse_order_by` rejects an order entry with
  neither a `descending` flag nor a callable `desc()`, since a
  backward (`last`-only) window cannot be expressed for it."

### C2: `PathResolutionError` enumeration omits the guard / conversion arms

- Observation: the
  `django_strawberry_framework/exceptions.py::PathResolutionError`
  docstring heads its enumeration "Raise sites (all in
  `utils/relations.py::classify_path`):" and lists four segment
  shapes, but `classify_path` holds six raise statements: the
  non-`str` `field_path` guard (`relations.py:295`, raised before
  segmentation with the whole value as the segment) and the hostile
  `is_relation` conversion (`relations.py:308-309`, where
  `utils/relations.py::relation_bool`'s `ConfigurationError` becomes
  this error) are unlisted. Layout identical at HEAD,
  `ITEM_BASELINE`, and live.
- Evidence: the six-statement census (Trace) against the four-bullet
  list; the location parenthetical ("all in ...") holds — every
  statement is in `classify_path` — only the shape inventory is short.
- Impact: a reader asking "when is this raised?" misses the
  type-guard arm and the malformed-metadata conversion; no caller
  depends on the list (both arms raise the documented type with the
  documented message shape).
- Severity: Medium — stale-by-omission enumeration on a public
  (`__all__`) symbol; factor: bookkeeping list, first-line contract
  true, no caller dependence.
- Recommendation: at the owner (this module's `PathResolutionError`
  docstring; contract source: the `classify_path` body), either add
  the guard-arms bullet (text after) or scope the header to the
  segment-shape inventory it lists; the Comments verifier judges
  which lands, the true grade governing.
- Must not change: no code behavior; prose-only (a `--code-digest`
  identity is owed).
- Proof: `grep -c "relation_bool" django_strawberry_framework/exceptions.py`
  prints `1` (prints `0` now); the `PathResolutionError` docstring
  grades true. Static, shared tree; self-contained.
- Freshness: Trace fingerprints cover every file; no additional file.
- Symbol: `django_strawberry_framework/exceptions.py::PathResolutionError`
  docstring. Grade: stale (omission). Text before: the four-bullet
  list under "Raise sites (all in
  `utils/relations.py::classify_path`):". Text after: that list plus
  this bullet: "- Guard arms the segment list above does not name: a
  `field_path` that is not a `str` (raised before segmentation, naming
  the whole value as the segment), and a segment whose `is_relation`
  flag `utils/relations.py::relation_bool` rejects as malformed
  metadata."

### C3: `LookupValidationError` enumeration omits the guard / conversion arms

- Observation: the
  `django_strawberry_framework/exceptions.py::LookupValidationError`
  docstring heads its enumeration "Raised by
  `utils/relations.py::validate_lookup_expr` when:" and lists three
  bullets, but `validate_lookup_expr` holds six raise statements: the
  non-`str` `lookup_expr` guard (`relations.py:384`, raised before
  splitting) and the Django `FieldError` conversion
  (`relations.py:409-412`, a chain Django refuses, e.g. a transform
  with no output field yet) are unlisted. Layout identical at HEAD,
  `ITEM_BASELINE`, and live.
- Evidence: the six-statement census (Trace) against the three-bullet
  list; bullet one's "empty" covers only `""` (the type guard fires
  first for every non-`str`), and bullets two and three cover
  `None`-returns, not the raised `FieldError`.
- Impact: a reader asking "when is this raised?" misses the
  type-guard arm and the `FieldError` conversion; no caller depends
  on the list (both arms raise the documented type with the
  documented message shape).
- Severity: Medium — stale-by-omission enumeration on a public
  (`__all__`) symbol; factor: bookkeeping list, first-line contract
  true, no caller dependence.
- Recommendation: at the owner (this module's `LookupValidationError`
  docstring; contract source: the `validate_lookup_expr` body),
  either add the guard-arms bullet (text after) or scope the header
  to the resolution-failure inventory it lists; the Comments verifier
  judges which lands, the true grade governing.
- Must not change: no code behavior; prose-only (a `--code-digest`
  identity is owed).
- Proof: `grep -c "FieldError" django_strawberry_framework/exceptions.py`
  prints `1` (prints `0` now); the `LookupValidationError` docstring
  grades true. Static, shared tree; self-contained.
- Freshness: Trace fingerprints cover every file; no additional file.
- Symbol: `django_strawberry_framework/exceptions.py::LookupValidationError`
  docstring. Grade: stale (omission). Text before: the three-bullet
  list under "Raised by
  `utils/relations.py::validate_lookup_expr` when:". Text after: that
  list plus this bullet: "- Guard arms the list above does not name:
  a `lookup_expr` that is not a `str` (raised before splitting), and
  a chain Django refuses with `FieldError` (e.g. a transform applied
  to a bare field with no output field yet), converted to this error."

Handoff: Mechanics review is closed with no own-axis findings, four
rejections, and three Medium cross-axis leads for Comments. Read
beyond the record's trace: the HEAD-vs-live diff to attribute the
concurrent truth-migration (which this pass reviews live, not as a
change), the `relation_bool` / strictness-function / `_reverse_order_by`
spans named above, and the truthful-reads `--report` (tier-1 0 errors;
both `truth: ok` markers inventoried). Considered and dropped without
a rejection entry: the strictness bullet's "covers both" (one
statement, verified reachable through the list, single, and
`connection_to_attr` probe kinds in the one function — true);
`FieldMeta`'s two non-`str`-name arms against bullet one's
"(missing name / is_relation)" parenthetical (the head, "not a Django
field descriptor", covers them — true). The judgment call most likely
to be revisited is C2/C3's framing (guard arms vs segment-shape
inventory): the text-after and the header-scoping alternative are both
on record so the Comments pass can take either. Concurrent-work note
(not a finding on this item): the in-flight spec's citation of the
deleted `describe_value` helper no longer resolves live (the migration
removed it from `django_strawberry_framework/exceptions.py` in favor of
`django_strawberry_framework/utils/truth.py::describe`); renaming sweeps
belong to the migration change, flagged here only so Worker-0 is not
surprised. Open threads: none. Cells default / sharded / pg all
inapplicable by construction (reason in Trace); cells unverified: none.

## Verification (Mechanics)

Pass 1, address `review/exceptions.py/verify-mechanics-1`, scratch
`docs/review/temp-tests/exceptions/verify-mechanics-1/` (created;
holds no files — every instrument below is a static shared-tree
command except the one workspace attack run, whose log lives in the
flow evidence folder). Item diff
`docs/review/temp-tests/exceptions/diff/pass-1.diff`.

Step 1 — tree still carries the sent change: `git diff
c78eb5f150bcd2a5f448a135e078ef58a5594cf4 --
django_strawberry_framework/exceptions.py tests/test_exceptions.py`
hashes equal to `pass-1.diff` (sha256 `f2acd1ef...451d256`
both sides, `cmp` HASH_EQUAL; HEAD `0c0537e2dd94` unmoved).
Grade proceeds.

Proofs run verbatim before reading `## Implementation (Worker-2)`:
none in-axis — state so. This record's three Proof lines sit
under `## Cross-axis (for Comments)` (C1 `_reverse_order_by`, C2
`relation_bool`, C3 `FieldError`) and are graded by the Comments
verifier, not here; this record's own Findings are High/Medium/Low
all `None`, so zero in-axis Proofs are owed. The Performance
record holds no `## Cross-axis` section and no Proof line; the
Comments record holds four Proofs, all own-axis, and no
`## Cross-axis` section. No other record holds a Proof for
Mechanics. No workspace run owed for this step; none made.

Behavior preservation: code-digest identity, both files exit 0
with equal digest pairs, matching the digests Worker-2 reported:
`django_strawberry_framework/exceptions.py`
`sha256:2c01d220...8b8d10` both sides;
`tests/test_exceptions.py` `sha256:bdbf204b...4714c5`
both sides. A revert proof is vacuous with no production hunk —
state so: the item diff holds seven docstring hunks only (target:
M1 paragraph, C2 bullet, L2 sentence, C3 bullet, C1/L1 bullet
plus the `fallback` fix; tests: M2 docstring), and a scan of
every added/removed line for `import`, `__all__`, `def`,
`class` returns zero matches. No `prove` manifest owed
(prose-only owes no failability).

Whole-diff reading through the Mechanics axis: no placement,
dependency, state-ownership, duplication, twin, guard, or
`__all__` consequence. Imports untouched (the four deferred
`truth` imports and the `__all__` list byte-identical); no
symbol moved, renamed, added, or deleted, so no `--cited-by`
sweep owed. The two new prose citations (`_reverse_order_by`,
`relation_bool`) are doc text creating no import edge; the
tree-wide citation gate below confirms they resolve. The landed
prose's truth is the Comments verifier's grade, not this axis's;
nothing in the diff moves a rule, a boundary, or a contract the
Mechanics looks-for list owns.

Attacks on the Mechanics axis, all passing:

- A1 (no-code corroboration): the diff keyword scan above plus
  the digest identity — no executable line reachable.
- A2 (hierarchy and messages intact, at the verify address):
  `uv run python scripts/workspace.py run
  review/exceptions.py/verify-mechanics-1 -- pytest
  tests/test_exceptions.py::test_inheritance_lattice
  tests/test_exceptions.py::test_path_resolution_error_message_is_pinned
  tests/test_exceptions.py::test_lookup_validation_error_message_is_pinned
  --no-cov -q` → run `review-20260929T044123-bfefff`, exit 0,
  3 passed, copy fresh, shared unmoved. The lattice pin and
  both message pins hold on the changed tree.
- A3 (fingerprint match): live `git hash-object` gives
  `93401220...aa0bd` (target) and `1374fef5...ae07f`
  (tests), identical to the fingerprints Worker-2 reported
  after its pass — no drift between implement and verify.

Disputes: none recorded — nothing to judge. The artifact
states "No finding disputed, discharged, or deferred" and the
word appears nowhere else in it; no `disputed:` marker exists.

Test tier: none owed — prose-only change (REVIEW.md Comments:
no before/after, no permanent test, no failability). The A2 run
above exercises existing oracle pins as an attack, not a relied-on
gate.

Lint gates (`--check` forms only), all green:

- `uv run ruff check django_strawberry_framework/exceptions.py
  tests/test_exceptions.py` → exit 0, All checks passed.
- `uv run ruff format --check <same two paths>` → exit 0,
  2 files already formatted (plus the standing COM812
  formatter-conflict warning, a config note, not a failure).
- `uv run python scripts/check_trailing_commas.py --check <same
  two paths>` → exit 0, 0 violations.
- `uv run python scripts/check_citations.py --check` (tree-wide)
  → exit 0, OK: 1299 citations resolve.

Cells: default, sharded, and pg all inapplicable by
construction (record Trace reason stands: pure exception
hierarchy plus message-label builders; no database, alias, or
dialect decision; the diff is prose-only). Cells unverified:
none. No new finding on any axis; no gap to route.

Handoff: Mechanics verification is closed `verified` with zero
in-axis Proofs (none owed), digest identity on both files, one
passing workspace attack (`review-20260929T044123-bfefff`),
zero disputes, and four green lint gates. Read beyond the
records: the full item diff (seven prose hunks), the `##
Implementation (Worker-2)` report after the proof step, and the
live test node list for the A2 attack. Nothing in this pass
revisits the review judgments (R1-R4 rejections stand; C1-C3
framing is the Comments verifier's call). Open threads: none.
