# Conversation changes and code-review handoff — 2026-11-09

**Historical pre-review snapshot.** The [external-review follow-up][follow-up] records the
subsequent fixes, executed verification and corrected cleanup plan. The counts and source
pins below describe the handoff's original state.

**This working tree is not ready to commit.** Six historical commit scopes completed source
review. Commit 07 has a frozen ninth implementation and an interrupted adversarial review
with five reported defects. No work on commit 08 began. The original audit remains paused.
This document consolidates the conversation for an independent review of the accumulated
changes; it does not certify the combined current tree.

This document records the pre-review state. The external review has since been returned for
implementation. Its correction supersedes the original stash plan: carve ready changes into
a private index and leave unrelated work in place. Targeted pytest in isolated copies is
explicitly authorized. The maintainer authorized committing the reviewed changes on the
current branch; creating or switching branches is not authorized.

## Review scope and exact starting state

Repository: `.` (the repository root).
Branch: `main`. HEAD: `3714f49565dcb6ff33fe2be36a7f3b505d573ea1`.

Before adding this handoff, the checkout contained **59 dirty paths: 32 modified tracked files
and 27 untracked files, with nothing staged**. The tracked diff against HEAD had 9,014
insertions and 829 deletions. Those figures exclude untracked content. This handoff adds one
document, and the existing review index receives a narrow status/link update.

A later reconciliation during preparation observed **63 dirty paths: 35 tracked modifications
and 28 untracked files**, still with nothing staged and the same HEAD. Three previously clean
paths became dirty concurrently: `examples/fakeshop/test_query/test_direct_filter_actor_api.py`,
`scripts/work.py` and `tests/test_work.py`. They were not edited for this handoff and are outside
its authored-change/commit scope. All original 59 file hashes stayed unchanged except the intended
review-index edit. The detailed inventory tables below retain their explicit starting scope.

Review both the tracked diff and the six untracked source/test/license files listed below.
An ordinary `git diff HEAD` omits those new files, including both new serializer guard modules.
Recheck HEAD and file contents before editing: this is a concurrently used checkout.

The two read-only summary agents reconstructed the historical changes and independently
inventoried every dirty path. Their detailed JSON, initial file hashes and metadata are in
`.work/evidence/fix-fix100-review/dsf-conversation-review-handoff-20261109/` as `history-summary.json`,
`worktree-inventory.json` and `worktree-start.json`. This document contains the consolidated
review context; those files provide additional provenance on this machine.

## How this work developed

The original request was to inspect the last 100 commits, selecting subjects starting with
`fix(scope):`, with Terra 6.1 Medium fact-finding, Sol 6.1 Extra High adversarial review and
Sol High implementation. The fixed selection was made at
`5060aa0142ec507be444534e37ddc9b5219e16b8` and contained 40 matching commits.

The maintainer rejected an initial batched audit and required a restart with **one commit
through the entire process before the next**. The restart also used fresh postfix reviewers
after implementations and repeated that step when source defects remained. The rejected batch's
two reports remain historical artifacts; their correctness conclusions were not used to close
the sequential scopes. Nothing in this handoff claims all 40 commits were reviewed.

At the restart, seven implementation paths were already dirty from the earlier attempt:
the serializer resolver and spec, scalar schema and serializers, live-test README and scalar
mutation tests, and package serializer resolver tests. Those files were preserved. Commit 01
did not certify them; later serializer and numeric reviews independently checked the relevant
inherited changes.

The [sequential index][index] links the per-commit reports. Each report's companion JSON
contains the corresponding detailed evidence and historical hashes. An old acceptance applies
to its recorded source, not automatically to a file modified again by a later audit round.

| Scope | Original commit | Subject area | Implementation / completed fresh postfix rounds | State |
| --- | --- | --- | --- | --- |
| 01 | `5060aa0142ec` | Unsupported filter output diagnostics, item 730 | 3 / 3 | Source review accepted |
| 02 | `13982ba895f2` | Nested serializer uniqueness binding, item 810 | 3 / 3 | Source review accepted |
| 03 | `0dcc88c6f15b` | SQLite decimal read-back, item 726 | 3 / 1 | Source review accepted |
| 04 | `90f758756aa4` | Queryset-only list/range comparison fields, item 804 | 6 / 6 | Source review accepted at that stage |
| 05 | `059a66175f52` | Numeric endpoint and uniqueness evidence, item 725 | 2 / 2 | Source review accepted |
| 06 | `6cd57b127bd2` | Inherited/composite relation-view identity, item 807 | 2 / 2 | Source review accepted |
| 07 | `d6e19b74ea77` | Raw filter-form refusal parity, items 724/743 | 9 / 8; ninth review interrupted | Open; five reported issues below |

All changes described here remain uncommitted by this audit. No branch was created or switched.

