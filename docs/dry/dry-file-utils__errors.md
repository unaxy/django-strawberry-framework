# DRY review: `utils/errors.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target `django_strawberry_framework/utils/errors.py` is the flavor-neutral
owner of write-error leaf construction: the single `FieldError` leaf
constructor plus the framework `codes` vocabulary, the flat Django
`ValidationError` mapper, the save-time `IntegrityError` leaf, three
per-condition leaves (relation / null / empty), the dotted error-path
joiner, and — the explicitly separate surface — the coded-`GraphQLError`
`extensions` shape with its three owned codes.

Trace basis is HEAD bytes (`0c0537e2`, blob `3e25e93b`, 443 lines). The
worktree (`6a389474`, 353 lines) is dirty with 8 hunks (65+/155-) that
attribute by content to one concurrent-external change family — the
truth-substrate migration (`_safe_text` / `_unprintable` / `try/except
BaseException` bodies become `truth.*` calls; five private readers fold
into `_is_text_atom` / `_leaf_codes`) plus the `field_name_map` wire-name
feature — importing the untracked `utils/truth.py`, with no
`## Owned changes` ledger row naming this file, the file absent from the
`## Cycle baseline` dirt, and an EMPTY item-scoped diff (worktree blob
equals `ITEM_BASELINE` `15727c1c` on this path). Zero-edit file item:
nothing tracked touched, no consolidation, no plan edit.

Consumer census (whole package, re-derived fresh): `filters/sets.py` and
`filters/base.py` (coded shape + `FILTER_INVALID` / `GLOBALID_*` codes),
`relay.py` (`GLOBALID_INVALID` + shape), `resource_policy.py` (shape for
`ResourceLimitExceeded`), `mutations/resolvers.py` (leaves, both mappers,
four code constants), `forms/resolvers.py` (shared mapper, function-local),
`rest_framework/resolvers.py` (leaves, both mappers, joiner, flattener),
`auth/mutations.py` (null leaf + leaf ctor, function-local),
`utils/write_values.py` (relation leaf via the shared decode spine),
`utils/write_transaction.py` (`conflict_error` via the shared ctor).
Oracle: `tests/utils/test_errors.py` (behavior pins + vocabulary pin +
settings-read pin + adopted G1/G2/G3 singularity gates; dirty in both the
adopted-gate and external-migration senses — both states fingerprinted).
Projections: the [`FieldError` envelope][glossary] glossary entry,
`docs/README.md` write-flavor prose, and the module docstrings stating the
three intentional separations (envelope-vs-extensions, text-vs-relation-id
atoms, generic-vs-M2M null).

Connected behavior examined in full: the target at both states; the
verified `mutation-error-envelope` family artifact (untracked input,
triggers re-checked, censuses re-derived, never trusted);
`mutations/inputs.py` (`FieldError`, `NON_FIELD_ERROR_KEY`); the four
flavor resolvers' leaf/mapper/save-map/decode sites;
`utils/write_values.py` (decode spine, atom set);
`utils/write_transaction.py` (`conflict_error`); `filters/base.py` +
`filters/sets.py` + `relay.py` + `resource_policy.py` coded raise sites;
`extensions/resource_policy.py` + `extensions/error_policy.py` (raise
shape vs correlation shape); `schema.py` + `list_field.py` (inline coded
shape); `testing/client.py` (multipart split); `exceptions.py`
(`_safe_text` / `_unprintable` at HEAD); the oracle test bodies.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Enumerated model / form /
   serializer / auth against leaves, mappers, save-maps, and relation
   decoders. Every flavor composes the shared ctors by name; the model
   M2M-null vs generic-null split, the flat-vs-recursive flattener split,
   and the three save-mapper split each converge onto an already-recorded
   separation (R6/R7 evidence; the flattener split converges via F3).
  No flavor-local second definition.
2. **Sync/async twins.** Inapplicable with reason: all 14 top-level
   functions are sync pure construction (string/dict/enum shaping, no
   ORM, no await point, no execution color); there is no twin and no
   boundary that could separate one.
3. **Derived rather than repeated knowledge.** The 7-code table vs
   literals at raise sites: zero string-literal `codes=` in package
   source (G3 gate + fresh grep); every framework site names a constant
   and only Django/DRF-native values flow through passthrough variables.
   Each leaf message is derived once at its ctor. The `NON_FIELD_ERRORS`
   sentinel is single-sourced at `mutations/inputs.py` and composed by
   import. (`field_name_map` wire-name derivation exists only in the
   external worktree state; not traced.)
4. **Inverse / round-trip pairs.** `join_error_path` (join) and the
   `field_error` segment split are one dotted-path grammar with both
   halves in this file — single owner, two coordinated points (C8). No
   second error-path joiner or splitter package-wide: the
   `testing/client.py` multipart split and the `filters/sets.py` version
   split are different grammars (R2). The surface is construct-only; no
   envelope parser exists (the Django/DRF flatteners are upstream
   adapters terminating in the shared ctor, not inverses).
5. **Contracts restated in another medium.** Oracle (independent):
   `tests/utils/test_errors.py` behavior pins + G1/G2/G3 gates spell
   every message, code, and shape literally. Oracle: per-flavor live
   `test_query` envelope rows. Projection: glossary + `docs/README.md`
   envelope prose. Projection: module docstrings stating the three
   separations (each verified against its body before designing on it;
   one stale word found — D2).
6. **Enforcement by omission.** All four flavors × (leaf kinds, mappers)
   enumerated: model, form, serializer, and auth-register compose the
   shared ctors; the codeless failed-login leaf is the family-cleared
   byte-compatibility contract, not a gap. No flavor hand-builds a leaf.
   The one mis-spelling (auth reaching the ctor through
   `mutations.resolvers` at two HEAD sites) is D1, not an omission.

