# DRY review: `soft-dependency-require-guard`

Status: verified
Run: 0.0.15 2026-10-01-10

## System trace

The rule candidate is the soft-dependency require guard: when an optional
third-party dependency is absent, raise `ImportError` carrying a feature-keyed
install hint (chaining the original); when present, return the imported module
unchanged; never memoize, so eviction-simulated absence tests can re-hit the
guard in one process. The owner candidate,
`django_strawberry_framework/utils/imports.py::require_optional_module`, is
re-derived below from the bytes, not inherited.

Site census, every site read at the fingerprinted bytes (roles per DRY.md
vocabulary; `def`/`return` lines verified, not grepped-and-assumed):

| Site | Role | Shape |
|---|---|---|
| `django_strawberry_framework/utils/imports.py::require_optional_module` | definition (sole) | `importlib.import_module(module_name)`; on `ImportError` raise `ImportError(_plain_text(install_hint)) from exc` |
| `django_strawberry_framework/rest_framework/__init__.py::require_drf` | consumer (declaration) | one `return` binding `("rest_framework", _DRF_INSTALL_HINT)`; called at leaf import + from the root `__getattr__` |
| `django_strawberry_framework/routers.py::require_channels` | consumer (declaration) | one `return` binding `("channels", _CHANNELS_INSTALL_HINT)`; called at builder entry |
| `django_strawberry_framework/auth/sessions.py::require_channels` | consumer (declaration) | one `return` binding `("channels", _CHANNELS_INSTALL_HINT)` (auth-keyed twin); called on the channels branch of `classify_transport` |
| `django_strawberry_framework/middleware/debug_toolbar.py::require_debug_toolbar` | consumer (declaration) | one `return` binding `("debug_toolbar", _DEBUG_TOOLBAR_INSTALL_HINT)`; called at leaf import |
| `django_strawberry_framework/keyset.py::_cursor_crypto_types` | consumer (direct calls) | two `require_optional_module(...)` calls (`cryptography.exceptions`, `...aead`) under one `_CRYPTOGRAPHY_INSTALL_HINT` |
| `django_strawberry_framework/__init__.py::__getattr__` | transitive consumer | calls `require_drf()`, then imports the routed submodule by name |
| Per-feature hint constants (`_DRF_INSTALL_HINT`, two `_CHANNELS_INSTALL_HINT`s, `_DEBUG_TOOLBAR_INSTALL_HINT`, `_CRYPTOGRAPHY_INSTALL_HINT`) | declarations | one literal each, single-sited at the feature owner; channels interpolates `CHANNELS_FLOOR`, the router's broken-install hints also `STRAWBERRY_FLOOR` |

Connected behavior examined: the primitive's three sibling members
(`import_attr_if_importable`, `loaded_attr`, `import_attr`) and every one of
their call sites (registry co-clear, finalizer auth bind, inputs namespace
clearing, postgres-only reads in `types/converters.py` and
`optimizer/nested_planner.py`); the routers present-but-broken split
(`_CHANNELS_BROKEN_HINT`, `_STRAWBERRY_CHANNELS_BROKEN_HINT`); the toolbar
`INSTALLED_APPS` wiring gate; every `except ImportError` in the package (11
sites); every soft-dependency import in the package (statement and
function-local); the root lazy-export table; `tests/_soft_dependency.py`;
the governance floor rows; specs 039 Decision 12, 041 Decision 5, 042
Decision 5 (contract sources for the guard shape, the hint strings, and the
no-`feature_label` / no-memoization terms).

Fingerprints (short blob per state; baseline is the item baseline object
`985111ee`, copy is the synced workspace copy at slot-2):

