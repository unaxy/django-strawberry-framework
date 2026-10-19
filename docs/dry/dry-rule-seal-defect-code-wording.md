# DRY review: `seal-defect-code-wording`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Rule: the wording of seal defect codes. Every violation code the sealed-execution
queryset emits renders a stable actionable message through one central dispatch rule.
Provisional owner [querysets.py][querysets] `::_defect_message`, confirmed below.

What the mechanism is:

- [querysets.py][querysets] `::_seal_or_defect` emits one of nine canonically ordered
  codes (`type` -> `table` -> `untrusted` -> `routing` -> `evaluated` -> `sliced` ->
  `combined` -> `projection` -> `alias`). The codes are the sealed family's rule;
  their WORDING is this family's.
- [querysets.py][querysets] `::_defect_message` is the single dispatch: look the code
  up in the site's arm map, else render the loud fallback naming the code, carrying
  the detail, and declaring the site words it not (`framework defect: a seal defect
  code was added without an arm at this site`). Six call sites compose it by name;
  no site restates the dispatch.
- Each site owns its own prose arms for exactly the subset its call shape can reach.
  The per-site prose question is the sealed family's R-wording rejection
  (`dry-rule-sealed-execution-queryset.md` R-wording: per-site prose differs by
  subject/contract; home at the `::_defect_message` docstring) — used here as a
  trigger to check, never a verdict; re-derived below.

D5 question first (freshness queue Q1): routed defect D5 (seal wording no policy can
reach — `combined` arm at `_raw_list_source_message`, `evaluated`/`routing` arms at
`_visibility_result_error`/`_prepared_visibility_source`, plus the false docstring
reason) may have landed via `5741eaa6`. Verdict: LANDED, subject GONE —

- `git show 5741eaa6` removes exactly those four arms and corrects the raw-list
  docstring to name `evaluated`, `sliced`, `combined`, `projection` as switched off.
- Exact-key grep over `django_strawberry_framework` at HEAD `bfaee91d`:
  `_UNRECOMPOSED_CHILD_POLICY` 0 hits; `combining queries` 0 hits;
  `requires an unevaluated` 0 hits; `get_queryset changed database routing intent`
  0 hits. The one surviving `changed database routing intent` hit is the orderset
  site's live `routing` arm (`{method_name} changed database routing intent`),
  a different subject, reachable by construction (see Enumeration).
- The defect-message test now pins the vacated cells instead of exercising dead
  wording (`tests/utils/test_querysets.py::test_visibility_defect_messages`:
  `evaluated`/`routing` render the fallback at both visibility sites; `combined`
  renders its arm under `_LIST_ARGUMENT_VISIBILITY_POLICY`).

New-D5 sweep (is any REMAINING arm unreachable): none — every arm is reachable
under at least one policy/call shape reaching its site, and every absence is
pinned to the policy flag or call shape that switches it off (matrix in
Enumeration; WS probe proves the absent cells fall back loud rather than
mislabel). One observed edge (child-propagated `alias` at the raw-list site)
falls back by design; recorded in the finding, not a defect.

Prior records only as triggers: the querysets file item's F3 (gate-only, refined
by I-R4 to gate-plus-declaration with the four-term gate population) and D5, plus
the sealed family's R-wording/R-guard and its parked gate note ("gate design
belongs with the `seal-defect-code-wording` family"). F3's `SITES` table is
updated here for HEAD (`_PREFETCH_CHILD_POLICY` replaces the retired
`_UNRECOMPOSED_CHILD_POLICY` on the visibility runners). R-guard (connection
pre-slice triage vs seal proof) is observed, not re-litigated: that guard renders
no seal code and calls no `_defect_message` site.

Fence honored: [querysets.py][querysets] read freely, fingerprinted, never edited
(another item disputes its file artifact). `permissions.py` read freely, never
edited (no consolidation needs it). Dirty paths elsewhere read-only for trace.

## Verification

### Matrix

1. Cross-flavor mirroring: sync/async `apply_type_visibility_*` thread the same
   `policy` to BOTH seals, so source and result sites see identical policy sets
   on both colors; sync/async `_apply_orderset_*` share
   `_validate_post_orderset_result` + `_snapshot_routing_intent`; cascade async
   wraps the sync walk, sharing both renderers. No color-specific wording.
2. Sync/async twins: compared by behavior (same maps, same fallback); the only
   color split in wording is the `SyncMisuseError` recourse family, already
   rejected elsewhere (`sync-boundary-recourse-wording`), out of this population.
3. Derived knowledge: subjects are formatted at the call from names the caller
   already holds (`type_cls`/`model`/`method_name`/edge path); no site re-derives
   another site's subject. A reachability matrix test would re-derive policy
   knowledge — noted in the gate design as cost, not built here.
4. Round-trip pairs: seal codes (producer, `_seal_or_defect`) ↔ arm maps
   (consumers); `_defect_message` fallback closes the loop so an unmapped code
   fails loud instead of mislabeling. No second codec.
5. Other media: oracles (`tests/utils/test_querysets.py` wording + orderset
   rejection rows, `tests/test_permissions.py` cascade prose rows) and
   projections (site docstrings, [spec-045][spec-045]) listed, not counted.
6. Enforcement by omission: each site's missing arms checked against the policy
   flags and call shapes that switch them off (Enumeration table). Every absence
   is justified by a contract source; the fallback covers the theoretical cells
   (notably prefetch-child `alias` at the source site). No member lacks a guard
   the contract requires.

### Enumeration

Instruments: exact-key grep populations (counts printed, zero `truncated` lines),
full read of both member files, policy-to-site threading trace
(`apply_type_visibility_*`, `_apply_orderset_*`, cascade root/edge, walker
child, raw-list), and a WS execution probe classifying all 36 pure-renderer
cells (4 sites × 9 codes).

- Codes: 9 canonical (`type`, `table`, `untrusted`, `routing`, `evaluated`,
  `sliced`, `combined`, `projection`, `alias`).
- `_defect_message` call sites: 6 (one body). Four in [querysets.py][querysets]
  (`_validate_post_orderset_result`, `_raw_list_source_message`,
  `_visibility_result_error`, `_prepared_visibility_source`), two in
  [permissions.py][permissions] (`_root_error_renderer`, `_edge_error_renderer`).
  No other module imports `_defect_message` (grep: 2 files).
- Look-alike prose swept and excluded with reason: `connection.py`
  `totalCount`-guard `GraphQLError`, `list_field.py` `ListArgumentError`
  wording, optimizer degrade/classify prose (`nested_fetch.py`,
  `predicates.py`, `walker.py` comments), `resource_policy.py` row-bound prose
  — none renders a seal `(code, detail)` pair, none calls the dispatch.

Per-site arms (all execution-proved by the WS probe except the two
seal-driven sites, proved by existing oracles + the same dispatch body):

| Site | Arms | Each absence switched off by |
|---|---|---|
| `_raw_list_source_message` (`_RAW_LIST_SOURCE_POLICY`, no alias expectation, no `expected_routing`) | `type`, `table`, `untrusted` | `evaluated` (`require_unevaluated` off), `sliced` (`reject_sliced` off), `combined` (`reject_combined` off — the landed D5 arm), `projection` (`require_model_rows` off), `routing` (no `expected_routing`), `alias` (no required alias) |
| `_visibility_result_error` (policies: default, cascade, prefetch-child, list-argument; no `expected_routing`) | `type`, `table`, `untrusted`, `sliced`, `combined`, `projection`, `alias` | `evaluated` (no result policy sets `require_unevaluated`; only `_ORDERSET_RESULT_POLICY` does and it never reaches this site), `routing` (no `expected_routing` at any result seal — the single passer is the orderset validator) |
| `_prepared_visibility_source` (same four policies; required alias always `None`) | `type`, `table`, `untrusted`, `sliced`, `combined`, `projection` | `evaluated`, `routing` (same two reasons as the result site — the landed D5 arms), `alias` (required alias `None`; prefetch-child shared-alias could theoretically emit it for a routed source, unreachable in practice, fallback covers) |
| `_validate_post_orderset_result` (`_ORDERSET_RESULT_POLICY` + `expected_routing`) | shape sentence for `type`, `table`, `untrusted`, `evaluated`, `sliced`, `combined`, `projection`; own arm for `routing` | `alias` ABSENT BY SUBSUMPTION (site comment, verified against `_snapshot_routing_intent`: required alias IS `effective_alias`, always a string; the seal checks `routing` first and `effective_alias == intent.db` whenever routed, so an `alias` defect cannot arrive) |
| `_root_error_renderer` (`_CASCADE_SEAL_POLICY`, no alias expectation) | `type`, `table`, `untrusted`, `sliced`, `combined` | `projection` (`require_model_rows=False` — `.values()` root is supported input), `evaluated`/`routing`/`alias` (policy off / no expectation) |
| `_edge_error_renderer` (`_CASCADE_SEAL_POLICY`, required alias always the root `str`) | `type`, `table`, `untrusted`, `sliced`, `combined`, `alias` | `projection` (same cascade reason), `evaluated`/`routing` (same as result site) |

Shared-policy arms are one site's subset under several policies, never one
policy's wording in two places: `combined` at the visibility sites is reachable
via cascade + list-argument (not default, not prefetch-child) yet rendered once
per site; `sliced` likewise. Reachable-under-SOME-policy is the correct
criterion — a per-(site, policy) split would be seven wordings for one subject.

### Challenges

- W1 — new defect code (e.g. a tenth shape): `_defect_message` dispatch is the
  1 definition (fallback renders it legibly everywhere on day one); one arm is
  owed at each site that can reach it (consumers, listed not counted).
  Count: 1.
- W2 — reword one message (e.g. the cascade edge `sliced` prose): exactly that
  arm moves; the other five sites and the dispatch do not. Count: 1.
  (WS probe `per-site-prose-differs` cell: same code, different subjects, byte-
  different strings — execution-verified.)
- W3 — new (seventh) message site: composes `_defect_message` by name (1 call
  site, arms for its reachable subset). A site rendering seal codes WITHOUT the
  dispatch is the bypass the parked gate population names. Count: 1 call site.
- D5-landed (Q1): exact deleted keys 0 hits each (see System trace); the four
  arms are gone from the tree, the two D5 docstring defects corrected, the
  vacated cells pinned by `test_visibility_defect_messages`. Not re-filed.
