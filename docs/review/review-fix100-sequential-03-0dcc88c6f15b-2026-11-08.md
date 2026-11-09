# Sequential scoped-fix review — commit 03

**Closed at source-review level:** `0dcc88c6f15b97f1f9e75401bbe1ccade479f686`.

`fix(writes): a decimal SQLite cannot read back is the field error before the write (item 726)`

Fresh Terra 6.1 Medium fact-finding, Sol 6.1 Extra High adversarial review, Sol High
implementation and a new Sol 6.1 Extra High postfix review completed before commit 04.
The [complete evidence][evidence] preserves the reports, source hashes and check provenance.

## Findings and corrections

| Finding | Root cause | Correction |
| --- | --- | --- |
| R03-001, P2 | The private trial renamed the real column, losing SQLite name-based conversion. | Preserve the real name with Django quoting in native CREATE and SELECT. |
| R03-002, P2 | An existing test assumed modern SQLite text precision on every supported engine. | Derive its expectation from an independent real ORM read-back. |

A source-derived discriminator is a normal `DecimalField(max_digits=16, decimal_places=2)` with
`db_column="amount [decimal_text]"` and a bytes-to-ASCII decoder. Django's default parser flags
already enable name-based conversion, which takes precedence over declared-type conversion.
[Python's sqlite3 documentation][sqlite-parser] describes this public configuration.

On the reviewed Django 6.1 / SQLite 3.53.x path, wire amount `"99999999999999.99"` can be read through
that text converter. The old trial selected `value`, received a float instead and incorrectly
returned the field's `invalid` error. The corrected
[django_strawberry_framework/utils/errors.py::_refused_read_back][errors]
asks the native driver using the actual quoted name, retaining storage, save preparation and
backend conversion. SQLite's released precision boundary is [3.53.0][sqlite-release];
[3.52.0 was withdrawn][sqlite-withdrawn]. No floating-point model was added.

## Regression source and verification

The [new live module][live] covers model, ModelForm and serializer mutations, create/update,
and fitting/boundary input: twelve HTTP cells. A direct ORM save/get supplies the independent
expected result. The source asserts exact payloads, converter configuration, stored values,
no extra row on refusal and preserved prior values on failed updates. Global converters and
transient tables are restored. The [declared-type unit][unit] retains older Django's native
`TypeError` control and follows each engine's actual boundary behavior.

The implementation received two pre-handoff hygiene revisions for the model `TextField`
convention and reuse of the shared bound-column narrowing primitive. One fresh postfix review
accepted the final five hashes, both findings and integration, with no residual defect.

Ruff, full default/floor basedpyright, source layout, citations and diff checks pass.
The final private-population suppression ledger checked 645 files: 699 ignore comments,
103 casts, zero violations. No type suppressions or casts were added; the quoted identifier's
single lint exemption is explained in the evidence.

Behavioral tests, dependency-floor collection, coverage and the version matrix remain unexecuted.
The required [TREE][tree] owner-generator check passed with the new module and the four earlier
untracked modules included through a genuine private index/object store. Its metadata snapshot
was isolated; the shared index and source database were preserved. This metadata-only workflow
is recorded separately from behavioral validation.

Fact-finding and review independently compared the original immutable database blobs: schema
unchanged, only the FieldError glossary row's body and timestamp changed. No new glossary,
source-database or CHANGELOG edit was made. Concurrent work and the original 100-commit
selection remain preserved; acceptance applies to the recorded source hashes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[evidence]: ../../.work/evidence/fix-fix100-review/review-records/review-fix100-sequential-03-0dcc88c6f15b-2026-11-08.json
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[errors]: ../../django_strawberry_framework/utils/errors.py

<!-- tests/ -->
[unit]: ../../tests/utils/test_errors.py

<!-- examples/ -->
[live]: ../../examples/fakeshop/test_query/test_decimal_column_name_readback_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[sqlite-parser]: https://docs.python.org/3.10/library/sqlite3.html
[sqlite-release]: https://sqlite.org/releaselog/3_53_0.html
[sqlite-withdrawn]: https://sqlite.org/releaselog/3_52_0.html
