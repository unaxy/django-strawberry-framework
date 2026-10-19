# Review · Comments: `django_strawberry_framework/registry.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=da5c1882de6a2330b1ce41878b78c073ef5a36b4

## Trace

Read the whole live target (641 lines) plus every docstring and comment in its
own test module `tests/test_registry.py` (2086 lines) whole, plus the prose
other test modules hold about the target's symbols (`tests/filters/`,
`tests/orders/`, `tests/optimizer/test_extension.py`,
`tests/test_relay_connection.py`, `tests/test_relay_node_field.py`,
`tests/test_list_field.py`, `tests/types/`), plus the package prose that cites
the target's symbols (`types/finalizer.py`, `types/base.py`,
`types/converters.py`, `types/relations.py`, `optimizer/extension.py`,
`optimizer/walker.py`, `connection.py`, `relay.py`, `utils/inputs.py`,
`utils/imports.py`, `filters/` + `orders/` inits) to confirm or deny each
claim. Required reading done: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan, `rev-registry.md`; sibling axis records
`rev-registry.{performance,mechanics}.md` do not exist yet (concurrent
passes), so no Handoff or Cross-axis sections were read. Routed lead from
connection.py Comments judged: CONFIRMED for the connection twin (F1) and the
relay twin (F2); REJECTED for the order twin (R1, mechanism matches).

Instruments (all static, shared tree): `review_inspect.py` orientation;
`build_tree_md.py --list-docstrings` (target and own test module: both ok);
`check_citations.py --paths ... --substrings` (target: 1 citation resolves;
own test module: 26 resolve, 0 substring pinpoints — the one `#"..."` pinpoint
is wrapped across two lines, F9); provenance sweep
(`spec-|card|round|worker|legacy|moved from|no longer|previously|\bnow\b|fix
for`, case-insensitive) over target + own test module, every hit triaged
below. No database cell is reached: every instrument is a static reader that
never imports the package, so sharded and pg are inapplicable by
construction. No workspace runs, no run ids.

Looks-for discharged: module first lines (target + own test module, both
one-line / one-sentence / trailing `.`, no e.g./i.e.); mood gate
(functions/methods imperative, classes descriptive — one violation, F7);
no "Tests that"/"Ensures" test openings; no we/you/I; no line-number source
refs; every `path::Symbol` resolves; no public symbol lacks a docstring;
duplication sweep (one candidate, R8); unrecorded-separation sweep (one
candidate, R7); spec-pointer sweep (kept pointers, R5). Proposed edits touch
no module first line, so no TREE.md churn.

Target dirty at read (concurrent work, per dispatch): fingerprints below are
what was graded.

Fingerprints (`git hash-object` at read; ` M
django_strawberry_framework/registry.py`, ` M tests/orders/test_inputs.py`,
everything else clean):

- `django_strawberry_framework/registry.py` 492654d219d1061fef33f186d962dc5369b71ebe
- `tests/test_registry.py` 48af782ff707baaf1619da26d2e286d2ba5178f4
- `django_strawberry_framework/utils/imports.py` 291ecedd30c7d8af9c007758112e867c09d031eb
- `django_strawberry_framework/filters/__init__.py` 86b258186638c96995e31919346f44d7951c65ea
- `django_strawberry_framework/filters/inputs.py` a932dbf85d89791280774b0600a40b5fb43b89e4
- `django_strawberry_framework/utils/inputs.py` b5af8255dfa18a2ff423cdd2de211723c5a15590
- `django_strawberry_framework/types/finalizer.py` b9d8acb2b9428cc8297550414ff86bdd98e0d1a7
- `django_strawberry_framework/types/base.py` dc67f084cbc969d64b7b1f1ef18c388095d394f7
- `django_strawberry_framework/types/converters.py` f6cadb0856c725d96ce316abb4418b4c9d55bf9d
- `django_strawberry_framework/types/relations.py` 5e9b5cdbc7fb919f15afef090a2aae5c7663b706
- `django_strawberry_framework/relay.py` e75e2b66a9b406f60d55e952a001d640392331c1
- `django_strawberry_framework/connection.py` 1fca6266cd5f748915875badf1881680b599de37
- `django_strawberry_framework/optimizer/extension.py` 39a8739c7e568e89aff030d98d0ba31d9f04371c
- `django_strawberry_framework/optimizer/walker.py` d5759ef8533a6218942a0a2a33e64f59599a93a7
- `django_strawberry_framework/orders/__init__.py` ed546f9c70d56d73e0d84a029e9e04f27da3934b
- `django_strawberry_framework/orders/inputs.py` 2d258da74ee36f5d851ffa6550462b0fd65bd460
- `tests/filters/test_finalizer.py` 4bbcfaabb80d580658f7ee7321813c351625fd96
- `tests/filters/test_sets.py` ea6d0b04d9a82214d6bbe45778bb93de1dc1121e
- `tests/optimizer/test_extension.py` 8b3e2e1c5f940803cd283a7a0683eb318929446c
- `tests/types/test_definition_order.py` aff87c5211e97940781d03d3bc2b43fb3bb83fff
- `tests/test_relay_node_field.py` af4866a1bd06dbb9055c89f7aa1c2c93ecfa828a
- `tests/test_relay_connection.py` fe2b2d24ab6e71e6238183690b02821abb239497
- `tests/test_list_field.py` d78aa5e79fee14b37564f856d3d4bc74e7d9630b
- `tests/types/test_converters.py` ddf24f5997a5185dec079598d7506b6c7d3cf6a3
- `tests/types/test_resolvers.py` d78d605f1dc70874ffa6ebdcf17051b3a81e5e92
- `tests/orders/test_inputs.py` be8b48a3373a999175fe269918d5a776a9171621
- `tests/orders/test_composition.py` d0cc87225bde5d29273e9139479ec17591a6dc25
- `tests/types/test_relations.py` 2e18880ad7f4f816ee74327c2c128f6fab3398bc
- `examples/fakeshop/test_query/test_library_api.py` 26dd0abb537df74f06fe864bd0e3c22634307541
- `examples/fakeshop/test_query/test_schema_composition_api.py` 6df1401b3bf7481467573e599c7ecf1b3a86420d

