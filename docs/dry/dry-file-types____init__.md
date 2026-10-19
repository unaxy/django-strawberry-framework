# DRY review: `types/__init__.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

The target is a 35-line eager re-export leaf: module docstring (three
prose paragraphs), three `from .<submodule> import <name>` re-exports,
one three-member `__all__` tuple. It owns no definition with behavior;
it owns the subpackage's public surface membership (which three names
answer at the dotted `django_strawberry_framework.types` path, and the
withholding of everything else) plus two prose contracts (canonical
dotted-path posture; types→optimizer dependency direction).

Sites found, by role:

- Definitions composed by name: [base.py][types-base]`::DjangoType`
  (wt:600, HEAD:609), [finalizer.py][types-finalizer]`::finalize_django_types`
  (wt:776, HEAD:824),
  [utils/querysets.py][querysets]`::SyncMisuseError` (wt:123, HEAD:121,
  already indexed file-local at its owner) reached through the
  [relay.py][types-relay] redundant-alias hop (wt:44, HEAD:41, rationale
  comment wt:40-43, HEAD:37-40).
- Withheld-but-reachable dotted paths (docstring para 1 names four):
  `convert_scalar` ([converters.py][types-converters] wt:352, HEAD:353),
  `convert_choices_to_enum` (wt:718, HEAD:740),
  `_make_relation_resolver` ([resolvers.py][types-resolvers] wt:491,
  HEAD:477), `_attach_relation_resolvers` (wt:827, HEAD:803). All four
  def-verified at HEAD; dotted-path reachability is exercised by
  production imports ([mutations/inputs.py][mutations-inputs]:51 both
  revisions, [filters/inputs.py][filters-inputs] wt:356 / HEAD:355,
  [finalizer.py][types-finalizer]:81) and test imports (all HEAD-verified,
  see Freshness).
- Consumers of the leaf surface: the package root
  ([__init__.py][pkg-root]:52, CLEAN) re-exports all three names through
  the leaf into its own 38-name `__all__`; [list_field.py][list-field]
  (wt:83, HEAD:89) takes `DjangoType` through the leaf; the identity
  oracle [test_init.py][test-init] (`test_reexported_types_resolve_to_canonical_subpackage_definitions`,
  wt:292-361, HEAD:176-235) pins root≡leaf `is` for all three.
  Absolute-leaf import census repo-wide: exactly those oracle lines plus
  submodule-attribute imports (`import converters`, `import finalizer`,
  … — namespace use, not manifest use) and prose. Zero production or
  example consumers use the absolute leaf path; zero importers of any
  withheld name through the leaf; zero `types import *` sites.
- Second `SyncMisuseError` alias hop (listed, not counted):
  [permissions.py][permissions] (wt:136, HEAD:135) re-exports the same
  definition with a comment citing "the established `types/relay.py`
  convention" — a distinct dotted path (`permissions.SyncMisuseError`),
  same single definition.
- Sibling-flavor sweep (axis 1): all 13 sibling `__init__.py` leaves
  read at CLEAN bytes — [auth][auth-init], [extensions][extensions-init],
  [filters][filters-init], [forms][forms-init], [management][management-init],
  [management/commands][commands-init], [middleware][middleware-init],
  [mutations][mutations-init], [optimizer][optimizer-init],
  [orders][orders-init], [rest_framework][rest-init],
  [testing][testing-init], [utils][utils-init]. Five distinct postures,
  no shared driver (see R2).
- Module-hook census (HEAD `git grep`, package-wide): exactly two
  `def __getattr__` ([__init__.py][pkg-root]:98 CLEAN,
  [routers.py][routers] wt:539 / HEAD:533) — the standing
  no-third-hook trigger re-checked unfired.
- Optimizer→types census (HEAD `git grep`, package-wide): exactly one
  `from ..types` import inside `optimizer/`, the in-function lazy read
  at [walker.py][walker] (wt:1465, HEAD:1464) inside
  `_has_custom_id_resolver` (wt:1449, HEAD:1448), landing in
  [definition.py][types-definition]. The docstring's
  "single sanctioned exception" verifies byte-true.
- Contract sources: archived [spec-010][spec-010] step 11 + "Public API
  delta" (finalize re-exported from BOTH root and leaf "for symmetry
  with `DjangoType`); leaf docstring itself for the rest.
- Projections: [TREE.md][tree] renders the docstring first line twice
  (:286, :420, identical both revisions); root `__all__` + docstring
  mirror sentences describe the same membership from other levels.

No consolidation inside this file item. Two file-local rules, four
rejections (three CONVERGE on verified rows with fresh trigger checks,
one fresh), one minor HEAD defect (D1, stale-by-refactor prose),
zero new families, zero adoptions.

## Verification

### Enumeration

Instrument: `ast.parse` over the target file, every node in
`ast.Module.body` in order (5 statements), plus every bound name (4)
and every `__all__` member (3). Command and output recorded in the
work order; digest: `Expr(docstring)`, three `ImportFrom`, one
`Assign(__all__)`.

| # | Statement (target line) | Binds | Home |
|---|---|---|---|
| S0 | docstring, paras 1-3 (:1-29) | — (prose) | paras 1-2 → FL1 `types-leaf-manifest`; para 3 → FL2 `types-dependency-direction-prose` |
| S1 | `from .base import DjangoType` (:31) | `DjangoType` | FL1 |
| S2 | `from .finalizer import finalize_django_types` (:32) | `finalize_django_types` | FL1 |
| S3 | `from .relay import SyncMisuseError` (:33) | `SyncMisuseError` | FL1 |
| S4 | `__all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")` (:35) | `__all__` (3 members) | FL1 |

Coverage: 5/5 statements, 4/4 bound names, 3/3 `__all__` members homed.
Cross-file candidates raised by the challenges route to rejections
R1–R4 (recorded at their rows, all in this artifact — no holding
family owed since every count came back 1). No member is unassigned;
no consolidation lives here.

### Matrix

