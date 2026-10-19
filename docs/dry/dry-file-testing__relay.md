# DRY review: `django_strawberry_framework/testing/relay.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to a holding
family for Worker-0 to add, or is a rejection carrying its contract
difference + trigger. Zero production edits; zero tracked files changed.
HEAD-bytes trace throughout (see Dirt note).

## System trace

Small target (110 lines at HEAD): the public Relay test helpers
`global_id_for` / `decode_global_id` (spec-032 Decision 10). It DEFINES one
multi-gate helper (`global_id_for`: registered-own-definition proof,
finalized gate, stamp read, non-Relay gate, encode-only refusal, mint tail)
and COMPOSES the rest by name: `decode_global_id` re-exported from
[types-relay][types-relay], the gate constants + strategy set + `DjangoType`
from [types-base][types-base], `registry` from [registry][registry],
`ConfigurationError` + `_safe_arg_repr` from [exceptions][exceptions], and
`relay.GlobalID` from Strawberry. No `class`, no branch outside the one
function, no `await`, no `sync_to_async`, no bus row, no queryset, no
transport: runtime effects are validation + pure string minting.

Connected code read for judgment, outside the item: [testing-init][testing-init]
(full, clean), [testing-wrap][testing-wrap] (full, clean),
[types-relay][types-relay] (`encode_typename`, `decode_global_id`,
`MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` + the three predicates,
`install_globalid_typename_resolver`, `_resolve_id_default`, at HEAD bytes),
[types-base][types-base] (gate-constant block + census comments,
`STRING_GLOBALID_STRATEGIES`, the four `Meta` gates,
`_validate_globalid_strategy`, `_is_relay_shaped` site, at HEAD bytes),
[root-relay][root-relay] (`_decode_or_graphql_error`,
`decode_model_global_id`, `_validate_node_target`, at HEAD bytes),
[list-field][list-field] (`_validate_djangotype_target` head + docstring +
body, `_validate_relay_djangotype_target` docstring, at HEAD bytes),
[filters-base][filters-base] (`FRAMEWORK_GLOBALID_STRATEGIES` /
`ENCODE_ONLY_GLOBALID_STRATEGIES`, `_accepted_globalid_type_names`,
`_decode_and_validate_global_id`, at HEAD bytes), [registry][registry]
(`get` / `get_definition` / `definition_for_graphql_name` sites, at HEAD
bytes), [exceptions][exceptions] (`_safe_arg_repr` body, at HEAD bytes),
[mutation-fields][mutation-fields] (`_validate_mutation_target` body, at HEAD
bytes), [inspect][inspect] (definition/finalized check, at HEAD bytes),
[types-resolvers][types-resolvers] (optional-metadata read, at HEAD bytes),
[optimizer-extension][optimizer-extension] (origin reachability read, at HEAD
bytes), [types-definition][types-definition] (stamp slots, at HEAD bytes),
[finalizer][finalizer] (audit + finalized-loop sites, at HEAD bytes),
[connection][connection] (cache-provenance check, at HEAD bytes),
oracles [test-relay][test-relay] (all 11 bodies, at HEAD bytes) and
[test-library-api][test-library-api] (the two relay tests + `_decode_global_id`
helper, at HEAD bytes), contract sources [spec-032][spec-032] Decision 10 +
DoD + exports-list note (read) and [spec-043][spec-043] Decision 4 (passage,
read), projections [docs-readme][docs-readme] line 244 (identical at both
revisions) + [glossary][glossary] helper entry, and the consumer census
(dotted-`testing.relay` import sites across `tests/` at HEAD bytes plus
`examples/fakeshop/`).

Dirt note (HEAD-only judgment; nothing touched): the target itself is DIRTY
— worktree `f807bf92fbc41f5b3f5fd19c0fed24da2f6eff88` (109 lines) vs HEAD
`df0dc72a178854e261fa7236c6614a758a008722` (110 lines): a `truth`-migration
hunk inside `global_id_for` (`_safe_arg_repr` → `truth.render`,
`isinstance`/`getattr` → `truth.is_subclass`/`truth.static_attr`, `except
BaseException` arm deleted) plus one import line. Per dispatch this dirt is
concurrent-external (absent from the ledger and the cycle baseline); it is
fingerprinted, never judged. The worktree further holds an in-flight
truth-migration: `utils/truth.py`, `scripts/check_truthful_reads.py`, and
the `[tool.truthful_reads]` config are all worktree-only (absent from HEAD
— verified: `git show HEAD:` fails for both files, HEAD pyproject carries
no such table), and worktree [exceptions][exceptions] deletes
`_safe_arg_repr` outright (0 hits vs 10 at HEAD). Judging worktree bytes
would judge a mid-migration tree against HEAD contracts; every verdict
below reads HEAD bytes. All other dirty inputs are fingerprinted with both
hashes; clean inputs ([testing-init][testing-init], [testing-wrap][testing-wrap],
both specs, [glossary][glossary]) are named once.

Excluded with reason: `one-sync-boundary` (no boundary call here — token
grep 0, C22), `subsystem-clear-lifecycle` (no bus row — token grep 0, C23),
`typed-globalid-decode` (verified; this file is a recorded consumer — mint
via `encode_typename`, decode re-exported — not a member, C24),
`sealed-execution-queryset` and the optimizer families (no queryset here),
`soft-dependency-require-guard` (hard deps only), `hostile-mapping-hardening`
(no mapping read here), `upstream-patch-lifecycle` /
`upstream-patch-refusal-wording` (no patch mechanics here). The verified
`relay-node-target-guard` family covers the field-factory side of target
validation and never names this file (grep 0 for `testing` in its artifact);
R1's holding family reconciles scope with it (recorded in F1, not adopted).
`types/relay.py::decode_global_id` internals below the re-export are
witnessed by the decode-identity oracle plus a full HEAD body read (needed
for the asymmetry + Step-2 contract), never re-verified.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The mint half has no flavor mirror:
whole-package census at HEAD finds exactly one `relay.GlobalID(`
construction ([testing-relay][testing-relay] HEAD :110); live emission
travels Strawberry's own `Node` machinery (`resolve_typename` closures over
`encode_typename`), which this helper calls rather than copies (F5). The
decode half is consumed, not mirrored: root fields via
[root-relay][root-relay]`::_decode_or_graphql_error`, write flavors via
`::decode_model_global_id`, filters via their own `from_id` + strategy
validation ([filters-base][filters-base]`::_decode_and_validate_global_id`
— a different contract: `GraphQLError` envelopes + pk coercion, rejected at
F4). The analogous target guard in the mutation flavor
([mutation-fields][mutation-fields]`::_validate_mutation_target`) is
deliberately duck-typed per spec-038 Decision 5 (protocol + `_mutation_meta`
+ ledger, never `issubclass`) — a different rule, excluded on body strength.
One genuine cross-module twin found: the registered-own-definition proof
(F1, routed to a holding family).

**2. Sync/async twins.** Inapplicable with reason: the target defines no
colored pair — token grep over HEAD bytes for `async` / `await` /
`sync_to_async` returns 0 (full 110-line read). Mint and decode are sync
dict/string work; the verified `typed-globalid-decode` family records the
same no-twin posture for the pipeline this helper feeds. Considered family
`one-sync-boundary`: checked, no boundary call lives here (C22).

**3. Derived rather than repeated knowledge.** The payload is derived once
at its owner and composed here: `encode_typename` computes the slot
([types-relay][types-relay]), this helper passes its recorded strategy
through (F5, C11 → 0 here). The strategy itself is read from the
finalize-stamped slot, never re-derived from settings or `Meta` (F2, C4 →
token grep 0 for `RELAY_GLOBALID_STRATEGY` / `relay_globalid_strategy_setting`).
The gate wording is composed from the shared constants, never re-typed
(F3, C7 → 0 here). `__all__` hand-mirrors the two bindings in the same file
(one edit region, adjacent lines — F6). Nothing is re-derived at runtime.

