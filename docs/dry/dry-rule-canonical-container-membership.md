# DRY review: `canonical-container-membership`

Status: verified
Run: 0.0.15 2026-10-01-11

Item kind: FAMILY (responsibility family). Owner re-derived fresh, not
inherited: a membership predicate in
`django_strawberry_framework/utils/canonical.py` is the principle-7
owner. The duplication is CONFIRMED (count 3 at HEAD and WT bytes) but
the consolidation is BLOCKED on concurrent dirt: every line it would
edit is truth-migration / maintainer rework with no ledger row. Zero
production edits, zero test edits. Migration, agreement gate, and
rejection home-clauses specified for the landing after that dirt
commits.

Concurrency: all three indexed files carry concurrent dirt (truth
migration + maintainer `except`-narrowing, no ledger row covering any
of it) plus the f45-ledgered compositions in `utils/inputs.py` and
`utils/input_values.py`. Attribution below is by diff content vs
`git show HEAD:<path>`; every concurrent byte preserved, nothing
touched. The f45 reads-axis artifact was orientation only: every
membership count here was re-derived with fresh censuses at current
bytes.

Baselines: `ITEM_BASELINE=7d0b4b84da5318d7485c1368bd6f014c0a4e31a6`
(resolves; item-scope diff on the three indexed files vs WT is empty).
HEAD `dd0b6691` unmoved throughout. Dispatch pins verified at task
start and unchanged: `utils/canonical.py` WT `d754e71c` / HEAD
`7f5bb5f7`, `utils/inputs.py` WT `8839b38d` / HEAD `0b7d353c`,
`utils/write_transaction.py` WT `db1efbca` / HEAD `20900a51`.
Address `dry/canonmem-f46/consolidate` (slot-2; every workspace proof
ran there).

Gates (tree-state, zero-edit item; all in the workspace copy):
basedpyright 0 errors / 0 warnings / 0 notes
(`dry-20261001T191545-0265af`, exit 0); check_any 128 uses at 89 sites
(`dry-20261001T191607-bdd01a`, exit 0, `ALLOWED_ANY` untouched);
truthful-reads tier-1 0 / errors 0 over 119 files
(`dry-20261001T191608-661271`, exit 0). No ruff run (zero edits, zero
paths touched). No pytest for the counts (every verdict below is
static against committed bytes; a test run proves nothing about
definition counts); the one pytest run is the `## Pending
execution` oracle re-run — the migration handoff, not count
evidence — 38/38 green (`dry-20261001T193302-c8c9b8`).

## System trace

The rule: exactly the five built-in containers (`dict`, `set`,
`frozenset`, `list`, `tuple`, subclasses included) count as readable
containers for the canonical walks; anything else is refused, never
iterated on the consumer's terms. Three spellings, set-equal at both
states (member lists verified element by element):

- Spelling A — `utils/inputs.py::_hashable_meta_value` gate. HEAD
  :541-551: `is_container = isinstance(v, (dict, set, frozenset, list,
  tuple))`. WT :536-557: `_META_CONTAINER_TYPES` (same five, same
  order) + `if _is_one_of(v, _META_CONTAINER_TYPES):` (concurrent-new
  lines). Walk-vs-leaf for the Layer-6 cache-key walk; non-members
  fall to `hash(v)`-or-opaque-token.
- Spelling B — `utils/write_transaction.py::_field_fingerprint` gate.
  HEAD :1010-1020: `isinstance(item, (dict, list, tuple, set,
  frozenset))`. WT :839-845 + :1025: `_FINGERPRINT_CONTAINER_TYPES`
  (same five, same order) + `if not _is_one_of(item,
  _FINGERPRINT_CONTAINER_TYPES):` (concurrent-new lines). Walk-vs-leaf
  for the pre-save drift fingerprint; non-members fall to
  `_leaf_token` (bytes/bytearray explicitly "not containers" per the
  :1026-1027 comment).
- Spelling C — the dispatch inside
  `utils/canonical.py::base_container_values`. HEAD :72-80: five
  `isinstance` arms (dict/set/frozenset/list/tuple) + the typed
  refusal :82-87. WT :72-86: same arms as `truth.is_instance`
  (concurrent rewrite), same refusal naming `truth.kind(value)`.
  Read-vs-refuse: the behavior-defining spelling.

The two gates already differ cosmetically in tuple order at both
states; `isinstance` order is irrelevant, so the shared meaning is the
SET. All three spellings agree today: no behavior defect, pure
drift-risk (count 3).

Consumers (invoke or derive, never re-define): the Layer-6 hashable
walk (gate A → per-shape dispatch → owner reads), the drift
fingerprint (gate B → three arms → owner reads),
`utils/inputs.py::_sorted_meta_values` (ungated by design: translates
the refusal — exclusion re-verified fresh),
`utils/inputs.py::make_set_meta_cache_key` arms (dict / (list, tuple) /
unordered / raw dispatch, never re-define),
`utils/inputs.py::canonicalize_set_meta_fields` arms, and
`utils/input_values.py` traversal (dict/dataclass/list shape gates +
two f45-ledgered owner reads; no five-gate — R10). Producer census:
exactly 2 production importers of the owner at HEAD (`utils/inputs.py`,
`utils/write_transaction.py`), 3 at WT (+ f45-ledgered
`utils/input_values.py`); no re-export; no existing
`is_canonical*` predicate anywhere (census zero hits outside unrelated
input-name tests).

