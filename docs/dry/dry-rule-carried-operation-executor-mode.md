# DRY review: `carried-operation-executor-mode`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule as the holding file item framed it: which GraphQL executor is
driving an operation is a carried per-operation fact, never a sampled one.
A two-member color settled by entry point (`OperationMode`), translated
once from the `sync` flag upstream hands `get_extensions`
(`schema.py::_operation_mode`), carried into the chain the schema built
(`_OperationModeMarker`, admitted and refusal paths alike), read back
once by the runner (`_declared_operation_mode`), bound everywhere the
runner binds state as a lease (`_bind` over `bind_operation_mode`), and
read through the lease (`current_operation_mode`). The ambient event
loop is a different fact that disagrees with this one exactly where a
field must not guess, so no stage samples it.

Verdict: CONFIRM — single-owned, zero-edit. Every stage of the carry
counts at most 1 authoritative definition per posited change
(C1–C8 below); every consumer composes by name; every nearby shape is
excluded with a contract difference + trigger (R1–R12). No production,
test, or doc line moves.

The carry decomposes into six single-owned sub-decisions, re-derived
fresh (stages, not families — no new index rows; see `## Judgment`):

- S1 vocabulary: [exec-mode][exec-mode]`::OperationMode` (`SYNC` /
  `ASYNC`, values `"sync"` / `"async"`).
- S2 flag translation: [schema][schema]`::_operation_mode` — the one
  `sync: bool` to member mapping, at receipt.
- S3 chain carriage: [op-state][op-state]`::_OperationModeMarker`
  (the class) plus its two construction sites, one per chain builder
  ([schema][schema]`::_refused_chain` `:752`,
  [schema][schema]`::_admitted_chain` `:1290`), both consuming S2.
- S4 chain declaration read:
  [op-state][op-state]`::_declared_operation_mode` — exact-type,
  first-found, `None` when no member declares.
- S5a fact-side binding: the lease `ContextVar`
  (`_OPERATION_MODES`), [exec-mode][exec-mode]`::bind_operation_mode`
  (returns the var, the token, and the lease), and
  [exec-mode][exec-mode]`::current_operation_mode` — one composite
  declaration block (`:83–:115`), one oracle group.
- S5b lifetime-side binding:
  [op-state][op-state]`::_RunnerScope.mode` (the slot, `None` for an
  unmarked chain) plus the mode arm inside
  [op-state][op-state]`::_bind` (`:669–:670`: skip when `None`, else
  bind) — composes S5a by name; close + token reset ride the shared
  `_Binding` lifecycle both colors already use.

Consumer census (whole package, re-derived fresh at WT bytes; held by
the queued F2/F3 families, listed here as boundary, never counted):
`async_execution` — 17 calls in 8 files (`types/resolvers.py` 6,
`types/relay.py` 2, `connection.py` 2, `relay.py` 2,
`list_field.py` 2, `mutations/fields.py` 1, `auth/mutations.py` 1,
`schema.py` 1); `operation_is_async` — 2 calls in 2 files
(`connection.py:2155`, `list_field.py:1735`, both as the caller's
`async_executor=` answer). Every site calls by name; none restates a
verdict. (The file item's Worker-2 counted 5 `types/resolvers.py`
calls; HEAD and WT both carry 6 calls + 1 docstring mention there —
record note, verdict-neutral; the F2 item owns that census.)

Concurrency: all three indexed files fingerprinted at task start; pins
match dispatch exactly (`exec-mode` WT `b86a08cd` / HEAD `b86a08cd`,
CLEAN; [schema][schema] WT `7390c985` / HEAD `f3b6df8f`;
[op-state][op-state] WT `5f6f255d` / HEAD `009714fd`). Dirt attributed
by diff content vs `git show HEAD:<path>`, nothing edited, reverted,
or tidied:

- [schema][schema] (68-line diff): the f47 ledgered owner import +
  `_refusal` composition (`coded_error_extensions` — the one hunk this
  item could build on, untouched); everything else concurrent — the
  truth migration (`describe_value` → `truth.describe`,
  `issubclass(type(...))` → `truth.is_*`, `_is_class` deletion,
  `truth.static_attr` for `_mutation_meta`, the `_stream` narrowing
  simplification) plus docstring prose rewords. Zero added/removed
  lines carry a mode token (`OperationMode`, `_operation_mode`,
  `_OperationModeMarker`, `async_execution`, `current_operation_mode`,
  `operation_is_async`, `bind_operation_mode`); the schema
  verdict-critical mode lines are content-identical HEAD-vs-WT
  (translation 1:1, marker construction 2:2 — the full 12-line
  cross-file content check is under F1 `Freshness`).
- [op-state][op-state] (81-line diff): all concurrent truth migration
  (`truth.name`, `truth.is_subclass`, three `# truth: ok own instance
  namespace` markers, the `_binds_operation_state` guard deletion).
  Zero added/removed lines carry a mode token.
- [exec-mode][exec-mode]: CLEAN, WT identical to HEAD.

Baselines: `ITEM_BASELINE=c3bc77f14bf6830121c69c93a0bdf26533a0a0bc`
(resolves, type `commit`); `git diff <baseline> -- <three indexed
paths>` is empty — the tree did not move under this item. HEAD
`dd0b6691` unmoved throughout. Address
`dry/carryop-f48/consolidate` (slot-2; all gate runs there).

Record correction (prior-record note, verdict-neutral): the file item
states the "subscribe is ASYNC" clause holds by upstream construction
because no test row executes it directly. At current bytes the clause
is ALSO pinned behaviorally:
`tests/extensions/test_operation_state.py::test_every_frame_of_a_stream_carries_the_operations_mode`
drives `schema.subscribe` and pins `[ASYNC, ASYNC]` per frame, and the
installed strawberry-graphql 0.324.0 `subscribe` is a thin wrapper
around `stream` (`:1090–:1118`), which calls `get_extensions()` with
the `False` default (`:1158`); the sole `sync=True` call in upstream
is the `execute_sync` path (`:821`).

## Verification

### Matrix

Each axis was searched against the rule's mechanism (the carried
executor fact: enum, flag translation, marker, chain read, lease
bind/read), not the targets' neighbours.

