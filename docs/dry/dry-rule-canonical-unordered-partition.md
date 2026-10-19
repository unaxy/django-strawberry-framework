# DRY review: `canonical-unordered-partition`

Status: verified
Run: 0.0.15 2026-10-09-13

Item kind: FAMILY (responsibility family). Owner re-derived fresh, not
inherited: a partition predicate in
`django_strawberry_framework/utils/canonical.py` is the principle-7
owner. The duplication is CONFIRMED (one definition per walk at both
states: the inputs-side unordered half plus the fingerprint-side
ordered half) but the consolidation is BLOCKED on concurrent dirt:
every line it would edit is truth-migration with no ledger row, and
the predicate body must spell the WT real-class test from untracked
`utils/truth.py`. Zero production edits, zero test edits. Migration,
agreement gate, and rejection home-clauses specified for the landing
after that dirt commits.

Concurrency: all three indexed files carry concurrent dirt (truth
migration + maintainer rework, no ledger row covering any of it)
plus the surviving f45-ledgered composition in `utils/inputs.py`
(site B, the set-meta dict-branch read). Attribution below is by
diff content vs `git show HEAD:<path>`; every concurrent byte
preserved, nothing touched. The f46 S1 nomination was INPUT only:
every count here was re-derived with fresh censuses at current
bytes, and the nomination's counts are stale (see System trace).

Baselines: `ITEM_BASELINE=247bec86253b7a711109fd67138806517677719f`
(resolves; item-scope diff on the three indexed files vs WT is
empty). HEAD `23b5f421` unmoved throughout. Dispatch pins verified
at task start and unchanged: `utils/inputs.py` WT `0b8d3daa` / HEAD
`c199eaa4`, `utils/write_transaction.py` WT `50909be8` / HEAD
`2b9f861c`, `utils/canonical.py` WT `23a7c41a` / HEAD `a1209117`.
Address `dry/canonpart-f64/consolidate` (slot-2; every workspace
proof ran there).

Gates (tree-state, zero-edit item; all in the workspace copy):
basedpyright 0 errors / 0 warnings / 0 notes
(`dry-20261009T215931-36c907`, exit 0); floor
(`-p pyrightconfig.floor.json`) 0 errors / 0 warnings / 0 notes
(`dry-20261009T220044-7a5c99`, exit 0); truthful-reads tier-1 0 /
errors 0 over 120 files (`dry-20261009T220155-97e398`, exit 0).
No ruff run (zero edits, zero paths touched). No pytest for the
counts (every verdict below is static against committed bytes; a
test run proves nothing about definition counts); the one pytest
run is the `## Pending execution` oracle re-run - the migration
handoff, not count evidence - 9/9 green
(`dry-20261009T220215-fc6ef3`).

## System trace

The rule: within the canonical walks, `{set, frozenset}` are the
unordered members (sorted to process-stable order) and `{list,
tuple}` the ordered ones (order preserved); `dict` pairs sort by
key in both walks (shared, never partitioned). Two walks compose
the owner's reads plus its sort key (producer census: exactly 2
production importers of `canonical_sort_key` at both states -
`utils/inputs.py`, `utils/write_transaction.py` - plus the owner;
`base_container_values` gains the f45-ledgered
`utils/input_values.py` reads-only importer at WT). No third
canonical walk exists at either state.

The two halves are spelled INVERTED: the inputs walk tests the
unordered half positively (ordered falls through to passthrough);
the fingerprint dispatch tests the ordered half positively
(unordered is the residual `else`). Each half verified complete
over the non-dict four by full-function reads at both states:

- Half U - inputs unordered test. HEAD: two inline
  `isinstance(x, (set, frozenset))` in
  `utils/inputs.py::canonicalize_set_meta_fields` (:570 the
  fields gate, :574 the dict-value arm). WT: one
  `_UNORDERED_TYPES` table (:526, concurrent insert) with two
  by-name walk uses (:582, :586). Sort-vs-passthrough for the
  `Meta.fields` canonicalization walk.
- Half O - fingerprint ordered arm. HEAD:
  `utils/write_transaction.py::_field_fingerprint` :1056
  `elif isinstance(item, (list, tuple))`. WT: :1062
  `elif truth.is_instance(item, list) or
  truth.is_instance(item, tuple)` (concurrent rewrite).
  Order-preserving `[...]` emission; the `else` catches
  set/frozenset by elimination (comment + `set | frozenset`
  annotation name them; no positive test at either state).

Nomination deltas (all re-derived; the f46 S1 counts do not
survive the rebase): the Layer-6 hashable/cache-key walk is gone
at BOTH states (`_hashable_meta_value`,
`make_set_meta_cache_key`, `_META_CONTAINER_TYPES`: zero hits
package-wide at HEAD and WT, with their tests), taking three
HEAD unordered sites and the ordered inputs site with it; the
fingerprint unordered arm is the residual `else` at BOTH states
(no explicit `(set, frozenset)` test - the nominated `:1060`
predates the restructure); f45 site A died with its function,
site B survives as WT `:587`
(`for key, value in base_container_values(fields)`, buildable).
Partition-rule total at CURRENT bytes: unordered half 1 WT
(table) / 2 HEAD (inlines, walk only); ordered half 1 WT / 1
HEAD - 2 definitions WT, 3 spellings HEAD. (The declaration
reject, HEAD `:817` / WT `:833` by-name use, is a separate rule:
R1.)

