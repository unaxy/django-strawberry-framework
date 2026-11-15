# Rationale: spec-024 — Django Trac #37064 and `safe_wrap_connection_method` (derivation, rejected alternatives)

Deliberative companion to [`spec-024-django_trac_37064_hardening-0_0_7.md`][spec-024]. The spec is the contract and states what the code does; this file carries the derivation behind each Decision and the alternatives each rejected.

## Decision 1 — The helper declines to clobber Django's wrapper

Spec text: [Decision 1][spec-024-d1].

### Derivation

The wrap site is the one lifecycle point this package can influence cheaply: declining costs one `isinstance` and installs nothing. It is unavoidably advisory — the package cannot make third-party wrappers call it — and Django's own `wontfix` position on Trac #37064 puts the restoration on whoever replaced the wrapper, which is the contract the helper's docstring states.

### Alternatives considered (and rejected)

- **Restore the original method on the consumer's behalf.** Rejected: restoration needs the original, the ordering, and the teardown hook, none of which the helper owns. The docstring carries the worked `setUp` / `tearDown` shape instead.
- **Interpolate the offending object into the `TypeError`.** Rejected: the object is consumer-supplied and a `__repr__` that raises would replace the intended `TypeError` with whatever it raised. The diagnostic loses the object's identity deliberately.

## Decision 2 — The helper is a submodule export only

Spec text: [Decision 2][spec-024-d2].

### Derivation

The package's general posture is zero public-export change per card. A public surface is nonetheless correct here: the sibling multi-database card needed no new symbols because the cooperation it pinned already existed in source, whereas Trac #37064 is a bug in Django that consumers meet in their own test code, so the value-add *is* a helper they can write defensive `setUp` code against. The submodule path is the compromise: opt-in by import, invisible to anyone who does not want it.

### Alternatives considered (and rejected)

- **Re-export from `django_strawberry_framework/__init__.py`.** Rejected: a test-only helper does not belong on the package's front page, and the root `__all__` is the package's whole public surface.
- **Ship no public symbol at all.** Rejected per the derivation: it leaves consumers nothing to cooperate with.
- **The subpackage name `test`.** Rejected: `django_strawberry_framework.test` shadows the stdlib-adjacent `test` name and collides with collection of a package so named.

## Decision 3 — Coverage lives in the package test tree

Spec text: [Decision 3][spec-024-d3].

### Derivation

The helper acts on Django test-class setup/teardown state and is not reachable through a live `/graphql/` query, so the [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" preference does not apply and its documented fallback does. The example project stays useful as fixtures.

### Alternatives considered (and rejected)

- **Live `/graphql/` coverage in `examples/fakeshop/test_query/`.** Rejected: no query can reach `tearDownClass` of a Django test case.

## Decision 4 — Joint `0.0.7` cut

Spec text: [Decision 4][spec-024-d4].

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
[spec-024-d1]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-1--the-helper-declines-to-clobber-djangos-wrapper
[spec-024-d2]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-2--the-helper-is-a-submodule-export-only
[spec-024-d3]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-3--coverage-lives-in-the-package-test-tree
[spec-024-d4]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-4--joint-007-cut

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