Scratch: `docs/review/temp-tests/registry/comments/` (`inspect/`,
`registry.json`, `citations-test-registry.json`).

## Findings

### High

None.

### Medium

#### F1 — connection twin pins a retired `clear()` guard block

- Observation: `tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule`
  docstring + inline comment describe an `except ImportError` guard with a
  cycle-safe local import inside `clear()` that no longer exists.
- Evidence: live `TypeRegistry.clear` performs no import; it replays
  `iter_subsystem_clears()` resolved callables (`registry.py` lines 621-625).
  The connection subsystem binds `clear_connection_type_cache` and
  `clear_window_edge_class_cache` at its own import time
  (`connection.py` lines 1415, 1432), so poisoning `sys.modules` after import
  skips no block — the replay runs the already-resolved callables. The test
  still passes (it pins "clear() imports nothing", the live contract) but its
  prose narrates the retired shape. Routed lead from connection.py Comments
  confirmed.
- Impact: a reader learns a mechanism (`from .connection import ...` guard,
  "skips that block") that contradicts the body; the next clear() refactor
  inherits a false constraint.
- Severity: Medium (stale test-module prose).
- Recommendation: rewrite in the filter/order twins' replay framing (below).
- Must not change: n/a.
- Proof: `grep -c -e 'spec-030-connection_field-0_0_9' -e 'from \.connection import' tests/test_registry.py` prints `0`; the rewritten docstring + comment grade true.
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule`
- Grade: stale
- Text before (docstring):
  `The connection-cache ``except ImportError`` guard in ``clear()`` is best-effort. / Connection twin of ``test_clear_tolerates_unimportable_order_submodules``. The connection-type-cache co-clear (``clear_connection_type_cache``) uses a cycle-safe local import (``spec-030-connection_field-0_0_9`` P3b). If ``connection.py`` cannot be imported (forced here by poisoning ``sys.modules``), ``clear()`` skips that block and still clears the registry's own state rather than raising.`
  Text before (comment): ` ``None`` in ``sys.modules`` makes ``from .connection import ...`` raise ImportError, exercising the connection-cache guard.`
- Text after (docstring):
  ```text
  ``clear()`` itself imports nothing, so a broken ``sys.modules`` cannot break it.

  Connection twin of ``test_clear_tolerates_unimportable_order_submodules``. The connection
  subsystem binds its teardown callbacks at ITS import time via ``register_subsystem_clear``
  (``clear_connection_type_cache``, ``clear_window_edge_class_cache``), and ``clear()`` replays
  the already-resolved callables. That replay imports nothing, so the poisoned ``connection``
  module cannot make ``clear()`` raise: the registry's own state is dropped either way.
  ```
  (keep the `Registry lifecycle` paragraph). Text after (comment):
  ```text
  # ``None`` in ``sys.modules`` is the shape that makes an import of
  # the module raise ImportError. ``clear()`` itself runs no import,
  # and the replayed connection callbacks import nothing, so nothing
  # on the teardown path can raise OUT of ``clear()``.
  ```

