# DRY review: `list-argument-supplied-spelling`

Status: verified
Run: 0.0.15 2026-10-01-12

## System trace

The rule under review: a schema-layer argument counts supplied unless it is
`None` or the `UNSET` sentinel — the package's one active-input rule. Two
candidate definitions were nominated and re-derived fresh at current bytes:

1. `django_strawberry_framework/utils/input_values.py::is_inactive_value`
   (the parameterized rule) with its
   `django_strawberry_framework/utils/connections.py::is_supplied` binding
   (`unset_sentinel=strawberry.UNSET`), one composed definition.
2. The x3 hand-spelling
   (`x is not None and x is not strawberry.UNSET`) in
   `django_strawberry_framework/list_field.py::_normalize_list_arguments`.

Complete reads: `list_field.py` (1789 lines, all `is None` sites
classified), `utils/input_values.py` (all), `utils/connections.py` (all).
Whole-package sweep instruments, all over 120 `.py` files:

- `rg` for `strawberry.UNSET` / `UNSET`: per-file census; every hit
  classified as default, prose, composed call, distinct sentinel, or
  comparison.
- `rg` for `is not None and ... UNSET` (both orders), `is UNSET`,
  `is not UNSET`, `== UNSET`, `!= UNSET`, `UNSET is`, membership forms:
  code hits only the x3 block plus one docstring mention.
- AST census for `Compare` nodes with an UNSET operand: exactly 5 nodes
  pre-change — the x3 block, `utils/inputs.py:1308`, and
  `types/finalizer.py:877`. No multi-line or alternate spelling exists.
- `rg` for `is_supplied\(` / `is_inactive_value\(`: 1 + 13 call sites
  pre-change for the binding (5 internal to `utils/connections.py`, 8 in
  `connection.py`), 1 + 19 for the rule (3 `filters/inputs.py`, 10
  `filters/sets.py`, 3 internal, 1 the binding, 1 `utils/permissions.py`,
  1 `sets_mixins.py`).
- Import-closure check for the `list_field` -> `utils/connections` edge:
  only `__init__.py`, `connection.py`, `relay.py` import `list_field`;
  the closure (`conf`, `exceptions`, `utils/*`, stdlib, django,
  strawberry, graphql) imports no root module at runtime. No cycle.
- Dirt attribution by diff content vs `git show HEAD:<path>`: the x3
  lines are byte-identical across HEAD / baseline / pre-edit WT (only
  the line numbers moved); the `is_inactive_value` body is unchanged
  in its dirty file; `utils/connections.py` is HEAD-clean.

Connected behavior examined: the normalizer's `None`-mapping (inactive
maps to `None`, so every downstream `is None` read is correct by
construction), all three resolver wrappers (pass-through, no
pre-checks), the sync/async pipelines (consume the record only),
`OrderSet._input_has_active_terms` (separate active-terms rule, family
`active-terms-purity-agreement`), the write-flavor provided walk, the
keyset/offset window derivations, and the existing oracles
(`tests/test_list_field.py` supplied rows, 100 live list-field tests).

## Verification

### Matrix

1. **Cross-flavor mirroring** — searched. Read surfaces compose the
   owner (filters, orders, permissions via `is_inactive_value`;
   connections via `is_supplied`); write surfaces (mutations, forms,
   serializers) go through the distinct provided walk (R1). The list
   surface was the only read surface hand-spelling. No second copy.
2. **Sync/async twins** — inapplicable with reason. `_normalize_list_arguments`
   is a pure sync function; both pipeline colorings consume its record
   through the shared `_argument_record`. There is no async twin to drift.
3. **Derived knowledge** — searched. The supplied flags are re-stated,
   not derived — that is the finding. The `norm_*` mapping derives from
   the flags (not a second statement of the rule).
4. **Inverse / round-trip pairs** — searched. `is_supplied` is the
   negation of `is_inactive_value` composed by call
   (`utils/connections.py:140`), one definition. No raw
   `is None or ... UNSET` spelling exists (AST census). The UNSET-only
   check at `utils/inputs.py:1308` is the distinct provided rule (R1),
   not an inverse half.
