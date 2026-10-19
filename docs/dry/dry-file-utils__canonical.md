# DRY review: `utils/canonical.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits.

## System trace

Target `django_strawberry_framework/utils/canonical.py` owns the two
hostile-safe reads every consumer-container walk must share: base-slot
container iteration with a typed refusal
(`utils/canonical.py::base_container_values`), and the total ordering key
(`utils/canonical.py::canonical_sort_key`). Both exist because the reads sit
on security checks (a Layer-6 cache key and a pre-save drift digest), where
a subclass-lying iteration or a constant `__repr__` is fail-OPEN.

Target identity and attribution. HEAD blob
`b9ded33b3733aa4599a65a62c86f22881b49e893` (90 lines); worktree blob
`ce7f40f4e6fbc530e3761e411441570265c6348` (90 lines). `git diff HEAD`
shows 4 hunks, 21+/21-, all attributed by content to concurrent-external
work, none to this item (which made zero edits):

- Hunk 1 (module docstring): drops `Hostile-safe` from the title and the
  raising-`__repr__` clause from the Ordering bullet.
- Hunk 2 (imports): `..exceptions._safe_arg_repr/_safe_type_name` replaced
  by `from . import truth`.
- Hunk 3 (`base_container_values` body): five `isinstance` arms become
  `truth.is_instance`, refusal names `truth.kind(value)`.
- Hunk 4 (`canonical_sort_key` docstring + body): guarded-repr contract
  becomes `truth.render`, whose exceptions propagate.

Every hunk is the shared-tree `truth.*` migration (untracked
`django_strawberry_framework/utils/truth.py` and `lazy.py` on disk, the
whole `utils/` tree dirty the same way). `ITEM_BASELINE` blob for this
path equals the worktree blob (`ce7f40f4`), proving zero worktree change
since the item baseline: the dirt predates this item. No `## Owned
changes` ledger row names this file. This trace reads HEAD bytes only;
worktree bytes are fingerprinted, never reasoned from.

Consumers, classified (HEAD bytes; all line numbers HEAD-blob lines).
Exactly two production importers, both `from .canonical import
base_container_values, canonical_sort_key`; no re-export
(`utils/__init__.py` HEAD `1a4c2ec8` carries no `canonical` name; module
import-spelling census confirms no other importer):

- `utils/inputs.py` (HEAD `ee31d360`): the generated-input metadata
  cache-key walk. `_sorted_meta_values` (:472; :481 sorts by the key,
  translating refusal into metadata wording), `_hashable_meta_value`
  (:491; dict arm :517-525 sorts pairs by the key, set arm :526-531 and
  list/tuple arm :532-534 compose `base_container_values`), and the
  `make_set_meta_cache_key` fields arms (:695 list/tuple read, :698-704
  set ordering). Gated arrival: the five-type `is_container` gate at
  :493-502, the per-shape `isinstance` dispatches at :690-698, and the
  set/frozenset gates before `_sorted_meta_values` at :628, :631, :777.
- `utils/write_transaction.py` (HEAD `eca9ad4d`): the pre-save drift
  fingerprint `_field_fingerprint` (:907). Gate at :951-959, read at
  :977, dict-key ordering at :982-984, set ordering at :999.

Composed-by-name inputs (not rules of this file):
`exceptions.py::ConfigurationError`, `exceptions.py::_safe_arg_repr`,
`exceptions.py::_safe_type_name` (HEAD `e06b0b7f`; owned by verified File
`exceptions.py`).

Oracles: `tests/utils/test_canonical.py` (HEAD
`a1d76cc27aca2297b48c73093aed60e9014b4e65`; 11 test functions spelling
literal tuples, the literal `<unprintable _RaisingRepr>` placeholder, and
override-installed identity assertions — independent of the owner) and
the refusal-translation row
`tests/utils/test_inputs.py::test_meta_sorting_wraps_a_hostile_generic_iterator`
(HEAD `598f1440`). Worktree oracle `cffa66a2` (truth dirt, -49 lines)
NOT traced. Projections: the target module docstring; the consumer
docstrings/comments (`inputs.py::_sorted_meta_values`,
`inputs.py::make_hashable_meta_value` with the D1 caveat,
`write_transaction.py::_field_fingerprint` + :970-976 comment block);
`docs/bug_hunt/bug_hunt-0_0_15.md` mentions (HEAD `9771e3a5`,
per-cycle record). No GLOSSARY anchor (HEAD grep for the module and both
symbols: zero hits).

