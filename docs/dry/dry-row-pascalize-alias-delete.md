# DRY review: `pascalize-alias-delete`

Status: verified
Run: 0.0.15 2026-10-11-17

## System trace

[mut-inputs][mut-inputs] bound the legacy `_pascalize_token = pascalize_token`
alias under a 5-line promotion comment: the injective single-leading-capital
token encoder had graduated to [utils-inputs][utils-inputs]`::pascalize_token`
(spec-039, at three consumers: model + form + serializer). The owner serves
`name_set_input_type_name` (model + form namings) and
[rf-inputs][rf-inputs] `_shape_token` directly; the alias served nobody.
Census (below): 0 code importers of the alias anywhere; the only
`path::Symbol` cites are the two sentences rewritten in this change.
Underscore-private, so no deprecation promise is owed.

## Verification

### Matrix

1. Cross-flavor mirroring: no sibling alias; the historical path existed once.
2. Sync/async twins: a module binding; no twin surface.
3. Derived knowledge: the alias derived nothing (pure rebinding).
4. Round-trip pairs: one binding, one owner; no pair.
5. Other media: spec cite + owner-docstring cite rewritten here; per-cycle
   dry mentions are exempt history, left; the board carries no mention.
6. Enforcement by omission: n/a — the deletion removes the surface itself.

### Census

Method (four instruments, all over package + tests/ + examples/ + scripts/):
word-boundary `_pascalize_token` (catches every `import`/`from` spelling,
attribute path, `getattr`/dynamic string, `__all__` entry — each must spell
the name); word-boundary `pascalize_token` (catches routing through the old
module); an `import *` sweep; full reads of the four multi-line
from-mutations.inputs import lists. Pre-edit population (7 lines, 4 files):
the alias def + its 2 cite-bearing comment lines (deleted here); the
owner-docstring sentence (rewritten here); 2 bare-name term uses in
[rf-inputs][rf-inputs] prose (comment + docstring — token-shape description,
not an import path, not `path::Symbol` cites; left per fenced scope); 1
substring hit in the owner's test name (`test_pascalize_token_...`, not the
alias). Zero hits in examples/ and scripts/. The module defines no `__all__`,
so no star-reexport. `__pycache__` holds 4 stale `.pyc` (alias module + prose
+ owner-test-name residue — regenerable, not importers).

### Challenges

- C1 (token-grammar change): the owner moves; the alias was transparent.
  Count 1 before and after.
- C2 (new consumer): imports the owner directly. Count 1.
- The alias added zero to every count: a principle-11 deletion (abstraction
  with no responsibility), not a count-2 consolidation.

## Findings

