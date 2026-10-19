# DRY review: `relay-id-slot-reads`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

One rule ("Strawberry scan + `"pk"`
fallback") in three lifecycle stages,
plus two neighboring contracts. Stages:
`types/relay.py:244` creation pin,
`:276` public read (slot hit + cold
scan), `:194` gate preflight
(pass-to-raise). Read-time:
`relay.py:146` `(attr, field)` mapping +
`:177` field consumer. Detection:
`definition.py:364` one bool body +
`:340` wrapper + walker `:1699` fork.
Consumers: `types/relay.py`
`:352/:1057/:1130/:455`, walker `:869`.
Slot: 1 writer + 1 production reader;
`_id_attr` 0 framework readers;
finalizer 0 code readers; optimizer 0
slot readers — slot-reader hypotheses
REFUTED. Fences (cited, untouched): H1
owns the four `"pk"` twins, I the gate
detection, G the color twins.

## Verification

### Matrix

1. Cross-flavor: Relay-only (raw-pk
non-mirror at `write_values.py:134`).
2. Sync/async: sync pure reads reused by
async paths (G owns the twins). 3.
Derived-twice: F1 seeded-vs-unseeded
stages; F2/F3 different outputs. 4.
Round-trip: encode/decode/projection
share the public read. 5. Other media:
oracles + specs in What shrinks; zero
sentences falsified. 6. Omission:
fallback covers unstamped classes;
non-Relay contracted `False`. No gap
with a contract source.

### Challenges

C1 (renamed slot): 1 token — count 1.
C2 (default moves): two one-line
literals, non-security, zero drift —
below bar; H1 fenced. C3 (third shape):
1 body — count 1. C4 (skew hunt): no
bypass; D1 filed. C5 (fourth field
shape): slot body alone — count 1.

## Findings

### F1: stamp vs fallback — REJECTED (stages + filed skew)

Same try/scan/except-`"pk"` at creation
(seeded, write-once) and cold read
(unseeded). Below bar as x2 thin
literals AND a real contract difference:
D1 proves the unseeded skew is live, so
sharing a helper either bakes D1 in or
changes fallback behavior (barred).
Owner: none new. Zero-edit, net 0, no
machinery, no coupling. Index row for
Worker-0: `relay-id-stamp-vs-fallback`,
`types/relay.py`, `rejected`. Proof:
execution-verified probe (fallback
SHADOWED, stamped CORRECT) + upstream
source. Freshness: HEAD `c37a08a0`,
baseline `8e082d41`, pins in What
shrinks, item diff EMPTY. Triggers: T1
third spelling; T2 D1 fixed — re-pose
extraction; T3 default moves with a
third site; T4 a reader bypasses the
public read/slot.

### F2: `(attr, field)` mapping — single-owned, merge REJECTED

Different question (field, not name).
One body, 5 threading call sites, 0
re-derivations. Owner
`relay.py::_node_id_slot`, never stored.
Zero-edit. Index row:
`relay-node-id-slot-mapping`, `rejected`
(vs raising `_resolve_segment_field`,
walker FieldMeta scan). Proof: static
census + threading spy. Triggers: a
second mapping; per-id re-resolution.

### F3: custom-id detection — single-owned, merge REJECTED

Bool for elision safety, never the
attr. One body + memoized wrapper +
walker fork on the same function; C3
count 1. Owner `definition.py`.
Zero-edit. Index row:
`relay-custom-id-detection`, `rejected`
(bool vs attr). Proof: static census +
oracles. Triggers: a second body; an
inlined caller.

### F4: gate preflight — REJECTED (distinct contract)

Escape-hatch validation: pass-to-raise
vs `"pk"` fallback — different error
vocabulary. Item I owns detection.
Zero-edit. Index row:
`relay-gate-scan-posture`, `rejected`.
Proof: static vocabulary table.
Trigger: gate adopts `"pk"`
(implausible — spec-015 `:241`).

### F5: consumers — CONFIRMED, no bypass

All six consumers call the public read
or take the threaded slot. No index row
(enforcement sites). Proof: static
censuses + spy. Trigger: shared T4.

## Defects

- D1 (fallback shadows on unstamped
chains): the cold scan runs unseeded, so
two unstamped `relay.Node` classes with
differing `NodeID`s resolved parent-first
return the parent's column for the child.
Execution-proven; no oracle pins a
two-unstamped chain. Narrow reachability
(post-finalization subclasses, direct
unit calls). Owner:
`types/relay.py::_resolve_id_attr_default`.
Fix (not this item, wrong-to-right):
seed-before-scan; fires T2.

### Worker-2 errata (verdict-neutral; no code change)

- D-W2-1 (Worker-2): What shrinks claims
  stamp, slot, gate-scan, and fallback
  bodies "byte-identical HEAD to WT",
  but the same sentence correctly
  discloses the slot-read line
  (`cls.__dict__` -> `truth.class_dict`),
  the gate raise line
  (`_safe_class_name` -> `truth.name`),
  the walker guard, and the
  detection/docstring drift as foreign
  truth-migration hunks. The slot hunk is
  docstring-only; the other two are
  single-expression mechanical renames
  with identical logic. Suggest "logic
  identical; named lines carry foreign
  renames". Owner: this artifact
  (Worker-0 may fold into Outcomes or
  leave as scratch errata).

## Pending execution

None (probe executed; all else
static-reviewed).

## Judgment

One rule in three lifecycle stages plus two neighboring contracts;
every reader composes by name; zero edits, four triggers, one filed defect.

## Independent verification (Worker-2)

### Own trace (recorded before opening Findings)

One id-attr rule in three lifecycle
stages, two neighboring contracts.
Pin: `types/relay.py::_stamp_relay_id_attr`
(seeded scan, write-once at finalize
2.5). Read: `::_resolve_id_attr_default`
(own-dict hit + unseeded cold scan).
Preflight: `::_check_composite_pk_for_relay_node`
(pass-to-raise escape check).
Neighbor A (slot tuple):
`relay.py::_node_id_slot` `(attr, field)`
+ `::_coerce_pk_or_none` consumer.
Neighbor B (custom bool):
`definition.py::origin_has_custom_id_resolver`
+ memoized wrapper + walker fork.
Census: `_dsf_relay_id_attr` 1 writer
(stamp) + 1 production reader
(default); tests spell the literal as
oracles. `_id_attr`: 1 framework writer
(seed), 0 framework readers. Slot: 1
def, 5 direct calls (`relay.py:215/`
`:312/:364/:791`,
`types/relay.py:455`) + memo-threaded
readers. Finalizer: 0 value readers.
Optimizer: 0 slot readers. Six
public-read sites compose by name; three
upstream-direct scans differ by posture.
Counts: rename 1; default-move thin +
H1-fenced; third detection shape 1;
fourth field shape 1 (sole `get_field`
site; consumers test `None`/`"pk"`
vocabulary only). Own verdict: zero-edit
reject + D1 filed, reachability to rule
against the finalize lifecycle.

### Reconciliation

Every W1 site, role, and count
re-derived at WT bytes: CONFIRMED F1
stages + skew, F2 one body + 5 threading
sites + 0 re-derivations, F3 one body +
wrapper + fork, F4 posture split (I owns
detection), F5 6/6 compose by name. WT
blobs re-derived identical
(`3b4447ae`/`edfa8d6d`/`cde8437f`/`5508e486`);
item diff baseline `8e082d41` to WT on
all four candidate paths EMPTY; no new
package files (artifact untracked by
design). D-W2-1 records the one wording
slip; no finding changes.

### Consolidation search (independent)

Hunted bypass (walker FieldMeta scan
needs FieldMeta, not ModelField;
value-render and bool-compare differ in
output + fail-closed posture;
single-call double-read is one dict hit
while the batch already precomputes;
filters pk reads are the pk rule;
`_resolve_segment_field` raises vs slot
fall-through), stamp skew (extraction
needs a mode flag or bakes/changes the
D1 skew -- both barred; the `_id_attr`
spelling is upstream-owned), detection
overlap (guard already shares the free
function; merging postures changes
behavior). No above-bar candidate;
rejection stands. T1-T4 each firable as
written.

### D1 ruling: robustness row, non-blocking

Reproduced independently (parent-first
`code`/`code` SHADOWED, child-first
correct -- order-dependent, matching
W1's probe with names swapped). AGENTS.md
bar: no contract row (spec-015 `:271`
says "scan directly + map to pk", met
exactly; shadow-freedom `:267` is the
stamp's, pinned `:1223`); no feasible
shape (post-finalize Meta raises at
creation; Meta-less never registers; no
incremental finalize -- rerun no-ops;
private-function unit calls are not
public API); no wire input (registered
types always stamped; pre-finalize reads
hit upstream, not the fallback).
Seed-before-scan fix direction sound
(matches stamp incl. MRO inherit; must
not write the framework slot -- keeps 1
writer); "no two-unstamped-chain oracle"
verified (`:1223` stamped pair, `:1278`
singletons); T2 fires on the fix by
definition. Worker-0 homes D1 to a named
card; it blocks nothing here.

### Gates

Matrix 1-6 discharged soundly
(Relay-only + raw-pk non-mirror; sync
pure, G owns color twins; F1/F2/F3 hunt;
round trip shares the public read;
oracles + specs consistent, zero
falsified; fallback covers unstamped,
non-Relay contracted `False`). Pending
None sufficient: the one behavioral
claim is execution-verified twice; the
rest are structural counts. Coupling
none. Prose clean (`:NN` refs allowed in
`dry-*.md`; link scaffold 10/10). Shape:
body 148, trace ~20, judgment 2, Run
matches. Ruff: zero touched package
paths, no run. Verdict: verified, plain.

## What shrinks

Net package change: zero lines
(rejection). What was counted and where
it stays:

- The id-attr rule stays in three
lifecycle stages in `types/relay.py`:
creation pin (`_stamp_relay_id_attr`,
seed + scan + `"pk"` + slot write),
per-call public read
(`_resolve_id_attr_default`, slot hit +
cold scan + `"pk"`), gate preflight
(scan + pass-to-raise). The cold scan
re-spells the creation try/scan/except
deliberately unshared: the stages differ
by the `_id_attr=None` seed (D1), so
extraction either bakes the skew in or
changes fallback behavior.
- The `(attr, field)` mapping stays one
body (`relay.py::_node_id_slot`) with 5
threading call sites (`:215/:312/:364/`
`:791`, `types/relay.py:455`) and 0
re-derivations. The `filters` `_meta.pk`
reads are pk reads, not id-attr
mappings. The `:169` dispatch head is
H1's, cited untouched.
- Custom-id detection stays one body
(`origin_has_custom_id_resolver`) with
its memoized wrapper and the walker fork
on the same function; a third shape moves
exactly 1 body plus its docstring mirror.
- Upstream mechanics (venv strawberry
0.327.7, quoted from
`Node.resolve_id_attr` source):
`if cls._id_attr is not None: return
cls._id_attr` (inherited attribute read —
the shadowing vector) and
`cls._id_attr = candidates[0]` on success
only (runtime-cls write; failures cache
nothing). The MRO scan is child-first-safe;
only the cache read is order-dependent.
- Probe command (read-only, executed
GREEN via `heavy`):
`PYTHONPATH=examples/fakeshop heavy uv run
python
docs/dry/temp-tests/relay-id-slot-reads/probe_fallback_shadow.py`
— output: `fallback parent-first:
parent='slug' child='slug'` SHADOWED;
`stamped parent-first: parent='slug'
child='code'` CORRECT. Retained at that
path as referenced evidence (untracked).
- Oracle inventory (each spells its own
expectation, none reads the owner):
default pin
(`test_relay_interfaces.py:515`),
stamped parent-first shadowing pin
(`:1223`), slot-spelling pin (`:1244`),
single-class fallback pins (`:1278`),
both detection shapes + malformed +
cache pins (`test_definition_relations.py`),
per-batch slot-threading spy
(`test_relay_node_field.py:561`), elision
verdicts (`test_walker.py:1291`). Gap: no
two-unstamped-chain pin (D1).
- Adjudication record: stamp, slot,
gate-scan, and fallback bodies
byte-identical HEAD (`c37a08a0`) to WT
(verified by extraction diff); the
slot-read line, gate raise line, walker
`:868` guard, and detection bodies carry
foreign truth-migration hunks (no ledger
row); the slot docstring carries
unledgered concurrent prose; item diff
baseline `8e082d41` to WT on all four
candidate paths EMPTY (only plan-file
drift). WT blobs: types/relay
`3b4447ae`, relay `edfa8d6d`, definition
`cde8437f`, walker `5508e486`. Zero edits
owe zero touch regions; any future
consolidation re-verifies the foreign
regions first.
- Spec grep
(`resolve_id_attr|_stamp_relay_id_attr|`
`_dsf_relay_id_attr` over `docs/SPECS/` +
`docs/spec-*.md`): spec-015
`:148/:267/:271` (stamp + fallback +
default, exactly as shipped), spec-032
slot-to-field mapping + oracles, spec-031
+ spec-019 consumer-facing mentions — all
consistent; nothing falsified, nothing
rewritten.

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