1. **Cross-flavor policy mirroring — SEARCHED.** All 13 sibling leaves
   read in full (all CLEAN; hashes under Freshness). Posture census:
   eager re-export + plain `__all__` tuple (types/, auth/,
   optimizer/, utils/); eager + typed `__all__` tuple (forms/,
   mutations/, filters/ +orders/ with Decision-11 helper + ledger +
   clear row); eager + `__all__` LIST (extensions/, testing/); bare
   marker, no re-export (management/, management/commands/,
   middleware/ with documented no-re-export posture); guard-only, no
   manifest (rest_framework/). Root-mirror posture also varies:
   via-leaf (types/, forms/, mutations/), partial/direct-submodule
   (extensions/, optimizer/, types/ file-output quartet bypassing the
   leaf at [__init__.py][pkg-root]:53-58), absent (auth/ structural
   opt-in, filters/, orders/, testing/, utils/), lazy-`__getattr__`
   only (rest_framework/). Nearest shapes to this leaf: forms/ and
   mutations/ (eager + root-via-leaf). No shared membership, no shared
   container, no shared driver → R1 (root) + R2 (siblings). The
   redundant-`as` re-export idiom at [relay.py][types-relay]:44 and
   [permissions.py][permissions]:136 vs the leaf's plain form → R4.
2. **Sync/async twins — INAPPLICABLE.** The leaf defines no callable
   and no await boundary; `SyncMisuseError` is a re-exported name
   whose sync/async contract lives at its [querysets][querysets]
   definition (already indexed file-local there).
3. **Derived rather than repeated knowledge — SEARCHED.** Three
   pairings, all same-file idiom, no cross-file derivation to
   consolidate: (a) `__all__` members repeat the three import names —
   the standard manifest pairing, order gate-held by RUF022 (selected
   wholesale at [pyproject.toml][pyproject]:161 both revisions,
   RUF022 never ignored; `ruff check` + `ruff format --check` pass on
   the target) and membership failure-loud via the identity oracle;
   (b) the docstring's "(DjangoType, SyncMisuseError, and
   finalize_django_types)" lists the same three in `__all__` order —
   same-file projection, moves in the same edit; (c) root `__all__`
   carries the three names alphabetically among 38 — different
   membership, different order, owned at the root → R1. Imports are
   module-sorted (`base` < `finalizer` < `relay`); `__all__` is
   ASCII-sorted — both orders gate-clean (near-miss N3 cleared, no row).
4. **Inverse / round-trip pairs — INAPPLICABLE.** No encode/decode,
   pack/unpack, or build/parse grammar in a re-export leaf; the
   finalize/register and seal/unseal lifecycles merely named here are
   owned by [finalizer.py][types-finalizer], `registry.py`, and
   [querysets][querysets], outside this file's surface.
5. **Contracts restated in another medium — SEARCHED.** Media census
   with roles: root manifest = consumer (owns its 38 names; imports
   the three through the leaf — principle 6, compose by name);
   [test_init.py][test-init] identity test = independent oracle
   (spells the leaf path literally; a dropped leaf name fails the
   import, not the oracle); [TREE.md][tree]:286/:420 = projection
   (first line ×2, re-rendered by `build_tree_md.py`); [spec-010][spec-010]
   step 11 + Public API delta = contract source (S2's dual
   re-export "for symmetry with `DjangoType`"); leaf docstring paras
   1-2 = projection of S1–S4, para 3 = the FL2 statement. Every medium
   a change forces to move is named in the challenges; only the leaf
   counts. → FL1 (+R1 for the root side).
6. **Enforcement by omission — SEARCHED.** Withheld population
   enumerated, each member checked: the four named helpers all
   def-exist at HEAD and stay dotted-reachable (production + test
   importers HEAD-verified, see System trace); the unnamed remainder
   = every other public in the seven siblings (seven-module census via
   `git ls-tree HEAD`, 8 entries incl. the leaf). Negative sweeps:
   zero leaf imports of any withheld name repo-wide; zero
   `from ...types import *` sites; `__all__` admits exactly the three
   imports (no leakage, no omission). Withholding is enforced by
   Python attribute semantics plus `__all__` for star imports — no
   second definition, no enforcement gap, no defect. The root's four
   direct-submodule file-type names (bypassing the leaf by design)
   further prove each level owns its surface → R1. The `__all__` has
   no exact-set pin (cf. standing oracle-economy precedent) — recorded
   as non-defect observation O1 under F1, not a defect: zero star
   consumers, and the identity oracle pins all three members by name.

### Challenges

Counts are AUTHORITATIVE definitions only; consumers, oracles, and
projections that also move are listed, never counted. All proofs
`static-reviewed` (import composition + prose-vs-imports, inspection
decides; see Pending execution for why no execution was owed).

FL1 `types-leaf-manifest` (S0 paras 1-2, S1–S4):

- C1 "Add a fourth leaf name (e.g. `DjangoTypeDefinition`)."
  Definitions forced: 1 — the leaf (import line + `__all__` member +
  docstring sentence move as one edit). Consumers/oracles/projections
  listed: root manifest (may mirror or not — the file-type quartet
  proves independence), identity oracle (unchanged — it pins only the
  three it spells), TREE.md (first line only; unchanged). Count: 1.
- C2 "Drop `SyncMisuseError` from the leaf." Definitions: 1 (the
  leaf). Moves-but-not-counted: root:52 import breaks (consumer),
  oracle breaks (proves oracle independence). Does NOT move: the
  [relay.py][types-relay] `as` hop, the [querysets][querysets]
  definition, the [permissions.py][permissions] hop — proving the hops
  are per-level surface, not copies. Count: 1.
- C3 "`SyncMisuseError` moves again (out of `utils/querysets.py`)."
  Definitions: 1 ([relay.py][types-relay] hop updates; leaf S3 is
  UNCHANGED — it composes the subpackage layer by name per principle
  6). A direct `..utils.querysets` import at the leaf would force a
  second move; the via-`.relay` path is load-bearing. Count: 1.
- C4 "Reorder `__all__` non-ASCIIbetically." Definitions: 1 (the
  leaf) and the RUF022 gate fires. Count: 1.
- C5 "Withhold one of the three (dotted-only, e.g. finalize via
  `types.finalizer`)." Definitions: 1 (the leaf). The oracle breaks
  (its leaf-path import fails) — again proving oracle independence;
  [spec-010][spec-010] would need a contract amendment (contract
  source, not a definition). Count: 1.

FL2 `types-dependency-direction-prose` (S0 para 3):

- C6 "Optimizer gains a second `types/` import." Definitions: 1 —
  this paragraph must re-decide the 'single sanctioned exception'
  sentence. The [walker.py][walker] inline comment is bilateral prose
  for a different audience (walker editors), listed not counted → R3.
  Count: 1.
- C7 "`types/` drops `pascal_case`." Definitions: 1 (the `..utils`
  parenthetical). Note D1 IS this challenge already true for two of
  the three names. Count: 1.
- C8 "A `utils/`→`types/` inverse import appears." Definitions: 1
  (the 'bounded by the same rule' sentence). Count: 1.