5. **Contracts in another medium** — searched. Oracles:
   `tests/test_list_field.py` supplied rows (plus the new UNSET-arm
   test); live `test_list_field_api.py` / `test_list_field_async_api.py`.
   Projections: the `is_supplied` docstring (single-rule claim, holds),
   the `input_values.py` module docstring, the `utils/__init__.py`
   ownership note. The `_normalize_list_arguments` docstring states no
   supplied rule, so no prose moves with the change.
6. **Enforcement by omission** — searched. Family enumerated: filter
   normalizer, order normalizer, permission walkers, connection
   surfaces, list normalizer. Every member either composes the owner
   or (list) is the finding. Write flavors and cursor presence are
   excluded by contract sources (R1, R4), not by silence. No axis-6
   defect: no member lacks a guard its contract requires.

### Enumeration

Instrument: the `rg` + AST censuses above over
`django_strawberry_framework/` (120 files). Every UNSET-adjacent member
homes below; nothing unassigned.

| # | Member | Home |
|---|---|---|
| 1 | `is_inactive_value` rule body | F1 owner |
| 2 | `is_supplied` UNSET binding | F1 owner |
| 3 | x3 hand-spelling, `_normalize_list_arguments` | F1 consolidated |
| 4 | 19 `is_inactive_value` call sites | F1 consumers |
| 5 | 13 `is_supplied` call sites (16 post-change) | F1 consumers |
| 6 | `utils/inputs.py:1308` UNSET-only check | R1 separation |
| 7 | `GLOBALID_SETTING_UNSET` (registry/finalizer) | R2 exclusion |
| 8 | `_LIVE_UNSET` (conf) | R3 exclusion |
| 9 | engine-truthiness cursor presence | R4 separation |
| 10 | `filters/sets.py:2324` redundant `None` term | R5 consumer note |
| 11 | all other `is None` sites in `list_field.py` | None-only, correct |
| 12 | UNSET defaults / prose package-wide | not the rule |

### Challenges

Counts are authoritative definitions only; the 32 consumer call sites,
oracles, and projections move with the owner and are listed, never
counted. Pre-change counts first, post-change recount after.

| # | Rule axis | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | sentinel arm | `strawberry.UNSET` replaced by a package sentinel | pre **2** (binding + hand-spelling), post **1** | F1 |
| C2 | None arm | explicit null becomes supplied on reads | pre **2** (rule body + hand-spelling), post **1** | F1 |
| C3 | new marker | a third inactive spelling | pre **2** (rule body + hand-spelling), post **1** | F1 |

The refused shape — `list_field.py` calling `is_inactive_value` with
its own `unset_sentinel=strawberry.UNSET` — composes the rule but
splits the binding 1 -> 2, so C1 stays 2 under it. Only composing
`is_supplied` drives every axis to 1.

No source-mutating experiment was needed to establish the counts (pure
predicate, bodies read); behavior is proved executed under Findings
(P2-P6).

## Findings

### F1 — list-argument supplied rule (CONFIRMED, consolidated 2 -> 1)

- **Contract + variation.** A schema-layer argument is supplied iff it
  is neither `None` nor `strawberry.UNSET`. Varies on: the sentinel
  identity (C1), the None arm (C2), further inactive markers (C3).
- **Sites + roles.** Definitions (2 pre, 1 post): the composed owner
  (`is_inactive_value` + `is_supplied` binding) and the x3
  hand-spelling. Consumers: 19 + 13 call sites (16 post). Oracles: the
  normalizer supplied rows in `tests/test_list_field.py`, the new
  UNSET-arm test, the 219 live list-field tests. Projections: the
  owner docstrings (all hold post-change; none needed an edit).
- **Challenges.** C1-C3 above: every axis counts 2 pre, 1 post.
- **Owner + lifetime.** Owner: `utils/connections.py::is_supplied`
  (principle 7). The rule body must stay strawberry-free by charter,
  so the binding is the narrowest cohesive owner a schema layer can
  compose without splitting the sentinel decision. Dependency
  direction verified acyclic (trace above). No stored derivation, so
  no principle-4 lifetime fields. The layer split does not defeat
  composition: it only bars moving the binding down into the
  traversal substrate; the list field is a schema layer that already
  imports strawberry, so composing the schema-layer binding preserves
  the split. A new list-local helper was refused (principle 11: a
  composed owner exists).
