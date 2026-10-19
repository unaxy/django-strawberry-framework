# DRY review: `orders/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights in slot-2 only). Audits the
unassigned remainder of the `orders/` folder and the families that
cross its ownership boundaries at current bytes (HEAD `23b5f421` +
working tree). The five member file artifacts are run-5/run-6 era
inputs, not verdicts: every assignment below was re-derived fresh at
WT bytes, and every assignment the tree has falsified is flagged as a
finding inside this item for the closeout defect-homing pass. No prior
artifact is summarized and no row is reopened.

Verdict: zero-edit CONFIRM. 18 cross-file compositions hold by name
(FC-1..FC-18, each with a fresh census); 31 merges rejected with
triggers (FR-1..FR-31, 17 converging on standing member rejections
whose triggers were re-checked against current bytes); 6
tree-falsified prior assignments flagged for closeout (FF-1..FF-6,
rows not reopened); 0 FAM-N (the strongest twins — the visible-rows
colorings and the `field_name`-fallback trio — re-traced fresh and
held separate on coloring-contract and read-posture evidence, FR-1 /
FR-2); 0 new defects (all seven member D1s re-verified persisting,
riding to closeout); 0 new Family-hold rows (f33 persists
owed-but-blocked on hunt-dirty lines and is already rowed open).
The 240-row `tests/orders` suite runs green in slot-2 at current
bytes.

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da`.
`ITEM_BASELINE=8add57f948d9d14c9a0378bb53a144e52c929d7e`
(resolves as a commit; all five orders blobs equal the working tree
as dispatched, so BASE=WT pre-edit for every target). Slot-2
(`dry/folder-orders/consolidate`) verified byte-identical to WT on
all five targets before tracing and again after the witness suite
(the suite wrote no source). Blob fingerprints are `git hash-object`
(WT = BASE) and `git rev-parse HEAD:<path>` (HEAD), short-8:

| File | Lines | WT = BASE | HEAD | State |
|---|---|---|---|---|
| `orders/__init__.py` | 149 | `e835e9b3` | `e835e9b3` | clean |
| `orders/base.py` | 168 | `5dcc88e0` | `96767f4e` | dirty |
| `orders/factories.py` | 83 | `5319f33a` | `5319f33a` | clean |
| `orders/inputs.py` | 412 | `1ed19c1f` | `535eb96c` | dirty |
| `orders/sets.py` | 1080 | `fd453bec` | `2d35adfa` | dirty |

Item-scoped diff (`ITEM_BASELINE` → WT over the folder): empty. This
item landed zero edits in slot-2 and zero in the shared tree; the
three dirty files' WT-vs-HEAD hunks are attributed below, none made
here.

## System trace

The folder owns ordering end to end: the declaration primitive
(`base.py`: deferred family base, `RelatedOrder` adapter + gate +
`field_name` shape), the input namespace (`inputs.py`: `Ordering`
vocabulary, substrate aliases, module-path constant, namespace
lifecycle, leaf converter, triples builder, whole-value normalizer +
provenance gate, `__all__` helper), the BFS factory
(`factories.py`: bare-triples hook over the shared walk), the set
lifecycle + resolver pipeline (`sets.py`: ledger, return gate,
metaclass, expansion, guard, delegate, permission config, flat walk,
term selection, scope resolution, expression resolver, visible-rows
pair, pipeline tail + colorings, naming posture), and the 6-name leaf
manifest + Decision-11 helper spellings (`__init__.py`). Data flows
declaration → expansion → BFS input build → materialization →
normalize → permission gates → resolve → `order_by`. Every
cross-folder seam (BFS walk, emit scaffold, namespace quartet,
traversal mechanics, naming rule, lifecycle skeleton, gates,
collector, path classifier, visibility appliers, predicate kit,
relation walk, sync boundary, clear bus) is owned outside and
composed by name.

Member-file inputs re-derived at current bytes (not inherited):
[file-init][file-init], [file-base][file-base],
[file-factories][file-factories], [file-inputs][file-inputs],
[file-sets][file-sets]. Where the tree falsified an assignment the
record sits under Findings as FF (flag for closeout; no row
reopened, nothing re-applied). Run-5/run-6 blobs (`ed546f9c`,
`4736fda0`, `4f35b66b`, `6f6ec946`, `6044ab1a`) all resolve in the
object store and were diffed against WT to separate committed
evolution from concurrent dirt.

### Attribution of the working-tree dirt (by diff content vs HEAD)

One provenance: concurrent bug-hunt work (the `truth.*` identity-read
migration). The `## Owned changes` ledger names zero `orders/`
paths, so every WT-vs-HEAD hunk below is external. Never edited,
reverted, or tidied here; the two clean files (`__init__.py`,
`factories.py`) carry zero dirt.

- `base.py` (3 hunks): `_safe_*` import → `truth` import;
  `_validate_target` predicate + label + message reads through
  `truth.*`; one docstring clause naming the `truth` posture.
- `inputs.py` (4 hunks): `_safe_*` import → `truth` import +
  `models`/`Options` TYPE_CHECKING imports;
  `_get_concrete_field_names_for_order` guard + message through
  `truth.*` with a `cast` + comment; `normalize_input_value` leaf
  message through `truth.*`.