#### F2 — relay twin pins the same retired `clear()` guard block

- Observation: `tests/test_registry.py::test_clear_tolerates_unimportable_relay_module`
  docstring + inline comment describe a node-field-ledger `except ImportError`
  guard with a cycle-safe local import inside `clear()` that no longer exists.
- Evidence: same as F1: `clear()` replays resolved callables; relay binds
  `_clear_node_fields_declared` at its own import time (`relay.py` line 100).
  The docstring's closing sentence (positive co-clear pinned by
  `tests/test_relay_node_field.py::test_node_field_without_node_types_raises_at_finalize`)
  is true — that test's ledger-reset half (`registry.clear()` then a clean
  finalize) pins it — so only the guard-mechanism sentences and the inline
  comment are stale. Routed lead's "relay twin shares the staleness"
  confirmed.
- Impact: same as F1: false mechanism constraint on the next clear() change.
- Severity: Medium (stale test-module prose).
- Recommendation: rewrite in the replay framing (below), keeping the true
  positive-path sentence and citation.
- Must not change: n/a.
- Proof: `grep -c -e 'spec-032 Decision 8' -e 'from \.relay import' tests/test_registry.py` prints `0`; the rewritten docstring + comment grade true.
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/test_registry.py::test_clear_tolerates_unimportable_relay_module`
- Grade: stale
- Text before (docstring):
  `The node-field-ledger ``except ImportError`` guard in ``clear()`` is best-effort. / Relay twin of ``test_clear_tolerates_unimportable_connection_submodule``. The root-node-field ledger co-clear (``_node_fields_declared.clear()``, spec-032 Decision 8) uses a cycle-safe local import. If the top-level ``relay.py`` cannot be imported (forced here by poisoning ``sys.modules``), ``clear()`` skips that block and still clears the registry's own state rather than raising.`
  Text before (comment): ` ``None`` in ``sys.modules`` makes ``from .relay import ...`` raise ImportError, exercising the ledger guard.`
- Text after (docstring):
  ```text
  ``clear()`` itself imports nothing, so a broken ``sys.modules`` cannot break it.

  Relay twin of ``test_clear_tolerates_unimportable_connection_submodule``. The relay subsystem
  binds its ledger teardown at ITS import time via ``register_subsystem_clear``
  (``_clear_node_fields_declared``), and ``clear()`` replays the already-resolved callable. That
  replay imports nothing, so the poisoned ``relay`` module cannot make ``clear()`` raise: the
  registry's own state is dropped either way. The positive co-clear path is pinned by
  ``tests/test_relay_node_field.py::test_node_field_without_node_types_raises_at_finalize``.
  ```
  (keep the `Registry lifecycle` paragraph). Text after (comment):
  ```text
  # ``None`` in ``sys.modules`` is the shape that makes an import of
  # the module raise ImportError. ``clear()`` itself runs no import,
  # and the replayed relay callback imports nothing, so nothing
  # on the teardown path can raise OUT of ``clear()``.
  ```

#### F3 — unregister section comment narrates a replacement that never completed

- Observation: the `tests/test_registry.py` section comment above the
  unregister tests calls `unregister` "the new public surface that replaces
  the direct private-map pokes in the walker/extension fixtures and the older
  check_schema-audit fixtures", with a four-map census.
- Evidence: the extension fixture `tests/optimizer/test_extension.py::_force_unregister_after_finalize`
  still pokes `registry._models/_types/_primaries/_definitions` deliberately —
  its docstring says the public `unregister` honours `_check_mutable` and the
  helper exists exactly for the post-finalize simulation `unregister`
  refuses, matching `registry.py::TypeRegistry.unregister`'s own "must use a
  test-local helper" paragraph. No walker fixture pokes private maps. So
  "replaces" is false as a completed migration, "new"/"older" are temporal
  provenance, and the census omits the pending-relation purge and the
  connection-cache eviction `unregister` performs.
- Impact: misdirects the next fixture author (the pokes look like leftovers
  to convert; converting the post-finalize one is impossible by design) and
  undercounts the method's scope.