**4. Inverse / round-trip pairs.** This file IS one half of the package's
GlobalID round-trip pair plus the re-exported other half: mint
(`global_id_for` here) vs decode (`decode_global_id` in
[types-relay][types-relay], re-exported here). One grammar, two halves —
the verified `typed-globalid-decode` family records the pair explicitly
("`global_id_for` mints via `encode_typename`"). The asymmetry (secondary
mints, decode routes to primary) is the documented Decision-10 contract,
pinned by oracles at two tiers (F5/F7). No second mint half exists (the
`GlobalID(` census above); no second decode half exists (`from_id` census:
exactly two production sites — [types-relay][types-relay] :751 inside the
owned decode, [filters-base][filters-base] :770 inside the filter contract
— plus docstring mentions).

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (the helper + re-export + `__all__`);
authoritative contract sources ([spec-032][spec-032] Decision 10 for the
helper pair + asymmetry + export gate, [spec-043][spec-043] Decision 4 for
the submodule-only posture); independent oracles ([test-relay][test-relay]
11 bodies spelling literals and driving behavior, never reading owner
tables; the two live-tier tests comparing helper output against wire bytes);
projections (module + function docstrings, the [testing-init][testing-init]
withholding bullet, [docs-readme][docs-readme] line 244, the
[glossary][glossary] entry, owner cross-reference comments at
[types-base][types-base] :120-123 and [types-relay][types-relay]
`encode_typename`). A strategy-vocabulary change moves each owner once;
this file's rows follow by name (C7, C9, C11).

**6. Enforcement by omission.** Four probed absences, each with a contract
source or a recorded rejection: (a) [inspect][inspect] checks
`definition is None` + `finalized` but not registry-canonicality — its
target resolves through the registry by construction, and no contract
source requires the proof there (rejected J4, not a defect); (b) secondary
emitters mint payloads that decode to the primary — documented Decision-10
asymmetry with a dedicated live oracle, not a gap; (c) `callable`/`custom`
have no mint path — the contract (consumer owns its helper), refused with
the recorded rationale; (d) `utils/truth.py` readers do not exist at HEAD
(absent from the tree — verified), so no shared-reader consolidation is
available to this file at HEAD (rejected J2). No member lacks a guard its
contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned HEAD blob
`df0dc72a178854e261fa7236c6614a758a008722`, counting `ast.Module.body`
members — **8 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection. (HEAD line numbers; the worktree's 109-line revision shifts the
import block by one — nothing below cites worktree lines.)

| # | Statement (HEAD) | Binds / carries | Home |
|---|---|---|---|
| 0 | module docstring (public-path rule, strategy table, asymmetry contract, import-light passage) | (none — prose) | R7, rejected projection |
| 1 | `from strawberry import relay` | `relay` | R5 (mint tail consumer) |
| 2 | `from ...exceptions import ConfigurationError, _safe_arg_repr` | raise vocabulary + safe render | R1–R4 (consumers; owner [exceptions][exceptions]) |
| 3 | `from ...registry import registry` | `registry` | R1 (consumer; owner [registry][registry]) |
| 4 | `from ...types.base import (_RELAY_NODE_GATE_INHERIT_TAIL, _RELAY_NODE_GATE_LEAD, STRING_GLOBALID_STRATEGIES, DjangoType)` | gate pair + strategy set + base | R1 (`DjangoType`) + R3 (gate pair) + R4 (strategy set), all consumers |
| 5 | `from ...types.relay import decode_global_id, encode_typename` | re-export + slot computer | R6 (`decode_global_id`) + R5 (`encode_typename`), both consumers |
| 6 | `__all__ = ["decode_global_id", "global_id_for"]` | 2-name manifest | R6, file-local |
| 7 | `def global_id_for(type_cls, id)` (HEAD :52–110: step-1a proof :61–77, finalized gate :78–89, stamp read :90, `None` gate :91–97, membership gate :98–104, mint tail :105–110) | the helper | R1 (family) + R2–R5 (file-local) |

Rules: R1 registered-own-definition validation (member 7, :61–77);
R2 finalized-gate + stamp-read-never-setting (member 7, :78–90);
R3 non-Relay gate composing the shared constants (member 7, :91–97);
R4 encode-only refusal (member 7, :98–104); R5 mint tail + signature
(member 7, :105–110 + :52); R6 submodule manifest + re-export (members
5–6); R7 module contract prose (member 0). One holding family named (R1);
no indexed family adopted (C22–C26 check six with no surface or
consumer-only posture); two convergences recorded (J1 with the verified
shared-except direction, F7-nested with the verified
withholding-prose-pair direction). Twelve index rows named for Worker-0
(1 open family + 5 file-local + 6 rejected).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. All bodies judged at HEAD bytes (see Dirt note).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 proof | accept inherited definitions (drop the own-definition arm) | **2** (this block + [list-field][list-field]`::_validate_djangotype_target`) | candidate → holding family |
| C2 | R1 proof | drop the registry-identity arm (`definition is canonical`) | **2** (same pair) | candidate → holding family |
| C3 | R1 proof | contain `BaseException` uniformly (one scope at both proof sites) | **2** bodies, 1 must move (this block already contains `BaseException` over the whole proof; the list-field base catches `Exception` around the read only — currently diverged) | candidate → holding family |
| C4 | R2 stamp read | read the live `RELAY_GLOBALID_STRATEGY` setting instead of the stamp | **1** here (the refused direction; proves the stamp-read is the rule — token grep 0 for the setting) | independent — lawful snapshot consumer |
| C5 | R2 gate order | drop finalized-first (read the stamp before the gate) | **1** here (the Phase-3-stamped-unfinalized oracle fails) | independent |
| C6 | R2 remediation | reword the finalize-first remediation | **1** here (message + its oracle pins listed) | independent |
| C7 | R3 gate wording | change the Relay-gate lead/tail wording | **1** ([types-base][types-base] constants; **0** here — follows by name) | independent — consumer |
| C8 | R3 composition | give the helper its own inline gate message | **1** here | independent |
| C9 | R4 membership | add a fourth string strategy | owners move (`STRING_GLOBALID_STRATEGIES` + payload-shape memberships); **0** hand-edits here (membership follows by name, message interpolates `{strategy!r}`) | independent — consumer |
| C10 | R4 message | reword the live-root rationale | **1** here (message + the `live root` oracle pin listed) | independent |
| C11 | R5 payload | change the model-label / type-name slot shapes | **1** (`encode_typename`; **0** here — follows by call) | independent — consumer |
| C12 | R5 encoding | change the `GlobalID` wire encoding | **0** here (Strawberry owns `str(GlobalID)`; equality oracles pin) | independent — consumer |
| C13 | R5 coercion | reject UUID (or accept only `int`) | **1** here (the `str(id)` tail + the id-types oracle listed) | independent |
| C14 | R6 manifest | add a third helper to the submodule | **1** here (`__all__` + binding; **0** at the leaf — the withholding holds) | independent |
| C15 | R6 re-export | wrap `decode_global_id` instead of re-exporting | **1** here (the identity oracle fails → oracle update listed) | independent |
| C16 | R7 prose | reword Decision 10 | **0** definitions (spec + projections move) | no definition here — prose follows |
| C17 | J1 guard | drive both `except` sites from one shared guard driver | **0**-as-consolidation (CONVERGE with the verified shared-except direction) | rejected |
| C18 | J3 predicate | gate the helper on declared interfaces instead of the stamp | refused (lifecycle-phase difference — the stamp is post-finalize classification, the predicate pre-finalize declaration) | rejected |
| C19 | J4 CLI check | unify with the `inspect` finalized check | refused (different surfaces; no stamp read there) | rejected |
| C20 | J5 coercion | unify `str(id)` with the row-id `str()` sites | refused (caller-supplied pk vs resolved row value) | rejected |
| C21 | J2 readers | route the slot reads through shared truth readers | refused at HEAD (no such module exists — verified absent from the tree) | rejected |
| C22 | `one-sync-boundary` check | change the one-boundary rule | **0** here (no boundary call — token grep 0) | no surface — do not inherit |
| C23 | `subsystem-clear-lifecycle` check | change the clear-bus contract | **0** here (no bus row — token grep 0) | no surface — do not inherit |
| C24 | `typed-globalid-decode` check | change the typed-decode pipeline | **0** here as member (recorded consumer: mint via `encode_typename`, decode re-exported — the family artifact names both) | consumer only — do not inherit |
| C25 | grammar check | change a refusal wording | **0** new here (per-subject grammars stay at their subjects — CONVERGE with the verified direction) | no surface — do not inherit |
| C26 | `globalid-setting-snapshot` check | change the snapshot rule | **0** here as member (lawful stamp consumer; T-reader/T-compute/T-lifetime re-checked fresh — all unfired) | consumer only — do not inherit |