- `sets.py` (10 hunks): `_safe_*` import → `truth` import +
  `Mapping` TYPE_CHECKING import; `claim` / `_validate_normalized_terms`
  (×2) / `__all__` gate / entry check / path check / guard verdicts
  (×2, the f33 arms) / resolve guards (×2, now in
  `_active_order_terms`) label + message reads through `truth.*`;
  `get_fields._build` related-map read + `_expand_meta_fields`
  `Meta`/`model` reads through `truth.static_attr` with casts.

`utils/truth.py` itself exists on disk but is untracked and absent
from HEAD (`File utils/truth.py` stays blocked); the migration is
unlanded by definition.

## Verification

### Matrix

1. Cross-flavor: every filter twin re-read fresh at current bytes
   (base gate + loader + `get_queryset`, inputs converter +
   normalizer + builder, factory hook, sets build + normalize +
   apply + metaclass + `get_fields`, `__init__` helper twin,
   `_permission` config). The order side composes shared owners by
   name and declares per-family adapters; all fifteen twin
   separations re-derive with unmet triggers (FR-17..FR-31). The
   `field_name or <fallback>` idiom spans three read postures
   (FR-2); the `truth.*` read idiom is hunt-owned migration
   vocabulary, not a package rule. Discharged.
2. Sync/async: the folder carries exactly two `async def`
   (`apply_async`, `_visible_rows_async`) and four `await` lines,
   all in `sets.py`; the other four files carry zero. No
   twinship: `apply_async` shares the one uncolored tail
   (F-APPLY), and the visible-rows pair splits on a
   coloring-forced seam (lazy sync derive vs upfront async
   derive — FR-1). Discharged.
3. Derived knowledge: every same-token population in the folder was
   walked on body strength. Genuine single owners with by-name
   composers: the leaf manifest (6 names), the helper body (2
   spellings), the BFS hook delegate (2 callers), the triples
   builder (2 callers), the normalizer (1 delegate +
   self-recursion), the provenance gate (2 callers),
   the traversal table (1 holder + walker), the column helper (1
   caller), the gate base (1 caller), the ledger recorder (3
   attestation points), the return gate (3 call sites), the term
   selector (2 consumers), the scope resolver (2 consumers), the
   expression builder (1 caller), the pipeline tail (2
   colorings), the direction vocabulary (2 consumers of the
   discriminator). The visible-rows pair (FR-1), the fallback
   trio (FR-2), the recourse wording (FR-3), the separator
   spellings (FR-4), and the prefix pair (FR-5) are distinct
   contracts with triggers. Discharged.
4. Round-trip: getters/setters compose one mixin seam (validation
   on read, documented at the owner); `Ordering.resolve` is
   encode-only (no `OrderBy` → direction decode exists);
   materialize idempotency + collision raise are one directional
   pin at the quartet owner; the ledger publish/claim halves are
   one co-located grammar. Discharged.
5. Other media: package oracles (`tests/orders/`, 7 modules, 240
   rows, all green in slot-2 at current bytes,
   `dry-20261010T044357-deebfa`), live `/graphql` rows (the
   `orderBy:` suites pin wire behavior), projections
   (module/class/method docstrings; the seven member D1s ride to
   closeout per `## Defects` and are never fixed here). No medium
   carries a second definition of a folder rule. Discharged.
6. Omission: all five files enumerated below; every member lands
   in a verified family row, a member-artifact assignment
   re-verified at current bytes, or one of this item's
   transcribed rows. No unassigned member remains. Discharged.

### Enumeration

Instrument: `ast` top-level census (`len(ast.Module.body)`, def /
assign split) over the folder at WT bytes, plus `grep` composer
censuses for every cross-file read. Every member below lands in a
verified family row (f-numbered), a member assignment re-verified
at current bytes, or one of this item's transcribed rows (T-numbers
in `## Index rows for Worker-0`).

| File | Top-level members | Homes |
|---|---|---|
| `__init__.py` | 16 stmts, 4 defs, 3 assigns | `orders-leaf-manifest` (6 names now, FF-2) + `orders-decision-11-leaf-parameters` (T-1 spelling pair; bindings intact) + ledger member (verified family) + R-leaf-vs-root stands (FR-30) |
| `base.py` | 10 stmts, 2 defs, 0 assigns | F1/F2/F3/F4 converge (deferred base / adapters / gate / `field_name`) + R-base twins stand (FR-26..FR-29); D1 stands (rides) |
| `factories.py` | 9 stmts, 1 def, 0 assigns | F-1/F-5c converge (BFS declarations / clear membership) + R-bag/R-mutid stand (FR-19/FR-31); Layer-6 subjects deleted (FF-1); D1 stands (rides) |
| `inputs.py` | 32 stmts, 8 defs, 9 assigns | F-ENUM/F-ALIAS/F-PATH/F-CONC/F-CONV/F-NORM/F-ENS converge + F-BFS/F-NS convergences + R-conv/R-norm/R-build/R-guards stand (FR-17/FR-18/FR-19/FR-15); D1/D2 stand (ride) |
| `sets.py` | 41 stmts, 9 defs, 5 assigns | F-LEDGER/F-VALIDATE/F-META/F-EXPAND/F-ACTIVE/F-NORMDEL/F-PERM/F-FLAT/F-RESOLVE/F-APPLY/F-LIFE/F-NAME converge + f33 persists blocked + R-m1..R-m4/R-EXPAND/R-LEASE/R-CLAIM stand (FR-20..FR-25/FR-16) + T-2..T-6 (5 new rules) + FF-3/FF-5/FF-6; D1/D2/D3 stand (ride) |