Rejections (contract difference + reconsideration trigger; full
records under Findings):

- R1 `types-leaf-vs-root-manifest`: posit "root drops the three while
  the leaf keeps them" → root moves (1), leaf moves 0 (its mirror
  sentence goes stale — projection lag, not a definition). Posit the
  reverse → leaf moves (1), root import breaks as consumer.
  Difference: membership owned per level (root: 38 names incl. four
  direct-submodule names the leaf withholds; leaf: exactly three).
  CONVERGE with the verified orders/testing/rest-framework
  leaf-vs-root direction — triggers re-checked unfired (no shared
  driver; spec-010 paired one decision, precedent unpairs the next).
- R2 `types-leaf-vs-sibling-manifest`: posit "every leaf gains a
  helper+ledger" → 14 independent edits (guard/marker/helper/eager
  postures; tuple/typed-tuple/list/no-container). Count 14 =
  independence. CONVERGE with verified
  `rest-framework-leaf-vs-sibling-manifest` — trigger (shared manifest
  driver or coupled membership) unfired on the fresh 14-leaf census.
- R3 `types-dependency-prose-vs-walker-comment`: posit "reword the
  cycle rationale" → each side rewords for its own audience
  (subpackage importers vs walker editors); merging orphans one.
  CONVERGE with verified hints-R4 bilateral-import-rationale-prose —
  trigger (one shared statement) unfired.
- R4 `types-leaf-plain-reexport-vs-module-as-alias`: posit "spell all
  re-exports identically" → either direction breaks a lint contract:
  `__init__.py`+`__all__` marks re-export intent for plain imports
  (F401-clean), while regular modules
  ([relay.py][types-relay]:44, [permissions.py][permissions]:136) need
  the redundant alias. Fresh rejection (no prior verdict; relay item
  undispatched). Trigger: a lint/gate change treating both spellings
  identically.

Considered, no row (near-misses / observations, cleared with evidence):

