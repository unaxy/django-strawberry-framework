# DRY review: `utils/imports.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target `django_strawberry_framework/utils/imports.py` is the package's single
optional-import owner: four import-handling members (best-effort, loaded-only,
strict, raising-guard), one private hostile-input normalizer, two install-hint
floor constants, and an exact-set leaf manifest. Every production consumer
reaches it by name; the trace below proves each of the four members has exactly
one authoritative definition and records the one adoption into an open family.

Cleanliness verified before tracing: worktree bytes hash to `291ecedd`
(`git hash-object`), identical to `HEAD:django_strawberry_framework/utils/imports.py`
(`git rev-parse`), 139 lines, `git status --short` is silent for the target
(this artifact path itself is the expected new `??` untracked file),
`git diff 010323ee -- <target>` is empty, and no
[plan][plan] `## Owned changes` row names the file (grep over plan lines
1142–1206). HEAD is `0c0537e2`, unmoved since dispatch. Nothing tracked was
touched; all bytes traced are HEAD bytes.

Production consumer census (11 files, every import statement read):

- `import_attr_if_importable`: `registry.py::_clear_if_importable` (per-type
  co-clear), `utils/inputs.py::_safe_import` (attr-lenient wrapper for the
  partial-load lifecycle), `types/converters.py` (`_ARRAY_FIELD_CLS`,
  `_HSTORE_FIELD_CLS` module-level sentinels), `optimizer/nested_planner.py`
  (`_PostgresBTreeIndex` module-level sentinel feeding `_BTREE_INDEX_TYPES`).
- `loaded_attr`: `types/finalizer.py` phase-2.5 auth bind (single call site).
- `import_attr`: `mutations/sets.py::resolver_seams` (four generated-body call
  sites, one seam).
- `require_optional_module`: `rest_framework/__init__.py::require_drf`,
  `routers.py::require_channels`, `auth/sessions.py::require_channels`,
  `middleware/debug_toolbar.py::require_debug_toolbar`, and two direct calls in
  `keyset.py::_cursor_crypto_types` under one `_CRYPTOGRAPHY_INSTALL_HINT`.
- `CHANNELS_FLOOR`: interpolated into four hints (`routers.py` three,
  `auth/sessions.py` one). `STRAWBERRY_FLOOR`: interpolated into one hint
  (`routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT`).

## Verification

### Enumeration

Instrument: `ast.Module.body` of the target at blob `291ecedd`. 13 members:
1 module docstring, 4 import statements (`__future__`, `importlib`, `sys`,
`typing.Any`), and 8 named top-level symbols. Every named symbol is homed
below; imports are machinery with no rule (stdlib-only, no package import,
which is itself the layering fact R1 relies on).

| # | Symbol | Kind | Home |
|---|---|---|---|
| 1 | `__all__` | manifest, 6 names | FL6 file-local |
| 2 | `CHANNELS_FLOOR` | constant `"4.3.2"` | FL5 file-local |
| 3 | `STRAWBERRY_FLOOR` | constant `"0.316.0"` | FL5 file-local |
| 4 | `_plain_text` | private helper | FL4 file-local (+ R1 rejected twin) |
| 5 | `import_attr_if_importable` | public helper | FL1 file-local (+ advisory consumer edge) |
| 6 | `loaded_attr` | public helper | FL2 file-local |
| 7 | `import_attr` | public helper | FL3 file-local |
| 8 | `require_optional_module` | public helper | F1 ADOPT into open `soft-dependency-require-guard` |

Count check: 8 named symbols = 1 adoption + 6 file-local homes + 0 unassigned
(R1–R11 are pair verdicts about these same symbols, not additional members).

### Matrix

1. **Cross-flavor policy mirroring.** Swept every sibling import-handling shape
   in the package: `management/commands/_imports.py` (R2, rejected: CommandError
   translation for CLI paths), `sets_mixins.py::resolve_lazy_class` (R3,
   rejected: two-attempt absolute-then-module-relative ladder with factory arms),
   the five upstream-patch `except ImportError` skip-guards (R4, converge: owned
   by open family `upstream-patch-lifecycle`), Django `import_string` strict
   sites for consumer-configured paths (`middleware/request_body.py` entry
   resolution, `utils/sessions.py` session-engine resolution — Django's own
   helper, strict by contract, no optional semantics), and the root
   `__getattr__` direct `importlib` use (R6, converge: verified File
   `__init__.py` rejection stands).
2. **Sync/async twins.** No async surface: all four members are synchronous
   import calls with no await point, no executor, no twin. Nothing to compare.
