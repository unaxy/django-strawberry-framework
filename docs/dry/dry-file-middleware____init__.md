# DRY review: `django_strawberry_framework/middleware/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, or is a rejection
carrying its contract difference + trigger. Zero production edits; zero
tracked files changed.

## System trace

Trivial target (11 lines, FRESH — no prior cycle record names it): a module
docstring and nothing else — no imports, no names bound, no `__all__`, no
logic. Its two stated rules are both about what the file does NOT do: it
imports nothing optional (so parent-package import stays clean on
toolbar-less machines and whole-package walkers traverse it), and it
re-exports neither leaf (the consumer surface is the full leaf dotted path
in a `MIDDLEWARE` settings string; importing the leaf is the
soft-dependency opt-in, spec-042 Decisions 3/4/5).

Connected code read for judgment, outside the item:
[middleware/debug_toolbar.py][debug-toolbar] (full; `require_debug_toolbar()`
thin wrapper over [utils/imports.py][imports]`::require_optional_module`
run at leaf import time, plus the `INSTALLED_APPS` second gate — the
mechanism this file's opt-in prose projects),
[middleware/request_body.py][request-body] (full head + `__all__`; the
second leaf, likewise un-re-exported, reached by `MIDDLEWARE` dotted path),
[utils/imports.py][imports] (full; the `require_optional_module` raising
primitive owned there), the package root [__init__.py][pkg-root] (full;
confirms no middleware import and a toolbar-free `__all__` — the
Decision-3-shaped omission at the root side), the contract source
[spec-042][spec-042] Decisions 3/4/5 (lines 1009-1103 read), the oracle
[test_debug_toolbar.py][test-debug-toolbar] (absence/presence/broken-install
guards read), and the projection [TREE.md][tree] `middleware/` folder lines
plus the [tree-render][tree-render] generator body (`ast.parse` +
`ast.get_docstring`, no import — projection by derivation, verified
first-hand, same shape the `management/__init__.py` artifact records).

Excluded with reason: the concurrent dirt named in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, IN-FLIGHT `filters/inputs.py` range
hunk + `tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was left
untouched; none of it is in this item's paths and none of it names this
namespace. Sibling leaf items are precedents only
(`package-root-public-surface` rejected each with its own difference; each
named file-local manifest rows) — this artifact re-derives rather than
inherits them.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates no flavor: it binds
no names for any surface. Sibling leaves each aggregate only their own
flavor; the package root is the sole cross-flavor aggregator, so there is
no second cross-flavor export table to drift. Considered family
`package-root-public-surface`: rejected, see F2 (own difference).

**2. Sync/async twins.** No `def`, no `await`, no resolver body. The only
colored pair under this namespace (`__call__` / `__acall__`) is owned and
documented at [request_body.py][request-body]`::GraphQLRequestBodyBoundaryMiddleware`.
No surface (C6 ends here with 0 definitions).

**3. Derived rather than repeated knowledge.** Nothing is derived here and
there is no `__all__` mirror to drift against bindings. The one short
`MIDDLEWARE` dotted-path spelling in the docstring is prose illustration
of the leaf path, not a second statement of it. Considered family
`soft-dependency-require-guard` (indexed owner
[utils/imports.py][imports]`::require_optional_module`, files-covered names
[middleware/debug_toolbar.py][debug-toolbar]): checked, no surface — no
guard call, no hint string, no optional import lives here (C5 ends here
with 0 definitions). Considered boundary-mark families
(`request-body-boundary-protocol-marks`, `boundary-method-name-single-sourcing`,
`csrf-ordering-exemption`, whose files-covered name the request_body leaf):
checked, no surface — this file holds no mark, no method name, no
exemption object (C6 ends here with 0 definitions).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack,
build/parse halves. No surface.

**5. Contracts restated in another medium.** Three media carry this file's
contracts: production mechanism (the leaf guard + the root omission, both
elsewhere); the authoritative contract source [spec-042][spec-042]
Decisions 3 (no root, no `__init__` re-export; dotted-path surface),
4 (subpackage marker stays empty-and-importable; leaf is the opt-in), 5
(import-time guard at the leaf; walkers traverse the innocent parent);
projections (this docstring, [TREE.md][tree] folder lines rendered from it
without importing). Consumers/oracles: Django's `MIDDLEWARE`
`import_string` (leaf only), the absence oracle below. A Decision-3 lift
moves the root + leaf guard, never this file (C4).

**6. Enforcement by omission.** The no-re-export IS the enforced omission
and it carries its contract source (Decision 3). Both leaves are absent;
nothing the contract requires is missing — the request_body leaf is
likewise leaf-surfaced via its `MIDDLEWARE` string per its own module
docstring, so the omission is uniform, not a gap over one leaf. No member
lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **1 top-level statement**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (import-clean paragraph + no-re-export/opt-in paragraph + walker paragraph) | (none) | F1 + F2 (prose projection; code binds nothing) |

Rules: R1 import-clean marker (zero imports); R2 no-re-export leaf
opt-in surface (absence of both leaves). Two indexed families considered
(`soft-dependency-require-guard`, `package-root-public-surface`): one
checked with no surface (Matrix axis 3, C5), one rejected with contract
difference + trigger (F2). No existing family name is reused for a
finding; two new file-local rows are named for Worker 0 to add (see
Judgment).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 reword | reword the import-clean paragraph (e.g. rename the walkers) | **1** (this file's statement 1; [TREE.md][tree] folder lines re-render as projection; the absence oracle reads behavior, not wording) | file-local — proves no second site |
| C2 | R1 violation | add an eager leaf import (`from .debug_toolbar import ...`) | **1** (this file gains the binding; the absence oracle `test_package_and_middleware_imports_stay_clean_without_toolbar` fails as oracle, not counted) | file-local — proves the marker is load-bearing |
| C3 | R2 violation | re-export either leaf (`from .debug_toolbar import DebugToolbarMiddleware` or the request_body class) | **1** (this file gains the binding; Decision 3 prose + leaf guard move not at all) | file-local — proves the omission is the rule |
| C4 | R2 omission lift | lift Decision 3 (root-export the toolbar) | **0 here** (root gains import lines; the leaf guard moves; this docstring paragraph becomes false prose, a projection, not a definition) | independent — proves separation |
| C5 | `soft-dependency-require-guard` check | change hint text or guard semantics | **0 here** ([utils/imports.py][imports]`::require_optional_module` + [debug_toolbar.py][debug-toolbar]`::require_debug_toolbar` move; no guard verb appears in this file) | no surface — do not inherit |
| C6 | boundary-mark / async-twin check | change boundary marks, method name, exemption, or the `__call__`/`__acall__` pair | **0 here** (`_boundary_ordering.py` + [request_body.py][request-body] + `views.py` move; this file holds no mark, no name, no twin) | no surface — do not inherit |
| C7 | R2 leaf-side move | rename the leaf path or class | **0 here** (leaf + spec prose move; this docstring illustration follows as projection) | independent — proves separation |

No executable proof was run: the target has no runtime semantics beyond
package existence (no branches, no awaits, no queryset/transport code), so
there is no behavior an execution could distinguish. The read-only
`ast.parse` enumeration above ran in the shared tree (non-mutating; the
workspace recipe authorizes mutating proofs, of which this item has none).
Parent-package import cleanliness is exercised by the absence oracle on
every suite run. All claims below are therefore `static-reviewed`; there
is no `execution-deferred` proof and no `docs/dry/temp-tests/` scratch was
created.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — middleware import-clean marker (file-local)

- **Contract + variation.** `import django_strawberry_framework.middleware`
  imports nothing optional and binds nothing, so it succeeds on
  toolbar-less machines and whole-package walkers (the [TREE.md][tree]
  renderer, coverage collection) traverse it safely. Legitimate variation:
  docstring wording only — verified first-hand: the body is one `Expr`
  node, zero `Import`/`ImportFrom` nodes.
- **Sites + roles.** *Definition*: `django_strawberry_framework/middleware/__init__.py`
  statement 1 (the file binds no symbol to cite). *Contract source*:
  [spec-042][spec-042] Decisions 4 (marker stays empty-and-importable)
  + 5 (walkers traverse the innocent parent; the leaf guards at import).
  *Projection*: [TREE.md][tree] `middleware/` folder lines, rendered from
  this docstring by the [tree-render][tree-render] generator without
  importing (`ast.parse` + `ast.get_docstring` read in its body).
  *Oracle* (independent): [test_debug_toolbar.py][test-debug-toolbar]`::test_package_and_middleware_imports_stay_clean_without_toolbar`
  (fresh parent import under simulated toolbar absence stays clean; star
  import binds no toolbar name). *Consumers*: none of the bare namespace —
  package-wide grep finds no `from ...middleware import` of the parent;
  Django reaches the leaf directly via the `MIDDLEWARE` dotted string.
- **Challenges.** C1 → 1 definition (this file); C2 → 1 here (the marker
  is load-bearing: violating it trips the oracle).
- **Owner + lifetime.** This file (narrowest cohesive owner by
  responsibility: a package marker can only live at its own path; no other
  module can own it without reversing the import direction). No stored
  derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): the single owner stands.
- **Distinct behavior.** The marker covers import-cleanliness + traversal
  only; the guard mechanism lives at the leaf (F2's mechanism note), the
  boundary ordering at `_boundary_ordering.py` + the request_body leaf.
- **Behavioral proof.** `static-reviewed`. Rejects "a second site states
  the cleanliness rule" (whole-package grep for the parent namespace finds
  only this file, the two leaf modules, and the oracle; the leaf
  docstrings state their own guard facts, not the parent's) and "the
  TREE.md lines are a second definition" (the generator derives them from
  this docstring without importing — derivation, not authorship).
- **Structural gate.** The absence oracle above; negative control is
  structural (C2: any eager optional import here fails the fresh-import
  assertion loudly). No bespoke existence test owed (principle-9 economy).
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/middleware/__init__.py`
  `6e1b64ca7b937bb71e9cadeadd92e82236d9e1f8`,
  `django_strawberry_framework/middleware/debug_toolbar.py`
  `5360149bfa207e707c98985e9a1d79672220b210`,
  `django_strawberry_framework/middleware/request_body.py`
  `e6e32e785ec84360c63c9ff529a58f8d63bc8898`,
  `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
  `f1990e71d817ce8b23df90b6ee10e95b2a1c760d`,
  `tests/middleware/test_debug_toolbar.py`
  `692f1ef918f597786453a4f2244f4ccf3a46ccac`,
  `docs/TREE.md`
  `cd075cbb6726bfb7f317ca206d44645eac323cfd`,
  `scripts/build_tree_md.py`
  `b8c4d47a29fa0d48a33d09c9a75b4df7ea08a385`.
  Searched population for a second cleanliness statement: whole package +
  `tests/middleware/` + `docs/`; bodies of both leaves, [imports][imports],
  and [pkg-root][pkg-root] read in full and excluded on strength of body
  (distinct contracts recorded above).

### F2 — middleware no-re-export leaf opt-in surface (file-local)

- **Contract + variation.** Neither leaf is re-exported here — deliberately
  (Decision 3). The consumer surface is the full leaf dotted path in a
  `MIDDLEWARE` string
  (`django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware`;
  the request_body leaf likewise by its own dotted path); importing the
  leaf module is the soft-dependency opt-in. No legitimate variation while
  Decision 3 stands.
- **Sites + roles.** *Contract source*: [spec-042][spec-042] Decision 3
  (no root, no `__init__` re-export; dotted-path surface; class name as
  ecosystem convention). *Mechanism definitions*:
  [debug_toolbar.py][debug-toolbar]`::require_debug_toolbar` (thin wrapper
  over [imports][imports]`::require_optional_module`, run at leaf import
  time) + the `INSTALLED_APPS` gate; the request_body leaf's
  `MIDDLEWARE`-string surface per its own module docstring.
  *Projection*: this file's statement-1 paragraphs 2-3 (states the dotted
  path + the opt-in + the Decisions pointer). *Omission enforcement*:
  root [__init__.py][pkg-root] carries no middleware import and its
  `__all__` stays toolbar-free (full read). *Oracle*: the leaf-absent
  raise (`test_leaf_import_raises_install_hint_when_toolbar_absent`) pins
  the leaf as the opt-in boundary independently of this prose.
- **Challenges.** C3 → 1 here; C4 → 0 here; C7 → 0 here. C3/C4 opposition
  proves the separation: violating the omission moves only this file,
  lifting the contract moves everything but this file.
- **Owner + lifetime.** Decision 3 owns the contract; the leaf + the root
  own the mechanism (guard call; omission). This file carries prose only.
  No stored derivation; no lifetime fields owed.
- **Migration.** None.
- **Distinct behavior.** The omission covers both leaves uniformly; the
  debug_toolbar guard (soft-dep) and the request_body ordering (hard-dep,
  no guard) differ in mechanism but share the surface shape — leaf dotted
  path, never a re-export.
- **Behavioral proof.** `static-reviewed` (grep: no bound name in this
  file; no middleware import in the root; leaf guard body read).
- **Structural gate.** The leaf-absent oracle above (pre-existing, not a
  new gate); the omission itself needs none — any re-export arrives as a
  visible import line in this file.
- **Coupling.** None.
- **Freshness.** Target `6e1b64ca7b937bb71e9cadeadd92e82236d9e1f8`,
  leaf `5360149bfa207e707c98985e9a1d79672220b210`,
  [imports][imports] `291ecedd30c7d8af9c007758112e867c09d031eb`,
  package root `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  spec file `f1990e71d817ce8b23df90b6ee10e95b2a1c760d`,
  oracle file `692f1ef918f597786453a4f2244f4ccf3a46ccac`.
- **Rejection (nested).** Considered: consolidate the no-re-export posture
  into indexed family `package-root-public-surface` (same "manifest"
  vocabulary). Contract difference (OWN — distinct from the auth and
  extensions rejections): those leaves hold eager re-export manifests
  (`__all__` mirrors of home-module bindings) whose root-exclusion is
  structural-per-flavor; this file holds NO manifest at all — not even for
  the guard-free request_body leaf — because a Django middleware's public
  identity is a settings dotted string, never an import binding, so there
  is no binding table here to unify with the root's. Posit lifting
  Decision 3 → the root moves and this file does not (C4); posit adding a
  second middleware leaf → this file still moves not at all (no manifest
  to extend — contrast the auth manifest, which gains a row per factory).
  Different responsibility, different population, opposite reasons to
  change: same vocabulary, not the same rule. Trigger to reconsider: a
  decision to re-export middleware symbols for import (abandoning the
  dotted-string surface) would make the sites one rule. Durable home: this
  clause.

## Defects

None. The docstring matches its body (a marker with no other content);
the Decisions 3/4/5 pointer matches the spec headings verbatim (verified
at [spec-042][spec-042] lines 1009-1103: D3 states both non-re-exports +
the dotted-path surface; D4 states the empty-and-importable marker + leaf
opt-in; D5 states the leaf import-time guard + walker traversal of the
parent); the zero-optional-imports claim is trivially true (zero import
nodes); the axis-6 sweep finds no member lacking a required guard.

(Worker 2): traced independently first-hand; no additional defects found.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond package existence, parent cleanliness resolves through the absence
oracle on every suite run, and the only instrument used (`ast.parse`) is
non-mutating. Inspection alone suffices — there is no ordering,
transactional, or async axis an execution could distinguish (principle 8),
and the file composes no body by name that a behavior proof could target.

## Judgment

Zero-edit file item. Two rules traced, both file-local with proving
challenges (C1-C4, C7); two indexed families considered — one rejected
with its own contract difference + trigger (`package-root-public-surface`,
F2), one checked with no surface (`soft-dependency-require-guard` via
Matrix axis 3 + C5); boundary-mark and async-twin families checked with no
surface (C6). No defects, no pending execution, no production edits.
Worker-0 instructions: (a) tick the plan item
`File middleware/__init__.py — dry-file-middleware____init__.md` as
verified under Run `0.0.15 2026-09-18-1` once Worker 2 confirms; (b) add
these two `## Responsibility index` rows (both `file-local`, holding item
`File middleware/__init__.py`):

| `middleware-import-clean-marker` | `django_strawberry_framework/middleware/__init__.py` | `django_strawberry_framework/middleware/__init__.py` | File `middleware/__init__.py` | file-local |
| `middleware-no-reexport-opt-in-surface` | spec-042 Decision 3 (mechanism: `django_strawberry_framework/middleware/debug_toolbar.py::require_debug_toolbar` + root omission) | `django_strawberry_framework/middleware/__init__.py` | File `middleware/__init__.py` | file-local |

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `5e8573388643ef6d95e80ca52e81fcfca8727635`:
`git diff <baseline> -- django_strawberry_framework/middleware/__init__.py`
empty; `git status --short -- django_strawberry_framework/middleware/`
clean; target blob `6e1b64ca7b937bb71e9cadeadd92e82236d9e1f8` matches both
`HEAD:django_strawberry_framework/middleware/__init__.py` and the working
tree — target CLEAN. The artifact itself
(`docs/dry/dry-file-middleware____init__.md`) is a new untracked file, the
item's only output. No `uv run ruff format .` / `ruff check` run (no edits
to format). The `## Owned changes` ledger (walker D1 fix + 2 live test
files) gains no row from this item. Concurrent dirt named in the dispatch
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, IN-FLIGHT `filters/inputs.py` range
hunk + `tests/filters/test_inputs.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) plus sibling
untracked `dry-file-*.md` artifacts were left untouched. No scratch paths
created (`docs/dry/temp-tests/`, workspace copies: none). No shared-tree
pytest (entry command authorizes none for this item; inspection-only proof
needs none — stated above, not a gap).

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Worked expectation-first: read AGENTS.md,
DRY.md, worker-2.md, the plan item (`File middleware/__init__.py`, Run
`0.0.15 2026-09-18-1`), the 11-line target, the item-scoped diff
(`git diff 5e8573388643ef6d95e80ca52e81fcfca8727635 --
django_strawberry_framework/middleware/__init__.py`, empty, exit 0, plus
`git status --short`), every connected site below, then the artifact
findings. Worker 1's worker-memory never opened. HEAD `9031cb3d`
confirmed (`git rev-parse HEAD`).

### Own trace

Re-derived before opening `## Findings`. The target binds nothing: one
module docstring, zero `Import`/`ImportFrom` nodes, no `__all__`, no
logic. Its two stated rules are both about what the file does NOT do.

