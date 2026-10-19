# Review · Comments: `django_strawberry_framework/auth/mutations.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8a53fa0958877d9c10e62631deb5b38e2096d539

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for
this target and no Routed lead on this item),
`docs/review/rev-auth__mutations.md` (skeleton: `Status: reviewing`,
blank Path class), all three axis records with every `Handoff:` and
`## Cross-axis` section, then the WHOLE live target. Sibling
`rev-auth__mutations.performance.md` read whole (Status:
no-findings, Path class hot with the per-request/per-field reason,
14/14 hot-path bounds `ok`, 7 query shapes constant, R1-R7, no
`## Cross-axis` section; its Handoff asks only that a
resolver-body-touching finding re-run `probe_query_counts.py` -
this record's findings are prose-only, so the probes stand).
Sibling `rev-auth__mutations.mechanics.md` read whole (Status:
findings-recorded, one Low F1 consolidating
`django_strawberry_framework/auth/mutations.py::_SealedAuthHolderMeta`
into the owner's metaclass plus R1-R19, no `## Cross-axis`
section; its Handoff routes a GLOSSARY `is_active` omission and a
`resolvers.py` memoization out, and notes README's informal
"AllowAny" as docs prose, not a finding). No conflict with either
sibling: F1 deletes a class whose docstring this record grades
true (the grade goes moot with the class; no finding filed on
that prose), and F1's own test-docstring tail is Worker-2's prose
for the verify pass to grade. This record creates
`rev-auth__mutations.comments.md`.

Target read whole (1367 lines, blob `84183c89`). Dirty vs HEAD
(+84/-113, concurrent work: truth migration, the
`_authenticated_actor_or_none` simplification,
compensation-clause narrowing, `field_name_map` threading -
reviewed as it stands, no hunk attributed here) and byte-identical
to ITEM_BASELINE (`git diff 8a53fa09 --` over the target, the own
test module and `tests/auth/conftest.py` is empty). Own test
module `tests/auth/test_mutations.py` read whole (2689 lines, blob
`ff8a261d`; dirty vs HEAD, identical to ITEM_BASELINE).
`tests/auth/conftest.py` (35 lines, blob `a7e8a55e`) and
`tests/auth/_helpers.py` (39 lines, blob `996762b0`) read whole
(prose about the target's symbols: the `_sync_boundary_spy`
docstring, filed here as M6).

Instruments (all static; no workspace run was needed):
`review_inspect.py` census for the target under
`docs/review/temp-tests/auth-mutations/comments/inspect/` (JSON
`docs/review/temp-tests/auth-mutations/comments/mutations.json`);
an AST first-line census script at
`docs/review/temp-tests/auth-mutations/comments/census.py` (every
class + non-`test_` function first line in both graded files, run
verbatim in the shared tree);
`build_tree_md.py --list-docstrings` on both files (1 module, 0
breaking, each); `check_citations.py --paths <file> --substrings
--json` (target 4 citations, own tests 7 citations, 0
violations); the REVIEW.md provenance pattern plus `used to` /
`Tests that` / `Ensures` / voice-pronoun / `line \d+` scans over
both files. Every grade below is against the live text at the
fingerprints in this section, each claim checked against its body
and one real caller or authority: installed Django 6.1
(`SessionBase.save` / `flush` / `cycle_key` / `modified` /
`key_salt`, `auth.login` / `logout` backend selection,
`AbstractBaseUser.password`, `_get_backend_from_user`), installed
channels 4.3.2 (`auth.login` / `logout` rotation, persistence,
`request=None` signals), `docs/SPECS/spec-040-auth_mutations-0_0_13.md`
(Decisions 3/5/6/7/8/9, helper-reuse D1/D3/D6/D8/D12/D13/D16/D17,
D-N1/D-N2/D-N3, the re-record passage, the `DenyAll`
request-time-raise precedent), `pyproject.toml` (no
`AUTH_USER_MODEL` override read; fakeshop default `auth.User`),
and `git log -S` / `git show` dating for every staleness claim.

Other-module prose census: every other test module's prose about
the target's symbols (`tests/auth/test_queries.py` me-only bind
row: true; `tests/auth/test_sessions.py`: no auth-mutations prose;
`tests/test_routers.py` same-socket logout group incl. the
structural-exemption docstring: true, deferring to the verified
routers/consumers passes; `tests/mutations/test_sets.py`:
`register_mutation` hits are the sets homonym, no auth prose;
`examples/fakeshop/test_query/test_auth_api.py` module docstring,
SDL-shape row, strictness-holder row, enumeration-guard,
signal-compensation and cookie pins: true; `tests/base/test_init.py`
public-surface census comment: behavior true, card/version
narrative Routed as R2) was read and graded. Every package
module's prose about the target's symbols was read:
`types/finalizer.py` phase-2.5 comment (true),
`auth/__init__.py` module docstring (true),
`auth/queries.py` module docstring + `current_user` docstring
(true), `mutations/fields.py::_lazy_ref` promotion paragraph
(true), `mutations/resolvers.py::_model_write_step` D6 paragraph
(true), `consumers.py` revocation paragraph + predicate comment
(true, just verified, deferred), `utils/directives.py` module
docstring (auth halves true; the `DjangoConnectionField`
omission is the already-Routed list_field lead, not duplicated
here), `mutations/sets.py::make_declaration_registry` docstring
(stale pair + "two ledgers" census, Routed as R1).

The routers-subject history sentences in
`tests/auth/test_mutations.py::_channels_router` (paragraphs 1-2)
are owned by `rev-routers.comments.md`'s G-finding (deferred,
file untouched there); verified still present at this pass's
fingerprint and not re-filed. This record files only that
docstring's third paragraph (L2), which the routers pass left
unruled.

Cells: default, sharded, and pg are all `inapplicable by
construction` for this Comments pass (no database-reaching probe;
every Proof is a static count plus a grade judgment; Worker-2's
prose edits owe `--code-digest` identity, not cell runs). Cells
unverified: none. Run ids: none (no `workspace.py` runs).

