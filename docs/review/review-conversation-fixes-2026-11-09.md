# External review follow-up — 2026-11-09

This closes the findings returned against the [conversation handoff][handoff]. The original
40-commit audit remains paused; commit 08 has not started. This pass fixes and verifies the
accumulated changes rather than continuing that audit.

## Changes

| Review rows | Result |
| --- | --- |
| B1, M1 | Bare runtime Django field construction and a checker-only lookup alias work without the stubs monkeypatch. The static gate also detects executable Django subscripts. |
| M2 | Class names, exact-type membership and instance-local subtype changes follow the truthful-read rules. |
| m1 | Removed the obsolete query-value guard and its dead branches/tests; actual compiler guards own uniqueness binds. |
| F1 | The exact cached consumer form participates in FilterSet-owned text preflight, native cleaning and held binding. Plain forms retain their own validation policy. |
| F2 | Reused generated forms retain the outer clean owner even when native cleaning takes the unchanged route. |
| F3, F4 | Only genuinely missing package parsers prepare early, using the actual form route, widget value and disabled initial. Consumer parsers and empty values retain native timing. |
| F5 | Async acquisition and readiness use the constructed instance's database alias. Both complete-field and missing-parser sharded requests terminate. |
| F6 | Native absent-leaf noop decisions prevent unused annotation hooks. Ordinary supplied-empty leaves retain their existing hook timing. |
| F7 | Default invalid roots stop before arm construction; public validation policies that accept selected errors continue through the logical domain and postclean binding. |
| T1–T7 | Canonical model annotations, real HTTP change-detection tests, independent converter observations, native DRF decisions, public field configuration, corrected docstrings and meaningful empty-value expectations. |

The independent follow-up also found and fixed compiler provenance left behind by Django's
`EmptyResultSet` / `FullResultSet` shortcuts. A discarded integer operand can no longer be
mistaken for an equal surviving Decimal parameter. Native DRF supplies the acceptance and
uniqueness controls in the new HTTP rows.

Nested serializer agreement now uses the owning serializer's model and optional-field
configuration. Uniqueness source maps use DRF's own source spelling for each validator family.
The live rows cover schema/runtime agreement, dotted nested sources, fitting and refused
values, duplicate values and independent parent/child optional declarations.

Executing the scope-06 controls uncovered an inherited-source SQL defect that source review
had missed. The relation view now scopes its identity turn with native `Exists` and follows
an inherited forward key with an ordinary nullable join, avoiding Django's repeated parent
join for a multi-hop filtered alias. The full source primary-key components remain compared.
All 442 relation-view HTTP cases pass.

The final filter pass also preserves lazy database routing, ordinary supplied-empty hook
calls and the actual terminal path used by async acquisition. Huge reverse-relation operands
retain native `RelatedExact` behavior; their control asks the corresponding one-past-range
outcome instead of assuming an empty result. Private metadata tests now select the actual
hop-owned child and verify reuse without assuming the former class-only cache key.

## Verification and cleanup

Targeted pytest was explicitly authorized after the external review. Tests run only in
isolated copies with their own environments. Every pre-commit hook runs against each carved
tree, including both type-check configurations, installed public-type completeness, truthful
reads, executable/annotation subscripts and the metadata/spec/citation gates. Final receipts
and candidate tree hashes are preserved under `.work/evidence/fix-fix100-review/`.

Independent Sol 6.1 Extra High source reviewers checked the serializer and filter fixes;
implementation used Sol High agents. Source-review acceptance and executed tests are recorded
separately. PostgreSQL-only rows skipped in the SQLite runs; the full suite, coverage gate and
version matrix remain CI work.

The three coherent groups are serializer/decimal/numeric changes, inherited/composite relation
views, and the remaining filter changes with these review records. Ready hunks are carved
into isolated indexes. No stash, branch switch or unrelated working-tree cleanup is needed.
The foreign item-748/751 handoff in the bug-hunt document stays outside these commits.

The durable evidence replaces the former temporary location. Bulky companion JSON is archived
byte-for-byte in `.work/evidence/fix-fix100-review/review-records/`, with a SHA-256 manifest;
the Markdown records remain versioned. The response working note is removed once the fixes
are ready. Historical reports and the original handoff describe their recorded snapshots,
not the final tree's test status.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[handoff]: review-conversation-handoff-2026-11-09.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
