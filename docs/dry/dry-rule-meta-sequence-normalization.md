# DRY review: `meta-sequence-normalization`

Status: verified
Run: 0.0.15 2026-10-11-17
Item: Family `meta-sequence-normalization` (run 17, never-compared normalizers)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `c42960efae3f276596b9c81cfd410a1742c6472f` (resolves as commit)
HEAD: `c37a08a085113d628a554ee199f4d741d7c86cdf`
Slot: `dry/meta-sequence-normalization/consolidate` (no source-mutating run needed; zero edits)

## System trace

Seeds re-derived fresh at current bytes, then execution-compared
over a 16-input matrix (probe, What shrinks). (A)
`types/base.py::_normalize_sequence_spec` (+ `_normalize_fields_spec`,
`__all__`-aware): accepts None / Sequence / AbstractSet incl. sets
and dict views; rejects bare str, generators, dicts, non-string
entries; no duplicate check; entries returned as-is (str subclasses
preserved). Four keys share the one body with the rejecting key
named. (B) `utils/inputs.py::normalize_field_name_sequence`:
accepts None / any `tuple()`-readable iterable (lists, tuples,
generators, dicts-as-keys, views) EXCEPT sets/frozensets; rejects
bare str, non-string entries, duplicates; flattens entries to exact
str. Downstream coherence: A's readers discard order by construction
(`_select_fields` walks `_meta.get_fields()`; three keys hit
`frozenset` immediately); B's readers depend on it (narrowing keeps
caller order into SDL; `serializer_input_type_name` concatenates
per-field tokens in walk order). Sweep finds: the set-side third
contract (re-readability gate + canonicalization + per-family entry
gates, F2); B's by-name consumers (F3); two mapping validators that
are not sequence gates (F3). Excluded by body: cursor/relation-shape
ladders (other subjects, standing splits), `pascalize_token` (name
encoder, not a gate).

## Verification

### Matrix

1. Cross-flavor: every flavor swept; the set-side third contract is
   the find (F2). No fourth field-collection gate exists.
2. Sync/async twins: inapplicable; all gates pure sync predicates.
3. Derived knowledge: no fact reconstructed twice; selection,
   narrowing, expansion each compute their own set from their own gate.
4. Inverse/round-trip pairs: none; every gate is one-way.
5. Contracts in another medium: both rationales stated at owners;
   oracles + specs listed under F1, not counted.
6. Enforcement by omission: B flattens str subclasses, A preserves;
   no contract source extends flattening to A; realistic inputs
   agree (Defects). B's dict/generator acceptance is pinned
   intentional. Discharged.

### Challenges

| Change posited | Definitions forced | Count |
|---|---|---|
| Accept sets in B | B + order-dependent readers only | 1 |
| Accept generators in A | A only (B takes them by pinned rule) | 1 |
| Reject duplicates in A | A only (no downstream dup reader) | 1 |
| Add `__all__` to B | B + write narrowing only (rejected today, pinned) | 1 |
| Flatten entries in A | A only; unobservable at every reader | 1 |
| Accept bare strings anywhere | 3 bodies, but one-line guards; change implausible | 3, below bar |

## Findings

### F1 — A vs B: different contracts, not drifted copies (REJECTED)

Five divergence axes, each owner-stated or pinned, each coherent
with its downstream: sets (A welcomes, B refuses: order-discarding
vs order-preserving pipelines); duplicates (A passes through into
set ops, B fails loud before `frozenset` collapse); `__all__`
(A-fields grammar; B rejects bare strings incl. `__all__`, pinned);
str-subclass entries (A preserves as-is, B flattens through the
`str` slot — HEAD-committed both sides, unobservable either way
through set-membership readers); container shape (A: Sequence-or-
AbstractSet real class; B: any `tuple()`-readable iterable minus
sets, generator acceptance pinned). Convergences (None, empties,
bare-string/non-string verdicts, keys-view acceptance) are
single-guard coincidences with per-subject wordings. A helper
serving both needs container + duplicate + grammar + entry-type
parameters: barred mode flags. Proofs: probe matrix + 10 oracles,
all execution-verified (What shrinks). Trigger: one side adopting
the other's stance on any axis, or a shared downstream reader
unifying order semantics.

