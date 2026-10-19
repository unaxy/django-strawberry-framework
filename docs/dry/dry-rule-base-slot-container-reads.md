# DRY review: `base-slot-container-reads`

Status: verified
Run: 0.0.15 2026-10-01-11

Item kind: FAMILY (responsibility family). Owner candidate re-derived fresh,
not inherited: `django_strawberry_framework/utils/canonical.py::base_container_values`
CONFIRMED as the owner. Consolidation implemented in this same change.

Concurrency: every indexed file carries concurrent dirt (truth migration +
except-`BaseException` deletions, no ledger row covering any of them); all of
it is attributed by diff content below and preserved byte-for-byte. All five
production edit lines were byte-identical between HEAD and WT before the edit;
the test additions are purely additive. No concurrent line edited, reverted,
or tidied.

Baselines: `ITEM_BASELINE=ebefd760c9579285ad47418a266692fc3d7343fa`
(resolves); HEAD `dd0b6691` unmoved throughout. Dispatch pins verified at task
start: `utils/canonical.py` WT `d754e71c` / HEAD `7f5bb5f7`,
`utils/inputs.py` WT `0826c9d4` / HEAD `0b7d353c`,
`utils/input_values.py` WT `905451cc` / HEAD `929e81b5`. Address
`dry/baseslot-f45/consolidate` (slot-2; every proof ran there).

## System trace

The rule: a consumer-controlled built-in container is ENUMERATED through its
type's UNBOUND iteration slot (`dict.items`, `set` / `frozenset` / `list` /
`tuple` `__iter__`), never through the instance's overridable attribute, so a
subclass cannot decide what a security walk sees. The owner candidate states
exactly this contract: `utils/canonical.py::base_container_values` returns a
`tuple` snapshot - pairs for a `dict`, members for the other four - and
REFUSES anything outside the five with a typed `ConfigurationError`.

Mechanism census (re-derived, not inherited). AST probe over all 120 package
`.py` files at WT bytes for `dict.items` / `<builtin>.__iter__` attribute
reads, plus a word-boundaried `git grep` at HEAD bytes for the same forms
plus `keys` / `values` / `get` / `__getitem__` / `__contains__` / `__len__`
/ `__str__` / `__repr__`, plus a `getattr(..., 'items' | '__iter__')` sweep
(zero hits) and an alias sweep (`= dict.items` / `= list.__iter__`: only the
two assignment sites below, both composed away). Pre-change WT hits: exactly
13, in four files:

- `utils/canonical.py::base_container_values` (:73/:75/:77/:79/:81): the five
  arms. One definition.
- `utils/inputs.py::_hashable_meta_value` dict arm (`:577` WT, `:571` HEAD):
  `for key, value in dict.items(v)` - site A, COMPOSED in this change.
- `utils/inputs.py::canonicalize_set_meta_fields` dict branch (`:695` WT,
  `:684` HEAD): `for key, value in dict.items(fields)` - site B, COMPOSED.
- `utils/input_values.py::iter_input_items` dict arm (`:110` WT post-edit,
  `:108` HEAD): `pairs = dict.items(input_value)` - site C, COMPOSED.
- `utils/input_values.py::iter_active_fields` list arm (`:340` WT post-edit,
  `:372` HEAD): `elements = list.__iter__(input_value)` - site D, COMPOSED.
- `utils/inputs.py::make_set_meta_cache_key` (`:773` WT, `:761` HEAD):
  `dict.items(safe_meta)` - separation R-I (framework-built exact dict).
- `utils/inputs.py::normalize_set_meta_for_factory` (`:812` WT, `:801`
  HEAD): `dict.items(meta)` - separation R-G (interpreter-built exact dict
  at the sole production call site).
- `utils/inputs.py::build_strawberry_input_class` (`:1390` WT, `:1384`
  HEAD): `dict(dict.items(raw_kwargs))` - separation R-H (framework-built
  triples; copy contract).
- `utils/permissions.py::_related_declarations` (`:642` WT, `:689` HEAD):
  `dict.items(declarations)` inside a conditional accepting non-dict
  mappings - separation R-F (accept-vs-refuse).
- `utils/input_values.py::input_field_value` (`dict.get`, not in the
  enumeration census by design) - separation R-E (point lookup).