| Rule | Owner I would choose | Change test | Count |
|---|---|---|---|
| R1 import-clean marker | this file (narrowest cohesive owner: a package marker can only live at its own path; no other module can own it without reversing the import direction) | reword paragraph / add eager leaf import | 1 / 1 here |
| R2 no-re-export leaf opt-in | spec-042 Decision 3 owns the contract; the leaf + the root own the mechanism (guard call; omission); this file carries prose only | re-export a leaf / lift Decision 3 / rename leaf path | 1 here / 0 here / 0 here |

Docstring claims verified first-hand:

- Zero imports: `ast.parse` over the working tree gives
  `len(ast.Module.body) == 1`, kinds `['Expr']`, zero import nodes.
- Leaf-module opt-in mechanism at
  [debug_toolbar.py][debug-toolbar]: `require_debug_toolbar()` thin
  wrapper over [imports][imports]`::require_optional_module` run at leaf
  import time (line 117), plus the `INSTALLED_APPS` second gate (lines
  128-129); full leaf body read (301 lines).
- Spec-042 Decisions 3/4/5: headings at lines 1009/1033/1073 read
  verbatim — D3 states both non-re-exports + the dotted-path surface
  (lines 1020-1029); D4 states the empty-and-importable marker + leaf
  opt-in (lines 1040-1042); D5 states the leaf import-time guard + walker
  traversal of the innocent parent (lines 1091-1105).