## Implemented changes from the six completed scopes

### 01 — Contextual filter refusals and valid remedies

The [commit 01 report][review-01] records three original diagnostic defects. A generated
column's unsupported output could raise before the FilterSet-aware refusal, omit the declaration
and recommend `Meta.exclude` even though that does not remove a declared filter. Relation advice
also conflated a joined `to_field`, target primary key and Relay identity. Projected child paths
could combine incompatible namespaces and recommend a nonexistent doubled relation path.

The changes separate neutral generated-column discovery from output policy, then apply the
shared policy with the original FilterSet/declaration context at publication and active unserved
requests. Advice follows the same effective generation-policy and shape-capability seams as
generation, including registered alternate NodeIDs, composite identities and consumer generation
hooks. A projected operand resolves on its actual declaring child. Valid mapped transforms and
consumer-selected filters retain their behavior.

The principal files are [filter base][filter-base], [input conversion][filter-inputs],
[FilterSet generation][filter-sets], [type converters][converters] and
[generated-column metadata][relations]. Regression source covers unsupported outputs, valid
transforms, provenance, method ownership, target-PK versus joined-column requirements and
consumer hooks. The typed HTTP control actually publishes `FilterInput` through a public
`Meta.filterset_class`; separate JSON controls exercise unserved request behavior.

### 02 — Guard the uniqueness query DRF actually executes

The [commit 02 report][review-02] records six active finding groups and independent retention
of the inherited read-only-default fix. A predictive scan could inspect values before prior
validators normalized them, model DRF's required/null/change decisions incorrectly, confuse
validation defaults with writes, miss actual lookup preparation or use the wrong database alias.

The implementation replaces that prediction with instance-local query/compiler guards:

- `django_strawberry_framework/rest_framework/query_bind.py::guard_query` follows actual Django
  preparation and compilation, retaining source attribution and checking parameters that survive
  into executable SQL. Empty or eliminated predicates retain native behavior.
- `django_strawberry_framework/rest_framework/validator_guard.py::guard_uniqueness_validator`
  keeps the original DRF call, validator order, current attrs, instance fallback and nested
  ownership. Copied validator querysets are pinned to the write alias.
- `django_strawberry_framework/rest_framework/resolvers.py::_hold_serializer_values` integrates
  the guards while distinguishing root storage checks from values actually queried by validators.

Query binding and storage range are separate questions. The implementation distinguishes native
SQLite driver integer limits, PostgreSQL typed/client parameters and integer-array selection,
and DRF's recoverable psycopg list-adaptation errors. A narrow `Q.check` adaptation is needed
because that upstream method has no query-injection seam; it preserves the inspected Django
version differences, names its origin and uses the existing Django license text.

Two new [ordinary][serializer-live] and [sharded][serializer-sharded] HTTP modules cover the
public Meta mutation path, fitting duplicates, nested error paths, no-write outcomes, actual
annotations/iterable operands, eager preparation, eliminated queries, prior normalization,
conditional constraints and the selected write alias. Scalar schema/serializer fixtures and
existing package tests support these cases. No global compiler/connection patch was introduced.

### 03 — Reproduce SQLite's real column-name conversion

The [commit 03 report][review-03] identifies a false refusal in the decimal storability trial.
Its scratch column was renamed to `value`, which lost SQLite's configured column-name conversion
for a real `db_column` such as `amount [decimal_text]`. The real ORM read could succeed where
the trial received a float and rejected the input.

`django_strawberry_framework/utils/errors.py::_refused_read_back` now quotes and preserves the
actual bound column name in both native CREATE and SELECT. Existing save preparation, native
driver conversion and Django's backend converters remain in the trial. An older expected-value
test now derives its result from independent native ORM read-back instead of assuming one
engine's decimal precision behavior.

The new [column-name HTTP module][decimal-live] contains 12 parameter cells across model,
ModelForm and serializer create/update, with fitting/boundary values, exact errors and persisted
value checks. It restores its transient tables and global converter state. A narrow SQL lint
exemption concerns a trusted quoted identifier; values remain bound parameters. It is distinct
from type-suppression growth.

### 04 — Resolve list/range cleaners from actual queryset operands

The [commit 04 report][review-04] covers continued annotation aliases, reverse aliases and
projected child contexts. Cleaning and integer holding previously used inconsistent path,
output-field and lookup resolutions. A reverse alias could omit the preparing lookup and
convert an enormous negative Decimal before applying the safe integer hold.

The base primitives now use the actual query's resolved operand and full terminal operation,
including implicit exact. Reverse relations use their native compared target column, and holding
occurs before identity coercion. Missing list/range inner cleaners are installed without
replacing consumer fields, validators, widgets or existing inner fields.