### Challenges

Authoritative definitions only; consumers, oracles and projections
that also move are listed, never counted. Current bytes.

- C1 leaf-manifest membership → 1 per home module (6 import rows
  follow by name); root omission → 0 here (FR-30).
- C2 helper form → 1 (the driver; 0 here); helper wording → 1
  (the leaf body; filter twin untouched).
- C3 spelling change → 1 (`_order_input_annotation`; both
  spellings follow — T-1).
- C4 BFS substrate (queue/collision/guard) → 1 (the base; 0
  here); ninth hook attr → 1 + 2 family declarations.
- C5 emission mechanics → 1 (the emit scaffold); related-path
  closure → 1 here (FR-2 keeps the trio split).
- C6 leaf semantics / recursion / check → 1 here; traversal
  mechanics → 1 (the walker + config owner).
- C7 provenance-gate trigger → 1 here (no filter twin — FR-13).
- C8 clear contract → 1 (bus + quartet owner; 0 here).
- C9 family-base rename/edge → 1 here (FR-26 keeps the twin).
- C10 bind/resolve policy → 1 (the mixin; 0 here); slot rename →
  1 (the param; `target_slot=` follows).
- C11 target-kind/wording → 1 here (FR-28 keeps the twin).
- C12 `field_name` required → 1 here (no counterpart).
- C13 ledger claim/close/shape → 1 here each (FR-25 keeps the
  lease).
- C14 return shape/strictness → 1 here (FR-15 keeps the seams).
- C15 metaclass policy → 1 here; machinery → owners (FR-23 keeps
  the twin).
- C16 publish/selection/branch → 1 at the owning site each
  (FR-20/FR-24 keep the twins).
- C17 guard sense/structure → 1 here (FR-14 keeps the polarity
  pair split; verdicts route to f33).
- C18 delegate target/obligation → 1 here.
- C19 traversal axis → 1 declaration here; warm-up → 1 here.
- C20 flat-walk shape/prefix → 1 here (0 production non-default
  callers, re-censused).
- C21 term selection (None-filter + guards) → 1
  (`_active_order_terms`; 2 consumers — T-2).
- C22 scope resolution → 1 (`_scoped_hops`; 2 consumers — T-3).
- C23 visible-rows seed/derivation → 1 per coloring (FR-1:
  laziness is coloring-forced; the seed line is a call-shaped
  composition over a 5-site idiom).
- C24 aggregate/alias → 1 (`_resolve_order_expressions`; sole
  emission site, re-censused).
- C25 pipeline stages → 1 (the tail; both colorings follow);
  boundary → 1 (the boundary owner); dispatcher → absence holds
  (zero `def apply`, re-censused).
- C26 naming posture → declaration here; rule → 1 (the mixin).
- C27 purity verdict/compare → 2 here (the f33 arms; blocked —
  no edit).
- C28 enum members/discrimination/resolve → 1 here each (the
  `str | Expression` widening stays in the owner).
- C29 module-path rename → 1 here (quartet + emit + helper
  follow; FR-9 keeps the twin constant).
- C30 column selection → 1 here (sole production caller,
  re-censused).
- C31 leaf-annotation shape → 1 here (FR-17 keeps the ladder).
- C32 recourse wording → 1 here (FR-3 keeps the template).
- C33 substrate rename → 0 here (5 declarations follow).
- C34 ledger-vs-lease merge → separation stands (FR-25).
- C35 claim-vs-guard verdicts → split stands (FR-16).

## Findings

### Compositions (each holds by name at current bytes)

Leaf and helper. FC-1 manifest: the 6 `__all__` names compose
their homes by name (1 from `base.py`, 1 public from `inputs.py`,
2 from `sets.py`, `order_input_type` + `OrderInput` defined here);
the root still carries zero orders imports (re-grepped) and the
factory still stays out (FR-30). FC-2 helper body:
`_order_input_annotation` passes all six driver kwargs
(`expected_base`, `helper_spelling`, `expected_label`, `ledger`,
`input_type_name_for`, `module_path` — signature re-read at the
driver); `order_input_type` and `OrderInput.__class_getitem__`
are one call each with their spelling (T-1). FC-3 ledger: the leaf
declares set + clear fn + bus row (`orders.helper_references`);
the driver writes (`utils/inputs.py` ledger add, re-read) and the
finalizer reads (function-local import + orphan check, re-read).

Factory and emission. FC-4 hook: `OrderArgumentsFactory` declares
8 hook attrs + 2 caches and returns `_build_input_fields(...)`
bare (R-bag stands, FR-19); the BFS walk/collision/cache/guard
stay at the base (re-grepped: exactly 2 direct subclasses).
FC-5 emission reads: `_build_input_fields` reads
`orderset_cls.get_fields()` (sets), `entry.orderset` + `entry.field_name`
(base), and the quartet/emit owners — 2 production callers of the
builder itself (the hook + `_ensure_field_specs`, re-censused).

Normalization. FC-6 delegate: `OrderSet._normalize_input` is one
call to `normalize_input_value` (sole production caller besides
self-recursion, re-censused). FC-7 provenance gate:
`_ensure_field_specs` warms from the normalizer entry + the
permission warm-up hook (both call sites re-censused; no filter
twin — verified absence). FC-8 traversal table: `_permission`
holds `_field_specs` by reference; the normalizer and the facade
walkers classify through the one `_input_traversal` derivation.

