# DRY review: `optimizer/selections.py`

Status: verified
Run: 0.0.15 2026-09-19-1
Target: `django_strawberry_framework/optimizer/selections.py` (720 lines)
Blob: `a48f6172c6f04331740d1b110d742f17701ff846` (worktree == HEAD ==
ITEM_BASELINE `a48f6172c6f04331740d1b110d742f17701ff846`; zero diff on all
three; target worktree-clean)
Item baseline: `a48f6172c6f04331740d1b110d742f17701ff846`
Ledger check: `## Owned changes` in the plan names exactly one
optimizer-area row (walker D1 seal-policy on `optimizer/walker.py`: import
`_PREFETCH_CHILD_POLICY`, `_build_child_queryset` seal policy + docstring)
plus gate-only pins and docstring trigger clauses on other families;
no row touches this item's path. `grep -n "selections"` over the plan finds
only the item line plus the `optimizer-execution-frame` index row (reused
below as F-0, not inherited). Confirmed before reading the target.

## System trace

The target owns the optimizer's selection-tree traversal substrate: two
explicit adapters over the same fragment/directive/response-key contracts.
The AST adapter (`ast_child_selections`, `resolve_unvisited_fragment`,
`directive_variable_names`) serves `optimizer/extension.py` (plan-cache key
construction, reachable-fragment collection, cache-relevant variable sweep,
converted-selection fallback at `extension.py:1223`). The converted-selection
adapter (everything from `is_fragment` down) serves `optimizer/walker.py`
(level descent, alias merging, FK-id-elision scalar scan),
`optimizer/nested_planner.py` (nested connection windows, split count
observers at `nested_planner.py:1353-1354`), `optimizer/extension.py`'s
root-connection seam (`_connection_node_child_selections`,
`mutation_payload_child_selections`), and `connection.py` (resolve-time
`_total_count_requested` / `_has_next_page_requested` plus
`prime_selected_fields` at `connection.py:1341`). The AST-to-converted
mirror (`ast_to_converted_selections` + `prime_selected_fields`) is the
package-owned faithful copy of Strawberry's `convert_selections`, needed
because Strawberry's `InlineFragment.from_node` dereferences
`node.type_condition.name.value` unguarded (installed
`.venv/.../strawberry/types/nodes.py:128`, strawberry 0.324.0, floor pin
`strawberry-graphql>=0.316.0`) and crashes on spec-valid anonymous inline
fragments.

Sites read (roles: definition / consumer / oracle / projection):

- Definitions owned here, consumers elsewhere: every one of the 19
  functions + `ConnectionFieldNames` + both module assigns is defined
  exactly once package-wide (`probe_singledef.py` 20/20 single-site,
  `multi_site=NONE`). Consumer map per `probe_consumers.py`: extension.py
  (AST trio + `connection_node_children` + `node_children_with_runtime_prefix`
  + `named_children` + `response_key` + `connection_field_names` +
  `ast_to_converted_selections`); walker.py (`included_field_selections`,
  `is_fragment`, `named_children`, `node_children_with_runtime_prefix`,
  `response_key(s)`, `should_include`, `with_runtime_prefix` — all via
  underscore aliases at `walker.py:63-70`); nested_planner.py
  (`connection_node_children`, the two split count observers,
  `connection_field_names`, `response_keys` as `_response_keys`,
  `ConnectionFieldNames` as an annotation); connection.py
  (`connection_field_names`, the two count observers,
  `prime_selected_fields`). Bodies read at each call site; every call
  composes by name, no inline re-derivation found.
- Definitions consumed (not owned here): `optimizer/_context.py::
  converted_selections_memo` (clean `3d8dcfdf` both; family
  `optimizer-execution-frame`, already consolidated — reused as F-0);
  `utils/typing.py::schema_config_from_info` (clean `de6309f6` both);
  Strawberry's `SelectedField` / `FragmentSpread` / `InlineFragment` /
  `convert_arguments` / `convert_directives` (mirror inputs, never
  re-spelled); `utils/connections.py::FetchMode` + spec-033 Decision 4
  (the observability contract `connection_count_required` pins).
- Oracles: `tests/optimizer/test_selections.py` (clean `04bbb23d` both;
  30 tests covering every public name incl. the memo lifecycle, the
  fast-path identity, the one-shot-iterable materialization, the
  count-required matrix, and the four converter-vocabulary tests);
  `tests/optimizer/test_walker.py` (clean `5bbd7a56` both; `_should_include`
  / `_is_fragment` rows via the walker aliases);
  `tests/test_relay_connection.py` (clean `b6bd90d9` both; one
  `connection_count_required` cite); live anonymous-inline-fragment tests
  in `examples/fakeshop/test_query/test_library_api.py`
  (`test_anonymous_inline_fragment_*`, 4 tests) and
  `test_glossary_api.py` (`ast_to_converted_selections` prose cite).
- Projections: module + symbol docstrings (each states its contract; several
  state reconsideration triggers); `ATTENTION.md` (forward-resolution
  direction cited by `connection_field_names`); BACKLOG
  `polymorphic_interface_connections` (the TODO-anchored tri-state
  classifier pseudo block at target lines 376-389, ERA001-exempt);
  spec-033 Decision 4/7 + spec-035 Decision 6/7 (cited in bodies).
  Prior-cycle records used as trigger checks only, re-derived below:
  the 0.0.11 review-cycle `selections.py` verdict ("module IS the
  consolidation point; adapters stay explicit" — first half confirmed by
  the singledef census, second half re-challenged as R-1) and the
  `dry-file-connection.md` R7/C22 rows (vocabulary owned here, connection
  follows — re-proved by the code-literal census, nothing inherited).

Sibling dirt (read-only; never edited): `optimizer/nested_fetch.py`
(worktree `29ce5201` vs HEAD `4d8d37a7`; no selections import — mechanism
context only), `optimizer/nested_planner.py` (worktree `e69dbf5f` vs HEAD
`0ad8ff5d`; single +9 advisory hunk at 609, every cited line outside it,
HEAD-identical), `optimizer/join_taxonomy.py` (worktree `e1cbb3e3` vs HEAD
`9b355a50`; no selections import — mechanism context only),
`optimizer/hints.py` (worktree `8064af14` vs HEAD `da46ef89`; hostile-guard
hunk at 60, cited `flag_names`/`skip` lines at 170/271 outside it),
`connection.py` (worktree `3c4d5dcb` vs HEAD `93e998f2`; hunks at 54/703/734,
every cited line outside them, HEAD-identical text confirmed),
`extensions/resource_policy.py` (worktree `583bf460` vs HEAD `52084078`;
charge arms added, zero removed lines touch the cited
`type_condition`/`.directives`/marker symbols — cited lines are
HEAD-identical context), `mutations/inputs.py` (+25, hunks at 430-518;
cited `"node"` line at 934 outside), `mutations/resolvers.py` (+33/-77
hostile-hardening; cited prose at 357/784 outside). Clean neighbors
fingerprinted in `## Freshness fingerprints`. Findings hold at worktree
AND HEAD.

Cross-file observation (not this file's rule; routed to the walker item /
optimizer folder pass, no defect): `walker.py:63-70` carries eight
underscore aliases for selections names, of which `_should_include`,
`_named_children`, `_node_children_with_runtime_prefix`, and
`_with_runtime_prefix` have no in-module body reader. `_should_include`
and `_is_fragment` are imported from `optimizer.walker` by
`tests/optimizer/test_walker.py`; the other three alias lines
(`_named_children`, `_node_children_with_runtime_prefix`,
`_with_runtime_prefix`) have no reader anywhere — `extension.py:142-144`
carries its own look-alike aliases which ARE read
(`extension.py:685-688`). Cheap re-export seams, no contract broken,
no behavior to pin; the walker item decides keep-vs-delete under
principle 11.

## Verification

### Matrix

Each axis discharged against the target's real surface (117 `.py`
package population; census per axis; probes read-only, no Django import,
no shared-tree pytest):

1. **Cross-flavor policy mirroring.** No flavor twin. The target is
   optimizer-internal; sibling flavors carry no selection-traversal
   compiler. `utils/directives.py::validated_field_directives`
   (family `hostile-directives-containment`, open) validates directives
   at field-definition time against hostile shapes — definition-time
   containment, not runtime `@skip`/`@include` evaluation (R-2,
   rejected with difference + trigger). `optimizer/hints.py:170,271`
   reads a hint-dict `"skip"` flag — optimizer-hint vocabulary, not the
   GraphQL directive (R-6). Forms / rest_framework / mutations / types
   carry no fragment/directive/response-key evaluator
   (`directives.get` code hits package-wide: this file only).
