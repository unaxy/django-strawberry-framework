# DRY review: `authenticated-actor-predicate`

Status: verified
Run: 0.0.15 2026-10-12-24

## System trace

Three spellings of authenticated-vs-anonymous classification. (a) `auth/mutations.py:498`
`_authenticated_actor_or_none`: None arm + legacy-callable arm + disposed-awaitable arm +
flag read; 2 consumers (logout `ok` via `_logout_observation`, `me` via
`_current_user_resolve_body`); docstring scopes it to "the session-auth surfaces"
(spec-040 D5/D7). (b) `consumers.py:1025` + `:1066` inside `_actor_is_current`: the
plain-attribute core (`X is None or not getattr(X, "is_authenticated", False)`) spelled
twice, with the recorded reason (`:1015-1021`: no scope actor takes the callable/awaitable
arms; auth-private import would drag Strawberry into transport) and the recorded
third-site promotion trigger (`:1022-1024`, to `utils/permissions.py`). (c) `views.py:1018`
`getattr(user, "is_authenticated", None)`: read-and-discarded evaluation touch (spec-046 D6).

Whole-package sweep: `is_authenticated` reads = exactly these 4 code sites (plus prose);
`AnonymousUser` verdicts = teardown writes + the deliberate non-downgrade (`:1067`);
`user`-None branches = the helper, the twin, the eval touch, `DjangoModelPermission`
(FENCED perm-based, reads no flag), `require_session` (config error, not classification).
`auth/sessions.py` = transports only; `utils/permissions.py` = request recognition only
(ITEM 5 territory); the provenance latch is FENCED context.

Population verified against installed `channels/auth.py`: post-`AuthMiddlewareStack`
scope actors = None (no key) | `UserLazyObject` (resolving to user or `AnonymousUser`) |
real user (login/write-back) | `AnonymousUser` (logout/`get_user` invalid shapes);
`_refreshed_actor` = `get_user` answer | failure-None. Trust reading (GOAL.md): app
Python trusted; package no more secure than Django. Django's own `login_required` and
`channels.auth.logout` read the flag by truthiness without calling/disposing, so the
helper's arms are beyond-Django hardening, live only for consumer-model shapes that
already defeat Django itself. No servable shape missed within the boundary: DANGER
clause not triggered, no blocked report. Floor `Django>=5.2.16`; flag a bool property
since 1.10 (installed 6.1.2 checked at both classes).

## Verification

### Matrix

1. Cross-flavor: login/logout/`me` share the helper by call; write flavors gate by
   perm (fenced); no second classifier. Discharged by sweep.
2. Sync/async twins: helper is sync-only (async paths call it inside the one sync
   boundary); the core is a sync expression inside an async fn. No twin.
3. Derived-twice: the twice-derived core = this item's question; judged in F1/F2.
4. Inverse/round-trip: classification has no inverse; teardown/write-back are state
   transitions, not inverses. Inapplicable.
5. Other media: spec-040 D5/D7+DoD, spec-046 D6/D11, oracles in `tests/auth`,
   `tests/test_routers.py`, `test_transport_api.py`. Listed; D1 staleness found.
6. Omission: family enumerated (above); every member classified; no member lacks an
   applicable guard. Discharged.

### Challenges

- C1 drop the legacy-callable arm: helper only (count 1; fail-open direction, barred).
- C2 flip the getattr default to raise: helper + twin x2 (2 rules, 3 spellings; breaks
  the pinned duck-type degradation, barred).
- C3 add an arm to the twin (population falsified): twin x2 (count 2); correct
  landing is promotion per the recorded trigger, not local duplication.
- C4 views needs a verdict, not a touch: fires the `:1022-1024` trigger (count 3).
- C5 unify (a)+(b) via a shared full classifier: behavior change on pathological
  shapes (fail-closed flip + disposal side effect) + helper split + rewire; removes
  no servable obligation (arms dead at consumers sites in-boundary). Rejected (F1).

## Findings

### F1 (a)-vs-(b): REJECT unification, stay separate

Contract difference (4x): (i) population: request actors incl. lazy/foreign/
pathological-consumer vs lease-scoped actors (scope set above; refreshed =
`get_user`|failure-None); (ii) arms: beyond-Django hardening vs Django/channels-posture
core; (iii) layering: auth-private vs transport (channels/strawberry-free, test-pinned
by `test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package`);
(iv) consequence: nullable actor/`ok` vs liveness verdict under the actor lease.
Sites: helper = definition (auth); twin = 2 applications (transport); no bool core
exists that the helper could compose (it returns the actor, arms interleaved).
Challenges: C1/C2/C5. Owner stays split (auth surface vs transport liveness).
Migration/shrinkage: none (zero-edit). Behavioral proof: P1 (execution-verified,
run dry-20261012T102129-bf0d35, 1 passed): helper verdict vs core branch agree on all
9 servable shapes, split pinned on 2 pathological shapes; existing oracles pin each
side (F4 + twin rows below). Negative control: P1's pathological rows ARE the bypass
attempts (core reloads, helper refuses) — divergence documented, unservable in-boundary.
Triggers: servable arm-shape (falsifies population claim) ->
promote a full classifier; auth opt-in layering change; third site.

