# DRY review: `utils/typing.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits, zero plan edits.

## System trace

Target [utils-typing][utils-typing] at HEAD blob
`de6309f6cb5915e9f42d0e19f564f4e67226e334` (280 lines). The worktree blob is
`a672cd6b4f5cf6c207bd4f65eb080acd971a6b98` (280 lines, 2 hunks, 10+/10-).
No `## Owned changes` row names this file, so the dirt entered as
concurrent-external until content attribution proved otherwise — and it did:

| Hunk (HEAD lines) | Content | Attribution |
|---|---|---|
| import block (`:27-28`) | adds `from . import truth` | external: imports `utils/truth.py`, untracked at HEAD |
| `is_async_callable` tail (`:150-162`) | class/instance `getattr(…, "__call__")` pair → single `truth.static_attr(type(target), "__call__")` | external: same migration, same untracked import |

Both hunks are the hunt's truthful-reads migration: `utils/truth.py` does
not exist in the HEAD tree (`git ls-tree HEAD` has no such entry; worktree
status `??`, alongside untracked `utils/lazy.py`). Nothing in either hunk
is ledger-owned, and nothing is mine — I made no edits. Mechanics agree:
`ITEM_BASELINE=d573e9f3…` already carries target blob `a672cd6b`, so the
dirt predates the item. This artifact therefore traces HEAD bytes
exclusively, read via `git show HEAD:…`; worktree bytes were used only to
fingerprint the dirt above. Nothing tracked was touched.

What the target owns: the package's declared-shape interrogation seam —
two Strawberry-private schema digs, the two-shape config ladder, the one
wrapper-depth ceiling, the callable-wrapper peel, the partial-aware async
predicate, and four type peels with four different stop rules. Production
callers at HEAD, all composing by name: `is_async_callable` from 3 call
sites in 3 files; `unwrap_return_type` from 1; `unwrap_graphql_type` from 2
sites in 1 file; `unwrap_non_null` from 3 sites in 1 file;
`unwrap_container_type` from 1; `strawberry_schema_from_schema` /
`strawberry_schema_from_info` from 1 file; `schema_config_from_info` from 3
sites in 3 files (census under Matrix).

Connected behavior examined (all at HEAD, fingerprints in Findings):
[connection][connection] `4894f90f` (async dispatch + edge-class consumers),
[list-field][list-field] `21380eb7` (async-dispatch consumer),
[mutations-sets][mutations-sets] `7800bd53` (shape lock + GlobalID-core
consumer), [mutations-fields][mutations-fields] `d4edcbb7` (asymmetry
projection), [types-base][types-base] `dda91365` (encoder-gate consumer),
[types-relay][types-relay] `52439862` (`__func__` identity tests),
[types-resolvers][types-resolvers] `72d62dc4` (awaitable value checks),
[extension][extension] `e0e53a8e` (schema-dig + full-peel consumer),
[selections][selections] `a48f6172` + [walker][walker] `75f9c6b6` (config
consumers), [utils-connections][utils-connections] `f549389e` (config
consumer), [utils-init][utils-init] `1a4c2ec8` (pinned 2-of-9 re-export),
[querysets][querysets] `3616927d` (value route + adapter name-twin),
[execution-mode][execution-mode] `9805cdaf` (executor fact),
[resource-policy][resource-policy] `19e2309d` (NonNull consumer +
`get_named_type` contrast), [debug][debug] `bf25c146` (recorded ceiling
separation), [request-body][request-body] `e6e32e78` (asgiref capability),
[inspect][inspect] `2807d0fc` (renderers + Union reads),
[auth-mutations][auth-mutations] `d1a59c44` (awaitable value checks), HEAD
[test-typing][test-typing] `70a257a1` (480 lines, oracle census) and HEAD
[test-init][test-init] `8d340656` (re-export identity pins). Prior file
artifacts touching this surface (`utils/execution_mode.py`,
`utils/connections.py`, `utils/__init__.py`, `optimizer/extension.py`,
`types/base.py`, `extensions/resource_policy.py`) were used only as
rejected-candidate triggers to check, per [DRY.md][dry].

## Verification

### Matrix

Each axis discharged against the target's real surface (`git grep` at HEAD
unless noted; line numbers are HEAD).

1. **Cross-flavor policy mirroring.** The target IS a cross-flavor seam:
read fields, write flavors, the optimizer, and the type system. Census
(production call sites): `is_async_callable` —
[connection][connection] `:2035`, [list-field][list-field] `:1696`,
[types-base][types-base] `:451`; `unwrap_return_type` —
[mutations-sets][mutations-sets] `:1608`; `unwrap_graphql_type` —
[extension][extension] `:742/:829`; `unwrap_non_null` —
[resource-policy][resource-policy] `:501/:976/:1002`;
`unwrap_container_type` — [connection][connection] `:283`;
`strawberry_schema_from_schema` — [extension][extension] `:737`;
`strawberry_schema_from_info` — [extension][extension] `:833` (+ internal
`:76`); `schema_config_from_info` — [selections][selections] `:562`,
[walker][walker] `:243`, [utils-connections][utils-connections] `:731`;
`_callable_inspection_target` — in-file only (+ oracle). Every site
composes by call; what differs per flavor is the surrounding pipeline,
never the peel or predicate body. Discharged: no mirrored policy body.

2. **Sync/async twins.** The target's async surface is one pure
declared-shape predicate (no `await`, no I/O, no executor color); no twin
owed by construction. The neighbors classify different things and are
rejected with contract differences: value-at-resolve-time
(`is_async_only_iterable`, `reject_async_iterable_in_sync_context`,
`isawaitable` sites — R4), executor-fact-at-operation-time
(`operation_is_async`/`async_execution` — R5, already held), ASGI
capability at middleware construction (asgiref `iscoroutinefunction` —
R5). Discharged: one predicate per question, each owned once.

