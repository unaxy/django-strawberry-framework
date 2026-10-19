# DRY review: `mro-map-key-lookup`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule is the MRO-map key lookup: the first class in
`type(field).__mro__` keying a class map, or absence. Two tree states
tell one story. At HEAD bytes the lookup is spelled three times: two
value legs in [converters][converters] (`scalar_for_field` over
`SCALAR_MAP`, value-or-raise; `_field_output_type_for` over
`FIELD_OUTPUT_TYPE_MAP`, value-or-`None`) and one naming predictor in
[inspect][inspect] (`_matched_scalar_key` over `SCALAR_MAP`,
key-name-or-concrete-name). In the worktree the hunt's in-flight
truth-migration unified the two value legs behind a new
`_class_map_lookup` identity scan while leaving the CLI predictor on
its plain-`in` walk — so the worktree carries two live walk bodies
that observably disagree (see the divergence probe under F1).

Sites found, with roles:

- *Definitions.* HEAD: 3 (`scalar_for_field`, `_field_output_type_for`,
  `_matched_scalar_key`). Worktree: 2 (`_class_map_lookup` serving
  both value legs, `_matched_scalar_key` still spelling its own walk).
- *Consumers (compose by name, listed not counted).* Of
  `scalar_for_field`: `convert_scalar`, `filters/inputs.py::
  _scalar_from_model_field`, the `mutations/inputs.py` id-type rule,
  two `serializer_converter.py` sites (5 call expressions, 4
  modules). Of `_field_output_type_for`: `convert_field_output`,
  `resolvers.py` attach, `base.py` selection check, the inspect
  `_scalar_row` file branch (4 sites). Of `_matched_scalar_key`: the
  `_scalar_row` converter column (1 site).
- *Oracles (independent literals, never read the owner).* 8 nodes in
  `tests/types/test_converters.py` (subclass scalar ×2, unknown
  raises, Duration raises, Binary raises, output precedence,
  consumer-image-subclass opt-in, unsupported message) + 1 node in
  `tests/management/test_inspect_django_type.py` (predictor names the
  ancestor). All 9 re-run green at baseline (run
  `dry-20261001T175412-d2b4bf`).
- *Projections.* Module + function docstrings restating first-match
  in both family files; the `forms/converter.py` resolution comment;
  the skeleton riders' docstrings.

