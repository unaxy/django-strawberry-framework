# DRY review: `types/relay.py`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Target [types-relay][types-relay] at HEAD blob
`524398622354` (1035 lines). Worktree `4b2a9df59d6d`
(1067 lines) mixes one OWNED hunk with concurrent-external
hunt dirt: the owned hunk is the 8-line
`relay-node-type-stamp` reconsideration-trigger comment above
`_NODE_TYPE_HINT_ATTR` (ledger row
`types/relay.py — adopted orphan relay-node-type-stamp —
trigger comment`, matched by diff content verbatim; the
dispatch brief's `relay-node-name-decode` label for this
hunk is a mislabel — the name-decode ledger row lives at
[registry][registry]`::definition_for_graphql_name`, and no
name-decode text exists anywhere in this target's diff).
Everything else in the 16-hunk diff is the hunt's
`truth.*`/`unwrap_lazy_object` migration plus the
maintainer's `except BaseException` narrowing (16 `@@`
regions, 99+/67-), absent from the ledger and the cycle
baseline. Traced at HEAD bytes throughout (`git show
HEAD:` + `git grep HEAD`); nothing tracked touched;
target diff vs `ITEM_BASELINE=ba32b64a` is empty
(unchanged since dispatch).

The module is the Relay foundation: the post-injection
Relay predicate, `is_type_of` injection + the type-hint
honor half, interface base injection, the composite-pk
gate, the id-attr stamp/read pair, the four
`resolve_*` defaults with their async siblings, the
GlobalID strategy compute/precedence/encode/decode
cluster, and the `__func__`-identity installer. It owns
no registry, no root field, no filter: decode's Step-1
roots belong to Django (`apps.get_model`) and verified
`relay-node-name-decode` ([registry][registry]); the
stamp half belongs to verified `relay-node-type-stamp`
([root-relay][root-relay]`::_stamp_node_type`); the
typed write pipeline belongs to verified
`typed-globalid-decode` ([root-relay][root-relay]`::decode_model_global_id`;
this file's `decode_global_id` is its composed
primitive); filter validation belongs to
[filters-base][filters-base] under verified
`globalid-decode-input-hardening`; the setting snapshot
write + retry guard belong to
[types-finalizer][types-finalizer], the slot to
[registry][registry]; the strategy vocabulary +
callable validation belong to [types-base][types-base];
the record slots belong to
[types-definition][types-definition]; the queryset seed
+ visibility + coercion primitives belong to
[querysets][querysets] (open
`queryset-seed-and-model-read`, adopted); the executor
fact belongs to [execution-mode][execution-mode].

Sites found (`D` = definition, `C` = consumer, `O` =
oracle, `P` = projection). `implements_relay_node`: 1
`D` (:53) + 14 production `C` calls ([types-finalizer][types-finalizer]
:674/:690/:1002/:1039/:1384/:1454,
[filters-sets][filters-sets] `filter_for_field` :1597 +
:1669 + `filter_for_lookup` :1966 +
`_is_own_pk_under_relay_owner` :2043,
[mutations-inputs][mutations-inputs] :353 (`relation_id_scalar`)
+ :917 (`payload_object_slot`),
[mutations-resolvers][mutations-resolvers] :1240
(`coerce_lookup_id`), [registry][registry] :490
(in-function)). `decode_global_id`: 1 `D` (:686) + 2
production calls ([root-relay][root-relay] :117
(`_decode_or_graphql_error`) + :313
(`decode_model_global_id`)) + 1 re-export
([testing-relay][testing-relay] :47). `encode_typename`:
1 `D` (:481) + 2 calls (in-file closure :680,
[testing-relay][testing-relay] :109). Memberships: 2 `D`
(:442/:443) + in-file reads (:453/:465/:478/:533) +
[filters-base][filters-base] union :68 + reads :708/:710.
`_emits/_accepts` predicates: 3 `D` + finalizer `C`
(:416/:440/:475). Installers: `install_is_type_of` 1
`D` + 1 `C` ([types-base][types-base] :825);
`apply_interfaces` 1 `D` + 1 `C` (finalizer :1001) +
sole package `__bases__ =` write (:150);
`install_relay_node_resolvers` /
`install_globalid_typename_resolver` 1 `D` each + 1 `C`
each (finalizer :1004/:1005); `_validated_globalid_setting`
1 `D` + 1 `C` (finalizer :884);
`_resolve_globalid_strategy` 1 `D` + 1 `C` (in-file
:649) + 1 test-only `C`. `_NODE_TYPE_HINT_ATTR`: 1
literal (:75) + in-file honor read (:115) + root stamp
write ([root-relay][root-relay] :430). `effective_*`
writers: exactly 2 lines, both in-file (:646/:654).
`definition_for_graphql_name` sole production caller:
:803. `relay_globalid_strategy_setting` sole caller:
:378. `GlobalID.from_id` production calls: exactly 2
(:751, [filters-base][filters-base] :770).
`str.__str__` in-file: exactly 4 (:525/:749/:777/:778).
`except BaseException` in-file: exactly 3 (:116/:151/:763)
+ 7 specific arms. Upstream `_id_attr` package writes:
exactly 1 (:235). `SyncMisuseError` alias: 1 of 2
regular-module redundant aliases (this file :41,
[permissions][permissions] :135).

Oracles (all independent literals/identities, never
owner reads): [test-relay-interfaces][test-relay-interfaces]
(~126 tests: interfaces validation, composite gate +
NodeID escape, `is_type_of` inject/preserve/hostile,
suppression trio, resolver inject + `resolve_*`
contracts, strategy encode/decode, generator/required/
async-hook, `SyncMisuseError`),
[test-node-field][test-node-field] (24: bare/typed
refetch, multi-type `__typename`, stamp/poison/passthrough,
NodeID attr + coercion, guards, finalize check, async
twins, `SyncMisuseError`:651/:820),
[test-relay-connection][test-relay-connection] (63),
[test-testing-relay][test-testing-relay] (11: mint/refuse),
[test-filters-base][test-filters-base] (109: strategy
round-trips, mismatch, encode-only fail-closed, unbound
fallback), [test-types-finalizer][test-types-finalizer]
(17), [test-mutations-resolvers][test-mutations-resolvers]
(36: typed-id envelopes), [test-types-base][test-types-base]
(strategy validation + precedence :1215 import),
[test-filters-finalizer][test-filters-finalizer] (audit
rejects :1289/:1323/:1355),
[test-definition-relations][test-definition-relations]
(custom-id recognition over `_resolve_id_default`),
live [test-library-api][test-library-api]
`test_nodes_batch_mixed_types_order_and_null` (:5289)
over [library-schema][library-schema] node fields
(:1080/:1082). Projections: module + function
docstrings (verified clause-by-clause; D1 + N1 filed),
[spec-031][spec-031] Decisions 3/4/5/6/7/8/10/11/13
(titles verified present), spec-015/spec-032 pins as
cited, glossary `Relay Node integration` + 85
mentions, TREE subsystem lines, upstream
strawberry-0.324.0 bodies (`GlobalIDValueError ⊂
ValueError`, `_id_attr` inherited-cache read,
`resolve_id_attr` MRO scan, `NodeIDAnnotationError`
0/2+ arms, `resolve_typename → info.path.typename`)
and strawberry-django port anchors (`type.py:204`
`__dict__` check, `:214` + `:224` `__func__` test,
`relay/utils.py:179 map_results`, `:285
resolve_model_id_attr`).

Connected behavior examined: the finalizer Phase-2.5
loop (:992/:1009) + snapshot block (:873/:899) +
audits (:378/:424/:445/:1906/:1953), the base
producer (:825 install, :545 predicate, :376 validator,
:1113 interfaces validation, :502 marker detection,
:740 collision guard, :1928 suppression branch), the
definition record (:195/:202 strategy slots, :230
name property, :264 lookup, :374/:407/:440
recognition cluster), root
relay (:101/:148/:184/:202/:217/:232/:287/:327/:347/:369/:398/:434
+ factories), registry decode entries (:59/:462),
filter decode + accepted-set (:55/:68/:77/:638/:683/:715),
filter/test/mutation/list/conf/exceptions/querysets/
execution-mode regions named above, the walker
id-projection (:770/:800), connection edge building
(`_resolve_from_window`, upstream `Connection.resolve_node`
— N2), the six-attname census (exactly 6 production
`pk.attname` reads package-wide), the `__func__`
census, and the full importer census (11 production
importers — 9 module-top + 2 in-function — + 12 test
importers, closed above).
Excluded on body strength:
[types-converters][types-converters] (zero
relay/GlobalID hits — empty census),
[types-resolvers][types-resolvers] (1 prose mention, no
mechanism), [types-relations][types-relations] (no
relay surface), walker internals past the projection,
and every open family whose trigger vocabulary finds
no member here (matrix 1).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Read every
sibling flavor for a GlobalID/relay mirror. Mutations
(`coerce_lookup_id`), relations (`_decode_relation_id_set`
via [write-values][write-values]), forms, and DRF all
decode through the one typed primitive
(`decode_model_global_id`) — consumers, never second
definitions (verified `typed-globalid-decode`,
T-pipeline re-checked: no write `id` decode bypasses
it). Filters decode + validate through their own
audited path (verified `globalid-decode-input-hardening`,
T-compose/T-errors/T-fallback re-checked). Connection
and list fields guard targets through the one shared
guard (verified `relay-node-target-guard`,
T-lifecycle re-checked: no guard reads `DecodeResult`
statuses). Orders/auth/keyset carry no GlobalID rule
(empty census). Hostile-mapping hardening (open
family): this file reads no mappings — checked, not a
member. Upstream-name collision (`Connection.resolve_node`
vs `Node.resolve_node`): both upstream-owned, out of
population (N2). No flavor redefines a rule owned
here; every pair is a C or R row below.