Already-composing consumers (verified by call census, zero inline
restatements): `utils/inputs.py::_sorted_meta_values`,
`_hashable_meta_value` set/list arms, `make_set_meta_cache_key` list/set
arms, and `utils/write_transaction.py::_field_fingerprint` (three calls:
dict pairs, ordered sequence, unordered members). Post-change WT census: 9
hits (5 owner arms + 4 separations), pinned by the new gate.

Oracles (all independent: they spell literal tuples or install lying
overrides; none reads the owner): `tests/utils/test_canonical.py` (lying
subclass pins per shape, refusal rows with `iter_calls == 0`),
`tests/utils/test_inputs.py::test_meta_cache_helpers_bypass_container_overrides`
(hostile dict/set/list through the cache helpers, incl. a hostile `fields`
dict through site B),
`tests/utils/test_input_values.py::test_dict_subclass_overrides_cannot_replace_the_shared_walk`
(site C + R-E) and
`::test_hostile_list_iteration_cannot_escape_the_order_walk` (site D).
Projections: the owner module docstring (shared-read contract + intentional
output separation) and the consumer docstrings. No GLOSSARY anchor (the
nomination's zero-hit grep stands; not re-swept as a verdict input).

## Verification

### Matrix

1. Cross-flavor policy mirroring - SEARCHED. The enumeration rule spans
   three flavors: the construction-time cache-key walk (`utils/inputs.py`,
   sites A/B + composed arms), the request-time drift fingerprint
   (`utils/write_transaction.py`, fully composed), and the set-input
   traversal (`utils/input_values.py`, sites C/D). The authorization flavor
   (`utils/permissions.py`, site F) was swept and rejected on contract
   (R-F), not missed. No fourth consumer-container walk exists (producer
   census: exactly three production importers of the owner after this
   change).
2. Sync/async twins - NO SUCH SURFACE. The owner and all four composed
   sites are pure in-memory reads with no await point, no executor, and no
   I/O; every consumer calls them from synchronous walks.
3. Derived rather than repeated knowledge - SEARCHED. Container MEMBERSHIP
   (which five types count) is spelled at the gates plus the dispatch; that
   is open Family `canonical-container-membership` (FB), a different item -
   this change touches no gate and no membership spelling (coupling: none).
   `dict(d)` copies and `dict.get` point reads derive nothing from the
   enumeration rule (R-E, R-H).
4. Inverse / round-trip pairs - SEARCHED, no such surface. The reads are
   one-way. The nearest pair shape - H's pairs-to-`dict` materialization -
   is a copy contract on framework-built triples, examined and rejected
   (R-H), not a second half of the enumeration grammar.
5. Contracts restated in another medium - SEARCHED. Every medium a change
   moves is classified in System trace. Two projection defects already homed
   by verified file items (referenced, not re-homed): File `utils/inputs.py`
   D1 (bare-`repr` prose limbs where bodies use the sort key) and File
   `utils/permissions.py` D1 (unconditional UNBOUND claim vs the dict-only
   conditional body; closeout homing).
6. Enforcement by omission - SEARCHED. Bound reads on consumer mappings
   elsewhere are the absence of the mechanism, not restatements: `related`
   membership/index reads in `iter_active_fields` (intentional separation
   recorded at `related_declaration_mapping`'s docstring: the traversal
   reads membership lazily - standing, trigger-checked, unfired),
   `tuple(dataclass_fields)` name iteration (Mapping-proofed, not
   dict-proofed; homed file-local by verified File `utils/input_values.py` -
   converged, not re-litigated), and bound reads on framework-owned
   containers (`safe_meta.get`, `kwargs.get("name")`, `cache.get`,
   `config.field_specs.get`). No new omission gap; nothing routes to the maintainer.

Standing triggers checked: canonical R4 (atom base-slot reads - no
spanning primitive at HEAD; WT `truth.text` is uncommitted concurrent
work), canonical R5 (hostile-mapping hardening - open family, opposite
accept-vs-refuse stance), canonical R6 / policies R3 (no owned
rejection-message grammar - none adopted). All unfired.

### Challenges

Each change posited on the rule's variation axes; authoritative definitions
counted (consumers, oracles, projections listed, never counted). Counts are
pre-change -> post-change; HEAD and WT agree on every count (concurrent
dirt touches no enumeration line).

- C1 - enumeration vehicle (live view vs snapshot): posit reading every
  dict through a snapshot. Owner + A + B + C + D move (5 -> 1). Site D is
  the sharp case: its live `list.__iter__` streams across `yield`s while
  the owner snapshots. The laziness is incidental, not contractual - no
  docstring, oracle, or caller requires incremental observation, the
  generator still yields element-by-element after composition, and the only
  divergence (mid-iteration mutation by the walker consumer) is performed
  by no caller and pinned by no oracle. CONFIRMED as one rule.
- C2 - sixth readable type: posit accepting one more built-in. Only the
  owner gains an arm (1 -> 1); A/B/C/D are single-shape gated and move
  only if their gates widen, which is FB's domain. This challenge draws
  the family boundary: membership is FB's, per-shape reads are this
  family's.
- C3 - base-slot mechanism: posit the slots being read through a new
  primitive (or the refusal widening). Owner + A + B + C + D move (5 ->
  1). THE consolidation evidence: one mechanism change, one edit.
- C4 - refusal stance: posit tolerating arbitrary iterables. Owner only
  (1 -> 1); A/B/C/D gate single shapes, so non-members never arrive.
  Refusal was already single-owned.
- C5 - point-lookup default (R-E independence): posit the absent default
  changing. Only `input_field_value` moves (1); the enumeration rule's
  axes (vehicle, sixth type, refusal, pair-vs-member) never move it.
  Independence evidence for the R-E rejection.
- C6 - related declarations restricted to dicts (R-F independence): posit
  the `Mapping` proof narrowing to `dict`. Only the permissions
  conditional collapses (1); the owner is unaffected. Independence
  evidence for the R-F rejection.

Experiment (execution-verified, `dry-20261001T190042-f7370b`): the one
exactness question for site D - a `list`+`dict` multiple-inheritance
instance would take the owner's dict-first arm while the site gates
list-only. All 10 pairs among the five built-ins raise instance lay-out
conflict at class creation, so no such instance is constructible: the
composition is exactly behavior-preserving on every constructible input.
The wrong result this rejects: an arm-order divergence hiding behind the
dict-first dispatch.

No `docs/dry/temp-tests/` scope was created: every static claim was
decided against committed bytes, and every execution ran through
`workspace.py` at the item address.

## Findings

### F1 - Container-enumeration reads (CONFIRMED + CONSOLIDATED, 5 -> 1)

Contract: enumerating a consumer-controlled built-in container reads every
member through the type's unbound iteration slot. Variation axes: dict
(pairs) vs the other four (members); the eager `tuple` vehicle. The
membership set is FB's axis, not this finding's.

Sites + roles: one authoritative definition,
`utils/canonical.py::base_container_values` (five arms + refusal); four
restatements now composing by name (A: `_hashable_meta_value` dict arm, B:
`canonicalize_set_meta_fields` dict branch, C: `iter_input_items` dict
arm, D: `iter_active_fields` list arm). Consumers: `_sorted_meta_values`,
the set/list hashable arms, the cache-key list/set arms, and the drift
fingerprint's three reads. Oracles and projections as in System trace.

Challenges: C1 5->1, C2 1->1 (boundary), C3 5->1, C4 1->1.

Owner + lifetime (principle 7): `base_container_values` - the narrowest
module every consumer already imports downward with no reversal
(`utils/inputs.py`, `utils/write_transaction.py`, now
`utils/input_values.py`; no cycle: the owner imports only `exceptions`
plus the concurrent `truth` leaf). No stored derivation: the owner is a
pure function, "not cached" (principle 4); no lifetime fields owed.

Migration: four one-line compositions (the unbound read becomes the owner
call; surrounding control flow, gating, sorting, and error wording
untouched) plus one import (`input_values.py` gains
`from .canonical import base_container_values`, mirroring the existing
import order in `utils/inputs.py`).

Distinct behavior: site D's live-to-snapshot vehicle change, analyzed in
C1 and closed by the MI experiment - unobservable on every constructible
input. The dict-first arm order stands (unreachable second arms are
unconstructible, not unspecified). R-E/R-F/R-G/R-H/R-I stay separate per
their rows.

Behavioral proof: execution-verified. P1: the family's oracle surface
(`test_canonical.py` + `test_input_values.py` + `test_inputs.py` +
`test_permissions.py`, 156 rows incl. all four hostile pins) green in a
fresh workspace copy (`dry-20261001T185900-faed65`, exit 0) - rejects a
behavior change at any composed line. P2: the new census gate green
(`dry-20261001T190027-ca539e`, 14/14 on a fresh sync at final bytes) -
rejects a miscounted population. P3: failability (see Structural gate).
A/B/C are additionally inspection-sufficient: the composed call evaluates
the identical `tuple(dict.items(x))` sequence the inline code consumed.

Structural gate:
`tests/utils/test_canonical.py::test_container_enumeration_reads_only_through_the_owner_or_a_named_separation`
- an exact-match AST census over the 120 package `.py` files for
`dict.items` / `<builtin>.__iter__` attribute reads, asserting the exact
multiset of 9 `(relpath, qualname)` hits (5 owner arms + the 4 named
separations). Point lookups and indexed reads are outside the census by
design (different operations, R-E). Negative control
(execution-verified): `prove` mutating site A back to the
behavior-identical `dict.items(v)` fails exactly the gate while all 13
behavior rows pass; restore byte-proved (blob `8839b38d` before and
after). First ran against the tree showing the rule holds (9/9, zero
allowlist drift).

Coupling: none. FB (`canonical-container-membership`) is adjacent but
independent: no gate, dispatch order, or refusal text moved.

Freshness: `utils/canonical.py` WT `d754e71c` / HEAD `7f5bb5f7`
(untouched); `utils/inputs.py` WT `8839b38d` / HEAD `0b7d353c`
(baseline WT `0826c9d4`); `utils/input_values.py` WT `463f81a8` / HEAD
`929e81b5` (baseline WT `905451cc`); `tests/utils/test_canonical.py` WT
`95e186d6` / HEAD `a1d76cc2`; read-only evidence
`utils/permissions.py` WT `bb3e0493` / HEAD `0e13b869`,
`utils/write_transaction.py` WT `db1efbca` / HEAD `20900a51`,
`tests/utils/test_inputs.py` WT `220fecd2` / HEAD `ef303037`,
`tests/utils/test_input_values.py` WT `69f7b2c0` / HEAD `2c6de200`,
`tests/utils/test_permissions.py` WT `71e1ff4b` / HEAD `abf30ad3`.
Searched population: 120 package files (AST probe) + HEAD word-boundaried
grep + `getattr`/alias sweeps. Excluded on the strength of its body:
every R-E..R-I site below; every module outside the hit list on the
strength of the empty census.

### R-E - Single-key base-slot lookup (REJECTED)

`utils/input_values.py::input_field_value` reads ONE field via
`dict.get(input_value, field_name)` with an absent default. Contract
difference: point lookup with `None`-when-absent vs full enumeration;
the `_field_name` normalization and the dict-vs-dataclass sniff are part
of its contract, and no enumeration-rule change (C1-C4) moves it (C5
counts 1). Composing it on the enumerating owner would need an O(n) scan
or a new point-lookup helper with one caller (principle 11). The
separation is already recorded at its docstring ("the single-field
sibling"). Reconsideration trigger: the owner gains a point-lookup arm,
or a change constrains point reads and enumeration together.

### R-F - Conditional related-mapping materialization (REJECTED)

`utils/permissions.py::_related_declarations` reads `dict.items` for
dicts and bound `.items()` for non-dict mappings. Contract difference:
conditional ACCEPT of arbitrary mappings vs the owner's REFUSE; composing
would change what is accepted, which needs a contract source (axis 6) -
and the only candidate source is the already-homed File `utils/permissions.py`
D1, whose verdict faulted the docstring's unconditional UNBOUND claim, not
the body's conditional accept. The WT line is hunt-dirtied
(`isinstance` -> `truth.is_instance`), a second bar to any edit.
Reconsideration trigger: related declarations restricted to dicts (C6),
or the owner gaining a mapping arm.

### R-G - Factory-meta exact-dict copy (REJECTED)

`utils/inputs.py::normalize_set_meta_for_factory` copies `meta` minus
reserved keys via `dict.items(meta)`. Contract difference: a filtering
materialization over an interpreter-built exact dict (`**meta` catch-all
at the sole production caller,
`utils/inputs.py::make_dynamic_set_getter.get_set_class`) vs a hostile
container read; the unbound spelling is defense in depth, exercised only
by a direct hostile-dict call in the oracle. Adjacent concurrent work
(the containment deletion around it) bars rework regardless; touched
nothing. Reconsideration trigger: a production caller passing a
possibly-hostile mapping.

### R-H - Field-spec kwargs copy (REJECTED)

`utils/inputs.py::build_strawberry_input_class` copies
`dict(dict.items(raw_kwargs))` for dict-shaped specs. Contract difference:
copy-into-exact-dict materialization over framework-built triples (all
four production callers pass emitted triples) with a lenient
non-dict-mapping `else` arm, vs enumeration for a walk. Reconsideration
trigger: a caller threading consumer mappings into field specs.

### R-I - Cache-key extras reads (REJECTED)

`utils/inputs.py::make_set_meta_cache_key` reads `dict.get` / `dict.items`
over `safe_meta`, a dict comprehension built two frames up - an exact
dict by construction. Not a hostile-container read; the unbound spelling
is incidental. (The `dict.get` pair is outside the gate census with R-E.)
Reconsideration trigger: `safe_meta` ever arriving as a
consumer-controlled value.

### Observed, not homed (uncommitted concurrent bytes)

WT-only unbound-slot sites, all inside truth-migration / typing dirt with
no ledger row: `rest_framework/sets.py` `tuple.__len__` / `tuple.__getitem__`
(4 hits, pair-shape validation), `types/relay.py` `dict.get`, `utils/querysets.py`
`dict.keys`, `utils/truth.py` `dict.get` + `str` renders (untracked file),
`utils/lazy.py` (untracked, zero hits). Excluded from the family verdict:
uncommitted bytes home no rows. The gate census runs over the package as
checked out; these sites are outside its operation scope (`items` /
`__iter__`) except none - verified green at WT.

## Defects

None new. Referenced (already homed, not re-homed): File `utils/inputs.py`
D1 (bare-`repr` prose limbs, homed at that item) and File
`utils/permissions.py` D1 (UNBOUND claim vs dict-only body, closeout
homing). The site-D vehicle analysis and the MI experiment closed without
a defect. No behavior defect, no guard gap, nothing for the maintainer.

## Pending execution

None. Every proof executed in the workspace copy at the item address; the
shared tree ran zero pytest. Sharded and Postgres cells are inapplicable
by construction: the owner and all four composed sites are pure in-memory
reads reaching no database, alias, or dialect decision, and every oracle
above runs on in-memory containers only (Worker-2 to judge).

## Judgment

CONFIRM-consolidated. The enumeration rule had five independently
maintained definitions (the owner plus four inline unbound reads); one
mechanism change now lands in one body. Counts: C1 5->1, C2 1->1, C3
5->1, C4 1->1, C5/C6 independence for the two contractual rejections;
five rejections with triggers (R-E..R-I), zero sub-rule families (no
index row beyond the five rejections is owed), zero defects, zero pending
execution. Net tracked change +88/-4 over three files, all green.

## Implementation (Worker-1)

Tracked edits (7 hunks vs `ITEM_BASELINE=ebefd760`, all attributed to this
item; every other hunk on these paths predates the baseline and was left
byte-identical):

- `django_strawberry_framework/utils/inputs.py` (+2/-2): `_hashable_meta_value`
  dict arm `:577` and `canonicalize_set_meta_fields` dict branch `:695`
  compose `base_container_values` (import pre-existing).
- `django_strawberry_framework/utils/input_values.py` (+3/-2): import
  `:42` (purely additive, mirroring `utils/inputs.py` order);
  `iter_input_items` `:110` and `iter_active_fields` `:340` compose the
  owner.
- `tests/utils/test_canonical.py` (+83/-0): `_READABLE_CONTAINER_NAMES` +
  `_unbound_enumeration_reads` helper + the census gate
  `:269` (imports `:15-:21` in the clean import block; body appended after
  the tail).

Concurrency attribution by diff content vs `git show HEAD:<path>` before
the first edit: all five production edit lines were context lines
identical between HEAD and WT (adjacent `isinstance` -> `truth.is_instance`
and containment-deletion hunks are the concurrent truth migration /
maintainer rework); both import inserts purely additive; no concurrent
line edited, reverted, or tidied. `utils/canonical.py` untouched.
Proposed Worker-0 transcription: Family `base-slot-container-reads` ->
consolidated; index row likewise; `## Owned changes` rows for the 3
paths above (+88/-4).

Gates (all in workspace copy `dry/baseslot-f45/consolidate`, slot-2):
ruff `check` + `format --check` on the 3 touched paths clean (shared
tree, post-edit); `check_trailing_commas.py` on the 3 touched paths 0
violations; basedpyright 0/0/0 (`dry-20261001T185936-02df43`); check_any
128 uses at 89 sites exit 0 (`dry-20261001T185944-9a104c`, ALLOWED_ANY
untouched - zero new Any/cast/suppression); truthful-reads tier-1 0 /
errors 0 (`dry-20261001T185945-6facf1`). Failability record
(`dry-20261001T185919-bc34dc`): baseline 14 passed, mutant exactly the
gate failing, restore byte-proved. Banned-word sweep of the additions:
`plan audit sweep restored hardening previously worker grader feedback`
zero hits (case-insensitive grep over the item diff). No `pragma: no
cover`. `mypy` never run, never cited.

## Index rows for Worker 0

(Worker-0 alone edits the plan; rows named here for transcription.)

- Family `base-slot-container-reads` | Owner
  `django_strawberry_framework/utils/canonical.py::base_container_values` |
  Files `utils/canonical.py`, `utils/inputs.py`, `utils/input_values.py` |
  Holding item Family `base-slot-container-reads` | consolidated (F1:
  5->1, C1/C3; R-E..R-I rejected with triggers)
- `single-key-base-slot-lookup` |
  `django_strawberry_framework/utils/input_values.py::input_field_value`
  (rejection recorded here; point lookup with absent default vs full
  enumeration) | `django_strawberry_framework/utils/input_values.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `base-slot-container-reads` | rejected (trigger: owner gains a
  point-lookup arm, or a change constrains point reads with enumeration)
- `conditional-related-mapping-materialization` |
  `django_strawberry_framework/utils/permissions.py::_related_declarations`
  (rejection recorded here; conditional accept of non-dict mappings vs
  refuse; WT line hunt-dirtied; converges with already-homed File
  `utils/permissions.py` D1) |
  `django_strawberry_framework/utils/permissions.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `base-slot-container-reads` | rejected (trigger: related declarations
  restricted to dicts, or owner gains a mapping arm)
- `factory-meta-exact-dict-copy` |
  `django_strawberry_framework/utils/inputs.py::normalize_set_meta_for_factory`
  (rejection recorded here; filtering copy over the interpreter-built
  `**meta` dict; adjacent concurrent containment rework) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `base-slot-container-reads` | rejected (trigger: a production caller
  passing a possibly-hostile mapping)
- `field-spec-kwargs-copy` |
  `django_strawberry_framework/utils/inputs.py::build_strawberry_input_class`
  (rejection recorded here; copy-into-exact-dict over framework-built
  triples with a lenient non-dict arm) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `base-slot-container-reads` | rejected (trigger: a caller threading
  consumer mappings into field specs)
- `cache-key-extras-framework-reads` |
  `django_strawberry_framework/utils/inputs.py::make_set_meta_cache_key`
  (rejection recorded here; reads over the framework-built exact
  `safe_meta` dict) | `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `base-slot-container-reads` | rejected (trigger: `safe_meta` arriving
  as a consumer-controlled value)

## Independent verification (Worker-2)

Address `dry/baseslot-f45/verify-1` (slot-3). Method note: the artifact
is one file, so `## Findings` was visible when the required reading
reached it; every count below was still re-derived with independent
tooling (my own AST visitor, my own greps, my own MI run, my own prove
manifest) and reconciled against the findings afterwards. Reconciliation:
zero differences - every site, count, and role reproduced exactly.

Own trace. The rule is the unbound-slot enumeration of a
consumer-controlled built-in container. Mechanism census with my own
`ast.NodeVisitor` (`Attribute` on a `Name` in the five builtins +
`items` / `__iter__`), run over all 120 package files at WT bytes and
over the same population at `ebefd760` bytes (3 WT files new vs the
baseline: `_multipart.py`, `utils/lazy.py`, `utils/truth.py`, all zero
hits): 13 hits pre, 9 post. Pre = 5 owner arms in
`utils/canonical.py::base_container_values` + 4 inline restatements (A:
`utils/inputs.py::_hashable_meta_value` dict arm; B:
`utils/inputs.py::canonicalize_set_meta_fields` dict branch; C:
`utils/input_values.py::iter_input_items` dict arm; D:
`utils/input_values.py::iter_active_fields` list arm) + 4 separations
(R-F `utils/permissions.py::_related_declarations`, R-G
`normalize_set_meta_for_factory`, R-H `build_strawberry_input_class`,
R-I `make_set_meta_cache_key`). Post = 5 + 4, A/B/C/D gone. My owner
choice is `base_container_values` (principle 7): the narrowest module
all three consumer files already import downward with no reversal, pure
function ("not cached", no principle-4 lifetime owed). My challenge
counts, re-derived: C1 vehicle 5->1, C2 sixth type 1->1 (FB boundary),
C3 mechanism 5->1, C4 refusal 1->1.

Enumeration + matrix, member by member. HEAD greps redone without
`\b` (git grep ERE does not honor it - my first two `\b` sweeps were
void and I re-ran them): `dict.items` code hits exactly owner + A + B
+ C + R-G + R-H + R-I + R-F (plus 3 prose mentions);
`list.__iter__` exactly owner + D; set/frozenset/tuple `__iter__`
exactly the owner arms; no unbound `keys` / `values` / `__getitem__` /
`__contains__` / `__len__` / `__str__` / `__repr__` reads (nearest
hits are a docstring, a Django `values("pk")`, and a comment).
`getattr(..., 'items' | '__iter__' | 'keys' | 'values')`: zero at HEAD
and WT. Alias form `= <builtin>.(items|__iter__)`: exactly C and D at
HEAD, zero at WT. `dict.get(`: R-E (`input_field_value`, committed at
HEAD) + R-I pair (committed) + bound `node_dict.get` reads (receiver
is a local, not the `dict` type). Call census of the owner: exactly 3
production importers (`utils/inputs.py`, `utils/input_values.py`,
`utils/write_transaction.py`); already-composing consumers confirmed:
`_sorted_meta_values`, the hashable set/list arms, the cache-key
list/set arms, the drift fingerprint's 3 reads. Axis 2: zero
`async`/`await` in `canonical.py` / `input_values.py` - no such
surface. Axis 6 absences I checked beyond the artifact's list:
`utils/errors.py:367` bound `.items()` on Django's `error_dict`
(Django-owned, fail-closed `try/except`); `normalize_field_name_sequence`
`tuple(value)` (developer-declared Meta shape validation, fail-loud,
different subject); `basis.items()` / `safe_meta.get` / `cache.get`
(framework-owned). No new gap, nothing for the maintainer.

Roles + oracles. Sites/roles confirmed as found. No oracle reads the
owner to compute an expectation: the hostile pins install
raising `items` / `__iter__` / `get` overrides and spell literals
(`[("name", "x")]`, `[("title", "x")]`, `["contains", "exact"]`); the
two direct owner tests assert literals against the owner itself, which
is legitimate. Point lookups and indexed reads stay outside the census
by design (different operations).

Equivalence, point (a) (site D vehicle). Re-derived: (1) No caller
mutates the walked list mid-iteration - the order normalizer, both
permission partitioners, and the filter loop each build their own
output (`result` / `leaf_paths`+`branches` / `data`). (2) No
docstring, oracle, or caller requires incremental observation: the
only "stream" prose names yield order, which is preserved (the
generator still yields per element); the "lazily" prose is about the
`related` mapping reads, not site D. (3) A hostile `__iter__` never
ran before either (unbound both times), pinned by the raising oracle.
(4) MI experiment re-run by me: all 10 builtin pairs raise instance
layout-conflict, 0 constructible. Laziness-incidental: ACCEPTED. One
sub-case I weighed explicitly: a hostile `__hash__` mutating its
ancestor dict mid-walk would raise `RuntimeError` pre-change (live
view) but not post-change (snapshot). That divergence needs a hook
attacking its own walk - exactly the interference class the module
exists to neutralize - is pinned by no oracle, promised by no
docstring, and the snapshot is the owner's documented vehicle (C1
posits exactly this). Incidental, not contractual.

Point (b) (dict-first arms). The owner body dispatches dict first,
then set / frozenset / list / tuple; A/B/C gate dict-only and D gates
list-only (each a single `truth.is_instance` shape check, verified in
the diff context). With MI instances unconstructible, the gated shape
is the dispatched arm on every constructible input - exact. A/B/C
additionally evaluate the identical `tuple(dict.items(x))` sequence
the inline code consumed (each consumed within one expression; the
per-pair callees `_hashable_meta_value`, `_sorted_meta_values`,
`_field_name` are non-mutating, and cyclic re-entry raises identically
either way).

Point (c) (rejections + FB boundary). R-E..R-I each carry a contract
difference, a trigger, and a home; converge-claims re-read at the
standing records: canonical R4 (atom rendering vs enumeration; no
spanning primitive at HEAD, WT `truth.text` concurrent), R5
(accept-vs-refuse), R6/policies R3 (no rejection grammar), File
`utils/inputs.py` D1 (4 bare-`repr` limbs, homed there), File
`utils/permissions.py` D1 (unconditional UNBOUND claim faulted, body
stands), input_values FL1 (`__dataclass_fields__` walk file-local).
Durable homes: R-E and R-F have pre-existing docstring clauses (the
"single-field sibling" sentence; the "different contracts, not a
missed merge" sentence); R-G/R-H/R-I ride the plan index rows, matching
verified precedent (f44 same practice). FB boundary: the item diff
touches no gate, dispatch-order, or refusal text - 4 one-line read
swaps + 1 additive import + the additive gate - so C2's split holds
and coupling is none. R-G's sole-production-caller claim confirmed
(only `get_set_class` with its interpreter-built `**meta` dict; rest
are tests/docstrings/gate). R-F's WT line is truth-dirtied concurrent
work, untouched. Freshness re-hashed same-kind: `8839b38d`,
`463f81a8`, `95e186d6`, `d754e71c` all match (`git hash-object`;
canonical.py untouched by the item).

Point (d) (gate + failability). Re-ran the gate file 14/14 and the
behavior scope 142/142 in my copy (total 156, matching the claimed
surface). Failability re-proved with my OWN manifest (site A hand
copy): exit 0, exactly the gate failing, restore byte-proved
(`8839b38d` before and after). The 9-hit multiset is exact with zero
allowlist drift (my census byte-matches the gate's expectation), and
the `items` / `__iter__` operation cut is right: no other unbound
enumeration-slot form exists at HEAD, and every WT addition
(`dict.get`, `dict.keys`, `tuple.__len__` / `__getitem__`) is
concurrent dirt outside the cut. Pending-None correct: every proof
executed. Concurrency: all 4 edited production lines verified
byte-identical between HEAD and baseline blobs (C :108/:109, D
:372/:339, A :571/:577, B :684/:695); the WT-vs-HEAD hunks containing
them are adjacency with concurrent truth-migration lines, attributed
by content; imports additive; test diff zero minus-lines; canonical.py
untouched.

Point (e) (tier + gates). `tests/` tier ACCEPTED: the gate asserts a
package-source structural property unreachable from any GraphQL query
(AGENTS.md weakest-tier rule), and f39's AST census gate also landed
in `tests/`. `ruff format --check` + `ruff check` on all three touched
paths: clean. Banned-word sweep of the test additions: zero hits. Type
gates re-run in my copy: basedpyright 0/0/0, check_any 128 uses at 89
sites exit 0, truthful-reads tier-1 0 / errors 0 - all vs the run-11
baseline. No new cast/Any/suppression in the item diff, ALLOWED_ANY
untouched, no import cycle (`input_values` -> `canonical` ->
`exceptions` + stdlib-only `truth`). mypy never run, never cited.
Sharded/PG inapplicable-by-construction ACCEPTED: pure in-memory reads
reaching no database, alias, or dialect decision, oracles on in-memory
containers only.

Defects: none (Worker-2). Verdict: verified.