## Verification

### Enumeration

Instrument: every name in `ast.Module.body` of the HEAD bytes
(`b9ded33b`, 90 lines), read via `git show HEAD:` plus an AST dump.
Count: 7 nodes. Every member lands below; nothing is unassigned.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (shared-read contract + intentional output separation) | Projection at the owner; supports FA/FB/R7 (prose, not a definition) |
| 1 | `from __future__ import annotations` | Mechanics; no rule |
| 2 | `from typing import Any` | Mechanics; no rule |
| 3 | `from ..exceptions import ...` (`ConfigurationError`, `_safe_arg_repr`, `_safe_type_name`) | Consumer link to `exceptions.py`-owned rules; no rule here |
| 4 | `__all__` (`base_container_values`, `canonical_sort_key`) | File-local L2 (leaf manifest) |
| 5 | `base_container_values` | FA (`base-slot-container-reads`); five-arm dispatch also FB (`canonical-container-membership`) |
| 6 | `canonical_sort_key` | File-local L1 (total ordering key; no second definition) |

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. The two walks are the
   mirror: construction-time cache key (hashable-structure output) and
   request-time drift digest (flat-string output). They share the reads
   (composed by name) and deliberately differ in output (R7); the
   producer census (`make_hashable_meta_value` /
   `make_set_meta_cache_key` / `_field_fingerprint`) finds no third
   consumer-container fingerprint walk.
2. Sync/async twins — NO SUCH SURFACE. Both primitives are pure
   in-memory functions with no await point, no executor, and no I/O;
   both consumers call them from synchronous walks. No twin to drift.
3. Derived rather than repeated knowledge — SEARCHED. The container
   membership is spelled three times (two gates + the dispatch → FB);
   the base-slot read is spelled five times (→ FA). Per-shape
   `isinstance` dispatches derive from the same membership but dispatch,
   not re-define, it. `dict.get`/`dict.items` on framework-built
   `safe_meta` (`inputs.py:688-689`, :710) read a framework-owned
   container, not a consumer one — examined and excluded.
4. Inverse / round-trip pairs — NO SUCH SURFACE (examined). Both reads
   are one-way. The nearest pair — hashable structure versus digest
   string — is intentionally asymmetric (R7), two rules, not two halves
   of one grammar.
5. Contracts restated in another medium — SEARCHED. Every medium a
   change moves is classified in System trace. Oracles spell literal
   expectations; none reads the owner. One projection defect found (D1:
   three `inputs.py` docstrings claim bare-`repr` sorting where the
   bodies use the key).
6. Enforcement by omission — SEARCHED. Sort-key rule: every
   fingerprint/cache-key unordered ordering uses the key (five consumer
   arms enumerated in System trace); the bare-`repr` sorts elsewhere
   are diagnostic listings or repr-injective framework signatures (R3),
   never fingerprints. Read rule: both walks compose the primitive
   except the inline restatements (→ FA, duplication, not omission).
   `iter_input_items`' dataclass arm reads fields via `getattr`, not
   containers — not a member. No omission gap; nothing routes to the maintainer.

Standing triggers checked: `_request_body` J1 (shared `except` guard —
target has no `try`/`except`; inapplicable) and J2 (shared exact-type
gate — target uses subclass-INCLUSIVE `isinstance` by contract, since
subclasses are inside the readable domain; inapplicable by design, the
deliberate contrast recorded here). No prior DRY artifact names either
symbol (worktree `docs/dry` census: zero hits), so no other trigger
applies.

### Challenges

Each rule, changes posited on its variation axes, authoritative
definitions counted (consumers, oracles, projections listed, never
counted):

- Base-slot read, snapshot versus live: posit snapshot semantics —
  definitions DISAGREE today (1 snapshots via `tuple()`, 4 stream live
  views/iterators). The family item's sharpest question (FA).