- Severity: Medium (stale test-module comment).
- Recommendation: present-tense scope + the deliberate exception (below).
- Must not change: n/a.
- Proof: `grep -c 'new public surface' tests/test_registry.py` prints `0` and `grep -c '_force_unregister_after_finalize' tests/test_registry.py` prints `1`; the rewritten comment grades true.
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/test_registry.py` #"The ``unregister`` public helper"
- Grade: stale
- Text before:
  ```text
  # The ``unregister`` public helper. Tests below
  # exercise the new public surface that replaces the direct private-map
  # pokes in the walker/extension fixtures and the older
  # check_schema-audit fixtures (types list, model index, primary slot, and
  # definition map).
  ```
- Text after:
  ```text
  # The ``unregister`` public helper. Tests below exercise removal of one
  # type's traces (types list, model index, primary slot, definition map,
  # sourced pending relations, connection-cache entry), sibling preservation,
  # the primary-loss-then-audit contract, the unknown-type no-op, and the
  # post-finalize refusal. The extension module's ``check_schema`` fixtures
  # keep their own private-map surgery (``_force_unregister_after_finalize``)
  # for the post-finalize simulation ``unregister`` deliberately refuses.
  ```

#### F4 — `iter_types` names the walker as a consumer that never calls it

- Observation: `TypeRegistry.iter_types` docstring ends "Public iterator so
  consumers (the schema audit, the walker) do not reach into ``_types``
  directly", but the walker never calls `iter_types`.
- Evidence: repo-wide sweep finds exactly one production caller,
  `optimizer/extension.py::DjangoOptimizerExtension.check_schema` line 1465
  (the schema audit); `git log -S 'iter_types' -- optimizer/walker.py` is
  empty, so the walker never did. The walker routes through `registry.get` /
  `registry.get_definition` instead.
- Impact: a reader tracing "who iterates the registry" is sent to a module
  with no such call; a walker refactor inherits a phantom coupling.
- Severity: Medium (false consumer citation in a production docstring; the
  yield contract itself is stated correctly).
- Recommendation: name the real consumer only (below).
- Must not change: n/a.
- Proof: `grep -c 'the schema audit, the' django_strawberry_framework/registry.py` prints `0` and `grep -c 'so the schema audit does not reach into' django_strawberry_framework/registry.py` prints `1`; the rewritten docstring grades true.
- Freshness: trace (no beyond-trace files).
- Symbol: `django_strawberry_framework/registry.py::TypeRegistry.iter_types`
- Grade: stale
- Text before: `by model. Public iterator so consumers (the schema audit, the walker) do not reach into ``_types`` directly.`
- Text after: `by model. Public iterator so the schema audit does not reach into ``_types`` directly.`

#### F5 — "every mutator raises" overclaims: `clear()` bypasses the guard by design

- Observation: `tests/test_registry.py::test_mutators_reject_calls_after_mark_finalized`
  first line claims "After ``mark_finalized``, every mutator raises
  ``ConfigurationError``", but `clear()` is the public mutator that
  intentionally bypasses `_check_mutable`.
- Evidence: `TypeRegistry.clear` never calls `_check_mutable`, and its own
  docstring states "this is the only public mutator that bypasses the guard"
  so test teardown can reset a finalized registry. All other mutators
  (`register`, `register_type_teardown`, `unregister`,
  `register_definition`, `add_pending_relation`, `discard_pending`,
  `register_enum`, `register_with_definition` via `register`) do call it.
- Impact: states the wrong contract for the defense-in-depth boundary; a
  reader could conclude clear-after-finalize (the documented recovery path)
  raises.
- Severity: Medium (false universal in a test docstring about a guard).
- Recommendation: scope the universal to guarded mutators (below).
- Must not change: n/a.
- Proof: `grep -c 'every mutator raises' tests/test_registry.py` prints `0` and `grep -c 'every guarded mutator raises' tests/test_registry.py` prints `1`; the rewritten first line grades true.
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/test_registry.py::test_mutators_reject_calls_after_mark_finalized`
- Grade: stale
- Text before: `"""After ``mark_finalized``, every mutator raises ``ConfigurationError``.`
- Text after: `"""After ``mark_finalized``, every guarded mutator raises ``ConfigurationError``.`

#### F6 — orders composition fixture cites the retired "local-import dance"

- Observation: `tests/orders/test_composition.py::_isolate_registry`
  docstring says `registry.clear()` triggers the namespace + helper-set
  clears "via the local-import dance (spec-028 Decision 9)".
- Evidence: `clear()` performs no local import; every named clear is a
  resolved `register_subsystem_clear` callback replayed from
  `iter_subsystem_clears()`. The trigger claim is true; only the mechanism
  noun is the retired shape (same family as F1/F2). Single repo-wide
  occurrence of the phrase.
- Impact: same as F1/F2 at one remove: the composition fixture's rationale
  names a mechanism that contradicts the body.
