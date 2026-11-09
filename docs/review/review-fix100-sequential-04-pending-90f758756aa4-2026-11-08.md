# Sequential scoped-fix review — commit 04 pending

**Open:** `90f758756aa449f159262aa25ccadd2dce506ceb`. The closed count remains **3 of 40**.

`fix(filters): a list or range filter over a path only the queryset resolves cleans its values (item 804)`

Fresh Terra 6.1 Medium fact-finding, Sol 6.1 Extra High adversarial review, three Sol High
implementation rounds and three fresh Sol 6.1 Extra High postfix reviews are recorded in the
[complete pending evidence][evidence]. The third postfix review accepts the independent repairs
at their recorded hashes and finds no further independent defect. It does not close this commit.

## Independent findings and corrections

| Finding | Source-derived defect | Current correction |
| --- | --- | --- |
| C04-F01, P2 | Continued aliases used inconsistent field paths and operations for cleaning, membership and ranges. | One actual queryset split supplies the terminal field and operation, including implicit exact. |
| C04-F02, P2 | Flat child filters lacked target-annotation cleaners; later attempts lost field ownership or derived irrelevant hooks. | Cached target context supplies inner cleaners while retaining owned outer fields; omitted reads derive no hook. Sync annotation preparation remains pending. |
| C04-F03, P1 | A reverse alias omitted its preparing lookup and could convert an extreme negative Decimal before holding its range. | Use the real reverse lookup registry and target column before integer coercion. |
| C04-F04, P2 | Resolving that reverse lookup exposed a stale concrete-field assertion on a late-applied alias. | Reuse the actual last-join compared-column seam and require a single integer target. |
| C04-F02-R04, P2 | A child constructor's harmless queryset clone falsely triggered refresh and discarded its inner validator. | Track the installed package context separately from the consumer's mutable queryset. |

The [base primitives][base] ask Django's query split, lookup registry and actual target fields.
[django_strawberry_framework/filters/sets.py::FilterSet._projection_child][sets]
preserves the child constructor and field state for an already
installed active context. The third review also checks the concurrent deferred-choice changes
at this commit's schema/form intersection; it finds no independent intersection defect.

## Required lifecycle decision

[Spec 027 Decision 8][spec] states that a sync flat hook's misuse error occurs at the `.qs` read,
“after the permission pass and form validation.” Its step-8 derivation also places ordinary
sync flat target hooks there. The queryset-only cleaning promise includes annotations known
only after the target type's actual `get_queryset` returns.

The authenticated installed and minimum-supported [Django form implementation][django-form]
cleans fields before it calls consumer `Form.clean`. It cannot provide the actual annotation
cleaner before that hook runs while also invoking the hook only after form validation.
Reordering or repeating consumer form validation would change supported semantics.

The maintainer question is pending: allow only a necessary hook-only annotation target to be
derived after permission checks and before field/form validation, retaining post-validation
hooks for ordinary model-resolved flat filters. This would explicitly move that necessary
annotation hook's sync-misuse phase. No answer or contract amendment is assumed.

After that choice, the dependent preparation and a true base-built child promoted to active
context still need implementation, live regression source and a fresh final review. Existing
sync annotation cases can fail until then. Commit 05 has not been dispatched.

## Regression source and checks

The [apply-arguments module][apply-tests] adds real HTTP source for flat/nested annotations,
constructor widget and validator ownership, omitted/null/empty inputs, async hooks, cloned
child context, logical arms, ordinary sync error ordering and completely replaced/no-inner
form fields. The [scalar module][scalar-tests] covers continued/direct aliases, implicit exact,
reverse extreme/mixed membership and handed/late reverse aliases. The [raw module][raw-tests]
covers package and plain django-filter parents through actual QueryDict forms. An existing
[package ownership assertion][set-tests] was updated for declaration-specific child keys.

Ruff, explicit-path layout, full default/floor basedpyright and diff checks pass. The private
final-population ledger checks 645 files, including all five earlier untracked modules:
699 type-ignore comments, 103 casts, zero violations. All 216 current source citations resolve.
One added `A002` lint exemption is disclosed; the second implementation report's zero count
was corrected explicitly in the third report. No type suppression or cast grew.

**No behavioral tests or probes ran.** Runtime results, coverage and the version/backend matrix
remain unverified. Source-level assertions and static green checks do not make this commit
complete. Original immutable database comparison found unchanged schema and only glossary row
463's body changed. No source database, generated glossary/tree or CHANGELOG edit was made.

The original 100-commit selection is fixed. Concurrent maintainer commits through
`0726d6020360d6df532bbb8d4c302e51b3e356a8` and all other work are preserved. Authored,
concurrent-base and combined patches have separate authenticated provenance.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[evidence]: ../../.work/evidence/fix-fix100-review/review-records/review-fix100-sequential-04-pending-90f758756aa4-2026-11-08.json

<!-- docs/SPECS/ -->
[spec]: ../SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/filters/base.py
[sets]: ../../django_strawberry_framework/filters/sets.py

<!-- tests/ -->
[set-tests]: ../../tests/filters/test_sets.py

<!-- examples/ -->
[apply-tests]: ../../examples/fakeshop/test_query/test_filter_apply_arguments_api.py
[scalar-tests]: ../../examples/fakeshop/test_query/test_scalar_predicate_binding_api.py
[raw-tests]: ../../examples/fakeshop/test_query/test_raw_filter_forms_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[django-form]: ../../.venv/lib/python3.14/site-packages/django/forms/forms.py

<!-- External -->