- TREE renderer traversal:
  [tree-render][tree-render]`::python_docstring` (`ast.parse` +
  `ast.get_docstring`, lines 164-174, no import),
  `::folder_description` (reads `__init__.py` first sentence, lines
  363-380), `::first_python_docstring_sentence` (lines 233-240); TREE.md
  `middleware/` folder lines (244, 377) render this file's first
  sentence verbatim, and the leaf lines render each leaf's first
  sentence — projection by derivation, not authorship.
- MIDDLEWARE dotted-string surface: package-wide scan finds no
  `from ...middleware import` of the parent (only docstring mentions +
  leaf dotted strings); `examples/fakeshop/config/settings.py` lines 94
  and 103 list both leaves by full dotted path; the package root
  [pkg-root][pkg-root] carries no middleware import and its `__all__`
  stays toolbar-free (full 169-line read).

### Reconciliation vs Worker 1

Agree on every row: same owners, same counts (C1 = 1 here; C2 = 1 here,
marker load-bearing; C3 = 1 here; C4 = 0 here; C5 = 0 here; C6 = 0 here;
C7 = 0 here). No difference to reconcile.

### Enumeration check

Own instrument: `ast.parse`, `len(ast.Module.body)` = 1, node kinds
`['Expr']`. Member-by-member vs W1's table: statement 1 (module
docstring, three paragraphs) lands in F1 + F2 as prose projection; code
binds nothing. 1/1 lands, none unassigned. Count matches W1 (1).