| File | HEAD `5c3496e0` | WT | Baseline | Copy |
|---|---|---|---|---|
| `django_strawberry_framework/utils/imports.py` | `3ea52b16` | `3ea52b16` | `3ea52b16` | `3ea52b16` |
| `django_strawberry_framework/rest_framework/__init__.py` | `b1b5a12d` | `b1b5a12d` | `b1b5a12d` | `b1b5a12d` |
| `django_strawberry_framework/routers.py` | `74dae938` | `16b68dcb` | `16b68dcb` | `16b68dcb` |
| `django_strawberry_framework/auth/sessions.py` | `d4a4857c` | `82b38f88` | `82b38f88` | `82b38f88` |
| `django_strawberry_framework/middleware/debug_toolbar.py` | `fb5f5549` | `47b30dcd` | `47b30dcd` | `47b30dcd` |
| `django_strawberry_framework/keyset.py` | `6af980b8` | `7d43c6b1` | `7d43c6b1` | `7d43c6b1` |

All six match the dispatch pins; HEAD is unmoved; status count is 481 as at
dispatch. The four dirty files carry concurrent hunt/review dirt (truth
migration, prose revisions); the guard `return` lines and every hint literal
are byte-identical between HEAD and WT — the single exception is two prose
hunks in `routers.py` (the `_CHANNELS_INSTALL_HINT` comment now names the
auth twin, the `require_channels` docstring says "this module's" where HEAD
says "the single"). No hunk in this item's scope is DRY-owned, and this item
lands zero edits, so no attribution stop arises.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Discharged by census, not sampling:
   the four `require_*` wrappers plus the keyset direct calls ARE the
   cross-flavor set, and every one was read in full. Each wrapper binds only
   its own (module name, hint) pair over the primitive; the hints differ per
   feature (DRF floor text, router channels text, auth channels text,
   toolbar text, cryptography text). No flavor carries a second
   import-or-raise body.
2. **Sync/async twins.** Inapplicable by construction: the primitive is a
   synchronous import plus a raise, with no await boundary, no executor, and
   no suspension point; every call site runs at module import, class-build,
   transport-classify, or first-crypto-use time, all synchronous contexts.
   `grep "async def require"` over the package returns zero lines.
3. **Derived rather than repeated knowledge.** The floor literals are the
   target's one derived-knowledge surface, treated as sub-rule R2 below:
   the channels floor is centralized (`CHANNELS_FLOOR`, 4 hint sites) while
   the DRF, toolbar, and cryptography floors stay literal in their single
   hint each. The re-typed floor literals in tests (`_HINT_SUBSTRING` and
   friends) are independent oracles under the documented tripwire
   discipline, never definitions.
4. **Inverse / round-trip pairs.** Inapplicable by construction: the guard
   is one-directional (import-or-raise). No encode/decode, pack/unpack, or
   build/parse pair exists on this surface.
5. **Contracts restated in another medium.** Inventoried with roles: unit
   oracles (`tests/utils/test_imports.py`, 16 tests — re-executed green in
   the shared venv for this item), per-flavor absence oracles (DRF suite,
   `tests/test_routers.py` channels rows,
   `tests/auth/test_sessions.py::test_classify_channels_scope_without_channels_raises_the_install_hint`,
   toolbar suite,
   `tests/test_keyset.py::test_cursor_crypto_is_a_soft_dependency`), the
   shared `tests/_soft_dependency.py` helper (oracle machinery, single
   home), governance comparators (channels + strawberry floor rows in
   `tests/test_ci_governance.py`), spec Decisions 039/12, 041/5, 042/5
   (contract sources), and glossary projections (see `## Defects`
   considered-not-defects). A hint rewording moves production + its
   oracles together by design; oracles are listed, never counted.
6. **Enforcement by omission.** The soft-dependency crossing family was
   enumerated in full: every statement and function-local import of
   `channels`, `rest_framework`, `debug_toolbar`, and `cryptography` in the
   package. Each crossing is either behind a `require_*` call (DRF leaf
   submodules via parent-package execution order, toolbar statements below
   the leaf guard, router builder imports after `require_channels()`,
   keyset crypto behind `_cursor_crypto_types`, root names behind
   `require_drf()`) or downstream of one by construction — reachable only
   with the dependency's own objects in hand
   (`auth/mutations.py` channels-login/logout after `classify_transport`,
   `consumers.py` revalidation/denier arms on live channels connections,
   with the channels-free-at-import posture stated in the code). No member
   lacks a guard; no enforcement gap; no defect.

