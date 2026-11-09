# Commit 07 timing approval correction

Commit 07 remains open; six of the forty selected commits are closed. The maintainer has
approved the timing choice, and implementation is continuing. Commit 08 has not started.

The earlier record incorrectly extended pre-clean approval to annotation leaves whose
consumer value fields were already complete. The [exact replies][approval] supersede that
interpretation and the waiting-for-input statements in the [earlier packet][history].

Supplied complete-field values and values first introduced by consumer cleaning use one
post-clean bind phase. Only active annotation leaves acquire a new source; inactive fields
make no hook call. Field errors precede a new uncached bind-only hook or misuse error.
The annotation-owning hook runs once per request and database alias, with its result reused
by binding and application.

The [source reconciliation][design] distinguishes source needed to build a genuinely missing
automatic inner cleaner from source needed only for binding. Existing nested step-3 behavior
and genuinely necessary cleaner preparation remain explicit. Complete native fields, owned
inner cleaners, whole-value consumer fields and complete disabled initials join the unified
post-clean phase after the entire consumer `full_clean`, including post-super work.

Native django-filter `.qs` still applies surviving cleaned values when a form has errors.
The implementation must therefore prevent an unresolved deferred annotation leaf from
invoking a new hook during a later invalid raw `.qs` read, while preserving safe partial
siblings. Existing local or cached-source bind refusals can still join ordinary errors
without a new hook. Async source acquisition must await outside the worker and finalize
the same form without a second consumer clean.

This records the approved correction and source plan. It does not claim that the revised
phase has been implemented or verified. The [standing spec][spec] and regression sources
will be updated and independently reviewed before this commit closes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[approval]: ../../.work/evidence/fix-fix100-review/review-records/review-fix100-sequential-07-phase-correction-d6e19b74ea77-2026-11-08.json
[design]: ../../.work/evidence/fix-fix100-review/review-records/review-fix100-sequential-07-phase-correction-d6e19b74ea77-2026-11-08.json
[history]: review-fix100-sequential-07-pending-d6e19b74ea77-2026-11-08.md

<!-- docs/SPECS/ -->
[spec]: ../SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