Oracles (all independent: literal tuples, literal refusal text, or
lying overrides; none reads the owner):
`tests/utils/test_canonical.py` five-shape acceptance rows + two
`pytest.raises(ConfigurationError, match="Cannot canonically read a
...")` rows spelling literal type names, and the HEAD-only
refusal-translation row `tests/utils/test_inputs.py:530`
(`test_meta_sorting_wraps_a_hostile_generic_iterator` — deleted at
WT with the translator: HEAD `:520-533` wraps the owner call in a
typed re-raise, WT `:522-530` is the bare `return sorted(...)`).
Live WT refusal-boundary coverage is the twelve `test_inputs.py`
nodes in the `## Pending execution` re-run. Projections:
the owner module docstring (the five-clause contract), the consumer
docstrings/comments, per-cycle bug-hunt mentions at HEAD. No GLOSSARY
anchor (symbol census over `docs/`: zero hits outside per-cycle
records and this cycle's own item list — re-derived).

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. The membership question
   spans the construction-time cache-key walk, the request-time drift
   fingerprint, and (reads-only) the set-input traversal. Adjacent
   flavors with same-name container sets were each read at HEAD bytes
   and decided on contract, never missed: the hook-data freeze walk
   (R1), the seal exact-type taxonomy (R2), the snapshot six-set (R3),
   the order-RHS four-set (R4), the filter raw-value classifier (R5),
   the variable freezer (R6), declaration-shape validators (R7),
   per-domain sequence/pair gates (R8), leaf/scalar allow-lists (R9),
   traversal shapes (R10), the permissions conditional (R11). No fourth
   canonical-container walk exists (producer census above).
2. Sync/async twins — NO SUCH SURFACE. The dispatch and both gates are
   pure in-memory tests with no await point, no executor, and no I/O;
   both consumers call them from synchronous walks (both walk bodies
   read in full: zero `await`).
3. Derived rather than repeated knowledge — SEARCHED. The five-set is
   spelled 3x (F1); the unordered/ordered partition within it 2x (S1,
   split to its own row); the real-class test mechanism 3x in WT-only
   dirt (observed-not-homed). Per-shape and per-pair `isinstance`
   dispatches below the gates dispatch, never re-define (exclusion
   re-verified fresh at HEAD and WT). Reads over framework-built
   containers (`safe_meta.get`/`dict.items`, `cache.get`,
   `config.field_specs.get`) read exact-owned objects, not consumer
   containers — examined and excluded on body.
4. Inverse / round-trip pairs — NO SUCH SURFACE (examined). Gates are
   one-way. The nearest pair — hashable structure versus digest string
   — is the intentional output separation the standing file-item R7
   records; trigger re-checked unfired.
5. Contracts restated in another medium — SEARCHED. Every medium a
   change moves is classified in System trace. One projection defect
   already homed by a verified file item (File `utils/inputs.py` D1,
   bare-`repr` prose limbs — referenced, not re-homed). Oracles spell
   literals; none reads the owner.
6. Enforcement by omission — SEARCHED. Both canonical walks gate (2/2);
   the traversal needs no five-gate (R10); every other walk answers a
   different question (R1–R9, R11). No omission gap; nothing routes to
   the maintainer.

Standing triggers checked: file-item R4 (atom base-slot reads — no
spanning primitive at HEAD; WT `truth.text` is uncommitted concurrent
bytes), R5 (hostile-mapping open family, opposite accept-vs-refuse
stance), R6 / policies R3 (no owned rejection-message grammar — none
adopted), and the f45 R-E..R-I reads-axis separations (membership
questions re-derived fresh here, not inherited). All unfired.

### Challenges

Each change posited on the rule's variation axes; authoritative
definitions counted (consumers, oracles, projections listed, never
counted). HEAD and WT agree on every count (concurrent dirt
re-spells, never re-members: all three sets verified element-equal at
both states).

- C1 — drop `frozenset` from the readable set. Gate A + gate B + the
  dispatch arm (+ refusal text) move: count 3. THE duplication
  evidence. Gate-ADMIT partial moves fail loud, not open (a
  gate-admitted frozenset reaches the refusal, which propagates —
  zero swallowing `except` on any owner-call path, verified by
  full-function reads). The gate-NARROW direction is unclaimed: a
  gate-narrowed frozenset falls to `hash(v)` / `_leaf_token`
  silently, coherently for an immutable member — no loudness owed
  there, and no verdict rests on it.
- C2 — sixth built-in joins the readable set. The same 3 + per-walk
  follow-ons (unordered/ordered partition S1, per-shape dispatch arm,
  refusal text): count 3 with coupling F1↔S1.
- C3 — reorder a gate tuple. Count 0 (cosmetic; the gates already
  differ in order at both states).
- C4 — reword the refusal. Count 1 (dispatch only; oracle literals
  listed, not counted). Refusal already single-owned (production
  census: exactly 1 wording site at both states).
- C5 — `bytearray` joins the readable set. Canonical-3 move; the
  snapshot six-set does NOT (already a member for mutability reasons —
  R3 boundary evidence). Sharpens C1: a gate without its arm
  mis-walks (the fingerprint's admitted-but-unarmed value emits no
  parts while holding its active id — coherence, not a defect today).
- C6 — drop `tuple`, freeze-table view. Canonical-3 move; the freeze
  table must KEEP tuple (dropping it fails CLOSED — a tuple value
  falls to `_freeze_leaf`, which raises `ConfigurationError` for a
  non-leaf non-member — breaking tuple-carrying hook data loudly).
  R1 independence evidence: divergent criterion (mutability-descent
  membership vs readability) plus the availability break, not
  opposite aliasing.
- C7 — exclude subclasses from readability. Canonical-3 move; the seal
  tables unmoved (subclasses were never members). R2 independence
  evidence.

No read-only probe was needed: every count above is decided statically
against committed bytes (definition census, importer census, `or`-chain
census, grep-verified absences), so no `temp-tests/` scope was created
and no pytest ran for the counts. Workspace runs: the three
tree-state gates (ids in the header block) plus the `## Pending
execution` 38-node oracle re-run (`dry-20261001T193302-c8c9b8`,
exit 0, 38/38) — the migration-handoff equivalence witness, not
count evidence.

## Findings

### F1 — Canonical container membership (CONFIRMED count-3, BLOCKED on concurrent dirt, zero edits)

Contract: exactly the five built-in containers (`dict`, `set`,
`frozenset`, `list`, `tuple`, subclasses included) count as readable
containers for the canonical walks; anything else is refused, never
iterated on the consumer's terms. Variation axis: the member set.
Follow-on behavior per walk (depth bound, node budget, cycle guards,
leaf rendering, output encoding) differs and stays with each walk.

Sites + roles: three authoritative definitions (A: inputs gate, B:
fingerprint gate, C: canonical dispatch — spans in System trace).
Consumers, oracles, projections as in System trace.

Challenges: C1 3, C2 3 (+ S1 follow-ons), C3 0, C4 1, C5 3, C6/R1 and
C7/R2 independence. Counts identical at HEAD and WT.

Owner + lifetime (principle 7): a membership predicate in
`utils/canonical.py` (name for the landing item; `is_canonical_container`
fits the module's vocabulary). Responsibility: the module already owns
the readability contract both consumers import downward with no
reversal (2 importers at HEAD, 3 at WT); the dispatch — the
behavior-defining spelling — lives there, so the predicate makes
gate/dispatch agreement by construction rather than by parallel
memory. Dependency direction wins cleanly (no consumer imports
sideways). Pure function, "not cached": no principle-4 lifetime owed.

Migration (specified, not landed): (1) one private member table in
`canonical.py` read by BOTH the new predicate and a table-driven
dispatch (dict-first order preserved; the f45
multiple-inheritance-unconstructibility result keeps the dispatch
exact); (2) both gates compose the predicate by name; (3) both
gate tuples deleted; (4) the S1 partition row decides the
unordered/ordered half in its own item; (5) the specified agreement
gate lands in `tests/utils/test_canonical.py` (f39/f45 tier
precedent); (6) the R1–R11 home-clauses below land as one docstring
clause each at the stated homes.

Distinct behavior: each walk keeps its gate follow-on (opaque-token
vs leaf-token vs fail-closed families), its budgets, and its output
encoding; the refusal text and the dict-first arm order stay.

Behavioral proof: static-reviewed. P1: the three sets verified
element-equal at HEAD and at WT — rejects silent divergence (sets
agree today; no behavior defect). P2: all five owner-call paths read
in full with zero swallowing `except` between gate and read (the HEAD
`_sorted_meta_values` translator re-raises typed; WT has none) —
rejects fail-open divergence in the verified gate-ADMIT direction
(a gate-overbroad member reaches the refusal, which propagates as
`ConfigurationError`); the gate-narrow direction is unclaimed (a
narrowed member leaf-renders silently — coherent, not loud — and
no verdict rests on it). P3: the whole-package censuses
(`frozenset` 273 hits at HEAD classified; tuple-`isinstance` census;
`or`-chain census at WT; importer census) — rejects a fourth
spelling. No execution for the counts: counts and control-flow
absence are decided from committed bytes; nothing ordering,
transactional, or async is involved. The executed part is the
`## Pending execution` oracle re-run (migration-handoff
equivalence, 38/38 green), not count evidence.

Structural gate: SPECIFIED, not landed. The landing item adds an
agreement test asserting the predicate/table, the dispatch arms
(AST-read, same technique as the f45 census gate), and both gate
call-sites compose the predicate (no residual five-tuple literal:
exact-match census over the two walk modules). Negative control: a
behavior-preserving hand copy — re-spell one gate as an inline
five-tuple with identical members — fails exactly the gate while all
behavior rows pass (the copy is correct). First run must show the
rule holding (sets agree today). NOT landed now: the gate would pin
`_META_CONTAINER_TYPES` / `_FINGERPRINT_CONTAINER_TYPES`, private
names that exist only in uncommitted dirt (absent at HEAD); a gate
born on dirt breaks on the migration's rename and gets weakened, not
fixed. The landing item runs it via `prove` with restore byte-proof.

Coupling: S1 (partition sub-rule — a sixth member forces a
partition decision per walk); the blocked landing (below). No other
coupling: no gate, dispatch order, refusal text, or follow-on moves
in this item.

Blocking record (exact hunks, all concurrent, no ledger row — touch
nothing):

- `utils/inputs.py @@ -525,30 +527,34 @@` tail + `@@ -538` gate
  rewrite: the `_META_CONTAINER_TYPES` / `_UNORDERED_TYPES` /
  `_is_one_of` insert (WT :535-548) and `if _is_one_of(v,
  _META_CONTAINER_TYPES):` (WT :557) are truth-migration inserts. (The
  f45-ledgered `:577` / `:695` composition lines sit in adjacent hunks
  and are buildable by content — but the consolidation needs the gate
  lines, not those.)
- `utils/write_transaction.py @@ -829,6 +835,19 @@` and
  `@@ -1006,17 +1022,7 @@`: the `_FINGERPRINT_CONTAINER_TYPES` /
  `_is_one_of` insert (WT :839-850) and `if not _is_one_of(item,
  _FINGERPRINT_CONTAINER_TYPES):` (WT :1025) are the same migration.
- `utils/canonical.py @@ -69,33 +69,33 @@`: the dispatch arms are the
  same migration's `truth.is_instance` rewrite. Regardless of whether
  the landing reshapes the dispatch, the predicate body must spell the
  WT real-class test — `truth.is_instance` from untracked concurrent
  `utils/truth.py`. An `isinstance` spelling is fail-open against the
  migrated dispatch: a lying `__class__` can only FEIGN membership
  against exact-builtin-cls `isinstance` (verified by probe: a
  non-member with `__class__ = dict` passes while a real member
  passes regardless of what `__class__` reports — feign, never
  hide), so the feigner passes the gate while the truth-based arms
  miss it; in the fingerprint's armless dispatch (no `else` at
  either state) the admitted-but-unarmed value emits no parts and
  no refusal — walk-to-OMISSION per C5 — silently blinding the
  drift digest (the exact hole the migration closes).
- Deleting either gate tuple deletes concurrent lines. Appending the
  home-clauses to the owner docstring rewrites the concurrent docstring
  hunk (`@@ -1,4 +1,4 @@` + Ordering bullet). Every consolidation
  shape touches concurrent bytes: blocked, zero edits.

Freshness: `utils/canonical.py` WT `d754e71c` / HEAD `7f5bb5f7`;
`utils/inputs.py` WT `8839b38d` / HEAD `0b7d353c`;
`utils/write_transaction.py` WT `db1efbca` / HEAD `20900a51`;
read-only evidence `utils/input_values.py` WT `463f81a8` / HEAD
`929e81b5`, `utils/permissions.py` WT `bb3e0493` / HEAD `0e13b869`,
`utils/querysets.py` WT `6d471bd7` / HEAD `adc74b64`,
`utils/errors.py` WT `a4afaf43` / HEAD `53d74870`,
`rest_framework/resolvers.py` WT `08310034` / HEAD `5e80bbf7`,
`filters/sets.py` WT `14884190` / HEAD `76abccb0`,
`filters/base.py` WT `9edbef64` / HEAD `058fcfb1`,
`list_field.py` WT `b534ea32` / HEAD `3842542a`,
`optimizer/extension.py` WT `8e3fe7c1` / HEAD `b7b6c434`,
`extensions/resource_policy.py` WT `2971618b` / HEAD `289dc159`,
`sets_mixins.py` WT `c496feb2` / HEAD `42e8c862`,
`types/base.py` WT `e7a62d32` / HEAD `e0ad32aa`,
`testing/client.py` WT `ee6f26bc` / HEAD `4d6791fa`,
`optimizer/lateral_fetch.py` WT `17afda7e` / HEAD `17afda7e` (clean),
`optimizer/selections.py` WT `3b1c0bf8` / HEAD `ed22de27`,
`types/converters.py` WT `97f3399e` / HEAD `312bd290`,
`connection.py` WT `6c4b01f9` / HEAD `38491372`,
`tests/utils/test_canonical.py` WT `95e186d6` / HEAD `a1d76cc2`,
`tests/utils/test_inputs.py` WT `220fecd2` / HEAD `ef303037`.
Searched population: 117 package files at HEAD, 120 at WT (3 WT-new:
f39-ledgered `_multipart.py` + untracked `truth.py` / `lazy.py`),
via the `frozenset` word census, the tuple-`isinstance` census, the WT
`or`-chain census, the importer census, and the refusal-wording
census. Excluded on the strength of its body: every R1–R11 site; every
module outside the hit lists on the strength of the empty censuses;
untracked `truth.py` / `lazy.py` as uncommitted bytes (no row homes on
dirt).

### S1 — Canonical unordered/ordered partition (SUB-RULE ROW for Worker-0)

Within the canonical walks, `{set, frozenset}` are the unordered
members (sorted) and `{list, tuple}` the ordered ones (order
preserved); `dict` pairs sort by key. Two spellings of the unordered
half: the inputs side (HEAD: five inline `(set, frozenset)` gates at
:574/:679/:683/:748 plus the declaration reject at :1149; WT: one
`_UNORDERED_TYPES` tuple, five uses) versus the fingerprint arm (HEAD
:1060 `isinstance(item, (set, frozenset))`; WT :1066 `or`-chain). Two
of the ordered half: inputs (HEAD :743; WT :755 inline `(list,
tuple)`) versus the fingerprint arm (HEAD :1055; WT :1061
`or`-chain). Posit `frozenset` turning ordered: both files move
(partition-rule total count 4 at WT / 8 at HEAD — unordered half 2
WT / 6 HEAD plus ordered half 2 WT / 2 HEAD). Separate axis from F1
(partition, not
membership — F1 can fix the five while S1 still double-spells the
roles), coupled via C2 (a sixth member forces a partition decision).
Owner TBD by its family item (candidate: the same canonical module).
All WT lines concurrent-dirtied; counts stand at HEAD bytes.

### R1 — Hook-view freeze-descent five (REJECTED)

`rest_framework/resolvers.py::_FROZEN_VIEW_CONTAINERS` (HEAD :762-776:
the same five names) + `_FrozenContainer` (:217-219) + the
`(set, frozenset)` finalize arm (:839). Contract difference:
mutability-descent membership ("may transitively contain
hook-mutable structure; rendered immutable per-shape through BOUND
reads" — `_entries` uses `iter(enumerate(container))`) versus
readability ("has an un-overridable base iterator; read through base
slots, else refused"). The freeze reads do not consume the
readability contract at all, and non-member stance differs
(fail-closed + leaf allow-list + per-type conversions vs
refuse/leaf-render). Decisive (C6): drop-tuple moves canonical-3
while freeze must KEEP tuple — dropping it fails CLOSED (loud
`_freeze_leaf` rejection of tuple-carrying hook data), so the
independence stands on the divergent criterion (mutability-descent
membership vs readability) plus the availability break, not on
opposite aliasing. Reconsideration trigger: the freeze walk composing
`base_container_values` for its reads. Durable home owed: one clause
at the freeze table (landing with F1's home-clauses).

### R2 — Seal exact-type container taxonomy (REJECTED)

`utils/querysets.py::_PLAIN_CONTAINER_TYPES` (HEAD :1094-1100: the
same five names in a frozenset) + `_is_plain_container` (:1105),
`_is_plain_container_value` (:1116), `_is_exact_dict` /
`_is_exact_tuple` / `_is_exact_sequence` (:1135) /
`_is_exact_tuple_or_list` (:1140) / `_is_exact_set` (:1149).
Contract difference: exact-type seal membership (subclasses
EXCLUDED to the provenance proof — "a `list`/`dict` SUBCLASS can
override `__iter__`/`items`", per the owner docstring — with bound
reads downstream) versus subclass-inclusive readability (subclasses
INCLUDED; base-slot reads make them safe). Same five names,
opposite subclass stance, both stated. Decisive (C7): a
subclass-stance change moves each side independently. Reconsideration
trigger: either side changing its subclass stance (the seal learning
base-slot reads, or canonical excluding subclasses). Durable home
owed: one clause at `_is_plain_container`.

### R3 — Mutable-snapshot six-set (REJECTED)

`utils/write_transaction.py::_MUTABLE_SNAPSHOT_TYPES` (HEAD :822-830:
canonical-five + `bytearray`). Contract difference: mutable-in-place
snapshot-vs-alias decision (`bytearray` MUST fingerprint — mutable —
but is a leaf, never walked: the gate comment says bytes/bytearray
"are not containers") versus walk-vs-leaf readability. The sets
already differ by design. Decisive (C5): `bytearray`-joins-readable
moves canonical-3 while the snapshot table stays put.
Reconsideration trigger: the snapshot site composing the canonical
predicate for its five-subset (blocked today on the same dirt).
Durable home owed: one clause at the snapshot table.

### R4 — Order-RHS four-set (REJECTED)

`list_field.py::_ORDER_VALUE_CONTAINERS` (HEAD :724-729: `list`,
`tuple`, `set`, `frozenset` — NO `dict`) + the :997 walk.
Contract difference: ORM predicate-RHS shapes (`__in` takes a
sequence, `__range` a pair; a `dict` is deliberately absent and
falls through to literal) read with BOUND iteration for
SQL-fragment detection versus consumer-container readability.
Decisive: `dict` membership differs by design. Reconsideration
trigger: `dict` gaining RHS-container meaning AND the walk adopting
base-slot reads. Durable home owed: one clause at the table.

### R5 — Filter raw-value classifier (REJECTED)

`filters/sets.py::_operator_bag_items` four-tuple (HEAD :2651-2660:
`list`, `tuple`, `set`, `frozenset` → `None`) + the `dict`
key-disambiguation arm (:2678-2679: operator bag vs multi-key value
by key vocabulary). Contract difference: filter raw-value shape
classification (the four refused-unwalked, `dict` disambiguated by
KEYS — a question canonical never asks) versus readability. Same
five names across two arms, different rule. Reconsideration
trigger: the classifier consuming the canonical predicate for a
container gate. Durable home owed: one clause at the classifier.

### R6 — Variable-value freezer (REJECTED)

`optimizer/extension.py::_freeze_variable_value` (HEAD :447: ABC
ladder — `Mapping` / `Set` / `(list, tuple)` — with degrade-to-opaque
on hostile `__instancecheck__`, :448-456). Contract difference:
ABC-accepting variable freezing where hostile values DEGRADE to
opaque identity (cache-miss cost) with exact-`type()` scalars
(`_SAFE_CACHE_SCALAR_TYPES`, subclasses excluded) versus
builtin-only refuse/leaf stance on a security check. Decisive:
opposite stance on unknown shapes (accept-degrade vs refuse), opposite
scalar stance (exact vs inclusive). Reconsideration trigger: the
freezer narrowing to builtins with a refuse/leaf stance. Durable home
owed: one clause at the freezer.

### R7 — Declaration-shape validators (REJECTED)

The developer-declared Meta-shape family, fail-loud, ABC-accepting:
`sets_mixins.py::is_re_readable_field_declaration` (`Collection`
minus text atoms — views, `range`, custom Collections admitted),
`types/base.py::_normalize_sequence_spec` (:1011: `(Sequence,
AbstractSet)`), `utils/inputs.py::normalize_field_name_sequence`
(rejects unordered at HEAD :1149, then ACCEPTS arbitrary readable
sequences via `tuple(value)`), the `exclude` four-tuple sort gate
(HEAD :826-833: sorts ALL FOUR shapes — order meaningless for
exclusions — with `dict` meaningless-excluded). Contract
difference: declaration validation (a shape a developer wrote; views
and one-shot-iterable bans are its questions) versus
consumer-controlled security walks — and the sharpest split: the
normalizer ACCEPTS arbitrary iterables, the exact shape canonical
refuses. Reconsideration trigger: a declaration shape arriving
consumer-controlled on a security walk. Durable home owed: one clause
at `is_re_readable_field_declaration` (the family's shared spine).

### R8 — Per-domain sequence/pair gates (REJECTED, shared idiom)

The `(list, tuple)` / `(set, frozenset)` / `(dict, list)` pair idiom
across eleven domains, each answering its own question (census at HEAD):
`utils/errors.py` :199-207 (error-detail iteration, `Iterable`
INCLUSIVE, fail-closed) and :231-239 (Django `message` read, bound
`list(msg)`); `extensions/resource_policy.py` :585 (`(list, tuple,
Mapping)` — `Mapping`-accepting width/node charging);
`filters/base.py` :234/:424/:445/:659/:1224 (lookup-value arity);
`rest_framework/resolvers.py` :579/:623/:1161 (error-shape and
many-decode gates); `optimizer/extension.py` :1504 (stash-union
defensive coerce); `testing/client.py` :338 (multipart placeholder
walk over a framework-built envelope); `optimizer/lateral_fetch.py`
:942, `optimizer/selections.py` :500, `types/converters.py` :727,
`types/base.py` :1240, `connection.py` async-iterable pairs.
Contract difference per domain (acceptance varies: `Mapping` /
`Iterable` / exact pairs; follow-ons vary: materialize, charge,
verify, decode); no single change moves any two together — shared
idiom, not a shared rule. Reconsideration trigger: a domain adopting
the canonical readability contract for its gate. Durable home owed:
one clause at the canonical dispatch (the standing
single-shape-dispatch exclusion, extended to pairs).

### R9 — Leaf/scalar allow-lists (REJECTED, different subject)

`rest_framework/resolvers.py::_IMMUTABLE_LEAF_TYPES` (freeze
by-reference allow-list), `optimizer/extension.py` +
`utils/querysets.py` scalar tables (`_SAFE_CACHE_SCALAR_TYPES`,
`_INERT_VALUE_TYPES`, `_TEMPLATE_PARAM_VALUE_TYPES`,
`_RETAINED_LEAF_TYPES`), and the two `_TEXT_ATOM_TYPES` tables
(`sets_mixins.py`, `utils/errors.py` — the latter pair already
carries the homed bilateral separation). Different subject: leaves,
not containers. Reconsideration trigger: a leaf table constraining
container membership. No home-clause owed (subject disjoint).

### R10 — Traversal-shape membership (REJECTED, converge)

`utils/input_values.py::iter_input_items` (HEAD :108: dict arm, then
the dataclass `__dataclass_fields__` sniff with `getattr` field
reads) + `iter_active_fields` list arm. The traversal rule homed
file-local already; converge with trigger re-checked unfired. Contract
difference: traversal-shape membership (which shapes carry set-input
fields — `dataclass` membership via attribute reads is a question
canonical never asks) versus readability; the dict/list arms consume
the owner READS post-f45 while the shape gate stays traversal-local.
Reconsideration trigger: the traversal gating a five-shaped walk.
Durable home owed: none (standing home stands).

### R11 — Permissions conditional accept (REJECTED, converge)

`utils/permissions.py::_related_declarations` (HEAD :689-691: dicts
read unbound, non-dict mappings read BOUND — conditional ACCEPT).
Converge with the f45 R-F direction on fresh evidence (body re-read
at HEAD). Contract difference: conditional accept of arbitrary
mappings versus refuse. Reconsideration trigger (standing):
related declarations restricted to dicts, or the owner gaining a
mapping arm. Durable home owed: none (f45 home stands).

### Observed, not homed (uncommitted concurrent bytes)

WT-only, no row homes on dirt: the `_is_one_of` real-class test
spelled identically 3x (`utils/inputs.py:546`,
`utils/write_transaction.py:848`,
`rest_framework/resolvers.py:772` — the third found by this item's
census); the WT `or`-chain pair dispatches (same pairs as the HEAD
tuples — no new spelling); untracked `utils/truth.py` /
`utils/lazy.py`. The landing item re-checks whether the committed
migration kept the `_is_one_of` triple (a fourth `utils` home
candidate) or collapsed it.

## Defects

None. The admit-without-arm coherence note in F1/C5 is not a defect:
the three sets agree today at both states, so the hazard
materializes only on a divergence the consolidation exists to
prevent. No guard gap, nothing for the maintainer.

## Pending execution

proof: `uv run python scripts/workspace.py run
dry/canonmem-f46/consolidate -- pytest
tests/utils/test_canonical.py::test_base_container_values_reads_a_plain_dicts_items
tests/utils/test_canonical.py::test_base_container_values_reads_plain_members_for_the_other_four_containers
tests/utils/test_canonical.py::test_base_container_values_reads_a_dict_subclass_through_the_base_items_slot
"tests/utils/test_canonical.py::test_base_container_values_reads_subclasses_through_the_base_iterator[set]"
"tests/utils/test_canonical.py::test_base_container_values_reads_subclasses_through_the_base_iterator[frozenset]"
"tests/utils/test_canonical.py::test_base_container_values_reads_subclasses_through_the_base_iterator[list]"
"tests/utils/test_canonical.py::test_base_container_values_reads_subclasses_through_the_base_iterator[tuple]"
tests/utils/test_canonical.py::test_base_container_values_refuses_a_non_base_iterable
tests/utils/test_canonical.py::test_base_container_values_refuses_a_hostile_iterable_without_running_its_iter
tests/utils/test_canonical.py::test_base_container_values_refusal_is_not_chained_to_a_consumer_error
tests/utils/test_inputs.py::test_make_hashable_meta_value_sorts_mixed_dict_keys
tests/utils/test_inputs.py::test_make_hashable_meta_value_rejects_cyclic_containers
tests/utils/test_inputs.py::test_make_hashable_meta_value_rejects_excessive_container_depth
tests/utils/test_inputs.py::test_make_hashable_meta_value_allows_shared_acyclic_containers
tests/utils/test_inputs.py::test_make_hashable_meta_value_keys_opaque_unhashable_by_identity
tests/utils/test_inputs.py::test_make_hashable_meta_value_depth_boundary_is_exact
tests/utils/test_inputs.py::test_normalize_field_name_sequence_rejects_unordered_sets
tests/utils/test_inputs.py::test_normalize_sequence_unordered_rejection_names_the_set_type
tests/utils/test_inputs.py::test_meta_cache_helpers_bypass_container_overrides
tests/utils/test_inputs.py::test_make_set_meta_cache_key_tags_fields_shape
tests/utils/test_inputs.py::test_read_set_meta_fields_canonicalizes_sets_without_mutating_source
tests/utils/test_inputs.py::test_normalize_meta_drops_falsy_exclude
tests/mutations/test_write_transaction.py::test_target_state_snapshot_and_drift_rejection
tests/mutations/test_write_transaction.py::test_snapshot_target_state_fingerprints_mutable_container_values
tests/mutations/test_write_transaction.py::test_snapshot_target_state_captures_filefield_name_not_the_mutable_descriptor
tests/mutations/test_write_transaction.py::test_assert_no_target_drift_propagates_a_planted_eq_error
tests/mutations/test_write_transaction.py::test_file_name_snapshot_compares_a_non_fieldfile_replacement_raw
tests/mutations/test_write_transaction.py::test_snapshot_fingerprint_is_iterative_and_budgeted
tests/mutations/test_write_transaction.py::test_field_fingerprint_covers_container_kinds_and_is_deterministic
tests/mutations/test_write_transaction.py::test_field_fingerprint_reads_hostile_containers_through_their_base_slots
tests/mutations/test_write_transaction.py::test_field_fingerprint_orders_by_a_guarded_key_not_a_bare_repr
tests/mutations/test_write_transaction.py::test_field_fingerprint_rejects_a_reference_cycle
tests/mutations/test_write_transaction.py::test_field_fingerprint_admits_a_repeated_sibling_that_is_not_a_cycle
tests/mutations/test_write_transaction.py::test_field_fingerprint_reads_atom_leaves_through_base_slots
tests/mutations/test_write_transaction.py::test_field_fingerprint_reads_bytes_through_their_base_buffer
tests/mutations/test_write_transaction.py::test_field_fingerprint_distinguishes_opaque_objects_a_constant_repr_cannot_collapse
tests/mutations/test_write_transaction.py::test_field_fingerprint_walks_dict_keys_as_nodes
tests/mutations/test_write_transaction.py::test_field_fingerprint_leaf_tokens_stay_type_tagged
-n0 --no-cov -q` — discharges F1's migration-handoff equivalence
for the unblock item (10 canonical five-shape + refusal nodes, 12
inputs hashable/unordered/cache-key nodes, 16 fingerprint/snapshot
nodes; every node WT-live, verified by `--collect-only` at WT bytes
before the run — the HEAD-only `:530` translator row is excluded,
see System trace). Validated 38/38 green in the workspace copy
(`dry-20261001T193302-c8c9b8`, exit 0, copy fresh; shared-tree
moved-notice names only the two doc files). No failability witness
owed: the agreement gate is specified-not-landed, and failability
belongs to the landing change. Sharded and Postgres cells are
inapplicable by construction: the dispatch, both gates, and every
oracle above are pure in-memory container tests reaching no
database, alias, or dialect decision (Worker-2 to judge).

## Judgment

CONFIRM-blocked. The membership rule has three independently
maintained definitions (two walk gates + the canonical dispatch,
set-equal today at both states); one member-set change now requires
three coordinated edits. Counts: C1 3, C2 3 (+S1), C3 0, C4 1, C5 3,
C6/R1 and C7/R2 independence; eleven rejections with triggers
(R1–R11), one sub-rule row (S1 unordered/ordered partition, total
count-4 WT / 8 HEAD), zero defects, one pending-execution proof
(38/38 validated oracle re-run for the unblock item). The
consolidation cannot land: every
shape edits truth-migration lines with no ledger row (exact hunks in
F1), and the predicate body must spell the WT real-class test from
untracked `utils/truth.py` — an `isinstance` spelling is fail-open
against the migrated dispatch. Migration + agreement gate +
home-clauses specified for the landing after that dirt commits. Net
tracked change +0/-0 (artifact only).

## Index rows for Worker 0

(Worker-0 alone edits the cycle record; rows named here for
transcription. No `## Owned changes` row: zero edits.)

- Family `canonical-container-membership` | Owner
  `django_strawberry_framework/utils/canonical.py` membership predicate
  (specified-not-landed; blocked-on-hunt) | Files
  `utils/canonical.py`, `utils/inputs.py`,
  `utils/write_transaction.py` | Holding item Family
  `canonical-container-membership` | open (F1 CONFIRMED count-3 but
  blocked-on-hunt, migration + agreement gate specified, zero edits;
  R1–R11 with triggers; S1 split to its own row)
- `canonical-unordered-partition` | Owner TBD by family item
  (candidate: the same canonical module) |
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/write_transaction.py` | Holding
  item Family `canonical-unordered-partition` | open (S1: unordered
  `{set, frozenset}` vs ordered `{list, tuple}` within the canonical
  walks, partition-rule total count-4 at WT / 8 at HEAD (unordered
  half 2/6, ordered half 2/2); all WT lines concurrent-dirtied)
- `freeze-descent-five-vs-canonical-five` |
  `django_strawberry_framework/rest_framework/resolvers.py::_FROZEN_VIEW_CONTAINERS`
  (rejection recorded here; mutability-descent through bound reads vs
  readability; C6 opposite-move) |
  `django_strawberry_framework/rest_framework/resolvers.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: the freeze
  walk composing `base_container_values` for its reads)
- `seal-exact-type-container-taxonomy` |
  `django_strawberry_framework/utils/querysets.py::_is_plain_container`
  (rejection recorded here; exact-type seal membership, subclasses
  excluded, vs subclass-inclusive readability; C7) |
  `django_strawberry_framework/utils/querysets.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: either side
  changing its subclass stance)
- `mutable-snapshot-six-set` |
  `django_strawberry_framework/utils/write_transaction.py::_MUTABLE_SNAPSHOT_TYPES`
  (rejection recorded here; snapshot-vs-alias with leaf-rendered
  `bytearray` vs walk-vs-leaf; C5) |
  `django_strawberry_framework/utils/write_transaction.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: the snapshot
  site composing the canonical predicate for its five-subset)
- `order-rhs-four-set` |
  `django_strawberry_framework/list_field.py::_ORDER_VALUE_CONTAINERS`
  (rejection recorded here; ORM RHS shapes, `dict` deliberately
  absent, bound reads, vs readability) |
  `django_strawberry_framework/list_field.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: `dict`
  gaining RHS-container meaning AND the walk adopting base-slot
  reads)
- `filter-raw-value-classifier` |
  `django_strawberry_framework/filters/sets.py::_operator_bag_items`
  (rejection recorded here; shape classification with `dict`
  key-disambiguation vs readability) |
  `django_strawberry_framework/filters/sets.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: the
  classifier consuming the canonical predicate for a container gate)
- `variable-value-freezer` |
  `django_strawberry_framework/optimizer/extension.py::_freeze_variable_value`
  (rejection recorded here; ABC-accepting degrade-to-opaque vs
  builtin-only refuse/leaf) |
  `django_strawberry_framework/optimizer/extension.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: the freezer
  narrowing to builtins with a refuse/leaf stance)
- `declaration-shape-validators` |
  `django_strawberry_framework/sets_mixins.py::is_re_readable_field_declaration`
  (rejection recorded here; fail-loud ABC-accepting Meta validation,
  arbitrary iterables accepted, vs security walks) |
  `django_strawberry_framework/sets_mixins.py`,
  `django_strawberry_framework/types/base.py`,
  `django_strawberry_framework/utils/inputs.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: a declaration
  shape arriving consumer-controlled on a security walk)
- `per-domain-sequence-pair-gates` |
  `django_strawberry_framework/utils/canonical.py::base_container_values`
  (rejection recorded here; eleven-domain `(list, tuple)` /
  `(set, frozenset)` idiom, each domain its own question — shared
  idiom, not a shared rule) |
  `django_strawberry_framework/utils/errors.py`,
  `django_strawberry_framework/extensions/resource_policy.py`,
  `django_strawberry_framework/filters/base.py`,
  `django_strawberry_framework/rest_framework/resolvers.py`,
  `django_strawberry_framework/optimizer/extension.py`,
  `django_strawberry_framework/testing/client.py`,
  `django_strawberry_framework/optimizer/lateral_fetch.py`,
  `django_strawberry_framework/optimizer/selections.py`,
  `django_strawberry_framework/types/converters.py`,
  `django_strawberry_framework/types/base.py`,
  `django_strawberry_framework/connection.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: a domain
  adopting the canonical readability contract for its gate)
- `leaf-scalar-allow-lists` |
  `django_strawberry_framework/rest_framework/resolvers.py::_IMMUTABLE_LEAF_TYPES`
  (rejection recorded here; different subject — leaves, not
  containers) |
  `django_strawberry_framework/rest_framework/resolvers.py`,
  `django_strawberry_framework/optimizer/extension.py`,
  `django_strawberry_framework/utils/querysets.py`,
  `django_strawberry_framework/sets_mixins.py`,
  `django_strawberry_framework/utils/errors.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: a leaf table
  constraining container membership)
