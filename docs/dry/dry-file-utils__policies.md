# DRY review: `utils/policies.py`

Status: verified
Run: 0.0.15 2026-09-22-5

## System trace

Target `django_strawberry_framework/utils/policies.py` owns the shared
schema-construction policy shape: the resolution ladder
(`utils/policies.py::resolve_policy`), the canonical copy
(`utils/policies.py::canonical_policy`), the handout copy
(`utils/policies.py::copy_policy`), and the message-grammar article
(`utils/policies.py::_article`). Two flavor adapters compose the ladder by
name and are pure declarations: `error_policy.py::resolve_error_policy` and
`resource_policy.py::resolve_resource_policy`, each a single
`resolve_policy(...)` call differing only in `policy_cls`, `default`,
`read_setting`, `display_name`, `unit`. The settings readers they pass,
`conf.py::resource_policy_setting` and `conf.py::error_policy_setting`, are
thin `getattr` readers owned by `conf.py`, not rules of this file. Nothing
re-exports this module (`utils/__init__.py` and the package root carry no
`policies` name): all four production importers use the full path
(`error_policy.py`, `resource_policy.py`, `extensions/resource_policy.py`,
`schema.py`), so the narrow owner imposes no dependency reversal.

The canonical-copy split this item exists to state (cited by the six
re-traces): each flavor keeps three object roles. `DEFAULT_*` is the
exported value TEMPLATE, consumer-held, read by no enforcement seam in the
package (HEAD package-wide grep: `DEFAULT_*_POLICY` is read only to build
`_PACKAGE_*`; every other production hit is the declaration, the export, or
prose). `_PACKAGE_*` is the import-time canonical copy
(`canonical_policy(DEFAULT_*, ...)`), the authority every fallback reads.
The resolved per-schema policy is canonicalized at resolution — including
the no-override path — stored in the private enforcement record
(`schema.py::_SCHEMA_ENFORCEMENT`), and every consumer-reachable surface
answers with a `copy_policy` duplicate.

Consumer sites, classified (HEAD bytes; `canonical` builds authority,
`copy` hands a duplicate to a consumer-reachable surface, `read` is an
internal field read that never exposes the object):

- `canonical_policy`: the three `resolve_policy` arms (explicit instance,
  `default`, setting instance); `error_policy.py::_PACKAGE_ERROR_POLICY`
  and `resource_policy.py::_PACKAGE_RESOURCE_POLICY` declarations;
  `resource_policy.py::_operation_policy`, which arms
  `resource_policy.py::begin_resource_budget`,
  `resource_policy.py::stash_resource_policy`, and the
  `extensions/resource_policy.py` constructor settle.
- `copy_policy`: `schema.py::DjangoSchema.resource_policy`,
  `schema.py::DjangoSchema.error_policy`,
  `resource_policy.py::policy_from_info` (armed arm and mirror-or-miss
  arm), `resource_policy.py::_publish_budget_mirror`,
  `extensions/resource_policy.py::_policy`.
- `_PACKAGE_*` internal reads: `extensions/error_policy.py::_degraded`
  (message attribute),
  `extensions/error_policy.py::schema_error_policy` (both fallbacks flow
  only to masking field reads),
  `extensions/error_policy.py` teardown fallback,
  `extensions/resource_policy.py::_resolved_policy` (canonicalized by
  `begin_resource_budget` before anything is armed),
  `schema.py::_FALLBACK_ENFORCEMENT` (copied at each property read),
  `schema.py::_masked_return` floor.
- Indirect, via `policy_from_info` copies only: `list_field.py` (reads
  `max_list_rows` off the copy) and `utils/connections.py` (reads
  `max_page_size` off the copy through `effective_bound`).

Oracles: `tests/utils/test_policies.py` (probe-policy ladder pins plus
both-flavor hostile-mapping rows), `tests/test_error_policy.py` and
`tests/test_resource_policy.py` (identity pins: resolved `is not` the
passed instance and `is not` the exported template),
`examples/fakeshop/test_query/test_error_policy_api.py::test_a_written_exported_default_cannot_unmask_a_later_schema`
and
`examples/fakeshop/test_query/test_resource_policy_api.py::test_a_written_exported_default_cannot_widen_an_unconfigured_schema`
(live DEFAULT-tamper rows). Projections: the module docstrings at the
target and the five direct-consumer modules (`error_policy.py`,
`resource_policy.py`, `extensions/error_policy.py`,
`extensions/resource_policy.py`, `schema.py`), and the GLOSSARY
`ErrorPolicy`, `ResourcePolicy`, Execution resource policy, and Production
error policy anchors. (`list_field.py` and `utils/connections.py` are
consumers through `policy_from_info` copies, not projection sites.)

Composed-by-name inputs (not rules of this file):
`exceptions.py::describe_value` (the one owned `got` tail translation),
`exceptions.py::ConfigurationError`, `dataclasses.fields`. The target's
docstring cites `conf.py::upstream_patches_enabled` twice as precedent for
the materialize-once and key-guard arms; that citation is examined as F3,
not taken as verdict.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. The two schema-construction
   policies are the mirror and both resolve through `resolve_policy`; the
   Settings key census (`conf.py`: exactly `RESOURCE_POLICY_KEY` plus
   `ERROR_POLICY_KEY` among policy keys; every other key is a scalar or
   toggle with its own validator) proves no third deployment policy
   exists. Internal seal policies (`utils/querysets.py::_SealPolicy`,
   `_DEFAULT_SEAL_POLICY`, `_LIST_ARGUMENT_VISIBILITY_POLICY`) carry no
   settings key and no instance-or-mapping surface; rejected as R6.