No executable proof was run. Every claim below is `static-reviewed`:
bodies compared by reading at pinned HEAD bytes, censuses by whole-tree
grep over a `git archive HEAD` extraction, and behavior already pinned by
the cited oracles (no pytest per [AGENTS.md][agents]). A probe could
distinguish nothing further — the one executable-shaped claim (a
classification string through `encode_typename` falls to the `type`
branch) follows from `callable("callable") is False` plus the `in`
membership arms, read directly. No `docs/dry/temp-tests/` scratch was
created. No workspace runs (nothing source-mutating was needed).

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it, or routes the confirmed cross-file
candidate to the holding family named for Worker-0.

### F1 — registered-own-definition validation (holding family)

- **Contract + variation.** A consumer-presented object counts as a usable
`DjangoType` class only when it is a `DjangoType` subclass carrying the
registry's own definition for that exact class: the attribute definition
is not `None`, is identical to `registry.get_definition(type_cls)`, and
its `origin` is the class itself. Inherited definitions (unregistered
child), stale definitions (post-`registry.clear()`), copies, and
fabricated lookalikes are rejected; hostile inputs (raising metaclass
`__getattr__`, broken `__repr__`) fail closed into the same typed
`ConfigurationError`. Legitimate variation: the proof arms (subclass /
attribute / registry-identity / origin), the containment scope, and the
per-subject message.
- **Sites + roles.** *Definitions (2)*: this file's step-1a block (HEAD
:61–77 — `isinstance` + `issubclass` + `getattr` + registry read +
triple-`and`, all inside `try`/`except BaseException`, one fused message
via `_safe_arg_repr`) and [list-field][list-field]`::_validate_djangotype_target`
(HEAD — `inspect.isclass` + `issubclass` pre-gates with per-arm messages,
`try`/`except Exception` around the `getattr` only, `definition is None`
/ `origin is not` / `definition is not canonical` disjunction, returns the
definition). *Consumers of the list-field base*: [root-relay][root-relay]
`::_validate_node_target` (thin wrapper) and the connection field (per the
base docstring). *Oracles*: the inherited/stale oracle, the
hostile-`__getattr__` oracle, the hostile-`repr` oracle (all independent:
they drive hostile inputs and spell the fused message, never read the
proof arms), plus the list-field construction oracles. *Projections*: the
base docstring's "registered target cannot mean different things"
sentence (whose scope names only the list, connection, and Relay node
entry points — this helper is a fourth meaning-site outside the sentence).
- **Challenges.** C1 → 2; C2 → 2; C3 → 2 bodies currently diverged on
containment scope (the disproof attempt — inputs, outputs, errors, timing,
hooks — fails: both are sync pre-use guards, arbitrary object in,
`ConfigurationError` out; only messages, return-vs-local, and containment
breadth differ, all parameterizable without mode flags).
- **Owner + lifetime.** TBD by the family item. Candidates: a light home
every consumer can import ([registry][registry] itself, e.g. a
`registered_own_definition` predicate — dependency direction favors the
registry over the heavyweight field module, whose import weight this
helper's docstring promises to avoid), or the list-field base with this
block as its third consumer. No stored derivation; no lifetime fields
owed.
- **Migration.** For the family item: one proof body; per-site messages
stay (per-subject grammars); return-vs-local adapts at call sites; the
stronger containment wins (oracle-pinned).
- **Distinct behavior.** The resolver-callability seam stays at the
list-field base (a factory-only rule, no counterpart here); the fused vs
split messages stay per subject.
- **Behavioral proof.** `static-reviewed` (bodies compared at HEAD bytes;
oracles read, not executed). Rejects "one site proves a different fact"
(C1/C2 force both) and "containment scope is the contract" (C3 shows the
scope itself diverged — drift-shaped, exactly what the family reunites).
- **Structural gate.** Owed by the family item (a census gate over the
proof mechanism: `get_definition` + `origin`-identity co-sites — closed
here at exactly 2 by the sweep in Freshness). No new gate proposed by
this file item: a hand copy of either proof passes every behavior oracle
(the copy is correct), so behavior oracles cannot guard singularity.
- **Coupling.** J1 (the `except` shape at this site) and J2 (the
`getattr` shape at this site) both move if the family reunites the proof
— named here so neither rejection is read alone.
- **Freshness.** Target HEAD `df0dc72a…` (worktree `f807bf92…` migration
unjudged), [list-field][list-field] HEAD `21380eb7…` (worktree
`450e87cd…`), [root-relay][root-relay] HEAD `c3c5aea5…` (worktree
`e75e2b66…`), [registry][registry] HEAD `81bd561c…` (worktree
`492654d2…`), [exceptions][exceptions] HEAD `e06b0b7f…` (worktree
`206e9f8d…`, `_safe_arg_repr` deleted there), [test-relay][test-relay]
HEAD `55e43ed2…` (worktree `4e61e8f1…`: hostile-oracle removals +
message-pin rewrite — judged at HEAD). Searched population for a third
proof site: every `get_definition` consumer file (12) crossed with
`origin`-identity checks — only this pair co-locates both arms.
Excluded on strength of body: [connection][connection] `:1508`
(cache-provenance identity, not a registration proof),
[optimizer-extension][optimizer-extension] `:754-755` (origin reachability
for traversal, not a proof), [types-resolvers][types-resolvers] `:354`
(`None`-tolerant optional-metadata read, not a proof),
[mutation-fields][mutation-fields]`::_validate_mutation_target`
(duck-typed mutation-family protocol per spec-038 Decision 5 — a
different family by design), [inspect][inspect] `:151-156` (CLI check
without canonicality — J4), [finalizer][finalizer] finalized-loop skips
(idempotency, not gates).
- **Family note.** The verified `relay-node-target-guard` family covers
the field side (fifth guard + consumers) and never names this file; its
W2-C1 count-1 rests on a census that missed this site. Not a defect (no
contract row broken — a census-completeness note): the holding family
reconciles scope with it. The list-field file item is REOPENED (its
artifact is prior evidence only) — this routing rests on a fresh HEAD
trace, not on its R1 record.
- Named for Worker-0 as open family
`registered-djangotype-definition-validation` (no such row exists in the
current plan).

### F2 — finalized-gate + stamp-read-never-setting (file-local)

- **Contract + variation.** The helper gates on `definition.finalized`
FIRST (a partial-finalize failure can leave a non-`None` stamp on an
unfinalized type — the comment names Phase 2.5 vs Phase 3), then reads
the recorded `effective_globalid_strategy` — never the live setting, never
`Meta` — so minting is consistent-by-construction with live emission.
Legitimate variation: gate order (load-bearing), remediation text.
- **Sites + roles.** *Definition*: this file (HEAD :78–90). *Stamp writer*:
[types-relay][types-relay]`::install_globalid_typename_resolver` (Phase
2.5 classification). *Fellow stamp consumers*: decode Step 2, the
strategy-aware filter, the finalizer audits (all read the stamp, never
the setting — the snapshot family's own census). *Oracles*: the
unfinalized oracle (finalize-first pins), the Phase-3-stamped-unfinalized
oracle (proves the ordering), the strategy-equality oracles (prove the
stamp matches live emission). *Projection*: the function docstring's
"(never the setting)" clause.
- **Challenges.** C4 → 1 here (the refused live-read direction; T-reader
trigger unfired — zero setting reads by token grep); C5 → 1 here; C6 → 1
here.
- **Owner + lifetime.** This function (the gate + remediation are the
helper's own contract). Lawful convergence onto the
`globalid-setting-snapshot` direction as a stamp consumer (fresh trigger
checks: T-reader — no second production setting reader here; T-compute —
no validated-setting compute here; T-lifetime — no stored derivation
here; all unfired). That family is UNAPPLIED (recorded in the plan, not
in the tree) — this convergence adopts no tree change, only the
reader-posture direction.
- **Migration.** None (zero-edit item).
- **Distinct behavior.** The finalized gate is this helper's lifecycle
contract, not the finalizer's loop idempotency (`if definition.finalized:
continue` — excluded above) and not the CLI's print-guard (J4).
- **Behavioral proof.** `static-reviewed`. Rejects "the gate order is
cosmetic" (C5: the Phase-3 oracle pins the order) and "the helper could
read the setting" (C4: token grep 0 + the snapshot direction).
- **Structural gate.** Gate-only justification: the three oracles pin the
gate, the order, and the stamp agreement; a bespoke gate proving "reads
the slot" would restate the Phase-3 oracle. Negative control note: a
hand copy reading the setting instead fails the Phase-3 oracle (a stamped
unfinalized type mints) — the oracle guards the order, not the spelling.
- **Coupling.** None.
- **Freshness.** Target HEAD `df0dc72a…`, [types-relay][types-relay] HEAD
`52439862…` (worktree `4b2a9df5…`), [types-definition][types-definition]
HEAD `fa6c4d33…` (worktree `1c59a3fe…`), [finalizer][finalizer] HEAD
`de34ae2a…` (worktree `b9d8acb2…`), [test-relay][test-relay] HEAD
`55e43ed2…`. D1 (below) touches none of these lines.

### F3 — non-Relay gate composing the shared constants (file-local)

- **Contract + variation.** A finalized type whose stamp is `None` was
never Relay-Node-shaped (the stamp is written only for Relay-Node-shaped
types); the helper raises the shared gate wording by composing
`_RELAY_NODE_GATE_LEAD` + `_RELAY_NODE_GATE_INHERIT_TAIL` by name.
Legitimate variation: none here — wording lives at the constants.
- **Sites + roles.** *Definition*: the constants at
[types-base][types-base] :119-125. *Consumers*: the `Meta.connection`,
`Meta.cursor_field`, `Meta.globalid_strategy` gates in-file, this helper
(HEAD :91–97, byte-identical join), and the `relation_shapes` LEAD-only
variant. *Oracle*: the non-Node oracle spelling the LEAD literal
(independent: spells the literal, never reads the constant).
- **Challenges.** C7 → 1 at [types-base][types-base], 0 here; C8 → 1 here.
- **Owner + lifetime.** [types-base][types-base] (existing owner by
responsibility: the constants + the hoist comment recording this site as
a compose site). This helper is a consumer (principle 6).
- **Migration.** None (zero-edit item).
- **Distinct behavior.** Stamp-`None` (post-finalize classification
absence) vs interface-predicate (pre-finalize declaration) — J3 records
the split; the parenthesized fifth-guard variants in
[root-relay][root-relay] / [connection][connection] stay inline per the
owner comment (a different byte shape, already recorded at the owner).
- **Behavioral proof.** `static-reviewed`. Rejects "the helper owns gate
wording" (C7: a wording change moves zero lines here).
- **Structural gate.** Gate-only justification: composition by name IS the
structure (an inline re-typing would be caught by reading, and the oracle
pins the composed bytes). No bespoke gate owed.
- **Coupling.** D1 (the owner comment's stale census names this site's
neighborhood — the composition itself is unaffected).
- **Freshness.** Target HEAD `df0dc72a…`, [types-base][types-base] HEAD
`dda91365…` (worktree `dc67f084…`), [test-relay][test-relay] HEAD
`55e43ed2…`.

### F4 — encode-only refusal (file-local)

- **Contract + variation.** A recorded `callable` / `custom` strategy
raises: those encoders run on a live `root` the helper does not have, so
it cannot promise the payload (a consumer with a custom encoder owns its
own test helper). The membership gate (`strategy not in
STRING_GLOBALID_STRATEGIES`) names no `{"callable", "custom"}` literal —
absence-based, consistent with the [types-relay][types-relay] "no
literal" rule — and the message interpolates the recorded value. The gate
is load-bearing for correctness, not just contract: a classification
string is never `callable(...)`, so an un-gated `"callable"` would fall
through `encode_typename` to the `type` branch and mint a
wrong-but-valid-looking payload silently.
- **Sites + roles.** *Definition*: this file (HEAD :98–104). *Membership
owner*: `STRING_GLOBALID_STRATEGIES` at [types-base][types-base] (this
file + the `Meta`/setting validator are its only executable consumers).
*Oracles*: the parametrized callable/custom oracle (independent: builds
both shapes, pins the classification + `live root`). *Projection*: the
module docstring's encoder paragraph.
- **Challenges.** C9 → 0 hand-edits here (membership follows by name);
C10 → 1 here.
- **Owner + lifetime.** This function (the refusal + rationale are the
helper's own contract). Message-grammar convergence: per-subject
grammars stay at their subjects (C25, CONVERGE with the verified
direction).
- **Migration.** None (zero-edit item).
- **Distinct behavior.** Observation O1 (not a defect): for a hypothetical
future string strategy the "live root" rationale would mislead — but the
recorded classification is closed today (`install_globalid_typename_resolver`
stamps exactly the five values), so the arm is unreachable and no
contract row breaks. Trigger if a sixth classification lands: revisit the
message.
- **Behavioral proof.** `static-reviewed`. Rejects "the gate is
contract-only" (the fall-through analysis above — removing the gate mints
wrong payloads, which the callable/custom oracle would catch as minted
output instead of a raise).
- **Structural gate.** Gate-only justification: the parametrized oracle
pins both classifications' refusal; no bespoke gate owed.
- **Coupling.** None.
- **Freshness.** Target HEAD `df0dc72a…`, [types-base][types-base] HEAD
`dda91365…`, [types-relay][types-relay] HEAD `52439862…`,
[filters-base][filters-base] HEAD `ba52351c…` (worktree `3b1dcbce…`),
[finalizer][finalizer] HEAD `de34ae2a…`, [test-relay][test-relay] HEAD
`55e43ed2…`.
- **Rejection (nested R-A).** Considered: unifying with the filter
encode-only backstop ([filters-base][filters-base]`::_decode_and_validate_global_id`
→ `GLOBALID_UNVALIDATABLE` `GraphQLError`) and the build-time audit
([finalizer][finalizer]`::_audit_globalid_filter_strategies`). Contract
difference here: this refusal is a test-helper `ConfigurationError` with
a consumer-owns-its-helper remediation; the backstop is a request-path
coded `GraphQLError` for hand-built filtersets; the audit is a
build-time error naming filterset + field. Different envelopes, timing,
audiences, remediations — a message change at any one moves only it
(C10/C25). Fresh rejection, no prior verdict. Trigger to reconsider: a
shared encode-only taxonomy with per-surface renderers would make the
three one rule. Durable home: this artifact + the owner docstrings
(already state each surface). No separate index row (carried by this
file-local row's record).
- **Rejection (nested R-B).** Considered: `STRING_GLOBALID_STRATEGIES`
([types-base][types-base]) vs `FRAMEWORK_GLOBALID_STRATEGIES`
([filters-base][filters-base] — the `MODEL_LABEL | TYPE_NAME` union).
Contract difference here: equal memberships, different derivation
contracts — the former is the hand-maintained strategy vocabulary (the
validator + this gate read it); the latter is derived from the encoder's
payload-shape memberships so "validatable on a filter" cannot drift from
"emitted by the encoder" (its comment states the derivation; it is never
hand-edited). A fourth strategy hand-edits the vocabulary + shape sets
and the union follows by construction — C9 moves one hand-edit, not two
definitions. Fresh rejection, no prior verdict. Trigger to reconsider: a
hand-edit to the union, or a strategy landing in one set but not the
other, would make them two vocabularies. Durable home: the derivation
comment at [filters-base][filters-base] :64-68 (already states it). No
separate index row (carried here).

### F5 — mint tail + signature (file-local)

- **Contract + variation.** For a string strategy the helper mints the
payload through the exact live code path — `encode_typename(definition,
strategy, type_cls, None)` (the comment records why `None` is safe: only
the gated-out `callable` branch touches `root`) — then encodes via
Strawberry's own `relay.GlobalID(type_name=payload, node_id=str(id))`.
The `id: object` parameter accepts `int` / `str` / `UUID` (stringified),
following the package-wide wire-name parameter convention (`id` +
`# noqa: A002`, shared with the mutation/form/serializer decoders and the
node field — 13+ sites). Legitimate variation: accepted id types, the
`None`-root assumption.
- **Sites + roles.** *Definition*: this file (HEAD :52 + :105–110) — the
sole `GlobalID(` construction package-wide (census: exactly 1 site).
*Slot owner*: `encode_typename` ([types-relay][types-relay]); *encoding
owner*: Strawberry's `GlobalID.__str__`. *Oracles*: the two
strategy-equality oracles (live wire id == helper output — proving the
`None`-root call rides the live path), the id-types oracle (int/str/UUID
round-trips), the two live-tier tests (model-label mint + secondary
asymmetry over HTTP). All independent: they compare against wire bytes
and manual base64, never read the mint body.
- **Challenges.** C11 → 1 at the slot owner, 0 here; C12 → 0 here; C13 →
1 here.
- **Owner + lifetime.** This function for the tail (sole construction
site); the slot and encoding stay at their owners. No stored derivation.
- **Migration.** None (zero-edit item).
- **Distinct behavior.** Caller-supplied-pk stringification vs resolved
row-value stringification ([types-relay][types-relay]`::_resolve_id_default`,
`::_order_nodes` coerce resolved row attrs) — J5 records the split. The
`id` name shadows the builtin deliberately (wire-name convention, noqa
present — no prior index row; the shape is noted here, not routed).
- **Behavioral proof.** `static-reviewed`. Rejects "the helper re-derives
the payload" (C11: it calls the live path) and "the `None` root is
assumed" (the strategy-equality oracles execute both paths and compare
bytes).
- **Structural gate.** Gate-only justification: the equality oracles fail
on any payload divergence (live vs helper); the id-types oracle fails on
any coercion narrowing. A hand copy mints identically (correct copy) —
singularity needs no gate because the census (1 site) + the live-path
call make a second mint self-contradicting. No bespoke gate owed.
- **Coupling.** None.
- **Freshness.** Target HEAD `df0dc72a…`, [types-relay][types-relay] HEAD
`52439862…`, [test-relay][test-relay] HEAD `55e43ed2…`,
[test-library-api][test-library-api] HEAD `1f107fff…` (worktree
`2cd1b6dd…` — judged regions: the two relay tests + helper at HEAD
bytes), Strawberry `relay.GlobalID` (installed contract anchor, not a
fingerprinted input).

### F6 — submodule manifest + re-export (file-local)

- **Contract + variation.** The submodule's public surface is exactly two
names: `decode_global_id` (the public re-export of
[types-relay][types-relay]`::decode_global_id` — same uniform
`ConfigurationError` contract, same `(target_type, node_id)` return; the
internal signature is already consumer-shaped, so no wrapper exists) and
`global_id_for` (defined here). `__all__` mirrors the two bindings
in-file; the import block pays `types`-package + Strawberry costs only
for importers of this submodule. Legitimate variation: set membership
only.
- **Sites + roles.** *Definitions*: [types-relay][types-relay]`::decode_global_id`
(re-exported) + member 7 here. *Consumer rows*: member 5 + member 6.
*Oracle*: the decode-identity assertion (`testing_relay.decode_global_id
is types_relay.decode_global_id` — independent: an identity probe, never
reads a body) + the round-trip assertions riding the re-exported name.
*Projections*: the module docstring's re-export bullet, the
[testing-init][testing-init] withholding bullet, [docs-readme][docs-readme]
line 244, the [glossary][glossary] entry.
- **Challenges.** C14 → 1 here (leaf 0 — proves the withholding is a leaf
rule, converging with the verified F2/C7 direction); C15 → 1 here.
- **Owner + lifetime.** Per-symbol home modules (existing owners by
responsibility). This file is a consumer for `decode_global_id`
(principle 6: compose by name — a re-export, not a wrapper, per
Decision 10). No stored derivation.
- **Distinct behavior.** Plain-import + `__all__` membership (this file)
vs the redundant-alias idiom (`X as X`, e.g. the `SyncMisuseError`
re-export in [types-relay][types-relay]): both mark re-export to the
linter; the choice is per-module style with no behavioral delta — noted
here, not routed (no consolidation could change behavior; trigger: a lint
rule forcing one idiom). The withheld-from-leaf posture is owned at the
leaf (verified F2), not here.
- **Behavioral proof.** `static-reviewed` (identity assertion read at
HEAD bytes, not executed). Rejects "the re-export wraps" (identity is
`is`, and C15 shows a wrapper breaks it).
- **Structural gate.** Gate-only justification: the identity oracle pins
re-export-not-wrapper on every suite run; consumer imports resolve
explicitly, so a dropped binding fails loudly. No bespoke gate owed.
- **Coupling.** F1–F5 (a `global_id_for` contract change moves the
manifest's defined half, never the re-exported half).
- **Freshness.** Target HEAD `df0dc72a…`, [types-relay][types-relay] HEAD
`52439862…`, [testing-init][testing-init] `48b45d1b…` (clean),
[test-relay][test-relay] HEAD `55e43ed2…`, [spec-032][spec-032]
`1e96ad41…` (clean; Decision 10 + DoD + exports-list note),
[spec-043][spec-043] `a31a06f1…` (clean; Decision 4),
[docs-readme][docs-readme] HEAD `1497164f…` / worktree `30978c34…`
(line 244 byte-identical, `cmp`-verified), [glossary][glossary]
`3413edc3…` (clean). Dotted-path consumer census: 7 import lines across 6
files under `tests/` at HEAD bytes + 4 live-tier files (worktree read;
matches the W2-refined N1 census of 10 statements + the submodule line) —
all resolve without the leaf.

### F7 — module contract prose (rejected)

- **Contract + variation.** The member-0 docstring states the public-path
rule, the per-strategy payload table, the finalize-first + encode-only
rationales, and the secondary-emitter asymmetry. The shared form
considered: the docstring as a second contract source beside
[spec-032][spec-032] Decision 10.
- **Sites + roles.** *Contract source*: Decision 10 (owns every sentence
— payload table, asymmetry equation, export gate, audience). *Projection*:
this docstring (0 definitions: every mechanics change moves code/spec,
prose follows — C16). *Oracles*: the package + live suites pin the
mechanics, never read the prose.
- **Challenges.** C16 → 0 definitions here under every posited prose
change.
- **Owner + lifetime.** [spec-032][spec-032] Decision 10 (existing owner).
No stored derivation.
- **Migration.** None (zero-edit item).
- **Distinct behavior.** Verified sentence-by-sentence against bodies at
HEAD bytes: strategy table matches `encode_typename` arms; finalize-first
matches the gate + stamp phase; encode-only rationale matches the
`(type_cls, model, root)` signature; asymmetry equation matches decode
Step 1 (`registry.get(model)`) + the secondary live oracle; the
import-light passage matches the verified withholding (with the leaf's O1
looseness — the `types` clause overstates, inherited verbatim from
Decision 4; observed there, not re-filed).
- **Behavioral proof.** `static-reviewed`. Rejects "the prose duplicates
the rules" (C16 proves zero definitions under every change).
- **Structural gate.** Gate-only justification: prose drift is caught by
reading (done this pass, above), not by a mechanical oracle; a bespoke
prose-equality test would violate the gate-only economy (principle 9).
- **Coupling.** None.
- **Freshness.** Target HEAD `df0dc72a…`, [spec-032][spec-032]
`1e96ad41…`, [testing-init][testing-init] `48b45d1b…`.
- **Rejection.** Contract difference: submodule-audience contract summary
(what the helpers promise + where to import them, moving with the helper
contract) vs the spec's decision record (why the surface exists, moving
on design changes) — C16 proves opposite move sets with zero package
definitions under every prose change. Trigger to reconsider: the
docstring starts stating rules the spec doesn't (then it becomes a second
contract source — fold back into the spec). Durable home: Decision 10
(already the full contract) + this artifact. Named for Worker-0 as
rejected index row `testing-relay-contract-prose-vs-spec-decision` (no
such row exists in the current plan).
- **Rejection (nested, CONVERGE).** The import-light passage vs the
[testing-init][testing-init] withholding bullet: CONVERGE with the
verified `testing-relay-withholding-prose-pair` direction on fresh
evidence — trigger re-checked at HEAD bytes (neither passage has grown
the other's audience rule: the leaf bullet names no helper semantics
beyond the one-line mint/decode shape, the relay passage names no leaf
export set) — unfired. No separate index row (carried by the existing
verified row).