### Matrix judgment

Axis 1: agree — target aggregates no flavor (binds no names); sibling
leaves each aggregate only their own flavor; the package root is the
sole cross-flavor aggregator; `package-root-public-surface` rejected
with this file's own difference (below), not inherited. Axis 2: agree —
no `def`, no `await` in target; the only colored pair under the
namespace (`__call__` / `__acall__`) is owned and documented at
[request-body][request-body]`::GraphQLRequestBodyBoundaryMiddleware`;
C6 ends here with 0 definitions. Axis 3: agree — nothing derived here,
no `__all__` mirror; the dotted-path spelling is prose illustration,
not a second statement; `soft-dependency-require-guard` checked with no
surface (target grep for `_BOUNDARY` / `require_optional` /
`require_debug` empty; no guard call, no hint string, no optional
import); boundary-mark families checked with no surface (this file
holds no mark, no method name, no exemption object). Axis 4: agree — no
encode/decode halves. Axis 5: agree — Decision-3 lift moves root + leaf
guard, never this file (C4); three media correctly classified
(mechanism elsewhere / spec-042 source / projections). Axis 6: agree —
the no-re-export IS the enforced omission with contract source
(Decision 3); both leaves absent uniformly (request_body leaf likewise
leaf-surfaced via its `MIDDLEWARE` string per its own module
docstring); no member lacks a required guard. Minimal-matrix reasons
all judged sound.