3. **Derived rather than repeated knowledge.** Each neighboring derivation
was censused and either composes or is rejected with a trigger: the
`_strawberry_schema` literal is spelled exactly twice (`:49`, `:60`),
both in-file (R7); no raw `info.schema.config` dig exists in production
(the `.config` production reads are this module's own `:76/:78` plus
the one-line [inspect][inspect] `:138` consumer, which takes a schema
object or `None` with a default-converter fallback — no ladder, a
different input, no second definition, no new row);
`.func` unwrapping exists only at `:109`; HEAD `__func__` sites are
classmethod-identity compares, never descents (R10);
`get_origin`/`get_args` neighbors answer Union/Optional
([inspect][inspect] `:461-462/:627-634`), depth
([mutations-sets][mutations-sets] `:1581`, R2), and Annotated
([types-base][types-base] `:496-497`) questions — none peels an inner
type; `get_named_type` is upstream's own graphql-core-only peel (R1);
`unwrap_async_queryset_adapter` is an adapter unwrap, not a type peel
(R9). Discharged: one derivation per fact, consumers by name.

4. **Inverse / round-trip pairs.** No encode/decode pair: the four peels
are one-way descents with four different stop rules, co-sited in this
module (R6); the config ladder (wrapped-then-direct) is a preference, not
a round trip; FL1/FL2 are two entries to one dig, co-sited (R7).
Discharged: pairs co-sited, never split across modules.

5. **Contracts restated in another medium.** Production: the target.
Oracles (all literal, none reading an owner table): HEAD
[test-typing][test-typing] — 27 tests pinning every rule (one-layer
shapes incl. bare-list→`Any`, full-peel depth + cyclic refusal,
container gate + cyclic refusal, NonNull-only + cyclic refusal,
wrapper-table async pins, metaclass pins, cyclic-callable refusal,
exact-depth acceptance ×3, schema/config shape pins incl. the
explicit-`None` fallthrough); HEAD [test-init][test-init] pins the
2-of-9 re-export by identity. The oracle module docstring states
wrapper-peeling has no selection-set spelling and wire color lives in
`test_list_field_async_api.py`; no live-tier pin names these helpers
(the one `test_query` hit is a comment). Projections: module + 10
per-symbol docstrings, the [utils-init][utils-init] bullets, the TREE.md
line, owner-citing consumer comments (connection, list-field,
mutations-sets, mutations-fields, types-base, utils-connections), the
GLOSSARY `is_async_callable` pair (`:670`, `:724`), CHANGELOG history
(`:236`, `:280`), and archived spec rationale (history, not contract).
Discharged: media classified, oracles independent.

6. **Enforcement by omission.** `is_async_callable`'s family is exactly
{connection, list-field, types-base validator}: [mutations-fields][mutations-fields]
and [relay][types-relay]'s node fields have no consumer-`resolver=` seam
(documented absence — package-owned resolvers dispatch on runtime
`async_execution()` — not a gap); `_callable_inspection_target` is
reachable only through `is_async_callable` (whole-repo census); all three
config readers compose FL3; all four in-file peels honor the FL4 ceiling
(the [debug][debug] local 64 is a recorded separation, R8). Discharged:
no gap.

### Enumeration

Instrument: `ast.Module.body` over HEAD bytes — 15 statements: module
docstring, 3 imports, `__all__`, 9 function defs, 1 ceiling assign.
Every member is homed below.

| # | Member | Home |
|---|---|---|
| 0 | module docstring | FL0 (rule-map projection) |
| 1 | `import functools` | FL0 (partial machinery for FL5) |
| 2 | `import inspect` | FL0 (coroutine reads for FL6) |
| 3 | `from typing import Any, get_args, get_origin` | FL0 (list-shape reads for FL10) |
| 4 | `__all__` (exact 9) | FL0 |
| 5 | `strawberry_schema_from_schema` | FL1 (literal half of R7) |
| 6 | `strawberry_schema_from_info` | FL2 (literal half of R7) |
| 7 | `schema_config_from_info` | FL3 |
| 8 | `MAX_TYPE_WRAPPER_DEPTH = 64` | FL4 |
| 9 | `_callable_inspection_target` | FL5 |
| 10 | `is_async_callable` | FL6 |
| 11 | `unwrap_graphql_type` | FL7 (stop-rule quarter of R6) |
| 12 | `unwrap_non_null` | FL8 (stop-rule quarter of R6) |
| 13 | `unwrap_container_type` | FL9 (stop-rule quarter of R6) |
| 14 | `unwrap_return_type` | FL10 (stop-rule quarter of R6) |

15/15 homed. No member routes to a family: the executor-fact sameness
sight is already held by verified
`execution-mode-fact-vs-shape-classification` (R5), the ceiling sight by
the owner-recorded [debug][debug] separation (R8).

### Challenges

Counts are authoritative definitions forced per posited change; consumers,
oracles, and projections that also move are listed, never counted.

