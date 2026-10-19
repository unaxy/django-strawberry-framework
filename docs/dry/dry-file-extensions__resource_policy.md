# DRY review: `django_strawberry_framework/extensions/resource_policy.py`

Status: verified
Run: 0.0.15 2026-09-18-1 (prior evidence only; run-7 re-trace appended at tail, `Run: 0.0.15 2026-09-29-7`)

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one REUSED plan family (trigger re-checked fresh on
current evidence — never inherited), a file-local record with its proving
challenge, or a recorded rejection with difference + trigger + home. Zero
production edits; zero tracked files changed.

## System trace

FRESH target, 1435 lines, 50 top-level statements: the request-side
enforcement half of the execution resource policy. It DEFINES the pre-parse
text scan ([extensions-resource-policy][extensions-resource-policy]`::scan_document_text`),
the post-parse document walk
([extensions-resource-policy][extensions-resource-policy]`::charge_document`
over `[extensions-resource-policy][extensions-resource-policy]::_DocumentBudget`
plus the schema-shape helpers), the argument-value walk
([extensions-resource-policy][extensions-resource-policy]`::_ValueBudget`
plus `[extensions-resource-policy][extensions-resource-policy]::_closes_a_cycle`),
the bind-spec bridge that classifies relation lists
([extensions-resource-policy][extensions-resource-policy]`::_mutation_input_specs`
plus `[extensions-resource-policy][extensions-resource-policy]::_nested_specs_map`),
the extension configuration record
([extensions-resource-policy][extensions-resource-policy]`::_AcceptedPolicy`
plus `[extensions-resource-policy][extensions-resource-policy]::_EXPLICIT_POLICY`),
the admission-verdict restatement
([extensions-resource-policy][extensions-resource-policy]`::restate_admission_verdict`),
and the two chain members
([extensions-resource-policy][extensions-resource-policy]`::DjangoResourcePolicyExtension`
plus `[extensions-resource-policy][extensions-resource-policy]::_AdmissionGuard`).
It CONSUMES by name the budget object half
([resource-policy][resource-policy]: 13 imported names — arm/read/verdict
seams plus the canonicalizer plus the copy), the operation-bound mechanism
([extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`),
the context mirror helper
([utils-context][utils-context]`::restored_context_keys`), the private
configuration carrier ([utils-private-state][utils-private-state]`::PrivateAuthority`),
the null-peeling helper ([utils-typing][utils-typing]`::unwrap_non_null`),
the relation-kind constant ([utils-inputs][utils-inputs]`::RELATION_MULTI`),
and the mutation-class marker
([mutations-fields][mutations-fields]`::MUTATION_CLASS_MARKER`). It does NOT
define the budget record, its domain gate, its resolution ladder, its
deadline, its row windowing, or its rejection constructor — those live at
[resource-policy][resource-policy], which this file imports one way (probe:
zero back-edge — the root module never names this one). It executes no
queryset, builds no row source, seals nothing, renders no `got` tail, logs
nothing, and awaits nothing. The module docstring additionally STATES the
hook-ordering boundary (admission ahead of the validation chain), the
transport reach (every operation on every transport), and the schema install
shape — the first two are owned here and verified against the hook bodies,
the install shape is projection of [schema][schema] (verified against its
chain builder, never counted).

Connected code read for judgment, outside the item:
[resource-policy][resource-policy] (full read — budget record, domain gate,
ladder, narrowing, authority lifecycle, deadline, both window colors,
rejection ctor; every seam below verified against its body);
[extensions-operation-state][extensions-operation-state] (base contract plus
`::OperationState.rebind_on_resume` body — mechanism-vs-consumer split
re-derived, single-registration claim verified by package-wide call census);
[extensions-error-policy][extensions-error-policy] (full read — the
enforcement twin compared pair by pair, not assumed);
[schema][schema] (chain builder plus declaration folding plus entry reads —
install + authority lines, bodies read);
[utils-policies][utils-policies] (full read — shared driver plus
canonical/copy bodies); [utils-private-state][utils-private-state] (settle /
recall bodies); [utils-context][utils-context] (`::restored_context_keys`
plus `MISSING` bodies); [utils-typing][utils-typing]
(`::unwrap_non_null`); [utils-inputs][utils-inputs] (`RELATION_MULTI`
spelling); [mutations-fields][mutations-fields] (`MUTATION_CLASS_MARKER`
spelling); [exceptions][exceptions]`::describe_value` (scope paragraph —
tail family difference); [extensions-init][extensions-init] (leaf manifest
plus install-rationale prose). Package-wide sweeps for a second definition
of every private helper (`_charge_*`, `_page_bound`, `_collection_rows`,
`_is_connection_type`, `_root_type`, `_field_definition`,
`_bounded_members`, `_closes_a_cycle`, `_ValueBudget`, `_DocumentBudget`,
`_AcceptedPolicy`, `_EXPLICIT_POLICY`, `Lexer(`): hits only here, at the
schema consumer, or in oracles/prose; the one `_root_type` hit outside is
`sets_mixins.py::_root_type_suffix`, an unrelated input-naming attribute
adjudicated by body, not a definition. Oracles
[test-resource-policy][test-resource-policy] (193 test functions; module
docstring tier split read — package-tier walker edge cases live here) and
the live wire matrix
[test-resource-policy-api][test-resource-policy-api] (90 tests over
`django.test.Client`; head + scaffolding read) plus
[test-operation-state][test-operation-state] (resumption rows for the
single registration). Contract source spec-047 cited only as a pointer
(defaults and boundaries pinned by oracles instead, bodies not relied
upon). Prior artifacts used only as rejected-candidate triggers, each
re-derived fresh from this side (the root artifact's J2 plus
driver/copy/tail sharing; its F1/F2/F3 consumer rows; the error-policy
artifact's J1 plus F3/F4 absence rows; the operation-state artifact's F1
mechanism-vs-override split plus F4 single-registration note). Never read
another worker's `worker-memory/`. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched and hold none of this finding's
sites; concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** No sibling flavor defines charging:
package-wide sweeps find the scan/walk/charge vocabulary (`Lexer(`,
`max_selections`, `_charge_*`, `_ValueBudget`, `_DocumentBudget`) only
here, at the schema consumer, or in oracles/prose. The flavors participate
by being CHARGED, never by charging: their mutation inputs are classified
through the bind-spec bridge whose PRODUCER lives in the write flavors
(`mutations/sets.py` stashes `cls._input_field_specs`; the form, serializer,
and auth flavors carry their own stash lines; every flavor's decode walks
the same records) while this file is the single CONSUMER that reads them
for budgeting. One bridge, producer at the flavors, reader here — C4
proves the split. The `package-root-public-surface` shape does not apply:
the leaf `__all__` mirrors same-file definitions in one edit region (same
difference the error-policy artifact records for its four names).
`awaitable-refusal-and-disposal` checked: 0 awaitable vocabulary (probe) —
no surface, do not inherit. Axis discharged.

**2. Sync/async twins.** No twin owed. Zero `AsyncFunctionDef`, zero
`await` (probe): both walks are iterative over explicit stacks, and all
four hooks are plain synchronous generators the engine enters on both
execution colors. The genuinely different work the package splits by color
— row-source windowing with iterator cleanup — lives at
[resource-policy][resource-policy]`::bounded_rows` /
`::bounded_rows_async`, never here; this file charges coerced-shape input
before any queryset exists (module docstring boundary, verified: no
queryset import, no row-source construction, exactly one prose `queryset`
stating the negative). `one-sync-boundary` checked: 0
`run_in_one_sync_boundary` / `sync_to_async` — the target performs no ORM
execution inside any hook, so there is no boundary to join; do not
inherit. The `islice` / `sys.maxsize` / `sys.get_int_max_str_digits`
tokens are docstring prose only (no `itertools` / `sys` import — probe);
the bounded read `[extensions-resource-policy][extensions-resource-policy]::_ValueBudget._bounded_members`
hand-rolls its loop so a hostile `__next__` becomes a typed rejection,
which is J3, not a twin. Axis discharged by absence with reason.

**3. Derived rather than repeated knowledge.** The policy is derived once
per operation: `[extensions-resource-policy][extensions-resource-policy]::DjangoResourcePolicyExtension.on_operation`
resolves the configuration a single time and arms the snapshot; every
later charge reads the armed object
([resource-policy][resource-policy]`::armed_resource_policy`), never the
configuration (both hook docstrings state the re-read hazard explicitly).
The only re-resolution sits on the documented off-scope fallback (a plain
`strawberry.Schema` whose consumer invokes the hook with nothing armed),
which answers exactly as arming would have — one derivation, one stated
fallback, not two owners. The open/close delimiter sets derive by
comprehension from the single pairs table (principle 2 in-file: one table,
two projections). The explicit policy is canonicalized once at acceptance
(`__init__` via [resource-policy][resource-policy]`::_operation_policy`),
never per read. No reconstructed copy found. Axis discharged.

**4. Inverse / round-trip pairs.** Four pairs, each one grammar with two
halves owned here or composed by name: `scan_document_text` /
`charge_document` (pre-parse text plus depth / post-parse selections plus
values — the spending twin of the root's budget halves; configuration vs
application split across the import edge, one way); `record` / `publish`
of the verdict (root owns both verbs;
`[extensions-resource-policy][extensions-resource-policy]::DjangoResourcePolicyExtension.on_parse`
is their single joint caller); `restate_admission_verdict` applied at its
two positions (own hook plus
`[extensions-resource-policy][extensions-resource-policy]::_AdmissionGuard`
— one body, two call sites, C7 proves the split); `_mutation_input_specs`
/ `_nested_specs_map` (top-level map / nested-level map — two levels of
one bridge, C4 proves the seam). `charge_selection` counts each alias WITH
its selection in one body, so the two counters cannot drift. No pair is
split across two owners. Axis discharged.

**5. Contracts restated in another medium.** Four media: production code
(the definitions); consumers composing by name (the schema installs both
chain members, folds declarations, and reads `_policy` through the
private record — bodies read; plain-schema consumers add the entry
explicitly); independent oracles
([test-resource-policy][test-resource-policy]: 193 rows including
walker edge cases — hostile containers, cycle closes, synthetic-list
coercion, per-field vs aggregate relation counters, upload-size refusals,
subclass-number discipline; [test-resource-policy-api][test-resource-policy-api]:
90 live rows, one narrowed bound family per mount; resumption rows in
[test-operation-state][test-operation-state]) — all spelling literals and
driving the public surface, none enumerating the owner's internals;
projections (module plus class plus method docstrings, spec-047 pointer,
leaf manifest, install-rationale prose). A charging change moves the
production owner once; oracles and prose follow as listed-never-counted
(every challenge below). Axis discharged.

**6. Enforcement by omission.** Three populations checked. (a) Operations
reached: passes 2–3 run at `on_parse`, which the engine enters whether or
not validation rules exist, on HTTP and subscribe alike (module boundary
prose; pinned live for HTTP by the 90-row matrix and package-tier for the
walker halves — the subscribe-path entry claim is static-reviewed prose,
stated honestly); pass 1 runs on every operation carrying a document.
(b) Chain position: admission is AHEAD of the validation chain by engine
ordering (every parsing hook finishes before any validation hook begins),
and the recorded verdict survives to the last word via the appended
`[extensions-resource-policy][extensions-resource-policy]::_AdmissionGuard`
(schema chain lines read: error masker, consumer entries, resource
extension, guard, mode marker). (c) Deliberate fallbacks, not gaps: the
off-scope `_resolved_policy` fallback (plain schema, nothing armed);
the raw-schema shared-instance limitation (documented in the class
docstring; corroborates the operation-state artifact's axis-6 row);
no deadline enforcement here (the deadline is the ROOT's seam —
`check_deadline` at the collection resolvers — and this file only
publishes its mirror through the arming call; the omission is the
budget/spend split, not a gap). No member lacks a guard its contract
requires; no defect, no card.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **50 top-level statements (0–49)** — plus, better than the
minimum, every body member of all 5 classes (11/4/2/9/2). Every member
lands below; every challenge in `### Challenges` ends in a family row, a
file-local row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (spend-side contract: three passes, transport reach, admission-ahead boundary, publish-vs-record split, raise-vs-publish split) | (none) | prose projection; hook order + reach owned here (R1/R2/R6), install shape projection of [schema][schema] |
| 1–18 | `__future__` + stdlib/upstream/first-party imports (18 `ImportFrom`, zero `Import`) | names | consumer bindings (F1 + R-rows per import: root 13 names, mechanism, mirror, carrier, null-peel, kind, marker) |
| 19 | `__all__ = ("DjangoResourcePolicyExtension",)` | 1-member manifest | R7 file-local (mirrors the error-policy leaf row's difference) |
| 20 | `_STRUCTURAL_DELIMITER_PAIRS` (3 bracket families) | token table | R1 file-local |
| 21–22 | `_OPEN_TOKEN_KINDS` / `_CLOSE_TOKEN_KINDS` (comprehensions over #20) | derived sets | R1 file-local (principle-2 derivation, not a second spelling) |
| 23–24 | `_ID_SCALAR_NAME` / `_UPLOAD_SCALAR_NAME` (wire-name fallback vocabulary) | 2 names | R3 file-local |
| 25 | `_STRAWBERRY_DEFINITION_BACKREF` (upstream extension key) | 1 key | R4 file-local (bridge machinery) |
| 26 | `_NODE_IDS_ARGUMENT` (`"ids"` query-side shape) | 1 name | R3 file-local |
| 27–28 | `_CONNECTION_MARKER_FIELD` / `_EDGE_MARKER_FIELDS` (connection shape) | shape test | R2 file-local |
| 29–31 | `_SCHEMA_META_FIELD` / `_TYPE_META_FIELD` / `_TYPENAME_META_FIELD` | 3 names | R2 file-local |
| 32 | `scan_document_text` | pre-parse scan | R1 file-local |
| 33 | `_mutation_input_specs` | top-level spec map | R4 file-local |
| 34 | `_nested_specs_map` | nested spec map | R4 file-local |
| 35 | `_EXACT_SEQUENCE_TYPES` (`list`, `tuple`) | owned-operation types | R3 file-local |
| 36 | `_closes_a_cycle` (`is`-identity ancestor guard) | cycle predicate | R3 file-local (+ J2) |
| 37 | `_ValueBudget` + 10 members (docstring, `__init__`, `_reject`, `_bounded_members`, `begin_mutation_field`, `charge`, `_charge_container`, `_charge_list_family`, `_charge_relation_ids`, `_charge_leaf`, `_charge_upload`) | value charges | R3 file-local (+ J3 for `_bounded_members`) |
| 38 | `_DocumentBudget` + 3 members (docstring, `__init__`, `charge_selection`, `charge_collection`) | shape charges | R2 file-local |
| 39 | `_root_type` | operation→root | R2 file-local (the `sets_mixins` hit is `_root_type_suffix`, adjudicated unrelated) |
| 40 | `_field_definition` (incl. introspection meta-field resolution) | field lookup | R2 file-local |
| 41 | `_page_bound` (exact-`int` variable read, ceiling fallback) | row bound | R2 file-local |
| 42 | `_collection_rows` (edges-list exception) | collection test | R2 file-local |
| 43 | `_is_connection_type` (whole edge-shape test) | connection test | R2 file-local |
| 44 | `charge_document` | post-parse walk | R2 file-local |
| 45 | `_AcceptedPolicy` + 1 member (docstring + `policy` field) | settled record | R5 file-local |
| 46 | `_EXPLICIT_POLICY` authority | config carrier | R5 file-local |
| 47 | `restate_admission_verdict` | verdict republish | R6 file-local |
| 48 | `DjangoResourcePolicyExtension` + 8 members (docstring, `_reconstruction_refusal`, `__init__`, `_policy`, `_resolved_policy`, `on_operation`, `on_parse`, `on_validate`, `on_execute`) | chain member | F1 (consumer) + R5 (config) + R6 (hooks) |
| 49 | `_AdmissionGuard` + 1 member (docstring + `on_validate`) | trailing guard | R6 file-local |

Rules: R1 pre-parse scan; R2 document walk; R3 value walk; R4 bind-spec
bridge; R5 extension configuration; R6 admission-verdict lifecycle; R7
leaf manifest plus vocabulary. Indexed families considered:
`operation-bound-extension-mechanism` (F1 — consumer, verified fresh),
`typed-rejection-value-tail` (F2 — checked, not a member and not a
consumer), `async-only-queryset-row-adapter` (F3 — checked, not a member),
`sealed-execution-queryset` (F4 — checked, not a member),
`one-sync-boundary` plus `awaitable-refusal-and-disposal` plus
`logger-single-sourcing` plus `soft-dependency-require-guard` plus
`subsystem-clear-lifecycle` (all absence probe-verified — Matrix axes 1–2;
every remaining indexed family has no vocabulary in this target on full
read: no filter/order/mutation/form/relay/registry/consumer/view/
request-body/auth machinery beyond the cited bridge reads). No new family
is named: every cross-file rule terminates in an already-indexed family
(F1–F4) and every other rule counts 1 with no second site; the three
considered shared forms are rejections (J1–J3).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 scan domain | charge a new pre-parse bound (e.g. per-variable payload bytes at the text stage) | **1** (the scan body; the policy field follows as declaration) | file-local |
| C2 | R2 spread accounting | spread fragments charged once per fragment instead of per spread site | **1** (`charge_document`; the per-site expansion is the contract the oracles pin) | file-local |
| C3 | R3 reference accounting | an already-charged container charged once on second reference (charge-once cache) | **1** (`_ValueBudget`; the walk docstring already refuses with the measured `id()`-reuse rationale) | file-local |
| C4 | R4 classification | classify relation lists by wire name only (drop the spec bridge) | **1** here (bridge fns plus `_charge_list_family`; the flavor decodes follow — the bridge exists so the budget cannot disagree with the decode) | file-local |
| C5 | F1 refusal | reword the base reconstruction refusal | **0** here / **1** at the base (proves override-not-copy); rewording this extension's string → **1** here | consumer |
| C6 | F1 resume registration | a second whole-operation value registers (e.g. the optimizer frame) | **0** new here / **1** at the state (the caller follows by name — the single call is a use, not a second registry) | consumer |
| C7 | R6 restate position | restate AFTER `yield` in `on_validate` | **1** (the hook body; `restate_admission_verdict` unchanged — position is the contract, and the last-word reason is stated where it is enforced) | file-local |
| C8 | R6 record/publish split | publish without recording (drop `record_admission_rejection`) | **1** (`on_parse`; the `ValidationCache`-overwrite disclosure returns — proves the split) | file-local |
| C9 | R5/R6 arming scope | resolve + arm per hook instead of once per operation | **1** (`on_operation`; every charge follows — proves the single-derivation) | file-local |
| C10 | R2/R3 bound rename | rename a bound (e.g. `max_aliases`) | **1** (the `ResourcePolicy` field; the `_reject` name strings plus attribute reads here follow as references, listed never counted) | file-local |
| C11 | over-bound comparison | flip `>` to `>=` in the exceedance test | held non-rule (see text): `>` is language semantics; the package rule (which counter vs which bound with what prose) is spelled once per site, and every site composes the root ctor by name | no second definition |
| C12 | cycle-guard shape | one shared charge-every-reference guard for fragment spreads and value containers | refused — J2 (name-domain expansion vs identity-domain walk; distinct termination arguments) | refused |
| C13 | enforcement halves | one shared request/response enforcement base beyond the mechanism | refused — J1 (opposite lifecycle positions, distinct policies and hooks; mechanism already shared at the base) | refused |
| C14 | `_bounded_members` refusal | propagate the container's raw error instead of the typed bound rejection | **1** either way (`_bounded_members`; the typed refusal IS the contract — a refusal to measure is a rejection of the bound being measured) — and no second measure-or-reject read exists, see J3 | file-local |
| C15 | F1 membership | a fifth operation-bound extension kind | **0** here / **1** at the new subclass declaration (proves the consumer role) | consumer |
| C16 | install position | the guard not last (or the extension not appended where it is) | **0** here / **1** at [schema][schema] (this file's install paragraphs are projection — proves prose-vs-owner split) | projection |
| C17 | entry refusal | a subclass entry admitted on `DjangoSchema` | **0** here / **1** at [schema][schema] (refusal owned at declaration folding; the class docstring describes it) | projection |

**Experiment.** Read-only probe (no source mutation, no Django setup, no
DB, no shared-tree pytest — the workspace recipe is for mutating proofs,
of which this zero-edit item has none):

```shell
python3 docs/dry/temp-tests/dry-file-extensions__resource_policy/probe_w1.py
```

Output (`W1 PROBE: ALL OK`, 44 checks): 50-member module AST with exact
kind sequence + 5-class body census (11/4/2/9/2); zero async defs, zero
`await`; zero family vocabulary for all fourteen absence probes (the one
`queryset` is module-docstring prose stating the negative); one
`rebind_on_resume` call, one scan call, one charge call, two restate
calls, one top-level spec call, three nested-spec calls, one settle, one
recall, one arm, one disarm; 13-name one-way root edge; one-member
manifest; refusal override present with no state factory and no
`_new_operation_state`; `islice`/`sys` prose-only; working blob ==
`HEAD:` blob == item-baseline blob; item-scoped diff empty; package
population 117. Status: `execution-verified` for every
identity/count/shape/absence/import claim below. Rejects the wrong results
"a 51st member exists", "an async twin is missing", "the seam restates the
mechanism", "a second registrar exists", "the target drifted from its
baseline". Bodies, seams, and oracle rows are `static-reviewed`.

## Findings

No production edit is owed by a file item; the one touched family below
is REUSED from the plan (trigger re-checked fresh on current evidence),
three more checked and held non-members, the rest are file-local records
and three recorded rejections.

### F1 — operation-bound extension mechanism (existing family `operation-bound-extension-mechanism`, consumer, status stays `open`)

- **Contract + variation.** One state object per (resolved extension,
  runner), composed by subclassing the base plus declaring the refusal
  string plus building (or inheriting) the state. This extension's
  composition, re-derived fresh (not inherited from the operation-state
  artifact): its own `_reconstruction_refusal` (the accepted-policy
  wording — an override, since C5 moves the base alone); NO state
  factory and NO `_new_operation_state` override (probe) — it uses the
  base `OperationState` directly, because it keeps no per-operation
  scratch beyond the budget the root half owns; exactly ONE
  `rebind_on_resume` registration call (probe: one AST call;
  package-wide census: the definition at
  [extensions-operation-state][extensions-operation-state]`::OperationState.rebind_on_resume`
  plus this call plus two docstring mentions — no second caller).
- **Sites + roles.** *Definition*:
  [extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`
  (unchanged). *Consumer verified here*: statements 18 (import), 48
  (subclass + refusal + `__init__` settle + `_operation_state()` read +
  the registration call). *Oracles*: resumption rows in
  [test-operation-state][test-operation-state] plus the budget-resume
  rows in [test-resource-policy][test-resource-policy] (cited, not
  re-litigated). *Projections*: the class docstring (entry-shape
  paragraphs — the `DjangoSchema`-vs-plain-schema split is owned at
  [schema][schema], described here).
- **Challenges.** C5, C6, C15 → 0 here / 1 at the owner or the new
  declaration each (proves consumer-by-declaration).
- **Index note for Worker 0 (additive only, never an edit by this
  worker).** The plan's index row already lists
  `extensions/resource_policy.py` under Files covered — verified-correct
  (probe: subclass + refusal + one registration call). No index change
  owed.
- **Trigger re-checked fresh.** A second registration call, a state
  subclass, or a carrier/managed/selection restatement appearing here
  would reopen. Swept: none (probe + package census).
- **Owner + lifetime.** [extensions-operation-state][extensions-operation-state]
  (unchanged). The settled `_AcceptedPolicy` lifetime: per extension
  instance under [utils-private-state][utils-private-state]`::PrivateAuthority`
  (settle-once at construction; recall per read) — filed under R5, not
  a second authority over operation state.
- **Migration / Coupling.** None.
- **Behavioral proof.** `execution-verified` for the census, the
  single-call count, and the no-factory shape (probe); `static-reviewed`
  for the base body plus the `on_operation` registration lines. Rejects
  "this extension redefines the mechanism" and "a second registrar
  exists".
- **Structural gate.** The existing resumption rows (a local copy of the
  binding would pass happy-path oracles and fail the nested/streamed
  isolation rows the owner adds) — pre-existing, no new gate owed by a
  file item.
- **Freshness.** Target
  `52084078ac166d8116b9e4bb2522e8ce193251ea`,
  [extensions-operation-state][extensions-operation-state]
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9`.

### F2 — typed rejection value tail (existing family `typed-rejection-value-tail`, checked, not a member and not a consumer)

- **Contract difference.** The family renders `got` tails for
  outside-package values through [exceptions][exceptions]`::describe_value`
  at transport-boundary and schema-construction refusal sites (scope
  paragraph read — this file is not among the named sites). This file
  renders no tail at all: zero `describe_value`, zero `got `, zero
  `ConfigurationError` (probe) — its thirteen `ResourceLimitExceeded`
  constructions carry literal per-bound prose, and the charged amounts
  are counters, widths, and sizes the walk produced (integers no
  consumer code answers for, per the `_reject` / `_charge_leaf` /
  `_page_bound` docstrings, which cite the root's exact-type discipline
  instead of rendering any outside value). Posit a hostile-tail change
  at the renderer → nothing here moves; posit C10/C14 here → no tail
  moves.
- **Reconsideration trigger.** A `got {describe_value(...)}` tail (or any
  `describe_value` call) appearing in this module — then it becomes a
  consumer row. Durable home: this finding + the tail owner; nothing
  here.
- **Freshness.** Target as in F1 (absence probe-verified) plus
  [exceptions][exceptions]
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` (scope paragraph).

### F3 — async-only queryset row adapter (existing family `async-only-queryset-row-adapter`, checked, not a member)

- **Contract difference.** The family spells async-only
  (`utils/querysets.py::is_async_only_iterable`) and carries sliced
  querysets through async completion (`::_AsyncQuerySetRows`). This file
  touches neither: zero `QuerySet` / `queryset` code vocabulary, zero
  `is_async_only_iterable` / `normalized_row_source` /
  `_AsyncQuerySetRows` (probe) — it charges coerced-shape input before
  any queryset exists and awaits nothing. The plan index row's
  `resource_policy.py` is the ROOT file (verified: the root consumes
  the predicate in `::_windowed_rows_async` and the rebuild in
  `::_windowed_rows` — root artifact F2/F3, re-checked, not re-litigated).
  Posit C13 at the owner (drop the `not Iterable` half) → the root's
  async window plus the list-field branch follow; nothing here moves.
- **Reconsideration trigger.** Any async-iterator dispatch, queryset
  read, or row-source construction appearing in this module.
  Durable home: this finding + the adapter owner; nothing here.
- **Freshness.** Target as in F1 (absence probe-verified).

### F4 — sealed execution queryset (existing family `sealed-execution-queryset`, checked, not a member)

- **Contract difference.** The family rebuilds framework-owned plain
  querysets from validated state at execution boundaries
  (`utils/querysets.py::_seal_or_defect`). This file seals nothing and
  executes nothing: zero `seal` tokens (probe); the single `queryset`
  is the module docstring stating the negative ("no queryset is built
  before it either passes or rejects") — projection of the
  budget/spend boundary the root owns, not a seal. A sealing change
  moves the seal sites; nothing here does.
- **Reconsideration trigger.** Any queryset read, seal, or visibility
  check appearing in this module. Durable home: this finding + the seal
  owner; nothing here.
- **Freshness.** Target as in F1 (absence probe-verified).

### File-local records (no second definition after the matrix)

- **R1 — pre-parse text scan.**
  `[extensions-resource-policy][extensions-resource-policy]::scan_document_text`
  (whole-document token + bracket-depth charge before the parse, with the
  malformed-document and non-text-input declines) over the pairs table
  (#20) with the derived open/close sets (#21–22). C1 → 1. The only
  `Lexer(` in the package (sweep). Trigger: a second raw-document scan
  would make it a family. Freshness: target.
- **R2 — document walk.**
  `[extensions-resource-policy][extensions-resource-policy]::charge_document`
  (named-operation-only fragment-expanding walk with spread-path
  cycle guard) over
  `[extensions-resource-policy][extensions-resource-policy]::_DocumentBudget`
  (selection + alias + multiplicative collection counters),
  `::_root_type`, `::_field_definition` (with the introspection
  meta-field resolution), `::_page_bound` (exact-`int` variable read
  with ceiling fallback), `::_collection_rows` (the edges-list
  exception), `::_is_connection_type` (whole edge-shape test), plus the
  connection (#27–28) and meta-field (#29–31) vocabulary. C2, C10 → 1
  each. Trigger: a second fragment-expanding charge would make it a
  family. Freshness: target.
- **R3 — value walk.**
  `[extensions-resource-policy][extensions-resource-policy]::_ValueBudget`
  (iterative stack with ancestor-path identity guard, every-reference
  charging, synthetic one-item-list coercion, five family classifier
  `::_charge_list_family` with the per-field + aggregate relation
  counters `::_charge_relation_ids`, byte-size leaves `::_charge_leaf`,
  upload charging `::_charge_upload`) plus
  `::_closes_a_cycle`, `::_EXACT_SEQUENCE_TYPES`, and the ID/Upload/ids
  vocabulary (#23–24, #26). C3, C4, C14 → 1 each here. Trigger: a
  second input-cardinality walk would make it a family. Freshness:
  target.
- **R4 — bind-spec bridge.** `::_mutation_input_specs` (one call site:
  per top-level mutation field in `charge_document`) plus
  `::_nested_specs_map` (three call sites: synthetic item, mapping
  child, list item — one body, three positions in the same walk) over
  the `_STRAWBERRY_DEFINITION_BACKREF` key (#25), reading the flavors'
  `_input_field_specs` through
  [mutations-fields][mutations-fields]`::MUTATION_CLASS_MARKER` and the
  [utils-inputs][utils-inputs]`::RELATION_MULTI` kind. C4 → 1 here
  (producer flavors follow as listed-never-counted). Trigger: a second
  reader of the bind specs for a different purpose would make it a
  family. Freshness: target plus [utils-inputs][utils-inputs]
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` plus
  [mutations-fields][mutations-fields]
  `cf518361d7884b8b71550cb6b73bff0c1a64549e`.
- **R5 — extension configuration.**
  `::_AcceptedPolicy` / `::_EXPLICIT_POLICY` (settle-once construction
  record distinguishing configured-without-override from
  never-constructed) plus `::DjangoResourcePolicyExtension.__init__`
  (canonicalize at acceptance via
  [resource-policy][resource-policy]`::_operation_policy`), `::_policy`
  (copy-out through the authority — the seam
  [schema][schema]`::_entry_resource_policy` reads by name), and
  `::_resolved_policy` (explicit else schema else default, once per
  operation). C9 → 1. Trigger: a second configuration carrier for this
  extension would make it a family. Freshness: target plus
  [resource-policy][resource-policy]
  `647133d23785d325856b2d1d495d18c5741dd23c` plus
  [utils-private-state][utils-private-state]
  `08088b820ac20579e471915644a931953362fca8` plus [schema][schema]
  `2f72732123ca1156c4eb122ce7b53de6269de95e`.
- **R6 — admission-verdict lifecycle.** `::restate_admission_verdict`
  (one body, two positions: own `on_validate` plus
  `::_AdmissionGuard.on_validate`) plus the four hooks (`on_operation`
  arms/scans/restores with the single resume registration;
  `on_parse` records + publishes + empties validation rules — the only
  production caller of each; `on_validate` restates before yield;
  `on_execute` refuses the rejected) over the
  [utils-context][utils-context]`::restored_context_keys` mirror scope.
  C7, C8 → 1 each. Trigger: a second verdict channel for the same
  operation would make it a family. Freshness: target plus
  [resource-policy][resource-policy] as in R5 plus
  [utils-context][utils-context]
  `cd0adcc509a3a40e5b46ba761c6cbfec2c44359c` plus [schema][schema] as
  in R5 (chain lines).
- **R7 — leaf manifest plus vocabulary.**
  `__all__` (1 name; the class exported, every helper private — the
  same privacy the extensions leaf row records from its side). C10
  name-reference reasoning applies. Trigger: a second manifest over
  this name would make it a family. Freshness: target plus
  [extensions-init][extensions-init]
  `dc3ebdc24b4817a64ea360d92bbbed340ad30bcc`.

### J1 — error/resource enforcement unification (refused shared form, corroborated from THIS side)

Both enforcement halves carry an extension, a policy object, and a
schema install — the symmetry the matrix compared, not assumed. Pair by
pair from THIS side: resolution ladders already share
[utils-policies][utils-policies]`::resolve_policy` (C6 at the root
artifact proves it); copies share `::copy_policy` (R5 reads through
it); tails share [exceptions][exceptions]`::describe_value` (F2 proves
the non-membership); the per-operation mechanism shares
[extensions-operation-state][extensions-operation-state]`::_OperationBoundExtension`
(F1 — the composition, already the DRY answer). What remains per side
is distinct mechanism, not shared vocabulary: pre-execution budget
gating over `on_operation` / `on_parse` / `on_validate` / `on_execute`
with append-to-setup-last plus a trailing guard vs post-execution
message rewriting in one `on_operation` teardown with
prepend-to-tear-down-last; ~20 numeric bounds with a deadline plus
narrowing plus windowing on the resource side vs three string/bool
options with a neutral message on the error side. Posit C13 (one base
enforcement class): a change to either side's hooks (C7/C8 vs the
teardown shape) moves exactly one body today, and swapping install
positions breaks both lifecycles in opposite directions (each module
docstring records the other's direction). Unifying the pair would
couple a request gate to a response rewrite across inverse orderings.
Reconsideration trigger: a third enforcement extension arriving with
the identical resolve→install→enforce shape — then the SHAPE (not the
policies) becomes a family with the schema chain as its owner (rides
the error-policy artifact's J1 trigger verbatim). Durable home: this
finding + each module's install-position paragraph (both already record
the other's direction; no edit owed). No new index row today.

### J2 — charge-every-reference cycle guards (refused shared form, recorded here)

`charge_document` guards fragment cycles by spread-path membership
(`name in path`, `path | {name}` — names, charged at every spread
site) while `_ValueBudget` guards value cycles by ancestor identity
(`_closes_a_cycle` — `is`, every reference charged except the
cycle-closing one). Considered: one shared guard. Refused: distinct
identity domains with distinct termination arguments — posit C2
(charge-once-per-fragment) → only the walk moves; posit C3
(charge-once-per-container) → only the budget moves, whose docstring
already states why identity (not `id()`) is the guard. A shared helper
parameterized by "identity" would abstract the whole content of each
(the name expansion on one side, the liveness-scoped `is` scan on the
other) while coupling AST traversal to value traversal across
different reasons to change. Reconsideration trigger: a third
charge-every-reference walk (e.g. over directive arguments) — then the
GUARD SHAPE becomes a family owned here. Durable home: this finding
plus both docstring paragraphs (both already state their
charge-every-reference rule; no edit owed). No new index row today.

### J3 — measure-or-reject vs truncate (refused shared form, recorded here)

`_ValueBudget._bounded_members` reads an exotic container one member
past the width bound and turns ANY measurement failure into a typed
`ResourceLimitExceeded` for the bound being measured; the root's
`_windowed_rows` truncates response rows with `list(islice(...))` and
lets resolver-iteration failures propagate as resolver failures.
Considered: one "bounded iteration" helper. Refused: opposite failure
contracts with opposite reasons — a measurement the admission stage
cannot take is a refusal OF that stage (nothing may execute on an
unmeasured charge), while a row source failing mid-response is the
resolver's failure to report, not a bound to reject on. Posit C14 →
only `_bounded_members` moves; posit propagating a truncation error →
only the root moves. Reconsideration trigger: a second
measure-or-reject read (a value measurement outside the value walk)
— then the refusal becomes a family owned here. Durable home: this
finding plus the `_bounded_members` docstring paragraph (already states
the rule; no edit owed). No new index row today.

## Defects

None. Every claim checked while tracing held: the one-way import edge
(13 names in, zero back); the single registration call (package census);
the single arm/disarm pair (only production `begin_resource_budget`
caller; tests arm directly as oracles); the two-position restatement
over one body; the one top-level spec call plus three nested-spec
calls over one body each; the chain order (masker, consumer entries,
resource extension, guard, mode marker — schema lines read); the
refusal-only + base-state consumer shape (no factory, no
`_new_operation_state`); the off-scope fallback answering as arming
would; the axis-6 sweep finding no member lacking a guard its contract
requires (fallbacks and omissions are contract-sourced in the bodies).
(Static review beyond the probe — no shared-tree pytest per item rules;
oracle bodies cited above are `static-reviewed`.) Nothing routed to any
owner.

- **(Worker 2) R4 freshness transposition (artifact, not package).**
  `### Findings` R4 attributes `ee31d360…` to
  [mutations-fields][mutations-fields] and `cf518361…` to
  [utils-inputs][utils-inputs]; the tree hashes the reverse
  (content-verified: `RELATION_MULTI` in utils/inputs,
  `MUTATION_CLASS_MARKER` in mutations/fields; both blobs clean at
  HEAD). Routes to this item's pass-2 resubmission (swap the two
  hashes, re-run the unchanged probe) — sole revision driver, see
  `## Independent verification (Worker 2)`.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
package-wide name sweeps, command in `### Challenges`) already ran green
against the shared tree; they mutate no source, open no database, and
import no Django, so no workspace copy was owed and no `__file__`/DB
`NAME` record applies. No pytest was run in the shared tree, per item
rules; oracle bodies are `static-reviewed`. No `execution-deferred`
items. No `FAKESHOP_SHARDED` or Postgres cell is owed: the target's code
path reaches no database, alias, or dialect decision
(`inapplicable by construction` — graphql-core lexer/AST walk plus
ContextVar/lease/token binding; the only Django-adjacent reads are the
mutation-class marker and kind constant, never the ORM).

## Judgment

Backstop discharged: 50/50 `ast.Module.body` members enumerated plus all
5 class bodies (11/4/2/9/2), 17 challenges run, every rule terminating
in the one reused family it composes (F1
`operation-bound-extension-mechanism` — consumer: refusal-only, base
state, single registration call, C5/C6/C15 at 0 here), a checked
non-member with difference + trigger (F2 tail, F3 adapter, F4 seal —
all at 0 with the root file adjudicated as the actual index member),
a file-local record with its proving challenge (R1–R7, C1–C4/C7–C10/C14
at 1), a held non-rule with its reasoning (C11), or a recorded
rejection with difference + trigger + home (J1–J3). The J2 unification
question is answered fresh from this side: the spend half spends what
the root half owns across a one-way import edge (configuration vs
application, not duplication), and the driver/copy/tail sharing the
root item records is corroborated (resolve driver, `copy_policy`,
`describe_value` — each consumed here by name or provably absent).
No consolidation owed (composition is already by name on every edge),
no defect found, no new family named, no pending execution. Zero-edit
result is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: every
family this target touches is already indexed (F1 carries no index
change — the row already lists this file; F2–F4 need none; J1–J3 live
at their owner paragraphs plus these findings).

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `f4142bcc170c06939c9d0bedafc70374018a17ff`:
`git diff <baseline> -- django_strawberry_framework/extensions/resource_policy.py`
empty (0 bytes, probe `w1-item-diff-empty`); working blob
`52084078ac166d8116b9e4bb2522e8ce193251ea` equals the item baseline, the
cycle-baseline member, and `HEAD:` — target CLEAN, so no hunk
attribution was owed. The artifact itself
(`docs/dry/dry-file-extensions__resource_policy.md`) is a new untracked
file, the item's only output besides scratch. `uv run ruff format` plus
`ruff check --fix` ran on the probe path only (explicit path, untracked
scratch — never repo-wide, so no concurrent work was touched; 6 remaining
annotation/docstring nits are scratch-exempt style, probe still green).
No shared-tree pytest run. Untracked scratch
created (not tracked changes): the read-only probe
`docs/dry/temp-tests/dry-file-extensions__resource_policy/probe_w1.py`
(`W1 PROBE: ALL OK`, 44 checks; no source mutation, no Django import, no
DB, no shared-tree pytest). Concurrent dirt listed in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus the
other untracked `dry-file-*.md` artifacts were left untouched; the
`## Owned changes` ledger (walker D1 fix + 2 live test files) gains no
row from this item. No commit.

## Independent verification (Worker 2)

Read order kept: AGENTS.md, DRY.md (canonical), worker-2.md, plan item
(File `extensions/resource_policy.py`, Run `0.0.15 2026-09-18-1`), the
complete target (1435 lines — `wc -l` confirms), the item-scoped diff,
consumers/tests of the touched sites, then this artifact. Never
worker-memory. No pytest run (not authorized); the read-only probe
re-run below mutates nothing, imports no Django, opens no DB.

### Own trace (derived before opening `## Findings`)

The target is the spend half of the execution resource policy; the
budget half lives at [resource-policy][resource-policy]. Own rules,
posited changes, definition counts, and the owner I would choose:

- **V1 pre-parse scan.** `scan_document_text` + `_STRUCTURAL_DELIMITER_PAIRS`
  with the two derived kind sets. Change: a new pre-parse bound →
  **1** (the scan body). Owner: this file. (W1 R1 — agree.)
- **V2 document walk.** `charge_document` + `_DocumentBudget` +
  `_root_type` + `_field_definition` + `_page_bound` + `_collection_rows`
  + `_is_connection_type` + connection/meta vocab. Changes: per-spread-site
  accounting → per-fragment (`charge_document` only, **1**); a renamed
  bound (`max_aliases`) → **1** at the `ResourcePolicy` field, name
  strings here follow as references. Owner: this file. (W1 R2 — agree.)
- **V3 value walk.** `_ValueBudget` (10 methods + docstring) +
  `_closes_a_cycle` + `_EXACT_SEQUENCE_TYPES` + ID/Upload/`ids` vocab.
  Changes: charge-once cache → **1** (`_ValueBudget`; the `id()`-reuse
  rationale is already in its docstring); typed refusal → raw error →
  **1** either way (`_bounded_members` IS the contract). Owner: this
  file. (W1 R3 — agree.)
- **V4 bind-spec bridge.** `_mutation_input_specs` (1 call site) +
  `_nested_specs_map` (3 call sites, 1 body) over the backref key, reading
  the flavors' `_input_field_specs` via
  [mutations-fields][mutations-fields]`::MUTATION_CLASS_MARKER` and the
  [utils-inputs][utils-inputs]`::RELATION_MULTI` kind. Change: drop the
  bridge, classify by wire name → **1** here (bridge + classifier;
  flavor decodes follow listed-never-counted). Producer at the flavors,
  single consumer here. Owner of the bridge: this file. (W1 R4 — agree
  on substance; freshness labels transposed — see `### Freshness`.)
- **V5 configuration.** `_AcceptedPolicy` + `_EXPLICIT_POLICY`
  (settle-once / recall-per-read) + `__init__` (canonicalize at
  acceptance) + `_policy` (copy-out) + `_resolved_policy` (once per
  operation). Change: arm per hook → **1** (`on_operation`). Owner:
  this file for the record;
  [extensions-operation-state][extensions-operation-state] for the
  mechanism. (W1 R5 — agree.)
- **V6 verdict lifecycle.** `restate_admission_verdict` (1 body,
  2 positions: own `on_validate` + `_AdmissionGuard.on_validate`) +
  4 hooks + context-mirror scope. Changes: restate after `yield` →
  **1** (position is the contract); publish without recording → **1**
  (`on_parse`, the `ValidationCache`-overwrite returns). Owner: this
  file. (W1 R6 — agree.)
- **V7 manifest.** `__all__` (1 name). Owner: this file. (W1 R7 — agree.)
- **V8 operation-bound mechanism.** Refusal override + base state +
  exactly **1** `rebind_on_resume` call (package census: definition at
  [extensions-operation-state][extensions-operation-state]`::OperationState.rebind_on_resume`
  + this call + 2 docstring mentions; no second caller — re-derived).
  Changes: reword base refusal → **0** here / **1** at base; second
  registrar → **0** new here / **1** at state; fifth extension kind →
  **0** here / **1** at the new declaration. Consumer, owner at the
  base. (W1 F1 — agree.)

Reconciliation: V1–V8 match W1 R1–R7 + F1 one for one. No rule I found
lacks a W1 home; no W1 home lacks evidence. Differences: (a) R4
freshness transposition (revision driver, below); (b) oracle phrasing
caveat (below); (c) "10/8 members" prose is a consistent
non-docstring-member convention, not an error — withdrawn as a nit.

### Enumeration (member by member vs own count)

Own instrument: `ast.parse`, `len(ast.Module.body)` = **50**; class
bodies `_ValueBudget` **11**, `_DocumentBudget` **4**, `_AcceptedPolicy`
**2**, `DjangoResourcePolicyExtension` **9**, `_AdmissionGuard` **2**
— all match W1's 50 + 11/4/2/9/2. Kind sequence matches the probe's
pinned sequence (`Expr` + `ImportFrom` x18 + 4 table/derived assigns +
9 name assigns + 3 `FunctionDef` + assign/function/class/class + 6
functions + class/annassign/function/class/class). Every member lands:
#0 prose (R1/R2/R6 + schema-install projection); #1–18 consumer
bindings (13-name root edge verified below, rest per import); #19 R7;
#20–22 R1; #23–24 + #26 + #35 R3; #25 #33–34 R4; #27–31 + #38–44 R2;
#36–37 R3 (+J2/J3); #45–46 + `__init__`/`_policy`/`_resolved_policy`
R5; #47–49 R6; #48 also F1-consumer. The `sets_mixins.py` `_root_type`
hit is `_root_type_suffix` (input-naming attribute, body-adjudicated
unrelated — verified). The one `queryset` token is docstring prose
stating the negative. Agree with W1's table in full.

### Matrix (vs real surface)

1. Cross-flavor — agree. `Lexer(`, `_ValueBudget`, `_DocumentBudget`,
   `_charge_*`, `max_selections` occur only here, at the schema
   consumer, or in oracles/prose (package sweeps). Flavors stash specs;
   only this file reads them for budgeting (C4/V4). Zero awaitable
   vocabulary in target (own grep).
2. Sync/async — agree, absence with reason. Zero `AsyncFunctionDef`,
   zero `await`; walks are explicit-stack iteration; hooks are sync
   generators. Color-split row windowing lives at the root
   (`bounded_rows` / `bounded_rows_async` — read); `islice`/`sys` are
   prose-only (no imports). No ORM execution in any hook → no
   `one-sync-boundary` surface.
3. Derived-once — agree. Single resolve + arm in `on_operation`; all
   charges read `armed_resource_policy()`; the plain-schema fallback
   answers as arming would (stated in both hook docstrings). Delimiter
   sets derive from the pairs table (principle 2 in-file).
   Canonicalization at acceptance, never per read.
4. Round-trip — agree. Four pairs, each one grammar: scan/charge halves;
   record/publish (single joint caller `on_parse`); restate body at two
   positions; top/nested spec maps. `charge_selection` counts alias with
   its selection in one body (read).
5. Other media — agree with one phrasing caveat. Oracle counts
   re-derived: [test-resource-policy][test-resource-policy] **193**
   test functions, [test-resource-policy-api][test-resource-policy-api]
   **90**, [test-operation-state][test-operation-state] 46. Caveat: one
   package-tier test imports the private `_field_definition` directly
   (None-parent shape, literal `is None` expectation) — so "none
   enumerating the owner's internals" overstates slightly; the DRY
   property still holds (expectations are spelled literals, the test
   fails if the owner breaks, and no oracle was rewritten in this
   zero-edit item). Consumers compose by name (schema installs both
   chain members, folds declarations via `_entry_resource_policy`
   reading `_policy` — body read); projections are docstrings + leaf
   manifest + spec-047 pointer.
6. Omission — agree. Passes 2–3 at `on_parse` (engine enters with or
   without validation rules, both transports); pass 1 on every
   document-carrying operation; admission ahead of the validation chain
   by engine ordering with `_AdmissionGuard` last (chain order read:
   error masker, consumer entries, resource extension, guard, mode
   marker); fallbacks (off-scope resolve, shared-instance limit, no
   deadline here — root's `check_deadline` seam) are contract-sourced
   in the bodies. Subscribe-path entry honestly marked static-reviewed.
   No missing-guard defect.

### Counts + roles

Definition counts V1–V8 confirmed as above (C11 held non-rule: `>` is
language semantics — agree, with reasoning). Roles: definitions here
(R1–R7) except the mechanism base (F1 definition at operation-state,
this file consumer); schema entries are consumers; the 193/90/46 rows
are oracles (caveat above); docstrings/manifest/spec pointer are
projections. No oracle rewritten (zero production edits; zero test
edits).

### Equivalence (principle 8)

Zero-edit item: no observable behavior can change. Inspection basis per
rule — short-circuit order, exceptions (`ResourceLimitExceeded` raise
vs publish sites), transaction effects (none — no ORM), the arming
point where policy is observed (single `on_operation` scope) — all
read at the bodies; nothing reordered, no predicate split or hoisted.
Probe (`W1 PROBE: ALL OK`, 44 checks) re-run green — see `### Scratch`.

### Zero-edit + families

Item-scoped diff confirmed empty by hand: `git diff
f4142bcc170c06939c9d0bedafc70374018a17ff --
django_strawberry_framework/extensions/resource_policy.py` = 0 bytes;
working blob `52084078ac166d8116b9e4bb2522e8ce193251ea` == `HEAD:` ==
item-baseline blob; target CLEAN (1435 lines). Coverage: 50/50 +
5/5 class bodies, all assigned; 17 challenges all homed. No new family
owed. F1 reused-consumer — agree (single registration census
re-derived). F2 tail — agree non-member/non-consumer (zero
`describe_value`/`got `/`ConfigurationError` in target; 13 rejections
carry literal prose). F3 adapter — agree non-member, and W1's
adjudication is CORRECT: the plan index row's `resource_policy.py` is
the ROOT file (root imports `is_async_only_iterable`, uses it in
`_windowed_rows_async` + `_windowed_rows`; extensions file has zero
queryset/adapter hits). F4 seal — agree non-member (zero `seal`
tokens; single `queryset` is the negative-stating prose).

### Rejections

J1 (enforcement unification) — agree: pair-by-pair corroborated from
this side (single-`on_operation` error half with zero `max_*` vs four
hooks + 53 `max_` hits here; resolve/copy/tail/mechanism already
shared by name). Difference + trigger (third enforcement extension →
shape family at the schema chain) + home (both install paragraphs)
present. J2 (cycle guards) — agree: name-domain vs `is`-identity
domains, distinct termination arguments; trigger (third
charge-every-reference walk → family here) + home present. J3
(measure-or-reject vs truncate) — agree: opposite failure contracts;
trigger (second measure-or-reject read → family here) + home present.
C11 held non-rule — agree. Coupling: none — agree (nothing to land
together in a zero-edit item).

### Freshness (re-hashes; ONE mismatch)

Working tree == HEAD for every fingerprinted file (all clean).
Re-hashed (`git hash-object`): target `52084078…` match; operation-state
`b2674a22…` match; exceptions `e06b0b7f…` match; root `647133d2…`
match; private-state `08088b82…` match; schema `2f727321…` match;
context `cd0adcc5…` match; extensions-init `dc3ebdc2…` match.
**Mismatch (Worker 2): R4 `### Findings` freshness has the two hashes
transposed** — it attributes `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`
to [mutations-fields][mutations-fields] and
`cf518361d7884b8b71550cb6b73bff0c1a64549e` to
[utils-inputs][utils-inputs], while the tree (content-verified:
`RELATION_MULTI` lives in utils/inputs, `MUTATION_CLASS_MARKER` in
mutations/fields) hashes utils/inputs → `ee31…`, mutations/fields →
`cf51…`. A later per-path reconciliation would false-report both files
changed and wrongly reopen R4. Repro: `git hash-object
django_strawberry_framework/utils/inputs.py
django_strawberry_framework/mutations/fields.py`. Fix: swap the two
hashes in R4; nothing else moves; probe re-run unchanged.

### Gates + Pending

F1 relies on the owner's pre-existing resumption rows (46 tests incl.
resume vocabulary in [test-operation-state][test-operation-state] plus
budget-resume rows in [test-resource-policy][test-resource-policy] —
existence verified, bodies static-reviewed; no pytest per item rules).
No negative control (`prove_failability`) was run in this item, by W1
or me: for a zero-edit file-item consumer finding the gate's
failability is owed at the FAMILY item holding the owner, not here —
accepted with that caveat recorded; no new gate owed. `## Pending
execution`: absent — agree, with `inapplicable by construction`
(target reaches no database/alias/dialect; only Django-adjacent reads
are the class marker + kind constant, never the ORM).

### AGENTS.md prose check

Diff empty → no production prose to check. Artifact: reference-style
links with the 10-group `LINK DEFINITIONS` block present; citations in
`path::Symbol` form, no raw `path:NN` source refs outside the allowed
scratchpad scope; no process provenance; no feedback-file mention; no
test-tier change; no commit. Probe scratch nits (6
annotation/docstring notes, per W1) are scratch-exempt style with the
probe still green. Pass.

### Verdict

`revision-needed` on exactly ONE required fix: swap the two transposed
hashes in R4's Freshness (utils/inputs ↔ mutations/fields). All 50
members, all counts, all families, all rejections, and the zero-edit
result otherwise verify. W1 pass 2 needs no re-trace: apply the swap,
re-run the unchanged probe, resubmit. The oracle-phrasing caveat and
the gate-failability caveat above are recorded differences, not
additional fixes.

### Scratch (Worker 2)

- `python3
  docs/dry/temp-tests/dry-file-extensions__resource_policy/probe_w1.py`
  → `W1 PROBE: ALL OK (44 checks)` (re-run, shared tree, read-only:
  no source mutation, no Django import, no DB). Execution-verified:
  50-member count + kind sequence + 11/4/2/9/2 census + absence/shape/
  count claims + blob==HEAD==item-baseline + empty item diff +
  population 117. Bodies, seams, oracle rows: static-reviewed.
- Own AST census (`ast.parse`, module + 5 class bodies) and package
  sweeps (`rebind_on_resume`, `Lexer(`, `_root_type`,
  `describe_value`/`QuerySet`/`seal`, `_charge_*` family, 13-name root
  edge + back-edge absence, oracle test counts 193/90/46) via
  read-only inspection. No workspace copy (no mutating proof owed).
- Concurrent dirt preserved untouched: `connection.py` hunk,
  `tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
  `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, all
  other untracked `dry-file-*.md` artifacts. No commit.

### Re-pass (Worker 2, pass 2)

Pass-1 `revision-needed` discharged. R4 Freshness lines 480–483 now
attribute [utils-inputs][utils-inputs] → `ee31d360…` and
[mutations-fields][mutations-fields] → `cf518361…`, matching own
`git hash-object` re-hash and Worker 0's independent verification;
cross-artifact corroboration holds (`dry-file-auth__queries.md`
pins `ee31…` to utils-inputs; `dry-file-schema.md` /
`dry-file-auth__mutations.md` pin `cf51…` to mutations/fields).
Full-artifact grep: remaining `ee31…`/`cf51…` mentions are this
section's pre-fix history plus the pass-2 note — no live
misattribution. Probe re-run green (`W1 PROBE: ALL OK`, 44 checks).
`## Iterations (pass 2)` is swap-only; pass-1 W2 trace, defect entry,
and link block intact; item-scoped production diff still 0 bytes;
concurrent dirt untouched. Verdict: **verified**, no pending execution.

## Iterations (pass 2)

Pass 2 swapped the two transposed R4 Freshness hashes so [utils-inputs][utils-inputs] carries `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` and [mutations-fields][mutations-fields] carries `cf518361d7884b8b71550cb6b73bff0c1a64549e`, matching Worker 0's `git hash-object` verification; grep confirms no other Freshness misattribution remains (the remaining `ee31…`/`cf51…` mentions describe the pre-fix transposition and stay verbatim); the unchanged read-only probe `docs/dry/temp-tests/dry-file-extensions__resource_policy/probe_w1.py` re-ran green (`W1 PROBE: ALL OK (44 checks)`) after the prose-only edit.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-context]: ../../django_strawberry_framework/utils/context.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-policies]: ../../django_strawberry_framework/utils/policies.py
[utils-private-state]: ../../django_strawberry_framework/utils/private_state.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-operation-state]: ../../tests/extensions/test_operation_state.py
[test-resource-policy]: ../../tests/test_resource_policy.py

<!-- examples/ -->
[test-resource-policy-api]: ../fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Run-7 scoped re-trace (Worker-1, REOPENED queue item d5)

Run: 0.0.15 2026-09-29-7. Everything above this section is PRIOR EVIDENCE
ONLY (09-18/19 artifact, `Status: verified` at its stamp). This section
re-traces the target fresh at HEAD bytes and issues a CONFIRM or REVISE
verdict for every prior finding, with fresh evidence for each. No
consolidation beyond this file item; no production edits; no plan edits.

### Scope, attribution, fingerprints

Three states fingerprinted, all by blob id over exact bytes:

- Drift base `5ee86193:django_strawberry_framework/extensions/resource_policy.py`
  = `388018335b94c5765bf6d7f92b2a22f41b6a9b40` (1435 lines). DIFFERS from
  HEAD: real committed delta, verified below (not assumed from the plan's
  one-line drift note, which turns out to understate it).
- HEAD (`0c0537e2`, movement re-checked at close):
  `HEAD:django_strawberry_framework/extensions/resource_policy.py` =
  `19e2309d06bdb3bf9441bd102b5755e55ab561a1` (1647 lines). All tracing
  below is against these bytes (read via `git show HEAD:` into `/tmp`,
  never the dirty worktree copy).
- Worktree: `0134d83a9aa2db580b7b8180ded27a3d31b115c7` (1631 lines;
  `git status` M). `git diff HEAD` shows exactly 2 hunks, 7+/23-.
- ITEM_BASELINE `3581277d3402abd446482786dd371850da3eb6fe` (a commit
  object; `git cat-file -t` = commit). Untouched.

Drift `5ee86193`..HEAD for this target, split per commit (both verified by
`git diff` of the exact range):

- `982537c3` ("classify extension entries by real type ..."): PROSE ONLY.
  One hunk in `DjangoResourcePolicyExtension`'s class docstring (entry-shape
  paragraphs reordered, `DjangoSchema(resource_policy=...)` configuration
  example added, plain-schema spelling updated). Zero code tokens move.
- `0c0537e2` (= HEAD, "charge every value validation converts before it
  runs"): the real delta. Module docstring pass-3 restatement; 7 new
  graphql-core imports (`DirectiveNode`, `ListValueNode`, `Node`,
  `ObjectValueNode`, `VariableNode`, `is_input_type`, `type_from_ast`);
  `scan_document_text` docstring (value-bounds follow validation);
  `charge_document` rewritten from a single-operation walk into a
  multi-root driver over the new `_DocumentWalk` plus the new
  `_variable_names`, `_type_system_directives`, `_declared_input_type`;
  `on_parse` docstring. Nothing else in the file moves: `_ValueBudget`,
  `_DocumentBudget`, `_root_type`, `_field_definition`, `_page_bound`,
  `_collection_rows`, `_is_connection_type`, the spec bridge, the
  configuration record, and all four hook bodies are byte-identical to the
  drift base (the `git diff` hunks cover docstrings, imports, and the
  `charge_document` region only).

The plan's recorded drift note ("unconfigured-schema fallback retargeted
to `_PACKAGE_RESOURCE_POLICY`") describes stamp-to-HEAD, not base-to-HEAD:
the prior stamp blob `52084078` (retrieved, imports re-read) carries
`DEFAULT_RESOURCE_POLICY` in the root import, while the drift base
`38801833` already carries `_PACKAGE_RESOURCE_POLICY` (line 106) with the
`_resolved_policy` miss arm already reading it (base line 1274). The
retarget landed between the stamp and `5ee86193`; within the re-trace
window the import row is byte-stable. R5 is REVISEd for the stamp wording,
with the canonical-copy split cited to the verified
`dry-file-utils__policies.md` outcome (Status: verified, run 5, HEAD blob
`8c881c0a`) and the verified File `resource_policy.py` run-7 re-trace
(HEAD blob `4b69e974`).

Attribution of both worktree hunks by content. No `## Owned changes`
ledger row names this file (ledger re-read in full; its only extensions
row is the adopted docstring hunk on `extensions/error_policy.py`), so
both hunks are concurrent-external; the trace runs on HEAD bytes and
touches nothing tracked:

- Hunk 1 (`_ValueBudget._bounded_members`, worktree lines 419-431): removes
  the `try/except Exception` that converts a measurement failure into a
  typed `ResourceLimitExceeded` for the bound being measured, and rewords
  the docstring ("a refusal to measure is a typed rejection ..." becomes
  "whatever the container's own iteration raises ... propagates"). This is
  J3's contract verbatim, inverted. W2 must trace HEAD bytes, where the
  refusal stands (probe `bounded-members-try` PASS).
- Hunk 2 (`_ValueBudget._charge_upload`, worktree lines 817-823): removes
  the `try/except Exception` around the `size` getattr, letting a hostile
  `size` property propagate instead of answering the unmeasurable-size
  rejection. Same J3 family, same external verdict.

Connected-file freshness (worktree vs HEAD; every seam below re-read at
HEAD bytes): `resource_policy.py` HEAD `4b69e974` (matches the verified
run-7 re-trace); `schema.py` HEAD `e6b52335`; `extensions/operation_state.py`
HEAD `b2674a22` (unchanged since the prior stamp); `extensions/error_policy.py`
HEAD `7ee4e9dd` (matches its verified run-7 re-trace); `utils/policies.py`
HEAD `8c881c0a` (unchanged); `utils/private_state.py` HEAD `08088b82`
(unchanged); `utils/context.py` HEAD `cd0adcc5` (unchanged); `utils/typing.py`
HEAD `de6309f6`; `utils/inputs.py` HEAD `ee31d360` (unchanged);
`mutations/fields.py` HEAD `d4edcbb7`; `exceptions.py` HEAD `e06b0b7f`
(unchanged); `extensions/__init__.py` `dc3ebdc2` (clean, unchanged). All
but the leaf are worktree-dirty (concurrent); nothing below depends on
dirty bytes.

### Enumeration (fresh, HEAD bytes)

Instrument: `ast.parse` over the HEAD dump, `len(ast.Module.body)` =
**54 top-level statements (0-53)** — REVISE of the prior 50 — plus every
body member of all **6** classes: `_ValueBudget` 11, `_DocumentBudget` 4,
`_DocumentWalk` **7** (new: docstring, `__init__`, `charge_arguments`,
`charge_directives`, `operation`, `fragment`, `walk`), `_AcceptedPolicy` 2,
`DjangoResourcePolicyExtension` 9, `_AdmissionGuard` 2. Kind sequence
pinned by the probe (`Expr` + `ImportFrom` x18 + table/name assigns +
functions/classes in prior order with the four new members inserted before
`charge_document`). Every member lands below; every challenge ends in a
family row, a file-local row, or a rejection.

| # | Statement | Home |
|---|---|---|
| 0 | module docstring (pass-3 paragraph restated by `0c0537e2`) | prose; hook order + reach owned here (R1/R2/R6), install shape projection of `schema.py` |
| 1-18 | `__future__` + stdlib/upstream/first-party imports (18 `ImportFrom`, zero `Import`) | consumer bindings (graphql block +7 names; root 13 names with the `_PACKAGE_RESOURCE_POLICY` token — R5) |
| 19 | `__all__ = ("DjangoResourcePolicyExtension",)` | R7 file-local |
| 20-22 | `_STRUCTURAL_DELIMITER_PAIRS` + derived `_OPEN/_CLOSE_TOKEN_KINDS` | R1 file-local |
| 23-24 | `_ID_SCALAR_NAME` / `_UPLOAD_SCALAR_NAME` | R3 file-local |
| 25 | `_STRAWBERRY_DEFINITION_BACKREF` | R4 file-local |
| 26 | `_NODE_IDS_ARGUMENT` | R3 file-local |
| 27-28 | `_CONNECTION_MARKER_FIELD` / `_EDGE_MARKER_FIELDS` | R2 file-local |
| 29-31 | `_SCHEMA_META_FIELD` / `_TYPE_META_FIELD` / `_TYPENAME_META_FIELD` | R2 file-local |
| 32 | `scan_document_text` (body untouched; docstring restated) | R1 file-local |
| 33 | `_mutation_input_specs` | R4 file-local |
| 34 | `_nested_specs_map` | R4 file-local |
| 35 | `_EXACT_SEQUENCE_TYPES` | R3 file-local |
| 36 | `_closes_a_cycle` | R3 file-local (+ J2) |
| 37 | `_ValueBudget` + 11 members (byte-identical to drift base) | R3 file-local (+ J3) |
| 38 | `_DocumentBudget` + 4 members | R2 file-local |
| 39-43 | `_root_type`, `_field_definition`, `_page_bound`, `_collection_rows`, `_is_connection_type` | R2 file-local |
| 44 | `_variable_names` (NEW: value-AST variable iterator) | R2 file-local (+ N1) |
| 45 | `_type_system_directives` (NEW: generic `node.keys` descent) | R2 file-local |
| 46 | `_declared_input_type` (NEW: `type_from_ast` + `is_input_type`) | R2 file-local |
| 47 | `_DocumentWalk` + 7 members (NEW: multi-root walk state) | R2 file-local |
| 48 | `charge_document` (rewritten: multi-root driver) | R2 file-local |
| 49 | `_AcceptedPolicy` + 2 members | R5 file-local |
| 50 | `_EXPLICIT_POLICY` authority | R5 file-local |
| 51 | `restate_admission_verdict` | R6 file-local |
| 52 | `DjangoResourcePolicyExtension` + 9 members (bodies untouched) | F1 consumer + R5 + R6 |
| 53 | `_AdmissionGuard` + 2 members | R6 file-local |

### Matrix (re-discharged)

**1. Cross-flavor policy mirroring — REVISE.** The prior sweep stands and
extends: `Lexer(`, `_ValueBudget`, `_DocumentBudget`, `_charge_*`,
`max_selections` still occur only here, at the schema consumer, or in
oracles/prose (package `.py` sweep re-run). The six new drift names
(`_variable_names`, `_type_system_directives`, `_declared_input_type`,
`_DocumentWalk`, `charge_arguments`, `charge_directives`) occur as
exact-word definitions only here in production (the `_variable_names`
character string also occurs inside `directive_variable_names` at
`optimizer/selections.py` and its `optimizer/extension.py` consumer — a
substring twin, adjudicated as N1 below, not a second definition). One
fresh pair needed adjudication: `_variable_names` vs the verified
`optimizer/selections.py::directive_variable_names` (definition in verified
File `optimizer/selections.py`: W1 F-D named `ast-directive-variable-extraction`,
W2 re-homed the member under `ast-walk-substrate`, no plan row transcribed) —
refused as N1 below (every-variable deep iterator for default-read tracking vs
skip/include-only top-level set for the plan-cache key: distinct
population, shape, and reason to change). Two verified convergences cover
the directive-charging half without a new family:
`directives-validation-vs-directive-cost-charging` (verified File
`utils/directives.py` rejection: construction-time allowlist validation vs
request-time cost charging) and `testing-client-walk-vs-budget-walk`
(verified File `testing/client.py` rejection: single-path placeholder
verify vs full-traversal charge) — both cite this file and stand; not
re-litigated. Flavors still participate by being charged (bind-spec
producer seam re-verified at HEAD `mutations/sets.py:265` stash,
`mutations/fields.py:73` marker spelling, `utils/inputs.py:261`
`RELATION_MULTI`); `awaitable-refusal-and-disposal` still 0 vocabulary.

**2. Sync/async twins — CONFIRM.** Zero `AsyncFunctionDef`, zero `await`
(probe); both walks remain explicit-stack iteration, all four hooks plain
sync generators. The drift adds no execution color: `_DocumentWalk` holds
budgets and sets, never a queryset or an awaitable. `one-sync-boundary`
still 0 vocabulary; `islice`/`sys` still prose-only (no imports).

**3. Derived rather than repeated knowledge — CONFIRM.** Single
resolve-and-arm in `on_operation` intact (1 `begin_resource_budget`, 1
`end_resource_budget`, 1 `settle`, 1 `recall` — probe); every charge reads
`armed_resource_policy()`; the off-scope `on_parse` fallback still answers
exactly as arming would (`policy if policy is not None else
self._resolved_policy()`). Per-root `variables`/`read`/`in_mutation` on
`_DocumentWalk` are walk state, not re-derivation of the policy.

**4. Inverse / round-trip pairs — REVISE.** Four prior pairs re-homed plus
two new single-body/multi-site pairs. `scan_document_text`/`charge_document`
is now shape-vs-values-everywhere (shape bounds on the selected operation
alone; value bounds on every definition validation converts) rather than
named-operation-vs-whole-document — one grammar, restated, still one way
across the root import edge. `record`/`publish` (single joint caller
`on_parse`), `restate_admission_verdict` (one body, two positions), and
`_mutation_input_specs`/`_nested_specs_map` (1 + 3 call sites, probe)
stand. New: `charge_arguments` (single body; field args + directive args
via `charge_directives`) and `charge_directives` (single body; 6 call
sites: var-def directives, operation directives, spread directives,
expanded-fragment directives, fragment-root directives, type-system
directives) — each one body every caller composes by name. No pair split
across two owners.

**5. Contracts restated in another medium — REVISE.** Counts only. Oracles
at HEAD bytes: `tests/test_resource_policy.py` 196 `def test_` rows (prior
193), `examples/fakeshop/test_query/test_resource_policy_api.py` 118 (prior
90 — the drift's value-charging rows), `tests/extensions/test_operation_state.py`
46 (unchanged). All three files are worktree-dirty (concurrent); counts are
over `git show HEAD:`. The W2 pass-1 caveat (one package-tier test imports
private `_field_definition`) stands as recorded. Consumers still compose by
name (chain + `_entry_resource_policy` reading `_policy` re-read at HEAD
`schema.py:1295-1299`, `:1381`); projections unchanged in kind.

**6. Enforcement by omission — REVISE.** Reach widens, still without gaps.
(a) Passes 2-3 still run at `on_parse` on every transport; the drift
extends pass 3 to every value validation converts: unselected operations
(values-only, variables as `None`), unspread fragment definitions (own
roots, duplicate names included), type-system-definition directives, and
defaults no use site charged (once at definition). (b) Chain position
re-read at HEAD: error masker, consumer entries, resource extension, guard,
mode marker (`schema.py:1295-1299`) — admission still ahead, guard still
last. (c) Deliberate fallbacks unchanged: off-scope `_resolved_policy`
fallback, raw-schema shared-instance limit, no deadline here (root seam).
No member lacks a guard its contract requires; the subscribe-path entry
claim stays honestly static-reviewed.

### Prior-finding verdicts (fresh evidence each)

- **F1 operation-bound-extension-mechanism — CONFIRM.** Consumer shape
  byte-identical to the prior trace: own `_reconstruction_refusal`, NO
  state factory, NO `_new_operation_state` (probe), exactly ONE
  `rebind_on_resume` call (probe + package sweep: definition at
  `extensions/operation_state.py:165` plus this call plus 2 docstring
  mentions). Base blob `b2674a22` unchanged since the prior stamp. C5/C6/C15
  re-counts: 0 here / 1 at owner each. Index state CORRECTED (F-A): the plan
  carries NO row for this family (0 mentions in `## Responsibility index`,
  no `## Families` item — the verified File `extensions/operation_state.py`
  artifact proposed both but Worker-0 never transcribed them). The row is
  NAMED for Worker-0 in `## Index rows for Worker-0` below, adopting the
  holding artifact's proposed text verbatim (owner
  `extensions/operation_state.py::_OperationBoundExtension`, five files incl.
  this one as consumer, status open) plus its `## Families` item.
- **F2 typed-rejection-value-tail — CONFIRM.** Still neither member nor
  consumer: zero `describe_value`, zero `got `, zero `ConfigurationError`
  (probe); the 13 `ResourceLimitExceeded` token occurrences are unchanged
  base-to-HEAD (9 constructions + import + except + isinstance re-raise
  guard + 1 docstring prose — the prior "thirteen constructions" wording
  counted tokens; the count is exact and drift-stable either way).
  Exceptions HEAD `e06b0b7f` unchanged.
- **F3 async-only-queryset-row-adapter — CONFIRM.** Zero `QuerySet`,
  zero `is_async_only_iterable` / `_AsyncQuerySetRows` (probe); the single
  `queryset` token is still the module-docstring negative. The index row's
  `resource_policy.py` remains the ROOT file (root re-trace verified).
- **F4 sealed-execution-queryset — CONFIRM.** Zero `seal` tokens (probe);
  still seals nothing, executes nothing.
- **R1 pre-parse text scan — CONFIRM.** Body byte-identical to drift base;
  the docstring restatement (value bounds follow validation) describes R2's
  new reach, not a new scan rule. Only `Lexer(` in the package (sweep).
  C1 re-count: 1.
- **R2 document walk — REVISE.** The rule grows from "named-operation
  fragment-expanding walk" to "multi-root walk: shape on the selected
  operation, values everywhere validation converts". New members #44-47
  plus rewritten #48, all single definitions with no second site
  (package sweeps). Intact within the rewrite: spread-path cycle guard
  (`name in path`, `path | {name}`), charge-at-every-spread-site, all six
  helpers (#39-43) byte-identical, `_DocumentBudget` byte-identical.
  C2/C10 re-counts: 1 each at the new bodies.
- **R3 value walk — CONFIRM (at HEAD; dirt is external).** `_ValueBudget`
  byte-identical to the drift base; `_closes_a_cycle`, `_EXACT_SEQUENCE_TYPES`,
  ID/Upload/`ids` vocabulary untouched. C3/C4/C14 re-count: 1 each at HEAD.
  Both worktree dirt hunks land in this rule's bodies and invert J3; they
  are concurrent-external (no ledger row), so the CONFIRM is a HEAD verdict
  and W2 must trace HEAD bytes.
- **R4 bind-spec bridge — CONFIRM.** Bridge functions byte-identical; call
  census intact (1 top-level `_mutation_input_specs`, 3 `_nested_specs_map`
  — probe); the top-level call now sits in `walk` (called even when
  `field_def` is `None`, yielding `None` specs = untyped charging, the
  documented fallback). Producer seam re-verified at HEAD (`mutations/sets.py:265`
  stash + `:1047` declaration; marker `mutations/fields.py:73`;
  `RELATION_MULTI` `utils/inputs.py:261`). C4 re-count: 1 here.
- **R5 extension configuration — REVISE (stamp wording only).** Since the
  prior stamp the import token retargeted `DEFAULT_RESOURCE_POLICY` →
  `_PACKAGE_RESOURCE_POLICY` and the `_resolved_policy` miss arm reads the
  canonical copy (both already so at the drift base; byte-stable across
  the re-trace window). This converges onto the verified
  `policy-authority-isolation` record: `_PACKAGE_RESOURCE_POLICY` is the
  import-time `canonical_policy(...)` copy (`resource_policy.py:457`,
  verified root re-trace blob `4b69e974`); the settled explicit policy is
  canonicalized at acceptance via `_operation_policy`; `_policy` hands out
  `copy_policy` duplicates; the schema consumer reads it through
  `_entry_resource_policy` (HEAD `schema.py:1381`). Settle-once/recall-per-read
  census intact (1/1 — probe). C9 re-count: 1. Family row already lists this
  file; no index change.
- **R6 admission-verdict lifecycle — CONFIRM.** All four hook bodies
  byte-identical to drift base; `restate_admission_verdict` one body at two
  positions (2 calls — probe); `on_parse` still the sole record+publish caller
  that empties validation rules; chain order re-read at HEAD (`schema.py`
  masker/entries/extension/guard/marker). C7/C8 re-count: 1 each.
- **R7 leaf manifest — CONFIRM.** `__all__` 1 name, unchanged; leaf file
  clean at `dc3ebdc2`, the prior stamp's hash.
- **J1 enforcement unification — CONFIRM.** Pair re-verified from this side
  at HEAD: error half still a single `on_operation` teardown with ZERO
  `max_*` hits (HEAD blob `7ee4e9dd`, its verified run-7 re-trace); this
  half still four hooks with 56 `max_*` hits; resolve/copy/tail/mechanism
  still shared by name. Trigger (third enforcement extension) unfired.
- **J2 cycle guards — CONFIRM.** Both guards byte-intact (name-domain spread
  path; `is`-identity `_closes_a_cycle`). The drift's new helpers are
  finite AST descents over tree-shaped nodes, not reference-charging walks
  — the "third charge-every-reference walk" trigger is not met. C12 stays
  refused.
- **J3 measure-or-reject vs truncate — CONFIRM (at HEAD; dirt is external).**
  Both typed refusals intact at HEAD (`_bounded_members` "cannot measure"
  rejection; `_charge_upload` unmeasurable-size branches — probe). The
  worktree dirt deletes both `try/except` wrappers; concurrent-external, so
  the CONFIRM is a HEAD verdict. C14 re-count: 1 at HEAD. Trigger (second
  measure-or-reject read) unfired — the dirt is a deletion, not a second
  definition.

Prior challenges C1-C17: all re-counted at HEAD bytes, all agree (C1-C4,
C7-C10, C14 at 1 here; C5/C6/C15/C16/C17 at 0 here with the named owner;
C11 held non-rule; C12/C13 refused). No challenge changes home.

### New-shape challenges, family/file-local assignment, new rejection

The drift introduces one new rule shape (values-everywhere charging) owned
entirely inside R2's file-local home — no new family is named. Six
challenges on its own variation axes, each count 1:

- **NC1** unselected-operation variable resolution: resolve supplied values
  instead of charging `None` → 1 (`charge_arguments` carried-`None`
  branch). File-local (R2).
- **NC2** type-system-definition scope: charge shape as well as directive
  values → 1 (`charge_document` elif arm + `_type_system_directives`
  scope docstring). File-local (R2).
- **NC3** expanded-fragment directive accounting: charge once per definition
  instead of per expansion → 1 (the spread arm's
  `charge_directives(fragment.directives)` inside expansion). File-local (R2).
- **NC4** duplicate-name fragment roots: do not walk a shadowed duplicate as
  an extra root → 1 (`charge_document` second loop). File-local (R2).
- **NC5** default-read tracking: drop the `read` set, charge every default
  at its definition → 1 (`operation` method's `defaulted`/`read` pair).
  File-local (R2).
- **NC6** per-root mutation-ness: one walk-wide flag instead of per-root
  `in_mutation` → 1 (`operation`/`fragment` assignments + `walk` reads).
  File-local (R2).

**N1 — value-AST variable names vs cache-key directive variables (new
refused shared form, recorded here).** `_variable_names` (this file: deep
iterator yielding EVERY variable nested in a value AST, for default-read
tracking) vs `optimizer/selections.py::directive_variable_names`
(definition in verified File `optimizer/selections.py` — W1 F-D named
`ast-directive-variable-extraction`, W2 re-homed the member under
`ast-walk-substrate`, no plan row transcribed: top-level `VariableNode`s in
`@skip`/`@include` `if` args only, as a set, for the plan-cache key; sole
production consumer `optimizer/extension.py`, composing the selections owner
by name via one import at HEAD `:126` plus one call at HEAD `:278` with a
comment citing the owner — a consumer edge, not a second definition).
Considered: one shared variable-name extractor. Refused: distinct
populations (arbitrary value trees vs two named directives' scalar args),
distinct shapes (lazy deep iterator vs strict filtered set), distinct
reasons to change (validation-conversion coverage vs cache-key relevance);
the shared helper would parameterize away its whole content (descent depth
+ directive filter). Reconsideration trigger: a third variable-name walk
  over value ASTs, or either side generalizing to the other's population —
  then the EXTRACTION becomes a family owned at the generalizing site.
  Durable home: this finding + the optimizer owner's docstring paragraph
  (no edit owed by a file item). One `## Responsibility index` row named
  below for Worker-0 to add.

Convergences (already verified, already indexed, this file listed or
cited — no rows owed): `directives-validation-vs-directive-cost-charging`
(File `utils/directives.py`) for `charge_directives`;
`testing-client-walk-vs-budget-walk` (File `testing/client.py`) for the
budget walk; `operation-bound-extension-mechanism` (F1);
`policy-authority-isolation` (R5); `typing-non-null-only-peel` (the
`unwrap_non_null` consumer edge — verified File `utils/typing.py`,
this file listed).

### Defects

None. Every claim checked while tracing held at HEAD bytes: the one-way
13-name root edge with the `_PACKAGE_RESOURCE_POLICY` token (zero
back-edge — the root module never names this one); the single registration
call; the single arm/disarm pair; the two-position restatement; the 1 + 3
spec calls; the chain order (masker, consumer entries, resource extension,
guard, mode marker — schema lines re-read at HEAD); the refusal-only +
base-state consumer shape; the off-scope fallback answering as arming
would; the 13 `ResourceLimitExceeded` token occurrences unchanged
base-to-HEAD. The two worktree dirt hunks are concurrent-external J3
inversions, not HEAD defects: left untouched, reported here, never
reverted. Nothing routed to any owner.

### Pending execution

None. The execution proofs are the read-only probe (`/tmp/rp_probe.py`,
ALL PASS, 40 checks: 54-member AST + kind sequence + 11/4/7/2/9/2 census,
zero async/await, 13-name root edge + token checks, all call-count and
absence claims, drift-base import census) plus the package-wide name
sweeps, all cited by content above; they mutate no source, open no
database, and import no Django, so no workspace copy was owed and no
`__file__`/DB `NAME` record applies (the `/tmp`-only probe convention
follows the run-7 `utils/querysets.py` re-trace). No pytest was run in the
shared tree, per item rules; oracle bodies are `static-reviewed`. No
`FAKESHOP_SHARDED` or Postgres cell is owed: the target's code path reaches
no database, alias, or dialect decision (`inapplicable by construction` —
graphql-core lexer/AST walk plus ContextVar/lease/token binding; the only
Django-adjacent reads are the mutation-class marker and kind constant,
never the ORM).

### Judgment

Backstop re-discharged at HEAD bytes: 54/54 `ast.Module.body` members
enumerated plus all 6 class bodies (11/4/7/2/9/2), 17 prior challenges
re-counted plus 6 new-shape challenges, every rule terminating in the one
reused family it composes (F1 — consumer, byte-identical shape), a checked
non-member (F2-F4, absence probes green), a file-local record (R1-R7: R2
and R5 REVISEd, rest CONFIRMed), or a recorded rejection (J1-J3 CONFIRMed
at HEAD, N1 newly refused). The drift is one prose commit plus the
values-everywhere walk rewrite, all file-local to R2; the `_PACKAGE_*`
retarget predates the re-trace window and converges onto verified
`policy-authority-isolation`. No consolidation owed (composition is already
by name on every edge, old and new), no defect found, no new family named,
no pending execution. Zero-edit result is legitimate. HEAD `0c0537e2`
unmoved at close (re-checked after the artifact write).

## Index rows for Worker-0

(Worker-0 alone edits the plan; rows named here for transcription.)

- CONFIRMed, unchanged text: `policy-authority-isolation`
  (open; already lists this file; R5 converges onto its verified canonical-copy
  record, HEAD blobs `19e2309d` + `4b69e974` + `8c881c0a` as cited there);
  `typed-rejection-value-tail`, `sealed-execution-queryset`,
  `async-only-queryset-row-adapter` (open; checked, still non-members);
  `directives-validation-vs-directive-cost-charging`,
  `testing-client-walk-vs-budget-walk`, `typing-non-null-only-peel`
  (verified rejections/convergences citing this file; stand, no
  re-litigation); J1/J2/J3 refused shared forms (triggers unfired; J3's
  dirt is concurrent-external, not a trigger).
- REVISEd at artifact level, no transcription owed: R2 document walk
  (file-local record grows to the multi-root walk; no index row);
  R5 extension configuration (import-row wording `_PACKAGE_*`; family row
  untouched); enumeration 50->54 + matrix axes 1/4/5/6 (artifact wording
  only); oracle counts 193/90/46 -> 196/118/46 at HEAD (citation update).
- New rows (1): `budget-value-variable-names-vs-cache-key-directive-variables`
  | owner `django_strawberry_framework/extensions/resource_policy.py::_variable_names`
  (rejection recorded here) | files `extensions/resource_policy.py`,
  `optimizer/selections.py` | holding item File `extensions/resource_policy.py`
  | status `rejected` (deep every-variable iterator vs skip/include-only
  cache-key set; trigger: a third value-AST variable walk or either side
  generalizing to the other's population).
- Named for transcription (F-A; CORRECTS the withdrawn "already lists this
  file" claim — 0 plan mentions, never transcribed): adopt the verified
  File `extensions/operation_state.py` holding artifact's proposed text
  verbatim — `## Families` item `- [ ] Family
  `operation-bound-extension-mechanism` —
  [dry-rule-operation-bound-extension-mechanism.md](dry-rule-operation-bound-extension-mechanism.md)`
  plus `## Responsibility index` row
  `operation-bound-extension-mechanism` | owner
  `django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`
  | files `.../extensions/operation_state.py`, `.../extensions/debug.py`,
  `.../extensions/error_policy.py`, `.../extensions/resource_policy.py`
  (this file, consumer — census re-verified byte-identical at HEAD
  `19e2309d`), `.../optimizer/extension.py` | holding item Family
  `operation-bound-extension-mechanism` | status `open`.

## Independent verification (Worker-2, run 7)

Expectation-first: the trace below was derived from HEAD bytes before the
run-7 findings were opened; reconciliation follows it. Scope is the run-7
re-trace only; everything above `## Run-7 scoped re-trace` is prior
evidence. HEAD `0c0537e2` unmoved at open and at close (re-checked after
this write); `git status` dirt is concurrent work, untouched.

### Own trace (before opening run-7 findings)

- Fingerprints (independent): `HEAD:` target
  `19e2309d06bdb3bf9441bd102b5755e55ab561a1` (1647 lines); worktree
  `0134d83a9aa2db580b7b8180ded27a3d31b115c7` (1631 lines);
  `5ee86193:` target `388018335b94c5765bf6d7f92b2a22f41b6a9b40`;
  ITEM_BASELINE `3581277d3402abd446482786dd371850da3eb6fe` is a commit
  whose target blob equals the worktree (`0134d83a`), so both
  HEAD→worktree hunks predate W1.
- Enumeration (own `ast.parse` over the HEAD dump): 54 module members
  (0 docstring, 1–18 `ImportFrom` x18 with zero `Import`, 19 `__all__`,
  20–22 `AnnAssign`, 23–31 assigns, 32–36 functions, 37–38 classes,
  39–43 helpers, 44–47 new functions + new class, 48 rewritten driver,
  49–53 record/authority/restatement/extension/guard). Class bodies:
  `_ValueBudget` 11, `_DocumentBudget` 4, `_DocumentWalk` 7,
  `_AcceptedPolicy` 2, `DjangoResourcePolicyExtension` 9,
  `_AdmissionGuard` 2. Drift-base count is 50; delta is exactly +4.
- Hunks (own read of `git diff HEAD`): 2, both in `_ValueBudget`.
  Hunk 1 (`_bounded_members`) deletes the `try/except Exception` that
  converts a measurement failure into a typed `ResourceLimitExceeded`
  and rewords the docstring from typed-rejection to propagate. Hunk 2
  (`_charge_upload`) deletes the `try/except` around the `size`
  getattr. Both invert committed fail-closed behavior (the HEAD
  commit message says those wrappers are unchanged), cohere as one
  behavior change, match no ledger row naming this file, and were
  dirty at item entry: concurrent-external by content and by timing.
- Drift window (`git log 5ee86193..HEAD -- <target>`): exactly 2
  commits. `982537c3` touches only the extension class docstring
  (own docstring-stripped AST comparison: identical to the base).
  `0c0537e2` (+288/−84) rewrites the value walk around a new
  multi-root driver. `_PACKAGE_RESOURCE_POLICY` is already at base
  lines 106/1274 with the miss arm reading it, and `0c0537e2` touches
  zero `_PACKAGE_*` lines: any retarget predates the window.

### Reconciliation (per required judgment)

1. Enumeration: STANDS. Counts, kind sequence, class censuses, and the
   member-by-member table all agree with the independent parse,
   including #44–47 new and #48 rewritten.
2. Hunk attribution: STANDS. Content, line spans, and the
   concurrent-external verdict agree; the inversion reading is
   confirmed against the HEAD bodies (refusals intact at HEAD).
3. Drift scope: STANDS. Prose-commit proof, rewrite footprint, and the
   pre-window retarget (stamp `52084078` retrieved: carries
   `DEFAULT_RESOURCE_POLICY` at the same two lines) all re-verified.
   Every symbol W1 lists as untouched is AST-identical base→HEAD;
   `scan_document_text` differs by docstring only (proven).
4. CONFIRMs (all 12 spot-probed at HEAD bytes): substance STANDS.
   Zero async/await; 13 `ResourceLimitExceeded` tokens; F2/F3/F4
   absence probes green (`queryset` x1 is the module-docstring
   negative); sole package `Lexer(`; 1/1 settle/recall and
   begin/end calls; 56 `max_*` here vs 0 with a single `on_operation`
   at error-policy HEAD `7ee4e9dd`; 1 `rebind_on_resume` call with
   the definition at `operation_state.py:165`; 2 restatement calls;
   1 + 3 spec calls with the top-level call in `walk` and a
   None-safe fallback; 6 `charge_directives` call sites; chain order
   and `_entry_resource_policy` at `schema.py:1295-1299` and `:1381`;
   all four producer-seam lines; all 12 connected-file fingerprints;
   oracle counts 196/118/46 over `git show HEAD:`. Two nits ride
   with the verdict below (F2 tail wording, axis-1 sweep sentence).
5. REVISEs: both ENDORSED. R2 — the rule genuinely changes shape
   (shape on the selected operation, values everywhere validation
   converts); the four new members are exact-word single-sited
   (package `git grep`); guards, helpers, and budget intact as
   claimed; NC1–NC6 each grounded in cited code. R5 — stamp-wording
   correction proven; canonical-copy convergence accurate
   (import token, miss arm, settle/recall, schema consumer edge);
   the `policy-authority-isolation` plan row exists and lists this
   file. Both are artifact-level; no transcription owed for either.
6. N1: refusal ENDORSED, record needs repair (see fix F-B). Both
   bodies read: deep lazy every-variable iterator for
   default-read tracking vs top-level skip/include-only strict set
   for the plan-cache key — distinct population, shape, depth, and
   reason to change; the trigger is well-formed. The counterpart
   status label and the uncited consumer are the defects, not the
   refusal.
7. Family convergence: 4 of 5 STAND
   (`policy-authority-isolation`, `directives-validation-vs-directive-cost-charging`,
   `testing-client-walk-vs-budget-walk`, `typing-non-null-only-peel`
   are each indexed, list or cite this file, and sit under verified
   holding files). `operation-bound-extension-mechanism` FAILS: the
   plan contains zero mentions of it — the holding file's verified
   artifact proposed the row but Worker-0 never transcribed it — so
   "Index row already lists this file; no change owed" is false
   (see fix F-A). Sibling run-7 re-traces' matching claims all point
   at rows that exist; this one does not.
8. Zero-defect call: STANDS for production substance. No production
   defect found; dirt correctly left untouched. The defects below
   are record-accuracy defects in convergence/index sentences.

### Verdict: revision-needed (record-accuracy only)

No re-trace, no production edits, no new probes. W1 resubmits from
the SAME context as `ready-for-verification/2` with exactly these
repairs in the run-7 section (resubmission returns to the SAME
Worker-2; fresh only if that context is gone):

- F-A (F1 + Index rows): replace both "already lists this file; no
  change owed" claims for `operation-bound-extension-mechanism` with
  the accurate state (named in verified File
  `extensions/operation_state.py`, proposed row never transcribed —
  0 plan mentions) and NAME the row for Worker-0 (adopt the holding
  artifact's proposed row text: owner
  `extensions/operation_state.py::_OperationBoundExtension`, five
  files incl. this one as consumer, status open; plus the `##
  Families` item if still absent).
- F-B (N1): replace "(verified family
  `ast-directive-variable-extraction`...)" with the accurate
  counterpart status (definition in verified File
  `optimizer/selections.py`; W1 F-D named
  `ast-directive-variable-extraction`, W2 re-homed the member under
  `ast-walk-substrate`; no plan row transcribed). Add the
  `optimizer/extension.py` consumer site (import + 1 call + comment,
  composing the selections owner by name) to N1's sites, or state
  the files list covers definitions with the consumer noted.
- F-C (axis 1): qualify "occur only here in production" as
  exact-word definitions, noting the `_variable_names` substring
  also occurs inside `directive_variable_names` (adjudicated as
  N1). Optional nit: F2's tail decomposition counts the line-274
  `isinstance` re-raise guard as prose; reword or drop it.
- Re-check HEAD unmoved plus all fingerprints at close; keep the
  zero-edit, no-pending-execution posture.

Ruff: nothing to run — the only touched path is this Markdown
artifact (`.md` is outside ruff's corpus); no production or test
file was edited. AGENTS.md prose rules hold for the touched text
(symbol citations, no process provenance).

### Re-pass (Worker-2, run 7, pass 2)

Resubmission `ready-for-verification/2`, same Worker-2 context.
Preconditions re-checked mechanically: HEAD `0c0537e2` unmoved;
target diff vs ITEM_BASELINE `3581277d` still empty; HEAD blob
still `19e2309d`; every pass-1 judgment line intact (R2/R5 REVISEs,
12 CONFIRMs, N1 refusal, judgment — spot-grepped, unmoved).

- F-A REPRODUCES. F1 now states "0 mentions in `##
  Responsibility index`, no `## Families` item": index spans
  plan:285–1268 and contains zero `operation-bound` mentions (the
  only two plan mentions sit at :6082/:6097 in Worker-0 run notes);
  no Families item exists. The NAMED row + Families item match the
  holding artifact's proposed text (owner, five files in order,
  holding item, `open`), modulo path abbreviation and one
  parenthetical flagging this file's re-verified consumer census.
  The family is correctly removed from the "unchanged text" bullet.
- F-B REPRODUCES. N1 counterpart status corrected (W1 F-D /
  W2 `ast-walk-substrate` / no plan row) and the
  `optimizer/extension.py` consumer cited at import `:126` + call
  `:278`, matching the independent pass-1 grep exactly.
- F-C REPRODUCES. Axis-1 sweep qualified as "exact-word
  definitions", with the substring twin adjudicated to N1; the F2
  tail nit fixed (`isinstance` re-raise guard + 1 prose).

Two residuals, recorded with precision (neither blocks: no
verdict, count, or transcription instruction is affected):

- R1: the `Convergences` paragraph still files F1 under
  "(already verified, already indexed ... no rows owed)". Stale —
  it predates the F-A correction and was outside the named fix
  scope. The corrected F1 verdict and the Index-rows F-A bullet
  govern; Worker-0 transcribes from `## Index rows for Worker-0`,
  which is correct.
- R2: the Index-rows F-A bullet's "0 plan mentions" shorthand is
  now literally 2 — Worker-0's run-note records of this defect
  (plan:6082/:6097). Operative claim (zero in the Responsibility
  index proper, no Families item) true.

Verdict: verified. Zero-edit re-trace stands; one NEW index row
(N1) plus one NAMED transcription (F-A family item + row) owed to
Worker-0; no pending execution.