- `traversal-shape-membership` |
  `django_strawberry_framework/utils/input_values.py::iter_input_items`
  (rejection recorded here; converge with the homed traversal rule —
  `dataclass` shapes vs readability) |
  `django_strawberry_framework/utils/input_values.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: the traversal
  gating a five-shaped walk)
- `permissions-conditional-accept` |
  `django_strawberry_framework/utils/permissions.py::_related_declarations`
  (rejection recorded here; converge with f45 R-F — conditional
  accept of non-dict mappings vs refuse) |
  `django_strawberry_framework/utils/permissions.py`,
  `django_strawberry_framework/utils/canonical.py` | Family
  `canonical-container-membership` | rejected (trigger: related
  declarations restricted to dicts, or the owner gaining a mapping
  arm)

## Independent verification (Worker-2)

### Own trace (recorded before reading `## Findings`)

Rule re-derived fresh from the three indexed files at HEAD
`dd0b6691` and WT bytes: which values count as readable
containers for the canonical walks. My AST census (tuple-class
constants, every `isinstance` / `truth.is_instance` call, every
`or`-chain with calls, both states) finds three spellings of the
five-set, each element-equal to `{dict, set, frozenset, list,
tuple}`:

- A — inputs gate: HEAD :541 inline five-tuple
  `isinstance(v, (dict, set, frozenset, list, tuple))`; WT
  :536-542 `_META_CONTAINER_TYPES` (same five, same order) +
  :557 `if _is_one_of(v, _META_CONTAINER_TYPES):`. Definition.
