# DRY review: `shared-helper-import-aliases`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Target: nine private module-level aliases — the filters/orders
`inputs.py` helper trios (WT filters `:84-86`, orders `:61-63`; HEAD
`:83-85` / `:56-58`, text identical) and three bound-`.store`
registry handles (auth `:205`/HEAD `:203`, mutations `:766`/HEAD
`:790`, forms `:147`/HEAD `:142`, text identical). Shifts are nearby
dirt only; the verdict touches nothing, so no hold triggers.

Two instruments, re-derived fresh: an AST visitor over 503 repo
`.py` files (package + tests + examples + scripts; 503/503 parsed,
0 failures; Name/Attribute/import-from/string roles) and word-exact
`rg -w` over the whole tree (148 lines; `.venv`, `.git`,
`__pycache__`, `*.sqlite3` and the cycle record excluded).
Longer-name traps defeated: `auto_camel_case` and
`clear_mutation_registry` match only without `-w`.

Result: zero 0-reader aliases — every alias has executable readers
(28 reads + 9 imports; all committed, HEAD text identical). No
`__all__` listing (neither family `inputs` module defines one; both
flavor `__all__`s exclude the names), no star-import path, no
getattr/string reader, no examples/ or scripts/ hit. Both flavor
`__init__`s import `_input_type_name_for` for body use, not
re-export: nothing imports it from either package.

## Verification

### Matrix

1: write flavors call `graphql_camel_name` directly (forms `:521`
`:592`, rest `:1543`, mutations `:616` `:699` `:792`) and never saw
the set helpers — the family alias block is extraction-compat
addressability (owner docstring says so), not a package idiom.
Explained, kept. 2: no await surface. 3: pure rebinds, `is`-pinned,
never re-derived. 4: no inverse halves. 5: specs name
`_input_type_name_for` x2 + `_iter_orderset_subclasses` as surface;
the substrate docstring enumerates all five helper spellings. 6: all
nine enumerated, each with a reader.

### Challenges

- C1 (owner behavior change, e.g. camel digit rule): touches the
owner only; aliases carry no logic. Count 1.
- C2 (owner rename): mechanical 1-token/site respell. No logic moves.
- C3 (drop a test-only helper alias): strands the substrate
docstring enumeration plus spec-028 `:353`/rationale `:27` (orders
`_iter_`) plus guard arms with no public-name form — repairs outside
the fence. Keep.
- C4 (drop a store handle): no public migration target (`.store` is
equally private); strands sets `:582` + forms `:131` prose. Keep.
- C5 (`_input_type_name_for` x2): production readers out of fence.
Keep.

## Findings

### F1: six set-substrate helper aliases — kept, all live

- Contract: transparent private rebinds (`is`-identical, zero logic)
of the set-family substrate; documented addressable surface.
- Sites (WT refs; HEAD text identical):
  - filters `_camel_case` (`:84`): 3-assert behavior test + guard pin.
  - filters `_iter_filterset_subclasses` (`:85`): diamond test + pin.
  - filters `_input_type_name_for` (`:86`): production readers
  (`filters/__init__.py` `:41`/`:72`, intra-module `:1280`) + pin.
  - orders `_camel_case` (`:61`): 3-assert behavior test + guard pin.
  - orders `_iter_orderset_subclasses` (`:62`): diamond test + pin.
  - orders `_input_type_name_for` (`:63`): production readers
  (`orders/__init__.py` `:33`/`:64`, intra-module `:277`) + behavior
  test + pin.
