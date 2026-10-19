# DRY review: `nested-connection-strategy-selection`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is nested-connection strategy SELECTION: how the fetch
strategy for a nested connection page is chosen from hints, configuration,
and capability. The plan's owner candidate,
`optimizer/nested_fetch.py::resolve_strategy`, is re-derived below, not
inherited. SELECTION stays in this item; the strategy seam (the
`NestedConnectionStrategy` protocol, the plan/False contract, the shared
windowed floor, the recognized-queryset skeleton) lives in the queued
sibling `nested-fetch-strategy-seam`, and the hint value contract plus
the skip read are the verified siblings `optimizer-hint-shape` (f15)
and `optimizer-hint-skip-predicate` (f16) -- hints enter here as INPUT.

Traced at working-tree bytes with a HEAD cross-check at `5c3496e0`.
Five of the six indexed files are dirty with concurrent work (the
bug-hunt truth migration, typing, and the maintainer `except
BaseException` deletions -- none of it in the plan's `## Owned
changes` ledger); `optimizer/lateral_fetch.py` is clean at `a48cb0a4`.
The both-states selection census is identical (site line-counts 12/12,
16/16, 4/4, 10/10, 4/4, 0/0 across the six indexed files in plan
order), and the selection-region bodies differ only by the migration
spellings (`isinstance` -> `truth.is_instance`, `_safe_*` renderers ->
`truth.render`/`truth.kind`, the dropped `except BaseException` arm
around the `plan` read). No hunk adds, removes, or re-homes a selection
site, so the verdict below holds at both states. Line numbers cited are
working-tree lines. Prior file/family records were read as orientation
and adjudicated fresh; nothing below is inherited.

Sites found, by role. One definition per selection sub-decision; every
other site composes by name.

- Definitions.
  - `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`
    (`:437`): the spelling-to-instance map. `None` reads the setting,
    `"auto"` answers the stable auto singleton, registered names scan
    the `_builtin_strategies` registry (`:430`, one two-entry literal)
    by base-`str` content equality, and a non-class value with a
    callable `plan` passes through as a consumer backend; anything else
    raises `ConfigurationError`.
  - `django_strawberry_framework/optimizer/nested_planner.py::_select_nested_strategy`
    (`:225`): the per-field precedence ladder. A hint's
    `nested_strategy` override re-resolves through `resolve_strategy`;
    otherwise the active instance default answers via
    `active_strategy`. Single call site (`:1436`), feeding the single
    `strategy.plan` call (`:1479`).
  - `django_strawberry_framework/conf.py::nested_connection_strategy_setting`
    (`:450`): the thin setting read with the `"windowed"` default.
    Single production caller (the `resolve_strategy` `None` arm);
    validation lives in `resolve_strategy`, never here.
  - `django_strawberry_framework/optimizer/nested_fetch.py::active_strategy`
    (`:489`): the frame read with the `WINDOWED_STRATEGY` default for
    unmanaged callers. Single production caller (the
    `_select_nested_strategy` fallback).
- Consumers (compose by name, restate nothing).
  - `optimizer/extension.py::DjangoOptimizerExtension.__init__` (`:1018`):
    settles `resolve_strategy(kwarg-or-None)` once per instance.
  - `optimizer/extension.py::_configuration` (`:1045`): the
    never-constructed-subclass fallback settles `resolve_strategy(None)`.
  - `optimizer/extension.py::on_execute` (`:1128`): the sole production
    frame publisher (`strategy=self.nested_connection_strategy`).
  - `optimizer/hints.py::_require_strategy` (`:86`): factory/construction
    validation that delegates acceptance to `resolve_strategy` and keeps
    only its own contract (explicit `None` rejects here instead of
    reading the setting).
  - `optimizer/_context.py::active_nested_strategy` (`:302`): the frame
    read mechanism `active_strategy` defaults over.
- Shared vocabulary (one definition, three annotation sites).
  `nested_fetch.py::StrategySelection` (`:313`) annotates the extension
  kwarg, the hint field, and the hint factory; the planner's local
  (`:237`) and `_require_strategy`'s return (`:86`) compose it.
- Excluded decisions (different contract, recorded under Findings,
  never absorbed). The lateral plan-time eligibility downgrade
  (`lateral_fetch.py::LateralPrefetchStrategy.plan` `:986` calling the
  windowed floor when `_build_lateral_spec` returns `None`); the
  fetch-time vendor dispatch (`lateral_fetch.py::_fetch_lateral_rows`
  `:533`, `connection.vendor != "postgresql"`); the single-parent
  runtime gate (`single_parent_fetch.py`, spec eligibility plus the
  `SINGLE_PARENT_FAST_PATH` fetch-time toggle and the len==1 check);
  the views int-ladder (`views.py::_resolved_max_request_body_bytes`
  `:179`); the deployment policy ladder
  (`utils/policies.py::resolve_policy`); the field-`auto` spelling
  (`types/base.py:653`); the GlobalID strategy setting
  (`conf.py::relay_globalid_strategy_setting` `:514`); the Strawberry
  `auto` re-export token (`__init__.py:166`); the mutation-auth
  read-only-barrier vendor branch
  (`utils/write_transaction.py:356`-`:366`); the debug telemetry
  vendor field (`extensions/debug.py:299`); the compiler-emitter
  vendor prose (`utils/querysets.py:749`).
- Oracles. `tests/optimizer/test_nested_fetch.py` (resolution truth
  table `:101`-`:205`: names/auto/instance/setting/`None`/unknown/hostile
  subclasses/raising `plan`/lateral backend; precedence `:225`-`:266`;
  active default + frame `:270`-`:313`);
  `tests/optimizer/test_hints.py` (factory/validation `:97`-`:271`,
  including the `get_type_hints` resolution row);
  `tests/optimizer/test_walker.py` (two frame-bound strategy consumers
  `:5712`, `:5773`, composing `resolve_strategy` by name);
  `tests/optimizer/test_extension.py` (the `_context` `__all__` pin
  `:3508` covering `active_nested_strategy`);
  `tests/base/test_conf.py` (thin-reader verbatim `:374`, defaults
  `:472`, delattr resync `:411`); the live
  `examples/fakeshop/test_query/test_optimizer_auto_api.py`
  (per-field override wins over either extension default, both
  directions, over `/graphql` `:384`-`:429`). Every oracle spells its
  own expectation; none reads the owner's internals.
- Projections. The `nested_fetch.py` module docstring (per-instance
  selection, the `None` rung, the auto design); the `StrategySelection`
  ownership comment (`:300`-`:312`); `resolve_strategy`,
  `_select_nested_strategy`, `_require_strategy`, and
  `nested_connection_strategy_setting` docstrings; the extension
  construction comment (`:1005`-`:1013`); `docs/README.md` (the
  consumer selection ladder) and `docs/GLOSSARY.md` (the
  `OptimizerHint.strategy` row).

Connected behavior examined: the strategy seam (protocol, floor,
skeleton -- queued sibling ground, excluded with a contract
difference); the hint value contract and skip predicate (verified f15 /
f16, taken as input, never re-litigated); the walker hint dispatch and
the prefetch-lookups read (queued siblings, excluded); the scalar-only
and keyset-cursor projections (queued siblings, request inputs, never
the strategy choice); every `strategy=` publisher, every
`"windowed"`/`"lateral"`/`"auto"` literal, and every `connection.vendor`
check package-wide.

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched. The only same-shape ladder
   is the views int-ladder (`views.py::_resolved_max_request_body_bytes`,
   constructor > setting > default) -- excluded: different value
   contract (positive-int-or-None-disable with an exact-type gate and
   per-rung sentinel readings) and different reasons to change; the
   standing rejection trigger-checks clean at HEAD. The deployment
   policy ladder (`resolve_policy`: sealed-vs-deployment precedence over
   mappings) and the GlobalID strategy setting (a type-slot vocabulary
   that never resolves to a `NestedConnectionStrategy`) differ likewise.
   No other flavor selects a fetch backend.
2. Sync/async twins: inapplicable with reason. Selection is pure
   decision code with no await point; the extension's sync/async
   resolver arms share `_optimize` and therefore the one selection
   path. No twin exists to drift.
3. Derived rather than repeated knowledge: searched. The unknown-name
   message derives its vocabulary from `sorted(registry)` (composes,
   never restated); the `_require_strategy` `None` message spells the
   three names as user-facing wording, which is oracle-class (spelled
   expectations are listed, not counted -- the acceptance behavior
   delegates). The `.name` class attributes have one telemetry read,
   no decision reader (the refusal-log line's defensive
   `getattr(strategy, 'name', ...)`); renaming one cannot move
   selection, so they are not a second definition of it -- identity
   agreement is seam-sibling ground. No site re-derives the decision.
4. Inverse / round-trip pairs: inapplicable with reason. Selection is a
   one-way spelling-to-instance map; one telemetry read maps an
   instance back to a name for logging, no decision reader, so there
   is no inverse half to drift.
5. Contracts restated in another medium: counted. Production (four
   definitions above), oracles (six test files: resolution truth
   table, precedence rows, active-default rows, factory/validation
   rows, frame-consumer rows, thin-reader rows, plus the live
   both-directions override rows), projections (module + function
   docstrings, the README ladder, the GLOSSARY row). A selection change
   legitimately moves all three media together -- a contract change,
   not duplication.
6. Enforcement by omission: enumerated, no gap. Every nested-connection
   plan flows through the single `_select_nested_strategy` call
   (`nested_planner.py:1436`) feeding the single `strategy.plan` call
   (`:1479`); both extension construction paths settle through
   `resolve_strategy`; the execution frame is published by the single
   `on_execute` site; unmanaged callers get the `active_strategy`
   floor. No planning member lacks the selection.

### Enumeration

Family item: the population is the rule's mechanism, swept
package-wide by spelling (`resolve_strategy`, `_select_nested_strategy`,
`active_strategy`, `nested_strategy`, `nested_connection_strategy`,
`StrategySelection`, `NESTED_CONNECTION_STRATEGY`, the
`"windowed"`/`"lateral"`/`"auto"` literals, `connection.vendor`, and
every `strategy=` publisher). 13 production files carry a hit: the 6
indexed files plus `optimizer/_context.py` (frame mechanism),
`views.py` (ladder-shape prose + the int-ladder, R4),
`types/base.py` (field-`auto` + hint admission, R6),
`optimizer/single_parent_fetch.py` (runtime gate, R3),
`__init__.py` (the Strawberry `auto` re-export token -- upstream
pass-through, disjoint vocabulary),
`utils/write_transaction.py` (the mutation-auth read-only-barrier
vendor branch -- transaction control, different subject),
`extensions/debug.py` (telemetry payload -- different subject), and
`utils/querysets.py` (one docstring line on compiler emitter
dispatch -- prose, different subject). Each was read and either
roled or excluded with a contract difference under Findings.
Nothing reachable was left unassigned: 4 definitions, 5
consumer/mechanism sites, 1 shared vocabulary, 13 exclusions, 6
oracle files, projections.

### Challenges

Each variation axis of the selection rule, posited change plus the
authoritative definitions forced to move (consumers, oracles,
projections listed, never counted):

- C1, new built-in strategy name (e.g. `"correlated"`): the
  `_builtin_strategies` registry literal only. The unknown-name
  message re-derives from `sorted(registry)`; every caller, the hint
  validation, and the precedence ladder inherit by name. Count 1.
  (The `_require_strategy` `None` wording and the docstrings spell the
  old vocabulary -- oracle-class moves, listed: `hints.py:105` plus
  prose.)
- C2, new configured default (e.g. setting default `"auto"`): the
  `nested_connection_strategy_setting` default only. Count 1.
- C3, new precedence (e.g. the instance default wins over the hint):
  `_select_nested_strategy` only. Count 1.
- C4, new unmanaged-execution default: `active_strategy` only.
  Count 1.
- C5, new name-matching semantics (e.g. case-insensitive): the
  `resolve_strategy` body only (auto arm plus registry scan share the
  one function). Count 1.

Execution: the precedence claim (C3's ladder, hint-over-default plus
the `None`/empty-hint fallback) is execution-verified by the authorized
focused run `uv run pytest
tests/optimizer/test_nested_fetch.py::test_select_nested_strategy_honors_a_per_field_hint
--no-cov -n0 -q` (1 passed, shared venv, WT bytes). All other
challenge evidence is static census (single-site counts), which needs
no execution; the remaining oracles are cited static-reviewed (not
re-executed in this item).

## Findings

### F1: nested-connection strategy selection is single-owned (CONFIRM, zero-edit)

Contract + variation. Four sub-decisions, each owned once: (a) a
consumer spelling (name / `"auto"` / instance / `None`) resolves to a
strategy instance (`resolve_strategy`); (b) a per-field hint override
wins over the extension default (`_select_nested_strategy`); (c) the
configured default is read thin with a `"windowed"` fallback
(`nested_connection_strategy_setting`); (d) an unmanaged caller gets
the windowed floor (`active_strategy`). The rule varies on the
registered-name set, the configured default, the precedence order, the
unmanaged default, and the name-matching semantics -- one challenge
each (C1-C5), every count 1.

Sites + roles. Under System trace: 4 definitions, 5
consumer/mechanism sites (extension `__init__`, `_configuration`,
`on_execute`, `_require_strategy`, `active_nested_strategy`), 1
shared vocabulary, oracles, projections.

Challenges. C1-C5, each count 1; C3 execution-verified, the rest
static census.

Owner + lifetime. Ownership is already at the narrowest cohesive
owner per sub-decision (principle 7): the spelling map beside the
strategy protocol and registry (`nested_fetch.py`, which every
consumer can import without reversing a dependency -- the verified
acyclic runtime import the `StrategySelection` comment documents);
the precedence ladder at its sole call site's module
(`nested_planner.py`, which owns the plan loop that consumes it);
the setting read in `conf.py` beside every other thin reader; the
frame default beside the frame reader. No stored derivation beyond
the `@cache`d two-entry registry (immutable `MappingProxyType`,
process lifetime, published at first resolution) -- nothing to move.

Migration. None owed: there is no second definition to migrate.
Every consumer already composes by name.

Distinct behavior. The excluded decisions below stay separate; the
f15 value contract and the f16 skip read stay owned by their
verified siblings (this item reads `nested_strategy` and honors the
skip gate's prior verdict without restating either).

Behavioral proof. The in-tree oracles pin every verdict of the
contract independently of the owner's spelling: the resolution
truth table (names, auto, instance, setting, `None`, unknown,
hostile), the precedence rows (hint-over-default both directions
live over `/graphql`, plus `None`/empty-hint fallback), the
active-default rows (unmanaged floor, frame read, falsey-strategy
preservation), the factory/validation rows, and the thin-reader
rows. C3 execution-verified (the focused run above); all other
oracle citations static-reviewed. No `proof:` entry: nothing lands,
so no failability proof is owed.

Structural gate: no new gate owed, and the rule currently holds
(the HEAD/WT census above is the first-run check). The plausible
bypass is a second selection site -- a second name-to-instance map
or a nested-connection plan path that skips `_select_nested_strategy`.
No natural mechanical census closes that beyond a bespoke
literal/AST existence test per helper, which is the forbidden shape;
the in-tree oracles instead pin every contract verdict (rejection,
precedence both directions, defaults) so a divergent second site
fails behaviorally where it matters. Negative control reasoned: a
hand copy of `resolve_strategy`'s body passes every behavior oracle
(the copy is correct), which is exactly why no new oracle is
proposed as a gate.

Coupling: none. No defect blocks landing because nothing lands.

Freshness: input pins under Judgment; any fingerprint change reopens
the finding. The WT dirt (truth migration, typing, `except
BaseException` deletions) was censused at both states and moves no
selection site -- verdict identical at HEAD and WT.

### Rejections and exclusions (contract difference + trigger each)

- R1, lateral plan-time eligibility downgrade
  (`LateralPrefetchStrategy.plan` -> windowed floor): decides the
  plan shape WITHIN one already-selected strategy (can this SQL
  express this request?), never which strategy fetches. Queued seam
  sibling's ground. Trigger: the downgrade starts consulting the
  hint or the extension default to pick a DIFFERENT strategy rather
  than the fixed windowed floor.
- R2, fetch-time vendor dispatch (`_fetch_lateral_rows` vendor
  check): execution dispatch inside the selected strategy at fetch
  time (which SQL runs under this alias?), after selection closed at
  plan time. Trigger: a plan-time branch on vendor/capability appears
  in the selection path.
- R3, single-parent runtime gate (`single_parent_spec` eligibility +
  `SINGLE_PARENT_FAST_PATH` toggle + len==1): a fast path WITHIN the
  windowed strategy, gated by request shape and a runtime toggle,
  never a choice between backends. Trigger: the gate starts
  returning a different strategy instance.
- R4, views int-ladder (`_resolved_max_request_body_bytes`): same
  constructor > setting > default SHAPE, different value contract
  (positive-int-or-None-disable, exact-type gate, per-rung sentinel
  readings) and different reasons to change. Standing rejection,
  trigger-checked clean at HEAD. Trigger: either ladder generalizes
  to a shared validated-ladder driver (a new family, not a merge
  into this one).
- R5, deployment policy ladder (`resolve_policy`): precedence over
  sealed-vs-deployment mapping sources with per-subject validation;
  different inputs, different errors, different change reasons.
  Standing rejection, trigger-checked clean. Trigger: strategy
  selection gains a sealed-source rung.
- R6, strategy `"auto"` vs field `"auto"` (`types/base.py:653`):
  the field spelling resolves a Strawberry `auto` marker to a model
  field; the strategy spelling resolves to the auto backend. Shared
  token, disjoint contracts. Standing rejection, trigger-checked
  clean. Trigger: one vocabulary starts accepting the other's
  spellings.
- R7, GlobalID strategy setting (`relay_globalid_strategy_setting`):
  names a GlobalID type-slot policy; its values never resolve to a
  `NestedConnectionStrategy` and no selection site reads it. Trigger:
  a selection site reads the GlobalID vocabulary.
- R8, planner re-resolution vs build-time validation (standing
  hints-R7): `_require_strategy` fails loud at schema build;
  `_select_nested_strategy` re-resolves a validated spelling at plan
  time and cannot raise on a landed schema. Fail-fast admission vs
  total plan-time read -- different contracts sharing one validator
  by name. Trigger-checked clean. Trigger: the plan-time read starts
  accepting spellings the validator rejects.
- R9, `active_strategy` floor vs extension `_configuration`
  fallback (standing nested_fetch-R3): frame-absent safety floor
  (constant windowed) vs never-constructed-extension default
  (setting-resolved). Different absences, different answers.
  Trigger-checked clean. Trigger: the two defaults are required to
  agree by a new contract.
- R10, walker hint dispatch (`_apply_hint`, queued
  `optimizer-hint-dispatch`): decides WHICH hint arm fires per
  relation kind; the strategy arm is intentionally split into the
  planner (per the s12 record). Dispatch selects arms, selection
  selects backends. Trigger: dispatch starts resolving strategy
  instances.
- R11, attached-prefetch-lookups read (queued sibling): reads
  already-attached lookups downstream of planning; consumes
  selection's output, never selects. Trigger: the read starts
  choosing a backend.
- R12, recognized-queryset skeleton (queued sibling): the
  clone/rebind/fetch-all execution machinery shared by backends;
  selection never touches it. Trigger: selection branches on the
  queryset class.
- R13, scalar-only and keyset-cursor projections (queued siblings):
  child-query column inputs to the request; they vary WHAT is
  fetched, never WHICH backend fetches. Trigger: a projection feeds
  back into the strategy choice.

No new index rows owed: every member is the family rule itself, a
consumer of it, or a named queued/verified row above.

## Defects

None. No non-duplication defect was found while tracing. In
particular the no-ticked-row-wrong check passes: the run-5 naming
(`resolve_strategy` owner candidate, six indexed files including
`lateral_fetch.py`) matches HEAD -- the candidate re-derives to the
same owner, every indexed file carries a selection-role site except
`lateral_fetch.py`, which carries the explicitly-excluded adjacent
decisions (R1, R2) that justify its index membership.

## Pending execution

None. No `proof:` entry (nothing lands, so no failability proof is
owed) and no `gate:` entry. The `--cell sharded` and `--cell pg`
cells are inapplicable by construction: selection resolves from
hints, a setting read, and the execution frame at plan time and
reaches no database, alias, or dialect decision -- backend
neutrality is the load-bearing design (the `auto` strategy defers
the alias read to fetch time inside the backend, R2 ground, not
selection). The one authorized shared-tree run (the C3 precedence
test, green) plus source reads in the shared tree are the only
execution this item used.

## Judgment

CONFIRM: nested-connection strategy selection is single-owned --
four sub-decisions, one definition each (C1-C5 all count 1), every
consumer composing by name -- and the consolidation is therefore a
proved zero-edit verdict: no tracked file changed, no test added,
no `## Owned changes` row owed, no `## Implementation` section.
Thirteen exclusions carry contract differences plus triggers (R1-R13,
including four standing rejections trigger-checked clean and six
queued-sibling boundaries); f15/f16 verdicts taken as input, never
re-litigated; zero defects; no new index rows.

Freshness fingerprints (HEAD `5c3496e0`; WT pins match dispatch):

- `django_strawberry_framework/optimizer/nested_fetch.py`:
  HEAD `bedaa76e`, WT `c36826bb`
- `django_strawberry_framework/optimizer/hints.py`: HEAD `f6776564`,
  WT `ee68ae03`
- `django_strawberry_framework/optimizer/extension.py`:
  HEAD `b7b6c434`, WT `8e3fe7c1`
- `django_strawberry_framework/optimizer/nested_planner.py`:
  HEAD `8c3a45f5`, WT `b6ff0a0e`
- `django_strawberry_framework/conf.py`: HEAD `eccddc21`,
  WT `d239302a`
- `django_strawberry_framework/optimizer/lateral_fetch.py`:
  HEAD/WT `a48cb0a4` (clean)
- Adjacent readers censused (WT pins, single-state):
  `optimizer/_context.py`, `optimizer/single_parent_fetch.py`,
  `optimizer/walker.py`, `types/base.py`, `views.py`,
  `utils/policies.py` (mechanism + exclusion vocabulary only; pins
  not recorded -- any fingerprint change in the six indexed files
  reopens the finding regardless)
- Searched population: the nine spelling instruments under
  `### Enumeration`, run over `django_strawberry_framework/` plus
  the oracle sweep over `tests/`, `examples/`, `docs/`
- ITEM_BASELINE `d7f6814eac9749eb285ed99feb395ef2b839c758`;
  no item-scoped diff (zero-edit; artifact untracked)

Type gates: vacuous -- zero-edit verdict, no symbol added, moved,
or removed, so no consolidation exists to type-check; Worker-2
re-runs `mypy`, `basedpyright`, and `check_any` per convention.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (only the header lines and this
anchor were read first). Fresh trace at WT bytes, HEAD `5c3496e0`
cross-checked by grep; ITEM_BASELINE
`d7f6814eac9749eb285ed99feb395ef2b839c758`.

### W2 sites and roles

- DEFINITION S1, name-to-instance spelling map:
  `optimizer/nested_fetch.py::resolve_strategy` (the `"auto"` arm plus
  the linear registry scan, both rejection messages) with
  `optimizer/nested_fetch.py::_builtin_strategies` (the two-entry
  `MappingProxyType` registry). One body, one change site.
- DEFINITION S2, per-field override precedence (hint `nested_strategy`
  wins, else the active default):
  `optimizer/nested_planner.py::_select_nested_strategy`. Sole reader
  of `hint.nested_strategy` in the package (grep over
  `django_strawberry_framework/`); sole call site is the
  `plan_connection_relation` window loop.
- DEFINITION S3, extension-wide default ladder (explicit kwarg >
  `NESTED_CONNECTION_STRATEGY` setting > `"windowed"`): composed by
  name -- `optimizer/extension.py::DjangoOptimizerExtension.__init__`
  passes the kwarg straight into `resolve_strategy`, and the
  `None`-means-setting-means-default rung lives inside
  `resolve_strategy`'s `None` arm, which delegates the read to
  `conf.py::nested_connection_strategy_setting` (thin reader holding
  the `"windowed"` default). `extension.py::_configuration`'s
  subclass-without-`__init__` fallback calls `resolve_strategy(None)`
  by name; it restates nothing.
- DEFINITION S4, unmanaged-execution default (frame strategy else
  `WINDOWED_STRATEGY`): `optimizer/nested_fetch.py::active_strategy`.
  The frame slot it reads
  (`optimizer/_context.py::active_nested_strategy`) is transport, not
  a second decision: it stores what `extension.py::on_execute`
  published and decides nothing.
- DEFINITION S5, consumer-strategy duck-type acceptance (non-class
  value with callable `plan`): the second arm of `resolve_strategy`.
  `optimizer/hints.py::_require_strategy` delegates validation to
  `resolve_strategy` by call; its own `None`-rejects arm is a
  DISTINCT contract (an explicit `None` to the factory must not
  resolve the setting the way `resolve_strategy(None)` legitimately
  does), kept deliberately separate.
- EXCLUDED-adjacent E1, fetch-time vendor dispatch for `auto`:
  `optimizer/lateral_fetch.py::_fetch_lateral_rows` reads
  `connections[queryset.db]` (the EFFECTIVE alias) and degrades to
  the windowed body on non-Postgres. Execution dispatch, not
  plan-time selection: no name, setting, or hint is consulted. This
  is the load-bearing half of lateral_fetch's index membership.
- EXCLUDED-adjacent E2, plan-time lateral downgrade:
  `optimizer/lateral_fetch.py::LateralPrefetchStrategy.plan` falls
  back to `WINDOWED_STRATEGY.plan` when `_build_lateral_spec` refuses.
  Strategy-internal fetch-body choice, no selection vocabulary.
- PROJECTIONS (not counted): the `name = "windowed"/"auto"/"lateral"`
  class attrs (never consumed by any lookup -- grep finds no
  `.name`-based selection read), the `'windowed' | 'lateral' |
  'auto'` literal in `_require_strategy`'s rejection message
  (validation delegates to `resolve_strategy` on the next line), and
  every docstring spelling of the vocabulary.
- CONSUMERS (all by name): `extension.py` (`__init__`,
  `_configuration`, `on_execute` frame publish + read-only
  `nested_connection_strategy` property), `nested_planner.py`
  (`_select_nested_strategy` + its one call site), `hints.py`
  (`_require_strategy`, `strategy()` factory, `__post_init__` arm),
  `conf.py` (thin setting reader), example project
  (`strategy_schemas.py`, `test_generic_connection.py`,
  `test_query/test_optimizer_auto_api.py` per-field override rows).
- ORACLES (independent, spell expectations literally):
  `tests/optimizer/test_nested_fetch.py` (registry identity,
  `resolve_strategy` name/auto/instance/rejection/hostile-`__eq__`
  rows, `test_select_nested_strategy_honors_a_per_field_hint`),
  `tests/optimizer/test_hints.py` (factory/`None`/typo rows),
  `tests/optimizer/test_walker.py` (refusing/accepting/raising
  strategy frames, lateral-through-walker, both-strategies
  unwindowable rows), `tests/optimizer/test_extension.py`
  (construction-settled strategy rows),
  `examples/fakeshop/test_query/test_optimizer_auto_api.py`
  (live-tier hint-wins-over-default rows both directions).

### W2 change challenges (fresh, incl. ones W1 may not have posited)

- C-W1, new built-in kind `"correlated"`: forces exactly one
  definition edit -- one registry entry in `_builtin_strategies`
  (the unknown-name message derives from `sorted(registry)` and
  follows for free). The `_require_strategy` message literal and the
  `.name` attrs are projections; a stale message mislists but
  misdecides nothing. Count 1.
- C-W2, rename `"windowed"` to `"prefetch"`: the load-bearing edit is
  the registry key plus the `conf.py` default (TWO edits, but ONE
  definition of the spelling -- the default is the ladder's terminal
  value, not a second map; nothing looks the default up by name).
  Count 1 definition.
- C-W3, per-field override gains a third rung (e.g. per-model
  default): one edit in `_select_nested_strategy`; no other site
  reads `nested_strategy`. Count 1.
- C-W4, precedence inversion (extension default beats the hint): one
  edit in `_select_nested_strategy`. Count 1.
- C-W5, default ladder gains a rung (e.g. env var between kwarg and
  setting): one edit in `resolve_strategy`'s `None` arm; the
  extension pass-through and `_configuration` fallback need no
  touch. Count 1.
- C-W6, unmanaged-execution default changes: one edit in
  `active_strategy`. Count 1.
- C-W7, consumer-strategy acceptance tightens (e.g. require
  `isinstance` of the Protocol): one edit in `resolve_strategy`'s
  duck-type arm; `_require_strategy` inherits it by delegation.
  Count 1.
- C-W8, `auto` stops deferring and pins at plan time: forces the
  `resolve_strategy` `"auto"` arm AND `_fetch_lateral_rows`' vendor
  read to move together -- but that is the REUNIFICATION trigger for
  excluded E1, not a second definition today: E1 currently consults
  no selection vocabulary. Count 1 for selection; E1 stays excluded
  with a stated trigger.

No posited selection change forces count > 1 with a landable owner.
The nearest near-miss, C-W2's registry-key-plus-default pair, is one
map plus its ladder's terminal value, not two maps: the default is
never consulted by name and no second site maps names to instances
(package-wide grep for `"windowed"|"lateral"|"auto"` code spellings
finds only the registry, the `resolve_strategy` arm, the `conf.py`
default, the unconsumed `.name` attrs, and the `_require_strategy`
message literal; `types/base.py` `"auto"` is the unrelated
StrawberryAuto vocabulary).

### W2 owner choice (principle 7)

- S1/S3-terminal/S4/S5: `optimizer/nested_fetch.py::resolve_strategy`
  (with `_builtin_strategies` and `active_strategy` beside it) --
  the narrowest module every legitimate consumer already depends on
  without reversing a dependency (`extension`, `hints` at runtime,
  `nested_planner` all import `nested_fetch`; `nested_fetch` imports
  none of them). ENDORSE the plan's owner candidate, re-derived.
- S2: `optimizer/nested_planner.py::_select_nested_strategy` stays
  where it is -- the planner's own composition point (per-field hint
  read + active-default fallback); moving it into `nested_fetch`
  would drag the `OptimizerHint` import against the verified acyclic
  direction. One definition, already at its narrowest valid owner.