- **Migration.** The x3 block becomes three `is_supplied` calls; one
  import added. Both owners untouched (the f45/f47 precedent: compose
  by name, never restate).
- **Distinct behavior.** None within the rule. The five exclusions
  (R1-R5) stay separate with triggers below. The `is_supplied`
  docstring's "connection surfaces" wording stays true (it is that
  spelling; the list surface now shares it), so no prose edit was owed.
- **Behavioral proof.**
  - P1 `static-reviewed`: `not (v is None or v is UNSET)` is the De
    Morgan exact equivalent of the replaced conjunction on every
    input; both are pure identity checks that run no hooks, raise
    nothing, and touch no state (principle 8: no short-circuit,
    exception, or effect difference). Rejects "wrong result on any
    input", including `""` (supplied under both, then the
    `non_integer` arm), `[]`/`0` (supplied under both), hostile
    `int` subclasses (supplied under both, then the exact-type arm),
    and `bool` (supplied under both, then `non_integer`).
  - P2 `execution-verified`: the 4 new rows pass in the shared tree
    (`uv run pytest tests/test_list_field.py::test_normalize_list_arguments_treats_unset_as_omitted tests/utils/test_connections.py::test_unset_identity_comparisons_live_only_at_named_separations --no-cov -n0`).
  - P3 `execution-verified`: neighbor suites, 157 passed in the
    workspace copy (`workspace.py run dry/listsup-f55/consolidate --
    pytest tests/utils/test_connections.py tests/test_list_field.py
    --no-cov -n0`, run `dry-20261002T040059-8d9752` exit 0).
  - P4 `execution-verified`: live list-field suites, 219 passed in
    the workspace copy (`... test_list_field_api.py
    test_list_field_async_api.py --no-cov`, run
    `dry-20261002T040116-1664fb` exit 0). Rejects "wire behavior
    moved".
  - P5 `execution-verified`: gate negative control —
    hand-spelling reintroduced as a mutant fails exactly the gate
    row while the 3 behavioral rows pass (1 failed, 3 passed).
  - P6 `execution-verified`: oracle failability — `order_by_supplied
    = True` mutant fails exactly the 3 behavioral rows. P5/P6 via
    `workspace.py prove dry/listsup-f55/consolidate
    docs/dry/temp-tests/listsup-f55/manifest.json` (exit 0, both
    entries pinned, restores byte-proved).
- **Structural gate.**
  `tests/utils/test_connections.py::test_unset_identity_comparisons_live_only_at_named_separations`:
  exact-match AST census over the 120 package files pinning exactly
  the two R1/R2 separation hits
  (`("utils/inputs.py", "iter_provided_input_fields")`,
  `("types/finalizer.py", "finalize_django_types")`), zero elsewhere.
  Defaults are not `Compare` nodes, so the five legitimate
  `order_by=UNSET` defaults never trip it. Negative control is P5:
  every behavior oracle passes the bypass mutant, the gate fails it.
- **Coupling.** None. Single-file production edit plus two test
  appends. The new import edge adds `strawberry.relay.utils` to the
  list-field import closure; it is side-effect-free and the 157 + 219
  green runs prove import health.
- **Freshness.** HEAD `dd0b6691` unmoved. ITEM_BASELINE `a09b9552`
  (== pre-edit WT on all three indexed files; zero drift at dispatch).
  Blobs (`HEAD / baseline / WT-post`): `list_field.py`
  `3842542a / f7b75c2a / caf1f290`; `utils/input_values.py`
  `929e81b5 / 463f81a8 / 463f81a8`; `utils/connections.py`
  `5bf8f5fa` throughout. Connected: `utils/inputs.py` `8839b38d`,
  `types/finalizer.py` `09f3e327`, `filters/sets.py` `17dae905`,
  `connection.py` `6c4b01f9`, `tests/test_list_field.py`
  `5b4e5339 -> dc146cd7`, `tests/utils/test_connections.py`
  `65d54027 -> 67a9e6e5` (WT). Searched population: 120 package
  `.py` files. Excluded on body strength: every module in the R1-R5
  rows plus all default/prose-only UNSET sites. Cells: default only;
  sharded/PG inapplicable by construction (the rule is a pure
  predicate over argument values — no database, alias, or dialect
  decision; Worker-2 judges).

