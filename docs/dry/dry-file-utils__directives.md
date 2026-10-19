# DRY review: `utils/directives.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target
`django_strawberry_framework/utils/directives.py` is the
single owner of the construction-time validation for
the consumer-supplied `directives=` forward: one
char-wise reject arm, one `tuple()` materialization
with a typed containment, two fixed wordings, and a
label seam naming the consuming factory. Six direct
call sites compose it by name (list, connection,
mutation, node, nodes, the auth `_make_auth_field`
helper) plus two transitive paths
(`register_mutation` through `DjangoMutationField`,
`current_user` through the auth helper import),
covering all nine public factories that accept
`directives=`. No production edits; no plan edits;
nothing tracked touched.

Trace basis is HEAD bytes throughout
(`380786cf7b3213603a592717cc65386892d7bf50`,
77 lines). The worktree state
(`84f770d4830661387fa9e42e88429f51b3dbe362`,
78 lines) carries 3 hunks (24+/23-) of
concurrent-external dirt, attributed by content
below; the item-scoped diff vs `ITEM_BASELINE`
(`2b27ee5444ee81f9f6ddb8d8d1d1eace0f41f6e9`)
is empty on this path (the baseline blob on this
path IS the worktree blob, so the dirt predates
the item). The plan's `## Owned changes` ledger
carries no row naming this file (verified: the
section grep for `utils/directives` is empty).
HEAD is `0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`
at dispatch and at writing (unmoved).

### Hunk attribution (HEAD -> worktree)

All three hunks are the hunt's truth-migration,
the same migration the plan records as
concurrent-external dirt across the worktree
(`utils/truth.py` untracked (`??`), absent at
HEAD, worktree blob `d5c96bc8…`):

- Hunk 1 (module-docstring first line):
  "containment" becomes "validation". Prose
  half of the migration, matching the
  except-narrowing below.
- Hunk 2 (module-docstring body): the
  three-copies history plus the
  `except`-`Exception` rationale becomes the
  validation paragraph plus the package-wide
  exception-policy prose citing
  `utils/truth.py` and
  `scripts/check_truthful_reads.py`. Prose
  half of the same migration.
- Hunk 3 (imports + body):
  `-_safe_type_name` / `+from . import truth`;
  `isinstance(directives, _CHAR_WISE_TYPES)`
  becomes the `truth.is_instance` loop;
  `_safe_type_name` becomes `truth.kind`
  (x2); `except Exception` becomes
  `except TypeError` with a rewritten
  comment. Code half of the same migration.
  The identity-rendering swap is
  verdict-equivalent on ordinary inputs
  (`truth.is_instance` is real-MRO
  membership, `truth.kind` carries the
  same class-names-itself contract as
  HEAD `_safe_type_name`); the
  except-narrowing is NOT equivalent: a
  non-`TypeError` raised by iteration,
  which HEAD contained as
  `ConfigurationError`, propagates in the
  worktree. The oracle file moved with it
  (`9e832a5e…` -> `c8428955…`, 8 tests ->
  6: the first five defs byte-identical
  down to line numbers, the three
  containment rows replaced by the one
  `test_iterator_error_propagates`). A
  consistent concurrent contract change,
  judged by neither state here.

Connected sources read whole or at the riding
seam: all six direct call sites at HEAD bytes
(connection :2316, list :1603, relay :461 +
:545, mutations/fields :313, auth/mutations
:431) plus both transitive paths at HEAD
(`register_mutation` def :1271 returning
`DjangoMutationField(...)`, `current_user`
routing through the imported
`_make_auth_field`), `exceptions.py` HEAD
(`e06b0b7f…`, `_safe_type_name` :19) and
worktree (`93401220…`, reader deleted),
`utils/truth.py` (`is_instance` :158, `kind`
:340), the oracles (shared suite HEAD
`9e832a5e…` 8 tests / worktree `c8428955…` 6
tests; per-factory suites at HEAD `038e69ce…`
6 tests, `2fd9e458…` 3 tests, `e7ea7e12…` 4
tests), the distinguished validators
(`schema.py::_consumer_extension_entries`,
`utils/policies.py::resolve_policy`,
`optimizer/selections.py::should_include`,
`extensions/resource_policy.py::charge_directives`),
and the contract-source sweep (no spec,
glossary, or KANBAN mention; owner prose +
oracles only).