- Reachability re-derivation for HEAD (I-R4's table, updated):
  `expected_routing` passed at exactly one `_seal_or_defect` call site
  (orderset validator); policies reaching the visibility runners are default,
  cascade, prefetch-child (walker, replacing retired unrecomposed), list-argument
  — none sets `require_unevaluated`. So `evaluated`/`routing` stay absent-correct
  at both visibility sites, and prefetch-child adds no new arm obligation
  (`sliced` off but present via other policies; `alias` at the result site
  present and exercised by the walker's own fail-closed contract).

## Findings

### F-wording — REJECTED consolidation; per-site prose stands, dispatch stays single

Contract + variation: each seal violation code renders a stable actionable
message. Varies on subject and contract per site (read surface vs hook result
vs orderset method vs raw-list ceiling vs cascade root vs cascade edge);
invariant across sites is dispatch + exhaustiveness, never the sentences.

Sites + roles: definition `::_defect_message` (dispatch + fallback);
consumers the six arm maps above (each renders only its reachable subset);
oracles the wording/rejection rows in `tests/utils/test_querysets.py`
(`test_visibility_defect_messages`, `test_defect_message_*`,
`test_validate_post_orderset_result_rejects_*`) and `tests/test_permissions.py`
(`test_hook_return_rejections_fail_closed`,
`test_root_queryset_shape_rejections`, cascade-prose rows);
projections the per-site "which codes can reach me" docstrings and
[spec-045][spec-045].

Challenges: W1=1, W2=1, W3=1 call site. New-code and reword changes each move
exactly one definition or one arm.

Owner + lifetime (principle 7): owner stays
`utils/querysets.py::_defect_message` — the narrowest cohesive owner every
legitimate consumer already imports without reversing a dependency
(`permissions.py` imports from `utils/querysets.py`; `utils` never imports
back into `permissions`). Pure derivation, nothing stored: no lifetime fields
are owed ("pure derivation says 'not cached'"). Enforcement authority is the
fallback itself — it fails loud at runtime for every code at every site with no
population to enumerate.

Migration: none — already single; the sealed family's R-wording is confirmed,
not moved.

Distinct behavior kept: six subjects, six contracts — source wording names
`apply_type_visibility` + model rows; result wording names `get_queryset` + the
type; orderset wording is one shape sentence + a routing arm keyed to the
method; raw-list wording names the slice-ownership ceiling; cascade root names
`apply_cascade_permissions`; cascade edge names the `Model.field` path + target
column (the path is the only thing locating a hook defect on a deep walk).
Merging any two would attribute a rejection to the wrong call. The
child-propagated `alias` edge at the raw-list site (prefetch child sealed under
`_PREFETCH_CHILD_POLICY` inside a raw-list parent seal) renders the fallback —
legible (names code + detail), fails closed, by design: the site's docstring
defines its arms as the `_RAW_LIST_SOURCE_POLICY` subset, and the fallback
contract explicitly owns every unrendered code.

Behavioral proof: execution-verified — WS probe
(`PYTHONPATH=<WS>/examples/fakeshop uv run --directory <WS> python
probe_wording.py`; copy `__file__`
`<WS>/django_strawberry_framework/__init__.py`, DB `NAME`
`<WS>/examples/fakeshop/db.sqlite3`; 0 SQL, no rows touched): all 36
pure-renderer cells classify as expected; every absent cell's fallback names
the code and carries the detail; direct-dispatch unit (arm verbatim, unknown
code falls back without borrowing prose) passes; per-site-prose-differs passes.
Rejects: a site mislabeling an unrendered code; two sites sharing a subject's
sentence. Plus execution-verified shared-tree oracle
(`tests/utils/test_querysets.py::test_visibility_defect_messages --no-cov -n0`,
1 passed) pinning the D5-vacated cells at both visibility sites. The
seal-driven sites (source, orderset) are proved through their existing oracles
(cited above) running the same dispatch body — no new oracle added, none owed.

Structural gate: EVALUATED, landing DEFERRED with reason (parked design
discharged as design, not as code). Owed design, recorded for the item that
can land it: for each `_defect_message` call site, the code set reachable at
that site computed from (i) the policies reaching it, (ii) `expected_routing`
presence, (iii) required-alias non-`None` possibility, and (iv) the ONE
documented subsumption (`routing` subsumes `alias` at the orderset validator) —
with (iv) declared at the site in a form the gate reads (I-R4's
gate-plus-declaration: a small production change, hence not gate-only). Known
instrument hazard (I-R4's qualification): a hand-written reachability table
reports the subsumption as a missing arm unless it encodes (iv); the gate must
read the declaration, not hardcode the table. Negative control: drop any
reachable arm (or add an unreachable one) → gate red; the WS probe above is
the prototype of that check (24 armed cells + 12 fallback cells + direct unit).
NOT landed here because (a) the (iv) declaration is a production edit in fenced
[querysets.py][querysets]; (b) the gate test belongs in `tests/utils/
test_querysets.py`, which carries unattributed concurrent staged dirt (+31) —
editing it trips the attribution stop; (c) nothing is unprotected meanwhile:
the runtime fallback enforces exhaustiveness mechanically at every site today,
and the existing oracles pin the exact cells D5 vacated. No `proof:`/`gate:`
command owed.

Coupling: none. No consolidation, no dependent defect.

Freshness: HEAD `bfaee91d`; [querysets.py][querysets] `96618fba`
(== HEAD, clean); [permissions.py][permissions] `757dce34` (== HEAD, clean);
walker `9b111ed9` (== HEAD, clean; prefetch-policy threading verified);
`list_field.py` worktree `d6af6164` (HEAD `ce682d5f`; +8 ledgered
relay-guard docstring dirt only — cited `policy=` lines verified untouched by
diff grep, 0 hits); `tests/utils/test_querysets.py` `8b39c9f8` (worktree, staged
concurrent dirt, read-only for oracles); `tests/test_permissions.py`
`4a1d7775`; [spec-045][spec-045] per sealed artifact. ITEM_BASELINE
`43f06d13bc62d6947cd8bddffbdb7a557cbc3767`. Searched population: all `.py`
under `django_strawberry_framework` for wording keys; excluded from the family
with reason: optimizer degrade/classify prose, connection/list-field client
errors, resource row-bound prose (no seal code rendered — verified by content).
Any fingerprint change reopens.

## Defects

None new. Tracing found no non-duplication bug: every absent arm is justified
by its policy/call-shape contract, every present arm reachable, the fallback
names code + detail on all 12 absent cells (execution-proved), and the
orderset `alias` omission carries its subsumption proof at the site. The
`## Owned changes` ledger carries nothing on this family's paths (confirmed by
content grep) — no attribution stop tripped because no tracked path was edited.

## Judgment

D5 landed (`5741eaa6`); no new D5 — six sites render exactly their reachable
subsets through the single `_defect_message` dispatch, per-site prose differs
by subject/contract (R-wording confirmed with trigger + home, zero edits), and
the parked code-without-arm gate is designed but deliberately unlanded (fenced
owner + dirty gate file + runtime fallback already enforcing). Owner stays
`utils/querysets.py::_defect_message`.

Item-scoped diff state: zero tracked edits (`git diff 43f06d13 --
django_strawberry_framework/utils/querysets.py
django_strawberry_framework/permissions.py` empty; both files clean vs HEAD).
One new untracked artifact (this file). No test file touched
(`grep -c truncated` over the evidence sweeps == 0; no truncated output relied
on). Scratch: WS copy
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/seal-defect-code-wording`
(WS-only `probe_wording.py` + generated `.venv`; never in the shared tree;
remove by explicit path after verification). Shared-tree spend: the one
authorized focused test (`test_visibility_defect_messages`, passed); no other
run converted into evidence.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-045]: ../SPECS/spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[permissions]: ../../django_strawberry_framework/permissions.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
## Independent verification (Worker 2)

Worker 2 phase-1 trace, recorded WITHOUT reading any other section of this
artifact. Sources read at HEAD bytes (fingerprints below); `django_strawberry_framework/utils/querysets.py` read-only, never edited; `tests/utils/test_querysets.py` read freely, never edited.

### (1) Message-rendering sites found, with roles

- S0 `django_strawberry_framework/utils/querysets.py::_defect_message` — DEFINITION. Owns the dispatch and the exhaustiveness contract: exact-map lookup plus a loud fallback naming an unrendered code as a framework defect. Owns no wording itself.
- S1 `django_strawberry_framework/utils/querysets.py::_raw_list_source_message` — renderer (consumer of S0). Fixed policy `django_strawberry_framework/utils/querysets.py::_RAW_LIST_SOURCE_POLICY`, called only from `django_strawberry_framework/utils/querysets.py::normalized_row_source`.
- S2 `django_strawberry_framework/utils/querysets.py::_visibility_result_error` defaults (`render_error=None` branch) — renderer. Reached via `django_strawberry_framework/utils/querysets.py::_normalized_visibility_result` from both colored runners with whatever policy the caller passed.
- S3 `django_strawberry_framework/utils/querysets.py::_prepared_visibility_source` defaults (`render_error=None` branch) — renderer. Reached from both colored runners with whatever policy the caller passed, always with `required_alias=None` and no routing expectation.
- S4 `django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result` map — renderer. Fixed policy `django_strawberry_framework/utils/querysets.py::_ORDERSET_RESULT_POLICY`, fixed routing expectation present. Explicit per-code map (not S0 defaults) so a new seal code self-names.
- S5 `django_strawberry_framework/permissions.py::_root_error_renderer` — renderer. Cascade root end, via `django_strawberry_framework/utils/querysets.py::_prepared_visibility_source` under `django_strawberry_framework/permissions.py::_CASCADE_SEAL_POLICY` (imported from `django_strawberry_framework/utils/querysets.py::_CASCADE_SEAL_POLICY`).
- S6 `django_strawberry_framework/permissions.py::_edge_error_renderer` — renderer. Cascade per-edge end, via `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` under `_CASCADE_SEAL_POLICY` with `required_alias` pinned to the walk alias.
- Non-rendering consumers (checked, correctly carry no arms): `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`, `django_strawberry_framework/utils/querysets.py::apply_type_visibility_async`, `django_strawberry_framework/utils/querysets.py::_normalized_visibility_result`, `django_strawberry_framework/list_field.py` pipelines (pass `_LIST_ARGUMENT_VISIBILITY_POLICY`, render through S2/S3), `django_strawberry_framework/optimizer/walker.py` prefetch-child path (passes `_PREFETCH_CHILD_POLICY`, renders through S2/S3), `django_strawberry_framework/list_field.py` orderset callers of S4.
- Oracles (independent expectations, spell wording literally, never read the owner maps): `tests/utils/test_querysets.py` (`test_unrendered_defect_code_says_so_instead_of_mislabelling`, `test_visibility_defect_messages`, `test_apply_type_visibility_sync_combined_result_error`, `test_validate_post_orderset_result_*` battery, seal-policy unit tests), `tests/test_permissions.py` (`test_root_queryset_shape_rejections`, unsealable-root cascade-prose test), `tests/test_resource_policy.py` (raw-list bound `cannot be sealed` / `_result_cache is a ...` asserts).
- Excluded on body strength (not seal-code renderers): `django_strawberry_framework/utils/errors.py::_validation_messages` etc. (input-validation wording), `django_strawberry_framework/utils/input_values.py::_walk_error` (input walk), `django_strawberry_framework/utils/querysets.py::_coerced_manager_queryset` / `::_row_source_model` (own non-code-specific ConfigurationError prose).

### (2) Per-site arms vs codes their policies can reach (own analysis)

Canonical seal order per `django_strawberry_framework/utils/querysets.py::_seal_or_defect`: type, table, untrusted, routing, evaluated, sliced, combined, projection, alias. Reachability is a function of the policy tuple plus the call shape (`required_alias`, `expected_routing`).

- S1 arms: type, table, untrusted. Policy `_RAW_LIST_SOURCE_POLICY` sets `require_model_rows=False, reject_sliced=False, carry_result_cache=True` with `reject_combined`/`require_unevaluated`/`require_shared_alias` off and no routing expectation, sealed with alias `None`. Reachable set is exactly type/table/untrusted: evaluated/sliced/combined/projection switched off, routing/alias need an expectation never stated. Arms match exactly; no dead arm, no gap.
- S2 arms: type, table, untrusted, sliced, combined, projection, alias. No evaluated/routing arms. This site serves the UNION of policies callers pass: `_DEFAULT_SEAL_POLICY` (combined off), `_CASCADE_SEAL_POLICY` (combined on, projection off), `_LIST_ARGUMENT_VISIBILITY_POLICY` (combined on), `_PREFETCH_CHILD_POLICY` (sliced off, shared-alias on). Union over the four: sliced reachable (three of four), combined reachable (cascade/list-arg; proven live by `test_apply_type_visibility_sync_combined_result_error`), projection reachable (default/list-arg/prefetch), alias reachable (pinned resolutions and prefetch-child explicit routing). Evaluated unreachable (no reaching policy sets `require_unevaluated`); routing unreachable (no reaching caller states `expected_routing`). Absences correct; every present arm reachable by at least one policy/input pair.
- S3 arms: type, table, untrusted, sliced, combined, projection. No evaluated/routing/alias arms. Same four-policy union as S2, except this seal always runs with `required_alias=None` and `require_shared_alias` never satisfied by a feasible input (default/cascade/list-arg never set it; the prefetch path seeds from an unrouted framework-built base). So alias is unreachable HERE while reachable at S2 — the asymmetry is correct, not a gap. Evaluated/routing absences correct for the same reason as S2. Combined arm reachable via cascade/list-arg source seals (proven live by the `union` source test through `_LIST_ARGUMENT_VISIBILITY_POLICY`); sliced/projection reachable via default-family source seals.
- S4 arms: type, table, untrusted, evaluated, sliced, combined, projection, routing. No alias arm. Policy `_ORDERSET_RESULT_POLICY` sets `reject_combined=True, require_unevaluated=True` with model-rows on and slice rejection on; `expected_routing` always present. Reachable set is exactly the eight armed codes; alias is subsumed by the routing check (routed intent pins the candidate to the required alias; unrouted intent plus a `None` candidate never trips the alias branch), as the site comment derives. Arms match exactly.
- S5 arms: type, table, untrusted, sliced, combined. Fixed `_CASCADE_SEAL_POLICY` (`require_model_rows=False, reject_combined=True`), source seal with alias `None`, no routing expectation. Projection/evaluated/routing/alias unreachable. Arms match exactly.
- S6 arms: type, table, untrusted, sliced, combined, alias. Same fixed policy as S5 but result seal with `required_alias` pinned to the walk alias, so alias is reachable (divergent hook routing). Projection off (values returns are supported cascade input), evaluated/routing off. Arms match exactly.
- Net: no dead arm remains at any of the six renderers; no reachable code lacks an arm. The three dead arms removed by the recent fast-forward (combined at S1; evaluated/routing at S2/S3) are gone and their docstrings/tests now state the switched-off codes explicitly.

### (3) Definition counts per posited change

- New seal code (e.g. a new `_seal_or_defect` code for a shape only the cascade edge can produce): shared dispatch count 1 — S0 already handles the unrendered code loudly with no existing site forced to move for correctness. Wording count equals the number of REACHABLE sites that choose to word it; each site's sentence is its own definition (different subject: edge path vs `get_queryset` vs source vs method name), not one rule restated.
- Reword (e.g. change S6's sliced sentence, or S2's combined recourse): count 1 — the one site moves, the other five do not.
- New site (e.g. a new surface with its own renderer calling S0 with its reachable subset): count 1 — one new declaration, zero existing definitions move.
- All three challenges return count 1 for the shared machinery and per-site independence for the prose: the signature of intentional separation, not duplication.

### (4) Owner I would choose (principle-7 reasoning)

- Dispatch + exhaustiveness: S0 in `django_strawberry_framework/utils/querysets.py`. Responsibility: the seal lives there (`_seal_or_defect`, `_SealPolicy`, all six policy constants); every legitimate consumer (read surfaces, list/connection pipelines, cascade both ends, raw-list bound, orderset validator, optimizer prefetch child) already depends on that module, and `permissions.py` already imports `_defect_message`/`_CASCADE_SEAL_POLICY` from it.
- Reachable-set definition: `_SealPolicy` in the same module — one record declares which codes a surface can emit; renderers follow it.
- Per-site prose: stays at each renderer (S1–S6). Reasons to change differ per subject (cascade edge attribution and recourse vs generic `get_queryset` wording vs source attribution vs method-name contract); fusing them into one wording table would couple independent diagnostics.
- Dependency direction decides against any cascade-side or test-side owner: `utils/querysets.py` must never import `permissions.py` (cycle; stated in its module docstring), while the reverse import already exists. Narrowest cohesive owner every consumer can depend on without reversing a dependency is therefore `utils/querysets.py`. No new owner, no moved table.

### (5) Consolidation, rejection, or defect

- Wording consolidation: REJECTION. The six renderers encode distinct responsibilities and distinct reasons to change (principle 2 target is ONE translation — the code-to-message dispatch in S0, already single — not zero prose variation; principle 7 keeps distinct decisions at the adapters). Positing a shared wording table fails the change challenge: one site's recourse edit must not move the other five.
- Defect: NONE FOUND in this phase. Against GOAL.md trust boundary (messages are author-facing diagnostics — a wrong message misleads, a missing arm fails loud via S0 or degrades): every rendered arm is reachable by a feasible project shape (queryset/hook-return subclasses, sliced/combined/projection shapes, explicit `.using()` routing, evaluated orderset results, routing-intent drift), and every reachable code has an arm except alias-at-S4, which is proven subsumed rather than missing. No contract row + reaching input pair names a live mislabel or silent pass. No AGENTS.md defect-bar case is made.
- Sibling note (context only, verified independently): the seal core reads as single-owned (one `_seal_or_defect`, one `_SealPolicy` record, one S0 dispatch); this trace found no second definition of the code-rendering rule.

### (6) Structural gate owed?

- YES — gate-only (no consolidation attached). Justification: the exact failure mode already shipped once — three dead arms (combined at S1; evaluated/routing at S2/S3) survived until human review removed them, proving no existing oracle fails on a PRESENT-but-unreachable arm. The existing oracles pin reachable wording plus the S0 fallback, but nothing asserts absence of dead arms.
- Owed population: the six renderer maps (S1–S6) crossed with the nine canonical codes, with reachability derived from the `_SealPolicy` fields plus the call shape (`required_alias` presence, `expected_routing` presence, `require_shared_alias`) — not a hand list. Per-region identity plus cardinality: each renderer must arm exactly its reachable subset.
- Negative controls: (a) delete one reachable arm → renderer falls back to `declares no wording for` and the gate fails; (b) add one unreachable arm (e.g. restore `combined` at S1) → the reachability assertion fails; (c) rename/truncate a code → both the cardinality check and the fallback oracle fail. Each control must be shown failing before the gate is accepted.
- Form: a permanent test (strongest tier that can import the renderers without a live query — `tests/` package level, beside the existing defect-message tests) that enumerates the six maps against policy-derived reachable sets. Bespoke per-helper existence asserts are explicitly NOT owed.

### (7) Freshness fingerprints (HEAD bytes, `git hash-object`)

- HEAD: bfaee91d
- `django_strawberry_framework/utils/querysets.py`: 96618fba4eafb6a87e73414770014e3aee5b41ef (clean at task start; READ-ONLY this cycle, never edited)
- `django_strawberry_framework/permissions.py`: 757dce34cecd7a249b2634947a771d4608808bfe
- `tests/utils/test_querysets.py`: 8b39c9f8caeafd5bb9991177f8dcb8069b86e314 (staged work of another cycle present at task start; read freely, edited never — no hunks by this worker)
- `tests/test_permissions.py`: 4a1d7775b32a38c06a15745d1c581daea917c71e
- `tests/test_resource_policy.py`: eaaa1fa16d64118abda847f688a2b347401a1dd1
- `django_strawberry_framework/list_field.py`: d6af61646784deac2f3053bb4096b8599deae2f5
- `django_strawberry_framework/optimizer/walker.py`: 9b111ed938951a073a9226ccbcfacabc3af981e8
- Searched populations: all `def _.*(message|error|renderer)` under `django_strawberry_framework/utils/`; all `_defect_message|_raw_list_source_message|_visibility_result_error|_root_error|_edge_error|_validate_post_orderset_result` and all six policy constants under `django_strawberry_framework/`; defect-wording assertions across `tests/` (`declares no wording`, `cannot be sealed`, cascade shape matches, orderset rejection battery).
- Contract sources: GOAL.md trust boundary; AGENTS.md defect bar; DRY.md principles 2/7/9/11.
- History inspected (no bytes relied on): 5741eaa6 (dead-arm removal), 4d9f1c3d (retired seal-policy symbol).
- Status set: NONE. No verdict on Worker 1 proposed (findings not read).

## Reconciliation (Worker 2)

Phase-2 record. HEAD `bfaee91d`, fingerprints re-hashed below. Nothing in
`## Independent verification (Worker 2)` was modified in this phase; nothing
outside this artifact was edited.

### Phase-1 integrity

The phase-1 section is intact on disk and was recorded before exposure: the
phase-1 message ended with `PHASE-1-TRACE-RECORDED` plus the artifact path,
and Worker 1's claims arrived only in the phase-2 tasking. All six arm lists,
both fingerprints sets, and the gate-only position above predate that
exposure. No phase-1 sentence is retracted except the landing form in
`(6)` (refined, not reversed — see gate judgment).

### D5 re-verification (own greps at HEAD)

- `_UNRECOMPOSED_CHILD_POLICY`: 0 hits. `combining queries`: 0 hits.
  `requires an unevaluated`: 0 hits.
  `get_queryset changed database routing intent`: 0 hits.
- `changed database routing intent`: exactly 1 hit, and it is the live
  orderset arm (`django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result`
  `messages["routing"]`, `f"{method_name} changed database routing intent; …"`),
  reachable by construction (`_ORDERSET_RESULT_POLICY` + `expected_routing`
  always present). AGREE: D5 landed via `5741eaa6`, subject GONE, no new D5.

### Per-claim reconciliation

- Sites + roles: AGREE. My S0–S6 equal Worker 1's six call sites plus the
  single dispatch; my consumer/oracle/exclusion lists match (same
  look-alikes excluded for the same reason: no seal `(code, detail)` pair,
  no dispatch call).
- Arm counts, re-derived by me from map keys: S1 3 (`type`, `table`,
  `untrusted`); S2 7 (+`sliced`, `combined`, `projection`, `alias`); S3 6
  (no `alias`); S4 8 (seven shape codes + `routing`); S5 5; S6 6 (+`alias`).
  Exact match with Worker 1's table, including the two asymmetries that
  matter (S3 without `alias`: source seal always alias-`None`; S4 without
  `alias`: subsumed by `routing`, site comment verified against
  `django_strawberry_framework/utils/querysets.py::_snapshot_routing_intent`).
- Definition counts: AGREE (new code 1, reword 1, new site 1 call site).
  Same challenges, same evidence.
- Owner: AGREE with an emphasis note. Worker 1 names
  `utils/querysets.py::_defect_message`; my phase-1 additionally records
  `utils/querysets.py::_SealPolicy` as the reachable-set co-record. Same
  tree, same module, no action: policies declare reachability, S0 enforces
  dispatch, prose stays per site. Dependency direction (permissions already
  imports from utils; never the reverse) rules out any other home.
- REJECT vs consolidate: AGREE. R-wording stands with trigger (same
  `(code, subject)` pair twice) and home (the S0 exhaustiveness docstring
  clause, present at HEAD, zero edits owed). A shared wording table would
  couple six independent subjects/contracts.

### Gate-deferral judgment: DEFERRAL STANDS (verified, not revision-needed)

- Reason (a), fenced `querysets.py`: LEGITIMATE and tasking-level. The
  parked design is gate-plus-declaration: the `(iv)` subsumption must be
  declared at the site in a form the gate reads. That declaration is a
  production edit in a file this cycle holds read-only. This alone blocks
  the strong gate.
- Reason (b), dirty `tests/utils/test_querysets.py`: REAL (+31 staged,
  confirmed). Landing in a NEW clean file instead was considered and
  rejected: it would fragment the defect-message oracles AND force the
  subsumption knowledge into the test, duplicating call-shape facts the
  owner should declare (deriving a duplicated fact still duplicates it)
  and misplacing the grammar (grammar belongs at the owner, not in the
  test). A gate without `(iv)` is born red on the correct tree (it would
  demand an `alias` arm at S4) — landing it weakened is explicitly
  forbidden. So no landable gate shape exists inside this item's fence.
- Fallback check with one qualification: S0's loud fallback
  (`django_strawberry_framework/utils/querysets.py::_defect_message`,
  unrendered-code arm) fires on ANY missing arm at ANY site by
  construction — single dispatch, all six sites compose it by name (grep:
  2 files, 6 sites, no bypass) — execution-proved over all 12 absent
  cells by the WS probe and pinned by oracles
  (`tests/utils/test_querysets.py::test_unrendered_defect_code_says_so_instead_of_mislabelling`,
  `::test_visibility_defect_messages`, the orderset battery, the cascade
  shape rows). Qualification recorded: the fallback enforces the
  missing-arm direction (the dangerous one — mislabeling is impossible),
  not the dead-arm direction. Dead arms are behaviorally harmless (never
  quoted; D5 itself proved it), and their catcher is exactly the parked
  design. Worker 1's "enforces exhaustiveness" is accepted as the
  dangerous half.
- Unblock conditions for the landing item: fence on `querysets.py` lifts
  (disputing item closes) → land the machine-readable `(iv)` declaration
  at `_validate_post_orderset_result`; `tests/utils/test_querysets.py`
  dirt settles → land the four-term gate test there; both negative
  controls shown red-then-green (drop a reachable arm; add an unreachable
  arm) before acceptance. Worker 0 homes this to the item that can
  legitimately edit those paths.

### Freshness re-hash + scope + proofs

- HEAD `bfaee91d` (unchanged). `querysets.py` `96618fba` (clean, read-only
  honored — no hunks by either worker). `permissions.py` `757dce34`
  (clean). `tests/utils/test_querysets.py` `8b39c9f8` (other cycle's
  staged work intact, never edited here). Item-scoped diff vs W1 baseline
  `43f06d13` on all family paths: EMPTY. Remaining tree drift is
  concurrent work outside this item's scope (a fresh stash hash differs
  from the tasking-quoted one; no family-path content moves with it).
- `## Pending execution`: NONE owed. The WS probe executed (copy
  `__file__` + DB `NAME` recorded in Findings); the one focused
  shared-tree test passed and is recorded. No `proof:`/`gate:` entries
  remain; I add no runs (re-verification is grep+read; AGENTS.md default
  is no pytest without explicit ask, and no behavior changed).
- AGENTS.md prose on the empty diff: artifact-only change; citations use
  `path::Symbol` form; no process provenance in the finding substance;
  ruff N/A (no `.py` touched). Matrix judged discharged on reasons;
  enumeration confirmed member-by-member (9 codes, 6 sites); no oracle
  reads from the owner it checks (wording spelled literally).

### Defects

None. No `(Worker 2)` entries: every absent arm is justified by its
policy/call-shape contract, every present arm reachable, the dangerous
half enforced by construction + execution.

### Verdict: verified — exact plan rows for Worker 0

- Tick `docs/dry/dry-0_0_15.md` Family `seal-defect-code-wording` row:
  `[ ]` → `[x]`, verdict substance `verified (Run 0.0.15 2026-09-19-1;
  D5 landed via 5741eaa6 confirmed GONE by W2 re-grep; no new D5;
  F-wording REJECTED with trigger + home, zero edits; gate-plus-
  declaration DESIGNED, landing deferred on fenced querysets.py +
  staged test_querysets.py dirt, dangerous half enforced by fallback)`.
- Index row `seal-defect-code-wording`: `open (carries F3 as
  gate-plus-declaration, and D5)` → `rejected` (zero-change
  confirmation per the plan's convention; substance on the tick).
- D5-closeout note for `## Outcomes`: old routed D5 (unreachable seal
  wording) landed via `5741eaa6` — W2 re-verified GONE at HEAD
  (four dead keys zero source hits; sole surviving routing hit is the
  S4 live arm); no new D5 (six sites arm exactly reachable subsets
  3/7/6/8/5/6).
- Scratch: `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/seal-defect-code-wording`
  (WS-only probe + generated venv; remove by explicit path after
  `## Outcomes` is bound).

## Run-8 scoped re-trace (Worker 1, REOPENED item s18)

Run: 0.0.15 2026-09-30-8. Every section above is prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh: it scopes the
drift delta across the three member files, CONFIRMs or REVISEs every prior
family finding, re-derives the wording rule with the member census at HEAD,
writes the R-wording home clause s17 handed off (endorsed — this item owns
it), adjudicates O1 with fresh evidence, and attributes the worktree dirt by
content. Zero production edits; zero tracked files changed except this
artifact.

Method: probes `/tmp/s18/*.py` (`wording_extract.py` AST wording-artifact
extractor run at base / `5c5e32c5` / HEAD / worktree, `oracles.py` pin
attribution, `dirt.py` hunk classifier), cited by content. All execution via
`workspace.py run dry/sealword-retrace-s18/consolidate` (copy slot-2, synced
2026-09-30T21:03:01Z; the copy carries no `.git`, so all git reads are
`git -C <shared>` through the same runner). The target is never imported:
pure `git show` bytes plus `git grep` with a directory pathspec. No pytest;
read-only probes only.

### Scope and fingerprints

Drift base `0c0537e2`, HEAD `83998e08` (unmoved at close).
`ITEM_BASELINE=28c61cdb997f59b9d28178746f22ac8462d4e88c` (resolves; before
copy pinned slot-1). Copy bytes == shared bytes (sha1 identical on all three
members at close).

| File | Base | HEAD | Worktree |
|---|---|---|---|
| `utils/querysets.py` | `3616927d` | `392e50d0` | `cfc773ba` |
| `permissions.py` | `72102cc0` | `d77c5050` | `42c3c19c` |
| `optimizer/walker.py` | `75f9c6b6` | `bdd9c2f1` | `9130aceb` |
| `tests/utils/test_querysets.py` | `73e7a6c2` | `3ff4094a` | `b1fc954b` |
| `tests/test_permissions.py` | `384f451b` | `14961acd` | `7cf7b3af` |

(`git rev-parse <rev>:<path>` / `git hash-object`; member blobs match the
s3/s12/s16/s17 pins digit-for-digit.)

### Drift delta (base `0c0537e2` .. HEAD `83998e08` on members)

Exactly 6 commits touch the three member files (843+/441-): `5c5e32c5`
(301+/106- on members, +376 on the two oracle files), `10d2b9cd`,
`999a1aab` (121+/56-), `b20277fe` (420+/301-), `dfbea72b` (3+/2-),
`fef11e64` (7+/10-).

- `5c5e32c5` (behavior, the wording drift): adds [querysets][querysets]
  `::_COMBINED_WHAT` and recomposes all five dispatch `combined` arms onto
  it (subject prefix + shared text); adds [walker][walker]
  `::_hint_prefetch_over_pk_set` composing the same text outside the
  dispatch; deletes `_LIST_ARGUMENT_VISIBILITY_POLICY` (7 -> 6
  constructions) and the `reject_combined` axis (0 hits package-wide at
  HEAD), replacing it with `rewrite_combined` (default `True`, `False`
  solely at raw-list); moves the canon order (`combined` after
  `projection`); rewords the seal/runner/renderer docstrings to the
  serve-or-refuse vocabulary. Base list-argument policy differed from
  default on `reject_combined` alone, so its deletion merges list-field
  seals into default with no arm obligation lost.
- `10d2b9cd` (behavior, wording-neutral): 2 hunks on [querysets][querysets]
  (import + `base_queryset`-region owners), none in a wording function.
- Typing-only (`999a1aab`, `b20277fe`, `dfbea72b`, `fef11e64`):
  wording-neutral, proved three ways: (1) the wording-artifact extraction
  (arm keys + arm first-lines + sharing flags + dispatch source + constant
  texts + policy flags + seal emissions + call shapes) at `5c5e32c5` ==
  HEAD, normalized diff EMPTY; (2) every quote-bearing changed line on
  members is a `cast(...)` / `TypeVar` / annotation or an identical
  f-string re-wrapped around one; (3) the two suspect hunks read in full
  (the `getattr` cast-wrap, the `.filter(pk__in=...)` re-wrap) are
  behavior-identical.

### Re-derived rule and census at HEAD

Canon order (stated at [querysets][querysets] `::_seal_or_defect`): `type`
-> `table` -> `untrusted` -> `routing` -> `evaluated` -> `sliced` ->
`projection` -> `combined` -> `alias` (prior: `combined` before
`projection`).

Dispatch: 1 definition ([querysets][querysets] `::_defect_message`, source
byte-identical to base including the O1 sentence) + 6 call sites in 2
files (orderset `:3152`, raw-list `:3992`, result-error `:4119`,
prepared-source `:4242`, cascade root `permissions.py:362`, cascade edge
`permissions.py:423`) + 1 import + 1 prose cite. No bypass: the walker's
composer raises directly without rendering a seal `(code, detail)` pair.

Arm sets (re-derived from map keys): orderset 8 (6-code shape sentence
+ own `combined` + own `routing`; `alias` absent by the still-prose-only
subsumption comment), raw-list 3, result 7, source 6, cascade root 5,
cascade edge 6 — the prior 8/3/7/6/5/6 counts, every key identical.

Reachability re-derived (HEAD basis): runner policies are default,
cascade, prefetch-child, list-relation-child (4; list-argument deleted,
list-field now default; external `policy=` exactly permissions x2 +
walker x2, both runners thread one policy to both seals).
`expected_routing=` exactly 1 passer (orderset `:3109`), so `routing`
stays absent-correct at both visibility sites.
`require_unevaluated=True` solely at `_SIDECAR_RESULT_POLICY` (`:2915`),
which never reaches a visibility seal, so `evaluated` stays
absent-correct. Source seal always `required_alias=None`, so `alias`
stays absent-correct there while reachable at the result seal
(`:4340` threads it). `combined` now reachable under every policy except
raw-list (`rewrite_combined` default `True`) — the prior "via cascade +
list-argument, not default" clause is superseded; every `combined` arm
stays reachable-under-SOME-policy, now including default. `sliced` off
solely under prefetch-child; `projection` off solely under cascade. No
dead arm, no gap; the prefetch-child `alias`-at-source theoretical cell
still falls back loud by design.

Shared texts (third independent derivation, pin-for-pin with the s3 row
and the s16/s17 convergences): `_UNSEALABLE_STATE_CAUSES` 1 definition
(`:3961`, text byte-identical to base) + 5 code composers (`:4008`,
`:4136`, `:4257`, `permissions.py:378`, `permissions.py:443`) + 2 prose
cites (`:2482`, `permissions.py:411`) + 1 import; `_COMBINED_WHAT` 1
definition (`:3973`) + 6 code composers (`:3149`, `:4147`, `:4268`,
`permissions.py:387`, `permissions.py:455`, [walker][walker] `:1424`) + 2
prose cites (`:3117`, `permissions.py:409`) + 2 imports. All five old
inline combined wordings extinct (0 hits each for their distinctive
phrases across package + tests + examples); `reject_combined`,
`_LIST_ARGUMENT_VISIBILITY_POLICY`, `_UNRECOMPOSED_CHILD_POLICY`,
`connection.py::_sidecar_visibility_policy` all 0 hits package-wide.

Oracles at HEAD: 8 independent literal WHAT-head pins in 8 distinct tests
(2 package + 6 live, each spelling subject + WHAT head verbatim, none
importing the constant) + 3 owner-reading composers
(`test_visibility_defect_messages`, the orderset serves/refuses test,
the walker hint test) + lost-property detail rows (cascade x2,
seal/prefetch/live rows) + the fallback pins (`:5450` direct unit,
`:5473` evaluated-falls-back). Cause list: 6 fragment-pinning tests (head
+ advice substrings) with the run-7 origin-lead oracle carried. No
arm-set gate test exists (name sweep over `tests/` finds only unrelated
arms) — the parked gate-plus-declaration is still unlanded, and the
(iv) subsumption is still a prose comment (`subsume` exactly 1 hit at
`:3123`).

`_sentence_start`: 1 definition + 4 in-file readers, all refusal sites;
the adoption alternative is DECLINED (recorded below) — it stays
file-local.

### Dispositions

- F-wording — REVISE (rejection stands, rule text updated): per-site prose
  stands — all six ladders still name their own subject and contract, and
  merging any two would still misattribute. What changed is the sharing
  line: two clause texts are now constant-owned and composed by name
  (cause list + combined contract), each under the site's own subject.
  Owner stays [querysets][querysets] `::_defect_message` (dependency
  direction unchanged: `permissions.py` imports from `utils/querysets.py`,
  never the reverse; the walker likewise imports only). Challenges:
  new-code 1 (fallback covers day one), reword 1 (one arm, or the one
  constant for a shared clause), new-site 1 call site. The sealed
  family's R-wording rejection is confirmed with the home clause this
  item writes (below), zero edits.
- Structural gate — REVISE (design stands, population re-pinned, deferral
  persists): the four-term gate-plus-declaration design is unchanged and
  still owed; term (i) now reads default/cascade/prefetch-child/
  list-relation-child with default combined-capable, and the canon order
  carries the swap. Landing still blocked: (a) the (iv) declaration is a
  production edit and this is a zero-edit item; (b) the gate file is still
  dirty (`tests/utils/test_querysets.py` worktree `b1fc954b` vs HEAD).
  The dangerous half stays enforced by the fallback (execution shape
  unchanged, oracles pin the vacated cells); the dead-arm half stays
  parked. No `proof:`/`gate:` command owed.
- D5 — CONFIRM gone: the four dead keys 0 hits each (re-grep at HEAD);
  the sole `changed database routing intent` package hit is the live
  orderset arm (`:3151`, + 8 test pins); the drift's own removed wordings
  (all five inline combined bodies) extinct with 0 survivors. Not
  re-filed.
- W2 phase-1 (S0–S6, arm counts, definition counts, owner) — CONFIRM with
  refreshed pins: same six renderers, same 3/7/6/8/5/6 sets, same
  counts (1/1/1), same owner; the two asymmetries (source without
  `alias`, orderset subsumption) re-verified against current bytes.
- Reconciliation deferral judgment — CONFIRM: reasons (a)+(b) re-verified
  above; the fallback qualification (dangerous half only) stands; the
  unblock conditions are unchanged.
- Carried run-8 evidence — CONFIRM from the family side: s3/s16
  `_COMBINED_WHAT` 1+6+2 (third derivation, pin-for-pin), s16 O1
  strengthened (below), s17 R-wording REVISE (home-clause handoff
  discharged here), s16 I-R4 runner set of 4.
- `_sentence_start` adoption — DECLINED, stays file-local: a generic
  capitalize-first-letter helper, not seal-code wording; two of its four
  readers raise outside the dispatch, and no second capitalization site
  exists package-wide. The index row stands as written.

### R-wording home clause (owned by this item)

Exact replacement text for the [querysets][querysets] `::_defect_message`
docstring's final sentence (`:4082`-`:4084`), to be landed by the closeout
defect-homing pass together with O1 (this zero-edit item lands no
production prose):

> Each site owns its own prose (a cascade edge names the edge, a read
> surface names ``get_queryset``); what is shared is the dispatch and the
> exhaustiveness, plus the two clause texts no surface respells -- the
> untrusted cause list (``_UNSEALABLE_STATE_CAUSES``) and the
> combined-queryset contract (``_COMBINED_WHAT``) -- each composed under the
> site's own subject.

("No surface respells" is chosen over "renders verbatim" because raw-list
capitalizes the cause list's first letter via `_sentence_start` — a
mechanical transform, not a respelling.) Trigger (carried, extended): a
site respelling either shared clause, or two sites rendering the same
(code, subject) pair. No other copy of the stale sentence exists
package-wide (exactly 1 hit), so the repair is single-site.

### O1 adjudication (persists strengthened, fresh evidence)

`_defect_message` `:4084` still reads "exhaustiveness, never the wording"
— verbatim at HEAD, and now doubly false: the cause list (1+5+2,
re-derived above) AND the combined text (1+6+2, re-derived above) are
both shared. Same D4 class (a next author honoring "never the wording"
would un-share either constant), same owner
([querysets][querysets] `::_defect_message` docstring), same one-clause
repair — now with the exact clause text owned above. Routes to the
closeout defect-homing pass (pending there since run 7; s16's routing
stands). No behavior is affected; no consolidation depends on it.

### Worktree dirt attribution (by content; all concurrent, zero owned)

The `## Owned changes` ledger names one member hunk (the committed walker
D1 fix, already in HEAD); the current dirt matches no ledger row on any
member. `-U0` classification by my instrument: querysets 137 hunks (116
truth + 21 other), permissions 38 (25 truth + 13 other), walker 9 (9
truth + 0 other); numstat +222/-283, +42/-36, +9/-10. Content: hunt
truth-migration (`_safe_*`/`__name__`/`isinstance`/`object.__getattribute__`
-> `truth.*`, incl. the `_safe_class_name` deletion and the
`_readable_queryset_state` collapse), hunt except-narrowing and casts,
the hunt router-behavior rework, spec-034 prose cites, the `_walk`
filter batching. Every wording-region hunk read in full: arm bodies
differ solely in subject/detail-render calls, while arm keys, sharing
flags, the dispatch, both constants, and the O1 sentence are
byte-identical worktree-vs-HEAD (extraction diff: exactly the 4
mechanical deltas — one seal `untrusted` emission collapsed into
`truth.instance_state`, one `_sentence_start` reader collapsed with its
function, one `cast` at the prefetch-child seal call, the truth-migrated
subject renders). The seal's code SET is unchanged in the worktree. No
family verdict moves with the dirt either way.

### Defects (run-8)

O1 persists strengthened (above; closeout homing still owed). No new
defect: every absent arm is justified by its policy/call-shape contract,
every present arm reachable, the fallback names code + detail, and the
orderset `alias` omission still carries its subsumption proof at the
site. No `(Worker 1)` entries beyond O1's carry.

### Judgment

F-wording REVISE (rejection stands, sharing line redrawn around the two
constant-owned clauses), gate REVISE (design stands, re-pinned, deferral
persists), D5 CONFIRM gone, W2 phase-1 + reconciliation CONFIRM, carried
s3/s16/s17 evidence CONFIRM, home clause WRITTEN and owned, O1 persists
strengthened to closeout, `_sentence_start` adoption DECLINED. Owner
stays `utils/querysets.py::_defect_message`. Zero-edit item: this
artifact is the whole delta.

Worker-0 instructions (exact texts; Worker-0 alone edits the plan):

- Tick Family `seal-defect-code-wording`: `[ ]` -> `[x]`, verdict
  substance `REOPENED run 8, re-trace verified s18 (2 REVISE + CONFIRM
  set + GONE, zero-edit, home clause written, O1 persists to closeout)`.
- Member row `Unsealable-state cause-list wording single-source`:
  `open` -> `consolidated` (1 definition + 5 composers + 2 prose cites
  re-derived at HEAD, cause text byte-identical, 6 fragment oracles +
  origin lead pin it; s17 precedent: already-single + verified).
- Member row `Combined-refusal shared text (_COMBINED_WHAT)`: `open` ->
  `consolidated` (1 definition + 6 composers + 2 prose cites
  third-derived pin-for-pin, old inline bodies extinct, 8 independent
  literal oracles + 3 owner-reading composers pin it).
- O1 (`:4084` "never the wording", doubly false) with the owned home
  clause above -> the closeout defect-homing pass (single-site docstring
  repair; no other copy package-wide).
- No new rows (`_sentence_start` stays file-local, adoption declined).

### Item-scoped diff state

Own run: this artifact only (header flip + this section + one link
definition; every prior section untouched). HEAD `83998e08` unmoved at
close. Item diff on package + tests is 0 bytes. Shared-tree spend: none
(no focused test authorized or owed for zero edits). Probes `/tmp/s18/`
read-only, cited by content; no scratch in the tree.

## Run-8 verification (Worker 2)

Every row below is re-derived expectation-first with W2's own
instruments at HEAD bytes; W1's section is the claim under test, never
evidence. All execution via `workspace.py run
dry/sealword-retrace-s18/verify` (slot-3, synced 2026-09-30T21:37:11Z;
all git reads `git -C <shared>` through the runner). Own probes
`/tmp/s18v/` (`extract.py` AST wording-artifact extractor,
`sealorder.py`, `jdiff.py`, `ascii.py`, `basecombined.py`,
`oracles2.py`, `strand2.py`, `dirt.py`), cited by content. No pytest;
read-only probes only. Nothing tracked edited except this artifact
(which is untracked, `??`).

### Scope and fingerprints

Drift base `0c0537e2` and HEAD `83998e08d48c911199527ed0411ab8041805c8b5`
resolve; HEAD unmoved at close (re-checked after every probe batch).
`ITEM_BASELINE=28c61cdb997f59b9d28178746f22ac8462d4e88c` resolves to a
stash commit `WIP on (no branch): 83998e08 ...` (not an ancestor by
construction). Copy bytes == shared bytes on all three members at
close (`cfc773ba` / `42c3c19c` / `9130aceb`; `shared unmoved since
sync` on every run).

| File | Base | HEAD | Worktree |
|---|---|---|---|
| `utils/querysets.py` | `3616927d` | `392e50d0` | `cfc773ba` |
| `permissions.py` | `72102cc0` | `d77c5050` | `42c3c19c` |
| `optimizer/walker.py` | `75f9c6b6` | `bdd9c2f1` | `9130aceb` |
| `tests/utils/test_querysets.py` | `73e7a6c2` | `3ff4094a` | `b1fc954b` |
| `tests/test_permissions.py` | `384f451b` | `14961acd` | `7cf7b3af` |

All fifteen blobs match W1's pins digit-for-digit (independent
`rev-parse` / `hash-object`).

### Drift delta (own re-scope)

Exactly 6 commits touch the three member files on
`0c0537e2..83998e08` (`rev-list --count` = 6, same SHAs):
range diff 843+/441- (`213/115` walker, `77/64` permissions,
`553/262` querysets). Per-commit member stats re-derived:
`5c5e32c5` 301+/106-, `999a1aab` 121+/56-, `b20277fe` 420+/301-,
`10d2b9cd` 26+/1-, `dfbea72b` 3+/2-, `fef11e64` 7+/10-; oracle files
on `5c5e32c5` 302+/74- (= 376 changed lines). `5c5e32c5` is the
wording drift; the other five are wording-neutral, proved three ways
with W2's own instruments:

1. Own AST extraction (`extract.py`: dispatch source, both constant
   values, all arm keys + first lines, seal literal set, all
   `_SealPolicy` constructions, all `_seal_or_defect` call shapes,
   composers, imports) at `5c5e32c5` vs HEAD: normalized diff EMPTY
   (`jdiff.py` prints only `done`).
2. Own quote-bearing-line census per commit on members: 43 / 35 / 0 /
   6 / 9 (`999a1aab` / `b20277fe` / `dfbea72b` / `fef11e64` /
   `10d2b9cd`). Every line classified: `cast(...)` targets, `TypeVar`
   / `ParamSpec`, annotations, `type: ignore`, typing comments,
   identical f-string re-wraps around a cast, one `TYPE_CHECKING`-only
   `Protocol` docstring (walker `_CustomGetQuerysetReporter`), and the
   two new order-helper docstrings of `10d2b9cd` (whose 2 hunks,
   import + `base_queryset`-region functions, were read in full --
   none in a wording function). No arm body, constant, dispatch, or
   seal-emission line touched.
3. Both suspect hunks read in full: the walker `getattr` wrap
   (`999a1aab`) adds `cast("str", ...)` around the identical
   `or`-expression (typing-only); the `pk__in` hunk (`fef11e64`)
   adds an annotation and re-wraps one call. Behavior-identical.

Base-vs-HEAD extraction diff shows exactly the drift and nothing
else: dispatch source and cause-list text byte-identical (no diff
lines), `_COMBINED_WHAT` `MISSING` -> present, four combined-arm
first lines changed (the fifth, orderset, is a `dict.fromkeys` my
Dict-walk does not parse -- closed by direct read below),
constructions 7 -> 6 with `reject_combined` gone and
`rewrite_combined` in, `combined` literal gone from the seal body
(emission moved to `_pk_membership_query_or_defect`, reached after
the projection check per its docstring and the seal comment).

### Census at HEAD (own counts)

- Canon order from the `_seal_or_defect` check sequence plus its
  docstring enumeration: `type` -> `table` -> `untrusted` ->
  `routing` -> `evaluated` -> `sliced` -> `projection` -> `combined`
  -> `alias`. `combined` moved after `projection` (base had the
  literal between `sliced` and `projection`; HEAD emits it from the
  pk-rewrite helper after the projection check).
- Dispatch: 1 definition ([querysets][querysets] `::_defect_message`
  `:4070`, 1372 chars, byte-identical to base) + 6 call sites in 2
  files (`:3152`, `:3992`, `:4119`, `:4242`, [permissions][permissions]
  `:362`, `:423`) + 1 import (`permissions.py:123`) + 1 prose cite
  (`:3119`). Package-wide `_defect_message` hits: exactly those 9.
  The walker composer (`:1424`) raises directly, consumes only
  `defect[1]`, never calls the dispatch: no seventh site, no bypass.
- Arm sets re-derived (map keys by read; orderset via `dict.fromkeys`
  + 2 own arms): orderset 8, raw-list 3, result 7, source 6, cascade
  root 5, cascade edge 6 -- the prior 8/3/7/6/5/6 with every key
  identical. Every arm body read; each site's subject verified
  distinct (`method_name`, `The {name} {origin}`,
  `{name}.get_queryset`, `The apply_type_visibility source for
  {name}`, `The apply_cascade_permissions root for {name}`, `The
  {name}.get_queryset return for the cascade subquery on {edge}`,
  `OptimizerHint.prefetch(obj) on {type}.{name}`).
- Runner policies reaching the visibility seals: default, cascade,
  prefetch-child, list-relation-child (4). External seal-policy
  passers package-wide: exactly permissions x2 (`:635`, `:717`
  cascade) + walker x2 (`:635` passthrough of its
  `_LIST_RELATION_CHILD_POLICY` default, `:663` prefetch-child);
  both runners thread one `policy` to both seals (sync `:4426` /
  `:4447`, async `:4704` / `:4725`); list-field passes none (default).
  `expected_routing=` exactly 1 passer (`:3109`, orderset);
  `require_unevaluated=True` solely at `_SIDECAR_RESULT_POLICY`
  (`:2915`), which reaches only the orderset seal (`:3108`) --
  `_ORDERSET_RESULT_POLICY` is gone (0 hits). Source seal always
  `required_alias=None` (`:4232`); result seal threads it (`:4340`).
  `rewrite_combined` default `True` (`:2871`), `False` solely at
  raw-list (`:2929`); `sliced` off solely under prefetch-child and
  `projection` off solely under cascade among runner policies
  (raw-list's own policy separately switches off `sliced` /
  `projection` / `combined`, per its site docstring). `combined`
  reachable under every policy except raw-list, now including
  default: every `combined` arm is reachable-under-SOME-policy; no
  dead arm, no gap. (Sole scope note: the "solely" clauses above are
  runner-policy-scoped; the seal docstring states the raw-list
  exclusions alongside.)
- `_UNSEALABLE_STATE_CAUSES`: 1 definition (`:3961`, text
  byte-identical to base) + 5 code composers (`:4008`, `:4136`,
  `:4257`, `permissions.py:378`, `:443`) + 2 prose cites (`:2482`,
  `permissions.py:411`) + 1 import (`permissions.py:122`).
  Package-wide hits: exactly those 9, pin-for-pin.
- `_COMBINED_WHAT`: 1 definition (`:3973`) + 6 code composers
  (`:3149`, `:4147`, `:4268`, `permissions.py:387`, `:455`,
  [walker][walker] `:1424`) + 2 prose cites (`:3117`,
  `permissions.py:409`) + 2 imports (`permissions.py:121`,
  `walker.py:18`). Package-wide hits: exactly those 11,
  pin-for-pin.
- No-respell triple lock: the 5 base combined bodies (4 inline Dict
  bodies + the orderset `unsliced, uncombined` shape sentence, all
  extracted from base bytes) have 0 hits each for W2's own
  distinctive phrases across package + tests + examples;
  `reject_combined`, `_LIST_ARGUMENT_VISIBILITY_POLICY`,
  `_UNRECOMPOSED_CHILD_POLICY`, `_sidecar_visibility_policy` all 0
  hits package-wide; distinctive mid-constant substrings
  (`Prefetch it cannot rebuild`, `without changing its rows`) 1 hit
  each (the constant). No surface respells either clause.
- Oracles re-derived with W2's own attribution (`oracles2.py`,
  grouped by enclosing test): 8 literal WHAT pins
  (`combined queryset as the set of ... primary keys it selects`)
  in 8 distinct tests -- 2 package (`tests/test_connection.py` x2)
  + 6 live (pagination x3, library, list-field, list-field-async),
  none importing the constant; 2 spot-read, both spell subject +
  head verbatim across adjacent literals. 3 owner-reading composers
  in 2 files: `test_visibility_defect_messages` (`:5462`, `:5483`),
  `test_validate_post_orderset_result_serves_a_combined_result_and_refuses_a_lost_property`
  (`:5672`), walker
  `test_plan_refuses_a_combined_prefetch_obj_hint_the_primary_key_set_cannot_carry`
  (`:1703`). Lost-property detail rows: cascade params x2 (`:1074`,
  `:1077`) + cascade row (`:1403`), seal rows, walker row, live
  rows. Fallback pins at `:5450` (`declares no wording for`) and
  `:5473` (`with the 'evaluated' defect ... declares no wording
  for`). Cause list: 6 fragment tests (content + advice; 1 live + 2
  permissions + 1 resource-policy + 2 querysets) + the origin-lead
  oracle (`test_resource_policy.py:2152`,
  `message.startswith("A collection resolver returned ...")`).
  No arm-set gate test (name sweep finds only unrelated arms;
  `_defect_message` in tests is the direct fallback unit only).
  `(iv)` still a prose comment (`subsume` 1 hit in querysets.py at
  `:3123`; 3 package-wide with 2 unrelated -- see precision notes).
