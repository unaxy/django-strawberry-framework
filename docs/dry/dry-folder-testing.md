# DRY review: `testing/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights in slot-2 only). Audits the
unassigned remainder of the `testing/` folder and the families that
cross its ownership boundaries at current bytes (HEAD `23b5f421` +
working tree). The four member file artifacts are run-7/run-8 era
inputs, not verdicts: every assignment below was re-derived fresh at
WT bytes, and every assignment the tree has falsified is flagged as a
finding inside this item for the closeout defect-homing pass. No prior
artifact is summarized and no row is reopened.

Verdict: zero-edit CONFIRM. 16 cross-file compositions hold by name
(FC-1..FC-16, each with a fresh census); the f39 consolidation holds
consolidated (owner + 2 consumers + 2 gates, zero residue); the one
already-rowed duplication persists exactly as rowed (f40
`registered-djangotype-definition-validation`, open+blocked — no new
row); 19 merges rejected with triggers (FR-1..FR-19, 7
folder-fresh, 12 converging on standing member rejections whose
bodies + triggers were re-read at current bytes); 9
tree-falsified prior assignments flagged for closeout (FF-1..FF-9,
rows not reopened); 0 FAM-N (the three load-bearing near-misses —
the manifest triple, the raise-type trio, and the slot-read pair —
re-traced fresh and held separate on level-ownership / per-subject
/ live-vs-stored evidence, FR-1 / FR-2 / FR-4); 0 new defects
(client D1 + relay D1 re-verified persisting and riding to closeout;
client D2 closed by a landed spec update); 0 new Family-hold rows
(no consolidation is blocked beyond what the plan already rows).
The 70-row `tests/testing` + `tests/test_multipart.py` suite runs
green in slot-2 at current bytes.

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da`.
`ITEM_BASELINE=f47518d34b02ed7d500b10d74d55b738ea02951b`
(resolves as a commit; the item-scoped diff `ITEM_BASELINE` → WT
over the folder plus `_multipart.py` plus both test files is empty,
so BASE=WT pre-edit for every target). Slot-2
(`dry/folder-testing/consolidate`) verified byte-identical to WT on
all four targets before tracing and again after the witness suite
(the suite wrote no source). Blob fingerprints are `git hash-object`
(WT) and `git rev-parse HEAD:<path>` (HEAD), short-8:

| File | Lines WT / HEAD | WT | HEAD | State |
|---|---|---|---|---|
| `testing/__init__.py` | 64 / 64 | `48b45d1b` | `48b45d1b` | clean |
| `testing/_wrap.py` | 149 / 149 | `4a6c4098` | `4a6c4098` | clean |
| `testing/client.py` | 653 / 656 | `3b122fd5` | `0c166285` | dirty |
| `testing/relay.py` | 120 / 123 | `8a31c1ad` | `f94b3577` | dirty |

Item-scoped diff (`ITEM_BASELINE` → WT over the folder): empty. This
item landed zero edits in slot-2 and zero in the shared tree; the two
dirty files' WT-vs-HEAD hunks are attributed below, none made here.

Cycle-owned untracked: `django_strawberry_framework/_multipart.py`
(`ea88e966`, the f39 owner, ledgered) and
`tests/test_multipart.py` (the f39 gates, ledgered) — both absent
from HEAD by design (new files of a verified-but-uncommitted
family). Hunt-owned untracked: `utils/truth.py` (+ `utils/lazy.py`),
absent from HEAD; the migration is unlanded by definition.

## System trace

The folder owns the consumer test surface end to end: the leaf
manifest (`__init__.py`: 7-name re-export + the relay withholding
by omission), the wrap-time guard leaf (`_wrap.py`: decline-or-
install protocol, non-callable guard, no-restore posture), the HTTP
client family (`client.py`: sibling clients over one generic base,
endpoint ladder, body builder + placeholder walker, transport seam,
login brackets, graphene-shaped mixin + combos, assertion helpers),
and the Relay helpers (`relay.py`: registered-definition proof,
finalized gate, stamp read, non-Relay gate, encode-only refusal,
mint tail, decode re-export). Data flows import → construct →
build → post → decode → assert; mint flows proof → gate → stamp →
encode. Every cross-folder seam (endpoint setting + default,
engine base + `_decode` + field schema, multipart vocabulary,
`_DatabaseFailure` predicate, registry, gate constants + strategy
set, `encode_typename` / `decode_global_id`, the one-sync-boundary
owner, upstream Strawberry / strawberry-django / graphene shapes)
is owned outside and composed by name.

Member-file inputs re-derived at current bytes (not inherited):
[file-init][file-init], [file-wrap][file-wrap],
[file-client][file-client], [file-relay][file-relay]. Where the
tree falsified an assignment the record sits under Findings as FF
(flag for closeout; no row reopened, nothing re-applied). Run-7
blobs (`48b45d1b`, `0df97813`, `d8feebb2`, `df0dc72a`) and the s13
blob (`2466edae`) all resolve in the object store and were diffed
against WT to separate committed evolution from concurrent dirt.

### Attribution of the working-tree dirt (by diff content vs HEAD)

Two provenances. The `## Owned changes` ledger names one
`testing/` path (run-11 f39, verified, uncommitted): the multipart
import block, the guard-set line, and the emission-keys return in
`client.py` match that ledger row by content (f39's "leaf import;
guard set + emission keys compose by name; message line untouched")
and are DRY-owned concurrent work. Every other WT-vs-HEAD hunk is
the concurrent bug-hunt `truth.*` identity-read migration
(import swaps, `_safe_arg_repr` → `truth.render`, `isinstance` →
`truth.is_subclass`, `getattr` → `truth.static_attr`,
`BaseException`/`Exception` arm deletions, prose) — external by
content. Never edited, reverted, or tidied here; the two clean
files carry zero dirt. No ledger row names `relay.py`,
`_wrap.py`, or `__init__.py` (verified by sweeping the ledger
section: the single `testing/` hit is the f39 client row).

- `client.py` (7 `@@` hunks): 1 pure-ledger hunk (H3, the
  emission-keys return) + 2 mixed hunks split by line (H1: the
  5-line `_multipart` import is ledger, the `truth` import swap
  is hunt; H2: the `reserved = set(...)` line is ledger, the
  `truth.render` message line is hunt) + 4 pure-hunt hunks (H4
  docstring sentence deletion; H5/H6/H7 `truth.render`
  retargets; the H6 len-guard arm deletion with its message +
  `from exc` chain).
- `relay.py` (3 `@@` hunks): 0 ledger hunks — all 3 hunt (H1
  the exceptions-import narrowing; H2 the `truth` import; H3
  the proof reshape: `try`/`except BaseException` deleted,
  `isinstance`/`getattr`/`getattr(definition, "origin")`
  retargeted, message render retargeted).

## Verification

### Matrix

1. Cross-flavor: the folder serves ONE subsystem (consumer test
   utilities) with no flavor mirror. The sibling leaves re-read
   fresh (filters eager twin, rest guard-only non-manifest); the
   package root still carries zero `testing` / `TestClient` tokens
   (re-grepped: 0); the three testing modules stay disjoint (zero
   client tokens in wrap/relay, zero wrap tokens in client/relay,
   zero relay tokens in wrap/client — re-swept at WT). The
   `truth.*` read idiom (11 call sites) is hunt-owned migration
   vocabulary, not a package rule (FR-5). Discharged.
2. Sync/async: exactly 2 `async def` in the folder, both in
   `AsyncTestClient` (`query` :511, `login` :541); exactly 3
   `await` expressions, all in that class (:538/:548/:552,
   AST-censused). No cross-file twinship: wrap/relay/init carry
   zero `async`/`await` code tokens; both client colors share
   builder + tail below the color line (FC-4/FC-5). Discharged.
3. Derived knowledge: every same-token population walked on body
   strength. Single owners with by-name composers: the endpoint
   default (1 reader + 1 call site), the multipart names (1 owner
   + 2 consumers + 2 gates), the GlobalID payload (1 slot owner
   + 1 call site), the gate wording (LEAD 5 compose sites:
   4 in-file + the helper; TAIL 4: 3 + the helper), the
   strategy stamp (1 writer + lawful readers), the
   collection guard (1 site + inheritance), the wrap predicate
   (1 def + 2 calls), the installer (1 site in a 4-hit census),
   the mint (1 `GlobalID(` site), the decode (1 re-export),
   the ladder (1 composition + 5 rung participants), the map
   rule (1 comprehension), the triple construction (1 site),
   the intersections (1 folder site of 3). The manifest triple
   (FR-1), the raise trio (FR-2), the coercion pair (FR-3), the
   slot-read pair (FR-4), and the guard trio (FR-6) are distinct
   contracts or per-subject spellings with triggers. Discharged.
4. Round-trip: mint vs decode is one grammar, two halves, with
   the decode half re-exported (identity oracled) and the live
   path composed (no second mint: the `GlobalID(` census is 1);
   emit vs parse stays two bodies with the name set consolidated
   at the f39 owner (FC-3); the wrap has no restore half by
   contract (Non-goal 1, composition-oracled). Discharged.
5. Other media: package oracles (`tests/testing/`, 33 + 9 + 9
   test functions at WT, all green in slot-2 as
   `dry-20261010T053140-241639`; the f39 pair of gates green
   with them; the 5 hunt-deleted hostile rows are concurrent
   deletions, FF-8), live `/graphql` rows (the client/relay
   API suites pin wire behavior), contract sources (spec-032
   Decision 10 intact; spec-043 Decision 8 now current —
   FF-7), projections (module/class/method docstrings; README
   + glossary entries re-read intact; the two persisting member
   D1s ride to closeout per `## Defects` and are never fixed
   here). No medium carries a second definition of a folder
   rule. Discharged.
6. Omission: all four files enumerated below; every member lands
   in a verified family row, a member-artifact assignment
   re-verified at current bytes, or one of this item's
   transcribed rows. The deliberate omissions (relay
   withholding, no restore, no `mutate()`, no `input_data=`)
   each carry a contract source; the one uncovered shape is
   the filed D1. No unassigned member remains. Discharged.

### Enumeration

Instrument: `ast` top-level census (`len(ast.Module.body)`,
def / class / import split) over the folder at WT bytes, plus
`grep` + AST composer censuses for every cross-file read. Every
member below lands in a verified family row (f-numbered), a
member assignment re-verified at current bytes, or one of
this item's transcribed rows (T-numbers in `## Index rows for
Worker-0`).

| File | Top-level members | Homes |
|---|---|---|
| `__init__.py` | 4 stmts: docstring + 2 ImportFrom + Assign | F1/F2 converge (manifest / withholding) + F3 stands (bullets); nested rejections stand (FR-14) |
| `_wrap.py` | 5 stmts: docstring + 3 ImportFrom + 1 def (was 6: the `typing.Any` import deleted by committed drift — FF-1) | F1/F2/F3/F4/F5 converge (protocol / guard / wrap-only / mechanics / prose) + R-A/R-B/R-C/R-D stand (FR-15) |
| `client.py` | 24 stmts: docstring + 11 ImportFrom + 2 Import + If + 2 Assign + 7 classes (was 23: the f39 `_multipart` import added — FF-3; base carries 2 typing-only `@overload` defs — FF-2) | F1..F16 converge (FF-2/FF-3/FF-4 note body evolutions, verdicts intact) + FC1 consolidated (f39, FC-3) + R1..R12 stand-or-refresh (FR-8..FR-13) |
| `relay.py` | 11 stmts: docstring + 7 ImportFrom + If + Assign + 1 def (was 8: +`typing` import +`truth` import +`TYPE_CHECKING` block — FF-5/FF-6) | F2/F3/F4/F5/F6 converge + F7 stands; FAM-PROOF persists open+blocked (f40, FC-14); J1/J2 HEAD-hold + WT-moot (FR-16); J3/J4/J5 stand (FR-17) |

### Challenges

Authoritative definitions only; consumers, oracles and projections
that also move are listed, never counted. Current bytes.

- C1 leaf membership/rename/home-move → 1 at the home module
  (import lines + `__all__` entries follow as consumers).
- C2 root-export lift → 0 here (the root moves; proves
  separation — FR-14).
- C3 withholding lift / sibling growth / path rename → 1 here /
  0 here / 1 at the submodule (the enforcement lives in the
  leaf import block).
- C4 ladder rung / default / non-persistence → 1 here (the
  composition) / 1 at the setting owner / prohibited (pinned
  refusal).
- C5 third color / third extension → 1 new color here + 0 new
  builder defs / 1 per signature, same file.
- C6 wire triple / post shape / operationName / variables gate /
  map rule → 1 here each (envelope emission is single-sited).
- C7 walker container set / index grammar / key type → 1 here
  each (+ D1 on the key type — defect, not second def).
- C8 login arms / session scope → 1 per color, same file (the
  two `finally` arms move together); boundary routing refused
  (FR-8, trigger unfired).
- C9 mixin state / surface / combos → 1 declaration here each
  (zero new machinery).
- C10 assertion checks / message shape → 1 here; msg
  unification refused (structured details vs graphene
  passthrough — FR-12).
- C11 control-field name set (third field, rename) → 1 (the
  f39 owner; both consumers + both gates follow).
- C12 wrap decline posture / guard message / restore support →
  1 here each (the unwrap half untouched; Non-goal 1 retires).
- C13 proof arms / containment scope → 2 (this block + the
  list-field base — f40 persists blocked).
- C14 stamp read / gate order / remediation → 1 here each (the
  stamp writer + fellow consumers untouched).
- C15 gate wording → 1 at the constants owner, 0 here (follows
  by name).
- C16 strategy vocabulary / refusal message → 0 hand-edits here
  (membership follows by name) / 1 here.
- C17 payload shape / wire encoding / id coercion → 1 at the
  slot owner / 0 here / 1 here.
- C18 manifest grain (7th client name held back, 8th leaf
  export, 3rd relay helper) → 1 at the holding level each
  (levels own surfaces — FR-1).
- C19 guard-type unification / message reword per subject → 1
  per subject (refused — FR-2); collection-guard helper → 0
  as consolidation (one token each — FR-10).
- C20 render vocabulary (`truth.render` → owner call) → 0 as
  consolidation (hunt-owned migration spelling, not a package
  rule — FR-5).
- C21 slot-read unification (wrap `getattr` vs relay proof
  read) → 1 per side (live-slot `AttributeError` vs stored
  read feeding a typed reject — FR-4).
- C22 `str()` unification (mint `str(id)` vs index `str(index)`)
  → 1 per side (caller pk vs canonical render — FR-3).
- C23 spec prose / bullet prose / framing prose changes → 0
  definitions here (projections follow — FR-14/FR-15/FR-17).

## Findings

### Compositions (each holds by name at current bytes)

Leaf and withholding. FC-1 manifest: the leaf binds exactly 7
names (6 from `client.py`, 1 from `_wrap.py`, re-read) with
`__all__` mirroring them in-file (probed: `sorted(__all__)`
is exactly the 7); the by-name identity probed
(`testing.TestClient is client.TestClient`); 25 matching
`from ...testing import` lines (23 consumer name-imports +
the submodule line + the docstring example, re-censused —
every code site resolves through the leaf, zero competing
manifests). FC-2 withholding: the leaf import block carries
zero `relay` imports (full-read verified); the absence probed
(`hasattr(testing, "global_id_for")` is `False`,
`testing.relay` absent from `sys.modules` post-import); 13
dotted-path consumers + the 1 submodule line resolve without
the leaf (re-censused).

Multipart and endpoint. FC-3 vocabulary: the f39 owner
(`_multipart.py`, ledgered) + the client guard set (:292) +
the client emission keys (:306/:307) + the views loss loop
(`views.py:794`, re-read) compose by name; zero code spellings
of the literals remain in the folder (the surviving mentions
are docstring/comment/message prose); both f39 gates green in
the witness. FC-6 ladder: the base `__init__` (:139-145)
resolves presence + forwards `url`; per-leaf transport
defaults (:411-412, :508-509), the request `url=` arm (:231),
and the mixin rungs (:578/:602) participate; the setting +
default compose from the conf owner (sole call site :140).

Colors and transport. FC-4 query twin: both colors build via
the one builder, post via the one transport, finish via the
one tail (bodies re-read; only the `request()` await differs).
FC-5 login bracket: `force_login` hits only this file (2 code
sites + prose, re-censused); `.logout()` has exactly 1 code
site (:493, the async color routes through `sync_to_async`);
`finally` logout both colors. FC-7 delegation: the mixin
forward (:602) is the sole in-package `TestClient(`
construction (re-censused); zero in-package
`AsyncTestClient(` constructions; the mixin owns no
body/decoding/endpoint logic. FC-8 tail: the sole
`self._decode(` site (:169) + the explicit raise (:178-179).
FC-9 transport: the sole conditional poster (:201-231) with
the omission switch + the dropped `format=` kwarg (both
re-read). FC-10 builder: the sole builder (:233-309) with the
gate trio + the uniform map rule (:304) + the FC-3 envelope.
FC-11 walker: the sole path walker (:311-386) with 8 uniform
`AssertionError` raises (AST-censused; the 9th HEAD raise is
the hunt-deleted len arm — FF-4) + D1.

Guards and wrap. FC-12 collection guard: the one `__test__`
site (:137) + inheritance probed on both leaves; the conf
function guard is the separate one-token mechanism (FR-10).
FC-13 wrap: the sole installer (:148) in the exact-4
`setattr(connection` census (unwrap :380 + 2 upstream-verbatim
constants, re-classified); the predicate composes from its
owner (1 def + 2 calls, re-censused); zero production call
sites (the docstring :100 hit is the worked example —
projection); the one `TypeError` (:142) with the pinned
non-interpolating message.

Relay. FC-14 proof: the WT block (:67-84) + the list-field
base (`_validate_djangotype_target`, identity check :197,
2 consumers) are the two bodies (f40 persists blocked — all
three touch paths dirty). FC-15 gates: finalized-first (:87)
+ stamp read (:99, never the setting — token grep 0 for the
setting) + the composed LEAD/TAIL wording (:104-105) + the
absence-based membership (:107); the `Meta.cursor_field`
compose site re-verified (relay D1 persists). FC-16 mint +
manifest: the sole `GlobalID(` construction (:120, census 1)
via the live `encode_typename` path with `definition.origin`
(the runtime-equivalent committed edit — FF-5); the
`decode_global_id` re-export (:49 + :55) with the identity
oracle; the `__all__` 2-name mirror.

### FAM verdict: none raised

Nineteen twin hypotheses were traced to a verdict; every one
resolves to single ownership, a standing rejection with an
unmet trigger, the already-rowed blocked duplication, or a
distinct contract (FR-1..FR-19). The three load-bearing
near-misses are FR-1 (the manifest triple shares the
`__all__`-mirror shape, but each level owns its own surface:
the module declares what it defines, the leaf declares what
it re-exports, the relay submodule declares its pair, and
the single-name module correctly carries none — C18 proves
opposite changes move opposite files; a merged manifest
couples definition sets to export policy), FR-2 (the
raise-type trio shares the guard posture, but a malformed
test call fails as `AssertionError` so one `pytest.raises`
catches every bad shape here, a non-callable wrapper fails
as spec-pinned `TypeError` at the wrap site, and a bad mint
input fails as `ConfigurationError` with a remediation —
unifying changes which failures which callers catch),
and FR-4 (the slot-read pair shares the attribute-read shape,
but the wrap read IS the live slot — a missing method raises
`AttributeError` today (pinned oracle) — while the relay
read feeds a typed reject — a `None` from either shape is the
same verdict there; a shared reader that defaulted on absence
would install where the wrap oracle demands a raise).
The f40 count-2 verdict persists but is already rowed
open+blocked, so no new Family-hold row is owed: no
consolidation is blocked beyond what the plan already rows.

### Rejections (each re-derived fresh; triggers re-checked)

Folder-fresh:

- FR-1 manifest triple: leaf 7 vs client 6 vs relay 2 vs
  wrap none — each level owns its surface (C1/C18 prove
  opposite move sets). Trigger: a package-wide
  single-manifest mechanism.
- FR-2 raise-type trio: `AssertionError` (malformed test
  call, 8 sites) vs `TypeError` (wrap arg, 1 site) vs
  `ConfigurationError` (mint input, 4 sites) — per-subject
  types + messages + reasons to change (C19). Trigger: a
  package-wide guard protocol.
- FR-3 `str()` pair: mint `str(id)` (caller-supplied pk of
  unknown type at mint time) vs index `str(index)`
  (canonical-render comparison inside the walker) — different
  inputs, timing, and move sets (C22). Trigger: a shared
  node-id-stringification helper with callers at both phases.
- FR-4 slot-read pair: wrap live `getattr` (missing method →
  `AttributeError`, pinned) vs relay proof read (`None`
  feeds the typed reject) — different errors and state
  effects (C21). Trigger: a truth write protocol plus a spec
  row redefining the missing-method contract.
- FR-5 `truth.render` vocabulary (10 client + 1 relay call
  sites): hunt-owned migration spelling, not a package rule —
  every site is a `+` line over a HEAD `_safe_arg_repr` site,
  and the HEAD owner is deleted at WT by the same wave. No
  trigger (needs a package render rule; the consolidation
  would edit hunt-owned lines).
- FR-6 guard trio: wrap `callable()` vs client `(list, tuple)`
  / `dict` vs relay `truth.is_subclass` — each guards its own
  subject with its own accepted set (the folder's
  `(list, tuple)` census is exactly 1 site). Trigger: one
  shared guard protocol for all seams.
- FR-7 color confinement: the async surface is exactly the 2
  `async def` + 3 `await` in `AsyncTestClient` — no twin
  exists to merge (wrap/relay/init carry zero colored
  tokens). No trigger (needs a second colored site).

Member-twin re-verifications (each body re-read fresh):

- FR-8 login vs one-sync-boundary (CONVERGE R1): harness-only
  session writes, kwarg-absent calls (:548/:552, re-read),
  no transaction/`using` in the full 653-line read; the code
  census refreshed (owner + 3 WT-composed arms (ledger) vs 3
  HEAD-direct arms + schema + 2 — FF-9). Trigger unfired:
  transaction-pinned sessions.
- FR-9 len-guard vs shared except (CONVERGE R3): the arm is
  intact at HEAD (:351 `except Exception` + `from exc` +
  message, re-read) with its oracle byte-identical at HEAD;
  deleted at WT by hunt dirt (H6). Verdict holds at HEAD,
  moot at WT — closeout-conditional (FF-4).
- FR-10 guard/manifest pairs (CONVERGE R2/R4/R5): per-subject
  rejection types intact (8/1/4 census re-derived);
  collection guards still one token each (class :137 +
  function, re-read); module vs leaf manifests still
  level-owned (C18). Triggers unfired.
- FR-11 ladder + emit/parse pairs (CONVERGE R6/R7): URL
  selection vs policy resolution (outside owner re-read,
  different domain); emit body vs the views loss loop
  (:794, re-read — different directions, reasons, failure
  postures). The name set is explicitly not refused — it
  consolidated at f39. Triggers as membered.
- FR-12 same-file separations (CONVERGE R8/R9/R10): gate trio
  (`is not None` :262 / truthiness :265 / mode-switch :270
  with :226/:169 agreeing, re-read); flipped defaults
  (`True` :421/:518 vs `False` :589, re-read, spec-owned);
  msg fallbacks (:625 vs :640, bodies re-read). Triggers as
  membered.
- FR-13 intersections + walks (CONVERGE R11/R12): exactly 3
  `& set(` sites (re-pinned: :292 + the two rest_framework
  sites, verdicts re-read); single-path verify vs
  full-traversal charge (both bodies re-read). Triggers as
  membered.
- FR-14 leaf pairs (CONVERGE init nested): leaf-vs-root
  (root grep-0 re-run; Decision 4 intact); withholding
  prose pair (neither passage grew the other's audience
  rule — re-read); bullet summaries (C23: every mechanics
  change moves zero leaf definitions). Triggers as membered.
- FR-15 wrap pairs (CONVERGE R-A/R-B/R-C/R-D): halves still
  separate lifecycle sites (consumer `bool` at setUp vs
  Django-invoked `None` at tearDown — bodies re-read);
  callable guards still per-subject (3 witnesses re-read);
  slot-read-vs-truth still behavior-differing (the pinned
  `AttributeError` vs default-then-install); framing still
  split by audience (wrap contract vs audit record).
  Triggers as membered.
- FR-16 relay except + slot reads (CONVERGE J1/J2): at HEAD
  the `except BaseException` whole-proof arm (:80, re-read)
  differs per site from the list-field read-only `Exception`
  scope, and no shared reader constrains the shape; at WT
  both subjects are hunt-reshaped (H3). Verdicts hold at
  HEAD, moot at WT — closeout-conditional (FF-6).
- FR-17 relay stamp/CLI/coercion/prose (CONVERGE J3/J4/J5/F7):
  post-finalize stamp vs pre-finalize predicate (lifecycle
  phases re-read); mint guard vs table-print guard (no
  contract source at the CLI — re-read); caller pk vs
  resolved row value (inputs/timing re-read); docstring as
  projection (C23). Triggers as membered.
- FR-18 f40 scope (CONVERGE family note): the verified
  `relay-node-target-guard` family still never names this
  file (grep-0 re-run); the f40 item owns the scope
  reconciliation (open+blocked). No trigger (family-owned).
- FR-19 dotted-path split trio (CONVERGE errors row): this
  `key.split(".")` (object-path placeholder walk, 1 site)
  vs the error-path split vs the filter split — three
  dotted grammars, three contracts (bodies re-read).
  Trigger as membered.

### Falsifications (record-only; no row reopened, nothing re-applied)

- FF-1 `_wrap.py` blob `0df97813` → `4a6c4098` (committed
  typing: `5c3496e0` Any→object + `91cd9ceb` reachability
  comment; runtime-neutral, diff-read). The run-7 "6 stmts
  / 4 imports / `Callable[..., Any]`" cites are stale
  (now 5 / 3 / `Callable[..., object]`); verdicts intact
  (FR-15). Closeout refreshes the cites.
- FF-2 `client.py` s13→HEAD committed typing (6 commits:
  overloads, `TYPE_CHECKING` imports, `Mapping`/`object`,
  `array` local, comment-only suppressions; all
  runtime-neutral, diff-read commit by commit). The s13
  "23 stmts / 635 lines" cites are stale (now 24 / 656 at
  HEAD); verdicts intact. Closeout refreshes the cites.
- FF-3 f39 LANDED (ledgered, verified run 11): the s13
  "FC1 open, owner TBD" record is SUPERSEDED — the
  `multipart-control-field-names` row is `consolidated`
  at `_multipart.py`, both consumers compose by name, both
  gates green in the witness (FC-3). No closeout action
  (the row already reads consolidated); the s13 note
  stands as history.
- FF-4 client hunt dirt (7-hunk split above): the 10
  `truth.render` retargets + the len-guard deletion. R3
  holds at HEAD, moot at WT (FR-9); the 3 hostile oracles
  are deleted at WT by the same wave. Blocked-on-hunt:
  closeout revisits R3 only after the hunt lands or is
  dropped.
- FF-5 `relay.py` run-7→HEAD committed typing (7 commits:
  `TYPE_CHECKING`/`cast`, `type[object]`, comments,
  suppressions; runtime-neutral, diff-read) + the
  `type_cls` → `definition.origin` mint-tail edit
  (`345cd632` — runtime-equivalent: the gate proves
  identity on every reaching path). The "8 stmts / 110
  lines / `type_cls` call" cites are stale (now 11 / 123
  at HEAD / `definition.origin`); verdicts intact.
  Closeout refreshes the cites.
- FF-6 relay hunt dirt (3 hunks, all hunt): the proof
  reshape + `BaseException` deletion + renders. J1/J2
  hold at HEAD, moot at WT (FR-16); the 2 hostile oracles
  are deleted at WT by the same wave; f40 stays
  open+blocked (all three touch paths dirty). Blocked-on-
  hunt: closeout revisits J1/J2 only after the hunt lands
  or is dropped.
- FF-7 client D2 CLOSED: spec-043 Decision 8 now reads
  "sibling of `TestClient` over one shared base" (:884 +
  :33/:386/:435/:733, re-read) and the rationale D8 reads
  "sibling clients over one shared base" (:195, re-read)
  with the stale short-cite gone (grep-0 for the cited
  symbol). The s13 closeout condition (a spec-text update)
  is satisfied; no home.
- FF-8 oracle census refresh (record only, verdicts
  intact): WT test functions 33/9/9 vs HEAD 36/11/9 —
  exactly the 5 hostile deletions by the hunt wave (3
  client + 2 relay, named in the trace) + 1 wrap prose
  reword; every surviving oracle body re-read. Consumer
  census refresh: leaf lines 25 (23 name-imports +
  submodule line + docstring example — name-import count
  steady with the corrected 23); dotted relay 13 + 1
  submodule line (was 10 + 1) — growth strengthens the
  withholding conclusion.
- FF-9 R1 census refreshed (verdict intact): at WT the
  types/resolvers trio composes the owner (3 ledgered
  `run_in_one_sync_boundary` arms — DRY-owned dirt,
  matched by content) while at HEAD it still calls
  `sync_to_async(` directly (3 sites, re-read); the client
  pair stays kwarg-absent at both (FR-8). Record only.

## Defects

None found while tracing. Checks run: every hunt-evolved
member's docstring re-read against its body (walker
uniform-guard clause + len-sentence deletion, builder
envelope prose, proof-block comments, render call sites —
no contradiction; the walker docstring follows its arm
deletion); every guard family enumerated for omission
against its contract source (the 8 walker raises + D1, the
4 relay raises, the 1 wrap raise, the 2 guard call sites
covering both leaves, the 5 rung participants — no missing
member); layering claims hold (init imports wrap + client
only, client imports neither sibling, relay imports
neither sibling, wrap imports only the patch module — no
reversed import, no cycle).

The two member D1 defects re-verified persisting at
current bytes (record-only; each already rides to closeout
under its member item — no new homing): client D1 (the
non-`str` `files=` key still escapes as `AttributeError`
at `client.py:335` while the docstring :376 still promises
the uniform type); relay D1 (the "three gates" / "three
compose sites" census comments at `types/base.py:139/147`
still undercount the four LEAD sites (:296/:344/:400/:474)
plus the helper). Client D2 is CLOSED (FF-7) — it does not
ride.

## Pending execution

No `proof:` owed (zero-edit: nothing to prove beyond the
green witness already run). `gate:` entries for the final
gate:

- `gate:` `uv run python scripts/workspace.py run
  dry/folder-testing/verify-1 -- python -m pytest
  tests/testing tests/test_multipart.py -q --no-cov -p
  no:cacheprovider` (re-run the 70-row witness; ran green
  in slot-2 as `dry-20261010T053140-241639`).
- `gate:` the final gate's live `/graphql` suites carrying
  testing-client rows (client API, uploads, relay library
  shapes, visibility, multi-db) — named by the gate, not
  re-run here.
- Cells `inapplicable by construction`: the folder's code
  reaches no database, alias, or dialect decision (pure
  build/walk/proof/mint work; the transport posts through
  the caller's wrapped client; session writes are
  caller-harness ORM work outside any transaction) — the
  same construction the four member items ruled.

## Judgment

The folder is at single ownership: 16 compositions hold by
name with fresh censuses and probes, the f39 consolidation
holds with zero residue, the one already-rowed duplication
persists exactly as rowed (open+blocked), 19 twin hypotheses
resolve without a new second definition, and the witness
suite runs 70/70 green at current bytes. The folder-fresh
rejections transcribe below as T-1..T-7 for Worker-0 to
row. Zero edits, zero new defects, zero new blocked
consolidations.

## Index rows for Worker-0

One line per row; Worker-0 alone edits the plan. Holding
item for all: Folder integration `testing/`.
Freshness: WT blobs in `## Pins and fingerprints` (BASE =
WT); HEAD troupes listed there for the two dirty files.
No tracked files changed (item-scoped diff empty; no
ledger rows); HEAD unmoved at `23b5f421`; slot-2
byte-identical re-verified after the witness suite; NO
`## Families` item (no new multi-definition rule — the
one blocked duplication is already rowed); no
`docs/dry/temp-tests/` scratch was created. No commit.

Rejections (folder-scope merges considered; each with trigger):

- T-1 `testing-manifest-triple-merge` (FR-1) — files
  `testing/__init__.py`, `testing/client.py`,
  `testing/relay.py`, `testing/_wrap.py` — rejected (each
  level owns its surface; C18 proves opposite move sets;
  trigger: a package-wide single-manifest mechanism).
- T-2 `testing-raise-type-trio-merge` (FR-2) — files
  `testing/client.py`, `testing/_wrap.py`,
  `testing/relay.py` — rejected (per-subject types +
  messages + reasons to change; trigger: a package-wide
  guard protocol).
- T-3 `testing-str-coercion-merge` (FR-3) — files
  `testing/relay.py`, `testing/client.py` — rejected
  (caller pk vs canonical render; trigger: a shared
  node-id-stringification helper with callers at both
  phases).
- T-4 `testing-slot-read-merge` (FR-4) — files
  `testing/_wrap.py`, `testing/relay.py` — rejected
  (live-slot `AttributeError` vs stored read feeding a
  typed reject; trigger: a truth write protocol plus a
  spec row redefining the missing-method contract).
- T-5 `testing-render-vocabulary-merge` (FR-5) — files
  `testing/client.py`, `testing/relay.py` — rejected
  (hunt-owned migration spelling, not a package rule; no
  trigger — needs a package render rule).
- T-6 `testing-guard-trio-merge` (FR-6) — files
  `testing/_wrap.py`, `testing/client.py`,
  `testing/relay.py` — rejected (each guards its own
  subject; folder `(list, tuple)` census is 1 site;
  trigger: one shared guard protocol for all seams).
- T-7 `testing-color-confinement` (FR-7) — files
  `testing/client.py` — rejected (async surface is 2
  defs + 3 awaits in one class; no twin exists; no
  trigger — needs a second colored site).

Closeout notes (not rows): FF-1/FF-2/FF-5 (refresh the
stale member cites to current blobs); FF-3 (no action —
the row already reads consolidated); FF-4/FF-6
(conditional: revisit R3/J1/J2 only after the hunt lands
or is dropped); FF-7 (close client D2, no home); FF-8/FF-9
(no plan change — census refreshes, verdicts intact);
f40 persists open+blocked (no change); client D1 + relay
D1 ride (no new homing).

## Independent verification (Worker-2)

Verdict: verified (plain; no pending execution —
`## Pending execution` carries `gate:` entries only, and
the suite gate was re-run green below).

Sequencing disclosure: the dispatch brief ordered the
artifact read before any tracing, so the ideal
expectation-first order (own trace recorded before
opening `## Findings`) could not be followed. Mitigation:
every position below was fixed by my own commands —
pins, AST censuses, greps, diffs, probes, suite runs —
before comparison against W1's record; agreements are
re-derivations, listed as such.

### Own trace (re-derived, then reconciled)

The folder owns the consumer test surface end to end:
leaf manifest + withholding (`__init__.py`), wrap-time
guard leaf (`_wrap.py`), HTTP client family
(`client.py`), Relay mint/decode helpers (`relay.py`).
Every cross-folder seam composes by name from an
outside owner I re-pinned: endpoint setting + default
(`conf.py`, sole production call site `client.py:140`,
default literal once at `conf.py:489`); engine base +
`_decode` + field schema (strawberry, sole `self._decode(`
at `client.py:169`); multipart vocabulary (`_multipart.py`
owner + `client.py:292` guard + `client.py:306/307`
emission + `views.py:794` loop, zero code spellings
elsewhere in the folder); `_DatabaseFailure` predicate
(`_django_patches.py:292`, 1 def + 2 calls at
`_wrap.py:146` and `_django_patches.py:379`); registry
(`registry.py`); gate wording + strategy set
(`types/base.py`: LEAD 5 = 4 in-file + helper,
TAIL 4 = 3 + helper); `encode_typename` /
`decode_global_id` (`types/relay.py`); one-sync-boundary
owner (refused: the client pair stays kwarg-absent at
`:548/:552` with zero transaction/`using` code tokens
in the 653-line file).

Definition counts (mine): leaf membership 1 per
holding level (init 7 = client 6 + wrap 1, relay 2,
wrap none — opposite move sets); raise types 1 per
subject (client file-total 8 `AssertionError`, wrap
1 `TypeError` at `_wrap.py:142` with a
non-interpolating message, relay 4
`ConfigurationError`); slot reads 1 per side (live
`getattr` at `_wrap.py:145` vs proof read feeding a
typed reject); `str()` 1 per side (`relay.py:120`
caller pk vs `client.py:358` canonical render);
multipart names 1 at the f39 owner; proof pair count 2
(`relay.py:67-84` + `list_field.py:136/197`, 2 call
sites at `:240/:1592`) = the already-rowed f40.
Owner choices: agree on all — no second definition
wants a new owner, and the count-2 pair is rowed.

### Enumeration (member by member)

Independent `ast` census at WT bytes reproduces W1
exactly: `__init__.py` 4 (docstring + 2 ImportFrom +
Assign); `_wrap.py` 5 (docstring + 3 ImportFrom + 1
def); `client.py` 24 (docstring + 11 ImportFrom + 2
Import + If + 2 Assign + 7 classes); `relay.py` 11
(docstring + 7 ImportFrom + If + Assign + 1 def).
Color census: 2 `async def` + 3 `await`, all in
`AsyncTestClient` (`await` at :538/:548/:552 exact;
the `def` lines are :512/:542 — see O1).
Disjointness re-swept: zero client tokens in
wrap/relay, zero wrap tokens in client/relay, zero
relay tokens in wrap/client; package root 0
`testing`/`TestClient` tokens; wrap/relay/init zero
colored code tokens. Homes agree: every member lands
in a verified family row, a re-verified member
assignment, or T-1..T-7; nothing unassigned.

### Matrix (judged on reasons)

1. Cross-flavor: agree discharged — one subsystem,
leaf 25 re-censused (23 name-imports + submodule
line + docstring example), dotted relay 13 + 1,
plain-import code sites 0, `truth.render` 10 + 1 =
hunt-owned migration spelling (every site a `+`
line over a HEAD `_safe_arg_repr` site).
2. Sync/async: agree discharged — colors confined
as censused; both colors share builder + tail below
the color line; no cross-file twin.
3. Derived knowledge: agree discharged — every
same-token population walked on body strength;
censuses reproduce (`GlobalID(` 1, `TestClient(`
1 code site at `:602`, `AsyncTestClient(` 0,
`setattr(connection` 4 package, `& set(` 3,
`__test__` class + function, `(list, tuple)` 1,
`_is_database_failure` 1 + 2).
4. Round-trip: agree discharged — mint 1 site via
the live path with `definition.origin`
(runtime-equivalent: the `:75-78` gate proves
`canonical.origin is type_cls`); decode re-exported
with identity oracle; emit/parse names at the f39
owner; wrap has no restore half by contract.
5. Other media: agree discharged — oracles WT
33/9/9 vs HEAD 36/11/9 re-censused; the delta is
exactly the 5 hostile deletions (3 client + 2
relay, named by diff) plus a prose-only wrap
reword; contract sources re-read (spec-032
Decision 10 intact; spec-043 Decision 8 now
current — FF-7 verified below); no medium carries
a second definition.
6. Omission: agree discharged — deliberate
omissions each carry a contract source (no
`relay` import in the leaf block, no restore, no
`mutate()`, `input_data=` refused in prose);
the uncovered shape is the filed D1.

### Compositions, rejections, falsifications

FC-1..FC-16: all 16 hold. Line pins spot-checked
against WT bytes (`:139-145`, `:411-412`,
`:508-509`, `:231`, `:578/:602`, `:169`,
`:178-179`, `:201-231`, `:233-309`, `:304`,
`:311-386`, `:137`, `:148`, `:142`, `:67-84`,
`:87`, `:99`, `:104-105`, `:107`, `:120`,
`:49 + :55`) — all hit. Execution probes in
slot-3: `sorted(__all__)` is exactly the 7,
`testing.TestClient is client.TestClient`,
`hasattr(testing, "global_id_for")` is False,
`testing.relay` absent from `sys.modules`
post-import, `__test__` False inherited on both
leaves. f39 holds consolidated (owner + 2
consumers + 2 gates, both gates green in the
witness). One wording note: FC-11's "8 raises"
is the file total (8 WT / 9 HEAD, re-censused);
the walker proper holds 5 at WT / 6 at HEAD —
see O3. Verdict-neutral.

FR-1..FR-19: all 19 resolve without a new second
definition. The three load-bearing near-misses
were re-traced fresh from bodies and hold
separate: FR-1 on level ownership (C18 opposite
move sets re-verified); FR-2 on catch contracts
(one `pytest.raises(AssertionError)` vs
spec-pinned `TypeError` vs remediating
`ConfigurationError` — unifying changes which
callers catch what); FR-4 on error contracts
(pinned live-slot `AttributeError` vs `None`
feeding a typed reject — a defaulting shared
reader breaks the wrap oracle). Converge bodies
re-read fresh: FR-8 (kwarg-absent pair, no
transaction), FR-9 (HEAD len arm: `except
Exception` + `from exc` + message intact at
HEAD, deleted at WT), FR-10 (8/1/4 + one token
each + level-owned manifests), FR-11 (URL vs
policy domains; emit vs loss-loop directions),
FR-12 (all pins hit: `:262/:265/:270`,
`:226/:169`, `:421/:518/:589`, `:625/:640`),
FR-13 (`:292` + the two rest_framework sites),
FR-14 (root grep-0; prose pairs re-read),
FR-15 (halves/guards/reads/framings re-read),
FR-16 (HEAD `except BaseException` whole-proof
arm vs list-field read-only scope; both moot at
WT), FR-17 (lifecycle phases, no CLI contract
source, inputs/timing, projection), FR-18
(family grep-0 for this file, re-run), FR-19
(three splits: `client.py:335`,
`utils/errors.py:185`, `filters/sets.py:505`).
Every rejection carries its contract difference
+ trigger (or a stated no-trigger reason).

FF-1..FF-9: endpoints verified. All five old
blobs resolve; WT/HEAD states match the record;
the client 7-hunk / relay 3-hunk split holds by
line (H1 mixed 5-ledger/1-hunt, H2 mixed
1-ledger/1-hunt, H3 pure ledger, H4-H7 pure
hunt; relay 0 ledger); the f39 ledger row is the
single `testing/` ledger hit and matches by
content; FF-9's trio endpoints census 3 WT arms
(`:772/:838/:910`) vs 3 HEAD direct sites.
FF-7 (client D2 CLOSED): Decision 8 reads the
sibling shape at :884 (+ :386/:435/:733 and
:39 — see O2), rationale D8 at :195, the stale
`TestClient._assert_file_placeholders` short
form greps 0 across both files, and the old pin
wording is gone — the s13 closeout condition (a
spec-text update) is satisfied; close with no
home. f40 persists exactly as rowed: both
bodies present, all three touch paths dirty
(`relay.py`, `list_field.py`, `registry.py`),
plan rows open+blocked.

### Zero-edit, defects, index rows, gates

Zero-edit CONFIRMED: `git diff
f47518d34b02ed7d500b10d74d55b738ea02951b`
names exactly one path, `docs/dry/dry-0_0_15.md`
(Worker-0's dispatch lines, expected); over
package/tests/examples the diff is empty; WT
blobs equal ITEM_BASELINE blobs on all four
targets; no new tracked files; the untracked set
is pre-existing (ledgered f39 pair + hunt pair +
other items' files); no `docs/dry/temp-tests/`
scope for this item. Independent
consolidation search (within-folder twins,
cross-folder seams, sync/async remainders,
one-line declarations): no missed FAM-N, no new
Family-hold owed. Ruff gates vacuous (zero
`.py` touched); artifact carries no banned
mentions; citations are WT-verified path pins.

Defects: none new. Client D1 persists
(`:335` unguarded `key.split` vs the `:373-376`
uniform-type promise — see O4) and relay D1
persists (`types/base.py:139/147` undercount
the 4 LEAD / 4 TAIL sites); both ride to
closeout, no new homing. No `(Worker-2)`
entries.

Index rows T-1..T-7: 7/7 confirmed for
transcription — files and triggers match the
FR bodies in every row. Zero corrections
(no CC-N owed).

Gates run (all through `heavy`, GREEN, one at
a time): witness `tests/testing` +
`tests/test_multipart.py` in slot-3 =
70 passed (`dry-20261010T054133-8404b4`,
copy fresh, shared unmoved); leaf/withholding
probe green (`dry-20261010T054159-79f681`);
dotted-absence probe green
(`dry-20261010T054207-2b9592`); slot-3
byte-identical to WT on all four targets
before and after. Sharded/pg cells: agree
`inapplicable by construction` — zero
DB/alias/dialect code tokens in the folder
(all hits docstring prose or the worked
example); session writes ride the caller's
harness client outside any transaction.

Freshness: WT pins `48b45d1b` / `4a6c4098` /
`3b122fd5` / `8a31c1ad` (re-derived; first two
= HEAD); HEAD `23b5f421` unmoved;
ITEM_BASELINE `f47518d3` resolves as a commit.

### Observations (verdict-neutral, no action owed)

- O1: matrix axis 2 cites the async defs at
:511/:541 (decorator lines); the AST `def`
lines are :512/:542. Census unaffected.
- O2: FF-7 cites a sibling-wording site at
spec :33; the line is :39. Wording and
closeout consequence unaffected.
- O3: FC-11 attaches the file-total 8 to the
walker range; the walker proper holds 5
raises at WT (6 at HEAD). FR-2/FR-9/FR-10
use the file total consistently; no row
transcribes a walker count.
- O4: the client-D1 promise cite ":376" is a
code comment (`:373-376`), not the method
docstring (`:316-332`). Defect substance
unaffected.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-client]: dry-file-testing__client.md
[file-init]: dry-file-testing____init__.md
[file-relay]: dry-file-testing__relay.md
[file-wrap]: dry-file-testing___wrap.md
[self]: dry-folder-testing.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