### Enumeration

Instrument: `git show HEAD:<target>` piped to an AST walk over
`ast.Module.body` (read-only, nothing written). COUNT: 34 nodes —
1 module docstring, 6 imports, 1 `TYPE_CHECKING` block, 12 assigns
(`__all__`, `_TEXT_ATOM_TYPES`, 7 `FIELD_ERROR_CODE_*`, 3 coded
`*_ERROR_CODE`), 14 functions. Every node is homed below; F-rows
converge onto the verified family or name the new one, FL1 carries
mechanics, R-rows record the considered pairs with triggers.

| # | Node | Home |
|---|---|---|
| 0 | module docstring | FL1 |
| 1–6 | `__future__`, `Iterable`, `TYPE_CHECKING`/`Any`, django exceptions, `Promise`, `..exceptions` imports | FL1 |
| 7 | `TYPE_CHECKING` block | FL1 |
| 8 | `__all__` (18 names, all defined) | FL1 |
| 9 | `_TEXT_ATOM_TYPES` | F1 (+ R1 second half) |
| 10–16 | `FIELD_ERROR_CODE_*` (7) | F2 |
| 17–19 | `GLOBALID_INVALID`, `GLOBALID_UNVALIDATABLE`, `FILTER_INVALID` | F9 |
| 20 | `coded_error_extensions` | F9 |
| 21 | `field_error` | F1 |
| 22 | `_str_list` | F1 |
| 23–26 | `_validation_messages`, `_validation_code`, `_validation_leaves`, `_validation_codes` | F3 |
| 27 | `empty_validation_error` | F7 |
| 28 | `null_field_error` | F6 |
| 29 | `_error_dict_entry` | F3 |
| 30 | `relation_field_error` | F5 |
| 31 | `validation_error_to_field_errors` | F3 |
| 32 | `integrity_error_field_errors` | F4 |
| 33 | `join_error_path` | F8 |

Homing totals: 25 nodes in 9 F-rows (8 converges onto verified
`mutation-error-envelope`, 1 new family), 9 nodes in FL1, 8 R-rows
(5 converges onto prior verified verdicts, 3 fresh). Zero unassigned.

### Challenges

Each change posited against HEAD bytes; counts name authoritative
definitions only (consumers, oracles, projections listed, never counted).

| Id | Change posited | Count | Home |
|---|---|---|---|
| C1 | Root rule (`[]` vs `["__all__"]`), sentinel, message/coercion policy | 1 (`field_error` + `_str_list`; type half stays at `mutations/inputs.py` per family F1) | F1 |
| C2 | One framework code value (e.g. `"not_found"` → `"missing"`) | 1 (the constant; 5 importer files follow by import; G3 guards) | F2 |
| C3 | New `ValidationError` shape (bucket kind, metadata read) | 1 (mapper + its 5 private readers, one body family) | F3 |
| C4 | Integrity-fallback message or code | 1 (`integrity_error_field_errors`; 5 call sites follow by call) | F4 |
| C5 | Relation-decode message or shape | 1 (`relation_field_error`; zero per-flavor remnants; 3 flavors route via the shared decode spine) | F5 |
| C6 | Generic null message | 1 (`null_field_error`; M2M wording stays put by recorded contract) | F6 |
| C7 | Detail-less failure message | 1 (`empty_validation_error`; internal + DRF-flattener callers follow) | F7 |
| C8 | Dotted-path separator grammar | 1 owner, 2 coordinated points in the one file (join + split) | F8 |
| C9 | Universal coded-shape key (or `"code"` rename) | 3 (`coded_error_extensions`, `schema.py` inline, `list_field.py` inline) | F9 NEW |
| C10 | Owned-code relocation (e.g. `FILTER_INVALID` to `filters/`) | 1 (the constant; 4 consumer files follow by import) | F9 |
| C11 | Text-atom set growth (e.g. admit `Mapping`) | 1 (this set; relation-id set independent by R1) | R1 |
| C12 | HEAD safe-render policy (fallback rung, leak strip) | 1 (`exceptions.py`; this file composes by name) | R8 |

### Freshness

`HEAD` `0c0537e2` (unmoved at every check);
`ITEM_BASELINE` `15727c1c` (item diff on the target: empty). Blobs are
`git hash-object` worktree / `git rev-parse HEAD:` (8 hex); target censuses
below re-derived at these states.

| Input | Worktree / HEAD | State as cited |
|---|---|---|
| `utils/errors.py` | `6a389474` / `3e25e93b` | HEAD traced; worktree = item baseline, external |
| `mutations/inputs.py` | `840da733` / `fc442047` | `FieldError` + sentinel read both states |
| `mutations/resolvers.py` | `c9cff059` / `043a2d0b` | leaf/mapper/save-map sites read worktree |
| `forms/resolvers.py` | `a1000f21` / `35c282cc` | flattener + decode route read worktree |
| `rest_framework/resolvers.py` | `c49ce3c2` / `0d302782` | flattener + code reader + save map read worktree |
| `auth/mutations.py` | `84183c89` / `d1a59c44` | D1 verified at BOTH states |
| `utils/write_values.py` | `72f132f0` / `d28587c7` | decode spine + atom set read worktree |
| `utils/write_transaction.py` | `4a83f43d` / `eca9ad4d` | `conflict_error` read worktree |
| `filters/base.py` | `3b1dcbce` / `ba52351c` | coded sites read worktree |
| `filters/sets.py` | `e47c6758` / `993e887a` | coded sites read worktree |
| `relay.py` | `e75e2b66` / `c3c5aea5` | coded site read worktree |
| `resource_policy.py` | `cc3f9d80` / `4b69e974` | `ResourceLimitExceeded` shape read worktree |
| `extensions/resource_policy.py` | `0134d83a` / `19e2309d` | raises the shared class; no inline shape |
| `extensions/error_policy.py` | `a1defd39` / `7ee4e9dd` | correlation shape read worktree |
| `schema.py` | `84f2d5aa` / `e6b52335` | bypass verified at BOTH states |
| `list_field.py` | `f5b0183e` / `21380eb7` | bypass verified at BOTH states |
| `testing/client.py` | `b1439443` / `d8feebb2` | multipart split read worktree |
| `exceptions.py` | `93401220` / `e06b0b7f` | helpers present at HEAD, gone worktree |
| `tests/utils/test_errors.py` | `8c763a7a` / `ad939939` | oracle read worktree; dirt characterized |
| `docs/GLOSSARY.md` | `3413edc3` / same | CLEAN; envelope entry is projection |
| `dry-rule-mutation-error-envelope.md` | `792b7b2b` / untracked | trigger input only; censuses re-derived |
| `utils/truth.py` | untracked | external migration substrate; not traced |