- Bar: C1/C2 count 1 — no change obligation removed. P11 keeps on a
documented responsibility (substrate docstring + `is` guard +
spec-027 `:378`/`:887` + spec-028 `:346`/`:351`/`:353`/`:600`/
`:658`/`:672`/`:875` + rationale `:27`); deletion strands
out-of-fence prose (C3). No machinery either way.
- Owner/lifetime: [utils/inputs.py][utils-inputs] (and
[utils/strings.py][utils-strings] for camel); import-time bindings,
no stored derivation.
- Migration: none. Trigger: reconsider only if the guard retires AND
the projecting prose is reworded AND a fresh census reads 0.
- Index rows for Worker-0: `shared-helper-import-aliases` F1
(owner `utils/inputs.py`, files both `inputs`/`__init__` pairs +
substrate, `rejected` + trigger).
- Shrinkage: none — see `## What shrinks`.
- Distinct: the production-live pair vs the test-only quartet, per
the site list; `FieldSpec`/`build_input_class` out of scope.
- Proof: 26-node reader suite green at live bytes
(execution-verified); prove entries 1-2 pinned (wrong-value mutants
fail exactly the expected 2+3 nodes; restore byte-identical). Owner
behavior is pinned direct too. No new tests: coverage exists at both
tiers, and absence assertions are barred census tests.
- Negative control: none; bypass is not the threat.
- Coupling: none.
- Freshness: HEAD `c37a08a0`, baseline `942dfc3d`; blobs filters
`4114d17`, orders `430ac82`, substrate `0fae4a0`, inits `8df38dd` /
`d784c77`, tests `4260fc0` / `9e69f40` / `9de61ae`, specs `a73f867` /
`f2fa4c0` / `b5f400b`.

### F2: three bound-`.store` registry handles — kept, all live

- Contract: the documented test-introspection point for each
declaration ledger (the backing list itself).
- Sites: auth `_auth_declarations` (`:205`, 5 asserts / 3 tests);
mutations `_mutation_registry` (`:766`, 2 asserts / 2 files); forms
`_form_mutation_registry` (`:147`, 1 assert). All committed.
- Bar: no public-name form exists; respelling tests to
`_x_declaration_registry.store` lengthens private reach for zero
gain. Run-20 landed bound-`.clear` as the accepted bound-member
idiom. Deletion strands out-of-fence prose (C4).
- Owner/lifetime: [mutations/sets.py][mutations-sets]`::make_declaration_registry`
(mechanics; disjoint per-flavor stores); import-time handle.
- Migration: none. Trigger: reconsider only if the introspecting
oracles are re-expressed through public iteration AND the covering
prose is reworded.
- Index rows for Worker-0: `shared-helper-import-aliases` F2 (owner
`mutations/sets.py`, files the three sets modules, `rejected`).
- Proof: idempotency oracles green in the 26-run; prove entry 3
pinned (`[]` rebind fails `assert 0 == 1`; restore byte-identical).
- Negative control: none. Coupling: none.
- Freshness: blobs auth `217c6bf`, mutations `6f2fa2f`, forms
`6681c33`, tests `2a224eb` / `c95a185` / `4270e6a`.

## Defects

- D1: the filters alias-block comment claims `factories.py` imports
the five alias names; the census finds it imports none of them at
HEAD or WT (only `_build_input_fields` / `_build_logic_fields`).
Doc-only; owner is the filters comment; homed to closeout, unfixed
here since defects are never fixed inside the item.

## Pending execution

- `gate: heavy uv run pytest -n0 --no-cov -q tests/utils/test_inputs.py::test_filter_and_order_families_share_one_substrate tests/utils/test_inputs.py::test_filter_and_order_input_namespaces_ride_make_set_input_namespace tests/utils/test_inputs.py::test_graphql_camel_name tests/utils/test_inputs.py::test_iter_set_subclasses_dedupes_diamond_inheritance tests/utils/test_inputs.py::test_set_input_type_name_delegates_to_type_name_for tests/filters/test_inputs.py::test_camel_case_returns_input_when_no_word_characters tests/filters/test_inputs.py::test_iter_filterset_subclasses_dedupes_diamond_inheritance tests/filters/test_inputs.py::test_filter_input_type_returns_forwardref_in_annotation_args tests/filters/test_inputs.py::test_filter_input_type_is_idempotent_under_repeated_calls tests/filters/test_inputs.py::test_materialize_input_class_registers_in_module_globals tests/filters/test_inputs.py::test_build_input_class_returns_strawberry_input_decorated_dataclass tests/orders/test_inputs.py::test_input_type_name_for_returns_classname_inputtype tests/orders/test_inputs.py::test_camel_case_returns_input_when_split_yields_no_parts tests/orders/test_inputs.py::test_iter_orderset_subclasses_dedupes_diamond_inheritance tests/orders/test_inputs.py::test_order_input_type_returns_element_annotation_for_orderset_subclass tests/orders/test_inputs.py::test_order_input_type_is_idempotent_under_repeated_calls tests/orders/test_inputs.py::test_materialize_input_class_is_idempotent_on_same_pair tests/auth/test_mutations.py::test_same_args_factory_calls_dedupe_to_one_cached_holder tests/auth/test_mutations.py::test_declarations_survive_the_pre_bind_reset tests/auth/test_mutations.py::test_register_factory_recache_and_reregister_on_every_call tests/mutations/test_sets.py::test_registration_is_idempotent tests/forms/test_sets.py::test_plain_form_registration_is_idempotent` — reader-liveness witness re-run (26 passed); routes nowhere.
- `gate: heavy uv run python scripts/workspace.py prove dry/shared-helper-import-aliases/consolidate ~/dry/tmp/sha9/sha9-manifest.json` — failability re-run (3/3 pinned); routes nowhere.