2. **Sync/async twins.** None owed. Probe asserts zero
   `AsyncFunctionDef`, zero `async def` / `await` / `sync_to_async`
   tokens in-file. All 19 functions are pure selection-object
   construction/inspection (no I/O, no await points); async callers
   reach them through the consolidated one-sync-boundary, never a
   second body.
3. **Derived rather than repeated knowledge.** Every derivation composes
   its owner by name: connection vocabulary via
   `utils/typing.py::schema_config_from_info` + the schema's
   `NameConverter.apply_naming_config` (forward resolution per
   `ATTENTION.md`); the python-name tuple derived from the dataclass
   itself (`_CONNECTION_FIELD_PYTHON_NAMES`, one line); the converted
   memo owned by `optimizer/_context.py` (family
   `optimizer-execution-frame`, reused F-0); Strawberry dataclasses +
   `convert_arguments` / `convert_directives` reused inside the mirror
   (never re-spelled). The AST-string census proves the negative:
   zero code uses of `"totalCount"` / `"pageInfo"` / `"hasNextPage"`
   outside this file (`probe_vocab.py`: all three `CODE-ZERO`).
4. **Inverse / round-trip pairs.** Two genuine pairs, each single-owned:
   `response_key` (one selection) vs `response_keys` (possibly merged;
   composes `response_key` by name at target line 372 — one grammar,
   two arities, not two definitions); `with_runtime_prefix` (clone
   primitive) vs `node_children_with_runtime_prefix` (filter + delegate
   by name at target line 495). `direct_child_selected` is the shared
   walk the two count halves compose by name — again one walk, three
   arities (`totalCount` / `hasNextPage` / their OR).
5. **Contracts restated in another medium.** Production + oracles + docs
   move together by design here, not as independent implementations:
   30 package tests pin each primitive (incl. identity, memo lifecycle,
   generator, count matrix, converter vocabulary); 4 live
   anonymous-fragment tests pin the mirror over HTTP; docstrings state
   each contract + several triggers. Counted as consumers/oracles/
   projections under each finding, never as definitions.
6. **Enforcement by omission.** Enumerated every converted-selection
   walk and checked its directive gate: `included_field_selections`
   filters; `named_children` filters; `node_children_with_runtime_prefix`
   filters its level; `direct_child_selected` filters (field and
   fragment shell); `connection_node_children` filters at both levels
   (edges/node via `named_children`, children via
   `node_children_with_runtime_prefix`); `with_runtime_prefix` clones
   WITHOUT filtering — by construction, not a gap: both call sites
   pre-filter (`node_children_with_runtime_prefix:493-495` and its own
   fragment recursion at 470-473), directives ride the clones, and the
   walker re-filters at each descent level (`walker.py:569,1265` via
   `_included_field_selections`; fragment shells re-gated at
   `walker.py:1371,1382`). `walker.py::_merge_aliased_selections`
   passes fragments through unfiltered, but both its call sites feed it
   already-filtered lists — no contract source demands merge-time
   filtering, so no gap is established. Absence investigated, none
   routed as defect.

### Enumeration

Instrument: every name in `ast.Module.body` of
`django_strawberry_framework/optimizer/selections.py` (no import of the
target; Django settings never touched). Probe:
`docs/dry/temp-tests/dry-file-optimizer__selections/probe_enumeration.py`
→ `top_level=30` (`FunctionDef` 19, `ClassDef` 1, `Assign` 2,
`ImportFrom` 7, `Expr` 1), `top_async=[]`, async tokens all zero.
`probe_singledef.py` → all 20 def/class names single-site
(`multi_site=NONE`). `probe_vocab.py` → the three camelCase GraphQL
names `CODE-ZERO` outside the target; `"edges"`/`"node"` code uses
exactly the five known sites (R-3/R-4/R-5 evidence).
`probe_consumers.py` → the consumer map cited in System trace.