- N1 "canonical" (para 1) vs dominant root usage: cleared — no
  contradiction. 'Canonical' = the canonical *subpackage* spelling
  (vs `types.base`), coexisting with the root as primary consumer
  path (para 2's own "consumers that prefer" framing). Census:
  root-path dominant across tests/examples; absolute leaf path used
  only by the oracle; relative leaf path by root:52 + list_field:83;
  one intra-package dotted-submodule importer
  ([inspect_django_type.py][inspect]:63) — internal code reaching an
  internal path the docstring explicitly blesses as reachable.
- N2 walker function naming (para 3 names walker's
  `origin_has_custom_id_resolver` "fallback"; the walker def is
  `_has_custom_id_resolver`): cleared — the name resolves 3× in
  [walker.py][walker] (docstring, lazy import, call) and every
  operative claim verifies (in-function, imports `types.definition`,
  dodges the init cycle, single exception per the package-wide HEAD
  census). Imprecise possessive, true substance; not a contradiction.
- N3 `__all__`+docstring order (DjangoType, SyncMisuseError,
  finalize…) vs import order (base, finalizer, relay): cleared — both
  orders independently conventional and gate-clean (module-sorted
  imports, ASCII-sorted manifest).
- O1 oracle economy: no exact-set pin for the 3-member `__all__`
  (star-import behavior unpinned). Non-defect per the standing
  testing-leaf precedent: zero star-import consumers, and the identity
  oracle pins every member by literal name.

## Findings

### F1 `types-leaf-manifest` — file-local

- **Contract + variation.** The leaf admits exactly three public
  names — `DjangoType` (para 1: the canonical dotted-path spelling,
  folder layout internal), `finalize_django_types` (contracted by
  [spec-010][spec-010] "for symmetry with `DjangoType`"),
  `SyncMisuseError` (via the subpackage's own relay hop) — in an
  ASCII-sorted `__all__`; everything else in the seven siblings stays
  dotted-reachable but unexported. Varies on: membership (which
  names), order (gate-held), withholding boundary (omission).
- **Sites + roles.** Definition: this leaf (S0 paras 1-2, S1–S4).
  Composed definitions (owned elsewhere, not counted):
  [base.py][types-base]`::DjangoType`,
  [finalizer.py][types-finalizer]`::finalize_django_types`,
  [querysets][querysets]`::SyncMisuseError` via the
  [relay.py][types-relay] hop. Consumers: root manifest
  ([__init__.py][pkg-root]:52 + `__all__`), [list_field.py][list-field]
  (:83/:89). Oracle: [test_init.py][test-init] identity test (all
  three, HEAD:233-235). Projections: TREE.md first line ×2, docstring
  mirror sentences, [spec-010][spec-010] export-points prose.
  Listed-not-counted sibling hop: [permissions.py][permissions]:136.
- **Challenges.** C1–C5, each count 1 (see above).
- **Owner + lifetime.** Owner is this leaf: narrowest surface every
  legitimate consumer (root, list_field, oracle, dotted-path
  consumers) can depend on without reaching into submodules. No
  stored derivation (pure re-export; "not cached").
- **Migration.** None — zero-edit; nothing moves.
- **Distinct behavior.** The four direct-submodule root names
  (`DjangoFile*`, [__init__.py][pkg-root]:53-58) stay leaf-withheld by
  design; submodule-attribute namespace use (`import converters`, …)
  is Python semantics, unaffected by the manifest.
- **Behavioral proof.** `static-reviewed`: membership = import lines
  + `__all__` (wrong result rejected: a fourth exported name or a
  missing member — visible in the 5-statement body); withholding =
  negative sweeps (zero leaf imports of withheld names, zero star
  sites); mirror = root:52 read + identity oracle executing the path
  in CI (existing oracle, not authored here). No execution owed (see
  Pending execution).
- **Structural gate.** Pre-existing, no new gate: RUF022
  (`__all__` sort; selected wholesale both revisions, never ignored;
  `ruff check` green on the target) + the identity oracle (fails by
  ImportError if a leaf name is dropped — failure mode read off the
  test's own import lines, no mutation run needed for a cited,
  unmodified gate). Negative control: N/A — no new gate introduced;
  a hand copy of the three import lines would pass the identity
  oracle (it pins identity, not single-siting), which is why the
  finding stays file-local rather than claiming a consolidation.
- **Coupling.** None.
- **Freshness.** Full input table (worktree `wt`, HEAD `hd` at
  `0c0537e2`; every load-bearing claim re-verified at HEAD bytes —
  worktree/HEAD line pairs are given per site above):

| Input | wt | hd | State |
|---|---|---|---|
| `types/__init__.py` (target) | `1bf69028` | `1bf69028` | CLEAN |
| `types/base.py` | `dc67f084` | `dda91365` | DIRTY, regions HEAD-verified |
| `types/converters.py` | `f6cadb08` | `058f1081` | DIRTY, regions HEAD-verified |
| `types/definition.py` | `1c59a3fe` | `fa6c4d33` | DIRTY, regions HEAD-verified |
| `types/finalizer.py` | `b9d8acb2` | `de34ae2a` | DIRTY, regions HEAD-verified |
| `types/relations.py` | `5e9b5cdb` | `5e9b5cdb` | CLEAN |
| `types/relay.py` | `4b2a9df5` | `52439862` | DIRTY, regions HEAD-verified |
| `types/resolvers.py` | `640905c6` | `72d62dc4` | DIRTY, regions HEAD-verified |
| `__init__.py` (root) | `0ef72601` | `0ef72601` | CLEAN |
| `list_field.py` | `450e87cd` | `21380eb7` | DIRTY, :89 HEAD-verified |
| `permissions.py` | `ef66f8b9` | `72102cc0` | DIRTY, :135 HEAD-verified |
| `utils/querysets.py` | `8fc556d5` | `3616927d` | DIRTY, :121 HEAD-verified |
| `utils/relations.py` | `05ff55b0` | `8dbc3fe6` | DIRTY, defs HEAD-verified |
| `optimizer/walker.py` | `d5759ef8` | `75f9c6b6` | DIRTY, :1448-1466 HEAD-verified |
| `routers.py` | `e18772f7` | `7d5e4814` | DIRTY, :533 HEAD-verified |
| `mutations/inputs.py` | `840da733` | `fc442047` | DIRTY, :51 HEAD-verified |
| `filters/inputs.py` | `a932dbf8` | `82b52d97` | DIRTY, :355 HEAD-verified |
| `management/commands/inspect_django_type.py` | `bb63204c` | `2807d0fc` | DIRTY, :63 HEAD-verified |
| `auth/__init__.py` | `2e480818` | `2e480818` | CLEAN |
| `extensions/__init__.py` | `dc3ebdc2` | `dc3ebdc2` | CLEAN |
| `filters/__init__.py` | `86b25818` | `86b25818` | CLEAN |
| `forms/__init__.py` | `cfd550b2` | `cfd550b2` | CLEAN |
| `management/__init__.py` | `beb4e0ee` | `beb4e0ee` | CLEAN |
| `management/commands/__init__.py` | `31cb58b8` | `31cb58b8` | CLEAN |
| `middleware/__init__.py` | `6e1b64ca` | `6e1b64ca` | CLEAN |
| `mutations/__init__.py` | `c13283f8` | `c13283f8` | CLEAN |
| `optimizer/__init__.py` | `d400569a` | `d400569a` | CLEAN |
| `orders/__init__.py` | `ed546f9c` | `ed546f9c` | CLEAN |
| `rest_framework/__init__.py` | `45cf7b63` | `45cf7b63` | CLEAN |
| `testing/__init__.py` | `48b45d1b` | `48b45d1b` | CLEAN |
| `utils/__init__.py` | `1a4c2ec8` | `1a4c2ec8` | CLEAN |
| `tests/base/test_init.py` | `239648ed` | `4cc12105` | DIRTY, oracle HEAD-verified |
| `tests/mutations/test_inputs.py` | `118f431c` | `b001451d` | DIRTY, :406/:446 HEAD-verified |
| `tests/forms/test_inputs.py` | `6c4617aa` | `95f71cb5` | DIRTY, :591 HEAD-verified |
| `tests/rest_framework/test_inputs.py` | `fa60df50` | `e6636d41` | DIRTY, :351 HEAD-verified (wt :371) |
| `tests/types/test_resolvers.py` | `d78d605f` | `346e945d` | DIRTY, :39/:106 HEAD-verified |
| `docs/TREE.md` | `769c2743` | `5d562733` | DIRTY, :286/:420 HEAD-verified |
| `docs/SPECS/spec-010-foundation-0_0_4.md` | `408e3536` | `408e3536` | CLEAN |
| `pyproject.toml` (RUF select) | `964c1339` | `9be86493` | DIRTY, :161 + zero RUF022 HEAD-verified |
| `docs/dry/dry-0_0_15.md` (index conventions) | `3c454a40` | `ba411b27` | DIRTY (concurrent Worker-0 writes) |

Searched populations (replayable census commands, all run at HEAD
where HEAD-pinned): package-wide `^def __getattr__` (= 2);
package-wide `from ..types` (= 15 sites, exactly one under
`optimizer/`, in-function); repo-wide absolute-leaf imports (oracle
lines + submodule-attribute uses + prose, enumerated above);
repo-wide withheld-name leaf imports (= 0); repo-wide
`types import *` (= 0); `__all__` in `types/` (= 1 manifest; other
hits are `Meta.fields="__all__"` strings, a different rule).
Modules EXCLUDED on body strength: the 13 sibling leaves (postures
read, membership disjoint — fingerprints above) and the 13
non-walker `optimizer/` modules (negative on the `..types` census;
population closed by the package-wide `git grep`, walker the sole
hit with fingerprints above).

### F2 `types-dependency-direction-prose` — file-local

- **Contract + variation.** Docstring para 3 states the layering:
  `types/` consumes `optimizer/` (FieldMeta, OptimizerHint, plan
  helpers, framework-wide logger — all four HEAD-verified in the
  sibling import blocks) one-way at module-import time; the single
  sanctioned exception is [walker.py][walker]'s in-function lazy read
  of `types.definition`; `types/` consumes `..utils` leaf helpers
  (parenthetical — D1 filed: two of three names dead); shared
  primitives belong in `optimizer/` or a sibling utility module.
  Varies on: consumed-name list, exception count, inverse-direction
  bound.
- **Sites + roles.** Definition (statement): this paragraph — the only
  place the rule is stated as a rule. Bilateral prose (listed, not
  counted): the [walker.py][walker]:1461-1464 lazy-import comment
  (cycle reason at the import site) → R3. Enforcement: Python import
  semantics (a module-top `optimizer`→`types` import would cycle —
  the walker comment says exactly so); no mechanical gate.
- **Challenges.** C6–C8, each count 1.
- **Owner + lifetime.** Owner is this leaf: the subpackage boundary
  statement lives with the subpackage surface. No stored derivation.
- **Migration.** None — zero-edit (D1 unfixed per item rules).
- **Distinct behavior.** The rule binds `optimizer/`↔`types/` only;
  filters/mutations/orders/rest_framework import `types/` submodules
  at top level legitimately (HEAD census: 14 such sites outside
  `optimizer/`).
- **Behavioral proof.** `static-reviewed`: every operative claim
  re-derived at HEAD bytes (import census 14/14, lazy-import
  singularity, seven-module `ls-tree`, D1 bare-word census). Wrong
  result rejected: a second top-level optimizer→types import or a
  consumed name with zero importers — the sweeps came back 1 and
  (for D1) 0 respectively.
- **Structural gate.** None pre-exists; none introduced (a new
  import-direction gate is a project-level mechanism, out of scope
  for a file item — the folder/project items own that question).
  Gate-only justification: the paragraph is prose posture, and prose
  posture findings carry no negative control.
- **Coupling.** None (D1 homing is editorial, blocks nothing).
- **Freshness.** As F1 (same table; D1 additionally pins
  `f83bb71b`/`d2e80523`/`2bcd50bd`/`e1ba094e` commit bytes, immutable).

### R1 `types-leaf-vs-root-manifest` — rejected

Difference: membership owned per level. The leaf admits exactly three
names and withholds the file-output quartet; the root admits 38 names
alphabetically, taking three through the leaf and four through
`types.converters` directly. Either side moves without forcing the
other (challenges under R1 above); [spec-010][spec-010] paired one
decision (finalize), the quartet unpairs the next. Trigger: a shared
manifest driver or a standing must-mirror rule — re-checked unfired.
CONVERGE with the verified orders/testing/rest-framework
leaf-vs-root direction on fresh evidence. Durable home: spec-010
step 11 + Public API delta + the leaf docstring. Freshness: as F1.

### R2 `types-leaf-vs-sibling-manifest` — rejected

Difference: 14 leaves, five postures (eager plain-tuple / eager
typed-tuple / eager list / bare marker / guard-only), disjoint
memberships, disjoint containers — no shared variation axis for a
driver to own. A cross-leaf change costs 14 independent edits =
independence, not duplication. Trigger: a shared manifest driver or
coupled membership — unfired on the fresh full-leaf census.
CONVERGE with verified `rest-framework-leaf-vs-sibling-manifest` on
fresh evidence. Durable home: each leaf docstring (this leaf's paras
1-2). Freshness: as F1 (all 13 sibling fingerprints above).

### R3 `types-dependency-prose-vs-walker-comment` — rejected

Difference: two audiences. The leaf paragraph states the rule for
subpackage importers (one-way + exception + bound); the
[walker.py][walker]:1461-1464 comment states the cycle reason for
walker editors at the import site. Merging orphans one audience;
rewording either never forces the other (C6). Trigger: one shared
statement — unfired. CONVERGE with verified hints-R4
bilateral-import-rationale-prose on fresh evidence. Durable home: the
leaf docstring + the walker comment. Freshness: as F1.

### R4 `types-leaf-plain-reexport-vs-module-as-alias` — rejected

Difference: two lint contracts. Plain `from .x import y` in an
`__init__.py` with `__all__` marks re-export intent (F401-clean —
`ruff check` green on the target); regular modules need the redundant
alias ([types/relay.py][types-relay]:44,
[permissions.py][permissions]:136). Spelling all three sites
identically breaks one contract or the other. Fresh rejection (no
prior verdict; the relay file item is undispatched). Trigger: a
lint/gate change treating both spellings identically. Durable home:
this finding + the relay/permissions rationale comments. Freshness:
as F1.

## Defects

### D1 Stale `..utils` consumption parenthetical names two helpers the subpackage does not import (minor, HEAD, unfixed)

- **What.** Docstring para 3 (target :26-27, CLEAN line): "consumes
  leaf helpers from `..utils` (`pascal_case`, `RelationKind`,
  `relation_kind`)". `pascal_case` verifies ([converters.py][types-converters]
  HEAD import + call). `RelationKind` and `relation_kind` have ZERO
  importers across all seven siblings at HEAD (bare-word census:
  only `is_many_side_relation_kind` imports/calls, one docstring
  mention, and `field_meta.relation_kind` attribute reads). The names
  exist ([utils/relations.py][utils-relations] HEAD:42/:160/:235) —
  they are just not consumed here. The live `..utils.relations`
  consumption is `instance_accessor` + `is_many_side_relation_kind`
  (HEAD-verified both import lines).
- **Provenance (stale-by-refactor + partial repair).** Accurate at
  birth: `f83bb71b` wrote the sentence when [relations.py][types-relations]:24
  imported `RelationKind` and [resolvers.py][types-resolvers]:46
  imported `relation_kind`. `d2e80523` dropped the resolvers import;
  `2bcd50bd` dropped the relations import; neither updated the
  sentence. `e1ba094e` (the maintainer, Sep 25) then removed `snake_case` from
  the same parenthetical (field_map rekeying) but left the two dead
  names — the diff is quoted in the trace record.
- **Contract.** Docstring-claims-imports: every other consumption
  claim in the paragraph verifies (four optimizer categories 14/14,
  walker exception, seven-module census), so the paragraph reads as a
  verified manifest, not loose prose. A reader extending `..utils`
  consumption trusts a list that is 2/3 dead.
- **Fix shape (not applied).** Swap the two dead names for the live
  ones (`instance_accessor`, `is_many_side_relation_kind`) or
  re-survey the parenthetical; one docstring edit, no behavior change.
- **Owner.** File `types/__init__.py` (the docstring). Routes to
  normal closeout homing (CLEAN-line HEAD defect; blocks nothing).

No other defects. Near-misses N1–N3 and observation O1 are cleared
under Challenges and need no homing.

## Pending execution

None. No `proof:` entry: every conclusion is `static-reviewed`
(import composition, census counts, prose-vs-imports — inspection
decides; nothing ordering-, transactional-, or async-sensitive was
judged). No `gate:` entry: no regression witness was needed
(zero-edit; the cited identity oracle and RUF022 already execute in
CI). Sharded and PG cells are inapplicable by construction: the leaf
reaches no database, alias, or dialect decision (three re-exports +
manifest + prose). No workspace run was needed; none was made.

## Judgment

Zero-edit file item. Five rules traced: two file-local with proving
challenges (F1 manifest + withholding, C1–C5; F2 dependency prose,
C6–C8), four rejected with contract differences + triggers (R1
leaf-vs-root, R2 leaf-vs-sibling, R3 prose pair, R4 plain-vs-alias;
three CONVERGE on verified rows with fresh trigger checks, one
fresh). Enumeration covers 5/5 statements, 4/4 bound names, 3/3
`__all__` members. One minor HEAD defect filed (D1, stale
parenthetical, unfixed); three near-misses cleared with evidence; one
oracle-economy observation recorded, not filed. No families named, no
adoptions, no pending execution, no production edits.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs `ITEM_BASELINE=6db6579fea97227cd6e4eacb98de130aad8b0b15`:
`git status --short -- django_strawberry_framework/types/__init__.py`
is empty and the working blob `1bf69028dbdcac9a42f6b6ba05e1220fdde0a155`
equals `HEAD:django_strawberry_framework/types/__init__.py` at HEAD
`0c0537e2` — target CLEAN, so no hunk attribution was owed. The
artifact itself is a new untracked file at the exact dispatched path
`docs/dry/dry-file-types____init__.md`, the item's only output. The
`## Owned changes` ledger gains no row from this item. Concurrent dirt
(hunt edits across `django_strawberry_framework/`, test churn,
`docs/dry/dry-0_0_15.md`) left untouched; every load-bearing claim
rests on HEAD bytes with both fingerprints recorded. `uv run ruff
check` + `uv run ruff format --check` run read-only on the target
(both pass; no `--fix`, no `.py` touched). No shared-tree pytest run
(AGENTS.md: only when asked; inspection + the pre-existing identity
oracle suffice). No workspace runs (nothing source-mutating was
needed). No `docs/dry/temp-tests/` scratch created. No commit.

Worker-0 instructions: (a) tick the plan item `File types/__init__.py`
once Worker 2 agrees; (b) add the six `## Responsibility index` rows
under `## Index rows for Worker-0` verbatim (holding item
`File types/__init__.py`); (c) add the `## Families` items under
`## Families` (none). No commit.

## Index rows for Worker-0

| `types-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/types/__init__.py`) | `django_strawberry_framework/types/__init__.py` (+3 owner modules) | File `types/__init__.py` | file-local |
| `types-dependency-direction-prose` | `django_strawberry_framework/types/__init__.py` (para 3: optimizer one-way + walker lazy exception + `..utils` consumption; D1 filed on the utils parenthetical) | `django_strawberry_framework/types/__init__.py` | File `types/__init__.py` | file-local |
| `types-leaf-vs-root-manifest` | `django_strawberry_framework/types/__init__.py` (rejection recorded here; CONVERGE with verified orders/testing/rest-framework leaf-vs-root direction on fresh evidence; durable home spec-010 step 11 + Public API delta + leaf docstring) | `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/__init__.py` | File `types/__init__.py` | rejected |
| `types-leaf-vs-sibling-manifest` | `django_strawberry_framework/types/__init__.py` (rejection recorded here; CONVERGE with verified rest-framework-leaf-vs-sibling-manifest on fresh evidence — 14 leaves, 5 postures, trigger unfired) | `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/auth/__init__.py`, `django_strawberry_framework/extensions/__init__.py`, `django_strawberry_framework/filters/__init__.py`, `django_strawberry_framework/forms/__init__.py`, `django_strawberry_framework/management/__init__.py`, `django_strawberry_framework/management/commands/__init__.py`, `django_strawberry_framework/middleware/__init__.py`, `django_strawberry_framework/mutations/__init__.py`, `django_strawberry_framework/optimizer/__init__.py`, `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/utils/__init__.py` | File `types/__init__.py` | rejected |
| `types-dependency-prose-vs-walker-comment` | `django_strawberry_framework/types/__init__.py` (rejection recorded here; CONVERGE with verified hints-R4 bilateral-import-rationale-prose on fresh evidence; durable home leaf docstring + walker comment) | `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/optimizer/walker.py` | File `types/__init__.py` | rejected |
| `types-leaf-plain-reexport-vs-module-as-alias` | `django_strawberry_framework/types/__init__.py` (rejection recorded here; fresh pair, no prior verdict — `__init__`+`__all__` vs regular-module redundant alias; trigger: a lint/gate change treating both spellings identically) | `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/permissions.py` | File `types/__init__.py` | rejected |

