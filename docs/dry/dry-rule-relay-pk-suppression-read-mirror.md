# DRY review: `relay-pk-suppression-read-mirror`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `relay-pk-suppression-read-mirror` (rule: predicting whether a Relay
pk field will be suppressed — the inspect command mirrors the performer's
suppression decision for display). Provisional performer
[types-base][types-base]`::_build_annotations`, predictor
[inspect-cmd][inspect-cmd]`::Command._is_suppressed_relay_pk` — both
re-derived from their bodies, nothing inherited. Prior records only as
triggers: the file item's N1 nomination (C10/C11 two-counts, owner
candidates, reject-trigger) and the relay-node-target-guard item's
`_is_relay_shaped` sharing precedent — every edge below re-derived from
the current bodies. Never read any `worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds no row on
`types/base.py`, `management/commands/inspect_django_type.py`, or
`tests/management/test_inspect_django_type.py` — confirmed by full read
of the ledger (optimizer/walker D1 rows, `tests/base/test_init.py`,
`tests/optimizer/test_extension.py`, error-policy/registry/relay/list_field/
types-relay/finalizer docstring rows only). Both member files were
worktree-clean at `ITEM_BASELINE` (`9c45ef6c…`, verified present via
`git cat-file -t`; item-scoped diff pre-edit empty) and `git diff HEAD`
shows exactly this item's hunks on the three touched paths — concurrent
dirt elsewhere (auth/connection/filters/forms/mutations/optimizer/registry
hunks per `git status --short`) read freely, never edited.

## System trace

Rule: "which fields lose their synthesized annotation on a Relay-shaped
type". The exact suppression decision, re-derived from the performer body
(pre-edit lines 1931/1940/1983, now one owner call):

- Suppressed ⟺ (a) the field is NON-relation, (b) the type is
  Relay-Node-shaped (`_is_relay_shaped(cls, interfaces)` — `Meta.interfaces`
  holding a `relay.Node` subclass OR direct `class Foo(DjangoType,
  relay.Node)` inheritance), (c) `field.name == source_model._meta.pk.name`
  (the Django field NAME, not the column attname), (d) [performer only]
  the field is NOT in `consumer_authored_fields` (checked BEFORE (c) in
  the scalar branch — spec-029 line 99 pins the order).
- A relation pk (`OneToOneField(primary_key=True)`, an MTI parent link)
  is NEVER suppressed: the loop routes every relation through its
  relation branch before the pk check, so it keeps its auto-synthesized
  annotation and finalize resolves it to the target type.

Whether the predictor calls the performer: NO — and it cannot
(`_build_annotations` synthesizes with side effects: pending-relation
records, converter calls). Pre-edit the predictor RE-DERIVED the
conjunction inline (relation-first guard + `_is_relay_shaped` composed by
name + `definition.model._meta.pk.name` equality) and OMITTED input (d)
entirely, while `_resolve_row` dispatches suppressed-BEFORE-consumer
(the performer and the nullability validator both go consumer-first).
Post-edit the conjunction lives once in
[types-base][types-base]`::_is_suppressed_relay_pk`; the performer loop
and the predictor method both call it. `_is_relay_shaped` was already
shared (pinned by the direct-inheritance oracle); this item extends the
sharing from the predicate to the whole decision.

Connected sources read: [types-base][types-base] (full suppression
region + `_is_relay_shaped` + `_validate_nullability_override_targets`
relay-pk arm + id-collision guard), [inspect-cmd][inspect-cmd] (full
`_resolve_row` dispatch + all row builders), [finalizer][finalizer]
(pending-walk defense-in-depth + `_field_surface_names`), [resolvers][resolvers]
(`_attach_file_resolvers` consumer-skip), [types-relay][types-relay]
(NodeID/`resolve_id_attr` surface), `converters.py` (entry-point prose), [spec-029][spec-029] Decision 4 + line-99 ordering, [spec-019][spec-019]
(`code: str` override accepted), [file-item][file-item] (R4/N1/C10/C11).
Excluded on strength of body: `connection.py:860` (`"pk"`-segment alias
in cursor/order paths), `filters/base.py::_target_definition_for`
(GlobalID decode routing), every other package module (zero suppression
vocabulary in the whole-package sweep).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** One synthesis surface (types) + one
   diagnostic reader (management command). No sibling flavor (filters,
   orders, mutations, forms, `rest_framework`) synthesizes type
   annotations or re-derives pk suppression — swept by mechanism tokens.
   Trigger: a second annotation synthesizer.
2. **Sync/async twins.** Pure sync predicate over class objects, model
   metadata, and field flags; no await boundary, no twin, none owed.
3. **Derived rather than repeated knowledge.** The pk identity
   (`model._meta.pk.name`) is read from Django at both sites — same
   source, not a copy. The DUPLICATED knowledge was the conjunction
   (relation-first + shape + pk-equality), spelled twice pre-edit, now
   once. Trigger: a third site spelling the conjunction.
4. **Inverse / round-trip pairs.** Build (emit-or-drop at class creation)
   vs display (predict the row post-finalize) answer the SAME question
   at different phases — not inverses. No encode/decode pair exists.
5. **Contracts restated in another medium.** Production (performer +
   predictor); oracles (independent literals/throwaway types on both
   sides — never reading the owner); projections (both docstrings; the
   predictor's 20-line decision restatement was a prose third copy —
   deleted by this item, now a pointer); specs (spec-029 Decision 4,
   spec-019 override acceptance); glossary (Relay-suppressed-pk entries —
   descriptive, counted zero).
6. **Enforcement by omission.** Population enumerated (6 members + 1
   boundary): relay scalar pk, non-relay scalar pk, direct-inheritance
   relay pk, relay relation pk, non-relay relation pk, non-`id` scalar pk
   — every member carries the guard its contract requires EXCEPT the
   consumer-authored pk, which the predictor omits (contract sources:
   spec-019 acceptance + spec-029 ordering + schema wire truth) → defect
   D1, not a second definition. Untyped assigned-only overrides never
   finalize (`MissingFieldAnnotationError` at `strawberry.type` time, WS
   probe) so they never reach the predictor — outside the population.

### Enumeration

Instrument: whole-package grep for `suppress_pk_annotation |
_is_suppressed_relay_pk | relay_pk_name | pk_name | _meta\.pk\.name` over
117 `.py` (plan count; no adds/renames) + `def` census per symbol.

- `_is_suppressed_relay_pk`: 2 defs post-edit — [types-base][types-base]
  (authoritative decision, 1 def) + [inspect-cmd][inspect-cmd]`::Command`
  (display adapter unpacking the definition, 1 def, consumer role).
  Production callers of the owner: 2 (performer loop, predictor method).
- `suppress_pk_annotation` / `pk_name` locals: 0 post-edit (folded into
  the owner; was 1 derivation site).
- `_is_relay_shaped`: 1 def; now 1 fewer direct reader (the predictor
  reads it transitively through the owner).
- `_meta.pk.name` production reads: owner body + validator
  `relay_pk_name` (adjacent override-rejection rule, listed not counted)
  + `connection.py:860` + `filters/base.py` docstring prose (different
  rules sharing the token, excluded).
- Oracles: performer unit rows (`_build_annotations` direct calls incl.
  CustomNode + non-relay control in [test-relay-interfaces][test-relay-interfaces]),
  predictor row rows (direct-inheritance, O2O, MTI in
  [test-mgmt-inspect][test-mgmt-inspect], GenreType live in
  [fakeshop-inspect][fakeshop-inspect], override validation in
  [test-types-base][test-types-base]), NEW mirror gate (6 arms, below). All use
  independent literals/records, never the owner.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Pre-consolidation counts (the
duplication evidence); post-consolidation each moves at the owner alone.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Relation pks join the suppressed population (suppress relation pks too) | **2** (performer loop order + predictor `is_relation`-first check; the O2O/MTI twins fail — listed). File-item C11 re-derived. |
| C2 | Pk-identity rule change (suppress by attname; a second pk-like name) | **2** (performer pk derivation + predictor pk read; validator `relay_pk_name` also moves — listed adjacent, not counted). |
| C3 | Consumer-authored pk must display as its consumer row (the D1 fix) | **1** (performer already consumer-first — moves zero; only the predictor moves). NOT duplication: single-sited rule + predictor omission = defect D1. |

## Findings

### F1 — relay-pk-suppression decision (CONFIRMED duplication → consolidated)

- **Contract + variation.** Which selected fields lose their synthesized
  annotation on a Relay-shaped type. Varies on the suppressed population
  (today: non-relation pks only) and the pk-identity rule (field NAME).
- **Sites + roles.** *Definition*: [types-base][types-base]
  `::_is_suppressed_relay_pk` (new; pure per-field predicate).
  *Consumers*: `_build_annotations` loop (calls it in the scalar branch
  after the consumer short-circuit — order preserved) and
  `Command._is_suppressed_relay_pk` (unpacks
  `origin/interfaces/model/field`, calls it — the method stays as the
  command-side entry so the file-item index row and `_resolve_row` call
  site are undisturbed). *Oracles / projections*: as listed.
- **Challenges.** C1 → 2; C2 → 2; C3 → 1 (omission, see D1).
- **Owner + lifetime (principles 7, 4).** [types-base][types-base] stands:
  synthesis owns the drop (keeping Strawberry's interface `id` from
  colliding is a type-construction contract); the command already
  imported from it (no reversed dependency); it is the narrowest module
  both sides can depend on. No stored derivation — pure per-call
  predicate over class/model/field inputs (recomputed per non-relation
  field at class-creation time only; negligible cost, no cache).
- **Migration.** Performer: `suppress_pk_annotation`/`pk_name` locals +
  comments folded into the owner (NAME-vs-attname knowledge moved, not
  dropped); loop calls the owner. Predictor: 20-line restated docstring
  replaced by an adapter pointer; body delegates; `_is_relay_shaped`
  import swapped for the owner (now its only transitive reader).
- **Distinct behavior.** Consumer-first ordering at BOTH pre-existing
  sites untouched (performer short-circuit, `_resolve_row` dispatch) —
  D1 persists byte-identically (see D1; no coupling: this consolidation
  lands without it).
- **Behavioral proof.** `execution-verified` in WS: 6-arm mirror probe
  pre-edit (4 agree + 2 D1-diverge), gate + 43 inspect tests + full
  relay-interfaces module + relay/override selections post-edit, N1/N2
  controls; plus the authorized shared-tree focused gate runs.
  `static-reviewed` for import shape, comment moves, oracle independence.
- **Structural gate.** NEW mirror-consistency test
  `test_inspect_suppressed_pk_mirror_matches_synthesis` (6 arms over the
  covered population; oracle reads the merged `__annotations__` record,
  never the owner). Negative controls proved in WS: N1 divergent mutant
  (dropped guards) FAILS the gate; N2 behavior-preserving hand copy
  PASSES it (gate checks behavior not call-unity — unity rests on the
  def/caller census + T-triggers, the sibling-item standard).
- **Coupling.** None — D1 is independent (lands or not without touching
  this consolidation; its future fix extends the gate + adds the
  T-exemption parameter).
- **Freshness.** Blob ids below. Any fingerprint change reopens.
- **Reconsideration triggers (recorded at the owner).** T-population
  (new suppressed member → extend the owner body, both callers follow);
  T-identity (pk-identity change → the owner read owns NAME-vs-attname);
  T-exemption (consumer exemption → add the parameter here, never a
  second predicate at a caller). Durable homes: the owner docstring
  clause, this finding, and the plan's `## Outcomes` via Worker 0.