## Verification

### Matrix

1. **Cross-flavor policy mirroring** -- searched.
   The three sibling construction-time
   consumer-input validators each carry a
   distinct contract: schema `extensions=`
   entry classification (R1, fresh),
   optimizer runtime `@skip`/`@include`
   evaluation (R2, CONVERGE with verified
   selections R-2 on fresh evidence),
   resource-policy AST directive charging
   (R3, fresh), and the policy-precedence
   ladder (R4, fresh). Instrument: full
   `directives` token census over the
   package (every remaining hit is AST
   nodes, cost charging, or prose -- same
   token, different rule) plus body reads
   of all four validators.
2. **Sync/async twins** -- inapplicable by
   construction. Instrument: `grep` for
   `async|await` over both target states
   returns zero; zero ORM access. Pure
   construction-time validation: every
   factory calls it at field build, never
   inside a resolver, so no await boundary
   exists to twin across.
3. **Derived rather than repeated knowledge** --
   searched. No second derivation of
   "char-wise" or "materialize once" exists:
   the `_CHAR_WISE_TYPES` table and the
   `tuple()` containment each appear once,
   and the type-name rendering is composed
   by name from `exceptions._safe_type_name`
   (HEAD), never re-derived. The worktree
   `truth.*` spellings are the dirt's
   re-pointing, not a second derivation.
4. **Inverse / round-trip pairs** -- searched.
   The `tuple()` materialization has no
   inverse: single-pass iterables are
   consumed exactly once (pinned by the
   generator oracle, whose re-read proves
   the source is not re-driven), and no
   decode half exists by construction. The
   two reject arms are one-way diagnostics,
   not an encode/decode pair.
5. **Contracts restated in another medium** --
   searched. Contract sources: the owner
   docstring (projection; every claim
   re-verified against the bodies except
   the D1 omission) plus the 8-test HEAD
   suite (independent literals, never read
   from the owner) and the three
   per-factory suites (13 tests pinning
   call-through with real directive
   instances as positive controls). No
   spec, glossary, or KANBAN row restates
   the rule. No live-tier test exists, and
   none is owed: a construction-time
   `ConfigurationError` is unreachable
   from a real query, so the package tier
   is the correct home.
6. **Enforcement by omission** -- searched, no
   defect. Family: every public factory
   accepting `directives=` -- list,
   connection, mutation, node, nodes,
   login, logout, register, current_user
   (9 for 9 from the package census; no
   tenth param exists). All route through
   the one function (6 direct, 2
   transitive). Nothing routes to the maintainer.

### Enumeration

Instrument: `ast.Module.body` census of both
target states. HEAD: 6 members. Worktree: 7
members (+1: the dirt import, homed in the
hunk attribution above, not as a rule). No
nested defs. Every member lands below; line
numbers are HEAD bytes at `380786cf…`.

| # | Member (HEAD) | Home |
|---|---|---|
| 1 | Module docstring (:1-33) | F-MECH (projection; claims verified, D1 omission filed) |
| 2 | `typing` import (:35) | F-MECH |
| 3 | `exceptions` import (:37; `ConfigurationError` + `_safe_type_name`) | F-VALIDATE consumer link + F-MECH |
| 4 | `__all__` (:39; 1 name) | F-MECH |
| 5 | `_CHAR_WISE_TYPES` (:45-50; comment :41-44) | F-VALIDATE |
| 6 | `validated_field_directives` (:53-77) | F-VALIDATE |
| 7 | `from . import truth` (worktree only) | Dirt; see hunk attribution |

### Challenges

Each change posited with the definition count at
HEAD bytes. Consumers / oracles / projections that
also move are listed, never counted.

| ID | Change posited | Count | Home |
|---|---|---|---|
| C1 | A fifth char-wise type | 1 (`_CHAR_WISE_TYPES` + its comment; oracle param row listed) | F-VALIDATE |
| C2 | Reject-wording change | 1 (the f-string; 4 oracle files listed, independent literals by design) | F-VALIDATE |
| C3 | Containment-arm change (e.g. narrow `except Exception`) | 1 (the `except` arm; oracles listed) | F-VALIDATE |
| C4 | A tenth factory with `directives=` | 0 here (caller passes a label; function untouched) | F-VALIDATE split proof |
| C5 | Per-caller wording variation | Refused (fixed wording is the contract; the label is the variation seam) | F-VALIDATE |