## Judgment

Nine aliases, nine live, zero deletions. Census, liveness, and pinned
failability agree. Ready for verification.

## What shrinks

Nothing shrinks: zero 0-reader aliases, zero edits (net +0/-0). The
accounting, so no cycle re-derives it:

- Instrument A (AST, `~/dry/tmp/sha9/census_ast.py`): 503 `.py`
files, 503 parsed, 0 failures. Every Name/Attribute/import-from hit
classified: 9 definitions, 27 executable reads, 11 alias-imports
across 10 statements, 0 getattr, 0 star-imports into the flavor
modules. String hits were
substring traps (`auto_camel_case`), all defeated by instrument B.
- Instrument B (`rg -w`, `~/dry/tmp/sha9/rg_all.txt`): 148 lines =
26 package + 40 tests + 19 specs/builder/review prose + 63 prior dry
records. Examples 0, scripts 0. Specs name `_input_type_name_for` x2
(spec-027 `:378`/`:697`/`:887`; spec-028 `:346`/`:351`/`:353`/
`:600`/`:658`/`:672`/`:875`) and `_iter_orderset_subclasses`
(spec-028 `:353`, rationale `:27`); `_camel_case`,
`_iter_filterset_subclasses` and the three store handles appear in no
spec, board, or glossary line (only longer-name traps).
- Per-alias executable readers (defining line first, then readers):
  - filters `_camel_case` (`:84`): test import + 3 asserts
  (`test_camel_case_returns_input_when_no_word_characters`) + guard
  pin (`test_filter_and_order_families_share_one_substrate`).
  - filters `_iter_filterset_subclasses` (`:85`): test import +
  diamond test + guard pin.
  - filters `_input_type_name_for` (`:86`): `filters/__init__.py`
  `:41`/`:72`, intra-module `:1280`, guard pin
  (`test_filter_and_order_input_namespaces_ride_make_set_input_namespace`).
  - orders `_camel_case` (`:61`): test import + 3 asserts + guard pin.
  - orders `_iter_orderset_subclasses` (`:62`): test import +
  diamond test + guard pin.
  - orders `_input_type_name_for` (`:63`): test import + naming test
  (`:73`), `orders/__init__.py` `:33`/`:64`, intra-module `:277`,
  guard pin.
  - `_auth_declarations` (`:205`): test import + 5 asserts across
  dedupe/survive/recache tests.
  - `_mutation_registry` (`:766`): 2 test imports + 2 idempotency
  asserts (auth + mutations suites).
  - `_form_mutation_registry` (`:147`): test import + 1 idempotency
  assert.
