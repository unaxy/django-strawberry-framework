# DRY review: `auth-fail-closed-anonymity-arms`

Status: verified
Run: 0.0.15 2026-10-12-24

## System trace

Four session-failure arms + one polarity. (L1) `auth/mutations.py:690`
`_django_http_login_establish`: `request.user = AnonymousUser()` + flush,
cleanup failure re-raises the primary via `__context__`. (L2) `:736`
Channels twin: `scope["user"]` + `await aflush()` + same chaining, inside
the held scope lock. (O1) `:905` `_django_http_logout`: anonymize + bare
re-raise, no flush. (O2) `:976` `_channels_logout`: scope twin under scope
lock + `actor_transition`. (P) `consumers.py:1066-1071`
`_actor_is_current`: stale actor stays, `return False` (spec-046 D11).
Sweep: `AnonymousUser()` code writes = exactly the 4 arms; `scope["user"]`
writes = L2/O2 + `:1077` success write-back; `request.user` = L1/O1; flush
= `:691`/`:737`. The adapter's `user` is read-only (no setter), so Channels
arms must write the scope cell. `_refreshed_actor` failure collapses to
`None` into (P); invalid shapes answer `AnonymousUser` (channels-owned).
Spec-040 `:1701-1707` splits the contracts: login anonymous+flush+chain vs
logout anonymous-where-possible+propagate, durable intact pre-flush. Item 3
fences the checkpoint DECISION + helper (cited). DANGER swept: untriggered.

## Verification

### Matrix

1. Cross-flavor: anonymity arms are session-auth-only; write flavors gate by
   perm (fenced); `current_user` reads via the item-3 helper. Discharged.
2. Sync/async twins: L1/L2 + O1/O2 are the question (F1/F2); bridges
   compose the arms by call (consumers). Discharged.
3. Derived-twice: chain comment x2 is prose each `noqa` site needs; breadth
   x4 unextractable, locally reasoned. Below bar.
4. Inverse pairs: establish-compensation vs teardown-anonymize are asymmetric
   by design (spec-040 splits them); (P) is a checkpoint arm, not an inverse.
   No unification owed.
5. Other media: spec-040 `:1701-1707` + Test plan, spec-046 D11/D16, 11 arm
   oracles + verdict/close/read/provenance oracles; one gap found (D1).
6. Omission: login x2 + logout x2 armed, checkpoint (P), write-back
   (infallible), `_refreshed_actor` into (P), `actor_transition` latch-only,
   lock/observation/payload pre-mutation (no arm owed). All guarded.

### Challenges

- C1 add a compensation step: L1+L2 (count 2) - no shared form w/o machinery (F1).
- C2 chain-vs-bare: L-only; O has no fallible cleanup, so nothing to chain.
- C3 O-gains-flush: contract-barred (spec-040 + O1 oracle pins durable-intact).
- C4 flip (P) to downgrade: D11 rewrite only; touches neither L nor O; passes
  the suite today (D1).
- C5 unify (P)+O2 ("scope actor on failure"): phase, lifetime, cancellation
  posture, and cell ownership all differ (F4).
- C6 catch-breadth change: all 4 move, but `except` clauses are
  unextractable, each locally reasoned; (P) shows the opposite live. Not shared.
- C7 shared one-line anonymize helper: principle-11 machinery (the assignment
  IS the logic). Barred.

## Findings

### F1 (L1,L2) transport twins: REJECT consolidation

One compensation rule (same phase, ordering, chain policy) spelled twice,
but color + cell force adapters: L2 must `aflush` on the loop, L1 cannot
await (a bridge in cleanup = machinery + thread hop), and the adapter's
read-only `user` bars a shared request-side write. Twin helpers rename,
closures add definitions, extracting `raise primary` changes the traceback.
Docstrings already cross-link. Challenges C1/C6. Proofs: P3
(execution-verified, run dry-20261012T104228-1751c5, 11 passed). Triggers:
upstream color unification; settable adapter user; third transport.

### F2 (O1,O2) transport twins: REJECT, below bar