1. Cross-flavor policy mirroring — searched. Executor mode is
   single-surface infrastructure, not a per-flavor policy: no flavor
   mirrors the carry. All 8 dispatch flavors + 2 fact pass-throughs
   consume the readers by name (census above); the only direct
   `OperationMode` users are the carry stages S1–S4 themselves (15
   hits in 3 files, `### Enumeration`). No mirror.
2. Sync/async twins — searched, none of the carry itself. The carry
   has no color: all four `exec-mode` functions are synchronous (one
   bind, three reads) answering ABOUT color. The runner's twin scopes
   (`_BoundScope.__enter__` / `__aenter__`,
   `get_extensions_results` / `get_extensions_results_sync`) each
   compose the one `_bind` — consumers, and their twin-ness is the
   runner-lifetime rule (standing File `extensions/operation_state.py`
   territory), not a second mode definition. The two readers'
   split (refusing dispatch vs statable fact) is the queued F2/F3
   boundary (R11).
3. Derived rather than repeated knowledge — searched. The mode is
   settled once (S2) and carried (S3–S5); it is never re-derived.
   The `"sync"` / `"async"` values are spelled exactly twice, both
   in the enum body (S1 census). Ambient-loop sampling exists only
   at the three `exec-mode` sites (two reader fallbacks + the misuse
   check — F2/F3 substrate, R11). No second derivation.
4. Inverse / round-trip pairs — searched. Two pairs, each half
   single-owned: bind (S5a) vs close + token reset (the runner's
   `_Binding` lifecycle, standing R2 split — lifetime belongs to the
   runner); marker pack (S3) vs chain read (S4) — pack/unpack halves
   of one chain grammar. No scattered half: sole bind call site
   (`:670`), sole chain-read call site (`:915`).
5. Contracts restated in another medium — classified, never counted.
   Oracles: the entry-point matrix (8 rows in
   [test-exec-mode][test-exec-mode]), the lifetime rows (no-marker
   binds none, nested restore, copied-context reads none, per-frame
   binding incl. the subscribe-driven row, cancelled/failed binds
   nothing — [test-op-state][test-op-state]), the chain-shape rows
   (marker last on both admitted and refused paths —
   [test-schema][test-schema] ×3, [test-error-policy][test-error-policy]
   ×1), the enum pin (`test_the_two_modes_are_distinct_members`).
   Every pin spells literals (`"OperationMode.SYNC"`,
   `{"sync", "async"}`, `"_OperationModeMarker"`) without reading the
   owner. Projections: the `exec-mode` module grammar, the runner +
   marker + chain-builder docstrings citing by `path::Symbol`, the
   [readme][readme] entry-point paragraph, the [glossary][glossary]
   `SyncMisuseError` executor bullet (F2 wording half). Each medium
   moves for its own reason.