- **C1 — Strawberry renames the private attr.** `:49` plus `:60` move
together — 2 spellings, 1 file; extraction refused (R7). Consumers 0;
schema-shape oracles move.
- **C2 — a third config shape.** The FL3 ladder (`:73-79`) alone —
count 1. Consumers 0; config oracles move.
- **C3 — ceiling value or failure policy changes.** `:88` plus the 4
loop ranges — 1 file (FL4; the debug merge refused, R8). Consumers 0;
exact-depth + cyclic oracles move.
- **C4 — a new callable wrapper shape.** The FL5 peel (`:106-109`) plus
the FL6 docstring — count 1. Consumers 0; wrapper-table oracles move.
- **C5 — async-generator becomes async.** The FL6 body (`:147-162`) —
count 1; the value route stands (different contract, R4). Consumers move
by behavior (connection/list dispatch arms), listed not counted;
async-generator oracles move.
- **C6 — the metaclass rule is dropped.** `:150-157` — count 1.
Consumers 0; metaclass oracles move.
- **C7 — the full peel must stop at lists.** FL7 alone — count 1
(callers needing lists already use FL8; R6). Consumers 0 by edit
(extension sites keep calling); extension oracles move.
- **C8 — NonNull classification needs lists too.** 0 here: the 3
[resource-policy][resource-policy] sites switch to FL7 — proves the
separation (R6). Policy oracles move.
- **C9 — the container gate is dropped.** FL9 alone — count 1; the
leaf-with-`of_type` oracle FAILS, proving the gate (R6). Consumers 0.
- **C10 — the one-layer peel becomes a full peel.** FL10 alone —
count 1; the R2 depth read is unaffected, proving the separation.
Consumers 0; M2M-shape oracles move.
- **C11 — the bare-list sentinel changes.** `:278-279` — count 1.
Consumers 0; bare-list oracles move.
- **C12 — a tenth export is added.** `__all__` here — count 1; the
[utils-init][utils-init] pinned set is a separate decision (it carries 2
of 9 today). Consumers 0.

## Findings

### FL0 — `typing-module-mechanics` (file-local)

- **Contract + variation.** The leaf's mechanics: a rule-map docstring
naming both contracts (unwrap loops, async predicate, private digs),
stdlib-only imports (`functools`, `inspect`, `typing`), and an exact-9
`__all__` with zero star-importers (whole-package census). Varies on the
export set only (C12).
- **Sites + roles.** Definition: the target (`:0-39`). Consumers: every
importer reads the submodule by name; [utils-init][utils-init] re-exports
2 of 9 (verified file-local there). Oracles: `__all__` membership is
pinned transitively by the oracle import block plus [test-init][test-init]
identity pins. Projections: the docstring, the TREE.md line.
- **Challenges.** C12 count 1.
- **Owner + lifetime.** The target (principle 7 — every consumer already
depends on `utils`). No stored derivation.
- **Freshness.** Target as header; [utils-init][utils-init] `1a4c2ec8`,
[test-init][test-init] `8d340656`.

### FL1 — `typing-schema-unwrap-or-self` (file-local)

- **Contract + variation.** Unwrap a Strawberry `Schema` to its inner
schema; return the input when already unwrapped (test fixtures pass the
inner schema directly). Varies on the private attr name (C1, shared half
with FL2).
- **Sites + roles.** Definition: `strawberry_schema_from_schema`
(`:42-50`). Consumers: [extension][extension] `:737` by call. Oracles:
shape pins (wrapped + bare). Projections: the docstring's fallback
clause.
- **Challenges.** C1 count 2 spellings, 1 file.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [extension][extension] `e0e53a8e`.

### FL2 — `typing-info-schema-walk` (file-local)