3. **Derived rather than repeated knowledge.** The two floors are written
   exactly twice each (constant + own `pyproject.toml` row) and pinned by the
   `tests/test_ci_governance.py` comparators, which fail on drift; `__all__`
   names exactly the 6 public symbols with zero star-import consumers
   (package-wide grep for `utils.imports import *`: no hits), so the manifest
   cannot drift from the surface unnoticed; the module docstring's five-bullet
   roster over six call sites was re-verified live (registry, finalizer, inputs,
   converters, nested_planner, require_* guards — 6/6 present).
4. **Inverse / round-trip pairs.** None: the members are one-way lookups with
   no encode/decode, pack/unpack, or build/parse half. Inapplicable with no
   such surface.
5. **Contracts restated in another medium.** Oracles: `tests/utils/test_imports.py`
   (16 tests, independent — hand-built `ModuleType` fakes, hostile `str`
   subclasses, a no-memoize pin via monkeypatched `importlib`, sentinel-shape
   pins; none read from the owner). Projections: the [glossary][glossary]
   `require_optional_module` entry (stale "planned / non-goal" wording already
   ruled not-a-defect at verified File `rest_framework/__init__.py` — converge,
   no re-home), spec-041/spec-042 contract sources, `tests/_soft_dependency.py`
   (shared absence discipline consuming the ImportError-only reframing
   contract), `pyproject.toml` floor rows + CI comparators (mechanical pins,
   not restatements).
6. **Enforcement by omission.** `except ImportError` census over the package:
   11 sites. Two are this file's definitions; five are patch-lifecycle guards
   (R4); two are the routers broken-install split (R8, feature-owned shapes);
   one is the sets_mixins ladder (R3); one is the finalizer error translation
   (R5). All four `require_*` wrappers plus both keyset direct calls route
   through the primitive — no hand-rolled soft-dependency guard remains. No
   omission found.

### Challenges

Each challenge posits a change and counts authoritative definitions forced.

| ID | Change posited | Definitions forced | Home |
|---|---|---|---|
| C1 | Best-effort member also degrades a new failure mode | 1 (`import_attr_if_importable`); 4 consumers follow by call; `_safe_import`'s own `except AttributeError` is the lifecycle's separate rule, untouched | FL1 |
| C2 | Loaded-only member imports when a finder is available | 1 (`loaded_attr`); the finalizer opt-in contract is the consumer, not a second definition | FL2 |
| C3 | Strict member reframes failures with a hint | 1 (`import_attr`); the 4 generated-body sites follow; proves it is not a second guard (R-guards live at feature owners) | FL3 |
| C4 | Guard absence carries a new signal beside the hint | 1 (`require_optional_module`); 4 wrappers + keyset follow by call, 0 edits at wrappers (agrees routers C3) | F1 |
| C5 | Channels floor bump | 1 definition + 1 declared second place (constant + `pyproject.toml` row, CI-pinned); 4 hint sites follow by interpolation, 0 hint edits | FL5 |
| C6 | `_plain_text` rejects non-str at its own boundary | 1 here; the strings twin keeps its own contract (proves R1: different error obligations) | FL4 + R1 |
| C7 | A third dependency needs a multi-site hint floor | Extension point fires: a new constant here (declared in the module docstring), not a literal at the new site | FL5 |

### Freshness

