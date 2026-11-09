# Sequential scoped-fix review — commit 06

**Accepted at source-review level:** `6cd57b127bd263b4cb60b90760c63afba0914e4d`.

`fix(filters): a to-many relation view keeps a parent whose first related row is hidden (item 807)`

Fresh Terra 6.1 Medium fact-finding, Sol 6.1 Extra High adversarial review, Sol High implementation
and two fresh Sol 6.1 Extra High postfix reviews completed for this commit. The
[complete evidence][evidence] preserves every report, both authored patches, concurrent drift,
source hashes, static checks and a separate preservation erratum.

## Findings and correction

| Finding | Broken behavior | Root-cause correction |
| --- | --- | --- |
| 06-R1, P2 | An inherited foreign key's reverse turn compares the ancestor key with an independent child key. A visible relation can appear absent. | Correlate the actual declaring model's concrete key fields. |
| 06-R2, P2 | A composite source makes `F("pk")` a `ColPairs` expression, rejected during Django tuple-lookup preparation. | Use native scalar Q/F comparisons for every declared key component. |

The [relation-view code][sets] now asks the foreign key's actual `field.model._meta.pk_fields`
and compares each concrete `attname` on both sides through Django's ordinary Q/F resolution.
It neither substitutes the child model's `pk` shorthand nor builds an unsupported whole composite
expression. Native metadata and lookup construction handle inherited columns and composite parts;
no upstream algorithm was copied. The documented eligibility exceptions and decisions 799/809
remain intact.

Both defects have feasible Meta-based declarations and ordinary JSON filter input. The inheritance
case uses a Book child with its own integer primary key. The composite case selects scalar title
output and a Branch choice input; it requests neither a composite scalar filter nor default Relay
identity. Empty or absent choices reach the relation-view fallback; named choices retain their
separate matching route.

## Regression source and review corrections

The [live HTTP module][live] adds 42 parameter cells: ordinary parent-link, independent child and
composite sources; sync, raw bound form and async; supplied empty and absent choices; positive and
negative relation answers, plus named/default-path/excluded-default controls. Exact ordered titles
and one-versus-two override calls are asserted. A hidden first shelf, visible occupied shelf and
visible empty shelf distinguish the visibility answers.

The first postfix review accepted production and found three test issues, all corrected in the
second implementation pass:

- The composite peers originally exposed only one missing comparison. Occupied keys now include
  `(1,1)`, `(1,3)` and `(3,1)`. The positive override keeps duplicates observable; omitting either
  comparison would produce five rows instead of the exact three-title answer.
- Independent children now explicitly use parent IDs `10000+n` and local keys `1000+n`, so a
  database sequence cannot hide the intended identity mismatch.
- Temporary models originally registered globally while their tables existed only inside a
  fixture. They are now declared by a function-local factory, selected through string parameters,
  and restored by the existing Apps cleanup. Explicit transactional markers place registration
  restoration before flush and post-migration signals. This protects existing Book/Shelf deletion
  controls from references to missing temporary tables.

The second fresh reviewer independently checked Django's reference/tuple preparation, model save,
schema-editor, Apps and pytest finalizer seams at selected/floor versions and accepted all three
final owned hashes with no residual finding. All 42 cells, DDL, cross-test deletion and async runtime
results remain unexecuted; the five-versus-three counterfactual is source-derived.

## Preservation and static evidence

During implementation, main advanced to `7a09a1f0ba2574b83c18324945c3e8da5f47897e` with a GlobalID
routing change. Its ordinary model-choice/non-Relay intersection was checked against the current
combined source. Concurrent hunks are preserved separately from the authored patch; the original
100-commit selection stays fixed. Earlier projected-child ownership and timing changes remain.

The original postfix report overstated that changed-path membership established whole-file HEAD
equality. Its hash manifest already recorded four working overlays as different from HEAD. A
separate erratum corrects the prose and preserves the original report; the final reviewer rehashed
all 54 context paths and found only the intended test revision changed. No source was reverted.

Ruff, source layout, full default/floor basedpyright, 134 source citations and diff checks pass.
The private-population ledger checks 646 Python files: 699 ignores, 103 casts, zero violations.
No type suppression, cast, lint exemption or coverage exclusion was added. TREE and GLOSSARY owner
checks pass using an isolated metadata backup and genuine private index; the shared database and
index were preserved. These metadata checks are separate from behavioral validation.

The entire original diff and its changed test assertions were reviewed. Immutable historical
SQLite comparison found identical schema and other rows, with only FilterSet glossary row 463's
body and timestamp changed. No source-database, generated-document or CHANGELOG edit was needed.
No tests, builds, CI dispatches, branches or commits were made by this audit stage.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[evidence]: ../../.work/evidence/fix-fix100-review/review-records/review-fix100-sequential-06-6cd57b127bd2-2026-11-08.json

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[sets]: ../../django_strawberry_framework/filters/sets.py

<!-- tests/ -->

<!-- examples/ -->
[live]: ../../examples/fakeshop/test_query/test_relation_key_overrides_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