- Base-slot read, sixth readable type: posit accepting one more
  builtin — the dispatch gains an arm and both FB gates plus both
  walks' follow-ons move with it (coupling FA↔FB, recorded in both).
- Base-slot read, refusal stance: posit tolerating arbitrary
  iterables — 1 definition (the refusal arm); refused by the
  silent-lying-`__iter__` reason the docstring states, pinned by the
  `iter_calls == 0` oracle row.
- Membership: posit dropping `frozenset` from the readable set — 3
  spellings move (two gates + dispatch; count 3 = family evidence).
  Posit reordering a gate tuple — 0 definitions (order is cosmetic;
  the two gates already differ in order).
- Sort key, identity tail: posit dropping `(id(type), id(value))` — 1
  definition; refused by the constant-`__repr__` collapse the
  `test_canonical_sort_key_keeps_identical_reprs_distinct` row pins.
- Sort key, head grammar: posit rendering via `str` instead of the
  guarded `repr` — 1 definition; R1/R2/R3 twins unaffected (rejections
  hold).
- Output encodings: posit one shared encoding for both walks —
  refused (R7); 2 owners stay.

No read-only probe was needed: every claim above is decided statically
against HEAD bytes (definition counts, import census, producer census,
grep-verified absences), so no `docs/dry/temp-tests/` scope was created
and no pytest ran. No workspace runs at all (all inspection read-only in
the shared tree: `git rev-parse`/`git show`/`git grep HEAD`,
`git hash-object`, worktree greps; nothing source-mutating).

## Findings

### FA — Base-slot container reads (NEW family `base-slot-container-reads`, open)

Contract: a consumer container's members are read through the type's
UNBOUND iteration slot (`dict.items`, `set`/`frozenset`/`list`/`tuple`
`__iter__`), never through the instance's overridable attribute, so a
subclass cannot decide what a security walk sees. Variation axes: eager
(snapshot) versus lazy (stream); dict (pairs) versus the other four
(members).

Sites and roles: definition candidate
`utils/canonical.py::base_container_values` (:61-75: five arms plus the
refusal); restatements `utils/inputs.py::_hashable_meta_value` dict arm
(:523 `dict.items(v)`), `utils/inputs.py::canonicalize_set_meta_fields`
dict branch (:632 `dict.items(fields)`),
`utils/input_values.py::iter_input_items` dict arm (:91
`dict.items(input_value)`), `utils/input_values.py::iter_active_fields`
list arm (:355 `list.__iter__`). Consumers: the two walks in System
trace. Oracles: the base-slot identity rows in `test_canonical.py`
(lying-subclass pins) plus the bug-hunt verified walk rows (cited, not
re-derived).