- The family verdict is therefore CONFIRM single ownership with the
  owner SPLIT by sub-decision exactly as the code has it: spelling
  map at `resolve_strategy`, precedence ladder at
  `_select_nested_strategy`, ladder terminal at
  `nested_connection_strategy_setting`, unmanaged default at
  `active_strategy`. No consolidation to land.

### W2 matrix pre-discharge (against the real surface)

- Cross-flavor: selection has exactly two consumer seams (extension
  kwarg, hint field), both typed `StrategySelection` from the one
  definition; no sibling flavor re-selects. Discharged by the
  consumer grep above.
- Sync/async twins: selection is pure synchronous resolution
  consumed identically by both plan paths; the strategy protocol's
  `plan` is sync-only. No twin surface.
- Derived knowledge: registry keys are literals, never derived from
  `.name` attrs (and nothing derives names back from instances).
  The `sorted(registry)` message derivation composes by name.
- Round-trip: selection is one-directional (name -> instance); no
  inverse mapping exists anywhere (no instance-to-name read found).
- Contracts in other media: oracles spell names literally and would
  fail on drift (independent); docs/projections describe only.
- Enforcement by omission: the family is "who selects", not "who is
  guarded" -- every nested-connection plan flows through the single
  `_select_nested_strategy` call site; no second planning entry
  point bypasses selection (the walker frames carry an already-
  selected instance).

