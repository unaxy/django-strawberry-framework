# DRY review: `dynamic-set-class-getter`

Status: verified
Run: 0.0.15 2026-10-01-10

## System trace

The rule candidate is the dynamic-set class getter: the deferred
auto-set surface builds a synthetic set class from a `Meta` dict
through one normalize → key → `type(...)` skeleton over a
family-owned cache, parameterized by base class, reserved keys, name
suffix, synonym alias, and fields/exclude gate; class-Meta write-back
and expansion reads share the same fields fingerprint. The owner
candidate, `django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter`,
is re-derived below from the bytes, not inherited.

Scope held in this item: `make_dynamic_set_getter` plus
`normalize_set_meta_for_factory`, `make_set_meta_cache_key`,
`create_dynamic_set_class`, the synonym quartet
(`resolve_set_meta_fields`, `promote_set_meta_fields`,
`read_set_meta_fields`, `canonicalize_set_meta_fields`),
`FILTERSET_FIELDS_ALIAS`, the `_set_meta_*` duality, and the hashing
helpers (`make_hashable_meta_value` and its private walk); both
family declaration triples (`_get_*` construction, `_dynamic_*_cache`,
`_RESERVED_FACTORY_KEYS`, suffix, public `get_*` wrapper); both
metaclass write-back calls; the orders expansion read. Sibling
boundaries, each verified fresh rather than inherited: the
input-class BFS (`set-arguments-factory-bfs`, verified — build vs
declare split stands); the get-or-store walk shape
(`shape-build-get-or-store`, open — it owns the question whether the
getter's inline miss path joins its spine; this item records the site
and routes the question, decided nowhere here); the canonical
readers (`base_container_values`, `canonical_sort_key` — composed by
name, not duplicated); the Decision-11 forward-ref helper
(`build_lazy_input_annotation`); the write-flavor declaration
registries (`make_declaration_registry`); the input-naming spine
(`generated_input_type_name`).

Contract sources, read fresh: spec-028 Decision 12 (the single-siting
mandate — plumbing ships as the filter-side twin "so the `Meta`
hashing and `type(...)` construction stay single-sited in
`utils/inputs.py::make_dynamic_set_getter` rather than being copied
the day a caller lands", and "No package path calls either one");
spec-027 Non-goals #"Auto-generation of `FilterSet`" (deferred
surface); the KANBAN DRY-squeeze WP-D bullet (the principle-11
existence question — dead code vs deliberately symmetric skeleton —
is a contract-level call homed there, re-derived below as already
homed, not re-litigated here).

Fingerprints (short blob per state; baseline is the item baseline
object `e8f39d08`, copy is the synced workspace copy at slot-2):

| File | HEAD `5c3496e0` | WT | Baseline | Copy |
|---|---|---|---|---|
| `django_strawberry_framework/utils/inputs.py` | `0caa3416` | `0575e9b2` | `0575e9b2` | `0575e9b2` |
| `django_strawberry_framework/filters/factories.py` | `7576caea` | `7576caea` | `7576caea` | `7576caea` |
| `django_strawberry_framework/orders/factories.py` | `17204c27` | `17204c27` | `17204c27` | `17204c27` |
| `django_strawberry_framework/filters/sets.py` | `85699ac2` | `697ffd40` | `697ffd40` | `697ffd40` |
| `django_strawberry_framework/orders/sets.py` | `a8cd33c7` | `8ce11495` | `8ce11495` | `8ce11495` |

Baseline == WT on all five; copy == WT on all five; both factories
clean (WT == HEAD). Oracle pins (WT):
`tests/utils/test_inputs.py` `42bfb6a7`,
`tests/filters/test_factories.py` `49491bb9`,
`tests/orders/test_factories.py` `4ec2ec05`. Contract-source pins
(WT): `docs/SPECS/spec-028-orders-0_0_8.md` `94a3141c`,
`docs/SPECS/spec-027-filters-0_0_8.md` `ca463bdd`.

Dirt attribution (by diff content vs `git show HEAD:<path>`; the
`## Owned changes` ledger carries no row for any of the five files,
so every hunk below pre-dates the item and is concurrent work, left
untouched): `utils/inputs.py` 29 hunks of truth-migration rewrites
(`isinstance` → `truth.is_instance`, `getattr` → `truth.static_attr`,
new `_is_one_of`) plus docstring/comment reflow across the hashing /
meta / getter block; `filters/sets.py` truth-migration plus comment
reflow (the hunk at the metaclass rewords the presence comment, the
`promote_set_meta_fields` call line itself is byte-identical);
`orders/sets.py` truth-migration (`Meta` / `related_orders` reads)
plus reflow. The rule-region definition count is identical at HEAD
and WT (all nine `def`s present at both; both metaclass calls and the
orders expansion read present at both). `git status` count 479 at
dispatch, still 479; HEAD unmoved at `5c3496e0`.