### R1 — write-flavor provided rule (rejected; distinct contract)

`utils/inputs.py::iter_provided_input_fields` (`utils/inputs.py:1308`)
skips `UNSET` but keeps an explicit `None` as provided — a
null-clear must survive decoding. Same token, opposite None arm,
separate reasons to change (read inactivity vs write decoding).
Durable home: the function's own docstring states the distinction.
Trigger: the write flavors adopt None-inactive decoding.

### R2 — `GLOBALID_SETTING_UNSET` (rejected; distinct sentinel)

The registry's setting-snapshot tri-state (`registry.py`,
`types/finalizer.py:877`) answers "not yet computed", never input
activity. Different subject, different sentinel object. Trigger: the
snapshot merges into the input-activity vocabulary.

### R3 — `_LIVE_UNSET` (rejected; distinct sentinel)

`conf.py`'s private live-source tri-state. Same reasoning as R2.
Trigger: it merges into the input-activity vocabulary.

### R4 — engine-truthiness cursor presence (rejected; recorded separation)

`derive_connection_window_bounds` reads cursor presence by engine
truthiness (`utils/connections.py:727-728`), where `""` is absent —
while under this rule `""` is active. The comment records why:
`SliceMetadata` builds its slice under `if before:` / `if after:`.
Trigger: the engine changes its truthiness reads.

### R5 — `filters/sets.py:2324` redundant None term (consumer note, no action)

`branch_value is None or is_inactive_value(branch_value, ...)`
composes the owner with a redundant first term. It is not a second
definition under any plausible change: sentinel and marker changes
still land once at the owner. Not a defect (behavior-identical).
Trigger: the rule stops treating `None` as inactive — then the term's
fate is a behavior question for the maintainer, not this family.

No sub-rule decomposed: no new index row is owed to Worker-0.

## Defects

None.

## Pending execution

None. Every proof above executed; the workspace run ids are cited
inline (P3-P6). No `proof:` or `gate:` entry is owed.

## Judgment

CONFIRM and landed. The list normalizer's x3 hand-spelling was the
sole remaining restatement of the active-input rule package-wide
(AST census over 120 files); it now composes `is_supplied`, driving
all three variation axes from 2 definitions to 1. The sentinel-binding
layer split is preserved, not defeated: the binding stays single-sited
at the schema layer. Five exclusions carry triggers; no defect found.

## Implementation (Worker-1)

Tracked changes (`git diff a09b9552 -- <paths>`, +89/-3 over 3 files):

- `django_strawberry_framework/list_field.py` (+4/-3): import
  `is_supplied` from `.utils.connections` (`list_field.py:88`); the
  x3 block becomes three `is_supplied` calls
  (`list_field.py:447-449`). The edited lines are byte-identical to
  HEAD (only line numbers moved); f47's ledgered `coded_error_extensions`
  hunk and the external truth-migration hunks in the same file are
  untouched by content. No hunt-dirtied line edited.
- `tests/test_list_field.py` (+17): new parametrized UNSET-arm test
  (3 rows), appended at end; file was ruff-clean with a HEAD-identical
  tail, so the append is a pure addition.
- `tests/utils/test_connections.py` (+68): AST census gate + helper,
  appended at end with 3 import lines; file was HEAD-clean and
  ruff-clean.
- Owners untouched: `utils/input_values.py`, `utils/connections.py`
  (zero bytes changed).

Gates (all own runs, whole scope): `uv run basedpyright` — 0 errors,
0 warnings, 0 notes; `uv run python scripts/check_any.py` — 128
allowed uses at 89 sites, exit 0 (no new `Any`); `uv run python
scripts/check_truthful_reads.py --check` — errors 0. No new
cast/`Any`/suppression (the replaced code needed none; the new code
needs none). `ruff check --fix` + `ruff format` on exactly the three
touched paths: clean, zero reflow of concurrent lines (item-scoped
diff shows only the hunks above). `check_trailing_commas.py --check`
on the three paths: 0 violations.

