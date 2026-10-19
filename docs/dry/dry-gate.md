# DRY review: `final test gate`

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

Gate worker (Worker-1, queue item `gate`, run 13) for DRY cycle 0.0.15.
Worktree `~/projects/worktrees/django-strawberry-framework/dry-0015`,
HEAD `23b5f42106ffd14805936560f5155dd90d7568da` at dispatch.
`ITEM_BASELINE=838074f7cb0481025aecdcf61982d4b5cbf9d25d` (from
`workspace.py baseline dry/gate`; pool shows slot-1 `dry/gate/before`
ready). Own copy `dry/gate/consolidate` on slot-2, synced via
`workspace.py run` through `heavy` (run `dry-20261010T104722-a4394f`,
copy fresh, shared unmoved since sync, package digest
`sha256:2d87dc608b6baf58101e5d19f608dd673a28e3243dcaabe0a33a653557dbc50b`).

Gate = CI's lint job + FULL default suite + CI's floor cell, run as
`uv run python scripts/workspace.py gate dry --suites lint,default,floor`
in the gate copy (own git index, detached HEAD at shared HEAD), plus
every `## Pending execution` command from every artifact, run as listed.
No maintainer authorization for sharded/pg runs exists: no `--cell` run was
made, and every cell-gated entry is listed unverified. No source edit
was made or is expected of this item.

Address translation (recorded once, applies to every translated run
below): pending entries addressed at item copies
(`dry/<item>/consolidate`, `dry/<item>/verify-1`) execute here as
`uv run python scripts/workspace.py run dry/gate/consolidate -- <inner>`
in slot-2, synced from the same shared bytes in default cell; bare
`uv run ...` / `heavy uv run ...` entries likewise run inside slot-2
(the entry command authorizes workspace runs, not shared-tree pytest).
The tree, cell, and inner command are identical to the listing; only the
slot binding differs, which carries no semantic content. Each run cites
its own run id.

## Verification

### Matrix

Not applicable: the gate item traces no rule and proposes no
consolidation. Verification here = the three bound suites plus the
pending-command dispositions below.

### Enumeration

