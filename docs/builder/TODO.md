# Builder TODO

Outstanding items moved out of the archived build plans in `docs/builder/DONE/`. Each entry was removed from its source build file when it was recorded here. The maintainer reviews this list to decide, item by item, whether to implement or drop.

Entry format:

```
### T-NNN: <one-line title>
- Source: `docs/builder/DONE/<build file>` (section / line it came from)
- Original text: "<short quote or faithful paraphrase>"
- Current state: <what the code / board / docs show today, with file:line or card ref>
- Also tracked: <KANBAN card, spec, or doc that already carries it, or "nowhere else">
```

## Verdicts

- IMPLEMENT (71): T-002, T-003, T-007, T-008, T-009, T-011, T-013, T-014, T-015, T-016, T-018, T-020, T-021, T-023, T-024, T-025, T-026, T-027, T-030, T-032, T-033, T-035, T-036, T-037, T-038, T-039, T-040, T-043, T-044, T-045, T-046, T-049, T-051, T-052, T-053, T-054, T-055, T-058, T-059, T-061, T-062, T-064, T-066, T-067, T-069, T-070, T-072, T-075, T-078, T-079, T-083, T-084, T-085, T-087, T-090, T-091, T-092, T-094, T-096, T-097, T-098, T-099, T-101, T-102, T-103, T-104, T-108, T-109, T-110, T-111, T-114.
- DROP (43): entries removed after their board rows were deleted.
- Audit side findings: refresh the stale board lines in one DB pass after the IMPLEMENT items land (dropped items' board rows are deleted, not repointed); leave the `DONE/` filename versions as closed history.

## Items

### T-002: Nested-branch FK-id elision leak test (sibling nested branches under one parent type)
- Source: `docs/builder/DONE/build-003-optimizer_nested_prefetch_chains-0_0_2.md` (`### Test-plan coverage`, row `test_optimizer_nested_fk_id_elision_does_not_leak_to_sibling_branch`; `### The read-only correctness audit` closing paragraph)
- Original text: "The sibling-nested-branch axis under one parent type is untested (noted as untested-but-correct, since the resolver key distinguishes branches by runtime path)."
- Current state: Not found in tree: `tests/types/test_resolvers.py::test_b2_forward_fk_id_elision_does_not_leak_across_parent_types` covers the parent-type axis, `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_does_not_leak_to_sibling_root_in_http_query` the sibling-root axis, and `tests/optimizer/test_walker.py::test_plan_records_nested_fk_id_elision_with_resolver_key` one nested key; no test pins two sibling nested branches under one parent type.
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): one live test in `examples/fakeshop/test_query/` with two sibling nested branches under one parent type; a leak there serves wrong data over the wire.

### T-003: `_prefetch_lookup_paths` has no depth cap while `runtime_path_from_path` is bounded
- Source: `docs/builder/DONE/build-003-optimizer_nested_prefetch_chains-0_0_2.md` (`### The read-only correctness audit`, closing paragraph)
- Original text: "`optimizer/plans.py::_prefetch_lookup_paths` recurses with no depth cap while its sibling `::runtime_path_from_path` is bounded (theoretical asymmetry only; the walker cannot construct a cyclic `Prefetch` graph)."
- Current state: Still unbounded: `django_strawberry_framework/optimizer/plans.py::_prefetch_lookup_paths` recurses through `_consumer_prefetch_lookups` with no limit; `::runtime_path_from_path` uses `_MAX_PATH_DEPTH = 1024`.
- Also tracked: Card `TODO-ALPHA-053-0.0.15` (Boundary hardening and system-wide DRY squeeze), `KANBAN.md` line 283: bound it to match its sibling or record why the asymmetry is deliberate.
- Verdict: **IMPLEMENT** (done): docstring sentence only, no bound: the input is consumer-authored `Prefetch` objects (finite, no wire path), while `::runtime_path_from_path` reads the wire-derived `info.path`.

