# DRY review: `registered-djangotype-definition-validation`

Status: verified
Run: 0.0.15 2026-10-01-11

Family `registered-djangotype-definition-validation`. CONFIRMED count-2,
blocked-on-hunt, zero edits. The two proof sites re-derived fresh at current
worktree bytes: [testing-relay][testing-relay]`::global_id_for` (step-1a
proof block) and [list-field][list-field]`::_validate_djangotype_target`
(identity core). Owner decided by principle 7:
[registry][registry]`::registered_own_definition` (to create) — not
inherited from either index-row candidate sketch. Prior records used as
orientation only: the verified [relay-node-target-guard][guard] family
(reconciled below, never adopted) and the
[testing-relay file item][file-relay] F1 (re-derived body by body at WT
bytes; its HEAD-pinned C3 divergence has since closed under concurrent
work). Never read any `worker-memory/`.

Attribution: `ITEM_BASELINE`
`d3d51c9e1151a2ce1de36a47c9c79a91570ff71b` verified present
(`git cat-file -t` → `commit`). HEAD `dd0b6691`. Dispatch pins verified
digit-for-digit: `testing/relay.py` WT `572f8d64…` / HEAD `76de954f…`,
`list_field.py` WT `b534ea32…` / HEAD `3842542a…`. `testing/relay.py`
carries no `## Owned changes` row and no cycle-baseline entry: all three
of its WT hunks are concurrent truth-migration work. `list_field.py`'s
`@@ -245,10 +221,17 @@` hunk is MIXED — the ledgered
`relay-node-target-guard` trigger paragraph (adopted orphan, attributed by
content) inside a concurrent comment-reword hunk — and every other hunk on
the path is unattributed. `registry.py`'s
`@@ -499,13 +526,17 @@` hunk is MIXED — the ledgered
`relay-node-name-decode` single-inverse trigger paragraph (adopted
orphan, attributed by content; absent at HEAD per
`git show HEAD:`) inside a concurrent prose-reword hunk — and the other
15 hunks are unattributed truth migration. Every path the consolidation
would touch carries an unattributed hunk: the item stops per the dispatch
rule, nothing was edited, nothing was reverted.

## System trace

Rule: a consumer-presented object counts as a usable `DjangoType` class
only when it is a `DjangoType` subclass carrying the registry's OWN
definition for that exact class — the attribute definition is identical
to `registry.get_definition(type_cls)` AND its `origin` is the class
itself. Inherited definitions (unregistered child), stale definitions
(post-`clear()` / post-`unregister`), copies, and fabricated lookalikes
are rejected; hostile inputs fail closed into the same typed
`ConfigurationError`.

What each site proves, re-derived from its WT body:

- **Testing mint guard** (`testing/relay.py::global_id_for`, WT :67–86):
  `truth.is_subclass` gate, then `truth.static_attr` read +
  `registry.get_definition` + the triple conjunction
  (`canonical is not None and definition is canonical and
  canonical.origin is type_cls`), fused into one boolean and one fused
  `ConfigurationError`. Keeps the proven definition in a local for the
  finalized gate + stamp read below.
- **Field-factory base**
  (`list_field.py::_validate_djangotype_target`, WT :182–200):
  `truth.is_type` / `truth.is_subclass` pre-gates with per-arm messages,
  then the same `truth.static_attr` read + `registry.get_definition` +
  the same triple as a disjunction
  (`canonical is None or definition is not canonical or
  canonical.origin is not target_type`), one factory-interpolated
  `ConfigurationError`, the factory-only resolver-callability seam,
  returns the canonical definition onward.
- **Writer** (`types/base.py::DjangoType.__init_subclass__`, WT :887–891):
  `register_with_definition` + attribute assignment from one value — the
  pair the proof verifies. Definition source, not a proof site.
- **Consumers of the base**: `relay.py::_validate_node_target` (thin
  wrapper, WT :469–486, passes `None` + label + message) and
  `connection.py::DjangoConnectionField` (WT :2431–2439, passes resolver
  + label + message), both via
  `_validate_relay_djangotype_target`. Verified by reading: neither
  re-spells a proof arm.
- **Oracles**: `tests/testing/test_relay.py` (10 nodes incl. the
  inherited/stale oracle + the fused-message pin) and the 13 list-field
  guard nodes (non-class / non-subclass / without-definition /
  without-own-meta / non-callable-resolver / fabricated / copy /
  never-seen / acceptance-identity / read-once). All independent: hostile
  inputs driven, literal messages spelled, never reading a proof arm.
  Both oracle files are hunt-dirty at WT; judged as-run-green, never
  edited.

Connected sources read at WT bytes: `registry.py` (full:
`get_definition`, `definition_for_graphql_name`,
`register_with_definition`, `IdentityMap` trade),
`relay.py::_check_typed_match` + `_stamp_node_type` + `_validate_node_target`,
`connection.py` call site + `_connection_type_for` provenance check,
`mutations/fields.py::_validate_mutation_target` (duck-typed protocol
per spec-038 Decision 5), `inspect_django_type.py` CLI check (WT
:157–171), `types/base.py` writer + `has_custom_get_queryset` tolerant
branch, `types/definition.py::related_target_for`,
`types/resolvers.py` + `types/relay.py` + optimizer registry reads,
`types/finalizer.py` relation-target audits,
`utils/querysets.py::model_for` hot-path read,
`utils/truth.py` (`is_type`, `is_subclass`, `static_attr`, `render`,
`name` — untracked concurrent work, read-only). Excluded on strength of
body: every other package module (zero proof vocabulary in the
mechanism sweep below).