### J1 — site `except` vs a shared guard driver (rejected)

Considered: driving this file's `except BaseException` (HEAD :70–71)
from one shared guard body with the package's other contained reads
([list-field][list-field]'s `except Exception`, the 85-site population
behind the standing direction). Contract difference here: this `except`
is the proof's own fail-closed arm (a `BaseException` anywhere in the
subclass/attribute/registry reads means "cannot be PROVEN registered" —
the hostile-`__getattr__` oracle pins `RuntimeError` containment), with
site-chosen scope (whole-proof, `BaseException`) vs the list-field base's
read-only, `Exception` scope — C3 proves the scopes already differ per
site — vs [types-base][types-base]`::_meta_attr`'s re-raise-as-`ConfigurationError`
posture (a third shape: contain-then-raise, neither `False` nor bare
pass-through). CONVERGE with the verified `_request_body.py` J1
shared-except-guard direction on fresh evidence (this site's own scope
difference re-derived above). Trigger to reconsider: a shared driver
parameterizing scope + covered region without a mode flag would make the
sites one rule. Durable home: the standing J1 row. Named for Worker-0 as
rejected index row `testing-relay-except-guard-vs-shared-guard` (no such
row exists in the current plan). Freshness: target HEAD `df0dc72a…`,
[test-relay][test-relay] HEAD `55e43ed2…`. (Coupling: moves with F1.)

