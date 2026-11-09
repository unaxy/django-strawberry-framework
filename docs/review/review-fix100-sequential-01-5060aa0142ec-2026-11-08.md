# Sequential commit review 01 — 5060aa0142ec

**Closed at source-review level.** Three original diagnostic defects fixed; three implementation rounds and three fresh postfix reviews completed. No later commit was started before this closure.

## Scope and workflow

Commit `5060aa0142ec507be444534e37ddc9b5219e16b8`: `fix(filters): a filter declared over a field no SCALAR_MAP entry covers is refused in the FilterSet’s words (item 730)`.

Fresh Terra 6.1 medium fact-finding was followed by a fresh Sol 6.1 Extra High adversarial review, Sol High implementation, and fresh Sol 6.1 Extra High postfix agents. The first two postfix passes required corrections; the third accepted the combined patch. The earlier batched audit was superseded and was not used as evidence for this restart.

The [full evidence bundle][evidence] preserves the fact report, original findings, all implementation and postfix rounds, final source fingerprints, and actual static-check results. Findings follow the [trust boundary][trust-boundary] and precise [filter contract][filter-spec].

## Original findings and repairs

- **C01-F1 — GeneratedField output bypass.** Output-specific validation could raise before the new FilterSet refusal, naming no filter and recommending `Meta.exclude`, which does not remove a declared filter. Neutral generated-column discovery now feeds a shared output-policy classifier; filter publication and active unserved requests apply it with original declaration context. Unsupported file/image and array-choice outputs remain refused; valid mapped transforms retain their types.
- **C01-F2 — Inapplicable relation remedies.** Advice did not account for scalar requirements, distinct target primary and joined `to_field` columns, registered Relay alternate `NodeID`s, composite identities, or consumer generation hooks. Diagnostics now distinguish the routes and ask the same effective-origin/shape-capability verdict used by native generation. Consumer selection remains intact; optional generated advice is withheld when native selection cannot establish it.
- **C01-F3 — Projected crossing namespace.** A projected child could combine a walked child path with a pre-crossing field and recommend nonexistent `branch__branch` paths. Operand resolution now follows the original declaring child; field, remedy path and provenance agree while method-owned and request-instance behavior remain preserved.

The production changes are in the [filter base][filter-base], [input conversion][filter-inputs], [FilterSet generation/request paths][filter-sets], [type converter policy][converters], and [generated-column metadata][relations].

## Verification and regression controls

The first postfix pass caught an introduced unbound-transform crash, an unserved-request policy gap, incomplete Relay advice, stale assertion strings, and an HTTP control that exercised JSON rather than generated input. The second accepted those corrections and caught the remaining public generation-hook precedence gap. These were implementation-review issues, not additional defects attributed to the historical commit. The third independently accepted all findings and root verification questions at the recorded source hashes.

[Public construction regressions][input-tests] cover unsupported computed outputs, mapped controls, projected child provenance and method semantics, target-pk versus joined-column prerequisites, composite/alternate Relay ids, and custom/delegating generation hooks. [Existing generation assertions][set-tests] now expect the intended contextual errors. [Generated metadata controls][relation-tests] cover unbound transform output handling. [Live JSON request controls][apply-tests] cover unserved generated sources and ordinary-duration controls. The [typed projected HTTP control][typed-tests] binds `Meta.filterset_class` and `FilterInput`, uses a discriminating child constructor customization, and exercises the actual input-typing path.

Fact-finding compared the two committed source database blobs read-only: 99 non-internal tables had identical schemas; only two glossary rows changed, solely in their bodies, matching the rendered documentation. No application database was modified.

## Checks and limits

- Repository Ruff check and format: passed.
- Explicit source-layout checks: passed.
- Full default and floor basedpyright: zero diagnostics in both.
- Type-suppression ledger: passed; no growth.
- `git diff --check`: passed.
- All eleven final source fingerprints and scoped diff matched the accepted implementation.
- No tests, schema/app runtime probes, database writes, builds, or runtime version matrix were executed. Regressions are added but unrun under the repository’s explicit rule.

Changes remain uncommitted on `main`. The seven inherited implementation paths from the rejected audit were preserved and are not claimed reviewed by this commit’s closure.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[trust-boundary]: ../../GOAL.md#trust-boundary

<!-- docs/ -->
[evidence]: ../../.work/evidence/fix-fix100-review/review-records/review-fix100-sequential-01-5060aa0142ec-2026-11-08.json

<!-- docs/SPECS/ -->
[filter-spec]: ../SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filter-base]: ../../django_strawberry_framework/filters/base.py
[filter-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filter-sets]: ../../django_strawberry_framework/filters/sets.py
[converters]: ../../django_strawberry_framework/types/converters.py
[relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[input-tests]: ../../tests/filters/test_inputs.py
[set-tests]: ../../tests/filters/test_sets.py
[relation-tests]: ../../tests/utils/test_relations.py

<!-- examples/ -->
[apply-tests]: ../../examples/fakeshop/test_query/test_filter_apply_arguments_api.py
[typed-tests]: ../../examples/fakeshop/test_query/test_scalar_predicate_binding_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