Connected behavior examined whole: both family files, the
[utils-converters][utils-converters] skeleton + its four riders, the
six other executable MRO scans (finalizer, relay, definition, base,
sets-mixins, querysets bodies), `utils/truth.py` (the read
mechanism), every `SCALAR_MAP` / `FIELD_OUTPUT_TYPE_MAP` /
`FILESYSTEM_PATH_OUTPUT_TYPE_MAP` use package-wide (the only
out-of-module map read is the predictor's own walk line), the
`FILESYSTEM_PATH_OUTPUT_TYPE_MAP[output_type]` direct subscript
(designed-non-walk), and the three oracle files. Prior records
(FAM-MRO, the utils-converge note, RJkeywalk) were orientation only;
every count below is re-derived at HEAD `dd0b6691` + worktree.

## Verification

### Matrix

Each axis discharged for the family as a whole.

1. **Cross-flavor policy mirroring** — searched. Read-side
   model-field lookup (this family) vs flavor dispatch
   (`convert_with_mro` + prechecks, R1); mutations model-input
   triple (total classifier, no registry walk); orders leaf
   annotation (single-kind mapping); filter form-field ladder
   (fallback typing where no model field backs the filter).
   Instrument: full reads of every converter pair + the AST
   census below.
2. **Sync/async twins** — inapplicable by construction. The rule
   is construction-time class dispatch (type build) plus a
   cold-path CLI renderer; zero `async` / `await` tokens in
   either family file (grep census empty), zero ORM access.
3. **Derived rather than repeated knowledge** — searched: this
   IS the family. The firing-row derivation is spelled 3× at
   HEAD, 2× in the worktree (F1).
4. **Inverse / round-trip pairs** — searched, none owed. The
   lookup is one-way; the CLI predictor is a projection of the
   dispatch, not an inverse definition.
5. **Contracts restated in another medium** — searched. First-match
   prose in 3+ docstrings (projections, move with F1); oracles
   pin resolutions + names with independent literals; SDL
   carries enum names, never the walk. No second maintained
   spelling outside the finding.
6. **Enforcement by omission** — searched, no defect. The AST
   census enumerates all 9 executable MRO reads; each
   non-member is excluded on a distinct question (R1–R5, R7)
   with a contract source or body-strength reason. No source
   requires any excluded scan to use the key lookup.

### Enumeration

Instrument: AST census over all 120 package `.py` files for
function bodies containing an MRO read (a `.mro(` call or an
`__mro__` attribute) — docstrings and comments excluded by
construction. Result: exactly 9 executable MRO reads, every one
homed (token grep `truth\.mro\(|__mro__` reports 21 lines / 11
files; the delta is prose + the truth slot alias, inventoried
out individually).

| # | Site | Home |
|---|---|---|
| 1 | [converters][converters]`::_class_map_lookup` (worktree) | F1 (value legs, via hunt dirt) |
| 2 | [converters][converters]`::scalar_for_field` (HEAD leg) | F1 |
| 3 | [converters][converters]`::_field_output_type_for` (HEAD leg) | F1 |
| 4 | [inspect][inspect]`::_matched_scalar_key` | F1 (predictor leg) |
| 5 | [utils-converters][utils-converters]`::convert_with_mro` walk | R1 (sibling, listed-not-counted) |
| 6 | `types/definition.py::origin_has_custom_id_resolver` | R2 (R14 family) |
| 7 | `types/base.py::_detect_custom_get_queryset` | R2 (R14 family) |
| 8 | `sets_mixins.py::collect_related_declarations` scan | R2 (R14 family) |
| 9 | `types/finalizer.py::_field_surface_names` walk | R3 |
| 10 | `types/relay.py::apply_interfaces` filter | R4 |
| 11 | `utils/querysets.py::_rhs_hook_defect` scan | R5 |

(`utils/truth.py` owns the read mechanism — R7. Rows 2–3 are the
HEAD spellings unified into row 1 by hunt dirt; all three states
fingerprinted under F1.)

### Challenges

Counts are AUTHORITATIVE definitions only, at both states (HEAD /
worktree). Consumers, oracles, projections that also move are
listed, never counted.

| Id | Change posited | HEAD | WT | Home |
|---|---|---|---|---|
| C1 | Membership-test hardening (plain `in` → identity scan) | 3 | 1 remaining (predictor) | F1 |
| C2 | MRO-source hardening (`type(field).__mro__` → `truth.mro`) | 3 | 0 remaining (moved in 3 hunks) | F1 (count proof) |
| C3 | Firing-row rule change (first-match → other) | 3 | 2 | F1 |
| C4 | Snapshot mechanics (`tuple(items)` → `dict` copy) | — | 1 (helper only) | F1 migration constraint |
| S1 | Fallthrough posture change (raise / `None` / fallback name) | 0 co-moves | 0 co-moves | R8 split proof |
| S2 | Add/remove a `SCALAR_MAP` row | 0 walks move | 0 walks move | F-SCALARMAP split proof |

C1 is execution-verified live divergence, not a hypothetical: the
hunt fired it on the two value legs and not on the predictor, so a
hostile-metaclass field splits them today (TypeError through the
predictor's `in` vs ConfigurationError through the identity scan;
control agrees — run `dry-20261001T175424-713d24`). The wrong
result this rejects: "the predictor spells the same rule as the
value legs" — no input could split one definition. C2 already
fired across three separate hunks (two files), which is itself
the count-3 evidence at change time. C3 is the standing
misattribution argument: the predictor exists BY CONSTRUCTION to
name the row the dispatch fired (its docstring says so), so any
firing-rule change moves both or the converter column lies. C4
moves only the helper (the skeleton already snapshots via
`dict`, the predictor holds no snapshot), proving the skeleton
is not a co-moving member. S1/S2 are the split proofs: miss
postures stay per site (standing per-subject direction), table
rows are data.

## Findings

### F1 — the MRO-map key lookup (CONFIRMED, blocked-on-hunt)

- **Contract + variation.** The first class in the field's real
  MRO keying a model-field class map, or absence. Varies as the
  lookup only: MRO source, scan order, membership test,
  snapshot. The three miss postures (raise / `None` / fallback
  name) and the two maps' rows are not lookup facets (S1/S2).
- **Sites + roles.** *Definitions:* HEAD 3 (`scalar_for_field`
  :365-367, `_field_output_type_for` :517-519,
  `_matched_scalar_key` :503-505 — all plain `type(field).__mro__
  + in`); worktree 2 (`_class_map_lookup` :346-361 serving both
  value legs, `_matched_scalar_key` :500-503 still spelling its
  own `truth.mro + in` walk). *Consumers:* 5 + 4 + 1 call sites
  (System trace). *Oracles:* the 9 firing-row nodes (System
  trace). *Projections:* first-match docstrings in both files.
- **Challenges.** C1 3→1-remaining (divergence
  execution-verified); C2 3→0 (three-hunk proof); C3 3→2. Every
  count > 1.
- **Owner + lifetime.** [converters][converters], via one key
  lookup both maps and the CLI compose — principle 7: it owns
  both key spaces (`SCALAR_MAP`, `FIELD_OUTPUT_TYPE_MAP`) and,
  at worktree, the value-lookup helper; the CLI already imports
  from it, so no dependency reverses; it is the narrowest
  cohesive module every legitimate consumer can import (no
  consumer outside these two files needs the lookup). The
  [utils-converters][utils-converters] alternative is rejected:
  it owns flavor dispatch over disjoint key spaces
  (forms/DRF fields), and its walk is phase 2 of preemptible
  dispatch (R1) — hosting the model-field lookup there moves
  the rule away from its maps for zero change-obligation
  relief. Pure lookup; no stored derivation (the per-call
  snapshot dies on return).
- **Migration (specified for the unblock item).** (1) One key
  lookup at the owner returning the `(key, value)` pair or
  `None` — the pair, not the key alone, because subscripting
  the map after an identity scan would re-dispatch `__hash__`,
  the exact dispatch the hardening removes; snapshot via
  `dict` copy (the skeleton posture, C4); no fallthrough
  verdict inside. (2) `scalar_for_field`: pair-or-raise, the
  message byte-identical (oracle-pinned). (3)
  `_field_output_type_for`: pair-value-or-`None`. (4)
  `_matched_scalar_key`: compose the owner by name
  (`truth.name(key)` or the concrete fallback) — deletes the
  last plain-`in` walk and closes the divergence. (5) Retire
  `_class_map_lookup` / `_MISSING` if subsumed (else one thin
  alias; constraint: exactly one walk body). (6) Land the
  census gate + 3 composition assertions; failability via
  [prove_failability][prove]. (7) Record this home clause, the
  R-home clauses, and the RJkeywalk supersession at the owner.
- **Distinct behavior.** Miss postures stay per site (R8); the
  `FILESYSTEM_PATH_OUTPUT_TYPE_MAP` subscript stays a direct
  read (R6); the skeleton keeps its prechecks + factory (R1).
  The hunt owns hostile-hardening decisions: if it accepts the
  cold-path risk on the predictor, C1's axis narrows but C2+C3
  still span both bodies.
- **Behavioral proof.** Divergence `execution-verified` (run
  `dry-20261001T175412-d2b4bf` is the 9/9 oracle baseline;
  run `dry-20261001T175424-713d24` is DIVERGED +
  CONTROL-AGREES — rejects "one definition"). Post-migration
  equivalence `execution-deferred` → the `proof:` entry under
  `## Pending execution` (same 9 nodes re-run by the unblock
  item; behavior-preserving per principle 8: same values,
  same miss verdicts, same raise sites, hostile input takes
  the typed path on both halves).
- **Structural gate (specified, unapplied).** AST census over
  the two family files: exactly one MRO-reading def (the
  owner), plus `calls-the-owner` composition assertions on
  `scalar_for_field`, `_field_output_type_for`, and
  `_matched_scalar_key`. Negative-control direction
  `execution-verified` read-only: `/tmp/mromap_census.py`
  reports exactly the 2 live walk bodies, 3 with the
  never-imported `/tmp/mromap_synthetic.py` hand copy
  (`CENSUS-DISCRIMINATES` both ways — a hand copy passes
  every behavior oracle yet moves the count). The gate is
  born red today (count 2, not 1), so it stays specified;
  landed-gate failability via [prove_failability][prove] is
  owed by the unblock item.
- **Coupling.** BLOCKED-ON-HUNT: every touch line is hunt
  dirt. In [converters][converters] the owner reshape edits
  the helper-intro hunk (`_Missing` / `_MISSING` / `_V` /
  `_class_map_lookup` + `Mapping` / `Final` / `Literal` /
  `truth` imports) and both leg-rewrite hunks
  (`scalar_for_field`, `_field_output_type_for`); in
  [inspect][inspect] the CLI composition rewrites the
  `_matched_scalar_key` return hunk (`truth.mro` /
  `truth.name`) and rides the hunt's `truth` import. No
  `## Owned changes` row covers `converters.py` at all; the
  inspect adopted-orphan row covers only a docstring citation
  fix beside a REVERTED consumer half (run-3 note) — the
  walk-line dirt matches the hunt's truth-migration
  (`truth.*` reads + `except BaseException` deletions +
  untracked `utils/truth.py`), not the ledger. Prior
  rejection RJkeywalk (File `inspect_django_type`) is
  SUPERSEDED by this confirmation: its trigger (a
  `key_for_field`-style entry point beside `scalar_for_field`)
  is exactly the specified owner, engaged here and landing
  with the unblock.
- **Freshness.** HEAD `dd0b6691`; ITEM_BASELINE `cf0791c6`
  (commit). Worktree vs HEAD blob ids (`git hash-object` vs
  `git rev-parse HEAD:path`): [converters][converters]
  `97f3399e…` / `312bd290…`; [inspect][inspect] `2e1223dc…` /
  `034dd692…`; [utils-converters][utils-converters]
  `55e056d4…` / `9eae7cbb…`; `types/base.py` `e7a62d32…` /
  `e0ad32aa…`; `types/definition.py` `e79d7129…` /
  `ff80ef02…`; `types/relay.py` `a9b90a17…` / `a200f190…`;
  `types/finalizer.py` `09f3e327…` / `724a9421…`;
  `sets_mixins.py` `c496feb2…` / `42e8c862…`;
  `utils/querysets.py` `6d471bd7…` / `adc74b64…`;
  `filters/inputs.py` `993f365c…` / `08516597…`;
  `mutations/inputs.py` `fe2218dd…` / `fd0f17d8…`;
  `serializer_converter.py` `a22dcbe3…` / `469a4959…`;
  `forms/converter.py` `52b10986…` / `a70fe126…`;
  `types/resolvers.py` `b37b85d6…` / `2c588030…`; oracles
  `tests/types/test_converters.py` `ddf24f59…` /
  `c2ff9fca…`, `tests/management/test_inspect_django_type.py`
  `a91b1e92…` / `9b1360d0…`, `tests/utils/test_converters.py`
  `447fa2c5…` CLEAN. Shared tree unmoved across all workspace
  runs. Gates in the workspace copy: `basedpyright` 0 errors /
  0 warnings / 0 notes (run `dry-20261001T175357-c150da`);
  `check_any.py` 128 uses at 89 sites, exit 0 (run
  `dry-20261001T175407-d551ee`); `check_truthful_reads.py
  --check` 119 files, tier-1 0, errors 0 (run
  `dry-20261001T175407-8913d4`). Zero tracked edits, so no
  new cast / `Any` / suppression exists to judge; ruff
  vacuous (no `.py` touched). `--cell sharded/pg`
  inapplicable by construction (construction-time class
  dispatch + cold-path CLI rendering; no queryset, alias, or
  dialect decision reachable) — Worker-2 judges.

### R1 — skeleton walk leg (excluded sibling, listed-not-counted)

[utils-converters][utils-converters]`::convert_with_mro` :143-146
walks the MRO against a caller-supplied registry with an identity
scan — the hardened posture F1 converges toward. Contract
difference: F1 is a pure lookup (first keying class or absence,
caller-owned miss posture); the skeleton's walk is phase 2 of
preemptible flavor dispatch (ordered `isinstance` prechecks can
shadow any registry hit, the registry is per-call caller data over
disjoint forms/DRF key spaces, a miss raises through a caller
factory). C4 moves only F1's helper; C7-style firing changes move
only F1's legs. CONVERGE with the standing FAM-MRO verdict and
the File `utils/converters.py` converge record on fresh bodies
(re-read at both states). Trigger: a non-dispatch rider needing
a bare model-field key lookup that cannot import
[converters][converters] (then the ownership decision reopens;
mere mechanical similarity never fires it). Durable home
(specified for the unblock item): one clause on
`convert_with_mro`'s phase-2 comment.

### R2 — override / declaration namespace scans (rejected)

`types/definition.py::origin_has_custom_id_resolver` :374,
`types/base.py::_detect_custom_get_queryset` :944-949,
`sets_mixins.py::collect_related_declarations` :352-359. Contract
difference: each asks whether a NAME occurs in some class
namespace along the MRO (resolver override? `get_queryset`
override before `DjangoType`? inherited declaration?) — three
different questions over three different MROs, none of them "which
class keys a map". CONVERGE with verified R14 on fresh bodies
(re-read at worktree; the standing R14 trigger — an owned
bare-MRO helper — stays unfired: F1's owner is a key lookup, not
a namespace predicate). Trigger: the standing R14 trigger.
Durable home: existing R14 clauses (no new prose).

### R3 — finalizer surface walk (rejected)

`types/finalizer.py::_field_surface_names` :222 walks
`reversed(truth.mro(type_cls)[1:])` collecting inherited
Strawberry fields per base. Contract difference: attribute
collection across bases in reverse-MRO order (later bases
overwrite), not a first-match key lookup; no map, no firing row.
Trigger: the surface builder needing a firing-row decision over
a class map. Durable home (specified): the function's docstring
already states the three-source collection; no new clause —
this row is the record.

### R4 — relay interface filter (rejected)

`types/relay.py::apply_interfaces` :171-174 keeps interfaces not
already in the MRO. Contract difference: membership of interface
OBJECTS in the MRO tuple (injection guard), not MRO classes
keying a map; the MRO is the searched collection, not the
search key stream. Trigger: interface injection keying off a
class map. Durable home: existing docstring (injection guard);
this row is the record.

### R5 — seal-proof hook scan (rejected)

`utils/querysets.py::_rhs_hook_defect` :1228-1234 walks the MRO
checking hook names per class namespace, skipping trusted bases.
Contract difference: a fail-closed safety proof over namespaces
(trusted-base skip + hook verdict), never a map lookup; its
reasons to change are seal-posture changes, not dispatch
changes. Trigger: the seal proof deriving verdicts from a class
map. Durable home: existing docstring (proof posture); this row
is the record.

### R6 — path-map direct subscript (rejected)

[converters][converters] :569
`FILESYSTEM_PATH_OUTPUT_TYPE_MAP[output_type]`. Contract
difference: keyed on the already-resolved OUTPUT type, not on a
field class — deliberately not an MRO walk (its comment states
the anti-duplication rationale: re-keying on the field would
duplicate the walk and let the maps disagree). It is the
migration's model citizen, not a third leg. Trigger: the path
map re-keyed on field classes. Durable home: existing map
comment (no new prose).

### R7 — truth read mechanics (rejected)

`utils/truth.py::mro` (+ `_mro_lookup`, `_get_mro`). Contract
difference: the hostile-safe READ mechanism every scan above
rides, not a lookup definition — it answers no firing question
itself. Sharing it further is composition, already complete.
Trigger: none possible (mechanism, not rule). Durable home:
existing module docstring.

### R8 — fallthrough postures (rejected as lookup facets)

Raise-with-message / `None` / concrete-name-fallback. Contract
difference: per-subject miss verdicts owned by the caller's
contract (conversion must fail loud; output probing must stay
optional; the CLI column must always print), not facets of the
lookup — S1 moves none together. CONVERGE with the standing
per-subject direction. Trigger: two sites adopting one shared
miss verdict for one reason. Durable home (specified for the
unblock item): the owner's docstring names the postures as
caller-owned.

No new responsibility-index rows are owed: R1 converges on the
standing converge record, R2/R8 on verified standing verdicts,
R3–R7 are exclusions whose homes already exist or are specified
above. Worker-0 transcribes nothing except F1's confirmation +
blocked coupling and the RJkeywalk supersession.

## Defects

None. The hostile-input divergence is F1's own duplication
evidence and closes with the specified migration; it is not
homed separately. The hunt owns hostile-hardening posture (F1
notes the cold-path caveat).

## Pending execution

- `proof: uv run python scripts/workspace.py run dry/mromap-f42/consolidate -- pytest tests/types/test_converters.py::test_convert_scalar_resolves_subclass_of_supported_field_to_parent_scalar tests/types/test_converters.py::test_convert_scalar_subclass_with_null_widens_through_mro_resolution tests/types/test_converters.py::test_convert_scalar_unknown_field_type_still_raises tests/types/test_converters.py::test_convert_scalar_duration_field_raises_unsupported tests/types/test_converters.py::test_convert_scalar_binary_field_raises_unsupported tests/types/test_converters.py::test_field_output_map_mro_precedence_image_subclass_wins tests/types/test_converters.py::test_consumer_imagefield_subclass_opts_in_to_the_image_sibling tests/types/test_converters.py::test_unsupported_field_message_names_the_field_class_and_label tests/management/test_inspect_django_type.py::test_matched_scalar_key_names_supported_mro_ancestor -n0 --no-cov -q`
  — re-discharges F1 behavioral equivalence when the unblock
  item lands the migration (validated runnable 9/9 at baseline,
  run `dry-20261001T175412-d2b4bf`).

## Judgment

CONFIRM-blocked. The MRO-map key lookup is one rule with three
HEAD definitions and — after the hunt's partial unification —
two worktree definitions that observably disagree on
hostile-metaclass input (execution-verified split) while
agreeing on the control. Owner re-derived as
[converters][converters] (both key spaces + existing CLI
dependency; utils alternative rejected on responsibility).
Migration, census gate with an execution-verified
negative-control direction, all 8 rejections with triggers +
homes, and the deferred equivalence proof are specified; zero
tracked edits were made because every touch line is hunt dirt;
nothing was touched.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converters]: ../../django_strawberry_framework/types/converters.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[prove]: ../../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