`django_strawberry_framework/filters/sets.py::FilterSet._projection_child` retains the actual
per-hop child and its constructor restrictions. Native PK-subquery membership carries those
restrictions into terminal filtering and outward correlation. Resolved annotation expressions
are not transplanted into unrelated query plans. The request-wide declaration/database cache
continues to own target visibility.

Live source covers actual annotation and reverse-transform spellings, extreme values,
permissions, one hook across validation/application, earlier-hop timing, materialized field
ownership, methods, constructor restrictions and genuine child promotion. One review explanation
was corrected openly: Django's field deepcopy does not recursively clone the custom
`RangeField.bound_field`; the regression explicitly replaces its owned inner field.

**The later policy correction in commit 07 supersedes broad older timing prose.** The original
early-source exception remains necessary only for a genuinely missing automatic parser. Complete
consumer fields use the post-clean phase described below.

### 05 — PostgreSQL numeric endpoint and a discriminating query test

The [commit 05 report][review-05] records an inherited false refusal at the zero exponent
endpoint `0E+1073741823`: the inspected PostgreSQL 14/15 behavior rejects it, while 16+ accepts
and normalizes it. The shared numeric rule now asks the real connection's database-version
seam only at that exact endpoint. Values below retain their acceptance; `0E+1073741824` remains
refused. No setting or ordinary-value version lookup was added.

Django exposes no native server numeric-parser preflight. The narrow adapted endpoint rule names
its PostgreSQL origin and ships [LICENSE.postgresql][postgres-license], included in both
packaging lists in [pyproject.toml][pyproject]. The current pyproject diff is those two inclusion
entries, not a version bump.

The serializer fixture now declares a real amount/active `UniqueTogetherValidator`. A field
hook changes fitting input to a refused exponent, and a passive `execute_wrapper` records actual
query operands while forwarding execution. The forbidden value must not reach SQL; a fitting
duplicate must reach it and produce DRF's unique error. This distinguishes query guarding from
a later storage refusal. Adjacent-exponent native ORM controls, zero read-back and exact
create/update outcomes are present as unexecuted regression source. Package test expectations
and renamed test references in the two mutation specs were reconciled.

### 06 — Use the declaring relation's real identity

The [commit 06 report][review-06] records two relation-view defects. An inherited foreign key
could compare an ancestor's key with an independent child key. A composite source could turn
`F("pk")` into a `ColPairs` expression that native tuple lookup preparation rejects.

`django_strawberry_framework/filters/sets.py::FilterSet._relation_view` now reads the actual
foreign key's declaring model and its concrete `pk_fields`, then builds native scalar Q/F
comparisons for every component's `attname`. It uses neither the wrong child `pk` shorthand nor
an unsupported whole-composite expression. No copied upstream algorithm was needed.

The [relation-key live module][relation-live] adds 42 parameter cells spanning ordinary,
independent-child and composite shapes, sync/raw/async paths, absent/empty/named choices,
exclusion and exact visible-row results. Distinct explicit parent/child IDs and composite peers
make both missing comparisons observable. Temporary models are created in a function-local
factory with registry cleanup before transactional flush, protecting other deletion tests.

## Commit 07 — Current implementation, not accepted

The original commit is `d6e19b74ea77e90a929e871d1db4ed1fa60512e8`, concerning raw form refusal
parity with typed input. Eight prior review rounds accepted independent repairs at their own
hashes. R9 implements the latest timing correction and remains unaccepted.

The cumulative changes address these areas:

- Generated forms reused as later `Meta.form` classes need one current owner around the entire
  consumer clean, rather than stale callbacks, duplicate asks or an invalid MRO.
- Native `has_changed()` can itself read a widget and raise an owned refusal. The actual form's
  route and known widget error are retained; unrelated consumer errors still propagate.
- A flat annotation leaf must use its actual final source, declaring policy, constructor
  restriction and comparison field through the entire hop chain.
- Raw tuple/list/dict members are traversed for unstorable text before field cleaning.
- Real integer transforms must reach bind checking, while ordinary stored/generated integer
  columns, `F` aliases and `Count` retain native member dropping. Actual Transform nodes/start
  expressions replace the rejected field-identity heuristic. Package integer ranges ask their
  actual `gte`/`lte` predicate; native CSV ranges keep their own predicate.

R9 separates parser preparation from bind-only preparation in
`django_strawberry_framework/filters/form_binding.py::FilterFormAsks` and
`django_strawberry_framework/filters/form_binding.py::BindAskingFilterForm._ask_full_clean`.
The coordinator stages native cleaning and later binding on the same captured forms. It builds
the root and logical descendants before new bind-only hooks, and async awaits sources outside
the sync worker. Ordinary field errors suppress new uncached binding sources across that input.