6. Enforcement by omission — family enumerated, each member checked.
   Chains: admitted + refused — both carry the marker (pinned by all
   4 chain-shape oracles). Runner scopes: operation,
   streaming-result, resume, both result-collection twins — all 5
   compose the one `_bind` (via `_bound` at `:955`, `:972`, `:978`
   and `_BoundScope` at `:795`, `:809`). Chain builders:
   `_admitted_chain` 1 call,
   `_refused_chain` 4 calls, all inside `get_extensions` — no third
   builder. `get_extensions` / `create_extensions_runner`: 1 override
   each, both in [schema][schema]. No `DjangoSchema` subclass in the
   package or `examples/fakeshop/config/` overrides the chain; a
   consumer subclass building its own chain is covered by the
   no-marker oracle (binds none → ambient, upstream's own behavior).
   Zero members lack the carry; no gap.

### Enumeration

Instrument one: AST census `/tmp/f48-census.py` over
`django_strawberry_framework/**/*.py` (120 files, 0 unparseable,
`__pycache__` excluded) for the mechanism vocabulary
(`OperationMode`, `_OPERATION_MODES`, `bind_operation_mode`,
`current_operation_mode`, `_operation_mode`, `_OperationModeMarker`,
`_declared_operation_mode`, `in_async_context`,
`operation_is_nested`), `.mode` attribute reads, `"sync"` /
`"async"` string literals, chain/runner defs and calls. Instrument
two: grep censuses for the adjacent populations (reader consumers,
lease readers, misuse raises, shape detectors, marker tokens,
subclass/re-export closure). Every hit is homed: S1–S5 carry the
rule; R1–R12 carry the exclusions.

| Population | Hits | Home |
|---|---|---|
| `OperationMode` refs | 15 in 3 files (9 `exec-mode` incl. def + 2 compares; 3 `schema` incl. the 2 member loads in the S2 ternary; 3 `op-state` annotations) | S1–S4 |
| `"sync"` / `"async"` literals | 2, both in the enum body | S1 |
| `_OPERATION_MODES` refs | 4 (1 def, 1 set in bind, 1 read + var pass-through) | S5a |
| `bind_operation_mode` calls | 1 (`op-state:670`) | S5a/S5b seam |
| `current_operation_mode` calls | 2 (the two readers) | S5a, R11 |
| `_operation_mode` (schema fn) | 1 def + 2 calls (both marker constructions) | S2/S3 seam |
| `self._operation_mode` (runner attr) | 1 write (`:915`) + 1 read (`:931`) | R8 |
| `_OperationModeMarker` | 1 class + 2 constructions + 1 exact-type read | S3/S4 seam |
| `_declared_operation_mode` calls | 1 (`:915`) | S4 |
| `.mode` reads | 3 (`:376` chain, `:669` + `:670` scope) + 1 init write (`:364`) | S3–S5b |
| `in_async_context` calls | 3, all in `exec-mode` | R11 (F2/F3 substrate) |
| `get_extensions` / `create_extensions_runner` defs | 1 each, both in `schema` | S2/S3 (Matrix 6) |
| `_admitted_chain` / `_refused_chain` calls | 1 / 4, all in `get_extensions` | S3 (Matrix 6) |
| Reader consumers | 17 + 2 calls in 8 + 2 files, all by name | R11 |
| Lease-reader shape lines | 4 sites | R1 |
| `operation_is_nested` | 1 def + 1 aliased consumer | R5 |
| Shape detectors | `is_async_callable` 1 def + 3 code calls; `iscoroutinefunction` direct 5; `is_async_only_iterable` 1 def + 5 value branches | R4 |
| `raise SyncMisuseError` | 5 (4 `querysets` guards + 1 F2 refusal) | R3 |
| `isinstance(result, AsyncIterable)` executor-branch guard | 1 (`_graphql_core_patches:152–156`) | R7 |
| `Marker` tokens elsewhere | pagination "Marker rows" prose only | R9 |
| `DjangoSchema` subclasses / `execution_mode` re-exports / second ContextVar-name spellings | 0 / 0 / 0 | Matrix 6 / S5a |

### Challenges

The rule's variation axes, re-derived fresh: color vocabulary (V1),
entry-point mapping (V2), carry channel (V3), binding lifetime (V4),
absent-marker posture (V5), chain coverage (V6). Counts are
authoritative definitions of the carried fact per sub-decision;
consumers, oracles, and projections that also move are listed, never
counted.

- C1 vocabulary rename (V1: respell `"sync"` / `"async"`): S1 counts
  1 (`OperationMode`); S2–S5 count 0 (member refs, never literals —
  the S1 census proves no literal spelling elsewhere in production).
  Oracles listed: the enum pin spells both literals.
- C2 third executor color (V1+V2: e.g. subscriptions gain their own
  color): S1 counts 1 (member), S2 counts 1 (mapping); S3/S4/S5a/S5b
  count 0 (marker, chain read, bind, and lease read all carry the
  mode opaquely). Consumers listed: the F2/F3 readers each need a
  verdict for the new color (their families' change, not this one's).
  Max per sub-decision: 1.
- C3 refused path drops the marker (V6): S3 counts 1 — that one
  construction only; the admitted construction does not move. The two
  byte-identical lines are independent enforcement sites on
  independently-contracted chains (refusal order vs admitted order),
  not two definitions: the shared translation already lives once in
  S2, and a `_mode_marker(sync)` wrapper would relieve no change
  obligation (a translation change still touches S2 once; a
  membership change still touches one site).
- C4 chain carries two markers (V3): S4 counts 0 — exact-type
  first-found already decides deterministically. (Adversarial shape
  considered: a consumer entry importing the private marker name to
  forge the mode. Deterministic first-found, and fails closed both
  directions — forged SYNC under the async executor raises in every
  `async_execution` reader; forged ASYNC under the sync executor
  returns values that executor refuses to complete. Forging requires
  the deployment's own configuration to import a private name, which
  is outside the supported public API the trust boundary covers —
  no defect filed. See `## Defects`.)
- C5 new runner binding scope (V4: a sixth scope): S5a/S5b count 0 —
  it composes `_bind` / `_bound` by name, as all five existing scopes
  do.
- C6 drop the lease (V4: plain value instead of `OperationLease`):
  S5a counts 1 — the composite (var + bind + read move as one
  declaration block, `:83–:115`, under one oracle group); S5b listed
  as the composing consumer (the `_Binding` pack shape). And the
  inverse axis: "a copied context keeps answering" counts 0 here —
  that change moves `OperationLease.held` (the lease owner's rule),
  not the mode binding.
- C7 unmarked chain binds a default (V5): S5b counts 1 (the
  `scope.mode is None` arm in `_bind`); S4 counts 0 (still answers
  `None`); the raw-schema read posture counts 0 here (F2/F3 readers
  — R11 boundary).
- C8 new upstream entry point (V2: a fifth `get_extensions` caller):
  S2 counts 1 (mapping); S1/S3–S5 count 0. Upstream census
  (strawberry-graphql 0.324.0): exactly 3 callers with fixed flags
  today, so the trigger is precise.

Family-level: every challenge counts at most 1 per sub-decision; a
ninth consumer flavor counts 0 (calls the readers); binding a further
per-operation fact counts 0 (declares a new lease binding composing
`OperationLease` by name).

## Findings

### F1 — the carried operation executor mode (CONFIRM, single-owned, zero-edit)

- **Contract + variation.** Which GraphQL executor drives an
  operation is a carried per-operation fact: a two-member color
  settled by entry point, translated once, carried in the chain,
  bound by the runner as a lease, read through the lease. Varies on
  vocabulary, entry-point mapping, carry channel, binding lifetime,
  absent-marker posture, and chain coverage (V1–V6); never on thread
  or loop state.
- **Sites + roles.** Definitions: S1–S5 above (one vocabulary, one
  translation, one marker class, one chain read, one fact-side
  binding composite, one lifetime-side arm). Consumers: the two
  marker constructions (S3 enforcement sites, independence proved by
  C3), the five runner scopes (S5b enforcement sites), the F2/F3
  readers + their 19 call sites (R11 boundary). Oracles: entry
  matrix (8 rows), lifetime rows (5 groups), chain-shape rows (4),
  enum pin (1) — `### Matrix` axis 5. Projections: module + runner +
  marker + chain-builder docstrings, the README entry-point
  paragraph, the glossary executor bullet (F2 half).
- **Challenges.** C1–C8 above: every change counts at most 1
  definition per sub-decision, 0 for a new consumer or a new leased
  fact. The end-to-end coherence pin: one oracle row
  (`test_a_synchronous_operation_is_synchronous_all_the_way_down`)
  spans S1+S2+S3+S4+S5 in a single assertion — the stages are one
  pipeline with one contract, tested as one behavior.
- **Owner + lifetime.** Principle 7: the fact vocabulary + binding
  (S1, S5a) live in [exec-mode][exec-mode] — the neutral leaf every
  legitimate consumer already depends on (`schema`, `op-state`, and
  all 8 reader-consumer files import from it). The translation (S2)
  stays at receipt in [schema][schema] (the `sync` flag arrives at
  `get_extensions`; moving it would add a hop with no second reader
  — standing R6). The carriage + lifetime (S3–S4, S5b) stay with the
  runner in [op-state][op-state] (close/reset timing belongs to the
  operation lifetime — standing R2). No single module can own all
  three stages without reversing a dependency: `exec-mode` cannot
  see the flag, `schema` has no lifetime authority, and moving the
  vocabulary into `op-state` would make 8 files import
  extension machinery for a leaf fact. Lifetime (principle 4): bound
  by the runner per operation across all five scopes, closed + token
  reset on every exit path incl. resumes; nested operations restore
  via token (pinned), copied contexts read `None` after close
  (pinned).
- **Migration.** None — zero-edit. No production, test, or doc line
  moves.
- **Distinct behavior.** The two questions asked of the fact stay in
  their queued families (R11): refusing dispatch (F2) vs statable
  fact (F3). The bind/close split stays (R2); the four lease readers
  stay separate (R1); shape classification stays separate (R4);
  nesting stays separate (R5); the value-shape executor guard stays
  separate (R7).
- **Behavioral proof.** `static-reviewed`. Whole-package AST + grep
  censuses closed at every stage, bodies read, upstream flag mapping
  verified in the installed sources, oracles read (not run — the
  gate owns suite-green; no pytest ran in this item). Nothing
  ordering-, transactional-, or async-sensitive was judged. Wrong
  result (a) "a second definition hides under another spelling" is
  rejected by the mechanism censuses (member loads 4, literal
  spellings 2-in-enum, set sites 1, bind calls 1, chain-read calls
  1, flag translations 1, chain builders 2-with-marker, runner
  overrides 1+1, subclass/re-export/second-var spellings 0/0/0).
  Wrong result (b) "the two constructions are two definitions" is
  rejected by C3 (one moves without the other) + the already-factored
  S2. Wrong result (c) "an unmarked chain binds a stale or guessed
  mode" is rejected by the no-marker oracle (binds none) + the S5b
  arm body + the copied-context oracle (reads none).
- **Structural gate.** None owed. Four plausible bypasses, each
  judged against the gate-only bar (justified population, never a
  bespoke existence test per helper — f21 precedent,
  verifier-endorsed):
  - second binder of the private var: population closable (one
    var), but the bypass is implausible — the var is private, the
    bind returns an undo-triple no second site can honor, and the
    file item + this trace both census exactly one binder. A
    set-census would guard a bypass nobody has a reason to write.
  - second `sync`-to-mode translation: implausible — the flag
    arrives only at the single `get_extensions` override, and
    upstream calls it from exactly 3 fixed sites. The upstream call
    census + single override IS the mechanical closure.
  - sampling `in_async_context` for an executor question: plausible
    (the easiest mistake), but the population is unjustified — the
    same token legitimately answers "may I touch the ORM here" (the
    module docstring's own split), so a call census would redden on
    legitimate reads and get weakened, not fixed. Standing
    enforcement is the docstring grammar + the disagreement oracle.
  - a chain built without the marker: plausible only via a new chain
    builder, whose population is not mechanically enumerable (no
    syntactic shape defines "chain builder"). The 4 chain-shape
    oracles pin both existing paths instead.
  The package-wide censuses in this artifact are the first-run check
  that the rule currently holds, and the in-tree oracles pin every
  contract verdict so a divergent second site fails behaviorally
  where it matters. Negative control reasoned: a hand copy of the
  S2 body passes every behavior oracle (the copy is correct), which
  is exactly why no new oracle is proposed as a gate. No failability
  run is owed: nothing lands, so no divergence exists to prove
  catchable.
- **Coupling.** None. Zero-edit verdict; no finding depends on
  another landing.
- **Freshness.** WT (`git hash-object`) / HEAD (`git rev-parse
  HEAD:<path>`), same-kind pairs: `exec-mode` `b86a08cd` /
  `b86a08cd` (CLEAN), `schema` `7390c985` / `f3b6df8f`,
  `op-state` `5f6f255d` / `009714fd`, `operation_lease` `d1d272c5`
  / `d1d272c5` (CLEAN), `querysets` `6d471bd7` / `adc74b64`,
  `_graphql_core_patches` `efadf7fb` / `b4737d78`,
  `optimizer/_context` `274a138b` / `274a138b` (CLEAN),
  `optimizer/extension` `8e3fe7c1` / `b7b6c434`,
  `resource_policy` `f95f1580` / `9faff1a8`, `utils/typing`
  `1fa47d59` / `defbe7ee`, `middleware/request_body` `1febddbc` /
  `63a9a4a8`, `types/base` `e7a62d32` / `e0ad32aa`, `views`
  `c944b4be` / `fbf00ddf`, `connection` `6c4b01f9` / `38491372`,
  `list_field` `f7b75c2a` / `3842542a`, `relay` `63bbba0b` /
  `037723cd`, `types/relay` `a9b90a17` / `a200f190`,
  `types/resolvers` `5abd9b93` / `2c588030`,
  `mutations/fields` `3368f696` / `0fada991`, `auth/mutations`
  `8d9e8561` / `101dbf82`, `test_execution_mode` `724ed67f` /
  `724ed67f` (CLEAN), `test_operation_state` `d0e1061b` /
  `d4c91208`, `test_schema` `fee39a76` / `ee3e2912`,
  `test_error_policy` `9a72cdb8` / `58129ec2`. Census population:
  120 package files, 0 unparseable. Upstream: strawberry-graphql
  0.324.0 (`schema.py:442` flag default, `:747` / `:821` / `:1158`
  call sites, `:1090–:1118` subscribe wrapper). 12/12
  verdict-critical lines content-identical HEAD-vs-WT. Any
  fingerprint change reopens the finding.

### R1 — the four lease-reader lines (excluded, CONVERGE)

`return None if lease is None else lease.held()` at `exec-mode:115`,
`optimizer/_context.py:251` (CLEAN file), `resource_policy.py:622`,
`op-state:388` — 4 sites, bodies read, each HEAD-vs-WT
content-identical at 1:1. Contract difference: same mechanism,
different rules — executor mode, optimizer frame, request budget,
runner scope, each with its own `None`-contract. The shared semantics
already live once in `OperationLease.held`; a `read_lease(var)`
helper would hide which variable each owner reads while relieving no
change obligation. CONVERGE with the verified File
`utils/execution_mode.py` R1 on fresh evidence (this item's census +
body reads are its own). Trigger: a read-semantics change that must
move all four readers without moving `held` — none exists while `held`
owns the closed-answers-nothing rule.

### R2 — bind/close reunification (excluded, CONVERGE)

Considered: one helper owning both `bind_operation_mode` and the
runner's close/reset. Rejected: close/reset timing belongs to the
operation lifetime the runner owns (per-frame rebinds, adopted
bindings, unwind-on-partial-bind, the `_already_bound` re-entry rule);
the bind deliberately returns "everything that undoes it" so the
runner owns all three. Moving lifetime into the fact module reverses
the dependency (principle 7). Binder census re-derived fresh: exactly
one (`_OPERATION_MODES.set` only inside bind; sole bind call at
`op-state:670`). CONVERGE with the verified File
`utils/execution_mode.py` R2. Trigger: a second binder of
`_OPERATION_MODES` appears.

### R3 — the `SyncMisuseError` raise seams (excluded, CONVERGE)

5 raises: 4 in `utils/querysets.py` (`:223` hook-awaitable, `:526`
async-iterable source, `:3290` sidecar-awaitable, `:4835`
sync-source-awaitable) + 1 F2 refusal (`exec-mode:149`). Contract
difference: the TYPE is shared, the contracts differ — each seam
answers a different misuse with its own recourse wording (the guard
docstrings state the per-seam prose; the write template's own
docstring excludes genuinely different wordings). The carry itself
(S1–S5) never raises; the marker import in `exec-mode` is F2's
substrate. CONVERGE with the verified File `utils/execution_mode.py`
R3 + the rejected `sync-boundary-recourse-wording` family (12
wordings / 9 files, each single-owned). Trigger: a second
executor/loop-disagreement raise appears anywhere.

### R4 — resolver-shape and value-shape classification (excluded, CONVERGE)

`is_async_callable` (1 def in `utils/typing.py`, 3 code calls:
`types/base.py:503`, `connection.py:2210`, `list_field.py:1778`),
bare `iscoroutinefunction` (5: `middleware/request_body.py:147,168`,
`utils/typing.py:221,231`, `views.py:594` — the last selects the
sync/async view wrapper at `as_view()` time),
`is_async_only_iterable` (1 def in
`utils/querysets.py:444`, 5 value branches: the `:525` guard,
`resource_policy.py:1369`, `list_field.py:1311,1315,1731`).
Contract difference: they classify what a callable or value IS
(construction/selection/completion time), never which executor IS
DRIVING (operation time). The separation is pinned at one site:
`list_field.py:1731` branches on the returned value's shape while
`:1735` feeds the executor fact into the same guard — two inputs, two
jobs, one function. CONVERGE with the verified File
`utils/execution_mode.py` R4 on the fresh census. Trigger: a shape
check used AS an executor verdict — branching on what a value is
where the contract needs which executor drives.

### R5 — `operation_is_nested` (excluded, CONVERGE)

1 def (`op-state:391`) + 1 aliased consumer
(`optimizer/extension.py:1126`, imported as `_operation_is_nested`).
Contract difference: runner nesting vs executor color are independent
facts over separate `ContextVar`s — a nested sync operation inside an
async one is SYNC and nested, pinned by
`test_a_nested_operation_restores_the_outer_mode_on_the_way_out` (+ the
`seen["rows"] == [SYNC]` row). CONVERGE with the verified File
`utils/execution_mode.py` R5. Trigger: a consumer needing both answers
as one predicate.

### R6 — flag-translation placement (excluded, CONVERGE)

Considered: moving `schema.py::_operation_mode` into `exec-mode`
(e.g. `mode_from_sync_flag`). Rejected: the `sync` flag arrives at
`get_extensions`, so the translation stays at receipt beside its only
consumer — the two marker constructions on the one schema call path
(S3). A move adds a hop with no second reader. Census re-derived
fresh: still 1 def + 2 calls, both consuming S2. CONVERGE with the
verified File `utils/execution_mode.py` R6 (recorded at the owner,
`schema.py::_operation_mode`). Trigger: a second `sync`-flag to mode
translation need.

### R7 — the executor-branch value-shape guard (excluded, CONVERGE)

`_graphql_core_patches.py:152–156`: `isinstance(result,
AsyncIterable) and not is_iterable(result) and is_awaitable(res)`.
Contract difference: branches on the VALUE being completed (async-only
shape + residual awaitable), never on which executor drives — read
fresh at WT bytes (`efadf7fb`). CONVERGE with the verified File
`_graphql_core_patches.py` rejections (executor-branch guard
predicate vs `is_async_only_iterable`; executor-residual completion
vs awaitable-refusal-and-disposal). Trigger: the guard conditions on
the driving executor rather than the value shape.

### R8 — `self._operation_mode` vs `schema._operation_mode` (excluded, same token)

The runner attribute (1 write `:915`, 1 read `:931`) and the schema
function (S2) share one name. Contract difference: stored declaration
(the mode this runner's chain declared, possibly `None`) vs flag
translation (the mapping from upstream's `sync` bool to a member).
Different inputs (chain list vs bool), different outputs (nullable
stored fact vs total mapping), different owners by responsibility —
same token, not one rule. Both are private to their modules, so no
reader can import one expecting the other. Trigger: either becomes
public, or a single reader needs both the stored declaration and the
translation (then the name must split).

### R9 — pagination "Marker rows" (excluded, same token)

`optimizer/plans.py:1193`, `connection.py:379,515,1365` (spec-033
`limit == 0` window sentinels). Contract difference: page-existence
sentinels in windowed fetching vs the executor-mode chain carrier —
different subject, different mechanism, sharing only the English word
"marker". Trigger: none foreseeable — subjects differ permanently.

### R10 — entry-point selection and transport color (excluded, upstream)

`consumers.py:1186,1194` (`subscribe` / `stream` entry calls),
`views.py` transport arms (incl. the `view_is_async` note at `:586`),
`middleware/request_body.py:147` (`iscoroutinefunction` on the
response callable). Contract difference: these choose WHICH entry
point runs — the flag's cause — while S2 reads the flag (the
effect). Direction differs permanently: selection flows
transport → entry point → flag → S2, and no selection site branches a
resolver return on its own color. Trigger: a transport branching a
resolver return on its own color instead of the carried mode.

### R11 — the two readers as consumers (boundary, held by queued families)

`operation_is_async` (2 calls) and `async_execution` (17 calls) read
the S5a fact and add their own contracts (ambient fallback without
refusal; dispatch with refusal). Boundary: this family owns the fact
they read; the queued Families `async-execution-dispatch-decision`
and `ambient-fallback-executor-read` own the questions. Neither reader
restates the carry — both compose `current_operation_mode` by name
(the only 2 calls). Trigger: a third reader needing a different fact
(a new color, a new absence posture) reopens the vocabulary (S1),
not the readers.

### R12 — the runner's twin binding scopes (excluded, lifetime rule)

`_BoundScope.__enter__` / `__aenter__` (`:795` / `:809`),
`get_extensions_results` / `get_extensions_results_sync` (`:972` /
`:978`), `operation()` / `on_stream_result()` / `resumed()`.
Contract difference: each pair is a sync/async twin of the
RUNNER-LIFETIME rule (hold every binding across this scope in either
color), and each composes the one `_bind` — the mode arm inside it is
S5b, unchanged by the twin-ness. Standing File
`extensions/operation_state.py` territory (verified); this item's
verdict on the twin bodies (both compose one `_bind`) is re-derived
fresh at WT bytes. Trigger: a twin binding the mode by any path other
than `_bind`.

## Defects

None found while tracing. Checks performed for contract: 8
docstring-vs-body pairs read at WT bytes (S2's "execute_sync and
nothing else" vs the upstream call census; the marker's "read once,
by the runner" vs the sole `:915` call site; the "exactly one
marker" clause vs the 4 chain-shape oracles; the module's "around
result collection, every streamed frame, every resume" vs the 5
`_bind` compositions; the runner-scope `None` clause vs the
no-marker oracle; the plain-schema boundary vs the 2 fallback rows;
the lease/token paragraph vs the nested-restore + copied-context
oracles; the `_declared_operation_mode` first-found rule vs the loop
body) — every claim matches its body. The forged-marker adversarial
shape (C4) is deterministic first-found and fails closed both
directions, and reaching it requires the deployment's own
configuration to import a private name — outside the supported
public API the trust boundary covers, so no defect is filed.

## Pending execution

None. Every verdict is `static-reviewed` (closed censuses, body
comparison, upstream source reads, pinned oracles — inspection
decides; nothing ordering-, transactional-, or async-sensitive was
judged). No `proof:` entry: nothing lands, so no failability probe
is owed. No `gate:` entry: zero-edit, no regression witness needed.
No shared-tree pytest ran (no behavioral proof needs execution).
Sharded and PG cells are inapplicable by construction: the traced
surface is enum vocabulary + flag translation + chain-list
membership + `ContextVar` lease binding, reaching no database, alias,
or dialect decision — stated for Worker-2 to judge.

## Judgment

CONFIRM: the carried operation executor mode is single-owned — one
vocabulary, one flag translation, one marker class with two
independently-contracted construction sites, one chain read, one
fact-side binding composite, one lifetime-side arm; eight challenges
counting at most 1 per sub-decision, every consumer composing by
name — and the consolidation is therefore a proved zero-edit
verdict: no tracked file changed, no test added, no `## Owned
changes` row owed. Twelve exclusions carry contract differences plus
triggers (R1–R7 converge on standing rows with fresh evidence, R8–R9
same-token splits, R10 upstream, R11 queued-family boundary, R12
lifetime rule); zero defects; no new index rows.

Worker-0 instructions: (a) tick the plan item Family
`carried-operation-executor-mode` as verified under Run `0.0.15
2026-10-01-11` once Worker 2 agrees, transcribing the family row to
`consolidated` (single-owned: S1–S5 each count ≤1, consumers by
name); (b) no `## Owned changes` row; (c) no new index rows — every
exclusion is a boundary on an existing or queued row, not a family;
(d) the F2/F3 queued families
(`async-execution-dispatch-decision`, `ambient-fallback-executor-read`)
are untouched by this verdict and still own their items.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for
verification). Item-scoped attribution vs
`ITEM_BASELINE=c3bc77f14bf6830121c69c93a0bdf26533a0a0bc`: `git diff
<baseline> -- <three indexed paths>` is empty — all WT-vs-HEAD dirt
predates the baseline window and was never touched; the artifact
itself is a new untracked file, the item's only output. The [plan][plan]
`## Owned changes` ledger gains no row from this item. No `uv run ruff`
run (no `.py` touched; `.md` is outside ruff format scope; census
scripts live in `/tmp`, outside the repo). No shared-tree pytest run
(see `## Pending execution`). No `docs/dry/temp-tests/` scratch
created. Three workspace runs at `dry/carryop-f48/consolidate`
(slot-2, each provenance-fresh, shared tree unmoved since sync), all
green: `basedpyright` 0 errors / 0 warnings / 0 notes
(`dry-20261001T201339-780bd4`), `check_any` 128 uses at 89 sites exit
0 (`dry-20261001T201349-5eb364`), `check_truthful_reads --check`
119 files tier-1 0 / errors 0 (`dry-20261001T201350-7f3b1c`) —
tree-state results matching the run-11 baseline, zero-edit item. No
new cast / `Any` / suppression (no code changed; `ALLOWED_ANY`
untouched). No commit. mypy never run, never cited.

## Independent verification (Worker-2)

Recorded before opening `## Findings`, from Worker-2's own instruments
over all 120 package files (`/tmp/w2_f48_census.py` AST walk: 91 hits;
regex sweeps for literals, subclasses, flag surface, misuse seams).

Sites + roles (Worker-2's own decomposition; W1's stage labels were
unread at this point, mine are X-stages):

- **Vocabulary.** `execution_mode.py::OperationMode` — 1 class def
  (:64); members `SYNC = "sync"` / `ASYNC = "async"` (:72-73) are the
  only `"sync"`/`"async"` literals in the package (grep). No subclass
  (no `OperationMode)` base anywhere). Member refs: `.SYNC` only at
  `schema.py:766`; `.ASYNC` at `execution_mode.py:127,146` +
  `schema.py:766`.
- **Flag translation.** `schema.py::_operation_mode` — 1 def (:756);
  called exactly twice (:752 in `_refused_chain`, :1290 in
  `_admitted_chain`). Already factored: both chains compose it by
  name; no inline `SYNC if sync else ASYNC` anywhere else. `sync:`
  surface is `get_extensions(sync=False)` → both chain builders →
  `_operation_mode`; upstream strawberry is the flag's only author.
- **Marker carriage.** `_OperationModeMarker` — 1 class def
  (`operation_state.py:344`); constructions exactly 2 (`schema.py:752`
  + `:1290`), byte-identical
  `_OperationModeMarker(_operation_mode(sync=sync)),` lines. No
  subclass; no other construction. Each construction sits in a
  distinct chain builder (admitted vs refused chains differ in
  membership and refusal semantics).
- **Chain read.** `_declared_operation_mode` — 1 def
  (`operation_state.py:367`), exact-type first-found; called once
  (:915, runner `__init__`). `.mode` read once (:376); `scope.mode`
  read twice (:669 the `is not None` guard + :670 the bind argument —
  correction during reconciliation: W1's `.mode` row is exact, mine
  undercounted; same S5b arm, count unaffected).
- **Bind primitive.** `bind_operation_mode` — 1 def
  (`execution_mode.py:89`); `_OPERATION_MODES.set(` once (:103,
  inside it); called once (`operation_state.py:670`, inside `_bind`).
  No second mode `ContextVar` (`.get()` once at :114, inside
  `current_operation_mode`).
- **Lifetime arm.** `_bind` / `_unbind` — 1 def each (:642 / :710);
  the five scope entries (`operation`, `on_stream_result`,
  `resumed`, both result-collection overrides) compose
  `_bind`/`_bound` by name. `resumed` re-binds via the registrar;
  no token spans a yield.
- **Readers (consumers of the fact, definitions of their own
  questions).** `operation_is_async` — 1 def (:118), 2 call sites
  (`connection.py:2155`, `list_field.py:1735`, both as
  `async_executor=` to `reject_async_iterable_in_sync_context`).
  `async_execution` — 1 def (:130), 17 call sites in 8 files
  (`types/resolvers.py` 6 at :470,493,723,750,817,890;
  `types/relay.py` 2; `connection.py` 2; `relay.py` 2;
  `list_field.py` 2; `auth/mutations.py`, `mutations/fields.py`,
  `schema.py` 1 each). `current_operation_mode` callers are only
  the two readers (:124, :143) — zero external callers.
  `in_async_context` occurs only in `execution_mode.py` (import +
  3 calls) — no second sampler anywhere.
- **Misuse seam.** `SyncMisuseError` — 1 class def
  (`querysets.py:171`); `raise SyncMisuseError(` at
  `execution_mode.py:149` (SYNC-mode + running loop) plus four
  pipeline-discipline raises in `querysets.py`
  (:223,526,3290,4835); one `except` (`filters/sets.py:3841`);
  re-exports only (`types/relay.py`, `types/__init__.py`, root
  `__init__.py`, `permissions.py`).

Definition counts per posited change (Worker-2's own challenges):

- X1 vocabulary (rename a member / add a third color): count 1
  (`OperationMode`); literal grep proves no second spelling.
- X2 translation (flag meaning changes): count 1 (`_operation_mode`);
  both construction sites compose it and do not move.
- X3 carriage (refused path drops its marker): count 1 (:752); the
  admitted line does not move — and conversely. The two
  byte-identical lines are independent enforcement sites:
  each chain must carry the mode or its operations fall back to
  ambient sampling.
- X4 read (last-found / `isinstance` / read-twice): count 1
  (`_declared_operation_mode`) + its single call site.
- X5 bind (bind without lease / second variable): count 1
  (`bind_operation_mode`) + its single call site.
- X6 lifetime (stop binding on resume / result collection): count
  1 mechanism (`_bind`/`_bound` composition); scope entries are
  enforcement sites, not definitions.
- X7 reader contract (drop a fallback / drop the raise): count 1
  per reader; 2 + 17 consumer call sites compose by name.
- X8 misuse wording (mode-mismatch message): count 1 (:149); the
  four `querysets.py` raises are pipeline-shape contracts with
  separate reasons to change.

Owner Worker-2 would choose: the three-stage split is correct and
no single module can own all three. Vocabulary + bind primitive +
readers live in `execution_mode.py` (importable by both others
without a cycle); translation + construction live in `schema.py`
(alone handed the `sync` flag, alone building the chain); marker
shape + chain read + lifetime live in `operation_state.py` (alone
seeing chain + engine context together, alone binding per-operation
state). Dependency direction (`schema` → `operation_state` →
`execution_mode`) forces it: the flag arrives at the top, the
vocabulary must sit at the bottom.

Matrix discharged against the real surface (Worker-2):

1. Cross-flavor: readers consumed across 8 files, all by name;
   `in_async_context` grep clean outside the owner — no
   flavor-local restatement.
2. Sync/async twins: `_BoundScope` sync/async entries share the one
   `_bind`/`_unbind` primitive; both result-collection overrides
   compose `_bound`. No twin drift.
3. Derived knowledge: no re-derivation of mode from loop, `_meta`,
   or settings anywhere (greps).
4. Round-trip: carry (construct) + read (exact-type scan) halves in
   `schema.py` / `operation_state.py`, one grammar, composed by
   name.
5. Other media: module docstrings are projections; test oracles pin
   behavior without defining mode (oracle identities recorded
   under step 4 below, read-not-run judgment there).
6. Enforcement by omission: chain-builder family
   {admitted, refused} both carry; runner-scope family
   {operation, stream-result, resumed, results x2} all bind. Plain
   `strawberry.Schema` binds nothing by documented contract, not
   omission.

Zero-edit search (Worker-2): item diff vs `ITEM_BASELINE` is the
plan edit alone (verified `git diff --stat`); status 499 = 498 +
the artifact; artifact untracked. Consolidation hunt over the
census: the only textual twin is the X3 pair — independent
enforcement sites, factoring them would merge the admitted and
refused chain contracts. The S2 translation is already factored.
No second definition of any stage in 120 files. Zero-edit
accepted pending steps 2-7 below.

(RECONCILIATION, recorded after reading `## Findings`: see
`## Iterations`.)

## Iterations

### Pass 1 reconciliation (Worker-2, after reading `## Findings`)

Worker-2's X1–X8 converge challenge-for-challenge with W1's C1–C8
(X3 = C3 two-line independence, re-derived with the same
one-moves-without-the-other proof); sites, roles, counts, owner
split, matrix, and zero-edit all agree. Differences, every one
verdict-neutral (W1 bytes intact throughout):

1. `.mode` reads: W1's row (3 reads + 1 write) is exact; my trace
   undercounted `scope.mode` (`:669` guard + `:670` bind argument).
   Corrected in my section above; same S5b arm, count unaffected.
2. `OperationMode` ref tally: my precise AST recount gives 18 refs
   incl. 2 imports (exec-mode 10 = def + 7 annotations + 2
   compares; schema 4 = import + annotation + 2 loads; op-state 4
   = import + 3 annotations) — 16 refs on 15 lines ex-imports.
   W1's total "15" matches the line count; the exec-mode
   sub-count "9" should be "10". Verdict-critical sub-counts (1
   def, 2 compares, member loads, literal census) are exact.
3. Diff-size units: schema "68-line" = changed lines (32+36,
   exact); op-state "81-line" = raw diff output lines (changed
   lines 12+13 = 25). Scene-setting only; attribution verified
   and zero added/removed lines carry a mode token (grep count 0).
4. R7 transcription compresses `_is_awaitable(res, self)` to
   `is_awaitable(res)`; R4's trigger is sharpened vs file-R4
   (compatible, more precise). Both verdict-neutral.
5. Bypass-4's re-check trigger ("no third builder") lives in
   Matrix 6 rather than as a trigger sentence — implicit but
   derivable; durable triggers ride the R-findings.
6. C4's mechanism sketch covers the `async_execution` legs; W2
   verified the `operation_is_async` legs independently (forged
   SYNC → loud typed guard refusal; forged ASYNC → sync-executor
   loud completion failure). "Fail-closed both directions" is
   true as stated; the trust-boundary leg alone grounds the
   dismissal.

Worker-0 points ruled:

- (a) Single-ownership CONFIRMED on reproduced censuses (own AST
  walk over 120 files + regex sweeps: defs 1 each; constructions
  2 with C3 independence; S2 already factored — no inline
  ternary; member loads only in S2 + 2 reader compares; zero
  subclasses/re-exports/second vars). No second definition
  anywhere. Three-stage split agreed — dependency direction
  forces it.
- (b) No-gate ENDORSED. Bypass 1–2 implausible (private var; no
  second flag source — upstream census re-verified: exactly 3
  callers, sole `sync=True` at `execute_sync`). Bypass 3
  plausible but unjustified (a call census reddens on legitimate
  ORM-touch reads; standing enforcement is the docstring grammar
  + the disagreement oracle, verified live). Bypass 4
  unenumerable: every syntactic proxy for "chain builder" reddens
  on correct code (`get_extensions` itself returns
  `list[SchemaExtension]` by delegation — verified) or is
  name-magic. The negative control correctly rules out behavior
  oracles; no composition census has a justified population. The
  f21/f34-precedent application is sound (one body exists;
  census would be machinery; principle-10 clauses + triggers at
  owners). No gate owed.
- (c) Pending-None STANDS → plain. A single-owned zero-edit
  verdict asserts no equivalence (nothing lands, nothing
  blocked), so no `proof:` entry is owed; f46-pass-1's ruling
  targeted blocked CONFIRMs. Static closure decides the count
  verdict. Corroboration per f33/f34 practice, run by W2:
  19 focused oracles `--no-cov`, 19/19 green (entry matrix 8,
  lifetime 6, chain-shape 4 nodes incl. 1 param). Every cited
  oracle verified WT-live with literal-spelling independence.
- (d) Exclusions VERIFIED. R1–R7 converge faithful against
  standing rows (file-R1..R6 texts + triggers match;
  `sync-boundary-recourse-wording` plan row with "12 wordings /
  9 files" exact; R7 homes plan `:351`–`:352` verbatim).
  R8–R12 bodies verified (R8 1-write+1-read both sides; R9
  prose-only with the mechanism census closing it; R10 exact
  lines, selection-time only; R11 queued F2/F3 rows real; R12
  twins compose `_bind`, file item verified). Each carries
  contract difference + trigger + home.
- (e) No-new-rows ENDORSED under the f21/f23/f34
  single-owned-zero-edit precedent (row-less; f46/f47 transcribed
  rows for blocked/landed items — different character). R8/R10
  are non-candidate exclusions (same token / upstream cause),
  R9 prose-only; R11/R12 bound existing rows.
- (f) Forged-marker dismissal CORRECT under GOAL.md: reaching it
  requires importing a private name in deployment config (not
  supported public API; the package does not contain its own
  process's configuration), and no wire input reaches marker
  construction (built from the `sync` flag) — fails the
  defect test, so no defect, no card. Determinism +
  fail-closed-both-directions verified against the chain-read
  body (exact-type first-found; a planted marker shadows
  deterministically) and both reader families' bodies.

Freshness: all 24 pins re-hashed same-kind, exact (3/3 indexed
match dispatch; `exec-mode` CLEAN). Verdict-critical lines
re-diffed HEAD-vs-WT by W2 (13/13 content-identical — translation
def + body, 2 constructions 2:2, 9 op-state carry lines);
W1's 12/12 claim substantiated on W2's superset.

Gates re-run by W2 (shared tree): `ruff format --check` +
`ruff check` on the 3 indexed paths pass (vacuous — zero `.py`
touched); basedpyright 0/0/0; check_any 128/89; truthful-reads
119 files tier-1 0 / errors 0 — all match the run-11 baseline
exactly. mypy never run, never cited.

Record notes judged: types/resolvers 6 (W1 states 6 + notes the
file-item's 5 — accurate, verdict-neutral, no correction);
subscribe-ASYNC pin (verified: test drives `schema.subscribe`
and pins `[ASYNC, ASYNC]`; upstream wrapper + sole `sync=True`
confirmed in installed strawberry 0.324.0) — accurate
prior-record correction, verdict-neutral.

Sharded/PG inapplicable-by-construction ENDORSED (enum +
translation + chain membership + `ContextVar` binding; no
database, alias, or dialect decision). Coupling none. Banned
words vacuous (zero test/production edits; role names in prose
are DRY-required). Defects: none.

Verdict: `verified`, plain. Worker-0: tick Family
`carried-operation-executor-mode` (verified under Run `0.0.15
2026-10-01-11`); family row → `consolidated` (single-owned);
no `## Owned changes` row; no new index rows; F2/F3 queued
families untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[plan]: dry-0_0_15.md
[readme]: ../README.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exec-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[op-state]: ../../django_strawberry_framework/extensions/operation_state.py
[schema]: ../../django_strawberry_framework/schema.py

<!-- tests/ -->
[test-error-policy]: ../../tests/test_error_policy.py
[test-exec-mode]: ../../tests/utils/test_execution_mode.py
[test-op-state]: ../../tests/extensions/test_operation_state.py
[test-schema]: ../../tests/test_schema.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