22 rule-bearing top-level elements (19 functions + 1 class + 2 module
assigns; the 5 dataclass fields counted inside their owner's row). The
7 imports and the module docstring are consumers/projections, not rules.
Every rule-bearing member lands in exactly one home below; docstring
contract + trigger clauses are covered inside their owner's row. The
`TODO(BACKLOG ...)` pseudo block at target lines 376-389 is
ERA001-exempt design prose for a deferred card, not a rule.

| # | Member | Home |
|---|---|---|
| 1 | `ast_to_converted_selections` | F-A `anonymous-safe-converted-mirror` (definition; upstream-faithful) |
| 2 | `prime_selected_fields` | F-A (publish step of the same rule) |
| 3 | `ast_child_selections` | F-B `ast-child-iteration` (definition) |
| 4 | `resolve_unvisited_fragment` | F-C `fragment-visit-guard` (definition) |
| 5 | `directive_variable_names` | F-D `ast-directive-variable-extraction` (definition) |
| 6 | `is_fragment` | F-E `converted-fragment-discriminator` (definition) |
| 7 | `should_include` | F-F `converted-directive-evaluation` (definition) |
| 8 | `response_key` | F-G `response-key-grammar` (definition; composed by #9) |
| 9 | `response_keys` | F-G (merged arity; composes #8 by name) |
| 10 | `included_field_selections` | F-H `fragment-inlining-flatten` (definition; fast path + generator arms) |
| 11 | `named_children` | F-I `fragment-descending-name-match` (definition) |
| 12 | `with_runtime_prefix` | F-J `runtime-prefix-cloning` (clone primitive) |
| 13 | `node_children_with_runtime_prefix` | F-J (filter + delegate; composes #12 by name) |
| 14 | `ConnectionFieldNames` (+ 5 fields) | F-K `connection-vocabulary-resolution` (record sub-row) |
| 15 | `DEFAULT_CONNECTION_FIELD_NAMES` | F-K (fallback sub-row) |
| 16 | `_CONNECTION_FIELD_PYTHON_NAMES` | F-K (derivation sub-row) |
| 17 | `connection_field_names` | F-K (forward-resolution body) |
| 18 | `connection_node_children` | F-L `edges-node-unwrap` (definition) |
| 19 | `direct_child_selected` | F-M `count-observer-walks` (shared walk) |
| 20 | `connection_total_count_selected` | F-M (totalCount half; composes #19 by name) |
| 21 | `connection_has_next_page_selected` | F-M (hasNextPage half; composes #19 by name) |
| 22 | `connection_count_required` | F-M (OR composition; zero production callers — kept, see finding) |

No file-local rows: every member has a consumer outside the target, a
twin candidate discharged as a rejection, or a family home above (a row
naming a second site is a family or a rejection, never file-local). No
consolidation in this file item.

### Challenges

Change challenges posit a plausible rule change and count AUTHORITATIVE
definitions that must move (consumers / oracles / projections listed, not
counted). All `static-reviewed` against the pinned blob; inspection beats
execution on every challenge (body identity + def-census + code-literal
census decide each count), so no shared-tree pytest run was made.

- C1 (F-A): Strawberry stops crashing on anonymous inline fragments
  (upstream guards `type_condition`). Moves: the mirror's anonymous
  branch (1 definition — delete the `None` shell, keep the recursion);
  `prime_selected_fields` + memo + every consumer unmoved. Count: 1.
  Oracles: `test_ast_to_converted_selections_converts_anonymous_and_named_fragments`
  + 4 live anonymous-fragment tests.
- C2 (F-A): the memo key shape changes (e.g. graphql-core stops sharing
  node identity across rows). Moves: the `memo_key` probe (1); the
  `_context.py` memo store unmoved (F-0). Count: 1.
- C3 (F-B): a new AST node kind gains a selection set. Moves:
  `ast_child_selections` (1); both extension walkers + the mirror's
  `_convert` follow. Count: 1.
- C4 (F-C): a third visit-key axis (e.g. per-operation key). Moves:
  `resolve_unvisited_fragment` (1); the vars walk passes the new axis,
  the reachable walk keeps omitting it. Count: 1.
- C5 (F-D): a third tree-affecting directive (e.g. `@tag`). Moves:
  `directive_variable_names` (1); the vars walk follows. Count: 1.
- C6 (F-E): a third fragment shape (e.g. a Strawberry subclass without
  `type_condition`). Moves: `is_fragment` (1); walker merge gates,
  `included_field_selections`, `named_children`,
  `direct_child_selected` follow. Count: 1.
- C7 (F-F): `@skip` gains a third truthy spelling. Moves:
  `should_include` (1); every walk follows. Count: 1.
- C8 (F-G): the merged marker moves off `_optimizer_response_keys`.
  Moves: `response_keys` (1); walker merge writer + nested_planner
  readers follow. Count: 1.
- C9 (F-H): fragment inlining becomes type-conditional (the BACKLOG
  tri-state classifier). Moves: `included_field_selections` (1) + the
  walker-supplied classifier (new, walker-owned); both call sites
  follow. Count: 1 + 1 new adapter (designed, not landed).
- C10 (F-I): name matching goes alias-aware. Moves: `named_children`
  (1); extension slot walk + unwrap follow. Count: 1.
- C11 (F-J): prefixes move off `_optimizer_runtime_prefixes`. Moves:
  `with_runtime_prefix` (1); `node_children_with_runtime_prefix` +
  walker readers follow. Count: 1.
- C12 (F-K): a sixth structural field (e.g. `startCursor` observer).
  Moves: the `ConnectionFieldNames` declaration + fallback +
  derivation + resolver (1 machinery); `connection_field_names`
  callers (connection, extension, nested_planner) follow. Count: 1.
- C13 (F-K): the schema renames `totalCount` under a custom converter.
  Moves: 0 here (converter already authoritative); the three
  camelCase literals stay `CODE-ZERO`. Count: 0 here, 1 upstream.
- C14 (F-L): a second unwrap shape (e.g. mutation `<slot>` siblings).
  Moves: `connection_node_children` unmoved — the slot shape already
  lives beside it in `extension.py::mutation_payload_child_selections`
  composing `_named_children` + `_node_children_with_runtime_prefix`
  by name (R-7-noted distinct shape, not a second unwrap). Count: 1
  only if the shapes are unified; today 1 + 1 intentional sibling.
- C15 (F-M): `hasPreviousPage` becomes count-observable. Moves:
  `connection_has_next_page_selected` + `connection_count_required`
  (1 rule — the matrix test pins `previous_only is False` today);
  nested_planner split + connection resolve-time halves follow.
  Count: 1.
- C16 (F-M): the OR moves (e.g. AND semantics). Moves:
  `connection_count_required` (1 — zero production callers, so only
  the test matrix + prose cites move); the split halves unmoved.
  Count: 1.
- C17 (R-1): a third selection shape arrives (e.g. subscription
  payloads). Moves: 0 shared today — the AST and converted adapters
  have disjoint attribute shapes (`selection_set` vs `selections`,
  `DirectiveNode` vs dict); each gains its own branch. Count: 0
  (rejection evidence).
- C18 (R-2): runtime evaluation needs hostile-shape hardening.
  Moves: `should_include` unmoved today (converted directives carry
  live evaluated args, never hostile AST); hardening would ADD a
  validation call, not move the predicate. Count: 0 (rejection).
- C19 (R-3/R-4/R-5): the `"edges"`/`"node"` token changes. Moves:
  `ConnectionFieldNames` (1) + each considered site separately —
  and C13 shows none of them reads the converter, so each is its own
  rule (rejection evidence).

## Findings

Worker 0 note: families F-A..F-M are NAMED here for the plan's
`## Responsibility index` (F-0 reuses the consolidated
`optimizer-execution-frame` row; R-1..R-7 are rejections with contract
difference + trigger + home). No plan edit made from this item; no
consolidation in a file item — the family items decide gates.

### F-0 `optimizer-execution-frame` (reuse; owner `optimizer/_context.py`)

The converted-selection memo STORE (`converted_selections_memo`,
`begin/end_execution_frame`) is already consolidated under the
`optimizer-execution-frame` family (verified). This file is a consumer:
`ast_to_converted_selections` reads the memo, keys on node ids, and
writes the converted list (target lines 137-146, 191-193). The key
SHAPE (single-id fast path vs tuple) is selections-local and travels
with F-A; the store, frame lifecycle, and reset discipline stay with
F-0. Challenge C2 counts them separately (key 1, store 0). Oracles:
`test_ast_to_converted_selections_memoized_per_execution` (lifecycle +
rebuild-wrapper hit + outside-frame fresh-convert). No new row owed.

### F-A `anonymous-safe-converted-mirror` (new family; owner `optimizer/selections.py::ast_to_converted_selections`)

Contract: the connection path reads Strawberry-compatible converted
selections that survive spec-valid anonymous inline fragments at any
depth. Variation axes: fragment shape (anonymous vs named vs spread),
memo presence (installed frame vs direct caller), priming order (before
first `selected_fields` read). Sites: definition here (#1 mirror body,
#2 publish step); consumers `extension.py:1223` (`_node_selections`
fallback) and `connection.py:1341` (resolve-path priming);
upstream contract Strawberry `convert_selections` (+ `from_node`
recursions) at installed `.venv/.../strawberry/types/nodes.py:67-128`;
oracles the mirror-identity test
(`test_ast_to_converted_selections_converts_anonymous_and_named_fragments`),
the memo test, the priming lifecycle test
(`test_prime_selected_fields_lifecycle`), and 4 live
`test_anonymous_inline_fragment_*` tests; projections the
faithful-mirror docstring (byte-identity load-bearing claim) and the
silent-no-op NOTE. Challenges C1 (count 1), C2 (key 1, store 0).
Owner reasoning: narrowest module every legitimate consumer can import
without reversing a dependency — walker/extension/connection already
import it; the mirror touches only graphql-core AST types + stdlib +
two below-it helpers. Lifetime (principle 4): the converted list is a
pure derivation shared per execution — owner selections.py, validity
key the field-node id tuple, publish point `prime_selected_fields` /
memo write, mutability read-only (walker clones before mutating),
invalidation frame close. Behavioral proof: `static-reviewed` (body
read vs upstream source at the pinned version; anonymous branch is the
sole deviation, and it produces Strawberry's own dataclasses so
`isinstance` consumers hold) + oracle pin (identity test fails on any
non-anonymous divergence). Structural gate: the existing mirror +
priming + live tests (negative control owed at the family item:
hand-copy the mirror minus the `None` shell — every behavior oracle
passes except the anonymous-shape arms).

### F-B `ast-child-iteration` (new family; owner `optimizer/selections.py::ast_child_selections`)

Contract: one "iterate an AST node's children" implementation
(`getattr(selection_set)` + `selections or ()` → tuple;
`FragmentSpreadNode` yields `()`). Consumers: both extension walkers
(via `_child_selections` alias at `extension.py:140`), the mirror's
`_convert` (3 in-file call sites). Challenge C3, count 1. Oracles:
`test_ast_child_selections_returns_children_or_empty`. Proof:
`static-reviewed` (single body, alias is assignment).

### F-C `fragment-visit-guard` (new family; owner `optimizer/selections.py::resolve_unvisited_fragment`)

Contract: resolve-once-per-visit-key fragment-spread guard; key is the
bare name (reachable-fragment walk) or `(name, depth)` (vars walk, where
the same spread at two depths must walk twice — spec-033 Decision 7).
Consumers: `extension.py:304` (depth-aware) + reachable walk (via
`_unvisited_fragment_definition` alias, name-only). Challenge C4,
count 1. Oracles: both `test_resolve_unvisited_fragment_*` tests
(resolve-once + depth-keyed visits). Proof: `static-reviewed`.

### F-D `ast-directive-variable-extraction` (new family; owner `optimizer/selections.py::directive_variable_names`)

Contract: variable names inside `@skip`/`@include` `if` args only; every
other variable excluded; non-`DirectiveNode` objects skipped
(defensive, pinned by
`test_walk_cache_relevant_vars_ignores_non_directive_objects`).
Consumer: the vars walk (`extension.py:278`). Challenge C5, count 1.
Oracles: both `test_directive_variable_names_*` tests. Proof:
`static-reviewed`.

### F-E `converted-fragment-discriminator` (new family; owner `optimizer/selections.py::is_fragment`)

Contract: THE fragment-vs-field discriminator for converted selections,
duck-typed on `type_condition` (covers Strawberry classes + walker
`SimpleNamespace` shells + the mirror's `None`-condition shells).
Consumers: walker merge gates (`walker.py:1371,1382`, `seen_names`
probe), `included_field_selections`, `named_children`,
`with_runtime_prefix`, `direct_child_selected`. Challenge C6, count 1.
Oracles: `test_is_fragment_discriminates_on_type_condition` +
test_walker `_is_fragment` rows (via alias). Proof: `static-reviewed`
(one `hasattr`; every consumer composes by name or alias).

### F-F `converted-directive-evaluation` (new family; owner `optimizer/selections.py::should_include`)

Contract: evaluate live `@skip`/`@include` args on a converted
selection (`skip.if is True` → out; `include.if is False` → out;
directive-free fast path; unresolved variables stay selected —
oracles pin the last). Consumers: every converted walk (F-H..F-M) +
walker alias (test-re-exported; no in-module body reader — noted in
System trace). Challenge C7, count 1. Oracles:
`test_should_include_honors_skip_and_include` + 6 test_walker rows.
Proof: `static-reviewed`.

### F-G `response-key-grammar` (new family; owner `optimizer/selections.py::response_key`)

Contract: one selection's response key is `alias or name` (#8); a
possibly merged selection's keys are the `_optimizer_response_keys`
union or the singleton fallback (#9, composing #8 by name at target
line 372). Consumers: extension slot walk, walker merge + prefix math
(`walker.py:502-512,1394-1418`), nested_planner (`_response_keys`
alias at 7+ call sites). Homonym noted, not counted:
nested_planner's `relation_connection_to_attr(response_key=...)`
params are attr-grammar INPUTS in the consumer position, not a second
response-key definition. Challenge C8, count 1. Oracles:
`test_response_key_prefers_alias` +
`test_response_keys_reads_merged_marker_or_falls_back`. Proof:
`static-reviewed`.

### F-H `fragment-inlining-flatten` (new family; owner `optimizer/selections.py::included_field_selections`)

Contract: return included fields with fragment bodies inlined BEFORE
field merging; directives filter fragments and fields alike; identity
passthrough when already flat (mirroring walker's merge passthrough);
non-list/tuple iterables materialized once at entry (the silent-drop
fix: probe loop + rebuild loop would otherwise exhaust a generator
between them). Consumers: walker level descent (`walker.py:569`) and
the FK-id-elision scalar scan (`walker.py:1265`, audited as the
BACKLOG card's R2). Challenge C9, count 1 + 1 new walker-owned
classifier when the card lands (designed at both seams, unlanded).
Oracles: inline/filter test + identity test + generator test (the
last pins the found-by-probe silent drop). Proof: `static-reviewed`
+ oracle pin (generator arms fail pre-fix by construction).

### F-I `fragment-descending-name-match` (new family; owner `optimizer/selections.py::named_children`)

Contract: included direct children named `name`, recursing through
fragments without allocating shell wrappers. Consumers: the unwrap
(F-L), the extension slot walk (`_named_children` alias at
`extension.py:685`), the walker alias (readerless in-module — System
trace note). Challenge C10, count 1. Oracles:
`test_named_children_recurses_through_fragments`. Proof:
`static-reviewed`.

### F-J `runtime-prefix-cloning` (new family; owner `optimizer/selections.py::with_runtime_prefix`)

Contract: clone a node-level selection carrying runtime prefixes;
fragments descended-never-marked (marker lands on field leaves only);
`node_children_with_runtime_prefix` filters one level then delegates
by name (target line 495). Consumers: the unwrap (F-L), the extension
seam (`_node_children_with_runtime_prefix` alias), walker merge math
(`_selection_runtime_prefixes`, `_merge_runtime_prefixes`).
Challenge C11, count 1. Oracles:
`test_node_children_with_runtime_prefix_clones_with_prefix`.
Proof: `static-reviewed`.

### F-K `connection-vocabulary-resolution` (new family; owner `optimizer/selections.py::connection_field_names`)

Contract: a connection's five structural GraphQL names resolved
FORWARD from python attribute names through the active schema's
`NameConverter.apply_naming_config` (the `auto_camel_case=False`
closure: literal matching silently misreported `totalCount` /
`hasNextPage`, choosing `FetchMode.NONE` / raising on unset attrs).
Record `ConnectionFieldNames` (#14, camel-invariant `edges`/`node`
carried so no half resolves by another mechanism) + fallback
`DEFAULT_CONNECTION_FIELD_NAMES` (#15, direct/test callers without a
schema) + derivation `_CONNECTION_FIELD_PYTHON_NAMES` (#16, read off
the dataclass's own fields) + resolver body (#17, `None`/missing-converter
→ default). Consumers, all three by name:
`connection.py:1199` (`_connection_field_requested`),
`extension.py:656` (`_connection_node_child_selections`),
`nested_planner.py:1230` (window planning). Challenges C12 (count 1),
C13 (count 0 here — converter authoritative). Oracles: the four
`test_connection_field_names_*` tests (default camelCase, camel-off,
custom converter, unreachable-converter fallback) +
`test_connection_field_python_names_matches_dataclass_fields` +
`test_connection_predicates_consume_the_resolved_names`. Proof:
`static-reviewed` + code-literal census (three camelCase names
`CODE-ZERO` package-wide — the connection-file R7/C22 trigger
re-proved, not inherited).

### F-L `edges-node-unwrap` (new family; owner `optimizer/selections.py::connection_node_children`)

Contract: THE `edges { node { ... } }` composition — accumulate
response-key prefixes down both levels, clone node children with the
connection-aware prefix; `[]` when no `edges { node }` (pageInfo /
totalCount only). Shared by the root seam (`extension.py:659`) and
nested planning (`nested_planner.py`) so prefix semantics cannot drift;
`names` defaults to the F-K default vocabulary. Challenge C14
(count 1; the `<slot>` sibling is a distinct intentionally-separate
shape — R-7). Oracles: unwrap + empty-without-edges tests (prefix
math pinned field-by-field). Proof: `static-reviewed`.

### F-M `count-observer-walks` (new family; owner `optimizer/selections.py::direct_child_selected`)

Contract: count OBSERVABILITY (spec-033 Decision 4) — `totalCount` as a
direct connection child (#20) or `hasNextPage` under a direct
`pageInfo` child (#21), each through fragment wrappers only (a
node-level nested `totalCount` must NOT fire the outer predicate —
oracles pin), each gated on live directives; the generic OR (#22)
composes both halves by name. Consumers: plan-time split halves at
`nested_planner.py:1353-1354` (split to avoid re-walking; prose there
defines the split AS the OR — the OR's contract, not a second
definition) and resolve-time `_connection_field_requested` at
`connection.py:1200` via `_total_count_requested` /
`_has_next_page_requested`. Kept-with-note: #22 has ZERO production
callers (`connection_count_required(` hits: def + tests/prose only) —
kept because it is the spec-named generic gate with direct oracles
(the 7-arm matrix: edges-only False, total True, hasNext True,
previous-only False, fragment-wrapped True, skipped False,
nested-only False) and the halves' split contract is stated in terms
of it; trigger for deletion under principle 11: a production caller
needing the un-split OR, or the halves' split becoming the stated
contract instead. Challenges C15/C16 (count 1 each). Proof:
`static-reviewed` + matrix pin (each arm fails if its walk drifts).

### Rejections

- R-1 (C17): one polymorphic walker over both adapters. Difference:
  AST nodes (`selection_set`, `DirectiveNode`, fragment definitions in
  a side map) and converted selections (`.selections`, directive dicts,
  inline shells) have disjoint attribute shapes — a shared walker
  would branch on shape at every level, the exact over-generic
  merger the module docstring records as the anti-goal. Trigger: a
  THIRD selection shape both adapters must serve. Home: this module's
  docstring adapter-split clause (owner of the separation).
- R-2 (C18): `should_include` vs
  `utils/directives.py::validated_field_directives` (family
  `hostile-directives-containment`, open). Difference: definition-time
  hostile-shape validation vs runtime live-arg evaluation on already-
  converted selections — separate inputs, separate reasons to change.
  Trigger: runtime evaluation needing hostile hardening. Home: the
  directives family (`utils/directives.py`).
- R-3: `resource_policy.py` AST reads (`type_condition` at 1199/1219-1220,
  `.directives` walks at 1070-1239, `_CONNECTION_MARKER_FIELD`/
  `_EDGE_MARKER_FIELDS` at 179-180) vs F-E/F-D/F-K. Difference:
  charge-document cost attribution over the AST (how much a shape may
  cost) vs plan-time selection matching (what to prefetch / observe) —
  same tokens, disjoint contracts; the cited lines are HEAD-identical
  context under the worktree charge arms. Trigger: resource_policy
  moving its walk onto converted selections. Home: resource_policy
  charge-document owner.
- R-4: `connection.py:275 type_def.get_field("edges")` vs F-K/F-L.
  Difference: schema-TYPE introspection (does this connection type
  carry an edges field) vs per-QUERY selection matching. Trigger: the
  connection factory deriving field presence from the converter
  vocabulary. Home: `connection.py` factory.
- R-5: `mutations/inputs.py:934` payload `"node"` slot +
  `lateral_fetch.py:709` `("node", ...)` recognizer tag vs F-K/F-L.
  Difference: payload-slot naming / strategy-signature tagging vs
  GraphQL selection names. Trigger: either site matching document
  selections by name. Home: respective owners.
- R-6: `hints.py:170,271` `"skip"` hint flag vs F-D/F-F. Difference:
  optimizer-hint dict vocabulary (`force_select`/`force_prefetch`/
  `skip`) vs the GraphQL `@skip` directive. Trigger: hints honoring
  document directives. Home: `optimizer/hints.py`.
- R-7 (C14): `extension.py::mutation_payload_child_selections` (one
  `<slot>` level via `_named_children` +
  `_node_children_with_runtime_prefix`) vs F-L. Difference: sibling
  shapes sharing primitives by name, not one unwrap with a mode flag —
  unifying them saves one closure while coupling the Relay and
  mutation-payload seams. Trigger: a third unwrap shape. Home: the
  F-L family (unwrap owner records the sibling).

## Defects

None. Audited and cleared: the `connection.py` "SAME implementation
the plan-time `connection_count_required` uses" prose reads (upon body
inspection) as "the same implementation `connection_count_required`
itself uses internally" — true (the OR composes the halves at target
lines 717-720); the nested_planner split is the documented
re-walk avoidance, not a drift. The `prime_selected_fields`
silent-no-op NOTE is documented with its live-test regression net
(4 anonymous-fragment tests), not a fail-open. The four
readerless walker aliases are a keep-or-delete question for the
walker item (System trace), not a behavior defect. The BACKLOG
classifier block is in-scope pseudo (ERA001-exempt), not drift.

## Pending execution

None. Every challenge discharged by inspection (single-body identity +
def-census + code-literal census); no `execution-deferred` proof and
no `gate:` witness owed. No shared-tree pytest run was made.

## Judgment

Zero-edit file item: the target is the package's single-owned
selection-traversal substrate and the censuses confirm it — 20/20
definitions single-sited, three camelCase names code-zero outside it,
every consumer composing by name, every walk directive-gated, prior
review claims re-proved rather than inherited. Thirteen families named
(F-0 reuse + F-A..F-M new) and seven rejections recorded with triggers
for Worker 0; consolidation, if any, lives in the family items.

## Freshness fingerprints

HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e`. Target
`django_strawberry_framework/optimizer/selections.py` clean:
worktree `a48f6172c6f04331740d1b110d742f17701ff846` = HEAD (720
lines). Item-scoped diff vs `a48f6172c6f04331740d1b110d742f17701ff846`
on target + artifact path: EMPTY (no production edit; this artifact is
the only new file, untracked). Neighbors (worktree read; HEAD
alongside where dirty): `optimizer/walker.py` clean `9b111ed9` both
(incl. the ledgered D1 seal-policy row — read, untouched);
`optimizer/extension.py` clean `49667a93` both;
`optimizer/nested_planner.py` worktree `e69dbf5f` vs HEAD `0ad8ff5d`
(hunk at 609 only; import block, annotation, split observers, and
prose cites HEAD-identical); `optimizer/nested_fetch.py` worktree
`29ce5201` vs HEAD `4d8d37a7` (`resolve_strategy` dirt only; no
selections import); `optimizer/join_taxonomy.py` worktree `e1cbb3e3`
vs HEAD `9b355a50` (composite-pk dirt; no selections import);
`optimizer/hints.py` worktree `8064af14` vs HEAD `da46ef89` (hunk at
60 only); `optimizer/lateral_fetch.py` clean `db1ea315` both;
`optimizer/plans.py` clean `cce98531` both; `optimizer/_context.py`
clean `3d8dcfdf` both; `utils/typing.py` clean `de6309f6` both;
`utils/directives.py` clean `380786cf` both; `utils/connections.py`
clean `f549389e` both; `connection.py` worktree `3c4d5dcb` vs HEAD
`93e998f2` (hunks 54/703/734; all cited lines HEAD-identical);
`extensions/resource_policy.py` worktree `583bf460` vs HEAD `52084078`
(zero removed lines touch cited symbols); `mutations/inputs.py`
worktree `fcbb964d` vs HEAD `fc442047` (hunks 430-518; cited line 934
outside); `mutations/resolvers.py` worktree `a322d17a` vs HEAD
`3fd1e571` (hostile-name hunks; cited prose outside);
`tests/optimizer/test_selections.py` clean `04bbb23d` both (30 tests);
`tests/optimizer/test_walker.py` clean `5bbd7a56` both;
`tests/test_relay_connection.py` clean `b6bd90d9` both; upstream
`.venv/.../strawberry/types/nodes.py` at installed strawberry 0.324.0
(floor pin `strawberry-graphql>=0.316.0`; untracked, version-recorded
not hashed). Searched population: 117 `.py` under
`django_strawberry_framework` + package tests + fakeshop suites
(431 files in probe scans). Any fingerprint change reopens.

## Independent verification (Worker 2)

Phase 1 only: no verdict on Worker 1, no status set, no production edit owed (file item).
Independence note: one repo-wide grep before scoping briefly surfaced artifact-line
fragments; the artifact was never opened, nothing from it is recorded or relied on below.
Families, names, counts, and owners are my own.

### Enumeration (Worker 2, own instrument)

Instrument: every name in `ast.Module.body` of
`django_strawberry_framework/optimizer/selections.py` (720 lines).
`len(Module.body)` = 30: 1 module docstring + 7 `ImportFrom` + 19 `FunctionDef` +
1 `ClassDef` (`ConnectionFieldNames`, 5 `AnnAssign` field members) + 2 `Assign`
(`DEFAULT_CONNECTION_FIELD_NAMES`, `_CONNECTION_FIELD_PYTHON_NAMES`).
Nested defs `_convert` (in `ast_to_converted_selections`) and `_check` (in
`direct_child_selected`) travel with their parents. Named-member count: 22.
Every member is assigned below; nothing is file-local; rejections carry contract
difference + trigger.

| # | Member | Worker-2 family (my naming) |
|---|--------|------------------------------|
| 1 | `ast_to_converted_selections` | W2-F-CONVERT `ast-to-converted-mirror` |
| 2 | `prime_selected_fields` | W2-F-CONVERT `ast-to-converted-mirror` |
| 3 | `ast_child_selections` | W2-F-AST `ast-walk-substrate` |
| 4 | `resolve_unvisited_fragment` | W2-F-AST `ast-walk-substrate` |
| 5 | `directive_variable_names` | W2-F-AST `ast-walk-substrate` |
| 6 | `is_fragment` | W2-F-CONV `converted-selection-substrate` |
| 7 | `should_include` | W2-F-CONV `converted-selection-substrate` |
| 8 | `response_key` | W2-F-CONV `converted-selection-substrate` |
| 9 | `response_keys` | W2-F-CONV `converted-selection-substrate` |
| 10 | `included_field_selections` | W2-F-CONV `converted-selection-substrate` |
| 11 | `named_children` | W2-F-CONV `converted-selection-substrate` |
| 12 | `with_runtime_prefix` | W2-F-CONV `converted-selection-substrate` |
| 13 | `node_children_with_runtime_prefix` | W2-F-CONV `converted-selection-substrate` |
| 14 | `ConnectionFieldNames` (+ 5 fields) | W2-F-CONN `connection-vocabulary-and-unwrap` |
| 15 | `DEFAULT_CONNECTION_FIELD_NAMES` | W2-F-CONN `connection-vocabulary-and-unwrap` |
| 16 | `_CONNECTION_FIELD_PYTHON_NAMES` | W2-F-CONN `connection-vocabulary-and-unwrap` |
| 17 | `connection_field_names` | W2-F-CONN `connection-vocabulary-and-unwrap` |
| 18 | `connection_node_children` | W2-F-CONN `connection-vocabulary-and-unwrap` |
| 19 | `direct_child_selected` | W2-F-COUNT `count-observer-walks` |
| 20 | `connection_total_count_selected` | W2-F-COUNT `count-observer-walks` |
| 21 | `connection_has_next_page_selected` | W2-F-COUNT `count-observer-walks` |
| 22 | `connection_count_required` | W2-F-COUNT `count-observer-walks` |

Rejections (considered, not consolidated): (a) merging AST `directive_variable_names`
(names-set for the plan-cache key) with converted `should_include` (boolean gate for
planning) — contract difference: variable-identity collection (superset-safe,
depth-independent) vs per-selection inclusion verdict (skip-precedence boolean);
trigger: a cache-key design that needs booleans instead of names. (b) merging
`connection_count_required` (generic OR) into the planner's split observers —
contract difference: observability predicate vs per-observer fetch-mode inputs
(`nested_planner.py` 1353-1354 feeds them separately to `WindowRangePlan.fetch_mode`);
trigger: planner stops splitting total vs has-next inputs.

Routed to holding (file item owes no edit): H-1 `optimizer-marker-attribute-protocol`
(`_optimizer_response_keys` written `walker.py` 1395-1396/1418, read `selections.py`
372; `_optimizer_response_key_arguments` written `walker.py` 1422, read
`walker.py` 1455/1510 + `nested_planner.py` 1167; `_optimizer_runtime_prefixes`
written `selections.py` 481 + `walker.py` 1419/1531-1536, read `walker.py` 505-506/1520;
`_optimizer_response_key_argument_conflict` written/read `walker.py` 1459/1493):
round-trip write/read pairs sharing private-name literals across modules.
H-2 walker compat aliases with no production/test readers
(`walker.py` `_named_children`, `_node_children_with_runtime_prefix`,
`_with_runtime_prefix` — verified zero `_(...)` call sites; observation only, target
definitions themselves are live). H-3 `connection_count_required`
zero-production-caller status (see definition-count section).

### Matrix discharged (Worker 2, searches run)

1. Cross-flavor mirroring: searched `is_fragment|should_include|response_key|
included_field_selections|named_children|with_runtime_prefix|
node_children_with_runtime_prefix` across `django_strawberry_framework/` — hits only
in `optimizer/` (`selections.py`, `walker.py`, `extension.py`, `nested_planner.py`)
and `connection.py`. Sibling flavors (types/filters/orders/mutations/forms/
rest_framework) carry no selection-tree traversal. No second owner. Discharged.
2. Sync/async twins: `selections.py` contains zero `AsyncFunctionDef` (AST scan);
all walks are pure sync over already-materialized selections. The sync/async split
lives in `connection.py` resolve paths, which share these pure predicates rather
than twinning them. No twin. Discharged with reason.
3. Derived-not-repeated: connection vocabulary is derived once via
`connection_field_names` through the schema `NameConverter`
(`apply_naming_config` over `_CONNECTION_FIELD_PYTHON_NAMES`); hardcoded-literal
search (`"totalCount"|"pageInfo"|"hasNextPage"` etc.) finds only the `ConnectionFieldNames`
defaults (the documented fallback), one prose recollection in `connection.py` 1211,
and unrelated `Meta.connection['total_count']` consumer config keys. No literal
re-derivation at walk sites (`connection.py` 1199, `extension.py` 656,
`nested_planner.py` 1230 all resolve through the owner). Response keys are computed
by `response_key`, never re-concatenated. Discharged.
4. Inverse/round-trip: no AST<->converted inverse exists (one direction only).
Live pairs found and checked: (a) plan-time observers
(`connection_total_count_selected`, `connection_has_next_page_selected`) called from
both `nested_planner.py` 1353-1354 and `connection.py` 1230/1249 via
`_connection_field_requested` — one implementation, two callers (consumer sites, not
definitions). (b) `_optimizer_response_keys` write (`walker.py`) / read
(`selections.py::response_keys`) — shared private literal, routed to H-1, not
consolidated here. (c) Window-range `Q`-render (`plans.py::apply_window_pagination`)
vs raw-SQL render (`lateral_fetch.py::build_lateral_sql`) share
`window_range_plan` decisions — owned outside this target; noted, not touched.
Discharged with H-1 routed.
5. Contracts in other media: oracles READ, never run (`tests/optimizer/test_selections.py`,
722 lines, covers all 19 functions + vocabulary + memo + anonymous/named fragments;
`tests/optimizer/test_walker.py` imports `_should_include`/`_is_fragment` from the
walker aliases; live suites `examples/fakeshop/test_query/` cover anonymous inline
fragments and count observers end to end). Oracles build inputs from
`graphql.parse` + `SimpleNamespace` shells — never read the owner they check.
Prose projections: target module docstring, `connection.py` 1203-1248 predicate
docstrings, `nested_planner.py` 1333-1354 comment. Each site role-tagged in findings
below; no oracle rewrite. Discharged.
6. Enforcement by omission (family enumerated, each member checked): fragment gates
present in `included_field_selections` (fragments + fields), `named_children`
(filter-then-recurse, excluded fragment prunes subtree), `node_children_with_runtime_prefix`
(level filter), `direct_child_selected` (both levels). Pure accessors correctly
gateless: `is_fragment`, `response_key(s)`, `ast_child_selections`,
`resolve_unvisited_fragment`, `connection_field_names`. `with_runtime_prefix`
descends fragment children without re-filtering — verified benign: it preserves the
`directives` dict on every clone and all three consumer pipelines
(root seam, nested planner, mutation-payload extractor) descend through
`_walk_selections` -> `included_field_selections` before planning, so no unfiltered
consumption path exists. `connection_count_required` inherits both observers' gates
(pinned by oracle matrix incl. skipped/nested cases). No omission gap. Discharged.

AST-walking rules vs upstream (fidelity): `ast_child_selections` mirrors the
`getattr(<node>.selection_set, "selections", [])` idiom Strawberry's
`convert_selections`/`SelectedField.from_node`/`InlineFragment.from_node`/
`FragmentSpread.from_node` repeat (`.venv/.../strawberry/types/nodes.py`
107-109/129-130/153-155) — centralized, faithful. `resolve_unvisited_fragment`
mirrors `graphql.execution.collect_fields.collect_fields_impl` spread handling
(name-keyed `visited_fragment_names` + `fragments.get`) and extends it with the
`(name, depth)` key for the variable walk — divergence stated in its docstring
(spec-033 Decision 7 spread-site depth). `should_include` (converted) mirrors
`collect_fields.should_include_node` (skip-precedence, `if True`/`if False`
semantics) over already-evaluated directive dicts — faithful. `response_key`
mirrors `get_field_entry_key` (alias else name) — faithful.
`ast_to_converted_selections` mirrors `convert_selections` + the three `from_node`
constructors — one stated fix: anonymous inline fragments build
`type_condition=None` instead of dereferencing the missing condition (upstream
`nodes.py` 128 crashes). `directive_variable_names` is package-owned (no upstream;
cache-key concern), restricted to `@skip`/`@include` `VariableNode` args.
Fragment coverage: named spread, inline named, inline anonymous in both adapters
(converted pinned by `test_ast_to_converted_selections_converts_anonymous_and_named_fragments`;
AST spread/definition recursion pinned by reachable + cache-var walk tests).
Directive coverage: `@skip`/`@include` on fields, fragment shells, spread nodes,
and inside fragment bodies, both adapters. `does_fragment_condition_match`
(type-condition vs runtime type) is intentionally NOT mirrored: INLINE-all is the
documented design (module docstring + staged TODO), safe as over-approximation
(unknown names miss `field_map` and `continue`), and abstract roots never reach the
walker (`extension.py` 1163-1170 passes through when `model_for_type` is None).

### Definition counts per posited change (Worker 2)

- R1 fragment-vs-field discrimination (change: a new selection kind): 1
(`is_fragment`; `walker`/`extension`/`nested_planner` call sites are consumers).
- R2 directive evaluation, converted (change: third directive / new precedence): 1
(`should_include`; `included_field_selections`/`named_children`/
`node_children_with_runtime_prefix`/`direct_child_selected` consume).
- R3 directive variables, AST (change: new cache-key directive): 1
(`directive_variable_names`; `_walk_cache_relevant_vars` consumes).
- R4 response key (change: alias-vs-name rule): 1 (`response_key`; `response_keys`
composes it by name; walker merge/marker writes are the H-1 protocol, listed not
counted).
- R5 fragment inlining (change: new wrapper kind to inline or prune): 1
(`included_field_selections`; walker level-descent + FK-elision scan consume).
- R6 child search (change: search semantics): 1 (`named_children`; extension slot
extractor + `connection_node_children` consume).
- R7 prefix cloning (change: prefix shape): 1 per layer —
`with_runtime_prefix` (clone), `node_children_with_runtime_prefix` (level filter,
calls R7-clone by name), `connection_node_children` (edges->node composition, calls
both by name). Each change touches exactly its layer.
- R8 AST child iteration (change: new AST node shape with children): 1
(`ast_child_selections`; both AST walks + `_convert` consume).
- R9 fragment-resolve guard (change: new keying axis): 1
(`resolve_unvisited_fragment` `depth` param already spans name-key and
(name, depth)-key; both walks consume).
- R10 AST->converted mirror (change: Strawberry gains a field/shape): 1 conversion
(`ast_to_converted_selections`) + 1 prime (`prime_selected_fields`, idempotent
seeding) + memo owned by `_context.converted_selections_memo` (principle 4:
owner `_context.py::_ExecutionFrame`; validity key = field-node ids mirroring
graphql-core's subfields cache; published in `on_execute`; mutated only by the
memo writer; invalidated at frame end; `None` outside managed execution).
- R11 connection vocabulary (change: new structural field / converter knob): 1
(`connection_field_names`; `ConnectionFieldNames` record + defaults + python-name
tuple are its one declaration; `connection.py`/`extension.py`/`nested_planner.py`
consume).
- R12 count observers (change: 4th observable field): 1 (new primitive composing
`direct_child_selected` by name) + 1 (extend the `connection_count_required` OR);
existing primitives unchanged. `connection_count_required` itself has zero
production callers (verified: only its `def` + prose/test mentions package-wide);
the planner consumes the split observers (`nested_planner.py` 1353-1354) and
resolve-time consumes them via `_connection_field_requested`. What breaks if
`connection_count_required` were removed: `test_connection_count_required_matrix`
+ `test_connection_predicates_consume_the_resolved_names` fail; production
behavior unchanged. Kept-or-deleted is H-3's question, not this item's; oracles
stay independent either way.

### Owners (Worker 2, principle 7)

All rules stay owned by `optimizer/selections.py` (module docstring already states
the two-adapter grammar — principle 10 satisfied): the narrowest cohesive owner
every legitimate consumer (`walker.py`, `extension.py`, `nested_planner.py`,
`connection.py`) can already import without reversing a dependency (selections
imports only graphql-core AST types + stdlib + below-it `_context`/`utils/typing`;
verified cycle-safe direction). R2/R3 stay separate (different contracts/consumers).
R12's shared walk stays on `direct_child_selected` (fragment-only recursion is the
load-bearing contract both halves need). H-1's marker-name literals would belong to
their holding family if ever consolidated — not here.

### Defects (Worker 2)

None. Explicit attention items, each checked, none a contract break with a reaching
input: (a) upstream-mirror fidelity — every mirror faithful or diverged with a
stated reason recorded above; sub-note (not a defect): `_convert`'s `else` branch
treats any non-inline non-spread node as a field where upstream `convert_selections`
raises `TypeError` — unreachable under validation (`FieldNode |
FragmentSpreadNode | InlineFragmentNode` exhaustive), no wire input reaches it.
(b) zero-caller members — none: every definition has intra-module and/or
cross-module and/or oracle callers (call-site tables above); `connection_count_required`
has zero *production* callers with test-oracle callers — routed to H-3, no
behavioral contract broken (planner's split consumption is the documented design).
(c) designed-but-unlanded machinery — the BACKLOG tri-state classifier TODO is
comment-only pseudocode (no executable classifier exists to be dead code); it is
unreached by construction (`extension.py` 1163-1170 abstract passthrough verified
by inspection); staged-slice marker format names card + contract, per convention.
Not a defect. (d) `with_runtime_prefix` unfiltered descent — all consumer pipelines
gate downstream (matrix axis 6); no reaching unfiltered input. Not a defect.

### Freshness fingerprints (Worker 2)

HEAD = `bfaee91dcd332a5f86250fff90ab21b377bc674e`.
Target `optimizer/selections.py` worktree-clean: HEAD `a48f6172c6f04331740d1b110d742f17701ff846`
= worktree `a48f6172c6f04331740d1b110d742f17701ff846` (720 lines).

| Inspected input | HEAD blob | Worktree blob | Attribution for relied-on lines |
|---|---|---|---|
| `optimizer/selections.py` | `a48f6172`…`f846` | identical (clean) | — |
| `optimizer/extension.py` | `49667a93`…`19a2a` | identical (clean) | — |
| `optimizer/walker.py` | `9b111ed9`…`81e8` | identical (clean) | — |
| `optimizer/plans.py` | `cce98531`…`f036` | identical (clean) | — |
| `optimizer/lateral_fetch.py` | `db1ea315`…`99a9` | identical (clean) | — |
| `optimizer/_context.py` | `3d8dcfdf`…`01a9` | identical (clean) | — |
| `utils/typing.py` | `de6309f6`…`e334` | identical (clean) | — |
| `tests/optimizer/test_selections.py` | `04bbb23d`…`7732` | identical (clean) | oracle, read only |
| `tests/optimizer/test_walker.py` | `5bbd7a56`…`8cb8` | identical (clean) | oracle, read only |
| `optimizer/nested_fetch.py` | `4d8d37a7`…`3e28` | `29ce5201`…`66af` (dirty) | worktree hunk = `resolve_strategy` hostile-`__class__` hardening only; relied-on seam docstring unaffected — valid on both |
| `optimizer/nested_planner.py` | `0ad8ff5d`…`87e0` | `e69dbf5f`…`91d6` (dirty) | worktree hunk = `_advise_composite_index` M2M silence only; relied-on lines (imports 66-75, `_connection_node_selections` 763-781, vocabulary/observers 1224-1231/1333-1354) identical in HEAD and worktree |
| `connection.py` | `93e998f2`…`c75a` | `3c4d5dcb`…`98d6` (dirty) | worktree hunks = `from_base64` import + negative-cursor guard only; relied-on lines (imports 89-94, `_connection_field_requested` 1192-1249) identical in HEAD and worktree |
| `.venv/.../strawberry/types/nodes.py` | n/a (not in git) | `e12929f8`…`34d` | upstream mirror source |
| graphql-core `execution/collect_fields` | n/a | graphql-core 3.2.8 (`should_include_node`, `get_field_entry_key`, `collect_fields_impl`, `does_fragment_condition_match` source-read) | upstream mirror source |
| `GOAL.md` Trust boundary | HEAD tree | worktree (unmodified per status) | contract source |

Searches executed (all read-only, no pytest): `ast.Module.body` enumeration of the
target; package-wide caller searches per symbol (production vs test split);
`_...(` call-site verification in walker/extension/nested_planner/connection/
selections; `_optimizer_*` literal-spelling census; hardcoded-vocabulary literal
search; upstream source reads (Strawberry `nodes.py` whole; graphql-core
`collect_fields` four functions); oracle reads (`test_selections.py` whole,
`test_walker.py` alias imports); worktree-vs-HEAD diff attribution for the three
dirty neighbors. No execution proofs owed (zero-edit file item; principle 8
n/a — no consolidation proposed).

PHASE-1-TRACE-RECORDED — artifact: `docs/dry/dry-file-optimizer__selections.md`

## Reconciliation (Worker 2, phase 2)

Verdict: `verified`. No production edit, no new tests, no defects found.
Phase-1 integrity: my trace above is unchanged and unedited; every position
reconciled below against Worker 1's record challenge-by-challenge. Groupings
did not align (my 5 coarse coverage families vs their 13 rule families) —
reconciled per rule, nothing sampled.

### Enumeration map

30 = 30 (19 `FunctionDef`, 1 `ClassDef`, 2 `Assign`, 7 `ImportFrom`, 1 `Expr`;
zero async — my AST scan agrees). 22 rule-bearing members map 1:1 onto their
table: my #1-2 = F-A, #3 = F-B, #4 = F-C, #5 = F-D, #6 = F-E, #7 = F-F,
#8-9 = F-G, #10 = F-H, #11 = F-I, #12-13 = F-J, #14-17 = F-K, #18 = F-L,
#19-22 = F-M. The 5 dataclass fields ride F-K; nested `_convert`/`_check`
ride F-A/F-M; the TODO pseudo block (376-389) is design prose, not a rule —
agreed. Zero file-local rows — agreed (every member has an outside consumer,
a discharged twin, or a family home).

### Family-grouping verdict

Worker 1's finer split stands; my coarse families were coverage backstop
groupings and are superseded as follows: W2-F-AST splits into F-B/F-C/F-D
(three contracts: child iteration vs visit guard vs variable extraction;
separate consumers C3/C4/C5 each count 1 — one rule each, my lump was
under-split). W2-F-CONV splits into F-E/F-F/F-G/F-H/F-I/F-J (same reason;
C6/C7/C8/C9/C10/C11 each count 1). W2-F-CONN splits into F-K/F-L
(vocabulary resolution vs unwrap composition; C12/C13 vs C14). W2-F-CONVERT
= F-A and W2-F-COUNT = F-M exactly — adopted unchanged. Holdings collapse:
H-1 (marker-attribute protocol) folds into F-G/C8's writer+reader follow-list
(same sites, no separate row owed); H-3 (OR zero-production-caller status)
folds into F-M's kept-with-note + deletion trigger (same evidence, same
trigger); H-2 (walker readerless aliases) is identical to their cross-file
observation, already routed to the walker item — stands routed, no row here.
Index corrections: NONE. All 13 new rows verified present in
`docs/dry/dry-0_0_15.md` (F-A at family line 642, F-B..F-L at 643-653, F-M
at 654; F-0 consolidated at 612); owners and holding items as named.
Worker 0 tick: file item `optimizer/selections.py` (plan line 192) may be
ticked `verified` with no pending execution.

### Divergence (i): zero-caller members — SETTLED, both right at stated scopes

Open the OR (`connection_count_required`): production callers = 0, confirmed
independently — zero `connection_count_required(` hits in
`django_strawberry_framework/` (def + prose/test mentions only); dirty
neighbors don't call it (`nested_planner.py` consumes the split halves at
1353-1354; `connection.py` consumes the halves via `_connection_field_requested`);
walker dead aliases (H-2) are unrelated names. Total callers = 2 test
functions (`test_connection_count_required_matrix`,
`test_connection_predicates_consume_the_resolved_names`). So Worker 1's
"zero production callers — kept" is correct at production scope and my "none
fully caller-less" is correct at total scope: no conflict. Resolution stands:
kept as the spec-named generic gate with direct oracles, deletion trigger
recorded (a production caller needing the un-split OR, or the split becoming
the stated contract). Under principle 11 this is a keep-with-trigger, not a
deletion demand — F-M's note already encodes it; H-3 adds nothing further.

### Divergence (ii): designed-but-unlanded classifier — SETTLED, agree

No executable classifier exists anywhere: both TODO blocks (target 376-389
and the walker-seam counterpart) are comment-only pseudocode, ERA001-exempt
anchors naming the BACKLOG card + spec-035 Decisions 6/7. "Designed-unlanded
at both seams" describes where the staged design is recorded, not execution —
nothing executes at either seam. Single entry guard covers both: abstract
roots pass through at `extension.py:1163-1170` (`model_for_type` None → return
unchanged), and the walker seam runs only downstream of that resolution, so
no abstract field ever reaches `included_field_selections`. Not dead code
(no machinery to delete); staged-slice marker per convention. Agreed fully.

### Rejection/holding map (R-1..R-7 judged)

- R-1 (polymorphic walker, C17 count 0): ACCEPT. Confirmed from my trace —
  disjoint attribute shapes (`selection_set`+`DirectiveNode`+side-map vs
  `.selections`+directive-dicts+shells); a shared walker branches per level.
  Home (module-docstring separation clause) correct.
- R-2 (runtime eval vs `validated_field_directives`): ACCEPT. Token verified
  (`utils/directives.py:53`, label+directives signature = definition-time);
  my `should_include` reads live converted dicts (phase 1) — separate inputs,
  separate change reasons. Home (directives family) correct.
- R-3 (resource_policy AST reads): ACCEPT. Tokens verified at cited lines
  (179-180 markers; 964/989/996 cost-shape walk; 1199/1219-1220
  `type_condition` reads; file dirty but cited lines are context outside the
  charge-arms hunks per Worker 1 attribution, token presence confirmed at
  worktree). Same-token/disjoint-contract reading accepted on stated evidence.
- R-4 (`connection.py:275` edges introspection): ACCEPT. Line verified;
  schema-type presence vs per-query matching is an evident contract split.
- R-5 (payload `"node"` slot + lateral `("node", ...)` tag): ACCEPT. Verified
  (`mutations/inputs.py:930-934` slot naming; `lateral_fetch.py:708-712`
  signature tag — cite reads 709, tag spans 708-712, same site). Naming vs
  selection-matching split accepted.
- R-6 (hints `"skip"` flag): ACCEPT. Verified (`hints.py:170,271`); hint-dict
  vocabulary vs GraphQL directive accepted.
- R-7 (mutation `<slot>` sibling vs F-L): ACCEPT from my own phase-1 read
  (`extension.py:668-695` composes `_named_children` +
  `_node_children_with_runtime_prefix` by name for a one-level shape) —
  intentional sibling, no mode flag. Trigger (third unwrap shape) + home
  (F-L records the sibling) correct.
- My rejection (a) (AST-vars vs converted-bool): consistent with the F-D/F-F
  split + C5/C7 — same verdict at finer grain, no separate row. My (b): folded
  into F-M kept-with-note (above). No surviving independent holdings.

### No-defect agreement

Agreed: no defects. Their four cleared audits vs mine: connection prose
(true — OR composes halves at 717-720; split is re-walk avoidance), priming
NOTE (documented + live-test net), walker aliases (routed, not behavior),
BACKLOG block (in-scope pseudo) — all compatible with my (a)-(d), which were
explicit non-defects. One asymmetry, no conflict: my `_convert` else-branch
vs upstream `TypeError` note (unreachable — `SelectionNode` union
exhaustive) and their merge-passthrough call-site feeding note (stronger
axis-6 evidence than mine) — both point the same way: no gap, no defect.
No `(Worker 2)` entries added under `## Defects` because there is nothing to
home — Worker 0 owes no defect card from this item.

### Proof adequacy + freshness + AGENTS.md prose

`## Pending execution`: none — JUDGED ADEQUATE. Every challenge decides
definition singularity (body identity + def-census + literal census); no
consolidation proposed, so principle 8 has no equivalence to prove and no
`proof:` entry is owed; no `gate:` witness is owed at this item (the final
gate runs the full suite per DRY.md). Negative controls live where they
belong: F-A records the owed hand-copy control at its family item, and all
13 families stand open — nothing deferred is dropped. Re-hashed at
reconciliation time: target `a48f6172`…`f846` worktree == HEAD (empty
item-scoped diff confirmed via `git diff HEAD --stat`); `extension.py`
`49667a93`, `walker.py` `9b111ed9`, `test_selections.py` `04bbb23d` clean;
`nested_planner.py` HEAD `0ad8ff5d`/worktree `e69dbf5f`,
`connection.py` HEAD `93e998f2`/worktree `3c4d5dcb` (re relied-on lines
still outside dirty hunks); graphql-core 3.2.8, artifact's strawberry
0.324.0 pin uncontested. AGENTS.md prose: empty diff (no `.py` touched —
no ruff run owed); citations `path::Symbol` throughout; no process
provenance in my sections; Worker 1's probe path
(`docs/dry/temp-tests/dry-file-optimizer__selections/`, read-only) is
pre-existing scratch — Worker 0 removes it by explicit path after `verified`
per DRY.md; concurrent dirt preserved; no commit. Plan rows for Worker 0:
tick file item plan-line 192 `verified` (no pending execution); index
corrections: none; scratch: `docs/dry/temp-tests/dry-file-optimizer__selections`.