### F2 — stored suppressed flag on the definition (REJECTED)

- **Contract difference considered.** Publish `relay_suppressed_pk`
  (or per-field set) on `DjangoTypeDefinition` at construction; the
  predictor becomes a pure fact reader. Same verdicts as F1 on every
  reachable input.
- **Why rejected.** New stored state for a pure derivable predicate =
  machinery (principle 4: pure derivation says "not cached";
  anti-duplication never mandates new shared state). Blast radius:
  `definition.py` shape + base.py publish + command read + principle-4
  lifetime fields owed, against F1's one helper + two call sites. The
  predictor's inputs are all available at display time, so no capability
  gap forces the store.
- **Trigger.** Predictor needs an input unavailable post-finalize, or
  the per-field predicate cost becomes load-bearing on a hot path.
  Home: this finding + the F1 owner clause.

### F3 — derive-from-absence (REJECTED)

- **Contract difference considered.** Predictor checks `field.name not in
  origin.__annotations__` instead of predicting — agreement by
  construction, zero new state.
- **Why rejected.** Absence is AMBIGUOUS post-state: assigned-only
  consumer overrides share it (present in
  `__strawberry_definition__`, absent from `__annotations__`), so the
  dispatch still needs the consumer check first — and absence is
  FAIL-OPEN to future synthesis skips (a new skip silently reports as
  the Relay `id` row), while the explicit predicate fails closed (falls
  to the scalar/consumer branch — loud). The connection-only shape's
  absence detection is not precedent: it keys off the synthesizer's own
  `relation_connections` record, not bare absence.