- `_sentence_start`: 1 definition (`:3952`, first letter up, rest
  untouched) + 4 in-file readers (`:3840`, `:3946` raising outside
  the dispatch, `:3991`, `:4008`); package-wide hits exactly 5.
  Raw-list composes the cause list solely through it (mechanical
  capitalization, not a respelling: the constant starts lowercase).
  No second sentence-start site package-wide (`utils/strings.py`
  `capitalize` is identifier-case conversion, a different
  transform -- see precision notes).

### Row verdicts

- F-wording REVISE: SURVIVES. Per-site prose stands (six ladders,
  six subjects, all read); the sharing line is redrawn exactly as
  claimed (2 constant-owned clause texts, 1+5+2 / 1+6+2
  re-derived pin-for-pin); owner stays [querysets][querysets]
  `::_defect_message` (dependency direction unchanged:
  permissions and walker import from utils, never the reverse);
  challenges 1/1/1 re-derived.
- Structural gate REVISE: SURVIVES. Four-term design unchanged,
  term (i) re-pinned to the 4 runner policies with default
  combined-capable (verified above); landing still blocked on (a)
  the production `(iv)` declaration in fenced querysets.py and (b)
  the dirty gate file (`tests/utils/test_querysets.py` worktree
  `b1fc954b` vs HEAD, re-fingerprinted); dangerous half enforced
  by the fallback (construction + oracles above), dead-arm half
  parked. No `proof:`/`gate:` owed.
