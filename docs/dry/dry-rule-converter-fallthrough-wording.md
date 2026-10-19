# DRY review: `converter-fallthrough-wording`

Status: verified
Run: 0.0.15 2026-10-11-18

## System trace

Question: one owner for the unsupported-field refusal wording (form
factory vs serializer factory vs types inline raise), or disprove.
Census (case-sensitive `rg`, package source): `Unsupported X field
type` = 3 messages + 1 docstring bullet; `no supported ancestor` = 2
messages + 3 docstrings; `has no mapping` = 2 messages (+1 unrelated);
`def convert_with_mro` = exactly 1 with 4 riders (form, serializer,
filter convert, filter normalize); `_class_map_lookup` = exactly 1
with 2 in-file call sites. The types raise carries no "no mapping /
no supported ancestor" sentence at all. Oracles + contract sources
(spec-036/037/038/039, GOAL.md) read; both exact-message asserts
byte-compared against the worktree constructions and match.
Attribution: all three targets dirty vs HEAD, every hunk matching
neither the ledger nor the cycle baseline (truth-read adoption +
`_class_map_lookup` extraction; `utils/truth.py` untracked) -- all
external, so all three paths STOP for edits and this verdict is
record-only; durable-home clause owed in Findings.

## Verification

### Matrix

1. **Cross-flavor mirroring** -- searched. Nouns + recourses are
   flavor-local (C2); shared mechanisms already single-owned upstream.
   No fourth flavor: package `Unsupported` census = these 3 sites.
2. **Sync/async twins** -- inapplicable: pure sync string-building at
   schema build; zero awaits in all riders, factories, raise (read).
3. **Derived knowledge** -- searched. Class-name read single-owned in
   `utils/truth.py` (call sites are consumers; worktree spelling
   variance external). "Which ancestor fired" = open `mro-map-key-lookup`
   (C5); other `truth.mro` users answer distinct questions (each read).
4. **Round-trip pairs** -- inapplicable: a raising fallthrough has no
   decode half; nothing parses these messages.
5. **Other media** -- searched. Oracles: 4 test modules (listed, not
   counted). Projections: spec-037 names the types head; specs pin the
   posture, not the sentences; docstrings restate posture (verified).
6. **Omission** -- searched. Every unmapped-field path raises (filter
   riders: unreachable-internal factory; `object` arm = specified
   totality). Mutations classifier is specified-total (refusal lands
   downstream); orders leaf has no refusal population. No gap, no defect.

### Challenges

| Id | Change posited | Definitions forced | Home |
|---|---|---|---|
| C1 | machine-readable code/shape on the refusals | 0 shared (3 single-expression f-strings; parameterizing every noun leaves no responsibility -- principle 11) | F1 reject |
| C2 | change one flavor's recourse vocabulary | 1 (that message alone; disjoint mechanisms) | F1 reject |
| C3 | change the identity-read rule | 0 here (`utils/truth.py` owns it; call sites consume; variance external) | F1 reject |
| C4 | change MRO discipline / catch-all posture | 0 here (`convert_with_mro` + per-caller wiring own it; sentence is projection, absent from types) | F1 reject |
| C5 | change the pure key-lookup firing rule | 0 here (1 def, 2 in-file consumers; skeleton leg differs: precheck-walk-raise vs sentinel-miss) | open `mro-map-key-lookup` |
| C6 | a fourth converter flavor | 0 here (supplies its own factory; skeleton absorbs riders) | F1 reject |

No executable probes: rejection rests on contract differences + trigger
checks (both exact oracles byte-compared statically and match).

## Findings

### F1 -- unsupported-field refusal wording (REJECTED as one rule)

- **Contract + variation.** Each converter refuses an unmapped field
  with a `ConfigurationError` naming field + class and offering the
  flavor's escape hatch. Varies per flavor on subject, self-name,
  middle sentence, recourse.
- **Sites + roles.** As one rule: 3 candidates. Verdict: 3 separate
  single-owned grammars, not one rule. *Consumer:* skeleton wiring
  (F-DISPATCH C3 confirmed fresh). *Oracles:* exact asserts in
  `tests/forms/test_converter.py` + `tests/types/test_converters.py`,
  `match=` heads in `tests/rest_framework/test_converter.py`,
  hostile-MRO end-to-end in `tests/utils/test_converters.py`.
  *Projections:* spec-037 head quote; posture docstrings.
- **Challenges.** C1-C4 + C6 (max count 1, on single-expression prose).
- **Owner + lifetime.** Standing: each flavor module owns its message
  (pure construction, nothing stored). Layering agrees (forms/types
  must not import DRF -- no flavor can host a shared template).