### J2 — slot reads vs shared truth readers (rejected)

Considered: reading `__django_strawberry_definition__` / `origin`
through shared identity readers instead of `getattr`-with-default.
Contract difference here: at HEAD bytes the reads ARE plain
`getattr`-with-`None`-default inside whole-proof `BaseException`
containment (the site's whole contract — a `None` feeds the typed reject;
the hostile oracles pin both raising shapes) — and no shared reader
exists at HEAD (`utils/truth.py` verified absent from the HEAD tree; the
gate config + checker script absent too, so no HEAD gate constrains the
shape either). The verified `testing-wrap-slot-read-vs-truth-readers`
rejection was checked as prior input: its difference (live-slot `AttributeError`
vs default-returning static read changing install behavior) does not
transfer — here a `None` from either shape feeds the same typed reject,
so the shapes coincide observably. Fresh rejection at HEAD, no prior
verdict covering it. Trigger to reconsider: a shared identity-reader
module landing in-tree (the worktree's untracked `truth.py` + this
file's worktree migration are concurrent work — fingerprinted, unjudged)
plus a spec row redefining the hostile-input contract would reopen the
read shape. Durable home: [spec-032][spec-032] Decision 10 + the hostile
oracles. Named for Worker-0 as rejected index row
`testing-relay-slot-reads-vs-truth-readers` (no such row exists in the
current plan). Freshness: target HEAD `df0dc72a…`, HEAD tree (absence
verified by failed `git show HEAD:` + empty census). (Coupling: moves
with F1.)

### J3 — stamp-`None` gate vs the interface predicate (rejected)

Considered: gating the helper on `_is_relay_shaped` (declared
`Meta.interfaces`) instead of the finalize-stamped strategy, unifying
with the field fifth-guards ([list-field][list-field]`::_validate_relay_djangotype_target`,
[root-relay][root-relay]`::_validate_node_target`). Contract difference
here: the stamp is post-finalize classification (written in Phase 2.5
only for Relay-Node-shaped types — absence after finalization IS the
non-Relay verdict, C18 refused), while the predicate is pure over
`(cls, interfaces)` declaration inputs (body read: an `issubclass`
disjunction over the tuple plus the class — no registry, no finalize
state — driving creation-time and annotation-time call sites).
Different lifecycle phases,
different inputs (a presented-for-minting class vs a
being-constructed field target), different timing — C18 forces opposite
move sets. Fresh rejection, no prior verdict. Trigger to reconsider: a
single Relay-shapedness predicate valid at both phases would make the
sites one rule. Durable home: the stamp-slot contract at
[types-definition][types-definition] + this artifact. Named for Worker-0
as rejected index row `testing-relay-stamp-gate-vs-interface-predicate`
(no such row exists in the current plan). Freshness: target HEAD
`df0dc72a…`, [types-base][types-base] HEAD `dda91365…`,
[list-field][list-field] HEAD `21380eb7…`, [root-relay][root-relay] HEAD
`c3c5aea5…`.

### J4 — finalized gate vs the CLI finalized check (rejected)

Considered: unifying with [inspect][inspect] `:151–157` (`definition is
None` → `CommandError`, `finalized is False` → `CommandError`). Contract
difference here: the CLI check guards table-printing (different error
surface — `CommandError`, different remediation — none, no stamp read,
no canonicality proof), while this gate guards minting with a
finalize-first remediation + Phase-ordered stamp read. Different
surfaces, different remediations, C19 forces opposite move sets — and no
contract source requires canonicality at the CLI (its target resolves
through the registry by construction), so axis 6 files no defect. Fresh
rejection, no prior verdict. Trigger to reconsider: a shared
definition-lifecycle guard vocabulary across CLI + helpers would make
the sites one rule. Durable home: this artifact. Named for Worker-0 as
rejected index row `testing-relay-finalized-gate-vs-cli-check` (no such
row exists in the current plan). Freshness: target HEAD `df0dc72a…`,
[inspect][inspect] HEAD `2807d0fc…` (worktree `bb63204c…`).

### J5 — mint coercion vs row-id coercions (rejected)

Considered: unifying `node_id=str(id)` (HEAD :110) with the row-id
`str()` sites ([types-relay][types-relay]`::_resolve_id_default`,
`::_order_nodes`, the `coerced_keys` comprehension). Contract difference
here: this call stringifies a caller-supplied pk of unknown type
(`int`/`str`/`UUID` per the id-types oracle) at mint time with no row in
scope; those calls stringify resolved row attributes (dict/cache reads
keyed on the id attr) at serve time. Different inputs, different timing,
C20 forces opposite move sets (a UUID rejection moves here alone; a
cache-key change moves there alone). Fresh rejection, no prior verdict.
Trigger to reconsider: a shared node-id-stringification helper with
callers at both phases would make the sites one rule. Durable home: this
artifact. Named for Worker-0 as rejected index row
`testing-relay-mint-coercion-vs-row-coercions` (no such row exists in the
current plan). Freshness: target HEAD `df0dc72a…`,
[types-relay][types-relay] HEAD `52439862…`, [test-relay][test-relay]
HEAD `55e43ed2…`.

## Defects

D1 (minor, HEAD, owner: File `types/base.py` — undispatched): the
Relay-gate census comments at [types-base][types-base] HEAD :113–125
undercount their compose sites. The LEAD comment claims "the three
`Meta`-key gates (`Meta.connection`, `Meta.globalid_strategy`,
`Meta.relation_shapes`)"; the TAIL comment claims "byte-identical at
three compose sites" naming "the connection / globalid gates here and
`global_id_for`". Executable census at HEAD bytes: LEAD composes at
FOUR in-file gates (`Meta.connection` :260, `Meta.cursor_field` :308,
`Meta.relation_shapes` :360, `Meta.globalid_strategy` :431) plus this
helper; TAIL at FOUR sites (the same minus `relation_shapes`, plus this
helper). Both comments omit the `Meta.cursor_field` gate. Stale from
birth: `51421e54` introduced the constants, the "three" census, AND the
cursor-field gate in one commit (verified via `git show 51421e54:` —
the census already said "three" beside the fourth site). No behavior is
affected (composition by name holds at all four sites — F3); the hazard
is a reader trusting the census and missing the cursor-field site when
changing the literal. Unfixed (file items never fix; the types/base.py
item owns the wording). Freshness: [types-base][types-base] HEAD
`dda91365a7e8cb146d718b6f61b95e4821d6a555`.

No defect in the target itself. Every docstring claim was verified
sentence-by-sentence against HEAD bodies (F7 Distinct behavior); the
`except BaseException` scope violates no HEAD-configured gate (the
truthful-reads gate does not exist at HEAD — verified absent); the
`id` builtin shadow follows the package-wide wire-name convention with
its noqa present; O1 (F4) and the leaf's O1 (F7) are unreachable/looseness
observations breaking no contract row.

## Pending execution

None. No `execution-deferred` proof: every verdict rests on HEAD-byte
body comparison, whole-tree census greps, and oracles the suite already
pins; no behavior exists that an execution could distinguish and the
cited oracles do not already cover. Sharded / Postgres cells are
inapplicable by construction: the target reaches no database, alias, or
dialect decision (registry + pure string work only).

## Judgment

File item with one genuine cross-file candidate: seven rules traced,
F1 routes to the holding family
`registered-djangotype-definition-validation` (C1–C3 force two
definitions, currently diverged on containment scope), F2–F6 stand
file-local with proving challenges (four lawful consumer postures + the
submodule manifest), F7 + J1–J5 are rejections with contract differences
+ triggers (two convergences on fresh evidence, four fresh). One minor
HEAD defect filed against File `types/base.py` (stale census comment,
D1). Enumeration covers 8/8 statements; all six matrix axes discharged
against the target's real surface. No defects in the target, no pending
execution, no production edits.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs
`ITEM_BASELINE=f3d68581b263471b1414db121d28d73e42da2b53`: `git diff
<baseline> -- django_strawberry_framework/testing/relay.py` is empty —
the HEAD-vs-worktree dirt on the target predates the baseline window
and was never touched; the 7 paths changed in the window
(`_strawberry_patches.py`, the plan, the review plan, two live-tier
tests, two package tests) are all concurrent work outside this item,
left alone. The `## Owned changes` ledger gains no row from this item
(no row names the target; verified by reading). The artifact itself is a
new untracked file, the item's only output. No `uv run ruff` run (no
`.py` touched; `.md` is outside ruff format scope; no `.py` scratch
created). No shared-tree pytest run (static review + pinned oracles
suffice — see `### Challenges` note). No workspace runs. No
`docs/dry/temp-tests/` scratch created. No commit.