## Families

None. No new family named, no adoption into an open family (every
change challenge counted exactly one authoritative definition). The
holding items for the composed definitions are the undispatched file
items `types/base.py`, `types/finalizer.py`, `types/relay.py` and the
verified file item `utils/querysets.py` (whose file-local row already
owns the `SyncMisuseError` catch-shape contract).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[pyproject]: ../../pyproject.toml

<!-- docs/ -->
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-010]: ../SPECS/spec-010-foundation-0_0_4.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[commands-init]: ../../django_strawberry_framework/management/commands/__init__.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[list-field]: ../../django_strawberry_framework/list_field.py
[management-init]: ../../django_strawberry_framework/management/__init__.py
[middleware-init]: ../../django_strawberry_framework/middleware/__init__.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[optimizer-init]: ../../django_strawberry_framework/optimizer/__init__.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[permissions]: ../../django_strawberry_framework/permissions.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[rest-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[routers]: ../../django_strawberry_framework/routers.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-init]: ../../django_strawberry_framework/utils/__init__.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-init]: ../../tests/base/test_init.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Fresh context; HEAD `0c0537e2` unmoved throughout. All censuses below were
re-run by Worker-2 at HEAD bytes (worktree read-only; no source-mutating run
was needed so no `workspace.py` run id exists for this pass). Zero `.py`
touched by the item, so no ruff fix/format pass was owed; `uv run ruff check`
+ `uv run ruff format --check` were run read-only on the target and both pass.

