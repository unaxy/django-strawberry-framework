# DRY review: `django_strawberry_framework/testing/__init__.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to an open
family holding item, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Small target (64 lines): the consumer-testing subpackage's leaf manifest. It
DEFINES one enforcement (the relay-helper withholding, by omission of any
`relay` import) and COMPOSES the rest by name: 1 re-export binding from
`_wrap.py`, 6 from `client.py`, and the 7-member `__all__` mirror. The module
docstring carries five contract bullets (three client-family summaries, the
wrap-helper bullet, the withholding bullet). No `def`, no `class`, no branch,
no `await`, no `sync_to_async`, no `__getattr__`, no bus row, no deprecation
shim, no queryset, no transport: runtime effects are import-time binding only.

Connected code read for judgment, outside the item: [testing-client][testing-client]
(full 556-line worktree read; HEAD 568 lines — dirt characterized below),
[testing-wrap][testing-wrap] (full), [testing-relay][testing-relay] (full worktree
read; dirt characterized below), [django-patches][django-patches] (module
docstring framing + `_is_database_failure` region at HEAD bytes; dirt outside
both), [conf][conf] (`TESTING_ENDPOINT_KEY` block +
`testing_endpoint_setting` + `__test__` guard; dirt outside all three),
[pkg-root][pkg-root] (full grep: zero `testing` / `TestClient` tokens),
[filters-init][filters-init] (full: the eager-re-export twin leaf),
[rest-init][rest-init] (full: the guard-only leaf, a deliberate non-manifest),
oracles [test-client][test-client] (export-surface + collection-guard tests;
byte-identical at both revisions, line numbers only moved),
[test-relay][test-relay] (import block + decode-identity assertion; dirt
outside both) and [test-wrap][test-wrap] (import block), contract sources
[spec-043][spec-043] Decision 4 (full passage, read) and [spec-032][spec-032]
Decision 10 + DoD + exports-list note (read), consumer-import census across
`django_strawberry_framework/` + `tests/` + `examples/fakeshop/` (grep
population: 24 root-import sites, 9 dotted-`testing.relay` sites), and prose
projections [docs-readme][docs-readme] (2 usage lines, identical at HEAD) +
[glossary][glossary] (TestClient family entries) + [fakeshop-readme][fakeshop-readme]
(TestClient import block).

Dirt note (judged regions verified identical at both revisions; nothing
touched): the target itself is CLEAN — worktree
`48b45d1b433283c40bf8d602d71a26d261a833b2` equals
`HEAD:django_strawberry_framework/testing/__init__.py`. [testing-wrap][testing-wrap],
[pkg-root][pkg-root], [filters-init][filters-init], [rest-init][rest-init],
[test-wrap][test-wrap], both specs, [glossary][glossary], and
[fakeshop-readme][fakeshop-readme] are clean. Hunt-dirtied inputs, each traced
with both fingerprints recorded: [testing-client][testing-client] (worktree
`b1439443…` vs HEAD `d8feebb2…`: `_safe_arg_repr` → `truth.render` retarget
plus one deleted `len()`-guard arm plus one docstring reflow — all outside the
judged regions: class/def names, `__all__`, the `__test__` guard, the endpoint
ladder, and the delegation line); [testing-relay][testing-relay] (worktree
`f807bf92…` vs HEAD `df0dc72a…`: `truth` migration inside `global_id_for` —
outside the judged regions: module docstring, `__all__`, def name/signature);
[django-patches][django-patches] (4 hunks in capture/validate/install
functions — outside the framing docstring and `_is_database_failure`);
[conf][conf] (126 changed lines, zero naming `TESTING_ENDPOINT` /
`testing_endpoint_setting` — grep-verified); [test-client][test-client] (70
changed lines, zero naming `export_surface` / `testing_root` / `__test__` —
grep-verified; the two oracle bodies are byte-identical, HEAD lines 584/644 vs
worktree lines 526/586); [test-relay][test-relay] (hostile-input test
removals — outside the import block and the decode-identity assertion);
[docs-readme][docs-readme] (2-line insertion elsewhere — both cited lines
identical at HEAD). Every count below holds at both revisions.

Excluded with reason: the only Responsibility-index row whose files-covered
list names this subsystem is `one-sync-boundary` (names `testing/client.py`,
not this leaf — checked, no surface: C11). `upstream-patch-lifecycle` and
`upstream-patch-refusal-wording` (open; patch-module mechanics + raise wordings
— checked: this file is a by-name consumer row only, C13/C14),
`subsystem-clear-lifecycle` (verified; no bus row here — full read, C12),
`soft-dependency-require-guard` (open; hard deps only here, C14),
`hostile-mapping-hardening` (open; no mapping read here, C14). The definitions
this leaf composes are owned by the undispatched file items `testing/_wrap.py`,
`testing/client.py`, `testing/relay.py` — their routing is theirs, not this
item's. `types/relay.py::decode_global_id` (the re-export chain below the
leaf) is witnessed by the decode-identity oracle, never body-read. No index row
named `package-root-public-surface` exists; the filters-twin and orders-twin
treatments of the leaf-vs-root shape were orientation only (prior rejections
are triggers to check), and the difference is re-derived fresh below with this
leaf's own Decision-4 evidence (F1 nested rejection).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Target aggregates ONE subsystem
(consumer test utilities) from two home modules plus one deliberate
withholding. Sibling leaves, each fully read: [filters-init][filters-init] is
the eager-re-export twin (13 primitives + helper + ledger + `__all__` tuple);
[rest-init][rest-init] is the deliberate non-manifest (guard call only, no
`__all__` — different responsibility, not a missing manifest); the orders leaf
per its verified artifact is the same eager shape with per-family parameters.
The package root is the sole cross-flavor aggregator and carries zero
`testing` / `TestClient` tokens (grep count 0 over [pkg-root][pkg-root]) per
[spec-043][spec-043] Decision 4. The shared eager-re-export + `__all__` shape
across manifest leaves is intentional separation per export-grain contract
(Decision 4 documents all three postures of THIS subpackage in one paragraph:
wrap root-re-exported, relay submodule-only, client family root-re-exported by
prior commitment), not duplication — re-derived fresh with this leaf's own
difference (F1 nested rejection). No second testing manifest exists anywhere:
whole-tree grep for `from django_strawberry_framework.testing import` finds
only consumer imports (24 sites) plus the [testing-wrap][testing-wrap]
docstring example — every one resolves through this file.

