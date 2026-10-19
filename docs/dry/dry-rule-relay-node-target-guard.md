# DRY review: `relay-node-target-guard`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `relay-node-target-guard`. Provisional owner
`django_strawberry_framework/list_field.py::_validate_relay_djangotype_target`
— CONFIRMED, not inherited. Member files:
`django_strawberry_framework/list_field.py`,
`django_strawberry_framework/relay.py`,
`django_strawberry_framework/connection.py`. The only item hunk is a
docstring trigger clause on `list_field.py`, below. Prior records only as
triggers: the relay + list_field file items (F8/L2 in the relay item, R1/C9/C10
in the list_field item — every edge below re-derived from the body, nothing
inherited) and the three verified GlobalID families (decode vs guard vs
hardening = shape-vs-existence-vs-policy per the typed-decode item — verified,
not inherited). Never read any `worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds no row on
`list_field.py` or `connection.py` — confirmed by full read; its one row on
`relay.py` is the `typed-globalid-decode` docstring clause, confirmed by hunk
content (`git diff HEAD -- django_strawberry_framework/relay.py` shows exactly
that 5-line clause and nothing else). `connection.py` carries EXTERNAL
concurrent dirt (the cursor-guard feature: `from_base64` import,
`_offset_cursor_prefix`, `_reject_negative_offset_cursor`, the
non-queryset fallback branch): verified vs `git show HEAD:` — none of its
hunks touches a guard site (the `_validate_relay_djangotype_target` call,
`_connection_type_for`, `_guard_source_not_pre_sliced`,
`_resolve_order_path_field` are all outside the hunk ranges). `list_field.py`
is byte-identical to HEAD (`ce682d5f…`). No dirty path was edited: the one
tracked edit lands on clean `list_field.py`. `ITEM_BASELINE`
`399c797d…` verified present via `git cat-file -t`. Reading the dirty files
was free.

## System trace

Rule: guarding that a Relay node target EXISTS and is resolvable — the
existence half of node resolution. Node resolution decomposes into three
questions answered at three lifecycle phases: decode (is the wire id well
shaped — owned by the hardening/decode families), target guard (is the target
a registered, resolvable Relay type — this family), visibility (may this
viewer see the row — owned by the permission/cascade families).

What "target exists" means at each site (each re-derived from its body):

- **Construction, factory target** ([list-field][list-field]
  `::_validate_relay_djangotype_target`, the single definition): the
  supplied class is a class, subclasses `DjangoType`, carries its OWN
  `__django_strawberry_definition__` whose `origin is target_type` AND which
  `is` the registry's canonical definition (identity — a fabricated
  same-origin lookalike, a copied definition, and a never-registered
  definition are all rejected), the resolver seam is callable, and the target
  is Relay-Node-shaped (`_is_relay_shaped`: `relay.Node` in declared
  `Meta.interfaces` OR direct inheritance). Failure envelope: raises
  `ConfigurationError` at the line that constructed the field, naming the
  factory. Returns the one contained definition read onward so no caller
  re-reads the attribute.
- **Construction, callers** ([root-relay][root-relay]`::_validate_node_target`,
  [connection][connection]`::DjangoConnectionField`): pure pass-throughs —
  the relay wrapper passes `None` + its field label + its own
  `relay_error_message`; the connection call passes its resolver + its own
  label + message. Verified in source: neither body re-spells a guard.
  Same envelope (the owner's raise, with the caller's label).
- **Runtime, row existence** ([relay-types][relay-types]
  `::_resolve_node_default` / `::_resolve_nodes_default` /
  `::_order_nodes` + async twins): the visibility-scoped row is present.
  Envelope is the upstream `required` flag contract, not this family's:
  `required=False` yields `None` (`qs.first()` / `index.get`) for a missing
  or hidden row; `required=True` raises the model's `DoesNotExist`
  (`qs.get()` / explicit raise). The node root fields always dispatch with
  `required=False`, so a well-formed-but-absent id resolves to `null`
  (single) or a positional `null` hole (batch) — softness applies to ROWS,
  never to TYPES.
- **Runtime, wire-name resolution** ([relay-types][relay-types]
  `::decode_global_id` Steps 1–2): the id's type slot resolves to a
  registered Relay type (model label via `apps.get_model` +
  `registry.get`; type name via `definition_for_graphql_name`) whose
  recorded strategy permits the payload shape. Envelope: `ConfigurationError`
  → converted at the field boundary to `GraphQLError GLOBALID_INVALID`
  (decode) or mapped to `DecodeResult` statuses (write path). Owned by the
  name-decode/hardening families — seam, not member.
- **Finalize, relation targets** ([finalizer][finalizer]
  `::finalize_django_types` pending walk): every `PendingRelation`'s
  `related_model` has a registered type; otherwise raise
  `ConfigurationError` BEFORE any class object is mutated. Synthesized
  relation connections add a shape arm: an explicit `"connection"` /
  `"both"` over a non-Node target raises at finalize.
- **Construction, connection cache provenance** ([connection][connection]
  `::_connection_type_for`): a warm cache serves only when the caller holds
  the SAME definition object as the entry's provenance; a second definition
  for one target raises `ConfigurationError` (one shape per node type).

GOAL.md migration-note question ("unregistered relation target raises at
finalize — does the RUNTIME guard agree?"): YES, loud at every phase, and
the soft `required=False → None` arm never contradicts it. An unregistered
target cannot reach a resolver: factory targets are rejected at the
construction line; relation targets are rejected at finalize before any
class mutation (the `PendingRelationAnnotation` sentinel otherwise stays in
`__annotations__`, which fails schema build, never a query); wire ids
naming unregistered types are rejected at decode. No silent pk-stub exists
anywhere on these paths — the GOAL.md non-goal holds.

Connected sources read: [list-field][list-field] (both validators +
`DjangoListField` call), [root-relay][root-relay] (`_validate_node_target`,
both factories, `_check_typed_match`, resolvers), [connection][connection]
(factory call, `_connection_type_for`), [relay-types][relay-types] (decode
Steps 1–2, resolve defaults, `_order_nodes`), [types-base][types-base]
(`_is_relay_shaped`), [finalizer][finalizer] (pending walk + raise),
[converters][converters] (`resolved_relation_annotation`),
[mutations-fields][mutations-fields] (`_validate_mutation_target` trio —
seam), [goal][goal] (migration note), [typed-decode][typed-decode] (seam
split). Excluded on strength of body: every other package module (zero rule
vocabulary over the whole-package sweep for the guard tokens).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** All three Relay entry points
   (`DjangoNodeField`, `DjangoNodesField`, `DjangoConnectionField`) ride
   the one validator; `DjangoListField` rides its base. The mutation
   target trio (`_validate_mutation_target` + protocol/ledger probes) is a
   different contract (duck-typed mutation-protocol membership +
   phase-2.5 ledger registration; model-less members allowed) — seam, not
   member. Trigger: a Relay factory validating without the owner.
2. **Sync/async twins.** The construction guard is sync-only dict/identity
   work; no twin exists, none owed. The runtime `required`-flag triple is
   three execution shapes of one upstream contract (below, F2) — each the
   single site for its shape.
3. **Derived rather than repeated knowledge.** Registered-ness derives once
   per construction at the owner (one contained attribute read + one
   registry read, both threaded onward as the returned definition); no
   caller re-reads. `definition.model` / sidecar classes come off that one
   read. Trigger: a second `__django_strawberry_definition__` read at a
   factory.
4. **Inverse / round-trip pairs.** Guard (class → verdict at construction)
   vs decode (wire string → type at runtime) are opposite directions of one
   lifecycle, owned separately (this family vs hardening/decode). They meet
   only in `_check_typed_match` (decoded type `is` construction target —
   relay file-local L2, verified below as seam).
5. **Contracts restated in another medium.** Production (validator +
   callers); oracles (independent per-factory rejection rows naming each
   factory's label — never reading the owner body); projections (docstrings
   verified against bodies; the owner docstring already states the
   load-bearing order + identity rule).
6. **Enforcement by omission.** Every Relay entry point runs the guard:
   both node factories (via the wrapper), the connection factory (direct),
   the list factory (base). Bare node fields (`target_type=None`) skip by
   design — any decoded registered type may resolve, and decode's registry
   arms cover existence. Explicit non-Node relation connections raise at
   finalize; the implicit list-only default stays soft by design (live
   pinned). No member lacks the guard its contract requires: no defect.

### Enumeration

Instrument: whole-package sweep for `_validate_relay_djangotype_target |
_validate_djangotype_target | _validate_node_target | _is_relay_shaped |
is not a registered DjangoType | Relay-Node-shaped` + `def` census per
symbol. Population: 117 `.py` (plan count; no adds/renames).

- `_validate_relay_djangotype_target`: 1 def ([list-field][list-field]:217);
  2 production callers (`_validate_node_target`, `DjangoConnectionField`).
- `_validate_djangotype_target`: 1 def (:128); 2 production callers (the
  Relay validator, `DjangoListField`).
- `_validate_node_target`: 1 def ([root-relay][root-relay]:332); 2 in-file
  call sites (both factories). Pass-through verified (`None,` +
  `field=field` in source).
- `_is_relay_shaped`: 1 def ([types-base][types-base]:546); production
  readers are the Relay validator + two class-creation-time sites (id
  collision guard + annotation synthesis — different contracts, listed).
- `_connection_type_for` provenance check: 1 site ([connection][connection]
  cache-hit arm).
- Oracles: `test_node_field_target_guards` (2 factories × 4 guards),
  `test_non_node_target_explicit_raises` (2 shapes),
  `test_djangolistfield_*guard*` + `test_djangolistfield_rejects_a_target…`
  + fabricated/copied/dropped-identity rows, per-factory
  `Relay-Node-shaped` message rows. All use independent literals.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace proofs map onto the
behavioral rows (8-test selection `execution-verified` in the copy and in
the shared tree; bypass control `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New Relay-shape arm (a third accepted Node-interface spelling) | **1** (`_is_relay_shaped`; the validator body + both callers unchanged — they take the boolean). |
| C2 | Registration-canonicality change (accept inherited definitions; drop the registry-identity check) | **1** (`_validate_djangotype_target`; wrapper + connection follow as consumers — the list_field item's C9, re-derived). |
| C3 | New Relay factory with its own label/message (a future node field) | **0** existing (new consumer calls the owner with label + message; per-factory wording stays at callers by design). Envelope change (raise → return) → **1** + consumer adapter updates (listed). |

## Findings

### F1 — construction-time Relay target guard (CONFIRMED single-owned: no consolidation owed)

- **Contract + variation.** Registered + Relay-Node-shaped + callable
  resolver, at the construction line. Varies on factory label +
  `relay_error_message` only — both stay at callers.
- **Sites + roles.** *Definition*: `_validate_relay_djangotype_target`
  (+ base `_validate_djangotype_target`, predicate `_is_relay_shaped` —
  each 1 def). *Consumers*: `_validate_node_target`, the connection
  factory call (compose by name, verified). *Oracles / projections*: as
  listed.
- **Challenges.** C1 → 1; C2 → 1; C3 → 0. Count > 1 nowhere in one rule.
- **Owner + lifetime (principles 7, 4).**
  [list-field][list-field]`::_validate_relay_djangotype_target` stands:
  both consumers already import from it (no reversed dependency), it is
  the narrowest module every Relay entry point can depend on, and the
  returned-definition threading makes it the canonical-metadata source by
  construction. Stored-derivation lifetime: none — pure per-call guard,
  no cache, memo, or index (`static-reviewed` over all three bodies).
- **Migration.** None — already single. One docstring trigger clause at
  the owner (projection; behavior identical — AST-identity proof below).
- **Distinct behavior (stays separate).** Per-factory wording; the
  `None`-resolver seam (refetch fields take no `resolver=`); the base
  list guard (non-Relay targets are legal for lists).
- **Behavioral proof.** `execution-verified` (WS 8 passed + authorized
  shared-tree 8 passed, zero member edits in flight). `static-reviewed`
  for pass-through shape, oracle independence, docstring prose.
- **Structural gate.** None owed, with proved reason: the bypass control
  (a correct hand-copy of the owner's logic serving `_validate_node_target`
  instead of the call) passes the full 8-test selection — no behavioral
  gate can pin call-unity. Same standard as the verified typed-decode,
  name-decode, and subscription-masking items. Unity rests on the
  def/caller census + triggers T-shape / T-canonical / T-lifecycle below.
  Standing per-factory rejection rows keep failing a lost or weakened arm.
- **Coupling.** None. Adjacent open families untouched; the clause is
  docstring-only.
- **Freshness.** Blob ids below. Any fingerprint change reopens.
- **Reconsideration triggers (recorded at the owner).** T-shape fires on
  a new Relay-shape arm (`_is_relay_shaped` owns the predicate); T-canonical
  fires on a registration-identity change (the base validator owns the
  check); T-lifecycle fires on a guard reading `DecodeResult` statuses
  (row existence lives in the resolve defaults, relation-target existence
  in the finalizer audit — construction answers registered + shaped only).
  Durable homes: the new docstring clause on
  [list-field][list-field]`::_validate_relay_djangotype_target`, this
  finding, and the plan's `## Outcomes` via Worker 0.

### F2 — runtime row-existence envelope (REJECTED consolidation)

- **Contract difference.** Answers "is the visibility-scoped ROW present"
  per request; F1 answers "is the TARGET TYPE registered + shaped" per
  construction. Different inputs (pk + info vs class object), different
  timing (per-request vs import-time), different envelope (`None` /
  `DoesNotExist` under the upstream `required` flag vs `ConfigurationError`
  always). A change to one never moves the other: new row-visibility
  policy touches the resolve defaults; new target-kind policy touches F1.
- **Within-runtime triple.** `required=True → raise / False → None` is
  spelled three times — `_resolve_node_default` (`get`/`first`),
  `_resolve_node_async` (`aget`/`afirst`), `_order_nodes` (per-key
  raise/`get`, shared by both batch paths) — but each is the single site
  for its execution shape of the upstream
  `strawberry.relay.Node.resolve_node(s)` `required` contract (principle 5:
  awaits intervene; single-row Django API vs positional reassembly differ).
  Sharing the two-line verdict across them would be machinery hiding three
  different Django calls.
- **Trigger.** A fourth execution shape adding a fourth spelling, or
  upstream dropping `required`, or a runtime guard reading F1's arms
  (T-lifecycle). Home: this finding + the F1 owner clause; no owner edit
  (nothing to move).
- **Lifetime.** No stored derivation — live manager reads per call.

### F3 — finalize-time relation-target audit (REJECTED consolidation)

- **Contract difference.** Answers "is every DISCOVERED relation target
  registered" for auto-synthesized relations (`PendingRelation` records),
  not "is this factory-supplied class valid". Different population
  (related models reached through fields vs explicitly passed targets),
  different phase (finalize audit, pre-mutation, vs construction line),
  different home ([finalizer][finalizer]). The relation-shape arm
  (explicit connection over non-Node target) is the same phase/population.
- **Trigger.** Factory targets validated via a pending ledger instead of
  a direct registry read, or vice versa. Home: this finding + the F1
  owner clause; the finalizer's own prose already states its rule.

### F4 — connection cache-provenance check (REJECTED consolidation)

- **Contract difference.** Answers "does this caller hold the SAME
  definition object the cached connection class was built from"
  (one-shape-per-type coherence), not "is the target registered".
  Fires only across two constructions over one target with divergent
  definition objects (e.g. across a `registry.clear()` rebuild) — a
  scenario F1's per-construction verdict cannot see.
- **Trigger.** A provenance check reading the registry instead of the
  cache entry. Home: this finding; the existing
  `_connection_type_for` docstring already states the rule, so no owner
  edit (and `connection.py` carries external dirt — left untouched).

### Sibling seams (open families or file-local — stated, not decided)

- Decode/shape (`typed-globalid-decode`, `globalid-decode-input-hardening`,
  `relay-node-name-decode`): wire-input questions; F1 composes nothing
  from them and they read nothing from F1. Verified split:
  shape-vs-existence-vs-policy.
- Visibility policy (cascade/permissions families): row-LEVEL access
  inside an existing target; F1/F2 decide target + presence.
- `_check_typed_match` (decoded type `is` construction target, raising
  code-less `GraphQLError`): re-derived — 1 def, 2 in-file call sites;
  the write side reports non-raising `WRONG_MODEL`. Agree with the relay
  item's L2: file-local, different envelope. Trigger: a third
  wrong-type raise site.
- `relay-node-type-stamp`: downstream consumer of decode routing; never
  guards. Trigger: stamping before decode.
- Mutation-target trio: different contract (protocol + ledger), noted in
  Matrix axis 1. Its in-flight hunk is external to this item; only the
  contract boundary is recorded here.

## Defects

None new. The two stale-name prose references on these paths
(`_decode_relation_id_set` in the `decode_model_global_id` docstring + test
comment; `_coerce_relation_pk_or_none` in the forms module docstring) are
already filed as D1/D2 under Family `typed-globalid-decode` — not re-filed.
Matrix axis 6 found no omission gap.

### D-W2-1 (Worker 2): freshness doc-label rotation (prose-only, blocks nothing)

The `Freshness fingerprints` block (Worker 1) lists
`dry-file-relay.md c5b92c65…`, `dry-file-list_field.md 83180d9a…`,
`dry-file-connection.md 191ba3c7…`. Current `git hash-object` reads
`dry-file-relay.md 191ba3c7…`, `dry-file-list_field.md c5b92c65…`,
`dry-file-connection.md 83180d9a…` — same three blobs as a SET, labels
rotated one step. Package/test/contract fingerprints all match exactly, so no
finding reopens; correction owed at closeout (Worker 0 relabels the three
rows, no re-trace). Filed here, not homed on a card (artifact-prose fix).

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace; the one authorized shared-tree focused run executed green
(8 passed) with zero member edits in flight. No `execution-deferred`
items. `FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by
construction`: every executed claim is construction-time validation plus
default-DB single-alias ORM lookups (the recorded `NAME` is the copy's own
file). Full-suite gate business is deferred to the final-gate item with
reason: the entry authorizes workspace runs plus one focused `--no-cov`
test, and a green unmutated suite would discharge no failability proof for
a confirmation that proposes no gate.

## Judgment

The Relay node-target guard is already one definition:
`_validate_relay_djangotype_target` owns registered + Relay-shaped at the
construction line (C1 → 1, C2 → 1, C3 → 0); the relay wrapper and the
connection factory compose it by name. Runtime row-existence, finalize
relation-target audit, and connection cache provenance answer different
existence questions at different phases with different envelopes —
rejected with difference + trigger + home each. The GOAL.md question
resolves loud-everywhere: construction, finalize, and decode each reject
an unregistered target; `required=False → None` softens rows, never types.
Owner confirmed; one projection-only trigger clause added; no defects.

## Implementation (Worker 1)

Tracked change (1 file, docstring-only):
`django_strawberry_framework/list_field.py` —
`_validate_relay_djangotype_target` docstring gains the T-shape /
T-canonical / T-lifecycle reconsideration-trigger clause (projection;
behavior untouched). Attribution: `list_field.py` clean at `ITEM_BASELINE`
and at HEAD before the edit; no `## Owned changes` row exists on the path;
`relay.py` / `connection.py` hunks attributed above and untouched. Worker 0
appends: `django_strawberry_framework/list_field.py` — Family
`relay-node-target-guard` — `_validate_relay_djangotype_target` docstring
trigger clause (projection; behavior untouched).

Proofs (disposable workspace per [DRY.md][dry] "Tests"; `rsync` copy,
docs excluded; every command via `uv run --frozen --directory "$WS"`):

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-node-target-guard-w1
uv run --frozen --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --frozen --directory "$WS" pytest <8-test selection> --no-cov -n0 -q
```

Copy `__file__`:
`.../dry-ws/relay-node-target-guard-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/relay-node-target-guard-w1/examples/fakeshop/db.sqlite3`
(the copy's own tree and database). Behavioral selection (8 passed in the
copy; 8 passed shared-tree, zero member edits in flight):
`test_node_field_target_guards`, `test_non_node_target_explicit_raises`,
four `test_djangolistfield_*guard*` / `test_djangolistfield_rejects…`
rows. Negative control (same workspace, pristine backup kept, restored
byte-identical via `cmp` and re-verified): bypass mutant inlining a
correct hand-copy of the owner's logic at `_validate_node_target`
(imports rewired to `_validate_djangotype_target` + `_is_relay_shaped`,
no owner call) → selection still 8 passed. No behavioral gate can pin
call-unity; none owed. No source mutation in the proofs; restores N/A
beyond the control backup (removed after restore).

After the edit: `uv run ruff check --fix
django_strawberry_framework/list_field.py` + `uv run ruff format
django_strawberry_framework/list_field.py` — both green (`format --check`
+ `check` pass on the path; scoped to the path so no concurrent dirt is
rewritten). INVERSE proof (docstring-only edit): docstring-stripped AST of
`HEAD:list_field.py` vs worktree — `AST-IDENTITY-NO-DOCSTRINGS: True`
(read-only check, not a test run). Per `AGENTS.md` no pytest after edits;
the pre-edit focused run (8 passed) still discharges the finding by that
AST identity. No `CHANGELOG.md` touch. No commit per standing rule.

Scratch paths (removal is Worker 0's, after `verified`, by explicit path):
`WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-node-target-guard-w1`
(includes its own `.venv`; the control backup was removed after restore).
No manifest (no `prove_failability.py` run — no gate added, none owed; the
hand-proved bypass is the negative control).

Worker 0 rows: tick Family `relay-node-target-guard` (this artifact); no
`## Responsibility index` change needed beyond `open` → decided per the
four findings above (provisional owner + all three member files already
covered); append the `## Owned changes` row above; no defects to home.

Freshness fingerprints (`git hash-object` worktree unless noted; HEAD
`bfaee91d`; `ITEM_BASELINE` `399c797d…` present):
`list_field.py` `ce682d5f…` pre-clause, `d6af6164…` post-clause (docstring-only;
`relay.py` `69085e7a…` (ledgered decode clause; decode lines outside it),
`connection.py` `3c4d5dcb…` (external cursor-guard hunk; guard sites
outside it), `types/relay.py` `52439862…`, `types/base.py` `91c58747…`,
`types/finalizer.py` `77fd9a2d…`, `types/converters.py` `9ceb34af…`,
`types/relations.py` `6bd7c63d…`, `mutations/fields.py` `64410c86…`
(external trio hunk; contract boundary only),
`tests/test_relay_node_field.py` `2fd9e458…`,
`tests/test_relay_connection.py` `b6bd90d9…`,
`tests/test_list_field.py` `2f77f77d…`, `GOAL.md` `7dfbef5c…`,
`dry-rule-typed-globalid-decode.md` `7743927f…`, `dry-0_0_15.md`
`4469dc8d…`, `dry-file-relay.md` `191ba3c7…`, `dry-file-list_field.md`
`c5b92c65…`, `dry-file-connection.md` `83180d9a…`. Searched population:
whole package (117 `.py`) for the guard tokens. Any fingerprint change
reopens the finding.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[goal]: ../../GOAL.md
[typed-decode]: dry-rule-typed-globalid-decode.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[converters]: ../../django_strawberry_framework/types/converters.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[relay-types]: ../../django_strawberry_framework/types/relay.py
[root-relay]: ../../django_strawberry_framework/relay.py
[types-base]: ../../django_strawberry_framework/types/base.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Worker 2 trace, recorded before opening `## Findings` (Run `0.0.15 2026-09-19-1`,
HEAD `bfaee91d`; worktree dirty — see freshness below). Sources read:
`django_strawberry_framework/list_field.py` (full, incl.
`_validate_djangotype_target`, `_validate_relay_djangotype_target`,
`DjangoListField` call site), `django_strawberry_framework/relay.py`
(`_validate_node_target`, `DjangoNodeField`/`DjangoNodesField` call sites,
`DecodeResult`/`_resolve_real_pk`/`resolve_node(s)` dispatch),
`django_strawberry_framework/connection.py`
(`DjangoConnectionField` call site + surrounding guard comment),
`django_strawberry_framework/types/base.py::_is_relay_shaped` +
its three in-file callers, `django_strawberry_framework/types/relay.py`
(decode/`resolve_node` defaults surface), `django_strawberry_framework/types/finalizer.py`
(relation-target audit surface); tests `tests/test_list_field.py`,
`tests/test_relay_node_field.py`, `tests/test_connection.py` (guard rows only);
item-scoped diff `git diff 399c797d72ba6fc6417bc79fec0491e6d4be10e8..0df5cde47c9cc11836bf99b98c982f3a5c2345d1`
and `git diff HEAD -- <three member files>`.

### Guard mechanism per site (what "existence" means, failure envelope)

- `list_field.py::_validate_djangotype_target` — base constructor guard.
  "Existence" = the target is a registered `DjangoType`: `inspect.isclass` →
  `issubclass(DjangoType)` → contained `getattr(target,"__django_strawberry_definition__",None)`
  with own-class `origin is target_type` PLUS registry-canonical identity
  (`definition is registry.get_definition(target_type)`) → callable-`resolver`
  check. Failure envelope = `ConfigurationError` at the line that wrote
  `<field>(...)`, message interpolated with caller `field=` name, values
  rendered via `_safe_arg_repr`/`_safe_class_name` (hostile `__repr__`/`__name__`
  contained), metaclass `__getattr__` non-`AttributeError` contained to the same
  typed reject (fail-closed). Returns the canonical definition from the ONE
  contained read. Role: base definition (owns the 4-guard + canonicality rule).
- `list_field.py::_validate_relay_djangotype_target` — Relay superset guard.
  "Existence" = base-existence PLUS Relay-Node-shaped:
  `definition = _validate_djangotype_target(...)` then
  `if not _is_relay_shaped(target_type, definition.interfaces):
  raise ConfigurationError(relay_error_message)`. Predicate composed BY NAME
  (imports `_is_relay_shaped` from `types/base.py`); error wording supplied by
  caller so each factory names itself; returns the same single definition read
  onward (no second attribute read — stateful-metaclass note in body). Failure
  envelope = base envelope plus the caller-worded shape arm. Role: authoritative
  definition of the relay-target rule (the only place base+shape compose).
- `types/base.py::_is_relay_shaped(cls, interfaces)` — shape predicate.
  `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`.
  Reads declared `Meta.interfaces` (pre-Phase-2.5, before `apply_interfaces`
  injects into `__bases__`) OR direct inheritance. Role: predicate definition
  (owns the shape spelling), CONSUMED by the relay guard by name — not a second
  guard definition. Its other in-file callers (`__init_subclass__` id-collision
  guard, `_validate_connection`/`_validate_meta` gate, `_build_annotations`
  pk-suppression) are distinct rules sharing the token, not the guard.
- `relay.py::_validate_node_target(target_type, *, field)` — thin wrapper.
  Calls `_validate_relay_djangotype_target(target_type, None, field=field,
  relay_error_message=<node wording>)`, discards return (`-> None`).
  In-file calls: exactly 2 (`DjangoNodeField` body, `DjangoNodesField` body;
  bare `None` form skips the call). No `resolver=` seam so `None` passed.
  Role: consumer (enforcement site, boundary adapter naming itself).
- `connection.py::DjangoConnectionField` — pass-through consumer.
  Calls `_validate_relay_djangotype_target(target_type, resolver, field=
  "DjangoConnectionField", relay_error_message=<connection wording>)` once,
  keeps `definition` for `_connection_type_for(target_type, definition)` and
  `_build_connection_resolver(...)` (same-object-by-construction, no second
  read). Role: consumer (enforcement site + definition-thread-through).
- `list_field.py::DjangoListField` — NOT a consumer of the relay guard; calls
  the base `_validate_djangotype_target(..., field="DjangoListField")` once.
  Confirms the relay variant adds exactly one arm over the base.
- What "existence" does NOT mean here: no site checks DB row existence,
  `DecodeResult` statuses (`OK`/`WRONG_MODEL`/`UNCOERCIBLE_PK`/`DECODE_FAILED`),
  `required=` flag behavior, or relation-target resolvability at construction.
  Row existence lives in `relay.py` resolve dispatch (`required=False` →
  `null`; `_order_nodes` positional holes) and `types/relay.py` resolve
  defaults; relation-target existence lives in the finalizer
  (`_synthesize_relation_connections` + unresolved-target audit). Construction
  answers registered + shaped only.

### Definition counts per posited change (Worker 2 own challenges)

- W2-C1 (registration-canonicality change: e.g. drop the
  `definition is canonical` identity arm, or accept an inherited definition):
  count 1 — `list_field.py::_validate_djangotype_target` only. Relay guard,
  node wrapper, connection field follow by construction (they call/delegate).
- W2-C2 (Relay-shape spelling change: e.g. accept a third shape arm such as a
  custom `@strawberry.interface` subsuming `relay.Node`, or reject direct
  inheritance): two layers distinguished. (a) Predicate spelling → count 1 at
  `types/base.py::_is_relay_shaped` (guard follows as consumer by name).
  (b) Guard wiring (which predicate, when applied, whose wording) → count 1 at
  `list_field.py::_validate_relay_djangotype_target` (callers follow). No
  second guard body spells the shape inline — verified by source read
  (both callers import, neither re-derives from `_meta` nor concatenates names).
- W2-C3 (require live row/relation-target existence at construction: e.g.
  refuse a target whose table is empty, or read `DecodeResult` statuses in the
  constructor): count 0 — no construction-time site does this. Would be a NEW
  behavior (axis-6 enforcement-by-omission question, contract source required),
  not a consolidation. This matches the T-lifecycle trigger framing.

### Owner Worker 2 would choose

`django_strawberry_framework/list_field.py::_validate_relay_djangotype_target`
(keeping `_is_relay_shaped` where it is). Reasons (principle 7): the rule is
"a field factory may bind only a registered Relay-shaped target" — a
field-construction contract, not a type-system predicate nor a transport rule.
`list_field.py` already owns the base 4-guard contract (spec-020 home statement;
both siblings already import from it), so the superset is the narrowest
cohesive extension every legitimate consumer (`relay.py`, `connection.py`) can
depend on without reversing a dependency or importing a sibling flavor for its
machinery. Dependency direction wins: `relay.py`→`list_field.py`,
`connection.py`→`list_field.py`, `list_field.py`→`types/base.py` (predicate
only). Moving the guard into `types/base.py` would drag field-factory wording
(`field=`, `relay_error_message=`, `resolver=` seam) into the type layer;
moving it into `relay.py` would make `connection.py` import a sibling flavor.
Predicate stays at `types/base.py` (shared with id-guard/pk-suppression/
`Meta.connection` gate — distinct rules, one token, composed by name).

### Freshness (Worker 2 fingerprints at trace time)

- Worktree blobs: `list_field.py d6af6164…` (= ITEM-current `0df5cde4…` blob;
  HEAD `ce682d5f…`; delta = +8 docstring trigger clause only),
  `relay.py 69085e7a…` (HEAD `c3c5aea5…`; delta = +5 `typed-globalid-decode`
  trigger clause from the sibling family — outside this item, left alone),
  `connection.py 3c4d5dcb…` (HEAD `93e998f2…`; delta = +65 cursor-guard
  `_offset_cursor_prefix`/`_reject_negative_offset_cursor` + fallback-branch
  call — outside this item, left alone), `types/base.py 91c58747…` (= HEAD,
  clean).
- Searched population for sibling guards: `grep _validate_.*target` over
  `django_strawberry_framework/` + `grep ConfigurationError` raise sites in the
  three member files; full-file reads above. No second construction-time
  registered+shaped body found (see sibling sweep in verdict section).

### Reconciliation (Worker 2, after opening `## Findings`)

Agreement/difference per reconciliation point (re-derived, then judged):

- Single definition: AGREE. AST census package-wide: exactly 1 `def`
  each of `_validate_relay_djangotype_target`, `_validate_djangotype_target`
  (both `list_field.py`), `_validate_node_target` (`relay.py`),
  `_is_relay_shaped` (`types/base.py`). Relay validator delegates to base then
  one `_is_relay_shaped` call composed by name; no caller re-spells a guard.
- Consumers: AGREE. `relay.py::_validate_node_target` has exactly 2 in-file
  calls (`DjangoNodeField`, `DjangoNodesField`; bare-`None` form skips by
  design); `connection.py::DjangoConnectionField` has exactly 1 call and
  threads `definition` onward to `_connection_type_for`/`_build_connection_resolver`
  (pass-through, no second read). `DjangoListField` calls the base only —
  confirms the relay variant adds one arm.
- Rejections: AGREE (all three carry difference + trigger + home).
  F2 runtime row-existence (`required`-flag triple: sync/async/`_order_nodes`
  as three execution shapes of the upstream contract, principle 5);
  F3 finalize relation-target audit (`PendingRelation` population, pre-mutation
  phase, finalizer home); F4 connection cache-provenance (same-object
  coherence across rebuilds, fires only where F1 cannot see). Homes and
  no-owner-edit reasons verified.
- Challenges C1→1, C2→1, C3→0: AGREE on counts, DIFFER on third-axis choice
  (not a defect). Artifact C3 = new factory with own label → 0 existing
  (principle-1 declaration axis); W2-C3 = row-existence-at-construction → 0
  (lifecycle axis). Both valid; counts coincide as a set {1,1,0}.
- Owner `list_field.py` (principle 7): AGREE (see owner reasoning above;
  dependency direction `relay.py`→`list_field.py`,
  `connection.py`→`list_field.py`, `list_field.py`→`types/base.py`
  predicate-only; spec-020 home statement).
- Already-single +8 docstring trigger clause (T-shape/T-canonical/T-lifecycle):
  AGREE. `git diff HEAD -- list_field.py` shows exactly the 8-line clause,
  nothing else; `git diff ITEM_BASELINE..CURRENT` shows the same +8 with
  `relay.py`/`connection.py` empty in that range. AST-identity-no-docstrings
  HEAD-vs-worktree: True (recomputed by W2). Clause is projection; behavior
  untouched.
- No defects (typed-decode D1/D2 deduped, not re-filed): AGREE. No new
  omission gap (axis 6: both node factories, connection factory, list base
  all guarded; bare-`None` skip and implicit list-only default by design with
  contract sources). One W2 prose defect filed above (D-W2-1 label rotation).
- No pending execution: AGREE. All proofs `execution-verified` (WS 8 passed +
  shared-tree 8 passed, zero member edits in flight per record); no
  `execution-deferred` item exists to list. `FAKESHOP_SHARDED=1`/Postgres
  `inapplicable by construction` accepted: executed claims are
  construction-time `ConfigurationError` verdicts plus default-DB single-alias
  reads (copy `__file__` + `NAME` recorded); reason stated by W1, judged
  sufficient. Full-suite gate correctly deferred to the final-gate item.
- No structural gate (bypass-mutant 8-green): CONCUR. A correct hand-copy
  serving `_validate_node_target` passes the same 8-test selection, so no
  behavioral gate CAN pin call-unity (same standard as the verified
  typed-decode/name-decode/subscription-masking items). No population census
  named: a `def`-name census would miss an inline re-spelling without a `def`;
  a literal/`ConfigurationError`-wording census is noisy by design
  (per-factory wording stays at callers); an import-identity assertion on the
  wrapper would be a bespoke per-helper existence test, which DRY.md forbids
  for gate-only findings. Unity rests on the def/caller census + T-triggers;
  correctness of each arm rests on the standing per-factory rejection rows
  (which fail a lost/weakened arm). None owed.
- Proofs in WS + shared-tree focused run: ACCEPTED on record (copy `__file__`
  + DB `NAME` both inside `$WS`, 8 passed each, control restored
  byte-identical via `cmp`). Not re-executed by W2: entry authorizes WS runs +
  one focused `--no-cov` test, and AGENTS.md bars pytest unless explicitly
  asked — this task asks for ruff only (run below). The docstring-only edit
  is discharged by the recomputed AST identity.
- Connection dirt zero-overlap, untouched: AGREE. `git diff HEAD --
  connection.py` = `from_base64` import + `_offset_cursor_prefix` +
  `_reject_negative_offset_cursor` + non-queryset fallback-branch call (+65);
  none touches the `_validate_relay_djangotype_target` call,
  `_connection_type_for`, `_guard_source_not_pre_sliced`, or
  `_resolve_order_path_field`. `relay.py` dirt = sibling-family +5 decode
  clause only. Neither edited by this item.

### Sibling-validator sweep (Worker 2, construction-time existence check?)

Question: is there truly no second construction-time registered+shaped check?
Swept `def _validate_*target*` package-wide + `raise ConfigurationError` in
the three member files + `is not a registered DjangoType` /
`Relay-Node-shaped` literals package-wide. Result: no second body.

- `mutations/fields.py` trio (`_validate_mutation_target`,
  `_has_mutation_protocol`, `_is_registered_mutation_target`): different
  contract (duck-typed mutation-protocol membership + phase-2.5 ledger;
  model-less members allowed). Seam, not member.
- `types/base.py` trio (`_validate_nullability_override_targets`,
  `_validate_filesystem_path_targets`, `_validate_relation_shape_targets`) +
  `_validate_connection`/`_validate_globalid_strategy`/`_validate_filterset_class`:
  `Meta`-key target validation at type-creation/finalize; distinct populations
  and phases. Not the factory-target guard.
- `filters/base.py::RelatedFilter._validate_target`,
  `orders/base.py::RelatedOrder._validate_target`,
  `sets_mixins.py::_validate_target`: resolved-value gates, not
  construction-time class guards. Different envelope.
- `management/commands/inspect_django_type.py` "not a registered DjangoType"
  strings: CLI `CommandError` introspection tool (operator surface), not a
  field-construction `ConfigurationError`. Distinct contract/tool.
- `filters/sets.py` Relay-aware filter selection, `finalizer.py`
  `_synthesize_relation_connections` shape arm, `types/base.py` id-guard /
  pk-suppression / `Meta.connection` gate: share the `_is_relay_shaped` TOKEN
  for distinct rules (filter-instance choice, synthesis eligibility,
  type-creation gates). Composed by name; counted zero as guard definitions.
- `connection.py::_connection_type_for` provenance arm + `relay.py`
  `_check_typed_match` + runtime `required` triple + finalizer pending walk:
  per F2/F3/F4/L2 — rejected/separate with triggers, not second definitions.

### Owner-edit judgment (Worker 2, run myself)

- `uv run ruff format --check django_strawberry_framework/list_field.py` →
  already formatted. `uv run ruff check django_strawberry_framework/list_field.py`
  → all checks passed. Same both-green on `relay.py` + `connection.py`
  (untouched, confirming no collateral reformat).
- Prose: +8 clause carries no process provenance (no worker/run/baseline/
  timestamps), cites `types/base.py::_is_relay_shaped` + same-file base
  sibling + lifecycle homes (`types/relay.py` resolve defaults, finalizer
  audit) — consistent with this file's established short-path docstring
  style; ASCII-only; lines within length. No test tier owed (behavior
  identical by AST identity). No `CHANGELOG.md` touch (not authorized).
- AGENTS.md diff rules: `path::Symbol` citations present where cross-file,
  test tier N/A for projection-only, no pytest run by W2 per standing rule.

### Freshness re-hash (Worker 2)

`git hash-object` worktree now: `list_field.py d6af6164…` (post-clause;
HEAD `ce682d5f…`), `relay.py 69085e7a…`, `connection.py 3c4d5dcb…`,
`types/relay.py 52439862…`, `types/base.py 91c58747…`,
`types/finalizer.py 77fd9a2d…`, `types/converters.py 9ceb34af…`,
`types/relations.py 6bd7c63d…`, `mutations/fields.py 64410c86…`,
`tests/test_relay_node_field.py 2fd9e458…`,
`tests/test_relay_connection.py b6bd90d9…`,
`tests/test_list_field.py 2f77f77d…`, `GOAL.md 7dfbef5c…`,
`dry-rule-typed-globalid-decode.md 7743927f…`, `dry-0_0_15.md 4469dc8d…`
— all match the artifact. `dry-file-relay.md 191ba3c7…`,
`dry-file-list_field.md c5b92c65…`, `dry-file-connection.md 83180d9a…`
match as a SET with labels rotated (D-W2-1 above); no package/test finding
depends on those doc blobs. `ITEM_BASELINE 399c797d…` present
(`git cat-file -t` = commit). No fingerprint change on any load-bearing
input: nothing reopens.

### Pending execution judgment (Worker 2)

`## Pending execution`: None — CORRECT. No `execution-deferred` proof exists;
no `gate:` witness is owed by this finding (the bypass negative control
already executed in WS; a green unmutated suite would discharge nothing).
Sharded/Postgres correctly marked inapplicable with reason. Full suite stays
with the final gate.

Verdict: `verified`. No production edit owed; the +8 projection stands;
D-W2-1 is prose-only for Worker 0 closeout.