### Own trace (pre-Findings)

Recorded before opening `## Findings`. Sources: `git show
HEAD:django_strawberry_framework/types/converters.py`,
`git show
HEAD:django_strawberry_framework/management/commands/inspect_django_type.py`,
WT bytes of both, `git diff HEAD` on both paths, the ledger
(`## Owned changes`), the RJkeywalk record in
`dry-file-management__commands__inspect_django_type.md`, and a
whole-package `__mro__` / `truth.mro` / `_get_mro` grep. HEAD
`dd0b6691` unmoved; WT pins `97f3399e` / `2e1223dc` match
dispatch.

HEAD (three definitions, each `type(field).__mro__` + `in`):

- D1 `types/converters.py::scalar_for_field` — DEFINITION
  (value leg, scalar): walks the MRO against `SCALAR_MAP`,
  returns the scalar; miss raises `ConfigurationError`.
- D2 `types/converters.py::_field_output_type_for` —
  DEFINITION (value leg, output): same shape against
  `FIELD_OUTPUT_TYPE_MAP`; miss returns `None`.
- D3 `management/commands/inspect_django_type.py::_matched_scalar_key`
  — DEFINITION (key leg / predictor): names the matched
  `SCALAR_MAP` ancestor; miss falls back to the concrete
  class name.

