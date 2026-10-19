# DRY review: `django_strawberry_framework/conf.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, rejection
re-checked fresh against its trigger) or a file-local record with its proving
challenge. Zero production edits; zero tracked files changed.

## System trace

Mid-size target (616 lines, 34 top-level statements): the package's settings
boundary. It DEFINES the whole `DJANGO_STRAWBERRY_FRAMEWORK` read contract —
the shape guard (`conf.py::_normalize_user_settings`), the django-backed
live-sync lifecycle (`conf.py::Settings`, its `_LIVE_UNSET` sentinel, the
`conf.py::settings` singleton, `conf.py::reload_settings` plus the
`setting_changed` connect), the attribute-access contract
(`conf.py::Settings.__getattr__`), the upstream-patch gate vocabulary
(`conf.py::upstream_patches_enabled` plus `conf.py::APPLY_UPSTREAM_PATCHES_KEY`
and `conf.py::UPSTREAM_PATCH_DEPENDENCIES`), and nine thin per-key readers
(each `*_KEY` constant plus its `*_setting()` function). It ENFORCES the
patch-gate shapes itself (bool vs mapping, per-dependency opt-out, whole
mapping validated on every read) and the top-level dict shape; every
feature-key DOMAIN validation lives downstream (strategy registry, globalid
validator, body-cap resolver, policy resolvers), by a documented thin-reader
split the consumers' docstrings repeat as projection.

Connected code read for judgment, outside the item:
`django_strawberry_framework/exceptions.py` (full read of
`exceptions.py::_safe_type_name`, the guarded renderer both normalize paths
consume); `django_strawberry_framework/utils/policies.py` (full read of
`utils/policies.py::resolve_policy`, the shared policy ladder both policy
readers feed); `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`
(full read, strategy-side validation); `django_strawberry_framework/types/relay.py::_validated_globalid_setting`
(full read, setting-side validation); `django_strawberry_framework/views.py::_resolved_max_request_body_bytes`
(full read, cap-side validation); `django_strawberry_framework/error_policy.py::resolve_error_policy`
and `django_strawberry_framework/resource_policy.py::resolve_resource_policy`
(full reads, precedence ladders); `django_strawberry_framework/filters/inputs.py`
(HIDE_FLAT_FILTERS consumer lines, truthiness coercion);
`django_strawberry_framework/optimizer/single_parent_fetch.py` (fetch-time
flag read); `django_strawberry_framework/testing/client.py::TestClient`
(endpoint precedence + `__test__` guard); `django_strawberry_framework/types/base.py::_meta_optimizer_hints`
(None-seam corroboration) and `::RELAY_GLOBALID_STRATEGY_KEY` framing use;
`django_strawberry_framework/types/finalizer.py` (once-per-finalization
snapshot); `django_strawberry_framework/registry.py` (snapshot slot);
`django_strawberry_framework/schema.py` (explicit-arg-outranks-setting
ladders); `django_strawberry_framework/apps.py` (dispatch consumer of the
gate vocabulary); the four patch modules at gate level (`apply` gate lines,
gate imports); `tests/base/test_conf.py` (full read, 813 lines, every oracle
row); live-tier rows in `test_transport_api.py`, `test_library_api.py`,
`test_products_api.py`, `test_client_api.py`,
`test_single_parent_fastpath_api.py` (grep-verified pins, bodies spot-read);
`examples/fakeshop/config/settings.py` (`INSTALLED_APPS`, no framework dict —
absence is the default path); `docs/GLOSSARY.md` (RELAY / kill-switch /
request-body-cap entries, prose projections).

Excluded with reason: in-flight spec bodies behind the reader docstrings'
Decision pointers (spec-043 endpoint, spec-046 body cap, spec-031 relay,
spec-048 error policy) — cited as pointers, defaults pinned by oracles
instead, bodies not relied upon; `django_strawberry_framework/keyset.py`
`SECRET_KEY_FALLBACKS` read (Django's own setting, different dict, no shared
vocabulary); optimizer `or {}` reflective-shape reads (the module docstring
names them a separate case with its own contract — corroborated by sweep,
bodies not re-litigated); the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) — never touched, not in this finding's sites;
concurrent dirt (`connection.py`, `tests/test_connection.py`,
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) — left untouched, none in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The nine readers were compared against
every sibling flavor surface: filters, orders, mutations, forms,
rest_framework carry no settings vocabulary of their own — each consumes
exactly one named reader by import (`filters/inputs.py` imports
`hide_flat_filters_setting`; `optimizer/nested_fetch.py` imports
`nested_connection_strategy_setting`; `optimizer/single_parent_fetch.py`
imports `single_parent_fast_path_setting`; `testing/client.py` imports
`testing_endpoint_setting`; `types/relay.py` imports
`relay_globalid_strategy_setting`; `views.py` imports
`max_request_body_bytes_setting`; `resource_policy.py` /
`error_policy.py` import their readers). Probe-verified: `from .conf
import` / `from ..conf import` / root-form imports occur in exactly those
consumer modules plus the four patch modules (gate), 16 hits total, no
flavor spells a key string or a default inline. The two policy readers both
feed the one `utils/policies.py::resolve_policy` driver (already shared —
nothing to consolidate here). The `RELAY_GLOBALID_STRATEGY_KEY` constant is
imported by `types/base.py` for error framing only (consumer, listed never
counted). No second definition of any key, default, or gate exists outside
this file.

**2. Sync/async twins.** Target has no async surface (AST: zero
`AsyncFunctionDef`, zero `Await`, probe §3). `Settings` is sync by Django
contract (`setting_changed` is test-only signal machinery; the docstring
states the single-threaded convention). No reader has an async twin; the
async test client resolves its endpoint through the same sync
`testing_endpoint_setting()` at construction. Axis discharged by absence.

**3. Derived rather than repeated knowledge.** Each default is spelled once
in production (probe §6: eight thin readers, one `getattr` line each with
the expected default; the patch gate defaults `True` once at
`conf.py::upstream_patches_enabled`). Every other spelling is a consumer,
oracle, or projection, listed never counted: downstream docstrings restating
their own default (`views.py` deliberately does NOT restate 1 MiB —
"this module never restates that number"); the `test_conf.py` direct spells
(`"windowed"`, `"/graphql/"`, `1_048_576`, …) as independent oracles; the
delattr-enumeration test spelling all ten keys as the live-sync census;
GLOSSARY entries. The `__all__`-style mirror hazard does not apply (no
manifest tuple here). `type(value) is dict` fast-path identity vs
`dict(value)` copy is one body, not a restated fact. No reconstructed copy
found.

**4. Inverse / round-trip pairs.** The write side (all four
`_normalize_user_settings` call sites: `Settings.__init__`,
`Settings.user_settings`, `Settings.reload`,
`Settings._reload_from_django`) and the read side (`user_settings`
identity fast-path, `__getattr__`, the nine readers) share the one
`conf.py::_normalize_user_settings` contract — one grammar, N halves, all
in this file, all composing the same function by name. `reload(mapping)`
vs `_reload_from_django(value)` is the deliberate backed/unbacked pair
(one drops backing, one keeps it; docstrings record the split; oracles pin
both). No second normalize body exists anywhere (package-wide sweep for
`must be a mapping or None` finds only this module's raises plus oracle
match strings). The signal `reload_settings` has no uninstall twin (same
shape as the patch lifecycle's revert-by-identity oracles, not a second
definition).

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target); oracles that compose by name —
`tests/base/test_conf.py` (invalid-attr, lazy-load, preset, falsy-None,
reload × 5, dispatch-uid, uninitialized, racy-normalize, the full
per-dependency parametrized gate suite, liar/hostile containment rows, the
delattr census over all ten keys, the reader default/override table, the
silent-bad-replacement resync row, the explicit-instance row) plus the
live-tier rows (`test_transport_api.py` body-cap rows 16/17, non-mapping
GET row, None-serves row, patch opt-out rows; `test_library_api.py`
HIDE_FLAT rows; `test_products_api.py` relay row; `test_client_api.py`
endpoint-typo row; `test_single_parent_fastpath_api.py` flag-off row);
projections (module/class/function docstrings, GLOSSARY kill-switch /
relay / body-cap entries, spec Decision pointers). Every oracle spells
literals directly and drives behavior through the public readers; none
reads the owner's internals to enumerate (the delattr census spells each
key as an independent expectation — it would fail, not follow, a renamed
key). Spec "three appliers"-style staleness does not occur here (no spec
body relied upon).