Raw `.qs` requires special handling: native django-filter still applies surviving `cleaned_data`
when a bound form has errors. R9 records unavailable-source leaves in `_bind_unavailable_names`
so later application cannot resurrect their suppressed hooks, while safe local/cached partial
siblings remain usable. Logical branch reuse and legitimate constructor/queryset fallback must
carry the same suppression state.

### Latest approved timing and error order

The maintainer explicitly corrected the earlier claim that supplied complete fields were approved
for pre-clean hooks. Both actual answers are preserved in the [phase correction][phase-correction]
and its companion JSON. **No phase-policy answer is pending.** Older pending artifacts and
stale nested checkpoint strings must not override those answers.

| Case | Required source timing |
| --- | --- |
| Nested `RelatedFilter` derivation | Existing step 3, including its internal child pipeline |
| A genuinely missing automatic package list/range inner parser | Necessary owner after the applicable permission gate and before that native field clean |
| Complete native/consumer/owned-inner annotation fields | One bind phase after the entire actual consumer `full_clean`, with root and all logical forms natively valid first |
| Other sync flat leaves | Existing step-8 `.qs` application timing |

The complete-field phase handles supplied values, complete disabled initials, and values added,
repaired or removed by `Form.clean` or outer post-super work. Only actual active values need a
new bind-only owner. The owner's result is cached once per declaration/scope and database alias,
then reused by validation and `.qs`. Only the annotation-owning hop moves early unless a real
dependency requires another hop. Source preparation and bind questions must not execute SQL.

For complete fields, an ordinary invalid field comes before a new hook or its `SyncMisuseError`.
That includes an invalid later OR/AND arm: arm order must not change `FILTER_INVALID` into misuse.
Local or already-cached bind refusals may still join ordinary errors without acquiring a hook.
The genuinely missing-parser path can still encounter sync misuse before parsing. Ordinary
resolved async hops retain their established preawait. This is not a global promise that no
kind of hook runs before any error anywhere.

These rules are reflected in the five governing homes of [spec 027][filter-spec] and its
comparison discussion. They require one actual form/consumer clean, not a guessed parser,
trial clean, second constructor or later re-clean. A consumer's own `.form` override retains
its documented raw exception and typed validation fallback.

R9's added/updated live source covers invalid complete fields, unrelated errors, supplied and
clean-created values, repair/removal/inactivity, post-super work, complete versus missing-parser
initials, both logical arm orders, deep `not`/`and`, raw same-instance errors/validity/`.qs`,
safe partial siblings and hook counts. These tests have not run, and the following gaps remain.

### Five reported issues for the external reviewer

These are source-traced findings reported by the interrupted fresh reviewer, preserved in
messages and `root-r9-source-notes.json`. Its formal `verification-r9.json` was not completed.
They have not received another implementation pass. The labels below are handoff labels,
not invented final finding IDs from that unfinished report.

1. **H07-1: unchanged generated-form reuse binds before the outer consumer finishes.**
   In `BindAskingFilterForm._ask_full_clean`, the `route=False` path calls `clean()` without
   the active-owner guard used by `route=True`. A public `Meta.form` can reuse a generated form
   whose consumer adds a duration in post-super `full_clean`, then subclass it with an outer
   consumer that repairs/removes that duration after `super()`. On a direct raw unchanged bound
   form, the inherited owner can invoke the current binding callback before the outer repair.
   An async-only owner can raise misuse before outer continuation; a sync owner can leave a stale
   bind error/finalized flag. The pipeline's deferred callback avoids that particular raw escape.
   Required: the current owner surrounds the entire outer clean even on the unchanged route.

2. **H07-2: supported plain consumer forms fail before their fallback validator.**
   `FilterSet._finish_known_annotation_validation` unconditionally requires a
   `BindAskingFilterForm`; branch reuse also assumes that class. A supported `.form` property
   returning a cached plain `get_form_class()(self.data, prefix=...)` therefore TypeErrors on
   valid public `apply_sync`/`apply_async` input. The existing
   `tests/filters/test_base.py::_OwnFormYearSet` demonstrates that public shape, and
   `_validate_form_or_raise` still documents/implements its fallback. Native-only staging also
   reads that form's errors before the fallback's text preflight. Simply deleting the class
   requirement is insufficient if a model-choice cleaner can bind refused text first.
   Required: retain the actual own form, preflight order, custom validation policy and logical
   native-clean boundary without replacing the form or cleaning it twice.

3. **H07-3: a named missing-parser leaf can invoke a hook before the unchanged decision.**
   `_prepare_annotation_hops_sync` asks `_named_annotation_hops` before the native form route
   is consulted, and the named helper has no route guard. An empty-permitted form with a package
   `ListFilter(field_name="partner__lag", lookup_expr="in")` can set its actual initial to
   `["1 00:00:00"]` and receive exactly that list. With no installed inner parser, the native
   field's pass-through change comparison is unchanged and would clean no value. The typed
   preparation can nevertheless acquire the async-only owner and raise misuse first. Raw
   unchanged routing skips it. Required: respect the actual unchanged/no-added-value decision
   before unnecessary source work, retaining owned-widget refusal handling.