- Severity: Medium (stale test-module prose about the target's symbol).
- Recommendation: name the replay mechanism (below); keep the spec-028
  Decision 9 pointer.
- Must not change: n/a.
- Proof: `grep -c 'local-import dance' tests/orders/test_composition.py` prints `0`; the rewritten sentence grades true.
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/orders/test_composition.py::_isolate_registry`
- Grade: stale
- Text before: `plus both ``_helper_referenced_*.clear()`` via the local-import dance (spec-028 Decision 9); the explicit per-ledger clears below pin the`
- Text after: `plus both ``_helper_referenced_*.clear()`` via the registered-callback replay (spec-028 Decision 9); the explicit per-ledger clears below pin the`

### Low

#### F7 — `register_with_definition` first line is not imperative

- Observation: the first line reads "Atomic ``register`` +
  ``register_definition`` pair." — a noun phrase, while every other
  function/method in the module opens imperative and the Comments axis is
  the mood gate (D401 unchecked).
- Evidence: read of all 30 method/function first lines in the target; this
  is the only non-imperative one.
- Impact: one inconsistent entry point in an otherwise uniform surface.
- Severity: Low.
- Recommendation: imperative first line (below).
- Must not change: n/a.
- Proof: `grep -c 'Atomic ``register``' django_strawberry_framework/registry.py` prints `0`; the rewritten first line is imperative and grades true.
- Freshness: trace (no beyond-trace files).
- Symbol: `django_strawberry_framework/registry.py::TypeRegistry.register_with_definition`
- Grade: duplicates the code
- Text before: `"""Atomic ``register`` + ``register_definition`` pair.`
- Text after: `"""Register ``type_cls`` and its definition as one atomic pair.`

#### F8 — `_detach_type_from_model` says `register` does not touch `_primaries`

- Observation: "Callers own everything else that ``register`` does NOT
  touch here - ``_primaries``, ..." reads, with `register` as the subject,
  as "register does not touch _primaries" — but `register` sets
  `_primaries[model]` (`registry.py` line 258).
- Evidence: the only true parse binds "here" to the helper while the
  subject is `register`, which is ungrammatical; a reader checking the
  sentence against `register`'s body finds it contradicted. The operative
  claims around it (callers own the rest; unregister purges; the rollback
  restores) are all true.
- Impact: a maintainer extending `register` with a new side effect misreads
  which state this helper covers.
- Severity: Low (bounded clarity in an internal docstring).
- Recommendation: bind the clause to the helper (below).
- Must not change: n/a.
- Proof: `grep -c 'does NOT touch here' django_strawberry_framework/registry.py` prints `0`; the rewritten sentence grades true.
- Freshness: trace (no beyond-trace files).
- Symbol: `django_strawberry_framework/registry.py::TypeRegistry._detach_type_from_model`
- Grade: stale
- Text before: `invariant is maintained. Callers own everything else that ``register`` does NOT touch here - ``_primaries``, ``_definitions``, pending relations, type teardowns - because ...`
- Text after: `invariant is maintained. Callers own everything this helper does not undo - ``_primaries``, ``_definitions``, pending relations, type teardowns - because ...` (rest of the paragraph unchanged).

#### F9 — unregister-contract citation wraps its pinpoint across two lines

- Observation: `tests/test_registry.py::test_unregister_of_primary_leaves_state_that_audit_rejects`
  cites `registry.py::TypeRegistry.unregister #"When ``type_cls`` is the /
  primary for its model"` with the `#"..."` pinpoint split across two
  physical lines, so it matches no source text.
- Evidence: `check_citations.py --paths tests/test_registry.py --substrings`
  reports 0 substring pinpoints — the wrapped pinpoint is invisible to the
  gate (it resolves as a bare symbol only). Convention requires quoting text
  on one source line; `registry.py` line 322 carries "its primary even if
  siblings remain" on one line.
- Impact: the pin the docstring claims ("at ...") is unverifiable and
  silently rots.
- Severity: Low.
- Recommendation: one-line citation with a single-line substring (below).
  The resulting line is 102 chars: an unbreakable citation line under the
  110 E501 grace, not a violation.
- Must not change: n/a.
- Proof: `uv run python scripts/check_citations.py --paths tests/test_registry.py --substrings --json | uv run python -c "import json,sys; d=json.load(sys.stdin); c=[x for x in d['citations'] if 'unregister' in x['cite'] and x['kind']=='substring']; assert len(c)==1 and c[0]['substring'] is not None and c[0]['resolved'], json.dumps(c); print('pinpoint ok')"` prints `pinpoint ok`. [Worker-0 one-token correction per the Verify comments open thread (1): the tool emits both the bare-symbol and the substring records for the line, so the filter must select `kind=='substring`; review-time text otherwise untouched.]
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/test_registry.py::test_unregister_of_primary_leaves_state_that_audit_rejects`
- Grade: stale
- Text before:
  ```text
  Pins the contract narrated by ``unregister``'s docstring at
  ``django_strawberry_framework/registry.py::TypeRegistry.unregister #"When ``type_cls`` is the
  primary for its model"``: when ``type_cls`` is the primary for its model, the model loses its
  ```
- Text after:
  ```text
  Pins the contract narrated by ``unregister``'s docstring
  (``django_strawberry_framework/registry.py::TypeRegistry.unregister #"even if siblings remain"``):
  when ``type_cls`` is the primary for its model, the model loses its
  ```

#### F10 — `no_longer` process provenance in a test name

- Observation: `test_register_second_type_for_same_model_no_longer_raises_collision`
  carries "no longer", explicitly listed as process provenance: the name
  narrates the spec-018 delta (this used to raise) instead of stating the
  present-tense rule its own docstring already gives ("A second type for an
  existing model registers without raising.").
- Evidence: axis rule (REVIEW.md Comments: provenance "delete or rewrite as
  the present-tense rule"); the docstring first line is the present-tense
  form.
- Impact: minor; the name teaches history where the rule suffices.
- Severity: Low (rides on a file higher findings already change).
- Recommendation: rename to `test_register_second_type_for_same_model_does_not_raise`
  and sweep the two bare-name prose references in the same change:
  `docs/SPECS/spec-018-meta_primary-0_0_6.md:60` and
  `docs/dry/dry-rule-already-registered-error-wording.md:148` (the latter
  belongs to another flow's cycle — Worker-0 routes if untouched).
- Must not change: n/a.
- Proof: `grep -c 'no_longer_raises_collision' tests/test_registry.py` prints `0` and `grep -c 'def test_register_second_type_for_same_model_does_not_raise' tests/test_registry.py` prints `1`.
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/test_registry.py::test_register_second_type_for_same_model_no_longer_raises_collision`
- Grade: process provenance
- Text before: `def test_register_second_type_for_same_model_no_longer_raises_collision(fresh_registry):`
- Text after: `def test_register_second_type_for_same_model_does_not_raise(fresh_registry):`

#### F11 — "(separate block)" names clear()'s retired block structure

- Observation: `tests/orders/test_inputs.py::test_registry_clear_clears_helper_referenced_ordersets`
  docstring ends "(separate block)", written when `clear()` held a separate
  try/except block per cache (`git show 11d9fbe0:.../registry.py`, the
  commit that introduced the wording).
- Evidence: live `clear()` has no blocks; the helper-set clear is a
  separate registered callback (`orders.helper_references`) from the
  namespace clear (`orders.input_namespace`). The docstring's operative
  claim ("empties _helper_referenced_ordersets") is true; only the
  parenthetical is spent. Single repo-wide occurrence.
- Impact: two-word stale fragment; same family as F1/F2/F6.
- Severity: Low.
- Recommendation: "(separate callback)" (below).
- Must not change: n/a.
- Proof: `grep -c '(separate block)' tests/orders/test_inputs.py` prints `0`; the rewritten docstring grades true.
- Freshness: trace (no beyond-trace files).
- Symbol: `tests/orders/test_inputs.py::test_registry_clear_clears_helper_referenced_ordersets`
- Grade: stale
- Text before: `"""``registry.clear()`` empties ``_helper_referenced_ordersets`` (separate block)."""`
- Text after: `"""``registry.clear()`` empties ``_helper_referenced_ordersets`` (separate callback)."""`

## Rejected

- R1 — order/filter/clear-mechanism twins judged true (routed lead partly
  rejected). `test_clear_tolerates_unimportable_filter_submodules` and
  `test_clear_tolerates_unimportable_order_submodules` describe the live
  mechanism (register-at-import, replay resolved callables, the two
  best-effort `utils/inputs.py::_safe_import` lookups — verified against
  `clear_generated_input_namespace`'s factory + set-root lookups), and
  `test_unregister_tolerates_unimportable_connection_submodule` is true: the
  `except ImportError` guard genuinely lives on its path
  (`utils/imports.py::import_attr_if_importable`). Trigger: `clear()` regains
  import-time submodule lookups, or the unregister eviction stops delegating
  to the best-effort owner.
- R2 — sequencing "now"/"still"/"previously" in test prose is not project
  provenance. Hits at `tests/test_registry.py` lines 571, 1093, 1278, 1299,
  1309, 1445, 1740, 1912 and `test_clear_does_not_remove_mutation_from_previously_finalized_classes`
  all sequence steps within the test ("previously finalized" = finalized
  earlier in the test), never project history. Trigger: a wording that
  contrasts with a retired project behavior.
- R3 — spec-stem section labels kept as contract-source pointers. The
  `spec-031` / `(spec-018-meta_primary-0_0_6.md)` labels and the
  `(spec-027/028 Decision 9)` pointers name the contract source; none
  narrates change history. Trigger: a pointer that no longer names the
  contract source (retired mechanism, as in F1/F2, where the pointer goes
  with the sentence).
- R4 — `optimizer/walker.py::plan_optimizations` "(which returns the
  primary)" parenthetical judged contextual shorthand, not stale. True for
  the nested multi-type case under discussion; the three return states are
  documented at the `get()` owner. No Routed lead. Trigger: `get()` stops
  returning the primary first.
- R5 — `unregister` docstring's silence on `_enums` is not an unrecorded
  separation. `_enums` is `(model, field)`-keyed, outside the "traces of
  `type_cls`" scope the docstring enumerates; the survival reliance is
  recorded where it is used (`tests/types/test_converters.py`, "`unregister`
  skips ``_enums``", verified true). Trigger: a type-keyed map `unregister`
  skips.
- R6 — `TypeRegistry.mark_finalized` one-liner kept. Deleting it would trip
  the public-symbol-must-have-docstring rule, so the thin docstring wins over
  none. Trigger: a behavior worth stating appears on the method.
- R7 — "NOT the historical ... chain" in
  `tests/filters/test_sets.py` (two twin docstrings) judged load-bearing
  exclusion, not legacy narration: it states the collapse contract and bars
  re-introducing the `primary_for or get` chain. Trigger: the chain is
  reintroduced.
- R8 — `model_for_type`'s "walk ``model._meta.get_fields()``" purpose clause
  judged true-enough. The capability exists on the planning path
  (`walker.py::_resolve_field_map` fallback); the precise contract (None
  handling, pipeline) sits in the second paragraph. Trigger: the get_fields
  fallback is removed from `_resolve_field_map`.

## Verification (Comments)

Not a verify pass; no verification section.

Handoff: Graded the whole target (every docstring/comment true except F4,
F7, F8), the whole own test module (true except F1, F2, F3, F5, F9, F10),
and all other-test-module prose about the target's symbols (true except F6,
F11). No stale prose found in any other package module, so no Routed leads.
No Cross-axis findings. Two threads for the owning passes, neither a
finding: (1) Mechanics may note `register_type_teardown`'s post-finalize
raise is unpinned anywhere (only `test_mutators_...` uses `mark_finalized`,
and it covers five mutators; the raise itself is true by code) — F5's
"every guarded mutator" text-after relies on the true-by-code behavior.
(2) `tests/orders/test_inputs.py` is dirty with concurrent work at read;
Worker-2 must attribute F11's hunk. `review_inspect.py` orientation and the
citations JSON sit under `docs/review/temp-tests/registry/comments/`.

## Verify comments

Pass 1, static only (no workspace runs; every instrument below is a static
reader). Pass diff `docs/review/temp-tests/registry/diff/pass-1.diff` read
whole. Scratch: `docs/review/temp-tests/registry/verify-comments-1/`.
Fingerprints at verify (`git hash-object`): `registry.py` 27358cbc,
`tests/test_registry.py` 8bd9a869, `tests/orders/test_composition.py`
9414d257, `tests/orders/test_inputs.py` be8b48a3 (identical to the record's
read), `spec-018-meta_primary-0_0_6.md` 9f7c3784.

- F1 pass. `grep -c -e 'spec-030-connection_field-0_0_9' -e 'from
  \.connection import' tests/test_registry.py` prints `0`. Landed docstring
  grades true: both teardown callbacks are bound at the connection
  subsystem's import time (`connection.py` lines 1415, 1432, owners
  `connection.type_cache` / `connection.edge_class`), and `clear()` drops
  its own maps then replays resolved callbacks (no import in the body).
  Landed text improves on the proposal by naming both callbacks. `Registry
  lifecycle` paragraph kept.
- F2 pass. `grep -c -e 'spec-032 Decision 8' -e 'from \.relay import'
  tests/test_registry.py` prints `0`. Landed docstring grades true: the
  relay binding sits at `relay.py` line 100 (owner `relay.node_fields`),
  and the true positive-path sentence plus its
  `test_relay_node_field.py` citation are kept verbatim.
- F3 pass. `grep -c 'new public surface'` prints `0`;
  `grep -c '_force_unregister_after_finalize'` prints `1`. Landed comment
  grades true: every enumerated trace (types list, model index, primary
  slot, definition map, sourced pending relations, connection-cache entry)
  is confirmed in the `unregister` body/docstring, and the four named
  behaviors sit below the comment (sibling test line 1811, primary-loss
  line 1843, unknown no-op line 1898, post-finalize refusal line 1913).
- F4 pass. `grep -c 'the schema audit, the'
  django_strawberry_framework/registry.py` prints `0`; `grep -c 'so the
  schema audit does not reach into'` prints `1`. Landed docstring grades
  true (single real consumer named).
- F5 pass. `grep -c 'every mutator raises'` prints `0`; `grep -c 'every
  guarded mutator raises'` prints `1`. First line grades true against the
  `clear()` bypass the `clear()` docstring documents ("the only public
  mutator that bypasses the guard"), and stays coherent with the L1 rows:
  both added rows (`register_type_teardown`, unknown-type `unregister`)
  raise, so "every guarded mutator" holds.
- F6 pass. `grep -c 'local-import dance'
  tests/orders/test_composition.py` prints `0`. Landed
  "registered-callback replay (spec-028 Decision 9)" grades true against
  the `clear()` body; the Decision pointer is kept.
- F7 pass. `grep -c 'Atomic ``register``'` prints `0`. Landed first line
  ("Register ... as one atomic pair.") is imperative and true.
- F8 pass. `grep -c 'does NOT touch here'` prints `0`. Landed
  "everything this helper does not undo" binds the clause to the helper
  and grades true against `register`'s body (which does set
  `_primaries`).
- F9 pass with note. The gate resolves the pinpoint: `--paths
  tests/test_registry.py --substrings` reports `OK: 27 citations resolve
  (1 of them substring pinpoints)`, and the single pinpoint is
  `TypeRegistry.unregister #"even if siblings remain"` at line 1847,
  `resolved: true` (the substring sits in the `unregister` docstring,
  one source line). Citation line is 102 chars, inside the 110 grace.
  Note: the record's literal pipeline exits 1, but on its own count
  assertion, not the text: the gate yields two records per pinpoint cite
  (a `symbol` record from `CITATION_RE` plus the `substring` record from
  `SUBSTRING_RE`; see `iter_citation_records`), so `len(c)==1` cannot
  hold. Pre-fix the file held 26 citations / 0 pinpoints; post-fix 27 /
  1: the delta is exactly the new pinpoint. Proof-line correction only,
  no text change owed.
- F10 pass. `grep -c 'no_longer_raises_collision'
  tests/test_registry.py` prints `0`; `grep -c 'def
  test_register_second_type_for_same_model_does_not_raise'` prints `1`.
  Spec-018 sweep: the bare name in `spec-018-meta_primary-0_0_6.md` is
  renamed (the surrounding "no longer raises" sentence is that archived
  spec's own pre-existing prose, outside the finding). Repo-wide the old
  name survives only in `docs/dry/dry-rule-already-registered-error-wording.md`
  line 148, deliberately unswept per dispatch (Worker-0 routes it).
- F11 deferred, confirmed untouched. `git diff <ITEM_BASELINE> --
  tests/orders/test_inputs.py` is empty, the fingerprint matches the
  record's read (be8b48a3), and `grep -c '(separate block)'` still prints
  `1`. The file's `M` flag vs HEAD is the concurrent work the record
  already noted.
- L1 rows disturb no graded prose: the pass adds exactly four code lines
  (two `pytest.raises` blocks) inside
  `test_mutators_reject_calls_after_mark_finalized`; no docstring or
  comment in the file is touched by them, and both rows cohere with F5's
  "every guarded mutator" first line.
- Mechanics C1 (Comments-owned prose): `grep -c 'except ImportError'
  tests/test_registry.py` prints `1`; the survivor is the unregister
  twin's true claim (line 1743, routes through `_clear_if_importable`).
- Inverse proofs: `review_inspect.py --code-digest <ITEM_BASELINE>:<path>
  <path>` exit 0 with equal digests for `registry.py`
  (sha256:3949c414...) and `tests/orders/test_composition.py`
  (sha256:17208974...); both are prose-only. (`tests/test_registry.py`
  carries L1 code rows, so no digest is owed there.)
- Citation gates: `check_citations.py --paths tests/test_registry.py
  --substrings` exit 0, no violations; `--paths
  django_strawberry_framework/registry.py --substrings` exit 0, 1
  citation resolves. Provenance sweep over the pass diff's added lines:
  clean (no spec-/card/round/worker/legacy/no-longer/now/fix-for
  introduced).

Status: verified. Open threads: (1) F9's Proof line needs a one-token
correction (filter `kind == 'substring'` or expect two records) — record
hygiene, no text change. (2) F11 stays deferred; its file is untouched.
(3) The dry-rule F10 reference stays with Worker-0 per dispatch. No new
defects found; no text this pass wrote grades below true.