### Own trace (recorded before reconciliation)

Target re-read cold: a 35-line eager re-export leaf. My `ast.parse`
reproduction gives exactly `Expr(docstring :1-29)`, three `ImportFrom`
(`.base`/`DjangoType`, `.finalizer`/`finalize_django_types`,
`.relay`/`SyncMisuseError`), one `Assign(__all__)` 3-tuple: 5 statements, 4
bound names, 3 members. `git ls-tree HEAD` on `types/` gives 8 entries (leaf
+ 7 siblings), matching the docstring's "seven sibling modules".

Sites and roles as I derive them: the three composed definitions live at
`types/base.py::DjangoType` (HEAD:609), `types/finalizer.py::finalize_django_types`
(HEAD:824), `utils/querysets.py::SyncMisuseError` (HEAD:121, already indexed
file-local at its owner) reached via the `types/relay.py` redundant-alias hop
(HEAD:41, rationale comment HEAD:37-40). Consumers: the package root
(`__init__.py`:52, via-leaf for all three) and `list_field.py` (HEAD:89).
Oracle: `tests/base/test_init.py::test_reexported_types_resolve_to_canonical_subpackage_definitions`
(HEAD:176-235, three literal leaf imports + three `is` asserts at :233-235).
Projections: `docs/TREE.md` first line x2 (:286/:420 byte-identical),
docstring mirror sentences, `spec-010` step 11 + Public API delta (contract
source for the finalize dual re-export "for symmetry with `DjangoType`").
Listed-not-counted second hop: `permissions.py` (HEAD:135, "established
`types/relay.py` convention" comment).

My posited changes and counts: add a fourth leaf name (1: the leaf);
drop `SyncMisuseError` from the leaf (1: the leaf; hops/root/oracle move as
consumer/oracle/proof, not definitions); `SyncMisuseError` moves again (1: the
relay hop; leaf S3 unchanged via the `.relay` path — load-bearing);
reorder `__all__` (1 + RUF022 fires); withhold one name to dotted-only (1);
second optimizer `types/` import (1: the para-3 sentence); drop a `..utils`
name (1: the parenthetical); a `utils/`-to-`types/` inverse import (1: the
bound sentence). Every count is 1. My homes: leaf manifest + withholding
file-local here; dependency-direction prose file-local here; leaf-vs-root,
leaf-vs-sibling, prose-vs-walker-comment, and plain-vs-as-alias all rejected
on per-level membership / five postures / two audiences / two lint contracts.
No second definition anywhere: no family, no adoption, zero-edit.

Reconciliation: this matches Worker-1's assignment exactly (FL1, FL2, R1-R4,
zero-edit, 6 index rows). The only deltas are five immaterial record notes
(E1-E5 below); none moves a home, count, gate, or defect.