4. **H07-4: an owned complete range parser is classified by an unused empty slot.**
   `_needs_automatic_comparison` treats every package `RangeField` with `bound_field=None` as
   incomplete. A public `RangeField` subclass can own a complete `to_python`, returning native
   empties and cleaning both bounds through `forms.DurationField.clean`, without ever reading
   `bound_field`. A `RangeFilter` subclass using it still runs the shipped filter. On unresolved
   `partner__lag`, input with `start="not-a-duration"` should produce its native field error
   before any new owner. The current classifier instead acquires the owner pre-clean and can
   report sync misuse. Required: distinguish actual parser ownership from concrete field family
   and empty storage slots, preserving genuine automatic-inner preparation and consumer seams.

5. **H07-5: a native no-op choice value is treated as active merely because it is nonempty.**
   A shipped `MultipleChoiceFilter` subclass with `always_filter=False`,
   `field_name="partner__lag"`, `choices=[("one", "One")]`, `required=True`, `disabled=True`
   and `initial=["one"]` has a complete native field. Bound input `{}` cleans the disabled
   initial successfully. Native `MultipleChoiceFilter.is_noop` recognizes all choices selected
   and returns the input queryset by identity. Since the key is absent, the existing absent-leaf
   probe/application would derive no hook. `_postclean_binding_hops` instead treats the
   nonempty list as active and acquires the unresolved owner, yielding an extra call or sync
   misuse. Required: ask native shipped activity/identity semantics without probing arbitrary
   consumer filter overrides. Preserve established timing for ordinarily supplied hops.

## Dirty-file inventory and ownership

The following tables describe the **pre-handoff 59-path snapshot**. Scope numbers refer to the
table above. "07" means current cumulative source is unfinished; older repairs in those same
files must survive the next fix. Whole-file hash drift from an old closure is not sufficient
evidence of a new foreign uncommitted edit.

### Modified package source — eight files

| Path | Main work represented |
| --- | --- |
| `django_strawberry_framework/filters/base.py` | 01/04/07 operand, cleaner, transform and integer predicate behavior |
| `django_strawberry_framework/filters/form_binding.py` | 04/07 actual form ownership, widget route and deferred bind lifecycle |
| `django_strawberry_framework/filters/inputs.py` | 01 contextual output/refusal policy plus preserved committed input work |
| `django_strawberry_framework/filters/sets.py` | 01/04/06/07 generation, source/hop contexts, relation identity and pipeline |
| `django_strawberry_framework/rest_framework/resolvers.py` | Inherited then independently reviewed 02 serializer guard integration |
| `django_strawberry_framework/types/converters.py` | 01 neutral generated-output policy boundary |
| `django_strawberry_framework/utils/errors.py` | 02/03/05/07 query/storage, decimal and raw-text rules |
| `django_strawberry_framework/utils/relations.py` | 01 neutral generated-column metadata |

### Modified documentation/configuration — seven files