Target: worktree `291ecedd` == `HEAD:` `291ecedd` == dispatch brief; item
baseline `010323ee` diff empty; HEAD `0c0537e2` unmoved at artifact write,
re-confirmed unmoved at `/2` resubmission with the target blob unchanged.
Connected sources read (worktree `git hash-object`; `=` marks paths clean in
`git status`, i.e. HEAD blobs): `management/commands/_imports.py` = `05e9de80`,
`rest_framework/__init__.py` = `45cf7b63`, `__init__.py` = `0ef72601`,
`tests/_soft_dependency.py` = `7b28c078`, `tests/test_ci_governance.py` =
`cfc66f6e`, `docs/GLOSSARY.md` = `3413edc3`; dirty concurrent-work paths
(inspected bodies only, never edited): `utils/strings.py` `5a4f4811`,
`registry.py` `27358cbc`, `utils/inputs.py` `b5af8255`, `types/finalizer.py`
`b9d8acb2`, `mutations/sets.py` `21c15c0b`, `types/converters.py` `f6cadb08`,
`optimizer/nested_planner.py` `d32d1b7b`, `keyset.py` `d1a6dec2`, `routers.py`
`e18772f7`, `auth/sessions.py` `865d6e70`, `middleware/debug_toolbar.py`
`ffda621e`, `sets_mixins.py` `088ddab0`, `pyproject.toml` `964c1339`.
`tests/utils/test_imports.py` is status-clean with `sha1sum`
`9bd59824` identical for worktree bytes and `HEAD:` bytes; its git blob id
renders as the empty-blob id through every local hasher for this one path
(tooling anomaly, content equality proven both sides), so the `sha1sum` is the
fingerprint of record. Searched population: 117 package `.py` files
(`except ImportError`, `import_string`/`import_module`, star-import, and
floor-literal censuses above), plus — at `/2` — the full `sys.modules`
census over the same population (`.get`, subscript, assignment, eviction):
exactly 3 executable readers — this file's `loaded_attr` (`sys.modules.get`
+ loud `getattr`, the FL2 definition), `utils/querysets.py:580`
(`sys.modules.get` + defaulted `getattr` identity probe, R10), and
`utils/inputs.py:1415` (`sys.modules[module_path]` subscript + `setattr`
write, R11); zero production assignments/evictions (remaining hits are
docstrings, comments, and the test helper). R10/R11 bodies read at
`/2`-fresh worktree fingerprints `utils/querysets.py` `8fc556d5`,
`utils/inputs.py` `b5af8255` (unchanged since `/1`). Excluded on body
strength after reading: `middleware/request_body.py`, `utils/sessions.py`
(Django strict `import_string`, no optional semantics), the five patch
modules (lifecycle guards, R4; confirmed zero `sys.modules` reads).

## Findings

### F1 — raising optional-dependency guard primitive (ADOPT into open family)

- **Contract + variation.** `require_optional_module(module_name, *,
  install_hint)`: return the imported module unchanged; on `ImportError`
  raise a new `ImportError` carrying the caller's hint, chained `from exc`.
  No memoization (eviction-simulated absence re-hits the guard); no
  `feature_label` (hint text lives single-sited at the feature owner).
  Varies only by caller-supplied module name + hint.
- **Sites + roles.** Definition: this file. Consumers: the four `require_*`
  thin wrappers + two keyset direct calls (census above). Oracles:
  `tests/utils/test_imports.py` (4 guard tests) + per-feature absence suites
  via `tests/_soft_dependency.py`. Projections: glossary entry, spec-041
  Decision 5.
- **Challenges.** C4: count 1.
- **Owner + lifetime.** Owner candidate is this definition, as the open
  [plan][plan] family `soft-dependency-require-guard` already records. No
  stored derivation ("not cached" is the contract). The family item decides
  the wrappers' final shape; this file item adopts the definition into it
  and makes no production edit.
- **Distinct behavior.** Hint strings, broken-install splits (R8), and the
  single-site DRF/toolbar/crypto floors (R7) stay at feature owners.

### FL1 — cycle-safe best-effort import (FILE-LOCAL)

- **Contract.** `import_attr_if_importable`: `None` on `ImportError`
  (including the `sys.modules` None-sentinel shape); loud `AttributeError`
  for a missing attr on an importable module.
- **Sites.** One definition; four consumers compose by name
  (`registry._clear_if_importable`, `inputs._safe_import`,
  `converters` sentinels, `nested_planner` sentinel). `inputs._safe_import`
  is a distinguished consumer, not a second definition: it delegates to the
  primitive and adds only the partial-load lifecycle's own attr-leniency.