Worker-0 instructions: (a) tick the plan item `File testing/relay.py`
as verified under Run `0.0.15 2026-09-28-7` once Worker 2 agrees; (b) add
the twelve `## Responsibility index` rows under `## Index rows for
Worker-0` verbatim (1 open family row with holding item
`Family registered-djangotype-definition-validation`, 5 file-local +
6 rejected with holding item `File testing/relay.py`); (c) add the
`## Families` item under `## Families`. Home D1 on its owning card at
closeout (owner: File `types/base.py`). No commit.

## Index rows for Worker-0

| `registered-djangotype-definition-validation` | TBD by family item (candidates: `django_strawberry_framework/registry.py` via a `registered_own_definition` predicate, or `django_strawberry_framework/list_field.py::_validate_djangotype_target` as the shared base; reconcile scope with verified `relay-node-target-guard`) | `django_strawberry_framework/testing/relay.py`, `django_strawberry_framework/list_field.py` | Family `registered-djangotype-definition-validation` | open |
| `testing-relay-finalized-gate-and-stamp-read` | `django_strawberry_framework/testing/relay.py::global_id_for` (finalized-first gate + stamp read, never the setting; lawful convergence onto the `globalid-setting-snapshot` reader posture, T-reader/T-compute/T-lifetime re-checked unfired) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | file-local |
| `testing-relay-non-node-gate-composition` | `django_strawberry_framework/types/base.py` (constants; this helper composes `_RELAY_NODE_GATE_LEAD` + `_RELAY_NODE_GATE_INHERIT_TAIL` by name) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | file-local |
| `testing-relay-encode-only-refusal` | `django_strawberry_framework/testing/relay.py::global_id_for` (callable/custom live-root refusal + absence-based membership; nested R-A/R-B rejections carried here) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | file-local |
| `testing-relay-mint-tail` | `django_strawberry_framework/testing/relay.py::global_id_for` (sole `GlobalID(` construction via the live `encode_typename` path + `str(id)` tail + wire-name signature) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | file-local |
| `testing-relay-submodule-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/testing/relay.py`: 1 re-export + 1 definition) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | file-local |
| `testing-relay-contract-prose-vs-spec-decision` | `django_strawberry_framework/testing/relay.py` (rejection recorded here; 0 definitions — projection of spec-032 Decision 10; CONVERGE with verified `testing-relay-withholding-prose-pair` on the import-light passage, trigger re-checked unfired) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | rejected |
| `testing-relay-except-guard-vs-shared-guard` | `django_strawberry_framework/testing/relay.py::global_id_for` (rejection recorded here; CONVERGE with the verified `_request_body.py` J1 shared-except-guard direction on fresh evidence) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | rejected |
| `testing-relay-slot-reads-vs-truth-readers` | `django_strawberry_framework/testing/relay.py::global_id_for` (rejection recorded here; fresh at HEAD — no shared reader exists in the HEAD tree; verified `testing-wrap-slot-read-vs-truth-readers` checked, non-transferring) | `django_strawberry_framework/testing/relay.py` | File `testing/relay.py` | rejected |
| `testing-relay-stamp-gate-vs-interface-predicate` | `django_strawberry_framework/testing/relay.py::global_id_for` (rejection recorded here; fresh pair — post-finalize stamp vs pre-finalize declaration, no prior verdict) | `django_strawberry_framework/testing/relay.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/relay.py` | File `testing/relay.py` | rejected |
| `testing-relay-finalized-gate-vs-cli-check` | `django_strawberry_framework/testing/relay.py::global_id_for` (rejection recorded here; fresh pair — mint guard vs table-print guard, no prior verdict) | `django_strawberry_framework/testing/relay.py`, `django_strawberry_framework/management/commands/inspect_django_type.py` | File `testing/relay.py` | rejected |
| `testing-relay-mint-coercion-vs-row-coercions` | `django_strawberry_framework/testing/relay.py::global_id_for` (rejection recorded here; fresh pair — caller-supplied pk vs resolved row value, no prior verdict) | `django_strawberry_framework/testing/relay.py`, `django_strawberry_framework/types/relay.py` | File `testing/relay.py` | rejected |