Consumers (invoke or derive, never re-define): the `Meta.fields`
canonicalization walk (half U -> `_sorted_meta_values` -> owner
reads), the drift fingerprint (gate -> dict / ordered /
residual arms -> owner reads), and the declaration gate as a
WT by-name consumer of the moved spelling (excluded rule,
retargeted by the migration). Producer census above; no
re-export; no existing `is_unordered*` / `is_ordered*`
partition predicate anywhere (word census zero hits outside
this cycle's own item list).

Oracles (all independent: literal containers in, literal
lists/dicts/digest-relations out, literal refusal text, or
lying overrides; none reads the owner or the partition
spelling): `tests/utils/test_canonical.py` three sort-key
totality rows; `tests/utils/test_inputs.py`
`test_normalize_field_name_sequence_rejects_unordered_sets`,
`test_meta_fields_canonicalization_bypasses_container_overrides`,
`test_read_set_meta_fields_canonicalizes_sets_without_mutating_source`,
`test_normalize_sequence_unordered_rejection_names_the_set_type`;
`tests/mutations/test_write_transaction.py`
`test_field_fingerprint_covers_container_kinds_and_is_deterministic`
(pins unordered-sorted via set-equality AND ordered-preserved
via list-inequality) and
`test_field_fingerprint_orders_by_a_guarded_key_not_a_bare_repr`.
Projections: the owner module docstring (the Ordering bullet),
the walk docstrings/comments, the residual comment/annotation.
No GLOSSARY anchor (word census over `docs/GLOSSARY.md`: zero
hits; spec hits are result-ordering prose, not this rule).

## Verification

### Matrix

1. Cross-flavor policy mirroring - SEARCHED. The partition
   spans the construction-time `Meta.fields` walk and the
   request-time drift fingerprint. Adjacent flavors with
   same-pair spellings were each read at bytes and decided on
   contract: the declaration unordered-reject (R1), the
   hook-view freeze finalize arm (R2), the seal exact
   taxonomy (R3), the variable freezer set/sequence split
   (R4), the traversal list-shape gate (R6),
   the snapshot six-set (R7), the canonical dispatch
   arms (R8), and every per-domain ordered-pair gate
   (R5: standing domains trigger-checked, fresh sites
   read at bytes, one converge - details there). No
   third canonical walk exists (producer census both
   states).
2. Sync/async twins - NO SUCH SURFACE. The halves and both
   walks are pure in-memory tests with no await point, no
   executor, and no I/O; `await` census over the three
   indexed files is 0/0/0 at WT and 0/0/0 at HEAD.
3. Derived rather than repeated knowledge - SEARCHED. The
   partition is spelled 2x in inverted halves (F1); the
   real-class test mechanism is spelled 2x in WT-only dirt
   (`_is_one_of` bodies vs the or-chain shape -
   observed-not-homed); the residuals (inputs fallthrough,
   fingerprint `else`) and their comment/annotation prose
   examined (projections, not definitions). Reads over
   framework-built containers examined and excluded on body.
4. Inverse / round-trip pairs - NO SUCH SURFACE (examined).
   The halves are one-way classifications. The nearest pair -
   sorted-list output versus digest-string output - is the
   intentional output separation the standing file-item R7
   records; trigger re-checked unfired (encodings still
   differ in the bodies).
5. Contracts restated in another medium - SEARCHED. Every
   medium a change moves is classified in System trace. One
   projection defect already homed by a verified file item
   (File `utils/inputs.py` D1, bare-`repr` prose limbs -
   the `canonicalize_set_meta_fields` docstring still says
   "repr-sorted" while the body sorts by the canonical key;
   referenced, not re-homed). Oracles spell literals; none
   reads the owner.
6. Enforcement by omission - SEARCHED. Both canonical walks
   encode the partition (2/2, inverted halves); the
   traversal needs no ordering decision (R6); the
   declaration gate enforces its own rule (R1); every
   other walk answers a different question. No omission gap;
   nothing routes to the maintainer.

Standing triggers checked: file-item R7 (output separation -
encodings still differ), R4/R5/R6 (no spanning primitive, no
mapping arm, no message grammar - none adopted), f45 R-E..R-I
(reads-axis separations - untouched by this item), and the
f46 R1/R2/R3/R6/R7/R8/R10/R11 separations (each re-checked at
current bytes in its R section; all unfired). The f46
`_is_one_of`-triple observation stands (third site
re-verified at `rest_framework/resolvers.py:755`; still
WT-only dirt, still unhomed).

### Challenges

Each change posited on the rule's variation axes;
authoritative definitions counted (consumers, oracles,
projections listed, never counted). The declaration gate is
excluded from every count (R1); its WT by-name use is a
consumer the migration retargets.

- C1 - `frozenset` turns ordered. Half U narrows (WT: the
  table; HEAD: both inlines) + half O widens (the elif
  gains `frozenset`; residual comment/annotation prose
  listed, not counted): WT 2, HEAD 3 spellings. THE
  duplication evidence.
- C2 - `list` turns unordered. Half U widens + half O
  narrows: WT 2, HEAD 3 spellings. Same evidence, opposite
  direction.
- C3 - sixth container joins as unordered. Half U widens;
  the fingerprint residual catches it with no executable
  move (comment/annotation prose only): WT 1, HEAD 2 +
  prose. The residual halves the obligation on this axis -
  but C1/C2 still move both walks.
- C4 - sixth container joins as ordered. The inputs
  fallthrough catches it with no move; half O widens:
  count 1. Mirror of C3.
- C5 - reorder a spelling tuple/table. Count 0 (cosmetic;
  `isinstance`/`or`-chain order is irrelevant, and the
  WT halves already spell the mechanism differently).
- C6 - real-class mechanism change (truth API). WT: the
  `_is_one_of` body + the or-chain shape (table-use sites
  compose the helper by name): count 2. HEAD: bare
  `isinstance` at all three spellings: count 3. Second
  axis, same verdict.

No read-only probe was needed for the counts: every count
above is decided statically against committed bytes
(pair-tuple census, or-chain census, separate-arm census,
type-identity census, importer census, zero-`await`
census), so no `temp-tests/` scope was created and no
pytest ran for the counts. Workspace runs: the three
tree-state gates (ids in the header block) plus the `##
Pending execution` 9-node oracle re-run
(`dry-20261009T220215-fc6ef3`, exit 0, 9/9) - the
migration-handoff equivalence witness, not count evidence.
One interpreter-semantics probe (bare `python -c`, reads
nothing, mutates nothing) re-verified feign-never-hide for
the blocking record: a non-member with `__class__ = set`
passes `isinstance(x, (set, frozenset))` while its real
class is not a member; a real member passes regardless of
a lying `__class__`.

## Findings

### F1 - Canonical unordered/ordered partition (CONFIRMED count-2, BLOCKED on concurrent dirt, zero edits)

Contract: within the canonical walks, `{set, frozenset}`
are unordered (sorted to process-stable order) and
`{list, tuple}` are ordered (order preserved); `dict`
pairs sort by key in both walks. Variation axes: the
half memberships (C1-C4) and the real-class mechanism
(C6). Follow-on behavior per walk (passthrough vs digest
emission, budgets, cycle guards, leaf rendering) differs
and stays with each walk.

Sites + roles: two authoritative definitions in inverted
halves (U: inputs unordered test; O: fingerprint ordered
arm - spans in System trace). Consumers, oracles,
projections as in System trace.

Challenges: C1 WT 2 / HEAD 3, C2 WT 2 / HEAD 3, C3 WT 1 /
HEAD 2 + prose, C4 1, C5 0, C6 WT 2 / HEAD 3. Inverted
halves do not defeat the count: no single site states
the full partition, and a classification-axis change
moves both walks (C1/C2); the owner states both halves
once.

Owner + lifetime (principle 7): a partition predicate in
`utils/canonical.py` (names for the landing item;
`is_unordered_container` / `is_ordered_container` fit the
module's vocabulary - or one partition table read by
both). Responsibility: the module already owns the
readability contract, the refusal, and the sort key both
walks import downward with no reversal (2 importers at
HEAD, 2 + 1 reads-only at WT); the predicate makes
half-agreement by construction rather than by parallel
memory. Dependency direction wins cleanly (no consumer
imports sideways). Pure function, "not cached": no
principle-4 lifetime owed.

Migration (specified, not landed): (1) one unordered-half
+ one ordered-half spelling in `canonical.py` read by
BOTH new predicates, spelling the committed real-class
test; (2) half U (gate + dict-value arm) composes the
unordered predicate by name; the WT table + local
`_is_one_of` deleted; (3) half O (the elif) composes the
ordered predicate by name; the residual `else` stays
residual (comment/annotation refreshed, never
restructured into a positive test - that would add a
refusal the walks do not have today); (4) the R1 WT
use retargeted (consumer of the moved spelling); (5) the
specified agreement gate lands in
`tests/utils/test_canonical.py` (f39/f45 tier precedent);
(6) the R1-R8 home-clauses below land as one docstring
clause each at the stated homes.

Distinct behavior: each walk keeps its follow-ons
(passthrough vs `s{`/`[` emission, budgets, guards,
encodings); the residuals keep their shape; the refusal
text stays single-sited.

Behavioral proof: static-reviewed. P1: the halves
verified complementary-and-complete over the non-dict
four at both states (full-function reads of
`canonicalize_set_meta_fields` and `_field_fingerprint`;
dict arms + residuals cover the remainder) - rejects
silent divergence (halves agree today; no behavior
defect). P2: the whole-package censuses (HEAD pairs
6 + 26; WT pairs 4 + 20; or-chains 8; separate arms 2;
type-identity 1; importer census; zero-`await` census) -
rejects a third partition spelling. P3: the predicate
must spell the WT real-class test (refuse-vs-passthrough
divergence on the inputs path: the unordered test is
FIRST there, no membership gate precedes it, so an
`isinstance` spelling feign-admits a non-member into
`_sorted_meta_values`, where the truth-based owner
REFUSES - while current WT misses the feigner at both
tests and passes it through to the declaration gate;
verified against the bodies + the feign probe) - rejects
a HEAD-shaped landing. No execution for the counts:
counts and control-flow shape are decided from committed
bytes; nothing ordering-observable beyond the oracles,
transactional, or async is involved. The executed part
is the `## Pending execution` oracle re-run
(migration-handoff equivalence, 9/9 green), not count
evidence.

Structural gate: SPECIFIED, not landed. The landing item
adds an agreement test asserting the predicates/table,
both composition sites (no residual pair literal:
exact-match census over the two walk modules, same
technique as the f45 census gate), and the residuals
untouched. Negative control: a behavior-preserving hand
copy - re-spell one half as an inline pair with identical
members - fails exactly the gate while all behavior rows
pass (the copy is correct). First run must show the rule
holding (halves agree today). NOT landed now: the gate
would pin `_UNORDERED_TYPES` / `_is_one_of`, private
names that exist only in uncommitted dirt (absent at
HEAD); a gate born on dirt breaks on the migration's
rename and gets weakened, not fixed. The landing item
runs it via `prove` with restore byte-proof.

Coupling: open Family `canonical-container-membership`
(F1) - the fingerprint residual's correctness assumes
the gate admits exactly the five (the f46 C5
admit-without-arm coherence note); the partition
landing follows the membership landing, or lands with
it - partition-first pins the halves while the gate
still double-spells the five. The f45 site-B read line
sits inside the blocked hunk (buildable, untouched -
the consolidation needs the gate lines, not the read).
No other coupling: no ladder, refusal text, budget, or
follow-on moves in this item.

Blocking record (exact hunks, all concurrent, no ledger
row - touch nothing):

- `utils/inputs.py @@ -515,19 +517,24 @@`: the
  `_UNORDERED_TYPES` table (WT :526) + `_is_one_of`
  (WT :529-531) inserts are truth-migration inserts.
- `utils/inputs.py @@ -565,14 +575,16 @@`: the half-U
  gate rewrites (WT :582/:584/:586) are the same
  migration. (The f45-ledgered `:587` read line sits in
  this hunk and is buildable by content - but the
  consolidation needs the gate lines, not the read.)
- `utils/inputs.py @@ -806,37 +818,41 @@`: the R1
  use rewrite (WT :833) is the same migration (the
  migration retargets this consumer use).
- `utils/write_transaction.py @@ -1047,20 +1053,20 @@`:
  the half-O or-chain (WT :1062) + `cast` (WT :1069)
  are the same migration.
- `utils/canonical.py @@ -1,4 +1,4 @@` + `@@ -70,33
  +70,33 @@`: appending the owner + home-clauses
  rewrites the concurrent docstring/dispatch hunks.
- Regardless of shape, the predicate body must spell the
  WT real-class test - `truth.is_instance` from
  untracked concurrent `utils/truth.py` (P3 above). An
  `isinstance` spelling diverges refuse-vs-passthrough
  on the inputs path.
- Deleting the WT table deletes concurrent lines;
  retargeting the WT uses rewrites concurrent lines.
  Every consolidation shape touches concurrent bytes:
  blocked, zero edits.

Freshness: `utils/canonical.py` WT `23a7c41a` / HEAD
`a1209117` / baseline `23a7c41a`;
`utils/inputs.py` WT `0b8d3daa` / HEAD `c199eaa4` /
baseline `0b8d3daa`; `utils/write_transaction.py` WT
`50909be8` / HEAD `2b9f861c` / baseline `50909be8`
(baseline == WT on all three; item diff empty).
Read-only evidence (WT/HEAD): `utils/input_values.py`,
`utils/querysets.py`, `utils/errors.py`,
`rest_framework/resolvers.py`, `rest_framework/sets.py`,
`filters/sets.py`, `filters/base.py`,
`filters/inputs.py`, `list_field.py`,
`optimizer/extension.py`,
`extensions/resource_policy.py`, `types/base.py`,
`testing/client.py`, `optimizer/lateral_fetch.py`,
`optimizer/selections.py`, `types/converters.py`,
`utils/relations.py`, `tests/utils/test_canonical.py`,
`tests/utils/test_inputs.py`,
`tests/mutations/test_write_transaction.py` (pins in
`## Judgment`). Searched population: 121 package files
at WT, 118 at HEAD (3 WT-new: f39-ledgered
`_multipart.py` + untracked `truth.py` / `lazy.py`),
via the pair-tuple census, the or-chain census, the
separate-arm census, the type-identity census, the
importer census, and the zero-`await` census. Excluded
on the strength of its body: every R1-R8 site; every
module outside the hit lists on the strength of the
empty censuses; untracked `truth.py` / `lazy.py` as
uncommitted bytes (no row homes on dirt).

### R1 - Declaration unordered-reject (REJECTED, separate rule)

`utils/inputs.py::normalize_field_name_sequence`
(HEAD :817 inline; WT :833 by-name use of the moved
spelling). Contract difference: declaration-shape
validation ("a declared write-flavor field sequence
must be ordered; unordered rejected because
per-process iteration order would make generated
names/SDL nondeterministic") versus canonicalization
("unordered walked values are sorted to stable form").
The sharpest split, re-verified in the body: the gate
ACCEPTS arbitrary iterables via `tuple(value)` (WT
:842) - the exact shape canonical refuses. Different
subject (declared Meta sequences vs walked values),
different follow-on (reject vs sort), opposite stance
on foreign iterables. The WT by-name use makes it a
consumer of the moved spelling (retargeted by step 4
of the migration), not a family member. Reconsideration
trigger: the gate consuming a canonical-walk ordering
decision (sort/preserve) rather than rejecting, or a
walk consuming its verdict. Durable home owed: one
clause at the gate (landing with F1's home-clauses).

### R2 - Hook-view freeze finalize arm (REJECTED, converge)

`rest_framework/resolvers.py::_finalize` (WT :831
`_is_one_of(source, (set, frozenset))` -> frozenset,
else tuple). Converge with f46 R1 on fresh evidence:
body re-read at WT bytes - mutability-descent
rendering through BOUND reads (`_entries` uses
`iter(container.items())` / `iter(enumerate(container))`),
fail-closed leaf allow-list, per-type conversions;
the walk does not compose `base_container_values`
(producer census: no import at either state).
Contract difference stands: descent membership vs
readability. Reconsideration trigger (standing): the
freeze walk composing `base_container_values` for its
reads. Durable home owed: one clause at the freeze
table (landing with F1's home-clauses).

### R3 - Seal exact-type taxonomy (REJECTED, converge)

`utils/querysets.py::_is_exact_sequence` /
`_is_exact_tuple_or_list` / `_is_exact_set` (WT
:1137/:1146/:1151). Converge with f46 R2 on fresh
evidence: bodies re-read - exact-type membership,
subclasses EXCLUDED to the provenance proof ("a
`list` / `dict` SUBCLASS can override `__iter__` /
`items`", verbatim in the owner docstring), versus
subclass-inclusive readability. Reconsideration
trigger (standing): either side changing its subclass
stance. Durable home owed: one clause at
`_is_plain_container`.

### R4 - Variable-value freezer set/sequence split (REJECTED, converge)

`optimizer/extension.py::_freeze_variable_value`
(WT :415 sequence test, :448-458 set-vs-sequence
freeze arms). Converge with f46 R6 on fresh evidence:
body re-read at WT bytes - still ABC-accepting
(`isinstance(value, Mapping)` / `isinstance(value,
Set)`; only the sequence half migrated to the
truth or-chain, mechanism-only), degrade-to-opaque
for unknowns, exact-type scalars, iteration "on its
own terms". Opposite stance on unknown shapes
(accept-degrade vs refuse) and on reads (bound vs
base-slot). Reconsideration trigger (standing): the
freezer narrowing to builtins with a refuse/leaf
stance. Durable home owed: one clause at the
freezer.

### R5 - Per-domain pair gates (REJECTED, shared idiom)

The `(list, tuple)` / `(set, frozenset)` / real-2-tuple
idiom across sixteen domains, each answering its own
question (ten standing domains trigger-checked, five
fresh sites read at bytes, one converge; HEAD census
26 ordered + 6 unordered sites, all classified; the
eleventh standing domain, `connection.py`, carries
zero pair spellings at either current state):
`extensions/resource_policy.py`
width/node charging (`_charge_container`,
`_type_system_directives`); `filters/base.py`
lookup-value arity (five gates);
`filters/inputs.py::_require_list_container`
(widget list-shape gate);
`filters/sets.py::_validate_logic_branch_shape`
(branch sequence-vs-single);
`rest_framework/resolvers.py` error-shape
(`_error_detail_codes`) and many-decode gates;
`testing/client.py` multipart-envelope path walk;
`optimizer/lateral_fetch.py` lookup-RHS shape;
`optimizer/selections.py` re-iterable guard;
`utils/relations.py::_link_field_tuple` (link-field
coercion); `utils/querysets.py` SQL/node guards;
`types/base.py` interfaces-shape validation;
`types/converters.py` grouped-choices detection
(two sites); `rest_framework/sets.py` hook-map
2-tuple checks (two sites - entry shape, sets
rejected); `optimizer/extension.py::_stash_union`
(stash merge); `utils/errors.py::_str_list`
(Iterable-inclusive fail-closed); `list_field.py`
order-RHS four-table (converge f46 R4: all four
treated uniformly, `dict` absent, bound iteration -
no unordered/ordered distinction in the body).
No two move together; the producer census proves no
domain adopted the canonical contract at either
state. Reconsideration trigger: a domain adopting
the canonical readability contract for its gate.
Durable home owed: one clause at the canonical
dispatch (the standing single-shape-dispatch
exclusion, extended to pairs).

### R6 - Traversal list-shape gate (REJECTED, converge)

`utils/input_values.py::iter_active_fields` (WT :344:
order-input list elements must be mapping/dataclass
values). Converge with the f46 R10 direction on fresh
evidence: body re-read - traversal-shape validation
with no ordering decision and no sorting; the
traversal consumes owner READS only (f45-ledgered),
never the sort key. Contract difference:
traversal-shape membership vs partition. Reconsideration
trigger: the traversal gating an ordering decision.
Durable home owed: none (standing homes stand).

### R7 - Mutable-snapshot six-set (REJECTED, converge)

`utils/write_transaction.py::_MUTABLE_SNAPSHOT_TYPES`
(canonical-five + `bytearray`). Converge with f46 R3
on the standing body-read: mutable-in-place
snapshot-vs-alias decision (`bytearray` MUST
fingerprint - mutable - but is a leaf, never walked)
versus walk-vs-leaf readability; the sets already
differ by design. No partition distinction inside
(the snapshot site does not sort). Reconsideration
trigger (standing): the snapshot site composing the
canonical predicate for its five-subset. Durable home
owed: one clause at the snapshot table.

### R8 - Canonical dispatch arms (REJECTED, no distinction)

`utils/canonical.py::base_container_values` five arms
(WT :73-82 `truth.is_instance`, HEAD :73-82
`isinstance`). All five arms do the identical thing
(yield members/pairs through the base slot); the
dispatch draws no unordered-vs-ordered distinction -
the partition lives downstream in the walks, never
here. Reconsideration trigger: an arm gaining
order-dependent behavior. Durable home owed: none
(the dispatch docstring already states the read-only
contract).

### Observed, not homed (uncommitted concurrent bytes)

WT-only, no row homes on dirt: the `_is_one_of`
real-class test spelled identically 3x
(`utils/inputs.py:529`,
`utils/write_transaction.py:848`,
`rest_framework/resolvers.py:755` - the third
re-verified byte-identical in shape this item); the
WT or-chain pair dispatches (same pairs as the HEAD
tuples - no new spelling); untracked `utils/truth.py`
/ `utils/lazy.py`. Converges with the f46
observation: the landing item re-checks whether the
committed migration kept the `_is_one_of` triple (a
fourth `utils` home candidate) or collapsed it.

## Defects

None. The fingerprint residual's admit-without-arm
coherence (a gate-admitted-but-unarmed value emits no
parts and no refusal) is the f46 C5 note, already
recorded there as not-a-defect: the halves agree
today at both states, so the hazard materializes only
on a divergence the consolidation exists to prevent -
referenced, not re-homed. The `canonicalize_set_meta_fields`
"repr-sorted" docstring limb is homed File
`utils/inputs.py` D1 - referenced, not re-homed. No
guard gap, nothing for the maintainer.

## Pending execution

proof: `uv run python scripts/workspace.py run
dry/canonpart-f64/consolidate -- pytest
tests/utils/test_canonical.py::test_canonical_sort_key_totally_orders_mutually_unorderable_types
tests/utils/test_canonical.py::test_canonical_sort_key_keeps_identical_reprs_distinct
tests/utils/test_canonical.py::test_canonical_sort_key_repr_error_propagates
tests/utils/test_inputs.py::test_normalize_field_name_sequence_rejects_unordered_sets
tests/utils/test_inputs.py::test_meta_fields_canonicalization_bypasses_container_overrides
tests/utils/test_inputs.py::test_read_set_meta_fields_canonicalizes_sets_without_mutating_source
tests/utils/test_inputs.py::test_normalize_sequence_unordered_rejection_names_the_set_type
tests/mutations/test_write_transaction.py::test_field_fingerprint_covers_container_kinds_and_is_deterministic
tests/mutations/test_write_transaction.py::test_field_fingerprint_orders_by_a_guarded_key_not_a_bare_repr
-n0 --no-cov -q` - discharges F1's migration-handoff
equivalence for the unblock item (3 sort-key totality
nodes, 4 inputs unordered/canonicalize nodes, 2
fingerprint partition nodes; every node WT-live,
verified by `--collect-only` at WT bytes before the
run - 9/9 collected). Validated 9/9 green in the
workspace copy (`dry-20261009T220215-fc6ef3`, exit 0,
copy fresh; shared-tree unmoved-notice on every run).
No failability witness owed: the agreement gate is
specified-not-landed, and failability belongs to the
landing change. Sharded and Postgres cells are
inapplicable by construction: the halves, the
predicate, and every oracle above are pure in-memory
container classification and sorting reaching no
database, alias, or dialect decision (Worker-2 to
judge).

## Judgment

CONFIRM-blocked. The canonical unordered/ordered
partition has two independently maintained definitions
in inverted halves (the inputs-side unordered test +
the fingerprint-side ordered arm, complementary and
complete over the non-dict four today at both
states); a classification-axis change now requires
two coordinated edits. Counts: C1 WT 2 / HEAD 3, C2
WT 2 / HEAD 3, C3 WT 1 / HEAD 2 + prose, C4 1, C5 0,
C6 WT 2 / HEAD 3; eight rejections with triggers
(R1-R8); zero defects; one pending-execution proof
(9/9 validated oracle re-run for the unblock item).
The consolidation cannot land: every shape edits
truth-migration lines with no ledger row (exact hunks
in F1), and the predicate body must spell the WT
real-class test from untracked `utils/truth.py` - an
`isinstance` spelling diverges refuse-vs-passthrough
on the inputs path. Migration + agreement gate +
home-clauses specified for the landing after that
dirt commits. Net tracked change +0/-0 (artifact
only).

Freshness pins (connected evidence, WT / HEAD):
`utils/input_values.py` `b0a2c66a` / `01c46036`,
`utils/querysets.py` `e6660894` / `4d8a3d39`,
`utils/errors.py` `e9572ea9` / `9cf4e952`,
`rest_framework/resolvers.py` `4d05a330` /
`14ffc9c8`, `rest_framework/sets.py` `d3a16114` /
`2ecaab56`, `filters/sets.py` `9428aba9` /
`b8740187`, `filters/base.py` `77c2e7a6` /
`a43513a7`, `filters/inputs.py` `a269a3fe` /
`d77a113c`, `list_field.py` `b5cfe957` / `c84cefb2`,
`optimizer/extension.py` `49346716` / `e18210e5`,
`extensions/resource_policy.py` `2123cbef` /
`4cd95703`, `types/base.py` `f42bcee3` / `a63b7edf`,
`testing/client.py` `3b122fd5` / `0c166285`,
`optimizer/lateral_fetch.py` `995f1aa2` / `995f1aa2`
(clean), `optimizer/selections.py` `e14e6e30` /
`d8dc9d52`, `types/converters.py` `d8905d0a` /
`38f102ab`, `utils/relations.py` `cc68c6ba` /
`63f46750`, `tests/utils/test_canonical.py`
`8aecc495` / `90907dbd`, `tests/utils/test_inputs.py`
`4260fc02` / `2713d1cb`,
`tests/mutations/test_write_transaction.py`
`1c65ad43` / `ca9da127`.

## Index rows for Worker 0

(Worker-0 alone edits the cycle record; rows named here
for transcription. No `## Owned changes` row: zero
edits.)

- Family `canonical-unordered-partition` | Owner
  `django_strawberry_framework/utils/canonical.py`
  partition predicate (specified-not-landed;
  blocked-on-hunt) | Files `utils/canonical.py`,
  `utils/inputs.py`, `utils/write_transaction.py` |
  Holding item Family `canonical-unordered-partition`
  | open (F1 CONFIRMED count-2 - one definition per
  walk in inverted halves, WT 2 defs / HEAD 3
  spellings - but blocked-on-hunt, migration +
  agreement gate specified, zero edits; R1-R8 with
  triggers; 0 defects; verified, pending execution)
- `declaration-unordered-reject-vs-walk-partition` |
  `django_strawberry_framework/utils/inputs.py::normalize_field_name_sequence`
  (rejection recorded here; validate-vs-sort, accepts
  arbitrary iterables via `tuple()`; WT by-name
  consumer of the moved spelling) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: the gate consuming a canonical-walk
  ordering decision, or a walk consuming its verdict)
- `freeze-finalize-arm-vs-partition` |
  `django_strawberry_framework/rest_framework/resolvers.py::_frozen_hook_view`
  (rejection recorded here; converge with f46 R1 -
  mutability-descent through bound reads vs
  readability) |
  `django_strawberry_framework/rest_framework/resolvers.py`,
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: the freeze walk composing
  `base_container_values` for its reads)
- `seal-exact-taxonomy-vs-partition` |
  `django_strawberry_framework/utils/querysets.py::_is_plain_container`
  (rejection recorded here; converge with f46 R2 -
  exact-type seal membership, subclasses excluded,
  vs subclass-inclusive readability) |
  `django_strawberry_framework/utils/querysets.py`,
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: either side changing its subclass stance)
- `freezer-split-vs-partition` |
  `django_strawberry_framework/optimizer/extension.py::_freeze_variable_value`
  (rejection recorded here; converge with f46 R6 -
  ABC-accepting degrade-to-opaque vs builtin-only
  refuse/leaf) |
  `django_strawberry_framework/optimizer/extension.py`,
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: the freezer narrowing to builtins with a
  refuse/leaf stance)
- `per-domain-pair-gates-vs-partition` |
  `django_strawberry_framework/utils/canonical.py::base_container_values`
  (rejection recorded here; sixteen-domain pair
  idiom, each domain its own question - shared idiom,
  not a shared rule; ten standing domains
  trigger-checked + five fresh sites read at bytes +
  order-RHS converge; eleventh standing domain
  retired) |
  `django_strawberry_framework/extensions/resource_policy.py`,
  `django_strawberry_framework/filters/base.py`,
  `django_strawberry_framework/filters/inputs.py`,
  `django_strawberry_framework/filters/sets.py`,
  `django_strawberry_framework/rest_framework/resolvers.py`,
  `django_strawberry_framework/rest_framework/sets.py`,
  `django_strawberry_framework/testing/client.py`,
  `django_strawberry_framework/optimizer/extension.py`,
  `django_strawberry_framework/optimizer/lateral_fetch.py`,
  `django_strawberry_framework/optimizer/selections.py`,
  `django_strawberry_framework/types/base.py`,
  `django_strawberry_framework/types/converters.py`,
  `django_strawberry_framework/utils/errors.py`,
  `django_strawberry_framework/utils/querysets.py`,
  `django_strawberry_framework/utils/relations.py`,
  `django_strawberry_framework/list_field.py`,
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: a domain adopting the canonical
  readability contract for its gate)