Suggested `## Owned changes` rows for Worker-0 (verbatim shape):

- Run-12 Family `list-argument-supplied-spelling` (f55; +89/-3):
  - `django_strawberry_framework/list_field.py` — Family
    `list-argument-supplied-spelling` (f55) — owner import + 3
    one-line compositions (`_normalize_list_arguments`
    supplied flags).
  - `tests/test_list_field.py` — Family
    `list-argument-supplied-spelling` (f55) — new UNSET-arm
    behavioral test (3 rows).
  - `tests/utils/test_connections.py` — Family
    `list-argument-supplied-spelling` (f55) — new structural
    gate: exact-match AST census pinning 2 UNSET-comparison hits.

## Independent verification (Worker-2)

Own trace, from fresh reads of the three indexed targets plus the
package-wide sweeps below, before opening `## Findings`. Sites and
roles: `django_strawberry_framework/utils/input_values.py::is_inactive_value`
(the parameterized rule, `value is None or value is unset_sentinel`)
plus `django_strawberry_framework/utils/connections.py::is_supplied`
(the `unset_sentinel=strawberry.UNSET` binding, composing the rule by
call) form one composed definition; the x3 `x is not None and x is not
strawberry.UNSET` block in
`django_strawberry_framework/list_field.py::_normalize_list_arguments`
(baseline lines 446-448) was the second definition. Consumers: every
`is_inactive_value(` call expression (19: 3 filters/inputs, 10
filters/sets, 3 input_values-internal, 1 the binding, 1 permissions, 1
sets_mixins) and every `is_supplied(` call expression (13 pre: 5
internal to utils/connections — line 178 holds two — plus 8 in
connection.py; 16 post). Separations: the UNSET-only provided walk
(`utils/inputs.py::iter_provided_input_fields`, explicit `None` kept as
provided), the `GLOBALID_SETTING_UNSET` snapshot check
(`types/finalizer.py::finalize_django_types`), the never-compared
`conf.py::_LIVE_UNSET` tri-state (assignments only; the live read is
`live is self._live_source`), engine-truthiness cursor presence
(`bool(before)` / `bool(after)` with the recorded split comment), and
the subsumed `branch_value is None` term at `filters/sets.py:2324`
(absence-shaped, right after the two-spelling extraction fallback).
Owner I would choose: `utils/connections.py::is_supplied` — the rule
body is strawberry-free by charter (input_values imports only
exceptions/truth/canonical) and takes the sentinel as a parameter, so a
schema layer that already imports strawberry must compose the binding;
calling the rule with an own `unset_sentinel=strawberry.UNSET` would fix
a second binding site instead of removing one.

My definition counts, posited independently: C1 (sentinel binding
changes for the schema-layer surfaces) pre 2 (binding + x3), post 1;
C2 (the None arm changes) pre 2 (rule body + x3), post 1; C3 (an
observability/effect obligation lands on the rule, e.g. counting
evaluations) pre 2 (rule body + the bypassing x3), post 1. The
family-sentinel declarations (`unset_sentinel=UNSET` at set-family call
sites) are principle-1 declarations, listed not counted, under every
axis. The R5 leading term does not join the C2 count: under "None
becomes supplied" its correct post-state is underdetermined by the rule
(absent-branch skipping stays regardless; present-None-vs-absent is the
the maintainer behavior question the trigger names), so it is not a definition that
must move together with the rule — and it sits identically pre and post,
so the consolidation delta is unaffected under any reading.

Reconciliation with `## Findings`: every count, role, and home above
matches W1 member-for-member (Enumeration rows 1-12, C1-C3 2->1, R1-R5
with triggers, the refused-shape binding-split reasoning). One apparent
difference arose and resolved in W1's favor: my first line-based sweep
counted 4 internal `is_supplied` sites vs W1's 5; expression-counting
shows line 178 holds two call expressions, so 5 internal / 13 pre / 16
post / 32 consumers all stand. No other difference.