211 exact `## Pending execution` sections across 231 artifact files
(`docs/dry/dry-*.md` minus the 5 plan files minus this draft itself:
207 files carry exactly one section, `dry-file-consumers.md` and
`dry-rule-relation-kind-taxonomy.md` carry two each (all four `None`),
22 carry no section — "Absent when none" per DRY.md. Correction by the
fresh worker: the first draft's breakdown (209 x 1, 2 x 0) never
reconciled (209+2+2=213, not 231); the reconciled census is
207+2+22=231 files, 207+4=211 sections, re-derived first-hand. The 22
zero-section files are all `Status: verified`: the 2 named in the
first draft (`dry-folder-utils.md`, `dry-project.md`, whose
`## Verification` witnesses already ran green in verification) plus
20 more (`dry-file-mutations__permissions.md`,
`dry-file-testing__client.md`, `dry-file-types__converters.md`, 11
`dry-file-utils__*` files, and 6 `dry-rule-*` files — enumerated under
`## Implementation`), each swept for `proof:`/`gate:`/`execution-deferred`
mentions: every hit is a "none owed / nothing deferred" statement or a
finding-field label, no runnable command. One near-miss header,
`dry-file-_boundary_ordering.md` "## Pending execution and defects
(expected: unaffected)", is a Worker-2 adjudication appendix entry
stating the real section is empty — read, not counted. Every section
was read first-hand by the fresh worker: the 107 sections containing
backticked commands in full, the 79 bare-keyword sections via an
owe-language scan plus full reads of the 7 mentioning re-runs, the 25
signal-free sections in full. Sections not named below say
`None`/`Nothing deferred`/`Empty`/`Absent` with at most
already-executed replay evidence and owe no command.

Typed entries (`proof:`/`gate:` strict or prose form) and their
dispositions:

### Runnable entries (run at gate; results under `## Implementation`)

Folder witnesses — `gate:` re-runs, translated to slot-2:

- G-auth-1..6 (`dry-folder-auth.md`): `basedpyright`;
  `basedpyright -p pyrightconfig.floor.json`;
  `python scripts/check_truthful_reads.py --check`;
  `pytest -n0 tests/auth/test_queries.py -q --no-cov`;
  `pytest -n0 tests/auth/test_mutations.py -q --no-cov`;
  `pytest -n0 tests/auth/test_sessions.py -q --no-cov`.
- G-ext-1..7 (`dry-folder-extensions.md`): the same 3 static gates;
  `pytest -n0 tests/extensions/test_debug.py -q --no-cov`;
  `pytest -n0 tests/extensions/test_operation_state.py -q --no-cov`;
  `pytest -n0 tests/test_error_policy.py -q --no-cov`;
  `pytest -n0 tests/test_resource_policy.py -q --no-cov`.
- G-fil-1..5 (`dry-folder-filters.md`): the same 3 static gates;
  `pytest tests/filters/test_sets.py -n0 -q --no-cov`;
  `prove dry/gate/consolidate
  ~/dry/tmp/folder-filters-failability.json` (failability
  by mutation, as listed — manifest present on disk).
- G-for-1..7 (`dry-folder-forms.md`): the same 3 static gates;
  `pytest -n0 tests/forms/test_converter.py -q --no-cov`;
  `pytest -n0 tests/forms/test_inputs.py -q --no-cov`;
  `pytest -n0 tests/forms/test_resolvers.py -q --no-cov`;
  `pytest -n0 tests/forms/test_sets.py -q --no-cov`.
- G-mgmt-1..2 (`dry-folder-management.md`):
  `pytest -n0 tests/management/test_imports.py -q --no-cov`;
  `python scripts/build_tree_md.py --check`.
- G-mcmd-1..7 (`dry-folder-management__commands.md`): the same 3
  static gates; `pytest -n0 tests/management/test_imports.py -q
  --no-cov`; `pytest -n0 tests/management/test_export_schema.py -q
  --no-cov`; `pytest -n0
  tests/management/test_inspect_django_type.py -q --no-cov`;
  `pytest -n0
  examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_connection_only_relation_shape_renders_row
  -q --no-cov`.
- G-mw-1..4 (`dry-folder-middleware.md`):
  `pytest -n0 tests/middleware/test_debug_toolbar.py --no-cov -q`;
  `pytest -n0 tests/test_views.py --no-cov -q`;
  `pytest -n0 examples/fakeshop/test_query/test_debug_toolbar_api.py
  --no-cov -q`; `python scripts/build_tree_md.py --check`.
- G-mut-1..5 (`dry-folder-mutations.md`):
  `pytest -n0 tests/mutations/test_inputs.py --no-cov -q`;
  `pytest -n0 tests/mutations/test_sets.py --no-cov -q` (also
  discharges the mutations__sets settle file selection below — one
  execution, cited twice);
  `pytest -n0 tests/mutations/test_fields.py --no-cov -q`;
  `pytest -n0 tests/mutations/test_resolvers.py
  tests/mutations/test_permissions.py --no-cov -q`;
  `pytest -n0 examples/fakeshop/test_query/test_products_api.py
  --no-cov -q`.
- G-opt-1 (`dry-folder-optimizer.md`):
  `python -m pytest tests/optimizer -q --no-cov -p no:cacheprovider`
  (931-row witness).
- G-ord-1 (`dry-folder-orders.md`):
  `python -m pytest tests/orders -q --no-cov -p no:cacheprovider`
  (240-row witness).
- G-rf-1 (`dry-folder-rest_framework.md`):
  `python -m pytest tests/rest_framework -q --no-cov -p
  no:cacheprovider` (564-row witness).
- G-tst-1 (`dry-folder-testing.md`):
  `python -m pytest tests/testing tests/test_multipart.py -q --no-cov
  -p no:cacheprovider` (70-row witness).
- G-typ-1..3 (`dry-folder-types.md`):
  `python -m pytest tests/types -q --no-cov -p no:cacheprovider`
  (571-row witness);
  `python -m pytest tests/management/test_inspect_django_type.py -q
  --no-cov -p no:cacheprovider -n0` (24-row witness);
  P1 leaf probe `python ~/dry/tmp/folder_types_p1.py
  <slot-2 root>` (script present on disk; verify-copy-root argv
  becomes the slot-2 root under the translation).

File items:

- G-qs-2 (`dry-file-utils__querysets.md` entry 2, `gate:`):
  `pytest tests/utils/test_querysets.py tests/test_list_field.py
  tests/optimizer/test_extension.py --no-cov`.
- G-ms-1 (prose, `dry-file-mutations__sets.md` settle-gated re-run):
  `python
  docs/dry/temp-tests/dry-file-mutations__sets/probe_safe_name_coverage.py`
  (expect pass; script present) plus the
  `tests/mutations/test_sets.py` hostile-name file selection —
  discharged by the G-mut-2 execution (same file, same tree).
- G-gid-1 (`dry-rule-globalid-decode-input-hardening.md`, `gate:`):
  `pytest
  tests/filters/test_base.py::test_decode_global_id_hostile_repr_still_raises_the_coded_error
  --no-cov -n0`.

Rule items:

- P-f46 (`dry-rule-canonical-container-membership.md`, `proof:`):
  38-node selection (10 canonical + 12 inputs + 16
  fingerprint/snapshot) — migration-handoff equivalence re-confirmation.
- P-f64 (`dry-rule-canonical-unordered-partition.md`, `proof:`):
  9-node selection (3 sort-key + 4 inputs + 2 fingerprint).
- P-f38 (`dry-rule-mutation-discovery-own-snapshot-read.md`, `proof:`
  entry 1 of 2): 3-node selection (1 rest_framework + 2 forms) —
  "the final gate runs it as listed".
- P-f28 (`dry-rule-relation-connection-to-attr-grammar.md`, `proof:`):
  `prove dry/gate/consolidate /tmp/relattr-f28-manifest.json` —
  genuine deferred failability proof (pool-bound at proof time);
  manifest recreated byte-identically from the artifact; anchor and
  all 3 nodes verified present at gate bytes before running
  (`connection.py:2300`, `test_relay_connection.py:1023, 1993,
  2856`). Failability by mutation, as specified.

Named-by-gate entries (no separate run; discharged by the bound
default suite, suite names recorded under `## Implementation`):

- N-opt (`dry-folder-optimizer.md`): live `/graphql` suites covering
  optimizer wire behavior.
- N-ord (`dry-folder-orders.md`): live `/graphql` suites carrying
  `orderBy:` rows.
- N-rf (`dry-folder-rest_framework.md`): live `/graphql` suites
  carrying serializer-mutation rows.
- N-tst (`dry-folder-testing.md`): live `/graphql` suites carrying
  testing-client rows.
- N-typ (`dry-folder-types.md`): live `/graphql` suites carrying
  type-system rows.

### Not run (recorded with reason; each stays carried, none reopens)

Cell-gated (no maintainer authorization for sharded/pg exists; no `--cell`
run made — all read `unverified`):

- U-qs-1 (`dry-file-utils__querysets.md` entry 1, `proof:`):
  `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query -k
  prefetch --no-cov` — D1 cross-connection consequence unverified.
- U-perm-1 (prose, `dry-file-permissions.md`):
  `FAKESHOP_SHARDED=1 uv run pytest tests/test_permissions.py -k
  "multi_db or alias or pinned" --no-cov` — F2 cross-connection
  consequence unverified; PG cells unverified.
- U-ca-1 (prose, `dry-rule-child-queryset-alias-inheritance.md`):
  `FAKESHOP_SHARDED=1` trio in `test_multi_db.py` + any PG cell —
  unverified (executed default-cell evidence stands as recorded).

Blocked proofs (each record says "runnable only after the unblocked
consolidation lands" / "re-discharges ... when the unblock item lands";
every block persists per the plan's `## Families` — no landing is
recorded, no `<manifest>` authored; a green pre-migration run would
discharge nothing, so none was run):

- B-f60 (`dry-rule-bound-filter-model-field-walk.md`):
  `pytest tests/filters/test_base.py -n0 --no-cov -q`.
- B-f36 (`dry-rule-canonical-input-provisional-name.md`):
  `pytest tests/rest_framework/test_resolvers.py
  tests/rest_framework/test_inputs.py tests/utils/test_inputs.py -n0
  --no-cov -q`.
- B-f37 (`dry-rule-generated-choice-enum-name-template.md`):
  `pytest tests/types/test_converters.py
  tests/rest_framework/test_converter.py
  "examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_metadata_serializer_expanded_input_type_system_over_http"
  -n0 --no-cov -q`.
- B-f41 (`dry-rule-graphql-name-gate.md`): 7-node selection.
- B-f42 (`dry-rule-mro-map-key-lookup.md`): 9-node selection.
- B-f40 (`dry-rule-registered-djangotype-definition-validation.md`):
  `tests/testing/test_relay.py` + 10 `test_list_field.py` nodes.
- B-e9 (`dry-rule-prepared-view-handoff-shape.md`): 2-node selection
  (`test_views.py` + `test_transport_api.py`).
- B-e8 (`dry-rule-queryset-seed-and-model-read.md`):
  `pytest tests/utils/test_querysets.py
  tests/types/test_relay_interfaces.py tests/mutations/test_resolvers.py
  -n0 --no-cov -q` (sharded/PG reach real — inapplicability correctly
  NOT claimed).
- B-f63 (`dry-rule-write-pipeline-alias-recovery.md`): 1-node pin
  (`test_custom_node_id_real_pk_lookup_uses_pinned_alias`).
- B-f38-2 (`dry-rule-mutation-discovery-own-snapshot-read.md`, `proof:`
  entry 2 of 2): landing-owed `prove ... <manifest>` — the record
  forbids running it before the landing pass authors the manifest.

Already-executed evidence (original run ids stand; re-running the
recorded command is impossible because the scratch lived on another
machine's `/tmp` or was removed post-verification — no failability
obligation is outstanding on any of them):

- E-e2/e3/e4/e5/e6/e7 (`dry-rule-recomposition-illegal-source-rejection.md`,
  `dry-rule-related-object-visibility-recheck.md`,
  `dry-rule-field-value-coercion.md`,
  `dry-rule-sync-boundary-recourse-wording.md`,
  `dry-rule-async-only-queryset-row-adapter.md`,
  `dry-rule-post-set-apply-result-validation.md`): `execution-verified`
  probes (`dry-20260930T232512-466a50`, `dry-20261001T000756-31604e`,
  `dry-20261001T003743-c980ee`, `dry-20261001T011302-edd678`,
  `dry-20261001T014044-2a5afd`, `dry-20261001T021510-89921c`);
  probe scripts were under `/tmp`/`/private/var/folders` on the
  originating machine and are absent here.
- E-seal (`dry-rule-sealed-execution-queryset.md`): executed probe in
  a removed disposable workspace (`dry-ws/sealed-execution-queryset`).
- G-qs-3 (`dry-file-utils__querysets.md` entry 3, `gate:`):
  `probe_defect_arms.py` no longer exists under
  `docs/dry/temp-tests/dry-file-utils__querysets-w2/` (post-verification
  scratch removal; successor `probe_defect_arms_r2.py` scope likewise
  absent) — unrunnable as listed; original revision-1 measurement
  (`sites with a mismatch: 4/6` with the I-R4 modelling-artifact
  qualification) stands as the record.

## Findings

None: the gate item traces no rule and lands no consolidation.

## Defects

D1 — `tests/filters/test_inputs.py::test_normalize_input_declared_range_filter_rejects_list_end_to_end`
fails in both bound suites (default + floor): expects `ConfigurationError`
matching "range input", production raises "has no 'range' lookup (lookups:
['exact']); it would apply nothing". Cause: the test is new concurrent dirt
(absent at HEAD; no ledger row) whose expectation matches neither HEAD nor
gate production — a declared package `RangeFilter` carries
`lookup_expr='exact'` (django-filter default; `RangeFilter`/`TypedFilter`
HEAD-identical), the grouping rule assigns the declared filter to the
`exact` bag slot (line HEAD-identical), the dict `{"range": [...]}` is
detected as an operator bag (rule HEAD-identical), and the per-lookup-miss
raise fires (branch present at HEAD). FAM-1 (Folder `filters/`, the only
cycle hunk on this path) moved two HEAD-identical lines verbatim into
`FilterSet._leaf_lookups_by_attr`; for a modeled set it returns the
identical `filter_lookup_table(cls).by_input_attr` expression, so it cannot
have changed the table. No cycle item caused this; the item-back clause
does not apply (nothing for Folder `filters/` to fix). Routes to the maintainer as
concurrent-work failure (hunt test vs HEAD-identical production); owning
card for Worker-0 to home (hunt side). Gate row blocked on it.