WT (two definitions):

- D1+D2 now compose `_class_map_lookup(mapping, field)` by
  name: `truth.mro(truth.class_of(field))` with an
  identity-scan membership test (`key is klass`) and a
  `_MISSING` sentinel. One remaining definition for both
  value legs.
- D3 keeps its own walk: `truth.mro(type(field))` with a
  hash/`__eq__` membership test (`klass in SCALAR_MAP`).
  Second remaining definition.
- Count: 3-at-HEAD / 2-in-WT.

Consumers (all by name, none a second definition):
`convert_scalar` → D1; `convert_field_output` → D2;
`filters/inputs._scalar_from_model_field`, `mutations/inputs`,
`serializer_converter` (two sites) → D1;
`types/resolvers._attach_file_resolvers`, `types/base.py`
(filesystem-path gate), `inspect._scalar_row` → D2;
`inspect._scalar_row` → D3 for the converter label.

Challenges (my own three axes):

- C1 match semantics (first-match → longest-match, or
  identity → equality): HEAD 3 move; WT 2 move.
- C2 walk span / MRO subject (skip `object`, start from
  bases): HEAD 3 move; WT 2 move (each body spells its
  own `truth.mro(...)` call).
- C3 miss posture (raise vs `None` vs concrete-name
  fallback): each leg moves alone (count 1) — the
  independence axis; consolidation must preserve all three
  postures, not merge them.