- **Migration.** None.
- **Distinct behavior.** (a) Subjects differ (whole-field `render` vs
  bound `field_name` vs `Model.field`). (b) Middle sentence in 2/3 only
  (types names the `SCALAR_MAP` hook). (c) Disjoint recourses:
  `input_class` merge, validated register + `Meta.fields/exclude`,
  `SCALAR_MAP` hook + `Meta.exclude`. (d) Shared "register a supported
  base" parses per flavor (subclass-only for forms -- no register fn;
  subclass-or-register for serializer). (e) Single f-strings.
  Converges: R-FALLTHROUGH, per-subject-rejection-grammars, e11.
- **Behavioral proof.** `static-reviewed` (rejection). Posture pinned by
  the catch-all-shadowing oracles (a base-`Field` row breaks them).
- **Negative control.** None (bypass not the threat; hostile-name
  containment single-owned upstream).
- **Coupling.** None. Durable-home clause OWED (factory docstrings sit
  in external hunks; land at closeout): "Refusal wording is per-flavor
  by design (`converter-fallthrough-wording`, rejected); only the
  fail-loud posture is shared (`utils/converters.py::convert_with_mro`).
  Reopen only on a cross-flavor diagnostic-normalization contract."
- **Freshness.** HEAD `c37a08a0`; ITEM `6ef1cade` (WIP stash on HEAD).
  Blobs: `52b10986`/`89edbc6e`/`d6e61cec`/`53ce2b2e`/`711352b1`(untr.)/
  `4114d171`/`072432e6`; oracles `17cf3658`/`f450459e`/`2cd066a7`/
  `be7d723c`. Population: `Unsupported` 9/6 files, `no supported
  ancestor` 5/2, `has no mapping` 3/3 (1 unrelated), `convert_with_mro`
  21/4 (1 def + 4 riders), `_class_map_lookup` 3/1, `truth.mro` users
  all read, `catch-all` 5 files, tables 26/12/16/1 re-derived.
- **Index row (Worker-0):** `converter-fallthrough-wording` |
  per-flavor (each converter module owns its message) | 3 converter
  files | Family `converter-fallthrough-wording` | rejected
  (single-expression triplet, per-flavor nouns/recourses; triggers:
  cross-flavor diagnostic-normalization contract, or a logic-carrying
  definition behind any message, or the subset-table trigger).

## Defects

None at HEAD bytes in scope. The worktree identity-read spelling
variance (one denoted value, three spellings) is uncommitted concurrent
work and routes to that flow's verification.

## Judgment

Three per-flavor refusal grammars, not one rule: subjects, self-names,
middle sentences, and recourses vary by population, each site is a
single f-string, and shared mechanisms are already single-owned
upstream. Rejected with triggers; zero-edit (paths STOPped on external
hunks; durable-home clause owed to closeout).

## What shrinks

- Rule: `converter-fallthrough-wording` -- REJECTED, no consolidation.
- Owner: unchanged -- each flavor module keeps its message.
- Net package lines over ITEM_BASELINE: +0/-0 (zero-edit; no tracked file touched).
- Deleted: nothing. Added machinery: none -- attested: no new helper, wrapper,
  constant, driver, registry, or mode flag; no test added (existing oracles
  already pin all three messages).
- Ruled out, so no cycle re-litigates it: a shared message template would
  parameterize flavor noun + subject + converter name + recourse -- the parameters
  ARE the message (principle 11: no abstraction with no responsibility). The split
  the brief ordered verified fresh: `convert_with_mro` is exactly 1 def with 4
  riders (control flow owned once); factories are per-caller definitions
  (F-DISPATCH C3, confirmed); the read-side `_class_map_lookup` is a different
  contract (sentinel-miss pure lookup, no prechecks, no raise) whose firing-rule
  question belongs to open family `mro-map-key-lookup` -- its new worktree shape
  (external hunk, already removed one same-file leg) is trigger-check input for
  that family's holder, not this item.
- Reconsideration triggers: (1) a cross-flavor diagnostic-normalization contract
  for build-time `ConfigurationError`s (the runtime `FieldError` envelope is a
  different medium and does not fire this); (2) a second logic-carrying definition
  behind any one message (code table / structured shape, i.e. gate-plus-declaration
  as in `seal-defect-code-wording`); (3) the `converter-table-separation` trigger --
  a new surface whose population is a SUBSET of an existing table's key space with
  identical value contract + lifecycle (census re-derived at current bytes:
  26/12/16/1, unfired).

## Independent verification (Worker-2)

Recorded before reading `## Findings` (expectation-first per `worker-2.md`).

### Own trace