C3 is the observed-concurrent-change probe: the
worktree dirt IS a C3 change (narrow to
`except TypeError`) with its oracle co-move,
counted 1 here in both states. No judgment on
the concurrent contract itself.

## Findings

### FL1 -- F-VALIDATE: the one directives validation (file-local)

- **Contract + variation.** `validated_field_directives`
  takes a factory label plus the raw consumer
  value and returns a tuple or raises the
  typed construction-time reject: a char-wise
  `str` / `bytes` / `bytearray` / `memoryview`
  (TABLE-driven, `isinstance` so subclasses
  reject too) refuses with the "must be a
  sequence" wording naming the value's real
  kind; anything else is materialized once
  via `tuple()` and an escaping `Exception`
  refuses with the "could not be read"
  wording naming the exception's type and
  chaining it as `__cause__` (never its
  message, which a hostile `__str__` owns);
  `BaseException` propagates. Both wordings
  are fixed across every caller; the label
  is the only per-caller variation.
- **Sites + roles.** *Definition*: this
  function + table (one body). *Consumers*:
  the six direct call sites (each passing
  only its label) plus the two transitive
  paths. *Oracles*: the 8-test shared
  suite (4 char-wise params, label,
  ordinary, generator, non-iterable chained
  `TypeError`, `RuntimeError` containment,
  midway-`ValueError` containment,
  `KeyboardInterrupt` passthrough) plus 13
  per-factory tests (list 6, relay 3,
  mutations 4, each with a real-directive
  positive control). *Projections*: the
  module docstring + each caller's
  single-siting comment (all verified
  against the bodies).
- **Challenges.** C1 counts 1; C2 counts 1;
  C3 counts 1; C4 counts 0 here (the
  connection factory arrived as a pure
  caller); C5 refused.
- **Owner + lifetime.** This module (the
  flavor-agnostic check lives nowhere else;
  every factory imports it by name). Pure
  function over an immutable table; nothing
  stored.
- **Migration.** None (no consolidation in a
  file item; the rule is already single-sited).
- **Distinct behavior.** Per-caller labels
  stay per caller (the documented variation
  seam); the kind rendering stays owned by
  `exceptions.py` and is composed, not
  restated.
- **Behavioral proof.** `static-reviewed`
  (body + all six call sites + both
  transitive paths + all four oracle files
  read at HEAD bytes; every arm pinned with
  independent literals).
- **Freshness.** Target `380786cf…` (work
  `84f770d4…`); consumers `21380eb7…`,
  `4894f90f…`, `c3c5aea5…`, `d4edcbb7…`,
  `d1a59c44…`, `b036bdac…` (CLEAN);
  renderer `e06b0b7f…`; oracles
  `9e832a5e…`, `038e69ce…`, `2fd9e458…`,
  `e7ea7e12…` (all HEAD).

### FL2 -- F-MECH: module mechanics (file-local)

- **Contract + variation.** The module
  docstring states the lazy-consumption
  hazard, the three failure modes, the
  single-owner claim, the three-copies
  history, and the `except`-`Exception`
  rationale with the `BaseException`
  exclusion; `__all__` admits exactly the
  one public name; the import block binds
  only annotation substrate plus the
  `exceptions.py` consumer link. All
  docstring claims re-verified against the
  bodies except the D1 omission: the
  every-factory sentence names list /
  mutation / register-passthrough / auth /
  node / nodes but not the connection
  factory, which calls the validator at
  HEAD (`connection.py:2316`).
- **Sites + roles.** *Definition*: docstring +
  imports + `__all__` (one mechanics rule).
  *Oracles*: the shared suite (behavioral
  pins for every docstring failure mode).
- **Challenges.** Adding a public name or an
  import counts 1.
- **Owner + lifetime.** This module.
- **Behavioral proof.** `static-reviewed`.
- **Freshness.** Target `380786cf…` (work
  `84f770d4…`); renderer `e06b0b7f…`.

### R1 -- validation vs schema extensions entries (rejected)