- **Trigger.** Synthesis guarantees every non-suppressed selected scalar
  present in `__annotations__` (absence ⟺ suppressed) AND the consumer
  check ordered first. Home: this finding + the F1 owner clause.

## Defects

### D1 — predictor ignores `consumer_authored_fields` (UNFIXED, routes to owner)

A consumer override of the pk column on a Relay-shaped type is legal
(spec-019: "`code: str` on `models.CharField(primary_key=True)`" is
accepted; the `id: relay.NodeID[int]` escape hatch is accepted) and the
performer honors it (consumer short-circuit runs BEFORE suppression, so
the consumer annotation survives the merge). The predictor consults
neither `definition.consumer_authored_fields` nor the consumer row, and
`_resolve_row` dispatches suppressed-first — so the table claims the
interface row while the schema exposes the consumer's type. WS
wire proof (copy `__file__` + DB `NAME` recorded below): relay type
over a `code`-pk model with `code: str` override → table row
`('GlobalID!', 'no', 'relay.Node id')`, schema wire `code: String!`.
Escape-hatch variant: table `GlobalID!`/`relay.Node id`, wire `id: ID!`
(type display coincides by the command's `GlobalID!` spelling
convention; the converter column misattributes the producer).
Pre-existing (reproduced against the unedited WS copy before this
item's first edit — no consolidation needed to exhibit it) and
preserved byte-identically by F1. Owner:
`management/commands/inspect_django_type.py::Command._resolve_row`
(dispatch order + missing input; future fix adds the T-exemption
parameter at the F1 owner). Worker 0 homes it on a NAMED owning card;
never fixed inside this item.

## Pending execution

None. Every behavioral claim is `execution-verified` in the disposable
workspace (commands + results under `## Implementation (Worker 1)`),
plus the authorized shared-tree focused gate node (same node, twice —
pre/post ASCII-fix — 1 passed each).
`FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by construction`:
every executed claim is class-creation synthesis plus finalized-record
reads — no database row, alias, or dialect decision is reached (the
recorded `NAME` is the copy's own untouched sqlite file). Full-suite
gate business deferred to the final-gate item with reason: the entry
authorizes workspace runs plus one focused `--no-cov` test, and a green
unmutated suite would discharge no failability proof for this finding.

## Judgment

The suppression decision was spelled twice (performer branch +
predictor re-derivation, C1/C2 → 2) with the shape predicate already
shared: duplication confirmed and consolidated at
[types-base][types-base]`::_is_suppressed_relay_pk`, both call sites
composing it by name, behavior byte-identical. Stored-flag and
derive-from-absence alternatives rejected with difference + trigger +
home. The consumer-authored gap is NOT duplication (C3 → 1) but a
predictor omission with spec + wire proof — defect D1, unfixed, routed.
Mirror gate added with both proved negative controls.

## Implementation (Worker 1)

Tracked changes (3 files; `git diff 9c45ef6c…` shows exactly these):

- `django_strawberry_framework/types/base.py` — new owner
  `_is_suppressed_relay_pk(cls, interfaces, source_model, field)` with
  the decision + NAME-vs-attname + T-population/T-identity/T-exemption
  trigger clause; `_build_annotations` loop calls it (locals
  `suppress_pk_annotation`/`pk_name` folded in, branch comments kept).
  Attribution: clean at baseline (`91c58747…`) and at edit time; no
  ledger row on the path.
- `django_strawberry_framework/management/commands/inspect_django_type.py`
  — predictor method delegates to the owner (decision restatement
  replaced by adapter pointer); import swaps `_is_relay_shaped` for
  `_is_suppressed_relay_pk`. Attribution: clean at baseline
  (`46dffb3d…`); no ledger row.
- `tests/management/test_inspect_django_type.py` — `MirrorCodeModel`
  (non-`id` scalar pk), `_mirror_check` helper, 6-arm
  `test_inspect_suppressed_pk_mirror_matches_synthesis` gate (consumer
  arm excluded with D1 reason); direct-inheritance docstring mechanism
  sentence updated to the delegation path. Attribution: clean at
  baseline (`6bad5092…`); no ledger row.

Proofs (disposable workspace per [DRY.md][dry] "Tests"; `rsync` copy
minus `.git/.venv/__pycache__/docs`; every command via
`uv run --frozen --directory "$WS"` with
`WS=.../dry-ws/relay-pk-suppression-read-mirror-w1`):

- Copy `__file__`:
  `.../relay-pk-suppression-read-mirror-w1/django_strawberry_framework/__init__.py`;
  DB `NAME` resolved from inside `$WS`:
  `.../relay-pk-suppression-read-mirror-w1/examples/fakeshop/db.sqlite3`
  (the copy's own tree and database; import-identity asserted
  `is_relative_to(WS)` in every probe).
- Pre-edit probe `exp-relay-pk-w1.py` (`execution-verified`): 4
  predictor⟺performer AGREE (relay scalar pk incl. non-`id` spelling,
  non-relay control, direct inheritance, relation pk) + D1/D1b DIVERGE
  with schema-wire lines (`code: String!`, `id: ID!` vs `GlobalID!`
  rows). Untyped assigned-only override dies at finalize
  (`MissingFieldAnnotationError`) — outside the population, recorded.
- Post-edit (edits synced by `cp`, `cmp`-verified in-sync, all on
  final bytes): new gate 1 passed;
  `tests/management/test_inspect_django_type.py` +
  `examples/fakeshop/tests/test_inspect_django_type.py` 43 passed;
  full `tests/types/test_relay_interfaces.py` 142 passed;
  relay/override selections across `test_relay_interfaces.py` +
  `tests/types/test_base.py` 14 passed.
- N1 divergent mutant (guards dropped) → gate 1 FAILED (failability
  proved); N2 hand copy (old inline body, no owner call) → gate 1
  PASSED (behavior not call-unity); both restored byte-identical via
  `cmp` + full module re-verified (19 passed).
- Authorized shared-tree focused run (same node, twice: pre- and
  post-ASCII-fix — the second edit touched comment bytes only):
  `uv run pytest
  tests/management/test_inspect_django_type.py::test_inspect_suppressed_pk_mirror_matches_synthesis
  --no-cov -n0 -q` → 1 passed each time. WS copies re-synced by `cp`
  after the ASCII fix and `cmp`-verified in-sync; WS module re-run
  19 passed, so all proofs bind the final bytes.
- After edits: `uv run ruff check --fix` + `uv run ruff format` on the
  three paths — both green (`format --check` + `check` pass; scoped to
  the paths so concurrent dirt is untouched) plus
  `check_trailing_commas.py --check` green (artifact excluded from
  source-layout rules; the 5 em-dash hits it reported in new `.py`
  prose were replaced with ASCII hyphens before the final proof runs).
  No `CHANGELOG.md` touch. No commit per standing rule.

Worker 0 rows: tick Family `relay-pk-suppression-read-mirror` (this
artifact); `## Responsibility index` row → `consolidated` with owner
`django_strawberry_framework/types/base.py::_is_suppressed_relay_pk`
(files covered unchanged); append `## Owned changes`:
`django_strawberry_framework/types/base.py` — Family
`relay-pk-suppression-read-mirror` — new `_is_suppressed_relay_pk`
owner + `_build_annotations` call site (consolidation;
behavior-preserving);
`django_strawberry_framework/management/commands/inspect_django_type.py`
— Family `relay-pk-suppression-read-mirror` — predictor delegates to
the owner (consolidation; behavior-preserving);
`tests/management/test_inspect_django_type.py` — Family
`relay-pk-suppression-read-mirror` — `MirrorCodeModel` +
`test_inspect_suppressed_pk_mirror_matches_synthesis` mirror gate +
negative controls N1/N2; home D1 on a NAMED owning card (owner:
`management/commands/inspect_django_type.py::Command._resolve_row`).

Freshness fingerprints (`git hash-object` worktree; HEAD `bfaee91d`;
`ITEM_BASELINE` `9c45ef6c…` present; pre-edit baseline blobs
`91c58747…` / `46dffb3d…` / `6bad5092…`): `types/base.py`
`4bd9ad16…`, `inspect_django_type.py` `9d52ddbc…`,
`types/finalizer.py` `f4266a15…`, `types/resolvers.py` `f3341e6a…`,
`types/relay.py` `c333c785…`,
`tests/management/test_inspect_django_type.py` `0d000bb6…`,
`tests/types/test_relay_interfaces.py` `26fb2ccf…`,
`tests/types/test_base.py` `4282e0b0…`,
`examples/fakeshop/tests/test_inspect_django_type.py` `925a394d…`,
`dry-file-management__commands__inspect_django_type.md` `7c01464c…`,
`dry-0_0_15.md` `e732711b…`, `spec-029-consumer_dx_cleanup-0_0_9.md`
`2dca98da…`, `spec-019-consumer_overrides_scalar-0_0_6.md`
`ec838460…`. Searched population: whole package (117 `.py`) for the
suppression tokens; every other module excluded on zero vocabulary.
Any fingerprint change reopens the finding.

Scratch paths (removal is Worker 0's, after `verified`, by explicit path):
`WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/relay-pk-suppression-read-mirror-w1`
(includes its own `.venv`), probe
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/exp-relay-pk-w1.py`,
mutator
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/mutate-relay-pk-w1.py`,
pristine backup
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/inspect-cmd-pristine-w1.py`
(kept only until Worker 2 confirms the restore; `cmp`-verified
identical already).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[file-item]: dry-file-management__commands__inspect_django_type.md
[spec-019]: ../SPECS/spec-019-consumer_overrides_scalar-0_0_6.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[inspect-cmd]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-mgmt-inspect]: ../../tests/management/test_inspect_django_type.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py
[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-inspect]: ../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Worker-2 independent trace, recorded BEFORE reading `## Findings` (only
`Status:`/`Run:`/`## ` headings + plan + source + item-scoped diff inspected).

Scope: Family `relay-pk-suppression-read-mirror`, Run `0.0.15 2026-09-19-1`.
ITEM_BASELINE `9c45ef6c0535d3606150599711d5c9b652f002e3`; item-scoped diff
(`git diff <baseline> -- <3 paths>`) is EXACTLY 3 files, +170/-37:
`django_strawberry_framework/types/base.py` (+60/-~: new
`_is_suppressed_relay_pk` + build-loop call site), `django_strawberry_framework/management/commands/inspect_django_type.py`
(import swap + `_is_suppressed_relay_pk` body -> delegation), `tests/management/test_inspect_django_type.py`
(+108: `MirrorCodeModel` + `_mirror_check` + mirror gate). Full-tree diff vs
the same baseline adds only `docs/bug_hunt/bug_hunt-0_0_15.md` (orders/base
hunting->verified bookkeeping) — concurrent, not this item. No other hunks in
the 3 paths; `git diff HEAD -- <3 paths>` reproduces the same content (dirty
only by this item plus concurrent tree dirt elsewhere, left alone).

Sites traced (whole-package read fenced by the rule mechanism
`_meta.pk.name` / `_is_relay_shaped` / `is_relation` + consumers/tests):

1. `django_strawberry_framework/types/base.py::_build_annotations` (PERFORMER,
   pre-consolidation inline): hoisted `suppress_pk_annotation =
   _is_relay_shaped(cls, interfaces)` + `pk_name = source_model._meta.pk.name
   if suppress_pk_annotation else None` once before the loop; inside the
   non-relation scalar branch AFTER the `consumer_authored_fields`
   short-circuit, `if suppress_pk_annotation and field.name == pk_name:
   continue`. Relation fields never reach the check (early `field.is_relation`
   branch with its own consumer short-circuit + pending append). Decision =
   non-relation AND relay-shaped AND name == pk NAME (comment explicitly
   NAME-not-attname with the `user` vs `user_id` example + the
   `getattr(root, pk_attname)` lazy-load warning). AUTHORITATIVE definition 1.
2. `django_strawberry_framework/management/commands/inspect_django_type.py::Command._is_suppressed_relay_pk`
   (PREDICTOR, pre-consolidation inline): `if field.is_relation: return False`;
   `if not _is_relay_shaped(definition.origin, definition.interfaces): return
   False`; `return field.name == definition.model._meta.pk.name`. Called FIRST
   in `_resolve_row` BEFORE the `consumer_authored_fields` check, so a
   consumer override of the pk column predicts suppressed. AUTHORITATIVE
   definition 2. Same three conjuncts as (1), different input shapes
   (loop-locals `cls`/`interfaces`/`source_model`/`field` vs unpacked
   `definition.origin`/`definition.interfaces`/`definition.model`/`field`) and
   different timing (build-time hoisted boolean + per-field name compare vs
   per-call full recompute).
3. Adjacent, ruled OUT as same rule (reasons to change differ):
   - `django_strawberry_framework/types/base.py::_validate_nullability_override_targets`
     `relay_pk_name` arm: VALIDATION rejection (`ConfigurationError` when an
     override names the suppressed pk), contract = nullability-override
     surface, not annotation-suppression/display. Change the suppression
     population and this error message moves only as a consequence; change the
     override policy and suppression does not move. Separate.
   - `django_strawberry_framework/connection.py::_resolve_order_path_field`
     `pk`-segment alias (`current._meta.pk.name if segment == "pk"`): order/
     cursor path resolution, no relay-shape gate, no relation guard. Separate.
   - `django_strawberry_framework/filters/base.py::_target_definition_for` /
     `::resolve_globalid_target_definition` own-PK-vs-relation branch:
     GlobalID filter target resolution (owner vs related target), consumes pk
     NAME but answers a different question (which definition validates).
     Separate.
   - `django_strawberry_framework/types/base.py::_is_relay_shaped` itself:
     shared SUB-predicate (shape only), already single-owned, consumed by
     both sites — not a second suppression definition.
   - `django_strawberry_framework/list_field.py` relay-shape read: shape
     consumer, not suppression.

Definition counts (change-challenge, pre-consolidation):
- C1 (new suppressed population member, e.g. suppress a second column):
  count 2 — build loop + predictor each spell the full conjunct list.
- C2 (pk-identity rule change NAME->attname or different pk source): count 2
  — `pk_name` derivation + predictor `field.name == ...pk.name` each move.
- C3 (shape-gate change, e.g. new Relay spelling): count 1 —
  omission-not-duplication; both sites already composed `_is_relay_shaped`
  by name, so only the shared predicate moves. (This is why the family is a
  2-site partial-mirror consolidation, not a 3-site one.)

Owner I would choose: `django_strawberry_framework/types/base.py::_is_suppressed_relay_pk`
(synthesis owns the drop). Responsibility: the build loop is where the
annotation is actually dropped and where the relation-first branch order +
NAME-vs-attname contract + spec-015 Decision 2 prose already live; the
command is a display-time read mirror that already imports from
`types.base` (`DjangoType`, `_is_relay_shaped`), so depending on the new
helper reverses no dependency, while the reverse (types importing a
management command) would. Narrowest cohesive owner every legitimate consumer
can import. Signature `(cls, interfaces, source_model, field)` keeps the
caller's input shapes (loop-locals vs unpacked definition) at the adapters.
`consumer_authored_fields` deliberately NOT a parameter: both callers apply
their consumer exemption OUTSIDE the predicate (build loop short-circuits
before; `_resolve_row` dispatches after) — folding it in would change the
predictor's observed order and couple the owner to a caller-specific
exemption. Reconsideration trigger for that exemption belongs at the owner
as prose.

Freshness at trace time: `types/base.py` blob `4bd9ad163eeb692ab9d3ae55c3d18a08088f94a7`,
`inspect_django_type.py` blob `9d52ddbc74b85ddde9a4e4ca58c626cb24053c4a`,
`test_inspect_django_type.py` blob `0d000bb67c5e950c68ae5cda05b512186c173539`;
HEAD `bfaee91d`; CURRENT BASELINE `859e55ba76a4494ee39bf227430d57f6cef2fdbd`
(not yet re-hashed — owed in reconciliation below).

### Reconciliation + verdict (Worker 2) — read AFTER the trace above

Hunk-by-hunk (against `git show 9c45ef6c…` pre-edit bodies; item diff
exactly 3 files +170/-37, the only extra tree-vs-baseline delta is the
concurrent `docs/bug_hunt/bug_hunt-0_0_15.md` orders bookkeeping):

- Helper `types/base.py::_is_suppressed_relay_pk` == union of the two
  prior inline predicates, nothing dropped: `field.is_relation → False`
  (both), `not _is_relay_shaped(cls, interfaces) → False` (both; predictor
  already composed it by name, performer hoisted it), `field.name ==
  source_model._meta.pk.name` (both; performer's `pk_name` ternary folded
  in). NAME-vs-attname comment moved with its `user`/`user_id` example +
  `getattr(root, pk_attname)` lazy-load warning intact. Short-circuit
  order identical at the predictor; at the performer the shape check moves
  from hoisted-before-loop to per-field-after-`is_relation`, same values
  (`cls`/`interfaces` loop-invariant).
- Call-site parity: performer calls post-`consumer_authored_fields`
  short-circuit in the non-relation branch (order preserved; the helper's
  `is_relation` guard is unreachable-but-harmless there). Command adapter
  unpacks `definition.origin/interfaces/model` + `field` — the exact values
  the inline read — still first in `_resolve_row` (D1 order preserved
  byte-identically, by design). Import swap `_is_relay_shaped` →
  `_is_suppressed_relay_pk` leaves no code reference behind (one prose
  mention only); census: 1 authoritative def + 1 adapter def + 2
  production callers, no other readers.
- Principle 8: no query/transaction/cancellation/state effects (pure
  `_meta` reads at class-creation/display time; per-field `_meta.pk`
  re-read vs one hoisted read is unobservable — every Django model has a
  pk). Exceptions parity holds on all reachable shapes; the only divergence
  is theoretical (hostile `interfaces` + hostile field both raising →
  different precedence; empty `fields` + broken `_meta.pk` → old raised at
  hoist, new never calls) — unreachable via validated interfaces + real
  `_meta` fields, no contract row, not a defect.

Tests: tier correct (`tests/management/` — management-command display +
construction-time record, unreachable from live GraphQL; the schema side
stays covered by `test_relay_interfaces.py`). Oracle independent: opened
the +108 hunks — `_mirror_check` compares predictor AND build record
(`field.name not in origin.__annotations__`) each against the `expected`
literal, never the owner; N2-hand-copy-passes is documented as intended
(unity rests on def/caller census + T-triggers). Population covers relay
scalar pk (`id` + non-`id` `code` via new `MirrorCodeModel`), non-relay
control, direct inheritance, relay + non-relay relation pks; the consumer
arm is excluded with the D1 reason stated in the gate docstring. Prior
behaviors preserved: WS2 full inspect module 19 passed, WS2
`test_relay_interfaces.py` 142 passed.

N1/N2 (RE-RAN the stronger, N1, in a FRESH copy
`dry-ws/relay-pk-suppression-read-mirror-w2` taken after W1's edits;
`__file__` + DB `NAME` both resolve inside the copy): pristine gate 1
passed; N1 (adapter → bare `field.name == …pk.name`, W1's mutator text
replicated) FAILED (`MirrorPlainCategory.id: predictor True`, `1 failed`);
restored byte-identical (`cmp` vs shared tree) → full module 19 passed.
N2 accepted on record: its text is the baseline inline body (verified via
`git show`), W1 recorded PASS, and my N1-fail + pristine-pass pair already
proves the gate is behavior-sensitive and non-vacuous.

D1 (HARD, execution-confirmed in fresh WS2 on final bytes): relay type
over a `code`-pk model with accepted `code: str` override →
`consumer_authored == ['code']`, predictor `True`, yet `code` stays in
`origin.__annotations__` as `str` and the Strawberry surface exposes
`code: str` — table would claim the interface row while the schema exposes
the consumer type. Bar met: contract rows (spec-019 override acceptance +
spec-029 consumer-first ordering + schema wire truth), feasible shape
(plain consumer scalar override on a Relay pk), reaching input (the
inspect command). Class: wrong-DISPLAY behavior defect (schema behavior
correct), regular card — no security impact, no `SECURITY.md` path. Owner
`inspect_django_type.py::Command._resolve_row` correct (dispatch order +
missing input). No-coupling CORRECT: the helper takes no consumer param,
both callers keep their pre-existing consumer order, F1 lands with D1
byte-identical; the fix path (T-exemption param + gate consumer arm) is
recorded at the owner.

F2/F3 rejections judged CORRECT: F2 (principle-4 pure derivation, no
capability gap, blast-radius reasoning; trigger = unavailable input or
hot-path cost); F3 (absence ambiguous with assigned-only overrides,
fail-open vs fail-closed, connection-only precedent distinguished by its
own `relation_connections` record; trigger conjoins both needed
guarantees). Homes recorded.

Freshness re-hashed: 3 touched blobs match W1 exactly (`4bd9ad16…`,
`9d52ddbc…`, `0d000bb6…`); related inputs match (`f4266a15…`,
`c333c785…`, `26fb2ccf…`, `4282e0b0…`, `925a394d…`); HEAD still `bfaee91d`;
`859e55ba` is the dispatch WIP stash on `bfaee91d` (my fresh `stash
create` differs only by later concurrent tracked dirt — out of scope,
untouched). No fingerprint change → no reopen. `## Pending execution`:
None — judged CORRECT (every claim execution-verified; sharded/PG
inapplicable by construction: synthesis + finalized-record reads reach no
row/alias/dialect; full-suite gate belongs to the final-gate item).

AGENTS.md prose: `.py` diff grep for worker/pass/provenance tokens clean;
citations are `path::Symbol` (`types/base.py::_is_suppressed_relay_pk`,
`types/base.py::_is_relay_shaped`), no line numbers; test/helper names
state invariants
(`test_inspect_suppressed_pk_mirror_matches_synthesis`,
`_mirror_check`, trigger clauses at the owner). Ruff (run myself on the 3
paths): `format --check` 3 files already formatted;
`check` All checks passed; `check_trailing_commas.py --check` exit 0.
Shared-tree focused gate (authorized `--no-cov`): 1 passed.

Agreement/difference vs the points: helper body, both call sites,
adjacent exclusions, owner, F1 byte-identical, F2/F3, D1 unfixed +
uncoupled, no-pending-execution, WS proofs — all AGREE. One complement,
not conflict: my trace C3 posited the shape-gate change (count 1, already
shared) while the artifact C3 posits the consumer-exemption change (count
1, D1 omission) — both true; together they pin why this is a 2-site
partial-mirror consolidation.

Defects: none new (Worker 2) — the theoretical exception-precedence edge
above has no contract row and is unreachable; D1 stands as filed.

Verdict: `verified`, no pending execution. Worker 0 rows — tick Family
`relay-pk-suppression-read-mirror`; `## Responsibility index` row →
`consolidated`, owner
`django_strawberry_framework/types/base.py::_is_suppressed_relay_pk`;
`## Owned changes` += the 3 W1-listed rows verbatim
(`types/base.py` owner + call site; `inspect_django_type.py` delegation;
`test_inspect_django_type.py` gate + N1/N2) + home D1 on a NAMED owning
card (owner `management/commands/inspect_django_type.py::Command._resolve_row`);
scratch removal (after tick, by explicit path): W1 `WS` tree +
`exp-relay-pk-w1.py` + `mutate-relay-pk-w1.py` +
`inspect-cmd-pristine-w1.py` (artifact lines 389-399) AND W2
`dry-ws/relay-pk-suppression-read-mirror-w2/` +
`dry-ws/inspect-cmd-pristine-w2.py` (this run; shared tree + live-test DB
untouched — WS2 `.venv` + `examples/fakeshop/db.sqlite3` are the copy's
own).

## Run 0.0.15 2026-09-21-3 note (Worker 0, appended — history above untouched)

Consolidation UNAPPLIED in this tree. The owner half
(`types/base.py::_is_suppressed_relay_pk`) was never written here (0 hits at
`69a25369`, at `24e6b4d3`, and in the worktree); the maintainer's agent reverted the
consumer half, so `management/commands/inspect_django_type.py` is HEAD plus a
7-line docstring citation fix and the predictor is back to its inline form.
The `## Implementation` / verification record above describes 09-19 bytes on
another checkout — a prior-cycle input per the worktree-entry ruling, not
evidence. Current state: no owner, no delegation, no behavior change; the
adopted mirror-gate test dirt is retained and guards the inline predictor
(`--collect-only`: 19 collected, 0 errors — the ImportError is gone).
Blocked-on-hunt: re-applying the owner would edit hunt-dirtied
`types/base.py`. Options stand: (a) the maintainer restores the owner hunk himself; (b)
the maintainer authorizes a DRY repair item; (c) leave reverted. Do not re-apply the
consumer half. Full record: plan `## Run 0.0.15 2026-09-21-3`.