- Package prose projecting the aliases (all true, all kept):
filters `:280`, orders `:12`/`:56-57`, forms `:131`/`:136`,
mutations `:582`/`:757`, substrate docstring `:15-19` and
`set_input_type_name` docstring `:117`. The filters covering comment
overclaims `factories.py` readership (D1); the orders comment
(`__init__` takes it, intra-module reads, tests address all five)
verified accurate line by line.
- Asymmetry verified: forms/rest/mutations `inputs.py` call the
public `graphql_camel_name` directly (no alias) and never saw the
set-only helpers — the alias block exists only where the substrate
was extracted from the families. No module uses both spellings: the
public names occur in the family modules only in imports + alias
right-hand sides. No drift.
- Liveness: 26/26 focused nodes green at live bytes (the Pending
execution witness). Failability: prove run `dry-20261012T023138`
3/3 pinned — camel→pascal mutant fails 2/2, naming→iterator mutant
fails 3/3 (guard + naming oracle + Decision-11 helper), `[]`
rebind fails `assert 0 == 1`; all baselines green, all post-run
bytes identical, copy clean after.
- Excluded scope untouched and un-relied-upon: connection
`_ends_in_unique_column`, `SyncMisuseError` re-exports, run-20
bound-`.clear` rows, extension twin aliases.

## Independent verification (Worker-2)

Written before reading `## Findings` (pass 1, address
`dry/shared-helper-import-aliases/verify-1`).

### Own census (WT == ITEM_BASELINE bytes on all 7 target files)

Baseline `942dfc3d` is a stash commit on HEAD `c37a08a0`; all 7
touched-path blobs are baseline==WT, HEAD differs by concurrent dirt
only, alias text identical. Item-scoped diff over touched paths is
empty (zero-edit; W1 wrote copy-only, nothing to port).

Instrument A (mine): `rg -n \bNAME\b` per spelling (artifact
excluded). Instrument B (mine): AST visitor over 505 repo `.py`
files (`.venv`/`__pycache__`/`docs`/`hunt-ws` skipped; 0 parse
failures) reporting ImportFrom/Name/Attribute, plus a separate
string-constant sweep. Traps defeated and quantified: naive
`_camel_case` = 28 files vs `\b` = 6 (`auto_camel_case` noise);
`clear_mutation_registry` / `*_declaration_registry` /
`_form_input_type_name_for` excluded by the same boundary. No
`as`-renames, no plain-`import` path hits, no `__all__` string
entries, no getattr readers, no examples/ or scripts/ hit.

Both instruments agree exactly: 26 package lines + 40 test lines;
27 executable reads + 11 alias name-imports across 10 statements:

- filters `_camel_case` (`:84`): test import + 3 calls in 2
behavior tests + `is` pin. Keep.
- filters `_iter_filterset_subclasses` (`:85`): test import +
diamond behavior test + `is` pin. Keep.
- filters `_input_type_name_for` (`:86`): production body
(`:1280` intra-module delegate pass; `filters/__init__.py` `:41`
import + `:72` body pass) + `is` pin; no filters-side behavior
test. Production-live. Keep.
- orders `_camel_case` (`:61`): function-local test import + 3
calls in 1 behavior test + `is` pin. Keep.
- orders `_iter_orderset_subclasses` (`:62`): test import +
diamond test + `is` pin. Keep.
- orders `_input_type_name_for` (`:63`): test import + naming
behavior test (`:73`) + production bodies (`:277`,
`orders/__init__.py` `:33`/`:64`) + `is` pin. Production-live. Keep.
- `_auth_declarations` (`:205`): test import + 5 asserts
(len x4, count x1) across dedupe/survive/recache tests.
Substantive. Keep.
- `_mutation_registry` (`:766`): 2 test imports + 2
idempotency count asserts (mutations + auth suites). Keep.
- `_form_mutation_registry` (`:147`): test import + 1
idempotency count assert. Keep.

Scratch-only readers (untracked `docs/dry/temp-tests/` from sibling
items: adjud2 head-tree copies, `p4_behavior.py`, probe attrs) are
ephemeral concurrent work, correctly out of population; committed
tree has no other reader. Untracked scratch will vanish at sibling
closeout and must never anchor a verdict.

### Own definition counts + owner

- C1 (owner behavior change: camel digit rule, dedup rule, naming
rule, registry mechanics): each alias is a zero-logic rebinding;
the change lands at the one owner, aliases follow by binding.
Count 1 per alias.
- C2 (owner rename): mechanical 1-token/site respell, no logic
moves. Count 1 definition.
- Owner choice: unchanged — `utils/inputs.py`,
`utils/strings.py`, `make_declaration_registry` already own; every
alias already composes by name (principle 6 satisfied). No
consolidation available.