Expansion. FC-9 column helper: `_expand_meta_fields` is the sole
production caller of `_get_concrete_field_names_for_order`
(re-censused); the `__all__` model-require + loop stay here.
FC-10 metaclass: `OrderSetMetaclass` collects `RelatedOrder`
(base) with MRO-merge + owner bind through the shared collector
and resolves `Meta.fields` through the shared write-back (pure
read, re-verified). FC-11 gate base: `_validate_target` is the
sole caller of `_order_set_class` (re-censused); the
`orders.sets → orders.base` edge still forces the deferral
(module-top back-import re-verified). FC-12 slot consumer:
`should_cache_expansion(target_slot="_orderset")` names base's
slot to query string-laziness, never reading a class through it.
FC-13 branch guard: `_build` reads `_expand_meta_fields().keys()`
through `_order_paths` (new since run-6, committed) into the one
`reject_captured_branches` owner.

Pipeline. FC-14 attestation: the one recorder serves 3
attestation points in `_apply_orderings`; the guard claims; the
list field is the sole scope opener (function-local import,
re-read) and the guard's sole production caller (re-censused).
FC-15 stages: both colorings run request → permission checks →
`_prepared_orderings` → `_apply_orderings` (new stage split,
committed; T-5); the tail filters via `_active_order_terms`
(T-2), scopes via `_scoped_hops` (T-3), builds via
`_resolve_order_expressions`, and reads rows via the visible-rows
pair (T-4). FC-16 direction vocabulary: `is_ascending` feeds
`resolve` + the Min/Max pick; `resolve` feeds scalar and
aggregate terms (sole aggregate-emission site + `_dst_order_`
prefix, re-censused).
FC-17 namespace: quartet unpack + one-line wrappers + bus row
(`orders.input_namespace`, `before_bind=True`); factory caches +
`_lifecycle` binding attrs reset through it, helper ledger
through its own row.
FC-18 naming: the BFS names via the `_input_type_name_for`
delegate → the mixin rule (0 definitions here); `OrderSet`
still carries no `_field_type_suffix` override (re-grepped:
docstring mention only).

### FAM verdict: none raised

Thirty-one twin hypotheses were traced to a verdict; every one
resolves to single ownership, a standing rejection with an unmet
trigger, or a distinct contract (FR-1..FR-31). The two load-bearing
near-misses are FR-1 (the visible-rows colorings share the seed
line and the derive-once shape, but laziness is coloring-forced:
the async half must await every scope up front because no await
may live in the sync tail, while the sync half derives on demand;
the seed is a call-shaped composition over a 5-site idiom whose
alias source varies per site) and FR-2 (the `field_name`-fallback
trio shares the `or`-default skeleton, but the three sites differ
in predicate — `is None` vs `or`-falsy — in read posture —
cross-family `object | None` hop vs asserted same-family entry —
and in consumer — match vs span length vs emission path). The
f33 twin verdicts persist but are already rowed open+blocked, so
no new Family-hold row is owed: no consolidation is blocked
beyond what the plan already rows.

### Rejections (each re-derived fresh; triggers re-checked)

Folder-fresh:

- FR-1 visible-rows colorings: lazy sync closure+memo vs upfront
  async pre-derive + `__getitem__` map; eagerness is
  coloring-forced, the seed line composes two owners. Trigger: a
  third seed site or the seed gaining logic.
- FR-2 `field_name`-fallback trio: walk matcher (`is None`,
  segment matching) vs span length (`or`-falsy, ORM-span count)
  vs emission source (cast entry, django path). Trigger: the
  walk adopting one shared typed accessor the span and emission
  readers both use.
- FR-3 recourse wording vs pipeline template: related-term
  read-path recourse (async alternative offered) vs write-pipeline
  template (no alternative). Trigger: the read path collapsing
  into the write template.
- FR-4 separator spellings: `f"{prefix}__{child_path}"` vs
  `LOOKUP_SEP.join(...)` — Django owns the value; raw `"__"`
  splits/joins are pervasive (connection, filters, keyset).
  Trigger: a package decision routing all separator spellings
  through one owner.
- FR-5 prefix pair: flat re-prefix (`""`-join, default empty)
  vs recursion prefix (`__`-join, tree walk). Trigger: a shared
  path-prefix grammar.
- FR-6/FR-7 exact-type predicates: `_is_normalized_term` +
  container check + entry check guard three seams with
  per-seam subjects (standing J2 class). Trigger: a shared gate.
- FR-8 spelling-pair merge: two spellings, one leaf body, one
  driver; the filter twin mirrors the shape. Trigger: the
  families merging.
- FR-9 module-path constants: per-family values pinning
  per-family modules. Trigger: none by construction (values
  differ).
- FR-10 helper ledgers: disjoint per-family sets under one bus
  (verified family membership, not a merge). No trigger.
- FR-11 `_permission` configs: per-family declarations
  (list+UNSET vs logic-keys). Trigger: the families merging.
- FR-12 `_lifecycle` descriptors: per-family slot declarations
  over the shared derivation (worked-example shape). No trigger.
- FR-13 warm-up hook vs filter absence: verified absence (2
  `def` sites: mixin + this override). Trigger: filters gaining
  lazy specs.
- FR-14 None polarities: `direction is not None` (guard) vs
  `direction is None: continue` (selection) — opposite
  spellings of one 3-token check; a helper is machinery.
  Trigger: the check gaining logic.