**2. Sync/async twins.** Inapplicable with reason: the target defines no
colored pair — no `def`, no `async def`, no `await`, no `sync_to_async` (full
64-line read). The sync/async colors (`TestClient.query` /
`AsyncTestClient.query`, sync/async `login`) are owned at
[testing-client][testing-client]. Considered family `one-sync-boundary`
(files-covered names `testing/client.py`, not this leaf): checked, no boundary
call lives in this file (C11). No twin surface here.

**3. Derived rather than repeated knowledge.** `__all__` hand-mirrors the 1 +
6 re-export bindings in the SAME file (one edit region, adjacent lines, not
two definitions). Nothing is re-derived at runtime: the leaf computes no
default (the `"/graphql/"` default is spelled in the docstring bullet as prose
and owned at [conf][conf]`::testing_endpoint_setting`, consumed by
[testing-client][testing-client]`::TestClient.__init__`); the input light-ness
is structural (no `relay` import exists to pay), not a derived flag. The
endpoint-ladder sentence and the Trac-framing bullet restate owner contracts
in prose only — projections, challenged at C9/C10, rejected at F3 (0
definitions here). The `__test__` collection-guard question ends here with 0
definitions (C15: the guard lives once on the class object at
[testing-client][testing-client] and once on the reader function at
[conf][conf]; the attribute travels with the imported object, so the leaf
needs no second guard).

**4. Inverse / round-trip pairs.** No encode/decode, pack/unpack, build/parse
halves. Import binding → `__all__` membership → `import *` binding is one
direction with a single author (this file), not two halves that can drift
apart. The relay withholding has no decode half (absence is absence; the
dotted submodule path is the forward path, not an inverse). No deprecation
shim exists (no `warnings`, no `deprecated` token in the full read). No
surface.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (2 import statements + `__all__` + the withholding
omission); authoritative contract sources ([spec-043][spec-043] Decision 4 for
the export grain + root exclusion, [spec-032][spec-032] Decision 10 + DoD +
exports-list note for the relay gate, the [django-patches][django-patches]
framing docstring for the Trac record, the [testing-client][testing-client] /
[testing-wrap][testing-wrap] docstrings for the summarized mechanics);
independent oracles (the export-surface test pinning 6 names present +
root-absent in both accurate shapes, the collection-guard test, explicit-name
consumer imports at 24 sites resolving through this file without reading
`__all__`, dotted-path imports at 9 sites resolving without the leaf, the
decode-identity assertion); projections (leaf docstring, both READMEs,
[glossary][glossary], spec code blocks, the [testing-wrap][testing-wrap]
docstring example). A new export moves its home definition once; this file's
rows follow by name (C1–C3, C6–C8).

**6. Enforcement by omission.** Three deliberate omissions, each with a
contract source: the relay helpers stay out of the leaf ([spec-043][spec-043]
Decision 4 passage + [spec-032][spec-032] Decision-10 export gate; absence
execution-verified: `hasattr(testing, 'global_id_for')` is `False` and
`testing.relay` is absent from `sys.modules` after `import testing`) — F2; the
whole testing surface stays out of the package root (Decision 4 + oracle +
grep-0) — F1; nothing else is withheld (`client.__all__`'s 6/6 names bound
here, `_wrap.py`'s single public name bound here — verified against both home
modules). No member lacks a guard its contract requires: the only guard in
this subsystem (`__test__`) is owned where its objects live (C15). The
withholding carries no negative suite oracle (no test asserts the absence) —
recorded as observation O2 in F2's gate section, not a defect: no contract row
requires a negative pin, and a bespoke absence test per withheld name would
violate the gate-only economy (principle 9).

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **4 top-level statements**, binding **8 module-level names** (7
re-exports + `__all__`). Every member lands below; every challenge in
`### Challenges` ends in a family row, a file-local row, a rejection, or a
no-surface routing.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (5 contract bullets: client pair + endpoint sentence, Response, mixin family, wrap helper + Trac framing, relay withholding + import-light rationale) | (none) | prose projection, F1/F2/F3 |
| 2 | `from ...testing._wrap import safe_wrap_connection_method` | 1 name | R1, F1 (+ F3 bullet source) |
| 3 | `from ...testing.client import (AsyncTestClient, GraphQLTestCase, GraphQLTestMixin, GraphQLTransactionTestCase, Response, TestClient)` | 6 names | R1, F1 (+ F3 bullet source) |
| 4 | `__all__ = [...]` | 7-member list | R1, F1 |