Sites (worktree bytes; HEAD cross-checked per site): S1
`forms/converter.py::_unsupported_form_field` (fallthrough factory) +
`convert_form_field` (rider) + `_SCALAR_FORM_FIELDS` (12 rows) + 5 prechecks;
S2 `rest_framework/serializer_converter.py::_unsupported_serializer_field`
(factory) + `convert_serializer_field` (rider) + `_BUILTIN_SCALAR_CONVERTERS`
(16 rows) + live `_SERIALIZER_FIELD_CONVERTERS` + 6 prechecks; S3
`types/converters.py::scalar_for_field` inline raise + `_field_label` +
`SCALAR_MAP` (26 rows) + `FIELD_OUTPUT_TYPE_MAP` (2 rows) + `_class_map_lookup`
(worktree-only def, 2 in-file calls; absent at HEAD); S4
`utils/converters.py::convert_with_mro` (skeleton, exactly 1 def, 4 riders:
forms, serializer, filters convert + normalize) + `make_scalar_converter` /
`make_kind_converter` / `finish_field_conversion` / `MRO_CONTINUE`; S5
identity reads: HEAD `exceptions._safe_type_name` / `_safe_arg_repr`
(uniform across all three), worktree `truth.kind` / `truth.name` /
`truth.render` (`utils/truth.py`, untracked). Oracles:
`tests/forms/test_converter.py` full `==` (line 260),
`tests/types/test_converters.py` full `==` (line 2660),
`tests/rest_framework/test_converter.py` `match=` prefix only (lines 480,
1016, 2371 -- no full-equality oracle on the serializer fallthrough),
`tests/utils/test_converters.py` skeleton `match=` pins.

Roles: S4 skeleton = definition (dispatch mechanics, single-owned). S1/S2
factories + S3 inline raise = three wording definitions (one sentence each).
Tables = definitions, one per key space (`forms.Field` vs
`serializers.Field` vs `models.Field` -- never merged). Oracles =
independent (spell literals; none reads a registry). Module + factory
docstrings = projections (each already states its no-catch-all posture).

Definition counts per posited change: C1 error type/shape
(`ConfigurationError` -> coded envelope): 1 (the package type; raises are
consumers). C2 recourse vocabulary (reword "register a supported base
class"): 2 single f-strings (forms + serializer; types carries no such
sentence) -- count 2 but zero logic, below bar. C3 identity-read rule
(hostile `__name__` containment): HEAD 1 (`_safe_type_name` consumed by all
three); worktree 3 spellings proven behavior-identical (`truth.kind(f) ==
truth.name(type(f))` is True; `truth.render` of the name quotes like `!r`;
hostile `__class__` contained) -- owned by the concurrent truth migration,
routes there. C4 MRO-walk discipline: write flavors 1 (`convert_with_mro`);
types worktree 1 (`_class_map_lookup`, concurrent extraction); cross-layer
walk sharing is open family `mro-map-key-lookup` (f42, blocked), not this
item. C5 catch-all posture: 1 per layer, each recorded at its owner (skeleton
step 3 + three module docstrings); no second definition anywhere.

Owner I would choose: none for the wording -- rejection. The separation's
durable home is one clause at the skeleton (`convert_with_mro` step-3
paragraph, which already says "its own fallthrough error factory") naming
WHY plus the read-side exclusion; per-flavor docstrings already carry their
own no-catch-all sentences. Minimal complete shape: one skeleton clause (two
if `scalar_for_field` needs its own mirror -- judged after reading W1).

Verdict on one-rule-vs-three-grammars: three grammars. Forms/serializer
share a sentence shape but differ in self-name and second recourse
(`input_class` vs `Meta.fields/exclude` -- different extension contracts),
each a single f-string with no logic: below bar even as a pair. Types shares
no sentence; its recourse names a different extension mechanism (`SCALAR_MAP`
entry vs base-class registration): different contract. Soft-dep layering
bars a shared template: nothing all three can import without threading
flavor nouns as parameters (barred machinery), and
forms/types/utils never import `rest_framework` (one-direction graph
confirmed). No fourth refusal spelling package-wide (swept
`Unsupported .* field type`, `no supported ancestor`, `has no mapping`,
`register a supported base` at HEAD and worktree). No P11 deletion: the
factories are skeleton-mandated callables, and inlining them into lambdas
removes no change obligation while losing the docstring homes;
`list_field.py::_field_label` is a different contract (resolver-info label),
examined and excluded.

STOP pre-verdict (hunk attribution, own): every refusal-area hunk is
external. Forms: 2/2 hunks truth-adoption, zero ledger rows on the file.
Serializer: the `@@ -611` `_unsupported_serializer_field` hunk is
truth-adoption (body only; docstring lines clean but inside the dirty
function); ledger rows on the file (f35 `normalize_serializer_source`, batch
rows 42/43 prose) cover disjoint lines. Types: `@@ -375`
(`scalar_for_field` walk+raise), `@@ -325` (`_field_label`), `@@ -349`
(`_class_map_lookup` extraction) all truth-migration; batch rows 12/13 prose
cover disjoint lines. Cycle baseline names no package path. Scoped diff vs
`6ef1cade` over the 3 converters + tests + examples is EMPTY (re-ran
`git diff <baseline> -- <paths>` + name-status new-file check: both empty).
Line-level: serializer/types refusal docstrings and skeleton step-3 prose
are HEAD-clean lines, but the forms refusal docstring is dirty-external, so
no COMPLETE landing spot for a three-way clause exists now.