2. Sync/async twins — NO SUCH SURFACE. The target is construction-time
   plus per-read in-memory copies with no await point, no executor, and
   no I/O; there is no async twin to drift.
3. Derived rather than repeated knowledge — SEARCHED. Both `known` sets
   (`resolve_policy` over `policy_cls`, `ResourcePolicy.narrowed` over
   `self`) derive from the single dataclass declaration via `fields()`,
   so a new field moves zero definitions (R5). The `display_name` /
   `unit` grammar and `_article` derive each message at the one site
   that emits it.
4. Inverse / round-trip pairs — NO SUCH SURFACE. The nearest pair,
   canonical-construct versus handout-duplicate, is intentionally
   asymmetric (re-validate versus never re-validate); it is two rules,
   not two halves of one grammar, and is recorded as such in F2.
5. Contracts restated in another medium — SEARCHED. Every medium a change
   moves is classified in System trace: oracles (probe, identity, and
   live tamper rows listed there) and projections (six consumer-module
   docstrings plus four GLOSSARY anchors). The oracles spell expectations
   independently (probe policy, literal messages); none reads the owner.
6. Enforcement by omission — SEARCHED. Ladder family: both deployment
   policies resolve through it (key census above); no member lacks the
   guard. Isolation family: every consumer-reachable handout audited
   above answers with a copy, and every fallback reads `_PACKAGE_*`
   (zero `DEFAULT_*` readers in the package); no uncopied handout and no
   template reader at HEAD. Omission would be a defect, and none was
   found; the family item (F2) owns the gate that keeps it that way.

### Enumeration

Instrument: every name in `ast.Module.body` of the HEAD bytes
(`8c881c0a`, 187 lines), read via `git show HEAD:` plus an AST dump.
Count: 12 nodes. Every member lands below; nothing is unassigned.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (shared-shape contract prose) | Projection at the owner; supports F1/F2 (prose, not a definition) |
| 1-4 | `__future__`, `collections.abc`, `dataclasses`, `typing` imports | Mechanics; no rule |
| 5 | `..exceptions` import (`ConfigurationError`, `describe_value`) | Consumer link to `exceptions.py`-owned rules; no rule here |
| 6 | `__all__` (`canonical_policy`, `copy_policy`, `resolve_policy`) | File-local L2 (leaf manifest; `_article` deliberately private) |
| 7 | `PolicyT` | File-local L2 (module-local generic plumbing; single definition) |
| 8 | `copy_policy` | F2 (`policy-authority-isolation`) |
| 9 | `canonical_policy` | F2 (`policy-authority-isolation`) |
| 10 | `_article` | File-local L1 |
| 11 | `resolve_policy` | F1 (`schema-construction-policy-ladder`); mapping arm also F3 (`hostile-mapping-hardening`) |

### Challenges

Each rule, changes posited on its variation axes, authoritative
definitions counted (consumers, oracles, projections listed, never
counted):

- Ladder precedence (explicit, setting, default): posit a fourth source
  — 1 definition (`resolve_policy`); the two flavor adapters are
  declarations and move only if their parameters change shape.
- Ladder instance acceptance: posit rejecting setting-slot instances —
  1 definition. Posit returning `default` as-is on the no-override path
  — 1 definition (and it breaks F2; coupling noted, not fixed here).
- Ladder variation axes: posit a third policy flavor — 0 existing
  definitions change; one new adapter declaration plus one settings
  reader. Posit renaming a unit word — 1 definition (the two flavors
  move together through `display_name`/`unit`).
- Canonical copy: posit skipping validation for exact-type inputs — 1
  definition (`canonical_policy`); refused by the subclass-read and
  `__dict__`-write reasons its docstring states.
- Handout copy: posit re-validating per read — 1 definition
  (`copy_policy`); refused by the per-field-seam cost reason its
  docstring states.
- Shared flat-copy assumption: posit a mutable field type on either
  policy — 2 mechanisms move (`canonical_policy` passes values by
  reference into the new instance; `copy_policy` passes them by
  reference into the new `__dict__`); both assume immutable leaves, an
  assumption currently enforced per flavor by exact-type
  `__post_init__` checks. Recorded in F2 for the family item.
- Hostile mapping, full triple (materialize-once + key-guard +
  unknown-vocabulary): posit coercing non-string keys — 2 definitions
  (`resolve_policy`, `conf.py::upstream_patches_enabled`).
- Hostile mapping, materialize-once alone: posit a new hostile
  iteration shape — 3 definitions (the two above plus
  `conf.py::_normalize_user_settings`).
- Hostile mapping, unknown-key grammar: posit quoting names with `!r` —
  policy flavors move as 1 through the shared parameters; every other
  subject (`conf.py`, `types/base.py`) moves independently (R3).
- Field-name derivation: posit a new bound on `ResourcePolicy` — 0
  definitions (`resolve_policy` and `narrowed` both derive from
  `fields()`); the declaration is the one owner (R5).

No read-only probe was needed: every claim above is decided statically
against HEAD bytes (definition counts, import census, key census,
grep-verified absence of `DEFAULT_*` readers), so no
`docs/dry/temp-tests/dry-file-utils__policies/` scope was created and no
pytest ran.

## Findings

### F1 — Schema-construction policy ladder (NEW family `schema-construction-policy-ladder`, open)

Contract: one deployment policy resolves per schema construction down
the ladder explicit argument, settings mapping, package default; an
instance from either override slot is canonicalized; a mapping is
applied over the dataclass defaults after the hostile-mapping arms; a
non-mapping override and unknown keys are typed rejections whose wording
derives from `display_name`/`unit` so the two flavors cannot drift in
text or behavior. Variation axes, each a `resolve_policy` parameter:
`policy_cls`, `default`, `read_setting`, `display_name`, `unit`.