Challenges: snapshot-vs-live counts disagreeing definitions (the
item's question, not its answer); sixth-type couples to FB; refusal
counts 1. Owner by responsibility: `base_container_values` — the
narrowest module both `utils` consumers already import downward with
no reversal; migration is composition by name at the four inline
sites, unless the family item finds the streaming shape load-bearing
(`iter_active_fields` yields lazily; the other three inlines build
eagerly and would be identical composed). This file item names the
family and makes no edit.

Freshness: target HEAD `b9ded33b` (worktree `ce7f40f4` truth dirt, NOT
traced); `utils/inputs.py` `ee31d360`, `utils/write_transaction.py`
`eca9ad4d`, `utils/input_values.py` `f2566609` (all HEAD blobs;
worktrees dirty, NOT traced). Excluded on the strength of its body:
`make_set_meta_cache_key`'s `dict.get`/`dict.items` on `safe_meta`
(framework-owned container, no hostile reader).

### FB — Canonical container membership (NEW family `canonical-container-membership`, open)

Contract: exactly the five built-in containers (`dict`, `set`,
`frozenset`, `list`, `tuple`, subclasses included) count as readable
containers; anything else is refused, never iterated on the consumer's
terms. Variation axis: the member set. Follow-on behavior per walk
(depth bound, node budget, cycle guards) differs and stays with each
walk.

Sites and roles: three spellings —
`utils/inputs.py::_hashable_meta_value` gate (:493-502, order
dict/set/frozenset/list/tuple),
`utils/write_transaction.py::_field_fingerprint` gate (:951-959, order
dict/list/tuple/set/frozenset), and the five-arm dispatch inside
`utils/canonical.py::base_container_values` (:61-70). The two gates
already differ cosmetically in tuple order; `isinstance` order is
irrelevant, so the shared meaning is the SET. Oracles: the refusal
rows (`_PlainIterable` / `_HostileIterable` pins) plus the secondary
translation row in `tests/utils/test_inputs.py` (HEAD `598f1440`).

Challenges: drop-a-member counts 3; add-a-member counts 3 plus the
refusal arm; reorder counts 0. Owner: TBD by the family item
(candidates: `canonical.py` via a membership predicate every gate
calls, making gate/dispatch agreement by construction; or the status
quo with a structural gate proving the three spellings agree). The
family item also owns the coupling question with FA (a sixth type
moves both). This file item names the family and makes no edit.

Freshness: target HEAD `b9ded33b` (worktree `ce7f40f4` NOT traced);
`utils/inputs.py` `ee31d360`, `utils/write_transaction.py` `eca9ad4d`
(HEAD blobs). Excluded: `_sorted_meta_values` (ungated by design —
translates the refusal; not a gate spelling) and single-shape
`isinstance` dispatches (dispatch, not membership).

### L1 — Total ordering key for consumer values (file-local)

`utils/canonical.py::canonical_sort_key` returns `(guarded repr,
id(type), id(value))`: content-first, total even under repr collision.
One definition, two consumer walks, zero twins — the package-wide
`(repr, id, id)` census is this site plus the rejected lookalikes R1
(marker-headed token), R2 (leaf-tail suffix), and R3 (bare-`repr`
sorts on non-fingerprint domains). Challenges: drop-the-tail and
change-the-head each count 1 with pinned refusals (see `###
Challenges`). Reconsideration trigger: a second total-order key for
consumer values, or a fingerprint/cache-key ordered by a bare `repr`.

Freshness: target HEAD `b9ded33b`.

### L2 — Module mechanics (file-local)

`__all__` admits exactly the two public primitives; the three imports
are future/typing mechanics plus the `exceptions.py` consumer link.
Producer census: exactly two production importers (full-path, no
re-export) plus one direct test module. No rule, no second site.

Freshness: target HEAD `b9ded33b`; `utils/__init__.py` HEAD
`1a4c2ec8` (absence verified by grep).

### R1 — Opaque meta-value token versus the sort key (rejected)

`utils/inputs.py::_opaque_meta_value` (:469:
`("__unhashable_meta_value__", id(type), id(value))`) shares the
identity-pair tail and nothing else: a fixed-marker token whose
contract is NON-ALIASING (no real string meta value may equal it),
versus a content-headed key whose contract is TOTAL ORDER. Contract
difference: unforgeable marker versus content rendering; the heads
can never unify. Reconsideration trigger: either site changes what
its head guarantees.

### R2 — Leaf-token identity tail versus the sort key (rejected)

`utils/write_transaction.py::_leaf_token` (:875; opaque arm :904) ends
its fingerprint fragment with the same identity pair, headed by a
`type:repr` grammar for digest uniqueness — an ordering of nothing.
Contract difference: fingerprint-suffix uniqueness versus sort
totality. Reconsideration trigger: leaves need ordering, or keys need
fingerprint grammar.

### R3 — Bare-`repr` sorts versus the sort key (rejected)

Three sites sort by a bare `repr`, each on a domain where it is already
total or already harmless: `types/base.py:650` and
`rest_framework/resolvers.py:666` order offender keys for an ERROR
MESSAGE (diagnostic listing, never a fingerprint — a constant
`__repr__` misorders prose, not a check); `optimizer/lateral_fetch.py`
:712/:764 order framework-built normalized signature tuples whose
`repr` is injective over that domain (strings, bools, connectors —
no consumer dunder runs). Contract difference: diagnostic/framework
ordering versus consumer-value fingerprint ordering. Types and
resolvers heads read at `dda91365` / `0d302782`; lateral at `db1ea315`
(clean). Reconsideration trigger: a fingerprint or cache key sorted by
a bare `repr` (that is L1's trigger too).

### R4 — Atom base-slot reads versus container iteration reads (rejected)

`utils/write_transaction.py::_leaf_token` reads atoms through base
slots (`int.__repr__`, `str.__repr__`, the `memoryview` buffer). Same
threat model (hostile dunders), different rule: per-atom-type CONTENT
RENDERING (which atoms are content-honest, which opaque, bytes
type-insensitive) versus member ENUMERATION. A shared primitive would
own the threat model but no single contract. Reconsideration trigger:
a base-slot-read primitive spanning atoms and containers with one
contract.

### R5 — Hostile-mapping materialization versus base-slot reads (rejected)

The open `hostile-mapping-hardening` family
(`utils/policies.py::resolve_policy` mapping arm at HEAD `8c881c0a`:
`plain = dict(overrides)` materialize-once at :164 plus key-guard and
unknown-vocabulary) normalizes ARBITRARY deployment mappings; this
module reads KNOWN builtins through slots and REFUSES the rest. One
accepts-and-validates, the other reads-or-refuses — opposite stances
on unknown shapes. Reconsideration trigger: the family item narrows
the mapping rule to a shared hostile-iteration primitive (it may still
sweep this module; this rejection records the contract difference, not
a boundary).

### R6 — Refusal wording versus a shared rejection grammar (rejected)

The refusal message (`Cannot canonically read a {T} value: only the
built-in ...`) names its own subject and vocabulary, as does every
other per-module rejection. CONVERGE with verified File
`utils/policies.py` R3 on fresh evidence: the package has no owned
rejection-message grammar, and none is owed. Reconsideration trigger:
the package adopts one.

### R7 — Output-encoding unification (rejected)

The two walks' OUTPUT encodings (hashable structure versus flat digest
string) are intentionally separate, stated at the owner (module
docstring :3-8): variation axes are disjoint (cache-key hashability
versus digest compactness and request scope), and unifying them would
couple a construction-time cache to a request-scoped check.
Reconsideration trigger: a third consumer needing both encodings from
one walk.

## Defects

D1 — `utils/inputs.py` prose claims bare-`repr` sorting where the
bodies use `canonical_sort_key` (doc-only; owner: File
`utils/inputs.py`, open; NOT fixed — file item makes no edits):

- (a) `make_hashable_meta_value` docstring (:550-556): "Both unordered
  branches sort by ``repr`` ... so they stay total-ordered." The bodies
  sort by `canonical_sort_key`, and bare `repr` is precisely what
  CANNOT promise totality — the identity tail exists for that. A reader
  acting on this prose would reintroduce the fail-open.
- (b) `make_set_meta_cache_key` docstring (:681): "Dict-shaped
  ``fields`` keys sort via ``key=repr``." The body recurses into
  `make_hashable_meta_value`, which sorts (key, value) PAIRS by the
  canonical key — wrong noun twice over.
- (c) `canonicalize_set_meta_fields` docstring (:622) and (d)
  `normalize_set_meta_for_factory` docstring (:736): "``repr``-sorted
  lists" shorthand for `_sorted_meta_values` (canonical key). Align
  with (a)/(b).
- Contrast (correct prose, same threat model):
  `write_transaction.py::_field_fingerprint` docstring + :970-976
  comment ("ordered by the guarded key, never a bare ``repr``").

Freshness: `utils/inputs.py` HEAD `ee31d360` (worktree `b5af8255` NOT
traced; re-verify prose at verification time).

## Pending execution

None. All conclusions are static against HEAD bytes; no probe, no
pytest, no scratch scope, no workspace runs. Sharded and Postgres cells
are inapplicable by construction: the target is pure in-memory
computation reaching no database, alias, or dialect decision, and both
consumers call it over in-memory containers only.

## Judgment

Zero-edit file item: the target single-owns the hostile-safe read
contract its module docstring states, composed by name at both walks
for ordering and at most read sites for iteration, with two new
families named for Worker 0 (`Index rows` below), two file-local rows,
seven rejections, and one doc-only defect routed to the open File
`utils/inputs.py` item. The genuine possible-duplication candidates
(the four inline base-slot restatements and the triple-spelled
membership set) go to their family items undecided. No pending
execution, no production edit, no test edit. All four worktree hunks
are concurrent-external truth-migration dirt predating the item
baseline; HEAD (`0c0537e2`) did not move during this item.

## Index rows for Worker 0

(Worker 0 alone edits the plan; rows named here for transcription.)

- Family `base-slot-container-reads` | Owner candidate
  `utils/canonical.py::base_container_values` | Files
  `utils/canonical.py`, `utils/inputs.py`, `utils/input_values.py` |
  Holding item Family `base-slot-container-reads` | open
- Family `canonical-container-membership` | Owner TBD by family item
  (candidates: `utils/canonical.py` membership predicate, or status
  quo plus agreement gate) | Files `utils/canonical.py`,
  `utils/inputs.py`, `utils/write_transaction.py` | Holding item
  Family `canonical-container-membership` | open
- Total ordering key for consumer values |
  `utils/canonical.py::canonical_sort_key` | `utils/canonical.py` |
  File `utils/canonical.py` | file-local (single definition; trigger:
  second total-order key or bare-`repr` fingerprint ordering)
- Module leaf manifest and import mechanics | `utils/canonical.py`
  (`__all__`, imports) | `utils/canonical.py` | File
  `utils/canonical.py` | file-local
- Opaque meta-value token versus the sort key |
  `utils/canonical.py::canonical_sort_key` (rejection recorded here) |
  `utils/canonical.py`, `utils/inputs.py` | File `utils/canonical.py`
  | rejected
- Leaf-token identity tail versus the sort key |
  `utils/canonical.py::canonical_sort_key` (rejection recorded here) |
  `utils/canonical.py`, `utils/write_transaction.py` | File
  `utils/canonical.py` | rejected
- Bare-`repr` sorts versus the sort key |
  `utils/canonical.py::canonical_sort_key` (rejection recorded here) |
  `utils/canonical.py`, `types/base.py`,
  `rest_framework/resolvers.py`, `optimizer/lateral_fetch.py` | File
  `utils/canonical.py` | rejected
- Atom base-slot reads versus container iteration reads |
  `utils/canonical.py::base_container_values` (rejection recorded
  here) | `utils/canonical.py`, `utils/write_transaction.py` | File
  `utils/canonical.py` | rejected
- Hostile-mapping materialization versus base-slot reads |
  `utils/canonical.py::base_container_values` (rejection recorded
  here) | `utils/canonical.py`, `utils/policies.py` | File
  `utils/canonical.py` | rejected
- Refusal wording versus a shared rejection grammar |
  `utils/canonical.py::base_container_values` (rejection recorded
  here; CONVERGE with verified File `utils/policies.py` R3) |
  `utils/canonical.py` | File `utils/canonical.py` | rejected
- Output-encoding unification |
  `utils/canonical.py` module docstring (rejection recorded here) |
  `utils/canonical.py`, `utils/inputs.py`, `utils/write_transaction.py`
  | File `utils/canonical.py` | rejected

## Independent verification (Worker-2)

Method note: the dispatch brief front-loaded W1's claims, so a
pre-reading expectation record was impossible; independence was kept by
re-deriving every claim from HEAD bytes with fresh instruments (own AST
dump, own `git grep HEAD` censuses, own `sed` line reads) rather than
by sampling W1's citations. Every line number below was re-pinned by
Worker-2; agreements are agreements of independently read bytes.

Own trace (HEAD `0c0537e2`, target blob `b9ded33b`, 90 lines). The
target defines two primitives: `base_container_values` (five
subclass-inclusive `isinstance` arms reading through unbound base
slots, plus a typed `ConfigurationError` refusal naming
`_safe_type_name`) and `canonical_sort_key` (`(_safe_arg_repr(value),
id(type(value)), id(value))`). Import census: exactly two production
importers (`utils/inputs.py:44`, `utils/write_transaction.py:81`,
both `from .canonical import base_container_values,
canonical_sort_key`); no re-export (`utils/__init__.py` HEAD
`1a4c2ec8` has zero `canonical` hits); test importers are
`tests/utils/test_canonical.py` and `tests/utils/test_inputs.py` only.
`canonical_sort_key` use census outside the owner: exactly five
`key=` arms (`inputs.py:481` via `_sorted_meta_values`, `:525` dict
pairs, `:531` set values, `:703` set fields, `write_transaction.py:983`
dict keys, `:999` set members — five orderings plus the shared
helper); `base_container_values` call census: `:481`, `:529`, `:533`,
`:695`, `:702`, `write_transaction.py:977`, plus the four inline
restatements W1 assigns to FA (`inputs.py:523` `dict.items(v)`, `:632`
`dict.items(fields)`, `input_values.py:91` `dict.items(input_value)`,
`:355` `list.__iter__(input_value)`, the last inside a generator —
`yield from` confirmed). The owner I would choose for each family is
the one W1 names. No third consumer-container fingerprint walk exists.

Judgment 1 — enumeration 7/7 COMPLETE. Own AST dump of HEAD bytes:
docstring, `__future__` import, `typing` import, `..exceptions`
import (`ConfigurationError`, `_safe_arg_repr`, `_safe_type_name`),
`__all__`, two `FunctionDef`s. Every member is homed (projection,
mechanics x2, consumer link, L2, FA+FB, L1). Nothing unassigned.

Judgment 2 — hunk attribution STANDS. `git diff HEAD` shows exactly 4
hunks, 21+/21-, each re-read for content: docstring title +
Ordering-bullet rewrite, `..exceptions._safe_*` replaced by `from .
import truth`, five `isinstance` arms become `truth.is_instance` with
`truth.kind` in the refusal, `canonical_sort_key` docstring + body
become `truth.render`. All four are the shared-tree truth migration
(`truth.py`/`lazy.py` present on disk, absent at HEAD; the whole
`utils/` tree dirty the same way). `git show
ITEM_BASELINE:django_strawberry_framework/utils/canonical.py` hashes
to `ce7f40f4` = worktree: the dirt predates the baseline, and the
item-scoped diff vs `ITEM_BASELINE` names only plan/review-plan docs
(Worker-0/concurrent), no package path. Zero-edit item confirmed.

Judgment 3 — NEW families: FA ENDORSED, FB ENDORSED. FA: the four
inline base-slot reads were each re-read at HEAD bytes; all four
bypass the owner on the same threat model, and the snapshot-vs-live
question (owner snapshots via `tuple()`; `iter_active_fields`
streams) is a genuine family-item question, correctly left open with
the eager/lazy variation axis stated. FB: both gates re-read
(`inputs.py:493-502` order dict/set/frozenset/list/tuple,
`write_transaction.py:951-959` order dict/list/tuple/set/frozenset)
plus the five-arm dispatch; drop-a-member counts 3 spellings, reorder
counts 0 (orders already differ cosmetically) — family evidence
holds. Owner reasoning (narrowest downward-importable module for FA;
predicate-vs-gate options honestly open for FB) and the FA↔FB sixth-type
coupling are correctly recorded in both findings. Freshness blobs
`ee31d360`, `eca9ad4d`, `f2566609` all re-pinned.

Judgment 4 — all 7 rejections PROBED INDEPENDENTLY, all stand. R1:
`_opaque_meta_value` `:469` re-read — fixed-marker non-aliasing token
vs content-headed total order; heads cannot unify. R2: `_leaf_token`
`:875`, opaque arm `:904` re-read — fingerprint-suffix uniqueness,
orders nothing. R3: all four sites re-read at re-pinned blobs
(`types/base.py:650` @`dda91365`, `rest_framework/resolvers.py:666`
@`0d302782`, `lateral_fetch.py:712`/:764 @`db1ea315`, file clean in
worktree) — diagnostic offender listings and framework-built
signature tuples, never fingerprints. R4: atom base-slot reads
re-read (`int.__repr__`, `str.__repr__`, `memoryview` buffer) —
content rendering vs member enumeration. R5: `plain =
dict(overrides)` re-pinned at `policies.py:164` exactly —
accept-and-validate vs read-or-refuse, opposite stances. R6:
CONVERGE verified — verified File `utils/policies.py` R3
(per-subject rejection grammars, trigger "the package adopts one
owned rejection-message grammar") read fresh from
`docs/dry/dry-file-utils__policies.md:362-370`; this refusal names
its own subject and vocabulary, no package grammar exists. R7: output
separation stated at the owner (module docstring `:3-8`), disjoint
variation axes (cache-key hashability vs request-scoped digest
compactness); unification would couple a construction-time cache to a
request-scoped check. Every rejection carries its contract difference
and trigger.

Judgment 5 — D1 VERIFIED limb by limb at HEAD bytes; routing
ENDORSED. (a) `make_hashable_meta_value` docstring "Both unordered
branches sort by ``repr`` ... so they stay total-ordered" (`:551-555`
sentence; bodies at `:525`/`:531` use `canonical_sort_key`, and bare
`repr` cannot promise totality — the prose inverts the guarantee).
(b) `make_set_meta_cache_key` docstring "Dict-shaped ``fields`` keys
sort via ``key=repr``" (dict arm recurses into
`make_hashable_meta_value`, which sorts (key, value) PAIRS by the
canonical key — wrong key and wrong noun). (c) `canonicalize_set_meta_fields`
docstring `:622` "``repr``-sorted lists" (body calls
`_sorted_meta_values`, canonical key). (d)
`normalize_set_meta_for_factory` docstring "``repr``-sorted lists"
(both call paths land on `_sorted_meta_values`). Contrast prose in
`write_transaction.py:970-976` ("ordered by the guarded key, never a
bare ``repr``") re-read and correct. Doc-only, owner File
`utils/inputs.py` is OPEN, file item correctly made no edit; freshness
`ee31d360`/`b5af8255` re-pinned. Routing stands.

Judgment 6 — index rows COMPLETE and TRANSCRIBABLE. Mechanical count:
11 dash-led rows. Contents: FA, FB, L1, L2, R1–R7 — every finding
exactly once, each carrying family, owner (or candidates), files,
holding item, status. Dash-list form confirmed.

Matrix and oracles: all six axes judged on their reasons — axis 2/4
inapplicability (pure in-memory one-way reads) accepted; axes 1/3/5/6
searches corroborated by own censuses. Oracle fingerprints re-pinned:
`test_canonical.py` HEAD `a1d76cc2` (11 test functions counted,
`iter_calls == 0`, identical-reprs, `<unprintable _RaisingRepr>` rows
present), worktree `cffa66a2` (`-49` lines confirmed);
`test_inputs.py` HEAD `598f1440` with the translation row at `:530`.
Bug-hunt record HEAD `9771e3a5` with `canonical` mentions; GLOSSARY
zero hits; no second `docs/dry` mention census re-run needed (claim
is about worktree state at W1 time, immaterial to every finding).

Observations (standing, verdict unaffected — not defects, no
revision): O1 — `optimizer/extension.py:415` (`value_type_id =
id(type(value))`) is a fourth `id(type(` site; correctly outside
L1's `(repr, id, id)` census (no repr head, no ordering use —
plan-cache token, R1-shaped not L1-shaped; L1's trigger is
unthreatened). O2 — Matrix axis 6 calls `:777` a "set/frozenset
gate"; the gate is the four-shape `(list, tuple, set, frozenset)`
`exclude` gate. Substance (gated arrival before
`_sorted_meta_values`) is correct; one-word label imprecision in a
per-cycle artifact.

Checks: ruff has no touched `.py` path to run against (zero-edit
item; item-scoped diff touches no package path) — correctly no run.
No `## Pending execution` entries; sharded/PG inapplicability by
construction accepted (pure in-memory reads, no database/alias/dialect
surface). HEAD unmoved at `0c0537e2` (re-verified after all reads).

Verdict: VERIFIED. Zero-edit file item; 7/7 enumeration, 4/4 hunks
externally attributed, FA+FB endorsed, 7/7 rejections stand, D1
verified and correctly routed, 11/11 index rows transcribable.