Searched populations: whole package for `FieldError\(`, `codes=`,
`"code":`, `coded_error_extensions(`, `relation_field_error(`,
`join_error_path(`, `validation_error_to_field_errors(`,
`integrity_error_field_errors(`, `null_field_error(`,
`empty_validation_error(`, `_relation_field_error`, `field_name_map`,
`_safe_text|_unprintable`, `.split(".")`. Modules excluded on strength
of body: every package module outside the consumer census above (zero
rule tokens over the sweeps).

## Findings

File-item records: contract, sites with roles, challenges with counts,
home. Behavioral proof throughout is `static-reviewed` (zero-edit; every
census below was re-derived fresh against the fingerprinted states —
prior artifacts served as trigger inputs only). No migration, no gate,
no consolidation inside this item.

### F1 — sole leaf ctor + coercion + root rule (CONVERGE verified family)

- **Contract.** One `FieldError` leaf constructor: empty path → the
  `NON_FIELD_ERROR_KEY` sentinel with `path == []`; bare-sentinel whole
  path → `[]` (root rule); nested paths split to segments; `messages`
  and `codes` coerced by the one `_str_list` body over
  `_TEXT_ATOM_TYPES`. Varies on path shape and container kind.
- **Sites + roles.** Definition: `utils/errors.py::field_error` (+
  `_str_list`, `_TEXT_ATOM_TYPES`). Consumers by call: the flat Django
  mapper, the recursive DRF flattener, the form adapter (via the mapper),
  every per-condition wrapper, all four flavor decoders. Oracle: G1 (sole
  `FieldError(` site — re-derived: exactly one code site) + leaf-shape
  behavior pins. Projection: `FieldError` docstring path/codes prose.
- **Challenges.** C1 → 1; C11 → 1. The `FieldError` type half stays at
  `mutations/inputs.py` per the family's ownership split (dependency
  direction wins; the function-local import is the blessed seam).
- **Home.** CONVERGE onto verified `mutation-error-envelope` F1 on fresh
  evidence (T-construct + T-code triggers re-checked, both still hold).

### F2 — framework `codes` vocabulary table (CONVERGE verified family)

- **Contract.** The 7 wire codes a client branches on; open at the
  ctor (Django/DRF codes flow through unvalidated); framework
  `"invalid"` deliberately collides with Django's/DRF's.
- **Sites + roles.** Definition: the 7 `FIELD_ERROR_CODE_*` constants.
  Consumers by name (this module internally + 5 importer files, all
  verified): model leaves, serializer leaves + truncation, auth password
  leaves, unencodable-text leaf, conflict leaf, integrity leaf. Oracle:
  vocabulary pin + G3 (zero
  literal `codes=` — re-derived fresh) + `test_conflict_code...` ctor
  pin. Django/DRF passthroughs (`codes=codes`, `codes=leaf_codes`) are
  upstream vocabularies correctly not mirrored.
- **Challenges.** C2 → 1; C10-shape reasoning applies (followers are
  imports, uncounted).
- **Home.** CONVERGE onto verified `mutation-error-envelope` F1 code
  table on fresh evidence.

### F3 — flat Django mapper + private readers (CONVERGE verified family)

- **Contract.** `error_dict` branch (per-field buckets;
  `NON_FIELD_ERRORS` → sentinel; per-leaf messages + truthy codes) with
  `error_list`/`messages` fallback; empty buckets → the empty leaf.
  HEAD signature is `(exc)`; the worktree `field_name_map` parameter is
  external dirt, not traced.
