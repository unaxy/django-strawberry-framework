# Rationale: spec-024 — Django Trac #37064 hardening + `safe_wrap_connection_method` (derivation, rejected alternatives)

Deliberative companion to [`spec-024-django_trac_37064_hardening-0_0_7.md`][spec-024]. The spec is the contract and states what the code does; this file carries the derivation behind each Decision and the alternatives each rejected.

## Decision 1 — A private patch module per dependency, applied from ready()

Spec text: [Decision 1][spec-024-d1].

### Derivation

- A private module keeps `apps.py` short and gives future Django patches a natural home. The leading underscore is the visibility signal; consumers never import it.
- `ready()` is Django's canonical one-time-setup hook and fires once after all apps load, which is exactly the lifecycle point at which `SimpleTestCase` is importable and the patch has not yet been needed.
- Function-local imports in `ready()` mean importing `apps` outside a configured Django project pulls in no patch module.

### Alternatives considered (and rejected)

- **Inline the patch in `apps.py`.** Rejected: the patch carries far more rationale than code, and inlining it would bury the `AppConfig` shape (which is a different card's contract) under it.
- **A single patch module for every dependency.** Rejected: the settings surface is keyed per dependency, so one module per dependency keeps `UPSTREAM_PATCH_DEPENDENCIES` and the module list in one-to-one correspondence and makes an opt-out mean exactly one module.

## Decision 2 — The patch installs on `SimpleTestCase`

Spec text: [Decision 2][spec-024-d2].

### Derivation

Django defines `_remove_databases_failures` on `SimpleTestCase`. Patching the definition site covers `TransactionTestCase`, `TestCase`, and every direct `SimpleTestCase` subclass in one assignment, and covers them through the same MRO Django itself relies on.

### Alternatives considered (and rejected)

- **Install on `TransactionTestCase`.** Rejected: a direct `SimpleTestCase` subclass with `TransactionTestCase` nowhere in its MRO bypasses the net entirely, which is a correctness hole rather than a stylistic preference.

## Decision 3 — The replacement re-wraps foreign replacements, then delegates

Spec text: [Decision 3][spec-024-d3].

### Derivation

- The crash is *inside* the loop upstream runs, at its unconditional `method.wrapped` read, so a wrapper cannot skip one method's unwrap. It can instead make that read succeed: wrapping a foreign replacement in a `_DatabaseFailure` of the patch's own before the call means Django's unwrap reads the replacement back off `wrapped` and restores it. Django's `_DatabaseFailure(wrapped, message)` constructor and its unwrap's single `.wrapped` read are the only protocol the patch relies on.
- Delegating keeps the unwrap Django's own: an upstream body change flows through the call, the way it does for the delegating sibling patch modules, so the patch validates only the call shape and the method list's presence, and copies no upstream body.
- The re-wrap restores the symmetry Django's own docstring claims: `_add_databases_failures` and `_remove_databases_failures` operate on the methods *they* wrapped, and the patched form leaves a method the pair never owned as it found it.
- The `finally` delete is what keeps "as it found it" true for a class-level replacement: reading through the instance and writing back through Django's `setattr` would otherwise freeze the class-level value onto the instance, where it outlives the class-level patch.

### Alternatives considered (and rejected)

- **Reimplement upstream's loop behind one `isinstance(method, _DatabaseFailure)` guard.** Rejected: a reimplementation copies Django's body, so an upstream body change does not flow through it, and keeping it honest needs every audited upstream body pinned as source text and compared at app load. That pin aborts on a comment-only upstream edit or a source-less install, and the copied body owes Django's license.
- **Uninstall Django's wrapper and reinstall it around the risky window** — the `django-debug-toolbar` cache-panel owner-sentinel shape. Rejected because the package does not own `_DatabaseFailure`; the pattern needs the wrapper's owner. It remains the right answer for any future package-owned connection instrumentation, and the module docstring's ecosystem-precedent section names it as the pattern explicitly *not* available here.

## Decision 4 — Fail-closed upstream validation in three tiers

Spec text: [Decision 4][spec-024-d4].

### Derivation

Two facts force the tiers. The module reads Django private symbols (`_DatabaseFailure`, a private classmethod, the private list of disallowed connection methods), and it re-wraps the methods that list names before delegating. Any of them can drift silently. Silently dropping a defensive patch leaves a consumer believing they have protection they do not have; refusing to install is loud, and is only tolerable because an explicit opt-out exists to recover from it ([Decision 6](#decision-6--apply_upstream_patches-is-the-escape-hatch)). That dependency is the reason the two Decisions cannot be read apart.

### Alternatives considered (and rejected)

- **Degrade gracefully on a missing private symbol — log one notice and return.** Rejected on the ground above: the consumer would keep a teardown they believe is hardened and is not.
- **Pin the upstream body's source text.** Rejected: the patch delegates, so a body change flows through the call and needs no audit; a text pin would abort on a comment-only upstream edit or a source-less install while protecting nothing.
- **Pin a Django version range.** Rejected: a version range is a proxy for the shape and drifts from it; the three tiers read the shape itself.

## Decision 5 — Two homes of the method list, discriminated by the feature flag

Spec text: [Decision 5][spec-024-d5].

### Derivation

The class attribute is the home on Django `5.2.16` - `6.0.x` and the connection feature flag on `6.1`. Both resolve to the same four `(name, operation)` pairs, so one re-wrap step serves both provided the *read* differs.

**Why the feature flag first and not `hasattr(cls, …)`, stated as mechanism because it is the part that gets "simplified" back:** a Django `6.1` subclass may still declare its own `_disallowed_connection_methods`, but upstream's `_add_databases_failures` ignores that attribute and wraps the **feature list**. The re-wrap must read the same list setup wrote, or it re-wraps names nothing wrapped while leaving a foreign replacement on a wrapped name unprotected. The flag's presence is read with a `None` default, never a truthiness test, so an empty flag list stays the flag's answer.

### Alternatives considered (and rejected)

- **`hasattr(cls, "_disallowed_connection_methods")` as the discriminator.** Rejected for the reason above: on `6.1` it honours a subclass list that setup never wrapped.
- **Branch on a Django version number.** Rejected: where the list lives, not the version, is what the read depends on, and a version check drifts from it.

## Decision 6 — `APPLY_UPSTREAM_PATCHES` is the escape hatch

Spec text: [Decision 6][spec-024-d6].

### Derivation

A patch that can raise at `AppConfig.ready` ([Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers)) can refuse to boot a consumer who upgraded Django ahead of the package, so the hatch is the documented recovery path, not optional polish. [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" is satisfied: the feature that needs the key is the fail-closed validation. The installed replacement is defensive, leaving a foreign replacement as it found it; that describes teardown, not `apply()`, and it is no argument against the opt-out.

That coupling is why the gate is `apply()`'s **first** statement, ahead of validation, and why `tests/test_django_patches.py::test_django_dependency_opt_out_silences_missing_method_list_abort` pins the pairing end to end rather than the two features separately. A gate placed after validation would be unreachable in the situation it exists for.

### Alternatives considered (and rejected)

- **No key; a consumer who needs to disable the patch files a card.** Rejected: a card is not a remedy on the timescale of a blocked deployment.
- **A bool only.** Rejected: this is a *test-only* patch beside the other dependencies' patches, two of which are *production* request hardening, so a consumer disabling this one should not lose those. The per-dependency mapping exists to make the blast radius one module.
- **Coerce loose values (`"false"`, `0`).** Rejected in `django_strawberry_framework/conf.py::upstream_patches_enabled`: a `"false"` string is truthy and would silently *enable* the patches — the failure direction that produces a false sense of having opted out. Every off-contract shape raises `ConfigurationError`, and the whole mapping is validated on every read so a typo'd dependency name fails at the first gate regardless of which patch module reads first.

## Decision 7 — Idempotent, self-healing, and reload-safe

Spec text: [Decision 7][spec-024-d7].

### Derivation

`ready()` fires more than once under some Django test runners, and a third party can revert the class attribute between calls. Reading actual state satisfies both cases with one mechanism; a flag satisfies only the first.

Reload safety follows from delegation: once the patch calls a captured "original", the capture itself becomes a correctness surface. `importlib.reload()` re-executes the module while `SimpleTestCase` still points at the previous replacement, so a naive re-capture stores the package's own function as the original, and the still-installed replacement then delegates to itself instead of Django at the next teardown. The owner stamp is what breaks that chain.

### Alternatives considered (and rejected)

- **A module-global first-call-wins bool.** Rejected: it makes re-entrant calls no-ops but never re-installs after a third party reverts.
- **Refuse to support reload and document it.** Rejected: the failure mode is not a missing feature but a teardown that recurses into the package's own replacement instead of reaching Django, which nothing at the failure site attributes to the reload.

## Decision 8 — The wrap-time half degrades where the unwrap-time half aborts

Spec text: [Decision 8][spec-024-d8].

### Derivation

The two halves sit at the two lifecycle sites this package can influence, and the wrap-time check is the cheaper of the two: declining costs one predicate and installs nothing. It is unavoidably advisory — the package cannot make third-party wrappers call it — which is why the unwrap-time half exists and is not optional.

**Why the helper does not follow `apply()` into fail-loud.** `apply()` runs inside `AppConfig.ready`, where raising is a decision about whether the *package* should install a protection it cannot verify. `safe_wrap_connection_method` is reached through the public `django_strawberry_framework.testing` import, where the same posture would make a consumer's import crash on a Django private-symbol move. The helper instead reads a missing `_DatabaseFailure` as "no Django wrapper is present, so the slot is free", installs, and returns `True`. `tests/testing/test_wrap.py::test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing` pins it, so the asymmetry is a contract rather than an oversight. It is also barely reachable in practice: with the Django patch enabled, `ready()` has already refused to boot.

### Alternatives considered (and rejected)

- **Follow `apply()` into fail-loud.** Rejected on the boundary argument above.
- **Restore the original method on the consumer's behalf.** Rejected: restoration needs the original, the ordering, and the teardown hook, none of which the helper owns. The docstring carries the worked `setUp` / `tearDown` shape instead, and the unwrap-time backstop makes omitting it non-fatal.
- **Interpolate the offending object into the `TypeError`.** Rejected: the object is consumer-supplied and a `__repr__` that raises would replace the intended `TypeError` with whatever it raised. The diagnostic loses the object's identity deliberately.

## Decision 9 — The helper is a submodule export only

Spec text: [Decision 9][spec-024-d9].

### Derivation

The package's general posture is zero public-export change per card. A public surface is nonetheless correct here: the sibling multi-database card needed no new symbols because the cooperation it pinned already existed in source, whereas Trac #37064 is a bug in Django and this package's guard is the first defensive layer — the value-add *is* new behaviour. Shipping only the auto-applied unwrap patch protects every consumer but gives them nothing to write defensive `setUp` code against. The submodule path is the compromise: opt-in by import, invisible to anyone who does not want it.

### Alternatives considered (and rejected)

- **Re-export from `django_strawberry_framework/__init__.py`.** Rejected: a test-only helper does not belong on the package's front page, and the root `__all__` is the package's whole public surface.
- **Ship no public symbol at all.** Rejected per the derivation: it leaves the wrap-time half unreachable by consumers.
- **The subpackage name `test`.** Rejected: `django_strawberry_framework.test` shadows the stdlib-adjacent `test` name and collides with collection of a package so named.

## Decision 10 — Coverage lives in the package test tree

Spec text: [Decision 10][spec-024-d10].

### Derivation

The failure is Django test-class setup/teardown behaviour and is not reachable through a live `/graphql/` query, so the [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" preference does not apply and its documented fallback does. The bug sits below the GraphQL API layer; the example project stays useful as fixtures.

No `FAKESHOP_SHARDED=1` gate, because the hardening protects every consumer rather than only multi-database ones. Running the same focused scope under the sharded mode is still worthwhile — it is the only mode configuring more than one alias, which is the condition upstream wraps disallowed methods for — but it is an extra run of the same tests, not a separate suite.

### Alternatives considered (and rejected)

- **Live `/graphql/` coverage in `examples/fakeshop/test_query/`.** Rejected: no query can reach `tearDownClass` of a Django test case.
- **A hardcoded copy of Django's upstream body inside the negative test.** Rejected: the negative test's job is to prove the bug is real at the installed Django *and to stop proving it* when upstream fixes it — a retirement signal. A hardcoded copy would keep crashing no matter what the installed Django ships, so it could never deliver that signal. The test reverts to the live import-time capture and first asserts the captured descriptor's `__func__.__module__` is `django.test.testcases`, so its premise is checked before its conclusion.

## Decision 11 — Joint `0.0.7` cut

Spec text: [Decision 11][spec-024-d11].

### Alternatives considered (and rejected)

- **A separate `0.0.8` cut for this card.** Rejected in favour of the joint cut under [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-020-decision-10--joint-007-cut]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-024]: ../spec-024-django_trac_37064_hardening-0_0_7.md
[spec-024-d1]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-1--a-private-patch-module-per-dependency-applied-from-ready
[spec-024-d10]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-10--coverage-lives-in-the-package-test-tree
[spec-024-d11]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-11--joint-007-cut
[spec-024-d2]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-2--the-patch-installs-on-simpletestcase
[spec-024-d3]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-3--the-replacement-re-wraps-foreign-replacements-then-delegates
[spec-024-d4]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-4--fail-closed-upstream-validation-in-three-tiers
[spec-024-d5]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-5--two-homes-of-the-method-list-discriminated-by-the-feature-flag
[spec-024-d6]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-6--apply_upstream_patches-is-the-escape-hatch
[spec-024-d7]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-7--idempotent-self-healing-and-reload-safe
[spec-024-d8]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-8--the-wrap-time-half-degrades-where-the-unwrap-time-half-aborts
[spec-024-d9]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-9--the-helper-is-a-submodule-export-only

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