Sites and roles: definition `utils/policies.py::resolve_policy`
(HEAD `8c881c0a`); declarations `error_policy.py::resolve_error_policy`
and `resource_policy.py::resolve_resource_policy` (HEAD `1a19cd7d`,
`4b69e974`); setting readers `conf.py::resource_policy_setting` /
`conf.py::error_policy_setting` (HEAD `c6ad46aa`); consumers — every
`canonical_policy`/`copy_policy`/`_PACKAGE_*` site in System trace;
oracles `tests/utils/test_policies.py` (HEAD `57ab2170`), the flavor
identity pins, and the two live tamper rows; projections — the five
direct-consumer-module docstrings and four GLOSSARY anchors.

Challenges: all ladder rows in `### Challenges` count 0–1 definitions;
no second ladder exists. Owner by responsibility: `resolve_policy` —
the narrowest module every flavor already imports downward with no
reversal. The family item audits the ladder whole (both adapters, both
readers, the `_PACKAGE_*` defaults each flavor passes) and decides the
structural gate; this file item makes no edit.

Freshness: target HEAD `8c881c0a165dc31022051dd628d6e36d99d44eca`
(worktree `3f2066a9be57188bc3500675561ed6d86b592a74`, 236 lines,
concurrent hunt dirt — resolve guards, isinstance armor, key
normalization — NOT traced); `error_policy.py` HEAD `1a19cd7d9c15`,
`resource_policy.py` HEAD `4b69e974decb`, `conf.py` HEAD `c6ad46aa3f0c`,
`tests/utils/test_policies.py` HEAD `57ab21701c28` (worktree
`763ee8ca9fea83a2ea01389f55b88cd71a3dc2b4`, hunt dirt +115, NOT traced).

### F2 — Policy authority isolation (NEW family `policy-authority-isolation`, open)

Contract: no enforcement seam reads an object a consumer holds, and no
consumer-reachable surface answers with the authority. Three mechanisms
share the contract with disjoint variation axes. `canonical_policy`
(construction/arming): always a new `policy_cls`, exact type never
exempt; every field re-read once (a raising read is `ConfigurationError`)
and rebuilt through the constructor so `__post_init__` re-validates;
the original discarded. `copy_policy` (handout): `object.__new__` plus
`__dict__` transfer, no constructor, no re-validation, for the
per-field seam. `_PACKAGE_*` (import time): the canonical fallback
every miss path reads. The template/canonical/resolved split plus the
per-site copy/canonical/read classification in System trace is the
record the six re-traces cite; `list_field.py` (HEAD `21380eb72364`)
and `utils/connections.py` (HEAD `f549389ef0ed`) are indirect
consumers through `policy_from_info` copies only.

Sites and roles: definitions `utils/policies.py::canonical_policy` and
`utils/policies.py::copy_policy` (intentionally separate rules — the
re-validate axis — sharing one isolation contract); declarations
`error_policy.py::_PACKAGE_ERROR_POLICY`,
`resource_policy.py::_PACKAGE_RESOURCE_POLICY`;
consumers/enforcement sites — the full System trace list across
`error_policy.py`, `resource_policy.py`,
`extensions/error_policy.py` (HEAD `7ee4e9dda5b0`),
`extensions/resource_policy.py` (HEAD `388018335b94`), `schema.py`
(HEAD `19f90bf55289`); oracles — identity pins plus both live tamper
rows; projections as in F1.

Challenges: per-mechanism changes count 1 each with docstring-stated
refusals; the mutable-field change counts 2 (shared flat-copy
assumption, currently enforced by per-flavor exact-type checks) and is
the family item's sharpest question. Owner: `canonical_policy` for the
contract, with `copy_policy` as the named no-revalidate variant — one
module, one import direction. Coupling: the no-override arm of F1 is
what keeps the resolved authority canonical; a change there reopens
this contract. The family item verifies the audit (every handout a
copy, every fallback canonical) and owns the gate; this file item makes
no edit.

Freshness: target HEAD `8c881c0a` (worktree `3f2066a9` hunt dirt, NOT
traced); `error_policy.py` `1a19cd7d9c15`, `resource_policy.py`
`4b69e974decb`, `extensions/error_policy.py` `7ee4e9dda5b0`,
`extensions/resource_policy.py` `388018335b94`, `schema.py`
`19f90bf55289`, `list_field.py` `21380eb72364`, `utils/connections.py`
`f549389ef0ed`, `tests/test_error_policy.py` `d7c467dc86ae`,
`tests/test_resource_policy.py` `b9db7c2f3985`,
`test_error_policy_api.py` `4c2c05ecc6cc`,
`test_resource_policy_api.py` `bd32df874611`, GLOSSARY `d3ef357c26ed`
(all HEAD blobs; GLOSSARY anchors read, not line-pinned).

### F3 — Hostile deployment-mapping hardening (NEW family `hostile-mapping-hardening`, open)

Contract candidate: a deployment-supplied mapping is materialized ONCE
into a plain `dict` (a `ConfigurationError` from its own reads
propagates; any other failure is the typed "iteration failed"
rejection), its keys pass a string-type guard before any set or sort
can leak a bare `TypeError`, and unknown keys are rejected naming the
valid vocabulary. Full triple: 2 definitions
(`utils/policies.py::resolve_policy` mapping arm,
`conf.py::upstream_patches_enabled` mapping arm — HEAD `c6ad46aa3f0c`).
Partial members: `conf.py::_normalize_user_settings` (shape gate plus
materialize, no key rule) and
`types/base.py::_validate_relation_shapes` (HEAD `91c587477ff8`;
`dict`-only gate, per-key guard, per-value vocabulary — validates over
live iteration and copies last, the reverse order). Accepted shapes,
vocabulary sources (dataclass fields versus constant sets), value
rules (constructor versus exact-bool versus enum membership), and
message grammars all differ per site; whether the shared triple is one
rule with two definitions or an intentionally separated idiom is the
family item's decision, with the per-site bodies
(`upstream_patches_enabled` carries hostile-`isinstance` armor the
HEAD `resolve_policy` lacks) as evidence either way.