The opaque-instance forward
(`_CHAR_WISE_TYPES` arm + `tuple()`
materialize + fixed wordings, no per-entry
inspection) vs
`schema.py::_consumer_extension_entries`
(exact-authority classification per entry,
policy folding into the schema record,
subclass refusal, `SCHEMA_CONFIGURATION_UNAVAILABLE`
for late-deciding factories). Contract
differences: entries classified by exact
type with behavior folded out vs entries
never inspected and forwarded whole; a
shared "consumer-iterable validator" would
couple the two refusal shapes. Fresh pair,
no prior verdict. Trigger: a second
opaque-forward consumer iterable needing
the identical two arms. Freshness: target
`380786cf…`, schema body cited (worktree).

### R2 -- validation vs optimizer runtime directive evaluation (rejected)

Definition-time hostile-shape validation
(label + raw value in, tuple or
`ConfigurationError` out) vs
`optimizer/selections.py::should_include`
(runtime `@skip` / `@include` evaluation on
already-converted selection dicts) and its
`convert_directives` compiler. Contract
differences: separate inputs (consumer
iterable vs converted AST), separate phases
(field build vs per-walk evaluation),
separate reasons to change. CONVERGE with
verified selections R-2 on fresh evidence,
never inherited (that row's trigger --
runtime evaluation needing hostile
hardening -- re-checked unfired: the body
reads plain converted dicts). Trigger: the
selections standing trigger. Freshness:
target `380786cf…`, selections body cited.

### R3 -- validation vs resource-policy directive charging (rejected)

Shape validation of a consumer iterable vs
`extensions/resource_policy.py::charge_directives`
(per-AST-node cost charging over
`operation.directives` / `var_def.directives` /
fragment spreads). Contract differences: a
reject-or-materialize gate vs a cost walk
that never rejects shapes; disjoint
populations (definition-time values vs
request documents). Fresh pair, no prior
verdict. Trigger: cost charging needing
shape validation. Freshness: target
`380786cf…`, resource-policy body cited.

### R4 -- validation vs the policy-precedence ladder (rejected)

Iterable forwarding vs
`utils/policies.py::resolve_policy`
(mapping-or-instance normalization through
the explicit / setting / default
precedence into a frozen policy record).
Contract differences: different input
populations (arbitrary iterables vs policy
mappings), different outputs (tuple vs
frozen record), no precedence axis here.
Fresh pair, no prior verdict. Trigger: a
precedence axis on a forwarded iterable.
Freshness: target `380786cf…`.

### R5 -- standing guard triggers re-checked (rejected)

J1 (shared `except`-guard driver, standing
rejection at File `_request_body.py`):
unfired -- the HEAD `except Exception` arm
is containment-specific (names the escaping
TYPE, chains `__cause__`, documents why the
message is excluded); a shared driver would
own catch mechanics, not this diagnostic
contract. J2 (shared exact-type gate,
standing rejection at File
`_request_body.py`): unfired -- the
char-wise check is deliberately NOT
exact-type (`str` subclasses iterate
char-wise too), and no exact-type gate
lives here. Freshness: target
`380786cf…`.

## Defects

### D1 -- module docstring omits the connection-factory consumer (minor, HEAD)

The every-factory sentence
(`utils/directives.py` module docstring
:3-5) enumerates list, mutation,
register-passthrough, auth, and node /
nodes, but `DjangoConnectionField` calls
the validator at HEAD
(`connection.py:2316`,
`validated_field_directives("DjangoConnectionField",
directives)`). A reader auditing "every
field factory" from the owner prose misses
one consumer. Non-duplication doc-accuracy
defect, owned by this file; no
authorization / routing / exposure surface
is involved. Pending closeout homing.

## Judgment

Zero-edit file item, ready for verification.
All 7 `ast.Module.body` members homed (6
HEAD members to 2 file-local findings + 5
rejections; the worktree-only import to the
hunk attribution): 2 file-local, 0 new
families, 0 convergences needing plan
changes (R2 converges on fresh evidence
with the standing row untouched), 5
rejected, 1 minor defect pending closeout
homing. The rule is already single-sited:
six direct consumers plus two transitive
paths, one definition, zero second sites.

## Index rows for Worker-0

Pipe-table rows to transcribe verbatim (7
new rows; R2 converges with the standing
selections row and needs no family change):