- `traversal-shape-vs-partition` |
  `django_strawberry_framework/utils/input_values.py::iter_active_fields`
  (rejection recorded here; converge with the f46
  R10 direction - traversal-shape validation, no
  ordering decision, reads-only) |
  `django_strawberry_framework/utils/input_values.py`,
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: the traversal gating an ordering
  decision)
- `mutable-snapshot-vs-partition` |
  `django_strawberry_framework/utils/write_transaction.py::_MUTABLE_SNAPSHOT_TYPES`
  (rejection recorded here; converge with f46 R3 -
  snapshot-vs-alias with leaf-rendered `bytearray`,
  no partition distinction) |
  `django_strawberry_framework/utils/write_transaction.py`,
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: the snapshot site composing the canonical
  predicate for its five-subset)
- `canonical-dispatch-arms-vs-partition` |
  `django_strawberry_framework/utils/canonical.py::base_container_values`
  (rejection recorded here; all five arms yield
  identically - no unordered/ordered distinction) |
  `django_strawberry_framework/utils/canonical.py` |
  Family `canonical-unordered-partition` | rejected
  (trigger: an arm gaining order-dependent behavior)

## Independent verification (Worker-2)

### Own trace (recorded before reading `## Findings`)

Rule as I state it: within the two canonical walks - the
set-`Meta.fields` walk
(`django_strawberry_framework/utils/inputs.py::canonicalize_set_meta_fields`
over `_sorted_meta_values`) and the drift-fingerprint walk
(`django_strawberry_framework/utils/write_transaction.py::_field_fingerprint`)
- unordered containers `{set, frozenset}` are emitted in
`canonical_sort_key` order while ordered containers `{list, tuple}` keep
their order (`dict` is key-sorted on both sides and outside this rule).