- FR-15 R-guards three-seam split (CONVERGE inputs row): value
  check (`isinstance`, names field) vs return gate
  (exact-type, names `_normalize_input`) vs term guards
  (`isinstance`, names path — now in `_active_order_terms`,
  FF-3). Trigger: the pipeline collapsing to one point.
- FR-16 claim-vs-guard verdicts (CONVERGE sets R-CLAIM):
  inter-application middle vs same-input middle; middles
  re-read, still distinct. Trigger: the events collapsing.

Member-twin re-verifications (each body re-read fresh):

- FR-17 R-conv (CONVERGE inputs row): fixed `Ordering | None`
  vs the 11-arm kind ladder (MRO dispatch re-read). Trigger:
  per-type order leaves.
- FR-18 R-norm (CONVERGE inputs row): whole-value walk `(cls,
  value) → pairs` vs per-instance dispatch `(instance, raw) →
  scalar/list/patch` (signatures re-read). Trigger: one shared
  walker entry.
- FR-19 R-build + R-bag (CONVERGE inputs + factories rows):
  direct triples + bare hook vs grouped bags + HIDE skip +
  operator splice (both bodies re-read). Trigger: orders
  gaining a bag.
- FR-20 R-m1 (CONVERGE sets row): merge-only `_build` vs
  snapshot + `base_filters` + `on_reentry` publish (twin
  lines re-read). Trigger: a publish change moving both.
- FR-21 R-m2 (CONVERGE sets row): delegate + return gate vs
  self-walk + kind dispatch + RELATED strip (twin body
  re-read; covers the W2 twin row one level up). Trigger: a
  normalize change moving both.
- FR-22 R-m3 (CONVERGE sets row): one tail vs prelude/finalize
  split (twin defs re-grepped). Trigger: twin await points
  collapsing.
- FR-23 R-m4 (CONVERGE sets row): plain `type` + MRO-merge vs
  django-filter subclass + declared stream (twin class line
  re-read). Trigger: a construction change moving both.
- FR-24 R-EXPAND (CONVERGE sets row): self-derive branches vs
  upstream narrow + per-field expansion (twin body re-read).
  Trigger: one shared Meta-reader.
- FR-25 R-LEASE (CONVERGE sets row): append-only ledger +
  lock tombstone vs one-payload one-store lease (both bodies
  re-read; the lease docstring still states the split).
  Trigger: the ledger collapsing to one payload.
- FR-26 deferred bases (CONVERGE base row): per-family edges
  (`orders.sets→orders.base` vs `filters.sets→filters.base`;
  twin body re-read). Trigger: both edges going safe.
- FR-27 adapter merge (CONVERGE base row): mixin-only vs
  mixin + `ModelChoiceFilter` bases; `field_name` vs
  `lookups=`/`queryset` members (twin `__init__` re-read).
  Trigger: the families merging.
- FR-28 target gates (CONVERGE base row): OrderSet-only vs
  FilterSet-only predicates + messages (twin gate re-read in
  full). Trigger: the families merging.
- FR-29 queryset absence (CONVERGE base row): zero queryset
  tokens here vs `get_queryset` + explicit intent there
  (twin body re-read). Trigger: ordering deriving querysets.
- FR-30 leaf-vs-root manifest (CONVERGE init row): family-grain
  opt-in vs default recipe; root still zero orders imports
  (re-grepped). Trigger: root-exporting the surface.
- FR-31 input identity vs mutation shape (CONVERGE factories
  row): class-derived naming + same-name-collide vs
  shape-derived naming (no shape axis here — the Layer-6 key
  is gone, trigger cleaner). Trigger: a narrowing-derived
  name axis.

### Falsifications (record-only; no row reopened, nothing re-applied)

- FF-1 Layer-6 deletion (committed, both families): orders
  `factories.py` lost `_dynamic_orderset_cache`,
  `_RESERVED_FACTORY_KEYS`, `_get_orderset_class`,
  `get_orderset_class` (clean file, WT=HEAD); the filter twin
  lost its four (clean); the four owner helpers
  (`make_dynamic_set_getter`, `create_dynamic_set_class`,
  `normalize_set_meta_for_factory`, `make_set_meta_cache_key`)
  have zero defs + zero callers package-wide.
  `orders-factory-reserved-keys`, `orders-reserved-keys-vs-filter-twin`,
  `orders-layer6-cache-vs-filter-twin`,
  `orders-getter-defaults-vs-filter-gate` rows name deleted
  subjects; F-2 citations name deleted call sites. CONVERGE
  with the filters-folder deferred `dynamic-set-class-getter`
  retire-or-revise → closeout retires/revises together.
- FF-2 init manifest 5→6 (committed): `OrderInput` joined
  `__all__`; the member artifact's "exactly 5" is stale.
  Verdict intact (homes compose by name); the plan row pins no
  count → no plan change; the spelling pair transcribes as T-1.
- FF-3 R-guards seam-(c) home moved (committed): the
  `isinstance` + path guards moved from
  `_resolve_order_expressions` into `_active_order_terms`
  (re-read: same predicate, same path-naming, same leniency
  rationale). Verdict intact; the plan row names no method →
  no plan change; citations refresh here only.
- FF-4 artifact-only name drift: the inputs member artifact
  cites `_active_permission_field_paths` (zero tree hits);
  the tree comment cites `OrderSet._active_permission_targets`
  (exists, `sets_mixins.py`). No plan row cites either → no
  action.