### Enumeration — AGREE

5/5 statements + 4/4 bound names + 3/3 `__all__` members, member-by-member
against my own AST reproduction above. S0 paras 1-2 -> FL1, para 3 -> FL2,
S1-S4 -> FL1. No member unassigned; cross-file candidates route to R1-R4 with
every count at 1, so no holding family is owed.

### Matrix — AGREE (all six axes)

- Axis 1 SEARCHED: all 13 sibling leaves re-read at CLEAN bytes (hashes match
  the table digit-for-digit); my posture census reproduces five postures
  (plain-tuple / typed-tuple / list / bare marker / guard-only) with disjoint
  memberships. Nearest shapes (forms/, mutations/) confirmed nearest, still
  disjoint. -> R1 + R2 + R4.
- Axis 2 INAPPLICABLE: correct reason — the leaf defines no callable and no
  await boundary; the sync/async contract lives at the querysets definition.
- Axis 3 SEARCHED: all three pairings re-derived (manifest pairing RUF022-held
  with `RUF` selected wholesale at `pyproject.toml`:161 and zero `RUF022`
  ignores; same-file docstring list; root's distinct 38-import membership).
  Import order module-sorted, `__all__` ASCII-sorted, both gate-clean.
- Axis 4 INAPPLICABLE: correct reason — no encode/decode or build/parse
  grammar in a re-export leaf; the named lifecycles are owned elsewhere.
- Axis 5 SEARCHED: roles confirmed (root = consumer composing by name per
  principle 6; identity test = independent oracle spelling the leaf path
  literally; TREE.md = projection; spec-010 = contract source; paras 1-2 =
  projection of S1-S4, para 3 = the FL2 statement).
- Axis 6 SEARCHED: withheld population re-verified — the four named helpers
  def-exist at HEAD (`converters.py`:353/:740, `resolvers.py`:477/:803) with
  dotted-path reachability exercised by production importers
  (`mutations/inputs.py`:51, `filters/inputs.py`:355, `finalizer.py`:81, all
  HEAD-verified) and the six cited test import lines (all six HEAD-verified).
  Negative sweeps reproduced: zero withheld-name leaf imports, zero
  `types import *` code sites (only a consumer-app prose example in spec-010),
  `__all__` admits exactly the three imports. No gap, no defect.

### Convergences R1-R3 — AGREE on fresh evidence

- R1 (leaf-vs-root): my fresh checks — root takes three through the leaf
  (:52) plus four `types.converters` file-type names directly (:53-58); the
  leaf withholds the quartet; spec-010 paired exactly one decision
  (finalize); no shared manifest driver exists. Trigger
  (shared driver / must-mirror rule) re-checked unfired. CONVERGE direction
  holds.
- R2 (leaf-vs-sibling): my fresh 14-leaf census reproduces 5 postures and
  disjoint memberships/containers; a cross-leaf change costs 14 independent
  edits. Trigger (shared driver / coupled membership) unfired. CONVERGE holds.
- R3 (prose-vs-walker-comment): both texts re-read — leaf paragraph states the
  rule for subpackage importers, `walker.py`:1461-1464 states the cycle reason
  for walker editors at the import site. Merging orphans one audience; C6
  count 1 reproduced. Trigger (one shared statement) unfired. CONVERGE with
  hints-R4 holds.
- Module-hook trigger re-check: exactly two module-level `def __getattr__`
  (root:98, routers:533); the three other HEAD hits are instance-attribute
  methods, a different mechanism. No-third-hook trigger unfired.
- Optimizer-to-types singularity re-check: exactly one `from ..types` import
  under `optimizer/` (walker:1464, in-function inside `_has_custom_id_resolver`
  :1448, importing `types.definition`). "Single sanctioned exception"
  byte-true. (Total-site figure: see E1; singularity unaffected.)

### Rejections R1-R4 — AGREE

Each carries its contract difference + reconsideration trigger, with durable
homes recorded (spec-010 step 11 + delta + leaf docstring; each leaf
docstring; leaf docstring + walker comment; this finding + the
relay/permissions rationale comments, both verified present). R4 is fresh with
no prior verdict — confirmed the relay file item is undispatched per the plan,
and the lint-mechanics difference is real (plain imports F401-clean under
`__init__.py` + `__all__` per the green `ruff check`; regular modules need the
redundant alias at relay HEAD:41 / permissions HEAD:135). Triggers are genuine
reconsideration conditions. (R4 line-ref qualifier: see E4.)

### D1 — ENDORSE as filed

Minor HEAD defect, owner this file, stale-by-refactor provenance — every byte
re-verified: accurate at birth (`f83bb71b` leaf sentence + `relations.py`:24
`RelationKind` + `resolvers.py`:46 `relation_kind` imports all present);
`d2e80523` dropped the resolvers import; `2bcd50bd` dropped the relations
import; `e1ba094e` removed `snake_case` from the same parenthetical but left
the two dead names (diff matches the trace record). HEAD census reproduced:
`RelationKind` occurs in `types/` only in the leaf docstring; `relation_kind`
has zero importers (only the `is_many_side_relation_kind` import/call
substring, one docstring mention, `field_meta.relation_kind` reads); both
names exist in `utils/relations.py` but are unconsumed here; live consumption
is `instance_accessor` + `is_many_side_relation_kind` (both import lines
HEAD-verified). Contract: docstring-claims-imports — every other paragraph
claim verifies (optimizer categories 14/14 import lines, walker exception,
seven-module census), so the paragraph reads as a verified manifest and a
reader extending `..utils` consumption trusts a 2/3-dead list. This is the
DRY.md "docstring contradicting its body" defect class and the direct sibling
of the endorsed testing/relay D1 (stale census comments): feasible project
shape under supported public API, clean-line HEAD defect for normal closeout
homing, blocks nothing. Fix shape (docstring-only) correctly not applied.

### Near-misses N1-N3 + O1 — AGREE

- N1 cleared: 'canonical' = canonical subpackage spelling vs `types.base`,
  coexisting with root-dominant usage per para 2's own framing. Census
  substance verified (oracle sole absolute-leaf consumer; root:52 +
  list_field:89 relative; inspect:63 dotted-submodule). See E2 for a count
  imprecision that strengthens, not weakens, the clearance.
- N2 cleared: `origin_has_custom_id_resolver` resolves 3x in walker
  (docstring:1453, import:1464, call:1466); every operative claim verifies
  (in-function, imports `types.definition`, dodges the init cycle, sole
  exception). Imprecise possessive, true substance — not a contradiction.
- N3 cleared: both orders independently conventional and gate-clean.
- O1 non-defect AGREE: no exact-set pin is correct per the standing
  testing-leaf oracle-economy precedent — zero star-import code consumers
  (reproduced) and the identity oracle pins all three members by literal name.

### Freshness — AGREE (40 rows mechanically checked)

39/40 `(worktree, HEAD)` pins match digit-for-digit. The single mismatch is
the plan file's worktree pin (`3c454a40` claimed, `b2454557` current): that is
Worker-0's own concurrent record appends (the dispatch + submission lines in
the window diff below), and the HEAD pin `ba411b27` matches. The plan is an
index-conventions input, not a load-bearing contract source — no finding
reopens. D1's four commit pins are immutable and all resolve. Searched
populations are replayable as stated; excluded modules (13 sibling leaves +
13 non-walker optimizer modules) are fingerprinted or closed by the
package-wide grep with walker the sole hit.