### T-007: Decide whether `DjangoSchema` and `DjangoMutationExecutionContext` earn their own glossary entries
- Source: `docs/builder/DONE/build-006-public_surface-0_0_3.md` (`### Maintainer decision 2`, the `WIDENED by one CardItem` paragraph); also `docs/builder/DONE/build-048-secure_output_defaults-0_0_17.md` (catalog of the retired `bld-048-final.md`, `git show 567cc6d0:docs/builder/bld-048-final.md`: "`docs/GLOSSARY.md` has no `DjangoSchema` entry", so card 047's rows link a `#djangoschema` anchor that resolves to nothing)
- Original text: "Whether `DjangoSchema` earns a full glossary entry with its own anchor stays card 052's decision - it is an editorial call about entry granularity, not a contract violation."
- Current state: Open. `docs/GLOSSARY.md` `## Public exports` carries unlinked bullets for `DjangoSchema` and `DjangoMutationExecutionContext` (no `## DjangoSchema` heading or anchor exists).
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 524 (also notes the `DjangoSchema` bullet collapses to one line only if the entry is authored).
- Verdict: **IMPLEMENT** (done): `DjangoSchema` is required for generated mutations and owns both policies; a core export with no glossary entry. Author `## DjangoSchema` (glossary ORM edit), with `DjangoMutationExecutionContext` as a paragraph inside it.

### T-008: `## Public exports` has no group bullets for `views`, `routers`, `middleware.debug_toolbar`
- Source: `docs/builder/DONE/build-006-public_surface-0_0_3.md` (`### Maintainer decision 2`, `CORRECTION` bullet list)
- Original text: "The three families the section omits - `views`, `routers`, `middleware.debug_toolbar` - are NOT in scope here ... only the group listing is absent ... it goes to card 052's list."
- Current state: Open. `docs/GLOSSARY.md` `## Public exports` has groups for the root, `extensions`, `testing` and `auth` only; none for `views`, `routers` or `middleware.debug_toolbar`, each of which has its own glossary entry.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 524.
- Verdict: **IMPLEMENT** (done): add the three group bullets (glossary ORM edit plus render).

### T-009: Board sentence cites a `## The discharged deferral` heading that no longer exists
- Source: `docs/builder/DONE/build-006-public_surface-0_0_3.md` (`### Corrections to Worker 0's own instruments`, correction 2)
- Original text: "the live fix is `CardItem` pk 1260's, target order: maintainer at commit, else card `TODO-ALPHA-052-0.1.0`" (the board prose quotes the spec-002 rationale's discharge heading).
- Current state: Still open and now worse. `KANBAN.md` line 529 says the discharge "is recorded in that companion's `## The discharged deferral`", but `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` has no such heading (its `##` headings are the four "Why ..." sections; 0 hits for "discharged deferral").
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 529 (the sentence itself); the fix is an ORM edit of that `CardItem.text` plus a regenerate.
- Verdict: **IMPLEMENT** (done): the sentence cites a heading that does not exist; ORM edit of that `CardItem` plus render.

### T-011: AGENTS.md raw `path:NN` exemption list does not name `build-*.md` plans
- Source: `docs/builder/DONE/build-007-onboarding_docs_spec_consolidation-0_0_4.md` (`### Verified spec-versus-HEAD drift`, "Two further observations", item (b))
- Original text: "`AGENTS.md` rule 27 exempts per-cycle `docs/builder/bld-*.md` scratchpads but does not name `build-*.md` plans. Six committed plans do the same, so it is a standing-doc question for the maintainer - whether the exemption's list should name the plan file alongside the artifacts."
- Current state: Open. The `AGENTS.md` source-refs rule (`Source refs in docs and code comments use symbol paths never line numbers`) still lists only `docs/review/review-*.md`, `rev-*.md`, `docs/dry/dry-*.md` and `docs/builder/bld-*.md`; `build-*.md` is not named.
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): add `docs/builder/build-*.md` (live and `DONE/`) to the rule-28 exemption list in `AGENTS.md`; maintainer's file.

### T-013: Stale end-to-end pointer in `test_relay_node_strips_django_id_annotation`'s docstring
- Source: `docs/builder/DONE/build-015-relay_interfaces-0_0_5.md` (`## Post-gate disposition of the deferred catalog`, `### Board edits landed` table, catalog items 2 + 5)
- Original text: "2 (stranded Risk-note citation) + 5 (stale test docstring)" homed on the boundary-hardening card; the docstring points at a file that exists but cannot support the sentence.
- Current state: Open. `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation` docstring still says end-to-end coverage lives in `tests/types/test_definition_order_schema.py`; that file carries no Relay coverage (`grep -ciE 'relay|node|global_id'` -> 0). The coverage is in `examples/fakeshop/test_query/test_library_api.py::test_relay_genre_type_emits_node_interface_and_global_id_live` and `::test_mixed_relay_and_non_relay_no_interface_bleed_live`. (The other half of that row, the stranded Risk-note citation, is done: the `test_apply_interfaces_wraps_typeerror_as_configuration_error` docstring now cites the rationale companion.)
- Also tracked: Card `TODO-ALPHA-053-0.0.15` (Boundary hardening and system-wide DRY squeeze), `KANBAN.md` line 291 (fold into whichever WP batch opens the file).
- Verdict: **IMPLEMENT** (done): repoint the docstring at the two live tests.

### T-014: No package-tier test pins Relay-target relation planning against a non-Relay target (A/B row)
- Source: `docs/builder/DONE/build-015-relay_interfaces-0_0_5.md` (`## Post-gate disposition of the deferred catalog`, `### Board edits landed` table, catalog item 4)
- Original text: "4 (unpinned A/B relation-planning row)" homed on the boundary-hardening card: `test_relay_target_relation_planning_unchanged` was retired at `4f4db722` and the comparison cannot be made in the live tier because every `products` type now declares a `get_queryset`.
- Current state: Open. `rg test_relay_target_relation_planning_unchanged tests examples django_strawberry_framework` returns nothing; `tests/optimizer/` has no non-Relay-target planning comparison (`rg -i 'non.?relay' tests/optimizer` empty; only `tests/optimizer/test_walker.py::test_plan_relay_id_projects_real_pk_attname_when_not_id` and `::test_plan_relay_id_projects_attname_when_pk_is_relation` touch Relay planning).
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 292 (to be opened together with the `_record_relation_access` ordering guard).
- Verdict: **IMPLEMENT** (done): package-tier test comparing relation planning for a Relay and a non-Relay target; the contract lost its only pin when the old test was retired.

### T-015: Rule-27 source-reference spellings left in `optimizer/walker.py` and `optimizer/field_meta.py` by the spec-016 consolidation
- Source: `docs/builder/DONE/build-016-fieldmeta_consolidation-0_0_6.md` (`## Deferred-work homing (Worker 0, post-gate)`, first bullet, catalog items 1, 5 and 6)
- Original text: "catalog items 1, 5 and 6 as one rule-27 fold-in row over `optimizer/walker.py`, `optimizer/field_meta.py` and `tests/test_registry.py`".
- Current state: Open for two of three. `django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation` docstring still cites `utils.relations.instance_accessor` in dotted form (needs `django_strawberry_framework/utils/relations.py::instance_accessor`); `django_strawberry_framework/optimizer/field_meta.py::_target_pk_name` docstring still cites `_field_meta_for_resolver` as a bare symbol (the module's own `::_from_field_shape` docstring spells it `types/resolvers.py::_field_meta_for_resolver`). The `tests/test_registry.py` third is done (no `_record_pending_relation` reference left).
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 294.
- Verdict: **IMPLEMENT** (done): convert both spellings to `path::Symbol` so `scripts/check_citations.py` reads them.

### T-016: Rule-27 spellings in `registry.py` and `types/converters.py` docstrings
- Source: `docs/builder/DONE/build-016-fieldmeta_consolidation-0_0_6.md` (`## Deferred-work homing (Worker 0, post-gate)`, second bullet, catalog items 3 and 4)
- Original text: "`TODO-ALPHA-052-0.1.0` gained one row: catalog items 3 and 4, whose two files no `051` WP batch opens".
- Current state: Open. `django_strawberry_framework/registry.py` module docstring lists `types.converters.resolved_relation_annotation` and `types.converters.convert_choices_to_enum` in dotted form; `django_strawberry_framework/types/converters.py::convert_scalar` docstring says `types/base._build_annotations` (slash-and-dot hybrid). The same dotted `types.converters.convert_choices_to_enum` spelling also appears in `django_strawberry_framework/filters/inputs.py` (a site the board row does not list).
- Also tracked: Card `TODO-ALPHA-056-0.0.17` (Alpha documentation-debt discharge), `KANBAN.md` line 550.
- Verdict: **IMPLEMENT** (done): same conversion, including the `filters/inputs.py` site.

### T-018: `scripts/check_citations.py` does not flag a line-wrapped `#"substring"` pinpoint
- Source: `docs/builder/DONE/build-016-fieldmeta_consolidation-0_0_6.md` (`## Retained from the final gate, which is retired`, "item 17 is carded on 052 as the checker's reflow obligation"); also `docs/builder/DONE/build-027-filters-0_0_8.md` (`## Surviving items migrated out of bld-final-027.md before its deletion`, "No instrument here can see a citation wrapped across a line break") and `docs/builder/DONE/build-028-orders-0_0_8.md` (`### Live and uncarded`, B1 clause 2; see T-040 for the other clauses)
- Original text: The checker's reflow obligation: an opened `#"` with no closing quote on its line should be a finding, with a wrapped pinpoint as the regression test.
- Current state: Open. `scripts/check_citations.py` scans `#"` pinpoints one line at a time (`_scan_windows(text, '#"', wrap=False)`) and has no unclosed-quote detection (`rg -i 'reflow|unterminated|never closed' scripts/check_citations.py` empty); no wrapped-pinpoint regression test found.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 549.
- Verdict: **IMPLEMENT** (done): flag an unclosed `#"` on its line; one checker change with T-030 and T-040.

### T-020: `DONE-017-0.0.6` card still says the Strawberry `DeprecationWarning` is suppressed at the definition site
- Source: `docs/builder/DONE/build-017-deferred_scalars-0_0_6.md` (`## Maintainer handoff` MF-1 bullet; `### MF-1 replacement text`)
- Original text: "the DB-backed `KANBAN.md` `DONE-017-0.0.6` suppression claim (**MF-1** - 4 occurrences: `CardItem` 703/713/715 plus `CardReference` 62 on card 39, with 715 and 62 byte-identical and amendable only together)"
- Current state: Open. `examples/fakeshop/db.sqlite3` still carries the present-tense claim in `kanban_carditem` 703 ("suppressed at the definition site"), 713 ("guard so future regressions to the suppression are explicit") and 715, and in `kanban_cardreference` 62 (same text as 715, FK-backed `card_ref` placeholder to keep verbatim); `KANBAN.md` `DONE-017-0.0.6` still renders the 713 and 62 text. The suppression no longer exists: `CHANGELOG.md` `[0.0.7]` `### Removed` records its removal by `DONE-025-0.0.7`. Fix is an ORM edit of the four rows (703: past-tense "at `0.0.6` ... suppressed ... no longer exists"; 713: "warning-free import surface"; 715 and 62 together: past tense plus "`DONE-025-0.0.7` replaced that suppression: `BigInt` is a bare `NewType` registered through the package scalar map merged by `strawberry_config()`") then `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py`. The verbatim replacement text lived in the build file's `### MF-1 replacement text` section, removed with this entry; it is recoverable from git history of that file.
- Also tracked: Card `TODO-ALPHA-056-0.0.17` (Alpha documentation-debt discharge), `KANBAN.md` line 551 (its bullet still cites the build file's removed `### MF-1 replacement text` section).
- Verdict: **IMPLEMENT** (done): `KANBAN.md` is a state doc and the rows claim, in the present tense, a suppression that no longer exists; ORM edit of the four rows plus render.

### T-021: `DONE-018-0.0.6` card row names the private `audit_primary_ambiguity()` as public; ten sibling note rows are import-truncated
- Source: `docs/builder/DONE/build-018-meta_primary-0_0_6.md` (`## Closeout record`, `### Maintainer hand-offs` item 1)
- Original text: "The live `KANBAN.md` `DONE-018-0.0.6` card body names the public `audit_primary_ambiguity()` - private as `_audit_primary_ambiguity` since commit `13d8dac5`"; also "10 of that card's 15 `note` items end mid-sentence (rows 720, 721, 722, 723, 725, 726, 727, 728, 732, 733)".
- Current state: Open. `kanban_carditem` 723 (`note`, order 6) still reads "`finalize_django_types()` runs `audit_primary_ambiguity()` first" (`sqlite3` read-only against `examples/fakeshop/db.sqlite3`); the live symbol is `django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity`. All ten named rows are still 61-70 characters ending mid-sentence. Fix the symbol name only; repairing the clipped rows is a separate card-wide call (the lost text has to be recovered from the card's history).
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 552 (carries the row id, the fix instrument and the truncation finding).
- Verdict: **IMPLEMENT** (done): fix the symbol name in row 723 only. Drop the truncated-row repair: the lost text is not false, just short.

### T-023: `DONE-020-0.0.7` board card lists `django_strawberry_framework/apps.py` under `#### Package files`
- Source: `docs/builder/DONE/build-020-list_field-0_0_7.md` (`### Escalated to the maintainer` item 2; `## Deferred-work homing` row 2 and "Two catalog claims", claim 2)
- Original text: "`KANBAN.md`'s `DONE-020-0.0.7` card lists `django_strawberry_framework/apps.py` under `#### Package files`. That file is `DONE-021-0.0.7`'s subject, not this card's."
- Current state: Open. `KANBAN.md` `DONE-020-0.0.7` `#### Package files` lists `__init__.py`, `apps.py`, `list_field.py`; `apps.py` belongs only to `DONE-021-0.0.7`. Board-DB-backed (`CardPathLink` of kind `changed` linking `apps.py` to card 20): delete that one link by ORM, then regenerate `KANBAN.md` and `KANBAN.html`. No card-files JSON is checked into the repo, so the DB fix is durable; the only residual risk is a future hand-authored JSON for card 20 copying the wrong list.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 553.
- Verdict: **IMPLEMENT** (done): delete the one `CardPathLink` plus render.

### T-024: Unqualified "appends a pk tiebreaker" comparative for `DjangoConnectionField` in the `DjangoListField` ordering text
- Source: `docs/builder/DONE/build-020-list_field-0_0_7.md` (`## Deferred-work homing`, row 3, the `orderBy` / pk-tiebreaker bundle)
- Original text: "The comparative '`DjangoConnectionField` appends a pk tiebreaker' is unqualified where the shipped append is **conditional**" (`django_strawberry_framework/optimizer/plans.py::deterministic_order` appends only when `ends_in_unique_column` is False; the keyset branch appends nothing). Take the whole population or none.
- Current state: Open for the (ii) half. Unqualified wording remains in `docs/SPECS/spec-020-list_field-0_0_7.md` (`### Decision 8` bullets, "a pk tiebreaker appended"), in the `DjangoListField` docstring `Ordering contract` passage of `django_strawberry_framework/list_field.py` ("close the order with a primary-key tiebreaker"), and in `docs/GLOSSARY.md` `DjangoListField` `**Ordering.**` ("appends a pk tiebreaker because its positional cursors require a total order"). The (i) half (the `orderBy` recourse naming an argument the field does not wire) is obsolete: spec-050 gave every `DjangoListField` published `offset` / `limit` / `orderBy` arguments. Glossary fix goes by `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py`, never a hand-edit.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 297 (still describes half (i) as live).
- Verdict: **IMPLEMENT** (done): qualify the tiebreaker as conditional at all three sites (spec-020, `list_field.py` docstring, glossary ORM edit).

### T-025: `list_field.py` comment understates the `is_async_callable` contract
- Source: `docs/builder/DONE/build-020-list_field-0_0_7.md` (`## Deferred-work homing`, row 5)
- Original text: "the retired `one-hop` / three-shape `is_async_callable` characterisation": the comment calls it the "`__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`".
- Current state: Open. `django_strawberry_framework/list_field.py` comment above the consumer-wrapper branch still reads "(the ``__call__``/``functools.partial``-aware superset of ``inspect.iscoroutinefunction``)"; `django_strawberry_framework/utils/typing.py::_callable_inspection_target` also peels raw `staticmethod` layers to any nesting and the predicate reads a metaclass `async def __call__`. Understatement, not falsehood; fold with T-024 (same file).
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 298.
- Verdict: **IMPLEMENT** (done): replace the characterization with a pointer to `django_strawberry_framework/utils/typing.py::is_async_callable`; same edit as T-024.

### T-026: Glossary `SyncMisuseError` entry omits `DjangoListField` and the async-only-iterable misuse
- Source: `docs/builder/DONE/build-020-list_field-0_0_7.md` (`## Deferred-work homing`, row 4)
- Original text: "glossary `SyncMisuseError` omits `DjangoListField`" (the entry frames the raise as only "when `cls.get_queryset` returns a coroutine").
- Current state: Open. `docs/GLOSSARY.md` `## SyncMisuseError` raising-surface bullet lists the Relay Node defaults, the `DjangoConnectionField` sync pipeline, the optimizer sync prefetch-child build and the `FilterSet` related-visibility derive; it does not name `DjangoListField`'s sync default resolver (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`) nor `utils/querysets.py::reject_async_iterable_in_sync_context`, which raises the same error for an async-only iterable met from sync execution. Fix by `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py`, never a hand-edit.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 299.
- Verdict: **IMPLEMENT** (done): glossary ORM edit naming both raise sites.

### T-027: Glossary `## Schema introspection management command` entry states no selector-rejection contract
- Source: `docs/builder/DONE/build-022-export_schema-0_0_7.md` (`## Deferred-work homing`, catalog item 1); also `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md` (`## Worker-0 pre-dispatch verification`, `### D. Outside the fence`, second bullet, and `## Deferred-work homing`, "Two recorded non-misses")
- Original text: "1 - introspection entry's symmetric validator gap", homed on the Alpha documentation-debt card; the sibling export entry now states the empty-module-path and relative-module-path rejections, the introspection entry states none.
- Current state: Open. `rg -c 'relative module path|module path is empty|_imports' docs/GLOSSARY.md` returns 1 (the export entry). The introspection entry (`docs/GLOSSARY.md` `## Schema introspection management command`) lists its `CommandError` cases without any selector-shape rejection, although `inspect_django_type` reaches `django_strawberry_framework/management/commands/_imports.py::_validate_absolute_module_path` through both `import_module_symbol_or_command_error` and `import_string_or_command_error` (so three rejections, two labels). Fix is a `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py`, never a hand-edit.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 554 (carries the three-rejection detail).
- Verdict: **IMPLEMENT** (done): glossary ORM edit adding the selector rejections.

### T-030: `scripts/check_citations.py --substrings` is not part of the pre-commit hook or CI, so dead `#"substring"` pinpoints reach no gate
- Source: `docs/builder/DONE/build-022-export_schema-0_0_7.md` (`## Deferred-work homing`, catalog item 5); also `docs/builder/DONE/build-038-form_mutations-0_0_12.md` (`### The one finding no card carries`: the `#"substring"` half of rule 27 is as ungated as its ordinal half; 1,434 citations, about 128 unresolved at the time)
- Original text: "5 - citations whose target is a script-rendered doc" (a pinpoint into `docs/TREE.md`, `KANBAN.md` or `docs/GLOSSARY.md` dies on every regenerate with no edit to the citer); homed with both resolvers' figures (47 tokens / 44 parsed / 11 resolve / 33 dead versus 47 parsed / 25 resolve / 22 dead), the divergence being a line naming two candidate target files.
- Current state: Open. `.pre-commit-config.yaml` hook `check-citations` (line 138) and `.github/workflows/django.yml` (line 86, `--check`) pass no `--substrings`. Run by hand today (`uv run python scripts/check_citations.py --substrings`) it reports 5 dead pinpoints: `examples/fakeshop/test_query/test_multi_db.py` (857), `KANBAN.md` (294), `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md` (23, `pyproject.toml #"ANN002"`), `docs/SPECS/spec-020-list_field-0_0_7.md` (46 and 85); 0 ambiguity warnings repo-wide. The two-candidate-file line is still the intended first regression test.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 557.
- Verdict: **IMPLEMENT** (done): fix the five dead pinpoints, then add `--substrings` to the pre-commit hook and the CI `--check` run.

### T-032: Glossary `## Multi-database cooperation` omits the resolver-level alias re-pin in `_visible_related_object`
- Source: `docs/builder/DONE/build-023-multi_db-0_0_7.md` (`## Deferred-work homing`, item 2)
- Original text: "`_visible_related_object`'s resolver-level alias re-pin is absent from the same GLOSSARY entry"; constraint: it lands as a refinement of axis 3, not a fifth axis (the spec, `CHANGELOG.md` and the entry all say "four axes").
- Current state: Open. `rg -c '_visible_related_object' docs/GLOSSARY.md` returns 0 and the entry (`docs/GLOSSARY.md` `## Multi-database cooperation`) has no sentence on the relation visibility re-check re-pinning onto the related row's own alias; the behavior ships at `django_strawberry_framework/types/resolvers.py::_visible_related_object` (`source = source.using(alias)`). Item 1 of the same homing (the plan-time versus fetch-time qualifier on axis 3) is done: axis 3 now reads "no root alias in the plan; its routing is alias-late, decided at fetch time". Fix is a `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py`, never a hand-edit.
- Also tracked: Nowhere else (`rg _visible_related_object KANBAN.md` empty; the `TODO-ALPHA-051-0.0.15` row the build named no longer carries it).
- Verdict: **IMPLEMENT** (done): one sentence under axis 3 (glossary ORM edit).

### T-033: Package docstring schema examples disagree on `config=strawberry_config()`
- Source: `docs/builder/DONE/build-025-scalar_map_helper-0_0_7.md` (`## Deferred-work homing`, "Package docstring schema examples split on `config=strawberry_config()`")
- Original text: "whether a topic-scoped illustration (an optimizer example, a resource-policy example) should carry an unrelated `config=` line is a doc-style decision for the maintainer, not a defect a spec cycle may settle."
- Current state: Still split. `django_strawberry_framework/extensions/debug.py` (module docstring) and `extensions/resource_policy.py::DjangoResourcePolicyExtension` (class docstring, two examples) carry `config=strawberry_config()`; `django_strawberry_framework/optimizer/extension.py` (module docstring and the singleton-in-a-factory method docstring) construct `strawberry.Schema(query=Query, extensions=[lambda: _optimizer])` without it.
- Also tracked: Card `TODO-ALPHA-053-0.0.15` (Boundary hardening and system-wide DRY squeeze), `KANBAN.md` line 304 (doc-style call, homed not decided).
- Verdict: **IMPLEMENT** (done): align the package docstring examples on the canonical form in `docs/README.md` and `TODAY.md`: `DjangoSchema(..., config=strawberry_config(), ...)`.

### T-035: `CHANGELOG.md` `[0.0.7]` `DONE-026-0.0.7` entry carries three errors
- Source: `docs/builder/DONE/build-026-scalar_conversion_fakeshop-0_0_7.md` (`## Final gate record`, `### Deferred work: all three items HOMED, not carried`)
- Original text: "`CHANGELOG.md`'s repetition of the retired exclusivity shape ... `CHANGELOG.md`'s two undercounts (three retired tests where six, eight live tests where nine)"
- Current state: Open. `CHANGELOG.md` line 216 still says three `tests/types/test_converters.py` tests were removed (six were, adding the three JSON ones), still says "(eight tests" where `examples/fakeshop/test_query/test_scalars_api.py` shipped nine (the omitted one is `test_scalar_specimen_introspects_json_scalar_in_both_shapes`), and still says the paired-model layout exercises "surfaces no other example app touches". The card-body half of that homing (the `DONE-026-0.0.7` `CardItem` rows 762/763) is already clean.
- Also tracked: Card `TODO-ALPHA-056-0.0.17` (Alpha documentation-debt discharge), `KANBAN.md` line 558 (the three errors, clause by clause; `AGENTS.md` rule 22 makes the CHANGELOG edit the maintainer's call).
- Verdict: **IMPLEMENT**: maintainer edit: the counts were wrong on their own release; delete the counts and the "no other example app" clause rather than restate them.

### T-036: `types/base.py` comment names a build-process phase (`spec-032 integration pass`)
- Source: `docs/builder/DONE/build-027-filters-0_0_8.md` (`## Surviving items migrated out of bld-final-027.md before its deletion`, first "Still live" bullet)
- Original text: "`django_strawberry_framework/types/base.py` names a build-process phase in shipped source. 1 occurrence of `spec-032 integration pass`."
- Current state: Open. The comment above `_RELAY_NODE_GATE_INHERIT_TAIL` in `django_strawberry_framework/types/base.py` still reads "byte-identical at every compose site (spec-032 integration pass)".
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 300 (retire the phase name, keep the invariant).
- Verdict: **IMPLEMENT** (done): banned process provenance in shipped source; keep the invariant, drop the phase name.

### T-037: `tests/test_routers.py` cites `spec-046 Decision 11` for a lease contract that Decision 16 owns
- Source: `docs/builder/DONE/build-027-filters-0_0_8.md` (`### Cohorts I and H (follow-up) amendments`, the "Cohort I's strongest attributions" paragraph)
- Original text: "it **declined a renumber it could not ground**: ... 17 of 18 `lease` occurrences under `spec-046 Decision 16` and **0** under Decision 11, making the cited number an author slip ... It added the card and escalated the number."
- Current state: Open. The docstring of the test in `tests/test_routers.py` that opens "spec-046 Decision 11, the lease held through the send: the sibling race." is unchanged in substance; `docs/SPECS/spec-046-transport_security-0_0_14.md` `### Decision 11` contains 0 occurrences of "lease" while `### Decision 16` (connection-scoped revocation) contains 17. Whether the number is a slip is the maintainer's call (Decision 11 does reference Decision 16's outbound gate).
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): `### Decision 11` is the consumer-injection seam and carries no lease; retarget the docstring to Decision 16.

### T-038: Numbered-item citation vocabulary in `.py` (`Decision N`, `Finding N`, `Revision N`, `Spec-NNN`) not swept
- Source: `docs/builder/DONE/build-027-filters-0_0_8.md` (`### The largest remaining in-fence population, and Worker 0's stopping decision`; `Cohorts I and H (follow-up) amendments`; `Closeout of the catalog-discharge cohorts`); `docs/builder/DONE/build-028-orders-0_0_8.md` (`### Live and deliberately left`, E2 and C3); `docs/builder/DONE/build-038-form_mutations-0_0_12.md` (`### Where the deferred catalog's 18 items went`, the two "Carded on" bullets: stranded review-round labels in `tests/`, `examples/` and package source); `docs/builder/DONE/build-040-auth_mutations-0_0_13.md` (`### Slice 7`, deferred entry 5: `Revision N` citations in `test_library_api.py`)
- Original text: "The tail is a `TODO-ALPHA-052-0.1.0` sweep, not a slice" (spaced `Decision N`); capital-S `Spec-NNN` ("52 in `.py`"); out-of-family review-item ids ("the next pass must re-measure rather than quote either figure"); four lowercase `spec Decision N` sites.
- Current state: Not swept. Re-counted today in `.py`: 36 hyphenated `Decision-N`, 11 `Finding N` (all `tests/forms/` and `tests/mutations/` docstrings), 3 `Revision N` (`examples/fakeshop/test_query/test_library_api.py`), 50 capital-S `Spec-NNN`, and one unanchored lowercase `per spec Decision 5` (`tests/types/test_resolvers.py`). The board's anchor-graded defect population for spaced `Decision N` is 13 occurrences across 4 files; today `django_strawberry_framework/permissions.py` carries 7, `tests/test_apps.py` 3, `optimizer/hints.py` 1, `management/commands/inspect_django_type.py` 1. The `Spec-NNN` capital-S spelling awaits a maintainer ruling (sentence-initial openers, none is rot). Stranded review-round labels from the spec-038 sweep, re-checked today: `tests/mutations/test_resolvers.py` still names `spec-036 FV-1` 8 times (spec-036 pair carries none); `django_strawberry_framework/optimizer/nested_planner.py` still carries `the P2-3 false-coverage defect` / `the P2-3 defect` (spec-033 pair carries none); `tests/test_connection.py` still has the `P3aNode` / `P3bDirectNode` / `P3bRegistryNode` type names; `examples/fakeshop/test_query/test_library_api.py` still has `the P0 served it 1`. The `Md<n>`, `M1a`, `H4`, `SR-3`, `L3-1`, `M3-1`, `P1-B` and `the P1 bug` / `the P2 bug` sites the spec-038 catalog listed are gone from the tree.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 571 (the graded population and the ruling); card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` lines 317 and 595 (stranded review-round labels in named files).
- Verdict: **IMPLEMENT** (done): the defect subset only: stale review labels (`spec-036 FV-1`, `P2-3` in `nested_planner.py`, the `P3a` / `P3b` type names, `the P0`), unanchored spaced `Decision N` (qualify with `spec-NNN`), and `Finding N` / `Revision N` that point at nothing. Drop the capital-S `Spec-NNN` ruling: sentence-initial and resolvable.

### T-039: Raw `line NN` spec citations remain in `tests/mutations/test_sets.py` and `tests/optimizer/test_extension.py`
- Source: `docs/builder/DONE/build-028-orders-0_0_8.md` (`### Live and deliberately left`, E1); `docs/builder/DONE/build-027-filters-0_0_8.md` (`### Catalog-discharge cohorts`, item 6); `docs/builder/DONE/build-035-optimizer_hardening-0_0_10.md` (`## Partition correction`, "Out of scope, cataloged not fixed"; `### Deferred work: final disposition`, D4)
- Original text: "the tree-wide `line NN` citation residue: 10 line-scoped / 12 flattened across four files, re-derived unchanged" (all naming `spec-035` / `spec-036`).
- Current state: Open for two of four files. `tests/mutations/test_sets.py` still cites "spec-036 Decision 6 line 334" and "Edge cases line 509" (three sites plus one wrapped across two comment lines); `tests/optimizer/test_extension.py` still cites "Decision 7 line 346" / "line 347" (three sites). The `optimizer/walker.py` and `tests/optimizer/test_walker.py` sites are gone. The upstream-cookbook line refs (`tests/orders/test_sets.py` "cookbook line 280", `tests/orders/test_factories.py` "cookbook lines 124-130") are a recorded non-repair: the target is an unpinned third-party checkout, do not re-open without pinning it.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 572 (thirteen prose citations by line number, with the resolutions).
- Verdict: **IMPLEMENT** (done): replace each `line NN` with its Decision or heading.

### T-040: `scripts/check_citations.py` cannot resolve `spec-NNN <Heading>` or the split / case / comment-wrapped citation forms
- Source: `docs/builder/DONE/build-028-orders-0_0_8.md` (`### Live and uncarded`, B1); `docs/builder/DONE/build-038-form_mutations-0_0_12.md` (`### Where the deferred catalog's 18 items went`, "Carded on `TODO-ALPHA-056-0.0.17`": the ordinal gate, extending `check_citations.py` to flag a `spec-<NNN>` followed by an ordinal token not on an allowlist, with en-dash-tolerant ranges and numbered-list / abbreviation resolution (`spec-028 DoD 4(c)`, `spec-043 scenario 4`, `spec-048 D1`)); `docs/builder/DONE/build-027-filters-0_0_8.md` (`## Surviving items migrated out of bld-final-027.md before its deletion`, "Two method findings no gate in this repository holds"); `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` (`### Deferred work catalog`, group D item 11, part (a): resolve `spec-<NNN> Decision <N>` in first-party `.py` against the spec's `### Decision <N>` headings)
- Original text: "the `scripts/check_citations.py` gate extension, five clauses": (1) a broken `spec-NNN <Heading>` citation; (2) a citation wrapped across two source lines; (3) a citation split mid-path-segment at a `/`; (4) a case variant, `Spec-028` versus `spec-028`; (5) a citation wrapped inside a `#` comment.
- Current state: Open. `scripts/check_citations.py` has no `Decision` / heading resolution and scans `#"` pinpoints one line at a time (`_scan_windows(text, '#"', wrap=False)`); clause (2) is T-018. Live demonstration cases: `examples/fakeshop/test_query/test_products_api.py` comment splitting `tests/rest_framework/` from `test_resolvers.py` (clause 3); `examples/fakeshop/test_query/test_library_api.py` `#"reuse_all=True"` wrapped pinpoint into Django (third-party target). Cross-cycle evidence for the card: the spec-027 cycle's final artifact certified "no wrapped citation introduced" over a hunk that was itself a wrapped join. The spec-038 ordinal-gate provisions (en-dash-tolerant range comparison; numbered-list and abbreviated-form resolution so `spec-028 DoD 4(c)`, `spec-043 scenario 4` and `spec-048 D1` are not false positives) are not in `scripts/check_citations.py` (`rg -i 'en.?dash|numbered' scripts/check_citations.py` returns nothing); which ordinal vocabularies stay legitimate (`Decision N`, `DoD N`, `TODO(spec-NNN slice N)`) is a maintainer policy call that gates the script.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 569 (clause 1 only, `spec-<NNN> Decision <N>` resolution, with its caveat); clauses 3-5 nowhere else.
- Verdict: **IMPLEMENT** (done): clauses 1 (`spec-NNN Decision N` resolution), 2 (T-018), 3 and 5 in `scripts/check_citations.py`. Drop clause 4 (a case variant is not rot) and the wider ordinal allowlist.

### T-043: `DONE-028-0.0.8` card body (`CardItem` 857) still carries stale claims
- Source: `docs/builder/DONE/build-028-orders-0_0_8.md` (`### Live and uncarded`, F1)
- Original text: "All the retired claims sit in **one** `CardItem` row ... `grows exactly 14 live HTTP tests` (16 functions / 19 rows); `reverse-FK with denormalized-multiplicity-pinned` ... the five-orderset roster where `orders.py` now declares seven; ... `Layer 6 ... deferred to 0.0.9`." Destination: DB edit plus `scripts/build_kanban_md.py` regenerate.
- Current state: Open. `kanban_carditem` 857 (card 28, read read-only from `examples/fakeshop/db.sqlite3`) still reads "Layer 6 (dynamic OrderSet generation) deferred to `0.0.9` alongside `DjangoConnectionField`", "grows exactly 14 live HTTP tests", "reverse-FK with denormalized-multiplicity-pinned", "Five-layer lazy-resolution pipeline" and a five-orderset roster (`examples/fakeshop/apps/library/orders.py` declares seven). The `check_permissions` and pre-archive-spec-path claims the build also listed are already fixed in that row.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 547 (carries only the "Layer 6 deferred to `0.0.9`" clause of this row).
- Verdict: **IMPLEMENT** (done): ORM edit of `CardItem` 857 plus render (same state-doc reasoning as T-020).

### T-044: Glossary `## RelatedOrder` entry narrates its own history ("not `filters.base` as named in earlier revisions")
- Source: `docs/builder/DONE/build-028-orders-0_0_8.md` (`### Live and uncarded`, F2 and F3; integration pass "findings" bullet on the deferred-work consolidation)
- Original text: "`## RelatedOrder` **narrates its own history** - \"not `filters.base` as named in earlier revisions\" - which is the shape `BUILD.md`'s rationale-extraction rule forbids in a spec, here sitting in a generated standing doc."
- Current state: Open. `docs/GLOSSARY.md` `## RelatedOrder` still contains "not `filters.base` as named in earlier revisions". (The F2 half, a missing position-side-channel note on `## OrderSet`, is moot: `docs/SPECS/spec-028-orders-0_0_8.md` no longer claims the glossary carries one.) Fix is a `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py`, never a hand-edit.
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): standing doc narrating its own history; drop the clause (glossary ORM edit).

### T-045: No test pins `filter_input_type` under PEP 563 deferred annotations
- Source: `docs/builder/DONE/build-027-filters-0_0_8.md` (`## Surviving items migrated out of bld-final-027.md before its deletion`, last "Still live" bullet)
- Original text: "The PEP-563 deferred-annotation path for `filter_input_type` has no dedicated test ... The spec's `## Test plan` licenses the absence as a coverage boundary ... -> `TODO-BETA-068-0.1.8`."
- Current state: Open. `rg test_filter_input_type_under_future_annotations tests` returns nothing; `tests/filters/test_inputs.py` pins repeat-safety (`test_filter_input_type_is_idempotent_under_repeated_calls`) but no `from __future__ import annotations` case for the helper. `docs/SPECS/spec-027-filters-0_0_8.md` states the PEP 563 behavior (two implications) without a test row. The board does not carry it: the build named `TODO-BETA-068-0.1.8`, and neither current 0.1.8 card (`TODO-BETA-071-0.1.8`, `TODO-BETA-072-0.1.8`) mentions it.
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): the spec states the PEP 563 behavior and no test pins it; add one.

### T-046: Scalar-scoped wording of the nullability overrides survives in `CHANGELOG.md` and spec-034
- Source: `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md` (`## Deferred-work homing`, `### Open — outside the fence`, rows 2 and 3)
- Original text: "`CHANGELOG.md` ... carries the same retired claim ('decouple a scalar field's GraphQL nullability', 'scalar-only')"; "`spec-034` says `Meta.nullable_overrides` is scalar-only (spec-029 Decision 10) - a cross-spec citation into a Decision this cycle renamed (`Scalar-only scope` -> `Non-relation scope`). Its conclusion still holds; only the cited reason is retired."
- Current state: Open. `CHANGELOG.md` line 143 (`[0.0.9]`, the `Meta.nullable_overrides` / `Meta.required_overrides` bullet) still says "decouple a scalar field's GraphQL nullability" and "scalar-only"; `docs/SPECS/spec-034-permissions-0_0_10.md` line 391 (the non-nullable forward-FK bullet) still says "is scalar-only (spec-029 Decision 10)". `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` `### Decision 10` now reads "Non-relation scope" and `docs/GLOSSARY.md` `**Non-relation scope.**` carries the corrected wording. The terms-CSV half (rows 14, 44, 45) is already fixed. `AGENTS.md` rule 22 makes the CHANGELOG edit the maintainer's call.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 574 (CHANGELOG half only); the spec-034 citation is nowhere else.
- Verdict: **IMPLEMENT** (done): fix the spec-034 citation (specs describe the current code). The CHANGELOG half is the maintainer's: it was already false at `0.0.9`, the release that shipped the non-relation scope.

### T-049: `tests/test_ci_governance.py` first docstring line still describes only the CI workflow corpus
- Source: `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md` (`## Deferred-work homing`, `### Open — outside the fence`, row 7; the cycle's Slice 2 Amendment 1)
- Original text: "`tests/test_ci_governance.py`'s first docstring line still reads 'Governance tests for the CI workflow definitions' now that the module carries a first-party-source pin ... the fix forces a `docs/TREE.md` regenerate (matches twice, once under each render root)."
- Current state: Open. `tests/test_ci_governance.py` line 1 still reads "Governance tests for the CI workflow definitions." while the following paragraph names the first-party `extensions=` form sweep; `docs/TREE.md` lines 503 and 792 render the same narrow line. The edit must ship with a `scripts/build_tree_md.py` regenerate (CI runs its `--check`).
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 302 (carries the item and the regenerate cost).
- Verdict: **IMPLEMENT** (done): one docstring line plus `scripts/build_tree_md.py`.

### T-051: No test pins Relay-pk-before-relation precedence in `_validate_nullability_override_targets`
- Source: `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md` (`## Deferred-work homing`, `### Open — test coverage and instrument integrity`, row 9)
- Original text: "The Relay-pk-before-relation precedence is a shipped contract pinned by no test ... no fixture pairs a relation pk with a Relay-shaped type and an override ... Owed row: a test naming such a pk in `nullable_overrides` and asserting the Relay message rather than the relation one."
- Current state: Open. `tests/types/test_base.py::test_override_relay_suppressed_pk_raises` uses `Category`'s plain `id` and `::test_override_relation_field_raises` a non-pk relation; no row combines a relation primary key with a Relay-Node-shaped type. The fixture pattern exists at `tests/optimizer/test_walker.py::test_plan_relay_id_projects_attname_when_pk_is_relation`.
- Also tracked: Nowhere else (the build named `TODO-BETA-068`, now a different card; `TODO-BETA-072-0.1.8` holds sibling jointly-pinned-boundary rows but not this one).
- Verdict: **IMPLEMENT** (done): one package test using the relation-pk fixture shape from `tests/optimizer/test_walker.py`.

### T-052: `_format_unknown_fields_error` docstring enumerates its callers
- Source: `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md` (`## Deferred-work homing`, `### Open — test coverage and instrument integrity`, row 11)
- Original text: "`types/base.py::_format_unknown_fields_error` enumerates its callers ... Currently complete and correct, but carries the same rot risk Slice 4's Decision 1 removed from `_selected_meta_targets`. Left alone deliberately, not overlooked."
- Current state: Open (latent). The docstring of `django_strawberry_framework/types/base.py::_format_unknown_fields_error` still lists `Meta.fields`, `Meta.exclude`, `Meta.optimizer_hints`, `Meta.nullable_overrides`, `Meta.required_overrides`, `Meta.filesystem_path_fields` and `Meta.relation_shapes`; the list is complete today.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 285 (the same docstring, under the unknown-fields error-shape item).
- Verdict: **IMPLEMENT** (done): replace the caller list with a non-enumerating phrase.

### T-053: Glossary connection entries never say `totalCount` gating is directive-resolved
- Source: `docs/builder/DONE/build-030-connection_field-0_0_9.md` (`## Deferred-work homing`, `### Open`, bullet MF-1)
- Original text: "the three `030` glossary entries never say `totalCount` gating is directive-resolved (`optimizer/selections.py::should_include`). DB-backed regenerate."
- Current state: Open. `docs/GLOSSARY.md` `## DjangoConnection`, `## DjangoConnectionField` and `## Meta.connection` say nothing about `@skip` / `@include` on `totalCount` (the file's only `@skip` / `@include` hit is the plan-cache key bullet in the optimizer entry). The gate is `django_strawberry_framework/optimizer/selections.py::should_include`, live-pinned by `examples/fakeshop/test_query/test_library_api.py::test_genre_connection_total_count_skip_include_no_count`. Fix is a `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py`.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 559.
- Verdict: **IMPLEMENT** (done): one glossary sentence (ORM edit).

### T-054: Keyset-cursor feature (`Meta.cursor_field`) has no owning spec and no glossary heading
- Source: `docs/builder/DONE/build-030-connection_field-0_0_9.md` (`## Deferred-work homing`, `### Open`, bullet MF-2 + MF-3 + MF-7)
- Original text: "the keyset / `Meta.cursor_field` feature is missing all three of its documentation homes: no owning spec, no glossary heading, no CHANGELOG entry" (one maintainer decision, not three).
- Current state: Open for two of three. `docs/GLOSSARY.md` has no `## Meta.cursor_field` heading (`rg -n '^## .*cursor_field'` empty; the key is referenced from other entries) and `docs/SPECS/` has no keyset / cursor spec. The CHANGELOG home is done: `CHANGELOG.md` `[0.0.14]` carries "Stable encrypted keyset cursors — `Meta.cursor_field`". The surface ships in `django_strawberry_framework/types/base.py::ALLOWED_META_KEYS` and `django_strawberry_framework/keyset.py`.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 563 (its "no CHANGELOG entry" clause is stale).
- Verdict: **IMPLEMENT** (done): author `## Meta.cursor_field` in the glossary, and put the keyset contract in `docs/SPECS/spec-030-connection_field-0_0_9.md` (connection owner) rather than a new spec.

### T-055: Already-sliced `QuerySet` `GraphQLError` on a connection `resolver=` is undocumented
- Source: `docs/builder/DONE/build-030-connection_field-0_0_9.md` (`## Deferred-work homing`, `### Open`, bullet MF-4)
- Original text: "the already-sliced-`QuerySet` `GraphQLError` is undocumented in both `CHANGELOG.md` and `docs/GLOSSARY.md`, under five tested spellings."
- Current state: Open. `django_strawberry_framework/connection.py::_guard_source_not_pre_sliced` raises it; `rg -i 'pre-sliced|already-sliced|already sliced'` over `CHANGELOG.md` and `docs/GLOSSARY.md` returns 0 (the sealed-visibility entries mention sliced results only for the filter / order recomposition refusal). Glossary fix is a `GlossaryTerm.body` ORM edit plus `scripts/build_glossary_md.py`.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 560.
- Verdict: **IMPLEMENT** (done): one glossary sentence (ORM edit); skip the CHANGELOG.

### T-058: Nested-connection strictness probe answers "attribute present", not "the window was consumed"
- Source: `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` (`### Deferred work catalog`, group A item 1; `## Escalations`, item 1)
- Original text: "The `connection_to_attr` strictness probe answers 'attribute present', not 'the window was consumed' ... three refusal shapes read as 'served' and `"raise"` stays silent on a real per-parent query." Paths: thread the resolver's already-computed boolean and restate Decision 8's third condition, or accept it and record in Decision 8 that a `_dst_`-namespace write can silence strictness.
- Current state: Open. `django_strawberry_framework/types/resolvers.py::_check_n1` still computes `lazy = getattr(root, to_attr, None) is None` for `kind == "connection_to_attr"`, and `django_strawberry_framework/connection.py::_build_relation_connection_resolver` still passes the probed `to_attr` rather than the resolver's own served/unserved answer. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (closing paragraph under its questions section) records it only as a standing limitation pointing at the rationale companion's Risks section; `rg -i 'strictness probe|window was consumed|attribute present' KANBAN.md BACKLOG.md` is empty.
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): root-cause fix: pass the resolver's served / unserved answer into `_check_n1`; strictness `"raise"` is silent today on real per-parent queries.

### T-059: The nested-connection fetch-strategy seam has no owning spec
- Source: `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` (`### Deferred work catalog`, group A item 4; `## Cycle outcome`)
- Original text: "The nested-connection strategy seam has no owning spec, and it is the root cause of items 1-3 ... R1c argues for opening a card for the seam and moving the inverted contracts onto its spec, which is what the package's 'every shipped surface has an owning spec' posture implies."
- Current state: Open. No file under `docs/SPECS/` has the seam (`django_strawberry_framework/optimizer/nested_fetch.py`, `lateral_fetch.py`, `single_parent_fetch.py`, `join_taxonomy.py`) as its subject. `docs/SPECS/spec-068-structural_templates-0_1_6.md` `### Decision 9` only requires pluggable strategies to consume the sidecar pipeline; the only released-doc records are the `CHANGELOG.md` `[0.0.14]` "Pluggable nested-connection fetching" bullet and the strategy paragraph in `docs/GLOSSARY.md`. `rg -i 'strategy seam' KANBAN.md` is empty.
- Also tracked: Partly `docs/SPECS/spec-068-structural_templates-0_1_6.md` `### Decision 9` and the `BACKLOG.md` strategy-extension entries (`sqlite_correlated_json_nested_fetch`, `mti_aware_lateral_nested_fetch`); no card owns the seam itself.
- Verdict: **IMPLEMENT** (done): the seam needs an owning spec (START.md: a surface with no owning spec inverts the specs describing it); open a card for it.

### T-061: Relocate the `to_attr` grammar from `optimizer/nested_planner.py` to `utils/connections.py`
- Source: `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` (`### Deferred work catalog`, group C item 6)
- Original text: "`connection.py` imports `_extend_only_projection`, `_relation_connection_to_attr` and `_relation_connection_to_attr_for_key` from `optimizer.nested_planner` ... Decision 11 created `utils/connections.py` as 'a neutral, cycle-safe home' ... the `to_attr` grammar is as much a cursor-parity contract as the bounds are ... The argument is placement, not the privacy of the imported names."
- Current state: Open. `django_strawberry_framework/connection.py` still imports `_extend_only_projection` and `relation_connection_to_attr` from `.optimizer.nested_planner` and uses the latter at the resolver's per-key probe (`::_build_relation_connection_resolver`); `django_strawberry_framework/utils/connections.py` carries no `to_attr` grammar. The per-key variant is now one function, `nested_planner.py::relation_connection_to_attr(relation_field_name, response_key=None)`.
- Also tracked: Card `TODO-ALPHA-053-0.0.15` (Boundary hardening and system-wide DRY squeeze), `KANBAN.md` line 306.
- Verdict: **IMPLEMENT** (done): move the `to_attr` grammar to `utils/connections.py`, ending `connection.py`'s import of `nested_planner` names. `connection.py` is dirty from another session; wait for it to land.

### T-062: Name the `_optimizer_runtime_prefixes` attribute string
- Source: `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` (`### Deferred work catalog`, group C item 8)
- Original text: "The **string literal** occurs twice, in one module (`optimizer/walker.py`, both inside `getattr`); `optimizer/selections.py` carries the name as a keyword argument. Still a real cross-seam attribute-name grammar with no named constant, and still cheap."
- Current state: Open. `django_strawberry_framework/optimizer/walker.py::_selection_runtime_prefixes` (a `getattr` tuple entry) and `::_merge_runtime_prefixes` (a `read_attr(merged, ...)` call) each spell the literal; `django_strawberry_framework/optimizer/selections.py::with_runtime_prefix` passes it as a keyword argument; no named constant exists.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 308.
- Verdict: **IMPLEMENT** (done): a typo in either `getattr` literal reads the default silently (fail-open); one named constant.

### T-064: `tests/test_relay_connection.py` has no safe default for a bare `Decision N`
- Source: `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` (`### Deferred work catalog`, group D item 10)
- Original text: "Its module docstring cites `spec-032` while its body carries live references belonging to `spec-030`, `spec-032`, `spec-033` and `spec-047` ... Remedy: qualify every bare reference in that file with its `spec-0NN` prefix ... **Not a spec edit.**"
- Current state: Open. A whitespace-flattened scan of `tests/test_relay_connection.py` finds 19 `Decision N` references, 8 with no `spec-0NN` / `SPECS/spec` within 60 characters before them (for example "Decision 6 sidecar fallback", "Decision 4: the fast path's ...", "Decision 5: the resolver ..."); the docstring names only `spec-032` Decisions 6/7/11. The board's 24 / 16 figures came from a different instrument.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 568.
- Verdict: **IMPLEMENT** (done): qualify the eight bare references; same sweep as T-038.

### T-066: ARTIFACT.md defines who sets `Status:` but not when it may be read as a completion signal
- Source: `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` (`### Deferred work catalog`, group F item 18; R3 checklist entry, "Worker-0 dispatch error")
- Original text: "`BUILD.md`'s dispatch loop keys off a `Status:` line a worker writes before it finishes appending ... The durable fix is a dispatch rule ... **wait for the agent's own completion signal, not for the file to change.** `ARTIFACT.md` `## Status field ownership` defines who sets the line but not when it may be *read*."
- Current state: Not found in tree: `docs/builder/ARTIFACT.md` `## Status field ownership` still only lists the per-transition owners and says Worker-0 "reads it to drive dispatch"; `rg -i "completion signal|own completion|wait for the agent" docs/builder/*.md` is empty. Process-doc edit under `BUILD.md`'s corpus ratchet.
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): one sentence in `ARTIFACT.md`: read `Status:` only after the worker's agent call returns.

### T-067: `_is_unsupported_forward_edge` reads `is_relation` through `getattr` with a fail-open default
- Source: `docs/builder/DONE/build-034-permissions-0_0_10.md` (`## Deferred-work disposition`, row on `permissions.py::_is_unsupported_forward_edge`)
- Original text: "`permissions.py::_is_unsupported_forward_edge`'s `getattr(field, "is_relation", False)` fail-open ... `TODO-ALPHA-051-0.0.15`, with both resolution paths recorded. Unreachable at `HEAD` (closed input population), so hardening rather than a bug."
- Current state: Open. `django_strawberry_framework/permissions.py::_is_unsupported_forward_edge` still opens with `getattr(field, "is_relation", False)` while its sibling predicates use plain attribute access; the sole caller `::_edge_plan` feeds it `model._meta.get_fields()`. Paths: read `field.is_relation` directly (an unanswerable shape raises), or keep it and record the closed-population argument in the docstring.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 310.
- Verdict: **IMPLEMENT** (done): read `field.is_relation` directly and drop the fail-open default.

### T-069: No `FAKESHOP_SHARDED` row pins a `Prefetch` child's `.db` under an active cascade
- Source: `docs/builder/DONE/build-034-permissions-0_0_10.md` (`## Deferred-work disposition`, row on `FAKESHOP_SHARDED` and the `Prefetch` child)
- Original text: "No `FAKESHOP_SHARDED` row asserts a `Prefetch` child's `.db` under an active cascade."
- Current state: Open. `tests/test_permissions.py::test_multi_db_subquery_pinned_to_caller_alias` (sharded-gated) pins the cascade subquery's alias for a `.using("shard_b")` caller only; `rg -ci cascad tests/optimizer/test_multi_db.py examples/fakeshop/test_query/test_multi_db.py` returns 0 for both.
- Also tracked: Card `TODO-BETA-072-0.1.8` (Adversarial non-live test suite), `KANBAN.md` line 1629.
- Verdict: **IMPLEMENT** (done): a sharded test pinning a `Prefetch` child's alias under an active cascade.

### T-070: `seed_cascade_split` has no per-app test
- Source: `docs/builder/DONE/build-034-permissions-0_0_10.md` (`## Deferred-work disposition`, row on `services.py::seed_cascade_split`)
- Original text: "`services.py::seed_cascade_split` has no per-app test."
- Current state: Open. `examples/fakeshop/apps/products/tests/test_services.py` mentions the helper only in a membership assertion over the module's public helpers; nothing calls it there. It is exercised through `examples/fakeshop/test_query/test_products_api.py` and `test_list_field_api.py`.
- Also tracked: Card `TODO-BETA-067-0.1.5`, `KANBAN.md` line 1332.
- Verdict: **IMPLEMENT** (done): per-app test (`AGENTS.md`: each app carries its own coverage).

### T-072: Fifth carry-forward anchor `TODO(spec-035)` in `test_library_api.py` still names the build spec
- Source: `docs/builder/DONE/build-035-optimizer_hardening-0_0_10.md` (`## Final report`, `### Deferred work: final disposition`, D1; `### Verified code state`, deviation 5)
- Original text: "The fifth carry-forward anchor at `examples/fakeshop/test_query/test_library_api.py:3680` is still `TODO(spec-035)` ... `TODO-ALPHA-053-0.0.15` -- the only card whose sweep opens that file."
- Current state: Open. `rg 'TODO\(spec-035' --glob '*.py'` returns exactly one hit, `examples/fakeshop/test_query/test_library_api.py` #"TODO(spec-035): extend this live connection-fragment block"; the other four sites carry `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)`. Only the head swap is owed; the anchor itself must stay.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 312.
- Verdict: **IMPLEMENT** (done): retarget the anchor head to the BACKLOG card, like its four siblings.

### T-075: The `0.0.14` mutation write hardening has no owning spec
- Source: `docs/builder/DONE/build-036-mutations-0_0_11.md` (`## R1 outcome`, "Contract-level findings escalated to the maintainer"; `## Maintainer decisions`, Decision A; `## Deferred-work disposition`, "The load-bearing item")
- Original text: "The `0.0.14` write hardening has no owning spec, and `spec-036` is not it. Nine specs carry the `0_0_14` segment and none scopes the completion-spanning transaction, the `DjangoSchema` requirement, `Meta.select_for_update`'s lock semantics, single-write-alias pinning, the retryable `conflict` envelope, the immutable authorized-pk snapshot, the phased alias guard, the strict-`bool` authorization contract, or the point-in-time authorization rule."
- Current state: Open. No `docs/SPECS/spec-*.md` takes the write pipeline's transaction / lock / authorization semantics as its subject; `rg -c 'select_for_update|require_managed_write|DjangoMutationExecutionContext' docs/SPECS` tops out at `spec-039-serializer_mutations-0_0_13.md` (18).
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 589.
- Verdict: **IMPLEMENT** (done): same as T-059: the write pipeline needs an owning spec; open a card.

### T-078: Should `FieldError` / `NON_FIELD_ERROR_KEY` live in `mutations/inputs.py` at all
- Source: `docs/builder/DONE/build-036-mutations-0_0_11.md` (`## R1 outcome`, "Two DRY ownership findings", R1a N6; `## Deferred-work disposition`, `TODO-ALPHA-053-0.0.15` bullet)
- Original text: "the neutral `utils/` layer three write flavors share depends **upward** on `mutations/inputs.py` for `FieldError`, paid for with two function-local imports whose stated purpose is dodging an import cycle." Contract-level: the answer decides a WP-A `import-linter` contract; a move owes a re-export because `FieldError` is a public root export.
- Current state: Open. `django_strawberry_framework/utils/errors.py`, `utils/write_transaction.py` and `utils/write_values.py` each still import `FieldError` (and `NON_FIELD_ERROR_KEY`) from `django_strawberry_framework.mutations.inputs` inside function bodies (one carries `# noqa: PLC0415 - import cycle`).
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 315.
- Verdict: **IMPLEMENT** (done): move `FieldError` / `NON_FIELD_ERROR_KEY` down into `utils/` and re-export them from `mutations.inputs` and the root; this deletes the cycle-dodging local imports.

### T-079: Should `mutations/sets.py` own the cross-flavor write substrate
- Source: `docs/builder/DONE/build-036-mutations-0_0_11.md` (`## R1 outcome`, "Two DRY ownership findings", R1b DRY-1; `## Deferred-work disposition`, `TODO-ALPHA-053-0.0.15` bullet)
- Original text: "`mutations/sets.py` (1,606 lines) has become the cross-flavor write substrate -- 25 distinct symbols imported out by `forms/sets.py`, `rest_framework/sets.py`, and `auth/mutations.py`, 4 private-by-name and 6 helpers with zero caller inside `mutations/` -- with `sets_mixins.py` the exact precedent and the home Decision 4 predicted."
- Current state: Open (contract-level, maintainer call). `django_strawberry_framework/mutations/sets.py` is now about 2,000 lines and is still imported by `forms/sets.py`, `forms/resolvers.py`, `rest_framework/sets.py`, `rest_framework/resolvers.py`, `auth/mutations.py`, `types/finalizer.py` and `utils/write_transaction.py`; the 25 / 6 figures were not re-derived.
- Also tracked: Card `TODO-ALPHA-053-0.0.15` (WP-B), `KANBAN.md` line 316.
- Verdict: **IMPLEMENT**: under card 053 WP-B: extract the cross-flavor substrate out of `mutations/sets.py`. Large; the file is dirty from another session now.

### T-083: No gate greps for a staged `TODO(spec-NNN ...)` anchor
- Source: `docs/builder/DONE/build-036-mutations-0_0_11.md` (`## R1 outcome`, "The two SKIPPED contracts", item 1; `## Deferred-work disposition`, "Homed on cards", the `TODO-ALPHA-056-0.0.17` bullet "the absent staged-anchor gate")
- Original text: "Why it rotted for four release lines: no gate greps for it. Verified by Worker 0 -- `grep -rn 'TODO(spec-'` over `scripts/`, `.pre-commit-config.yaml`, and `.github/workflows/` returns nothing."
- Current state: Open. `rg 'TODO\(spec' scripts .pre-commit-config.yaml .github/workflows tests/test_ci_governance.py` returns nothing. Source carries 3 `TODO(spec-` hits today: `django_strawberry_framework/filters/sets.py` and `django_strawberry_framework/filters/inputs.py` (`TODO(spec-060 Slice 1)`, a live staged anchor) and `examples/fakeshop/test_query/test_library_api.py` (`TODO(spec-035)`, see the T-072 entry).
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 591.
- Verdict: **IMPLEMENT** (done): a governance test that every `TODO(spec-NNN ...)` names an existing spec whose card is not done.

### T-084: No test pins that excluding a file / image column removes it from the read-side SDL and resolver set
- Source: `docs/builder/DONE/build-037-upload_file_image_mapping-0_0_11.md` (`### Not dispatched, and why`, the file-column read-side `Meta.exclude` bullet; `### Board-DB enactment`, card `TODO-ALPHA-054-0.0.16` paragraph)
- Original text: "The file-column read-side `Meta.exclude` test homes on `TODO-ALPHA-054-0.0.16` ... its byte-identity DoD needs the exclusion path pinned before that refactor, not after."
- Current state: Open. No test excludes a `FileField` / `ImageField` column from a read `DjangoType`: `tests/types/test_base.py::test_exclude_accepts_a_frozenset_too` excludes the scalar `label` and asserts `attachment` stays; the file-column `exclude` pins found are write-side only (`tests/mutations/test_inputs.py::test_file_field_narrowed_by_meta_fields_and_exclude`). `django_strawberry_framework/types/converters.py::FIELD_OUTPUT_TYPE_MAP` and `types/resolvers.py::_attach_file_resolvers` special cases still exist, so the card's migration has not happened.
- Also tracked: Card `TODO-ALPHA-054-0.0.16` (Pluggable field-conversion registry), `KANBAN.md` line 415 (scope item) and line 447 (`related` reference).
- Verdict: **IMPLEMENT** (done): pin it now, before card 054's refactor.

### T-085: Subprocess-isolation idiom spelled inline at every test site, with no shared helper
- Source: `docs/builder/DONE/build-040-auth_mutations-0_0_13.md` (`### Final gate`, the census-trap paragraph; `### Slice 7`, the card-53 row homing)
- Original text: "the subprocess idiom first measured 7 files (`tests/base/test_init.py` builds argv into a local, invisible to the regex; the bare `sys.executable` token recovers it at 8)" and Slice 7's "two new `Scope` `CardItem` rows -- card 53 (`TODO-ALPHA-053-0.0.15`, order 64) for the subprocess idiom".
- Current state: Open. `tests/auth/test_mutations.py::_auth_free_subprocess` is a file-local prototype (fakeshop `sys.path` + `DJANGO_SETTINGS_MODULE` + `django.setup()` prologue, body appended, return code asserted); `rg -c 'sys\.executable' tests` still finds the inline spelling in `tests/test_scalars.py`, `tests/base/test_init.py`, `tests/auth/test_sessions.py`, `tests/orders/test_inputs.py`, `tests/filters/test_finalizer.py`, `tests/filters/test_sets.py` and `tests/rest_framework/test_soft_dependency.py`; no shared `tests/` helper exists.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 324 (carries the population, the instrument trap and the prototype).
- Verdict: **IMPLEMENT** (done): add a `tests/_subprocess.py` helper, following the `tests/_soft_dependency.py` precedent.

### T-087: No `DEBUG_TOOLBAR_FLOOR` constant or governance row, and the DRF twin's `three-places-that-must-agree` comment counts a spec Decision as a gated site
- Source: `docs/builder/DONE/build-042-debug_toolbar-0_0_14.md` (catalog items 3 and 4 of the retired `bld-042-final.md`, `git show 50b7d489:docs/builder/bld-042-final.md`; the build file's `M4` finding and the `## The cycle's instrument failures` section cover the same population)
- Original text: "The DRF twin is the package's last false-population comment" (`rest_framework/__init__.py` and `tests/rest_framework/test_soft_dependency.py` name three places for `djangorestframework>=3.17.0`, and no `tests/test_ci_governance.py` row gates the `pyproject.toml` side); "The `DEBUG_TOOLBAR_FLOOR` refinement, trigger fired" (hoist the toolbar floor beside `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR`, interpolate it into the hint, gate it beside the two existing rows).
- Current state: Open. `rg DEBUG_TOOLBAR_FLOOR` finds nothing; `django_strawberry_framework/utils/imports.py` declares only `CHANNELS_FLOOR` and `STRAWBERRY_FLOOR`, and `7.0.0` is typed literally into `_DEBUG_TOOLBAR_INSTALL_HINT` in `django_strawberry_framework/middleware/debug_toolbar.py` (line 102). `tests/test_ci_governance.py` has the Channels and Strawberry floor-vs-`pyproject.toml` rows (around lines 1020-1043) and no toolbar or DRF row. `django_strawberry_framework/rest_framework/__init__.py` module docstring and `tests/rest_framework/test_soft_dependency.py` still say "place 2 of the three-places-that-must-agree" with the spec-039 Decision as place 3. The toolbar side already separates gated sites from a census (middleware and test comments).
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 326 (lands as one change with the floor decision above).
- Verdict: **IMPLEMENT** (done): add `DEBUG_TOOLBAR_FLOOR` and a DRF floor constant, each with a governance row; make the "three places" comment count only gated sites.

### T-090: `scripts/prove_failability.py` verdict arithmetic has no row-isolation case (a one-row success reads `WEAKLY PINNED - revision-needed`)
- Source: `docs/builder/DONE/build-042-debug_toolbar-0_0_14.md` (`## Decided - do not re-raise`, item 4)
- Original text: "It labels a one-row result `WEAKLY PINNED - revision-needed` because the arithmetic is written for boundary proofs ... A row-isolation proof seeks exactly one row, and a second would falsify it, so the tool's line reads as a finding against a proof that succeeded. Twice in this cycle a pass had to write a paragraph explaining the verdict does not apply."
- Current state: Open. `scripts/prove_failability.py` (around the `is_weakly_pinned` note, `**WEAKLY PINNED - revision-needed**`) has no row-isolation mode (`rg -i 'row.isolation' scripts/prove_failability.py` empty).
- Also tracked: Card `TODO-BETA-072-0.1.8`, `KANBAN.md` line 1631 (beside that card's failability-manifest item).
- Verdict: **IMPLEMENT** (done): add a row-isolation mode so a successful one-row proof stops reading as a finding.

### T-091: No gate fails an undeclared raw `.post(` / `.generic(` in `examples/fakeshop/test_query/`; three files would fail it first
- Source: `docs/builder/DONE/build-043-test_client-0_0_14.md` (`## Maintainer decisions taken mid-cycle`, Decision 3, closing sentence of the `test_list_field_async_api.py` paragraph; catalog items 1-3 of the retired `bld-043-final.md`, `git show c536fdc3:docs/builder/bld-043-final.md`)
- Original text: "No gate fails a raw `.post(` / `.generic(` on a Django client in `examples/fakeshop/test_query/` that carries no exemption declaration" (spec-043 Decision 11 has never had a gate); three files retain a raw posture declared under a different regime (`test_transport_api.py` and `test_auth_api.py`: the `graphql_client.py` raw-envelope exemption; `test_list_field_async_api.py`: the sync-only exemption over one raw `AsyncClient` post, a file the spec-050 cycle owned).
- Current state: Open. Nothing in `scripts/` or `.pre-commit-config.yaml` inspects live-tier HTTP call shapes. `rg 'AsyncClient|\.post\(|\.generic\(' examples/fakeshop/test_query/*.py` still shows raw posts in `test_list_field_async_api.py` (`await http_client.post(`), `test_transport_api.py`, `test_resource_policy_api.py` (`Client().post(` and an `AsyncClient()` site), `test_relation_deadline_api.py` and `test_products_api.py`; each retained site's declaration was not re-graded today. The spec-043 text was rewritten as a rule over the switchover's own population, so a conversion needs no spec amendment.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 327 (carries the gate, the `.post(` AND `.generic(` counting note and the three files).
- Verdict: **IMPLEMENT** (done): a governance test for raw `.post(` / `.generic(` in `examples/fakeshop/test_query/` without a declared exemption.

### T-092: Shared async post helper for the live tier is undecided, and the live-tier `README.md` `Async` bullet is falsified until it is
- Source: `docs/builder/DONE/build-043-test_client-0_0_14.md` (`## Items Cohort D routed to Worker 0`, item 1; `## Escalation pending: the async-helper extraction (Cohort D, final verification)`)
- Original text: "Extracting a shared async post helper reverses `examples/fakeshop/graphql_client.py`'s stated sync-only contract and runs into `AGENTS.md`'s async-exemption rule. That is a contract choice, not a worker's call." Plus: the `examples/fakeshop/test_query/README.md` `Async` bullet names `django.test.AsyncClient` and a helper exemption for both `test_list_field_async_api.py` and `test_relations_async_api.py` while the second drives `AsyncTestClient` and declares no exemption; its corrected text depends on the decision.
- Current state: Open. `examples/fakeshop/test_query/README.md` (the `- **Async.**` bullet, around line 917) is unchanged: it still lists `test_relations_async_api.py` under `django.test.AsyncClient` with "declare the helper exemption". The near-copy `AsyncTestClient().query(...)` bodies are still spread over the converted live modules, plus `test_kanban_mutations_api.py` and the raw post in `test_list_field_async_api.py`; no shared async helper exists and `examples/fakeshop/graphql_client.py` is still sync-only. Both options and the corrected wording lived in the retired `bld-043-review-4-live_conversion.md` (`git show 974d25b4:docs/builder/bld-043-review-4-live_conversion.md`).
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 328 (decision bullet; fallback home for the README fix is `TODO-ALPHA-056-0.0.17` if the answer is "no helper").
- Verdict: **IMPLEMENT** (done): the README fix only: async modules drive the package's own `django_strawberry_framework.testing.AsyncTestClient`. No new helper; `graphql_client.py` stays sync-only.

### T-094: Eight glossary terms card 046 authored are absent from the spec-046 terms CSV and from the card's glossary links
- Source: `docs/builder/DONE/build-046-transport_security-0_0_15.md` (`## Closeout checklist`, box `R3`, phase A "the six orphaned terms plus the CSV rows that link them"; `## Worker-0-verified facts`, V6); also catalog item 2 of the retired `bld-final.md` (`git show 97dc05d7:docs/builder/bld-final.md`, "The terms CSV stays at 37 rows")
- Original text: "`docs/spec-046-transport_security-0_0_15-terms.csv` holds only the 37 pre-existing terms the spec *references* and no row for any term the card *introduced*, so `import_spec_terms` creates no `CardGlossaryTerm` for them."
- Current state: Open. `docs/SPECS/appx/spec-046-transport_security-0_0_14-terms.csv` still has 37 rows (38 lines with the header). `docs/GLOSSARY.md` carries all eight entries (`DjangoGraphQLView`, Request-body cap, UTF-8 wire contract, WebSocket consumer-injection seam, WebSocket revalidation window, Connection-scoped revocation, WebSocket Host boundary, `GraphQLRequestBodyBoundaryMiddleware`), none linked to card 046. The rest of that R3 box landed: spec archived, `docs/TREE.md` lists `middleware/request_body.py`, the card body no longer names the review file.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 573 (carries the fix order and the distinct-anchor and spec-link constraints).
- Verdict: **IMPLEMENT** (done): add the eight CSV rows, then `manage.py import_spec_terms`.

### T-096: spec-046 Decision 7 says the body-size probe "reaches for four capabilities"; the code guards six calls
- Source: catalog item 13 of the retired generic-named `bld-final.md` of the card-046 build (`git show 97dc05d7:docs/builder/bld-final.md`); `docs/builder/DONE/build-046-transport_security-0_0_15.md` carries no pointer to it
- Original text: "Decision 7 says the probe 'reaches for **four** capabilities'; the code guards **six** call sites across **five** `try` blocks ... `## Edge cases`'s capability bullet repeats the same four-item list, so the fix has two sites."
- Current state: Open. `docs/SPECS/spec-046-transport_security-0_0_14.md` Decision 7 (`**An unmeasurable stream has three outcomes, not two.**`) still reads "The size probe reaches for four capabilities"; call-site count in `django_strawberry_framework/_request_body.py` not re-derived.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 272.
- Verdict: **IMPLEMENT** (done): re-derive the count and fix both spec sites, or drop the number.

### T-097: `send_revalidated_operation_frame` docstring still calls the derived adapter a "two-line delegation"
- Source: catalog item 14 of the retired `bld-final.md` (`git show 97dc05d7:docs/builder/bld-final.md`)
- Original text: "`consumers.py::send_revalidated_operation_frame`'s docstring says the derived adapter stays a 'two-line delegation'; `_RevocationGatedWebSocketAdapter.send_json`'s body is **four** statements." Pre-measured replacement: "a four-statement delegation - the frame-type test, the plain `super()` delegation for a non-information-bearing frame, its `return`, and the gated call".
- Current state: Open. `django_strawberry_framework/consumers.py::send_revalidated_operation_frame` docstring still reads "what lets the derived adapter stay a two-line delegation"; `::_RevocationGatedWebSocketAdapter.send_json` carries two arms with a docstring of its own.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 273.
- Verdict: **IMPLEMENT** (done): drop the count ("a thin delegation") rather than restate it.

### T-098: The WebSocket `Host` denial logs nothing while the other fail-closed paths do
- Source: catalog item 8 of the retired `bld-final.md` (`git show 97dc05d7:docs/builder/bld-final.md`, "L9")
- Original text: "the third fail-closed path logs nothing ... Recommendation from three separate passes, unchanged: **log all three, no wire change.**" Django's `django.security.DisallowedHost` logging was read at 6.0.5 and unconfirmed at the floor.
- Current state: Open. The `except DisallowedHost:` arm in `django_strawberry_framework/consumers.py` (the Host validator's `__call__`) returns Channels' `WebsocketDenier` with no logger call; the module's other failure arm logs through `logger.exception`.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 274 (contract-level; floor confirmation still owed).
- Verdict: **IMPLEMENT** (done): log the denial on `django.security.DisallowedHost`, as Django does for HTTP; no wire change.

### T-099: `conf.py` `MAX_REQUEST_BODY_BYTES` comment says "EXCEPT for a multipart request" without the POST scope
- Source: catalog item 9 of the retired `bld-final.md` (`git show 97dc05d7:docs/builder/bld-final.md`, "the fifth L3 surface"); `docs/builder/DONE/build-046-transport_security-0_0_15.md` (round-2 W3 review summary: "`conf.py:117` remains genuinely open as the maintainer's", clause removed with this entry)
- Original text: the carve-out clause is POST-scoped in the spec, the views and the other four surfaces of the wording; `conf.py` is the one surface that omits it (maintainer's own file, never edited by a worker).
- Current state: Open. `django_strawberry_framework/conf.py` comment above `MAX_REQUEST_BODY_BYTES_KEY` still reads "- EXCEPT for a multipart request, whose bound is the declaration plus Django's own ``MultiPartParser``" with no method scope (`rg 'POST-scoped' django_strawberry_framework/conf.py` empty). The sibling clause on `UPSTREAM_PATCH_DEPENDENCIES` was already corrected.
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 275.
- Verdict: **IMPLEMENT** (done): add the POST scope to the comment; maintainer's file.

### T-101: spec-046 DRY `parse_json` bullet attributes `_validate_upstream_shape` to "the upstream-mounted path"
- Source: catalog item 18 of the retired `bld-final.md` (`git show 97dc05d7:docs/builder/bld-final.md`, custodian item 8)
- Original text: "That gate decides whether the patch installs at all, for **every** mount, so pairing it with the genuinely path-scoped `UnicodeDecodeError` translation under one prepositional phrase is loose."
- Current state: Open. `docs/SPECS/spec-046-transport_security-0_0_14.md` DRY section still reads "`_validate_upstream_shape` gate for the upstream-mounted path".
- Also tracked: Card `TODO-ALPHA-053-0.0.15`, `KANBAN.md` line 277.
- Verdict: **IMPLEMENT** (done): one-phrase spec fix.

### T-102: `tests/test_views.py::_strawberry_patch_opted_out` does not assert the patch is actually un-installed
- Source: catalog item 10 of the retired `bld-final.md` (`git show 97dc05d7:docs/builder/bld-final.md`, "L-B")
- Original text: "`tests/test_views.py::_strawberry_patch_opted_out` lacks the live copy's `assert strawberry_patches._patch_is_installed() is False`. Nothing pins that the package-tier simulation really un-installed the patch."
- Current state: Open. The helper (restores `BaseView.parse_json` / `parse_query_params`, sets the setting, yields) contains no `_patch_is_installed` assertion; the only `_patch_is_installed() is False` in the file is the cross_web one in a different test.
- Also tracked: Card `TODO-BETA-072-0.1.8` (Adversarial non-live test suite), `KANBAN.md` line 1624.
- Verdict: **IMPLEMENT** (done): add the `_patch_is_installed() is False` assertion.

### T-103: `BACKLOG.md` describes the protocol router as serving HTTP + WebSocket in the present tense
- Source: catalog item 6 of the retired `bld-final.md` (`git show 97dc05d7:docs/builder/bld-final.md`, "L5")
- Original text: "`BACKLOG.md:1616` / `:1661` describe the router as serving HTTP + WebSocket in the present tense. Owner: a future spec author. Deliberately outside spec-046's `## Doc updates` set."
- Current state: Open. `BACKLOG.md` (now lines 1746 and 1793, `Transport substrate: **shipped**`) still says `DjangoGraphQLProtocolRouter` "already wires Strawberry's Channels consumers onto HTTP + WebSocket" / "carries queries over WebSocket"; since card 046 the router owns only the WebSocket route and Django owns HTTP.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 527 (cites the old line numbers `:1616` / `:1661`).
- Verdict: **IMPLEMENT** (done): correct the two BACKLOG sentences.

### T-104: BUILD.md does not say a Worker-0 dispatch finding is a hypothesis to re-verify
- Source: `docs/builder/DONE/build-046-transport_security-0_0_15.md` (`### Three Worker-0 dispatch findings the Slice 5 planning pass refuted`, closing "Retrospective candidate for closeout" paragraph, removed with this entry)
- Original text: "a finding stated in a dispatch prompt is a *hypothesis to re-verify*, exactly like a review's prescribed remediation. `BUILD.md` already says a worker may not treat a review's prescription as authority; it does not say the same of Worker 0's own pre-verified findings, and it should."
- Current state: Not found in tree: `docs/builder/BUILD.md` `### Worker-0 verifies every finding against source before dispatching` says only that "a prescribed fix is a hypothesis, never an instruction"; `rg -i 'hypothes|pre-verified' docs/builder/worker-*.md` is empty. Process-doc edit under `BUILD.md`'s corpus ratchet.
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): widen the existing `BUILD.md` sentence to cover Worker-0's own findings (no corpus growth).

### T-108: `AGENTS.md` mandates repo-wide write-mode `ruff`; `worker-2.md` tells workers to scope it to their own files
- Source: `docs/builder/DONE/build-046-transport_security-0_0_15.md` (`## Open maintainer decisions`, the `AGENTS.md:15` vs. scoped `ruff` bullet, removed with this entry; also catalog item 24 of the retired `bld-final.md`, `git show 97dc05d7:docs/builder/bld-final.md`)
- Original text: "`AGENTS.md:15` mandates the repo-wide form and the role files defer to `AGENTS.md` on conflict, so **the scoping instruction is inert until this is reconciled.**"
- Current state: Open. `AGENTS.md` (the ``Run `uv run ruff check --fix .` then `uv run ruff format .` after every edit`` rule) and `START.md` "Session rules you will forget" both still mandate the repo-wide form; `docs/builder/worker-2.md` step 5 still says "on the files this pass touched - never on `.`" (the other role files no longer mention it).
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT**: reconcile the two. Recommend `AGENTS.md` / `START.md` adopt touched-path `ruff`, matching the explicit-path rule for `check_trailing_commas.py` under concurrent sessions; the maintainer picks the direction.

### T-109: The Uvicorn and Hypercorn thirds of spec-046 Decision 8's "no ASGI server bounds the total body" were never verified
- Source: `docs/builder/DONE/build-046-transport_security-0_0_15.md` (`### Six further spec divergences from an out-of-band adversarial claim audit`, closing "Two audit items stay open" paragraph; the Daphne half closed as true and stays)
- Original text: "the Uvicorn and Hypercorn thirds of Decision 8's 'no mainstream ASGI server bounds the total body' (absent from the venv; installing is barred, and the error direction is safe - if either *did* cap, the spec would be understating protection)."
- Current state: Still unverified. `.venv` carries only `daphne` 4.2.2 (no `uvicorn`, no `hypercorn`); the claim stands in `docs/SPECS/spec-046-transport_security-0_0_14.md` Decision 8 and in `docs/README.md` (the request-body-cap paragraph names all three servers).
- Also tracked: Nowhere else.
- Verdict: **IMPLEMENT** (done): reword spec-046 Decision 8 and `docs/README.md` to claim only what was verified (Daphne) and that the package relies on no server's cap.

### T-110: Stale search-card id `TODO-BETA-047-0.1.2` survives in archived specs
- Source: `docs/builder/DONE/build-047-resource_policy-0_0_14.md` (`## Worker-0 verification pass`, finding M, the "`spec-060`'s own slice table owns the comment-id fix ... do not touch it" clause removed with this entry; also catalog item 4 of the retired `bld-047-final.md`, `git show 94ddfe39:docs/builder/bld-047-final.md`)
- Original text: "`TODO-BETA-047-0.1.2` survives at 16 sites and is NOT this card's anchor ... the old numbering of a different, unshipped search card."
- Current state: Open for the spec sites. `rg TODO-BETA-047` (outside `KANBAN.*`) now finds `docs/SPECS/spec-020-list_field-0_0_7.md` twice (lines naming it as the search card), `docs/SPECS/spec-059-fieldset-0_1_1.md` once (calls it the pre-renumber id of card 060) and `docs/SPECS/spec-060-search_fields-0_1_2.md` three times (describing the stale comments); the live search card is `TODO-BETA-060-0.1.2`. `examples/fakeshop/apps/products/schema.py` carries none any more, so spec-060's Slice 4 clause "fix stale `TODO-BETA-047` comment IDs" is moot.
- Also tracked: `docs/SPECS/spec-060-search_fields-0_1_2.md` Slice 4 row (products-schema half only, now moot); the spec-020 sites nowhere.
- Verdict: **IMPLEMENT** (done): point the spec-020 sites at the live search card, delete the spec-059 history note and spec-060's moot Slice 4 clause.

### T-111: Strawberry's relay / pagination argument rejections still carry no audited `extensions.code`
- Source: `docs/builder/DONE/build-048-secure_output_defaults-0_0_17.md` (no pointer in the build file; catalog of the retired `bld-048-final.md`, `git show 567cc6d0:docs/builder/bld-048-final.md`, "Upstream argument rejections are masked", and its "A consequence worth stating plainly")
- Original text: "The fix is for the package to raise Strawberry's relay/pagination argument rejections as `GraphQLError` carrying an audited `extensions.code`, which brings them under the untouched branch of the structural rule without loosening it. Not licensed by this spec; belongs to a follow-up card."
- Current state: Half done. `django_strawberry_framework/utils/connections.py::PaginationArgumentError` (a `GraphQLError`) now carries offset-cursor and `first` / `last` rejections to the client; no `extensions.code` is audited for them. `KANBAN.md` line 691 records the code as "still open".
- Also tracked: Card `TODO-ALPHA-057-0.1.0` (Beta release), `KANBAN.md` line 691 ("needs a card or an explicit deferral reason in this card's parity audit").
- Verdict: **IMPLEMENT** (done): give `PaginationArgumentError` an audited `extensions.code` before the beta.

### T-114: `scripts/archive_spec.py` to replace NEXT.md Step 8's hand-run archive procedure
- Source: `docs/builder/DONE/build-044-debug_extension-0_0_14.md` (the retired `bld-044-final.md`, `git show 99696bac^:docs/builder/bld-044-final.md`, `### 11. scripts/archive_spec.py`; the build file carries no pointer to it)
- Original text: "`scripts/archive_spec.py` — a real future card, not an annoyance": `docs/SPECS/NEXT.md` Step 8's archive procedure is ~120 lines of hand-run steps.
- Current state: Open. `scripts/` has no `archive_spec.py`; the procedure is still manual.
- Also tracked: Card `TODO-ALPHA-056-0.0.17`, `KANBAN.md` line 625 (the open question whether the script should exist and warrants its own card).
- Verdict: **IMPLEMENT** (done): its own card; Step 8's hand sweeps caused several entries above.

## Audit side findings

Found while auditing, not moved out of any build file. Board line numbers are `KANBAN.md` as of the audit; board fixes are DB edits plus a re-render.

### Board lines that pointed at passages now removed from the build files

- 302 -> T-049; 304 -> T-033; 306 -> T-061; 308 -> T-062; 551 -> T-020; 552 -> T-021; 553 -> T-023, T-026; 568 -> T-064; 569 -> T-040.
- Card rows that carry the same work as a TODO entry without naming a build file: 310, 312, 313, 314, 315, 316, 588, 589, 591, 592, 593, 768, 1332, 1333, 1351, 1629 (see each entry's "Also tracked").

### Board text stale against the tree

- 267, 293 (`TODO-ALPHA-053`): `_resolve_field_map` dual-contract retirement and the `DUAL CONTRACT` paragraph deletion are already done; 278: `_optimizer_field_map` test-name sweep done.
- 271: `_package_view_instance` docstring is already scoped.
- 284-285: the `exceptions.py` and `_format_unknown_fields_error` docstring edits are made, not "never made".
- 291, 292, 294: cite retired `bld-015-final.md` / `bld-016-final.md`.
- 296: fail-soft test names are gone. 297 half (i): `DjangoListField` now wires `orderBy` (spec-050).
- 301: `workstream A/B/C/D` has 0 `.py` occurrences, not 35.
- 307: the `_COERCION_ERRORS` tuple is gone from `connection.py` and `auth/mutations.py`. 312: cites `test_library_api.py:3680`, now near 6856. 313: the operation-map clause is done.
- 317: `orders/sets.py` no longer carries `P1-B`.
- 525: specs 040-043 now have rationale companions. 527: BACKLOG lines are now 1746 / 1793.
- 529: cites a `## The discharged deferral` heading that no longer exists (T-009).
- 537: the docstring half of spec-005 R3 is done.
- 540: `check_trailing_commas.py` now prunes git-ignored paths.
- 547: `DjangoListField` `orderBy` shipped in spec-050.
- 548 (c): 0 `docs/spec-` tokens remain, not 13. 556: 55 `python3.14/site-packages` paths, not 54. 559: names old id `TODO-ALPHA-052`.
- 563: CHANGELOG `[0.0.14]` carries the keyset / `cursor_field` entry. 570: TREE.md lists all seven optimizer modules. 571: 12 anchorless `Decision N`, not 13.
- 595: `the P1 bug` / `the P2 bug` tokens are gone from `tests/test_relay_node_field.py`. 596: BUILD.md 540 / 547 now cover the venv and `/tmp` recipes.
- 625: the two standing-doc defects and the 14 orphan-row pairs are fixed. 1632: `tests/base/test_conf.py` has a verbatim `TESTING_ENDPOINT: None` row.
- The 056 unused-link-definition bullet: today 46 definitions across 7 files, none in `docs/SPECS/`.

### Judged not outstanding (recorded for the maintainer's call)

- build-007 D9: "the changelog's own state is a maintainer follow-up" for CHANGELOG 0.0.8; no concrete work found.
- build-008 D6: manual relation-annotation cardinality validation "deferred"; GLOSSARY states it as deliberate.
- build-014 F9: strictness-mode live coverage stays in spec-014's `## Remaining follow-ups`.
- build-016: `verified_upstream` convention, NEXT.md Step 3c loop, `review_inspect.py` docstring blindness.
- build-025: `python3.10` population count discrepancy.
- build-027: `TODO(spec-027-filters-0_0_8 Meta.search_fields)` anchor in `filters/sets.py` (live card `TODO-BETA-060-0.1.2`).
- build-028 F4: `docs/TREE.md` omits `__init__.py` from file counts.
- build-029 row 10 (`CORPUS_REGIONS` accepted residual); row 12 (`_validate_optimizer_hints` DRY candidate declined); process proposals (underscore slugger trap, zsh `PIPESTATUS`).
- build-031: rationale-companion census "board row pk 1278" (row does not exist).
- build-032: "pre-flight should run every gate command the final gate runs" (in no process doc).
- build-035 D6 / D7 / D8 (judged, deliberately left).
- build-036 DoD item 6: full-suite-green claim not re-verified (no test run).
- build-040 entry 12: rename `model` to `user_model` in `tests/auth/test_mutations.py`.
- build-046 retired-catalog item 12: `auth/mutations.py` repeated literals (on `TODO-ALPHA-053-0.0.15`, `KANBAN.md` 276).
- build-050 retired final C2 / C4 (`_SealPolicy` does not enforce "no policy sets both"), and the Decision 20 collection-hook fail-opens.
- Deliberately unticked boxes kept: build-042 `Cohort B`; build-043 superseded checklist (5), `Cohort B`, superseded `Final gate`.

### Filename versions

- `build-046-transport_security-0_0_15.md` and `build-048-secure_output_defaults-0_0_17.md` carry version suffixes that disagree with their cards (`DONE-046-0.0.14`, `DONE-048-0.0.14`) and archived specs (`0_0_14`).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