Owner I would choose: `types/converters.py` via one
`(key, value)`-pair lookup over a caller-supplied mapping,
with three thin composers (scalar: value-or-raise; output:
value-or-`None`; predictor: key-name-or-concrete-fallback).
Both key spaces live there; every consumer already depends
on it (no reversal); the `utils/converters.py::convert_with_mro`
alternative bundles `isinstance` prechecks plus a raising
fallthrough neither output leg (returns `None`) nor
predictor (never raises) shares — reuse would need mode
flags or dead parameters, so it stays an excluded sibling.
Whole-package sweep: the remaining `truth.mro` / `_get_mro`
sites (finalizer base walk, relay interface filter,
definition origin walk, `types/base.py` scan, querysets
walk, sets_mixins scan, truth internals) are namespace /
interface / read-mechanics walks, none a class → map-entry
lookup over the converters maps.

### Reconciliation (post-Findings)

Every difference between my trace and the artifact, decided
explicitly. Verdict: VERIFIED — the plan item reads
`verified, pending execution` (one `proof:` entry remains).

- Counts, sites, roles: full agreement. 3-at-HEAD /
  2-in-WT re-derived by me at `git show HEAD:` + WT bytes;
  consumers 5 + 4 + 1 re-derived identical; owner
  independently chosen as [converters][converters] via a
  `(key, value)`-pair lookup with the utils-skeleton
  rejection on the same grounds (prechecks + raising
  fallthrough neither output leg nor predictor shares).