**6. Enforcement by omission.** Five deliberate omissions, each with a
contract source and a pinning oracle: (a) thin readers validate nothing —
domain checks live downstream (`resolve_strategy`, `_validated_globalid_setting`,
`_resolved_max_request_body_bytes`, `resolve_resource_policy` /
`resolve_error_policy`; each reader docstring records the split; downstream
rejection rows pin it); adding validation here would double-own the
vocabulary. (b) `single_parent_fast_path_setting` and
`testing_endpoint_setting` coerce nothing — the former passes values
through for truthiness (oracle pins `0` / `"yes"` verbatim), the latter
hands the value to `Client.post` unchanged (oracle pins the typo surfacing
as Django's `ValueError`); the `hide_flat_filters_setting` truthiness
coercion lives at the consumer (`bool(...)` in `filters/inputs.py`, whose
comment says the reader stays thin). (c) `RESOURCE_POLICY` /
`ERROR_POLICY` absent means package defaults with no disable spelling
(reader docstrings + `resolve_policy` `None`-means-default arm). (d) no
`None`-as-value acceptance for `APPLY_UPSTREAM_PATCHES` (explicit `None`
is rejected, oracle-pinned — unlike the top-level `None`-means-empty
stance). (e) no async reader twin (axis 2). No member lacks a guard its
contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **34 top-level statements** — plus, better than the minimum,
every `Settings` body member (6). Every member lands below; every challenge
in `### Challenges` ends in a family row or a file-local record.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (settings-dict contract + None stance + `or {}` history + reflective-shape separation) | (none) | projection, R1 |
| 2 | `from collections.abc import Callable, Mapping` | `Callable`, `Mapping` | machinery for R1, F1 |
| 3 | `from typing import Any` | `Any` | machinery |
| 4 | `from django.conf import settings as django_settings` | `django_settings` | machinery for R2 |
| 5 | `from django.test.signals import setting_changed` | `setting_changed` | machinery for R4 |
| 6 | `from ...exceptions import ConfigurationError, _safe_type_name` | guard + renderer | machinery for R1, R3, F1 |
| 7 | `DJANGO_SETTINGS_KEY = "DJANGO_STRAWBERRY_FRAMEWORK"` | settings-dict name | R2, file-local |
| 8 | `_DISPATCH_UID = "…conf.reload_settings"` | signal identity | R4, file-local |
| 9 | `APPLY_UPSTREAM_PATCHES_KEY = "APPLY_UPSTREAM_PATCHES"` | gate key | R5, F1 |
| 10 | `UPSTREAM_PATCH_DEPENDENCIES = frozenset({…4…})` | gate vocabulary | R5, F1 |
| 11 | `NESTED_CONNECTION_STRATEGY_KEY = "…"` | key source | R6, file-local |
| 12 | `SINGLE_PARENT_FAST_PATH_KEY = "…"` | key source | R7, file-local |
| 13 | `TESTING_ENDPOINT_KEY = "…"` | key source | R8, file-local |
| 14 | `HIDE_FLAT_FILTERS_KEY = "…"` | key source | R9, file-local |
| 15 | `RELAY_GLOBALID_STRATEGY_KEY = "…"` | key source (+ framing consumer in `types/base.py`) | R10, file-local |
| 16 | `MAX_REQUEST_BODY_BYTES_KEY = "…"` | key source | R11, file-local |
| 17 | `RESOURCE_POLICY_KEY = "RESOURCE_POLICY"` | key source | R12, file-local |
| 18 | `ERROR_POLICY_KEY = "ERROR_POLICY"` | key source | R13, file-local |
| 19 | `_LIVE_UNSET: Any = object()` | unbounded-yet sentinel | R2, file-local |
| 20 | `def _normalize_user_settings(value)` | shape contract | R1, file-local |
| 21 | `class Settings` | accessor lifecycle | R2/R3 |
| 21.1 | class docstring | (none) | projection, R2 |
| 21.2 | `def __init__(self, user_settings=None)` | backed vs fixed | R2, file-local |
| 21.3 | `def user_settings` (`@property`) | lazy load + live-sync | R2, file-local |
| 21.4 | `def reload(self, value)` | direct replacement, drops backing | R2, file-local |
| 21.5 | `def _reload_from_django(self, value)` | signal replacement, keeps backing | R2, file-local |
| 21.6 | `def __getattr__(self, name)` | attr contract | R3, file-local |
| 22 | `settings = Settings(None)` | singleton | R2, file-local |
| 23 | `def upstream_patches_enabled(dependency)` | patch gate | R5, F1 |
| 24 | `def nested_connection_strategy_setting()` | thin reader, default `"windowed"` | R6, file-local |
| 25 | `def single_parent_fast_path_setting()` | thin reader, default `True` | R7, file-local |
| 26 | `def testing_endpoint_setting()` | thin reader, default `"/graphql/"` | R8, file-local |
| 27 | `testing_endpoint_setting.__test__ = False` | collection guard | R14, rejection |
| 28 | `def hide_flat_filters_setting()` | thin reader, default `False` | R9, file-local |
| 29 | `def relay_globalid_strategy_setting()` | thin reader, default `None` | R10, file-local |
| 30 | `def max_request_body_bytes_setting()` | thin reader, default `1_048_576` | R11, file-local |
| 31 | `def resource_policy_setting()` | thin reader, default `None` | R12, file-local |
| 32 | `def error_policy_setting()` | thin reader, default `None` | R13, file-local |
| 33 | `def reload_settings(setting, value, **kwargs)` | signal receiver | R4, file-local |
| 34 | `setting_changed.connect(reload_settings, dispatch_uid=…)` | import-time wiring | R4, file-local |

Rules: R1 top-level shape normalization + None stance; R2 django-backed
live-sync lifecycle; R3 attribute-access contract; R4 signal wiring;
R5 upstream-patch gate vocabulary (the conf side of the install
lifecycle); R6–R13 the eight feature thin readers; R14 pytest collection
guard. The plan's `## Responsibility index` already carries
`upstream-patch-install-lifecycle` (rejected) covering R5 and this target —
reused, not renamed. No other existing family owns a definition here (the
policy-ladder sharing lives at `utils/policies.py::resolve_policy`, which
this target only feeds). No new family is named: R1–R4 and R6–R13 each
count 1 with no second definition site (challenges below); R14 and the two
hardening shapes considered are rejections with contract differences +
triggers recorded in the findings.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 None stance | tighten `None` to raise | **1** (`_normalize_user_settings` `None` arm; the `types/base.py::_meta_optimizer_hints` seam is the documented twin with its own reason — listed, and the tightening is deferred by the recorded contract) | independent |
| C2 | R1 fail-loud | accept a new mapping shape (e.g. list of pairs) | **1** (the `Mapping` check + copy arms here; oracles move, not definitions) | independent |
| C3 | R1 hostile shape | new hostile descriptor (`__class__` boom, `__iter__` boom, metaclass `__name__` boom, `dict`-subclass `__getitem__` boom) | **1** (this body; `exceptions.py::_safe_type_name` is the consumed renderer, unchanged) | independent |
| C4 | R2 silent mutation | Django deletes/replaces the key without a signal (pytest-django `del`) | **1** (`Settings.user_settings` live-`is` re-check; the delattr census oracle moves as consumer) | independent |
| C5 | R2 backing split | explicit `Settings(mapping)` must follow live Django after all | **1** (the `_django_backed` flag + three write sites here; the explicit-instance oracle moves) | independent |
| C6 | R2 poisoned cache | rejected live shape must not bind as a good cache key | **1** (normalize-BEFORE-bind order in `user_settings`; the resync-fails-loud oracle moves) | independent |
| C7 | R3 missing key | rename the `Invalid setting` message | **1** (`__getattr__` raise; the invalid-attr oracle moves) | independent |
| C8 | R3 introspection | new dunder probe to short-circuit | **1** (the dunder guard set here; the dunder oracle moves) | independent |
| C9 | R3 malformed live dict | read any attribute while live value is non-mapping | **1** at R1 (normalize raises; R3 propagates by the recorded `except ConfigurationError: raise` arm — propagation, not a second definition) | independent |
| C10 | R4 routing | our key renamed | **1** (the `setting == DJANGO_SETTINGS_KEY` branch + the constant; the refresh oracle moves) | independent |
| C11 | R4 idempotence | module re-imported under a second name | **1** maintenance point (the `dispatch_uid` connect line; the dispatch-uid oracle moves) | independent |
| C12 | R4 rebind | `reload_settings` rebinds the global instead of mutating | **1** (the receiver body; the already-imported-reference oracle moves) | independent |
| C13 | R5 global toggle | change the absent-key default | **1** (`getattr(settings, APPLY_UPSTREAM_PATCHES_KEY, True)` line; the four defaults-true oracles move) | independent |
| C14 | R5 per-dep opt-out | add a fifth dependency name | **1** here (the frozenset + its docstring rule) plus one lifecycle per new module as consumer follow (the recorded trigger's arrival shape, not a count owed today) | independent (see F1) |
| C15 | R5 hostile/typo shapes | unknown name, non-bool value, non-string key, non-bool-non-mapping top, unknown `dependency` arg, liar-`bool`, hostile `__iter__`/`isinstance` | **1** (the one validating body; the hostile/typo oracles move) | independent |
| C16 | R5 retirement | upstream fixes one patch | **1** lifecycle point per module (that module deletes; the gate's vocabulary drops its name here as consumer follow) | independent (see F1) |
| C17 | R6 nested default | default `"windowed"` → `"eager"` | **1** (the reader's default; `resolve_strategy` + oracles follow) | file-local |
| C18 | R6 nested rename | key renamed | **1** (constant + reader: one rule in two statements, same file; consumer import unchanged by name) | file-local |
| C19 | R7 fast-path default | default `True` → `False` | **1** (the reader; the fetch-time consumer + flag-off live row follow) | file-local |
| C20 | R7 fast-path rename | key renamed | **1** (constant + reader, same file) | file-local |
| C21 | R8 endpoint default | default `"/graphql/"` → slash-less | **1** (the reader; `TestClient` construction + typo oracle follow; graphene's spelling is a documented non-borrow) | file-local |
| C22 | R8 endpoint rename | key renamed | **1** (constant + reader, same file) | file-local |
| C23 | R9 hide-flat default | default `False` → `True` | **1** (the reader; the consumer `bool()` + live shape rows follow) | file-local |
| C24 | R9 hide-flat rename | key renamed | **1** (constant + reader, same file) | file-local |
| C25 | R10 relay default | schema-wide default `None` → `"type"` | **1** (the reader; finalizer snapshot + relay live row follow) | file-local |
| C26 | R10 relay rename | key renamed | **1** here (constant + reader; the `types/base.py` framing import is the consumer spelling, follows by name) | file-local |
| C27 | R11 body-cap default | default `1_048_576` → another bound | **1** (the reader; the resolver + transport rows follow; `views.py` restates no number) | file-local |
| C28 | R11 body-cap rename | key renamed | **1** (constant + reader, same file) | file-local |
| C29 | R12 resource rename | key renamed / absent-meaning changed | **1** (constant + reader; `resolve_resource_policy` ladder follows) | file-local |
| C30 | R13 error rename | key renamed / absent-meaning changed | **1** (constant + reader; `resolve_error_policy` ladder follows) | file-local |
| C31 | R6–R13 mechanism | single `_read_setting(key, default)` driver for all nine readers | **0** moves — refused (each reader's NAME is the importable contract with its own lifetime/validation split in its docstring; the shared token is Python `getattr` idiom, not a package rule — see file-local records) | refused |
| C32 | R14 function guard | rename `testing_endpoint_setting` off the `test*` pattern | **1** (the guard line deletes with the rename; the self-proving oracle moves) | independent |
| C33 | R14 class guard | rename `TestClient` off the `Test*` pattern | **0** here (owned at `testing/client.py::TestClient`; this site does not move) | refused-as-shared (see R14) |
| C34 | R2/R4 sentinel | drop `_LIVE_UNSET` for `None` | **0** moves — refused (`None` is a valid live value meaning "no settings"; the sentinel's distinctness is the contract, pinned by the reload-`None` rows) | refused |
| C35 | R1 prose | unify the two `None` seams into one helper | **0** moves — refused (top-level settings-dict seam vs per-`Meta` seam: different populations, different owners; the docstring records the non-unification, see R1) | refused |

**Experiment.** Read-only probe (no source mutation, no SQL, no Django
setup, no shared-tree pytest — the workspace recipe is for mutating proofs,
of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-conf/probe_w1.py
```

Output (`ALL OK`, 16 sections): 34-member module AST with kinds (probe
§§1–2); zero async nodes (§3); all ten KEY constants present (§4); all
nine reader defs present (§5); eight thin readers each one `getattr` line
with the expected default (§6); population 117 `.py` files (§7); gate call
sites exactly the four `apply()` gates with gate imports exactly the four
patch modules (§§8–9); `__test__` guards exactly the two known sites
(§10); `_normalize` one def + four in-file call sites, sentinel /
singleton / signal-connect single-sited (§§11–12); `Settings` six members
(§§13–14); item-baseline diff empty (§15); target blob `c6ad46aa…` (§16).
Two first-draft checks failed on probe precision (scratchpad parent-depth
index; `ast.unparse` rendering `'windowed'` single-quoted and `1_048_576`
un-under-scored) and were corrected to compare the parsed bodies — both
re-verified green, substance unaffected. Status:
`execution-verified` for every identity/count/shape/absence claim below.
Rejects the wrong results "a fifth gate callsite exists", "a key is
spelled twice in production", "a thin reader validates", "an async twin
exists", "the target drifted from its baseline".

## Findings

No production edit is owed by a file item; the one family below is REUSED
from the plan (rejection re-checked fresh), the rest are file-local records
and two recorded rejections.

### F1 — upstream-patch install lifecycle (existing family `upstream-patch-install-lifecycle`, status stays `rejected`)

- **Contract + variation.** The per-dependency install shape — gate by
dependency name, fail loud on drift, install idempotently, self-heal a
third-party revert — repeated as a skeleton in four modules with
per-module validation depth and install arity. This target holds the gate
vocabulary side: the key, the four-name set, and the bool-vs-mapping read
rule with whole-mapping validation. Legitimate variation axes: global vs
per-dependency spelling, member names, per-entry value vocabulary.
- **Sites + roles.** *Definitions*: the four patch modules' install
triples (owned by the sibling artifacts) plus, for the vocabulary, this
target's `conf.py::upstream_patches_enabled`,
`conf.py::APPLY_UPSTREAM_PATCHES_KEY`,
`conf.py::UPSTREAM_PATCH_DEPENDENCIES`. *Consumers* (compose by name):
each `apply()` gate (`if not upstream_patches_enabled("…")`),
`apps.py::DjangoStrawberryFrameworkConfig.ready` (dispatch, gateless by
contract). *Oracles*: the per-dependency parametrized gate suite,
typo/non-bool/non-string/non-mapping/liar-hint/hostile-`__iter__` rows,
the unknown-dependency `ValueError` row, the delattr census row, each
module's lifecycle rows, the live transport opt-out rows. *Projections*:
the reader docstring (full shape contract), each patch module's kill-switch
paragraph, the GLOSSARY kill-switch entry.
- **Challenges.** C13, C14, C15 → 1 each; C16 → the trigger's arrival
shape; C10/C11 show the key itself is single-owned here.
- **Trigger re-checked fresh (not inherited).** The recorded trigger is "a
sequence-level change needed in two or more patch modules, or a fifth
patch module arriving with an identical install shape". Measured today:
package still 117 `.py` files (probe §7); still exactly four gate
callsites in the same four modules with the same four gate imports (probe
§§8–9); `UPSTREAM_PATCH_DEPENDENCIES` still the same four names (full
read); all four `apply()` bodies re-read at gate level — still
gate→validate→check→install with no logging, locking, or ordering
additions. No fifth module, no sequence change: the rejection stands on
fresh evidence.
- **REJECTED shared forms (unchanged, plus one considered here).**
(a) One driver owning the gate→validate→check→install sequence (prior
rejection, stands for the recorded reasons). (b) Considered here: routing
the patch mapping through `utils/policies.py::resolve_policy` (or
extracting the defensive-copy + key-guard-first + unknown-naming steps
into one helper shared with it). Contract differences: the patch gate
validates per-entry BOOLEANS against a fixed four-name vocabulary with a
default-`True` open world, while the policy ladder validates bound/option
names against dataclass fields with domain validation in `__post_init__`
plus instance canonicalization — a shared driver would own the mechanism
but pin neither vocabulary, and a change to either trigger (C15 vs a new
policy bound) moves exactly one body. The cross-citations are precedent
pointers (`policies.py` cites this function twice; this function cites
the `types/base.py` key-guard precedent), not ownership claims.
Reconsideration trigger: a third mapping-gate arriving with the identical
copy-first + key-guard-first + unknown-naming + per-value-check shape —
then the hardening steps (not the vocabularies) become the shared rule.
Durable home: plan's rejected index row + this finding + the existing
precedent comments at both owners.
- **Owner + lifetime.** No new owner (rejected — vocabulary stays here;
install bodies stay per module). No stored derivation in this target
beyond the `user_settings` cache owned by R2; the defensive `dict()`
copies are call-local ("not cached" by construction).
- **Migration.** None (zero-edit item; rejection, not consolidation).
- **Distinct behavior.** C16 retires one member without moving the others;
C15's whole-mapping validation means a typo fails at the first gate read
regardless of which patch reads first.
- **Behavioral proof.** `execution-verified` for vocabulary population +
gate-callsite census + import census (probe §§8–10).
`static-reviewed` for per-module depth differences (four gate bodies read;
full bodies in the sibling artifacts) and oracle bodies (not run; no
shared-tree pytest per item rules). Rejects "a fifth gate site exists".
- **Structural gate.** The existing gate-shape oracles (whole-mapping
typo row raising on the correctly-spelled read; empty-mapping row;
per-dependency opt-out row; unknown-argument `ValueError` row). Negative
control (by construction, stated honestly): renaming a dependency in the
frozenset without touching its `apply()` call fails the unknown-argument
row deterministically; a shared driver would pass every current
behavioral oracle, so the rejection rests on vocabulary/retirement
contracts with the trigger above, not on a behavioral gate.
- **Coupling.** None.
- **Freshness.**
`django_strawberry_framework/conf.py`
`c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`,
`django_strawberry_framework/_django_patches.py`
`ba98f5859ec32971c3aa566c221bdc4db392e137`,
`django_strawberry_framework/_strawberry_patches.py`
`f77df3499eb96051d70055266a677ca3cde5b219`,
`django_strawberry_framework/_cross_web_patches.py`
`6b3a7c35ed0c4f0d61f588fa816af37bf2e26aaf`,
`django_strawberry_framework/_graphql_core_patches.py`
`1cd579fb9f9c6f9994e0e2f0312dd3afb91c14a5`,
`django_strawberry_framework/apps.py`
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f`,
`tests/base/test_conf.py`
`f35c70742354d0ab123b163a92c6a8a503c6ea29`,
`django_strawberry_framework/utils/policies.py`
`860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e`
(precedent-cited, body excluded from this finding's sites beyond the
cited lines),
`examples/fakeshop/test_query/test_transport_api.py`
`17320f1ff335a868d5ed324a49f1d7c4ee899cfc` (live opt-out rows).

### File-local records (no second definition after the matrix)

- **R1 — top-level shape normalization + None stance.**
`conf.py::_normalize_user_settings` (C1, C2, C3 → 1 each). The four
in-file call sites (`Settings.__init__`, `Settings.user_settings`,
`Settings.reload`, `Settings._reload_from_django`) are consumers of the
one body, not copies — a change to any arm moves the one function. The
`exceptions.py::_safe_type_name` renderer is consumed, not defined, here
(C3). The module-docstring None stance (two seams: this module +
`types/base.py::_meta_optimizer_hints`, corroborated by read; the old
`or {}` collapse vs fail-loud history; the reflective-shape separation,
corroborated by the optimizer `or {}` sweep) is projection with no second
definition — C35's unification refused at the docstring that already
records the non-unification. Trigger: a second top-level
settings-dict shape guard the package must keep in sync would make it a
family. Freshness: target + `exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` +
`types/base.py`
`91c587477ff8257e80dbb9a9c79859f34c5b4c7e` (None-seam lines only) +
`tests/base/test_conf.py` as in F1.
- **R2 — django-backed live-sync lifecycle.** `DJANGO_SETTINGS_KEY`,
`_LIVE_UNSET`, `Settings.__init__` / `user_settings` / `reload` /
`_reload_from_django`, the `settings` singleton (C4, C5, C6, C34 → 1
each; C34 refused with the distinctness contract pinned by the
reload-`None` rows). The `is`-identity fast-path preserves dict identity
for in-place mutation; normalize-before-bind keeps a rejected live shape
retrying loud instead of caching stale. `Settings(mapping)` explicit
instances are a different backing state of the same object, not a second
lifecycle. Trigger: a second django-backed settings holder would make it
a family. Freshness: target + `tests/base/test_conf.py` as in F1.
- **R3 — attribute-access contract.** `Settings.__getattr__` (C7, C8 →
1 each; C9 → 1 at R1, propagation here). Dunder short-circuit, `Invalid
setting` `AttributeError`, `ConfigurationError`/`AttributeError`
pass-through before the generic containment — order pinned by the
racy-normalize and hostile-lookup rows. No second attribute-access rule
exists for this dict. Trigger: a second accessor over the same cache
would make it a family. Freshness: target + `tests/base/test_conf.py`
as in F1.
- **R4 — signal wiring.** `_DISPATCH_UID`, `reload_settings`,
`setting_changed.connect(…)` (C10, C11, C12 → 1 each). Mutate-in-place
(not rebind), unrelated keys ignored, `**kwargs` absorbing the signal
payload, idempotent connect — each pinned by its oracle row. The
`AppConfig.ready()` dispatch is the adjacent opposite decision (ready
time, not import time) with its own contract, not a second site of this
rule. Trigger: a second signal receiver mutating the same singleton
would make it a family. Freshness: target + `apps.py` `8ae1a3a3…` (as
excluded neighbor) + `tests/base/test_conf.py` as in F1.
- **R6 — nested-connection strategy key.** `NESTED_CONNECTION_STRATEGY_KEY`
+ `nested_connection_strategy_setting` (C17, C18 → 1 each). Thin: no
validation here; unknown names fail in `resolve_strategy` where the
registry lives (consumer docstring + rejection row pin it). Trigger: a
second spelling of this key/default the package must keep in sync would
make it a family. Freshness: target +
`optimizer/nested_fetch.py`
`4d8d37a7f52cf94d2916f17db3a8a21393e28d57` (consumer lines) +
`tests/base/test_conf.py` as in F1.
- **R7 — single-parent fast-path flag.** `SINGLE_PARENT_FAST_PATH_KEY` +
`single_parent_fast_path_setting` (C19, C20 → 1 each). Pure unvalidated
toggle read at fetch time (plan-cache invisible); non-bools pass through
for truthiness (oracle pins `0` / `"yes"` verbatim). Trigger as R6.
Freshness: target +
`optimizer/single_parent_fetch.py`
`e995270af9b213b7f931c03d7dc8f7c084819e1b` +
`tests/base/test_conf.py` as in F1 +
`test_single_parent_fastpath_api.py`
`492fac736277abd13af0a4eceb36c4ec08ed519b` (flag-off live row).
- **R8 — testing endpoint.** `TESTING_ENDPOINT_KEY` +
`testing_endpoint_setting` (C21, C22 → 1 each). Unvalidated hand-off to
`Client.post` (typo surfaces as Django's `ValueError`; oracle pins it).
Trigger as R6. Freshness: target +
`testing/client.py`
`91d61442339b1baac232e7df9bff5b9a70cd4a60` +
`testing/__init__.py`
`48b45d1b433283c40bf8d602d71a26d261a833b2` +
`tests/base/test_conf.py` as in F1 +
`test_client_api.py`
`aecd36efd42e00635d61fd2cdc20ee967070a525` (typo live row).
- **R9 — hide-flat-filters key.** `HIDE_FLAT_FILTERS_KEY` +
`hide_flat_filters_setting` (C23, C24 → 1 each). Truthiness coercion
owned by the consumer (`bool(…)` in `filters/inputs.py`, whose comment
says the reader stays thin). Trigger as R6. Freshness: target +
`filters/inputs.py`
`82b52d97b8f8b26d2846df24dabcabb793507c87` +
`tests/base/test_conf.py` as in F1 +
`test_library_api.py`
`fd00388bdac5c0b1c84d1139ca07fc53f8bc973b` (shape live rows).
- **R10 — relay globalid strategy key.** `RELAY_GLOBALID_STRATEGY_KEY` +
`relay_globalid_strategy_setting` (C25, C26 → 1 each). Thin: validated
once per finalization through the shared Meta-path validator
(`types/relay.py::_validated_globalid_setting`; finalizer snapshot).
The `types/base.py` framing import is a consumer spelling. Trigger as
R6. Freshness: target + `types/relay.py`
`5243986223547af7bcab691032e1d6792655fd9d` +
`types/base.py` `91c58747…` (framing lines) +
`types/finalizer.py`
`77fd9a2dd229eb9de5f29188c5058035d3606323` +
`registry.py`
`9cc8bb553fd417fc465809a541769a8383469cda` +
`tests/base/test_conf.py` as in F1 +
`test_products_api.py`
`8f415dd168b4e13ee5d4d94a5493f61057c389c8` (relay live row).
- **R11 — request-body cap key.** `MAX_REQUEST_BODY_BYTES_KEY` +
`max_request_body_bytes_setting` (C27, C28 → 1 each). Thin: `None`
disables, `0` rejected, positivity + exact-`int` owned by
`views.py::_resolved_max_request_body_bytes` (which restates no number).
Trigger as R6. Freshness: target + `views.py`
`9f85b0df26a17e800ec392aa13f6848e07633895` +
`tests/base/test_conf.py` as in F1 +
`test_transport_api.py` `17320f1f…` (cap rows 16/17).
- **R12 — resource-policy key.** `RESOURCE_POLICY_KEY` +
`resource_policy_setting` (C29 → 1). Thin: absent means package
defaults with no disable spelling; shape + domain owned by
`resolve_resource_policy` via the shared `resolve_policy` driver (which
already consolidates the two policy ladders — nothing owed here). The
`DjangoSchema(resource_policy=…)` argument outranks the setting
(`schema.py` ladder). Trigger as R6. Freshness: target +
`resource_policy.py`
`9205124f41814dbda5a7df0a4882e10b5f951b2f` +
`utils/policies.py` `860b181f…` (driver, consumer side) +
`schema.py`
`eb767f01a4916b9bdce315255cd3a9b5fa0a1b24` +
`tests/base/test_conf.py` as in F1 +
`test_resource_policy_api.py`
`47c86d288e8125880656a85f5878f2db3e882d7a` (kwarg-path live rows).
- **R13 — error-policy key.** `ERROR_POLICY_KEY` +
`error_policy_setting` (C30 → 1). Same thin split as R12 via
`resolve_error_policy`; opt-out is spelled `{"enabled": False}` (a
recorded decision, never an omission). Trigger as R6. Freshness:
target + `error_policy.py`
`fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91` +
`utils/policies.py` + `schema.py` as in R12 +
`tests/base/test_conf.py` as in F1 +
`test_error_policy_api.py`
`5dbcf2013f98b10567b0dc8efddd9705141fa6c7` (kwarg-path live rows).
- **R14 — pytest collection guard (rejection, not a family).**
`testing_endpoint_setting.__test__ = False` (C32 → 1 here; C33 → 0
here). The second site (`testing/client.py::TestClient.__test__ =
False`) is a different contract in the same hazard class: a `test*`
FUNCTION returning `str` (trips `PytestReturnNotNoneWarning` under
`filterwarnings = error`) vs a `Test*` CLASS (collected as a suite).
A shared driver is impossible — the attribute must live on the very
object pytest would collect — and a shared comment would couple two
unrelated renames. Considered shared form (one guard helper owning
both): refused. Contract differences: different pytest patterns
(`test*` vs `Test*`), different failure modes (return-warning vs
suite-collect), independent retirement (C32 deletes here alone; C33
moves only the client). Reconsideration trigger: a lint or fixture
that owns the `test*`/`Test*` vocabulary package-wide (then both
attributes become consumers of it). Durable home: the conf comment
already records "Same hazard class (and same idiom) as
`testing/client.py::TestClient`'s class-level guard" — that clause is
the rejection record; this finding points at it. Freshness: target +
`testing/client.py` `91d61442…`.

### C31 — thin-reader mechanism (refused shared form, recorded here)

Nine readers sharing the `getattr(settings, KEY, default)` token look
like nine copies of one read rule. They are nine rules sharing Python
idiom: posit changing one default (C17/C19/C21/C23/C25/C27) or one key
name (C18/C20/C22/C24/C26/C28/C29/C30) → exactly one reader moves, its
consumers and oracles following as listed-never-counted. Posit changing
the lookup mechanism itself → that change has no rule behind it today
(no caching, no fallback chain, no second access path); a
`_read_setting(key, default)` driver would save nine one-liners while
hiding each reader's importable feature NAME and its per-key
lifetime/validation docstring — the name IS the contract consumers grep
for. Reconsideration trigger: a mechanism change (cache layer, fallback
chain, access-path rename) touching three or more readers at once — then
the mechanism becomes the shared rule with this finding as its seed.
No new index row today.

## Defects

None. Every claim checked while tracing held: all ten key strings
single-sited in production per key (probe §4 + flavor-import sweep — the
only cross-file spellings are the `types/base.py` framing consumer and
oracle/prose restatements); all eight thin defaults match their
documented values (probe §6); thinness claims verified per consumer
(strategy registry, globalid validator, body-cap resolver, policy
resolvers, `bool()` coercion site, `Client.post` hand-off, fetch-time
flag read); the gate's four callsites/imports (probe §§8–9); both
`__test__` sites with distinct contracts; the signal connect once with
the recorded uid; the singleton constructed once with `None`; the
normalize-before-bind order present in the body; the delattr census in
the oracle suite enumerating all ten keys; GLOSSARY kill-switch
(four-applier prose) consistent with the frozenset. Nothing routed to
any owner.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
117-file sweeps, command in `### Challenges`) already ran green against
the shared tree; they mutate no source and open no database, so no
workspace copy was owed and no `__file__`/DB `NAME` record applies. No
pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. No `FAKESHOP_SHARDED`
or Postgres cell is owed: the target's code path reaches no database,
alias, or dialect decision (`inapplicable by construction` — pure
settings-dict reads; the only DB-adjacent knob is a string endpoint
default never resolved here).

## Judgment

Backstop discharged: 34/34 `ast.Module.body` members enumerated plus all
6 `Settings`-body members, 35 challenges run, every rule terminating in
the one existing rejected family it belongs to
(`upstream-patch-install-lifecycle`, trigger re-checked fresh — still
rejected, no new row owed), a file-local record with its proving
challenge (R1–R4, R6–R13), or a recorded rejection with difference +
trigger + owner home (R14, C31, the F1(b) defensive-copy form) — no
consolidation owed, no defect found, no new family named. Zero-edit
result is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: the only
family this target touches is already indexed; the two refused shared
forms live at their owner comments plus this finding.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
e4fa05c73a6789d0f90df730194399f43a05f8bb --
django_strawberry_framework/conf.py` is empty (0 bytes, re-measured
after the probe runs via probe §15); the working blob
`c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25` equals the item baseline, the
cycle-baseline member, and `HEAD:` — the target is clean, so no hunk
attribution was owed. Before touching any path, the item-scoped paths
were verified clean; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt (`connection.py`,
`tests/test_connection.py`, `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied (working `connection.py` `3c4d5dcb…` vs
`HEAD` `93e998f2…` cursor-guard hunks attributed by content as external
and left alone). Dirt elsewhere left alone, not a stop. No commit.
Untracked scratch created (not tracked changes): this artifact
`docs/dry/dry-file-conf.md` and the read-only probe
`docs/dry/temp-tests/dry-file-conf/probe_w1.py` (`ALL OK`, 16 sections;
no source mutation, no DB, no shared-tree pytest). No ruff run owed (no
tracked `.py` edits; artifact is `.md` only; probe is untracked
scratch). No `__file__`/DB record (no workspace copy — no mutating
proof exists).

## Independent verification (Worker 2)

Own trace, recorded before reconciling with `## Findings` (fresh AST +
sweeps, not a re-read of the finding text). Probe:
`docs/dry/temp-tests/dry-file-conf-w2/probe_w2.py` (`W2 ALL OK`, 9
sections; read-only, no Django setup, no DB, no shared-tree pytest).

- **Enumeration (own count).** `ast.Module.body` = **34** top-level
  statements (docstring + 5 imports + 12 constants/sentinel + normalize
  def + `Settings` class + singleton + gate def + 8 thin-reader defs +
  1 `__test__` guard + 1 signal receiver + 1 connect); `Settings` body =
  **6** (docstring + `__init__` + `user_settings` + `reload` +
  `_reload_from_django` + `__getattr__`). Zero `AsyncFunctionDef`, zero
  `Await`. Nine `*_setting`/gate bodies each exactly one `getattr(`
  line. `_normalize_user_settings`: 1 def + 4 in-file call sites
  (`Settings.__init__`, `Settings.user_settings`, `Settings.reload`,
  `Settings._reload_from_django`). Matches the artifact table
  row-for-row.
- **Sites + roles + counts (own).** R1 shape normalization + None
  stance: **1** definition
  (`django_strawberry_framework/conf.py::_normalize_user_settings`);
  the four call sites are consumers; `exceptions.py::_safe_type_name`
  is a consumed renderer. R2 live-sync lifecycle: **1**
  (`django_strawberry_framework/conf.py::Settings` +
  `DJANGO_SETTINGS_KEY` + `_LIVE_UNSET` + `settings` singleton);
  explicit `Settings(mapping)` is a backing state, not a second
  lifecycle. R3 attribute contract: **1**
  (`django_strawberry_framework/conf.py::Settings.__getattr__`).
  R4 signal wiring: **1** (`reload_settings` + `dispatch_uid`
  connect; `apps.py::ready` is the adjacent opposite decision, not a
  second site). R5 gate vocabulary: conf side (`APPLY_UPSTREAM_PATCHES_KEY`
  + `UPSTREAM_PATCH_DEPENDENCIES` +
  `upstream_patches_enabled`) plus the four per-module install triples
  owned by the sibling artifacts; consumers are the four `apply()`
  gates + the `apps.py` dispatch; oracles are the parametrized gate
  suite + typo/liar/hostile rows + delattr census + live opt-out rows.
  R6–R13 eight thin readers: **1** each (constant + reader = one rule
  in two statements, same file); domain validation downstream
  (`resolve_strategy`, `_validated_globalid_setting`,
  `_resolved_max_request_body_bytes`, `resolve_resource_policy` /
  `resolve_error_policy`); the `types/base.py`
  `RELAY_GLOBALID_STRATEGY_KEY` framing import is a consumer spelling.
  R14 collection guard: conf function guard vs
  `testing/client.py::TestClient` class guard are different contracts
  (`test*` function return-warning vs `Test*` class suite-collect);
  the attribute must live on the collected object, so no shared
  driver. C31 `_read_setting(key, default)` driver: refused — each
  reader NAME is the importable contract with its own
  lifetime/validation docstring; no caching/fallback mechanism exists
  to own. F1(b) `resolve_policy` routing: refused — per-entry bools
  over a fixed four-name open world vs dataclass-field closed world
  with `__post_init__` domain validation + canonicalization.
- **Owner I would choose.** Same as the artifact throughout:
  normalize + lifecycle + attr contract + signal wiring + each key in
  `conf.py`; install bodies per patch module (rejected consolidation);
  refused shared forms stay refused. No new family, no new index row.
- **Matrix (own judgment).** (1) Cross-flavor: discharged — every
  sibling flavor consumes exactly one named reader by import; gate
  imports exactly the four patch modules; no second key/default
  definition in production (non-conf hits are strategy-registry
  vocabulary, docstrings, and prose). (2) Sync/async: discharged by
  absence (own zero-count). (3) Derived knowledge: discharged —
  defaults single-spelled; `views.py` restates no number. (4)
  Round-trip: discharged — one grammar, N halves, all composing the
  one normalize body by name; `reload` vs `_reload_from_django` is
  the deliberate backed/unbacked pair. (5) Other media: discharged
  with ONE correction (below) — delattr census + reader default
  table spell literals directly (independent); the parametrized gate
  population does not (see reconciliation). (6) Omission:
  discharged — five deliberate omissions each with contract source +
  pinning oracle (thin-reader non-validation, pass-through
  coercion policy, no-disable policy absence, `None` rejected for
  the patch key, no async twin).
- **Equivalence (principle 8).** Zero-edit item: no behavior to
  preserve across a move. Observable-behavior claims checked by
  inspection of bodies + oracle bodies (static-reviewed): normalize
  arms, normalize-before-bind order, `is`-identity fast-path,
  dunder short-circuit order, mutate-in-place receiver, idempotent
  connect, whole-mapping validation order (copy-first,
  key-guard-first, unknown-naming, per-value check). No
  ordering/transactional/async axis exists on this target beyond the
  documented single-threaded test-signal convention. No execution
  beyond the read-only probe was owed.
- **Zero-edit check (own).** `git diff
  e4fa05c73a6789d0f90df730194399f43a05f8bb --
  django_strawberry_framework/conf.py` = 0 bytes (re-measured by
  Worker 2); working blob `c6ad46aa…` = `HEAD:` blob = artifact
  blob. `git status --short -- django_strawberry_framework/conf.py`
  empty. Coverage + assignment validated (enumeration + challenges
  above); candidates routed (F1 → existing rejected family; R14 /
  C31 / F1(b) → recorded rejections at owner comments + artifact).
  No production edit demanded or made.
- **Fingerprints (all re-hashed by Worker 2, every one matches).**
  `conf.py` `c6ad46aa…`; `_django_patches.py` `ba98f585…`;
  `_strawberry_patches.py` `f77df349…`; `_cross_web_patches.py`
  `6b3a7c35…`; `_graphql_core_patches.py` `1cd579fb…`; `apps.py`
  `8ae1a3a3…`; `tests/base/test_conf.py` `f35c7074…`;
  `utils/policies.py` `860b181f…`; `exceptions.py` `e06b0b7f…`;
  `types/base.py` `91c58747…`; `optimizer/nested_fetch.py`
  `4d8d37a7…`; `optimizer/single_parent_fetch.py` `e995270a…`;
  `testing/client.py` `91d61442…`; `testing/__init__.py`
  `48b45d1b4…`; `filters/inputs.py` `82b52d97…`; `types/relay.py`
  `52439862…`; `types/finalizer.py` `77fd9a2d…`; `registry.py`
  `9cc8bb55…`; `views.py` `9f85b0df…`; `resource_policy.py`
  `9205124f…`; `error_policy.py` `fa94fcd9…`; `schema.py`
  `eb767f01…`; `test_transport_api.py` `17320f1f…`;
  `test_library_api.py` `fd00388b…`; `test_products_api.py`
  `8f415dd1…`; `test_client_api.py` `aecd36ef…`;
  `test_single_parent_fastpath_api.py` `492fac73…`;
  `test_resource_policy_api.py` `47c86d28…`;
  `test_error_policy_api.py` `5dbcf201…`. No finding stale.
- **Gates + negative controls.** Delattr census and reader table
  spell every key/default literally — a rename fails them rather
  than follows (bodies read). Typo / non-bool / non-string /
  non-mapping rows fail loud with the promised `ConfigurationError`
  framings (bodies read). Collection guard is self-proving via the
  unaliased import (static-reviewed; no shared-tree pytest per item
  rules). One misattribution corrected below; every gate still
  fails its divergence.
- **Pending execution.** None — agreed. Probe already ran green
  (read-only, no DB); oracle bodies static-reviewed; target
  reaches no database, alias, or dialect decision (pure
  settings-dict reads; the endpoint default is never resolved
  here), so `FAKESHOP_SHARDED` / Postgres are inapplicable by
  construction with that reason. No workspace copy owed (no
  mutating proof), so no `__file__` / DB `NAME` record applies.
- **Coupling.** None — agreed (zero-edit).
- **AGENTS.md prose.** Item-scoped diff empty: no production/test
  prose to violate, no process provenance, no commit, no ruff owed
  (no tracked `.py` edits; W2 scratch is untracked read-only
  scratch under `docs/dry/temp-tests/dry-file-conf-w2/`).
  Concurrent dirt (`connection.py`, `tests/test_connection.py`,
  `tests/utils/test_querysets.py`,
  `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`)
  untouched. Citations use `path::Symbol` form.

### Reconciliation with `## Findings`

Agreement per family: F1 reuse + stays-rejected (trigger
re-checked fresh on current 117-file / 4-gate / 4-import census —
agreed, own W2-7 confirms); R1/R2/R3/R4 file-local (agreed);
R6–R13 file-local thin readers (agreed, own W2-4 confirms);
R14 rejection (agreed); C31 refusal (agreed); F1(b) refusal
(agreed). Enumeration 34 + 6: agreed member-by-member. Counts:
every `1` claimed re-derived as `1` above; every `0-moves`
refusal re-derived as refused for the same contract reason.
No oracle rewritten in this item (diff empty — holds vacuously).

Difference (one, non-blocking): the artifact states in `### Matrix`
axis 5 and `### F1` sites that no oracle reads the owner's
internals to enumerate. `tests/base/test_conf.py:32`
(`_PATCH_DEPENDENCIES = sorted(conf.UPSTREAM_PATCH_DEPENDENCIES)`)
does: the four parametrized gate tests follow the frozenset
population. Consequences, verified by reading the bodies: (a) a
frozenset rename without touching its `apply()` call still fails
— via the hardcoded `"django"` strings in the opt-out / typo /
  value rows (which would raise `ValueError` instead of the
  expected outcome), not via the "unknown-argument row" the
  artifact names — so the negative control still fails, but the
  attribution is wrong; (b) a fifth frozenset name with no new
  gate callsite would pass freely (new param asserts
  defaults-true trivially; no permanent test pins the exact
  four-population; the probe census is scratch, not a gate).
This predates the item (zero test edits here), so it is not an
item-introduced violation; it is routed as a hardening note to
the holding family `upstream-patch-install-lifecycle` (see
`## Defects (Worker 2)` W2-1), never a file-item production
edit. Verdict unaffected.

## Defects (Worker 2)

- **W2-1 (non-blocking hardening note, routes to Family
  `upstream-patch-install-lifecycle`).** `tests/base/test_conf.py:32`
  parametrizes four gate tests from the owner
  (`sorted(conf.UPSTREAM_PATCH_DEPENDENCIES)`), so the exact
  vocabulary population has no independent permanent pin: adding a
  fifth frozenset name passes without a new gate callsite, and the
  artifact misattributes the rename negative control to the
  unknown-argument row (it fails via the hardcoded-name rows).
  Suggested trigger-carrier for the family item: pin the exact
  four-name population with literals (or assert the gate-callsite
  census as a permanent structural gate with its negative
  control), without weakening the existing hardcoded-name rows.
  Not a production defect; below the AGENTS.md defect bar (no
  contract row reachable by wire/config input breaks today);
  recorded so the family item, not this file item, decides.
  Owner: Family `upstream-patch-install-lifecycle`.
- **W2-2 (artifact accuracy, already reconciled above).** Axis-5 /
  F1 "none reads the owner's internals" overstates by the one
  line in W2-1. Correction recorded in the reconciliation; no
  resubmission demanded (substance — counts, roles, rejection,
  fingerprints, gates-fail — re-derived green).

## Re-pass at 9031cb3d (Worker 1)

Bounded re-pass only; prior reasoning above stands untouched.
Target `conf.py` is byte-identical (`c6ad46aa…` = working = `HEAD:`),
so this re-derives ONLY rows the ff range `f8a75753..9031cb3d`
could touch, then re-hashes every fingerprint and spot-confirms
the rest by identity.

Range in scope: 5 package files changed
(`permissions.py`, `resource_policy.py`, `schema.py`,
`types/resolvers.py`, `utils/querysets.py`; name-status shows
zero added package files) plus test/doc files. Of the artifact's
population, 5 files are stale: the 3 named at dispatch plus 2
more the re-hash found (`test_library_api.py`, `test_products_api.py`).
`permissions.py` / `types/resolvers.py` / `utils/querysets.py` are
referenced by no conf finding (no reader, ladder, gate, or oracle
touches those symbols) — out of population, no row affected.

Method (read-only; no Django setup, no DB, no shared-tree pytest):

```shell
uv run python docs/dry/temp-tests/dry-file-conf/repass_w1_9031.py
```

Result `REPASS ALL OK` (12 sections), plus hunk-level `git diff`
reads of each stale file below. One first-draft probe assertion
failed on precision (frozenset spelled multi-line, not single-line)
and was corrected to match the parsed shape — re-verified green,
substance unaffected.

Per-affected-row verdicts (one line each):

- R12 resource-policy thin reader: CONFIRM file-local, still 1
  (C29) — reader still one `getattr` defaulting `None`; the
  `resource_policy.py` diff is two docstring-only hunks
  (`_windowed_rows`/`bounded_rows` prose, zero `def` changes);
  `resolve_resource_policy` still calls `resolve_policy` with
  `read_setting=resource_policy_setting` and the
  explicit-greater-than-setting-greater-than-default precedence
  prose intact; driver `utils/policies.py` hash-identical.
- R12 schema ladder: CONFIRM outranking still true —
  `DjangoSchema.__init__` still takes
  `resource_policy=... = None` and resolves via
  `resolve_resource_policy(resource_policy if declared_resource
  is None else declared_resource)`; the `schema.py` diff is a
  single docstring hunk (subclass-refusal wording broadened,
  9 insertions / 6 deletions, no logic touched).
- R12 oracles: CONFIRM intact — `test_resource_policy_api.py`
  diff is additive only (module-docstring extension, one import,
  new `CARRY_RELATION_*` schema/views/routes/tests; 19
  `resource_policy=` hits still present, zero existing
  kwarg-path rows touched).
- R6–R13 spot: CONFIRM each still 1 — all eight thin readers
  still exactly one `getattr` line with unchanged defaults
  (probe); downstream validators for R6–R11/R13 all
  hash-identical (`nested_fetch`, `single_parent_fetch`,
  `testing/client`, `filters/inputs`, `types/relay`,
  `finalizer`, `registry`, `types/base`, `views`,
  `error_policy`); the two oracle-file diffs touch no pinned
  row (HIDE_FLAT: 0 diff hits; relay-strategy row outside all
  changed hunks; changed hunks are optimizer-hint prose plus
  new mutation/optimizer tests).
- F1 trigger: CONFIRM reuse, stays rejected — fresh census:
  117 package `.py` files; exactly 4 gate callsites in the same
  4 patch modules; exactly 4 gate imports; `frozenset` still the
  same 4 names; all 4 patch modules + `apps.py`
  hash-identical (no sequence change, no fifth module).
- Rest (R1–R4, R14, C31, F1(b)): SPOT-CONFIRM by identity —
  `conf.py` unchanged so every body is identical, and every
  neighbor those rows cite (`exceptions.py`, `apps.py`,
  `testing/client.py`, `testing/__init__.py`,
  `utils/policies.py`, `tests/base/test_conf.py`) is
  hash-identical; no re-derivation owed.

Fingerprint table old → new (`*` = changed in range):

| File | Old | New |
|---|---|---|
| `conf.py` | `c6ad46aa…` | `c6ad46aa…` |
| `_django_patches.py` | `ba98f585…` | `ba98f585…` |
| `_strawberry_patches.py` | `f77df349…` | `f77df349…` |
| `_cross_web_patches.py` | `6b3a7c35…` | `6b3a7c35…` |
| `_graphql_core_patches.py` | `1cd579fb…` | `1cd579fb…` |
| `apps.py` | `8ae1a3a3…` | `8ae1a3a3…` |
| `tests/base/test_conf.py` | `f35c7074…` | `f35c7074…` |
| `utils/policies.py` | `860b181f…` | `860b181f…` |
| `exceptions.py` | `e06b0b7f…` | `e06b0b7f…` |
| `types/base.py` | `91c58747…` | `91c58747…` |
| `optimizer/nested_fetch.py` | `4d8d37a7…` | `4d8d37a7…` |
| `optimizer/single_parent_fetch.py` | `e995270a…` | `e995270a…` |
| `testing/client.py` | `91d61442…` | `91d61442…` |
| `testing/__init__.py` | `48b45d1b4…` | `48b45d1b4…` |
| `filters/inputs.py` | `82b52d97…` | `82b52d97…` |
| `types/relay.py` | `52439862…` | `52439862…` |
| `types/finalizer.py` | `77fd9a2d…` | `77fd9a2d…` |
| `registry.py` | `9cc8bb55…` | `9cc8bb55…` |
| `views.py` | `9f85b0df…` | `9f85b0df…` |
| `error_policy.py` | `fa94fcd9…` | `fa94fcd9…` |
| `test_transport_api.py` | `17320f1f…` | `17320f1f…` |
| `test_client_api.py` | `aecd36ef…` | `aecd36ef…` |
| `test_single_parent_fastpath_api.py` | `492fac73…` | `492fac73…` |
| `test_error_policy_api.py` | `5dbcf201…` | `5dbcf201…` |
| `resource_policy.py` * | `9205124f…` | `647133d2…` |
| `schema.py` * | `eb767f01…` | `2f727321…` |
| `test_resource_policy_api.py` * | `47c86d28…` | `94d9d079…` |
| `test_library_api.py` * | `fd00388b…` | `ea74fb5d…` |
| `test_products_api.py` * | `8f415dd1…` | `eff4cd80…` |

(Full 40-hex hashes re-measured in this pass; prefixes above
match the artifact's recorded prefixes row-for-row.)

Proof status: `execution-verified` for every re-derived
identity/count/shape/absence claim (new probe green against the
shared tree; mutates nothing, opens no DB, so no workspace copy
and no `__file__`/DB record owed). Oracle bodies
`static-reviewed` (`test_conf.py` identical; live additions
additive, pinned rows untouched). Rejects the wrong results "the
range renamed a key", "the ladder moved", "a fifth gate site
arrived", "a thin reader validates".

Gate re-checks: delattr census, reader default/override table,
typo/non-bool/non-string/non-mapping/liar/hostile rows all live
in `test_conf.py` `f35c7074…` (identical) — every gate still
fails its divergence. W2-1/W2-2 stand as recorded (the
parametrized-from-owner population pin is still absent; still a
family-item hardening note, unchanged by this range).

Defects: none new (no new numbers). Both stale production diffs
are prose-only; both stale oracle diffs are additive plus
docstring rewords on unrelated rows.

Pending execution: none. No `execution-deferred` items; no
`FAKESHOP_SHARDED`/Postgres cell owed (`inapplicable by
construction` — pure settings-dict reads, same reason as prior).

Item-scoped diff state: `git diff
5eccb18a9400b1bc0daf154e36acc853a3c29ae6 --
django_strawberry_framework/conf.py` is empty (0 bytes);
`git status --short -- django_strawberry_framework/conf.py`
empty; working blob = `HEAD:` blob = `c6ad46aa…`. The ledger
paths (`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt
(`connection.py`, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) was never edited, reverted, or tidied.
No production edits. No commit.

Scratch paths: new read-only probe
`docs/dry/temp-tests/dry-file-conf/repass_w1_9031.py`
(`REPASS ALL OK`); prior `probe_w1.py` untouched. No
shared-tree pytest run.

## Independent verification (Worker 2) — re-pass at 9031cb3d

Own bounded trace, recorded before reconciling with `## Re-pass at
9031cb3d (Worker 1)` above. Probe (read-only, no Django setup, no DB,
no shared-tree pytest):

```shell
uv run python docs/dry/temp-tests/dry-file-conf-w2/repass_w2_9031.py
```

Result `W2 ALL OK` (9 sections). One first-draft probe assertion
failed on precision (bare `"RESOURCE_POLICY"` mention sweep matched
two docstring projections; corrected to assert the BINDING
`RESOURCE_POLICY_KEY = "RESOURCE_POLICY"` single-sited plus the
mention set exactly the three known files) and one overstated the
oracle rule (direct `conf._normalize_user_settings` calls in
`tests/base/test_conf.py` are R1's own unit rows, not
enumeration-from-owner; corrected to assert the R12 rows spell
literals). Both re-verified green, substance unaffected.

- **R12 re-derived.** Reader
  `django_strawberry_framework/conf.py::resource_policy_setting`
  still one `getattr(settings, RESOURCE_POLICY_KEY, None)` line,
  default `None`, no validation (count 1). Binding single-sited
  (only `conf.py`); mentions exactly `conf.py` +
  `resource_policy.py` + `schema.py` docstring projections, never a
  second definition. `resolve_resource_policy` still feeds the
  shared `utils/policies.py::resolve_policy` driver with
  `read_setting=resource_policy_setting`,
  `policy_cls=ResourcePolicy`, `default=DEFAULT_RESOURCE_POLICY`
  (feed intact). Schema ladder intact:
  `DjangoSchema.__init__` still takes `resource_policy=... = None`
  and resolves via `resolve_resource_policy(resource_policy if
  declared_resource is None else declared_resource)` — kwarg
  outranks setting outranks defaults. Oracles: `test_conf.py`
  reader hits 6 + key spells 2 (unchanged file);
  `test_resource_policy_api.py` `resource_policy=` hits 19 (18 old
  intact + 1 new `CARRY_RELATION` mount; zero removed lines carry
  that pattern); live-tier file holds no `conf` import and no
  `RESOURCE_POLICY_KEY` spelling; setting-backed ladder rows in
  `tests/test_resource_policy.py` untouched by the range (zero
  R12-pattern hits in its diff). No oracle rewritten to read from
  the owner.
- **F1 re-checked.** 117 package `.py` files; exactly 4 gate
  callsites in the same 4 patch modules; exactly 4 gate imports;
  `UPSTREAM_PATCH_DEPENDENCIES` still the same 4 names; all 4 patch
  modules + `apps.py` hash-identical. Trigger still absent:
  reuse stays rejected.
- **Fingerprints.** All 5 changed hashes re-measured and match
  (`resource_policy.py` `647133d2…`, `schema.py` `2f727321…`,
  `test_resource_policy_api.py` `94d9d079…`,
  `test_library_api.py` `ea74fb5d…`, `test_products_api.py`
  `eff4cd80…`); all 24 unchanged members of the artifact's
  population re-hashed identical (full 29-file sweep, no finding
  stale on any other account). Production diffs in range are
  prose-only on every R12-touched path (`resource_policy.py` two
  docstring hunks, zero `def` changes, `read_setting` untouched;
  `schema.py` one docstring hunk, ladder code untouched).
  Oracle diffs additive or unrelated (`test_resource_policy_api`
  +1 mount, existing kwarg rows untouched; `test_library_api`
  removed lines are optimizer-hint docstring reword only,
  HIDE_FLAT hits 0; `test_products_api` purely additive, relay
  row intact).
- **Gates / negative controls (affected rows).** Delattr census,
  reader default/override table, typo/non-bool/non-string/
  non-mapping/liar/hostile rows all live in `test_conf.py`
  `f35c7074…` (identical) — every gate still fails its
  divergence. Rename-`RESOURCE_POLICY_KEY` still fails the two
  literal key spells + reader rows. W2-1/W2-2 stand as recorded
  (parametrized-from-owner population pin still absent; rename
  still fails via the hardcoded-name rows per the recorded
  correction; still a family-item hardening note, unchanged by
  this range).
- **Pending.** None — agreed. Probe already ran green
  (read-only, no DB); oracle bodies static-reviewed; target
  reaches no database, alias, or dialect decision (pure
  settings-dict reads; the endpoint default is never resolved
  here), so `FAKESHOP_SHARDED` / Postgres are inapplicable by
  construction with that reason. No workspace copy owed (no
  mutating proof), so no `__file__` / DB `NAME` record applies.
- **Zero-edit.** `git diff
  5eccb18a9400b1bc0daf154e36acc853a3c29ae6 --
  django_strawberry_framework/conf.py` = 0 bytes (re-measured by
  Worker 2); working blob `c6ad46aa…` = `HEAD:` blob; `git status
  --short -- django_strawberry_framework/conf.py` empty. No
  production edit demanded or made.
- **AGENTS.md prose.** Item-scoped diff empty: no production/test
  prose to violate, no process provenance, no commit, no ruff
  owed (no tracked `.py` edits; W2 scratch is untracked
  read-only scratch under
  `docs/dry/temp-tests/dry-file-conf-w2/`). Citations use
  `path::Symbol` form; the one raw `path:NN` below is inside
  this `docs/dry/dry-*.md` scratchpad artifact, which the rule
  permits. Concurrent dirt untouched (ledger paths never
  touched; `connection.py`, `tests/test_connection.py`, staged
  `tests/utils/test_querysets.py`,
  `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`
  left alone).

### Reconciliation with `## Re-pass at 9031cb3d (Worker 1)`

Agreement per row: R12 reader still 1 (agreed); R12 feed intact
(agreed); schema ladder outranks (agreed); R12 oracles intact —
19 hits (agreed; precision: 18 pre-existing intact + 1 new
`CARRY_RELATION` mount = 19 total, zero existing kwarg-path rows
touched); R6–R13 spot still 1 each with identical downstream
validators (agreed); F1 trigger absent, stays rejected on 117 /
4 / 4 / 4 census (agreed); R1–R4 / R14 / C31 / F1(b)
spot-confirm by identity (agreed); fingerprint table 5 changed +
24 unchanged (agreed row-for-row — own 29-file sweep matches);
gates still fail their divergences with W2-1/W2-2 standing
(agreed); pending none with the same inapplicability reason
(agreed); zero-edit diff state (agreed).

Differences (two, both non-blocking, neither demands
resubmission): (a) W1's R12e states "19 hits still present" —
read strictly, 18 were still present and 1 is new; the
additive-only substance (no existing row touched) is confirmed
by the removed-line sweep above. (b) W1's stale census ("5 files
are stale") covers the artifact's fingerprinted population but
not `tests/test_resource_policy.py`, which changed +208/−5 in
range without ever being fingerprinted although R12's
setting-backed ladder rows (e.g. the `resolve_resource_policy`
setting-vs-default rows) live there. Worker 2 closed the gap
for this range: its diff carries zero R12-pattern hits
(`RESOURCE_POLICY`, `resource_policy_setting`,
`resolve_resource_policy(None)`,
`DJANGO_STRAWBERRY_FRAMEWORK`), removed lines are two import
extensions plus three docstring prose lines, and additions are
evaluated-window `bounded_rows` tests that never touch a
settings reader — so no finding goes stale on its account.
Observation for Worker 0 (below the defect bar — no contract
row breaks, no resubmission): consider fingerprinting that file
in R12's freshness set so the next range need not re-derive
this by sweep.

## Defects (Worker 2) — re-pass at 9031cb3d

None new. W2-1/W2-2 (prior pass) stand unchanged by this range
(`test_conf.py` identical). The census observation in the
reconciliation above breaks no contract row under any
wire/configuration input and is not routed as a defect.

## Judgment (Worker 2) — re-pass at 9031cb3d

Bounded re-pass complete: R12 and F1 re-derived fresh at
`9031cb3d`, all 5 changed fingerprints verified plus full
29-file sweep identical elsewhere, gates re-checked with
negative controls intact, no oracle rewritten, zero-edit
confirmed, no pending execution, no new defects. Zero-edit
result stands legitimate.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Bounded re-review at bfaee91d (Worker 2, Q4)

Phase 1 of a two-phase bounded re-reconciliation (Q4). Scope: whether the
settings-vs-argument precedence findings for `conf.py` still hold after
`schema.py` grew new methods. Zero edits; re-review only. Tests were oracles
READ, not run. No status set; no verdict on prior findings proposed here.

### 1. Precedence ladder re-derived from current source (per parameter)

`DjangoSchema.__init__` policy-override surface (current HEAD bytes):

- `django_strawberry_framework/schema.py::DjangoSchema.__init__` accepts exactly
  two policy/setting overrides: `resource_policy` (`ResourcePolicy | Mapping |
  None = None`) and `error_policy` (`ErrorPolicy | Mapping | None = None`).
  All other constructor input is passthrough (`*args`, plus `**kwargs` entries
  `extensions` and `execution_context_class`, handled for chain settlement, not
  as policy vocabularies). The delta did not touch this signature or body.
- Ladder, per policy, highest first (from
  `django_strawberry_framework/utils/policies.py::resolve_policy`, bound per
  policy by `django_strawberry_framework/resource_policy.py::resolve_resource_policy`
  and `django_strawberry_framework/error_policy.py::resolve_error_policy`):
  1. the explicit `DjangoSchema(...)` argument (instance or mapping; `None`
     means absent and falls through);
  2. the `DJANGO_STRAWBERRY_FRAMEWORK` settings-dict slot
     (`RESOURCE_POLICY` / `ERROR_POLICY`), read thinly by
     `django_strawberry_framework/conf.py::resource_policy_setting` /
     `django_strawberry_framework/conf.py::error_policy_setting`
     (`getattr(settings, KEY, None)`; `None` means absent);
  3. the package default (`DEFAULT_RESOURCE_POLICY` / `DEFAULT_ERROR_POLICY`).
- So per parameter: argument outranks setting; setting outranks default.
  `resource_policy=` outranks `RESOURCE_POLICY`; `error_policy=` outranks
  `ERROR_POLICY`. The two parameters are independent ladders sharing one
  mechanism.
- Normalization at each rung (shared, not per-policy): an instance from EITHER
  override slot is canonicalized through
  `django_strawberry_framework/utils/policies.py::canonical_policy` into a
  private freshly validated duplicate (never the caller-held object); a mapping
  from either slot is materialized once into a plain dict and applied over the
  dataclass defaults (partial override); a non-mapping override is
  `ConfigurationError`; unknown keys are `ConfigurationError` naming the valid
  vocabulary; domain validation stays in the policy classes (`__post_init__`).
- Resource-only extra path, re-derived from the unchanged `__init__` body and
  `django_strawberry_framework/schema.py::_consumer_extension_entries`: an exact
  `DjangoResourcePolicyExtension(policy=...)` instance supplied in
  `extensions=[...]` is folded at construction and occupies the EXPLICIT slot
  passed to `resolve_resource_policy` (hence also outranks the setting); a bare
  class entry declares nothing and is dropped; arg + entry together raise
  `ConfigurationError` (double declaration refused). An exact error-policy
  entry is NOT folded (dropped at construction; a resolved member claiming
  either authority is refused later in
  `django_strawberry_framework/schema.py::DjangoSchema.get_extensions`). No
  per-request override exists; per-operation reads come from the settled record.
- `conf.py` stays a thin reader: no domain validation there beyond the shared
  malformed-dict guard (`_normalize_user_settings` -> `ConfigurationError`) and
  the missing-key `AttributeError` contract. This matches the AGENTS.md rows:
  `conf.settings` reads the dict; missing keys raise `AttributeError`; keys land
  only with their feature.
- Oracles read (not executed): `tests/test_resource_policy.py`
  (`test_the_setting_supplies_the_policy_when_no_argument_does`,
  `test_an_explicit_argument_outranks_the_setting`,
  `test_an_instance_through_the_setting_slot_resolves_on_the_same_terms`,
  `test_no_source_at_all_resolves_to_the_package_defaults`),
  `tests/test_error_policy.py`
  (`test_the_setting_supplies_the_policy_when_no_argument_does`,
  `test_an_explicit_argument_outranks_the_setting`,
  `test_no_source_at_all_resolves_to_the_package_defaults`),
  `tests/utils/test_policies.py`
  (`test_the_setting_supplies_overrides_when_the_argument_is_absent`,
  `test_an_explicit_mapping_outranks_the_setting`),
  `tests/test_schema.py`
  (`test_a_policy_behind_the_setting_is_snapshotted_like_an_explicit_one`).

### 2. New schema methods configuration reads (delta)

Delta (`9031cb3d..bfaee91d`, target-scoped) is exactly: import-row expansion
(single `DjangoErrorPolicyExtension` import -> five-name import incl.
`degraded_result`, `is_maskable_result`, `mask_execution_result`,
`masking_is_active`) + one class-docstring paragraph (hook-escape seam) +
three methods (`execute_sync`, `execute`, `_masked_return`). All other
`schema.py` lines byte-identical (confirmed from the target-scoped diff;
`conf.py` diff is empty). Nothing else in the two targets changed -- stated
loudly as required.

Per new method, traced from current HEAD bytes:

- `django_strawberry_framework/schema.py::DjangoSchema.execute_sync`: no
  configuration read. Passes `*args/**kwargs` to `super().execute_sync` and
  hands the returned result to `_masked_return`.
- `django_strawberry_framework/schema.py::DjangoSchema.execute` (async twin):
  no configuration read. Awaits `super().execute` and hands the returned result
  to `_masked_return`. Docstring records streamed operations are not masked
  here.
- `django_strawberry_framework/schema.py::DjangoSchema._masked_return`: reads
  the SETTLED record only -- `django_strawberry_framework/schema.py::_enforcement(self)`
  `.error_policy` (backed by `django_strawberry_framework/schema.py::_SCHEMA_ENFORCEMENT`),
  with the pre-read floor `DEFAULT_ERROR_POLICY` for the fail-closed degrade.
  Gates and masking compose by name from the owning module:
  `extensions/error_policy.py::masking_is_active`,
  `extensions/error_policy.py::is_maskable_result`,
  `extensions/error_policy.py::mask_execution_result`,
  `extensions/error_policy.py::degraded_result` (plus `logger.exception` on the
  guard path). It deliberately does NOT read `schema.error_policy` (the
  per-read copy resolvers can reach), does NOT read `django.conf.settings` /
  `conf.settings` / `resource_policy_setting` / `error_policy_setting` /
  `RESOURCE_POLICY_KEY` / `ERROR_POLICY_KEY`, and does NOT read resource policy
  at all. Textual check: the only `RESOURCE_POLICY`/`ERROR_POLICY` hits in
  `schema.py` are the pre-existing `__init__` wiring, docstrings, and fallback
  record; the only settings-adjacent hit in the new bodies is the
  `DEFAULT_ERROR_POLICY` floor.
- Net: no new method bypasses the ladder. The ladder still runs once at
  construction; the new seam consumes its settled output, from the same record
  the admitted per-operation chain is built from. No direct settings read was
  added on any request path.

### 3. Definition counts

DRY.md sense: independently maintained implementations/declarations of the
rule; consumers, oracles, projections listed separately, not counted.

- New settings key introduced by the delta: 0 definitions. The delta adds no
  `_KEY` constant and no `*_setting` reader; `conf.py` is byte-identical across
  the delta. Current package population for context: 10 `_KEY` constants in
  `django_strawberry_framework/conf.py` (`DJANGO_SETTINGS_KEY`,
  `APPLY_UPSTREAM_PATCHES_KEY`, `NESTED_CONNECTION_STRATEGY_KEY`,
  `SINGLE_PARENT_FAST_PATH_KEY`, `TESTING_ENDPOINT_KEY`, `HIDE_FLAT_FILTERS_KEY`,
  `RELAY_GLOBALID_STRATEGY_KEY`, `MAX_REQUEST_BODY_BYTES_KEY`,
  `RESOURCE_POLICY_KEY`, `ERROR_POLICY_KEY`); the two policy-relevant keys each
  have exactly one thin reader (`resource_policy_setting`,
  `error_policy_setting`). No second definition of either policy key added.
- New per-init override introduced by the delta: 0 definitions. The `__init__`
  signature is unchanged (2 policy overrides: `resource_policy`,
  `error_policy`); the three new methods take `(*args, **kwargs)` passthrough
  (`execute_sync`, `execute`) and `(result)` (`_masked_return`) respectively,
  none of which is a policy/setting override spelling. No second spelling of
  either override added.
- The new seam is a consumer/enforcement site, not a definition: masking
  vocabulary (active/maskable/shape/floor) is defined once in
  `extensions/error_policy.py`; `_masked_return` calls it by name (DRY.md
  principle 6). The ladder is defined once in `utils/policies.py::resolve_policy`;
  the two `resolve_*` functions are thin adapters, not second ladders.
- Oracles touching the seam (read): `tests/test_error_policy.py`
  (`test_the_return_seam_passes_an_already_masked_result_through_by_identity`,
  `test_the_return_seam_degrades_when_masking_itself_raises`,
  `test_the_return_seam_is_a_no_op_when_the_policy_is_disabled`).

### 4. Owners I would choose (DRY.md principles 2/7)

- Shared explicit > setting > default normalization: owner
  `django_strawberry_framework/utils/policies.py::resolve_policy` (the narrowest
  cohesive owner every legitimate consumer can depend on without reversing a
  dependency; both policy resolvers delegate with their setting reader,
  display name, and unit). `resolve_resource_policy` / `resolve_error_policy`
  stay thin adapters binding vocabulary; `resource_policy_setting` /
  `error_policy_setting` stay thin readers (no domain validation) -- distinct
  responsibilities (principle 7), one translation of the ladder (principle 2).
- Settled per-schema authority and lifetime: owner
  `django_strawberry_framework/schema.py::_SCHEMA_ENFORCEMENT` (with
  `django_strawberry_framework/schema.py::_SchemaEnforcement` /
  `::_enforcement`), settled once in `DjangoSchema.__init__` before the base
  constructor runs; per-operation/per-read consumers (`get_extensions`,
  `_admitted_chain`, `_refused_chain`, `resource_policy` / `error_policy`
  copy-out properties, `_masked_return`) read from it. Lifetime: construction
  to schema death (weak-evidence drop); no consumer-visible name answers with
  the authority itself.
- Return-seam masking vocabulary: owner `extensions/error_policy.py` (active /
  maskable / masked shape / degraded floor); `DjangoSchema._masked_return`
  owns only the application point (fail-closed degrade around the returned
  result), composing by name. The teardown and the return seam share the one
  implementation rather than restating the classifier.
- No consolidation or move proposed in this phase (re-review only).

### 5. Whether the delta breaks anything derived

No. The ladder derivation in section 1 holds unchanged after the delta: the
resolver chain (`resolve_policy` <- `resolve_*` <- `*_setting` <- settings
dict), the `__init__` wiring (including the resource-entry fold and the
double-declaration refusal), and `conf.py` bytes are all untouched. The new
seam reads the same settled record the admitted chain is built from, so the
per-operation policy source is unchanged; double application is a structural
no-op (already-masked errors carry `original_error=None`, which the shared
classifier reads as deliberate -- oracle: identity assertion in
`test_the_return_seam_passes_an_already_masked_result_through_by_identity`);
the disabled-policy path stays a no-op through the shared
`masking_is_active` gate (oracle:
`test_the_return_seam_is_a_no_op_when_the_policy_is_disabled`); the degrade
floor is built from the package default without re-reading the schema policy
inside the guard, so the floor cannot raise. No new settings key means the
AGENTS.md "keys land only with their feature" row is untouched; no
missing-key/attribute path changed. No defect found: no contract row broken,
so no reaching wire/configuration input to name (per the GOAL.md trust
boundary a defect would require contract row + feasible project shape +
  reaching input; none applies).

### 6. Freshness fingerprints (everything inspected)

- HEAD: `bfaee91dcd332a5f86250fff90ab21b377bc674e`; delta base: `9031cb3d`.
- Targets (working tree clean vs HEAD; `git status --short --` on both paths
  empty, so working blob == `HEAD:<path>`):
  - `django_strawberry_framework/conf.py`: blob `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25` (whole target read, 616 lines).
  - `django_strawberry_framework/schema.py`: blob `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5` (whole target read, 1319 lines).
- Delta shape: `git diff 9031cb3d..bfaee91d --stat -- schema.py`: 84 insertions,
  1 deletion (the 1 deletion is the replaced single-line import); `git diff
  9031cb3d..bfaee91d -- conf.py` byte count 0. Target-scoped unified diff
  inspected in full: only the import-row hunk, the class-docstring hook paragraph
  hunk, and the `execute_sync` / `execute` / `_masked_return` hunk.
- Ladder/mechanism sources read:
  - `django_strawberry_framework/resource_policy.py`: blob `647133d23785d325856b2d1d495d18c5741dd23c` (resolve + `DEFAULT_RESOURCE_POLICY` region).
  - `django_strawberry_framework/error_policy.py`: blob `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91` (resolve + `DEFAULT_ERROR_POLICY` region).
  - `django_strawberry_framework/utils/policies.py`: blob `860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e` (whole file, 177 lines).
  - `django_strawberry_framework/extensions/error_policy.py`: blob `bd763bcc428ce0f495448e6d228061dd0bc08688` (import-target surface only).
- Oracles read: `tests/test_resource_policy.py` blob `eaaa1fa16d64118abda847f688a2b347401a1dd1`; `tests/test_error_policy.py` blob `9ff5328eaed329a5fd69ac2e7002cf0052452241`; `tests/test_schema.py` blob `02f4bb717b4717e4d90322a6f8bb3fb1d6523e83`; `tests/utils/test_policies.py` blob `295ef658c852330c6f1f5ca576678a57720cec5d`.
- Contract sources read: `AGENTS.md` blob `e42247fa310bf7a85914d7efa7f177ee5307b860`; `docs/dry/DRY.md` blob `e8151123ff7e129fe9881ec342231e9e1795148e`; `docs/dry/worker-2.md` blob `4f089ea4a58d73295638e83abf8c612bf31487f8`.
- Concurrent dirt preserved: `git status --short` at inspection shows many
  paths dirty outside the two targets (package, tests, docs, example DBs); none
  touched by this phase (zero edits; this append is the only write, scoped to
  the new section below the prior content). No commit. Not read in this phase:
  `docs/dry/dry-file-conf.md` prior sections (append-only; no prior bytes
  modified).

PHASE-1-TRACE-RECORDED -- artifact: docs/dry/dry-file-conf.md

## Bounded re-review at bfaee91d (Worker 2, Q4) -- Phase 2 reconciliation

Scope: Q4 only (R11/R12/R13 + R6 trigger family vs the schema +84). Settled
rows (R1-R10, R14, C31, F1, W2-1/W2-2) confirmed untouched, not re-litigated.
No status changed by this worker. No verdict on anything outside Q4.

### Phase-1 integrity

My phase-1 section `## Bounded re-review at bfaee91d (Worker 2, Q4)` is intact
at the artifact tail (lines 1172-1391, header plus sections 1-6 present as
drafted, ending PHASE-1-TRACE-RECORDED). It was recorded before exposure:
the phase-1 message ended PHASE-1-TRACE-RECORDED without opening the artifact
(the section itself records "Not read in this phase" for the prior sections),
and the prior findings R11/R12/R13/R6 were first seen in the phase-2 prompt.
No prior line touched: `Status: verified`, `Run: 0.0.15 2026-09-18-1`,
System trace, Verification, Findings (F1, R1-R13 file-locals, R14, C31),
Defects, Pending execution, Judgment, Implementation, Independent verification,
re-pass sections, and the LINK DEFINITIONS block all byte-untouched by me
(artifact remains untracked `??`; this append is the only write).

### Delta shape re-established (loudly)

`git diff 9031cb3d..bfaee91d --stat -- django_strawberry_framework/schema.py`:
84 insertions, 1 deletion. Hunk headers: `@@ -62,7 +62,13 @@` (import-row
expansion only), `@@ -705,6 +711,15 @@` (one class-docstring paragraph, the
hook-escape seam), `@@ -1005,6 +1020,74 @@` (the three new methods). Full
`^[+-]` body read: nothing else changed -- no `__init__` hunk, no resolver
hunk, no enforcement-record hunk. `git diff 9031cb3d..bfaee91d --
django_strawberry_framework/conf.py` byte count 0; conf blob identical both
sides (`c6ad46aa...`, see re-hashes). Views, resource_policy, error_policy,
utils/policies diffs in range: empty for the five files checked
(`git diff ... --stat` names schema.py alone). NOTHING ELSE CHANGED in the two
targets -- stated loudly as required.

### R11 -- HOLDS (same thin split, same owner, same trigger)

Re-derived at current bytes. `django_strawberry_framework/conf.py::max_request_body_bytes_setting`
is still one `getattr(settings, MAX_REQUEST_BODY_BYTES_KEY, 1_048_576)` line,
no validation (count 1; constant + reader = one rule in two statements, same
file). `MAX_REQUEST_BODY_BYTES_KEY` binding still single-sited; `_KEY`
census 10 both sides of the delta. Validation still lives downstream in
`django_strawberry_framework/views.py::_resolved_max_request_body_bytes`
(re-read whole body at current bytes): `None` from the view mount falls to
the setting, `None` from the setting disables the cap, `0` rejected,
positivity + exact-`int` (`type(value) is not int`, so `bool` excluded) owned
there with `ConfigurationError` via `describe_value`; the module restates no
number. Owner unchanged: key + thin reader in conf.py; bound vocabulary in
views.py. Trigger unchanged (as R6). Oracles still pin it (reader
default/override table + transport cap rows, untouched by this range -- no
views.py diff in range).

### R12 -- HOLDS (same thin split, same ladder, same trigger)

Re-derived at current bytes.
`django_strawberry_framework/conf.py::resource_policy_setting` still one
`getattr(settings, RESOURCE_POLICY_KEY, None)` line, default `None` (absent =
package defaults, no disable spelling), no shape/domain validation (count 1).
Feed intact: `django_strawberry_framework/resource_policy.py::resolve_resource_policy`
still calls the shared
`django_strawberry_framework/utils/policies.py::resolve_policy` with
`read_setting=resource_policy_setting`, `policy_cls=ResourcePolicy`,
`default=DEFAULT_RESOURCE_POLICY`. Ladder intact: `DjangoSchema.__init__`
signature lines byte-identical across the delta
(`resource_policy: ResourcePolicy | Mapping[str, Any] | None = None` at prior
728 / current 743; `error_policy` pair likewise), body still resolves via
`resolve_resource_policy(resource_policy if declared_resource is None else
declared_resource)` -- explicit argument outranks setting outranks defaults,
with the exact-entry fold / double-declaration refusal unchanged (no hunk
there). Owner unchanged: thin reader in conf.py; normalization in the shared
driver; wiring in `__init__`; settled authority in
`django_strawberry_framework/schema.py::_SCHEMA_ENFORCEMENT`. Trigger
unchanged (as R6).

### R13 -- HOLDS (same thin split, same ladder, same trigger)

Re-derived at current bytes.
`django_strawberry_framework/conf.py::error_policy_setting` still one
`getattr(settings, ERROR_POLICY_KEY, None)` line, default `None`, no
validation (count 1). Feed intact:
`django_strawberry_framework/error_policy.py::resolve_error_policy` still
delegates to the same shared driver with `read_setting=error_policy_setting`.
Opt-out still spelled `{"enabled": False}` (recorded decision, never omission)
at the policy layer, untouched by the delta. Same owners and trigger as R12.

### Load-bearing question -- NO BYPASS (each new method body opened)

- `django_strawberry_framework/schema.py::DjangoSchema.execute_sync`: body is
  `return self._masked_return(super().execute_sync(*args, **kwargs))`. No
  policy object constructed, no settings read, no `*_setting()` call, no KEY
  reference. It does not construct with any policy; it forwards and masks.
- `django_strawberry_framework/schema.py::DjangoSchema.execute`: body is
  `return self._masked_return(await super().execute(*args, **kwargs))`.
  Same: no construction, no configuration read (async twin; streamed frames
  explicitly not masked here per its docstring).
- `django_strawberry_framework/schema.py::DjangoSchema._masked_return`: body
  reads the policy from the ACCEPTED ENFORCEMENT RECORD ONLY --
  `policy = _enforcement(self).error_policy` (backed by `_SCHEMA_ENFORCEMENT`),
  with the pre-read floor `policy = DEFAULT_ERROR_POLICY` for the fail-closed
  degrade. Gates and masking compose by name from the owning module:
  `masking_is_active`, `is_maskable_result`, `mask_execution_result`,
  `degraded_result` (plus `logger.exception` on the guard path). It does NOT
  read `django.conf.settings` / `conf.settings` / `resource_policy_setting` /
  `error_policy_setting` / either KEY, does NOT read `schema.error_policy`
  (the per-read copy, deliberately avoided per its docstring), and does NOT
  read resource policy at all. Textual check holds: the only
  `RESOURCE_POLICY`/`ERROR_POLICY` hits in schema.py are the pre-existing
  `__init__` wiring, docstrings, and fallback record.
- Net: the ladder still runs ONCE at construction; the new seam consumes its
  settled output from the same record the admitted per-operation chain
  (`_admitted_chain` / `_refused_chain`) is built from. No new method reads
  policy/settings configuration directly; no bypass exists.

### R6 trigger -- NOT FIRED

Recorded trigger shape: arrival of a new settings key / new per-init override
(C13-C16 pattern; preemptive keys violate the AGENTS.md rule). Measured at
bfaee91d: zero new `_KEY` constants (10 before, 10 after; conf.py diff empty),
zero new `*_setting` readers, zero new `__init__` parameters (signature
identical, see above). The +84 is one import-row expansion + one docstring
paragraph + three methods taking `(*args, **kwargs)` passthrough / `(result)`
-- none is a settings key or an override parameter spelling. So the +84 does
NOT constitute "a new per-init override" and does not fire the trigger. The
AGENTS.md row (keys land only with their feature) is untouched; the
missing-key `AttributeError` path is untouched.

### Freshness re-hashed (just now, worktree == HEAD:bfaee91d)

- `django_strawberry_framework/conf.py` `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25` (whole target; matches every prior record).
- `django_strawberry_framework/schema.py` `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5` (whole target, 1319 lines).
- `django_strawberry_framework/views.py` `9f85b0df26a17e800ec392aa13f6848e07633895` (matches the artifact's R11 row).
- `django_strawberry_framework/resource_policy.py` `647133d23785d325856b2d1d495d18c5741dd23c` (matches the 9031cb3d re-pass new hash).
- `django_strawberry_framework/error_policy.py` `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91` (matches the artifact's R13 row).
- `django_strawberry_framework/utils/policies.py` `860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e` (driver identical).
- `django_strawberry_framework/extensions/error_policy.py` `bd763bcc428ce0f495448e6d228061dd0bc08688` (masking owner surface).
- Targets clean: `git status --short --` on conf.py + schema.py empty, so working blobs == `HEAD:<path>`. HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e`; delta base `9031cb3d`.
- Searched population for Q4: both targets whole, all four policy/body-cap consumers (views resolver, both policy resolvers, shared driver, masking owner), `__init__` signature both sides, `_KEY` census both sides, target-scoped unified diff in full. Excluded as before: R1-R10/R14/C31/F1 bodies (conf-identical, no re-derivation owed), unrelated delta files outside the five checked (none changed).

### Verdict

`verified` -- R11/R12/R13 stand at bfaee91d (same thin splits, same owners,
same triggers); the +84 adds no settings key and no per-init override, so the
R6 trigger is not fired; no new method bypasses the ladder (settled-record
reads only); zero tracked edits by this re-review.

### Defects

None new. (Worker 2) No defect found in Q4 scope: no contract row breaks under
any wire/configuration input, so nothing routes to `## Defects`.

### Exact plan rows (for Worker 0; this worker edits no plan)

- `docs/dry/dry-0_0_15.md` File `conf.py` tick: from `verified (Run 0.0.15
  2026-09-18-1, re-pass at 9031cb3d; zero edits, no pending execution)` to
  `verified (Run 0.0.15 2026-09-18-1, re-pass at 9031cb3d; bounded re-review
  Q4 at bfaee91d, zero edits, no pending execution)`.
- Q4 queue note (`File conf (schema ladder vs +84)`): close as done by this
  reconciliation.
- Responsibility index: no new row (no family named; thin-reader rows stand).
- `## Owned changes`: no new row (zero tracked edits; this artifact remains
  untracked).