Rulings on the Worker-0 check-points: (a) C1-C3 counts and the
refused-shape reasoning hold (my own three axes above agree). (b) The
binding-as-owner choice holds: strawberry-free charter verified by the
input_values import list, narrowest composable owner for a schema
layer, layer split preserved. (c) Principle-8 equivalence holds: De
Morgan exact by inspection (same identity comparisons, same order, no
hooks runnable, both sides return exact `bool`), plus my executed
14-input probe (`docs/dry/temp-tests/listsup-f55/w2_equiv.py`, 0
mismatches, hostile `__eq__`/`__bool__` never invoked) covering `""`,
`[]`, `0`, `bool`, int subclasses, and the downstream None-mapping
inputs. (d) Gate census exactness holds: my independent AST census over
the same 120 files finds exactly the 2 named hits post-change and
exactly the x3 block in baseline list_field.py (5 pre-change total);
the 5 legitimate `order_by=UNSET` defaults are present and the gate is
green, so defaults never trip; P5/P6 mutant reasoning re-derived sound
from the on-disk manifest (bypass mutant: gate 1-fail / behavioral
3-pass; `order_by_supplied=True` mutant: all 3 behavioral rows fail
since the record carries `UNSET`/`True`/`True`). (e) The
sole-remaining-restatement claim holds: 5 pre-change UNSET-Compare
nodes re-derived; every `is None or` / `is not None and` conjunction
package-wide swept, all different-subject/different-rule; no
`==`/`!=`/`in` UNSET forms exist. (f) R1-R5 each carry a contract
difference plus a trigger; the R5 no-action call is sound per the C2
analysis above. (g) The 219 live + 157 neighbor rows both re-ran green
in the shared tree at current bytes (see below), matching W1's
workspace counts exactly. (h) The `tests/` tier is correct for both
tests: a live GraphQL request cannot express UNSET here — the
synthesized `__signature__` Strawberry reads sets `default=None` for
all three args, so omitted and explicit-null both arrive as `None`;
UNSET arrives only via direct calls (the real-signature
`order_by=UNSET` default or an explicit pass) — and the gate is
structural by nature. (i) Dirt attribution byte-proved: x3 lines
identical HEAD/baseline (only numbers moved), the import a pure
single-line insert, both test appends pure additions
(`test_connections.py` diff vs HEAD is exactly the +68; the
`test_list_field.py` tail test byte-stable with count 3 both sides),
`utils/connections.py` untouched (5bf8f5fa throughout),
`is_inactive_value` body identical HEAD/WT (15/15 lines). (j) The new
`list_field` -> `utils.connections` edge is acyclic: only `__init__`,
`connection.py`, `relay.py` import `list_field`, and none of the
closure (`exceptions`, `resource_policy`, `input_values`, `typing`,
plus their `conf`/`utils/*`/stdlib/django/strawberry/graphql imports)
imports any of those three; the `strawberry.relay.utils` closure
addition is import-healthy per the 157 + 219 green runs. (k)
Sharded/pg inapplicable by construction, judged sound: the rule is a
pure predicate over argument values and both tests run on
`SimpleNamespace` info plus a stashed policy with no database, alias,
or dialect decision in reach.

Gates, all re-run whole-scope by Worker-2 in the shared venv at
current bytes: `uv run basedpyright` 0 errors / 0 warnings / 0 notes;
`uv run python scripts/check_any.py` 128 allowed at 89 sites (no new
`Any`); `uv run python scripts/check_truthful_reads.py --check`
errors 0. `uv run ruff format --check` + `uv run ruff check` +
`scripts/check_trailing_commas.py --check` on the three touched paths:
all clean. Execution re-runs: 4 new rows passed, both neighbor files
157 passed, both live list-field suites 219 passed. The production diff
adds no cast, `Any`, or suppression the replaced code did not need.
`## Pending execution` correctly lists nothing. Prose rules: no
process provenance in the diff, `path:NN` citations permitted in this
`docs/dry/dry-*.md` scratchpad, link scaffold intact (10 headers), no
oracle rewritten to read from the owner (both new tests pin literal
expectations; the item diff otherwise only appends).

No (Worker-2) defects: `## Defects` stays as written. Verdict
`verified`, plain.

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