Challenges: coercion counts 2; new-iteration-shape counts 3;
per-subject rewording counts 1 per subject. Owner: TBD by the family
item (candidates: the narrowest new owner every mapping validator can
import, or the status quo with the separation recorded at each site).
This file item names the family and makes no edit.

Freshness: target HEAD `8c881c0a` (worktree `3f2066a9` hunt dirt, NOT
traced); `conf.py` `c6ad46aa3f0c`, `types/base.py` `91c587477ff8`,
`tests/utils/test_policies.py` HEAD `57ab21701c28` (hostile-mapping
rows; worktree `763ee8ca` dirt NOT traced).

### L1 — Indefinite-article derivation (file-local)

`utils/policies.py::_article` derives "a"/"an" from the class-name
initial for the one rejection that names the policy class. One
consumer, one definition; inputs are always non-empty CamelCase
`__name__` values (both flavors plus the probe pin "a _ProbePolicy").
Challenge: posit a second article-needing message — no second site
exists (package-wide `_article`/article census is this module plus an
unrelated test identifier). Reconsideration trigger: a second
consumer.

Freshness: target HEAD `8c881c0a`.

### L2 — Module mechanics (file-local)

`__all__` admits exactly the three public helpers (`_article`
deliberately private); `PolicyT` is module-local generic plumbing with
its single definition here (package-wide census: no other
`canonical_policy`/`copy_policy`/`resolve_policy`/`_article`/`PolicyT`
definitions). Importers are exactly four production modules plus the
probe tests. No rule, no second site.

Freshness: target HEAD `8c881c0a`.

### R1 — `object.__new__` mechanism versus query-AST reconstruction (rejected)