One failure-anonymize rule in one line per transport (run-14 f33 precedent);
the cell split is forced (F1's adapter reason). No fallible step, so no
chain structure exists to share. Challenges C2/C3/C7. Proofs: P3 (the 4
teardown rows: anonymous actor + propagated error + O1 durable-intact).
Triggers: an arm gains a fallible step (becomes L-shaped, re-ask F3); a
third teardown transport.

### F3 (L,O) compensate-vs-anonymize: REJECT, distinct rules

Flush directions are opposite (L destroys partial state it created or the
cookie authenticates a half-login; O refuses a durable claim it did not
achieve), chain-vs-bare is structural (fallible IO vs one infallible
write), spec-040 states them as two contracts, and the oracles pin opposite
durable outcomes (L1 row deleted vs O1 row intact). A change to either side
never moves the other. Challenges C2/C3. Proofs: P3. Trigger: the spec
unifies the failure contract.

### F4 (P) never-downgrade: REJECT, its own contract

(P) is one arm of the item-3-fenced checkpoint decision, not the arms'
boundary: connection-lifetime drain (socket open, siblings in flight) vs a
single erroring request; `except Exception` (a verdict must never be
fabricated from a teardown) vs `except BaseException` (cleanup owed even on
cancel); the shared `scope["user"]` cell is channels-owned vocabulary,
excluded by the bar. The D11 reason verified against the bodies: the close
is not instantaneous (decide-then-await-close), the lease serializes
checkpoints against transitions, and provenance is write-once - so a later
checkpoint denies an anonymous-with-history actor read-free (pinned by
`test_a_same_socket_logout_stops_a_running_subscription_on_both_protocols`).
The load-bearing edge is the drain-window readers + a later teardown's `ok`,
which keep revocation attribution instead of a clean anonymous. Flip test
count 1. Challenges C4/C5. Proofs: P1 (execution-verified, run
dry-20261012T104214-e0ebcc, 2 shapes green: mismatch + store-failure denial
keep actor identity + provenance); P2 (execution-verified, run
dry-20261012T104242-47500b: baseline green, the actor-clearing mutant fails
exactly the declared set, restore byte-verified). Negative control: P2's
mutant IS the bypass attempt (attribution destruction), refused by P1.
Triggers: a D11 rewrite; a `RevokedActor` sentinel (re-asks all five sites).

### Freshness (worktree bytes, `git hash-object`; HEAD `c37a08a0`, unmoved)

`auth/mutations.py` 217c6bff744a; `consumers.py` 24aa6f3d69be;
`utils/sessions.py` de3cf2c9ab3c; `utils/permissions.py` dbb8f6021fa2;
`auth/sessions.py` 6e5fadb7afc1; `auth/queries.py` b0c60920eb9d; `views.py`
82e95fa147a5; `auth/test_mutations.py` 2a224eb18c05; `test_routers.py`
ab9b138a2fe5; `test_consumers.py` ca1f91143fb1; spec-040 0a821df6477a;
spec-046 2d4bb1d611e9; item-3 artifact 77c4dd46cd88; P1 probe eb37e944359a;
P2 manifest f74141f32efc (copy slot-2, digest sha256:423e64b7, shared
unmoved at every run). Searched population: every `AnonymousUser`
mention, `scope["user"]` / `request.user` write, flush call, and
session-mutating path (counts in trace). Excluded (named): establish /
teardown bodies (item 6), checkpoint decision + helper (item 3), perm gates,
transports, recognition, provenance latch, `_refreshed_actor` internals.

## Defects

D1 (P) stale-identity unpinned (test gap; unfixed; route to Worker-0 for
homing): spec-046 D11 "the stale actor stays" has verdict/close/log/read
oracles but no scope-actor-identity assertion - every `"user"` assertion in
`test_routers.py` / `test_consumers.py` was read and none pins it, so a
downgrade/clear passes the suite (P2's mutant fails only the scratch
probe). Owner: the revoked/store-failure rows in `tests/test_routers.py`
(spec-046 D11 surface).

## Pending execution

None. P1/P2/P3 are execution-verified (run ids in Findings); the final gate
runs at closeout.

## Judgment

Zero-edit REJECT on every pair: the twins sit below the no-machinery bar
(color + read-only adapter force adapters), (L,O) are distinct contracts
with opposite durable pins, and (P) is its own checkpoint-liveness contract
with the D11 reason verified against the lease/latch bodies. Separations
are already recorded at the owners and in the specs. DANGER untriggered; D1
routed for homing.

## What shrinks

Net package lines over `ITEM_BASELINE=38570690673aa54258bd98f3d30bcf9e39c0876c`:
0 (zero-edit; nothing to port; live tree touched only by this artifact).
Considered shapes: (S1) twin compensation helpers (reject: renames, the
obligation stays 2); (S2) one async compensation + `async_to_sync` bridge
in L1 (reject: machinery + thread hop + new failure modes in cleanup);
(S3) one body over (write-actor, flush) closures (reject: 2 bodies + 2
adapters > today's 2 bodies); (S4) extracting the `raise primary` chain
line (reject: adds a traceback frame, saves one line); (S5) shared
one-line anonymize (reject: principle 11, obscures ownership); (S6)
promoting (P) into a scope-failure rule with O2 (reject F4: different
phase, lifetime, cancellation, cell ownership).
Census: 4 arm definitions (2 rules x 2 transports), 1 polarity arm, 0
shared forms, 11 arm oracles green, 2 probe shapes green, 1 mutation
control (declared set exact, restore byte-identical).
DANGER sweep (no arm leaves an authenticated actor where anonymity is owed
on a servable path): both L arms anonymize first with a sync,
un-cancellable write before the fallible flush; both O arms are a single
sync write; pre-mutation failures (prologue, observation, payload build,
lock acquisition) owe no compensation and propagate; `actor_transition`
and lock exits only release infallible locks; cancellation follows the
docstring-stated split (L: cleanup attempted, cancel propagates with the
primary as context; P: cancel propagates, never a verdict), pinned by
`test_login_cleanup_cancellation_propagates_with_the_primary_as_context`
and the checkpoint's `except Exception` comment; `last_login` is not
rolled back (impossible in general; strictly more closed than Django,
which compensates nothing).
D11 verification detail: the checkpoint verdict denies under either
spelling - a downgraded actor would take the `:1025` provenance arm, which
denies every connection the `:1027` latch ever saw authenticated (the latch
runs before any refresh, and is write-once), exactly as the same-socket
logout rows pin - so the never-downgrade invariant loads on observation
integrity during the drain: in-flight `request_from_info` readers keep the
revoked identity instead of a clean anonymous, and a later same-connection
teardown observes the true `ok` (`_authenticated_actor_or_none` reads the
scope actor through the read-only adapter).

## Independent verification (Worker-2)

### Own trace (recorded before opening `## Findings`)

Sites (worktree bytes). L1 `auth/mutations.py:690-691`
(`request.user = AnonymousUser()` + `request.session.flush()`), chain
`:692-693`, under `except BaseException` `:688`: DEFINITION, sync
login-establish compensation. L2 `:736-737` (`scope["user"]` +
`await aflush()`), chain `:738-739`, under `:734`, inside the scope
lock: DEFINITION, async login-establish compensation. O1 `:905`
(`request.user = AnonymousUser()`, bare raise `:906`) under `:904`:
DEFINITION, sync logout-teardown anonymize-only. O2 `:976` (bare raise
`:977`) under `:975`, inside scope lock + actor lease: DEFINITION,
async logout-teardown anonymize-only. (P) `consumers.py:1066-1071`,
the deliberate NON-write + `return False`: DEFINITION,
never-downgrade polarity, its own contract. Consumers: `:1077`
`scope["user"] = refreshed` (success-path write-back, only past the
`:1066` authenticated check) is a CONSUMER of the verdict, not an arm;
`scope.get("user")` `:1006` read; provenance latch. `_refreshed_actor`
(`:1363-1397`) answers `AnonymousUser()` on a synthetic store via
channels `get_user` - Django/channels-owned, never the live store, not
a 5th arm (foreign rule). Oracles: `tests/auth/test_mutations.py`
(`:1711/:1738/:1752/:1763/:1779` L1, `:2094/:2114/:2144/:2161` L2,
`:2298/:2319` O1, `:2336/:2355` O2);
`tests/test_routers.py:6031/:6190/:6202/:6289` (logout-transition
identity only, none post-failed-revalidation);
`tests/test_consumers.py` has zero user assertions (window + host
only). Projections: spec-040 D11 `:1701-1707` (login
anonymize+flush+chain vs logout anonymize-where-possible, durable
intact on pre-flush failure), spec-046 D11 `:1372-1382`
(never-downgrade, stale stays), matching docstrings - all verified
against bodies.

Censuses re-run: `AnonymousUser()` code writes = exactly the 4 arms;
`scope["user"]` writes = `:736`, `:976` (arms) + `:1077` (success
write-back); `request.user` assignments = `:690`, `:905`;
`flush()/aflush()` code calls = `:691`, `:737`; `except BaseException`
in `auth/mutations.py` = exactly the 4 arm guards. No 5th arm.

Challenges (mine): C1 login compensation gains a step -> L1, L2 = 2,
shared form machinery-barred (attempt C below). C2 logout
re-raise/wrap shape -> O1, O2 = 2 single-token sites (1-line
assignment + bare raise carry no real logic each) -> below bar. C3
durable-pin change -> L1, L2 move; O1, O2, (P) untouched ->
compensate vs anonymize-only are distinct rules. C4 actor-write
target change -> Django-HTTP arms vs Channels arms split by
transport, no shared target. C5 polarity flip (consumers downgrades)
-> refused by spec-046 D11; (P) owns the opposite pin, mutation arms
unaffected -> own contract. C6 cancellation-clause change -> the
`except BaseException` token is shared by 4 arms but bodies differ
(flush+chain vs bare); consumers `except Exception` is the deliberate
opposite (cancel propagates, never converts to denial) -> clause is
idiom, bodies are per-phase contracts. C7 chain idiom
(`__context__` -> `__cause__`) -> L1, L2 chain lines = 2 single-token
sites -> below bar.

Shared-form attempts, each built far enough to fail concretely. (A)
Twin sync compensator L1+O1: O1 must NOT flush (spec-040 D11 leaves
the durable row intact on pre-flush failure) while L1 must -> needs a
flush flag = mode flag; without it the helper owns one assignment
line and every real change still reasons per-site. Refused. (B)
Async compensator L2+O2: same flush split, plus O2 holds the actor
lease INNER - a `(scope, session)` helper that branches is a mode
flag. Refused. (C) Cross-transport login helper L1+L2: color split -
sync L1 cannot await `aflush`; an `async_to_sync` bridge adds an
event-loop/thread hop to the sync failure path (principle-8
observable: thread affinity, await points); request-vs-scope targets
need a discriminator = mode flag; the reverse (`sync_to_async`
around a sync helper in L2) runs sync DB IO on the loop
(`SynchronousOnlyOperation`); a closure factory with a color flag is
a mode flag, and two closures are two definitions with no shrinkage.
Refused: bridge + mode flag. (D) Chain-line extraction (`raise
primary` x2): inseparable from its `except Exception:` frame (the
chain reads the handled exception); a `_reraise(e)` helper is a
1-line P11 deletion candidate, not an abstraction. Below bar.
Refused. (E) Logout-twin helper O1+O2: the only shared token is
Django's `AnonymousUser()` constructor (foreign rule, uncountable) +
the bare-raise idiom; targets and locks differ. Below bar. Refused.
(F) All-four "anonymize" helper: C's bridge + A/B's flush flag +
target discriminator. Refused. (G) (P) composed with mutation arms:
opposite polarity (must-anonymize vs must-not); a shared resolver
needs a polarity flag encoding opposite contracts. Refused: distinct
rules. P11 scan: the arms are inline 1-2 liners; no helper, wrapper,
or constant exists for them -> nothing to delete.

Owner I would choose: no consolidation. Each arm stays inline in its
body's except clause (bodies owned by item 6; the arm is the body's
failure clause, context here), polarity stays at the checkpoint with
its D11 comment. Zero-edit REJECT on every pair.

Matrix (my discharge): (1) cross-flavor - auth is single-surface;
consumers carries the opposite contract, in-family; the actor-write
census is closed, no second surface writes session actors. (2)
twins - L1/L2 and O1/O2 are the pairs, in-family. (3) derived-twice -
classification is item 3's, fenced; arms assign, never classify;
`AnonymousUser()` is Django-owned. (4) round-trip - establish vs
teardown asymmetric by spec (C3); `:1077` is success-path, not an
inverse of any arm. (5) media - spec prose verified against bodies
(spec-040 D11 `:1701-1707`, spec-046 D11 `:1372-1382`); docstrings
match; oracles listed above; stale-identity unpinned -> D1. (6)
omission - enumerated: prologue and authenticate-failure mutate
nothing -> no arm owed (spec-040 D11 table: refused before
authentication/mutation; failed login returns before establish);
establish/teardown armed; revalidation non-downgrade by contract. No
missing member.

### Reconciliation (after reading `## Findings`)

Verdicts agree on all four: F1 count-2-but-machinery-barred (my C1 +
attempt C), F2 below bar (my C2), F3 distinct rules (my C3), F4 own
contract (my C5 + attempt G). Challenge mapping: W1 C1/C3/C4/C5/C6
match my C1/C3/C5/G/C6 one-for-one with identical counts; W1 C2
(chain is L-only) discriminates L/O while my C2 counts the O-pair
wrap shape - compatible, both REJECT; W1 C7 matches my (A/B/E).
Shared forms: S1/S2/S3/S5/S6 match my (A/B)/(C)/(C)/(E)/(G); on S4 I
refine W1's "adds a traceback frame": extraction is mechanically
separable with identical `__context__` chaining (the handled
exception survives the call) but gains a frame and is a P11 1-liner -
refusal stands, verdict-neutral. My extra (F) all-four helper is
refused consistently. Owner: agree (arms inline, polarity at the
checkpoint). Matrix: agree on all six (my axis-1 rests on the closed
actor-write census, W1's on flavor fencing - compatible). No count
disagrees; no difference changes a verdict.

Zero-edit confirmed: item-scoped diff vs `ITEM_BASELINE` is the plan
+5 dispatch lines only; the 3 untracked package files predate the run
(Oct-10 mtimes); no file added by W1. Independent search: censuses
re-run whole-package (4 writes, 3 scope writes incl. success
write-back, 2 request writes, 2 flushes, 4 `except BaseException`
guards) - no 5th arm; 7 shared forms attempted, all refused; P11
scan finds no deletable abstraction. Family item carries no `###
Enumeration`; the site census above is its equivalent, re-run fully,
not sampled. Every rejection carries contract differences +
triggers; `## Pending execution` correctly lists none.

Load-bearing sub-claims verified: adapter `user` is a read-only
property (`utils/permissions.py:141-143`, no setter) so the
Channels cell split is forced; O1 durable-intact pinned at
`tests/auth/test_mutations.py:2315`; `actor_transition` exit
releases only the lease (`utils/sessions.py:396-399`);
cancellation split as stated (arms `BaseException`-compensate,
checkpoint `except Exception` never fabricates a verdict).

Execution (mine). Shared-tree single run: P1 probe (2) + all 13
committed arm-oracle rows green (`15 passed in 6.87s`) - P1 re-run
by me; P3's unscoped "11" covered by the 13-superset (W1 recorded
no P3 scope; immaterial, rows are committed and CI-gated).
Workspace `prove` at `dry/auth-fail-closed-anonymity-arms/verify-1`
(run `dry-20261012T105828-9197fd`, exit 0, slot-3): entry 1
reproduces P2 (baseline `2 passed` -> mutant fails exactly the
declared pair; restore filecmp + sha256 proved) - the negative
control (attribution-destruction mutant refused by the probe) holds
from my run; entry 2 (downgrade mutant, `expect_failing: []`):
`14 passed` baseline and `14 passed` under the mutant over the 9
committed denial rows - D1 confirmed by execution. P2's restore at
current bytes holds: 15/15 fingerprints re-match
(`consumers.py 24aa6f3d69be`), HEAD `c37a08a0` unmoved.

D1 adjudicated: DEFECT (test gap, behavior present and correct -
P1 green - but unpinned on a security-relevant invariant).
Downgrade passes the suite (entry 2). Owning card: 053 test-debt
(a missing test; 056 is doc-debt per the item-3 precedent).
DANGER independently UNTRIGGERED: L arms anonymize-first with
sync un-cancellable writes before the fallible flush; O arms are
single sync writes; pre-mutation paths owe no arm; `:1077`
write-back runs only past the authenticated check; the D11 drain
reasoning verified against the latch/lease/close bodies. No
(Worker-2) defect beyond D1's confirmation. AGENTS.md prose: no
source diff to judge; `:NNN` refs allowed in this scratchpad
artifact; layout gate excludes it (`--check` clean); ruff N/A.

Verdict-neutral nits: (N1) matrix axis-2 "(consumers)"
parenthetical is unclear - the bridges composing arms by call are
the auth sync/async resolve bodies (verified at `:781/:783`,
`:826`, `:1002/:1006`); (N2) S4 reason refined above; (N3) "11 arm
oracles" vs 13 counted, P3 scope unrecorded. None warrants a
re-pass.

VERDICT: verified.