### F2 twin `:1025`/`:1066`: REJECT, below bar

One rule spelled twice (shared classification function), but: single-expression
verdict arms (run-14 f33 precedent); None sources differ (structural absence vs
fail-closed assignment) and consequences differ (provenance carve-out vs deny); core
is stable Django-owned semantics (Django changes excluded by the bar); no plausible
our-rule change lands locally (C3 lands as promotion); co-located, comment-linked,
test-pinned at both sites (`:1025` by `test_actor_without_is_authenticated_attribute...`
+ `test_an_anonymous_socket_is_not_revalidated`; `:1066` by revoked/valid/failure
rows + P1's recorder-anonymous denials). Challenges: C3. Migration/shrinkage: none.
Proofs: P1 execution-verified (both lines per shape) + cited oracles. No negative
control beyond F1's (misclassification pinned by refuse/admit rows). Triggers:
recorded third-site promotion; arm addition; spelling divergence.

### F3 (c) views touch: REJECT, different contract

Evaluation, not classification (spec-046 D6): no verdict, discarded result, default
unobservable (only the read side effect + AttributeError suppression observe).
Composing the helper would ADD call + dispose side effects (observable change);
composing a bool core would add a branch the contract never needs. Not a third site;
`:1022-1024` trigger unfired via (c). Proof: live
`test_the_async_package_view_hands_sync_hooks_an_evaluated_session_actor` (3 verdicts;
static-reviewed: evaluation proven, no verdict exists to dispute) + static arm
analysis. Trigger: views needing an authenticated-vs-anonymous VERDICT.

### F4 helper arms live-or-vestigial: CONFIRMED, no change

Arms spec'd (spec-040 D5/D7, modulo D1) and test-pinned
(`test_legacy_callable_..._classifies`, `test_awaitable_..._anonymous`,
`test_legacy_callable_returning_an_awaitable...`, `test_custom_awaitable_...`,
`test_future_...`, `test_a_raising_..._propagates...`): vestigial for Django-shipped
classes on the floor, live only for pathological consumer models; deletion is
fail-open, barred. Owner stays `auth/mutations.py`. No migration, no shrinkage.

### Freshness (worktree bytes, `git hash-object`; HEAD `c37a08a0`, unmoved)

`consumers.py` 24aa6f3d69be; `auth/mutations.py` 217c6bff744a;
`auth/queries.py` b0c60920eb9d; `views.py` 82e95fa147a5;
`utils/permissions.py` dbb8f6021fa2; `utils/sessions.py` de3cf2c9ab3c;
`utils/querysets.py` f9267729db8f; `auth/sessions.py` 6e5fadb7afc1;
`mutations/permissions.py` 127575bb623f (fence, named); `test_routers.py` ab9b138a2fe5;
`auth/test_queries.py` b87ae0ce14fd; `auth/test_mutations.py` 2a224eb18c05;
`test_transport_api.py` ce099d5a1e80; spec-040 0a821df6477a; spec-046 2d4bb1d611e9;
GOAL.md 34fed47646a7; P1 probe e78bac79f936 (copy run abae9e/bf0d35, digest
sha256:423e64b7, shared unmoved); channels `auth.py` 9da53b03f7b5e (installed 4.3.2,
`AuthMiddlewareStack` population source). Searched population: every flag read,
`AnonymousUser` mention, `user`-None branch (counts in trace). Excluded (named):
`DjangoModelPermission`, latch, `require_session`, recognition.

## Defects

D1 spec-040 stale anonymity clauses (docs; unfixed; route to Worker-0 for homing):
D7 `:1275-1279` ("legacy callable collapses to null", "raising truthiness collapses
to null") + DoD `:2212-2215` ("legacy-callable ... never as authenticated") vs WT
contract "awaitable collapses, legacy result classifies (True -> user, test-pinned),
raises propagate (`test_a_raising_is_authenticated_propagates_to_the_error_policy`)".
Owner: spec-040 prose. (Folder-auth index already records the WT contract.)

## Judgment

Zero-edit REJECT on all unifications: (c) is an evaluation touch, the twin is one
rule spelled twice below bar, (a)/(b) are separate contracts with the population
claim verified in-boundary and layering test-pinned. Separations already recorded
at both owners; promotion trigger unfired; no security-path defect. D1 routed.

## What shrinks

Net package lines over `ITEM_BASELINE=70488521`: 0 (zero-edit; nothing to port).
Considered shapes: (S2) within-function closure for the twin (-1 spelling, +1 name;
rejected F2: no real obligation, f33 precedent, None-sources differ); (S3) promote
the bool core per trigger (rejected: trigger unfired, no third site); (S4) shared
full classifier splitting the helper (rejected F1: pathological-shape behavior
change + machinery + scatters the ONE definition). Census: 1 full definition
(4 arms, 2 consumers), 2 spelled cores (1 fn), 1 eval touch, 0 third sites.

## Independent verification (Worker-2)

Own trace (derived from source + installed deps, not inherited). Sites/roles:
(a) `auth/mutations.py:498` = 1 definition, 4 arms (None/absent, legacy-call,
disposed-awaitable, flag), 2 consumers (`:880` logout-ok, `queries.py:106`
inside `_current_user_resolve_body:83`); request-actor population.
(b) `consumers.py:1025` + `:1066` = 2 applications inside 1 definition
(`_actor_is_current`): scope actor -> provenance carve-out vs refreshed actor
-> deny; lease-scoped population. (c) `views.py:1018` = evaluation touch, no
verdict, different contract. Fenced (verified): `DjangoModelPermission`
(perm-based, reads no flag), `require_session` (config error), transports,
recognition, provenance latch. Owner I would choose: split (auth-private vs
transport liveness); bool-core promotion to `utils/permissions.py` iff a third
site fires the `:1022-1024` trigger. No P11 deletion: helper has 2 consumers;
the touch has 1 caller but carries a named boundary step + effect isolation.

Population (installed channels 4.3.2 `auth.py`, re-read in full): scope actors
= absent key | `UserLazyObject`->(user|`AnonymousUser`) | real user
(`login`/write-back `:1077`) | `AnonymousUser` (`logout`/`get_user`/package
compensations `:736`/`:976`); refreshed = `get_user` answer | failure-None.
No in-boundary writer produces a callable/awaitable-flag actor. Django 6.1.2:
both classes carry a bool `is_authenticated` property; `login_required` and
`channels.auth.logout` read it by truthiness without calling/disposing, so the
helper's arms are beyond-Django hardening. Divergence set derived by hand =
exactly {callable flag, awaitable flag} (core admits, helper refuses); both
unservable in-boundary (a consumer model breaking the bool-property contract
already defeats Django itself; GOAL.md "no more secure than they are" bounds
it out). DANGER untriggered; no blocked report.

Censuses re-run: `is_authenticated` code reads = exactly the 4 sites above
(+ prose); `AnonymousUser` = teardown writes + deliberate non-downgrade +
prose; `user`-None branches = helper, twin, touch, the two fenced sites. No
4th site. Own challenge counts: C1 = 1; C2 = 2 defs / 3 spellings (barred,
pinned degradation); C3 = 1 def / 2 spellings (lands as promotion); C4 =
trigger fires; C5 rejected (pathological-shape behavior change + machinery,
no servable obligation removed). Matrix: axis 4 inapplicable (a predicate has
no inverse; teardown/write-back mutate its input, they do not invert it);
axis 6 discharged (family enumerated via the three censuses, no member lacks
an applicable guard). F1/F2/F3 rejections + all triggers confirmed.

Proofs: P1 suffices, no execution owed from me — the 9+2 table is statically
decisive on 8 lines, P1 carries run-id/digest provenance, and unservability
is a writer-population argument execution cannot strengthen. F3 static review
suffices — "no verdict exists" is structural (result discarded, no consumer),
pinned by the cited live evaluation test. Negative controls confirmed (P1's
pathological rows = bypass attempts, divergence documented, unservable).
Freshness re-hashed: 9/9 package + 4/4 test + spec-040/046 + GOAL.md +
channels blobs match; HEAD `c37a08a0` unmoved (P1 probe hash is copy-scoped,
accepted on provenance). Diff: package diff vs ITEM_BASELINE empty, no new
source files; AGENTS prose + ruff N/A on zero-edit; `path:NN` cites permitted
in `dry-*.md`. D1 confirmed on both sides (spec D7/DoD text vs helper body +
`true-authenticates`/`propagates` oracles): real defect, spec-only -> 056
doc-debt for Worker-0 homing. Shape ruling: `## Pending execution` absent =
COMPLIANT per DRY.md "Absent when none" (zero deferred proofs, zero
witnesses) — verdict-neutral, no fix. Reconciliation: one counting difference
(C3: my 1-def/2-spellings vs W1's "count 2") — verdict-neutral, both below
bar; every other trace, count, and trigger converges. Verdict: verified.