### F2 — Set-side third contract (different-contract, REJECTED)

`require_re_readable_field_declaration` (Collection-based: admits
dicts/views/ranges, refuses one-shot iterators for re-expansion)
+ `canonicalize_set_meta_fields` (unordered shapes sorted stable)
+ per-family entry gates (`orders/sets.py:610` exact-str entries;
filters lookup-bag + per-field `__all__`). Third stance on every
F1 axis incl. entry type (refuse vs preserve vs flatten).
CONVERGES `sequence-gate-split`; its trigger (one side adopting
the other's stance) unfired, now with entry-type evidence added.

### F3 — Consumers stay; mapping validators excluded (classified)

Consumer: `resolve_effective_fields` spine, form/serializer
wrappers, the mutations pair helper, optional/injected-fields
reads — all call B by name, none re-spells the ladder.
Different-contract: `_form_field_basis` and
`_validate_schema_field_map` validate hook-returned MAPPINGS
(identifier/plain-string/bound-name gates), never a declared
sequence. Trigger: a consumer re-spelling the ladder reopens F1.

### F4 — Prior rows: four converges, zero reopens

`types-base-spec-normalization` + `sequence-shape-gate` stand
file-local, now cross-checked (no second definition of either
rule). `types-base-sequence-ladders-split` stands (A-fields/A-seq
still differ on sets/`__all__`/views). `sequence-gate-split`
stands, strengthened (F2). All triggers unfired.

## Defects

None. A-preserves vs B-flattens has no contract row on either
side (both docstrings silent, no oracle pins entry types; the
description-flatten oracle is another subject) and no realistic
input misbehaves, so it is benign unpinned divergence, not a
defect. B's dict acceptance rides the docstring-stated
coerce-to-tuple design with generator acceptance pinned; no
row broken.

## Judgment

Disproved: two field-collection gates, five contrary axes, each
coherent with an order-discarding vs order-preserving downstream,
plus a set-side third contract. No shared rule; no edit owed.

## What shrinks

- The rule: none shared. The family decomposes into F1 (five-axis
  contract split, order-discarding vs order-preserving), F2
  (set-side third contract), F3 (consumers + mapping exclusions),
  F4 (four prior-row converges).
- The change: zero edits. Attribute-before-edit never triggered
  (no path touched); both seed files stay exactly as found.
- The owner: none (no consolidation, no new abstraction).
- Net lines: +0/-0 over ITEM_BASELINE.
- Machinery attestation: no new helper, driver, registry, mode flag,
  test, or prose relocation; nothing added that obscures ownership.
- Proofs, all execution-verified: (1) read-only probe
  `docs/dry/temp-tests/meta-sequence-normalization/probe.py`
  (ignored scratch, kept for re-run) — 16 inputs x A-seq/A-fields/B
  + set-side gate + canonicalize; decisive rows: sets accepted by
  A-seq / rejected by A-fields and B, `__all__` accepted only by
  A-fields, duplicates passed by A / rejected by B, Sub preserved
  by A / flattened by B, generators+dicts rejected by A / accepted
  by B, dict views accepted by A-seq and B. (2) One focused run,
  10 oracles green: `tests/utils/test_inputs.py:459`
  set-rejection, `tests/types/test_base.py:2485+2494` frozenset
  acceptance (3 nodes), `tests/mutations/test_sets.py:182`
  dup-rejection, `tests/rest_framework/test_inputs.py:610`
  `__all__`-rejection, `tests/mutations/test_inputs.py:633`
  any-iterable acceptance (4 nodes). No new tests, so no
  failability entries are owed.
- Freshness fingerprints (WT bytes via `git hash-object`):
  base.py `7e65b2bd`, inputs.py `3d99df6c`, sets_mixins.py
  `616dbf20`, orders/sets.py `79c369b3`, forms/inputs.py `df1df485`,
  rest_framework/sets.py `d3a16114`, test_inputs.py `4260fc02`,
  test_base.py `bc858987`, mutations/test_sets.py `c95a185d`,
  mutations/test_inputs.py `e19514e0`, rf/test_inputs.py `a0177083`.
  Searched population: package-wide caller censuses for both
  normalizers + the re-readability gate + the narrowing spine,
  `__all__` census over the three write flavors, entry-type and
  `fields_spec`/`exclude_spec` reader censuses, str-subclass oracle
  census (no A/B pin). Contract sources: both owner docstrings,
  the six oracles above, spec-038/039 (B integration + flatten
  lineage), spec-028 (order `__all__`), spec-029 (A override
  staging).

## Independent verification (Worker-2)

Own trace, from fresh reads at WT bytes. Sites: (A)
`types/base.py::_normalize_sequence_spec` (+ `_normalize_fields_spec`,
`__all__` grammar, Sequence-only) — declaration gates whose readers
discard order (`_select_fields` walks `_meta.get_fields()` into set
ops; 3 of 4 A-seq keys hit `frozenset` at once); (B)
`utils/inputs.py::normalize_field_name_sequence` — write-side gate
whose readers keep caller order (narrowing spine, descriptor naming);
set-side `sets_mixins.py::require_re_readable_field_declaration` (+
predicate) + `utils/inputs.py::canonicalize_set_meta_fields` + orders
exact-str gate (`orders/sets.py:610`) + filters lookup-bag/per-field
`__all__`; B's by-name consumers (pair helper, spine, both wrappers,
nested configs, optional/injected reads). My wider sweep adds two
parameter-side contracts: `mutations/inputs.py::_frozenset_of_attr_names`
(attr sets to frozenset, no entry check, one-shots consumed once) and
`permissions.py::_validate_fields` (cascade-walk parameter + edge
membership). Roles: each normalizer defines its own contract; B's
callers are consumers; the 10 oracles are byte-pinned and read from no
owner; docstrings are projections. Challenges (mine): sets-in-B,
generators-in-A, duplicates-in-A, `__all__`-in-B, flatten-in-A each
force exactly 1 definition; bare-strings hits N one-line guards but the
change is implausible, below bar; the parameter-side pair counts 1 on
every axis. Owner I would choose: none — no shared rule, and each gate
already sits with its subject. Str-subclass (preserve/flatten/refuse)
and bare-string guards would need mode or message knobs to share =
barred machinery; both stand separate.

Reconciliation: F1/F2/F3/F4 stand on my evidence. "Mutations pair
helper" is `mutations/sets.py::normalize_meta_field_selection` (calls
B twice), not the attr-name freezer — no contradiction. Two
verdict-neutral record points: matrix axis 1 "no fourth gate" holds
inside the Meta-declaration scope (the parameter-side pair stands
separate; trigger: either adopts Meta-subject entry validation/output
shape); the "3 bodies" bare-string count is loose (more guards exist)
but the below-bar conclusion only strengthens. Freshness: all 11
fingerprints re-hashed identical. Execution: probe re-run green at
`dry-20261011T133906-8858a5` (staging `dry-20261011T133857-452613`;
copy fresh, shared unmoved) — every decisive row matches; 10/10 oracles
green in one focused `--no-cov -n0` run. Every rejection carries
difference + trigger; matrix discharged on the real surface (axis-2
inapplicability sound: pure sync gates); `## Pending execution`
correctly absent; no process provenance in findings; `path:NN` allowed
here; ruff has no .py to check (tracked diff empty, this edit .md
only). Defects: none (Worker-2) — the unpinned flatten divergence is
benign (no contract row, unobservable at readers); the probe's
`__all__` entry-types display is scratch-cosmetic, verdict correct.