### Own deletion search (one case per alias, each defeated or accepted)

- Test-only quartet (`_camel_case` x2, `_iter_*` x2): case =
migrate behavior tests to owner names + drop guard arms. Defeated:
bar fails (C1 count 1; zero-logic bindings remove no change
obligation); costs are spec/docstring/guard rewrites for net -4
lines. Trigger reopening it: a guard firing on drift (alias
growing its own logic) reopens as a drift consolidation, not a
deletion.
- Production pair (`_input_type_name_for` x2): case = re-point 4
production body sites to the owner + migrate the orders naming
test + drop 2 guard arms. Defeated: `__init__` imports are
body-used delegate args, not re-exports (zero downstream
importers from either package, both instruments); re-pointing the
`__init__`s still leaves the `inputs.py` aliases alive
(intra-module + spec + tests), so no deletion results; the edit
would falsify spec-027's alias table, spec-028 `:353` + the
`__init__`-tier sentence, and two substrate docstrings for zero
obligation relief. Trigger: Decision-11 helper removal AND spec
surface-list edits together (neither alone strands the alias).
- Store trio: case A (`.store`-direct respell) lengthens private
reach (registry object + attribute hop) for identical assertions
and contradicts the covering "backing list the tests introspect"
design. Case B (`iter_*()` snapshots) is behaviorally equal for
these count/len asserts but observes a snapshot, not the live
ledger the `DeclarationRegistry` docstring explicitly keeps the
`store` handle for ("for the tests that introspect it directly").
Both defeated on the bar (zero logic at the bindings; the quad +
`.store` remain either way). Trigger: a test needing live-list
mutation methods, or a second introspection binding over the same
store (a twin consolidation).
- No concrete above-bar deletion exists. Verdict per alias: keep 9/9.

### Own rulings (pre-findings)

- `is`-guard circularity: the guards pin a surface the project
treats as supported (substrate docstring `:16-19` addressability
declaration; spec-028 `:353` + rationale `:27` "addressable
surface" for the named ones; quad docstring + covering comments
for stores), and their stated contract guards SHARING (no
family-local copy), a real property. Not manufactured support.
Verdict-neutral either way: the bar fails on C1/C2 regardless,
and P11 keeps boundary names with dependent readers.
- Axis-1 asymmetry: real for camel/build spellings (forms
`:521`/`:592`, rest `:672`/`:677`/`:678`/`:1368`/`:1543`,
mutations `:616`/`:1060`, forms `:718` call owners directly);
absent for `_iter_*`/`_input_type_name_for` (no production caller
outside aliases + substrate). It retires any "package idiom"
framing — the block is set-family extraction-compat
addressability — but readers alone do not decide and neither does
asymmetry: the verdict rests on (bar fails on C1/C2) AND (P11
keep-clause: boundary names with readers). Both point to keep.

### Reconciliation (every difference vs `## Findings`)

Sites/roles/counts: exact match on all 9 aliases (lines, readers,
production-vs-test split). My instruments confirm W1's What-shrinks
numbers (27 reads, 11 name-imports / 10 statements; 26 package + 40
test `rg` lines) — which CONTRADICT W1's System-trace line ("28
reads + 9 imports", D-W2-1, verdict-neutral; the trace undercounts
imports by excluding the 2 production `__init__` statements and
overcounts reads by one).

- Mutations `:699`/`:792` (axis-1): reproduced (my first display
was `head`-truncated at 25 lines, not a census miss); both are
`graphql_camel_name` code calls, WT==baseline. Strengthens the
asymmetry point; verdict unchanged.
- Spec cites: my independent enumeration produced exactly W1's 10
lines (027 `:378`/`:697`/`:887`; 028 `:346`/`:351`/`:353`/`:600`/
`:658`/`:672`/`:875`) + rationale `:27`, each read in full; the
spec-silent five (`_camel_case` x2, `_iter_filterset_subclasses`,
3 stores) confirmed absent from specs/board/glossary. Exact match.
- `rg` totals 148 vs my 161: package 26 + tests 40 identical; the
13-line delta is docs prose (exclusion-set + concurrent doc
churn). File counts 503 vs my 505: concurrent untracked-`.py`
churn (9 untracked now; tracked 497); delta files reader-free.
Both verdict-neutral.
- Scratch readers under untracked `docs/dry/temp-tests/` (sibling
items) correctly out of population on both sides.