## Families

One. Worker-0 must add the family item
`Family registered-djangotype-definition-validation`
(`dry-rule-registered-djangotype-definition-validation.md`), queued after
the standing family queue: two proof definitions (this file's step-1a
block + `list_field.py::_validate_djangotype_target`), scope to reconcile
with verified `relay-node-target-guard`, structural gate owed by the
family item (proof-mechanism census, closed here at exactly 2).

## Independent verification (Worker-2)

### Own trace (HEAD bytes; homes chosen before reconciling)

Instrument reproduced: `ast.Module.body` over HEAD blob
`df0dc72a178854e261fa7236c6614a758a008722` = 8 members (docstring,
5 `ImportFrom`, `__all__` assign, `global_id_for`). My homes: member
0 → projection, no definition (reject as contract source); member 1
(`relay`) → mint-tail consumer; member 2 (`ConfigurationError` +
`_safe_arg_repr`) → raise-vocabulary consumers; member 3 (`registry`)
→ proof consumer; member 4 (gate pair + strategy set + `DjangoType`)
→ proof/gate/membership consumers; member 5 (`decode_global_id` +
`encode_typename`) → re-export + slot consumers; member 6 →
manifest, file-local; member 7 → one holding family (step-1a proof)
+ four file-local rules (finalized gate + stamp read, `None` gate,
encode-only refusal, mint tail + signature). Twin hunt closed by my
own sweep: `origin`-identity against a presented class exists at
exactly two sites (this block + [list-field][list-field]`::_validate_djangotype_target`),
and only this pair co-locates the registry-identity arm; `optimizer/extension.py`
reachability, `connection.py` cache provenance, `types/resolvers.py`
metadata read, the finalizer loop skips, the CLI check, and the
duck-typed mutation guard are non-proofs by body strength (plus
`filters/sets.py` owner-resolution read, likewise a non-proof).
Posited changes: drop the own-definition arm → 2; drop the
registry-identity arm → 2; unify containment → 2 bodies, diverged
(`BaseException` whole-proof here vs `Exception` read-only there).
Owner I would choose: the family item decides; lightest valid home
is a registry-side predicate (dependency direction beats the
heavyweight field module, whose import weight this helper's docstring
promises to avoid). Reconciliation: no difference from the artifact
in enumeration, homes, counts, or owner direction. Two record
corrections below; neither moves a verdict.