### Enumeration

The rule's mechanism population, enumerated by instrument (each `grep`
below ran over `django_strawberry_framework/`, `*.py` only):

- `require_optional_module(` — 7 hits: 1 `def` (the definition) + 4
  wrapper `return` lines + 2 keyset call lines in 1 function (the
  consumers). No other caller exists.
- `def require_` — 18 hits: the 1 primitive + the 4 soft guards + 13
  unrelated validation helpers (`require_session`,
  `require_queryset_related_model`, `require_non_delete_operation`,
  `require_backing_class`, `require_subclass`, `require_model_class`,
  `require_orderset_class`, `require_managed_write`,
  `require_write_pipeline`, `require_re_readable_field_declaration`,
  `require_one_segment_source`, `require_nested_fields_mapping`,
  `require_nested_serializer_config`), each excluded on the strength of
  its body (model/operation/field validation, no import, no hint).
- `except ImportError` — 11 hits: 2 at the owner (best-effort member +
  primitive, both the rule's own machinery), 2 router present-but-broken
  arms (intentional absence-vs-broken split, spec-041), 1 finalizer
  set-expansion reframe (finalize contract, `ConfigurationError`), 1
  lazy class-ref fallback (consumer-string resolution, re-raises), 5
  version/availability probes (`utils/querysets.py` Django-constant
  fallback + the four upstream-patch modules, each with a compat fallback,
  never an install hint). Zero hand-rolled raising guards: no fourth
  import-handling pattern exists anywhere in the package.

### Challenges

Each change posited against the rule's variation axes; only authoritative
definitions counted:

| Id | Change posited | Definitions forced | Verdict |
|---|---|---|---|
| C1 | Absence signaling changes (new signal beside the hint, different exception type, memoization) | **1** (`require_optional_module`; 4 wrappers + keyset + root follow by call, zero edits) | proves single ownership |
| C2 | One feature's hint reworded (new pip spelling for DRF) | **1** (`_DRF_INSTALL_HINT`; nothing else moves) | proves hints are per-feature declarations, not copies |
| C3 | A new soft dependency lands (new feature, new hint) | **1** new declaration (hint + one-line wrapper at the feature owner); the primitive is untouched | proves the variation axis is declared, not defined, per feature |
| C4 | Merge the two `require_channels` into one shared guard | **0** definitions removed (the primitive stays the only one); the merge would couple two feature-keyed messages + two call postures to save one `return` line | rejected (R1) |
| C5 | Hoist the DRF/toolbar/cryptography floors into `utils/imports.py` beside `CHANNELS_FLOOR` | **0** obligations relieved (3 gated sites either way: constant-or-literal + pyproject row + test comparator) | rejected (R2) |
| C6 | Extract a named `require_cryptography()` over keyset's two direct calls | **0** definitions removed (the two calls import different modules; a wrapper still contains both) | folded into F1 (composition, not a separation) |

No executable experiment was owed: every challenge is decided by reading
single-expression delegation at fingerprinted bytes ("body composed by
name", inspection-sufficient per DRY.md). The one shared-tree run for this
item re-executed the primitive's oracle file green (see F1 proof).

## Findings

### F1 — the raising require guard (CONFIRMED single-owned, zero-edit)

- **Contract + variation.** `require_optional_module(module_name, *,
  install_hint)`: import the module and return it unchanged; on
  `ImportError` raise a new `ImportError` carrying `install_hint`,
  chaining the original; no memoization; no `feature_label` (feature
  text lives entirely in the caller's hint). Varies legitimately on two
  axes only: which module, which hint — both caller-supplied.
- **Sites + roles.** 1 definition (the primitive) + 4 wrapper
  declarations + 1 direct-call consumer + 1 transitive consumer, per the
  census table in `## System trace`. The wrappers are declarations, not
  definitions: each body is a single `return` binding its feature's
  (module, hint) pair, with no logic that could drift.
- **Challenges.** C1–C3 count 1 (single ownership proved on the
  signaling, wording, and new-member axes); C4–C6 count 0 (the
  conceivable further consolidations remove no definition). Consumers,
  oracles, and projections that move with a change are listed in the
  matrix, never counted.
- **Owner + lifetime.** `django_strawberry_framework/utils/imports.py::require_optional_module`,
  by responsibility (principle 7): it is the package's stated
  optional-import owner, the narrowest module every consumer (root,
  routers, auth, middleware, keyset, rest_framework) can import without
  reversing a dependency, and the existing home of the sibling members.
  No stored derivation: pure function, nothing cached ("not cached" by
  design — memoization would break eviction-simulated absence tests).
- **Migration.** None: every site already composes the owner by name.
  Zero production edits, zero test edits.
- **Distinct behavior.** Per-feature hint strings stay single-sited at
  their feature owners (C2); the router's present-but-broken split stays
  separate (absence vs broken-install are different contracts, spec-041);
  the best-effort / loaded-only / strict siblings stay separate members
  (return-`None` vs raise vs propagate are different contracts).
- **Behavioral proof.** Static-reviewed (composition by name at
  fingerprinted bytes — every wrapper body read in full, each a single
  delegating `return`): `uv run pytest tests/utils/test_imports.py
  --no-cov -n0 -q` → 16 passed in the shared venv, pinning the
  primitive's return-the-module / hint-plus-chain / no-memoize contract;
  per-flavor absence oracles pin each wrapper's hint text and are cited
  by node in matrix axis 5 (suite-green confirmation belongs to the
  final gate, not this zero-edit item). Cells: sharded and pg are
  inapplicable by construction — the target path reaches no database,
  alias, or dialect decision (pure import + raise).
- **Structural gate.** None proposed, deliberately: one body is not
  impossible here — it exists — so principle 9's check-shape does not
  apply; an AST census over the 11 `except ImportError` sites would be
  machinery pinning heterogeneous mechanisms (compat fallbacks, lazy-ref
  retries, finalize reframes) to this rule. The durable enforcement is
  the principle-10 clause already at the owner ("New optional-import
  handling belongs here, not inline at a new call site"), and the
  whole-package sweep in `### Enumeration` shows the rule currently
  holds. Re-check trigger: any new `except ImportError` + `raise
  ImportError` raising pair outside `utils/imports.py`.
- **Coupling.** None: zero edits, no other finding depends on this one.
- **Freshness.** The six-file fingerprint table in `## System trace`
  (HEAD, WT, baseline `985111ee`, slot-2 copy); the three mechanism
  greps over the full package (`require_optional_module(`, `def
  require_`, `except ImportError`); the soft-import census; contract
  sources spec-039 Decision 12, spec-041 Decision 5, spec-042 Decision 5.
  Modules excluded on the strength of their bodies: every file carrying
  one of the 13 unrelated `require_*` validators or one of the 9
  non-owner `except ImportError` sites (named in `### Enumeration`).
  Any fingerprint change reopens the finding.

### R1 — unifying the wrappers, esp. the two `require_channels` (REJECTED)

The four wrappers share one line shape, not one contract. The two
`require_channels` differ on three axes: the hint text (router-keyed vs
auth-keyed, each naming its own feature context), the call posture
(builder entry vs channels-branch-only classify call), and the
enforcement timing (router class-build vs per-request transport
classification). The DRF and toolbar wrappers differ further (leaf
import-time guards over different dependencies). A merge removes zero
definitions (C4), couples two features' user-facing messages, and
forces one call posture onto two boundaries. **Trigger:** the two
channels hints converge to identical text AND one call site; then a
single channels guard becomes one declaration instead of two.
**Durable home:** already at the owners — the routers hint comment
names the auth twin, the auth hint comment states the feature-keying,
and the primitive docstring states that hint strings stay single-sited
at the feature owner. No edit owed.

### R2 — hoisting single-use floors beside `CHANNELS_FLOOR` (REJECTED)

`CHANNELS_FLOOR` is centralized because the channels floor is named at
4 hint sites (the router's three + the auth one); without the constant
a floor bump is a 4-literal edit nothing compares. The DRF, toolbar,
and cryptography floors are each named once. Hoisting a single-use
floor relieves zero change obligations (C5): the gated population stays
3 either way (constant-or-literal + pyproject row + test comparator),
with one more indirection hop. Uniformity of placement is a governance
taste, not a DRY consolidation — the KANBAN card asking for the toolbar
hoist plus its governance row owns that decision, not this item.
**Trigger:** a second production site naming the same floor; then the
constant relieves a real multi-site obligation, exactly the channels
precedent. **Durable home:** already at the owner — the `CHANNELS_FLOOR`
comment states it is centralized because channels "is the one optional
dependency whose hint text is written at more than one site". No edit
owed.

## Defects

None. Two candidates were examined and are NOT defects (recorded so
Worker 2 can see they were considered, not missed):

- (Not a defect) The `require_drf` docstring counts "the three
  soft-dependency guards" while four named `require_*` wrappers exist at
  current bytes. Prose census ambiguity, breaking no contract row: every
  wrapper's behavior is correct and oracle-pinned. Owned already by the
  concurrent review (`docs/review/review-0_0_15.md` routes the exact
  sentence to the rest_framework Comments pass to judge); this item
  converges with that routing and double-homes nothing.
- (Not a defect) The glossary `require_optional_module` entry still says
  "planned" and calls the `require_drf()` migration "a deliberate
  follow-on non-goal", although the migration shipped. Stale projection:
  the behavior is correct, only the rendered description lags, and
  projections never own the rule. Converges with the verified File
  `rest_framework/__init__.py` not-a-defect judgment on fresh bytes (the
  entry text is unchanged); at most a glossary-DB refresh note for the
  owning card queue. No contract row breaks; no owner, no routing.

## Judgment

The family is already consolidated: one raising primitive owns the
rule, four one-line wrappers declare their features' (module, hint)
pairs over it, keyset and the root compose it directly, and the
whole-package sweep finds no second definition and no unguarded
crossing. The three conceivable further moves (wrapper merge, floor
hoisting, keyset extraction) each remove zero definitions and are
rejected with triggers; both rejections' durable clauses already exist
at their owners. Zero edits, zero new tests, nothing blocked.

## Independent verification (Worker-2)

Recorded from the target + item-scoped diff BEFORE opening `## Findings`
(headers + `## Judgment` seen for anchoring; Matrix/Enumeration/Challenges/
Findings/Defects bodies unread at trace time).

### Worker-2 trace (pre-findings)

Population swept: `require_optional_module` def/call census, every
top-level + function-local import of the four soft distributions
(`rest_framework`, `channels`, `debug_toolbar`, `cryptography`),
every `except ImportError`, every `import_module(` call, every
`INSTALL_HINT`/`_FLOOR` spelling, all package-wide.

- **Definition (count 1):**
  `django_strawberry_framework/utils/imports.py::require_optional_module`
  — try `importlib.import_module`, except `ImportError` raise
  `ImportError(plain-text hint) from exc`; returns the module unchanged;
  no memoization. No second raising body exists: the only other
  `except ImportError` sites are the best-effort `None`-returning
  sibling (`import_attr_if_importable`), the two present-but-broken
  arms in `routers.py::_build_router_class_uncached` (guard already
  passed; different contract), and audited-upstream/best-effort seams
  (`_django_patches.py`, `_cross_web_patches.py`,
  `_graphql_core_patches.py`, `_strawberry_patches.py`,
  `utils/querysets.py`, `sets_mixins.py`, `types/finalizer.py`).
- **Wrapper declarations (4, one line each):**
  `rest_framework/__init__.py::require_drf`,
  `routers.py::require_channels`,
  `auth/sessions.py::require_channels`,
  `middleware/debug_toolbar.py::require_debug_toolbar` — each
  `return require_optional_module(<module>, install_hint=<own hint>)`.
- **Direct composers:** `keyset.py::_cursor_crypto_types` (two calls,
  one shared `_CRYPTOGRAPHY_INSTALL_HINT`, no `require_cryptography`
  wrapper); root `__init__.py::__getattr__` (calls `require_drf()`
  then `import_module`, no wrapper of its own).
- **Hint constants (5, per-feature prose, single-sited):**
  `_DRF_INSTALL_HINT`, routers `_CHANNELS_INSTALL_HINT`, sessions
  `_CHANNELS_INSTALL_HINT`, `_DEBUG_TOOLBAR_INSTALL_HINT`,
  `_CRYPTOGRAPHY_INSTALL_HINT`.
- **Floors:** `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR` hoisted in
  `utils/imports.py` (channels named at 3+ hint sites across two
  features); DRF/toolbar/cryptography floors stay literals inside
  their single-sited hints. Per-subject constants, not one rule.
- **Downstream consumers (post-guard, not definitions):**
  function-local `channels.auth` / `channels.security.websocket`
  imports in `auth/mutations.py` (2), `consumers.py` (2), `routers.py`
  builder (3, behind `require_channels()`); top-level
  `rest_framework` imports in `rest_framework/` submodules (guarded
  transitively by the package `require_drf()` import-time call);
  `debug_toolbar.*` statement imports below the leaf guard.
- **Oracles (independent literals, never read from the owner):**
  `tests/utils/test_imports.py`, `tests/rest_framework/
  test_soft_dependency.py`, `tests/middleware/test_debug_toolbar.py`
  (hint-vs-literal-vs-pyproject drift-catch),
  `tests/test_routers.py`, `tests/_soft_dependency.py`.

### Worker-2 challenges (pre-findings)

- C1 failure-contract change (exception type, chaining, memoization):
  count 1 (the primitive; wrappers pass through untouched).
- C2 a fifth soft dependency: count 1 (new hint + one-line wrapper
  or direct call; primitive unchanged).
- C3 reword one feature's hint: count 1 (that feature's constant).
- C4 merge the 4 wrappers into one generic: removes zero definitions
  (each wrapper is a boundary name its callers depend on; the
  mechanism is already single) — expect REJECT.
- C5 hoist the single-use floor literals beside `CHANNELS_FLOOR`:
  removes zero definitions (each floor is per-subject; channels was
  hoisted only because 3+ sites name it) — expect REJECT with a
  second-naming trigger.

### Worker-2 owner choice (pre-findings)

`utils/imports.py::require_optional_module` — the one raising body,
importable from every consumer without reversing a dependency; hint
strings stay at their feature owners per the primitive's own
documented contract.

### Worker-2 matrix (pre-findings)

1. Cross-flavor mirroring: searched — all four soft distributions +
   both channels features route through the one primitive.
2. Sync/async twins: inapplicable — the rule has no await boundary;
   the guard body is sync-only (called from sync and async contexts
   alike, but the body itself never awaits).
3. Derived knowledge: searched — hints single-sited per feature;
   no shared fact reconstructed by a second means.
4. Round-trip pairs: inapplicable — raise-only guard, no
   encode/decode halves.
5. Contracts in another medium: searched — test oracles pin hint
   substrings as independent literals; prose projections in module
   docstrings describe, never own.
6. Enforcement by omission: searched — all four soft distributions
   guarded (DRF/channels/toolbar via wrappers, cryptography direct);
   no unguarded optional-import crossing found; the non-raising
   siblings are intentionally unguarded by contract.

(Trace ends. Reconciliation with `## Findings` follows after reading.)

### Worker-2 reconciliation (post-findings)

- **Enumeration, member by member:** reproduced exactly. `def
  require_` = 18 (1 primitive + 4 guards + the same 13 named
  validators, each body-checked as non-import validation);
  `except ImportError` = 11 (2 owner + 2 router broken-arms + 1
  finalizer reframe + 1 sets_mixins lazy-ref + 1 querysets fallback
  + 4 patch-module probes); `require_optional_module(` = 7 code
  hits (1 def + 4 wrapper returns + 2 keyset lines). No sample;
  full census agrees.
- **Definition count + owner:** agree — count 1 on every
  signaling/wording/new-member change; owner
  `utils/imports.py::require_optional_module` with the same
  responsibility reasoning (narrowest module all six consumers can
  import; hint text stays at feature owners).
- **Roles:** agree — wrappers are declarations (single delegating
  `return`, no driftable logic), keyset a direct-call consumer,
  root a transitive consumer, tests independent oracles (hint
  substrings pinned as literals, never read from the owner).
- **Challenges:** W1 C1–C3 = my C1–C3 (count 1 each); W1 C4/C5 = my
  C4/C5 (count 0, the two rejections). W1 C6 (named
  `require_cryptography`) I had not separately posited; verified
  from the body that it removes zero definitions (the two calls
  import different modules, so a wrapper still contains both) —
  no disagreement, folding into F1 is correct.
- **Matrix:** agree on all six axes, including both
  inapplicability reasons (no await boundary; one-directional
  guard) and the axis-6 full crossing census (matches my
  downstream-consumer list member for member).
- **R1/R2:** each carries a contract difference + trigger +
  verified durable-home clause at the owner bytes (routers hint
  comment names the auth twin; auth hint comment states
  feature-keying; `CHANNELS_FLOOR` comment states the multi-site
  reason). R2's trigger correctly says "production site",
  excluding test comparators. Both rejections stand.
- **Freshness:** all six short blobs match the dispatch pins and
  my recomputation; HEAD unmoved at `5c3496e0`; WT == dispatch
  pins, so zero-edit holds. One evidence-precision correction
  (W2-C1, not a defect): the freshness prose says "two prose
  hunks in routers.py" — guard-word-adjacent prose changes span
  three hunks (hint comment, `require_channels` docstring,
  builder docstring). The material claim stands verified: every
  guard `return` line and every hint literal is byte-identical
  HEAD-vs-WT by targeted grep.
- **Examined-and-cleared notes:** (a) "three guards" docstring
  census — sentence verified at
  `rest_framework/__init__.py` and its routing verified at
  `docs/review/review-0_0_15.md` line 563 (owning Comments pass);
  agree, no double-homing. (b) glossary `require_optional_module`
  staleness — entry body verified stale exactly as described
  ("planned", "landing in Slice 1", "deliberate follow-on
  non-goal" vs the shipped migration); stale projection, no
  contract row breaks; agree.
- **Absent `## Pending execution`:** correct — nothing deferred.
  Every challenge is decided by single-expression delegation at
  fingerprinted bytes (inspection-sufficient), and the oracle
  file was executed green twice (W1 + this verification).
- **Structural gate (none):** judged sound — the single body
  exists, so principle 9's check-shape does not apply; a census
  gate over 11 heterogeneous `except` sites would be machinery.
  The principle-10 clause is at the owner and the re-check
  trigger (new raising pair outside `utils/imports.py`) is
  concrete.
- **Cells:** sharded/PG `inapplicable by construction` judged
  sound — verified from the primitive body (import + raise only;
  no database, alias, or dialect decision).
- **Diff vs AGENTS.md prose:** item diff vs baseline is the
  plan dispatch record alone; production diff is empty; no
  provenance, citation, or tier rule is engaged. Ruff on the
  touched paths is vacuous (W1 touched zero tracked `.py`) and
  passes.
- **No `(Worker-2)` defects.** W2-C1 above is a record-precision
  note corrected in place, with no bearing on the verdict.

Re-ran (shared tree, shared venv): `uv run pytest
tests/utils/test_imports.py --no-cov -n0 -q` → 16 passed;
`uv run mypy` → no issues, 119 files; `uv run basedpyright` →
0/0/0; `uv run python scripts/check_any.py` → 130 allowed uses
at 90 sites; `uv run ruff format --check` + `uv run ruff check`
on the touched paths → pass. No workspace run was needed: no
source-mutating proof is owed by a zero-edit item.

**Verdict: verified** (plain — no `proof:` entry remains).

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