### Pending execution — AGREE (None correct)

Every conclusion is `static-reviewed` over import composition, census counts,
and prose-vs-imports; nothing ordering-, transactional-, or async-sensitive
was judged. No `proof:` owed, no `gate:` witness needed (zero-edit; identity
oracle + RUF022 already execute in CI). Sharded/PG inapplicable by
construction endorsed: three re-exports + manifest + prose reach no database,
alias, or dialect decision.

### Index rows — AGREE (6/6)

All six `## Index rows for Worker-0` texts match their findings (rule names,
owners, files covered, holding item `File types/__init__.py`, statuses:
2 file-local + 4 rejected). No Families items — correct, none named.

### Window attribution — all concurrent/out-of-scope, left alone

`git diff ITEM_BASELINE --stat` names exactly 3 tracked paths plus the
untracked artifact at the dispatched 4-underscore path (the item's only
output); HEAD unmoved at `0c0537e2`:

- `docs/dry/dry-0_0_15.md`: one hunk, Worker-0's own run-7 record lines
  (testing/relay outcome fixup + this item's dispatch/submission/W2-dispatch
  records). Mine/concurrent, out of scope.
- `docs/review/review-0_0_15.md`: review-flow concurrent work (apps.py
  verified record, conf.py reviewing, Owned-changes row for `tests/test_apps.py`,
  Drift line noting this very artifact). Out of scope.
- `tests/test_apps.py`: two hunks, review-flow apps.py Comments findings
  (dispatch-test masking paragraph + `spec-021` Decision anchors), matching
  the review ledger row; target untouched. Out of scope.

No `docs/dry/temp-tests/` scope was created for this item (verified absent);
no scratch to remove. No `.py` touched, so no ruff fix/format pass was owed.

### AGENTS.md prose check — PASS

Artifact uses reference-style cross-file links with all 10 canonical group
headers present and zero inline `[text](path)` links; citations use
`path::Symbol` with raw `:NN` confined to this per-cycle `dry-*.md` scratchpad
artifact where allowed; no `feedback` mentions; no tests touched (tier rules
untriggered); no CHANGELOG touch; plan untouched by Worker-2.

### Immaterial record notes (verdicts stand, no revision owed)

- E1: the `from ..types` total "15 sites / 14 outside optimizer/" reproduces
  as 14 / 13 at both HEAD and worktree (reproducible `git grep`; the 15th is
  plausibly the `docs/dry/dry-0_0_11.md` prose mention caught by a repo-wide
  grep). Every load-bearing claim built on it (exactly one under optimizer/,
  in-function, singularity; F2's legitimate-importer point) is byte-true.
- E2: N1's "one intra-package dotted-submodule importer" undercounts —
  `testing/relay.py`:41-45 also imports `DjangoType` from `types.base`. The
  clearance stands (a second blessed-reachable importer strengthens it).
- E3: `## Judgment` says "Five rules traced" but records two file-local +
  four rejected = six. Arithmetic slip; findings and index rows unambiguous.
- E4: R4 cites relay:44 / permissions:136 without a revision qualifier —
  those are worktree lines (HEAD:41/:135); both sites verified at both
  revisions.
- E5: "38-name `__all__`" for the root — the tuple holds 39 strings (38
  imports + the `__version__` literal); consistent with the standing verified
  root row's import-admitted convention. No correction needed.

### Defects (Worker-2)

None. D1 endorsed as filed; no new defect found.

### Verdict

`Status: verified` (zero-edit; 5/5 + 4/4 + 3/3 homed; 2 file-local, 4
rejections with 3 convergences on fresh evidence + 1 fresh; D1 minor HEAD
defect endorsed for normal closeout homing; no pending execution).