- D5 gone: SURVIVES. Four dead keys 0 hits each at HEAD; sole
  package `changed database routing intent` hit is the live
  orderset arm (`:3151`); 8 pins in `tests/` (5 + 2 + 1,
  re-counted) plus 11 live pins in `examples/`; drift's five
  removed wordings extinct (above). Not re-filed.
- W2 phase-1 + reconciliation: SURVIVE with refreshed pins (same
  six renderers, same sets, same counts, same owner; deferral
  reasons re-verified).
- Carried s3/s16/s17 evidence: SURVIVES from the family side
  (`_COMBINED_WHAT` 1+6+2 third-derived pin-for-pin, O1 below,
  runner set of 4, R-wording handoff received -- but the handoff
  clause itself FAILS, next section).
- `_sentence_start` adoption DECLINED: SURVIVES (file-local 1+4,
  two readers outside the dispatch, generic helper, no second
  sentence-start site).

### R-wording home clause: FAILS (one precise defect)

Judged word by word against HEAD bytes. Every content word
survives: the kept first clause matches `:4082`-`:4083` verbatim;
the two constant names are exact; "no surface respells" is the
right verb (raw-list's `_sentence_start` is a mechanical transform,
proved above); "each composed under the site's own subject" holds
at all 11 composer sites (subjects listed above). The defect is
punctuation, and it is gate-failing: the quoted exact replacement
text contains two U+2014 EM DASHes (artifact `:711`, `:713`).
[querysets][querysets] is ASCII-only at HEAD (0 non-ASCII lines in
all three members; 0 em dashes in any `.py` repo-wide), and
`scripts/check_trailing_commas.py` fails on non-ASCII in `.py` in
BOTH modes (exit 1 with `ascii_hits` under `--check` and `--fix`;
"fails in BOTH modes, so the pre-commit `--fix` run catches it
too"). Landing the clause verbatim fails the lint gate and
pre-commit. Fix: replace both U+2014 with `--` (the checker's own
prescribed ASCII replacement) and re-check ASCII. No other word
changes.

### O1 adjudication: SURVIVES (routing stands, blocked on the clause fix)

`:4084` reads `exhaustiveness, never the wording.` verbatim at
HEAD; `never the wording` / `exhaustiveness` each exactly 1 hit
package-wide (directory pathspec); doubly false (both constants
shared, re-derived above). Same D4 class, same owner, same
one-clause repair -- whose clause text is owned above but
unlandable until the em-dash fix. Closeout-homing routing stands.

### Dirt attribution (own instrument, by content)

Hunk totals and numstat match exactly: querysets 137 hunks
+222/-283, permissions 38 +42/-36, walker 9 +9/-10. (W2's keyword
split differs: 127/10, 26/12, 8/1 vs W1's 116/21, 25/13, 9/0 --
the boundary is heuristic; walker's 9th hunk is the `truth`
import, content-truth, so 9/9 by content. Substance agrees.)
Classes sighted by content: truth-migration dominant (164 changed
lines with `truth.`; `_safe_*`/`__name__`/`isinstance`/`__getattribute__`
-> `truth.*`, `_safe_class_name` deletion,
`_readable_queryset_state` collapse -- both hunks read in full),
except-narrowing, casts, `_snapshot_routing_intent` rework,
spec-034 prose cites, `_walk` batching. The `## Owned changes`
ledger names exactly one member path (the committed walker D1 fix:
`_PREFETCH_CHILD_POLICY` import + seal policy, present at HEAD at
`walker.py:18` / `:663`); no dirt hunk touches a ledger row.
Every wording-region hunk read in full: renderer dirt is solely
subject/detail-render migration (`__name__`/`_safe_class_name` ->
`truth.name`, incl. moving two assignments inside `_render`);
arm keys, sharing flags, dispatch source, both constant values,
and the O1 sentence are byte-identical worktree-vs-HEAD (own
extraction diff: exactly 1 first-line delta, the root `type`
subject render). Seal code set unchanged: all 9 codes still
emitted; the single-line-count delta (untrusted 6 -> 7) is two
multi-line emissions collapsing to one line plus the
`unreadable-state` emission moving into `truth.instance_state`
(all three hunks read). No verdict moves with the dirt either way.
Zero owned.

### Zero-edit and item-scoped diff

HEAD `83998e08` unmoved at close; no commits by this item. All
member dirt is concurrent hunt work (above); no hunk carries
family authorship. The artifact is untracked (`??`, not in HEAD
or `ITEM_BASELINE`, which is a tracked-only stash on HEAD), so
this verification touches no tracked file at all.

### Precision notes (non-verdict)

- `subsume`: 1 hit file-scoped (`:3123`), 3 package-wide (the
  other two name unrelated subsumptions). The row -- `(iv)` still
  prose-only, gate unlanded -- is unaffected.
- Capitalization: `utils/strings.py` holds identifier-case
  `str.capitalize` (lowercases the rest), a different transform
  from sentence-start. The row -- no second sentence-start site,
  stays file-local -- is unaffected.
- Routing pins: `+ 8` is the `tests/` scope; `examples/` carries
  11 further live pins (strengthening).
- W2 instrument qualifications: `extract.py` misses non-`Dict`
  arm maps (orderset `dict.fromkeys`) and uses BFS literal order;
  both gaps closed by direct HEAD reads recorded above.

### Verdict: changes-requested

One failure: the owned home clause's two U+2014 EM DASHes
(artifact `:711`, `:713`) make the "exact replacement text"
unlandable -- it fails `check_trailing_commas.py` (exit 1, both
modes) and pre-commit on landing. Every other row survives on
W2's independent evidence. W1: replace both dashes with `--`,
re-check ASCII-only, no other change; re-verification need only
re-check the clause bytes and the ASCII gate. Worker-0: hold the
s18 tick and the closeout routing until the clause is repaired;
no new rows (the `_sentence_start` decline stands).

## Run-8 verification (Worker 2, re-verify)

Fresh Worker-2. No prior section is evidence here: every row
below is re-derived expectation-first with my own instruments
(`/tmp/s18r/`: `rv.py`, `clause.py`, `census.py`, `p2.py`–`p10.py`,
all read-only, cited by content). All execution via
`workspace.py run dry/sealword-retrace-s18/verify` (slot-3; all
git reads `git -C <shared>` through the runner; package-wide
greps use a directory pathspec). The claim under test is the W1
re-trace plus the W1b resubmission fix (the clause at
`:709`–`:714`, now carrying `--`) plus the prior W2 section.
Nothing tracked edited except this artifact (which is
untracked, `??`). No pytest; read-only probes only.

### Scope and fingerprints

Drift base `0c0537e2`, HEAD `83998e08d48c911199527ed0411ab8041805c8b5`
(unmoved at close, re-checked after the last probe batch).
`ITEM_BASELINE=28c61cdb997f59b9d28178746f22ac8462d4e88c`
resolves to the stash commit `WIP on (no branch): 83998e08 ...`.
Copy bytes == shared bytes on all five files at close (raw
sha1); `git diff 28c61cdb -- <members>` is EMPTY, so the
worktree is unmoved since the baseline on every member path.

| File | Base | HEAD | Worktree |
|---|---|---|---|
| `utils/querysets.py` | `3616927d` | `392e50d0` | `cfc773ba` |
| `permissions.py` | `72102cc0` | `d77c5050` | `42c3c19c` |
| `optimizer/walker.py` | `75f9c6b6` | `bdd9c2f1` | `9130aceb` |
| `tests/utils/test_querysets.py` | `73e7a6c2` | `3ff4094a` | `b1fc954b` |
| `tests/test_permissions.py` | `384f451b` | `14961acd` | `7cf7b3af` |

All fifteen blobs match the claimed pins digit-for-digit
(independent `rev-parse` / `hash-object`; blob hashes, not raw
file hashes). Drift re-scope: exactly 6 commits on
`0c0537e2..83998e08` over the members (same SHAs), range
843+/441-, per-commit `5c5e32c5` 301+/106-, `999a1aab`
121+/56-, `b20277fe` 420+/301-, `10d2b9cd` 26+/1-,
`dfbea72b` 3+/2-, `fef11e64` 7+/10-.

### The resubmission fix: PASSES (heaviest row, fully re-derived)

Judged byte by byte against HEAD, not against any prior
description of the failure:

- The owned clause (artifact `:709`–`:714`, `> `-stripped)
  is pure ASCII: 0 non-ASCII chars, exactly 2 `--`, 0
  U+2014. The artifact-wide em-dash census lists 70+ prose
  lines but NOT `:709`–`:714`.
- The kept first clause matches HEAD `:4082`–`:4083`
  word-for-word (re-wrapped across the 6-line replacement,
  necessarily: the new sentence is longer). HEAD `:4084`
  is still `exhaustiveness, never the wording.`
- The only delta vs the failed text is exactly the 2
  substitutions U+2014 -> `--`: token streams are
  identical otherwise. No other word changes.
- The fix matches file convention: the same HEAD
  docstring already writes `MISLABELS -- the schema
  author`, and the checker's own docstrings prescribe
  `--`.
- Landing simulation: splicing the clause (4-space
  indent) over HEAD `:4082`–`:4084` yields 6 lines of
  max length 78 (limit 99), and the spliced file parses.
  `scripts/check_trailing_commas.py` on the spliced
  file: `--check` exit 0, `--fix` exit 0, `non-ASCII 0`
  both modes. Negative control (the em-dash text
  spliced identically): exit 1 with exactly the 2
  `non-ASCII U+2014` hits at the two dash sites — the
  gate is live and the old text fails it.
- The `_sentence_start` leg of the landing: the helper
  (`:3952`, `phrase[:1].upper() + phrase[1:]`, docstring
  "first letter capitalized, the rest untouched") is a
  mechanical transform, and raw-list composes the cause
  list solely through it (`:4008`), so "no surface
  respells" remains the right verb.

The prior `changes-requested` failure is repaired and
gated. The clause is landable verbatim.

### Row verdicts (re-derived unless marked spot-checked)

- F-wording REVISE: SURVIVES. Re-derived: canon order
  from the seal docstring (`combined` after `projection`;
  literal gone from the seal body); dispatch 1 def
  (`:4070`, 1372 chars, byte-identical to base) + 6 call
  sites (`:3152`, `:3992`, `:4119`, `:4242`,
  [permissions][permissions] `:362`, `:423`) + 1 import
  + 1 prose cite = exactly 9 package-wide hits; arm sets
  8/3/7/6/5/6 with every key (orderset by direct read:
  6-code `dict.fromkeys` shape sentence + own `combined`
  + own `routing`, subsumption comment `:3122`–`:3132`
  intact); runner policies default/cascade/
  prefetch-child/list-relation-child; external passers
  exactly permissions x2 (`:635`, `:717`) + walker x2
  (`:635` passthrough, `:663` prefetch-child); both
  runners thread one policy to both seals (sync `:4426` /
  `:4447`, async `:4704` / `:4725`); `expected_routing=`
  exactly 1 passer (`:3109`); `require_unevaluated=True`
  solely at `_SIDECAR_RESULT_POLICY` (`:2915`);
  `rewrite_combined` default `True`, `False` solely at
  raw-list; source seal alias-`None` (`:4234`), result
  seal threads it (`:4340`); `_UNSEALABLE_STATE_CAUSES`
  1+5+2+1 pin-for-pin (`:3961`, text byte-identical to
  base), `_COMBINED_WHAT` 1+6+2+2 pin-for-pin (`:3973`);
  all 11 composers compose by name (`.format(` /
  interpolation / `_sentence_start`, every line read).
  No dead arm, no gap; both asymmetries (source without
  `alias`, orderset subsumption) hold on current bytes.
  Owner stays [querysets][querysets] `::_defect_message`
  (permissions and walker import from utils, never the
  reverse); challenges 1/1/1. (Spot-checked: per-site
  subject distinctness at the composer lines captured
  in the census output; orderset read in full.)
- Structural gate REVISE: SURVIVES. Design unchanged,
  term (i) re-pinned to the 4 runner policies with
  default combined-capable (verified above); landing
  still blocked on (a) the production `(iv)` declaration
  (`subsume` 3 package-wide, 1 file-scoped at `:3123`,
  still prose-only) and (b) the dirty gate file
  (worktree `b1fc954b` vs HEAD, re-fingerprinted). No
  arm-set gate test exists (name sweep over
  `tests/utils/test_querysets.py` finds only unrelated
  arms plus the direct fallback unit). Dangerous half
  enforced by the fallback (construction + oracles
  below); dead-arm half parked. No `proof:`/`gate:`
  owed.
- D5 gone: SURVIVES. All four dead keys 0 hits each at
  HEAD; sole package `changed database routing intent`
  hit is the live orderset arm (`:3151`); all five
  drift-removed combined bodies extinct (extracted from
  base bytes, 0 hits each for my own distinctive
  phrases across package + tests + examples).
- W2 phase-1 + reconciliation: SURVIVE with refreshed
  pins (same six renderers, same sets, same counts,
  same owner; deferral reasons re-verified).
- Carried s3/s16/s17 evidence: SURVIVES (`_COMBINED_WHAT`
  1+6+2 fourth-derived pin-for-pin, O1 below, runner set
  of 4, R-wording handoff discharged by the now-passing
  clause above).
- `_sentence_start` adoption DECLINED: SURVIVES. 1 def
  + 4 in-file readers (`:3840`, `:3946`, `:3991`,
  `:4008`), exactly 5 hits package-wide; the two
  outside-dispatch readers raise `ConfigurationError`
  directly (both read in full); `utils/strings.py`
  `capitalize` lowercases the rest (identifier-case
  conversion, a different transform). Stays file-local.
- Typing neutrality of the five non-wording commits:
  SURVIVES. My own AST extraction (`5c5e32c5` vs HEAD:
  arm keys + first-line hashes, constant values,
  dispatch source, seal literal set) is EMPTY-diff; the
  only count deltas are the `Generic` class-def line and
  its one docstring line (both typing, read); all three
  suspect hunks read in full (`cast("str", ...)` /
  `cast("list[object] | None", ...)` around identical
  expressions, one annotation + re-wrap).
- WHAT oracles: SURVIVE. 8 literal pins in 8 distinct
  tests (attributed to enclosing defs: 2 package + 6
  live), none importing the constant; 2 spot-read spell
  subject + head verbatim across adjacent literals. 3
  owner-reading composers in 2 files
  (`test_visibility_defect_messages` x2, orderset
  serves/refuses, walker hint). Fallback pins at
  `:5450` / `:5473`. Cause advice fragment pinned by 6
  tests with the exact 1+2+1+2 distribution; origin
  lead at `tests/test_resource_policy.py:2152`. (Spot-checked:
  lost-property detail rows, one cascade window read.)
- O1 adjudication: SURVIVES, routing stands. `:4084`
  verbatim at HEAD, exactly 1 hit package-wide, doubly
  false (both constants shared, re-derived above). Same
  D4 class, same owner, same one-clause repair — whose
  clause text now passes the ASCII gate above.
  Closeout-homing routing stands, unblocked.

### Precision notes (non-verdict)

- The "mid-constant substring" parenthetical from the
  prior round is imprecise for one of its two phrases:
  `without changing its rows` line-hits once at the
  seal docstring (`:3573`), not at the constant — the
  constant holds the same words across a source-line
  wrap, which line grep cannot hit. The no-respell
  conclusion is unaffected (all 11 composer lines read;
  every one composes by name; the docstring occurrence
  renders no seal pair).
- Cause fragments: the head+advice basis reproduces
  exactly 6 pins with the claimed distribution; my
  wider six-fragment sweep finds 8 tests, a superset
  (strengthening, not a conflict).
- `_SealPolicy(` counts 7 hits including the class def
  (`:2800`); constructions are 6, matching the six
  policy constants.

### Dirt attribution (own instrument, by content; zero owned)

Hunks 137/38/9 and numstat +222/-283, +42/-36, +9/-10
match exactly. Classes by content: truth-migration
dominant (164 added `truth.` lines; `_safe_class_name`
deletion and `_readable_queryset_state` collapse both
present), except-narrowing, casts, the
`_snapshot_routing_intent` rework, spec-034 prose cites,
`_walk` batching — all concurrent hunt work. The `##
Owned changes` ledger names exactly one member path (the
committed walker D1 fix, present at HEAD); no dirt hunk
touches a ledger row. Wording-region check worktree vs
HEAD: dispatch source, both constant values, seal
literal set, all AST-visible arm keys, both composer
populations, the O1 sentence, the subsumption comment,
and the orderset routing arm all byte-identical (line
numbers shifted only); the full 9-code seal set still
emitted. Deltas are the known mechanical ones (subject
renders through `truth.*`, one `_sentence_start` reader
collapsed with its function — def + raw-list composer
survive). No verdict moves with the dirt either way.

### Zero-edit and item-scoped diff

HEAD unmoved at close; no commits by this item. Worktree
equals `ITEM_BASELINE` on all member paths (empty diff).
This verification touched no tracked file: probes live
in `/tmp/s18r/`, landing-check scratch lives only in the
disposable copy. The artifact is untracked (`??`).

### Verdict: verified — exact plan rows for Worker 0

- Tick Family `seal-defect-code-wording`: `[ ]` ->
  `[x]`, verdict substance `REOPENED run 8, re-trace
  re-verified s18 (2 REVISE + CONFIRM set + GONE,
  zero-edit, home clause written ASCII-clean and
  gate-proved both modes, O1 persists to closeout)`.
- Member row `Unsealable-state cause-list wording
  single-source`: `open` -> `consolidated` (1+5+2
  re-derived at HEAD, cause text byte-identical, 6
  fragment oracles + origin lead pin it).
- Member row `Combined-refusal shared text
  (_COMBINED_WHAT)`: `open` -> `consolidated` (1+6+2
  fourth-derived pin-for-pin, old inline bodies
  extinct, 8 independent literal oracles + 3
  owner-reading composers pin it).
- O1 (`:4084` "never the wording", doubly false) with
  the owned home clause above -> the closeout
  defect-homing pass (single-site docstring repair,
  ASCII-clean, lands verbatim).
- No new rows (`_sentence_start` stays file-local,
  adoption declined).