## Verification

### Matrix

Discharged against the rule's real surface at WT bytes.

1. **Cross-flavor policy mirroring.** Both factories read whole
   (186 + 161 lines). Shared substrate: one
   `make_dynamic_set_getter` construction each, disjoint caches /
   suffixes / reserved literals, filter-only `fields_alias` plus
   `require_fields_or_exclude=True` vs order defaults — every
   divergence a declared parameter with a documented split (E-rows
   below). Write flavors swept: `mutations/sets.py`
   `make_declaration_registry` is a consumer-class registration quad,
   not Meta-dict class synthesis (E-registry); the
   `get_or_store_shape_build` riders are F-NEW's population
   (boundary, not decided here); `build_lazy_input_annotation` is the
   Decision-11 forward-ref rule (E-decision11); the
   `generated_input_type_name` spine is input naming (E-shapename).
   No second getter rule in any flavor.
2. **Sync/async twins.** Zero `async` / `await` tokens in the rule
   block (`utils/inputs.py:517-955`, awk-verified) and zero in both
   factories whole files (grep-verified). The rule is pure
   construction-time derivation; no await boundary exists to twin
   across. The sets files' async appliers are apply-time query
   execution, a different rule with its own owners.
3. **Derived rather than repeated knowledge.** Generated name
   `f"{model}{suffix}"` has one site (`create_dynamic_set_class`);
   model naming reads `truth.name` once; the fields fingerprint has
   one site per operation (resolve / promote / read /
   canonicalize); no concatenation twin (`AutoFilter` / `AutoOrder`
   appear only as the two suffix declarations plus oracle literals).
   Field-set derivation splits by owner: orders expansion composes
   `read_set_meta_fields`, filter expansion is django-filter
   machinery over the promoted `.fields` (E-read).
4. **Inverse / round-trip pairs.** No inverse exists and none is
   owed: there is no class → Meta parser and no cache-key decoder;
   the key is one-way by design (opaque values key by identity).
   The `(name, cls)` idempotency rule is the BFS family's ledger
   contract, not this one.