- B — fingerprint gate: HEAD :1009 inline five-tuple
  (dict-first order); WT :839-845
  `_FINGERPRINT_CONTAINER_TYPES` + :1025 `if not
  _is_one_of(item, _FINGERPRINT_CONTAINER_TYPES):`.
  Definition.
- C — canonical dispatch:
  `utils/canonical.py::base_container_values` five-arm ladder +
  typed refusal; `isinstance` arms at HEAD :72-80,
  `truth.is_instance` at WT :72-80. Definition (the
  behavior-defining spelling).

My challenges: add-a-sixth-member (A+B+C move: 3),
drop-a-member (3), reorder-a-tuple (0), reword-the-refusal (1:
C only — refusal census finds exactly one production wording
site at both states), subclass-to-exact-stance (3). No fourth
spelling (importer census: 2 HEAD / 3 WT; `is_canonical*`
zero outside unrelated input-name tests). Owner I would
choose: a membership predicate in `utils/canonical.py` — the
module already owns the read, the refusal, and the sort key,
and both walk modules already import downward into it, so the
predicate makes gate/dispatch agreement by construction with
no dependency reversal. Pure function, no lifetime owed.

Partition sub-rule (own census): unordered-pair spellings —
HEAD six inline `(set, frozenset)` tuples (inputs :574 / :679 /
:683 / :748 / :1149 + write_transaction :1060); WT two
(`_UNORDERED_TYPES` + five by-name uses, write_transaction
:1066 `or`-chain). Ordered-half spellings — HEAD two (inputs
:743, write_transaction :1055); WT two (inputs :755,
write_transaction :1061 `or`-chain).