### W2 structural-gate expectation

Single-owner rules need a gate only where a bypass is plausible with
a justified population. The plausible bypass here would be a second
name-to-instance map or a second `nested_strategy` reader; both are
one-grep populations already enumerated above. A gate-only finding is
NOT owed: the mechanism is a plain function call, not a bypassable
convention, and no second definition exists to guard against. The
independent oracles (esp. the hostile-`__eq__` and per-field live
rows) already fail on the divergences that matter.

## W2 reconciliation (read AFTER the trace above; every delta explicit)

Reconciled against `## Findings` after the trace above was recorded.
Verdict inputs, one line per adjudicated claim:

- F1 sub-decision (a) spelling map at `resolve_strategy`: ENDORSE.
  W1's C1 (new name, count 1) and C5 (matching semantics, count 1)
  reproduce; my harder C-W1 (message follows via `sorted(registry)`)
  and C-W2 (registry key + `conf.py` default = one map plus its
  ladder's terminal value, never consulted by name) also count 1.
  My S5 duck-type arm is W1's (a) folded in -- same body, no
  disagreement, granularity only.
- F1 sub-decision (b) precedence ladder at `_select_nested_strategy`:
  ENDORSE. W1's C3 (count 1) reproduces; my C-W3 (third rung) and C-W4
  (inversion) also force exactly that one site -- package-wide grep
  confirms the sole `nested_strategy` reader and the sole call site
  at `nested_planner.py:1436`. C3 execution-verified twice: W1's
  authorized run plus my fresh shared-tree re-run
  (`test_select_nested_strategy_honors_a_per_field_hint` +
  `test_resolve_strategy_by_name_auto_and_instance`, 2 passed).
- F1 sub-decision (c) thin setting read at
  `nested_connection_strategy_setting`: ENDORSE. W1's C2 (count 1)
  reproduces; my C-W5 (new ladder rung lands in the `None` arm
  alone) agrees. Single production caller confirmed.
- F1 sub-decision (d) unmanaged floor at `active_strategy`: ENDORSE.
  W1's C4 (count 1) reproduces; my C-W6 agrees. The frame slot is
  transport, confirmed at `_context.py:302` (stores, never decides).
- Owner choice (principle 7): ENDORSE as stated -- per-sub-decision
  narrowest owners identical to mine (spelling map `nested_fetch`,
  ladder `nested_planner`, thin read `conf.py`, floor beside the
  frame reader), including the acyclic-import reasoning for keeping
  S2 out of `nested_fetch`. No consolidation to land; my eight
  challenges found no count->1 change with a landable owner.
- R1 lateral plan-time downgrade: ENDORSE (my E2; verified at
  `lateral_fetch.py:986`-`:990` -- fixed windowed floor, no
  selection vocabulary; trigger real).
- R2 fetch-time vendor dispatch: ENDORSE (my E1; verified at
  `lateral_fetch.py:532`-`:534` -- effective-alias read at fetch
  time; the C-W8 reunification trigger matches W1's trigger).
- R3 single-parent runtime gate: ENDORSE (grep: no selection
  vocabulary in `single_parent_fetch.py` beyond prose; trigger real).
- R4 views int-ladder: ENDORSE, trigger-clean at HEAD (verified at
  `views.py:179` -- exact-int gate, None-disables, per-rung
  readings; shares no code with selection).
- R5 deployment policy ladder: ENDORSE, trigger-clean at HEAD
  (verified `utils/policies.py::resolve_policy` -- mapping
  canonicalization over explicit/setting/default; strategy
  selection has no sealed-source rung).
- R6 field `"auto"`: ENDORSE, trigger-clean (verified
  `types/base.py:653` StrawberryAuto vocabulary, disjoint).
- R7 GlobalID strategy setting: ENDORSE (verified `conf.py:514`;
  no selection site reads it -- grep-clean).
- R8 build-vs-plan validation split (standing hints-R7): ENDORSE,
  trigger-clean (matches my S5 distinct-`None`-contract analysis;
  plan-time re-resolution cannot raise on a landed schema because a
  non-`None` name never touches the setting).
- R9 floor-vs-fallback absences (standing nested_fetch-R3): ENDORSE,
  trigger-clean (constant `WINDOWED_STRATEGY` vs setting-resolved
  `resolve_strategy(None)` -- verified both bodies).
- R10 walker hint dispatch: ENDORSE -- names the REAL open row
  `optimizer-hint-dispatch`, whose own index text records the
  strategy-arm split into the planner.
- R11 attached-prefetch-lookups read: ENDORSE with a precision note
  (observation O1 below) -- the ground is real and covered by the
  open row `prefetch-attach-column-projection`, but R11 cites it as
  "(queued sibling)" without naming the row, unlike R10/R12.
- R12 recognized-queryset skeleton: ENDORSE -- real open row
  `recognized-fetch-queryset-skeleton`.
- R13 scalar-only + keyset projections: ENDORSE -- both real open
  rows (`scalar-only-window-projection`,
  `keyset-cursor-column-projection`).
- Six queued-sibling boundaries: COUNT CONFIRMED (R1 seam, R10
  dispatch, R11 attach-read, R12 skeleton, R13 x2 projection rows).
- Four standing rejections: OBSERVATION O2 (below) -- five rows
  carry standing labels (R4/R5/R6/R8/R9) while Judgment says four;
  all five are trigger-clean on fresh evidence, so the count moots
  nothing. Scratch-prose nit, not verdict-spending.
- f15/f16 input boundary: ENDORSE -- taken as input, nothing
  re-litigated (no hint-shape/skip-semantics claims beyond the
  input citation), nothing dropped (the `nested_strategy` read is
  owned HERE at S2; the skip gate is honored upstream of it).
- Matrix discharge: ENDORSE all six axes against the real surface
  (cross-flavor searched with real alternatives; sync/async +
  round-trip inapplicable with verified reasons -- sync-only
  protocol, no instance-to-name read; derived-knowledge searched --
  my independent grep likewise finds zero `.name` readers;
  other-media counted; omission enumerated over the single call
  site, both construction paths, the single frame publisher).
- "No new index rows owed": ENDORSE -- every member is the family
  rule, a by-name consumer, a verified row, or a real queued row.
- Pending-execution "None": ENDORSE -- nothing lands, no `proof:`
  owed; C3 executed green twice. Plain `verified` (no `pending
  execution`).
- Cells "inapplicable by construction": ENDORSE -- selection reads
  hints/setting/frame only; the ONLY alias reads in the optimizer
  are the R2 fetch-time effective-alias check and the unrelated
  index-advisory alias loop (`nested_planner.py:149`). The
  `auto`-defers-alias claim is verified AT ITS SITE
  (`_fetch_lateral_rows`: `connections[queryset.db]`, vendor gate,
  windowed-body fallback): no default-alias consultation, no
  plan-time vendor branch. Backend neutrality load-bearing and
  holding.
- Structural gate + negative control: ENDORSE -- matches my
  pre-registered expectation (no gate owed; bespoke existence test
  is the forbidden shape; oracles pin the verdicts; hand-copy
  control reasoned correctly).
- Freshness fingerprints: ENDORSE -- all six indexed HEAD/WT pins
  recomputed by me and matching exactly
  (`bedaa76e`/`c36826bb`, `f6776564`/`ee68ae03`,
  `b7b6c434`/`8e3fe7c1`, `8c3a45f5`/`b6ff0a0e`,
  `eccddc21`/`d239302a`, `a48cb0a4` clean). Adjacent-reader pins
  explicitly declined with a stated reopen rule -- accepted; the
  trigger-checks re-run each cycle and every adjacent module is
  itself a plan item whose own dirt reopens its own challenges.
  (Observation, not a defect.)
- Zero-edit structural gates, ALL RE-VERIFIED by me: no
  `## Implementation` section in the artifact; 6/6 WT pins match
  dispatch pins; `git diff ITEM_BASELINE --name-only` is the plan
  edit alone (`docs/dry/dry-0_0_15.md`); the artifact is untracked
  scratch (raw `path:NN` allowed, no style cleanup owed).
  Tracked diff EMPTY -- confirmed.
- AGENTS.md prose on the item-scoped diff: VACUOUS (no tracked
  path touched). `ruff format --check` + `ruff check`: VACUOUS --
  zero tracked `.py` touched (my own edit is untracked scratch
  `.md`, outside ruff's population). Recorded as such, not run
  against `.` per the no-blanket rule.
- Type gates whole-package, RE-RUN by me in the shared tree:
  `uv run mypy` -> "Success: no issues found in 119 source files";
  `uv run basedpyright` -> "0 errors, 0 warnings, 0 notes";
  `uv run python scripts/check_any.py` -> "130 allowed use(s) of
  Any at 90 site(s)". All green.

Observations (scratch-precision only; neither is a `## Defects`
entry -- no production-code defect was found -- and neither spends
the verdict):

- O1 (Worker-2): R11 cites its queued-sibling boundary without
  naming the row; the ground resolves to real open row
  `prefetch-attach-column-projection`. Zero misrouting risk (that
  family censuses the read itself).
- O2 (Worker-2): Judgment says "four standing rejections" but five
  rows carry standing labels (R4/R5/R6/R8/R9). All five verified
  trigger-clean fresh, so the verdict is unaffected either way.

Deltas between my trace and W1's findings: NONE material. Sites,
roles, counts (C1-C5 = 1 each, plus my eight harder challenges all
count 1), owner split, every R-row contract difference and trigger,
the f15/f16 boundary, the matrix, the gate reasoning, and the
fingerprints all converge. The two observations above are the
complete difference list.

Provenance: shared venv for the one focused re-run (slots 1-3
venv damage noted in dispatch; no workspace run needed --
zero-edit item, no source-mutating proof); everything else is
source reads + grep census at WT bytes with HEAD cross-checks.
No production fix written or demanded. W1 sections byte-intact
(this section and the Status flip are my only additions).

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