5. **Contracts restated in another medium.** Production (nine
   definitions plus helpers, below); oracles (three test modules —
   literal-spelling behavior arms plus the twin-closure gate, all
   independent: none reads the owner's bodies); projections
   (module and function docstrings, spec-027 / spec-028 prose, the
   KANBAN WP-D bullet, the glossary `OrderSet` closing clause whose
   imprecision the board already owns as a Slice 5 edit). Roles
   tabled under F1; only definitions counted.
6. **Enforcement by omission.** Family members enumerated: two
   caches (both without a clear hook — symmetric, documented
   deliberate: keys embed model identity, a rebuilt model takes a
   fresh key); two getter constructions (both bare); two public
   wrappers; two reserved-key literals; two metaclass write-back
   calls (both present); expansion reads (orders present, filters
   absent by contract — E-read). No gap: every absence carries a
   contract source or is symmetric-deliberate. Whether Layer-6
   caches want a clear hook at all is a design question, not a
   member gap — both members agree.

### Enumeration

Instrument: exact `def` census plus exact-call-site census per
helper plus package-wide mechanism-vocabulary sweeps
(`make_dynamic_set_getter`, `normalize_set_meta_for_factory`,
`make_set_meta_cache_key`, `create_dynamic_set_class`,
`resolve/promote/read/canonicalize_set_meta_fields`,
`make_hashable_meta_value`, `FILTERSET_FIELDS_ALIAS`,
`_get_filterset_class`, `_get_orderset_class`,
`get_filterset_class(`, `get_orderset_class(`, `type("Meta"`,
`**meta`, `AutoFilter`, `AutoOrder`). Population: 9 rule
definitions plus 11 mechanism helpers / constants, all in
`utils/inputs.py`; 2 family declaration groups (construction plus
cache plus reserved literal plus suffix plus public wrapper each);
3 composed call sites (2 metaclass write-backs, 1 expansion read);
0 production callers of either public getter outside its factory
module (both surfaces deferred, Decision 12). Closing censuses:
`type("Meta"` occurs once package-wide (`create_dynamic_set_class`
`:901`); `normalize` / `key` / `create` each have exactly one
production caller (the getter closure); `**meta` occurs 8 times (4
signatures — protocol, closure, 2 public — plus 2 delegates plus 2
docstrings). Every member lands below: one CONFIRM finding, 12
exclusions each with contract difference plus trigger, 1 routed
boundary, zero unassigned.

### Challenges

Authoritative definitions only; consumers, oracles, and projections
that also move are listed, never counted. All challenges
static-reviewed at WT bytes; the twin-closure behavior is
additionally pinned by one executed oracle re-run fresh in the
shared venv
(`tests/utils/test_inputs.py::test_filter_and_order_dynamic_caches_ride_make_dynamic_set_getter`,
1 passed).

- C1 Skeleton order. Posit explicit-first moved after normalize,
  or the hit check dropped: 1 definition moves (the
  `get_set_class` closure). Both constructions follow as
  declarations (0); both wrappers follow (0).
- C2 Normalize rule. Posit a new reserved handling, alias
  equivalence, or canonical shape: 1 definition
  (`normalize_set_meta_for_factory`). A vocabulary change also
  touches the 2 reserved-key declarations (listed, not counted);
  both metaclasses follow only if the shared synonym rule moves
  (C5).
- C3 Key rule. Posit a new fields-shape tag or extras treatment: 1
  definition (`make_set_meta_cache_key`). Posit a value-walk change
  (depth, cycle, opaque-token rule): 1 definition
  (`make_hashable_meta_value`); the canonical readers it composes
  move only on their own axis (0 here).
- C4 Construction. Posit a new Meta validation, name template, or
  base wiring: 1 definition (`create_dynamic_set_class`). A suffix
  change touches the 2 suffix declarations (listed, not counted).
- C5 Synonym rule. Posit a new alias or precedence: 1 definition
  (`resolve_set_meta_fields`). A write-back change moves
  `promote_set_meta_fields` (1); an expansion-read change moves
  `read_set_meta_fields` (1); a canonical-shape change moves
  `canonicalize_set_meta_fields` (1). The 2 metaclass calls, the
  orders expansion read, and the filter construction's
  `fields_alias` parameter follow as consumers (0).
- C6 Fields/exclude gate. Posit gating the order side too, or
  dropping the filter gate: 1 declaration flip per family
  (`require_fields_or_exclude`), 0 definitions — the arm already
  exists in `create_dynamic_set_class`. A semantic change to the
  arm itself: 1 definition.
- C7 Error wording. Posit rewording model-missing / non-model /
  fields-missing: 1 definition each (the three f-strings in
  `create_dynamic_set_class`); `getter_name` / `explicit_param`
  threading is declaration (0). Oracle `match=` literals follow
  (listed, not counted).
- C8 Miss-path shape. Posit return-stored-vs-built or a miss
  counter: 1 definition here (the closure). The walk-shape
  question — whether this inline miss path joins the
  `get_or_store_shape_build` spine — is owned by open Family
  `shape-build-get-or-store` (boundary row below); this item
  counts its own rule only and decides nothing there.

## Findings

### F1: the dynamic-set class getter is single-owned (CONFIRM, zero-edit)

Contract + variation. The deferred auto-set surface builds a
synthetic set class from a `Meta` dict through one normalize →
key → `type(...)` skeleton over a family-owned cache; class-Meta
write-back and expansion reads share the same fields fingerprint
(resolve, then canonicalize; write-back on class Meta only).
Legitimate variation: the per-family construction parameters
(base class, reserved keys, name suffix, synonym alias,
fields/exclude gate) plus cache identity — declarations, never
definitions.

Sites + roles. Definitions (9, all `utils/inputs.py`):
`make_dynamic_set_getter` (`:906`, skeleton factory),
`normalize_set_meta_for_factory` (`:782`),
`make_set_meta_cache_key` (`:732`), `create_dynamic_set_class`
(`:853`), `resolve_set_meta_fields` (`:651`),
`promote_set_meta_fields` (`:700`), `read_set_meta_fields`
(`:720`), `canonicalize_set_meta_fields` (`:680`),
`make_hashable_meta_value` (`:598`); mechanism helpers / constants
(11, same file): `_hashable_meta_value`, `_sorted_meta_values`,
`_opaque_meta_value`, `_set_meta_has`, `_set_meta_get`,
`_is_one_of`, `_MAX_META_VALUE_DEPTH`, `_META_CONTAINER_TYPES`,
`_UNORDERED_TYPES`, `_META_ABSENT`, `FILTERSET_FIELDS_ALIAS`.
Declarations: `filters/factories.py` construction `:133-147`,
cache `:71`, reserved `:76`, suffix `:136`, public wrapper
`:150-186`; the orders mirror (`orders/factories.py` `:119-127`,
`:53`, `:58`, `:122`, `:130-161`). Consumers: the two metaclass
write-back calls (`filters/sets.py:1109` with alias,
`orders/sets.py:341` without) and the orders expansion read
(`orders/sets.py:521`); zero production callers of either public
getter (Decision 12; verified by package-wide caller census).
Oracles: Layer-6 arms of `tests/filters/test_factories.py:365-771`
plus `:824-825`, `tests/orders/test_factories.py:414-551`, and
`tests/utils/test_inputs.py:520-833` — all literal-spelling and
family-driving, hence drift-failing; plus the twin-closure gate
(gate record below) and the `co_names` composition pins
(`:653-654`, oracles not gates — a hand copy passes them).
Projections: the module / factory / wrapper docstrings, spec-027
Non-goals and spec-028 Decision 12 prose, the KANBAN WP-D bullet,
the glossary `OrderSet` clause (board-owned).

Challenges. C1–C8 above, each count 1 (C6 counts a declaration
flip; C8 counts 1 here with the spine question routed).

Owner + lifetime. `make_dynamic_set_getter` plus helpers in
`utils/inputs.py`, by responsibility (principle 7): both families
already import that module without a cycle (its docstring states
the contract, the same one `utils/connections.py` carries), so it
is the narrowest cohesive owner every legitimate consumer can
depend on; hosting in either sibling flavor would reverse the
flavor dependency. Decision 12 names the same owner, re-derived
here from the import graph, not inherited from the spec. Lifetime:
per-process family dicts with no clear hook (documented
deliberate — keys embed model identity, a rebuilt model takes a
fresh key; test isolation rides per-module fixture clears, not
the clear bus); generated classes park in the cache until process
end.

Migration. None: every site already composes by declaration,
delegation, or call. Zero-edit verdict.

Distinct behavior. The exclusions below; each stays separate and
is recorded at its owner prose or in this artifact. One
prose-accuracy note, below the defect bar: the key / normalize /
hash docstrings say unordered branches sort "by `repr`", while
the body sorts by `canonical_sort_key` (`truth.render`, then
type/value identity). The wording is loose but the stated
contract — total ordering over mixed member types, structural
inputs collapsing to one key — verifies against the body (equal
members are interchangeable in the emitted tuple, so the
identity tie-break cannot split a key), and keys never persist
across processes. Loose naming, intact contract: observation,
not defect.

Behavioral proof. Static-reviewed throughout (both constructions
are bare `make_dynamic_set_getter` invocations; both wrappers are
one-line delegates; the metaclass and expansion calls compose by
name; `type("Meta"` has one site; the three helpers have one
production caller each), corroborated by executed independent
oracles: the Layer-6 collapse / distinctness / gate / alias /
reserved / model-guard arms named above, all of which fail on any
second definition that drifts (they spell literals and drive
both families). One oracle re-run fresh in the shared venv passes
(`test_filter_and_order_dynamic_caches_ride_make_dynamic_set_getter`,
1 passed). No execution-deferred proof: nothing here decides
ordering, transactionality, or async behavior beyond the
oracle-pinned skeleton order, and no change is proposed.

Structural gate. The existing twin-closure oracle
(`tests/utils/test_inputs.py:798`) IS the gate — no bespoke gate
owed beyond it. Three arms: (a) `__code__`-identity between the
two `_get_*` closures fails ANY second body (hand copy, wrapper,
or re-spelling — a distinct `def` execution can never share a
code object); (b) the no-private-alias pins (three `hasattr`
assertions per factory module) trip the obvious helper-fork
shape; (c) the disjoint-cache behavior arms (`filt is not order`,
distinct names and bases) fail a cache merge. Negative control:
byte-identical source compiled twice yields distinct code
objects, demonstrated mechanically by an import-free workspace
probe (run `dry-20261001T134014-cf7535`, slot-2, exit 0,
`identical-source-distinct-code`) — so arm (a) fails the
behavior-preserving hand copy by language construction, while
every behavior oracle passes it. The plausible bypass population
(whole-closure copy, helper fork plus thin closure, cache merge)
is covered; a fork under novel private names still fails arm
(a).

Coupling. None: zero edits, zero new symbols, zero import moves.

Freshness. Family-file fingerprints as tabled under System trace
(HEAD, WT, baseline, and copy states — baseline == WT and copy ==
WT on all five); searched population is the whole
`django_strawberry_framework/` tree (exact-name plus
mechanism-vocabulary censuses above); oracles pinned (WT blobs
above); contract sources pinned (spec blobs above; KANBAN WP-D
quoted from WT). Modules excluded on the strength of their
bodies: every write-flavor input builder (input dataclasses from
field specs via `build_strawberry_input_class`, never set
classes from Meta dicts), every declaration registry, the BFS
factory, the Decision-11 helper, the input-naming spine — plus
every remaining package module, which carries no `**meta`
entry, no `type("Meta"` synthesis, and no Meta-dict key builder
(the sweeps above are package-wide). Any fingerprint change
reopens the finding.

### Exclusions (contract difference plus reconsideration trigger each)

- E-cache: the two `_dynamic_*_cache` dicts stay family-owned.
  Difference: disjointness is the documented rule ("a filter
  clear cannot drop an order class (and the reverse)"); one dict
  would let a same-key cross-family hit return the wrong base
  class. Home: the cache comments both sides. Trigger: a
  shared-cache lifecycle demand with a key that discriminates
  family.
- E-reserved: the two `_RESERVED_FACTORY_KEYS` literals stay
  per-family. Difference: distinct values
  (`filterset_base_class` vs `orderset_base_class`), each naming
  its own family's collision surface; declarations, not a rule.
  Home: the member comments. Trigger: a shared reserved
  vocabulary across families.
- E-gate: filter-only `require_fields_or_exclude=True` plus
  `FILTERSET_FIELDS_ALIAS` vs order defaults stays a declared
  split. Difference: django-filter's metaclass hard-asserts
  fields/exclude while the order `type` metaclass accepts a
  fields-less Meta (whose zero-field rejection stays at the BFS
  site); the cookbook synonym exists only on the filter side.
  Home: the `create_dynamic_set_class` and
  `make_dynamic_set_getter` docstrings. Trigger: the order
  metaclass gaining the assertion, or a cookbook order synonym.
- E-wrapper: the public `get_*` wrappers stay thin delegates.
  Difference: each carries the family type signature, the public
  name, and the contract docstring; the private binding carries
  the construction. No rule logic lives in either body.
  Recorded here. Trigger: a wrapper growing logic — it becomes
  a second definition the day it does.
- E-read: `read_set_meta_fields` stays orders-only. Difference:
  package-owned Meta.fields expansion exists only on the order
  side; filter expansion is django-filter machinery
  (`super().get_fields()`) over the already-promoted `.fields`,
  whose output order follows declaration / model order, never
  raw set iteration. Home: both expansion docstrings. Trigger:
  `FilterSet` gaining package-owned Meta.fields expansion.
- E-suffix: `AutoFilter` / `AutoOrder` stay per-family literals.
  Difference: distinct values feeding one template; declarations.
  Home: the construction call sites. Trigger: a shared generated-name
  vocabulary across families.
- E-clear: both Layer-6 caches stay without a clear hook.
  Difference: symmetric deliberate omission (axis 6), not a
  member gap — keys embed model identity. Home: the lifecycle
  comments both sides. Trigger: a consumer reload path that
  demands eviction.
- E-registry: `make_declaration_registry` stays separate.
  Difference: consumer-class registration (register / clear /
  iter / store over declared classes) vs Meta-dict class
  synthesis (normalize → key → `type(...)` over kwargs); different
  subjects, inputs, and change reasons. Trigger: a registry that
  synthesizes classes from Meta dicts.
- E-decision11: `build_lazy_input_annotation` stays separate.
  Difference: forward-ref annotation plus ledger plus validation
  vs class synthesis; shares the substrate file, not the rule.
  Trigger: the leaf helpers growing synthesis duties.
- E-bfs: `GeneratedInputArgumentsFactory` stays separate.
  Difference: input-class BFS build vs set-class declaration;
  folding them couples unrelated lifecycles over a shared file
  (the F-1/F-2 ruling, re-verified: no walk, collision, or cache
  spelling is shared). Trigger: a unified build-and-declare
  lifecycle.
- E-shapename: `generated_input_type_name` /
  `name_set_input_type_name` stay separate. Difference: input
  type-name derivation (suffix rule plus full-vs-derived
  branching) vs set-class synthesis. Trigger: generated set
  classes taking their names from the input-naming spine.
- E-hashshare: the hashing arms' composition of
  `base_container_values` / `canonical_sort_key` stays as is.
  Difference: none to resolve — already composed by name; only
  the metadata-flavored rejection wording stays local, which is
  the correct parameterization split. Trigger: none (converged).

Boundary (routed, not a rejection): the closure's inline miss
path (`cache.get` → None-check → build → store → return,
`utils/inputs.py:939-951`) dual-homes to open Family
`shape-build-get-or-store`, which owns the walk-shape question
for all three spellings (spine, this miss path, the Range
per-instance cache). That item decides; this one records the
site and counts its own rule only (C8).

## Defects

None. The one prose-accuracy observation from the trace (the
"by `repr`" wording vs the `canonical_sort_key` body) is
recorded under F1 Distinct behavior and sits below the defect
bar: the stated collapse / totality contract verifies against
the body, and no wire or configuration input distinguishes the
two wordings.

## Pending execution

None. No `proof:` entry (zero-edit verdict; every proof is
static-reviewed over bodies composed by name, corroborated by
the existing executed oracles plus one fresh re-run) and no
`gate:` entry. Cell typing: `default` executed (1 probe green,
shared venv); `sharded` and `pg` are `inapplicable by
construction` — the family decides pure construction-time class
derivation (normalize, key, `type(...)`, fingerprint reads) and
reaches no queryset, database alias, or dialect decision; cache
keys embed model identity but no query is built, and the oracle's
`django_db` mark serves model-class availability only.
Worker-2 judges the typing.

## Judgment

CONFIRM: the dynamic-set class getter is single-owned by
`django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter`
plus its eight composed helpers, with both families composing by
bare declaration. Eight challenges count 1; twelve exclusions
carry contract differences plus triggers; the miss-path
walk-shape question routes to open Family
`shape-build-get-or-store`; the Layer-6 existence question stays
homed at the DRY-squeeze card's WP-D. Zero edits, zero defects.

## Implementation (Worker-1)

No production edits (zero-edit verdict) and no new tracked files
besides this artifact (untracked until Worker-0 records it). No
ruff run (zero tracked `.py` touched — vacuous, no run owed).
One focused `--no-cov` oracle re-run in the shared tree plus one
import-free workspace probe (run `dry-20261001T134014-cf7535`,
slot-2, fresh sync, exit 0), both recorded above. Concurrent
dirt explicitly untouched: the truth-migration plus reflow hunks
in all three dirty family files plus the remainder of the
479-entry `git status` list.

Type gates (shared venv, read-only): `mypy` clean (119 source
files, no issues), `basedpyright` clean (0 errors, 0 warnings,
0 notes), `check_any.py` clean (130 allowed uses at 90 sites).
Vacuous as consolidation gates — zero-edit verdict, no symbol
added, moved, or removed — reported here per convention for the
verifier to re-run.

## Independent verification (Worker-2)

Recorded before opening `## Findings` (only the header, `## System
trace`, `## Verification`, and the `## Implementation` tail above
were read first; the verdict brief in the dispatch note was not
inherited as evidence). All traces below are fresh at WT bytes,
HEAD era `5c3496e0`.

### W2 sites and roles (own census)

Definitions (9, all in `django_strawberry_framework/utils/inputs.py`):
`::make_dynamic_set_getter` (the lookup / normalize / key /
`type(...)` skeleton driver), `::normalize_set_meta_for_factory`,
`::make_set_meta_cache_key`, `::create_dynamic_set_class`,
`::resolve_set_meta_fields`, `::promote_set_meta_fields`,
`::read_set_meta_fields`, `::canonicalize_set_meta_fields`,
`::make_hashable_meta_value`; plus the `::FILTERSET_FIELDS_ALIAS`
literal declaration. Private mechanics under the nine
(`::_set_meta_has`, `::_set_meta_get`, `::_hashable_meta_value`,
`::_sorted_meta_values`, `::_is_one_of`, `::_opaque_meta_value`,
`::_MAX_META_VALUE_DEPTH`, `::_META_CONTAINER_TYPES`,
`::_UNORDERED_TYPES`) are sub-steps of their public helper, not
separate rules — no challenge moves one without its helper.

Consumers / declarations (0 counted): both family construction
calls (`filters/factories.py::_get_filterset_class`,
`orders/factories.py::_get_orderset_class`) are bare parameter
declarations; both caches (`::_dynamic_filterset_cache`,
`::_dynamic_orderset_cache`), both reserved literals, both suffix
literals, both public wrappers (`::get_filterset_class`,
`::get_orderset_class`, one-line delegates) are family-owned
data; the two metaclass write-back calls
(`filters/sets.py::FilterSetMetaclass.__new__`,
`orders/sets.py::OrderSetMetaclass.__new__`) and the one
expansion read (`orders/sets.py::OrderSet._expand_meta_fields`)
compose by name.

Oracles (independent, literal-spelling): `tests/utils/test_inputs.py`
(helper arms plus the twin-closure gate asserting `__code__ is`
between the two family closures), `tests/filters/test_factories.py`,
`tests/orders/test_factories.py`, and the structural co-name asserts
in `tests/orders/test_sets.py`. None reads an owner body.

Projections: the module and function docstrings on all five indexed
files, spec-027 / spec-028 prose, the KANBAN WP-D bullet.

Zero production callers of either public getter outside its factory
module (package-wide `get_filterset_class(` / `get_orderset_class(`
sweep: definitions + wrappers + docstrings + tests only) — both
surfaces deferred per spec-028 Decision 12.

### W2 challenges (own posits, authoritative definitions only)

- W2-C1 alias vocabulary. Rename `filter_fields` or add a second
  synonym: 1 definition (the `FILTERSET_FIELDS_ALIAS` literal plus
  the `resolve_set_meta_fields` precedence arm — one rule, one
  module). Both metaclass bindings and the filter construction
  follow as consumers (0).
- W2-C2 new `Meta.fields` container shape. 1 rule site
  (`canonicalize_set_meta_fields`); the `make_set_meta_cache_key`
  shape branches accept the same shapes as documented defense in
  depth and move in the same module — listed, same owner, no second
  family to sync.
- W2-C3 skeleton order (explicit check after normalize, hit check
  dropped, store-before-validate): 1 definition (the
  `get_set_class` closure). Both constructions and both wrappers
  follow (0).
- W2-C4 reserved-key vocabulary (strip one more shared key): the
  rule moves once (`normalize_set_meta_for_factory`); the 2
  family literals move as declared data (listed, not counted —
  principle 1: different members, one stripping rule).
- W2-C5 gate flip (order side gated too, or filter gate dropped):
  0 definitions — declaration flips on `require_fields_or_exclude`;
  the arm already exists once in `create_dynamic_set_class`. A
  semantic change to the arm itself: 1 definition.
- W2-C6 error wording (model-missing / non-model /
  fields-missing): 1 f-string each, all in `create_dynamic_set_class`;
  `getter_name` / `explicit_param` threading is declaration (0);
  oracle `match=` literals follow (0).
- W2-C7 third set family: 0 new bodies — one more bare declaration
  (cache + base + suffix + alias-or-None + gate flag). The driver
  extends by parameter (principle 1), never by copy.
- W2-C8 miss-path walk shape (return-stored-vs-built, miss
  counter): 1 definition here (the closure). Whether the inline
  miss path joins the `get_or_store_shape_build` spine is NOT
  decided here — the plan index row for open Family
  `shape-build-get-or-store` already names the Layer-6 inline miss
  path as population member 2 of 3, so the question is routed
  there by the plan itself.

Every posit counts ≤1 definition; no posit moves two
independently maintained bodies.

### W2 owner (own choice)

`django_strawberry_framework/utils/inputs.py::make_dynamic_set_getter`
plus the eight composed helpers — the same seat W1 names, chosen
fresh on principle 7: the neutral mechanics module both families
already import without a cycle (its documented no-family-import
contract), owning hashing / normalize / skeleton mechanics while
each family keeps its cache dict, base class, and binding
parameters (principle 1 declared variation; dependency direction
over narrowness). No narrower seat is importable by both families;
no existing family owner can host the twin without reversing the
dependency.

### W2 zero-edit search (own sweep, not a re-derivation)

Single-`type("Meta"` site package-wide (`create_dynamic_set_class`);
single set-class `type(name, (set_base_class,)` site; single
`filter_fields` handling rule (`resolve_set_meta_fields` +
literal; metaclasses and the filter construction compose it);
`AutoFilter` / `AutoOrder` only as the two suffix declarations
plus oracle literals; no `custom_filterset_factory` twin (the
docstring names the replaced external, correctly not mirrored);
`build_strawberry_input_class`'s `type(...)` builds Strawberry
input dataclasses — the f31 input-class rule, a different subject
with a different contract. No second getter body exists to land a
consolidation on; the scoped diff (plan edit plus this untracked
artifact — verified below) carries zero production edits, which is
the correct shape for this census, not an omission.

### W2 matrix judgment (own discharge)

1. Cross-flavor: both factories read whole; every filter/order
   divergence is a declared getter parameter with a documented
   split in the construction call. Write-flavor registries
   (`mutations/sets.py::make_declaration_registry`), the
   Decision-11 forward-ref helper, and the input-naming spine are
   different rules on different subjects — exclusions, judged on
   their bodies, not their names.
2. Sync/async: inapplicable by construction — the rule block and
   both factories contain no await boundary (pure
   construction-time derivation); the sets files' async appliers
   are apply-time execution, a different rule.
3. Derived knowledge: one name template, one fingerprint per
   operation; orders expansion composes the shared reader while
   filter expansion is django-filter machinery over the
   metaclass-promoted `.fields` — the alias is resolved once at
   class creation, so the filter read is downstream of the shared
   rule, not a second derivation.
4. Inverse pairs: none owed — one-way key by design (opaque
   identity tokens admit no decoder); no class → Meta parser
   exists.
5. Other media: three oracle modules plus doc/spec/board prose;
   roles as tabled above; only definitions counted.
6. Enforcement by omission: family enumerated — 2 caches (both
   hookless, symmetric, documented deliberate), 2 constructions,
   2 wrappers, 2 reserved literals, 2 metaclass calls (both
   present), expansion reads (orders present; filters absent
   because django-filter owns that expansion over already-promoted
   fields — contract difference, not a gap). No member lacks an
   applicable rule without a contract source. The Layer-6
   existence question (dead code vs deliberate skeleton) is a
   principle-11 call already homed on the DRY-squeeze card's WP-D
   (KANBAN bullet re-derived fresh: "Dead code or deliberately
   symmetric skeleton is a contract-level call, not a worker's") —
   routing confirmed, not re-litigated.

### W2 reconciliation (read after the above was recorded)

No material difference on any load-bearing claim. Sites and roles
re-derived identical (9 definitions, same names and seats; same 3
composed calls; same 0 production callers). One census-completeness
note, not a verdict spend: W1's 11 mechanism helpers include
`::_META_ABSENT`, which my trace folded silently under
`::_set_meta_has` — a sentinel sub-step, no rule, no count impact.
Challenges map 1:1 in substance (W1-C1=W2-C3, C2⊃W2-C4,
C3⊃W2-C2-key-half, C4 verified-single-site, C5⊃W2-C1/W2-C2,
C6=W2-C5, C7=W2-C6, C8=W2-C8); my extra W2-C7 third-family
stress (0 new bodies) strengthens rather than conflicts. Owner
identical with identical principle-7 reasoning. All 12 exclusions
re-verified on bodies with contract difference plus trigger
(E-read's django-filter-expansion split confirmed at the metaclass
call and `FilterSet.get_fields`; E-gate's metaclass asymmetry
confirmed in both constructions; E-registry / E-decision11 /
E-shapename bodies read fresh and genuinely other rules;
E-hashshare confirmed composed by name at the import). Both
routings confirmed: the miss-path walk shape dual-homes to open
Family `shape-build-get-or-store` (named as its population member
2 of 3 by the plan index itself — do not re-home), and the
Layer-6 existence question stays homed at the DRY-squeeze card's
WP-D (KANBAN bullet re-derived verbatim — do not re-litigate).
The "by `repr`" prose note sits below the defect bar on the
stated reason (verified: `canonical_sort_key` is total; the
identity tie-break decides only among equal-render members, which
are interchangeable in the emitted tuple for every realistic
Meta shape; keys never cross processes). Defects-None agreed —
zero W2 defects. `## Pending execution`-None correct: static
proofs over bodies composed by name, corroborated by executed
oracles plus two fresh green probes (below). Cell typing
`default`-executed plus sharded/pg `inapplicable by
construction` ENDORSED — pure construction-time derivation,
verified reaching no queryset, alias, or dialect decision; the
oracle's `django_db` mark serves model-class availability only.

W2 evidence (shared venv unless noted): twin-closure oracle
re-run 1 passed (`tests/utils/test_inputs.py::test_filter_and_order_dynamic_caches_ride_make_dynamic_set_getter`);
stdlib compile-twice probe `identical-source-distinct-code: True`
(corroborates the gate's negative-control mechanism without
importing anything); ruff `format --check` + `check` clean on
all 5 indexed files as the closest meaningful gate (W1 touched
zero tracked `.py`, so ruff on the item's touched paths is
vacuous — stated, not run as a false gate); `mypy` 119 clean,
`basedpyright` 0/0/0, `check_any` 130/90 — all three re-run,
matching W1 and the run-10 baseline exactly. Fingerprints 10/10
corroborated (5 family files × WT/HEAD/baseline 15/15, 3 oracle
pins, 2 spec pins); copy-state pins accepted on W1's recorded
slot-2 probe (no mutating proof needed, no second copy synced);
dirt attribution corroborated (29 `@@` hunks in
`utils/inputs.py`, 3 dirty files, both factories clean, all
concurrent truth-migration, `promote` call lines byte-identical).
Contract quotes verified verbatim in WT spec-028 (`:794`)
and spec-027 (`:137`). Zero-edit re-verified: item diff vs
`e8f39d08…` is the plan edit alone plus this untracked artifact.
Status count 480, HEAD `5c3496e0` unmoved. No workspace run owed
(no source-mutating proof exists to need one).

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