### Reconciliation with Findings (read after recording the above)

Confirmed fresh, no difference: exactly 1 `convert_with_mro` def with 4
riders (forms:267, serializer:579, filters:632/:747, HEAD-identical);
exactly 1 `_class_map_lookup` with 2 in-file calls (worktree-only, absent
at HEAD); types raise carries no mapping/ancestor sentence (sweep:
`no supported ancestor` only in forms+serializer); both full-`==` oracles
byte-match (forms:260, types:2660 -- re-proved by execution, 5 passed via
`heavy`; serializer correctly listed as `match=`-only); matrix 6/6
(axes 2+4 inapplicability sound: zero awaits; raising fallthrough has no
decode half and nothing parses the messages); no fourth spelling at HEAD
or worktree; soft-dep bar (forms/types/utils never import `rest_framework`;
DRF soft via `_DRF_SOFT_EXPORTS`); identity-read routing to the truth flow
(HEAD unifies all three on `_safe_type_name`; variance is worktree-only);
firing-rule routing to open f42; freshness 11/11 re-hashed
(52b10986/89edbc6e/d6e61cec/53ce2b2e/711352b1-untr./4114d171-filters/
072432e6-scalars.py + 4 oracles; HEAD `c37a08a0` unmoved); caps, prose
rules (no banned terms, no `path:NN`, `path::Symbol` cites), absent
`## Pending execution`, uncoupled findings.

Differences, all explicit: (D1) C1 count -- W1 "0 shared" vs my "1 (the
type)": yield to W1; for the WORDING rule the count is 0, my 1 was the
already-single package error type (consistent with rejection). (D2) C2
posit -- W1 "change one recourse" (1) vs my "reword the shared fragment"
(2 f-strings): both true; W1's C1 P11 argument (parameters ARE the message)
discharges my C2 -- below bar either way, converge. (D3) Census "1": my
re-derivation gives `FIELD_OUTPUT_TYPE_MAP` = 2 rows (HEAD==worktree, AST),
and no 1-entry dict exists in the five files -- the "1" matches nothing I
can find. Verdict-neutral record slip (T3's subset logic stands either
way); carried as CC-W2-1 for Worker-0 closeout (re-pin with the table
named). (D4) "Factory docstrings sit in external hunks": precision --
forms factory docstring IS dirty-external; serializer factory docstring and
`scalar_for_field` docstring are clean LINES inside externally-dirty
functions (types has no factory). Path-level STOP stands regardless: all
three files dirty-external with no covering ledger row (f35 + batch rows
cover disjoint lines; cycle baseline names no package path). W1's STOP
confirmed; zero-edit confirmed (scoped diff + new-file check both empty).

### Owed-clause judgment (Worker-2)

(a) TEXT: not signed as-is -- "Reopen only on [T1]" contradicts the three
triggers (T2/T3 also reopen). Corrected minimal text: "Refusal wording is
per-flavor by design (`converter-fallthrough-wording`, rejected); only the
fail-loud posture is shared
(`utils/converters.py::convert_with_mro`). Reopen on a cross-flavor
diagnostic-normalization contract, a logic-carrying definition behind any
message, or the subset-table trigger." (b) LANDING: three docstrings,
identical clause each (one-clause-or-three decided: three -- the types
reader never touches the skeleton, so a skeleton-only clause would miss
it; the skeleton itself needs no edit, it already says "its own
fallthrough error factory"): `forms/converter.py::_unsupported_form_field`
(anchor "stays in this module's wording"),
`rest_framework/serializer_converter.py::_unsupported_serializer_field`
(anchor "lives in this wording"),
`types/converters.py::scalar_for_field` (anchor "raises
``ConfigurationError`` for an unsupported field class"). (c) VEHICLE:
relaunch-after-settle -- new Worker-1 address when the truth migration
lands (trigger: all three refusal functions HEAD-clean + `utils/truth.py`
committed). Worker-0 closeout edit REJECTED (forms anchor dirty-external
NOW; every candidate file path-dirty under active rewrite -- landing now
edits around concurrent work). Defer-to-card REJECTED (no new rule; settle
needs no card). No `(Worker-2)` `## Defects` entries (CC-W2-1 rides here,
not Defects). Ruff: vacuous -- the item touched zero `.py` paths (no run;
none over `.`).

### Verdict

`verified`. Rejection stands with triggers; STOP correct; owed clause
scheduled as relaunch-after-settle with corrected text + three anchors
above. Staleness: any fingerprint change reopens.

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