- `| directives-field-validation | django_strawberry_framework/utils/directives.py::validated_field_directives | django_strawberry_framework/utils/directives.py | File utils/directives.py | file-local |`
- `| directives-module-mechanics | django_strawberry_framework/utils/directives.py | django_strawberry_framework/utils/directives.py | File utils/directives.py | file-local |`
- `| directives-validation-vs-schema-extension-entries | django_strawberry_framework/utils/directives.py::validated_field_directives (rejection recorded here; fresh pair, no prior verdict) | django_strawberry_framework/utils/directives.py, django_strawberry_framework/schema.py | File utils/directives.py | rejected |`
- `| directives-validation-vs-runtime-directive-evaluation | django_strawberry_framework/utils/directives.py::validated_field_directives (rejection recorded here; CONVERGE with verified selections R-2 on fresh evidence) | django_strawberry_framework/utils/directives.py, django_strawberry_framework/optimizer/selections.py | File utils/directives.py | rejected |`
- `| directives-validation-vs-directive-cost-charging | django_strawberry_framework/utils/directives.py::validated_field_directives (rejection recorded here; fresh pair, no prior verdict) | django_strawberry_framework/utils/directives.py, django_strawberry_framework/extensions/resource_policy.py | File utils/directives.py | rejected |`
- `| directives-validation-vs-policy-precedence-ladder | django_strawberry_framework/utils/directives.py::validated_field_directives (rejection recorded here; fresh pair, no prior verdict) | django_strawberry_framework/utils/directives.py, django_strawberry_framework/utils/policies.py | File utils/directives.py | rejected |`
- `| directives-standing-guard-triggers | django_strawberry_framework/utils/directives.py::validated_field_directives (rejection recorded here; standing J1/J2 triggers re-checked unfired) | django_strawberry_framework/utils/directives.py, django_strawberry_framework/_request_body.py | File utils/directives.py | rejected |`

## Independent verification (Worker-2)

### Read-order note

The dispatch brief named W1's shape (6 members,
3 hunks, 5 rejections, D1) and required the
artifact as up-front reading, so blind
expectation-first was unavailable. Mitigation:
every judgment below is re-derived from HEAD
bytes with independent instruments (fresh
fingerprints, fresh censuses, fresh body reads).
Read order affects narrative, not evidence.

### Expectations (method-derived)

Small validation leaf: 5-8 module members, one
public function plus table plus manifest. N
direct consumers each passing only a label; any
"every factory" prose checkable against a
`directives:` param census (no tenth param, or
a defect). Dirt attribution checkable by hunk
content plus `truth.py` presence/absence plus
oracle co-move. Token collisions (AST
directives, cost charging) expected to reject
on phase/population differences; any CONVERGE
must name the standing row plus trigger with a
fresh-evidence re-check. Owner expectation:
this module (flavor-agnostic leaf, every
factory imports it by name).

### Independent trace