- **Sites + roles.** Definition: `validation_error_to_field_errors` +
  `_validation_messages`, `_validation_code`, `_validation_leaves`,
  `_validation_codes`, `_error_dict_entry` (one body family at HEAD).
  Consumers: model `full_clean` tail, form adapter ("No parallel
  mapper"), serializer Django-`save()` arm. Oracle: mapper behavior pins
  at both states (sentinel keying, empty-envelope, lazy) plus the
  worktree-only params-mismatch propagation pin.
- **Challenges.** C3 → 1.
- **Home.** CONVERGE onto verified `mutation-error-envelope` F1/R1
  (flat-vs-recursive distinct behavior) on fresh evidence.

### F4 — save-time integrity leaf (CONVERGE verified family)

- **Contract.** The honest-superset `"A database constraint was
  violated."` + `constraint` code on the sentinel for the residual
  `IntegrityError` after validation; no cross-backend field mapping
  claimed.
- **Sites + roles.** Definition: `integrity_error_field_errors`.
  Consumers: model tail (4 sites), serializer three-`except` save map.
  Oracle: live constraint rows per flavor.
- **Challenges.** C4 → 1.
- **Home.** CONVERGE onto verified `mutation-error-envelope` F1 on fresh
  evidence.

### F5 — uniform relation-decode leaf (CONVERGE verified family)

- **Contract.** Wrong-model / hidden / missing / uncoercible ids collapse
  to one field-keyed shape on the GraphQL wire name (no existence leak).
- **Sites + roles.** Definition: `relation_field_error`. Consumers: the
  shared `write_values` decode spine (all three flavors route through
  it — the docstring's "DIRECTLY" is stale, D2); zero per-flavor
  `_relation_error` remnants package-wide. Oracle: relation
  `not_found` live rows.
- **Challenges.** C5 → 1.
- **Home.** CONVERGE onto verified `mutation-error-envelope` R1
  (per-condition wrappers stay) on fresh evidence; R1 trigger (two
  wrappers, one condition) checked, not met.

### F6 — generic explicit-null leaf (CONVERGE verified family)

- **Contract.** "This field cannot be null." + `null` code for a
  non-nullable field arriving explicitly null; the M2M
  clear-signal wording stays separate by recorded contract.
- **Sites + roles.** Definition: `null_field_error`. Consumers: model
  tail (2 sites), auth register password. Deliberate sibling (not a
  fork): `mutations/resolvers.py::_relation_null_error`. Oracle:
  null-leaf shape pin.
- **Challenges.** C6 → 1.
- **Home.** CONVERGE onto verified `mutation-error-envelope` R1 on fresh
  evidence; the owner-recorded M2M separation stands.

### F7 — detail-less failure leaf (CONVERGE verified family)

- **Contract.** Fail-closed leaf for a validation failure carrying no
  (or unreadable) details; public so the DRF flattener composes it
  instead of re-typing the pair.
- **Sites + roles.** Definition: `empty_validation_error`. Consumers:
  the flat mapper's empty buckets + the DRF flattener's empty payload.
  Oracle: root/named empty-leaf shape pins.
- **Challenges.** C7 → 1.
- **Home.** CONVERGE onto verified `mutation-error-envelope` R1 on fresh
  evidence.

### F8 — dotted error-path grammar, join + split (CONVERGE verified family)

- **Contract.** `join_error_path` joins (`items` + `0` → `items.0`;
  empty prefix yields the bare segment so root `__all__` stays bare
  while nested becomes `items.0.__all__`); `field_error` splits the
  dotted key back to segments. One grammar, two halves, one file.
- **Sites + roles.** Definitions: `join_error_path` + the split inside
  `field_error` (single owner). Consumers: DRF decode + flattener (6
  call sites at both states: HEAD `rest_framework/resolvers.py`
  `:331,387,524,528,1655,1750`). No second error-path joiner (forms
  is flat) or splitter (R2). Oracle: join-variation pins +
  structured-path leaf pins.
- **Challenges.** C8 → 1 owner (2 coordinated points, same file).
- **Home.** CONVERGE onto verified `mutation-error-envelope` F1 (path
  half of leaf construction) on fresh evidence.

### F9 — coded `GraphQLError` extensions shape + owned codes (NEW FAMILY)

- **Contract + variation.** Every coded framework rejection carries
  `extensions == {"code": <CODE>, **detail}` so a client branches
  without parsing prose. Varies on code (per-subsystem vocabulary) and
  detail keys. The placement rule: a subsystem code lives here or stays
  at its owner and is passed in (`RESOURCE_LIMIT_*` stays at
  `resource_policy.py` by that rule).
- **Sites + roles.** Definition (shape): `coded_error_extensions`.
  Definitions (bypass spellings of the same shape): `schema.py`
  (`extensions={"code": SCHEMA_CONFIGURATION_ERROR_CODE}`, HEAD:721)
  and `list_field.py` (`{"code": "LIST_ARGUMENT_INVALID", ...}` with
  conditional keys, HEAD:313) — verified at BOTH states. Vocabulary
  definitions: the 3 owned constants. Consumers by name (9 sites):
  `filters/sets.py` (2), `filters/base.py` (5), `relay.py` (1),
  `resource_policy.py` (1, via `ResourceLimitExceeded`, which the
  extension layer raises, never rebuilds). Oracle: coded-shape pins.
  No import cycle either way (`utils/errors.py` never imports `schema`
  or `list_field`), so composing by name is feasible; the family item
  proves it.
- **Challenges.** C9 → 3 (the duplication); C10 → 1; C2-analog for the
  owned codes → 1 each (named-constant consumers only; prose mentions
  in `filters/base.py` docstrings are projections).
- **Owner + lifetime.** Candidate owner: `coded_error_extensions`
  (already the shape owner; narrowest module every consumer imports).
  Lifetime: pure construction, nothing stored. The family item decides
  the migration (compose-by-name at the 2 bypasses + a would-be gate
  with negative control) and whether `LIST_ARGUMENT_INVALID` graduates
  to a named constant; that literal is single-sited, so it is a naming
  note, not a second definition.
- **Coupling.** None (zero-edit file item; the family item lands any
  migration with its own tests).
- **Freshness.** Target HEAD `3e25e93b` (shape + vocabulary byte-identical
  in worktree `6a389474` — no hunk touches F9 lines); bypasses verified
  at both states per the table above.
- **Home.** NEW FAMILY `coded-error-extensions-shape` (index row + family
  item owed; Worker-0 queues). R3-converge note: this family is scoped
  to the extensions side only — unification with envelope codes stays
  rejected per R5.

### FL1 — module mechanics (FILE-LOCAL)

- **Contract.** The 18-name `__all__` (7 + 3 + 8; every name defined,
  13 pinned by the vocabulary test, the rest by behavior), the module
  docstring (leaf catalog + layering rule + vocabulary history), the
  import block (django-only at module time; `FieldError` /
  `NON_FIELD_ERROR_KEY` function-local per the blessed seam;
  `TYPE_CHECKING` import), and the HEAD `..exceptions` composition
  import.
- **Challenges.** Manifest membership → 1 (`__all__`); layering seam →
  1 (the function-local import, mirrored by auth/forms/serializer
  callers as consumers of the seam, not definitions).
- **Home.** FILE-LOCAL: no second site defines any of these (the
  `test_errors.py` settings-read pin guards the configuration-free
  half). Challenge C12 evidence lives here; the rule half converges
  via R8.

### R1 — text atoms vs relation-id atoms (REJECTED, fresh)

Message-container atoms (`_TEXT_ATOM_TYPES`: str/bytes/bytearray/
memoryview/Promise) vs relation-id-container atoms
(`write_values.py::RELATION_ID_ATOM_TYPES`, which adds `Mapping` — a
container, just never that one). Shared form considered: one atom tuple
— owns the overlap, but the write path must reject mappings while the
message path must render mapping payloads; one set cannot serve both
contracts. Separation stated bilaterally at both owners; C11 confirms
independent change. Trigger: one set subsuming the other's contract
(e.g. the write path rendering mappings as messages).

### R2 — error-path split vs multipart/version splits (REJECTED, fresh)

`field_error`'s error-path split vs `testing/client.py`'s multipart
object-path split (spec-envelope validation, rejects empty segments)
vs `filters/sets.py`'s version-string split. Shared form considered: a
dotted-path walker — the three grammars validate, structure, and parse
different languages with different failure modes; sharing the walker
couples them with no change obligation relieved. Trigger: a genuinely
shared dotted-path grammar introduced with one contract.

### R3 — coded shape vs correlation extensions (REJECTED, fresh)

`coded_error_extensions` (`{"code", ...}`, machine rejection code) vs
`extensions/error_policy.py`'s `{correlation_key: id}` (per-error
support identifier, deliberately codeless so masked errors stay
indistinguishable). Different layers, different readers, different
indistinguishability contracts. Trigger: the correlation payload
gaining a client-branched `"code"` key.

### R4 — Django vs DRF code readers (REJECTED, converge)

HEAD `_validation_codes` (Django `error_list` flattening + `None`-drop)
vs `rest_framework/resolvers.py::_error_detail_codes` (DRF `ErrorDetail`
list `.code` reads, plain-`str` drop). Different input contracts, same
verdict as the verified file: CONVERGE with File
`rest_framework/resolvers.py` `drf-vs-django-code-readers` on fresh
evidence (HEAD bodies re-read; trigger unchecked-tripped: no unified
reader introduced).

### R5 — envelope codes vs extension codes (REJECTED, converge)

In-band `FieldError.codes` vs top-level `extensions.code`: different
clients at different layers. CONVERGE with verified
`mutation-error-envelope` R3 on fresh evidence — R3 trigger (a client
contract reading both as one vocabulary) checked across tests, glossary,
and `docs/README.md`: none exists; the media keep them apart.

### R6 — per-condition wrappers (REJECTED, converge)

Named ctors stay: one condition per message+code+path, distinct reasons
to change; the shared parametrized form already exists (`field_error`).
CONVERGE with verified `mutation-error-envelope` R1 on fresh evidence
(R1 trigger checked: null/relation/not-found/invalid-id/protected/
conflict/constraint/validation/login-failure still distinct; F5–F7 are
this file's instances).

### R7 — three save-mappers (REJECTED, converge)

Model `save_or_field_errors` tail vs serializer three-`except` save map
vs form tail: separate flavor contracts that all terminate in the shared
leaves (`integrity_error_field_errors`, `validation_error_to_field_errors`).
CONVERGE with verified File `rest_framework/resolvers.py`
`three-branch-save-mapper-vs-save-or-field-errors` on fresh evidence
(re-censused on the bodies-owned basis: model 1, serializer 1 with 3
arms, form 0 — form reuses the shared tail and contributes only 1
mapper call, not a mapper body).

### R8 — safe-renderer composition (REJECTED, converge)

HEAD errors.py renders through `exceptions.py::_safe_text` /
`_unprintable` by import (9 call sites in 5 calling functions —
HEAD:157,197,212,216,217,335,381,441,442 — 1 import); no inline fallback
ladder, no second policy. CONVERGE with verified File `exceptions.py`
C2/C5 compose-by-name on fresh evidence (C12 → 1 at HEAD bytes). The
worktree `truth.*` re-spelling is the external migration (O1), not a
second definition under this item.

## Defects

Non-duplication defects found while tracing, each with its owner. Both
are minor, behavior-neutral, and present at HEAD; closeout homing owed.

### D1 — auth reaches the leaf ctor through `mutations.resolvers` (HEAD)

`auth/mutations.py` calls `resolvers.field_error` at two sites (HEAD:545
incorrect-credentials leaf, HEAD:1143 register `validate_password` leaf;
worktree:496/1103). The register function already imports `field_error`
from `utils/errors.py` directly (HEAD:1119) and calls it directly at
HEAD:1126, while the same function's :1143 site uses the `resolvers.`
spelling; the :545 function has no direct import at all. Contract row:
the target module docstring's layering rule —
promotion exists precisely so "the model mutation resolver is not the
utility module" — restated in `null_field_error`'s docstring as the
layering it "exists to undo". Same function object, so behavior-neutral;
a layering wart, not a fork. Wire input: any login/register mutation.
Owner: `auth/mutations.py`. Fix shape (not applied here): import from
`utils/errors.py` at both sites.

### D2 — `relation_field_error` docstring "DIRECTLY" is stale (HEAD + worktree)

The docstring claims the 036/038/039 decoders "call this DIRECTLY". At
HEAD bytes all three flavors route through the shared `write_values`
decode spine (model + serializer via `decode_visible_relation_ids`, form
via `decode_visible_relation`); no flavor calls the leaf directly. The
parenthetical's true claim — the per-flavor `_relation_error` aliases
were folded away (zero remnants package-wide) — stands; only the
one-word call-shape claim contradicts the call graph. Owner:
`utils/errors.py` (own docstring). Fix shape (not applied here): "route
through the shared decode spine" with the existing no-aliases evidence.

### Observed, not homed

- **O1 — worktree truth-migration dirt (external).** All 8 hunks
  (65+/155-) attribute to the concurrent truth-substrate migration +
  `field_name_map` feature: (1) import → `from . import truth`;
  (2) `field_error` path render; (3) `_str_list` rewrite +
  `_is_text_atom`/`_leaf_codes`, deleting 4 private readers;
  (4) `_error_dict_entry` deletion; (5) `relation_field_error` render;
  (6–7) mapper signature + body; (8) `join_error_path` renders. No
  ledger row, absent from cycle-baseline dirt, importer `utils/truth.py`
  untracked, oracle-test dirt mirrors it (153+/265-, hostile-degradation
  pins become propagation pins). Left untouched; F9 lines byte-identical
  in both states.
- **O2 — family fingerprint vs worktree drift.** The verified family's
  `utils/errors.py` pin (`3e25e93b`) equals HEAD, which this item
  traced; the worktree has since drifted externally. Closeout re-hash
  owed; no reopen by this item (HEAD bytes unchanged).
- **O3 — oracle gates intact in worktree.** The adopted G1/G2/G3 gates
  and vocabulary/settings pins are present and consistent with the
  worktree code; the dirt removed only hostile-object behavior pins
  that the migration's propagation contract supersedes. Both oracle
  states fingerprinted above.

## Judgment

Zero-edit file item, ready for verification. 34/34 enumeration homed:
8 converges onto verified `mutation-error-envelope` (family triggers
T-construct, T-code, R1, R3 re-checked fresh, none tripped; T-shape and
R2 touch no line of this target — T-shape holds by fresh HEAD re-check
(no `errors:` field outside `build_payload_type`) plus the live
SDL/per-flavor rows),
1 new family
(`coded-error-extensions-shape`: C9 → 3 over the shape owner + 2
HEAD-verified bypasses), 1 file-local mechanics row, 8 rejections (5
converging onto prior verified verdicts, 3 fresh with triggers), 2
minor HEAD defects for closeout homing, 3 observed-not-homed notes. No
pending execution (all proofs `static-reviewed`; no source-mutating run
was needed or made). Nothing tracked touched; item-scoped diff empty;
HEAD `0c0537e2` unmoved.

## Index rows for Worker-0

Proposed transcriptions for `## Responsibility index` (20 rows) and one
`## Families` item. Statuses follow the established vocabulary;
`consolidated` marks a converge onto an already-single verified home.

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `errors-sole-leaf-ctor` | `django_strawberry_framework/utils/errors.py::field_error` (CONVERGE with verified `mutation-error-envelope` F1 on fresh evidence; T-construct + T-code re-checked) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Family `mutation-error-envelope` | consolidated |
| `errors-framework-code-table` | `django_strawberry_framework/utils/errors.py::FIELD_ERROR_CODE_INVALID` (table of 7; CONVERGE with verified `mutation-error-envelope` F1 on fresh evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/utils/write_values.py`, `django_strawberry_framework/utils/write_transaction.py` | Family `mutation-error-envelope` | consolidated |
| `errors-flat-django-mapper` | `django_strawberry_framework/utils/errors.py::validation_error_to_field_errors` (CONVERGE with verified `mutation-error-envelope` F1/R1 on fresh evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/rest_framework/resolvers.py` | Family `mutation-error-envelope` | consolidated |
| `errors-integrity-leaf` | `django_strawberry_framework/utils/errors.py::integrity_error_field_errors` (CONVERGE with verified `mutation-error-envelope` F1 on fresh evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/rest_framework/resolvers.py` | Family `mutation-error-envelope` | consolidated |
| `errors-relation-leaf` | `django_strawberry_framework/utils/errors.py::relation_field_error` (CONVERGE with verified `mutation-error-envelope` R1 on fresh evidence; R1 trigger checked) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/utils/write_values.py` | Family `mutation-error-envelope` | consolidated |
| `errors-null-leaf` | `django_strawberry_framework/utils/errors.py::null_field_error` (CONVERGE with verified `mutation-error-envelope` R1 on fresh evidence; M2M separation recorded at owner stands) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Family `mutation-error-envelope` | consolidated |
| `errors-empty-leaf` | `django_strawberry_framework/utils/errors.py::empty_validation_error` (CONVERGE with verified `mutation-error-envelope` R1 on fresh evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/rest_framework/resolvers.py` | Family `mutation-error-envelope` | consolidated |
| `errors-dotted-path-grammar` | `django_strawberry_framework/utils/errors.py::join_error_path` (join half; split half in `::field_error`; CONVERGE with verified `mutation-error-envelope` F1 on fresh evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/rest_framework/resolvers.py` | Family `mutation-error-envelope` | consolidated |
| `coded-error-extensions-shape` | `django_strawberry_framework/utils/errors.py::coded_error_extensions` (shape + 3 owned codes + placement rule; bypasses at `schema.py` + `list_field.py`) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/schema.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/relay.py`, `django_strawberry_framework/resource_policy.py` | Family `coded-error-extensions-shape` | open |
| `errors-module-mechanics` | `django_strawberry_framework/utils/errors.py` (`__all__` + docstring + import block + function-local seam) | `django_strawberry_framework/utils/errors.py` | File `utils/errors.py` | file-local |
| `errors-text-atoms-vs-relation-id-atoms` | `django_strawberry_framework/utils/errors.py::_TEXT_ATOM_TYPES` (rejection recorded here; bilateral separation, Mapping contract differs) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/utils/write_values.py` | File `utils/errors.py` | rejected |
| `errors-path-split-vs-multipart-split` | `django_strawberry_framework/utils/errors.py::field_error` (rejection recorded here; three dotted grammars, three contracts) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/filters/sets.py` | File `utils/errors.py` | rejected |
| `errors-coded-shape-vs-correlation-shape` | `django_strawberry_framework/utils/errors.py::coded_error_extensions` (rejection recorded here; rejection code vs codeless support identifier) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/extensions/error_policy.py` | File `utils/errors.py` | rejected |
| `errors-django-vs-drf-code-readers` | `django_strawberry_framework/utils/errors.py::_validation_codes` (rejection recorded here; CONVERGE with verified File `rest_framework/resolvers.py` `drf-vs-django-code-readers` on fresh evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/rest_framework/resolvers.py` | File `utils/errors.py` | rejected |
| `errors-envelope-vs-extension-codes` | `django_strawberry_framework/utils/errors.py` (rejection recorded here; CONVERGE with verified `mutation-error-envelope` R3 on fresh evidence; R3 trigger checked) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/inputs.py` | File `utils/errors.py` | rejected |
| `errors-per-condition-wrappers` | `django_strawberry_framework/utils/errors.py::null_field_error` (rejection recorded here; CONVERGE with verified `mutation-error-envelope` R1 on fresh evidence; R1 trigger checked) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/utils/write_transaction.py` | File `utils/errors.py` | rejected |
| `errors-three-save-mappers` | `django_strawberry_framework/utils/errors.py::integrity_error_field_errors` (rejection recorded here; shared leaf both mappers compose; CONVERGE with verified File `rest_framework/resolvers.py` `three-branch-save-mapper-vs-save-or-field-errors` on fresh evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py` | File `utils/errors.py` | rejected |
| `errors-safe-renderer-composition` | `django_strawberry_framework/utils/errors.py::field_error` (rejection recorded here; CONVERGE with verified File `exceptions.py` C2/C5 compose-by-name on fresh HEAD-byte evidence) | `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/exceptions.py` | File `utils/errors.py` | rejected |
| `errors-auth-resolvers-spelling` | `django_strawberry_framework/auth/mutations.py` (D1: `resolvers.field_error` double-spelling at 2 HEAD sites; closeout homing owed) | `django_strawberry_framework/auth/mutations.py` | File `utils/errors.py` | defect-routed |
| `errors-directly-docstring-word` | `django_strawberry_framework/utils/errors.py::relation_field_error` (D2: stale "DIRECTLY" vs shared-spine call graph; closeout homing owed) | `django_strawberry_framework/utils/errors.py` | File `utils/errors.py` | defect-routed |

`## Families` item owed: `- [ ] Family `coded-error-extensions-shape` —
[dry-rule-coded-error-extensions-shape.md][rule-new]
— no artifact on disk; undispatched (named by File `utils/errors.py` F9;
owner candidate `utils/errors.py::coded_error_extensions`; members
`schema.py` + `list_field.py` bypasses, consumers `filters/base.py`,
`filters/sets.py`, `relay.py`, `resource_policy.py`; queue after the 11)`.

## Independent verification (Worker-2)

Expectation-first trace, formed from HEAD bytes (`0c0537e2`,
`django_strawberry_framework/utils/errors.py` blob `3e25e93b`, 443 lines),
the verified `mutation-error-envelope` family artifact (triggers only),
and whole-package HEAD sweeps (`git grep ... HEAD`) BEFORE reading
`## Findings`. No `worker-memory/` read. Worktree blob `6a389474`
(353 lines) throughout; item-scoped diff
(`git diff 15727c1c -- <target>`) EMPTY at every check — zero-edit
confirmed mechanically, all 8 hunks predate the item.

Own trace. Role: flavor-neutral write-error leaf construction —
`field_error` + `_str_list` + atoms, 7-code table, flat Django mapper +
5 private readers, 3 per-condition leaves, integrity leaf, dotted-path
join, coded-extensions shape + 3 codes, module mechanics. Own AST walk
over `git show HEAD:` bytes: 34 nodes (docstring, 6 imports, 1
`TYPE_CHECKING`, `__all__`, `_TEXT_ATOM_TYPES`, 7 + 3 constants, 14
functions) — identical member-for-member to the artifact's table.
Owners I would choose: envelope type at
`mutations/inputs.py::FieldError`, leaf construction + code table here
(family-confirmed split, dependency direction wins); coded shape at
`coded_error_extensions` as a NEW family IFF a second spelling exists —
found two (`schema.py:721`, `list_field.py:312-322`), so warranted.
Defects found independently before reading: auth `resolvers.field_error`
at HEAD `auth/mutations.py:545,1143` vs the direct import at `:1119`
(layering wart, owner `auth/mutations.py`); "DIRECTLY" stale (zero
direct `relation_field_error` callers outside `write_values.py`; model +
serializer via `decode_visible_relation_ids`, form via
`decode_visible_relation` at `forms/resolvers.py:200`; zero
`_relation_error` remnants) — owner this file.

Trigger re-checks, all at HEAD, all hold (none tripped): T-construct
(exactly one code `FieldError(` site at `utils/errors.py:171` + one
Django-`FieldError` docstring mention); T-code (zero string-literal
`codes=`; all constants or passthrough vars); T-shape (no `errors:`
payload field outside `build_payload_type`); async envelope ctor
(none; `_channels_logout` is the R2-covered observation path); slot
derivation (one def at `mutations/inputs.py:910`, rest compose by
name); split/join (one owner; `testing/client.py:338` multipart and
`filters/sets.py:439` version splits are different grammars); R1
(wrapper set distinct, no collapse); R2 (exactly the 3 known
model-less `payload_cls(ok=...)` sites); R3 (tests read each
`extensions["code"]` vocabulary separately; no unified reader);
`drf-vs-django-code-readers` (no unified leaf shape);
three-branch-save-mapper (still 3 except arms vs 1-class
`save_or_field_errors`; form owns zero mapper bodies, reuses the
shared tail at `forms/resolvers.py:509,540`); exceptions C2/C5
(single `..exceptions` import, no local fallback ladder). All 19
artifact HEAD fingerprints re-derived byte-exact. F9 bypass census is
COMPLETE at HEAD (whole-package `"code":` sweep: code sites only at
the owner, `schema.py:721`, `list_field.py:313`; rest is prose).

Reconciliation. AGREE on every verdict: enumeration 34/34 homed, zero
unassigned; hunk attribution (my independent 8-hunk content map matches
O1 exactly; externality confirmed via untracked `utils/truth.py`, no
`## Owned changes` row, absence from `## Cycle baseline` dirt, empty
item diff, cross-file `field_name_map` feature in worktree); F1–F8
converges onto the verified family (homes fit, evidence fresh);
F9 ENDORSED as new family `coded-error-extensions-shape` (C9 → 3 is a
real count>1; placement rule + R3-compat + single-sited-literal notes
sound); R1–R8 verdicts (3 fresh triggers well-formed, 5 converges with
triggers genuinely re-checked); D1 + D2 substance, defect bar (DRY.md
listed shapes: layering-claim-contradicted-by-imports,
docstring-contradicting-call-graph), and owners; FL1; O1–O3 substance
(worktree gates present: `_OWNER_SYMBOLS` + 3 `test_envelope_*`; test
dirt exactly 153+/265-); matrix discharge incl. the axis-2
inapplicability reason; zero-edit/no-execution/AGENTS.md-prose
standing-prose compliance (per-cycle scratch conventions; scaffold
intact).

DIFFER on record accuracy only — 7 blemishes, none verdict-moving,
each reproducible below. Per the cycle's record-accuracy bar this is
`revision-needed`, not `verified`: resubmission to the SAME W1 context
(no re-trace; judgments all stand; fix the prose, keep the verdicts).

1. F8 "(4 join sites)": actually 6 call sites at BOTH states —
   `git show HEAD:django_strawberry_framework/rest_framework/resolvers.py | grep -n 'join_error_path('`
   → 331, 387, 524, 528, 1655, 1750 (worktree `grep -c` also 6; no
   partition yields 4).
2. R7 "(model 4+1, serializer 3-arm, form 1)": form owns ZERO
   save-mapper bodies (reuses the shared tail at
   `forms/resolvers.py:509,540`) plus 1 mapper call (`:429`) — "form
   1" is wrong under any consistent basis; recast the census on one
   basis (bodies vs branches vs call sites) and state it.
3. Matrix axis 1 "(R6/R7/R-f evidence)": "R-f" dangles (no such
   row; R-rows are R1–R8) — name the intended row.
4. Judgment "(the former stays pinned by gate G2)": G2 pins
   one-def-each (family artifact: "one def each of the five owner
   symbols"), not T-shape — correct the attribution (T-shape holds by
   fresh HEAD re-check + live SDL/per-flavor rows).
5. R8 "5 call shapes": 9 call sites in 5 calling functions
   (HEAD `utils/errors.py:157,197,212,216,217,335,381,441,442`;
   4 syntactic shapes) — "functions", not "shapes".
6. D1 "two lines above one of them": wrong at both states
   (direct import HEAD `auth/mutations.py:1119`, site at `:1143`;
   the `:545` function has no direct import at all) — restate as
   same-function direct import + direct use vs `resolvers.` spelling.
7. F3 oracle "(... params-mismatch propagation)": that pin name is
   worktree-only (`grep mismatch` at HEAD oracle is empty) — scope
   oracle citations by state.

HEAD movement check: `0c0537e2` at dispatch and at every W2 check
(first to last); worktree blob `6a389474` stable; no new ledger row
could have landed (plan untouched by W2 per dispatch). No new
Worker-2 defects. Verdict: `revision-needed` on record accuracy; all
judgments stand pending the one-word-class fixes above.

## Independent re-verification (Worker-2) — pass 2, verdict `verified`

Re-pass on resubmission `ready-for-verification/2` (same W2 context).
Gates: HEAD `0c0537e2` unmoved, target blob `6a389474` stable, item
diff vs `ITEM_BASELINE` still empty — pass-1 HEAD evidence stands
without re-trace. All 7 record fixes reproduce mechanically: (1) F8
now cites 6 join sites `:331,387,524,528,1655,1750` at both states
(re-grepped both); (2) R7 recast on the bodies-owned basis (model 1,
serializer 1 with 3 arms, form 0 + 1 mapper call); (3) "R-f" resolved
to "(R6/R7 evidence; the flattener split converges via F3)"; (4)
Judgment drops the G2 misattribution (T-shape by fresh HEAD re-check
+ live rows); (5) R8 cites 9 sites in 5 functions with exact HEAD
lines (re-grepped); (6) D1 restated with exact HEAD lines
1119/1126/1143 + the :545 no-import note (re-read); (7) F3 oracle
state-scoped (HEAD pins re-grepped present both states; `mismatch`
0 at HEAD, params pin worktree-only). Nothing else moved: W1 verdict
prose stable (8 converges, C9 → 3, 20 rows), pass-1 W2 section
byte-intact, no stale string outside its historical quote. No new
defects. Verdict: `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary]: ../GLOSSARY.md
[rule-new]: dry-rule-coded-error-extensions-shape.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