- **Contract + variation.** Walk `info.schema._strawberry_schema`;
`None` when any step is missing ("no schema available, nothing to look
up"). Varies on the private attr name (C1, shared half with FL1).
- **Sites + roles.** Definition: `strawberry_schema_from_info`
(`:53-60`). Consumers: [extension][extension] `:833` + FL3 (`:76`) by
call. Oracles: shape pins. Projections: the docstring's `None` clause.
- **Challenges.** C1 count 2 spellings, 1 file.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [extension][extension] `e0e53a8e`.

### FL3 — `typing-config-preference-ladder` (file-local)

- **Contract + variation.** `StrawberryConfig` from plan-time
graphql-core or resolve-time `Info`: wrapped
(`info.schema._strawberry_schema.config`) first, direct
(`info.schema.config`) second, `None` when neither carries one; callers
decide what `None` means. Varies on the shape ladder (C2).
- **Sites + roles.** Definition: `schema_config_from_info` (`:63-79`).
Consumers (3, all by call): [selections][selections] `:562`,
[walker][walker] `:243`, [utils-connections][utils-connections] `:731`.
Oracles: preference + explicit-`None`-fallthrough pins. Projections: the
docstring's caller-decides clause, the
[utils-connections][utils-connections] `:720-724` neither-dereferences
note.
- **Challenges.** C2 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; `a48f6172`, `75f9c6b6`, `f549389e`.

### FL4 — `typing-wrapper-depth-ceiling` (file-local)

- **Contract + variation.** One ceiling (64) over every wrapper peel in
the module — type stacks and callable stacks alike — with a loud
`RuntimeError` past it (cyclic/corrupt is the only way past). Varies on
the value and the failure policy (C3).
- **Sites + roles.** Definition: the `:88` assign + the 4 loop ranges
(`:106`, `:183`, `:209`, `:237`) with their 4 messages. Consumers: the 4
in-file peels. Oracles: exact-depth acceptance ×3, cyclic refusal ×4.
Projections: the NASA Power-of-Ten comment block.
- **Challenges.** C3 count 1 file.
- **Owner + lifetime.** The target. No stored derivation.
- **Freshness.** Target as header.

### FL5 — `typing-callable-inspection-peel` (file-local)

- **Contract + variation.** Peel `partial`/`staticmethod` layers to the
callable inspection target, bounded by FL4: `partial` flattens at
construction but a staticmethod descriptor can contain a partial, so both
kinds peel until the target. Varies on the wrapper kinds (C4).
- **Sites + roles.** Definition: `_callable_inspection_target`
(`:91-113`). Consumers: FL6 (`:147`) + the oracle's depth pins, only
(whole-repo census). Oracles: exact-depth acceptance, cyclic partial +
cyclic staticmethod refusal. Projections: the docstring's flattening
note.
- **Challenges.** C4 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header.

### FL6 — `typing-partial-aware-async-predicate` (file-local)

- **Contract + variation.** Whether calling `value` yields a coroutine:
direct coroutine function, or async `__call__` read on the class (so
instances, metaclass-carried classes, partials, and raw staticmethod
descriptors all classify); a plain class stays sync; an `async def` that
`yield`s is intentionally False (async-generator returns classify by
value at resolve time, never by declared shape). Varies on the shape
table (C4–C6).
- **Sites + roles.** Definition: `is_async_callable` (`:116-162`).
Consumers (3 call sites): [connection][connection] `:2035`,
[list-field][list-field] `:1696`, [types-base][types-base] `:451`.
Oracles: wrapper-table pins, metaclass pins (async-meta True,
class-body-`__call__` False), cyclic refusal. Projections: the 4-shape
docstring, the factory asymmetry comments, GLOSSARY `:670/:724`.
- **Challenges.** C4 + C5 + C6 count 1.
- **Owner + lifetime.** The target (principle 7 — read, write, and
validator consumers all already depend on `utils`). Pure derivation,
never stored.
- **Freshness.** Target as header; `4894f90f`, `21380eb7`, `dda91365`.

### FL7 — `typing-full-oftype-peel` (file-local)

- **Contract + variation.** Peel ALL `of_type` layers (graphql-core or
Strawberry), bounded by FL4; pass through `None` and non-wrappers
untouched. Varies on the stop rule (C7; the list-keeping quarter is FL8).
- **Sites + roles.** Definition: `unwrap_graphql_type` (`:165-190`).
Consumers: [extension][extension] `:742/:829` by call (the `:819`
"recursively peels" prose describes the delegated effect; the body
composes). Oracles: full-peel, deep-finite, cyclic-refusal, `None`
passthrough, exact-depth pins.
- **Challenges.** C7 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [extension][extension] `e0e53a8e`.

### FL8 — `typing-non-null-only-peel` (file-local)

- **Contract + variation.** Peel ONLY `GraphQLNonNull` layers, bounded;
leave `GraphQLList` in place for the callers that must still see it
(list-vs-connection classification answers wrong on a full peel).
Varies on the stop rule (C8).
- **Sites + roles.** Definition: `unwrap_non_null` (`:193-216`).
Consumers (3, all by call): [resource-policy][resource-policy]
`:501/:976/:1002`; the single-step `.of_type` reads beside them
(`:528/:536/:651/:657/:1005`) descend from the peeled result, they do
not re-peel. Oracles: NonNull-only + cyclic-refusal pins.
- **Challenges.** C8 count 0 here (proves the FL7 separation).
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [resource-policy][resource-policy]
`19e2309d`.

### FL9 — `typing-container-only-peel` (file-local)

- **Contract + variation.** Peel `StrawberryContainer` layers only,
bounded; the `isinstance` gate is load-bearing — a concrete leaf that
happens to expose `of_type` must NOT peel (the bare-`hasattr` contract
would descend into it). Function-local import keeps the module
stdlib-only at import time. Varies on the gate (C9).
- **Sites + roles.** Definition: `unwrap_container_type` (`:219-244`).
Consumers: [connection][connection] `:283` by call. Oracles:
container-peel + leaf-with-`of_type` refusal + cyclic-refusal +
exact-depth pins.
- **Challenges.** C9 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [connection][connection] `4894f90f`.

### FL10 — `typing-one-layer-return-peel` (file-local)

- **Contract + variation.** Unwrap ONE list layer: `of_type` first (so a
wrapper that also presents a list-like origin yields its declared inner
type), then `list[T]` → `T`, bare `list`/`typing.List` → `Any` (unknown
element sentinel), else identity. Varies on the layer count and the
sentinel (C10–C11).
- **Sites + roles.** Definition: `unwrap_return_type` (`:247-280`).
Consumers: [mutations-sets][mutations-sets] `:1608` by call. Oracles:
one-layer shapes incl. `list[list[int]]` → `list[int]`, bare-list
sentinels, `None`-inner preservation, direct-class identity.
Projections: the ordering-rationale docstring paragraph.
- **Challenges.** C10 + C11 count 1.
- **Owner + lifetime.** The target. Pure derivation, never stored.
- **Freshness.** Target as header; [mutations-sets][mutations-sets]
`7800bd53`.

### R1 — `typing-full-peel-vs-upstream-get-named-type` (rejected, fresh)

[resource-policy][resource-policy] uses graphql-core's own
`get_named_type` at `:710/:788/:979/:1005/:1256`. Same answer on a
well-formed graphql-core stack, different rule: upstream peels only
`GraphQLList`/`GraphQLNonNull` instances, unbounded, with no `None`
shape; FL7 peels ANY `of_type` (Strawberry wrappers included), passes
`None` through, and fails loud past FL4. Substituting FL7 into those
sites changes the failure policy (silent unbounded → loud bounded) on a
request path; substituting upstream into FL7's callers drops the
Strawberry tolerance the optimizer needs. Upstream owns its primitive;
this module owns the bounded Strawberry-tolerant peel. Durable home: this
row. Trigger: FL7 narrowing to graphql-core-only AND upstream bounding,
or a policy site needing Strawberry-tolerant peeling. Freshness: target
as header; `19e2309d`.

### R2 — `typing-peel-vs-shape-lock` (rejected, fresh)

[mutations-sets][mutations-sets]`::_strawberry_field_shape` (`:1612-1632`)
peels `of_type` counting `StrawberryList` depth and cycle-guards with a
silent-stop `seen` id-set; the adjacent `:1581` read (`get_origin(…)
is list`) answers depth, never inner type. Three contract differences
from FL7/FL10: it returns `(depth, core)` where the peels return a core;
it counts only Strawberry lists where FL7 peels everything; its cycle
policy is silent-stop where FL4 is loud. Folding the lock into FL7 loses
depth; routing it through FL10 loses the multi-layer count; loud cycles
at the bind change diagnostics. Durable home: this row. Trigger: the
lock needing loud cycles, or a second depth-counting peel. Freshness:
target as header; `7800bd53`.

### R3 — `typing-peel-vs-render` (rejected, fresh)

[inspect][inspect]`::_render_strawberry_type` (`:488-500`) and
`_render_annotation` (`:627-634`) descend wrappers to RENDER GraphQL
nullability/scalar strings; the descent is incidental to the render, and
no peeled core escapes as a value. Calling FL7 inside the render would
still need the per-layer nullability walk — the peel answers a question
the render never asks. Durable home: this row. Trigger: a render needing
the peeled core as a value (then it composes FL7 by call — composition,
not a merge). Freshness: target as header; `2807d0fc`.

### R4 — `typing-async-shape-vs-value-route` (rejected, fresh)

Declared-shape-at-construction (FL6) vs value-at-resolve-time:
[querysets][querysets]`::is_async_only_iterable` (`:377-390`),
`reject_async_iterable_in_sync_context`, and the `isawaitable` checks
([querysets][querysets] `:188/:213/:3127/:3160`,
[types-resolvers][types-resolvers] `:629/:705/:778`,
[auth-mutations][auth-mutations] `:505/:509`,
[extension][extension] `:1124`) classify what a resolver RETURNED, on a
path where FL6 already answered. The split is deliberate and recorded:
`d4c07d7d` deleted `is_async_generator_callable` from this module so
async-only sources classify by value at one seam, and the FL6 docstring
pins async-generator False on exactly that basis. Unifying the two means
either predicting returns from declarations (impossible) or deferring
factory dispatch to resolve time (Strawberry freezes handling at schema
build). Durable home: the FL6 docstring + this row. Trigger: a
construction-time need to see async-generators again. Freshness: target
as header; `3616927d`, `72d62dc4`, `d1a59c44`, `e0e53a8e`.

### R5 — executor fact vs shape classification (CONVERGE, row stands)

Verified `execution-mode-fact-vs-shape-classification` re-checked at
HEAD: `operation_is_async`/`async_execution` still answer which executor
*is driving* (operation time) while FL6 answers what a callable *is*
(construction/selection time); [request-body][request-body]'s asgiref
`iscoroutinefunction` still answers ASGI middleware capability at
construction. Bodies re-read, trigger ("a shape check used to branch a
resolver return at runtime") unfired — connection/list-field commit
wrappers at construction, relay/mutations branch on the runtime fact. No
new row; the standing row stands. Freshness: `9805cdaf`, `e6e32e78`.

### R6 — `typing-peels-vs-each-other` (rejected, fresh, same-file)

Four peels, four stop rules, one module: FL7 peels everything, FL8 keeps
lists, FL9 keeps non-containers, FL10 peels one layer. Each narrower
peel's docstring states the caller failure the wider peel would cause
(list classification, leaf descent, M2M-shape lock), and C7–C10 move at
most one each. A unified peel needs mode flags for exactly the parts
that differ. Durable home: the four docstrings + this row. Trigger: two
stop rules converging, or a fifth peel. Freshness: target as header.

### R7 — `typing-schema-literal-pair` (rejected, fresh, same-file)

`:49` and `:60` spell the `_strawberry_schema` literal twice in one
module — the only two production spellings (whole-package census: every
other hit is a function name, a docstring, or a test). The entries differ
(unwrap-or-self vs chain-or-`None`), and a rename is one edit in the
owning module: no second owner exists, so no family is owed and a
within-module constant would be style, not a change obligation removed.
Durable home: this row. Trigger: a third spelling, in or out of this
file. Freshness: target as header.

### R8 — ceiling vs debug hops (CONVERGE, separation stands)

The [debug][debug] `:120-125` separation re-checked at HEAD:
`_MAX_ORIGINAL_ERROR_HOPS = 64` is still deliberately NOT imported, with
its failure-policy difference (stop-and-keep vs raise) and its trigger
("until a fourth chain-peel motivates a shared extraction") recorded at
the owner. Body re-read, trigger unfired. No new row. Freshness:
`bf25c146`.

### R9 — `typing-peel-vs-adapter-unwrap-name-twin` (rejected, fresh)

[querysets][querysets]`::unwrap_async_queryset_adapter` shares the
`unwrap_` prefix and nothing else: it unwraps the async-only row adapter
around a final queryset, not a wrapper stack around a type. Name-twin
only. Durable home: this row. Trigger: an adapter that IS a type
wrapper. Freshness: target as header; `3616927d`.

### R10 — `typing-func-peel-vs-identity-tests` (rejected, fresh)

HEAD [types-relay][types-relay] `__func__` sites (`:562/:584/:589/:1032-1033`)
COMPARE `__func__` identity (classmethod-default detection); FL5
DESCENDS through `__func__` to an inspection target. Compare vs descend
are different operations on the same dunder; no descent loop exists
outside `:109` (`.func` census is this line + docstrings). Durable home:
this row. Trigger: a second callable-descent need. Freshness: target as
header; `52439862`.

## Defects

None. The examinations that could have produced one all closed clean at
HEAD bytes: archived spec-020 cites the removed
`is_async_generator_callable`, but archives are point-in-time and the
removal was deliberate (`d4c07d7d` by-value seam; live GLOSSARY is
current) — not a contradiction; the extension `:819` "recursively peels"
prose describes FL7's delegated effect while the body composes by call;
the GLOSSARY "one-hop partial" phrase is accurate for partials
(construction-flattened); every loop in the module is FL4-bounded with a
loud terminal, and every `None`/missing step in the digs returns rather
than raises per its docstring.

## Judgment

The declared-shape seam is already one owner per rule: two digs, one
config ladder, one ceiling, one wrapper peel, one async predicate, and
four peels each defined once in this module and composed by name from
every flavor, with the neighboring derivations (upstream named-type,
shape lock, renderers, value route, executor fact, adapter unwrap,
identity tests) each carrying a contract difference and a trigger.
Zero-edit stands.

## Index rows for Worker-0

| `typing-module-mechanics` | `django_strawberry_framework/utils/typing.py` (rule-map docstring + stdlib-only imports + exact-9 `__all__`, zero star-importers) | `django_strawberry_framework/utils/typing.py` | File `utils/typing.py` | file-local |
| `typing-schema-unwrap-or-self` | `django_strawberry_framework/utils/typing.py::strawberry_schema_from_schema` (unwrap-or-self fallback; 1 consumer by call) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/optimizer/extension.py` | File `utils/typing.py` | file-local |
| `typing-info-schema-walk` | `django_strawberry_framework/utils/typing.py::strawberry_schema_from_info` (chain-or-None walk; 2 consumers by call) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/optimizer/extension.py` | File `utils/typing.py` | file-local |
| `typing-config-preference-ladder` | `django_strawberry_framework/utils/typing.py::schema_config_from_info` (wrapped-then-direct-then-None; 3 consumers by call) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/optimizer/selections.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/utils/connections.py` | File `utils/typing.py` | file-local |
| `typing-wrapper-depth-ceiling` | `django_strawberry_framework/utils/typing.py::MAX_TYPE_WRAPPER_DEPTH` (64 + loud RuntimeError over 4 in-file peels) | `django_strawberry_framework/utils/typing.py` | File `utils/typing.py` | file-local |
| `typing-callable-inspection-peel` | `django_strawberry_framework/utils/typing.py::_callable_inspection_target` (partial/staticmethod descent, FL4-bounded; FL6-only consumer) | `django_strawberry_framework/utils/typing.py` | File `utils/typing.py` | file-local |
| `typing-partial-aware-async-predicate` | `django_strawberry_framework/utils/typing.py::is_async_callable` (4-shape coroutine predicate, async-generator False; 3 call sites) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/types/base.py` | File `utils/typing.py` | file-local |
| `typing-full-oftype-peel` | `django_strawberry_framework/utils/typing.py::unwrap_graphql_type` (peel-all + None passthrough; 2 call sites) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/optimizer/extension.py` | File `utils/typing.py` | file-local |
| `typing-non-null-only-peel` | `django_strawberry_framework/utils/typing.py::unwrap_non_null` (NonNull-only, lists kept; 3 call sites) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/extensions/resource_policy.py` | File `utils/typing.py` | file-local |
| `typing-container-only-peel` | `django_strawberry_framework/utils/typing.py::unwrap_container_type` (StrawberryContainer-only gate; 1 consumer) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/connection.py` | File `utils/typing.py` | file-local |
| `typing-one-layer-return-peel` | `django_strawberry_framework/utils/typing.py::unwrap_return_type` (of_type-first one-layer + bare-list-Any; 1 consumer) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/mutations/sets.py` | File `utils/typing.py` | file-local |
| `typing-full-peel-vs-upstream-get-named-type` | `django_strawberry_framework/utils/typing.py::unwrap_graphql_type` (rejection recorded here; fresh — bounded Strawberry-tolerant peel vs upstream graphql-core-only primitive; trigger: domain/failure-policy convergence) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/extensions/resource_policy.py` | File `utils/typing.py` | rejected |
| `typing-peel-vs-shape-lock` | `django_strawberry_framework/utils/typing.py::unwrap_graphql_type` (rejection recorded here; fresh — core peel vs (depth, core) with silent-stop cycles; trigger: loud cycles or a second depth peel) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/mutations/sets.py` | File `utils/typing.py` | rejected |
| `typing-peel-vs-render` | `django_strawberry_framework/utils/typing.py::unwrap_graphql_type` (rejection recorded here; fresh — peel-to-value vs descend-to-render; trigger: a render needing the core as a value) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/management/commands/inspect_django_type.py` | File `utils/typing.py` | rejected |
| `typing-async-shape-vs-value-route` | `django_strawberry_framework/utils/typing.py::is_async_callable` (rejection recorded here; fresh — declared-shape-at-construction vs value-at-resolve-time, `d4c07d7d` seam; trigger: a construction-time async-generator need) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/utils/querysets.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/optimizer/extension.py` | File `utils/typing.py` | rejected |
| `typing-peels-vs-each-other` | `django_strawberry_framework/utils/typing.py::unwrap_graphql_type` (rejection recorded here; fresh same-file — four peels, four stop rules, unified peel needs mode flags; trigger: stop rules converging or a fifth peel) | `django_strawberry_framework/utils/typing.py` | File `utils/typing.py` | rejected |
| `typing-schema-literal-pair` | `django_strawberry_framework/utils/typing.py::strawberry_schema_from_schema` (rejection recorded here; fresh same-file — 2 spellings 1 file, no second owner; trigger: a third spelling) | `django_strawberry_framework/utils/typing.py` | File `utils/typing.py` | rejected |
| `typing-peel-vs-adapter-unwrap-name-twin` | `django_strawberry_framework/utils/typing.py::unwrap_graphql_type` (rejection recorded here; fresh — type-stack peel vs queryset-adapter unwrap, name-twin only; trigger: an adapter that is a type wrapper) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/utils/querysets.py` | File `utils/typing.py` | rejected |
| `typing-func-peel-vs-identity-tests` | `django_strawberry_framework/utils/typing.py::_callable_inspection_target` (rejection recorded here; fresh — descend-through vs compare-identity; trigger: a second callable-descent need) | `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/types/relay.py` | File `utils/typing.py` | rejected |

## Families

None new. Zero adoptions. Two convergences onto standing rows
(`execution-mode-fact-vs-shape-classification`,
the owner-recorded debug-ceiling separation — triggers re-checked in
R5/R8, both stand). Eight fresh rejections (R1–R4, R6–R7, R9–R10).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[connection]: ../../django_strawberry_framework/connection.py
[debug]: ../../django_strawberry_framework/extensions/debug.py
[execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[extension]: ../../django_strawberry_framework/optimizer/extension.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[request-body]: ../../django_strawberry_framework/middleware/request_body.py
[resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[selections]: ../../django_strawberry_framework/optimizer/selections.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py
[utils-init]: ../../django_strawberry_framework/utils/__init__.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-init]: ../../tests/utils/test_init.py
[test-typing]: ../../tests/utils/test_typing.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Traced expectation-first: required reading, full worktree target read,
HEAD bytes via `git show HEAD:…` (blob `de6309f6`, 280 lines), AST
enumeration over HEAD bytes, HEAD-vs-worktree diff (2 hunks),
item-scoped diff vs `ITEM_BASELINE=d573e9f3` (empty on the target —
the baseline tree already carries `a672cd6b`, so the dirt predates
the item by mechanics; content attribution below is independent of
that fact), whole-package production greps at HEAD for all nine
exported names plus `_callable_inspection_target`, and every
connected site plus both oracle files opened — all before this
artifact's `## Findings`. HEAD `0c0537e2` unmoved at start;
worktree blob `a672cd6b` (280 lines); path `M`; artifact untracked.

My trace. Enumeration instrument: `ast.Module.body` over HEAD bytes —
15 statements: module docstring, 3 imports (`functools`, `inspect`,
`typing`), `__all__`, 9 defs (`strawberry_schema_from_schema`,
`strawberry_schema_from_info`, `schema_config_from_info`,
`_callable_inspection_target`, `is_async_callable`,
`unwrap_graphql_type`, `unwrap_non_null`, `unwrap_container_type`,
`unwrap_return_type`), 1 ceiling assign. Eleven rules, all owned
here: two schema-dig entries, one config ladder, one ceiling, one
callable peel, one async predicate, four peels with four stop rules,
plus module mechanics. Matrix expectations: axis 1 — the target is
the seam, flavors compose by call (expected ≤3 async consumers, one
config trio); axis 2 — pure predicate, no twin owed; axis 3 — the
`_strawberry_schema` spelling count and the Union/Annotated/get_args
neighbors are the sights to clear; axis 4 — peels are one-way, no
round trip; axis 5 — oracle literalness to check; axis 6 — the
async-consumer family boundary (which field factories lack a
consumer-resolver seam) to confirm. Owner by responsibility: this
module for all eleven — every consumer already depends on `utils`.

Reconciliation — every judgment STANDS except 4 verdict-neutral
record blemishes (reproductions below):

- Enumeration 15/15: AGREE. W1's homing table matches my AST dump
  member by member (#0–#14, positions exact). Blemish 1 is prose
  only (see below).
- Hunk attribution: AGREE, independently re-derived. The 2 hunks
  are (a) `from . import truth` in the import block and (b) the
  `is_async_callable` tail rewrite (class/instance `getattr`
  pair → `truth.static_attr(type(target), "__call__")`).
  `utils/truth.py` is absent from HEAD (`git ls-tree` —
  zero hits) and untracked in the worktree (with `utils/lazy.py`);
  both hunks belong to that migration, neither to the ledger
  (`## Owned changes` names no `typing.py` row), neither to W1.
  HEAD-bytes tracing is the correct call.
- R1–R4, R6, R7, R9, R10: AGREE, each probed fresh at HEAD.
  R1: `get_named_type` at resource-policy `:710/:788/:979/
  :1005/:1256`, unbounded upstream primitive vs FL7's bounded
  Strawberry-tolerant peel — confirmed different rules.
  R2: `_strawberry_field_shape` returns `(depth, core)`,
  counts Strawberry lists only, silent-stop `seen` set; `:1581`
  answers depth only — confirmed. R3: both inspect renderers
  descend to RENDER strings, no core escapes — confirmed. R4:
  value-at-resolve-time sites confirmed (`is_async_only_iterable`
  `:377-390`, `isawaitable` at querysets `:188/:213/:3127/
  :3160`, types-resolvers `:629/:705/:778`, auth-mutations
  `:505/:509`, extension `:1124`); `d4c07d7d` confirmed real
  (by-value seam commit). R6: four stop rules re-read, each
  narrower peel's docstring states the wider peel's caller
  failure — confirmed. R7: `_strawberry_schema` literal in
  production code exactly at `:49`/`:60`; all other hits are
  function names, docstrings, or comments — confirmed. R9:
  adapter unwrap returns `(inner, bool)`, name-twin only —
  confirmed. R10: types-relay `:562/:584/:589/:1032-1033`
  compare identity; no second descent loop (the `:109`
  `.func` line stands alone) — confirmed.
- R5/R8 convergences: AGREE. R5: executor-fact bodies re-read,
  asgiref capability reads at request-body `:143/:161`,
  relay/mutations branch on the runtime fact, trigger unfired;
  standing row located in the plan index. R8: the debug
  separation re-read — deliberately-not-imported, stop-and-keep
  vs raise, "fourth chain-peel" trigger unfired. Blemish 2 is
  the cite only.
- Zero-defect call: AGREE. Re-read every loop (all FL4-bounded,
  loud terminals), every dig's `None`/missing path (returns
  per docstring), the `:819` prose (describes delegated effect,
  body composes), the GLOSSARY pair and CHANGELOG rows (both
  present as cited). The `inspect:138` read found under
  blemish 4 is a one-line consumer of a public upstream
  attribute, not a second ladder definition — no family, no
  defect, census footnote only. No Worker-2 defects.
- Freshness: all 21 cited `HEAD:` short blobs re-hashed exact.
  Consumer census re-derived line-for-line (connection
  `:2035`, list-field `:1696`, types-base `:451`,
  mutations-sets `:1608`, extension `:742/:829` + aliased
  `:737/:833`, resource-policy `:501/:976/:1002`, connection
  `:283`, selections `:562`, walker `:243`, utils-connections
  `:731`; `_callable_inspection_target` in-file only;
  utils-`__init__` 2-of-9; zero star-importers; the one
  `test_query` hit is a comment). Challenges C1–C12 line refs
  spot-verified (`:88`, loop ranges, `:150-157`, `:278-279`).
  No `## Pending execution` owed (all proofs static).

DIFFER on record accuracy only — 4 blemishes, none
verdict-moving, each reproducible below. Per the cycle's
record-accuracy bar (File `utils/strings.py` W2, following
File `utils/sessions.py` W2: `revision-needed` for
verdict-neutral blemishes), this is `revision-needed`, not
`verified`: resubmission to the SAME W1 context (no re-trace;
every judgment stands; fix the prose, keep the verdicts).

1. Enumeration instrument overcounts defs. "module docstring, 3
   imports, `__all__`, 10 function defs, 1 ceiling assign"
   sums to 16, not 15: HEAD carries 9 defs (mechanical:
   `git show HEAD:… | python3 -c` AST dump — 9 `FunctionDef`
   nodes). Fix "10 function defs" → "9 function defs".
   The #0–#14 homing table is already correct, verbatim.
2. R8 range off by one. The debug separation spans `:120-125`
   (comment block + `_MAX_ORIGINAL_ERROR_HOPS = 64` assign);
   `:119` is blank and the cited `:119-124` misses the
   constant. Fix the cite to `:120-125`. Separation and
   trigger stand verbatim.
3. Oracle count wrong. Axis 5 "25 tests" reproduces as 27
   module-level `def test_` functions (`git show
   HEAD:tests/utils/test_typing.py | grep -c "def test"` —
   27, all genuine, 480 lines confirmed). Fix "25 tests" →
   "27 tests". Oracle independence stands verbatim.
4. Axis-3 `.config` census misses a same-population read.
   "(the only `.config` production reads are this module's
   own `:76/:78`)" — but `getattr(schema_object,
   "config", None)` also reads at
   management/commands/inspect_django_type.py `:138`
   (mechanical: `git grep -n '"config"' HEAD -- package`
   yields exactly 3 sites). Dispose it on a stated basis:
   recommended wording is fold-in with a contract clause —
   the inspect read takes a schema object or `None` with a
   default-converter fallback (no ladder, different input; a
   one-line consumer of a public upstream attribute, so no
   second ladder definition and no new row). Corrected
   census strengthens the axis; no verdict moves.

HEAD movement check: `0c0537e2` at dispatch, at every W2
check, and at verdict; target blobs `de6309f6`/`a672cd6b`
stable; item diff vs `ITEM_BASELINE` still empty on the
target; no new ledger row names this file; plan untouched by
W2 per dispatch. Ruff: no tracked path touched by the item
(zero-edit file item; target dirt is concurrent-external),
so no `ruff check`/`format --check` population exists; this
verdict section adds no cross-file links (scaffold intact).
Verdict: `revision-needed` on record accuracy (SAME W1
context, prose-only fixes 1–4 above); all judgments stand
pending them.

## Iterations

### Pass 2 (record-accuracy revision, same W1 context)

W2 verdict `revision-needed` on 4 prose blemishes; every judgment
stood. No re-trace, no verdict change, no production or plan edit.
Each fix re-proven mechanically this pass before the prose moved:
(1) AST dump over HEAD bytes — 9 `FunctionDef` nodes, so the
instrument line now reads "9 function defs" (homing table #0–#14
verbatim); (2) debug.py `:119` blank, comment block + assign span
`:120-125` — R8 cite fixed; (3) `grep -c "def test"` over HEAD
`test_typing.py` — 27, all genuine — axis-5 count fixed; (4) `"config"`
census is exactly 3 sites (this module `:76/:78` +
[inspect][inspect] `:138`, which takes schema-or-`None` with the
`:139` default-converter fallback) — axis-3 sentence folded in with
the no-ladder contract clause, no new row. HEAD `0c0537e2` unmoved;
target blobs unchanged (`de6309f6` / `a672cd6b`); resubmitted as
`ready-for-verification/2`.

## Independent re-verification (Worker-2) — pass 2, verdict `verified`

Re-pass on resubmission `ready-for-verification/2` (same W2
context). Gates: HEAD `0c0537e2` unmoved, target blobs
`de6309f6`/`a672cd6b` stable, item diff vs `ITEM_BASELINE`
still empty on the target — pass-1 HEAD evidence stands
without re-trace. All four record fixes reproduce mechanically:
(1) instrument reads "9 function defs", AST re-dump counts 9
`FunctionDef` nodes, homing table #0–#14 verbatim; (2) R8 cites
`:120-125`, re-proven (`:119` blank, comment block + assign
span `:120-125`); (3) axis 5 reads "27 tests", `grep -c`
re-proves 27; (4) axis-3 census folded in with the stated
contract clause (schema-or-`None`, no ladder, no new row),
`"config"` census re-proves exactly 3 sites and the
inspect `:138-139` shape. Nothing else moved: every section
header shifted exactly +3 (the axis-3 insertion), the other
three fixes are in-place word swaps, my pass-1 W2 section is
byte-intact, stale phrases survive only inside its blemish
quotations, and the delta is Status + the four rows +
`## Iterations`. All pass-1 judgments stand; record now
reproduces. Verdict: `verified`.