- FF-5 reject-call added to `_build` (committed): run-6 had
  zero `reject_captured_branches` hits; current threads
  `_order_paths` (new 3-line module reader) into the one
  owner call. Expansion row gains a facet → closeout note
  (with `_is_normalized_term` → return-gate row).
- FF-6 `Ordering.resolve` widened `str` → `str | Expression`
  (committed): same owner, same sentinels. F-ENUM row stands;
  note only.

## Defects

None found while tracing. Checks run: every new-since-run-6
member's docstring re-read against its body (`_active_order_terms`
filter+guard order, `_scoped_hops` root/owner spans,
`_visible_rows_sync` memo shape, `_visible_rows_async` pre-derive
+ `__getitem__` return, `_prepared_orderings` normalize+flatten
split, `_is_normalized_term` exact-type arms, `_order_paths` key read,
`_ORDER_ASYNC_RECOURSE` wiring into the sync visibility call,
`OrderInput` element-type + never-instantiated clauses,
`_order_input_annotation` six-kwarg pass-through) — no
contradiction; every guard family enumerated for omission against
its contract source (the three R-guards seams, the exact-type
population, the target-type gates, the per-field permission
dispatch — no missing member); layering claims hold (sets
imports base + inputs at module scope, inputs TYPE_CHECKING-only
back-edge, no reversed import).

All seven member D1s re-verified persisting at current bytes
(record-only; each already rides to closeout under its member
item — no new homing): base D1 (the `field_name` mutation prose
still names a metaclass step; `.field_name =` census still
exactly the self-store + 2 filter-side rebases); factories D1
(the `build_input_class`-from-`orders/inputs.py` path still
untaken; orders alias still zero production callers vs the twin's
two); inputs D1 (the `factories.py` consumer clause still false
for all five; tests import all five, re-censused); inputs D2
(`normalize_input_value` still cites Decision 13 — still the
coverage strategy); sets D1 (`apply_sync` still cites Decision
13); sets D2 (both `P1-B` cites still dangle — `P1-B` census
still 0 in spec-030); sets D3 (module docstring still says
"verbatim port"; the collector + write-back deltas still stand).

## Pending execution

No `proof:` owed (zero-edit: nothing to prove beyond the green
witness already run). `gate:` entries for the final gate:

- `gate:` `uv run python scripts/workspace.py run
  dry/folder-orders/verify-1 -- python -m pytest
  tests/orders -q --no-cov -p no:cacheprovider` (re-run the
  240-row witness; ran green in slot-2 as
  `dry-20261010T044357-deebfa`).
- `gate:` the final gate's live `/graphql` suites carrying
  `orderBy:` rows (direction vocab, null handling, to-many
  aggregates, visibility scoping) — named by the gate, not
  re-run here.
- Cells `unverified` with inapplicability correctly NOT claimed:
  the pipeline threads real database aliases
  (`using=queryset.db`) and builds ORM expressions evaluated
  against the database, so sharded + pg reach is real; both
  cells await the maintainer's word.

## Judgment

The folder is at single ownership: 18 compositions hold by name
with fresh censuses, 31 twin hypotheses resolve without a second
definition, the f33 duplication persists exactly as rowed
(already open+blocked), and the witness suite runs 240/240 green
at current bytes. The unassigned remainder — six rules the tree
grew or split since run-6 plus nine folder-fresh merge verdicts —
transcribes below as T-1..T-15 for Worker-0 to row. Zero edits,
zero new defects, zero new blocked consolidations.

## Index rows for Worker-0

One line per row; Worker-0 alone edits the plan. Holding item for
all: Folder integration `orders/`. Freshness: WT blobs in `## Pins
and fingerprints` (BASE = WT); HEAD troupes listed there for the
three dirty files.

New rules (fresh CONFIRM single-owned, zero-edit):

- T-1 `orders-helper-spelling-pair` — owner
  `orders/__init__.py::_order_input_annotation` — files
  `orders/__init__.py` — consolidated (C3: 2 spellings → 1
  body → 1 driver; FR-8).
- T-2 `orders-active-term-selection` — owner
  `orders/sets.py::OrderSet._active_order_terms` — files
  `orders/sets.py` — consolidated (C21: 2 consumers; carries
  R-guards seam (c); FF-3).
- T-3 `orders-relation-scope-resolution` — owner
  `orders/sets.py::OrderSet._scoped_hops` — files
  `orders/sets.py` — consolidated (C22: 2 consumers; FR-2).
- T-4 `orders-scoping-visible-rows` — owner
  `orders/sets.py::OrderSet._visible_rows_sync` (+
  `_visible_rows_async` coloring) — files `orders/sets.py` —
  consolidated (C23; FR-1).
- T-5 `orders-prepared-orderings` — owner
  `orders/sets.py::OrderSet._prepared_orderings` — files
  `orders/sets.py` — consolidated (2 colorings consume).
- T-6 `orders-async-recourse-wording` — owner
  `orders/sets.py::_ORDER_ASYNC_RECOURSE` — files
  `orders/sets.py` — file-local (C32; FR-3).

Rejections (folder-scope merges considered; each with trigger):

- T-7 `orders-visible-rows-coloring-merge` (FR-1) — files
  `orders/sets.py` — rejected (laziness coloring-forced;
  trigger: third seed site or seed logic).
