# Sequential scoped-fix review — commit 07 pending

**Open:** `d6e19b74ea77e90a929e871d1db4ed1fa60512e8`. The closed count remains **6 of 40**.

`fix(filters): raw filter forms refuse what the typed input refuses (items 724, 743)`

Fresh Terra 6.1 Medium fact-finding, Sol 6.1 Extra High adversarial review, eight Sol High
implementation rounds and eight fresh Sol 6.1 Extra High postfix reviews are preserved in the
[complete evidence][evidence]. The latest review accepts the independent source repairs at
their recorded hashes. One required lifecycle decision remains; this commit is not closed.
Commit 08 has not started. Original JSON reports are archived verbatim with their hashes;
authored patches and concurrent changes remain separate.

## Independent repairs

| Finding | Defect | Source correction |
| --- | --- | --- |
| F07-01, P2 | Reusing a generated form as `Meta.form` could fail its MRO or run stale/duplicate asks. | One current owner encloses the entire consumer clean, including post-super work; inherited owners delegate. |
| F07-02, P2 | Native change detection could raise a known widget refusal before form error handling. | Share the actual form route, recover only its owned widget refusal, and retain unbound/unchanged delegation. |
| F07-03, P2 | Flat annotations could lose their actual final query, cleaner, source dependency or cached field enrichment. | Follow every hop, prepare only a necessary owner, preserve consumer fields, and use actual terminal rows through validation and application. |
| F07-04, P2 | Raw tuple members bypassed unstorable-text checks. | Traverse accepted tuple/list/dict contents before field cleaning, preserving empty and omitted semantics. |
| F07-05, P2 | Field identity and incomplete source context misclassified integer transforms and stored generated columns. | Native transform nodes/start expressions and the actual query govern classification; the actual shipped list/range predicate owns the bind question. |

The [form owner][binding], [pipeline and source map][sets], [native filter primitives][base]
and [text walker][errors] retain native consumer ownership. Ordinary stored integer, `F`,
`Count` and generated-column members keep their dropping behavior; genuine transform members
reach the bind ask. Package integer ranges retain their actual `gte` / `lte` construction;
native CSV ranges keep their numeric predicate. Intermediate regressions, corrected assertions
and report wording errors remain explicit in the evidence rather than being overwritten.

## Approved annotation timing

The supplied-value sync amendment is implemented in all five required [Spec 027 homes][spec],
with the additional comparison-table clarification. On `apply_sync`, a nested branch remains
at step 3; a necessary flat annotation owner runs after the permission pass and before form
cleaning; other flat leaves remain at step 8. A sync denial calls no flat annotation hook.
Validation and `.qs` reuse one owner-and-alias cache entry. Only the final owner runs early;
earlier hops retain their timing unless independently needed. On that necessary sync path,
`SyncMisuseError` precedes invalid-input `FILTER_INVALID`.
Async supplied flat hops retain their existing preawait timing.

Known disabled initial values are discoverable before cleaning. They use the same source
preparation, including native filters whose complete parsers still need actual query context.
Async preparation awaits outside the worker and finishes the same form once. These cases are
separate from the decision below. The supplied-value approval is not being requested again.

## Required decision: values first introduced by consumer cleaning

A supported `Meta.form` can add an active annotation value absent from the input. The concrete
case declares both `label` and its own native CSV duration filter `lag_among` over `partner__lag`.
The registered target type adds the duration annotation in `get_queryset`. Input
`{"label": {"exact": "of-child"}}` supplies no duration, while consumer `Form.clean` adds
`lag_among = [timedelta(days=999999999)]`. The raw equivalent supplies only `label=of-child`.

The corrected public shape and full sync/async/raw source trace are in the evidence. Before
consumer cleaning there is no active value to identify; afterward the annotation source is
still uncached. The later query can therefore escape form-owned refusal. This production
contract issue remains open, established by the documented source trace.

The existing three timings, inactive-zero-hook behavior and arbitrary consumer activation
cannot all be retained. The pending choices are:

1. **Post-clean hooks only for newly active values (recommended):** retain zero calls for
   inactive filters and explicitly add a fourth timing for this case.
2. **Prepare potential annotation fields before cleaning:** retain three timings and allow
   calls for fields that ultimately stay inactive.

The choice remains pending. The dependent source finalization and regression rows still
need implementation and fresh verification. A post-clean choice must keep one form/consumer
clean, await outside async workers, and combine ordinary and bind errors on that same form.

## Evidence and verification limits

The [apply source][apply-tests] covers actual multi-hop/scoped/declared annotations,
permissions, one hook, ordinary-late timing, initial values, consumer policies and ownership,
methods, integer transforms and exact rows/errors. The [raw source][raw-tests] and
[widget source][widget-tests] cover raw form reuse, actual readers, tuple text, lifecycle and
error unions. The [generated-column source][generated-tests] retains the existing public
mixed/all-huge acceptance row and adds declared List/Array and same-instance raw controls.
These are live HTTP test sources; they were not executed.

Ruff, explicit-path layout, full default/floor basedpyright, source citations, diff checks and
the private-population suppression ledger pass. The ledger checks 647 Python files with
699 ignore comments, 103 casts and zero violations. All nine independent source hashes match.
Required generated TREE/GLOSSARY parity passes against an isolated read-only-source metadata
backup and genuine private Git index/object store. The shared index is unchanged during that
operation. No behavioral test, coverage gate or backend/version matrix result is claimed.

The original 100-commit selection remains fixed. Concurrent maintainer work through
`3714f49565dcb6ff33fe2be36a7f3b505d573ea1` and earlier source drift is separately authenticated
and preserved. No branch, commit, stash, shared database or unrelated source was changed by
this publication. Earlier review artifacts remain intact.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[evidence]: ../../.work/evidence/fix-fix100-review/review-records/review-fix100-sequential-07-pending-d6e19b74ea77-2026-11-08.json

<!-- docs/SPECS/ -->
[spec]: ../SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/filters/base.py
[binding]: ../../django_strawberry_framework/filters/form_binding.py
[sets]: ../../django_strawberry_framework/filters/sets.py
[errors]: ../../django_strawberry_framework/utils/errors.py

<!-- tests/ -->

<!-- examples/ -->
[apply-tests]: ../../examples/fakeshop/test_query/test_filter_apply_arguments_api.py
[raw-tests]: ../../examples/fakeshop/test_query/test_raw_filter_forms_api.py
[widget-tests]: ../../examples/fakeshop/test_query/test_filter_widget_binding_api.py
[generated-tests]: ../../examples/fakeshop/test_query/test_library_generated_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
