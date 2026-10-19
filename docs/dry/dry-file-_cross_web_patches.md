# DRY review: `django_strawberry_framework/_cross_web_patches.py`

Status: verified
Run: 0.0.15 2026-09-21-2

## System trace

Target: `django_strawberry_framework/_cross_web_patches.py` (347 lines at HEAD,
blob `6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`; clean in the working tree;
item-baseline diff empty — see Freshness). The module is one of the package's
four one-per-dependency upstream-patch modules. It replaces the **sync**
`cross_web.DjangoHTTPRequestAdapter.body` property — upstream's bare
`self.request.body.decode()` — with a getter returning the raw request bytes,
so both of upstream's transports hand the same bytes to the same `parse_json`
and an undecodable body raises where a response can be produced instead of
inside a property (unhandled 500).

What the target owns, by role:

- Definitions in-target: the import-time upstream capture
  (`_captured_upstream_body_getter`, `_original_body_fget`), the shape
  validation (`_validate_upstream_shape`), the replacement
  (`_patched_body` + its two stamp `setattr`s), the install probe
  (`_patch_is_installed`), the gated idempotent applier (`apply`), the
  stamp constants (`_PATCH_OWNER_ATTRIBUTE`, `_PATCH_ORIGINAL_ATTRIBUTE`,
  `_PATCH_OWNER`), the `ImportError -> None` import sentinel, and the
  module docstring (bug record, upstream status + permalink, gate/audience
  narrative, retirement probes).
- Consumer edges (compose by name, not definitions): `apply()` gates on
  `conf.py::upstream_patches_enabled("cross_web")`; `apps.py::ready()` calls
  `apply()`; the docstring's gate/audience claims project rules owned by
  `conf.py` and `views.py`.
- Upstream contract oracle: `AsyncDjangoHTTPRequestAdapter.get_body`
  (installed cross_web 0.7.0) already returns raw bytes; the base
  `SyncHTTPRequestAdapter.body` is an abstract `Union[str, bytes]` with no
  default decode, so no second eager decode hides in the base.
- Oracles: `tests/test_cross_web_patches.py` (14 rows: lifecycle, raw-bytes
  return type incl. BOM/UTF-16-LE, refusals, both gate spellings);
  `tests/test_apps.py` (four-patch dispatch + double-reload capture
  retention, parametrized over all four modules); live wire rows in
  `examples/fakeshop/test_query/test_transport_api.py` (the
  `test_the_cross_web_half_turns_upstreams_own_500_into_a_400` retirement
  diagnostic, the broad-switch row, the two-mount attribution row);
  `examples/fakeshop/test_query/test_products_api.py` (package-mount 400
  rows); `tests/test_views.py` (package-adapter pins + the async-needs-none
  pin); `tests/base/test_conf.py` (gate vocabulary).
