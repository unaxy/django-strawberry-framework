# Review · Mechanics: `django_strawberry_framework/keyset.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=d6f1f0a4c4d291b03cf14e680ab3649aeda10851

## Trace

Required reading in order: AGENTS.md, START.md,
`docs/review/REVIEW.md`, `docs/review/worker-1.md`, the plan
(`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl. its
`## Owned changes`, which holds no row for this target),
`docs/review/rev-keyset.md` (skeleton, `Status: reviewing`, blank
Path class). Sibling `docs/review/rev-keyset.performance.md`
(`Status: no-findings`, Path class hot, Handoff absorbed; no
`## Cross-axis` section in it) read whole; sibling
`rev-keyset.comments.md` absent (concurrent run, not yet written).

Target read whole live (709 lines) at blob `279ad7b0`.
`git diff <ITEM_BASELINE> -- <target>` is empty, so the tree reviewed
is the item baseline; `git diff HEAD -- <target>` is +11/-10 of
recorded concurrent work (the `truth.is_instance` /
`truth.render` / `truth.name` error-message conversions plus the
`from .utils import truth` import; plan run-3 Drift lines record the
target dirty). Reviewed live as dispatched. The concurrent hunks
touch raise-paths only and change no honest-input behavior
(`django_strawberry_framework/utils/truth.py::is_instance` is
subclass-aware real-MRO membership, so `str` subclasses still
validate); no finding below depends on them, and any finding about
them would belong to their owning flow, not this item.
Orientation: `review_inspect.py` overview + stripped source under
`<root>/mechanics/inspect/` (json `<root>/mechanics/keyset.json`):
32 symbols, 3 control-flow hotspots (all three are the documented
seek/validation cores), 0 import-time work items, 0 TODOs.

Caller/consumer trace (every import of the target in the package):

- `django_strawberry_framework/connection.py` (module top, 9 names):
  codec + state + errors for the root/per-parent slicer and the
  windowed-page edge build.
- `django_strawberry_framework/optimizer/nested_planner.py` (module
  top, 4 names): plan-time keyset context + cursor decode + seek
  carrier.
- `django_strawberry_framework/optimizer/lateral_fetch.py` (module
  top, `keyset_seek_sql` only): the raw-SQL renderer behind the
  `_keyset_seek_sql` adapter; `_keyset_seek_quals_match` verifies the
  `keyset_seek_q` tree shape against the shared plan.
- `django_strawberry_framework/types/base.py::_validate_cursor_field`
  and `django_strawberry_framework/types/finalizer.py` (finalization
  half): function-scope imports of `validate_cursor_field_references`
  / `validate_cursor_field_columns` (file-idiom order-independence,
  not cycle-breaking: the target never imports `types/`).
- `django_strawberry_framework/optimizer/plans.py` consumes the seek
  only through `KeysetSeek.q()` / the plan object (no import of the
  module); `django_strawberry_framework/utils/connections.py` names
  keyset in prose only (bounds derivation deliberately decoupled
  from the codec); `single_parent_fetch` refuses `keyset_seek`
  (v1 scope guard).

Contract sources read against the body: BACKLOG
`stable_cursor_field` + `permission_aware_cursor_decoding`,
CHANGELOG 0.0.14 keyset row, `docs/GLOSSARY.md` keyset passages,
`docs/README.md` pipeline paragraph, the module docstring claim by
claim, and the oracles `tests/test_keyset.py` (codec/bounds/SQL),
`tests/test_keyset_connection.py` (state/order/slicer),
`examples/fakeshop/test_query/test_keyset_api.py` (live round-trips,
stability, tamper/offset/fingerprint rejection, permission-aware
decode). Installed-dependency facts read from `.venv` source
(django 6.1: all six `value_to_string` definitions return `str`,
BinaryField base64 round-trips; strawberry-graphql 0.324.0:
`from_base64` converts every failure mode to `ValueError`).

`check_citations.py --cited-by` was not needed for a move/rename
(no recommendation moves or renames a symbol);
`check_citations.py --paths <target> --substrings` reports the
target's 3 citations resolve, 0 violations. No workspace run: every
uncertainty below was settled statically (dependency source reads
plus named oracles), so no finding owes a cell run; `sharded` and
`pg` are inapplicable by construction for every discharge (the
target opens no database, references no alias, and branches on no
vendor; the `%s` placeholder style is shared by both backends and
the Postgres-only lateral decision lives in `lateral_fetch`,
outside the fence).

Freshness (`git hash-object` at read time):
`django_strawberry_framework/keyset.py` `279ad7b0`,
`django_strawberry_framework/connection.py` `1fca6266`,
`django_strawberry_framework/optimizer/plans.py` `33140a76`,
`django_strawberry_framework/optimizer/lateral_fetch.py` `db1ea315`,
`django_strawberry_framework/optimizer/nested_planner.py` `d32d1b7b`,
`django_strawberry_framework/types/base.py` `dc67f084`,
`django_strawberry_framework/types/finalizer.py` `b9d8acb2`,
`django_strawberry_framework/types/definition.py` `1c59a3fe`,
`django_strawberry_framework/utils/__init__.py` `1a4c2ec8`,
`django_strawberry_framework/utils/truth.py` `d5c96bc8`,
`django_strawberry_framework/utils/imports.py` `291ecedd`,
`django_strawberry_framework/utils/connections.py` `efcf749a`,
`tests/test_keyset.py` `e5655de7`,
`tests/test_keyset_connection.py` `70db0483`,
`docs/review/rev-keyset.performance.md` `b9cde7cb`,
BACKLOG `9e00b605`, CHANGELOG `d4e10355`, GLOSSARY `3413edc3`.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

Looks-for discharges (each is `none` + reason, or a rejection +
trigger; no defect, no duplication, no cross-axis finding):

- R1 (rule at caller vs owner): every examined rule lives at its
  owner. The unique-terminal rule for `orderBy:` pages is enforced
  by `django_strawberry_framework/optimizer/plans.py::deterministic_order`
  (the order pipeline's own rule) before
  `django_strawberry_framework/connection.py::_keyset_order_state`
  reads the effective order; the per-order null/JSON checks in
  `_keyset_order_state` compose the target's own
  `django_strawberry_framework/keyset.py::_is_supported_cursor_field`
  + `django_strawberry_framework/keyset.py::keyset_contract_error`
  (DRY already counts 1 authoritative definition with the finalizer
  and the order-state as consumers); the single-parent keyset
  refusal is that strategy's own v1 scope; each cursor vocabulary
  rejects foreign prefixes at its own decode site. Trigger: a third
  consumer re-spelling the column predicate instead of composing
  the two primitives.
- R2 (policy in adapter / mechanism in policy): the target holds
  mechanism only (codec, seek plan + renderers, column validation).
  Keyset-vs-offset dispatch lives in `connection.py` /
  `nested_planner.py`, the Relay-Node gate in stage 1
  (`types/base.py::_validate_cursor_field`), backend selection in
  `lateral_fetch`. The error stem names `Meta.cursor_field` because
  the target owns that vocabulary. Trigger: the target gaining a
  branch on connection strategy, plan shape, or backend.
- R3 (contract sources vs body): verified claim by claim. BACKLOG
  tuple-seek = the row set both renderers select (OR-expansion is
  the portable spelling; uniform SQL emits the literal
  `(a, b) > (%s, %s)`); final unique tiebreak validated at
  finalization; opaque authenticated-encrypted payload with
  `SECRET_KEY_FALLBACKS` decrypt-only rotation; soft `cryptography`
  import at mint/decode only; deterministic SIV; fingerprint
  rejection; decode applied to the already-scoped queryset by the
  pipeline (correct layering: the target cannot scope). Stem-site
  count (1 + 4 across two modules) and fingerprint sole-site
  (`",".join`) re-derived, matching the docstrings. One sound
  generalization: a `unique=True` non-pk terminal is accepted where
  BACKLOG says `(pk)`; non-null is enforced on every entry, so it is
  a total-order equivalent. Trigger: a contract source pinning
  pk-only terminals.
- R4 (unreached branch): every defensive branch is a pinned
  validation/decode totality, not dead code: non-`str`
  `split_order_ref` (`test_split_order_ref_rejects_non_string_entry`),
  empty references, the forged-payload rejection matrix, the
  `SECRET_KEY_FALLBACKS`-absent getattr, the empty/arity-mismatch
  `KeysetSeekPlan` `ValueError`s, the `pk`-alias arm. `decode` is
  total over all inputs (upstream `from_base64` funnels every
  failure into `ValueError`, which the target converts). Trigger: an
  unpinned defensive branch (`fail_under = 100` fails first).
- R5 (mode flag for named adapter): `flip` is a direction bit
  consumed by the single direction rule
  (`django_strawberry_framework/keyset.py::keyset_seek_greater`),
  not a behavior selector; `uniform` / `lead_greater` are derived
  facts, not flags. Trigger: a second boolean selecting renderers.
- R6 (state in two places): `DeclaredCursorState` is frozen; the
  connection-class `_dst_keyset_state` slot is a memo of a pure
  derivation (keyed on target identity; declarations cannot change
  on a live type); `_cursor_aessiv` `@cache` is pure of the
  configured secret; the fingerprint pair is check-value vs
  expected-value, not dual ownership. Trigger: a mutable
  cursor-state write path.
- R7 (dependency direction): imports run leaf-ward only (stdlib,
  Django, graphql-core, `strawberry.relay.utils`, `.exceptions`,
  `.utils`, `.utils.imports`); no `TYPE_CHECKING`, no cycle, no
  flavor above the target. The `types/*` function-scope imports
  match file idiom. The `from .utils import truth` edge pulls no
  new package (submodule imports already execute
  `utils/__init__.py`, whose own imports are leaves). Trigger: the
  target importing `optimizer/`, `connection`, or `types/`.
- R8 (`django.conf.settings` at import): the module binds
  `LazySettings` only; reads happen at call time (encrypt/decrypt).
  Corroborated by the sibling Performance importtime row (no
  settings read at import). Trigger: any module-level settings
  attribute read.
- R9 (`__all__` vs public surface): absent, matching the
  engine-module convention (`connection`, `conf`, `plans`,
  `utils/connections` all carry none; only public-surface modules
  do), and no keyset name is root-exported. The test-suite
  `from_base64`-via-keyset import is incidental re-export
  consumption, not a surface promise. Trigger: a root export or
  documented public import of a keyset name.
- R10 (one rule twice; DRY change challenges): (a)
  `split_order_ref` vs
  `django_strawberry_framework/optimizer/plans.py::order_entry_name_and_direction`
  string branch: loud `ConfigurationError` + local-only vs
  `None`-signal + traversal-permitting; posit either contract
  change and the other stands pat — different rules, and merging
  would couple a loud boundary to a silent parser. (b)
  `keyset_seek_q` / `keyset_seek_sql`: two renderers under the one
  `KeysetSeekPlan` owner (DRY family; posit dropping the leading
  bound and both move with the verifier plus oracles). (c)
  `lateral_fetch._keyset_seek_quals_match` re-spells the tree shape
  because it is an independent fail-closed recognizer;
  consolidation would be self-verification. (d) The three `pk`-alias
  spellings (whole-name, path-segment, unique-terminal membership)
  apply Django's own convention in three shapes; posit a Django
  alias change and all three are mechanical. (e) Null/JSON per-order
  checks: consumers of the single `_is_supported_cursor_field`
  definition. Triggers: (a) keyset accepting traversal or plans
  raising; (b)/(c) a third renderer or a parameterized seek shape
  the verifier does not take; (d) a fourth spelling; (e) a consumer
  re-spelling the predicate.
- R11 (sync/async twins): no async surface in the target; `Q`
  construction is sync-safe under both engines, and the crypto +
  codec are pure CPU. Nothing to drift. Trigger: an async variant
  of any keyset helper.
- R12 (guard a sibling lacks): checked pair by pair. Encode and
  decode both reject NULL; mint embeds and decode checks the
  fingerprint and the arity; `keyset_seek_sql` carries the explicit
  arity check because its column refs arrive cross-object, while
  `keyset_seek_q` builds both sides from one object (a correct
  asymmetry); uniform row-value comparison is exactly the
  leading-bound OR-expansion under the non-null contract
  (set-equivalence plus the PG parity oracles); backward nested
  keyset routes per-parent and `keyset_seek` + `reverse` raises
  loud `OptimizerError` (pinned). Trigger: one flavor accepting a
  wire-reachable input its twin rejects.

Considered and rejected as findings:

- R13 (`("pk", "id")` alias pair accepted): the duplicate check
  compares declared names, so a `pk`-alias/attname pair passes
  validation. Harmless: both columns read the same attname with the
  same minted value, so the second OR arm is empty and the seek is
  exactly the single-column seek in every direction mix. Rejecting
  it would buy one redundant arm at the cost of attname-worded
  errors for declared refs. Trigger: a `pk`-alias pair that
  paginates wrongly.
- R14 (`SECRET_KEY_FALLBACKS` getattr default): unreachable on the
  supported floor (Django always defines it), but it is a pinned
  one-expression compat shim, not drift. Trigger: a gate against
  dead getattr defaults (not this item).
- R15 (custom-field codec shape): the codec relies on
  `value_to_string` returning `str`, which is Django's own field
  contract; all six stock definitions in installed Django 6.1
  return `str` (dates isoformat, durations `duration_string`,
  BinaryField base64 with a `str`-accepting `to_python`), so every
  stock column type round-trips and the re-serialize check stays
  type-stable. Trigger: a stock field returning non-`str`.

Handoff: Mechanics on `keyset.py` is a clean pass with no findings:
the codec is total over hostile input, both seek dialects render one
plan, every validation stage owns a distinct input shape, and the
only twin (the plans order parser) and the only re-spellings (the
SQL renderer, the lateral recognizer) fail closed or differ in
contract. The sibling Performance record corroborates the hot-path
map, the settings/cache split, and the decode-validation boundary
(R4/R8/R12); no direction in it conflicts with this record. The
concurrent `truth.*` hunks were read as part of the live tree and
verified behavior-preserving for honest inputs; they belong to
their owning flow. Nothing is left open for a further Mechanics
pass; the verifier owes this record no Proof runs (no findings, no
cross-axis entries) beyond confirming `Status: no-findings` stands
on the shipped tree.

## Verification (Mechanics)

Step 1 (tree still carries the sent change): `git diff
d6f1f0a4c4d291b03cf14e680ab3649aeda10851 --
django_strawberry_framework/keyset.py` is byte-identical to
`docs/review/temp-tests/keyset/diff/pass-1.diff` (both
`sha256:96670bf91b70e3f7e77d91ece2413b74f20c4ffaa463e8c56b34cb67b0b80043`,
`diff` reports `HASH_EQUAL`). Grading proceeds.

Proof runs: none exist to run. This record holds zero findings and
hence zero Proof lines (its only `Proof` mention is the review
Handoff anticipating this); `rev-keyset.performance.md` carries no
`## Cross-axis` section and `rev-keyset.comments.md` carries no
`## Cross-axis` section (confirmed by `grep`; the one `Cross-axis`
hit in this record is the Trace sentence noting the Performance
record has none). No verbatim run is owed, at any address.

Behavior preservation: `review_inspect.py --code-digest
d6f1f0a4c4d291b03cf14e680ab3649aeda10851:django_strawberry_framework/keyset.py
django_strawberry_framework/keyset.py` exits 0 with both digests
`sha256:bb01f2e8fe76bba0d0884be6ec485830283e6853df51348e7507551e6549ee05`,
matching the digest Worker-2 reported. A revert proof is vacuous:
the item-scoped diff holds no production hunk (5 docstring hunks,
21+/13-, on the target only), so there is no behavior-changing edit
to reverse-apply and no `prove` manifest is owed. No permanent test
exists or is owed (prose-only per REVIEW.md "Comments").

Whole-diff reading (Mechanics): every hunk sits inside a docstring
(module, `KeysetSeek`, `keyset_contract_error`,
`encode_keyset_cursor`, `KeysetSeekPlan`); no code token, import,
signature, decorator, or behavior-consumed literal changed.
Placement, ownership, dependency direction and state shape are
untouched, so discharges R1-R15 stand as written. The deferred Lows
(L2/L3 in `test_keyset_api.py`, L4 in `tests/types/test_base.py`)
touch files outside this diff, and both files are byte-identical to
ITEM_BASELINE (`88a432b0`, `bb56c89b`), so no mechanics surface
moved there either. `git diff <ITEM_BASELINE> --stat` over the three
candidate paths lists the target alone.

Attacks on the current state (all pass; static, shared tree — no
workspace run is owed for a prose-only diff):

- A1 dependency direction (R7): the `^import |^from ` list at
  baseline vs live is identical (18 lines; only line numbers shift
  from docstring growth). No new edge, no `optimizer/` /
  `connection` / `types/` import.
- A2 symbol inventory: the `^def |^class |^    def ` list at
  baseline vs live is identical (32/32). Nothing moved, renamed,
  added or removed, so no `--cited-by` sweep is owed.
- A3 settings at import (R8): `settings.SECRET_KEY` is read only at
  call time (`_encrypt_cursor_payload`, `_decrypt_cursor_payload`
  incl. the `SECRET_KEY_FALLBACKS` getattr); no module-level
  settings read. Holds.
- A4 `__all__` (R9): still absent. Holds.
- A5 error-stem census (R3, L1): 1 in-target call site
  (`keyset.py:516`, was `:511`) + 4 in `connection.py`
  (`:946,:953,:959,:1073`, unchanged) — the five-site/two-module
  sharing the rewritten docstring claims. Intact.
- A6 callers: `connection.py`, `nested_planner.py`,
  `lateral_fetch.py` are untouched by this single-file diff, so no
  consumer mechanics moved.

Disputes: none recorded. `## Implementation (Worker-2)` carries no
`disputed:` marker and closes "Nothing disputed, blocked, or
stopped". Nothing to judge.

Test tier / failability: no test is relied on, so no tier check and
no `prove` run apply; both deferred test files are confirmed
unmodified above.

Lint gates (`--check` forms only, 2026-09-29): `ruff check
django_strawberry_framework/keyset.py` → All checks passed, exit 0;
`ruff format --check` on the target → 1 file already formatted,
exit 0; `check_trailing_commas.py --check` on the target → 0
violations, exit 0; `check_citations.py --check` tree-wide → 1299
citations resolve, exit 0.

Cells: `sharded` and `pg` inapplicable by construction — a
prose-only diff on a target that opens no database, references no
alias and branches on no vendor moves no query in any cell. Cells
unverified: none.

Fingerprints (live tree at verify time): target `d1a6dec2`
(matches Worker-2's touched fingerprint, was `279ad7b0` at
ITEM_BASELINE); `test_keyset_api.py` `88a432b0`;
`tests/types/test_base.py` `bb56c89b` (both equal ITEM_BASELINE).
Scratch `docs/review/temp-tests/keyset/verify-mechanics-1/` created,
holds no probe (none owed for prose-only). No workspace runs, no run
ids.

Verdict: `Status: verified`. No new finding, no routed gap, no
`## Decisions` item. The pass-1 change is behavior-identical prose
on a Mechanics-clean file.

Handoff: Mechanics verification of pass 1 is complete and green:
hash-equal diff, digest-identical code, all four lint gates exit 0,
every Mechanics discharge re-confirmed on the shipped text. The
deferred Lows live entirely in the Comments axis (L2/L3 have no
owning open item; L4 rides with the `types/base.py` item) and move
no mechanics surface. Nothing is left open for a further Mechanics
pass; a re-pass would only be owed if a later pass touched code.