| Path | Main work represented |
| --- | --- |
| `docs/SPECS/spec-027-filters-0_0_8.md` | 01/04/07 contracts, latest approved timings, lifecycle and test references |
| `docs/SPECS/spec-038-form_mutations-0_0_12.md` | 05 renamed endpoint regression reference |
| `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | 02 actual validator/query rules and 05 endpoint references |
| `docs/TREE.md` | Required new module/test entries and preserved concurrent generated context |
| `docs/bug_hunt/bug_hunt-0_0_15_2.md` | **Mixed:** owned item-810 explanation plus another session's item-751 handoff |
| `examples/fakeshop/test_query/README.md` | 02/03/05/06 test index updates plus committed item-750 row |
| `pyproject.toml` | 05 PostgreSQL license inclusion in two lists |

### Modified example source/tests — nine files

| Path | Main work represented |
| --- | --- |
| `examples/fakeshop/apps/scalars/schema.py` | Inherited/02 nested uniqueness mutation exposure |
| `examples/fakeshop/apps/scalars/serializers.py` | Inherited/02 nested serializer fixture and 05 real uniqueness validator |
| `examples/fakeshop/test_query/test_filter_apply_arguments_api.py` | 01/04/07 public apply/annotation/lifecycle controls; current tracked diff adds 5,246 lines and removes 108 |
| `examples/fakeshop/test_query/test_filter_widget_binding_api.py` | 07 actual widget/change-detection refusal controls |
| `examples/fakeshop/test_query/test_library_generated_api.py` | 07 ordinary generated integer versus true Transform controls |
| `examples/fakeshop/test_query/test_raw_filter_forms_api.py` | 04/07 raw forms, generated reuse, tuple text, partial application |
| `examples/fakeshop/test_query/test_relation_key_overrides_api.py` | 06 inherited/composite visibility controls |
| `examples/fakeshop/test_query/test_scalar_predicate_binding_api.py` | 01/04 typed projected and actual alias/reverse predicate controls |
| `examples/fakeshop/test_query/test_scalars_mutation_api.py` | Inherited/02 nested guards, 05 endpoint/query-observer controls |

### Modified package test/support source — eight files

| Path | Main work represented |
| --- | --- |
| `tests/_postgresql_stand_in.py` | 05 explicit native server-version stand-in support |
| `tests/filters/test_inputs.py` | 01 publication diagnostics and controls, plus preserved committed input work |
| `tests/filters/test_sets.py` | 01 diagnostics and 04 per-declaration child ownership expectations |
| `tests/forms/test_resolvers.py` | 05 corrected above-endpoint refusal spellings |
| `tests/mutations/test_resolvers.py` | 05 corrected above-endpoint refusal spelling |
| `tests/rest_framework/test_resolvers.py` | Inherited/02 serializer behavior and 05 endpoint cases |
| `tests/utils/test_errors.py` | 03 converter/read-back controls and 05 version/endpoint matrix |
| `tests/utils/test_relations.py` | 01 unbound generated transform metadata |

### Six untracked source/test/license files — required, not scratch

| Path | Why it belongs with the change |
| --- | --- |
| `django_strawberry_framework/rest_framework/query_bind.py` | 02 production query guard, 331 lines |
| `django_strawberry_framework/rest_framework/validator_guard.py` | 02 production DRF validator/condition guard, 166 lines |
| `examples/fakeshop/test_query/test_serializer_validator_bind_api.py` | 02 live regressions, 1,136 lines |
| `examples/fakeshop/test_query/test_serializer_validator_bind_sharded_api.py` | 02 write-alias regressions, 201 lines |
| `examples/fakeshop/test_query/test_decimal_column_name_readback_api.py` | 03 live read-back regressions, 252 lines |
| `LICENSE.postgresql` | 05 required license for adapted numeric behavior |

### Twenty-one existing untracked review artifacts

They comprise six final sequential MD/JSON pairs, the sequential index, the earlier commit-04
pending pair, the commit-07 pending pair, the commit-07 correction pair, and the rejected original
batch pair. Their ten JSON files total 5,850,932 bytes. They are evidence, not executable package
modules or disposable test output.

The [commit-07 pending report][pending-07] is historical: its claim that a timing decision is
unanswered is superseded by the [correction][phase-correction]. Commit 04's final report likewise
predates the complete-field timing correction. Preserve the sequence instead of silently
rewriting old evidence. The rejected `review-fix100-2026-11-08.md/json` pair is excluded from
correctness authority even though retained in the inventory.

## Concurrent work and cleanup boundaries

Eight maintainer commits advanced main during the audit: `8b86f622` (734), `25b72786` (735),
`0726d602` (738), `7ba26721` (739), `acf60db3` (741), `7a09a1f0` (745), `08178cda` (746) and
`3714f495` (750). They are outside the fixed original selection and were not authored by this
audit. Relevant intersections were checked; that was not a wholesale audit of those commits.
In particular, the current raw-request context/actor handling must survive further form work.

The current input source and its package tests differ from commit-01 closure hashes but match
the start-of-07 snapshot, with intervening committed changes explaining their context. The
live-test README differs from commit-06's snapshot solely by the two committed item-750 index
additions. TREE matches its recorded later concurrent context and passed owner parity. Do not
mistake those whole-file hash differences for permission to revert foreign code.

**A genuinely foreign uncommitted hunk is present:** the bug-hunt document contains another
session's 32-line in-progress handoff for items 748/751, mentioning the `fix-i748-raw-heads`
private copies/evidence. The owned item-810 explanation and that handoff are separate hunks.
Do not whole-file stage, delete or overwrite the document. Its references to copies, database
carving and later actions are context, not instructions to execute for this task.

The three additional dirty paths identified in the opening reconciliation are also concurrent
work to preserve outside this task's landing. Default whole-tree diffs now include them; separate
them from the conversation-authored changes instead of silently expanding the review/commit scope.

No clearly disposable file was identified among the current 59 dirty paths. The likely-looking
temporary material is outside the checkout in `.work/evidence/fix-fix100-review/dsf-fix100-serial-20261108/`:
preedit snapshots, authored patch generations, private indexes/object stores, isolated metadata
backups and continuation checkpoints. That material still contains essential unfinished-R9
evidence; retain it through review and landing. The new summary-gathering directory is also
scratch, outside Git. Neither location contributes to `git status`.

The [repository instructions][agents] protect review records from bulk deletion/overwrite.
Although generated bug-hunt output is regenerable in principle, this file currently carries
another active handoff and is not a safe cleanup target. TREE is generator-owned and must stay
consistent with source. Do not clean another session's `.work/` copies/evidence, shared metadata
databases, existing stashes or the maintainer-edited dicta file as part of this work.

The pending-07 JSON deliberately archives raw JSON text with hashes under
`verbatim-json-documents-v1`. A publication formatter once failed on a decoded lone-surrogate
test value; the new artifact was restored exactly from backup and republished in the raw-text
encoding. No production formatter change resulted. Do not mass-decode and re-encode nested
evidence with unsafe Unicode handling during cleanup.

## Validation that actually happened

The audit added meaningful live HTTP regression **source** but did not run those tests.
No pytest, behavioral schema/HTTP/SQL probes, mutation proofs, coverage run or backend/version
matrix was executed by the sequential audit. Source-based predictions, including row counts,
are not observed runtime results. The repository requires an explicit maintainer request before
targeted pytest; this summary/commit request does not itself supply one.

After implementation edits, Ruff check with fixes and then Ruff format ran in that order.
The latest root R9 receipt, `root-static-checks-r9.json`, records:

| Check | Recorded result |
| --- | --- |
| Full configured default basedpyright | 0 errors, warnings or notes |
| Full Python-floor basedpyright | 0 errors, warnings or notes |
| Explicit cumulative nine-path source layout | 0 violations/errors |
| Structured source citations | 1,006 resolve |
| `git diff --check` | Pass |
| Genuine private-population suppression ledger | 647 Python files; 699 ignore comments, 103 casts, 0 violations |
| Required TREE owner parity | Pass |
| Required GLOSSARY owner parity | Pass |

The owner checks used a consistent isolated read-only-source SQLite backup and a genuine private
Git index/object store, with read-only shared alternates. The shared index was unchanged during
those operations; the source database was not written. Metadata generator queries were the
documented exception, separate from behavioral validation. No new suppression/cast allowance,
coverage workaround, setting, CHANGELOG edit or package version bump was introduced.

All nine R9 cumulative source pins still matched when this handoff inventory was taken:

| Path | SHA-256 |
| --- | --- |
| `django_strawberry_framework/filters/base.py` | `a21d5128e1e3b1b9a99e2adfae9bcd1242c2fb2c7ae6d7c57282e04906a041cd` |
| `django_strawberry_framework/filters/form_binding.py` | `d59b824056e55a839b5ff7d8eaf5bf76d134ea552a4b1ab479fb2ea15ef9c3f9` |
| `django_strawberry_framework/filters/sets.py` | `df0bed8abbcb030edccc24a3eaf1a038b1977d6dc7354e197e9dbd21492b570b` |
| `django_strawberry_framework/utils/errors.py` | `746a2a035b94baf4524875b44ec35a3f87ecea5106a13f3f66556cec5951868d` |
| `examples/fakeshop/test_query/test_filter_apply_arguments_api.py` | `0f5543bf8207ad7df74cc517da763fe72591c4ddaff356be7f9329898649cca4` |
| `examples/fakeshop/test_query/test_filter_widget_binding_api.py` | `e2f53f8f5fabdfa05d8c474e6ce78ec15068fae3f89bbb1bd6e04b5a8c6f5ded` |
| `examples/fakeshop/test_query/test_library_generated_api.py` | `78726626534e72d534910e2fefed54a47197af2a8a77578f8004e26a3cc9aabf` |
| `examples/fakeshop/test_query/test_raw_filter_forms_api.py` | `15d4b39db9950b55b4569164230d38aa693ce83b81a96e51aca37f73929398f1` |
| `docs/SPECS/spec-027-filters-0_0_8.md` | `b499c735a03affcb1ed65c50d6e26752e9731121a96de2f74b1bba98f93e18b0` |

The full R9 report is `implementation-r9.json`, SHA-256
`cecce54e7356a859595a92b49796598b4ab8c96be97c7599591f3afdde250e40`.
Its preedit-relative `authored-r9.patch` is SHA-256
`444db0143b466484eb3fb104e1d8b01f5258f8c6b802ca34aaaf568d7bfe710a`;
`implementation-hashes-r9.json` is SHA-256
`9068d59ff2b191374915e4ae25bcb1b25f1e5b8c2d7fa2bfce120523e163261f`.
They live under `.work/evidence/fix-fix100-review/dsf-fix100-serial-20261108/07-d6e19b74ea77/`.
That directory contains partial `verification-r9-evidence.json`, but no completed
`verification-r9.json`. Static success did not close the review.

## Requested external review

Review the accumulated current changes against HEAD, including the six untracked required files.
Start with the five H07 issues and check the combined interactions of form ownership, native
activity, parser dependency, permission gates, error order, logical branches, source/alias caches
and raw partial `.qs`. Preserve the independent earlier fixes, constructor restrictions,
consumer methods/fields and actual generated-column versus Transform behavior.

Then inspect the serializer query guards and backend binding boundaries, SQLite conversion,
numeric version endpoint, and inherited/composite relation correlation. Check the test source's
real public reachability and discriminating controls, not merely the existence or volume of tests.
The large apply-arguments test diff deserves particular scrutiny for stale expectations and
lifecycle interactions after the policy correction.

Use [AGENTS.md][agents], [START.md][start] and the [trust boundary][trust-boundary]. Consumer
surfaces remain Meta-based; upstream behavior should be obtained through real upstream seams.
An actionable finding needs a named contract, feasible supported declaration/project shape,
wire/configuration input, actual versus required outcome, source trace, root cause and meaningful
regression. Do not turn hostile trusted Python, speculative hardening or test absence alone into
a release blocker. This review need not restart the other 33 historical commit scopes.

Return a review report for this chat to implement. The review itself should preserve source and
history; tests remain unrun unless the maintainer explicitly requests them.

## Post-review fix, cleanup and commit plan (corrected after external review)

1. Re-snapshot current HEAD, status, index and affected contents before editing; reconcile any
   concurrent changes since this handoff.
2. Adjudicate the returned review and the five known open issues, then implement the root-cause
   fixes with meaningful regression source. Reconcile all affected spec homes and source-symbol
   references. No test-only workaround for a production abstraction defect.
3. Run the mandated Ruff sequence and appropriate allowed static/owner checks. Tests or matrix
   execution require the maintainer's explicit request; report the actual validation limits.
4. Separate ready conversation changes from unfinished and foreign hunks. Files such as
   `sets.py`, `base.py`, `form_binding.py` and the apply-arguments tests combine several scopes:
   stashing whole "commit-07 files" would also remove accepted earlier work. The mixed bug-hunt
   document needs a hunk-level separation. Inspect dependencies before calling a partial commit
   coherent.
5. Delete only specifically identified disposable outputs. None were established in the dirty
   snapshot. Preserve protected review records, required modules/tests/license and concurrent work.
6. Carve ready paths and hunks into a private index, preserving unrelated working-tree
   contents. Materialize each candidate tree through `scripts/work.py` and verify that exact
   tree. Run every hook with `uvx pre-commit run --files <intended paths>` in its isolated
   copy; targeted tests are now authorized. Do not stash concurrent work.
7. Commit the reviewed ready tree on the current branch with a change-description message
   and no attribution footer. Verify that remaining dirty hunks exactly match the preserved
   unrelated work. Keep the Markdown review records in git and archive the bulky companion
   JSON under `.work/evidence/fix-fix100-review/review-records/`, preserving their hashes.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[postgres-license]: ../../LICENSE.postgresql
[pyproject]: ../../pyproject.toml
[start]: ../../START.md
[trust-boundary]: ../../GOAL.md#trust-boundary

<!-- docs/ -->
[follow-up]: review-conversation-fixes-2026-11-09.md
[index]: review-fix100-sequential-2026-11-08.md
[pending-07]: review-fix100-sequential-07-pending-d6e19b74ea77-2026-11-08.md
[phase-correction]: review-fix100-sequential-07-phase-correction-d6e19b74ea77-2026-11-08.md
[review-01]: review-fix100-sequential-01-5060aa0142ec-2026-11-08.md
[review-02]: review-fix100-sequential-02-13982ba895f2-2026-11-08.md
[review-03]: review-fix100-sequential-03-0dcc88c6f15b-2026-11-08.md
[review-04]: review-fix100-sequential-04-90f758756aa4-2026-11-08.md
[review-05]: review-fix100-sequential-05-059a66175f52-2026-11-08.md
[review-06]: review-fix100-sequential-06-6cd57b127bd2-2026-11-08.md

<!-- docs/SPECS/ -->
[filter-spec]: ../SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converters]: ../../django_strawberry_framework/types/converters.py
[filter-base]: ../../django_strawberry_framework/filters/base.py
[filter-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filter-sets]: ../../django_strawberry_framework/filters/sets.py
[relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->

<!-- examples/ -->
[decimal-live]: ../../examples/fakeshop/test_query/test_decimal_column_name_readback_api.py
[relation-live]: ../../examples/fakeshop/test_query/test_relation_key_overrides_api.py
[serializer-live]: ../../examples/fakeshop/test_query/test_serializer_validator_bind_api.py
[serializer-sharded]: ../../examples/fakeshop/test_query/test_serializer_validator_bind_sharded_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