`copy_policy` and `utils/querysets.py::_reconstructed_value` (HEAD
`b68be0e337d1`) share the `object.__new__` plus `__dict__` transfer
spelling and nothing else: a flat duplicate of an exact frozen
dataclass for handout isolation versus a recursive validated rebuild
of a Django AST graph with memo, per-slot reconstruction, and type
normalization (`sets_mixins.py`, HEAD `ad8987ea2fb1, and
`utils/permissions.py`, HEAD `9889d6fe2a24`, use the allocator for bare
instances — further distinct contracts). Contract difference: sharing
no state with a known-exact source versus proving and rebuilding an
untrusted graph. Reconsideration trigger: `copy_policy` needs
member-wise or recursive semantics.

### R2 — Handout copy versus narrowing derivation (rejected)

`copy_policy` duplicates without re-validation on the per-read seam;
`resource_policy.py::ResourcePolicy.narrowed` derives with overrides
through `dataclasses.replace` (constructor re-validation) plus a
narrowing check. Contract difference: identity-preserving duplicate
versus validated derivation; the cost and safety reasons point
opposite ways by seam. Reconsideration trigger: either seam changes
its validation stance.

### R3 — Per-subject rejection grammars (rejected)

Policy rejections share one grammar through `display_name`/`unit`
(count 1); `conf.py`, `types/base.py::Unknown Meta keys`, and
`optimizer/nested_fetch.py` strategy wordings each name their own
subject and vocabulary source. Contract difference: one parameterized
grammar for two flavors versus per-module framing with no package-wide
message owner. Reconsideration trigger: the package adopts one owned
rejection-message grammar.

### R4 — `_article` generalization (rejected)

Folded into L1's trigger: no second consumer exists, so no shared
article rule is owed. Reconsideration trigger: a second consumer.

### R5 — Field-name-set derivation (rejected)

`resolve_policy` and `ResourcePolicy.narrowed` both compute `known`
from `fields()`; the dataclass declaration is the one owner and a new
field moves zero definitions. A shared derivation helper would own
nothing. Reconsideration trigger: a spelled (non-derived) vocabulary
copy appears.

### R6 — Seal-policy defaults versus the deployment ladder (rejected)

`utils/querysets.py::_SealPolicy` and its `_DEFAULT_SEAL_POLICY`,
`_LIST_ARGUMENT_VISIBILITY_POLICY`, and sibling module-level policies
are internal execution parameters passed as instance default
arguments: no settings key (key census: no `SEAL` key), no
explicit-or-mapping surface, no consumer configuration. Contract
difference: internal call-chain parameter versus deployment-resolved
policy. Reconsideration trigger: a seal policy gains a settings-backed
deployment surface.

## Defects

None. Three near-misses were considered against HEAD bytes and are not
defects: (a) `canonical_policy` catches `Exception`, not `BaseException`,
around field reads — a `BaseException` from a deployment's own policy
object fails loud at construction and never reaches a request, which
satisfies the fail-loud contract; (b) `_article` indexes `name[0]` and
tests uppercase initials only — inputs are always non-empty CamelCase
`__name__` values, correct on every actual input; (c) the mapping arm
builds `policy_cls(**plain)` over dataclass defaults rather than over
the passed `default` — equivalent by construction since every flavor
passes a canonical copy of the template built from those same defaults.

## Pending execution

None. All conclusions are static against HEAD bytes; no probe, no
pytest, no scratch scope. Sharded and Postgres cells are inapplicable
by construction: the target reaches no database, alias, or dialect
decision (construction-time normalization plus in-memory copies).

## Judgment

Zero-edit file item: the target is the single owner of the resolution
ladder and the isolation contract, composed by name everywhere it must
hold, with three new families named for Worker 0 (`Index rows` below),
two file-local rows, and six rejections. The hostile-mapping triple is
the one genuine possible-duplication candidate and goes to its family
item undecided. No defect, no pending execution, no production edit,
no test edit.

## Index rows for Worker 0

(Worker 0 alone edits the plan; rows named here for transcription.)

- Family `schema-construction-policy-ladder` | Owner
  `utils/policies.py::resolve_policy` | Files `utils/policies.py`,
  `error_policy.py`, `resource_policy.py`, `conf.py` (readers) |
  Holding item Family `schema-construction-policy-ladder` | open
- Family `policy-authority-isolation` | Owner
  `utils/policies.py::canonical_policy` (with `copy_policy` as the
  named no-revalidate variant) | Files `utils/policies.py`,
  `error_policy.py`, `resource_policy.py`,
  `extensions/error_policy.py`, `extensions/resource_policy.py`,
  `schema.py`, `list_field.py` (indirect), `utils/connections.py`
  (indirect) | Holding item Family `policy-authority-isolation` | open
- Family `hostile-mapping-hardening` | Owner TBD by family item |
  Files `utils/policies.py`, `conf.py`, `types/base.py` (partial) |
  Holding item Family `hostile-mapping-hardening` | open
- Indefinite-article derivation | `utils/policies.py::_article` |
  `utils/policies.py` | File `utils/policies.py` | file-local
  (single consumer; trigger: second consumer)
- Module leaf manifest and generic plumbing | `utils/policies.py`
  (`__all__`, `PolicyT`) | `utils/policies.py` | File
  `utils/policies.py` | file-local
- `object.__new__` handout copy versus query-AST reconstruction |
  `utils/policies.py::copy_policy` (rejection recorded here) |
  `utils/policies.py`, `utils/querysets.py` | File `utils/policies.py`
  | rejected
- Handout copy versus narrowing derivation |
  `utils/policies.py::copy_policy` (rejection recorded here) |
  `utils/policies.py`, `resource_policy.py` | File `utils/policies.py`
  | rejected
- Per-subject rejection grammars | `utils/policies.py::resolve_policy`
  (rejection recorded here) | `utils/policies.py`, `conf.py`,
  `types/base.py`, `optimizer/nested_fetch.py` | File
  `utils/policies.py` | rejected
- Field-name-set derivation | `utils/policies.py::resolve_policy`
  (rejection recorded here) | `utils/policies.py`,
  `resource_policy.py` | File `utils/policies.py` | rejected
- Seal-policy defaults versus the deployment ladder |
  `utils/policies.py::resolve_policy` (rejection recorded here) |
  `utils/policies.py`, `utils/querysets.py`, `connection.py`,
  `list_field.py` | File `utils/policies.py` | rejected

## Independent verification (Worker 2)

### Worker-2 independent trace (recorded before opening `## Findings`)

Trace subject is HEAD bytes only:
`git show HEAD:django_strawberry_framework/utils/policies.py`
(blob `8c881c0a165dc31022051dd628d6e36d99d44eca`, 187 lines).
Worktree file is blob `3f2066a9be57188bc3500675561ed6d86b592a74`
(236 lines); its diff vs HEAD is hostile-`__class__` guard arms on the
four classification reads plus `str`-subclass key normalization, matching
the run-5 dispatch record of concurrent hunt dirt — out of scope, untouched.
`git rev-parse --short HEAD` = `5ee86193` at trace time. Window diff
`git diff --name-only c8f821e9 -- django_strawberry_framework tests
examples` is empty: Worker 1 made zero production/test edits, as expected
for this file item. All site line numbers below are HEAD-blob lines.

#### Enumeration (own instrument)

`ast.parse` over the HEAD bytes: `len(ast.Module.body)` = 12 —
index 0 module docstring (`Expr`); indexes 1-5 imports
(`__future__.annotations`, `collections.abc` (`Callable`, `Mapping`),
`dataclasses.fields`, `typing` (`Any`, `TypeVar`), `..exceptions`
(`ConfigurationError`, `describe_value`)); index 6 `__all__` (`Assign`);
index 7 `PolicyT` (`Assign`); indexes 8-11 `FunctionDef`
(`copy_policy`, `canonical_policy`, `_article`, `resolve_policy`).
Named members the item must home: `copy_policy`, `canonical_policy`,
`_article`, `resolve_policy`, `PolicyT`, `__all__` (+ imports/docstring).

#### Rules, sites, roles, challenges, owners

Rule A — schema-construction policy resolution ladder (precedence explicit
> setting > default; an instance from either override slot is
canonicalized; non-mapping rejected; unknown keys rejected naming the
valid vocabulary; a mapping is applied over the dataclass defaults).

- Definition (exactly 1):
  `django_strawberry_framework/utils/policies.py::resolve_policy`.
- Consumers: `django_strawberry_framework/error_policy.py::resolve_error_policy`
  and `django_strawberry_framework/resource_policy.py::resolve_resource_policy`
  (thin delegates passing `policy_cls` / `default` / `read_setting` /
  `display_name` / `unit`); `django_strawberry_framework/schema.py::DjangoSchema.__init__`
  transitively (HEAD `schema.py` lines 756-759).
- Oracles: `tests/utils/test_policies.py` (HEAD blob `57ab2170`, 237
  lines; probe-policy ladder/type-gate/vocabulary/article pins plus a
  both-flavor hostile-mapping matrix); `tests/test_error_policy.py` and
  `tests/test_resource_policy.py` (flavor tiers, including the `"an
  ErrorPolicy"` vowel-branch pin and the `is not` canonical pins);
  `examples/fakeshop/test_query/test_error_policy_api.py` and
  `test_resource_policy_api.py` (live wire wording). No oracle reads an
  owner table: `test_policies.py` imports `resolve_policy` itself as the
  unit under test and pins behavior with independent literals.
- Projections: module/function docstrings; the flavor-resolver docstrings
  citing the shared contract; `docs/SPECS/spec-047-resource_policy-0_0_14.md`
  + rationale; `docs/builder/DONE/build-047-resource_policy-0_0_14.md`;
  `docs/TREE.md` test rows; `docs/bug_hunt/bug_hunt-0_0_15.md` entries.
- Challenges (definition counts): reword the unknown-key rejection -> 1
  (`resolve_policy` lines 183-186); flip the setting-slot instance from
  accept to reject -> 1 (lines 142-148); add a `ResourcePolicy` bound ->
  0 here (the rule is generic over `fields(policy_cls)`; the flavor's
  `__post_init__` + oracles move); add a third policy flavor -> 0 edits
  (a new delegate declares its five parameters — declaration, not method).
- Owner I would choose: `resolve_policy` (existing owner; the narrowest
  cohesive owner both flavors import without reversing a dependency).

Rule B — canonical validated private copy (fields re-read once and
re-validated through the constructor into an exact-type instance; always a
new object; an unreadable field is a typed `ConfigurationError`).

- Definition (exactly 1):
  `django_strawberry_framework/utils/policies.py::canonical_policy`.
- Consumers: `error_policy.py::_PACKAGE_ERROR_POLICY` and
  `resource_policy.py::_PACKAGE_RESOURCE_POLICY` (import-time);
  `resource_policy.py::_operation_policy` (per-operation arming, reached
  via `stash_resource_policy`, `begin_resource_budget`, and
  `extensions/resource_policy.py` line 1233); three internal calls inside
  `resolve_policy` (explicit/setting/default rungs).
- Oracles: the `is not` pins through `resolve_policy`
  (`test_policies.py` lines 56/73/87, `test_error_policy.py` line 225,
  `test_resource_policy.py` lines 290/349/521) plus the flavor-tier
  exact-type/subclass pins (`test_error_policy.py` lines 163-190,
  651-664). Nothing imports `canonical_policy` in tests.
- Challenges: skip the copy for exact types -> 1 (`canonical_policy`)
  and must NOT move `copy_policy` (different rule); change the
  unreadable-field error shape -> 1.
- Owner I would choose: `canonical_policy` (existing).

Rule C — unvalidated authority duplicate (field-dict copy via
`object.__new__`, no constructor call, shares no state with the source).

- Definition (exactly 1):
  `django_strawberry_framework/utils/policies.py::copy_policy`.
- Consumers (6 call sites, 4 seams):
  `schema.py::DjangoSchema.resource_policy` (line 879) and
  `.error_policy` (line 893);
  `resource_policy.py::_publish_budget_mirror` (line 631);
  `resource_policy.py::policy_from_info` (lines 900, 902);
  `extensions/resource_policy.py::_policy` (line 1258).
- Oracles: `is not` pins at the consumer tiers (`tests/test_schema.py`
  line 580; `tests/test_resource_policy.py` lines 3421/3445/3892;
  `test_error_policy.py` line 331). Nothing imports `copy_policy` in tests.
- Challenges: re-validate on copy -> 1 (`copy_policy`) and must NOT move
  `canonical_policy` (already validates) — this asymmetry is what makes B
  and C two rules, not one. Deep-copy field values: implausible (fields
  are exact-typed immutables under the `__post_init__` gates), so it is
  posited and set aside, not counted as sharing evidence.
- Owner I would choose: `copy_policy` (existing; every hand-out seam can
  import it without reversing a dependency).

Rule D — indefinite article for policy class names (`"an ErrorPolicy"` /
`"a ResourcePolicy"`).

- Definition (exactly 1): `utils/policies.py::_article`. Consumer
  (exactly 1): `resolve_policy` line 151.
- Oracles: `test_policies.py` line 98 (`"a _ProbePolicy"`);
  `test_error_policy.py` lines 285/290 (`"an ErrorPolicy"`);
  `test_resource_policy.py` lines 364/369 (`"a ResourcePolicy"`).
- One-caller helper kept for its concrete responsibility (both flavors'
  typed rejections compose one wording rule; the anti-drift rationale is
  stated on `resolve_policy`), so no deletion is owed.

`PolicyT` / `__all__` / imports / module docstring: generic plumbing and
the leaf manifest; no second site for any of them.

#### Six-axis matrix (own discharge)

1. Cross-flavor mirroring — SEARCHED. Exactly two schema-construction
   policy flavors exist and both delegate to the one owner with declared
   parameters. Neighbor ladders enumerated and distinguished (rejections
   R1-R3 below).
2. Sync/async twins — INAPPLICABLE BY CONSTRUCTION. Zero `async`/`await`
   tokens in the HEAD bytes; three pure functions plus one private
   helper; no awaits, no ORM, no thread affinity, no twin surface.
3. Derived knowledge — SEARCHED. Each `fields(policy_cls)` call derives
   for its own immediate use from the single source of truth (the
   dataclass declaration): a value dict in `canonical_policy`, a name
   set in `resolve_policy`. Neither restates the other's result; nothing
   is stored, so no lifetime fields are owed. `display_name`/`unit` are
   declared variation (DRY principle 1); `ConfigurationError` /
   `describe_value` are composed by name from `exceptions.py` (principle
   6); the module reads no settings itself (`read_setting` is an injected
   perimeter — confirmed: no settings import).
4. Inverse/round-trip pairs — SEARCHED. `canonical_policy` (validate +
   privatize) vs `copy_policy` (duplicate without validation) look like a
   pair but are deliberately distinct rules with opposite validation
   contracts and opposite cost contexts (construction-time vs per-read);
   the separation rationale is stated on `copy_policy` (`#"Built by
   field-dict copy rather than by calling the constructor"`). No
   encode/decode or build/parse halves anywhere in the target.
5. Contracts in another medium — SEARCHED. Oracles spell independent
   literals (probe policy, `"must be a _ProbePolicy"`, `"Unknown
   probe-policy bound(s): wirth"`, hostile-mapping matrices); none reads
   an owner table. A wording change moves 1 definition + N oracles /
   projections (listed, never counted).
6. Enforcement by omission — SEARCHED. Resolver family: exactly the two
   flavor delegates (whole-package `resolve_*` census shows no third
   policy flavor). Hand-out seams: all six `copy_policy` call sites copy;
   authority-holding sites (`schema_error_policy` fallback,
   `_FALLBACK_ENFORCEMENT`, `_PACKAGE_*`) hold transiently and are read
   only through copying properties or guarded field reads. No flavor
   resolves outside `resolve_policy`; no hand-out seam hands out an
   authority. No omission gap. Standing observation for the six citing
   re-traces (not a defect — no contract row requires it): the error side
   guards each policy read at its use sites while the resource side
   canonicalizes once per operation; each rationale is stated at its own
   site but the contrast is not stated in one place.

#### Candidate rejections (own, with contract difference + trigger)

- R1 — `conf.py::upstream_patches_enabled` mapping hardening
  (materialize-once + key-guard + unknown-name rejection).
  Difference: a patch-gate bool read over a fixed frozenset with
  whole-mapping bool validation at app load, reading settings itself —
  vs policy normalization over dataclass defaults with domain validation
  delegated to `__post_init__` at schema construction via an injected
  `read_setting`. The shared technique is cited as precedent in prose at
  both `resolve_policy` comment sites. Trigger: a third hostile-mapping
  consumer, or one identical mechanical change landing on both — then a
  `hostile-mapping-containment` family.
- R2 — `views.py::_resolved_max_request_body_bytes` ladder. Difference:
  scalar `int | None` whose setting rung reads `None` as DISABLE (the two
  rungs read one sentinel differently) vs `None`-means-absent at both
  rungs plus dataclass-default application. Trigger: a third dataclass
  policy flavor delegates here (declaration); a scalar disable-ladder
  joins views, not this.
- R3 — `optimizer/nested_fetch.py::resolve_strategy`. Difference:
  name/instance selection returning shared singletons BY DESIGN
  (strategies carry no mutable bounds) vs instance/mapping/`None`
  normalization returning a private policy BY DESIGN (policies are
  enforcement authorities). Opposite sharing contracts. No plausible
  trigger short of strategies gaining per-deployment mutable bounds.
- R4 — `utils/querysets.py` query-node rebuild (`object.__new__` +
  `__dict__` transfer). Difference: AST recompilation skipping `clone()`
  vs a frozen-dataclass authority duplicate; shared tokens, distinct
  rules and reasons to change. Trigger: a second frozen-dataclass
  authority boundary needing no-validation duplicates.
- R5 — `types/base.py` unknown-fields message. Difference: model-`Meta`
  field vocabulary vs policy bound/option vocabulary; different owners,
  audiences, triggers. No plausible trigger.

No `proof:` / `gate:` entries are owed: read-only probes only, no
mutating proof needed, zero-edit file item. Read-only probe record: every
`git show HEAD:<path>` / `git grep -n <pattern> HEAD` command above ran
against blobs, never the hunt-dirty worktree files; no `$WS` copy was
taken (none needed); no scratch files were written (nothing under
`docs/dry/temp-tests/` — no executable experiment was required to judge
these pure-function contracts).

### Reconciliation with `## Findings` (read only after the trace above)

Enumeration: Worker 1's count (12 nodes, members 0-11) matches my own
`ast.Module.body` count exactly, member by member (docstring; imports
1-5; `__all__`; `PolicyT`; `copy_policy`; `canonical_policy`;
`_article`; `resolve_policy`). Every member is homed; nothing is
unassigned. The 1-4 import grouping is explicit and complete.

Matrix, per axis against the target's real surface:

- Axis 1 (cross-flavor mirroring) — searched, with one W1-missed
  neighbor (see (d) below). The settings-key census and the internal
  seal-policy census were re-verified (exactly `RESOURCE_POLICY_KEY` +
  `ERROR_POLICY_KEY`; no `SEAL` key in `conf.py`; `_SealPolicy` /
  `_DEFAULT_SEAL_POLICY` / `_LIST_ARGUMENT_VISIBILITY_POLICY` are
  instance-default call-chain parameters).
- Axis 2 (sync/async twins) — inapplicability correctly claimed and
  correctly reasoned; I independently confirmed zero `async`/`await`
  tokens in the HEAD bytes.
- Axis 3 (derived knowledge) — searched; both `known` derivations
  re-verified (`resolve_policy` over `policy_cls`,
  `ResourcePolicy.narrowed` over `self`, both via `fields()`).
- Axis 4 (round-trip pairs) — inapplicability correctly claimed:
  canonical-construct vs handout-duplicate is two rules, not two
  halves; matches my own analysis including the stated separation on
  `copy_policy`.
- Axis 5 (other media) — searched; oracle pins, live tamper rows (both
  exact test names re-verified), and GLOSSARY anchors re-verified. No
  oracle reads an owner table.
- Axis 6 (omission) — searched; the `DEFAULT_*` reader census
  re-verified (declarations, exports, `_PACKAGE_*` construction args,
  and prose only — zero enforcement readers), all six `copy_policy`
  handouts and every transient authority hold (`schema_error_policy`
  fallbacks, teardown fallback into `degraded_result` field reads,
  `_FALLBACK_ENFORCEMENT`) re-verified. No omission gap.

Definition counts and roles: every challenge count re-checked (ladder
rows 0-1, canonical/handout rows 1 each with the stated refusals,
mutable-field 2, coercion 2, new-iteration-shape 3, per-subject
rewording 1-per-subject, new-bound 0). All hold. One breadth note,
accepted: F1 lists the copy/canonical/`_PACKAGE_*` sites as family
consumers though only the two flavor delegates call `resolve_policy`
directly — a family-scope listing, and the definition counts exclude
them correctly.

Differences reconciled:

(a) F2 shape (one `policy-authority-isolation` family holding
`canonical_policy` + `copy_policy` + `_PACKAGE_*`) vs my two-rule
split. Worker 1 is right. My trace set the shared flat-copy change
aside as implausible; that was wrong — a future collection-typed
bound is plausible, and both mechanisms pass leaves by reference, so
the count-2 challenge is genuine and is the family item's sharpest
question. One contract, two mechanisms, disjoint axes otherwise:
the family grouping stands.

(b) F3 (`hostile-mapping-hardening`, named and left undecided) vs my
R1 (outright rejection). Worker 1 is right. The triple is a genuine
candidate (identical 3-step shape, shared hostile-model reasons to
change, parameterizable variation per DRY principle 1), and a file
item must route a genuine candidate to its holding family, not decide
it. Worker 1's census (third member
`conf.py::_normalize_user_settings`, partial member
`types/base.py::_validate_relation_shapes`, armor asymmetry) exceeds
mine; I re-verified each body claim from HEAD bytes. My R1 is
withdrawn.