### Counts, roles, oracles

Counts confirmed as above (C1-C3 = 1 here; C4-C7 = 0 here). Roles
confirmed: this file statement 1 = definition of the marker/omission
(F1) + prose projection of Decision 3 (F2); spec-042 Decisions 3/4/5 =
contract sources; TREE.md folder lines = projections (derived without
import); Django's `MIDDLEWARE` `import_string` (leaf only) = consumer;
[test-debug-toolbar][test-debug-toolbar]`::test_package_and_middleware_imports_stay_clean_without_toolbar`
= independent absence oracle (fresh parent import under simulated
absence stays clean; star import binds no toolbar name — reads
behavior, not wording);
`::test_leaf_import_raises_install_hint_when_toolbar_absent` = leaf
opt-in oracle (pins the leaf as the boundary independently of this
prose). No oracle rewritten to read from the owner it checks.

### Equivalence (principle 8) + Pending

`static-reviewed`, and inspection-only is adequate here: the target has
no runtime semantics beyond package existence — no branches, no awaits,
no queryset/transport code — so no execution could distinguish anything
a read cannot; parent cleanliness resolves through the absence oracle
on every suite run; the file composes no body by name that a behavior
proof could target. No probe run, none owed. `## Pending execution`
absent: correct, nothing deferred. No `docs/dry/temp-tests/` scratch
created.

