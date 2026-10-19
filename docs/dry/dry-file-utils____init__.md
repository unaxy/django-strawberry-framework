# DRY review: `utils/__init__.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

The target is a 56-line eager re-export leaf: module docstring
(structure framing + a PINNED-surface paragraph + nine architecture
bullets, :1-42), three `from .<submodule> import <names>` re-exports
(:44-46), one seven-member `__all__` tuple (:48-56). It owns no
definition with behavior; it owns the subpackage's public surface
membership (which seven names answer at the dotted
`django_strawberry_framework.utils` path, and the withholding of
everything else) plus the submodule-ownership prose (which submodules
are architecturally notable, the upstream-convention framing, the
submodule-direct layering posture).

Sites found, by role:

- Definitions composed by name: [relations.py][utils-relations]
  `RelationKind` (TypeAlias, HEAD:42), `relation_kind` (HEAD:160),
  `is_many_side_relation_kind` (HEAD:235); [strings.py][utils-strings]
  `snake_case` (HEAD:96), `pascal_case` (HEAD:138);
  [typing.py][utils-typing] `unwrap_graphql_type` (HEAD:165),
  `unwrap_return_type` (HEAD:247). All seven def-verified at HEAD.
- Consumers of the leaf surface: NONE beyond the oracle. The
  repo-wide HEAD census finds zero `from ...utils import <name>`
  lines (every leaf-path import is a submodule-attribute alias:
  `import <submodule> as ..._module`), zero `utils.<name>`
  attribute reads outside the oracle, zero `import *` sites, zero
  `getattr(utils`, zero intra-package relative leaf-path imports.
  The sole reader of the short spelling is the oracle below. The
  nearest real consumer, [types/converters.py][types-converters]:79,
  takes `pascal_case` via the dotted-submodule path
  (`from ..utils.strings import pascal_case`).
- Oracle: [test_init.py][test-init] (CLEAN `8d340656`), three tests —
  exact-set pin (`__all__` tuple equality, :20-29), identity (seven
  `is` asserts, :34-40), reachability (`hasattr` loop, :44-46).
  Unlike the types/testing leaves this leaf's set IS pinned exactly,
  so no oracle-economy observation is owed.
- Withheld-but-reachable dotted paths: everything else in the 21
  HEAD siblings (`git ls-tree HEAD`, 22 entries incl. the leaf),
  incl. the docstring-named `is_async_callable` (HEAD:116),
  `schema_config_from_info` (HEAD:63), `session_store_class`
  ([sessions.py][utils-sessions] HEAD:202), `SyncMisuseError`
  ([querysets.py][utils-querysets] HEAD:121). Dotted reachability is
  exercised by production imports ([auth/sessions.py][auth-sessions]
  HEAD:61, [auth/mutations.py][auth-mutations] HEAD:74,
  [consumers.py][consumers] HEAD:394/:1608,
  [middleware/debug_toolbar.py][toolbar] HEAD:64).
- Root posture: ABSENT — zero `utils` mentions in
  [__init__.py][pkg-root] (CLEAN) and zero in
  `tests/base/test_init.py`. The root owns nothing from `utils/`.