- Challenges: W1's C1 (3→1-remaining) / C2 (3→0
  three-hunk proof) frame counts as remaining-to-move
  after the hunt partially fired each change; mine counted
  future co-move (3/2). Same underlying facts, W1's frame
  is sharper given the partial unification — adopted.
  C4/S1/S2 add genuine information (snapshot constraint,
  posture + data split proofs). No disagreement.
- (a) Divergence-as-evidence-not-defect: AGREE, correct.
  The split is between the two remaining definitions of
  one confirmed rule — it IS C1's evidence and closes
  with migration step 4; homing it separately would
  double-count, and hostile-hardening posture belongs to
  the hunt. Reproduced fresh by me in two shapes
  (`/tmp/w2_mromap_divergence.py`: mapped hostile →
  TypeError-vs-`str`; `divergence2`: unmapped hostile →
  TypeError-vs-ConfigurationError) with control agreeing
  on all three legs. No (Worker-2) defect.
- (b) RJkeywalk supersession: AGREE, substantively
  correct. The fresh trace (execution-verified C1 split +
  C3 misattribution argument from the predictor's own
  docstring) overturns "shared iteration shape, not a
  shared rule"; the trigger (a `key_for_field`-style
  entry beside `scalar_for_field`) is exactly the
  specified owner, and "engaged here and landing with
  the unblock" honestly records the deferral.
  Record-by-reference in this artifact + the explicit
  Worker-0 transcription note is the correct update path
  (the family item does not edit the file artifact).