Rules: R1 testing leaf manifest (statements 2–4 + bullets 1–3 + root-exclusion
posture; 7 = 6 client + 1 wrap); R2 relay withholding (the statement-2/3
omission of any `relay` import + bullet 5; the rule is DEFINED here by
omission); R3 leaf-bullet contract summaries (bullets 1–4 as projections of
owner mechanics). No indexed family is adopted (see Excluded with reason
above); two convergences are recorded as nested rejections (F1, F2); no new
family is named. Five index rows are named for Worker 0 (2 file-local + 3
rejected); the holding items for the composed definitions are the
undispatched file items `testing/_wrap.py`, `testing/client.py`,
`testing/relay.py`.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed, never
counted. All bodies judged identically at HEAD and worktree bytes (see Dirt
note: every dirt hunk sits outside every judged region, grep-verified per
input).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new member | expose an 8th export (e.g. a second `_wrap` helper) | **1** (the definition at its home module; this file's import line + `__all__` entry are consumer rows that follow by name; README blocks are projections) | independent |
| C2 | R1 rename | rename `TestClient` → `GraphQLTestClient` | **1** ([testing-client][testing-client]; import line + list entry + docstring bullets here follow) | independent |
| C3 | R1 home move | move `safe_wrap_connection_method` from `_wrap.py` to `client.py` | **1** (the owner move; exactly one import line here follows) | independent |
| C4 | R1 omission lift | lift Decision 4 (root-export `TestClient`) | **0 here** (the root gains import lines; this file does not move) | independent — proves separation |
| C5 | R1 manifest grain | add a 7th `client.py` name to `client.__all__` without leaf re-export | **1** ([testing-client][testing-client]; the submodule manifest is the distinct 6-name rule — this file's 7-name superset rule does not move) | independent — distinct sets, opposite changes move opposite files |
| C6 | R2 lift | re-export `global_id_for` from the leaf | **1 here** (import line + `__all__` entry; the 9 dotted-path consumers keep resolving — compatible alias, listed not counted; [testing-relay][testing-relay] untouched) | independent — the enforcement lives here |
| C7 | R2 sibling growth | add a third helper to `testing/relay.py` | **0 here** ([testing-relay][testing-relay] moves; the withholding holds unchanged) | independent — proves separation |
| C8 | R2 path rename | rename the submodule `relay` → `globalids` | **1** (the submodule move; this file's bullet follows as projection; 9 consumers follow by name) | independent |
| C9 | R3 ladder change | Decision 7 gains a rung (e.g. per-thread override) | **0 here** ([testing-client][testing-client] + [conf][conf] own the ladder; the leaf bullet is projection) | no definition here — prose follows |
| C10 | R3 framing change | Django fixes Trac #37064 (retire the patch) | **0 here** ([django-patches][django-patches] owns the framing, [testing-wrap][testing-wrap] the consumer contract; the leaf bullet is projection) | no definition here — prose follows |
| C11 | `one-sync-boundary` check | change the one-boundary rule | **0 here** (owned at `utils/querysets.py::run_in_one_sync_boundary`; the family names `testing/client.py`, not this leaf; no boundary call lives here) | no surface — do not inherit |
| C12 | `subsystem-clear-lifecycle` check | change the clear-bus contract | **0 here** (no `register_subsystem_clear` row in the full read) | no surface — do not inherit |
| C13 | `upstream-patch-lifecycle` check | change the capture/install/probe lifecycle | **0 here** (mechanics live in the four patch modules; statement 2 is a by-name consumer row of the helper, not a lifecycle site) | consumer row only — do not inherit |
| C14 | guard/wording checks | change a refusal wording, add a soft-dep guard, change a hostile-mapping read | **0 here** (no `raise`, no guard call, no mapping read in the full read; hard deps only) | no surface — do not inherit |
| C15 | `__test__` guard check | pytest collects `testing.TestClient` | **0 here** (guard owned once on the class object at [testing-client][testing-client] + once on the reader at [conf][conf]; the attribute travels with the imported object — the pinned guard test proves the shape) | no surface — do not inherit |

No executable proof was run beyond two read-only import probes quoted under
Findings (module import + attribute/sys.modules reads — non-mutating; the
workspace recipe authorizes mutating proofs, of which this item has none).
The target has no runtime semantics beyond import-time binding (no branches,
no awaits, no queryset/transport code), so no further behavior exists that an
execution could distinguish and the pinned oracles do not already cover. The
probes ran in the shared tree; every other claim below is `static-reviewed`.
No `docs/dry/temp-tests/` scratch was created — inspection suffices, and a
probe could distinguish nothing further.

## Findings

No production edit is owed by a file item; each finding records the rule with
the challenge that proved it has no second site.

### F1 — testing leaf manifest (file-local)

- **Contract + variation.** The testing subpackage's public surface is exactly
7 names, each composed by name from its home module (6 from `client.py`, 1
from `_wrap.py`), with `__all__` mirroring the re-export bindings in-file.
Legitimate variation: set membership only (an 8th export adds one import line
+ one list entry in this file). The whole surface stays out of the package
root ([spec-043][spec-043] Decision 4).
- **Sites + roles.** *Definitions*: [testing-client][testing-client]`::TestClient`,
`::AsyncTestClient`, `::Response`, `::GraphQLTestMixin`, `::GraphQLTestCase`,
`::GraphQLTransactionTestCase`; [testing-wrap][testing-wrap]`::safe_wrap_connection_method`.
*Consumer rows*: this file's statements 2, 3, 4. *Oracles*: the export-surface
test (pins 6/7 names present + root-absent in both accurate shapes —
independent: it spells the six literals and drives `getattr`/`hasattr`, never
reads an owner) + the collection-guard test + explicit-name consumer imports
at 24 sites (resolving through this file without reading `__all__`).
*Projections*: statement-1 bullets 1–3, the Decision 4 passage, both README
usage blocks, the [glossary][glossary] family entries, the
[testing-wrap][testing-wrap] docstring example.
- **Challenges.** C1, C2, C3 → 1 definition each (the home module); C4 → 0
here; C5 → 1 at [testing-client][testing-client] (distinct submodule-manifest
set — proves the two manifests are different rules sharing six members, not
one rule twice).
- **Owner + lifetime.** Per-symbol home modules (existing owners, chosen by
responsibility: each class's/function's declaration, validation, and runtime
machinery all live there; no narrower owner this file's consumers could depend
on exists). This file is a consumer (principle 6: compose by name). No stored
derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owners stand; a new export adds
its definition plus one consumer row here.
- **Distinct behavior.** The manifest intentionally covers only the 7 —
`client.py` names outside its own `__all__` are submodule-private, the relay
helpers are withheld (F2), the root is excluded (Decision 4: "The root's
`__all__` is the schema-building surface; test utilities live where
consumers' test code imports from"). `client.__all__` (6 names) vs leaf
`__all__` (7 names) is grain, not drift: C5 proves opposite changes move
opposite files.
- **Behavioral proof.** `execution-verified` for the binding facts (read-only
shared-tree probe: `testing.TestClient is client.TestClient` →
`True`; `testing.__all__` lists exactly the 7; `hasattr(root, 'TestClient')`
→ `False`; package-root grep count 0), `static-reviewed` for the oracle
readings (both oracle bodies read at both revisions, not executed — no pytest
per [AGENTS.md][agents]). Rejects "a re-export shadows its owner" (by-name
import identity, probed) and "star binding leaks an 8th name" (`__all__`
names exactly the 7 bound re-export names; full-read grep finds no other
public binding in this file).
- **Structural gate.** The export-surface oracle pins presence (6/7 — the wrap
helper rides unpinned) but no exact-set pin exists for this leaf — the same
standing as the filters, orders, auth, and extensions leaves. Standing in:
every consumer imports names explicitly, so a dropped binding fails loudly
(`ImportError`) at use sites on every suite run. Observation O2 (not a
defect): no contract row requires a manifest pin, and a bespoke existence
test per leaf manifest would violate the gate-only economy (principle 9).
- **Coupling.** F2 (a relay re-export would add F1 members while dissolving
F2's rule — one decision, one edit to this file; named here so neither half
is read alone).
- **Freshness.** Target `48b45d1b433283c40bf8d602d71a26d261a833b2` (worktree
== HEAD; target CLEAN), [testing-client][testing-client] HEAD
`d8feebb230bd4e8e2b71e07565c0422ce9d66708` (worktree `b1439443…` hunt dirt in
message renders + one guard arm + one guard docstring — outside the class/def
sites, `__all__`, guard, ladder, and delegation line judged),
[testing-wrap][testing-wrap] `0df97813659bea9ed2002f64e6885896c5cabd6f`
(clean), [pkg-root][pkg-root] `0ef72601ecac300ac87ff993af1b04a4f1bc335a`
(clean; zero `testing`/`TestClient` tokens), [filters-init][filters-init]
`86b258186638c96995e31919346f44d7951c65ea` (clean; eager-shape witness),
[rest-init][rest-init] `45cf7b63a2b768421b80b99ee78ec048a03641e1` (clean;
non-manifest witness), [test-client][test-client] HEAD
`fe01478e206277162c9d38daaa663390d64d07e0` (worktree `517cf1e6…` dirt moves
only line numbers around the byte-identical oracle bodies),
[spec-043][spec-043] `a31a06f1322f66872d99178476454bd792e4e0a7` (clean;
Decision 4), [docs-readme][docs-readme] HEAD
`1497164f903d505b75bfdb79f546a197ea103c0b` (worktree `30978c34…` 2-line
insertion elsewhere — both cited lines identical), [glossary][glossary]
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd` (clean),
[fakeshop-readme][fakeshop-readme] `5392dd1cfbc91bf0d9d7d69cde83eac9e5607af7`
(clean). Searched population for a second manifest of the 7-name set: whole
package + `tests/` + `examples/fakeshop/` + `docs/` (grep `from
django_strawberry_framework.testing import`: 24 consumer sites, all resolving
through this file; zero competing manifests). Excluded on strength of body:
[testing-client][testing-client]`__all__` (the distinct 6-name submodule rule,
C5) and [testing-wrap][testing-wrap] (single public name, no `__all__` — no
second manifest).
- **Rejection (nested).** Considered: consolidate the leaf manifest with the
package-root manifest into one shared manifest rule (same eager-re-export +
`__all__` shape — the filters and orders twins' artifacts rejected the same
shape for their leaves; compared fresh here, not inherited). Contract
difference here: the root manifest is the schema-building default recipe
every consumer pays at package import, while this leaf is the
consumer-test-code opt-in whose membership rule is the Decision-4 three-posture
split (wrap + client family re-exported, relay held out, root excluded) — and
Decision 4 forbids the root from ever carrying these names because both
upstreams separate test utilities from the schema surface the same way
(`strawberry_django.test`, `graphene_django.utils.testing`). Posit
root-exporting `TestClient` → the root moves and this file does not (C4);
posit adding an 8th export → this file moves and the root does not (C1).
Different responsibility, different population, opposite reasons to change:
same shape, not the same rule. CONVERGE with the verified
orders/filters/rest-framework leaf-vs-root direction on fresh evidence (this
leaf's own Decision-4 difference re-derived above). Trigger to reconsider: a
decision to root-export the testing surface, or to drive every subpackage
manifest from one shared driver/validator, would make the sites one rule.
Durable home: [spec-043][spec-043] Decision 4 (already states the grain) +
this file's docstring paragraph 1. Named for Worker 0 as rejected index row
`testing-leaf-vs-root-manifest` (no such row exists in the current plan).

### F2 — relay-helper withholding (file-local)

- **Contract + variation.** `global_id_for` / `decode_global_id` are NOT
re-exported from the leaf: the dotted `testing.relay` submodule path is the
public one, and `import testing` stays light of the relay submodule (no
`relay` import exists in the leaf's import block). Legitimate variation: the
withholding holds or it is lifted — a one-decision binary, not a spectrum.
- **Sites + roles.** *Definition (by omission)*: this file's import block
(statements 2–3 import from `_wrap` and `client` only — the one place that
decides the leaf's surface). *Contract sources*: [spec-043][spec-043]
Decision 4 ("the `relay` helpers are deliberately submodule-only ... keeping
them out of `__init__` keeps the import light") + [spec-032][spec-032]
Decision 10 + DoD (helpers placed at `testing.relay`) + the exports-list note
("the `testing.relay` helpers stay off the exports list per the Decision 10
export gate"). *Consumers*: 9 dotted-path import sites (5 under `tests/`, 4
live-tier) resolving via the submodule, never the leaf. *Oracle*: the
decode-identity assertion (`testing_relay.decode_global_id is
types_relay.decode_global_id` — pins the re-export chain below the leaf;
independent: an identity probe, never reads an owner body). *Projections*:
statement-1 bullet 5, the [testing-relay][testing-relay] docstring passage,
[docs-readme][docs-readme] line 244.
- **Challenges.** C6 → 1 here (the enforcement lives in this file's import
block); C7 → 0 here (a third relay helper moves [testing-relay][testing-relay]
only — proves the withholding is a leaf rule, not a relay rule); C8 → 1 (the
submodule move; the leaf bullet follows as projection).
- **Owner + lifetime.** This file (existing narrowest site by responsibility:
the omission lives in the leaf's import block; no narrower owner exists — a
module cannot un-import itself from its package root, so the rule cannot live
at [testing-relay][testing-relay]). No stored derivation; no lifetime fields
owed.
- **Migration.** None (zero-edit item): the omission stands; lifting it would
be one edit here (import line + `__all__` entry) plus the spec-row update.
- **Distinct behavior.** The withholding is import-posture, not visibility:
the helpers are fully public at the dotted path (DoD-placed, oracle-covered,
live-tier-consumed). Observation O1 (not a defect): bullet 5's "the
submodule's `types`-package imports are paid only by suites that import it"
overstates at HEAD — probed: `types.base` is already in `sys.modules` after a
bare `import django_strawberry_framework` (the root pays it for every importer
of anything under the package), so the marginal `types` cost of a leaf-level
relay import would be zero too. What holds is the load-bearing pair: the
relay submodule itself stays unimported (`testing.relay` absent from
`sys.modules` after both `import django_strawberry_framework` and `import
...testing`, probed) and the leaf adds zero marginal imports beyond
`_wrap`+`client`. The mechanics hold; the rationale clause is loose — breaks
no contract row (the contract is absence + dotted path + gate, all verified),
so not a defect.
- **Behavioral proof.** `execution-verified` (read-only shared-tree probes:
`hasattr(testing, 'global_id_for')` → `False`; `testing.relay` absent from
`sys.modules` post-import; the 9-site dotted-path census resolves without the
leaf). Rejects "the withholding is documentation-only" (the import block
contains no `relay` import — full-read verified — and the probe confirms the
absence at runtime).
- **Structural gate.** No negative suite oracle asserts the absence (grep over
[test-relay][test-relay]: zero `__all__` / `hasattr` / star-import hits) —
recorded as observation O2 (shared with F1's gate note), not a defect: no
contract row requires a negative pin, and a bespoke absence test per withheld
name would violate the gate-only economy (principle 9). Standing in: the
Decision-4 + Decision-10 prose, the enforced-absence probe above, and the
dotted-path consumer census (a widening breaks no consumer loudly — stated
honestly: the gap is a widened surface + paid submodule import with no red
test, which is exactly what a future gate would need to catch).
- **Coupling.** F1 (see F1 Coupling — one decision, one edit).
- **Freshness.** Target `48b45d1b433283c40bf8d602d71a26d261a833b2`,
[testing-relay][testing-relay] HEAD `df0dc72a178854e261fa7236c6614a758a008722`
(worktree `f807bf92…` hunt dirt inside `global_id_for` — outside the module
docstring, `__all__`, and def name/signature judged), [test-relay][test-relay]
HEAD `55e43ed2dc2b740bfbb42a0e4dfca60cab720d73` (worktree `4e61e8f1…`
hostile-test removals — outside the import block and decode-identity
assertion judged), [spec-032][spec-032]
`1e96ad410466b58f1c4ad88e8d8f963feee62565` (clean; Decision 10 + DoD +
exports-list note), [spec-043][spec-043] `a31a06f1322f66872d99178476454bd792e4e0a7`
(Decision 4 passage), [docs-readme][docs-readme] HEAD `1497164f…` / worktree
`30978c34…` (cited line identical). Searched population for a leaf-level relay
re-export: whole package + `tests/` + `examples/` + `docs/` (zero hits — the
9 dotted-path sites are the complete consumer census). Excluded on strength
of body: [testing-relay][testing-relay]`__all__` (the 2-name submodule rule —
the withheld set's definition, not a second withholding).
- **Rejection (nested).** Considered: single-source the withholding rationale
in one docstring (this bullet vs the [testing-relay][testing-relay] docstring
passage restating the light-import rule). Contract difference here: the leaf
bullet states the leaf-side rule (NOT re-exported here + why) for readers
choosing an import path at the leaf; the relay passage states the
submodule-side public-path rule for helper consumers who already arrived.
Different audiences, opposite edit triggers (the bullet moves when the leaf's
export set changes; the passage moves with the helper contract — C7 proves
the passage's home moves alone). Same rationale sentence, not the same rule.
CONVERGE with verified hints-R4 bilateral-import-rationale-prose on fresh
evidence (trigger re-checked: neither passage has grown the other's audience
rule — the leaf bullet names no helper semantics beyond the one-line
mint/decode shape the export grain needs, the relay passage names no leaf
export set). Trigger to reconsider: either passage starts carrying the
other's audience rule → fold into one pointer. Durable home:
[spec-043][spec-043] Decision 4 (already states both postures in one paragraph
— the single prose home for the contrast). Named for Worker 0 as rejected
index row `testing-relay-withholding-prose-pair` (no such row exists in the
current plan).

### F3 — leaf-bullet contract summaries (rejected)

- **Contract + variation.** Statement-1 bullets 1–4 summarize owner mechanics
in one line each: the Decision-7 endpoint ladder + per-instance/per-call
overrides (bullet 1), the `Response` shape + raw-`HttpResponse` carriage
(bullet 2), the mixin family + `self.client` delegation + assertion helpers
(bullet 3), the wrap-time decline + debug-toolbar mirror + Trac #37064
backstop pointer (bullet 4). The shared form considered: shrinking every
bullet to a bare pointer ("see `client.py` / `_wrap.py` / the patch module").
- **Sites + roles.** *Definitions (mechanics owners)*:
[testing-client][testing-client] (ladder passage, `TestClient.__init__`,
`Response`, mixin delegation), [conf][conf] (`TESTING_ENDPOINT` default),
[testing-wrap][testing-wrap] (wrap contract), [django-patches][django-patches]
(Trac framing — the owner of the file-local "Trac record + framing prose"
row, trigger-checked fresh below). *Projections*: the four leaf bullets.
*Oracles*: the subsystem behavior suites (they pin the mechanics, never read
the leaf bullets).
- **Challenges.** C9 → 0 definitions here (a new ladder rung moves owner
docstrings + code; the bullet follows as prose); C10 → 0 definitions here (a
Trac retirement moves the framing owner + wrap contract; the bullet follows
as prose). Both challenges move zero definitions at the leaf under every
posited mechanics change — the bullets are projections, and projections never
own.
- **Owner + lifetime.** Per-bullet mechanics owners above (existing owners by
responsibility; no consolidation moves text anywhere). No stored derivation;
no lifetime fields owed.
- **Migration.** None (zero-edit item): owners stand, bullets stand.
- **Distinct behavior.** Each bullet is a bounded audience summary (the what +
the where, one line, with an explicit see-ref carrying the full contract —
bullet 4's "see the patch module's docstring for the full framing" is the
shape), never a mechanics restatement: no bullet carries a signature, a
predicate body, a version pin, or remediation steps. The
[django-patches][django-patches] file-local framing row's trigger ("a second
framing owner") was checked fresh: the leaf bullet restates no framing
mechanics (no `isinstance` predicate, no audited-source set, no
capture/install/probe lifecycle) — trigger unfired, that row stands
untouched.
- **Behavioral proof.** `static-reviewed`. Rejects "the bullets duplicate the
rules" (C9/C10 prove every mechanics change moves zero leaf definitions —
prose follows, nothing is maintained twice).
- **Structural gate.** Gate-only justification, no new gate: prose drift
between a one-line summary and its owner is caught by reading, not by a
mechanical oracle — every bullet was verified sentence-by-sentence against
its owner body in this pass (endpoint default `"/graphql/"` at
[conf][conf]`::testing_endpoint_setting`'s return; the
`strawberry.test.client.Response` subclass at
[testing-client][testing-client]`::Response`; the `self.client` delegation at
`::GraphQLTestMixin.query`; `::assertResponseNoErrors` /
`::assertResponseHasErrors`; the decline-on-`_DatabaseFailure` at
[testing-wrap][testing-wrap]`::safe_wrap_connection_method` — all symbol-cited
because hunt dirt above them shifts worktree-vs-HEAD line numbers, except the
`Response` class line 61 and the `_wrap.py` lines 144–145, which are identical
at both revisions);
debug-toolbar mirror passage in both wrap docstrings; Trac URL in the patch
framing). A bespoke prose-equality test per bullet would violate the gate-only
economy (principle 9).
- **Coupling.** None.
- **Freshness.** Target `48b45d1b433283c40bf8d602d71a26d261a833b2`,
[testing-client][testing-client] HEAD `d8feebb2…` / worktree `b1439443…`
(dirt outside every judged docstring + body line, as F1),
[testing-wrap][testing-wrap] `0df97813…` (clean),
[django-patches][django-patches] HEAD `ba98f5859ec32971c3aa566c221bdc4db392e137`
(worktree `63f3fa9c…` 4 hunks — outside the framing docstring and
`_is_database_failure`), [conf][conf] HEAD
`c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25` (worktree `ae3de0a3…` — zero
`TESTING_ENDPOINT` lines, grep-verified), [test-wrap][test-wrap]
`4d3c1351254377197994ee577e4f77844c7c309b` (clean; consumer import witness).
Excluded on strength of body: [testing-client][testing-client] internals
beyond the summarized seams (multipart builder, placeholder guards — no leaf
bullet touches them) and the debug-toolbar upstream source (external
precedent, not a package site).
- **Rejection.** Contract difference: bounded leaf-audience summaries (what +
where + see-ref, moving only when the export set or one-line shape changes)
vs owner mechanics (signatures, predicates, pins, remediation text, moving on
mechanics changes) — C9/C10 prove opposite move sets with zero leaf
definitions under every mechanics change. Trigger to reconsider: a bullet
starts restating mechanics (a signature, a predicate, a pin, remediation
steps) instead of pointing → shrink that bullet to a pointer (a projection
consolidation, never a definition change). Durable home: the owner
docstrings (already the full contract) + this artifact; no new prose owed.
Named for Worker 0 as rejected index row
`testing-leaf-bullet-summaries-vs-owner-contracts` (no such row exists in the
current plan).

## Defects

None. Every docstring claim checked held: the 7/7 bindings (verified against
both home modules' definition sites + `client.__all__`), the endpoint sentence
(default + both override seams verified at [conf][conf] and
[testing-client][testing-client]`::TestClient.__init__` + `query(url=)`), the
`Response` lineage + raw-carriage clause, the mixin delegation + helper names,
the wrap bullet (decline semantics + toolbar mirror + backstop pointer, all
three verified at [testing-wrap][testing-wrap] + [django-patches][django-patches]),
and the withholding bullet (absence + dotted path verified by probe + census;
the import-light rationale is observation O1 below, mechanics verified). The
axis-6 sweep finds no missing guard: all required members present, all three
omissions carry contract sources, the `__test__` question ends at its two
owners (C15). Two observations, neither a defect (each breaks no contract
row): O1 — the import-light rationale clause overstates at HEAD (root pays
`types` imports regardless; the load-bearing absence + zero-marginal-cost
pair holds — F2 Distinct behavior); O2 — the export-surface oracle pins 6/7
present with no exact-set pin and no withholding pin (gate-absence under the
principle-9 economy, with the standing-ins named — F1/F2 gate sections).

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding, the binding/absence facts are execution-verified
by the quoted read-only import probes (no workspace run owed — nothing
mutated), and the oracle bodies were read at both revisions. Sharded /
Postgres cells are inapplicable by construction: the target reaches no
database, alias, or dialect decision.

## Judgment

Zero-edit file item. Three rules traced: two file-local with proving
challenges (F1 manifest, C1–C5; F2 withholding, C6–C8), one rejected with its
contract difference + trigger (F3 bullet summaries, C9–C10). Two lawful
convergences transcribed as nested rejections (F1→leaf-vs-root direction,
F2→hints-R4). Five indexed families checked with no surface (C11–C15; the
only row naming this subsystem covers `testing/client.py`, not this leaf).
Enumeration covers 4/4 statements and 8/8 bound names. No defects, no pending
execution, no production edits.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs `ITEM_BASELINE=b98363030b383440e190e0ea71be306d8ad5f02d`:
`git diff <baseline> -- django_strawberry_framework/testing/__init__.py` is
empty and the working blob `48b45d1b433283c40bf8d602d71a26d261a833b2` equals
`HEAD:django_strawberry_framework/testing/__init__.py` at HEAD `0c0537e2` —
target CLEAN, so no hunk attribution was owed. The artifact itself is a new
untracked file, the item's only output. The `## Owned changes` ledger gains
no row from this item. Concurrent dirt (hunt edits across
`django_strawberry_framework/`, `tests/testing/*`, `docs/README.md`,
`docs/dry/dry-0_0_15.md`) left untouched. No `uv run ruff` run (no `.py`
touched; `.md` is outside ruff format scope; no `.py` scratch created). No
shared-tree pytest run (inspection + read-only import probes suffice — see
`### Challenges` note; the entry command authorizes a focused `--no-cov` run
only where it could settle a judgment, and here it could settle nothing). No
workspace runs (nothing source-mutating was needed). No
`docs/dry/temp-tests/` scratch created. No commit.

Artifact-name note for Worker-0: this file was created at the dispatched
path `docs/dry/dry-file-testing__init__.md`, which differs from the plan
link `dry-file-testing____init__.md` and from the DRY.md (`/`→`__`, `.py`
dropped) + all-eleven-precedent spelling. Re-key (rename + plan-link touch)
is Worker-0's call — content is unaffected either way.

Worker-0 instructions: (a) tick the plan item `File testing/__init__.py`
as verified under Run `0.0.15 2026-09-28-7` once Worker 2 agrees; (b) add
the five `## Responsibility index` rows under `## Index rows for Worker-0`
verbatim (holding item `File testing/__init__.py`); (c) add the
`## Families` items under `## Families` (none). No commit.

## Index rows for Worker-0

| `testing-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/testing/__init__.py`) | `django_strawberry_framework/testing/__init__.py` (+2 owner modules) | File `testing/__init__.py` | file-local |
| `testing-relay-withholding` | `django_strawberry_framework/testing/__init__.py` (enforced by omission; dotted `testing.relay` path is public) | `django_strawberry_framework/testing/__init__.py` (+1 withheld module) | File `testing/__init__.py` | file-local |
| `testing-leaf-vs-root-manifest` | `django_strawberry_framework/testing/__init__.py` (rejection recorded here; CONVERGE with verified orders/filters/rest-framework leaf-vs-root direction on fresh evidence; durable home spec-043 Decision 4 + leaf docstring) | `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/__init__.py` | File `testing/__init__.py` | rejected |
| `testing-relay-withholding-prose-pair` | `django_strawberry_framework/testing/__init__.py` (rejection recorded here; CONVERGE with verified hints-R4 bilateral-import-rationale-prose on fresh evidence; durable home spec-043 Decision 4) | `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/testing/relay.py` | File `testing/__init__.py` | rejected |
| `testing-leaf-bullet-summaries-vs-owner-contracts` | `django_strawberry_framework/testing/__init__.py` (rejection recorded here; owner mechanics at `testing/client.py`, `testing/_wrap.py`, `_django_patches.py`, `conf.py`) | `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/conf.py` | File `testing/__init__.py` | rejected |

## Families

None. No new family named, no adoption into an open family (all five
considered families checked with no surface at this leaf, C11–C15). The
holding items for the composed definitions are the undispatched file items
`testing/_wrap.py`, `testing/client.py`, `testing/relay.py`.

## Independent verification (Worker-2)

Address `dry/dry-file-testing__init__/verify-1`. Fresh context; expectation-first:
I traced the target, every connected site, and both revisions before reconciling
with `## Findings` below. Verdict: `verified` (zero-edit file item; no defects;
no pending execution). HEAD `0c0537e2` unmoved throughout; target CLEAN at
`48b45d1b433283c40bf8d602d71a26d261a833b2` (worktree == HEAD).

### Own trace (recorded before opening Findings)

Target read in full (64 lines): a leaf manifest — module docstring (5 contract
bullets), 2 re-export statements (1 name from `_wrap.py`, 6 from `client.py`),
`__all__` mirroring the 7. No `def`/`class`/`await`/`raise`/guard/bus-row/shim
(full-read + token grep: `warnings`, `deprecated`, `sync_to_async`,
`__getattr__`, `register_subsystem_clear`, `require_`, `async ` all 0). Roles I
chose: statements 2–4 = consumer rows composing by name (homes: the per-symbol
owner modules); the relay withholding = the one rule DEFINED here, by omission
of any `relay` import; docstring bullets = projections of owner mechanics.
Connected reads: [testing-client][testing-client] (judged regions: 6 class
sites, `__all__`, `__test__` guard at `::TestClient`, endpoint ladder,
`::GraphQLTestMixin.query` delegation line), [testing-wrap][testing-wrap]
(full), [testing-relay][testing-relay] (docstring, `__all__`, def
name/signature), [django-patches][django-patches] (framing docstring +
`::_is_database_failure` body), [conf][conf] (`TESTING_ENDPOINT_KEY` block +
`::testing_endpoint_setting` + `__test__` guard), [pkg-root][pkg-root] (grep-0
for `testing`/`TestClient`), [filters-init][filters-init] +
[rest-init][rest-init] (full), oracles [test-client][test-client] (both bodies),
[test-relay][test-relay] (import block + decode-identity assertion),
[test-wrap][test-wrap] (import block), [spec-043][spec-043] Decision 4 (full
passage) + [spec-032][spec-032] Decision 10 + DoD + exports-list note (all read,
all present as cited), consumer censuses (unanchored whole-tree greps),
[docs-readme][docs-readme] (line 244 + usage block), [glossary][glossary]
(family entries), [fakeshop-readme][fakeshop-readme] (import block).

Counts I reached independently: 4/4 `ast.Module.body` statements, 8/8 bound
names, every member homed (stmt 1 → projections; stmts 2–4 → R1 consumer rows;
the stmt-2/3 omission → R2 defined-here); challenge counts C1–C3 → 1,
C4 → 0, C5 → 1 at client, C6 → 1 here, C7 → 0 here, C8 → 1, C9/C10 → 0 here,
C11–C15 → 0 here. Homes I chose: F1 per-symbol home modules (file-local row),
F2 this file by omission (file-local row), F3 rejected (0 leaf definitions
under every mechanics change). Reconciliation: zero differences — every W1
home, count, and role matches my trace (census footnotes N1/N2 below refine
counts that strengthen, not move, the conclusions).

### Per-area verdicts

- Enumeration: AGREE (4/4 + 8/8 member-by-member; `ast.parse` re-run).
- Matrix: AGREE all 6 axes (1 searched incl. root grep-0 re-run; 2
  inapplicable with correct reason; 3 searched; 4 no-surface with correct
  reason; 5 four media classified; 6 three omissions each with a contract
  source + absence probed fresh).
- Convergences: AGREE both on fresh evidence. F1-nested: prior
  `orders-leaf-vs-root-manifest` direction re-read in its artifact; this
  leaf's Decision-4 difference re-derived from the full passage; trigger
  re-checked (root grep-0 at current bytes; no shared manifest driver) —
  unfired. F2-nested: hints-R4 re-read (rejected; trigger = divergent
  invariants); fresh check at current bytes — passages agree, neither carries
  the other's audience rule (leaf bullet is a see-ref pointer; relay passage
  names the non-path, not the leaf's export set) — unfired.
- Rejections: AGREE all 3 (F3 + 2 nested): each carries contract difference +
  trigger + durable home; every F3 bullet re-verified sentence-by-sentence
  against its owner body (`conf.py` default return, `client.py::Response` /
  delegation / helper names, `_wrap.py` decline + toolbar mirror, patch
  framing).
- O1: AGREE (non-defect observation correct). Fresh probe: `types.base` IS in
  `sys.modules` after bare root import (rationale loose) AND the load-bearing
  pair holds (`testing.relay` absent after both imports; marginal leaf cost =
  leaf + 2 homes + their declared deps only, no relay, no new `types`). Breaks
  no contract row (absence + dotted path + gate all verified) → not a defect
  per the AGENTS.md defect rule. Fresh ground: the clause is inherited
  verbatim from Decision 4's own passage, so "fixing" the bullet would
  contradict the spec.
- O2: AGREE (no-exact-set-pin correct under principle 9). No contract row
  requires a pin (Decision 4's presence-6 + root-absence are both oracled);
  named-leaves standing verified (no exact-set pins for the filters/orders/
  auth/extensions leaf manifests — those `__all__` hits are the lookup token;
  the existing exact-set pins elsewhere each carry their own justification);
  standing-ins real (explicit-name consumers fail loudly; gap stated honestly).
- Index rows: AGREE 5/5 match their findings; no Families items owed (C11–C15
  correctly route nothing here).
- Freshness: AGREE (all 17 fingerprints digit-for-digit at W1's bytes; all 7
  dirtied inputs' hunks confirmed outside judged regions — both oracle bodies
  byte-identical via AST extraction; see concurrent-work note).
- Pending execution: AGREE (None correct; sharded/PG inapplicable by
  construction — no DB/alias/dialect surface).
- Zero-edit: confirmed (target CLEAN; item authored only this untracked
  artifact; no `## Owned changes` row owed).
- AGENTS.md prose rules: PASS (no process provenance/banned tokens;
  `path::Symbol` citations; no tests owed; link scaffold = all 10 canonical
  headers; single artifact at the plan-link spelling, sha256 `01eec662…`
  matching Worker-0's record). Ruff: no `.py` touched — confirmed instead of
  run; my probes wrote only outside the repo.

Fresh execution (read-only probes, via workspace at my address): run
`dry-20260928T211007-404cbe` (O1a True; F2a/F2c absent; F2b False; F1a True;
F1b exactly the 7; F1c False; F1d 7 vs 6) and run `dry-20260928T211023-27bdc8`
(marginal `import testing` cost = exactly 6 modules: leaf + 2 homes +
`_django_patches` + `strawberry.test` × 2).

### Window attribution (vs `ITEM_BASELINE=b9836303…`)

8 tracked paths, all concurrent/out-of-scope, none item-authored (the item
touched zero tracked paths): the plan (Worker-0's dispatch records — not
touched); 4 review-flow paths (`docs/review/review-0_0_15.md`,
`rev-utils__strings.md`, `.comments.md`, `.performance.md`); plus 3 from a
concurrent hunt wave that landed mid-verification
(`django_strawberry_framework/_django_patches.py`,
`tests/test_django_patches.py`, `tests/testing/test_wrap.py` — prose/body
dirt outside every judged region; the last file is not a fingerprinted input).
Two worktree fingerprints moved in that wave (`_django_patches`
`63f3fa9c…` → `6918a213…`, `test_wrap` `4d3c1351…` → `6818d96b…`); I
re-verified both judged regions byte-intact at current bytes (predicate body
identical, import block identical). Worker-0 may note the refreshed hashes; no
finding reopens.

### Immaterial record notes (move no home/count/gate)

- N1: dotted-relay census reads "9 (5 tests + 4 live)" but both revisions show
  10 `testing.relay import` statements (6 under `tests/`, incl. the
  function-local import at `tests/filters/test_sets.py:2939`, + 4 live-tier)
  plus the `from testing import relay` submodule line. F2 strengthens with the
  correction.
- N2: root-import census "24 sites plus the docstring example" counts the
  fakeshop README code block as a site; resolving code sites are 23 + README
  projection + docstring example. No-second-manifest conclusion unaffected.
- N3: `test_client.py` dirt "70 changed lines" vs stat 68 (5+/63-). The
  load-bearing claims (grep-0 over oracle ids, byte-identical oracle bodies)
  verified true.

No defects filed (no `(Worker-2)` entries owed — O1/O2 are correctly
observations, and the notes above are record accuracy, not candidates).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-043]: ../SPECS/spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[django-patches]: ../../django_strawberry_framework/_django_patches.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[rest-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[testing-wrap]: ../../django_strawberry_framework/testing/_wrap.py

<!-- tests/ -->
[test-client]: ../../tests/testing/test_client.py
[test-relay]: ../../tests/testing/test_relay.py
[test-wrap]: ../../tests/testing/test_wrap.py

<!-- examples/ -->
[fakeshop-readme]: ../../examples/fakeshop/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