- Sibling-flavor sweep (axis 1): all 13 sibling `__init__.py` leaves
  re-read at CLEAN bytes — [auth][auth-init], [extensions][ext-init],
  [filters][filters-init], [forms][forms-init],
  [management][mgmt-init], [management/commands][cmds-init],
  [middleware][mw-init], [mutations][mutations-init],
  [optimizer][optimizer-init], [orders][orders-init],
  [rest_framework][rest-init], [testing][testing-init],
  [types][types-init]. Five distinct postures, disjoint memberships
  and containers, no shared driver (see R2). The one cross-leaf
  citation touching this file is
  [extensions][ext-init]:21-22 ("the `utils/__init__.py` /
  `testing/__init__.py` shape") — one-directional explanatory prose,
  and the citer implements a LIST `__all__` where this leaf holds a
  tuple (near-miss N1, zero definitions).
- Module-hook census (HEAD `git grep`, package-wide): exactly two
  `def __getattr__` ([__init__.py][pkg-root]:98,
  `routers.py`:533) — the standing no-third-hook trigger re-checked
  unfired; the target defines no callable at all.
- Contract sources: the leaf docstring itself (the PINNED paragraph
  states the membership rule; D1 filed on three of its claims) and
  the upstream checkouts for the structure sentence
  (`graphene_django/utils/` carries `str_converters`/`testing`/
  `utils`; `strawberry_django/utils/` carries seven submodules —
  the focused-submodules claim verifies).
- Projections: [TREE.md][tree] renders the docstring first line
  twice (:294, :428, byte-identical at HEAD); the oracle's module
  docstring echoes "short spelling" as its rationale.

No consolidation inside this file item. Two file-local rules, two
rejections (both CONVERGE on verified rows with fresh trigger
checks), one minor HEAD defect (D1, PINNED-paragraph overclaims,
unfixed), zero new families, zero adoptions.

## Verification

### Enumeration

Instrument: `ast.parse` over the target file, every node in
`ast.Module.body` in order (5 statements), plus every bound name (8)
and every `__all__` member (7). Digest: `Expr(docstring :1-42)`,
three `ImportFrom` (:44-46), one `Assign(__all__ :48-56)`.

| # | Statement (target line) | Binds | Home |
|---|---|---|---|
| S0a | docstring first line + upstream framing (:1-5) | — (prose) | FL2 `utils-submodule-ownership-prose` |
| S0b | docstring PINNED paragraph (:7-13) | — (prose) | FL1 `utils-leaf-manifest` (D1 filed) |
| S0c | docstring architecture bullets (:15-41) | — (prose) | FL2 |
| S1 | `from .relations import RelationKind, is_many_side_relation_kind, relation_kind` (:44) | 3 names | FL1 |
| S2 | `from .strings import pascal_case, snake_case` (:45) | 2 names | FL1 |
| S3 | `from .typing import unwrap_graphql_type, unwrap_return_type` (:46) | 2 names | FL1 |
| S4 | `__all__` 7-tuple (:48-56) | `__all__` (7 members) | FL1 |

Coverage: 5/5 statements, 8/8 bound names, 7/7 `__all__`
members homed. Cross-file candidates raised by the challenges route
to rejections R1–R2 (recorded at their rows, all in this artifact —
no holding family owed since every count came back 1). No member is
unassigned; no consolidation lives here.

### Matrix

1. **Cross-flavor policy mirroring — SEARCHED.** All 13 sibling
   leaves re-read in full (all CLEAN; hashes under Freshness).
   Posture census, fresh: eager re-export + plain `__all__` tuple
   (utils/, types/, auth/, optimizer/); eager + typed `__all__`
   tuple (forms/, mutations/, filters/ + orders/ with Decision-11
   helper + ledger + clear row); eager + `__all__` LIST
   (extensions/, testing/); bare marker, no re-export (management/,
   management/commands/, middleware/ with documented no-re-export
   posture); guard-only, no manifest (rest_framework/). Root-mirror
   posture also varies: via-leaf (types/, forms/, mutations/),
   partial/direct-submodule (extensions/, optimizer/),
   absent-but-importable (auth/ structural opt-in, filters/,
   orders/, testing/, utils/), lazy-`__getattr__` only
   (rest_framework/). Nearest shapes to this leaf: types/ and auth/
   (eager plain-tuple, small fixed membership) — still disjoint
   memberships, and auth/ carries a structural-opt-in contract this
   leaf has no analogue of. No shared membership, no shared
   container, no shared driver → R1 (root) + R2 (siblings). The
   extensions shape citation (:21-22) vs this leaf's tuple → N1.
   The types-R4 plain-vs-`as`-alias pair has no second site here:
   zero redundant-alias re-exports of any of the seven names
   repo-wide (HEAD census) → searched-negative, no row.
2. **Sync/async twins — INAPPLICABLE.** The leaf defines no callable
   and no await boundary; the async contracts of the composed names
   (e.g. `is_async_callable`'s predicate) live at their owner
   definitions. The standing `one-sync-boundary` trigger has no
   surface here.
3. **Derived rather than repeated knowledge — SEARCHED.** Three
   pairings, all same-file idiom: (a) `__all__` members repeat the
   seven import names — the standard manifest pairing, order
   gate-held by RUF022 (selected wholesale at
   [pyproject.toml][pyproject]:161 at HEAD, zero `RUF022` strings
   repo-wide; `ruff check` + `ruff format --check` pass on the
   target read-only) and membership failure-loud via the exact-set
   oracle; (b) the PINNED paragraph's "the seven" counts the same
   seven — same-file projection, moves in the same edit (D1(a)
   filed on its rationale clause, not its count); (c) the bullets
   name owner-submodule symbols (`session_store_class`, the
   `iter_*` trio, …) — same-tree projections of those definitions,
   each def-verified at HEAD. Imports are module-sorted
   (`relations` < `strings` < `typing`); within-line names and
   `__all__` are ASCII-sorted — all gate-clean.
4. **Inverse / round-trip pairs — INAPPLICABLE.** No encode/decode,
   pack/unpack, or build/parse grammar in a re-export leaf; the
   generated-input lifecycle and queryset-visibility contracts
   merely named in the bullets are owned by [inputs.py][utils-inputs]
   and [querysets.py][utils-querysets], outside this file's surface.
5. **Contracts restated in another medium — SEARCHED.** Media census
   with roles: owner submodules = definitions (composed by name
   per principle 6); [test_init.py][test-init] = independent oracle
   (exact-set + identity + reachability; a widened/narrowed/rebound
   leaf fails it, never the reverse); [TREE.md][tree]:294/:428 =
   projection (first line ×2, re-rendered by `build_tree_md.py`);
   leaf docstring S0b = the FL1 statement (D1 filed), S0a/S0c =
   the FL2 statement + projections of owner defs. No root medium
   exists (root-absent → R1). Every medium a change forces to move
   is named in the challenges; only the leaf counts.
6. **Enforcement by omission — SEARCHED.** Withheld population
   enumerated: 21 HEAD siblings minus the 7 exported names, incl.
   the docstring-named `is_async_callable`,
   `schema_config_from_info`, `session_store_class`,
   `SyncMisuseError` — each def-verified at HEAD and dotted-
   reachable through production importers (see System trace).
   Negative sweeps: zero leaf-path imports of any withheld name
   (every `from ...utils import ...` line is a submodule-attribute
   alias), zero `from ...utils import *` sites, zero
   `getattr(utils`, zero intra-package relative leaf imports.
   `__all__` admits exactly the seven imports (no leakage, no
   omission). Withholding is enforced by Python attribute
   semantics plus `__all__` for star imports — no second
   definition, no enforcement gap, no defect.

### Challenges

Counts are AUTHORITATIVE definitions only; consumers, oracles, and
projections that also move are listed, never counted. All proofs
`static-reviewed` (import composition + census counts +
prose-vs-bytes, inspection decides; see Pending execution for why
no execution was owed).

FL1 `utils-leaf-manifest` (S0b, S1–S4):

- C1 "Add an eighth leaf name." Definitions forced: 1 — the leaf
  (import line + `__all__` member + 'the seven' count move as one
  edit). Moves-but-not-counted: the exact-set oracle FAILS (proving
  oracle independence — it pins the set, never reads it);
  TREE.md unchanged (first line only). Count: 1.
- C2 "Drop one of the seven." Definitions: 1 (the leaf). The
  identity oracle breaks (its `utils.<name>` read fails) — again
  proving oracle independence; zero consumers move because zero
  exist. Count: 1.
- C3 "Reorder `__all__` non-ASCIIbetically." Definitions: 1 (the
  leaf) and the RUF022 gate fires. Count: 1.
- C4 "Rebind rather than forward (the leaf defines its own
  `snake_case`)." Definitions permitted: 0 new — the identity
  oracle rejects the second definition (`is` fails). The oracle is
  the structural backstop for single-siting. Count: 1 (unchanged).
- C5 "Withhold one name to dotted-only." Definitions: 1 (the
  leaf). The oracle breaks by design (set pin + identity); the
  dotted path keeps working (production importers already use it).
  Count: 1.

FL2 `utils-submodule-ownership-prose` (S0a, S0c):

- C6 "A 22nd submodule lands." Definitions: 1 — this bullet list
  (the actual posture is selective: 9 of 21 named). Note D1(b) IS
  the standing overclaim that the list covers 'each submodule'.
  Count: 1.
- C7 "`session_store_class` is renamed at its owner."
  Definitions: 1 (the owner def moves; the bullet + sessions
  paragraph update as projections, listed not counted). Count: 1.
- C8 "A production module imports the short spelling."
  Definitions: 0 move — the 'keeps importing submodules directly'
  sentence goes stale. It is statement-only posture (no gate);
  the census (zero such imports at HEAD) is its current truth.
  Count: 1 (the statement, unchanged in force).
- C9 "An upstream flattens `utils/` to one module."
  Definitions: 1 (the convention sentence). Count: 1.

Rejections (contract difference + reconsideration trigger; full
records under Findings):

- R1 `utils-leaf-vs-root-manifest`: posit "root re-exports the
  seven" → root moves (1), leaf moves 0. Posit "leaf drops the
  seven" → leaf moves (1), root moves 0 (it owns nothing here).
  Difference: membership owned per level; this level holds 7,
  the root holds 0 (structural absence, the auth posture).
  CONVERGE with the verified orders/testing/rest-framework/types
  leaf-vs-root direction — trigger re-checked unfired (no shared
  driver; not even a one-sided mirror exists to pair).
- R2 `utils-leaf-vs-sibling-manifest`: posit "every leaf gains a
  helper+ledger" → 14 independent edits (guard/marker/helper/eager
  postures; tuple/typed-tuple/list/no-container). Count 14 =
  independence. CONVERGE with verified
  `rest-framework-leaf-vs-sibling-manifest` (via types-R2) — the
  dispatch-mandated direction — trigger (shared manifest driver
  or coupled membership) unfired on the fresh 14-leaf census.