Definitions (WT, current bytes):

- D1 - `django_strawberry_framework/utils/inputs.py::_UNORDERED_TYPES` +
  `_is_one_of`: the unordered-membership test, one definition (tuple +
  helper, both WT-added). In-walk consumers: the two
  `canonicalize_set_meta_fields` arms (top-level, dict-value). Out-of-walk
  consumer: `normalize_field_name_sequence` (shares the tuple mechanically;
  contract differs - declaration rejection, not canonical ordering).
- D2 -
  `django_strawberry_framework/utils/write_transaction.py::_field_fingerprint`
  ordered arm (`truth.is_instance(item, list) or truth.is_instance(item,
  tuple)`) plus the residual `else` (set/frozenset by elimination over the
  `_FINGERPRINT_CONTAINER_TYPES` gate): one definition of the ordered half,
  inverted relative to D1.

HEAD spellings: H1 `canonicalize_set_meta_fields` top-level
`isinstance(fields, (set, frozenset))`; H2 its dict-value twin; H3
`normalize_field_name_sequence` `isinstance(value, (set, frozenset))`
(out-of-family: reject-vs-sort); H4 `_field_fingerprint` `elif
isinstance(item, (list, tuple))` + set/frozenset `else`; H5 the inline
five-tuple container gate (membership, adjacent rule); H6
`_snapshot_field_value` over `_MUTABLE_SNAPSHOT_TYPES` (snapshot-vs-alias,
adjacent rule); H7 `base_container_values` five-arm read dispatch (yields
identically per arm - no order distinction).