F1 (consolidated — deleted): the alias. Contract: none — pure indirection,
no boundary name, no isolation, no extension point. Sites: alias + comment
(deleted), the `pascalize_token` import name (deleted — its only in-module
use was the alias RHS), owner (kept, byte-identical def), the two falsified
sentences (rewritten), 5 proving suites (kept, unmodified). Owner: the
existing [utils-inputs][utils-inputs]`::pascalize_token` by responsibility
(serves all three consumers; pure function, no lifetime). Migration: delete
the binding; the promotion rationale already lives at the owner docstring, so
the alias-preservation prose retires with nothing to relocate ("Prose is
movable"). Shrinkage +3/-14 (net -11); machinery attestation: nothing added,
one import name removed. Distinct behavior: none — binding removal;
underscore-private, no deprecation owed. Behavioral proof:
execution-verified — 408/408 focused suites green post-edit (same count as
the pre-edit baseline) + 2/2 failability pins (ImportError / AttributeError
crash lines, restores byte-identical). Negative control: none (no bypass
threat — private alias, 0 importers). Coupling: none. Freshness: mut-inputs
`f821661e`->`5e99a667`, utils-inputs `c199eaa4`->`0fae4a0e`, spec
`ff9e2e9f`->`29f54d5f`; HEAD `c37a08a0`; ITEM_BASELINE `1529c7e6`; proving
suites at WT `e19514e0`/`4260fc02`/`a0177083`/`f450459e`/`92f69da5`.

## Defects

None. Pre-edit baseline 408/408 green: no pre-existing failure in scope.

## Pending execution

None — every proof executed. Sharded/pg cells inapplicable by construction
(an import binding + prose; no queryset, alias, or dialect surface; suites
run default sqlite) for Worker-2's judgment.

## Judgment

The alias carried no responsibility: private, zero importers, its promotion
rationale already owned by the surviving docstring. Deleted with its feed
import and the two sentences that asserted its existence; behavior pinned
green, miss-an-importer pinned red. The two bare-name term uses in
[rf-inputs][rf-inputs] prose stand (token-shape description, ungated,
outside this item's fenced scope).

## Implementation (Worker-1)

Production, 2 hunks in [mut-inputs][mut-inputs]: the `pascalize_token`
import name dropped (leaving it would trip F401 — the removal rides along)
and the 5-line comment + alias deleted (8 lines incl. separators). Prose, 2
hunks: owner docstring last sentence removed (the promotion paragraph now
ends at the `pascal_case` distinction); [spec-039][spec039] token-encoder
bullet de-parenthesized (the `utils/inputs.py::pascalize_token` cite stands
alone). Ledger-ready: `django_strawberry_framework/mutations/inputs.py`,
`django_strawberry_framework/utils/inputs.py`,
`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`; +3/-14 (net -11).
Attribution vs HEAD: my 4 hunks sit on HEAD-clean lines (`@@ -63`,
`@@ -772`, `@@ -684`, `@@ -2422`); every neighbor is untouched — ledgered
run-13 FAM-3 + adopted reverse-map in mut-inputs, ledgered run-16
pop-sentence in spec-039, hunt truth-migration hunks adjacent in both `.py`
files, all byte-identical; ruff `--fix` a no-op. Runs: shared smoke 1/1;
baseline `dry-20261011T141423-09bbec` 408/408; post
`dry-20261011T141436-4b16ad` 408/408; prove `dry-20261011T141526-17b330`
2/2 pinned; both basedpyrights 0/0/0; citations 3347 resolve; commas 0;
truthful-reads tier-1 0. Prove manifest at
`docs/dry/temp-tests/pascalize-alias-delete/prove.json` (live scratch for
Worker-0's removal).

## What shrinks

[mut-inputs][mut-inputs]: +0/-9 — the 5-line promotion comment, the alias
binding, its 2 blank separators, and the `pascalize_token` import name that
fed only the alias. [utils-inputs][utils-inputs]: +1/-2 (net -1) — the
"The old name remains as an import alias" sentence goes; the promotion
paragraph keeps its siting rationale (three consumers, shared machinery,
`pascal_case` distinction). [spec-039][spec039]: +2/-3 (net -1) — the
parenthetical asserting the alias goes; the surviving cite is the owner
alone. Overall +3/-14 (net -11): 0 new functions, 0 new tests, 0 new gates.

What leaves the tree: the historical import path, the comment that existed
only to preserve it, the feed import, and two existence-claim sentences. No
reader must resolve "which pascalize" again; a grep for the dead name now
returns only exempt per-cycle history, two ungated token-shape term uses,
and the owner's own test name. The next token-grammar change touches the
owner only — as it always did, since the alias never absorbed a change.
No machinery added: three deletions plus three reworded lines.

## Independent verification (Worker-2)

### Own trace (recorded from independent instruments, then reconciled)

Knowledge boundary: required reading exposed this artifact's `## Findings`
before this section was written; the trace below derives from my own
instruments over ITEM_BASELINE bytes (`1529c7e6`), my own workspace runs at
`dry/pascalize-alias-delete/verify-1` (slot-3), and my own prove manifest —
different instruments and anchors from Worker-1's throughout.

Census (0 live importers, two instruments over pre-edit bytes). (1)
`git grep` at ITEM_BASELINE: `_pascalize_token` = 7 lines / 4 files in
package + tests/ + examples/ + scripts/ (alias def + 2 comment lines in
[mut-inputs][mut-inputs]; 2 bare-name prose uses in [rf-inputs][rf-inputs];
owner-docstring sentence in [utils-inputs][utils-inputs]; owner test-name
substring) + the [spec-039][spec039] sentence; zero in examples/ and
scripts/. Every spelling is the def, prose, or a substring — no import, no
attribute read, no `getattr`/dynamic string, no `__all__` entry (the module
defines no `__all__`, so star-import would skip the private name anyway;
zero star-imports from any mutation module exist). (2) AST walk over the
494 baseline `.py` files (extracted via `git archive`): 0 static
from/imports of the alias, 0 `._pascalize_token` attribute reads, 0 bare
Name loads, 0 `pascalize_token`-from-`mutations.inputs` routings.
Snapshot gap closed: no `dir()`/`vars()`/`__dict__` enumeration of the
module exists anywhere (only provider `dir()` + parked-class prose).
If even one live importer had survived, the verdict would be
revision-needed; none did.

Sites/roles: alias + comment (deleted non-definition); feed import name
(deleted — its only in-module use was the alias RHS, confirmed by grep);
owner [utils-inputs][utils-inputs]`::pascalize_token` (kept, byte-identical
def); 2 falsified sentences (rewritten); ratchet + 4 suites (kept oracles).
Owner choice: the existing owner — it already serves all three consumers
(model + form via `name_set_input_type_name`, serializer via direct
`_shape_token` call), pure function, no lifetime; no other candidate
exists. Challenges: token-grammar change and new consumer both count 1
before and after — the alias absorbed zero changes. Verdict I would reach:
DELETE, principle-11 abstraction with no responsibility.

### Reconciliation (every difference explicit)

- Census: FULL AGREE (same 7-line / 4-file population via different
  instruments; 0 importers).
- Hunks re-derived: slot-1 vs slot-2 differ in exactly the 3 touched files
  (+ Worker-0's 4-line dispatch record in the plan, not W1's edit); +3/-14
  net -11; HEAD-side hunk ranges in WT = baseline ranges + exactly W1's 4
  (`-63,7`, `-772,14`, `-684,8`, `-2422,9`), so all 35 concurrent hunks
  pre-existed byte-identical and W1's sit on HEAD-clean lines. AGREE.
- Falsified sentences: FULL AGREE. Spec-corpus sweep: only [spec-039][spec039]
  `:2424` asserted the alias (rewritten); the other 4 spec `pascalize` hits
  cite the owner. `dry-rule-*` / folder / file / plan mentions are
  per-cycle `dry-*.md` records, not spec sentences; their single-ownership
  verdicts strengthen under deletion, and no reopening is owed ("Drift
  reopens nothing").
- Fenced scope (2 [rf-inputs][rf-inputs] term uses): STANDS. Both assert
  token shape ("single-leading-capital base"), not import-path existence,
  and the adjacent prose cites the owner (`:1025`, `:1075-1076`); the
  deletion falsifies nothing there.
- Behavior preservation (principle 8): CONFIRMED. No runtime path executed
  the alias; the only observable delta is two unread names absent from one
  module `__dict__` (zero readers, snapshot gap closed above); import side
  effects unchanged; underscore-private, no deprecation owed.
- Freshness: re-hashed live — `5e99a667` / `0fae4a0e` / `29f54d5f` and all
  5 suite pins (`e19514e0` = mut inputs, `4260fc02` = utils inputs,
  `a0177083` = rf inputs, `f450459e` = rf converter, `92f69da5` = ratchet)
  match; HEAD `c37a08a0` unmoved; slot-3 == live on all checked paths.
- AGENTS.md prose rules: PASS. No provenance in rewritten sentences; owner
  `path::Symbol` cites intact; no tests added or removed (correct — nothing
  to add); artifact links all reference-style, 10/10 group headers, zero
  inline links; W1 submission 144 non-`What shrinks` lines ≤ 150 (this
  appendix is DRY.md-mandated and outside the cap, per f66 precedent).
- Pending execution empty: AGREE. Every proof executed (W1's + my re-runs
  below); sharded/pg inapplicable-by-construction SOUND (pure string
  function + binding + prose; no queryset, alias, or dialect surface).
- One volatile figure: `.pyc` residue re-measures 2 files, both mirroring
  live source (kept rf prose + kept test name), 0 stale — W1's "4 stale"
  decayed via post-edit cache regeneration. Verdict-neutral (caches are
  never importers). No defect owed.
- Matrix: AGREE on all six axes against the real surface. Bar: HOLDS (P11
  deletion, +3/-14, zero machinery, behavioral proofs at tier, falsified
  sentences rewritten).

Fresh runs (all via `heavy`, slot-3 unless noted): 5-file focused suite
408/408 green (`dry-20261011T142620-d809c4`, incl. the `pascalize_token`
identity ratchet row); forms consumer extra 66/66
(`dry-20261011T142630-9f3ac0`); own prove manifest 2/2 pinned with
independent anchors (`dry-20261011T142636-8c2f59`: ImportError +
AttributeError crash lines, both restores byte-identical); both
basedpyrights 0/0/0 (`dry-20261011T142740-fe8a21`,
`dry-20261011T142855-01c8e7`); live-tree `ruff check` + `ruff format
--check` on both touched `.py` paths exit 0 (no F401 — nothing orphaned);
`check_citations` 3347/3347 (exactly 3351 − 4 removed cites);
`check_trailing_commas --check` 0 violations.

Touches this pass: this artifact only (Status + this section). No
production edits. Scratch kept at `~/dry/tmp/w2_pascalize_*`
and `~/dry/tmp/w2-base-tree/`. Verdict: verified.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[mut-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