Reconciliation with verified `relay-node-target-guard`: that family owns
the Relay-shaped SUPERSET guard (still single-owned — this item changes
nothing there) and never names the testing helper (grep `testing` over
its artifact: 0). Its F1-C2 count-1 ("registration-canonicality change
→ 1, the base validator") rested on a census missing this file. The
T-canonical trigger it recorded contemplated exactly a canonicality
question and pointed at the base; re-derived with the full population,
the pointer moves one level down to the registry predicate, with the
base validator becoming a composing consumer. Specified as a docstring
repoint at landing, below. Not a defect: no contract row broken, a
census-completeness note.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Field flavor (list / connection /
   node factories via the base) and testing flavor (mint guard) share
   the rule — the family. Mutation flavor (`_validate_mutation_target`)
   is duck-typed protocol + ledger by spec decision (R6). CLI flavor
   checks subclass + attribute presence without canonicality (R3).
   Trigger: a third flavor co-locating the attribute + registry +
   origin arms.
2. **Sync/async twins.** Inapplicable with reason: both proof bodies are
   sync-only pure validation (registry map read + identity
   comparisons); neither body names `async` / `await` / a boundary
   runner. No twin exists, none owed.
3. **Derived rather than repeated knowledge.** The readers are
   single-owned at `utils/truth.py` (`is_subclass`, `static_attr`,
   `render`, `name`) — both sites compose them by name at WT. What is
   still spelled twice is the proof COMPOSITION: which three reads
   co-locate and what verdict they jointly produce. Deriving each read
   from the shared reader does not single-source their conjunction.
4. **Inverse / round-trip pairs.** Proof (class → verdict at pre-use)
   vs decode (wire string → type at runtime) are opposite directions of
   one lifecycle, owned separately (this family vs the decode families).
   Converge with `relay-node-target-guard` Matrix-4; no new pair found.
5. **Contracts restated in another medium.** Production (2 definitions);
   oracles (independent literals, 23 nodes green); projections
   (docstrings read against bodies — the base docstring's "cannot mean
   different things to the list, connection and Relay node entry points"
   enumerates three consumers while a fourth meaning-site exists; the
   invariant still holds — all four agree — so this is an incomplete
   enumeration, not a contradiction; fixed by the migration's sentence
   update, not filed as a defect).
6. **Enforcement by omission.** Proof-shaped population enumerated by
   the sweep: the 2 members guard; the inspect CLI lacks the
   canonicality arm by contract (R3); registry-only readers lack the
   attribute arm by contract (R5); message/tolerant readers never take a
   verdict (R1/R2/R4). No contract source extends the proof to any of
   them. No member lacks a guard its contract requires: no defect.

### Enumeration

Instrument: whole-package word-boundary sweep for `get_definition`
(`grep -rnw`, 19 lines: 16 calls + 1 def + 2 docstring mentions;
raw-substring `grep -rn` is 67 WT / 68 HEAD, the balance 48
`*target_definition*` noise lines),
`__django_strawberry_definition__` (17 hits), plus the regex census for
`origin is (not )?(target_type|type_cls)` + `definition is (not
)?canonical` + `is not a registered DjangoType` (`grep -rnE`, 9 hits).
Population: 119 package files per the truthful-reads gate census.

- Triple co-location (attribute read + registry read + origin
  identity): exactly **2** executable sites — `testing/relay.py:77`,
  `list_field.py:192`. All other regex hits are comments (:118, :236,
  `connection.py:2440`, `list_field.py:1566`) or messages without the
  check (`inspect_django_type.py:167,199`, `list_field.py:194`).
- `__django_strawberry_definition__` readers that are NOT proofs (each
  verified by body): the writer (`types/base.py:891`), the CLI check
  (`inspect_django_type.py:163`, no registry arm), the tolerant model
  read (`relay.py:580`, no verdict), the tolerant branch
  (`types/base.py:929`, no registry arm), the message reads
  (`relay.py:233–234`, post-validation), the hot-path model read
  (`utils/querysets.py:277`, assumes registered).
- `get_definition` readers that are NOT proofs: finalizer audits (4
  call shapes, finalize phase over discovered relations),
  `types/resolvers.py:412,450`, `types/relay.py:956`,
  `types/definition.py:329`, optimizer reads (4 shapes), connection
  cache provenance (cache-entry identity, not registry proof).
- No `registered_own_definition` predicate exists anywhere in source
  (only the local boolean in `testing/relay.py`).

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Accept inherited definitions (drop the own-origin arm) | **2** (list triple + testing triple; oracles: inherited-child rows both sides fail) |
| C2 | Drop the registry-identity arm (trust attribute + origin) | **2** (same pair; fabricated / copy / stale oracles fail) |
| C3 | Change the class/subclass gate (admit non-type probes, or move the hostile-metaclass posture) | **2** compositions (list's two message arms + testing's fused branch; readers 0 — single-owned at `truth.py`) |
| C4 | Reword one rejection message | **1** per subject (rejected consolidation — per-subject grammars; riders only) |

C3 note: at HEAD the two sites additionally diverged on containment
shape (`try/except BaseException` over the whole proof vs
`try/except Exception` around the read only). At WT both delegate to
the truth readers — converged by concurrent migration, not by this
item. The gate COMPOSITION (where the check happens, what message it
feeds) is still spelled twice, which is what C3 counts.

## Findings

### F1 — registered-own-definition proof (CONFIRMED count-2, blocked-on-hunt)

- **Contract + variation.** A probe counts as a usable `DjangoType`
  class iff it is a `DjangoType` subclass whose attribute definition
  `is` the registry's definition for it and whose `origin is` the
  probe. Varies on: proof arms (subclass / attribute / registry /
  origin), gate composition vs message split, return-vs-local
  adaptation. Messages vary per subject (R7, not part of the rule).
- **Sites + roles.** *Definitions (2)*: `testing/relay.py::global_id_for`
  step-1a block (WT :67–86), `list_field.py::_validate_djangotype_target`
  identity core (WT :182–197). *Writer*: `types/base.py` registration
  pair. *Consumers*: `_validate_node_target`, `DjangoConnectionField`
  (via the Relay validator), the testing helper's own finalized gate +
  stamp read below the proof. *Oracles*: 23 nodes, independent.
  *Projections*: both docstrings + the relay-node-target-guard T-canonical
  pointer (repoint specified).
- **Challenges.** C1 → 2; C2 → 2; C3 → 2; C4 → per-subject (rejected).
  The disproof attempt fails: same inputs (arbitrary object), same
  outputs (`ConfigurationError` vs proven definition), same timing
  (pre-use, sync), same hooks (none). Only messages, return-vs-local,
  and arm spelling differ — all parameterizable without mode flags.
- **Owner + lifetime (principles 7, 4).**
  `registry.py::registered_own_definition` (to create): the registry
  owns registration and canonicality — `register_with_definition`
  writes the pair the proof verifies, `get_definition` is the
  canonical read. Both consumers already import `registry` (zero new
  import edges); routing the testing helper through `list_field.py`
  would import sibling-flavor machinery against its import-light
  contract, and the base's factory messages + resolver seam are the
  wrong envelope for a mint guard. Dependency direction wins over the
  base-validator alternative. Pure per-call proof returning
  `DjangoTypeDefinition | None` (callers own messages); no stored
  derivation, no lifetime fields owed. `DjangoType` arrives via an
  in-function import (the `definition_for_graphql_name` cycle
  precedent — `types/base.py` imports `registry` at runtime).
- **Migration (specified, not applied — blocked).** One change when the
  block clears: (1) new predicate in `registry.py` with docstring
  clauses for the contract + R1–R8 triggers + the guard reconciliation;
  (2) base validator keeps its class/subclass message arms + resolver
  seam, replaces the attribute+registry+triple block with one owner
  call + its existing unregistered message, returns the definition;
  base docstring scope sentence gains the testing helper as fourth
  consumer; (3) testing helper replaces its proof block with one owner
  call + its existing fused message; (4) T-canonical pointer repointed
  base → predicate; (5) census gate + predicate unit rows land in
  `tests/test_registry.py` (package tier: construction rejection
  reaches no schema, same tier as the existing guard oracles);
  (6) failability manifest proving the census fails on a hand-copy
  mutant. No `ALLOWED_ANY` movement (no `Any` in the proof bodies; the
  `cast` sites dissolve into the typed return).
- **Distinct behavior (stays separate).** Per-subject messages (R7);
  the resolver-callability seam at the base (R8); the Relay-shape fifth
  guard (guard family); the finalized gate + stamp read (file-local
  F2 of the testing file item).
- **Behavioral proof.** Current agreement `execution-verified`
  (workspace run `dry-20261001T171754-54daac`, 23/23 green — rejects
  "the sites prove different facts" and "one site accepts what the
  other rejects"). Bodies + oracle independence `static-reviewed` at
  pinned WT blobs. Post-migration equivalence `execution-deferred`
  (no migration landed — blocked): the 23-node re-run is the `proof:`
  entry. Principle-8 coverage: same exception type, same per-site
  messages (untouched by the migration), same accepted object (the
  registry's identity, pinned by the acceptance oracle), same
  observation point (pre-use, no transaction / await / query effects).
  Cells: sharded + pg inapplicable by construction — the rule is
  construction-time validation over registry maps; it reaches no
  database, alias, or dialect decision (oracles construct classes only,
  issue no queries). Worker-2 judges.
- **Structural gate (specified, not landed — blocked).** AST census
  over the package: exactly one function body co-locates (a) an
  attribute read of `__django_strawberry_definition__`, (b) a
  `registry.get_definition` call, (c) an origin-identity comparison —
  and that body is the predicate; both consumers reference the owner
  by name. Negative control: a behavior-preserving hand copy of the
  predicate body at one consumer passes all 23 behavior oracles and
  fails ONLY the census — proving the census, not the behavior pins,
  guards the single-sourcing. Failability via `prove_failability.py`
  at landing (deferred — no gate landed while blocked; a singularity
  gate born red is a defect, not a gate).
- **Coupling.** The six migration steps land together (one rule);
  blocked on the hunt's truth migration + the maintainer
  `except-BaseException` deletions settling on all three paths.
- **Freshness.** WT `git hash-object` / HEAD `git rev-parse HEAD:path`:
  `testing/relay.py` `572f8d64…` / `76de954f…`,
  `list_field.py` `b534ea32…` / `3842542a…`,
  `registry.py` `e95c39e7…` / `5480c2eb…`,
  `relay.py` `63bbba0b…` / `037723cd…`,
  `connection.py` `6c4b01f9…` / `38491372…`,
  `mutations/fields.py` `3368f696…` / `0fada991…`,
  `inspect_django_type.py` `2e1223dc…` / `034dd692…`,
  `types/base.py` `e7a62d32…` / `e0ad32aa…`,
  `types/definition.py` `e79d7129…` / `ff80ef02…`,
  `types/resolvers.py` `b37b85d6…` / `2c588030…`,
  `types/relay.py` `a9b90a17…` / `a200f190…`,
  `types/finalizer.py` `09f3e327…` / `724a9421…`,
  `optimizer/extension.py` `8e3fe7c1…` / `b7b6c434…`,
  `optimizer/walker.py` `b71db9e0…` / `57a27b4a…`,
  `utils/querysets.py` `6d471bd7…` / `adc74b64…`,
  `tests/testing/test_relay.py` `4e61e8f1…` / `55e43ed2…`,
  `tests/test_list_field.py` `5b4e5339…` / `09d93c61…`,
  `utils/truth.py` `711352b1…` / absent at HEAD (verified:
  `git rev-parse` fails; untracked concurrent work). Orientation-only:
  guard artifact `5f4b74f3…`, file artifact `5c08128b…` (both
  untracked, absent at HEAD). Searched population: 119 package files
  for the mechanism tokens above. Any fingerprint change reopens.
- **Reconsideration triggers (specified for the owner clause).**
  T-proof: a third site co-locating the three arms, or a proof-arm
  change (inherited acceptance, identity weakening) — the predicate
  owns it. T-envelope: a consumer needing a verdict richer than
  definition-or-`None` — messages stay per subject, the predicate
  stays pure. T-lifecycle: a guard reading row-existence or
  finalize-phase state — construction answers registered-only.
- **Blocked-on-hunt (exact hunks, touched nothing).**
  `testing/relay.py @@ -63,25 +64,21 @@` (proof block) + import hunks
  `@@ -38,7 +38,7 @@`, `@@ -47,6 +47,7 @@` — no ledger row, no
  baseline entry. `list_field.py @@ -171,57 +167,37 @@` (guard block)
  + import/docstring hunks; `@@ -245,10 +221,17 @@` is MIXED
  (ledgered trigger paragraph inside a concurrent reword). `registry.py`
  — 15 WT hunks unattributed (e.g. `@@ -122,16 +123,33 @@`
  `IdentityMap`) + `@@ -499,13 +526,17 @@` MIXED (ledgered
  single-inverse trigger paragraph inside a concurrent prose reword;
  the paragraph is WT dirt, absent at HEAD). Type gates on this
  tree state, workspace copy: basedpyright 0 errors / 0 warnings /
  0 notes (`dry-20261001T171641-c3ab95`); `check_any.py` exit 0,
  128 uses at 89 sites (`dry-20261001T171650-7ddf7e`);
  `check_truthful_reads.py --check` exit 0
  (`dry-20261001T171651-105c19`).

### R1 — `_check_typed_match` message reads (rejected)

Contract difference: renders `graphql_type_name` off two already-proven
types (factory-admitted target, decode-resolved candidate) for a
mismatch message. No registry arm, no verdict — reading, not proving.
Trigger: a registry read or rejection verdict there. Home: specified
owner clause + this artifact. Converge with the guard family's L2.

### R2 — `_stamp_node_type` tolerant model read (rejected)

Contract difference: `static_attr` + `getattr(definition, "model",
None)` tolerant read on a decode-resolved type to decide a copy before
stamping a routing hint. Best-effort by documented posture; a `None`
definition degrades to no-copy, never a rejection. Trigger: a verdict
there. Home: this artifact (the site docstring already states the
tolerant posture; no owner edit owed beyond the clause).

### R3 — inspect CLI check (rejected)

Contract difference: subclass gate + attribute-presence (`None`) check
for a table-print surface; no canonicality arm. Bare-name targets
resolve through the registry by construction; dotted paths trust the
import. Different surface, different envelope (`CommandError`), no
stamp read. Trigger: a contract source requiring canonicality at the
CLI. Home: this artifact. Converge with the file item's J4.

### R4 — `has_custom_get_queryset` tolerant branch (rejected)

Contract difference: optional-metadata read — a `None` definition
falls back to the `_is_default_get_queryset` flag read. No registry
arm, no verdict. Trigger: verdict semantics there. Home: this
artifact. Converge with the `types-base-queryset-hook-contract`
file-local row.

### R5 — registry-only readers (rejected, grouped)

Contract difference: each reads `get_definition` WITHOUT the attribute
arm, answering a different question — finalizer audits ("is every
DISCOVERED relation target registered", pre-mutation finalize phase),
`related_target_for` / resolver / decode / optimizer reads (hot-path
metadata off registry-held types), `model_for` (assumes registered by
contract), connection cache provenance ("does this caller hold the SAME
object the cached class was built from"). Different populations,
phases, envelopes. Triggers: an attribute arm joining any of them, or
the proof moving to a pending ledger. Homes: finalizer + provenance
with the guard family's F3/F4; the rest in-artifact. The
`queryset-seed-and-model-read` F2 single-ownership of the model read
stands untouched.

### R6 — mutation-target trio (rejected)

Contract difference: duck-typed mutation-protocol membership
(`_mutation_meta` + resolve seams + ledger) per spec-038 Decision 5;
model-less members allowed, `issubclass` deliberately absent (load
cycle). Different family by design. Trigger: mutation targets joining
the `DjangoType` registry. Home: this artifact. Converge with the
guard family's Matrix-1 + the file exclusion.

### R7 — per-subject message grammars (rejected)

Contract difference: list-side factory-interpolated arms vs the
testing fused message are per-subject wordings; a wording change moves
exactly its subject (C4). Sharing them would couple factory labels to
a test helper's remediation. Trigger: a shared wording taxonomy with
per-surface renderers. Home: the standing per-subject direction; the
predicate stays message-free by construction.

### R8 — resolver-callability seam (rejected)

Contract difference: `resolver must be callable` is a factory-only
rule at the base validator; the testing helper takes no resolver.
Stays at the base. Trigger: a second resolver seam. Home: the base
validator (no edit — already owned there).

Sub-rules for Worker-0: none new. F1 is the existing open
`registered-djangotype-definition-validation` index row (stays open,
blocked); R1–R8 converge with standing rows or record in-artifact
with specified owner-clause homes. No `## Families` item owed. No
`## Owned changes` rows — zero tracked changes landed.

## Defects

None. The base-docstring scope sentence (three enumerated consumers,
fourth meaning-site exists) was examined as a docstring-vs-body
candidate and is explicitly not a defect: the stated invariant (one
meaning everywhere) holds — all four sites agree, 23/23 green — only
the enumeration is incomplete, and no contract row breaks. The
migration's sentence update closes it. Matrix axis 6 found no omission
gap.

## Pending execution

- `proof: uv run python scripts/workspace.py run dry/regdef-f40/consolidate -- pytest tests/testing/test_relay.py "tests/test_list_field.py::test_djangolistfield_rejects_non_class_argument" "tests/test_list_field.py::test_djangolistfield_rejects_non_djangotype_class" "tests/test_list_field.py::test_djangolistfield_rejects_djangotype_without_definition" "tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta" "tests/test_list_field.py::test_djangolistfield_rejects_non_callable_resolver" "tests/test_list_field.py::test_djangolistfield_rejects_a_fabricated_same_origin_definition" "tests/test_list_field.py::test_djangolistfield_rejects_a_copy_of_the_real_definition" "tests/test_list_field.py::test_djangolistfield_rejects_a_target_the_registry_has_never_seen" "tests/test_list_field.py::test_djangolistfield_accepts_and_captures_the_registrys_exact_object" "tests/test_list_field.py::test_list_field_reads_the_target_definition_once_and_dispatches_through_it" --no-cov -n0 -q` (discharges F1's post-migration equivalence once the block clears; validated runnable 23/23 green at current bytes in run `dry-20261001T171754-54daac`; the census gate's `prove_failability.py` negative control runs at landing with the gate itself and has no command yet by construction).

## Judgment

The registered-own-definition proof is one rule with two authoritative
definitions — the testing mint guard and the field-factory base — on
three variation axes (C1 → 2, C2 → 2, C3 → 2), with current agreement
execution-verified at 23/23. The owner is the registry predicate by
dependency direction, reconciling the guard family's T-canonical
pointer one level down. Every touch path is hunt-dirty, so the
consolidation is specified — predicate, both compositions, sentence
fix, repoint, census gate, failability — and nothing is edited. Eight
exclusions carry contract differences with triggers; no defects; one
validated deferred proof.

## Independent verification (Worker-2)

### Own trace (recorded before opening `## Findings`)

Rule in my words: a probe counts as a usable `DjangoType` class
iff it is a `DjangoType` subclass whose
`__django_strawberry_definition__` attribute `is` the registry's
definition for it and whose `origin is` the probe. Three reads,
one verdict, fail closed into `ConfigurationError`.

- **Definitions (2).** [testing-relay][testing-relay]`::global_id_for`
  step-1a block (`:67-86`: subclass gate, attribute read,
  `get_definition`, triple conjunction fused into one boolean and one
  fused message, proven definition kept for the gates below) and
  [list-field][list-field]`::_validate_djangotype_target` identity
  core (`:190-197` inside `:182-200`: same three reads as a
  disjunction, one factory-interpolated message, canonical
  returned onward).
- **Writer (not a proof).** `types/base.py::DjangoType`
  `__init_subclass__` (`:887-891`): `register_with_definition` plus
  the attribute assignment from one value. The pair the proofs
  verify; classified writer, correctly uncounted.
- **Consumers (compose by name).** `_validate_relay_djangotype_target`
  (calls the base), `relay.py::_validate_node_target` (calls the
  relay wrapper), `connection.py::DjangoConnectionField` (`:2431`),
  `DjangoListField` (`:1565`), the testing helper's own finalized
  gate plus stamp read below the proof, post-admission display
  reads (`relay.py:233-234`, `:580`), every single-arm registry
  or attribute reader. None re-spells a proof arm; verified by
  body at the validator chain and by census elsewhere.
- **My counts.** C1 (accept inherited definitions) forces 2; C2
  (drop the registry-identity arm) forces 2; C3 (change the
  class/subclass gate or hostile posture) forces 2 compositions
  with 0 reader movement (readers single-owned at `truth.py`);
  C4 (reword one message) forces 1 per subject. Messages,
  return-vs-local adaptation, and arm spelling are the only
  differences and all parameterize without mode flags.
- **My owner.** [registry][registry]`::registered_own_definition`
  (to create), by principle 7 dependency direction: the registry
  writes the pair (`register_with_definition`) and holds the
  canonical read (`get_definition`); both consumers already import
  it (zero new edges). The base-validator alternative is refused:
  routing the testing helper through `list_field.py` would import
  sibling-flavor machinery against its documented import-light
  contract, and the base's factory messages plus resolver seam are
  the wrong envelope for a mint guard.

### Reconciliation

AGREE on every verdict-bearing claim: F1 CONFIRM count-2,
the owner, all eight rejections (each carries a contract
difference plus a trigger plus a home, confirmed member by
member against bodies), the blocked-on-hunt call (re-derived
below), zero-edit acceptance (no landable consolidation exists
independently of W1's trace: the one confirmed consolidation
edits hunt-dirty lines on all three touch paths, and the
refused-direction shortcut would edit them too), the writer /
proof / consumer classifications, the structural gate as
specified-not-landed (landing it now would be born-red — two
sites, no predicate — which the method prohibits, so deferral
is correct), the `proof:` typing of the deferred 23-node re-run,
sharded/PG inapplicable-by-construction (construction-time
validation over in-memory registry maps; the oracles' incidental
row fetches run on `default` in every cell and no finding varies
by alias or dialect), and the examined-and-cleared
docstring-enumeration note (below the defect bar: the stated
one-meaning invariant holds at all four sites, 23/23 green; only
the enumeration is incomplete, and no contract row breaks).

Guard-family reconciliation: AGREE, note not defect. The ticked
guard checkbox (plan `:1326`) stays factually true — the shape
guard is still single-sited in tree and the adopted trigger
paragraph is still in tree. Only the guard artifact's internal
F1-C2 census count (1, missing the testing file — confirmed:
`grep -c testing` over [guard][guard] is 0, and its C2 row reads
"1 (`_validate_djangotype_target` ...)") is stale against the
true count of 2. That staleness is documented here with the
T-canonical repoint specified to ride the migration, so no
closeout-homing finding is owed and the row stays shut.

Blocked-on-hunt, re-derived from `git diff HEAD` content:
`testing/relay.py` 3 hunks (proof `@@ -63,25 +64,21 @@` plus 2
import hunks), all unattributed, no ledger row, no baseline
entry; `list_field.py` MIXED `@@ -245,10 +221,17 @@` (ledgered
guard trigger paragraph inside a concurrent reword — the MIXED
call verified by content against the adopted-orphan row) with
every other hunk unattributed, including the guard block
`@@ -171,57 +167,37 @@` and both import hunks;
`registry.py` 15 unattributed plus 1 MIXED (see W2-C1), including
the import hunk and the `get_definition` region. Zero legal
partial landings: the predicate needs the uncommitted `truth`
import to preserve the hostile-metaclass posture, both
compositions edit hunt hunks, an owner without consumers is dead
code relieving no change obligation, and the gate now would be
born-red. The item correctly stopped with zero edits: item diff
vs `ITEM_BASELINE` (`d3d51c9e…`, `git cat-file -t` → `commit`,
verified myself) is the plan edit alone, and the only new file
is this untracked artifact. No oracle rewritten (nothing
tracked changed at all).

DIFFER on three record-accuracy items (all verdict-neutral;
finding verdicts, counts, owner, rejections, and the block
stand accepted):

- **W2-C1 (registry.py attribution — hard error).** "Ledgered
  content already at HEAD; all 16 WT hunks unattributed" is
  false. `git show HEAD:registry.py` contains no single-inverse
  trigger text (`grep "single inverse"` → zero), while the WT
  hunk `@@ -499,13 +526,17 @@` adds the trigger paragraph
  ("re-opens whether this scan stays the single inverse")
  beside the hunt prose reword (`NOT type_cls.__name__` → `NOT
  the class's own name`). Correct: 15 unattributed plus 1 MIXED
  (ledgered `relay-node-name-decode` paragraph plus hunt
  reword), symmetric with the `list_field.py` MIXED hunk.
- **W2-C2 (triple regex census — hard error).** "8 hits" → 9.
  W1's own enumeration lists 9 (2 executable, 4 comments, 3
  messages) and my WT grep reproduces exactly those 9:
  `grep -rn 'origin is (not )?(target_type|type_cls)|definition
  is (not )?canonical|is not a registered DjangoType'`.
  The enumeration itself is complete and correct; only the
  headline count is wrong.
- **W2-C3 (get_definition sweep — hard error).** "30 hits"
  reproduces as neither raw substring lines (67 at WT, 68 at
  HEAD) nor clean call-plus-def-plus-comment lines (19: 16
  calls, 1 def, 2 comments). Walker's per-file count is exactly
  30 — possible transcription slip. Re-derive with a stated
  instrument. Disposition completeness is unaffected (verified
  independently: every true call site lands in R5 or the
  proofs). The dunder instrument ("17 hits") re-hashes exact,
  and the "119 package files" gate census re-hashes exact
  (gate: 119 checked plus 1 exempt; `find` gives 120).

Soft note, no correction owed: my shape-grouping of the
finalizer and optimizer `get_definition` sites differs
slightly from "4 call shapes" each (5 sites each; shapes depend
on the unstated grouping criterion), but every site is disposed
into R5 either way.

### Checks performed

- Mechanism sweeps reproduced myself at WT bytes: dunder 17/17
  exact; triple census 9 lines, exactly 2 executable
  (`testing/relay.py:77`, `list_field.py:192`), remainder
  comments or messages without the check; origin-identity regex
  confirms no third co-locating body; `registered_own_definition`
  exists nowhere (only the testing local boolean).
- Principle-8 equivalence for the SPECIFIED migration verified
  against bodies: same exception type (`ConfigurationError`
  both sides), same per-site messages (migration steps keep each
  site's wording untouched), same accepted object (predicate
  returns the registry identity; both current success paths
  already resolve to exactly that object), same observation
  point (pre-use sync validation over maps — no transaction,
  await, or query effects), same short-circuit order (gates
  before the triple at both sites). Hostile-input fail-closure
  is pinned by the existing hostile oracles and rides the
  deferred proof.
- Freshness re-hashed myself same-kind (`git hash-object` WT,
  `git rev-parse HEAD:path`): indexed pins
  `572f8d64`/`76de954f` and `b534ea32`/`3842542a` match dispatch
  (no drift during the item); spot-checks `registry.py`
  `e95c39e7`/`5480c2eb`, `relay.py` `63bbba0b`/`037723cd`,
  `connection.py` `6c4b01f9`/`38491372`, `types/base.py`
  `e7a62d32`/`e0ad32aa`, `utils/querysets.py` `6d471bd7`/
  `adc74b64`, both oracle files, and `truth.py`
  `711352b1`/absent-at-HEAD all match digit-for-digit. Nothing
  reopened.
- Pending execution: the `proof:` selection collect-only
  validates at exactly 23 nodes (`--collect-only`, no
  execution, shared tree unmutated); typing as `proof:` is
  correct (discharges post-migration equivalence once the block
  clears), so the plan item will read `verified, pending
  execution` after the re-pass.
- Gates re-run myself in the shared tree (read-only):
  basedpyright 0/0/0, `check_any.py` 128 uses at 89 sites exit
  0, `check_truthful_reads.py --check` tier-1 0 exit 0 — all
  match the run-11 baseline and corroborate W1's workspace-copy
  runs by a second route. mypy neither run nor cited (gone).
- Ruff on the touched path (this `.md` artifact; zero touched
  `.py` paths): `format --check` clean, `check` vacuous ("No
  Python files found … All checks passed") — stated as
  expected. Prose rules: `path::Symbol` citations, raw
  `path:NN` confined to this `docs/dry/dry-*.md` scratchpad
  (permitted), LINK DEFINITIONS plus all 10 canonical headers
  present, run ids are required evidence citations not process
  provenance, specified tests target the package tier with a
  same-tier justification. No new test or production files, so
  no banned-word surface. HEAD `dd0b6691` unmoved at finish;
  status count 491.
- Oracle independence judged by reading (zero-edit, so none
  rewritten regardless): the copy/fabricated oracles drive the
  public factory, spell literal messages, and read the dunder
  only to construct hostile inputs, never to compute an
  expectation. `## Defects` correctly empty; I append none.

### Verdict: `revision-needed` (record-accuracy only)

All finding verdicts — F1 CONFIRM count-2 blocked-on-hunt, the
registry-predicate owner, R1–R8, the guard reconciliation, the
deferred gate and proof — are ACCEPTED. No re-trace is owed.
The revision corrects W2-C1, W2-C2, W2-C3, each re-derived by
Worker-1 against tree bytes (never copied from my numbers),
plus the Status line. Resubmission returns to the same
Worker-2; the re-pass checks exactly the three corrected
records plus nothing-else-changed.

## Iterations

### Pass 2 (Worker-1, record-accuracy revision, zero production edits)

Accepted Worker-2's `revision-needed`: all three findings
re-derived fresh against tree bytes (never copied), all confirmed
verdict-neutral as posited — no challenge, exclusion, or block call
moves. HEAD `dd0b6691` unmoved; artifact file only.

- **W2-C1 — registry.py attribution (fixed, neutral).** Repro:
  `git show HEAD:django_strawberry_framework/registry.py | grep -c
  "single inverse"` → 0 vs WT `grep -c` → 1; `git diff HEAD --`
  the path → 16 `@@` hunks. The `@@ -499,13 +526,17 @@` hunk
  adds the ledgered `relay-node-name-decode` single-inverse
  trigger paragraph (adopted orphan per the `## Owned changes`
  ledger row) beside the hunt prose reword (`NOT
  type_cls.__name__` → `NOT the class's own name`): MIXED,
  symmetric with the `list_field.py` MIXED hunk. Correct: 15
  unattributed + 1 MIXED. Fixed in the header attribution
  paragraph and the F1 blocked-on-hunt clause. Neutral: the
  block stands on the same paths — the MIXED hunk still
  carries hunt dirt and the other 15 hunks (import hunk,
  `get_definition` region) are still unattributed, so no
  landing opens or closes.
- **W2-C2 — triple census headline (fixed, neutral).** Repro:
  `grep -rnE 'origin is (not )?(target_type|type_cls)|definition
  is (not )?canonical|is not a registered DjangoType'` over the
  package → 9 lines (2 executable, 4 comments, 3 messages),
  exactly the enumeration's own listing. (Bare `grep -rn`
  without `-E` yields 3 — the alternations need ERE.)
  Headline corrected 8 → 9. Neutral: challenges count
  definitions (2), never census hits.
- **W2-C3 — `get_definition` sweep (fixed, neutral).** Repro:
  raw-substring `grep -rn` → 67 WT / 68 HEAD
  (`git grep ... HEAD -- django_strawberry_framework`);
  word-boundary `grep -rnw` → 19 lines, classified by reading
  as 16 calls + 1 def + 2 docstring mentions; the 48-line
  balance is `*target_definition*` substring noise
  (`target_definition` embeds `get_definition` at index 3).
  "30 hits" reproduces under no instrument tried (raw 67/68,
  word-boundary 19, files-with-matches 12/9) and is dropped.
  Corrected figure 19 recorded with the `grep -rnw`
  definition. Neutral: all 16 true call sites were already
  disposed (2 proofs + 14 across R5); the disposition list is
  unchanged.
- **Corroborated standing figures (untouched).** Dunder sweep
  re-hashes 17/17; `find` gives 120 package `.py` files =
  gate census 119 checked + 1 exempt. Fingerprints,
  verdicts, gates, proofs, and the W2 section otherwise
  intact. Status → `ready-for-verification/2`.

### Pass 2 (Worker-2, re-pass at dry/regdef-f40/verify-2 — `verified`)

Adopted the pass-1 `## Independent verification (Worker-2)` trace as
my starting trace; spot-checked its key claims rather than re-tracing
from zero. Re-ran all three W2-C1/C2/C3 repros myself at current tree
bytes; all three corrections confirm exactly as written. HEAD
`dd0b6691` unmoved; item diff vs `ITEM_BASELINE` (`d3d51c9e…`,
`git cat-file -t` → `commit`, verified myself) is still the plan edit
alone; artifact still untracked.

- **W2-C1 — CONFIRMED.** `git diff HEAD -- registry.py` → 16 `@@`
  hunks, including `@@ -499,13 +526,17 @@`; `git show
  HEAD:registry.py | grep -c "single inverse"` → 0 vs WT `grep -c`
  → 1; the hunk carries the ledgered single-inverse trigger paragraph
  beside the hunt prose reword (`NOT type_cls.__name__` → `NOT the
  class's own name`): 15 unattributed + 1 MIXED. Both corrected
  sentences present (header attribution paragraph; F1 blocked-on-hunt
  clause). Neutral: the MIXED hunk still carries hunt dirt, the other
  15 hunks (import hunk, `get_definition` region) still unattributed —
  the block stands on the same paths.
- **W2-C2 — CONFIRMED.** `grep -rnE 'origin is (not
  )?(target_type|type_cls)|definition is (not )?canonical|is not a
  registered DjangoType'` over the package (`--include='*.py'`) → 9
  lines, line-for-line the enumeration's listing: 2 executable
  (`testing/relay.py:77`, `list_field.py:192`), 4 comments
  (`testing/relay.py:118`, `list_field.py:236,1566`,
  `connection.py:2440`), 3 messages (`inspect_django_type.py:167,199`,
  `list_field.py:194`). Headline reads 9. Neutral: challenges count
  definitions (2), never census hits.
- **W2-C3 — CONFIRMED.** Raw `grep -rn` → 67 WT / 68 HEAD (`git grep`
  at HEAD); word-boundary `grep -rnw` → 19 lines, classified by reading
  as 16 calls + 1 def (`registry.py:514`) + 2 docstring mentions — my
  count agrees call by call (finalizer 5, resolvers 2, relay 1,
  definition 1, walker 3, extension 2, testing 1, list 1); the 48
  non-word lines all contain `target_definition` (0 without), which
  embeds `get_definition` at index 3. `30` reproduces under no
  instrument (67/68, 19, files 12 raw / 9 word). Neutral: all 16 true
  call sites were already disposed (2 proofs + 14 across R5);
  disposition unchanged.
- **Stale-spelling sweep.** Old-figure spellings over the artifact → 5
  lines, every one legitimate: three are pass-1 W2's frozen
  error-naming record (quoting the old figure to name the error —
  never erased), one is W1's pass-2 drop-explanation for `30 hits`,
  one is the new corrected `all 16 true call sites` disposition prose.
  No headline asserts an old figure as current.
- **Verdict-neutrality holds.** No challenge count moved (C1 → 2,
  C2 → 2, C3 → 2, C4 per-subject); no exclusion moved (R1–R8 all still
  rejected with contract difference + trigger + home); no fingerprint
  moved (below); the block stands (same three touch paths hunt-dirty,
  zero legal partial landings as derived on pass 1).
- **Nothing else changed.** F1 CONFIRM count-2 blocked-on-hunt, the
  registry-predicate owner, `## Defects` (none), the single `proof:`
  entry, and the full pass-1 W2 section (own trace, reconciliation,
  checks, verdict) are intact; required sections all present; Run line
  unchanged; only the Status line, the three corrected records, and
  this log moved.
- **Freshness re-hashed same-kind.** `testing/relay.py`
  `572f8d64…`/`76de954f…`, `list_field.py`
  `b534ea32…`/`3842542a…` match dispatch digit-for-digit; spot-checks
  `registry.py` `e95c39e7…`/`5480c2eb…` and
  `tests/testing/test_relay.py` `4e61e8f1…` match the F1 block.
  Nothing reopened. Standing figures corroborated: dunder 17/17,
  `find` 120 = gate census 119 + 1 exempt, status count 491.
- **Ruff on the touched path** (this `.md` artifact; zero touched
  `.py` paths): `format --check` clean, `check` vacuous — as on
  pass 1. Recorded from the run after appending this record.

Soft note, no correction owed (pass-1 precedent): W1's C2 aside "(Bare
`grep -rn` without `-E` yields 3…)" reproduces as 0 lines on this tree
— without `-E` the `|`/`()`/`?` are literal, so the full ERE pattern
matches nothing under either BSD or GNU BRE; 3 is the count of the
literal tail alone. Auxiliary log prose only; the corrected record
(9 = 2+4+3) is exactly right and the aside moves no verdict, count, or
disposition.

**Verdict: `verified`.** The 1 `proof:` entry remains, so the plan
item reads `verified, pending execution`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-relay]: dry-file-testing__relay.md
[guard]: dry-rule-relay-node-target-guard.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[list-field]: ../../django_strawberry_framework/list_field.py
[registry]: ../../django_strawberry_framework/registry.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