(c) Worker-1-found candidates my trace missed (R2 narrowing
derivation, R5 field-name derivation, R6 seal defaults, F3 partial
members). Each re-verified independently from HEAD bytes (`narrowed`
body: `known` + `replace` + narrowing check; `_normalize_user_settings`
body: shape gate + materialize, no key rule; `_reconstructed_value`
recursion with memo; seal policies keyless). All confirmed with
sound contract differences and triggers.

(d) Worker-2-found candidate Worker 1 missed:
`views.py::_resolved_max_request_body_bytes` (HEAD
`9f85b0df26a17e800ec392aa13f6848e07633895`), a constructor >
setting > default ladder adjacent to F1. Rejected, with the contract
difference and trigger recorded in my trace (R2 above): its setting
rung reads `None` as DISABLE while `resolve_policy` reads `None` as
absent at both rungs — a change to either `None` handling must not
move the other. Outcome-neutral (no consolidation owed, no family
wants it) and already durable on-record here, so it is not
revision leverage; a correction index row is supplied for Worker 0
in the verification report.

(e) Nits, no action: L1's parenthetical reads as if both flavors pin
`"a _ProbePolicy"` (they pin their own class names; the branch
coverage itself is verified); F1's consumer-listing breadth (noted
above, accepted).

Rejections R1-R6: each carries a contract difference and a
reconsideration trigger (R4 folds into L1's trigger — accepted,
harmless). Freshness: every Worker-1 blob re-hashed and confirmed,
including both worktree hunt-dirt fingerprints. Two completions
(Worker 2): `optimizer/nested_fetch.py` HEAD
`4d8d37a7f52cf94d2916f17db3a8a21393e28d57` backs R3's strategy-wording
exclusion; `views.py` HEAD (above) backs my R2. Pending execution:
none, correctly — and the sharded/Postgres inapplicability carries
its construction reason. Prose: no process-provenance words (tight
whole-word scan clean; remaining hits are verbs and the required
`Worker 0` protocol name), `path::Symbol` citations throughout, test
tier N/A with zero test edits (window diff vs `c8f821e9` empty on
package/test paths, re-confirmed at verdict time; HEAD still
`5ee86193`). Ruff on the touched path: `ruff format --check` exit 0
(`1 file already formatted`), `ruff check` exit 0 (`No Python files
found ... All checks passed`) — the artifact is `.md`, ruff-excluded
in effect; `check_trailing_commas.py --check` exit 0 (`excluded from
the source-layout rules`). No full-tree `--fix` (banned over
concurrent hunt files).

Defects (Worker 2): none. No contract-row break found anywhere on
the trace; the three near-misses in `## Defects` were re-judged and
are sound (a: `BaseException` must propagate from construction;
b: actual `__name__` inputs `E`/`R`/`_` all answer correctly;
c: mapping-over-dataclass-defaults is the documented contract and
both callers satisfy its precondition). No `## Defects` entry added.

Note for the six citing re-traces: the F2 canonical-copy record —
template/canonical/resolved split plus the per-site
copy/canonical/read classification — is verified site-by-site above
and safe to cite. Standing context (not a defect): the error side
guards each policy read at its use sites while the resource side
canonicalizes once per operation; each rationale is stated at its
own site but the contrast is not stated in one place — the
`extensions/error_policy.py` re-trace may record that as intentional
separation.

Verdict: `verified`. Zero-edit file item; coverage complete (12/12
members homed); assignment correct (3 families, 2 file-local,
6 rejections, all confirmed); matrix discharged (one missed neighbor
resolved as an outcome-neutral rejection on-record); no defect, no
pending execution, no production or test edit.
