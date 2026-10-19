# DRY review: `django_strawberry_framework/forms/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, or is a rejection
carrying its contract difference + trigger. Zero production edits; zero
tracked files changed.

## System trace

Tiny target (30 lines, FRESH — no prior cycle record names it beyond a
passing blob mention in the root artifact): the form-mutations leaf manifest.
It DEFINES nothing behavioral — two re-export bindings composing the
`DjangoFormMutation` / `DjangoModelFormMutation` class names by name from
[forms-sets][forms-sets], plus the 2-member `__all__` mirror and a docstring
stating the four-module map (spec-038 Decision 4) plus the public-surface path
(spec-038 Decision 5: [forms-sets][forms-sets] backs the re-exports, the
package root exports them from here). No logic, no branching, no guard, no
`__getattr__`, no ledger, no queryset, no transport, no sync/async machinery:
the only runtime effect is import-time binding.

Connected code read for judgment, outside the item:
[forms-sets][forms-sets] (both class definitions
`::DjangoFormMutation` / `::DjangoModelFormMutation`, read at head + class
lines), [forms-converter][forms-converter] (head + `convert_form_field`
contract), [forms-inputs][forms-inputs] (head + `INPUTS_MODULE_PATH` passage),
[forms-resolvers][forms-resolvers] (head + pipeline account), the package root
[pkg-root][pkg-root] (full; confirms the `from .forms import` line + the two
`__all__` entries), sibling leaf manifests [mutations-init][mutations-init]
(full head; cites this file's shape) and [filters-init][filters-init] (head),
[auth-init][auth-init] + [extensions-init][extensions-init] (shape precedents),
the contract source [spec-038][spec-038] Decisions 4-5 (read), oracles
[test-init][test-init] (forms import block, read) and `tests/forms/*`
(consumer imports via grep), and prose projections [tree][tree] (forms rows)
+ [glossary][glossary] (form-mutation anchors).

Excluded with reason: every other indexed family whose files-covered list
touches `forms/` was judged on its mechanism against this target's REAL
surface and found to have none here (see Matrix axes 1-3 and Challenges
C5-C8); the concurrent dirt (`django_strawberry_framework/connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was left
untouched; none of it is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates ONE flavor (forms)
from one home module. Sibling leaves each aggregate only their own flavor;
the package root is the sole cross-flavor aggregator, so there is no second
cross-flavor export table to drift. Considered family
`package-root-public-surface`: rejected, see F1.

**2. Sync/async twins.** Target defines no colored pair: no `def`, no `await`,
no `sync_to_async` (full 30-line read). The form sync/async twinship
(`resolve_form_sync` / `resolve_form_async` via `make_resolver_entries`) is
owned at [forms-resolvers][forms-resolvers]. Considered families
`one-sync-boundary`, `related-object-visibility-recheck`,
`sync-boundary-recourse-wording`: checked, no surface — this file holds no
boundary call, no decoder, no recourse string (C5-C7 end here with 0
definitions). `subsystem-clear-lifecycle` (files-covered names
`forms/inputs.py` + `forms/sets.py`, not this leaf): checked, no surface —
this file registers no clear callback and holds no ledger.

**3. Derived rather than repeated knowledge.** `__all__` hand-mirrors the two
import bindings in the SAME file (one edit region, not two definitions). The
input-type NAME derivation is not re-derived here: no naming rule lives in
this file. Considered families `set-type-naming`,
`converter-table-per-surface-ownership`: checked, no surface — this file holds
no naming rule and no converter table (C8 ends here with 0 definitions; do
not inherit).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack, build/parse
halves. Import binding → `__all__` membership → `import *` binding is one
direction with a single author (this file), not two halves. No surface.

**5. Contracts restated in another medium.** Three media carry this file's
contracts: production code (bindings + manifest); authoritative contract
sources ([spec-038][spec-038] Decisions 4-5); projections (in-file docstring,
[tree][tree] + [glossary][glossary] blocks). A new form base moves its home
definition once; this file plus the root follow by name (C1). Counted once,
at [forms-sets][forms-sets].

**6. Enforcement by omission.** One deliberate omission with a contract
source: no `FieldError` / `DjangoMutationField` re-declaration here (Decision
5: both flavors ride the existing factory + envelope). Every member the
contract requires is present: both bases exported, nothing else bound. No
member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **4 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (subsystem paragraph + four module-role bullets + public-path paragraph) | (none) | prose projection, F1/F2 |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3 | `from .sets import DjangoFormMutation, DjangoModelFormMutation` | 2 names | R1, F1 |
| 4 | `__all__: tuple[str, ...] = (...)` | 2-member tuple | R1, F1 |

Rules: R1 forms leaf manifest (statements 3-4 + public-path prose); R2
four-module map prose (statement 1 paragraphs 1-2, Decision 4 mirror shape).
Four indexed families considered (`package-root-public-surface`,
`subsystem-clear-lifecycle`, `converter-table-per-surface-ownership`,
`one-sync-boundary` + `related-object-visibility-recheck` +
`sync-boundary-recourse-wording` as no-surface checks): one rejected with
contract difference + trigger (F1), the rest checked with no surface (Matrix
axes 1-3, C5-C8). No existing family name is reused for a finding; two new
file-local index rows are named for Worker 0 (`F1`, `F2`).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new base | expose a 3rd form base (e.g. a split plain flavor) | **1** (the definition at [forms-sets][forms-sets]; this file's import line + `__all__` entry plus the root's import line + `__all__` entry + oracle rows are consumer rows that follow by name) | independent |
| C2 | R1 rename | rename `DjangoFormMutation` → `DjangoPlainFormMutation` | **1** (home definition; two lines here + root lines + consumer imports follow) | independent |
| C3 | R1 home move | move `DjangoModelFormMutation` out of `sets.py` | **1** (the owner move; exactly one import line here follows) | independent |
| C4 | R1 un-root | root stops exporting the forms pair (leaf stays) | **0 here** (root import + `__all__` + pin oracle move; this file does not) | independent — proves separation |
| C5 | `subsystem-clear-lifecycle` check | change the clear-bus contract | **0 here** (bus at `registry.py`; rows live in `forms/inputs.py` + `forms/sets.py`, none here — grep: zero `register_subsystem_clear` in this file) | no surface — do not inherit |
| C6 | `related-object-visibility-recheck` + `sync-boundary-recourse-wording` check | change relation visibility or the sync-misuse recourse sentence | **0 here** (decoders at [forms-resolvers][forms-resolvers], recourse at `utils/querysets.py::sync_pipeline_recourse`; no decoder token, no recourse token lives here) | no surface — do not inherit |
| C7 | `one-sync-boundary` check | change the write-pipeline boundary worker | **0 here** (skeleton at `mutations/resolvers.py`; this file holds no boundary call) | no surface — do not inherit |
| C8 | `converter-table-per-surface-ownership` + `set-type-naming` check | change the form scalar table or the input-type naming derivation | **0 here** (table at [forms-converter][forms-converter], naming via `forms/inputs.py::form_input_type_name` → driver; this file holds neither) | no surface — do not inherit |
| C9 | R2 module-role change | change what `converter.py` owns | **0 here** (that module moves; this file's bullet becomes stale prose, a projection, not a definition) | independent — proves projection |

No executable proof was run: the target has no runtime semantics beyond
import-time binding (no branches, no awaits, no queryset/transport code), so
there is no behavior an execution could distinguish. The read-only
`ast.parse` enumeration above ran in the shared tree (non-mutating; the
workspace recipe authorizes mutating proofs, of which this item has none).
Every binding is exercised by consumer imports on every suite run
(`tests/forms/*`, `tests/base/test_init.py`, fakeshop suites). All claims
below are therefore `static-reviewed`; there is no `execution-deferred`
proof and no `docs/dry/temp-tests/` scratch was created — inspection
suffices, and a probe could distinguish nothing. No shared-tree pytest run.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — forms leaf manifest (file-local)

- **Contract + variation.** The forms subpackage's public surface is exactly
  two mutation-base names, each composed by name from [forms-sets][forms-sets],
  with `__all__` mirroring the bindings in-file. Legitimate variation: set
  membership only (a 3rd base adds one import line + one tuple entry in this
  file, plus consumer rows at the root).
- **Sites + roles.** *Definitions*:
  [forms-sets][forms-sets]`::DjangoFormMutation`,
  `::DjangoModelFormMutation`. *Consumer rows*: this file's statements 3-4;
  the package root [pkg-root][pkg-root] `from .forms import` line +
  two `__all__` entries (second-layer consumer, pinned by the root's
  exact-tuple oracle). *Oracles*: explicit-name consumer imports
  (`tests/forms/*`, [test-init][test-init] forms block, fakeshop schemas) —
  independent (they resolve the homes through this file without reading the
  manifest). *Projections*: statement-1 public-path paragraph, Decision 5
  code block, [tree][tree] + [glossary][glossary] blocks.
- **Challenges.** C1, C2, C3 → 1 definition each (the home module); C4 → 0
  here.
- **Owner + lifetime.** Per-symbol home module [forms-sets][forms-sets]
  (existing owner, chosen by responsibility: both classes' declaration,
  `Meta` validation, and bind machinery all live there; no narrower owner
  this file's consumers could depend on exists). This file is a consumer
  (principle 6: compose by name). No stored derivation; no lifetime fields
  owed.
- **Migration.** None (zero-edit item): single owner stands; a new base adds
  its definition plus one consumer row here (plus the root's consumer row).
- **Distinct behavior.** The manifest intentionally covers only the two bases
  — no `FieldError` / `DjangoMutationField` re-declaration (Decision 5:
  both flavors ride the existing factory + envelope, Matrix axis 6).
- **Behavioral proof.** `static-reviewed`. Rejects "a re-export shadows its
  owner" (bindings are by-name imports; `forms.DjangoFormMutation is
  forms.sets.DjangoFormMutation` by construction of the import system) and
  "star binding leaks a 3rd name" (`__all__` names exactly the two; grep
  finds no other binding in this file).
- **Structural gate.** No exact-`__all__` oracle exists for this leaf (grep:
  no `import *` on `forms`, no `__all__` assertion in `tests/forms/`) —
  the same standing as the auth/extensions/filters leaves. Standing in:
  every consumer imports the two names explicitly, so a dropped binding
  fails loudly (`ImportError`) at use sites on every suite run; the root's
  exact-tuple pin additionally pins the two names one layer up. Noted as an
  observation, not a defect: no contract row requires a manifest pin, and
  a bespoke existence test per leaf manifest would violate the gate-only
  economy (principle 9).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/forms/__init__.py`
  `a76a4f797414e90b102eaca2598314ed6ba4b47c`,
  `django_strawberry_framework/forms/sets.py`
  `36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`,
  `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  `django_strawberry_framework/mutations/__init__.py`
  `9a5683e91457b1a47e795de8b5fbd9db48ca1039`,
  `django_strawberry_framework/filters/__init__.py`
  `86b258186638c96995e31919346f44d7951c65ea`,
  `django_strawberry_framework/auth/__init__.py`
  `6bc3c4a5eb965988d91fef5c87240826e5163e6c`,
  `django_strawberry_framework/extensions/__init__.py`
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
  `tests/base/test_init.py`
  `4cc121057689409213beb5ec31772130cdacb975`,
  `docs/SPECS/spec-038-form_mutations-0_0_12.md`
  `fb1ba405cb1af5e6194ab79cc5b49b7210ee68d5`.
  Searched population for a second manifest of the 2-name set: whole
  package + `tests/` + `examples/` + `docs/` (grep `DjangoFormMutation`:
  only homes, this file, the root consumer, and prose mentions). Excluded
  on strength of body: `mutations/sets.py` machinery (different subsystem)
  and `forms/inputs.py::FORM` (operation-kind sentinel, not the class —
  shared token, not shared rule).
- **Rejection (nested).** Considered: consolidate the leaf manifest into
  indexed family `package-root-public-surface` (same eager-re-export +
  `__all__` shape — the auth, extensions, and filters items rejected the
  same family for their leaves, each with its OWN difference + trigger;
  this leaf is the same SHAPE but not the same difference, compared fresh,
  nothing inherited). Contract difference here: the root manifest is the
  cross-flavor default recipe every consumer pays for at package import
  (38 eager bindings across 16 statements, exact-tuple pin + identity
  oracles, four deliberate omissions), while this leaf is the single-flavor
  2-name manifest with no pin whose explicit-import consumers fail loud as
  `ImportError` — and unlike the auth/filter leaves this flavor IS
  root-exported by Decision 5, so a new base moves BOTH files as layered
  consumers (C1) while un-rooting the pair moves ONLY the root (C4) and
  root-side changes to unrelated symbols move ONLY the root. Different
  responsibility (flavor grain vs cross-flavor recipe), different
  population (2 vs 39), different gates: same shape, not the same rule.
  Trigger to reconsider: a decision to drive every subpackage manifest
  from one shared driver/validator, or to root-export the whole leaf
  wholesale by construction (e.g. `from .forms import *`), would make the
  sites one rule. Durable home: [spec-038][spec-038] Decision 5 (already
  states the root export) + this file's public-path paragraph.

### F2 — four-module map prose (file-local)

- **Contract + variation.** The docstring maps the four sibling modules to
  their responsibilities (converter / inputs / sets / resolvers) in the
  spirit of `mutations/` per Decision 4, and states the public-surface path
  (sets backs the re-exports; root exports from here per Decision 5). No
  legitimate variation while Decisions 4-5 stand; a module rename or role
  change revises prose, not behavior.
- **Sites + roles.** *Contract sources*: [spec-038][spec-038] Decisions 4-5.
  *Mechanism definitions*: [forms-converter][forms-converter]
  (`convert_form_field` + kind constants), [forms-inputs][forms-inputs]
  (generators + `INPUTS_MODULE_PATH`), [forms-sets][forms-sets] (bases +
  `Meta` validation + bind), [forms-resolvers][forms-resolvers] (pipeline).
  *Projection*: this file's statement 1. *Consumers*: [tree][tree] forms
  rows (rendered from module docstrings, not this file).
- **Challenges.** C9 → 0 definitions here — proves the prose is enforced
  away from this file; this file could not drift any module's contract even
  if edited carelessly.
- **Owner + lifetime.** Each sibling module owns its contract (existing
  owners by responsibility); Decisions 4-5 own the layout. This file carries
  prose only. No stored derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The map covers exactly the four modules; the
  `mutations/` six-module quartet-plus-permissions-plus-operations shape is
  the named precedent, not a twin (Decision 4 text verified: converter /
  inputs / sets / resolvers + reuse of `DjangoMutationField` + `FieldError`).
- **Behavioral proof.** `static-reviewed` (each bullet's named symbol
  verified at its owner: `convert_form_field`, `InputFieldSpec`,
  `base_fields` generators, both bases, pipeline steps; Decision 4-5 text
  matches the spec headings verbatim).
- **Structural gate.** None owed: stale prose is visible in review, not
  silently absorbable, and no gate pins docstring wording.
- **Coupling.** None.
- **Freshness.** Target `a76a4f797414e90b102eaca2598314ed6ba4b47c`,
  [forms-converter][forms-converter]
  `b717fd0f68bba4c50ee9883ed4a9ccd59b700a51`,
  [forms-inputs][forms-inputs]
  `55614839ff479b3610b6026be65f2107ee560fcd`,
  [forms-resolvers][forms-resolvers]
  `4edb984b299b4e2a71492e73382558b01865f48a`,
  [forms-sets][forms-sets] `36ce80b4…`, spec-038 `fb1ba405…`.

## Defects

None. Every docstring claim checked held: the four-module map (Decision 4
text verified: converter / inputs / sets / resolvers + reuse of
`DjangoMutationField` + `FieldError`); each module-role bullet (named symbols
verified at their owners); the `InputFieldSpec` single-siting clause (defined
in `utils/inputs.py`, built by `forms/inputs.py::_field_triple_and_spec`);
the public-path paragraph (sets defines both bases; root line 25 imports both
from here; root `__all__` carries both). The axis-6 sweep finds no missing
guard: both required members present, the single omission carries Decision 5.

(Worker 2): no additional defects found; docstring, map, and omission
claims re-checked against owners — all hold (see verification below).

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding, all bindings resolve through consumer imports on
every suite run, and the only instrument used (`ast.parse`) is non-mutating.

## Judgment

Zero-edit file item. Two rules traced, both file-local with proving
challenges (F1 manifest, C1-C4; F2 map prose, C9); six indexed families
considered — one rejected with this leaf's own contract difference + trigger
(`package-root-public-surface`, F1 nested rejection, compared fresh against
the auth/extensions/filters leaf rejections rather than inherited), five
checked with no surface (`subsystem-clear-lifecycle` via C5,
`related-object-visibility-recheck` + `sync-boundary-recourse-wording` via
C6, `one-sync-boundary` via C7, `converter-table-per-surface-ownership` +
`set-type-naming` via C8). Enumeration covers 4/4 statements. No defects, no
pending execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (design-equivalent zero-edit result submitted for
verification). Item-scoped diff vs
`4e5da142b8c634ca61d2d597364bab03529c4c5d`:
`git diff <baseline> -- django_strawberry_framework/forms/__init__.py` empty
(exit 0); working blob `a76a4f797414e90b102eaca2598314ed6ba4b47c` equals
`HEAD:django_strawberry_framework/forms/__init__.py` and HEAD `9031cb3d` —
target CLEAN, so no hunk attribution was owed. The artifact itself
(`docs/dry/dry-file-forms____init__.md`) is a new untracked file, the item's
only output. No `uv run ruff format .` / `ruff check` run (no edits to
format; `.md` is outside ruff format scope). No shared-tree pytest run. No
`docs/dry/temp-tests/` scratch created (inspection suffices — see
`### Challenges` note). Concurrent dirt listed in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) plus the other untracked `dry-file-*.md`
artifacts were left untouched; the `## Owned changes` ledger (walker D1 fix
+ 2 live test files) gains no row from this item. Worker-0 instructions: (a)
tick the plan item `File forms/__init__.py — dry-file-forms____init__.md`
as verified under Run `0.0.15 2026-09-18-1` once Worker 2 agrees; (b) add
these two `## Responsibility index` rows (both `file-local`, holding item
`File forms/__init__.py`):

| `forms-leaf-manifest` | per-symbol home module (`__all__` manifest at `django_strawberry_framework/forms/__init__.py`) | `django_strawberry_framework/forms/__init__.py` (+1 owner module) | File `forms/__init__.py` | file-local |
| `forms-module-map-prose` | spec-038 Decisions 4-5 (mechanism: sibling modules + registry/finalizer bind) | `django_strawberry_framework/forms/__init__.py` | File `forms/__init__.py` | file-local |

No commit.

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Verified at HEAD `9031cb3d`
(`git rev-parse HEAD`); target 30 lines, working blob equals
`HEAD:django_strawberry_framework/forms/__init__.py`. Own trace below was
derived from the target, owners, consumers, and contract sources before
reconciling with W1's findings; every difference is reconciled explicitly
(verdict: none — full agreement).

### Own trace (expectation-first)

Target read in full (30 lines): a leaf manifest with no behavioral
definition — two by-name re-export bindings, one `__all__` mirror, one
docstring, one `__future__` import. I derive two rules:

- **R1 (2-name manifest + `__all__` mirror).** Definitions: the two class
  objects live in `django_strawberry_framework/forms/sets.py`
  (`::DjangoFormMutation`, `::DjangoModelFormMutation` — declaration,
  `Meta` validation, and bind machinery all there). Consumer rows: this
  file's import line + `__all__` tuple; the package root's
  `from .forms import` line (line 25) + its two `__all__` entries.
  Counts I posit independently: new 3rd base → 1 definition (home
  module; both manifest files follow by name); rename →
  1 (home; manifests follow); home move → 1 (owner move; one import
  line here follows); un-root the pair → 0 here (root rows move; this
  file does not — proves layered separation). Owner I would choose:
  per-symbol home module `forms/sets.py` (existing owner by
  responsibility; no narrower owner this file's consumers could depend
  on; principle 6 compose-by-name; principle 7 dependency direction).
  No stored derivation, no lifetime fields owed.
- **R2 (four-module map prose).** Contract sources: spec-038 Decisions 4
  (converter/inputs/sets/resolvers split + reuse of `DjangoMutationField`
  + `FieldError`, verified verbatim) and 5 (root export of the pair,
  verified verbatim). Mechanism owners: the four sibling modules
  (converter `convert_form_field` + kind constants; inputs generators +
  `INPUTS_MODULE_PATH`; sets bases + `Meta` + bind; resolvers pipeline).
  This file's docstring is a projection: a module-role change moves 0
  definitions here (stale prose only). Owner I would choose: each sibling
  for its contract + Decisions 4-5 for the layout — same as W1.

Reconciliation vs W1: R1 = W1 F1 (contract, sites/roles, C1-C4 counts,
owner, migration none, distinct-behavior omission) — agree on every
row. R2 = W1 F2 (contract, roles, C9, owners, no gate owed) — agree.
No difference in sites, roles, counts, or owners.

### Enumeration (member-by-member vs own count)

Own instrument: `ast.parse` over the working tree file → **4**
`ast.Module.body` members (re-ran; matches W1's pinned-blob count):

| # | Statement | W1 home | Worker 2 |
|---|---|---|---|
| 1 | module docstring | prose projection, F1/F2 | agree — projection, no binding |
| 2 | `from __future__ import annotations` | boilerplate | agree — boilerplate, no rule |
| 3 | `from .sets import` (2 names) | R1, F1 | agree — consumer row |
| 4 | `__all__` 2-tuple | R1, F1 | agree — in-file mirror, one edit region |

4/4 land (F1/F2/file-local/boilerplate); no member unassigned. R1/R2
naming matches the rules; the two new file-local index-row names are
fresh (no existing family name reused) — agree.

### Matrix (judged on the target's real surface)

1. **Cross-flavor** — agree with inapplicability reason: target
   aggregates one flavor from one home; siblings aggregate only their
   own; the root is the sole cross-flavor aggregator (39-entry
   `__all__`). No second cross-flavor table exists to drift.
2. **Sync/async** — agree: no `def`, no `await`, no `sync_to_async`
   (full read + token grep confirms; only docstring prose mentions the
   pipeline). Twinship lives at `forms/resolvers.py`.
3. **Derived knowledge** — agree: `__all__` mirrors the two bindings in
   the same file (one region, not two definitions); no naming rule or
   converter table lives here (docstring token `convert_form_field` is
   prose, not a table — checked).
4. **Round-trip** — agree: binding → `__all__` → star binding is one
   direction with a single author, not two halves.
5. **Other media** — agree with classification: production (bindings +
   manifest), contract sources (Decisions 4-5), projections (docstring,
   TREE forms rows, GLOSSARY anchors — both confirmed present).
   Counted once at `forms/sets.py`.
6. **Omission** — agree: both required bases present; the one omission
   (`FieldError`/`DjangoMutationField`) carries Decision 5 (spec text
   verified: "reuses ... rather than re-declaring"). No missing guard.

Prior-leaf comparison (fresh, not inherited): auth rejects on structural
opt-out (root must never import auth); extensions on per-extension
recipe (debug deliberately not default); filters on family-grain opt-in
(Decision 2 forbids root carriage). This leaf's difference is its own:
the flavor IS root-exported (Decision 5), so C1 moves both manifests as
layered consumers while C4 moves only the root; population 2 vs ~39;
gates differ (explicit-import `ImportError` here vs root exact-tuple
pin). Same shape, not the same rule — W1's nested rejection is
correctly scoped and its trigger (shared driver/validator, or wholesale
star re-export) is the right reconsideration condition.

### Counts + roles; oracles

C1/C2/C3 → 1, C4 → 0 here, C5-C8 → 0 here (verified by token grep:
zero `register_subsystem_clear`, zero recourse/decoder/boundary/naming
tokens in code), C9 → 0 here — agree on all nine. Roles agree:
definitions at `forms/sets.py`; consumers here + root; oracles are
explicit-name imports (`tests/forms/*`, `tests/base/test_init.py`
forms block, fakeshop schemas) that resolve through the manifest
without reading it — independent, not rewritten. The root exact-tuple
pin (`tests/base/test_init.py`) pins the second-layer consumer, not
this leaf; `tests/forms/test_sets.py` asserts root `__all__`
membership, not leaf `__all__` — no oracle reads the owner it checks.

### Equivalence (principle 8)

Zero-edit item: no observable behavior changes, so no equivalence proof
is owed beyond the standing construction argument, which holds
(bindings are by-name imports; `forms.X is forms.sets.X` by import
semantics; `__all__` names exactly the two bound names — grep finds no
third binding). No ordering, transaction, async, or exception axis
exists in this file.

### Zero-edit, coverage, routing

Item-scoped diff confirmed empty by Worker 2:
`git diff 4e5da142b8c634ca61d2d597364bab03529c4c5d -- django_strawberry_framework/forms/__init__.py`
prints nothing (exit 0); `git status --short` shows the target clean
and the artifact as the only new path for this item. Zero production
edits — correct for a file item (no production edit is ever owed;
validation + assignment is the bar). Coverage: both bindings exercised
by explicit consumer imports on every suite run; assignment: F1/F2 both
file-local with proving challenges; routing: one rejection
(`package-root-public-surface`, own difference + trigger — endorsed)
plus five no-surface checks (C5 `subsystem-clear-lifecycle`, C6
`related-object-visibility-recheck` + `sync-boundary-recourse-wording`,
C7 `one-sync-boundary`, C8 `converter-table-per-surface-ownership` +
`set-type-naming`) — each judged adequate above (register rows live in
`forms/sets.py` line 125/160 + `forms/inputs.py` line 169, none here;
no decoder/recourse/boundary/naming surface here).

### Freshness (re-hashed by Worker 2 — all match)

`forms/__init__.py` `a76a4f797414e90b102eaca2598314ed6ba4b47c`,
`forms/sets.py` `36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`,
root `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
`mutations/__init__.py` `9a5683e91457b1a47e795de8b5fbd9db48ca1039`,
`filters/__init__.py` `86b258186638c96995e31919346f44d7951c65ea`,
`auth/__init__.py` `6bc3c4a5eb965988d91fef5c87240826e5163e6c`,
`extensions/__init__.py` `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`,
`tests/base/test_init.py` `4cc121057689409213beb5ec31772130cdacb975`,
spec-038 `fb1ba405cb1af5e6194ab79cc5b49b7210ee68d5`,
`forms/converter.py` `b717fd0f68bba4c50ee9883ed4a9ccd59b700a51`,
`forms/inputs.py` `55614839ff479b3610b6026be65f2107ee560fcd`,
`forms/resolvers.py` `4edb984b299b4e2a71492e73382558b01865f48a`.
Searched population (whole package + `tests/` + `examples/` + `docs/`
grep for `DjangoFormMutation`: only homes, this file, root consumer,
prose) and exclusions (`mutations/sets.py` machinery, `FORM` sentinel
— shared token, not shared rule) — agree.

### Gates, Pending, coupling

Gate reasoning endorsed: no leaf exact-`__all__` oracle exists (grep
confirms: no `import *` on `forms`, no leaf `__all__` assertion) — the
same standing as the auth/extensions/filters leaves. Negative control:
dropping a binding fails loudly — every consumer's explicit import
raises `ImportError`, and the root's `from .forms import` line breaks
(which the root exact-tuple pin then pins one layer up). Truncating
`__all__` alone has no gate, but no contract row requires a manifest
pin and a bespoke per-leaf existence test would violate the gate-only
economy (principle 9) — correctly noted as observation, not defect.
`## Pending execution` absent — adequate: no runtime semantics beyond
import-time binding, no mutating proof owed, `ast.parse` non-mutating,
no shared-tree pytest run, no `temp-tests/` scratch (a probe could
distinguish nothing). Coupling: none — agree.

### AGENTS.md prose check

Item-scoped diff is empty, so no process provenance, citation, tier,
or formatting rule is triggered. Artifact citations reuse the file's
existing reference-style link block (no new bare links); concurrent
dirt (`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`, sibling artifacts) left untouched. No commit.

### Verdict

`Status: verified`. Zero-edit file item: 4/4 statements covered, six
axes discharged, nine challenges counted, one rejection with own
difference + trigger, five no-surface routings judged, no defects, no
pending execution, no production edits.

Worker-0 instructions: (a) tick plan item
`File forms/__init__.py — dry-file-forms____init__.md` as verified
under Run `0.0.15 2026-09-18-1`; (b) add the two `## Responsibility
index` rows named in `## Implementation (Worker 1)` (both `file-local`,
holding item `File forms/__init__.py`).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[pkg-root]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->
[test-init]: ../../tests/base/test_init.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