**2. Sync/async twins.** The target's async surface is
exactly 2 `async def` (:900/:966), both homed in
F-NODE-DEFAULTS: each sync default branches on
`async_execution()` and returns its async sibling's
coroutine, sharing the pure `_apply_node_filter` /
`_coerce_node_ids` / `_order_nodes` decisions. Compared
by behavior with [connection][connection]'s
`_pipeline_sync`/`_pipeline_async` pair (R16: same
twin pattern — branch + two colors sharing pure
decisions — distinct rules; Strawberry's single-slot
seam forces this file's in-default branch). The
`one-sync-boundary` / `sealed-execution-queryset`
machinery is consumed transitively via
`apply_type_visibility_*` (C-TRANSITIVE, never called
by name here). No other twin exists: `decode_global_id`,
encode, installs, and gates are pure sync with no
awaitable half (verified by `async` census: 2/2
homed).

**3. Derived rather than repeated knowledge.** Every
derived fact audited: the `"pk"` literal resolves at
3 sites over 3 subjects/shapes (R12 — the
root-`__class__` vs model divergence proves distinct
rules); `pk.attname` is 1 of the standing 6 readers
(C-ATTNAME, census exact); `id_attr` derives once per
call chain (stamp → MRO-resolved read → single
`resolve_id_attr()` per default); `effective_*` is
written once and read everywhere (never re-derived —
decode/filter/audit/testing all read the stamp);
`graphql_type_name` / `label_lower` / `model` are
composed by attribute, never rebuilt; the `"custom"` /
`"callable"` classifications are produced once (:646/
:650/:654) and matched downstream by membership. No
fact is reconstructed by different means: the
`coerced_keys` twin lines and prelude shapes are twin
vocabulary (R9), the `__func__` spells are mechanism
(R5), the `str` copies are stdlib vocabulary (R4).

**4. Inverse / round-trip pairs.** Encode
(`encode_typename`) ↔ decode (`decode_global_id`):
one grammar per strategy (model-label ↔
`apps.get_model` + `registry.get`; type-name ↔
`definition_for_graphql_name`; Step-2 enforces via the
same memberships the encoder reads). Install ↔
recognition (install writes `classmethod(default)`,
definition recognizes by closed identity — R5).
Stamp ↔ honor (verified `relay-node-type-stamp`,
T-attr/T-value/T-lifecycle re-checked). Single ↔
multi coerce (`_coerce_node_ids` delegates to
`_coerce_node_id` — F-COERCE). Upstream wire
re-encode (`_encode_global_id_input`) preserves
`type_name` for the filter gate (consumer of
`relay.to_base64`, hardening D-d). `from_id` census:
exactly 2 production calls (C-HARDEN). No second
un-encode, un-stamp, or un-install exists
(sweep-clean).

**5. Contracts restated in another medium.** Per rule:
production (this file) + oracles (the suites above —
every mechanics row spells literals or asserts
identities; the `_safe_class_name` oracle imports the
name through this module's implicit passthrough —
F-MECH) + projections (docstrings verified
clause-by-clause against bodies: install phases,
`__func__`/`__dict__` discriminators, stamp
orderings, Step-0/1/2/3, audit orderings — all true
except D1's rationale and N1's shorthand; spec-031
decision titles verified present; glossary/TREE pins
verified present; upstream bodies verified). Media
counted per finding; oracles listed, never counted.

**6. Enforcement by omission.** Guards this file's
contracts require, each checked present at its owner:
composite-pk gate (:161, Phase 2.5, NodeID escape
pinned); both-declared conflict (:638, pinned);
encode-only build audit + runtime backstop
(finalizer :1906 + filter :791, pinned); routing audit
+ collapse warning (finalizer :378/:445, pinned);
unregistered-target audit (finalizer, pinned);
no-Node-types check (finalizer :1038, pinned);
`required` missing-id raise (`_order_nodes` +
`qs.get()`, pinned); per-site `except` verdicts (R1);
`SyncMisuseError` on sync/async misuse (raised
downstream by `apply_type_visibility_*` /
`async_execution`, pinned :651/:820 — correctly
not raised here). Absences correctly absent:
registered-own-definition proof (canonical by
construction — registry-sourced targets only; testing
J4 direction, no defect); suppression interplay
(model-column reads are suppression-proof by subject);
CLI mirror (no contract source — J4 direction, no
defect). No member lacks a required guard: no defect
under this axis.

### Enumeration

Instrument: `ast.parse` over HEAD bytes
(`ast.Module.body` = 47 top-level members, #0–#46)
plus full nested expansion (2 nested `def`s:
`install_is_type_of>is_type_of`,
`_install_typename_closure>resolve_typename`; no
classes, no other nesting). 49/49 homed; no member
unassigned. (`F-*` = file-local finding, `C-*` =
converge transcribing nothing, `R-*` = rejection,
`A1` = open-family adoption; all defined under
`## Findings`.)

| # | Member (HEAD line) | Home |
|---|---|---|
| 0 | Module docstring (lifecycle map, :1–21) | F-MECH (projection; N1 shorthand) |
| 1 | `from __future__ import annotations` (:23) | F-MECH |
| 2 | `from collections.abc import Callable` (:25) | F-MECH (F-INSTALL annotation) |
| 3 | `from typing import TYPE_CHECKING, Any` (:26) | F-MECH |
| 4 | `from django.apps import apps` (:28) | F-MECH (F-DECODE Step-1 root) |
| 5 | `from django.db import models` (:29) | F-MECH (F-ID/F-NODE-DEFAULTS) |
| 6 | `from django.db.models import CompositePrimaryKey` (:30) | F-MECH (F-COMPOSITE gate) |
| 7 | `from strawberry import relay` (:31) | F-MECH (Node/GlobalID vocabulary) |
| 8 | `from strawberry.relay.exceptions import NodeIDAnnotationError` (:32) | F-MECH (R6 trio verdicts) |
| 9 | `from ..exceptions import ...` (:34) | F-MECH (R1/R3 consumers) |
| 10 | `from ..utils.execution_mode import async_execution` (:35) | F-MECH (F-NODE-DEFAULTS dispatch) |
| 11 | `SyncMisuseError as SyncMisuseError` (:41) | F-MECH + C-REEXPORT |
| 12 | querysets 4-name import (:42–47) | F-MECH + A1 (seed/read) + F-NODE-DEFAULTS (visibility) |
| 13 | `TYPE_CHECKING` definition import (:49–50) | F-MECH |
| 14 | `implements_relay_node` (:53) | F-PRED (+ C-R5/R19/R20 for the pairs) |
| 15 | `_NODE_TYPE_HINT_ATTR` (:75) | F-HINT + C-STAMP |
| 16 | `install_is_type_of` (:78) + nested `is_type_of` (:113) | F-HINT (+ R7 discriminator third) |
| 17 | `apply_interfaces` (:128) | F-INTERFACES (+ R11 phase pair) |
| 18 | `_check_composite_pk_for_relay_node` (:161) | F-COMPOSITE (+ R6/R11/R22) |
| 19 | `_RELAY_ID_ATTR_SLOT` (:208) | F-IDATTR |
| 20 | `_stamp_relay_id_attr` (:211) | F-IDATTR (+ R6/R22) |
| 21 | `_resolve_id_attr_default` (:243) | F-IDATTR (+ R6) |
| 22 | `_resolve_id_default` (:279) | F-ID (+ R12/R21/C-J5) |
| 23 | `_coerce_node_id` (:311) | F-COERCE (+ R15) |
| 24 | `_coerce_node_ids` (:315) | F-COERCE |
| 25 | `_apply_node_filter` (:321) | F-COERCE |
| 26 | `_validated_globalid_setting` (:347) | F-SETTING |
| 27 | `_resolve_globalid_strategy` (:389) | F-SETTING |
| 28 | `MODEL_LABEL_STRATEGIES` (:442) | F-MEMBERSHIP (+ C-R8-STRAT) |
| 29 | `TYPE_NAME_STRATEGIES` (:443) | F-MEMBERSHIP (+ C-R8-STRAT) |
| 30 | `_emits_model_label` (:446) | F-MEMBERSHIP (+ R8) |
| 31 | `_accepts_model_label_decode` (:456) | F-MEMBERSHIP (+ R8) |
| 32 | `_accepts_type_name_decode` (:468) | F-MEMBERSHIP (+ R13) |
| 33 | `encode_typename` (:481) | F-ENCODE (+ R4/R17) |
| 34 | `_FRAMEWORK_CLOSURE_MARKER` (:548) | F-TYPENAME |
| 35 | `_inherits_framework_closure` (:551) | F-TYPENAME (+ R5) |
| 36 | `_consumer_overrode_resolve_typename` (:566) | F-TYPENAME (+ R5) |
| 37 | `install_globalid_typename_resolver` (:593) | F-TYPENAME (+ R18) |
| 38 | `_install_typename_closure` (:657) + nested `resolve_typename` (:676) | F-TYPENAME (+ R10) |
| 39 | `decode_global_id` (:686) | F-DECODE (+ C-HARDEN/C-TYPED/C-NAMEDECODE/R4/R12/R13) |
| 40 | `_order_nodes` (:827) | F-NODE-DEFAULTS (+ R9) |
| 41 | `_resolve_node_default` (:864) | F-NODE-DEFAULTS (+ R9) |
| 42 | `_resolve_node_async` (:900) | F-NODE-DEFAULTS (+ R16) |
| 43 | `_resolve_nodes_default` (:921) | F-NODE-DEFAULTS (+ R9) |
| 44 | `_resolve_nodes_async` (:966) | F-NODE-DEFAULTS (+ R16) |
| 45 | `_RELAY_RESOLVER_DEFAULTS` (:995) | F-INSTALL |
| 46 | `install_relay_node_resolvers` (:1003) | F-INSTALL (+ R5/R7/R10) |

### Challenges

Counts are authoritative definitions only;
consumers, oracles, projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Third Relay-shape spelling (new way to be Relay-shaped) | **2, one per phase** — the pre-injection disjunction ([types-base][types-base]) + this post-injection MRO check move together BY DESIGN (C-R5 timing split; each single for its phase) |
| C2 | Fifth `resolve_*` default (new upstream slot) | **1** (table row + loop install it; oracles pin the shape) → F-INSTALL |
| C3 | Consumer overrides `resolve_node(s)` | **0** (installer preserves by `__func__` identity; oracles pin preserve + install arms) → F-INSTALL |
| C4 | `is_type_of` fallback change (e.g. proxy-aware) | **1** (honor closure; stamp half + oracles follow as listed) → F-HINT |
| C5 | Second hint scheme (hypothetical) | **Fires C-STAMP T-attr** (grammar + both halves re-open; today 1 grammar, 2 directional halves) |
| C6 | Interface-injection error wording | **1** (the in-body formatter; per-subject — R3) → F-INTERFACES |
| C7 | Second composite-pk escape shape | **1** (gate; base marker detection is a different question — R22) → F-COMPOSITE |
| C8 | Stamp-slot rename | **1** (constant; stamp + read compose by name — listed) → F-IDATTR |
| C9 | `resolve_id` cache-key grammar change | **1** (the read) + 1 coupled consumer (walker projection follows — listed, R21) → F-ID |
| C10 | `node_ids=None` posture change | **1 rule in 2 colors** (sync + async arms move together — twin constraint) → F-NODE-DEFAULTS |
| C11 | Order-key shape change (non-`str` index) | **1 rule, 3 spell sites** (sync line + async line + index build — R9 twin vocabulary) → F-NODE-DEFAULTS |
| C12 | Fifth framework strategy string | **1 per direction** (vocabulary base-side; membership + encoder + decoder arms here; filter derivation filter-side — C-R8-STRAT is why no single site moves alone) |
| C13 | `callable` gains a decode path | **1 per direction** (memberships + Step-2 + filter literal + audit; R14 records the absence-vs-literal split) |
| C14 | Second setting source | **1** (`_validated_globalid_setting`; validator + reader composed — listed) → F-SETTING |
| C15 | Precedence reorder (setting beats Meta) | **1** (pure `_resolve_globalid_strategy`) → F-SETTING |
| C16 | Both-declared conflict wording | **1** (install step; per-subject — R3) → F-TYPENAME |
| C17 | Closure-marker rename | **1** (constant; both readers compose by name — listed; R5 records the per-question split) → F-TYPENAME |
| C18 | New decode failure mode | **1** (`decode_global_id`; root maps all `ConfigurationError` uniformly — no per-mode arms to add) → F-DECODE |
| C19 | Second wire shape (new parse) | **1** (decode owns the parse; fires typed T-shape if it lands outside) → F-DECODE |
| C20 | `str`-copy primitive change | **0** (stdlib vocabulary; per-site verdicts stay — R4) |
| C21 | Hint-read failure posture (raise vs fallback) | **1** (that arm alone; J1 per-site verdicts — R1) |
| C22 | Re-export spelling (`as`-alias → `__all__`) | **0 moves, breaks lint** (C-REEXPORT: either direction breaks a contract) |
| C23 | `model_for`/seed contract change | **0 here** (3 + 4 consumer calls follow; A1 family owns) |
| C24 | Required-missing exception-type change | **Inexpressible uniformly** (`qs.get()` raises Django's own — homogeneous by construction, documented) → F-NODE-DEFAULTS |
| C25 | Third production `from_id` parse | **Fires hardening census + T-shape** (today exactly 2 — C-HARDEN) |

## Findings

### F-MECH — module mechanics (file-local)

- **Contract + variation.** Module docstring maps the
  three lifecycle phases (creation `install_is_type_of`
  via `__dict__`, synthesis tuple check in base,
  Phase-2.5 trio via `__func__`) + the upstream-port
  note; 12 import statements + the `TYPE_CHECKING`
  block bind exactly the names the bodies use (every
  binding consumed — census below); no `__all__`
  (implicit surface — the `SyncMisuseError` alias +
  `_safe_*` passthrough are importable);
  `TYPE_CHECKING` definition import for annotations
  only. Varies as the map prose + import set.
- **Sites + roles.** Definition: header here (#0–#13).
  `SyncMisuseError` alias consumers:
  [types-init][types-init] :32, package root (via
  types), [permissions][permissions] (own alias —
  C-REEXPORT), 5 test importers (`filters/test_sets`,
  `test_connection`, `test_list_field`,
  `test_relay_node_field`, `types/test_relay_interfaces`
  ×2). Other suites import the same exception from
  `utils.querysets` — a separate surface, not this
  alias's consumers.
  `_safe_class_name` passthrough consumer: the
  exceptions oracle itself
  ([test-relay-interfaces][test-relay-interfaces] :28 —
  pins passthrough behavior). Cite targets: base /
  finalizer / upstream (listed, not counted).
- **Challenges.** C22 → 0 moves (either respell breaks
  a lint contract); import-set changes move here
  alone.
- **Owner + lifetime.** Here (principle 7: the header
  its bodies import through). Lifetime: module scope.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Every import's rule stays at
  its owner (R1/R3 wordings + guards, A1 seed/read,
  F-NODE-DEFAULTS dispatch, R6 verdicts); the alias
  stays a regular-module alias (C-REEXPORT).
- **Behavioral proof.** `static-reviewed` (19/19
  bindings consumed — AST code-use counts:
  Callable→7, Any→23, TYPE_CHECKING→own-guard,
  apps→1, models→3, CompositePrimaryKey→1, relay→10,
  NodeIDAnnotationError→3, ConfigurationError→14,
  `_safe_arg_repr`→6, `_safe_class_name`→4,
  `_safe_type_name`→1, async_execution→2,
  SyncMisuseError→re-export-only (0 code uses),
  model_for→3, initial_queryset→4,
  apply_sync→2, apply_async→2,
  DjangoTypeDefinition→5; map claims verified: base
  :825 install, base :1928 suppression branch,
  finalizer :1001/:1008 trio).
- **Structural gate.** None owed (cite half already
  executed by `check_citations` in CI; import half is
  load-bearing — an unused import fails lint).
- **Coupling.** None.
- **Freshness.** Target `524398622354`;
  [types-init][types-init] `1bf69028dbdc` (HEAD ==
  worktree); [root-init][root-init] `0ef72601ecac`
  (HEAD == worktree); [permissions][permissions] HEAD
  `72102cc08e19` / WT `ef66f8b9ce5c` (alias region
  :130–135 byte-identical both revisions).

### F-PRED — post-injection Relay predicate (file-local)

- **Contract + variation.** `issubclass(type_cls,
  relay.Node)` over the resolved MRO — answers
  "Relay-shaped" AFTER Phase-2.5 base injection, so it
  also catches direct `relay.Node` inheritance without
  `Meta.interfaces`. Varies as the MRO fact.
- **Sites + roles.** Definition: :53 (sole —
  `def implements_relay_node` census = 1). Consumers:
  the 14 production calls + finalizer prose (listed
  in trace). Oracles: every relay-shape row pins it
  transitively (inject/no-inject, filter GlobalID
  shaping, payload slot, coerce arms, name-decode
  relay-only scan).
- **Challenges.** C1 → 2, one per phase (the timing
  split is the contract — C-R5).
- **Owner + lifetime.** Here (principle 7: every
  consumer already imports this module; the question
  is MRO-truth at/after injection). Lifetime: pure
  per-call.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Pre-injection declaration
  reading stays in base (C-R5); the inline fail-closed
  probe stays in definition (R19); the post-finalize
  stamp read stays in testing (R20).
- **Behavioral proof.** `static-reviewed` (sole-def
  census + 14 consumer call shapes; no
  ordering/transaction/async surface).
- **Structural gate.** None owed (single 1-line body;
  a hand copy passes every oracle by construction —
  same gate-only bar as the verified items).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; finalizer
  HEAD `de34ae2aaed1`; [filters-sets][filters-sets]
  HEAD `993e887a7001`; [mutations-inputs][mutations-inputs]
  HEAD `fc4420475f40`;
  [mutations-resolvers][mutations-resolvers] HEAD
  `043a2d0bb2f6`; registry HEAD `81bd561c99cb`.

### F-HINT — type-hint grammar + `is_type_of` honor (file-local)

- **Contract + variation.** `_NODE_TYPE_HINT_ATTR`
  names the one private slot; `install_is_type_of`
  installs (at class creation, for EVERY DjangoType)
  the closure that honors a stamped hint (`is`
  identity) before the `(type_cls, model)` isinstance
  fallback, preserving a consumer-declared
  `is_type_of` via the own-`__dict__` discriminator
  and degrading a hostile hint read to the fallback.
  Varies as the slot name + honor precedence (both
  frozen — C-STAMP).
- **Sites + roles.** Grammar definition: :75 (sole
  literal — package census 1). Honor definition: :78
  + nested :113 (sole). Stamp half: root
  `_stamp_node_type` (verified split — C-STAMP).
  Installer consumer: base :825 (sole). Oracles:
  inject-for-all, preserve-declared, hostile-fallback,
  multi-type `__typename` ×2, no-poison, passthrough
  pair (all literal/pinned).
- **Challenges.** C4 → 1.
- **Owner + lifetime.** Grammar + honor here
  (principle 7, verified: every `is_type_of` reader
  already depends on this module; dependency
  direction wins — C-STAMP). Lifetime: per-instance
  hint, published at refetch on a copy, valid for the
  response, read per abstract resolution, never
  deleted.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Stamp body + copy semantics
  stay in root; the `__dict__` discriminator third
  stays distinct from the `__func__`/tuple thirds
  (R7); upstream `cast` branch stays omitted
  (documented).
- **Behavioral proof.** `static-reviewed` (this pass;
  the verified family proved failability by execution
  — mutant B fails 3 multi-type rows, mutant A proves
  no behavioral gate can pin call-unity).
- **Structural gate.** None owed (verified family's
  proved reason stands: standing oracles fail every
  behavioral divergence).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; base HEAD
  `dda91365a7e8`; root relay HEAD `c3c5aea52768`;
  [test-node-field][test-node-field] HEAD
  `2fd9e458dd41`.

### F-INTERFACES — base-class injection (file-local)

- **Contract + variation.** `apply_interfaces`
  appends `definition.interfaces` entries missing
  from the MRO to `__bases__` (idempotent under
  rerun), wrapping any assignment failure in a
  `ConfigurationError` naming the offending
  interfaces. Varies as the skip rule + message.
- **Sites + roles.** Definition: :128 (sole; sole
  package `__bases__ =` write). Consumer: finalizer
  :1001 (sole, `if definition.interfaces` arm).
  Oracles: direct-inherit no-double-injection,
  incompatible-bases message, rerun idempotence.
- **Challenges.** C6 → 1.
- **Owner + lifetime.** Here (principle 7: the
  injection mechanics beside the injection-phase
  guards it precedes). Lifetime: once per class at
  Phase 2.5 (rerun-safe by the MRO filter).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Tuple validation stays at
  creation in base (R11); the Relay gate + resolver
  injection that read the mutated MRO stay downstream
  in the same loop.
- **Behavioral proof.** `static-reviewed` (sole-write
  census + idempotence shape; no async/transactional
  surface).
- **Structural gate.** None owed (single write site;
  oracles fail a lost skip or a raw leak).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; finalizer
  HEAD `de34ae2aaed1`.

### F-COMPOSITE — composite-pk gate (file-local)

- **Contract + variation.** Relay + composite pk is
  rejected unless the class carries an explicit
  `NodeID` annotation — detected by asking
  Strawberry's scan DIRECTLY (`__func__` bypass, so
  an inherited framework default cannot swallow the
  `NodeIDAnnotationError` into `"pk"`). Varies as
  the gate + escape.
- **Sites + roles.** Definition: :161 (sole —
  `CompositePrimaryKey` gate census = 1 production
  site). Consumer: finalizer :1003 (sole). Oracles:
  composite-raise + explicit-annotation-accept
  (monkeypatched-pk pair).
- **Challenges.** C7 → 1.
- **Owner + lifetime.** Here (principle 7: beside the
  stamp the bypass exists to protect). Lifetime:
  once per Relay type at Phase 2.5.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Shape validation stays at
  creation (R11); the bypass-vs-honor split stays
  (C-R14); marker presence-classification stays in
  base (R22); target-guard T-lifecycle re-checked
  (reads annotations, never statuses — C-GUARD).
- **Behavioral proof.** `static-reviewed` (sole-gate
  census + bypass-necessity comment verified against
  the default's swallow arm :270–276).
- **Structural gate.** None owed (oracles fail a
  removed gate (accept-composite) and a removed
  bypass (reject-escape)).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; finalizer
  HEAD `de34ae2aaed1`; base HEAD `dda91365a7e8`.

### F-IDATTR — id-attr stamp + default (file-local)

- **Contract + variation.** `_stamp_relay_id_attr`
  resolves once (upstream scan over a seeded
  `_id_attr = None` blinding the inherited cache;
  `NodeIDAnnotationError` → `"pk"`) and pins the
  result in the framework slot; `_resolve_id_attr_default`
  reads the OWN-`__dict__` stamp (steady state) with
  a live-scan fallback for unstamped callers. Fixes
  order-dependent shadowing + per-row rescan. Varies
  as the slot + resolve order.
- **Sites + roles.** Slot definition: :208 (sole).
  Stamp definition: :211 (sole; sole package
  `_id_attr` write :235). Default definition: :243
  (sole). Consumers: install step 0 (sole stamp
  caller), every `resolve_id_attr()` reader (in-file
  :302/:892/:954 + walker :791 + root :138 +
  definition :428 — all read the INSTALLED default
  or upstream, never the slot directly except :270).
  Oracles: chain-shadow, per-row-scan, fallback-to-pk,
  idempotence rows.
- **Challenges.** C8 → 1 (C2/C3 cover the install
  half).
- **Owner + lifetime.** Here (principle 7: beside the
  gate it protects and the default that reads it;
  upstream stays the single scan implementation —
  no ported walk). Lifetime: stamped at Phase 2.5,
  read per `resolve_id` call, never re-stamped
  (idempotent overwrite).
- **Migration.** None — zero-edit.
- **Distinct behavior.** The scan stays upstream's
  (R22); the three direct-scan verdicts stay split
  (R6); the bypass-vs-honor split stays (C-R14).
- **Behavioral proof.** `static-reviewed` (sole-slot
  + sole-write censuses; upstream inherited-cache
  read verified at strawberry-0.324.0
  `types.py:421–423`).
- **Structural gate.** None owed (chain/shadow
  oracles fail a lost seed; scan oracles fail a
  ported walk).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; upstream
  strawberry-0.324.0 (contract anchor, unpinned
  per precedent).

### F-ID — default `resolve_id` with cache check (file-local)

- **Contract + variation.** `cls.resolve_id_attr()`
  → coerce literal `"pk"` to
  `root.__class__._meta.pk.attname` (proxy-correct
  subject) → `root.__dict__` hit avoids the ORM
  hit → `getattr` fallback. Varies as the
  subject + key + fallback order.
- **Sites + roles.** Definition: :279 (sole).
  Consumers: Strawberry's `_id` seam (upstream) +
  definition recognition (closed-identity read —
  R5). Oracles: dict-cache hit (:519), getattr
  fallback (:537), attname-contract rows (:466–:542
  region pinning the `root.__class__` subject),
  branch unit (:1357).
- **Challenges.** C9 → 1 + coupled consumer.
- **Owner + lifetime.** Here (principle 7: beside
  the attr default it calls). Lifetime: pure
  per-call.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The `"pk"`-literal trio
  stays split by subject/shape (R12); the walker
  projection stays its coupled consumer (R21); the
  mint-time stringify stays caller-side (C-J5).
- **Behavioral proof.** `static-reviewed` (key
  grammar + fallback order; the proxy clause
  verified against the installed-default call
  chain).
- **Structural gate.** None owed (cache-hit/miss
  oracles fail a dropped arm).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; definition
  HEAD `fa6c4d330e72`; walker HEAD `75f9c6b65ed1`.

### F-COERCE — node-id coerce + filter (file-local)

- **Contract + variation.** `_coerce_node_id`
  unwraps a `GlobalID` envelope to its `node_id`
  (passthrough otherwise); `_coerce_node_ids`
  maps it None-preserving over iterables (incl.
  generators); `_apply_node_filter` applies the
  color-agnostic lazy `.filter` (`{id_attr: x}` /
  `{id_attr__in: xs}` / unfiltered). The single arm
  coerces inside; the multi arm takes the caller's
  pre-coerced list (reused for order keys — N3).
  Varies as the unwrap + filter shapes.
- **Sites + roles.** Definitions: :311/:315/:321
  (sole each; no production caller outside
  :896/:917/:959/:984). Oracles: envelope unwrap,
  generator ids, `__in` shaping rows.
- **Challenges.** C10/C11 (shared halves — each
  moves once for the rule).
- **Owner + lifetime.** Here (principle 7: beside
  the four defaults that are their only callers).
  Lifetime: pure per-call; the `.filter` stays lazy.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Field-typed coercion stays
  downstream (`_coerce_pk_or_none` + the shared
  primitive — R15); the single/multi coerce
  asymmetry stays (N3 economy: one coercion per
  path).
- **Behavioral proof.** `static-reviewed` (in-file-
  only caller census + lazy-shape inspection; no
  materialization surface).
- **Structural gate.** None owed (unwrap/filter
  oracles fail a dropped arm).
- **Coupling.** None.
- **Freshness.** Target `524398622354`.

### F-SETTING — setting compute + strategy precedence (file-local)

- **Contract + variation.** `_validated_globalid_setting`
  reads the thin conf reader once and validates
  non-`None` through the shared base validator with
  setting framing; `_resolve_globalid_strategy`
  resolves Meta → setting snapshot → `"model"`
  default by pure precedence (reads no setting,
  validates nothing). Lawful convergence onto the
  `globalid-setting-snapshot` posture (record-only
  family — testing precedent): compute here, write +
  retry guard in finalizer, slot in registry.
- **Sites + roles.** Definitions: :347/:389 (sole
  each). Composed primitives: `conf.
  relay_globalid_strategy_setting` (sole caller :378),
  base `_validate_globalid_strategy` +
  `DEFAULT_GLOBALID_STRATEGY` (listed). Consumers:
  finalizer :884 (sole
  compute caller), install step (sole precedence
  caller :649), 1 test-only precedence caller.
  Oracles: precedence
  (`test_resolve_globalid_strategy_precedence`
  :1204), invalid-setting raises incl. zero-relay
  (:2340/:2380/:2406/:2418), retry-mix refusal
  (:2501), `override_settings` rows (file-scoped);
  slot invalidation owned by `registry.clear()`
  (registry/finalizer suites, listed).
- **Challenges.** C14 → 1; C15 → 1.
- **Owner + lifetime.** Compute + precedence here
  (principle 7: beside the strategy cluster that is
  their only reader). Lifetime: computed once per
  finalization; cached on the registry slot;
  invalidated by `registry.clear()` (finalizer +
  registry owned).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Snapshot write/retry/guard
  stay in finalizer; the slot + reset stay in
  registry; validation stays in base; the reader
  stays thin in conf.
- **Behavioral proof.** `static-reviewed` (sole-
  caller censuses + once-per-build ordering
  verified in the finalizer block).
- **Structural gate.** None owed (precedence +
  retry oracles fail a second read or a silent mix).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; finalizer
  HEAD `de34ae2aaed1`; registry HEAD `81bd561c99cb`;
  base HEAD `dda91365a7e8`; [conf][conf] HEAD
  `c6ad46aa3f0c`.

### F-MEMBERSHIP — strategy→shape mapping (file-local)

- **Contract + variation.** The two frozensets own
  which strategies emit/accept a model label
  (`model`, `type+model`) vs a type name (`type`,
  `type+model`); `callable`/`custom` are in neither
  (absence IS the no-decode contract — no third
  literal); the three one-line predicates name the
  read direction (emit vs model-accept vs type-
  accept). Varies as the memberships.
- **Sites + roles.** Definitions: :442/:443/:446/
  :456/:468 (sole each). Consumers: in-file encoder
  (:533) + decode Step-2 (:812–:816), finalizer
  audit/warn (:416/:440/:475), filter union :68 +
  accepted-set :708/:710. Oracles: every strategy
  round-trip/reject row reads through these
  memberships.
- **Challenges.** C12/C13 → 1 per direction.
- **Owner + lifetime.** Here (principle 7: the
  strategy cluster every consumer already imports;
  principle 2: one translation). Lifetime: import-
  time constants + pure per-call predicates.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The declared vocabulary
  stays in base (C-R8-STRAT); the filter's accepted-
  set derivation + encode-only literal stay filter-
  shaped (R13/R14); the emit/accept name split stays
  (R8).
- **Behavioral proof.** `static-reviewed` (sole-def
  census + every consumer composes by name — no
  re-typed literal package-wide: `{"model",
  "type+model"}` grep-clean outside :442).
- **Structural gate.** None owed (round-trip oracles
  fail a dropped member; the no-third-literal clause
  is grep-verifiable).
- **Coupling.** None.
- **Freshness.** Target `524398622354`;
  [filters-base][filters-base] HEAD `ba52351c2844`;
  finalizer HEAD `de34ae2aaed1`.

### F-ENCODE — per-strategy slot computation (file-local)

- **Contract + variation.** `encode_typename`
  computes the `GlobalID` type-name slot:
  model-label strategies → `label_lower`; `type` →
  `graphql_type_name`; callable → validated non-empty
  exact-`str` return (`ConfigurationError`
  otherwise; `info` deliberately withheld). Varies
  per strategy arm.
- **Sites + roles.** Definition: :481 (sole).
  Consumers: installed closure :680 (sole live
  caller) + `global_id_for` :109 (mint path — reads
  the stamp, never the setting). Oracles: per-arm
  payload rows, non-`str`/empty callable returns,
  mint/emit agreement rows.
- **Challenges.** C12 (arm moves) → 1 per arm.
- **Owner + lifetime.** Here (principle 7: the
  encode seam beside decode). Lifetime: pure
  per-call (strategy resolved at install, never
  per request).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Arity/sync validation stays
  at creation in base (R17); `str`-copy verdicts
  stay per-site (R4); setting reads stay out (the
  closure captures the resolved strategy).
- **Behavioral proof.** `static-reviewed` (sole-def
  + 2-caller census; the `(type_cls, model, root)`
  call shape verified against
  `_GLOBALID_CALLABLE_PARAMS`).
- **Structural gate.** None owed (arm oracles fail
  a dropped strategy; return oracles fail a leak).
- **Coupling.** None.
- **Freshness.** Target `524398622354`;
  [testing-relay][testing-relay] HEAD `df0dc72a1788`;
  base HEAD `dda91365a7e8`.

### F-TYPENAME — typename-resolver install (file-local)

- **Contract + variation.** Step-0 re-entrancy guard
  (recorded strategy = already processed) → override
  detection (both-declared → raise; override alone →
  record `"custom"`, install nothing) → precedence
  resolve + closure install for everything but
  plain `type` (shadow-install when inheriting a
  parent framework closure) → record the
  classification. The marker distinguishes installed
  closures from consumer overrides across the MRO.
  Varies as the steps + classification.
- **Sites + roles.** Definitions: :548/:551/:566/
  :593/:657 (sole each). Consumers: finalizer :1005
  (sole install caller); decode/filter/audit/testing
  read the recorded stamp (listed). Oracles:
  re-entrancy rerun, both-declared raise, `custom`
  record, per-strategy install/skip, shadow-install,
  marker-inheritance rows.
- **Challenges.** C16 → 1; C17 → 1 (constant).
- **Owner + lifetime.** Here (principle 7: beside
  the encoder + recorder it wires). Lifetime:
  install at Phase 2.5; classification recorded
  once (doubles as the guard); closure captures
  `(definition, strategy)` for the build.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The `__func__` per-question
  split stays (R5); closure-vs-table install spells
  stay (R10); the sentinel-vs-flag split stays
  (R18); Strawberry's `type` default stays
  unshadowed except the parent-closure case.
- **Behavioral proof.** `static-reviewed` (step
  order + guard-first shape verified against the
  finalizer loop + rerun contract).
- **Structural gate.** None owed (rerun/misclassify
  oracles fail a lost guard or marker).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; finalizer
  HEAD `de34ae2aaed1`; definition HEAD `fa6c4d330e72`.

### F-DECODE — GlobalID decode primitive (file-local)

- **Contract + variation.** Input gate (GlobalID-or-
  `str` only) → parse (`from_id`, `ValueError` →
  uniform error) → slot read + `str` checks +
  exact-`str` normalize + non-empty → Step-1 resolve
  (dot = model label via `apps.get_model` +
  `registry.get`; no dot = GraphQL name via
  `definition_for_graphql_name`) → Step-2 strategy
  permits payload shape → `(target_type, node_id)`.
  Every failure is one uniform `ConfigurationError`.
  Varies per arm (gate/parse/roots/enforce).
- **Sites + roles.** Definition: :686 (sole —
  `def decode_global_id` census = 1). Consumers:
  root :117 + :313, testing re-export (listed in
  trace). Composed primitives: upstream `from_id`,
  `apps.get_model`, `registry.get`,
  `definition_for_graphql_name` (sole production
  caller :803), `_accepts_*` (listed). Oracles:
  gate rejects, malformed/empty rejects, label +
  name resolution, primary routing, per-strategy
  permit/forbid matrix, no-strategy reject.
- **Challenges.** C18 → 1; C19 → 1; C25 (census
  guard).
- **Owner + lifetime.** Here (principle 7, verified:
  every legitimate consumer already depends on it
  — C-HARDEN/C-TYPED). Lifetime: pure per-call;
  validity key = the registry/finalizer lifecycle
  read live.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Error surfaces stay
  caller-mapped (C-TYPED/C-HARDEN); name inversion
  stays in registry (C-NAMEDECODE); the filter's
  owner-rooted validation stays filter-side
  (C-HARDEN D-a); `"pk"`-trio subjects stay split
  (R12); accepted-set derivation stays set-shaped
  (R13). Canonical-by-construction (registry-
  sourced targets need no own-definition proof —
  testing J4 direction).
- **Behavioral proof.** `static-reviewed` (this
  pass; the verified families proved the gap shape
  + taxonomy by execution).
- **Structural gate.** None owed (verified
  families' proved reasons stand: `from_id` census
  2 + triggers pin unity).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; root relay
  HEAD `c3c5aea52768`; registry HEAD `81bd561c99cb`;
  testing-relay HEAD `df0dc72a1788`.

### F-NODE-DEFAULTS — node fetch defaults (file-local)

- **Contract + variation.** `_resolve_node_default`
  (single: `qs.get()` when required, `.first()`
  otherwise) + `_resolve_nodes_default` (bulk:
  queryset for `None`, order-preserving list with
  `None` holes / `DoesNotExist` when required) +
  async siblings (await the visibility hook, then
  `aget`/`afirst` / `async for` + shared order).
  All four read `id_attr` → branch on
  `async_execution()` → visibility-scope →
  `_apply_node_filter`. The `required` missing-id
  semantic is homogeneous with `qs.get()` by
  construction (C24). Varies per terminal.
- **Sites + roles.** Definitions: :827/:864/:900/
  :921/:966 (sole each). Shared halves: F-COERCE
  trio (composed). Consumers: root refetchers
  (:491/:596/:608), upstream `GlobalID.resolve_node`
  (`n_type.resolve_node` delegation), consumer
  overrides (preserved). Oracles: visibility
  scoping, order + holes, required raises,
  generator ids, async-hook + `SyncMisuseError`
  twins, length-check + interleave rows.
- **Challenges.** C10 → 1 rule/2 colors; C11 → 1
  rule/3 spells; C24 → inexpressible (documented).
- **Owner + lifetime.** Here (principle 7: beside
  the coerce/order halves). Lifetime: per-request;
  sync branch runs inline, async branch returns an
  awaitable for the async executor.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Twin preludes + key lines
  stay twin vocabulary (R9); the pattern-vs-rule
  split vs connection stays (R16); boundary/seal
  machinery stays downstream (C-TRANSITIVE);
  connection's `resolve_node` stays upstream's
  row-mapper (N2).
- **Behavioral proof.** `static-reviewed` (branch
  shapes + shared-helper composition verified;
  twin color discipline matches the verified
  connection precedent).
- **Structural gate.** None owed (order/hole/
  required/async oracles fail a dropped arm or a
  color cross).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; root relay
  HEAD `c3c5aea52768`; querysets HEAD `3616927de2bc`;
  [execution-mode][execution-mode] `9805cdafd244`
  (HEAD == worktree).

### F-INSTALL — resolver-defaults install (file-local)

- **Contract + variation.** `_RELAY_RESOLVER_DEFAULTS`
  declares the four `(name, default)` pairs;
  `install_relay_node_resolvers` stamps the id attr
  (step 0) then installs each default wherever the
  MRO-resolved method is absent or still upstream's
  (`__func__` identity), preserving consumer
  overrides (incl. non-classmethod existings and
  `resolve_node`, which upstream does not define —
  N4). Varies as the table + install condition.
- **Sites + roles.** Definitions: :995 (sole; "appears
  nowhere else" verified: 3 hits = def + docstring
  + loop) + :1003 (sole). Consumers: finalizer
  :1004 (sole). Oracles: inject-all-four, preserve-
  override ×4, stamp-before-install, rerun safety.
- **Challenges.** C2 → 1; C3 → 0 (preserve by
  design).
- **Owner + lifetime.** Here (principle 7: the
  table its loop iterates). Lifetime: once per
  Relay type at Phase 2.5.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The `__func__` third stays
  distinct from the `__dict__`/tuple thirds (R7);
  per-attr verdicts stay per-attr (R5); the
  `setattr(classmethod(...))` spell stays stdlib
  vocabulary (R10); upstream stays the port source
  (anchors verified).
- **Behavioral proof.** `static-reviewed` (table
  totality 4/4 + condition arms verified against
  upstream `Node` surface: `resolve_node` absent
  ✓, other three present ✓).
- **Structural gate.** None owed (inject/preserve
  oracles fail a lost arm or a clobbered override).
- **Coupling.** None.
- **Freshness.** Target `524398622354`; finalizer
  HEAD `de34ae2aaed1`; upstream strawberry-0.324.0
  (contract anchor).

### A1 — `queryset-seed-and-model-read` (adoption, transcribes nothing)

This file's `model_for` ×3 (:111/:179/:850) +
`initial_queryset` ×4 (:895/:916/:957/:982) are
consumers of the open family (owner
[querysets][querysets]`::model_for`): seeds +
model reads, never re-derived (`_meta` is read off
the returned model/queryset, the field/alias rules
stay downstream). The standing row already covers
`types/relay.py` — adoption record only, no new row,
no family item. Freshness: target `524398622354`;
querysets HEAD `3616927de2bc`.

### Convergences (no new rows; triggers re-checked unfired)

- **C-STAMP** (verified `relay-node-type-stamp`).
  Attribute + honor here, stamp in root — the split
  stands at HEAD bytes: literal census still 1
  (:75), honor read still via the constant (:115),
  stamp write still via the import (root :430), no
  deleter, no second writer (whole-package sweep).
  T-attr (second scheme/rename): unfired. T-value
  (stored beyond resolving type): unfired
  (`setattr`/`is` spells byte-stable). T-lifecycle
  (stamper outside root fields): unfired (4 call
  sites, all in root refetchers). The owned trigger
  comment is present verbatim in worktree (ledger,
  attributed by content). Home: the standing family
  row + owned comment + this note.
- **C-TYPED** (verified `typed-globalid-decode`).
  This file's `decode_global_id` is still the
  composed primitive (root :313 sole typed caller
  besides :117; zero own parses in the pipeline —
  `from_id` census holds). T-pipeline (write `id`
  decode bypass): unfired (all write decoders route
  through the primitive — mutations :1245,
  write-values :151, forms/DRF prose pins).
  T-status (fifth status): unfired (4 members).
  T-shape (new wire shape): unfired (gate + parse
  unchanged). Home: the standing family row + this
  note.
- **C-HARDEN** (verified
  `globalid-decode-input-hardening`). Gate + 7 arms
  here, filter validation filter-side — the split
  stands: `from_id` production calls still exactly 2
  (:751 + filter :770), `str.__str__` still 4 here
  vs 0 in the filter gate path, error surfaces
  unchanged (`ConfigurationError` vs coded
  `GraphQLError`/mismatch). T-compose (filter via
  primary): unfired (owner-target resolution
  intact). T-errors (filter surfaces
  `ConfigurationError`): unfired. T-fallback
  (unbound path removed): unfired. Home: the
  standing family row + this note.
- **C-NAMEDECODE** (verified
  `relay-node-name-decode`). Sole production caller
  of `definition_for_graphql_name` still :803.
  T-scan (second name path): unfired. T-key (decode
  keys beyond `graphql_type_name`): unfired (Step-1
  branches unchanged). T-population (relay-only
  widens): unfired (`implements_relay_node`
  predicate intact at registry :490). Home: the
  standing family row + this note.
- **C-GUARD** (verified `relay-node-target-guard`).
  Construction-guard split stands (list-field guard
  + root wrapper + composite gate here answer
  registered/shaped/composite — never existence).
  T-lifecycle (guard reads `DecodeResult` statuses):
  unfired (`DecodeResult` named only in root relay.py
  — def + pipeline; no guard switches on statuses).
  Home: the standing family row + this note.
- **C-R5** (verified `types-base-relay-predicate-
  vs-post-injection-check`). Timing split stands:
  `_is_relay_shaped` still pre-injection
  (tuple-or-inheritance, base :556), :53 still
  post-injection MRO. Trigger (collection moves
  post-injection): unfired (install call still at
  base :825 pre-injection; finalizer loop still
  post-injection). Home: the standing row + this
  note.
- **C-R8-STRAT** (verified `types-base-strategy-
  vocabulary-vs-payload-memberships`). Vocabulary
  (base :134, 3 strings) vs memberships (:442/:443)
  vs filter derivation (union + reads) — the
  three-way split stands; `callable`/`custom` still
  in neither membership. Trigger (every strategy
  both declared and decodable): unfired. Home: the
  standing row + this note.
- **C-R14** (verified `types-definition-effective-
  read-vs-raw-scan`). Honor-install (definition
  :428 MRO-resolved read) vs bypass-install (:188
  direct `__func__` scan) — the split stands; the
  bypass comment still names the swallow it dodges
  and the default still swallows (:270–:276).
  Trigger (one read posture): unfired. Home: the
  standing row + this note.
- **C-R19** (verified `types-definition-lazy-
  imports-vs-hoisting`). No shared lazy posture:
  this file's base-cycle rationale is TRUE
  (base→relay top edge verified at base :63; a
  relay→base top edge would close it), the conf
  ride-along is colocation, and the registry-site
  rationale is separately WRONG (D1 — own comment,
  own defect; the R19 verdict on definition's sites
  is untouched). Trigger (sites share one posture):
  unfired. Home: the standing row + this note.
- **C-J5** (verified `testing-relay-mint-coercion-
  vs-row-coercions`). Mint-time caller-pk stringify
  (testing :110) vs serve-time row-attr stringify
  (:306/:308/:848/:962/:987) — the phase split
  stands. Trigger (shared node-id-stringification
  helper): unfired (no such helper; `str()` is
  stdlib vocabulary). Home: the standing row + this
  note.
- **C-ATTNAME** (verified six-`pk.attname`-readers).
  Census re-derived at HEAD: exactly 6 production
  reads (join_taxonomy :219, lateral :1143, planner
  :685, plans :901, walker :793, here :304) — six
  reasons intact (this one: proxy-correct dict-key).
  Trigger (two reasons collapse): unfired. Home:
  the standing row + this note.
- **C-REEXPORT** (verified `types-leaf-plain-
  reexport-vs-module-as-alias`). Plain re-export in
  `__init__`+`__all__` vs redundant alias in
  regular modules (:41, permissions :135) — the
  lint-contract split stands (both spellings
  F401-clean at HEAD). Trigger (lint treats both
  identically): unfired. Home: the standing row +
  this note.
- **C-TRANSITIVE** (verified `one-sync-boundary` +
  `sealed-execution-queryset`). This file never
  imports either owner by name (import census
  proves it); the async siblings consume both
  transitively via `apply_type_visibility_async`.
  Transitive consumers are not members — no census
  append owed to either verified family. Home: the
  standing rows + this note.

### R1 — `except` arms vs a shared guard (rejected)

CONVERGE with the verified shared-except-guard J1
direction on fresh evidence: 3 `BaseException` arms
with three verdicts (hint-fallback-`None` :116,
bases-wrap :151, slot-read-wrap :763) + 7 specific
arms (`NodeIDAnnotationError` ×3 with pass/`"pk"`/
`"pk"` verdicts, `KeyError` getattr-fallback :307,
`ValueError` parse-wrap :752, `LookupError`
model-wrap :790, `KeyError` DoesNotExist-wrap :855).
No two arms share scope + verdict; a driver would
need a verdict mode flag (principle 5). Trigger:
the standing J1 trigger (a guard needing the same
position-state classification), re-checked unfired.
Freshness: target `524398622354`.

### R2 — `isinstance` gates vs a shared exact gate (rejected)

CONVERGE with the verified shared-exact-type-gate
J2 direction on fresh evidence: every gate here is
subclass-tolerant by contract (`issubclass` MRO
predicate :63, `(type_cls, model)` fallback tuple
:123, composite gate :180, GlobalID envelope :312,
callable/strategy shapes :514/:533, decode input
gate :742/:748 + slot checks :768) — the opposite
mechanism from an exact-type gate, and each answers
its own boundary question. Trigger: the standing J2
trigger, re-checked unfired. Freshness: target
`524398622354`.

### R3 — error wordings vs an owned grammar (rejected)

CONVERGE with verified per-subject-rejection-
grammars on fresh evidence: 14 `ConfigurationError`
raises + 1 `DoesNotExist` raise, each naming its
own subject/remediation (interface add, composite
escape, callable return ×2, both-declared, 9 decode
arms, missing-key). Still no owned message grammar
at HEAD — unifying needs a grammar owner that does
not exist. Trigger: a message-grammar owner both
sides could read, unfired. Freshness: target
`524398622354`.

### R4 — `str` copies vs a shared helper (rejected)

CONVERGE with verified definition-R1 (per-site
verdicts) on fresh evidence: the 4 in-file
`str.__str__` copies fuse the stdlib copy with
per-boundary verdicts (encode-return :525 raise/
raise; wire-parse :749 parse-or-raise; slot keys
:777/:778 truthiness + registry-lookup keys),
against definition's 4 (raise/`None`/`None`/`True`)
and base's 1 (:1290). A helper needs a verdict flag
(principle 5); the copy step is frozen stdlib (C20
→ 0). Trigger: all uses converge on one verdict,
unfired. Freshness: target `524398622354`;
definition HEAD `fa6c4d330e72`; base HEAD
`dda91365a7e8`.

### R5 — `__func__` identity vs override detection (rejected)

CONVERGE with the verified definition-R15
mechanism-vs-question direction on fresh evidence,
extended to this file's trio: the marker-inheritance
test (:551–:563), the override test (:566–:590),
and the per-attr install test (:1030–:1034) share
the `getattr(__func__) + is` MECHANISM but answer
three questions (shadow? / consumer-authored? /
install-which?) — as do definition's closed-default
recognition and the filterset hook-ownership
detector. Same mechanism, opposite questions; a
change to marker semantics, install conditions, or
hook ownership each moves exactly its own site(s)
(C17 → 1 via the constant). Trigger: a consumer
default sharing identity with a default (R15's),
re-checked unfired (a consumer `def` is always a new
object). Home: the standing R15 row + this finding.

### R6 — upstream-scan trio verdicts (rejected)

Same-file intentional separation: the three direct
`relay.Node.resolve_id_attr.__func__` calls serve
three verdicts — gate (:188: raise-or-pass), stamp
(:237: resolve-or-`"pk"` over a seeded cache),
default fallback (:274: return-or-`"pk"`). Each
reads where the others would misread (the gate must
bypass the install the default honors — C-R14; the
stamp must seed what the others assume). Sharing the
call is sharing upstream's primitive (already
single); sharing the verdicts needs a mode flag.
Trigger: two verdicts collapse by construction.
Home: the three docstrings as-is + this finding.

### R7 — three discriminator thirds (rejected)

Same-file intentional separation, durable home the
install docstring (:1021–:1026): `__dict__`
membership (declared-on-this-class, creation phase),
`__func__` identity (overridden-vs-upstream,
finalize phase), tuple-or-inheritance (declared
shape, synthesis phase). Each runs where the others
would misread (phase + inputs differ). Trigger: two
phases merge (then those two thirds merge). Home:
the install docstring + this finding.

### R8 — emit vs accept names (rejected)

Same-file intentional separation, durable home the
membership comment (:433–:441): `_emits_model_label`
and `_accepts_model_label_decode` have identical
bodies and are still two names — read by opposite
halves of the contract (encoder + routing audit vs
decode enforcement). Unifying strands one half's
readers for zero change relief (C12 moves the SET
once either way). Trigger: encode/decode acceptance
diverge (split the set, not just the predicates).
Home: the comment + this finding.

### R9 — node-prelude twin spells (rejected)

Same-file twin vocabulary: the four defaults share
the prelude shape (read `id_attr` → color-branch →
visibility → filter) and the sync/async bulk pair
shares the `coerced_keys` line verbatim. The shared
STEPS are already shared helpers (F-COERCE); the
remaining spells are what the twin constraint
(Strawberry's single-slot seam + await boundary)
forces into each color. Extracting them owns one
line per helper (principle 11: machinery). Trigger:
Strawberry calls separate sync/async slots (then the
colors separate for real). Home: this finding.

### R10 — closure install vs table install (rejected)

Same-file intentional separation: the typename
closure install (one parameterized closure
(captures `(definition, strategy)`, stamps the
marker) while `install_relay_node_resolvers`
installs four stateless defaults from a table. The
shared `setattr(classmethod(...))` spell is stdlib
vocabulary; the payloads (captured vs shared,
marked vs plain) differ per rule. Trigger: installs
gain a shared lifecycle (guard/ordering/audit)
beyond the one-line spell. Home: this finding.

### R11 — injection/gate vs creation validation (rejected)

Fresh pair: base `_validate_interfaces` (creation-
time tuple normalization: shapes, strawberry-
interface check, helper/self/duplicate rejects) vs
`apply_interfaces` (finalize-time `__bases__`
mutation with MRO skip + wrap) vs
`_check_composite_pk_for_relay_node` (finalize-time
semantic gate). Three verbs at two phases, each
documented at both ends (base defers composite +
MRO inspection to finalize explicitly). A shape
change moves validation alone; an injection change
moves the loop alone. Trigger: validation and
injection share one phase. Home: this finding.

### R12 — `"pk"`-literal resolution trio (rejected)

Fresh triple: this file's `"pk"`→`root.__class__.
_meta.pk.attname` dict-key (:303–:304, proxy-correct
subject) vs root `_node_id_slot`'s `"pk"`→`model.
_meta.pk` Field (:140–:141, coerce/filter subject)
vs the walker projection's `"pk"`→`model._meta.pk.
attname` column (:792–:793, `.only()` subject).
Contract difference: same upstream literal, three
subjects (row class vs resolved model vs planned
model) and three shapes (key string vs Field vs
column string) for three reasons (cache-hit vs
coerce-correctness vs N+1-avoidance) — unifying on
the model mis-keys proxy rows (this file's
deliberate clause). Adjacent to verified
definition-R13 (predicate-vs-mapping) from the
resolver side. Trigger: the three subjects coincide
by construction (then those sites merge). Home:
this finding.

### R13 — accepted-set vs predicate enforcement (rejected)

Fresh pair: filter `_accepted_globalid_type_names`
(derives the SET of accepted names — needed for the
`expects X or Y` message + membership test) vs this
file's `_accepts_*` boolean enforcement (decode
Step-2 verdict). Both compose the one memberships
by name (F-MEMBERSHIP); the shapes differ because
the needs differ (names vs verdict). Sharing the
derivation strands the message; sharing the verdict
loses the names. Trigger: one accepted-shape rule
serving message + verdict. Home: this finding.

### R14 — encode-only absence vs literal (rejected)

Fresh pair: this file's no-decode contract IS the
absence of `callable`/`custom` from both memberships
(closed boolean enforcement needs no names) vs the
filter's `ENCODE_ONLY_GLOBALID_STRATEGIES` literal
(names needed for the reject message + audit
membership). Each exists for what the other cannot
express (C13 moves each for its own direction).
Trigger: a shared classification vocabulary both
derive (message names + closed memberships from one
record). Home: this finding.

### R15 — envelope unwrap vs field coercion (rejected)

Fresh pair: `_coerce_node_id(s)` (GlobalID-envelope
→ `node_id` payload, no field in scope) vs root
`_coerce_pk_or_none` (payload → field-typed Python
value via the shared `coerce_field_value_or_none`
primitive). Unwrap answers "which string"; coercion
answers "which value for this column" — sequential
stages, not two spellings (a UUID envelope unwraps
here alone; an int-column range rule moves there
alone). The rejected `field-value-coercion` family
row was checked as prior input (no artifact, no
transferring verdict). Trigger: unwrap and coerce
share one field-aware contract. Home: this finding.

### R16 — twin pattern vs connection twins (rejected)

Fresh pair recording the principle-5 contrast:
this file's branch-inside-one-slot + two colors
sharing `_apply_node_filter`/`_coerce_node_ids`/
`_order_nodes` vs connection's `_pipeline_sync`/
`_pipeline_async` sharing window/page/seal decisions.
Same twin PATTERN (branch + two colors + shared pure
decisions — both must await consumer `async def`
hooks), distinct RULES (node refetch vs edge/page
assembly) with disjoint shared sets. A shared twin
driver would parameterize over both rule sets = mode
flags. Trigger: the shared decision sets coincide.
Home: this finding (+ the standing connection-side
record).

### R17 — return check vs arity validation (rejected)

Fresh pair: `encode_typename`'s per-call
non-empty-`str` return check (serves request-time
values; documented in base as living "in the
install closure") vs base's creation-time
arity/sync-ness validation (`_validate_globalid_callable`). Different inputs
(return value vs declared callable), different
phases (request vs creation), different failures
(`ConfigurationError`-on-value vs on-shape).
Trigger: one callable contract serving declaration
+ invocation. Home: this finding.

### R18 — re-entrancy sentinel vs finalized gates (rejected)

CONVERGE with the verified per-verb finalized-gates
direction (base R10 / definition R18) on fresh
evidence: the `effective_*`-is-set step guard (6th
verb: per-step re-entry — "already processed in a
prior partial run, skip") joins the five standing
verbs (refuse-register, no-op, refuse-declare,
cache-read, refuse-mint) + CLI check; the FLAG
stays single-owned by verified
`type-registry-finalize-gate`. Trigger: the standing
trigger (one shared gate verb), re-checked unfired.
Freshness: target `524398622354`.

### R19 — predicate vs id-column probe (rejected)

CONVERGE with verified base-R6 (gate vs probe) on
fresh evidence, from this gate's side: `:53` (bare
`issubclass`, raises on hostile — a GATE over
presented classes) vs definition's inline probe
(fail-closed containment: hostile answers `True` —
a safety verdict where `True` means "elision
unsafe"). The probe cannot call this predicate
(hostile must answer, never raise); this predicate
cannot inline the probe (callers need the MRO fact,
not a safety verdict). Trigger: probe callers need
plain MRO facts (R6's), re-checked unfired. Home:
the standing R6 row + this finding.

### R20 — predicate vs stamp read (rejected)

Fresh pair adjacent to testing-J3: `:53`
(post-injection MRO-subclass fact over a presented
class) vs `global_id_for`'s stamp-`None` gate
(post-finalize recorded classification over a type
presented for minting). Different inputs, different
phases, different verdicts (shape fact vs
mintability); J3 records stamp-vs-declaration, this
records MRO-vs-stamp — the trio is pairwise split.
Trigger: a single Relay-shapedness predicate valid
at all three phases. Home: this finding.

### R21 — id-cache read vs walker projection (rejected)

Fresh pair adjacent to verified definition-R16
(guard-vs-use): this file's `__dict__`-first read
(the USE: key grammar + fallback order) vs the
walker's id-column projection (the USE-SUPPORT:
project the column so the read hits). Complementary
halves with one-way dependence (projection serves
the read; the read stays correct without it via
`getattr`). A key-grammar change moves the read
with the projection following as consumer (C9); a
projection-tuning moves the walker alone. Trigger:
one id-column rule serving read + projection. Home:
this finding.

### R22 — marker detection vs annotation scan (rejected)

Fresh pair: base's NodeID-marker detection
(presence-classification at creation: regex +
`Annotated` marker, pure boolean for the collision
guard — must NOT raise, must NOT cache) vs
Strawberry's `resolve_id_attr` scan consumed here
(attr-NAME resolution at finalize/serve: raises on
0/2+, caches `_id_attr`). The detector cannot use
the scan (raise + cache side effects break the
guard); the stamp/gate/default cannot use the
detector (presence is not a name). Trigger: one
annotation rule serving presence + resolution.
Home: this finding.

### Considered, no row (near-misses cleared with evidence)

- **N1** "relay.Node in interfaces" shorthand (module
  docstring :9–:11, `:53` docstring :58–:61) vs
  base's issubclass-per-entry rule (:1922–:1928):
  cleared — imprecise shorthand in a contrast
  clause, but the load-bearing claim (pre- vs
  post-injection timing) is exact and the precise
  contract is recorded at both owners (base comment
  + verified R5). No verdict moves.
- **N2** `Connection.resolve_node` (upstream
  row-mapper, called at connection :549/:561/:1076)
  vs `Node.resolve_node` (installed default): cleared
  — both names upstream-owned (strawberry-0.324.0
  `types.py:163` + `:688`), out of the package
  population; no package rule to consolidate.
- **N3** `_apply_node_filter` coerce asymmetry
  (single coerces inside :335, multi takes
  pre-coerced :338): cleared — deliberate economy
  (one coercion per path; the multi caller reuses
  the list for order keys); both shapes oracle-
  pinned.
- **N4** Install `existing is None` arm for
  `resolve_node`: cleared — upstream `Node` defines
  no `resolve_node` (verified absent), so the arm is
  the always-install path, correct; non-classmethod
  existings are correctly preserved as consumer-
  authored.

## Defects

- **D1** (wrong rationale prose, UNFIXED, minor,
  doc-only): `decode_global_id`'s in-function-import
  comment (:735–:739) states a module-load cycle
  that cannot exist: "`registry.py` imports
  `implements_relay_node` from this module
  in-function, and `relay.py` must not import
  `registry` at module top - the same cycle-dodge".
  An in-function import cannot close a load cycle,
  and registry's runtime import closure is
  stdlib-leaf (`exceptions`: future-import only;
  `utils/imports`: stdlib only; the `types.*` edges
  are `TYPE_CHECKING`-only) — no path leads back to
  `types.relay`, so hoisting is statically safe.
  Proof by construction: [types-base][types-base]
  already imports `registry` at module top (:58)
  beside `types.relay` (:63). Same wrong-rationale
  shape as verified definition-D2 (which this
  item's C-R19 explicitly scopes to definition's
  own sites). The comment also mispoints ("the
  cycle-dodge `_resolve_globalid_strategy` above
  documents" — the rationale block lives in
  `_validated_globalid_setting`, :369–:374).
  Contract row broken: the comment's own "must not"
  load-cycle claim (false — a later reader will
  preserve or extend a dodge that guards nothing).
  Owner:
  `django_strawberry_framework/types/relay.py::decode_global_id`
  comment (correct the rationale to weight/
  colocation, or hoist after verifying no import-
  lightness test pins the laziness — none found:
  the import-light contract covers
  `testing/__init__`, not this edge). Filed for
  normal closeout homing: the 5 lines are
  byte-identical at HEAD (:735–:739) and worktree
  (:775–:779), outside every hunt hunk (unchanged
  context of diff `@@ -739,47 +779,40 @@`). Not
  fixed inside this item (file item; zero-edit).
  Freshness: target HEAD `524398622354` / WT
  `4b2a9df59d6d`; registry HEAD `81bd561c99cb`;
  base HEAD `dda91365a7e8`.

## Pending execution

None. All behavioral proofs are `static-reviewed`
(censuses + body comparison over HEAD bytes — the
two execution-proved families this item converges
onto carry their own `execution-verified` records;
no new behavior exists that an execution could
distinguish and the cited oracles do not already
cover). No `execution-deferred` items. Sharded/PG
cells: the node-fetch defaults reach the database
only through the composed `apply_type_visibility_*`
/ `initial_queryset` / `model_for` primitives owned
elsewhere (A1/C-TRANSITIVE) — every rule THIS file
defines (predicates, installs, gates, stamps,
coercion shapes, strategy compute, encode/decode
branching, ordering) is database-free pure dispatch
+ string work; cell-specific execution would prove
the composed primitives, not these rules.
`inapplicable by construction` for this item's own
verdicts. No workspace runs were made (read-only
`git show`/`git grep` trace; no source-mutating
probe exists).

## Judgment

Single-owned Relay foundation, zero-edit: the
predicate, hint grammar + honor, injection,
composite gate, stamp/read pair, id default, coerce
+ filter trio, setting compute + precedence,
strategy memberships, encoder, typename install,
decode primitive, node-fetch twins, and resolver
install each count exactly 1 authoritative
definition, with the registry/root/filter/finalizer
halves already owned by five verified families
(all 13 of their triggers — T-attr/T-value/
T-lifecycle, T-pipeline/T-status/T-shape,
T-compose/T-errors/T-fallback, T-scan/T-key/
T-population, T-lifecycle-guard — re-checked
unfired at HEAD bytes) plus 1 open-family adoption
and 8 verified-row convergences (all transcribing
nothing). Twenty-two rejections (7 CONVERGEd onto
verified verdicts with fresh trigger checks, 15
fresh incl. 5 same-file separations) carry contract
differences + triggers. One minor wrong-rationale
defect filed for closeout homing. No consolidation,
no new family.

## Implementation (Worker-1)

No tracked changes. Item-scoped diff vs
`ITEM_BASELINE`
(`ba32b64acf7d50124b0b5767458a896c9553c726`) is
empty for `django_strawberry_framework/types/relay.py`
(verified: `git diff <baseline> -- <target>`
prints nothing — the worktree dirt predates
dispatch). Hunk attribution by content against
`git show HEAD:<path>` (16 `@@` regions, 99+/67-):
1 owned hunk (the 8-line `relay-node-type-stamp`
trigger comment, ledger-matched verbatim; the
brief's `relay-node-name-decode` label for it is a
dispatch mislabel — content governs, no stop: the
name-decode ledger row lives at `registry.py` and
no such text exists in this diff) + 15
concurrent-external hunt regions (imports,
`truth.*` migration, `unwrap_lazy_object`,
`_ID_NOT_CACHED`, `_classmethod_function`,
narrowed `except`, reworded docstrings) — all
fingerprinted, none judged, none touched. No hunk
in a path this item touches falls outside those
two homes: no stop triggered. The only new path is
this artifact (untracked, owned by this item). No
`.py` touched, so no ruff run is owed (none
expected per brief). No commit per standing rule.
HEAD unmoved (`0c0537e2`) from dispatch to writing.

## Index rows for Worker-0

| `types-relay-module-mechanics` | `django_strawberry_framework/types/relay.py` (module docstring lifecycle map + 12 import statements + `TYPE_CHECKING` block binding 19 names, all consumed + no-`__all__` implicit surface) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-post-injection-predicate` | `django_strawberry_framework/types/relay.py::implements_relay_node` (post-injection MRO `issubclass` check incl. direct inheritance) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-hint-grammar-and-honor` | `django_strawberry_framework/types/relay.py::_NODE_TYPE_HINT_ATTR` (+ `install_is_type_of` honor closure with `__dict__` preserve + hostile-fallback) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-interface-injection` | `django_strawberry_framework/types/relay.py::apply_interfaces` (MRO-skip `__bases__` append, sole package write + offending-named wrap) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-composite-pk-gate` | `django_strawberry_framework/types/relay.py::_check_composite_pk_for_relay_node` (direct-scan bypass gate with explicit-NodeID escape) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-id-attr-stamp-and-default` | `django_strawberry_framework/types/relay.py::_stamp_relay_id_attr` (+ `_RELAY_ID_ATTR_SLOT` + `_resolve_id_attr_default` own-dict read with live-scan fallback) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-id-default` | `django_strawberry_framework/types/relay.py::_resolve_id_default` (proxy-keyed `__dict__`-first read with `getattr` fallback) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-node-id-coerce-and-filter` | `django_strawberry_framework/types/relay.py::_coerce_node_id` (+ `_coerce_node_ids` None-preserving map + `_apply_node_filter` color-agnostic lazy filter) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-setting-compute-and-precedence` | `django_strawberry_framework/types/relay.py::_validated_globalid_setting` (+ pure `_resolve_globalid_strategy` Meta → snapshot → default; lawful convergence onto the record-only `globalid-setting-snapshot` posture) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-strategy-shape-memberships` | `django_strawberry_framework/types/relay.py::MODEL_LABEL_STRATEGIES` (+ `TYPE_NAME_STRATEGIES` + the three directional predicates + absence-is-no-decode clause) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-typename-encode` | `django_strawberry_framework/types/relay.py::encode_typename` (per-strategy slot computation with callable non-empty-str return check) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-typename-resolver-install` | `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver` (+ `_FRAMEWORK_CLOSURE_MARKER` + shadow/override detectors + closure installer + classification record) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-globalid-decode` | `django_strawberry_framework/types/relay.py::decode_global_id` (gate → parse → resolve-then-enforce with uniform `ConfigurationError`) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-node-fetch-defaults` | `django_strawberry_framework/types/relay.py::_resolve_node_default` (+ `_resolve_nodes_default` + both async siblings + `_order_nodes`) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-resolver-defaults-install` | `django_strawberry_framework/types/relay.py::_RELAY_RESOLVER_DEFAULTS` (+ table-driven `install_relay_node_resolvers` with step-0 stamp + `__func__`-identity preserve) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | file-local |
| `types-relay-except-arms-vs-shared-guard` | `django_strawberry_framework/types/relay.py::install_is_type_of` (rejection recorded here; CONVERGE with the verified shared-except-guard J1 direction on fresh evidence — 3 `BaseException` + 7 specific arms, no two sharing scope + verdict) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-gates-vs-shared-exact-gate` | `django_strawberry_framework/types/relay.py::implements_relay_node` (rejection recorded here; CONVERGE with the verified shared-exact-type-gate J2 direction on fresh evidence — subclass-tolerant by contract, opposite mechanism) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-wordings-vs-shared-grammar` | `django_strawberry_framework/types/relay.py::decode_global_id` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence — 14 + 1 per-subject raises, still no owned grammar at HEAD) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-str-normalize-vs-shared-helper` | `django_strawberry_framework/types/relay.py::encode_typename` (rejection recorded here; CONVERGE with verified definition-R1 on fresh evidence — 4 in-file copies fuse stdlib copy with per-boundary verdicts) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/base.py` | File `types/relay.py` | rejected |
| `types-relay-func-identity-vs-override-detection` | `django_strawberry_framework/types/relay.py::install_relay_node_resolvers` (rejection recorded here; CONVERGE with the verified definition-R15 mechanism-vs-question direction on fresh evidence — trio shares the `__func__` mechanism, answers three questions) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/types/finalizer.py` | File `types/relay.py` | rejected |
| `types-relay-scan-trio-verdicts` | `django_strawberry_framework/types/relay.py::_check_composite_pk_for_relay_node` (rejection recorded here; same-file intentional separation — gate vs stamp vs default-fallback verdicts over the one upstream scan) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-discriminator-thirds` | `django_strawberry_framework/types/relay.py::install_relay_node_resolvers` (rejection recorded here; same-file intentional separation — `__dict__` vs `__func__` vs tuple thirds at three phases; durable home the install docstring) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-emit-vs-accept-names` | `django_strawberry_framework/types/relay.py::_emits_model_label` (rejection recorded here; same-file intentional separation — identical bodies, opposite-halves readers; durable home the membership comment) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-prelude-twin-spells` | `django_strawberry_framework/types/relay.py::_resolve_nodes_default` (rejection recorded here; same-file twin vocabulary — shared steps already shared helpers; spells forced by the single-slot seam + await boundary) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-closure-install-vs-table-install` | `django_strawberry_framework/types/relay.py::_install_typename_closure` (rejection recorded here; same-file intentional separation — parameterized marked closure vs stateless table defaults over stdlib spell) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-injection-vs-creation-validation` | `django_strawberry_framework/types/relay.py::apply_interfaces` (rejection recorded here; fresh triple — tuple normalization at creation vs bases mutation + semantic gate at finalize) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/base.py` | File `types/relay.py` | rejected |
| `types-relay-pk-literal-resolution-trio` | `django_strawberry_framework/types/relay.py::_resolve_id_default` (rejection recorded here; fresh triple — dict-key vs Field vs column over three subjects; unifying mis-keys proxy rows) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/relay.py`, `django_strawberry_framework/optimizer/walker.py` | File `types/relay.py` | rejected |
| `types-relay-accepted-set-vs-predicate` | `django_strawberry_framework/types/relay.py::_accepts_type_name_decode` (rejection recorded here; fresh pair — name-set derivation for the message vs boolean enforcement over the one memberships) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/filters/base.py` | File `types/relay.py` | rejected |
| `types-relay-encode-only-absence-vs-literal` | `django_strawberry_framework/types/relay.py::MODEL_LABEL_STRATEGIES` (rejection recorded here; fresh pair — absence-is-no-decode vs message-needing literal; trigger: a shared classification vocabulary) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/filters/base.py` | File `types/relay.py` | rejected |
| `types-relay-envelope-unwrap-vs-field-coercion` | `django_strawberry_framework/types/relay.py::_coerce_node_id` (rejection recorded here; fresh pair — envelope-to-payload vs payload-to-field-value sequential stages) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/relay.py`, `django_strawberry_framework/utils/querysets.py` | File `types/relay.py` | rejected |
| `types-relay-twin-pattern-vs-connection-twins` | `django_strawberry_framework/types/relay.py::_resolve_nodes_default` (rejection recorded here; fresh pair recording the principle-5 contrast — same twin pattern, disjoint shared-decision sets) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/connection.py` | File `types/relay.py` | rejected |
| `types-relay-return-check-vs-arity-validation` | `django_strawberry_framework/types/relay.py::encode_typename` (rejection recorded here; fresh pair — per-call return check vs creation-time arity/sync-ness validation) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/base.py` | File `types/relay.py` | rejected |
| `types-relay-reentrancy-sentinel-vs-finalized-gates` | `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver` (rejection recorded here; CONVERGE with the verified per-verb finalized-gates direction on fresh evidence — recorded-strategy is the 6th verb, flag stays single-owned) | `django_strawberry_framework/types/relay.py` | File `types/relay.py` | rejected |
| `types-relay-predicate-vs-id-probe` | `django_strawberry_framework/types/relay.py::implements_relay_node` (rejection recorded here; CONVERGE with verified base-R6 on fresh evidence — bare-MRO gate vs fail-closed safety probe, neither can call the other) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/definition.py` | File `types/relay.py` | rejected |
| `types-relay-predicate-vs-stamp-read` | `django_strawberry_framework/types/relay.py::implements_relay_node` (rejection recorded here; fresh pair adjacent to testing-J3 — post-injection MRO fact vs post-finalize mintability verdict) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/testing/relay.py` | File `types/relay.py` | rejected |
| `types-relay-id-cache-read-vs-walker-projection` | `django_strawberry_framework/types/relay.py::_resolve_id_default` (rejection recorded here; fresh pair adjacent to verified definition-R16 — use vs use-support with one-way dependence) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/optimizer/walker.py` | File `types/relay.py` | rejected |
| `types-relay-marker-detection-vs-annotation-scan` | `django_strawberry_framework/types/relay.py::_stamp_relay_id_attr` (rejection recorded here; fresh pair — pure presence-classification vs raising/caching name resolution) | `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/base.py` | File `types/relay.py` | rejected |

## Families

None. No cross-file consolidation candidate: every rule
this file defines is single-sited (all counts 1, or 2-by-
design across a verified phase split), all cross-file
pairs converge onto verified families/rows (13 + 8
triggers re-checked unfired) or reject with recorded
differences + triggers, and the one open-family touch
(`queryset-seed-and-model-read`) is an adoption the
standing row already covers. No `Family ...` item for
Worker-0 to add.

## Independent verification (Worker-2)

### Own trace (pre-Findings; HEAD bytes)

Target `django_strawberry_framework/types/relay.py` at HEAD
`5243986223547af7bcab691032e1d6792655fd9d` (1035 lines;
`git show HEAD:` + `git grep HEAD` throughout). Worktree
`4b2a9df59d6dc99270e3aa8ffac397468f7eee1b` (1067 lines):
1 owned hunk (8-line `relay-node-type-stamp` trigger comment
above `_NODE_TYPE_HINT_ATTR`, ledger-matched by content; the
dispatch `relay-node-name-decode` label is a mislabel — that
trigger lives at `registry.py::definition_for_graphql_name`)
+ hunt `truth.*`/`unwrap_lazy_object` migration
(`MethodType` import, `_ID_NOT_CACHED`, `_classmethod_function`,
narrowed `except`, reworded docstrings). `ITEM_BASELINE`
`ba32b64acf7d50124b0b5767458a896c9553c726` resolves; HEAD
`0c0537e2` unmoved. Nothing tracked touched by this item;
target diff vs baseline empty. Own trace below drafted from
the HEAD target + package sweeps before opening `## Findings`;
`## Verification` read only for count comparison, homes are my own.

Instrument: `ast.Module.body` = 47 top-level members (#0 docstring
+ 12 imports + `TYPE_CHECKING` If + 27 functions (25 `def` + 2
`async def`) + 6 constants) plus 2 nested `def`
(`install_is_type_of>is_type_of` :113,
`_install_typename_closure>resolve_typename` :676). Total 49.
Top-level: #0 docstring :1, #1 `__future__` :23, #2 `Callable`
:25, #3 `TYPE_CHECKING,Any` :26, #4 `apps` :28, #5 `models` :29,
#6 `CompositePrimaryKey` :30, #7 `relay` :31, #8
`NodeIDAnnotationError` :32, #9 exceptions 4-name :34, #10
`async_execution` :35, #11 `SyncMisuseError as` :41, #12
querysets 4-name :42, #13 `TYPE_CHECKING` :49, #14
`implements_relay_node` :53, #15 `_NODE_TYPE_HINT_ATTR` :75, #16
`install_is_type_of` :78, #17 `apply_interfaces` :128, #18
`_check_composite_pk_for_relay_node` :161, #19
`_RELAY_ID_ATTR_SLOT` :208, #20 `_stamp_relay_id_attr` :211, #21
`_resolve_id_attr_default` :243, #22 `_resolve_id_default` :279,
#23 `_coerce_node_id` :311, #24 `_coerce_node_ids` :315, #25
`_apply_node_filter` :321, #26 `_validated_globalid_setting`
:347, #27 `_resolve_globalid_strategy` :389, #28
`MODEL_LABEL_STRATEGIES` :442, #29 `TYPE_NAME_STRATEGIES` :443,
#30 `_emits_model_label` :446, #31
`_accepts_model_label_decode` :456, #32
`_accepts_type_name_decode` :468, #33 `encode_typename` :481, #34
`_FRAMEWORK_CLOSURE_MARKER` :548, #35
`_inherits_framework_closure` :551, #36
`_consumer_overrode_resolve_typename` :566, #37
`install_globalid_typename_resolver` :593, #38
`_install_typename_closure` :657, #39 `decode_global_id` :686,
#40 `_order_nodes` :827, #41 `_resolve_node_default` :864, #42
`_resolve_node_async` :900, #43 `_resolve_nodes_default` :921,
#44 `_resolve_nodes_async` :966, #45 `_RELAY_RESOLVER_DEFAULTS`
:995, #46 `install_relay_node_resolvers` :1003. My count 49/49.

Sites + roles (HEAD). Definitions in target: the 27 functions +
6 constants + 2 nested closures above. Consumers of external
owners: `model_for`/`initial_queryset`/`apply_type_visibility_*`
(owner `utils/querysets.py`), `_validate_globalid_strategy` +
`DEFAULT_GLOBALID_STRATEGY` (owner `types/base.py`),
`relay_globalid_strategy_setting` (owner `conf.py`), `registry`
(owner `registry.py`), `ConfigurationError` + `_safe_*` (owner
`exceptions.py`), `async_execution` (owner
`utils/execution_mode.py`), `apps.get_model`/`CompositePrimaryKey`
(Django), `relay.Node`/`relay.GlobalID` (Strawberry). `SyncMisuseError`
is a re-export (`as`-alias) of the querysets owner. Consumers of
this target: `types/base.py::__init_subclass__`
(`install_is_type_of`), `types/finalizer.py` Phase 2.5
(`implements_relay_node`, `apply_interfaces`,
`_check_composite_pk_for_relay_node`,
`install_relay_node_resolvers`,
`install_globalid_typename_resolver`, `_emits/_accepts`,
`_validated_globalid_setting`), root `relay.py` (`decode_global_id`,
`_NODE_TYPE_HINT_ATTR` stamp side, `resolve_id_attr` reads),
`filters/base.py` + `filters/sets.py` (strategy sets,
`implements_relay_node`), `mutations/inputs.py` +
`mutations/resolvers.py` (`implements_relay_node`, typed decode via
root), `testing/relay.py` (`decode_global_id` re-export,
`encode_typename` direct call), `registry.py`
(`implements_relay_node`), `optimizer/walker.py` +
`types/definition.py` (`resolve_id_attr` reads). Oracles:
`tests/types/test_relay_interfaces.py`,
`tests/test_relay_node_field.py`,
`tests/test_relay_connection.py`, `tests/testing/test_relay.py`,
plus live `test_query` suites. Projections: module + function
docstrings, spec-015/spec-031 decision prose, glossary/TREE pins.

Matrix (my discharge). 1 Cross-flavor: swept mutations, filters,
orders, forms, rest_framework, connection, auth, keyset for
GlobalID/relay mirrors. Mutations/relations/forms/DRF decode via
root `decode_model_global_id` (consumers); filters have their own
audited decode+validate path; connection/list guard via one shared
guard; orders/auth/keyset carry no GlobalID rule. No second
definition of any rule owned here. 2 Sync/async: exactly 2
`async def` (:900/:966); each sync default branches on
`async_execution()` and returns the sibling coroutine, sharing
`_apply_node_filter`/`_coerce_node_ids`/`_order_nodes`. Pure
decisions shared, await points preserved — the correct twin shape.
`decode_global_id`, encode, installs, gates are pure sync with no
awaitable half (inapplicable by construction: no I/O, no hook
await). 3 Derived: `model_for` consumed (3 calls), never re-derived;
`pk.attname` 1 reader here among the standing population;
`id_attr` derived once per chain (stamp → read → single
`resolve_id_attr()` per default); `effective_*` written once, read
everywhere; `graphql_type_name`/`label_lower`/`model` composed by
attribute. No fact reconstructed by different means. 4 Round-trip:
encode ↔ decode share the strategy memberships; stamp (root)
↔ honor (closure) share `_NODE_TYPE_HINT_ATTR`; stamp-slot write ↔
read share `_RELAY_ID_ATTR_SLOT`; closure install ↔ override/marker
reads share `_FRAMEWORK_CLOSURE_MARKER`; `_coerce_node_ids`
delegates to `_coerce_node_id`. One grammar per pair, no second
un-encode/un-stamp/un-install (sweep-clean). 5 Media: production +
oracles (suites spell literals / assert identities) + projections
(docstrings verified clause-by-clause; spec decision titles +
glossary/TREE pins present). Oracles listed, never counted. 6
Omission: composite gate, both-declared conflict, encode-only audit
+ backstop, routing audit + collapse warning, unregistered-target
audit, no-Node-types check, `required` missing-id raise, per-site
`except` verdicts, downstream `SyncMisuseError` — each present at
its owner. No member lacks a required guard; no defect under this
axis.

Challenges + homes I would choose (counts = authoritative
definitions only). Hint-attr rename → 1 (`_NODE_TYPE_HINT_ATTR`;
stamp + honor follow by name) → file-local. `is_type_of` fallback
change → 1 (honor closure) → file-local. Interface-injection
wording → 1 (in-body formatter; per-subject) → file-local.
Composite second escape → 1 (gate; base marker detection answers a
different question) → file-local. Stamp-slot rename → 1 (constant;
stamp + read compose by name) → file-local. `resolve_id` cache-key
change → 1 (the read; walker projection is a coupled consumer, not
a second definition) → file-local. `node_ids=None` posture → 1 rule
in 2 colors (twin constraint) → file-local. Order-key shape → 1
rule, 3 spell sites (twin vocabulary: sync line + async line +
index build) → file-local. Fifth strategy string → 1 per direction
(vocabulary base-side; membership + encoder + decoder arms here;
filter derivation filter-side) → file-local here + convergences
elsewhere. `callable` decode path → 1 per direction (memberships +
Step-2 + filter literal + audit) → file-local. Second setting
source → 1 (`_validated_globalid_setting`; validator + reader
composed) → file-local. Precedence reorder → 1 (pure
`_resolve_globalid_strategy`) → file-local. Both-declared wording →
1 (install step; per-subject) → file-local. Marker rename → 1
(constant; both readers compose by name) → file-local. New decode
failure mode → 1 (`decode_global_id`; root maps uniformly) →
file-local. Second wire shape → 1 (decode owns the parse) →
file-local. `str`-copy primitive → 0 here (stdlib vocabulary fused
with per-boundary verdicts; prior definition-R1 direction) →
rejection/converge. Hint-read failure posture → 1 (that arm alone;
per-site verdicts) → rejection/converge onto J1. Re-export spelling
→ 0 moves (either direction breaks a contract) → converge. `model_for`
contract → 0 here (consumers follow; family owns) → adoption into
`queryset-seed-and-model-read` iff the standing row already covers
this file. Required-missing exception type → inexpressible uniformly
(`qs.get()` raises Django's own; homogeneous by construction) →
file-local. Third `from_id` parse → fires hardening census (today
exactly 2) → converge. Upstream-scan `__func__` trio (gate vs stamp
vs default-fallback) → 3 sites, 1 upstream scan, 3 verdicts over it
→ rejection (same-file intentional separation). `__func__` identity
trio (install vs typename-override vs marker-inherit) → 3 questions,
1 mechanism → rejection. `__dict__` vs `__func__` vs tuple thirds →
3 phases → rejection. Emit vs accept identical bodies → 2 names,
opposite-halves readers, 1 set → rejection. Closure install vs table
install → parameterized marked closure vs stateless table defaults →
rejection. Injection vs creation validation → tuple normalization at
creation vs bases mutation + semantic gate at finalize → rejection.
`pk`-literal trio (dict-key vs Field vs column) → 3 subjects →
rejection. Accepted-set derivation vs predicate enforcement → name-set
for the message vs boolean enforcement → rejection. Encode-only
absence vs literal → absence-is-no-decode vs message-needing literal
→ rejection. Envelope unwrap vs field coercion → sequential stages →
rejection. Twin pattern vs connection twins → same pattern, disjoint
shared-decision sets (principle-5 contrast) → rejection. Return check
vs arity validation → per-call check vs creation-time validation →
rejection. Re-entrancy sentinel vs finalized gates → recorded-strategy
is one more verb, flag single-owned → rejection/converge. Predicate vs
id-probe → bare-MRO gate vs fail-closed probe → rejection/converge.
Predicate vs stamp read → MRO fact vs mintability verdict →
rejection. Marker detection vs annotation scan → presence
classification vs name resolution → rejection. Fifth `resolve_*`
default → 1 (table row + loop) → file-local. Consumer override of
`resolve_node(s)` → 0 (preserved by identity) → file-local. I name no
new family; the one open-family touch adopts iff already covered;
the rest file-local or rejected with triggers at owners.

(End of pre-Findings trace.)

### Reconciliation (post-Findings; fresh checks)

Read `## Findings` (`F-MECH` through `R22`, near-misses,
`## Defects`, `## Pending execution`, `## Judgment`) after
recording the trace above. Every home I chose matches W1's:
15 file-local groups, 1 adoption, 13 convergences, 22
rejections, 0 new families. No difference in definition
counts, owners, or triggers except the one immaterial census
note below. Per-area verdicts (all re-derived at HEAD bytes
via `git show HEAD:` + `git grep HEAD`, no workspace runs):

Enumeration AGREE 49/49 member-by-member. My instrument (47
top-level + 2 nested) matches W1's; every #0-46 line pin
verified (`:53/:75/:78/:128/:161/:208/:211/:243/:279/:311/
:315/:321/:347/:389/:442/:443/:446/:456/:468/:481/:548/:551/
:566/:593/:657/:686/:827/:864/:900/:921/:966/:995/:1003` +
imports `:23-:42` + `TYPE_CHECKING` `:49` + nested `:113/:676`).
All 49 land in a file-local row, the adoption, a converge
note, or a rejection; no member unassigned. Import census
19/19 consumed (future excluded) spot-checked (`model_for` 3,
`initial_queryset` 4, `ConfigurationError` 14 raises + 1
`DoesNotExist`, `str.__str__` 4, `except BaseException` 3,
`_id_attr` write 1, `__bases__` write 1, `from_id` production
calls 2, `pk.attname` production reads 6 — all exact).

Matrix AGREE 6/6. Axis 1: sibling flavors swept; mutations/
relations/forms/DRF decode via root `decode_model_global_id`
(consumers), filters own audited path, connection/list via one
guard, orders/auth/keyset empty, hostile-mapping not a member
(no mapping reads), upstream-name collision out of population.
Axis 2: exactly 2 `async def` (`:900/:966`); sync branches on
`async_execution()` share `_apply_node_filter`/`_coerce_node_ids`/
`_order_nodes`; pure sync elsewhere inapplicable (no I/O, no
hook await). Axis 3: `model_for` consumed never re-derived;
`id_attr` once per chain; `effective_*` written once (`:646/
:654`); `graphql_type_name`/`label_lower`/`model` composed by
attribute; twin/`__func__`/`str` spells are vocabulary (R9/R5/
R4). Axis 4: encode-decode share memberships; stamp-honor share
`_NODE_TYPE_HINT_ATTR`; slot write-read share
`_RELAY_ID_ATTR_SLOT`; install-override share
`_FRAMEWORK_CLOSURE_MARKER`; `_coerce_node_ids` delegates to
`_coerce_node_id`; no second un-encode/un-stamp/un-install.
Axis 5: oracles spell literals/assert identities (never owner
reads); docstrings verified except D1+N1; spec-031 titles +
glossary/TREE + upstream bodies pinned. Axis 6: composite gate,
both-declared, encode-only audit+backstop, routing audit+warn,
unregistered-target audit, no-Node-types check, `required`
raise, per-site `except` verdicts, downstream `SyncMisuseError`
all present at owners; no gap, no defect under this axis.

Adoption AGREE. `queryset-seed-and-model-read` owner
`utils/querysets.py::model_for`; standing plan row already lists
`types/relay.py` in files-covered; this file's `model_for` x3 +
`initial_queryset` x4 are seeds/reads never re-derived.
"Transcribes nothing" correct: no new row, no family item.

Convergences AGREE 13/13 on fresh evidence (triggers re-checked
unfired by my own sweeps, not inherited). C-STAMP: literal census
1 (`:75`), 4 stamp calls all in root refetchers, T-attr/T-value/
T-lifecycle unfired; owned comment verbatim. C-TYPED: root `:117/
:313` sole callers, 4 `GlobalIDDecode` members, write decoders
route via primitive, T-pipeline/T-status/T-shape unfired.
C-HARDEN: `from_id` exactly 2, `str.__str__` 4 here vs 0 in
filter gate, surfaces unchanged, T-compose/T-errors/T-fallback
unfired. C-NAMEDECODE: sole caller `:803`, T-scan/T-key/
T-population unfired (registry `:490` predicate intact).
C-GUARD: `DecodeResult` only in root relay, T-lifecycle unfired.
C-R5: base `:556` pre-injection vs `:53` post-injection, install
at base `:825`, trigger unfired. C-R8-STRAT: base `:134` 3
strings vs memberships vs filter union, `callable`/`custom` in
neither, trigger unfired. C-R14: definition `:428` MRO read vs
`:188` bypass, swallow intact `:270-276`, trigger unfired.
C-R19: base-cycle rationale TRUE (base `:63` top edge), conf
colocation, registry rationale separately WRONG (D1), trigger
unfired. C-J5: testing `:110` mint vs `:306/:308/:848/:962/
:987` serve, trigger unfired. C-ATTNAME: exactly 6 production
reads, six reasons intact, trigger unfired. C-REEXPORT: `:41` +
permissions `:135` lint-split stands, trigger unfired.
C-TRANSITIVE: import census proves no by-name import; transitive
via `apply_type_visibility_async`, not members, no census append
owed.

Rejections AGREE 22/22 (contract difference + trigger recorded
at owner or durable same-file home). R1 CONVERGE J1 (3+7 arms,
no two share scope+verdict). R2 CONVERGE J2 (subclass-tolerant,
opposite mechanism). R3 CONVERGE per-subject grammars (14+1
per-subject raises, no grammar owner). R4 CONVERGE definition-R1
(4+4+1 copies fuse stdlib with per-boundary verdicts). R5
CONVERGE definition-R15 (trio shares mechanism, three
questions). R6 same-file verdicts (gate vs stamp vs fallback;
sharing verdicts needs mode flag). R7 thirds (`__dict__` vs
`__func__` vs tuple; home install docstring). R8 emit/accept
identical bodies, opposite readers; home membership comment;
trigger split-the-set. R9 twin vocabulary (shared steps already
helpers; trigger separate slots). R10 closure vs table (captured
+marked vs stateless; trigger shared lifecycle). R11 triple
(creation normalize vs finalize mutate+gate; trigger one phase).
R12 triple (dict-key vs Field vs column; three subjects; trigger
coincide; proxy mis-key proved). R13 set-vs-verdict (names for
message vs boolean; trigger one rule). R14 absence-vs-literal
(closed boolean vs message names; trigger shared vocabulary).
R15 unwrap-vs-coerce (sequential stages; prior rejected row
checked, no verdict transfer). R16 twin-pattern vs connection
(principle-5 contrast, disjoint sets; trigger coincide). R17
return-vs-arity (per-call vs creation; trigger one contract).
R18 CONVERGE finalized-gates (6th verb, flag single-owned).
R19 CONVERGE base-R6 (gate raises vs probe fail-closed; neither
can call other). R20 MRO-vs-stamp (phases differ; trio pairwise
split). R21 use-vs-support (one-way dependence; trigger one
rule). R22 presence-vs-resolution (must-not-raise/cache vs
raises/caches; trigger one rule). All triggers unfired at HEAD.

D1 ENDORSED as filed (minor doc-only, clean-line homing).
Wrong-rationale prose verified: in-function import cannot close a
load cycle; registry closure stdlib-leaf (exceptions future-only,
utils/imports stdlib-only, types.* `TYPE_CHECKING`-only);
base `:58` already imports registry at top beside relay `:63`
(proof by construction); mispoint verified (rationale lives in
`_validated_globalid_setting` `:369-374`, not
`_resolve_globalid_strategy`). Contract row broken (comment's own
"must not"), feasible shape (later reader preserves/extends a
dodge guarding nothing), reaching actor (maintainer reading
prose; no wire input reaches docs — minor per precedent, filed
for normal closeout homing, not a blocker). Clean lines verified
byte-identical HEAD `:735-739` vs worktree `:775-779`, unchanged
context of `@@ -739,47 +779,40 @@`. Owner
`types/relay.py::decode_global_id` comment correct; import-light
scope note correct (covers `testing/__init__`, not this edge).
Same-shape-as-definition-D2 scoping correct via C-R19.

Index rows AGREE 37/37 (15 file-local + 22 rejections; 0 named,
1 adoption + 13 convergences transcribing nothing; no Families
items). Each row's owner/files/status matches its finding;
fidelity exact (row texts match finding contracts; no verbatim
drift). No literal-row gap (adoption + converges correctly
row-less).

Freshness AGREE. Re-derived digit-for-digit: target `52439862`;
finalizer `de34ae2a`, base `dda91365`, root `c3c5aea5`, registry
`81bd561c`, conf `c6ad46aa`, filters-base `ba52351c`,
filters-sets `993e887a`, mutations-inputs `fc442047`,
mutations-resolvers `043a2d0b`, definition `fa6c4d33`, walker
`75f9c6b6`, querysets `3616927d`, execution-mode `9805cdaf`,
testing-relay `df0dc72a`, types-init `1bf69028`, root-init
`0ef72601`, permissions HEAD `72102cc0`/WT `ef66f8b9` (alias
region byte-identical). Exclusions (converters zero hits,
resolvers 1 prose mention, relations no surface) recorded.
Pending-None correct: all `static-reviewed` (censuses + body
comparison); converged execution-proved families carry their own
records; sharded/PG `inapplicable by construction` endorsed
(rules defined here are DB-free dispatch + string work; DB reach
only via composed A1/C-TRANSITIVE primitives owned elsewhere).

Window attribution AGREE hunk-by-hunk. `ITEM_BASELINE`
`ba32b64a` resolves; target diff vs baseline empty (0 lines);
HEAD `0c0537e2` unmoved. Owned hunk (8-line
`relay-node-type-stamp` trigger comment) matches the ledger row
by content (`types/relay.py — adopted orphan
relay-node-type-stamp — trigger comment`); dispatch
`relay-node-name-decode` label is a mislabel (that trigger lives
at `registry.py`), content governs, no stop. Plan diff is
Worker-0's own dispatch record (concurrent, out of scope).
`review-0_0_15.md` diff is review-flow (error_policy verified/
closed + exceptions reviewing + routed findings + drift line for
this artifact) — concurrent. `test_error_policy_api.py` +
`test_error_policy.py` diffs are review-flow test prose (11
findings, comments/docstrings + 1 key-set assertion; target
untouched) — concurrent. Artifact is the only new path, owned by
this item. No hunk in a touched path falls outside owned +
concurrent homes: no stop. Zero `.py` touched by the item, so no
ruff run owed (confirmed; the 2 window `.py` are concurrent, not
item's). Artifact prose rules pass: `path:NN` allowed in
`docs/dry/dry-*.md`; reference-style links only with all 10
canonical groups present; no process provenance; no new links
added by this section.

Immaterial record note I1 (verdicts stand, no home/count/gate
moves): F-PRED consumer census reads "14 production calls" with
finalizer pins `:674/:690/:1002/:1039/:1384/:1454`, but HEAD has
16 calls (finalizer `:1384/:1385` prev+new decision pair and
`:1454/:1457` message pair; W1's pins collapse each pair to one
line). `:1385` is a decision consumer (missed); `:1457` is
message rendering (projection, correctly excludable from
consumers but still a call). Definition count stays 1, home
stays file-local, no gate moves. Not filed as a defect.

No Worker-2 defects. No pending execution. Nothing-else-changed
(this section + Status only). No workspace runs (read-only `git
show`/`git grep` trace). No commit per standing rule.

Verdict: verified (zero-edit; 49/49 homed; 15 file-local, 1
adoption + 13 convergences transcribing nothing, 22 rejections;
D1 minor doc-only correctly filed for normal closeout homing).

## Scoped re-trace (run 8) — Worker 1

Scoped run: `0.0.15 2026-09-30-8` (queue s14). HEAD
`83998e08` at start, verified unmoved at finish (`git
rev-parse HEAD` both times). Prior text above is prior
evidence only and stands untouched; this section appends.
Zero production edits; a file item owes none. Every claim
below is traced at HEAD bytes unless marked worktree or
pre-merge; the worktree is read only for hunk attribution.
Read-only probes, `/tmp`-only, no Django import, no DB, no
source mutation, no pytest: `/tmp/s14_probe.py` (118 checks
— `ALL OK`) + `/tmp/s14_probe2.py` … `/tmp/s14_probe5.py`
(discovery/adjudication) + one strawberry-only runtime
check, all executed via `workspace.py run
dry/relay-retrace-s14/consolidate`. Nine first-draft
expectations failed on probe precision (unsorted-list
compare, overlapping substring counts, comment-literal and
docstring trips, `git grep <rev>` prefix parsing,
wrong-file/module lookups, one `ast.dump` misuse), all
corrected in the instrument; two coarse checks surfaced
real corrections (N4, the `from_id` prose) adjudicated
below. None a finding. Package-wide censuses use the
directory pathspec (`git grep … HEAD --
django_strawberry_framework`).

### Scope of the delta (drift base → HEAD → worktree → pre-merge)

Drift base `0c0537e2` (target blob `52439862`, 1035 lines
— the run-7 bytes) → HEAD `83998e08` (blob `968fb95a`,
1128 lines) on the target is 6 commits: 2
behavior-bearing + 4 typing-only.

- `2935e0e4` (86+/23- here; 60+/- in [root-relay][root-relay],
  +176 in [test-node-field][test-node-field]): the
  node/nodes resolve seams take the decoded `node_id`
  STRING per Strawberry's `node_id: str` contract (anchor
  re-derived: upstream `Node.resolve_node(cls, node_id:
  str, *, info)` at `relay/types.py:590`, runtime-
  confirmed). `_coerce_node_ids` deleted; new
  `_node_value_or_none` / `_node_values` /
  `_raise_if_required` (coerce through the composed
  `relay.py::_coerce_pk_or_none` rule; required-miss
  raises); the single-filter arm no longer coerces
  inside; `_order_nodes` keys go `list[str | None]` with
  `None` arms; all four defaults coerce first and answer
  no-row ids pre-query. 3 new oracles (string-seam pin,
  `007`-spelling fix, `abc`-uncoercible fix — names under
  O01).
- `b63df99d` (18+/14- here + 1 line in
  `LIFECYCLE.html`): the id filter splits into
  `_apply_node_filter(qs, id_attr, value)` /
  `_apply_nodes_filter(qs, id_attr, values)`, both
  required-positional; the unfiltered fall-through is
  deleted (it was fail-open: a `None` id reached
  `.first()` over the whole visible queryset).

The 4 typing commits are proved inert two ways.
Full-diff read, every hunk: annotations (`TypeGuard`,
`type[DjangoType]`, `type[relay.Node]`, `object`,
`Info`, `AwaitableOrValue`, `GlobalIDStrategy`,
`Iterable`, `gid: object`), `cast()` (runtime identity),
`# type: ignore` / `# mypy:` comments, import widening,
the TYPE_CHECKING-only `_RelayDjangoType` class,
`_ModelT`, bare local annotations (`type_name: object`),
and `fef11e64`'s cast/ignore removals. Mechanical
screen: normalized whole-module AST equality across
each commit (annotations, docstrings, comments,
TYPE_CHECKING, imports stripped; `cast()` transparent;
`AnnAssign` → `Assign`; TypeVar dropped) —
`normalized-equal=True` for all four (T999/Tb202/Tdfb/
Tfef). Per-symbol screen base→HEAD under the same
normalizer: changed exactly the 6 behavior defs
(`_apply_node_filter`, `_order_nodes`, the 4 resolve
defaults), added exactly the 4 new helpers, removed
exactly `_coerce_node_ids`; `decode_global_id`
normalized-identical (D04); `_RELAY_RESOLVER_DEFAULTS`
identical (D05); every other def and constant
identical.

HEAD → worktree is 20 hunks, 129+/75-, blob `6c2e8c20`
(1182 lines). Attribution by content against `git show
HEAD:` (full diff read): NO owned hunk — the dispatch
states no owned ledger hunk names this file, so all 20
are concurrent-external, untouched, never judged: the
`utils/truth.py` migration (imports, `truth.*` renders,
`set_bases`, `TypeError` narrowing, `truth.text`),
`unwrap_lazy_object`, `_ID_NOT_CACHED` + namespace
reads, `_classmethod_function` + its 3 call sites,
`slot=` threading (new `_node_value_or_none` param,
`_node_values` precompute + in-function `_node_id_slot`
import, `ModelField` import), and docstring/comment
rewords. The 8-line `relay-node-type-stamp` trigger
paragraph (hunk 04) is content-identical to the run-7
owned text and byte-identical PRE↔WT (9 lines), but it
rides the pre-merge tree side only (HEAD count 0 — the
merge took main's side which lacks it): concurrent by
the dispatch rule, not owned. The 4 new HEAD helpers
are all present in WT (F02); `_coerce_node_ids` is
absent (F03); the D1 comment is identical HEAD↔WT
(F04).

Pre-merge `9aaaad5d`: target blob `4b2a9df5` (1067
lines — the run-7 worktree bytes), read for
fingerprints + trigger identity only.
`ITEM_BASELINE=2ac2ee55…` (WIP stash on `83998e08` at
dispatch): target diff vs baseline is EMPTY (0 bytes,
G02) — the target is unchanged since dispatch.

### Enumeration (fresh instrument at HEAD bytes)

Instrument: `ast.parse` over `git show HEAD:` bytes:
**51 top-level statements** — 1 module docstring, 12
`ImportFrom`, 1 `TYPE_CHECKING` guard, 6 `Assign`, 28
`FunctionDef`, 2 `AsyncFunctionDef`, 1 `AnnAssign` —
plus 2 nested `def` (`install_is_type_of>is_type_of`
:127, `_install_typename_closure>resolve_typename`
:756). **53/53 homed; no member unassigned.** Delta vs
run-7's 49 is exactly +5/−1, order kept (E04–E06):
added `_ModelT`, `_node_value_or_none`,
`_raise_if_required`, `_node_values`,
`_apply_nodes_filter`; removed `_coerce_node_ids`.
(`F-*` = file-local, `C-*` = converge transcribing
nothing, `R-*` = rejection, `A1` = adoption; `N4`/`N5`
notes; all under Findings.)

| # | Member (HEAD line) | Home |
|---|---|---|
| 0 | Module docstring (:1–21, byte-identical to base) | F-MECH (N1) |
| 1 | `from __future__ import annotations` (:23) | F-MECH |
| 2 | `from collections.abc import Callable, Iterable` (:25) | F-MECH |
| 3 | `from typing import TYPE_CHECKING, TypeGuard, TypeVar, cast` (:26) | F-MECH |
| 4 | `from django.apps import apps` (:28) | F-MECH (F-DECODE Step-1) |
| 5 | `from django.db import models` (:29) | F-MECH |
| 6 | `from django.db.models import CompositePrimaryKey` (:30) | F-MECH (F-COMPOSITE) |
| 7 | `from strawberry import relay` (:31) | F-MECH |
| 8 | `from strawberry.relay.exceptions import NodeIDAnnotationError` (:32) | F-MECH (R6) |
| 9 | `from ..exceptions import ...` (:34) | F-MECH (R1/R3) |
| 10 | `from ..utils.execution_mode import async_execution` (:35) | F-MECH (F-NODE-DEFAULTS) |
| 11 | `SyncMisuseError as SyncMisuseError` (:41) | F-MECH + C-REEXPORT |
| 12 | querysets 4-name import (:42–47) | F-MECH + A1 + F-NODE-DEFAULTS |
| 13 | `TYPE_CHECKING` block (:49–61, +`_RelayDjangoType`) | F-MECH |
| 14 | `_ModelT` (:64) | F-MECH (typing) |
| 15 | `implements_relay_node` (:67) | F-PRED (+R23) |
| 16 | `_NODE_TYPE_HINT_ATTR` (:89) | F-HINT + C-STAMP |
| 17 | `install_is_type_of` (:92) + nested `:127` | F-HINT (+R7) |
| 18 | `apply_interfaces` (:142) | F-INTERFACES (+R11) |
| 19 | `_check_composite_pk_for_relay_node` (:175) | F-COMPOSITE (+R6/R11/R22) |
| 20 | `_RELAY_ID_ATTR_SLOT` (:223) | F-IDATTR |
| 21 | `_stamp_relay_id_attr` (:226) | F-IDATTR (+R6/R22) |
| 22 | `_resolve_id_attr_default` (:259) | F-IDATTR (+R6) |
| 23 | `_resolve_id_default` (:297) | F-ID (+R12/R21/C-J5) |
| 24 | `_coerce_node_id` (:334) | F-COERCE (+R15) |
| 25 | `_node_value_or_none` (:338) | F-COERCE (+F2 nomination) |
| 26 | `_raise_if_required` (:360) | F-NODE-DEFAULTS (+R3) |
| 27 | `_node_values` (:382) | F-COERCE |
| 28 | `_apply_node_filter` (:398) | F-COERCE |
| 29 | `_apply_nodes_filter` (:413) | F-COERCE |
| 30 | `_validated_globalid_setting` (:427) | F-SETTING |
| 31 | `_resolve_globalid_strategy` (:469) | F-SETTING |
| 32 | `MODEL_LABEL_STRATEGIES` (:522) | F-MEMBERSHIP (+C-R8-STRAT) |
| 33 | `TYPE_NAME_STRATEGIES` (:523) | F-MEMBERSHIP (+C-R8-STRAT) |
| 34 | `_emits_model_label` (:526) | F-MEMBERSHIP (+R8) |
| 35 | `_accepts_model_label_decode` (:536) | F-MEMBERSHIP (+R8) |
| 36 | `_accepts_type_name_decode` (:548) | F-MEMBERSHIP (+R13, N5) |
| 37 | `encode_typename` (:561) | F-ENCODE (+R4/R17) |
| 38 | `_FRAMEWORK_CLOSURE_MARKER` (:628) | F-TYPENAME |
| 39 | `_inherits_framework_closure` (:631) | F-TYPENAME (+R5) |
| 40 | `_consumer_overrode_resolve_typename` (:646) | F-TYPENAME (+R5) |
| 41 | `install_globalid_typename_resolver` (:673) | F-TYPENAME (+R18) |
| 42 | `_install_typename_closure` (:737) + nested `:756` | F-TYPENAME (+R10) |
| 43 | `decode_global_id` (:767) | F-DECODE (+C-HARDEN/C-TYPED/C-NAMEDECODE/R4/R12/R13/D1) |
| 44 | `_order_nodes` (:911) | F-NODE-DEFAULTS (+R9) |
| 45 | `_resolve_node_default` (:949) | F-NODE-DEFAULTS (+R9) |
| 46 | `_resolve_node_async` (:989) | F-NODE-DEFAULTS (+R16) |
| 47 | `_resolve_nodes_default` (:1014) | F-NODE-DEFAULTS (+R9) |
| 48 | `_resolve_nodes_async` (:1059) | F-NODE-DEFAULTS (+R16) |
| 49 | `_RELAY_RESOLVER_DEFAULTS` (:1088) | F-INSTALL |
| 50 | `install_relay_node_resolvers` (:1096) | F-INSTALL (+R5/R7/R10; N4 corrected) |

### Matrix re-discharge (at HEAD bytes)

**1. Cross-flavor policy mirroring — CONFIRM.**
Mutations/relations/forms/DRF still decode through the
one typed primitive (consumers — s4 T-pipeline +
F7 re-verified; this file's `decode_global_id` is
normalized-identical, D04). Filters keep their audited
path (C-HARDEN split stands: `from_id` code-calls
exactly 2, P05). Connection/list guard via the one
shared guard (C-GUARD: `DecodeResult` relay-only, 8
hits). Orders/auth/keyset carry no GlobalID rule
(empty census, re-run). Hostile-mapping hardening
(open family): at HEAD bytes this file has
hostile-*descriptor* verdicts (R1 arms :130/:845) but
no hostile-*mapping* reads — the namespace-subclass
hardening is worktree-only (truth migration),
unjudged; not a member. Upstream-name collision
(`Connection.resolve_node` :584/:596/:1116 vs
`Node.resolve_node` :590): both upstream-owned, out of
population (N2 re-pinned). No flavor redefines a rule
owned here; the walker MRO conjunct is R23 (new).

**2. Sync/async twins — REVISE (shapes re-derived,
verdict stands).** Still exactly 2 `async def`
(:989/:1059, C17). Each sync default branches on
`async_execution()` (:979/:1048) and returns its
sibling's coroutine; the shared pure decisions are now
`_node_value_or_none`/`_node_values`/
`_apply_node(s)_filter`/`_order_nodes` (the single
async sibling takes the pre-coerced `value` by
parameter :993 — colorless handoff, computed once).
`decode_global_id`, encode, installs, gates, and the
new coerce helpers are pure sync with no awaitable
half (inapplicable: no I/O, no hook await). Twin
pattern-vs-connection contrast stands (R16; s1
verified).

**3. Derived rather than repeated knowledge —
REVISE (counts, verdict stands).** `model_for`
consumed 4× (A1; never re-derived);
`initial_queryset` 6× (bulk arms doubled by the
early-return split); `pk.attname` 1 code read here
(:327) among the standing 6 files (C-ATTNAME);
`id_attr` once per chain (seam read per default);
`effective_*` written once (:726/:734), read
everywhere; `graphql_type_name`/`label_lower`/`model`
composed by attribute; `callable`/`custom`
classifications produced once (:726/:730/:734).
`coerced_keys` twin lines, `__func__` spells, `str`
copies are twin vocabulary/mechanism (R9/R5/R4).

**4. Inverse / round-trip pairs — REVISE (coerce
half reshaped, verdict stands).** Encode ↔ decode
share the memberships (bodies identical modulo
annotations). Install ↔ recognition (closed identity
[types-definition][types-definition] :484 — R5).
Stamp ↔ honor (C-STAMP). Single ↔ multi coerce now
reads `_node_value_or_none` ← `_node_values`
(delegates by call :391 — the multi/single economy
moved into the shared helper; N3 retired). Wire
re-encode preserves `type_name` (consumer, D-d
unchanged). No second un-encode/un-stamp/un-install
(sweep-clean).

**5. Contracts restated in another medium — REVISE
(oracle set grew + record notes, verdict stands).**
Production + oracles (every mechanics row spells
literals or asserts identities; node-field suite 26
fns = 23 + the 3 string-seam pins O01; precedence
[test-types-base][test-types-base] :1204; live rows)
+ projections (docstrings verified clause-by-clause:
install phases, discriminators, stamp orderings,
Step-0/1/2/3, audit orderings, the new helpers'
docstrings — all true except D1's rationale, N1's
shorthand, and N5's loose verb; spec-031 Decisions
3/4/5/6/7/8/10/11/13 present O04; glossary O05;
LIFECYCLE names both filters O06; upstream bodies
re-pinned incl. `GlobalIDValueError` at
`relay/types.py:70` and the `:590` seam). N4
corrected (upstream presence, not a medium restatement
— no production docstring made the absent claim, U07).

**6. Enforcement by omission — CONFIRM.** Composite
gate (:175), both-declared conflict (:720),
encode-only build audit + runtime backstop
([types-finalizer][types-finalizer] + [filters-base][filters-base] :858),
routing audit + collapse warning (:428/:452/:487),
unregistered-target audit (:425), no-Node-types check
(:1059), `required` missing-id raises (3 homogeneous
sites :377/:941/`qs.get()`), per-site `except`
verdicts (R1), downstream `SyncMisuseError` (s4
pinned) — each present at its owner. Absences
correctly absent (canonical-by-construction,
suppression-proof model-column reads, no CLI
contract). No defect under this axis.

### Challenges (definition counts at HEAD)

Authoritative definitions only; consumers, oracles,
projections listed, not counted. All counts
probe-verified (`execution-verified` read-only);
oracle/spec bodies `static-reviewed`.

| # | Change posited | Definitions forced | Home |
|---|---|---|---|
| C1 | Third Relay-shape spelling | **3 spellings**: base disjunction + predicate + walker conjunct (R23-separated by dependency; C-R5 covers the phase split) | F-PRED REVISE |
| C2 | Fifth `resolve_*` default | **1** (table row + loop) | F-INSTALL CONFIRM |
| C3 | Consumer overrides `resolve_node(s)` | **0** (preserved by `__func__` identity, uniform across all four) | F-INSTALL CONFIRM |
| C4 | `is_type_of` fallback change | **1** (honor closure) | F-HINT CONFIRM |
| C5 | Second hint scheme | **Fires C-STAMP T-attr** (1 grammar, 2 halves) | F-HINT CONFIRM |
| C6 | Interface-injection wording | **1** (in-body formatter; per-subject R3) | F-INTERFACES CONFIRM |
| C7 | Second composite-pk escape | **1** (gate; R22) | F-COMPOSITE CONFIRM |
| C8 | Stamp-slot rename | **1** (constant) | F-IDATTR CONFIRM |
| C9 | `resolve_id` cache-key grammar | **1** + coupled walker consumer (R21) | F-ID CONFIRM |
| C10 | `node_ids=None` posture | **1 rule in 2 colors** (early-return shape both arms) | F-NODE-DEFAULTS REVISE |
| C11 | Order-key shape change | **1 rule**: `str\|None` keys, spells :933/:1055/:1080 + `None` arms (R9) | F-NODE-DEFAULTS REVISE |
| C12 | Fifth strategy string | **1 per direction** (C-R8-STRAT) | F-MEMBERSHIP CONFIRM |
| C13 | `callable` gains decode | **1 per direction** (R14) | F-MEMBERSHIP CONFIRM |
| C14 | Second setting source | **1** (`_validated_globalid_setting`) | F-SETTING CONFIRM |
| C15 | Precedence reorder | **1** (pure precedence; test :1237) | F-SETTING CONFIRM |
| C16 | Both-declared wording | **1** (install step; R3) | F-TYPENAME CONFIRM |
| C17 | Closure-marker rename | **1** (constant; R5) | F-TYPENAME CONFIRM |
| C18 | New decode failure mode | **1** (`decode_global_id`; root maps uniformly) | F-DECODE CONFIRM |
| C19 | Second wire shape | **1** (decode owns the parse) | F-DECODE CONFIRM |
| C20 | `str`-copy primitive | **0** (stdlib; R4) | R4 CONFIRM |
| C21 | Hint-read failure posture | **1** (that arm; R1) | R1 CONFIRM |
| C22 | Re-export respell | **0 moves, breaks lint** (C-REEXPORT) | F-MECH CONFIRM |
| C23 | `model_for`/seed contract | **0 here** (4 + 6 consumer calls follow; A1) | A1 REVISE |
| C24 | Required-missing exc type | **3 homogeneous sites** (`qs.get`/`aget` + `_order_nodes` + `_raise_if_required`, documented) | F-NODE-DEFAULTS REVISE |
| C25 | Third `from_id` parse | **Fires census + T-shape** (still exactly 2) | C-HARDEN CONFIRM |
| C26 | Envelope-unwrap change | **1** (`_coerce_node_id`; composed by :357) | F-COERCE NEW |
| C27 | Coercion mechanics change | **0 here, 1 at owner** (delegate :357; nomination) | F-COERCE NEW |
| C28 | Required-raise wording | **1** (`_raise_if_required`; `_order_nodes` wording stays split — R3) | F-NODE-DEFAULTS NEW |

### Findings: CONFIRM / REVISE ledger (15 + 1 + 13 + 23)

Counts are authoritative definitions only;
consumers, oracles, projections listed, never counted.

- **F-MECH — REVISE (import set + binding census;
  verdict stands).** Header #0–#14: 12 imports
  (`Iterable` added, `Any` gone, `TypeGuard`/`TypeVar`/
  `cast` added), TYPE_CHECKING block (+`Info`,
  `AwaitableOrValue`, `DjangoType`, `GlobalIDStrategy`,
  `_RelayDjangoType`), new `_ModelT`; no `__all__`
  (implicit surface unchanged). Use census
  re-derived: Callable 1, Iterable 3, TypeGuard 1,
  TypeVar 1, cast 3, apps 1, models 14,
  CompositePrimaryKey 1, relay 16,
  NodeIDAnnotationError 3, ConfigurationError 14,
  `_safe_arg_repr` 7, `_safe_class_name` 5,
  `_safe_type_name` 1, async_execution 2,
  SyncMisuseError 0 (re-export-only), model_for 4,
  initial_queryset 6, apply_sync/async 3/3,
  DjangoTypeDefinition 5, Info 6, AwaitableOrValue 2,
  DjangoType 2, GlobalIDStrategy 6 — every binding
  consumed (E09–E17). In-function imports 5 (C19):
  the 4 run-7 sites + the TRUE-cycle `..relay`
  import :355 (C-R19). Map prose byte-identical
  (module docstring). Owner + lifetime unchanged.
- **F-PRED — REVISE (census + pins; verdict
  stands).** Sole def :67 (body identical;
  `TypeGuard` annotation only). **14 production
  calls: 12 consumers + 2 message renders.**
  Consumers: [filters-sets][filters-sets] :2096
  (`filter_for_lookup`) + :2155
  (`_is_own_pk_under_relay_owner`) — 4→2 in the s9
  rewrite; [mutations-inputs][mutations-inputs] :374
  (`relation_id_scalar`) + :948
  (`payload_object_slot`); [mutations-resolvers][mutations-resolvers]
  :1352 (`coerce_lookup_id`); [registry][registry]
  :499; [types-finalizer][types-finalizer] :693/:710
  (`_synthesize_relation_connections`) + :1022/:1059
  (`finalize_django_types`) + :1419/:1420 (decision
  pair). Renders (projections, W2-I1 rule): :1489/
  :1492 (`_format_owner_pk_mismatch_error`).
  Examples: 1 prose comment (out of population).
  Tests: 5 hits (import + assert + 3 prose). C1
  REVISED (3 spellings; R23). Home file-local.
- **F-HINT — CONFIRM (re-pinned).** Slot :89
  (literal census 1, P02), install :92, honor
  :127–137 (`BaseException` arm :130, `is`
  identity :136, fallback :137), installer
  [types-base][types-base] :888. Body
  normalized-identical (not in D01). Oracles
  pin inject/preserve/hostile (token counts M).
- **F-INTERFACES — CONFIRM (re-pinned).** :142;
  sole package `__bases__ =` write :164 (P03);
  MRO skip :160; wrap :165–172 (`ConfigurationError`
  :167); consumer finalizer :1021 (`if
  definition.interfaces` arm :1020). Body
  normalized-identical.
- **F-COMPOSITE — CONFIRM (re-pinned).** :175;
  gate :194 (`CompositePrimaryKey` code census 1
  — [root-relay][root-relay] :180 is docstring
  prose, not a gate); bypass :203; escape
  `NodeIDAnnotationError` :204; raise :208;
  consumer finalizer :1023. Body
  normalized-identical.
- **F-IDATTR — CONFIRM (re-pinned).** Slot :223;
  stamp :226 (seed :250 — sole `_id_attr` write
  P04; scan :253; pin :256); default :259 (read
  :287; fallback :292); stamp caller :1121
  (sole, C-calls). Bodies normalized-identical.
- **F-ID — CONFIRM (re-pinned).** :297; seam
  read :325; `"pk"`→attname :326–327
  (proxy-correct subject); dict-hit :329;
  `getattr` :331. Body normalized-identical
  (annotations only). Coupled walker consumer
  :825–827 (R21).
- **F-COERCE — REVISE (reshaped by 2935+b63;
  rule stays single-sited).** `_coerce_node_ids`
  DELETED (C27: 0 hits). `_coerce_node_id` :334
  retained (sole caller :357). New
  `_node_value_or_none` :338: unwrap + field
  coerce via the single `_coerce_pk_or_none`
  delegate call :357 (C28; 0 mechanics here,
  C29) — the s4-nominated composing consumer.
  New `_node_values` :382: bulk map :391 +
  required loop :392–394. Filters split:
  `_apply_node_filter` :398 (single,
  required `value`) + `_apply_nodes_filter`
  :413 (batch, required `values`); no
  fall-through (C34/C35). Callers: :391/:978
  (value), :1052/:1077 (values), :985/:1010
  (single filter), :1054/:1079 (batch filter).
  The single-coerces-inside asymmetry is gone
  (N3 retired). Docstrings verified true
  (same-rule clause cross-checked at root
  :188–191). **Index row names the old shape —
  row edit proposed below.**
- **F-SETTING — CONFIRM (re-pinned).**
  Compute :427 (reader call :458; validator
  [types-base][types-base] :422), precedence
  :469 (in-file caller :729; test-only caller
  `test_base.py:1237`), finalizer compute caller
  :904 inside the snapshot + retry-guard block
  :893–915 (ordering re-verified), slot
  [registry][registry] :66/:137/:610, default
  base :156. Bodies normalized-identical
  (`GlobalIDStrategy` annotations only).
- **F-MEMBERSHIP — CONFIRM (re-pinned).** Sets
  :522/:523 (literals stable, C36); predicates
  :526/:536/:548 (emit/accept code-identical,
  C38); consumers: encoder :613, Step-2
  :895/:897, finalizer :428 (audit) + :452/:487
  (emitter/warning — the trio intact),
  [filters-base][filters-base] import :59 +
  union :72 + reads :766/:768. No third
  literal (C37 — the `:512` comment documents
  the absence). N5 (new near-miss, cleared):
  the :548–558 docstring's "Read by …
  `_accepted_globalid_type_names`" verb is
  loose — the filter reads the SETS (:766/
  :768), never the predicates (0 hits at base
  AND head) — but the load-bearing claim (one
  membership home, never re-typed) is exact
  and no wrong change follows (set moves move
  both readers; predicate-only moves affect
  decode alone — the R8 split). No verdict
  moves; not a defect (N1-class shorthand).
- **F-ENCODE — CONFIRM (re-pinned).** :561;
  callable arm :594–612 (return checks
  :596–611, `str` copy :605); label arm
  :613–614; type arm :616. Callers: closure
  :760 + [testing-relay][testing-relay] :121.
  Body normalized-identical. Call shape
  `(type_cls, model, root)` vs
  `_GLOBALID_CALLABLE_PARAMS` (base
  :419/:441/:488/:512) unchanged.
- **F-TYPENAME — CONFIRM (re-pinned).** Marker
  :628; detectors :631/:646; install :673
  (guard :715, both-declared raise :720,
  records :726/:734); closure :737 (nested
  :756, marker stamp :762, install :764).
  Consumer finalizer :1025 (snapshot
  threaded :1028). Bodies
  normalized-identical.
- **F-DECODE — CONFIRM (re-pinned).** :767;
  gate :823; parse :830–837; slot read
  :843–844; checks :850–860; Step-1 :868–886
  (label :871/:877/:883, name :885);
  Step-2 :888–904; return :908. Root callers
  :125/:329. **Normalized-identical to base
  (D04)** — the decode rule is byte-stable
  across the drift. D1 re-pinned (:816–820).
- **F-NODE-DEFAULTS — REVISE (reshaped by
  2935; rule stays single-sited).** Single
  :949/:989: coerce-first :978, `None` answer
  pre-query :981–983/:1006–1008, filter on
  value :985/:1010; async takes `value` :993.
  Bulk :1014/:1059: `None` early-return
  :1050/:1075, `_node_values` :1052/:1077,
  non-`None` filter :1054/:1079, `None`-hole
  keys :1055/:1080. `_order_nodes` :911:
  `list[str | None]` keys, arms :937/:945.
  New `_raise_if_required` :360 (raise :377;
  callers :394/:982/:1007) joins this finding:
  the required-miss rule (C24 now 3
  homogeneous sites, documented :367–372).
  Root dispatch callers :513/:620/:636 pass
  strings; upstream `:590` seam anchors the
  shape. Oracles: the 3 O01 pins
  (`test_consumer_overrides_receive_the_decoded_node_id_string`,
  `test_default_resolvers_find_a_row_whose_id_literal_spells_its_pk_differently`,
  `test_default_resolvers_read_an_uncoercible_id_as_no_row_under_strawberrys_node_field`)
  + order/hole/required/async rows (M).
- **F-INSTALL — REVISE (record correction;
  mechanism untouched).** Table :1088 (D05
  identical); install :1096 (stamp :1121,
  loop :1122–1128); consumer finalizer :1024.
  **N4 corrected:** upstream `Node` DEFINES
  `resolve_node` (real classmethod,
  `relay/types.py:590` delegating to
  `resolve_nodes`, runtime-confirmed at
  0.324.0 — the version run-7 cited) — the
  "verified absent / always-install path"
  rationale is overturned. No behavior
  delta: the `existing is None or identity`
  condition handles both shapes, so install
  is uniform via `__func__` identity across
  all four and the `None` arm is defensive
  for all four (C2/C3 counts hold). No
  production docstring made the absent claim
  (U07) — record-only correction, not a
  defect.
- **A1 — REVISE (census; adoption stands).**
  `model_for` 3→4 (:125/:193/:376/:935),
  `initial_queryset` 4→6
  (:984/:1009/:1051/:1053/:1076/:1078),
  apply_sync/async 2→3 each — all still
  seeds/reads/scopes, never re-derived (slot
  fields reach only via the F2 picker).
  Standing `queryset-seed-and-model-read`
  row covers this file; transcribes nothing.

- **Convergences (11 CONFIRM + 2 REVISE; all
  transcribing nothing; every trigger re-checked
  unfired).** C-STAMP CONFIRM (literal 1 :89;
  honor :129; root import :67 + write :451; def
  :419 + 4 calls :457/:524/:628/:645; WT
  trigger concurrent, never judged).
  C-TYPED CONFIRM (root callers :125/:329;
  `from_id` census holds; s4's per-element
  batched consumer cited, not re-derived).
  C-HARDEN CONFIRM (`from_id` code-calls
  exactly 2 — :832 + filter :828, prose
  :13/:914 excluded by AST, P05; `str`
  copies 4; surfaces unchanged).
  C-NAMEDECODE CONFIRM (def registry :471;
  sole caller :885; relay-only scan :499).
  C-GUARD CONFIRM (`DecodeResult` 8 hits,
  all in root relay). C-R5 CONFIRM (base
  :594 pre-injection vs :67 post; install
  base :888). C-R8-STRAT CONFIRM
  (vocabulary base :155, 3 strings, vs
  memberships vs filter derivation;
  `callable`/`custom` in neither). C-R14
  CONFIRM (definition MRO read :446 vs
  bypass :203; swallow :293–294).
  **C-R19 REVISE** (postures re-derived:
  base-cycle TRUE — base :74 imports this
  module at top; conf ride-along
  colocation; registry rationale still
  WRONG = D1; **new** relay import :355
  with TRUE rationale — root imports this
  module at top :67, P10/P11 — so each of
  the 5 in-function sites keeps its own
  posture). **C-J5 REVISE** (phase split
  stands with the new census: mint
  testing :122 vs serve :329/:331/:933/
  :1055/:1080). C-ATTNAME CONFIRM (6 code
  reads re-pinned: join_taxonomy :236,
  lateral :1194, planner :713, plans :958,
  walker :827, here :327; prose :816/:320/
  :321 excluded). C-REEXPORT CONFIRM (:41
  + [permissions][permissions] :137 with
  the convention comment :131–136).
  C-TRANSITIVE CONFIRM (no by-name
  boundary/seal imports — the new `..relay`
  edge is the coerce picker, not boundary
  machinery; async consumption stays
  transitive via apply_async).
- **R1–R8 — CONFIRM (re-pinned).** R1:
  3 `BaseException` (:130/:165/:845) + 7
  specific (NodeIDAnnotationError ×3,
  KeyError ×2, ValueError, LookupError —
  C04); new helpers add no `except` arms;
  J1 trigger unfired. R2: every gate
  subclass-tolerant; J2 unfired. R3: see
  REVISE below. R4: 4 + 4 + 1 copies
  re-derived (`str.__str__` here
  :605/:830/:859/:860; definition 4, base
  1); C20 → 0. R5: trio re-pinned
  (:631/:646/:1096 + definition closed read
  :484); mechanism-vs-question stands.
  R6: gate :203 / stamp :253 / fallback
  :292 verdicts. R7: thirds; home the
  install docstring :1115–1119. R8:
  emit/accept code-identical (C38); home
  the membership comment :514–521.
- **R3 — REVISE (count 14+1 → 14+2;
  verdict stands).** 14 `ConfigurationError`
  (C01 lines) + 2 `DoesNotExist`
  (:377/:941, C02), each per-subject; still
  no owned grammar. The new adjacency —
  `_raise_if_required`'s
  `_safe_arg_repr(node_id)` vs
  `_order_nodes`' `{key!r}` — is considered
  and split: raw client literal (needs the
  safe render) vs coerced key (typed value,
  `!r`); different inputs, different
  rendering verdicts (C28). Trigger: both
  render the same value class.
- **R9 — REVISE (twin spells re-derived;
  verdict stands).** Shared steps are now
  `_node_values` + `_apply_node(s)_filter`
  + `_order_nodes`; remaining spells (gate
  lines, `coerced_keys` :1055/:1080, index
  :933) are what the single-slot seam +
  await boundary force into each color
  (principle 11: extracting owns one line
  per helper). Trigger stands.
- **R10/R11 — CONFIRM (re-pinned).** R10:
  parameterized marked closure vs
  stateless table. R11: creation
  normalization ([types-base][types-base]
  :1182, composite-deferral prose :1208)
  vs finalize mutate (:142) + gate (:175).
- **R12 — REVISE (pins; verdict stands).**
  Dict-key :326–327 (row-class subject)
  vs root Field :150–151 (coerce/filter
  subject) vs walker column :826–827
  (`.only()` subject) — three subjects,
  three shapes, three reasons; unifying
  mis-keys proxy rows. Trigger unfired.
- **R13/R14 — CONFIRM (re-pinned).** R13:
  filter name-set :741–770 (message +
  membership) vs boolean :895/:897 over
  the one memberships. R14: absence here
  vs filter literal :81 + read :858.
- **R15 — REVISE (boundary moved; verdict
  stands in the new shape).**
  `_node_value_or_none` now OWNS the
  unwrap→coerce composition (unwrap :334
  by call + field-coerce by delegate
  :357); mechanics stay at
  [querysets][querysets] via the root
  picker. Unwrap still answers "which
  string", coercion "which value for this
  column" — sequential stages (a UUID
  envelope unwraps here alone; an
  int-column rule moves at the owner
  alone). Trigger unfired. (Nomination
  below is this edge's membership.)
- **R16–R22 — CONFIRM (re-pinned).** R16:
  twin pattern vs connection twins (s1
  verified; disjoint shared sets). R17:
  per-call return check :596–611 vs
  creation-time arity validation (base
  :422). R18: guard :715, 6th verb. R19:
  bare-MRO gate :67 vs fail-closed probe
  (definition :438 + `True` arms) —
  neither can call the other. R20: MRO
  fact :67 vs stamp-`None` gate (testing
  :103). R21: use :325–331 vs walker
  :824–827 support (one-way dependence).
  R22: presence-detection (base :532/:535;
  must not raise/cache) vs raising/
  caching scan. All triggers unfired.
- **R23 — NEW (predicate vs walker inline;
  dependency-separated).** Walker :824
  (`… and issubclass(type_cls, relay.Node)`,
  pre-existing at base :790, homed by s12
  to F-W8's projection guard) spells the
  same MRO question as :67 — same timing
  validity (post-finalization), same
  failure mode (bare `issubclass`, no
  containment). C1 moves both. The
  separation is forced at the top level
  by the documented one-way dependency
  ([types-init][types-init] docstring:
  "the optimizer subpackage must not
  import from `types/` at the top of any
  module" — the cycle path is
  [types-base][types-base] :67–68 +
  [types-finalizer][types-finalizer] :63–64
  top optimizer edges): the 1-line stdlib
  spell is the boundary-allowed form.
  Trigger: the predicate grows beyond the
  1-line test, or the boundary lifts —
  then the walker takes the sanctioned
  lazy-import shape (walker :1559–1562
  precedent) + call. F-PRED stays
  file-local. (Missed by run-7, which
  read the line for the projection
  question, and by s12, which homed it
  without engaging the predicate
  question — recorded here so no cycle
  re-litigates.)
- **Near-misses.** N1 CONFIRM (module
  docstring byte-identical; shorthand +
  exact timing claim intact). N2 CONFIRM
  (upstream-owned names, re-pinned
  :584/:596/:1116 vs `:590`). N3 RETIRED
  (the coerce asymmetry is gone — both
  filters take caller-coerced values;
  superseded by 2935+b63). N4 REVISED
  (record correction under F-INSTALL).
  N5 NEW (cleared under F-MEMBERSHIP).

### Nomination adjudication (s4 F2, from this file's side)

**ENDORSED.** `field-value-coercion` gains the
composing consumer
`types/relay.py::_node_value_or_none` →
`relay.py::_coerce_pk_or_none`, verified from this
side at HEAD bytes: the edge is real (by-call
composition — the single delegate call :357,
C28); the in-function import carries a TRUE cycle
rationale (root imports this module at top :67,
P10; no top import back, P11); the picker
delegates mechanics once (root :191, N02) with
field choice via L1 (`_node_id_slot` :188; this
file reaches slot fields ONLY through the picker
— no `_meta`/`get_field` slot derivation here);
routing re-derived with s4-W2's precision
(single-sync direct :978, single-async by
parameter :980/:993, batch ×2 via `_node_values`
:1052/:1077); 0 new coercion mechanics here
(C29: `to_python`/`run_validators` 0 hits);
mechanics change → 0 here, 1 at
[querysets][querysets] (C27). Membership (no new
row) is the right shape — no new rule is named —
and the F2 family item is the right home (that
file's rows live there). Routing note for
Worker-0: the standing `field-value-coercion`
plan row (status `rejected` = no consolidation;
files-covered lacks this file) gains this
consumer — append `types/relay.py` to its
files-covered now, or hold the membership for
the F2 family item; either way the rejection
verdict is untouched (a new consumer re-opens
nothing).

### Defects (run 8)

- **D1 (run-7, re-pinned, still UNFIXED, minor,
  doc-only):** the `decode_global_id`
  in-function-import comment (:816–820) is
  byte-identical to base (:735–739) — the wrong
  load-cycle rationale (an in-function import
  cannot close a cycle), the TRUE/FALSE split
  (registry has no `types`/`relay` top edge,
  P12; [types-base][types-base] imports
  `registry` at top :69 beside this module
  :74 — proof by construction stands), and the
  mispoint (rationale lives in
  `_validated_globalid_setting` :449–454, not
  `_resolve_globalid_strategy`) all persist.
  Contract row broken: the comment's own "must
  not" claim. Owner unchanged:
  `types/relay.py::decode_global_id` comment.
  Filed for normal closeout homing (re-pin,
  not close). Identical in worktree (F04);
  outside every behavior delta (decode is
  D04-identical). Not fixed inside this item
  (file item; zero-edit). Freshness: target
  HEAD `968fb95a` / WT `6c2e8c20` / PRE
  `4b2a9df5`; registry HEAD `9d2021eb`; base
  HEAD `d160998a`.

No new defect. N4 is a prior-artifact record
error (no production claim — U07), N5 is
N1-class shorthand (no wrong-change hazard):
neither meets the defect bar.

### Pending execution (run 8)

None. All 118 probe checks are
`execution-verified` read-only (HEAD bytes via
`git show`, AST + token census; the one runtime
check imports strawberry only, no Django, no
DB, no registry writes, no source mutation).
No consolidation proposed, so no consolidation
gate with negative control is owed. DB-backed
cells inapplicable by construction: the new
helpers reach the database only through
composed primitives owned elsewhere (A1 seeds/
scopes, the F2 picker, lazy `.filter` —
materialization is Django's, covered by the
O01 oracles); every rule THIS file defines is
dispatch + string work. Oracle/spec bodies
stay `static-reviewed`, the honest label for a
zero-edit item. No shared-tree pytest run, per
the item fence (and the standing no-pytest
rule).

### Judgment (run 8)

Zero-edit file re-trace: drift delta owned at
HEAD bytes (2935 string seams + composing
helpers; b63 filter split; 4 typing commits
proved inert by diff read + normalized-AST
screen), 53/53 enumeration members homed (0
renamed, order kept), 38/38 carried rows
re-derived (28 CONFIRM + 10 REVISE, none
moving rule ownership) + 1 new rejection
(R23, dependency-separated) + the s4 F2
nomination endorsed from this side, every
rule still exactly one authoritative
definition with cross-module reads composing
by name. D1 re-pinned (persists). 3 plan-row
edits + 1 new rejection row + 1 membership
note for Worker-0 below. No production edit,
no test change, no pending execution.

### Freshness (run 8)

Target HEAD blob `968fb95a` (1128 lines) /
worktree `6c2e8c20` (1182 lines) / pre-merge
`4b2a9df5` (1067 lines). `ITEM_BASELINE=
2ac2ee55…`; HEAD `83998e08` unmoved
start→finish (G03). Zero tracked paths
touched: the target's item diff is 0 bytes
(G02); this artifact is the sole written
path. Upstream lock pins strawberry-graphql
0.324.0 at base AND head (floor 0.316.0 →
0.322.2); all upstream anchors re-verified
against the same installed bytes.

| Path | HEAD | Worktree | 9aaaad5d |
|---|---|---|---|
| `django_strawberry_framework/types/relay.py` | `968fb95a` | `6c2e8c20` | `4b2a9df5` |
| `django_strawberry_framework/types/base.py` | `d160998a` | `909c25a7` | `dc67f084` |
| `django_strawberry_framework/types/definition.py` | `5bf257c3` | `936ab86f` | `1c59a3fe` |
| `django_strawberry_framework/types/finalizer.py` | `cb2dde6b` | `7d354e77` | `b9d8acb2` |
| `django_strawberry_framework/types/__init__.py` | `1bf69028` | `1bf69028` | `1bf69028` |
| `django_strawberry_framework/relay.py` | `a09485a1` | `fd88aafa` | `f5760b45` |
| `django_strawberry_framework/registry.py` | `9d2021eb` | `57fa18ae` | `27358cbc` |
| `django_strawberry_framework/conf.py` | `10096f84` | `8092d80b` | `3820c575` |
| `django_strawberry_framework/filters/base.py` | `e2e683a8` | `fc1cf61f` | `3b1dcbce` |
| `django_strawberry_framework/filters/sets.py` | `3d307402` | `ec278851` | `e47c6758` |
| `django_strawberry_framework/mutations/inputs.py` | `fd463fff` | `2870a8d1` | `840da733` |
| `django_strawberry_framework/mutations/resolvers.py` | `7a25afea` | `dd00ec6e` | `c9cff059` |
| `django_strawberry_framework/optimizer/walker.py` | `bdd9c2f1` | `9130aceb` | `d5759ef8` |
| `django_strawberry_framework/utils/querysets.py` | `392e50d0` | `cfc773ba` | `8fc556d5` |
| `django_strawberry_framework/utils/execution_mode.py` | `b86a08cd` | `b86a08cd` | `9805cdaf` |
| `django_strawberry_framework/testing/relay.py` | `8e5f9c9d` | `0c48f0a9` | `f807bf92` |
| `django_strawberry_framework/__init__.py` | `8b165672` | `8b165672` | `0ef72601` |
| `django_strawberry_framework/permissions.py` | `d77c5050` | `42c3c19c` | `6c97d887` |
| `django_strawberry_framework/connection.py` | `3d6dd424` | `64b85d0e` | `1fca6266` |
| `django_strawberry_framework/utils/write_values.py` | `01a3318c` | `4fa8118d` | `13548c76` |
| `tests/types/test_relay_interfaces.py` | `515ebce5` | `3ffb75b8` | `3ffb75b8` |
| `tests/test_relay_node_field.py` | `7c0f22ed` | `7f47c3dd` | `d4ce0c7d` |
| `tests/test_relay_connection.py` | `29a2be59` | `e6b4b556` | `fe2b2d24` |
| `tests/testing/test_relay.py` | `55e43ed2` | `4e61e8f1` | `4e61e8f1` |
| `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` | `45f43dfe` | `45f43dfe` | `45f43dfe` |

Searched population for every "no second site"
claim: full package source at HEAD (`git grep
HEAD`, directory pathspec), both oracle files at
HEAD bytes, the installed strawberry-0.324.0
sources, and the spec. Exclusions re-checked:
[types-converters][types-converters] (zero
relay/GlobalID hits — empty census, re-run),
[types-resolvers][types-resolvers] (1 prose
mention, no mechanism),
[types-relations][types-relations] (no relay
surface), walker internals past the projection,
and every open family whose trigger vocabulary
finds no member here (matrix 1).

## Index rows for Worker-0 (run-8 s14)

(Worker-0 alone edits the plan; rows named here
for transcription. Prior run-7 rows stand except
as revised below; all other finding texts name
symbols, never lines, so re-pins move no text.)

- File-local REWRITE
  `types-relay-node-id-coerce-and-filter`: owner
  `django_strawberry_framework/types/relay.py::_node_value_or_none`
  (+ `_node_values` bulk map, `_coerce_node_id`
  envelope unwrap, `_apply_node_filter` single +
  `_apply_nodes_filter` batch required-positional
  filters with no fall-through;
  `_coerce_node_ids` deleted at `2935e0e4`).
- File-local REVISE
  `types-relay-node-fetch-defaults`: append
  `+ _raise_if_required` (required-miss
  `DoesNotExist`, `2935e0e4`; C24 now 3
  homogeneous sites) and the string-seam /
  `None`-hole-keys reshape note.
- File-local NOTE `types-relay-resolver-defaults-install`
  (text stands; record corrected in-artifact):
  upstream defines all four slots incl.
  `resolve_node` (N4 overturned; install
  uniform via `__func__` identity).
- File-local NOTE `types-relay-post-injection-predicate`
  (text stands; census in-artifact): 12
  consumers + 2 message renders at HEAD; the
  walker conjunct is R23-separated (new row
  below), not a second definition.
- Rejection COUNT-EDIT
  `types-relay-wordings-vs-shared-grammar`:
  `14 + 1` → `14 + 2` per-subject raises
  (new `_raise_if_required` `DoesNotExist`;
  still no owned grammar).
- NEW rejection row
  `types-relay-predicate-vs-walker-inline` |
  `django_strawberry_framework/types/relay.py::implements_relay_node`
  (rejection recorded here; same MRO question
  as the walker :824 projection-guard
  conjunct, separated at the top level by
  the documented one-way types→optimizer
  dependency; trigger: predicate grows
  beyond the 1-line test or the boundary
  lifts — then the walker takes the
  sanctioned lazy-import shape) |
  `django_strawberry_framework/types/relay.py`,
  `django_strawberry_framework/optimizer/walker.py`
  | File `types/relay.py` | rejected |
- Membership note `field-value-coercion` gains
  the composing consumer
  `types/relay.py::_node_value_or_none` (no
  new row; home the F2 family item; verdict
  untouched — see Nomination adjudication).

No `## Families` item owed (R23 is a rejection
with a trigger, not a consolidation); zero
`## Owned changes` (file item, zero-edit).
AGENTS.md prose check: touched paths = this
`.md` artifact only, so no ruff/mypy run is
owed; citations reuse the existing
reference-style link block (no new ref-ids,
scaffold intact); `path:NN` allowed in
`docs/dry/dry-*.md`; no process provenance;
concurrent dirt preserved; no commit.

## Run-8 verification (Worker 2)

Independent re-trace at HEAD `83998e08`
(verified unmoved start→finish), expectation-
first against the run-8 claim. Instruments of
my own: `/tmp/w2_s14_A.py` … `/tmp/w2_s14_P.py`
(AST + token censuses at HEAD bytes, normalized-
AST inertness screen, source + runtime upstream
checks), all executed via `workspace.py run
dry/relay-retrace-s14/verify` (run ids in
`dry/evidence/logs/`; `git -C` against the
shared checkout since copies carry no git).
One runtime check ran in the shared venv: the
verify copy's venv lacks `typing_extensions`,
so `import strawberry` fails there; the check
imports strawberry only (no Django, no DB, no
source mutation). No pytest; read-only probes
only. Package-wide censuses use the directory
pathspec. Prior text stands untouched; this
section appends. Nothing tracked touched
except this artifact (untracked, owned by this
item); the target's item diff is 0 bytes.

### Own trace (pre-reconciliation)

Drift `0c0537e2`→HEAD on the target is exactly
the 6 claimed commits in order (`999a1aab`,
`b20277fe`, `2935e0e4`, `b63df99d`,
`dfbea72b`, `fef11e64`); `2935e0e4` is
86+/23-, `b63df99d` 18+/14-. My normalizer
(annotations, docstrings, comments,
TYPE_CHECKING, imports stripped; `cast()`
transparent; `AnnAssign`→`Assign`; TypeVar
dropped) proves all four typing commits
normalized-equal parent→child, and my
base→HEAD per-symbol screen changes exactly
the 6 behavior defs, adds exactly the 4
helpers + `_ModelT`, removes exactly
`_coerce_node_ids`, with `decode_global_id`
and `_RELAY_RESOLVER_DEFAULTS` identical.
Enumeration at HEAD bytes: 51 top-level (1
docstring, 12 `ImportFrom`, 1 `If`, 6
`Assign`, 28 `FunctionDef`, 2 `AsyncFunctionDef`,
1 `AnnAssign`) + 2 nested (`:127`, `:756`) =
53/53, delta +5/−1 order-kept. Every member
pin re-derived matches the claimed table
#0–#50. I homed all 53 file-local / adoption
/ converge / rejection before reading the
claim's homes; the reconciliation below
records each agreement with my own counts.

### Reconciliation (38 carried rows + R23)

FINDINGS — all 15 file-local rows survive.
F-MECH REVISE: 12 imports + TYPE_CHECKING
block (+`_RelayDjangoType`, 5 annotation
uses) + `_ModelT` confirmed; use census
re-derived (Callable 1, Iterable 3, TypeGuard
1, TypeVar 1, cast 3, apps 1, models 14,
CompositePrimaryKey 1, relay 16,
NodeIDAnnotationError 3, ConfigurationError
14, `_safe_arg_repr` 7, `_safe_class_name` 5,
`_safe_type_name` 1, async_execution 2,
SyncMisuseError 0, model_for 4,
initial_queryset 6, apply_sync/async 3/3,
DjangoTypeDefinition 5, Info 6,
AwaitableOrValue 2, DjangoType 2,
GlobalIDStrategy 6 — every binding consumed;
relay/DjangoType counts include the
TYPE_CHECKING-guard use at :56); in-function
imports exactly 5 by AST
(:355/:455/:456/:493/:821); module docstring
byte-identical to base. F-PRED REVISE: sole
def :67; 14 calls = 12 consumers + 2 renders
at the claimed pins (filters-sets :2096/:2155,
mutations-inputs :374/:948,
mutations-resolvers :1352, registry :499,
finalizer :693/:710/:1022/:1059/:1419/:1420 +
renders :1489/:1492); examples 1 prose,
tests 5 (import + assert + 3 prose).
F-HINT/F-INTERFACES/F-COMPOSITE/F-IDATTR/F-ID
CONFIRM: slot :89 (literal census 1), honor
:127–:137, installer base :888; :142, sole
`__bases__` write :164, wrap :167, finalizer
:1020/:1021; gate :194, bypass :203, escape
:204, raise :208, finalizer :1023,
CompositePrimaryKey code census 1;
slot :223, seed :250 (sole `_id_attr` write),
scan :253, pin :256, read :287, fallback :292,
sole stamp caller :1121; :297/:325/:326–:327/
:329/:331. F-COERCE REVISE: `_coerce_node_ids`
0 hits; `_coerce_node_id` :334 sole caller
:357; `_node_value_or_none` :338–:357 (single
delegate call); `_node_values` :382 (map :391
+ required loop :392–394); filters :398/:413
required-positional, no fall-through (base
:339 `return qs` fail-open confirmed gone);
callers :391/:978/:1052/:1077/:985/:1010/
:1054/:1079. F-SETTING CONFIRM: :427/:458/
:469/:729, base validator :422, default :156,
finalizer :904 in :893–915, slot :66/:137/:610,
test calls :1237/:1240/:1243. F-MEMBERSHIP
CONFIRM: sets :522/:523 stable, predicates
:526/:536/:548, encoder :613, Step-2 :895/:897,
finalizer :428/:452/:487, filter :59/:72/
:766/:768, no third literal. F-ENCODE CONFIRM:
:561, callable arm :594–612, :613–614/:616,
callers :760 + testing :121. F-TYPENAME
CONFIRM: :628/:631/:646/:673 (:715 guard,
:720 raise, :726/:734 records, :730
classification)/:737 (:756/:762/:764),
finalizer :1025/:1028. F-DECODE CONFIRM:
:767, gate :823, parse :830–837, checks
:850–860, Step-1 :868–886 (:885 sole registry
caller), Step-2 :888–904, root :125/:329,
normalized-identical to base. F-NODE-DEFAULTS
REVISE: single :949/:989 (coerce :978, branch
:979, handoff :980/:993, None :981–983/
:1006–1008, filter :985/:1010), bulk
:1014/:1059 (early-return :1050/:1075,
:1052/:1077, filter :1054/:1079, keys
:1055/:1080), `_order_nodes` :911
(`list[str | None]` :914, index :933, arms
:937/:945, raise :941), `_raise_if_required`
:360 (raise :377, callers :394/:982/:1007).
F-INSTALL REVISE: table :1088–1093 identical,
:1096 (stamp :1121, loop :1122–1128,
condition :1127), finalizer :1024; N4
corrected (below). A1 REVISE: 4/6/3/3, all
seeds/reads/scopes, standing row covers.

CONVERGENCES — 11 CONFIRM + 2 REVISE, all
transcribing nothing, every trigger re-
checked unfired with my own sweeps. C-STAMP:
literal 1, honor :129, root :67/:419/:451 +
4 calls :457/:524/:628/:645, all in root
refetchers (`_await_and_stamp`,
`DjangoNodeField._resolve`,
`DjangoNodesField._resolve`/`_gather`).
C-TYPED: root :125/:329, `from_id` census
holds, 4 statuses. C-HARDEN: `from_id`
code-calls exactly 2 (:832 + filter :828;
prose excluded by AST), `str.__str__` 4
(:605/:830/:859/:860), surfaces unchanged.
C-NAMEDECODE: registry :471, sole caller
:885, scan :499. C-GUARD: `DecodeResult` 8
hits, all in root relay. C-R5: base :594 vs
:67, install :888. C-R8-STRAT: base :155 (3
strings) vs memberships vs filter derivation.
C-R14: definition :446 vs bypass :203,
swallow :293–294. C-R19 REVISE: base-cycle
TRUE (base :74 top edge), conf colocation,
registry rationale still WRONG (D1), new
relay :355 TRUE (root :67 top edge, no top
import back). C-J5 REVISE: mint testing :122
vs serve :329/:331/:933/:1055/:1080. C-ATTNAME:
6 code reads (join_taxonomy :236, lateral
:1194, planner :713, plans :958, walker :827,
here :327; prose :816/:320/:321 excluded).
C-REEXPORT: :41 + permissions :137 (:131–136
comment). C-TRANSITIVE: no by-name
boundary/seal import; `:355` is the coerce
picker.

REJECTIONS — 18 CONFIRM + 4 REVISE, each
with contract difference + trigger at owner
or durable same-file home, all triggers
unfired. R1: 3 `BaseException`
(:130/:165/:845) + 7 specific, no two sharing
scope + verdict. R2: no exact-gate spell in
target; J2 unfired. R3 REVISE: exactly
14 `ConfigurationError` (:167/:208/:597/:607/
:720/:824/:834/:846/:851/:862/:873/:879/:890/
:900) + 2 `DoesNotExist` (:377/:941), all
per-subject; the `:378` safe-render vs `:942`
`{key!r}` adjacency stays split by input
class. R4: 4 + 4 (definition
:265/:299/:415/:454) + 1 (base :1363). R5:
trio :631/:646/:1096 + definition :484. R6:
:203/:253/:292 verdicts. R7: thirds, home
:1115–1119. R8: :533/:545 code-identical,
home :514–521. R9 REVISE: shared steps now
`_node_values` + filters + `_order_nodes`;
spells :933/:1055/:1080. R10: closure :737 vs
table :1088. R11: base :1182/:1208 vs
:142/:175. R12 REVISE: :326–327 vs root
:150–151 vs walker :826–827. R13: filter
:741–770 vs :895/:897. R14: absence vs filter
:81/:858. R15 REVISE: composition owned at
:357, mechanics at querysets via root :191
(field :188). R16: twin contrast (s1
verified). R17: :596–611 vs base :422. R18:
guard :715, 6th verb. R19: :67 vs definition
:438–:440 fail-closed probe. R20: :67 vs
testing :103. R21: :325–331 vs walker
:824–827. R22: base :532/:535 vs raising/
caching scan.

R23 NEW — ADOPTED as drawn. Walker :824
spells the same MRO question as :67
(pre-existing at base :790, byte-same
shape), same timing validity, same bare-
`issubclass` failure mode. Top-level sharing
is barred by the documented one-way
dependency (`types/__init__.py` :17–:28:
optimizer must not import from `types/` at
top; cycle path base :67–:68 + finalizer
:63–:64 verified at top). Trigger (predicate
grows past the 1-line test, or the boundary
lifts → walker takes the :1559–:1562
lazy-import shape + call) is feasible and
falsifiable. F-PRED stays file-local. The
proposed row text is judged exact (below).

NEAR-MISSES — N1 CONFIRM (docstring
byte-identical), N2 CONFIRM (connection
:584/:596/:1116 vs upstream `:590`, both
upstream-owned), N3 RETIRED (base asymmetry
:334–:339 confirmed reshaped away), N4
REVISED (record correction — overturn
reproduced myself: `Node.__dict__[
'resolve_node']` is a real classmethod at
`relay/types.py:590`, `node_id: str` seam,
delegating to `resolve_nodes`, at installed
strawberry-graphql 0.324.0; no production
docstring made the absent claim, so
record-only, not a defect), N5 NEW cleared
(docstring :552–554 names the filter reader
loosely, but the filter reads the SETS
(:766/:768) and never the predicates — 0
hits at base AND head — while the load-
bearing one-home claim is exact; N1-class
shorthand, no defect).

MATRIX — 6/6 re-discharged: (1) CONFIRM —
typed-primitive consumers, audited filter
path, one shared guard, no GlobalID rule in
orders/auth/keyset (W2-I3), no mapping reads
at HEAD bytes, upstream collision out of
population, walker conjunct R23; (2) REVISE —
2 `async def` (:989/:1059), branches
:979/:1048, shared decisions
`_node_value_or_none`/`_node_values`/
filters/`_order_nodes`, `value` by parameter
:993, pure-sync rest; (3) REVISE — 4/6
consumed, attname 1-of-6, id-attr once per
chain (sync reads :977/:1047, async by
parameter :991/:1061), `effective_*`
:726/:734, classifications :726/:730/:734;
(4) REVISE — memberships shared, closed
identity :484, stamp↔honor, `_node_values`
→ `_node_value_or_none` by call :391, N3
superseded; (5) REVISE — oracles grew (W2-I1:
true 24→28, +4 incl. the async twin; the 3
named O01 pins verified present),
precedence :1204 (calls :1237+), spec-031
Decisions 3/4/5/6/7/8/10/11/13 present,
glossary + LIFECYCLE (both filters) present,
upstream re-pinned (`GlobalIDValueError` ⊂
`ValueError` at `:70`, seam `:590`); (6)
CONFIRM — composite :175, both-declared :720,
encode-only audit + backstop (:858),
routing :428/:452/:487, unregistered :425,
no-Node-types :1058–:1061, required-miss 3
sites (:377/:941/:986), per-site `except`
verdicts, downstream `SyncMisuseError`.

CHALLENGES — C1 3 spellings (base :594 +
:67 + walker :824, R23-separated); C2–C9
CONFIRM counts hold (table/preserve/honor/
formatter/gate/constant/read+walker); C10 1
rule/2 colors (:1050/:1075); C11 1 rule
(`str|None`, :933/:1055/:1080 + :937/:945);
C12–C22 CONFIRM; C23 4+6; C24 3 homogeneous
sites; C25 census holds; C26 1
(`_coerce_node_id`, sole caller :357); C27 0
here/1 at querysets (0 `to_python`/
`run_validators` hits); C28 1
(`_raise_if_required`, R3 split).

### Nomination (s4 F2, from this file's side)

ENDORSED — agree with W1 on my own
derivation. The edge is real (single delegate
call :357); the in-function import rationale
is TRUE (root :67 top edge, no top import
back in the 12-import census); the picker
delegates mechanics once (root :191) with
field choice via `_node_id_slot` :188, and
this file's new helpers reach slot fields
only through the picker (full bodies read: no
`_meta`/`get_field` derivation); routing is
single-sync direct :978, single-async by
parameter :980/:993, batch ×2 via
`_node_values` :1052/:1077; 0 new coercion
mechanics here. Membership (no new row) in
the F2 family item is the right shape; the
standing plan row (`rejected`, files-covered
lacking this file) is the right target. The
rejection verdict is untouched.

### Defects, hunks, freshness, zero-edit

D1 re-pinned and persists (minor, doc-only,
UNFIXED, normal closeout homing): the comment
is byte-identical base :735–739 ↔ HEAD
:816–820 ↔ worktree; the load-cycle rationale
stays impossible (registry top edges are
stdlib-leaf + TYPE_CHECKING-only + in-function
:494 — P12 re-derived) with proof by
construction intact (base :69 beside :74);
the mispoint persists (rationale lives at
:449–454, not in `_resolve_globalid_strategy`).
No new defect: N4 is a prior-artifact record
error with no production claim; N5 is
N1-class shorthand.

HEAD→worktree is 20 hunks, 129+/75-, blob
`6c2e8c20`, attributed by content against
`git show HEAD:`: 01 `MethodType` import, 02
truth/lazy imports, 03 `ModelField`, 04
`truth.is_subclass`, 05 trigger paragraph, 06
honor-read migration, 07 bases migration +
`TypeError` narrowing, 08/09/13/15/18/19
truth renders, 10 `_ID_NOT_CACHED`, 11
`_resolve_id_default` migration (carries the
`_classmethod_function` def), 12/14 `slot=`
threading (+ `_node_id_slot` import), 16/17/20
`_classmethod_function` call sites, 18 decode
migration. NO owned hunk: the dispatch names
no ledger hunk for this file, so all 20 are
concurrent-external, untouched, never judged.
The trigger paragraph is content-identical to
the run-7 text and byte-identical PRE↔WT (9
lines with the attr line), but HEAD count is
0 — it rides the pre-merge side only — hence
concurrent by the dispatch rule. The 4 HEAD
helpers are present in WT; `_coerce_node_ids`
absent; D1 identical HEAD↔WT.

Fingerprints re-derived digit-for-digit: target
HEAD `968fb95a` (1128 lines) / WT `6c2e8c20`
(1182) / PRE `4b2a9df5` (1067); the full
25-path HEAD/WT/PRE table verifies 25/25.
`ITEM_BASELINE=2ac2ee55…` (`2ac2ee55dd518ddf…
`, WIP on `83998e08`): target diff vs
baseline is EMPTY (0 bytes) — unchanged since
dispatch. HEAD `83998e08` unmoved start→finish.

### Index rows for Worker-0 (judgment)

The run-8 row instructions are judged as exact
replacement text and endorsed verbatim: the
REWRITE of `types-relay-node-id-coerce-and-
filter` (owner `_node_value_or_none` is the
per-id kernel all four defaults coerce
through; members + `2935e0e4` deletion note
accurate); the REVISE of
`types-relay-node-fetch-defaults` (`+
_raise_if_required`, C24 now 3 homogeneous
sites, string-seam/`None`-hole reshape);
the COUNT-EDIT `14 + 1` → `14 + 2` (raise
lines re-derived exactly); the two NOTEs
(text stands; N4 + census/R23 records live
in-artifact); the NEW `types-relay-predicate-
vs-walker-inline` rejection row (contract
difference, dependency bar, trigger, files,
and `:824` HEAD pin all accurate); and the
`field-value-coercion` membership note (no new
row; append `types/relay.py` to files-covered
now or hold for the F2 item). No `Families`
item owed.

### Record notes (immaterial; verdicts stand)

W2-I1: the node-field oracle census counts
sync `def test_` only (claimed 23→26, +3).
True counts include `async def test_`: base
23+1=24, HEAD 26+2=28; `2935e0e4` added 4
tests (+176 lines), the 4th being the async
twin `test_async_default_resolvers_read_an_
uncoercible_id_as_no_row`. Oracles are
listed-never-counted per protocol, and the
missed twin covers the same rule in the
second color — coverage only stronger. No
home/count/gate moves.

W2-I2: `_classmethod_function` has 5 worktree
call sites across 3 functions (:704/:725/:730/
:1179/:1180; def rides hunk 11), not "3 call
sites". Attribution unaffected (all
concurrent-external).

W2-I3: orders carries 1 prose mention
(`orders/inputs.py:299`, a removal note
explicitly stating ordering has no
leaf-shape divergence), not a literally empty
hit census. Zero GlobalID rules either way.

No Worker-2 defects. No pending execution:
all probes are execution-verified read-only;
no consolidation is proposed so no gate with
negative control is owed; DB-backed cells
stay inapplicable by construction (rules here
are dispatch + string work; DB reach only via
composed A1/F2/lazy-filter primitives owned
elsewhere). Prose check: this section adds no
link ref-ids (plain code spans only),
scaffold intact; `path:NN` allowed here; no
process provenance; no commit per standing
rule.

Verdict: verified (zero-edit; 53/53 homed;
28 CONFIRM + 10 REVISE carried, R23 adopted,
s4 F2 endorsed from this side; D1 persists
for closeout homing; 3 immaterial notes).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[root-init]: ../../django_strawberry_framework/__init__.py

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[permissions]: ../../django_strawberry_framework/permissions.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[root-relay]: ../../django_strawberry_framework/relay.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-definition-relations]: ../../tests/types/test_definition_relations.py
[test-filters-base]: ../../tests/filters/test_base.py
[test-filters-finalizer]: ../../tests/filters/test_finalizer.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-node-field]: ../../tests/test_relay_node_field.py
[test-relay-connection]: ../../tests/test_relay_connection.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py
[test-testing-relay]: ../../tests/testing/test_relay.py
[test-types-base]: ../../tests/types/test_base.py
[test-types-finalizer]: ../../tests/types/test_finalizer.py

<!-- examples/ -->
[library-schema]: ../../examples/fakeshop/apps/library/schema.py
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