### Census reproduction (all re-run by me, both states)

- Indexed pins, same-kind (`git hash-object` WT vs `git
  rev-parse` HEAD): canonical `d754e71c` / `7f5bb5f7`, inputs
  `8839b38d` / `0b7d353c`, write_transaction `db1efbca` /
  `20900a51` — all match dispatch.
- Connected pins spot-checked 6/6 byte-exact: input_values
  `463f81a8` / `929e81b5`, permissions `bb3e0493` /
  `0e13b869`, resolvers `08310034` / `5e80bbf7`, types/base
  `e7a62d32` / `e0ad32aa`, test_canonical `95e186d6` /
  `a1d76cc2`, test_inputs `220fecd2` / `ef303037`.
- `frozenset` word census at HEAD: 273 — exact.
- Zero `await` in all three modules at both states.
- Item diff vs `7d0b4b84` = the plan edit alone; artifact
  untracked; zero tracked edits. No independent consolidation
  found: the only consolidation is the blocked F1.

### Reconciliation

Every material claim reconciles except the proof-bar call and
four record-accuracy precisions (all named below as
resubmission feedback):

- (a) Count-3 + set-equality: STANDS at both states by my
  census above. C1 fail-loud direction (gate-overbroad reaches
  the refusal): verified by a full `except` census plus
  full-function reads of all five owner-calling functions
  (`_sorted_meta_values`, `_hashable_meta_value`,
  `canonicalize_set_meta_fields`, `make_set_meta_cache_key`,
  `_field_fingerprint`) — zero swallowing `except` between
  gate and read at either state (HEAD `_sorted_meta_values`
  translator re-raises typed; every other `except` in both
  modules sits on unrelated paths: `hash(v)` leaf,
  sequence-shape validation, triple validation, `_safe_import`,
  pk-compare, conflict probe). Precision note (verdict-neutral):
  "never silent" overreaches for the gate-narrow direction,
  which is silently-coherent for immutable `frozenset`, not
  loud — the fail-OPEN half (the security-relevant half)
  holds.