### Confirmation checklist

- Matrix: axis-1 cites verified (`:616`/`:699`/`:792` etc.);
asymmetry real for camel/build, absent for `_iter_*`/
`_input_type_name_for`; correctly scoped as family convention, not
package idiom. Axes 2/3/4/6 discharged as stated (no await
surface; pure `is`-pinned rebinds; no inverse halves; 9/9 with a
reader). Axis-5 cites verified textually above.
- Triggers: F1 triple-conjunction firable/measurable (guard diff +
prose diff + fresh census); F2's first conjunct is satisfiable in
principle via the existing public `iter_*()` snapshots (see
D-W2-3) but satisfying it still fails the bar, so the keep stands.
- Freshness: all 16 pins re-hashed exact, WT==baseline, zero
drift. Gap: `utils/strings.py` (camel owner) unpinned (D-W2-2,
verdict-neutral; cured here: `0b1774a`, WT==baseline).
- Pending: 2x `gate:` correctly typed (zero-edit keep has no
`proof:` obligation; witnesses only); manifest path live
(`sha9-manifest.json` + census/probe files present); 22/22 nodes
exist, incl. the 3 owner-direct tests; `routes nowhere` honest (a
`gate:` failure reopens no item).
- Coupling: none. D1: re-derived at HEAD+WT (filters imports only
`_build_input_fields`/`_build_logic_fields`; orders only
`_build_input_fields`), doc-only, homing non-blocking. Run-20
bound-`.clear` precedent confirmed in-plan (rows `:1720-1721`,
`:1888-1889`) and consistent (bind-don't-wrap mechanism).
- Prose rules: raw `:NN` allowed in `dry-*.md`; run ids/commands
are required evidence, not process provenance; link scaffold 10/10
headers, refs used; this append preserves the bottom block. Shape:
144-line body + uncapped What-shrinks; Run line matches the plan.
Ruff: no touched code paths (zero-edit; this `.md` append is not a
ruff target) — no run. No pytest per AGENTS.md (not asked;
inspection decisive; witnesses re-run at gate).

### Verdict-neutral record nits (cured in-record, no revision)

- D-W2-1: System-trace "28 reads + 9 imports" contradicts the
correct What-shrinks "27 + 11" (confirmed by both my instruments).
- D-W2-2: `utils/strings.py` missing from F1 freshness pins;
pinned here (`0b1774a`).
- D-W2-3: F1/F2 reason past the `iter_*()`-snapshot re-expression
without naming it, and "no public-name form exists" is true only
for the LIVE-LIST handle — public snapshot iteration exists and
is already used by sibling oracles in the same files. Defeated in
my deletion search (Case B): behaviorally equal for these asserts
but a different observation channel than the documented
direct-ledger introspection, and the bar fails regardless (C1
count 1; churn-only edit). Brief premise corrected accordingly:
no PUBLIC LIVE-LIST handle exists.
- D-W2-4: "out-of-fence prose" misnomer — rationale `:27`
(shipped-spec corpus) and sets `:582` / forms `:131` (in-population
package prose) are all rewordable in-fence (the bar MANDATES
same-change spec rewrites); the accurate frame is "deletion
strands N additional prose repairs" (cost). Prose is secondary:
the bar fails on C1/C2 regardless. Confirmed.

### Verdict: verified

Keep-all-9 stands. Independent census reproduces every reader; no
above-bar deletion exists (9 own cases + the `iter_*()` alternative
all defeated); matrix, triggers, freshness, Pending, D1, Coupling,
and prose/shape gates all confirm. Zero-edit: no `proof:` remains.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