- T-8 `orders-field-name-fallback-merge` (FR-2) — files
  `orders/inputs.py`, `orders/sets.py`,
  `utils/permissions.py` — rejected (three predicates /
  postures / consumers; trigger: shared typed accessor).
- T-9 `orders-async-recourse-vs-pipeline-template` (FR-3) —
  files `orders/sets.py`, `utils/querysets.py` — rejected
  (read-path vs write-pipeline events; trigger: read path
  collapsing into the template).
- T-10 `orders-separator-spelling-merge` (FR-4) — files
  `orders/inputs.py`, `orders/sets.py` — rejected (Django
  owns the value; trigger: package-wide routing decision).
- T-11 `orders-path-prefix-merge` (FR-5) — files
  `orders/inputs.py`, `orders/sets.py` — rejected (flat vs
  recursion levels; trigger: shared grammar).
- T-12 `orders-exact-type-gate-merge` (FR-6/FR-7) — files
  `orders/sets.py` — rejected (three seams, per-seam
  subjects; trigger: shared gate).
- T-13 `orders-spelling-pair-merge` (FR-8) — files
  `orders/__init__.py`, `filters/__init__.py` — rejected
  (per-family declarations over one driver; trigger:
  families merging).
- T-14 `orders-inputs-path-vs-filter-path` (FR-9) — files
  `orders/inputs.py`, `filters/inputs.py` — rejected
  (per-family values; no trigger by construction).
- T-15 `orders-none-polarity-merge` (FR-14) — files
  `orders/sets.py` — rejected (opposite spellings; helper
  would be machinery; trigger: logic).

Closeout notes (not rows): FF-1 (retire
`orders-factory-reserved-keys`,
`orders-reserved-keys-vs-filter-twin`,
`orders-layer6-cache-vs-filter-twin`,
`orders-getter-defaults-vs-filter-gate` alongside the deferred
`dynamic-set-class-getter` retire-or-revise); FF-2/FF-3/FF-4/FF-6
(no plan change — verdicts intact, rows pin no stale member);
FF-5 (append `_order_paths` to `orders-fields-expansion` and
`_is_normalized_term` to `orders-normalize-return-gate` owner
cells); f33 persists open+blocked (no change); the seven member
D1s ride (no new homing).

## Independent verification (Worker-2)

Verdict: verified. Zero-edit CONFIRM stands at current bytes
(HEAD `23b5f421`, WT pins below, slot-3 byte-identical).

Sequencing disclosure: the dispatch brief required reading
this artifact before any other step, so the Findings were read
before this trace was recorded — a deviation from the
expectation-first order. Mitigation: every position below was
re-derived by independent greps, pins, and censuses at current
bytes and only then compared; agreements are matches, nothing
is inherited.

### Own trace (re-derived, not trusted)

Pins re-derived: `__init__` 149 lines `e835e9b3` = HEAD clean;
`base` 168 `5dcc88e0` vs HEAD `96767f4e` dirty; `factories` 83
`5319f33a` = HEAD clean; `inputs` 412 `1ed19c1f` vs HEAD
`535eb96c` dirty; `sets` 1080 `fd453bec` vs HEAD `2d35adfa`
dirty. All five match the artifact. AST census re-derived:
16/4/3, 10/2/0, 9/1/0, 32/8/9, 41/9/5 — match.
`ITEM_BASELINE` resolves as a commit; item diff vs baseline
over package + `tests/orders` + examples is 0 bytes: zero-edit
confirmed. Slot-3 copy byte-identical to WT on all five
targets (run header: fresh, shared unmoved since sync).

Dirt attribution re-derived by full diff content: every added
line in the three dirty files is the `truth.*` identity-read
migration (import swaps, `_safe_*` to `truth.*`, `getattr` to
`truth.static_attr`, `__name__`/`__qualname__` to
`truth.name`/`truth.qualname`, paired casts and comments); no
other semantic change hides in any hunk. The `## Owned
changes` ledger (plan lines 1778–1977) names zero `orders/`
paths, so all dirt is external. `utils/truth.py` is untracked
(`??`) and absent from HEAD. Counts: C1–C35 all read (35),
FC-1–FC-18 all read (18), FR-1–FR-31 all read (31, of which
FR-17–FR-31 are 15 twin separations), FF-1–FF-6 all read (6),
T-1–T-15 all read (15), member D1s counted at 7.

### Composition and rejection evidence

Each census below is an independent grep at WT bytes:

- Sync/async: exactly 2 `async def`, both in `sets.py`; the
  other four files zero. Executable `await` lines are 3
  (`sets.py` 961, 1077, 1079); see CC-2. Zero `def apply`
  dispatcher; root carries zero orders imports; exactly 2
  direct BFS subclasses (both families).
- FC-2/FC-3: driver signature carries the 6 kwargs as listed;
  driver writes via `ledger.add`; finalizer reads via a
  function-local import plus orphan check. FC-4: base declares
  7 ClassVar hooks plus the triples method; both families
  declare 8 class assigns; see CC-1. FC-5: 2 production
  callers of the triples builder (hook + `_ensure_field_specs`).
  FC-6: 1 delegate plus self-recursion. FC-7: 2 warm-up call
  sites. FC-9: sole production caller of the column helper.
  FC-11: sole caller of the gate base; deferral edge intact.
  FC-14: 3 attestation points; list field is sole scope opener
  (function-local import) and sole guard caller. FC-16:
  direction feeds resolve plus the Min/Max pick; sole
  aggregate-emission site plus `_dst_order_` prefix (one other
  hit is a docstring mention). FC-18: no suffix override
  (docstring mention only). Term selector and scope resolver:
  2 consumers each. Flat walk: 0 production non-default
  callers. Helper ledger, traversal table, slot consumer,
  branch guard, metaclass, namespace quartet: bodies re-read,
  hold by name.