- (c) 9-vs-11 accounting: EXACT and unambiguous. My
  independent AST census over all 120 package files
  reproduces exactly 9 executable MRO reads
  (`/tmp/w2_mro_census.py`): rows 1 + 4–11 live at WT,
  rows 2–3 the HEAD-only spellings unified into row 1.
  Token grep `truth\.mro\(|__mro__` reproduced at 21
  lines / 11 files; the 12-line delta is 11 prose lines
  + the truth slot alias, each identified. All six
  census-row enclosures (R2–R5 sites) verified by line.
- Enumeration member-by-member: all 11 rows homed
  correctly; R1–R5 bodies read by me confirm each
  stated contract difference; the only executable
  out-of-module map read is the predictor's walk line
  (remainder is prose or the unrelated package scalar
  map).
- Zero-edit: item diff vs ITEM_BASELINE is the plan
  edit alone (1 file, 54 insertions); only new file is
  this untracked artifact; the 3 untracked package
  `.py` files are pre-attributed (f39 ledger +
  briefed hunt concurrent). No oracle rewritten; the 9
  `proof:` nodes exist (1 each), assert independent
  literals, and re-ran 9/9 green by me read-only
  (`-n0 --no-cov`).
- Blocked-on-hunt: AGREE. Re-derived from `git diff
  HEAD` content: helper-intro + both leg rewrites in
  converters, predictor return hunk + `truth` import in
  inspect — all hunt truth-migration dirt. No ledger
  row covers converters.py (verified); the inspect
  adopted-orphan/run-3 row covers only the docstring
  citation fix beside the REVERTED half, which does not
  constrain the walk-line attribution (content matches
  the hunt, not the ledger). Zero legal partial
  landings: a pure-additive owner without leg rewrites
  adds a third walk body with zero composers (dead code
  per principle 11).