D2 — concurrent deletion of
`tests/filters/test_base.py::test_decode_global_id_hostile_repr_still_raises_the_coded_error`
(replaced by `test_related_filter_gate_rejection_message_is_pinned`; no
ledger row) removed the only non-string caller of
`filters/base.py::_decode_and_validate_global_id`, leaving line 941
(`raise ValueError("a GlobalID filter value is a base64 string")`,
HEAD-identical at HEAD:979) uncovered: the single miss behind the 99.99%
coverage. Independent of D1 (proven: D1's test executes its full
production path — the raise happens, only the message regex fails — so
its coverage contribution equals the passing case; and line 941 sits in
GlobalID decode, unreachable from the range-test path whose set holds no
GlobalID filter). The same deletion makes pending gate entry G-gid-1
error as listed (exit 4, "no tests ran"). Routes to the maintainer as
concurrent-work failure; owning card for Worker-0 to home. Gate row
blocked on it.

D3 — pending settle re-run P3 (`probe_safe_name_coverage.py`, G-ms-1)
fails at current bytes: one hit `(742, 'built')` where the item recorded
zero. The hit is a probe-vs-new-code false positive, not a hostile-name
hole: line 742 is a STORE (`built.__name__ = name`, assigning a plain
`str`), which the probe's matcher does not distinguish from a READ, on
`built = MetaValidatingMetaclass`, the framework's own freshly built
metaclass (its own comment says so; the `# truth: ok` annotations mark
the author's intent) — a new framework-built base the probe's
`BENIGN_BASES` does not know. Per the item's W2 settle ruling the
fingerprint change (sets.py `936f5ae7` at verification vs `6f2fa2f9`
now; HEAD moved too) reopens rows F2/FL11/FL16 for Worker-0's
re-verification; the hostile-name oracle file itself is green
(tests/mutations/test_sets.py, 100 passed, run
dry-20261010T130521-7876de). Routes to the maintainer (probe update vs row
re-verification is Worker-0's closeout call); reopens no item (the
entry is witness-class per the ruling, explicitly "NOT a deferred
proof").

## Pending execution

None for this item: the gate runs other artifacts' entries, and every
one is dispositioned under `## Implementation` — 45 fresh executions
(43 distinct commands as listed, all green except G-ms-1/P3 exit 1
per D3, G-gid-1 exit 4 per D2, and P-f46 exit 4 on 9
concurrently-removed nodes; plus 1 labeled diagnostic subset proving
P-f46's 29 surviving nodes green, plus 1 superseded slot-2 tree-check
attempt that proved the bare static entry needs shared-tree git
semantics), 5 named-by-gate live-suite sets confirmed green in the
bound suite, 3 cell-gated entries unverified (no maintainer authorization),
10 blocked proofs unlanded per the plan, 8 already-executed evidence
records standing. No sharded/pg run was made. The gate item itself
lands no edit and owes no further command.

## Judgment

Gate verdict: RED and BLOCKED, routed, nothing item-back. Lint GREEN
(exit 0, adopted + re-verified). Both suites RED on the same single
concurrent-work failure D1 (production HEAD-identical; test
expectation never held) with coverage 99.99% on the independent
concurrent-work miss D2. Every pending command ran fresh as listed
(or is recorded with its reason): witnesses green, both failability
proves pinned, P-f64/P-f38 green, P-f46's substance green on the 29
live nodes with the 9 removed-API nodes carried, P3 red per D3,
G-gid-1 erroring per D2. No failure sits in a path any cycle item
changed; D1/D2/D3 all route to the maintainer through Worker-0 (owning cards to
be homed), and the gate row is blocked on D1 + D2. Cells sharded/pg:
unverified throughout (no authorization); inapplicability claims are
each artifact's own, judged at verification, not re-judged here.

## Implementation (Worker-1)

Fresh worker (prior gate worker wedged post-suites and was cancelled;
same item/slot/baseline/pass, nothing submitted before). No source
edit made. All `workspace.py` runs below went through `heavy`,
sequentially, on a GREEN machine with 2 GiB+ free throughout.

### Suite evidence: verify-adopted, not re-run

The prior worker's `workspace.py gate dry --suites lint,default,floor`
completed (exit 1) with result file
`dry/evidence/gate-dry-20261010T115331-40b63a.json`. Adoption premises,
each verified first-hand against current bytes (no premise trusted from
the handoff note):

- Package digest `sha256:2d87dc60...` (full:
  `2d87dc608b6baf58101e5d19f608dd673a28e3243dcaabe0a33a653557dbc50b`)
  is identical across the gate-time manifest, the shared tree, the
  gate copy, slot-1, and slot-2 (recomputed with the same
  `workspace.py` digest function; slot-2 re-checked after all prove
  runs — restores byte-identical).
- HEAD `23b5f42106ffd14805936560f5155dd90d7568da` unmoved;
  `pyproject.toml` blob `21cccc6d...`, `uv.lock` blob `8fb5f01c...`
  match the result file.
- Tracked diff vs the gate-time stash `bbda7f26...` is exactly
  `docs/dry/dry-0_0_15.md` (plan prose, +3/-1 over the gate run;
  one more prose line landed mid-gate from Worker-0's own status
  note) — prose, which DRY.md excludes from invalidation.
- Byte diff shared-vs-gate-copy: `django_strawberry_framework/`,
  `tests/`, `examples/` (excluding `*.sqlite3*`/caches), `scripts/`,
  `pytest.ini`, `pyproject.toml`, `uv.lock` all identical. The gate
  copy lacks `docs/dry/temp-tests/` by design (`EXCLUDED_SEGMENTS`
  in `scripts/workspace.py`); temp-tests are scratch outside every
  suite's `testpaths`.
- Mode/deps/cells unchanged: default cell, same floor venv
  (pins Django 5.2.16 / python 3.10 / strawberry-graphql 0.322.2,
  key `c4fed73b...`, `reused: false`).

No bound input changed: re-running 62 minutes of suites would
reproduce the same bytes' results. Adopted.

### Suite results (re-read first-hand, counts confirmed by grep)

Lint (`dry-20261010T104724-d9f29f`, exit 0, 233s): GREEN. All 13
commands pass — ruff check, ruff format --check (506 files),
basedpyright 0/0/0 both configs, public-types 100% (2 allowlisted),
trailing-commas 0, truthful-reads tier-1 0, citations resolve (3321),
all four generators --check up to date. Exit confirmed in
`runs.jsonl` (`exit: 0`) and the `sh -exc` log reaching its last line.

Default (`dry-20261010T105117-6a321e`, exit 1, 1410s, Python 3.14.8,
Django 6.1.2): 1 failed, 10440 passed, 43 skipped; collected 10482.
Count reconciliation (verified, not assumed): 10440 `PASSED` lines +
41 `SKIPPED` lines + 1 `FAILED` line = 10482 collected; the summary's
43 skips add exactly the 2 module-level collection skips
(`test_multi_db.py`, `test_generic_connection_sharded.py`, both gated
on `FAKESHOP_SHARDED=1`, each +1 with no per-test line). Zero
`ERROR`, `XPASS`/`XFAIL`, `INTERNALERROR`. The single FAILED is D1.
Coverage: TOTAL 19994 stmts, 1 miss —
`django_strawberry_framework/filters/base.py` 397/1/99% line 941 (D2);
every other file 100%. `fail_under=100` not reached (99.99%).

Floor (`dry-20261010T111447-becca6`, exit 1, 2323s, Python 3.10.22,
Django 5.2.16): 1 failed, 10437 passed, 46 skipped; collected 10482
(10437 + 44 line-skips + 1 failed = 10482, +2 module-skips = 46).
Same single FAILED (D1, byte-identical failure body modulo the
interpreter path). No coverage gate on this cell (floor command
overrides addopts without cov).

### Pending-command dispositions (all run fresh in slot-2 unless noted)

Address translation (extends the draft's note): `dry/<item>/...`
addresses run as `workspace.py run dry/gate/consolidate -- <inner>`;
bare `pytest` entries run in slot-2 the same way. Two corrections to
the draft's blanket translation, both proven by execution: (a) the
bare static entry `python scripts/build_tree_md.py --check` MUST run
in the shared tree — slot-2 has no `.git`, so the tool falls back to
a filesystem walk that flags the 10 untracked files it by design
ignores (attempt run dry-20261010T125723-260efe, exit 1, superseded;
shared-tree run exit 0, "up to date", agreeing with the adopted lint
GREEN); the folder items' own green re-runs must likewise have been
shared-tree. (b) The P3 probe script (temp-tests are
sync-excluded) was staged into slot-2 byte-identically (sha256
`eb368ebe...`, both trees) so the listed relative command runs
verbatim; the staging is the run log's single `copy_edits` entry on
every run. Textually identical static entries across artifacts share
one fresh execution each (same tree, same bytes — re-running the
identical command adds no information); every entry below cites its
run id. Own sync run: dry-20261010T125343-d5f17c (slot-2 reused,
fresh, digest match; shared moves: the 2 prose files only).

Static (each discharging every artifact entry naming it):
basedpyright 0/0/0 (dry-20261010T125420-986707, 85s);
basedpyright -p pyrightconfig.floor.json 0/0/0
(dry-20261010T125551-80638e, 84s); check_truthful_reads tier-1 0
(dry-20261010T125721-0e1c9d); build_tree_md shared-tree exit 0.
All GREEN.

Pytest witnesses, all exit 0: auth 18 + 91 + 31 (dry-20261010T125849-1b89c7, dry-20261010T125903-6513c9,
dry-20261010T125919-9a7350); extensions 75 + 56 + 66 + 284 (dry-20261010T125927-0aab3d, dry-20261010T125936-466127, dry-20261010T125943-dd1e37,
dry-20261010T125946-ddae84); filters/test_sets.py 630 (dry-20261010T130012-85ab4a); forms 35 + 66 + 36 + 107
(dry-20261010T130111-bb92cc, dry-20261010T130114-15a294, dry-20261010T130120-05cf99, dry-20261010T130130-f92280); management 19 + 5 + 24 + 2 (dry-20261010T130138-e97946,
dry-20261010T130141-04ac38, dry-20261010T130149-fa4e79, dry-20261010T130152-896826 — the single-node live selection yields 2 via
parametrization; the imports run is shared by G-mgmt-1/G-mcmd-4);
middleware 71 + 202 + 15 (dry-20261010T130207-f9f41d, dry-20261010T130214-089fa1, dry-20261010T130233-fc8c2b); mutations 83 +
100 + 15 + 68 + 198 (dry-20261010T130518-268d05, dry-20261010T130521-7876de, dry-20261010T130529-259c6a, dry-20261010T130539-642c3c, dry-20261010T130556-ee385f —
the 100-row test_sets.py run also discharges G-ms-1's hostile-name
file half); optimizer 933 (dry-20261010T130931-929379 — artifact said 931, +2 concurrent
rows, green); orders 240 (dry-20261010T131031-76d789); rest_framework 564 (dry-20261010T131059-da71bd);
testing+multipart 70 (dry-20261010T131129-998ac9); types 571 (dry-20261010T131155-c11d8f); inspect variant 24
(dry-20261010T131232-4e6cde); querysets trio 636 (dry-20261010T131320-378cf6, G-qs-2). All ids
are full `dry-...` run ids; logs live under `dry/evidence/logs/`.

Probes/proves: G-fil prove exit 0, 3/3 entries pinned (dry-20261010T130039-a7ca9c, JSON
at `dry/evidence/proofs/gate/consolidate/`); P-f28 prove exit 0 —
entry 1 pinned (census fails exactly expect_failing), entry 2
behaviour preserved (dry-20261010T131524-9f4c9a; manifest recreated byte-identically from
the artifact JSON at /tmp/relattr-f28-manifest.json, `cmp` clean;
anchor verified at connection.py:2300 and all 3 nodes present before
running); P1 leaf probe P1-PASS with package `__file__` inside
slot-2 (dry-20261010T131240-50d49c); P3 probe exit 1 per D3 (dry-20261010T131247-c4cbc5); G-gid-1 exit 4
("no tests ran", dry-20261010T131410-c5f4de) per D2; P-f46 as listed exit 4 (dry-20261010T131425-8e4344 —
"collected 29 items / no tests ran", the 9 `ERROR: not found` lines
naming exactly the removed-API nodes) with the labeled diagnostic
subset 29/29 green (dry-20261010T131443-90bfe1); P-f64 9/9 (dry-20261010T131508-491753); P-f38 3/3 (dry-20261010T131516-bc4e6a).

P-f46 routing note: the `proof:` command fails as listed, but the
strict item-back clause does not apply — f46 landed zero edits
(blocked, specified-not-landed), the finding holds 29/29 on every
live oracle, and the 9 nodes test `make_hashable_meta_value`, an API
concurrent work removed wholesale (0 references left in package or
tests). There is nothing for f46's Worker-1 to fix; re-pointing or
retiring the 9 nodes is Worker-0's closeout call with the maintainer. The item
stays "verified, pending execution" with this gap carried.

Named-by-gate live sets (confirmed green in the bound default log,
0 FAILED under test_query/): N-opt — optimizer wire (7 files:
test_optimizer_auto_api 5, test_connection_pagination_api 112,
test_keyset_api 39, test_single_parent_fastpath_api 11,
test_products_visibility_api 22,
test_joined_relation_visibility_api 11, test_combined_visibility_api
198 passed); N-ord — 15 orderBy: files live-green (test_multi_db.py
module-skips; counts: library 454, resource_policy 204, list_field
141, connection_pagination 112, list_field_async 79, products 198,
kanban 40, products_visibility 22, shapes 17, inheritance 13,
scalars_filter 10, schema_composition 9, glossary 5,
combined_visibility 198); N-rf — serializer-mutation rows
(test_library_api.py, test_products_api.py per the artifact text,
454 + 198); N-tst — testing-client rows (test_client_api.py 13,
test_uploads_api.py 23; multi-db rows unverified — see below);
N-typ — type-system rows (relay row files, the 3 visibility files,
test_uploads_api.py 23, choices rows in test_library_api.py;
multi-db rows unverified). test_multi_db.py collected 0 in default
mode (module skip): every multi-db row stays unverified.

Not run, with reason (all verified against current bytes): U-qs-1,
U-perm-1, U-ca-1 — cell-gated, no maintainer authorization, no `--cell`
run made; B-f60, B-f36, B-f37, B-f41, B-f42, B-f40, B-e9, B-e8,
B-f63, B-f38-2 — every block persists per the plan's Families rows
(all "open/blocked-on-hunt, zero edits, migration specified but
unlanded", re-checked at gate bytes; a green pre-migration run would
discharge nothing); E-e2/e3/e4/e5/e6/e7, E-seal — already-executed
records standing (run ids match the artifacts; probe scripts on
another machine's /tmp or a removed disposable workspace);
G-qs-3 — unrunnable as listed (`probe_defect_arms.py` and the r2
successor both absent from `dry-file-utils__querysets-w2/`, which
holds only w2_arms_alias/w2_bake_carry/w2_enum.py; the similarly
named `probe_defect_arms_9031.py` in the sibling scope is a
different file, not the listed command).

### Gate binding (this submission)

- `ITEM_BASELINE=838074f7cb0481025aecdcf61982d4b5cbf9d25d`
  (gate dispatch; slot-1 `dry/gate/before`).
- Gate-time stash (adopted suites): `bbda7f26449d79dac46f1ecf29cf127c17747a95`.
- Completion stash (this artifact): `75c49201ae0a771db2d81daac96df9ec0ab523c2`
  (`git stash create` after the last run; HEAD `23b5f421` unmoved;
  `git status` 542 lines: 201 modified + 341 untracked; the only
  tracked delta vs gate time is plan prose).
- Blobs: `pyproject.toml` `21cccc6d0caceb0cc91ff9ccafaa470a936c3ade`,
  `uv.lock` `8fb5f01c99f332731ad121be4b01b9b4c3a4443e` (match the
  adopted result file).
- Tree/package digests: gate `tree_digest`
  `sha256:44b4e557...e2d5e`, package `sha256:2d87dc60...c50b`
  (recomputed equal in all four trees).
- Cells: default throughout; sharded/pg never run (no
  authorization). Floor pins: Django 5.2.16, python 3.10,
  strawberry-graphql 0.322.2 (key `c4fed73b...`).
- Run-id ledger: adopted lint/default/floor
  (dry-20261010T104724-d9f29f/dry-20261010T105117-6a321e/dry-20261010T111447-becca6) + result file `gate-dry-20261010T115331-40b63a.json`;
  own sync dry-20261010T125343-d5f17c; pending runs dry-20261010T125420-986707, dry-20261010T125551-80638e, dry-20261010T125721-0e1c9d, dry-20261010T125723-260efe
  (superseded), dry-20261010T125849-1b89c7, dry-20261010T125903-6513c9, dry-20261010T125919-9a7350, dry-20261010T125927-0aab3d, dry-20261010T125936-466127, dry-20261010T125943-dd1e37,
  dry-20261010T125946-ddae84, dry-20261010T130012-85ab4a, dry-20261010T130039-a7ca9c, dry-20261010T130111-bb92cc, dry-20261010T130114-15a294, dry-20261010T130120-05cf99, dry-20261010T130130-f92280, dry-20261010T130138-e97946,
  dry-20261010T130141-04ac38, dry-20261010T130149-fa4e79, dry-20261010T130152-896826, dry-20261010T130207-f9f41d, dry-20261010T130214-089fa1, dry-20261010T130233-fc8c2b, dry-20261010T130518-268d05, dry-20261010T130521-7876de,
  dry-20261010T130529-259c6a, dry-20261010T130539-642c3c, dry-20261010T130556-ee385f, dry-20261010T130931-929379, dry-20261010T131031-76d789, dry-20261010T131059-da71bd, dry-20261010T131129-998ac9, dry-20261010T131155-c11d8f,
  dry-20261010T131232-4e6cde, dry-20261010T131240-50d49c, dry-20261010T131247-c4cbc5, dry-20261010T131320-378cf6, dry-20261010T131410-c5f4de, dry-20261010T131425-8e4344, dry-20261010T131443-90bfe1, dry-20261010T131508-491753,
  dry-20261010T131516-bc4e6a, dry-20261010T131524-9f4c9a (all `dry-20261010T` prefix; logs under
  `dry/evidence/logs/`, prove JSONs under
  `dry/evidence/proofs/gate/consolidate/`).

### Zero-section files (the 20 beyond the draft's 2)

`dry-file-mutations__permissions.md`, `dry-file-testing__client.md`,
`dry-file-types__converters.md`, `dry-file-utils__connections.md`,
`dry-file-utils__converters.md`, `dry-file-utils__directives.md`,
`dry-file-utils__errors.md`, `dry-file-utils__imports.md`,
`dry-file-utils__operation_lease.md`, `dry-file-utils__private_state.md`,
`dry-file-utils__sessions.md`, `dry-file-utils__strings.md`,
`dry-file-utils__typing.md`, `dry-rule-awaitable-refusal-and-disposal.md`,
`dry-rule-multipart-control-field-names.md`,
`dry-rule-relation-absence-containment.md`,
`dry-rule-seal-defect-code-wording.md`,
`dry-rule-soft-dependency-require-guard.md`,
`dry-rule-upstream-patch-lifecycle.md`,
`dry-rule-upstream-patch-refusal-wording.md` — all `Status: verified`,
all swept clean (see Enumeration).

### Closeout notes for Worker-0/Worker-2

- Worker-2 completes the gate row by confirming the bound inputs
  still match the tree and each pending command ran. `workspace.py
  audit` over this file: 56 cited, 49 bind ok; the 7 non-binding
  cites are correct — the 6 quoted-foreign E-* run ids (evidence
  recorded on another machine, never in this pool) plus the gate
  result-file id (a file, not a run-log entry).
- D1/D2/D3 need NAMED owning cards (all concurrent-work; none
  item-back). f46's 9-node gap rides with D2-class drift (concurrent
  API removal) at closeout.
- Staged scratch inside slot-2 (outside bound inputs, recorded in
  run logs): the P3 probe copy. Outside the repo: /tmp scripts and
  manifests under `/tmp` and `~/dry/tmp` (f28 manifest
  byte-identical to the artifact). No repo scratch created.
- Concurrent work untouched: zero repo edits outside this artifact;
  the one mid-gate tracked change (Worker-0's own plan status line)
  is prose.

## Independent verification (Worker-2)

Pass 1, slot-3 `dry/gate/verify-1` under
`ITEM_BASELINE=838074f7cb0481025aecdcf61982d4b5cbf9d25d`. Own sync run
`dry-20261010T133621-0bc944` (slot-3 fresh, digest match, shared
unmoved). Verify-only: no `.py` edits anywhere; no probe tests
written. Every numbered claim below was re-derived first-hand at
current bytes; nothing is trusted from the submission.

Verdict: **verified**. The gate ITEM is verified; the gate RESULT is
red/blocked per the routing (D1 + D2 blocking, D3 riding). A verified
RED gate is a completed gate item. The gate row completes as
BLOCKED-per-routing (completion text at the end of this section).

### Bound inputs still match (re-derived)

- HEAD `23b5f42106ffd14805936560f5155dd90d7568da` unmoved.
- `pyproject.toml` blob `21cccc6d0caceb0cc91ff9ccafaa470a936c3ade`,
  `uv.lock` blob `8fb5f01c99f332731ad121be4b01b9b4c3a4443e`: match the
  result file.
- Package digest `sha256:2d87dc60...c50b` recomputed with the
  workspace digest function: identical in shared, gate copy, slot-1,
  slot-2 (slot-2 re-checked after W1's prove runs; restores held).
- Byte diff shared-vs-gate-copy: `django_strawberry_framework/`
  (ignoring `__pycache__`), `tests/`, `examples/` (ignoring caches
  and sqlite artifacts), `scripts/`, `pytest.ini`,
  `pyproject.toml`, `uv.lock`: all identical.
- Tracked diff vs the gate-time stash `bbda7f26...` is exactly
  `docs/dry/dry-0_0_15.md`, plan prose only, now +5/-1 (W1's +3/-1
  plus Worker-0's post-completion submission note): prose, which
  DRY.md excludes from invalidation. Current `git stash create`
  differs from W1's completion stash for that prose reason alone.
- Floor pins re-read from the live floor venv: key `c4fed73b...`,
  python 3.10.22, Django 5.2.16, strawberry-graphql 0.322.2.
- Item-scoped diff vs `ITEM_BASELINE` over package/tests/examples/
  scripts/config: empty (gate landed no edits).

Binding holds: the 62 minutes of suites were adopted, not re-run.

### Suites (all 3 logs re-read first-hand)

- Lint `dry-20261010T104724-d9f29f`: exit 0, all 13 commands green
  (ruff check, format --check 506 files, both basedpyright 0/0/0,
  public-types 100% + 2 allowlisted, trailing-commas 0,
  truthful-reads tier-1 0, citations 3321, 5 generators up to
  date). Exit confirmed in `runs.jsonl`.
- Default `dry-20261010T105117-6a321e`: exit 1, Python 3.14.8 /
  Django 6.1.2. Grep counts: 10440 `PASSED` + 41 `SKIPPED` + 1
  `FAILED` = 10482 collected; summary's 43 skips = 41 lines + 2
  module-level collection skips (proven fresh: collect-only of the
  two sharded-gated files in slot-3 reports `collected 0 items / 2
  skipped`, run `dry-20261010T133735-62f0c0`). Zero `ERROR` /
  `XPASS` / `XFAIL` / `INTERNALERROR`. Coverage TOTAL 19994 stmts,
  1 miss: `filters/base.py` 397/1/99% line 941; 99.99% <
  `fail_under=100`.
- Floor `dry-20261010T111447-becca6`: exit 1. 10437 + 44 + 1 =
  10482; summary 46 = 44 + the same 2 module skips. Same single
  FAILED; failure body identical to default modulo the interpreter
  path and one pytest caret-render line. Floor skips = default's 41
  plus exactly 3 version-gated rows (2 postgres-converter, 1 MTI
  prefetch). Zero xfail/error.
- The single FAILED in both suites is D1 (message reproduced in the
  D1 section below).

### D1 re-derived (adversarial pass)

- The test is absent at HEAD (`git show HEAD:` count 0) and its file
  carries no ledger row: new concurrent dirt. Confirmed.
- Expectation never held at HEAD bytes NOR gate bytes. Full decision
  chain on the raise path, each checked HEAD-vs-gate:
  - `RangeFilter` / `TypedFilter` set no `lookup_expr` at either
    bytes; django-filter's `DEFAULT_LOOKUP_EXPR` is `exact` (pinned
    dependency, no project override). The observed
    `(lookups: ['exact'])` matches.
  - Grouping core (`lookup_expr` into the declared head slot):
    lines HEAD-identical; surrounding reads changed
    `getattr`/`isinstance`/`__qualname__` to the `truth.*` forms
    (concurrent refactor) with identical values on this set (no
    `__` in the name, plain declared filter).
  - Bag detection `_operator_bag_items`: body byte-identical (md5
    match); `_LOOKUP_PYTHON_ATTRS` definition and `LOOKUP_NAME_MAP`
    body both byte-identical. `{"range": [...]}` is a bag at both
    bytes.
  - Per-lookup-miss raise: identical but for
    `cls.__qualname__` to `truth.qualname(cls)`, which renders the
    same string for the test's local class (visible in the log);
    neither spelling contains `range input`.
  - `iter_active_fields` classification: happy path identical
    (containment removal only); `window` is LEAF at both bytes.
  - `_input_traversal`: docstring-only diff. `ConfigurationError`:
    plain subclass at both bytes, no `__str__` change.
- FAM-1 verbatim-move proof: the removed inline expression and the
  new `_leaf_lookups_by_attr` body are the identical
  `filter_lookup_table(cls).by_input_attr if ... else {}`; the
  `_normalize_input` composition is behavior-identical.
- Challenge (could ANY cycle item have caused this?): the ledger
  owns exactly these touches near the path — f51 logic-depth
  (5 compositions, all in visibility/apply/logic methods, none on
  this path), Folder `filters/` FAM-1 (verbatim, exonerated) plus
  seed/projection compositions (visibility/seed methods, off-path),
  f45 `iter_input_items` dict arm (`dict.items(view)` to
  `base_container_values`, identical iteration for a plain dict
  with a pure key normalizer) — see CC-1. `filters/inputs.py`,
  `filters/base.py`, `exceptions.py`, `sets_mixins.py`, and the test
  file have no cycle rows. No cycle item could have caused D1; the
  failure exists independent of every cycle edit, so item-back
  would be vacuous (nothing for any Worker-1 to fix).
- Observed failure (both suites): `pytest.raises` expects
  `range input`; production raises `filter input field 'window' has
  no 'range' lookup (lookups: ['exact']); it would apply nothing`
  (the expected exception TYPE fires; only the message regex
  misses — load-bearing for D2 independence).
- Routing stands: concurrent-work failure (never-held test
  expectation vs HEAD-identical production), `## Defects`, gate row
  blocked, owning card for Worker-0 to home on the hunt side.

### D2 re-derived

- Miss line 941 (`raise ValueError("a GlobalID filter value is a
  base64 string")`) is statement-identical to HEAD line 979
  (verified both line numbers by grep). Nearby hunks are message-
  render refactors below the miss; `filters/base.py` carries no
  ledger row (no cycle edit in the file at all).
- Deleted-test attribution by diff content: HEAD
  `tests/filters/test_base.py:1565` held
  `test_decode_global_id_hostile_repr_still_raises_the_coded_error`
  (calls `_decode_and_validate_global_id` with a non-string
  hostile-`__repr__` object: executes line 941, then the coded
  `GraphQLError` arm). Current bytes replace it with
  `test_related_filter_gate_rejection_message_is_pinned`; the
  deleted name occurs nowhere in tests/examples. The test file has
  no ledger row: concurrent deletion. Confirmed.
- Only-non-string-caller proof: every remaining test caller passes
  a base64 `str` or a `relay.GlobalID` (the latter skips line 941
  by branch); production callers pass wire values; the full suite
  empirically leaves 941 the single miss.
- Independence of D1, both directions: (a) D1's test executes its
  whole production path — the `ConfigurationError` raise fires and
  only pytest's message match fails, so its package-line coverage
  equals the passing case; (b) line 941 sits in GlobalID decode,
  unreachable from the range path (the D1 set holds no GlobalID
  filter); fixing D1's expectation cannot cover 941, and restoring
  the deleted test cannot fix D1.
- Downstream effect reproduced fresh in slot-3: the G-gid-1 node
  exits 4 with `collected 0 items / no tests ran` (run
  `dry-20261010T133756-aa31f1`). Routing stands: concurrent-work
  failure, `## Defects`, gate row blocked.

### D3 re-derived (reproduced, then refuted as a hole)

- Reproduced exactly in the shared tree (read-only AST probe):
  `consumer-controlled __name__ reads in code: [(742, 'built')]`,
  exit 1. Same hit W1 recorded.
- False positive, proven five ways: (1) the probe source never
  inspects `node.ctx`, so a STORE hits exactly like a READ;
  (2) line 742 is `built.__name__ = name`, a STORE of the plain
  `str` parameter `name: str`; (3) `built` aliases the
  framework-built `MetaValidatingMetaclass` one line above, and the
  probe's `BENIGN_BASES` (`input_cls`, `payload_cls`,
  `MetaValidatingMetaclass`) does not know the alias; (4) diff
  archaeology: HEAD spelled the same three stores on the allowlisted
  base (probe-silent) — the concurrent `built`-alias refactor kept
  the semantics and tripped only the probe's name model; (5) the
  probe's own contract is consumer-controlled `__name__` READS —
  line 742 is neither a read nor consumer-controlled.
- Settle ruling checked verbatim in the item artifact: P3 is `the
  settle instruction, NOT a deferred proof` (witness-class), so it
  reopens no item; `F2/FL11/FL16 are verified-on-working-bytes-only`
  and `the hunk landing or reverting is a fingerprint change that
  reopens those three rows`. Fingerprints re-hashed: work
  `936f5ae7...` at verification vs `6f2fa2f9...` now; HEAD blob
  `cffa29e5...` then vs `a123aea8...` now. Reopening F2/FL11/FL16
  for Worker-0 re-verification is the correct application.
- Hostile-name oracle green confirmed in W1's log tail
  (`tests/mutations/test_sets.py`, 100 passed) and re-run fresh in
  slot-3 (100 passed, run `dry-20261010T133626-b76a45`). Routing
  stands: rides to the maintainer/Worker-0 closeout (probe update vs row
  re-verification), reopens no item.

### Pending commands (every runnable one ran)

- Census reproduced by machine count over current bytes: 237
  `dry-*.md` files minus 5 plan files minus this artifact = 231
  artifacts; exact-header `## Pending execution` count 207x1 + 2x2
  + 22x0 = 211 sections. The two double-section files and all 22
  zero-section files match W1's lists exactly.
- No missed runnable: a sweep of all 211 section bodies for typed
  `proof:`/`gate:` entries and backticked run commands surfaced
  only entries W1 dispositioned, plus untyped replay-evidence
  commands; 11 of those `None`-with-replay sections read in full,
  each explicitly owing no command.
- `workspace.py audit` over this artifact re-run: 56 cited, 49
  bind ok, 7 non-binders = exactly the 6 foreign-machine E-* run
  ids + the result-file id (a file, not a run). All 49 bound runs
  show `cell=default` and the gate package digest. Bound exits:
  43 exit 0; exit 1 = the 2 RED suites + the superseded tree-check
  + P3 (D3); exit 4 = G-gid-1 (D2) + P-f46 as-listed. Every
  nonzero is accounted for in the narrative.
- Log tails re-read first-hand: G-qs-2 636 passed; P-f64 9/9;
  P-f38 3/3; P-f46 diagnostic 29/29; G-gid-1 `no tests ran`;
  P3 `[(742, 'built')]`; P1 `P1-PASS` with the package `__file__`
  inside slot-2; optimizer 933 passed.
- Prove JSONs re-read: G-fil exit 0, 3/3 entries `pinned: the 1
  failing row(s) are exactly the declared expect_failing`;
  P-f28 exit 0, entry 1 pinned + entry 2 `behaviour preserved`;
  all 5 restores `filecmp True` with matching sha256. Manifest
  hashes on disk match the JSONs. Mutations ran in slot-2 (the
  copy), never the shared tree.
- Fresh re-runs in slot-3 (all through `heavy`, machine GREEN,
  8+ GiB free): witness `tests/mutations/test_sets.py` 100/100
  (`dry-20261010T133626-b76a45`); P-f46 survivors 29/29
  (`dry-20261010T133644-b797f3`, selection re-extracted from the
  f46 artifact: 38 = 10 + 12 + 16, minus the 9 absent nodes);
  G-fil failability prove 3/3 pinned with byte-identical restores
  (`dry-20261010T133706-3b875a`); P-f38 3/3
  (`dry-20261010T133833-688af2`); optimizer collects 933
  (`dry-20261010T133748-c62c4c`, +2 vs the artifact's 931);
  P-f46 as-listed exit 4 with `collected 29 items / no tests
  ran` (`dry-20261010T133806-55b325`).
- P-f46 routing endorsed: `proof:` exit 4, but f46 landed zero
  edits (blocked, specified-not-landed), holds 29/29 on every live
  oracle, and the 9 nodes address a wholesale-removed API family
  (0 references each: `make_hashable_meta_value*` x6 plus 3
  sibling-helper nodes — see CC-2). Nothing for f46's Worker-1 to
  fix; stays `verified, pending execution` with the gap carried to
  Worker-0's closeout call. The 9 nodes are absent at HEAD too
  (existed only in authoring-bytes dirt), so no committed-bytes
  re-point exists to verify against.
- Named-by-gate live sets spot-confirmed in the bound default log:
  0 FAILED under `test_query/` (2032 live PASSED); N-opt's 7 file
  counts exact (5/112/39/11/22/11/198); library 454, client 13,
  uploads 23; `test_multi_db.py` 0 lines (module skip: multi-db
  rows unverified, as recorded).
- `build_tree_md.py --check` re-run in the shared tree: `up to
  date`, exit 0 — confirms W1's correction (a) and agrees with the
  adopted lint GREEN.

### Not-run reasons (each confirmed)

- Cell-gated (U-qs-1, U-perm-1, U-ca-1): no maintainer authorization
  exists anywhere (plan carries the decision as still owed; my own
  brief authorizes default cell only); the pool's `runs.jsonl`
  shows `cell=default` on every run ever made. Unverified stands.
- Blocked (B-f60, B-f36, B-f37, B-f41, B-f42, B-f40, B-e9, B-e8,
  B-f63, B-f38-2): all 10 Families rows re-read at current bytes —
  every one `open ... blocked-on-hunt ... migration specified,
  zero edits ... verified, pending execution`; no landing recorded,
  no ledger row. A green pre-migration run would discharge
  nothing. Carried stands. B-f38-2's record forbids running before
  the landing pass authors `<manifest>`: correctly not run.
- Already-executed (E-e2/e3/e4/e5/e6/e7, E-seal): all 6 foreign
  run ids found verbatim in their artifacts; E-seal's
  execution-verified probe record cites a removed
  `/var/folders/...` disposable workspace. Standing records, none
  re-runnable here. Stands.
- G-qs-3: `probe_defect_arms.py` and the r2 successor both absent
  from every temp-tests scope (the w2 dir holds only the three
  `w2_*` files; sibling `*_9031.py` / adjudication files are
  different instruments). Unrunnable as listed; the revision-1
  measurement stands as the record.

### Transcribable corrections (2, both wording-only; routing unaffected)

- CC-1 (D1 text): `FAM-1 (Folder filters/, the only cycle hunk on
  this path)` is imprecise. Family f45's `iter_input_items` dict-arm
  composition (`pairs = dict.items(input_value)` to
  `pairs = base_container_values(input_value)`) is a second
  cycle-owned hunk on the D1 path. It is exonerated (`tuple()` of
  the same base-slot items; identical iteration for the plain-dict
  input through the pure `_field_name`), so the conclusion — no
  cycle item caused D1, nothing item-back — is unchanged. Fix: name
  both touches with their exonerations.
- CC-2 (P-f46 routing note): `the 9 nodes test
  make_hashable_meta_value` is loose. Six test
  `make_hashable_meta_value*`; three test sibling helpers of the
  same removed family
  (`test_meta_cache_helpers_bypass_container_overrides`,
  `test_make_set_meta_cache_key_tags_fields_shape`,
  `test_normalize_meta_drops_falsy_exclude`). All nine address APIs
  with 0 references in package/tests/examples/scripts. Fix: `the 9
  nodes test the removed container/meta-cache API family`.

### Gate-row completion text

Gate item verified (Worker-2 pass 1). Gate result RED and BLOCKED,
routed, nothing item-back: lint GREEN 13/13; default 1 failed /
10440 passed / 43 skipped, coverage 99.99% (miss
`filters/base.py:941`); floor same single failure 1 / 10437 / 46;
0 xfails; every pending command ran fresh or is recorded with a
confirmed reason. D1 (never-held range-test expectation vs
HEAD-identical production) and D2 (concurrent test deletion leaving
the single coverage miss) block the gate row as concurrent-work
failures; D3 (P3 probe false positive on a framework-built STORE)
rides for closeout with rows F2/FL11/FL16 reopened per the settle
ruling; f46's 9-node gap rides with D2-class drift. Cells
sharded/pg unverified throughout (no authorization). Worker-0 homes
D1/D2/D3 each on a NAMED owning card at closeout.

Status set to `verified` on this verdict: the gate ITEM is verified
even though the gate RESULT is red/blocked.