- FR-1: both coloring bodies re-read. Laziness is
  coloring-forced (async pre-derives every scope up front
  because no await may live in the sync tail; sync derives on
  demand with memo). The seed line composes two owners; the
  5-site `base_queryset(model_for(...))` idiom re-censused with
  varying alias sources. Holds separate.
- FR-2: trio re-read — walk matcher (`is None`, segment
  matching, cross-family hop), span length (`or`-falsy,
  ORM-span count for the roots/owners map), emission source
  (asserted entry, django path). Three predicates, postures,
  consumers. Holds separate.
- FR-3: order recourse offers the async alternative; the
  write-pipeline template offers only the sync rewrite. FR-4:
  both spellings located; raw `"__"` pervasive in connection
  (2), filters (6+), keyset (1). FR-5: flat vs recursion
  prefixes located. FR-6/FR-7: exact-type predicates at three
  seams. FR-9–FR-14: per-family values, disjoint ledgers,
  per-family configs, per-family descriptors, 2 warm-up def
  sites, opposite None polarities — all censused. FR-17/FR-18:
  twin signatures confirm distinct contracts. FR-23/FR-25/
  FR-26/FR-28/FR-30/FR-31: order-side bodies re-read, twin
  shapes sampled; lease is one payload slot vs append-only
  ledger with tombstone.
- FF-1: zero defs plus zero callers of the four owner helpers
  package-wide; zero hits for all four deleted orders subjects
  and the filter-side subjects; both factory files clean
  (orders `5319f33a` = HEAD, filters `3132a702` = HEAD).
  FF-2: 6-name manifest including `OrderInput` re-read. FF-3:
  guards live in `_active_order_terms` with the same
  predicate, path-naming, and leniency. FF-4: zero hits for
  the drifted name; the tree-cited target exists in
  `sets_mixins.py`. FF-5: `_order_paths` plus the owner call
  re-read. FF-6: `str | Expression` widening re-read, same
  owner and sentinels.
- f33: the two guard verdicts persist with identical structure
  (diff shows only label/message reads changed); already rowed
  open plus blocked. The ledger-claim third `is not pure` line
  is FR-16's claim side, not an f33 arm — count-2 confirmed.
- Member D1s riding (all 7 re-verified): `.field_name =`
  census exactly the self-store plus 2 filter-side rebases;
  orders alias zero production callers vs the twin's two;
  tests import all five aliases; Decision 13 cites intact in
  both files; `P1-B` census 0 in the spec; `verbatim port`
  clause plus collector and write-back deltas intact.

Independent consolidation sweep (own search, no inherited
positions): the paired `_expand_meta_fields` model reads sit
in mutually exclusive branches (early return between them)
and compose one owner by name; the paired selector/scope
consumers carry distinct contracts (filtering plus validation
vs scope derivation); the seed lines already compose shared
owners with family-owned appliers; the None-polarity pair is
one 3-token check where a helper would be machinery. No
missed FAM-N; no consolidation is owed.

### Index rows and corrections

T-1–T-15: every owner symbol verified to exist at its cited
path; every file list matches the sites re-derived above
(T-8's third file holds the walk matcher; T-9's second file
holds the write-pipeline template). All 15 transcribe as
written — zero row corrections.

Prose corrections (none touch rows, counts, or the verdict):

- CC-1: FC-4/C4 "8 hook attrs + 2 caches" overcounts. The tree
  shows 8 class-level assigns (6 string hooks + 2 caches) plus
  the `_build_input_triples` hook method. Fix: "6 hook attrs +
  2 caches (+ the hook method)"; C4 "ninth hook attr" reads
  "ninth class attr". Challenge count (1 + 2 family
  declarations) unaffected.
- CC-2: matrix axis 2 "four `await` lines" counts one prose
  line in `_ORDER_ASYNC_RECOURSE`. Fix: "3 executable awaits
  plus 1 prose line". Twinship verdict unaffected.
- CC-3: attribution "3/4/10 hunks" are semantic hunks; git
  `@@` counts are 2/4/12 (base splits one block into code plus
  docstring; sets merges three import blocks into one).
  Content attribution is complete; fix is the convention note.

### Gates and cells

- Witness suite re-run in slot-3 (own copy, fresh):
  `tests/orders`, 240 passed in 16.02s, run
  `dry-20261010T045418-85e920`, exit 0. The 7-module/240-row
  shape matches the artifact.
- Ruff gate: not applicable — zero-edit item, no touched
  paths; nothing to check and nothing failed.
- Sharded + pg cells: correctly left `unverified` without an
  inapplicability claim. Confirmed real DB reach: the pipeline
  threads `using=queryset.db` (both visible-rows seed lines)
  and `queryset.model` into ORM expressions evaluated against
  the database (`annotate`/`order_by` tail). Both cells await
  the maintainer's word.
- Defects: none found. No new Family-hold rows owed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-base]: dry-file-orders__base.md
[file-factories]: dry-file-orders__factories.md
[file-init]: dry-file-orders____init__.md
[file-inputs]: dry-file-orders__inputs.md
[file-sets]: dry-file-orders__sets.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