### Zero-edit confirmation

Item-scoped diff confirmed empty by my own command (no output, exit 0);
`git status --short -- django_strawberry_framework/middleware/` clean;
working blob `6e1b64ca7b937bb71e9cadeadd92e82236d9e1f8` reported by
`git hash-object` equals the artifact's recorded target blob.
Coverage validated (1/1 members assigned; 2 indexed families
considered). No production edit owed by a file item; none demanded.

### Rejections, fingerprints, gates, pending, coupling

F2 nested rejection carries its OWN contract difference (judged vs the
auth and extensions prior rejections): auth = structural opt-in vs
default recipe (root must never import auth so an auth-free consumer
never pays `django.contrib.auth`); extensions = default-recipe root
rule vs opt-in per-extension membership rule; this file = NO manifest
at all — not even for the guard-free request_body leaf — because a
Django middleware's public identity is a settings dotted string, never
an import binding, so there is no binding table here to unify with the
root's. C4/C-second-leaf opposition proves it (lifting Decision 3
moves the root and not this file; adding a second middleware leaf moves
this file not at all — contrast the auth manifest, which gains a row
per factory). Trigger (decision to re-export middleware symbols for
import, abandoning the dotted-string surface) is concrete and would
make the sites one rule; durable home (this clause) named. The two
no-surface routings each judged sound (C5 greps re-verified empty;
C6 marks/names/twins live at `_boundary_ordering.py` +
[request-body][request-body] + `views.py`, none here). All 9 freshness
blobs re-hashed via `git hash-object` — every one matches, including
the target (`6e1b64ca…`), both leaves (`5360149b…`, `e6e32e78…`), spec
(`f1990e71…`), oracle (`692f1ef9…`), TREE (`cd075cbb…`), tree renderer
(`b8c4d47a…`), imports (`291ecedd…`), and root (`0ef72601…`). No new
gate created (principle-9 economy correct: C2 is the structural
negative control — any eager optional import here fails the fresh-import
assertion loudly; the leaf-absent oracle is pre-existing, not a new
gate). Coupling: none marked, none owed.

### AGENTS.md prose check

No production diff, so no provenance, citation, tier, changelog, or
commit rule is reachable. Artifact uses `path::Symbol` citations and
the reference-style link block with all 10 canonical group headers;
concurrent dirt (connection.py / resource_policy.py / filters+forms
hunks, staged querysets test, bug-hunt/dry plan edits, sibling
untracked `dry-file-*.md` artifacts) untouched — only this artifact's
`Status:` line, `## Defects` (Worker 2) line, and this section changed.
No commit.

### Verdict

`Status: verified`. Two file-local rows owed; Worker 0 index lines in
the return. No defects, no pending execution, no edits.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-042]: ../SPECS/spec-042-debug_toolbar-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[imports]: ../../django_strawberry_framework/utils/imports.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[request-body]: ../../django_strawberry_framework/middleware/request_body.py

<!-- tests/ -->
[test-debug-toolbar]: ../../tests/middleware/test_debug_toolbar.py

<!-- examples/ -->

<!-- scripts/ -->
[tree-render]: ../../scripts/build_tree_md.py

<!-- .venv/ -->

<!-- External -->