- **Challenges.** C1: count 1. The `composite-index-advisory` consumer edge
  (nested_planner's `_PostgresBTreeIndex` probe) carries no advisory logic
  in this file — converge with that open family by reference, no new row.
- **Proof of singularity.** Axis-6 census: no other best-effort
  import-then-getattr body exists; the nearest shapes are rejected pairs
  (R2, R3, R4) or translations (R5).

### FL2 — already-loaded-only lookup (FILE-LOCAL)

- **Contract.** `loaded_attr`: `None` unless the module is in `sys.modules`;
  never imports (the opt-in-preserving variant); loud `getattr` like FL1.
- **Sites.** One definition; one consumer (finalizer phase-2.5 auth bind).
- **Challenges.** C2: count 1. The `sys.modules` census (Freshness: 3
  executable readers package-wide) leaves FL2 single: the querysets
  genuineness probe is a bool-verdict fail-closed rule over a type object
  (R10), and the inputs materialization is a strict write path assuming
  presence (R11) — neither is a second loaded-only attr lookup.

### FL3 — strict internal deferred-import seam (FILE-LOCAL)

- **Contract.** `import_attr`: failures propagate; unloaded modules ARE
  imported; no hint reframing. For package-own deferred seams where any
  failure is a real bug.
- **Sites.** One definition; one seam family of consumers
  (`mutations/sets.py::resolver_seams`, 4 generated bodies).
- **Challenges.** C3: count 1. Deliberately not a fifth guard: a broken
  internal module must fail loud, never degrade (FL1) or reframe (F1).

### FL4 — hostile string-subclass normalization (FILE-LOCAL)

- **Contract.** `_plain_text`: exact-`str` and non-`str` pass through
  unchanged; a `str` subclass is copied through `str.__str__` so a lying
  `__str__`/`__hash__` cannot redirect the import or the `sys.modules`
  lookup. Applied by all four members to every string they touch, including
  the raised hint.
- **Sites.** One definition, file-private; 16-oracle pin includes the
  hostile-name test across three members plus the hostile-hint test.
- **Challenges.** C6: count 1; the strings twin is untouched by the same
  change (R1).

### FL5 — install-hint floor constants (FILE-LOCAL)

- **Contract.** `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR`: the verified floors
  interpolated into multi-site (channels, 4 hints) and comparison-orphaned
  (strawberry, 1 hint) install hints; each has exactly one other written
  copy (its `pyproject.toml` row), pinned by a CI governance comparator.
- **Sites.** One definition per floor; interpolation consumers in
  `routers.py` and `auth/sessions.py`.
- **Challenges.** C5 + C7: bump = 1 definition + 1 declared pinned place;
  new multi-site floor = new constant here per the module docstring's
  declared extension point.

### FL6 — module leaf manifest (FILE-LOCAL)

- **Contract.** `__all__` names exactly the 2 floors + 4 helpers.
- **Sites.** One manifest; zero star-import consumers, so the set is
  enforced by inspection plus the bug-hunt star-import binding proof, not
  by a runtime population.
- **Challenges.** Adding a public helper without the manifest row breaks the
  exact-set invariant — 1 place to change, found by reading the file.

### R1 — `_plain_text` vs `utils/strings.py::_plain_text` (REJECTED, fresh)

Same name, deliberately different contracts. Strings' twin is
`(object) -> str`: raises `ConfigurationError` on non-strings, orders the
exact-`str` fast path first for the hot optimizer-walker call, and reads
through `utils/truth.py`. This file's is `(Any) -> Any`: non-strings pass
through so the import machinery fails loud with ITS error (a `TypeError`
from `import_module`, never a package error for a package-internal seam),
and it uses plain `isinstance` because this module is stdlib-only by
layering (imported at registry import time; `strings.py` drags `truth` +
`ConfigurationError`). Merging would either weaken the walker's
fail-loud input gate or couple the import leaf to the truth module.
**Trigger:** if this file ever needs to reject non-str at its own boundary
with a package error, revisit.

### R2 — `management/commands/_imports.py` translators (REJECTED, fresh)

Different contract, different population: strict resolution of
consumer-typed CLI paths (`module[:symbol]`, dotted paths) re-raised as
`CommandError`, with malformed-path pre-validation. No optional semantics,
no degradation, no hint interpolation. Routing commands through FL1/F1
would mistranslate a typo'd schema path as an absent optional dependency.
**Trigger:** if a command ever needs optional-module degradation, revisit.

### R3 — `sets_mixins.py` lazy class-ref ladder (REJECTED, fresh)

Different rule: absolute-`import_string` attempt, then module-relative
retry for unqualified names, then zero-arg factory / passthrough arms for
non-strings. The `except ImportError` there is a control-flow step between
two resolution attempts, not an absence signal. **Trigger:** none foreseen;
the ladder's arms share no variation axis with these members.

### R4 — upstream-patch skip guards (REJECTED, converge)

The five `except ImportError` guards in the patch modules + `querysets.py`
implement "skip the patch when the upstream module is absent" — owned by
open family `upstream-patch-lifecycle`. Same exception, different rule
(lifecycle skip vs value-returning lookup). No row here; converge by
reference.

### R5 — finalizer set-expansion error translation (REJECTED, fresh)

`types/finalizer.py` catches `ImportError` from set expansion and raises
`ConfigurationError` attributing the failure to one set class. That is
finalization error attribution over consumer configuration, not optional
import handling; it runs strictly and never degrades. **Trigger:** none
foreseen.

### R6 — root `__getattr__` direct `importlib` use (REJECTED, converge)

The root lazy-export hook calls `importlib.import_module` directly. Verified
File `__init__.py` already rejected unifying it with this module's members
(PEP 562 hook shape vs lookup helpers); the bodies are unchanged since that
verdict. No row here; the standing rejection stands on fresh census.

### R7 — single-site floors as re-typed literals (REJECTED, converge)

DRF (`3.17.0`), debug-toolbar (`7.0.0`), and cryptography (`44.0.0`) floors
stay as literals in their owner hints. Verified File
`rest_framework/__init__.py` already rejected centralizing them
(`rest-framework-shared-guard-consolidation` /
`rest-framework-floor-const-interpolation`: byte-pinned hints, single-site
each). No row here; restated trigger: a floor-drift incident or a second
hint site for one of those dependencies reopens it at the family item.

### R8 — routers broken-install split hints (REJECTED, converge)

`routers.py`'s two `except ImportError` halves raise feature-owned
present-but-incompatible messages. That split (which half broke) is the
router's error-shape rule, recorded at routers F3; the primitive only
supplies the true-absence path it runs first. No row here.

### R9 — hint siting + no-`feature_label` (CONVERGE, no row)

Hint strings single-sited at feature owners and the deliberate absence of a
`feature_label` parameter are the open `soft-dependency-require-guard`
family's own design surface; the family item, not this file item, judges
them. Recorded here only to show the surface was considered, not missed.

### R10 — querysets Django-provenance probe (REJECTED, fresh, `/2`)

`utils/querysets.py::_type_is_genuinely_django` shares only the
`sys.modules.get` token with FL2. Different inputs (a type object, whose
module/qualname are read truthfully, vs path strings), different output (a
`bool` verdict vs the attr itself), and the opposite error obligation:
fail-closed (`False` on absent module, dotted qualname, or identity
mismatch) vs FL2's fail-loud un-defaulted `getattr`. The probe's
`getattr(module, qualname, None) is node_type` default exists precisely so a
missing name fails closed instead of raising — routing it through
`loaded_attr` would turn a seal rejection into an `AttributeError`, and
routing FL2 through the probe would turn a missing-attr bug into a `None`.
**Trigger:** if a seal consumer ever needs the genuine attr VALUE rather
than an identity verdict, revisit.

### R11 — inputs generated-class materialization write (REJECTED, fresh, `/2`)

`utils/inputs.py::materialize_generated_input_class` is a WRITE path, not a
lookup: `sys.modules[module_path]` subscript (strict — `KeyError` if the
module is absent, the opposite of loaded-only leniency) followed by
`setattr(module, name, cls)` pinning the class as a module global for
Strawberry's `LazyType.resolve_type`, guarded by an idempotent ledger plus a
collision `ConfigurationError`. It assumes presence where FL2 tolerates
absence, and mutates where FL2 only reads. **Trigger:** if materialization
must ever tolerate an unloaded target module (skip instead of `KeyError`),
revisit.

## Defects

None. One candidate was examined and is NOT homed here:

- O1 (observed, not homed): the [glossary][glossary] `require_optional_module`
  entry still says "planned ... landing in Slice 1" and calls the
  `require_drf()` migration "a deliberate follow-on non-goal", although the
  migration shipped (the target's own line 55 delegates). Verified File
  `rest_framework/__init__.py` already dispositioned exactly this staleness
  as a ruled-out stale projection (behavior correct, oracle-covered, no
  contract row breaks), and that item is verified. Converge with that
  verdict; re-homing the same prose would fork the record.

## Judgment

Zero-edit file item. Eight named symbols: one adoption into the open
`soft-dependency-require-guard` family (F1, this file holds the owner
candidate), six file-local homes (FL1–FL6) each proven single by challenge
count 1, and eleven pair verdicts (six fresh rejections R1/R2/R3/R5/R10/R11
with triggers, five convergences by reference). The `composite-index-advisory`
edge is a consumer relationship only — no advisory logic lives in this
file. No consolidation inside a file item; no production edits; no defects.
No deferred proofs: every claim above rests on inspected bodies and
censuses, so there is no `## Pending execution` section.

## Index rows for Worker-0

F1 adopts the definition into the already-open family (existing plan row
stands, holding item unchanged). FL1–FL6 and R1/R2/R3/R5/R10/R11 are new rows
for the [plan][plan] `## Responsibility index`.

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `soft-dependency-require-guard` | `django_strawberry_framework/utils/imports.py::require_optional_module` | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/routers.py`, `django_strawberry_framework/auth/sessions.py`, `django_strawberry_framework/middleware/debug_toolbar.py`, `django_strawberry_framework/keyset.py` | Family `soft-dependency-require-guard` | open (F1 adopts the definition here; no new row, existing row stands) |
| `imports-best-effort-attr-lookup` | `django_strawberry_framework/utils/imports.py::import_attr_if_importable` | `django_strawberry_framework/utils/imports.py` | File `utils/imports.py` | file-local (FL1; C1 count 1; `_safe_import` distinguished as consumer) |
| `imports-loaded-only-attr-lookup` | `django_strawberry_framework/utils/imports.py::loaded_attr` | `django_strawberry_framework/utils/imports.py` | File `utils/imports.py` | file-local (FL2; C2 count 1) |
| `imports-strict-attr-lookup` | `django_strawberry_framework/utils/imports.py::import_attr` | `django_strawberry_framework/utils/imports.py` | File `utils/imports.py` | file-local (FL3; C3 count 1) |
| `imports-hostile-name-normalization` | `django_strawberry_framework/utils/imports.py::_plain_text` | `django_strawberry_framework/utils/imports.py` | File `utils/imports.py` | file-local (FL4; C6 count 1) |
| `imports-hint-floor-constants` | `django_strawberry_framework/utils/imports.py::CHANNELS_FLOOR` | `django_strawberry_framework/utils/imports.py` | File `utils/imports.py` | file-local (FL5; C5 + C7; covers `STRAWBERRY_FLOOR`) |
| `imports-leaf-manifest` | `django_strawberry_framework/utils/imports.py::__all__` | `django_strawberry_framework/utils/imports.py` | File `utils/imports.py` | file-local (FL6; exact-set 6, zero star consumers) |
| `imports-plain-text-vs-strings-twin` | `django_strawberry_framework/utils/imports.py::_plain_text` (rejection recorded here) | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/utils/strings.py` | File `utils/imports.py` | rejected (R1; pass-through vs ConfigurationError + stdlib-only layering; trigger: own-boundary non-str rejection need) |
| `imports-vs-command-path-translators` | `django_strawberry_framework/management/commands/_imports.py::import_or_command_error` (rejection recorded here) | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/management/commands/_imports.py` | File `utils/imports.py` | rejected (R2; CommandError CLI translation vs optional semantics; trigger: command needing optional degradation) |
| `imports-vs-lazy-class-ref-ladder` | `django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class` (rejection recorded here) | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/sets_mixins.py` | File `utils/imports.py` | rejected (R3; absolute-then-relative + factory arms; no trigger foreseen) |
| `imports-vs-finalizer-expansion-translation` | `django_strawberry_framework/types/finalizer.py` (rejection recorded here) | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/types/finalizer.py` | File `utils/imports.py` | rejected (R5; finalization attribution, strict, never degrades; no trigger foreseen) |
| `imports-vs-querysets-provenance-probe` | `django_strawberry_framework/utils/querysets.py::_type_is_genuinely_django` (rejection recorded here) | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/utils/querysets.py` | File `utils/imports.py` | rejected (R10, `/2`; fail-closed bool verdict over a type vs fail-loud attr lookup; trigger: seal needing the attr value) |
| `imports-vs-inputs-materialization-write` | `django_strawberry_framework/utils/inputs.py::materialize_generated_input_class` (rejection recorded here) | `django_strawberry_framework/utils/imports.py`, `django_strawberry_framework/utils/inputs.py` | File `utils/imports.py` | rejected (R11, `/2`; strict subscript + setattr write vs loaded-only read; trigger: materialization tolerating unloaded targets) |

Convergences by reference (no rows): `composite-index-advisory` (consumer
edge only, FL1), `upstream-patch-lifecycle` (R4), verified File `__init__.py`
PEP 562 rejection (R6), verified `rest-framework-floor-const-interpolation`
rejection (R7), routers F3 broken-install split (R8), `soft-dependency-require-guard`
hint-siting surface (R9).

## Independent verification (Worker-2)

Trace recorded before reading `## Findings`; reconciliation follows it.

### My trace

Target `django_strawberry_framework/utils/imports.py`: worktree
`git hash-object` = `291ecedd`, `git diff HEAD -- <target>` empty,
`git status --short` silent for the target, 139 lines, HEAD `0c0537e2`
unmoved. All bytes traced are HEAD bytes; nothing tracked touched.

`ast.Module.body` census: 13 members — 1 docstring, 4 imports
(`__future__`, `importlib`, `sys`, `typing.Any`; stdlib-only, no package
edge), `__all__`, `CHANNELS_FLOOR`, `STRAWBERRY_FLOOR`, `_plain_text`,
`import_attr_if_importable`, `loaded_attr`, `import_attr`,
`require_optional_module`. 8 named symbols.

Production consumer census (package-wide regex search, every hit read):

- `import_attr_if_importable`: `registry.py` import + call,
  `utils/inputs.py::_safe_import` (delegating wrapper with its own
  `except AttributeError -> None` arm), `types/converters.py` 2
  module-level sentinels, `optimizer/nested_planner.py`
  `_PostgresBTreeIndex` sentinel.
- `loaded_attr`: `types/finalizer.py` auth-bind call, single site.
- `import_attr`: `mutations/sets.py` import + 4 generated-body calls.
- `require_optional_module`: `rest_framework/__init__.py::require_drf`,
  `routers.py::require_channels`,
  `auth/sessions.py::require_channels`,
  `middleware/debug_toolbar.py::require_debug_toolbar`,
  `keyset.py::_cursor_crypto_types` 2 direct calls under one hint.
- `CHANNELS_FLOOR`: interpolated into 4 hints (routers 3, sessions 1).
  `STRAWBERRY_FLOOR`: interpolated into 1 hint (routers).

`except ImportError` census: 11 sites — 2 in this file, 5
patch-lifecycle skip guards (4 patch modules + `querysets.py:105`), 2
routers broken-install halves, 1 sets_mixins ladder step, 1 finalizer
translation. No hand-rolled soft-dependency guard remains outside the
primitive.

Competing shapes read in full before judging: both `_plain_text`
bodies, `utils/inputs.py::_safe_import` + `:1415` materialization,
`utils/querysets.py:580` genuineness probe, `sets_mixins.py`
lazy ladder, `management/commands/_imports.py`, routers broken-install
split, finalizer expansion translation, root `__getattr__`,
`tests/utils/test_imports.py` (16 tests, hand-built fakes), CI floor
comparators, glossary `require_optional_module` entry.

Owner I would choose: this file for all four members, both floors, the
normalizer, and the manifest; `require_optional_module` into the
already-open `soft-dependency-require-guard` family whose plan row
names it owner. Definition count 1 per rule; the querysets probe and
the inputs materialization are different rules (below), not second
definitions.

### Reconciliation

(1) Enumeration: STANDS. 13 members / 8 named symbols reproduce
exactly over HEAD bytes; every symbol is homed (F1 + FL1–FL6, FL5
covering both floors). Cleanliness re-verified independently.

(2) F1 adoption: STANDS. Consumer census matches mine site for site
(wrapper names `require_drf` / `require_channels` x2 /
`require_debug_toolbar` confirmed by `def` lines; keyset 2 calls under
one hint confirmed). No memoization and no `feature_label` confirmed
against the body. The family is open with this owner in the plan.

(3) Fresh rejections R1/R2/R3/R5: STAND on bodies, with one
evidence gap owned by FL2 (below), not by these four. R1: both
`_plain_text` bodies differ exactly as stated (raise-`ConfigurationError`
vs pass-through; truth-based vs stdlib-only — `strings.py` imports
`truth` + `ConfigurationError`, confirmed). R2: `_imports.py` read in
full, CommandError-translation contract confirmed. R3: ladder arms
(absolute retry + factory/passthrough) confirmed. R5: finalizer
ImportError→ConfigurationError attribution confirmed. Each carries a
contract difference and a trigger line.

(4) Convergences R4/R6/R7/R8/R9: STAND. R4: 5 skip guards confirmed
by census. R6: root `__getattr__` body routes via `require_drf` +
direct `import_module`; root blob `0ef72601` identical at commit
`5ee86193` and worktree, so unchanged since the run-2 verdict, and
that artifact cites this target at `291ecedd`. R7: the three
single-site literals (`3.17.0`, `7.0.0`, `44.0.0`) confirmed at owner
hints; `rest_framework/__init__.py` still `45cf7b63`, the verified
blob. R8: routers halves confirmed as feature-owned split shapes.
R9: family-surface deferral, no row owed. The
`composite-index-advisory` consumer-only edge is correct:
`_PostgresBTreeIndex` feeds `_BTREE_INDEX_TYPES` membership in the
planner; no advisory logic lives here. Matrix axes 1–6 discharged
against the real surface except the FL2 census gap below; axis-2
inapplicability (no await surface) judged sound. Freshness
fingerprints: all six `=` marks re-verified clean with matching
hashes; the `test_imports.py` empty-blob-id anomaly reproduces under
my own `git hash-object` call and the `sha1sum` equality both sides
reproduces too — transparently handled, accepted. O1: the glossary
staleness wording verified at `GLOSSARY.md` line 1750 and the
rest_framework `__init__` artifact's rule-out (defect-(b), endorsed)
says exactly what W1 cites — converge, correctly not homed. Zero
production defects: agreed, none found on my trace either.

(5) FL2 evidence gap — REVISION REQUIRED. FL2's proof sentence
("the only other `sys.modules` readers are the test helper and patch
install/uninstall paths") is false, and the Freshness searched
population lists no `sys.modules` census, so the claim rests on a
search never run. Reproduce with one command:

`search pattern sys\\.modules over django_strawberry_framework/`

Production readers it returns beyond this file:

- `utils/querysets.py:580` (`sys.modules.get` + `getattr(..., None)`
  identity comparison): the fail-closed Django-provenance probe over a
  type object. Different inputs (type vs path strings), output (bool
  vs attr), and error obligation (fail-closed vs fail-loud).
- `utils/inputs.py:1415` (`sys.modules[module_path]` subscript +
  `setattr`): the generated-input materialization WRITE, assuming
  presence (`KeyError` if absent). A write path, not a lookup.

Conversely the sentence's second half is also wrong: no
`_*_patches.py` module reads `sys.modules` at all (zero hits in the
same search). My judgment is that neither site is a second
loaded-only definition — the FL2 file-local outcome should stand —
but the verdict must rest on a true census plus recorded pair
verdicts, not on these two shapes being unmentioned.

### Resubmission (SAME W1 context, submit as `/2`)

1. Run the `sys.modules` census (`.get`, subscript, assignment,
   eviction) over the 117-file population and record it in Freshness
   searched population.
2. Correct the FL2 proof sentence; home the querysets probe and the
   inputs materialization as new pair verdicts (rejections with
   contract differences + triggers, or body-strength exclusions with
   the distinguishing reason stated — either with fresh
   fingerprints), and add any rows Worker-0 needs.
3. Record-accuracy, same pass: (a) the System-trace cleanliness
   sentence claims `git status --short` names neither path, but the
   artifact itself is the expected new untracked file (`??`) —
   rephrase; (b) "six-bullet call-site roster" is five bullets over
   six sites — reword.
4. Re-confirm HEAD unmoved and target blob `291ecedd` at resubmit.

No production edit is owed; this is evidence-only. Nothing else in
the artifact is challenged.

## Iterations

`/2` (evidence-only resubmission, same Worker-1 context): ran the full
`sys.modules` census over the 117-file population (3 executable readers,
zero production assignments/evictions; patch modules confirmed zero reads)
and recorded it in Freshness; corrected the FL2 proof sentence; homed the
querysets probe and the inputs materialization as fresh rejections R10/R11
with contract differences, triggers, `/2`-fresh fingerprints, and index
rows; rephrased the cleanliness sentence (artifact is the expected `??`
file) and the roster wording (five bullets over six sites); re-confirmed
HEAD `0c0537e2` unmoved and target blob `291ecedd`. Nothing else changed;
judgments (1)–(4), O1, and zero defects stand as Worker-2 left them.

### Verify-2 (Worker-2 re-pass, same context)

Re-ran the `sys.modules` search independently: identical hit set, exactly
3 executable readers (`imports.py:94`, `querysets.py:580`,
`inputs.py:1415`), zero executable production assignments/evictions
(sole assignment-shaped hit is a `rest_framework/__init__.py` docstring
line), patch modules zero reads — W1's recorded census matches.
Corrected FL2 proof sentence is now true. R10/R11 judged sound:
named symbols verified
(`querysets.py::_type_is_genuinely_django` @ :550 ⊃ :580,
`inputs.py::materialize_generated_input_class` @ :1377 ⊃ :1415),
contract differences confirmed against both bodies (bool-verdict
fail-closed probe; strict-subscript + `setattr` write with idempotent
ledger and collision error), triggers concrete, fingerprints match
my hashes (`8fc556d5`, `b5af8255`). Both record-accuracy fixes
verified. F1–R9/O1/Defects text unchanged from `/1`; my pass-1
section untouched. HEAD `0c0537e2` unmoved, target `291ecedd`
re-confirmed. Evidence now supports the verdict: **verified**.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[plan]: dry-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