My challenges (before seeing W1's numbering):

- MC1 "reclassify `tuple` as unordered": WT D1 tuple + D2 ordered arm = 2;
  HEAD H1 + H2 + H4 = 3 (H3 excluded - separate reject rule).
- MC2 "drop `frozenset` from unordered": same 2 / 3.
- MC3 "a new unordered kind must sort": WT D1 tuple +
  `_FINGERPRINT_CONTAINER_TYPES` gate = 2 (the `else` catches it only if
  gated in; the ordered arm itself unmoved); HEAD H1 + H2 + H5 gate = 3.
  The gate is container-membership (adjacent rule), noted as coupling, not
  counted as a partition definition.

Owner I choose:
`django_strawberry_framework/utils/canonical.py` - a partition predicate
beside `base_container_values` / `canonical_sort_key`, which both walks
already import (no dependency reversal, no sibling-flavor import).
Principle-4 lifetime: pure derivation, not cached. Matches the
nomination's candidate on responsibility, not inheritance.

Roles: consumers - `read_set_meta_fields` through the FilterSet/OrderSet
metaclasses and expansion (D1 side); `_snapshot_field_value` /
`assert_no_target_drift` through the serializer flavor (D2 side).
Oracles - the PYTHONHASHSEED set-ordering pins and the drift-detection /
fingerprint pins (exact node ids taken from W1's proof entry, re-run by
me below). Projections - the module docstrings stating the shared-read
contract.

My whole-package sweep (literal `frozenset` census plus regex
`is_instance(..., list) or` / `(list, tuple)` / `(tuple, list)` /
exact-type spellings) surfaced these third-site candidates with my
dispositions: (A) `rest_framework/resolvers.py::_frozen_hook_view`
finalize (`_is_one_of(source, (set, frozenset))` - immutability rendering,
no sort; REJECT, other contract); (B)
`optimizer/extension.py::_freeze_variable_value` (`isinstance(value, Set)`
ABC + list-or-tuple split, frozenset freeze without sort; REJECT, cache
identity over ABC membership); (C) `utils/querysets.py` exact-type
predicates (`_is_exact_sequence` / `_is_exact_tuple_or_list` /
`_is_exact_set` / `_is_plain_container` - exactness is load-bearing,
subclass exclusion; REJECT); (D) `utils/querysets.py::_reconstructed_value`
(`value_type is tuple or value_type is frozenset` - immutable-vs-mutable
memo axis, not unordered-vs-ordered; REJECT); (E)
`normalize_field_name_sequence` (shares the WT tuple; REJECT from the
family - reject-vs-sort); (F) `base_container_values` arms (read dispatch,
no order distinction; REJECT); (G) per-domain sequence-shape guards
(`filters/sets.py`, `filters/inputs.py`, `filters/base.py`,
`utils/relations.py`, `resource_policy.py`, `testing/client.py`,
`optimizer/selections.py`, `optimizer/lateral_fetch.py`,
`types/converters.py`, `rest_framework/resolvers.py` error/child paths,
`utils/querysets.py` SQL-shape probes - shape validation, none sorts an
unordered arm; REJECT as an idiom group); (H) membership tuples for other
walks (`_MUTABLE_SNAPSHOT_TYPES`, `_FINGERPRINT_CONTAINER_TYPES`,
`_FROZEN_VIEW_CONTAINERS`, `_PLAIN_CONTAINER_TYPES` - membership, adjacent
rule; REJECT); (I) `types/base.py` set-acceptance prose (declaration
acceptance; REJECT).

My block assessment (before seeing W1's hunks): the block is REAL. Every
touch-zone line is truth-migration concurrent dirt with no ledger row
(`utils/inputs.py` carries only f45's two one-line compositions, of which
exactly the `base_container_values(fields)` dict-branch line sits in the
touch zone and the migration would not move it;
`utils/write_transaction.py` and `utils/canonical.py` carry no ledger row
at all). A new predicate must spell `truth.is_instance` from untracked
`utils/truth.py`; I verified `truth.is_instance` reads the real MRO only
(`django_strawberry_framework/utils/truth.py::is_instance`), so a plain
`isinstance` spelling over-accepts `__class__`-lying values and diverges
refuse-vs-passthrough on the inputs path (misrouted into
`_sorted_meta_values`, which refuses) and branch-vs-branch on the
fingerprint path. Gate-only is not an available unblocked shape (the owner
is not single - a gate would pin two definitions, not enforce one), and a
HEAD-shaped landing would clobber hunt hunks. Zero-edit stands.

Fingerprints I re-derived (all three states agree with dispatch): WT
`0b8d3daa` / HEAD `c199eaa4` (`utils/inputs.py`), WT `50909be8` / HEAD
`2b9f861c` (`utils/write_transaction.py`), WT `23a7c41a` / HEAD `a1209117`
(`utils/canonical.py`); item-scoped diff vs ITEM_BASELINE `247bec86` over
the three paths is empty; no new files under
`django_strawberry_framework/utils/`.

### Reconciliation (read after recording the above)

Every difference between my trace and W1's, explicitly closed:

- Counts: AGREE. My MC1/MC2 (reclassification across the partition, WT 2 /
  HEAD 3) are W1's C1/C2; my halves D1/D2 are W1's halves U/O; my H1/H2/H4
  are W1's three HEAD spellings with H3 excluded as R1, as I did. Owner:
  AGREE (`utils/canonical.py` partition predicate, pure, uncached).
- My MC3 vs W1 C3 (sixth unordered kind): W1 counts WT 1 ("residual
  catches it with no executable move"); I counted the membership gate as a
  second move. Reconciled as SCOPE, not fact: the gate is f46's
  membership rule, and W1's F1 Coupling already records the residual's
  dependence on it ("assumes the gate admits exactly the five"). Within
  this family's rule the count is 1 either way; the C3 prose would be
  sharper with the "within this rule" qualifier, but the coupling note
  carries the fact. No verdict impact, no defect.
- My sweep candidates A-I vs W1 R1-R8: AGREE one-for-one. A=R2, B=R4, C=R3,
  E=R1, F=R8, G=R5 (idiom group; W1's sixteen-domain table covers every
  site in my G list - I checked each file), H=R7 plus f46-owned membership
  tuples. My D (`_reconstructed_value` tuple-or-frozenset) sits inside the
  seal walk R3 converges (exact-type machinery; immutability axis, no
  partition distinction - verified by my body read). My I
  (`types/base.py::_normalize_sequence_spec` set-acceptance prose) draws no
  partition distinction either (ABC-accept, uniform normalize, no sort -
  verified by my body read); the file is pinned and read, and R5 names the
  file via its pair site. Two same-file second sites W1 does not name
  explicitly (that one plus the `filters/sets.py` 4-tuple, which f46
  dispositioned at its line 441): both verified partition-free by my own
  body reads. No missed definition, no record defect - neither is a
  plausible partition candidate.
- Censuses: W1's pair counts reproduce EXACTLY under my independent
  instrument (WT 4 + 20, HEAD 6 + 26, same files). Producer census (2
  importers + owner, both states; f45 reads-only third at WT), zero-`await`
  census (0/0/0 both states), Layer-6 zero-hits (package-wide both states;
  HEAD docs hits are historical records, out of scope), and
  no-`is_unordered*`/`is_ordered*` census all reproduce. The "or-chains 8"
  figure I could not reproduce with a container-scoped instrument (I count
  5 container-pair or-chains at WT); every one I found is classified
  (D2, R4, R5 x3 incl. both converters sites), so this is instrument scope,
  not a coverage gap.
- Block: AGREE, real. I independently attributed every touch-zone hunk to
  the truth migration (no ledger row), confirmed f45's single ledgered line
  in the zone is not a line the migration moves, confirmed `truth.py` is
  untracked concurrent work, and re-proved the P3 divergence myself
  (property-`__class__` liar feign-admits under `isinstance` while its real
  MRO lacks the member; `truth.is_instance` reads the real MRO only).
  Gate-only is correctly unavailable (owner not single); the specified
  gate's reason for staying unlanded (would pin dirt-private names) is
  sound.
- Migration spec: byte-precise against current bytes (spans, line
  numbers, and the residual-stays-residual principle-8 call, which
  correctly refuses to add a refusal arm); the agreement-gate shape
  (exact-match census over the two walk modules + hand-copy negative
  control + `prove` with restore proof) matches the f45 precedent at
  `tests/utils/test_canonical.py`. Behavior-preservation holds trivially
  for the zero-edit outcome; the halves' present agreement is witnessed by
  the executed oracle re-run below.
- Matrix: axis 2 and 4 inapplicabilities hold (pure in-memory
  classification, no await surface either state; one-way tests, and the
  output-separation trigger re-check references a real standing row -
  File `utils/canonical.py` R7, with R4/R5/R6 likewise real). Sharded/pg
  inapplicable-by-construction ENDORSED: the rule, the predicate, and all
  9 oracle bodies are pure in-memory container work reaching no database,
  alias, or dialect decision - I read all 9 bodies (no `django_db` marks,
  no owner reads, literal containers in / literal relations out).
- Shape: no `### Enumeration` is correct for a family item (DRY.md scopes
  that section to file items; whole-package censuses + pins substitute).
  No `## Implementation (Worker-1)` is correct (DRY.md requires it "on
  tracked changes" only; the checker has no such requirement; the brief's
  ask yields to canonical DRY.md). Zero `][` links, so no link-def block
  is owed. The artifact carries no new-file diff and no tracked edits, so
  the AGENTS.md prose rules and the ruff gates apply to the EMPTY path set
  - stated explicitly, no run owed or run (a repo-wide run would grade
  concurrent dirt).
- Referenced-not-rehomed homes exist: f46 C5 not-a-defect note, File
  `utils/inputs.py` D1 limbs, f46 R1/R2/R3/R4/R6/R10/R11 converge targets.
  All 20 connected-evidence freshness pins plus the 3 indexed pins verify
  (23/23, current bytes); searched population 121 WT / 118 HEAD with
  exactly the 3 stated WT-new files; all 6 blocking-record hunk headers
  match current `git diff HEAD` exactly.

### Gate re-runs (Worker-2, own copy `dry/canonpart-f64/verify-1`, slot-3)

- basedpyright all-mode: 0 errors / 0 warnings / 0 notes, exit 0
  (`dry-20261009T221620-3cefc4`, copy fresh, shared unmoved).
- basedpyright floor (`-p pyrightconfig.floor.json`): 0 / 0 / 0, exit 0
  (`dry-20261009T221735-2420dd`).
- truthful-reads `--check`: 120 files, tier-1 0, errors 0, exit 0
  (`dry-20261009T221845-056227`).
- Oracle re-run (the `proof:` entry verbatim, 9 nodes): 9/9 green, exit 0
  (`dry-20261009T221852-0e5074`). All 9 node ids exist exactly once at WT
  bytes.

### Index-row rulings (Worker-2)

- Family `canonical-unordered-partition` row: ENDORSE (owner, files,
  counts, triggers, and the `verified, pending execution` outcome all
  transcribe F1/Judgment faithfully).
- `declaration-unordered-reject-vs-walk-partition`: ENDORSE (R1 contract,
  consumer note, and trigger match).
- `freeze-finalize-arm-vs-partition`: ENDORSE (R2 converge + trigger match).
- `seal-exact-taxonomy-vs-partition`: ENDORSE (R3 converge + trigger match;
  home `_is_plain_container` as stated in R3).
- `freezer-split-vs-partition`: ENDORSE (R4 converge + trigger match).
- `per-domain-pair-gates-vs-partition`: ENDORSE (R5 sixteen-domain table:
  10 trigger-checked + 5 fresh + 1 converge = 16 + owner file = 17 paths
  listed; retired eleventh domain noted; trigger matches).
- `traversal-shape-vs-partition`: ENDORSE (R6 converge + trigger match).
- `mutable-snapshot-vs-partition`: ENDORSE (R7 converge + trigger match).
- `canonical-dispatch-arms-vs-partition`: ENDORSE (R8 no-distinction +
  trigger match).

No `## Owned changes` row is owed (zero edits) - confirmed.

### Verdict

No defects found (Worker-2). Zero-edit BLOCKED outcome stands: F1
CONFIRMED count-2 with migration + agreement gate specified, 8 rejections
with triggers, 0 defects, one `proof:` entry re-run green in my own copy.
Status set `verified`. The item keeps its `proof:` entry, so Worker-0 will
mark the plan row `verified, pending execution`.