- (b) Pending-None: REJECTED — the owed `proof:` entry (see
  Verdict). Eight of nine prior blocked CONFIRMs (e8, e9, f36,
  f37, f38, f40, f41, f42) carry a `proof:` entry naming
  existing oracle nodes, validated runnable at baseline, for
  the unblock item's equivalence re-run. The sole Pending-None
  precedent (f33) applies only when the witnessing oracles do
  not exist yet — and even f33 had an execution-verified
  agreement probe. Here the oracles exist, are nameable, and
  are green: my focused run of 44 membership-boundary nodes
  (canonical base-slot/refusal rows, hashable-meta /
  unordered / cache-key rows, fingerprint / snapshot / drift
  rows) passes 44/44 in the shared tree with `--no-cov`.
  W1's "a test run proves nothing about definition counts" is
  a category error — the entry is the migration handoff, not
  the count proof — and W1 cited a HEAD-deleted test
  (`test_inputs.py:530`, gone at WT with the translator) as a
  live oracle, which a validation run would have caught. No
  gate-failability witness is owed now: the gate is
  specified-not-landed, and failability belongs to the
  landing change (f41 precedent).
- (c) Block call: STANDS. Hunks re-derived exact from `git
  diff HEAD`: inputs `@@ -525,30 +527,34` (tail +
  `_META_CONTAINER_TYPES` / `_UNORDERED_TYPES` / `_is_one_of`
  inserts + gate line; "@@ -538" is a loose line pointer
  inside it, not a second hunk), write_transaction `@@
  -829,6 +835,19` + `@@ -1006,17 +1022,7`, canonical
  `@@ -69,33 +69,33`, docstring `@@ -1,4 +1,4` +
  Ordering bullet — all truth-migration / maintainer dirt,
  zero ledger coverage (the sole Owned-changes grep hit is the
  f45 TEST file; f45's production rows are the :577 / :695
  composition one-liners, buildable by content inside mixed
  hunks, not gate lines). Untracked-truth dependence is
  forced: a committed-form real-class read would duplicate the
  hunt's in-flight base-slot reads and violate the
  truthful-reads gate. The isinstance fail-open CONCLUSION is
  true via the fingerprint admit-without-arm omission (no
  else-arm: admitted-but-unarmed emits no parts, no refusal —
  C5's own note), but the stated MECHANISM is backwards and
  must be corrected in resubmission: a lying `__class__`
  cannot HIDE dict-ness from exact-builtin-cls `isinstance`
  (real members pass the type check before `__class__` is
  consulted — it can only feign membership), and the silent
  flip is walk-to-OMISSION, not walk-to-leaf. Zero legal
  partial landings confirmed (predicate-alone = dead code on
  uncommitted bytes; gate-now = born-on-dirt pinning WT-only
  private names absent at HEAD — the refusal is right, and
  f45's gate is distinguished: it pinned committed owner-call
  composition).
- (d) S1 split: ENDORSED — separate axis (partition, not
  membership), F1↔S1 coupling marked via C2, new Family
  `canonical-unordered-partition` row owed, queued after the
  existing families. Correction owed in resubmission: the "2
  WT / 6 HEAD" count covers the unordered half only; the
  ordered half adds 2 WT (inputs :755, write_transaction
  :1061) / 2 HEAD (inputs :743, write_transaction :1055),
  for a partition-rule total of 4 WT / 8 HEAD. Scope the row
  line or count the total.
- (e) Rejections: all eleven carry contract difference +
  trigger + home. R1 STANDS (descent-vs-readability,
  bound-reads verified, `_finalize` arm verified) except the
  C6 word "fail-open": dropping tuple from the freeze table
  fails CLOSED (loud `_freeze_leaf` rejection), breaking
  tuple-carrying hook data — independence stands on
  divergent criterion/availability, and the word must be
  corrected. R2 STANDS (exact-vs-inclusive stance verbatim
  in the owner comment; C7 decisive). R3 STANDS (six-set +
  bytearray-leaf comment; C5 decisive). R4 STANDS
  (dict-absent table + bound `:997` walk). R5 STANDS
  (four-refuse + dict key-disambiguation). R6 STANDS (ABC
  ladder + degrade-to-opaque + exact scalars). R7 STANDS
  (Collection-minus-atoms spine; sharpest split verified in
  the normalizer body; converges with standing
  `sequence-gate-split`). R8 STANDS (sample-verified:
  errors.py Iterable-inclusive fail-closed, resource_policy
  Mapping-accepting charge; idiom, not rule). R9 STANDS
  (leaves, no home owed — correct). R10 STANDS (converge
  with homed FL1/FL6 file-local traversal rules; trigger
  re-checked). R11 STANDS (converge with f45 R-F, trigger
  verbatim, body re-read). Observed triple verified
  (resolvers:772 identical body, third site real).

Matrix: A1 searched (R1–R11 each read); A2 correctly no
surface (zero `await`, both walk bodies read); A3 searched
(F1/S1/`_is_one_of`-dirt + exclusions); A4 correctly no
surface (standing canonical-R7 output separation, trigger
unfired — encodings still differ in the bodies); A5 searched
(oracles literal-independent; D1 correctly referenced to
homed File `utils/inputs.py` D1, verified present); A6
searched (2/2 walks gate; R10 needs none; no maintainer route).

Migration equivalence reasoning holds on principle-8 axes
against the bodies: follow-ons stay per walk
(opaque-token vs `_leaf_token` vs fail-closed families differ;
depth-64 vs node-budget-100k differ; hashable-structure vs
digest-string differ); refusal text single-sited; dict-first
order in A, B, and C. Structural gate design is sound with
the correct negative-control direction (inline five-tuple
respell fails exactly the gate; behavior rows pass).

AGENTS.md prose: `path::Symbol` citations throughout, bare
`:NN` (allowed in `docs/dry/dry-*.md`), no process
provenance beyond precedent-consistent run-id/address
citations, no tests added (no tier owed). Ruff:
vacuous — zero tracked paths touched. Banned words: N/A
(no new test/production files). Type gates re-run by me in
the shared tree: basedpyright 0/0/0, check_any 128 uses at
89 sites, truthful-reads tier-1 0 / errors 0 over 119 files
— all match the run-11 baseline (mypy neither run nor
cited). Sharded/PG inapplicable-by-construction: SOUND —
dispatch, gates, predicate, and oracles are pure in-memory
container tests reaching no database, alias, or dialect
decision.

**Defects.** None. (Worker-2: no new defect. The C5 admit-without-arm
coherence note is not a defect today — sets agree at both
states. The four precision items below are record-accuracy
feedback for the resubmission, not defects.)

**Verdict.** `revision-needed`. The F1 CONFIRM (count-3, set-equal, owner
in `utils/canonical.py`), the BLOCKED-ON-HUNT call, the S1
split, all eleven rejections, the zero-defect call, and the
gate/freshness/cell judgments stand — but the DRY proof bar
for a blocked confirm with existing, nameable, green oracles
requires the equivalence re-run handoff, and the resubmission
must carry four cheap precision corrections. Reproduce: re-run
my census script logic (tuple constants + all
`isinstance`/`truth.is_instance` calls + `or`-chains, HEAD vs
WT) and the 44-node focused oracle run; both are described
above.

Concrete resubmission feedback for Worker-1 (same W2 on
return):

1. Add the owed entry under `## Pending execution`: one
   `proof: uv run python scripts/workspace.py run
   dry/canonmem-f46/consolidate -- pytest <explicit node IDs>
   -n0 --no-cov -q` re-running the membership-boundary
   oracles across all three sites (canonical base-slot +
   refusal rows in `tests/utils/test_canonical.py`;
   `test_make_hashable_meta_value_*`,
   `test_normalize_field_name_sequence_rejects_unordered_sets`,
   `test_normalize_sequence_unordered_rejection_names_the_set_type`,
   `test_meta_cache_helpers_bypass_container_overrides`,
   `test_make_set_meta_cache_key_tags_fields_shape`,
   `test_read_set_meta_fields_canonicalizes_sets_without_mutating_source`,
   `test_normalize_meta_drops_falsy_exclude` in
   `tests/utils/test_inputs.py`; `test_field_fingerprint_*`
   + `test_target_state_snapshot_and_drift_rejection` +
   `test_snapshot_target_state_*` +
   `test_assert_no_target_drift_*` + `test_file_name_snapshot_*`
   + `test_snapshot_fingerprint_*` in
   `tests/mutations/test_write_transaction.py`), validated
   runnable N/N at baseline with the run id recorded
   (f41/f42 style). Baseline reference: my shared-tree
   focused run of 44 such nodes passed 44/44.
2. Correct the Blocking-record fail-open mechanism sentence:
   feigned (not hidden) container-ness passes an `isinstance`
   gate while truth-based arms miss; the fingerprint
   dispatch then emits no parts and no refusal
   (walk-to-OMISSION per C5), blinding the drift digest
   silently. Conclusion and block unchanged.
3. Correct the C6/R1 word "fail-open": dropping tuple from
   the freeze table fails CLOSED (loud `_freeze_leaf`
   rejection); the independence stands on the divergent
   criterion (descent membership vs readability) and the
   availability break, not on aliasing.
4. Scope the S1 and Index-row count line to the unordered
   half ("unordered half 2 WT / 6 HEAD; ordered half 2 WT /
   2 HEAD") or count the partition-rule total (4 WT / 8
   HEAD), citing inputs :755/:743 and write_transaction
   :1061/:1055 for the ordered half.
5. Qualify the `tests/utils/test_inputs.py:530` oracle
   citation as HEAD-only (row deleted at WT with the
   translator); the Pending entry in (1) must name
   WT-existing nodes only.

## Iterations

### Pass 2 (Worker-1, artifact-only revision; `Status:
ready-for-verification/2`)

Revision driver + four record corrections, each re-derived against
tree bytes (not inherited from the W2 trace). HEAD `dd0b6691`
unmoved; all six pins re-verified byte-exact before editing
(canonical `d754e71c` / `7f5bb5f7`, inputs `8839b38d` /
`0b7d353c`, write_transaction `db1efbca` / `20900a51`,
test_canonical `95e186d6` / `a1d76cc2`, test_inputs `220fecd2` /
`ef303037`). Zero production/test edits; every verdict,
fingerprint, and gate intact.

1. `proof:` entry added under `## Pending execution`: 38 explicit
   WT-live node IDs (10 canonical five-shape + refusal, 12
   inputs, 16 fingerprint/snapshot), validated 38/38 green in
   the workspace copy (`dry-20261001T193302-c8c9b8`, exit 0,
   copy fresh). Node liveness pre-verified by `--collect-only`
   at WT bytes; the `:530` translator row confirmed HEAD-only
   (`grep` hits at HEAD, zero at WT) and excluded. The
   canonical-file sort-key rows and the f39 enumeration-census
   gate were deliberately excluded as different rules. No
   failability witness: gate specified-not-landed. Header,
   Challenges tail, F1 proof paragraph, and Judgment updated to
   name the run as the migration handoff (counts stay static).
2. Blocking-record mechanism corrected (F1): feigned, never
   hidden, membership — verified by an `isinstance` probe
   (non-member with `__class__ = dict` passes; real member
   passes regardless) plus a read of `truth.is_instance`
   (real-class via `type(obj)` MRO, `:168-170`) and of the
   fingerprint ladder at both states (no `else` arm — admitted
   but unarmed emits no parts, no refusal). Silent flip is
   walk-to-OMISSION per C5. Conclusion and block unchanged.
3. C6/R1 word corrected to fails CLOSED: verified by reading
   `_frozen_hook_view` at both states (non-member falls to
   `_freeze_leaf`, which raises `ConfigurationError` for a
   tuple) — independence restated on divergent
   criterion/availability. R1 verdict unchanged.
4. S1 scope: chose the RECOUNT (partition-rule total 4 WT / 8
   HEAD, with the per-half breakdown inline) over scoping the
   row to the unordered half — the ordered-half sites were
   already listed in the row, so the total is the exact claim.
   All eight HEAD spellings and all four WT spellings
   re-grepped at bytes (unordered HEAD `:574/:679/:683/:748/`
   `:1149` + `:1060`; ordered HEAD `:743` + `:1055`; WT
   `_UNORDERED_TYPES` + `:1066`, `:755` + `:1061`). Split
   rationale intact; Index row recounts likewise.
5. "Never silent" scoped to the verified gate-admit direction
   (C1, F1 P2): gate-narrow silence verified by reading both
   leaf fallthroughs (hashable `hash(v)` succeeds for
   `frozenset`; fingerprint `_leaf_token` never raises) —
   coherent, not loud, and unclaimed. Fail-open-half verdict
   unchanged.
6. `:530` citation qualified as HEAD-only in System trace with
   the translator-deletion spans (HEAD `:520-533` vs WT
   `:522-530`, both read in full).

Neutrality check: every correction re-derived verdict-neutral —
no finding, rejection, count, owner, or gate moved. Observed
while re-reading (not homed, not a defect): the WT
`_sorted_meta_values` docstring still claims "the
metadata-flavored rejection wording" though the rewrite removed
the `except` — uncommitted concurrent prose inside the hunt's
in-flight hunk, so no row and no `## Defects` entry.

### Pass 2 (Worker-2, `Status: verified`)

Pass-1 trace adopted after spot-check (pins, censuses, and
reconciliation re-verified below); judged only the pass-2
delta. HEAD `dd0b6691` unmoved; item diff vs
`7d0b4b84da5318d7485c1368bd6f014c0a4e31a6` on the three
indexed files still empty; pins same-kind byte-exact
(canonical `d754e71c` / `7f5bb5f7`, inputs `8839b38d` /
`0b7d353c`, write_transaction `db1efbca` / `20900a51`,
test_canonical `95e186d6` / `a1d76cc2`, test_inputs
`220fecd2` / `ef303037`).

1. `proof:` entry VALIDATED 38/38 as listed: 38 node IDs
   extracted from the artifact block (10 canonical + 12
   inputs + 16 fingerprint/snapshot, no dups, all three
   oracle files covered) collect 38/38 at WT bytes in the
   shared tree and pass 38/38 green in a fresh workspace
   copy at my address (`dry-20261001T193853-18e106`, exit
   0, slot-3 fresh, shared unmoved since sync). `:530`
   exclusion right: the translator row hits once at HEAD
   (`def` at test-file :530, typed re-raise spans read)
   and zero at WT. No failability witness owed: gate
   specified-not-landed, f41 precedent stands.
2. Mechanism rewrite CONFIRMED: my own probe (feigner passes
   `isinstance`, real member passes regardless of lying
   `__class__`; `truth.is_instance` sees through both)
   plus reads of `truth.is_instance` (real-class via
   `type(obj)` MRO) and the fingerprint ladder (no `else`
   at either state) - feign-never-hide + walk-to-OMISSION
   per C5.
3. C6/R1 fails-CLOSED CONFIRMED: `_frozen_hook_view` falls
   to `_freeze_leaf`, which raises `ConfigurationError`
   for a tuple - divergent criterion/availability, verdict
   unchanged. Stale-sweep: `fail-open` now only in the
   approved gate-admit/isinstance-conclusion uses plus the
   historical pass-1 section.
4. S1 recount CONFIRMED: unordered HEAD six (inputs
   `:574/:679/:683/:748/:1149` + write_transaction
   `:1060`), ordered HEAD two (`:743` + `:1055`), WT two
   spellings per half (`_UNORDERED_TYPES` + five uses +
   `:1066`; `:755` + `:1061`) - partition total 4 WT / 8
   HEAD with per-half breakdown in row and Index. No stale
   total remains in W1 text.
5. "Never silent" scoping CONFIRMED: gate-admit direction
   only in C1/F1 P2; gate-narrow silence verified coherent
   (`hash(v)` succeeds for `frozenset`; `_leaf_token`
   never raises). No unscoped claim remains in W1 text.
6. `:530` qualification CONFIRMED: HEAD-only in System
   trace, translator spans verified (HEAD production
   `:520-533` exact, def through `) from exc`; WT
   `:522-530` bare `return sorted(...)` exact). Nit (not
   blocking, no new pass): the span follows a test-file
   citation but names production-file lines -
   content-correct under the only coherent reading.

Neutrality holds: F1 CONFIRM count-3, canonical.py predicate
owner, R1-R11, S1 split with the new Family row owed, block,
gates, zero defects - none moved. Pass-1 W2 section present
in full, content-cross-checked against the tracked plan
record. The stale-docstring observation in W1's pass record
verified accurate (WT docstring claims the wording, body is
the bare return) and correctly unhomed concurrent prose.
Ruff: vacuous (artifact-only `.md`, zero tracked paths).
Comma script: artifact excluded from the layout rules
(`--check` verified). One `proof:` entry remains: plan item
reads `verified, pending execution`.