Fingerprints (`git hash-object` of every file whose body was
read): `django_strawberry_framework/auth/mutations.py`
`84183c893fdbf258e112ccf6d1cc66f6bc50c513` (live, whole, dirty,
== ITEM_BASELINE); `tests/auth/test_mutations.py`
`ff8a261d09ca63a0f606673bf11b9262f2bb1f35` (live, whole, dirty,
== ITEM_BASELINE); `tests/auth/conftest.py`
`a7e8a55eea91684dbd1247325c4cf0af97c43662` (live, whole, dirty,
== ITEM_BASELINE); `tests/auth/_helpers.py`
`996762b0db5d527da12f636342a5ba45d86c99ed` (live, whole);
`tests/auth/test_queries.py`
`86fa35e3659ff838ac61a7bf5f9df6878f9bad2a` (surface-keyed region
+ census); `tests/auth/test_sessions.py`
`b71c84ecd4dc90b9af37518d186716f1d64d9a96` (scope-lock pointer
+ census); `tests/test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (same-socket logout
group); `tests/mutations/test_sets.py`
`69668c00e65d7a6fde011ad37f745e60c62854e9` (homonym census);
`tests/base/test_init.py`
`239648ed635fa67baa10bf5bd428cd127098088b` (surface-census
comment); `examples/fakeshop/test_query/test_auth_api.py`
`17fc9ddb7c31c5ae936795fe524f233b3a1e4304` (module docstring,
guard, signal, cookie, SDL, holder regions);
`examples/fakeshop/apps/accounts/schema.py`
`dd2e81b3474e7d0ce8c42eb573642addc579af1b` (AllowAny census);
`examples/fakeshop/config/settings.py`
`e2ba51142ef2921163a7d3b8a880ed109df4e3a8` + `test_settings.py`
`842e47530f471b96e9986240ff0931883f42f810` (`AUTH_USER_MODEL`
absence); `django_strawberry_framework/auth/queries.py`
`b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9` (module docstring,
alias namespace, `current_user` factory);
`django_strawberry_framework/auth/sessions.py`
`865d6e704d2df50bcad465ad3005eccb39e8c545` (invariant-12 home,
capability predicates);
`django_strawberry_framework/auth/__init__.py`
`2e480818424d4b130e613e3e2da027aaad7144ad` (whole);
`django_strawberry_framework/registry.py`
`27358cbcaa5a7d0e6caea7374b184e17d8124cde` (clear + subsystem
rows); `django_strawberry_framework/mutations/sets.py`
`21c15c0b92c6046a300bf62b317535af1ab3cd29` (validator,
declaration registry, `check_permission`, bind payload call);
`django_strawberry_framework/mutations/resolvers.py`
`c9cff0590157de85bd9374ab85588b00e62080e0` (`authorize_or_raise`,
decode/write steps, D6 paragraph);
`django_strawberry_framework/mutations/inputs.py`
`840da733f95678be5ea494bb6ab595c8425a1884` (shape naming,
payload builder, namespace row);
`django_strawberry_framework/mutations/fields.py`
`0e4d5ed1c7efbcbb4e70db9162f2ffc85460a699` (lazy-ref promotion,
field directives);
`django_strawberry_framework/mutations/permissions.py`
`55e5edf80c601f373c1802d34fc4e497919d17e7` (walk + model-permission
label); `django_strawberry_framework/utils/permissions.py`
`1c9cfd398e6096e03bda82ba93dfd66a6d2fb890` (`request_from_info`);
`django_strawberry_framework/utils/inputs.py`
`b5af8255dfa18a2ff423cdd2de211723c5a15590` (shape-name owner);
`django_strawberry_framework/utils/errors.py`
`6a389474293cbd471b732fd73ba2b8632205c938` (`field_error`);
`django_strawberry_framework/utils/directives.py`
`84f770d4830661387fa9e42e88429f51b3dbe362` (module docstring);
`django_strawberry_framework/utils/execution_mode.py`
`9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9` (dispatch decider);
`django_strawberry_framework/consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b` (revocation prose,
predicate comment);
`django_strawberry_framework/types/finalizer.py`
`b9d8acb2b9428cc8297550414ff86bdd98e0d1a7` (phase-2.5 comment);
`docs/SPECS/spec-040-auth_mutations-0_0_13.md`
`4c9c585c3a1d372ae7413823d3afe20b9f17bdc4` (Decisions +
directives + precedents);
`docs/review/review-0_0_15.md`
`c64670dd770856f62889ac3fdba9d221fc0e43af` (plan + ledger);
`docs/review/rev-auth__mutations.md`
`0d96992a3beaa129f3310d388a01425f7c20b4fd` (skeleton);
`docs/review/rev-auth__mutations.performance.md`
`4df964e8968d638d3cd3366b1f7972a868dffb97` (whole);
`docs/review/rev-auth__mutations.mechanics.md`
`5fc46e232314eb80f83703bfa06f1d4e1d766ce5` (whole);
`docs/review/rev-routers.comments.md`
`8f0c06da85119d2e988e8b9e699f4f8700a65038` (shape + G-finding +
Routed-format regions);
`docs/review/rev-consumers.comments.md`
`20dd334645dae9b075dc1669c134962ee56f2f78` (predicate-finding
region); `docs/review/rev-consumers.md`
`a1b4d0088f6f2f01d9ac962385411bfe902e9780` (implementation
region); `docs/review/rev-schema.comments.md`
`dcd545ea6021de39a81c09ae5176c55a6603a517` (mood-consensus
regions); `docs/review/rev-sets_mixins.comments.md`
`d67f7fa013dc63944e79f31177d1703a7cea45fc` (mood-consensus
region). A finding's Freshness lists only files beyond these:
none.

## Findings

### High

None.

### Medium

#### M1: the declaration-ledger comment still cites "the hand row in `registry.py`"

- Observation: the `_auth_declaration_registry` comment says the
  ledger is "Cleared by ``TypeRegistry.clear()`` ONLY (the hand row
  in ``registry.py``)". There is no hand row in `registry.py`:
  `48f9f65d` ("Refactor subsystem clear registration and
  handling") replaced hand-maintained per-subsystem rows with
  owner-registered `register_subsystem_clear` callbacks (the
  auth row is the `owner="auth.declarations"` call six lines
  below the comment), and `registry.py::TypeRegistry.clear`
  now documents that subsystems announce their own teardown
  instead of leaving rows behind there. The commit updated this
  file's module-docstring twin ("a hand row beside
  ``clear_mutation_registry`` ..." became "an owner-registered
  callback without the ``before_bind`` phase flag") and missed
  this comment.
- Evidence: `git show 48f9f65d` hunk read (module docstring
  reworded, ledger comment untouched); live `registry.py` clear
  body read (iterates `iter_subsystem_clears()`, no per-subsystem
  rows); live auth registration row read
  (`register_subsystem_clear(clear_auth_mutation_registry,
  owner="auth.declarations")`).
- Impact: a reader auditing the clear lifecycle looks for a row
  in `registry.py` that cannot exist by design, and misses the
  owner-registered row that actually governs the ledger.
- Severity: Medium (stale comment on internal code).
- Recommendation: reword the parenthetical to the
  owner-registered row; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'hand row' django_strawberry_framework/auth/mutations.py` prints `0` (1 today); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/mutations.py`
  (`_auth_declaration_registry` comment).
- Grade: stale.
- Text-before:
  `Cleared by ``TypeRegistry.clear()`` ONLY (the hand row in ``registry.py``), never by the pre-bind reset - declarations must survive a recover-in-place re-finalize so ``bind_auth_mutations()`` can re-read them.`
- Text-after:
  `Cleared by ``TypeRegistry.clear()`` ONLY (the owner-registered ``auth.declarations`` row below), never by the pre-bind reset - declarations must survive a recover-in-place re-finalize so ``bind_auth_mutations()`` can re-read them.`

#### M2: the family-label comment claims all four auth fields resolve under it; `register` never does

- Observation: the `_AUTH_FAMILY_LABEL` comment says it is "The
  one family label every auth surface resolves its request
  under" so wording "cannot drift between the four auth
  fields". `register` never resolves under it: no framework
  `request_from_info` call exists anywhere on the register path
  (`mutations/resolvers.py` and `mutations/fields.py` carry
  none; the rider rides `run_write_pipeline_sync`, whose gate
  delegates to the configured permission classes), so a
  `register` request resolves under whatever label its gates
  use - `DjangoModelPermission` resolves under `"DjangoMutation"`
  (`mutations/permissions.py:170`), a custom gate under its own.
  Only `login` / `logout` / `me` resolve under `"AuthMutation"`
  (three call sites in this module, one in `auth/queries.py`).
- Evidence: package-wide `request_from_info(` caller census (4
  auth-family sites + the `DjangoMutation`, `SerializerMutation`
  and FilterSet/OrderSet family sites); `authorize_or_raise` /
  `check_permission` / `run_permission_classes` bodies read
  (the holder travels to the hook as `mutation`; resolution
  happens inside the hook with its label).
- Impact: a reader takes "cannot drift between the four auth
  fields" literally and expects `register` misconfiguration
  errors to name `AuthMutation`; they name `DjangoMutation` (or
  the custom gate's label) instead.
- Severity: Medium (stale census on internal code; same class as
  the routers T1 scoping finding).
- Recommendation: scope the claim to the three fixed fields and
  name the register exception; see text-after.
- Must not change: n/a.
- Proof: `grep -c -e 'every auth surface' -e 'the four auth fields' django_strawberry_framework/auth/mutations.py` prints `0` (2 today, both in this comment); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/mutations.py`
  (`_AUTH_FAMILY_LABEL` comment).
- Grade: stale.
- Text-before:
  `The one family label every auth surface resolves its request under (the spec-040 D1 reuse directive): a single module-level constant, never a per-field string literal, so the ``request_from_info`` resolution wording cannot drift between the four auth fields.`
- Text-after:
  `The one family label the three fixed auth fields resolve their request under (the spec-040 D1 reuse directive): a single module-level constant, never a per-field string literal, so the ``request_from_info`` resolution wording cannot drift between ``login`` / ``logout`` / ``me`` (``register`` rides the write skeleton, whose permission classes resolve under their own labels).`

#### M3: the register decode docstring still promises UNSET passwords are always captured; they yield `None` since `99a9f2d7`

- Observation: `django_strawberry_framework/auth/mutations.py::_register_decode_step`
  ends "``password`` is a required input field
  (``AbstractBaseUser.password`` has no default / blank), so a
  reached decode always captured it." Since `99a9f2d7` the body
  returns `excluded_values.get("password")` (was
  `excluded_values["password"]`), so a reached decode with an
  UNSET password returns `raw_password=None` - pinned by
  `tests/auth/test_mutations.py::test_register_decode_step_with_unset_password_returns_none_password`
  ("safely returns None when password is omitted/UNSET instead
  of raising KeyError"), with the write step's null guard as
  the downstream consumer. The commit changed the body, added
  the null/non-`str` write guards and the three
  defense-in-depth tests, and left this sentence untouched.
- Evidence: `git show 99a9f2d7` hunks read (body `.get`,
  write-step guards, new tests); `fa704722` pre-image read
  (`["password"]` + the same sentence, true then only because
  UNSET raised); live test body read (tuple unpacks,
  `raw_password is None` asserted).
- Impact: the docstring's absolute ("always captured")
  contradicts the pinned contract a reader must implement
  against: UNSET yields `None`, and the null guard below is
  load-bearing, not dead.
- Severity: Medium (stale docstring sentence on internal code).
- Recommendation: restate as the real-path guarantee plus the
  UNSET-`None` handoff; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'always captured it' django_strawberry_framework/auth/mutations.py` prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/mutations.py::_register_decode_step`.
- Grade: stale.
- Text-before:
  ```password`` is a required input field (``AbstractBaseUser.password`` has no default / blank), so a reached decode always captured it.`
- Text-after:
  ```password`` is a required input field (``AbstractBaseUser.password`` has no default / blank), so the real path always provides it; an UNSET password yields ``None`` here and the write step rejects it as null.`

#### M4: the Channels logout docstring says an `asave()` after `flush()` "would double-flush"; it would persist a fresh empty row

- Observation: `django_strawberry_framework/auth/mutations.py::_channels_logout`
  says "no explicit ``asave()`` is added here (that would
  double-flush)". An `asave()` is not a flush: `flush()` clears,
  deletes the durable row and sets the session key to `None`
  (installed Django 6.1 `SessionBase.flush`), so a subsequent
  `save()` takes the `session_key is None` branch into
  `create()` - a fresh EMPTY row INSERT, and on Channels HTTP a
  new cookie for it. The design (no `asave`; durability via the
  native teardown) is right; the parenthetical reason for it is
  wrong, and wrong in the understating direction (a reader may
  conclude the avoided call is merely redundant).
- Evidence: installed `SessionBase.flush` / `save` / `create`
  bodies read; `channels.auth.logout` body read (no save after
  its flush, corroborating the design).
- Impact: DRY principle 10, cited by the axis: a wrong stated
  reason is worse than none - it invites re-adding the call it
  exists to forbid.
- Severity: Medium (wrong stated reason on internal code).
- Recommendation: name what the avoided call actually does; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'that would double-flush' django_strawberry_framework/auth/mutations.py` prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/mutations.py::_channels_logout`.
- Grade: stale (false mechanism gloss across the supported
  range, not by a body change since).
- Text-before:
  `Channels' flush is itself durable, so no explicit ``asave()`` is added here (that would double-flush); logout's durability requirement is complete via the native teardown, unlike login's key-write which needs the explicit save.`
- Text-after:
  `Channels' flush is itself durable, so no explicit ``asave()`` is added here (a save after ``flush()`` would persist a fresh empty row); logout's durability requirement is complete via the native teardown, unlike login's key-write which needs the explicit save.`

#### M5: the dispatch-split test docstring names `in_async_context`; dispatch moved to `async_execution()` in `92e4efeb`

- Observation: `tests/auth/test_mutations.py::test_auth_field_dispatch_splits_sync_and_async_resolver_bodies`
  says "``_make_auth_field`` picks the sync body vs the async
  body by ``in_async_context``." The dispatcher in
  `django_strawberry_framework/auth/mutations.py::_make_auth_field`
  resolves "via ``async_execution()``" (the target's own
  docstring, current): `92e4efeb` ("Own the executor mode per
  operation") moved every `in_async_context` dispatch site to
  the operation-mode-aware `async_execution()`, whose commit
  message states the two observably disagree ("whenever
  `execute_sync` is called from inside an asynchronous
  operation") and which adds a `SyncMisuseError` third state
  the bare loop check has no notion of. The test docstring was
  born in `c8346750` under the old dispatcher and missed the
  move.
- Evidence: `git log -S` dates the docstring to `c8346750`;
  `git show 92e4efeb` read (removes the auth
  `in_async_context` import, message states the divergence);
  live `utils/execution_mode.py::async_execution` body read
  (bound-mode decision + third-state raise, ambient fallback
  only).
- Impact: the docstring attributes the sync/async pick to a
  decider that is neither the direct seam nor behaviorally
  equivalent to it on the bound-mode (normal `DjangoSchema`)
  path.
- Severity: Medium (stale mechanism in a test docstring stating
  behavior).
- Recommendation: name the current decider, mirroring the
  target docstring; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'by ``in_async_context``' tests/auth/test_mutations.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_mutations.py::test_auth_field_dispatch_splits_sync_and_async_resolver_bodies`.
- Grade: stale.
- Text-before:
  ```_make_auth_field`` picks the sync body vs the async body by ``in_async_context``.`
- Text-after:
  ```_make_auth_field`` picks the sync body vs the async body by ``async_execution``.`

#### M6: the shared spy fixture docstring says login/logout ride the interim bridge; only `current_user` does

- Observation: `tests/auth/conftest.py::_sync_boundary_spy` says
  "Both ``login`` / ``logout`` and ``current_user`` ride the
  same ``_make_auth_field`` dispatch seam and the same
  ``_sync_bridged_async_body`` interim async body". Only
  `current_user` rides the bridge (`auth/queries.py` passes
  `_sync_bridged_async_body(sync_body)`); `login` / `logout`
  await native async bodies
  (`_login_resolve_body_async` / `_logout_resolve_body_async`,
  passed as `functools.partial`s at the factories), which cross
  `run_in_one_sync_boundary` directly. Both the native bodies
  and the sentence landed in `c8346750`, so the sentence never
  described the landed tree. The spy's counting contract (each
  async-body await crosses the worker exactly once) stays true;
  only the shared-body mechanism is false.
- Evidence: factory `async_body=` arguments read (native
  partials vs bridge call); `_login_resolve_body_async` /
  `_logout_resolve_body_async` bodies read (exactly one worker
  crossing per arm); `git show c8346750` counts (native bodies
  0 before / 4 after; sentence introduced by the same commit).
- Impact: a reader extending the async tests believes all three
  fields share one interim body and may "fix" login/logout by
  routing them back through the bridge the native bodies
  deliberately replaced.
- Severity: Medium (stale mechanism in shared test prose).
- Recommendation: state the mixed world (bridge for `me`,
  native for login/logout, one shared worker for all); see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'the same ``_sync_bridged_async_body``' tests/auth/conftest.py` prints `0` (1 today); the rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/conftest.py::_sync_boundary_spy`.
- Grade: stale (born-stale in `c8346750`; false across the
  supported range, not by a later body change).
- Text-before:
  `Both ``login`` / ``logout`` and ``current_user`` ride the same ``_make_auth_field`` dispatch seam and the same ``_sync_bridged_async_body`` interim async body, which bridges to the sync body through this ONE shared worker. Counting its calls counts how many times the native async body was awaited (and so proves which path resolved the field).`
- Text-after:
  `Both ``login`` / ``logout`` and ``current_user`` ride the same ``_make_auth_field`` dispatch seam and cross this ONE shared ``run_in_one_sync_boundary`` worker - ``current_user`` through the ``_sync_bridged_async_body`` interim bridge, ``login`` / ``logout`` through their native async bodies. Counting its calls counts how many times an async body was awaited (and so proves which path resolved the field).`

### Low

#### L1: "Since spec-046" temporal prefixes on the two sync-body router sentences

- Observation: `django_strawberry_framework/auth/mutations.py::_login_resolve_body`
  and `::_logout_resolve_body` both open "Since spec-046 the
  package router serves no HTTP at all, so ...". The
  present-tense rule is true (the Mechanics sibling
  corroborates it at R4); the "Since spec-046" prefix narrates
  when the rule arrived - file history in the shape the
  routers G-finding filed ("Through ``0.0.14`` ..."), not a
  content-bearing Decision pointer.
- Evidence: both sentences read whole; spec-046 Decision 2
  (HTTP to the consumer's own Django ASGI application) is the
  content the prefix gestures at, per the routers
  G-finding's kept pointer.
- Impact: trivial arrival-history on two shipped docstrings.
- Severity: Low.
- Recommendation: convert the prefix into the kept Decision
  pointer, mirroring the routers G text-after; see text-after
  (same edit, both sites).
- Must not change: n/a.
- Proof: `grep -c 'Since spec-046' django_strawberry_framework/auth/mutations.py` prints `0` (2 today); both rewritten sentences earn grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/auth/mutations.py::_login_resolve_body`,
  `django_strawberry_framework/auth/mutations.py::_logout_resolve_body`.
- Grade: process provenance.
- Text-before (shared):
  `Since spec-046 the package router serves no HTTP at all, so a Channels HTTP scope reaches here only from a consumer the project mounted itself.`
- Text-after (shared):
  `The package router serves no HTTP at all (spec-046 Decision 2 gives HTTP to the consumer's own Django ASGI application), so a Channels HTTP scope reaches here only from a consumer the project mounted itself.`

#### L2: the transport-harness docstring's third paragraph narrates the move ("unchanged", "original", "moved from the package")

- Observation: `tests/auth/test_mutations.py::_channels_router`'s
  third paragraph says the surface "is unchanged", the
  assertions "keep[] [their] original subject", and "only the
  harness ... moved from the package into this file". "Moved
  from" is REVIEW.md provenance vocabulary, and the paragraph
  otherwise restates file history the second paragraph already
  justifies (the router cannot be the harness). Its load - the
  assertions still test the shipped surface, not a fork - is
  real and survives a present-tense recast. Paragraphs 1-2 are
  the routers G-finding's (deferred, not re-filed here); this
  paragraph it left unruled.
- Evidence: docstring read whole against the composed harness
  (consumer-mounted `GraphQLHTTPConsumer`, the shape
  `auth/sessions.py`'s `Transport.CHANNELS_HTTP` arm serves).
- Impact: relocation history heading the suite's transport
  harness.
- Severity: Low.
- Recommendation: keep the shipped-surface reassurance,
  drop the history; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'moved from the' tests/auth/test_mutations.py` prints `0` (1 today; the phrase wraps across lines 1663-1664); the rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_mutations.py::_channels_router`
  (third paragraph).
- Grade: process provenance.
- Text-before:
  `The Channels-HTTP auth surface itself is unchanged and still shipped: ``auth/sessions.py``'s ``Transport.CHANNELS_HTTP`` arm serves any consumer who mounts Strawberry's ``GraphQLHTTPConsumer`` themselves, which is precisely the shape composed here. Every assertion in the tests below therefore keeps its original subject; only the harness that supplies the transport moved from the package into this file.`
- Text-after:
  `The Channels-HTTP auth surface is still shipped: ``auth/sessions.py``'s ``Transport.CHANNELS_HTTP`` arm serves any consumer mounting Strawberry's ``GraphQLHTTPConsumer`` themselves - the shape composed here - so every assertion below tests the shipped surface through this file's harness.`

#### L3: five test docstrings open with "Row 5/6/7/9/12" ordinals whose table exists nowhere

- Observation: five docstrings open `Row 5`, `Row 6`, `Row 7`,
  `Row 9`, `Row 12` (non-consecutive; siblings 1-4, 8, 10, 11
  nowhere). The numbered table is on no reader path: not in
  spec-040, not in `docs/`, not in the live tier, not in the
  introducing commit's message (`c8346750`), not in any
  per-cycle doc. START.md cites contracts by content, never
  ordinal, and the defect test is exactly this (nothing
  establishes the home). Each remainder already states the
  behavior.
- Evidence: repo-wide `Row [0-9]` census (5 hits, all in this
  file); spec, docs, live-tier, commit-message and
  per-cycle-dir searches all empty.
- Impact: five unresolvable pointers; a reader cannot check
  coverage against the plan they imply.
- Severity: Low.
- Recommendation: drop the ordinals (capitalize the exposed
  first word); see text-after list, in Symbol order.
- Must not change: n/a.
- Proof: `grep -c -e '"""Row 5' -e '"""Row 6' -e '"""Row 7' -e '"""Row 9' -e '"""Row 12' tests/auth/test_mutations.py` prints `0` (5 today, each anchor matching exactly its site); every rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_mutations.py::test_login_payload_construction_failure_is_execution_error_session_untouched`,
  `tests/auth/test_mutations.py::test_login_backend_selection_failure_compensates`,
  `tests/auth/test_mutations.py::test_login_session_cycle_failure_keeps_actor_anonymous_and_surfaces_original`,
  `tests/auth/test_mutations.py::test_login_explicit_save_failure_compensates`,
  `tests/auth/test_mutations.py::test_login_cleanup_failure_retains_primary_and_chains_cleanup`.
- Grade: process provenance (plan residue).
- Text-before / text-after, per site in Symbol order:
  `Row 5 (the one justified mock): a payload build after authenticate never mutates the session.` /
  `The one justified mock: a payload build after authenticate never mutates the session.`
  `Row 6: multi-backend + a stripped ``user.backend`` -> login-time ``ValueError`` + compensation.` /
  `Multi-backend + a stripped ``user.backend`` -> login-time ``ValueError`` + compensation.`
  `Row 7: a session-store outage during rotation -> no success, actor anonymous, error observable.` /
  `A session-store outage during rotation -> no success, actor anonymous, error observable.`
  `Row 9: the explicit in-resolver ``save`` failing -> compensation, no candidate actor remains.` /
  `The explicit in-resolver ``save`` failing -> compensation, no candidate actor remains.`
  `Row 12: a raising signal (primary) + a raising ``delete`` (cleanup) -> primary retained, cleanup chained.` /
  `A raising signal (primary) + a raising ``delete`` (cleanup) -> primary retained, cleanup chained.`

#### L4: two "(Stage 0)" pointers name a stage defined nowhere on any reader path

- Observation: two docstrings carry "Stage 0" - "(real-object
  manipulation, per Stage 0)" and "The receiver fires BEFORE
  ``flush`` (Stage 0)". The token appears nowhere else:
  not in spec-040, not in the package, not in `docs/`,
  KANBAN or BACKLOG, not in per-cycle docs. It is not the
  target's numbered login/logout steps (1-5 / 1-3) and not a
  DRY/HUNT stage. Both sentences are complete and true
  without the parenthetical.
- Evidence: repo-wide `Stage 0` census (2 hits, both filed
  here); target step-numbering read (no stage zero).
- Impact: opaque process pointer; a reader cannot resolve what
  "Stage 0" obliges.
- Severity: Low.
- Recommendation: delete both parentheticals; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Stage 0' tests/auth/test_mutations.py` prints `0` (2 today); both rewritten sentences earn grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_mutations.py::test_login_backend_selection_failure_compensates`,
  `tests/auth/test_mutations.py::test_django_logout_signal_failure_no_ok_and_actor_anonymized`.
- Grade: process provenance.
- Text-before / text-after, per site in Symbol order:
  `the annotation is removed test-side (real-object manipulation, per Stage 0) after a REAL authenticate so ``_get_backend_from_user`` raises.` /
  `the annotation is removed test-side (real-object manipulation) after a REAL authenticate so ``_get_backend_from_user`` raises.`
  `The receiver fires BEFORE ``flush`` (Stage 0), so the durable row is NOT invalidated - and the resolver never falsely claims it was (no ok payload; the error propagates as a top-level GraphQL error).` /
  `The receiver fires BEFORE ``flush``, so the durable row is NOT invalidated - and the resolver never falsely claims it was (no ok payload; the error propagates as a top-level GraphQL error).`

#### L5: an empty "Enumeration guard" section header with zero rows beneath it

- Observation: the banner "Enumeration guard: one
  byte-identical envelope across failure classes" heads an
  empty section (two blanks, then the next banner). The guard
  it names is pinned live -
  `test_wrong_password_and_unknown_username_return_identical_envelope`
  plus the surrogate byte-identity rows in
  `examples/fakeshop/test_query/test_auth_api.py` - and no
  package row compares failure classes (the nearest,
  `test_async_channels_http_wrong_password_is_failed_login_envelope_session_untouched`,
  pins one class). The header is the residue of promoting the
  guard live: the stand-in went, its banner stayed.
- Evidence: banner + surrounding lines read (no test between
  the banners); live guard tests read (cross-class `==`
  asserted); package file censused for unknown-user rows
  (none).
- Impact: a dangling section promise; a placement audit from
  the banners miscounts where the guard lives.
- Severity: Low.
- Recommendation: delete the banner line and collapse the
  leftover blank pair.
- Must not change: n/a.
- Proof: `grep -c 'Enumeration guard: one byte-identical envelope' tests/auth/test_mutations.py` prints `0` (1 today).
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_mutations.py` (orphaned section
  banner).
- Grade: stale (promotion residue).
- Text-before:
  `Enumeration guard: one byte-identical envelope across failure classes`
- Text-after:
  `(delete the banner line; the guard it names is pinned live by ``test_wrong_password_and_unknown_username_return_identical_envelope``)`

#### L6: the logout banner's placement census omits the resident raising-receiver row

- Observation: the logout banner partitions rows into four
  package-owned kinds (Channels HTTP round trip, WS logout +
  reconnect, signed-cookie WS rejection, `delete` failure
  injection) and says "a raising ``user_logged_out`` receiver"
  lives in `test_auth_api.py`. But
  `test_django_logout_signal_failure_no_ok_and_actor_anonymized`
  stands here: Django HTTP, raising receiver, no store
  injection - fitting neither the owned four nor the live
  sentence's exclusivity. The row belongs here (its
  local-actor-anonymized-beside-the-surviving-row verdicts are
  in-process-only; the live twin pins the wire verdicts), so
  the banner, not the row, is wrong. (The login banner's
  symmetric sentence holds: every package login-signal row
  carries store injection or a Channels transport.)
- Evidence: banner read whole; the resident row's body read
  (plain store, local-actor + row-survival asserts); the live
  twin read (wire verdicts + still-authenticates follow-up);
  login-banner rows censused (all injection/Channels).
- Impact: a placement audit from the banner concludes no
  raising-receiver logout row stands here.
- Severity: Low.
- Recommendation: add the fifth owned row and scope the live
  sentence to the wire verdicts; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'in-process verdicts' tests/auth/test_mutations.py` prints `1` (0 today); the rewritten banner earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/auth/test_mutations.py` (logout section
  banner).
- Grade: stale (incomplete census).
- Text-before:
  `These package tests own the logout rows a live fakeshop ``/graphql/`` request cannot drive: the Channels HTTP round trip + anonymous residue flush (real HttpCommunicator), the real WebSocket server-side logout + reconnect-with-old-cookie invalidation, the signed-cookie WebSocket rejection before mutation, and SessionStore ``delete`` failure injection a ``django.test.Client`` cannot carry. The Django HTTP authenticated/anonymous round trip and a raising ``user_logged_out`` receiver live in ``examples/fakeshop/test_query/test_auth_api.py``.`
- Text-after:
  `These package tests own the logout rows a live fakeshop ``/graphql/`` request cannot drive: the Channels HTTP round trip + anonymous residue flush (real HttpCommunicator), the real WebSocket server-side logout + reconnect-with-old-cookie invalidation, the signed-cookie WebSocket rejection before mutation, SessionStore ``delete`` failure injection a ``django.test.Client`` cannot carry, and the raising-receiver in-process verdicts (local-actor anonymization beside the surviving row). The Django HTTP authenticated/anonymous round trip and the raising-receiver wire verdicts live in ``examples/fakeshop/test_query/test_auth_api.py``.`

## Rejected

- Descriptive function/method first lines (target: the two
  prologues, the four resolve bodies, `_channels_logout`, the
  register decode/write steps, the rider's `resolve_sync` /
  `resolve_async`; tests: `_request_with_store`). Rejected as
  style preference per the standing 9-item consensus
  (connection-R1, relay-R12, list_field-R6,
  resource_policy-R8, error_policy-R5, exceptions-R1,
  keyset-R1, conf-R1, scalars-R1, restated at schema-R1):
  family convention beats the imperative rule, and the
  register steps additionally twin the shared steps'
  descriptive form (`_model_decode_step` /
  `_model_write_step`), so recasting them would diverge twins.
  Trigger: a maintainer decision enforcing mood package-wide.
- Test-function docstrings stating behavior descriptively
  (present-tense third-person, e.g. "safely rejects ...").
  Rejected: test functions are unaffected by the mood rule;
  their rule is behavior statements (schema-R6), and every one
  here states behavior. No `Tests that` / `Ensures` /
  `Test that` opener in either graded file (verified by grep).
  Trigger: none.
- Helper-class first lines: every documented class in both
  graded files opens descriptive (AST census); no imperative
  class opener to file. Undocumented doubles (Mutation
  shells, gates, store-method overrides, `_Query`,
  `_StubContext` / `_StubInfo`, input shells, `Meta`s) and
  undocumented one-liner helpers stand per schema-R3/routers
  (single-use doubles whose contracts live in the using
  docstrings); undocumented `__init__`s and `has_permission` /
  `authenticate` overrides per schema-R4 (documented on the
  class / protocol). Trigger: a double becoming importable or
  asserted on directly, or a parameter gaining behavior the
  class docstring does not state.
- "Explicit empty-list default" twice (target
  `_declare_auth_surface` docstring, `login_mutation`
  docstring) for the `()` tuple the validator returns.
  Rejected: the owner module's own vocabulary writes the
  tuple default in list brackets (`[DjangoModelPermission]`),
  and the claim is effect-true (`None` normalizes identically
  to `[]`). Trigger: the owner rewording to tuple.
- "The legacy callable form (pre-1.10 ...)" (target
  `_authenticated_actor_or_none`). Rejected: upstream-historical
  age label, factually pinned, and consistent with the
  consumers item's just-verified "legacy-callable" wording for
  the same arm. Trigger: none.
- "Historical" in
  `test_model_decode_step_without_exclusion_keeps_the_historical_three_tuple`.
  Rejected: true age label for the pre-exclusion shape, same
  kept class as above. Trigger: none.
- "Today" twice ("today exactly the normalized
  ``permission_classes``", "the observation is captured
  today"). Rejected: unbanned vocabulary scoping substantive
  claims (a growable key; the twin capture-point guarantee),
  both corroborated by the bodies. Trigger: none.
- "Interim" / "later" in `_sync_bridged_async_body`
  ("the interim async resolver body", "injected later").
  Rejected: present-tense design status, not process history -
  the seam claims stay exact for the remaining consumer
  (`current_user`), and the login/logout native replacements
  corroborate rather than stale the prediction. Trigger: the
  bridge losing its last caller.
- The D8 / Decision-8 pair (`_failed_login_payload` "(the D8
  reuse directive)" for the `__all__` leaf vs
  `_SURFACE_FACTORY_NAMES` "(spec-040 Decision 8 ...)" for the
  bind validation). Rejected: different numbering schemes,
  both verified against the spec (helper-reuse D8 owns the
  sentinel; spec Decision 8 owns the primary bind
  validation). Trigger: none.
- "Raises ... the ``DenyAll`` precedent documents"
  (`test_gate_introspecting_the_mutation_object_raises_on_the_model_less_fields`).
  Rejected: spec-anchored phrasing (spec-040 names "the
  `DenyAll` request-time-raise precedent"). Trigger: none.
- "(spec-040 Decision 8)" on the reload-cycle register-arm
  test. Rejected: consistent attribution - the test pins
  Decision-8 validation surviving the second finalize, the
  framing the spec's own re-record passage (Decision 6
  section) and the target's `register_mutation` docstring use.
  Trigger: none.
- The "``036`` own-write exception" shorthand
  (`_run_register_pipeline_sync`). Rejected: established
  package vocabulary (same shorthand in
  `mutations/resolvers.py::_model_decode_step`), resolvable to
  the shipped spec-036. Trigger: none.
- "Consumer behaviour" spelling (target
  `_authenticated_actor_or_none`). Rejected: standing
  package vocabulary (25 `behaviour` hits incl. two more
  "consumer behaviour"). Trigger: none.
- "The OLD cookie can no longer authenticate" (line 2348
  comment). Rejected: present-tense post-teardown state rule,
  the schema-R7 kept class. Trigger: none.
- "`logout` / ``me``" field shorthand (target
  `_make_auth_field`) and "`me` returns" (queries prose).
  Rejected: the documented consumer field name (`me =
  current_user()` in both READMEs and the accounts schema).
  Trigger: a field rename.
- "Security invariant 12" (concurrency banner). Rejected: the
  invariant's content is stated at its owner
  (`auth/sessions.py::scope_session_lock`), with three
  consistent sites - resolvable, unlike the filed ordinals.
  Trigger: none.
- "(single-sited for every field factory)" (target
  `_make_auth_field` comment). Rejected: census-verified true
  (auth, `DjangoMutationField`, `DjangoConnectionField`,
  `DjangoNodeField(s)`, `DjangoListField` all route through
  `validated_field_directives`; register rides the mutation
  field's passthrough, already verified by the list_field
  pass). Trigger: a factory bypassing validation.
- Routed (owner: the `mutations/sets` item's Comments pass):
  `django_strawberry_framework/mutations/sets.py::make_declaration_registry`
  docstring gives the label pair
  `(``"DjangoMutation"`` / ``"DjangoFormMutation"``)` and says
  "the two ledgers stay disjoint", omitting the auth third
  flavor (`"AuthMutation"` ledger, this target) that spec-040
  added. Pre-existing phrasing; a reader auditing declaration
  ledgers from it undercounts two for three.
- Routed (owner: the Project integration item's Comments
  pass; extends that item's existing `test_init.py` 0.0.14
  lead): `tests/base/test_init.py:171-174` "(the
  auth-mutations card) owns the ``0.0.13`` cut (Decision 12)"
  card/version narrative inside the public-surface census
  comment. The behavioral claim beside it (no package-root
  auth exports, submodule-only per Decision 3) is true; only
  the card/version framing is provenance, project-subject
  like the already-routed lines below it.

Handoff: Comments review is closed with 6 Medium and 6 Low
findings and 2 Routed leads. The judgment calls a verifier
could revisit are L1 (temporal-plus-spec kept as a Decision
pointer rather than deleted, mirroring the routers G
text-after), L2 (filed on REVIEW.md's explicit "moved from"
listing against the true-claims leniency direction), M4's
Medium (wrong stated reason per DRY-10 rather than Low
clarity), and L6 (banner incompleteness rather than a
redundant test - the row's in-process verdicts are
live-unreachable, verified against the live twin). Everything
else was discharged by first-hand reads: every docstring and
comment in the target, the own test module whole, the shared
conftest/helpers whole, every other test module's prose about
the target's symbols, every package module's prose about them,
all spec Decisions and directives cited, both module first
lines passing `--list-docstrings`, all 11 citations resolving,
no `Tests that`/`Ensures`, no line-number cites, no voice
pronouns in prose, every public symbol documented. No defects;
no cross-axis text placed or
owed. For the verify pass: Mechanics F1 deletes
`_SealedAuthHolderMeta` (docstring graded true here; the grade
goes moot - no conflict) and rewrites one sentence of
`test_auth_permission_holder_head_is_sealed`'s docstring
(grade the new text); the F1 code move keeps every
`--code-digest` comparison on a reconstruction basis for the
target file. The sibling R1 phrasing ("resolution ... under
the single `_AUTH_FAMILY_LABEL`") shares M2's overclaim in
record prose, not production prose - noted, not filed.
Prose-only diffs move no bench figure and no query count, so
the Performance probes stand. Cells unverified: none (all
three inapplicable by construction).

## Verify comments

Verify pass 1 over Implement pass 1. Read, in order: AGENTS.md,
START.md, REVIEW.md, worker-2.md, the plan incl. `## Owned
changes` (3 rows for this item), all four records with every
Handoff, `docs/review/temp-tests/auth-mutations/diff/pass-1.diff`
whole (284 lines), then the live touched files. Fully static;
no workspace run. Live item diff is byte-identical to
pass-1.diff (modulo `index` lines), so the fingerprints below
are the pass's.

Fingerprints (`git hash-object`, live == pass post-image):
`django_strawberry_framework/auth/mutations.py` `98ae63f1`,
`tests/auth/test_mutations.py` `4cb49982`,
`tests/auth/conftest.py` `a5c413ba`. Item baseline
`8a53fa09`, cycle baseline `6ac69870`.

### Per-finding verdicts

Every Proof re-run verbatim in the shared tree; every landed
docstring/comment read whole and graded against its body plus
one authority.

- M1 (ledger comment): PASS. `grep -c 'hand row'
  django_strawberry_framework/auth/mutations.py` prints `0`
  (was 1). Landed parenthetical names "the owner-registered
  ``auth.declarations`` row below": the row
  `register_subsystem_clear(clear_auth_mutation_registry,
  owner="auth.declarations")` stands at target line 172, six
  lines below the comment (lines 160-165), and
  `registry.py::TypeRegistry.clear` iterates registered
  callbacks (no hand rows). Grade: true.
- M2 (family-label comment): PASS. `grep -c -e 'every auth
  surface' -e 'the four auth fields' ...` prints `0` (was 2).
  Census reproduced: 3 `request_from_info(...,
  family_label=_AUTH_FAMILY_LABEL)` sites in the target
  (lines 494/699/894) + 1 in `auth/queries.py:82`; zero
  `request_from_info` in `mutations/resolvers.py` /
  `mutations/fields.py` (the register path); `DjangoModelPermission`
  resolves under `"DjangoMutation"`
  (`mutations/permissions.py:170`). The "three fixed fields +
  register rides its own labels" scoping is exact. Grade: true.
- M3 (decode docstring): PASS. `grep -c 'always captured it'
  ...` prints `0` (was 1). Body returns
  `excluded_values.get("password")` (line 1031) and the write
  step rejects null/non-`str` (lines 1062/1064), so "the real
  path always provides it; an UNSET password yields ``None``
  here and the write step rejects it as null" states the
  pinned contract. Grade: true.
- M4 (Channels logout docstring): PASS. `grep -c 'that would
  double-flush' ...` prints `0` (was 1). Installed Django 6.1
  read: `SessionBase.flush` clears, deletes, sets
  `_session_key = None`; db `save()` on a `None` key takes
  the `create()` branch (fresh INSERT of the emptied
  session). "A save after ``flush()`` would persist a fresh
  empty row" is the true mechanism. Grade: true.
- M5 (dispatch docstring): PASS. `grep -c 'by
  ``in_async_context``' tests/auth/test_mutations.py` prints
  `0` (was 1). The dispatcher reads `async_execution()` at
  target line 408 with the docstring "via
  ``async_execution()``" (line 387); landed "by
  ``async_execution``" mirrors it. Grade: true.
- M6 (spy docstring): PASS. `grep -c 'the same
  ``_sync_bridged_async_body``' tests/auth/conftest.py`
  prints `0` (was 1). Factories pass native partials for
  login/logout (target lines 925/953) and
  `_sync_bridged_async_body(sync_body)` for `current_user`
  (`queries.py:115`); the mixed-world reword plus the kept
  one-shared-worker counting contract is exact. Grade: true.
- L1 (two router sentences): PASS. `grep -c 'Since spec-046'
  ...` prints `0` (was 2). Both sites carry the identical
  Decision pointer; spec-046 Decision 2 is "HTTP dispatches
  directly to a required, consumer-supplied Django ASGI
  application" (`docs/SPECS/spec-046-...:943`), which the
  landed parenthetical restates. Arrivals-history gone,
  content kept. Grade: true x2.
- L2 (harness paragraph): PASS. `grep -c 'moved from the'
  ...` prints `0` (was 1); "original subject" / "itself is
  unchanged" also print 0. Landed paragraph is present-tense
  shipped-surface reassurance; paragraphs 1-2 intact
  (`Through ``0.0.14``` still 1 hit - routers G deferred,
  untouched). Grade: true.
- L3 (five ordinals): PASS. The five-anchor `"""Row N` grep
  prints `0` (was 5). All five first lines read whole;
  exposed words capitalized, each remainder a behavior
  statement. Grade: true x5.
- L4 (two Stage-0 parentheticals): PASS. `grep -c 'Stage 0'
  ...` prints `0` (was 2). Both sentences complete and true
  without the parentheticals. Grade: true x2.
- L5 (orphan banner): PASS. `grep -c 'Enumeration guard: one
  byte-identical envelope' ...` prints `0` (was 1). Banner
  line deleted, exactly two blanks before the next banner
  (no leftover blank pair). Grade: true (deletion correct;
  guard pinned live per the record).
- L6 (logout banner): PASS. `grep -c 'in-process verdicts'
  ...` prints `1` (was 0). Resident row
  `test_django_logout_signal_failure_no_ok_and_actor_anonymized`
  stands at line 2084; live twin at
  `test_auth_api.py:1066` ("A raising ``user_logged_out``
  receiver ... the durable session survives"). The five-kind
  census + wire/in-process split is exact. Grade: true.

### F1 handoff items

- New seal-test sentence ("The holder rides the
  write-flavor metaclass guard
  (``DjangoMutationMetaclass``)..."): graded TRUE. The
  factory returns `DjangoMutationMetaclass(holder_name, (),
  ns)` (target line 242, import line 62); the sentence's
  remaining claims (hook receives holder, bypass class,
  synthesis honored, rebind/delete raise) are preserved by
  the owner's seal per Mech F1 "Must not change".
- Deleted `_SealedAuthHolderMeta` docstring grade: MOOT with
  the class, per the record Handoff.
- F1 disturbs no other graded claim: `grep -rn
  "_SealedAuthHolderMeta"` over source + tests + examples
  prints nothing (exit 1); old tail "validated permission
  set is captured once" prints nothing; the
  `_AuthMutationMetaSnapshot` docstring + snapshot-test
  prose (the only other seal prose) reference only
  `_ValidatedMutationMeta` and the snapshot's own seal,
  both untouched.

### Gates and sweeps

- `check_citations.py --paths <all three touched files>
  --substrings --json`: exit 0, 10 checked, 0 violations, 0
  warnings. (Record counted 11; the deleted metaclass
  docstring carried the 11th citation - delta explained.)
- `build_tree_md.py --list-docstrings` on all three files:
  3 modules, 0 breaking (first lines untouched, no TREE.md
  render owed).
- Provenance sweep over the 46 added lines: `spec-040 D1`
  (M2, carried pointer) and `spec-046` x2 (L1, kept
  Decision pointers) are the kept class; "round" hits are
  `run_in_one_sync_boundary` and "round trip" substrings,
  not review rounds. No `Tests that` / `Ensures` /
  `used to`, no voice pronouns, no `line N` cites in added
  lines.
- No new defects found. No `Routed` leads (the record's R1/R2
  stand filed).

Scratch: `docs/review/temp-tests/auth-mutations/verify-comments-1/`
(`added-lines.txt`, `citations.json`, `live-item.diff` +
no-index pair).

Handoff: Comments verify closes pass 1 with 12/12 findings
passing. The one judgment call carried forward is L1's
kept-Decision-pointer shape (mirrors routers G; upheld).
Mechanics/Performance verifiers own the F1 behavior and the
`--code-digest` reconstruction comparison; this pass graded
prose only. Open threads: none.

Status: verified