Considered, no row (near-misses, cleared with evidence):

- N1 extensions shape citation ([extensions][ext-init]:21-22
  "the `utils/__init__.py` / `testing/__init__.py` shape"):
  cleared — one-directional explanatory citation, zero definitions
  on this side; and the citer disproves a shared container (LIST
  `__all__` vs this leaf's tuple). Strengthens R2.
- N2 types "leaf helpers" phrasing ([types][types-init] para 3
  "consumes leaf helpers from `..utils`"): cleared — loose
  phrasing in ANOTHER file's docstring, and the live consumption
  ([types-converters][types-converters]:79) uses the dotted-
  submodule path, which is exactly this leaf's stated layering
  posture. The dead names in that parenthetical are owned by the
  endorsed types D1, not this item.
- N3 oracle docstring "helpers those names implement are live in
  `test_library_api.py`": cleared — true transitively (the helpers
  execute via package code paths during those live tests, e.g.
  `pascal_case` in enum building); the oracle's own words already
  concede the short spelling itself is not a live surface ("That
  identity is not a GraphQL field"). Test-doc prose, out of scope,
  not false.

## Findings

### F1 `utils-leaf-manifest` — file-local

- **Contract + variation.** The leaf admits exactly seven public
  names — `RelationKind`, `relation_kind`,
  `is_many_side_relation_kind` (relations), `snake_case`,
  `pascal_case` (strings), `unwrap_graphql_type`,
  `unwrap_return_type` (typing) — in an ASCII-sorted `__all__`
  tuple; everything else in the 21 siblings stays
  dotted-reachable but unexported. Varies on: membership (which
  names), order (gate-held), withholding boundary (omission).
- **Sites + roles.** Definition: this leaf (S0b, S1–S4).
  Composed definitions (owned elsewhere, not counted):
  [relations.py][utils-relations]`::RelationKind` /
  `::relation_kind` / `::is_many_side_relation_kind`,
  [strings.py][utils-strings]`::snake_case` / `::pascal_case`,
  [typing.py][utils-typing]`::unwrap_graphql_type` /
  `::unwrap_return_type`. Consumers: none (census-closed; the
  sole short-spelling reader is the oracle). Oracle:
  [test_init.py][test-init] (exact-set + identity +
  reachability). Projections: TREE.md first line ×2, the S0b
  count, the oracle docstring's rationale echo.
- **Challenges.** C1–C5, each count 1 (C4: 1 unchanged — the
  oracle rejects the second definition).
- **Owner + lifetime.** Owner is this leaf: narrowest surface
  every legitimate consumer can depend on without reaching into
  submodules (today: zero consumers, one oracle — the surface is
  held for the short spelling, not driven by demand; D1(a)
  records that the rationale sentence overstates this). No
  stored derivation (pure re-export; "not cached").
- **Migration.** None — zero-edit; nothing moves.
- **Distinct behavior.** Submodule-attribute namespace use
  (`from ...utils import <submodule> as ...`, 13 test lines) is
  Python semantics, unaffected by the manifest; the manifest
  governs the seven names only.
- **Behavioral proof.** `static-reviewed`: membership = import
  lines + `__all__` (wrong result rejected: an eighth exported
  name or a missing member — visible in the 5-statement body);
  forwarding = the seven `is` asserts executing in CI (existing
  oracle, not authored here); withholding = negative sweeps
  (zero withheld-name leaf imports, zero star sites, zero
  `getattr`). No execution owed (see Pending execution).
- **Structural gate.** Pre-existing, no new gate: RUF022
  (`__all__` sort; selected wholesale at HEAD, never ignored;
  `ruff check` green on the target) + the exact-set oracle
  (fails by tuple inequality if the leaf widens/narrows — failure
  mode read off the test's own assert, no mutation run needed for
  a cited, unmodified gate). Negative control: N/A — no new gate
  introduced; a hand copy of the seven import lines would pass
  the identity oracle (it pins identity, not single-siting),
  which is why the finding stays file-local rather than claiming
  a consolidation.
- **Coupling.** None.
- **Freshness.** Full input table (worktree `wt`, HEAD `hd` at
  `0c0537e2`; every load-bearing claim re-verified at HEAD bytes):

| Input | wt | hd | State |
|---|---|---|---|
| `utils/__init__.py` (target) | `1a4c2ec8` | `1a4c2ec8` | CLEAN |
| `utils/relations.py` | `05ff55b0` | `8dbc3fe6` | DIRTY, :25/:42/:160/:235 HEAD-verified |
| `utils/strings.py` | `5a4f4811` | `991f7dad` | DIRTY, :96/:138 HEAD-verified |
| `utils/typing.py` | `a672cd6b` | `de6309f6` | DIRTY, :63/:116/:165/:247 HEAD-verified |
| `utils/connections.py` | `efcf749a` | `f549389e` | DIRTY, module head HEAD-verified |
| `utils/sessions.py` | `21041723` | `f0d9297c` | DIRTY, :202 HEAD-verified |
| `utils/inputs.py` | `b5af8255` | `ee31d360` | DIRTY, first line HEAD-verified |
| `utils/permissions.py` | `1c9cfd39` | `9889d6fe` | DIRTY, first line HEAD-verified |
| `utils/input_values.py` | `18992b79` | `f2566609` | DIRTY, :77/:137/:321 HEAD-verified |
| `utils/querysets.py` | `8fc556d5` | `3616927d` | DIRTY, :121/:268/:283/:4103 HEAD-verified |
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
| `types/__init__.py` | `1bf69028` | `1bf69028` | CLEAN |
| `__init__.py` (root) | `0ef72601` | `0ef72601` | CLEAN |
| `tests/utils/test_init.py` | `8d340656` | `8d340656` | CLEAN |
| `types/converters.py` | `f6cadb08` | `058f1081` | DIRTY, :79 HEAD-verified |
| `auth/sessions.py` | `865d6e70` | `fad7feb8` | DIRTY, :61 HEAD-verified |
| `auth/mutations.py` | `84183c89` | `d1a59c44` | DIRTY, :74 HEAD-verified |
| `consumers.py` | `0791c04a` | `936210e2` | DIRTY, :394/:1608 HEAD-verified |
| `middleware/debug_toolbar.py` | `ffda621e` | `5360149b` | DIRTY, :64 HEAD-verified |
| `docs/TREE.md` | `769c2743` | `5d562733` | DIRTY, :294/:428 HEAD-verified |
| `pyproject.toml` (RUF select) | `964c1339` | `9be86493` | DIRTY, :161 + zero RUF022 HEAD-verified |
| `docs/dry/dry-0_0_15.md` (index conventions) | (concurrent) | (concurrent) | DIRTY (Worker-0 writes; conventions only) |

Searched populations (replayable HEAD `git grep` censuses): every
`from ...utils import ...` line repo-wide (13, all submodule-attribute
aliases in tests); every `utils.<name>` attribute read (oracle lines
only); `utils import *` (= 0); `getattr(utils` (= 0); intra-package
relative leaf imports (= 0); `^def __getattr__` package-wide (= 2);
`__all__`-less `utils/` submodules (= 5:
[connections][utils-connections], [input_values][utils-input_values],
[querysets][utils-querysets], `write_transaction`, `write_values`).
Modules EXCLUDED on body strength: the 13 sibling leaves (postures
read, membership disjoint — fingerprints above); the 12
bullet-unnamed `utils/` siblings (no leaf-path surface; population
closed by the `ls-tree` 22-entry census).
Upstream checkouts read for the structure sentence:
`graphene_django/utils/` (3 submodules + tests) and
`strawberry_django/utils/` (7 submodules) — versions per [TREE.md][tree]
provenance. D1 birth pins `a8f31a2d` / `d4c07d7d` are immutable
commits (short ids resolve).

### F2 `utils-submodule-ownership-prose` — file-local

- **Contract + variation.** Docstring S0a states the structure
  framing (focused submodules per concern, the both-upstreams
  convention — verified); S0c names what nine architecturally
  notable submodules own (relations / strings / typing /
  connections / sessions / inputs+permissions / input_values /
  querysets — every named symbol def-verified at HEAD, every
  ownership gloss confirmed against its module head); S0b's tail
  sentence states the layering posture (production code imports
  submodules directly — zero counterexamples at HEAD). Varies on:
  notable-submodule selection, per-bullet gloss, layering-posture
  wording, upstream-convention claim.
- **Sites + roles.** Definition (statement): this docstring — the
  only place the selection + framing + posture are stated as a
  rule (HEAD `git grep` for the PINNED/layering sentences: this
  file + the oracle docstring's rationale echo, listed not
  counted). Projections of owner defs: the per-bullet symbol
  names (each moves with its owner per C7). Bilateral prose:
  none — N1/N2 are unilateral citations in other files' words.
- **Challenges.** C6–C9, each count 1 (C8: the statement stands
  alone, ungated).
- **Owner + lifetime.** Owner is this leaf: the subpackage
  boundary statement lives with the subpackage surface. No
  stored derivation.
- **Migration.** None — zero-edit (D1 unfixed per item rules).
- **Distinct behavior.** The selection is deliberately partial
  (9 of 21) — the accurate posture the pre-`a8f31a2d` "Includes,
  among others:" framing stated; D1(b) records that the current
  'each submodule' sentence overclaims it.
- **Behavioral proof.** `static-reviewed`: every operative claim
  re-derived at HEAD bytes (18 symbol defs, 4 production
  dotted-path importers, both upstream dir listings, the
  zero-counterexample layering census, TREE.md byte-identity).
  Wrong result rejected: a bullet naming a dead symbol or a
  production short-spelling import — the sweeps came back 18/18
  live and 0 respectively.
- **Structural gate.** None pre-exists; none introduced (a prose-
  accuracy gate is out of scope for a file item — the
  folder/project items own that question). Prose posture findings
  carry no negative control.
- **Coupling.** None (D1 homing is editorial, blocks nothing).
- **Freshness.** As F1 (same table; D1 additionally pins the
  immutable `a8f31a2d`/`d4c07d7d` bytes).

### R1 `utils-leaf-vs-root-manifest` — rejected

Difference: membership owned per level, and the root level holds
nothing — zero `utils` mentions in [__init__.py][pkg-root] at HEAD
(structural absence, the auth posture, not an oversight: the leaf
exists for the short spelling while the root never took it up).
Either side moves without forcing the other (challenges under R1
above). Trigger: a shared manifest driver or a standing
must-mirror rule — re-checked unfired (no one-sided mirror even
exists to pair). CONVERGE with the verified
orders/testing/rest-framework/types leaf-vs-root direction on fresh
evidence. Durable home: the leaf docstring (S0b) + this finding.
Freshness: as F1.

### R2 `utils-leaf-vs-sibling-manifest` — rejected

Difference: 14 leaves, five postures (eager plain-tuple / eager
typed-tuple / eager list / bare marker / guard-only), disjoint
memberships, disjoint containers — no shared variation axis for a
driver to own. A cross-leaf change costs 14 independent edits =
independence, not duplication. The nearest shapes (types/, auth/)
share only the container, never a member or a helper. Trigger: a
shared manifest driver or coupled membership — unfired on the
fresh full-leaf census (all 13 siblings re-read at CLEAN bytes,
hashes digit-identical to the types census). CONVERGE with
verified `rest-framework-leaf-vs-sibling-manifest` (via types-R2)
on fresh evidence — the dispatch-mandated convergence direction,
confirmed, not distinguished. Durable home: each leaf docstring
(this leaf's S0b/S0c). Freshness: as F1.

## Defects

### D1 PINNED paragraph overclaims its rationale, coverage, and manifest pointer (minor, HEAD, unfixed)

- **What.** Three limbs, all in S0b (target :7-13, CLEAN lines),
  all verifiably false at HEAD:
  - (a) "the seven that consumer-facing code and tests already
    reach for by the short spelling" — zero short-spelling
    consumers exist. The closed HEAD census (every
    `from ...utils import ...` spelling, every `utils.<name>`
    read, every relative leaf import, `import *`, `getattr`)
    leaves exactly one reader: the oracle itself
    ([test_init.py][test-init]:34-40). The nearest real consumer
    ([types-converters][types-converters]:79) uses the
    dotted-submodule path.
  - (b) "the architecture notes below name what each submodule
    OWNS" — 9 of 21 HEAD siblings are named. Unnamed:
    `canonical`, `context`, `converters`, `directives`, `errors`,
    `execution_mode`, `imports`, `operation_lease`, `policies`,
    `private_state`, `write_transaction`, `write_values`.
  - (c) "for a submodule's full public surface you read its own
    `__all__`" — 5 of the 21 submodules have no `__all__` at all
    ([connections][utils-connections],
    [input_values][utils-input_values],
    [querysets][utils-querysets], `write_transaction`,
    `write_values`), three of them among the named nine.
- **Provenance (inaccurate at birth, not stale-by-growth).**
  `d4c07d7d` framed the list accurately ("Includes, among
  others:"). `a8f31a2d` introduced the PINNED paragraph with all
  three overclaims in one edit: 18 submodules existed then (9
  named), no `__all__`-less check was made, and the short-spelling
  census at that commit already shows only the oracle.
- **Contract.** Docstring-claims-tree: the paragraph reads as a
  verified manifest (the S0c bullets it introduces are 18/18
  accurate, the layering sentence has zero counterexamples), so a
  reader trusts a rationale with no consumers, a coverage claim
  missing 12 modules, and a manifest pointer dangling for 5. This
  is the DRY.md "docstring contradicting its body" defect class
  and the direct sibling of the endorsed types D1 (stale
  parenthetical): feasible project shape under supported public
  API, clean-line HEAD defect for normal closeout homing, blocks
  nothing.
- **Fix shape (not applied).** One docstring edit, no behavior
  change: restore a selective framing ("the notes below name the
  architecturally notable submodules …"), soften the rationale to
  the held-for-convenience truth (or cite the oracle as the
  pinning consumer), and qualify the `__all__` pointer ("where
  the submodule defines one").
- **Owner.** File `utils/__init__.py` (the docstring). Routes to
  normal closeout homing (CLEAN-line HEAD defect; blocks nothing).

No other defects. Near-misses N1–N3 are cleared under Challenges
and need no homing.

## Pending execution

None. No `proof:` entry: every conclusion is `static-reviewed`
(import composition, census counts, prose-vs-bytes — inspection
decides; nothing ordering-, transactional-, or async-sensitive was
judged). No `gate:` entry: no regression witness was needed
(zero-edit; the cited exact-set oracle and RUF022 already execute
in CI). Sharded and PG cells are inapplicable by construction: the
leaf reaches no database, alias, or dialect decision (three
re-exports + manifest + prose). No workspace run was needed; none
was made.

## Judgment

Zero-edit file item. Four rules traced: two file-local with proving
challenges (F1 manifest + withholding, C1–C5; F2 ownership prose,
C6–C9), two rejected with contract differences + triggers (R1
leaf-vs-root, R2 leaf-vs-sibling; both CONVERGE on verified rows
with fresh trigger checks, R2 on the dispatch-mandated direction).
Enumeration covers 5/5 statements, 8/8 bound names, 7/7 `__all__`
members. One minor HEAD defect filed (D1, three-limb
PINNED-paragraph overclaim, unfixed); three near-misses cleared
with evidence. No families named, no adoptions, no pending
execution, no production edits.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs `ITEM_BASELINE=36e6042f62af3b62ed537fb9bd1b6f212ffca94d`:
`git status --short -- django_strawberry_framework/utils/__init__.py`
is empty and the working blob `1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee`
equals `HEAD:django_strawberry_framework/utils/__init__.py` at HEAD
`0c0537e2` — target CLEAN, so no hunk attribution was owed. The
artifact itself is a new untracked file at the exact dispatched path
`docs/dry/dry-file-utils____init__.md`, the item's only output. The
`## Owned changes` ledger gains no row from this item (verified: no
ledger hunk names this file). Concurrent dirt (hunt edits across
`django_strawberry_framework/`, test churn, `docs/dry/dry-0_0_15.md`)
left untouched; every load-bearing claim rests on HEAD bytes with
both fingerprints recorded. `uv run ruff check` + `uv run ruff
format --check` run read-only on the target (both pass; no `--fix`,
no `.py` touched). No shared-tree pytest run (AGENTS.md: only when
asked; inspection + the pre-existing exact-set oracle suffice). No
workspace runs (nothing source-mutating was needed). No
`docs/dry/temp-tests/` scratch created. HEAD unmoved at `0c0537e2`
(first byte-check to final fingerprint). No commit.

Worker-0 instructions: (a) tick the plan item `File utils/__init__.py`
once Worker 2 agrees; (b) add the four `## Responsibility index` rows
under `## Index rows for Worker-0` verbatim (holding item
`File utils/__init__.py`); (c) add the `## Families` items under
`## Families` (none). No commit.

## Index rows for Worker-0

| `utils-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/utils/__init__.py`) | `django_strawberry_framework/utils/__init__.py` (+3 owner modules) | File `utils/__init__.py` | file-local |
| `utils-submodule-ownership-prose` | `django_strawberry_framework/utils/__init__.py` (S0a structure framing + S0c architecture bullets + S0b submodule-direct layering posture; D1 filed on the PINNED paragraph) | `django_strawberry_framework/utils/__init__.py` | File `utils/__init__.py` | file-local |
| `utils-leaf-vs-root-manifest` | `django_strawberry_framework/utils/__init__.py` (rejection recorded here; CONVERGE with verified orders/testing/rest-framework/types leaf-vs-root direction on fresh evidence — root-absent, trigger unfired) | `django_strawberry_framework/utils/__init__.py`, `django_strawberry_framework/__init__.py` | File `utils/__init__.py` | rejected |
| `utils-leaf-vs-sibling-manifest` | `django_strawberry_framework/utils/__init__.py` (rejection recorded here; CONVERGE with verified rest-framework/types leaf-vs-sibling-manifest on fresh evidence — 14 leaves, 5 postures, trigger unfired) | `django_strawberry_framework/utils/__init__.py`, `django_strawberry_framework/auth/__init__.py`, `django_strawberry_framework/extensions/__init__.py`, `django_strawberry_framework/filters/__init__.py`, `django_strawberry_framework/forms/__init__.py`, `django_strawberry_framework/management/__init__.py`, `django_strawberry_framework/management/commands/__init__.py`, `django_strawberry_framework/middleware/__init__.py`, `django_strawberry_framework/mutations/__init__.py`, `django_strawberry_framework/optimizer/__init__.py`, `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/rest_framework/__init__.py`, `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/types/__init__.py` | File `utils/__init__.py` | rejected |

## Families

None. No new family named, no adoption into an open family (every
change challenge counted exactly one authoritative definition). The
holding items for the composed definitions are the undispatched file
items `utils/relations.py`, `utils/strings.py`, `utils/typing.py`
(plus the verified file item `utils/querysets.py` for the
`SyncMisuseError` name the bullets project but the leaf withholds).

## Independent verification (Worker-2)

Expectation-first trace (from the bare target at HEAD bytes, before
reconciling the findings): a 56-line eager re-export leaf — docstring
+ three `ImportFrom` + one `__all__` `Assign` = 5 statements; 7
forwarded names + `__all__` = 8 bound names; `__all__` = the same 7,
ASCII-sorted. Expected homes: one manifest rule (file-local,
oracle-pinned identity), one docstring-prose rule (file-local), at
most two rejections (vs root, vs sibling leaves); no family (every
change counts exactly 1: the leaf alone moves). Owner for both
rules: the leaf itself.

Reconciliation: W1's structure matches on every point. Judgments
below were each re-derived mechanically at HEAD `0c0537e2` (target
blob `1a4c2ec8`, worktree-identical, CLEAN; `lazy.py`/`truth.py` in
the worktree are untracked concurrent work, correctly outside the
21-sibling HEAD census).

(a) Enumeration CONFIRM. My own `ast.parse` over HEAD bytes: 5
statements (`Expr` docstring :1-42, three `ImportFrom` :44-46, one
`Assign` :48-56), 8 bound names, 7 `__all__` members with `__all__`
== imported set, ASCII-sorted, modules sorted. 5/5 statements, 8/8
bound names, 7/7 members homed (FL1: S0b+S1–S4; FL2: S0a+S0c). No
member unassigned.

(b) Matrix CONFIRM. Axis 1 reproduced: all 13 sibling leaves
re-fingerprinted CLEAN (hashes digit-identical to W1's table) and
all 14 manifests censused at HEAD bytes — 5 postures as claimed, 53
members across 10 manifests with zero intersections (programmatic
check). Axes 2/4 inapplicability judged sound (no callable, no
grammar in the leaf). Axis 3: `RUF` selected wholesale at
pyproject :161, zero `RUF022` strings repo-wide, `ruff check` +
`ruff format --check` pass read-only on the target. Axis 5: oracle
read in full — exact-set (:21-29), identity (:34-40), reachability
(:45-46), CLEAN `8d340656`; TREE.md :294/:428 byte-identical;
upstream dir listings confirmed (strawberry 7 submodules, graphene
`str_converters`/`testing`/`utils`). Axis 6: withheld population
closed by the 22-entry `ls-tree` census.

(c) Challenges CONFIRM. C1–C9 counts re-derived at 1 (C4/C8: the
oracle/statement stands alone). Every cited HEAD line number
re-verified: relations :42/:160/:235, strings :96/:138, typing
:63/:116/:165/:247, sessions :202, querysets :121, input_values
:77/:137/:321, converters :79, auth/sessions :61, auth/mutations
:74, consumers :394/:1608, toolbar :64. Oracle untouched (CLEAN) —
no oracle rewritten to read from an owner.

(d) R1 CONFIRM (CONVERGE grounded). Root-absence re-proven (`git
grep "utils"` over the root + `tests/base/test_init.py` at HEAD:
zero matches). Contract difference (per-level membership; root
holds 0) and trigger re-checked unfired on fresh evidence.
Convergence grounded on three explicit verified `rejected` plan
rows (orders, testing, types leaf-vs-root). O1 (Worker-2,
observed-not-homed, blocks nothing): no dedicated
`rest-framework-leaf-vs-root` plan row exists; the `rest-framework`
token in the direction phrase is inherited convention from the
verified testing/types rows' own language. The rejection stands on
fresh evidence regardless.

(e) R2 CONFIRM (CONVERGE grounded, dispatch-mandated direction).
14-leaf census reproduced at HEAD bytes: 5 postures, disjoint
containers (tuple / typed-tuple / list / marker / guard), disjoint
memberships (53/53, zero clashes). Trigger (shared driver or
coupled membership) unfired. Convergence grounded on verified
`rest-framework-leaf-vs-sibling-manifest` via types-R2. N1
verified (extensions :21-22 citation real; LIST vs tuple
strengthens the rejection); N2 verified (types :26 parenthetical;
dead names owned by endorsed types D1); N3 verified (`pascal_case`
called at converters :775, transitively live).

(f) D1 — ENDORSE as filed (minor HEAD defect, closeout homing,
blocks nothing). Limb (a) reproduced: 13 `from ...utils import`
lines at HEAD all bind submodule attributes in tests;
`utils.<name>` reads are exactly the 7 oracle lines;
star/`getattr`/relative-leaf imports zero; remaining leaf-path
references are prose/proof-command projections. The "already reach
for" demand rationale is false in substance (the pin is not the
demand). Limb (b) reproduced mechanically: 9 named, 12 unnamed,
exact lists match. Limb (c) reproduced: exactly connections,
input_values, querysets, write_transaction, write_values lack
`__all__`. Birth provenance re-verified (`a8f31a2d` introduced all
three claims in one edit over 18 submodules with 9 named and
oracle-only short-spelling reads; `d4c07d7d` framing accurate).
Defect bar: DRY.md "docstring contradicting its body" class,
direct sibling of endorsed types D1; filed as
minor/closeout-homed/blocks-nothing, the correct non-blocker
routing — editorial fix shape, no behavior change.

(g) No-families / no-adoptions / nothing-pending CONFIRM. All
counts 1; composed defs route to undispatched file items
(relations/strings/typing) and verified querysets; Pending
execution correctly absent (all `static-reviewed`, zero-edit, no DB
surface — sharded/PG inapplicable by construction, accepted).
Index rows: 4, collision-free, correctly held. Item-scoped diff:
target CLEAN, artifact the only (untracked) output — no ledger row
owed. Link scaffold intact (every use defined, every def used, all
targets exist). HEAD unmoved at `0c0537e2`.

Verdict: verified. Zero-edit file item stands as submitted.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[pyproject]: ../../pyproject.toml

<!-- docs/ -->
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[cmds-init]: ../../django_strawberry_framework/management/commands/__init__.py
[consumers]: ../../django_strawberry_framework/consumers.py
[ext-init]: ../../django_strawberry_framework/extensions/__init__.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[mgmt-init]: ../../django_strawberry_framework/management/__init__.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mw-init]: ../../django_strawberry_framework/middleware/__init__.py
[optimizer-init]: ../../django_strawberry_framework/optimizer/__init__.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[rest-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py
[utils-input_values]: ../../django_strawberry_framework/utils/input_values.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-init]: ../../tests/utils/test_init.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
