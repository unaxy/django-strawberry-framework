# Review · Comments: `django_strawberry_framework/auth/` integration

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5676d4fc6310a5ff0d075771593a0f3068eb9406

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds the three
verified auth file rows and no other row for this folder, plus the
Routed lead on this item judged here as R1),
`docs/review/rev-auth.md` (skeleton: `Status: reviewing`, blank
Path class). Sibling `rev-auth.performance.md` and
`rev-auth.mechanics.md` did not exist at close (siblings run
concurrently); no foreign Handoff or `## Cross-axis (for
Comments)` owed — the verifier confirms none appeared (open
thread 1). This record creates `rev-auth.comments.md`.

All nine closed folder-file records read whole (review +
verify sections, every Handoff): `rev-auth__mutations.*`,
`rev-auth__queries.*`, `rev-auth__sessions.*` (statuses
verified / verified / findings-recorded at read time for the
mutations trio — its comments verify had not landed when read;
verified for both other trios). No finding below re-files
theirs: each file's target prose and own-test-module prose
was graded there, and the two standing Routed leads out of
them (`mutations/sets.py` two-ledger census; `test_init.py`
card/version narrative) are not duplicated here.

Folder target read whole as one component:
`django_strawberry_framework/auth/__init__.py` (20 lines, the
item's Init file), plus the cross-module seams and every
folder-level ownership/lifecycle claim in the three module
docstrings (`auth/mutations.py` docstring + ledger/family
comments + `_declare_auth_surface` + import block;
`auth/queries.py` whole, 121 lines; `auth/sessions.py`
docstring + install-hint region). Folder-level test prose
read whole: `tests/auth/__init__.py` (the suite census, F1),
`tests/auth/conftest.py` (module docstring + spy docstring),
`tests/auth/_helpers.py` (module docstring + both helpers),
the three test-module docstrings, and the live-tier
`test_auth_api.py` module docstring + test-name census.
Authorities read at their owners: the
`register_subsystem_clear` rows (`mutations/inputs.py:243`,
`auth/queries.py:60`), the finalizer phase-2.5 comment +
`bind_auth()`-before-`bind_mutations()` order, the
package-wide auth-import census (sole production edge is the
finalizer's already-loaded-only `loaded_attr` string),
spec-040 Decision 3 anchor title, the GLOSSARY
`request_from_info` row (open thread 2), and the plan's
`## Decisions` glossary pattern. `git show fad17c20` /
`e6a33c46` date the suite census; `git log --diff-filter=A`
dates `test_sessions.py` (c8346750, before the census
rewrite).

Instruments (all static; no workspace run was needed):
`review_inspect.py` on the Init file under
`docs/review/temp-tests/auth-integration/comments/inspect/`
(JSON `.../comments/init.json`, leads only);
`build_tree_md.py --list-docstrings` on
`django_strawberry_framework/auth/` (4 modules, 0 breaking)
and on the three `tests/auth/` support files (3 modules, 0
breaking); `check_citations.py --paths
django_strawberry_framework/auth/__init__.py --substrings
--json` (0 citations, 0 violations); the REVIEW.md
provenance pattern over the four folder-owned prose files
(2 hits, both kept class: the spec-040 Decision 3 pointer,
the one-shared-worker wording); a saved AST helper-mood
census (`.../comments/census.py`, output
`.../comments/helpers.txt`).

Cells: default, sharded, and pg are all `inapplicable by
construction` for this Comments pass (no database-reaching
probe; the F1 Proof is three static counts plus a grade
judgment; Worker-2's prose edit owes `--code-digest`
identity, not cell runs). Cells unverified: none. Run ids:
none (no `workspace.py` runs).

Fingerprints (`git hash-object` of every file whose body was
read): `django_strawberry_framework/auth/__init__.py`
`2e480818424d4b130e613e3e2da027aaad7144ad` (live, whole);
`django_strawberry_framework/auth/mutations.py`
`98ae63f1965a08d28332ae6e24aa24ea39d9d511` (docstring,
ledger/family comments, `_declare_auth_surface`, imports);
`django_strawberry_framework/auth/queries.py`
`b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9` (live, whole);
`django_strawberry_framework/auth/sessions.py`
`e50011e6cae837a7b1322d704a7f8adbb69bcec3` (docstring,
install-hint region); `django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` (import census);
`django_strawberry_framework/types/finalizer.py`
`b9d8acb2b9428cc8297550414ff86bdd98e0d1a7` (phase-2.5
region); `django_strawberry_framework/mutations/inputs.py`
`840da733f95678be5ea494bb6ab595c8425a1884` (clear-row
region); `tests/auth/__init__.py`
`09e0f06d9c93719e6e75dbcd54e8c03255c655b0` (live, whole);
`tests/auth/conftest.py`
`a5c413ba57dfc3f97e4f3743f04851977de777de` (live, whole);
`tests/auth/_helpers.py`
`996762b0db5d527da12f636342a5ba45d86c99ed` (live, whole);
`tests/auth/test_mutations.py`
`4cb499820cbed5163777099e9c9804cf7a523b50` (module
docstring, helper census, `_request_with_store`, pin
spot-checks); `tests/auth/test_queries.py`
`a57722d438a10d7dc1bf68929bbbbc26e2473a28` (module
docstring, helper census, spy usage);
`tests/auth/test_sessions.py`
`b71c84ecd4dc90b9af37518d186716f1d64d9a96` (module
docstring, helper census, test-name census);
`tests/base/test_init.py`
`239648ed635fa67baa10bf5bd428cd127098088b` (surface-census
comment); `examples/fakeshop/test_query/test_auth_api.py`
`17fc9ddb7c31c5ae936795fe524f233b3a1e4304` (module
docstring, test-name census);
`docs/SPECS/spec-040-auth_mutations-0_0_13.md`
`4c9c585c3a1d372ae7413823d3afe20b9f17bdc4` (Decision 3
anchor); `docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`
(`request_from_info` row); `docs/review/review-0_0_15.md`
`3f5d15c2a28f7b4bb7dd2dafe87711a63b23cc36` (plan + ledger +
Decisions); `docs/review/rev-auth.md`
`0dd3f19bc7f6fc94d5cbf05fe3f765b4f42ef773` (skeleton);
`docs/review/rev-auth__mutations.performance.md`
`b9070df1d9696cb29a586400070af86526d1e169` (whole);
`docs/review/rev-auth__mutations.mechanics.md`
`c2c6fe2056cd71a64eb55f1faa769188e1914841` (whole);
`docs/review/rev-auth__mutations.comments.md`
`46dd3080dbf6e2e8552d98ae4b2992f7363c13da` (whole);
`docs/review/rev-auth__queries.performance.md`
`979d1c157c883feba16be414249285b40f813e78` (whole);
`docs/review/rev-auth__queries.mechanics.md`
`36a2e5f06ed2acdc260a368415d70f130a0b1f4a` (whole);
`docs/review/rev-auth__queries.comments.md`
`0d45a3d71948ea78ac5bf3d1254fe821ccc2c31a` (whole);
`docs/review/rev-auth__sessions.performance.md`
`43950dcac67ed65384893ce5f67b563a153ea6c2` (whole);
`docs/review/rev-auth__sessions.mechanics.md`
`ea3c900c5a125eb2d24a850fed969f0c23851c0c` (whole);
`docs/review/rev-auth__sessions.comments.md`
`8a1b6901d2bcdb02a5f15289465b063bcb90c1f5` (whole). A
finding's Freshness lists only files beyond these: none.

## Findings

### High

None.

### Medium

None.

### Low

#### F1: the suite docstring census omits the transport-boundary module and nine scattered pins

- Observation: `tests/auth/__init__.py` holds the suite as
  `ONLY` seven enumerated residues, but the enumeration
  misses a whole module and nine tests. Missing: (a) every
  `tests/auth/test_sessions.py` pin (28 tests: transport
  classification incl. the lazy/stand-in/install-hint arms,
  the session pre-check arms, the scope-lock lifecycle
  incl. immutable-scope/cancellation/corruption, signed-cookie
  detection incl. the subclass leg, the login/logout
  capability answers, the channels-absent path and the
  channels-free import proof); (b) the
  `test_async_has_permission_raises_sync_misuse_never_a_silent_allow`
  + `test_async_permission_hook_rejected_inside_the_sync_worker_too`
  `SyncMisuseError` pair and
  `test_sync_django_http_login_leaves_session_modified_for_the_cookie`
  in `tests/auth/test_mutations.py`; (c) the mapping-context
  request shape, the absent-user arms, the bare-string
  `directives` rejection, the legacy / awaitable / raising
  `is_authenticated` forms, and the async lazy-user forcing
  in `tests/auth/test_queries.py` (the five the queries L2
  paragraph now names). Every listed element IS present
  (verified: same-args/cache tests, decode/write guards,
  alias tests, throwaway-schema gate tests, store-fault
  tests, six dispatch-spy tests, communicator transport
  tests; no `config/asgi.py` on disk), so the census is
  true as far as it goes — maintained as exhaustive, with
  gaps.
- Evidence: the census was rewritten at `fad17c20` (the
  live promotion) to track the suite — commit message
  "tests/auth keeps only what no live request can drive:
  <enumeration>" plus the file rewrite in the same commit;
  `e6a33c46` since touched the first line only. The
  omitted module predates the rewrite (`test_sessions.py`
  born `c8346750`, July 2026; rewrite September 2026), so
  the gap is not a later addition the census never saw.
  The (c) pins are the L2-verify mapping (all 15
  `test_queries.py` tests mapped); the (b) pins stand at
  `test_mutations.py:817,842,2007`. No file pass graded
  this docstring: each graded its own test module whole,
  and the sessions pass's "support files clean" is a
  no-prose-about-its-symbols census, not a completeness
  grade.
- Impact: a reader relying on the suite census misses a
  whole module (28 tests) plus nine pins across the other
  two; a placement audit from it concludes the
  transport-boundary behavior is pinned nowhere.
- Severity: Low (incomplete census on internal prose;
  true as far as it goes; the queries-L2 precedent, same
  grade — nothing claimed is absent, which would be
  Medium-stale).
- Recommendation: extend the enumeration to name the
  three gap groups; keep the first line byte-identical so
  no TREE.md render is owed (body-only change). See
  text-after.
- Must not change: n/a.
- Proof: at `review/auth/integration/verify-comments-<n>`,
  shared tree: `grep -c "scope-lock" tests/auth/__init__.py`
  prints `1` (0 today); `grep -c "SyncMisuseError"
  tests/auth/__init__.py` prints `1` (0 today); `grep -c
  "directives" tests/auth/__init__.py` prints `1` (0
  today); the rewritten paragraph earns grade true (names
  all three gap groups; first line unchanged).
- Freshness: none beyond Trace.
- Symbol: `tests/auth/__init__.py` (module docstring body).
- Grade: incomplete census.
- Text-before:
  `Holds ONLY the residue a live fakeshop ``/graphql/`` request cannot drive: the surface-keyed declaration ledger / bind, register-rider factory cache and decode / write defense-in-depth, ``current_user`` alias lifecycle, permission-gate variants on isolated throwaway schemas (one-declaration-per-process vs the aggregate AllowAny default), session-store failure injection, dispatch spies, and Channels / WebSocket transport (no ``config/asgi.py``).`
- Text-after:
  `Holds ONLY the residue a live fakeshop ``/graphql/`` request cannot drive: the surface-keyed declaration ledger / bind, register-rider factory cache and decode / write defense-in-depth, ``current_user`` alias lifecycle, permission-gate variants on isolated throwaway schemas (one-declaration-per-process vs the aggregate AllowAny default), the async-permission ``SyncMisuseError`` discipline, ``request.session.modified``, the mapping-context request shape, the absent-user arms, the bare-string ``directives`` rejection, the legacy / awaitable / raising ``is_authenticated`` forms, the async lazy-user forcing, the transport-boundary unit pins (real-class-first classification, the scope-lock lifecycle, signed-cookie-engine detection, the login/logout capability answers, the channels-absent path and the channels-free import proof), session-store failure injection, dispatch spies, and Channels / WebSocket transport (no ``config/asgi.py``).`

## Looks-for discharge

Every Comments list entry: finding, `none` + reason, or
rejection + trigger.

- Every docstring and comment in the folder Init file
  (`auth/__init__.py`, owned by this item): graded true.
  First line descriptive, one sentence, terminal `.`, 0
  breaking; the structural opt-in paragraph verified
  (package root carries no auth import; sole production
  edge is the finalizer's already-loaded-only
  `loaded_attr` string; 0-of-69 importtime rows per all
  three file passes); the spec-040 Decision 3 pointer
  resolves (kept class); the example import block equals
  `__all__` in order; the `django.contrib.auth` cost
  claim is precise (that import sits at the top of
  `.mutations`, reached only through this file).
- Module docstrings disagreeing about who owns what (the
  folder question): none found. Declaration ledger
  (mutations docstring "cleared by `TypeRegistry.clear()`
  only" vs queries trio comment "by contrast, registers
  a full-clear-only callback" vs finalizer "not a
  pre-bind row"): agree. Emit seam (mutations "Login /
  Logout payloads ride the `mutations.inputs` row
  (imported transitively here)" — the `before_bind=True`
  row stands at import — vs queries "the alias namespace
  rides its own row"): agree. Opt-in (init vs sessions
  "neither `auth.__all__` nor the package root names it"
  vs sessions "`auth/__init__.py` eagerly imports
  `.mutations` / `.queries`" vs finalizer opt-in
  contract): agree. Surface census (init four imports,
  spec Decision 3 four factories, `_declare_auth_surface`
  "all four factories", bind "four surfaces") vs the
  landed M2 "three fixed fields" scoping: consistent —
  different censuses (declaration vs request-resolution
  labels), and the bodies route exactly that way.
- Folder-level prose other test modules hold about the
  target's symbols: F1 filed; everything else true.
  `conftest.py` module docstring (one fixture, shared by
  `test_mutations` + `test_queries` — usage verified in
  both; helpers live in `_helpers.py`): true.
  `_helpers.py` module docstring (each helper used by
  more than one module — call sites verified in two
  modules each; explicit import, not injection): true.
  The three test-module docstrings + the live-tier
  module docstring corroborate the placement split in
  both directions (each names what the other side
  owns): agree, no contradiction. The landed M6 spy
  docstring (bridge-vs-native seam across all three
  fields): true, agreed with both verifiers, not
  re-filed.
- Stale prose in another package module: none new. The
  `mutations/sets.py` two-ledger census and the
  `test_init.py` card/version narrative stay routed as
  filed (plan leads, not duplicated). The GLOSSARY
  `request_from_info` label parenthetical is docs-DB
  prose, not a package module: observed for Worker-0,
  not a finding (open thread 2).
- First lines, by kind: init + all three auth modules +
  all three support files pass `--list-docstrings`, 0
  breaking. No finding touches a first line: no TREE.md
  render owed.
- Mood: R1 judged (rejected, trigger carried).
- Public symbol without a docstring: none (four
  factories documented; trio names carry comments).
- Restated signature, voice pronouns, "Tests that" /
  "Ensures", line-number cites, dead names: none in
  folder-owned prose (provenance sweep: 2 hits, both
  kept class).
- Wrong stated reason: none (every lifecycle reason
  re-verified at its owner body).
- Unrecorded intentional separation: none filed. The
  load-bearing top-level `queries.py` -> `.mutations`
  import (finalizer `loaded_attr` requirement) is
  unrecorded in prose, but import placement is the
  folder Mechanics sibling's axis, already judged at
  the file level (queries-Mechanics Handoff 1): noted,
  not filed.

## Rejected

- R1: the plan's Routed lead —
  `tests/auth/test_mutations.py::_request_with_store`
  opens descriptively ("A Django request wired to an
  explicit session store, anonymous actor"). Rejected:
  the owning pass (`rev-auth__mutations.comments.md`)
  explicitly graded this exact candidate and rejected
  it with trigger "a maintainer decision enforcing
  mood package-wide", and that trigger is unmet. The
  first-hand census confirms the outlier status (the
  sole descriptive documented helper across
  `tests/auth/*.py`, ~40 helpers, all others imperative
  or undocumented one-liners per the schema-R3/routers
  precedent) — but no folder mood norm exists to sweep
  toward: the mutations target is descriptive by
  upheld convention while the queries/sessions targets
  are imperative, each blessed by its closed item, so
  imposing one folder mood re-litigates closed
  rejections. The lead was routed by the queries passer
  without reading the owning rejection (its Trace
  fingerprints lack the mutations comments record);
  the L1 analogy fails (L1's file is imperative
  throughout, so its helper was an outlier against its
  own file's convention — this helper's file upheld
  descriptive as its target-family convention and
  explicitly placed the helper in it). The honest
  counterweight, stated for Worker-0: the test-helper
  census is imperative-unanimous-minus-one even
  within `test_mutations.py` itself, so a future
  maintainer mood pass could revisit — which is
  exactly the owning trigger. Trigger: a maintainer
  decision enforcing mood package-wide, or the
  auth/mutations.py item reopening.

Handoff: Comments review closes findings-recorded with
one Low (F1, suite-census gaps) and one judged Routed
lead (R1, upheld rejection). The judgment calls a
verifier could revisit are R1 (uphold vs file — the
record states the counterweight plainly) and F1's Low
(true-as-far-as-it-goes per the L2 precedent, not
Medium). Beyond the record I read the `fad17c20` commit
message whole (the census-maintenance evidence), the
GLOSSARY `request_from_info` row (open thread 2), and
the `test_init.py` surface-census comment (already
routed, agreed). Open threads: (1) sibling axis records
were absent at close — the verifier confirms neither
carries a `## Cross-axis (for Comments)`; (2) GLOSSARY
`request_from_info` parenthetical
(`FilterSet`/`OrderSet`/`DjangoMutation`) omits the
`AuthMutation` + `SerializerMutation` labels though its
own sentence lists those callers — docs-DB prose for
Worker-0's `## Decisions` (glossary-DB edit + render
pattern, outside the item fence), not a finding;
(3) the load-bearing top-level `.mutations` import
direction is unrecorded in prose (folder Mechanics
awareness, already judged at file level). Scratch kept
under `docs/review/temp-tests/auth-integration/comments/`
(`inspect/` overview + stripped source, `init.json`,
`census.py`, `helpers.txt`).

## Verify comments

Pass 1, fully static (no copy bound, no workspace run — none
owed on a zero-path implement pass).

Deferral confirmation: the Implement pass took zero paths and
the deferral landed. `git diff ITEM_BASELINE --` over
`django_strawberry_framework/auth/` + `tests/auth/__init__.py`
is empty (0 bytes), ITEM_BASELINE
5676d4fc6310a5ff0d075771593a0f3068eb9406. F1's file
`tests/auth/__init__.py` hashes
09e0f06d9c93719e6e75dbcd54e8c03255c655b0 — byte-identical
to the review fingerprint. Folder fingerprints reproduce
exactly (init 2e480818, mutations 98ae63f1, queries
b036bdac, sessions e50011e6); the `auth/mutations.py` +
`auth/sessions.py` dirty-vs-HEAD hunks are the two verified
file items' own ledger rows, as the Performance review
already states. No production or test file was touched for
this item, so no `--code-digest` proof, no `--list-docstrings`
re-run, and no TREE.md render is owed; the whole-diff reading
is an empty diff, so there is nothing to attack and no new
prose to grade.

R1 judgment — UPHOLD, no revision thread. The owning
rejection exists and names this exact helper:
`rev-auth__mutations.comments.md` `## Rejected` first bullet
("Descriptive function/method first lines (target: ...;
tests: `_request_with_store`)", style preference per the
standing 9-item consensus, trigger "a maintainer decision
enforcing mood package-wide"). The trigger is unmet: the
plan's `## Decisions` holds no mood decision, and the
mutations item is verified/closed. The helper is unchanged
(descriptive opener at `test_mutations.py:1431-1432`; file
blob 4cb49982 matches the review fingerprint). The routing
provenance is corroborated: the queries comments record
cites `rev-auth__mutations` 0 times and its Trace
fingerprints list no review record, so the lead was routed
without reading the owning rejection, as R1 states. The
counterweight stands as stated (sole descriptive documented
helper, imperative-unanimous-minus-one per the saved
`helpers.txt` census) — but that is exactly the owning
trigger's domain, a future maintainer mood pass, not a
folder finding. Re-filing would re-litigate a closed
rejection without new evidence.

F1 census gaps real-but-deferred: the three Proof counts
still read 0/0/0 pre-fix (`scope-lock`, `SyncMisuseError`,
`directives` in `tests/auth/__init__.py`). The gaps are
real: `tests/auth/test_sessions.py` holds 28 `def test_`
with 0 named in the census; the (b) pins stand at
`test_mutations.py:817,842,2007`; the (c) five pins are
named in the landed queries L2 paragraph live. Severity Low
stands (placement exclusivity true; enumeration incomplete
per the accepted L2 precedent — nothing claimed is absent).
Deferred correctly per the ride rule: a Low whose file no
higher finding touches.

Sibling Cross-axis: Performance carries only `## Cross-axis`
with none, and its verify section adds no Cross-axis
content. Mechanics DOES carry `## Cross-axis (for Comments)`
(review-time, lines 309-318) — so the literal "none
appeared" does not hold — but it carries no finding and no
Proof line: it judges the plan's Routed lead out of
Mechanics scope and passes it to this Comments pass, where
R1 already judged it. The Mechanics verify section adds no
new Cross-axis content. No actionable Cross-axis content
appeared; nothing is owed to Comments. Both siblings read
whole including their concurrently-landed verify sections
(Performance + Mechanics each `Status: verified`); neither
grades Comments content.

Open threads: (1) sibling Cross-axis — closed with the
correction above (section exists, non-finding, nothing
owed); (2) GLOSSARY `request_from_info` parenthetical —
confirmed live (the anchor sentence lists the auth
`current_user` + serializer-mutation-hooks callers while
the `family_label` parenthetical names only
`FilterSet`/`OrderSet`/`DjangoMutation`): handed to Worker-0
for `## Decisions` (glossary-DB edit + render pattern,
outside the item fence), not a finding; (3) unrecorded
load-bearing `.mutations` import direction — noted, not
filed (Mechanics axis, already judged at file level):
closed.

Cells: inapplicable-by-construction stands (F1's Proof is
three static counts; no database reach); none unverified.
No new defects.

Scratch: `docs/review/temp-tests/auth-integration/verify-comments-1/`
(`fingerprints.txt`, `proof-counts.txt`, `item-diff.diff`).

Handoff: Comments verification closes with the deferral
confirmed, R1 upheld, and the F1 gaps real-but-deferred on
a byte-identical tree. Nothing here depends on further
sibling verdicts: both siblings are verified and their
Cross-axis posture is as judged above.

Status: verified. Open threads: none on this item (thread 2 handed to Worker-0 as a `## Decisions` candidate).