HEAD blob `380786cf` (77 lines), worktree
`84f770d4` (78 lines); HEAD `0c0537e2`
unmoved (checked at start and end).
`ast.Module.body` census HEAD: 6 members
(docstring, `typing` import, `exceptions`
import [`ConfigurationError` +
`_safe_type_name`], `__all__`,
`_CHAR_WISE_TYPES`, `validated_field_directives`);
worktree: 7 (plus `from . import truth`). No
nested defs. Owner: this module.
Call-site census at HEAD (`git grep`, whole
package): exactly 6 direct calls (connection
:2316, list :1603, relay :461/:545,
mutations/fields :313, auth/mutations :431)
plus imports, `__all__`, and the def itself;
transitive `register_mutation`
(auth/mutations :1271 returning
`DjangoMutationField(...)`) and `current_user`
(auth/queries :92-120 through the imported
`_make_auth_field`). `directives:` params: 9
public factories plus the internal helper
(:406), `charge_directives`, the selections
read, and the validator's own signature. No
tenth factory.
Oracles: shared HEAD `9e832a5e` (8 tests,
independent literals throughout) to worktree
`c8428955` (6 tests; bytes identical before
:88 including the 5 def lines, 3 containment
rows replaced by 1 propagation test);
per-factory `038e69ce` (6), `2fd9e458` (3),
`e7ea7e12` (4), each with a real-directive
positive control. Bodies read fresh:
`schema.py::_consumer_extension_entries`
(:1303, exact-type classify plus fold plus
subclass/double-declare refusal),
`selections.py::should_include` (converted-dict
runtime eval), `charge_directives` (:1100, AST
cost walk), `policies.py::resolve_policy`
(:107, precedence ladder into a frozen record).
Standing rows: selections R-2 (verified;
trigger "runtime evaluation needing hostile
hardening"); `_request_body` J1 (trigger "a
new guard needing the same position-state
classification") and J2 (trigger "a new
foreign-object protocol needing exclusion
inside a boundary").

### Reconciliation

1. Enumeration STANDS: counts and homes
   reproduced member by member (6 HEAD to
   F-VALIDATE/F-MECH, worktree-only import to
   dirt).
2. Hunk attribution STANDS: 3 hunks, content
   matches the hunt truth-migration (docstring
   halves plus code half); `truth.py`
   untracked, absent at HEAD, `d5c96bc8`;
   exceptions reader present at HEAD
   (`e06b0b7f` :19) and deleted at worktree
   (`93401220`); oracle co-move consistent;
   the except-narrowing non-equivalence is
   correctly left unjudged as concurrent.
3. All 5 rejections STAND. R1/R3/R4 are fresh
   pairs (no prior verdict in the schema, conf,
   or extensions artifacts; consumer artifacts
   treat the validator as definition only).
   R2 CONVERGE is accurate (same pair, same
   contract difference; trigger re-checked
   unfired: `should_include` reads plain
   converted dicts). R5 unfired on fresh
   evidence (J1: the arm is a type-naming
   diagnostic with `__cause__`, no
   position-state classification needed; J2:
   `isinstance` is deliberately
   subclass-inclusive, no `type()` gate in the
   target).
4. D1 STANDS at HEAD bytes (docstring :3-5
   omits the connection factory;
   `connection.py:2316` calls the validator)
   and meets the DRY defect bar
   (universality-claim omission, the
   docstring-contradicting-body class; minor;
   owned by this file; closeout homing
   correct; no authorization, routing, or
   exposure surface).
Challenges C1 (1), C2 (1), C3 (1,
worktree-observed), C4 (0 here), C5 (refused):
STAND. Matrix axes 1/3/4/5/6 verified
searched (census reproduced; generator re-read
pin confirmed; live tier correctly not owed --
a construction-time reject is unreachable from
a real query); axis 2 judgment stands with
correction W2-C2. Freshness pins reproduced
(target, oracles, renderer, all six consumer
HEAD blobs) with correction W2-C1. Item diff
empty (baseline path blob equals worktree
`84f770d4`; artifact untracked; W1 touched
nothing tracked); `## Owned changes` grep
empty; no `## Pending execution` owed
(zero-edit, all `static-reviewed`); no
structural gate owed (no consolidation);
AGENTS.md prose holds (raw `:NN` allowed in
`dry-*.md`; 10-header link scaffold present);
ruff N/A (no tracked source touched).

### Corrections (Worker-2)

- W2-C1 (freshness annotation): consumers
  "(CLEAN)" is inaccurate -- 5 of 6 files are
  dirty in the worktree (`M`: connection,
  list_field, relay, mutations/fields,
  auth/mutations; clean: auth/queries
  `b036bdac` both states). Worktree blobs:
  list `f5b0183e`, connection `1fca6266`,
  relay `e75e2b66`, mutations/fields
  `0e4d5ed1`, auth/mutations `84183c89`. All
  six seam call lines are byte-identical
  HEAD-vs-worktree (connection 2316/2347,
  list 1603/1549, relay 461/468 and 545/552,
  mutations/fields 313/335, auth/mutations
  431/430), so the HEAD-based trace holds for
  both states and the HEAD pins remain the
  correct staleness pins. No finding depends
  on the cleanliness claim.
- W2-C2 (axis-2 instrument): "grep for
  `async|await` over both target states
  returns zero" is inaccurate -- the worktree
  returns 1 hit (module-docstring prose
  `asyncio.CancelledError` in the dirt's
  exception-policy paragraph). Zero code hits
  in both states; the inapplicability judgment
  (pure construction-time validation, no await
  boundary) stands.

### Verdict

`verified`: zero-edit file item; 2 file-local,
0 new families, 5 rejected, D1 minor HEAD
defect pending closeout homing. Index rows
transcribed as given (7 rows; R2 converges
with the standing selections row, no family
change).

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