- Projections: the target docstring itself; `docs/GLOSSARY.md` ("defensive
  upstream patches", "kill switch" entries); `docs/TREE.md` module lines
  (generated); KANBAN S9 history lines; sibling-module docstrings restating
  the pair coupling (`_strawberry_patches.py`, `conf.py` comments,
  `views.py` adapter docstring).

Sites found outside the target, by mechanism sweep (HEAD `bfaee91d`,
populations printed with each sweep):

- Patch-stamp mechanism (`_PATCH_OWNER`): exactly the four patch modules —
  `_cross_web_patches.py`, `_django_patches.py`,
  `_graphql_core_patches.py`, `_strawberry_patches.py`. No fifth site.
- Install/validate/capture vocabulary (`_patch_is_installed`,
  `_validate_upstream_shape`, `_captured_upstream*`): the same four
  modules (definitions) plus test consumers (`tests/test_apps.py`,
  per-module suites, `test_transport_api.py` helpers). No other
  production site.
- `DjangoHTTPRequestAdapter` in production: the target (patch),
  `views.py` (import + `_RawBodyRequestAdapter` one-property subclass +
  prose), `tests/*` (oracles). `middleware/request_body.py` imports only
  `cross_web.HTTPException` (error type, examined and excluded).
  `utils/policies.py` cites `conf.py::upstream_patches_enabled` only as a
  mapping-validation precedent in comments (examined and excluded).
- `request.body` raw reads in production: the target's `_patched_body`,
  `views.py::_RawBodyRequestAdapter.body`, and upstream's async
  `get_body`. The `middleware/debug_toolbar.py` `json.loads(request.body)`
  is panel display parsing, unrelated. The two in-package raw-bytes
  getters are the R1 intentional-separation pair, already recorded at
  both owners.
- Upstream read sites: installed strawberry 0.324.0
  `sync_base_view.py::parse_http_body` reads `request.body` at exactly
  one site (`data = self.parse_json(request.body)`, `request` being the
  `SyncHTTPRequestAdapter`); `async_base_view.py` reads
  `await request.get_body()` (two call sites, one method). The
  "exactly one site" claim the views docstring makes holds at the
  installed version.

Prior cycle records checked as triggers only: `docs/dry/dry-file-__init__.md`
mentions the target once (submodule-fallback imports resolve outside
`__all__` — consistent with the target's private-surface prose, no trigger);
`docs/dry/dry-file-_boundary_ordering.md` has no patch-family trigger. Fresh
trace below; nothing imported.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED, hit. The four patch modules
   are the mirror: each spells the full safe-replacement lifecycle
   (import sentinel, stamp, capture, validation, install probe, gated
   applier) in local vocabulary. Yields F1 (mechanism) + F2 (wording).
   Non-patch flavors (`rest_framework`, `forms`, `filters`, `orders`)
   share no rule with this target.
2. Sync/async twins — SEARCHED, no twin defined here. The target defines
   one sync getter; its async counterpart is upstream-owned
   (`AsyncDjangoHTTPRequestAdapter.get_body`), an oracle of the raw-bytes
   contract, not a second definition. The async transport needs no patch
   (pinned by
   `tests/test_views.py::test_the_async_view_needs_no_adapter_override_because_upstream_hands_bytes`).
   No behavior pair in-target can drift.
3. Derived rather than repeated knowledge — SEARCHED, hit inside F1. The
   install-state question is answered once (`_patch_is_installed`,
   identity compare); the capture-vs-live split (validate pins the
   import-time capture, the probe reads the live descriptor) is
   deliberate and pinned by
   `test_apply_fails_loudly_when_original_getter_was_never_captured`.
   The `inspect.signature` arity-pin idiom is shared with all three
   siblings (F1 sub-rule). The per-module test
   `test_patch_is_installed_on_adapter` re-derives installed-state by
   direct identity compare as an independent oracle (oracles never read
   from the owner they check) — listed, not counted.
4. Inverse / round-trip pairs — SEARCHED, ruled inapplicable with reason.
   The lifecycle is install-once process-global; revert exists only as
   test scaffolding (restore saved descriptors by identity), not a
   product round-trip, and no contract requires an uninstall half. The
   capture-read/install-write kind agreement (fget ↔ `property(...)`)
   is recorded inside F1 as a kind-parameterized pair.
5. Contracts restated in another medium — SEARCHED, classified. Gate
   semantics: owned by `conf.py::upstream_patches_enabled`, projected
   by this docstring, composed by name in `apply()` (no restatement in
   code). Mount/audience split: owned by `views.py`, projected here.
   Retirement procedure: this docstring is the sole definition (L1);
   the live diagnostic row it names is an independent oracle.
   GLOSSARY/TREE.md/KANBAN lines are projections/history. Test `match=`
   substrings pin F2 message fragments as oracles (listed, not counted).
6. Enforcement by omission — SEARCHED, no gap. Population: every member
   of installed `cross_web/request/_django.py` (sync: query_params,
   path_params, body, method, headers, post_data, files, get_form_data,
   content_type, url, cookies; async: get_body, get_form_data, + shared
   properties). Only sync `body` decodes (verified in installed source);
   the rest perform no decode. Async `get_body` is correct by
   construction (probe P4 + permanent async pin). Non-Django adapters
   (flask/starlette/...) are outside the package's serving surface (the
   package mounts Django adapters only). The two in-package body
   sources (patched class, package subclass) are both raw-bytes by
   distinct ownership (R1). No member lacks a guard its contract
   requires.

### Enumeration

Instrument: every statement in `ast.Module.body` of the target at HEAD
(16 nodes; verified by executing `ast.parse` over the file — see
Challenges preamble for the command). Rule-bearing members (13) each land
below in a family (F1/F2), the rejection (R1), or a file-local row
(L1/L2); the 3 plain imports carry no rule.

| # | `ast` node | Name / content | Home |
|---|---|---|---|
| 1 | Expr (docstring) | bug record, gate/audience narrative, retirement probes | L1 (+ projections noted) |
| 2 | Import | `inspect` | — (no rule) |
| 3 | ImportFrom | `typing.Any` | — (no rule) |
| 4 | ImportFrom | `.conf::upstream_patches_enabled` | — (consumer edge; rule owned by File `conf.py`) |
| 5 | Try | `from cross_web import DjangoHTTPRequestAdapter` / `except ImportError -> None` | F1 (import sentinel) |
| 6 | Assign | `_PATCH_OWNER_ATTRIBUTE` literal | F1 (stamp identity) |
| 7 | Assign | `_PATCH_ORIGINAL_ATTRIBUTE` literal | F1 (stamp identity) |
| 8 | Assign | `_PATCH_OWNER` per-module value | F1 (stamp identity) |
| 9 | FunctionDef | `_captured_upstream_body_getter` | F1 (recovery) + L2 (property-kind check) |
| 10 | Assign | `_original_body_fget` import-time capture | F1 (capture + None sentinel) |
| 11 | FunctionDef | `_validate_upstream_shape` | F1 (validation step) + F2 (3 messages) |
| 12 | FunctionDef | `_patched_body` | R1 (rejection vs package adapter) |
| 13 | Expr | `setattr` owner stamp | F1 (marking) |
| 14 | Expr | `setattr` original stamp | F1 (marking) |
| 15 | FunctionDef | `_patch_is_installed` | F1 (install check) + L2 (fget-read kind) |
| 16 | FunctionDef | `apply` | F1 (4-step order) + gate consumer edge |

Count check: 16 nodes enumerated, 13 rule-bearing nodes assigned (3 of
them split across two rows by aspect: 9, 11, 15), 3 imports correctly
rule-free. Nothing unassigned.

### Challenges

Enumeration command (replayable):
`python3 -c "import ast; m=ast.parse(open('django_strawberry_framework/_cross_web_patches.py').read()); print(len(m.body))"`
prints `16` (node-kind listing in the scratch note below; target clean at
HEAD so the working-tree parse equals HEAD).

Change challenges per rule (consumers/oracles/projections listed, never
counted):

- LC-C1 (stamp rename): rename the `_PATCH_OWNER_ATTRIBUTE` value
  (`"_django_strawberry_framework_patch_owner"`). Forced moves: the
  literal + capture read + marking write in each of the 4 patch
  modules. Count: **4 authoritative definitions**. Consumers: none
  outside the four (mechanism sweep). Oracles: `tests/test_apps.py`
  reload test (behavioral, survives a rename).
- LC-C2 (apply order): check installed-before-validate (skip validation
  when already installed). Forced moves: the 4 `apply()` bodies (all
  four spell gate → validate → installed-check → install today).
  Count: **4**.
- LC-C3 (fifth dependency): a new upstream needs a patch module.
  Forced moves: a full 5th spelling (~40 lines: sentinel, capture,
  stamp, validate, probe, applier) — no driver to extend, only prose
  precedent. Count: **new 5th definition** (proves principle-1 pressure;
  the family item decides driver vs deliberate independence).
- LC-C4 (sentinel convention): replace the `None` missing-shape sentinel
  with a dedicated marker. Forced moves: the `None` reads in all 4
  modules' captures, probes, and validators. Count: **4**.
- W-C1 (hint reword): reword the shared `Disable this patch with
  APPLY_UPSTREAM_PATCHES = {"<dep>": False} ... or use a supported ...`
  grammar. Forced moves: 11 raise sites (cross_web 3, django 3,
  strawberry 3, graphql_core 2). Count: **11 sites / 4 module wordings**.
  Oracles pinning fragments (`match=` in per-module suites): listed.
- R-C1 (package drops its strict contract): only `views.py` moves (the
  patch still serves Strawberry's own view). Count: **1**.
- R-C2 (gate removed / patch retired upstream): only the patch side
  moves (the package adapter stays as package policy; whether the
  retirement change also removes the then-redundant shadow is that
  change's choice, not forced). Count: **1**.
- L-C1 (retirement-procedure prose change, e.g. upstream 0.8.0 fixes
  the decode): only this docstring moves (GLOSSARY follows as
  projection). Count: **1**.
- L-C2 (upstream reshapes `body` to a plain method): only this
  module's property-kind checks move (siblings patch classmethod /
  plain methods — disjoint kinds). Count: **1**.

Experiments: one read-only probe, `execution-verified` (7/7 PASS),
command + what it proved under F1/R1 Behavioral proof; replay in
`docs/dry/temp-tests/dry-file-_cross_web_patches-r2-w1/probe_upstream_shape.py`.

## Findings

### F1 — Upstream-patch safe-replacement lifecycle (new family `upstream-patch-lifecycle`)

- Contract + variation: how a patch module safely replaces one upstream
  member process-wide: stay importable without the upstream (None
  sentinel); capture the genuine member at import; stamp the
  replacement with owner + original so a reloaded module recovers the
  genuine capture instead of mistaking its own prior replacement for
  drift; validate presence + call shape (and, for reimplementers, body
  source) before installing; install idempotently and self-heal a
  third-party revert; gate everything on the per-dependency switch.
  Legitimate variation: dependency key, upstream symbol(s), descriptor
  kind (property / classmethod / plain method), delegator vs
  reimplementer depth. The kind parameterizes the read/write spelling;
  the state machine does not vary.
- Sites + roles (definitions): `django_strawberry_framework/_cross_web_patches.py`
  (property kind: sentinel, stamp, `_captured_upstream_body_getter`,
  `_original_body_fget`, `_validate_upstream_shape` presence+arity,
  2-line marking, fget-identity probe, 4-step `apply`);
  `django_strawberry_framework/_django_patches.py` (classmethod kind +
  2-body audited set + teardown-time read discriminator);
  `django_strawberry_framework/_strawberry_patches.py` (4 plain-method
  captures, delegating wrapper + reimplemented shield + multipart
  twins, `_mark_patch_replacement` helper + 4 calls, 4-member
  conjunction probe); `django_strawberry_framework/_graphql_core_patches.py`
  (1 plain-method capture, delegating wrapper, single-identity probe).
  Consumers: `apps.py::ready` (4 `apply()` calls, in listed order);
  `tests/test_apps.py::_PATCHED_SLOTS` + `_all_patches_installed`;
  `test_transport_api.py` opt-out helpers (restore-by-identity +
  probe asserts). Oracles: per-module suites, the `test_apps.py`
  dispatch + double-reload rows, the live transport/attribution rows.
  Projections: the four module docstrings' lifecycle prose,
  `conf.py::UPSTREAM_PATCH_DEPENDENCIES` comment, GLOSSARY
  "defensive upstream patches" entry.
- Challenges: LC-C1 count 4; LC-C2 count 4; LC-C3 new 5th definition;
  LC-C4 count 4 (see ### Challenges).
- Owner + lifetime: TBD by the family item. Candidates: a shared
  small owner the four modules import (narrowest cohesive owner every
  applier can depend on without reversing a dependency), vs keeping
  the spelling per-module as deliberate deletion-independence (each
  module today must stay importable and deletable without reaching
  into siblings — the `_strawberry_patches.py` `_UPSTREAM_JSON_PARSE_REASON`
  comment states that stance for its own twin literal). Lifetime:
  process-global from `AppConfig.ready()`; reload-safe by stamp
  recovery (principle 4: owner = each patch module today; validity key
  = stamp identity; publish point = `apply()`; mutation = install /
  third-party revert + self-heal; invalidation = none — install-once).
- Migration (for the family item to decide, not designed here): either
  extract the kind-independent machine (sentinel/capture/stamp/probe/
  order) behind one driver with kind adapters (property/classmethod/
  plain), leaving per-module symbols + pins + replacements as
  declarations; or record deliberate per-module ownership with the
  deletion-independence reason at each owner. The `_mark_patch_replacement`
  helper shows the in-module factoring precedent.
- Distinct behavior (stays separate whatever the family decides):
  descriptor-kind read/write spellings (property fget vs `__func__`
  unwrap vs plain attr); delegator (shape-only pin: cross_web,
  graphql_core) vs reimplementer (body-source pin: django's 2-source
  set, strawberry's shield source); strawberry's 4-member install
  conjunction (guard must never run without its shield); django's
  validated-source teardown discriminator. In-family divergences the
  item must resolve: graphql_core's capture accepts any
  `django_strawberry_framework.*` owner prefix where the other three
  require exact `_PATCH_OWNER` equality (unreachable today — disjoint
  members — but a different contract); graphql_core's capture carries
  no docstring where its strawberry twin does.
- Behavioral proof: definition counts are `static-reviewed` (mechanism
  sweeps with populations). The lifecycle's live behavior is pinned by
  permanent oracles (dispatch, double-reload, idempotence, self-heal
  rows) — no new behavior claimed here. Probe P1a/P1b/P5
  `execution-verified`: the capture in this tree IS genuine upstream
  (identity with the live class dict in a bare process), uninstalled
  there as expected, arity `(self)` as pinned. Command:
  `uv run python docs/dry/temp-tests/dry-file-_cross_web_patches-r2-w1/probe_upstream_shape.py`
  (7/7 PASS; inputs HEAD-clean — target, `conf.py`, `exceptions.py`
  verified clean, cross_web 0.7.0 installed).
- Structural gate + negative control: owed by the family item (e.g. a
  population-enumerated check over the four modules' lifecycle members,
  or an existence-and-shape test if a driver is extracted). Negative
  control shape: a hand copy of the lifecycle with one step reordered
  or one stamp renamed must fail the gate while every behavioral
  oracle stays green. No gate proposed here beyond naming the
  requirement.
- Coupling: F2 (wording lives inside the same `apply()`/`validate`
  bodies; a lifecycle reshape touches the lines the wording owns —
  land together or sequence explicitly). The sibling File items
  (`_django_patches.py`, `_strawberry_patches.py`,
  `_graphql_core_patches.py`, `conf.py`, `apps.py`) trace the same
  sites from their side; Worker 0 dedups identical namings.
- Freshness: target `6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`;
  `_django_patches.py` `ba98f5859ec32971c3aa566c221bdc4db392e137`;
  `_strawberry_patches.py` `f77df3499eb96051d70055266a677ca3cde5b219`;
  `_graphql_core_patches.py` `1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`;
  `conf.py` `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`;
  `apps.py` `8ae1a3a3b12f0c9792094959c573ea6fab5d804f`;
  `tests/test_cross_web_patches.py` `70c16389aa5d2a14746dba1612c909263bffd822`;
  `tests/test_apps.py` `5ca8b62c53185343ebfec95315f59ec6104fc851`;
  `tests/test_strawberry_patches.py` `f4a0a8ff935fcece1e4fea4083965fe8b285d7cd`;
  `tests/base/test_conf.py` `f35c70742354d0ab123b163a92c6a8a503c6ea29`;
  `test_transport_api.py` `17320f1ff335a868d5ed324a49f1d7c4ee899cfc`;
  `docs/GLOSSARY.md` `bc51debc54cf3ed142b45fa9feda1b99bce60c79`;
  upstream `cross_web/request/_django.py` blob `fa2a5bef5a6b0a63143247305718a94c33542aa0`
  (cross-web 0.7.0, `git hash-object` of the installed file).
  Searched populations: `_PATCH_OWNER` → 4 production files;
  `_patch_is_installed|_validate_upstream_shape|_captured_upstream`
  → 4 production + 5 test files; `upstream_patches_enabled` →
  4 production call sites + `conf.py` owner. Excluded on body
  strength: `middleware/request_body.py`
  (`e6e32e785ec84360c63c9ff529a58f8d63bc8898`, imports only
  `HTTPException`); `utils/policies.py`
  (`860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e`, cites the gate only
  as a mapping-validation precedent).

### F2 — Upstream-patch refusal wording (new family `upstream-patch-refusal-wording`)

- Contract + variation: the `RuntimeError` grammar every patch
  `apply()` raises on unsupported upstream shape: `Cannot apply
  django-strawberry-framework's <patch> patch: <expected-shape> ...
  Disable this patch with APPLY_UPSTREAM_PATCHES = {"<dep>": False}
  or use a supported <version-noun>.` Legitimate variation: patch
  name, expected-shape clause, dependency key, version noun. The
  opt-out hint spelling and the disable-vs-upgrade two-exit framing
  do not vary.
- Sites + roles (definitions): 11 raise sites — target 3
  (symbol-missing, capture-missing, signature);
  `_django_patches.py::_validate_upstream_shape` 3
  (symbol/descriptor, signature, body-pin);
  `_strawberry_patches.py::_validate_upstream_shape` 3 (presence,
  per-method signature loop, body-pin);
  `_graphql_core_patches.py::_validate_upstream_shape` 2 (presence,
  signature). Divergences: version nouns (`cross_web version` /
  `Django version` / `Strawberry version` + `supported dependency
  versions` / `graphql-core version`); strawberry's presence clause
  enumerates 6 symbols. Oracles (listed): per-module `match=`
  fragments (`DjangoHTTPRequestAdapter`, `expected (self) getter
  signature`, `no longer a readable property`, django/strawberry/
  graphql counterparts). Projections: module-docstring opt-out
  spellings, `conf.py` gate docstring, GLOSSARY "kill switch" entry.
- Challenges: W-C1 count 11 sites / 4 module wordings.
- Owner + lifetime: TBD by the family item (natural candidate: the
  F1 owner, if one is extracted, else `conf.py` beside the gate it
  phrases — the hint phrases `upstream_patches_enabled`'s own
  contract). Lifetime: import/process-global, same as F1.
- Migration (family item's decision): one message builder
  (patch-name, shape clause, dep key, version noun as parameters)
  vs recorded deliberate per-module wording. Either way the
  `match=` oracles move as oracles, never rewritten to read from
  the builder.
- Distinct behavior: the per-site expected-shape clauses stay
  per-module (they name disjoint upstream members); only the
  shared opt-out/two-exit framing is the family's.
- Behavioral proof: `static-reviewed` (literal sweeps; wording has
  no runtime behavior beyond the raised text, which the `match=`
  oracles pin). No execution claimed or needed.
- Structural gate + negative control: owed by the family item
  (e.g. pin the hint spelling against `UPSTREAM_PATCH_DEPENDENCIES`
  keys + the gate's accepted shapes; negative control: a message
  with a renamed key passes behavior oracles but fails the gate).
- Coupling: F1 (same bodies; sequence together). Sibling File
  items as in F1.
- Freshness: same production fingerprints as F1; oracles
  `tests/test_cross_web_patches.py`, `tests/base/test_conf.py` as
  above.

### R1 — Raw-bytes sync body getter vs the package view's own adapter (rejected)

- Contract + variation: two spellings of `return self.request.body`
  that look like one rule and are two. `Target::_patched_body`
  replaces the property on upstream's class process-wide so a
  consumer mounting **Strawberry's own** view gets a controlled 400;
  it is a workaround for someone else's bug, gated by
  `APPLY_UPSTREAM_PATCHES`, retirable when upstream stops decoding
  eagerly. `views.py::_RawBodyRequestAdapter.body` shadows the same
  property by subclass for **package** mounts only; it is permanent
  package policy (the body-source half of the spec-046 Decision 9
  wire contract), ungated, unretirable with upstream. Concrete
  contract difference: with the whole kill switch thrown, the two
  mounts answer the same undecodable body differently (upstream
  mount 500, package mount 400) — one spelling cannot produce both
  answers. Reconsideration trigger: if the patch lost its
  gate/retirement lifecycle (became permanent policy) or the
  package view delegated its body source to the patched class,
  the two would be one rule; consolidate then.
- Sites + roles: two independent definitions (rejected pair).
  Target `_patched_body` (+ its docstring's mount/lifecycle
  rationale); `views.py::_RawBodyRequestAdapter` (+ its "Why this
  is not the `cross_web` patch again" clause — the durable home of
  this rejection, already at the owner, mirrored by the target
  docstring's "not redundant ... it is what made the claim true").
  Oracle of the split: live attribution row
  `test_only_the_package_mount_answers_the_same_way_in_both_patch_states`
  (upstream mount moves 500↔200, package mount constant 400) plus
  `test_the_sync_view_hands_parse_json_raw_bytes_in_every_patch_state`
  (package adapter yields bytes while upstream's raises, same
  request).
- Challenges: R-C1 count 1 (views only); R-C2 count 1 (patch side
  only). A shared-form consolidation (one getter both mounts use)
  would own 2 lines and destroy the gate/audience split both
  docstrings exist to protect.
- Owner + lifetime: unchanged — each site keeps its owner (patch
  module: process-global while installed, retirable; view adapter:
  per-view class attribute, permanent).
- Migration: none (rejection).
- Distinct behavior: preserved exactly — the mounts' differing
  answers under the kill switch ARE the observable distinction.
- Behavioral proof: `static-reviewed` — rests on reading the two
  permanent live/in-process oracles above (not run in this item;
  the working tree is dirty under `test_transport_api.py`, so a
  shared-tree run would not measure HEAD; the oracles run at the
  cycle gate). Probe P2/P2b/P3 `execution-verified`: upstream
  still raises where the patch must route around (STILL NEEDED),
  and the replacement returns the bytes untouched (direct call,
  no install). Same replay command as F1.
- Structural gate + negative control: none owed (rejection, no
  owner to bypass). The existing attribution oracles already fail
  if either side is silently removed.
- Coupling: none.
- Freshness: target `6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`;
  `views.py` `9f85b0df26a17e800ec392aa13f6848e07633895`;
  `test_transport_api.py` `17320f1ff335a868d5ed324a49f1d7c4ee899cfc`;
  `tests/test_views.py` `4dc9a25723501cd1f84161423a1aefbf00ff7eb9`;
  `test_products_api.py` `b863b29c5ab77153cc73db9827f2dfa447e5b88f`;
  upstream blobs as in F1; installed strawberry 0.324.0
  single-body-read-site verified (`sync_base_view.py:171`
  `self.parse_json(request.body)`; async via
  `await request.get_body()`).

### L1 — cross_web retirement/audience prose (file-local)

- Contract + variation: the module docstring's cross_web-specific
  record — bug mechanics (gaps 1+2), upstream status
  (cross-web 0.7.0 unfixed, permalink, no tracking issue), the
  gate/audience narrative, and the two retirement checks (live-row
  procedure with its two verdict-inverting misreadings pinned; the
  `_original_body_fget` quick probe). Varies only with this
  upstream's history.
- Sites + roles: sole definition — the target docstring. The live
  diagnostic row it names is an oracle; the GLOSSARY/TREE.md lines
  are projections.
- Challenges: L-C1 count 1 (only this docstring moves; GLOSSARY
  follows as projection, never counted).
- Owner + lifetime: the target module; dies with the module at
  retirement.
- Migration / Distinct behavior / Coupling: none (file-local prose).
- Behavioral proof: the quick-probe snippet is substantively what
  probe P2 executes — `execution-verified` (STILL NEEDED on the
  installed 0.7.0). The live-row procedure is `static-reviewed`
  (oracle exists at HEAD, runs at the gate).
- Structural gate + negative control: none owed (unique prose; no
  bypass population).
- Freshness: target blob as above; `test_transport_api.py` as above.

### L2 — Property-descriptor-kind capture/install handling (file-local)

- Contract + variation: the descriptor-kind parameter of F1 as
  spelled for a `property` target: `isinstance(descriptor,
  property)` + `fget is None` guard in the capture, fget-identity
  read in the probe, `property(_patched_body)` install. Varies
  only with this upstream member's descriptor kind.
- Sites + roles: sole definition — the kind-specific lines of
  target nodes 9/15/16. Siblings patch disjoint kinds
  (django: classmethod `__func__` unwrap; strawberry/graphql_core:
  plain attribute identity) — parameters of F1, not second
  property sites. Oracle: `test_capture_returns_none_for_missing_adapter_or_body_property`
  (non-property `body` → None sentinel).
- Challenges: L-C2 count 1 (a kind reshape moves only this
  module). Descriptor-kind sweep: property ×1 (here), classmethod
  ×1, plain ×2 — no second property site anywhere in the package.
- Owner + lifetime: the target module (kind adapter of the F1
  machine, wherever F1 lands — the family item may relocate this
  spelling as F1's property adapter; until then it lives here).
- Migration / Distinct behavior: none pending; if F1 extracts a
  driver, this row becomes that driver's property adapter.
- Behavioral proof: `static-reviewed` (kind sweep + the oracle
  above). Probe P1a/P5 `execution-verified` the live kind facts
  (capture is the property's fget; arity `(self)`).
- Structural gate + negative control: none owed (single site).
- Coupling: F1 (kind adapter of that machine).
- Freshness: target + three sibling fingerprints as in F1.

## Defects

None found. Near-misses examined and ruled out (each checked against
its permanent oracle, not assumed):

- graphql_core's prefix-match capture vs the other three modules'
  exact-match: an in-family contract divergence, recorded under F1
  for the family item — not a defect (members are disjoint so no
  behavior differs; no contract source requires exactness).
- graphql_core's capture lacking the docstring its strawberry twin
  carries, and the `pragma: no cover` comment wording divergence
  ("monkeypatch" vs "patched imports"): prose gaps, not behavior.
- Time-sensitive docstring claims (cross-web 0.7.0 "latest", checked
  dates): retirement is diagnosed by the standing live row, never by
  the date; the installed version still matches (0.7.0).
- Reload hazards (stale capture, pre/post-reload identity operands),
  None-sentinel mishandling, live-vs-capture confusion in
  validate-vs-probe, gate bypass: each traced to a passing permanent
  oracle (double-reload row, missing-capture refusal row, both gate
  spellings, self-heal row). No guard any contract requires is
  missing (axis 6: full member enumeration, no gap).

## Pending execution

None. No `proof:` entry is owed: every conclusion resting on a probe
is `execution-verified` above (replay command recorded), and every
other conclusion rests on permanent oracles that the cycle gate runs.
`FAKESHOP_SHARDED=1` and Postgres cells are inapplicable by
construction: the target performs no database access and makes no
alias, routing, or dialect decision (pure monkeypatch lifecycle plus
a bytes handoff) — stated here for Worker 2's judgment.

## Index rows for Worker 0

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `upstream-patch-lifecycle` | TBD by family item | `django_strawberry_framework/_cross_web_patches.py`, `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/_graphql_core_patches.py` | Family `upstream-patch-lifecycle` | open |
| `upstream-patch-refusal-wording` | TBD by family item | `django_strawberry_framework/_cross_web_patches.py`, `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/_graphql_core_patches.py` | Family `upstream-patch-refusal-wording` | open |
| Raw-bytes sync body getter vs the package view's own adapter | `views.py::_RawBodyRequestAdapter` (rejection already recorded at both owners' docstrings) | `django_strawberry_framework/_cross_web_patches.py`, `django_strawberry_framework/views.py` | File `_cross_web_patches.py` | rejected |
| cross_web retirement/audience prose | `django_strawberry_framework/_cross_web_patches.py` (module docstring) | `django_strawberry_framework/_cross_web_patches.py` | File `_cross_web_patches.py` | file-local |
| Property-descriptor-kind capture/install handling | `django_strawberry_framework/_cross_web_patches.py` | `django_strawberry_framework/_cross_web_patches.py` | File `_cross_web_patches.py` | file-local |

## Judgment

Zero-edit result, proved: the target is a single-responsibility patch
module whose every rule-bearing member is assigned — two new families
named for Worker 0 (`upstream-patch-lifecycle`, 4 definitions across
the four patch modules; `upstream-patch-refusal-wording`, 11 raise
sites / 4 module wordings), one intentional-separation rejection with
its trigger (the raw-bytes getter vs the package adapter, already
recorded at both owners), two file-local rows with their challenges.
No production edit owed, none made; no defects; no pending execution.
The upstream defect is still present at the installed cross-web 0.7.0
(probe STILL NEEDED), so retirement is not in question this cycle.
## Independent verification (Worker 2) — expectations (Phase A)

Item: File `django_strawberry_framework/_cross_web_patches.py`, release 0.0.15, run 2.
Worker-1 diagnosis withheld; everything below is derived independently.
HEAD at start: `bfaee91dcd332a5f86250fff90ab21b377bc674e` (end value under
`### Pre-finish gate`). Target clean at HEAD blob
`6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf` (worktree hash identical; zero diff).
ITEM_BASELINE=`60aa7f887e38781c13cc507628a74a912226d117` (per dispatch; the
item touches only the artifact, which Phase A must not modify or read, and the
target, which is clean).

Method. All censused files read at HEAD bytes (`git show HEAD:<path>`):
the target, `apps.py`, `conf.py`, the three sibling patch modules,
`views.py` (wire-contract halves), `tests/test_cross_web_patches.py`,
`tests/test_apps.py`, `tests/test_views.py`, `tests/base/test_conf.py`,
`tests/test_graphql_core_patches.py`, and the dirty-at-worktree
`examples/fakeshop/test_query/test_transport_api.py`,
`examples/fakeshop/test_query/test_products_api.py`,
`tests/test_strawberry_patches.py` (concurrent dirt in the latter two is a
`{not json` live-tier move plus one import; none of it touches this item's
rows — verified by diff). Installed upstream read live from `.venv`
(cross-web 0.7.0, strawberry-graphql 0.324.0, Django 6.1). Four read-only
probes in `docs/dry/temp-tests/dry-file-_cross_web_patches-r2-w2/`
(`p1_enumerate.py`, `p2_upstream.py`, `p3_lifecycle.py`, `p4_two_routes.py`);
no pytest run, no source mutated, no FAKE_SHARDED/Postgres (nothing under
test reaches a database, alias, or dialect decision).

### Enumeration

Instrument: `ast.parse` over HEAD bytes; members = `ast.Module.body`
statements; names = module-scope bound identifiers (P1).
Count: 16 statements, 13 bound names. Members (statement index, line, kind):

- 0:1 Expr = module docstring (197 lines: organizing rule, gate, joint
  ownership, bug statement, retirement probes, upstream status, visibility).
- 1:199 `import inspect`; 2:200 `from typing import Any`;
  3:202 `from .conf import upstream_patches_enabled` (consumer import of the
  gate; the gate itself is owned by File `conf.py`, undispatched).
- 4:204 Try = import-resilient symbol capture (`DjangoHTTPRequestAdapter`
  or `None` + the "preserve module import" comment).
- 5:212 `_PATCH_OWNER_ATTRIBUTE`, 6:213 `_PATCH_ORIGINAL_ATTRIBUTE`,
  7:214 `_PATCH_OWNER` (stamp vocabulary declarations).
- 8:217 `_captured_upstream_body_getter` (reload-tolerant capture).
- 9:241 `_original_body_fget` (import-time capture; the `None` sentinel on
  missing shape; read by retirement probes and every test restore site).
- 10:244 `_validate_upstream_shape` (loud validation; 3 `RuntimeError`s).
- 11:279 `_patched_body` (the async-contract replacement).
- 12:320 + 13:321 Expr = the two owner/original stamps.
- 14:324 `_patch_is_installed` (identity probe).
- 15:332 `apply` (gated idempotent self-healing installer; the one
  public name, per the Surface-visibility rule).

### Contracts checked (fresh verdicts)

Every source-stated claim under test, each with its evidence:

- C1 "One patch module per third-party dependency." HOLDS. Contract
  source: spec-024 Decision 1 + rationale (one module per dependency, each
  with its own `apply()`, settings keyed per dependency). Corroborated by
  `apps.py::ready` docstring (four modules named), `conf.py` comment on
  `UPSTREAM_PATCH_DEPENDENCIES`, and the four `_*_patches.py` modules.
- C2 "Applied once from `apps.DjangoStrawberryFrameworkConfig.ready`,
  consumers get it via INSTALLED_APPS." HOLDS. `apps.py::ready` imports
  and calls all four `apply()`s (function-local imports); P3 step 1
  proves install via `django.setup()` with minimal settings; oracle
  `tests/test_apps.py::test_ready_dispatches_all_four_patch_appliers_and_refires_safely`
  reverts all four to captured originals and re-drives `ready()`.
- C3 "Gated by `APPLY_UPSTREAM_PATCHES`, default on; global-False and
  per-dependency-mapping opt-outs." HOLDS. Gate owner
  `conf.py::upstream_patches_enabled` (default True; bool or
  Mapping[str, bool]; whole-mapping validated; unknown names/keys/values
  raise `ConfigurationError`; unknown dependency raises `ValueError`).
  Target consults it once (`apply`, `"cross_web"` key). Oracles:
  `tests/base/test_conf.py` (14 gate rows incl. per-dependency matrix),
  `tests/test_cross_web_patches.py::test_apply_no_ops_when_toggle_disabled`
  and `::test_apply_no_ops_when_cross_web_dependency_opted_out`
  (the latter also pins `{"django": False}` leaves this half installing).
  P3 steps 4a–4c re-prove decline + self-heal + idempotence in-process.
- C4 "This patch + `_strawberry_patches` jointly own the malformed-body
  hardening on Strawberry's own sync view; disabling either leaves it
  incomplete." HOLDS, decomposed by P4 at installed versions: body 1
  (invalid UTF-8 inside JSON) needs BOTH halves — unpatched `parse_json`
  lets `UnicodeDecodeError` escape, patched translates it to 400; body 2
  (raw binary) needs ONLY this half — it decodes under `surrogatepass`
  and unpatched `parse_json` already 400s via upstream's own
  `except json.JSONDecodeError`. So "disabling either leaves it
  incomplete" is exact: without this half both bodies are the
  property-scope 500; without the Strawberry half body 1 is a 500.
  Live oracle: `test_transport_api.py::test_the_cross_web_half_turns_upstreams_own_500_into_a_400`
  (HEAD), whose docstring records the same decomposition
  ("raw-binary still 400, invalid-UTF-8 500" with the Strawberry half
  alone restored).
- C5 "The gate covers upstream defects only; a package view does not
  consult it." HOLDS structurally: production call sites of
  `upstream_patches_enabled` are exactly the four `apply()` gates
  (`git grep` at HEAD: cross_web:342, django:414, graphql_core:122,
  strawberry:842; `views.py` never calls it; `utils/policies.py`
  mentions are comment-only precedent citations). Package-view
  independence is pinned over the wire by the broad-switch row
  `test_the_sync_wire_contract_holds_with_every_upstream_patch_opted_out`
  and the attribution row
  `test_only_the_package_mount_answers_the_same_way_in_both_patch_states`
  (HEAD).
- C6 "Strict UTF-8 wire contract per spec-046 Decision 9: decode in
  `views.py::_RequestBodyBoundaryMixin.parse_json`, sync body source in
  `views.py::_RawBodyRequestAdapter`." HOLDS. Spec-046 Decision 9 (+10
  for the BOM) exists as cited; `views.py::parse_json` strict-decodes
  bytes then delegates via `super()`; `_RawBodyRequestAdapter` is the
  one-property subclass on `DjangoGraphQLView.request_adapter_class`;
  oracle `tests/test_views.py::test_the_sync_view_hands_parse_json_raw_bytes_in_every_patch_state`
  reinstalls the eagerly-decoding getter and shows the package adapter
  still yields bytes while upstream's raises.
- C7 "The bug: sync `body` bare-decodes; async `get_body` hands raw
  bytes; the asymmetry is the defect; the patch installs the async
  contract." HOLDS at installed cross-web 0.7.0 (P2): sync fget source
  is `return cast(Union[str, bytes], self.request.body.decode())` with
  no `try`; it raises `UnicodeDecodeError` on non-UTF-8 (STILL NEEDED)
  and returns `str` for BOM-less UTF-16-LE (gap-2 premise); async
  `get_body` returns `self.request.body` untouched; the sync protocol
  itself permits bytes (`Union[str, bytes]`, "Return the raw request
  body as bytes or string"), so the patch's contract is inside the
  declared protocol. Request-path liveness at installed
  strawberry-graphql 0.324.0 (P2): sync reads
  `self.parse_json(request.body)` (`sync_base_view.py`), async reads
  `self.parse_json(await request.get_body())` (`async_base_view.py`),
  Django views set `request_adapter_class` to the sync/async adapters
  respectively, and the async adapter defines no `body` member (the
  patched member is unreachable from async).
- C8 "Upstream status: unfixed as of cross-web 0.7.0 (checked
  2026-06-18); retirement probes." HOLDS at the installed version:
  P2/P3 both report STILL NEEDED. The "latest release" half of the
  dated claim was not re-checked (needs network); it does not need to
  be — the live retirement signal is probe 1 (the cross_web_half row's
  un-installed state answering 400) and probe 2 (captured getter no
  longer raising), both executable today. Probe 2's snippet is accurate
  (P3 step 3 executes its essence).
- C9 "Upstream's getter is still captured at import time so retirement
  probes and shape validation can see the bare `.decode()`, but the
  installed property does not call it." HOLDS under the capability
  reading, which is the coherent one: capture makes the GENUINE getter
  (as opposed to a previous package replacement) available to probes
  and validation; the installed property never calls it (P3 + body
  read). The sentence does not claim validation asserts a `.decode()`
  in the body — validation pins presence + `(self)` signature, and a
  same-shape semantic upstream fix is detected by retirement probe 1,
  which the docstring explicitly designates for exactly that case ("a
  400 in the un-installed state is what says upstream stopped decoding
  eagerly"). No gap, no defect (near-miss recorded, resolved).
- C10 "Surface visibility: module private; `apply` exported for
  regression tests." HOLDS: every test restore/call site uses
  `apply()` / `_patch_is_installed()` / `_original_body_fget` directly
  without going through the AppConfig (8 restore sites + dispatch +
  reload tests); root `__init__.py` and both conftests reference no
  patch symbol (verified by grep — no hidden consumers).

### Matrix (all six axes searched)

- Axis 1 — Cross-flavor mirroring: SEARCHED. The flavors are the four
  patch modules; all four read in full. Findings: the six-member
  lifecycle mechanism is one rule with four definitions (CH-L below);
  the `apply`/`_validate_upstream_shape`/`_patch_is_installed` shared
  NAMES are the compose-by-name protocol (spec-024: "each with its own
  `apply()`"), not duplication; per-module shapes are declarations +
  adapters. Root/conftest carry no patch mirror (grep-clean).
- Axis 2 — Sync/async twins: SEARCHED. The target IS the sync side of
  an upstream sync/async pair and deliberately defines no async twin:
  inapplicable-for-construction with reason — upstream's async contract
  is already correct (P2) and the async adapter exposes no `body`
  member, so there is nothing to patch and the patch aligns sync TO
  async. The no-twin state is pinned by oracle
  `test_the_async_view_needs_no_adapter_override_because_upstream_hands_bytes`.
  The companion's sync/async multipart delegates were read as the
  adjacent twin pair; correctly paired, not this item's rule.
- Axis 3 — Derived knowledge: SEARCHED. (a) `(self)` arity via
  `inspect.signature` — per-module declaration inside the shared
  validation mechanism. (b) Install state via identity — shared
  detection mechanism. (c) `"cross_web"` key literal: ONE production
  consumer (`apply`'s gate call); vocabulary owned by
  `conf.py::UPSTREAM_PATCH_DEPENDENCIES`; the 3 message spellings +
  docstrings are projections, tests are oracles — listed, not counted.
  (d) Upstream-shape premises — derived from installed source, verified
  by P2, not assumed.
- Axis 4 — Round-trip pairs: SEARCHED. capture→validate→install→detect
  is one consistent chain (P3 proves each link incl. post-reload
  reinstall). Install has no uninstall half: 8 test restore sites spell
  `property(<captured getter>)` (transport:2, test_apps:1,
  test_cross_web_patches:4, test_views:1) — consumers of the install
  idiom, folded into the family proposal as an open question (helper vs
  explicit-by-design; my lean is explicit, since "setting the switch is
  not a simulation" makes visible restore-by-identity load-bearing).
  Retirement probes 1+2 are complementary halves (behavioral + snippet),
  both present and both executable. Package-view halves (adapter +
  decode) compose gatelessly (broad-switch row, HEAD).
- Axis 5 — Other-medium restatements: SEARCHED and classified.
  Definitions live in code (conf gate, four `apply` gates, the two
  getters, the strict decode). Prose = projections at owners per
  principle 10 (organizing rule: spec-024 → conf comment → docstrings;
  bug statement: target docstring + `views.py::_RawBodyRequestAdapter`
  docstring + test comments; joint ownership: target + strawberry +
  conf comment + transport rows). Tests = oracles, and all are
  independent: refusal `match=` strings are spelled literally, never
  imported from the owner; live rows read wire statuses; the reload
  test compares pre/post values rather than reading an expectation
  from the module. No oracle reads from its owner.
- Axis 6 — Enforcement by omission: SEARCHED. Family = 4 modules ×
  lifecycle members. Census (all 4/4 unless noted): import-try,
  capture fn, validate, stamps, installed-probe, `apply`+own-gate-key,
  `ready()` dispatch line, `UPSTREAM_PATCH_DEPENDENCIES` key, gate-off
  oracle (global + per-dependency), per-module test file. Divergences
  (mechanism shared, adapters differ — for the family item, not
  defects): capture arity (nullary-property vs `(owner, name)` vs
  classmethod-unwrap); validation depth (delegators pin call shape,
  reimplementers pin body — the contract both docstrings state);
  install idiom (`property(...)` vs plain assign vs `classmethod(...)`);
  detection cardinality (single vs all-members); stamping mechanics
  (bare `setattr` ×3 modules vs `_mark_patch_replacement` helper);
  capture matching strictness (exact-own-owner ×3 vs graphql_core's
  `startswith("django_strawberry_framework.")` loosening — unjustified
  by any docstring or test, must-reconcile in the family item, not a
  defect: no contract row names the strictness).

### Challenges (definitions counted; consumers/oracles/projections listed)

- CH-L1 capture mechanism ("reload recovery must also verify X"):
  4 definitions (`_captured_upstream_body_getter`,
  `_captured_upstream_method` ×2 — strawberry + graphql_core, same
  name, near-identical bodies modulo the strictness divergence —
  `_captured_upstream_descriptor`). Consumers: 4 `apply()`s via
  module captures; `test_apps.py` reload oracles (behavioral; no
  literal reads of the stamp values anywhere in tests — grep-clean).
  Projections: spec-024 rationale paragraph (django vocabulary).
  Count 4 → new family (mechanism); per-module descriptor-kind
  handling = adapter (CH-A).
- CH-L2 stamp vocabulary ("rename cross_web's attribute only"): 1
  definition (reader + writer share the module constant; no
  cross-module reader of the ATTRIBUTE name exists — graphql_core's
  cross-read is of the owner VALUE on its own method only) →
  independence; the literal is a per-module declaration inside the
  family, not its own rule.
- CH-L3 validation mechanism ("every validator must also pin Y"): 4
  definitions (the four `_validate_upstream_shape`s) → new family.
  Declaration half ("cross_web pins more of the getter"): 1 → stays a
  declaration.
- CH-L4 refusal wording ("reword the opt-out hint package-wide"): 11
  literals in 4 modules (cross_web 3, django 3, graphql_core 2,
  strawberry 3), each spelling its own dependency key + shape clause;
  within-module copies share no constant → 11 independently maintained
  literals, 4 module message-sets → new family (wording is a rule per
  the `seal-defect-code-wording` / `sync-boundary-recourse-wording`
  precedent). Oracles: spelled `match=` strings (independent).
- CH-L5 install detection ("detection must also verify Y"): 4
  definitions (the four `_patch_is_installed`s) → new family;
  single-vs-all membership = per-module declaration.
- CH-L6 apply sequence ("apply must also do X", e.g. an ordering or
  logging step): 4 definitions (the four `apply` bodies:
  gate→validate→installed?→install) → new family. Consumers: the
  four `ready()` dispatch lines (compose by name) + every test's
  direct `apply()` call. The shared ENTRY NAME `apply` is the
  compose-by-name protocol (spec-024), not duplication — renaming one
  module's entry breaks only its dispatch line.
- CH-L7 import resilience ("absent upstream raises at import
  instead"): 4 definitions (the four try/except sentinels; 3 share
  the comment verbatim, graphql_core's differs) → new family (6th
  sub-rule); per-module symbol lists = declarations.
- CH-A property-descriptor adapter ("upstream `body` becomes a
  non-property attribute"): moves cross_web's capture
  (`__dict__.get("body")` + isinstance-property + fget-None) +
  install (`property(_patched_body)`) + detect
  (isinstance-property + fget-identity) trio, plus the 8 test
  restore sites as consumers; siblings pin their own shapes and do
  not move → 1 definition → file-local.
- CH-T twin getters ("return a copy / coerce / delete"): the two
  textually identical one-line bodies (`_patched_body` vs
  `views.py::_RawBodyRequestAdapter.body`) must NOT move together —
  "upstream fixes the bug" deletes the patch getter and keeps the
  adapter; "package view drops its adapter" is impossible without
  losing the gate-off 400 (broad-switch row). Same text, different
  responsibilities/lifecycles → rejection (contract difference +
  trigger below), never file-local (names a second site).
- CH-K key rename ("rename the `cross_web` key"): 1 definition
  (`UPSTREAM_PATCH_DEPENDENCIES`, owned by File `conf.py`); this
  module holds 1 consumer (gate call) + projections (3 message
  spellings, docstrings) — listed, not counted. No assignment from
  this item.
- CH-G gate semantics: owned by File `conf.py`; this item's only
  holding is the consumer call + the axis-6 proof that exactly the
  four `apply()`s consult it.

### Assignment proposals

No existing index family fits: the 13 querysets families are
ORM/seal/visibility/coercion rules; the `__init__.py` rows are root
surface; the `_boundary_ordering.py` rows are middleware/view ordering
(the open `prepared-view-handoff-shape` is the prepared-view handoff,
unrelated to patch install shape). The gate + key vocabulary belong to
undispatched File `conf.py`. Hence one new family, one file-local row,
one rejection:

- NEW FAMILY `upstream-patch-module-lifecycle` (status open, holding
  item Family `upstream-patch-module-lifecycle`, members: all four
  `_*_patches.py` modules). The rule: the patch-module lifecycle
  MECHANISM — (1) import-resilient capture w/ `None` sentinel, (2)
  reload-tolerant capture + owner-stamp protocol, (3) loud shape
  validation + refusal wording, (4) install detection, (5) gated
  idempotent self-healing `apply` + entry-point protocol (+ the
  test-restore-idiom open question), (6) per-module declarations and
  descriptor-kind adapters (property/classmethod/plain-method,
  delegator-vs-reimplementer validation depth, single-vs-all
  membership, capture-matching strictness — the graphql_core
  loosening must be reconciled here). Shape precedent: the
  `SetLifecycleAttrs` worked example (one driver + per-member
  declarations). Owner candidates for the family item: (a) a new
  shared helper importing only conf+stdlib (conditional lean — only
  if every driver parameter has ≥2 real members, principle 5), (b)
  per-module code + a structural gate pinning the shared shape, (c)
  status quo + recorded rejection. The four `apply` BODIES share
  lifecycle shape (family); the four `apply` NAMES are protocol
  (compose-by-name, no row). Proposed index row: Family
  `upstream-patch-module-lifecycle` | Owner TBD by family item
  (candidates: shared helper vs pinning gate vs status quo) | Files
  covered: the four `_*_patches.py` modules | Holding item Family
  `upstream-patch-module-lifecycle` | Status open. Proposed
  `## Families` line: `- [ ] Family
  `upstream-patch-module-lifecycle` —
  [dry-rule-upstream-patch-module-lifecycle.md](dry-rule-upstream-patch-module-lifecycle.md)`.
- FILE-LOCAL: "Property-descriptor capture/install/detect adapter" |
  Owner `django_strawberry_framework/_cross_web_patches.py` (capture +
  install + detect trio) | Files `_cross_web_patches.py` | Holding
  item File `_cross_web_patches.py` | Status file-local. Proving
  challenge: CH-A (no second definition site; siblings unaffected).
- REJECTION: "Sync raw-bytes getter twin (patch vs package view)" |
  Owner `django_strawberry_framework/_cross_web_patches.py::_patched_body`
  (rejection recorded here; durable prose already exists at both ends:
  target docstring "That second half is not redundant with this patch"
  + `views.py::_RawBodyRequestAdapter` docstring "Why this is not the
  cross_web patch again") | Files `_cross_web_patches.py`, `views.py` |
  Holding item File `_cross_web_patches.py` | Status rejected.
  Contract difference: `_patched_body` is a temporary gated workaround
  for someone else's bug, serving Strawberry's-own-view and preserving
  RFC 8259 auto-detection, retiring when upstream stops eager
  decoding; `_RawBodyRequestAdapter.body` is permanent ungated package
  policy feeding the strict UTF-8 decode, holding in every patch
  state. Trigger: if the package view ever consumed the patched
  property (adapter deleted), or upstream fixed the bug (patch getter
  deleted), the two become one rule — reopen, owned by the lifecycle
  family in the first case, deleted in the second.
- Projections/consumers/oracles (listed, no rows): docstring prose at
  this owner (principle 10, verified C1–C10); gate call + key
  spellings (consumers/projections of conf vocabulary); 8 test
  restore sites (consumers of install shape); spelled-literal oracles
  (independent — none reads from its owner).

### Defects

None. Near-misses examined and resolved (not defects): (1) C9's "can
see the bare `.decode()`" — capability reading, design covers the
same-shape fix via retirement probe 1; (2) graphql_core's looser
capture matching — sibling divergence with no contract row naming the
strictness, routed as must-reconcile input to the lifecycle family
item; (3) installed strawberry 0.324.0 vs the companion docstring's
0.316.0/0.317.2 audit pins — the pin still holds (P3's `django.setup()`
applies all four patches) and nothing in THIS target depends on the
Strawberry version beyond the joint 400, which P4 re-proves at 0.324.0;
(4) no uninstall API — folded into the family as an open question with
an explicit-by-design lean, not a gap (no contract promises one).

### Probes (all re-run in this pass; commands from the workspace root)

- P1 `uv run python
  docs/dry/temp-tests/dry-file-_cross_web_patches-r2-w2/p1_enumerate.py`
  → 16 `Module.body` statements, 13 bound names (table under
  `### Enumeration`). Proves the census instrument + count.
- P2 `uv run python
  docs/dry/temp-tests/dry-file-_cross_web_patches-r2-w2/p2_upstream.py`
  → sync fget bare-decodes (UnicodeDecodeError on non-UTF-8: STILL
  NEEDED; `str` on BOM-less UTF-16-LE); async `get_body` returns raw
  bytes; protocol permits `Union[str, bytes]`; `parse_json` catches
  `JSONDecodeError` only with the pinned literal; sync/async read
  sites and Django adapter seams as claimed; async adapter defines no
  `body`. Proves C7–C8 at installed versions.
- P3 `uv run python
  docs/dry/temp-tests/dry-file-_cross_web_patches-r2-w2/p3_lifecycle.py`
  → `ready()` installs (minimal settings, dirty files outside the
  import graph); patched getter passes undecodable bytes through;
  captured getter still raises (STILL NEEDED); global-False declines,
  re-enable self-heals, repeat idempotent; reload retains the genuine
  capture by identity and post-reload `apply()` installs fresh;
  missing capture refuses loud naming the `{"cross_web": False}`
  opt-out. Proves C2–C4 install halves + the reload contract.
- P4 `uv run python
  docs/dry/temp-tests/dry-file-_cross_web_patches-r2-w2/p4_two_routes.py`
  → invalid-UTF-8 body: `json.loads` raises UnicodeDecodeError,
  unpatched `parse_json` lets it escape, patched translates to
  400-caused-by-UnicodeDecodeError; raw-binary body: `json.loads`
  raises JSONDecodeError (post-`surrogatepass` decode), unpatched
  `parse_json` already 400s. First run tested a wrong body (double
  backslash landed as literal text — byte-compared against the live
  row via `od -c`, fixed with explicit `bytes([...])`, re-run green).
  Proves C4's two-mechanism decomposition, matching the live row's
  recorded verification.

### Freshness fingerprints (all re-hashed in this pass)

- Target `django_strawberry_framework/_cross_web_patches.py`:
  `6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf` (HEAD == worktree).
- `django_strawberry_framework/_strawberry_patches.py`:
  `f77df3499eb96051d70055266a677ca3cde5b219`.
- `django_strawberry_framework/_django_patches.py`:
  `ba98f5859ec32971c3aa566c221bdc4db392e137`.
- `django_strawberry_framework/_graphql_core_patches.py`:
  `1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`.
- `django_strawberry_framework/apps.py`:
  `8ae1a3a3b12f0c9792094959c573ea6fab5d804f`.
- `django_strawberry_framework/conf.py`:
  `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`.
- `django_strawberry_framework/views.py`:
  `9f85b0df26a17e800ec392aa13f6848e07633895`.
- `tests/test_cross_web_patches.py`:
  `70c16389aa5d2a14746dba1612c909263bffd822` (clean).
- `tests/test_apps.py`: `5ca8b62c53185343ebfec95315f59ec6104fc851`
  (clean).
- `tests/test_views.py`: `4dc9a25723501cd1f84161423a1aefbf00ff7eb9`
  (clean).
- `tests/base/test_conf.py`:
  `f35c70742354d0ab123b163a92c6a8a503c6ea29` (clean).
- `tests/test_graphql_core_patches.py`:
  `53dca51737e6163c09549d015713ebf9dfcdec88` (clean).
- `examples/fakeshop/test_query/test_transport_api.py`: HEAD
  `17320f1ff335a868d5ed324a49f1d7c4ee899cfc` (worktree
  `818b639b538df98dd4c9d4571ebfc694bedc221a`, dirty — all claims use
  HEAD bytes; dirt verified unrelated).
- `examples/fakeshop/test_query/test_products_api.py`: HEAD
  `b863b29c5ab77153cc73db9827f2dfa447e5b88f` (dirty — HEAD bytes used).
- `tests/test_strawberry_patches.py`: HEAD
  `f4a0a8ff935fcece1e4fea4083965fe8b285d7cd` (worktree
  `94a5bfa489029328cda91dff893882bf8fc93e6f`, dirty — HEAD bytes used).
- `docs/SPECS/spec-046-transport_security-0_0_14.md`:
  `8d8adaf2f2f07cbc6cd3d434a029b2419b7d4704`.
- `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md`:
  `46335d7e98ea569cd85c3ec256b7276b04fb7dc1`.
- Upstream (`.venv`, live read): cross-web 0.7.0
  (`cross_web/request/_django.py`: sync `body` bare-decodes,
  `AsyncDjangoHTTPRequestAdapter.get_body` raw bytes),
  strawberry-graphql 0.324.0 (`http/base.py::parse_json` catches
  `JSONDecodeError` only; `sync_base_view.py` reads
  `parse_json(request.body)`; `async_base_view.py` reads
  `parse_json(await request.get_body())`; `django/views.py` adapter
  seams), Django 6.1.
- Searched populations: `git grep -n "_cross_web_patches"` (15
  production+test hits + kanban constants + sqlite, enumerated);
  `upstream_patches_enabled` (exactly 4 production call sites);
  `"cross_web"` literal (target 6 incl. docstrings+gate, conf
  vocabulary, test/transport oracles); stamp attributes (4 modules ×
  reader+writer, zero test reads of the values); `cross_web` mention
  counts per file (target 28, transport 26, siblings/views/tests
  single digits — census table above); root/conftest patch grep
  (zero hits).

### Pre-finish gate

DRY-scoped stop check: the target shows zero diff vs HEAD (re-verified
at pass end); the artifact `docs/dry/dry-file-_cross_web_patches.md`
remains an untracked path I never opened (name observed via
`git status` only, as the dispatch requires); no third-party hunk in
any path this item touches. Concurrent dirt elsewhere (113 dirty
entries at start — the dispatch's 112 plus the artifact itself —
growing only outside this item's paths) is untouched and not a stop.
HEAD at end: `bfaee91dcd332a5f86250fff90ab21b377bc674e` — unmoved, so
every claim above rests on a single HEAD (P2/P3/P4 additionally execute
installed `.venv` bytes: cross-web 0.7.0, strawberry-graphql 0.324.0,
Django 6.1, which is the correct input for an installed-version
verification).

## Independent verification (Worker 2) — reconciliation (Phase B)

Phase-A section above was appended mechanically (`cat >>`, 28232-byte
tail byte-verified) before this read. HEAD still `bfaee91d`, target
still clean at `6b3a7c35`, no foreign hunk in any item path. Worker 1's
artifact (lines 1–560) and scratch probe read in full; W1's probe
re-run in my hands 7/7 PASS (P1a/P1b/P2/P2b/P3/P4/P5). Every difference
from Phase A is reconciled below; agreements are stated, not assumed.

### D1 — Family granularity: adopt W1's two-family split

Phase A proposed one family (`upstream-patch-module-lifecycle`, 6
sub-rules); W1 proposes F1 `upstream-patch-lifecycle` (mechanism) + F2
`upstream-patch-refusal-wording` (wording). W1's split is better: it
matches the cycle precedent (seal-policy vs seal-wording are separate
families), wording moves independently of the state machine (W-C1 vs
LC-C2), and the two halves have distinct natural owners (shared helper
vs `conf.py` beside the gate it phrases — principle 7). My six
sub-rules map completely: import-sentinel, capture+stamps, validation,
detection, gated-apply+entry protocol → F1; refusal wording (11
literals) → F2; declarations/adapters → F1 variation + L2. Adopt W1's
names verbatim (including the shorter `upstream-patch-lifecycle`).

### D2 — Retirement prose earns a file-local row: adopt W1's L1

Phase A treated all docstring prose as projections needing no row; W1
records L1 (retirement/audience prose, count-1 challenge L-C1). W1 is
more faithful to the backstop: every member must land in a row, and
the retirement procedure is DEFINED only in this docstring (the gate
narrative projects `conf.py`, but the two checks + misreading analysis
have no second site). My C8/C9 verifications become supporting
evidence for L1. Adopt.

### D3 — Rejection trigger + recording owner: adopt W1's

Same pair, same contract difference (kill-switch-thrown mounts answer
differently — one spelling cannot produce both). Trigger: W1's pair
(patch-becomes-permanent-policy OR view-delegates-to-patched-class) is
the correct merge-condition form; my second trigger (upstream fix
deletes the getter) was a lifecycle event, not a merge condition —
withdrawn. Recording owner: adopt W1's `views.py::_RawBodyRequestAdapter`
pointer (fuller clause lives there; separation prose verified at both
ends). Holding item unchanged (this file item).

### D4 — Axis-4 framing: both kept, no action

W1 rules the product round-trip inapplicable-with-reason (install-once;
revert is test scaffolding; no uninstall contract); Phase A searched
install-vs-restore as a pair with an open question. Substance agrees on
all three points (no uninstall owed; 8 restore sites are consumers of
the install idiom; kind-pair lives in family + adapter). Keep both
framings; W1 lists the transport helpers under F1 consumers, which is
where the restore question now lives.

### D5 — Axis-6 populations: both kept, complementary

W1 enumerates installed adapter members (only sync `body` decodes —
verified independently from my own read of `cross_web/request/_django.py`;
non-Django adapters excluded with reason); Phase A enumerated patch
modules × lifecycle members (4/4 census + 6 divergences). Both
correct, both no-gap; together they bound the omission question from
both ends. No action.

### D6 — W1-only additions: adopted

LC-C3 fifth-dependency challenge (principle-1 pressure — good addition,
no Phase-A equivalent); explicit non-patch-flavor exclusion;
`test_patch_is_installed_on_adapter` as independent re-derivation
oracle (verified: asserts `fget is` directly, never calls the probe);
prior-cycle trigger check; GLOSSARY + installed-file + `utils/policies.py`
fingerprints (all three re-hashed byte-identical by me: `bc51debc…`,
`fa2a5bef…`, `860b181f…`).

### D7 — W2-only additions: kept as supporting evidence

P3 (install/gate/reload under minimal settings) and P4 (two-route
decomposition of the joint 400: invalid-UTF-8 needs both halves,
raw-binary needs only this half — in-process proof of C4 beyond the
live row's docstring claim) stand as executed evidence both workers'
records may cite. CH-L2 precision kept inside F1's stamp sub-rule: a
single-module stamp rename moves 1 definition (the literal is a
per-module declaration; no cross-module reader of the ATTRIBUTE name
exists), while a protocol change moves 4 — mechanism-vs-declaration,
not a count dispute.

### D8 — Evidence correction: GLOSSARY entry title (no revision action)

W1 cites a GLOSSARY "'defensive upstream patches'" entry (System trace,
F1 projections). The entry is titled "Upstream patches" (verified,
`## Upstream patches` heading; "The kill switch" is its bolded
subsection; the prose says what W1 claims — four modules, gate shapes,
joint ownership). Only the label is imprecise; zero effect on any
count, role, row, or fingerprint. This reconciliation is part of the
artifact, so the record-as-a-whole now contains the truth. No
substantive driver exists to bundle a re-pass with → not a
revision-needed driver. (Same disposition for R-C2's loose "redundant
shadow" word: count unaffected — removal not forced.)

### Agreements (explicitly reconciled, all hold)

- Enumeration: 16 nodes / 13 rule-bearing + 3 rule-free imports, node
  homes identical (9/11/15 split by aspect both sides).
- Challenge counts: LC-C1 4, LC-C2 4, LC-C4 4, W-C1 11 sites / 4
  module wordings (exact), R-C1 1, R-C2 1, L-C2 1 — all independently
  matched. F2's 3/3/3/2 site split and version-noun divergences
  verified against the four validators.
- Fingerprints: all 15 shared inputs byte-identical across both
  workers' re-hashes (target, 3 siblings, apps, conf, views,
  test_cross_web_patches, test_apps, test_views, base/test_conf,
  test_strawberry_patches@HEAD, transport@HEAD, products@HEAD,
  request_body exclusion).
- Roles: async `get_body` = oracle (both); gate call = consumer edge
  owned by File `conf.py` (both); `match=` oracles spelled, never
  reading from owners (both); base `body` abstract with no default
  decode (verified `@abc.abstractmethod` + raise); toolbar
  `json.loads(request.body)` = panel display parsing, excluded
  (verified in context); KANBAN S9 history lines exist as cited.
- Defects: none either side; near-miss lists overlap (graphql_core
  prefix-match + missing docstring + pragma-comment divergence, dated
  version claims, reload/gate hazards each traced to a permanent
  oracle).
- Pending execution: empty; sharded/PG inapplicable by construction —
  endorsed (target performs no DB access; P3 ran with DATABASES={}).
- Zero-edit file item: no production edit owed or made (target clean
  confirms); structural gates correctly deferred to the family items
  with negative-control shapes named; F1↔F2 coupling recorded.
- Matrix discharged against the target's real surface on all six
  axes (D4/D5 framings both kept).

### Checks Worker 2 ran for this verdict

- W1 probe re-run: 7/7 PASS, exit 0 (bare process; imports only
  HEAD-clean modules — target, `conf.py`, `exceptions.py` all
  verified clean).
- W1-only fingerprints re-hashed: 3/3 identical (above).
- Item diff: artifact (untracked, W1 content + my blind-appended
  Phase-A section + this section) + untracked scratch only; zero
  tracked production/test edits; tree at 113 dirty entries, none in
  item paths.
- Ruff read-only over both scratch scopes: findings are scratch
  hygiene only (annotations, deliberate post-setup E402s, unused
  noqa, SIM/PERF nits) — no gate covers untracked scratch; all
  probes executed green. The item diff itself (artifact `.md`) is
  per-cycle scratch, style-exempt; `path:NN` uses inside it are
  allowed.
- AGENTS.md prose rules: no process provenance in any finding, no
  commits, plan untouched (Worker 0 alone edits it; it is
  concurrently dirty).

### Verdict + handoff to Worker 0

Status: verified (set below). No `proof:`/`gate:` entries → plain
`verified`, no pending-execution qualifier. Scratch custody: both
scopes retained (`dry-file-_cross_web_patches-r2-w1/`: replayable
7/7 probe; `dry-file-_cross_web_patches-r2-w2/`: Phase-A section +
P1–P4 probes) — closeout decides retention per the querysets
precedent, not this item.

Worker 0 is asked to: tick File `_cross_web_patches.py` as verified;
transcribe W1's 5 index rows (`upstream-patch-lifecycle` open,
`upstream-patch-refusal-wording` open, raw-bytes-getter rejection,
retirement-prose file-local, property-kind file-local — all
W2-endorsed, D8 label correction noted); add the 2 `## Families`
items; no `## Owned changes` rows (zero-edit).

## Iterations

### Adjudication-1 (Worker 1): freshness reconciliation 2, `bfaee91d..69a25369`

Scope: the scoped re-review dispatched under the plan's `## Run 0.0.15
2026-09-21-2` ("Freshness reconciliation 2" + "Schedule"). No
production edits owed or made; this section + the `Status:` line are
the whole item diff. `ITEM_BASELINE=1545fca1` verified resolvable
(`git cat-file -t` = commit). HEAD at dispatch and at finish:
`69a253690002fdd413704a7879528c3ded363020` — unmoved throughout.

Causing range: three commits, exactly one touching this item —
`a01a2ab8` ("move the request-observable rows live and pin the cost
each one claims"); `1dd7d147` is kanban-only, `69a25369` deletes
`docs/feedback2.md` only. Zero package files in the range.

#### Re-hash: the stale set is THREE files, not two (correction reported)

Every recorded fingerprint re-hashed from HEAD bytes (`git show
HEAD:<path> | git hash-object --stdin`; worktree is concurrently
dirty, so HEAD bytes are the correct input). 19/22 MATCH; stale:

| Input | Recorded | HEAD now |
|---|---|---|
| `examples/fakeshop/test_query/test_transport_api.py` | `17320f1f…` | `818b639b538df98dd4c9d4571ebfc694bedc221a` |
| `tests/test_strawberry_patches.py` | `f4a0a8ff…` | `94a5bfa489029328cda91dff893882bf8fc93e6f` |
| `examples/fakeshop/test_query/test_products_api.py` | `b863b29c…` | `106aeff76d6292e95166679b5231e065d83a027f` |

MATCH (byte-identical, no re-review owed): target `6b3a7c35…`,
`_django_patches.py` `ba98f585…`, `_strawberry_patches.py`
`f77df349…`, `_graphql_core_patches.py` `1cd579fb…`, `conf.py`
`c6ad46aa…`, `apps.py` `8ae1a3a3…`, `views.py` `9f85b0df…`,
`middleware/request_body.py` `e6e32e78…`, `utils/policies.py`
`860b181f…`, `tests/test_cross_web_patches.py` `70c16389…`,
`tests/test_apps.py` `5ca8b62c…`, `tests/base/test_conf.py`
`f35c7074…`, `tests/test_views.py` `4dc9a257…`,
`tests/test_graphql_core_patches.py` `53dca517…`, `docs/GLOSSARY.md`
`bc51debc…`, spec-046 `8d8adaf2…`, spec-024 `46335d7e…`, and the
installed upstream `cross_web/request/_django.py` `fa2a5bef…`
(live `.venv` read; installed strawberry still 0.324.0, Django
still 6.1).

The two expected blobs landed clean: both equal the dirty-worktree
hashes W2 recorded at `bfaee91d` (`818b639b…`, `94a5bfa4…`) exactly.
The third — `test_products_api.py` — is a reconciliation-2 miss:
it sits in R1's Freshness row (artifact line 448) and W2's
fingerprint list (lines 992–993), and it is in the landed set
(`git diff --name-only bfaee91d..69a25369` names it), yet the
reconciliation table lists only two stale inputs for this item.
Per dispatch ("any other mismatch reopens that finding's scope —
report it, do not silently widen"): R1's scope reopens for that
one input, re-reviewed below, now re-closed. No other finding
cites it (the remaining artifact hits at lines 44 and 578 are the
System-trace oracle listing and W2's read list, both file-level).

#### Hunk-by-hunk vs every recorded claim

`test_transport_api.py` (`a01a2ab8`, 2 hunks, +16/−1, net +15;
test-def count 61 → 62, zero removed, zero modified):

- Hunk 1 (import line): adds `post_graphql_raw` to the
  `graphql_client` import. Touches no helper, no oracle row, no
  restore site. F1's "opt-out helpers (restore-by-identity + probe
  asserts)" consumer claim (line 255) and W2's 8-restore-site
  census (transport:2) stand — the helpers sit between the two
  hunks, byte-identical.
- Hunk 2 (new row `test_post_not_json_body_is_upstreams_malformed_json_400`
  + docstring): purely additive. The three cited oracle rows —
  `test_the_cross_web_half_turns_upstreams_own_500_into_a_400`
  (F1/C4/L1 live pin, HEAD line 2070),
  `test_the_sync_wire_contract_holds_with_every_upstream_patch_opted_out`
  (C5 broad-switch, line 1934),
  `test_only_the_package_mount_answers_the_same_way_in_both_patch_states`
  (R1/C5 attribution, line 1969) — are all outside both hunks,
  byte-identical to `bfaee91d`. W2's P4 byte-comparison premise
  and C4's two-mechanism decomposition rest on unchanged bytes.

`tests/test_strawberry_patches.py` (`a01a2ab8`, 2 hunks, +2/−12):
docstring +2 lines pointing at the new live transport row, and
deletion of `test_patched_parse_json_passes_through_malformed_json_as_400`
(the re-tiering move: package-tier `HTTPException(400)` pin →
live wire row above). No artifact claim cites the deleted row by
name (verified by sweep: no `malformed_json_as_400` /
`passes_through_malformed` hit anywhere in this artifact); it
carried no `match=` fragment (`match=` count 12 → 12), so F2's
spelled-literal oracle pins are intact. F1 cites this file only
as sibling-suite oracle input; the strawberry production module
it oracles is MATCH.

`test_products_api.py` (`a01a2ab8`, 3 hunks, +116/−4): two new
`updateItem` attachment rows (purely additive, 200-path mutation
rows) and an extension of
`test_create_item_relation_id_for_hidden_category_is_field_error`
(docstring + missing-pk no-leak assertions — verdict
strengthened, still the same row). The artifact cites this file
only file-level ("package-mount 400 rows", line 44; R1
Freshness). The only modified row is a GraphQL field-error
envelope row (HTTP 200 + `errors`), not a wire-400 row; every
transport/package-mount-400 row is outside all three hunks and
byte-identical. R1's oracle citation stands.

#### Dispositions

- F1 `upstream-patch-lifecycle` (4-module definition counts,
  opt-out-helper consumer roles): CONFIRM. All production inputs
  MATCH; helpers untouched; sibling-suite move cites nothing
  counted. Fingerprints refreshed: transport `818b639b…`,
  strawberry-suite `94a5bfa4…`.
- F2 `upstream-patch-refusal-wording` (11 sites / 4 module
  wordings): CONFIRM. All four validators MATCH; `match=` oracle
  pins 12/12 intact. Same two refreshed hashes apply.
- R1 raw-bytes-getter rejection (live oracle pins): CONFIRM.
  Attribution + retirement-diagnostic rows byte-identical;
  products_api citing claims re-verified against the landed
  hunks (scope reopened and re-closed). Fingerprints refreshed:
  transport `818b639b…`, products_api `106aeff7…`.
- L1 retirement/audience prose (live-row procedure): CONFIRM.
  Diagnostic row identical. Fingerprint refreshed: transport
  `818b639b…`.
- L2 property-descriptor-kind handling: CONFIRM. All inputs
  (target + three siblings) MATCH; no stale input cites it.

No REVISE: the landed re-tiering moves no definition count,
no oracle role, and no projection citation. Every dispatch-named
artifact line (~41, ~62, ~255, ~324–326, ~434, ~446, ~477, ~577,
~649, ~988) was re-verified individually against the hunks above.

#### Pending execution, defects, probes

`## Pending execution` is still empty and still correct: every
probe-backed conclusion (W1 7/7 probe, W2 P1–P4) rests on inputs
verified byte-identical in this pass (target, installed upstream
file + versions, live-row bytes), so no conclusion I touch
requires re-derivation under a fresh scope — nothing was
touched, only confirmed by input identity. The run-2
`dry-file-_cross_web_patches-r2-*` scopes remain absent per the
worktree-entry note; no new scope was needed (static-decidable;
no `.py` added, so no ruff gate applies). No defects were
recorded and none were found. Sharded/PG inapplicable-by-construction
stands (no database, alias, or dialect surface in the stale
inputs' delta or anywhere in-target).

#### Index rows

No change owed to Worker 0. The 2 open families
(`upstream-patch-lifecycle`, `upstream-patch-refusal-wording`),
1 rejection, and 2 file-local rows stand exactly as transcribed:
no definition count moved. The one correction for the plan
record is the stale-set size itself (three inputs, not two),
with R1's products_api re-review now on record here.

## Independent verification (Worker 2) — adjudication

Method: two-phase per dispatch. Phase A (below, as recorded pre-read) was
written to `docs/dry/temp-tests/dry-adjud-crossweb-w2/phase_a_expectations.md`
BEFORE opening `## Iterations` (artifact line 1199+), from lines 1-1198 +
HEAD bytes only. `ITEM_BASELINE=1545fca1…` verified resolvable
(`git cat-file -t` = commit). HEAD at start `69a25369`, HEAD at finish
`69a25369` — unmoved, so every fingerprint and census below rests on one HEAD.
All content reads used `git show` / `git grep <rev>` (immune to concurrent
worktree dirt). No pytest (static-decidable: every conclusion rests on byte
comparisons); no `.py` added, so no ruff gate applies.

### Phase A (as recorded pre-read; full text in the scope file above)

Stale set derived independently: THREE files (single causing commit `a01a2ab8`;
all three clean in the worktree), not the two reconciliation 2 lists —
`test_transport_api.py` (`17320f1f…` → `818b639b538df98dd4c9d4571ebfc694bedc221a`),
`tests/test_strawberry_patches.py` (`f4a0a8ff…` → `94a5bfa489029328cda91dff893882bf8fc93e6f`),
`examples/fakeshop/test_query/test_products_api.py` (`b863b29c…` →
`106aeff76d6292e95166679b5231e065d83a027f`). The other 17 recorded git
fingerprints MATCH (every recorded value also verified == its `bfaee91d` blob);
installed upstream `cross_web/request/_django.py` re-hashes `fa2a5bef…`,
byte-identical. The two tabled blobs equal the dirty-worktree hashes run-2 W2
recorded at `bfaee91d` — `a01a2ab8` landed exactly the bytes run-2 already
cleared as unrelated (artifact line 580). Reconciliation 2's "remaining hits
are prose mentions, not `Freshness` rows" is wrong for `test_products_api.py`:
it sits in R1's Freshness row (line 448) and W2's fingerprint list (lines
992-993), so per DRY.md R1 reopens on it — a table correction note is owed to
Worker 0 regardless of W1's record.

Hunk expectations (no package blob moved; the artifact pins NO line numbers and
names NO row inside the strawberry/products files, verified by sweep over lines
1-1198): T1 (import +`post_graphql_raw`) no-op CONFIRM; T2 (+15 new
`test_post_not_json_body_is_upstreams_malformed_json_400`) CONFIRM — the three
cited oracle rows shift exactly +15 with identical bodies (2055→2070, 1919→1934,
1954→1969), test count 45→46 with zero deletions, restore idiom still exactly 2
in this file, `cross_web` mentions 27→27; S1 (docstring +2 moved-row pointer)
no-op CONFIRM; S2 (−12 deleted in-process malformed-JSON row) CONFIRM — the row
is named nowhere in lines 1-1198, `match=` 12→12 and `RuntimeError` 13→13 keep
every refusal oracle byte-intact, coverage moved live to T2, and F2 never
fingerprinted this file (MATCH-only, no F2 re-review owed); P1 (+92 two
`updateItem` attachment rows) no-op CONFIRM; P2 (visibility docstring reword)
no-op CONFIRM; P3 (missing-pk existence check) CONFIRM — zero deletions
(135→137), all 12 `status_code == 400` asserts byte-identical shifted uniformly
+112, the extended test is a visibility-envelope test, not a wire-contract row.
Sweep populations re-verified old-vs-new: `_PATCH_OWNER` exactly the 4 modules;
lifecycle vocab identical file set; `upstream_patches_enabled(` identical 4
gates at identical lines; deleted kanban test file 0 swept-term hits;
kanban `constants.py` diff 0 `cross_web` lines; `docs/TREE.md` correctly
excluded (prose projection, not fingerprinted). Expected overall: all CONFIRM,
three hashes refresh, pending stays empty, defects stay none.

### Reconciliation (every difference resolved)

- R-1 stale set: NO DISAGREEMENT. W1 independently derived the same THREE
  files, caught the same reconciliation-2 miss (products_api), and framed the
  same correction. The correction note to Worker 0 is endorsed (owed; W1's
  record already carries it, this section seconds it).
- R-2 dispositions: full agreement — F1/F2/R1/L1/L2 all CONFIRM, same three
  refreshed full hashes (all three W1-quoted in full, byte-identical to mine),
  pending empty, defects none, no execution needed.
- R-3 per-hunk: full agreement — T1/T2/S1/S2/P1-P3 claims all match (cited-row
  HEAD lines 2070/1934/1969 identical both sides; deleted row unnamed both
  sides; 12/12 `match=` both sides; products 400-rows byte-identical both
  sides). Four immaterial deltas: (a) W1's "19/22 MATCH" headline should read
  18/21 — mechanical enumeration of lines 1-1198 yields exactly 25 distinct
  40-hex values = 21 HEAD-fingerprint values (20 git paths + installed file) +
  HEAD id + baseline id + 2 run-2 worktree hashes; W1's own named list is my
  same 18+3=21 and every VALUE agrees, so the fraction is a summary slip only.
  (b) My Phase-A products stat "+115/−5" is WITHDRAWN — W1's "+116/−4" is
  correct (hunk headers: 92+4+20 added, 0+3+1 removed; net +112 matches the
  measured uniform shift). (c) Transport test-def count 61→62 (W1, unanchored)
  vs 45→46 (mine, anchored): instrument convention, same +1 delta, zero
  removed — verified both instruments both revs. (d) W1's "same two refreshed
  hashes apply" under F2 is loose phrasing (F2's Freshness names neither
  file, so no F2 hash refreshes) but the underlying check (12/12 pins intact)
  is correct and CONFIRM stands; a re-pass to reword it is not warranted.

### Verification job

- Fingerprint agreement: every quoted value agrees (18 MATCH prefixes + 3
  stale full-hash pairs, all byte-identical across both workers).
- Artifact untouched except W1's hunks: the file is untracked, so — heading
  sequence is exactly run-2's nine sections + `## Iterations` at 1199;
  junction (blank + header + blank) is a clean append; total 1348 = 1198 +
  150-line record; every W1-cited line (~41, ~62, ~255, ~324-326, ~434, ~446,
  ~477, ~577, ~649, ~988 — spot-checked all nine windows) resolves to the
  claimed citing content, which any mid-file edit would have shifted; `Status:`
  line 3 is the swap. No third-party hunk in any path this item touches (item
  touches only the artifact + my scope, which holds exactly the Phase-A file;
  no W1 scope exists, consistent with W1's static-decidable record).
- AGENTS.md prose on the diff: markdown-only append; raw line refs are allowed
  in `docs/dry/dry-*.md` per-cycle scratch; no process provenance as evidence,
  no commit, plan untouched, no prohibited content (swept).
- Pending execution still empty (lines 529-537, unchanged) and still correct:
  every probe-backed conclusion rests on inputs both workers verified
  byte-identical (target, installed upstream file + versions, live-row bytes),
  so no re-derivation is owed. Defects still none (lines 507-528, unchanged;
  W1 found none). Sharded/PG inapplicable-by-construction endorsed (no
  database, alias, or dialect surface in-target or in the delta).

### Verdict + handoff to Worker 0

Status: verified (set above). No `proof:`/`gate:` entries → plain `verified`.
Zero production edits, zero `## Owned changes` rows. Index rows unchanged (2
open families, 1 rejection, 2 file-local). Scratch custody: my scope
`docs/dry/temp-tests/dry-adjud-crossweb-w2/` (Phase-A record only) retained for
closeout. One item owed to Worker 0: the reconciliation-2 table correction
(this item's stale set is three inputs — `test_transport_api.py`,
`tests/test_strawberry_patches.py`, `test_products_api.py` — not two), already
recorded by W1 and seconded here.

### Adjudication-2 (Worker 1): freshness reconciliation 3, `69a25369..24e6b4d3`

Scope: the scoped re-review dispatched under the plan's `## Run 0.0.15
2026-09-21-3` ("Freshness reconciliation 3" + "Adjudication-2 dispatch,
File `_cross_web_patches.py`"). No production edits owed or made; this
section + the `Status:` line are the whole item diff.
`ITEM_BASELINE=3d181e5a05154d1374ea18307e84fcb335b37720` verified
resolvable (`git rev-parse --verify` returns it). HEAD at start and at
finish: `24e6b4d3e74b104779225cd6bbff713880bc48e3` — unmoved throughout.

Append-only self-proof (artifact untracked): pre-edit `85437 B /
sha256 13ae779fb2b751d87706bdfc3abea3d63fa43d0e9eb9b463effba0b1c5a3c349`.
W2 reconstructs by restoring the `Status:` line to `Status: verified`,
truncating to 85437 bytes, and hashing (self-verified by W1: matches).

Causing range: 11 commits, exactly two touching this item's inputs —
`9350eb8d` (default-policy canonicalization + ErrorPolicy exact-type
close; owns the whole `utils/policies.py` diff and 4 of 5 GLOSSARY
hunks) and `44712901` (sliced-child refusal; owns the 5th GLOSSARY
hunk, the Prefetch-alias-threading re-render at `:1555`). Per-file
`git log` in-range confirms the attribution (`policies.py`: only
`9350eb8d`; GLOSSARY: both). The other 9 commits touch no
fingerprinted input of this item.

#### Blind re-hash: exactly the 2 tabled stale inputs, zero unexpected

Every recorded fingerprint re-hashed from HEAD bytes (`git rev-parse
HEAD:<path>`; worktree is concurrently dirty, so HEAD bytes are the
correct input; installed file via `git hash-object` of the live
`.venv` path). Recorded pins below are the effective post-adjudication-1
values (transport `818b639b…`, strawberry-suite `94a5bfa4…`,
products `106aeff7…`); every one of them also equals its `69a25369`
blob (old-pin exactness holds in all 20 git rows).

STALE (2):

| Input | Recorded | HEAD now |
|---|---|---|
| `django_strawberry_framework/utils/policies.py` | `860b181f…` | `8c881c0a165dc31022051dd628d6e36d99d44eca` |
| `docs/GLOSSARY.md` | `bc51debc…` | `d3ef357c26ede6a5bd21d4290b394ade4eb987b4` |

MATCH (18 git + installed = 19, byte-identical): target `6b3a7c35…`,
`_django_patches.py` `ba98f585…`, `_strawberry_patches.py`
`f77df349…`, `_graphql_core_patches.py` `1cd579fb…`, `conf.py`
`c6ad46aa…`, `apps.py` `8ae1a3a3…`, `views.py` `9f85b0df…`,
`middleware/request_body.py` `e6e32e78…`,
`tests/test_cross_web_patches.py` `70c16389…`, `tests/test_apps.py`
`5ca8b62c…`, `tests/test_strawberry_patches.py` `94a5bfa4…`,
`tests/base/test_conf.py` `f35c7074…`, `tests/test_views.py`
`4dc9a257…`, `tests/test_graphql_core_patches.py` `53dca517…`,
`test_transport_api.py` `818b639b…`, `test_products_api.py`
`106aeff7…`, spec-046 `8d8adaf2…`, spec-024 `46335d7e…`, and the
installed upstream `cross_web/request/_django.py` `fa2a5bef…`.

Containment (run 2's three-not-two lesson, verified mechanically, never
by basename memory): (a) basename sweep of this artifact over all 37
in-range changed paths hits only `GLOSSARY.md` (lines 47, 327, 1235)
and `policies.py` (lines 68, 336, 657, 1103, 1231) — every other
changed basename (KANBAN, connection, walker, schema, the 7 package
tests, the 5 live modules, the 5 spec/builder docs, feedback.md,
README, KANBAN.html, db.sqlite3, the querysets artifact) has zero
hits; (b) distinct-40-hex enumeration over artifact lines 1–1198
yields exactly 25 = 21 HEAD-fingerprint values (20 git + installed) +
HEAD id + baseline id + 2 run-2 worktree hashes, reproducing W2's
adjudication-1 proof — so the grounded table size is **21 rows, not
22** (the plan's "2 of 22" denominator is off by one, an inherited
count erratum; the stale SET itself — these exact 2 files — is
correct and complete, and no finding's scope widens). No third stale
input exists to reopen any scope.

#### Hunk-by-hunk vs every recorded claim

`utils/policies.py` (`9350eb8d` only, 2 hunks, +12/−2):

- Hunk P1 (`@@ -5,7 +5,9`, module docstring): adds the
  fail-closed-default canonicalization sentence. Prose about policy
  resolution; names no gate, adds no call.
- Hunk P2 (`@@ -123,12 +125,20`, `resolve_policy` docstring +
  no-override return): +8 docstring lines + `return default` →
  `return canonical_policy(…)`. The behavior change is confined to
  policy resolution (the default path now canonicalizes like every
  other path).
- The gate cite both hunks sit above is OUTSIDE them and byte-identical:
  old `:152/:164` → new `:162/:174` (uniform +10 shift = P1's +2 plus
  P2's +8, all above), still exactly 2 mentions in the file at both
  heads (`git grep upstream_patches_enabled|APPLY_UPSTREAM_PATCHES`),
  both `#`-comment lines, content-identical
  ("`conf.py::upstream_patches_enabled` … its own settings mapping" /
  "key-guard precedent"). Zero gate-mention lines inside the delta
  (mechanical count: 0). The exclusion characterization — "cites the
  gate only as a mapping-validation precedent" (F1 Freshness, line 68,
  W2 C5) — reads exactly the same way at the new bytes, so the
  exclusion stands with no re-read ambiguity.
- C5's gate census re-verified at HEAD: production
  `upstream_patches_enabled(` call sites are exactly the four
  `apply()` gates at identical lines (cross_web:342, django:414,
  graphql_core:122, strawberry:842; the `conf.py:411` hit is the
  owner's own error-message f-string, not a call site — unchanged,
  `conf.py` MATCH). `views.py` still never calls it; policies
  mentions still comment-only. C5 HOLDS.

`docs/GLOSSARY.md` (4 hunks `9350eb8d` + 1 hunk `44712901`, all
substitutions, net zero lines):

- Hunk G1 (`@@ -24`, `9350eb8d`): `DEFAULT_*_POLICY` summaries +
  `DjangoErrorPolicyExtension` install-position summary reworded.
- Hunk G2 (`@@ -838`, `9350eb8d`): ErrorPolicy `__post_init__`
  exact-type sentence added.
- Hunk G3 (`@@ -1124`, `9350eb8d`): mask-ordering entry restated for
  built-first-chain install.
- Hunk G4 (`@@ -1555`, `44712901`): Prefetch-alias-threading sentence
  re-rendered (the `reject_sliced` correction).
- Hunk G5 (`@@ -1571`, `9350eb8d`): production-error-policy entry
  restated for built-first-chain masking.
- Zero patch-vocabulary lines in the whole delta (mechanical count over
  added/removed lines for `patch|kill switch|cross_web|
  upstream_patches|APPLY_UPSTREAM`: 0) — every hunk lives in a
  policy/error/optimizer entry this item never cites.
- F1's projection cite (the `## Upstream patches` entry at `:2089`,
  D8-corrected title as baseline) and F2's cite (the bolded `**The
  kill switch.**` subsection at `:2097`) are byte-identical at the new
  HEAD: window `:2085–2115` md5 `2dabc152…` at BOTH heads, same line
  numbers (all hunks above are net-zero, nothing shifts). No re-pin
  needed — nothing moved.

Counts re-verified, untouched: F1's 4-module definition counts (all
four patch modules + `conf.py`/`apps.py` MATCH); F2's 11 sites / 4
module wordings (all four validators MATCH); the `match=` oracle pins
recounted at both heads — test_strawberry_patches 12→12,
test_cross_web_patches 3→3, test_graphql_core_patches 2→2,
base/test_conf 26→26 (test_apps 0 both). The 12/12 wording pins stand.

R1/L1/L2 take no re-review: R1's inputs (views, transport,
test_views, products) all MATCH; L1's (target, transport) MATCH —
its GLOSSARY-projection prose mention names no line the delta
touches (delta has zero patch-vocabulary lines, shown above); L2's
(target + three siblings) MATCH.

#### Dispositions

- F1 `upstream-patch-lifecycle` (4-module definition counts,
  GLOSSARY projection, policies exclusion): CONFIRM. Projection
  lines byte-identical; exclusion cite re-read at the new bytes and
  intact (comment-only, same two lines, +10 shift). Fingerprints
  refreshed: policies `8c881c0a…`, GLOSSARY `d3ef357c…`.
- F2 `upstream-patch-refusal-wording` (11 sites / 4 module wordings,
  "kill switch" entry): CONFIRM. All validators MATCH; entry
  byte-identical; 12/12 pins recounted. Fingerprint refreshed:
  GLOSSARY `d3ef357c…` (F2's Freshness inherits F1's production pins
  plus its oracle pins, all MATCH).
- R1, L1, L2: CONFIRM (no stale input cites them; GLOSSARY delta
  proven patch-vocabulary-free).

No REVISE: the landed policy canonicalization + exact-type close and
the Prefetch prose re-render move no definition count, no oracle
role, no projection citation, and no exclusion hold.

#### Pending execution, defects, probes

`## Pending execution` is still empty and still correct: every
conclusion I touch rests on byte comparisons and `git grep`/`git
show` reads over HEAD bytes, so nothing requires re-derivation under
a fresh scope — static-decidable, no scope created (the run-2 scope
`docs/dry/temp-tests/dry-adjud-crossweb-w2/` exists as the prior
record and was never touched; no `.py` added, so no ruff gate
applies). No defects were recorded and none were found.
Sharded/PG inapplicable-by-construction stands (no database, alias,
or dialect surface in-target or in the delta).

#### Index rows

No change owed to Worker 0. The 2 open families
(`upstream-patch-lifecycle`, `upstream-patch-refusal-wording`),
1 rejection, and 2 file-local rows stand exactly as transcribed:
no definition count moved. The one correction for the plan record
is the table denominator itself (21 fingerprinted rows, not 22 —
the 2-file stale set is exact).

## Independent verification (Worker 2) — adjudication-2

Method: two-phase per dispatch. Phase A was recorded in
`docs/dry/temp-tests/dry-adjud2-crossweb-w2/phase_a_expectations.md`
BEFORE opening `### Adjudication-2` (artifact line 1462+), from lines
1–1461 + HEAD bytes only (`git show` / `git grep <rev>`; no pytest —
static-decidable, every conclusion rests on byte comparisons).
`ITEM_BASELINE=3d181e5a…` verified resolvable (`git cat-file -t` =
commit). HEAD `24e6b4d3` at start and at finish — unmoved, so every
fingerprint and census below rests on one HEAD.

Boundary note: the capped read overshot 9 lines into W1's record
(1462–1470: header, scope boilerplate, baseline, HEAD line — no stale
set, hash, hunk, or disposition). Independence is shown, not claimed:
the Phase-A instruments below were derived separately (different
enumeration domain, entry-span md5 vs W1's window md5, own grep
patterns) and agree to the digit.

### Phase-A record (as recorded pre-read; full text in the scope file)

Stale set derived independently: exactly TWO files —
`utils/policies.py` (`860b181f…` →
`8c881c0a165dc31022051dd628d6e36d99d44eca`), GLOSSARY (`bc51debc…` →
`d3ef357c26ede6a5bd21d4290b394ade4eb987b4`). The other 18 git rows
MATCH and the installed upstream file re-hashes `fa2a5bef…`; old pins
exact in all 21 rows. Mechanical enumeration over lines 1–1461 yields
27 distinct 40-hex values = 21 current fingerprint values (20 git + 1
installed) + 3 superseded pins + 2 HEAD ids + 1 baseline id — the live
table is 21 rows, the plan's "22" being the inherited adjudication-1
headline slip (run-2 W2 R-3(a)). Cross-checked against the 37
in-range changed paths: only the two stale paths intersect the
fingerprint set (changed specs are 034/047/048/050, changed tests and
live modules are all unfingerprinted) — no three-not-two recurrence,
verified row by row.

Causing hunks: policies single commit `9350eb8d`, 2 hunks, +12/−2
(module-docstring prose; `resolve_policy` docstring + `return default`
→ `return canonical_policy(…)`); GLOSSARY 5 net-zero swaps
(4×`9350eb8d` at `:24`/`:838`/`:1124`/`:1571` + 1×`44712901` at
`:1555`), all ≥500 lines above the Upstream-patches entry (`:2089`).

Expectations: F1 CONFIRM (entry md5-identical `fc764053…` both revs;
exclusion holds — still exactly 2 `#`-comment mentions, `:152/:164` →
`:162/:174` text-identical, production gate census still exactly 4 at
342/414/122/842); F2 CONFIRM (validators MATCH; live census 3/3/3/2 —
file-wide grep finds a 4th django raise at `:309` inside
`_patched_remove_databases_failures`, outside the `:232–279`
validator; strawberry-suite `match=` 12, `RuntimeError` 13);
R1/L1/L2 CONFIRM by input identity; pending stays empty, defects none.

### Reconciliation (every difference resolved)

- R-1 stale set: NO DISAGREEMENT — same 2 files, same full refreshed
  blobs character-identical.
- R-2 table size: AGREE — both derive 21 live rows independently (W1
  over lines 1–1198, mine over 1–1461; the "22" denominator is the
  known inherited erratum, the 2-file set exact).
- R-3 hunks: AGREE — same commits, same `@@` headers, same +12/−2 and
  net-zero stats, same per-commit attribution.
- R-4 gate cite: AGREE — same 2 comments, same +10 shift, same
  exactly-4 census at identical lines. W1's extras (an
  `APPLY_UPSTREAM_PATCHES` sweep at 0, the `conf.py:411` error-string
  clarification) are endorsed, same substance.
- R-5 GLOSSARY entry: AGREE — byte-identical, unmoved. W1's window
  (`:2085–2115`, md5 `2dabc152…` both heads) re-verified by me;
  my entry-span md5 is the complementary instrument.
- R-6 patch-vocabulary-free delta: W1's 0-count sweep re-run by me
  over added/removed lines → 0. Endorsed.
- R-7 counts: AGREE — 4-module, 11 sites / 4 wordings, pins
  (strawberry 12, cross_web 3, graphql_core 2, base/test_conf 26,
  test_apps 0 — my HEAD counts match W1's both-heads pairs; files
  MATCH so equality holds). My django-`:309` note is W2-only
  supporting detail, consistent with the 11.
- R-8 dispositions: full agreement — F1/F2/R1/L1/L2 all CONFIRM, no
  REVISE, pending empty, defects none, index rows unchanged,
  sharded/PG inapplicable.

### Verification job

- Fingerprint agreement: 21/21 values (18 MATCH git + 2 stale pairs
  + installed), every quoted value byte-identical across both workers.
- Append-only PROVED: `sed '3s/.*/Status: verified/'` + `head -c
  85437` + sha256 = `13ae779fb2b751d87706bdfc3abea3d63fa43d0e9eb9b463effba0b1c5a3c349`, exactly W1's recorded pre-edit size/hash.
  Junction is a clean append (text + blank + header + blank); the
  `Status:` line is the only swap. No third-party hunk in any path
  this item touches (artifact + my scope only; no W1 scope exists,
  consistent with the static-decidable record; run-2
  `dry-adjud-crossweb-w2/` never touched; plan diff in the window is
  Worker-0's, out of item scope).
- AGENTS.md prose on W1's hunks: PASS. Banned-word sweep over lines
  1462–1638 hits only the `(Worker 1)` / `Worker 0` role headers,
  `plan's` scope citations (the mandated dispatch-scope form),
  instrument vocabulary (`basename sweep` — the plan's own term), and
  the `feedback.md` filename in the changed-path list; no `audit`,
  `restored`, `hardening`, `previously`, or `grader` anywhere, and no
  hit is process provenance used as evidence. `path::Symbol` form
  used (`conf.py::upstream_patches_enabled`); `path:NN` refs are
  allowed in per-cycle scratch. No `pragma: no cover`.
- Ruff: N/A — the item diff holds no `.py` (artifact `.md` only, no
  W1 scope, my scope `.md` only), per the brief's "if any `.py`"
  qualifier and the static-decidable precedent.
- `## Pending execution` still empty and still correct; defects still
  none; the 2 open families + 1 rejection + 2 file-local index rows
  STAND.

### Verdict + handoff to Worker 0

Status: verified (set above) — plain `verified`, no
pending-execution qualifier. Zero production edits, zero
`## Owned changes` rows. Scratch custody: my scope
`docs/dry/temp-tests/dry-adjud2-crossweb-w2/` (Phase-A record only)
retained for closeout. One item owed to Worker 0: the plan-table
denominator correction (this item fingerprints 21 rows, not 22 —
the 2-file stale set itself is exact), already recorded by W1 and
seconded here.