### Per-area verdicts

- Enumeration: AGREE (8/8 member-by-member; instrument + count reproduced).
- Matrix: AGREE all six (axis 2 no-twin verified by full read;
`relay.GlobalID(` census = 1 site; executable `from_id` = 2 sites;
`utils/truth.py` + checker + config verified absent at HEAD).
- New family: AGREE (count 2, tested hard both directions — helper
side: non-subclass / hostile-repr / inherited / stale / hostile-getattr;
list-field side: abstract / inherited / fail-closed / fabricated /
copy / dropped; population closed by my own sweep; diverged
containment characterized correctly).
- Convergences: AGREE (withholding-prose triggers re-checked unfired
at HEAD bytes; shared-except scope difference re-derived; snapshot
T-reader/T-compute/T-lifetime unfired via token grep 0;
per-subject-grammar direction; `relay-node-target-guard` scope note
accurate — 0 `testing` mentions, W2-C1 count-1).
- Rejections: AGREE all six (contract difference + trigger + durable
home each). J4 sharpening: "resolves through the registry by
construction" holds for bare-name resolution only — dotted-path
targets arrive via `import_string` and can present an inherited
definition; no contract source requires canonicality at the CLI and
the worst case is a mislabeled operator table, so the no-defect
verdict stands.
- D1: ENDORSE as filed (minor, File `types/base.py`) with corrected
provenance: NOT stale-from-birth — `d418e649` introduced the
constants + "three" census when exactly 3 sites existed; `51421e54`
added the `cursor_field` gate without updating (stale-by-addition).
HEAD undercount verified (LEAD 4 in-file + helper; TAIL 4). GOAL
trust-boundary: DRY prose/body-contradiction defect,
behavior-unaffected (composition by name holds), hazard is a future
reader missing the 4th site. Worker-0: carry the corrected
provenance when homing.
- Non-findings: AGREE both (truth.py absent at HEAD;
`relay-node-target-guard` census note accurate, correctly not a defect).
- Index rows: AGREE (12 rows match their findings; Families item matches F1).

### Freshness, window, gates

All 17 HEAD fingerprints re-verified byte-exact; `## Pending
execution` None is correct and sharded/pg inapplicable-by-construction
holds (registry + pure string work; the string branches of
`encode_typename` reach no database, alias, or dialect decision).
Zero-edit confirmed (`git diff` baseline → target empty; this
artifact is the item's only output; no `.py` touched → ruff N/A,
confirmed not run). Window attributed hunk-by-hunk: the plan =
Worker-0's own dispatch/submission lines; the 6 concurrent paths =
review-cycle prose-only docstring edits carrying that cycle's ledger
rows — all out-of-scope, left alone. AGENTS.md prose rules hold
(10-header link scaffold, `path::Symbol` citations, HEAD line refs
confined to this scratchpad artifact, no process provenance). No
workspace runs (read-only inspection only); no `(Worker-2)` defects
filed. Verdict: verified.

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
[connection]: ../../django_strawberry_framework/connection.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutation-fields]: ../../django_strawberry_framework/mutations/fields.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[registry]: ../../django_strawberry_framework/registry.py
[root-relay]: ../../django_strawberry_framework/relay.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[testing-wrap]: ../../django_strawberry_framework/testing/_wrap.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-relay]: ../../tests/testing/test_relay.py

<!-- examples/ -->
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