- Migration sound on principle-8 axes: pair-return
  avoids re-dispatching `__hash__`; `None` is a safe
  miss signal for both maps; raise site stays in
  `scalar_for_field`; miss postures stay per site.
- Structural gate: negative-control direction
  reproduced by me (`/tmp/mromap_census.py`: 2 live, 3
  with the never-imported synthetic, DISCRIMINATES both
  ways). Born red today (count 2), correctly specified
  not landed.
- R1–R8: each carries contract difference + trigger +
  home; converge claims verified against the standing
  records (FAM-MRO naming + File utils/converters
  converge record re-read; R14 three-questions +
  unfired trigger re-read; f14 per-subject direction).
  R7's "trigger: none possible" is a reasoned
  mechanism-exclusion — verdict-neutral softness.
- Pending execution: correctly typed `proof:`
  (workspace-copy command discharging F1 equivalence);
  no `gate:` entries owed. Coupling marked.
- Matrix: all six axes discharged against the real
  surface; axis 2 verified (zero async/await tokens in
  both family files). Axis-4 "projection" wording is
  loose (the predictor is a DEFINITION of the key rule
  per C3, a projection only in the non-inverse sense)
  — verdict-neutral note.
- AGENTS.md prose: reference-style links with the full
  10-group block; `path::Symbol` + bare `:NN` (allowed
  in `docs/dry/dry-*.md`); no process provenance;
  banned words N/A (zero new test/production files).
- Gates re-run by me in the shared tree: basedpyright
  0/0/0; check_any 128 uses at 89 sites; truthful-reads
  119 files, tier-1 0, errors 0 — all match the run-11
  baseline and W1's workspace figures. mypy never run,
  never cited. Ruff passes on both family paths (the
  item touches zero `.py`, vacuous as an item gate).
- Sharded/PG inapplicable-by-construction: AGREE
  (construction-time class dispatch + cold-path CLI
  rendering; no queryset, alias, or dialect decision —
  my probes ran DB-free).

Defects: none. W1's zero-defect claim stands; no
(Worker-2) entry owed. Worker-0 transcribes F1's
confirmation + blocked coupling + the RJkeywalk
supersession; nothing else.
